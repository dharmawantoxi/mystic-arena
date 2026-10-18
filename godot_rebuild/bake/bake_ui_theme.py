"""Bake the source UI skin (``ui_theme.py``) into nine-patch sheets.

The panels and pill buttons of the pygame menus come from ``ui_theme.panel`` and
``ui_theme.pill``. This script calls those REAL functions on transparent surfaces:

* ``panels.png``: ``panel()`` as the dialogs call it (``border_w=2``) and with its defaults
  (``border_w=1``), each on a 80x80 canvas. The panel rect is 72x72 at (4, 4), so the
  4 px soft shadow lies in the canvas margin. Nine-patch margin 20 keeps the shadow, the
  radius-12 corners and the gold corner ticks (inset 2, length 11) inside the corner cells.
* ``pills.png``: every ``pill()`` kind in normal, hover (with the radial glow) and disabled
  state, each on a 54x48 canvas. The pill rect is 24x24 at (15, 12) so the hover glow
  (blitted at ``(x - 15, y - 12)``) fits. Nine-patch margin is 23 x 20.

The label is not part of the skin (Godot draws its own text), so ``draw_text`` is silenced
for the bake. ``palette`` records every colour constant of the module, ``pill_colors`` the
text/edge/fill table read from the ``pill()`` source, so the Godot theme can be pinned to
the source values rather than to copies.
"""
from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pygame_env as env  # noqa: E402

PANEL_RECT = (4, 4, 72, 72)
PANEL_CANVAS = (80, 80)
PANEL_MARGIN = 20
PANEL_EXPAND = 4
PANELS = (
    ("panel_bold", {"border_w": 2}),
    ("panel", {}),
)
PILL_RECT = (15, 12, 24, 24)
PILL_CANVAS = (54, 48)
PILL_MARGIN = (23, 20)
PILL_EXPAND = (15, 12)
STATES = ("normal", "hover", "disabled")


def _palette(ui_theme) -> dict:
    table = {}
    for name, value in sorted(vars(ui_theme).items()):
        is_color = isinstance(value, tuple) and len(value) == 3
        if name.isupper() and is_color and all(isinstance(c, int) for c in value):
            table[name] = list(value)
    return table


def _pill_table(ui_theme) -> dict:
    """The ``colors`` literal inside ``pill()``, evaluated in the module namespace."""
    tree = ast.parse(inspect.getsource(ui_theme.pill))
    for node in ast.walk(tree):
        is_colors = isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "colors"
        if is_colors:
            expression = ast.fix_missing_locations(ast.Expression(body=node.value))
            code = compile(expression, "ui_theme.pill colors", "eval")
            return eval(code, dict(vars(ui_theme)))  # noqa: S307 - source literal
    raise SystemExit("ui_theme.pill has no colors table")


def _rgba(pygame, surface):
    import numpy as np

    width, height = surface.get_size()
    raw = np.frombuffer(pygame.image.tostring(surface, "RGBA"), dtype=np.uint8)
    return raw.reshape(height, width, 4)


def main() -> int:
    import numpy as np

    pygame, _core, _screen = env.boot()
    import ui_theme

    assert ui_theme.cheap_alpha(), "the bake needs the rich (alpha) path of ui_theme"
    ui_theme.clear_caches()
    ui_theme.draw_text = lambda *args, **kwargs: None  # text is drawn by Godot

    panels = np.zeros((PANEL_CANVAS[1], PANEL_CANVAS[0] * len(PANELS), 4), dtype=np.uint8)
    panel_frames = {}
    for index, (key, kwargs) in enumerate(PANELS):
        canvas = pygame.Surface(PANEL_CANVAS, pygame.SRCALPHA)
        ui_theme.panel(canvas, PANEL_RECT, **kwargs)
        left = index * PANEL_CANVAS[0]
        panels[:, left : left + PANEL_CANVAS[0]] = _rgba(pygame, canvas)
        panel_frames[key] = [left, 0, PANEL_CANVAS[0], PANEL_CANVAS[1]]
    panel_entry = env.write_png(env.ART_DIR / "ui" / "panels.png", panels)

    table = _pill_table(ui_theme)
    kinds = list(table)
    cell_w, cell_h = PILL_CANVAS
    pills = np.zeros((cell_h * len(STATES), cell_w * len(kinds), 4), dtype=np.uint8)
    pill_frames = {}
    font = pygame.font.Font(None, 12)
    for column, kind in enumerate(kinds):
        for row, state in enumerate(STATES):
            canvas = pygame.Surface(PILL_CANVAS, pygame.SRCALPHA)
            ui_theme.pill(
                canvas,
                {},
                "bake",
                "",
                PILL_RECT,
                kind,
                font,
                hover=state == "hover",
                enabled=state != "disabled",
            )
            pills[row * cell_h : (row + 1) * cell_h, column * cell_w : (column + 1) * cell_w] = _rgba(
                pygame, canvas
            )
            pill_frames[f"{kind}:{state}"] = [column * cell_w, row * cell_h, cell_w, cell_h]
    pill_entry = env.write_png(env.ART_DIR / "ui" / "pills.png", pills)

    pill_colors = {
        kind: {"top": list(c[0]), "bottom": list(c[1]), "edge": list(c[2]), "text": list(c[3])}
        for kind, c in table.items()
    }
    env.write_manifest(
        "ui_theme",
        {
            "generator": "godot_rebuild/bake/bake_ui_theme.py",
            "source": "ui_theme.py panel / pill",
            "palette": _palette(ui_theme),
            "panels": {
                **panel_entry,
                "frames": panel_frames,
                "rect": list(PANEL_RECT),
                "margin": PANEL_MARGIN,
                "expand": PANEL_EXPAND,
            },
            "pills": {
                **pill_entry,
                "frames": pill_frames,
                "rect": list(PILL_RECT),
                "margin": list(PILL_MARGIN),
                "expand": list(PILL_EXPAND),
                "kinds": kinds,
                "states": list(STATES),
                "colors": pill_colors,
            },
        },
    )
    print(
        f"ui panels {panel_entry['bytes']} B {panel_entry['size']}  "
        f"pills {pill_entry['bytes']} B {pill_entry['size']}  kinds {kinds}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
