"""Crop Workstation Overview face from reference-command-center-2.png.

OPAQUE-scrubs ALL baked copy (including invented reference metrics) so HTML
overlays supply Workstation naming + honest values (real data or em dash).
Keeps glass chrome, corner brackets, pill rows, and circular icons.

Emits overview-face.png and embeds --jcc-photo-overview into hud-photo-assets.css.
"""
from __future__ import annotations

import base64
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media")
SRC = ROOT / "reference-command-center-2.png"
OUT = ROOT / "inject"

FACE_BOX = (178, 52, 348, 268)  # L,T,R,B → 170×216
FX, FY, FR, FB = FACE_BOX
FW, FH = FR - FX, FB - FY

im = Image.open(SRC).convert("RGBA")
face = im.crop(FACE_BOX).convert("RGBA")
arr = np.asarray(face.convert("RGB"))


def median_rgb(box: tuple[int, int, int, int]) -> tuple[int, int, int]:
    x0, y0, x1, y1 = box
    patch = arr[max(0, y0) : min(FH, y1), max(0, x0) : min(FW, x1)]
    if patch.size == 0:
        return (8, 18, 28)
    med = np.median(patch.reshape(-1, 3), axis=0).astype(int)
    return (int(med[0]), int(med[1]), int(med[2]))


draw = ImageDraw.Draw(face)

# Title strip — sample dark glass near title, paint opaque
title_bg = median_rgb((24, 8, 40, 16))
draw.rectangle((10, 1, 160, 20), fill=title_bg + (255,))

# Per-row text wells (icons live ~x 12–38)
row_bands = [
    (22, 48),
    (50, 74),
    (76, 100),
    (104, 128),
    (132, 156),
    (160, 184),
]
for y0, y1 in row_bands:
    # Sample pill fill just right of icon
    bg = median_rgb((48, y0 + 8, 58, y1 - 8))
    draw.rectangle((40, y0 + 3, 164, y1 - 3), fill=bg + (255,))

face_path = OUT / "overview-face.png"
face.save(face_path, optimize=True)
print("face", FACE_BOX, face.size, face_path.stat().st_size)

# Verify text column brightness dropped vs raw
raw = np.asarray(im.crop(FACE_BOX).convert("RGB"))
scrub = np.asarray(face.convert("RGB"))
# bright pixels in text col (likely glyphs)
bright_raw = ((raw[22:184, 42:162].max(axis=2) > 90).sum())
bright_scrub = ((scrub[22:184, 42:162].max(axis=2) > 90).sum())
print(f"bright text-col pixels raw={bright_raw} scrub={bright_scrub}")

preview = face.copy()
d = ImageDraw.Draw(preview)
d.rectangle((12, 4, 158, 18), outline=(0, 229, 255, 200))
for y0, y1 in row_bands:
    d.rectangle((42, y0 + 4, 130, y0 + 15), outline=(255, 255, 255, 160))
    d.rectangle((42, y0 + 15, 150, y1 - 4), outline=(0, 200, 255, 160))
(OUT / "_probe").mkdir(exist_ok=True)
preview.resize((FW * 3, FH * 3), Image.NEAREST).save(OUT / "_probe" / "ov_face_scrubbed.png")

assets_css = OUT / "hud-photo-assets.css"
existing = assets_css.read_text(encoding="utf-8") if assets_css.exists() else ":root {\n}\n"
existing = re.sub(r"\n\s*--jcc-photo-overview[^;]*;", "", existing)
existing = re.sub(r"\n\s*--jcc-photo-ov-ico-\d[^;]*;", "", existing)

b64 = base64.b64encode(face_path.read_bytes()).decode("ascii")
new_var = f'  --jcc-photo-overview: url("data:image/png;base64,{b64}");'

existing = existing.rstrip()
if existing.endswith("}"):
    body = existing[:-1].rstrip()
    if not body.endswith("\n"):
        body += "\n"
    existing = body + new_var + "\n}\n"
else:
    existing = (
        "/* Photo cutouts from reference-command-center-2.png — NOT generative art. */\n"
        ":root {\n" + new_var + "\n}\n"
    )

assets_css.write_text(existing, encoding="utf-8")
print("wrote", assets_css.name, assets_css.stat().st_size)
