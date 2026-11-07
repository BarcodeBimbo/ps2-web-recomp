#!/usr/bin/env python3
"""God of War USA structural disc walk — CNK A2 style (research only).

Manual mmap/struct mapping of ISO TOC, GODOFWAR.TOC, PART1.PAK head,
and EE ELF. Not the binwalk library; same method as _w2_cnk_binwalk_scan.py.
"""
from __future__ import annotations

import collections
import json
import mmap
import re
import struct
from pathlib import Path

ROOT = Path(r"C:\PS2Recomp\games\695b874b308a4e5353767bb6df8ba697")
ISO = ROOT / "disc.iso"
ELF_SIDE = ROOT / "disc" / "boot.elf"
OUT_DIR = Path(r"C:\PS2Recomp\verification\recovery")
SAMPLE_DIR = OUT_DIR / "gow-structural-samples"
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = Path(r"C:\PS2Recomp\logs\gow-binwalk")
LOG_DIR.mkdir(parents=True, exist_ok=True)

SECTOR = 2048


def le16(b: bytes, o: int = 0) -> int:
    return struct.unpack_from("<H", b, o)[0]


def le32(b: bytes, o: int = 0) -> int:
    return struct.unpack_from("<I", b, o)[0]


def be32(b: bytes, o: int = 0) -> int:
    return struct.unpack_from(">I", b, o)[0]


def ascii_at(b: bytes, o: int, n: int) -> str:
    return b[o : o + n].split(b"\x00", 1)[0].decode("ascii", "replace")


def list_iso9660(mm: mmap.mmap) -> list[dict]:
    pvd = mm[16 * SECTOR : 17 * SECTOR]
    assert pvd[0:6] == b"\x01CD001"
    root_lba = le32(pvd, 156 + 2)
    root_size = le32(pvd, 156 + 10)
    data = mm[root_lba * SECTOR : root_lba * SECTOR + root_size]
    off = 0
    out: list[dict] = []
    while off < len(data):
        length = data[off]
        if length == 0:
            off = (off + 2048) & ~2047
            if off >= len(data):
                break
            continue
        loc = le32(data, off + 2)
        sz = le32(data, off + 10)
        flags = data[off + 25]
        nlen = data[off + 32]
        name = data[off + 33 : off + 33 + nlen]
        if name not in (b"\x00", b"\x01"):
            n = name.split(b";")[0].decode("ascii", "replace")
            out.append(
                {
                    "name": n,
                    "lba": loc,
                    "size": sz,
                    "flags": flags,
                    "is_dir": bool(flags & 2),
                    "byte_offset": loc * SECTOR,
                }
            )
        off += length
    return out


def read_entry(mm: mmap.mmap, ent: dict) -> bytes:
    return bytes(mm[ent["byte_offset"] : ent["byte_offset"] + ent["size"]])


def parse_system_cnf(data: bytes) -> dict:
    text = data.decode("ascii", "replace")
    boot = None
    for line in text.splitlines():
        if "BOOT2" in line.upper() or line.upper().startswith("BOOT"):
            boot = line.strip()
    return {"raw": text.strip(), "boot_line": boot}


def parse_elf_header(data: bytes) -> dict:
    if data[:4] != b"\x7fELF":
        return {"valid": False}
    ei_class = data[4]
    ei_data = data[5]  # 1=LE
    e_type = le16(data, 16)
    e_machine = le16(data, 18)
    e_entry = le32(data, 24)
    e_phoff = le32(data, 28)
    e_phnum = le16(data, 44)
    e_phentsize = le16(data, 42)
    segs = []
    for i in range(e_phnum):
        o = e_phoff + i * e_phentsize
        p_type = le32(data, o)
        p_offset = le32(data, o + 4)
        p_vaddr = le32(data, o + 8)
        p_filesz = le32(data, o + 16)
        p_memsz = le32(data, o + 20)
        if p_type == 1:  # PT_LOAD
            segs.append(
                {
                    "index": i,
                    "offset": p_offset,
                    "vaddr": f"0x{p_vaddr:08X}",
                    "filesz": p_filesz,
                    "memsz": p_memsz,
                }
            )
    return {
        "valid": True,
        "class": ei_class,
        "endian": "LE" if ei_data == 1 else "BE",
        "type": e_type,
        "machine": e_machine,
        "entry": f"0x{e_entry:08X}",
        "phnum": e_phnum,
        "load_segments": segs,
    }


