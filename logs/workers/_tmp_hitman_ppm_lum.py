import pathlib

def ppm_stats(path, crop=None):
    data = path.read_bytes()
    if data[:2] != b"P6":
        return None
    i = 2

    def next_tok():
        nonlocal i
        while i < len(data) and data[i] in b" \t\r\n":
            i += 1
        if i < len(data) and data[i] == ord("#"):
            while i < len(data) and data[i] not in b"\r\n":
                i += 1
            return next_tok()
        j = i
        while i < len(data) and data[i] not in b" \t\r\n":
            i += 1
        return data[j:i].decode()

    w = int(next_tok())
    h = int(next_tok())
    _maxv = int(next_tok())
    while i < len(data) and data[i] in b" \t\r\n":
        i += 1
    pixels = memoryview(data)[i:]
    cw, ch = crop if crop else (w, h)
    cw = min(cw, w)
    ch = min(ch, h)
    total = 0.0
    nz = 0
    n = cw * ch
    for y in range(ch):
        row = y * w * 3
        for x in range(cw):
            o = row + x * 3
            r, g, b = pixels[o], pixels[o + 1], pixels[o + 2]
            total += 0.299 * r + 0.587 * g + 0.114 * b
            if r | g | b:
                nz += 1
    return dict(w=w, h=h, mean=total / n / 255.0, nz=nz, n=n, pct=100.0 * nz / n)


def summarize(label, paths, crop=(512, 448)):
    print(f"\n== {label} ==")
    if not paths:
        print("(none)")
        return
    for p in paths:
        s = ppm_stats(p, crop)
        if not s:
            print(p.name, "not ppm")
            continue
        print(
            f"{p.name}: {s['w']}x{s['h']} mean_lum={s['mean']:.4f} "
            f"nz={s['nz']}/{s['n']} ({s['pct']:.3f}%)"
        )


for tag, root in [
    (
        "NOTME present",
        pathlib.Path(
            r"C:\PS2Recomp\logs\autonomous-pipeline\hitman-modeB-notme-20261107T190853\frames"
        ),
    ),
    (
        "TYPE7FST present",
        pathlib.Path(
            r"C:\PS2Recomp\logs\autonomous-pipeline\hitman-modeB-type7fst-20261107T191649"
        ),
    ),
]:
    if not root.exists():
        print(tag, "MISSING", root)
        continue
    frames = sorted(root.rglob("frame_*.ppm"))
    if not frames:
        frames = sorted(root.glob("*.ppm"))
    summarize(tag, frames[-6:] if len(frames) > 6 else frames)

cap = pathlib.Path(r"C:\PS2Recomp\logs\hitman-capture-type7fst-180-2026-11-07")
summarize("TYPE7FST capture FBP288 late", sorted(cap.glob("*fbp120*.ppm"))[-5:])
summarize("TYPE7FST capture FBP400 late", sorted(cap.glob("*fbp190*.ppm"))[-5:])
base = pathlib.Path(r"C:\PS2Recomp\logs\autonomous-pipeline\capture-post-xyoffset")
if base.exists():
    summarize("BASE FBP288", sorted(base.glob("*fbp120*.ppm"))[-3:])
    summarize("BASE FBP400", sorted(base.glob("*fbp190*.ppm"))[-3:])
