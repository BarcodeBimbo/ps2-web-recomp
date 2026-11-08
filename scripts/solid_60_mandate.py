#!/usr/bin/env python3
"""Solid-60 mandate helpers + WebGPU/present pacing measurement (no V-Sync uncap).

Policy (master plan §0 / §5):
  - Default target is sustained ≥60 FPS (true 30/50 only via registry allowlist + reason).
  - FPS overlay is diagnostic only — never a pass signal.
  - Frameskip / V-Sync-off uncap are not allowed fixes.
  - Measurement of present-pacing constants is allowed; product uncap is God-locked.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "verification" / "recovery" / "game-fix-registry.json"
WEB_CPP = ROOT / "host" / "web.cpp"
WINDOW_CPP = ROOT / "host" / "window.cpp"
GS_CPP = ROOT / "runtime" / "src" / "gs" / "gs.cpp"
MEASURE_OUT = ROOT / "logs" / "workers" / "W-HOST-present-pacing-measure-2026-11-07.json"
LIBRARY_OUT = ROOT / "logs" / "workers" / "W-HOST-solid60-library-measure-2026-11-07.json"

# True 50/60 Hz art/timing exceptions only — never "we can't hit 60".
ALLOWED_EXCEPTION_FPS = {30.0, 50.0}


def load_registry() -> dict:
    if REGISTRY.is_file():
        return json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {"per_game": {}, "global_runtime": {}}


def load_registry_checked() -> tuple[dict, list[dict]]:
    """Load registry and audit min_fps_exceptions against policy (safe no-op when empty)."""
    reg = load_registry()
    return reg, validate_exceptions(reg)


def _exception_entry(raw: Any) -> dict | None:
    """Normalize min_fps_exceptions value to {min_fps, reason, ...}."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return {
            "min_fps": float(raw),
            "reason": "",
            "evidence": "",
            "verified_date": "",
            "legacy_scalar": True,
        }
    if isinstance(raw, dict):
        fps = raw.get("min_fps", raw.get("fps", raw.get("target")))
        if fps is None:
            return None
        return {
            "min_fps": float(fps),
            "reason": str(raw.get("reason") or raw.get("note") or ""),
            "evidence": str(raw.get("evidence") or ""),
            "verified_date": str(raw.get("verified_date") or raw.get("date") or ""),
            "legacy_scalar": False,
            "approved": bool(raw.get("approved", True)),
        }
    return None


def resolve_min_fps(game_id: str, reg: dict | None = None) -> dict:
    """Resolve solid-60 target for a title (allowlist → per-game → default 60)."""
    reg = reg or load_registry()
    meta = (reg.get("per_game") or {}).get(game_id) or {}
    global_rt = reg.get("global_runtime") or {}
    default = float(global_rt.get("min_fps_default", 60))
    exc_map = global_rt.get("min_fps_exceptions") or {}

    if game_id in exc_map:
        entry = _exception_entry(exc_map[game_id])
        if entry and entry.get("approved", True):
            target = float(entry["min_fps"])
            ok = target in ALLOWED_EXCEPTION_FPS
            return {
                "game_id": game_id,
                "min_fps": target,
                "source": "min_fps_exceptions",
                "allowlisted": True,
                "reason": entry.get("reason") or "",
                "exception_valid": ok,
                "exception_error": None
                if ok
                else f"allowlist fps must be one of {sorted(ALLOWED_EXCEPTION_FPS)}",
            }

    if meta.get("min_fps_target") is not None:
        return {
            "game_id": game_id,
            "min_fps": float(meta["min_fps_target"]),
            "source": "per_game.min_fps_target",
            "allowlisted": False,
            "reason": "",
            "exception_valid": True,
            "exception_error": None,
        }

    return {
        "game_id": game_id,
        "min_fps": default,
        "source": "min_fps_default",
        "allowlisted": False,
        "reason": "",
        "exception_valid": True,
        "exception_error": None,
    }


