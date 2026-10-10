"""Source oracle for `_render.py::BossDeathAnimation`.

`_render.py` cannot be imported because of its existing circular imports, so
this oracle extracts the real class block and executes it with a boss object,
fonts, pygame and mobile.perf shims. The fixture records the real random
fragment/particle state and update timeline. The real `draw()` also runs
against the shim; `sys.settrace` reads its flash, wave, dissolve and
celebration locals instead of rewriting animation curves in the oracle.

Run: python godot_rebuild/tests/boss_death_animation_source_oracle.py
"""
import json
import math
import random
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "boss_death_animation_source.json"
TAG = "_render.py:BossDeathAnimation"
SCREEN_W = 1280
SCREEN_H = 720

CASES = [
    {
        "name": "mini",
        "seed": 4061,
        "config": {
            "x": 100.0,
            "y": 200.0,
            "name": "Gornak",
            "title": "The Stone Maw",
            "boss_class": "mini",
            "color": [180, 90, 80],
            "color_dark": [90, 45, 40],
            "entrance_color": [255, 140, 80],
            "gold_reward": 1200,
            "radius": 40.0,
        },
        "snapshot_ticks": [0, 1, 15, 30, 59, 60, 61],
    },
    {
        "name": "true",
        "seed": 90210,
        "config": {
            "x": 320.0,
            "y": 180.0,
            "name": "Abaddon",
            "title": "The Abyssal King",
            "boss_class": "true",
            "color": [190, 70, 210],
            "color_dark": [95, 35, 105],
            "entrance_color": [220, 90, 255],
            "gold_reward": 800,
            "radius": 60.0,
        },
        "snapshot_ticks": [0, 1, 15, 30, 45, 89, 90, 91, 110, 126, 150, 192, 209, 210],
    },
]


class _Rect:
    def __init__(self, center=(0, 0), width=100, height=30):
        self.x = int(center[0] - width / 2)
        self.y = int(center[1] - height / 2)
        self.width = width
        self.height = height

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.width

    @property
    def centery(self):
        return self.y + self.height // 2


class _Text:
    def __init__(self, text):
        self.text = text
        self.alpha = 255

    def set_alpha(self, alpha):
        self.alpha = int(alpha)

    def get_rect(self, center):
        return _Rect(center, max(20, len(self.text) * 12), 30)


class _Font:
    def render(self, text, _antialias, _color):
        return _Text(text)


class _Surface:
    def __init__(self, size=(1, 1), _flags=0):
        self.size = tuple(size)

    def fill(self, *_args, **_kwargs):
        return None

    def blit(self, *_args, **_kwargs):
        return None

    def set_alpha(self, *_args, **_kwargs):
        return None


class _Draw:
    @staticmethod
    def circle(*_args, **_kwargs):
        return None

    @staticmethod
    def polygon(*_args, **_kwargs):
        return None


class _Time:
    @staticmethod
    def get_ticks():
        return 0


class _Pygame:
    SRCALPHA = 1
    K_SPACE = 32
    K_ESCAPE = 27
    Surface = _Surface
    draw = _Draw()
    time = _Time()


class _Theme:
    @staticmethod
    def letter(text):
        return text

    @staticmethod
    def draw_icon(*_args, **_kwargs):
        return None


class _Quality:
    cheap_alpha = True


class _Boss:
    def __init__(self, config):
        for key, value in config.items():
            setattr(self, key, tuple(value) if key in {"color", "color_dark", "entrance_color"} else value)


def _install_stubs():
    mobile = types.ModuleType("mobile")
    mobile.__path__ = []
    perf = types.ModuleType("mobile.perf")
    perf.Quality = _Quality
    perf.flash = lambda _surface, _alpha: None
    perf.darken = lambda _surface, _alpha: None
    mobile.perf = perf
    sys.modules["mobile"] = mobile
    sys.modules["mobile.perf"] = perf


def _load_class():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("class BossDeathAnimation:"))
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("# ====================================================================")),
        len(lines),
    )
    block = "\n".join(lines[start:end])
    namespace = {
        "math": math,
        "random": random,
        "pygame": _Pygame(),
        "get_font": lambda *_args, **_kwargs: _Font(),
        "title_font": lambda *_args, **_kwargs: _Font(),
        "ui_theme": _Theme(),
        "_skip_button_label": lambda: "SPACE",
    }
    exec(compile(block, TAG, "exec"), namespace)
    return namespace["BossDeathAnimation"]


def _round(value):
    return round(float(value), 6)


def _fragment_snapshot(fragment):
    return {
        "x": _round(fragment["x"]),
        "y": _round(fragment["y"]),
        "vx": _round(fragment["vx"]),
        "vy": _round(fragment["vy"]),
        "size": fragment["size"],
        "color": list(fragment["color"]),
        "rotation": _round(fragment["rotation"]),
        "rot_speed": _round(fragment["rot_speed"]),
        "gravity": _round(fragment["gravity"]),
        "life": fragment["life"],
        "max_life": fragment["max_life"],
    }


def _rising_snapshot(particle):
    return {
        "x": _round(particle["x"]),
        "y": _round(particle["y"]),
        "vx": _round(particle["vx"]),
        "vy": _round(particle["vy"]),
        "size": particle["size"],
        "color": list(particle["color"]),
        "life": particle["life"],
        "max_life": particle["max_life"],
        "phase": _round(particle["phase"]),
    }


