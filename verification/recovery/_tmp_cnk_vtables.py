import struct, json, collections, re, os

ELF = r'c:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc\boot.elf'
OUT = r'c:\PS2Recomp\verification\recovery\_cnk_elf_xrefs.json'
data = open(ELF,'rb').read()
LOAD_VA = 0x00100000
FILE_OFF = 0x80
FILESZ = 0x5F2000
MEMSZ = 0x62A480
text = data[FILE_OFF:FILE_OFF+FILESZ]

def va_ok(va):
    return LOAD_VA <= va < LOAD_VA + MEMSZ

def va_to_off(va):
    if LOAD_VA <= va < LOAD_VA + FILESZ:
        return FILE_OFF + (va - LOAD_VA)
    return None

def read_u32(va):
    off = va_to_off(va)
    if off is None: return None
    return struct.unpack_from('<I', data, off)[0]

def read_bytes(va, n):
    off = va_to_off(va)
    if off is None: return None
    return data[off:off+n]

# ---- extract C strings ----
strings = {}  # va -> s
i = 0
while i < len(text):
    if 32 <= text[i] < 127:
        j = i
        while j < len(text) and 32 <= text[j] < 127:
            j += 1
        if j - i >= 4 and (i == 0 or text[i-1] == 0):
            s = text[i:j].decode('ascii')
            strings[LOAD_VA + i] = s
        i = j
    else:
        i += 1

# Focus ig* / Alchemy class-like names (identifier-ish)
ig_names = {va:s for va,s in strings.items() if re.fullmatch(r'ig[A-Za-z0-9_]+', s) or s in ('Alchemy','ALCHEMY_BASE','alchemy.ini')}
print('ig-like class name strings:', len(ig_names))

# Find all pointers in file that point TO these name VAs (typeinfo name field / RTTI)
name_xrefs = {hex(va): {'name': s, 'ptr_sites': []} for va,s in sorted(ig_names.items())}
# Scan every word in LOAD for pointer == name_va
# Also scan for name_va used as lui/addiu builds

ptr_to_name = collections.defaultdict(list)  # name_va -> [site_va]
# Build reverse: for each 4-aligned word
for off in range(0, FILESZ, 4):
    w = struct.unpack_from('<I', text, off)[0]
    if w in ig_names:
        site = LOAD_VA + off
        ptr_to_name[w].append(site)

for name_va, sites in ptr_to_name.items():
    name_xrefs[hex(name_va)]['ptr_sites'] = [hex(s) for s in sites[:40]]
    name_xrefs[hex(name_va)]['ptr_count'] = len(sites)

print('names with ptr xrefs:', sum(1 for v in name_xrefs.values() if v.get('ptr_count',0)))

# Heuristic Alchemy typeinfo: often [vtable_or_meta, name_ptr, ...]
# For each ptr_site that points at a class name, look at -4/-8/+4 for other pointers into text
typeinfos = []
vtables = {}  # class -> inferred vtable va