def validate_exceptions(reg: dict | None = None) -> list[dict]:
    """Audit registry allowlist entries (schema + allowed fps set)."""
    reg = reg or load_registry()
    exc_map = (reg.get("global_runtime") or {}).get("min_fps_exceptions") or {}
    problems: list[dict] = []
    for gid, raw in exc_map.items():
        entry = _exception_entry(raw)
        if not entry:
            problems.append({"game_id": gid, "error": "unparseable_exception"})
            continue
        if entry["min_fps"] not in ALLOWED_EXCEPTION_FPS:
            problems.append(
                {
                    "game_id": gid,
                    "error": "fps_not_in_allowlist_set",
                    "min_fps": entry["min_fps"],
                    "allowed": sorted(ALLOWED_EXCEPTION_FPS),
                }
            )
        if not entry.get("reason"):
            problems.append(
                {
                    "game_id": gid,
                    "error": "missing_reason",
                    "note": "true 30/50 Hz exceptions require a registry reason",
                }
            )
        if entry.get("legacy_scalar"):
            problems.append(
                {
                    "game_id": gid,
                    "error": "legacy_scalar",
                    "note": 'prefer {"min_fps": 30, "reason": "..."}',
                }
            )
    return problems


def _fps_block(metrics: dict | None, key: str) -> dict:
    if not metrics:
        return {}
    block = metrics.get(key)
    return block if isinstance(block, dict) else {}


def detect_frameskip_signals(metrics: dict | None, log_text: str = "") -> list[str]:
    """Flag frameskip / hitch-train signals. Never treat skip as an acceptable fix."""
    hits: list[str] = []
    text = log_text or ""
    if re.search(r"frameskip|frame_skip|skip.?frame", text, re.I):
        hits.append("log_frameskip_keyword")
    if re.search(r"PS2_VSYNC\s*=\s*(0|off|false)", text, re.I):
        hits.append("log_vsync_disabled")
    if re.search(r"uncap(?:ped)?|fps.?limit\s*=\s*0", text, re.I):
        hits.append("log_uncap_hint")

    overlay = _fps_block(metrics, "fps_overlay")
    fps = _fps_block(metrics, "fps")
    # maxMs spikes with collapsed overlay min while stats claim ~60 → hitch/skip train.
    try:
        max_ms = overlay.get("maxMs_peak")
        ov_min = overlay.get("min")
        st_avg = fps.get("avg")
        if max_ms is not None and float(max_ms) >= 100.0 and ov_min is not None and float(ov_min) <= 1.0:
            if st_avg is not None and float(st_avg) >= 55.0:
                hits.append("overlay_hitch_train_maxMs")
    except (TypeError, ValueError):
        pass

    on_screen = None
    if metrics:
        on_screen = metrics.get("fps_on_screen_last") or metrics.get("on_screen")
        nested = metrics.get("fps_metrics") or {}
        if on_screen is None:
            on_screen = nested.get("fps_on_screen_last")
    if on_screen is not None:
        try:
            if int(on_screen) == 0 and fps.get("avg") and float(fps["avg"]) > 1.0:
                hits.append("zero_on_screen_with_nonzero_fps")
        except (TypeError, ValueError):
            pass
    return hits


def evaluate_solid_60(
    game_id: str,
    *,
    chrome_metrics: dict | None = None,
    fps_metrics: dict | None = None,
    log_text: str = "",
    reg: dict | None = None,
) -> dict:
    """Solid-60 verdict: stats/harness FPS only; overlay never passes; frameskip never OK."""
    target_info = resolve_min_fps(game_id, reg)
    target = float(target_info["min_fps"])
    metrics = dict(chrome_metrics or {})
    if fps_metrics:
        # Prefer explicit chrome fps; fall back to parsed stats.
        if "fps" not in metrics and fps_metrics.get("fps_avg") is not None:
            metrics["fps"] = {
                "avg": fps_metrics.get("fps_avg"),
                "min": fps_metrics.get("fps_min"),
                "max": fps_metrics.get("fps_max"),
            }
        if fps_metrics.get("fps_on_screen_last") is not None:
            metrics["fps_on_screen_last"] = fps_metrics["fps_on_screen_last"]

    fps = _fps_block(metrics, "fps")
    overlay = _fps_block(metrics, "fps_overlay")
    skip_hits = detect_frameskip_signals(metrics, log_text)

    # Acceptance samples: harness/stats FPS only — never overlay.
    samples: list[float] = []
    for key in ("min", "avg"):
        if fps.get(key) is not None:
            try:
                samples.append(float(fps[key]))
            except (TypeError, ValueError):
                pass
    if fps_metrics and fps_metrics.get("fps_min") is not None:
        try:
            samples.append(float(fps_metrics["fps_min"]))
        except (TypeError, ValueError):
            pass

    overlay_only = bool(overlay) and not samples
    sustained = None
    if samples:
        sustained = min(samples)

    violations: list[str] = []
    if target_info.get("exception_error"):
        violations.append(f"bad_allowlist:{target_info['exception_error']}")
    if overlay_only:
        violations.append("fps_overlay_only_rejected")
    if skip_hits:
        violations.extend(f"frameskip:{h}" for h in skip_hits)
    if sustained is None:
        violations.append("no_stats_fps_samples")
    elif sustained < target - 1.0:
        violations.append(f"below_target:{sustained:.2f}<{target}")

    passed = not violations
    return {
        "game_id": game_id,
        "pass": passed,
        "min_fps_target": target,
        "target_info": target_info,
        "sustained_fps": sustained,
        "stats_fps": fps or None,
        "fps_overlay_ignored_for_pass": True,
        "fps_overlay_observed": overlay or None,
        "frameskip_signals": skip_hits,
        "violations": violations,
        "policy": {
            "no_fps_overlay_pass": True,
            "no_frameskip_fix": True,
            "no_vsync_uncap": True,
            "measure_only_pacing": True,
        },
    }


