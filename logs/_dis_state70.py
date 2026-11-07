#!/usr/bin/env python3
"""Find Alchemy load-state machine around 0x70 and decompress call sites."""
from pathlib import Path
import struct

ee = Path("logs/cnk-nax.ram").read_bytes()[:0x2000000]
REGS = "r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split()


def dis(addr, n=40):
    for i in range(n):
        a = addr + i * 4
        w = struct.unpack_from("<I", ee, a)[0]
        op = (w >> 26) & 0x3F
        rs = (w >> 21) & 0x1F
        rt = (w >> 16) & 0x1F
        rd = (w >> 11) & 0x1F
        imm = w & 0xFFFF
        simm = imm - 0x10000 if imm & 0x8000 else imm
        fn = w & 0x3F
        s = f"{a:08X}: {w:08X}  "
        if op == 0 and fn == 0x0D:
            s += "break"
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
        elif op == 0 and fn == 0x2B:
            s += f"sltu {REGS[rd]}, {REGS[rs]}, {REGS[rt]}"
        elif op == 0 and fn == 0x24:
            s += f"and {REGS[rd]}, {REGS[rs]}, {REGS[rt]}"
        elif op == 0 and fn == 0x25:
            s += f"or {REGS[rd]}, {REGS[rs]}, {REGS[rt]}"
        elif op == 0 and fn == 0x27:
            s += f"nor {REGS[rd]}, {REGS[rs]}, {REGS[rt]}"
        elif op == 0 and fn == 0:
            s += f"sll {REGS[rd]}, {REGS[rt]}, {(w>>6)&0x1F}"
        elif op == 0 and fn == 2:
            s += f"srl {REGS[rd]}, {REGS[rt]}, {(w>>6)&0x1F}"
        elif op == 0 and fn == 3:
            s += f"sra {REGS[rd]}, {REGS[rt]}, {(w>>6)&0x1F}"
        elif op == 2:
            s += f"j 0x{((a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)):X}"
        elif op == 3:
            s += f"jal 0x{((a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)):X}"
        elif op == 4:
            s += f"beq {REGS[rs]}, {REGS[rt]}, 0x{a+4+simm*4:X}"
        elif op == 5:
            s += f"bne {REGS[rs]}, {REGS[rt]}, 0x{a+4+simm*4:X}"
        elif op == 6:
            s += f"blez {REGS[rs]}, 0x{a+4+simm*4:X}"
        elif op == 7:
            s += f"bgtz {REGS[rs]}, 0x{a+4+simm*4:X}"
        elif op == 8:
            s += f"addi {REGS[rt]}, {REGS[rs]}, {simm}"
        elif op == 9:
            s += f"addiu {REGS[rt]}, {REGS[rs]}, {simm}"
        elif op == 0xA:
            s += f"slti {REGS[rt]}, {REGS[rs]}, {simm}"
        elif op == 0xB:
            s += f"sltiu {REGS[rt]}, {REGS[rs]}, {simm}"
        elif op == 0xC:
            s += f"andi {REGS[rt]}, {REGS[rs]}, {imm:#x}"
        elif op == 0xD:
            s += f"ori {REGS[rt]}, {REGS[rs]}, {imm:#x}"
        elif op == 0xE:
            s += f"xori {REGS[rt]}, {REGS[rs]}, {imm:#x}"
        elif op == 0xF:
            s += f"lui {REGS[rt]}, {imm:#x}"
        elif op == 0x20:
            s += f"lb {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x21:
            s += f"lh {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x23:
            s += f"lw {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x24:
            s += f"lbu {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x25:
            s += f"lhu {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x28:
            s += f"sb {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x29:
            s += f"sh {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x2B:
            s += f"sw {REGS[rt]}, {simm}({REGS[rs]})"
        else:
            s += f"op{op:02x}"
        print(s)


# Find addiu *, r0, 0x70 followed by sw near gob/loader
print("=== state imm stores near 0x34xxxx / 0x35xxxx ===")
for a in range(0x340000, 0x370000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    # addiu rt, r0, imm
    if (w >> 26) & 0x3F != 9:
        continue
    if ((w >> 21) & 0x1F) != 0:
        continue
    imm = w & 0xFFFF
    if imm not in (0x60, 0x70, 0x80, 0x90, 0xA0, 0x50, 0x40, 0x30, 0x20, 0x10, 0x7A, 0x71, 0x72):
        continue
    rt = (w >> 16) & 0x1F
    for j in range(1, 12):
        w2 = struct.unpack_from("<I", ee, a + j * 4)[0]
        if ((w2 >> 26) & 0x3F) == 0x2B and ((w2 >> 16) & 0x1F) == rt:
            off = w2 & 0xFFFF
            sim = off - 0x10000 if off & 0x8000 else off
            print(f"  {a:08X}: addiu {REGS[rt]}, r0, {imm:#x}; sw @{a+j*4:08X} off={sim}")
            break

print("\n=== dis around 0x349190 (state 0x70) ===")
dis(0x349150, 50)

print("\n=== search lw of 0x70 compare near 6F5AA0 builder ===")
# Find lui/addiu to 0x6F5AA0 / 0x6F5A80
for a in range(0x300000, 0x400000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 0xF:
        continue
    imm = w & 0xFFFF
    if imm not in (0x6F, 0x70):
        continue
    rt = (w >> 16) & 0x1F
    for j in range(1, 8):
        w2 = struct.unpack_from("<I", ee, a + j * 4)[0]
        if ((w2 >> 26) & 0x3F) == 9 and ((w2 >> 21) & 0x1F) == rt:
            off = w2 & 0xFFFF
            sim = off - 0x10000 if off & 0x8000 else off
            ea = ((imm << 16) + sim) & 0xFFFFFFFF
            if 0x6F5A00 <= ea <= 0x6F5C00:
                print(f"  ref {a:08X} -> {ea:08X}")
