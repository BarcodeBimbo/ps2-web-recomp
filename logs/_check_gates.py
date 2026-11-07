#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-stbl0.ram").read_bytes()
print("635138", hex(struct.unpack_from("<I", ee, 0x635138)[0]))
print("635130", [hex(struct.unpack_from("<I", ee, 0x635130 + i * 4)[0]) for i in range(8)])

# Find gp from common EE ABI — search recent thread dump or known _gp
# From ELF
elf = Path("games/b49f2e769315347e8bda839feb705744/disc/boot.elf").read_bytes()
# EI_CLASS etc — find .reginfo or _gp symbol roughly via DT
# Check explore for gp in cpu state — look at common gp values used in lui pairs with 8494
# lb v0, -31596(gp) = gp + (-0x7B54) = gp - 31596
# store A3848494 was sb?, offset 0x8494 signed = -31596 yes

# Search code that sets gp: lui gp, imm
print("\nlui gp sites (early):")
for a in range(0x100000, 0x120000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) == 0xF and ((w >> 16) & 0x1F) == 28:
        print(f"  {a:08X}: lui gp, {w & 0xFFFF:#x}")

# From nax dump thread, check if we saved gp — scan for pointer table
# Typical CNK gp around 0x6Fxxxx or 0x70xxxx
for gp in [0x700000, 0x6F0000, 0x710000, 0x6E0000, 0x780000, 0x6C0000]:
    addr = (gp - 31596) & 0xFFFFFFFF
    if addr < len(ee):
        print(f"gp={gp:#x} flag@{addr:#x} = {ee[addr]}")

# Disassemble more of 0x242480 function - the gate
print("\n=== 0x242480 continue ===")
REGS = "r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split()
for i in range(0, 90):
    a = 0x242480 + i * 4
    w = struct.unpack_from("<I", ee, a)[0]
    op = (w >> 26) & 0x3F
    rs, rt, rd = (w >> 21) & 0x1F, (w >> 16) & 0x1F, (w >> 11) & 0x1F
    imm = w & 0xFFFF
    sim = imm - 0x10000 if imm & 0x8000 else imm
    fn = w & 0x3F
    s = f"{a:08X}: "
    if op == 3:
        s += f"jal 0x{((a&0xF0000000)|((w&0x3FFFFFF)<<2)):X}"
    elif op == 5:
        s += f"bne {REGS[rs]}, {REGS[rt]}, 0x{a+4+sim*4:X}"
    elif op == 4:
        s += f"beq {REGS[rs]}, {REGS[rt]}, 0x{a+4+sim*4:X}"
    elif op == 9:
        s += f"addiu {REGS[rt]}, {REGS[rs]}, {sim}"
    elif op == 0xF:
        s += f"lui {REGS[rt]}, {imm:#x}"
    elif op == 0x23:
        s += f"lw {REGS[rt]}, {sim}({REGS[rs]})"
    elif op == 0x20:
        s += f"lb {REGS[rt]}, {sim}({REGS[rs]})"
    elif op == 0x24:
        s += f"lbu {REGS[rt]}, {sim}({REGS[rs]})"
    elif op == 0x28:
        s += f"sb {REGS[rt]}, {sim}({REGS[rs]})"
    elif op == 0x2B:
        s += f"sw {REGS[rt]}, {sim}({REGS[rs]})"
    elif op == 0 and fn == 8:
        s += f"jr {REGS[rs]}"
    elif op == 0 and fn == 9:
        s += f"jalr {REGS[rd]}, {REGS[rs]}"
    else:
        s += f"{w:08X}"
    print(s)
