#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-stbl0.ram").read_bytes()
REGS = "r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split()


def dis(addr, n=60):
    print(f"=== {addr:#x} ===")
    for i in range(n):
        a = addr + i * 4
        w = struct.unpack_from("<I", ee, a)[0]
        op = (w >> 26) & 0x3F
        rs, rt, rd = (w >> 21) & 0x1F, (w >> 16) & 0x1F, (w >> 11) & 0x1F
        imm = w & 0xFFFF
        sim = imm - 0x10000 if imm & 0x8000 else imm
        fn = w & 0x3F
        s = f"{a:08X}: "
        if op == 3:
            s += f"jal 0x{((a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)):X}"
        elif op == 5:
            s += f"bne {REGS[rs]}, {REGS[rt]}, 0x{a + 4 + sim * 4:X}"
        elif op == 4:
            s += f"beq {REGS[rs]}, {REGS[rt]}, 0x{a + 4 + sim * 4:X}"
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
        elif op == 0 and fn == 0xC:
            s += "syscall"
        else:
            s += f"{w:08X}"
        print(s)


# Thread3 WaitSema ra=0x427234
dis(0x4271E0, 50)
# Look at 0x239F00 briefly
dis(0x239F00, 40)
# Walker gate at 0x242480
dis(0x242480, 40)

# Find who signals sema stored at 705C18 — iSignalSema after loading it
print("\nnear SignalSema (0x43CB00/10) callers that load 705C18:")
# Find jal 0x43CB00 or 0x43CB10 within 32 instr of 705C18 load
sema_loads = []
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 0xF or (w & 0xFFFF) != 0x70:
        continue
    for j in range(1, 8):
        w2 = struct.unpack_from("<I", ee, a + j * 4)[0]
        op = (w2 >> 26) & 0x3F
        imm = w2 & 0xFFFF
        sim = imm - 0x10000 if imm & 0x8000 else imm
        if op == 0x23 and sim == 0x5C18:
            sema_loads.append(a + j * 4)
            break

for load_a in sema_loads:
    for k in range(-8, 16):
        a = load_a + k * 4
        if a < 0:
            continue
        w = struct.unpack_from("<I", ee, a)[0]
        if ((w >> 26) & 0x3F) != 3:
            continue
        tgt = (a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
        if tgt in (0x43CB00, 0x43CB10, 0x43CB20):  # Signal / iSignal / Wait
            names = {0x43CB00: "SignalSema", 0x43CB10: "iSignalSema", 0x43CB20: "WaitSema"}
            print(f"  load@{load_a:08X} call@{a:08X} {names[tgt]}")
