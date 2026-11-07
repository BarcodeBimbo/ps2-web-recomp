from pathlib import Path
import math

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

def metrics(path, box):
    w, h, px = load(path)
    x0, y0, x1, y1 = box
    # local laplacian-ish energy and dark fraction
    energy = 0.0
    n = 0
    dark = 0
    lums = []
    for y in range(y0, y1):
        row = []
        for x in range(x0, x1):
            i = (y * w + x) * 3
            lum = 0.299 * px[i] + 0.587 * px[i + 1] + 0.114 * px[i + 2]
            row.append(lum)
            if px[i] + px[i + 1] + px[i + 2] < 40:
                dark += 1
        lums.append(row)
    for y in range(1, len(lums) - 1):
        for x in range(1, len(lums[0]) - 1):
            c = lums[y][x]
            lap = abs(4 * c - lums[y][x - 1] - lums[y][x + 1] - lums[y - 1][x] - lums[y + 1][x])
            energy += lap
            n += 1
    mean = sum(sum(r) for r in lums) / max(1, (y1 - y0) * (x1 - x0))
    return {
        "dark_frac": dark / max(1, (y1 - y0) * (x1 - x0)),
        "lap_mean": energy / max(1, n),
        "mean_lum": mean,
        "unique": len({(px[(y * w + x) * 3], px[(y * w + x) * 3 + 1], px[(y * w + x) * 3 + 2]) for y in range(y0, y1) for x in range(x0, x1)}),
    }

boxes = {
    "center": (200, 160, 440, 300),
    "roofL": (80, 180, 220, 280),
    "roofR": (360, 160, 520, 260),
}
files = [
    ("old1800", "logs/sly-gameplay/frame_01800.ppm"),
    ("old1500", "logs/sly-gameplay/frame_01500.ppm"),
    ("new1800", "logs/sly-gameplay-qfix2/frame_01800.ppm"),
    ("new1500", "logs/sly-gameplay-qfix2/frame_01500.ppm"),
]
for name, path in files:
    print("==", name)
    for bname, box in boxes.items():
        m = metrics(path, box)
        print(" ", bname, {k: round(v, 3) if isinstance(v, float) else v for k, v in m.items()})
