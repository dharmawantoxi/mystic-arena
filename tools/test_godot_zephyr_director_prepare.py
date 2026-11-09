#!/usr/bin/env python3
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import prepare_godot_zephyr_director as prepare


class ZephyrDirectorPrepareTest(unittest.TestCase):
    def test_current_and_deterministic(self):
        fixture, config = prepare.build()
        self.assertEqual((fixture, config), prepare.build())
        self.assertEqual(fixture, json.loads(prepare.OUTPUT.read_text()))
        self.assertEqual(config, json.loads(prepare.CONFIG.read_text()))

    def test_state_priority_and_death_lock(self):
        fixture, _ = prepare.build()
        rows = fixture["cases"][0]
        states = [row["expected"]["state"]["state"] for row in rows]
        self.assertTrue({"IDLE", "WALK", "RUN", "CHARGE", "SWING", "ATTACK", "SKILL", "SPECIAL", "HURT", "DEATH"}.issubset(states))
        self.assertEqual(states[-2:], ["DEATH", "DEATH"])

    def test_strict_lock_threshold(self):
        fixture, _ = prepare.build()
        rows = fixture["cases"][1]
        self.assertEqual([r["expected"]["state"]["state"] for r in rows],
                         ["HURT", "HURT", "HURT", "IDLE"])

    def test_swing_edge_and_source_recipe(self):
        fixture, _ = prepare.build()
        rows = fixture["cases"][2]
        self.assertEqual([r["expected"]["edge"] for r in rows], ["start", "", "end", "start", "end"])
        burst = rows[0]["expected"]["bursts"][0]
        self.assertEqual(burst["position"], [24.75, 21.75])
        self.assertEqual(burst["count"], 2)
        self.assertEqual(burst["options"]["direction"], 0.0)
        self.assertEqual(burst["options"]["shape"], "pixel")

    def test_attack_phase_boundaries_and_clamp(self):
        fixture, _ = prepare.build()
        self.assertEqual([r["expected"]["state"]["anim_phase"] for r in fixture["cases"][3]],
                         ["ANTICIPATION", "WINDUP", "SWING", "IMPACT", "FOLLOW", "RECOVERY", "RECOVERY", "RECOVERY"])

    def test_state_guard_is_executed_source(self):
        baseline, _ = prepare.build()
        source = prepare.SOURCE.read_text().replace("self.state_time > 0.05", "self.state_time > 0.01")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "changed.py"
            path.write_text(source)
            with patch.object(prepare, "SOURCE", path):
                changed, _ = prepare.build()
        self.assertNotEqual(baseline["cases"][1], changed["cases"][1])

    def test_stale_check_never_rewrites(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stale.json"
            path.write_text("{}\n")
            with patch.object(prepare, "OUTPUT", path), patch("sys.argv", ["prepare", "--check"]):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    prepare.main()
            self.assertEqual(error.exception.code, 1)
            self.assertEqual(path.read_text(), "{}\n")


if __name__ == "__main__":
    unittest.main()
