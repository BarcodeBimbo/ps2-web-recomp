import struct
from pathlib import Path
ram=Path('games/b49f2e769315347e8bda839feb705744/explore_ram.bin').read_bytes()
# dump ctx at 0x7430C0 and nearby FileIO structures
for base in [0x7430C0, 0x7432C0, 0x743000]:
    print(f'==== {base:#x} ====')
    chunk=ram[base:base+0x80]
    print(chunk[:0x40].hex())
    words=struct.unpack_from('<'+'I'*16, ram, base)
    print(' '.join(f'{w:08X}' for w in words))
# search for ileIO string
idx=ram.find(b'ileIO')
print('ileIO at', hex(idx) if idx>=0 else None)
idx=ram.find(b'FileIO')
print('FileIO at', hex(idx) if idx>=0 else None, ram[idx:idx+32] if idx>=0 else None)
# search ASSETS in ram
for name in [b'ASSETS.GFC', b'ASSETS.GOB', b'POOLS.CSV', b'\\SOUND', b'\\STREAM']:
    idx=0; hits=0
    while hits<5:
        i=ram.find(name, idx)
        if i<0: break
        print(name, hex(i), ram[i:i+40])
        idx=i+1; hits+=1
