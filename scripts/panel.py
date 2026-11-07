"""Loopback-only PS2 game library and player server."""
import base64
import binascii
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import http.server
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
from urllib.request import urlopen
from urllib.parse import urlsplit, parse_qs, unquote
import webbrowser

sys.path.insert(0, str(Path(__file__).resolve().parent))

from serve import Handler, ROOM_PATH, BoundedHTTPServer
from windows_port import EXTENSIONS, ROOT, prepared_game
from archives import ARCHIVE_EXTENSIONS, inspect_archive
from malware_guard import assert_safe_import
from log_paths import game_log, resolve_game_log
import cover_settings
import store

PORT = 8620
ORIGIN = f'http://127.0.0.1:{PORT}'
GAMES = ROOT / 'games'
TOKEN = secrets.token_urlsafe()
LOCK = threading.RLock()
PICKER_LOCK = threading.Lock()
ID = re.compile(r'[a-f0-9]{32}')
GAME_PATH = re.compile(r'/play/([a-f0-9]{32})/(.*)')
ASSET = re.compile(r'ps2web(?:[.][a-zA-Z0-9_-]+)+')
BUILDING = {}
QUEUE = deque()
PROGRESS = {}
BUILD_LIMIT = 1
MOBILE = {"status":"starting"}


COVER_POOL = ThreadPoolExecutor(max_workers=2, thread_name_prefix='cover')
COVER_PENDING = set()
COVER_RETRY = {}
COVER_LIMIT = 5 * 1024 * 1024
COVER_EXTS = ('.png', '.jpg', '.jpeg', '.webp')
COVER_MIME_EXT = {
    'image/png': '.png',
    'image/jpeg': '.jpg',
    'image/webp': '.webp',
}


def disc_serial(game_id):
    boot = ROOT / 'build' / f'web-{game_id}' / 'boot.txt'
    try:
        name = re.split(r'[/\\:]', boot.read_text(encoding='ascii').strip())[-1]
    except (OSError, UnicodeError):
        return None
    match = re.fullmatch(r'([A-Z]{4})[_-]?(\d{3})\.?(\d{2})(?:;\d+)?', name.upper())
    if match:
        prefix, first, last = match.groups()
        return f'{prefix}-{first}{last}'
    return None


def reset_cover_retries():
    with LOCK:
        COVER_RETRY.clear()


def clear_cover_cache():
    folder = GAMES / '.covers'
    if not folder.is_dir():
        return
    for path in folder.iterdir():
        if path.is_file() and path.suffix.lower() in COVER_EXTS + ('.tmp',):
            try:
                path.unlink()
            except OSError:
                pass


def cover_cache_dir():
    path = GAMES / '.covers'
    path.mkdir(exist_ok=True)
    return path


def _cover_candidates(serial, prefer):
    order = ('.png', '.webp', '.jpg', '.jpeg') if prefer == '3d' else ('.jpg', '.jpeg', '.png', '.webp')
    return [serial + ext for ext in order]


def find_cached_cover(serial):
    folder = cover_cache_dir()
    cfg = cover_settings.load()
    for name in _cover_candidates(serial, cfg.get('cover_prefer', '3d')):
        path = folder / name
        if path.is_file():
            return path
    for path in folder.glob(serial + '.*'):
        if path.suffix.lower() in COVER_EXTS and path.is_file():
            return path
    return None


def find_local_cover(serial, cfg=None):
    cfg = cfg or cover_settings.load()
    root = (cfg.get('cover_local_path') or '').strip()
    if not root:
        return None
    folder = Path(root)
    if not folder.is_dir():
        return None
    for name in _cover_candidates(serial, cfg.get('cover_prefer', '3d')):
        path = folder / name
        if path.is_file():
            return path
    return None


def _download_cover_url(url):
    with urlopen(url, timeout=8) as response:
        body = response.read(COVER_LIMIT + 1)
    if len(body) > COVER_LIMIT:
        raise ValueError('Cover image too large.')
    mime = poster_type(body)
    return body, mime


def _store_cover_bytes(title):
    proxy = store.lookup_poster(title, fetch=True)
    if not proxy:
        raise ValueError('No store cover.')
    if proxy.startswith('/api/store/image'):
        query = parse_qs(urlsplit(proxy).query)
        target = unquote((query.get('u') or [''])[0])
        if not target:
            raise ValueError('No store cover.')
        body, mime = store.provider_image(target)
    else:
        body, mime = _download_cover_url(proxy)
    if len(body) > COVER_LIMIT:
        raise ValueError('Cover image too large.')
    if mime.split(';', 1)[0].strip() not in COVER_MIME_EXT:
        mime = poster_type(body)
    else:
        poster_type(body)
    return body, poster_type(body)


