#!/usr/bin/env python3
from pathlib import Path
import struct

ee = Path("logs/cnk-stbl0.ram").read_bytes()

ptr_loc = 0x6CFCA8
print(f"context around {ptr_loc:#x}:")
for a in range(ptr_loc - 0x40, ptr_loc + 0x80, 4):
    v = struct.unpack_from("<I", ee, a)[0]
    mark = " <<<" if a == ptr_loc else ""
    note = ""
    if 0x100000 <= v < 0x700000:
        note = " code?"
    print(f"  {a:08X}: {v:08X}{note}{mark}")

# Who writes 0x23ED50 into memory? Search for lui/addiu constructing it
# 0x23ED50 = lui ?, 0x24; addiu ?, ?, -0x12B0  (0x240000-0x12B0=0x23ED50)
# or lui 0x23; ori 0xED50
print("\nconstructors of 0x23ED50:")
for a in range(0x100000, 0x700000, 4):
    w = struct.unpack_from("<I", ee, a)[0]
    if ((w >> 26) & 0x3F) == 0xF and (w & 0xFFFF) in (0x23, 0x24):
        rt = (w >> 16) & 0x1F
        hi = w & 0xFFFF
        for j in range(1, 6):
            w2 = struct.unpack_from("<I", ee, a + j * 4)[0]
            op = (w2 >> 26) & 0x3F
            if op == 9 and ((w2 >> 21) & 0x1F) == rt and ((w2 >> 16) & 0x1F) == rt:
                sim = w2 & 0xFFFF
                sim = sim - 0x10000 if sim & 0x8000 else sim
                val = ((hi << 16) + sim) & 0xFFFFFFFF
                if val == 0x23ED50:
                    print(f"  {a:08X} lui+addiu -> 0x23ED50")
            if op == 0xD and ((w2 >> 21) & 0x1F) == rt and ((w2 >> 16) & 0x1F) == rt:
                val = ((hi << 16) | (w2 & 0xFFFF)) & 0xFFFFFFFF
                if val == 0x23ED50:
                    print(f"  {a:08X} lui+ori -> 0x23ED50")

# Also search stores of that address - look at vtable at 0x6cfa80 from earlier
print("\nvtable 0x6cfa80 dump (more):")
vt = 0x6CFA80
for i in range(0, 0x80, 4):
    v = struct.unpack_from("<I", ee, vt + i)[0]
    print(f"  +{i:02X}: {v:08X}")

# 0x6cfca8 - 0x6cfa80 = 0x228 = 552. Not the same vtable.
# What object points here?
print("\npointers to 0x6CFCA8:")
hits = []
for a in range(0, min(len(ee) - 4, 0x2000000), 4):
    if struct.unpack_from("<I", ee, a)[0] == 0x6CFCA8:
        hits.append(a)
        if len(hits) >= 20:
            break
print([hex(h) for h in hits])

print("\npointers to 0x6CFA80 (vtable):")
hits = []
for a in range(0, min(len(ee) - 4, 0x2000000), 4):
    if struct.unpack_from("<I", ee, a)[0] == 0x6CFA80:
        hits.append(a)
        if len(hits) >= 20:
            break
print([hex(h) for h in hits])

# Object at 0x752340 had vtable 0x6cfa80
obj = 0x752340
print(f"\nobject {obj:#x}:")
for i in range(0, 0x40, 4):
    print(f"  +{i:02X}: {struct.unpack_from('<I', ee, obj + i)[0]:08X}")

# Find who calls through pointer at 0x6cfca8 — look for lui 0x6d; lw ?, 0xFCA8-0x10000?
# 0x6CFCA8: lui x,0x6D; lw y, -855(x) because 0x6D0000-855=0x6CFCA9? 
# 0x6CFCA8 - 0x6D0000 = -855 = 0xFCA9? Wait -0x3558?
off = 0x6CFCA8 - 0x6D0000
print(f"\noffset from 0x6D0000: {off} ({off & 0xFFFF:#x})")
off2 = 0x6CFCA8 - 0x6C0000
print(f"offset from 0x6C0000: {off2} ({off2 & 0xFFFF:#x})")

# Search lw with those offsets
for base, off in [(0x6D, off & 0xFFFF), (0x6C, off2 & 0xFFFF)]:
    print(f"lw sites lui {base:#x} + off {off:#x}:")
    for a in range(0x100000, 0x700000, 4):
        w = struct.unpack_from("<I", ee, a)[0]
        if ((w >> 26) & 0x3F) != 0xF or (w & 0xFFFF) != base:
            continue
        for j in range(1, 5):
            w2 = struct.unpack_from("<I", ee, a + j * 4)[0]
            if ((w2 >> 26) & 0x3F) == 0x23 and (w2 & 0xFFFF) == (off & 0xFFFF):
                print(f"  {a:08X}")
