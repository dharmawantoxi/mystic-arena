#!/usr/bin/env python3
"""Regression tests for the native _render.py preparation contract."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
spec = importlib.util.spec_from_file_location("prepare_render", ROOT / "tools/prepare_godot_render.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class RenderPrepareTests(unittest.TestCase):
    def test_check_passes(self) -> None:
        prepare.verify_assets()
        contract = prepare.render_contract()
        tracked = json.loads((PROJECT / "data/render_data.json").read_text(encoding="utf-8"))
        self.assertEqual(contract, tracked)

    def test_budgets_and_timings_match_source(self) -> None:
        contract = prepare.render_contract()
        self.assertEqual(contract["effect_caps"], {"MAX_FLOATING": 300, "MAX_PARTICLES": 500, "MAX_EXPLOSIONS": 80})
        self.assertEqual(contract["timings"]["combo"], 120)
        self.assertEqual(contract["timings"]["wave"], 120)
        self.assertEqual(contract["timings"]["path_preview"], 120)
        self.assertEqual(contract["timings"]["achievement"], 180)
        self.assertEqual(contract["timings"]["boss_intro"], 100)
        self.assertEqual(contract["timings"]["boss_death"], [60, 90])
        self.assertEqual(contract["timings"]["celebration"], 120)
        self.assertEqual(contract["timings"]["level_fade_in"], 30)
        self.assertEqual(contract["shops"], {"radiant": [340, 540], "dire": [940, 180], "size": 60})

    def test_easings_match_python_oracle(self) -> None:
        contract = prepare.render_contract()
        self.assertEqual(contract["easings"]["_ease_out_cubic"], [0.0, 0.578125, 0.875, 0.984375, 1.0])
        self.assertEqual(contract["easings"]["_ease_out_back"][0], 0.0)
        self.assertEqual(contract["easings"]["_ease_out_back"][-1], 1.0)
        self.assertEqual(contract["easings"]["_ease_in_back"][0], 0.0)
        self.assertEqual(contract["easings"]["_ease_out_elastic"][0], 0.0)
        self.assertEqual(contract["easings"]["_ease_out_elastic"][-1], 1.0)
        gd = (PROJECT / "scripts/render/RenderEasing.gd").read_text(encoding="utf-8")
        for name in ("out_back", "in_back", "out_cubic", "out_elastic"):
            self.assertIn(f"static func {name}(t: float) -> float:", gd)

    def test_gdscript_constants_match_contract(self) -> None:
        contract = prepare.render_contract()
        effects = (PROJECT / "scripts/render/CombatEffects.gd").read_text(encoding="utf-8")
        for name, value in contract["effect_caps"].items():
            self.assertRegex(effects, rf"const {name} := {value}\b")
        for name, key in (("COMBO_DURATION", "combo"), ("WAVE_DURATION", "wave"), ("PATH_DURATION", "path_preview"), ("ACHIEVEMENT_DURATION", "achievement")):
            self.assertRegex(effects, rf"const {name} := {contract['timings'][key]}\b")
        cinematics = (PROJECT / "scripts/render/RenderCinematics.gd").read_text(encoding="utf-8")
        self.assertRegex(cinematics, r"const BOSS_INTRO_DURATION := 100\b")
        self.assertRegex(cinematics, r"const BOSS_DEATH_TRUE := 90\b")
        self.assertRegex(cinematics, r"const BOSS_DEATH_MINI := 60\b")
        quality = (PROJECT / "scripts/render/RenderQuality.gd").read_text(encoding="utf-8")
        for level, values in contract["quality_presets"].items():
            self.assertIn(f'"{level}":', quality)
            self.assertIn(f'"max_damage_numbers": {values["max_damage_numbers"]}', quality)
        map_view = (PROJECT / "scripts/render/MapView.gd").read_text(encoding="utf-8")
        self.assertIn("Vector2(340, 540)", map_view)
        self.assertIn("Vector2(940, 180)", map_view)
        self.assertIn("SHOP_SIZE := 60.0", map_view)

    def test_map_coverage(self) -> None:
        contract = prepare.render_contract()
        self.assertEqual(len(contract["map_themes"]), 54)
        self.assertEqual(len(contract["map_png_sha256"]), 54)
        bakes = json.loads((PROJECT / "data/map_bakes.json").read_text(encoding="utf-8"))["maps"]
        for name, digest in contract["map_png_sha256"].items():
            import hashlib
            path = PROJECT / bakes[name]["file"][6:]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
