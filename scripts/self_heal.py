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
STATS_FPS = re.compile(r"\[stats\].*?\b(\d+(?:\.\d+)?)\s+fps\b", re.I)
FBP_TRIAD = re.compile(
    r"dispfb_fbp=(\d+).*?frame_ctx0_fbp=(\d+)|"
    r"mode-B present:\s*dispfb_fbp=(\d+)\s*->\s*frame_ctx0_fbp=(\d+)",
    re.I,
)
HARNESS_RUN_ID = re.compile(r"(\d{8}T\d{6}Z)")
CANVAS_LUM_MIN_DEFAULT = 5.0
WEB_REBUILD_POLL_INTERVAL_S = 3.0
WEB_REBUILD_POLL_TIMEOUT_S = 1800.0
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


def min_fps_target(game_id: str) -> float:
    reg = load_registry()
    meta = reg.get("per_game", {}).get(game_id, {})
    exc = (reg.get("global_runtime") or {}).get("min_fps_exceptions") or {}
    if game_id in exc:
        return float(exc[game_id])
    if meta.get("min_fps_target") is not None:
        return float(meta["min_fps_target"])
    return float((reg.get("global_runtime") or {}).get("min_fps_default", 60))


def min_canvas_lum(game_id: str) -> float:
    reg = load_registry()
    meta = reg.get("per_game", {}).get(game_id, {})
    sh = (reg.get("global_runtime") or {}).get("self_heal") or {}
    if meta.get("min_canvas_lum") is not None:
        return float(meta["min_canvas_lum"])
    return float(sh.get("min_canvas_lum", CANVAS_LUM_MIN_DEFAULT))


def find_harness_entry(game_id: str) -> dict | None:
    latest = ROOT / "logs" / "cyberarcade-live-harness-latest.json"
    if latest.is_file():
        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = None
        if data:
            for g in data.get("results") or []:
                if g.get("id") == game_id:
                    return g
            for g in (data.get("summary") or {}).get("games") or []:
                if g.get("id") == game_id:
                    return g
    runs = ROOT / "logs" / "harness-runs"
    if runs.is_dir():
        for path in sorted(runs.iterdir(), reverse=True):
            if not path.is_dir():
                continue
            summary = path / "summary.json"
            if not summary.is_file():
                continue
            try:
                data = json.loads(summary.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for g in data.get("results") or []:
                if g.get("id") == game_id:
                    return g
    return None


def harness_observe_end_lum(harness: dict) -> float | None:
    metrics = harness.get("metrics") or harness.get("shots") or []
    if isinstance(metrics, list):
        for shot in metrics:
            if not isinstance(shot, dict):
                continue
            name = str(shot.get("name") or shot.get("shot") or "")
            if "observe_end" in name or name.endswith("04_observe_end"):
                lum = shot.get("canvas_lum")
                if lum is not None:
                    return float(lum)
    note = harness.get("goal_note") or ""
    m = re.search(r"end_lum=([\d.]+)", note)
    return float(m.group(1)) if m else None


def detect_canvas_black_harness(game_id: str, harness: dict | None) -> bool:
    if not harness:
        return False
    thresh = min_canvas_lum(game_id)
    end_lum = harness_observe_end_lum(harness)
    if end_lum is not None and end_lum < thresh:
        return True
    if harness.get("goal_ok") is False and harness.get("booted"):
        for err in harness.get("errors") or []:
            if "black_screen" in err and "observe_end" in err:
                return True
    return False


def detect_low_fps(game_id: str, text: str, harness: dict | None) -> bool:
    target = min_fps_target(game_id)
    samples: list[float] = [float(m.group(1)) for m in STATS_FPS.finditer(text)]
    if harness:
        fps = harness.get("fps") or {}
        for key in ("min", "avg"):
            if fps.get(key) is not None:
                samples.append(float(fps[key]))
        overlay = harness.get("fps_overlay") or {}
        if overlay.get("min") is not None:
            samples.append(float(overlay["min"]))
    if not samples:
        return False
    tail = samples[-25:] if len(samples) > 25 else samples
    return min(tail) < target - 1.0


def detect_fbp_triad_mismatch(text: str) -> bool:
    for m in FBP_TRIAD.finditer(text):
        a = m.group(1) or m.group(3)
        b = m.group(2) or m.group(4)
        if a and b and a != b:
            return True
    return False


def score_matrix_text(game_id: str, text: str) -> dict | None:
    meta = load_registry().get("per_game", {}).get(game_id, {})
    key = meta.get("matrix_key")
    if not key or key not in ("hitman_bm", "nfs_mw"):
        return None
    matrix = ROOT / "verification" / "recovery" / "matrix_phase_check.py"
    if not matrix.is_file():
        return {"skipped": True, "reason": "no_matrix_script"}
    log_chunk = text[-500_000:] if len(text) > 500_000 else text
    proc = subprocess.run(
        [sys.executable, str(matrix), key, "-"],
        input=log_chunk,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(ROOT),
        timeout=120,
    )
    if proc.returncode != 0:
        return {"error": (proc.stderr or proc.stdout or "matrix_phase_check failed")[:500]}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"raw": proc.stdout[-1500:]}


