"""Crop soft-alpha globe hero from reference-command-center-2.png."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

SRC = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media\reference-command-center-2.png")
DEST = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media\inject\globe-hero.png")
PREVIEW = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media\inject\_globe_hero_preview.png")

# Globe + photo rings + short pedestal only (stop before agent cards)
L, T, R, B = 378, 62, 662, 318

im = Image.open(SRC).convert("RGBA")
crop = im.crop((L, T, R, B))
arr = np.array(crop).astype(np.float32)
h, w = arr.shape[:2]

rch = arr[:, :, 0]
gch = arr[:, :, 1]
bch = arr[:, :, 2]
cyan = ((bch - rch) + (gch - rch) * 0.35).clip(0, 255)
bright = 0.2 * rch + 0.45 * gch + 0.55 * bch

yy, xx = np.mgrid[0:h, 0:w]
cx, cy = w * 0.50, h * 0.46
rx, ry = w * 0.48, h * 0.50
ell = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2

px, py = w * 0.50, h * 0.88
prx, pry = w * 0.40, h * 0.16
pell = ((xx - px) / prx) ** 2 + ((yy - py) / pry) ** 2

sphere = ell <= 1.0
pedestal = pell <= 1.0
rings_zone = ell <= 1.28
glow = (cyan > 16) | (bright > 50)

alpha = np.zeros((h, w), dtype=np.float32)
alpha[sphere] = np.clip(200 + bright[sphere] * 0.35, 180, 255)
ring_vals = np.clip(cyan * 4.0 + bright * 0.8, 0, 255)
alpha[glow & rings_zone] = np.maximum(alpha[glow & rings_zone], ring_vals[glow & rings_zone])

pfeather = np.clip((1.2 - pell) / 0.4, 0, 1)
p_alpha = np.zeros_like(alpha)
p_alpha[pedestal] = np.clip(cyan[pedestal] * 5.5 + bright[pedestal] * 0.4, 0, 255) * pfeather[pedestal]
alpha = np.maximum(alpha, p_alpha)

feather = np.clip((1.32 - ell) / 0.32, 0, 1)
alpha = alpha * feather
alpha = np.maximum(alpha, p_alpha)

# Hard kill UI chrome below pedestal midline
alpha[yy > h * 0.93] = 0
# Kill rectangular card leftovers in lower corners
lower_corner = (yy > h * 0.78) & (~pedestal) & (ell > 0.95)
alpha[lower_corner] = 0
# Kill side panel leftovers
side = ((xx < w * 0.06) | (xx > w * 0.94)) & (ell > 1.05)
alpha[side] = 0

out = arr.copy()
out[:, :, 3] = alpha.clip(0, 255)
out_img = Image.fromarray(out.astype(np.uint8), "RGBA")
rgb = out_img.convert("RGB")
a_img = out_img.split()[-1].filter(ImageFilter.GaussianBlur(0.7))
out_img = Image.merge("RGBA", (*rgb.split(), a_img))

bbox = out_img.getbbox()
print("bbox", bbox, "pretrim", out_img.size)
if bbox:
    out_img = out_img.crop(bbox)

# Scale up slightly for crisp HUD display (2x nearest then soft — keep 1x for fidelity)
out_img.save(DEST, optimize=True, compress_level=9)
print("saved", DEST, out_img.size, DEST.stat().st_size)

prev = Image.new("RGBA", out_img.size, (2, 10, 24, 255))
prev = Image.alpha_composite(prev, out_img)
prev.convert("RGB").save(PREVIEW)
print("preview ok")
