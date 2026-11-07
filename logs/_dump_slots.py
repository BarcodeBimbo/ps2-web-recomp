import struct
d = open(r"c:\PS2Recomp\logs\cnk-f0f4b.ram", "rb").read()
lg = 0x74A2B0
for i in [0, 3]:
    base = lg + i * 96
    print(f"=== slot {i} ===")
    raw = d[base : base + 96]
    print("ascii", "".join(chr(b) if 32 <= b < 127 else "." for b in raw[:48]))
    for off in range(0, 96, 4):
        v = struct.unpack_from("<I", d, base + off)[0]
        extra = ""
        if 0x100000 < v < 0x2000000:
            extra += " PTR"
        print(f"  +{off:02X}={v:08X}{extra}")
