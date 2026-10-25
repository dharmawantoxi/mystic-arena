"""Bake the source main-menu background (``Menu._build_main_background`` of ``_core.py``).

The pygame menu blits one cached 1280x720 surface (night sky, nebula, 170 stars, the big
moon, arcane rings, mountain silhouettes, three glowing lanes, two portals, rune crystals,
a perspective grid and a vignette) and then draws the animated fog and particles on top.
This script runs the REAL background and two-layer fog builders on a live ``Menu``. It writes
the static layer plus both transparent fog textures; particles remain live GDScript, replaying
the exact source motion and glow equations. ``probes`` records source pixels for the static
frame, while the fog frames retain the source surfaces' RGBA values and parallax parameters.
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

    fog_layers = menu._build_menu_fog()
    fog_width = fog_layers[0][0].get_width()
    assert len(fog_layers) == 2 and all(
        fog.get_size() == (fog_width, height) for fog, _speed, _alpha in fog_layers
    )
    fog_rgba = np.zeros((height, fog_width * len(fog_layers), 4), dtype=np.uint8)
    fog_frames = []
    layer_params = []
    for index, (fog, speed, alpha) in enumerate(fog_layers):
        raw_fog = np.frombuffer(pygame.image.tostring(fog, "RGBA"), dtype=np.uint8)
        frame = raw_fog.reshape(height, fog_width, 4)
        left = index * fog_width
        fog_rgba[:, left : left + fog_width] = frame
        fog_frames.append([left, 0, fog_width, height])
        layer_params.append({"speed": speed, "alpha": alpha})
    fog_entry = env.write_png(env.ART_DIR / "menu" / "menu_fog.png", fog_rgba)
    env.write_manifest(
        "menu",
        {
            "generator": "godot_rebuild/bake/bake_menu_background.py",
            "source": "_core.py Menu._build_main_background / Menu._build_menu_fog",
            "background": entry,
            "fog": {
                **fog_entry,
                "frames": {f"layer_{index}": frame for index, frame in enumerate(fog_frames)},
                "layers": layer_params,
                "source_size": [fog_width, height],
            },
            "probes": probes,
        },
    )
    print(
        f"menu background {entry['bytes']} B {entry['size']}  "
        f"fog {fog_entry['bytes']} B {fog_entry['size']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
