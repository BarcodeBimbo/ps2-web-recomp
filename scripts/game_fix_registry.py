#!/usr/bin/env python3
"""Versioned game-fix registry helpers (machine-readable discfix applied list).

Schema id: ``ps2recomp.game_fix_registry/v1``
Canonical applied list: ``global_runtime.discfix_applied`` (objects with id/status/files).
Legacy ``global_runtime.disc_fix_applied`` string lists remain readable for older fixtures.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "verification" / "recovery" / "game-fix-registry.json"
BOARD = ROOT / "verification" / "recovery" / "discfix-matrix-board.json"

SCHEMA_ID = "ps2recomp.game_fix_registry/v1"
SCHEMA_VERSION = 1
REQUIRED_APPLIED_IDS = ("R3_readee", "R4D1_DiskReady")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def load_registry(*, path: Path | None = None) -> dict[str, Any]:
    return _read_json(path or REGISTRY)


def load_board(*, path: Path | None = None) -> dict[str, Any]:
    return _read_json(path or BOARD)


def _entry_id(item: Any) -> str | None:
    if isinstance(item, str) and item.strip():
        return item.strip()
    if isinstance(item, dict):
        raw = item.get("id")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return None


def discfix_applied_entries(reg: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return normalized applied entries (always dicts with at least ``id``)."""
    gr = (reg or {}).get("global_runtime") or {}
    raw = gr.get("discfix_applied")
    if raw is None:
        raw = gr.get("disc_fix_applied")
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        fid = _entry_id(item)
        if not fid:
            continue
        if isinstance(item, dict):
            entry = dict(item)
            entry["id"] = fid
            out.append(entry)
        else:
            out.append({"id": fid})
    return out


def discfix_applied_ids(reg: dict[str, Any] | None) -> list[str]:
    return [e["id"] for e in discfix_applied_entries(reg)]


def schema_ok(reg: dict[str, Any] | None) -> bool:
    if not isinstance(reg, dict):
        return False
    if reg.get("schema") != SCHEMA_ID:
        return False
    try:
        ver = int(reg.get("schema_version"))
    except (TypeError, ValueError):
        return False
    return ver == SCHEMA_VERSION


def validate_registry(
    reg: dict[str, Any] | None,
    *,
    board: dict[str, Any] | None = None,
    require_board_sync: bool = True,
) -> list[str]:
    """Return problem strings; empty list means valid."""
    problems: list[str] = []
    if not isinstance(reg, dict) or not reg:
        return ["registry missing or empty"]
    if reg.get("schema") != SCHEMA_ID:
        problems.append(f"schema want {SCHEMA_ID!r} got {reg.get('schema')!r}")
    try:
        ver = int(reg.get("schema_version"))
        if ver != SCHEMA_VERSION:
            problems.append(f"schema_version want {SCHEMA_VERSION} got {ver}")
    except (TypeError, ValueError):
        problems.append("schema_version missing or not int")

    gr = reg.get("global_runtime")
    if not isinstance(gr, dict):
        problems.append("global_runtime missing")
        return problems

    rich = gr.get("discfix_applied")
    if not isinstance(rich, list) or not rich:
        problems.append("global_runtime.discfix_applied missing or empty")
    else:
        seen: set[str] = set()
        for i, item in enumerate(rich):
            if not isinstance(item, dict):
                problems.append(f"discfix_applied[{i}] not object")
                continue
            fid = _entry_id(item)
            if not fid:
                problems.append(f"discfix_applied[{i}] missing id")
                continue
            if fid in seen:
                problems.append(f"discfix_applied duplicate id {fid}")
            seen.add(fid)
            status = item.get("status")
            if not isinstance(status, str) or not status.strip():
                problems.append(f"discfix_applied[{fid}] missing status")
            files = item.get("files")
            if files is None and item.get("file"):
                files = [item.get("file")]
            if not isinstance(files, list) or not files or not all(isinstance(f, str) and f for f in files):
                problems.append(f"discfix_applied[{fid}] files must be non-empty string list")
            board_path = item.get("board_path")
            if not isinstance(board_path, str) or not board_path.strip():
                problems.append(f"discfix_applied[{fid}] missing board_path")

        for required in REQUIRED_APPLIED_IDS:
            if required not in seen:
                problems.append(f"discfix_applied missing required id {required}")

    # Legacy alias: if present, must match rich ids (no drift).
    legacy = gr.get("disc_fix_applied")
    if legacy is not None:
        if not isinstance(legacy, list):
            problems.append("disc_fix_applied legacy alias must be a list")
        else:
            legacy_ids = [x for x in (_entry_id(i) for i in legacy) if x]
            rich_ids = discfix_applied_ids(reg)
            if legacy_ids != rich_ids:
                problems.append(
                    f"disc_fix_applied alias drift: {legacy_ids} != discfix_applied {rich_ids}"
                )

    per_game = reg.get("per_game")
    if not isinstance(per_game, dict) or not per_game:
        problems.append("per_game missing or empty")

    if require_board_sync:
        board = board if board is not None else load_board()
        applied = ((board or {}).get("discfix") or {}).get("applied") or {}
        if not isinstance(applied, dict) or not applied:
            problems.append("discfix-matrix-board discfix.applied missing")
        else:
            board_ids = set(applied.keys())
            reg_ids = set(discfix_applied_ids(reg))
            if board_ids != reg_ids:
                problems.append(
                    f"board/registry applied id mismatch board={sorted(board_ids)} reg={sorted(reg_ids)}"
                )
            for fid, meta in applied.items():
                if not isinstance(meta, dict):
                    continue
                if meta.get("status") != "verified_apply":
                    problems.append(f"board {fid} status not verified_apply")

    return problems


def audit(*, registry_path: Path | None = None, board_path: Path | None = None) -> dict[str, Any]:
    reg = load_registry(path=registry_path)
    board = load_board(path=board_path)
    problems = validate_registry(reg, board=board, require_board_sync=True)
    return {
        "schema": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "registry_path": str(registry_path or REGISTRY),
        "ok": not problems,
        "problems": problems,
        "discfix_applied_ids": discfix_applied_ids(reg),
        "discfix_applied": discfix_applied_entries(reg),
        "per_game_count": len((reg.get("per_game") or {})),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate versioned game-fix registry")
    ap.add_argument("--json", action="store_true", help="print audit JSON")
    ap.add_argument("--registry", type=Path, default=None)
    ap.add_argument("--board", type=Path, default=None)
    args = ap.parse_args(argv)
    result = audit(registry_path=args.registry, board_path=args.board)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = "pass" if result["ok"] else "fail"
        print(f"game_fix_registry audit: {status}")
        for p in result["problems"]:
            print(f"  - {p}")
        print(f"  applied={result['discfix_applied_ids']} per_game={result['per_game_count']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
