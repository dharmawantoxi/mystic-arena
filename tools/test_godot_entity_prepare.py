#!/usr/bin/env python3
"""Regression tests for the native _entity.py preparation pipeline."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
sys.path.insert(0, str(ROOT / "tools"))
import prepare_godot_entities as prep  # noqa: E402


class EntityPrepareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kits = prep.kits()
        cls.units = json.loads((PROJECT / "data/baked_units.json").read_text(encoding="utf-8"))
        cls.props = json.loads((PROJECT / "data/baked_props.json").read_text(encoding="utf-8"))

    def test_generated_kits_cover_skill_and_boss_dispatch(self):
        self.assertEqual(set(self.kits), {"HeroSkillKit.gd", "BossKit.gd"})
        hero = self.kits["HeroSkillKit.gd"]
        boss = self.kits["BossKit.gd"]
        self.assertIn("static func cast_q(", hero)
        self.assertIn("static func update_timers(", hero)
        self.assertIn("static func dispatch(", boss)
        self.assertIn(".pos", hero)
        self.assertNotIn(".global_position", hero)
        self.assertIn("attack_cooldown_seconds", hero)

    def test_sprite_manifest_counts_and_files(self):
        self.assertGreaterEqual(len(self.units["units"]), 222)
        self.assertEqual(len(self.props["minions"]), 10)
        self.assertEqual(len(self.props["towers"]), 8)
        self.assertEqual(len(self.props["nexus"]), 2)
        for entry in self.units["units"].values():
            path = PROJECT / entry["png"].removeprefix("res://")
            self.assertTrue(path.is_file(), path)
            if entry.get("skills_png"):
                self.assertTrue((PROJECT / entry["skills_png"].removeprefix("res://")).is_file())
        for group in ("minions", "towers", "nexus"):
            for entry in self.props[group].values():
                self.assertTrue((PROJECT / entry["png"].removeprefix("res://")).is_file())

    def test_check_is_current(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/prepare_godot_entities.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
