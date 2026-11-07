#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-stbl0.ram").read_bytes()
# lui gp + ori gp, gp, imm
for a in range(0x100000, 0x200000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 0xF or ((w >> 16) & 0x1F) != 28:
        continue
    imm_hi = w & 0xFFFF
    for j in range(1, 6):
        w2 = struct.unpack_from("<I", ee, a + j * 4)[0]
        op2 = (w2 >> 26) & 0x3F
        if op2 == 0xD and ((w2 >> 21) & 0x1F) == 28 and ((w2 >> 16) & 0x1F) == 28:  # ori
            gp = ((imm_hi << 16) | (w2 & 0xFFFF)) & 0xFFFFFFFF
            fa = (gp - 31596) & 0xFFFFFFFF
            print(f"ori-gp {a:#x} -> {gp:#x} flag@{fa:#x}={ee[fa] if fa < len(ee) else '?'}")
        if op2 == 9 and ((w2 >> 21) & 0x1F) == 28 and ((w2 >> 16) & 0x1F) == 28:
            off = w2 & 0xFFFF
            sim = off - 0x10000 if off & 0x8000 else off
            gp = ((imm_hi << 16) + sim) & 0xFFFFFFFF
            fa = (gp - 31596) & 0xFFFFFFFF
            print(f"addiu-gp {a:#x} -> {gp:#x} flag@{fa:#x}={ee[fa] if fa < len(ee) else '?'}")

# From ELF second load segment, search for _gp in symbol-less way:
# value at known CRT address 0x1000xx
print("\nfirst 64 insns:")
for i in range(32):
    a = 0x100000 + i * 4
    w = struct.unpack_from("<I", ee, a)[0]
    print(f"{a:08X}: {w:08X}")