def _write_cover_cache(serial, body, mime):
    ext = COVER_MIME_EXT.get(mime)
    if not ext:
        raise ValueError('Unsupported cover type.')
    folder = cover_cache_dir()
    for stale in folder.glob(serial + '.*'):
        if stale.suffix.lower() in COVER_EXTS:
            try:
                stale.unlink()
            except OSError:
                pass
    path = folder / (serial + ext)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes(body)
    temporary.replace(path)
    return path


def fetch_cover(serial, title=''):
    try:
        cfg = cover_settings.load()
        if cfg.get('cover_source') == 'local':
            local = find_local_cover(serial, cfg)
            if local:
                return
        else:
            prefer = cfg.get('cover_prefer', '3d')
            templates = (
                (cfg.get('cover_3d_url'), cfg.get('cover_2d_url'))
                if prefer == '3d' else
                (cfg.get('cover_2d_url'), cfg.get('cover_3d_url'))
            )
            for template in templates:
                try:
                    body, mime = _download_cover_url(cover_settings.render_url(template, serial))
                    _write_cover_cache(serial, body, mime)
                    return
                except (OSError, ValueError):
                    continue
        if title:
            body, mime = _store_cover_bytes(title)
            _write_cover_cache(serial, body, mime)
            return
        raise ValueError('Cover not found.')
    except (OSError, ValueError):
        with LOCK:
            COVER_RETRY[serial] = time.monotonic() + 600
    finally:
        with LOCK:
            COVER_PENDING.discard(serial)


def game_poster(game_id, schedule=False):
    custom = GAMES / game_id / 'poster.image'
    if custom.is_file():
        return custom
    serial = disc_serial(game_id)
    if not serial:
        return None
    cfg = cover_settings.load()
    if cfg.get('cover_source') == 'local':
        local = find_local_cover(serial, cfg)
        if local:
            return local
    cached = find_cached_cover(serial)
    if cached:
        return cached
    if schedule and serial not in COVER_PENDING and COVER_RETRY.get(serial, 0) <= time.monotonic():
        game = get_game(game_id)
        title = game.get('title') if game else ''
        COVER_PENDING.add(serial)
        COVER_POOL.submit(fetch_cover, serial, title or '')
    return None


def poster_type(body):
    if body.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    if body.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    if body[:4] == b'RIFF' and body[8:12] == b'WEBP':
        return 'image/webp'
    raise ValueError('Choose a PNG, JPEG or WebP image.')


def metadata(game_id):
    return GAMES / game_id / 'library.json'


def get_game(game_id):
    path = metadata(game_id)
    if not path.is_file(): return None
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        if (not isinstance(value, dict) or value.get('id') != game_id or
            value.get('status') not in {'ready','failed','building','queued','deleting','duplicate','cancelled'} or
            not isinstance(value.get('title'), str)):
            raise ValueError('Invalid library metadata.')
        return value
    except (ValueError, OSError, RecursionError):
        return {'id': game_id, 'title': game_id[:8], 'status': 'failed',
                'error': 'Library metadata is damaged. Delete this entry and add the original disc again.'}


def save(game):
    path = metadata(game['id'])
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(game, ensure_ascii=False), encoding='utf-8')
    temp.replace(path)


def start_queued():
    # Reserve build slots, dequeue work and publish state atomically. This is
    # called by request threads and finishing worker threads alike.
    with LOCK:
        while QUEUE and len(BUILDING) < BUILD_LIMIT:
            game, source, frames, rounds, password = QUEUE.popleft()
            slot = next(slot for slot in range(BUILD_LIMIT) if slot not in BUILDING.values())
            game_id = game['id']
            game['status'] = 'building'
            save(game)
            BUILDING[game_id] = slot
            PROGRESS[game_id] = {'stage': 'Starting build', 'step': 0, 'total': 6}
            worker = threading.Thread(target=build, args=(game, source, frames, rounds, slot, password),
                                      name='game-build-' + game_id[:8])
            try:
                worker.start()
            except RuntimeError as error:
                BUILDING.pop(game_id, None)
                PROGRESS.pop(game_id, None)
                game.update(status='failed', error='Could not start build worker: ' + str(error))
                save(game)


