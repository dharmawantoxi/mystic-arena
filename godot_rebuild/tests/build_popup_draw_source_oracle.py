"""Source oracle for the build tower popup (layer 9bv7).

`Game.draw` paints `ui.draw_build_popup(self.screen)` right after the tactical command bar
whenever `g.build_popup_slot` is set, i.e. while an empty build slot is selected. `BuildPopup`
(`ui_components/_bundle.py`, cheap-alpha branch) draws a 400 x 300 panel at the slot, clamped
into the frame, with a gold connector line, a shadow + gold gradient card, gold corner ticks,
the "BUILD TOWER" Cinzel title, the `Gold: n (Cost: 100)` line, an X close button and a 2x2
grid of four tower cards (archer, cannon, ice, mage) each with a coin icon and cost. Hover
comes from `pygame.mouse.get_pos()`; a card is hovered only when the gold covers the 100 cost.

The REAL `draw`, `_draw_tower_buttons` and `_draw_close_button` (the last inherited from
`BaseUIComponent`) plus `ui_theme.draw_icon`, `ui_theme.corner_ticks` and `ui_theme.fit_ellipsis`
run under the recording pygame shim. `_shadow`, `_vgrad`, `_radial` and `outline_text` are
recorded as one op each; every harvested helper call is preceded by a `section` op. The
fixture pins the classic fallback and the mobile right-panel branch. The latter runs the real
`platform_utils.panel_popup_pos`, compact panel width, and full display surface. The recorder's
`_has_glyph` shim intentionally exercises `fit_ellipsis`'s three-dot fallback; the live SidePanel
selects the real font's U+2026 glyph when available.

Run: python godot_rebuild/tests/build_popup_draw_source_oracle.py
"""
import ast
import json
import textwrap
import types
from pathlib import Path
from types import SimpleNamespace

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "ui_components" / "_bundle.py"
CORE = ROOT / "_core.py"
UI_THEME = ROOT / "ui_theme.py"
PLATFORM_UTILS = ROOT / "mobile" / "platform_utils.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "build_popup_draw_source.json"
SECTIONS = ("_draw_close_button", "_draw_tower_buttons")

# (label, slot, gold, mouse, cheap_alpha, panel_rect)
FRAMES = [
    ("center", (640, 400), 500, (0, 0), True, None),
    ("top_clamp", (640, 60), 500, (0, 0), True, None),
    ("left_clamp", (20, 400), 500, (0, 0), True, None),
    ("right_clamp", (1260, 400), 500, (0, 0), True, None),
    ("hover_close", (640, 400), 500, (820, 80), True, None),
    ("hover_tower", (640, 400), 500, (500, 150), True, None),
    ("cant_afford", (640, 400), 50, (0, 0), True, None),
    ("flat_panel", (640, 400), 500, (0, 0), False, None),
    ("big_gold", (640, 400), 1234, (0, 0), True, None),
    ("wide_panel_hover_tower", (640, 400), 500, (1310, 280), True, (1280, 0, 344, 720)),
    ("narrow_panel_flat", (640, 400), 50, (0, 0), False, (1280, 0, 120, 720)),
]


def _constant(path, name):
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("%s not found in %s" % (name, path.name))


def _method(text, class_name, name):
    owner = next(
        (n for n in ast.walk(ast.parse(text))
         if isinstance(n, ast.ClassDef) and n.name == class_name),
        None,
    )
    if owner is None:
        raise AssertionError("%s not found in %s" % (class_name, BUNDLE.name))
    found = {n.name: n for n in owner.body
             if isinstance(n, ast.FunctionDef) and n.name == name}
    if name not in found:
        raise AssertionError("%s.%s not found in %s" % (class_name, name, BUNDLE.name))
    return ast.get_source_segment(text, found[name], padded=True)


def _popup_class(namespace):
    text = BUNDLE.read_text(encoding="utf-8")
    body = "".join(
        textwrap.indent(textwrap.dedent(_method(text, cls, name)), "    ") + "\n"
        for cls, name in (("BuildPopup", "draw"), ("BuildPopup", "_draw_tower_buttons"),
                          ("BaseUIComponent", "_draw_close_button"))
    )
    exec(compile("class BuildPopup:\n%s" % body, BUNDLE.name, "exec"), namespace)
    cls = namespace["BuildPopup"]
    for name in SECTIONS:
        original = getattr(cls, name)

        def wrapped(self, surface, *args, _original=original, _name=name, **kwargs):
            surface.ops.append({"kind": "section", "name": _name})
            return _original(self, surface, *args, **kwargs)

        setattr(cls, name, wrapped)
    return cls


def _surface_with(op, w, h):
    surface = rec.Surface((w, h))
    surface.ops.append(op)
    return surface


