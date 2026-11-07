import struct, json, collections, re, os

ELF = r'c:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc\boot.elf'
data = open(ELF,'rb').read()
LOAD_VA = 0x00100000
FILE_OFF = 0x80
FILESZ = 0x5F2000
text = data[FILE_OFF:FILE_OFF+FILESZ]

def read_u32(va):
    if va < LOAD_VA or va >= LOAD_VA+FILESZ: return None
    return struct.unpack_from('<I', data, FILE_OFF+(va-LOAD_VA))[0]

# strings
strings={}
i=0
while i < len(text):
    if 32 <= text[i] < 127:
        j=i
        while j < len(text) and 32 <= text[j] < 127: j+=1
        if j-i>=4 and (i==0 or text[i-1]==0):
            strings[LOAD_VA+i]=text[i:j].decode('ascii')
        i=j
    else:
        i+=1

ig_names={va:s for va,s in strings.items() if re.fullmatch(r'ig[A-Za-z0-9_]+', s)}
print('ig names', len(ig_names))

# absolute ptr hits
abs_hits=collections.Counter()
for off in range(0,FILESZ,4):
    w=struct.unpack_from('<I',text,off)[0]
    if w in ig_names:
        abs_hits[ig_names[w]] += 1
print('abs ptr class hits:', len(abs_hits))
for n,c in abs_hits.most_common(40):
    print(' ',n,c)

# lui/addiu construction of name VAs
# For each name VA, himm = va>>16, lo = va&0xFFFF (or signed addiu)
def find_addr_builds(target_va, label):
    hi = (target_va >> 16) & 0xFFFF
    lo = target_va & 0xFFFF
    lo_s = lo if lo < 0x8000 else lo - 0x10000
    # lui rt, hi  then addiu rt, rt, lo_s  OR ori
    # Also lui hi+1 with negative addiu for addresses with high lo bit
    builds=[]
    for off in range(0, FILESZ-8, 4):
        w = struct.unpack_from('<I', text, off)[0]
        if (w >> 26) != 15:  # lui
            continue
        rt = (w >> 16) & 0x1F
        himm = w & 0xFFFF
        # check next few instr for addiu/ori same rt
        for k in range(1, 6):
            w2 = struct.unpack_from('<I', text, off+4*k)[0]
            op = (w2 >> 26) & 0x3F
            rs = (w2 >> 21) & 0x1F
            rt2 = (w2 >> 16) & 0x1F
            imm = w2 & 0xFFFF
            if op == 9 and rs == rt and rt2 == rt:  # addiu
                simm = imm - 0x10000 if imm >= 0x8000 else imm
                full = ((himm << 16) + simm) & 0xFFFFFFFF
                if full == target_va:
                    builds.append(LOAD_VA+off)
                    break
            if op == 13 and rs == rt and rt2 == rt:  # ori
                full = ((himm << 16) | imm) & 0xFFFFFFFF
                if full == target_va:
                    builds.append(LOAD_VA+off)
                    break
    return builds

KEY = ['igIGBFile','igFile','igPsx2IopRpcConnection','igPsx2VisualContext','igGuiSystem',
       'igRenderer','igStreamingSource','igInfoManager','igObject','igNode','igGroup',
       'igAttr','igMemoryPool','igMallocMemoryPool','igFileImage','igPsx2Audio2Context',
       'igSerialScheduler','igMessenger','igDataPump','igAnimationSystem']

# map name string -> va
name_to_va = {}
for va,s in ig_names.items():
    name_to_va.setdefault(s, va)

print('\n=== lui/addiu builds for key class name strings ===')
build_map={}
for s in KEY:
    va = name_to_va.get(s)
    if not va:
        print(s, 'STRING NOT FOUND')
        continue
    builds = find_addr_builds(va, s)
    build_map[s]={'name_va':hex(va),'builds':[hex(b) for b in builds], 'count':len(builds)}
    print('%s @ %s builds=%d %s' % (s, hex(va), len(builds), [hex(b) for b in builds[:6]]))

# Also Alchemy strings
for s in ['Alchemy','alchemy.ini','ALCHEMY_BASE','igFileIO.irx','Intrinsic Alchemy']:
    # find exact
    hits=[va for va,ss in strings.items() if ss==s or ss.startswith(s[:20])]
    print('str',s, [hex(h) for h in hits[:3]])

