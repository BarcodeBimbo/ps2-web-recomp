"""HTTP handler and malformed-disc regressions, no sockets or game files required."""
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import serve
import panel
import mobile
from disc import Image, open_source

class Connection:
    def __init__(self, request):
        self.input = io.BytesIO(request)
        self.output = io.BytesIO()
    def makefile(self, mode, *args): return self.input
    def sendall(self, data): self.output.write(data)
    def settimeout(self, value): pass

class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        serve.BUILD = str(self.root)
        serve.DISC = str(self.root / 'disc.iso')
        serve.ROOMS.clear()
        (self.root / 'ps2web.js').write_text('test')
        (self.root / 'secret.txt').write_text('private')
        (self.root / 'disc.iso').write_bytes(bytes(range(256)))
        self.server = SimpleNamespace(server_address=('127.0.0.1', 8620))
    def tearDown(self): self.temp.cleanup()
    def call(self, method, path, body=b'', headers=None, handler=serve.Handler):
        headers = {'Host': '127.0.0.1:8620', **(headers or {})}
        if body: headers.setdefault('Content-Length', str(len(body)))
        request = f'{method} {path} HTTP/1.1\r\n' + ''.join(f'{k}: {v}\r\n' for k,v in headers.items()) + '\r\n'
        connection = Connection(request.encode() + body)
        handler(connection, ('127.0.0.1', 1234), self.server)
        response = connection.output.getvalue()
        return int(response.split(b' ')[1]), response
    def test_host_origin_and_fetch_metadata(self):
        self.assertEqual(self.call('GET','/ps2web.js',headers={'Host':'evil.test'})[0],403)
        self.assertEqual(self.call('GET','/ps2web.js',headers={'Sec-Fetch-Site':'cross-site'})[0],403)
        self.assertEqual(self.call('POST','/room',headers={'Origin':'https://evil.test'})[0],403)
        self.assertEqual(self.call('POST','/room',headers={'Transfer-Encoding':'chunked'})[0],400)
    def test_static_and_ranges(self):
        self.assertEqual(self.call('GET','/secret.txt')[0],404)
        self.assertEqual(self.call('GET','/%2e%2e/secret.txt')[0],404)
        code, data = self.call('GET','/disc.iso',headers={'Range':'bytes=4-7'})
        self.assertEqual(code,206); self.assertTrue(data.endswith(bytes(range(4,8))))
        for value in ['bytes=-4','bytes=300-','bytes=9-2','bytes=0-1,4-5']:
            self.assertEqual(self.call('GET','/disc.iso',headers={'Range':value})[0],416)
        self.assertIn(b'X-Content-Type-Options: nosniff',data)
    def test_symlink_escape(self):
        with tempfile.NamedTemporaryFile() as secret:
            try: (self.root / 'ps2web.data').symlink_to(secret.name)
            except OSError: self.skipTest('Symbolic links are unavailable on this platform.')
            self.assertEqual(self.call('GET','/ps2web.data')[0],404)
    def test_room_limits(self):
        for _ in range(serve.MAX_ROOMS): self.assertEqual(self.call('POST','/room')[0],200)
        self.assertEqual(self.call('POST','/room')[0],429)
        code = next(iter(serve.ROOMS))
        for _ in range(serve.MAX_MESSAGES):
            self.assertEqual(self.call('POST',f'/room/{code}/host', b'{}')[0],200)
        self.assertEqual(self.call('POST',f'/room/{code}/host',b'{}')[0],429)
        self.assertEqual(self.call('POST',f'/room/{code}/host',headers={'Content-Length':'-1'})[0],400)
        self.assertEqual(self.call('PUT','/vu1/AAAAAAAAAAAAAAAA_AAAA.bin',headers={'Content-Length':'bad'})[0],400)
    def test_mobile_authorization(self):
        self.server.access_token = 'private-token'
        self.server.game_id = 'a'*32
        for route in ['/api/games','/play/'+'a'*32+'/disc.iso']:
            self.assertEqual(self.call('GET',route,handler=mobile.MobilePlayer)[0],403)
        code, response = self.call('GET','/connect?key=private-token',handler=mobile.MobilePlayer)
        self.assertEqual(code,303); self.assertIn(b'Secure; HttpOnly; SameSite=Strict', response)
        headers={'Cookie':'__Host-ps2session=private-token'}
        self.assertEqual(self.call('GET','/api/games',headers=headers,handler=mobile.MobilePlayer)[0],404)
        self.assertEqual(self.call('POST','/api/games',headers=headers,handler=mobile.MobilePlayer)[0],405)
        self.assertEqual(self.call('GET','/connect?key=%C3%A9',handler=mobile.MobilePlayer)[0],403)
    def test_cue_cannot_escape(self):
        cue = self.root/'test.cue';cue.write_text('FILE "../secret.bin" BINARY')
        with self.assertRaises(ValueError):
            with open_source(str(cue)): pass
    def test_malformed_iso_record(self):
        data=bytearray(24*2048);p=16*2048
        data[p:p+7]=b'\x01CD001\x01';struct.pack_into('<I',data,p+80,24)
        struct.pack_into('<I',data,p+158,20);struct.pack_into('<I',data,p+166,2048)
        data[20*2048]=3
        file=self.root/'bad.iso';file.write_bytes(data)
        image=Image(file)
        try:
            with self.assertRaises(ValueError): list(image.files())
        finally: image.file.close()

if __name__ == '__main__': unittest.main()