def _ui_theme(pygame, cheap_flag):
    module = types.ModuleType("ui_theme")
    module.pygame = pygame
    module.GOLD = _constant(UI_THEME, "GOLD")
    module.GOLD_BRIGHT = _constant(UI_THEME, "GOLD_BRIGHT")
    module.GOLD_TEXT = _constant(UI_THEME, "GOLD_TEXT")
    module.cheap_alpha = lambda: cheap_flag["cheap"]

    def radial(w, h, color, alpha):
        a = max(4, min(120, int(alpha) // 8 * 8))
        return _surface_with({"kind": "radial", "rect": [0, 0, int(w), int(h)],
                              "color": list(color), "alpha": a, "mult": 255}, w, h)

    def shadow(w, h, radius=12, alpha=110, spread=4):
        sw, sh = int(w) + spread * 2, int(h) + spread * 2
        return _surface_with({"kind": "shadow", "rect": [0, 0, sw, sh], "radius": int(radius),
                              "alpha": int(alpha), "mult": 255}, sw, sh)

    def vgrad(w, h, top, bottom, radius=0):
        return _surface_with({"kind": "vgrad", "rect": [0, 0, int(w), int(h)], "top": list(top),
                              "bottom": list(bottom), "radius": int(radius), "mult": 255}, w, h)

    def outline_text(screen, font, text, color, center, outline=(8, 9, 18), width=2,
                     body_top=None, body_bottom=None):
        w, h = font.size(text)
        x, y = int(center[0]) - w // 2, int(center[1]) - h // 2
        screen.ops.append({"kind": "outline_text", "text": text, "size": font.font_size,
                           "style": font.style, "pos": [x, y], "outline": list(outline),
                           "width": int(width),
                           "top": list(body_top) if body_top is not None else list(module.GOLD_BRIGHT),
                           "bottom": list(body_bottom) if body_bottom is not None else [196, 138, 40],
                           "mult": 255})
        return rec.Rect(x, y, w, h)

    module._radial, module._shadow, module._vgrad = radial, shadow, vgrad
    module.outline_text = outline_text
    module._has_glyph = lambda font, ch: False
    for segment in rec.harvest(UI_THEME, ["draw_icon", "corner_ticks", "fit_ellipsis"]):
        exec(compile(segment, UI_THEME.name, "exec"), module.__dict__)
    return module


def source_fixture():
    if not hasattr(rec.Rect, "center"):
        rec.Rect.center = property(lambda self: (self.x + self.w // 2, self.y + self.h // 2))
    clock = {"ticks": 0}
    pygame = rec.make_pygame(clock)
    gold = _constant(CORE, "GOLD")
    cheap_flag = {"cheap": True}
    mobile = types.ModuleType("mobile")
    platform_utils = types.ModuleType("mobile.platform_utils")
    display_state = {"panel": None, "full": None}
    platform_utils._display_state = display_state
    platform_utils.get_panel_rect = lambda: display_state["panel"]
    platform_utils.get_full_surface = lambda: display_state["full"]
    for segment in rec.harvest(PLATFORM_UTILS, ["panel_popup_pos"]):
        exec(compile(segment, PLATFORM_UTILS.name, "exec"), platform_utils.__dict__)
    mobile.platform_utils = platform_utils
    frames = []
    with rec.installed({"mobile": mobile, "mobile.platform_utils": platform_utils}):
        namespace = {
            "pygame": pygame, "math": __import__("math"),
            "ui_theme": _ui_theme(pygame, cheap_flag),
            "SCREEN_WIDTH": _constant(CORE, "SCREEN_WIDTH"),
            "SCREEN_HEIGHT": _constant(CORE, "SCREEN_HEIGHT"),
            "GOLD": gold,
            "RED": _constant(CORE, "RED"),
            "WHITE": _constant(CORE, "WHITE"),
            "GRAY": _constant(CORE, "GRAY"),
            "TOWER_TYPE_COLORS": _constant(CORE, "TOWER_TYPE_COLORS"),
            "get_font": lambda size, style="body", bold=False: rec.Font(size, style),
            "title_font": lambda size, bold=True: rec.Font(
                max(8, min(int(size), 220)), "title"),
        }
        for segment in rec.harvest(BUNDLE, ["_popup_di_panel"]):
            exec(compile(segment, BUNDLE.name, "exec"), namespace)
        cls = _popup_class(namespace)
        for label, slot, gold_value, mouse, cheap, panel_rect in FRAMES:
            cheap_flag["cheap"] = cheap
            pygame.mouse = SimpleNamespace(get_pos=lambda mouse=mouse: mouse)
            popup = cls.__new__(cls)
            popup.game = SimpleNamespace(
                gold=gold_value, ui_buttons={},
                build_popup_slot={"x": int(slot[0]), "y": int(slot[1])})
            screen = rec.Surface((1280, 720))
            if panel_rect is None:
                display_state["panel"] = None
                full_surface = screen
            else:
                display_state["panel"] = pygame.Rect(panel_rect)
                full_surface = rec.Surface((panel_rect[0] + panel_rect[2], panel_rect[1] + panel_rect[3]))
            display_state["full"] = full_surface
            popup.draw(screen)
            target_is_panel = full_surface is not screen and bool(full_surface.ops)
            target = full_surface if target_is_panel else screen
            frames.append({
                "label": label,
                "slot": [int(slot[0]), int(slot[1])],
                "gold": int(gold_value),
                "mouse": [int(mouse[0]), int(mouse[1])],
                "cheap_alpha": bool(cheap),
                "panel": list(panel_rect) if panel_rect is not None else None,
                "target_surface": "side_panel" if target_is_panel else "arena",
                "ops": target.ops,
                "buttons": {
                    key: list(value)
                    for key, value in popup.game.ui_buttons.items()
                },
            })
    return {
        "source": "ui_components/_bundle.py::BuildPopup.draw + mobile/platform_utils.py::panel_popup_pos",
        "glyph_factor": rec.GLYPH_FACTOR,
        "colors": {
            "gold": list(gold),
            "ui_gold": list(_constant(UI_THEME, "GOLD")),
            "gold_bright": list(_constant(UI_THEME, "GOLD_BRIGHT")),
            "gold_text": list(_constant(UI_THEME, "GOLD_TEXT")),
        },
        "frames": frames,
    }


def main():
    data = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    ops = sum(len(frame["ops"]) for frame in data["frames"])
    print("build popup oracle: %d frames, %d ops -> %s"
          % (len(data["frames"]), ops, FIXTURE.name))


if __name__ == "__main__":
    main()
