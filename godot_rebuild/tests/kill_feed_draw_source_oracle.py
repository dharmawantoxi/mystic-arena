"""Source oracle for the `KillFeed.draw()` visuals (layer 9bb).

`_render.py::KillFeed` already has its state ported (`scripts/ui/kill_feed.gd`,
`kill_feed_source_oracle.py`); this oracle pins the DRAW itself: the per-entry
fade-in / hold / fade-out alpha, the 100 px slide-in from the right edge, the
`inflate(12, 4)` black backing box at half alpha, the 1 px rounded team-colour
border at half alpha and the right-aligned text blitted with the full alpha.

The REAL class is harvested from `_render.py` with `ast` and `draw()` runs under
a recording pygame shim (fonts: int(size * 0.55) px per glyph, height = size).
Entry state comes from the real `add_kill` / `update`, so lifetimes and the
eased `y_offset` are the source's. Every blit is flattened into screen
coordinates with its surface alpha multiplier so
`scripts/ui/kill_feed_layout.gd` can emit the same op list.

Run: python godot_rebuild/tests/kill_feed_draw_source_oracle.py
"""
import ast
import json
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "kill_feed_draw_source.json"
W, H = 1280, 720
GLYPH_FACTOR = 0.55

# (label, kills as (tick, killer, victim, team), ticks sampled after update(),
# ticks sampled right after add_kill() but BEFORE update()).
SCENARIOS = [
    ("single_blue", [(0, "Kaizen", "Grimjaw", "blue")],
     [1, 7, 13, 14, 90, 133, 134, 135, 150, 170, 178, 179], [0]),
    ("single_red", [(0, "Zephyr", "Kaizen", "red")], [3, 10, 100, 160], []),
    ("stack_six", [(0, "Kaizen", "Grimjaw", "blue"), (3, "Thorne", "Vex", "red"),
                   (6, "Sylara", "Zephyr", "blue"), (9, "Grimjaw", "Sylara", "red"),
                   (12, "Vex", "Thorne", "blue"), (15, "Zephyr", "Kaizen", "red")],
     [2, 14, 16, 20, 40, 100, 140, 150, 170, 190], []),
    ("pending_kill", [(0, "Kaizen", "Grimjaw", "blue"), (100, "Thorne", "Vex", "red")],
     [101, 110], [100]),
    ("long_names", [(0, "Sylara the Everlasting", "Abaddon Lord of the Pit", "red")],
     [60], []),
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
    size = property(lambda s: (s.w, s.h))

    def inflate(self, dx, dy):
        # pygame keeps the centre: the origin moves by half the growth.
        return Rect(self.x - dx // 2, self.y - dy // 2, self.w + dx, self.h + dy)

    def __iter__(self):
        return iter((self.x, self.y, self.w, self.h))


class Surface:
    def __init__(self, size, *_args, **_kwargs):
        self.w, self.h = int(size[0]), int(size[1])
        self.ops = []
        self.alpha = 255

    def set_alpha(self, value):
        self.alpha = int(value)

    def fill(self, color):
        self.ops.append({"kind": "fill", "rect": [0, 0, self.w, self.h],
                         "color": _rgba(color), "mult": 255})

    def get_rect(self, **anchors):
        right, top = anchors["topright"]
        return Rect(int(right) - self.w, int(top), self.w, self.h)

    def blit(self, src, dest, *_args, **_kwargs):
        dx, dy = (dest.x, dest.y) if isinstance(dest, Rect) else (int(dest[0]), int(dest[1]))
        if isinstance(src, Text):
            self.ops.append({"kind": "text", "text": src.text, "size": src.font_size,
                             "style": src.style, "color": _rgba(src.color),
                             "mult": src.alpha, "pos": [dx, dy], "w": src.w, "h": src.h})
            return
        for op in src.ops:
            moved = dict(op)
            moved["mult"] = int(op["mult"] * src.alpha / 255)
            moved["rect"] = [op["rect"][0] + dx, op["rect"][1] + dy,
                             op["rect"][2], op["rect"][3]]
            self.ops.append(moved)


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
        surface.ops.append({"kind": "rect", "rect": list(Rect(rect)), "color": _rgba(color),
                            "mult": 255, "width": int(width), "radius": int(border_radius)})


def _harvest(name):
    text = SOURCE.read_text(encoding="utf-8")
    for node in ast.parse(text).body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return ast.get_source_segment(text, node)
    raise AssertionError("class %s not found in _render.py" % name)


def _load_class():
    pygame = types.SimpleNamespace(Surface=Surface, Rect=Rect, draw=Draw, SRCALPHA=65536)
    namespace = {
        "pygame": pygame,
        "get_font": lambda size, style="body", bold=False: Font(size, style),
    }
    exec(compile(_harvest("KillFeed"), "_render.py:KillFeed", "exec"), namespace)
    return namespace["KillFeed"]


def _entry_state(entry):
    return {
        "text": str(entry["text"]),
        "color": [int(channel) for channel in entry["color"]],
        "lifetime": int(entry["lifetime"]),
        "max_lifetime": int(entry["max_lifetime"]),
        "y_offset": float(entry["y_offset"]),
        "target_y": float(entry["target_y"]),
    }


def _frame(feed, label, tick, phase):
    screen = Surface((W, H))
    feed.draw(screen, W, H)
    return {"label": label, "tick": tick, "phase": phase,
            "entries": [_entry_state(entry) for entry in feed.entries],
            "ops": screen.ops}


def source_fixture():
    cls = _load_class()
    frames = []
    for label, kills, after_ticks, before_ticks in SCENARIOS:
        feed = cls()
        for tick in range(max(after_ticks + before_ticks) + 1):
            for kill_tick, killer, victim, team in kills:
                if kill_tick == tick:
                    feed.add_kill(killer, victim, team)
            if tick in before_ticks:
                frames.append(_frame(feed, label, tick, "pre"))
            feed.update()
            if tick in after_ticks:
                frames.append(_frame(feed, label, tick, "post"))
    return {
        "source": "_render.py::KillFeed.draw",
        "screen": [W, H],
        "glyph_factor": GLYPH_FACTOR,
        "scenarios": [
            {"label": label, "kills": [list(kill) for kill in kills],
             "after": list(after_ticks), "before": list(before_ticks)}
            for label, kills, after_ticks, before_ticks in SCENARIOS
        ],
        "frames": frames,
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, separators=(",", ":")) + "\n", encoding="utf-8")
    drawn = sum(len(frame["ops"]) for frame in fixture["frames"])
    print("wrote %s (%d frames, %d ops)" % (FIXTURE.relative_to(ROOT), len(fixture["frames"]), drawn))


if __name__ == "__main__":
    main()
