"""Source oracle for the LevelIntroScreen port.

`import _render` fails with a pre-existing circular import and the Python
sources are read-only, so this oracle extracts two blocks verbatim from
`_render.py` and executes them:

* the module-level `_begin_prompt_text()` helper (prompt wording),
* `class LevelIntroScreen` itself.

The fade-in curve, the theme tint, the difficulty bars and the gold / boss
labels all live inside `draw()` and its `_draw_*` helpers. They are not
re-implemented here: the real methods run against a minimal pygame / font /
theme shim and `sys.settrace` reads the real locals off the frame at fixed
lines. The config and boss dictionaries come from the real `levels/level_data.py`
and `bosses/boss_data.py` (both pure data, loaded by file path so the
`levels` / `bosses` package `__init__` files are not executed).

Two inputs are stubbed on purpose and are NOT part of this slice:
* `_core` exposes only `GameSettings`. `compute_starting_gold`,
  `compute_gold_per_second` and `format_gold_rate` are left out, so the source
  takes its own `except` fallbacks (`starting_gold` from the level config and
  `PASSIVE +{GOLD_PER_SECOND}/s`). The Godot port mirrors those fallbacks.
* `mobile.perf` is a no-op stub with `cheap_alpha = True` (the path a phone
  takes), and `pygame.time.get_ticks()` is pinned to 0.

Run: python godot_rebuild/tests/level_intro_screen_source_oracle.py
"""
import importlib.util
import json
import math
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "level_intro_screen_source.json"

TAG = "_render.py:LevelIntroScreen"
HELPER_TAG = "_render.py:_begin_prompt_text"
SCREEN_W = 1280
SCREEN_H = 720
TIMELINE_TICKS = 70
SKIP_AT_TICK = 70

# Inputs for the skip table. Names are the Godot test's vocabulary; the
# source gets the pygame key constants the shim below defines.
SKIP_INPUTS = [
    ("space", {"key": "K_SPACE"}),
    ("return", {"key": "K_RETURN"}),
    ("letter_a", {"key": "K_a"}),
    ("click", {"click": True}),
]


