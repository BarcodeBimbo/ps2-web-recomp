#!/usr/bin/env python3
"""CNK boot.elf Alchemy string/VA walk — research only, no patches."""
from __future__ import annotations

import json
import re
import struct
from collections import Counter
from pathlib import Path

ELF = Path(r"C:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc\boot.elf")
OUT_JSON = Path(r"C:\PS2Recomp\verification\recovery\_tmp_w1_cnk_elf_walk.json")

data = ELF.read_bytes()
assert data[:4] == b"\x7fELF"

e_entry = struct.unpack_from("<I", data, 24)[0]
e_phoff = struct.unpack_from("<I", data, 28)[0]
e_shoff = struct.unpack_from("<I", data, 32)[0]
e_phentsize, e_phnum = struct.unpack_from("<HH", data, 42)
e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)

phdrs = []
for i in range(e_phnum):
    off = e_phoff + i * e_phentsize
    p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align = struct.unpack_from(
        "<IIIIIIII", data, off
    )
    phdrs.append(
        {
            "i": i,
            "type": p_type,
            "offset": p_offset,
            "vaddr": p_vaddr,
            "filesz": p_filesz,
            "memsz": p_memsz,
            "flags": p_flags,
        }
    )

sections = []
for i in range(e_shnum):
    off = e_shoff + i * e_shentsize
    sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size, sh_link, sh_info, sh_addralign, sh_entsize = (
        struct.unpack_from("<IIIIIIIIII", data, off)
    )
    sections.append(
        {
            "i": i,
            "name_idx": sh_name,
            "type": sh_type,
            "addr": sh_addr,
            "offset": sh_offset,
            "size": sh_size,
            "entsize": sh_entsize,
            "link": sh_link,
        }
    )

shstr = b""
if e_shstrndx < e_shnum:
    s = sections[e_shstrndx]
    shstr = data[s["offset"] : s["offset"] + s["size"]]


def sname(idx: int) -> str:
    if not shstr:
        return "?"
    end = shstr.find(b"\x00", idx)
    return shstr[idx:end].decode("ascii", "replace")


for s in sections:
    s["name"] = sname(s["name_idx"])

load = [p for p in phdrs if p["type"] == 1]


def va_to_off(va: int):
    for p in load:
        if p["vaddr"] <= va < p["vaddr"] + p["filesz"]:
            return p["offset"] + (va - p["vaddr"])
    return None


def in_bss(va: int) -> bool:
    for p in load:
        if p["vaddr"] + p["filesz"] <= va < p["vaddr"] + p["memsz"]:
            return True
    return False


def read_va(va: int, n: int):
    off = va_to_off(va)
    if off is None:
        return None
    return data[off : off + n]


def disasm_words(va: int, nwords: int = 8):
    raw = read_va(va, nwords * 4)
    if raw is None:
        return None
    return [struct.unpack_from("<I", raw, i)[0] for i in range(0, len(raw), 4)]


