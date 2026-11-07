"""Run store browser-mode download against a synthetic worker result."""
import json, os, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import store


class Bridge(unittest.TestCase):
    def test_download_import_ipc(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            store.JOBS.clear()
            identifier = 'a' * 32
            store.JOBS[identifier] = {'id': identifier, 'title': 'Fixture', 'status': 'queued'}
            calls = []

            def importer(data):
                self.assertEqual(Path(data['path']).read_bytes(), b'fixture')
                self.assertEqual(data['password'], 'secret')
                calls.append(data)
                return {'id': 'b' * 32}

            def fake_worker(script, job, flags, job_id):
                out = Path(job['destination'] + '.iso')
                out.write_bytes(b'fixture')
                return {'event': 'complete', 'bytes': 7, 'total': 7, 'path': str(out)}

            with patch.object(store, '_run_node_worker', side_effect=fake_worker):
                store.download(
                    identifier,
                    'browser',
                    {'url': 'https://romsfun.com/roms/playstation-2/fixture.html'},
                    '.browser',
                    'secret',
                    root,
                    importer,
                )
            self.assertEqual(store.JOBS[identifier]['status'], 'complete')
            self.assertEqual(len(calls), 1)
            self.assertNotIn('secret', json.dumps(store.jobs()))


if __name__ == '__main__':
    unittest.main()
