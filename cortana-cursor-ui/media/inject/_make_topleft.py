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
    """Paint out entire glyph rectangle with L/R teal fill lerp (no residual JARVIS)."""
    tx0, ty0, tx1, ty1 = TEXT
    # Slightly wider paint so AA fringes and the left accent tick disappear.
    x0, x1 = 50, 134
    y0, y1 = 9, 41
    out = c.astype(np.float32)
    for y in range(y0, y1):
        left = out[y, 44:49].mean(axis=0)
        right = out[y, 134:142].mean(axis=0)
        for x in range(x0, x1):
            t = (x - x0) / max(1, (x1 - x0 - 1))
            out[y, x] = left * (1.0 - t) + right * t
    # Soft vertical feather at top/bottom of paint strip into original
    for feather_y, alpha in ((y0 - 1, 0.45), (y0, 0.75), (y1 - 1, 0.75), (y1, 0.45)):
        if 0 <= feather_y < out.shape[0]:
            for x in range(x0, x1):
                t = (x - x0) / max(1, (x1 - x0 - 1))
                base = out[feather_y, 44:49].mean(axis=0) * (1.0 - t) + out[
                    feather_y, 134:142
                ].mean(axis=0) * t
                out[feather_y, x] = c[feather_y, x].astype(np.float32) * (
                    1.0 - alpha
                ) + base * alpha
    return out.astype(np.uint8)


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
    var_css = (
        "/* Brand chrome crop from reference-command-center-2.png — not generative */\n"
        f':root {{ --jcc-photo-topleft: url("data:image/png;base64,{b64}"); }}\n'
    )
    (OUT / "_probe" / "topleft_var.css").write_text(var_css, encoding="utf-8")
    print("wrote topleft_var.css")


if __name__ == "__main__":
    main()
