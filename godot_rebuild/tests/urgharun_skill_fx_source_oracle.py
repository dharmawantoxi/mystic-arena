"""Source oracle for urgharun's remaining FX layers: LAYER 1 and the Q/W/E skill FX.

`bosses/level40.py::_NS_urgharun.draw_urgharun` paints, in this order:
  LAYER 1  `_draw_fury_aura` (aura surface + rage embers) and `_draw_ground_ring`
           (ring surface, plus a `fury_hot` ellipse while a skill is active),
  LAYER 2  the skill ground FX - Q `_draw_earthshock_ground`, R `_draw_enrage_ground`,
  LAYER 3  the body pose,
  LAYER 4  the skill foreground FX - Q `_draw_earthshock_fx`, W `_draw_overpower_fx`,
           E `_draw_furyswipes_fx`, R `_draw_enrage_fx`.
9bq4 pinned the R foreground, 9bq5 the R ground FX; this oracle pins LAYER 1 and the Q/W/E
skill FX. `_draw_basic_attack_fx` stays out of scope (it needs the `_urg_attack_progress`
swing state the rebuild does not carry).

The REAL members are harvested from the `_NS_urgharun` class body with `ast` and run under
the recording pygame shim of `draw_recorder.py`. W and E branch on `boss.target`: each
records one frame with a live target and one without, so both source branches are pinned.

Run: python godot_rebuild/tests/urgharun_skill_fx_source_oracle.py
"""
import ast
import json
import math
import textwrap
from pathlib import Path

import draw_recorder as rec

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "bosses" / "level40.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "urgharun_skill_fx_source.json"
NAMESPACE = "_NS_urgharun"
HARVESTED = (
    "HAS_AACIRCLE", "HAS_AALINES", "PALETTE", "_clamp", "_alpha", "_aacircle", "_poly",
    "_draw_fury_aura", "_draw_ground_ring",
    "_draw_earthshock_ground", "_draw_earthshock_fx",
    "_draw_overpower_fx", "_draw_furyswipes_fx",
)
PALETTE_KEYS = (
    "fury_darkest", "fury_dark", "fury_mid", "fury_light", "fury_hot", "fury_shine",
    "fur_darkest", "fur_mid", "shadow_deep", "white",
)


class _Target:
    """`boss.target`: only `x`, `y` and `alive` are read by the FX."""

    def __init__(self, x, y, alive=True):
        self.x, self.y, self.alive = x, y, alive


class _Boss:
    """Stand-in for the boss attributes the harvested functions read."""

    def __init__(self, direction=1, target=None, pulse=0.0):
        self.direction = direction
        self.target = target
        self.pulse = pulse


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

# (label, phase, enraged). 90 = the widest aura ring, 5 = the narrowest.
AURA_FRAMES = [
    ("aura_calm", 0.0, False),
    ("aura_calm_late", 21.4, False),
    ("aura_enraged", 0.0, True),
    ("aura_enraged_late", 63.2, True),
    ("aura_enraged_wrap", 133.9, True),
]
# (label, phase, skill). `skill` is the source's `active_skill` string (None = no cast).
RING_FRAMES = [
    ("ring_idle", 0.0, None),
    ("ring_idle_late", 12.3, None),
    ("ring_q", 0.0, "q"),
    ("ring_r", 57.1, "r"),
    ("ring_wrap", 133.9, "e"),
]
# (label, timer, phase). 55 = the Q cast window start, 1 = its last drawn tick.
EARTHSHOCK_GROUND_FRAMES = [
    ("q_ground_first", 55, 0.0),
    ("q_ground_mid", 30, 8.7),
    ("q_ground_late", 12, 40.1),
    ("q_ground_last", 1, 79.9),
]
EARTHSHOCK_FX_FRAMES = [
    ("q_fg_first", 55, 0.0),
    ("q_fg_debris", 30, 8.7),
    ("q_fg_cracks", 20, 40.1),
    ("q_fg_last", 1, 79.9),
]
# (label, timer, phase, direction, target). 50 = the W cast window, 40 the E one.
OVERPOWER_FRAMES = [
    ("w_first", 50, 0.0, 1, (700, 360)),
    ("w_late", 20, 12.3, -1, (580, 400)),
    ("w_no_target", 20, 12.3, 1, None),
    ("w_last", 1, 63.2, 1, (700, 360)),
]
FURYSWIPES_FRAMES = [
    ("e_first", 40, 0.0, 1, (700, 360)),
    ("e_mid", 25, 9.4, -1, (580, 340)),
    ("e_no_target", 25, 9.4, 1, None),
    ("e_far_target", 15, 30.7, 1, (1100, 600)),
    ("e_last", 1, 63.2, 1, (700, 360)),
]


