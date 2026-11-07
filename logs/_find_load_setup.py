#!/usr/bin/env python3
"""Find code that stores pointer 0x762390 / writes load-slot fields."""
from pathlib import Path
import struct

ee = Path("logs/cnk-nax.ram").read_bytes()[:0x2000000]

# Find lui/addiu forming 0x6F5AA8 / 0x6F5AA0 / 0x6F5AB0
targets = {
    0x6F5AA0,
    0x6F5AA8,
    0x6F5AB0,
    0x6F5AB8,
    0x6F5B20,
    0x6F5B30,
    0x762390,
    0x7AF300,
}
print("code refs to load-slot addresses:")
for a in range(0x300000, 0x450000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 0xF:
        continue
    imm = w & 0xFFFF
    rt = (w >> 16) & 0x1F
    for j in range(1, 10):
        w2 = struct.unpack_from("<I", ee, a + j * 4)[0]
        op2 = (w2 >> 26) & 0x3F
        if op2 == 9 and ((w2 >> 21) & 0x1F) == rt:
            off = w2 & 0xFFFF
            sim = off - 0x10000 if off & 0x8000 else off
            ea = ((imm << 16) + sim) & 0xFFFFFFFF
            if ea in targets:
                print(f"  {a:08X}+{j*4:X} -> {ea:08X}")
        if op2 == 0x2B and ((w2 >> 21) & 0x1F) == rt:  # sw rt_data, off(base_reg=rt from lui?)
            pass

# Broader: any sw of immediate-built address near 0x35xxxx gob
print("\nstores near fonts path string builder:")
# path at 0x6F5AE0 = ".ps2\\gfx\\fonts\\fonts.igb"
path = ee[0x6F5AE0 : 0x6F5AE0 + 40]
print("path bytes", path)

# Find xrefs to 0x6F5AE0
for a in range(0x300000, 0x450000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 0xF:
        continue
    imm = w & 0xFFFF
    if imm != 0x6F:
        continue
    rt = (w >> 16) & 0x1F
    for j in range(1, 8):
        w2 = struct.unpack_from("<I", ee, a + j * 4)[0]
        if ((w2 >> 26) & 0x3F) == 9 and ((w2 >> 21) & 0x1F) == rt:
            off = w2 & 0xFFFF
            sim = off - 0x10000 if off & 0x8000 else off
            ea = ((imm << 16) + sim) & 0xFFFFFFFF
            if 0x6F5A80 <= ea <= 0x6F5C00:
                print(f"  {a:08X} -> {ea:08X}")
