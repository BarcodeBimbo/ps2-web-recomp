#!/usr/bin/env python3
"""HTTP byte-range regressions used by the browser disc-streaming path."""
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import serve  # noqa: E402


class ServeRangeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.build = root / 'build'
        self.build.mkdir()
        self.disc = root / 'disc.iso'
        self.disc.write_bytes(b'PS2-TEST-DISC')
        serve.BUILD = str(self.build)
        serve.DISC = str(self.disc)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), serve.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.connection = HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.temp.cleanup()

    def test_existing_player_glue_gets_compatibility_prefix_in_workers(self):
        glue = self.build / 'ps2web.js'
        glue.write_text('/* existing compiled player */')
        self.connection.request('GET', '/ps2web.js?build=old', headers={'Accept-Encoding': 'gzip'})
        response = self.connection.getresponse()
        body = response.read()
        self.assertEqual(response.status, 200)
        self.assertIn(b'cyberarcade.ps2.fixedUpload', body)
        self.assertTrue(body.endswith(glue.read_bytes()))
        self.assertEqual(int(response.getheader('Content-Length')), len(body))
        self.assertIsNone(response.getheader('Content-Encoding'))
        self.connection.request('HEAD', '/ps2web.js?build=old')
        response = self.connection.getresponse()
        self.assertEqual(response.status, 200)
        self.assertEqual(response.read(), b'')
        self.assertEqual(int(response.getheader('Content-Length')), len(body))

    def test_single_byte_range_returns_exact_206_response(self):
        self.connection.request('GET', '/disc.iso', headers={'Range': 'bytes=0-0'})
        response = self.connection.getresponse()
        body = response.read()
        self.assertEqual(response.status, 206)
        self.assertEqual(response.getheader('Content-Range'), 'bytes 0-0/13')
        self.assertEqual(response.getheader('Accept-Ranges'), 'bytes')
        self.assertEqual(body, b'P')

    def test_full_range_returns_requested_slice(self):
        self.connection.request('GET', '/disc.iso', headers={'Range': 'bytes=5-8'})
        response = self.connection.getresponse()
        self.assertEqual(response.status, 206)
        self.assertEqual(response.getheader('Content-Range'), 'bytes 5-8/13')
        self.assertEqual(response.read(), b'EST-')

    def test_unsatisfiable_range_returns_416(self):
        self.connection.request('GET', '/disc.iso', headers={'Range': 'bytes=99-100'})
        response = self.connection.getresponse()
        self.assertEqual(response.status, 416)
        self.assertEqual(response.getheader('Content-Range'), 'bytes */13')
        self.assertEqual(response.read(), b'')

    def test_head_advertises_ranges_and_exact_length(self):
        self.connection.request('HEAD', '/disc.iso')
        response = self.connection.getresponse()
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader('Content-Length'), '13')
        self.assertEqual(response.getheader('Accept-Ranges'), 'bytes')
        self.assertEqual(response.read(), b'')


if __name__ == '__main__':
    unittest.main(verbosity=2)
