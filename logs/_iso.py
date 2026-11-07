from pathlib import Path
import struct
iso=Path('games/b49f2e769315347e8bda839feb705744/disc.iso').open('rb')
def read_sec(n):
    iso.seek(n*2048); return iso.read(2048)
pvd=read_sec(16)
print('PVD', pvd[1:6], 'root lba', struct.unpack_from('<I',pvd,158)[0], 'root size', struct.unpack_from('<I',pvd,166)[0])
print('path table LBA', struct.unpack_from('<I',pvd,140)[0], 'size', struct.unpack_from('<I',pvd,132)[0])
# dump dir records in sectors 261-264
for sec in [20,21,22,261,262,263,264]:
    data=read_sec(sec)
    print(f'==== sector {sec} ====')
    off=0; names=[]
    while off < 2048:
        ln=data[off]
        if ln==0:
            off=(off//2048+1)*2048
            if off>=2048: break
            continue
        if off+33>2048: break
        nlen=data[off+32]
        name=data[off+33:off+33+nlen]
        flags=data[off+25]
        lba=struct.unpack_from('<I',data,off+2)[0]
        size=struct.unpack_from('<I',data,off+10)[0]
        try: ns=name.decode('ascii','replace')
        except: ns=repr(name)
        if nlen>1:
            names.append((ns,lba,size,flags))
        off+=ln
    for n in names[:15]:
        print(n)
    print('... total', len(names))
