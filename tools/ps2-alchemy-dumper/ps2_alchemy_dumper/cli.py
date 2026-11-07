"""CLI for ps2-alchemy-dumper — ISO-first Alchemy isolation map."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .disc import DiscAccess
from .elf_alchemy import CNK_KEY_VAS, correlate_gfc_names_to_elf, scan_elf
from .gfc import parse_gfc
from .gob import (
    extract_file,
    probe_igb_head,
    sample_stbl_heads,
    select_igb_targets,
    verify_blocks,
)
from .optical import describe_stub
from .schema import build_map, write_outputs
from .verify import summarize, verify_alchemy_map

DEFAULT_NOTES = [
    "Custom Windows tool — does not wrap redumper / dumps2iso / mkps2iso binaries.",
    "Credits: https://github.com/superg/redumper (GPL-3.0), https://github.com/N4gtan/mkps2iso (GPL-2.0).",
    "CNK synthesis: verification/recovery/alchemy-rebuild-synthesis-a1-a4-2026-11-07.md",
]


def _game_id_hint(iso: Path) -> str | None:
    parts = iso.resolve().parts
    for i, p in enumerate(parts):
        if p.lower() == "games" and i + 1 < len(parts):
            return parts[i + 1]
    return None


def _sidecar_elf(iso: Path) -> Path | None:
    cand = iso.parent / "disc" / "boot.elf"
    return cand if cand.is_file() else None


def _resolve_iso(args: argparse.Namespace) -> Path:
    """Accept positional ISO or ``--iso`` alias (MASTER / muscle-memory)."""
    raw = getattr(args, "iso_flag", None) or getattr(args, "iso", None)
    if not raw:
        raise SystemExit("error: ISO path required (positional or --iso)")
    return Path(raw)


def cmd_list_iso(args: argparse.Namespace) -> int:
    iso = _resolve_iso(args)
    with DiscAccess(iso) as disc:
        for e in disc.iter_files():
            kind = "DIR" if e.is_dir else "FILE"
            print(f"{e.lba:8d}  {e.size:12d}  {kind:4s}  {e.path}")
        print(f"# {len(disc.toc)} entries from {iso}", file=sys.stderr)
    return 0


def _run_map(iso: Path, args: argparse.Namespace) -> tuple[dict, list[str] | None]:
    notes = list(DEFAULT_NOTES)
    if getattr(args, "note", None):
        notes.extend(args.note)

    with DiscAccess(iso) as disc:
        toc = disc.toc
        gfc_ent = disc.find("ASSETS.GFC")
        gob_ent = disc.find("ASSETS.GOB")
        boot_ent = disc.find_boot()

        gfc = parse_gfc(disc.read_entry(gfc_ent)) if gfc_ent else None

        gob_info: dict = {}
        igb_samples: list[dict] = []
        if gob_ent is not None and gfc is not None:
            reader = disc.gob_reader(gob_ent)
            block_verify = verify_blocks(reader, gfc)
            gob_info["block_verify"] = block_verify
            gob_info["block_verify_all_stbl"] = all(v["is_stbl"] for v in block_verify)
            gob_size_match = gfc.gob_size == gob_ent.size
            gob_info["gob_size_matches_gfc"] = gob_size_match

            if args.sample_gob:
                window = min(gob_ent.size, args.gob_window)
                gob_info["stbl_sample"] = sample_stbl_heads(reader(0, window))

            # Inflate priority / sample IGB heads
            if args.igb_heads > 0:
                heads_dir = Path(args.output) / "igb_heads"
                if args.save_igb_heads:
                    heads_dir.mkdir(parents=True, exist_ok=True)
                targets = select_igb_targets(gfc, limit=args.igb_heads)
                for fe in targets:
                    er = extract_file(
                        reader, gfc, fe, max_bytes=args.igb_max_bytes
                    )
                    sample: dict = {
                        "name": fe.name,
                        "crc32": f"0x{fe.crc32:08X}",
                        "uncompressed_size": fe.uncompressed_size,
                        "first_block": fe.first_block,
                        "blocks_walked": er.blocks_walked,
                        "complete": er.complete,
                        "error": er.error,
                        "extracted_len": len(er.data) if er.data else 0,
                    }
                    if er.data:
                        sample.update(probe_igb_head(er.data))
                        if args.save_igb_heads:
                            safe = (
                                fe.name.replace("\\", "_")
                                .replace("/", "_")
                                .replace(":", "_")
                            )[:80]
                            outp = heads_dir / f"{fe.crc32:08X}_{safe}.bin"
                            outp.write_bytes(er.data[: min(len(er.data), 4096)])
                            sample["head_file"] = str(outp.name)
                    igb_samples.append(sample)

        elf_report = None
        elf_bytes = None
        elf_label = None
        elf_source = None
        if boot_ent is not None:
            elf_bytes = disc.read_entry(boot_ent)
            elf_label = boot_ent.path
            elf_source = "iso"
        else:
            side = _sidecar_elf(iso)
            if side is not None:
                elf_bytes = side.read_bytes()
                elf_label = str(side)
                elf_source = "sidecar"

        if elf_bytes is not None and elf_label is not None and elf_source is not None:
            elf_report = scan_elf(
                elf_bytes,
                path=elf_label,
                source=elf_source,
                key_vas=CNK_KEY_VAS,
            )

        corr = []
        if elf_bytes is not None and gfc is not None:
            names = [f.name for f in gfc.files if f.name.lower().endswith(".igb")]
            corr = correlate_gfc_names_to_elf(elf_bytes, names, limit=40)

        modules_irx = disc.modules_irx()

        doc = build_map(
            input_iso=iso,
            toc=toc,
            gfc=gfc,
            gfc_entry=gfc_ent,
            gob_entry=gob_ent,
            gob_info=gob_info if gob_ent else None,
            elf=elf_report,
            modules_irx=modules_irx,
            game_id_hint=_game_id_hint(iso),
            notes=notes,
            igb_samples=igb_samples,
            elf_gfc_corr=corr,
        )
        catalog = elf_report.ig_class_catalog if elf_report else None
        return doc, catalog


def cmd_map(args: argparse.Namespace) -> int:
    iso = _resolve_iso(args)
    args.iso = str(iso)
    out_dir = Path(args.output)
    doc, catalog = _run_map(iso, args)
    written = write_outputs(
        out_dir, doc, write_tsv=not args.no_tsv, class_catalog=catalog
    )
    for p in written:
        print(p)

    gfc_n = (doc.get("assets_gfc") or {}).get("nfiles")
    samples = doc.get("igb_samples") or []
    dafa_ok = sum(
        1
        for s in samples
        if s.get("error") is None
        and (s.get("da_fa_at_0x28") or s.get("da_fa_offset") is not None)
    )
    print(
        f"# alchemy-map schema {doc['meta']['schema_version']} | toc={len(doc['disc_toc'])} | "
        f"gfc_files={gfc_n} | modules_irx={len(doc['modules']['irx'])} | "
        f"elf={bool(doc.get('elf_alchemy'))} | igb_da_fa={dafa_ok}/{len(samples)}",
        file=sys.stderr,
    )

    if args.verify:
        checks = verify_alchemy_map(doc, profile=args.verify_profile)
        passed, total = summarize(checks)
        for c in checks:
            mark = "PASS" if c["ok"] else "FAIL"
            print(f"  [{mark}] {c['name']}: {c['detail']}", file=sys.stderr)
        print(f"# verify {passed}/{total}", file=sys.stderr)
        return 0 if passed == total else 2
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Map + hard CNK assertions in one shot."""
    args.verify = True
    if not hasattr(args, "verify_profile"):
        args.verify_profile = "cnk"
    if not hasattr(args, "sample_gob"):
        args.sample_gob = True
    args.sample_gob = True
    args.save_igb_heads = getattr(args, "save_igb_heads", True)
    return cmd_map(args)


