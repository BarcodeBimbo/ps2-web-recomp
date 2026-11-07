"""Crop Memory Insights constellation from reference-command-center-2.png (not generative)."""
from pathlib import Path
import base64
import re
import numpy as np
from PIL import Image

ROOT = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media")
SRC = ROOT / "reference-command-center-2.png"
OUT = ROOT / "inject"
CSS = OUT / "hud-photo-assets.css"

# Art-only crop (nodes + lines). Excludes title, stats column, and "View Memory Map" link.
# Calibrated against bottom-row grid on 1024x573 authority photo.
BOX = (398, 414, 512, 462)  # 114x48

im = Image.open(SRC).convert("RGBA")
crop = im.crop(BOX)
arr = np.array(crop).astype(np.float32)
rgb = arr[:, :, :3]
lum = rgb.mean(axis=2)
# Keep cyan/white glow; punch panel navy so crop composites cleanly on glass panel.
# Soft alpha from luminance so bloom softens at edges.
alpha = np.clip((lum - 18.0) / 55.0, 0.0, 1.0) * 255.0
# Prefer source cyan channel for brighter nodes
cyanish = np.clip((rgb[:, :, 1] * 0.35 + rgb[:, :, 2] * 0.65 - rgb[:, :, 0] * 0.15), 0, 255)
alpha = np.maximum(alpha, np.clip((cyanish - 40.0) / 90.0, 0.0, 1.0) * 255.0)
arr[:, :, 3] = alpha.astype(np.uint8)
out_img = Image.fromarray(arr.astype(np.uint8), "RGBA")
path = OUT / "memory-constellation.png"
out_img.save(path, optimize=True)
print("wrote", path, BOX, out_img.size, path.stat().st_size)

raw = path.read_bytes()
b64 = base64.b64encode(raw).decode("ascii")
var_line = f'  --jcc-photo-memory-constellation: url("data:image/png;base64,{b64}");'

css = CSS.read_text(encoding="utf-8")
pat = re.compile(r"\n  --jcc-photo-memory-constellation: url\(\"data:image/png;base64,[^\"]+\"\);")
if pat.search(css):
    css = pat.sub("\n" + var_line, css)
else:
    # Insert before closing :root brace
    css = css.replace("\n}\n", "\n" + var_line + "\n}\n", 1)
    if var_line not in css:
        css = css.rstrip() + "\n:root {\n" + var_line + "\n}\n"
CSS.write_text(css, encoding="utf-8")
print("updated", CSS, "b64 chars", len(b64))
