"""Download/import and rebuild publication regressions using synthetic files."""
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import store
import windows_port
from store_pipeline_hooks import (
    begin_install_manifest,
    finalize_post_build,
    gate_inline_verify,
    gate_strict_ready,
)
from urllib.error import HTTPError



class Response(io.BytesIO):
    def __init__(self, data=b'ISO fixture', advertised=None):
        super().__init__(data)
        self.headers = {'Content-Length': str(len(data) if advertised is None else advertised), 'Content-Type': 'application/octet-stream'}


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        store.JOBS.clear(); store.CONTROLS.clear()
    def tearDown(self): self.temp.cleanup()
    def run_download(self, response, importer):
        store.JOBS['a'] = {'id': 'a', 'title': 'Fixture', 'status': 'queued'}
        with patch.object(store, 'open_url', return_value=response), patch.object(store.shutil, 'disk_usage', return_value=SimpleNamespace(free=1 << 40)):
            store.download('a', 'direct', {'url': 'https://example.com/disc.iso'}, '.iso', 'temporary secret', self.root, importer)
        return store.jobs()[0]
    def test_download_finishes_before_import_and_password_is_not_persisted(self):
        seen = []
        def importer(data):
            self.assertEqual(Path(data['path']).read_bytes(), b'ISO fixture')
            self.assertEqual(data['password'], 'temporary secret')
            self.assertEqual(data.get('download_job_id'), 'a')
            seen.append(data)
            return {'id': 'b' * 32}
        job = self.run_download(Response(), importer)
        self.assertEqual(job['status'], 'complete')
        self.assertEqual(len(seen), 1)
        self.assertNotIn('temporary secret', json.dumps(job))
        self.assertFalse(list(self.root.rglob('*.part')))
    def test_truncated_download_never_enters_library(self):
        job = self.run_download(Response(advertised=9999), lambda data: self.fail('Partial file was imported'))
        self.assertEqual(job['status'], 'failed')
        self.assertFalse(list(self.root.rglob('*.iso')))
        self.assertFalse(list(self.root.rglob('*.part')))
    def test_import_failure_removes_completed_download(self):
        def importer(data): raise ValueError('Build queue is full')
        job = self.run_download(Response(), importer)
        self.assertEqual(job['status'], 'failed')
        self.assertFalse(Path(job['path']).exists())
    def test_local_download_destinations_are_rejected(self):
        with patch.object(store.socket, 'getaddrinfo', return_value=[(2,1,6,'',('127.0.0.1',443))]):
            with self.assertRaisesRegex(ValueError, 'Private'): store.public_url('https://localhost/disc.iso')

    def test_store_default_password_and_explicit_override(self):
        with patch.object(store, 'public_url', side_effect=lambda url:url), patch.object(store.threading, 'Thread') as worker:
            for supplied, expected in [({}, 'romsfun.com'), ({'password': 'custom'}, 'custom'), ({'password': ''}, None)]:
                store.JOBS.clear()
                store.start({'url': 'https://example.com/disc.zip', **supplied}, self.root, lambda _: None)
                self.assertEqual(worker.call_args.kwargs['args'][4], expected)
                self.assertNotIn('password', store.jobs()[0])

    def test_provider_page_queues_origin_ip_resolver(self):
        with patch.object(store.threading, 'Thread') as worker:
            store.JOBS.clear()
            store.start({'url': 'https://romsfun.com/download/game-1/5', 'title': 'Fixture'}, self.root, lambda _: None)
        mode, payload, ext = worker.call_args.kwargs['args'][1:4]
        self.assertEqual(mode, 'browser')
        self.assertEqual(payload['url'], 'https://romsfun.com/download/game-1/5')
        self.assertEqual(ext, '.browser')

    def test_signed_cdn_url_is_allowed(self):
        self.assertTrue(store.is_signed_cdn_url(
            'https://sto.romsfast.com/PS2-Redump/Game%20(USA).zip?e=1794032318&s=abc'))
        self.assertFalse(store.is_signed_cdn_url('https://sto.romsfast.com/PS2-Redump/Game.zip'))

    def test_torrent_entry_queues_torrent_worker(self):
        entry = {'torrent': 'C:/t.torrent', 'file_index': 3, 'name': 'Game (USA).7z', 'title': 'Game', 'size': 10}
        with patch.object(store.torrent_index, 'resolve_entry', return_value=entry), patch.object(store.threading, 'Thread') as worker:
            store.JOBS.clear()
            store.start({'url': 'torrent:3', 'title': 'Game'}, self.root, lambda _: None)
        mode, payload, ext = worker.call_args.kwargs['args'][1:4]
        self.assertEqual(mode, 'torrent')
        self.assertEqual(payload['file_index'], 3)
        self.assertEqual(ext, '.7z')

    def test_provider_denial_has_a_useful_local_import_recovery(self):
        opener = SimpleNamespace(open=lambda *a, **kw: (_ for _ in ()).throw(
            HTTPError('https://example.com', 403, 'Forbidden', {}, None)))
        with patch.object(store, 'public_url'), patch.object(store.HTTP, 'opener', opener, create=True):
            with self.assertRaisesRegex(ValueError, 'HTTP 403.*Add game|HTTP 403.*Torrent'):
                store.open_url('https://example.com/disc.zip')
    def prepare(self):
        game = self.root / 'games' / 'fixture'
        game.mkdir(parents=True)
        (game / 'core.elf').write_bytes(b'ELF fixture')
        (game / 'disc.iso').write_bytes(b'ISO fixture')
        web = self.root / 'build' / 'web-fixture'
        web.mkdir(parents=True)
        (web / 'boot.txt').write_text('boot fixture')
        (web / 'ps2web.html').write_text('old working player')
        return web
    def test_rebuild_refreshes_old_generated_tail_calls(self):
        self.prepare()
        for folder in ['modules','overlays']:(self.root/'games/fixture'/folder).mkdir()
        with patch.object(windows_port,'ROOT',self.root),patch.object(windows_port,'cmake') as configure,patch.object(windows_port.subprocess,'run') as run:
            windows_port.refresh_translation('fixture',self.root/'games/fixture/core.elf',{})
        self.assertEqual(configure.call_args.kwargs['target'],'eerecomp')
        command=list(map(str,run.call_args.args[0]))
        for argument in ['--entries','--modules','--overlays','--out']:self.assertIn(argument,command)
        self.assertTrue((self.root/'games/fixture/entries.txt').is_file())

    def test_compile_failure_keeps_old_player(self):
        web = self.prepare()
        with patch.object(windows_port, 'ROOT', self.root), patch.object(windows_port, 'refresh_translation'), patch.object(windows_port, 'cmake', side_effect=RuntimeError('compile failed')):
            with self.assertRaises(RuntimeError): windows_port.build_web('fixture')
        self.assertEqual((web / 'ps2web.html').read_text(), 'old working player')
    def test_complete_build_publishes_together_and_versions_assets(self):
        web = self.prepare()
        def cmake(folder, *args, **kwargs):
            for ext in ('html','js','wasm','data'): (folder / ('ps2web.' + ext)).write_text('new ' + ext)
        with patch.object(windows_port, 'ROOT', self.root), patch.object(windows_port, 'refresh_translation'), patch.object(windows_port, 'cmake', side_effect=cmake):
            windows_port.build_web('fixture')
        self.assertEqual((web / 'ps2web.html').read_text(), 'new html')
        self.assertTrue(json.loads((web / 'build.json').read_text())['id'])
        self.assertFalse(web.with_name('web-fixture-previous').exists())

    def test_install_manifest_round_trip(self):
        game = self.root / 'games' / ('f' * 32)
        game.mkdir(parents=True)
        iso = self.root / 'incoming.iso'
        iso.write_bytes(b'ISO fixture for manifest')
        begin_install_manifest(
            game,
            game_id='f' * 32,
            title='Fixture',
            source=iso,
            download_job_id='deadbeef',
        )
        manifest_path = game / 'install_manifest.json'
        self.assertTrue(manifest_path.is_file())
        payload = json.loads(manifest_path.read_text(encoding='utf-8'))
        self.assertEqual(payload['download_job_id'], 'deadbeef')
        self.assertEqual(payload['source']['bytes'], len(b'ISO fixture for manifest'))
        self.assertEqual(len(payload['source']['sha256']), 64)
        health = {'status': 'ok', 'reasons': [], 'warnings': []}
        with patch('store_pipeline_hooks.ROOT', self.root):
            finalize_post_build('f' * 32, health, full_install=True)
        updated = json.loads(manifest_path.read_text(encoding='utf-8'))
        self.assertIsNotNone(updated['timestamps']['build_completed_at'])
        self.assertEqual(updated['health_status'], 'ok')

    def test_strict_verify_blocks_warn_status(self):
        health = {'status': 'warn', 'reasons': [], 'warnings': ['no_explore_or_smoke_log']}
        with patch.dict('os.environ', {'PS2_STRICT_VERIFY': '1'}):
            with self.assertRaisesRegex(RuntimeError, 'Strict verify'):
                gate_strict_ready(health, full_install=True)
        with patch.dict('os.environ', {}, clear=True):
            gate_strict_ready(health, full_install=True)

    def test_inline_verify_skipped_unless_env(self):
        with patch.dict('os.environ', {}, clear=True):
            self.assertIsNone(gate_inline_verify('a' * 32, full_install=True))
        with patch.dict('os.environ', {'PS2_INLINE_VERIFY': '1'}):
            self.assertIsNone(gate_inline_verify('a' * 32, full_install=False))

    def test_inline_verify_blocks_fail_status(self):
        fail_row = {'status': 'fail', 'health': {'status': 'fail', 'reasons': ['near_zero_prims']}}
        with patch.dict('os.environ', {'PS2_INLINE_VERIFY': '1', 'PS2_INLINE_VERIFY_FRAMES': '60'}):
            with patch('store_pipeline_hooks.run_inline_autonomous_verify', return_value=fail_row):
                with self.assertRaisesRegex(RuntimeError, 'Inline autonomous_verify failed'):
                    gate_inline_verify('b' * 32, full_install=True)

    def test_finalize_runs_inline_verify_and_updates_manifest(self):
        game_id = 'c' * 32
        game = self.root / 'games' / game_id
        game.mkdir(parents=True)
        iso = self.root / 'incoming.iso'
        iso.write_bytes(b'ISO fixture')
        begin_install_manifest(game, game_id=game_id, title='Fixture', source=iso, download_job_id='job1')
        pass_row = {
            'status': 'pass',
            'log': 'logs/autonomous-pipeline/fixture.log',
            'inline_frames': 60,
        }
        health = {'status': 'ok', 'reasons': [], 'warnings': []}
        with patch('store_pipeline_hooks.ROOT', self.root), patch.dict(
            'os.environ', {'PS2_INLINE_VERIFY': '1', 'PS2_INLINE_VERIFY_FRAMES': '60'}
        ), patch('store_pipeline_hooks.run_inline_autonomous_verify', return_value=pass_row) as smoke:
            finalize_post_build(game_id, health, full_install=True)
            smoke.assert_called_once_with(game_id)
        updated = json.loads((game / 'install_manifest.json').read_text(encoding='utf-8'))
        self.assertTrue(updated['pipeline']['autonomous_verify_inline'])
        self.assertEqual(updated['pipeline']['autonomous_verify_status'], 'pass')
        self.assertIsNotNone(updated['timestamps'].get('inline_verify_at'))


if __name__ == '__main__': unittest.main(verbosity=2)
