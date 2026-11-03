#!/usr/bin/env python3
"""Tests for the hero_skills -> Godot closed-world exporter and its gates."""

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
import prepare_godot_hero_skills as prepare  # noqa: E402

CONTRACT_PATH = ROOT / "godot_rebuild/data/hero_skills.json"
FIXTURE_PATH = ROOT / "godot_rebuild/tests/fixtures/hero_skills_parity.json"


def _current():
    contract = prepare.build_contract()
    with prepare.source_module() as module:
        oracle = prepare.build_oracle(contract, module)
    return contract, oracle


class PrepareGodotHeroSkillsTest(unittest.TestCase):
    def test_prepare_check_is_current(self):
        result = subprocess.run(
            [sys.executable, "tools/prepare_godot_hero_skills.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_contract_and_fixture_are_closed_world(self):
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        oracle = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(contract["schema"], 1)
        self.assertEqual(contract["source"], "hero_skills/")
        self.assertEqual(sorted(contract["source_files"]), ["__init__.py", "_bundle.py"])

        digest = hashlib.sha256()
        for name in ("__init__.py", "_bundle.py"):
            data = (ROOT / "hero_skills" / name).read_bytes()
            self.assertEqual(contract["source_files"][name], hashlib.sha256(data).hexdigest())
            digest.update(name.encode("utf-8"))
            digest.update(b"\0")
            digest.update(data)
        self.assertEqual(contract["source_sha256"], digest.hexdigest())
        self.assertEqual(oracle["source_sha256"], contract["source_sha256"])

        kit_hash = hashlib.sha256(
            (ROOT / "godot_rebuild/scripts/entities/generated/HeroSkillKit.gd").read_bytes()
        ).hexdigest()
        self.assertEqual(contract["generated_kit"]["sha256"], kit_hash)
        self.assertEqual(oracle["generated_kit_sha256"], kit_hash)
        for name in (
            "tools/gen_hero_skill_kit.py",
            "tools/prepare_godot_entities.py",
            "tools/prepare_godot_hero_skills.py",
        ):
            self.assertEqual(
                contract["tooling_sha256"][name],
                hashlib.sha256((ROOT / name).read_bytes()).hexdigest(),
                name,
            )

        self.assertEqual(contract["counts"]["starters"], 6)
        self.assertEqual(contract["counts"]["hero_handlers"], 222)
        self.assertEqual(contract["counts"]["recipes"], 66)
        self.assertEqual(contract["counts"]["state_keys"], 91)
        self.assertEqual(contract["counts"]["kit_static_functions"], 330)
        self.assertEqual(len(contract["handler_map"]), 222)
        self.assertEqual(len(contract["registry"]), 66)
        self.assertEqual(len(contract["state_keys"]), 91)
        self.assertTrue(contract["base"]["require_target"])
        self.assertAlmostEqual(contract["base"]["target_range_slack"], 1.15)
        self.assertEqual(contract["default_visual_duration"], {"q": 60, "w": 90, "e": 60, "r": 100})

        self.assertEqual(len(oracle["hero_kind_cases"]), 223)
        self.assertEqual(len(oracle["visual_duration_cases"]), 892)
        self.assertEqual(len(oracle["registry_cases"]), 868)
        self.assertEqual(len(oracle["cooldown_cases"]), 16)
        self.assertEqual(len(oracle["skill_range_cases"]), 7)
        self.assertEqual(len(oracle["geometry_cases"]), 3)
        self.assertEqual(len(oracle["aoe_cases"]), 4)
        self.assertEqual(len(oracle["trigger_cases"]), 37)
        self.assertEqual(oracle["contract_cases"]["hero_handlers"], 222)
        self.assertEqual(oracle["contract_cases"]["recipes"], 66)

    def test_outputs_are_deterministic_python_oracles(self):
        contract, oracle = _current()
        self.assertEqual(CONTRACT_PATH.read_text(encoding="utf-8"), prepare._text(contract))
        self.assertEqual(
            FIXTURE_PATH.read_text(encoding="utf-8"), prepare._text(oracle, float_digits=12)
        )
        again_contract, again_oracle = _current()
        self.assertEqual(again_contract, contract)
        self.assertEqual(again_oracle, oracle)

    def test_stale_source_hash_fails_check(self):
        contract, _ = _current()
        stale = dict(contract)
        stale["source_sha256"] = "0" * 64
        with mock.patch.object(prepare, "build_contract", return_value=stale):
            with self.assertRaises(SystemExit) as raised:
                prepare.main(["--check"])
        self.assertNotEqual(raised.exception.code, 0)

    def test_stale_python_oracle_fails_check(self):
        _, oracle = _current()
        stale = dict(oracle)
        stale["registry_cases"] = []
        with mock.patch.object(prepare, "build_oracle", return_value=stale):
            with self.assertRaises(SystemExit) as raised:
                prepare.main(["--check"])
        self.assertNotEqual(raised.exception.code, 0)

    def test_native_and_project_wiring(self):
        loader = (ROOT / "godot_rebuild/scripts/core/HeroSkills.gd").read_text(encoding="utf-8")
        self.assertIn("class_name HeroSkills", loader)
        self.assertIn("res://data/hero_skills.json", loader)
        self.assertIn("static func shared()", loader)
        self.assertIn("KIT.cast_q(", loader)
        core = (ROOT / "godot_rebuild/scripts/core/CoreData.gd").read_text(encoding="utf-8")
        self.assertIn("skills_path := HeroSkills.DEFAULT_PATH", core)
        self.assertIn("skills.valid()", core)
        battle = (ROOT / "godot_rebuild/scripts/core/BattleUnit.gd").read_text(encoding="utf-8")
        self.assertIn("HeroSkills.shared().init_state(self)", battle)
        self.assertIn("HeroSkills.shared().cast(self, key", battle)
        self.assertNotIn(
            'preload("res://scripts/entities/generated/HeroSkillKit.gd")', battle
        )
        movement = (
            ROOT / "godot_rebuild/scripts/entities/EntityMovement.gd"
        ).read_text(encoding="utf-8")
        self.assertIn("HeroSkills.shared().update_timers(", movement)
        self.assertNotIn(
            'preload("res://scripts/entities/generated/HeroSkillKit.gd")', movement
        )
        parity = (ROOT / "godot_rebuild/tests/HeroSkillsParityTest.gd").read_text(encoding="utf-8")
        self.assertIn("hero_skills_parity.json", parity)
        self.assertIn(
            "SkillsParity.run(self)",
            (ROOT / "godot_rebuild/tests/run_all.gd").read_text(encoding="utf-8"),
        )
        validator = (ROOT / "godot_rebuild/tests/validate_project.py").read_text(encoding="utf-8")
        self.assertIn("HeroSkills.gd", validator)
        self.assertIn("hero_skills.json", validator)
        self.assertIn("HeroSkillsParityTest.gd", validator)
        for workflow in ("godot-check.yml", "godot-rebuild.yml"):
            text = (ROOT / ".github/workflows" / workflow).read_text(encoding="utf-8")
            self.assertIn("python3 tools/prepare_godot_hero_skills.py --check", text)
            self.assertIn("python3 tools/test_godot_hero_skills_prepare.py", text)
            self.assertIn("hero_skills/**", text)
            self.assertIn("tools/prepare_godot_hero_skills.py", text)
            self.assertIn("tools/test_godot_hero_skills_prepare.py", text)
            self.assertIn("godot_rebuild/scripts/core/HeroSkills.gd", text)
            self.assertIn("godot_rebuild/tests/HeroSkillsParityTest.gd", text)


if __name__ == "__main__":
    unittest.main()
