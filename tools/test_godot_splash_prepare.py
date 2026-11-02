#!/usr/bin/env python3
"""Regression tests for the splash_screen.py -> Godot preparation gate."""
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
import prepare_godot_splash as prep  # noqa: E402


class SplashPrepareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = prep.build_contract()
        with prep.source_module() as (module, TrackSurface):
            cls.oracle = prep.build_oracle(module, TrackSurface)

    def test_contract_matches_ast_source(self):
        self.assertEqual(self.contract["schema"], 1)
        self.assertEqual(self.contract["source"], "splash_screen.py")
        self.assertEqual(self.contract["config"], prep._jsonable(prep.ast_spec.build_spec().values))
        self.assertEqual(len(self.contract["source_lines"]), 68)
        self.assertEqual(self.contract["font_files"]["title"], "Cinzel.ttf")
        self.assertTrue(self.contract["cheap_alpha_default"])
        self.assertEqual(self.contract["particle_seed"], 1234)

    def test_oracle_coverage(self):
        self.assertEqual(len(self.oracle["timeline"]), 5)
        self.assertEqual(len(self.oracle["layout_cases"]), 16)
        self.assertEqual(len(self.oracle["background"]), 4)
        self.assertEqual(len(self.oracle["logo_glow"]), 3)
        self.assertEqual(len(self.oracle["particles"]["initial"]), 46)
        self.assertEqual(self.oracle["source_sha256"], self.contract["source_sha256"])

    def test_check_is_current_and_deterministic(self):
        tracked = json.loads((PROJECT / "data/splash.json").read_text(encoding="utf-8"))
        self.assertEqual(tracked, self.contract)
        for seed in ("1", "99"):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/prepare_godot_splash.py"), "--check"],
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

    def test_background_collapses_to_black_interior(self):
        for row in self.oracle["background"]:
            interior = next(s for s in row["samples"] if s["pos"] == [2, 2])
            self.assertEqual(interior["rgb"], [0, 0, 0])


if __name__ == "__main__":
    unittest.main()
