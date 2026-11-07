from pathlib import Path
import hashlib

def h(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()[:12]

gp = Path("logs/sly-gameplay")
qf = Path("logs/sly-gameplay-qfix3")
for f in range(300, 2100, 300):
    name = "frame_%05d.ppm" % f
    a, b = gp / name, qf / name
    same = a.exists() and b.exists() and a.read_bytes() == b.read_bytes()
    print("%d: gp=%s qf=%s same=%s" % (f, h(a) if a.exists() else "-", h(b) if b.exists() else "-", same))

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

def darkfrac(px, w, box=(120, 170, 480, 290)):
    x0, y0, x1, y1 = box
    dark = tot = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            i = (y * w + x) * 3
            tot += 1
            if px[i] + px[i + 1] + px[i + 2] < 40:
                dark += 1
    return dark / tot

def lap(px, w, box=(200, 160, 440, 300)):
    x0, y0, x1, y1 = box
    lums = []
    for y in range(y0, y1):
        row = []
        for x in range(x0, x1):
            i = (y * w + x) * 3
            row.append(0.299 * px[i] + 0.587 * px[i + 1] + 0.114 * px[i + 2])
        lums.append(row)
    e = n = 0
    for y in range(1, len(lums) - 1):
        for x in range(1, len(lums[0]) - 1):
            c = lums[y][x]
            e += abs(4 * c - lums[y][x - 1] - lums[y][x + 1] - lums[y - 1][x] - lums[y + 1][x])
            n += 1
    return e / max(1, n)

wo, ho, po = load(gp / "frame_01800.ppm")
wn, hn, pn = load(qf / "frame_01800.ppm")
n = wo * ho
ch = sumd = 0
for i in range(0, len(po), 3):
    d = abs(po[i] - pn[i]) + abs(po[i + 1] - pn[i + 1]) + abs(po[i + 2] - pn[i + 2])
    if d:
        ch += 1
    sumd += d
print("changed %d/%d (%.3f%%) meanL1 %.3f" % (ch, n, 100.0 * ch / n, sumd / n))
print("dark old %.4f new %.4f" % (darkfrac(po, wo), darkfrac(pn, wn)))
print("lap old %.3f new %.3f" % (lap(po, wo), lap(pn, wn)))
