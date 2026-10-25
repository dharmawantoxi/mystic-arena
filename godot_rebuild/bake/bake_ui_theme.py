"""Bake source ``ui_theme.py`` panels, pills and interactive controls.

Every frame below is painted by the real pygame helper onto transparent
surfaces. Labels are deliberately omitted so Godot can render translated
text, while the exact source gradients, borders, glows and icon vectors stay
in the exported sheets.

Run: ``python godot_rebuild/bake/bake_ui_theme.py``
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
PANELS = (("panel_bold", {"border_w": 2}), ("panel", {}))
PILL_RECT = (15, 12, 24, 24)
PILL_CANVAS = (54, 48)
PILL_MARGIN = (23, 20)
PILL_EXPAND = (15, 12)
STATES = ("normal", "hover", "disabled")

BUTTON_CANVAS = (422, 94)
BUTTON_STYLES = {
    "continue": (140, 225, 255),
    "play": (100, 220, 110),
    "hero": (255, 220, 100),
    "input": (100, 200, 220),
    "help": (110, 180, 255),
    "settings": (205, 180, 105),
    "credits": (200, 130, 210),
    "quit": (225, 90, 90),
}
BUTTON_STATES = ("normal", "hover")
BUTTON_MARGINS = {"normal": [31, 22], "hover": [22, 18]}

TAB_CANVAS = (320, 40)
TAB_STYLES = {
    "starter": (100, 200, 255),
    "mini": (255, 150, 100),
    "true": (255, 80, 100),
}
TAB_STATES = ("active", "inactive", "hover")

TOGGLE_CANVAS = (60, 26)
TOGGLE_STATES = ("off", "off_hover", "on", "on_hover")
TOGGLE_MARGIN = [13, 13]

ICON_CANVAS = (36, 36)


def _palette(ui_theme) -> dict:
    table = {}
    for name, value in sorted(vars(ui_theme).items()):
        is_color = isinstance(value, tuple) and len(value) == 3
        if name.isupper() and is_color and all(isinstance(c, int) for c in value):
            table[name] = list(value)
    return table


def _pill_table(ui_theme) -> dict:
    """The ``colors`` literal inside ``pill()``, evaluated in its module namespace."""
    tree = ast.parse(inspect.getsource(ui_theme.pill))
    for node in ast.walk(tree):
        is_colors = isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "colors"
        if is_colors:
            expression = ast.fix_missing_locations(ast.Expression(body=node.value))
            code = compile(expression, "ui_theme.pill colors", "eval")
            return eval(code, dict(vars(ui_theme)))  # noqa: S307 - source literal
    raise SystemExit("ui_theme.pill has no colors table")


def _icon_names(ui_theme) -> list[str]:
    tree = ast.parse(inspect.getsource(ui_theme.draw_icon))
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare) or not isinstance(node.left, ast.Name):
            continue
        if node.left.id != "name":
            continue
        for comparator in node.comparators:
            if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
                names.add(comparator.value)
            elif isinstance(comparator, (ast.Tuple, ast.List)):
                names.update(
                    item.value
                    for item in comparator.elts
                    if isinstance(item, ast.Constant) and isinstance(item.value, str)
                )
    return sorted(names)


def _rgba(pygame, surface):
    import numpy as np

    width, height = surface.get_size()
    raw = np.frombuffer(pygame.image.tostring(surface, "RGBA"), dtype=np.uint8)
    return raw.reshape(height, width, 4)


def _sheet(np, canvas: tuple[int, int], columns: int, rows: int):
    return np.zeros((canvas[1] * rows, canvas[0] * columns, 4), dtype=np.uint8)


def main() -> int:
    import numpy as np

    pygame, _core, _screen = env.boot()
    import ui_theme

    assert ui_theme.cheap_alpha(), "the bake needs the rich (alpha) path of ui_theme"
    ui_theme.clear_caches()
    ui_theme.draw_text = lambda *args, **kwargs: None  # translated text belongs to Godot

    panels = _sheet(np, PANEL_CANVAS, len(PANELS), 1)
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
    pills = _sheet(np, PILL_CANVAS, len(kinds), len(STATES))
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

    # Premium menu button(): source gradient, left accent, bevel, ticks, shadow and hover glow.
    buttons = _sheet(np, BUTTON_CANVAS, len(BUTTON_STYLES), len(BUTTON_STATES))
    button_frames = {}
    for column, (style, accent) in enumerate(BUTTON_STYLES.items()):
        for row, state in enumerate(BUTTON_STATES):
            canvas = pygame.Surface(BUTTON_CANVAS, pygame.SRCALPHA)
            ui_theme.button(
                canvas,
                {},
                "bake",
                "",
                BUTTON_CANVAS[0] // 2,
                BUTTON_CANVAS[1] // 2,
                accent,
                font,
                w=360,
                h=50,
                icon=None,
                hover=state == "hover",
                letter_gap=False,
            )
            buttons[
                row * BUTTON_CANVAS[1] : (row + 1) * BUTTON_CANVAS[1],
                column * BUTTON_CANVAS[0] : (column + 1) * BUTTON_CANVAS[0],
            ] = _rgba(pygame, canvas)
            button_frames[f"{style}:{state}"] = [
                column * BUTTON_CANVAS[0],
                row * BUTTON_CANVAS[1],
                BUTTON_CANVAS[0],
                BUTTON_CANVAS[1],
            ]
    button_entry = env.write_png(env.ART_DIR / "ui" / "buttons.png", buttons)

    # Source tab(): active accent, inactive, and hovered inactive states.
    tabs = _sheet(np, TAB_CANVAS, len(TAB_STYLES), len(TAB_STATES))
    tab_frames = {}
    for column, (style, accent) in enumerate(TAB_STYLES.items()):
        for row, state in enumerate(TAB_STATES):
            canvas = pygame.Surface(TAB_CANVAS, pygame.SRCALPHA)
            ui_theme.tab(
                canvas,
                {},
                "bake",
                (0, 0, *TAB_CANVAS),
                "",
                accent,
                font,
                active=state == "active",
                hover=state == "hover",
            )
            tabs[
                row * TAB_CANVAS[1] : (row + 1) * TAB_CANVAS[1],
                column * TAB_CANVAS[0] : (column + 1) * TAB_CANVAS[0],
            ] = _rgba(pygame, canvas)
            tab_frames[f"{style}:{state}"] = [
                column * TAB_CANVAS[0],
                row * TAB_CANVAS[1],
                TAB_CANVAS[0],
                TAB_CANVAS[1],
            ]
    tab_entry = env.write_png(env.ART_DIR / "ui" / "tabs.png", tabs)

    # Source toggle(): its knob and gradient are baked; Godot supplies the localized ON/OFF label.
    toggles = _sheet(np, TOGGLE_CANVAS, 2, 2)
    toggle_frames = {}
    toggle_specs = (
        ("off", False, False),
        ("off_hover", False, True),
        ("on", True, False),
        ("on_hover", True, True),
    )
    for index, (state, is_on, hover) in enumerate(toggle_specs):
        column, row = index % 2, index // 2
        canvas = pygame.Surface(TOGGLE_CANVAS, pygame.SRCALPHA)
        ui_theme.toggle(canvas, {}, "bake", (0, 0, *TOGGLE_CANVAS), is_on, font, hover=hover)
        toggles[
            row * TOGGLE_CANVAS[1] : (row + 1) * TOGGLE_CANVAS[1],
            column * TOGGLE_CANVAS[0] : (column + 1) * TOGGLE_CANVAS[0],
        ] = _rgba(pygame, canvas)
        toggle_frames[state] = [
            column * TOGGLE_CANVAS[0],
            row * TOGGLE_CANVAS[1],
            TOGGLE_CANVAS[0],
            TOGGLE_CANVAS[1],
        ]
    toggle_entry = env.write_png(env.ART_DIR / "ui" / "toggles.png", toggles)

    icon_names = _icon_names(ui_theme)
    icon_columns = 6
    icon_rows = (len(icon_names) + icon_columns - 1) // icon_columns
    icons = _sheet(np, ICON_CANVAS, icon_columns, icon_rows)
    icon_frames = {}
    for index, name in enumerate(icon_names):
        column, row = index % icon_columns, index // icon_columns
        canvas = pygame.Surface(ICON_CANVAS, pygame.SRCALPHA)
        ui_theme.draw_icon(canvas, name, 18, 18, (255, 255, 255), s=0.9)
        icons[
            row * ICON_CANVAS[1] : (row + 1) * ICON_CANVAS[1],
            column * ICON_CANVAS[0] : (column + 1) * ICON_CANVAS[0],
        ] = _rgba(pygame, canvas)
        icon_frames[name] = [
            column * ICON_CANVAS[0],
            row * ICON_CANVAS[1],
            ICON_CANVAS[0],
            ICON_CANVAS[1],
        ]
    icon_entry = env.write_png(env.ART_DIR / "ui" / "icons.png", icons)

    glow = ui_theme._radial(36, 36, ui_theme.GOLD, 80)
    glow_entry = env.write_png(env.ART_DIR / "ui" / "slider_glow.png", _rgba(pygame, glow))

    pill_colors = {
        kind: {"top": list(c[0]), "bottom": list(c[1]), "edge": list(c[2]), "text": list(c[3])}
        for kind, c in table.items()
    }
    env.write_manifest(
        "ui_theme",
        {
            "generator": "godot_rebuild/bake/bake_ui_theme.py",
            "source": "ui_theme.py panel / pill / button / toggle / slider glow / tab / draw_icon",
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
            "controls": {
                "buttons": {
                    **button_entry,
                    "frames": button_frames,
                    "canvas": list(BUTTON_CANVAS),
                    "styles": list(BUTTON_STYLES),
                    "states": list(BUTTON_STATES),
                    "accents": {key: list(value) for key, value in BUTTON_STYLES.items()},
                    "margins": BUTTON_MARGINS,
                    "expands": BUTTON_MARGINS,
                },
                "tabs": {
                    **tab_entry,
                    "frames": tab_frames,
                    "canvas": list(TAB_CANVAS),
                    "styles": list(TAB_STYLES),
                    "states": list(TAB_STATES),
                    "accents": {key: list(value) for key, value in TAB_STYLES.items()},
                    "margin": [10, 10],
                    "expand": [0, 0],
                },
                "toggles": {
                    **toggle_entry,
                    "frames": toggle_frames,
                    "canvas": list(TOGGLE_CANVAS),
                    "states": list(toggle_frames),
                    "margin": TOGGLE_MARGIN,
                    "expand": [0, 0],
                },
                "icons": {
                    **icon_entry,
                    "frames": icon_frames,
                    "names": icon_names,
                    "tile": list(ICON_CANVAS),
                },
                "slider_glow": {
                    **glow_entry,
                    "frame": [0, 0, 36, 36],
                    "source": "ui_theme._radial(36, 36, GOLD, 80)",
                },
            },
        },
    )
    print(
        "ui panels %s  pills %s  buttons %s  tabs %s  toggles %s  icons %s"
        % (
            panel_entry["size"],
            pill_entry["size"],
            button_entry["size"],
            tab_entry["size"],
            toggle_entry["size"],
            icon_entry["size"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
