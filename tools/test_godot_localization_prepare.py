#!/usr/bin/env python3
"""Regression tests for the localization.py -> Godot preparation gate."""
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
import prepare_godot_localization as prep  # noqa: E402


class LocalizationPrepareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with prep.source_module() as module:
            cls.module = module
            cls.contract = prep.build_contract(module)
            cls.oracle = prep.build_oracle(module)

    def test_contract_matches_source(self):
        self.assertEqual(self.contract["schema"], 1)
        self.assertEqual(self.contract["source"], "localization.py")
        self.assertEqual(self.contract["languages"], ["id", "en"])
        self.assertEqual(self.contract["default_language"], "id")
        self.assertEqual(self.contract["language_labels"], self.module.LANGUAGE_LABELS)
        self.assertEqual(self.contract["key_count"], 224)
        self.assertEqual(self.contract["key_order"], list(self.module._TEXT["id"]))
        self.assertEqual(self.contract["texts"], self.module._TEXT)
        names = {name for row in self.contract["placeholders"].values() for name in row}
        self.assertEqual(names, {"count", "hero", "item", "items", "page"})

    def test_oracle_coverage(self):
        self.assertEqual(len(self.oracle["tr_cases"]), 448)
        self.assertEqual(len(self.oracle["missing_args_cases"]), 22)
        self.assertEqual(len(self.oracle["language_cases"]), 5)
        self.assertEqual(len(self.oracle["label_cases"]), 4)
        self.assertEqual(len(self.oracle["edge_cases"]), 4)
        self.assertEqual(self.oracle["source_sha256"], self.contract["source_sha256"])

    def test_source_language_is_restored(self):
        self.module.set_language("en")
        with prep.source_module() as module:
            self.assertEqual(module.get_language(), "id")
        self.assertEqual(self.module.get_language(), "en")
        self.module.set_language("id")

    def test_check_is_current_and_deterministic(self):
        tracked = json.loads((PROJECT / "data/localization.json").read_text(encoding="utf-8"))
        self.assertEqual(tracked, self.contract)
        for seed in ("1", "99"):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/prepare_godot_localization.py"), "--check"],
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

    def test_native_runtime_and_ci_wiring(self):
        localization = (PROJECT / "scripts/core/Localization.gd").read_text(encoding="utf-8")
        self.assertIn("class_name Localization", localization)
        self.assertIn("func tr_text(", localization)
        self.assertIn("func set_language(", localization)
        core = (PROJECT / "scripts/core/CoreData.gd").read_text(encoding="utf-8")
        self.assertIn("var localization: Localization", core)
        self.assertIn("localization.tr_for", core)
        runner = (PROJECT / "tests/run_all.gd").read_text(encoding="utf-8")
        self.assertIn("LocalizationParity.run(self)", runner)
        for workflow in ("godot-check.yml", "godot-rebuild.yml"):
            text = (ROOT / ".github/workflows" / workflow).read_text(encoding="utf-8")
            self.assertIn("tools/prepare_godot_localization.py --check", text)
            self.assertIn("tools/test_godot_localization_prepare.py", text)


if __name__ == "__main__":
    unittest.main()
