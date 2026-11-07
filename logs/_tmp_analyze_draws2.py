from pathlib import Path
from collections import Counter

p = Path(r"c:\PS2Recomp\logs\hitman-capture-post-xyoffset-2026-11-07\draws.tsv")
tests = Counter()
prims = Counter()
big_uv = 0
area_ok = 0
tme_on = 0
for line in p.read_text(errors="replace").splitlines()[2:]:
    if not line or line[0].isalpha():
        continue
    cols = line.split("\t")
    if len(cols) < 14:
        continue
    try:
        test = int(cols[11], 16)
        prim = int(cols[4], 16)
    except ValueError:
        continue
    tests[test] += 1
    prims[prim] += 1
    if prim & 0x10:
        tme_on += 1
    tex = cols[13]
    if "inf" in tex or "e+" in tex.lower() or "100000001504" in tex:
        big_uv += 1
    try:
        a, b = cols[12].split("-")
        x0, y0 = map(float, a.split(","))
        x1, y1 = map(float, b.split(","))
        if abs(x1 - x0) >= 1 and abs(y1 - y0) >= 1:
            area_ok += 1
    except Exception:
        pass

print("tests", tests.most_common(8))
print("prims", prims.most_common(12))
print("tme_on", tme_on, "big_uv_batches", big_uv, "area_ok", area_ok)
