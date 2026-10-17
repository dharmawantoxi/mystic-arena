"""Source oracle for the `LevelIntroScreen.draw()` visuals (layer 9av).

`_render.py::LevelIntroScreen` already has its state/getters ported
(`scripts/ui/level_intro_screen.gd`); this oracle pins the DRAW itself: the
split-screen layout (darken + theme tint + vignette + divider diamonds), the
left level column (LEVEL label, 200 px number with 6 shadow layers, rules,
name/desc, difficulty bars, reward/starting-gold coins, passive line), the
right boss column (FINAL BOSS, tag pill, pulsing aura rings, 12 rays, body /
inner / spike polygons, glowing eyes, name shadows, title, PREPARE FOR BATTLE
with warn icons) and the pulsing PRESS SPACE prompt with arrows.

The REAL class is harvested from `_render.py` with `ast` and run under a
recording pygame shim (fonts: int(size*0.55) px per glyph, height = size;
`mobile.perf.Quality.cheap_alpha = True`, the mobile/full path), with the
real `ui_theme.letter/corner_ticks/draw_icon` helpers. Every draw call is
flattened into screen coordinates with its surface alpha multiplier, so
`scripts/ui/level_intro_layout.gd` can emit the same op list.

Run: python godot_rebuild/tests/level_intro_draw_source_oracle.py
"""
import ast
import json
import math
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "level_intro_draw_source.json"
W, H = 1280, 720
TICKS = {"value": 0}
DIFFICULTY = {"value": "normal"}
BOSSES = {
    "abaddon": {"name": "ABADDON", "title": "Lord of the Pit", "color": (170, 40, 60),
                "color_dark": (85, 20, 30), "entrance_color": (255, 90, 90),
                "boss_class": "true"},
    "gnarl": {"name": "GNARL", "title": "Rootbound Warden", "color": (90, 140, 70),
              "color_dark": (45, 70, 35), "entrance_color": (150, 220, 110),
              "boss_class": "mini"},
}
LEVELS = [
    {"level_number": 7, "name": "Ashen Hollow", "description": "Cinders drift over the dunes",
     "enemy_hp_mult": 1.2, "enemy_damage_mult": 1.1, "meta_gold_reward_win": 750,
     "map_theme": "desert", "true_boss": "abaddon", "starting_gold": 1500},
    {"level_number": 12, "name": "Thornwood", "description": "The roots remember",
     "enemy_hp_mult": 1.6, "enemy_damage_mult": 1.3, "meta_gold_reward_win": 1200,
     "map_theme": "mystery", "true_boss": "gnarl", "starting_gold": 2250},
]
FRAMES = [
    ("desert_true", 0, 0, 0, "normal"),
    ("desert_true", 0, 15, 0, "normal"),
    ("desert_true", 0, 45, 0, "normal"),
    ("desert_true", 0, 45, 3141, "normal"),
    ("forest_mini_hard", 1, 15, 777, "hard"),
    ("forest_mini_hard", 1, 60, 3141, "hard"),
    ("forest_mini_easy", 1, 31, 250, "easy"),
]


def _rgba(color):
    color = tuple(int(c) if float(c).is_integer() else float(c) for c in color)
    return list(color) if len(color) == 4 else list(color) + [255]


def _num(value):
    value = float(value)
    return int(value) if value.is_integer() else value


