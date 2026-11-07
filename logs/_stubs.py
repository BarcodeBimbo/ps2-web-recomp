import struct
p=open("logs/vvaa.irx","rb").read(); text=p[0xb0:0xb0+0x3180]; base=0xB9400
# list import stubs with addresses from symbols earlier
# From earlier: stubs around B94xx-B96xx
# Find all jal to low offsets (imports)
from collections import Counter
c=Counter()
for off in range(0,0x3180,4):
    w=struct.unpack_from("<I",text,off)[0]
    if (w>>26)==3:
        t=(w&0x3ffffff)<<2
        if t < 0x400:  # import stub region roughly
            c[t]+=1
            print(f"{base+off:08X}: jal {base+t:08X} off={t:#x}")
print("counts", sorted(c.items()))
# dump stub table names via symtab imports
e_shoff=struct.unpack_from("<I",p,0x20)[0]
e_shentsize,e_shnum,e_shstrndx=struct.unpack_from("<HHH",p,0x2e)
secs=[struct.unpack_from("<IIIIIIIIII",p,e_shoff+i*e_shentsize) for i in range(e_shnum)]
shstr=p[secs[e_shstrndx][4]:secs[e_shstrndx][4]+secs[e_shstrndx][5]]
def nm(i):
    no=secs[i][0]; return shstr[no:shstr.index(0,no)].decode()
by={nm(i):secs[i] for i in range(e_shnum)}
symtab,strtab=by[".symtab"],by[".strtab"]
print("IMPORT stubs:")
for i in range(symtab[5]//16):
    name,value,size,info,other,shndx=struct.unpack_from("<IIIBBH",p,symtab[4]+i*16)
    if shndx!=0: continue
    nms=p[strtab[4]+name:p.index(0,strtab[4]+name)].decode() if name else ""
    if nms:
        print(f"  {nms}")
