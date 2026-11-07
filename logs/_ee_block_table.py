#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-nax.ram").read_bytes()
nblocks = struct.unpack_from("<I", ee, 0x6F5A80)[0]
nfiles = struct.unpack_from("<I", ee, 0x6F5A88)[0]
ft = struct.unpack_from("<I", ee, 0x6F5A90)[0]
print(f"nblocks={nblocks} nfiles={nfiles} ft={ft:#x}")

# file entry at fonts: search crc
crc = 0xC3994BD8
for i in range(nfiles):
    a = ft + i * 12
    c, s, f = struct.unpack_from("<III", ee, a)
    if c == crc:
        print(f"file[{i}] at {a:#x}: crc={c:#x} size={s:#x} first={f}")
        fonts_i = i
        fonts_first = f
        break
else:
    print("fonts not in EE file table with 12-byte entries")
    # try 16-byte
    for i in range(nfiles):
        a = ft + i * 16
        c, s, f, x = struct.unpack_from("<IIII", ee, a)
        if c == crc:
            print(f"file16[{i}] at {a:#x}: {c:#x} {s:#x} {f} {x:#x}")
            break
    raise SystemExit

# Guess block table location: often just before file table
# GFC on disk: header + blocks*12 + blocks*4 + files*12
# In EE maybe blocks at ft - nblocks*12 or separate pointer

# Search for block 2005 entry: compressed=24211, offset=?, next=2006
# On disk big-endian; in EE likely little-endian
target_comp = 24211
hits = []
for a in range(0x100000, 0x1000000, 4):
    if struct.unpack_from("<I", ee, a)[0] == target_comp:
        nxt = struct.unpack_from("<I", ee, a + 8)[0]
        if nxt == 2006:
            hits.append(a)
print("LE block0-like entries", [hex(h) for h in hits[:10]])
for a in range(0x100000, 0x1000000, 4):
    if struct.unpack_from(">I", ee, a)[0] == target_comp:  # still stored BE?
        nxt = struct.unpack_from(">I", ee, a + 8)[0]
        if nxt == 2006:
            print("BE hit", hex(a))

# dump around ft - 0x100
print("before ft:")
for a in range(ft - 64, ft + 64, 16):
    print(f"{a:08X}: " + " ".join(f"{struct.unpack_from('<I', ee, a+i*4)[0]:08X}" for i in range(4)))
