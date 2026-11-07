"""Manual row/icon measurement on overview face crop."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media")
face = Image.open(ROOT / "inject" / "overview-face.png").convert("RGB")
# Also raw unscrubbed crop for measurement
raw = Image.open(ROOT / "reference-command-center-2.png").convert("RGB").crop((178, 52, 348, 268))
arr = np.asarray(raw)
h, w = arr.shape[:2]
print("face", w, h)

# Horizontal luminance profile — find row bands
lum = arr.mean(axis=2)
row_mean = lum.mean(axis=1)
# Find local maxima in left strip (icons are bright)
left = arr[:, 8:45]
left_score = ((left[:, :, 2].astype(int) + left[:, :, 1].astype(int)) - left[:, :, 0].astype(int)).mean(axis=1)
print("left_score peaks:")
for y in range(1, h - 1):
    if left_score[y] > left_score[y - 1] and left_score[y] >= left_score[y + 1] and left_score[y] > 25:
        print(f"  y={y} score={left_score[y]:.1f}")

# Save annotated raw with grid
ann = raw.copy()
d = ImageDraw.Draw(ann)
for y in range(0, h, 10):
    d.line((0, y, w - 1, y), fill=(80, 80, 80))
    d.text((2, y), str(y), fill=(255, 80, 80))
for x in range(0, w, 10):
    d.line((x, 0, x, h - 1), fill=(40, 40, 60))
ann = ann.resize((w * 3, h * 3), Image.NEAREST)
ann.save(ROOT / "inject" / "_probe" / "ov_face_grid.png")
print("saved grid")

# Save title/row1 zoom
raw.crop((0, 0, w, 50)).resize((w * 4, 200), Image.NEAREST).save(
    ROOT / "inject" / "_probe" / "ov_title_zoom.png"
)
raw.crop((0, 20, 60, 55)).resize((240, 140), Image.NEAREST).save(
    ROOT / "inject" / "_probe" / "ov_ico0_zoom.png"
)
