#!/usr/bin/env python3
"""Nightly store pipeline: download → build → heal → verify.

Writes a dated summary + log under ``logs/autonomous-pipeline/``.
Respects single-writer locks under ``logs/locks/`` — never steals Hitman
``web-a2116*``, NFS ``web-60c82f*``, or CNK ``native-b49f2e*`` while cmake/ninja
are live, and never kills those processes.

Usage::

    py -3 scripts/nightly_pipeline.py --game <id> --frames 60
    py -3 scripts/nightly_pipeline.py --library --frames 200
    py -3 scripts/nightly_pipeline.py --game <id> --skip-build --dry-heal
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
GAMES = ROOT / "games"
LOCKS = ROOT / "logs" / "locks"
PIPELINE_LOG = ROOT / "logs" / "autonomous-pipeline"

# Hard quarantine: do not acquire these build trees while sibling workers own them.
PROTECTED_PREFIXES = (
    "web-a2116d2ac08a7be4db4e8455ad58d2e5",
    "web-60c82f4a111da300ac23bbec85272788",
    "native-b49f2e769315347e8bda839feb705744",
)

sys.path.insert(0, str(SCRIPTS))


def _stamp() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _game_title(game_id: str) -> str:
    ident = GAMES / game_id / "identity.json"
    if ident.is_file():
        try:
            data = json.loads(ident.read_text(encoding="utf-8"))
            title = data.get("title") or data.get("name")
            if title:
                return str(title)[:120]
        except (OSError, ValueError):
            pass
    return game_id


def list_candidate_ids(*, library: bool, games: list[str] | None) -> list[str]:
    if games:
        return list(dict.fromkeys(games))
    if not library:
        return []
    ids = []
    for path in sorted(GAMES.iterdir()):
        if not path.is_dir() or len(path.name) != 32:
            continue
        if (path / "disc.iso").is_file() or (ROOT / "build" / f"native-{path.name}" / "ps2run.exe").is_file():
            ids.append(path.name)
    return ids


def lock_paths_for(game_id: str) -> list[Path]:
    names = [
        f"native-{game_id}.lock",
        f"web-{game_id}.lock",
        f"web-{game_id}-next.lock",
    ]
    return [LOCKS / n for n in names]


def lock_is_protected(path: Path) -> bool:
    stem = path.name
    for prefix in PROTECTED_PREFIXES:
        if stem.startswith(prefix):
            return True
    return False


def cmake_ninja_live() -> bool:
    """True if cmake/ninja appear in the process table (Windows-friendly)."""
    if os.name != "nt":
        try:
            out = subprocess.check_output(["pgrep", "-x", "cmake|ninja"], text=True, stderr=subprocess.DEVNULL)
            return bool(out.strip())
        except (OSError, subprocess.CalledProcessError):
            return False
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq cmake.exe", "/NH"],
            text=True,
            stderr=subprocess.DEVNULL,
            cwd=str(ROOT),
        )
        if "cmake.exe" in out.lower():
            return True
        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq ninja.exe", "/NH"],
            text=True,
            stderr=subprocess.DEVNULL,
            cwd=str(ROOT),
        )
        return "ninja.exe" in out.lower()
    except (OSError, subprocess.CalledProcessError):
        return False


def build_blocked(game_id: str) -> dict | None:
    """Return a skip reason if we must not start a build for this game."""
    live = cmake_ninja_live()
    for lock in lock_paths_for(game_id):
        if not lock.is_file():
            continue
        protected = lock_is_protected(lock)
        if protected or live:
            return {
                "reason": "lock_present",
                "lock": str(lock.relative_to(ROOT)).replace("\\", "/"),
                "protected": protected,
                "cmake_ninja_live": live,
            }
    return None


def stage_download(game_id: str) -> dict:
    """Download stage: ISO already on disk counts as satisfied (no network re-pull)."""
    iso = GAMES / game_id / "disc.iso"
    if iso.is_file():
        return {
            "status": "ok",
            "action": "skipped_present",
            "path": str(iso.relative_to(ROOT)).replace("\\", "/"),
            "bytes": iso.stat().st_size,
        }
    return {
        "status": "fail",
        "action": "missing_iso",
        "error": "disc.iso missing — queue store download / import before nightly",
    }


def stage_build(game_id: str, *, skip_build: bool, force_build: bool) -> dict:
    native = ROOT / "build" / f"native-{game_id}" / "ps2run.exe"
    web = ROOT / "build" / f"web-{game_id}" / "ps2web.html"
    if skip_build and not force_build:
        if native.is_file():
            return {
                "status": "ok",
                "action": "skipped_present",
                "native": True,
                "web": web.is_file(),
            }
        return {"status": "fail", "action": "skip_build", "error": "native missing and --skip-build set"}

    if native.is_file() and not force_build:
        return {
            "status": "ok",
            "action": "skipped_present",
            "native": True,
            "web": web.is_file(),
        }

    blocked = build_blocked(game_id)
    if blocked:
        return {"status": "skipped", "action": "lock_skip", **blocked}

    iso = GAMES / game_id / "disc.iso"
    if not iso.is_file():
        return {"status": "fail", "action": "no_iso", "error": "cannot build without disc.iso"}

    env = {
        **os.environ,
        "PS2_BUILD_JOBS": os.environ.get("PS2_BUILD_JOBS", "1"),
        "PATH": os.pathsep.join(
            (
                str(ROOT / "tools" / "msys64" / "clang64" / "bin"),
                os.environ.get("PATH", ""),
            )
        ),
    }
    cmd = [
        sys.executable,
        "-u",
        str(SCRIPTS / "windows_port.py"),
        game_id,
        str(iso),
        "3600",
        "8",
    ]
    log_path = PIPELINE_LOG / f"nightly-build-{game_id}-{_stamp()}.log"
    PIPELINE_LOG.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        proc = subprocess.run(cmd, cwd=str(ROOT), env=env, stdout=log, stderr=subprocess.STDOUT)
    ok = proc.returncode == 0 and native.is_file()
    return {
        "status": "ok" if ok else "fail",
        "action": "windows_port",
        "exit_code": proc.returncode,
        "log": str(log_path.relative_to(ROOT)).replace("\\", "/"),
        "native": native.is_file(),
        "web": web.is_file(),
    }


def stage_heal(game_id: str, *, dry_heal: bool) -> dict:
    from self_heal import heal_game

    report = heal_game(game_id, dry_run=dry_heal, auto=not dry_heal)
    return {
        "status": "ok",
        "action": "dry_run" if dry_heal else "heal_game",
        "symptoms": report.get("symptoms") or [],
        "actions_taken": len(report.get("actions_taken") or []),
        "actions_planned": len(report.get("actions_planned") or []),
        "issues": str((GAMES / game_id / "install_issues.json").relative_to(ROOT)).replace("\\", "/")
        if (GAMES / game_id / "install_issues.json").is_file()
        else None,
    }


def stage_verify(game_id: str, frames: int) -> dict:
    from autonomous_verify import verify_game

    row = verify_game(game_id, frames, None)
    return {
        "status": row.get("status", "error"),
        "action": "autonomous_verify",
        "frames": frames,
        "log": row.get("log"),
        "health": (row.get("health") or {}).get("status"),
        "matrix": row.get("matrix"),
        "fps_metrics": row.get("fps_metrics"),
        "chrome_metrics": row.get("chrome_metrics"),
        "error": row.get("error") or row.get("reason"),
        "raw": row,
    }


def stage_chrome_serve(
    game_id: str,
    *,
    panel_base: str = "http://127.0.0.1:8620",
) -> dict:
    """Store→Chrome serve gate: panel must publish play assets without manual steps.

    Does not run the Playwright harness (that is a separate heavier check). Passes when
    ``/play/<id>/``, ``ps2web.js``, and ``ps2web.wasm`` all return HTTP 200.
    """
    import urllib.error
    import urllib.request

    paths = [
        f"/play/{game_id}/",
        f"/play/{game_id}/ps2web.js",
        f"/play/{game_id}/ps2web.wasm",
    ]
    results = []
    ok = True
    for path in paths:
        url = panel_base.rstrip("/") + path
        code = None
        err = None
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=15) as resp:
                code = getattr(resp, "status", None) or resp.getcode()
        except urllib.error.HTTPError as exc:
            code = exc.code
            err = str(exc.reason)[:120]
        except Exception as exc:  # noqa: BLE001
            # Some servers reject HEAD — retry GET.
            try:
                with urllib.request.urlopen(url, timeout=20) as resp:
                    code = getattr(resp, "status", None) or resp.getcode()
            except Exception as exc2:  # noqa: BLE001
                err = str(exc2)[:160]
                ok = False
        if code != 200:
            ok = False
        results.append({"path": path, "status": code, "error": err})
    return {
        "status": "pass" if ok else "fail",
        "action": "panel_play_assets",
        "panel_base": panel_base,
        "assets": results,
        "manual_patch_steps": False,
        "note": "Global runtime patches (R3/R4/XYOFFSET) ship in-tree; serve path needs no manual discfix apply",
    }


def run_game(
    game_id: str,
    *,
    frames: int,
    skip_build: bool,
    force_build: bool,
    dry_heal: bool,
    chrome_serve: bool = False,
    panel_base: str = "http://127.0.0.1:8620",
) -> dict:
    from store_pipeline_hooks import log_pipeline_event

    started = time.time()
    result: dict = {
        "game_id": game_id,
        "title": _game_title(game_id),
        "started": started,
        "stages": {},
    }
    log_pipeline_event("nightly_start", game_id=game_id, frames=frames)

    download = stage_download(game_id)
    result["stages"]["download"] = download
    if download.get("status") == "fail":
        result["status"] = "fail"
        result["failed_stage"] = "download"
        log_pipeline_event("nightly_game", game_id=game_id, status="fail", stage="download")
        return result

    build = stage_build(game_id, skip_build=skip_build, force_build=force_build)
    result["stages"]["build"] = build
    if build.get("status") == "fail":
        result["status"] = "fail"
        result["failed_stage"] = "build"
        log_pipeline_event("nightly_game", game_id=game_id, status="fail", stage="build")
        return result
    if build.get("status") == "skipped":
        # Locked: still attempt heal+verify on existing native if present.
        native = ROOT / "build" / f"native-{game_id}" / "ps2run.exe"
        if not native.is_file():
            result["status"] = "skipped"
            result["failed_stage"] = "build"
            log_pipeline_event("nightly_game", game_id=game_id, status="skipped", stage="build")
            return result

    try:
        heal = stage_heal(game_id, dry_heal=dry_heal)
    except Exception as exc:  # noqa: BLE001 — per-game isolation
        heal = {"status": "fail", "action": "heal_game", "error": str(exc)[:400]}
    result["stages"]["heal"] = heal
    if heal.get("status") == "fail":
        result["status"] = "fail"
        result["failed_stage"] = "heal"
        log_pipeline_event("nightly_game", game_id=game_id, status="fail", stage="heal")
        return result

    try:
        verify = stage_verify(game_id, frames)
    except Exception as exc:  # noqa: BLE001
        verify = {"status": "error", "action": "autonomous_verify", "error": str(exc)[:400]}
    result["stages"]["verify"] = verify

    vstatus = (verify.get("status") or "").lower()
    if vstatus in ("pass", "skipped"):
        result["status"] = "pass" if vstatus == "pass" else "skipped"
    else:
        result["status"] = "fail"
        result["failed_stage"] = "verify"

    if chrome_serve and result["status"] in ("pass", "skipped"):
        chrome = stage_chrome_serve(game_id, panel_base=panel_base)
        result["stages"]["chrome_serve"] = chrome
        if chrome.get("status") != "pass":
            result["status"] = "fail"
            result["failed_stage"] = "chrome_serve"

    result["elapsed_s"] = round(time.time() - started, 2)
    log_pipeline_event(
        "nightly_game",
        game_id=game_id,
        status=result["status"],
        frames=frames,
        verify_log=verify.get("log"),
        chrome_serve=(result.get("stages") or {}).get("chrome_serve", {}).get("status"),
        elapsed_s=result["elapsed_s"],
    )
    return result


def write_artifacts(summary: dict) -> tuple[Path, Path]:
    PIPELINE_LOG.mkdir(parents=True, exist_ok=True)
    stamp = summary["stamp"]
    json_path = PIPELINE_LOG / f"nightly-{stamp}.json"
    log_path = PIPELINE_LOG / f"nightly-{stamp}.log"
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"nightly_pipeline {stamp}",
        f"games={len(summary.get('results') or [])} overall={summary.get('overall')}",
        f"frames={summary.get('frames')} skip_build={summary.get('skip_build')} dry_heal={summary.get('dry_heal')}",
        "",
    ]
    for row in summary.get("results") or []:
        stages = row.get("stages") or {}
        lines.append(
            f"{row.get('game_id')}: {row.get('status')} "
            f"dl={ (stages.get('download') or {}).get('action') } "
            f"build={ (stages.get('build') or {}).get('action') } "
            f"heal={ (stages.get('heal') or {}).get('action') } "
            f"verify={ (stages.get('verify') or {}).get('status') } "
            f"log={ (stages.get('verify') or {}).get('log') }"
        )
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, log_path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Nightly download → build → heal → verify")
    ap.add_argument("--game", action="append", dest="games", help="Game id (repeatable)")
    ap.add_argument("--library", action="store_true", help="All installs with disc.iso or native")
    ap.add_argument("--frames", type=int, default=200, help="Verify smoke frames (default 200)")
    ap.add_argument("--skip-build", action="store_true", help="Never invoke windows_port (native must exist)")
    ap.add_argument("--force-build", action="store_true", help="Rebuild even when native exists")
    ap.add_argument("--dry-heal", action="store_true", help="self_heal dry-run only")
    ap.add_argument(
        "--chrome-serve",
        action="store_true",
        help="After verify pass, HEAD panel /play/<id>/ assets (store→Chrome serve gate)",
    )
    ap.add_argument(
        "--panel-base",
        default=os.environ.get("PS2_PANEL_BASE", "http://127.0.0.1:8620"),
        help="CyberArcade panel base URL for --chrome-serve",
    )
    ap.add_argument(
        "--store-contract",
        action="store_true",
        help="After each game, also evaluate store_ready_contract (no HTTP)",
    )
    ap.add_argument("--json", action="store_true", help="Print summary JSON to stdout")
    args = ap.parse_args(argv)

    ids = list_candidate_ids(library=args.library, games=args.games)
    if not ids:
        ap.error("Pass --game ID and/or --library")

    stamp = _stamp()
    results = []
    for gid in ids:
        row = run_game(
            gid,
            frames=max(30, int(args.frames)),
            skip_build=bool(args.skip_build),
            force_build=bool(args.force_build),
            dry_heal=bool(args.dry_heal),
            chrome_serve=bool(args.chrome_serve),
            panel_base=str(args.panel_base),
        )
        if args.store_contract:
            try:
                from store_ready_contract import evaluate_game

                contract = evaluate_game(gid, require_http=False)
            except Exception as exc:  # noqa: BLE001
                contract = {"status": "error", "error": str(exc)[:400]}
            row["stages"]["store_contract"] = contract
            if contract.get("status") not in ("pass", "skipped") and row.get("status") == "pass":
                row["status"] = "fail"
                row["failed_stage"] = "store_contract"
        results.append(row)

    statuses = [r.get("status") for r in results]
    if any(s == "fail" for s in statuses):
        overall = "fail"
    elif any(s == "pass" for s in statuses):
        overall = "pass" if all(s in ("pass", "skipped") for s in statuses) else "partial"
    else:
        overall = "skipped"

    summary = {
        "stamp": stamp,
        "overall": overall,
        "frames": max(30, int(args.frames)),
        "skip_build": bool(args.skip_build),
        "force_build": bool(args.force_build),
        "dry_heal": bool(args.dry_heal),
        "chrome_serve": bool(args.chrome_serve),
        "panel_base": str(args.panel_base),
        "store_contract": bool(args.store_contract),
        "results": results,
    }
    json_path, log_path = write_artifacts(summary)
    summary["artifacts"] = {
        "json": str(json_path.relative_to(ROOT)).replace("\\", "/"),
        "log": str(log_path.relative_to(ROOT)).replace("\\", "/"),
    }
    # Rewrite with artifact paths included.
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    from store_pipeline_hooks import log_pipeline_event

    log_pipeline_event(
        "nightly_complete",
        stamp=stamp,
        overall=overall,
        games=len(results),
        json=summary["artifacts"]["json"],
        log=summary["artifacts"]["log"],
    )

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"nightly overall={overall} -> {summary['artifacts']['log']}")
        for row in results:
            print(f"  {row.get('game_id')}: {row.get('status')}")
    return 0 if overall in ("pass", "skipped") else 1


if __name__ == "__main__":
    raise SystemExit(main())
