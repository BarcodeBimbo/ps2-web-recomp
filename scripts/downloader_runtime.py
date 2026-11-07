"""Shared paths for the project's private downloader runtime."""
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def _node_major(binary):
    try:
        out = subprocess.run([binary, '-p', 'process.versions.node'], capture_output=True, text=True, timeout=10)
        if getattr(out, 'returncode', 1):
            return 0
        text = getattr(out, 'stdout', None) or '0'
        return int(str(text).strip().split('.', 1)[0] or '0')
    except (OSError, ValueError, TypeError, subprocess.SubprocessError):
        return 0


def node_executable():
    """Prefer a Node.js that can load downloader native modules (webtorrent).

    MSYS clang64 Node is fine for tooling, but WebTorrent's native addons are
    installed against the Node used for `npm ci`. Prefer a PATH/system Node 22+
    when available so torrent downloads do not crash on ABI mismatch.
    """
    managed = ROOT / 'tools/msys64/clang64/bin/node.exe'
    path_node = shutil.which('node')
    candidates = []
    if path_node:
        candidates.append(path_node)
    if managed.is_file():
        managed_s = str(managed)
        if managed_s not in candidates:
            candidates.append(managed_s)
    usable = [binary for binary in candidates if _node_major(binary) >= 22]
    return usable[0] if usable else (path_node or (str(managed) if managed.is_file() else None))


def runtime_env():
    """Build the Node worker environment.

    Captcha keys are NOT passed via process env. They travel
    browser localStorage → download request body → job JSON on stdin.
    Never read config/store.private.json for captcha secrets.
    """
    binary = node_executable()
    # Strip HTTP(S)_PROXY so CDN/browser downloads use the system VPN tunnel,
    # not an app-level proxy from Settings or the environment.
    env = {
        **os.environ,
        'PATH': str(Path(binary).parent) + os.pathsep + os.environ.get('PATH', '') if binary else os.environ.get('PATH', ''),
        'PLAYWRIGHT_BROWSERS_PATH': str(ROOT / 'tools/downloader-browsers'),
    }
    for key in (
        'CDN_HTTP_PROXY', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY',
        'http_proxy', 'https_proxy', 'all_proxy',
        'PIA_USERNAME', 'PIA_PASSWORD', 'PIA_PROXY_HOST', 'MULLVAD_ACCOUNT_NUMBER',
        'TWOCAPTCHA_API_KEY',  # never inherit or inject captcha via env
    ):
        env.pop(key, None)
    env['NO_PROXY'] = '*'
    env['no_proxy'] = '*'
    return env
