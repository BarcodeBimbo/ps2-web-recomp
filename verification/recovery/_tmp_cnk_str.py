import struct, collections, re

elf_path = r'c:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc\boot.elf'
data = open(elf_path,'rb').read()
LOAD_VA = 0x00100000
FILE_OFF = 0x80
text = data[FILE_OFF:FILE_OFF+0x5F2000]

# Find strings related to Alchemy root / modules / IRX / sce
want = []
needles = [b'Alchemy', b'ALCHEMY', b'alchemy.ini', b'igFileIO', b'igUKbd', b'igUMouse',
           b'igPsx2IopRpc', b'sceCd', b'sceSif', b'CreateSema', b'WaitSema', b'SignalSema',
           b'CreateThread', b'DeleteSema', b'iSignalSema', b'ExitDeleteThread',
           b'IOPRP', b'.irx', b'.IRX', b'sio2man', b'padman', b'mtapman',
           b'mcman', b'mcserv', b'usbd', b'libsd', b'sdrdrv', b'vvaa', b'cri_adxi',
           b'lgdev', b'igFile', b'igIGB', b'$(Alchemy', b'/usr/local/Alchemy']
seen=set()
for n in needles:
    start=0
    while True:
        i = text.find(n, start)
        if i < 0: break
        # expand to full C string
        a=i
        while a>0 and 32<=text[a-1]<127: a-=1
        b=i
        while b<len(text) and 32<=text[b]<127: b+=1
        s=text[a:b].decode('ascii','replace')
        va=LOAD_VA+a
        key=(s,va)
        if key not in seen:
            seen.add(key)
            want.append((va,s))
        start=i+1

want.sort()
print('=== KEY STRINGS (%d) ===' % len(want))
for va,s in want:
    print('0x%08X: %s' % (va, s[:140]))

# Also search for exact IRX module path patterns
print('\n=== MODULE PATH STRINGS ===')
for va,s in sorted({(LOAD_VA+m.start(), m.group().decode()) for m in re.finditer(rb'[A-Za-z0-9_./:\\%-]+\.irx', text, re.I)}):
    print('0x%08X: %s' % (va,s))
