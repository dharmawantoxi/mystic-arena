#!/usr/bin/env python3
"""Regression tests for the native _system.py preparation contract."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
spec = importlib.util.spec_from_file_location("prepare_system", ROOT / "tools/prepare_godot_system.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class SystemPrepareTests(unittest.TestCase):
    def test_check_passes(self) -> None:
        contract = prepare.system_contract()
        tracked = json.loads((PROJECT / "data/system_data.json").read_text(encoding="utf-8"))
        self.assertEqual(contract, tracked)

    def test_performance_constants(self) -> None:
        perf = prepare.system_contract()["performance"]
        self.assertEqual(perf["frustum_margin"], 80)
        self.assertEqual(perf["spatial_cell_size"], 60)
        self.assertEqual(perf["fps_history_size"], 120)
        self.assertEqual(perf["fps_display_window"], 30)
        self.assertEqual(perf["fps_refresh_frames"], 10)
        self.assertEqual(perf["adaptive_history_size"], 30)
        self.assertEqual(perf["adaptive_high_threshold"], 50)
        self.assertEqual(perf["adaptive_medium_threshold"], 35)
        gd = {
            "SpatialGrid.gd": r"const DEFAULT_CELL_SIZE := 60\b",
            "FrustumCuller.gd": r"const MARGIN := 80\b",
            "FpsCounter.gd": r"const HISTORY_SIZE := 120\b",
            "AdaptiveQuality.gd": r"const HIGH_THRESHOLD := 50\.0\b",
        }
        for name, pattern in gd.items():
            text = (PROJECT / "scripts/system" / name).read_text(encoding="utf-8")
            self.assertRegex(text, pattern)
        fps = (PROJECT / "scripts/system/FpsCounter.gd").read_text(encoding="utf-8")
        self.assertRegex(fps, r"const DISPLAY_WINDOW := 30\b")
        self.assertRegex(fps, r"const REFRESH_FRAMES := 10\b")
        adaptive = (PROJECT / "scripts/system/AdaptiveQuality.gd").read_text(encoding="utf-8")
        self.assertRegex(adaptive, r"const MEDIUM_THRESHOLD := 35\.0\b")

    def test_audio_contract(self) -> None:
        audio = prepare.system_contract()["audio"]
        self.assertEqual(audio["channels"], 32)
        self.assertEqual(audio["volumes"], {"master": 0.7, "sfx": 0.6, "voice": 0.5, "bgm": 0.35, "ambient": 0.25})
        self.assertEqual(audio["throttle_ms"]["bullet_hit"], 40)
        self.assertEqual(audio["default_throttle_ms"], 50)
        self.assertEqual(len(audio["manifest"]), 17)
        director = (PROJECT / "scripts/audio/AudioDirector.gd").read_text(encoding="utf-8")
        for entry in audio["manifest"]:
            self.assertIn(f'"{entry["name"]}": "{entry["category"]}"', director)
        for name, value in audio["throttle_ms"].items():
            self.assertRegex(director, rf'"{name}": {value}\b')
        settings = (PROJECT / "scripts/core/GameSettings.gd").read_text(encoding="utf-8")
        for key, value in audio["volumes"].items():
            self.assertIn(f'"{key}_volume": {value}', settings)
        self.assertIn("func play_positional(", director)
        self.assertIn("maxf(0.15,", director)

    def test_save_contract(self) -> None:
        save = prepare.system_contract()["save"]
        self.assertEqual(save["num_slots"], 3)
        self.assertEqual(save["level_stats_defaults"]["best_score"], 0)
        self.assertEqual(save["level_stats_defaults"]["wins"], 0)
        repo = (PROJECT / "scripts/core/SaveRepository.gd").read_text(encoding="utf-8")
        self.assertRegex(repo, r"const NUM_SLOTS := 3\b")
        for key in save["empty_save_keys"]:
            self.assertIn(f'"{key}"', repo)
        for key in save["level_stats_defaults"]:
            self.assertIn(f'"{key}"', repo)
        for name in ("format_playtime", "format_time", "format_last_played", "all_slot_info", "migrate_legacy_save"):
            self.assertIn(f"func {name}(", repo)

    def test_spatial_order_oracle(self) -> None:
        # Pure-python reference of _system.SpatialGrid bucket order (cx, cy, insert).
        cell = prepare.system_contract()["performance"]["spatial_cell_size"]
        units = [(0, 0), (60, 0), (0, 60), (60, 60), (30, 30), (-1, -1)]
        buckets: dict[tuple[int, int], list[int]] = {}
        for index, (x, y) in enumerate(units):
            key = (x // cell, y // cell)
            buckets.setdefault(key, []).append(index)
        order = []
        for cx in range(-1, 2):
            for cy in range(-1, 2):
                order.extend(buckets.get((cx, cy), []))
        self.assertEqual(order, [5, 0, 4, 2, 1, 3])


if __name__ == "__main__":
    unittest.main(verbosity=2)
