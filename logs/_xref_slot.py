#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-nax.ram").read_bytes()[:0x2000000]
# Find lw/sw that use base built to 0x6F5Axx
hits = []
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 0xF:
        continue
    imm = w & 0xFFFF
    if imm not in (0x6F, 0x70, 0x76, 0x7A, 0x7B):
        continue
    rt = (w >> 16) & 0x1F
    for j in range(1, 12):
        w2 = struct.unpack_from("<I", ee, a + j * 4)[0]
        op2 = (w2 >> 26) & 0x3F
        if op2 == 9 and ((w2 >> 21) & 0x1F) == rt:
            off = w2 & 0xFFFF
            sim = off - 0x10000 if off & 0x8000 else off
            ea = ((imm << 16) + sim) & 0xFFFFFFFF
            if 0x6F5A00 <= ea <= 0x6F5C00 or ea in (0x762390, 0x7AF300, 0x7B3638):
                hits.append((a, ea, j))
        # also lw/sw with base=rt and immediate offset forming address? 
print("absolute refs", len(hits))
for h in hits[:40]:
    print(f"  {h[0]:08X} -> {h[1]:08X}")

# Search for lw of 0x762390 as immediate through lui 0x76
print("\nrefs near 0x762390:")
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 0xF:
        continue
    if (w & 0xFFFF) != 0x76:
        continue
    rt = (w >> 16) & 0x1F
    for j in range(1, 8):
        w2 = struct.unpack_from("<I", ee, a + j * 4)[0]
        if ((w2 >> 26) & 0x3F) == 9 and ((w2 >> 21) & 0x1F) == rt:
            off = w2 & 0xFFFF
            sim = off - 0x10000 if off & 0x8000 else off
            ea = ((0x76 << 16) + sim) & 0xFFFFFFFF
            if ea == 0x762390:
                print(f"  {a:08X}")
