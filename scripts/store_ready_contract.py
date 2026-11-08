#!/usr/bin/env python3
"""Store pull → Chrome playable contract (no manual patch steps).

Definition of done for master-campaign §3:
  - library status ``ready``
  - ``disc.iso`` present
  - browser player published (``build/web-<id>/ps2web.html``)
  - global runtime patches already in tree (R3 readee, R4-D1 DiskReady, GS XYOFFSET)
  - no per-game ``MANUAL_PATCHES*`` / ``patches.pending`` leftovers
  - panel post-build hooks wired (``finalize_post_build`` import path)
  - optional: loopback ``/play/<id>/`` returns HTTP 200

Usage::

    py -3 scripts/store_ready_contract.py --game <id>
    py -3 scripts/store_ready_contract.py --library --json
    py -3 scripts/store_ready_contract.py --game <id> --http
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAMES = ROOT / "games"
REGISTRY = ROOT / "verification" / "recovery" / "game-fix-registry.json"
PIPELINE_LOG = ROOT / "logs" / "autonomous-pipeline"
PANEL_ORIGIN = "http://127.0.0.1:8620"

# Source markers proving patches are pre-applied in the shared runtime (not per install).
PATCH_MARKERS = (
    {
        "id": "R3_readee",
        "path": "runtime/src/iop/cdvdfsv.cpp",
        "needle": "Match retail cdvdfsv cdvd_readee",
    },
    {
        "id": "R4D1_DiskReady",
        "path": "runtime/src/iop/cdvd.cpp",
        "needle": "sceCdDiskReady",
    },
    {
        "id": "GS_XYOFFSET",
        "path": "runtime/src/gs/gs.hpp",
        "needle": "xyoffset_component",
    },
)

MANUAL_PATCH_GLOBS = (
    "MANUAL_PATCHES*",
    "patches.pending",
    "manual_patches.json",
    "APPLY_PATCHES.txt",
)


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def global_patches_in_tree(*, root: Path = ROOT) -> dict:
    checks = []
    ok = True
    for marker in PATCH_MARKERS:
        path = root / marker["path"]
        present = False
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
                present = marker["needle"] in text
            except OSError:
                present = False
        checks.append({"id": marker["id"], "path": marker["path"], "present": present})
        if not present:
            ok = False
    # Registry should list the disc-fix pair as applied.
    reg = _read_json(root / "verification" / "recovery" / "game-fix-registry.json")
    applied = list((reg.get("global_runtime") or {}).get("disc_fix_applied") or [])
    for expected in ("R3_readee", "R4D1_DiskReady"):
        listed = expected in applied
        checks.append({"id": f"registry_{expected}", "present": listed, "applied": applied})
        if not listed:
            ok = False
    return {"ok": ok, "checks": checks}


def panel_hooks_wired(*, root: Path = ROOT) -> dict:
    panel = root / "scripts" / "panel.py"
    hooks = root / "scripts" / "store_pipeline_hooks.py"
    issues = []
    if not hooks.is_file():
        issues.append("store_pipeline_hooks.py missing")
    else:
        text = hooks.read_text(encoding="utf-8", errors="replace")
        for name in ("finalize_post_build", "begin_install_manifest", "gate_inline_verify"):
            if name not in text:
                issues.append(f"hooks missing {name}")
    if not panel.is_file():
        issues.append("panel.py missing")
    else:
        text = panel.read_text(encoding="utf-8", errors="replace")
        if "finalize_post_build" not in text:
            issues.append("panel.py does not call finalize_post_build")
        if "begin_install_manifest" not in text and "note_post_download" not in text:
            issues.append("panel.py missing post-download manifest hook")
    return {"ok": not issues, "issues": issues}


def manual_patch_leftovers(game_dir: Path) -> list[str]:
    found = []
    for pattern in MANUAL_PATCH_GLOBS:
        found.extend(str(p.relative_to(game_dir)).replace("\\", "/") for p in game_dir.glob(pattern))
    return found


def check_http_play(game_id: str, *, origin: str = PANEL_ORIGIN, timeout: float = 5.0) -> dict:
    url = f"{origin.rstrip('/')}/play/{game_id}/"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(64)
            return {
                "ok": 200 <= int(resp.status) < 300 and bool(body),
                "status": int(resp.status),
                "url": url,
                "bytes_sample": len(body),
            }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"ok": False, "status": None, "url": url, "error": str(exc)[:240]}


def evaluate_game(
    game_id: str,
    *,
    root: Path = ROOT,
    require_http: bool = False,
    origin: str = PANEL_ORIGIN,
) -> dict:
    game_dir = root / "games" / game_id
    lib = _read_json(game_dir / "library.json")
    web = root / "build" / f"web-{game_id}" / "ps2web.html"
    native = root / "build" / f"native-{game_id}" / "ps2run.exe"
    iso = game_dir / "disc.iso"
    leftovers = manual_patch_leftovers(game_dir) if game_dir.is_dir() else ["game_dir_missing"]
    patches = global_patches_in_tree(root=root)
    hooks = panel_hooks_wired(root=root)

    checks = {
        "library_ready": lib.get("status") == "ready",
        "disc_iso": iso.is_file(),
        "web_player": web.is_file(),
        "native_optional": native.is_file(),
        "no_manual_patch_files": not leftovers,
        "global_patches_preapplied": patches["ok"],
        "panel_hooks_wired": hooks["ok"],
    }
    http = None
    if require_http:
        http = check_http_play(game_id, origin=origin)
        checks["chrome_play_http"] = bool(http.get("ok"))

    # DoD: ready + iso + web + patches + hooks + no manual leftovers (+ http if requested).
    required = [
        "library_ready",
        "disc_iso",
        "web_player",
        "no_manual_patch_files",
        "global_patches_preapplied",
        "panel_hooks_wired",
    ]
    if require_http:
        required.append("chrome_play_http")
    ok = all(checks.get(k) for k in required)

    return {
        "game_id": game_id,
        "title": lib.get("title") or game_id,
        "status": "pass" if ok else "fail",
        "checks": checks,
        "manual_patch_leftovers": leftovers,
        "patches": patches,
        "hooks": hooks,
        "http": http,
        "paths": {
            "library": str((game_dir / "library.json").relative_to(root)).replace("\\", "/")
            if (game_dir / "library.json").is_file()
            else None,
            "web": str(web.relative_to(root)).replace("\\", "/") if web.is_file() else None,
            "iso": str(iso.relative_to(root)).replace("\\", "/") if iso.is_file() else None,
        },
    }


def list_ready_ids(*, root: Path = ROOT) -> list[str]:
    ids = []
    games = root / "games"
    if not games.is_dir():
        return ids
    for path in sorted(games.iterdir()):
        if not path.is_dir() or len(path.name) != 32:
            continue
        lib = _read_json(path / "library.json")
        if lib.get("status") == "ready":
            ids.append(path.name)
    return ids


def write_artifact(summary: dict) -> Path:
    PIPELINE_LOG.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    path = PIPELINE_LOG / f"store-ready-contract-{stamp}.json"
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Store pull → Chrome playable contract")
    ap.add_argument("--game", action="append", dest="games", help="Game id (repeatable)")
    ap.add_argument("--library", action="store_true", help="All library.json ready titles")
    ap.add_argument("--http", action="store_true", help="Require panel /play/<id>/ HTTP 200")
    ap.add_argument("--origin", default=PANEL_ORIGIN, help="Panel origin (default 8620)")
    ap.add_argument("--json", action="store_true", help="Print summary JSON")
    ap.add_argument("--write-artifact", action="store_true", help="Write under logs/autonomous-pipeline/")
    args = ap.parse_args(argv)

    ids = list(dict.fromkeys(args.games or []))
    if args.library:
        ids.extend(gid for gid in list_ready_ids() if gid not in ids)
    if not ids:
        ap.error("Pass --game ID and/or --library")

    results = [
        evaluate_game(gid, require_http=bool(args.http), origin=args.origin) for gid in ids
    ]
    overall = "pass" if results and all(r.get("status") == "pass" for r in results) else "fail"
    summary = {
        "stamp": time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
        "overall": overall,
        "require_http": bool(args.http),
        "results": results,
        "definition": (
            "Store pull → ready web player with global patches pre-applied; "
            "no per-game manual patch files; panel hooks on install path."
        ),
    }
    if args.write_artifact:
        art = write_artifact(summary)
        summary["artifact"] = str(art.relative_to(ROOT)).replace("\\", "/")

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"store_ready_contract overall={overall} games={len(results)}")
        for row in results:
            print(f"  {row['game_id']}: {row['status']} web={row['checks'].get('web_player')}")
        if summary.get("artifact"):
            print(f"artifact={summary['artifact']}")
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
