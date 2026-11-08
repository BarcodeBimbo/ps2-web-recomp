"""Unit tests for nightly download → build → heal → verify orchestrator."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import nightly_pipeline as np


class NightlyPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "games").mkdir()
        (self.root / "build").mkdir()
        (self.root / "logs" / "locks").mkdir(parents=True)
        (self.root / "logs" / "autonomous-pipeline").mkdir(parents=True)
        self.game_id = "a" * 32
        self.game = self.root / "games" / self.game_id
        self.game.mkdir()
        (self.game / "disc.iso").write_bytes(b"ISO fixture")
        (self.game / "identity.json").write_text(
            json.dumps({"title": "Fixture Title"}), encoding="utf-8"
        )
        native_dir = self.root / "build" / f"native-{self.game_id}"
        native_dir.mkdir()
        (native_dir / "ps2run.exe").write_bytes(b"MZ")

        self.patches = [
            patch.object(np, "ROOT", self.root),
            patch.object(np, "GAMES", self.root / "games"),
            patch.object(np, "LOCKS", self.root / "logs" / "locks"),
            patch.object(np, "PIPELINE_LOG", self.root / "logs" / "autonomous-pipeline"),
            patch.object(np, "SCRIPTS", self.root / "scripts"),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.temp.cleanup()

    def test_download_skipped_when_iso_present(self):
        row = np.stage_download(self.game_id)
        self.assertEqual(row["status"], "ok")
        self.assertEqual(row["action"], "skipped_present")
        self.assertEqual(row["bytes"], len(b"ISO fixture"))

    def test_download_fails_without_iso(self):
        (self.game / "disc.iso").unlink()
        row = np.stage_download(self.game_id)
        self.assertEqual(row["status"], "fail")
        self.assertEqual(row["action"], "missing_iso")

    def test_build_skipped_present(self):
        row = np.stage_build(self.game_id, skip_build=False, force_build=False)
        self.assertEqual(row["status"], "ok")
        self.assertEqual(row["action"], "skipped_present")

    def test_build_respects_protected_lock(self):
        (self.root / "build" / f"native-{self.game_id}" / "ps2run.exe").unlink()
        lock = self.root / "logs" / "locks" / f"native-{self.game_id}.lock"
        # Use Hitman-style protected id for prefix check via lock_is_protected on path name
        hitman = "a2116d2ac08a7be4db4e8455ad58d2e5"
        hitman_lock = self.root / "logs" / "locks" / f"web-{hitman}.lock"
        hitman_lock.write_text("owner=test\n", encoding="utf-8")
        self.assertTrue(np.lock_is_protected(hitman_lock))

        lock.write_text("owner=test\n", encoding="utf-8")
        with patch.object(np, "cmake_ninja_live", return_value=True):
            row = np.stage_build(self.game_id, skip_build=False, force_build=True)
        self.assertEqual(row["status"], "skipped")
        self.assertEqual(row["action"], "lock_skip")

    def test_run_game_chains_stages(self):
        heal_report = {
            "symptoms": [],
            "actions_taken": [],
            "actions_planned": [],
        }
        verify_row = {
            "status": "pass",
            "log": "logs/autonomous-pipeline/fixture.log",
            "health": {"status": "ok"},
            "matrix": {"skipped": True},
        }
        with patch.object(np, "stage_heal", return_value={"status": "ok", "action": "dry_run", "symptoms": [], "actions_taken": 0, "actions_planned": 0, "issues": None}) as heal, patch.object(
            np, "stage_verify", return_value={"status": "pass", "action": "autonomous_verify", "log": verify_row["log"], "health": "ok"}
        ) as verify, patch("store_pipeline_hooks.log_pipeline_event"):
            row = np.run_game(
                self.game_id,
                frames=60,
                skip_build=True,
                force_build=False,
                dry_heal=True,
            )
        self.assertEqual(row["status"], "pass")
        self.assertEqual(row["stages"]["download"]["action"], "skipped_present")
        self.assertEqual(row["stages"]["build"]["action"], "skipped_present")
        heal.assert_called_once()
        verify.assert_called_once()

    def test_write_artifacts(self):
        summary = {
            "stamp": "20261107T000000Z",
            "overall": "pass",
            "frames": 60,
            "skip_build": True,
            "dry_heal": True,
            "results": [
                {
                    "game_id": self.game_id,
                    "status": "pass",
                    "stages": {
                        "download": {"action": "skipped_present"},
                        "build": {"action": "skipped_present"},
                        "heal": {"action": "dry_run"},
                        "verify": {"status": "pass", "log": "x.log"},
                    },
                }
            ],
        }
        json_path, log_path = np.write_artifacts(summary)
        self.assertTrue(json_path.is_file())
        self.assertTrue(log_path.is_file())
        self.assertIn("overall=pass", log_path.read_text(encoding="utf-8"))

    def test_chrome_serve_pass(self):
        class Resp:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def getcode(self):
                return 200

        with patch("urllib.request.urlopen", return_value=Resp()):
            row = np.stage_chrome_serve(self.game_id, panel_base="http://127.0.0.1:8620")
        self.assertEqual(row["status"], "pass")
        self.assertFalse(row["manual_patch_steps"])
        self.assertEqual(len(row["assets"]), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
