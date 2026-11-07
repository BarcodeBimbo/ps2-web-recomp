"""Private Store settings kept out of git."""
from __future__ import annotations
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'config' / 'store.private.json'

KEYS = (
    'twocaptcha_api_key',
)

VPN_NAME_RE = re.compile(
    r'mullvad|pia|private\s*internet\s*access|wintun|wireguard|openvpn|nordlynx|'
    r'surfshark|proton|expressvpn|tunnelbear|nordvpn|cyberghost|ipvanish|'
    r'cloudflare.?warp|\bwarp\b|tailscale|zerotier|hamachi|tap-windows|'
    r'tap[- ]?adapter|forticlient|anyconnect|globalprotect|pulse\s*secure|'
    r'\bvpn\b|virtual\s*private',
    re.I,
)


def _blank():
    return {key: '' for key in KEYS}


def load():
    data = _blank()
    try:
        raw = json.loads(PATH.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return data
    if not isinstance(raw, dict):
        return data
    for key in KEYS:
        value = raw.get(key, '')
        data[key] = value.strip() if isinstance(value, str) else ''
    return data


def save(updates):
    if not isinstance(updates, dict):
        raise ValueError('Invalid settings payload.')
    current = load()
    for key in KEYS:
        if key not in updates:
            continue
        value = updates.get(key)
        if value is None:
            continue
        if not isinstance(value, str):
            raise ValueError(f'Invalid {key}.')
        if len(value) > 512:
            raise ValueError(f'{key} is too long.')
        if any(ch in value for ch in '\0\r\n'):
            raise ValueError(f'Invalid {key}.')
        current[key] = value.strip()
    PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = PATH.with_suffix('.tmp')
    temporary.write_text(json.dumps(current, indent=2) + '\n', encoding='utf-8')
    temporary.replace(PATH)
    return public_view(current)


def detect_vpn():
    """Best-effort: is a system VPN adapter up? Downloads use that tunnel automatically."""
    if os.name != 'nt':
        return {
            'connected': False,
            'name': '',
            'detail': 'Connect any system VPN before downloading so CDN requests use a fresh IP.',
        }
    try:
        out = subprocess.check_output(
            [
                'powershell', '-NoProfile', '-Command',
                "Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | "
                "Select-Object -ExpandProperty InterfaceDescription",
            ],
            text=True, timeout=12, stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return {
            'connected': False,
            'name': '',
            'detail': 'Could not read network adapters. Connect your VPN app, then retry.',
        }
    matches = []
    for line in out.splitlines():
        name = line.strip()
        if name and VPN_NAME_RE.search(name):
            matches.append(name)
    if matches:
        label = matches[0]
        return {
            'connected': True,
            'name': label[:120],
            'detail': f'Connected — {label[:80]}. Store downloads use this tunnel.',
        }
    return {
        'connected': False,
        'name': '',
        'detail': 'No VPN adapter detected. Connect any VPN in its app so CDN downloads use a fresh IP.',
    }


def public_view(data=None):
    data = data or load()
    vpn = detect_vpn()
    return {
        'twocaptcha_api_key': data.get('twocaptcha_api_key', ''),
        'has_twocaptcha': bool(data.get('twocaptcha_api_key')),
        'vpn_connected': bool(vpn.get('connected')),
        'vpn_name': vpn.get('name') or '',
        'vpn_detail': vpn.get('detail') or '',
    }
