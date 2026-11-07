"""Store settings helpers. Captcha keys are browser-localStorage only — never persisted here."""
from __future__ import annotations
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'config' / 'store.private.json'

# No server-side secrets. Legacy captcha keys in store.private.json are scrubbed.
KEYS = ()

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


def scrub_private_file():
    """Remove legacy captcha secrets from disk; delete the file if nothing remains."""
    if not PATH.is_file():
        return
    try:
        raw = json.loads(PATH.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        try:
            PATH.unlink(missing_ok=True)
        except OSError:
            pass
        return
    if not isinstance(raw, dict):
        try:
            PATH.unlink(missing_ok=True)
        except OSError:
            pass
        return
    raw.pop('twocaptcha_api_key', None)
    remaining = {key: value for key, value in raw.items() if value not in ('', None, {}, [])}
    try:
        if not remaining:
            PATH.unlink(missing_ok=True)
        else:
            temporary = PATH.with_suffix('.tmp')
            temporary.write_text(json.dumps(remaining, indent=2) + '\n', encoding='utf-8')
            temporary.replace(PATH)
    except OSError:
        pass


def load():
    scrub_private_file()
    return _blank()


def save(updates):
    if not isinstance(updates, dict):
        raise ValueError('Invalid settings payload.')
    # Ignore any captcha field from the client — browser localStorage owns that secret.
    scrub_private_file()
    return public_view()


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
    del data  # captcha is not server-stored
    scrub_private_file()
    vpn = detect_vpn()
    return {
        # Intentionally empty — the panel keeps the key in localStorage only.
        'twocaptcha_api_key': '',
        'has_twocaptcha': False,
        'twocaptcha_storage': 'localStorage',
        'vpn_connected': bool(vpn.get('connected')),
        'vpn_name': vpn.get('name') or '',
        'vpn_detail': vpn.get('detail') or '',
    }