def enqueue(game, source=None, frames=3600, rounds=8, password=None):
    with LOCK:
        game['status'] = 'queued'
        game.pop('error', None)
        save(game)
        QUEUE.append((game, source, frames, rounds, password))
        start_queued()


def build(game, source, frames, rounds, slot, password=None):
    game_id = game['id']
    had_player = (ROOT / 'build' / f'web-{game_id}' / 'ps2web.html').is_file()
    try:
        args = [game_id, source, str(frames), str(rounds)] if source else ['--web-only', game_id]
        env = {**os.environ, 'PS2_BUILD_SLOT': str(slot), 'PS2_BUILD_JOBS': os.getenv('PS2_BUILD_JOBS','1')}
        send_password = bool(password) and source and source.suffix.lower() in ARCHIVE_EXTENSIONS
        if send_password:
            env['PS2_ARCHIVE_PASSWORD_STDIN'] = '1'
        # The worker needs the project-managed 7-Zip executable even when the
        # panel itself was launched without MSYS2 on the inherited PATH.
        msys_bin = ROOT / 'tools' / 'msys64' / 'clang64' / 'bin'
        env['PATH'] = os.pathsep.join((str(msys_bin), env.get('PATH', '')))
        with game_log(game_id, 'build.log').open('wb' if source else 'ab') as log:
            if not source:
                log.write(b'\n== Rebuilding browser player ==\n')
            with subprocess.Popen([sys.executable, '-u', ROOT / 'scripts/windows_port.py', *args],
                                  cwd=ROOT, env=env,
                                  stdin=subprocess.PIPE if send_password else subprocess.DEVNULL,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as process:
                if process.stdin:
                    process.stdin.write(((password or '') + '\n').encode('utf-8'))
                    process.stdin.close()
                for line in process.stdout:
                    log.write(line)
                    log.flush()
                    stage = re.match(rb'== \[(\d+)/(\d+)\] (.+)', line)
                    tasks = re.match(rb'\[(\d+)/(\d+)\] ', line)
                    if stage or tasks:
                        with LOCK:
                            if stage:
                                PROGRESS[game_id] = {'stage': stage[3].decode('utf-8', 'replace'),
                                                     'step': int(stage[1]), 'total': int(stage[2])}
                            else:
                                PROGRESS[game_id].update(done=int(tasks[1]), count=int(tasks[2]))
                if process.wait():
                    raise RuntimeError('Build failed. See the build log for details.')
        if not (ROOT / 'build' / f'web-{game_id}' / 'ps2web.html').is_file():
            raise RuntimeError('The browser build is missing.')
        from install_health import write_health, gate_ready
        health = write_health(GAMES / game_id)
        try:
            from self_heal import heal_game
            heal_game(game_id, dry_run=False, auto=True)
        except Exception as heal_err:
            game['self_heal_error'] = str(heal_err)[:240]
        game['health'] = health.get('status')
        if health.get('warnings'):
            game['health_warnings'] = health.get('warnings')
        if health.get('status') == 'fail':
            game['health_reasons'] = health.get('reasons') or []
            if source:
                # Full installs must not silently become playable when explore proves broken.
                gate_ready(health)
            # Web-only rebuilds keep prior ready state but surface the health failure.
        game['status'] = 'ready'
        identity=GAMES/game_id/'identity.json'
        if identity.is_file(): game.update(json.loads(identity.read_text()))
        if source:
            cleanup_download_source(source)

    except Exception as error:
        # Keep the library state recoverable even if an unexpected worker-side
        # exception occurs. Do not leave the entry stuck in 'building'.
        identity=GAMES/game_id/'identity.json'
        duplicate=None
        if identity.is_file():
            try: duplicate=json.loads(identity.read_text()).get('duplicate_of')
            except (OSError,ValueError): pass
        if duplicate and ID.fullmatch(duplicate):
            game.update(status='duplicate',duplicate_of=duplicate)
            for path in (GAMES/game_id/'disc.iso',): path.unlink(missing_ok=True)
            if source: cleanup_download_source(source)
            return
        if source: cleanup_download_source(source)
        detail = str(error).strip() or type(error).__name__
        game.update(status='ready' if had_player else 'failed', error=('Build failed: ' + detail)[:500])
    finally:
        with LOCK:
            try:
                # Poster edits are stored separately from build state.
                save(game)
            finally:
                BUILDING.pop(game_id, None)
                PROGRESS.pop(game_id, None)
                start_queued()


def cleanup_download_source(source):
    path=Path(source).resolve()
    folder=(ROOT/'downloads').resolve()
    if path.parent==folder and ID.fullmatch(path.stem):
        path.unlink(missing_ok=True)


def retry_download_install(job, password):
    if password is not None and (not isinstance(password,str) or len(password)>1024 or any(c in password for c in '\0\r\n')):
        raise ValueError('Invalid archive password.')
    path=Path(job.get('path','')).resolve()
    if path.parent!=(ROOT/'downloads').resolve() or not path.is_file():raise ValueError('Managed download is unavailable.')
    with LOCK:
        game=get_game(job.get('game_id','')) if ID.fullmatch(job.get('game_id','')) else None
        if game and game['status'] in ('failed','ready'):
            if game['status']=='ready' and not game.get('error'):return game
            enqueue(game,path,3600,8,password or None)
            return game
        return import_game({'path':str(path),'title':job['title'],'password':password})


def download_state(game_id):
    with LOCK:
        game=get_game(game_id)
        if not game:return None
        if game.get('duplicate_of'):
            return {'status':'complete','duplicate':True,'game_id':game['duplicate_of']}
        state=game['status']
        progress=dict(PROGRESS.get(game_id,{}))
        if state=='building' and progress.get('step',0)<=1:state='importing'
        if 'identity' in progress.get('stage','').lower():state='verifying'
        if game.get('error'):state='failed'
        return {'status':{'ready':'complete','failed':'failed','queued':'queued','building':'building'}.get(state,state),
                'build_progress':progress, 'error':game.get('error')}


def pick_disc():
    if os.name != 'nt':
        raise ValueError('Paste the full disc image path to select a game on this system.')
    if not PICKER_LOCK.acquire(blocking=False):
        raise ValueError('A disc picker is already open.')
    try:
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-STA', '-ExecutionPolicy', 'Bypass',
             '-File', ROOT / 'scripts/pick-disc.ps1'],
            capture_output=True, encoding='utf-8', errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW, cwd=ROOT)
        if result.returncode:
            raise ValueError('The Windows disc picker could not open. You can paste the full path.')
        return result.stdout.rstrip('\r\n')
    finally:
        PICKER_LOCK.release()