def cmd_optical(args: argparse.Namespace) -> int:
    info = describe_stub(args.drive)
    print(json.dumps(info, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ps2-alchemy-dumper",
        description="Custom Windows PS2 Alchemy ISO isolation mapper (own code).",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list-iso", help="List ISO9660 paths with LBA/size")
    p_list.add_argument("iso", nargs="?", default=None, help="Path to disc.iso")
    p_list.add_argument("--iso", dest="iso_flag", default=None, help="Alias for ISO path")
    p_list.set_defaults(func=cmd_list_iso)

    def add_map_args(sp: argparse.ArgumentParser) -> None:
        sp.add_argument(
            "iso",
            nargs="?",
            default=None,
            help="Path to disc.iso (or pass --iso)",
        )
        sp.add_argument(
            "--iso",
            dest="iso_flag",
            default=None,
            help="Alias for positional ISO path",
        )
        sp.add_argument("-o", "--output", default="out", help="Output directory")
        sp.add_argument("--no-tsv", action="store_true", help="Skip TSV sidecars")
        sp.add_argument(
            "--sample-gob",
            action="store_true",
            help="Window-scan ASSETS.GOB for STBL tags",
        )
        sp.add_argument(
            "--gob-window",
            type=int,
            default=2 * 1024 * 1024,
            help="Bytes of GOB to sample when --sample-gob (default 2 MiB)",
        )
        sp.add_argument(
            "--igb-heads",
            type=int,
            default=16,
            help="How many .igb entries to inflate/probe",
        )
        sp.add_argument(
            "--igb-max-bytes",
            type=int,
            default=128 * 1024,
            help="Max inflated bytes per IGB sample (default 128 KiB)",
        )
        sp.add_argument(
            "--save-igb-heads",
            action="store_true",
            help="Write first 4 KiB of each inflated IGB under out/igb_heads/",
        )
        sp.add_argument(
            "--verify",
            action="store_true",
            help="Run CNK expectation checks after map",
        )
        sp.add_argument(
            "--verify-profile",
            default="cnk",
            help="Expectation profile (default: cnk)",
        )
        sp.add_argument("--note", action="append", default=[], help="Extra notes[] entry")

    p_map = sub.add_parser("map", help="Emit alchemy-map.json (+ TSV) from an ISO")
    add_map_args(p_map)
    p_map.set_defaults(func=cmd_map)

    p_ver = sub.add_parser(
        "verify",
        help="Full CNK end-to-end map + assertion suite (debug gate)",
    )
    add_map_args(p_ver)
    p_ver.set_defaults(func=cmd_verify, verify=True, sample_gob=True, save_igb_heads=True)

    p_opt = sub.add_parser("optical", help="Show optical-rip stub (no drive I/O yet)")
    p_opt.add_argument("--drive", help="Windows drive letter, e.g. E:")
    p_opt.set_defaults(func=cmd_optical)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
