import struct
p=open("logs/vvaa.irx","rb").read(); text=p[0xb0:0xb0+0x3180]; base=0xB9400
# find all sw to s5-relative in cmd4 region B9AA4-B9BD0
REGS='r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra'.split()
for off in range(0x6A4, 0x7D8, 4):
    a=base+off; w=struct.unpack_from('<I',text,off)[0]
    op=(w>>26)&0x3f; rs=(w>>21)&0x1f; rt=(w>>16)&0x1f; imm=w&0xffff; simm=imm-0x10000 if imm>=0x8000 else imm; fn=w&0x3f
    if op==0x2b and rs==21: # sw rt, off(s5)
        print(f'{a:08X}: sw {REGS[rt]}, {simm}(s5)')
    if op==0x23 and rs==21:
        print(f'{a:08X}: lw {REGS[rt]}, {simm}(s5)')
    if op==3:
        t=(w&0x3ffffff)<<2
        print(f'{a:08X}: jal {base+t:08X}')
    if op==9 and rt==21:
        print(f'{a:08X}: addiu s5, {REGS[rs]}, {simm}')
# Also check what 0x500C could be - print stream struct size math from cmd1
print('---')
# Disasm GetSwitch stub and see if SPU2 returns 0x500C
# Search SPU2 register defaults
from pathlib import Path
for pth in Path('runtime/src/iop').glob('spu*.cpp'):
    t=pth.read_text(encoding='utf-8',errors='replace')
    if '0x500C' in t or 'GetParam' in t or 'GetSwitch' in t:
        print(pth)
