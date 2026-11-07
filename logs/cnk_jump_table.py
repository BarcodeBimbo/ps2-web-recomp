from pathlib import Path
import struct
import sys

sys.path.insert(0, 'scripts')
from translation_repair import add_entry

gid = 'b49f2e769315347e8bda839feb705744'
elf = Path(r'C:\PS2Recomp\games') / gid / 'disc' / 'boot.elf'
data = elf.read_bytes()
phoff = struct.unpack_from('<I', data, 28)[0]
phentsize, phnum = struct.unpack_from('<HH', data, 42)


def map_addr(addr):
    for i in range(phnum):
        off = phoff + i * phentsize
        p_type, p_offset, p_vaddr, _p_paddr, p_filesz, _p_memsz, _p_flags, _p_align = struct.unpack_from(
            '<8I', data, off
        )
        if p_type == 1 and p_vaddr <= addr < p_vaddr + p_filesz:
            return p_offset + (addr - p_vaddr)
    return None


ra = 0x004BA8F4
print('--- code near ra ---')
for pc in range(ra - 0x40, ra + 0x20, 4):
    fo = map_addr(pc)
    word = struct.unpack_from('<I', data, fo)[0]
    print(f'0x{pc:08X}: {word:08X}')

print('--- pointer table near 0x006CB790 ---')
targets = set()
for addr in range(0x006CB700, 0x006CB900, 4):
    fo = map_addr(addr)
    if fo is None:
        continue
    ptr = struct.unpack_from('<I', data, fo)[0]
    if 0x006C0000 <= ptr < 0x00700000 and (ptr & 3) == 0:
        targets.add(ptr)
        print(f'[0x{addr:08X}] -> 0x{ptr:08X}')

entries = Path(r'C:\PS2Recomp\games') / gid / 'entries.txt'
added = 0
for t in sorted(targets):
    before = set(entries.read_text().split()) if entries.exists() else set()
    try:
        add_entry(elf, entries, t)
    except ValueError as exc:
        print('skip', hex(t), exc)
        continue
    after = set(entries.read_text().split())
    if after - before:
        added += 1
print('newly added', added, 'total entries', len(entries.read_text().split()), 'targets', len(targets))
