"""Source oracle for `_core.py::TowerDebuffMixin._draw_tower_debuff_fx` (layer 9bq9).

`Boss.draw` calls it once per frame, after the cached auras and the ground shadow, before the
per-type renderer dispatch:

    if not alive: return
    if include_rings and slow_timer > 0:                      # ground ring at the feet
        draw.ellipse((150, 220, 255), (x - r - 2, y + r - 7, (r + 2) * 2, 10), 1)
    if burn_timer > 0:                                        # three flame tongues
        flick = int(1.5 + 1.5 * sin(anim * 0.6))
        flames = ((-r + 2, -r - 2, 2 + flick), (r - 2, -r - 3, 2), (0, -r - 6, 3 + flick))
        each tongue: circle (255, 140, 40) at radius fr, circle (255, 220, 90) at max(1, fr - 1)
    pips (ice slow, ice attack-slow, mage skill-down, mage anti-heal, cannon burn all present):
        5 px apart from `x - total_w // 2` at `y + r + 12`, a 5x5 (10, 10, 14) block then a 4x4
        colour block per pip.

`anim` is `getattr(self, "anim_time", getattr(self, "pulse", 0))`, so a boss without `anim_time`
would fall back to `pulse`; `BossState` has both and the view passes `anim_time`.

The REAL method is harvested from `TowerDebuffMixin` with `ast` and runs under the recording
pygame shim of `draw_recorder.py` on a stand-in that carries only those timers.

Run: python godot_rebuild/tests/boss_debuff_fx_source_oracle.py
"""
import ast
import json
import math
import textwrap
from pathlib import Path

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_core.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "boss_debuff_fx_source.json"
MIXIN = "TowerDebuffMixin"
HARVESTED = ("_draw_tower_debuff_fx",)


class _Unit:
    """Stand-in for the debuff timers the harvested method reads."""

    def __init__(self, slow=0, atk_slow=0, skill_down=0, anti_heal=0, burn=0,
                 anim_time=0.0, alive=True):
        self.slow_timer = slow
        self.atk_slow_timer = atk_slow
        self.skill_down_timer = skill_down
        self.anti_heal_timer = anti_heal
        self.burn_timer = burn
        self.anim_time = anim_time
        self.alive = alive


def _harvest(pygame):
    text = SOURCE.read_text(encoding="utf-8")
    owner = next((node for node in ast.parse(text).body
                  if isinstance(node, ast.ClassDef) and node.name == MIXIN), None)
    if owner is None:
        raise AssertionError("%s not found in %s" % (MIXIN, SOURCE.name))
    found = {}
    for node in owner.body:
        if isinstance(node, ast.FunctionDef) and node.name in HARVESTED:
            found[node.name] = node
    missing = set(HARVESTED) - set(found)
    if missing:
        raise AssertionError("%s not found in %s.%s" % (sorted(missing), SOURCE.name, MIXIN))
    body = "".join(
        textwrap.indent(textwrap.dedent(ast.get_source_segment(text, found[name], padded=True)),
                        "    ") + "\n"
        for name in HARVESTED)
    namespace = {"pygame": pygame, "math": math}
    exec(compile("class %s:\n%s" % (MIXIN, body), SOURCE.name, "exec"), namespace)
    return namespace[MIXIN]


# (label, slow, atk_slow, skill_down, anti_heal, burn, anim_time, alive, include_rings)
FRAMES = [
    ("clean", 0, 0, 0, 0, 0, 0.0, True, True),
    ("slow_only", 30, 0, 0, 0, 0, 0.0, True, True),
    ("burn_only_anim0", 0, 0, 0, 0, 20, 0.0, True, True),
    ("burn_only_anim13", 0, 0, 0, 0, 20, 13.0, True, True),
    ("all_debuffs", 30, 30, 40, 40, 20, 5.5, True, True),
    # Integer `anim_time`, the shape `BossState.anim_time` always has; the view wiring uses it.
    ("all_debuffs_int_anim", 30, 30, 40, 40, 20, 6.0, True, True),
    ("all_without_rings", 30, 30, 40, 40, 20, 5.5, True, False),
    ("dead_ignores_everything", 30, 30, 40, 40, 20, 5.5, False, True),
]


def _record(pygame, mixin, frames):
    out = []
    for label, slow, atk_slow, skill_down, anti_heal, burn, anim, alive, rings in frames:
        screen = rec.Surface((1280, 720))
        unit = _Unit(slow, atk_slow, skill_down, anti_heal, burn, anim, alive)
        # The harvested member is a method of the mixin, so the stand-in is the first argument.
        if rings:
            mixin._draw_tower_debuff_fx(unit, screen, 640, 360, 36)
        else:
            mixin._draw_tower_debuff_fx(unit, screen, 640, 360, 36, include_rings=False)
        out.append({
            "label": label,
            "slow": slow,
            "atk_slow": atk_slow,
            "skill_down": skill_down,
            "anti_heal": anti_heal,
            "burn": burn,
            "anim_time": anim,
            "alive": alive,
            "include_rings": rings,
            "ops": screen.ops,
        })
    return out


def source_fixture():
    pygame = rec.make_pygame({"ticks": 0})
    with rec.installed({"pygame": pygame}):
        mixin = _harvest(pygame)
        return {"radius": 36, "anchor": [640, 360], "frames": _record(pygame, mixin, FRAMES)}


if __name__ == "__main__":
    FIXTURE.write_text(json.dumps(source_fixture(), indent=1) + "\n", encoding="utf-8")
    print("wrote", FIXTURE)
