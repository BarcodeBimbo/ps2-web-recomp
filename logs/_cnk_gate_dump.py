#!/usr/bin/env python3
"""Dump CNK Alchemy gate/state words from explore_ram and correlate with strings."""
from pathlib import Path
import struct

ram = Path(r"C:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\explore_ram.bin").read_bytes()
print("ram", len(ram))

addrs = [
    0x702BA0, 0x705BE0, 0x705BF0, 0x705C00, 0x705C10, 0x705C18, 0x705C20,
    0x705DF8, 0x705F10, 0x654290, 0x6542A0, 0x6542D8, 0x7430C0, 0x7504C0,
    0x782800, 0x1856B58 & 0x1FFFFFF,  # ready_be0 looked like ptr
]
for a in addrs:
    if a + 16 > len(ram):
        print(hex(a), "OOB")
        continue
    words = struct.unpack_from("<4I", ram, a)
    print(f"{a:08X}: " + " ".join(f"{w:08X}" for w in words), end="")
    # ascii hint
    chunk = ram[a : a + 16]
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    print(f"  |{asc}|")

# Follow pointer at 705BE0 from live dump was 01856B58 - check explore
be0 = struct.unpack_from("<I", ram, 0x705BE0)[0]
print("705BE0 ptr", hex(be0))
if be0 and be0 < len(ram):
    print(" *", " ".join(f"{w:08X}" for w in struct.unpack_from("<8I", ram, be0)))

# Search for references to 0x500C near code that might be SIID status checks on EE
hits = []
for a in range(0, len(ram) - 4, 4):
    w = struct.unpack_from("<I", ram, a)[0]
    if w == 0x500C:
        hits.append(a)
print("literal 0x500C count", len(hits), "first", [hex(h) for h in hits[:15]])

# Disassemble around WaitSema callers from dump: ra 0x423004 and 0x427234
# Just dump words as raw for now
for base in (0x422F80, 0x423000, 0x4271C0, 0x427200, 0x416E00):
    print(f"\ncode @{base:08X}")
    for i in range(0, 64, 4):
        w = struct.unpack_from("<I", ram, base + i)[0]
        print(f"  {base+i:08X}: {w:08X}")
