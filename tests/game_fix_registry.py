"""Versioned game-fix registry schema + discfix applied list."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import game_fix_registry as gfr

ROOT = Path(__file__).resolve().parents[1]


class GameFixRegistryTests(unittest.TestCase):
    def test_live_registry_audit_passes(self):
        result = gfr.audit()
        self.assertTrue(result["ok"], result["problems"])
        self.assertEqual(result["schema"], gfr.SCHEMA_ID)
        self.assertEqual(result["discfix_applied_ids"], ["R3_readee", "R4D1_DiskReady"])
        self.assertGreaterEqual(result["per_game_count"], 14)

    def test_applied_ids_from_rich_and_legacy(self):
        rich = {
            "global_runtime": {
                "discfix_applied": [
                    {"id": "R3_readee", "status": "verified_apply", "files": ["a.cpp"]},
                    {"id": "R4D1_DiskReady", "status": "verified_apply", "files": ["b.cpp"]},
                ]
            }
        }
        legacy = {"global_runtime": {"disc_fix_applied": ["R3_readee", "R4D1_DiskReady"]}}
        self.assertEqual(gfr.discfix_applied_ids(rich), ["R3_readee", "R4D1_DiskReady"])
        self.assertEqual(gfr.discfix_applied_ids(legacy), ["R3_readee", "R4D1_DiskReady"])

    def test_validate_rejects_schema_drift(self):
        reg = json.loads((ROOT / "verification" / "recovery" / "game-fix-registry.json").read_text(encoding="utf-8"))
        reg["schema"] = 1
        problems = gfr.validate_registry(reg, require_board_sync=False)
        self.assertTrue(any("schema want" in p for p in problems))

    def test_validate_rejects_alias_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reg = {
                "schema": gfr.SCHEMA_ID,
                "schema_version": 1,
                "global_runtime": {
                    "discfix_applied": [
                        {
                            "id": "R3_readee",
                            "status": "verified_apply",
                            "board_path": "discfix.applied.R3_readee",
                            "files": ["runtime/src/iop/cdvdfsv.cpp"],
                        },
                        {
                            "id": "R4D1_DiskReady",
                            "status": "verified_apply",
                            "board_path": "discfix.applied.R4D1_DiskReady",
                            "files": ["runtime/src/iop/cdvd.cpp"],
                        },
                    ],
                    "disc_fix_applied": ["R3_readee"],
                },
                "per_game": {"x": {"title": "x"}},
            }
            problems = gfr.validate_registry(reg, require_board_sync=False)
            self.assertTrue(any("alias drift" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
