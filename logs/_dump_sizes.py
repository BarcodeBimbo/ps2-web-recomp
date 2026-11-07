import struct

d = open(r"c:\PS2Recomp\logs\cnk-plantok.ram", "rb").read()

def dump(addr, n=64):
    print(f"=== {addr:#x} ===")
    for off in range(0, n, 4):
        a = addr + off
        v = struct.unpack_from("<I", d, a)[0]
        extra = ""
        if v in (4248, 400437, 0x750CC0, 3, 196, 1, 2):
            extra += f" VAL={v}"
        if 0x100000 < v < 0x2000000:
            head = d[v : v + 8].hex()
            extra += f" PTR head={head}"
        print(f"  {a:08X}={v:08X}{extra}")

for a in [0x6F5A00, 0x7B3F80, 0x7B4750, 0x7B4800, 0x70CDE0]:
    dump(a, 80)
