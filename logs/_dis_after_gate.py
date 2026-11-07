#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-stbl0.ram").read_bytes()
REGS = "r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split()


def dis(addr, n):
    print(f"=== {addr:#x} ===")
    for i in range(n):
        a = addr + i * 4
        w = struct.unpack_from("<I", ee, a)[0]
        op = (w >> 26) & 0x3F
        rs, rt, rd = (w >> 21) & 0x1F, (w >> 16) & 0x1F, (w >> 11) & 0x1F
        imm = w & 0xFFFF
        sim = imm - 0x10000 if imm & 0x8000 else imm
        fn = w & 0x3F
        s = f"{a:08X}: "
        if op == 2:
            s += f"j 0x{((a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)):X}"
        elif op == 3:
            s += f"jal 0x{((a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)):X}"
        elif op == 5:
            s += f"bne {REGS[rs]}, {REGS[rt]}, 0x{a + 4 + sim * 4:X}"
        elif op == 4:
            s += f"beq {REGS[rs]}, {REGS[rt]}, 0x{a + 4 + sim * 4:X}"
        elif op == 9:
            s += f"addiu {REGS[rt]}, {REGS[rs]}, {sim}"
        elif op == 0xF:
            s += f"lui {REGS[rt]}, {imm:#x}"
        elif op == 0x23:
            s += f"lw {REGS[rt]}, {sim}({REGS[rs]})"
        elif op == 0x2B:
            s += f"sw {REGS[rt]}, {sim}({REGS[rs]})"
        elif op == 0 and fn == 8:
            s += f"jr {REGS[rs]}"
        elif op == 0 and fn == 9:
            s += f"jalr {REGS[rd]}, {REGS[rs]}"
        elif op == 0 and fn == 0xC:
            s += "syscall"
        else:
            s += f"{w:08X}"
        print(s)


dis(0x423060, 120)

# Check finish pending / deferred state implications:
# Gate: 705C00=890 vs 6542A0=893 — need 3 more FINISH signals
# Why stopped? Look at FINISH log - last ones MASKED
print("\nCSR/IMR analysis from log already known")

# Check if 0x2422E0 / asset stream state would re-enter walker
# Dump stream state at 6F5B20 etc
base = 0x6F5B20
print("walker slot:")
for i in range(0, 0x40, 4):
    print(f"  {base+i:08X}: {struct.unpack_from('<I', ee, base+i)[0]:08X}")
print("flag bytes:", ee[0x6F5B20], "enable@6F2084:", ee[0x6F2084])
print("STBLz@762390:", ee[0x762390:0x762398])
# Inflated fonts destination?
print("fonts area 7B0000:", ee[0x7B0000:0x7B0010].hex())
