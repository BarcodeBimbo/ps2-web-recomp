#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-stbl0.ram").read_bytes()
REGS = "r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split()

# Pattern: lw X, 0(obj); lw t9, 0x228(X); jalr t9
print("vtable+0x228 call pattern:")
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 0x23 or (w & 0xFFFF) != 0x228:
        continue
    rt = (w >> 16) & 0x1F
    rs = (w >> 21) & 0x1F
    # look ahead for jalr of rt
    for k in range(1, 6):
        w2 = struct.unpack_from("<I", ee, a + k * 4)[0]
        if ((w2 >> 26) & 0x3F) == 0 and (w2 & 0x3F) == 9:
            rs2 = (w2 >> 21) & 0x1F
            if rs2 == rt:
                print(f"  CALL {a:08X}: lw {REGS[rt]},0x228({REGS[rs]}); jalr @{a+k*4:08X}")
                # show prelude
                for i in range(-6, k + 1):
                    b = a + i * 4
                    w3 = struct.unpack_from("<I", ee, b)[0]
                    op = (w3 >> 26) & 0x3F
                    rs3, rt3, rd3 = (w3 >> 21) & 0x1F, (w3 >> 16) & 0x1F, (w3 >> 11) & 0x1F
                    imm = w3 & 0xFFFF
                    sim = imm - 0x10000 if imm & 0x8000 else imm
                    fn = w3 & 0x3F
                    s = f"    {b:08X}: "
                    if op == 0x23:
                        s += f"lw {REGS[rt3]}, {sim}({REGS[rs3]})"
                    elif op == 0 and fn == 9:
                        s += f"jalr {REGS[rd3]}, {REGS[rs3]}"
                    elif op == 3:
                        s += f"jal 0x{((b&0xF0000000)|((w3&0x3FFFFFF)<<2)):X}"
                    elif op == 9:
                        s += f"addiu {REGS[rt3]}, {REGS[rs3]}, {sim}"
                    else:
                        s += f"{w3:08X}"
                    print(s)

# Search for AddIntcHandler / SetAlarm registering 0x23ED50
# Look for lui/ori of pieces - maybe gp-relative
# Or: the table is RTTI/vtbl and calls use small indices via a dispatcher

# Check if 0x23ED50 is reached via switch/dispatcher at 0x23DF20-style
# Search jalr targets by seeing who has 0x23ED50 in a jump table near code
print("\njump tables containing 0x23ED50:")
for a in range(0x100000, 0x700000, 4):
    if struct.unpack_from("<I", ee, a)[0] != 0x23ED50:
        continue
    # show neighbors
    print(f"  at {a:08X}")
    for i in range(-4, 8):
        print(f"    {a+i*4:08X}: {struct.unpack_from('<I', ee, a+i*4)[0]:08X}")

# Alternative: maybe 0x23ED50 is ONLY in the big vtable and the game calls it through
# a generic "invoke method N" with N in a register. Search for 0x228 as method id immediate
# in a0/a1 before a call
print("\nli/addiu a?, 0x8A (138) or 0x228 near jalr:")
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 9:
        continue
    sim = w & 0xFFFF
    sim = sim - 0x10000 if sim & 0x8000 else sim
    rt = (w >> 16) & 0x1F
    if sim not in (0x8A, 0x228, 138):
        continue
    if rt not in (4, 5, 6, 7, 2):  # a0-a3, v0
        continue
    # nearby jal/jalr
    for k in range(-2, 8):
        w2 = struct.unpack_from("<I", ee, a + k * 4)[0]
        op = (w2 >> 26) & 0x3F
        fn = w2 & 0x3F
        if op == 3 or (op == 0 and fn == 9):
            print(f"  {a:08X} addiu {REGS[rt]}, {sim} near {a+k*4:08X}")
            break

# Disassemble after-gate for Alchemy update calls
print("\n=== after gate 0x4230B0 region looking for 0x10xxxx / 0x23xxxx calls ===")
for a in range(0x4230B0, 0x423400, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 3:
        continue
    tgt = (a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
    if tgt < 0x500000:
        print(f"  {a:08X} jal {tgt:#x}")
