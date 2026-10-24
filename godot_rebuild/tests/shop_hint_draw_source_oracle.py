"""Source oracle for the floating shop hints (layer 9bv3).

`Game.draw` opens the unshaken UI pass with `self.ui.draw_shop_hints(self.screen)`, which runs
`ui_components/_bundle.py::ShopHints.draw`: two small gold pills that bob with
`pulse = int(sin(animation_time * 0.06) * 2)`.
  * ITEM FORGE over `map_renderer.radiant_shop_pos` (340, 540), centre shifted (+82, -30);
  * HERO SHOP over `map_renderer.dire_shop_pos` (940, 180), centre shifted (-82, +44).
Each label is `ui_theme.letter(label)` (one space between characters) in 14 px body_bold
`ui_theme.GOLD_TEXT`, centred on the hint point; the pill is the text rect inflated by
(16, 8), radius `h // 2`, filled with `_vgrad((48, 42, 20) -> (24, 20, 9))` when
`ui_theme.cheap_alpha()` (solid (30, 24, 10) otherwise) and edged 1 px in `ui_theme.GOLD`.
The REAL `ShopHints.draw` / `_draw_single_hint` (harvested from `_bundle.py`) and
`ui_theme.letter` run under the recording pygame shim of `draw_recorder.py` (text measured
with its fake `0.55 * size` glyphs); `ui_theme._vgrad` is recorded as one `vgrad` op.
Run: python godot_rebuild/tests/shop_hint_draw_source_oracle.py
"""
import ast
import json
import math
import textwrap
import types
from pathlib import Path
from types import SimpleNamespace

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "ui_components" / "_bundle.py"
RENDER = ROOT / "_render.py"
UI_THEME = ROOT / "ui_theme.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "shop_hint_draw_source.json"
HARVESTED = ("draw", "_draw_single_hint")
# (label, animation_time, cheap_alpha). int() truncates toward zero, so t = 60 (sin * 2 =
# -0.885) bobs 0 px, not -1.
FRAMES = [
    ("rest", 0, True),
    ("up", 13, True),
    ("truncated_zero", 60, True),
    ("down", 70, True),
    ("late", 12345, True),
    ("down_solid", 70, False),
]


def _class(path, name):
    text = path.read_text(encoding="utf-8")
    node = next((n for n in ast.walk(ast.parse(text))
                 if isinstance(n, ast.ClassDef) and n.name == name), None)
    if node is None:
        raise AssertionError("%s not found in %s" % (name, path.name))
    return text, node


def _shop_hints(namespace):
    text, owner = _class(BUNDLE, "ShopHints")
    found = {n.name: n for n in owner.body if isinstance(n, ast.FunctionDef) and n.name in HARVESTED}
    missing = set(HARVESTED) - set(found)
    if missing:
        raise AssertionError("%s not found in %s.ShopHints" % (sorted(missing), BUNDLE.name))
    body = "".join(
        textwrap.indent(textwrap.dedent(ast.get_source_segment(text, found[name], padded=True)),
                        "    ") + "\n"
        for name in HARVESTED)
    exec(compile("class ShopHints:\n%s" % body, BUNDLE.name, "exec"), namespace)
    return namespace["ShopHints"]


def _shop_positions():
    """`MapRenderer.__init__`'s `radiant_shop_pos` / `dire_shop_pos` literals."""
    _text, owner = _class(RENDER, "MapRenderer")
    found = {}
    for node in ast.walk(owner):
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Attribute):
            if node.targets[0].attr in ("radiant_shop_pos", "dire_shop_pos"):
                found[node.targets[0].attr] = ast.literal_eval(node.value)
    return found


def _constant(path, name):
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("%s not found in %s" % (name, path.name))


def _ui_theme(pygame, cheap):
    module = types.ModuleType("ui_theme")
    module.pygame = pygame
    module.GOLD = _constant(UI_THEME, "GOLD")
    module.GOLD_TEXT = _constant(UI_THEME, "GOLD_TEXT")
    module.cheap_alpha = lambda: cheap

    def vgrad(w, h, top, bottom, radius=0):
        surface = rec.Surface((w, h))
        surface.ops.append({"kind": "vgrad", "rect": [0, 0, int(w), int(h)], "top": list(top),
                            "bottom": list(bottom), "radius": int(radius), "mult": 255})
        return surface

    module._vgrad = vgrad
    for segment in rec.harvest(UI_THEME, ["letter"]):
        exec(compile(segment, UI_THEME.name, "exec"), module.__dict__)
    return module


def source_fixture():
    pygame = rec.make_pygame({"ticks": 0})
    shops = _shop_positions()
    frames = []
    with rec.installed({"pygame": pygame}):
        for label, animation_time, cheap in FRAMES:
            namespace = {"pygame": pygame, "math": math, "ui_theme": _ui_theme(pygame, cheap),
                         "get_font": lambda size, style="body", bold=False: rec.Font(size, style)}
            hints = _shop_hints(namespace)()
            hints.game = SimpleNamespace(
                animation_time=animation_time, map_renderer=SimpleNamespace(**shops))
            screen = rec.Surface((1280, 720))
            hints.draw(screen)
            frames.append({"label": label, "animation_time": animation_time,
                           "cheap_alpha": cheap, "ops": screen.ops})
    return {
        "source": "ui_components/_bundle.py::ShopHints.draw (+ ui_theme.letter)",
        "glyph_factor": rec.GLYPH_FACTOR,
        "shops": {name: list(value) for name, value in sorted(shops.items())},
        "frames": frames,
    }


def main():
    data = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    ops = sum(len(frame["ops"]) for frame in data["frames"])
    print("shop hint oracle: %d frames, %d ops -> %s" % (len(data["frames"]), ops, FIXTURE.name))


if __name__ == "__main__":
    main()
