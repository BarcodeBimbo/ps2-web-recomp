#!/usr/bin/env python3
"""Post-install / nightly verify: health + matrix phases + optional FPS note per library title."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAMES = ROOT / "games"
REGISTRY = ROOT / "verification" / "recovery" / "game-fix-registry.json"
LOG_DIR = ROOT / "logs" / "autonomous-pipeline"
MATRIX = ROOT / "verification" / "recovery" / "matrix_phase_check.py"
HARNESS_METRICS = ROOT / "logs" / "cyberarcade-harness-metrics-latest.json"
HARNESS_SUMMARY = ROOT / "logs" / "cyberarcade-live-harness-latest.json"

STATS_FPS = re.compile(
    r"\[stats\]\s+frame\s+\d+\s+([\d.]+)\s+fps(?:\s+\((\d+)\s+on screen\))?",
    re.I,
)
STOPPED_CYCLES = re.compile(
    r"\[ee\]\s+stopped after (\d+) frames,\s*(\d+) cycles",
    re.I,
)


def load_registry() -> dict:
    if REGISTRY.is_file():
        return json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {"per_game": {}, "global_runtime": {}}


def registry_exception_audit() -> list[dict]:
    """Wire solid_60_mandate.validate_exceptions into verify summaries (safe when empty)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from solid_60_mandate import validate_exceptions

    return validate_exceptions(load_registry())