def decode_mips(w: int) -> str:
    op = (w >> 26) & 0x3F
    rs = (w >> 21) & 0x1F
    rt = (w >> 16) & 0x1F
    rd = (w >> 11) & 0x1F
    sa = (w >> 6) & 0x1F
    fn = w & 0x3F
    imm = w & 0xFFFF
    simm = imm - 0x10000 if imm >= 0x8000 else imm
    target = (w & 0x03FFFFFF) << 2
    if op == 0:
        if fn == 0x08:
            return f"jr ${rs}"
        if fn == 0x09:
            return f"jalr ${rd},${rs}"
        if fn == 0x21:
            return f"addu ${rd},${rs},${rt}"
        if fn == 0x25:
            return f"or ${rd},${rs},${rt}"
        if fn == 0x00 and w == 0:
            return "nop"
        if fn == 0x00:
            return f"sll ${rd},${rt},{sa}"
        return f"SPECIAL fn=0x{fn:02X}"
    if op == 0x02:
        return f"j 0x{target:08X}"
    if op == 0x03:
        return f"jal 0x{target:08X}"
    if op == 0x04:
        return f"beq ${rs},${rt},{simm}"
    if op == 0x05:
        return f"bne ${rs},${rt},{simm}"
    if op == 0x08:
        return f"addi ${rt},${rs},{simm}"
    if op == 0x09:
        return f"addiu ${rt},${rs},{simm}"
    if op == 0x0C:
        return f"andi ${rt},${rs},0x{imm:X}"
    if op == 0x0D:
        return f"ori ${rt},${rs},0x{imm:X}"
    if op == 0x0F:
        return f"lui ${rt},0x{imm:X}"
    if op == 0x20:
        return f"lb ${rt},{simm}(${rs})"
    if op == 0x23:
        return f"lw ${rt},{simm}(${rs})"
    if op == 0x24:
        return f"lbu ${rt},{simm}(${rs})"
    if op == 0x28:
        return f"sb ${rt},{simm}(${rs})"
    if op == 0x2B:
        return f"sw ${rt},{simm}(${rs})"
    if op == 0x1C:  # MMI / special2 on EE
        return f"MMI/SPECIAL2 fn=0x{fn:02X}"
    return f"op=0x{op:02X}"


# ---- Key VAs ----
KEY_VAS = {
    "entry_crt0": 0x00108D28,
    "app_init": 0x00108F60,
    "loadgate_FCE0": 0x0010FCE0,
    "finalize_110100": 0x00110100,
    "bind_registry_bss": 0x00725F50,
    "bind_installer": 0x00520160,
    "bind_teardown": 0x00520210,
    "nullbind_helper": 0x0051AC80,
    "nullbind_ra_51ACEC": 0x0051ACEC,
    "factory_508930": 0x00508930,
    "allocator_bss_725F00": 0x00725F00,
    "alchemy_ver_str": 0x006B4920,
    "ALCHEMY_BASE": 0x006B2288,
    "alchemy_ini": 0x006B4B08,
    "igFileIO_irx": 0x006B8F18,
    "alchemy_iop_unix": 0x006B8E90,
    "alchemy_iop_win": 0x006B8EB0,
    "igIGBFile": 0x006B2B90,
    "igFile": 0x006B3198,
}

key_va_report = {}
for name, va in KEY_VAS.items():
    off = va_to_off(va)
    entry = {"va": f"0x{va:08X}", "file_off": None, "region": None, "preview": None}
    if off is not None:
        entry["file_off"] = f"0x{off:X}"
        entry["region"] = "LOAD"
        raw = data[off : off + 32]
        # string preview if printable
        try:
            nul = raw.find(b"\x00")
            s = raw[: nul if nul >= 0 else 32]
            if len(s) >= 4 and all(32 <= b < 127 or b in (9, 10, 13) for b in s):
                entry["preview"] = s.decode("ascii", "replace")
            else:
                words = [struct.unpack_from("<I", raw, i)[0] for i in range(0, min(16, len(raw)), 4)]
                entry["preview"] = " ".join(f"{w:08X}" for w in words)
                entry["disasm"] = [
                    {"va": f"0x{va + i*4:08X}", "word": f"0x{w:08X}", "asm": decode_mips(w)}
                    for i, w in enumerate(words)
                ]
        except Exception as e:
            entry["preview"] = f"err:{e}"
    elif in_bss(va):
        entry["region"] = "BSS"
        entry["preview"] = "(zero-filled at CRT0; not in file)"
    else:
        entry["region"] = "UNMAPPED"
    key_va_report[name] = entry

# Expand neighbors for critical code sites
NEIGHBOR = {
    "entry_crt0": (0x00108D28, 12),
    "loadgate_FCE0": (0x0010FCE0, 20),
    "finalize_110100": (0x00110100, 16),
    "bind_installer": (0x00520160, 24),
    "nullbind_helper": (0x0051AC80, 32),
    "nullbind_ra_51ACEC": (0x0051ACE0, 8),
}
neighbors = {}
for name, (va, n) in NEIGHBOR.items():
    words = disasm_words(va, n)
    if words is None:
        neighbors[name] = None
        continue
    neighbors[name] = [
        {"va": f"0x{va + i*4:08X}", "word": f"0x{w:08X}", "asm": decode_mips(w)}
        for i, w in enumerate(words)
    ]

