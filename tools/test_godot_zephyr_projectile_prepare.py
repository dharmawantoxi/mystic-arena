#!/usr/bin/env python3
import ast
import contextlib
import io
import json
import math
import os
from pathlib import Path
import random
import tempfile
import types
import unittest
from unittest.mock import patch
import prepare_godot_zephyr_projectile as prepare


class ZephyrProjectilePrepareTest(unittest.TestCase):
    def test_current_and_deterministic(self):
        fixture, config = prepare.build()
        self.assertEqual((fixture, config), prepare.build())
        self.assertEqual(fixture, json.loads(prepare.OUTPUT.read_text()))
        self.assertEqual(config, json.loads(prepare.CONFIG.read_text()))

    def test_strict_lifetime_impact_and_trail_cap(self):
        fixture, _ = prepare.build()
        cases = {c["name"]: c for c in fixture["cases"]}
        strict = cases["expiry_strict"]["expected"]
        self.assertEqual([r["state"]["state"] for r in strict], ["travel", "impact", "impact", "dead", "dead"])
        cap = cases["trail_cap"]["expected"]
        self.assertEqual(len(cap[19]["state"]["trail"]), 16)
        self.assertEqual(cap[-1]["commands"], [])
        self.assertFalse(cap[-1]["alive"])

    def test_impact_callback_once_and_no_damage(self):
        fixture, _ = prepare.build()
        moving = next(c for c in fixture["cases"] if c["name"] == "moving_target")
        hits = [hit for row in moving["expected"] for hit in row["hits"]]
        self.assertEqual(hits, [[9, -7]])
        collision = next(c for c in fixture["cases"] if c["name"] == "collision")
        self.assertEqual(collision["expected"][0]["hits"], [[10, 0]])
        self.assertEqual(collision["expected"][0]["state"]["damage"], 0)
        self.assertEqual(collision["expected"][0]["commands"], [])

    def test_manager_capacity_expiry_clear(self):
        fixture, _ = prepare.build()
        rows = fixture["manager"]["expected"]
        self.assertEqual([r["result"] for r in rows[:3]], [True, True, False])
        self.assertEqual([len(r["states"]) for r in rows], [1, 2, 2, 2, 2, 0, 1, 0])

    def test_original_integration_is_executed(self):
        baseline, _ = prepare.build()
        text = prepare.SOURCE.read_text().replace("self.position += self.velocity * dt", "self.position += self.velocity * dt * 2")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "changed.py"
            path.write_text(text)
            with patch.object(prepare, "SOURCE", path):
                changed, _ = prepare.build()
        self.assertNotEqual(baseline["cases"][0]["expected"], changed["cases"][0]["expected"])

    def test_shim_matches_real_pygame_vector_motion(self):
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        try:
            import pygame
        except ImportError:
            self.skipTest("pygame optional locally; installed in CI")
        fixture, _ = prepare.build()
        for case in fixture["cases"]:
            env = prepare.environment()
            env["pygame"].Vector2 = pygame.Vector2
            events, hits = [], []
            pool = types.SimpleNamespace(spawn=lambda *a, **kw: events.append({"args": a, "options": kw})) if case["connected"] else None
            projectile = env["ZephyrProjectile"](*case["args"], **case["options"], particles=pool,
                on_impact=lambda p: hits.append([p.hit_pos.x, p.hit_pos.y]))
            for action, expected in zip(case["actions"], case["expected"]):
                events.clear()
                hits.clear()
                if "target" in action:
                    projectile.target = types.SimpleNamespace(**action["target"])
                if "kill" in action:
                    projectile.kill(*action["kill"]) if action["kill"] is not None else projectile.kill()
                else:
                    projectile.update(action["dt"])
                actual = prepare.snapshot(projectile)
                for key in ("position", "velocity", "hit_pos"):
                    for left, right in zip(actual[key], expected["state"][key]):
                        self.assertAlmostEqual(left, right, places=9)
                self.assertEqual(actual["state"], expected["state"]["state"])
                self.assertEqual(hits, expected["hits"])
                canvas = prepare.Surface()
                if projectile.active:
                    projectile.draw(canvas)
                self.assertEqual(canvas.commands, expected["commands"])

    def test_real_pygame_ribbon_and_body_smoke(self):
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        try:
            import pygame
        except ImportError:
            self.skipTest("pygame optional locally; installed in CI")
        tree = ast.parse(prepare.SOURCE.read_text())
        functions = {"_clamp_color", "_mix", "_cache_put", "_scratch", "glow_surface", "draw_bolt"}
        nodes = [n for n in tree.body if
                 (isinstance(n, ast.FunctionDef) and n.name in functions)
                 or (isinstance(n, ast.ClassDef) and n.name == "ZephyrProjectile")]
        env = {"pygame": pygame, "math": math, "random": random.Random(1234),
               "P": prepare.particles.bolt.palette(tree), "_SURF_CACHE": {},
               "_SURF_CACHE_MAX": 384, "_SCRATCH": {}}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(prepare.SOURCE), "exec"), env)
        projectile = env["ZephyrProjectile"](100, 180, 600, 180)
        for _ in range(12):
            projectile.update(.016)
            canvas = pygame.Surface((640, 360), pygame.SRCALPHA)
            projectile.draw(canvas)
            self.assertTrue(any(pygame.image.tobytes(canvas, "RGB")))
        projectile.kill()
        self.assertEqual(projectile.state, "impact")
        projectile.draw(pygame.Surface((640, 360), pygame.SRCALPHA))

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
