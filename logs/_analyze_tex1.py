from pathlib import Path
from collections import Counter

lines = Path("logs/sly-cap1800/draws.tsv").read_text().strip().splitlines()
tex1_c = Counter()
mmin_c = Counter()
combo = Counter()
for line in lines[1:]:
    if not line or line.startswith(("vblank", "image", "transfer")):
        continue
    f = line.split("\t")
    if len(f) < 12:
        continue
    try:
        tex1 = int(f[8], 16)
        test = int(f[11], 16)
        prims = int(f[1])
    except ValueError:
        continue
    mmag = (tex1 >> 5) & 1
    mmin = (tex1 >> 6) & 7
    ate = test & 1
    atst = (test >> 1) & 7
    aref = (test >> 4) & 0xFF
    tex1_c[tex1 & 0x1FF] += prims
    mmin_c[mmin] += prims
    combo[(mmag, mmin, ate, atst, aref)] += prims

print("mmin", mmin_c.most_common())
print("tex1 low bits", tex1_c.most_common(12))
print("mmag/mmin/atest combos:")
for k, v in combo.most_common(20):
    print(k, v)
