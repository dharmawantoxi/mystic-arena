"""Bake the source main-menu background (``Menu._build_main_background`` of ``_core.py``).

The pygame menu blits one cached 1280x720 surface (night sky, nebula, 170 stars, the big
moon, arcane rings, mountain silhouettes, three glowing lanes, two portals, rune crystals,
a perspective grid and a vignette) and then draws the animated fog and particles on top.
This script runs the REAL builder on a live ``Menu`` and writes the static layer. ``probes``
records a few pixels as the source surface holds them, so the Godot side can be pinned to
the source rather than to a copy.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pygame_env as env  # noqa: E402

PROBES = (
    (0, 0),
    (640, 5),
    (1279, 719),
    (281, 115),
    (640, 360),
    (120, 612),
    (1135, 168),
    (30, 700),
    (900, 40),
)


def main() -> int:
    import numpy as np

    pygame, core, screen = env.boot()
    menu = core.Menu(screen)
    surface = menu._build_main_background()
    width, height = surface.get_size()
    assert (width, height) == env.SCREEN, (width, height)
    rgb = np.frombuffer(pygame.image.tostring(surface, "RGB"), dtype=np.uint8)
    rgb = rgb.reshape(height, width, 3)
    rgba = np.dstack([rgb, np.full((height, width), 255, dtype=np.uint8)])
    entry = env.write_png(env.ART_DIR / "menu" / "main_background.png", rgba)
    probes = [[x, y, *list(surface.get_at((x, y)))[:3]] for x, y in PROBES]
    env.write_manifest(
        "menu",
        {
            "generator": "godot_rebuild/bake/bake_menu_background.py",
            "source": "_core.py Menu._build_main_background",
            "background": entry,
            "probes": probes,
        },
    )
    print(f"menu background {entry['bytes']} B  {entry['size']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