def poll_until_build_idle(game_id: str) -> dict:
    """Wait until panel library entry leaves building/queued (idle-aware rebuild)."""
    started = time.monotonic()
    sys.path.insert(0, str(ROOT / "scripts"))
    import panel

    last = "unknown"
    while time.monotonic() - started < WEB_REBUILD_POLL_TIMEOUT_S:
        game = panel.get_game(game_id)
        if not game:
            return {
                "action": "web_rebuild_poll",
                "skipped": True,
                "reason": "no_game_metadata",
                "waited_s": round(time.monotonic() - started, 1),
            }
        last = game.get("status", "unknown")
        if last not in ("building", "queued"):
            return {
                "action": "web_rebuild_poll",
                "ok": True,
                "status": last,
                "waited_s": round(time.monotonic() - started, 1),
            }
        time.sleep(WEB_REBUILD_POLL_INTERVAL_S)
    return {
        "action": "web_rebuild_poll",
        "timeout": True,
        "last_status": last,
        "waited_s": round(time.monotonic() - started, 1),
    }


def read_matrix_logs(game_id: str) -> str:
    """Smoke/explore logs only — avoid false matrix_fail from unrelated campaign logs."""
    chunks: list[str] = []
    game_dir = GAMES / game_id
    for name in ("smoke.log", "health_smoke.log", "explore.log"):
        for base in (game_dir, ROOT / "logs" / "games" / game_id):
            path = base / name
            if path.is_file():
                try:
                    chunks.append(path.read_text(encoding="utf-8", errors="replace"))
                except OSError:
                    pass
    ap = ROOT / "logs" / "autonomous-pipeline"
    if ap.is_dir():
        for path in sorted(ap.glob(f"{game_id}-*.log"), reverse=True)[:1]:
            try:
                chunks.append(path.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass
    return "\n".join(chunks)


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
    meta = load_registry().get("per_game", {}).get(game_id, {})
    mk = meta.get("matrix_key")
    if mk:
        tokens = [t for t in re.split(r"[_\s]+", mk.lower()) if len(t) > 2]
        for path in sorted((ROOT / "logs").glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:24]:
            name = path.name.lower()
            if not (any(t in name for t in tokens) or mk.replace("_", "") in name.replace("_", "")):
                continue
            try:
                chunks.append(path.read_text(encoding="utf-8", errors="replace")[:120000])
            except OSError:
                continue
    return "\n".join(chunks)


def evaluate_symptoms(game_id: str, text: str, health: dict | None) -> Diagnosis:
    dx = Diagnosis(game_id=game_id)
    meta = load_registry().get("per_game", {}).get(game_id, {})
    harness = find_harness_entry(game_id)
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
    if web_build_stale(game_id):
        dx.symptoms.append("web_build_stale")
    if detect_canvas_black_harness(game_id, harness):
        dx.symptoms.append("canvas_black_harness")
    if detect_low_fps(game_id, text, harness):
        dx.symptoms.append("low_fps")
    if detect_fbp_triad_mismatch(text):
        dx.symptoms.append("fbp_triad_mismatch")
    matrix = score_matrix_text(game_id, read_matrix_logs(game_id) or text[:200000])
    if matrix and matrix.get("verdict") == "fail":
        dx.symptoms.append("matrix_fail")
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


def queue_web_rebuild(game_id: str, *, wait_idle: bool = False) -> dict:
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
        out: dict = {"action": "web_rebuild", "queued": True}
        if wait_idle:
            out["poll"] = poll_until_build_idle(game_id)
        return out
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
    harness = find_harness_entry(game_id)
    matrix = score_matrix_text(game_id, read_matrix_logs(game_id) or text[:200000])

    if "gs_negative_draw_boxes" in dx.symptoms:
        dx.actions_planned.append(
            {"fix": "global_gs_xyoffset_11bit", "note": "runtime patch; rebuild native if stale"}
        )
        if not dry_run and auto and web_build_stale(game_id):
            dx.actions_taken.append(queue_web_rebuild(game_id, wait_idle=True))

    if "web_serve_or_acl" in dx.symptoms or web_build_stale(game_id):
        dx.actions_planned.append({"fix": "web_rebuild_and_acl"})
        if not dry_run and auto:
            dx.actions_taken.append(fix_web_acl(game_id))
            if web_build_stale(game_id):
                dx.actions_taken.append(queue_web_rebuild(game_id, wait_idle=True))

    if "canvas_black_harness" in dx.symptoms:
        dx.actions_planned.append(
            {"fix": "chrome_canvas_gs_invariants", "note": "harness end_lum; web rebuild if stale"}
        )
        if not dry_run and auto and web_build_stale(game_id):
            dx.actions_taken.append(queue_web_rebuild(game_id, wait_idle=True))

    if "matrix_fail" in dx.symptoms:
        dx.actions_planned.append({"fix": "matrix_phase_reprobe", "auto": False})

    if "low_fps" in dx.symptoms:
        dx.actions_planned.append({"fix": "fps_optimize_pass", "auto": False, "note": "stub — measure only"})

    if "fbp_triad_mismatch" in dx.symptoms:
        dx.actions_planned.append(
            {"fix": "gs_framebuffer_triad_audit", "auto": False, "note": "stub — DISPFB vs FRAME FBP"}
        )

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
        "detectors": {
            "harness_goal_ok": harness.get("goal_ok") if harness else None,
            "harness_end_lum": harness_observe_end_lum(harness) if harness else None,
            "matrix_verdict": matrix.get("verdict") if matrix else None,
            "min_fps_target": min_fps_target(game_id),
            "min_canvas_lum": min_canvas_lum(game_id),
        },
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
