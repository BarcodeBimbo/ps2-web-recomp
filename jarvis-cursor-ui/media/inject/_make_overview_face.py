"""Crop overview panel from reference-command-center-2.png; scrub AI Core copy for Workstation overlay."""
from pathlib import Path
import base64
from PIL import Image, ImageFilter

ROOT = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media")
SRC = ROOT / "reference-command-center-2.png"
OUT = ROOT / "inject" / "overview-face.png"
PREVIEW = ROOT / "inject" / "_probe" / "ov_face_scrub_x3.png"
URI_OUT = ROOT / "inject" / "_overview_face_datauri.txt"

im = Image.open(SRC).convert("RGBA")
# Panel bounds from cyan-border detection + visual QA
box = (150, 48, 338, 232)
face = im.crop(box).convert("RGBA")
print("face", box, face.size)


def scrub_bright(face_img, x0, y0, x1, y1, thresh=90):
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b, a = face_img.getpixel((x, y))
            if r + g + b > thresh:
                face_img.putpixel(
                    (x, y),
                    (
                        int(r * 0.12 + 5 * 0.88),
                        int(g * 0.12 + 18 * 0.88),
                        int(b * 0.12 + 32 * 0.88),
                        a,
                    ),
                )


# Title: AI CORE OVERVIEW
scrub_bright(face, 6, 2, 170, 18, thresh=85)
# First row label: AI Core (keep circular icon left of ~42)
scrub_bright(face, 44, 26, 120, 44, thresh=95)

blur = face.filter(ImageFilter.GaussianBlur(0.55))
for y in range(2, 18):
    for x in range(6, 170):
        face.putpixel((x, y), blur.getpixel((x, y)))
for y in range(26, 44):
    for x in range(44, 120):
        face.putpixel((x, y), blur.getpixel((x, y)))

OUT.parent.mkdir(parents=True, exist_ok=True)
face.save(OUT, optimize=True)
PREVIEW.parent.mkdir(parents=True, exist_ok=True)
face.resize((face.width * 3, face.height * 3), Image.NEAREST).save(PREVIEW)
print("wrote", OUT, OUT.stat().st_size)

b64 = base64.b64encode(OUT.read_bytes()).decode("ascii")
uri = f'url("data:image/png;base64,{b64}")'
URI_OUT.write_text(uri, encoding="utf-8")
print("uri chars", len(uri))
print("wrote", URI_OUT)
