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
        rs, rt, rd = (w >> 21) & 0x1F, (w >> 16) & 0x1F, (w >> 11) & 0x1F
        fn, imm = w & 0x3F, w & 0xFFFF
        simm = imm - 0x10000 if imm & 0x8000 else imm
        target = (a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
        s = f"{a:08X}: {w:08X}  "
        if op == 0:
            if fn == 8: s += f"jr {REGS[rs]}"
            elif fn == 9: s += f"jalr {REGS[rd]}, {REGS[rs]}"
            elif fn in (0,2,3): s += f"shift {REGS[rd]}, {REGS[rt]}, { (w>>6)&0x1F}"
            else: s += f"spec{fn:02x} {REGS[rd]}, {REGS[rs]}, {REGS[rt]}"
        elif op == 3: s += f"jal {target:#x}"
        elif op == 2: s += f"j {target:#x}"
        elif op == 4: s += f"beq {REGS[rs]}, {REGS[rt]}, {a+4+simm*4:#x}"
        elif op == 5: s += f"bne {REGS[rs]}, {REGS[rt]}, {a+4+simm*4:#x}"
        elif op == 9: s += f"addiu {REGS[rt]}, {REGS[rs]}, {simm}"
        elif op == 0xF: s += f"lui {REGS[rt]}, {imm:#x}"
        elif op == 0x23: s += f"lw {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x2B: s += f"sw {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x24: s += f"lbu {REGS[rt]}, {simm}({REGS[rs]})"
        else: s += f"op{op:02x} {simm}"
        print(s)

dis(0x35DA30, 80, "post-alloc loader 35da30")
dis(0x33C1B0, 40, "allocator 33c1b0")
# Search for comparison with 'z' after STBL - lb / xori 0x7A ('z')
hits = []
for a in range(0x340000, 0x370000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    # xori/ori/addi with 0x7A or 0x30 ('0')
    if (w & 0xFC00FFFF) in (0x2400007A, 0x3800007A, 0x24000030, 0x38000030, 0x2400005A):
        hits.append(a)
print("imm 0x7A/0x30 sites", [hex(h) for h in hits[:40]])
