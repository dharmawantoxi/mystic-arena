"""Bake the source build-slot markers (``ui_components`` ``BuildSlots``).

``BuildSlots.draw`` blits one cached 40x38 surface per slot at ``(x - 20, y - 17)``: the
blue slot (stone platform, glowing plus, "100G" cost tag) in five pulse variants
``pk = int(round(sin(animation_time * 0.08) * 2))`` = -2..2, and one static red slot.
The frames come straight from the REAL ``_render_blue_slot_surface`` /
``_render_red_slot_surface`` of a live ``Game``. ``pulse_cases`` records the source
formula's answer for a run of animation times so the Godot picker can be replayed.
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pygame_env as env  # noqa: E402

PULSES = (-2, -1, 0, 1, 2)
ANCHOR = (20, 17)


def main() -> int:
    import numpy as np

    pygame, core, screen = env.boot()
    random.seed("slots")
    game = core.Game(screen, level_number=1)
    component = game.ui.build_slots_component
    frames = []
    for pulse in PULSES:
        surface = component._render_blue_slot_surface(pulse)
        frames.append((f"blue:{pulse}", surface))
    frames.append(("red", component._render_red_slot_surface()))
    width, height = frames[0][1].get_size()
    sheet = np.zeros((height, width * len(frames), 4), dtype=np.uint8)
    table = {}
    for index, (key, surface) in enumerate(frames):
        assert surface.get_size() == (width, height), key
        raw = np.frombuffer(pygame.image.tostring(surface, "RGBA"), dtype=np.uint8)
        sheet[:, index * width : (index + 1) * width] = raw.reshape(height, width, 4)
        table[key] = [index * width, 0, width, height, ANCHOR[0], ANCHOR[1]]
    entry = env.write_png(env.ART_DIR / "slots" / "slots.png", sheet)
    entry.update({"frames": table})
    cases = [
        [tick, int(round(math.sin(tick * 0.08) * 2))] for tick in list(range(0, 160, 3)) + [400, 1000]
    ]
    env.write_manifest(
        "slots",
        {
            "generator": "godot_rebuild/bake/bake_slot_atlas.py",
            "source": "ui_components/_bundle.py BuildSlots._render_blue_slot_surface",
            "pulses": list(PULSES),
            "pulse_cases": cases,
            "sheet": entry,
        },
    )
    print(f"slots {entry['bytes']} B  {entry['size']}  pulse cases {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
