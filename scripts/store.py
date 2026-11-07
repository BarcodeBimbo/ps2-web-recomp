"""Bounded HTTPS downloads, IP-bypass catalog, torrents, and signed CDN transfers."""
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, unquote, quote, quote_plus, urljoin, parse_qs
from urllib.request import Request, build_opener, HTTPRedirectHandler, HTTPCookieProcessor, HTTPSHandler, ProxyHandler
from urllib.error import HTTPError, URLError
from http.cookiejar import Cookie, CookieJar
from http.client import HTTPSConnection
from http.cookies import SimpleCookie
import hashlib
import html as html_lib
import ipaddress
import json
import os
import socket
import ssl
import subprocess
import threading
import time
import secrets
import shutil
import re
from downloader_runtime import node_executable, runtime_env
import torrent_index
BASE = 'https://romsfun.com'
ORIGIN_IP = '199.127.62.112'
ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = ROOT / 'torrents'
POSTER_CACHE_PATH = CACHE_ROOT / 'poster-cache.json'
CATALOG_CACHE_DIR = CACHE_ROOT / 'catalog-cache'
IMAGE_CACHE_DIR = CACHE_ROOT / 'image-cache'
CATALOG_TTL_SECONDS = 6 * 3600
IMAGE_TTL_SECONDS = 6 * 3600
PS2_SLUG = 'playstation-2'
_CATALOG_MEM = {}
_CATALOG_LOCK = threading.RLock()
DEFAULT_ARCHIVE_PASSWORD = 'romsfun.com'
MAX_DOWNLOAD = 16 * 1024 ** 3
MAX_PROVIDER_HTML = 4 * 1024 * 1024
MAX_PROVIDER_IMAGE = 5 * 1024 * 1024
EXTENSIONS = {'.iso', '.bin', '.img', '.chd', '.zip', '.7z', '.rar', '.gz', '.xz', '.bz2', '.zst'}
DEMO_RE = re.compile(r'\b(demo|prototype|proto|sample|beta|alpha|pre[- ]?alpha|prealpha|kiosk|preview|trial|pilot|taikenban)\b', re.I)
US_RE = re.compile(r'\b(?:usa|u\.s\.a\.?|us)\b|\(us\)|\(u\)|\bntsc\b(?![- ]?[je])', re.I)
GAME_HREF_RE = re.compile(rf'https://romsfun\.com/roms/{PS2_SLUG}/([^"/]+)\.html', re.I)
CATALOG_CARD_RE = re.compile(
    rf'<img[^>]+src="(https://romsfun\.com/wp-content/uploads/[^"]+)"[^>]*alt="([^"]*)"[\s\S]{{0,1200}}?'
    rf'<a href="(https://romsfun\.com/roms/{PS2_SLUG}/[^"/]+\.html)"[^>]*>\s*([^<]+?)\s*</a>',
    re.I,
)
PAGE_RE = re.compile(rf'/roms/{PS2_SLUG}/page/(\d+)/', re.I)
DOWNLOAD_ROM_RE = re.compile(
    r'href="(https://romsfun\.com/download/[^"]+)"[^>]*>[\s\S]{0,800}?Download ROM',
    re.I,
)
VERSION_LINK_RE = re.compile(
    r'href="(https://romsfun\.com/download/[^"]+/\d+)"[^>]*>\s*([^<]+)',
    re.I,
)
DOWNLOAD_LINK_RE = re.compile(
    r'id=["\']download-link["\'][^>]*href=["\']([^"\']+)["\']|href=["\']([^"\']+)["\'][^>]*id=["\']download-link["\']',
    re.I,
)
JOBS = {}
CONTROLS = {}
LOCK = threading.RLock()
TURN = threading.Condition(LOCK)
ACTIVE = None
HTTP = threading.local()
COOKIES = CookieJar()
PROVIDER_COOKIES = CookieJar()


