"""Source oracle for the LevelIntroScreen port.

`import _render` fails today with a pre-existing circular import and the Python
sources are read-only, so this oracle extracts `class LevelIntroScreen`
verbatim from `_render.py` and executes it against shims. No pygame needed:
the `pygame`, `mobile.perf` and `_core` names are fakes injected through
`sys.modules`, so CI (which has no pygame) runs the exact same source code.

The interesting numbers live inside `draw()`: the fade ramp (`fade_alpha`),
the theme tint alpha, the difficulty branch (`diff_title` / `diff_level` /
`diff_color`), the per-bar colours, the starting-gold fallback and the passive
income label. Re-implementing those would make the fixture a copy of my own
guess, so `sys.settrace` reads the locals straight off the real frames, the
same technique as the WaveAnnouncer / AchievementPopup oracles.

Determinism notes:

* `Quality.cheap_alpha = True` in the shim, matching the Android path the
  source optimises for.
* `_core` is an empty fake module, so every `from _core import ...` raises
  ImportError and the source fallbacks run — on any machine, including one
  with pygame installed. Difficulty is injected by attaching a stub
  `GameSettings` to that fake module; the branch maths itself stays source.
* The passive-income fallback line reads `GOLD_PER_SECOND`, which lives in
  `_core.py` (line 215, value 3) and is fed into the exec namespace.
* Boss info comes from the real `bosses.boss_data` module, which is pure data
  and imports cleanly without pygame.

Run: python godot_rebuild/tests/level_intro_screen_source_oracle.py
"""
import json
import math
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "level_intro_screen_source.json"

TAG = "_render.py:LevelIntroScreen"

SCREEN_W = 1280
SCREEN_H = 720
STEPS = 40
IDLE_STEPS = 2

# Order of the source's if/elif chain plus one unknown theme for the
# forest fallback.
THEMES = [
    "desert", "ice", "ocean", "abyss", "nethervenom", "spectral",
    "sundered", "empyrean", "solaris", "abysstide", "crimsonmatriarch",
    "astral", "shadowchain", "frostveil", "warshade", "outlaw", "hexbound",
    "voidbound", "earthborn", "heartbane", "sunfist", "voidwing",
    "crimsondevourer", "elementweave", "tempest", "sawmill", "croweye",
    "crystalstorm", "eternalwarlord", "explosiveart", "sandshadow",
    "emberweaver", "skyfury", "forest", "mystery_theme",
]

LEVEL_CONFIG = {
    "level_number": 7,
    "name": "Ashen Crossing",
    "description": "Hold the bridge against the crimson tide.",
    "enemy_hp_mult": 1.8,
    "enemy_damage_mult": 1.35,
    "meta_gold_reward_win": 320,
    "map_theme": "ice",
    "true_boss": "abaddon",
    "starting_gold": 1600,
}


# --------------------------------------------------------------------------
# Minimal shims: everything past the captured locals is drawing we do not
# port, so the shims only have to let draw() run to completion.
# --------------------------------------------------------------------------
class _RectShim:
    x = 0
    y = 0
    width = 0
    height = 0

    @property
    def size(self):
        return (self.width, self.height)

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.width

    @property
    def top(self):
        return self.y

    @property
    def bottom(self):
        return self.y + self.height

    def __init__(self, *args, **kwargs):
        center = kwargs.get("center")
        if center is not None:
            self.x = center[0]
            self.y = center[1]

    def inflate(self, dx, dy):
        clone = _RectShim()
        clone.x = self.x
        clone.y = self.y
        clone.width = self.width + dx
        clone.height = self.height + dy
        return clone


class _SurfaceShim:
    born = []

    def __init__(self, *args, **kwargs):
        self.fills = []
        _SurfaceShim.born.append(self)

    def set_alpha(self, *args, **kwargs):
        pass

    def get_at(self, *args, **kwargs):
        return (0, 0, 0, 255)

    def get_rect(self, **kwargs):
        return _RectShim(**kwargs)

    def fill(self, color, **kwargs):
        self.fills.append(tuple(color))

    def blit(self, *args, **kwargs):
        pass


