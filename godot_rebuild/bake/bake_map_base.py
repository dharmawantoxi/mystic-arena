"""Bake the source map base (layers 1-3) per theme and the border wall (layer 6).

``MapRenderer._render_static_map`` paints terrain + details (1), the river (2)
and three lanes (3), then decorations (4), shops (5) and the border wall (6),
all into one opaque surface. Layer 9bj baked what layers 4-5 add over the base;
Godot still rasterised layers 1-3 and 6 itself from recorded draw commands
(its own speckle seed, Bresenham lines and circles). This bake stores the base
exactly as the 9bj bake rendered it (same ``{theme}:base`` seed) and the wall,
so Godot paints base -> 9bj overlay -> wall. For every theme the script proves
that composite equals the source static map (layers 4-5 seeded like 9bj).
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pygame_env as env  # noqa: E402

# Key pixels pinned per theme so the Godot suite can prove it decodes the source
# base: left/right grass and earth, the river crossing, lanes and the centre.
PROBES = ((100, 650), (1180, 80), (640, 360), (320, 560), (960, 160), (40, 360), (1240, 360))
WALL_NAME = "border_wall"


def _rgb(pygame, surface):
    return pygame.surfarray.array3d(surface).swapaxes(0, 1)


def render_base(pygame, renderer):
    """Layers 1-3 with the 9bj bake's seed, so its overlay composes exactly."""
    from map_components.static_renderer import StaticRenderer

    width, height, theme = renderer.map_width, renderer.map_height, renderer.theme
    random.seed(f"{renderer.theme_name}:base")
    base = pygame.Surface((width, height))
    StaticRenderer.draw_terrain(base, width, height, theme)
    StaticRenderer.draw_terrain_details(base, width, height, theme)
    StaticRenderer.draw_river(base, renderer.river_points, width, height, theme)
    for points in (renderer.top_lane_points, renderer.mid_lane_points, renderer.bot_lane_points):
        StaticRenderer.draw_lane(base, points, width, height, theme)
    return base


def render_wall(pygame, renderer, np):
    """Layer 6 alone: opaque pixels over a transparent canvas.

    It is drawn over black and over white; a pixel belongs to the wall when either
    render changed it, and both renders must agree there (the wall is opaque).
    """
    from map_components.static_renderer import StaticRenderer

    width, height = renderer.map_width, renderer.map_height
    renders = []
    for fill in ((0, 0, 0), (255, 255, 255)):
        canvas = pygame.Surface((width, height))
        canvas.fill(fill)
        StaticRenderer.draw_border_wall(canvas, width, height, renderer.theme)
        renders.append(_rgb(pygame, canvas))
    dark, light = renders
    drawn = (dark != 0).any(axis=2) | (light != 255).any(axis=2)
    assert (dark[drawn] == light[drawn]).all(), "border wall must be opaque"
    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    rgba[drawn, :3] = dark[drawn]
    rgba[drawn, 3] = 255
    return rgba


def source_static_map(pygame, renderer, base):
    """``_render_static_map`` order, with layers 4-5 seeded like the 9bj bake."""
    from map_components.decoration_renderer import DecorationRenderer
    from map_components.shop_renderer import ShopRenderer
    from map_components.static_renderer import StaticRenderer

    name = renderer.theme_name
    full = base.copy()
    random.seed(f"{name}:decorations")
    DecorationRenderer.draw_all(full, renderer)
    random.seed(f"{name}:shops")
    ShopRenderer.draw(full, renderer.radiant_shop_pos, renderer.dire_shop_pos)
    StaticRenderer.draw_border_wall(full, renderer.map_width, renderer.map_height, renderer.theme)
    return _rgb(pygame, full)


def check_composite(np, name, base_rgb, wall, full_rgb):
    """Base, then the shipped 9bj overlay, then the wall == the source static map."""
    from PIL import Image

    overlay = np.array(Image.open(env.ART_DIR / "map" / f"{name}.png").convert("RGBA"))
    assert set(np.unique(overlay[..., 3])) <= {0, 255}, name
    composite = base_rgb.copy()
    covered = overlay[..., 3] == 255
    composite[covered] = overlay[covered, :3]
    walled = wall[..., 3] == 255
    composite[walled] = wall[walled, :3]
    assert (composite == full_rgb).all(), f"{name}: base + overlay + wall != source"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme", action="append", help="limit to these themes")
    args = parser.parse_args()
    import numpy as np

    pygame, _core, screen = env.boot()
    from _render import MapRenderer
    from map_components.themes import THEMES

    names = sorted(THEMES)
    if args.theme:
        names = [name for name in names if name in args.theme]
    out = env.ART_DIR / "map_base"
    wall = None
    entries = {}
    for name in names:
        renderer = MapRenderer(screen, theme_name=name)
        base = render_base(pygame, renderer)
        base_rgb = _rgb(pygame, base)
        theme_wall = render_wall(pygame, renderer, np)
        if wall is None:
            wall = theme_wall
        # The source ignores the theme for the wall, so one PNG serves every map.
        assert (theme_wall == wall).all(), f"{name}: border wall depends on the theme"
        check_composite(np, name, base_rgb, wall, source_static_map(pygame, renderer, base))
        rgba = np.dstack([base_rgb, np.full(base_rgb.shape[:2], 255, np.uint8)])
        entry = env.write_png(out / f"{name}.png", np.ascontiguousarray(rgba, dtype=np.uint8))
        entry["probes"] = [[x, y, [int(c) for c in base_rgb[y, x]]] for x, y in PROBES]
        entries[name] = entry
        print(f"{name:14s} {entry['bytes']:8d} B")
    wall_entry = env.write_png(out / f"{WALL_NAME}.png", wall)
    wall_entry["covered_pixels"] = int((wall[..., 3] == 255).sum())
    print(f"{WALL_NAME:14s} {wall_entry['bytes']:8d} B  covered {wall_entry['covered_pixels']}")
    if not args.theme:
        env.write_manifest(
            "map_base",
            {
                "generator": "godot_rebuild/bake/bake_map_base.py",
                "layers": "MapRenderer._render_static_map layers 1-3 (base) and 6 (border wall)",
                "seed": "{theme}:base",
                "themes": entries,
                "wall": wall_entry,
            },
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