def pick_folder():
    if os.name != 'nt':
        raise ValueError('Paste the full covers folder path on this system.')
    if not PICKER_LOCK.acquire(blocking=False):
        raise ValueError('A folder picker is already open.')
    try:
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-STA', '-ExecutionPolicy', 'Bypass',
             '-File', ROOT / 'scripts/pick-folder.ps1'],
            capture_output=True, encoding='utf-8', errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW, cwd=ROOT)
        if result.returncode:
            raise ValueError('The Windows folder picker could not open. You can paste the full path.')
        return result.stdout.rstrip('\r\n')
    finally:
        PICKER_LOCK.release()


def settings_view():
    import store_settings
    return {**store_settings.public_view(), **cover_settings.public_view()}


def save_settings(data):
    import store_settings
    if not isinstance(data, dict):
        raise ValueError('Invalid settings payload.')
    result = store_settings.save(data)
    covers = cover_settings.save(data)
    if any(key in data for key in cover_settings.KEYS):
        reset_cover_retries()
        clear_cover_cache()
    return {**result, **covers}


def import_game(data):
    if len(QUEUE) >= 16:
        raise ValueError('Build queue is full. Wait for a build to finish.')
    raw_source = data.get('path')
    if not isinstance(raw_source, str) or not raw_source.strip():
        raise ValueError('Enter the full path to a disc image.')
    source = Path(raw_source.strip().strip('"'))
    if not source.is_absolute() or source.suffix.lower() not in EXTENSIONS or not source.is_file():
        raise ValueError('Choose an existing ISO, BIN, CUE, IMG, CHD, ZIP, 7z or RAR file by full path.')
    source = source.resolve()
    if source.is_relative_to(GAMES):
        raise ValueError('Choose an original disc outside the managed games folder.')
    # Never execute imported content; reject PE/scripts and Defender detections first.
    assert_safe_import(source)
    title = data.get('title') or source.stem
    if not isinstance(title, str) or not title.strip() or len(title) > 120:
        raise ValueError('Enter a title between 1 and 120 characters.')
    frames, rounds = data.get('frames', 3600), data.get('rounds', 8)
    if type(frames) is not int or type(rounds) is not int or not (1 <= frames <= 36000 and 0 <= rounds <= 20):
        raise ValueError('Frames must be 1–36000 and rounds 0–20.')
    password = data.get('password') or None
    if password is not None and (not isinstance(password, str) or len(password) > 1024 or
                                 '\x00' in password or '\r' in password or '\n' in password):
        raise ValueError('Archive passwords must be text no longer than 1024 characters and cannot contain line breaks.')
    game_id = secrets.token_hex(16)
    game = {'id': game_id, 'title': title.strip(), 'status': 'building','added_at':time.time()}
    (GAMES / game_id).mkdir()
    enqueue(game, source, frames, rounds, password)
    return game


