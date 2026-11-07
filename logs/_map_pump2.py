#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-stbl0.ram").read_bytes()
REGS = "r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split()


def dis(addr, n=50):
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


dis(0x23ED40, 8)
dis(0x23DF20, 40)

# Find all jal/j to 0x23ED50 (actual pump with stack)
print("\nrefs to 0x23ED50:")
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    op = (w >> 26) & 0x3F
    if op not in (2, 3):
        continue
    tgt = (a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
    if tgt == 0x23ED50:
        print(f"  {a:08X} {'j' if op == 2 else 'jal'}")

# Function containing 0x23F094
for a in range(0x23F094, 0x23EE00, -4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) == 9 and ((w >> 16) & 0x1F) == 29 and ((w >> 21) & 0x1F) == 29:
        sim = w & 0xFFFF
        sim = sim - 0x10000 if sim & 0x8000 else sim
        if sim < 0:
            print(f"\n0x23F094 func prolog {a:#x}")
            dis(a, 20)
            # callers of that prolog
            print("callers:")
            for b in range(0x100000, 0x700000, 4):
                w2 = struct.unpack_from("<I", ee, b)[0]
                if ((w2 >> 26) & 0x3F) != 3:
                    continue
                t = (b & 0xF0000000) | ((w2 & 0x3FFFFFF) << 2)
                if t == a:
                    print(f"  {b:08X}")
            break

# Trace 0x23EC78 region - callers of pump trampoline
print("\n=== around 0x23EC60 ===")
dis(0x23EC40, 50)

# Who calls functions that call 0x23ED40?
print("\ncallers of 0x23EC?? that lead to pump - find parent of 0x23EC78")
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 3:
        continue
    tgt = (a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
    if 0x23EC00 <= tgt <= 0x23ED3C:
        print(f"  {a:08X} jal {tgt:#x}")
