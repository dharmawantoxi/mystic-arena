#!/usr/bin/env python3
"""Regression tests for the ui_theme.py -> Godot preparation gate."""
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
import prepare_godot_ui_theme as prep  # noqa: E402


class UiThemePrepareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = prep.build_contract()
        cls.oracle = prep.build_oracle()

    def test_contract_matches_source(self):
        self.assertEqual(self.contract["schema"], 1)
        self.assertEqual(self.contract["source"], "ui_theme.py")
        self.assertEqual(len(self.contract["palette"]), 32)
        self.assertEqual(len(self.contract["icons"]), 29)
        self.assertEqual(self.contract["palette"]["gold"], [255, 205, 85])
        self.assertEqual(self.contract["config"]["button"]["hover_inflate"], [18, 8])
        self.assertTrue(self.contract["cheap_alpha_default"])
        for anchor in self.contract["anchors"]:
            self.assertIn(anchor, (ROOT / "ui_theme.py").read_text(encoding="utf-8"))

    def test_oracle_coverage(self):
        self.assertEqual(len(self.oracle["components"]), 188)
        self.assertEqual(len(self.oracle["icons"]), 90)
        self.assertEqual(len(self.oracle["surfaces"]["gradient"]), 4)
        self.assertEqual(len(self.oracle["surfaces"]["radial"]), 4)
        self.assertEqual(len(self.oracle["surfaces"]["shadow"]), 3)
        self.assertEqual(self.oracle["source_sha256"], self.contract["source_sha256"])
        names = {row["name"] for row in self.oracle["components"]}
        for required in ("panel", "button", "pill", "chip", "toggle", "slider",
                         "option_cycler", "tab", "screen_title", "back_button",
                         "scroll_indicator", "hp_bar", "progress_bar"):
            self.assertIn(required, names)

    def test_check_is_current_and_deterministic(self):
        tracked = json.loads((PROJECT / "data/ui_theme.json").read_text(encoding="utf-8"))
        self.assertEqual(tracked, self.contract)
        for seed in ("1", "99"):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/prepare_godot_ui_theme.py"), "--check"],
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

    def test_source_drift_fails_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "ui_theme.py"
            source.write_text((ROOT / "ui_theme.py").read_text(encoding="utf-8").replace(
                "BG_DEEP        = (9, 12, 26)", "BG_DEEP        = (9, 12, 27)"), encoding="utf-8")
            with mock.patch.object(prep, "SOURCE", source):
                contract = prep.build_contract()
                self.assertNotEqual(contract["source_sha256"], self.contract["source_sha256"])
                self.assertEqual(contract["palette"]["bg_deep"], [9, 12, 27])


if __name__ == "__main__":
    unittest.main()
