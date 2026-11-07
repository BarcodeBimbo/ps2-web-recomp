#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-nax.ram").read_bytes()[:0x2000000]
entries = Path("games/b49f2e769315347e8bda839feb705744/entries.txt").read_text(errors="ignore")

# zlib version string area
base = ee.find(b"1.1.3")
print("1.1.3 at", hex(base) if base >= 0 else None)
for name in [b"inflate", b"inflateEnd", b"inflateInit", b"zlibVersion", b"adler32"]:
    i = ee.find(name)
    print(name, hex(i) if i >= 0 else None)

# Any absolute pointer to 0x635150 in data/code
needle = struct.pack("<I", 0x635150)
hits = [i for i in range(0, 0x800000, 4) if ee[i : i + 4] == needle]
print("ptr hits to 0x635150", [hex(h) for h in hits[:30]], "count", len(hits))

# Search code for addiu building 0x635150
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 0xF:
        continue
    imm = w & 0xFFFF
    if imm not in (0x63, 0x635):
        continue
    rt = (w >> 16) & 0x1F
    for j in range(1, 8):
        w2 = struct.unpack_from("<I", ee, a + j * 4)[0]
        if ((w2 >> 26) & 0x3F) == 9 and ((w2 >> 21) & 0x1F) == rt:
            off = w2 & 0xFFFF
            sim = off - 0x10000 if off & 0x8000 else off
            ea = ((imm << 16) + sim) & 0xFFFFFFFF
            if 0x635000 <= ea <= 0x636000:
                print(f"code ref {a:08X} -> {ea:08X}")

# Look for zlib-looking function prologues near common PS2 inflate
# inflateInit2_ often nearby; search for addiu a?, r0, 15 near jal
print("\nwindowBits=15 sites:")
count = 0
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 9:
        continue
    if (w & 0xFFFF) != 15:
        continue
    if ((w >> 21) & 0x1F) != 0:
        continue
    # nearby jal
    for j in range(-4, 8):
        w2 = struct.unpack_from("<I", ee, a + j * 4)[0]
        if ((w2 >> 26) & 0x3F) == 3:
            tgt = ((a + j * 4) & 0xF0000000) | ((w2 & 0x3FFFFFF) << 2)
            print(f"  {a:08X} imm15; jal@{a+j*4:08X} -> {tgt:08X}")
            count += 1
            break
    if count > 40:
        break

# Check entries coverage for candidate inflate ranges
cands = []
for line in entries.splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        addr = int(line.split()[0], 16) if line[0:2] != "0x" else int(line, 16)
    except Exception:
        try:
            addr = int(line, 16)
        except Exception:
            continue
    if 0x630000 <= addr <= 0x650000 or 0x340000 <= addr <= 0x360000:
        cands.append(addr)
print("\nentries in ranges", len(cands), "sample", [hex(x) for x in cands[:20]])

# STBL magic compare in code: look for bytes 'STBL' as immediate loads
# lui + ori building 0x5354424C or load of 'S','T','B','L'
stbl = 0x5354424C  # big endian STBL as word? on EE often compared bytewise
print("\nsearch for 'STBL' as ASCII in code immediates via memcmp pattern")
# Find addresses of "STBLz"/"STBL0" string constants
for sig in [b"STBLz", b"STBL0", b"STBL"]:
    idx = 0
    while True:
        i = ee.find(sig, idx)
        if i < 0 or i > 0x700000:
            break
        if i < 0x100000:
            print(f"  const {sig} @ {i:08X}")
        idx = i + 1
        if idx > 0x100000 and i > 0x100000:
            break
