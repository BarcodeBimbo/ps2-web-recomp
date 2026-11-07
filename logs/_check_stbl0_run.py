#!/usr/bin/env python3
from pathlib import Path
import struct
import zlib

ee = Path("logs/cnk-stbl0.ram").read_bytes()
print("len", len(ee))
ptr = struct.unpack_from("<I", ee, 0x6F5AA8)[0]
cap = struct.unpack_from("<I", ee, 0x6F5AB0)[0]
want = struct.unpack_from("<I", ee, 0x6F5B30)[0]
print(f"ptr={ptr:#x} cap={cap:#x} want={want:#x}")
print("magic", ee[ptr : ptr + 8])
print("want>=0x1000", want >= 0x1000)
# try inflate
try:
    z = zlib.decompress(ee[ptr + 5 : ptr + cap])
    print("inflate ok", len(z))
except Exception as e:
    print("inflate fail", e)
    # try with unused
    d = zlib.decompressobj()
    try:
        out = d.decompress(ee[ptr + 5 : ptr + min(cap, 0x10000)])
        print("partial", len(out), "unused", len(d.unused_data))
    except Exception as e2:
        print("partial fail", e2)
