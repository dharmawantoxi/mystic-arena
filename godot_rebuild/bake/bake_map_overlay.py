"""Bake the source map decorations and shop buildings, one PNG per theme.

``MapRenderer._render_static_map`` paints terrain, river and lanes (layers 1-3),
then DecorationRenderer (4), ShopRenderer (5) and the border wall (6). Godot
already rasterises layers 1-3 and 6 natively, so this bake keeps only what
layers 4-5 add: every pixel whose final colour differs from the layer 1-3
render is stored opaque, every other pixel stays transparent. Drawn over the
same base it reproduces the source pixel for pixel (checked below).
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pygame_env as env  # noqa: E402


def bake_theme(pygame, theme_name, screen, np):
    from _render import MapRenderer
    from map_components.decoration_renderer import DecorationRenderer
    from map_components.shop_renderer import ShopRenderer
    from map_components.static_renderer import StaticRenderer

    mr = MapRenderer(screen, theme_name=theme_name)
    width, height, theme = mr.map_width, mr.map_height, mr.theme
    # The source reseeds from entropy after generating its layout, so the fine
    # detail of every draw call differs per run. Fixed seeds keep the bake stable.
    random.seed(f"{theme_name}:base")
    base = pygame.Surface((width, height))
    StaticRenderer.draw_terrain(base, width, height, theme)
    StaticRenderer.draw_terrain_details(base, width, height, theme)
    StaticRenderer.draw_river(base, mr.river_points, width, height, theme)
    for points in (mr.top_lane_points, mr.mid_lane_points, mr.bot_lane_points):
        StaticRenderer.draw_lane(base, points, width, height, theme)
    full = base.copy()
    random.seed(f"{theme_name}:decorations")
    DecorationRenderer.draw_all(full, mr)
    random.seed(f"{theme_name}:shops")
    ShopRenderer.draw(full, mr.radiant_shop_pos, mr.dire_shop_pos)

    base_rgb = pygame.surfarray.array3d(base).swapaxes(0, 1)
    full_rgb = pygame.surfarray.array3d(full).swapaxes(0, 1)
    changed = (base_rgb != full_rgb).any(axis=2)
    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    rgba[changed, :3] = full_rgb[changed]
    rgba[changed, 3] = 255
    # Self-check: overlay over base == source composite.
    composite = np.where(changed[..., None], rgba[..., :3], base_rgb)
    assert (composite == full_rgb).all(), theme_name
    return rgba, int(changed.sum())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme", action="append", help="limit to these themes")
    args = parser.parse_args()
    import numpy as np

    pygame, _core, screen = env.boot()
    from map_components.themes import THEMES

    names = sorted(THEMES)
    if args.theme:
        names = [name for name in names if name in args.theme]
    entries = {}
    for name in names:
        rgba, covered = bake_theme(pygame, name, screen, np)
        entry = env.write_png(env.ART_DIR / "map" / f"{name}.png", rgba)
        entry["covered_pixels"] = covered
        entries[name] = entry
        print(f"{name:14s} {entry['bytes']:8d} B  covered {covered}")
    if not args.theme:
        env.write_manifest(
            "map_overlay",
            {
                "generator": "godot_rebuild/bake/bake_map_overlay.py",
                "layers": "MapRenderer._render_static_map layers 4-5",
                "themes": entries,
            },
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
