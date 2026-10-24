"""Source oracle for the tactical command visuals (layer 9bi2).

`tactical_commands.py::TacticalCommandManager` paints two things:
  * `draw_world` (world layer, after `effects.draw`, shaken with the map): the gather marker
    (rings r = 50..26 step -8 whose alpha gates them, a 6 px command-colour disc with a 2 px
    white core) and three dashes from every blue hero further than 80 px from it while the
    command is GATHER / PROTECT_CASTLE / ATTACK_BOSS / PROTECT_TOWER;
  * `draw_ui` (UI layer, right after `effects.draw_ui`): the feedback banner, 28 px
    `body_bold` text centred on (640, 90 + slide) over a black box (`inflate(20, 8)`, alpha
    160 * a / 255), a 2 px rounded border in the feedback colour and a black shadow at +2 px.

The REAL `TacticalCommand`, `_get_command_color`, `draw_world` and `draw_ui` are harvested
with `ast` and run under the recording pygame shim of `draw_recorder.py` (text measured with
its fake `0.55 * size` glyphs). Heroes come from a stand-in `_get_alive_blue_heroes`; the
wall clock (`pygame.time.get_ticks()`) is set per frame.

Run: python godot_rebuild/tests/tactical_draw_source_oracle.py
"""
import ast
import json
import math
import textwrap
import types
from pathlib import Path
from types import SimpleNamespace

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tactical_commands.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "tactical_draw_source.json"
MANAGER = "TacticalCommandManager"
HARVESTED = ("_get_command_color", "draw_world", "draw_ui")
COMMANDS = ("gather", "protect_tower", "protect_castle", "attack_boss", "attack_damage_dealer")

HEROES = [(200, 300), (430, 320), (700, 500), (95, 610)]
# (label, active command or None, gather point or None, gather_point_timer, get_ticks, heroes)
WORLD_FRAMES = [
    ("gather_fresh", "gather", (420, 300), 150, 0, HEROES),
    ("gather_mid", "gather", (420, 300), 100, 1234, HEROES),
    ("gather_faint", "gather", (420, 300), 3, 800, HEROES),
    ("tower", "protect_tower", (900, 250), 120, 777, [(500, 500), (880, 240)]),
    ("castle_fade", "protect_castle", (180, 600), 40, 2500, [(600, 200), (190, 590)]),
    ("boss", "attack_boss", (640, 360), 75, 3333, [(100, 100), (1200, 700)]),
    ("dealer_no_dashes", "attack_damage_dealer", (300, 400), 90, 4100, [(800, 100)]),
    ("expired_command", None, (500, 500), 60, 5000, [(100, 100)]),
    ("timer_out", "gather", (420, 300), 0, 900, HEROES),
    ("no_point", "gather", None, 50, 900, HEROES),
]
GATHER_TEXT = "GATHER! 3 heroes regrouping!"
CASTLE_TEXT = "PROTECT CASTLE! 4 heroes defending base!"
# (label, feedback text, feedback colour, feedback_timer). 180 = issued this tick (alpha 0,
# 20 px low), 151..180 slide in, 30..150 hold, below 30 fade out.
FEEDBACK_FRAMES = [
    ("issued", GATHER_TEXT, (100, 220, 255), 180),
    ("sliding", GATHER_TEXT, (100, 220, 255), 170),
    ("almost_in", GATHER_TEXT, (100, 220, 255), 151),
    ("held", GATHER_TEXT, (100, 220, 255), 150),
    ("refused", "No boss active!", (255, 100, 100), 90),
    ("fading", CASTLE_TEXT, (255, 220, 50), 29),
    ("last", CASTLE_TEXT, (255, 220, 50), 1),
    ("off", CASTLE_TEXT, (255, 220, 50), 0),
]


def _harvest_manager(pygame):
    """`TacticalCommandManager` rebuilt from only the harvested drawing members."""
    text = SOURCE.read_text(encoding="utf-8")
    owner = next((node for node in ast.parse(text).body
                  if isinstance(node, ast.ClassDef) and node.name == MANAGER), None)
    if owner is None:
        raise AssertionError("%s not found in %s" % (MANAGER, SOURCE.name))
    found = {node.name: node for node in owner.body
             if isinstance(node, ast.FunctionDef) and node.name in HARVESTED}
    missing = set(HARVESTED) - set(found)
    if missing:
        raise AssertionError("%s not found in %s.%s" % (sorted(missing), SOURCE.name, MANAGER))
    body = "".join(
        textwrap.indent(textwrap.dedent(ast.get_source_segment(text, found[name], padded=True)),
                        "    ") + "\n"
        for name in HARVESTED)
    body += "    def _get_alive_blue_heroes(self):\n        return self.heroes\n"
    namespace = {"pygame": pygame, "math": math}
    for segment in rec.harvest(SOURCE, ["TacticalCommand"]):
        exec(compile(segment, SOURCE.name, "exec"), namespace)
    exec(compile("class %s:\n%s" % (MANAGER, body), SOURCE.name, "exec"), namespace)
    return namespace[MANAGER]


def _manager(cls, **state):
    manager = cls()
    defaults = {"active_command": None, "gather_point": None, "gather_point_timer": 0,
                "heroes": [], "feedback_timer": 0, "feedback_text": "",
                "feedback_color": (255, 220, 100)}
    defaults.update(state)
    for name, value in defaults.items():
        setattr(manager, name, value)
    return manager


def source_fixture():
    clock = {"ticks": 0}
    pygame = rec.make_pygame(clock)
    render = types.ModuleType("_render")
    render.get_font = lambda size, style="body", bold=False: rec.Font(size, style)
    with rec.installed({"pygame": pygame, "_render": render}):
        cls = _harvest_manager(pygame)
        colors = {(command or ""): list(_manager(cls, active_command=command)._get_command_color())
                  for command in (*COMMANDS, None)}
        world_frames = []
        for label, command, point, timer, ticks, heroes in WORLD_FRAMES:
            clock["ticks"] = ticks
            manager = _manager(cls, active_command=command, gather_point=point,
                               gather_point_timer=timer,
                               heroes=[SimpleNamespace(x=float(x), y=float(y)) for x, y in heroes])
            screen = rec.Surface((1280, 720))
            manager.draw_world(screen)
            world_frames.append({
                "label": label, "command": command or "",
                "point": list(point) if point else None, "timer": timer, "ticks": ticks,
                "heroes": [list(hero) for hero in heroes], "ops": screen.ops})
        feedback_frames = []
        for label, text, color, timer in FEEDBACK_FRAMES:
            manager = _manager(cls, feedback_text=text, feedback_color=color, feedback_timer=timer)
            screen = rec.Surface((1280, 720))
            manager.draw_ui(screen)
            feedback_frames.append({"label": label, "text": text, "color": list(color),
                                    "timer": timer, "ops": screen.ops})
    return {
        "source": "tactical_commands.py::TacticalCommandManager.draw_world / draw_ui",
        "glyph_factor": rec.GLYPH_FACTOR,
        "colors": colors,
        "world_frames": world_frames,
        "feedback_frames": feedback_frames,
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, separators=(",", ":")) + "\n", encoding="utf-8")
    frames = fixture["world_frames"] + fixture["feedback_frames"]
    print("wrote %s (%d frames, %d ops)" % (FIXTURE.relative_to(ROOT), len(frames),
                                            sum(len(frame["ops"]) for frame in frames)))


if __name__ == "__main__":
    main()