def _search(src: str, pattern: str, flags: int = 0) -> str | None:
    m = re.search(pattern, src, flags)
    return m.group(1) if m else None


def measure_present_pacing() -> dict:
    """Static measure of WebGPU/present pacing constants (no runtime / no V-Sync change)."""
    web = WEB_CPP.read_text(encoding="utf-8", errors="replace") if WEB_CPP.is_file() else ""
    win = WINDOW_CPP.read_text(encoding="utf-8", errors="replace") if WINDOW_CPP.is_file() else ""
    gs = GS_CPP.read_text(encoding="utf-8", errors="replace") if GS_CPP.is_file() else ""

    kmax_em = _search(
        gs,
        r"#ifdef __EMSCRIPTEN__\s*constexpr std::uint32_t kMaxBehind\s*=\s*(\d+)",
        re.S,
    )
    kmax_nat = _search(
        gs,
        r"#else\s*constexpr std::uint32_t kMaxBehind\s*=\s*(\d+)",
        re.S,
    )
    raf_skip = _search(web, r"presents_queued\(\)\s*>\s*(\d+)")
    budget = _search(web, r"render_pending\([^;]*?,\s*([0-9.]+)\s*\)")
    spin = _search(web, r"sleep_ms\s*>\s*([0-9.]+)")
    vsync_default = _search(web, r"std::atomic<bool>\s+g_vsync\{(true|false)\}")
    period_default = _search(
        web, r"std::atomic<double>\s+g_frame_period_ms\{([^}]+)\}"
    )
    vsync_clamp = "fps > 60.5" in web and "g_vsync" in web
    uncap_guard = "Uncapped is only legal with V-Sync off" in web
    native_has_pace = "void pace()" in win
    native_calls_post = "post_present()" in win

    measured = {
        "schema": "ps2recomp.present_pacing.measure/v1",
        "god_lock": "no_vsync_uncap_without_unlock",
        "sources": {
            "host_web": str(WEB_CPP.relative_to(ROOT)).replace("\\", "/"),
            "host_window": str(WINDOW_CPP.relative_to(ROOT)).replace("\\", "/"),
            "gs": str(GS_CPP.relative_to(ROOT)).replace("\\", "/"),
        },
        "constants": {
            "kMaxBehind_emscripten": int(kmax_em) if kmax_em else None,
            "kMaxBehind_native": int(kmax_nat) if kmax_nat else None,
            "raf_skip_when_presents_queued_gt": int(raf_skip) if raf_skip else None,
            "render_pending_budget_ms": float(budget) if budget else None,
            "pace_spin_tail_ms": float(spin) if spin else None,
            "g_vsync_default": vsync_default == "true" if vsync_default else None,
            "g_frame_period_ms_expr": period_default,
            "vsync_on_fps_cap_60": vsync_clamp,
            "uncap_forbidden_under_vsync": uncap_guard,
            "native_window_has_pace": native_has_pace,
            "native_window_calls_post_present": native_calls_post,
        },
        "interpretation": {
            "steady_play": "depth 0–1 → hard RAF wait every present",
            "hitch_recovery": "depth >2 → skip RAF wait only (not a frameskip product)",
            "ee_backpressure": "post_present stalls EE beyond kMaxBehind",
            "mandate": "solid 60 via stats FPS; overlay/diagnostic only; no V-Sync uncap apply",
            "native_note": "host/window.cpp has its own pace()+post_present; shared kMaxBehind from gs.cpp",
        },
        "product_changes_applied": False,
    }
    # Native pace flags are informational; do not fail measure if absent.
    required = {
        k: v
        for k, v in measured["constants"].items()
        if not k.startswith("native_window_")
    }
    missing = [k for k, v in required.items() if v is None]
    measured["measure_complete"] = not missing
    measured["missing_fields"] = missing
    return measured