# Count jal to key targets in image
JAL_TARGETS = {
    0x0010FCE0: "FCE0",
    0x00110100: "110100",
    0x00520160: "bind_installer",
    0x00520210: "bind_teardown",
    0x0051AC80: "nullbind_helper",
    0x00508930: "factory",
    0x00108F60: "app_init",
}


def find_jal_sites(target_va: int):
    """Find jal encodings targeting target_va (MIPS absolute jal)."""
    enc = 0x0C000000 | ((target_va >> 2) & 0x03FFFFFF)
    sites = []
    # scan LOAD file image for the word
    for p in load:
        chunk = data[p["offset"] : p["offset"] + p["filesz"]]
        pos = 0
        needle = struct.pack("<I", enc)
        while True:
            i = chunk.find(needle, pos)
            if i < 0:
                break
            if i % 4 == 0:
                sites.append(p["vaddr"] + i)
            pos = i + 4
    return sites


jal_xrefs = {name: [f"0x{s:08X}" for s in find_jal_sites(va)] for va, name in JAL_TARGETS.items()}

# Also find lui/addiu / sw referencing 0x725F50 (lui 0x72 + addiu/sw 0x5F50)
# Pattern: lui at,0x72 then sw/lw ...,0x5F50(at)
lui72 = struct.pack("<I", 0x3C010072)  # lui at,0x72 — but register may vary
# broader: any lui with imm 0x72
lui_hits_725F50 = []
for p in load:
    chunk = memoryview(data)[p["offset"] : p["offset"] + p["filesz"]]
    for i in range(0, len(chunk) - 8, 4):
        w = struct.unpack_from("<I", chunk, i)[0]
        if (w >> 26) == 0x0F and (w & 0xFFFF) == 0x0072:  # lui rx, 0x72
            rt = (w >> 16) & 0x1F
            # look ahead few instructions for lw/sw with imm 0x5F50 and same base
            for j in range(1, 8):
                if i + j * 4 + 4 > len(chunk):
                    break
                w2 = struct.unpack_from("<I", chunk, i + j * 4)[0]
                op2 = (w2 >> 26) & 0x3F
                rs2 = (w2 >> 21) & 0x1F
                imm2 = w2 & 0xFFFF
                if rs2 == rt and imm2 == 0x5F50 and op2 in (0x23, 0x2B):  # lw / sw
                    va = p["vaddr"] + i + j * 4
                    lui_hits_725F50.append(
                        {
                            "lui_va": f"0x{p['vaddr'] + i:08X}",
                            "access_va": f"0x{va:08X}",
                            "op": "lw" if op2 == 0x23 else "sw",
                            "rt": (w2 >> 16) & 0x1F,
                        }
                    )
                    break

# ---- String extraction ----
# Extract C-strings >= 4 printable chars from LOAD image
string_re = re.compile(rb"[\x20-\x7e]{4,}")
raw_strings = []
off_to_va = []
for p in load:
    base_off = p["offset"]
    base_va = p["vaddr"]
    chunk = data[base_off : base_off + p["filesz"]]
    for m in string_re.finditer(chunk):
        s = m.group().decode("ascii", "replace")
        raw_strings.append((base_va + m.start(), s))


def count_substr(needle: str, case_insensitive: bool = False) -> int:
    n = 0
    if case_insensitive:
        nl = needle.lower()
        for _, s in raw_strings:
            if nl in s.lower():
                n += 1
    else:
        for _, s in raw_strings:
            if needle in s:
                n += 1
    return n


def find_strings_containing(needle: str, limit: int = 40, case_insensitive: bool = False):
    out = []
    nl = needle.lower() if case_insensitive else needle
    for va, s in raw_strings:
        hay = s.lower() if case_insensitive else s
        if nl in hay:
            out.append({"va": f"0x{va:08X}", "s": s[:200]})
            if len(out) >= limit:
                break
    return out


