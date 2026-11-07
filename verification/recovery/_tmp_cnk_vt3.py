import struct, json, collections, re

ELF = r'c:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc\boot.elf'
data = open(ELF,'rb').read()
LOAD_VA = 0x00100000
FILE_OFF = 0x80
FILESZ = 0x5F2000
text = data[FILE_OFF:FILE_OFF+FILESZ]
GP = 0x00709BF0

def read_u32(va):
    if va < LOAD_VA or va >= LOAD_VA+FILESZ: return None
    return struct.unpack_from('<I', data, FILE_OFF+(va-LOAD_VA))[0]

regs=['r0','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']

# All lw/sw with imm that resolve with base lui 0x72 to 0x725F50
print('=== ALL 0x725F50 accessors (hex) ===')
for off in range(0,FILESZ-4,4):
    w=struct.unpack_from('<I',text,off)[0]
    if (w>>26)!=15 or (w&0xFFFF)!=0x0072: continue
    rt=(w>>16)&0x1F
    base_va = LOAD_VA+off
    for k in range(1,20):
        w2=struct.unpack_from('<I',text,off+4*k)[0]
        op=(w2>>26)&0x3F
        rs=(w2>>21)&0x1F
        rt2=(w2>>16)&0x1F
        imm=w2&0xFFFF
        simm=imm-0x10000 if imm>=0x8000 else imm
        if rs!=rt: continue
        if op in (35,43) and simm==0x5F50:
            print('  %s 0x%08X  (lui@0x%08X reg=%s) -> 0x00725F50' % ('lw' if op==35 else 'sw', LOAD_VA+off+4*k, base_va, regs[rt2]))
            # print surrounding
            for j in range(-2,8):
                pc=LOAD_VA+off+4*k+4*j
                ww=read_u32(pc)
                if ww is None: continue
                print('    %08X: %08X'%(pc,ww))

# Find SW that writes NONZERO to 725F50 - already have sw r0. Search for sw of other regs.
# Also check addiu at, at, 0x5F50 then sw

print('\n=== addiu *,*,0x5F50 then following ===')
for off in range(0,FILESZ-8,4):
    w=struct.unpack_from('<I',text,off)[0]
    if (w>>26)==9 and (w&0xFFFF)==0x5F50:
        rt=(w>>16)&0x1F; rs=(w>>21)&0x1F
        print('addiu %s,%s,0x5F50 @ 0x%08X'%(regs[rt],regs[rs],LOAD_VA+off))
        for k in range(1,6):
            w2=struct.unpack_from('<I',text,off+4*k)[0]
            print('  +%d: %08X'%(k,w2))

# GP-relative: lw/sw gp, imm where GP+simm == target string or 725F50
def gp_refs_to(target, label, limit=20):
    want = (target - GP) & 0xFFFFFFFF
    # as signed 16
    if want >= 0x80000000: want_s = want - 0x100000000
    else: want_s = want
    if not (-0x8000 <= want_s <= 0x7FFF):
        print(label, 'not gp16 reachable from GP (delta', hex(want_s), ')')
        return []
    imm = want_s & 0xFFFF
    hits=[]
    for off in range(0,FILESZ,4):
        w=struct.unpack_from('<I',text,off)[0]
        op=(w>>26)&0x3F
        if op not in (32,33,35,36,37,40,41,43): continue
        rs=(w>>21)&0x1F
        if rs!=28: continue  # gp
        if (w&0xFFFF)!=imm: continue
        hits.append(LOAD_VA+off)
    print(label, 'gp refs', len(hits), [hex(h) for h in hits[:limit]])
    return hits

print('\nGP=0x%08X'%GP)
gp_refs_to(0x00725F50, '725F50')
gp_refs_to(0x00725EE0, '725EE0')

# For key class strings, check gp-relative
strings={}
i=0
while i<len(text):
    if 32<=text[i]<127:
        j=i
        while j<len(text) and 32<=text[j]<127: j+=1
        if j-i>=4 and (i==0 or text[i-1]==0):
            strings[LOAD_VA+i]=text[i:j].decode('ascii')
        i=j
    else: i+=1

for s in ['igIGBFile','igFile','igPsx2IopRpcConnection','igMallocMemoryPool','Alchemy','alchemy.ini']:
    vas=[va for va,ss in strings.items() if ss==s]
    for va in vas:
        print('---',s,hex(va),'delta',hex((va-GP)&0xFFFFFFFF))
        gp_refs_to(va, s)

# MetaObject pattern: search for "igMetaObject" or "Meta" registration tables
meta_strs=[(va,s) for va,s in strings.items() if 'eta' in s and ('ig' in s or 'Meta' in s or 'Registry' in s or 'Type' in s)]
print('\nmeta-ish strings sample:')
for va,s in sorted(meta_strs)[:40]:
    if len(s)<60: print(hex(va), s)

# Find function that STOREs into 725F50 with a live pointer: scan generated unit for st32 24400
