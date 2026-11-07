#!/usr/bin/env python3
"""Determine whether walker call sites are reachable and what drives them."""
from pathlib import Path
import struct

ee = Path("logs/cnk-stbl0.ram").read_bytes()
REGS = "r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split()


def dis(addr, n):
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


# Scan 0x23EEF0 through 0x23F120 for control flow to walker
print("=== 0x23EEF0 .. walker ===")
dis(0x23EEF0, 140)

print("\n=== any branch/jal/j targeting 0x23ED50-0x23EDEC ===")
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    op = (w >> 26) & 0x3F
    if op in (2, 3):
        tgt = (a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
        if 0x23ED50 <= tgt <= 0x23EDEC:
            print(f"  {a:08X} {'j' if op == 2 else 'jal'} {tgt:#x}")
    elif op in (4, 5, 6, 7):
        imm = w & 0xFFFF
        sim = imm - 0x10000 if imm & 0x8000 else imm
        tgt = a + 4 + sim * 4
        if 0x23ED50 <= tgt <= 0x23EDEC:
            print(f"  {a:08X} branch {tgt:#x}")

# Also check jr-table / function pointer stores of 0x23ED50
print("\n=== RAM pointers to 0x23ED50 / 0x242480 / 0x23F070 ===")
for needle in (0x0023ED50, 0x00242480, 0x0023F070, 0x0023F050, 0x0023EDAC):
    hits = []
    for a in range(0, min(len(ee) - 4, 0x2000000), 4):
        if struct.unpack_from("<I", ee, a)[0] == needle:
            hits.append(a)
            if len(hits) >= 12:
                break
    print(hex(needle), [hex(h) for h in hits[:12]], "count~", len(hits))

# Look at 0x42365C iSignalSema(45) handler context
print("\n=== iSignalSema45 handler ===")
dis(0x423600, 50)

# TIM0 handler registration - search AddIntcHandler for cause 9
# Also dump what 0x705C00 increment path looks like near 42365C
