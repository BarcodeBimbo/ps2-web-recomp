#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-nax.ram").read_bytes()[:0x2000000]
REGS = "r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split()


def dis(addr, n=60):
    print(f"\n=== {addr:#x} ===")
    for i in range(n):
        a = addr + i * 4
        w = struct.unpack_from("<I", ee, a)[0]
        op = (w >> 26) & 0x3F
        rs, rt, rd = (w >> 21) & 0x1F, (w >> 16) & 0x1F, (w >> 11) & 0x1F
        imm = w & 0xFFFF
        simm = imm - 0x10000 if imm & 0x8000 else imm
        fn = w & 0x3F
        s = f"{a:08X}: {w:08X}  "
        if op == 3:
            s += f"jal 0x{((a&0xF0000000)|((w&0x3FFFFFF)<<2)):X}"
        elif op == 2:
            s += f"j 0x{((a&0xF0000000)|((w&0x3FFFFFF)<<2)):X}"
        elif op == 5:
            s += f"bne {REGS[rs]}, {REGS[rt]}, 0x{a+4+simm*4:X}"
        elif op == 4:
            s += f"beq {REGS[rs]}, {REGS[rt]}, 0x{a+4+simm*4:X}"
        elif op == 6:
            s += f"blez {REGS[rs]}, 0x{a+4+simm*4:X}"
        elif op == 7:
            s += f"bgtz {REGS[rs]}, 0x{a+4+simm*4:X}"
        elif op == 9:
            s += f"addiu {REGS[rt]}, {REGS[rs]}, {simm}"
        elif op == 8:
            s += f"addi {REGS[rt]}, {REGS[rs]}, {simm}"
        elif op == 0xF:
            s += f"lui {REGS[rt]}, {imm:#x}"
        elif op == 0xD:
            s += f"ori {REGS[rt]}, {REGS[rs]}, {imm:#x}"
        elif op == 0xC:
            s += f"andi {REGS[rt]}, {REGS[rs]}, {imm:#x}"
        elif op == 0x23:
            s += f"lw {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x2B:
            s += f"sw {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x20:
            s += f"lb {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x24:
            s += f"lbu {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x28:
            s += f"sb {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0 and fn == 8:
            s += f"jr {REGS[rs]}"
        elif op == 0 and fn == 9:
            s += f"jalr {REGS[rd]}, {REGS[rs]}"
        elif op == 0 and fn == 0x21:
            s += f"addu {REGS[rd]}, {REGS[rs]}, {REGS[rt]}"
        elif op == 0 and fn == 0x23:
            s += f"subu {REGS[rd]}, {REGS[rs]}, {REGS[rt]}"
        elif op == 0 and fn == 0x25:
            s += f"or {REGS[rd]}, {REGS[rs]}, {REGS[rt]}"
        elif op == 0 and fn == 0x24:
            s += f"and {REGS[rd]}, {REGS[rs]}, {REGS[rt]}"
        elif op == 0 and fn == 0x2A:
            s += f"slt {REGS[rd]}, {REGS[rs]}, {REGS[rt]}"
        elif op == 0 and fn == 0:
            s += f"sll {REGS[rd]}, {REGS[rt]}, {(w>>6)&0x1F}"
        elif op == 0 and fn == 2:
            s += f"srl {REGS[rd]}, {REGS[rt]}, {(w>>6)&0x1F}"
        else:
            s += f"op{op:02x}/{fn:02x}"
        print(s)


# Disassemble around jal into zlib from gob path
for a in [0x342600, 0x343200, 0x344E40, 0x35CA80, 0x35FBC0]:
    dis(a, 50)

# Check 0x6F59D0 - referenced from zlib path as lw a0, 22992(v0) with v0=0x6f -> 0x6F59D0
print("\n6F59D0:", hex(struct.unpack_from("<I", ee, 0x6F59D0)[0]))
dump_base = 0x6F59C0
print("region:")
for i in range(0, 0x40, 16):
    a = dump_base + i
    words = [f"{struct.unpack_from('<I', ee, a+j*4)[0]:08X}" for j in range(4)]
    print(f"  {a:08X}: {' '.join(words)}")