def _trace_draw(animation):
    """Run the original draw and capture its local animation values."""
    result = {"death": {}, "celebration": {}}
    wave_values = []

    def tracer(frame, event, _arg):
        if event != "line" or frame.f_code.co_filename != TAG:
            return tracer
        local = frame.f_locals
        if frame.f_code.co_name == "_draw_death_sequence":
            death = result["death"]
            for key in ("elapsed", "progress", "flash_alpha"):
                if key in local:
                    death[key] = _round(local[key]) if isinstance(local[key], float) else int(local[key])
            if "ring_surf" in local and all(key in local for key in ("wave_elapsed", "wave_progress", "radius", "alpha", "color")):
                value = {
                    "wave_elapsed": int(local["wave_elapsed"]),
                    "wave_progress": _round(local["wave_progress"]),
                    "radius": int(local["radius"]),
                    "alpha": int(local["alpha"]),
                    "color": list(local["color"]),
                }
                if value not in wave_values:
                    wave_values.append(value)
        elif frame.f_code.co_name == "_draw_celebration":
            celebration = result["celebration"]
            for key in (
                "elapsed",
                "progress",
                "overlay_alpha",
                "bounce_prog",
                "eased",
                "text_alpha",
                "text_offset_y",
                "reward_alpha",
                "hint_pulse",
                "hint_alpha",
            ):
                if key in local:
                    value = local[key]
                    celebration[key] = _round(value) if isinstance(value, float) else int(value)
        return tracer

    sys.settrace(tracer)
    try:
        animation.draw(_Surface((SCREEN_W, SCREEN_H)))
    finally:
        sys.settrace(None)
    if wave_values:
        result["death"]["waves"] = wave_values
    return result


def _draw_values(animation):
    if not animation.active and not animation.celebration_active:
        return None
    traced = _trace_draw(animation)
    if animation.active:
        return {"death": traced["death"]}
    return {"celebration": traced["celebration"]}


def _snapshot(animation, tick):
    fragments = animation.fragments
    rising = animation.rising_particles
    return {
        "tick": tick,
        "active": bool(animation.active),
        "timer": animation.timer,
        "duration": animation.duration,
        "show_celebration": bool(animation.show_celebration),
        "celebration_active": bool(animation.celebration_active),
        "celebration_timer": animation.celebration_timer,
        "sound_played": bool(animation._sound_played),
        "fragment_count": len(fragments),
        "rising_particle_count": len(rising),
        "first_fragment": _fragment_snapshot(fragments[0]) if fragments else None,
        "last_fragment": _fragment_snapshot(fragments[-1]) if fragments else None,
        "first_rising": _rising_snapshot(rising[0]) if rising else None,
        "last_rising": _rising_snapshot(rising[-1]) if rising else None,
        "draw": _draw_values(animation),
    }


def _trace_case(cls, case):
    random.seed(case["seed"])
    config = case["config"]
    animation = cls(_Boss(config), SCREEN_W, SCREEN_H)
    fragment_specs = [_fragment_snapshot(value) for value in animation.fragments]
    rising_specs = [_rising_snapshot(value) for value in animation.rising_particles]
    wanted = set(case["snapshot_ticks"])
    snapshots = [_snapshot(animation, 0)]
    for tick in range(1, max(wanted) + 1):
        animation.update()
        if tick in wanted:
            snapshots.append(_snapshot(animation, tick))
    return {
        "name": case["name"],
        "seed": case["seed"],
        "config": config,
        "fragment_specs": fragment_specs,
        "rising_specs": rising_specs,
        "snapshots": snapshots,
    }


def _skip_cases(cls, case):
    config = case["config"]
    rows = []
    for label, key, click in (
        ("active_space", _Pygame.K_SPACE, False),
        ("active_escape", _Pygame.K_ESCAPE, False),
        ("active_click", None, True),
    ):
        random.seed(case["seed"])
        animation = cls(_Boss(config), SCREEN_W, SCREEN_H)
        result = animation.handle_skip(key, click)
        rows.append({"label": label, "result": result, "active": animation.active, "celebration_active": animation.celebration_active})
    random.seed(case["seed"])
    animation = cls(_Boss(config), SCREEN_W, SCREEN_H)
    for _ in range(animation.duration):
        animation.update()
    for label, key, click in (
        ("celebration_space", _Pygame.K_SPACE, False),
        ("celebration_escape", _Pygame.K_ESCAPE, False),
        ("celebration_click", None, True),
        ("celebration_letter", 97, False),
    ):
        if label != "celebration_space":
            random.seed(case["seed"])
            animation = cls(_Boss(config), SCREEN_W, SCREEN_H)
            for _ in range(animation.duration):
                animation.update()
        result = animation.handle_skip(key, click)
        rows.append({"label": label, "result": result, "active": animation.active, "celebration_active": animation.celebration_active})
    return rows


def source_fixture():
    _install_stubs()
    cls = _load_class()
    cases = [_trace_case(cls, case) for case in CASES]
    skips = {case["name"]: _skip_cases(cls, case) for case in CASES}
    return {
        "source": "_render.py::BossDeathAnimation",
        "screen": [SCREEN_W, SCREEN_H],
        "constants": {
            "true_duration": 90,
            "mini_duration": 60,
            "celebration_duration": 120,
            "flash_window": 15,
            "wave_duration": 40,
        },
        "cases": cases,
        "skip_cases": skips,
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=1) + "\n", encoding="utf-8")
    print("wrote %s (%d cases)" % (FIXTURE, len(fixture["cases"])))


if __name__ == "__main__":
    sys.exit(main())
