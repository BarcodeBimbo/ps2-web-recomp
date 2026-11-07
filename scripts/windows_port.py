"""Windows port pipeline. All build and game processes run as Win32 programs."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

from disc import Image, MAX_DISC_SIZE, modules, to_iso
from windows import windows
from windows_setup import BIN, EMSDK, ROOT, WGPU, tools_env

from archives import ARCHIVE_EXTENSIONS
from malware_guard import assert_safe_import
from log_paths import game_log, game_logs_dir
EXTENSIONS = {'.iso', '.bin', '.cue', '.img', '.chd', '.rom'} | ARCHIVE_EXTENSIONS
try:
    _requested_jobs = int(os.getenv('PS2_BUILD_JOBS', '1'))
except ValueError:
    _requested_jobs = 1
JOBS = max(1, min(_requested_jobs, os.cpu_count() or 1))


def relative(path):
    return path.relative_to(ROOT).as_posix()


def ensure_web_build_readable(folder):
    """Reset ACLs on published player assets so the non-elevated panel can read them.

    Elevated Emscripten/link steps on Windows sometimes emit ps2web.js with an
    explicit Administrators/SYSTEM/OWNER-only DACL (no Users RX). The panel then
    can stat the file for Content-Length but fails open(), which used to yield
    ERR_CONTENT_LENGTH_MISMATCH after the GPU-compat prefix.
    """
    if os.name != 'nt':
        return
    for name in ('ps2web.html', 'ps2web.js', 'ps2web.wasm', 'ps2web.data', 'boot.txt', 'build.json'):
        path = folder / name
        if not path.is_file():
            continue
        try:
            subprocess.run(['icacls', str(path), '/reset'], check=False, capture_output=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            pass


def cmake(folder, *options, target, env):
    subprocess.run([BIN / 'cmake.exe', '-S', '.', '-B', relative(folder),
                    '-G', 'Ninja', '-DCMAKE_BUILD_TYPE=Release',
                    f'-DCMAKE_MAKE_PROGRAM={BIN / "ninja.exe"}', *options],
                   check=True, cwd=ROOT, env=env, timeout=180)
    subprocess.run([BIN / 'cmake.exe', '--build', relative(folder),
                    '--parallel', str(JOBS), '--target', target],
                   check=True, cwd=ROOT, env=env, timeout=7200)


def native_env():
    env = tools_env()
    dll = next(WGPU.glob('*/wgpu_native.dll'), None)
    if dll is None:
        raise FileNotFoundError('wgpu-native DLL is missing. Run Setup.cmd again.')
    env['PATH'] = str(dll.parent) + os.pathsep + env['PATH']
    return env


def install_disc(source, target, password=None):
    source = Path(source)
    assert_safe_import(source)
    ext = source.suffix.lower()
    if ext == '.iso':
        # A managed image remains available even when the original drive is removed.
        size = source.stat().st_size
        if size <= 0 or size > MAX_DISC_SIZE:
            raise ValueError('The ISO is empty or exceeds the 16 GiB disc-image limit.')
        if source.resolve() != target.resolve(): shutil.copyfile(source, target)
    else:
        # Passwords are supplied only for this invocation and are never persisted.
        to_iso(str(source), target, password)
    # Re-check the managed copy so a swapped/polyglot payload cannot be staged.
    assert_safe_import(target, scan=True)


def prepared_game(game_id):
    game = ROOT / 'games' / game_id
    web = ROOT / 'build' / f'web-{game_id}'
    elf = game / 'core.elf'
    if not elf.is_file():
        elf = game / 'disc' / 'boot.elf'
    if all(p.is_file() for p in (elf, game / 'disc.iso', web / 'boot.txt')):
        return elf
    return None


def refresh_translation(game_id, elf, env):
    # Existing generated files contain literal musttail calls. Regenerate them
    # with the current compiler before selecting the compatibility runtime.
    slot=env.get('PS2_BUILD_SLOT','0')
    if slot not in ('0','1'):raise ValueError('Invalid build slot.')
    tools=ROOT/'build'/('tools-windows' if slot=='0' else 'tools-windows-'+slot)
    cmake(tools,f'-DCMAKE_CXX_COMPILER={BIN / "clang++.exe"}',target='eerecomp',env=env)
    game=ROOT/'games'/game_id
    entries=game/'entries.txt';entries.touch(exist_ok=True)
    command=[tools/'eerecomp.exe',relative(elf),'--entries',relative(entries)]
    for option,name in [('--modules','modules'),('--overlays','overlays')]:
        if (game/name).is_dir():command.extend([option,relative(game/name)])
    command.extend(['--unit-bits','12','--out',relative(ROOT/'generated'/game_id)])
    subprocess.run(command,check=True,cwd=ROOT,env=env,timeout=600)


def build_web(game_id):
    elf = prepared_game(game_id)
    if elf is None:
        raise ValueError('The extracted disc or boot data is incomplete. Add the original disc again.')
    published = ROOT / 'build' / f'web-{game_id}'
    web = ROOT / 'build' / f'web-{game_id}-next'
    if web.exists():
        # Windows/cmake trees can leave read-only generated objects; plain rmtree fails WinError 145.
        def _rmtree_onerror(func, path, exc):
            import stat
            if not os.access(path, os.W_OK):
                os.chmod(path, stat.S_IWUSR)
            func(path)
        shutil.rmtree(web, onerror=_rmtree_onerror)
    web.mkdir(parents=True)
    shutil.copyfile(published / 'boot.txt', web / 'boot.txt')
    generated = ROOT / 'generated' / game_id
    web_env = tools_env()
    async_mode=os.getenv('PS2_WEB_ASYNC_MODE','asyncify').lower()
    if async_mode not in ('asyncify','jspi'):raise ValueError('Invalid browser async runtime.')
    refresh_translation(game_id,elf,web_env)
    web_env.update(EMSDK=str(EMSDK), EM_CONFIG=str(EMSDK / '.emscripten'))
    toolchain = EMSDK / 'upstream/emscripten/cmake/Modules/Platform/Emscripten.cmake'
    cmake(web, f'-DCMAKE_TOOLCHAIN_FILE={toolchain}', f'-DPS2_GENERATED={generated}',
          f'-DPS2_WEB_ELF={elf}', f'-DPS2_WEB_BOOT_FILE={web / "boot.txt"}',
          f'-DPS2_WEB_ASYNC_MODE={async_mode}',
          target='ps2web', env=web_env)
    missing = [name for name in ('ps2web.html', 'ps2web.js', 'ps2web.wasm', 'ps2web.data')
               if not (web / name).is_file()]
    if missing:
        raise RuntimeError('Missing browser build files: ' + ', '.join(missing))
    import json, secrets
    (web / 'build.json').write_text(json.dumps({'id': secrets.token_hex(12),'async_mode':async_mode,'trampoline':async_mode=='asyncify'}), encoding='utf-8')
    backup = published.with_name(published.name + '-previous')
    if backup.exists(): shutil.rmtree(backup)
    published.rename(backup)
    try:
        web.rename(published)
    except BaseException:
        backup.rename(published)
        raise
    shutil.rmtree(backup)
    ensure_web_build_readable(published)


def port(game_id, source, frames=3600, rounds=8, password=None):
    game = ROOT / 'games' / game_id
    generated = ROOT / 'generated' / game_id
    native = ROOT / 'build' / f'native-{game_id}'
    web = ROOT / 'build' / f'web-{game_id}'
    slot = os.getenv('PS2_BUILD_SLOT', '0')
    if slot not in {'0', '1'}: raise ValueError('Invalid build slot.')
    tools = ROOT / 'build' / ('tools-windows' if slot == '0' else f'tools-windows-{slot}')
    iso = game / 'disc.iso'
    for folder in (game / 'disc', game / 'vu1', game / 'shots', generated, web):
        folder.mkdir(parents=True, exist_ok=True)

    print('== [1/6] Preparing disc', flush=True)
    install_disc(source, iso, password)
    print('== [1/6] Verifying disc identity', flush=True)
    from install_identity import claim_disc
    import json
    digest, duplicate = claim_disc(ROOT,game_id,iso)
    identity=game/'identity.json'
    identity.write_text(json.dumps({'disc_sha256':digest,'duplicate_of':duplicate}))
    if duplicate: raise ValueError('This disc is already installed as ' + duplicate)
    image = Image(iso)
    try:
        cnf = image.find('SYSTEM.CNF')
        if not cnf or cnf[3] > 65536:
            raise ValueError('Disc has no valid SYSTEM.CNF.')
        image.file.seek(cnf[2] * 2048)
        config = image.file.read(cnf[3]).decode('ascii', 'replace')
        match = re.search(r'^\s*BOOT2\s*=\s*(cdrom0:[^\r\n]+)', config, re.M | re.I)
        if not match:
            raise ValueError('SYSTEM.CNF does not name a PS2 BOOT2 executable.')
        boot = match[1].strip()
        entry = image.find(boot.split(':', 1)[1].split(';', 1)[0])
        if not entry:
            raise ValueError(f'Disc is missing the boot executable {boot}.')
        if entry[3] > 256 * 1024 * 1024:
            raise ValueError('Boot executable exceeds the 256 MiB safety limit.')
        elf = game / 'disc' / 'boot.elf'
        image.copy(entry, elf)
        print('== [2/6] Preparing executable', flush=True)
        core = image.find('CORE.GT4')
        if core:
            packed = game / 'disc' / 'CORE.GT4'
            image.copy(core, packed)
            elf = game / 'core.elf'
            subprocess.run([sys.executable, ROOT / 'scripts/gt4_core.py', packed, elf], check=True)
        content = elf.read_bytes()
        extra = []
        if b'SNR2' in content or b'xff2' in content:
            modules(image, game / 'modules')
            extra += ['--modules', relative(game / 'modules')]
    finally:
        image.file.close()
    overlays = game / 'overlays'
    if len(content) < 52 or content[:6] != b'\x7fELF\x01\x01':
        raise ValueError('The disc boot executable is not a little-endian 32-bit ELF.')
    if windows(content):
        overlays.mkdir(exist_ok=True)
        extra += ['--overlays', relative(overlays)]

    env = native_env() if rounds else tools_env()
    compiler = f'-DCMAKE_CXX_COMPILER={BIN / "clang++.exe"}'
    cmake(tools, compiler, target='eerecomp', env=env)
    subprocess.run([BIN / 'cmake.exe', '--build', relative(tools), '--parallel', str(JOBS),
                    '--target', 'vurecomp'], check=True, cwd=ROOT, env=env)
    entries = game / 'entries.txt'
    entries.touch()
    runner = native / 'ps2run.exe'

    def translate():
        subprocess.run([tools / 'eerecomp.exe', relative(elf), '--entries', relative(entries),
                        *extra, '--out', relative(generated)], check=True, cwd=ROOT, env=env)

    def build_native():
        cmake(native, compiler, f'-DPS2_GENERATED={generated}', target='ps2run', env=env)

    print('== [3/6] Translating PS2 machine code', flush=True)
    translate()
    print('== [4/6] Exploring game paths', flush=True)
    presses = ['--press', '300:start']
    for frame in range(600, frames, 300):
        presses += ['--press', f'{frame}:cross']
    misses, card, dump = (game / name for name in ('misses.txt', 'explore.ps2', 'explore_ram.bin'))
    explore_shots = game_logs_dir(game.name) / 'shots'
    explore_shots.mkdir(parents=True, exist_ok=True)
    explore_env = {**env, 'PS2_DUMP': relative(dump), 'PS2_GPU_LOW_POWER': '1',
                   'PS2_VU_RECORD': relative(game / 'vu1')}
    for index in range(rounds):
        build_native()
        for path in (misses, card, dump):
            path.unlink(missing_ok=True)
        with game_log(game.name, 'explore.log').open('wb') as log:
            result = subprocess.run(
                [runner, relative(elf), '--disc', relative(iso), '--boot', boot, '--misses', relative(misses),
                 '--memcard', relative(card), '--frames', str(frames), *presses,
                 '--frames-dir', relative(explore_shots), '--frame-every', '300'],
                cwd=ROOT, env=explore_env, stdout=log, stderr=subprocess.STDOUT, timeout=900)
        if result.returncode:
            raise RuntimeError(f'Exploration exited with status {result.returncode}. See Exploration log. Set maximum rounds to 0 to build without exploration.')
        captured = ''
        if overlays.exists() and dump.exists():
            captured = subprocess.check_output([sys.executable, ROOT / 'scripts/windows.py',
                                                'capture', elf, dump, overlays, misses], text=True)
        known = set(entries.read_text().split())
        found = set()
        if misses.exists():
            for item in misses.read_text().split():
                module, sep, address = item.rpartition(':')
                found.add(f'{module}{sep}{int(address, 16):x}')
        added = found - known
        print(f'Round {index + 1}: {len(added)} new entry points. {captured.strip()}', flush=True)
        if not added and not captured:
            break
        entries.write_text(''.join(item + '\n' for item in sorted(known | added)))
        translate()

    print('== [4b/6] Install health check', flush=True)
    from install_health import write_health, gate_ready
    health = write_health(game)
    print(f"Health {health.get('status')}: prims={health.get('primitives')} "
          f"reasons={health.get('reasons') or '-'} warnings={health.get('warnings') or '-'}",
          flush=True)
    gate_ready(health)

    print('== [5/6] Compiling vector unit programs', flush=True)
    if any((game / 'vu1').glob('*.bin')):
        subprocess.run([tools / 'vurecomp.exe', relative(game / 'vu1'), relative(generated)],
                       check=True, cwd=ROOT, env=env)
    print('== [6/6] Building browser player', flush=True)
    boot_file = web / 'boot.txt'
    boot_file.write_text(boot + '\n', encoding='ascii')
    build_web(game_id)


if __name__ == '__main__':
    if len(sys.argv) < 3: raise SystemExit('usage: windows_port.py GAME_ID DISC_PATH FRAMES ROUNDS | --web-only GAME_ID')
    supplied_id = sys.argv[2] if sys.argv[1] == '--web-only' else sys.argv[1]
    if not re.fullmatch(r'[a-f0-9]{32}', supplied_id): raise SystemExit('Invalid game ID.')
    archive_password = None
    if os.getenv('PS2_ARCHIVE_PASSWORD_STDIN') == '1':
        archive_password = sys.stdin.buffer.readline().decode('utf-8').rstrip('\r\n')
    if len(sys.argv) > 1 and sys.argv[1] == '--web-only':
        game_id = sys.argv[2]
        if not prepared_game(game_id):
            raise ValueError('Existing game files are incomplete.')
        print('== [1/1] Building browser player', flush=True)
        build_web(game_id)
    elif len(sys.argv) >= 5:
        port(sys.argv[1], Path(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), archive_password)
    else:
        raise SystemExit('usage: windows_port.py GAME_ID DISC_PATH FRAMES ROUNDS | --web-only GAME_ID')
