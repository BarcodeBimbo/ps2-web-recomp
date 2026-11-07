#!/usr/bin/env python3
"""Serves a web build and a disc image with HTTP range requests.

usage: serve.py <build dir> <disc image> [port] [--host address] [--record <dir for unrecorded VU1 programs>]

It also relays the messages that connect a host page to the guests it invites
(/room), so a friend can play along from another browser.
"""

import http.server
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import os
import re
import secrets
import shutil
import sys
import threading
import time

RECORD = None
ROOMS = {}
ROOMS_CHANGED = threading.Condition()
ROOM_PATH = re.compile(r'^/room(?:/([A-Z2-9]{6})/([a-z0-9]{1,16}))?$')
ROOM_LETTERS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
ROOM_IDLE = 3600
MAX_ROOMS = 8
MAX_PEERS = 4
MAX_MESSAGES = 64
MAX_MESSAGE_BYTES = 16384
TYPES = {'.html': 'text/html', '.js': 'text/javascript', '.wasm': 'application/wasm', '.data': 'application/octet-stream'}


class BoundedHTTPServer(http.server.ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 32

    def __init__(self, *args, **kwargs):
        self.slots = threading.BoundedSemaphore(32)
        super().__init__(*args, **kwargs)

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()


class Handler(http.server.BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(30)

    def parse_request(self):
        if not super().parse_request():
            return False
        host, port = self.server.server_address[:2]
        allowed = getattr(self.server, 'allowed_hosts', {f'{host}:{port}', f'localhost:{port}'})
        if len(self.headers.get_all('Host', [])) != 1 or self.headers.get('Host') not in allowed or self.headers.get('Sec-Fetch-Site') == 'cross-site':
            self.send_error(403)
            return False
        if self.command in ('POST', 'PUT'):
            scheme = getattr(self.server, 'scheme', 'http')
            origin = self.headers.get('Origin')
            if origin is not None and origin != f'{scheme}://{self.headers.get("Host")}':
                self.send_error(403)
                return False
        if self.headers.get('Transfer-Encoding') or len(self.headers.get_all('Content-Length', [])) > 1:
            self.send_error(400)
            return False
        return True

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'no-referrer')
        super().end_headers()

    def handle(self):
        try:
            super().handle()
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            # A browser can leave while a room poll or file response is pending.
            self.close_connection = True

    def target(self):
        path = self.path.split('?', 1)[0]
        if path in ('/', '/index.html'):
            path = '/ps2web.html'
        if path == '/disc.iso':
            return DISC
        if path.endswith('/'):
            path += 'index.html'
        name = unquote(path.lstrip('/'))
        # Expose only player outputs, never arbitrary files or linked secrets.
        if not re.fullmatch(r'(?:ps2web(?:[.][a-zA-Z0-9_-]+)+|boot[.]txt)', name):
            return None
        root = Path(BUILD).resolve()
        full = root / name
        return str(full) if full.is_file() and full.resolve().is_relative_to(root) else None

    def headers_for(self, path, length, encoding=None):
        self.send_header('Content-Type', TYPES.get(os.path.splitext(path)[1], 'application/octet-stream'))
        if encoding:
            self.send_header('Content-Encoding', encoding)
            self.send_header('Vary', 'Accept-Encoding')
        self.send_header('Content-Length', str(length))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
        self.end_headers()

    def send_json(self, value, status=200):
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def room_get(self, code, me):
        match = re.search(r'after=(\d+)', self.path)
        after = int(match.group(1)) if match and len(match.group(1)) <= 8 else 0
        deadline = time.time() + 20
        with ROOMS_CHANGED:
            while True:
                room = ROOMS.get(code)
                if room is None:
                    self.send_json({'error': 'no such room'}, 404)
                    return
                room['seen'] = time.time()
                if me not in room['inboxes'] and len(room['inboxes']) >= MAX_PEERS:
                    self.send_json({'error': 'room is full'}, 429)
                    return
                inbox = room['inboxes'].setdefault(me, [])
                if after > len(inbox):
                    self.send_json({'error': 'invalid cursor'}, 400)
                    return
                left = deadline - time.time()
                if len(inbox) > after or left <= 0:
                    messages = inbox[after:]
                    break
                ROOMS_CHANGED.wait(left)
        self.send_json({'messages': messages, 'next': after + len(messages)})

    def do_POST(self):
        match = ROOM_PATH.match(self.path.split('?', 1)[0])
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            self.send_error(400)
            return
        if length < 0:
            self.send_error(400)
            return
        if not match or length > MAX_MESSAGE_BYTES:
            self.send_error(404 if not match else 413)
            return
        body = self.rfile.read(length)
        code, to = match.groups()
        with ROOMS_CHANGED:
            now = time.time()
            for old in [c for c, r in ROOMS.items() if now - r['seen'] > ROOM_IDLE]:
                del ROOMS[old]
            if not code:
                if len(ROOMS) >= MAX_ROOMS:
                    self.send_json({'error': 'room limit reached'}, 429)
                    return
                code = ''.join(secrets.choice(ROOM_LETTERS) for _ in range(6))
                while code in ROOMS:
                    code = ''.join(secrets.choice(ROOM_LETTERS) for _ in range(6))
                ROOMS[code] = {'inboxes': {}, 'seen': now}
                result = {'room': code}
            elif code in ROOMS:
                try:
                    message = json.loads(body)
                except ValueError:
                    message = None
                if not isinstance(message, dict):
                    self.send_json({'error': 'bad message'}, 400)
                    return
                inboxes = ROOMS[code]['inboxes']
                if (to not in inboxes and len(inboxes) >= MAX_PEERS) or len(inboxes.get(to, [])) >= MAX_MESSAGES:
                    self.send_json({'error': 'room message limit reached; create a new room'}, 429)
                    return
                inboxes.setdefault(to, []).append(message)
                ROOMS[code]['seen'] = now
                ROOMS_CHANGED.notify_all()
                result = {}
            else:
                self.send_json({'error': 'no such room'}, 404)
                return
        self.send_json(result)

    def serve_player_js(self, head=False):
        path = self.target()
        if not path or Path(path).name != 'ps2web.js':
            return False
        # Pthread workers import the same glue URL. Prefixing it patches both
        # realms and repairs existing builds without translating games again.
        compat = Path(__file__).resolve().parents[1] / 'web/gpu_upload_compat.js'
        if not compat.is_file():
            return False
        # Read the full body before headers so a permission/IO failure cannot
        # advertise Content-Length and then only ship the compat prefix
        # (Chrome: net::ERR_CONTENT_LENGTH_MISMATCH → engine script abort).
        try:
            body = compat.read_bytes() + b'\n' + Path(path).read_bytes()
        except OSError:
            self.send_error(500, 'Player script is unreadable. Check permissions on the web build output.')
            return True
        self.send_response(200)
        self.headers_for(path, len(body))
        if not head:
            self.wfile.write(body)
        return True

    def do_HEAD(self):
        if self.serve_player_js(head=True):
            return
        path = self.target()
        if not path:
            self.send_error(404)
            return
        self.send_response(200)
        self.headers_for(path, os.path.getsize(path))

    def do_GET(self):
        match = ROOM_PATH.match(self.path.split('?', 1)[0])
        if match and match.group(1):
            self.room_get(*match.groups())
            return
        if self.serve_player_js():
            return
        path = self.target()
        if not path:
            self.send_error(404)
            return
        packed = path + '.gz'
        if ('Range' not in self.headers and 'gzip' in self.headers.get('Accept-Encoding', '') and os.path.isfile(packed)
                and os.path.getmtime(packed) >= os.path.getmtime(path)
                and Path(packed).resolve().parent == Path(path).resolve().parent):
            self.send_response(200)
            self.headers_for(path, os.path.getsize(packed), 'gzip')
            with open(packed, 'rb') as f:
                shutil.copyfileobj(f, self.wfile, 1 << 20)
            return
        size = os.path.getsize(path)
        requested = self.headers.get('Range')
        match = re.fullmatch(r'bytes=([0-9]{1,20})-([0-9]{0,20})', requested or '')
        if requested is not None and not match:
            self.send_response(416)
            self.send_header('Content-Range', 'bytes */%d' % size)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        start, end = 0, size - 1
        if match:
            start = int(match.group(1))
            end = min(int(match.group(2)) if match.group(2) else size - 1, size - 1)
            if start > end:
                self.send_response(416)
                self.send_header('Content-Range', 'bytes */%d' % size)
                self.send_header('Content-Length', '0')
                self.end_headers()
                return
            self.send_response(206)
            self.send_header('Content-Range', 'bytes %d-%d/%d' % (start, end, size))
        else:
            self.send_response(200)
        self.headers_for(path, end - start + 1)
        with open(path, 'rb') as f:
            f.seek(start)
            left = end - start + 1
            while left > 0:
                chunk = f.read(min(left, 1 << 20))
                if not chunk:
                    break
                self.wfile.write(chunk)
                left -= len(chunk)

    def do_PUT(self):
        match = re.match(r'^/vu1/([0-9A-F]{16}_[0-9A-F]{4}\.bin)$', self.path.split('?', 1)[0])
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            self.send_error(400)
            return
        if not RECORD or not match or length != 16384:
            self.send_error(501 if not RECORD else 400)
            return
        data = self.rfile.read(length)
        if len(data) != length:
            self.send_error(400)
            return
        target = os.path.join(RECORD, match.group(1))
        if not os.path.exists(target):
            os.makedirs(RECORD, exist_ok=True)
            with open(target, 'wb') as f:
                f.write(data)
            print('recorded', match.group(1), flush=True)
        self.send_response(201)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def log_message(self, fmt, *args):
        pass


def main():
    global RECORD, BUILD, DISC
    RECORD = None
    if '--record' in sys.argv:
        at = sys.argv.index('--record')
        RECORD = os.path.abspath(sys.argv[at + 1])
        del sys.argv[at:at + 2]
    HOST = '127.0.0.1'
    if '--host' in sys.argv:
        at = sys.argv.index('--host')
        HOST = sys.argv[at + 1]
        del sys.argv[at:at + 2]
    BUILD = os.path.abspath(sys.argv[1])
    DISC = os.path.abspath(sys.argv[2])
    PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 8620
    print('serving %s and %s on http://%s:%d/' % (BUILD, DISC, HOST, PORT))
    BoundedHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
