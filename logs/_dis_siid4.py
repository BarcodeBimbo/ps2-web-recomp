#!/usr/bin/env python3
from pathlib import Path
import struct

p = Path(r"C:\PS2Recomp\logs\vvaa.irx").read_bytes()
BASE = 0xB9400
load_ofs = 0xB0
REGS = "r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split()

def fo(addr):
    return load_ofs + (addr - BASE)

def dis(addr, n, title):
    print(f"\n=== {title} @ {addr:#x} ===")
    for i in range(n):
        a = addr + i * 4
        w = struct.unpack_from("<I", p, fo(a))[0]
        op = (w >> 26) & 0x3F
        rs = (w >> 21) & 0x1F
        rt = (w >> 16) & 0x1F
        rd = (w >> 11) & 0x1F
        sa = (w >> 6) & 0x1F
        fn = w & 0x3F
        imm = w & 0xFFFF
        simm = imm - 0x10000 if imm & 0x8000 else imm
        target = (a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
        # relocatable jal in IRX often wrong; show raw
        s = f"{a:08X}: {w:08X}  "
        if op == 0:
            names = {0x21:"addu",0x23:"subu",0x24:"and",0x25:"or",0x00:"sll",0x02:"srl",0x08:"jr",0x09:"jalr",0x0c:"syscall",0x2a:"slt",0x2b:"sltu",0x0a:"movz",0x0b:"movn",0x12:"mflo",0x10:"mfhi"}
            if fn in (0,2,3): s += f"{names.get(fn,'s')} {REGS[rd]}, {REGS[rt]}, {sa}"
            elif fn == 8: s += f"jr {REGS[rs]}"
            elif fn == 9: s += f"jalr {REGS[rd]}, {REGS[rs]}"
            else: s += f"{names.get(fn,f'spec{fn:02x}')} {REGS[rd]}, {REGS[rs]}, {REGS[rt]}"
        elif op == 2: s += f"j {target:#x}"
        elif op == 3: s += f"jal {target:#x}"
        elif op == 4: s += f"beq {REGS[rs]}, {REGS[rt]}, {a+4+simm*4:#x}"
        elif op == 5: s += f"bne {REGS[rs]}, {REGS[rt]}, {a+4+simm*4:#x}"
        elif op == 8: s += f"addi {REGS[rt]}, {REGS[rs]}, {simm}"
        elif op == 9: s += f"addiu {REGS[rt]}, {REGS[rs]}, {simm}"
        elif op == 0xA: s += f"slti {REGS[rt]}, {REGS[rs]}, {simm}"
        elif op == 0xB: s += f"sltiu {REGS[rt]}, {REGS[rs]}, {simm}"
        elif op == 0xC: s += f"andi {REGS[rt]}, {REGS[rs]}, {imm:#x}"
        elif op == 0xD: s += f"ori {REGS[rt]}, {REGS[rs]}, {imm:#x}"
        elif op == 0xF: s += f"lui {REGS[rt]}, {imm:#x}"
        elif op == 0x20: s += f"lb {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x23: s += f"lw {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x24: s += f"lbu {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x28: s += f"sb {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x2B: s += f"sw {REGS[rt]}, {simm}({REGS[rs]})"
        else: s += f"op{op:02x} imm={simm}"
        print(s)

dis(0xB990C, 120, "cmd<10 handler")
dis(0xB9A20, 40, "a0!=0 path")

# strings in IRX
for s in [b"MUSIC", b"siid", b"VVAA", b".L", b".R", b"ADX", b"err", b"stat"]:
    i = 0
    while True:
        j = p.find(s, i)
        if j < 0:
            break
        print("str", hex(BASE + j - load_ofs) if j >= load_ofs else hex(j), p[j:j+32])
        i = j + 1
