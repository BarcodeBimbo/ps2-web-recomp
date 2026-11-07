# -*- coding: utf-8 -*-
from pathlib import Path
import numpy as np
from PIL import Image

LIVE = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media\image.png")
REF = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media\reference-command-center-2.png")
OUT = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media\inject\_audit_deep")
OUT.mkdir(exist_ok=True)

live = Image.open(LIVE).convert("RGB")
ref = Image.open(REF).convert("RGB")
lw, lh = live.size
rw, rh = ref.size
print("LIVE", lw, lh, "REF", rw, rh)

live_s = live.resize((rw, rh), Image.Resampling.LANCZOS)
a = np.asarray(ref).astype("float32")
b = np.asarray(live_s).astype("float32")
d = np.abs(a - b).mean(axis=2)
dh = np.clip(d * 2.5, 0, 255).astype("uint8")
heat = Image.fromarray(dh, "L")
heat.convert("RGB").save(OUT / "diff_heat.png")
red = Image.merge("RGB", (heat, Image.new("L", (rw, rh), 0), Image.new("L", (rw, rh), 0)))
Image.blend(ref, red, 0.5).save(OUT / "diff_overlay.png")
live_s.save(OUT / "live_scaled_to_ref.png")

cols, rows = 6, 5
cw, ch = rw // cols, rh // rows
for r in range(rows):
    for c in range(cols):
        x0, y0 = c * cw, r * ch
        x1 = rw if c == cols - 1 else (c + 1) * cw
        y1 = rh if r == rows - 1 else (r + 1) * ch
        box = (x0, y0, x1, y1)
        ref.crop(box).save(OUT / f"cell_r{r}c{c}_ref.png")
        live_s.crop(box).save(OUT / f"cell_r{r}c{c}_live.png")
        md = float(np.abs(a[y0:y1, x0:x1] - b[y0:y1, x0:x1]).mean())
        print(f"cell r{r}c{c} mean_delta={md:.1f}")

live_zones = {
    "L_brand": (0, 0, 320, 90),
    "L_status": (280, 8, 620, 70),
    "L_clock": (620, 0, 980, 80),
    "L_search_ops": (980, 0, 1450, 80),
    "L_win_btns": (1450, 0, 1598, 80),
    "L_nav": (0, 90, 250, 520),
    "L_voice": (0, 520, 250, 780),
    "L_focus": (0, 780, 250, 860),
    "L_overview": (250, 85, 520, 340),
    "L_globe": (520, 85, 1050, 340),
    "L_feed": (1050, 85, 1590, 340),
    "L_agents": (250, 340, 820, 520),
    "L_timeline": (820, 340, 1250, 520),
    "L_qc": (1250, 340, 1590, 520),
    "L_monitor": (250, 520, 700, 780),
    "L_memory": (700, 520, 1050, 780),
    "L_llm": (1050, 520, 1590, 780),
    "L_footer_meta": (0, 800, 450, 899),
    "L_talk": (450, 800, 1150, 899),
    "L_brief": (1150, 800, 1598, 899),
}
for name, box in live_zones.items():
    live.crop(box).save(OUT / f"{name}.png")

ref_zones = {
    "R_brand": (0, 0, 200, 50),
    "R_header": (200, 0, 750, 50),
    "R_tools": (750, 0, 1024, 50),
    "R_nav": (0, 50, 157, 400),
    "R_voice": (0, 400, 157, 510),
    "R_overview": (165, 52, 375, 280),
    "R_globe": (380, 52, 650, 280),
    "R_feed": (655, 52, 1010, 280),
    "R_agents": (165, 288, 500, 440),
    "R_timeline": (505, 288, 750, 440),
    "R_qc": (755, 288, 1010, 440),
    "R_monitor": (165, 448, 420, 520),
    "R_memory": (425, 448, 650, 520),
    "R_llm": (655, 448, 1010, 520),
    "R_footer": (0, 525, 1024, 573),
}
for name, box in ref_zones.items():
    c = ref.crop(box)
    c.resize((c.width * 2, c.height * 2), Image.Resampling.NEAREST).save(OUT / f"{name}.png")


def border_run(im, x, y, axis="x"):
    px = im.load()
    w, h = im.size

    def lum(c):
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

    if axis == "x":
        best, bl = x, lum(px[x, y])
        for xx in range(max(0, x - 6), min(w, x + 7)):
            L = lum(px[xx, y])
            if L > bl:
                best, bl = xx, L
        thr = bl * 0.45
        lo = best
        while lo > 0 and lum(px[lo - 1, y]) >= thr:
            lo -= 1
        hi = best
        while hi < w - 1 and lum(px[hi + 1, y]) >= thr:
            hi += 1
        return hi - lo + 1, best, int(bl)
    best, bl = y, lum(px[x, y])
    for yy in range(max(0, y - 6), min(h, y + 7)):
        L = lum(px[x, yy])
        if L > bl:
            best, bl = yy, L
    thr = bl * 0.45
    lo = best
    while lo > 0 and lum(px[x, lo - 1]) >= thr:
        lo -= 1
    hi = best
    while hi < h - 1 and lum(px[x, hi + 1]) >= thr:
        hi += 1
    return hi - hi + 1 if False else hi - lo + 1, best, int(bl)


# Sample border thicknesses at likely panel edges on LIVE
samples = [
    ("live_overview_left", 255, 160, "x"),
    ("live_overview_top", 360, 95, "y"),
    ("live_feed_left", 1055, 160, "x"),
    ("live_agents_top", 400, 345, "y"),
    ("live_search_border", 1100, 35, "y"),
    ("live_talk_rim", 800, 830, "y"),
]
print("BORDER_SAMPLES")
for name, x, y, ax in samples:
    t, peak, L = border_run(live, x, y, ax)
    print(f"  {name}: thick~{t}px peak@{peak} lum={L}")

# Count near-black interiors in memory / overview
px = live.load()


def dark_frac(box, thr=12):
    x0, y0, x1, y1 = box
    dark = tot = 0
    for y in range(y0, y1, 2):
        for x in range(x0, x1, 2):
            c = px[x, y]
            L = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
            tot += 1
            if L < thr:
                dark += 1
    return dark / tot if tot else 0


print("DARK_FRAC overview", round(dark_frac((270, 120, 500, 320)), 3))
print("DARK_FRAC memory", round(dark_frac((720, 560, 1020, 760)), 3))
print("DARK_FRAC globe", round(dark_frac((560, 120, 1000, 320)), 3))
print("DARK_FRAC llm", round(dark_frac((1080, 560, 1550, 750)), 3))
print("done", len(list(OUT.glob('*.png'))))
