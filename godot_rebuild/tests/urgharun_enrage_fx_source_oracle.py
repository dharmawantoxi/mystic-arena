"""Source oracle for urgharun's R/enrage foreground FX (layer 9bq4).

`bosses/level40.py::_NS_urgharun.draw_urgharun` paints four layers:
  * LAYER 1 fury aura + ground ring,
  * LAYER 2 the skill ground FX (`_draw_enrage_ground` while `active_skill == "r"`),
  * LAYER 3 the body pose,
  * LAYER 4 the skill foreground FX (`_draw_enrage_fx` while `active_skill == "r"`).
`Boss.draw` then paints the HP bar and the name plate, so the foreground layer sits OVER
the body and UNDER the bar. This oracle pins only that LAYER 4 function for urgharun's R.

The REAL `HAS_AACIRCLE`, `PALETTE`, `_clamp`, `_alpha`, `_aacircle` and `_draw_enrage_fx`
are harvested from the `_NS_urgharun` class body with `ast` and run under the recording
pygame shim of `draw_recorder.py` (the shim has no `pygame.draw.aacircle`, so the namespace
falls back to `pygame.draw.circle` exactly like a pygame build without the AA helper).

Each frame is one `(timer, pulse, x, y)` sample: `timer` is the boss's
`active_skill_timer` (the source normalises it by its own `duration = 80` and then never
reads the result), `pulse` is the boss `pulse` (+0.1 per tick) and `x`/`y` are the int
anchor `Boss.draw` passes to the renderer.

Run: python godot_rebuild/tests/urgharun_enrage_fx_source_oracle.py
"""
import ast
import json
import math
import textwrap
from pathlib import Path

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "bosses" / "level40.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "urgharun_enrage_fx_source.json"
NAMESPACE = "_NS_urgharun"
HARVESTED = ("HAS_AACIRCLE", "PALETTE", "_clamp", "_alpha", "_aacircle", "_draw_enrage_fx")
PALETTE_KEYS = ("fury_dark", "fury_mid", "fury_light", "fury_hot", "fury_shine")

# (label, active_skill_timer, pulse, x, y). 80 = the source's own duration (first tick),
# 1 = last drawn tick. "timer_ignored" reuses `mid`'s pulse with a different timer: the
# source computes `progress` from the timer and never uses it, so both frames must be
# identical. Pulses above 1.0 wrap the per-flame / per-ember `% 1.0` phases.
FRAMES = [
    ("cast", 80, 0.0, 640, 360),
    ("early", 72, 3.7, 640, 360),
    ("mid", 40, 21.4, 640, 360),
    ("late", 12, 63.2, 640, 360),
    ("last", 1, 79.9, 640, 360),
    ("timer_ignored", 5, 21.4, 640, 360),
    ("edge_anchor", 33, 133.9, 60, 700),
]


def _harvest_namespace(pygame):
    """`_NS_urgharun` rebuilt from only the harvested members, exactly as written."""
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


def source_fixture():
    pygame = rec.make_pygame({"ticks": 0})
    with rec.installed({"pygame": pygame}):
        namespace = _harvest_namespace(pygame)
        frames = []
        for label, timer, pulse, x, y in FRAMES:
            screen = rec.Surface((1280, 720))
            # `boss` is unused by the foreground layer: it is a pure function of the
            # anchor, the cast timer and the pulse.
            namespace._draw_enrage_fx(screen, None, x, y, timer, pulse)
            frames.append({"label": label, "timer": timer, "pulse": pulse,
                           "anchor": [x, y], "ops": screen.ops})
        palette = {key: list(namespace.PALETTE[key]) for key in PALETTE_KEYS}
    return {
        "source": "bosses/level40.py::_NS_urgharun._draw_enrage_fx",
        "boss_type": "urgharun",
        "skill": "r",
        "duration": 80,
        "palette": palette,
        "frames": frames,
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, separators=(",", ":")) + "\n", encoding="utf-8")
    drawn = sum(len(frame["ops"]) for frame in fixture["frames"])
    print("wrote %s (%d frames, %d ops)" % (FIXTURE.relative_to(ROOT), len(fixture["frames"]),
                                            drawn))


if __name__ == "__main__":
    main()
