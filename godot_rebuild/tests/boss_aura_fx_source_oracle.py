"""Source oracle for the cached aura block of `bosses/base_boss.py::Boss.draw` (layer 9bq7).

`Boss.draw` paints three concentric-ring auras around the boss anchor, in this order:

  ABILITY AURA  `if self.ability_active:` - filled rings in `entrance_color`,
                radius `int(ability_range * pulse)`, band `range(aura_r, aura_r - 20, -3)`,
                alpha `int((aura_r - ar) * 8 * pulse)` capped at 255;
  ENRAGE AURA   `_draw_enrage_aura` - width-2 outline rings,
                radius `radius + int(14 * pulse)`, band `range(aura_r, max(5, aura_r - 18), -3)`,
                alpha `int((aura_r - r) * 12 * pulse)` capped at 200;
  TRUE AURA     `_draw_true_boss_aura` - filled rings for `boss_class == "true"`,
                radius `radius + 15`, band `range(aura_r, aura_r - 15, -2)`,
                alpha `int((aura_r - r) * 5 * pulse)` capped at 255.

All three build an off-screen surface and blit it so the surface centre sits on the anchor, so the
recorded ops are already in screen space. The `_BOSS_AURA_CACHE` is a pure memoisation of those
surfaces (`_aura_surface` + `_aura_phase`): the geometry and alpha only depend on the radius, so
the builder in `scripts/ui/boss_aura_fx_layout.gd` emits the ops directly. This oracle therefore
harvests the real cache helpers as well, so a change in the cache key or the band arithmetic
still shows up as fixture drift.

The ability aura lives inline in `Boss.draw`, so the `if self.ability_active:` block is lifted out
of that method with `ast` and re-executed as its own function - same statements, same order.

Run: python godot_rebuild/tests/boss_aura_fx_source_oracle.py
"""
import ast
import json
import math
import textwrap
from pathlib import Path

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "bosses" / "base_boss.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "boss_aura_fx_source.json"
NAMESPACE = "Boss"
## Module-level members the three aura builders call: the LRU cache and its phase bucketing.
MODULE_MEMBERS = (
    "_BOSS_AURA_CACHE", "_BOSS_AURA_PIXELS", "_BOSS_AURA_PIXEL_BUDGET",
    "_aura_surface", "_AURA_PHASES", "_aura_phase",
)
CLASS_METHODS = ("_draw_enrage_aura", "_draw_true_boss_aura")
ABILITY_GATE = "self.ability_active"


class _Boss:
    """Stand-in for the boss attributes the harvested methods read."""

    def __init__(self, radius=36, boss_class="mini", color=(255, 140, 60), pulse=0.0,
                 enrage_pulse=0.0, anim_time=0, ability_range=0.0,
                 entrance_color=(255, 200, 130), ability_active=False):
        self.radius = radius
        self.boss_class = boss_class
        self.color = color
        self.pulse = pulse
        self.enrage_pulse = enrage_pulse
        self.anim_time = anim_time
        self.ability_range = ability_range
        self.entrance_color = entrance_color
        self.ability_active = ability_active


def _module_source(text):
    """Harvest the cache helpers + phase bucketing, in source order."""
    tree = ast.parse(text)
    found = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in MODULE_MEMBERS:
            found[node.name] = node
        elif isinstance(node, (ast.Assign, ast.AnnAssign)) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in MODULE_MEMBERS:
                found[target.id] = node
    missing = set(MODULE_MEMBERS) - set(found)
    if missing:
        raise AssertionError("%s not found at module level of %s"
                             % (sorted(missing), SOURCE.name))
    return "".join(ast.get_source_segment(text, found[name]) + "\n" for name in MODULE_MEMBERS)


def _ability_block(text):
    """Lift `if self.ability_active:` out of `Boss.draw` so it can run on its own."""
    tree = ast.parse(text)
    owner = next((node for node in tree.body
                  if isinstance(node, ast.ClassDef) and node.name == NAMESPACE), None)
    if owner is None:
        raise AssertionError("%s not found in %s" % (NAMESPACE, SOURCE.name))
    draw = next((node for node in owner.body
                 if isinstance(node, ast.FunctionDef) and node.name == "draw"), None)
    if draw is None:
        raise AssertionError("%s.draw not found in %s" % (NAMESPACE, SOURCE.name))
    for node in ast.walk(draw):
        if (isinstance(node, ast.If) and isinstance(node.test, ast.Attribute)
                and node.test.attr == "ability_active"):
            return ast.get_source_segment(text, node)
    raise AssertionError("%s not found in %s.draw" % (ABILITY_GATE, SOURCE.name))


