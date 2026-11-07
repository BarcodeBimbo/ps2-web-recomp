#!/usr/bin/env python3
"""Panel queue isolation and worker-failure regressions; no toolchain needed."""
from collections import deque
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import panel  # noqa: E402


class FakeBuildThread:
    started = []

    def __init__(self, target, args, name):
        self.target = target
        self.args = args
        self.name = name

    def start(self):
        self.started.append((self.args[0]['id'], self.args[4]))


class PanelQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old = {
            'ROOT': panel.ROOT,
            'GAMES': panel.GAMES,
            'BUILDING': panel.BUILDING,
            'QUEUE': panel.QUEUE,
            'PROGRESS': panel.PROGRESS,
        }
        panel.ROOT = self.root
        panel.GAMES = self.root / 'games'
        panel.GAMES.mkdir()
        panel.BUILDING = {}
        panel.QUEUE = deque()
        panel.PROGRESS = {}
        FakeBuildThread.started = []

    def tearDown(self):
        for name, value in self.old.items():
            setattr(panel, name, value)
        self.temp.cleanup()

    def test_concurrent_enqueues_reserve_distinct_slots(self):
        games = []
        for index in range(10):
            game_id = f'{index + 1:032x}'
            (panel.GAMES / game_id).mkdir()
            games.append({'id': game_id, 'title': f'Game {index}', 'status': 'new'})

        # Create request threads before substituting the build-worker thread
        # factory. Each request enters enqueue concurrently; build workers are
        # captured rather than launched so the scheduling outcome is stable.
        request_threads = [threading.Thread(target=panel.enqueue, args=(game,)) for game in games]
        with patch.object(panel.threading, 'Thread', FakeBuildThread):
            for worker in request_threads:
                worker.start()
            for worker in request_threads:
                worker.join(timeout=5)
                self.assertFalse(worker.is_alive(), 'enqueue request did not finish')

        self.assertEqual(set(panel.BUILDING.values()), set(range(panel.BUILD_LIMIT)))
        self.assertEqual(len(panel.BUILDING), panel.BUILD_LIMIT)
        self.assertEqual(len(panel.QUEUE), 10 - panel.BUILD_LIMIT)
        self.assertEqual(len(FakeBuildThread.started), panel.BUILD_LIMIT)
        self.assertEqual(len({slot for _, slot in FakeBuildThread.started}), panel.BUILD_LIMIT)


    def test_blank_archive_password_is_normalized_to_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            games = root / 'games'
            games.mkdir()
            source = root / 'game.zip'
            source.write_bytes(b'not parsed by import validation')
            with patch.object(panel, 'GAMES', games), patch.object(panel, 'enqueue') as enqueue:
                result = panel.import_game({'path': str(source), 'password': ''})
            self.assertEqual(result['status'], 'building')
            self.assertIsNone(enqueue.call_args.args[4])

    def test_unexpected_worker_exception_marks_game_failed(self):
        game_id = 'a' * 32
        folder = panel.GAMES / game_id
        folder.mkdir()
        game = {'id': game_id, 'title': 'Worker test', 'status': 'building'}
        panel.BUILDING[game_id] = 0
        panel.PROGRESS[game_id] = {'stage': 'Starting build'}

        with patch.object(panel.subprocess, 'Popen', side_effect=ValueError('synthetic worker failure')):
            panel.build(game, None, 3600, 8, 0)

        self.assertEqual(game['status'], 'failed')
        self.assertIn('synthetic worker failure', game['error'])
        self.assertNotIn(game_id, panel.BUILDING)
        self.assertNotIn(game_id, panel.PROGRESS)
        saved = json.loads(panel.metadata(game_id).read_text(encoding='utf-8'))
        self.assertEqual(saved['status'], 'failed')


if __name__ == '__main__':
    unittest.main(verbosity=2)
