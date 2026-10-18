"""Bake the source tower bullets (``_entity.py`` ``_get_bullet_sprite``).

``Bullet.draw`` blits one cached sprite per key ``(bullet_type, team, angle_k)`` at
``(int(x - ax), int(y - ay))``. Only the arrow (``normal``) depends on the direction: 16
buckets ``angle_k = (int(angle / (2 * pi) * 16) + 16) % 16`` of the bearing to its target;
cannon, ice and mage bolts are static. The frames come from the REAL ``_get_bullet_sprite``;
``angle_cases`` records which bucket the real function chose for a ring of bearings so the
Godot picker can be replayed against it.
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pygame_env as env  # noqa: E402

TEAMS = ("blue", "red")
STATIC_TYPES = ("cannon", "ice", "mage")
BUCKETS = 16
COLUMNS = 8


def sprite_for(entity, bullet_cls, dummy_cls, bullet_type, team, bearing):
    """``(key, entry, seen)`` the real function builds for a bullet flying along ``bearing``.

    ``seen`` is the ``atan2`` bearing (-pi..pi) the function itself computes from the target.
    """
    entity._BULLET_SPRITE_CACHE.clear()
    target = dummy_cls(400.0 + math.cos(bearing) * 100.0, 300.0 + math.sin(bearing) * 100.0)
    bullet = bullet_cls(400.0, 300.0, target, 10, team, bullet_type)
    random.seed(f"{bullet_type}:{team}:{bearing:.4f}")
    entry = entity._get_bullet_sprite(bullet)
    keys = list(entity._BULLET_SPRITE_CACHE)
    assert len(keys) == 1, keys
    return keys[0], entry, math.atan2(target.y - bullet.y, target.x - bullet.x)


def main() -> int:
    import numpy as np

    pygame, _core, _screen = env.boot()
    import _entity as entity

    bullet_cls = entity.Bullet
    dummy_cls = entity._DummyBulletTarget
    frames = []
    for team in TEAMS:
        for bucket in range(BUCKETS):
            # Bucket 8 is reached only by a bearing of exactly pi (target dead left, same y).
            signed = bucket if bucket < 8 else bucket - 16
            bearing = (signed + (0.2 if signed >= 0 else -0.2)) * 2.0 * math.pi / BUCKETS
            if bucket == 8:
                bearing = math.pi
            key, (sprite, ax, ay), _seen = sprite_for(entity, bullet_cls, dummy_cls, "normal", team, bearing)
            assert key == ("normal", team, bucket), (key, bucket)
            frames.append((f"normal:{team}:{bucket}", sprite, ax, ay))
        for bullet_type in STATIC_TYPES:
            key, (sprite, ax, ay), _seen = sprite_for(entity, bullet_cls, dummy_cls, bullet_type, team, 0.0)
            assert key == (bullet_type, team, 0), key
            frames.append((f"{bullet_type}:{team}", sprite, ax, ay))
    cell_w = max(f[1].get_width() for f in frames)
    cell_h = max(f[1].get_height() for f in frames)
    rows = -(-len(frames) // COLUMNS)
    sheet = np.zeros((rows * cell_h, COLUMNS * cell_w, 4), dtype=np.uint8)
    table = {}
    for index, (key, sprite, ax, ay) in enumerate(frames):
        width, height = sprite.get_size()
        raw = np.frombuffer(pygame.image.tostring(sprite, "RGBA"), dtype=np.uint8)
        x, y = (index % COLUMNS) * cell_w, (index // COLUMNS) * cell_h
        sheet[y : y + height, x : x + width] = raw.reshape(height, width, 4)
        table[key] = [x, y, width, height, int(ax), int(ay)]
    entry = env.write_png(env.ART_DIR / "bullets" / "bullets.png", sheet)
    entry.update({"cell": [cell_w, cell_h], "columns": COLUMNS, "frames": table})
    cases = []
    for step in range(-32, 33):
        bearing = step * math.pi / 32.0 + 0.013
        key, _entry, seen = sprite_for(entity, bullet_cls, dummy_cls, "normal", "blue", bearing)
        cases.append([round(seen, 6), key[2]])
    key, _entry, seen = sprite_for(entity, bullet_cls, dummy_cls, "normal", "blue", math.pi)
    cases.append([seen, key[2]])
    env.write_manifest(
        "bullets",
        {
            "generator": "godot_rebuild/bake/bake_bullet_atlas.py",
            "source": "_entity.py _get_bullet_sprite via Bullet / _draw_hd_arrow",
            "buckets": BUCKETS,
            "types": ["normal", *STATIC_TYPES],
            "teams": list(TEAMS),
            "angle_cases": cases,
            "sheet": entry,
        },
    )
    print(f"bullets {entry['bytes']} B  {entry['size']}  frames {len(table)}  cases {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
