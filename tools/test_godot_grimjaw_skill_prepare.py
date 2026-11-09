#!/usr/bin/env python3
import ast
import math
import os
import random
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import prepare_godot_grimjaw_skill as prepare


class GrimjawSkillPrepareTest(unittest.TestCase):
    def test_ground_coverage_and_glow_gate(self):
        cases = prepare.front_cases(ground=True)
        self.assertEqual(len(cases), 780)
        self.assertEqual({c["phase"] for c in cases}, {"cast", "charge", "release", "area", "impact", "fade"})
        for case in cases:
            if not case["active"]:
                self.assertEqual(case["commands"], [])
        def commands(key, glow):
            return next(c["commands"] for c in cases if c["key"] == key and c["phase"] == "release"
                        and c["detail"] == 1.0 and c["glow"] == glow and c["x"] > 0)
        for key in "qwer":
            self.assertEqual(len(commands(key, True)) - len(commands(key, False)), 6)
        self.assertFalse(any(c[0] == "line" and c[1][3] == 255 for c in commands("w", False)))
        self.assertTrue(any(c[0] == "line" and c[1][3] == 255 for c in commands("q", False)))

    def test_ground_oracle_tracks_source(self):
        original = prepare.SOURCE.read_text()
        baseline = prepare.front_cases(ground=True)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "grimjaw_fx.py"
            source.write_text(original.replace("int(200 - 90 * t)", "int(199 - 90 * t)"))
            with patch.object(prepare, "SOURCE", source):
                self.assertNotEqual(baseline, prepare.front_cases(ground=True))

    def test_current_and_deterministic(self):
        fixture, config = prepare.build()
        self.assertEqual((fixture, config), prepare.build())
        self.assertEqual(fixture, json.loads(prepare.OUTPUT.read_text()))
        self.assertEqual(config, json.loads(prepare.CONFIG.read_text()))

    def test_timelines_palette_and_coverage(self):
        fixture, config = prepare.build()
        self.assertEqual(len(fixture["cases"]), 7)
        self.assertEqual(set(config["timeline"]), set("qwer"))
        self.assertEqual(config["director_limit"], 3)
        self.assertEqual(config["colors"]["w"], [config["palette"]["heal_dark"], config["palette"]["heal_core"]])
        phases = {row["state"]["phase"] for case in fixture["cases"] for row in case["expected"]}
        self.assertEqual(phases, {"charge", "release", "area", "impact", "fade"})
        for case in fixture["cases"]:
            self.assertFalse(case["expected"][-1]["alive"])
            self.assertEqual(case["expected"][-1]["events"], [])

    def test_ward_release_and_impact_have_no_explosion(self):
        fixture, _ = prepare.build()
        ward = fixture["cases"][1]
        release = [event for row in ward["expected"] if row["state"]["phase"] == "release" for event in row["events"]]
        self.assertEqual([event["args"][2] for event in release], [5])
        self.assertEqual(release[0]["options"]["shape"], "pixel")
        impact = [row for row in ward["expected"] if row["state"]["phase"] == "impact"]
        self.assertTrue(impact)
        self.assertTrue(all(not row["events"] for row in impact))

    def test_all_area_shapes_and_one_shot_bursts(self):
        fixture, _ = prepare.build()
        for case, shape in zip(fixture["cases"][:4], ["ember", "pixel", "ember", "shard"]):
            area = [event for row in case["expected"] if row["state"]["phase"] == "area" for event in row["events"]]
            self.assertTrue(area)
            self.assertEqual({event["options"]["shape"] for event in area}, {shape})
            counts = [event["args"][2] for row in case["expected"] for event in row["events"] if event["type"] == "burst"]
            self.assertLessEqual(counts.count(8), 1)
            self.assertLessEqual(counts.count(7), 1)

    def test_fallback_no_pool_and_skipped_phase(self):
        fixture, config = prepare.build()
        fallback = fixture["cases"][4]
        self.assertEqual(fallback["initial"]["kind"], "q")
        self.assertEqual(fallback["initial"]["radius"], config["radius"]["q"])
        disconnected = fixture["cases"][5]
        self.assertTrue(all(not row["events"] and row["random_index"] == 0 for row in disconnected["expected"]))
        jump = fixture["cases"][-1]["expected"][0]
        self.assertEqual(jump["state"]["phase"], "impact")
        self.assertFalse(jump["state"]["_released"])
        self.assertEqual(jump["events"][0]["args"][2], 7)

    def test_charge_formula_is_executed_source(self):
        baseline, _ = prepare.build()
        text = prepare.SOURCE.read_text().replace("-math.cos(a) * rr * 1.7", "-math.cos(a) * rr * 2.7")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "changed.py"
            path.write_text(text)
            with patch.object(prepare, "SOURCE", path):
                changed, _ = prepare.build()
        self.assertNotEqual(baseline["cases"][0]["expected"], changed["cases"][0]["expected"])

    def test_front_coverage_glow_gate_and_doodle_ring(self):
        fixture, _ = prepare.build()
        self.assertEqual(len(fixture["front"]), 780)
        for case in fixture["front"]:
            self.assertEqual(bool(case["commands"]), case["active"] and case["phase"] in ("release", "area", "impact"))
        release = next(c for c in fixture["front"] if c["key"] == "q" and c["phase"] == "release" and not c["glow"])
        self.assertEqual([c[0] for c in release["commands"]], ["polyline", "polyline"])
        for command in release["commands"]:
            self.assertEqual(command[2][0], command[2][-1])
        self.assertAlmostEqual(release["commands"][1][1][3], 127 * 230 / 255)

    def test_chevrons_have_source_facing_and_stroke(self):
        fixture, _ = prepare.build()
        cases = [c for c in fixture["front"] if c["key"] == "e" and c["phase"] == "area" and c["x"] > 0 and c["detail"] == 1 and not c["glow"]]
        left = next(c for c in cases if c["facing"] == -1)
        right = next(c for c in cases if c["facing"] == 1)
        self.assertEqual(len(left["commands"]), 4)
        for a, b in zip(left["commands"], right["commands"]):
            self.assertEqual(a[0], "polygon_outline")
            self.assertEqual(a[3], 2)
            for p, q in zip(a[2], b[2]):
                self.assertEqual(p[0] + q[0], 200)
                self.assertEqual(p[1], q[1])

    def test_ring_helper_is_actual_source(self):
        baseline, _ = prepare.build()
        text = prepare.SOURCE.read_text().replace("radius * 13 + i * 7", "radius * 17 + i * 7")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "changed.py"
            path.write_text(text)
            with patch.object(prepare, "SOURCE", path):
                changed, _ = prepare.build()
        self.assertNotEqual(baseline["front"], changed["front"])
        self.assertEqual(baseline["cases"], changed["cases"])

    def test_real_pygame_front_smoke(self):
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        try:
            import pygame
        except ImportError:
            self.skipTest("pygame optional locally; installed in CI")
        env = prepare.environment()
        env["pygame"] = pygame
        env["_SCRATCH"] = {}
        env["skill_detail"] = lambda: 1.0
        tree = ast.parse(prepare.SOURCE.read_text())
        helpers = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("_scratch", "ring_surface")]
        exec(compile(ast.Module(body=helpers, type_ignores=[]), str(prepare.SOURCE), "exec"), env)
        for glow in (False, True):
            env["glow_allowed"] = lambda: glow
            for key in "qwer":
                skill = env["SkillFX"](key, 320, 180)
                for age in (skill.t_charge * .5, (skill.t_charge + skill.t_release) * .5,
                            (skill.t_release + skill.t_area) * .5,
                            (skill.t_area + skill.t_impact) * .5, skill.t_impact):
                    skill.age = age
                    skill._set_phase()
                    canvas = pygame.Surface((640, 360), pygame.SRCALPHA)
                    skill.draw_front(canvas)
                    self.assertEqual(any(pygame.image.tobytes(canvas, "RGB")),
                                     skill.phase in ("release", "area", "impact"))

    def test_stale_check_never_rewrites(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "stale.json"
            output.write_text("{}\n")
            with patch.object(prepare, "OUTPUT", output), patch("sys.argv", ["prepare", "--check"]):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    prepare.main()
            self.assertEqual(error.exception.code, 1)
            self.assertEqual(output.read_text(), "{}\n")


if __name__ == "__main__":
    unittest.main()
