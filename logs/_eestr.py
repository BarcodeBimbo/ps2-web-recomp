import struct
from pathlib import Path
ram=Path('games/b49f2e769315347e8bda839feb705744/explore_ram.bin').read_bytes()
# string at 0x143B80
def cstr(a,n=80):
    b=ram[a:a+n]
    return b.split(b'\0',1)[0].decode('latin1','replace')
print('str 143B80', repr(cstr(0x143B80)))
# scan nearby strings
for a in range(0x143000, 0x145000, 4):
    if ram[a:a+4]==b'Wait' or ram[a:a+4]==b'File' or ram[a:a+5]==b'ASSETS' or ram[a:a+4]==b'igFi' or ram[a:a+4]==b'GFC' or ram[a:a+3]==b'GOB':
        print(hex(a), repr(cstr(a)))
# find WaitSema function
print('at 43CB28', struct.unpack_from('<I',ram,0x43CB28)[0])
# search strings related to sound/vvaa
count=0
for a in range(0x100000, 0x200000):
    if ram[a:a+4]==b'siid' or ram[a:a+4]==b'VVAA' or ram[a:a+6]==b'igFile' or ram[a:a+8]==b'FileIO.i':
        print('hit', hex(a), repr(cstr(a,60))); count+=1
        if count>30: break
# search for ASCII paths near GFC usage
for a in range(0x140000, 0x180000):
    if ram[a:a+10]==b'ASSETS.GFC' or ram[a:a+10]==b'ASSETS.GOB' or ram[a:a+9]==b'POOLS.CSV':
        print('path', hex(a), repr(cstr(a,40)))
