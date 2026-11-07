#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-live.ram").read_bytes()[:0x2000000]
print(ee[0x6A6900:0x6A6A40])
idx = 0
while True:
    i = ee.find(b"zlib", idx)
    if i < 0 or i > 0x700000:
        break
    print(hex(i), ee[i : i + 64])
    idx = i + 1
for s in [
    b"memory error",
    b"buffer error",
    b"version error",
    b"incorrect",
    b"need dict",
    b"stream error",
    b"data error",
    b"inflateEnd",
    b"inflateInit",
]:
    i = ee.find(s)
    print(s, hex(i) if i >= 0 else None)

print("load slot:")
for a in range(0x6F5A80, 0x6F5C80, 16):
    print(f"{a:08X}: " + " ".join(f"{struct.unpack_from('<I', ee, a+i)[0]:08X}" for i in range(0, 16, 4)))

# Look for error/status near STBLz pointer 0x762390
ptr = 0x762390
hits = [a for a in range(0, len(ee) - 4, 4) if struct.unpack_from("<I", ee, a)[0] == ptr]
print("ptrs to STBLz", [hex(h) for h in hits[:20]])
for h in hits[:5]:
    print(f" context {h:#x}: " + " ".join(f"{struct.unpack_from('<I', ee, h-16+i)[0]:08X}" for i in range(0, 48, 4)))
