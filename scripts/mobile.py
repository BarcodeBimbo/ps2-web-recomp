"""Read-only HTTPS access to one ready game. Desktop administration stays local."""
import argparse
import html
import ipaddress
import json
import os
import shutil
import socket
import subprocess
import threading
import tempfile
import hmac
from http.cookies import SimpleCookie, CookieError
import re
import secrets
import ssl
from urllib.parse import parse_qs, urlsplit

# Embedded Windows Python uses an isolated ._pth and omits the script directory.
import sys
from pathlib import Path
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
if not (SCRIPTS / 'panel.py').is_file():
    raise SystemExit('Missing scripts/panel.py. Extract the complete project ZIP, then run Setup.cmd again.')
import panel
from serve import Handler, BoundedHTTPServer


class MobilePlayer(panel.Panel):
    def parse_request(self):
        # Panel's fixed loopback Host is intentionally replaced by the explicit
        # HTTPS hostname on this read-only listener, never on the admin panel.
        return Handler.parse_request(self)

    def authorized(self):
        try:
            cookie = SimpleCookie(self.headers.get('Cookie', ''))
            value = cookie.get('__Host-ps2session')
            return bool(value and hmac.compare_digest(value.value, self.server.access_token))
        except (CookieError, TypeError):
            return False

    def allowed_route(self):
        match = panel.GAME_PATH.fullmatch(self.route)
        if not match or '/room' in self.route: return False
        selected = getattr(self.server, 'game_id', None)
        if selected is not None: return match[1] == selected
        game = panel.get_game(match[1])
        return bool(game and game['status'] == 'ready')

    def do_GET(self):
        if self.route == '/connect':
            token = parse_qs(urlsplit(self.path).query).get('key', [''])[0]
            if not hmac.compare_digest(token.encode(), self.server.access_token.encode()):
                self.send_error(403)
                return
            self.send_response(303)
            self.send_header('Set-Cookie', f'__Host-ps2session={token}; Secure; HttpOnly; SameSite=Strict; Path=/')
            self.send_header('Location', f'/play/{self.server.game_id}/?touch' if getattr(self.server, 'game_id', None) else '/')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        if not self.authorized():
            self.send_error(403, 'Open the private connection link printed on the PC.')
            return
        if self.route == '/' and getattr(self.server, 'game_id', None) is None:
            cards = []
            with panel.LOCK:
                ready = []
                for path in panel.GAMES.iterdir():
                    if panel.ID.fullmatch(path.name) and (game := panel.get_game(path.name)) and game['status'] == 'ready':
                        ready.append(game)
                ready.sort(key=lambda game: game['title'].casefold())
                for game in ready:
                    title = html.escape(game['title'])
                    poster = panel.game_poster(game['id'], schedule=True)
                    media = (f'<img src="/play/{game["id"]}/poster.image" alt="" loading="lazy">'
                             if poster else
                             '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
                             '<circle cx="12" cy="12" r="2"/><path d="m15 5 2 3M7 16l2 3"/></svg>')
                    cards.append(
                        f'<article data-title="{html.escape(game["title"].casefold())}">'
                        f'<div class="cover">{media}<a href="/play/{game["id"]}/?touch" aria-label="Play {title}"></a></div>'
                        f'<div class="card-body"><h2>{title}</h2><span class="badge ready">Ready</span>'
                        f'<a class="play" href="/play/{game["id"]}/?touch">Play</a></div></article>')
            count = len(cards)
            counts = '1 ready game' if count == 1 else f'{count} ready games'
            games = ''.join(cards) or '<div class="empty">No ready games on this PC yet.</div>'
            template = (panel.ROOT / 'web/mobile.html').read_text(encoding='utf-8')
            if '__GAMES__' not in template or '__COUNTS__' not in template:
                self.send_error(500, 'Mobile library template is incomplete.')
                return
            body = template.replace('__COUNTS__', counts).replace('__GAMES__', games).encode()
            self.send_response(200);self.headers_for('mobile.html', len(body));self.wfile.write(body)
            return
        if not self.allowed_route() or '/room' in self.route:
            self.send_error(404)
            return
        super().do_GET()

    def do_HEAD(self):
        if not self.authorized() or not self.allowed_route():
            self.send_error(403)
            return
        super().do_HEAD()

    def do_POST(self):
        self.send_error(405)

    do_PUT = do_POST
    do_DELETE = do_POST


class MobileServer(BoundedHTTPServer):
    # TLS handshake runs inside the bounded request thread, not the accept loop.
    def process_request_thread(self, request, address):
        wrapped = request
        try:
            request.settimeout(10)
            wrapped = self.tls.wrap_socket(request, server_side=True)
            self.finish_request(wrapped, address)
        except (OSError, ssl.SSLError):
            pass
        finally:
            self.shutdown_request(wrapped)
            self.slots.release()


