"""Bake the source boss bodies (``bosses/base_boss.py`` ``Boss.draw`` -> ``heroes.render_boss``).

``Boss.draw`` paints auras, a shadow, the body, then the HP bar and name plate above the
sprite top (``BOSS_LABEL_TOP``). The body comes from ``heroes._boss_render_sprite_fast`` (the
sprite the game caches per ``_boss_cache_key``). This bakes the standing pose, phase 0, for
both facings of every one of the 216 bosses: one PNG per boss holding the two crops side by
side. Walking, attack, skill and hurt-flash poses and the live FX layers are not baked.

The renderer grows its canvas in steps and returns ``None`` until it fits (the game draws the
direct path for those frames), so the bake simply asks again.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pygame_env as env  # noqa: E402

FACINGS = (-1, 1)
GAP = 2
MAX_TRIES = 12


def make_boss(boss_cls, boss_type, facing):
    random.seed(f"{boss_type}:{facing}:init")
    boss = boss_cls(boss_type)
    boss.x, boss.y = 400.0, 300.0
    boss.entrance_timer = 0
    boss.direction = facing
    return boss


def render(heroes_mod, boss_cls, draw_fn, boss_type, facing):
    """``(sprite, ax, ay)`` the game would cache for the standing pose, phase 0."""
    for attempt in range(MAX_TRIES):
        boss = make_boss(boss_cls, boss_type, facing)
        key = heroes_mod._boss_cache_key(boss_type, boss)
        assert key[8] == "idle" and key[9] == 0 and not key[10], key
        random.seed(f"{boss_type}:{facing}:{attempt}")
        heroes_mod._reset_hero_render_budget()
        out = heroes_mod._boss_render_sprite_fast(boss_type, boss, draw_fn, "idle")
        if out is not None:
            return out, key
    raise RuntimeError(f"{boss_type} facing {facing} never fit its canvas")


def main() -> int:
    import numpy as np

    pygame, _core, _screen = env.boot()
    import heroes as heroes_mod
    from bosses._boss_index import BOSS_INDEX
    from bosses.base_boss import BOSS_LABEL_TOP, Boss, _get_boss_draw_func

    bosses = {}
    total = 0
    for boss_type in sorted(BOSS_INDEX):
        draw_fn = _get_boss_draw_func(boss_type)
        sprites = {}
        for facing in FACINGS:
            (sprite, ax, ay), key = render(heroes_mod, Boss, draw_fn, boss_type, facing)
            assert key[4] == facing, key
            sprites[facing] = (sprite, int(ax), int(ay))
        probe = make_boss(Boss, boss_type, -1)
        width = sum(s[0].get_width() for s in sprites.values()) + GAP
        height = max(s[0].get_height() for s in sprites.values())
        sheet = np.zeros((height, width, 4), dtype=np.uint8)
        frames = {}
        x = 0
        for facing in FACINGS:
            sprite, ax, ay = sprites[facing]
            w, h = sprite.get_size()
            raw = np.frombuffer(pygame.image.tostring(sprite, "RGBA"), dtype=np.uint8)
            sheet[0:h, x : x + w] = raw.reshape(h, w, 4)
            frames[str(facing)] = [x, 0, w, h, ax, ay]
            x += w + GAP
        entry = env.write_png(env.ART_DIR / "bosses" / f"{boss_type}.png", sheet)
        entry.update(
            {
                "frames": frames,
                "radius": int(probe.radius),
                "class": probe.boss_class,
                "label_top": int(BOSS_LABEL_TOP.get(boss_type, probe.radius)),
            }
        )
        bosses[boss_type] = entry
        total += entry["bytes"]
    cases = []
    for direction in (-3, -1, 0, 1, 2, 7):
        boss = make_boss(Boss, "abaddon", -1)
        boss.direction = direction
        cases.append([direction, heroes_mod._boss_cache_key("abaddon", boss)[4]])
    env.write_manifest(
        "bosses",
        {
            "generator": "godot_rebuild/bake/bake_boss_atlas.py",
            "source": "bosses/base_boss.py Boss.draw via heroes._boss_render_sprite_fast",
            "pose": "idle phase 0",
            "facings": list(FACINGS),
            "facing_cases": cases,
            "bosses": bosses,
        },
    )
    print(f"bosses {len(bosses)}  {total} B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
