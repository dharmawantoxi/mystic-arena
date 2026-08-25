#!/usr/bin/env python3
"""Regression test: Easy mode schedule and progressive AI hero pool."""

import os
import random
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

# Must be set before importing storage_paths/_core.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_TEST_SAVE_DIR = tempfile.TemporaryDirectory(prefix="mystic-easy-ai-")
os.environ["MYSTIC_SAVE_DIR"] = _TEST_SAVE_DIR.name

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# storage_paths has a one-time migration from ./saves. Import from the temp
# working directory so a developer's real desktop save is never copied/read.
_ORIGINAL_CWD = os.getcwd()
os.chdir(_TEST_SAVE_DIR.name)
try:
    from _core import (  # noqa: E402
        AIPlayer,
        AI_HERO_PREFERENCES,
        Game,
        GameSettings,
        get_all_hero_types,
    )
    from levels import get_level_config  # noqa: E402
finally:
    os.chdir(_ORIGINAL_CWD)


def test_easy_schedule():
    cfg = get_level_config(7)
    bounds_by_mode = {
        "easy": (20, 40),
        "normal": (11, 30),
        "hard": (11, 30),
    }
    for mode, (low, high) in bounds_by_mode.items():
        fake_game = SimpleNamespace(level_config=cfg, difficulty=mode)
        for _ in range(100):
            schedule = Game._roll_mini_boss_schedule(fake_game)
            waves = list(schedule)
            assert len(waves) == len(set(waves)) == 3
            assert low <= min(waves) <= max(waves) <= high
            assert list(schedule.values()) == list(
                cfg["mini_bosses"].values())


def test_difficulty_cycle():
    GameSettings._instance = None
    settings = GameSettings()
    settings.set_difficulty("normal")
    assert settings.cycle_difficulty(1) == "hard"
    assert settings.cycle_difficulty(1) == "easy"
    assert settings.is_easy_mode()
    assert not settings.is_scaling_on()
    assert settings.cycle_difficulty(-1) == "hard"


def test_progressive_ai_pool_and_draft():
    catalog = get_all_hero_types()

    for level_no in range(1, 8):
        ai = AIPlayer(level_number=level_no)
        pool = ai._get_hero_pool()
        actual_bosses = {
            hero_type for hero_type in pool
            if catalog.get(hero_type, {}).get("is_boss_hero")
        }
        expected_bosses = set()
        for previous_level in range(1, level_no):
            cfg = get_level_config(previous_level)
            expected_bosses.update(cfg["mini_bosses"].values())
            expected_bosses.add(cfg["true_boss"])

        assert set(AI_HERO_PREFERENCES).issubset(pool)
        assert actual_bosses == expected_bosses
        assert len(pool) == len(set(pool))

    # Level 7: one random starter first, then a boss hero from Level 6.
    random.seed(7)
    ai = AIPlayer(level_number=7)
    pool = ai._get_hero_pool()
    starter = ai._choose_hero_purchase_target(pool, catalog)
    assert not catalog[starter].get("is_boss_hero")

    fake_hero = SimpleNamespace(hero_type=starter)
    ai.heroes = [fake_hero]
    boss_target = ai._choose_hero_purchase_target(
        [hero_type for hero_type in pool if hero_type != starter],
        catalog,
    )
    assert catalog[boss_target].get("is_boss_hero")
    assert ai._hero_source_levels[boss_target] == 6


if __name__ == "__main__":
    try:
        test_easy_schedule()
        test_difficulty_cycle()
        test_progressive_ai_pool_and_draft()
        print("PASS: Easy mode + progressive AI hero pool")
    finally:
        _TEST_SAVE_DIR.cleanup()
