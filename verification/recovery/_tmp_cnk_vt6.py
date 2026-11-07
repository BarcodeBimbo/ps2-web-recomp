import struct
ELF=r'c:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc\boot.elf'
data=open(ELF,'rb').read(); LOAD=0x00100000; OFF=0x80; text=data[OFF:OFF+0x5F2000]

def find_ptr(va):
    pat=struct.pack('<I',va)
    hits=[]
    i=0
    while True:
        j=text.find(pat,i)
        if j<0: break
        if j%4==0: hits.append(LOAD+j)
        i=j+1
    return hits

for va in [0x520160,0x520168,0x520210,0x51AC80,0x51AD80,0x10FCE0,0x110100,0x508930]:
    h=find_ptr(va)
    print(hex(va), 'data xrefs', len(h), [hex(x) for x in h[:10]])

# Who calls install - maybe earlier function wraps it; search jal to 0x520168 (first real insn after prologue?)
# Actually look at 0x10918c - first factory call - near boot main
print('\nNear boot factory use @0x10918c:')
for pc in range(0x109140, 0x1091E0, 4):
    w=struct.unpack_from('<I',data,OFF+(pc-LOAD))[0]
    print('%08X: %08X'%(pc,w))

# Count ig class name strings for report inventory
import re
strings=[]
i=0
while i<len(text):
    if 32<=text[i]<127:
        j=i
        while j<len(text) and 32<=text[j]<127: j+=1
        if j-i>=4 and (i==0 or text[i-1]==0):
            s=text[i:j].decode('ascii')
            if re.fullmatch(r'ig[A-Za-z0-9_]+',s):
                strings.append((LOAD+i,s))
        i=j
    else: i+=1
print('ig class strings', len(strings))
# categories
cats=collections.Counter()
import collections
for _,s in strings:
    if s.startswith('igPsx2'): cats['psx2']+=1
    elif s.startswith('igGui') or 'Gui' in s: cats['gui']+=1
    elif 'File' in s or 'IGB' in s: cats['file']+=1
    elif 'Anim' in s: cats['anim']+=1
    elif 'Meta' in s: cats['meta']+=1
    else: cats['other']+=1
print(dict(cats))
