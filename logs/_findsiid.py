from pathlib import Path
import struct
ram=Path('games/b49f2e769315347e8bda839feb705744/explore_ram.bin').read_bytes()
# igFile at 5289577
addr=5289577
print('igFile context', ram[addr-32:addr+64])
# find more ig/FileIO/siid/VVAA strings
for s in [b'igFile', b'FileIO', b'VVAA', b'siid', b'MUSIC', b'ASSETS', b'DiSnd', b'SndPs']:
    idx=0; n=0
    while n<5:
        i=ram.find(s, idx)
        if i<0: break
        print(hex(i), s, ram[i:i+40])
        idx=i+1; n+=1
# find lui/ori building 0x73696964 = lui 0x7369; ori 0x6964
# search for machine code
count=0
for a in range(0, len(ram)-8, 4):
    w0,w1=struct.unpack_from('<II',ram,a)
    # lui t, 0x7369 = 0x3c00|rt<<16|0x7369
    if (w0 & 0xffe0ffff) == 0x3c007369 and (w1 & 0xfc00ffff) == 0x34006964:
        print('build siid at', hex(a), 'w0', hex(w0), 'w1', hex(w1)); count+=1
        if count>10: break
print('done', count)
