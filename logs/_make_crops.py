from pathlib import Path
import struct

def load(p):
    data = Path(p).read_bytes()
    rest = data[data.find(b"\n") + 1 :]
    while rest.startswith(b"#"):
        rest = rest[rest.find(b"\n") + 1 :]
    nl = rest.find(b"\n")
    w, h = map(int, rest[:nl].split())
    rest = rest[nl + 1 :]
    nl = rest.find(b"\n")
    return w, h, rest[nl + 1 :]

def crop_bmp(ppm, out, x0, y0, x1, y1, scale=4):
    w, h, px = load(ppm)
    cw, ch = x1 - x0, y1 - y0
    sw, sh = cw * scale, ch * scale
    img = bytearray()
    for y in range(sh - 1, -1, -1):
        sy = y0 + y // scale
        for x in range(sw):
            sx = x0 + x // scale
            i = (sy * w + sx) * 3
            img += bytes([px[i + 2], px[i + 1], px[i]])
        pad = (4 - (sw * 3) % 4) % 4
        img += b"\x00" * pad
    hb = struct.pack("<2sIHHI", b"BM", 14 + 40 + len(img), 0, 0, 54)
    hib = struct.pack("<IiiHHIIiiII", 40, sw, sh, 1, 24, 0, len(img), 2835, 2835, 0, 0)
    Path(out).write_bytes(hb + hib + img)
    print("wrote", out, sw, sh)

crop_bmp("logs/sly-gameplay/frame_01800.ppm", "logs/_crop_old1800.bmp", 200, 170, 400, 280, 3)
crop_bmp("logs/sly-gameplay-qfix2/frame_01800.ppm", "logs/_crop_new1800.bmp", 120, 250, 400, 400, 3)
crop_bmp("logs/sly-gameplay/frame_01500.ppm", "logs/_crop_old1500.bmp", 200, 200, 450, 320, 3)
crop_bmp("logs/sly-gameplay-qfix2/frame_01500.ppm", "logs/_crop_new1500.bmp", 200, 200, 450, 320, 3)
