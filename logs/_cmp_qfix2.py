from pathlib import Path
import hashlib

def h(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()[:12]

gp = Path("logs/sly-gameplay")
qf = Path("logs/sly-gameplay-qfix2")
for f in range(300, 2100, 300):
    name = "frame_%05d.ppm" % f
    a = gp / name
    b = qf / name
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

wo, ho, po = load(gp / "frame_01800.ppm")
wn, hn, pn = load(qf / "frame_01800.ppm")
n = wo * ho
ch = 0
sumd = 0
for i in range(0, len(po), 3):
    d = abs(po[i] - pn[i]) + abs(po[i + 1] - pn[i + 1]) + abs(po[i + 2] - pn[i + 2])
    if d:
        ch += 1
    sumd += d
print("changed %d/%d (%.3f%%) meanL1 %.3f" % (ch, n, 100 * ch / n, sumd / n))

def darkfrac(px, w):
    dark = tot = 0
    for y in range(160, 300):
        for x in range(100, 500):
            i = (y * w + x) * 3
            tot += 1
            if px[i] + px[i + 1] + px[i + 2] < 40:
                dark += 1
    return dark / tot

print("roof dark old", darkfrac(po, wo), "new", darkfrac(pn, wn))