def game_action(game_id, action):
    game = get_game(game_id)
    if not game:
        raise ValueError('Game is missing.')
    if action == 'dequeue':
        with LOCK:
            item = next((item for item in QUEUE if item[0]['id'] == game_id), None)
            if not item: raise ValueError('This game has already started building.')
            QUEUE.remove(item)
            if item[1]: cleanup_download_source(item[1])
            had_player = (ROOT / 'build' / f'web-{game_id}' / 'ps2web.html').is_file()
            if had_player: game.update(status='ready')
            elif item[1] is None and prepared_game(game_id):
                game.update(status='failed',error='Queued browser rebuild was cancelled.')
            else: game.update(status='cancelled')
            save(game)
        return
    if game['status'] in ('building', 'queued'):
        raise ValueError('Wait for the build to finish.')
    if action == 'delete':
        game['status'] = 'deleting'
        save(game)
        for folder in (ROOT / 'build' / f'web-{game_id}',
                       ROOT / 'build' / f'native-{game_id}', ROOT / 'generated' / game_id):
            if folder.exists():
                shutil.rmtree(folder)
        folder = GAMES / game_id
        # Keep the manifest until the rest has been removed so deletion can be retried.
        for child in folder.iterdir():
            if child == metadata(game_id):
                continue
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
        metadata(game_id).unlink()
        folder.rmdir()
    elif action == 'reexplore' and game['status'] in ('failed', 'ready') and (GAMES / game_id / 'disc.iso').is_file():
        enqueue(game, GAMES / game_id / 'disc.iso', 3600, 8)
    elif action == 'retry' and game['status'] in ('failed', 'ready') and prepared_game(game_id):
        enqueue(game)
    else:
        raise ValueError('Browser build is unavailable.')


def _library_games():
    games = []
    for path in GAMES.iterdir():
        if not ID.fullmatch(path.name):
            continue
        game = get_game(path.name)
        if game and game['status'] not in ('duplicate', 'cancelled', 'deleting'):
            games.append(game)
    return games


def rebuild_all_games():
    """Queue browser rebuilds for every ready/failed title that still has prepared inputs."""
    queued = 0
    skipped = 0
    with LOCK:
        for game in _library_games():
            if game['status'] in ('building', 'queued'):
                skipped += 1
                continue
            if game['status'] in ('failed', 'ready') and prepared_game(game['id']):
                enqueue(game)
                queued += 1
            else:
                skipped += 1
    return {'queued': queued, 'skipped': skipped}


def delete_all_games():
    """Delete every library title that is not currently building or queued."""
    deleted = 0
    skipped = 0
    with LOCK:
        targets = []
        for game in _library_games():
            if game['status'] in ('building', 'queued'):
                skipped += 1
            else:
                targets.append(game['id'])
    for game_id in targets:
        try:
            with LOCK:
                game_action(game_id, 'delete')
            deleted += 1
        except (ValueError, OSError):
            skipped += 1
    return {'deleted': deleted, 'skipped': skipped}


def resolve_async_mode(game_id):
    """Prefer build.json; otherwise infer from published Emscripten glue.

    Never report asyncify for a JSPI wasm — that would skip the feature gate
    and fail later with a worse black screen.
    """
    build = ROOT / 'build' / f'web-{game_id}'
    try:
        info = json.loads((build / 'build.json').read_text(encoding='utf-8'))
        mode = info.get('async_mode')
        if mode in ('asyncify', 'jspi'):
            return mode
    except (OSError, ValueError, TypeError):
        pass
    try:
        glue = (build / 'ps2web.js').read_text(encoding='utf-8', errors='ignore')
    except OSError:
        return 'jspi'
    if 'WebAssembly.Suspending' in glue or 'Suspending' in glue:
        return 'jspi'
    if 'Asyncify' in glue or 'ASYNCIFY' in glue:
        return 'asyncify'
    return 'jspi'


