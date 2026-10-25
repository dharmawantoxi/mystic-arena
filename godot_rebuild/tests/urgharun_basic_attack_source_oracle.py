"""Source oracle for urgharun's basic-attack FX and the swing clock it reads (layer 9bq8).

`bosses/level40.py::_NS_urgharun.draw_urgharun` opens with `_update_urg_attack_anim(boss)`, which
is a presentation-only clock stored on the boss:

    previous = boss._urg_previous_timer (default: current timer)
    if (previous > cooldown - 5 and timer < 3) or timer >= cooldown - 1:   # arm
        _urg_attack_active = True; _urg_attack_frame = 0
    if active: _urg_attack_frame += 1; if it reaches 28: disarm, frame = 0
    _urg_previous_timer = timer
    _urg_attack_progress = min(1.0, frame / 28) if active else 0.0

`cooldown` is the RAW `attack_cooldown` (`max(2, int(...))`), not the slowed effective value, so a
slowed boss arms the swing while its timer is still above the reduced window - a source quirk.
The clock advances once per painted frame (it lives in the draw path).

The FX itself is LAYER 4, gated on `attacking and not active_skill`:
  progress < 0.30  wind-up:  `_aacircle(fury_light)` rings at both claws
  0.30..0.70       slash:    5 arcs x 10 segments x 4 nested lines, bright tips, 8 blood sparks
  progress >= 0.70 impact:   3 impact rings, a hot core, 5 scratch marks, 10 burst particles
`tx, ty` is `boss.target` when it is alive, else `(x + facing * 60, y)`; a target beyond 80 px is
pulled back to 60 px along the same bearing.

Run: python godot_rebuild/tests/urgharun_basic_attack_source_oracle.py
"""
import ast
import json
import math
import textwrap
from pathlib import Path

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "bosses" / "level40.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "urgharun_basic_attack_source.json"
NAMESPACE = "_NS_urgharun"
HARVESTED = (
    "HAS_AACIRCLE", "HAS_AALINES", "PALETTE", "_clamp", "_alpha", "_aacircle", "_poly",
    "_draw_basic_attack_fx", "_update_urg_attack_anim",
)
PALETTE_KEYS = (
    "fury_darkest", "fury_dark", "fury_mid", "fury_light", "fury_hot", "fury_shine", "white",
)


class _Target:
    """`boss.target`: the FX reads only `x`, `y` and `alive`."""

    def __init__(self, x, y, alive=True):
        self.x, self.y, self.alive = x, y, alive


class _Boss:
    """Stand-in for the boss attributes the two harvested functions read and write."""

    def __init__(self, direction=1, target=None, pulse=0.0, progress=0.0):
        self.direction = direction
        self.target = target
        self.pulse = pulse
        self._urg_attack_progress = progress
        # `_update_urg_attack_anim` only creates these on its first arm; the real boss has them
        # from the first tick, so the stand-in starts from the same defaults.
        self._urg_attack_active = False
        self._urg_attack_frame = 0


def _harvest_namespace(pygame):
    text = SOURCE.read_text(encoding="utf-8")
    owner = next((node for node in ast.parse(text).body
                  if isinstance(node, ast.ClassDef) and node.name == NAMESPACE), None)
    if owner is None:
        raise AssertionError("%s not found in %s" % (NAMESPACE, SOURCE.name))
    found = {}
    for node in owner.body:
        if isinstance(node, ast.FunctionDef) and node.name in HARVESTED:
            found[node.name] = node
        elif (isinstance(node, ast.Assign) and len(node.targets) == 1
              and isinstance(node.targets[0], ast.Name) and node.targets[0].id in HARVESTED):
            found[node.targets[0].id] = node
    missing = set(HARVESTED) - set(found)
    if missing:
        raise AssertionError("%s not found in %s.%s" % (sorted(missing), SOURCE.name, NAMESPACE))
    body = "".join(
        textwrap.indent(textwrap.dedent(ast.get_source_segment(text, found[name], padded=True)),
                        "    ") + "\n"
        for name in HARVESTED)
    namespace = {"pygame": pygame, "math": math}
    exec(compile("class %s:\n%s" % (NAMESPACE, body), SOURCE.name, "exec"), namespace)
    return namespace[NAMESPACE]


