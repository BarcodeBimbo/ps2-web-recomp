from PIL import Image, ImageDraw, ImageEnhance
from pathlib import Path
import numpy as np

im = Image.open(r"c:\PS2Recomp\jarvis-cursor-ui\media\reference-command-center-2.png").convert("RGBA")
arr = np.array(im)
out = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media\_probe")
out.mkdir(exist_ok=True)

# Find cyan-ish bright pixels in bottom band to locate panels
y0, y1 = 380, 520
band = arr[y0:y1, :, :3].astype(np.float32)
# cyan: high B+G, low R relative
cyan = (band[:, :, 2] > 80) & (band[:, :, 1] > 60) & (band[:, :, 0] < band[:, :, 2] * 0.85)
# also detect panel borders (slightly brighter than bg)
bright = band.mean(axis=2) > 25

# column density of cyan
col_cyan = cyan.sum(axis=0)
col_bright = bright.sum(axis=0)
# print peaks
peaks = []
for x in range(0, len(col_cyan), 20):
    peaks.append((x, int(col_cyan[x : x + 20].sum()), int(col_bright[x : x + 20].sum())))
print("x_bucket cyan_sum bright_sum")
for p in peaks:
    print(p)

# Save annotated bottom strip
strip = im.crop((0, y0, 1024, y1)).convert("RGB")
draw = ImageDraw.Draw(strip)
for x in range(0, 1024, 40):
    draw.line([(x, 0), (x, strip.size[1])], fill=(80, 80, 80))
    draw.text((x + 2, 2), str(x), fill=(180, 180, 0))
for y in range(0, strip.size[1], 20):
    draw.line([(0, y), (1024, y)], fill=(60, 60, 60))
    draw.text((2, y + 2), str(y0 + y), fill=(180, 180, 0))
strip.save(out / "bottom_grid.png")

# Try tighter memory panel candidates based on layout (between gauges and LLM)
for name, box in {
    "mem1": (300, 400, 520, 510),
    "mem2": (310, 395, 530, 505),
    "mem3": (320, 398, 545, 508),
    "mem4": (280, 398, 500, 508),
    "mem5": (290, 400, 510, 512),
    "const_only": (310, 415, 450, 475),
    "stats_only": (450, 415, 530, 500),
}.items():
    crop = im.crop(box)
    # upscale x3 for readability
    up = crop.resize((crop.size[0] * 3, crop.size[1] * 3), Image.NEAREST)
    up.save(out / f"{name}_x3.png")
    crop.save(out / f"{name}.png")
    print(name, box, crop.size)

# Also check Latest_UI_Update
latest = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media\Latest_UI_Update.png")
if latest.exists():
    lim = Image.open(latest).convert("RGBA")
    print("latest size", lim.size)
    lw, lh = lim.size
    # scale map from 1024x573 if different
    lim.crop((int(280 * lw / 1024), int(398 * lh / 573), int(560 * lw / 1024), int(515 * lh / 573))).save(
        out / "latest_mem_guess.png"
    )
print("done")
