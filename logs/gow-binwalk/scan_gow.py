import json, collections, mmap, re, struct
from pathlib import Path

SECTOR = 2048
ISO = Path(r"C:\PS2Recomp\games\695b874b308a4e5353767bb6df8ba697\disc.iso")
ELF = Path(r"C:\PS2Recomp\games\695b874b308a4e5353767bb6df8ba697\disc\boot.elf")
OUT = Path(r"C:\PS2Recomp\logs\gow-binwalk")
OUT.mkdir(parents=True, exist_ok=True)

def le32(b, o=0): return struct.unpack_from("<I", b, o)[0]

SIGS = {
    "ASSETS.GFC": b"ASSETS.GFC",
    "ASSETS.GOB": b"ASSETS.GOB",
    "STBLz": b"STBLz",
    "STBL0": b"STBL0",
    "DA_FA": b"\xDA\xFA",
    "IntrinsicAlchemy": b"Intrinsic Alchemy",
    "igFileIO": b"igFileIO",
    "igActor": b"igActor",
    "PART1.PAK": b"PART1.PAK",
    "GODOFWAR.TOC": b"GODOFWAR.TOC",
}

results = {"game": "God of War USA", "id": "695b874b308a4e5353767bb6df8ba697",
           "tools": ["python mmap signature scan (binwalk CLI not installed)"],
           "iso_size": ISO.stat().st_size, "toc": [], "sig_counts": {}, "elf": {}, "notes": []}

# ISO9660 shallow TOC via PVD
with ISO.open("rb") as f:
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    pvd = mm[16*SECTOR:17*SECTOR]
    assert pvd[0:6] == b"\x01CD001"
    root_lba = le32(pvd, 156+2); root_size = le32(pvd, 156+10)
    data = mm[root_lba*SECTOR:root_lba*SECTOR+root_size]
    off = 0
    while off < len(data):
        length = data[off]
        if length == 0:
            off = (off + 2048) & ~2047
            if off >= len(data): break
            continue
        loc = le32(data, off+2); sz = le32(data, off+10); flags = data[off+25]
        nlen = data[off+32]; name = data[off+33:off+33+nlen]
        if name not in (b"\x00", b"\x01"):
            n = name.split(b";")[0].decode("ascii","replace")
            results["toc"].append({"name": n, "lba": loc, "size": sz, "flags": flags})
        off += length

    # Sampled signature scan: first 64 MiB + last 16 MiB + every 256 MiB stride 4 MiB window
    windows = []
    size = len(mm)
    windows.append((0, min(size, 64*1024*1024)))
    if size > 16*1024*1024:
        windows.append((size - 16*1024*1024, size))
    stride = 256*1024*1024
    win = 4*1024*1024
    pos = 64*1024*1024
    while pos < size - 16*1024*1024:
        windows.append((pos, min(pos+win, size)))
        pos += stride

    counts = {k: 0 for k in SIGS}
    hits = {k: [] for k in SIGS}
    scanned = 0
    for a,b in windows:
        chunk = mm[a:b]
        scanned += len(chunk)
        for name, needle in SIGS.items():
            start = 0
            while True:
                i = chunk.find(needle, start)
                if i < 0: break
                counts[name] += 1
                if len(hits[name]) < 8:
                    hits[name].append(a+i)
                start = i + len(needle)
                if counts[name] > 100000: break
    results["sig_counts"] = counts
    results["sig_sample_offsets"] = hits
    results["bytes_scanned"] = scanned
    mm.close()

# ELF string scan
elf_bytes = ELF.read_bytes() if ELF.is_file() else b""
results["elf"]["path"] = str(ELF) if ELF.is_file() else None
results["elf"]["size"] = len(elf_bytes)
if elf_bytes:
    ig = sorted(set(m.group(0).decode("ascii") for m in re.finditer(rb"ig[A-Z][A-Za-z0-9_]{2,48}", elf_bytes)))
    results["elf"]["ig_class_count"] = len(ig)
    results["elf"]["ig_sample"] = ig[:20]
    results["elf"]["intrinsic_alchemy"] = b"Intrinsic Alchemy" in elf_bytes
    results["elf"]["igFileIO"] = b"igFileIO" in elf_bytes
    results["elf"]["STBLz"] = elf_bytes.count(b"STBLz")
    results["elf"]["DA_FA"] = elf_bytes.count(b"\xDA\xFA")

alchemy_like = any(results["sig_counts"][k] > 0 for k in ("ASSETS.GFC","ASSETS.GOB","STBLz","STBL0","IntrinsicAlchemy"))
results["alchemy_present"] = alchemy_like
results["notes"].append("GoW uses PART1.PAK + GODOFWAR.TOC packaging, not Alchemy GFC/GOB/IGB")
results["notes"].append("No ASSETS.GFC/GOB on ISO9660 root; IRX modules at root not MODULES/")

(OUT/"gow-binwalk-summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print(json.dumps({k: results[k] for k in ("alchemy_present","sig_counts","bytes_scanned","elf","toc")}, indent=2))
print("wrote", OUT/"gow-binwalk-summary.json")
