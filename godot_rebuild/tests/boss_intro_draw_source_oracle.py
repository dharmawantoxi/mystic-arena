"""Source oracle for the `BossIntroCinematic.draw()` visuals (layer 9bd).

`_render.py::BossIntroCinematic` already has its state ported
(`scripts/ui/boss_intro_cinematic.gd`, `boss_intro_cinematic_source_oracle.py`);
this oracle pins the DRAW itself: the 600x92 rounded banner (dark fill at
`210 * alpha / 255`, 2 px `entrance_color` border), the gold corner ticks that
only appear above alpha 60, the tag / name / quoted title text blitted with the
fade alpha, and the 150x12 rounded HP bar. The HP bar is drawn straight onto
the screen, so unlike the banner it does NOT fade: it shows at full strength
from the first frame to the last. That source quirk is pinned on purpose.

The REAL class is harvested from `_render.py` with `ast` and `draw()` runs under
a recording pygame shim. `ui_theme.corner_ticks` is harvested from `ui_theme.py`
too, so the eight tick lines are the source's own. State comes from the real
`update()` (its `_system` sound import is swallowed, so a stub `_system` without
`SoundManager` is installed while the oracle runs and restored afterwards).
Bosses are real `bosses/boss_data.py` entries (pure data, loaded by file path).
Text is recorded as (text, size, style, colour, surface alpha, top-left) only:
the draw never measures a font, so no metrics leak into the fixture.

Run: python godot_rebuild/tests/boss_intro_draw_source_oracle.py
"""
import ast
import importlib.util
import json
import math
import sys
import types
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
UI_THEME = ROOT / "ui_theme.py"
BOSS_DATA = ROOT / "bosses" / "boss_data.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "boss_intro_draw_source.json"

# (label, boss key, screen width, screen height, drawn after this many update()
# calls). Ticks: 0 = before the first update (alpha 0); 2-3 and 95-96 straddle
# the alpha > 60 corner tick threshold; 12 = fully faded in, 18 = slide done,
# 81 = first fade-out tick, 85+ = HP bar full, 100 = timer 0 so nothing draws.
SCENARIOS = [
    ("true_boss", "abaddon", 1280, 720,
     [0, 1, 2, 3, 4, 8, 12, 18, 40, 70, 81, 90, 95, 96, 99, 100]),
    ("mini_boss", "drakar", 1280, 720, [1, 18, 50, 99]),
    # min(600, screen_w - 40) clamps the banner on a narrow screen.
    ("narrow", "abaddon", 480, 720, [18, 50]),
]


def _rgba(color):
    values = [int(channel) for channel in color]
    return values if len(values) == 4 else values + [255]


class Rect:
    def __init__(self, x, y=None, w=None, h=None):
        if y is None:
            x, y, w, h = x
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)

    width = property(lambda s: s.w)
    height = property(lambda s: s.h)
    right = property(lambda s: s.x + s.w)
    bottom = property(lambda s: s.y + s.h)

    def __iter__(self):
        return iter((self.x, self.y, self.w, self.h))


class Surface:
    def __init__(self, size, *_args, **_kwargs):
        self.w, self.h = int(size[0]), int(size[1])
        self.ops = []
        self.alpha = 255

    def set_alpha(self, value):
        self.alpha = int(value)

    def blit(self, src, dest, *_args, **_kwargs):
        dx, dy = (dest.x, dest.y) if isinstance(dest, Rect) else (int(dest[0]), int(dest[1]))
        if isinstance(src, Text):
            self.ops.append({"kind": "text", "text": src.text, "size": src.font_size,
                             "style": src.style, "color": _rgba(src.color),
                             "mult": src.alpha, "pos": [dx, dy]})
            return
        for op in src.ops:
            moved = dict(op)
            moved["mult"] = int(op["mult"] * src.alpha / 255)
            moved["rect"] = [op["rect"][0] + dx, op["rect"][1] + dy, op["rect"][2], op["rect"][3]]
            self.ops.append(moved)


class Text(Surface):
    def __init__(self, text, font_size, style, color):
        super().__init__((len(text), font_size))
        self.text, self.font_size, self.style, self.color = text, font_size, style, color


