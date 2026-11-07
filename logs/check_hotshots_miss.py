from pathlib import Path
import struct
elf = Path('games/f29093e1f939f924fb11cc605b592b11/disc/boot.elf').read_bytes()
assert elf[:4] == b'\x7fELF'
phoff = struct.unpack_from('<I', elf, 28)[0]
phentsize, phnum = struct.unpack_from('<HH', elf, 42)
addr = 0x00332980
for i in range(phnum):
    off = phoff + i * phentsize
    t, offset, vaddr, paddr, filesz, memsz, flags, align = struct.unpack_from('<IIIIIIII', elf, off)
    if t == 1 and vaddr <= addr < vaddr + memsz:
        print(f'in PT_LOAD vaddr={vaddr:#x} filesz={filesz:#x} memsz={memsz:#x} flags={flags:#x}')
        fo = offset + (addr - vaddr)
        if (addr - vaddr) < filesz:
            print('bytes', elf[fo:fo + 16].hex())
        else:
            print('BSS or beyond filesz')
entries = Path('games/f29093e1f939f924fb11cc605b592b11/entries.txt').read_text(errors='replace')
print('entry present', '332980' in entries.lower() or '0x00332980' in entries.lower())
print('entries lines', len(entries.splitlines()))
