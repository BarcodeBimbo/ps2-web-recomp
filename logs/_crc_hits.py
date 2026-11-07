#!/usr/bin/env python3
import struct
from pathlib import Path

ee = Path("logs/cnk-live.ram").read_bytes()[:0x2000000]
hits = [a for a in range(0, len(ee) - 4, 4) if struct.unpack_from("<I", ee, a)[0] == 0x500C]
print("EE 0x500C", len(hits), [hex(h) for h in hits[:20]])

for name, crc in [
    ("fonts", 0xC3994BD8),
    ("background", 0xF2EC1F44),
    ("citadel_logo", 0x88C2823C),
    ("introtxr", 0x33340283),
    ("fetextur", 0x60C01EE2),
]:
    hs = [a for a in range(0, len(ee) - 4, 4) if struct.unpack_from("<I", ee, a)[0] == crc]
    print(name, hex(crc), [hex(h) for h in hs[:8]])

print("path@6F5AE0", ee[0x6F5AE0 : 0x6F5AE0 + 80])
print("catalog:")
print(" ".join(f"{struct.unpack_from('<I', ee, 0x6F5A80 + i*4)[0]:08X}" for i in range(48)))

# Is 0x762390 fonts data? check size after inflate header
print("STBLz0", ee[0x762390 : 0x762390 + 16])
print("STBLz1", ee[0x787000 : 0x787000 + 16])
