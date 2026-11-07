import struct, json, collections, re

ELF = r'c:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc\boot.elf'
data = open(ELF,'rb').read()
LOAD_VA = 0x00100000
FILE_OFF = 0x80
FILESZ = 0x5F2000
text = data[FILE_OFF:FILE_OFF+FILESZ]

def read_u32(va):
    if va < LOAD_VA or va >= LOAD_VA+FILESZ: return None
    return struct.unpack_from('<I', data, FILE_OFF+(va-LOAD_VA))[0]

def dec(w,pc):
    regs=['r0','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
    op=(w>>26)&0x3F; rs=(w>>21)&0x1F; rt=(w>>16)&0x1F; rd=(w>>11)&0x1F; fn=w&0x3F
    imm=w&0xFFFF; simm=imm-0x10000 if imm>=0x8000 else imm
    if op==0:
        if w==0: return 'nop'
        if fn==8: return 'jr '+regs[rs]
        if fn==9: return 'jalr '+regs[rs]
        if fn==33: return 'addu %s,%s,%s'%(regs[rd],regs[rs],regs[rt])
        if fn==37: return 'or/move %s,%s,%s'%(regs[rd],regs[rs],regs[rt])
        if fn==45: return 'daddu %s,%s,%s'%(regs[rd],regs[rs],regs[rt])
        return 'spec%d'%fn
    if op in (2,3):
        t=((pc+4)&0xF0000000)|((w&0x3FFFFFF)<<2)
        return '%s 0x%08X'%('j' if op==2 else 'jal',t)
    if op==15: return 'lui %s,0x%04X'%(regs[rt],imm)
    if op==9: return 'addiu %s,%s,%d'%(regs[rt],regs[rs],simm)
    if op==13: return 'ori %s,%s,0x%04X'%(regs[rt],regs[rs],imm)
    if op==35: return 'lw %s,%d(%s)'%(regs[rt],simm,regs[rs])
    if op==43: return 'sw %s,%d(%s)'%(regs[rt],simm,regs[rs])
    if op==32: return 'lb %s,%d(%s)'%(regs[rt],simm,regs[rs])
    if op==36: return 'lbu %s,%d(%s)'%(regs[rt],simm,regs[rs])
    if op==40: return 'sb %s,%d(%s)'%(regs[rt],simm,regs[rs])
    if op==4: return 'beq %s,%s,0x%08X'%(regs[rs],regs[rt],pc+4+simm*4)
    if op==5: return 'bne %s,%s,0x%08X'%(regs[rs],regs[rt],pc+4+simm*4)
    if op==31: return 'sq %s,%d(%s)'%(regs[rt],simm,regs[rs])
    if op==30: return 'lq %s,%d(%s)'%(regs[rt],simm,regs[rs])
    if op==63: return 'sd %s,%d(%s)'%(regs[rt],simm,regs[rs])
    if op==55: return 'ld %s,%d(%s)'%(regs[rt],simm,regs[rs])
    return 'op%d'%op

print('=== BIND REGISTRY INSTALLER around 0x00520140 ===')
for pc in range(0x00520140, 0x005202C0, 4):
    w=read_u32(pc)
    print('%08X: %08X  %s'%(pc,w,dec(w,pc)))

print('\n=== factory jal target 0x00508930 head ===')
for pc in range(0x00508930, 0x00508930+0x80, 4):
    w=read_u32(pc)
    print('%08X: %08X  %s'%(pc,w,dec(w,pc)))

# Find consecutive pointer tables to ig* strings (meta name tables)
strings={}
i=0
while i<len(text):
    if 32<=text[i]<127:
        j=i
        while j<len(text) and 32<=text[j]<127: j+=1
        if j-i>=4 and (i==0 or text[i-1]==0):
            strings[LOAD_VA+i]=text[i:j].decode('ascii')
        i=j
    else: i+=1
ig={va:s for va,s in strings.items() if re.fullmatch(r'ig[A-Za-z0-9_]+',s)}

# scan for runs of >=4 consecutive words that are ig name VAs
print('\n=== consecutive ig-name pointer runs ===')
runs=[]
off=0
while off < FILESZ-16:
    w=struct.unpack_from('<I',text,off)[0]
    if w in ig:
        run=[(LOAD_VA+off, ig[w])]
        o2=off+4
        while o2 < FILESZ:
            w2=struct.unpack_from('<I',text,o2)[0]
            if w2 not in ig: break
            run.append((LOAD_VA+o2, ig[w2]))
            o2+=4
        if len(run)>=3:
            runs.append(run)
            off=o2
            continue
    off+=4
print('runs', len(runs))
for r in runs[:15]:
    print(' run@%s len=%d: %s'%(hex(r[0][0]), len(r), ', '.join(n for _,n in r[:8])))

# Also: tables where every N words has an ig name ptr (meta object structs)
print('\n=== sparse meta tables (ig name every 8/12/16 bytes) ===')
# count density of ig ptrs in 0x68xxxx-0x6dxxxx data
for base in range(0x00680000, 0x006D0000, 0x10000):
    cnt=0
    for va in range(base, base+0x10000, 4):
        w=read_u32(va)
        if w in ig: cnt+=1
    if cnt:
        print('  %s: %d ig-name ptrs'%(hex(base),cnt))

# Loadgate constants from FCE0: slot stride 96, count 250, flags at +24008/+24016/+24020
# Confirm in ELF at 0x10FCE0
print('\n=== 0x0010FCE0 annotated ===')
for pc in range(0x0010FCE0, 0x0010FE20, 4):
    w=read_u32(pc)
    print('%08X: %08X  %s'%(pc,w,dec(w,pc)))

# stream+0x48: search lw/sw with imm 72 (0x48) near loadgate code
print('\n=== imm 0x48 near 0x0010Fxxx / 0x00110xxx ===')
for pc in range(0x0010F000, 0x00112000, 4):
    w=read_u32(pc)
    op=(w>>26)&0x3F
    if op in (35,43) and (w&0xFFFF)==0x48:
        print('%08X: %s'%(pc,dec(w,pc)))

# Sema ID storage globals
print('\n=== refs to 0x00705C18 / 0x00705F18 / 0x00705C10 ===')
for target,label in [(0x705C18,'sema45_slot'),(0x705F18,'sema16_lock'),(0x705C10,'sema47'),(0x705C00,'finish_ctr')]:
    hi=(target>>16)&0xFFFF
    lo=target&0xFFFF
    hits=[]
    for off in range(0,FILESZ-8,4):
        w=struct.unpack_from('<I',text,off)[0]
        if (w>>26)!=15 or (w&0xFFFF)!=hi: continue
        rt=(w>>16)&0x1F
        for k in range(1,8):
            w2=struct.unpack_from('<I',text,off+4*k)[0]
            op=(w2>>26)&0x3F; rs=(w2>>21)&0x1F; imm=w2&0xFFFF
            simm=imm-0x10000 if imm>=0x8000 else imm
            if rs==rt and op in (35,43) and simm==lo:
                hits.append((LOAD_VA+off+4*k, 'lw' if op==35 else 'sw'))
    print(label, hex(target), 'hits', len(hits), hits[:8])
