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
        p_type, p_offset, p_vaddr, _a, p_filesz, _b, _c, _d = struct.unpack_from('<8I', data, off)
        if p_type == 1 and p_vaddr <= addr < p_vaddr + p_filesz:
            return p_offset + (addr - p_vaddr)
    return None


# Explore now stops with r13=0x006CB900 and miss 0x006CB3A0.
# Scan a broader pointer window covering constructor/init tables.
windows = [
    (0x006CB700, 0x006CBA00),
    (0x006BC2E0, 0x006BC400),
    (0x006CB900, 0x006CBC00),
]
targets = set()
for start, end in windows:
    print(f'--- window {start:#x}-{end:#x} ---')
    for addr in range(start, end, 4):
        fo = map_addr(addr)
        if fo is None:
            continue
        ptr = struct.unpack_from('<I', data, fo)[0]
        if 0x00600000 <= ptr < 0x00800000 and (ptr & 3) == 0:
            targets.add(ptr)

# Also add the current miss and nearby function prologues found via scan of
# addiu sp patterns in this range is too broad; stick to pointer tables.
miss = 0x006CB3A0
targets.add(miss)

entries = Path(r'C:\PS2Recomp\games') / gid / 'entries.txt'
before = set(entries.read_text().split())
added = 0
for t in sorted(targets):
    try:
        add_entry(elf, entries, t)
    except ValueError:
        continue
after = set(entries.read_text().split())
print('targets', len(targets), 'newly added', len(after - before), 'total', len(after))
print('has miss', f'{miss:x}' in after)
# Show a few around the new miss
for t in sorted(x for x in targets if 0x006CB000 <= x <= 0x006CB500):
    print(f'  {t:08X}')
