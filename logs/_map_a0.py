#!/usr/bin/env python3
import struct
from pathlib import Path

iop = Path("logs/cnk-live.ram").read_bytes()[0x2000000:0x2200000]
for a0 in [0x2240, 0x2200, 0x2100, 0x1D00, 0x1700, 0x2241, 0x2250, 0x2260, 0x22C0, 0x2300, 0x2340]:
    v0 = (a0 >> 6) & 0x3FC
    addr = 0xB0000 + v0 + 0x6830
    ptr = struct.unpack_from("<I", iop, addr)[0]
    print(f"a0={a0:#06x} table@{addr:#x} ptr={ptr:#x}")

print("table slice B6880:")
for a in range(0xB6880, 0xB68E0, 4):
    print(f"{a:08X}: {struct.unpack_from('<I', iop, a)[0]:08X}")

# Also simulate what the fill loop uses - from disasm ori with 0x2240 and s4 counter
print("\nfill pattern s4=0..N with 0x2240:")
for s4 in range(0, 16):
    a0 = s4 | 0x2240
    v0 = (a0 >> 6) & 0x3FC
    bit0 = a0 & 1
    addr = 0xB0000 + v0 + 0x6830
    # plus bit0<<10 added to pointer after load
    ptr = struct.unpack_from("<I", iop, addr)[0]
    ptr2 = ptr + (bit0 << 10)
    print(f"  s4={s4} a0={a0:#x} ptr={ptr:#x} +bit={ptr2:#x}")
