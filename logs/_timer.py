import struct
p=open("logs/vvaa.irx","rb").read(); text=p[0xb0:0xb0+0x3180]; base=0xB9400
REGS='r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra'.split()
def dis(addr,n=50,label=''):
    print('===',label or hex(addr),'===')
    for i in range(n):
        a=addr+i*4; w=struct.unpack_from('<I',text,a-base)[0]
        op=(w>>26)&0x3f; rs=(w>>21)&0x1f; rt=(w>>16)&0x1f; rd=(w>>11)&0x1f; sa=(w>>6)&0x1f; fn=w&0x3f
        imm=w&0xffff; simm=imm-0x10000 if imm>=0x8000 else imm
        R=lambda x:REGS[x]; s=f'{a:08X}: '
        if w==0: s+='nop'
        elif op==0 and fn==0x08: s+=f'jr {R(rs)}'
        elif op==0 and fn==0x09: s+=f'jalr {R(rd)}, {R(rs)}'
        elif op==0 and fn==0x21: s+=f'addu {R(rd)}, {R(rs)}, {R(rt)}'
        elif op==0 and fn==0x00: s+=f'sll {R(rd)}, {R(rt)}, {sa}'
        elif op==3:
            t=(w&0x3ffffff)<<2; s+=f'jal {base+t:08X}'
        elif op==4: s+=f'beq {R(rs)}, {R(rt)}, {a+4+simm*4:08X}'
        elif op==5: s+=f'bne {R(rs)}, {R(rt)}, {a+4+simm*4:08X}'
        elif op==9: s+=f'addiu {R(rt)}, {R(rs)}, {simm}'
        elif op==0xc: s+=f'andi {R(rt)}, {R(rs)}, {imm:#x}'
        elif op==0xd: s+=f'ori {R(rt)}, {R(rs)}, {imm:#x}'
        elif op==0xf: s+=f'lui {R(rt)}, {imm:#x}'
        elif op==0x23: s+=f'lw {R(rt)}, {simm}({R(rs)})'
        elif op==0x2b: s+=f'sw {R(rt)}, {simm}({R(rs)})'
        else: s+=f'op{op:02x}/{fn:02x}'
        print(s)
dis(0xB9F40, 60, 'cmd1_timer_cd')
dis(0xBA2EC, 20, 'TimerCallback')
