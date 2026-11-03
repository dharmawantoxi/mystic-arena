#!/usr/bin/env python3
"""Regression tests for the native bosses/ exporter and closed-world gate."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import prepare_godot_bosses as prep  # noqa: E402


class BossesPrepareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = prep.build_contract()
        cls.oracle = json.loads(prep.FIXTURE.read_text(encoding="utf-8"))

    def test_closed_world_inventory(self):
        self.assertEqual(self.contract["schema"], 1)
        self.assertEqual(self.contract["counts"], {
            "files": 61, "renderers": 54, "mini": 162, "true": 54, "smart_ai": 79,
        })
        self.assertEqual(len(self.contract["files"]), 61)
        self.assertIn("__init__.py", self.contract["files"])
        self.assertEqual(len(self.contract["bosses"]), 216)
        for row in self.contract["bosses"].values():
            self.assertIn("png", row["art"])
            self.assertEqual(len(row["art"]["png"]["sha256"]), 64)
            self.assertTrue(row["module"].startswith("level"))
            self.assertTrue(row["draw_fn"].startswith("draw_"))

    def test_renderer_aliases_and_v4_closure(self):
        self.assertEqual(self.contract["bosses"]["morvaeth2"]["module"], "level42")
        self.assertEqual(self.contract["bosses"]["razak"]["source_modules"], ["level2", "razak_v4"])
        self.assertEqual(self.contract["bosses"]["nyzrak"]["source_modules"], ["level3", "nyzrak_v4"])
        self.assertEqual(self.contract["bosses"]["thalgryn"]["source_modules"], ["level6", "thalgryn_v4"])

    def test_oracle_coverage(self):
        self.assertEqual(len(self.oracle["runtime"]["bosses"]), 216)
        self.assertEqual(self.oracle["runtime"]["smart_ai_count"], 79)
        self.assertEqual(len(self.oracle["smart_ai"]["bosses"]), 79)
        self.assertEqual(len(self.oracle["controller"]), 10)
        self.assertEqual(len(self.oracle["combat"]), 10)
        self.assertEqual(len(self.oracle["normalization"]["final"]["mini"]), 162)
        self.assertEqual(len(self.oracle["normalization"]["final"]["true"]), 54)

    def test_check_is_current(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/prepare_godot_bosses.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_stale_source_fails_closed(self):
        source = ROOT / "bosses/base_boss.py"
        original = source.read_bytes()
        try:
            source.write_bytes(original + b"\n# stale-gate-test\n")
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/prepare_godot_bosses.py"), "--check"],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Stale bosses", result.stderr)
        finally:
            source.write_bytes(original)

    def test_renderer_drift_requires_bake(self):
        contract = prep.build_contract()
        row = contract["bosses"]["gornak"]
        old = row["source_sha256"]
        row["source_sha256"] = "0" * 64
        # Simulate tracked contract with changed renderer source but unchanged PNG.
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bosses.json"
            path.write_text(json.dumps(contract), encoding="utf-8")
            original = prep.CONTRACT
            try:
                prep.CONTRACT = path
                # gornak source unchanged on disk, tracked digest differs, PNG same -> fail
                with self.assertRaisesRegex(AssertionError, "run tools/prepare_godot_bosses.py --bake"):
                    prep.build_contract()
            finally:
                prep.CONTRACT = original
        self.assertEqual(len(old), 64)


if __name__ == "__main__":
    unittest.main()