def library_solid60_measure(*, write: bool = True) -> dict:
    """Prep helper for §5 library Chrome sweep — harness metrics only, no cmake."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from solid_60_mandate import measure_library_solid60

    return measure_library_solid60(write=write)


def native_exe(game_id: str) -> Path | None:
    p = ROOT / "build" / f"native-{game_id}" / "ps2run.exe"
    return p if p.is_file() else None


def run_smoke(game_id: str, frames: int, env: dict | None) -> tuple[int, Path]:
    exe = native_exe(game_id)
    if exe is None:
        raise FileNotFoundError(f"No native build: build/native-{game_id}/ps2run.exe")
    boot = GAMES / game_id / "disc" / "boot.elf"
    iso = GAMES / game_id / "disc.iso"
    if not boot.is_file():
        raise FileNotFoundError(f"Missing boot.elf for {game_id}")
    if not iso.is_file():
        raise FileNotFoundError(f"Missing disc.iso for {game_id}")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    log_path = LOG_DIR / f"{game_id}-{frames}f-{stamp}.log"
    cmd = [str(exe), str(boot), "--disc", str(iso)]
    cmd += ["--frames", str(frames)]
    merged_env = {**dict(**{k: v for k, v in __import__("os").environ.items()}), **(env or {})}
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        proc = subprocess.run(cmd, cwd=str(ROOT), env=merged_env, stdout=log, stderr=subprocess.STDOUT)
    return proc.returncode, log_path


def score_matrix(game_id: str, log_path: Path, meta: dict) -> dict:
    key = meta.get("matrix_key") or game_id
    if key not in ("hitman_bm", "nfs_mw"):
        return {"skipped": True, "reason": "no_matrix_profile"}
    text = log_path.read_text(encoding="utf-8", errors="replace")
    proc = subprocess.run(
        [sys.executable, str(MATRIX), key, "-"],
        input=text,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    if proc.returncode != 0:
        return {"error": proc.stderr.strip() or "matrix_phase_check failed"}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"raw": proc.stdout[-2000:]}


def parse_fps_from_log(text: str) -> dict:
    """Native smoke + optional web statslog lines — measurement only (no pacing changes)."""
    fps_vals = [float(m.group(1)) for m in STATS_FPS.finditer(text)]
    on_screen = [int(m.group(2)) for m in STATS_FPS.finditer(text) if m.group(2)]
    stopped = STOPPED_CYCLES.search(text)
    out: dict = {
        "fps_samples": len(fps_vals),
        "fps_avg": (sum(fps_vals) / len(fps_vals)) if fps_vals else None,
        "fps_min": min(fps_vals) if fps_vals else None,
        "fps_max": max(fps_vals) if fps_vals else None,
        "fps_on_screen_last": on_screen[-1] if on_screen else None,
        "native_vblank_frames": int(stopped.group(1)) if stopped else None,
        "ee_cycles_per_vblank": (
            int(stopped.group(2)) / int(stopped.group(1))
            if stopped and int(stopped.group(1)) > 0
            else None
        ),
        "source": "stats_log" if fps_vals else ("native_stopped" if stopped else None),
    }
    return out


def harness_chrome_metrics(game_id: str) -> dict | None:
    for path in (HARNESS_METRICS,):
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for g in data.get("games", []):
            if g.get("game_id") == game_id:
                return {
                    "run_id": data.get("run_id"),
                    "canvas_lum_end": g.get("canvas_lum_end"),
                    "canvas_black_end": g.get("canvas_black_end"),
                    "fps": g.get("fps"),
                    "fps_overlay": g.get("fps_overlay"),
                    "bootmenu": g.get("bootmenu"),
                    "max_prims": g.get("max_prims"),
                }
    if not HARNESS_SUMMARY.is_file():
        return None
    try:
        blob = json.loads(HARNESS_SUMMARY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    for r in blob.get("results", []):
        if r.get("id") == game_id:
            canvas_end = None
            for a in r.get("analyses") or []:
                if a.get("tag") == "04_observe_end" and a.get("canvas_lum") is not None:
                    canvas_end = a.get("canvas_lum")
            return {
                "run_id": (blob.get("summary") or {}).get("run_id"),
                "canvas_lum_end": canvas_end,
                "fps": r.get("fps"),
                "fps_overlay": r.get("fps_overlay"),
            }
    return None


def evaluate_health(game_id: str, log_path: Path) -> dict:
    sys.path.insert(0, str(ROOT / "scripts"))
    import install_health

    text = log_path.read_text(encoding="utf-8", errors="replace")
    return install_health.analyze_log(text)


def verify_game(game_id: str, frames: int | None, env: dict | None) -> dict:
    reg = load_registry()
    meta = reg.get("per_game", {}).get(game_id, {})
    if meta.get("disc_fix_quarantine") or meta.get("alchemy_only"):
        return {"game_id": game_id, "status": "skipped", "reason": "quarantined_track"}
    use_frames = frames or meta.get("smoke_frames", 400)
    code, log_path = run_smoke(game_id, use_frames, env)
    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    health = evaluate_health(game_id, log_path)
    fps_metrics = parse_fps_from_log(log_text)
    chrome_metrics = harness_chrome_metrics(game_id)
    matrix = score_matrix(game_id, log_path, meta)
    # Solid-60: measure/report only here — does not flip smoke status (Chrome gate owns that).
    sys.path.insert(0, str(ROOT / "scripts"))
    from solid_60_mandate import evaluate_solid_60

    solid_60 = evaluate_solid_60(
        game_id,
        chrome_metrics=chrome_metrics,
        fps_metrics=fps_metrics,
        log_text=log_text,
        reg=reg,
    )
    status = "pass" if code == 0 and health.get("status") != "fail" else "fail"
    if matrix and not matrix.get("skipped") and matrix.get("verdict") == "fail":
        status = "fail"
    return {
        "game_id": game_id,
        "title": meta.get("title", game_id),
        "status": status,
        "exit_code": code,
        "log": str(log_path.relative_to(ROOT)),
        "health": health,
        "matrix": matrix,
        "fps_metrics": fps_metrics,
        "chrome_metrics": chrome_metrics,
        "solid_60": solid_60,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Autonomous per-game verify (smoke + health + matrix).")
    ap.add_argument("--game", action="append", dest="games", help="Game id (hex folder); default all ready titles")
    ap.add_argument("--frames", type=int, default=0, help="Override smoke frame count")
    ap.add_argument("--json", action="store_true", help="Print JSON only")
    ap.add_argument(
        "--library-measure",
        action="store_true",
        help="Solid-60 library measure from harness metrics only (no native smoke / no cmake)",
    )
    ap.add_argument(
        "--skip-locked",
        action="store_true",
        help="Skip game ids that hold logs/locks/native-* or web-* locks (avoid contending Hitman/NFS/CNK)",
    )
    args = ap.parse_args()

    exception_problems = registry_exception_audit()

    if args.library_measure:
        lib = library_solid60_measure(write=True)
        payload = {
            "mode": "library_measure",
            "exception_problems": exception_problems,
            "library": lib,
        }
        summary_path = LOG_DIR / f"library-measure-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        payload["summary"] = str(summary_path.relative_to(ROOT)).replace("\\", "/")
        print(json.dumps(payload, indent=2))
        return 0 if not exception_problems else 1

    ids = args.games
    if not ids:
        ids = [p.name for p in GAMES.iterdir() if p.is_dir() and len(p.name) == 32 and native_exe(p.name)]
    if args.skip_locked:
        lock_dir = ROOT / "logs" / "locks"
        locked: set[str] = set()
        if lock_dir.is_dir():
            for lock in lock_dir.glob("*.lock"):
                name = lock.name
                for prefix in ("native-", "web-"):
                    if name.startswith(prefix) and name.endswith(".lock"):
                        rest = name[len(prefix) : -5]
                        gid = rest.split("-", 1)[0]
                        if len(gid) == 32:
                            locked.add(gid)
        ids = [g for g in ids if g not in locked]
    frames = args.frames or None
    results = []
    for gid in sorted(ids):
        try:
            results.append(verify_game(gid, frames, None))
        except OSError as e:
            results.append({"game_id": gid, "status": "error", "error": str(e)})
    summary = {
        "exception_problems": exception_problems,
        "results": results,
    }
    summary_path = LOG_DIR / f"summary-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if args.json:
        print(
            json.dumps(
                {
                    "exception_problems": exception_problems,
                    "results": results,
                    "summary": str(summary_path.relative_to(ROOT)),
                },
                indent=2,
            )
        )
    else:
        if exception_problems:
            print(f"registry exception_problems: {exception_problems}")
        for r in results:
            print(f"{r.get('game_id')}: {r.get('status')} log={r.get('log', r.get('error', ''))}")
        print(f"summary -> {summary_path}")
    ok = all(r.get("status") == "pass" for r in results if r.get("status") != "skipped")
    return 0 if ok and not exception_problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
