#!/usr/bin/env python3
"""Post-install / nightly verify: health + matrix phases + optional FPS note per library title."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAMES = ROOT / "games"
REGISTRY = ROOT / "verification" / "recovery" / "game-fix-registry.json"
LOG_DIR = ROOT / "logs" / "autonomous-pipeline"
MATRIX = ROOT / "verification" / "recovery" / "matrix_phase_check.py"


def load_registry() -> dict:
    if REGISTRY.is_file():
        return json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {"per_game": {}, "global_runtime": {}}


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
    health = evaluate_health(game_id, log_path)
    matrix = score_matrix(game_id, log_path, meta)
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
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Autonomous per-game verify (smoke + health + matrix).")
    ap.add_argument("--game", action="append", dest="games", help="Game id (hex folder); default all ready titles")
    ap.add_argument("--frames", type=int, default=0, help="Override smoke frame count")
    ap.add_argument("--json", action="store_true", help="Print JSON only")
    args = ap.parse_args()
    ids = args.games
    if not ids:
        ids = [p.name for p in GAMES.iterdir() if p.is_dir() and len(p.name) == 32 and native_exe(p.name)]
    frames = args.frames or None
    results = []
    for gid in sorted(ids):
        try:
            results.append(verify_game(gid, frames, None))
        except OSError as e:
            results.append({"game_id": gid, "status": "error", "error": str(e)})
    summary_path = LOG_DIR / f"summary-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps({"results": results}, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps({"results": results, "summary": str(summary_path.relative_to(ROOT))}, indent=2))
    else:
        for r in results:
            print(f"{r.get('game_id')}: {r.get('status')} log={r.get('log', r.get('error', ''))}")
        print(f"summary -> {summary_path}")
    return 0 if all(r.get("status") == "pass" for r in results if r.get("status") != "skipped") else 1


if __name__ == "__main__":
    raise SystemExit(main())
