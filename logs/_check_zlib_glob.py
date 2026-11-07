#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-nax.ram").read_bytes()


def dump(a, n=8):
    ws = [f"{struct.unpack_from('<I', ee, a + i * 4)[0]:08X}" for i in range(n)]
    print(f"{a:08X}:", " ".join(ws))


for a in [0x6F58E0, 0x6F58E8, 0x6F59D0, 0x6F59C0, 0x6F5A00, 0x6F5AA0]:
    dump(a, 8)

p = struct.unpack_from("<I", ee, 0x6F58E8)[0]
print("6F58E8 ptr", hex(p))
if p and p < 0x2000000:
    dump(p, 16)
    # follow vtable-ish
    v0 = struct.unpack_from("<I", ee, p)[0]
    print("vtable?", hex(v0))
    if v0 and v0 < 0x2000000:
        dump(v0, 12)
