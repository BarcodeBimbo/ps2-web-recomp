"""EE ELF Alchemy surface + class map — own code; CNK VA template from A1 research."""

from __future__ import annotations

import re
import struct
from dataclasses import dataclass, field
from pathlib import Path

# Default CNK (SLUS_206.49 / boot.elf) key VA template from A1 walk.
CNK_KEY_VAS: dict[str, int] = {
    "entry": 0x00108D28,
    "loadgate_fce0": 0x0010FCE0,
    "finalize": 0x00110100,
    "factory": 0x00508930,
    "bind_install": 0x00520160,
    "bind_clear": 0x00520210,
    "null_bind": 0x0051AC80,
    "null_bind_ra": 0x0051ACEC,
    "bind_registry_bss": 0x00725F50,
    "alchemy_version": 0x006B4920,
}

IG_WHOLE = re.compile(rb"(?<![A-Za-z0-9_])(ig[A-Za-z0-9_]+)(?![A-Za-z0-9_])")
IG_CLASS_ONLY = re.compile(rb"^ig[A-Za-z0-9_]+$")
CSTRING = re.compile(rb"[\x20-\x7e]{4,}")


@dataclass
class ElfAlchemyReport:
    path: str
    source: str
    size: int
    entry_va: str | None = None
    alchemy_version: dict = field(default_factory=dict)
    key_vas: dict[str, str] = field(default_factory=dict)
    key_vas_verified_in_image: dict[str, bool] = field(default_factory=dict)
    ig_class_whole_strings: int = 0
    ig_tokens_unique: int = 0
    igb_path_strings: int = 0
    igb_raw_hits: int = 0
    named_irx_in_elf: list[str] = field(default_factory=list)
    ig_class_sample: list[str] = field(default_factory=list)
    ig_class_catalog: list[str] = field(default_factory=list)
    igb_path_catalog: list[str] = field(default_factory=list)
    prefix_density: dict[str, int] = field(default_factory=dict)


def _elf_entry(data: bytes) -> int | None:
    if data[:4] != b"\x7fELF":
        return None
    if data[4] != 1 or data[5] != 1:
        return None
    return struct.unpack_from("<I", data, 0x18)[0]


def _va_file_offset_guess(data: bytes, va: int) -> int | None:
    """CNK-style PHDR0: file 0x80 → VA 0x00100000."""
    load_va = 0x00100000
    file_off = 0x80
    if va < load_va:
        return None
    off = file_off + (va - load_va)
    if 0 <= off < len(data):
        return off
    return None


def _prefix_bucket(name: str) -> str:
    # igPsx2Foo -> Psx2 ; igAnimationBar -> Animation
    if not name.startswith("ig") or len(name) < 3:
        return "other"
    rest = name[2:]
    i = 0
    while i < len(rest) and rest[i].isupper():
        i += 1
    # include following lowercase run for Camel buckets like Psx2
    while i < len(rest) and rest[i].islower():
        i += 1
    # digits
    while i < len(rest) and rest[i].isdigit():
        i += 1
    bucket = rest[:i] if i else rest[:8]
    return bucket or "other"


