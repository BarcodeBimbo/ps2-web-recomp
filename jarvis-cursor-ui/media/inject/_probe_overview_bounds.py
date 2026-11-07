"""Locate overview panel bounds in reference-command-center-2.png."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media")
im = Image.open(ROOT / "reference-command-center-2.png").convert("RGBA")
arr = np.asarray(im.convert("RGB"))
r, g, b = [arr[:, :, i].astype(np.int16) for i in range(3)]
cyan = (b > 120) & (g > 80) & (r < 110) & (b > r + 30)

lefts = []
for x in range(150, 220):
    c = int(cyan[58:265, x].sum())
    if c >= 10:
        lefts.append((x, c))
print("left edges", lefts)

rights = []
for x in range(280, 380):
    c = int(cyan[58:265, x].sum())
    if c >= 10:
        rights.append((x, c))
print("right edges", rights[:12], "...", rights[-5:] if rights else None)

tops, bots = [], []
for y in range(45, 90):
    c = int(cyan[y, 185:340].sum())
    if c >= 15:
        tops.append((y, c))
for y in range(240, 290):
    c = int(cyan[y, 185:340].sum())
    if c >= 12:
        bots.append((y, c))
print("tops", tops[:8])
print("bots", bots[:8])

out = ROOT / "inject" / "_probe"
out.mkdir(exist_ok=True)
for i, box in enumerate(
    [
        (178, 52, 348, 268),
        (182, 55, 345, 265),
        (185, 58, 342, 262),
        (190, 60, 340, 260),
        (200, 40, 420, 280),  # prior probe
    ]
):
    c = im.crop(box)
    d = ImageDraw.Draw(c)
    d.rectangle((0, 0, c.width - 1, c.height - 1), outline=(255, 0, 0, 255))
    p = out / f"ov_box_{i}.png"
    c.save(p)
    print("saved", p.name, box, c.size)
