#!/usr/bin/env python3
from pathlib import Path
import struct
import sys

sys.path.insert(0, "scripts")
from disc import Image

img = Image(Path("games/b49f2e769315347e8bda839feb705744/disc.iso"))
gfc = gob = None
for path, sector, isdir, size in img.files():
    u = path.upper().replace("\\", "/")
    if u.endswith("ASSETS.GFC") or u.endswith("ASSETS.GFC;1"):
        gfc = (path, sector, size)
    if u.endswith("ASSETS.GOB") or u.endswith("ASSETS.GOB;1"):
        gob = (path, sector, size)
print("GFC", gfc)
print("GOB", gob)

# read first sectors of GFC via Image API
# discover API
print("Image methods", [m for m in dir(img) if not m.startswith("_")])

ee = Path("logs/cnk-live.ram").read_bytes()[:0x2000000]

def find_builds(imm_hi, imm_lo, label):
    count = 0
    for a in range(0x100000, min(0x800000, len(ee)), 4):
        w0, w1 = struct.unpack_from("<II", ee, a)
        if (w0 & 0xFFE0FFFF) == (0x3C000000 | imm_hi) and (w1 & 0xFC00FFFF) == (0x34000000 | imm_lo):
            print(f"{label} at {a:#x} w0={w0:08X} w1={w1:08X}")
            count += 1
            if count >= 12:
                break
    print(label, "count", count)

find_builds(0x0001, 0x2114, "rpc 0x12114")
find_builds(0x7369, 0x6964, "rpc siid")

s = ee.find(b"igFileIO.irx")
print("igFileIO.irx at", hex(s) if s >= 0 else None)
if s >= 0:
    ptr_hits = []
    needle = struct.pack("<I", s)
    start = 0
    while len(ptr_hits) < 30:
        i = ee.find(needle, start)
        if i < 0:
            break
        if i % 4 == 0:
            ptr_hits.append(i)
        start = i + 1
    print("ptrs", [hex(h) for h in ptr_hits])

# Dump memory around string refs that look like code-adjacent data tables
for a in ptr_hits[:10]:
    words = struct.unpack_from("<8I", ee, a - 16)
    print(f"around ptr {a:#x}:", " ".join(f"{w:08X}" for w in words))
