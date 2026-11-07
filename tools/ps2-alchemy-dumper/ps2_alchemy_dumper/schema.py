"""Assemble alchemy-map.json + TSV sidecars."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .elf_alchemy import ElfAlchemyReport
from .gfc import GfcArchive
from .iso9660 import IsoEntry


def _hex32(v: int) -> str:
    return f"0x{v:08X}"


def build_map(
    *,
    input_iso: Path,
    toc: list[IsoEntry],
    gfc: GfcArchive | None,
    gfc_entry: IsoEntry | None,
    gob_entry: IsoEntry | None,
    gob_info: dict | None,
    elf: ElfAlchemyReport | None,
    modules_irx: list[str],
    game_id_hint: str | None,
    notes: list[str],
    igb_samples: list[dict] | None = None,
    elf_gfc_corr: list[dict] | None = None,
    include_full_gfc_files: bool = True,
) -> dict[str, Any]:
    alchemy_irx = {
        "igFileIO.irx": any(x.upper() == "IGFILEIO.IRX" for x in modules_irx),
        "igUKbd.irx": any(x.upper() == "IGUKBD.IRX" for x in modules_irx),
        "igUMouse.irx": any(x.upper() == "IGUMOUSE.IRX" for x in modules_irx),
    }
    doc: dict[str, Any] = {
        "meta": {
            "schema_version": "1.1",
            "tool": "ps2-alchemy-dumper",
            "tool_version": __version__,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "input_iso": str(input_iso.resolve()),
            "game_id_hint": game_id_hint,
            "platform_target": "windows",
        },
        "disc_toc": [
            {
                "path": e.path,
                "lba": e.lba,
                "size": e.size,
                "flags": e.flags,
                "is_dir": e.is_dir,
            }
            for e in toc
        ],
        "assets_gfc": {"present": False},
        "assets_gob": {"present": False},
        "igb_samples": igb_samples or [],
        "elf_alchemy": None,
        "elf_gfc_correlation": elf_gfc_corr or [],
        "modules": {
            "dir": "MODULES",
            "irx": modules_irx,
            "alchemy_irx_on_disc": alchemy_irx,
            "note": (
                "Alchemy IOP helpers are often named in the EE ELF but absent from "
                "retail MODULES (name-HLE on host)."
            ),
        },
        "notes": notes,
    }

    if gfc is not None and gfc_entry is not None:
        payload: dict[str, Any] = {
            "present": True,
            "path": gfc_entry.path,
            "lba": gfc_entry.lba,
            "size": gfc_entry.size,
            "magic": _hex32(gfc.magic),
            "gob_size": gfc.gob_size,
            "nblocks": gfc.nblocks,
            "nfiles": gfc.nfiles,
            "name_stride": gfc.name_stride,
            "ext_census": gfc.ext_census(),
        }
        if include_full_gfc_files:
            payload["files"] = [
                {
                    "index": f.index,
                    "name": f.name,
                    "crc32": _hex32(f.crc32),
                    "uncompressed_size": f.uncompressed_size,
                    "first_block": f.first_block,
                }
                for f in gfc.files
            ]
        doc["assets_gfc"] = payload

    if gob_entry is not None:
        doc["assets_gob"] = {
            "present": True,
            "path": gob_entry.path,
            "lba": gob_entry.lba,
            "size": gob_entry.size,
            **(gob_info or {}),
        }

    if elf is not None:
        doc["elf_alchemy"] = {
            "path": elf.path,
            "source": elf.source,
            "size": elf.size,
            "entry_va": elf.entry_va,
            "alchemy_version": elf.alchemy_version,
            "key_vas": elf.key_vas,
            "key_vas_verified_in_image": elf.key_vas_verified_in_image,
            "ig_class_whole_strings": elf.ig_class_whole_strings,
            "ig_tokens_unique": elf.ig_tokens_unique,
            "igb_path_strings": elf.igb_path_strings,
            "igb_raw_hits": elf.igb_raw_hits,
            "named_irx_in_elf": elf.named_irx_in_elf,
            "ig_class_sample": elf.ig_class_sample,
            "prefix_density": elf.prefix_density,
            "igb_path_catalog": elf.igb_path_catalog,
            # Full catalog lives in class-map.tsv; keep count here.
            "ig_class_catalog_count": len(elf.ig_class_catalog),
        }

    return doc


def write_outputs(
    out_dir: Path,
    doc: dict[str, Any],
    *,
    write_tsv: bool = True,
    class_catalog: list[str] | None = None,
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    json_path = out_dir / "alchemy-map.json"
    json_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    written.append(json_path)

    if write_tsv:
        toc_path = out_dir / "disc-toc.tsv"
        with toc_path.open("w", encoding="utf-8", newline="\n") as f:
            f.write("path\tlba\tsize\tflags\tis_dir\n")
            for row in doc.get("disc_toc", []):
                f.write(
                    f"{row['path']}\t{row['lba']}\t{row['size']}\t{row['flags']}\t{int(row['is_dir'])}\n"
                )
        written.append(toc_path)

        gfc = doc.get("assets_gfc") or {}
        if gfc.get("present") and gfc.get("files"):
            gfc_path = out_dir / "gfc-files.tsv"
            with gfc_path.open("w", encoding="utf-8", newline="\n") as f:
                f.write("index\tname\tcrc32\tuncompressed_size\tfirst_block\n")
                for row in gfc["files"]:
                    f.write(
                        f"{row['index']}\t{row['name']}\t{row['crc32']}\t"
                        f"{row['uncompressed_size']}\t{row['first_block']}\n"
                    )
            written.append(gfc_path)

        samples = doc.get("igb_samples") or []
        if samples:
            igb_path = out_dir / "igb-samples.tsv"
            with igb_path.open("w", encoding="utf-8", newline="\n") as f:
                f.write(
                    "name\tcrc32\tsize\tfirst_block\textracted_len\t"
                    "da_fa_offset\tda_fa_at_0x28\terror\tig_meta_count\n"
                )
                for s in samples:
                    f.write(
                        f"{s.get('name','')}\t{s.get('crc32','')}\t"
                        f"{s.get('uncompressed_size','')}\t{s.get('first_block','')}\t"
                        f"{s.get('extracted_len','')}\t{s.get('da_fa_offset','')}\t"
                        f"{int(bool(s.get('da_fa_at_0x28')))}\t{s.get('error') or ''}\t"
                        f"{s.get('ig_meta_count', 0)}\n"
                    )
            written.append(igb_path)

        if class_catalog:
            cm = out_dir / "class-map.tsv"
            with cm.open("w", encoding="utf-8", newline="\n") as f:
                f.write("index\tclass\n")
                for i, name in enumerate(class_catalog):
                    f.write(f"{i}\t{name}\n")
            written.append(cm)

    return written
