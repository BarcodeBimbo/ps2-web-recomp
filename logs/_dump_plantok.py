import struct

d = open(r"c:\PS2Recomp\logs\cnk-plantok.ram", "rb").read()
print("buta", d[0x1B00000:0x1B00000 + 16].hex())
print("intro", d[0x1B80000:0x1B80000 + 16].hex())
# count IGB headers in RAM
buta = bytes.fromhex("200100000F000000")
intro = bytes.fromhex("C402000024000000")
bh, ih = [], []
for a in range(0x100000, min(len(d), 0x1E00000) - 8, 4):
    h = d[a : a + 8]
    if h == buta:
        bh.append(a)
    if h == intro:
        ih.append(a)
print("buta hits", [hex(x) for x in bh[:20]], "count", len(bh))
print("intro hits", [hex(x) for x in ih[:20]], "count", len(ih))
lg = struct.unpack_from("<I", d, 0x6F2540)[0]
print("lg", hex(lg), "24008", d[lg + 24008], "24020", struct.unpack_from("<I", d, lg + 24020)[0])
for i in [0, 3]:
    base = lg + i * 96
    st = struct.unpack_from("<I", d, base + 0x50)[0]
    st76 = struct.unpack_from("<I", d, base + 0x54)[0]
    obj = struct.unpack_from("<I", d, base + 0x58)[0]
    cb = struct.unpack_from("<I", d, base + 0x5C)[0]
    path = "".join(chr(b) if 32 <= b < 127 else "." for b in d[base + 8 : base + 40])
    print(f"slot{i} st={st} +76={st76} obj={obj:X} cb={cb:X} path={path}")
    if 0x100000 < obj < 0x2000000:
        print("  obj+44/45", d[obj + 44], d[obj + 45])
        for off in range(0, 0x40, 4):
            v = struct.unpack_from("<I", d, obj + off)[0]
            if 0x100000 < v < 0x2000000:
                head = d[v : v + 8].hex()
                print(f"  obj+{off:02X}->{v:08X} head={head}")
