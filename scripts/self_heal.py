#!/usr/bin/env python3
"""Per-install self-healing: detect symptoms from logs/build state, apply whitelisted fixes."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAMES = ROOT / "games"
REGISTRY = ROOT / "verification" / "recovery" / "game-fix-registry.json"
ISSUES_NAME = "install_issues.json"
ACTIONS_LOG = ROOT / "logs" / "self-heal"

BLACK_HINT = re.compile(r"near_zero_prims|prims=\d\b|canvas.*black", re.I)
ALCHEMY = re.compile(
    r"host_signal(?:_sema)?\((?:16|54|55)\)|virt.?LBA|\+24008|"
    r"(?<![0-9A-Fa-f])(?:0x)?0*FCE0(?![0-9A-Fa-f])|soft-arm",
    re.I,
)
GS_NEG_BOX = re.compile(r"-1[0-9]{3}\.\d,-1[0-9]{3}", re.I)
WEB_STALE = re.compile(r"content-length|ACL|ps2web\.js", re.I)
MISSING = re.compile(r"missing code at 0x", re.I)


@dataclass
class Diagnosis:
    game_id: str
    symptoms: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    actions_taken: list[dict] = field(default_factory=list)
    actions_planned: list[dict] = field(default_factory=list)


def load_registry() -> dict:
    if REGISTRY.is_file():
        return json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {"per_game": {}, "global_runtime": {}}


def read_logs(game_id: str) -> str:
    chunks: list[str] = []
    game_dir = GAMES / game_id
    for name in ("smoke.log", "health_smoke.log", "explore.log", "build.log"):
        for base in (game_dir, ROOT / "logs" / "games" / game_id):
            path = base / name
            if path.is_file():
                try:
                    chunks.append(path.read_text(encoding="utf-8", errors="replace"))
                except OSError:
                    pass
    capture = list((ROOT / "logs" / "hitman-caller-readable").glob("*.tsv"))
    if capture:
        try:
            chunks.append(capture[0].read_text(encoding="utf-8", errors="replace")[:50000])
        except OSError:
            pass
    return "\n".join(chunks)


def evaluate_symptoms(game_id: str, text: str, health: dict | None) -> Diagnosis:
    dx = Diagnosis(game_id=game_id)
    meta = load_registry().get("per_game", {}).get(game_id, {})
    if health is None:
        sys.path.insert(0, str(ROOT / "scripts"))
        import install_health

        health = install_health.evaluate_game(GAMES / game_id)
    for r in health.get("reasons") or []:
        dx.symptoms.append(r)
    for w in health.get("warnings") or []:
        dx.symptoms.append("warn:" + w)
    if MISSING.search(text):
        dx.symptoms.append("missing_code_runtime")
    if ALCHEMY.search(text) and not meta.get("alchemy_only"):
        dx.symptoms.append("alchemy_pulse_on_non_cnk")
    if GS_NEG_BOX.search(text):
        dx.symptoms.append("gs_negative_draw_boxes")
    if WEB_STALE.search(text):
        dx.symptoms.append("web_serve_or_acl")
    if (health.get("primitives") or 0) > 50000:
        dx.features.append("high_prim_throughput")
    if meta.get("tracks"):
        dx.features.extend(f"track:{t}" for t in meta["tracks"])
    return dx


def web_build_stale(game_id: str) -> bool:
    native = ROOT / "build" / f"native-{game_id}" / "ps2run.exe"
    web = ROOT / "build" / f"web-{game_id}" / "ps2web.js"
    if not native.is_file() or not web.is_file():
        return False
    return native.stat().st_mtime > web.stat().st_mtime + 2


def fix_web_acl(game_id: str) -> dict:
    web = ROOT / "build" / f"web-{game_id}"
    if not web.is_dir():
        return {"action": "web_acl", "skipped": True, "reason": "no_web_build"}
    sys.path.insert(0, str(ROOT / "scripts"))
    import windows_port

    windows_port.ensure_web_build_readable(web)
    return {"action": "web_acl", "ok": True, "path": str(web)}


def queue_web_rebuild(game_id: str) -> dict:
    """Queue web-only rebuild via windows_port (same as panel retry)."""
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        import panel

        game = panel.get_game(game_id)
        if not game:
            return {"action": "web_rebuild", "skipped": True, "reason": "no_game_metadata"}
        if game.get("status") in ("building", "queued"):
            return {"action": "web_rebuild", "skipped": True, "reason": "busy"}
        panel.enqueue(game)
        return {"action": "web_rebuild", "queued": True}
    except Exception as e:
        return {"action": "web_rebuild", "error": str(e)}


def run_smoke(game_id: str, frames: int = 200) -> dict:
    verifier = ROOT / "scripts" / "autonomous_verify.py"
    if not verifier.is_file():
        return {"action": "smoke", "skipped": True}
    proc = subprocess.run(
        [sys.executable, str(verifier), "--game", game_id, "--frames", str(frames), "--json"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=600,
    )
    out = proc.stdout or proc.stderr
    try:
        payload = json.loads(out)
    except json.JSONDecodeError:
        payload = {"raw": out[-1500:]}
    return {"action": "smoke", "exit_code": proc.returncode, "result": payload}


def heal_game(game_id: str, *, dry_run: bool = False, auto: bool = True) -> dict:
    """Detect issues for one install and apply whitelisted fixes."""
    ACTIONS_LOG.mkdir(parents=True, exist_ok=True)
    text = read_logs(game_id)
    health_path = GAMES / game_id / "health.json"
    health = json.loads(health_path.read_text(encoding="utf-8")) if health_path.is_file() else None
    dx = evaluate_symptoms(game_id, text, health)

    if "gs_negative_draw_boxes" in dx.symptoms:
        dx.actions_planned.append(
            {"fix": "global_gs_xyoffset_11bit", "note": "runtime patch; rebuild native if stale"}
        )
        if not dry_run and auto and web_build_stale(game_id):
            dx.actions_taken.append(queue_web_rebuild(game_id))

    if "web_serve_or_acl" in dx.symptoms or web_build_stale(game_id):
        dx.actions_planned.append({"fix": "web_rebuild_and_acl"})
        if not dry_run and auto:
            dx.actions_taken.append(fix_web_acl(game_id))
            if web_build_stale(game_id):
                dx.actions_taken.append(queue_web_rebuild(game_id))

    if "alchemy_pulse_on_non_cnk" in dx.symptoms:
        dx.actions_planned.append({"fix": "quarantine_alchemy", "auto": False, "note": "registry flag only"})
        reg = load_registry()
        meta = reg.setdefault("per_game", {}).setdefault(game_id, {})
        meta["disc_fix_quarantine"] = True
        meta.setdefault("tracks", []).append("alchemy_leak_detected")
        if not dry_run:
            REGISTRY.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
            dx.actions_taken.append({"action": "registry_quarantine", "game_id": game_id})

    if any(s.startswith("missing_code") or "near_zero" in s for s in dx.symptoms):
        dx.actions_planned.append({"fix": "explore_rerun", "auto": False})

    if not dry_run and auto and dx.actions_taken:
        dx.actions_taken.append(run_smoke(game_id, 200))

    report = {
        "game_id": game_id,
        "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "symptoms": dx.symptoms,
        "features": dx.features,
        "actions_planned": dx.actions_planned,
        "actions_taken": dx.actions_taken,
        "dry_run": dry_run,
    }
    out_path = GAMES / game_id / ISSUES_NAME
    if not dry_run:
        out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        (ACTIONS_LOG / f"{game_id}-{stamp}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def heal_library(*, dry_run: bool = False) -> list[dict]:
    results = []
    for path in sorted(GAMES.iterdir()):
        if not path.is_dir() or len(path.name) != 32:
            continue
        if not (ROOT / "build" / f"native-{path.name}" / "ps2run.exe").is_file():
            continue
        results.append(heal_game(path.name, dry_run=dry_run))
    return results


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Self-healing per-install patch orchestrator.")
    ap.add_argument("--game", action="append", dest="games")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--library", action="store_true")
    args = ap.parse_args()
    if args.library:
        reports = heal_library(dry_run=args.dry_run)
    elif args.games:
        reports = [heal_game(g, dry_run=args.dry_run) for g in args.games]
    else:
        ap.error("Pass --game ID or --library")
    print(json.dumps(reports, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