def _kill_torrent_worker_pids():
    """Sweep any torrent_worker.mjs processes so a cancel cannot leave a seeder behind."""
    if os.name != 'nt':
        return
    try:
        # Avoid embedding the filename literally so the PowerShell process is not matched.
        subprocess.run(
            [
                'powershell', '-NoProfile', '-Command',
                "$needle='torrent'+'_worker.mjs'; "
                "Get-CimInstance Win32_Process | "
                "Where-Object { $_.Name -match 'node' -and $_.CommandLine -and $_.CommandLine.Contains($needle) } | "
                "ForEach-Object { taskkill /F /T /PID $_.ProcessId 2>$null | Out-Null }",
            ],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        pass


def _kill_worker(process):
    """Hard-stop a Node download worker so it cannot keep seeding after cancel/finish."""
    pid = getattr(process, 'pid', None) if process is not None else None
    if os.name == 'nt' and pid:
        try:
            subprocess.run(
                ['taskkill', '/F', '/T', '/PID', str(pid)],
                capture_output=True, text=True, timeout=15,
            )
        except (OSError, subprocess.SubprocessError):
            pass
    if process is not None:
        try:
            if process.poll() is None:
                process.kill()
        except OSError:
            pass
        try:
            process.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            try:
                process.kill()
            except OSError:
                pass
    # Belt-and-suspenders: ensure no torrent_worker.mjs is still holding peer connections.
    _kill_torrent_worker_pids()



class OriginHTTPSConnection(HTTPSConnection):
    """TCP to ORIGIN_IP with SNI for romsfun.com.

    Origin TLS often omits the full public chain that Cloudflare serves at the
    edge, so verification is disabled for this pinned-IP hop only. Host and path
    checks still keep requests on romsfun.com.
    """

    def connect(self):
        self.sock = socket.create_connection((ORIGIN_IP, self.port or 443), self.timeout, self.source_address)
        context = self._context or ssl._create_unverified_context()
        self.sock = context.wrap_socket(self.sock, server_hostname='romsfun.com')


def public_url(url):
    if not isinstance(url, str) or len(url) > 8192: raise ValueError('Invalid download URL.')
    parts = urlsplit(url)
    if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password or parts.port not in (None, 443):
        raise ValueError('Use a public HTTPS download link.')
    addresses = socket.getaddrinfo(parts.hostname, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('Private and local download addresses are not supported.')
    return url


def provider_url(query='', page=1):
    if not isinstance(query, str) or len(query) > 120: raise ValueError('Invalid catalog request.')
    if not isinstance(page, int) or page < 1 or page > 500: raise ValueError('Invalid catalog request.')
    if query.strip():
        q = quote_plus(query.strip())
        return f'{BASE}/page/{page}/?s={q}' if page > 1 else f'{BASE}/?s={q}'
    suffix = f'page/{page}/' if page > 1 else ''
    return f'{BASE}/roms/{PS2_SLUG}/{suffix}'


def normalize_provider_url(value):
    if not isinstance(value, str) or not value or len(value) > 8192:
        raise ValueError('Invalid provider URL.')
    absolute = urljoin(BASE + '/', value)
    parts = urlsplit(absolute)
    host = (parts.hostname or '').lower()
    if parts.scheme != 'https' or host not in ('romsfun.com', 'www.romsfun.com', ORIGIN_IP):
        raise ValueError('Only romsfun.com provider pages are supported.')
    if parts.username or parts.password or parts.port not in (None, 443):
        raise ValueError('Invalid provider URL.')
    return urlunsplit(('https', 'romsfun.com', parts.path or '/', parts.query, ''))


def _provider_path(url):
    parts = urlsplit(normalize_provider_url(url))
    path = parts.path or '/'
    return path + (('?' + parts.query) if parts.query else '')


def _ingest_set_cookie(header_value):
    if not header_value: return
    parsed = SimpleCookie()
    try: parsed.load(header_value)
    except Exception: return
    for name, morsel in parsed.items():
        domain = (morsel['domain'] or 'romsfun.com').lstrip('.')
        path = morsel['path'] or '/'
        cookie = Cookie(0, name, morsel.value, None, False, domain, True, False, path, True, True, None, True, None, None, {})
        PROVIDER_COOKIES.set_cookie(cookie)
        COOKIES.set_cookie(cookie)


def fetch_provider(url, *, binary=False, max_bytes=MAX_PROVIDER_HTML, redirects=5):
    target = normalize_provider_url(url)
    context = ssl._create_unverified_context()
    for _ in range(redirects + 1):
        path = _provider_path(target)
        # Host argument is unused for TCP; OriginHTTPSConnection always dials ORIGIN_IP.
        connection = OriginHTTPSConnection('romsfun.com', timeout=30, context=context)
        try:
            headers = {
                'Host': 'romsfun.com',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/*,*/*;q=0.8' if binary else 'text/html,application/xhtml+xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'identity',
                'Referer': BASE + '/',
                'Connection': 'close',
            }
            cookie = '; '.join(f'{c.name}={c.value}' for c in PROVIDER_COOKIES if (c.domain or '').endswith('romsfun.com') or not c.domain)
            if cookie: headers['Cookie'] = cookie
            connection.request('GET', path, headers=headers)
            response = connection.getresponse()
            msg = getattr(response, 'msg', None)
            for raw in ((msg.get_all('Set-Cookie') if msg and hasattr(msg, 'get_all') else None) or []):
                _ingest_set_cookie(raw)
            if response.status in (301, 302, 303, 307, 308):
                location = response.getheader('Location')
                response.read()
                if not location: raise ValueError('Provider returned an empty redirect.')
                target = normalize_provider_url(urljoin(target, location))
                continue
            if response.status >= 400:
                raise ValueError(f'The provider returned HTTP {response.status}.')
            chunks, total = [], 0
            while True:
                chunk = response.read(65536)
                if not chunk: break
                total += len(chunk)
                if total > max_bytes: raise ValueError('Provider response too large.')
                chunks.append(chunk)
            body = b''.join(chunks)
            content_type = (response.getheader('Content-Type') or '').lower()
            if binary:
                if 'text/html' in content_type: raise ValueError('Expected an image from the provider.')
                return body, content_type or 'application/octet-stream'
            text = body.decode('utf-8', 'replace')
            if 'just a moment' in text.lower() or 'cf-turnstile' in text.lower():
                raise ValueError('Provider challenge still active. Retry shortly.')
            return text
        finally:
            connection.close()
    raise ValueError('Too many provider redirects.')


def clean_text(value):
    return re.sub(r'\s+', ' ', html_lib.unescape(value or '')).strip()


def parse_catalog(html):
    if not isinstance(html, str): raise ValueError('Invalid catalog HTML.')
    games, seen = [], set()
    for poster, alt, url, title in CATALOG_CARD_RE.findall(html):
        url = normalize_provider_url(url)
        if url in seen: continue
        seen.add(url)
        name = clean_text(title) or clean_text(alt) or GAME_HREF_RE.search(url).group(1).replace('-', ' ')
        games.append({
            'title': name[:120],
            'url': url,
            'poster': poster,
            'downloads': '',
            'size': '',
        })
    if not games:
        for match in GAME_HREF_RE.finditer(html):
            url = normalize_provider_url(match.group(0))
            if url in seen: continue
            seen.add(url)
            games.append({
                'title': match.group(1).replace('-', ' ').title()[:120],
                'url': url,
                'poster': '',
                'downloads': '',
                'size': '',
            })
    return games


def parse_pages(html):
    pages = [int(value) for value in PAGE_RE.findall(html or '')]
    return max(pages) if pages else 1


def _download_slug(url):
    path = urlsplit(url or '').path or ''
    match = re.search(r'/download/([^/]+)', path, re.I)
    return (match.group(1) if match else '').lower()


def _region_key(title):
    text = (title or '').lower()
    if US_RE.search(text): return 'usa'
    if re.search(r'\b(europe|eur|pal)\b|\(e\)', text): return 'europe'
    if re.search(r'\b(japan|jpn|jap)\b|\(j\)', text): return 'japan'
    if re.search(r'\b(korea|kor)\b|\(k\)', text): return 'korea'
    return re.sub(r'\W+', '', text)[:40]


def parse_versions(html, game_slug=None):
    versions, seen_url, seen_region = [], set(), set()
    slug = (game_slug or '').lower()
    for href, label in VERSION_LINK_RE.findall(html or ''):
        text = clean_text(label)
        if not text or DEMO_RE.search(text): continue
        url = normalize_provider_url(href)
        link_slug = _download_slug(url)
        if slug and link_slug and link_slug != slug:
            continue
        if url in seen_url: continue
        region = _region_key(text)
        if region in seen_region: continue
        seen_url.add(url)
        seen_region.add(region)
        versions.append({'title': text[:160], 'filename': text[:160], 'url': url, 'region': region})
    return versions


def choose_version(versions):
    if not versions: raise ValueError('No non-demo versions were found.')
    for item in versions:
        if US_RE.search(item['title']): return item
    return versions[0]


def resolve_file(version_url, wait_seconds=20):
    """Fetch version page over ORIGIN_IP and return the signed CDN file URL."""
    version_url = normalize_provider_url(version_url)
    html = fetch_provider(version_url)
    match = DOWNLOAD_LINK_RE.search(html)
    if not match and wait_seconds > 0:
        time.sleep(min(max(wait_seconds, 1), 25))
        html = fetch_provider(version_url)
        match = DOWNLOAD_LINK_RE.search(html)
    if not match: raise ValueError('Provider returned no download link.')
    href = html_lib.unescape((match.group(1) or match.group(2) or '').replace('&amp;', '&'))
    if not href: raise ValueError('Provider returned no download link.')
    file_url = urljoin(BASE + '/', href)
    public_url(file_url)
    return file_url, version_url


def versions(game_url):
    page = fetch_provider(game_url)
    button = DOWNLOAD_ROM_RE.search(page)
    if not button: raise ValueError('No Download ROM button found for this game.')
    index_url = button.group(1)
    index = fetch_provider(index_url)
    result = parse_versions(index, game_slug=_download_slug(index_url))
    if not result: raise ValueError('No download versions found.')
    # USA first for the picker.
    result.sort(key=lambda item: (0 if item.get('region') == 'usa' else 1, item['title'].lower()))
    return result


def _poster_cache_load():
    try:
        data = json.loads(POSTER_CACHE_PATH.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _poster_cache_save(cache):
    try:
        POSTER_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        temporary = POSTER_CACHE_PATH.with_suffix('.tmp')
        temporary.write_text(json.dumps(cache, indent=0, ensure_ascii=True), encoding='utf-8')
        temporary.replace(POSTER_CACHE_PATH)
    except OSError:
        pass


def _normalize_poster_key(title):
    return re.sub(r'[^a-z0-9]+', '', (title or '').lower())


def _proxy_poster(url):
    if not url: return ''
    if url.startswith('/api/store/image'): return url
    return '/api/store/image?u=' + quote(url, safe='')


def _remember_posters(games):
    """Persist poster URLs from a catalog page so later pages do not re-scrape origin."""
    cache = _poster_cache_load()
    changed = False
    for game in games or []:
        title = game.get('title') or ''
        poster = game.get('poster') or ''
        if poster.startswith('/api/store/image'):
            continue
        key = _normalize_poster_key(title)
        if not key or not poster:
            continue
        if cache.get(key) != poster:
            cache[key] = poster
            changed = True
    if changed:
        _poster_cache_save(cache)


def _catalog_cache_key(query, page):
    raw = f'web|{(query or "").strip().lower()}|{int(page)}'
    return hashlib.sha1(raw.encode('utf-8')).hexdigest()


def _catalog_cache_path(key):
    return CATALOG_CACHE_DIR / f'{key}.json'


def _catalog_cache_get(query, page):
    key = _catalog_cache_key(query, page)
    now = time.time()
    with _CATALOG_LOCK:
        mem = _CATALOG_MEM.get(key)
        if mem and now - mem.get('fetched_at', 0) < CATALOG_TTL_SECONDS:
            return mem.get('payload')
    path = _catalog_cache_path(key)
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    fetched_at = data.get('fetched_at')
    payload = data.get('payload')
    if not isinstance(fetched_at, (int, float)) or not isinstance(payload, dict):
        return None
    if now - fetched_at >= CATALOG_TTL_SECONDS:
        return None
    with _CATALOG_LOCK:
        _CATALOG_MEM[key] = {'fetched_at': fetched_at, 'payload': payload}
    return payload


def _catalog_cache_put(query, page, payload):
    key = _catalog_cache_key(query, page)
    fetched_at = time.time()
    record = {'fetched_at': fetched_at, 'payload': payload}
    with _CATALOG_LOCK:
        _CATALOG_MEM[key] = record
    try:
        CATALOG_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = _catalog_cache_path(key)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(record, ensure_ascii=True), encoding='utf-8')
        temporary.replace(path)
    except OSError:
        pass


def _image_cache_paths(url):
    digest = hashlib.sha1(url.encode('utf-8')).hexdigest()
    base = IMAGE_CACHE_DIR / digest
    return base.with_suffix('.bin'), base.with_suffix('.meta.json')


def _image_cache_get(url):
    body_path, meta_path = _image_cache_paths(url)
    try:
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        age = time.time() - float(meta.get('fetched_at') or 0)
        if age >= IMAGE_TTL_SECONDS:
            return None
        body = body_path.read_bytes()
        mime = meta.get('mime') or 'application/octet-stream'
        if not body:
            return None
        return body, mime
    except (OSError, ValueError, TypeError):
        return None


def _image_cache_put(url, body, mime):
    body_path, meta_path = _image_cache_paths(url)
    try:
        IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        temporary = body_path.with_suffix('.tmp')
        temporary.write_bytes(body)
        temporary.replace(body_path)
        meta_path.write_text(
            json.dumps({'fetched_at': time.time(), 'mime': mime or 'application/octet-stream', 'url': url}, ensure_ascii=True),
            encoding='utf-8',
        )
    except OSError:
        pass


def lookup_poster(title, *, fetch=True):
    key = _normalize_poster_key(title)
    if not key: return ''
    cache = _poster_cache_load()
    hit = cache.get(key)
    if hit: return _proxy_poster(hit)
    if not fetch: return ''
    try:
        # Prefer a cached search page; only scrape origin when that misses.
        games = ((_catalog_cache_get(title, 1) or {}).get('games') or [])
        if not games:
            html = fetch_provider(provider_url(title, 1))
            games = parse_catalog(html)
            _remember_posters(games)
        poster = next((game.get('poster') for game in games if game.get('poster') and not str(game.get('poster')).startswith('/api/')), '')
        if not poster:
            for game in games:
                raw = game.get('poster') or ''
                if raw.startswith('/api/store/image?u='):
                    poster = unquote(raw.split('u=', 1)[-1])
                    break
        if not poster: return ''
        cache[key] = poster
        _poster_cache_save(cache)
        return _proxy_poster(poster)
    except Exception:
        return ''


def _fill_posters_background(titles):
    for title in titles:
        try: lookup_poster(title, fetch=True)
        except Exception: pass


def enrich_torrent_posters(result):
    cache = _poster_cache_load()
    missing = []
    for game in result.get('games') or []:
        if game.get('poster'): continue
        key = _normalize_poster_key(game.get('title'))
        if key and cache.get(key):
            game['poster'] = _proxy_poster(cache[key])
        elif game.get('title'):
            missing.append(game['title'])
    # Fill a few posters from URL cache / already-cached catalog pages only on the hot path.
    for title in missing[:4]:
        poster = lookup_poster(title, fetch=True)
        if not poster: continue
        key = _normalize_poster_key(title)
        for game in result.get('games') or []:
            if _normalize_poster_key(game.get('title')) == key:
                game['poster'] = poster
    rest = missing[4:12]
    if rest:
        threading.Thread(target=_fill_posters_background, args=(rest,), daemon=True).start()
    return result


def provider_cookie_header():
    return '; '.join(
        f'{cookie.name}={cookie.value}'
        for cookie in PROVIDER_COOKIES
        if (cookie.domain or '').endswith('romsfun.com') or not cookie.domain
    )


def find_torrent_match(title):
    """Best USA torrent match for a web title (CDN fail-safe + poster alignment)."""
    # Strip common web suffixes so "God of War II DVD5" still matches the torrent index.
    cleaned = re.sub(r'\b(dvd5|dvd9|cd\d+|disc\s*\d+)\b', '', title or '', flags=re.I)
    cleaned = re.sub(r'\([^)]*\)|\[[^\]]*\]', '', cleaned)
    needle = _normalize_poster_key(cleaned) or _normalize_poster_key(title)
    if not needle: return None
    data = torrent_index.catalog(cleaned or title or '', 1)
    best, score = None, 0
    for game in data.get('games') or []:
        key = _normalize_poster_key(game.get('title'))
        if not key: continue
        if key == needle or needle in key or key in needle:
            rank = 100 if key == needle else (80 if needle in key or key in needle else 50)
            if rank > score:
                best, score = game, rank
    return best


def find_torrent_token(title):
    match = find_torrent_match(title)
    return match.get('url') if match else None


def enrich_web_posters(games, *, allow_fetch=False):
    """Fill missing web posters from URL cache (and optionally a bounded origin scrape)."""
    missing = []
    for game in games:
        if game.get('poster'):
            continue
        title = game.get('title') or ''
        poster = lookup_poster(title, fetch=False)
        if not poster:
            match = find_torrent_match(title)
            if match and match.get('title'):
                poster = lookup_poster(match['title'], fetch=False)
                if poster:
                    game['torrent_title'] = match['title']
        if poster:
            game['poster'] = poster
        elif title:
            missing.append(title)
    if not allow_fetch or not missing:
        return games
    for title in missing[:4]:
        poster = lookup_poster(title, fetch=True)
        if not poster:
            match = find_torrent_match(title)
            if match and match.get('title'):
                poster = lookup_poster(match['title'], fetch=True)
        if not poster:
            continue
        key = _normalize_poster_key(title)
        for game in games:
            if _normalize_poster_key(game.get('title')) == key and not game.get('poster'):
                game['poster'] = poster
    rest = missing[4:12]
    if rest:
        threading.Thread(target=_fill_posters_background, args=(rest,), daemon=True).start()
    return games


def catalog(query='', page=1, source='web'):
    source = (source or 'web').lower()
    # Torrent catalog remains available for silent CDN fallback matching only.
    if source in ('torrent', 'local'):
        return enrich_torrent_posters(torrent_index.catalog(query, page))
    if source not in ('web', 'romsfun', 'provider', ''):
        raise ValueError('Unknown catalog source.')
    query = (query or '').strip()
    cached = _catalog_cache_get(query, page)
    if cached:
        games = [dict(game) for game in (cached.get('games') or [])]
        enrich_web_posters(games, allow_fetch=False)
        return {
            'games': games,
            'page': page,
            'pages': int(cached.get('pages') or 1),
            'query': query,
            'source': 'web',
            'cached': True,
        }
    url = provider_url(query, page)
    html = fetch_provider(url)
    games = parse_catalog(html)
    _remember_posters(games)
    for game in games:
        game['source'] = 'web'
        if game.get('poster'):
            game['poster'] = _proxy_poster(game['poster'])
    enrich_web_posters(games, allow_fetch=False)
    pages = parse_pages(html) if not query else max(page, parse_pages(html))
    payload = {'games': games, 'page': page, 'pages': pages or 1, 'query': query, 'source': 'web'}
    _catalog_cache_put(query, page, {
        'games': [dict(game) for game in games],
        'pages': pages or 1,
    })
    return payload


def provider_image(url):
    absolute = normalize_provider_url(url)
    path = urlsplit(absolute).path.lower()
    if '/wp-content/uploads/' not in path:
        raise ValueError('Only provider upload images can be proxied.')
    if not path.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
        raise ValueError('Unsupported provider image type.')
    hit = _image_cache_get(absolute)
    if hit:
        return hit
    body, mime = fetch_provider(absolute, binary=True, max_bytes=MAX_PROVIDER_IMAGE)
    _image_cache_put(absolute, body, mime)
    return body, mime


def connect_public(address, timeout=30, source_address=None):
    host, port = address
    addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError('The download host resolved to a private or local address.')
    failure = None
    for item in addresses:
        try:
            # Connect to the validated numeric address. TLS still verifies the
            # original hostname in HTTPSConnection, including its SNI name.
            return socket.create_connection((item[4][0], port), timeout, source_address)
        except OSError as error: failure = error
    raise failure or OSError('No public download address could be reached.')


class PublicHTTPSConnection(HTTPSConnection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._create_connection = connect_public


class PublicHTTPSHandler(HTTPSHandler):
    def https_open(self, req):
        return self.do_open(PublicHTTPSConnection, req, context=self._context)


class Redirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_url(url, extra_headers=None):
    public_url(url)
    if not hasattr(HTTP, 'opener'):
        HTTP.opener = build_opener(ProxyHandler({}), PublicHTTPSHandler(), Redirects(), HTTPCookieProcessor(COOKIES))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': BASE + '/',
        'Accept': 'application/octet-stream,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'identity',
        **(extra_headers or {}),
    }
    try:
        return HTTP.opener.open(Request(url, headers=headers), timeout=60)
    except HTTPError as error:
        if error.code in (401, 403, 429):
            raise ValueError(f'The provider refused this request (HTTP {error.code}). '
                             'Use Store, or Add game with a romsfun.com download page / local archive.') from None
        raise ValueError(f'The provider returned HTTP {error.code}. Try again later or use a fresh link.') from None
    except URLError as error:
        raise ValueError('Could not connect to the provider. Check your connection or add a downloaded archive.') from error


class Cancelled(Exception): pass


def interrupt_response(response):
    # Do not wait for a blocked HTTP read on the request handler thread.
    # urllib's socket is private API: close remains the fallback if unavailable.
    if response is None: return
    def close():
        try:
            transport = getattr(getattr(getattr(response, 'fp', None), 'raw', None), '_sock', None)
            if transport is not None: transport.shutdown(socket.SHUT_RDWR)
        except OSError: pass
        finally:
            try: response.close()
            except Exception: pass
    threading.Thread(target=close, daemon=True).start()



def jobs(state_lookup=None):
    with LOCK:
        result = []
        for identifier, original in list(JOBS.items()):
            job = dict(original)
            if state_lookup and job.get('game_id'):
                state = state_lookup(job['game_id'])
                if state: job.update(state)
            if job['status'] in ('failed', 'cancelled'):
                since = original.setdefault('finished_at', time.monotonic())
                if time.monotonic() - since > 15:
                    JOBS.pop(identifier, None); CONTROLS.pop(identifier, None)
                    continue
            else:
                original.pop('finished_at', None)
            if job['status'] == 'complete': job.pop('path', None); job['speed'] = 0
            job.pop('finished_at', None)
            result.append(job)
        return result


def update(identifier, **values):
    with LOCK:
        if identifier in JOBS: JOBS[identifier].update(values)


def control(identifier, action):
    if not isinstance(identifier, str) or not isinstance(action, str): raise ValueError('Invalid download control.')
    with TURN:
        job = JOBS.get(identifier)
        if not job: raise ValueError('Download no longer exists.')
        flags = CONTROLS.get(identifier)
        state = job['status']
        if action == 'remove' and state in ('complete', 'failed', 'cancelled'):
            JOBS.pop(identifier); CONTROLS.pop(identifier, None)
            return {'removed': True}
        if not flags or state not in ('queued', 'downloading', 'paused'):
            raise ValueError('This download has already entered installation. Use the game queue controls.')
        process = flags.get('process')
        if action == 'pause':
            if process is not None:
                raise ValueError('Pause is not available while the browser/torrent worker is active.')
            flags['generation'] = flags.get('generation', 0) + 1
            interrupt_response(flags.get('response'))
            flags['paused'] = True; job.update(status='paused', speed=0)
        elif action == 'resume':
            flags['paused'] = False; job.update(status='queued', speed=0)
        elif action in ('cancel', 'remove'):
            flags['generation'] = flags.get('generation', 0) + 1
            flags['cancelled'] = True
            interrupt_response(flags.get('response'))
            job.update(status='cancelled', speed=0, finished_at=time.monotonic())
        else: raise ValueError('Unknown download action.')
        TURN.notify_all()
    # Kill outside the lock so taskkill cannot stall other panel requests.
    if action in ('cancel', 'remove'):
        _kill_worker(process)
        with LOCK:
            job = JOBS.get(identifier) or {}
            return dict(job)
    with LOCK:
        job = JOBS.get(identifier) or {}
        return dict(job)


def is_provider_page(url):
    if not isinstance(url, str) or not url: return False
    parts = urlsplit(url)
    host = (parts.hostname or '').lower()
    if host not in ('romsfun.com', 'www.romsfun.com'): return False
    path = parts.path or ''
    return bool(re.search(rf'^/(roms/{PS2_SLUG}/[^/]+\.html|download/)', path, re.I))


def is_cdn_file_host(url):
    if not isinstance(url, str) or not url: return False
    host = (urlsplit(url).hostname or '').lower()
    return host.endswith('.romsfast.com') or host in ('romsfast.com', 'sto.romsfast.com')


def is_signed_cdn_url(url):
    """Hotlink ticket from the IP download page (?e=&s=)."""
    if not is_cdn_file_host(url): return False
    query = parse_qs(urlsplit(url).query)
    return bool(query.get('e') and query.get('s'))


def resolve_download_url(url):
    """Turn a romsfun game/version page or a direct file link into a public file URL."""
    if not isinstance(url, str) or not url: raise ValueError('Invalid download URL.')
    if url.startswith('torrent:'):
        entry = torrent_index.resolve_entry(url)
        return url, entry['title']
    parts = urlsplit(url)
    host = (parts.hostname or '').lower()
    if host in ('romsfun.com', 'www.romsfun.com'):
        provider = normalize_provider_url(url)
        if is_provider_page(provider):
            return provider, None
        raise ValueError('Use a PS2 game page, version link, or direct archive URL.')
    return public_url(url), None


def _normalize_twocaptcha_key(value):
    """Accept a browser-supplied key for one job; never persist it."""
    if value is None or value == '':
        return ''
    if not isinstance(value, str):
        raise ValueError('Invalid twocaptcha_api_key.')
    value = value.strip()
    if len(value) > 512 or any(ch in value for ch in '\0\r\n'):
        raise ValueError('Invalid twocaptcha_api_key.')
    return value


def start(data, root, importer):
    raw = data.get('url')
    password = data.get('password', DEFAULT_ARCHIVE_PASSWORD) or None
    twocaptcha_key = _normalize_twocaptcha_key(data.get('twocaptcha_api_key'))
    if password is not None and (not isinstance(password, str) or len(password) > 1024 or any(c in password for c in '\0\r\n')):
        raise ValueError('Invalid archive password.')
    url, resolved_title = resolve_download_url(raw)
    referer = BASE + '/'
    if isinstance(url, str) and url.startswith('torrent:'):
        entry = torrent_index.resolve_entry(url)
        ext = Path(entry['name']).suffix.lower() or '.bin'
        if ext not in EXTENSIONS: raise ValueError('Unsupported torrent file type.')
        title = data.get('title') or entry['title'] or Path(entry['name']).stem
        mode = 'torrent'
        payload = entry
    elif is_provider_page(url):
        # Same browser session: wait → parse #download-link → fetch href (no click).
        title = data.get('title') or resolved_title or 'Provider download'
        mode = 'browser'
        payload = {'url': url}
        ext = '.browser'
    else:
        if is_cdn_file_host(url) and not is_signed_cdn_url(url):
            raise ValueError(
                'CDN links expire. Use Store, or paste a romsfun.com download page '
                'into Add game so a fresh signed link can be resolved.'
            )
        name = unquote(Path(urlsplit(url).path).name)
        ext = Path(name).suffix.lower()
        if ext not in EXTENSIONS: raise ValueError('Use a direct disc or archive file link, a Store game, or a torrent entry.')
        title = data.get('title') or resolved_title or Path(name).stem
        if is_cdn_file_host(url):
            mode = 'cdn'
            payload = {'url': url, 'referer': data.get('referer') or referer}
            ext = '.browser'
        else:
            mode = 'direct'
            payload = {'url': url, 'referer': data.get('referer') or referer}
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120: raise ValueError('Enter a title under 121 characters.')
    with TURN:
        if sum(j['status'] in ('queued','downloading','paused','importing') for j in JOBS.values()) >= 16:
            raise ValueError('The download queue is full (16 transfers).')
        if len(JOBS) >= 64:
            oldest = next((key for key,j in JOBS.items() if j['status'] in ('complete','failed','cancelled')), None)
            if oldest: JOBS.pop(oldest); CONTROLS.pop(oldest, None)
        identifier = secrets.token_hex(16)
        detail = {
            'torrent': 'Torrent',
            'provider': 'Opening download page (origin IP)...',
            'cdn': 'Downloading signed CDN link...',
            'browser': 'Opening provider (origin IP)...',
        }.get(mode, '')
        JOBS[identifier] = {'id':identifier,'title':title.strip(),'status':'queued','bytes':0,'total':None,'speed':0,'detail':detail}
        CONTROLS[identifier] = {'paused':False,'cancelled':False}
        try:
            threading.Thread(
                target=download,
                args=(identifier, mode, payload, ext, password, Path(root), importer, twocaptcha_key),
                daemon=True,
            ).start()
        except RuntimeError:
            JOBS.pop(identifier, None); CONTROLS.pop(identifier, None)
            raise ValueError('Could not start the download worker. Try again after other transfers finish.') from None
        return dict(JOBS[identifier])


def _run_node_worker(script, job, flags, identifier, twocaptcha_key=''):
    node = node_executable()
    if not node: raise ValueError('Node.js is required for this download. Run Setup.cmd.')
    worker = Path(__file__).resolve().parents[1] / 'downloader' / script
    if not worker.is_file(): raise ValueError('Downloader worker is missing.')
    env = runtime_env()
    # Captcha key: Settings localStorage → request body → this field on stdin job JSON.
    # Never process.env.TWOCAPTCHA_API_KEY.
    payload = dict(job)
    if twocaptcha_key:
        payload['twocaptcha_api_key'] = twocaptcha_key
    else:
        payload.pop('twocaptcha_api_key', None)
    process = subprocess.Popen(
        [node, str(worker)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=str(worker.parent), env=env, text=True, encoding='utf-8', errors='replace', bufsize=1,
    )
    with TURN: flags['process'] = process
    try:
        process.stdin.write(json.dumps(payload))
        process.stdin.close()
        result = None
        while True:
            with TURN:
                if flags['cancelled']:
                    _kill_worker(process)
                    raise Cancelled()
                if flags['paused']:
                    _kill_worker(process)
                    raise ValueError('Pause is not available while the browser/torrent worker is active.')
            line = process.stdout.readline()
            if not line:
                break
            try: message = json.loads(line)
            except ValueError: continue
            event = message.get('event')
            if event == 'progress':
                update(identifier, bytes=int(message.get('bytes') or 0), total=message.get('total'), speed=int(message.get('speed') or 0))
            elif event == 'status':
                update(identifier, detail=str(message.get('message') or '')[:200])
            elif event == 'complete':
                result = message
            elif event == 'error':
                with TURN:
                    if flags['cancelled']:
                        raise Cancelled()
                raise ValueError(str(message.get('message') or 'Downloader failed.')[:500])
        with TURN:
            if flags['cancelled']:
                raise Cancelled()
        code = process.wait(timeout=30)
        err = (process.stderr.read() or '')[:500]
        with TURN:
            if flags['cancelled']:
                raise Cancelled()
        if code != 0 and not result:
            raise ValueError(err or 'Downloader failed.')
        if not result or not result.get('path'):
            raise ValueError('Downloader finished without a file.')
        return result
    finally:
        with TURN: flags.pop('process', None)
        # Ensure the worker (and any leftover torrent sockets) are gone — never keep seeding.
        _kill_worker(process)


def download(identifier, mode, payload, ext, password, root, importer, twocaptcha_key=''):
    global ACTIVE
    folder = root / 'downloads'
    destination = folder / identifier
    target = folder / (identifier + ('' if ext == '.browser' else ext))
    partial = target.with_suffix(target.suffix + '.part') if ext != '.browser' else None
    validator = None
    size = 0
    elapsed = 0.0
    try:
        folder.mkdir(exist_ok=True)
        with TURN:
            flags = CONTROLS.setdefault(identifier, {'paused':False,'cancelled':False})
        if mode == 'provider':
            with TURN:
                while True:
                    if flags['cancelled']: raise Cancelled()
                    first = next((key for key in JOBS if key in CONTROLS and not CONTROLS[key]['paused'] and not CONTROLS[key]['cancelled'] and JOBS[key]['status'] in ('queued','downloading')), None)
                    if not flags['paused'] and ACTIVE is None and first == identifier: break
                    TURN.wait(0.25)
                ACTIVE = identifier
                update(identifier, status='downloading', detail='Opening download page (origin IP)...')
            try:
                update(identifier, detail='Opening download page (origin IP)...')
                try:
                    file_url, referer = resolve_file(payload['url'], wait_seconds=20)
                    update(identifier, detail='Parsed CDN link; starting transfer...')
                    mode = 'cdn'
                    payload = {'url': file_url, 'referer': referer, 'cookies': provider_cookie_header()}
                except ValueError as resolve_error:
                    # Fall back to browser HTML parse (still no click) if origin-IP page fails.
                    update(identifier, detail='Origin-IP parse failed; opening provider in browser...')
                    try:
                        result = _run_node_worker('worker.mjs', {
                            'url': payload['url'],
                            'destination': str(destination),
                        }, flags, identifier, twocaptcha_key=twocaptcha_key)
                        path = Path(result['path'])
                        if not path.is_file(): raise ValueError('Downloader did not produce a file.')
                        update(identifier, status='importing', path=str(path), bytes=int(result.get('bytes') or path.stat().st_size), total=result.get('total'), speed=0, detail='Installing...')
                        game = importer({
                            'path': str(path),
                            'title': JOBS[identifier]['title'],
                            'password': password,
                            'download_job_id': identifier,
                        })
                        update(identifier, status='complete', game_id=game['id'], detail='')
                        return
                    except ValueError as browser_error:
                        token = find_torrent_token(JOBS[identifier]['title'])
                        if not token:
                            raise ValueError(
                                f'CDN download failed and no torrent match was found. {browser_error or resolve_error}'
                            ) from None
                        update(identifier, detail='CDN blocked briefly; switching to matched torrent...')
                        payload = torrent_index.resolve_entry(token)
                        if payload.get('title'):
                            update(identifier, title=payload['title'])
                        mode = 'torrent'
            finally:
                with TURN:
                    ACTIVE = None
                    TURN.notify_all()
            if mode not in ('cdn', 'torrent'):
                return
        if mode in ('cdn', 'browser', 'torrent'):
            with TURN:
                while True:
                    if flags['cancelled']: raise Cancelled()
                    first = next((key for key in JOBS if key in CONTROLS and not CONTROLS[key]['paused'] and not CONTROLS[key]['cancelled'] and JOBS[key]['status'] in ('queued','downloading')), None)
                    if not flags['paused'] and ACTIVE is None and first == identifier: break
                    TURN.wait(0.25)
                ACTIVE = identifier
                update(identifier, status='downloading', detail='Starting worker...')
            try:
                result = None
                worker_error = None
                if mode == 'cdn':
                    update(identifier, detail='Downloading signed CDN link...')
                    try:
                        result = _run_node_worker('worker.mjs', {
                            'mode': 'cdn',
                            'url': payload['url'],
                            'referer': payload.get('referer') or BASE + '/',
                            'cookies': payload.get('cookies') or '',
                            'destination': str(destination),
                        }, flags, identifier, twocaptcha_key=twocaptcha_key)
                    except ValueError as error:
                        worker_error = error
                        match = find_torrent_match(JOBS[identifier]['title'])
                        token = match.get('url') if match else None
                        if not token:
                            raise ValueError(
                                f'CDN download failed and no torrent match was found. {error}'
                            ) from None
                        update(identifier, detail='CDN blocked briefly; switching to matched torrent...')
                        payload = torrent_index.resolve_entry(token)
                        if payload.get('title'):
                            update(identifier, title=payload['title'])
                        mode = 'torrent'
                elif mode == 'browser':
                    update(identifier, detail='Opening provider (origin IP); parse CDN link...')
                    try:
                        result = _run_node_worker('worker.mjs', {
                            'url': payload['url'],
                            'destination': str(destination),
                        }, flags, identifier, twocaptcha_key=twocaptcha_key)
                    except ValueError as error:
                        worker_error = error
                        match = find_torrent_match(JOBS[identifier]['title'])
                        token = match.get('url') if match else None
                        if not token:
                            raise ValueError(
                                f'CDN download failed and no torrent match was found. {error}'
                            ) from None
                        update(identifier, detail='CDN blocked briefly; switching to matched torrent...')
                        payload = torrent_index.resolve_entry(token)
                        if payload.get('title'):
                            update(identifier, title=payload['title'])
                        mode = 'torrent'
                if mode == 'torrent':
                    result = _run_node_worker('torrent_worker.mjs', {
                        'torrent': payload['torrent'],
                        'fileIndex': payload['file_index'],
                        'destination': str(destination) + (Path(payload['name']).suffix.lower() or '.bin'),
                    }, flags, identifier, twocaptcha_key=twocaptcha_key)
                if not result:
                    raise worker_error or ValueError('Downloader finished without a file.')
                path = Path(result['path'])
                if not path.is_file(): raise ValueError('Downloader did not produce a file.')
                update(identifier, status='importing', path=str(path), bytes=int(result.get('bytes') or path.stat().st_size), total=result.get('total'), speed=0, detail='Installing...')
                game = importer({
                    'path': str(path),
                    'title': JOBS[identifier]['title'],
                    'password': password,
                    'download_job_id': identifier,
                })
                update(identifier, status='complete', game_id=game['id'], detail='')
            finally:
                with TURN:
                    ACTIVE = None
                    TURN.notify_all()
            return
        url = payload['url']
        referer = payload.get('referer') or BASE + '/'
        while True:
            with TURN:
                while True:
                    if flags['cancelled']: raise Cancelled()
                    first = next((key for key in JOBS if key in CONTROLS and not CONTROLS[key]['paused'] and not CONTROLS[key]['cancelled'] and JOBS[key]['status'] in ('queued','downloading')), None)
                    if not flags['paused'] and ACTIVE is None and first == identifier: break
                    TURN.wait(0.25)
                ACTIVE = identifier
                generation = flags.get('generation', 0)
                update(identifier,status='downloading', detail='Transferring...')
            started = time.monotonic()
            segment_bytes = 0
            try:
                if size and not validator:
                    size = 0
                headers = {'Referer': referer}
                if size:
                    headers.update({'Range': f'bytes={size}-', 'If-Range': validator})
                with open_url(url, headers) as response:
                    with TURN: flags['response'] = response
                    status = getattr(response, 'status', 200)
                    etag = response.headers.get('ETag','')
                    current_validator = etag if etag and not etag.startswith('W/') else response.headers.get('Last-Modified')
                    length = int(response.headers.get('Content-Length','0')) or None
                    if size and status == 206:
                        match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', response.headers.get('Content-Range',''))
                        if not match or int(match[1]) != size or int(match[2]) < size or int(match[2]) >= int(match[3]) or (length and length != int(match[2])-size+1) or current_validator != validator:
                            raise ValueError('The resumed file changed or returned an invalid byte range.')
                        total = int(match[3])
                    elif status == 200:
                        size = 0; total = length
                    else: raise ValueError('Unexpected download response status.')
                    validator = current_validator
                    if total is not None and not 0 < total <= MAX_DOWNLOAD: raise ValueError('Download exceeds 16 GiB.')
                    if 'text/html' in response.headers.get('Content-Type','').lower(): raise ValueError('The link returned a website page instead of a file.')
                    if shutil.disk_usage(folder).free < (max(0,total-size) if total else MAX_DOWNLOAD) + 512*1024**2: raise ValueError('Not enough free space.')
                    update(identifier,total=total,bytes=size)
                    with partial.open('ab' if size else 'wb') as output:
                        while True:
                            with TURN:
                                if flags['cancelled']: raise Cancelled()
                                if flags['paused'] or flags.get('generation', 0) != generation: break
                            chunk = response.read(256*1024)
                            with TURN:
                                if flags['cancelled']: raise Cancelled()
                            if not chunk: break
                            size += len(chunk)
                            if size > MAX_DOWNLOAD or elapsed+time.monotonic()-started > 4*3600: raise ValueError('Download exceeded its size or time limit.')
                            output.write(chunk)
                            segment_bytes += len(chunk)
                            update(identifier,bytes=size,speed=int(segment_bytes/max(.001,time.monotonic()-started)))
                    with TURN:
                        if flags['cancelled']: raise Cancelled()
                        if flags['paused'] or flags.get('generation', 0) != generation: continue
                        if not size or (total is not None and size != total): raise ValueError('Download is incomplete.')
                        # Atomically close cancellation before handing ownership to the installer.
                        update(identifier,status='importing',path=str(target),speed=0)
                partial.replace(target)
                game = importer({
                    'path': str(target),
                    'title': JOBS[identifier]['title'],
                    'password': password,
                    'download_job_id': identifier,
                })
                update(identifier,status='complete',game_id=game['id'])
                break
            except Exception:
                with TURN:
                    if flags['cancelled']: raise Cancelled()
                    if flags.get('generation', 0) != generation: continue
                raise
            finally:
                elapsed += time.monotonic()-started
                with TURN:
                    ACTIVE = None
                    flags.pop('response', None)
                    if flags['paused'] and not flags['cancelled']: update(identifier,status='paused',speed=0)
                    TURN.notify_all()
    except Cancelled:
        if partial is not None: partial.unlink(missing_ok=True)
        target.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        update(identifier,status='cancelled',speed=0,finished_at=time.monotonic())
    except Exception as error:
        if partial is not None: partial.unlink(missing_ok=True)
        target.unlink(missing_ok=True)
        for leftover in folder.glob(identifier + '.*'):
            leftover.unlink(missing_ok=True)
        update(identifier,status='failed',speed=0,error=str(error)[:500],finished_at=time.monotonic())
    finally:
        password = None
