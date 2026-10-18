"""Source oracle for the `ComboCounter.draw()` visuals (layer 9bc).

`_render.py::ComboCounter` already has its state ported
(`scripts/ui/combo_counter.gd`, `combo_counter_source_oracle.py`); this oracle
pins the DRAW itself: the `x{count}` text centred at (screen_w - 100, 100) at
`int(48 * display_scale)` px with its shadow, the tier label above it from five
kills on, the white flash lerp, and the 80x4 timer bar under it from two kills
on. Two source quirks are pinned on purpose: a single kill already draws `x1`
(the guard only checks `display_scale`), and the fade-out after the window
expires keeps drawing `x0` until the scale drops below 8 px.

The REAL class is harvested from `_render.py` with `ast` and `draw()` runs under
a recording pygame shim (fonts: int(size * 0.55) px per glyph, height = size).
The state (`count`, `timer`, `display_scale`, `color_flash`) comes from the real
`add_kill` / `update`. `draw()` imports `mobile.perf.Quality` at call time, so a
stub `mobile.perf` is installed while the oracle runs (`cheap_alpha` True draws
the 8-way shadow, False the single (2, 2) one) and there is deliberately no
`mobile.sidepanel`: `add_kill()` swallows that ImportError, exactly as in game
without the Python-only side panel. Every blit is flattened into screen
coordinates so `scripts/ui/combo_counter_layout.gd` can emit the same op list.

Run: python godot_rebuild/tests/combo_counter_draw_source_oracle.py
"""
import ast
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "combo_counter_draw_source.json"
W, H = 1280, 720
GLYPH_FACTOR = 0.55

# (label, tick of each add_kill() - applied at the start of that tick, before its
# update(); a repeated tick is a multi-kill in one frame -, ticks sampled right
# after add_kill() but BEFORE update() (full flash), ticks sampled after
# update(), ticks repeated with cheap_alpha False (the single (2, 2) shadow)).
SCENARIOS = [
    # Every second tick for 22 kills so the combo crosses every tier boundary.
    # 0-1: x1 pop with no bar; 2-7: COMBO tier; 8-17 / 18-27 / 28-37 / 38+: the
    # four labelled tiers (boundaries in pairs); 70-160: held window with a
    # draining bar; 161+: expiry and the x0 fade-out.
    ("climb", [2 * index for index in range(22)], [0, 8, 18],
     [0, 1, 2, 3, 7, 8, 9, 17, 18, 19, 27, 28, 29, 37, 38, 39, 43, 70, 100, 160]
     + list(range(161, 182)), [2, 8, 38, 165]),
    # Two kills in the same frame: before update() the scale is still 0, so the
    # source draws the timer bar and then skips the (sub 8 px) count text.
    ("double_kill", [0, 0], [0], [0, 1], [0]),
]


def _rgba(color):
    values = [int(channel) for channel in color]
    return values if len(values) == 4 else values + [255]


class Rect:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)


class Surface:
    def __init__(self, size=(0, 0)):
        self.w, self.h = int(size[0]), int(size[1])
        self.ops = []

    def get_rect(self, **anchors):
        # pygame centres with integer halves: x = cx - w // 2, y = cy - h // 2.
        cx, cy = anchors["center"]
        return Rect(int(cx) - self.w // 2, int(cy) - self.h // 2, self.w, self.h)

    def blit(self, src, dest, *_args, **_kwargs):
        dx, dy = (dest.x, dest.y) if isinstance(dest, Rect) else (int(dest[0]), int(dest[1]))
        self.ops.append({"kind": "text", "text": src.text, "size": src.font_size,
                         "style": src.style, "color": _rgba(src.color), "mult": 255,
                         "pos": [dx, dy], "w": src.w, "h": src.h})


class Text(Surface):
    def __init__(self, text, font_size, style, color):
        super().__init__((int(font_size * GLYPH_FACTOR) * len(text), font_size))
        self.text, self.font_size, self.style, self.color = text, font_size, style, color


class Font:
    def __init__(self, font_size, style):
        self.font_size, self.style = font_size, style

    def render(self, text, _antialias, color):
        return Text(text, self.font_size, self.style, color)


class Draw:
    @staticmethod
    def rect(surface, color, rect, width=0, border_radius=0, **_kwargs):
        x, y, w, h = [int(value) for value in rect]
        surface.ops.append({"kind": "rect", "rect": [x, y, w, h], "color": _rgba(color),
                            "mult": 255, "width": int(width), "radius": int(border_radius)})


class Quality:
    cheap_alpha = True


def _harvest(name):
    text = SOURCE.read_text(encoding="utf-8")
    for node in ast.parse(text).body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return ast.get_source_segment(text, node)
    raise AssertionError("class %s not found in _render.py" % name)


def _load_class():
    pygame = types.SimpleNamespace(Surface=Surface, Rect=Rect, draw=Draw)
    mobile = types.ModuleType("mobile")
    perf = types.ModuleType("mobile.perf")
    perf.Quality = Quality
    mobile.perf = perf
    sys.modules["mobile"], sys.modules["mobile.perf"] = mobile, perf
    namespace = {
        "pygame": pygame,
        "get_font": lambda size, style="body", bold=False: Font(size, style),
    }
    exec(compile(_harvest("ComboCounter"), "_render.py:ComboCounter", "exec"), namespace)
    return namespace["ComboCounter"]


def _frame(counter, label, tick, phase, cheap_alpha):
    Quality.cheap_alpha = cheap_alpha
    screen = Surface((W, H))
    counter.draw(screen, W, H)
    return {
        "label": label, "tick": tick, "phase": phase, "cheap_alpha": cheap_alpha,
        "state": {
            "count": int(counter.count), "timer": int(counter.timer),
            "max_timer": int(counter.max_timer),
            "display_scale": float(counter.display_scale),
            "color_flash": int(counter.color_flash),
        },
        "ops": screen.ops,
    }


def source_fixture():
    saved = {name: sys.modules.get(name) for name in ("mobile", "mobile.perf")}
    try:
        cls = _load_class()
        frames = []
        for label, kills, pre_ticks, post_ticks, single_ticks in SCENARIOS:
            counter = cls()
            for tick in range(max(post_ticks) + 1):
                for kill_tick in kills:
                    if kill_tick == tick:
                        counter.add_kill()
                if tick in pre_ticks:
                    frames.append(_frame(counter, label, tick, "pre", True))
                counter.update()
                if tick in post_ticks:
                    frames.append(_frame(counter, label, tick, "post", True))
                if tick in single_ticks:
                    frames.append(_frame(counter, label, tick, "post", False))
        return {
            "source": "_render.py::ComboCounter.draw",
            "screen": [W, H],
            "glyph_factor": GLYPH_FACTOR,
            "max_timer": int(counter.max_timer),
            "scenarios": [
                {"label": label, "kills": list(kills), "pre": list(pre_ticks),
                 "post": list(post_ticks), "single_shadow": list(single_ticks)}
                for label, kills, pre_ticks, post_ticks, single_ticks in SCENARIOS
            ],
            "frames": frames,
        }
    finally:
        Quality.cheap_alpha = True
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, separators=(",", ":")) + "\n", encoding="utf-8")
    drawn = sum(len(frame["ops"]) for frame in fixture["frames"])
    print("wrote %s (%d frames, %d ops)" % (FIXTURE.relative_to(ROOT), len(fixture["frames"]), drawn))


if __name__ == "__main__":
    main()
