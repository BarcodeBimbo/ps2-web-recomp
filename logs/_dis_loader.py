#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-nax.ram").read_bytes()[:0x2000000]
REGS = "r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split()


def dis(addr, n=80):
    print(f"\n=== {addr:#x} ===")
    for i in range(n):
        a = addr + i * 4
        w = struct.unpack_from("<I", ee, a)[0]
        op = (w >> 26) & 0x3F
        rs, rt, rd = (w >> 21) & 0x1F, (w >> 16) & 0x1F, (w >> 11) & 0x1F
        imm = w & 0xFFFF
        sim = imm - 0x10000 if imm & 0x8000 else imm
        fn = w & 0x3F
        s = f"{a:08X}: {w:08X}  "
        if op == 3:
            s += f"jal 0x{((a&0xF0000000)|((w&0x3FFFFFF)<<2)):X}"
        elif op == 2:
            s += f"j 0x{((a&0xF0000000)|((w&0x3FFFFFF)<<2)):X}"
        elif op == 5:
            s += f"bne {REGS[rs]}, {REGS[rt]}, 0x{a+4+sim*4:X}"
        elif op == 4:
            s += f"beq {REGS[rs]}, {REGS[rt]}, 0x{a+4+sim*4:X}"
        elif op == 6:
            s += f"blez {REGS[rs]}, 0x{a+4+sim*4:X}"
        elif op == 7:
            s += f"bgtz {REGS[rs]}, 0x{a+4+sim*4:X}"
        elif op == 9:
            s += f"addiu {REGS[rt]}, {REGS[rs]}, {sim}"
        elif op == 8:
            s += f"addi {REGS[rt]}, {REGS[rs]}, {sim}"
        elif op == 0xF:
            s += f"lui {REGS[rt]}, {imm:#x}"
        elif op == 0xD:
            s += f"ori {REGS[rt]}, {REGS[rs]}, {imm:#x}"
        elif op == 0xC:
            s += f"andi {REGS[rt]}, {REGS[rs]}, {imm:#x}"
        elif op == 0x23:
            s += f"lw {REGS[rt]}, {sim}({REGS[rs]})"
        elif op == 0x2B:
            s += f"sw {REGS[rt]}, {sim}({REGS[rs]})"
        elif op == 0x20:
            s += f"lb {REGS[rt]}, {sim}({REGS[rs]})"
        elif op == 0x24:
            s += f"lbu {REGS[rt]}, {sim}({REGS[rs]})"
        elif op == 0 and fn == 8:
            s += f"jr {REGS[rs]}"
        elif op == 0 and fn == 9:
            s += f"jalr {REGS[rd]}, {REGS[rs]}"
        elif op == 0 and fn == 0x21:
            s += f"addu {REGS[rd]}, {REGS[rs]}, {REGS[rt]}"
        elif op == 0 and fn == 0x23:
            s += f"subu {REGS[rd]}, {REGS[rs]}, {REGS[rt]}"
        elif op == 0 and fn == 0x2A:
            s += f"slt {REGS[rd]}, {REGS[rs]}, {REGS[rt]}"
        elif op == 0 and fn == 0x25:
            s += f"or {REGS[rd]}, {REGS[rs]}, {REGS[rt]}"
        elif op == 0 and fn == 0:
            s += f"sll {REGS[rd]}, {REGS[rt]}, {(w>>6)&0x1F}"
        else:
            s += f"op{op:02x}/{fn:02x}"
        print(s)


for a in [0x2423C0, 0x243850, 0x243B40, 0x243BE0]:
    dis(a, 60)
