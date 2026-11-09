#!/usr/bin/env python3
import ast
import json
import unittest
import prepare_godot_hero_feedback as prepare


class HeroFeedbackPrepareTest(unittest.TestCase):
    def test_current(self):
        script, fixture = prepare.build()
        self.assertEqual(prepare.OUT.read_text(), script)
        self.assertEqual(prepare.FIXTURE.read_text(), fixture)

    def test_coverage(self):
        _, fixture = prepare.build()
        cases = json.loads(fixture)["cases"]
        self.assertEqual(len(cases), 88)
        self.assertEqual({c["hero"] for c in cases}, set(prepare.STARTERS))
        self.assertEqual(sum(c["method"] == "on_cast" for c in cases), 20)

    def test_unsupported_feedback_control_flow_fails_closed(self):
        body = ast.parse("for i in range(2):\n    hit_stop(0.04)").body
        with self.assertRaises(ValueError):
            prepare.sliced(body)

    def test_unsupported_condition_fails_closed(self):
        body = prepare.sliced(ast.parse("if self.enabled:\n    shake(4, 0.2)").body)
        with self.assertRaises(ValueError):
            prepare.statements(body, 0)

    def test_actual_source_formulas(self):
        cases = json.loads(prepare.build()[1])["cases"]
        zephyr = next(c for c in cases if c["hero"] == "zephyr"
                      and c["method"] == "projectile_hit"
                      and c["params"] == {"damage": 0.0, "crit": False})
        self.assertEqual(zephyr["events"][0][0], "shake")
        self.assertAlmostEqual(zephyr["events"][1][1][0], 0.052)


if __name__ == "__main__":
    unittest.main()
