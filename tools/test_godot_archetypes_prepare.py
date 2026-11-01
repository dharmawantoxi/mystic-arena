#!/usr/bin/env python3
"""Regression tests for the hero_archetypes.py -> Godot preparation gate."""
from __future__ import annotations

import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
sys.path.insert(0, str(ROOT / "tools"))
import prepare_godot_archetypes as prep  # noqa: E402


class ArchetypePrepareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = prep.source_module()
        cls.contract = prep.build_contract(cls.module)
        cls.oracle = prep.build_oracle(cls.module)
        cls.core = json.loads((PROJECT / "data/core_data.json").read_text(encoding="utf-8"))

    def test_tables_are_exact_source_snapshot(self):
        self.assertEqual(self.contract["archetypes"], self.module.ARCHETYPES)
        self.assertEqual(len(self.contract["archetypes"]), 222)
        self.assertEqual(len(self.contract["boss_resistances"]), 216)
        self.assertEqual(self.contract["default_dmg_type"], "PHYSICAL")
        self.assertEqual(self.contract["armor_factor"], 0.06)
        self.assertEqual(self.contract["armor_max"], 40)
        self.assertEqual(self.contract["mr_max"], 0.45)
        self.assertEqual(set(self.contract["archetypes"]), set(self.core["heroes"]))
        bosses = set(self.core["bosses"]["mini"]) | set(self.core["bosses"]["true"])
        self.assertEqual(set(self.contract["boss_resistances"]), bosses)
        self.assertEqual(self.contract["source_sha256"], self.oracle["source_sha256"])

    def test_oracle_covers_manual_overrides_and_unknowns(self):
        self.assertEqual(set(self.oracle["heroes"]), set(self.module.ARCHETYPES))
        self.assertEqual(set(self.oracle["bosses"]), set(self.module.BOSS_RESISTANCES))
        self.assertEqual(self.module.get_archetype("vex", {"dmg_type": "physical"})["dmg_type"], "PHYSICAL")
        unknown = self.module.get_archetype("unlisted", {"dmg_type": "MAGIC"})
        self.assertEqual(unknown, {"dmg_type": "MAGIC", "playstyle": "FIGHTER"})
        fallback = self.module.get_archetype("unlisted")
        self.assertTrue(fallback["derived"])
        self.assertEqual(fallback["power"], 0)
        self.assertEqual(len(self.oracle["hero_overrides"]), 27)
        self.assertEqual(len(self.oracle["boss_setups"]), 7)

    def test_boss_table_wins_and_profile_edges_match_python(self):
        self.assertEqual(self.module.get_boss_resistances("abaddon", "mini"), (32, 0.095))
        self.assertEqual(self.module.get_boss_resistances("unlisted", "true"), (18, 0.20))
        cases = self.oracle["profiles"]
        self.assertEqual(len(cases), 22)
        ties = [case["expected"][0] for case in cases if case["profile"] == "balanced" and case.get("armor_off") in (0.5, 1.5, -11.5)]
        self.assertEqual(ties, [12, 14, 0])
        for case in cases:
            actual = self.module._resist_from_profile(
                case["profile"], case["boss_class"], base=case.get("base"), mods=case.get("mods"),
                armor_scale=case.get("armor_scale", 1.0), mr_scale=case.get("mr_scale", 1.0),
                armor_off=case.get("armor_off", 0))
            self.assertEqual(list(actual), case["expected"])

    def test_invalid_or_incomplete_contracts_fail_closed(self):
        core = copy.deepcopy(self.core)
        del core["heroes"]["kaizen"]
        with self.assertRaisesRegex(AssertionError, "missing heroes"):
            prep.validate(self.contract, core)
        for table, key, field, value in (
            ("archetypes", "kaizen", "dmg_type", "TRUE"),
            ("archetypes", "kaizen", "power", -1),
            ("boss_resistances", "abaddon", "armor", 41),
            ("boss_resistances", "abaddon", "magic_resist", 0.46),
            ("boss_resistances", "abaddon", "profile", "unknown"),
            ("boss_resistances", "abaddon", "boss_class", "mini"),
        ):
            contract = copy.deepcopy(self.contract)
            contract[table][key][field] = value
            with self.subTest(table=table, field=field), self.assertRaises(AssertionError):
                prep.validate(contract, self.core)
        with self.assertRaises(AssertionError):
            prep.validate(self.contract, {"heroes": {}, "bosses": {}})

    def test_check_is_current_and_writes_nothing(self):
        tracked = {
            prep.CONTRACT: json.dumps(self.contract, ensure_ascii=False, indent=2) + "\n",
            prep.FIXTURE: json.dumps(self.oracle, ensure_ascii=False, indent=2) + "\n",
        }
        for path, text in tracked.items():
            self.assertEqual(path.read_text(encoding="utf-8"), text)
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/prepare_godot_archetypes.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True, check=False)
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
                self.assertFalse(fixture.exists())
                contract.write_text("stale\n", encoding="utf-8")
                fixture.write_text(tracked_fixture_text(self.oracle), encoding="utf-8")
                with mock.patch.object(sys, "argv", ["prepare", "--check"]), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as stale:
                        prep.main()
                self.assertEqual(stale.exception.code, 1)
                self.assertEqual(contract.read_text(encoding="utf-8"), "stale\n")

    def test_native_constants_and_runtime_wiring(self):
        native = (PROJECT / "scripts/core/HeroArchetypes.gd").read_text(encoding="utf-8")
        for name, value in (("ARMOR_FACTOR", 0.06), ("ARMOR_MAX", 40), ("MR_MAX", 0.45)):
            self.assertRegex(native, rf"const {name} := {value}\b")
        unit = (PROJECT / "scripts/core/BattleUnit.gd").read_text(encoding="utf-8")
        self.assertIn("data.archetypes.get_archetype(hero_type, stats)", unit)
        self.assertIn("data.archetypes.boss_resistances_for(boss_type, boss_class, stats)", unit)
        boss_setup = unit.split("func setup_boss(", 1)[1].split("\nfunc ", 1)[0]
        minion_setup = unit.split("func setup_minion(", 1)[1].split("\nfunc ", 1)[0]
        self.assertIn("boss_resistances_for(boss_type, boss_class, stats)", boss_setup)
        self.assertNotIn("boss_resistances_for", minion_setup)
        self.assertIn("intentionally separate from the analyzed damage school", unit)
        combat = (PROJECT / "scripts/entities/EntityCombat.gd").read_text(encoding="utf-8")
        self.assertIn("HeroArchetypes.physical_mitigation(unit.armor)", combat)
        self.assertIn("unit.status.armor_shred_amount * HeroArchetypes.ARMOR_FACTOR", combat)
        self.assertIn("minf(HeroArchetypes.MR_MAX, unit.magic_resist)", combat)
        menu = (PROJECT / "scripts/ui/MenuView.gd").read_text(encoding="utf-8")
        self.assertIn("arch.short_label(hero_type, stats)", menu)
        self.assertIn("arch.detail_label(hero_type, stats)", menu)


def tracked_fixture_text(oracle: dict) -> str:
    return json.dumps(oracle, ensure_ascii=False, indent=2) + "\n"


if __name__ == "__main__":
    unittest.main()