# --------------------------------------------------------------------------
# Shims. Nothing from pygame, _core or mobile is imported.
# --------------------------------------------------------------------------
class _Rect:
    def __init__(self, x=0, y=0, w=0, h=0):
        self.x = x
        self.y = y
        self.width = w
        self.height = h

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.width

    @property
    def size(self):
        return (self.width, self.height)

    def inflate(self, dw, dh):
        return _Rect(self.x - dw // 2, self.y - dh // 2, self.width + dw, self.height + dh)


FILLS = []


class _Surface:
    def __init__(self, *args, **kwargs):
        pass

    def set_alpha(self, *args, **kwargs):
        pass

    def blit(self, *args, **kwargs):
        pass

    def fill(self, color, special_flags=None):
        FILLS.append(tuple(color))

    def get_at(self, pos):
        return (0, 0, 0, 0)

    def get_rect(self, **kwargs):
        return _Rect(0, 0, 10, 10)


class _FontShim:
    def __init__(self, *args, **kwargs):
        pass

    def render(self, *args, **kwargs):
        return _Surface()


class _ThemeShim:
    def letter(self, text):
        return text

    def draw_icon(self, *args, **kwargs):
        pass

    def corner_ticks(self, *args, **kwargs):
        pass


class _DrawShim:
    @staticmethod
    def rect(*args, **kwargs):
        pass

    @staticmethod
    def line(*args, **kwargs):
        pass

    @staticmethod
    def circle(*args, **kwargs):
        pass

    @staticmethod
    def polygon(*args, **kwargs):
        pass


class _TimeShim:
    @staticmethod
    def get_ticks():
        return 0


class _PygameShim:
    SRCALPHA = 1
    K_SPACE = 32
    K_RETURN = 13
    K_a = 97
    Surface = _Surface
    Rect = _Rect
    draw = _DrawShim
    time = _TimeShim


class _Quality:
    cheap_alpha = True


class _Pool:
    def get(self, w, h):
        return _Surface()

    def release(self, surface):
        pass


SETTINGS = {"difficulty": "normal"}


class _GameSettings:
    def __init__(self):
        self.difficulty = SETTINGS["difficulty"]


def _install_stubs():
    # `from bosses.boss_data import ...` inside __init__ needs the repo root.
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    # `mobile` is a bare package so `from mobile import platform_utils` fails
    # (caught by the source's except) and `mobile.perf` resolves to the stub.
    mobile = types.ModuleType("mobile")
    mobile.__path__ = []
    perf = types.ModuleType("mobile.perf")
    perf.Quality = _Quality
    perf.darken = lambda surface, alpha: None
    perf.cached_render = lambda key, w, h, paint: _Surface()
    perf.POOL = _Pool()
    perf.blit_overlay = lambda surface, overlay, rect: None
    mobile.perf = perf
    sys.modules["mobile"] = mobile
    sys.modules["mobile.perf"] = perf

    core = types.ModuleType("_core")
    core.GameSettings = _GameSettings
    sys.modules["_core"] = core


def _load_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _slice(lines, start_pred, end_pred):
    start = next(i for i, line in enumerate(lines) if start_pred(line))
    end = next(i for i, line in enumerate(lines) if i > start and end_pred(line))
    return "\n".join(lines[start:end])


def _load_class():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    helper_block = _slice(
        lines,
        lambda line: line.startswith("def _begin_prompt_text("),
        lambda line: line.startswith("# ----"),
    )
    class_block = _slice(
        lines,
        lambda line: line.startswith("class LevelIntroScreen:"),
        lambda line: line.startswith("# ===="),
    )
    namespace = {
        "math": math,
        "pygame": _PygameShim,
        "ui_theme": _ThemeShim(),
        "get_font": _FontShim,
        "title_font": _FontShim,
        "GOLD_PER_SECOND": _core_gold_per_second(),
    }
    exec(compile(helper_block, HELPER_TAG, "exec"), namespace)
    exec(compile(class_block, TAG, "exec"), namespace)
    return namespace, class_block


def _core_gold_per_second():
    # `GOLD_PER_SECOND` is only used by the fallback text; read the real value.
    text = (ROOT / "_core.py").read_text(encoding="utf-8")
    match = re.search(r"^GOLD_PER_SECOND = (\d+)", text, re.MULTILINE)
    assert match, "GOLD_PER_SECOND missing from _core.py"
    return int(match.group(1))


def _capture_lines(block):
    """1-based line numbers inside the class block to read locals on."""
    prefixes = {
        "tint": "surface.blit(tint, (0, 0))",
        "diff": "bar_start_x = cx - (5 * 22) // 2",
        "bar": "bar_surf = pygame.Surface((18, 10), pygame.SRCALPHA)",
        "gold": "start_text = self.font_medium.render(",
        "passive": "inc_text = self.font_tiny.render(",
        "tag": "tag_surf = self.font_small.render(",
        "prompt": "prompt_text = self.font_medium.render(",
    }
    found = {}
    stripped = [line.strip() for line in block.splitlines()]
    for key, prefix in prefixes.items():
        hits = [i + 1 for i, line in enumerate(stripped) if line.startswith(prefix)]
        assert len(hits) == 1, "%s matched %d times" % (prefix, len(hits))
        found[key] = hits[0]
    return found


def _trace_draw(screen, lines):
    """Run draw() once and read the source's own locals off the frames."""
    rec = {"bars": []}

    def tracer(frame, event, arg):
        if event == "call":
            return tracer if frame.f_code.co_filename == TAG else None
        if event == "line" and frame.f_code.co_filename == TAG:
            at = frame.f_lineno
            local = frame.f_locals
            if at == lines["tint"]:
                rec["fade_alpha"] = local["fade_alpha"]
                rec["tint_alpha"] = local["theme_tint_alpha"]
            elif at == lines["diff"]:
                rec["difficulty"] = {
                    "title": local["diff_title"],
                    "level": local["diff_level"],
                    "color": list(local["diff_color"]),
                }
            elif at == lines["bar"]:
                rec["bars"].append(list(local["bar_col"]))
            elif at == lines["gold"]:
                rec["starting_gold"] = local["sg"]
            elif at == lines["passive"]:
                rec["passive_text"] = local["inc_str"]
            elif at == lines["tag"]:
                rec["boss_tag"] = {"text": local["tag_text"], "color": list(local["tag_color"])}
            elif at == lines["prompt"]:
                rec["prompt_text"] = local["_prompt_str"]
        return tracer

    FILLS.clear()
    sys.settrace(tracer)
    try:
        screen.draw(_Surface())
    finally:
        sys.settrace(None)
    assert FILLS, "tint.fill never ran"
    rec["tint_rgba"] = list(FILLS[0])
    return rec


def _level_subset(config):
    keys = (
        "level_number", "name", "description", "enemy_hp_mult",
        "enemy_damage_mult", "meta_gold_reward_win", "map_theme",
        "true_boss", "starting_gold",
    )
    return {key: config[key] for key in keys if key in config}


def _boss_subset(boss):
    keys = ("name", "title", "boss_class", "color", "color_dark", "entrance_color")
    return {key: list(boss[key]) if isinstance(boss[key], tuple) else boss[key]
            for key in keys if key in boss}


def source_fixture():
    _install_stubs()
    namespace, class_block = _load_class()
    cls = namespace["LevelIntroScreen"]
    lines = _capture_lines(class_block)

    level_data = _load_file("level_data", ROOT / "levels" / "level_data.py")
    levels = []
    for number in range(1, 21):
        config = getattr(level_data, "LEVEL_%d" % number, None)
        if config is not None:
            levels.append(config)
    assert len(levels) == 20, "expected 20 level configs, got %d" % len(levels)
    themes = sorted(set(re.findall(r'self\.map_theme == "(\w+)"',
                                   SOURCE.read_text(encoding="utf-8"))))

    # 1. Timeline on the real level 1: fade-in, prompt appearance, then skip.
    SETTINGS["difficulty"] = "normal"
    level_one = levels[0]
    screen = cls(level_one, SCREEN_W, SCREEN_H)
    boss_snapshot = {
        "name": screen.boss_name, "title": screen.boss_title,
        "boss_class": screen.boss_class,
        "color": list(screen.boss_color),
        "color_dark": list(screen.boss_color_dark),
        "entrance_color": list(screen.boss_entrance_color),
    }
    fade_in_duration = screen.fade_in_duration
    timeline = []
    sound_steps = []
    for tick in range(TIMELINE_TICKS):
        screen.update()
        if tick == 0:
            sound_steps.append(bool(screen._sound_played))
        rec = _trace_draw(screen, lines)
        timeline.append([
            screen.timer, screen.is_active(), rec["fade_alpha"], rec["tint_alpha"],
            screen.timer > screen.fade_in_duration,
            rec.get("prompt_text"),
        ])
    screen.update()
    skip_at_end = screen.handle_skip(key=_PygameShim.K_SPACE)
    timeline_end = [screen.timer, screen.is_active(), skip_at_end]

    # 2. Skip table: each input on a fresh screen.
    skips = []
    for name, args in SKIP_INPUTS:
        fresh = cls(level_one, SCREEN_W, SCREEN_H)
        kwargs = {}
        if "key" in args:
            kwargs["key"] = getattr(_PygameShim, args["key"])
        if args.get("click"):
            kwargs["click"] = True
        skips.append([name, fresh.handle_skip(**kwargs), fresh.is_active()])
    inactive = cls(level_one, SCREEN_W, SCREEN_H)
    inactive.active = False
    skips.append(["inactive", inactive.handle_skip(key=_PygameShim.K_SPACE), False])

    # 3. Difficulty x all 20 levels, sampled after the fade (timer 40).
    difficulty_rows = []
    for index, config in enumerate(levels):
        for difficulty in ("easy", "normal", "hard"):
            SETTINGS["difficulty"] = difficulty
            screen = cls(config, SCREEN_W, SCREEN_H)
            for _ in range(40):
                screen.update()
            rec = _trace_draw(screen, lines)
            difficulty_rows.append({
                "level": _level_subset(config),
                "boss": _boss_subset({
                    "name": screen.boss_name, "title": screen.boss_title,
                    "boss_class": screen.boss_class,
                    "color": screen.boss_color,
                    "color_dark": screen.boss_color_dark,
                    "entrance_color": screen.boss_entrance_color,
                }),
                "difficulty_setting": difficulty,
                "hp_mult": screen.hp_mult,
                "fade_alpha": rec["fade_alpha"],
                "tint_alpha": rec["tint_alpha"],
                "difficulty": rec["difficulty"],
                "bars": rec["bars"],
                "reward": screen.reward,
                "starting_gold": rec["starting_gold"],
                "passive_text": rec["passive_text"],
                "boss_tag": rec["boss_tag"],
                "prompt_text": rec["prompt_text"],
            })
    SETTINGS["difficulty"] = "normal"

    # 4. Theme tint for every theme the source names, plus the default.
    theme_rows = []
    for theme in themes + ["unknown_theme"]:
        config = dict(level_one)
        config["map_theme"] = theme
        screen = cls(config, SCREEN_W, SCREEN_H)
        for _ in range(60):
            screen.update()
        rec = _trace_draw(screen, lines)
        theme_rows.append([theme, rec["tint_rgba"], rec["tint_alpha"]])

    return {
        "source": "_render.py::LevelIntroScreen",
        "fade_in_duration": fade_in_duration,
        "gold_per_second": namespace["GOLD_PER_SECOND"],
        "begin_prompt": namespace["_begin_prompt_text"](),
        "boss_snapshot": boss_snapshot,
        "level": _level_subset(level_one),
        "sound_on_first_update": sound_steps,
        "timeline": timeline,
        "timeline_end": timeline_end,
        "skip_inputs": [[name, args] for name, args in SKIP_INPUTS],
        "skips": skips,
        "difficulty_rows": difficulty_rows,
        "themes": theme_rows,
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    print("level_intro_screen: %d timeline ticks, %d skip inputs, %d difficulty rows, %d themes"
          % (len(fixture["timeline"]), len(fixture["skips"]),
             len(fixture["difficulty_rows"]), len(fixture["themes"])))
    print("  prompt: %s; fade at tick 15: %s; tint at tick 15: %s"
          % (fixture["begin_prompt"], fixture["timeline"][14][2], fixture["timeline"][14][3]))
    print("wrote %s" % FIXTURE.relative_to(ROOT))


if __name__ == "__main__":
    main()