class Panel(Handler):
    def parse_request(self):
        if not super().parse_request():
            return False
        if self.headers.get('Host') != f'127.0.0.1:{PORT}':
            self.send_error(403)
            return False
        return True

    @property
    def route(self):
        return urlsplit(self.path).path

    def target(self):
        match = GAME_PATH.fullmatch(self.route)
        if not match:
            return None
        game_id, asset = match.groups()
        with LOCK:
            game = get_game(game_id)
        if not game or game['status'] != 'ready':
            return None
        if asset == 'disc.iso':
            path = GAMES / game_id / asset
        else:
            asset = asset or 'ps2web.html'
            if asset != 'boot.txt' and not ASSET.fullmatch(asset):
                return None
            path = ROOT / 'build' / f'web-{game_id}' / asset
        base = GAMES / game_id if asset == 'disc.iso' else ROOT / 'build' / f'web-{game_id}'
        return str(path) if (path.is_file() and base.resolve().is_relative_to(ROOT.resolve())
                             and path.resolve().is_relative_to(base.resolve())) else None

    def serve_player_shell(self, head=False):
        match = GAME_PATH.fullmatch(self.route)
        if not match or match[2] not in ('', 'ps2web.html'):
            return False
        target = self.target()
        if not target:
            return False
        # The compiled HTML is only a readiness check. Generated markup can
        # vary with Emscripten versions, so never inspect it to select the UI.
        try:
            shell = (ROOT / 'web/shell.html').read_bytes()
        except OSError:
            self.send_error(500, 'Player interface is missing. Reinstall the current project files.')
            return True
        marker = b'{{{ SCRIPT }}}'
        if shell.count(marker) != 1 or b'class="control-settings"' not in shell:
            self.send_error(500, 'Player interface is outdated or incomplete. Replace web/shell.html.')
            return True
        mode = resolve_async_mode(match[1])
        body = shell.replace(b'__PS2_ASYNC_MODE__',mode.encode()).replace(marker, b'<script src="ps2web.js"></script>')
        self.send_response(200)
        self.headers_for('ps2web.html', len(body))
        if not head:
            self.wfile.write(body)
        return True

    def do_HEAD(self):
        if not self.serve_player_shell(head=True):
            super().do_HEAD()

    def do_GET(self):
        if self.serve_player_shell():
            return
        player_asset = re.fullmatch(r'/play/([a-f0-9]{32})/(metadata.json|poster.image)', self.route)
        if player_asset:
            game = get_game(player_asset[1])
            if not game or game['status'] != 'ready':
                self.send_error(404)
                return
            if player_asset[2] == 'metadata.json':
                try:
                    build_info = json.loads((ROOT / 'build' / ('web-' + game['id']) / 'build.json').read_text())
                except (OSError, ValueError):
                    build_info = {'id': str((ROOT / 'build' / ('web-' + game['id']) / 'ps2web.js').stat().st_mtime_ns)}
                self.send_json({
                    'title': game['title'],
                    'poster': bool(game_poster(game['id'])),
                    'serial': disc_serial(game['id']),
                    'build': build_info,
                })
                return
            path = game_poster(game['id'])
            if not path:
                self.send_error(404)
                return
            body = path.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', poster_type(body))
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)
            return
        if self.route == '/':
            body = (ROOT / 'web/panel.html').read_bytes().replace(b'__PANEL_TOKEN__', TOKEN.encode())
            self.send_response(200)
            self.headers_for('panel.html', len(body))
            self.wfile.write(body)
            return
        if self.route == '/known-cheats.json':
            path = ROOT / 'web' / 'known-cheats.json'
            if not path.is_file():
                self.send_json({})
                return
            body = path.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'public, max-age=3600')
            self.end_headers()
            self.wfile.write(body)
            return
        if self.route == '/api/mobile':
            self.send_json(dict(MOBILE));return
        if self.route == '/api/settings':
            self.send_json(settings_view())
            return
        if self.route == '/api/mobile/certificate':
            path=ROOT/'tools/mobile/phone-ca.crt'
            if not path.is_file(): self.send_error(404);return
            body=path.read_bytes();self.send_response(200)
            self.send_header('Content-Type','application/x-x509-ca-cert')
            self.send_header('Content-Disposition','attachment; filename="CyberArcade-Mobile-CA.crt"')
            self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
        if self.route == '/api/store/jobs':
            self.send_json(store.jobs(download_state))
            return
        if self.route == '/api/store/catalog':
            try:
                query = parse_qs(urlsplit(self.path).query)
                page_raw = (query.get('page') or ['1'])[0]
                try: page = int(page_raw)
                except ValueError: raise ValueError('Invalid catalog page.') from None
                q = unquote((query.get('q') or [''])[0])
                source = unquote((query.get('source') or ['web'])[0])
                self.send_json(store.catalog(q, page, source))
            except (ValueError, OSError) as error:
                self.send_json({'error': str(error)}, 400)
            return
        if self.route == '/api/store/image':
            try:
                query = parse_qs(urlsplit(self.path).query)
                target = unquote((query.get('u') or [''])[0])
                body, mime = store.provider_image(target)
            except (ValueError, OSError):
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'public, max-age=21600')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(body)
            return
        if self.route == '/api/games':
            with LOCK:
                games = [get_game(p.name) for p in GAMES.iterdir() if ID.fullmatch(p.name)]
                result = [dict(g, rebuild=bool(prepared_game(g['id'])),
                               progress=PROGRESS.get(g['id'], {}).copy(),
                               poster=bool(game_poster(g['id'], schedule=True)),serial=disc_serial(g['id']),
                               disc_bytes=(GAMES/g['id']/'disc.iso').stat().st_size if (GAMES/g['id']/'disc.iso').is_file() else 0) for g in games if g and g['status'] not in ('duplicate','cancelled')]
            self.send_json(result)
            return
        poster = re.fullmatch(r'/api/games/([a-f0-9]{32})/poster', self.route)
        if poster:
            path = game_poster(poster[1])
            if path is None:
                self.send_error(404)
                return
            try:
                body = path.read_bytes()
                mime = poster_type(body)
            except (OSError, ValueError):
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(body)
            return
        logs = re.fullmatch(r'/api/games/([a-f0-9]{32})/(build|explore|desktop)(/download)?', self.route)
        if logs:
            game_id, name, download = logs.groups()
            path = resolve_game_log(game_id, f'{name}.log', GAMES / game_id) or (GAMES / game_id / f'{name}.log')
            if download:
                try:
                    log = path.open('rb')
                except OSError:
                    self.send_error(404)
                    return
                with log:
                    length = os.fstat(log.fileno()).st_size
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain; charset=utf-8')
                    self.send_header('Content-Disposition', f'attachment; filename="{game_id[:8]}-{name}.log"')
                    self.send_header('Content-Length', str(length))
                    self.end_headers()
                    while length:
                        chunk = log.read(min(length, 65536))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        length -= len(chunk)
                return
            try:
                with path.open('rb') as log:
                    log.seek(max(0, path.stat().st_size - 24000))
                    content = log.read(24000).decode('utf-8', 'replace')
            except OSError:
                content = 'No log yet.'
            self.send_json({'log': content})
            return
        match = GAME_PATH.fullmatch(self.route)
        if match and ROOM_PATH.fullmatch('/' + match[2]):
            self.path = self.path[len('/play/' + match[1]):]
        super().do_GET()

    def do_POST(self):
        if self.headers.get('Origin') != ORIGIN:
            self.send_error(403)
            return
        match = GAME_PATH.fullmatch(self.route)
        if match and ROOM_PATH.fullmatch('/' + match[2]):
            self.path = '/' + match[2]
            super().do_POST()
            return
        if self.headers.get('X-Panel-Token') != TOKEN:
            self.send_error(403)
            return
        try:
            if self.route == '/api/settings':
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 16384: raise ValueError('Invalid settings size.')
                data = json.loads(self.rfile.read(length))
                self.send_json(save_settings(data))
                return
            if self.route.startswith('/api/store/'):
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 16384: raise ValueError('Invalid request size.')
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict): raise ValueError('Invalid store request.')
                def importer(value):
                    with LOCK: return import_game(value)
                if self.route == '/api/store/download': result = store.start(data, ROOT, importer)
                elif self.route == '/api/store/control': result = store.control(data.get('id'), data.get('action'))
                elif self.route == '/api/store/versions': result = store.versions(data.get('url'))
                else:
                    self.send_error(404)
                    return
                self.send_json(result)
                return
            repair = re.fullmatch(r'/api/games/([a-f0-9]{32})/repair', self.route)
            if repair:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=1024: raise ValueError('Invalid repair request.')
                data=json.loads(self.rfile.read(length))
                with LOCK:
                    game=get_game(repair[1]);elf=prepared_game(repair[1])
                    if not game or not elf or game['status'] not in ('ready','failed'):raise ValueError('Wait for this game build to finish.')
                    from translation_repair import add_entry
                    add_entry(elf,GAMES/game['id']/'entries.txt',data.get('address'))
                    enqueue(game)
                self.send_json({'queued':True});return
            poster = re.fullmatch(r'/api/games/([a-f0-9]{32})/poster', self.route)
            if poster:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 7 * 1024 * 1024:
                    raise ValueError('Choose a poster under 5 MB.')
                data = json.loads(self.rfile.read(length))
                encoded = data.get('image') if isinstance(data, dict) else None
                if not isinstance(encoded, str):
                    raise ValueError('Missing poster image.')
                body = base64.b64decode(encoded, validate=True)
                if len(body) > 5 * 1024 * 1024:
                    raise ValueError('Choose a poster under 5 MB.')
                poster_type(body)
                with LOCK:
                    if not get_game(poster[1]):
                        raise ValueError('Game is missing.')
                    path = GAMES / poster[1] / 'poster.image'
                    temp = path.with_suffix('.tmp')
                    temp.write_bytes(body)
                    temp.replace(path)
                self.send_json({})
                return
            if self.route == '/api/archive-check':
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 16384: raise ValueError('Invalid request size.')
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict) or not isinstance(data.get('path'), str): raise ValueError('Enter a game path.')
                path = Path(data['path'].strip().strip('"'))
                if not path.is_absolute() or not path.is_file() or path.suffix.lower() not in EXTENSIONS:
                    raise ValueError('Choose an existing supported game file.')
                self.send_json(inspect_archive(path))
                return
            if self.route == '/api/pick-disc':
                self.send_json({'path': pick_disc()})
                return
            if self.route == '/api/pick-folder':
                self.send_json({'path': pick_folder()})
                return
            if self.route in ('/api/games/rebuild-all', '/api/games/delete-all'):
                length = int(self.headers.get('Content-Length', '0'))
                if length < 0 or length > 16384:
                    raise ValueError('Invalid request size.')
                if length:
                    self.rfile.read(length)
                if self.route.endswith('rebuild-all'):
                    self.send_json(rebuild_all_games())
                else:
                    self.send_json(delete_all_games())
                return
            with LOCK:
                if self.route == '/api/games':
                    length = int(self.headers.get('Content-Length', '0'))
                    if not 0 < length <= 16384:
                        raise ValueError('Invalid request size.')
                    # Read the body outside the library lock.
                else:
                    action = re.fullmatch(r'/api/games/([a-f0-9]{32})/(delete|retry|dequeue|reexplore)', self.route)
                    if not action:
                        self.send_error(404)
                        return
                    game_action(*action.groups())
                    self.send_json({})
                    return
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError('Invalid game data.')
            with LOCK:
                result = import_game(data)
            self.send_json(result, 202)
        except (ValueError, OSError, binascii.Error, RecursionError) as error:
            self.send_json({'error': str(error)}, 400)