# Disassemble 0x51AC80..0x51AD20
regs=['r0','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7','s0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
def dec(w,pc):
    op=(w>>26)&0x3F; rs=(w>>21)&0x1F; rt=(w>>16)&0x1F; rd=(w>>11)&0x1F; sa=(w>>6)&0x1F; fn=w&0x3F
    imm=w&0xFFFF; simm=imm-0x10000 if imm>=0x8000 else imm
    if op==0:
        if w==0: return 'nop'
        if fn==8: return 'jr '+regs[rs]
        if fn==9: return 'jalr '+regs[rs]
        if fn==12: return 'syscall'
        if fn==33: return 'addu %s,%s,%s'%(regs[rd],regs[rs],regs[rt])
        if fn==35: return 'subu %s,%s,%s'%(regs[rd],regs[rs],regs[rt])
        if fn==36: return 'and %s,%s,%s'%(regs[rd],regs[rs],regs[rt])
        if fn==37: return 'or %s,%s,%s'%(regs[rd],regs[rs],regs[rt])
        if fn==42: return 'slt %s,%s,%s'%(regs[rd],regs[rs],regs[rt])
        if fn==43: return 'sltu %s,%s,%s'%(regs[rd],regs[rs],regs[rt])
        if fn==0: return 'sll %s,%s,%d'%(regs[rd],regs[rt],sa)
        if fn==2: return 'srl %s,%s,%d'%(regs[rd],regs[rt],sa)
        if fn==3: return 'sra %s,%s,%d'%(regs[rd],regs[rt],sa)
        if fn==8: return 'jr '+regs[rs]
        return 'spec%d'%fn
    if op==28:
        if fn==0x28: return 'paddw %s,%s,%s'%(regs[rd],regs[rs],regs[rt])
        return 'mmi 0x%02X'%fn
    if op in (2,3):
        t=((pc+4)&0xF0000000)|((w&0x3FFFFFF)<<2)
        return '%s 0x%08X'%('j' if op==2 else 'jal',t)
    if op==15: return 'lui %s, 0x%04X'%(regs[rt],imm)
    if op==9: return 'addiu %s, %s, %d'%(regs[rt],regs[rs],simm)
    if op==8: return 'addi %s, %s, %d'%(regs[rt],regs[rs],simm)
    if op==13: return 'ori %s, %s, 0x%04X'%(regs[rt],regs[rs],imm)
    if op==12: return 'andi %s, %s, 0x%04X'%(regs[rt],regs[rs],imm)
    if op==35: return 'lw %s, %d(%s)'%(regs[rt],simm,regs[rs])
    if op==32: return 'lb %s, %d(%s)'%(regs[rt],simm,regs[rs])
    if op==36: return 'lbu %s, %d(%s)'%(regs[rt],simm,regs[rs])
    if op==43: return 'sw %s, %d(%s)'%(regs[rt],simm,regs[rs])
    if op==40: return 'sb %s, %d(%s)'%(regs[rt],simm,regs[rs])
    if op==4: return 'beq %s,%s,0x%08X'%(regs[rs],regs[rt],pc+4+simm*4)
    if op==5: return 'bne %s,%s,0x%08X'%(regs[rs],regs[rt],pc+4+simm*4)
    if op==6: return 'blez %s,0x%08X'%(regs[rs],pc+4+simm*4)
    if op==7: return 'bgtz %s,0x%08X'%(regs[rs],pc+4+simm*4)
    if op==10: return 'slti %s,%s,%d'%(regs[rt],regs[rs],simm)
    if op==11: return 'sltiu %s,%s,%d'%(regs[rt],regs[rs],simm)
    if op==31: # SQ/LQ etc LQ=0x1E? actually LQ op=30=0x1E, SQ=0x1F
        return 'sq?/mmi-mem 0x%08X'%w
    if op==26: return 'ldl?'
    if op==63: return 'sd %s,%d(%s)'%(regs[rt],simm,regs[rs])  # approx
    if op==55: return 'ld %s,%d(%s)'%(regs[rt],simm,regs[rs])
    return 'op%d 0x%08X'%(op,w)

print('\n=== DISASM 0x0051AC80 .. 0x0051AD10 ===')
pc=0x0051AC80
while pc < 0x0051AD10:
    w=read_u32(pc)
    print('%08X: %08X  %s'%(pc,w,dec(w,pc)))
    pc+=4

# Find writers to 0x00725F50: lui 0x72 / sw ?, 0x5F50(at)
# Pattern: lui rX, 0x0072 ; ... sw rY, 0x5F50(rX)  or addiu then sw
print('\n=== refs involving 0x00725F50 / 0x5F50 with base 0x72 ===')
# lui *, 0x0072
lui72=[]
for off in range(0,FILESZ-4,4):
    w=struct.unpack_from('<I',text,off)[0]
    if (w>>26)==15 and (w&0xFFFF)==0x0072:
        lui72.append((LOAD_VA+off, (w>>16)&0x1F))
print('lui *,0x0072 count', len(lui72))

# For each, look ahead 1..12 for lw/sw with imm 0x5F50 or 0x5EE0 or 24288/24400
hits_5f50=[]
hits_5ee0=[]
for va,rt in lui72:
    off=FILE_OFF+(va-LOAD_VA)
    for k in range(1,16):
        w2=struct.unpack_from('<I',text,off+4*k)[0]
        op=(w2>>26)&0x3F
        rs=(w2>>21)&0x1F
        imm=w2&0xFFFF
        simm=imm-0x10000 if imm>=0x8000 else imm
        if rs!=rt: continue
        if op in (35,43) and simm in (0x5F50, 24400):  # lw/sw
            hits_5f50.append((va, LOAD_VA+ (off-FILE_OFF)+4*k, 'lw' if op==35 else 'sw', regs[(w2>>16)&0x1F]))
        if op in (35,43) and simm in (0x5EE0, 24288):
            hits_5ee0.append((va, LOAD_VA+ (off-FILE_OFF)+4*k, 'lw' if op==35 else 'sw', regs[(w2>>16)&0x1F]))

print('0x725F50 lw/sw sites:', len(hits_5f50))
for h in hits_5f50[:30]:
    print(' ',h)
print('0x725EE0 lw/sw sites:', len(hits_5ee0))
for h in hits_5ee0[:20]:
    print(' ',h)

# Store builds for report
out={
  'key_name_builds': build_map,
  'abs_ptr_hits_top': abs_hits.most_common(50),
  'bind_725F50': [{'lui':hex(a),'access':hex(b),'op':c,'reg':d} for a,b,c,d in hits_5f50],
  'bind_725EE0': [{'lui':hex(a),'access':hex(b),'op':c,'reg':d} for a,b,c,d in hits_5ee0],
}
open(r'c:\PS2Recomp\verification\recovery\_cnk_bind_xrefs.json','w').write(json.dumps(out,indent=2))
print('wrote bind xrefs')
