"""Dedicated log tree under the repo root.

Override with PS2_LOGS (absolute or repo-relative). Default: <repo>/logs

Layout:
  logs/                      run transcripts (*.log, *.out)
  logs/games/<gid>/          per-game build/explore/smoke/trace logs
  logs/frames/<name>/        frame dumps (--frames-dir)
  logs/ram/<name>.ram        RAM dumps (PS2_DUMP)
  logs/tools/                setup and tooling run logs
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def logs_root() -> Path:
    override = os.environ.get('PS2_LOGS', '').strip()
    if override:
        path = Path(override)
        return path if path.is_absolute() else (ROOT / path)
    return ROOT / 'logs'


def ensure_logs_tree() -> Path:
    root = logs_root()
    for sub in ('games', 'frames', 'ram', 'tools'):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


def game_logs_dir(game_id: str) -> Path:
    path = logs_root() / 'games' / game_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def game_log(game_id: str, name: str) -> Path:
    """Path for a per-game log file (e.g. build.log, explore.log)."""
    if not name.endswith('.log') and not name.endswith('.txt'):
        name = f'{name}.log'
    return game_logs_dir(game_id) / name


def resolve_game_log(game_id: str, name: str, game_dir: Path | None = None) -> Path | None:
    """Prefer logs/games/<id>/, then legacy games/<id>/ for reads."""
    if not name.endswith('.log') and not name.endswith('.txt'):
        name = f'{name}.log'
    preferred = logs_root() / 'games' / game_id / name
    if preferred.is_file():
        return preferred
    if game_dir is not None:
        legacy = Path(game_dir) / name
        if legacy.is_file():
            return legacy
    if preferred.parent.is_dir() or game_dir is None:
        return preferred
    return Path(game_dir) / name


def frames_dir(name: str) -> Path:
    path = logs_root() / 'frames' / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def ram_path(name: str) -> Path:
    ensure_logs_tree()
    if not name.endswith('.ram'):
        name = f'{name}.ram'
    return logs_root() / 'ram' / name


def tools_log(name: str) -> Path:
    ensure_logs_tree()
    if not name.endswith('.log'):
        name = f'{name}.log'
    return logs_root() / 'tools' / name
