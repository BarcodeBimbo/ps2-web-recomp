import struct

d = open(r"c:\PS2Recomp\logs\cnk-ee1.ram", "rb").read()
# Find virt LBAs
for lba, name in [(0xF0000000, "buta"), (0xF0000003, "intro")]:
    hits = []
    for a in range(0, min(len(d) - 4, 0x1E00000), 4):
        if struct.unpack_from("<I", d, a)[0] == lba:
            hits.append(a)
    print(name, "lba hits", [hex(h) for h in hits])
    for a in hits:
        print(f"  @{a:#x}:", d[a : a + 48].hex())
        for off in range(0, 48, 4):
            v = struct.unpack_from("<I", d, a + off)[0]
            if v in (4248, 400437, 0x1B00000, 0x1B80000, 0x750CC0) or (0x100000 < v < 0x2000000 and off > 0):
                print(f"    +{off:02X}={v:#x}")

# After UI setup, check slot objs again
lg = struct.unpack_from("<I", d, 0x6F2540)[0]
for i in [0, 3]:
    base = lg + i * 96
    st = struct.unpack_from("<I", d, base + 0x50)[0]
    st76 = struct.unpack_from("<I", d, base + 0x54)[0]
    obj = struct.unpack_from("<I", d, base + 0x58)[0]
    cb = struct.unpack_from("<I", d, base + 0x5C)[0]
    print(f"slot{i} st={st} +76={st76} obj={obj:#x} cb={cb:#x}")
