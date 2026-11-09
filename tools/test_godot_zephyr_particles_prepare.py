#!/usr/bin/env python3
import ast
import math
import os
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import prepare_godot_zephyr_particles as prepare


class ZephyrParticlesPrepareTest(unittest.TestCase):
    def test_current_and_deterministic(self):
        first = prepare.build()
        self.assertEqual(first, prepare.build())
        self.assertEqual(first, json.loads(prepare.OUTPUT.read_text()))

    def test_budgets_capacity_and_clear(self):
        fixture = prepare.build()
        self.assertEqual(len(fixture["pools"]), 4)
        for case in fixture["pools"]:
            for row in case["expected"]:
                self.assertLessEqual(len(row["live"]), case["cap"])
                self.assertLessEqual(row["pooled"], case["cap"])
            self.assertEqual(case["expected"][-1]["live"], [])
        self.assertEqual(fixture["pools"][0]["expected"][0]["result"], 0)

    def test_source_impact_recipes(self):
        fixture = prepare.build()
        self.assertEqual(len(fixture["recipes"]), 16)
        normal = next(c for c in fixture["recipes"] if c["power"] == 0.7
                      and not c["critical"] and c["angle"] == 0.0)
        self.assertEqual([r["count"] for r in normal["expected"]], [13, 6])
        self.assertEqual([r["options"]["shape"] for r in normal["expected"]], ["streak", "shard"])

    def test_motion_and_draw_shapes(self):
        cases = prepare.build()["particles"]
        self.assertEqual(len(cases), 12)
        self.assertEqual({c["options"]["shape"] for c in cases}, {"pixel", "streak", "shard", "spark", "glow", "unknown"})
        for case in cases:
            self.assertFalse(case["expected"][-1]["state"]["active"])
            self.assertEqual(case["expected"][-1]["commands"], [])

    def test_spark_and_glow_helper_requests(self):
        cases = prepare.build()["particles"]
        for shape in ("spark", "glow"):
            case = next(c for c in cases if c["options"]["shape"] == shape)
            command = case["expected"][0]["commands"][0]
            self.assertEqual(command[0], shape)
            self.assertEqual(command[2], [-28, 5] if shape == "spark" else [-34, -1])
            self.assertEqual(command[3], 8 if shape == "spark" else 14)
            self.assertEqual(command[1][3], 180 if shape == "spark" else 255)
            if shape == "glow":
                self.assertEqual(command[4], 0.9)
        unknown = next(c for c in cases if c["options"]["shape"] == "unknown")
        pixel = next(c for c in cases if c["options"]["shape"] == "pixel")
        self.assertEqual(unknown["expected"][0]["commands"], pixel["expected"][0]["commands"])

    def test_opacity_gate_applies_before_helpers(self):
        env, _ = prepare.environment()
        for shape in ("spark", "glow", "pixel"):
            for alpha in (0, 3, 4):
                particle = env["Particle"]().spawn(0, 0, 0, 0, 1, 1, (10, 20, 30),
                                                  shape=shape, alpha=alpha)
                self.assertEqual(bool(prepare.geometry(particle)), alpha > 3)

    def test_real_pygame_all_shape_smoke(self):
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        try:
            import pygame
        except ImportError:
            self.skipTest("pygame is optional locally; installed by Godot CI")
        tree = ast.parse(prepare.SOURCE.read_text())
        functions = {"_clamp_color", "_mix", "_cache_put", "_scratch",
                     "glow_surface", "spark_surface"}
        nodes = [n for n in tree.body if
                 (isinstance(n, ast.FunctionDef) and n.name in functions)
                 or (isinstance(n, ast.ClassDef) and n.name == "Particle")]
        env = {"pygame": pygame, "math": math, "P": prepare.bolt.palette(tree),
               "_SURF_CACHE": {}, "_SURF_CACHE_MAX": 384, "_SCRATCH": {}}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(prepare.SOURCE), "exec"), env)
        for shape in ("pixel", "streak", "shard", "spark", "glow", "unknown"):
            for fraction in (0.0, 0.4, 0.8):
                particle = env["Particle"]().spawn(64, 64, 10, -20, 1, 7,
                                                   (180, 240, 90), shape=shape)
                particle.life = 1.0 - fraction
                surface = pygame.Surface((128, 128), pygame.SRCALPHA)
                particle.draw(surface)
                # RGB_ADD does not copy alpha, so inspect RGB rather than alpha bounds.
                self.assertTrue(any(pygame.image.tobytes(surface, "RGB")), shape)

    def test_helper_radius_is_executed_source(self):
        baseline = prepare.build()
        text = prepare.SOURCE.read_text().replace("spark_surface(sz + 1, col)",
                                                  "spark_surface(sz + 3, col)")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "changed.py"
            path.write_text(text)
            with patch.object(prepare, "SOURCE", path):
                changed = prepare.build()
        before = next(c for c in baseline["particles"] if c["options"]["shape"] == "spark")
        after = next(c for c in changed["particles"] if c["options"]["shape"] == "spark")
        self.assertNotEqual(before["expected"][0]["commands"], after["expected"][0]["commands"])

    def test_hurt_hp_threshold_flash_and_recipe(self):
        cases = prepare.build()["hurt"]
        self.assertEqual(len(cases), 2)
        first = cases[0]["expected"]
        self.assertEqual(first[0]["bursts"], [])
        self.assertAlmostEqual(first[1]["hit_flash"], 0.144)
        self.assertEqual(first[1]["bursts"][0]["position"], [30.75, 42.25])
        self.assertEqual(first[1]["bursts"][0]["count"], 3)
        self.assertEqual(first[1]["bursts"][0]["options"]["shape"], "streak")
        self.assertEqual(first[-1]["commands"], [])
        second = cases[1]["expected"]
        self.assertEqual([len(row["bursts"]) for row in second], [0, 0, 0, 1, 1, 1])
        self.assertEqual(second[3]["hit_flash"], 0.16)
        self.assertEqual(second[3]["commands"][0][2], [-64, -60])
        self.assertEqual(second[-1]["hit_flash"], 0)

    def test_hurt_flash_is_actual_source(self):
        baseline = prepare.build()["hurt"]
        text = prepare.SOURCE.read_text().replace("self.hit_flash = 0.16", "self.hit_flash = 0.24")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "changed.py"
            path.write_text(text)
            with patch.object(prepare, "SOURCE", path):
                changed = prepare.build()["hurt"]
        self.assertNotEqual(baseline[0]["expected"][1], changed[0]["expected"][1])

    def test_integrator_is_actual_source_not_reimplementation(self):
        baseline = prepare.build()
        text = prepare.SOURCE.read_text().replace("self.pos.x += self.vel.x * dt", "self.pos.x += self.vel.x * dt * 2")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "changed.py"
            path.write_text(text)
            with patch.object(prepare, "SOURCE", path):
                changed = prepare.build()
        self.assertNotEqual(baseline["particles"][0]["expected"][2]["state"]["pos"],
                            changed["particles"][0]["expected"][2]["state"]["pos"])

    def test_check_never_rewrites_stale_fixture(self):
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
