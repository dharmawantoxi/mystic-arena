#!/usr/bin/env python3
"""Check the executable Python oracle, including ties-to-even and fake SDL time."""
import json
import unittest
import prepare_godot_combat_feel as prepare


class CombatFeelPrepareTest(unittest.TestCase):
    def test_current(self):
        self.assertEqual(prepare.build(), json.loads(prepare.OUTPUT.read_text()))

    def test_deterministic(self):
        self.assertEqual(prepare.build(), prepare.build())

    def test_freeze_does_not_stack(self):
        case = prepare.build()["cases"][0]
        self.assertEqual(case["expected"][2]["stats"]["hitstop_frames"], 5)
        self.assertEqual([r["result"] for r in case["expected"][3:]],
                         [True, True, True, True, True, False])

    def test_round_is_python_not_godot(self):
        rows = prepare.build()["cases"][1]["expected"]
        self.assertEqual(rows[0]["stats"]["hitstop_frames"], 2)
        self.assertEqual(rows[-1]["stats"]["hitstop_frames"], 4)

    def test_repeated_clock_does_not_decay_twice(self):
        rows = prepare.build()["cases"][4]["expected"]
        self.assertEqual(rows[2], rows[3])
        self.assertEqual(rows[5], rows[6])


if __name__ == "__main__":
    unittest.main()
