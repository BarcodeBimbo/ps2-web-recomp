"""Minimal PPM(P6)->PNG writer without Pillow."""
from pathlib import Path
import struct
import zlib


def png_chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def ppm_to_png(src: Path, dest: Path) -> None:
    raw = src.read_bytes()
    parts = []
    while len(parts) < 3:
        line, raw = raw.split(b"\n", 1)
        if not line.startswith(b"#"):
            parts.append(line)
    if parts[0] != b"P6":
        raise ValueError(f"unsupported {src}")
    w, h = map(int, parts[1].split())
    pixels = raw[: w * h * 3]
    rows = b"".join(b"\x00" + pixels[y * w * 3 : (y + 1) * w * 3] for y in range(h))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", zlib.compress(rows, 9)) + png_chunk(b"IEND", b"")
    dest.write_bytes(png)
    print("wrote", dest, w, h, "bytes", len(png))


out = Path("logs/shot_preview")
out.mkdir(exist_ok=True)
for gid, label, frame in [
    ("b49f2e769315347e8bda839feb705744", "cnk", "frame_00300.ppm"),
    ("b49f2e769315347e8bda839feb705744", "cnk_end", "frame_03600.ppm"),
    ("60c82f4a111da300ac23bbec85272788", "mw", "frame_03600.ppm"),
    ("c0671389c296be6afe9e5224c97d30df", "u2", "frame_03600.ppm"),
]:
    src = Path("games") / gid / "shots" / frame
    if src.exists():
        ppm_to_png(src, out / f"{label}.png")
