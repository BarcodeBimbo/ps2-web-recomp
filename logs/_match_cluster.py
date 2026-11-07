#!/usr/bin/env python3
from pathlib import Path
import struct
import zlib
import sys

sys.path.insert(0, "scripts")
from disc import Image

ee = Path("logs/cnk-nax.ram").read_bytes()
img = Image(Path("games/b49f2e769315347e8bda839feb705744/disc.iso"))
path, layer, lba, size = img.find("ASSETS.GFC")
gfc = img.read(layer.base + lba, (size + 2047) // 2048)[:size]
_, nblocks, nfiles = struct.unpack(">III", gfc[4:16])
off = 16
blocks = [struct.unpack(">III", gfc[off + i * 12 : off + (i + 1) * 12]) for i in range(nblocks)]
off = 16 + nblocks * 12 + nblocks * 4
files = [struct.unpack(">III", gfc[off + i * 12 : off + (i + 1) * 12]) for i in range(nfiles)]
fonts = next(f for f in files if f[0] == 0xC3994BD8)
print("fonts crc/size/first", hex(fonts[0]), hex(fonts[1]), fonts[2])

path, layer, glba, gsize = img.find("ASSETS.GOB")
ptr = 0x762390
for bi in [fonts[2], blocks[fonts[2]][2]]:
    c, o, n = blocks[bi]
    raw = img.read(layer.base + glba + o // 2048, (c + o % 2048 + 2047) // 2048)
    chunk = raw[o % 2048 : o % 2048 + c]
    print(f"block {bi}: comp={c} next={n} gob_magic={chunk[:8]} ee_magic={ee[ptr:ptr+8]}")
    print(f"  match ee? {chunk == ee[ptr:ptr+c]}")
    print(f"  match head8? {chunk[:8] == ee[ptr:ptr+8]}")
    z = zlib.decompress(chunk[5:])
    print(f"  inflate len={len(z)} head={z[:8].hex()}")

# How much of ee buffer is the first zlib stream?
z = zlib.decompressobj()
out = z.decompress(ee[ptr + 5 : ptr + 0x26000])
print("stream inflate len", len(out), "unused", len(z.unused_data), "used", 0x26000 - 5 - len(z.unused_data))
