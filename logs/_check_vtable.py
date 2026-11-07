#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-stbl0.ram").read_bytes()
obj = struct.unpack_from("<I", ee, 0x6F59D0)[0]
print("6F59D0", hex(obj))
if obj and obj < len(ee):
    vt = struct.unpack_from("<I", ee, obj)[0]
    print("vtable", hex(vt))
    if vt and vt < len(ee):
        for i in range(0, 64, 4):
            m = struct.unpack_from("<I", ee, vt + i)[0]
            print(f"  vt+{i:02X}: {m:08X}")
        m12 = struct.unpack_from("<I", ee, vt + 12)[0]
        print("method+12", hex(m12), "has code range?", 0x100000 <= m12 < 0x700000)

# callers into 0x23ED00-0x23F200
print("\ncallers:")
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 3:
        continue
    tgt = (a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
    if 0x23ED00 <= tgt <= 0x23F200:
        print(f"  {a:08X} -> {tgt:#x}")