def lan_address():
    # UDP connect selects the route/interface without transmitting application data.
    candidates=[]
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(('1.1.1.1', 80));candidates.append(probe.getsockname()[0])
    except OSError:pass
    try:candidates.extend(item[4][0] for item in socket.getaddrinfo(socket.gethostname(),None,socket.AF_INET))
    except OSError:pass
    networks = tuple(ipaddress.ip_network(net) for net in ('10.0.0.0/8','172.16.0.0/12','192.168.0.0/16'))
    for address in candidates:
        ip=ipaddress.ip_address(address)
        if any(ip in net for net in networks):return address
    raise ValueError('No private LAN interface found. Connect the PC to Wi-Fi or Ethernet and restart Setup.cmd.')


def prepare_certificate(address):
    folder = panel.ROOT / 'tools/mobile'
    folder.mkdir(parents=True, exist_ok=True)
    tool = panel.ROOT / 'tools/msys64/clang64/bin/openssl.exe'
    executable = str(tool) if tool.is_file() else shutil.which('openssl')
    if not executable: raise ValueError('OpenSSL is unavailable. Re-run Setup.cmd to repair the native tools.')
    ca, ca_key = folder/'phone-ca.crt', folder/'phone-ca.key'
    def command(*args):
        subprocess.run([executable,*map(str,args)], check=True, stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=60)
    if not ca.is_file() or not ca_key.is_file():
        command('req','-x509','-newkey','rsa:2048','-nodes','-days','3650','-sha256',
                '-subj','/CN=CyberArcade Local Mobile CA','-addext','basicConstraints=critical,CA:TRUE',
                '-addext','keyUsage=critical,keyCertSign,cRLSign','-keyout',ca_key,'-out',ca)
    # Regenerate the leaf on startup so LAN IP changes and certificate expiry are handled.
    with tempfile.TemporaryDirectory(dir=folder) as temporary:
        stage = Path(temporary);key=stage/'server.key';csr=stage/'server.csr';cert=stage/'server.crt'
        extensions=stage/'extensions.cnf'
        extensions.write_text('subjectAltName=IP:'+address+'\nbasicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\n')
        command('req','-new','-newkey','rsa:2048','-nodes','-subj','/CN=CyberArcade Mobile','-keyout',key,'-out',csr)
        command('x509','-req','-in',csr,'-CA',ca,'-CAkey',ca_key,'-set_serial',str(secrets.randbits(128) or 1),
                '-days','30','-sha256','-extfile',extensions,'-out',cert)
        key.replace(folder/'server.key');cert.replace(folder/'server.crt')
    if os.name != 'nt':
        os.chmod(ca_key,0o600);os.chmod(folder/'server.key',0o600)
    return folder/'server.crt', folder/'server.key'


def start_automatic():
    address = lan_address()
    cert, key = prepare_certificate(address)
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.minimum_version = ssl.TLSVersion.TLSv1_2;tls.load_cert_chain(cert,key)
    server = MobileServer((address,0), MobilePlayer)  # OS assigns a free, random port.
    server.tls=tls;server.scheme='https';server.game_id=None
    authority=f'{address}:{server.server_port}'
    server.allowed_hosts={authority};server.access_token=secrets.token_urlsafe(32)
    threading.Thread(target=server.serve_forever, daemon=True, name='mobile-lan').start()
    return server, {'status':'ready','url':f'https://{authority}/connect?key={server.access_token}',
                    'address':address,'port':server.server_port,
                    'help':'Same Wi-Fi/LAN. Trust the local phone certificate once for WebGPU and threaded gameplay. Allow Python through Windows Firewall on Private networks if prompted.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game_id', help='32-character ID from the game URL')
    parser.add_argument('--host', required=True, help='PC LAN IPv4 address to bind, e.g. 192.168.1.20')
    parser.add_argument('--hostname', required=True, help='DNS hostname or IPv4 address on the TLS certificate')
    parser.add_argument('--port', type=int, default=8621)
    parser.add_argument('--cert', required=True, help='PEM certificate trusted by the phone')
    parser.add_argument('--key', required=True, help='PEM private key; keep on the PC')
    args = parser.parse_args()
    if not panel.ID.fullmatch(args.game_id) or not re.fullmatch(r'[a-zA-Z0-9.-]+', args.hostname):
        parser.error('Invalid game ID or hostname.')
    game = panel.get_game(args.game_id)
    if not game or game.get('status') != 'ready':
        parser.error('Build this game in the desktop library first.')
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(args.cert, args.key)
    authority = args.hostname if args.port == 443 else f'{args.hostname}:{args.port}'
    with MobileServer((args.host, args.port), MobilePlayer) as server:
        server.tls = context
        server.scheme = 'https'
        server.allowed_hosts = {authority}
        server.access_token = secrets.token_urlsafe(32)
        server.game_id = args.game_id
        print(f'Private mobile link: https://{authority}/connect?key={server.access_token}', flush=True)
        print('Keep this window open. Closing it revokes access. Administration remains on localhost.', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    try:
        main()
    except OSError as error:
        raise SystemExit(f'Mobile server could not start: {error}. Check the certificate/key paths, bind address and port.') from None
