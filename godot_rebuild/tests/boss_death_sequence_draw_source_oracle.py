"""Source oracle for the `BossDeathAnimation._draw_death_sequence()` visuals (layer 9bf).

`_render.py::BossDeathAnimation` already has its state ported
(`scripts/ui/boss_death_animation.gd`, `boss_death_animation_source_oracle.py`);
this oracle pins the death-phase DRAW: the additive white flash of the first 15
ticks, the explosion waves (concentric 3 px rings plus a half-alpha core, blitted
2 px off the boss because the temp surface is 4 px larger than the radius), the
fading two-tone body, the shattering rotated-square fragments with a bright
edge, and the rising soul particles (radial glow discs plus a 1 px core).

The REAL class is harvested from `_render.py` with `ast` and `draw()` runs under
the recording pygame shim of `draw_recorder.py`. Fragments and rising particles
are random, so each scenario seeds `random` and stores the freshly created
dictionaries; the Godot port replays them through `configure(...)` and ticks
`update()`, which keeps the fixture independent of any RNG. State comes from the
real `update()` (its `_system` sound import is swallowed). Bosses are real
`bosses/boss_data.py` entries (pure data, loaded by file path).

Run: python godot_rebuild/tests/boss_death_sequence_draw_source_oracle.py
"""
import copy
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
BOSS_DATA = ROOT / "bosses" / "boss_data.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "boss_death_sequence_draw_source.json"
BOSS_POS = (640, 360)

# (label, boss key, screen width, screen height, ticks drawn after N update() calls).
# True boss (90 ticks): 0 = flash at full strength, 7 = flash fading, 15 = flash over and the
# second wave starts, 25 / 44 = three waves overlap and the body is still visible, 45 =
# progress 0.5 so the body is gone, 57 = last fragment frame, 60 = fragments dead, 89 = last
# tick. Mini boss (60 ticks): 2, 30 (body gone), 58 (fragments just below alpha 10).
SCENARIOS = [
    ("abaddon_true", "abaddon", 1280, 720, [0, 7, 15, 25, 44, 45, 57, 60, 89]),
    ("drakar_mini", "drakar", 1280, 720, [2, 30, 58]),
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


def _specs(items):
    """Created dictionaries as JSON-friendly lists (colours become RGB lists)."""
    return [{key: list(value) if isinstance(value, tuple) else value
             for key, value in item.items()} for item in copy.deepcopy(items)]


def _modules(clock):
    pygame = rec.make_pygame(clock)
    perf = rec.make_perf(True)
    mobile = types.ModuleType("mobile")
    mobile.perf = perf
    # `update()` swallows the failing `from _system import SoundManager`.
    return {"pygame": pygame, "mobile": mobile, "mobile.perf": perf,
            "_system": types.ModuleType("_system")}


def _load_class(pygame):
    namespace = {
        "math": math, "random": random, "pygame": pygame,
        "title_font": lambda size: rec.Font(size, "title"),
        "get_font": lambda size, style="body", bold=False: rec.Font(size, style),
    }
    for segment in rec.harvest(SOURCE, ["BossDeathAnimation"]):
        exec(compile(segment, "_render.py", "exec"), namespace)
    return namespace["BossDeathAnimation"]


def _frame(animation, label, tick, size):
    screen = rec.Surface(size)
    animation.draw(screen)
    return {
        "label": label, "tick": tick,
        "state": {"active": bool(animation.active), "timer": int(animation.timer)},
        "ops": screen.ops,
    }


def source_fixture():
    modules = _modules({"ticks": 0})
    random_state = random.getstate()
    try:
        with rec.installed(modules):
            cls = _load_class(modules["pygame"])
            bosses = _load_bosses()
            random.seed(1107)
            scenarios, frames, duration = [], [], {}
            for label, key, width, height, ticks in SCENARIOS:
                snapshot = _snapshot(bosses[key])
                animation = cls(_boss_object(snapshot), width, height)
                duration[label] = int(animation.duration)
                scenarios.append({
                    "label": label, "boss": snapshot, "screen": [width, height],
                    "ticks": list(ticks), "duration": duration[label],
                    "fragments": _specs(animation.fragments),
                    "rising": _specs(animation.rising_particles),
                })
                for tick in range(max(ticks) + 1):
                    if tick in ticks:
                        frames.append(_frame(animation, label, tick, (width, height)))
                    animation.update()
            return {
                "source": "_render.py::BossDeathAnimation._draw_death_sequence",
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
