import struct
ELF = r'c:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc\boot.elf'
data=open(ELF,'rb').read(); LOAD=0x00100000; OFF=0x80; text=data[OFF:OFF+0x5F2000]

def jal_sites(tgt):
    enc=struct.pack('<I', 0x0C000000|((tgt>>2)&0x3FFFFFF))
    hits=[]; i=0
    while True:
        j=text.find(enc,i)
        if j<0: break
        if j%4==0: hits.append(LOAD+j)
        i=j+1
    return hits

for t,n in [(0x520160,'install_bind'),(0x520210,'teardown_bind'),(0x508930,'factory_alloc'),(0x51AC80,'unbind_51AC80'),(0x10FCE0,'FCE0'),(0x110100,'110100'),(0x51ACEC,'ret_51ACEC')]:
    h=jal_sites(t)
    print(n, hex(t), 'x%d'%len(h), [hex(x) for x in h[:12]])

# hex sema sites
for target in (0x705C18,0x705F18,0x705C10,0x725F00,0x725EF0,0x725EF8):
    hi=(target>>16)&0xFFFF; lo=target&0xFFFF
    hits=[]
    for off in range(0,len(text)-8,4):
        w=struct.unpack_from('<I',text,off)[0]
        if (w>>26)!=15 or (w&0xFFFF)!=hi: continue
        rt=(w>>16)&0x1F
        for k in range(1,8):
            w2=struct.unpack_from('<I',text,off+4*k)[0]
            op=(w2>>26)&0x3F; rs=(w2>>21)&0x1F; imm=w2&0xFFFF
            simm=imm-0x10000 if imm>=0x8000 else imm
            if rs==rt and op in (35,43) and (simm&0xFFFF)==lo:
                hits.append((hex(LOAD+off+4*k), 'lw' if op==35 else 'sw'))
    print(hex(target), hits[:10])

# BSS note
print('BSS start 0x006F2000 end 0x0072A480; 0x725F50 in BSS?', 0x6F2000<=0x725F50<0x72A480)
print('PHDR0 filesz end VA', hex(0x100000+0x5F2000))
