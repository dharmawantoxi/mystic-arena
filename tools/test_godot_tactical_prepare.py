#!/usr/bin/env python3
"""Regression tests for the tactical_commands.py -> Godot preparation gate."""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
sys.path.insert(0, str(ROOT / "tools"))
import prepare_godot_tactical as prep  # noqa: E402


class TacticalPrepareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oracle = prep.build_oracle()
        cls.contract = prep.build_contract(cls.oracle)

    def test_contract_matches_source(self):
        self.assertEqual(self.contract["schema"], 1)
        self.assertEqual(self.contract["source"], "tactical_commands.py")
        self.assertEqual(self.contract["config"]["hold_tap_max_frames"], 20)
        self.assertEqual(self.contract["config"]["hold_release_tail"], 30)
        self.assertEqual(self.contract["config"]["gather_push_delay_frames"], 240)
        self.assertEqual(self.contract["config"]["command_duration"], 600)
        self.assertEqual(self.contract["config"]["command_colors"]["gather"], [100, 220, 255])
        for anchor in self.contract["anchors"]:
            self.assertIn(anchor, (ROOT / "tactical_commands.py").read_text(encoding="utf-8"))

    def test_oracle_coverage(self):
        self.assertEqual(len(self.oracle["scenarios"]), 37)
        self.assertEqual(len(self.oracle["draw"]["world"]), 3)
        self.assertEqual(len(self.oracle["draw"]["ui"]), 5)
        self.assertEqual(self.oracle["source_sha256"], self.contract["source_sha256"])
        names = {row["name"] for row in self.oracle["scenarios"]}
        for required in ("hold_tap_short", "hold_long_truncate", "hold_gather_push_lock",
                         "hold_armed_boss_appears", "auto_protect_castle", "auto_protect_tower",
                         "auto_attack_boss_trigger", "auto_attack_boss_no_roll"):
            self.assertIn(required, names)

    def test_check_is_current_and_deterministic(self):
        tracked = json.loads((PROJECT / "data/tactical.json").read_text(encoding="utf-8"))
        self.assertEqual(tracked, self.contract)
        for seed in ("1", "99"):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/prepare_godot_tactical.py"), "--check"],
                cwd=ROOT, capture_output=True, text=True, check=False, env=env)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_missing_and_stale_files_fail_check(self):
        with tempfile.TemporaryDirectory() as directory:
            contract = Path(directory) / "contract.json"
            fixture = Path(directory) / "fixture.json"
            with mock.patch.object(prep, "CONTRACT", contract), mock.patch.object(prep, "FIXTURE", fixture):
                with mock.patch.object(sys, "argv", ["prepare", "--check"]), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(prep.main(), 1)
                self.assertFalse(contract.exists())
                contract.write_text("stale\n", encoding="utf-8")
                fixture.write_text(prep._text(self.oracle), encoding="utf-8")
                with mock.patch.object(sys, "argv", ["prepare", "--check"]), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(prep.main(), 1)
                self.assertEqual(contract.read_text(encoding="utf-8"), "stale\n")


if __name__ == "__main__":
    unittest.main()
