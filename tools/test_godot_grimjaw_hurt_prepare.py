#!/usr/bin/env python3
import ast
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import prepare_godot_grimjaw_hurt as prepare


class GrimjawHurtPrepareTest(unittest.TestCase):
    def test_current_and_deterministic(self):
        fixture, config = prepare.build()
        self.assertEqual((fixture, config), prepare.build())
        self.assertEqual(fixture, json.loads(prepare.OUTPUT.read_text()))
        self.assertEqual(config, json.loads(prepare.CONFIG.read_text()))

    def test_hp_threshold_healing_retrigger_and_expiry(self):
        fixture, _ = prepare.build()
        rows = fixture["cases"][1]["expected"]
        self.assertEqual([len(r["bursts"]) for r in rows], [0, 0, 0, 1, 1, 1])
        self.assertEqual(rows[3]["hit_flash"], .16)
        self.assertEqual(rows[-1]["commands"], [])
        self.assertEqual(rows[-1]["hit_flash"], 0)

    def test_grimjaw_palette_recipe_and_posterized_flash(self):
        fixture, config = prepare.build()
        self.assertEqual(config["capacity"], 108)
        burst = fixture["cases"][0]["expected"][1]["bursts"][0]
        self.assertEqual(burst["position"], [30.75, 40.25])
        self.assertEqual(burst["options"]["colors"], [config["palette"]["fx_light"], config["palette"]["ember"]])
        commands = fixture["cases"][0]["expected"][1]["commands"]
        self.assertEqual(len(commands), 4)
        self.assertTrue(all(c[0] == "circle" for c in commands))
        self.assertGreater(commands[0][3], commands[-1][3])

    def test_budget_uses_python_round_not_zephyr_floor(self):
        fixture, _ = prepare.build()
        self.assertEqual([r["count"] for r in fixture["budgets"]], [0, 0, 1, 2, 2, 3])

    def test_source_streak_motion_and_expiry(self):
        fixture, _ = prepare.build()
        self.assertEqual(len(fixture["trajectories"]), 2)
        for case in fixture["trajectories"]:
            self.assertEqual(case["options"]["shape"], "streak")
            self.assertEqual(case["expected"][0]["commands"][0][0], "line")
            self.assertFalse(case["expected"][-1]["state"]["active"])
            self.assertEqual(case["expected"][-1]["commands"], [])

    def test_glow_bands_are_actual_source(self):
        baseline, _ = prepare.build()
        text = prepare.SOURCE.read_text().replace("(0.22, 0.45, 0.70, 1.0)", "(0.12, 0.35, 0.60, 1.0)")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "changed.py"
            source.write_text(text)
            with patch.object(prepare, "SOURCE", source):
                changed, _ = prepare.build()
        self.assertNotEqual(baseline["cases"][0]["expected"][1]["commands"], changed["cases"][0]["expected"][1]["commands"])

    def test_real_pygame_flash_smoke(self):
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        try:
            import pygame
        except ImportError:
            self.skipTest("pygame optional locally; installed in CI")
        env = prepare.environment()
        env["pygame"] = pygame
        owner = types.SimpleNamespace(hero=types.SimpleNamespace(x=320, y=180), hit_flash=.16)
        for flash in (.16, .144, .08, .016):
            owner.hit_flash = flash
            surface = pygame.Surface((640, 360), pygame.SRCALPHA)
            env["_draw_hit_flash"](owner, surface)
            self.assertTrue(any(pygame.image.tobytes(surface, "RGB")))

    def test_death_edge_respawn_and_feedback(self):
        fixture, config = prepare.build()
        self.assertEqual([len(row["bursts"]) for row in fixture["death"]], [0, 2, 0, 0, 2])
        self.assertEqual(config["death_feedback"], [[3.0, .3]])
        self.assertEqual([r["count"] for r in config["death_recipes"]], [8, 5])
        self.assertEqual([r["offset"] for r in config["death_recipes"]], [[0, -12], [0, 0]])
        self.assertTrue(config["death_recipes"][1]["options"]["back"])

    def test_ember_smoke_and_back_particle_coverage(self):
        fixture, _ = prepare.build()
        self.assertEqual(len(fixture["particles"]), 16)
        for case in fixture["particles"]:
            state = case["expected"][0]["state"]
            self.assertEqual(state["back"], state["shape"] == "smoke")
            self.assertEqual(case["expected"][-1]["commands"], [])
            if state["shape"] == "ember":
                self.assertEqual([r[0] for r in case["expected"][0]["commands"]], ["polygon", "polygon"])
            if state["shape"] == "smoke":
                self.assertEqual([r[0] for r in case["expected"][0]["commands"]], ["circle", "circle"])

    def test_pool_cap_budget_and_recycling(self):
        fixture, _ = prepare.build()
        self.assertEqual(len(fixture["pools"]), 5)
        for case in fixture["pools"]:
            for row in case["expected"]:
                self.assertLessEqual(len(row["live"]), 5)
                self.assertLessEqual(row["pooled"], 5)
            self.assertEqual(case["expected"][-1]["live"], [])

    def test_ember_geometry_is_executed_source(self):
        baseline, _ = prepare.build()
        text = prepare.SOURCE.read_text().replace("sz * 0.6", "sz * 0.9")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "changed.py"
            path.write_text(text)
            with patch.object(prepare, "SOURCE", path):
                changed, _ = prepare.build()
        self.assertNotEqual(baseline["particles"][0]["expected"], changed["particles"][0]["expected"])

    def test_real_pygame_death_layers_smoke(self):
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        try:
            import pygame
        except ImportError:
            self.skipTest("pygame optional locally; installed in CI")
        env = prepare.environment()
        env["pygame"] = pygame
        env["_SCRATCH"] = {}
        tree = ast.parse(prepare.SOURCE.read_text())
        scratch = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_scratch")
        exec(compile(ast.Module(body=[scratch], type_ignores=[]), str(prepare.SOURCE), "exec"), env)
        pool = env["ParticleSystem"]()
        owner = types.SimpleNamespace(hero=types.SimpleNamespace(x=320, y=180), particles=pool)
        env["on_death"](owner)
        self.assertEqual(pool.count(), 13)
        for _ in range(12):
            pool.update(.016)
            for layer in ("back", "front"):
                surface = pygame.Surface((640, 360), pygame.SRCALPHA)
                pool.draw(surface, layer=layer)
                self.assertTrue(any(pygame.image.tobytes(surface, "RGB")), layer)

    def test_spark_has_five_needles_and_effective_alpha(self):
        fixture, _ = prepare.build()
        sample = next(c for c in fixture["particles"] if c["options"]["shape"] == "spark")
        commands = sample["expected"][0]["commands"]
        self.assertEqual([c[0] for c in commands], ["line"] * 5 + ["circle"])
        self.assertEqual([c[4] for c in commands[:5]], [2, 1, 2, 1, 2])
        faded = sample["expected"][1]
        alpha = int(faded["state"]["alpha"] * (faded["state"]["life"] / faded["state"]["max_life"]) ** faded["state"]["fade_pow"])
        self.assertAlmostEqual(faded["commands"][0][1][3], 235 * alpha / 255)
        self.assertEqual(faded["commands"][-1][1][3], alpha)

    def test_low_quality_glow_shrinks_but_remains_visible(self):
        fixture, _ = prepare.build()
        samples = [c for c in fixture["particles"] if c["options"]["shape"] == "glow" and c["args"][5] == 6]
        full = next(c for c in samples if c["glow_allowed"])["expected"][0]["commands"]
        low = next(c for c in samples if not c["glow_allowed"])["expected"][0]["commands"]
        self.assertEqual(len(full), 4)
        self.assertEqual(len(low), 4)
        self.assertGreater(full[0][3], low[0][3])

    def test_stream_preserves_sampling_when_full_and_spawn_gate(self):
        fixture, _ = prepare.build()
        cases = {c["budget"]: c for c in fixture["pools"]}
        full = cases[1]["expected"]
        self.assertEqual(full[2]["result"], 0)
        self.assertEqual(full[2]["random_index"] - full[1]["random_index"], 6 * 7)
        half = cases[.5]["expected"]
        self.assertEqual(half[2]["random_index"] - half[1]["random_index"], 3 * 8)
        zero = cases[0]["expected"]
        self.assertTrue(all(row["random_index"] == 0 for row in zero))

    def test_stream_geometry_is_actual_source(self):
        baseline, _ = prepare.build()
        text = prepare.SOURCE.read_text().replace("random.uniform(-4, 4)", "random.uniform(-8, 8)")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "changed.py"
            path.write_text(text)
            with patch.object(prepare, "SOURCE", path):
                changed, _ = prepare.build()
        self.assertNotEqual(baseline["pools"], changed["pools"])
        self.assertEqual(baseline["particles"], changed["particles"])

    def test_real_pygame_glow_spark_smoke(self):
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        try:
            import pygame
        except ImportError:
            self.skipTest("pygame optional locally; installed in CI")
        env = prepare.environment()
        env["pygame"] = pygame
        for shape in ("glow", "spark"):
            for allowed in (False, True):
                env["glow_allowed"] = lambda: allowed
                particle = env["Particle"]().spawn(320, 180, 0, 0, 1, 6, env["P"]["ember"], shape=shape)
                for _ in range(4):
                    particle.update(.05)
                    canvas = pygame.Surface((640, 360), pygame.SRCALPHA)
                    particle.draw(canvas)
                    self.assertTrue(any(pygame.image.tobytes(canvas, "RGB")))

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
