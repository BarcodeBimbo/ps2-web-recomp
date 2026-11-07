#!/usr/bin/env python3
import struct
from pathlib import Path

iop = Path("logs/cnk-live.ram").read_bytes()[0x2000000:0x2200000]
# Import stub table near 0xB964C
print("=== import stubs ===")
for addr in range(0xB9640, 0xB9700, 8):
    w = struct.unpack_from("<I", iop, addr)[0]
    if (w >> 26) & 0x3F == 2:  # j
        target = (addr & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
        print(f"{addr:08X}: j {target:#x}")
        # identify module by address ranges from load log
        # LIBSD 0x20000, etc.
    else:
        print(f"{addr:08X}: {w:08X}")

# Follow cmd4 status fills: jal 0xb9654 and 0xb9664
for label, stub in [("status254", 0xB9654), ("status264", 0xB9664)]:
    w = struct.unpack_from("<I", iop, stub)[0]
    target = (stub & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
    print(f"\n{label} -> {target:#x}")
    for i in range(20):
        a = target + i * 4
        tw = struct.unpack_from("<I", iop, a)[0]
        print(f"  {a:08X}: {tw:08X}")

# Find 0x500C production: search LIBSD module for addiu/ori 0x500C
libsd_base = 0x20000
# module 1 and 15 both LIBSD - check both
for base, size in [(0x20000, 0x5A00), (0xB1F00, 0x5A00)]:
    print(f"\nscan libsd @{base:#x}")
    for off in range(0, size, 4):
        w = struct.unpack_from("<I", iop, base + off)[0]
        if (w & 0xFFFF) == 0x500C and (w >> 26) in (8, 9, 0xD, 0xF):
            print(f"  {base+off:08X}: {w:08X}")