def measure_library_solid_60(reg: dict | None = None) -> dict:
    """Evaluate solid-60 against existing harness metrics only (no Chrome launch)."""
    reg = reg or load_registry()
    by_id: dict[str, dict] = {}
    latest = ROOT / "logs" / "cyberarcade-harness-metrics-latest.json"
    if latest.is_file():
        try:
            blob = json.loads(latest.read_text(encoding="utf-8"))
            for g in blob.get("games") or []:
                if g.get("game_id"):
                    by_id[g["game_id"]] = g
        except (OSError, json.JSONDecodeError):
            pass
    runs = ROOT / "logs" / "harness-runs"
    if runs.is_dir():
        for path in sorted(runs.iterdir(), reverse=True):
            metrics = path / "metrics.json"
            if not metrics.is_file():
                continue
            try:
                blob = json.loads(metrics.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for g in blob.get("games") or []:
                gid = g.get("game_id")
                if gid and gid not in by_id:
                    by_id[gid] = g

    rows: list[dict] = []
    for gid, meta in sorted((reg.get("per_game") or {}).items()):
        if meta.get("alchemy_only") or meta.get("disc_fix_quarantine"):
            rows.append({"game_id": gid, "title": meta.get("title"), "status": "quarantined"})
            continue
        cm = by_id.get(gid)
        if not cm:
            rows.append({"game_id": gid, "title": meta.get("title"), "status": "no_chrome_metrics"})
            continue
        verdict = evaluate_solid_60(gid, chrome_metrics=cm, reg=reg)
        rows.append(
            {
                "game_id": gid,
                "title": meta.get("title"),
                "status": "pass" if verdict["pass"] else "fail",
                "solid_60": verdict,
            }
        )
    return {
        "schema": "ps2recomp.solid60.library_measure/v1",
        "exception_problems": validate_exceptions(reg),
        "titles": len(rows),
        "pass": sum(1 for r in rows if r.get("status") == "pass"),
        "fail": sum(1 for r in rows if r.get("status") == "fail"),
        "no_metrics": sum(1 for r in rows if r.get("status") == "no_chrome_metrics"),
        "quarantined": sum(1 for r in rows if r.get("status") == "quarantined"),
        "rows": rows,
    }


def write_measure(path: Path | None = None) -> dict:
    path = path or MEASURE_OUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = measure_present_pacing()
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    data["written"] = str(path.relative_to(ROOT)).replace("\\", "/")
    return data


def _self_check() -> int:
    """Offline checks: pacing measure + Hitman metrics reject overlay-only / low min."""
    errors: list[str] = []
    m = measure_present_pacing()
    if not m.get("measure_complete"):
        errors.append(f"measure incomplete: {m.get('missing_fields')}")
    c = m["constants"]
    if c.get("g_vsync_default") is not True:
        errors.append("expected g_vsync default true")
    if c.get("uncap_forbidden_under_vsync") is not True:
        errors.append("expected uncap guard under vsync")
    if c.get("kMaxBehind_emscripten") != 4:
        errors.append(f"kMaxBehind_emscripten={c.get('kMaxBehind_emscripten')}")
    if c.get("raf_skip_when_presents_queued_gt") != 2:
        errors.append(f"raf skip depth={c.get('raf_skip_when_presents_queued_gt')}")

    # Synthetic: overlay-only must fail.
    ov_only = evaluate_solid_60(
        "synthetic",
        chrome_metrics={"fps_overlay": {"avg": 60.0, "min": 60.0}},
    )
    if ov_only["pass"] or "fps_overlay_only_rejected" not in ov_only["violations"]:
        errors.append("overlay-only must not pass")

    # Synthetic: solid stats pass at 60.
    ok = evaluate_solid_60(
        "synthetic",
        chrome_metrics={"fps": {"avg": 60.0, "min": 59.5, "max": 60.0}},
    )
    if not ok["pass"]:
        errors.append(f"expected pass got {ok['violations']}")

    # Synthetic: frameskip keyword fails.
    skip = evaluate_solid_60(
        "synthetic",
        chrome_metrics={"fps": {"avg": 60.0, "min": 60.0}},
        log_text="enabled frameskip to smooth gameplay",
    )
    if skip["pass"] or not any(v.startswith("frameskip:") for v in skip["violations"]):
        errors.append("frameskip keyword must fail")

    # Allowlist schema: 30 with reason OK to resolve; bare 45 invalid.
    reg = {
        "global_runtime": {
            "min_fps_default": 60,
            "min_fps_exceptions": {
                "good30": {"min_fps": 30, "reason": "true 30 Hz title"},
                "bad45": {"min_fps": 45, "reason": "fake"},
            },
        },
        "per_game": {},
    }
    good = resolve_min_fps("good30", reg)
    if not good["allowlisted"] or good["min_fps"] != 30 or not good["exception_valid"]:
        errors.append(f"good30 resolve failed: {good}")
    bad = resolve_min_fps("bad45", reg)
    if bad["exception_valid"]:
        errors.append("bad45 should be exception_valid=False")
    problems = validate_exceptions(reg)
    if not any(p.get("game_id") == "bad45" for p in problems):
        errors.append("validate_exceptions missed bad45")

    # Live Hitman harness metrics if present — expect fail on min dip (measure only).
    latest = ROOT / "logs" / "cyberarcade-harness-metrics-latest.json"
    hitman = "a2116d2ac08a7be4db4e8455ad58d2e5"
    live = None
    if latest.is_file():
        try:
            blob = json.loads(latest.read_text(encoding="utf-8"))
            for g in blob.get("games") or []:
                if g.get("game_id") == hitman:
                    live = evaluate_solid_60(hitman, chrome_metrics=g)
                    break
        except (OSError, json.JSONDecodeError):
            pass

    print(
        json.dumps(
            {
                "self_check_ok": not errors,
                "errors": errors,
                "pacing": m["constants"],
                "hitman_live_verdict": live,
            },
            indent=2,
        )
    )
    return 0 if not errors else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--measure", action="store_true", help="Write pacing measure JSON under logs/workers/")
    ap.add_argument("--library", action="store_true", help="Measure solid-60 across registry from existing harness metrics")
    ap.add_argument("--self-check", action="store_true", help="Offline mandate + measure checks")
    ap.add_argument("--game", action="append", dest="games", help="Evaluate solid-60 for game id(s)")
    ap.add_argument("--validate-exceptions", action="store_true", help="Audit registry allowlist")
    ap.add_argument("--json-out", type=Path, help="Optional path for combined JSON output")
    args = ap.parse_args()

    out: dict[str, Any] = {}
    asked = any([args.self_check, args.games, args.validate_exceptions, args.library])
    if args.measure or not asked:
        out["measure"] = write_measure()

    if args.validate_exceptions:
        out["exception_problems"] = validate_exceptions()

    if args.library:
        lib = measure_library_solid_60()
        LIBRARY_OUT.parent.mkdir(parents=True, exist_ok=True)
        LIBRARY_OUT.write_text(json.dumps(lib, indent=2) + "\n", encoding="utf-8")
        lib["written"] = str(LIBRARY_OUT.relative_to(ROOT)).replace("\\", "/")
        out["library"] = lib

    if args.games:
        latest = ROOT / "logs" / "cyberarcade-harness-metrics-latest.json"
        by_id: dict[str, dict] = {}
        if latest.is_file():
            try:
                blob = json.loads(latest.read_text(encoding="utf-8"))
                for g in blob.get("games") or []:
                    if g.get("game_id"):
                        by_id[g["game_id"]] = g
            except (OSError, json.JSONDecodeError):
                pass
        out["evaluations"] = [
            evaluate_solid_60(gid, chrome_metrics=by_id.get(gid)) for gid in args.games
        ]

    if args.self_check:
        rc = _self_check()
        if args.json_out:
            # self-check already printed; still allow measure side-write
            if "measure" in out:
                args.json_out.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        return rc

    if not out:
        out["measure"] = write_measure()

    text = json.dumps(out, indent=2)
    print(text)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