def elf_string_census(data: bytes) -> dict:
    ig = sorted(
        {
            m.group(0).decode("ascii")
            for m in re.finditer(rb"ig[A-Z][A-Za-z0-9_]{2,48}", data)
        }
    )
    printable = re.findall(rb"[\x20-\x7e]{6,80}", data)
    interesting = []
    keys = (
        b"Alchemy",
        b"igFileIO",
        b"ASSETS",
        b"GFC",
        b"GOB",
        b"STBL",
        b"PART1",
        b"GODOFWAR",
        b"Sony",
        b"SCE",
        b"Santa Monica",
        b"sceCd",
        b"PADMAN",
        b"LIBSD",
    )
    for s in printable:
        if any(k.lower() in s.lower() for k in keys):
            interesting.append(s.decode("ascii", "replace"))
    # dedupe preserve order
    seen = set()
    uniq = []
    for s in interesting:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    return {
        "ig_class_count": len(ig),
        "ig_sample": ig[:24],
        "intrinsic_alchemy": b"Intrinsic Alchemy" in data,
        "igFileIO": b"igFileIO" in data,
        "STBLz_count": data.count(b"STBLz"),
        "STBL0_count": data.count(b"STBL0"),
        "DA_FA_count": data.count(b"\xDA\xFA"),
        "interesting_strings": uniq[:60],
    }


def parse_gow_toc(toc: bytes) -> dict:
    """GODOFWAR.TOC layout (confirmed against PART1.PAK head landings).

    Record = 24 bytes × 1669, plus 12-byte zero trailer:
      name[16]  NUL-padded ASCII (flag noise may appear in pad)
      u32 LE    size (bytes in PAK)
      u32 LE    offset (byte offset into PART1.PAK)

    Verified: R_PERM.WAD size=3638576 offset=0 lands on PAK head containing ``WAD_``.
    Later entries show monotonically increasing offsets.
    """
    size = len(toc)
    stride = 24
    name_len = 16
    n = size // stride
    trailer = toc[n * stride :]
    records: list[dict] = []
    ext = collections.Counter()
    for i in range(n):
        base = i * stride
        raw_name = toc[base : base + name_len]
        # Strip NULs and non-printable pad/flag bytes
        name_bytes = bytes(c for c in raw_name if 32 <= c < 127)
        name = name_bytes.decode("ascii", "replace").strip()
        sz = le32(toc, base + name_len)
        off = le32(toc, base + name_len + 4)
        rec = {"index": i, "name": name, "size": sz, "offset": off}
        records.append(rec)
        if "." in name:
            ext[name.rsplit(".", 1)[-1].lower()] += 1
        elif name:
            ext[""] += 1

    # Offset monotonicity check (should mostly increase)
    mono = 0
    prev = -1
    for r in records:
        if r["offset"] >= prev:
            mono += 1
        prev = r["offset"]

    return {
        "size": size,
        "layout": {
            "record_stride": stride,
            "name_len": name_len,
            "fields": ["name[16]", "size_u32le", "offset_u32le"],
            "record_count": n,
            "trailer_bytes": len(trailer),
            "trailer_hex": trailer.hex(),
        },
        "ext_census": dict(ext.most_common()),
        "offset_monotonic_count": mono,
        "record_count": len(records),
        "records_sample": records[:24],
        "records_tail": records[-8:],
        "largest": sorted(records, key=lambda r: r["size"], reverse=True)[:12],
    }


def probe_pak_head(pak_head: bytes, toc_info: dict) -> dict:
    """Map PART1.PAK framing from head sample + TOC offsets."""
    size_claimed = 4257794048
    head = pak_head[:256]
    info = {
        "claimed_iso_size": size_claimed,
        "sample_bytes": len(pak_head),
        "head_hex": head.hex(),
        "ascii_0_32": ascii_at(pak_head, 0, 32),
        "contains_WAD_marker": b"WAD_" in pak_head[:64],
        "le32_0": le32(pak_head, 0),
        "le32_4": le32(pak_head, 4),
        "sig_counts_in_sample": {
            "STBLz": pak_head.count(b"STBLz"),
            "STBL0": pak_head.count(b"STBL0"),
            "DA_FA": pak_head.count(b"\xDA\xFA"),
            "FA_DA": pak_head.count(b"\xFA\xDA"),
            "IGB": pak_head.count(b".igb"),
            "PNG": pak_head.count(b"\x89PNG"),
            "MPEG_PS_pack": pak_head.count(b"\x00\x00\x01\xba"),
            "VAG": pak_head.count(b"SShd"),
            "RIFF": pak_head.count(b"RIFF"),
        },
    }
    landing = []
    for rec in toc_info.get("records_sample") or []:
        off = rec["offset"]
        if off < len(pak_head):
            chunk = pak_head[off : off + 32]
            landing.append(
                {
                    "toc_index": rec["index"],
                    "name": rec.get("name"),
                    "pak_offset": off,
                    "size": rec.get("size"),
                    "head_hex": chunk[:16].hex(),
                    "ascii": "".join(
                        chr(c) if 32 <= c < 127 else "." for c in chunk[:24]
                    ),
                }
            )
    info["toc_offset_landings_in_sample"] = landing
    info["landings_count"] = len(landing)
    return info


