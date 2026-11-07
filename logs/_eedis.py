import struct
from pathlib import Path
ram=Path('games/b49f2e769315347e8bda839feb705744/explore_ram.bin').read_bytes()
# EE MIPS disasm helper
REGS='r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra'.split()
def dis(addr,n=25):
    print(f'=== {addr:#x} ===')
    for i in range(n):
        a=addr+i*4
        if a+4>len(ram): break
        w=struct.unpack_from('<I',ram,a)[0]
        op=(w>>26)&0x3f; rs=(w>>21)&0x1f; rt=(w>>16)&0x1f; rd=(w>>11)&0x1f; sa=(w>>6)&0x1f; fn=w&0x3f
        imm=w&0xffff; simm=imm-0x10000 if imm>=0x8000 else imm
        target=(a&0xF0000000)|((w&0x3ffffff)<<2)
        R=lambda x:REGS[x]; s=f'{a:08X}: {w:08X} '
        if w==0: s+='nop'
        elif op==0 and fn==0x08: s+=f'jr {R(rs)}'
        elif op==0 and fn==0x09: s+=f'jalr {R(rd)}, {R(rs)}'
        elif op==0 and fn==0x21: s+=f'addu {R(rd)}, {R(rs)}, {R(rt)}'
        elif op==0 and fn==0x2d: s+=f'daddu {R(rd)}, {R(rs)}, {R(rt)}'
        elif op==0 and fn==0x25: s+=f'or {R(rd)}, {R(rs)}, {R(rt)}'
        elif op==0 and fn==0x0c: s+=f'syscall {w>>6}'
        elif op==0 and fn==0x00: s+=f'sll {R(rd)}, {R(rt)}, {sa}'
        elif op==2: s+=f'j {target:08X}'
        elif op==3: s+=f'jal {target:08X}'
        elif op==4: s+=f'beq {R(rs)}, {R(rt)}, {a+4+simm*4:08X}'
        elif op==5: s+=f'bne {R(rs)}, {R(rt)}, {a+4+simm*4:08X}'
        elif op==9: s+=f'addiu {R(rt)}, {R(rs)}, {simm}'
        elif op==0xd: s+=f'ori {R(rt)}, {R(rs)}, {imm:#x}'
        elif op==0xf: s+=f'lui {R(rt)}, {imm:#x}'
        elif op==0x23: s+=f'lw {R(rt)}, {simm}({R(rs)})'
        elif op==0x2b: s+=f'sw {R(rt)}, {simm}({R(rs)})'
        elif op==0x1e: s+=f'lq {R(rt)}, {simm}({R(rs)})'  # approx
        elif op==0x1f: s+=f'sq {R(rt)}, {simm}({R(rs)})'
        else: s+=f'op{op:02x}/{fn:02x}'
        print(s)

# look for WaitSema jal near RA 0x423004 - search backwards for jal to 0x43CB28 or similar
wait=0x43CB28
for a in range(0x422f00, 0x423010, 4):
    w=struct.unpack_from('<I',ram,a)[0]
    if (w>>26)==3:
        t=(a&0xF0000000)|((w&0x3ffffff)<<2)
        print(f'jal at {a:#x} -> {t:#x}')
    if (w>>26)==0 and (w&0x3f)==9:
        print(f'jalr at {a:#x}')

dis(0x422f80, 40)
print('--- callers stack ---')
for addr in [0x00108EC0,0x00108EE0,0x001090AC,0x0010999C,0x0010A044,0x00118FE0,0x001AFB2C]:
    # find function start by scanning back for typical prologue addiu sp
    start=addr
    for back in range(0, 0x200, 4):
        w=struct.unpack_from('<I',ram,addr-back)[0]
        if (w&0xffff0000)==0x27bd0000: # addiu sp
            start=addr-back; break
    print(f'stack {addr:#x} fnstart {start:#x}')
    dis(addr-16, 8)
