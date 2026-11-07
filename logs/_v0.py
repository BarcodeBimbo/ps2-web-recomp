import struct
p=open('logs/vvaa.irx','rb').read(); text=p[0xb0:0xb0+0x3180]; base=0xB9400
REGS='r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra'.split()
def dis(addr,n=40,label=''):
    print('===',label or hex(addr),'===')
    for i in range(n):
        a=addr+i*4; w=struct.unpack_from('<I',text,a-base)[0]
        op=(w>>26)&0x3f; rs=(w>>21)&0x1f; rt=(w>>16)&0x1f; rd=(w>>11)&0x1f; sa=(w>>6)&0x1f; fn=w&0x3f
        imm=w&0xffff; simm=imm-0x10000 if imm>=0x8000 else imm
        target=(a&0xF0000000)|((w&0x3ffffff)<<2)
        R=lambda x:REGS[x]; s=f'{a:08X}: '
        if w==0: s+='nop'
        elif op==0 and fn==0x08: s+=f'jr {R(rs)}'
        elif op==0 and fn==0x09: s+=f'jalr {R(rd)}, {R(rs)}'
        elif op==0 and fn==0x21: s+=f'addu {R(rd)}, {R(rs)}, {R(rt)}'
        elif op==0 and fn==0x00: s+=f'sll {R(rd)}, {R(rt)}, {sa}'
        elif op==2: s+=f'j {target:08X}'
        elif op==3: s+=f'jal {target:08X}  #rel'
        elif op==4: s+=f'beq {R(rs)}, {R(rt)}, {a+4+simm*4:08X}'
        elif op==5: s+=f'bne {R(rs)}, {R(rt)}, {a+4+simm*4:08X}'
        elif op==9: s+=f'addiu {R(rt)}, {R(rs)}, {simm}'
        elif op==0xc: s+=f'andi {R(rt)}, {R(rs)}, {imm:#x}'
        elif op==0xd: s+=f'ori {R(rt)}, {R(rs)}, {imm:#x}'
        elif op==0xf: s+=f'lui {R(rt)}, {imm:#x}'
        elif op==0x23: s+=f'lw {R(rt)}, {simm}({R(rs)})'
        elif op==0x2b: s+=f'sw {R(rt)}, {simm}({R(rs)})'
        elif op==0x24: s+=f'lbu {R(rt)}, {simm}({R(rs)})'
        elif op==0x28: s+=f'sb {R(rt)}, {simm}({R(rs)})'
        else: s+=f'op{op:02x}/{fn:02x}'
        # annotate jal targets relative to module for stubs
        if op==3:
            t=(w&0x3ffffff)<<2
            s+=f'  (off {t:#x} -> {base+t:08X})'
        print(s)
dis(base+0x7d8, 30, 'cmd0')
# module start/entry - look for CreateSema StartThread SetupHardTimer calls in start
dis(0xB96D0, 50, 'module_start')
