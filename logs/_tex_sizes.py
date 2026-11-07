from pathlib import Path
from collections import Counter

lines = Path("logs/sly-cap1800/draws.tsv").read_text().splitlines()
sizes = Counter()
for line in lines[1:]:
    if not line or line.startswith(("vblank", "image", "transfer")):
        continue
    f = line.split("\t")
    if len(f) < 12:
        continue
    try:
        tex0 = int(f[7], 16)
        prims = int(f[1])
    except ValueError:
        continue
    tw = (tex0 >> 26) & 15
    th = (tex0 >> 30) & 15
    psm = (tex0 >> 20) & 63
    sizes[(1 << tw, 1 << th, psm)] += prims
print("tex sizes (w,h,psm)", sizes.most_common(15))
