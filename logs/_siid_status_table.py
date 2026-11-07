#!/usr/bin/env python3
import struct
from pathlib import Path

iop = Path("logs/cnk-live.ram").read_bytes()[0x2000000:0x2200000]
ee = Path("logs/cnk-live.ram").read_bytes()[:0x2000000]

ptr = struct.unpack_from("<I", iop, 0xB6830)[0]
print(f"ptr@B6830 = {ptr:#x}")
# dump table
for a in range(0xB6800, 0xB6900, 16):
    print(f"{a:08X}: " + " ".join(f"{struct.unpack_from('<I', iop, a+i)[0]:08X}" for i in range(0,16,4)))

if ptr and ptr < len(iop):
    print(f"\ntable at {ptr:#x}")
    for i in range(0, 0x100, 16):
        print(f"{ptr+i:08X}: " + " ".join(f"{struct.unpack_from('<I', iop, ptr+i+j)[0]:08X}" for j in range(0,16,4)))

# Also dump VVAA BSS stream objects near 0xBEAC0 ret and stream state
print("\n=== VVAA BSS ===")
for a in range(0xBEA00, 0xBF200, 32):
    ws = [struct.unpack_from("<I", iop, a + i)[0] for i in range(0, 32, 4)]
    if any(ws):
        print(f"{a:08X}: " + " ".join(f"{w:08X}" for w in ws))

# Disassemble status264 more completely from live
print("\n=== status264 full ===")
addr = 0xB5700
for i in range(40):
    a = addr + i * 4
    w = struct.unpack_from("<I", iop, a)[0]
    print(f"{a:08X}: {w:08X}")