class Rect:
    def __init__(self, x, y=None, w=None, h=None):
        if y is None:
            x, y, w, h = x
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)

    width = property(lambda s: s.w)
    height = property(lambda s: s.h)
    left = property(lambda s: s.x)
    right = property(lambda s: s.x + s.w)
    bottom = property(lambda s: s.y + s.h)
    size = property(lambda s: (s.w, s.h))

    def inflate(self, dx, dy):
        return Rect(self.x - dx // 2, self.y - dy // 2, self.w + dx, self.h + dy)

    def __iter__(self):
        return iter((self.x, self.y, self.w, self.h))


class Surface:
    def __init__(self, size, *_a, **_k):
        self.w, self.h = int(size[0]), int(size[1])
        self.ops = []
        self.alpha = 255

    def get_size(self):
        return (self.w, self.h)

    def get_width(self):
        return self.w

    def get_height(self):
        return self.h

    def set_alpha(self, value):
        self.alpha = int(value)

    def get_at(self, _pos):
        return (0, 0, 0, 0)

    def fill(self, color, rect=None, special_flags=0):
        box = [0, 0, self.w, self.h] if rect is None else list(Rect(rect))
        self.ops.append({"kind": "fill", "rect": box, "color": _rgba(color),
                         "mult": 255, "blend": int(special_flags)})

    def get_rect(self, **anchors):
        x, y = 0, 0
        if "center" in anchors:
            x = int(anchors["center"][0]) - self.w // 2
            y = int(anchors["center"][1]) - self.h // 2
        return Rect(x, y, self.w, self.h)

    def blit(self, src, dest, *_a, **_k):
        dx, dy = (dest.x, dest.y) if isinstance(dest, Rect) else (int(dest[0]), int(dest[1]))
        if isinstance(src, Text):
            self.ops.append({"kind": "text", "text": src.text, "size": src.size,
                             "color": _rgba(src.color), "mult": src.alpha,
                             "pos": [dx, dy], "w": src.w, "h": src.h})
            return
        for op in src.ops:
            moved = dict(op)
            moved["mult"] = int(op["mult"] * src.alpha / 255)
            if "rect" in op:
                moved["rect"] = [op["rect"][0] + dx, op["rect"][1] + dy, op["rect"][2], op["rect"][3]]
            if "center" in op:
                moved["center"] = [_num(op["center"][0] + dx), _num(op["center"][1] + dy)]
            if "a" in op:
                moved["a"] = [_num(op["a"][0] + dx), _num(op["a"][1] + dy)]
                moved["b"] = [_num(op["b"][0] + dx), _num(op["b"][1] + dy)]
            if "points" in op:
                moved["points"] = [[_num(p[0] + dx), _num(p[1] + dy)] for p in op["points"]]
            if "pos" in op:
                moved["pos"] = [op["pos"][0] + dx, op["pos"][1] + dy]
            self.ops.append(moved)


class Text(Surface):
    def __init__(self, text, size, color):
        super().__init__((int(size * 0.55) * len(text), size))
        self.text, self.size, self.color = text, size, color


class Font:
    def __init__(self, size):
        self.size = size

    def render(self, text, _aa, color):
        return Text(text, self.size, color)


class Draw:
    @staticmethod
    def rect(surface, color, rect, width=0, border_radius=0, **_k):
        surface.ops.append({"kind": "rect", "rect": list(Rect(rect)), "color": _rgba(color),
                            "mult": 255, "width": int(width), "radius": int(border_radius)})

    @staticmethod
    def circle(surface, color, center, radius, width=0, **_k):
        surface.ops.append({"kind": "circle", "center": [_num(center[0]), _num(center[1])],
                            "radius": _num(radius), "color": _rgba(color), "mult": 255,
                            "width": int(width)})

    @staticmethod
    def line(surface, color, a, b, width=1):
        surface.ops.append({"kind": "line", "a": [_num(a[0]), _num(a[1])],
                            "b": [_num(b[0]), _num(b[1])], "color": _rgba(color),
                            "mult": 255, "width": int(width)})

    @staticmethod
    def polygon(surface, color, points, width=0):
        surface.ops.append({"kind": "polygon", "points": [[_num(p[0]), _num(p[1])] for p in points],
                            "color": _rgba(color), "mult": 255, "width": int(width)})


def _pygame():
    pg = types.ModuleType("pygame")
    pg.Surface, pg.Rect, pg.draw = Surface, Rect, Draw
    pg.SRCALPHA, pg.BLEND_RGB_MULT, pg.K_SPACE, pg.K_RETURN = 65536, 1, 32, 13
    pg.time = types.SimpleNamespace(get_ticks=lambda: TICKS["value"])
    return pg


def _perf():
    perf = types.ModuleType("mobile.perf")

    def darken(target, alpha):
        a = max(0, min(255, int(alpha)))
        if a > 0:
            target.ops.append({"kind": "darken", "alpha": a, "mult": 255})

    class Quality:
        cheap_alpha = True

    class Pool:
        @staticmethod
        def get(w, h):
            return Surface((w, h))

        @staticmethod
        def release(_s):
            pass

    def cached_render(_key, w, h, painter):
        surf = Surface((w, h))
        painter(surf)
        return surf

    def blit_overlay(dst, overlay, rect=None, pos=(0, 0)):
        dst.blit(overlay, pos)

    perf.darken, perf.Quality, perf.POOL = darken, Quality, Pool
    perf.cached_render, perf.blit_overlay = cached_render, blit_overlay
    return perf


def _harvest(path, names, kind=(ast.FunctionDef, ast.ClassDef)):
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    return [ast.get_source_segment(text, node) for node in tree.body
            if isinstance(node, kind) and getattr(node, "name", None) in names]


def build():
    pg = _pygame()
    sys.modules["pygame"] = pg
    mobile = types.ModuleType("mobile")
    perf = _perf()
    plat = types.ModuleType("mobile.platform_utils")
    plat.TOUCH_MODE = False
    mobile.perf, mobile.platform_utils = perf, plat
    sys.modules["mobile"], sys.modules["mobile.perf"] = mobile, perf
    sys.modules["mobile.platform_utils"] = plat
    core = types.ModuleType("_core")
    core.GameSettings = lambda: types.SimpleNamespace(difficulty=DIFFICULTY["value"])
    core.compute_starting_gold = lambda cfg, _n, _d: cfg["starting_gold"]
    core.compute_gold_per_second = lambda _n, _d: 3
    core.format_gold_rate = lambda rate: str(rate)
    sys.modules["_core"] = core
    bosses = types.ModuleType("bosses")
    boss_data = types.ModuleType("bosses.boss_data")
    boss_data.get_all_boss_types = lambda: BOSSES
    bosses.boss_data = boss_data
    sys.modules["bosses"], sys.modules["bosses.boss_data"] = bosses, boss_data
    theme_ns = {"pygame": pg, "math": math}
    for seg in _harvest(ROOT / "ui_theme.py", {"letter", "corner_ticks", "draw_icon"}):
        exec(seg, theme_ns)
    ui_theme = types.SimpleNamespace(**theme_ns)
    ns = {"pygame": pg, "math": math, "ui_theme": ui_theme, "GOLD_PER_SECOND": 3,
          "title_font": Font, "get_font": lambda size, _style="body": Font(size)}
    for seg in _harvest(ROOT / "_render.py", {"LevelIntroScreen", "_begin_prompt_text"}):
        exec(seg, ns)
    return ns["LevelIntroScreen"]


def _state(intro, difficulty):
    return {
        "level_num": intro.level_num, "level_name": intro.level_name,
        "level_desc": intro.level_desc, "map_theme": intro.map_theme,
        "boss_name": intro.boss_name, "boss_title": intro.boss_title,
        "boss_class": intro.boss_class,
        "boss_entrance_color": list(intro.boss_entrance_color),
        "boss_color_dark": list(intro.boss_color_dark),
        "reward_text": f"+{intro.reward} HERO GOLD",
        "starting_gold_text": f"{intro.level_config['starting_gold']:,} GOLD",
        "passive_text": "PASSIVE +3/s", "prompt_text": "PRESS SPACE TO BEGIN",
        "difficulty_id": difficulty, "hp_mult": intro.hp_mult,
    }


def source_fixture():
    saved = dict(sys.modules)
    try:
        cls = build()
        frames = []
        for label, level_idx, timer, ticks, difficulty in FRAMES:
            DIFFICULTY["value"] = difficulty
            TICKS["value"] = ticks
            intro = cls(LEVELS[level_idx], W, H)
            intro.timer = timer
            screen = Surface((W, H))
            intro.draw(screen)
            frames.append({"label": label, "timer": timer, "ticks": ticks,
                           "state": _state(intro, difficulty), "ops": screen.ops})
        return {"screen": [W, H], "glyph_factor": 0.55, "levels": LEVELS,
                "bosses": {k: {kk: list(v) if isinstance(v, tuple) else v for kk, v in b.items()}
                           for k, b in BOSSES.items()},
                "frames": frames}
    finally:
        sys.modules.clear()
        sys.modules.update(saved)


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, separators=(",", ":")) + "\n", encoding="utf-8")
    print("wrote", FIXTURE, sum(len(f["ops"]) for f in fixture["frames"]), "ops")


if __name__ == "__main__":
    main()
