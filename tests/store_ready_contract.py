"""Store pull → Chrome playable contract (no manual patch steps)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import store_ready_contract as src


class StoreReadyContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "games").mkdir()
        (self.root / "build").mkdir()
        (self.root / "scripts").mkdir()
        (self.root / "runtime" / "src" / "iop").mkdir(parents=True)
        (self.root / "runtime" / "src" / "gs").mkdir(parents=True)
        (self.root / "verification" / "recovery").mkdir(parents=True)

        (self.root / "runtime" / "src" / "iop" / "cdvdfsv.cpp").write_text(
            "// Match retail cdvdfsv cdvd_readee: fixture\n", encoding="utf-8"
        )
        (self.root / "runtime" / "src" / "iop" / "cdvd.cpp").write_text(
            "sceCdDiskReady fixture\n", encoding="utf-8"
        )
        (self.root / "runtime" / "src" / "gs" / "gs.hpp").write_text(
            "inline int xyoffset_component(uint64_t reg, bool ofy);\n", encoding="utf-8"
        )
        (self.root / "verification" / "recovery" / "game-fix-registry.json").write_text(
            json.dumps(
                {
                    "global_runtime": {
                        "disc_fix_applied": ["R3_readee", "R4D1_DiskReady"],
                    }
                }
            ),
            encoding="utf-8",
        )
        (self.root / "scripts" / "store_pipeline_hooks.py").write_text(
            "def finalize_post_build():\n    pass\n"
            "def begin_install_manifest():\n    pass\n"
            "def gate_inline_verify():\n    pass\n",
            encoding="utf-8",
        )
        (self.root / "scripts" / "panel.py").write_text(
            "from store_pipeline_hooks import finalize_post_build, begin_install_manifest\n",
            encoding="utf-8",
        )

        self.game_id = "a" * 32
        self.game = self.root / "games" / self.game_id
        self.game.mkdir()
        (self.game / "library.json").write_text(
            json.dumps({"id": self.game_id, "title": "Fixture", "status": "ready"}),
            encoding="utf-8",
        )
        (self.game / "disc.iso").write_bytes(b"ISO")
        web = self.root / "build" / f"web-{self.game_id}"
        web.mkdir()
        (web / "ps2web.html").write_text("<html>player</html>", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_pass_when_ready_web_and_patches(self):
        row = src.evaluate_game(self.game_id, root=self.root, require_http=False)
        self.assertEqual(row["status"], "pass")
        self.assertTrue(row["checks"]["web_player"])
        self.assertTrue(row["checks"]["global_patches_preapplied"])

    def test_fail_when_manual_patch_file_present(self):
        (self.game / "patches.pending").write_text("do this by hand\n", encoding="utf-8")
        row = src.evaluate_game(self.game_id, root=self.root, require_http=False)
        self.assertEqual(row["status"], "fail")
        self.assertFalse(row["checks"]["no_manual_patch_files"])

    def test_fail_without_web_player(self):
        (self.root / "build" / f"web-{self.game_id}" / "ps2web.html").unlink()
        row = src.evaluate_game(self.game_id, root=self.root, require_http=False)
        self.assertEqual(row["status"], "fail")
        self.assertFalse(row["checks"]["web_player"])

    def test_http_gate(self):
        with patch.object(
            src,
            "check_http_play",
            return_value={"ok": True, "status": 200, "url": "http://x/play/"},
        ):
            row = src.evaluate_game(self.game_id, root=self.root, require_http=True)
        self.assertEqual(row["status"], "pass")
        self.assertTrue(row["checks"]["chrome_play_http"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
