#!/usr/bin/env python3
"""Regression tests for the hero_balance.py -> Godot preparation gate."""
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
import prepare_godot_balance as prep  # noqa: E402


class BalancePrepareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = prep.source_module()
        cls.raw = prep.raw_catalog()
        cls.core = json.loads((PROJECT / "data/core_data.json").read_text(encoding="utf-8"))
        cls.contract = prep.build_contract(cls.module, cls.core, cls.raw)
        cls.oracle = prep.build_oracle(cls.module, cls.raw)

    def test_contract_matches_source_and_core(self):
        self.assertEqual(len(self.raw), 222)
        self.assertEqual(len(self.contract["pristine_boss_stats"]), 216)
        self.assertEqual(self.contract["starter_heroes"], list(self.module.STARTER_HEROES))
        self.assertEqual(self.contract["switches"]["school_parity"], self.module.SCHOOL_PARITY)
        self.assertEqual(self.contract["constants"]["hp_mult_range"], list(self.module.HP_MULT_RANGE))
        self.assertEqual(self.contract["constants"]["starter_catchup_max"], self.module.STARTER_CATCHUP_MAX)
        final = copy.deepcopy(self.raw)
        with prep._game():
            prep._reset_last(self.module)
            self.module.apply_to_catalog(final)
        prep.validate_final(final, self.core)
        for hero in self.module.STARTER_HEROES:
            self.assertEqual(final[hero], self.raw[hero])
            self.assertNotIn("__bal", self.core["heroes"][hero])

    def test_oracle_covers_runtime_and_helpers(self):
        self.assertEqual(set(self.oracle["raw_catalog"]), set(self.raw))
        self.assertEqual(len(self.oracle["final_stats"]), 216)
        self.assertEqual(len(self.oracle["table"]), 222)
        self.assertEqual(len(self.oracle["resolve_table"]), 222)
        self.assertEqual(len(self.oracle["catchup"]["mult_grid"]), 8 * 8 * 8)
        self.assertEqual(len(self.oracle["calibrate"]["rows"]), 216)
        self.assertEqual(len(self.oracle["resolve_variants"]), 2)
        self.assertIn("pool_anchor", self.oracle["last"])
        self.assertIn("fix", self.oracle["last"])
        self.assertEqual(self.oracle["source_sha256"], self.contract["source_sha256"])

    def test_fixture_float_normalization_absorbs_cpython_sum_noise(self):
        noisy = prep._jsonable(copy.deepcopy(self.oracle))
        for delta in noisy["calibrate"]["report"]["_mods_mini"].values():
            delta[1] += 1e-16
        self.assertEqual(prep._text(self.oracle, float_digits=12), prep._text(noisy, float_digits=12))
        self.assertEqual(self.contract["constants"]["ehp_per_hp"], self.module.EHP_PER_HP)

    def test_catchup_and_unlock_semantics(self):
        self.assertEqual(self.module.starter_catchup("gornak", 0, 1), (1.0, 1.0))
        self.assertEqual(self.module.starter_catchup("kaizen", 12, 1), (1.0, 1.0))
        hp, dmg = self.module.starter_catchup("kaizen", 0, 1)
        self.assertGreater(hp, dmg)
        self.assertAlmostEqual(hp, 1.0 + (self.module.STARTER_CATCHUP_MAX - 1.0) * 1.25)
        self.assertAlmostEqual(dmg, 1.0 + (self.module.STARTER_CATCHUP_MAX - 1.0) * 0.85)
        self.assertEqual(self.module.boss_unlocks_for_purchases(["kaizen", "vex"]), 0)
        self.assertEqual(self.module.boss_unlocks_for_purchases(["gornak", "gornak", "kaizen"]), 2)
        self.assertEqual(self.module.starter_catchup_stats("kaizen", {"hp": 100, "damage": 10}, 12, 1), (100, 10))

    def test_stale_or_incomplete_core_fails_closed(self):
        core = copy.deepcopy(self.core)
        core["heroes"]["gornak"]["hp"] += 1
        final = copy.deepcopy(self.raw)
        with prep._game():
            prep._reset_last(self.module)
            self.module.apply_to_catalog(final)
        with self.assertRaisesRegex(AssertionError, "Stale core balance"):
            prep.validate_final(final, core)
        core = copy.deepcopy(self.core)
        del core["heroes"]["kaizen"]
        with self.assertRaisesRegex(AssertionError, "coverage"):
            prep.validate_final(final, core)

    def test_check_is_current_and_deterministic(self):
        tracked = json.loads((PROJECT / "data/hero_balance.json").read_text(encoding="utf-8"))
        self.assertEqual(tracked, self.contract)
        for seed in ("1", "99"):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/prepare_godot_balance.py"), "--check"],
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
        self.assertIn("var balance: HeroBalance", core_data)
        self.assertIn("balance.valid()", core_data)
        unit = (PROJECT / "scripts/core/BattleUnit.gd").read_text(encoding="utf-8")
        self.assertIn("data.balance.is_starter(hero_type)", unit)
        self.assertIn("data.balance.starter_catchup_stats(", unit)
        model = (PROJECT / "scripts/core/MatchModel.gd").read_text(encoding="utf-8")
        self.assertIn("data.balance.boss_unlocks_for_purchases(purchased_heroes)", model)
        ai = (PROJECT / "scripts/entities/EntityAI.gd").read_text(encoding="utf-8")
        self.assertIn("model.data.balance.boss_unlocks_for_purchases(model.purchased_heroes)", ai)
        runner = (PROJECT / "tests/run_all.gd").read_text(encoding="utf-8")
        self.assertIn("BalanceParity.run(self)", runner)
        for workflow in ("godot-check.yml", "godot-rebuild.yml"):
            text = (ROOT / ".github/workflows" / workflow).read_text(encoding="utf-8")
            self.assertIn("tools/prepare_godot_balance.py --check", text)
            self.assertIn("tools/test_godot_balance_prepare.py", text)


if __name__ == "__main__":
    unittest.main()
