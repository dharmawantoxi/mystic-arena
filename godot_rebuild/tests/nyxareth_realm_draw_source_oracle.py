"""Source oracle for nyxareth's full-screen ultimate layer (layer 9bq3).

`bosses/level17.py::_NS_nyxareth.draw_nyxareth` calls `_draw_astro_realm_bg` while the
smart ultimate "4" is active, after the cosmic aura and ground ring and before the skill
ground FX and the body. The layer fills the WHOLE render surface with
`PALETTE["cosmic_darkest"]` (an SRCALPHA layer whose alpha grows from 50 to 80) and
scatters 60 stars over it (every fifth one a bright cross). The boss atlas bake skips it
(`SCREEN_LAYERS` in `bake/bake_boss_atlas.py`), so `scripts/ui/nyxareth_realm_layout.gd`
paints it natively in screen space.

The REAL `PALETTE`, `_alpha` and `_draw_astro_realm_bg` are harvested from the
`_NS_nyxareth` class body with `ast` and run under the recording pygame shim of
`draw_recorder.py`. Each frame is one `(timer, phase, screen)` sample: `timer` is
`active_skill_timer` (the AI casts "4" for 95 ticks; the layer still normalises by its own
`duration = 120`), `phase` is the boss `pulse` (+0.1 per tick) and the screen size is the
render surface (`surface.get_size()`; 1280x720, plus one widened display).

Run: python godot_rebuild/tests/nyxareth_realm_draw_source_oracle.py
"""
import ast
import json
import math
import textwrap
from pathlib import Path

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "bosses" / "level17.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "nyxareth_realm_draw_source.json"
NAMESPACE = "_NS_nyxareth"
HARVESTED = ("PALETTE", "_alpha", "_draw_astro_realm_bg")

# (label, active_skill_timer, pulse, screen width, screen height). 95 = first cast tick
# (progress 0.208: layer alpha 50, stars at 41.7 %), 80 = stars full, 60 = layer full,
# 1 = last drawn tick. Large pulses move the stars and exercise the float modulo wrap.
FRAMES = [
    ("cast", 95, 0.0, 1280, 720),
    ("early", 88, 4.7, 1280, 720),
    ("stars_full", 80, 12.3, 1280, 720),
    ("layer_full", 60, 57.1, 1280, 720),
    ("late", 33, 133.9, 1280, 720),
    ("last", 1, 257.9, 1280, 720),
    ("wide_display", 70, 91.4, 1560, 720),
]


def _harvest_namespace(pygame):
    """`_NS_nyxareth` rebuilt from only the harvested members, exactly as written."""
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
        realm = _harvest_namespace(pygame)
        frames = []
        for label, timer, phase, width, height in FRAMES:
            screen = rec.Surface((width, height))
            # `boss`, `x` and `y` are unused by the layer: it only reads the surface size.
            realm._draw_astro_realm_bg(screen, None, 640, 360, timer, phase)
            frames.append({"label": label, "timer": timer, "phase": phase,
                           "screen": [width, height], "ops": screen.ops})
    palette = realm.PALETTE
    return {
        "source": "bosses/level17.py::_NS_nyxareth._draw_astro_realm_bg",
        "skill": "4",
        "palette": {key: list(palette[key])
                    for key in ("cosmic_darkest", "star_mid", "star_bright")},
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