def main(open_browser=False):
    GAMES.mkdir(exist_ok=True)
    with BoundedHTTPServer(('127.0.0.1', PORT), Panel) as server:
        for path in GAMES.iterdir():
            if ID.fullmatch(path.name) and (game := get_game(path.name)) and game['status'] in ('building', 'queued'):
                published = ROOT / 'build' / ('web-' + path.name)
                backup = published.with_name(published.name + '-previous')
                if not published.exists() and (backup / 'ps2web.html').is_file(): backup.rename(published)
                available = (published / 'ps2web.html').is_file()
                game.update(status='ready' if available else 'failed', error='The last build was interrupted. Rebuild to retry.')
                save(game)
        print(f'PS2 library (live player theme) running at {ORIGIN}/. Keep this window open.', flush=True)
        def mobile_start():
            try:
                from mobile import start_automatic
                mobile_server, info = start_automatic()
                server.mobile_server = mobile_server
                MOBILE.clear();MOBILE.update(info)
                print('Mobile LAN link: ' + info['url'], flush=True)
                print(info['help'], flush=True)
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                MOBILE.clear();MOBILE.update(status='unavailable',help=str(error))
                print('Mobile setup: '+str(error),flush=True)
        threading.Thread(target=mobile_start,daemon=True,name='mobile-setup').start()
        if open_browser:
            webbrowser.open(ORIGIN + '/')
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            mobile_server = getattr(server,'mobile_server',None)
            if mobile_server: mobile_server.shutdown();mobile_server.server_close()


if __name__ == '__main__':
    main(open_browser=False)
