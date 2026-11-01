#!/usr/bin/env python3
"""Regression tests for the native _core.py data exporter."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import prepare_godot_core as prep  # noqa: E402


class CorePrepareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = prep.build()

    def test_catalog_counts_and_source_rules(self):
        self.assertEqual(self.data["schema"], 1)
        self.assertEqual(len(self.data["levels"]), 54)
        self.assertGreaterEqual(len(self.data["heroes"]), 222)
        self.assertEqual(len(self.data["bosses"]["mini"]), 162)
        self.assertEqual(len(self.data["bosses"]["true"]), 54)
        self.assertEqual(len(self.data["items"]), 33)
        self.assertEqual(self.data["rules"]["MINION_WAVE_INTERVAL"], 1500)
        self.assertEqual(self.data["heroes"]["kaizen"]["hp"], 550)
        self.assertTrue(self.data["heroes"]["gornak"]["is_boss_hero"])

    def test_lanes_and_localization(self):
        self.assertEqual(set(self.data["lanes"]), {"top", "mid", "bot", "river"})
        self.assertGreater(len(self.data["lanes"]["top"]), 100)
        self.assertIn("id", self.data["localization"])
        self.assertIn("en", self.data["localization"])

    def test_check_is_current(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/prepare_godot_core.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_cloud_fixture_checksum(self):
        sys.path.insert(0, str(ROOT))
        from mobile.cloud_save import compute_checksum
        fixture = json.loads((ROOT / "godot_rebuild/tests/fixtures/cloud_payload.json").read_text())
        self.assertEqual(fixture["checksum"], compute_checksum(fixture))


if __name__ == "__main__":
    unittest.main()
