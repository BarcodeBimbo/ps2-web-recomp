from pathlib import Path
from collections import Counter

lines = Path("logs/sly-cap1800/draws.tsv").read_text().strip().splitlines()
fb = Counter()
zb = Counter()
for line in lines[1:]:
    if not line or line.startswith(("vblank", "image", "transfer")):
        continue
    f = line.split("\t")
    if len(f) < 12:
        continue
    try:
        frame = int(f[5], 16)
        zbuf = int(f[6], 16)
        prims = int(f[1])
    except ValueError:
        continue
    fpsm = (frame >> 24) & 0x3F
    fbp = frame & 0x1FF
    fbw = (frame >> 16) & 0x3F
    zpsm = (zbuf >> 24) & 0xF
    fb[(fpsm, fbw, fbp)] += prims
    zb[zpsm] += prims
print("frame targets", fb.most_common(10))
print("zpsm", zb.most_common())
