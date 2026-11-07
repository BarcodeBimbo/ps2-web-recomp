from PIL import Image
from pathlib import Path

im = Image.open(r"c:\PS2Recomp\jarvis-cursor-ui\media\reference-command-center-2.png")
out = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media\inject\_probe")
out.mkdir(exist_ok=True)

crops = {
    "hero_wide": (280, 40, 760, 360),
    "hero_tight": (360, 70, 680, 340),
    "hero_core": (400, 90, 640, 320),
    "mic_bl": (20, 380, 160, 545),
    "mic_tight": (45, 420, 130, 520),
    "talk_center": (280, 470, 760, 560),
    "talk_wave": (340, 485, 700, 545),
    "sidebar_brand": (0, 0, 200, 80),
    "voice_panel": (20, 350, 200, 560),
    "grid_overview": (200, 40, 420, 280),
}

for name, box in crops.items():
    crop = im.crop(box)
    crop.save(out / f"{name}.png")
    print(name, box, crop.size)

print("done")
