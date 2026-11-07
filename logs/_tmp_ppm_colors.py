from pathlib import Path
from collections import Counter

def parse_ppm(path: Path):
    data = path.read_bytes()
    i = 0

    def tok():
        nonlocal i
        while i < len(data) and data[i] in b" \t\r\n":
            i += 1
        if i < len(data) and data[i] == 35:
            while i < len(data) and data[i] != 10:
                i += 1
            return tok()
        j = i
        while j < len(data) and data[j] not in b" \t\r\n":
            j += 1
        t = data[i:j]
        i = j
        return t

    assert tok() == b"P6"
    w, h, _ = int(tok()), int(tok()), int(tok())
    while i < len(data) and data[i] in b" \t\r":
        i += 1
    if i < len(data) and data[i] == 10:
        i += 1
    pix = data[i : i + w * h * 3]
    return w, h, pix


cap = Path(r"c:\PS2Recomp\logs\hitman-capture-post-xyoffset-2026-11-07")
for name in ["000000_fbp120_psm00.ppm", "000001_fbp190_psm00.ppm", "001128_fbp120_psm00.ppm", "001129_fbp190_psm00.ppm"]:
    w, h, pix = parse_ppm(cap / name)
    c = Counter()
    for k in range(0, len(pix), 3):
        rgb = (pix[k], pix[k + 1], pix[k + 2])
        if rgb != (0, 0, 0):
            c[rgb] += 1
    print(name, "nonzero_colors", len(c), "top", c.most_common(8))
