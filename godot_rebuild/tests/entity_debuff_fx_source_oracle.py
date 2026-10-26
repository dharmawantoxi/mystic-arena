"""Source oracle for the non-boss call sites of the shared tower-debuff indicator (layer 9bq10).

`_core.py::TowerDebuffMixin._draw_tower_debuff_fx` is the same method the boss path already
replays (layer 9bq9). `_entity.py` calls it from two more `draw()` methods:

  Hero.draw:
      ...ground shadow ellipse (0, 0, 0, 100)...
      self._draw_tower_debuff_fx(surface, x, y, self.radius)          # rings ON
      ...hero shape...
    `Hero.__init__` pins `self.radius = 16`, and a hero has no `anim_time`, so the indicator's
    `getattr(self, "anim_time", getattr(self, "pulse", 0))` reads `pulse` (`+= 0.1` per tick).

  Minion.draw:
      ...if self.slow_timer > 0: ice aura (disc + orbiting specks)...
      self._draw_tower_debuff_fx(surface, x, y, self.radius,
                                 include_rings=False)               # rings OFF
      ...render_minion(...)...
    A minion carries an integer `anim_time` (`+= 1` per tick) and its radius comes from
    `stats["radius"]`.

The REAL mixin method is harvested with `ast` and runs under the recording pygame shim of
`draw_recorder.py`; the call sites themselves are audited from `_entity.py` with `ast` so the
argument list, the `include_rings` flag and the statement order stay pinned to the source.

Run: python godot_rebuild/tests/entity_debuff_fx_source_oracle.py
"""
import ast
import json
import math
import textwrap
from pathlib import Path

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_core.py"
ENTITY = ROOT / "_entity.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "entity_debuff_fx_source.json"
MIXIN = "TowerDebuffMixin"
HARVESTED = ("_draw_tower_debuff_fx",)
CALL = "_draw_tower_debuff_fx"
# (`_entity.py` class, the source radius of that unit)
CALL_OWNERS = (("Hero", 16), ("Minion", 9))


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


def call_sites():
    """Audit the two `draw()` call sites: arguments, keyword flag and statement neighbours."""
    text = ENTITY.read_text(encoding="utf-8")
    tree = ast.parse(text)
    out = {}
    for class_name, radius in CALL_OWNERS:
        owner = next((node for node in tree.body
                      if isinstance(node, ast.ClassDef) and node.name == class_name), None)
        if owner is None:
            raise AssertionError("%s not found in %s" % (class_name, ENTITY.name))
        draw = next((node for node in owner.body
                     if isinstance(node, ast.FunctionDef) and node.name == "draw"), None)
        if draw is None:
            raise AssertionError("%s.draw not found in %s" % (class_name, ENTITY.name))
        index = next((position for position, statement in enumerate(draw.body)
                      if isinstance(statement, ast.Expr)
                      and isinstance(statement.value, ast.Call)
                      and isinstance(statement.value.func, ast.Attribute)
                      and statement.value.func.attr == CALL), None)
        if index is None:
            raise AssertionError("%s.draw never calls %s" % (class_name, CALL))
        statement = draw.body[index]
        call = statement.value
        out[class_name] = {
            "args": [ast.get_source_segment(text, argument) for argument in call.args],
            "kwargs": {keyword.arg: ast.get_source_segment(text, keyword.value)
                       for keyword in call.keywords},
            "radius": radius,
            "before": ast.get_source_segment(text, draw.body[index - 1]) if index else "",
            "after": ast.get_source_segment(text, draw.body[index + 1])
            if index + 1 < len(draw.body) else "",
        }
    return out


# (label, owner, slow, atk_slow, skill_down, anti_heal, burn, anim, alive, radius)
FRAMES = [
    ("hero_clean", "Hero", 0, 0, 0, 0, 0, 0.0, True, 16),
    ("hero_slow_only", "Hero", 30, 0, 0, 0, 0, 3.0, True, 16),
    ("hero_burn_only", "Hero", 0, 0, 0, 0, 20, 5.5, True, 16),
    ("hero_all_debuffs", "Hero", 30, 30, 40, 40, 20, 7.2, True, 16),
    ("minion_slow_only_no_rings", "Minion", 30, 0, 0, 0, 0, 0.0, True, 9),
    ("minion_burn_only", "Minion", 0, 0, 0, 0, 20, 13.0, True, 9),
    ("minion_all_debuffs", "Minion", 30, 30, 40, 40, 20, 26.0, True, 9),
    ("minion_dead_ignores_everything", "Minion", 30, 30, 40, 40, 20, 26.0, False, 9),
]


def _record(pygame, mixin, frames):
    out = []
    for label, owner, slow, atk_slow, skill_down, anti_heal, burn, anim, alive, radius in frames:
        screen = rec.Surface((1280, 720))
        unit = _Unit(slow, atk_slow, skill_down, anti_heal, burn, anim, alive)
        rings = owner == "Hero"
        # The harvested member is a method of the mixin, so the stand-in is the first argument.
        if rings:
            mixin._draw_tower_debuff_fx(unit, screen, 640, 360, radius)
        else:
            mixin._draw_tower_debuff_fx(unit, screen, 640, 360, radius, include_rings=False)
        out.append({
            "label": label,
            "owner": owner,
            "radius": radius,
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
        return {
            "anchor": [640, 360],
            "call_sites": call_sites(),
            "frames": _record(pygame, mixin, FRAMES),
        }


if __name__ == "__main__":
    FIXTURE.write_text(json.dumps(source_fixture(), indent=1) + "\n", encoding="utf-8")
    print("wrote", FIXTURE)
