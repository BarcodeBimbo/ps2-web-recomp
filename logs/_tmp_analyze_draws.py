from collections import Counter
from pathlib import Path

p = Path(r"c:\PS2Recomp\logs\hitman-capture-post-xyoffset-2026-11-07\draws.tsv")
fbps = Counter()
zero_w = zero_h = total = 0
box_samples = []
dest400 = []
for line in p.read_text(errors="replace").splitlines()[2:]:
    if not line or line[0].isalpha():
        continue
    cols = line.split("\t")
    if len(cols) < 13:
        continue
    try:
        frame = int(cols[5], 16)
    except ValueError:
        continue
    fbp = frame & 0x1FF
    fbps[fbp] += 1
    total += 1
    box = cols[12]
    try:
        a, b = box.split("-")
        x0, y0 = map(float, a.split(","))
        x1, y1 = map(float, b.split(","))
    except Exception:
        continue
    w = abs(x1 - x0)
    h = abs(y1 - y0)
    if w < 1:
        zero_w += 1
    if h < 1:
        zero_h += 1
    if len(box_samples) < 12:
        box_samples.append((cols[0], cols[4], fbp, box, w, h, cols[7]))
    if fbp == 0x190 and len(dest400) < 15:
        tex0 = int(cols[7], 16) if cols[7] else 0
        dest400.append(
            {
                "draw": cols[0],
                "prim": cols[4],
                "tex0": cols[7],
                "tbp": tex0 & 0x3FFF,
                "tbw": (tex0 >> 14) & 0x3F,
                "tpsm": (tex0 >> 20) & 0x3F,
                "box": box,
                "w": w,
                "h": h,
                "texels": cols[13][:60] if len(cols) > 13 else "",
            }
        )

print("total_draws", total)
print("fbps", dict(fbps.most_common()))
print("zero_width", zero_w, "zero_height", zero_h)
print("samples")
for s in box_samples:
    print(s)
print("dest400")
for d in dest400:
    print(d)
