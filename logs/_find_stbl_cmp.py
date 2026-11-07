#!/usr/bin/env python3
"""Find code that compares against STBLz / STBL0 magic."""
from pathlib import Path
import struct

ee = Path("logs/cnk-nax.ram").read_bytes()[:0x2000000]

# Byte compares often load first word as 'STBL' = 0x4C425453 LE
magic = 0x4C425453
hits = []
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    # lui rt, imm where combined with ori yields magic — hard
    # Look for lui/ori building 0x4C42 or load immediate patterns
    # More reliable: find lw + addiu compare sequence referencing string "STBLz"
    pass

# Find "STBLz" / "STBL0" string constants in low memory / rodata
for sig in [b"STBLz", b"STBL0"]:
    idx = 0
    found = []
    while len(found) < 20:
        i = ee.find(sig, idx)
        if i < 0:
            break
        found.append(i)
        idx = i + 1
    print(sig, [hex(x) for x in found])

# Pointers to those strings
for sig in [b"STBLz", b"STBL0"]:
    i = ee.find(sig)
    if i < 0:
        continue
    needle = struct.pack("<I", i)
    ptrs = [a for a in range(0, min(len(ee), 0x800000), 4) if ee[a : a + 4] == needle]
    print(f"ptrs to {sig}@{i:#x}", [hex(p) for p in ptrs[:20]], "n=", len(ptrs))

# Disassemble zlib inflateInit area around first error-string ref 0x23D61C
REGS = "r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split()

def dis(addr, n=30):
    print(f"--- {addr:#x} ---")
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
        elif op == 9:
            s += f"addiu {REGS[rt]}, {REGS[rs]}, {simm}"
        elif op == 0xF:
            s += f"lui {REGS[rt]}, {imm:#x}"
        elif op == 0x23:
            s += f"lw {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x2B:
            s += f"sw {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0 and fn == 8:
            s += f"jr {REGS[rs]}"
        elif op == 0 and fn == 0x21:
            s += f"addu {REGS[rd]}, {REGS[rs]}, {REGS[rt]}"
        else:
            s += f"op{op:02x}/{fn:02x}"
        print(s)

# Find function that references both STBL and inflate - search for lbu of first byte 'S'=0x53 compare
# addiu rt, r0, 0x53 ; lb ; bne
print("S-compare sites near 0x23xxxx:")
for a in range(0x230000, 0x250000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) == 9 and ((w >> 21) & 0x1F) == 0 and (w & 0xFFFF) == 0x53:
        print(f"  {a:08X}")

dis(0x23F600, 40)

# Who calls into 0x23xxxx from gob loader 0x34/35?
print("\njals from 0x34/35 into 0x23:")
n = 0
for a in range(0x340000, 0x370000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) != 3:
        continue
    tgt = (a & 0xF0000000) | ((w & 0x3FFFFFF) << 2)
    if 0x230000 <= tgt < 0x250000:
        print(f"  {a:08X} -> {tgt:08X}")
        n += 1
        if n > 40:
            break