class _FontShim:
    def __init__(self, *args, **kwargs):
        pass

    def render(self, *args, **kwargs):
        return _SurfaceShim()


class _ThemeShim:
    def corner_ticks(self, *args, **kwargs):
        pass

    def draw_icon(self, *args, **kwargs):
        pass

    def letter(self, text):
        return text


POLYGONS = []


class _DrawShim:
    @staticmethod
    def rect(*args, **kwargs):
        pass

    @staticmethod
    def line(*args, **kwargs):
        pass

    @staticmethod
    def polygon(surface, color, points, *args, **kwargs):
        POLYGONS.append((tuple(color), [tuple(point) for point in points]))

    @staticmethod
    def circle(*args, **kwargs):
        pass


class _TimeShim:
    @staticmethod
    def get_ticks():
        return 0


class _PygameShim:
    SRCALPHA = 1
    BLEND_RGB_MULT = 2
    K_SPACE = 32
    K_RETURN = 13
    Surface = _SurfaceShim
    Rect = _RectShim
    draw = _DrawShim
    time = _TimeShim


class _QualityShim:
    cheap_alpha = True


class _PoolShim:
    @staticmethod
    def get(w, h):
        return _SurfaceShim()

    @staticmethod
    def release(surface):
        pass


def _install_shim_modules():
    # bosses.boss_data is pure data and imports headless; make it importable
    # regardless of the caller's cwd/sys.path.
    sys.path.insert(0, str(ROOT))
    perf = types.ModuleType("mobile.perf")
    perf.darken = lambda *args, **kwargs: None
    perf.Quality = _QualityShim
    perf.cached_render = lambda key, w, h, painter: _SurfaceShim()
    perf.POOL = _PoolShim()
    perf.blit_overlay = lambda *args, **kwargs: None
    mobile = types.ModuleType("mobile")
    mobile.perf = perf
    sys.modules["mobile"] = mobile
    sys.modules["mobile.perf"] = perf
    # Empty fake _core: every `from _core import ...` in the source must take
    # the except path regardless of what is installed on this machine.
    sys.modules["_core"] = types.ModuleType("_core")


def _set_difficulty(value):
    sys.modules["_core"].GameSettings = type(
        "GameSettings", (), {"difficulty": value})


def _clear_difficulty():
    fake = sys.modules["_core"]
    if hasattr(fake, "GameSettings"):
        del fake.GameSettings


def _slice_class(lines):
    start = next(
        i for i, line in enumerate(lines)
        if line.startswith("class LevelIntroScreen:")
    )
    end = next(
        i for i, line in enumerate(lines)
        if i > start and (line.startswith("class ") or line.startswith("import pygame"))
    )
    return "\n".join(lines[start:end]), start


def _load_class():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    block, offset = _slice_class(lines)
    namespace = {
        "math": math,
        "pygame": _PygameShim,
        "ui_theme": _ThemeShim(),
        "title_font": _FontShim,
        "get_font": _FontShim,
        "GOLD_PER_SECOND": 3,  # _core.py:215 — behind the source fallback
        "_begin_prompt_text": lambda: "PRESS SPACE TO BEGIN",
    }
    exec(compile(block, TAG, "exec"), namespace)
    return namespace, block, offset


def _line_no(block, offset, prefix):
    # compile(block, TAG, "exec") numbers lines relative to the block, so the
    # offset of the class inside _render.py must NOT be added here.
    for index, line in enumerate(block.splitlines()):
        if line.strip().startswith(prefix):
            return index + 1
    raise AssertionError("capture line not found: %s" % prefix)


# (prefix, [locals to read off the frame])
CAPTURE_SPECS = {
    "tint = pygame.Surface(": ["fade_alpha", "theme_tint_alpha"],
    "pygame.draw.line(surface, (100, 100, 130": ["divider_x"],
    "bar_start_x = cx - (5 * 22) // 2": ["cx", "diff_title", "diff_level", "diff_color"],
    "bar_surf = pygame.Surface((18, 10)": ["i", "bar_x", "bar_y", "bar_col"],
    "start_text = self.font_medium.render(": ["sg"],
    "inc_text = self.font_tiny.render(": ["inc_str"],
    "tag_surf = self.font_small.render(": ["cx", "tag_text", "tag_color"],
    "for i in range(num_spikes):": ["num_spikes"],
}