# (label, progress, direction, target, pulse). 0.30 and 0.70 are the phase boundaries; the far
# target records the 80 px melee clamp and `None` the `x + facing * 60` fallback.
FX_FRAMES = [
    ("fx_windup_start", 0.0, 1, (700, 360), 0.0),
    ("fx_windup_mid", 0.15, 1, (700, 360), 4.0),
    ("fx_windup_late", 0.29, 1, (700, 360), 9.5),
    ("fx_slash_start", 0.30, 1, (700, 360), 0.0),
    ("fx_slash_mid", 0.50, 1, (700, 360), 12.3),
    ("fx_slash_late", 0.69, -1, (580, 340), 30.7),
    ("fx_impact_start", 0.70, 1, (700, 360), 0.0),
    ("fx_impact_mid", 0.85, -1, (580, 340), 21.4),
    ("fx_impact_late", 0.99, 1, (700, 360), 63.2),
    ("fx_no_target", 0.85, 1, None, 5.0),
    ("fx_far_target", 0.50, 1, (1100, 600), 8.7),
]
# (label, cooldown, timers). Tick-by-tick `boss.timer` values as the draw path sees them.
CLOCK_RUNS = [
    # urgharun's own cooldown: the swing arms on the tick right after the attack resets it.
    ("clock_attack_cycle", 38, [38, 37, 36, 35, 34, 33, 32]),
    # A slowed boss keeps the effective timer above the raw window: it arms early (source quirk).
    ("clock_slowed_early_arm", 38, [50, 49, 48, 47]),
    # `just_reset` arms the swing even when the timer dropped away from the top of the window.
    ("clock_just_reset", 38, [36, 2, 1, 0, 38]),
    # The 28-frame swing window: arm, run out, then re-arm on the next top-of-window tick.
    ("clock_full_window", 30, [30] + [29 - i for i in range(0, 30)] + [30]),
    # A cooldown of 2 still works because the source clamps it with `max(2, ...)`.
    ("clock_tiny_cooldown", 1, [3, 2, 1, 0]),
]


def _record_fx(namespace, frames):
    out = []
    for label, progress, direction, target, pulse in frames:
        screen = rec.Surface((1280, 720))
        boss = _Boss(direction, None if target is None else _Target(*target), pulse, progress)
        namespace._draw_basic_attack_fx(screen, boss, 640, 360)
        out.append({
            "label": label,
            "progress": progress,
            "direction": direction,
            "target": None if target is None else list(target),
            "pulse": pulse,
            "ops": screen.ops,
        })
    return out


def _record_clock(namespace, runs):
    out = []
    for label, cooldown, timers in runs:
        boss = _Boss()
        boss.attack_cooldown = cooldown
        boss.timer = timers[0]
        steps = []
        for timer in timers:
            boss.timer = timer
            namespace._update_urg_attack_anim(boss)
            steps.append({
                "timer": timer,
                "active": bool(boss._urg_attack_active),
                "frame": int(boss._urg_attack_frame),
                "previous_timer": int(boss._urg_previous_timer),
                "progress": boss._urg_attack_progress,
            })
        out.append({"label": label, "cooldown": cooldown, "steps": steps})
    return out


def source_fixture():
    pygame = rec.make_pygame({"ticks": 0})
    with rec.installed({"pygame": pygame}):
        namespace = _harvest_namespace(pygame)
        palette = {key: list(namespace.PALETTE[key]) for key in PALETTE_KEYS}
        return {
            "palette": palette,
            "attack_duration": 28,
            "fx_frames": _record_fx(namespace, FX_FRAMES),
            "clock_runs": _record_clock(namespace, CLOCK_RUNS),
        }


if __name__ == "__main__":
    FIXTURE.write_text(json.dumps(source_fixture(), indent=1) + "\n", encoding="utf-8")
    print("wrote", FIXTURE)
