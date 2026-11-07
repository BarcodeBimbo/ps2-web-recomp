#!/usr/bin/env python3
"""Find virtual calls to vtable+0x228 (Alchemy pump 0x23ED50)."""
from pathlib import Path
import struct

ee = Path("logs/cnk-stbl0.ram").read_bytes()
REGS = "r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split()

# Pattern: lw t9, 0x228(reg) or lw t9, 552(reg)
print("lw ?, 0x228(reg):")
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 0x23:
        continue
    imm = w & 0xFFFF
    if imm != 0x228:
        continue
    rt = (w >> 16) & 0x1F
    rs = (w >> 21) & 0x1F
    print(f"  {a:08X}: lw {REGS[rt]}, 0x228({REGS[rs]})")
    # show nearby
    for i in range(-4, 8):
        b = a + i * 4
        w2 = struct.unpack_from("<I", ee, b)[0]
        op = (w2 >> 26) & 0x3F
        rs2, rt2, rd2 = (w2 >> 21) & 0x1F, (w2 >> 16) & 0x1F, (w2 >> 11) & 0x1F
        imm2 = w2 & 0xFFFF
        sim = imm2 - 0x10000 if imm2 & 0x8000 else imm2
        fn = w2 & 0x3F
        s = f"    {b:08X}: "
        if op == 3:
            s += f"jal 0x{((b & 0xF0000000) | ((w2 & 0x3FFFFFF) << 2)):X}"
        elif op == 0x23:
            s += f"lw {REGS[rt2]}, {sim}({REGS[rs2]})"
        elif op == 0 and fn == 9:
            s += f"jalr {REGS[rd2]}, {REGS[rs2]}"
        elif op == 9:
            s += f"addiu {REGS[rt2]}, {REGS[rs2]}, {sim}"
        elif op == 0xF:
            s += f"lui {REGS[rt2]}, {imm2:#x}"
        else:
            s += f"{w2:08X}"
        print(s)

# Also common: addiu to make offset then lw
print("\naddiu producing 0x228 then lw:")
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 9:
        continue
    sim = w & 0xFFFF
    sim = sim - 0x10000 if sim & 0x8000 else sim
    if sim != 0x228:
        continue
    print(f"  {a:08X}: addiu {REGS[(w>>16)&0x1F]}, {REGS[(w>>21)&0x1F]}, 0x228")

# Who loads 0x6F59D0 and then calls large offsets?
print("\nrefs to 0x6F59D0 (22992 from 0x6F0000):")
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 0xF or (w & 0xFFFF) != 0x6F:
        continue
    for j in range(1, 5):
        w2 = struct.unpack_from("<I", ee, a + j * 4)[0]
        if ((w2 >> 26) & 0x3F) == 0x23 and (w2 & 0xFFFF) == 22992:
            rt = (w2 >> 16) & 0x1F
            print(f"  {a:08X} load into {REGS[rt]}")
            # next 12 instrs looking for jalr
            for k in range(j, j + 16):
                w3 = struct.unpack_from("<I", ee, a + k * 4)[0]
                op = (w3 >> 26) & 0x3F
                fn = w3 & 0x3F
                rs3, rt3, rd3 = (w3 >> 21) & 0x1F, (w3 >> 16) & 0x1F, (w3 >> 11) & 0x1F
                imm3 = w3 & 0xFFFF
                sim3 = imm3 - 0x10000 if imm3 & 0x8000 else imm3
                b = a + k * 4
                if op == 0x23:
                    print(f"    {b:08X}: lw {REGS[rt3]}, {sim3}({REGS[rs3]})")
                elif op == 0 and fn == 9:
                    print(f"    {b:08X}: jalr {REGS[rd3]}, {REGS[rs3]}")
                elif op == 3:
                    print(f"    {b:08X}: jal 0x{((b & 0xF0000000) | ((w3 & 0x3FFFFFF) << 2)):X}")

# Disassemble 0x23EEA0 (adjacent vtable method) and see call pattern from game loop
print("\n=== 0x23EEA0 (vtable neighbor) ===")
for i in range(30):
    a = 0x23EEA0 + i * 4
    w = struct.unpack_from("<I", ee, a)[0]
    op = (w >> 26) & 0x3F
    if op == 3:
        print(f"{a:08X}: jal 0x{((a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)):X}")
    elif op == 0 and (w & 0x3F) == 8:
        print(f"{a:08X}: jr")
        break
    elif op == 9 and ((w >> 16) & 0x1F) == 29:
        sim = w & 0xFFFF
        sim = sim - 0x10000 if sim & 0x8000 else sim
        print(f"{a:08X}: addiu sp,{sim}")
    else:
        print(f"{a:08X}: {w:08X}")
