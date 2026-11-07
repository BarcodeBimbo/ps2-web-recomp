#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-stbl0.ram").read_bytes()

for a in range(0x23EDAC, 0x23E800, -4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) == 9 and ((w >> 16) & 0x1F) == 29 and ((w >> 21) & 0x1F) == 29:
        sim = w & 0xFFFF
        sim = sim - 0x10000 if sim & 0x8000 else sim
        if sim < 0:
            print(f"prolog at {a:#x} addiu sp,{sim}")
            break

targets = set()
print("jal into 0x23ED00-0x23F200:")
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 3:
        continue
    tgt = (a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
    if 0x23ED00 <= tgt <= 0x23F200:
        print(f"  {a:08X} jal {tgt:#x}")
        targets.add(tgt)
print("unique", [hex(t) for t in sorted(targets)])

print("direct jal 0x239F00:")
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 3:
        continue
    tgt = (a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
    if tgt == 0x239F00:
        print(f"  {a:08X}")

print("refs to 0x705C18 (lui 0x70 + lw/sw 0x5C18):")
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 0xF or (w & 0xFFFF) != 0x70:
        continue
    for j in range(1, 6):
        w2 = struct.unpack_from("<I", ee, a + j * 4)[0]
        op = (w2 >> 26) & 0x3F
        imm = w2 & 0xFFFF
        sim = imm - 0x10000 if imm & 0x8000 else imm
        if op in (0x23, 0x2B) and sim == 0x5C18:
            kind = "lw" if op == 0x23 else "sw"
            print(f"  {a:08X} lui + {a + j * 4:08X} {kind}")
            break

# Disassemble around 0x10F370 caller of 0x23eef0
REGS = "r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split()


def dis(addr, n=40):
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
        if op == 3:
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


dis(0x10F340, 40)
dis(0x23EEE0, 40)
dis(0x23ED20, 30)

# Who jal 0x23ED80-ish function starts?
print("\ncallers of 0x23ED40/80 region function starts:")
for tgt in [0x23ED40, 0x23ED80, 0x23EDA0, 0x23EDF0, 0x23EEF0, 0x23F050, 0x23F070]:
    hits = []
    for a in range(0x100000, 0x700000, 4):
        w = struct.unpack_from("<I", ee, a)[0]
        if ((w >> 26) & 0x3F) != 3:
            continue
        t = (a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
        if t == tgt:
            hits.append(a)
    print(hex(tgt), [hex(h) for h in hits])
