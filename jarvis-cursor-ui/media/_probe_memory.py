from PIL import Image
from pathlib import Path

im = Image.open(r"c:\PS2Recomp\jarvis-cursor-ui\media\reference-command-center-2.png").convert("RGBA")
out = Path(r"c:\PS2Recomp\jarvis-cursor-ui\media\_probe")
out.mkdir(exist_ok=True)

candidates = {
    "bottom_row": (160, 400, 860, 515),
    "mem_wide": (320, 400, 560, 515),
    "mem_a": (300, 405, 540, 510),
    "mem_b": (340, 410, 580, 505),
    "mem_c": (360, 412, 560, 500),
    "sys_mon": (160, 405, 340, 510),
    "llm": (560, 405, 860, 510),
}
for name, box in candidates.items():
    im.crop(box).save(out / f"{name}.png")
    print(name, box, (box[2] - box[0], box[3] - box[1]))
print("done")
