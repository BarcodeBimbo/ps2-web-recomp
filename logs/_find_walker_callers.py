#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-stbl0.ram").read_bytes()
targets = {0x242480, 0x243850, 0x2423C0, 0x241F20}
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 3:
        continue
    tgt = (a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
    if tgt in targets:
        print(f"{a:08X} jal {tgt:#x}")
