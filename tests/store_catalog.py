"""Catalog URL builder and HTML parsers for the IP-bypass Store."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import store

FIXTURE = Path(__file__).resolve().parent / 'fixtures' / 'catalog-cards.html'


class CatalogTests(unittest.TestCase):
    def test_provider_url_browse_and_search(self):
        self.assertEqual(store.provider_url('', 1), 'https://romsfun.com/roms/playstation-2/')
        self.assertEqual(store.provider_url('', 2), 'https://romsfun.com/roms/playstation-2/page/2/')
        self.assertEqual(store.provider_url('god of war', 1), 'https://romsfun.com/?s=god+of+war')
        self.assertEqual(store.provider_url('god of war', 2), 'https://romsfun.com/page/2/?s=god+of+war')
        with self.assertRaises(ValueError):
            store.provider_url('x' * 121, 1)
        with self.assertRaises(ValueError):
            store.provider_url('', 0)

    def test_parse_catalog_fixture(self):
        html = FIXTURE.read_text(encoding='utf-8')
        games = store.parse_catalog(html)
        self.assertGreaterEqual(len(games), 2)
        self.assertEqual(games[0]['title'], 'JoJo no Kimyou na Bouken: Phantom Blood')
        self.assertTrue(games[0]['url'].endswith('/jojo-no-kimyou-na-bouken-phantom-blood.html'))
        self.assertIn('/wp-content/uploads/', games[0]['poster'])

    def test_parse_pages_and_versions(self):
        html = '''
        <a href="https://romsfun.com/roms/playstation-2/page/2/">2</a>
        <a href="https://romsfun.com/roms/playstation-2/page/546/">last</a>
        <a href="https://romsfun.com/download/game-1/1">Game (Europe)</a>
        <a href="https://romsfun.com/download/game-1/5">Game (USA)</a>
        <a href="https://romsfun.com/download/game-1/5">Game (USA)</a>
        <a href="https://romsfun.com/download/other-game/3">Other (USA)</a>
        <a href="https://romsfun.com/download/game-1/7">Game (USA) (Demo)</a>
        '''
        self.assertEqual(store.parse_pages(html), 546)
        versions = store.parse_versions(html, game_slug='game-1')
        self.assertEqual([item['title'] for item in versions], ['Game (Europe)', 'Game (USA)'])
        self.assertEqual(store.choose_version(versions)['title'], 'Game (USA)')

    def test_resolve_download_url_direct_file(self):
        with patch.object(store, 'public_url', side_effect=lambda url: url):
            url, title = store.resolve_download_url('https://example.com/disc.zip')
        self.assertEqual(url, 'https://example.com/disc.zip')
        self.assertIsNone(title)

    def test_catalog_rewrites_posters_through_image_proxy(self):
        html = FIXTURE.read_text(encoding='utf-8')
        with patch.object(store, 'fetch_provider', return_value=html):
            result = store.catalog('', 1, source='web')
        self.assertEqual(result['page'], 1)
        self.assertEqual(result['source'], 'web')
        self.assertTrue(result['games'][0]['poster'].startswith('/api/store/image?u='))

    def test_fetch_provider_uses_origin_ip(self):
        seen = {}

        class FakeResponse:
            status = 200
            def getheader(self, name, default=None):
                return 'text/html; charset=utf-8' if name == 'Content-Type' else default
            def read(self, size=-1):
                if getattr(self, 'done', False):
                    return b''
                self.done = True
                return b'<html>ok</html>'

        class FakeConn:
            def __init__(self, *args, **kwargs):
                seen['args'] = args
                seen['kwargs'] = kwargs
            def request(self, method, path, headers=None):
                seen['method'] = method
                seen['path'] = path
                seen['headers'] = headers
            def getresponse(self):
                return FakeResponse()
            def close(self):
                pass

        with patch.object(store, 'OriginHTTPSConnection', FakeConn):
            text = store.fetch_provider('https://romsfun.com/roms/playstation-2/')
        self.assertEqual(text, '<html>ok</html>')
        self.assertEqual(seen['path'], '/roms/playstation-2/')
        self.assertEqual(seen['headers']['Host'], 'romsfun.com')
        self.assertEqual(store.ORIGIN_IP, '199.127.62.112')


if __name__ == '__main__':
    unittest.main(verbosity=2)