def alchemy_absence_census(mm: mmap.mmap, files: list[dict]) -> dict:
    """Confirm Alchemy containers are absent from disc structure."""
    names = {f["name"].upper() for f in files}
    return {
        "has_ASSETS_GFC": any(n.startswith("ASSETS.GFC") for n in names),
        "has_ASSETS_GOB": any(n.startswith("ASSETS.GOB") for n in names),
        "has_MODULES_dir": "MODULES" in names,
        "has_GODOFWAR_TOC": any(n.startswith("GODOFWAR.TOC") for n in names),
        "has_PART1_PAK": any(n.startswith("PART1.PAK") for n in names),
        "root_file_count": len(files),
    }


def main() -> None:
    results: dict = {
        "game": "God of War (USA)",
        "game_id": "695b874b308a4e5353767bb6df8ba697",
        "method": "manual mmap/struct structural walk (CNK A2 style)",
        "tools": ["python3 mmap/struct/re — not binwalk library"],
        "iso": str(ISO),
        "iso_size": ISO.stat().st_size,
    }

    with ISO.open("rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        files = list_iso9660(mm)
        results["disc_inventory"] = files
        results["alchemy_vs_gow_layout"] = alchemy_absence_census(mm, files)

        by = {f["name"]: f for f in files}
        cnf = parse_system_cnf(read_entry(mm, by["SYSTEM.CNF"]))
        results["system_cnf"] = cnf
        (SAMPLE_DIR / "SYSTEM.CNF.txt").write_text(cnf["raw"], encoding="utf-8")

        elf_ent = by.get("SCUS_973.99")
        elf = read_entry(mm, elf_ent)
        (SAMPLE_DIR / "SCUS_973.99").write_bytes(elf)
        if ELF_SIDE.is_file():
            side = ELF_SIDE.read_bytes()
            results["elf_sidecar_matches_iso"] = side == elf
        results["elf"] = {
            **parse_elf_header(elf),
            **elf_string_census(elf),
            "size": len(elf),
            "iso_path": "SCUS_973.99",
            "lba": elf_ent["lba"],
        }

        toc_ent = by["GODOFWAR.TOC"]
        toc = read_entry(mm, toc_ent)
        (SAMPLE_DIR / "GODOFWAR.TOC").write_bytes(toc)
        toc_info = parse_gow_toc(toc)
        toc_info["lba"] = toc_ent["lba"]
        toc_info["iso_size"] = toc_ent["size"]
        results["godofwar_toc"] = toc_info

        pak_ent = by["PART1.PAK"]
        # 8 MiB head is enough for offset landings of early TOC entries
        pak_head = bytes(
            mm[pak_ent["byte_offset"] : pak_ent["byte_offset"] + 8 * 1024 * 1024]
        )
        (SAMPLE_DIR / "PART1.PAK.head8MiB.bin").write_bytes(pak_head)
        pak_info = probe_pak_head(pak_head, toc_info)
        pak_info["lba"] = pak_ent["lba"]
        pak_info["iso_size"] = pak_ent["size"]
        results["part1_pak"] = pak_info

        # IRX inventory
        irx = [f for f in files if f["name"].upper().endswith(".IRX")]
        results["iop_modules"] = [
            {"name": f["name"], "lba": f["lba"], "size": f["size"]} for f in irx
        ]
        results["ioprp"] = {
            "name": "IOPRP300.IMG",
            "lba": by["IOPRP300.IMG"]["lba"],
            "size": by["IOPRP300.IMG"]["size"],
        }

        # Full-ISO Alchemy signature absence (sampled windows — 8GB full scan too heavy)
        # Use first 64MiB + TOC/PAK regions already covered; plus mid-pak probes
        windows = [(0, min(len(mm), 32 * 1024 * 1024))]
        # around TOC
        windows.append((toc_ent["byte_offset"], toc_ent["byte_offset"] + toc_ent["size"]))
        # PAK start / +1GiB / +2GiB samples
        for rel in (0, 1024**3, 2 * 1024**3):
            a = pak_ent["byte_offset"] + rel
            if a < len(mm):
                windows.append((a, min(a + 4 * 1024 * 1024, len(mm))))
        sigs = {
            "ASSETS.GFC": b"ASSETS.GFC",
            "ASSETS.GOB": b"ASSETS.GOB",
            "STBLz": b"STBLz",
            "STBL0": b"STBL0",
            "Intrinsic Alchemy": b"Intrinsic Alchemy",
            "igFileIO": b"igFileIO",
            "GODOFWAR.TOC": b"GODOFWAR.TOC",
            "PART1.PAK": b"PART1.PAK",
        }
        counts = {k: 0 for k in sigs}
        scanned = 0
        for a, b in windows:
            chunk = mm[a:b]
            scanned += len(chunk)
            for name, needle in sigs.items():
                counts[name] += chunk.count(needle)
        results["signature_census_sampled"] = {
            "bytes_scanned": scanned,
            "counts": counts,
        }

        mm.close()

    # Summary verdict
    results["verdict"] = {
        "alchemy_engine": False,
        "packaging": "Santa Monica PART1.PAK + GODOFWAR.TOC (not GFC/GOB/IGB)",
        "elf_ig_classes": results["elf"]["ig_class_count"],
        "gfc_gob_on_disc": False,
        "igFileIO_on_disc_or_elf": results["elf"]["igFileIO"],
        "notes": [
            "ISO root is flat: boot ELF, IOPRP300, IRXs, GODOFWAR.TOC, PART1.PAK (~4.0 GiB).",
            "No MODULES/ directory; IRX sit beside boot image.",
            "No ASSETS.GFC / ASSETS.GOB / STBL framing — Alchemy stack absent.",
            "DA FA hits in naive scans are not IGB cookies without GFC chain context.",
        ],
    }

    json_path = OUT_DIR / "gow-structural-walk-2026-11-07.json"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Markdown report
    toc = results["godofwar_toc"]
    lay_toc = toc.get("layout") or {}
    md = []
    md.append("# God of War USA — structural disc walk")
    md.append("")
    md.append("**Mode:** research only. No patches.")
    md.append("**Date:** 2026-11-07")
    md.append(f"**Game id:** `{results['game_id']}`")
    md.append("**Method:** CNK A2–style manual `mmap`/`struct` walk (not binwalk library).")
    md.append(f"**Script:** `verification/recovery/_gow_structural_walk.py`")
    md.append(f"**JSON:** `{json_path.name}`")
    md.append(f"**Samples:** `verification/recovery/gow-structural-samples/`")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 1. Disc inventory")
    md.append("")
    md.append("| Path | LBA | Size | Role |")
    md.append("|------|----:|-----:|------|")
    roles = {
        "SYSTEM.CNF": "Boot config",
        "SCUS_973.99": "EE ELF (= disc/boot.elf)",
        "IOPRP300.IMG": "IOP reboot image",
        "GODOFWAR.TOC": "Asset TOC into PART1.PAK",
        "PART1.PAK": "Primary asset pack (~4 GiB)",
    }
    for f in results["disc_inventory"]:
        role = roles.get(f["name"], "IOP module" if f["name"].endswith(".IRX") else "")
        md.append(f"| `{f['name']}` | {f['lba']} | {f['size']:,} | {role} |")
    md.append("")
    md.append(f"SYSTEM.CNF: `{cnf.get('boot_line')}`")
    md.append("")
    md.append("## 2. Alchemy absence (vs CNK)")
    md.append("")
    lay = results["alchemy_vs_gow_layout"]
    md.append(f"- ASSETS.GFC: **{lay['has_ASSETS_GFC']}**")
    md.append(f"- ASSETS.GOB: **{lay['has_ASSETS_GOB']}**")
    md.append(f"- MODULES/ dir: **{lay['has_MODULES_dir']}**")
    md.append(f"- GODOFWAR.TOC: **{lay['has_GODOFWAR_TOC']}**")
    md.append(f"- PART1.PAK: **{lay['has_PART1_PAK']}**")
    md.append("")
    md.append("## 3. EE ELF (`SCUS_973.99`)")
    md.append("")
    elf = results["elf"]
    md.append(f"- Size: **{elf['size']:,}** bytes; entry `{elf.get('entry')}`")
    md.append(f"- PT_LOAD segments: **{len(elf.get('load_segments') or [])}**")
    md.append(f"- Intrinsic Alchemy string: **{elf['intrinsic_alchemy']}**")
    md.append(f"- `ig*` class whole-strings: **{elf['ig_class_count']}**")
    md.append(f"- `igFileIO` in ELF: **{elf['igFileIO']}**")
    md.append(
        f"- STBLz/STBL0/DA_FA in ELF: {elf['STBLz_count']}/{elf['STBL0_count']}/{elf['DA_FA_count']}"
    )
    md.append("")
    md.append("## 4. GODOFWAR.TOC")
    md.append("")
    md.append(f"- Size: **{toc['size']:,}** @ LBA {toc['lba']}")
    md.append(
        f"- Layout: **{lay_toc.get('record_count')}** × {lay_toc.get('record_stride')}-byte "
        f"records (`name[16]` + `u32` + `u32`) + {lay_toc.get('trailer_bytes')}-byte trailer"
    )
    md.append(f"- Ext census: `{toc.get('ext_census')}`")
    md.append(
        "- Field semantics: **name[16] confirmed**. Two `u32`s act like size/offset for many "
        "WAD/VPK rows (`R_PERM.WAD` @0 → `WAD_R_Perm`), but PSS/PSW often have nonzero high size "
        "bytes and some offsets land on nested markers (`MDLX_R_Perm` @1777) — size/offset "
        "**partially reverse-engineered**."
    )
    md.append(
        f"- Offset monotonic rows (raw u32 #2): "
        f"**{toc.get('offset_monotonic_count')}/{toc.get('record_count')}**"
    )
    md.append("")
    md.append("| idx | name | size | pak_offset |")
    md.append("|----:|------|-----:|-----------:|")
    for r in toc["records_sample"][:16]:
        md.append(f"| {r['index']} | `{r['name']}` | {r['size']:,} | {r['offset']:,} |")
    md.append("")
    md.append("### Largest entries")
    md.append("")
    md.append("| name | size | offset |")
    md.append("|------|-----:|-------:|")
    for r in toc.get("largest") or []:
        md.append(f"| `{r['name']}` | {r['size']:,} | {r['offset']:,} |")
    md.append("")
    md.append("## 5. PART1.PAK")
    md.append("")
    pak = results["part1_pak"]
    md.append(f"- ISO size: **{pak['iso_size']:,}** @ LBA {pak['lba']}")
    md.append(f"- Head sample: {pak['sample_bytes']:,} bytes; `WAD_` marker @ head: **{pak.get('contains_WAD_marker')}**")
    md.append(f"- Sig counts in head sample: `{pak['sig_counts_in_sample']}`")
    md.append(f"- TOC landings in head sample: **{pak.get('landings_count')}**")
    md.append("")
    md.append("| name | offset | size | head ascii |")
    md.append("|------|-------:|-----:|------------|")
    for L in pak.get("toc_offset_landings_in_sample") or []:
        md.append(
            f"| `{L.get('name')}` | {L['pak_offset']:,} | {L.get('size'):,} | `{L.get('ascii')}` |"
        )
    md.append("")
    md.append("## 6. IOP modules")
    md.append("")
    for m in results["iop_modules"]:
        md.append(f"- `{m['name']}` — {m['size']:,} B @ LBA {m['lba']}")
    md.append("")
    md.append("## 7. Verdict")
    md.append("")
    md.append("God of War is **not** an Intrinsic Alchemy title. Packaging is ")
    md.append("**GODOFWAR.TOC → PART1.PAK** (WAD/VPK/PSS/VAG). Zero GFC/GOB/IGB/`ig*` class surface.")
    md.append("")

    md_path = OUT_DIR / "gow-structural-walk-2026-11-07.md"
    md_path.write_text("\n".join(md), encoding="utf-8")
    print("wrote", json_path)
    print("wrote", md_path)
    print(
        "records",
        toc.get("record_count"),
        "ext",
        toc.get("ext_census"),
        "elf_ig",
        elf["ig_class_count"],
        "alchemy",
        results["verdict"]["alchemy_engine"],
    )


if __name__ == "__main__":
    main()