def _record(pygame, namespace, frames, runner, label_key="label"):
    out = []
    for frame in frames:
        screen = rec.Surface((1280, 720))
        runner(namespace, screen, frame)
        body = {"ops": screen.ops}
        body.update(frame if isinstance(frame, dict) else {})
        out.append(body)
    return out


def source_fixture():
    pygame = rec.make_pygame({"ticks": 0})
    with rec.installed({"pygame": pygame}):
        namespace = _harvest_namespace(pygame)

        aura = _record(
            pygame, namespace,
            [{"label": label, "phase": phase, "enraged": enraged}
             for label, phase, enraged in AURA_FRAMES],
            lambda ns, screen, frame: ns._draw_fury_aura(
                screen, 640, 360, frame["phase"], frame["enraged"]))
        ring = _record(
            pygame, namespace,
            [{"label": label, "phase": phase, "skill": skill}
             for label, phase, skill in RING_FRAMES],
            # `draw_urgharun` passes `y + 50` as the ring anchor, so a boss at y = 360
            # records its ring at 410: the fixture keeps the value the view will pass.
            lambda ns, screen, frame: ns._draw_ground_ring(
                screen, 640, 360 + 50, frame["phase"], frame["skill"]))

        def run_earthshock_ground(ns, screen, frame):
            ns._draw_earthshock_ground(screen, None, 640, 360, frame["timer"], frame["phase"])

        def run_earthshock_fx(ns, screen, frame):
            ns._draw_earthshock_fx(screen, None, 640, 360, frame["timer"], frame["phase"])

        def run_overpower(ns, screen, frame):
            target = frame["target"]
            boss = _Boss(frame["direction"], None if target is None else _Target(*target),
                         frame["phase"])
            ns._draw_overpower_fx(screen, boss, 640, 360, frame["timer"], frame["phase"])

        def run_furyswipes(ns, screen, frame):
            target = frame["target"]
            boss = _Boss(frame["direction"], None if target is None else _Target(*target),
                         frame["phase"])
            ns._draw_furyswipes_fx(screen, boss, 640, 360, frame["timer"], frame["phase"])

        earthshock_ground = _record(
            pygame, namespace,
            [{"label": label, "timer": timer, "phase": phase}
             for label, timer, phase in EARTHSHOCK_GROUND_FRAMES],
            run_earthshock_ground)
        earthshock_fx = _record(
            pygame, namespace,
            [{"label": label, "timer": timer, "phase": phase}
             for label, timer, phase in EARTHSHOCK_FX_FRAMES],
            run_earthshock_fx)
        overpower = _record(
            pygame, namespace,
            [{"label": label, "timer": timer, "phase": phase, "direction": direction,
              "target": None if target is None else list(target)}
             for label, timer, phase, direction, target in OVERPOWER_FRAMES],
            run_overpower)
        furyswipes = _record(
            pygame, namespace,
            [{"label": label, "timer": timer, "phase": phase, "direction": direction,
              "target": None if target is None else list(target)}
             for label, timer, phase, direction, target in FURYSWIPES_FRAMES],
            run_furyswipes)

        palette = {key: list(namespace.PALETTE[key]) for key in PALETTE_KEYS}
    return {
        "source": "bosses/level40.py::_NS_urgharun (layer 1 + Q/W/E skill FX)",
        "boss_type": "urgharun",
        "anchor": [640, 360],
        "ring_anchor": [640, 410],
        "durations": {"q": 55, "w": 50, "e": 40},
        "palette": palette,
        "aura_frames": aura,
        "ring_frames": ring,
        "earthshock_ground_frames": earthshock_ground,
        "earthshock_fx_frames": earthshock_fx,
        "overpower_frames": overpower,
        "furyswipes_frames": furyswipes,
    }


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, separators=(",", ":")) + "\n", encoding="utf-8")
    groups = [key for key in fixture if key.endswith("_frames")]
    total = sum(len(frame["ops"]) for key in groups for frame in fixture[key])
    print("wrote %s (%d frames, %d ops)" % (
        FIXTURE.relative_to(ROOT), sum(len(fixture[key]) for key in groups), total))


if __name__ == "__main__":
    main()
