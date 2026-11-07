#!/usr/bin/env python3
import struct
from pathlib import Path

ee = Path("logs/cnk-live.ram").read_bytes()[:0x2000000]

def dump_around(a, before=32, after=48):
    start = a - before
    print(f"\n=== around {a:#x} ===")
    for off in range(start, a + after, 16):
        ws = " ".join(f"{struct.unpack_from('<I', ee, off+i)[0]:08X}" for i in range(0, 16, 4))
        mark = "<<" if off <= a < off + 16 else "  "
        print(f"{mark}{off:08X}: {ws}")

for name, crc in [
    ("fonts", 0xC3994BD8),
    ("background", 0xF2EC1F44),
    ("citadel_logo", 0x88C2823C),
    ("introtxr", 0x33340283),
]:
    a = next(a for a in range(0, len(ee) - 4, 4) if struct.unpack_from("<I", ee, a)[0] == crc)
    dump_around(a)

# SIID EE status copy
print("\n=== SIID EE status @155F140 / 155F948 ===")
dump_around(0x155F140, 0, 64)
dump_around(0x155F948, 16, 64)

# Check if any large decompressed buffers look like igb (often start with version/magic)
# Search for common igAlchemy igb magic if known - try 'igb' / 0x00626769
for magic in [b"igb\x00", b"IGB\x00", b"\x01\x00\x00\x00ig"]:
    idx = 0
    hs = []
    while len(hs) < 5:
        i = ee.find(magic, idx)
        if i < 0:
            break
        hs.append(i)
        idx = i + 1
    print("magic", magic, [hex(h) for h in hs])
