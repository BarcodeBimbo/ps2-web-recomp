#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-live.ram").read_bytes()[:0x2000000]
REGS = "r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split()

def dis(addr, n, title):
    print(f"\n=== {title} @ {addr:#x} ===")
    for i in range(n):
        a = addr + i * 4
        w = struct.unpack_from("<I", ee, a)[0]
        op = (w >> 26) & 0x3F
        rs = (w >> 21) & 0x1F
        rt = (w >> 16) & 0x1F
        rd = (w >> 11) & 0x1F
        sa = (w >> 6) & 0x1F
        fn = w & 0x3F
        imm = w & 0xFFFF
        simm = imm - 0x10000 if imm & 0x8000 else imm
        target = (a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
        s = f"{a:08X}: {w:08X}  "
        if op == 0:
            names = {0x21:"addu",0x23:"subu",0x24:"and",0x25:"or",0x00:"sll",0x02:"srl",0x08:"jr",0x09:"jalr",0x2a:"slt",0x2b:"sltu"}
            if fn in (0,2,3): s += f"{names.get(fn,'s')} {REGS[rd]}, {REGS[rt]}, {sa}"
            elif fn == 8: s += f"jr {REGS[rs]}"
            elif fn == 9: s += f"jalr {REGS[rd]}, {REGS[rs]}"
            else: s += f"{names.get(fn,f's{fn:02x}')} {REGS[rd]}, {REGS[rs]}, {REGS[rt]}"
        elif op == 2: s += f"j {target:#x}"
        elif op == 3: s += f"jal {target:#x}"
        elif op == 4: s += f"beq {REGS[rs]}, {REGS[rt]}, {a+4+simm*4:#x}"
        elif op == 5: s += f"bne {REGS[rs]}, {REGS[rt]}, {a+4+simm*4:#x}"
        elif op == 9: s += f"addiu {REGS[rt]}, {REGS[rs]}, {simm}"
        elif op == 0xD: s += f"ori {REGS[rt]}, {REGS[rs]}, {imm:#x}"
        elif op == 0xF: s += f"lui {REGS[rt]}, {imm:#x}"
        elif op == 0x23: s += f"lw {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x2B: s += f"sw {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x24: s += f"lbu {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x20: s += f"lb {REGS[rt]}, {simm}({REGS[rs]})"
        else: s += f"op{op:02x} imm={simm}"
        print(s)

dis(0x349160, 50, "state70 site A")
dis(0x356A30, 50, "state70 site B")
dis(0x6C7580, 40, "overlay state70")

# vvFsDevice string refs
s = ee.find(b"vvFsDevicePS2SceCd")
print("\nvvFsDevice at", hex(s))
needle = struct.pack("<I", s)
hs = []
idx = 0
while len(hs) < 15:
    i = ee.find(needle, idx)
    if i < 0:
        break
    if i % 4 == 0:
        hs.append(i)
    idx = i + 1
print("refs", [hex(h) for h in hs])
