#!/usr/bin/env python3
from pathlib import Path
import struct
import zlib
import sys

sys.path.insert(0, "scripts")
from disc import Image

ee = Path("logs/cnk-nax.ram").read_bytes()[:0x2000000]
if len(ee) < 0x100000:
    ee = Path("logs/cnk-live.ram").read_bytes()[:0x2000000]

def dump(a, n=16):
    print(f"{a:08X}: " + " ".join(f"{struct.unpack_from('<I', ee, a + i * 4)[0]:08X}" for i in range(n)))

dump(0x6F5A80, 32)
ptr = struct.unpack_from("<I", ee, 0x6F5AA8)[0]
cap = struct.unpack_from("<I", ee, 0x6F5AB0)[0]
dest = struct.unpack_from("<I", ee, 0x6F5AB8)[0]
want = struct.unpack_from("<I", ee, 0x6F5B30)[0]
print(f"ptr={ptr:#x} cap={cap:#x} dest={dest:#x} want={want:#x}")
print("src magic", ee[ptr : ptr + 8], "STBLz count", ee[ptr : ptr + cap].count(b"STBLz"))
print("dest head", ee[dest : dest + 32].hex(), "nonzero", sum(1 for b in ee[dest : dest + 0x20000] if b))

img = Image(Path("games/b49f2e769315347e8bda839feb705744/disc.iso"))
path, layer, lba, size = img.find("ASSETS.GFC")
gfc = img.read(layer.base + lba, (size + 2047) // 2048)[:size]
gob_size, nblocks, nfiles = struct.unpack(">III", gfc[4:16])
off = 16
blocks = []
for i in range(nblocks):
    blocks.append(struct.unpack(">III", gfc[off : off + 12]))
    off += 12
off += nblocks * 4
files = []
for i in range(nfiles):
    files.append(struct.unpack(">III", gfc[off : off + 12]))
    off += 12
fonts = next(f for f in files if f[0] == 0xC3994BD8)
print("fonts", [hex(x) for x in fonts])
b = fonts[2]
ids = []
while b != 0x7FFF and len(ids) < 20:
    ids.append(b)
    c, o, n = blocks[b]
    b = n
print("block ids", ids)
# inflate first cluster from EE buffer
chunk = ee[ptr:]
assert chunk[:5] == b"STBLz"
# find compressed size from block table
c0, o0, n0 = blocks[fonts[2]]
print("block0 comp", c0)
z = zlib.decompress(ee[ptr + 5 : ptr + c0])
print("inflate len", len(z), "match dest?", ee[dest : dest + 32] == z[:32])
print("z0", z[:16].hex(), "dest0", ee[dest : dest + 16].hex())
# second STBLz in buffer?
i2 = ee.find(b"STBLz", ptr + 5)
print("second STBLz", hex(i2) if i2 >= 0 else None, "offset", i2 - ptr if i2 >= 0 else None)