# Keyword hit counts (occurrence of substring across all extracted strings)
KEYWORDS = [
    "Intrinsic Alchemy",
    "Alchemy",
    "ALCHEMY_BASE",
    "alchemy.ini",
    "AlchemyRoot",
    "igFileIO",
    "igUKbd",
    "igUMouse",
    "/usr/local/Alchemy",
    "c:/Alchemy",
    "c:\\Alchemy",
    "IGB",
    ".igb",
    "GFC",
    "GOB",
    "ASSETS.GFC",
    "ASSETS.GOB",
    "Velocity",
    "velocity",
    "loadgate",
    "FCE0",
    "igMalloc",
    "igIGBFile",
    "igFile",
    "igPsx2",
    "STBL",
    "STBLz",
    "_isAlchemyMemory",
    "ABSOLUTE_BASE",
    "APPLICATION_BASE",
    "IOPRP255",
    "MODULES",
]

string_hit_counts = {k: count_substr(k) for k in KEYWORDS}
# also raw byte counts in whole file for critical ones
byte_hit_counts = {}
for k in [
    b"Intrinsic Alchemy",
    b"ALCHEMY_BASE",
    b"alchemy.ini",
    b"igFileIO.irx",
    b"/usr/local/Alchemy/iop/modules",
    b"c:/Alchemy/iop/modules",
    b"ASSETS.GFC",
    b"ASSETS.GOB",
    b"Velocity.igm",
]:
    byte_hit_counts[k.decode("ascii")] = data.count(k)

# Alchemy version string
ver_hits = find_strings_containing("Intrinsic Alchemy", limit=5)
alchemy_version_string = ver_hits[0]["s"] if ver_hits else None

# ig* class-name density: exact-ish tokens matching ig[A-Z]...
ig_class_re = re.compile(r"^ig[A-Za-z][A-Za-z0-9_]*$")
ig_classes = sorted({s for _, s in raw_strings if ig_class_re.match(s)})
# also count strings that START with ig and look like class names embedded in messages
ig_embedded = []
ig_token_re = re.compile(r"\big[A-Za-z][A-Za-z0-9_]*\b")
ig_token_counter = Counter()
for va, s in raw_strings:
    for tok in ig_token_re.findall(s):
        ig_token_counter[tok] += 1

# Prefix buckets
prefix_buckets = Counter()
for name in ig_classes:
    # bucket by first camel chunk after ig
    m = re.match(r"ig([A-Z][a-z0-9]*)", name)
    if m:
        prefix_buckets[m.group(1)] += 1
    else:
        prefix_buckets["_other"] += 1

# FileIO / module path strings
path_needles = [
    "Alchemy/iop",
    "igFileIO",
    "igUKbd",
    "igUMouse",
    ".irx",
    "IOPRP",
    "MODULES",
    "cdrom0",
]
path_catalog = {}
for n in path_needles:
    path_catalog[n] = find_strings_containing(n, limit=80)

# Specific path hits
alchemy_paths = find_strings_containing("Alchemy", limit=100)
irx_strings = [x for x in find_strings_containing(".irx", limit=200)]
igb_paths = find_strings_containing(".igb", limit=80, case_insensitive=True)
gfc_gob = find_strings_containing("ASSETS", limit=40)

# Relocs / imports
reloc_sections = [s for s in sections if s["type"] in (9, 4, 0x700000A0) or "rel" in s["name"].lower()]
dyn_sections = [s for s in sections if s["name"] in (".dynsym", ".dynstr", ".dynamic", ".symtab", ".strtab", ".got", ".interp")]
symtab = next((s for s in sections if s["name"] == ".symtab"), None)
strtab = next((s for s in sections if s["name"] == ".strtab"), None)
sym_count = 0
sample_syms = []
if symtab and strtab and symtab["entsize"]:
    stab = data[strtab["offset"] : strtab["offset"] + strtab["size"]]
    for i in range(0, symtab["size"], symtab["entsize"]):
        st_name, st_value, st_size, st_info, st_other, st_shndx = struct.unpack_from(
            "<IIIBBH", data, symtab["offset"] + i
        )
        if st_name == 0:
            continue
        end = stab.find(b"\x00", st_name)
        name = stab[st_name:end].decode("ascii", "replace")
        sym_count += 1
        if len(sample_syms) < 20:
            sample_syms.append({"name": name, "value": f"0x{st_value:08X}"})

