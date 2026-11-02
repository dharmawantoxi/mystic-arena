#!/usr/bin/env python3
"""Closed-world checks for the bosses/ pygame oracle fixture."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "godot_rebuild/tests/fixtures/bosses_parity.json"


class BossesParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oracle = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_runtime_rows_cover_every_boss(self):
        rows = self.oracle["runtime"]["bosses"]
        self.assertEqual(len(rows), 216)
        self.assertEqual(len({r["boss_type"] for r in rows}), 216)
        for row in rows:
            self.assertIn(row["boss_class"], ("mini", "true"))
            self.assertGreater(row["hp"], 0)
            self.assertGreater(row["max_damage_per_hit"], 0)
            self.assertEqual(row["entrance_frames"], 180 if row["boss_class"] == "true" else 120)
            self.assertAlmostEqual(row["tenacity"], 0.50)
            self.assertAlmostEqual(row["damage_reduction"], 0.30 if row["boss_class"] == "true" else 0.20)

    def test_smart_ai_traces_are_nonempty(self):
        smart = self.oracle["smart_ai"]
        self.assertEqual(len(smart["bosses"]), 79)
        self.assertEqual(len(smart["bosses"]), 79)
        for row in smart["bosses"]:
            self.assertEqual(set(row["scenarios"]), {"cluster", "duo_low", "solo_edge"})
            for case in row["scenarios"].values():
                self.assertGreater(case["frames"], 0)
                self.assertIn("final", case)
                self.assertIn("events", case)

    def test_controller_scenarios(self):
        cases = self.oracle["controller"]
        self.assertEqual(len(cases), 10)
        self.assertEqual({c["scenario"] for c in cases},
                         {"basic", "kite", "entrance", "stun", "lane", "heal"})
        for case in cases:
            self.assertEqual(len(case["steps"]), case["frames"])

    def test_combat_order_cases(self):
        cases = self.oracle["combat"]
        self.assertEqual(len(cases), 10)
        by_name = {c["name"]: c for c in cases}
        self.assertEqual(by_name["blind_miss"]["expected"]["dealt"], 0)
        self.assertGreater(by_name["blind_hit"]["expected"]["dealt"], 0)
        self.assertGreater(by_name["true_strike"]["expected"]["dealt"], 0)
        self.assertFalse(by_name["lethal"]["expected"]["alive"])
        self.assertTrue(by_name["lethal"]["expected"]["defeated"])
        self.assertGreater(by_name["cap"]["expected"]["dealt"], 0)
        self.assertLessEqual(by_name["cap"]["expected"]["dealt"], by_name["cap"]["cap_override"])

    def test_normalization_range_and_unlock_fields(self):
        final = self.oracle["normalization"]["final"]
        contract = json.loads((ROOT / "godot_rebuild/data/bosses.json").read_text(encoding="utf-8"))
        hints = contract["melee_role_hints"]
        for kind in ("mini", "true"):
            for key, row in final[kind].items():
                unlock = row.get("hero_unlock")
                if not unlock:
                    continue
                role = str(unlock.get("role", "")).lower()
                if any(h in role for h in hints):
                    self.assertEqual(unlock["range"], 70, f"{key} melee role range")
                else:
                    self.assertIn(unlock["range"], [70] + list(range(120, 221)), f"{key} range band")
                if unlock.get("skill_range", 0) > 0:
                    self.assertGreaterEqual(unlock["skill_range"], unlock["range"], f"{key} skill range")
                for field in ("hp", "damage", "skill_damage"):
                    self.assertGreaterEqual(int(unlock.get(field, 0)), 0, f"{key} {field}")

if __name__ == "__main__":
    unittest.main()
