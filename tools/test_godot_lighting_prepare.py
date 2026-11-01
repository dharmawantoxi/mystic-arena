#!/usr/bin/env python3
"""Regression tests for the lighting.py -> Godot preparation gate."""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
sys.path.insert(0, str(ROOT / "tools"))
import prepare_godot_lighting as prep  # noqa: E402


class LightingPrepareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with prep.source_module() as module:
            cls.module = module
            cls.contract = prep.build_contract(module)
            cls.oracle = prep.build_oracle(module)

    def test_contract_matches_source_constants(self):
        contract = self.contract
        self.assertEqual(contract["schema"], 1)
        self.assertEqual(contract["source"], "lighting.py")
        self.assertEqual(contract["light_dir"], list(self.module.LIGHT_DIR))
        self.assertEqual(contract["rim_add"], list(self.module.RIM_ADD))
        self.assertEqual(contract["shade_mul"], self.module.SHADE_MUL)
        self.assertEqual(contract["mask_alpha"], self.module.MASK_ALPHA)
        self.assertEqual(contract["band2_ratio"], self.module.BAND2_RATIO)
        self.assertEqual(contract["grad_steps"], self.module._GRAD_STEPS)
        self.assertEqual(contract["size_cache_limit"], 65)
        self.assertEqual(len(contract["canonical_mul_rgb"]), 28 * 28 * 3)
        self.assertEqual(len(contract["canonical_add_rgb"]), 28 * 28 * 3)

    def test_oracle_covers_masks_gradients_and_pixels(self):
        self.assertEqual(len(self.oracle["contour_cases"]), 8)
        self.assertEqual(len(self.oracle["gradient_cases"]), 40)
        self.assertEqual(len(self.oracle["apply_cases"]), 19)
        self.assertEqual(self.oracle["source_sha256"], self.contract["source_sha256"])
        names = {row["name"] for row in self.oracle["apply_cases"]}
        self.assertIn("03_threshold", names)
        self.assertIn("07_transparent_rgb", names)
        self.assertIn("17_islands", names)
        self.assertIn("18_square", names)

    def test_backend_is_pinned_and_restored(self):
        import pygame
        before = pygame.transform.get_smoothscale_backend()
        with prep.source_module():
            self.assertEqual(pygame.transform.get_smoothscale_backend(), "GENERIC")
        self.assertEqual(pygame.transform.get_smoothscale_backend(), before)

    def test_check_is_current_and_deterministic(self):
        tracked = json.loads((PROJECT / "data/lighting.json").read_text(encoding="utf-8"))
        self.assertEqual(tracked, self.contract)
        for seed in ("1", "99"):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools/prepare_godot_lighting.py"), "--check"],
                cwd=ROOT, capture_output=True, text=True, check=False, env=env)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_missing_and_stale_files_fail_check(self):
        with tempfile.TemporaryDirectory() as directory:
            contract = Path(directory) / "contract.json"
            fixture = Path(directory) / "fixture.json"
            with mock.patch.object(prep, "CONTRACT", contract), mock.patch.object(prep, "FIXTURE", fixture):
                with mock.patch.object(sys, "argv", ["prepare", "--check"]), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as missing:
                        prep.main()
                self.assertEqual(missing.exception.code, 1)
                self.assertFalse(contract.exists())
                contract.write_text("stale\n", encoding="utf-8")
                fixture.write_text(prep._text(self.oracle), encoding="utf-8")
                with mock.patch.object(sys, "argv", ["prepare", "--check"]), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as stale:
                        prep.main()
                self.assertEqual(stale.exception.code, 1)
                self.assertEqual(contract.read_text(encoding="utf-8"), "stale\n")

    def test_native_runtime_and_ci_wiring(self):
        lighting = (PROJECT / "scripts/render/Lighting.gd").read_text(encoding="utf-8")
        self.assertIn("class_name Lighting", lighting)
        self.assertIn("func contour_masks(", lighting)
        self.assertIn("func apply_to_rig(", lighting)
        resampler = (PROJECT / "scripts/render/LightingResampler.gd").read_text(encoding="utf-8")
        self.assertIn("static func resize(", resampler)
        visuals = (PROJECT / "scripts/entities/EntityVisuals.gd").read_text(encoding="utf-8")
        self.assertIn('entry.get("lighting_baked", true)', visuals)
        self.assertIn("lit_frame_texture", visuals)
        runner = (PROJECT / "tests/run_all.gd").read_text(encoding="utf-8")
        self.assertIn("LightingParity.run(self)", runner)
        for workflow in ("godot-check.yml", "godot-rebuild.yml"):
            text = (ROOT / ".github/workflows" / workflow).read_text(encoding="utf-8")
            self.assertIn("pygame==2.6.1", text)
            self.assertIn("tools/prepare_godot_lighting.py --check", text)
            self.assertIn("tools/test_godot_lighting_prepare.py", text)


if __name__ == "__main__":
    unittest.main()
