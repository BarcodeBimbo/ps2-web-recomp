#!/usr/bin/env python3
from pathlib import Path
import struct
import zlib
import sys

sys.path.insert(0, "scripts")
from disc import Image

ee = Path("logs/cnk-stbl0.ram").read_bytes()
print("flag byte", ee[0x6F5B20], "word", hex(struct.unpack_from("<I", ee, 0x6F5B20)[0]))
print("B24", hex(struct.unpack_from("<I", ee, 0x6F5B24)[0]))
print("B28", hex(struct.unpack_from("<I", ee, 0x6F5B28)[0]))
print("B30", hex(struct.unpack_from("<I", ee, 0x6F5B30)[0]))
print("B34", hex(struct.unpack_from("<I", ee, 0x6F5B34)[0]))
ptr = struct.unpack_from("<I", ee, 0x6F5AA8)[0]
print("magic", ee[ptr : ptr + 8])

img = Image(Path("games/b49f2e769315347e8bda839feb705744/disc.iso"))
path, layer, lba, size = img.find("ASSETS.GFC")
gfc = img.read(layer.base + lba, (size + 2047) // 2048)[:size]
_, nblocks, nfiles = struct.unpack(">III", gfc[4:16])
off = 16
blocks = [struct.unpack(">III", gfc[off + i * 12 : off + (i + 1) * 12]) for i in range(nblocks)]
off = 16 + nblocks * 12 + nblocks * 4
files = [struct.unpack(">III", gfc[off + i * 12 : off + (i + 1) * 12]) for i in range(nfiles)]
fonts = next(f for f in files if f[0] == 0xC3994BD8)
c, o, n = blocks[fonts[2]]
path, layer, glba, _ = img.find("ASSETS.GOB")
raw = img.read(layer.base + glba + o // 2048, (c + o % 2048 + 2047) // 2048)
chunk = raw[o % 2048 : o % 2048 + c]
print("scratch matches block0?", ee[ptr : ptr + c] == chunk)
z0 = zlib.decompress(chunk[5:])
print("inflated block0 in ee?", ee.find(z0[:32]))
print("AC0", hex(struct.unpack_from("<I", ee, 0x6F5AC0)[0]))

# gp-relative flag
# search for who stores to the flag byte
print("\n6F5B20 region:")
for a in range(0x6F5B00, 0x6F5B80, 16):
    print(f"{a:08X}: " + " ".join(f"{struct.unpack_from('<I', ee, a+i*4)[0]:08X}" for i in range(4)))
