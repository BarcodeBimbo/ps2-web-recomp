"""Install the Windows build tools locally, then launch the panel."""
import hashlib
import json
import ntpath
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from setup_progress import phase, run_command, REPORT
TOOLS = ROOT / 'tools'
MSYS = TOOLS / 'msys64'
BIN = MSYS / 'clang64' / 'bin'
EMSDK = TOOLS / 'emsdk'
EM_VERSION = '6.0.11'
# Pin the emsdk bootstrap itself, not just the SDK payload it installs.
# This is the emsdk 6.0.11 release commit (immutable Git object prefix).
EMSDK_BOOTSTRAP_REVISION = 'dd8e25632640cfc1fb570c7fa4cc374e8a5e5a72'
EMSDK_BOOTSTRAP_SHA256 = 'd2b411e52e299cae24b3b17bfba33fd5f8f4dc143acc138259d09dbf0c514c27'
WGPU = ROOT / 'third_party' / 'wgpu-native'
WGPU_VERSION = 'v29.0.1.1'
CHDMAN_DIR = TOOLS / 'chdman'
CHDMAN_EXE = CHDMAN_DIR / 'chdman.exe'
# Official MAME 0.289 x64 release. SHA-256 is pinned to the Windows Package
# Manager manifest (which verifies downloaded installers before acceptance).
MAME_VERSION = '0.289'
MAME_URL = 'https://github.com/mamedev/mame/releases/download/mame0289/mame0289b_x64.exe'
MAME_SHA256 = 'a1aa7912168c9d1b05e611906bc21b8b9be3935822aead36d12a1da363150b7d'


def run(*args, **kwargs):
    return run_command(args, cwd=ROOT, timeout=1800, **kwargs)


def download(url, path):
    print('Downloading', url, flush=True)
    with urllib.request.urlopen(url, timeout=90) as source, path.open('wb') as out:
        total=0;started=last=time.monotonic()
        while chunk := source.read(1 << 20):
            total+=len(chunk)
            if total>16*1024**3 or time.monotonic()-started>1800:raise RuntimeError('Tool download exceeded its size/time limit.')
            out.write(chunk)
            if time.monotonic()-last>=5:
                print(f'  Downloaded {total/1048576:.1f} MB in {int(time.monotonic()-started)}s',flush=True);last=time.monotonic()
        print(f'  Download finished: {total/1048576:.1f} MB. Verifying/extracting next...',flush=True)


