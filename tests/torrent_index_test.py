"""Torrent catalog search regressions."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import torrent_index


class TorrentIndexTests(unittest.TestCase):
    def test_catalog_search_and_resolve(self):
        result = torrent_index.catalog('god of war', 1)
        self.assertEqual(result['source'], 'torrent')
        self.assertGreater(len(result['games']), 0)
        self.assertTrue(all(game['source'] == 'torrent' for game in result['games']))
        first = result['games'][0]
        entry = torrent_index.resolve_entry(first['url'])
        self.assertTrue(Path(entry['torrent']).is_file())
        self.assertIn('God of War', entry['title'])

    def test_rejects_bad_tokens(self):
        with self.assertRaises(ValueError):
            torrent_index.resolve_entry('http://example.com')
        with self.assertRaises(ValueError):
            torrent_index.resolve_entry('torrent:999999')


if __name__ == '__main__':
    unittest.main(verbosity=2)
