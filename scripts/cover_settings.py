"""Library cover source settings (remote URL templates or a local folder)."""
from __future__ import annotations
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'config' / 'covers.json'

DEFAULT_2D_URL = 'https://raw.githubusercontent.com/xlenore/ps2-covers/main/covers/default/${serial}.jpg'
DEFAULT_3D_URL = 'https://raw.githubusercontent.com/xlenore/ps2-covers/main/covers/3d/${serial}.png'

KEYS = (
    'cover_source',
    'cover_prefer',
    'cover_2d_url',
    'cover_3d_url',
    'cover_local_path',
)


def defaults():
    return {
        'cover_source': 'remote',
        'cover_prefer': '3d',
        'cover_2d_url': DEFAULT_2D_URL,
        'cover_3d_url': DEFAULT_3D_URL,
        'cover_local_path': '',
    }


def _blank():
    return defaults()


def _validate_url(value, label):
    if not isinstance(value, str):
        raise ValueError(f'Invalid {label}.')
    text = value.strip()
    if not text:
        return ''
    if len(text) > 512:
        raise ValueError(f'{label} is too long.')
    if any(ch in text for ch in '\0\r\n'):
        raise ValueError(f'Invalid {label}.')
    if '${serial}' not in text:
        raise ValueError(f'{label} must include ${{serial}}.')
    parts = urlsplit(text)
    if parts.scheme != 'https' or not parts.netloc:
        raise ValueError(f'{label} must be an https URL.')
    return text


def _validate_source(value):
    if value not in ('remote', 'local'):
        raise ValueError('Cover source must be remote or local.')
    return value


def _validate_prefer(value):
    if value not in ('3d', '2d'):
        raise ValueError('Cover preference must be 3d or 2d.')
    return value


def _validate_local_path(value, *, require_exists=False):
    if not isinstance(value, str):
        raise ValueError('Invalid cover folder path.')
    text = value.strip().strip('"')
    if not text:
        return ''
    if len(text) > 512:
        raise ValueError('Cover folder path is too long.')
    if any(ch in text for ch in '\0\r\n'):
        raise ValueError('Invalid cover folder path.')
    path = Path(text)
    if not path.is_absolute():
        raise ValueError('Cover folder must be an absolute path.')
    if require_exists and not path.is_dir():
        raise ValueError('Cover folder does not exist.')
    return str(path)


def load():
    data = _blank()
    try:
        raw = json.loads(PATH.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return data
    if not isinstance(raw, dict):
        return data
    source = raw.get('cover_source', data['cover_source'])
    prefer = raw.get('cover_prefer', data['cover_prefer'])
    try:
        data['cover_source'] = _validate_source(source if isinstance(source, str) else data['cover_source'])
        data['cover_prefer'] = _validate_prefer(prefer if isinstance(prefer, str) else data['cover_prefer'])
        data['cover_2d_url'] = _validate_url(raw.get('cover_2d_url', ''), '2D cover URL') or DEFAULT_2D_URL
        data['cover_3d_url'] = _validate_url(raw.get('cover_3d_url', ''), '3D cover URL') or DEFAULT_3D_URL
        data['cover_local_path'] = _validate_local_path(raw.get('cover_local_path', '') or '')
    except ValueError:
        return _blank()
    return data


def save(updates):
    if not isinstance(updates, dict):
        raise ValueError('Invalid settings payload.')
    if not any(key in updates for key in KEYS):
        return public_view()
    current = load()
    if 'cover_source' in updates:
        current['cover_source'] = _validate_source(updates.get('cover_source'))
    if 'cover_prefer' in updates:
        current['cover_prefer'] = _validate_prefer(updates.get('cover_prefer'))
    if 'cover_2d_url' in updates:
        current['cover_2d_url'] = _validate_url(updates.get('cover_2d_url'), '2D cover URL') or DEFAULT_2D_URL
    if 'cover_3d_url' in updates:
        current['cover_3d_url'] = _validate_url(updates.get('cover_3d_url'), '3D cover URL') or DEFAULT_3D_URL
    if 'cover_local_path' in updates:
        path = _validate_local_path(updates.get('cover_local_path') or '')
        if current['cover_source'] == 'local' and path:
            _validate_local_path(path, require_exists=True)
        current['cover_local_path'] = path
    if current['cover_source'] == 'local':
        if not current['cover_local_path']:
            raise ValueError('Choose a local covers folder.')
        _validate_local_path(current['cover_local_path'], require_exists=True)
    PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = PATH.with_suffix('.tmp')
    temporary.write_text(json.dumps(current, indent=2) + '\n', encoding='utf-8')
    temporary.replace(PATH)
    return public_view(current)


def render_url(template, serial):
    text = (template or '').strip() or DEFAULT_2D_URL
    return text.replace('${serial}', serial)


def public_view(data=None):
    data = data or load()
    return {
        'cover_source': data.get('cover_source', 'remote'),
        'cover_prefer': data.get('cover_prefer', '3d'),
        'cover_2d_url': data.get('cover_2d_url', DEFAULT_2D_URL),
        'cover_3d_url': data.get('cover_3d_url', DEFAULT_3D_URL),
        'cover_local_path': data.get('cover_local_path', ''),
        'cover_defaults': defaults(),
    }