def github_release_asset(repository, tag, filename):
    request = urllib.request.Request(
        f'https://api.github.com/repos/{repository}/releases/tags/{tag}',
        headers={'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        release = json.load(response)
    return next((asset for asset in release.get('assets', []) if asset.get('name') == filename), None)


def verify_sha256(path, expected):
    if not isinstance(expected, str) or len(expected) != 64:
        raise RuntimeError('The tool release did not provide a valid SHA-256 digest.')
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual.lower() != expected.lower():
        raise RuntimeError('Downloaded tool archive checksum mismatch. Delete the partial archive and run Setup.cmd again.')


def tools_env():
    return {**os.environ, 'PATH': os.pathsep.join((str(BIN), str(Path(sys.executable).parent), os.environ['PATH']))}


def safe_extract_zip(archive, destination, *, max_members=100_000, max_uncompressed=4 * 1024 ** 3):
    """Extract an installer ZIP without permitting path traversal or links."""
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    total_size = 0
    seen = set()
    with zipfile.ZipFile(archive) as bundle:
        members = bundle.infolist()
        if len(members) > max_members:
            raise RuntimeError('Tool archive contains too many entries.')
        actual_size = 0
        for member in members:
            raw_name = member.filename.replace('\\', '/')
            windows_path = ntpath.splitdrive(raw_name)[0]
            # Normalize only trailing directory separators. Empty interior
            # components, dot segments and Windows device names are rejected.
            normalized = raw_name.rstrip('/')
            parts = normalized.split('/') if normalized else []
            invalid_chars = set('<>"|?*')
            reserved_devices = {'CON', 'PRN', 'AUX', 'NUL', 'CLOCK$', 'CONIN$', 'CONOUT$'} | {
                f'{prefix}{number}' for prefix in ('COM', 'LPT') for number in range(1, 10)
            }
            unsafe_component = any(
                part in ('', '.', '..') or ':' in part or
                any(ord(ch) < 32 or ch in invalid_chars for ch in part) or
                part.endswith((' ', '.')) or part.split('.', 1)[0].upper() in reserved_devices
                for part in parts
            )
            if (not parts or raw_name.startswith('/') or windows_path or unsafe_component or '\x00' in raw_name):
                raise RuntimeError('Tool archive contains an unsafe path: ' + member.filename[:160])
            mode = member.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise RuntimeError('Tool archive contains a symbolic link: ' + member.filename[:160])
            total_size += member.file_size
            if member.file_size < 0 or total_size > max_uncompressed:
                raise RuntimeError('Tool archive exceeds the uncompressed size limit.')
            relative = Path(*parts)
            output = (destination / relative).resolve()
            if not output.is_relative_to(destination):
                raise RuntimeError('Tool archive path escapes its install folder.')
            key = str(output).casefold()
            if key in seen:
                raise RuntimeError('Tool archive contains duplicate destination paths.')
            seen.add(key)
            if member.is_dir():
                output.mkdir(parents=True, exist_ok=True)
                continue
            output.parent.mkdir(parents=True, exist_ok=True)
            written = 0
            with bundle.open(member, 'r') as source, output.open('wb') as target:
                while True:
                    chunk = source.read(1 << 20)
                    if not chunk:
                        break
                    written += len(chunk)
                    actual_size += len(chunk)
                    if written > member.file_size or actual_size > max_uncompressed:
                        raise RuntimeError('Tool archive expands beyond its declared uncompressed size limit.')
                    target.write(chunk)
            if written != member.file_size:
                raise RuntimeError('Tool archive contains a truncated or inconsistent entry: ' + member.filename[:160])


def install_msys(stage):
    bash = MSYS / 'usr/bin/bash.exe'
    if not bash.is_file():
        release_url = 'https://api.github.com/repos/msys2/msys2-installer/releases/tags/2026-09-27'
        with urllib.request.urlopen(release_url, timeout=45) as response:
            release = json.load(response)
        asset = next((item for item in release['assets']
                      if item['name'] == 'msys2-base-x86_64-20260927.tar.xz'), None)
        if not asset or not (asset.get('digest') or '').startswith('sha256:'):
            raise RuntimeError('Could not find the verified MSYS2 release archive.')
        archive = stage / 'msys.tar.xz'
        download(asset['browser_download_url'], archive)
        with archive.open('rb') as source:
            digest = hashlib.sha256()
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
            digest = digest.hexdigest()
        if f'sha256:{digest}' != asset['digest']:
            raise RuntimeError('MSYS2 download checksum mismatch. Run Setup.cmd again.')
        run('tar.exe', '-xf', archive, '-C', stage)
        (stage / 'msys64').rename(MSYS)

    env = {**os.environ, 'MSYSTEM': 'CLANG64', 'CHERE_INVOKING': '1'}
    packages = ('clang', 'cmake', 'ninja', 'SDL2', '7zip', 'python', 'openssl')
    stamp = MSYS / '.ps2-tools-20261105-phone'
    if not stamp.exists():
        # A core update can close its own MSYS processes. Start a fresh shell
        # for the next pass, which must finish successfully.

        try: run(bash, '-lc', 'pacman -Syu --noconfirm', env=env)
        except subprocess.CalledProcessError: pass
        run(bash, '-lc', 'pacman -Syu --noconfirm', env=env)
        names = ' '.join('mingw-w64-clang-x86_64-' + item for item in packages)
        run(bash, '-lc', 'pacman -S --needed --noconfirm ' + names, env=env)
        stamp.touch()


def install_emsdk(stage):
    if not (EMSDK / 'emsdk.py').is_file():
        archive = stage / 'emsdk.zip'
        url = f'https://codeload.github.com/emscripten-core/emsdk/zip/{EMSDK_BOOTSTRAP_REVISION}'
        download(url, archive)
        verify_sha256(archive, EMSDK_BOOTSTRAP_SHA256)
        safe_extract_zip(archive, stage)
        extracted = stage / f'emsdk-{EMSDK_BOOTSTRAP_REVISION}'
        if not (extracted / 'emsdk.py').is_file():
            raise RuntimeError('Pinned Emscripten SDK bootstrap archive is incomplete or has an unexpected layout.')
        EMSDK.parent.mkdir(parents=True, exist_ok=True)
        if EMSDK.exists():
            shutil.rmtree(EMSDK)
        extracted.rename(EMSDK)
    stamp = EMSDK / f'.ps2-{EM_VERSION}'
    if not stamp.exists():
        run(BIN / 'python.exe', EMSDK / 'emsdk.py', 'install', EM_VERSION, env=tools_env())
        run(BIN / 'python.exe', EMSDK / 'emsdk.py', 'activate', EM_VERSION, env=tools_env())
        stamp.touch()


def install_chdman(stage):
    # Install the official MAME CHD utility into the project tools folder.
    override = os.environ.get('CHDMAN')
    if CHDMAN_EXE.is_file() or (override and Path(override).is_file()) or shutil.which('chdman'):
        return

    archive = stage / f'mame{MAME_VERSION.replace(".", "")}_x64.exe'
    download(MAME_URL, archive)
    verify_sha256(archive, MAME_SHA256)

    # MAME's Windows binary is a 7-Zip self-extracting package. Its documented
    # -y and -o switches install silently into the supplied folder.
    CHDMAN_DIR.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([str(archive), '-y', f'-o{CHDMAN_DIR}'],
                            cwd=ROOT, capture_output=True, text=True, errors='replace', timeout=900)
    if result.returncode != 0 or not CHDMAN_EXE.is_file():
        detail = (result.stderr or result.stdout or '').strip()[-1000:]
        raise RuntimeError('MAME CHD utility installation did not produce chdman.exe. ' + detail)


def install_wgpu(stage):
    def installed():
        return (any(WGPU.glob('*/wgpu_native.dll'))
                and (WGPU / 'lib/libwgpu_native.dll.a').is_file()
                and (WGPU / 'include/webgpu/wgpu.h').is_file())

    if installed():
        return
    archive = stage / 'wgpu.zip'
    asset_name = 'wgpu-windows-x86_64-gnu-release.zip'
    asset = github_release_asset('gfx-rs/wgpu-native', WGPU_VERSION, asset_name)
    digest = asset.get('digest', '') if asset else ''
    if not digest.startswith('sha256:'):
        raise RuntimeError('The pinned wgpu-native release has no SHA-256 digest for its Windows archive.')
    download(asset['browser_download_url'], archive)
    verify_sha256(archive, digest.removeprefix('sha256:'))
    safe_extract_zip(archive, WGPU)
    if not installed():
        raise RuntimeError('wgpu-native archive is missing Windows development files.')


def install_downloader():
    """Install Node (via MSYS), npm deps (webtorrent/phantomwright), and Chromium."""
    import downloader_runtime as runtime
    folder = ROOT / 'downloader'
    lockfile = folder / 'package-lock.json'
    stamp = folder / '.installed-dependencies'
    if not (folder / 'package.json').is_file() or not lockfile.is_file():
        raise RuntimeError('Store downloader package files are missing.')

    bash = MSYS / 'usr/bin/bash.exe'
    node = BIN / 'node.exe'
    npm_cli = MSYS / 'clang64/lib/node_modules/npm/bin/npm-cli.js'
    if not node.is_file() or not npm_cli.is_file():
        env = {**os.environ, 'MSYSTEM': 'CLANG64', 'CHERE_INVOKING': '1'}
        run(bash, '-lc', 'pacman -S --needed --noconfirm mingw-w64-clang-x86_64-nodejs', env=env)
        if not node.is_file() or not npm_cli.is_file():
            raise RuntimeError('Node.js was not installed into the managed MSYS tools.')

    digest = hashlib.sha256(lockfile.read_bytes()).hexdigest()
    env = runtime.runtime_env()
    needs_npm = stamp.read_text(encoding='utf-8').strip() != digest if stamp.is_file() else True
    if needs_npm:
        run_command([node, npm_cli, 'ci', '--omit=dev'], cwd=folder, env=env, timeout=1800)
        driver = folder / 'node_modules/phantomwright-driver/cli.js'
        if not driver.is_file():
            raise RuntimeError('Downloader dependencies installed without phantomwright-driver.')

    check = folder / 'check-browser.mjs'
    browser_ok = subprocess.run([str(node), str(check)], cwd=folder, env=env, capture_output=True).returncode == 0
    if not browser_ok:
        driver = folder / 'node_modules/phantomwright-driver/cli.js'
        if not driver.is_file():
            raise RuntimeError('Downloader browser installer is missing. Re-run Setup.cmd.')
        run_command([node, driver, 'install', 'chromium'], cwd=folder, env=env, timeout=1800)
        if subprocess.run([str(node), str(check)], cwd=folder, env=env, capture_output=True).returncode != 0:
            raise RuntimeError('Chromium for Store downloads did not install correctly.')

    if needs_npm:
        stamp.write_text(digest, encoding='utf-8')


def main():
    import msvcrt
    TOOLS.mkdir(exist_ok=True)
    with (TOOLS / 'setup.lock').open('a+b') as lock:
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            raise RuntimeError('Setup is already running. Use its existing window.') from None
        with tempfile.TemporaryDirectory(dir=TOOLS) as temp:
            stage = Path(temp)
            phase('1/5 Native build tools', lambda: install_msys(stage))
            phase('2/5 Emscripten SDK', lambda: install_emsdk(stage))
            phase('3/5 WebGPU libraries', lambda: install_wgpu(stage))
            try:
                phase('4/5 CHD tool', lambda: install_chdman(stage))
            except (OSError, RuntimeError, subprocess.SubprocessError, TimeoutError) as error:
                # Non-CHD imports remain usable even if MAME's optional media
                # utility cannot be installed on this CPU or network.
                print('CHD support was not installed: ' + str(error), flush=True)
                print('You can still use ISO/BIN/CUE images, or set CHDMAN to a compatible chdman.exe.', flush=True)
            try:
                phase('5/5 Store downloader', install_downloader)
            except (OSError, RuntimeError, subprocess.SubprocessError, TimeoutError) as error:
                print('Store downloader was not fully installed: ' + str(error), flush=True)
                print('Local Add game still works. Re-run Setup.cmd for torrent/web downloads.', flush=True)
    print('\nSETUP '+('FINISHED WITH WARNINGS' if any(item['status']=='failed' for item in REPORT) else 'COMPLETE')+'. Starting the desktop library and automatic LAN mobile service.', flush=True)
    print('Setup report: tools/setup-report.json | Detailed setup log: logs/tools/setup.log', flush=True)
    from panel import main as panel_main
    panel_main(open_browser=True)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        sys.exit(f'Setup failed: {error}')
