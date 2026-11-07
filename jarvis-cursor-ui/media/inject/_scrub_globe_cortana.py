"""Scrub JARVIS lettering from hero globe PNGs and stamp CORTANA; re-embed CSS var."""
from __future__ import annotations

import base64
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media\inject")
ASSETS = ROOT / "hud-photo-assets.css"
TARGETS = [
    ROOT / "jcc-hero-globe.png",
    ROOT / "globe-hero.png",
    ROOT / "hero-globe.png",
]


def font(size: int):
    for name in (
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\Bahnschrift.ttf",
    ):
        p = Path(name)
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def scrub(path: Path) -> None:
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    arr = np.asarray(im).astype(np.float32)
    # Center band where JARVIS / AI CORE sits
    y0, y1 = int(h * 0.32), int(h * 0.62)
    x0, x1 = int(w * 0.18), int(w * 0.82)
    patch = arr[y0:y1, x0:x1]
    # Inpaint-ish: dark navy fill matching nearby pixels
    sample = arr[max(0, y0 - 8) : y0, x0:x1]
    if sample.size == 0:
        fill = np.array([2, 12, 28, 220], dtype=np.float32)
    else:
        fill = np.median(sample.reshape(-1, 4), axis=0)
    # Soft ellipse mask
    yy, xx = np.mgrid[0 : y1 - y0, 0 : x1 - x0]
    cy, cx = (y1 - y0) / 2, (x1 - x0) / 2
    ell = ((xx - cx) / (cx * 0.95)) ** 2 + ((yy - cy) / (cy * 0.85)) ** 2
    mask = np.clip((1.15 - ell) / 0.35, 0, 1)[..., None]
    patch[:] = patch * (1 - mask) + fill * mask
    out = Image.fromarray(arr.astype(np.uint8), "RGBA")
    draw = ImageDraw.Draw(out)
    f_title = font(max(18, int(w * 0.11)))
    f_sub = font(max(10, int(w * 0.045)))
    title = "CORTANA"
    # Measure
    tb = draw.textbbox((0, 0), title, font=f_title)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    tx = (w - tw) // 2
    ty = int(h * 0.38)
    # Glow underlay
    glow = Image.new("RGBA", out.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.text((tx, ty), title, font=f_title, fill=(0, 212, 255, 90))
    glow = glow.filter(ImageFilter.GaussianBlur(3))
    out = Image.alpha_composite(out, glow)
    draw = ImageDraw.Draw(out)
    draw.text((tx, ty), title, font=f_title, fill=(180, 245, 255, 240))
    sub = "AI CORE"
    sb = draw.textbbox((0, 0), sub, font=f_sub)
    sw = sb[2] - sb[0]
    draw.text(((w - sw) // 2, ty + th + int(h * 0.02)), sub, font=f_sub, fill=(100, 200, 220, 210))
    ver = "v3.0.0"
    vb = draw.textbbox((0, 0), ver, font=f_sub)
    vw = vb[2] - vb[0]
    draw.text(((w - vw) // 2, ty + th + int(h * 0.08)), ver, font=f_sub, fill=(70, 150, 175, 180))
    out.save(path, optimize=True)
    print("scrubbed", path.name, out.size)


def embed_primary():
    primary = ROOT / "jcc-hero-globe.png"
    if not primary.exists():
        primary = ROOT / "globe-hero.png"
    b64 = base64.b64encode(primary.read_bytes()).decode("ascii")
    css = ASSETS.read_text(encoding="utf-8") if ASSETS.exists() else ":root {\n}\n"
    css = re.sub(r"\n\s*--jcc-photo-hero-globe[^;]*;", "", css)
    var = f'  --jcc-photo-hero-globe: url("data:image/png;base64,{b64}");'
    if css.rstrip().endswith("}"):
        body = css.rstrip()[:-1].rstrip()
        css = body + "\n" + var + "\n}\n"
    else:
        css = ":root {\n" + var + "\n}\n"
    ASSETS.write_text(css, encoding="utf-8")
    print("embedded --jcc-photo-hero-globe", primary.name, len(b64))


def main():
    for p in TARGETS:
        if p.exists():
            scrub(p)
        else:
            print("skip missing", p.name)
    embed_primary()


if __name__ == "__main__":
    main()
