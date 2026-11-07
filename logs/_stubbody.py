import struct
p=open("logs/vvaa.irx","rb").read(); text=p[0xb0:0xb0+0x3180]; base=0xB9400
# dump stub bodies for timer-related offs
for off in [0x1c4,0x1cc,0x1d4,0x1f8,0x200,0x208,0x210,0x198,0x14,0x1c,0x2b8,0x2c0]:
    abs=base+off
    words=[struct.unpack_from("<I",text,off+i*4)[0] for i in range(4)]
    print(f"{abs:08X}: " + " ".join(f"{w:08X}" for w in words))
# Also read import directories from IRX - look for "timrman" in file and nearby ordinals
idx=p.find(b"timrman")
print("timrman at", hex(idx))
print(p[idx-32:idx+64])
# sceCdRead stub
idx=p.find(b"sceCdRead")
print("sceCdRead at", hex(idx), p[idx:idx+20])
