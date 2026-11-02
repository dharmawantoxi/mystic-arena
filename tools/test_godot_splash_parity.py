#!/usr/bin/env python3
"""Active splash oracle gate for the native Godot project.

The removed legacy godot/gdext C++ port is not a prerequisite. This gate
re-runs the real pygame SplashScreen headless and checks the tracked fixture
used by godot_rebuild/tests/SplashParityTest.gd. Pixel-exact native rendering is
covered by the Godot suite; this file guards the Python oracle/contract itself.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
sys.path.insert(0, str(ROOT / "tools"))
import prepare_godot_splash as prep  # noqa: E402


class SplashParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads((PROJECT / "data/splash.json").read_text(encoding="utf-8"))
        cls.fixture = json.loads((PROJECT / "tests/fixtures/splash_parity.json").read_text(encoding="utf-8"))

    def test_hashes_match_source(self):
        digest = hashlib.sha256((ROOT / "splash_screen.py").read_bytes()).hexdigest()
        self.assertEqual(self.contract["source_sha256"], digest)
        self.assertEqual(self.fixture["source_sha256"], digest)

    def test_tracked_timeline_and_particles_match_live_source(self):
        with prep.source_module() as (module, TrackSurface):
            self.assertEqual(prep._jsonable(prep._timeline(module, TrackSurface)), self.fixture["timeline"])
            self.assertEqual(prep._jsonable(prep._particles(module, TrackSurface)), self.fixture["particles"])

    def test_skip_fade_is_absolute_not_relative(self):
        late = next(row for row in self.fixture["timeline"] if row["name"] == "skip_late")
        # Source measures fade from elapsed time; a late skip is immediately
        # hidden (1 - 2.0 / 0.35 clamps to 0) instead of restarting a fade.
        frame = late["frames"][120]
        self.assertGreaterEqual(frame[0], 2.0)
        self.assertEqual(frame[2], 0.0)
        self.assertTrue(frame[3])

    def test_hint_and_layout_anchors(self):
        self.assertEqual(self.contract["config"]["hint_text"], "Tap anywhere to skip")
        width, height = self.fixture["screen"]
        for row in self.fixture["layout_cases"]:
            if not row["drawn"]:
                continue
            x, y, w, h = row["hint_rect"]
            self.assertEqual(x + w // 2, width // 2)
            self.assertEqual(y + h // 2, height - self.contract["config"]["hint_margin"])
            self.assertEqual(row["hint_alpha"], int(140 * row["overall_alpha"]))

    def test_native_wiring_is_present(self):
        view = (PROJECT / "scripts/ui/SplashView.gd").read_text(encoding="utf-8")
        model = (PROJECT / "scripts/ui/SplashModel.gd").read_text(encoding="utf-8")
        main = (PROJECT / "scripts/Main.gd").read_text(encoding="utf-8")
        runner = (PROJECT / "tests/run_all.gd").read_text(encoding="utf-8")
        self.assertIn("model.update(minf(delta, 0.05))", view)
        self.assertIn("done = elapsed >= f(\"skip_done\")", model)
        self.assertIn("splash.skip()", main)
        self.assertIn("SplashParity.run(self)", runner)


if __name__ == "__main__":
    unittest.main()
