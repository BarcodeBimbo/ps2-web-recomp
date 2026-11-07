"""Validate static EE targets before scheduling a translation repair."""
from pathlib import Path
import struct


def add_entry(elf_path, entries_path, address):
    if type(address) is not int or address & 3 or not 0x1000 <= address < 0x02000000:
        raise ValueError('Invalid aligned EE code address.')
    data=Path(elf_path).read_bytes()
    if len(data)<52 or data[:7]!=b'\x7fELF\x01\x01\x01':raise ValueError('Unsupported boot ELF format.')
    phoff=struct.unpack_from('<I',data,28)[0];size,count=struct.unpack_from('<HH',data,42)
    if size<32 or count>1024 or phoff+count*size>len(data):raise ValueError('Invalid ELF program table.')
    found=False
    for i in range(count):
        kind,offset,base,_,filesize,_,flags,_=struct.unpack_from('<8I',data,phoff+i*size)
        if kind==1 and flags&1 and base<=address and address-base+4<=filesize and offset+filesize<=len(data):found=True;break
    if not found:raise ValueError('This address is runtime-loaded or outside the boot executable. Its RAM/module capture is required; a static rebuild cannot safely invent that code.')
    path=Path(entries_path);known=set(path.read_text().split()) if path.exists() else set()
    if len(known)>=65536:raise ValueError('Translation entry limit exceeded.')
    known.add(f'{address:x}');path.write_text(''.join(value+'\n' for value in sorted(known)))
