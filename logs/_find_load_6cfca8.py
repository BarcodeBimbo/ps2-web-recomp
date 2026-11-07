#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-stbl0.ram").read_bytes()
REGS = "r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split()

# 0x6CFCA8 can be reached as:
# lui x, 0x6D; lw y, -856(x)  because 0x6D0000 - 856 = 0x6CFCA8
# lui x, 0x6C; lw y, 0xFCA8(x)
off_6d = (0x6CFCA8 - 0x6D0000) & 0xFFFF
off_6c = (0x6CFCA8 - 0x6C0000) & 0xFFFF
print(f"offs 6D:{off_6d:#x} 6C:{off_6c:#x}")

for base in (0x6C, 0x6D, 0x6E, 0x6F):
    for off in range(0xFC00, 0xFD00):
        addr = (base << 16) + (off if off < 0x8000 else off - 0x10000)
        if addr != 0x6CFCA8:
            continue
        print("match base", hex(base), "off", hex(off))

# Broader: any lw that computes 0x6CFCA8
print("\nlw sites targeting 0x6CFCA8:")
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 0xF:
        continue
    hi = w & 0xFFFF
    rt = (w >> 16) & 0x1F
    if hi not in (0x6C, 0x6D):
        continue
    for j in range(1, 6):
        w2 = struct.unpack_from("<I", ee, a + j * 4)[0]
        if ((w2 >> 26) & 0x3F) != 0x23:
            continue
        if ((w2 >> 21) & 0x1F) != rt:
            continue
        imm = w2 & 0xFFFF
        sim = imm - 0x10000 if imm & 0x8000 else imm
        ea = ((hi << 16) + sim) & 0xFFFFFFFF
        if ea == 0x6CFCA8:
            print(f"  {a:08X} -> lw @{a+j*4:08X}")

# Also: lw from vtable register with offset, where vtable was loaded from 0x6F59D0
# Search for pattern loading object then vtable then big offset near 0x200+
print("\nPossible method-index dispatchers (lw t9, N(vtable) for N>=0x200):")
count = 0
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 0x23:
        continue
    imm = w & 0xFFFF
    if imm < 0x200 or imm > 0x300:
        continue
    rt = (w >> 16) & 0x1F
    rs = (w >> 21) & 0x1F
    # jalr of that reg soon?
    for k in range(1, 5):
        w2 = struct.unpack_from("<I", ee, a + k * 4)[0]
        if ((w2 >> 26) & 0x3F) == 0 and (w2 & 0x3F) == 9 and ((w2 >> 21) & 0x1F) == rt:
            print(f"  {a:08X}: lw {REGS[rt]}, {imm:#x}({REGS[rs]}); jalr")
            count += 1
            break
    if count > 30:
        print("...")
        break

# Check 0x2425D0 / 0x2422E0 — maybe they schedule the pump
print("\n=== 0x2422E0 start ===")
for i in range(20):
    a = 0x2422E0 + i * 4
    w = struct.unpack_from("<I", ee, a)[0]
    op = (w >> 26) & 0x3F
    if op == 3:
        print(f"{a:08X}: jal 0x{((a&0xF0000000)|((w&0x3FFFFFF)<<2)):X}")
    elif op == 0 and (w & 0x3F) == 8:
        print(f"{a:08X}: jr")
        break
    else:
        print(f"{a:08X}: {w:08X}")

# Look at alarm list / intc handlers in dump if we can find them
# Handler addresses often stored — search for 0x4235xx near FINISH handler
print("\nintc-like pointers to 0x423xxx:")
for a in range(0x700000, 0x800000, 4):
    v = struct.unpack_from("<I", ee, a)[0]
    if 0x423500 <= v <= 0x423700:
        print(f"  {a:08X}: {v:08X}")
