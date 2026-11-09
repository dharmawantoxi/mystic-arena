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
import prepare_godot_zephyr_skill as prepare


class ZephyrSkillPrepareTest(unittest.TestCase):
    def test_current_and_deterministic(self):
        fixture, config = prepare.build()
        self.assertEqual((fixture, config), prepare.build())
        self.assertEqual(fixture, json.loads(prepare.OUTPUT.read_text()))
        self.assertEqual(config, json.loads(prepare.CONFIG.read_text()))

    def test_all_phases_and_skills(self):
        fixture, config = prepare.build()
        self.assertEqual(set(config["timeline"]), set("qwer"))
        self.assertEqual(config["director_limit"], 3)
        self.assertEqual(len(fixture["cases"]), 7)
        phases = {row["state"]["phase"] for case in fixture["cases"] for row in case["expected"]}
        self.assertEqual(phases, {"charge", "release", "area", "impact", "fade"})
        for case in fixture["cases"]:
            self.assertEqual(case["initial"]["phase"], "cast")
            self.assertFalse(case["expected"][-1]["alive"])
            self.assertEqual(case["expected"][-1]["events"], [])

    def test_one_shot_bursts_and_tape(self):
        fixture, _ = prepare.build()
        for case in fixture["cases"]:
            counts = [event["args"][2] for row in case["expected"] for event in row["events"]
                      if event["type"] == "burst"]
            self.assertLessEqual(counts.count(8), 1)
            self.assertLessEqual(counts.count(4), 1)
            self.assertLessEqual(counts.count(7), 1)
        self.assertGreater(fixture["cases"][0]["expected"][-1]["random_index"], 0)

    def test_fallback_radius_and_no_pool(self):
        fixture, config = prepare.build()
        fallback = fixture["cases"][4]
        self.assertEqual(fallback["initial"]["kind"], "q")
        self.assertEqual(fallback["initial"]["radius"], config["radius"]["q"])
        disconnected = fixture["cases"][5]
        self.assertEqual(disconnected["initial"]["radius"], 35)
        self.assertTrue(all(not row["events"] for row in disconnected["expected"]))
        self.assertEqual(disconnected["expected"][-1]["random_index"], 0)

    def test_large_step_does_not_replay_skipped_phases(self):
        fixture, _ = prepare.build()
        case = fixture["cases"][-1]
        self.assertEqual(case["expected"][0]["state"]["phase"], "impact")
        self.assertFalse(case["expected"][0]["state"]["_released"])
        self.assertEqual([e["args"][2] for e in case["expected"][0]["events"]], [7])
        self.assertEqual(case["expected"][1]["events"], [])

    def test_emission_is_actual_source(self):
        baseline, _ = prepare.build()
        text = prepare.SOURCE.read_text().replace("-math.cos(a) * rr * 1.6", "-math.cos(a) * rr * 2.6")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "changed.py"
            source.write_text(text)
            with patch.object(prepare, "SOURCE", source):
                changed, _ = prepare.build()
        self.assertNotEqual(baseline["cases"][0]["expected"], changed["cases"][0]["expected"])

    def test_front_coverage_and_empty_phases(self):
        fixture, _ = prepare.build()
        self.assertEqual(len(fixture["front"]), 312)
        self.assertEqual({c["detail"] for c in fixture["front"]}, {.35, .55, 1.0})
        for case in fixture["front"]:
            visible = case["active"] and case["phase"] in ("release", "area", "impact")
            self.assertEqual(bool(case["commands"]), visible)
        area = next(c for c in fixture["front"] if c["phase"] == "area" and c["detail"] == 1)
        self.assertEqual(len(area["commands"]), 20)
        self.assertTrue(all(c[0] == "polygon" for c in area["commands"]))

    def test_ring_helper_geometry_and_alpha(self):
        fixture, _ = prepare.build()
        case = next(c for c in fixture["front"] if c["kind"] == "q" and c["x"] > 0
                    and c["phase"] == "release")
        self.assertEqual([c[0] for c in case["commands"]], ["glow", "circle"])
        ring = case["commands"][1]
        self.assertEqual(ring[1][3], 230)
        self.assertEqual(ring[2:], [[100, 200], 24, 5])

    def test_rune_geometry_is_actual_source(self):
        baseline, _ = prepare.build()
        text = prepare.SOURCE.read_text().replace("a * spd, 8 + k * 4", "a * spd * 2.0, 8 + k * 4")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "changed.py"
            path.write_text(text)
            with patch.object(prepare, "SOURCE", path):
                changed, _ = prepare.build()
        self.assertNotEqual(baseline["front"], changed["front"])

    def test_real_pygame_front_smoke(self):
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        try:
            import pygame
        except ImportError:
            self.skipTest("pygame is optional locally; installed in CI")
        tree = ast.parse(prepare.SOURCE.read_text())
        functions = {"_clamp_color", "_mix", "_cache_put", "_scratch", "glow_surface", "ring_surface"}
        nodes = [n for n in tree.body if
                 (isinstance(n, ast.FunctionDef) and n.name in functions)
                 or (isinstance(n, ast.ClassDef) and n.name == "SkillFX")]
        env = {"pygame": pygame, "math": math, "random": random.Random(1234),
               "P": prepare.particles.bolt.palette(tree), "_SURF_CACHE": {},
               "_SURF_CACHE_MAX": 384, "_SCRATCH": {}, "skill_detail": lambda: 1.0}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(prepare.SOURCE), "exec"), env)
        for kind in "qwer":
            skill = env["SkillFX"](kind, 320, 180)
            ages = [skill.t_charge * .5, (skill.t_charge + skill.t_release) * .5,
                    (skill.t_release + skill.t_area) * .5, (skill.t_area + skill.t_impact) * .5,
                    (skill.t_impact + skill.total) * .5]
            for age in ages:
                skill.age = age
                skill._set_phase()
                canvas = pygame.Surface((640, 360), pygame.SRCALPHA)
                skill.draw_front(canvas)
                self.assertEqual(any(pygame.image.tobytes(canvas, "RGB")),
                                 skill.phase in ("release", "area", "impact"))

    def test_ground_coverage_primitives_and_crack_alpha(self):
        fixture, _ = prepare.build()
        self.assertEqual(len(fixture["ground"]), 288)
        for case in fixture["ground"]:
            self.assertEqual(bool(case["commands"]), case["active"])
        area = next(c for c in fixture["ground"] if c["phase"] == "area" and c["detail"] == 1)
        self.assertEqual({c[0] for c in area["commands"]}, {"oval", "line"})
        cracks = [c for c in area["commands"] if c[0] == "line" and c[1][3] == 255]
        self.assertEqual(len(cracks), 20)

    def test_ground_hash_formula_is_actual_source(self):
        baseline, _ = prepare.build()
        text = prepare.SOURCE.read_text().replace("2654435761", "2654435767")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "changed.py"
            source.write_text(text)
            with patch.object(prepare, "SOURCE", source):
                changed, _ = prepare.build()
        self.assertNotEqual(baseline["ground"], changed["ground"])
        self.assertEqual(baseline["front"], changed["front"])

    def test_real_pygame_ground_and_rect_smoke(self):
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        try:
            import pygame
        except ImportError:
            self.skipTest("pygame optional locally; installed in CI")
        for box in ((4, 8, 120, 50), (4, 8, 84, 35)):
            self.assertEqual(prepare.Rect(*box).inflate(-6, -3).values,
                             list(pygame.Rect(*box).inflate(-6, -3)))
        tree = ast.parse(prepare.SOURCE.read_text())
        functions = {"_clamp_color", "_mix", "_cache_put", "_scratch", "ground_glow_surface", "_hash01"}
        nodes = [n for n in tree.body if
                 (isinstance(n, ast.FunctionDef) and n.name in functions)
                 or (isinstance(n, ast.ClassDef) and n.name == "SkillFX")]
        env = {"pygame": pygame, "math": math, "random": random.Random(1234),
               "P": prepare.particles.bolt.palette(tree), "_SURF_CACHE": {},
               "_SURF_CACHE_MAX": 384, "_SCRATCH": {}, "skill_detail": lambda: 1.0}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(prepare.SOURCE), "exec"), env)
        for kind in "qwer":
            skill = env["SkillFX"](kind, 320, 180)
            # Constructor-only cast is never entered by legacy update/draw.
            with self.assertRaises(ValueError):
                skill.draw_ground(pygame.Surface((640, 360), pygame.SRCALPHA))
            for age in (0, skill.t_charge, skill.t_release, skill.t_area, skill.t_impact):
                skill.age = age
                skill._set_phase()
                surface = pygame.Surface((640, 360), pygame.SRCALPHA)
                skill.draw_ground(surface)
                self.assertTrue(any(pygame.image.tobytes(surface, "RGB")))

    def test_stale_check_does_not_rewrite(self):
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
