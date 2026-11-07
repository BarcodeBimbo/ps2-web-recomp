"""Additive store install hooks: manifest stub, pipeline logging, optional strict verify.

Full ``autonomous_verify.py`` smoke is intentionally not run inline on the hot path
(build would block minutes per title). Use ``PS2_STRICT_VERIFY=1`` to tighten
``install_health`` gating; run ``python scripts/autonomous_verify.py`` or nightly
jobs for library smoke + matrix scoring.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPELINE_LOG = ROOT / 'logs' / 'autonomous-pipeline'
MANIFEST_NAME = 'install_manifest.json'
SCHEMA = 1


def strict_verify_enabled() -> bool:
    return os.environ.get('PS2_STRICT_VERIFY', '').strip().lower() in ('1', 'true', 'yes', 'on')


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
            'note': 'Run scripts/autonomous_verify.py or nightly pipeline for smoke/matrix.',
        },
    }
    return _write_manifest(game_dir, record)


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
    _write_manifest(game_dir, manifest)
    gate_strict_ready(health, full_install=full_install)
    log_pipeline_event(
        'post_build',
        game_id=game_id,
        health=health.get('status'),
        strict=manifest['strict_verify'],
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
