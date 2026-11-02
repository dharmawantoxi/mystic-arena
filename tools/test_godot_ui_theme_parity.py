#!/usr/bin/env python3
"""Active ui_theme oracle gate for the native Godot project."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
sys.path.insert(0, str(ROOT / "tools"))
import prepare_godot_ui_theme as prep  # noqa: E402


class UiThemeParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads((PROJECT / "data/ui_theme.json").read_text(encoding="utf-8"))
        cls.fixture = json.loads((PROJECT / "tests/fixtures/ui_theme_parity.json").read_text(encoding="utf-8"))

    def test_hashes_match_source(self):
        digest = hashlib.sha256((ROOT / "ui_theme.py").read_bytes()).hexdigest()
        self.assertEqual(self.contract["source_sha256"], digest)
        self.assertEqual(self.fixture["source_sha256"], digest)

    def test_check_cli_passes(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/prepare_godot_ui_theme.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_oracle_guards(self):
        components = self.fixture["components"]
        disabled = [row for row in components if row["name"] == "pill" and row["kwargs"].get("enabled") is False]
        self.assertTrue(disabled)
        for row in disabled:
            self.assertEqual(row["btns"], {})
        hover_buttons = [row for row in components if row["name"] == "button" and row["kwargs"].get("hover")]
        self.assertTrue(hover_buttons)
        for row in hover_buttons:
            self.assertEqual(row["result"][2], int(row["kwargs"].get("w", 300)) + 18)
            self.assertEqual(row["result"][3], int(row["kwargs"].get("h", 50)) + 8)
        cheap_panels = [row for row in components if row["name"] == "panel" and not row["cheap_alpha"]]
        self.assertTrue(cheap_panels)
        for row in cheap_panels:
            self.assertFalse(any(op["op"] == "gradient" for op in row["ops"]))
        unknown = [row for row in self.fixture["icons"] if row["name"] == "unknown"]
        self.assertTrue(unknown)
        for row in unknown:
            self.assertEqual(row["ops"], [])

    def test_native_wiring_is_present(self):
        theme = (PROJECT / "scripts/ui/UiTheme.gd").read_text(encoding="utf-8")
        ui = (PROJECT / "scripts/ui/Ui.gd").read_text(encoding="utf-8")
        main = (PROJECT / "scripts/Main.gd").read_text(encoding="utf-8")
        menu = (PROJECT / "scripts/ui/MenuView.gd").read_text(encoding="utf-8")
        runner = (PROJECT / "tests/run_all.gd").read_text(encoding="utf-8")
        self.assertIn("data/ui_theme.json", theme)
        self.assertIn("UiThemePanel", ui)
        self.assertIn("UiThemeButton", ui)
        self.assertIn("UiTheme.set_quality", main)
        self.assertIn('UiTheme.color("bg_deep")', menu)
        self.assertIn("UiThemeParity.run(self)", runner)
        self.assertTrue((PROJECT / "tests/UiThemeParityTest.gd").is_file())


if __name__ == "__main__":
    unittest.main()
