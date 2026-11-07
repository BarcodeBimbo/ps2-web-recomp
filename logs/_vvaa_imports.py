#!/usr/bin/env python3
"""Resolve VVAA IRX imports and find what cmd4 status calls."""
from pathlib import Path
import struct

p = Path(r"C:\PS2Recomp\logs\vvaa.irx").read_bytes()
# IOPMOD section
e_shoff = struct.unpack_from("<I", p, 0x20)[0]
e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", p, 0x2E)
print("shoff", hex(e_shoff), "shnum", e_shnum)

def sh_name(idx):
    shstr = e_shoff + e_shstrndx * e_shentsize
    strs_off = struct.unpack_from("<I", p, shstr + 0x10)[0]
    name_off = struct.unpack_from("<I", p, e_shoff + idx * e_shentsize)[0]
    end = p.index(b"\0", strs_off + name_off)
    return p[strs_off + name_off : end]

for i in range(e_shnum):
    off = e_shoff + i * e_shentsize
    name_off, typ, flags, addr, soff, size = struct.unpack_from("<IIIIII", p, off)
    name = sh_name(i)
    print(f"sec{i} {name} type={typ} addr={hex(addr)} off={hex(soff)} size={hex(size)}")

# .iopmod at typically section
# Imports: after iopmod header
# Look for 'libsd' 'ioman' strings
for s in [b"libsd", b"ioman", b"threadman", b"sifman", b"sifcmd", b"stdio", b"sysclib", b"intrman", b"loadcore", b"cdvdman", b"timrman"]:
    i = p.find(s)
    print(s, hex(i) if i >= 0 else None)

# Dump import table: IOPIRX typically has import tables with 0x41e00000 magic already seen at module base
# At runtime base 0xB9400, imports patched. From live IOP RAM, read jal targets at cmd4 site.

iop = Path("logs/cnk-live.ram").read_bytes()[0x2000000 : 0x2200000]
# At 0xB9ABC: jal was 0C000095 in file; at runtime it should be relocated
for addr in [0xB9ABC, 0xB9AE0, 0xB9AC0, 0xB9910, 0xB9950]:
    w = struct.unpack_from("<I", iop, addr)[0]
    if (w >> 26) & 0x3F == 3:
        target = ((w & 0x3FFFFFF) << 2) | (addr & 0xF0000000)
        print(f"{addr:08X}: jal {target:#x} raw={w:08X}")
        # disasm a few at target
        for i in range(8):
            tw = struct.unpack_from("<I", iop, target + i * 4)[0]
            print(f"  {target+i*4:08X}: {tw:08X}")
    else:
        print(f"{addr:08X}: {w:08X} not jal")
