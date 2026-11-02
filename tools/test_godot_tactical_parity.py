#!/usr/bin/env python3
"""Active tactical oracle gate for the native Godot project.

The removed legacy godot/ C++ port is not a prerequisite. This gate checks the
tracked closed-world pygame fixture consumed by TacticalParityTest.gd and the
native wiring that replaces the old placeholder TacticalCommands.gd.
"""
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
import prepare_godot_tactical as prep  # noqa: E402


class TacticalParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads((PROJECT / "data/tactical.json").read_text(encoding="utf-8"))
        cls.fixture = json.loads((PROJECT / "tests/fixtures/tactical_parity.json").read_text(encoding="utf-8"))

    def test_hashes_match_source(self):
        digest = hashlib.sha256((ROOT / "tactical_commands.py").read_bytes()).hexdigest()
        self.assertEqual(self.contract["source_sha256"], digest)
        self.assertEqual(self.fixture["source_sha256"], digest)

    def test_check_cli_passes(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/prepare_godot_tactical.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_oracle_guards(self):
        scenarios = {row["name"]: row for row in self.fixture["scenarios"]}
        tap = scenarios["hold_tap_short"]["steps"][1]["snapshot"]["manager"]
        self.assertGreater(tap["command_timer"], 30)
        hold = scenarios["hold_long_truncate"]["steps"][1]["snapshot"]["manager"]
        self.assertEqual(hold["command_timer"], 30)
        dead = scenarios["gather_oneshot_push_dead_arrived"]["steps"][-1]["snapshot"]["manager"]
        self.assertFalse(dead["gather_push_fired"])
        armed = scenarios["hold_armed_boss_appears"]["steps"]
        self.assertFalse(armed[0]["result"])
        self.assertTrue(armed[1]["snapshot"]["manager"]["hold_has_fired"])
        self.assertEqual(scenarios["auto_attack_boss_trigger"]["steps"][-1]["snapshot"]["manager"]["active_command"], "attack_boss")
        self.assertIsNone(scenarios["auto_attack_boss_no_roll"]["steps"][-1]["snapshot"]["manager"]["active_command"])

    def test_native_wiring_is_present(self):
        manager = (PROJECT / "scripts/core/TacticalCommands.gd").read_text(encoding="utf-8")
        model = (PROJECT / "scripts/core/MatchModel.gd").read_text(encoding="utf-8")
        game = (PROJECT / "scripts/game/CoreGame.gd").read_text(encoding="utf-8")
        main = (PROJECT / "scripts/Main.gd").read_text(encoding="utf-8")
        hud = (PROJECT / "scripts/ui/HudView.gd").read_text(encoding="utf-8")
        runner = (PROJECT / "tests/run_all.gd").read_text(encoding="utf-8")
        self.assertIn("data/tactical.json", manager)
        self.assertIn("hold_start", manager)
        self.assertIn("tactical.update(self)", model)
        self.assertNotIn("apply_tactical", model)
        self.assertIn("hold_start(action, [], follow_mouse)", game)
        self.assertIn('source.begins_with("key:") and command == "gather"', main)
        self.assertIn("world_draw_data", hud)
        self.assertIn("TacticalParity.run(self)", runner)


if __name__ == "__main__":
    unittest.main()
