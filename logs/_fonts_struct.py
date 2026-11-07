#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-nax.ram").read_bytes()

def dump(a, n=16):
    print(f"{a:08X}: " + " ".join(f"{struct.unpack_from('<I', ee, a+i*4)[0]:08X}" for i in range(n)))

print("fonts crc site:")
dump(0x7B3600, 32)

# find all refs to crc value as pointer targets - structure start
crc = 0xC3994BD8
for a in range(0x7B3000, 0x7B4000, 4):
    if struct.unpack_from("<I", ee, a)[0] == crc:
        print("crc at", hex(a))
        dump(a - 0x20, 24)

# Heap around 762390 - is there a header before the STBLz?
print("\nbefore STBLz:")
dump(0x762370, 12)

# Check 6F5A00 region meaning - filled count?
print("\n6F5A00 region:")
dump(0x6F59E0, 20)

# Look at cdvd read destinations recently - search for 762390 in IOP/EE shared
print("\nany other STBLz that matches fonts block0?")
import sys, zlib
sys.path.insert(0, "scripts")
from disc import Image
img = Image(Path("games/b49f2e769315347e8bda839feb705744/disc.iso"))
path, layer, lba, size = img.find("ASSETS.GFC")
gfc = img.read(layer.base + lba, (size + 2047) // 2048)[:size]
_, nblocks, nfiles = struct.unpack(">III", gfc[4:16])
off = 16
blocks = [struct.unpack(">III", gfc[off+i*12:off+(i+1)*12]) for i in range(nblocks)]
off = 16 + nblocks*12 + nblocks*4
files = [struct.unpack(">III", gfc[off+i*12:off+(i+1)*12]) for i in range(nfiles)]
fonts = next(f for f in files if f[0]==0xC3994BD8)
c,o,n = blocks[fonts[2]]
path, layer, glba, _ = img.find("ASSETS.GOB")
raw = img.read(layer.base+glba+o//2048, (c+o%2048+2047)//2048)
chunk0 = raw[o%2048:o%2048+c]
idx = 0
hits = []
while True:
    i = ee.find(chunk0[:32], idx)
    if i < 0: break
    hits.append(i)
    idx = i+1
print("block0 chunk hits", [hex(h) for h in hits])
z0 = zlib.decompress(chunk0[5:])
idx = ee.find(z0[:32])
print("block0 inflated hit", hex(idx) if idx>=0 else None)
