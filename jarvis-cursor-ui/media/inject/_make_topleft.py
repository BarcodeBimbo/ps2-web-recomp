"""Crop brand chrome from reference-command-center-2.png; blank JARVIS glyphs."""
from __future__ import annotations

import base64
from pathlib import Path

import numpy as np
from PIL import Image

SRC = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media\reference-command-center-2.png")
OUT = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media\inject")
BOX = (0, 0, 162, 48)  # exclusive — iris + trap chrome, stop before SYSTEM STATUS
TEXT = (52, 10, 130, 40)  # JARVIS / COMMAND CENTER glyph zone


def blank_text(c: np.ndarray) -> np.ndarray:
    tx0, ty0, tx1, ty1 = TEXT
    for y in range(ty0, ty1):
        left = c[y, 48:52].astype(np.float32).mean(axis=0)
        right = c[y, 128:135].astype(np.float32).mean(axis=0)
        for x in range(tx0, tx1):
            t = (x - tx0) / max(1, (tx1 - tx0 - 1))
            base = left * (1.0 - t) + right * t
            pix = c[y, x].astype(np.float32)
            lum = float(pix[0] + pix[1] + pix[2])
            if pix[1] > 120 or lum > 320 or (pix[2] > 140 and pix[0] > 40):
                c[y, x] = base.astype(np.uint8)
            elif pix[1] > 100:
                a = min(1.0, (float(pix[1]) - 100.0) / 40.0)
                c[y, x] = (pix * (1.0 - a) + base * a).astype(np.uint8)

    # Second pass: neighborhood heal residual AA fringes
    r = c[:, :, 0].astype(int)
    g = c[:, :, 1].astype(int)
    b = c[:, :, 2].astype(int)
    bright = (g > 125) & (b > 140) & ((r + g + b) > 300)
    mask = np.zeros(c.shape[:2], dtype=bool)
    mask[ty0:ty1, tx0:tx1] = bright[ty0:ty1, tx0:tx1]
    ys, xs = np.where(mask)
    for y, x in zip(ys.tolist(), xs.tolist()):
        y0, y1 = max(0, y - 3), min(c.shape[0], y + 4)
        x0, x1 = max(0, x - 4), min(c.shape[1], x + 5)
        patch = c[y0:y1, x0:x1]
        pr = patch[:, :, 0].astype(int)
        pg = patch[:, :, 1].astype(int)
        pb = patch[:, :, 2].astype(int)
        keep = ~((pg > 125) & (pb > 140) & ((pr + pg + pb) > 300))
        if keep.any():
            c[y, x] = patch[keep].mean(axis=0).astype(np.uint8)
    return c


def main() -> None:
    ref = Image.open(SRC).convert("RGBA")
    crop = ref.crop(BOX).convert("RGBA")
    c = blank_text(np.array(crop))
    out = Image.fromarray(c, "RGBA")
    path = OUT / "cortana-topleft.png"
    out.save(path, optimize=True)
    out.save(OUT / "_probe" / "cortana_topleft_blanked.png")
    print("saved", path, out.size, path.stat().st_size)

    tx0, ty0, tx1, ty1 = TEXT
    g2 = c[:, :, 1].astype(int)
    bright2 = (g2 > 140) & (c[:, :, 2].astype(int) > 150)
    print("bright leftovers", int(bright2[ty0:ty1, tx0:tx1].sum()))

    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    print("b64_chars", len(b64))
    (OUT / "_probe" / "topleft_b64.txt").write_text(b64, encoding="utf-8")


if __name__ == "__main__":
    main()
