import struct
p=open('logs/vvaa.irx','rb').read(); text=p[0xb0:0xb0+0x3180]; base=0xB9400
REGS='r0 at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra'.split()
def dis(addr,n=50,label=''):
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
        elif op==0 and fn==0x23: s+=f'subu {R(rd)}, {R(rs)}, {R(rt)}'
        elif op==0 and fn==0x00: s+=f'sll {R(rd)}, {R(rt)}, {sa}'
        elif op==0 and fn==0x2a: s+=f'slt {R(rd)}, {R(rs)}, {R(rt)}'
        elif op==0 and fn==0x2b: s+=f'sltu {R(rd)}, {R(rs)}, {R(rt)}'
        elif op==2: s+=f'j {target:08X}'
        elif op==3:
            t=(w&0x3ffffff)<<2
            s+=f'jal {base+t:08X}'
        elif op==4: s+=f'beq {R(rs)}, {R(rt)}, {a+4+simm*4:08X}'
        elif op==5: s+=f'bne {R(rs)}, {R(rt)}, {a+4+simm*4:08X}'
        elif op==9: s+=f'addiu {R(rt)}, {R(rs)}, {simm}'
        elif op==0xa: s+=f'slti {R(rt)}, {R(rs)}, {simm}'
        elif op==0xb: s+=f'sltiu {R(rt)}, {R(rs)}, {simm}'
        elif op==0xc: s+=f'andi {R(rt)}, {R(rs)}, {imm:#x}'
        elif op==0xd: s+=f'ori {R(rt)}, {R(rs)}, {imm:#x}'
        elif op==0xf: s+=f'lui {R(rt)}, {imm:#x}'
        elif op==0x23: s+=f'lw {R(rt)}, {simm}({R(rs)})'
        elif op==0x2b: s+=f'sw {R(rt)}, {simm}({R(rs)})'
        else: s+=f'op{op:02x}/{fn:02x}'
        print(s)
dis(0xB98F0, 60, 'before_handle')
# also look where CreateSema/StartThread for timer happens - search for jal to CreateSema stub 0x1C4?
# WaitSema stub offset from symbols: WaitSema at B95D4 -> off 0x1D4
# CreateSema B95C4 -> 0x1C4
# Find calls to CreateSema / AllocHardTimer / SetTimerHandler in text
print('--- calls to CreateSema/WaitSema/Signal/Timer ---')
for off in range(0,0x3180,4):
    w=struct.unpack_from('<I',text,off)[0]
    if (w>>26)==3:
        t=(w&0x3ffffff)<<2
        abs=base+t
        if abs in (0xB95C4,0xB95CC,0xB95D4,0xB96B8,0xB96C0,0xBB6D0,0xBB6FC,0xBBC48,0xBBC78):
            names={0xB95C4:'CreateSema',0xB95CC:'iSignalSema',0xB95D4:'WaitSema',0xB96B8:'sceCdRead',0xB96C0:'sceCdSync',0xBB6D0:'SystemOpen',0xBB6FC:'PrecacheFolder',0xBBC48:'FileOpen',0xBBC78:'FindOnCd'}
            print(f'  {base+off:08X}: jal {names[abs]}')