# .comment
comment_sec = next((s for s in sections if s["name"] == ".comment"), None)
comment_text = None
if comment_sec:
    raw = data[comment_sec["offset"] : comment_sec["offset"] + comment_sec["size"]]
    comment_text = b"\n".join(p for p in raw.split(b"\x00") if p).decode("ascii", "replace")

# Velocity / build strings
velocity_hits = find_strings_containing("elocity", limit=30)  # Velocity / velocity
rdy_hits = find_strings_containing("rdy", limit=20)
built_hits = find_strings_containing("built", limit=20, case_insensitive=True)
sep_hits = find_strings_containing("Sep", limit=20)

# Neighbor BSS globals around 725F50
bss_siblings = {}
for name, va in [
    ("725EE0", 0x00725EE0),
    ("725EF0", 0x00725EF0),
    ("725EF8", 0x00725EF8),
    ("725F00", 0x00725F00),
    ("725F50", 0x00725F50),
    ("725C20", 0x00725C20),
]:
    bss_siblings[name] = {"va": f"0x{va:08X}", "in_bss": in_bss(va), "in_file": va_to_off(va) is not None}

# Top ig class prefixes
top_ig = ig_token_counter.most_common(40)

report = {
    "elf_path": str(ELF),
    "size": len(data),
    "entry": f"0x{e_entry:08X}",
    "phdrs": phdrs,
    "sections": [{"name": s["name"], "type": s["type"], "addr": f"0x{s['addr']:08X}", "size": f"0x{s['size']:X}"} for s in sections],
    "comment": comment_text,
    "alchemy_version_string": alchemy_version_string,
    "key_vas": key_va_report,
    "neighbors": neighbors,
    "jal_xrefs": jal_xrefs,
    "lui_hits_725F50": lui_hits_725F50,
    "string_hit_counts": string_hit_counts,
    "byte_hit_counts": byte_hit_counts,
    "ig_class_exact_count": len(ig_classes),
    "ig_class_sample": ig_classes[:80],
    "ig_class_tail": ig_classes[-40:],
    "ig_token_unique": len(ig_token_counter),
    "ig_token_total_occurrences": sum(ig_token_counter.values()),
    "ig_prefix_buckets_top": prefix_buckets.most_common(40),
    "ig_token_top": top_ig,
    "path_catalog_summary": {k: len(v) for k, v in path_catalog.items()},
    "alchemy_path_strings": alchemy_paths[:60],
    "irx_strings": irx_strings[:80],
    "igb_paths": igb_paths[:50],
    "gfc_gob": gfc_gob,
    "velocity_hits": velocity_hits,
    "build_related": rdy_hits + built_hits + sep_hits,
    "reloc_sections": reloc_sections,
    "dyn_sections": dyn_sections,
    "sym_count": sym_count,
    "sample_syms": sample_syms,
    "bss_siblings": bss_siblings,
    "raw_string_count": len(raw_strings),
}

OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("Wrote", OUT_JSON)
print("version:", alchemy_version_string)
print("ig exact classes:", len(ig_classes))
print("ig unique tokens:", len(ig_token_counter))
print("entry:", f"0x{e_entry:08X}")
print("sym_count:", sym_count)
print("jal FCE0 sites:", jal_xrefs.get("FCE0"))
print("725F50 lw/sw sites:", len(lui_hits_725F50))
for k in ["Intrinsic Alchemy", "ALCHEMY_BASE", "alchemy.ini", "igFileIO", "Velocity", "ASSETS.GFC", "ASSETS.GOB"]:
    print(f"  hit[{k}]={string_hit_counts.get(k)}")
