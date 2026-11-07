#!/usr/bin/env python3
"""Disassemble VVAA IRX at known absolute addrs (module base 0xB9400)."""
from pathlib import Path
import struct

p = Path(r"C:\PS2Recomp\logs\vvaa.irx").read_bytes()
# From load: entry 0xB96D0, ELF e_entry 0x2D0 => base = 0xB9400
BASE = 0xB9400
# text in file: typically after ELF hdr; find PT_LOAD
e_phoff = struct.unpack_from("<I", p, 0x1C)[0]
e_phentsize, e_phnum = struct.unpack_from("<HH", p, 0x2A)
load_ofs = load_vaddr = None
for i in range(e_phnum):
    off = e_phoff + i * e_phentsize
    t, ofs, vaddr, paddr, filesz, memsz, flags, align = struct.unpack_from("<IIIIIIII", p, off)
    print(f"ph{i}: type={t} ofs={hex(ofs)} vaddr={hex(vaddr)} filesz={hex(filesz)}")
    if t == 1 and load_ofs is None:
        load_ofs, load_vaddr = ofs, vaddr

# IOP IRX often uses relative vaddrs; map absolute runtime addr -> file
# runtime_addr = BASE + (vaddr - load_vaddr) ... if load_vaddr==0, file_ofs = load_ofs + (addr-BASE)

def file_ofs(addr: int) -> int:
    rel = addr - BASE
    return load_ofs + rel

REGS = ["r0","at","v0","v1","a0","a1","a2","a3","t0","t1","t2","t3","t4","t5","t6","t7",
        "s0","s1","s2","s3","s4","s5","s6","s7","t8","t9","k0","k1","gp","sp","fp","ra"]

def dis(addr, n, title):
    print(f"\n=== {title} @ {addr:#x} ===")
    fo = file_ofs(addr)
    for i in range(n):
        a = addr + i * 4
        w = struct.unpack_from("<I", p, fo + i * 4)[0]
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
            names = {0x20:"add",0x21:"addu",0x22:"sub",0x23:"subu",0x24:"and",0x25:"or",0x26:"xor",0x27:"nor",
                     0x00:"sll",0x02:"srl",0x03:"sra",0x08:"jr",0x09:"jalr",0x0c:"syscall",0x0d:"break",
                     0x10:"mfhi",0x12:"mflo",0x18:"mult",0x19:"multu",0x1a:"div",0x1b:"divu",
                     0x2a:"slt",0x2b:"sltu"}
            if fn in (0,2,3):
                s += f"{names.get(fn,'spec')} {REGS[rd]}, {REGS[rt]}, {sa}"
            elif fn in (8,):
                s += f"jr {REGS[rs]}"
            elif fn in (9,):
                s += f"jalr {REGS[rd]}, {REGS[rs]}"
            elif fn in (0x10,0x12):
                s += f"{names.get(fn)} {REGS[rd]}"
            else:
                s += f"{names.get(fn,f'spec{fn:02x}')} {REGS[rd]}, {REGS[rs]}, {REGS[rt]}"
        elif op == 2:
            s += f"j {target:#x}"
        elif op == 3:
            s += f"jal {target:#x}"
        elif op == 4:
            s += f"beq {REGS[rs]}, {REGS[rt]}, {a+4+simm*4:#x}"
        elif op == 5:
            s += f"bne {REGS[rs]}, {REGS[rt]}, {a+4+simm*4:#x}"
        elif op == 6:
            s += f"blez {REGS[rs]}, {a+4+simm*4:#x}"
        elif op == 7:
            s += f"bgtz {REGS[rs]}, {a+4+simm*4:#x}"
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
        elif op == 0x23:
            s += f"lw {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x24:
            s += f"lbu {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x28:
            s += f"sb {REGS[rt]}, {simm}({REGS[rs]})"
        elif op == 0x2B:
            s += f"sw {REGS[rt]}, {simm}({REGS[rs]})"
        else:
            s += f"op{op:02x} rs={rs} rt={rt} imm={imm:#x}"
        print(s)

# Confirm base via string "siid" or export
print("BASE", hex(BASE), "load_ofs", hex(load_ofs), "load_vaddr", hex(load_vaddr))
dis(0xBA2EC, 24, "TimerCallback")
# cmd4 / status builder - search for store pattern near 0xBF3D0 refs
# Find lw/sw with imm 56 (stream flag) or 204
print("\n=== scanning for imm 56 / 204 / 0x500C ===")
text_start = load_ofs
text_end = load_ofs + 0x3180
for off in range(text_start, text_end, 4):
    w = struct.unpack_from("<I", p, off)[0]
    op = (w >> 26) & 0x3F
    imm = w & 0xFFFF
    if op in (0x23, 0x2B, 0x20, 0x28, 0x24) and imm in (56, 204, 0xCC, 0x38):
        addr = BASE + (off - load_ofs)
        print(f"{addr:08X}: op={op:02x} imm={imm} w={w:08X}")
    if imm == 0x500C and op in (0x9, 0xD, 0xF):
        addr = BASE + (off - load_ofs)
        print(f"{addr:08X}: loads 0x500C w={w:08X}")
