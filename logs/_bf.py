from pathlib import Path
import struct
ram=Path('games/b49f2e769315347e8bda839feb705744/explore_ram.bin').read_bytes()
pat=struct.pack('<I', 0x73696964)
idx=0; hits=[]
while True:
    i=ram.find(pat, idx)
    if i<0: break
    hits.append(i); idx=i+1
print('siid constant hits', len(hits), [hex(h) for h in hits[:20]])
# for each, look for code that loads it - hard. Instead dump nearby strings around MUSIC Stream
a=0x4ce6af
print(ram[a-200:a+200])
# BigFile / hlsfile - asset loading
for s in [b'BigFile', b'hlsfile', b'GFC', b'GOB', b'WaitSema', b'ASSETS']:
    i=ram.find(s)
    print(s, hex(i) if i>=0 else None, ram[i:i+60] if i>=0 else None)
