#!/usr/bin/env python3
from pathlib import Path
import struct

elf = Path("games/b49f2e769315347e8bda839feb705744/disc/boot.elf").read_bytes()
print("elf size", len(elf), "header", elf[:16].hex())
e_type = struct.unpack_from("<H", elf, 16)[0]
e_machine = struct.unpack_from("<H", elf, 18)[0]
print("type", e_type, "machine", e_machine)
# 64-bit?
ei_class = elf[4]
print("class", ei_class)
if ei_class == 2:
    e_phoff = struct.unpack_from("<Q", elf, 32)[0]
    e_phentsize = struct.unpack_from("<H", elf, 54)[0]
    e_phnum = struct.unpack_from("<H", elf, 56)[0]
else:
    e_phoff = struct.unpack_from("<I", elf, 28)[0]
    e_phentsize = struct.unpack_from("<H", elf, 42)[0]
    e_phnum = struct.unpack_from("<H", elf, 44)[0]
print("ph", e_phoff, e_phentsize, e_phnum)
for i in range(min(e_phnum, 20)):
    off = e_phoff + i * e_phentsize
    if ei_class == 2:
        p_type = struct.unpack_from("<I", elf, off)[0]
        p_offset = struct.unpack_from("<Q", elf, off + 8)[0]
        p_vaddr = struct.unpack_from("<Q", elf, off + 16)[0]
    else:
        p_type, p_offset, p_vaddr = struct.unpack_from("<III", elf, off)
    print(f"  [{i}] type={p_type:#x} vaddr={p_vaddr:#x}")
    if p_type == 0x70000000:
        gp = struct.unpack_from("<I", elf, p_offset + 20)[0]
        print("   GP", hex(gp))

ee = Path("logs/cnk-stbl0.ram").read_bytes()
# search all lui gp
count = 0
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) == 0xF and ((w >> 16) & 0x1F) == 28:
        imm = w & 0xFFFF
        for j in range(1, 8):
            w2 = struct.unpack_from("<I", ee, a + j * 4)[0]
            if ((w2 >> 26) & 0x3F) == 9 and ((w2 >> 21) & 0x1F) == 28 and ((w2 >> 16) & 0x1F) == 28:
                off = w2 & 0xFFFF
                sim = off - 0x10000 if off & 0x8000 else off
                gp = ((imm << 16) + sim) & 0xFFFFFFFF
                if count < 15:
                    fa = (gp - 31596) & 0xFFFFFFFF
                    print(f"gp {a:#x} -> {gp:#x} flag@{fa:#x}={ee[fa] if fa < len(ee) else '?'}")
                count += 1
                break
print("total gp inits", count)

# Also: who stores to offset 0x8494 from gp? sb rt, -31596(gp)
print("\nsb to gp-31596:")
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) == 0x28:  # sb
        rs = (w >> 21) & 0x1F
        imm = w & 0xFFFF
        sim = imm - 0x10000 if imm & 0x8000 else imm
        if rs == 28 and sim == -31596:
            print(f"  {a:08X}: sb rt={(w>>16)&0x1F}")