for name_va, sites in ptr_to_name.items():
    name = ig_names[name_va]
    for site in sites:
        # candidate typeinfo object containing name at offset 0 or 4
        for name_off in (0, 4, 8):
            ti = site - name_off
            if not va_ok(ti): continue
            # gather nearby words
            words = []
            ok = True
            for k in range(0, 8):
                w = read_u32(ti + 4*k)
                if w is None:
                    ok = False; break
                words.append(w)
            if not ok: continue
            if words[name_off//4] != name_va:
                continue
            # score: how many nearby words look like code/data pointers
            code_ptrs = [w for w in words if LOAD_VA <= w < LOAD_VA + 0x00500000]
            data_ptrs = [w for w in words if 0x00600000 <= w < LOAD_VA + MEMSZ]
            typeinfos.append({
                'class': name,
                'name_va': hex(name_va),
                'typeinfo_va': hex(ti),
                'name_field_off': name_off,
                'words': [hex(w) for w in words],
                'code_ptrs': [hex(w) for w in code_ptrs],
                'data_ptrs': [hex(w) for w in data_ptrs],
            })

# Dedup typeinfos by (class, typeinfo_va)
seen=set(); uniq=[]
for t in typeinfos:
    key=(t['class'], t['typeinfo_va'])
    if key in seen: continue
    seen.add(key); uniq.append(t)
typeinfos = uniq
print('candidate typeinfos:', len(typeinfos))

# For key classes of interest, print
KEY = ['igIGBFile','igFile','igFileIO','igPsx2IopRpcConnection','igPsx2VisualContext',
       'igObject','igMemoryPool','igMallocMemoryPool','igNode','igGroup','igAttr',
       'igGuiSystem','igRenderer','igStreamingSource','igInfoManager']
print('\n=== KEY CLASS typeinfo candidates ===')
for t in typeinfos:
    if t['class'] in KEY:
        print(t)

# Find vtables: search for sequences of >=8 consecutive pointers into executable range near/after typeinfo
# Better: for each typeinfo, if word0 looks like vtable ptr OR find refs TO typeinfo

# Refs TO typeinfo addresses
ti_refs = collections.defaultdict(list)
ti_set = {int(t['typeinfo_va'],16): t for t in typeinfos}
for off in range(0, FILESZ, 4):
    w = struct.unpack_from('<I', text, off)[0]
    if w in ti_set:
        ti_refs[w].append(LOAD_VA+off)

# Classic C++: vtable[-1] or vtable[0] points to typeinfo. On MW/PS2 often:
# vtable starts with typeinfo pointer OR offset-to-top + typeinfo then methods.
# Alchemy often: class registry maps name -> creator; vtable at object[0].

# Alternative approach used by many PS2 Alchemy dumps:
# Find string, find pointer to string, that structure's first field or nearby is meta;
# objects constructed with lui/addiu pointing at a method table.

def looks_like_vtable(va, min_fns=6):
    """va points to array of code pointers."""
    fns=[]
    for k in range(min_fns+4):
        w = read_u32(va + 4*k)
        if w is None: return None
        # code in first ~5MB of LOAD (text-ish)
        if not (LOAD_VA <= w < 0x00600000):
            if k < min_fns: return None
            break
        # prefer 4-aligned and not obviously data
        if w & 3: return None
        fns.append(w)
    return fns if len(fns) >= min_fns else None

# Scan for vtables that have typeinfo pointer at -4 or slot0
vtable_hits = []
for ti_va, t in ti_set.items():
    # search words equal to ti_va; if next words are code ptrs, it's RTTI-before-vtable
    for site in ti_refs.get(ti_va, []):
        # case A: [typeinfo][fn0][fn1]...  site is typeinfo slot in vtable prologue
        fns = looks_like_vtable(site+4, 8)
        if fns:
            vtable_hits.append({'class': t['class'], 'vtable_va': hex(site+4), 'rtti_slot': hex(site), 'n_methods': len(fns), 'methods0_5': [hex(x) for x in fns[:6]], 'pattern': 'ti_then_methods'})
            continue
        # case B: site points into a struct; check site-4 is start... 
        fns = looks_like_vtable(site, 8)
        if fns and fns[0] == ti_va:
            # first slot is typeinfo - unusual for calls
            pass
        # case C: pointer TO typeinfo is stored elsewhere; nearby code ptrs
        # if previous word is 0 or small offset and next are methods
        prev = read_u32(site-4) if site >= LOAD_VA+4 else None
        if prev is not None and prev in (0, 0xFFFFFFFF) or (prev is not None and prev < 0x100):
            fns = looks_like_vtable(site+4, 8)
            if fns:
                vtable_hits.append({'class': t['class'], 'vtable_va': hex(site+4), 'rtti_slot': hex(site), 'n_methods': len(fns), 'methods0_5': [hex(x) for x in fns[:6]], 'pattern': 'offset_ti_methods'})

# Dedup
seen=set(); vh=[]
for v in vtable_hits:
    key=(v['class'], v['vtable_va'])
    if key in seen: continue
    seen.add(key); vh.append(v)
vtable_hits = vh
print('\nvtable hits (RTTI pattern):', len(vtable_hits))
for v in vtable_hits:
    if v['class'] in KEY or 'File' in v['class'] or 'Iop' in v['class'] or 'IGB' in v['class']:
        print(v)

# Broader: for key names, take EVERY ptr site and try to find surrounding vtable-like arrays
print('\n=== Broad scan around key name ptr sites ===')
broad = []
for name_va,s in ig_names.items():
    if s not in KEY and not any(k in s for k in ('File','IGB','Iop','Visual','Gui','Stream')):
        continue
    for site in ptr_to_name.get(name_va, []):
        # walk backward up to 16 words looking for start of code-ptr run after this name ref
        for delta in range(-16, 17):
            cand = site + delta*4
            fns = looks_like_vtable(cand, 10)
            if fns:
                broad.append({'class':s,'name_va':hex(name_va),'name_ptr_site':hex(site),'vtable_cand':hex(cand),'n':len(fns),'m0':hex(fns[0]),'m20':hex(fns[20]) if len(fns)>20 else None, 'm21':hex(fns[21]) if len(fns)>21 else None})
                break

# dedup by class+vtable
seen=set(); b2=[]
for b in broad:
    key=(b['class'],b['vtable_cand'])
    if key in seen: continue
    seen.add(key); b2.append(b)
broad=b2
print('broad vtable cands:', len(broad))
for b in sorted(broad, key=lambda x:x['class'])[:60]:
    print(b)

result = {
    'elf': ELF,
    'load_va': hex(LOAD_VA),
    'entry': hex(0x00108D28),
    'ig_name_count': len(ig_names),
    'name_xrefs': {k:v for k,v in name_xrefs.items() if v.get('ptr_count',0)>0 and (v['name'] in KEY or any(x in v['name'] for x in ('File','IGB','Iop','Visual','Gui','Stream','Alchemy','Bind','Object')))},
    'typeinfos_key': [t for t in typeinfos if t['class'] in KEY or any(x in t['class'] for x in ('File','IGB','Iop'))][:80],
    'vtable_rtti': vtable_hits,
    'vtable_broad': broad,
}
open(OUT,'w').write(json.dumps(result, indent=2))
print('\nWrote', OUT, 'bytes', os.path.getsize(OUT))
