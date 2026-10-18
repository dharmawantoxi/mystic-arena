"""Source oracle for the `BossDeathAnimation._draw_celebration()` visuals (layer 9be).

`_render.py::BossDeathAnimation` already has its state ported
(`scripts/ui/boss_death_animation.gd`, `boss_death_animation_source_oracle.py`);
this oracle pins the post-death celebration DRAW of a true boss: the `darken`
overlay (fade in below 15 %, fade out above 85 %), the gold victory tint
`(80, 60, 20, 40)`, the bouncing `BOSS DEFEATED!` title with its six shadow
copies, the boss name with a drop shadow, the quoted title, the gold reward
with its coin icon, the `HERO UNLOCKED!` line with two vector stars, the six
rotating sparkles and the pulsing skip hint.

The REAL class is harvested from `_render.py` with `ast` and `draw()` runs under
the recording pygame shim of `draw_recorder.py`, with the real `ui_theme.letter`
and `ui_theme.draw_icon` and the real `_skip_button_label` (no touch mode and no
controller, so the label is `SPACE`). State comes from the real `update()`: the
death phase runs to its end, then each frame is drawn after N celebration ticks
with a chosen `pygame.time.get_ticks()` and `Quality.cheap_alpha`. Bosses are
real `bosses/boss_data.py` entries (pure data, loaded by file path).

Run: python godot_rebuild/tests/boss_celebration_draw_source_oracle.py
"""
import importlib.util
import json
import math
import random
import types
from pathlib import Path
from types import SimpleNamespace

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_render.py"
UI_THEME = ROOT / "ui_theme.py"
BOSS_DATA = ROOT / "bosses" / "boss_data.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "boss_celebration_draw_source.json"
BOSS_POS = (812, 304)

# (label, boss key, screen width, screen height, [(celebration tick, get_ticks, cheap_alpha)]).
# Celebration ticks (of 120): 0 = progress 0 (alpha 0), 18 = overlay full, 36 = bounce
# done, 37 = reward appears, 48-49 = sparkles appear, 60-61 = hint appears,
# 102-103 = tint ends, 119 = last drawn frame.
SCENARIOS = [
    ("abaddon", "abaddon", 1280, 720,
     [(0, 0, True), (4, 120, True), (12, 900, True), (18, 1500, True), (30, 2100, True),
      (36, 2400, True), (37, 2600, True), (48, 3000, True), (49, 3140, True),
      (60, 4000, True), (61, 4100, True), (80, 5000, True), (102, 5300, True),
      (103, 5400, True), (110, 6100, True), (119, 6500, True), (40, 2700, False)]),
    # A smaller screen moves cx / cy and the tint size; the other name changes widths.
    ("alchemist_small", "alchemist", 960, 540,
     [(24, 777, True), (70, 3141, True), (108, 9000, False)]),
]


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
        "gold_reward": int(boss["gold_reward"]), "radius": int(boss["radius"]),
        "x": BOSS_POS[0], "y": BOSS_POS[1],
    }


def _boss_object(snapshot):
    """Stand-in for the live Boss: exactly the attributes the class reads."""
    return SimpleNamespace(
        name=snapshot["name"], title=snapshot["title"], boss_class=snapshot["boss_class"],
        color=tuple(snapshot["color"]), color_dark=tuple(snapshot["color_dark"]),
        entrance_color=tuple(snapshot["entrance_color"]), gold_reward=snapshot["gold_reward"],
        radius=snapshot["radius"], x=snapshot["x"], y=snapshot["y"])


def _modules(clock):
    pygame = rec.make_pygame(clock)
    perf = rec.make_perf(True)
    platform = types.ModuleType("mobile.platform_utils")
    platform.TOUCH_MODE = False
    mobile = types.ModuleType("mobile")
    mobile.perf, mobile.platform_utils = perf, platform
    # `update()` swallows the failing `from _system import SoundManager`.
    return {"pygame": pygame, "mobile": mobile, "mobile.perf": perf,
            "mobile.platform_utils": platform, "_system": types.ModuleType("_system")}


def _load_class(pygame):
    theme_ns = {"pygame": pygame, "math": math}
    for segment in rec.harvest(UI_THEME, ["letter", "draw_icon"]):
        exec(compile(segment, "ui_theme.py", "exec"), theme_ns)
    namespace = {
        "math": math, "random": random, "pygame": pygame,
        "ui_theme": SimpleNamespace(letter=theme_ns["letter"], draw_icon=theme_ns["draw_icon"]),
        "title_font": lambda size: rec.Font(size, "title"),
        "get_font": lambda size, style="body", bold=False: rec.Font(size, style),
    }
    for segment in rec.harvest(SOURCE, ["_skip_button_label", "BossDeathAnimation"]):
        exec(compile(segment, "_render.py", "exec"), namespace)
    return namespace["BossDeathAnimation"]


def _frame(animation, label, spec, size, clock, perf):
    tick, ticks, cheap_alpha = spec
    clock["ticks"] = ticks
    perf.Quality.cheap_alpha = cheap_alpha
    screen = rec.Surface(size)
    animation.draw(screen)
    return {
        "label": label, "tick": tick, "ticks": ticks, "cheap_alpha": cheap_alpha,
        "state": {"celebration_active": bool(animation.celebration_active),
                  "celebration_timer": int(animation.celebration_timer)},
        "ops": screen.ops,
    }


def source_fixture():
    clock = {"ticks": 0}
    modules = _modules(clock)
    random_state = random.getstate()
    try:
        with rec.installed(modules):
            cls = _load_class(modules["pygame"])
            bosses = _load_bosses()
            random.seed(9)
            scenarios, frames, durations = [], [], {}
            for label, key, width, height, specs in SCENARIOS:
                snapshot = _snapshot(bosses[key])
                animation = cls(_boss_object(snapshot), width, height)
                durations = {"death": int(animation.duration),
                             "celebration": int(animation.celebration_duration)}
                while not animation.celebration_active:
                    animation.update()
                wanted = {spec[0]: spec for spec in specs}
                for tick in range(max(wanted) + 1):
                    if tick in wanted:
                        frames.append(_frame(animation, label, wanted[tick], (width, height),
                                             clock, modules["mobile.perf"]))
                    animation.update()
                scenarios.append({"label": label, "boss": snapshot, "screen": [width, height]})
            return {
                "source": "_render.py::BossDeathAnimation._draw_celebration",
                "glyph_factor": rec.GLYPH_FACTOR,
                "skip_label": "SPACE",
                "duration": durations["death"],
                "celebration_duration": durations["celebration"],
                "scenarios": scenarios,
                "frames": frames,
            }
    finally:
        random.setstate(random_state)


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, separators=(",", ":")) + "\n", encoding="utf-8")
    drawn = sum(len(frame["ops"]) for frame in fixture["frames"])
    print("wrote %s (%d frames, %d ops)" % (FIXTURE.relative_to(ROOT), len(fixture["frames"]),
                                            drawn))


if __name__ == "__main__":
    main()
