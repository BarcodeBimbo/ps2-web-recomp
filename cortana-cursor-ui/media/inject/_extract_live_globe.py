"""
Extract FULL AI Core globe REGION from reference-command-center-2.png.

Keeps every surrounding element in the hero region:
  - geodesic mesh + landmass silhouettes
  - ALL orbital rings + ring nodes
  - equator scanline
  - pedestal / concentric floor
  - background particle/dot field + faint outer arcs
Only baked JARVIS / AI CORE / v3.0.0 lettering is inpainted out.
Live HTML/CSS supply Cortana label + traveling node accents — never generative globe art.
"""
from __future__ import annotations

import base64
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media")
SRC = ROOT / "reference-command-center-2.png"
OUT = ROOT / "inject"
DEST = OUT / "jcc-hero-globe.png"
ASSETS = OUT / "hud-photo-assets.css"

# Wide enough for outer orbits + particle field; stop above Active Agents
L, T, R, B = 385, 45, 665, 268


def _telea_fill(rgb: np.ndarray, mask: np.ndarray, passes: int = 28) -> np.ndarray:
    out = rgb.astype(np.float32).copy()
    m = mask.astype(bool).copy()
    h, w = m.shape
    kernel = [
        (-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1),
        (-2, 0), (2, 0), (0, -2), (0, 2),
        (-2, -1), (-2, 1), (2, -1), (2, 1),
        (-1, -2), (1, -2), (-1, 2), (1, 2),
    ]
    for _ in range(passes):
        if not m.any():
            break
        known = ~m
        frontier = np.zeros_like(m)
        for dy, dx in kernel[:4]:
            shifted = np.roll(np.roll(known, dy, 0), dx, 1)
            if dy < 0:
                shifted[dy:, :] = False
            elif dy > 0:
                shifted[:dy, :] = False
            if dx < 0:
                shifted[:, dx:] = False
            elif dx > 0:
                shifted[:, :dx] = False
            frontier |= m & shifted
        if not frontier.any():
            break
        fy, fx = np.where(frontier)
        for y, x in zip(fy.tolist(), fx.tolist()):
            acc = np.zeros(3, dtype=np.float32)
            wsum = 0.0
            for dy, dx in kernel:
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and not m[ny, nx]:
                    wt = 1.0 / (abs(dy) + abs(dx) + 0.25)
                    acc += out[ny, nx] * wt
                    wsum += wt
            if wsum > 0:
                out[y, x] = acc / wsum
                m[y, x] = False
    if m.any():
        fill = np.median(out[~mask], axis=0) if (~mask).any() else np.array([4.0, 16.0, 34.0])
        out[m] = fill
    return out


