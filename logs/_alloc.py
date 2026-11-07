import struct
p=open("logs/vvaa.irx","rb").read(); text=p[0xb0:0xb0+0x3180]; base=0xB9400
# AllocSysMemory stub - find from imports
# Earlier: B9414 index 4 = AllocSysMemory (sysmem), B941C = FreeSysMemory
print('AllocSysMemory calls:')
for off in range(0,0x3180,4):
    w=struct.unpack_from('<I',text,off)[0]
    if (w>>26)==3:
        t=(w&0x3ffffff)<<2
        if base+t in (0xB9414, 0xB941C):
            print(f'  {base+off:08X}: jal {"Alloc" if base+t==0xB9414 else "Free"}')
            # print preceding 8 instructions for args
            for i in range(-6,1):
                a=base+off+i*4; ww=struct.unpack_from('<I',text,off+i*4)[0]
                print(f'    {a:08X}: {ww:08X}')
