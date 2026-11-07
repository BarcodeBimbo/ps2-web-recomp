from pathlib import Path

p = Path(r"c:\PS2Recomp\logs\hitman-capture-post-xyoffset-2026-11-07\draws.tsv")
# Capture boxes were computed with 11-bit OFX≈0, OFY≈32.
# Under true 16-bit OFX=0x7000 (1792px), OFY=0x7200 (1824px):
# screen = box - (1792, 1824-32) = box - (1792, 1792) approximately if oy_11=32
# More precisely: capture_box = (vtx - of_11)/16; true_screen = (vtx - of_16)/16
# = capture_box - (of_16 - of_11)/16
dx = 1792.0 - 0.0
dy = 1824.0 - 32.0
on = 0
off = 0
partial = 0
samples = []
for line in p.read_text(errors="replace").splitlines()[2:]:
    if not line or line[0].isalpha():
        continue
    cols = line.split("\t")
    if len(cols) < 13:
        continue
    try:
        a, b = cols[12].split("-")
        x0, y0 = map(float, a.split(","))
        x1, y1 = map(float, b.split(","))
    except Exception:
        continue
    # reorder
    xa, xb = sorted((x0 - dx, x1 - dx))
    ya, yb = sorted((y0 - dy, y1 - dy))
    # visible 0..511 x 0..447
    ix0, ix1 = max(xa, 0), min(xb, 511)
    iy0, iy1 = max(ya, 0), min(yb, 447)
    if ix1 >= ix0 and iy1 >= iy0 and (ix1 - ix0) >= 1 and (iy1 - iy0) >= 1:
        on += 1
        if len(samples) < 8:
            samples.append((cols[0], cols[4], cols[12], (xa, ya, xb, yb)))
    elif ix1 >= ix0 and iy1 >= iy0:
        partial += 1
    else:
        off += 1

print("with_16bit_ofx: on_screen_area", on, "partial_thin", partial, "off", off)
print("samples_on", samples)

# Also: how many current (11-bit) boxes are in 0..511
on11 = 0
for line in p.read_text(errors="replace").splitlines()[2:]:
    if not line or line[0].isalpha():
        continue
    cols = line.split("\t")
    if len(cols) < 13:
        continue
    try:
        a, b = cols[12].split("-")
        x0, y0 = map(float, a.split(","))
        x1, y1 = map(float, b.split(","))
    except Exception:
        continue
    xa, xb = sorted((x0, x1))
    ya, yb = sorted((y0, y1))
    if max(xa, 0) <= min(xb, 511) and max(ya, 0) <= min(yb, 447):
        if min(xb, 511) - max(xa, 0) >= 1 and min(yb, 447) - max(ya, 0) >= 1:
            on11 += 1
print("with_11bit_ofx: on_screen_area", on11)