def _traced_draw(intro, key_map, sinks):
    """Run draw() once, appending captured locals into the per-line sinks."""

    def tracer(frame, event, arg):
        if event == "call":
            return tracer if frame.f_code.co_filename == TAG else None
        if event == "line" and frame.f_code.co_filename == TAG:
            keys = key_map.get(frame.f_lineno)
            if keys is not None:
                sinks[frame.f_lineno].append(
                    [frame.f_locals[key] for key in keys]
                )
        return tracer

    sys.settrace(tracer)
    try:
        intro.draw(_SurfaceShim())
    finally:
        sys.settrace(None)


def _build_key_map(block, offset, prefixes):
    key_map = {}
    for prefix in prefixes:
        key_map[_line_no(block, offset, prefix)] = list(CAPTURE_SPECS[prefix])
    return key_map


def source_fixture():
    _install_shim_modules()
    namespace, block, offset = _load_class()
    cls = namespace["LevelIntroScreen"]

    line_map = _build_key_map(block, offset, CAPTURE_SPECS)
    sinks = {lineno: [] for lineno in line_map}

    intro = cls(dict(LEVEL_CONFIG), SCREEN_W, SCREEN_H)
    info = {
        "level_num": intro.level_num,
        "level_name": intro.level_name,
        "level_desc": intro.level_desc,
        "hp_mult": intro.hp_mult,
        "dmg_mult": intro.dmg_mult,
        "reward": intro.reward,
        "map_theme": intro.map_theme,
        "boss_type": intro.boss_type,
        "boss_name": intro.boss_name,
        "boss_title": intro.boss_title,
        "boss_color": list(intro.boss_color),
        "boss_color_dark": list(intro.boss_color_dark),
        "boss_entrance_color": list(intro.boss_entrance_color),
        "boss_class": intro.boss_class,
        "fade_in_duration": intro.fade_in_duration,
    }

    # Fade ramp: update() then draw(), reading the fade locals per tick.
    steps = []
    tint_line = _line_no(block, offset, "tint = pygame.Surface(")
    for _ in range(STEPS):
        intro.update()
        sinks[tint_line].clear()
        _traced_draw(intro, {tint_line: line_map[tint_line]}, sinks)
        rows = sinks[tint_line]
        fade_alpha, tint_alpha = rows[0] if rows else [None, None]
        steps.append([1, intro.timer, fade_alpha, tint_alpha])

    returned = intro.handle_skip(_PygameShim.K_SPACE)
    check_active = intro.is_active()
    for _ in range(IDLE_STEPS):
        intro.update()
        sinks[tint_line].clear()
        _traced_draw(intro, {tint_line: line_map[tint_line]}, sinks)
        rows = sinks[tint_line]
        if rows:
            raise AssertionError("inactive intro must not draw")
        steps.append([0, intro.timer, None, None])

    # Full-brightness layout pass (timer past the fade, prompt visible).
    layout_intro = cls(dict(LEVEL_CONFIG), SCREEN_W, SCREEN_H)
    for _ in range(100):
        layout_intro.update()
    POLYGONS.clear()
    _traced_draw(layout_intro, line_map, sinks)
    # Divider diamonds: gold 4-gons centred on the divider; the recorded
    # second point is (cx + 8, y), so the centre is x - 8.
    diamonds = [
        [points[1][0] - 8, points[1][1]]
        for color, points in POLYGONS
        if color == (255, 220, 100) and len(points) == 4
    ]
    divider = sinks[_line_no(block, offset, "pygame.draw.line(surface, (100, 100, 130")][0][0]
    tag_row = sinks[_line_no(block, offset, "tag_surf = self.font_small.render(")][0]
    spikes = sinks[_line_no(block, offset, "for i in range(num_spikes):")][0][0]
    layout = {
        "divider_x": divider,
        "level_cx": sinks[_line_no(block, offset, "bar_start_x = cx - (5 * 22) // 2")][0][0],
        "boss_cx": tag_row[0],
        "tag": [tag_row[1], list(tag_row[2])],
        "crown_spikes": spikes,
        "diamonds": diamonds,
    }

    # Difficulty branches: the stub GameSettings only feeds the setting, the
    # branch maths is source. The "normal" case exercises the ImportError
    # fallback path (no GameSettings on the fake module at all).
    difficulty = {}
    for name, value in (("normal", None), ("hard", "hard"), ("easy", "easy")):
        if value is None:
            _clear_difficulty()
        else:
            _set_difficulty(value)
        run = cls(dict(LEVEL_CONFIG), SCREEN_W, SCREEN_H)
        for _ in range(100):
            run.update()
        prefix = "bar_start_x = cx - (5 * 22) // 2"
        sinks[_line_no(block, offset, prefix)].clear()
        sinks[_line_no(block, offset, "bar_surf = pygame.Surface((18, 10)")].clear()
        sinks[_line_no(block, offset, "start_text = self.font_medium.render(")].clear()
        sinks[_line_no(block, offset, "inc_text = self.font_tiny.render(")].clear()
        _traced_draw(run, line_map, sinks)
        row = sinks[_line_no(block, offset, prefix)][0]
        bars = sinks[_line_no(block, offset, "bar_surf = pygame.Surface((18, 10)")]
        difficulty[name] = {
            "title": row[1],
            "level": row[2],
            "color": list(row[3]),
            "bars": [[b[0], b[1], b[2], list(b[3])] for b in bars],
            "starting_gold": sinks[_line_no(block, offset, "start_text = self.font_medium.render(")][0][0],
            "income": sinks[_line_no(block, offset, "inc_text = self.font_tiny.render(")][0][0],
        }
    _clear_difficulty()

    # Theme tint colours: the fill colour of the first surface born during a
    # full-brightness draw is the theme tint (r, g, b, tint_alpha).
    themes = {}
    for theme in THEMES:
        themed_config = dict(LEVEL_CONFIG)
        themed_config["map_theme"] = theme
        themed = cls(themed_config, SCREEN_W, SCREEN_H)
        for _ in range(100):
            themed.update()
        _SurfaceShim.born = []
        themed.draw(_SurfaceShim())
        tint = None
        for surface in _SurfaceShim.born:
            for fill in surface.fills:
                if len(fill) == 4 and fill[3] == 30:
                    tint = list(fill)
                    break
            if tint:
                break
        if tint is None:
            raise AssertionError("no tint fill captured for %s" % theme)
        themes[theme] = tint

    # Skip matrix: spacebar, enter, other key, click, wrong-key no-op and the
    # inactive guard.
    skip = []

    def probe(label, key, click):
        item = cls(dict(LEVEL_CONFIG), SCREEN_W, SCREEN_H)
        result = item.handle_skip(key, click=click)
        skip.append([label, result, item.is_active()])

    probe("space", _PygameShim.K_SPACE, False)
    probe("return", _PygameShim.K_RETURN, False)
    probe("other_key", 999, False)
    probe("click", None, True)
    probe("no_args", None, False)

    guarded = cls(dict(LEVEL_CONFIG), SCREEN_W, SCREEN_H)
    guarded.handle_skip(_PygameShim.K_SPACE)
    skip.append(["inactive_guard", guarded.handle_skip(_PygameShim.K_SPACE), guarded.is_active()])
    skip.append(["returned_by_main_skip", returned, check_active])

    return {
        "source": "_render.py::LevelIntroScreen",
        "screen_w": SCREEN_W,
        "screen_h": SCREEN_H,
        "level_config": LEVEL_CONFIG,
        "info": info,
        "steps": steps,
        "layout": layout,
        "difficulty": difficulty,
        "themes": themes,
        "skip": skip,
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    live = [step for step in fixture["steps"] if step[1] is not None and step[2] is not None]
    print("level_intro_screen: %d steps, %d live, %d themes, %d skip probes"
          % (len(fixture["steps"]), len(live), len(fixture["themes"]), len(fixture["skip"])))
    print("  first live: %s" % (live[0],))
    print("  last live:  %s" % (live[-1],))
    print("  hard: %s" % (fixture["difficulty"]["hard"],))
    print("wrote %s" % FIXTURE.relative_to(ROOT))


if __name__ == "__main__":
    main()
