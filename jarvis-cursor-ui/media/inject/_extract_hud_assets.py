"""Extract HUD chrome cutouts from authority photo + emit data-URI CSS."""
from pathlib import Path
import base64
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media")
SRC = ROOT / "reference-command-center-2.png"
OUT = ROOT / "inject"

im = Image.open(SRC).convert("RGBA")
W, H = im.size
print("source", W, H)


def save(name: str, box, mask_circle=False, feather=0):
    crop = im.crop(box).convert("RGBA")
    if mask_circle:
        w, h = crop.size
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        inset = max(0, feather)
        draw.ellipse((inset, inset, w - 1 - inset, h - 1 - inset), fill=255)
        if feather:
            mask = mask.filter(ImageFilter.GaussianBlur(feather))
        r, g, b, _ = crop.split()
        crop = Image.merge("RGBA", (r, g, b, mask))
    path = OUT / name
    crop.save(path, optimize=True)
    print(name, box, crop.size, path.stat().st_size)
    return crop


# Hero globe only — stop above agent cards (~y275)
hero_box = (368, 52, 672, 270)
save("hero-globe.png", hero_box)

save("brand-iris.png", (12, 8, 54, 50), mask_circle=True, feather=1)
save("voice-mic-iris.png", (52, 394, 124, 466), mask_circle=True, feather=2)
save("voice-wave.png", (52, 368, 124, 392))
save("talk-wave-left.png", (328, 526, 400, 554))
save("talk-wave-right.png", (624, 526, 696, 554))
save("agent-wave-cyan.png", (292, 332, 400, 352))
save("agent-wave-purple.png", (430, 332, 538, 352))
# Memory Insights constellation — run _extract_memory_constellation.py for alpha punch;
# box kept here so full regen still emits the var (opaque crop).
save("memory-constellation.png", (398, 414, 512, 462))

assets = {
    "hero-globe.png": "--jcc-photo-hero-globe",
    "brand-iris.png": "--jcc-photo-brand-iris",
    "voice-mic-iris.png": "--jcc-photo-voice-mic",
    "voice-wave.png": "--jcc-photo-voice-wave",
    "talk-wave-left.png": "--jcc-photo-talk-wave-l",
    "talk-wave-right.png": "--jcc-photo-talk-wave-r",
    "agent-wave-cyan.png": "--jcc-photo-agent-wave-cyan",
    "agent-wave-purple.png": "--jcc-photo-agent-wave-purple",
    "memory-constellation.png": "--jcc-photo-memory-constellation",
}

lines = [
    "/* Photo cutouts from reference-command-center-2.png — NOT generative art. */",
    "/* Data URIs so workbench inject resolves without extra staging. */",
    ":root {",
]
for name, var in assets.items():
    b64 = base64.b64encode((OUT / name).read_bytes()).decode("ascii")
    lines.append(f'  {var}: url("data:image/png;base64,{b64}");')
    print("embedded", name, len(b64), "chars")
lines.append("}")
css_path = OUT / "hud-photo-assets.css"
css_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("wrote", css_path, css_path.stat().st_size)

hx, hy, hx2, hy2 = hero_box
hw, hh = hx2 - hx, hy2 - hy
print("hero", hw, hh)
print(f"splash background-size: {(W / hw) * 100:.4f}% {(H / hh) * 100:.4f}%;")
print(f"splash background-position: {(-hx / hw) * 100:.4f}% {(-hy / hh) * 100:.4f}%;")
