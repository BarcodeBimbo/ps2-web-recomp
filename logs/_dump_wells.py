import struct

d = open(r"c:\PS2Recomp\logs\cnk-wells.ram", "rb").read()
print("buta plant", d[0x1B00000:0x1B00000 + 16].hex())
print("intro plant", d[0x1B80000:0x1B80000 + 16].hex())
print("objbuf 97E528", d[0x97E528 : 0x97E528 + 16].hex())
lg = struct.unpack_from("<I", d, 0x6F2540)[0]
print("lg", hex(lg), "24008", d[lg + 24008], "24016", d[lg + 24016], "24020", struct.unpack_from("<I", d, lg + 24020)[0])
for i in range(4):
    base = lg + i * 96
    st = struct.unpack_from("<I", d, base + 0x50)[0]
    st76 = struct.unpack_from("<I", d, base + 0x54)[0]
    obj = struct.unpack_from("<I", d, base + 0x58)[0]
    cb = struct.unpack_from("<I", d, base + 0x5C)[0]
    path = "".join(chr(b) if 32 <= b < 127 else "." for b in d[base + 8 : base + 40])
    print(f"slot{i} st={st} +76={st76} obj={obj:X} cb={cb:X} path={path}")
    if obj and 0x100000 < obj < 0x2000000:
        print("  obj+44/45", d[obj + 44], d[obj + 45])
        for off in (0x00, 0x10, 0x14, 0x18, 0x1C, 0x20):
            v = struct.unpack_from("<I", d, obj + off)[0]
            head = d[v : v + 8].hex() if 0x100000 < v < len(d) - 8 else "-"
            print(f"  obj+{off:02X}={v:08X} head={head}")
