#!/usr/bin/env python3
"""Regression tests for the hero_items.py -> Godot preparation gate."""
from __future__ import annotations

import contextlib
import copy
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
import prepare_godot_items as prep  # noqa: E402


class ItemsPrepareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with prep.source_module() as module:
            cls.module = module
            cls.contract = prep.build_contract(module)
            cls.oracle = prep.build_oracle(module)
        cls.core = json.loads((PROJECT / "data/core_data.json").read_text(encoding="utf-8"))

    def test_contract_matches_source_and_core(self):
        self.assertEqual(len(self.contract["catalog"]), 33)
        self.assertEqual(self.contract["catalog"], self.core["items"])
        self.assertEqual(self.contract["max_item_slots"], self.module.MAX_ITEM_SLOTS)
        self.assertEqual(self.contract["item_flat_cost"], self.module.ITEM_FLAT_COST)
        self.assertEqual(len(self.contract["shop_pages"]), 6)
        self.assertEqual(len(self.contract["item_shop_order"]), 33)
        self.assertEqual(set(self.contract["item_shop_order"]), set(self.contract["catalog"]))
        counts = {cls: 0 for cls in ("physical", "magic", "tank")}
        for sid in self.contract["catalog"]:
            counts[self.oracle["class_cases"][sid]] += 1
        self.assertEqual(counts, {"physical": 14, "magic": 10, "tank": 9})

    def test_oracle_covers_helpers_and_runtime(self):
        self.assertEqual(len(self.oracle["class_cases"]), 34)
        self.assertEqual(len(self.oracle["mechanics"]["id"]), 33)
        self.assertEqual(len(self.oracle["mechanics"]["en"]), 33)
        self.assertEqual(len(self.oracle["getter_cases"]), 18)
        self.assertEqual(len(self.oracle["trigger_cases"]), 19)
        self.assertEqual(len(self.oracle["on_hit_cases"]), 10)
        self.assertEqual(len(self.oracle["suggest_cases"]), 33)
        self.assertEqual(self.oracle["source_sha256"], self.contract["source_sha256"])

    def test_magic_role_and_class_gates(self):
        self.assertTrue(self.module.is_magic_hero(type("H", (), {"role": "Mage/Trickster"})()))
        self.assertTrue(self.module.is_magic_hero(type("H", (), {"role": "Boss/Magic"})()))
        self.assertFalse(self.module.is_magic_hero(type("H", (), {"role": "Anti-Mage"})()))
        self.assertFalse(self.module.is_magic_hero(type("H", (), {"role": ""})()))
        self.assertEqual(self.module.get_item_class("astral_codex"), "magic")
        self.assertEqual(self.module.get_item_class("tempest_vane"), "tank")
        self.assertEqual(self.module.get_item_class("abyss_breaker"), "tank")
        self.assertEqual(self.module.get_item_class("dead_edge"), "physical")

    def test_stale_core_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "data").mkdir()
            core = copy.deepcopy(self.core)
            core["items"]["dead_edge"]["cost"] += 1
            (project / "data/core_data.json").write_text(json.dumps(core), encoding="utf-8")
            with mock.patch.object(prep, "PROJECT", project):
                with self.assertRaisesRegex(AssertionError, "Stale core item catalog"):
                    prep.build_contract(self.module)

    def test_check_is_current_and_deterministic(self):
        tracked = json.loads((PROJECT / "data/hero_items.json").read_text(encoding="utf-8"))
        self.assertEqual(tracked, self.contract)
        for seed in ("1", "99"):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/prepare_godot_items.py"), "--check"],
                cwd=ROOT, capture_output=True, text=True, check=False, env=env)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_missing_and_stale_files_fail_check(self):
        with tempfile.TemporaryDirectory() as directory:
            contract = Path(directory) / "contract.json"
            fixture = Path(directory) / "fixture.json"
            with mock.patch.object(prep, "CONTRACT", contract), mock.patch.object(prep, "FIXTURE", fixture):
                with mock.patch.object(sys, "argv", ["prepare", "--check"]), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as missing:
                        prep.main()
                self.assertEqual(missing.exception.code, 1)
                self.assertFalse(contract.exists())
                contract.write_text("stale\n", encoding="utf-8")
                fixture.write_text(prep._text(self.oracle), encoding="utf-8")
                with mock.patch.object(sys, "argv", ["prepare", "--check"]), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as stale:
                        prep.main()
                self.assertEqual(stale.exception.code, 1)
                self.assertEqual(contract.read_text(encoding="utf-8"), "stale\n")

    def test_native_runtime_and_ci_wiring(self):
        core_data = (PROJECT / "scripts/core/CoreData.gd").read_text(encoding="utf-8")
        self.assertIn("var items: HeroItems", core_data)
        self.assertIn("items.valid()", core_data)
        inventory = (PROJECT / "scripts/core/UnitInventory.gd").read_text(encoding="utf-8")
        self.assertIn("func skill_amp()", inventory)
        self.assertIn("func roll_block(", inventory)
        triggers = (PROJECT / "scripts/entities/EntityItems.gd").read_text(encoding="utf-8")
        self.assertIn("static func update_auras(", triggers)
        self.assertIn("static func apply_miasma(", triggers)
        runner = (PROJECT / "tests/run_all.gd").read_text(encoding="utf-8")
        self.assertIn("ItemsParity.run(self)", runner)
        for workflow in ("godot-check.yml", "godot-rebuild.yml"):
            text = (ROOT / ".github/workflows" / workflow).read_text(encoding="utf-8")
            self.assertIn("tools/prepare_godot_items.py --check", text)
            self.assertIn("tools/test_godot_items_prepare.py", text)


if __name__ == "__main__":
    unittest.main()
