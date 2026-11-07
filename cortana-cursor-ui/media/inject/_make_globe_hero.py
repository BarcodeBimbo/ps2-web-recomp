"""Crop soft-alpha globe hero from reference-command-center-2.png."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

SRC = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media\reference-command-center-2.png")
DEST = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media\inject\globe-hero.png")
PREVIEW = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media\inject\_globe_hero_preview.png")

# Centered on sphere+rings; stop before agent-card row
L, T, R, B = 390, 70, 650, 300

im = Image.open(SRC).convert("RGBA")
crop = im.crop((L, T, R, B))
arr = np.array(crop).astype(np.float32)
h, w = arr.shape[:2]

rch = arr[:, :, 0]
gch = arr[:, :, 1]
bch = arr[:, :, 2]
cyan = ((bch - rch) + (gch - rch) * 0.4).clip(0, 255)
bright = 0.25 * rch + 0.4 * gch + 0.55 * bch

yy, xx = np.mgrid[0:h, 0:w]
cx, cy = w * 0.5, h * 0.48
# Cover sphere + tilted rings
rx, ry = w * 0.46, h * 0.52
ell = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2

# Soft elliptical window
window = np.clip((1.08 - ell) / 0.28, 0, 1)

# Prefer glowing wireframe; keep dim navy core softer so panel bg shows through
core = np.clip(140 + bright * 0.5, 0, 220)
glow_boost = np.clip(cyan * 2.8 + bright * 0.35, 0, 255)
base_a = np.maximum(core * 0.55, glow_boost)
alpha = base_a * window

# Extra ring allowance (tilted ellipses poke past main sphere)
ring_window = np.clip((1.22 - ell) / 0.22, 0, 1)
ring_a = np.clip(cyan * 5.0, 0, 255) * ring_window
alpha = np.maximum(alpha, ring_a)

# Pedestal: short concentric floor under sphere
px, py = w * 0.5, h * 0.90
prx, pry = w * 0.38, h * 0.14
pell = ((xx - px) / prx) ** 2 + ((yy - py) / pry) ** 2
pwin = np.clip((1.05 - pell) / 0.3, 0, 1)
# only keep pedestal glow strokes, not solid fill
p_a = np.clip(cyan * 6.0 + (bright > 40) * 40, 0, 255) * pwin
alpha = np.maximum(alpha, p_a)

# Kill anything that looks like card chrome (bright horizontal bars / purple accents low)
low = yy > h * 0.86
purpleish = (rch > 40) & (bch > gch) & (rch > gch * 0.7)
alpha[low & purpleish] = 0
alpha[yy > h * 0.96] = 0

out = arr.copy()
out[:, :, 3] = alpha.clip(0, 255)
out_img = Image.fromarray(out.astype(np.uint8), "RGBA")
rgb = out_img.convert("RGB")
a_img = out_img.split()[-1].filter(ImageFilter.GaussianBlur(0.6))
out_img = Image.merge("RGBA", (*rgb.split(), a_img))

bbox = out_img.getbbox()
print("bbox", bbox, "pretrim", out_img.size)
if bbox:
    # pad 2px
    l, t, r, b = bbox
    out_img = out_img.crop((max(0, l - 2), max(0, t - 2), min(w, r + 2), min(h, b + 2)))

out_img.save(DEST, optimize=True, compress_level=9)
print("saved", DEST, out_img.size, DEST.stat().st_size)

prev = Image.new("RGBA", out_img.size, (2, 10, 24, 255))
prev = Image.alpha_composite(prev, out_img)
prev.convert("RGB").save(PREVIEW)
print("preview ok")