def _harvest_class(pygame, text):
    """Rebuild `Boss` from the harvested aura methods plus the lifted ability block."""
    found = {}
    owner = next(node for node in ast.parse(text).body
                 if isinstance(node, ast.ClassDef) and node.name == NAMESPACE)
    for node in owner.body:
        if isinstance(node, ast.FunctionDef) and node.name in CLASS_METHODS:
            found[node.name] = node
    missing = set(CLASS_METHODS) - set(found)
    if missing:
        raise AssertionError("%s not found in %s.%s" % (sorted(missing), SOURCE.name, NAMESPACE))
    body = "".join(
        textwrap.indent(textwrap.dedent(ast.get_source_segment(text, found[name], padded=True)),
                        "    ") + "\n"
        for name in CLASS_METHODS)
    body += "    def _draw_ability_aura(self, surface, x, y):\n"
    body += textwrap.indent(textwrap.dedent(_ability_block(text)), "        ") + "\n"
    namespace = {"pygame": pygame, "math": math}
    exec(compile(_module_source(text), SOURCE.name, "exec"), namespace)
    exec(compile("class %s:\n%s" % (NAMESPACE, body), SOURCE.name, "exec"), namespace)
    return namespace[NAMESPACE]


# (label, ability_range, anim_time, entrance_color). 350 = urgharun, 60 = a small boss.
ABILITY_FRAMES = [
    ("ability_full", 350, 0, (255, 200, 130)),
    ("ability_rising", 350, 8, (255, 200, 130)),
    ("ability_peak", 350, 20, (255, 200, 130)),
    ("ability_small", 60, 12, (120, 200, 255)),
]
# (label, radius, enrage_pulse, boss_class).
ENRAGE_FRAMES = [
    ("enrage_mini", 36, 0.0, "mini"),
    ("enrage_mini_late", 36, 12.3, "mini"),
    ("enrage_true", 36, 63.2, "true"),
    ("enrage_true_peak", 58, 1.5708, "true"),
    # radius + 14 - 18 < 5, so `max(5, aura_r - 18)` clamps the innermost ring.
    ("enrage_tiny_radius", 5, 1.5708, "mini"),
]
# (label, radius, pulse, color).
TRUE_BOSS_FRAMES = [
    ("true_aura_mini_clock", 36, 0.0, (255, 140, 60)),
    ("true_aura_peak", 36, 1.5708, (255, 140, 60)),
    ("true_aura_late", 58, 63.2, (120, 60, 200)),
]


def _record(frames, runner):
    out = []
    for frame in frames:
        screen = rec.Surface((1280, 720))
        runner(screen, frame)
        body = {"ops": screen.ops}
        body.update(frame)
        out.append(body)
    return out


def source_fixture():
    pygame = rec.make_pygame({"ticks": 0})
    text = SOURCE.read_text(encoding="utf-8")
    with rec.installed({"pygame": pygame}):
        boss_class = _harvest_class(pygame, text)

        ability = _record(
            [{"label": label, "ability_range": ability_range, "anim_time": anim_time,
              "entrance_color": list(entrance_color)}
             for label, ability_range, anim_time, entrance_color in ABILITY_FRAMES],
            lambda screen, frame: boss_class._draw_ability_aura(
                _Boss(ability_range=frame["ability_range"], anim_time=frame["anim_time"],
                      entrance_color=tuple(frame["entrance_color"]), ability_active=True),
                screen, 640, 360))
        enrage = _record(
            [{"label": label, "radius": radius, "enrage_pulse": enrage_pulse,
              "boss_class": boss_class_name}
             for label, radius, enrage_pulse, boss_class_name in ENRAGE_FRAMES],
            lambda screen, frame: boss_class._draw_enrage_aura(
                _Boss(radius=frame["radius"], boss_class=frame["boss_class"],
                      enrage_pulse=frame["enrage_pulse"]),
                screen, 640, 360))
        true_boss = _record(
            [{"label": label, "radius": radius, "pulse": pulse, "color": list(color)}
             for label, radius, pulse, color in TRUE_BOSS_FRAMES],
            lambda screen, frame: boss_class._draw_true_boss_aura(
                _Boss(radius=frame["radius"], pulse=frame["pulse"], color=tuple(frame["color"])),
                screen, 640, 360))
    return {
        "anchor": [640, 360],
        "ability_frames": ability,
        "enrage_frames": enrage,
        "true_boss_frames": true_boss,
    }


if __name__ == "__main__":
    FIXTURE.write_text(json.dumps(source_fixture(), indent=1) + "\n", encoding="utf-8")
    print("wrote", FIXTURE)
