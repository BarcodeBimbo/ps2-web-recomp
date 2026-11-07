"""Parse explore/smoke logs into games/<id>/health.json for install-time gating.

Generic across all titles: catches missing code, WaitSema stalls with no draw,
halts, and near-zero prim black screens before the UI marks a game ready.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

MISSING_CODE = re.compile(r'missing code at 0x([0-9A-Fa-f]+)', re.I)
PRIMS = re.compile(r'\[gs\]\s+(\d+)\s+primitives drawn', re.I)
WAIT_SEMA = re.compile(r'WaitSema\((\d+)\)', re.I)
# Real fault halt — ignore the normal "halted: frame limit reached" end-of-smoke line.
HALTED = re.compile(r'halted:\s*(?!frame limit reached)(\S.+)', re.I)
FRAME_LIMIT = re.compile(r'frame limit reached', re.I)
STOPPED = re.compile(r'\[ee\] stopped after (\d+) frames', re.I)


def _read(path: Path) -> str:
    if not path or not path.is_file():
        return ''
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


def analyze_log(text: str, *, min_prims: int = 8, boot_frames: int = 60) -> dict:
    reasons: list[str] = []
    warnings: list[str] = []
    missing = [m.group(1).lower() for m in MISSING_CODE.finditer(text)]
    prim_matches = [int(m.group(1)) for m in PRIMS.finditer(text)]
    prims = prim_matches[-1] if prim_matches else None
    frames = None
    stopped = STOPPED.search(text)
    if stopped:
        frames = int(stopped.group(1))
    wait = WAIT_SEMA.findall(text)
    halt_m = HALTED.search(text)
    halted = bool(halt_m)
    reached_limit = bool(FRAME_LIMIT.search(text))

    if missing:
        reasons.append('missing_code:' + ','.join(dict.fromkeys(missing)))
    if halted:
        reasons.append('halted:' + halt_m.group(1).strip()[:80])
    if prims is not None and prims < min_prims and (frames is None or frames >= boot_frames):
        reasons.append(f'near_zero_prims:{prims}')
    if wait and prims is not None and prims < min_prims:
        reasons.append('waitsema_no_draw:' + ','.join(dict.fromkeys(wait[-4:])))
    elif wait and not reached_limit and prims is not None and prims < 100:
        warnings.append('waitsema_low_draw:' + ','.join(dict.fromkeys(wait[-4:])))

    if reasons:
        status = 'fail'
    elif warnings:
        status = 'warn'
    else:
        status = 'ok'

    return {
        'status': status,
        'reasons': reasons,
        'warnings': warnings,
        'primitives': prims,
        'frames': frames,
        'missing_code': missing,
        'reached_frame_limit': reached_limit,
    }


def evaluate_game(game_dir: Path, *, min_prims: int = 8) -> dict:
    game_dir = Path(game_dir)
    try:
        from log_paths import resolve_game_log
    except ImportError:
        resolve_game_log = None
    sources = []
    best = None
    # Smoke first. Keep the worst status across logs so a green explore cannot
    # hide a black-screen/missing-code smoke failure.
    for name in ('smoke.log', 'health_smoke.log', 'explore.log'):
        if resolve_game_log is not None:
            path = resolve_game_log(game_dir.name, name, game_dir)
        else:
            path = game_dir / name
        text = _read(path)
        if not text:
            continue
        sources.append(name)
        result = analyze_log(text, min_prims=min_prims)
        result['source'] = name
        result['sources'] = list(sources)
        if best is None:
            best = result
            continue
        severity = {'ok': 0, 'warn': 1, 'fail': 2}
        if severity.get(result['status'], 0) > severity.get(best['status'], 0):
            best = result
        elif result['status'] == best['status'] and (result.get('primitives') or -1) > (best.get('primitives') or -1):
            best = result
    if best is not None:
        best['sources'] = sources
        return best
    return {
        'status': 'warn',
        'reasons': [],
        'warnings': ['no_explore_or_smoke_log'],
        'primitives': None,
        'frames': None,
        'missing_code': [],
        'reached_frame_limit': False,
        'source': None,
        'sources': sources,
    }


def write_health(game_dir: Path, report: dict | None = None) -> dict:
    game_dir = Path(game_dir)
    report = dict(report or evaluate_game(game_dir))
    report['game_id'] = game_dir.name
    path = game_dir / 'health.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def gate_ready(report: dict) -> None:
    """Raise if install must not be marked ready."""
    if report.get('status') == 'fail':
        detail = '; '.join(report.get('reasons') or ['health check failed'])
        raise RuntimeError(f'Install health gate failed: {detail}')
