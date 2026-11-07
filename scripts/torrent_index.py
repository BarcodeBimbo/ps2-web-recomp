"""Searchable index over the bundled USA PS2 torrent collection."""
from __future__ import annotations
import json
import re
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / 'torrents' / 'ps2-usa-collection.index.json'
TORRENT_PATH = ROOT / 'torrents' / 'ps2-usa-collection.torrent'
PAGE_SIZE = 24
LOCK = threading.RLock()
_CACHE = None


def _load():
    global _CACHE
    with LOCK:
        if _CACHE is not None:
            return _CACHE
        if not INDEX_PATH.is_file() or not TORRENT_PATH.is_file():
            raise ValueError('Torrent collection is missing. Place the USA collection under torrents/.')
        data = json.loads(INDEX_PATH.read_text(encoding='utf-8'))
        files = data.get('files') or []
        if not isinstance(files, list) or not files:
            raise ValueError('Torrent index is empty or invalid.')
        _CACHE = {
            'name': data.get('name') or 'PS2 USA Collection',
            'info_hash': data.get('info_hash') or '',
            'torrent': str(TORRENT_PATH),
            'files': files,
        }
        return _CACHE


def reload():
    global _CACHE
    with LOCK:
        _CACHE = None
    return _load()


def _title_from_name(name: str) -> str:
    stem = Path(name).stem
    stem = re.sub(r'\s*\((?:USA|US|U)\)\s*', ' ', stem, flags=re.I)
    stem = re.sub(r'\s*\[[^\]]*\]\s*', ' ', stem)
    return re.sub(r'\s+', ' ', stem).strip() or name


def _format_size(size: int) -> str:
    if size >= 1024 ** 3:
        return f'{size / 1024 ** 3:.2f} G'
    if size >= 1024 ** 2:
        return f'{size / 1024 ** 2:.1f} M'
    return f'{max(1, size // 1024)} K'


def catalog(query='', page=1):
    if not isinstance(query, str) or len(query) > 120:
        raise ValueError('Invalid catalog request.')
    if not isinstance(page, int) or page < 1 or page > 500:
        raise ValueError('Invalid catalog request.')
    data = _load()
    needle = query.strip().lower()
    matches = []
    for index, item in enumerate(data['files']):
        name = item.get('name') or ''
        path = item.get('path') or name
        size = int(item.get('size') or 0)
        title = _title_from_name(name)
        hay = f'{title} {name} {path}'.lower()
        if needle and needle not in hay:
            continue
        matches.append({
            'title': title[:120],
            'url': f"torrent:{index}",
            'poster': '',
            'downloads': '',
            'size': _format_size(size),
            'source': 'torrent',
            'file_index': index,
            'path': path,
            'bytes': size,
        })
    pages = max(1, (len(matches) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(page, pages)
    start = (page - 1) * PAGE_SIZE
    return {
        'games': matches[start:start + PAGE_SIZE],
        'page': page,
        'pages': pages,
        'query': query.strip(),
        'source': 'torrent',
        'collection': data['name'],
        'total': len(matches),
    }


def resolve_entry(token: str):
    if not isinstance(token, str) or not token.startswith('torrent:'):
        raise ValueError('Invalid torrent selection.')
    try:
        index = int(token.split(':', 1)[1])
    except ValueError as error:
        raise ValueError('Invalid torrent selection.') from error
    data = _load()
    if index < 0 or index >= len(data['files']):
        raise ValueError('Torrent file is out of range.')
    item = data['files'][index]
    return {
        'torrent': data['torrent'],
        'info_hash': data['info_hash'],
        'file_index': index,
        'path': item.get('path') or item.get('name'),
        'name': item.get('name') or item.get('path'),
        'size': int(item.get('size') or 0),
        'title': _title_from_name(item.get('name') or ''),
    }
