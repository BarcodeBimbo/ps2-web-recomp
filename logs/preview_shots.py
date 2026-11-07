from pathlib import Path
import subprocess
import sys

try:
    from PIL import Image
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow", "-q"])
    from PIL import Image


def load_ppm(path: Path) -> Image.Image:
    data = path.read_bytes()
    parts = []
    while len(parts) < 3:
        line, data = data.split(b"\n", 1)
        if not line.startswith(b"#"):
            parts.append(line)
    w, h = map(int, parts[1].split())
    return Image.frombytes("RGB", (w, h), data[: w * h * 3])


out = Path("logs/shot_preview")
out.mkdir(exist_ok=True)
for gid, label, frame in [
    ("b49f2e769315347e8bda839feb705744", "cnk", "frame_00300.ppm"),
    ("b49f2e769315347e8bda839feb705744", "cnk_end", "frame_03600.ppm"),
    ("60c82f4a111da300ac23bbec85272788", "mw", "frame_03600.ppm"),
    ("c0671389c296be6afe9e5224c97d30df", "u2", "frame_03600.ppm"),
]:
    path = Path("games") / gid / "shots" / frame
    if path.exists():
        image = load_ppm(path)
        dest = out / f"{label}.png"
        image.save(dest)
        print("wrote", dest, image.size)