def scan_elf(
    data: bytes,
    *,
    path: str,
    source: str,
    key_vas: dict[str, int] | None = None,
    collect_ig_sample: int = 40,
) -> ElfAlchemyReport:
    key_vas = key_vas or CNK_KEY_VAS
    entry = _elf_entry(data)
    report = ElfAlchemyReport(
        path=path,
        source=source,
        size=len(data),
        entry_va=f"0x{entry:08X}" if entry is not None else None,
        key_vas={k: f"0x{v:08X}" for k, v in key_vas.items()},
    )

    ver_needle = b"Intrinsic Alchemy"
    idx = data.find(ver_needle)
    ver_info: dict = {"found": idx >= 0, "string": None, "va": None, "file_offset": None}
    if idx >= 0:
        end = data.find(b"\x00", idx)
        raw = data[idx:end] if end > idx else data[idx : idx + 80]
        raw = raw.split(b"\n", 1)[0].rstrip()
        ver_info["string"] = raw.decode("ascii", "replace")
        ver_info["file_offset"] = idx
        tmpl = key_vas.get("alchemy_version")
        if tmpl is not None:
            off = _va_file_offset_guess(data, tmpl)
            if off is not None and abs(off - idx) < 0x100:
                ver_info["va"] = f"0x{tmpl:08X}"
            else:
                est = 0x00100000 + (idx - 0x80)
                ver_info["va"] = f"0x{est:08X}"
    report.alchemy_version = ver_info

    for name, va in key_vas.items():
        if name in ("bind_registry_bss", "alchemy_version"):
            report.key_vas_verified_in_image[name] = (
                name == "alchemy_version" and ver_info["found"]
            )
            continue
        off = _va_file_offset_guess(data, va)
        if off is None:
            report.key_vas_verified_in_image[name] = False
            continue
        word = struct.unpack_from("<I", data, off)[0]
        report.key_vas_verified_in_image[name] = word != 0

    whole_classes: set[str] = set()
    tokens: set[str] = set()
    igb_paths: set[str] = set()
    irx_hits: set[str] = set()
    for m in CSTRING.finditer(data):
        s = m.group(0)
        if b".igb" in s.lower():
            igb_paths.add(s.decode("ascii", "replace"))
        for irx in (b"igFileIO", b"igUKbd", b"igUMouse"):
            if irx in s:
                label = irx.decode("ascii")
                if not label.lower().endswith(".irx"):
                    label = label + ".irx"
                irx_hits.add(label)
        if IG_CLASS_ONLY.match(s):
            whole_classes.add(s.decode("ascii"))
        for tm in IG_WHOLE.finditer(s):
            tokens.add(tm.group(1).decode("ascii"))

    catalog = sorted(whole_classes)
    prefix: dict[str, int] = {}
    for name in catalog:
        b = _prefix_bucket(name)
        prefix[b] = prefix.get(b, 0) + 1
    prefix_sorted = dict(sorted(prefix.items(), key=lambda kv: (-kv[1], kv[0]))[:20])

    report.ig_class_whole_strings = len(whole_classes)
    report.ig_tokens_unique = len(tokens)
    report.igb_path_strings = len(igb_paths)
    # A1 census counted raw `.igb` occurrences (47 on CNK), not unique strings.
    report.igb_raw_hits = data.lower().count(b".igb")
    report.named_irx_in_elf = sorted(irx_hits)
    report.ig_class_sample = catalog[:collect_ig_sample]
    report.ig_class_catalog = catalog
    report.igb_path_catalog = sorted(igb_paths)
    report.prefix_density = prefix_sorted
    return report


def scan_elf_path(path: Path, **kwargs) -> ElfAlchemyReport:
    return scan_elf(path.read_bytes(), path=str(path), source="file", **kwargs)


def correlate_gfc_names_to_elf(
    elf_data: bytes, gfc_names: list[str], limit: int = 40
) -> list[dict]:
    """Match GFC .igb basenames / paths against ELF string table."""
    hits: list[dict] = []
    for name in gfc_names:
        if not name or not name.lower().endswith(".igb"):
            continue
        base = name.replace("\\", "/").split("/")[-1]
        cands = [
            name,
            name.replace("\\", "/"),
            base,
            base.lower(),
        ]
        for c in cands:
            b = c.encode("ascii", "ignore")
            if len(b) < 6:
                continue
            fo = elf_data.find(b)
            if fo >= 0:
                va = 0x00100000 + (fo - 0x80)
                hits.append(
                    {
                        "gfc_name": name,
                        "needle": c,
                        "file_offset": fo,
                        "approx_va": f"0x{va:08X}",
                    }
                )
                break
        if len(hits) >= limit:
            break
    return hits
