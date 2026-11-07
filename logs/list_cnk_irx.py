from pathlib import Path
import sys

sys.path.insert(0, "scripts")
from disc import Image

img = Image(Path(r"C:\PS2Recomp\games\b49f2e769315347e8bda839feb705744\disc.iso"))
irx = []
for path, layer, sector, size in img.files():
    u = path.upper()
    if "IRX" in u or "MODULE" in u or u.startswith("IG"):
        irx.append((path, size))
print("matches", len(irx))
for path, size in sorted(irx):
    print(f"{path}  size={size}")
print("--- finds ---")
for want in [
    "MODULES/IGFILEIO.IRX",
    "MODULES/IGFILEIO.IRX;1",
    "MODULES\\IGFILEIO.IRX;1",
    "IGFILEIO.IRX",
]:
    print(want, "->", img.find(want))
