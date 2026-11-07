import struct

d = open(r"c:\PS2Recomp\logs\cnk-plantok.ram", "rb").read()
# Find size constants and nearby pointers
for want, name in [(4248, "buta_sz"), (400437, "intro_sz"), (0x1098, "buta_hex"), (0x61C35, "intro_hex")]:
    hits = []
    for a in range(0, min(len(d) - 4, 0x1E00000), 4):
        if struct.unpack_from("<I", d, a)[0] == want:
            hits.append(a)
    print(name, "count", len(hits), "first", [hex(h) for h in hits[:12]])

print("--- slot shared structs ---")
for a in [0x7E02A4, 0x974358]:
    print(hex(a), d[a : a + 64].hex())
    for off in range(0, 64, 4):
        v = struct.unpack_from("<I", d, a + off)[0]
        mark = ""
        if v in (4248, 400437, 0x750CC0, 0x1B00000, 0x1B80000):
            mark = " INTERESTING"
        if 0x100000 < v < 0x2000000:
            mark += " PTR"
        if mark:
            print(f"  +{off:02X}={v:08X}{mark}")

print("--- search ptrs to plant ---")
for plant in (0x1B00000, 0x1B80000):
    refs = []
    for a in range(0x100000, min(len(d) - 4, 0x1E00000), 4):
        if struct.unpack_from("<I", d, a)[0] == plant:
            refs.append(a)
    print(hex(plant), "refs", [hex(r) for r in refs[:20]], "n", len(refs))
