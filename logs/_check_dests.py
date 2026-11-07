#!/usr/bin/env python3
from pathlib import Path
import struct
import zlib
import sys

sys.path.insert(0, "scripts")
from disc import Image

ee = Path("logs/cnk-nax.ram").read_bytes()

img = Image(Path("games/b49f2e769315347e8bda839feb705744/disc.iso"))
_,_,lba,size = img.find("ASSETS.GFC")
gfc = img.read(img.find("ASSETS.GFC")[1].base + lba, (size + 2047) // 2048)[:size]
# fix find usage
path, layer, lba, size = Image(Path("games/b49f2e769315347e8bda839feb705744/disc.iso")).find("ASSETS.GFC")
gfc = img.read(layer.base + lba, (size + 2047) // 2048)[:size]
_, nblocks, nfiles = struct.unpack(">III", gfc[4:16])
off = 16
blocks = [struct.unpack(">III", gfc[off + i * 12 : off + (i + 1) * 12]) for i in range(nblocks)]
off = 16 + nblocks * 12 + nblocks * 4
files = [struct.unpack(">III", gfc[off + i * 12 : off + (i + 1) * 12]) for i in range(nfiles)]
fonts = next(f for f in files if f[0] == 0xC3994BD8)
c, o, n = blocks[fonts[2]]
_,_,glba,_ = img.find("ASSETS.GOB")
# proper
path, layer, glba, gsize = img.find("ASSETS.GOB")
raw = img.read(layer.base + glba + o // 2048, (c + o % 2048 + 2047) // 2048)
z = zlib.decompress(raw[o % 2048 + 5 : o % 2048 + c])
print("z len", len(z), "head", z[:16].hex())

for dest in [0x7AF300, 0x7A2820, 0x7504C0, 0x751CD0, 0x752340]:
    head = ee[dest : dest + 16]
    match = ee[dest : dest + 32] == z[:32]
    # search z in neighborhood
    window = ee[dest : dest + 0x20000]
    idx = window.find(z[:32])
    print(f"dest {dest:#x}: head={head[:8].hex()} match32={match} find_in_128k={idx} nonzero={sum(1 for b in window if b)}")

# search entire EE for inflated fonts
idx = ee.find(z[:32])
print("fonts inflate anywhere", hex(idx) if idx >= 0 else None)

# What's the object at 7AF300?
print("7AF300 as words:")
for i in range(0, 0x80, 16):
    ws = [f"{struct.unpack_from('<I', ee, 0x7AF300 + i + j)[0]:08X}" for j in range(0, 16, 4)]
    print(f"  +{i:02X}: {' '.join(ws)}")

print("7A2820 as words:")
for i in range(0, 0x40, 16):
    ws = [f"{struct.unpack_from('<I', ee, 0x7A2820 + i + j)[0]:08X}" for j in range(0, 16, 4)]
    print(f"  +{i:02X}: {' '.join(ws)}")
