import struct, collections, re

elf_path = r'c:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc\boot.elf'
data = open(elf_path,'rb').read()
LOAD_VA = 0x00100000
FILE_OFF = 0x80

def read_u32(va):
    return struct.unpack_from('<I', data, FILE_OFF + (va - LOAD_VA))[0]

regs = ['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7',
        's0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']

def decode(w, pc):
    op = (w >> 26) & 0x3F
    rs = (w >> 21) & 0x1F
    rt = (w >> 16) & 0x1F
    rd = (w >> 11) & 0x1F
    sa = (w >> 6) & 0x1F
    fn = w & 0x3F
    imm = w & 0xFFFF
    simm = imm - 0x10000 if imm >= 0x8000 else imm
    if op == 0:
        if w == 0: return 'nop'
        if fn == 12: return 'syscall'
        if fn == 8: return 'jr %s' % regs[rs]
        if fn == 9: return 'jalr %s' % regs[rs]
        if fn == 0: return 'sll %s, %s, %d' % (regs[rd], regs[rt], sa)
        if fn == 33: return 'addu %s, %s, %s' % (regs[rd], regs[rs], regs[rt])
        if fn == 37: return 'or %s, %s, %s' % (regs[rd], regs[rs], regs[rt])
        if fn == 17: return 'mthi %s' % regs[rs]
        if fn == 19: return 'mtlo %s' % regs[rs]
        return 'special fn=%d' % fn
    if op == 28:
        if fn == 0x28: return 'paddw %s, %s, %s' % (regs[rd], regs[rs], regs[rt])
        return 'mmi fn=0x%02X' % fn
    if op == 17:
        if rs == 4: return 'mtc1 %s, f%d' % (regs[rt], rd)
        return 'cop1 0x%08X' % w
    if op in (2,3):
        target = ((pc+4)&0xF0000000) | ((w&0x3FFFFFF)<<2)
        return '%s 0x%08X' % ('j' if op==2 else 'jal', target)
    if op == 15: return 'lui %s, 0x%04X' % (regs[rt], imm)
    if op == 9: return 'addiu %s, %s, %d' % (regs[rt], regs[rs], simm)
    if op == 13: return 'ori %s, %s, 0x%04X' % (regs[rt], regs[rs], imm)
    if op == 35: return 'lw %s, %d(%s)' % (regs[rt], simm, regs[rs])
    if op == 43: return 'sw %s, %d(%s)' % (regs[rt], simm, regs[rs])
    if op == 4:
        return 'beq %s, %s, 0x%08X' % (regs[rs], regs[rt], pc+4+simm*4)
    if op == 5:
        return 'bne %s, %s, 0x%08X' % (regs[rs], regs[rt], pc+4+simm*4)
    if op == 1:
        names = {0:'bltz',1:'bgez',16:'bltzal',17:'bgezal'}
        return '%s %s, 0x%08X' % (names.get(rt,'regimm'), regs[rs], pc+4+simm*4)
    if op == 3: return 'jal ...'
    return 'op=%d 0x%08X' % (op, w)

print('=== CRT0 from 0x00108E28 ===')
pc = 0x00108E28
while pc < 0x00109100:
    w = read_u32(pc)
    d = decode(w, pc)
    print('%08X: %08X  %s' % (pc, w, d))
    pc += 4
