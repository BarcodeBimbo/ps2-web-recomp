#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-live.ram").read_bytes()[:0x2000000]

def dump(a, n=16):
    print(f"{a:08X}: " + " ".join(f"{struct.unpack_from('<I', ee, a+i*4)[0]:08X}" for i in range(n)))

print("=== catalog region ===")
for a in range(0x6F59C0, 0x6F5B00, 0x20):
    dump(a, 8)

# file table pointer
ft = struct.unpack_from("<I", ee, 0x6F5A90)[0]  # guess from window
print("candidates around:")
dump(0x6F5A80, 16)

# From pair: at 0x6f5a80: blocks=0x10e7, files=0x726, ptr=0x7727a0
blocks = struct.unpack_from("<I", ee, 0x6F5A80)[0]
files = struct.unpack_from("<I", ee, 0x6F5A88)[0]
ptr = struct.unpack_from("<I", ee, 0x6F5A90)[0]
print(f"blocks={blocks} files={files} ptr={hex(ptr)}")
dump(ptr, 16)

# Each file entry might be 16 or 12 bytes - dump first few and search for logo crc
# Compute crc of gfx/ui path names using zlib crc32 like igfileio
import zlib

def norm(s):
    s = s.lower().replace("/", "\\")
    while s.startswith(".") or s.startswith("\\"):
        s = s[1:]
    return s

names = [
    "gfx/ui/background.igb",
    "gfx/ui/citadel_logo.igb",
    "ui/introtxr.igb",
    "ui/fetextur.igb",
    "logo.igb",
    "fonts.igb",
    "gfx/fonts/fonts.igb",
]
for n in names:
    c = zlib.crc32(norm(n).encode()) & 0xFFFFFFFF
    print(f"crc {n} => {c:08X}")
    # search LE crc in ee
    needle = struct.pack("<I", c)
    hits = []
    start = 0
    while len(hits) < 5:
        i = ee.find(needle, start)
        if i < 0:
            break
        if i % 4 == 0:
            hits.append(i)
        start = i + 1
    print("  hits", [hex(h) for h in hits])

# Inspect block table if present
# Also count how many STBLz and how large loaded asset regions are
print("STBLz offsets", end=" ")
idx = 0
while True:
    i = ee.find(b"STBLz", idx)
    if i < 0:
        break
    # size estimate: look at next STBLz or +256k
    print(hex(i), end=" ")
    idx = i + 1
print()

# Check if 0x7727a0 looks like array of {crc,size,first}
print("\nfile table sample")
for i in range(10):
    a = ptr + i * 12
    crc, size, first = struct.unpack_from("<III", ee, a)
    print(f"  [{i}] crc={crc:08X} size={size} first={first}")
