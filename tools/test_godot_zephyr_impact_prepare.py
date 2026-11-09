#!/usr/bin/env python3
import contextlib
import ast
import math
import os
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import prepare_godot_zephyr_impact as prepare


class ZephyrImpactPrepareTest(unittest.TestCase):
    def test_current_and_deterministic(self):
        fixture = prepare.build()
        self.assertEqual(fixture, prepare.build())
        self.assertEqual(fixture, json.loads(prepare.OUTPUT.read_text()))

    def test_coverage_and_radial_commands_do_not_raise(self):
        fixture = prepare.build()
        self.assertEqual(len(fixture["cases"]), 36)
        self.assertEqual(len(fixture["spark_helpers"]), 6)
        self.assertEqual(len(fixture["ellipse_rotations"]), 7)
        self.assertEqual(fixture["director_limit"], 8)
        for case in fixture["cases"]:
            first = case["frames"][0]["commands"]
            self.assertEqual(sum(c[0] == "line" for c in first), 8)
            self.assertEqual(sum(c[0] == "arc" for c in first), 3)
            self.assertEqual(first[-1][0], "spark")

    def test_power_clamp_lifecycle_and_late_frames(self):
        for case in prepare.build()["cases"]:
            self.assertGreaterEqual(case["initial"]["power"], 0.35)
            self.assertLessEqual(case["initial"]["duration"], 0.540000000001)
            self.assertEqual(case["frames"][-1]["commands"], [])
            self.assertFalse(case["lifecycle"][-1]["state"]["active"])
            self.assertEqual(case["frames"][-2]["commands"], [])

    def test_original_unbound_loop_variable_regression(self):
        text = prepare.SOURCE.read_text()
        start, end = text.index("class ImpactFX:"), text.index("class ZephyrProjectile:")
        body = text[start:end]
        self.assertEqual(body.count("for k in range(4):"), 2)
        broken = text[:start] + body.replace("for k in range(4):", "for i in range(4):") + text[end:]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.py"
            path.write_text(broken)
            with patch.object(prepare, "SOURCE", path), self.assertRaises(UnboundLocalError):
                prepare.build()

    def test_actual_source_controls_slash_geometry(self):
        baseline = prepare.build()
        text = prepare.SOURCE.read_text().replace("span = 0.55 + 0.5 * pw", "span = 0.55 + 0.6 * pw")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "changed.py"
            path.write_text(text)
            with patch.object(prepare, "SOURCE", path):
                changed = prepare.build()
        first = [c for c in baseline["cases"][0]["frames"][0]["commands"] if c[0] == "arc"]
        second = [c for c in changed["cases"][0]["frames"][0]["commands"] if c[0] == "arc"]
        self.assertNotEqual(first, second)

    def test_negative_ellipse_quantization_uses_python_floor(self):
        cases = prepare.build()["ellipse_rotations"]
        lookup = {c["degrees"]: c["expected"] for c in cases}
        self.assertEqual(lookup[-139.9], -140)
        self.assertEqual(lookup[-9.9], -10)
        self.assertEqual(lookup[-0.1], 0)

    def test_real_pygame_impact_draw_smoke(self):
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        try:
            import pygame
        except ImportError:
            self.skipTest("pygame is optional locally; installed by Godot CI")
        tree = ast.parse(prepare.SOURCE.read_text())
        functions = {"_clamp_color", "_mix", "_cache_put", "_scratch",
                     "glow_surface", "spark_surface", "ellipse_ring_surface"}
        nodes = [n for n in tree.body if
                 (isinstance(n, ast.FunctionDef) and n.name in functions)
                 or (isinstance(n, ast.ClassDef) and n.name == "ImpactFX")]
        env = {"pygame": pygame, "math": math, "P": prepare.bolt.palette(tree),
               "_SURF_CACHE": {}, "_SURF_CACHE_MAX": 384, "_SCRATCH": {}}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(prepare.SOURCE), "exec"), env)
        for angle in (0.0, 0.7, -2.4):
            for critical in (False, True):
                for fraction in (0.0, 0.1, 0.4, 0.6, 0.95):
                    impact = env["ImpactFX"](320, 180, angle, 1.0, critical)
                    impact.age = fraction * impact.duration
                    canvas = pygame.Surface((640, 360), pygame.SRCALPHA)
                    impact.draw(canvas)
                    if fraction < 0.95:
                        self.assertGreater(canvas.get_bounding_rect().width, 0)

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
