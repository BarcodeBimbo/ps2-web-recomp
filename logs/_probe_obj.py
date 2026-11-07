#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-nax.ram").read_bytes()

def u32(a):
    return struct.unpack_from("<I", ee, a)[0]

obj = 0x7AF300
print("scanning 0x70 object for EE pointers:")
for off in range(0, 0x200, 4):
    v = u32(obj + off)
    if 0x100000 <= v < 0x2000000 and (v & 3) == 0:
        head = ee[v : v + 8]
        print(f"  +{off:03X}: {v:08X} head={head[:5]} words={[hex(u32(v+i*4)) for i in range(4)]}")

# Also check if any pointer near load slot points to a buffer of size ~0x13BAC
print("\nload-slot neighborhood pointers:")
for a in range(0x6F5A80, 0x6F5C00, 4):
    v = u32(a)
    if 0x100000 <= v < 0x2000000 and (v & 3) == 0:
        print(f"  {a:08X}: {v:08X}")

# Search for allocation size 0x13BAC immediates in code
print("\ncode with imm 0x13bac / 0x13bb0 / 0x14000:")
for a in range(0x300000, 0x400000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 9:
        continue
    imm = w & 0xFFFF
    if imm in (0x3BAC, 0x3BB0, 0x4000, 0x13BAC & 0xFFFF):
        # need lui for high part
        print(f"  {a:08X}: addiu imm={imm:#x}")
