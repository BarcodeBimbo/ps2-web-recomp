from pathlib import Path
import sys

sys.path.insert(0, "scripts")
from disc import Image

img = Image(Path(r"C:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc.iso"))
hits = []
for path, _, _, size in img.files():
    u = path.upper()
    if any(
        x in u
        for x in (
            ".PSS",
            ".IPU",
            ".MPG",
            ".MAD",
            ".STR",
            "MOVIE",
            "VIDEO",
            "INTRO",
            "LOGO",
            "IGFILE",
            "IGU",
            "GFC",
            "GOB",
            "TGA",
            "VVAA",
            "ASSET",
        )
    ):
        hits.append((path, size))
print("hits", len(hits))
for path, size in sorted(hits):
    print(f"{path} {size}")