class Font:
    def __init__(self, font_size, style):
        self.font_size, self.style = font_size, style

    def render(self, text, _antialias, color):
        return Text(text, self.font_size, self.style, color)


class Draw:
    @staticmethod
    def rect(surface, color, rect, width=0, border_radius=0, **_kwargs):
        surface.ops.append({"kind": "rect", "rect": list(Rect(rect)), "color": _rgba(color),
                            "mult": 255, "width": int(width), "radius": int(border_radius)})

    @staticmethod
    def line(surface, color, start, end, width=1):
        surface.ops.append({"kind": "line", "a": [int(start[0]), int(start[1])],
                            "b": [int(end[0]), int(end[1])], "color": _rgba(color),
                            "mult": 255, "width": int(width)})


def _harvest(path, name, kind):
    text = path.read_text(encoding="utf-8")
    for node in ast.parse(text).body:
        if isinstance(node, kind) and node.name == name:
            return ast.get_source_segment(text, node)
    raise AssertionError("%s not found in %s" % (name, path.name))


def _load_class():
    pygame = SimpleNamespace(Surface=Surface, Rect=Rect, draw=Draw, SRCALPHA=65536)
    theme_ns = {"pygame": pygame}
    exec(compile(_harvest(UI_THEME, "corner_ticks", ast.FunctionDef), "ui_theme.py:corner_ticks",
                 "exec"), theme_ns)
    namespace = {
        "math": math,
        "pygame": pygame,
        "ui_theme": SimpleNamespace(corner_ticks=theme_ns["corner_ticks"]),
        "title_font": lambda size: Font(size, "title"),
        "get_font": lambda size, style="body", bold=False: Font(size, style),
    }
    exec(compile(_harvest(SOURCE, "BossIntroCinematic", ast.ClassDef),
                 "_render.py:BossIntroCinematic", "exec"), namespace)
    return namespace["BossIntroCinematic"]


def _load_bosses():
    spec = importlib.util.spec_from_file_location("boss_data", BOSS_DATA)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.get_all_boss_types()


def _snapshot(boss):
    return {
        "name": boss["name"], "title": boss["title"], "boss_class": boss["boss_class"],
        "color": list(boss["color"]), "color_dark": list(boss["color_dark"]),
        "entrance_color": list(boss["entrance_color"]),
    }


def _boss_object(snapshot):
    """Stand-in for the live Boss: exactly the attributes the class reads."""
    return SimpleNamespace(
        name=snapshot["name"], title=snapshot["title"], boss_class=snapshot["boss_class"],
        color=tuple(snapshot["color"]), color_dark=tuple(snapshot["color_dark"]),
        entrance_color=tuple(snapshot["entrance_color"]))


def _frame(cinematic, label, tick, width, height):
    screen = Surface((width, height))
    cinematic.draw(screen)
    return {
        "label": label, "tick": tick,
        "state": {"active": bool(cinematic.is_active()), "timer": int(cinematic.timer)},
        "ops": screen.ops,
    }


def source_fixture():
    saved = sys.modules.get("_system")
    sys.modules["_system"] = types.ModuleType("_system")
    try:
        cls = _load_class()
        bosses = _load_bosses()
        scenarios, frames, duration = [], [], 0
        for label, key, width, height, ticks in SCENARIOS:
            snapshot = _snapshot(bosses[key])
            cinematic = cls(_boss_object(snapshot), width, height)
            duration = int(cinematic.duration)
            for tick in range(max(ticks) + 1):
                if tick in ticks:
                    frames.append(_frame(cinematic, label, tick, width, height))
                cinematic.update()
            scenarios.append({"label": label, "boss": snapshot, "screen": [width, height],
                              "ticks": list(ticks)})
        return {
            "source": "_render.py::BossIntroCinematic.draw",
            "duration": duration,
            "scenarios": scenarios,
            "frames": frames,
        }
    finally:
        if saved is None:
            sys.modules.pop("_system", None)
        else:
            sys.modules["_system"] = saved


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, separators=(",", ":")) + "\n", encoding="utf-8")
    drawn = sum(len(frame["ops"]) for frame in fixture["frames"])
    print("wrote %s (%d frames, %d ops)" % (FIXTURE.relative_to(ROOT), len(fixture["frames"]), drawn))


if __name__ == "__main__":
    main()