def main() -> None:
    im = Image.open(SRC).convert("RGBA")
    crop = im.crop((L, T, R, B))
    arr = np.array(crop).astype(np.float32)
    h, w = arr.shape[:2]
    rch, gch, bch = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    cyan = ((bch - rch) + (gch - rch) * 0.35).clip(0, 255)
    bright = 0.22 * rch + 0.38 * gch + 0.55 * bch
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w * 0.50, h * 0.45
    rx, ry = w * 0.52, h * 0.54
    ell = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    window = np.clip((1.18 - ell) / 0.32, 0, 1)

    # --- lettering ONLY (protect rings / nodes / scanline / pedestal) ---
    band = (yy > h * 0.30) & (yy < h * 0.72) & (xx > w * 0.18) & (xx < w * 0.82)
    text_core = band & (bright > 88) & ((bch + gch) > (rch * 1.45 + 12))
    text_img = (
        Image.fromarray((text_core.astype(np.uint8) * 255), "L")
        .filter(ImageFilter.MaxFilter(11))
        .filter(ImageFilter.GaussianBlur(1.4))
    )
    text_soft = np.asarray(text_img).astype(np.float32) / 255.0
    text_soft *= np.clip((0.52 - ell) / 0.24, 0, 1)
    scan = (np.abs(yy - h * 0.48) < 2.0) & (xx > w * 0.16) & (xx < w * 0.84) & (cyan > 20)
    text_soft = np.where(scan, 0.0, text_soft)
    # lower v3.0.0 band
    ver = (yy > h * 0.55) & (yy < h * 0.68) & (xx > w * 0.35) & (xx < w * 0.65) & (bright > 70)
    text_soft = np.maximum(text_soft, ver.astype(np.float32) * np.clip((0.45 - ell) / 0.2, 0, 1))
    # right-side residual of final JARVIS glyph (often reads as S/6)
    right_glyph = (
        (yy > h * 0.36)
        & (yy < h * 0.58)
        & (xx > w * 0.58)
        & (xx < w * 0.78)
        & (bright > 85)
        & (ell < 0.55)
    )
    text_soft = np.maximum(text_soft, right_glyph.astype(np.float32) * 0.95)
    mask = text_soft > 0.25

    rgb = arr[:, :, :3].copy()
    if mask.any():
        filled = _telea_fill(rgb, mask, passes=28)
        for c in range(3):
            arr[:, :, c] = filled[:, :, c] * text_soft + arr[:, :, c] * (1.0 - text_soft)
        bright2 = 0.22 * arr[:, :, 0] + 0.38 * arr[:, :, 1] + 0.55 * arr[:, :, 2]
        residual = (
            band
            & (bright2 > 100)
            & ((arr[:, :, 2] + arr[:, :, 1]) > (arr[:, :, 0] * 1.45 + 20))
            & (ell < 0.48)
            & ~scan
        )
        if residual.any():
            arr[:, :, :3] = _telea_fill(arr[:, :, :3], residual, passes=16)

    # --- alpha: preserve glow on mesh, rings, particles, pedestal ---
    glow = np.clip(cyan * 2.6 + bright * 0.4, 0, 255)
    core = np.clip(95 + bright * 0.55, 0, 220)
    alpha = np.maximum(core * 0.5, glow * 0.6) * window
    stroke = np.clip(cyan * 5.5 + (bright > 35) * 30, 0, 255) * np.clip((1.28 - ell) / 0.28, 0, 1)
    alpha = np.maximum(alpha, stroke)
    px, py = w * 0.50, h * 0.90
    pell = ((xx - px) / (w * 0.40)) ** 2 + ((yy - py) / (h * 0.14)) ** 2
    alpha = np.maximum(
        alpha, np.clip(cyan * 6.5 + (bright > 28) * 50, 0, 255) * np.clip((1.08 - pell) / 0.32, 0, 1)
    )
    # Kill Active Agents / timeline panel chrome under the pedestal
    alpha[yy > h * 0.955] = 0
    # thin horizontal panel rules near bottom
    hrule = (yy > h * 0.90) & (bright > 40) & (cyan > 15) & (np.abs(np.gradient(bright, axis=0)) < 2)
    alpha[hrule] = 0
    purpleish = (rch > 38) & (bch > gch) & (rch > gch * 0.65) & (yy > h * 0.78)
    alpha[purpleish] *= 0.02
    dull = (bright < 12) & (cyan < 8) & (ell > 0.95)
    alpha[dull] = 0
    # soft-fade bottom so no hard panel edge leaks into hero
    bottom_fade = np.clip((h * 0.94 - yy) / (h * 0.06), 0, 1)
    alpha *= np.where(yy > h * 0.88, bottom_fade, 1.0)

    arr[:, :, 3] = alpha.clip(0, 255)
    out = Image.fromarray(arr.astype(np.uint8), "RGBA")
    rgb_i = out.convert("RGB")
    a = out.split()[-1].filter(ImageFilter.GaussianBlur(0.35))
    out = Image.merge("RGBA", (*rgb_i.split(), a))
    bbox = out.getbbox()
    if bbox:
        l, t, r, b = bbox
        out = out.crop((max(0, l - 3), max(0, t - 3), min(w, r + 3), min(h, b + 3)))

    out.save(DEST, optimize=True)
    for name in ("globe-hero.png", "hero-globe.png"):
        out.save(OUT / name, optimize=True)
    prev = Image.new("RGBA", out.size, (2, 10, 24, 255))
    Image.alpha_composite(prev, out).convert("RGB").save(OUT / "_globe_hero_preview.png")

    oa = np.asarray(out.convert("RGB"))
    oh, ow = oa.shape[:2]
    cyb = oa[int(oh * 0.36) : int(oh * 0.62), int(ow * 0.25) : int(ow * 0.75)]
    right = oa[int(oh * 0.38) : int(oh * 0.55), int(ow * 0.62) : int(ow * 0.78)]
    print(
        "saved",
        out.size,
        "center_max",
        int(cyb.max()) if cyb.size else -1,
        "center_mean",
        round(float(cyb.mean()), 2) if cyb.size else -1,
        "right_max",
        int(right.max()) if right.size else -1,
        "mask_px",
        int(mask.sum()),
    )

    b64 = base64.b64encode(DEST.read_bytes()).decode("ascii")
    css = ASSETS.read_text(encoding="utf-8") if ASSETS.exists() else ":root {\n}\n"
    css = re.sub(r"\n\s*--jcc-photo-hero-globe[^;]*;", "", css)
    var = f'  --jcc-photo-hero-globe: url("data:image/png;base64,{b64}");'
    if css.rstrip().endswith("}"):
        body = css.rstrip()[:-1].rstrip()
        css = body + "\n" + var + "\n}\n"
    else:
        css = ":root {\n" + var + "\n}\n"
    ASSETS.write_text(css, encoding="utf-8")
    print("embedded", len(b64))


if __name__ == "__main__":
    main()
