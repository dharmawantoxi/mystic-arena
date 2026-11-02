#!/usr/bin/env python3
"""Export tactical_commands.py to the active Godot project.

The state oracle reuses the closed-world pygame harness already present in
tools/test_godot_match_parity.py (real TacticalCommandManager + real pygame
units, no full Game.update). Draw geometry is recorded from the real draw_world
/ draw_ui methods with spies. --check is byte-exact and fail-closed.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import importlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
SOURCE = ROOT / "tactical_commands.py"
CONTRACT = PROJECT / "data/tactical.json"
FIXTURE = PROJECT / "tests/fixtures/tactical_parity.json"
PYGAME_VERSION = "2.6.1"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))


def _jsonable(value):
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise AssertionError(f"Non-finite tactical value: {value!r}")
    return value


def _text(value) -> str:
    return json.dumps(_jsonable(value), ensure_ascii=False, indent=2,
                      allow_nan=False, sort_keys=True) + "\n"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


ANCHORS = [
    "HOLD_TAP_MAX_FRAMES = 20", "HOLD_RELEASE_TAIL = 30",
    "GATHER_PUSH_DELAY_FRAMES = 240", "self.cooldown_max = 30",
    "self.feedback_timer = 180", "self.command_timer = 600",
    "self.gather_point_timer = 150", "self._auto_check_timer >= 90",
    "mid_mix = 0.35", "gather_x = max(200, min(1080, gather_x))",
    "gather_y = max(100, min(620, gather_y))", "gather_x, gather_y = 640, 360",
    "spread = 35 + (i % 3) * 15", "math.hypot(h.x - gx, h.y - gy) < 100",
    "arrived < len(heroes) * 0.6", "self.command_timer == 300",
    "threat = self._count_enemies_near(target_tower.x, target_tower.y, 250)",
    "num_to_send = 3 if threat >= 3 else 2", "spread = 30 + i * 10",
    "radius = 80 + (i % 2) * 30", "tx = max(50, min(1230, tx))",
    "ty = max(50, min(670, ty))", "spread = hero.range * 0.5 + i * 8",
    "enemies_near = self._count_enemies_near(tower.x, tower.y, 220)",
    "threat_score = enemies_near * 10 + (1 - hp_ratio) * 15",
    "if tower.x < 400:", "threat_score += 2", "count += 2  # boss dihitung 2",
    "best_dist = 9999", "enemies_near_castle = self._count_enemies_near(castle.x, castle.y, 300)",
    "hp_ratio < 0.4 and enemies_near_castle >= 2",
    "hp_ratio < 0.6 and enemies_near >= 2", "elif enemies_near >= 4:",
    "boss_hp_ratio < 0.8", "getattr(game, 'wave_number', 0) >= 11",
    "random.random() < 0.2", "for r in range(50, 20, -8):",
    "a = int((50 - r) * 4 * pulse)", "pygame.time.get_ticks() * 0.008",
    "* 0.3 + 0.7", "if dist > 80:", "t1 = seg * 0.33", "t2 = t1 + 0.18",
    "int(120 * pulse)", "font = get_font(28, \"body_bold\")",
    "if self.feedback_timer < 30:", "if self.feedback_timer > 150:",
    "prog = (180 - self.feedback_timer) / 30.0", "y_offset = int((1 - prog) * 20)",
    "center=(640, 90 + y_offset)", "bg_rect = text_rect.inflate(20, 8)",
    "int(160 * alpha / 255)", "border_radius=6", "shadow.set_alpha(alpha // 2)",
    "[:15]", "self.command_timer//60",
]


def build_contract(oracle: dict) -> dict:
    source = SOURCE.read_text(encoding="utf-8")
    for anchor in ANCHORS:
        if anchor not in source:
            raise AssertionError(f"Tactical source anchor missing: {anchor}")
    ast.parse(source)
    constants = dict(oracle["constants"])
    cfg = {
        **constants,
        "command_colors": oracle["command_colors"],
        "gather_mid_mix": 0.35,
        "gather_clamp_x": [200, 1080], "gather_clamp_y": [100, 620],
        "gather_single": [640, 360], "gather_spread_base": 35,
        "gather_spread_step": 15, "gather_spread_mod": 3,
        "gather_arrive_radius": 100.0, "gather_arrive_ratio": 0.6,
        "gather_push_timer": 300,
        "protect_tower_threat_radius": 250.0, "protect_tower_send_threshold": 3,
        "protect_tower_send_count": 3, "protect_tower_base_count": 2,
        "protect_tower_small_roster": 3, "protect_tower_spread_base": 30,
        "protect_tower_spread_step": 10,
        "castle_radius_base": 80, "castle_radius_step": 30, "castle_radius_mod": 2,
        "castle_clamp_x": [50, 1230], "castle_clamp_y": [50, 670],
        "attack_spread_range_mult": 0.5, "attack_spread_step": 8,
        "threat_radius": 220.0, "threat_enemy_weight": 10, "threat_hp_weight": 15,
        "threat_outer_x": 400.0, "threat_outer_bonus": 2,
        "boss_count_weight": 2, "nearest_init": 9999.0,
        "auto_castle_hp": 0.4, "auto_castle_enemies": 2, "auto_castle_radius": 300.0,
        "auto_tower_hp": 0.6, "auto_tower_enemies": 2, "auto_tower_radius": 250.0,
        "auto_tower_swarm": 4, "auto_boss_hp": 0.8, "auto_boss_wave": 11,
        "auto_boss_chance": 0.2,
        "feedback_default_color": [255, 220, 100],
        "feedback_gather": [100, 220, 255], "feedback_protect_tower": [100, 255, 100],
        "feedback_protect_castle": [255, 220, 50], "feedback_attack_boss": [255, 100, 100],
        "feedback_attack_dealer": [255, 130, 255], "feedback_no_heroes": [255, 100, 100],
        "feedback_missing": [255, 150, 100],
        "draw_ring_start": 50, "draw_ring_stop": 20, "draw_ring_step": -8,
        "draw_ring_alpha_mult": 4, "draw_pulse_rate": 0.008, "draw_pulse_amp": 0.3,
        "draw_pulse_base": 0.7, "draw_center_radius": 6, "draw_center_dot": 2,
        "draw_line_min_dist": 80.0, "draw_line_segments": 3, "draw_line_t_step": 0.33,
        "draw_line_t_len": 0.18, "draw_line_alpha": 120, "draw_line_width": 2,
        "draw_ui_font_size": 28, "draw_ui_fade_out": 30, "draw_ui_fade_in_start": 150,
        "draw_ui_fade_in_frames": 30.0, "draw_ui_y_offset": 20,
        "draw_ui_center": [640, 90], "draw_ui_inflate": [20, 8],
        "draw_ui_bg_alpha": 160, "draw_ui_border_width": 2, "draw_ui_border_radius": 6,
        "draw_ui_shadow_offset": 2, "status_target_chars": 15, "status_fps": 60,
        "sound_ui_click": "ui_click", "sound_ui_click_volume": 0.8,
        "sound_hero_skill": "hero_skill", "sound_hero_skill_volume": 0.9,
    }
    return _jsonable({
        "schema": 1, "source": "tactical_commands.py",
        "source_sha256": _sha(SOURCE.read_bytes()),
        "config": cfg, "anchors": ANCHORS,
        "rng": "godot-RandomNumberGenerator; parity injects random_script",
    })


@contextlib.contextmanager
def source_module():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame
    if pygame.version.ver != PYGAME_VERSION:
        raise AssertionError(f"Tactical draw oracle requires pygame=={PYGAME_VERSION}")
    spec = importlib.util.spec_from_file_location("mystic_tactical_export", SOURCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    try:
        yield module
    finally:
        sys.modules.pop(spec.name, None)


def _draw_oracle(module) -> dict:
    import pygame
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    world = []
    old_circle, old_line = pygame.draw.circle, pygame.draw.line
    old_ticks = pygame.time.get_ticks
    for timer, ticks in ((150, 0), (75, 12345), (10, 999)):
        heroes = [SimpleNamespace(alive=True, x=300.0, y=300.0),
                  SimpleNamespace(alive=True, x=700.0, y=400.0)]
        game = SimpleNamespace(heroes=heroes, state="playing")
        manager = module.TacticalCommandManager(game)
        manager.active_command = module.TacticalCommand.GATHER
        manager.gather_point = (500.0, 400.0)
        manager.gather_point_timer = timer
        circles, lines = [], []

        def circle(surface, color, center, radius, width=0):
            circles.append({"color": list(color), "center": list(center),
                            "radius": int(radius), "width": int(width)})

        def line(surface, color, start, end, width=1):
            lines.append({"color": list(color), "start": list(start),
                          "end": list(end), "width": int(width)})

        pygame.draw.circle, pygame.draw.line = circle, line
        pygame.time.get_ticks = lambda: ticks
        try:
            manager.draw_world(object())
        finally:
            pygame.draw.circle, pygame.draw.line = old_circle, old_line
            pygame.time.get_ticks = old_ticks
        world.append({"timer": timer, "ticks": ticks, "circles": circles, "lines": lines})

    ui = []
    old_rect = pygame.draw.rect
    old_render = sys.modules.get("_render")
    fake_render = SimpleNamespace(get_font=lambda size, style: FakeFont(size))
    sys.modules["_render"] = fake_render

    class FakeFont:
        def __init__(self, size):
            self.size = size

        def render(self, text, aa, color):
            surf = pygame.Surface((max(1, len(text) * self.size // 2), self.size), pygame.SRCALPHA)
            surf.fill(tuple(color) + (255,))
            return surf

    class UISurface(pygame.Surface):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.blits = []
            self.rects = []

        def blit(self, src, dest=None, *a, **k):
            pos = dest if dest is not None else (0, 0)
            if hasattr(pos, "x"):
                pos = (pos.x, pos.y)
            self.blits.append({"size": [src.get_width(), src.get_height()],
                               "pos": [int(pos[0]), int(pos[1])], "alpha": src.get_alpha()})
            return pygame.Surface.blit(self, src, dest, *a, **k)

    def rect(surface, color, box, width=0, **k):
        if hasattr(surface, "rects"):
            surface.rects.append({"color": list(color), "box": [int(box.x), int(box.y), int(box.width), int(box.height)],
                                  "width": int(width), "radius": int(k.get("border_radius", 0))})
        return old_rect(surface, color, box, width, **k)

    pygame.draw.rect = rect
    try:
        for timer in (180, 165, 150, 30, 15):
            game = SimpleNamespace(heroes=[], state="playing")
            manager = module.TacticalCommandManager(game)
            manager.feedback_text = "GATHER! 2 heroes regrouping!"
            manager.feedback_color = (100, 220, 255)
            manager.feedback_timer = timer
            surface = UISurface((1280, 720), pygame.SRCALPHA)
            manager.draw_ui(surface)
            ui.append({"timer": timer, "blits": surface.blits, "rects": surface.rects})
    finally:
        pygame.draw.rect = old_rect
        if old_render is None:
            sys.modules.pop("_render", None)
        else:
            sys.modules["_render"] = old_render
    return {"world": world, "ui": ui}


def build_oracle() -> dict:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    core = importlib.import_module("_core")
    entity = importlib.import_module("_entity")
    legacy = importlib.import_module("test_godot_match_parity")
    with contextlib.redirect_stdout(io.StringIO()):
        fixture = legacy.make_tactical_commands_fixture(core, entity)
    with source_module() as module:
        fixture["draw"] = _draw_oracle(module)
    fixture["source_sha256"] = _sha(SOURCE.read_bytes())
    return _jsonable(fixture)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        oracle = build_oracle()
        contract = build_contract(oracle)
        contract_text, oracle_text = _text(contract), _text(oracle)
        if args.check:
            if not CONTRACT.is_file() or not FIXTURE.is_file():
                raise AssertionError("Missing tactical contract/fixture; run prepare first")
            if CONTRACT.read_text(encoding="utf-8") != contract_text:
                raise AssertionError("Stale tactical contract")
            if FIXTURE.read_text(encoding="utf-8") != oracle_text:
                raise AssertionError("Stale tactical oracle fixture")
        else:
            CONTRACT.parent.mkdir(parents=True, exist_ok=True)
            FIXTURE.parent.mkdir(parents=True, exist_ok=True)
            CONTRACT.write_text(contract_text, encoding="utf-8")
            FIXTURE.write_text(oracle_text, encoding="utf-8")
    except (AssertionError, ValueError, TypeError, KeyError, OSError, ImportError) as exc:
        print(f"tactical preparation failed: {exc}", file=sys.stderr)
        return 1
    print(f"{'Verified' if args.check else 'Prepared'} tactical: "
          f"{len(oracle['scenarios'])} scenarios, {len(oracle['draw']['world'])} world draw cases; "
          f"sha256={contract['source_sha256'][:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
