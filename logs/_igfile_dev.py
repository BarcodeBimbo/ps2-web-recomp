#!/usr/bin/env python3
import struct
from pathlib import Path

ee = Path("logs/cnk-live.ram").read_bytes()[:0x2000000]
base = 0x6B8F18
print(ee[base : base + 128])
for off in range(0x20, 0xA0, 4):
    w = struct.unpack_from("<I", ee, base + off)[0]
    print(f"+{off:X}: {w:08X}")
    if 0x100000 < w < 0x800000:
        words = struct.unpack_from("<8I", ee, w)
        print("  ->", " ".join(f"{x:08X}" for x in words))

for a in (0x539EF0, 0x539EDC, 0x539EE4, 0x539F00, 0x53A000):
    print("====", hex(a))
    print(" ".join(f"{struct.unpack_from('<I', ee, a + i * 4)[0]:08X}" for i in range(16)))
    for i in range(12):
        f = struct.unpack_from("<I", ee, a + i * 4)[0]
        if 0x100000 <= f < 0x620000:
            print(f"  fn[{i}]={f:08X} instr={struct.unpack_from('<I', ee, f)[0]:08X}")

# Follow 0x742ED0 object more carefully — Alchemy meta object
obj = 0x742ED0
print("\n=== object 742ED0 deep ===")
for i in range(32):
    w = struct.unpack_from("<I", ee, obj + i * 4)[0]
    note = ""
    if 0x100000 <= w < 0x800000:
        # peek
        peek = ee[w : w + 32]
        if b"ig" in peek or b"File" in peek or b"cdrom" in peek:
            note = repr(peek[:32])
        elif struct.unpack_from("<I", ee, w)[0] & 0xFC000000 in (0x27BD0000, 0x3C010000, 0x27BD0000):
            note = "code?"
    print(f"{obj+i*4:08X}: {w:08X} {note}")

# Check 742948 / 742968 / 743160 pointed from object
for a in (0x742948, 0x742968, 0x743160, 0x743208, 0x743068, 0x742EC8):
    print(f"\n--- {a:08X} ---")
    print(" ".join(f"{struct.unpack_from('<I', ee, a + i * 4)[0]:08X}" for i in range(12)))
    chunk = ee[a : a + 64]
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    print(asc)
