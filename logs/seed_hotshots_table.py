from pathlib import Path
import struct

gid = "f29093e1f939f924fb11cc605b592b11"
root = Path(f"games/{gid}")
elf = (root / "disc/boot.elf").read_bytes()
phoff = struct.unpack_from("<I", elf, 28)[0]
phentsize, phnum = struct.unpack_from("<HH", elf, 42)
loads = []
for i in range(phnum):
    off = phoff + i * phentsize
    t, offset, vaddr, paddr, filesz, memsz, flags, align = struct.unpack_from("<IIIIIIII", elf, off)
    if t == 1:
        loads.append((vaddr, offset, filesz, memsz, flags))


def read_va(va, n):
    for vaddr, offset, filesz, memsz, flags in loads:
        if vaddr <= va < vaddr + memsz:
            if va - vaddr + n <= filesz:
                return elf[offset + (va - vaddr) : offset + (va - vaddr) + n]
            return None
    return None


print("table 0x338300:")
for va in range(0x338300, 0x338400, 4):
    b = read_va(va, 4)
    if not b:
        continue
    p = struct.unpack("<I", b)[0]
    mark = ""
    if 0x100000 <= p <= 0x400000 and (p & 3) == 0:
        c = read_va(p, 4)
        if c:
            mark = f" CODE first={struct.unpack('<I', c)[0]:08x}"
    print(f"  {va:08x}: {p:08x}{mark}")

targets = set()
for base in range(0x337000, 0x33A000, 4):
    b = read_va(base, 4)
    if not b:
        continue
    p = struct.unpack("<I", b)[0]
    if 0x00320000 <= p <= 0x00380000 and (p & 3) == 0 and read_va(p, 4):
        targets.add(p)

print("code ptr targets in 0x337000-0x33A000:", len(targets))
print(sorted(f"{t:x}" for t in targets))

starts = set(targets)
for va in range(0x00332000, 0x00338000, 4):
    code = read_va(va, 4)
    if not code:
        continue
    w = struct.unpack("<I", code)[0]
    if (w & 0xFFFF0000) == 0x27BD0000 and (w & 0xFFFF) >= 0x8000:
        starts.add(va)
    if w == 0x03E00008:
        starts.add(va)

entries_path = root / "entries.txt"
existing = set()
lines = []
for line in entries_path.read_text().splitlines():
    lines.append(line)
    s = line.strip()
    if not s or s.startswith("#"):
        continue
    existing.add(int(s, 16))

new = sorted(a for a in starts if a not in existing)
print("existing", len(existing), "new", len(new))
print([f"{x:x}" for x in new])

# Write hex lowercase without 0x to match current file style
fmt = "x"
if existing:
    sample = next(iter(existing))
    # detect if entries use 0x prefix
    raw = entries_path.read_text()
    fmt = "0x" if "0x" in raw.lower() else "x"

added = []
for a in new:
    text = f"0x{a:08X}" if fmt == "0x" else f"{a:x}"
    lines.append(text)
    added.append(text)

if added:
    entries_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print("wrote", len(added), "entries")
else:
    print("nothing to write")
