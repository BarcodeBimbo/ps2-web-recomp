#!/usr/bin/env python3
"""Load ASSETS.GFC from ISO and compare to EE buffer; inspect igFileIO EE callers."""
from pathlib import Path
import struct
import zlib

# Minimal ISO9660 path walk for one file
iso_path = Path(r"C:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc.iso")
iso = iso_path.read_bytes()  # 3.2GB - too big!
print("iso size", iso_path.stat().st_size)

# Read only via mmap
import mmap
with iso_path.open("rb") as f:
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

    def read_sector(lba, n=1):
        # ISO: sector 16+ ; assume 2048 user data, raw 2048 mode1
        return mm[lba * 2048 : (lba + n) * 2048]

    # Find primary volume
    pvd = read_sector(16)
    assert pvd[0:6] == b"\x01CD001", pvd[0:8]
    root = pvd[156:190]
    root_lba = struct.unpack_from("<I", root, 2)[0]
    root_size = struct.unpack_from("<I", root, 10)[0]
    print("root", root_lba, root_size)

    def list_dir(lba, size, prefix=""):
        data = read_sector(lba, (size + 2047) // 2048)[:size]
        off = 0
        out = []
        while off < len(data):
            length = data[off]
            if length == 0:
                off = (off + 2048) & ~2047
                if off >= len(data):
                    break
                continue
            loc = struct.unpack_from("<I", data, off + 2)[0]
            sz = struct.unpack_from("<I", data, off + 10)[0]
            flags = data[off + 25]
            name_len = data[off + 32]
            name = data[off + 33 : off + 33 + name_len]
            if name not in (b"\x00", b"\x01"):
                n = name.split(b";")[0].decode("ascii", "replace")
                out.append((n, loc, sz, flags))
            off += length
        return out

    entries = list_dir(root_lba, root_size)
    for n, loc, sz, flags in entries:
        if "ASSET" in n or "MUSIC" == n or n.endswith(".GFC") or n.endswith(".GOB"):
            print("ROOT", n, loc, sz, hex(flags))

    # find ASSETS.GFC
    gfc = next(e for e in entries if e[0].startswith("ASSETS.GFC"))
    print("GFC", gfc)
    head = read_sector(gfc[1], 2)[:64]
    print("GFC head", head[:32].hex())
    print("be32", [struct.unpack(">I", head[i : i + 4])[0] for i in range(0, 16, 4)])

    # Compare with EE buffer
    ee = Path(r"C:\PS2Recomp\logs\cnk-live.ram").read_bytes()[:0x2000000]
    buf = ee[0x7504C0 : 0x7504C0 + 64]
    print("EE  buf", buf[:32].hex())
    print("match head?", buf[:16] == head[:16])

    # Find where GFC signature lives in EE RAM
    sig = head[:4]
    idx = 0
    hits = []
    while len(hits) < 10:
        i = ee.find(sig, idx)
        if i < 0:
            break
        hits.append(i)
        idx = i + 1
    print("GFC sig hits in EE", [hex(h) for h in hits])

    # Also search for first 16 bytes
    i = ee.find(head[:16])
    print("full GFC head in EE at", hex(i) if i >= 0 else None)

# Analyze EE callers of rpc 0x12114 — search for lui/ori building 0x12114
ram = Path(r"C:\PS2Recomp\logs\cnk-live.ram").read_bytes()[:0x2000000]
count = 0
for a in range(0x100000, 0x620000, 4):
    w0, w1 = struct.unpack_from("<II", ram, a)
    # lui rt, 1 ; ori rt, rt, 0x2114  => 0x12114
    if (w0 & 0xFFE0FFFF) == 0x3C000001 and (w1 & 0xFC00FFFF) == 0x34002114:
        rt = (w0 >> 16) & 0x1F
        print(f"build 0x12114 at {a:#x} rt={rt} w0={w0:08X} w1={w1:08X}")
        count += 1
        if count > 15:
            break
print("done builds", count)

# Search for immediate 19 used near CallRpc patterns — hard; dump around string igFileIO.irx
s = ram.find(b"igFileIO.irx")
print("igFileIO.irx at", hex(s))
# find pointers to that string
ptr_hits = []
for a in range(0, len(ram) - 4, 4):
    if struct.unpack_from("<I", ram, a)[0] == s:
        ptr_hits.append(a)
        if len(ptr_hits) >= 20:
            break
print("ptrs to string", [hex(h) for h in ptr_hits])
