#!/usr/bin/env python3
"""Regression tests for the heroes renderer migration contract."""
import copy
import unittest
from unittest.mock import patch
import prepare_godot_heroes as prepare


class HeroesPrepareTest(unittest.TestCase):
    def test_contract_is_current(self):
        import json
        self.assertEqual(prepare.build(), json.loads(prepare.OUTPUT.read_text()))

    def test_all_sources_and_units(self):
        data = prepare.build()
        self.assertIn("heroes/__init__.py", data["sources"])
        self.assertIn("heroes/combat_feel.py", data["sources"])
        self.assertEqual(len(data["units"]), 222)
        self.assertEqual(sum(r["renderer"] == "hero" for r in data["units"].values()), 6)

    def test_no_false_native_fx_claim(self):
        modules = prepare.module_status()
        self.assertEqual(set(modules), {p.name for p in (prepare.ROOT / "heroes").glob("*.py")})
        self.assertTrue(modules["combat_feel.py"]["native"])
        for name, row in modules.items():
            if name.endswith("_fx.py"):
                self.assertNotIn(row["status"], ("native", "complete"))
                if row["native"]:
                    self.assertIn(row["status"], (
                        "native_feedback_only_visual_director_pending",
                        "native_feedback_hurt_death_slices_full_director_pending",
                        "native_zephyr_live_slices_full_director_pending"))
                else:
                    self.assertEqual(row["status"], "pending_native_port")

    def test_invalid_span_rejected(self):
        import json
        entry = copy.deepcopy(json.loads((prepare.PROJECT / "data/baked_units.json").read_text())["units"]["grimjaw"])
        entry["anims"]["idle"] = [9999, 8]
        with self.assertRaises(ValueError):
            prepare.atlas(entry)

    def test_missing_asset_fails_closed(self):
        with patch.object(prepare.Path, "read_bytes", side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                prepare.atlas({"png": "res://missing.png"})


if __name__ == "__main__":
    unittest.main()
