#!/usr/bin/env python3
"""Offline tests for solid-60 mandate helpers (no Chrome / no builds)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from solid_60_mandate import (  # noqa: E402
    evaluate_solid_60,
    measure_present_pacing,
    resolve_min_fps,
    validate_exceptions,
)


class Solid60MandateTests(unittest.TestCase):
    def test_present_pacing_measure_complete(self):
        m = measure_present_pacing()
        self.assertTrue(m["measure_complete"], m.get("missing_fields"))
        c = m["constants"]
        self.assertIs(c["g_vsync_default"], True)
        self.assertIs(c["uncap_forbidden_under_vsync"], True)
        self.assertEqual(c["kMaxBehind_emscripten"], 4)
        self.assertEqual(c["raf_skip_when_presents_queued_gt"], 2)
        self.assertFalse(m["product_changes_applied"])

    def test_overlay_only_rejected(self):
        v = evaluate_solid_60(
            "synthetic",
            chrome_metrics={"fps_overlay": {"avg": 60.0, "min": 60.0}},
        )
        self.assertFalse(v["pass"])
        self.assertIn("fps_overlay_only_rejected", v["violations"])

    def test_frameskip_rejected(self):
        v = evaluate_solid_60(
            "synthetic",
            chrome_metrics={"fps": {"avg": 60.0, "min": 60.0}},
            log_text="turn on frameskip",
        )
        self.assertFalse(v["pass"])
        self.assertTrue(any(x.startswith("frameskip:") for x in v["violations"]))

    def test_stats_pass(self):
        v = evaluate_solid_60(
            "synthetic",
            chrome_metrics={"fps": {"avg": 60.0, "min": 59.2, "max": 60.0}},
        )
        self.assertTrue(v["pass"], v["violations"])

    def test_allowlist_30_with_reason(self):
        reg = {
            "global_runtime": {
                "min_fps_default": 60,
                "min_fps_exceptions": {
                    "g": {"min_fps": 30, "reason": "true 30 Hz title"},
                },
            },
            "per_game": {},
        }
        info = resolve_min_fps("g", reg)
        self.assertTrue(info["allowlisted"])
        self.assertEqual(info["min_fps"], 30.0)
        self.assertTrue(info["exception_valid"])
        self.assertEqual(validate_exceptions(reg), [])

    def test_allowlist_rejects_45(self):
        reg = {
            "global_runtime": {
                "min_fps_default": 60,
                "min_fps_exceptions": {
                    "g": {"min_fps": 45, "reason": "fake soft miss"},
                },
            },
            "per_game": {},
        }
        info = resolve_min_fps("g", reg)
        self.assertFalse(info["exception_valid"])
        problems = validate_exceptions(reg)
        self.assertTrue(any(p.get("game_id") == "g" for p in problems))


if __name__ == "__main__":
    unittest.main()
