#!/usr/bin/env python3
"""Supplement: FileIO/IGB class catalog + pointer density."""
from __future__ import annotations

import json
import re
import struct
from pathlib import Path

data = Path(r"C:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc\boot.elf").read_bytes()
LOAD_OFF = 0x80
LOAD_VA = 0x00100000
LOAD_FSZ = 0x5F2000
chunk = data[LOAD_OFF : LOAD_OFF + LOAD_FSZ]
string_re = re.compile(rb"[\x20-\x7e]{4,}")
ig2 = re.compile(r"^ig[A-Za-z0-9_]+$")

classes_u = sorted(
    {m.group().decode("ascii") for m in string_re.finditer(chunk) if ig2.match(m.group().decode("ascii"))}
)
tok = set()
for m in string_re.finditer(chunk):
    for t in re.findall(r"ig[A-Za-z0-9_]+", m.group().decode("ascii")):
        tok.add(t)
camel = sorted(t for t in tok if re.match(r"^ig[A-Z]", t))

fileish = sorted(
    c
    for c in classes_u
    if re.search(
        r"File|IGB|Stream|Archive|IO|Rpc|Iop|Gob|MetaObject|MetaField|VisualContext|Display|MemoryPool|Malloc",
        c,
    )
)
psx = sorted(c for c in classes_u if c.startswith("igPsx2"))

needles = {
    "ver": b"Intrinsic Alchemy",
    "ALCHEMY_BASE": b"ALCHEMY_BASE",
    "ini": b"alchemy.ini",
    "igFileIO": b"igFileIO.irx",
    "unix_iop": b"/usr/local/Alchemy/iop/modules",
    "win_iop": b"c:/Alchemy/iop/modules",
    "igIGBFile": b"igIGBFile\x00",
    "igFile": b"igFile\x00",
    "Velocity.igm": b"Velocity.igm",
    "IOPRP": b"cdrom0:\\IOPRP255.IMG;1",
    "AlchemyRoot": b"$(AlchemyRoot)",
    "_isAlchemyMemory": b"_isAlchemyMemory",
    "rdy": b"Built by rdy",
    "igUKbd": b"igUKbd.irx",
    "igUMouse": b"igUMouse.irx",
    "sonyModulePath": b"sonyModulePath",
    "ABSOLUTE_BASE": b"ABSOLUTE_BASE",
    "APPLICATION_BASE": b"APPLICATION_BASE",
}

vas = {}
for k, n in needles.items():
    i = data.find(n)
    if i < 0:
        vas[k] = None
    elif LOAD_OFF <= i < LOAD_OFF + LOAD_FSZ:
        vas[k] = {
            "va": f"0x{LOAD_VA + (i - LOAD_OFF):08X}",
            "preview": data[i : i + min(len(n) + 48, 96)].split(b"\x00")[0].decode("ascii", "replace"),
        }
    else:
        vas[k] = {"file_off": i}

va_of = {
    LOAD_VA + m.start(): m.group().decode()
    for m in string_re.finditer(chunk)
    if ig2.match(m.group().decode())
}
ptrs = 0
pointed = set()
for i in range(0, len(chunk) - 4, 4):
    w = struct.unpack_from("<I", chunk, i)[0]
    if w in va_of:
        ptrs += 1
        pointed.add(va_of[w])

# MODULES / config neighborhood
i = data.find(b"sonyModulePath")
config_snip = data[i - 120 : i + 220].decode("ascii", "replace") if i >= 0 else None

# .igb path count
igb_paths = []
for m in string_re.finditer(chunk):
    s = m.group().decode("ascii")
    if ".igb" in s.lower():
        igb_paths.append({"va": f"0x{LOAD_VA + m.start():08X}", "s": s[:160]})

out = {
    "ig_whole_string_classes": len(classes_u),
    "ig_unique_tokens": len(tok),
    "ig_camel_tokens": len(camel),
    "fileish_classes": fileish,
    "psx2_classes": psx,
    "key_string_vas": vas,
    "abs_ptrs_to_class_strings": ptrs,
    "unique_classes_with_abs_ptr": len(pointed),
    "config_snip": config_snip,
    "igb_path_count": len(igb_paths),
    "classes_full": classes_u,
}
Path(r"C:\PS2Recomp\verification\recovery\_tmp_w1_cnk_elf_walk2.json").write_text(
    json.dumps(out, indent=2), encoding="utf-8"
)
print("classes", len(classes_u), "tokens", len(tok), "camel", len(camel))
print("fileish", len(fileish), "psx2", len(psx))
print("ptrs", ptrs, "pointed", len(pointed))
print("igb paths", len(igb_paths))
for k, v in vas.items():
    print(k, v)
