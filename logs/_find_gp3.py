#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-stbl0.ram").read_bytes()
# Brute: for each possible gp where (gp-31596) is in RAM and the byte was written as 0/1
# by our understanding — also check nax dump for comparison
for name in ["logs/cnk-stbl0.ram", "logs/cnk-nax.ram"]:
    ee = Path(name).read_bytes()
    print("===", name, "===")
    # From sb sites, after successful path flag should be 1 if walker armed
    # Search bytes that are 0 or 1 at addresses ending such that gp = addr+31596 is plausible
    candidates = []
    for addr in range(0x6A0000, 0x7A0000):
        if ee[addr] in (0, 1):
            gp = addr + 31596
            if 0x700000 <= gp <= 0x790000:
                candidates.append((addr, gp, ee[addr]))
    # Too many — narrow: look at who uses 0x8494 as signed offset with non-gp bases building absolute
    # lui + addiu forming addr, then sb
    for a in range(0x240000, 0x250000, 4):
        w = struct.unpack_from("<I", ee, a)[0]
        if ((w >> 26) & 0x3F) != 0xF:
            continue
        imm = w & 0xFFFF
        rt = (w >> 16) & 0x1F
        for j in range(1, 8):
            w2 = struct.unpack_from("<I", ee, a + j * 4)[0]
            if ((w2 >> 26) & 0x3F) == 9 and ((w2 >> 21) & 0x1F) == rt:
                off = w2 & 0xFFFF
                sim = off - 0x10000 if off & 0x8000 else off
                ea = ((imm << 16) + sim) & 0xFFFFFFFF
                if ea == 0 or True:
                    # check following sb to that reg
                    for k in range(j + 1, j + 6):
                        w3 = struct.unpack_from("<I", ee, a + k * 4)[0]
                        if ((w3 >> 26) & 0x3F) == 0x28 and ((w3 >> 21) & 0x1F) == ((w2 >> 16) & 0x1F):
                            print(f"  abs sb via {a:08X} ea={ea:#x}")

# Read gp from CPU context if stored in dump — PS2_DUMP may include more than RAM
# File size 37748736 = 0x2400000 = 36MB — might include IOP+scratch
print("file sizes", Path("logs/cnk-stbl0.ram").stat().st_size)

# Symbol approach: strings near flag
# The init at 0x2423C0 stores to flag — after jal 0x243E40
# Disassemble 0x243E40 to see what it needs
print("\n=== 0x243E40 ===")
REGS = "r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split()
ee = Path("logs/cnk-stbl0.ram").read_bytes()
for i in range(40):
    a = 0x243E40 + i * 4
    w = struct.unpack_from("<I", ee, a)[0]
    op = (w >> 26) & 0x3F
    rs, rt, rd = (w >> 21) & 0x1F, (w >> 16) & 0x1F, (w >> 11) & 0x1F
    imm = w & 0xFFFF
    sim = imm - 0x10000 if imm & 0x8000 else imm
    fn = w & 0x3F
    s = f"{a:08X}: {w:08X}  "
    if op == 3:
        s += f"jal 0x{((a&0xF0000000)|((w&0x3FFFFFF)<<2)):X}"
    elif op == 4:
        s += f"beq {REGS[rs]}, {REGS[rt]}, 0x{a+4+sim*4:X}"
    elif op == 5:
        s += f"bne {REGS[rs]}, {REGS[rt]}, 0x{a+4+sim*4:X}"
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
    else:
        s += f"op{op:02x}"
    print(s)
