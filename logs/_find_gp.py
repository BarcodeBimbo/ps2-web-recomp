#!/usr/bin/env python3
from pathlib import Path
import struct

elf = Path("games/b49f2e769315347e8bda839feb705744/disc/boot.elf").read_bytes()
assert elf[:4] == b"\x7fELF"
e_phoff = struct.unpack_from("<I", elf, 28)[0]
e_phentsize = struct.unpack_from("<H", elf, 42)[0]
e_phnum = struct.unpack_from("<H", elf, 44)[0]
for i in range(e_phnum):
    off = e_phoff + i * e_phentsize
    p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align = struct.unpack_from("<IIIIIIII", elf, off)
    if p_type == 0x70000000:  # PT_MIPS_REGINFO
        gp = struct.unpack_from("<I", elf, p_offset + 20)[0]
        print("REGINFO gp", hex(gp))
        flag_addr = (gp - 31596) & 0xFFFFFFFF
        print("gp-flag addr", hex(flag_addr))

ee = Path("logs/cnk-stbl0.ram").read_bytes()
for a in range(0x100000, 0x110000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) == 0xF and ((w >> 16) & 0x1F) == 28:
        imm = w & 0xFFFF
        for j in range(1, 6):
            w2 = struct.unpack_from("<I", ee, a + j * 4)[0]
            if ((w2 >> 26) & 0x3F) == 9 and ((w2 >> 21) & 0x1F) == 28 and ((w2 >> 16) & 0x1F) == 28:
                off = w2 & 0xFFFF
                sim = off - 0x10000 if off & 0x8000 else off
                gp = ((imm << 16) + sim) & 0xFFFFFFFF
                print(f"gp init {a:#x} -> {gp:#x}")
                fa = (gp - 31596) & 0xFFFFFFFF
                if fa < len(ee):
                    print(f"  flag@{fa:#x}={ee[fa]}")
