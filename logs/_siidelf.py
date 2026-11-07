from pathlib import Path
import struct
elf=Path('games/b49f2e769315347e8bda839feb705744/disc/boot.elf').read_bytes()
# find siid
needle=b'siid'
idx=0; hits=[]
while True:
    i=elf.find(needle, idx)
    if i<0: break
    hits.append(i); idx=i+1
print('siid string hits', [hex(h) for h in hits[:10]])
# find little-endian 0x73696964
pat=struct.pack('<I', 0x73696964)
idx=0; addrs=[]
while True:
    i=elf.find(pat, idx)
    if i<0: break
    addrs.append(i); idx=i+1
print('siid id immediates', [hex(a) for a in addrs[:20]], 'count', len(addrs))
# Also in explore ram
ram=Path('games/b49f2e769315347e8bda839feb705744/explore_ram.bin').read_bytes()
# This might be NFS - check for Crash strings
for s in [b'Crash', b'Nitro', b'CNK', b'siid', b'igFile', b'Wait']:
    print(s, ram.find(s))
