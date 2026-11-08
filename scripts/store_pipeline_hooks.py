"""Additive store install hooks: manifest stub, pipeline logging, optional verify gates.

``PS2_STRICT_VERIFY=1`` tightens ``install_health`` gating (warn/fail blocks ready).

``PS2_INLINE_VERIFY=1`` runs a short ``autonomous_verify.py`` smoke before ``ready``
on full installs (default off — smoke is minutes per title). Frame count via
``PS2_INLINE_VERIFY_FRAMES`` (default 200). Nightly / CLI can set both envs.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPELINE_LOG = ROOT / 'logs' / 'autonomous-pipeline'
MANIFEST_NAME = 'install_manifest.json'
SCHEMA = 1
DEFAULT_INLINE_FRAMES = 200


def strict_verify_enabled() -> bool:
    return os.environ.get('PS2_STRICT_VERIFY', '').strip().lower() in ('1', 'true', 'yes', 'on')


def inline_verify_enabled() -> bool:
    return os.environ.get('PS2_INLINE_VERIFY', '').strip().lower() in ('1', 'true', 'yes', 'on')


def inline_verify_frames() -> int:
    raw = os.environ.get('PS2_INLINE_VERIFY_FRAMES', str(DEFAULT_INLINE_FRAMES)).strip()
    try:
        return max(30, int(raw))
    except ValueError:
        return DEFAULT_INLINE_FRAMES


def _manifest_path(game_dir: Path) -> Path:
    return Path(game_dir) / MANIFEST_NAME


def _read_manifest(game_dir: Path) -> dict:
    path = _manifest_path(game_dir)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_manifest(game_dir: Path, payload: dict) -> dict:
    game_dir = Path(game_dir)
    path = _manifest_path(game_dir)
    path.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    return payload


def source_digest(source: Path, *, max_bytes: int | None = None) -> dict:
    source = Path(source)
    size = source.stat().st_size
    if max_bytes is not None and size > max_bytes:
        return {
            'path_basename': source.name,
            'bytes': size,
            'sha256': None,
            'sha256_skipped': True,
            'reason': f'exceeds_cap_{max_bytes}',
        }
    digest = hashlib.sha256()
    with source.open('rb') as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return {
        'path_basename': source.name,
        'bytes': size,
        'sha256': digest.hexdigest(),
    }


def begin_install_manifest(
    game_dir: Path,
    *,
    game_id: str,
    title: str,
    source: Path,
    download_job_id: str | None = None,
) -> dict:
    now = time.time()
    record = {
        'schema': SCHEMA,
        'game_id': game_id,
        'title': title,
        'download_job_id': download_job_id,
        'source': source_digest(source),
        'timestamps': {
            'import_queued_at': now,
            'build_completed_at': None,
        },
        'pipeline': {
            'autonomous_verify_inline': False,
            'note': 'Set PS2_INLINE_VERIFY=1 for post-build smoke; else CLI/nightly.',
        },
    }
    return _write_manifest(game_dir, record)


def run_inline_autonomous_verify(game_id: str, *, frames: int | None = None) -> dict:
    """Invoke ``autonomous_verify.py --game <id> --json`` and return the first result row."""
    frames = frames if frames is not None else inline_verify_frames()
    script = ROOT / 'scripts' / 'autonomous_verify.py'
    if not script.is_file():
        raise RuntimeError('Inline verify failed: scripts/autonomous_verify.py missing')
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            '--game',
            game_id,
            '--frames',
            str(frames),
            '--json',
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=max(120, frames * 3),
    )
    raw = (proc.stdout or '').strip() or (proc.stderr or '').strip()
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f'Inline verify failed: non-JSON output ({raw[-400:] or proc.returncode})'
        ) from exc
    results = payload.get('results') if isinstance(payload, dict) else None
    if isinstance(results, list) and results:
        row = results[0] if isinstance(results[0], dict) else {'status': 'error', 'raw': results[0]}
    elif isinstance(payload, dict) and payload.get('status'):
        row = payload
    else:
        row = {'status': 'error', 'error': f'empty verify payload exit={proc.returncode}', 'raw': raw[-400:]}
    row.setdefault('exit_code', proc.returncode)
    row['inline_frames'] = frames
    return row


def gate_inline_verify(game_id: str, *, full_install: bool) -> dict | None:
    """Optional env gate: full installs must pass autonomous_verify smoke before ready."""
    if not inline_verify_enabled() or not full_install:
        return None
    result = run_inline_autonomous_verify(game_id)
    status = (result.get('status') or '').lower()
    if status in ('pass', 'skipped'):
        return result
    detail = result.get('error') or result.get('reason') or status or 'verify failed'
    health = result.get('health') or {}
    if isinstance(health, dict) and health.get('reasons'):
        detail = f"{detail}; {'; '.join(health.get('reasons') or [])}"
    raise RuntimeError(f'Inline autonomous_verify failed: {detail}')


def finalize_post_build(
    game_id: str,
    health: dict,
    *,
    full_install: bool,
) -> dict:
    game_dir = ROOT / 'games' / game_id
    manifest = _read_manifest(game_dir)
    if not manifest:
        manifest = {
            'schema': SCHEMA,
            'game_id': game_id,
            'timestamps': {},
            'pipeline': {'autonomous_verify_inline': False},
        }
    manifest.setdefault('timestamps', {})
    manifest['timestamps']['build_completed_at'] = time.time()
    manifest['health_status'] = health.get('status')
    manifest['health_reasons'] = health.get('reasons') or []
    manifest['health_warnings'] = health.get('warnings') or []
    manifest['strict_verify'] = strict_verify_enabled()
    pipeline = manifest.setdefault('pipeline', {})
    pipeline['autonomous_verify_inline'] = False
    gate_strict_ready(health, full_install=full_install)
    inline_result = None
    try:
        inline_result = gate_inline_verify(game_id, full_install=full_install)
    except RuntimeError as exc:
        pipeline['autonomous_verify_inline'] = True
        pipeline['autonomous_verify_status'] = 'fail'
        pipeline['autonomous_verify_error'] = str(exc)[:500]
        _write_manifest(game_dir, manifest)
        log_pipeline_event(
            'inline_verify',
            game_id=game_id,
            status='fail',
            error=str(exc)[:240],
            full_install=full_install,
        )
        raise
    if inline_result is not None:
        pipeline['autonomous_verify_inline'] = True
        pipeline['autonomous_verify_status'] = inline_result.get('status')
        pipeline['autonomous_verify_log'] = inline_result.get('log')
        pipeline['autonomous_verify_frames'] = inline_result.get('inline_frames')
        manifest['timestamps']['inline_verify_at'] = time.time()
        log_pipeline_event(
            'inline_verify',
            game_id=game_id,
            status=inline_result.get('status'),
            log=inline_result.get('log'),
            frames=inline_result.get('inline_frames'),
            full_install=full_install,
        )
    _write_manifest(game_dir, manifest)
    log_pipeline_event(
        'post_build',
        game_id=game_id,
        health=health.get('status'),
        strict=manifest['strict_verify'],
        inline_verify=bool(pipeline.get('autonomous_verify_inline')),
        full_install=full_install,
    )
    return manifest


def gate_strict_ready(health: dict, *, full_install: bool) -> None:
    """Optional env tighten: fail installs that would only warn under default gating."""
    if not strict_verify_enabled() or not full_install:
        return
    from install_health import gate_ready

    gate_ready(health)
    if health.get('status') == 'warn':
        detail = '; '.join(health.get('warnings') or ['health warnings under strict verify'])
        raise RuntimeError(f'Strict verify failed: {detail}')


def log_pipeline_event(kind: str, **fields) -> None:
    PIPELINE_LOG.mkdir(parents=True, exist_ok=True)
    path = PIPELINE_LOG / 'store-pipeline-events.jsonl'
    row = {'ts': time.time(), 'kind': kind, **fields}
    try:
        with path.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(row, ensure_ascii=True) + '\n')
    except OSError:
        pass


def note_post_download(game_id: str, download_job_id: str | None, title: str) -> None:
    log_pipeline_event(
        'post_download',
        game_id=game_id,
        download_job_id=download_job_id,
        title=title[:120],
    )
