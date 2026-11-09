#!/usr/bin/env python3
"""Execute Zephyr director state/attack-phase/swing-event AST (not full director)."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import types
import prepare_godot_zephyr_particles as particles

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "heroes/zephyr_fx.py"
OUTPUT = ROOT / "godot_rebuild/tests/fixtures/zephyr_director.json"
CONFIG = ROOT / "godot_rebuild/data/zephyr_director.json"
FIELDS = ("state", "prev_state", "state_time", "anim_phase", "swing_active", "_swing_seen")
DEFAULTS = {"alive": True, "active_skill": None, "_zp_attack_active": False,
            "_zp_attack_progress": 0.0, "_moving_cached": False, "speed": 1.0,
            "x": 30.75, "y": -20.25, "facing": 1}


def environment():
    env, _ = particles.environment()
    tree = ast.parse(SOURCE.read_text())
    constants = [n for n in tree.body if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id in ("ANIM_PRIORITY", "ATTACK_PHASES") for t in n.targets)]
    phase = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "attack_phase")
    director = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ZephyrFXDirector")
    update = next(n for n in director.body if isinstance(n, ast.FunctionDef) and n.name == "update")
    index = next(i for i, n in enumerate(update.body) if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "swinging" for t in n.targets))
    hero_assignment = next(n for n in update.body if isinstance(n, ast.Assign)
                           and any(isinstance(t, ast.Name) and t.id == "h" for t in n.targets))
    update.body = [hero_assignment, *update.body[index:index + 3]]
    director.body = [n for n in director.body if isinstance(n, ast.FunctionDef) and n.name in (
        "__init__", "_resolve_state", "_update_state", "on_swing_start", "on_swing_end", "update")]
    env.update(ProjectileSystem=lambda _particles: None,
               SwingTrail=lambda: types.SimpleNamespace(reset=lambda: None))
    exec(compile(ast.Module(body=[*constants, phase, director], type_ignores=[]), str(SOURCE), "exec"), env)
    return env


def build():
    sequences = [
        [{}, {"_moving_cached": True}, {"_moving_cached": True, "speed": 2.2},
         *[{"_zp_attack_active": True, "_zp_attack_progress": p, "dt": .04 if p == .7 else .016} for p in (.1, .2, .35, .55, .7, .9)],
         {"active_skill": "q"}, {"active_skill": "r"}, {"hit_flash": .1}, {"alive": False}, {}],
        [{"hit_flash": .1, "dt": .05}, {"dt": 0}, {"dt": .000001}, {"dt": .016}],
        [{"_zp_attack_active": True, "_zp_attack_progress": .4, "facing": -1},
         {"_zp_attack_active": True, "_zp_attack_progress": .5, "facing": -1},
         {}, {"_zp_attack_active": True, "_zp_attack_progress": .58, "facing": -1}, {}],
        [{"_zp_attack_active": True, "_zp_attack_progress": p} for p in (-1, .16, .34, .52, .60, .80, 1, 2)],
    ]
    cases = []
    for sequence in sequences:
        env = environment()
        owner = env["ZephyrFXDirector"](types.SimpleNamespace(**DEFAULTS))
        bursts = []
        owner.particles = types.SimpleNamespace(burst=lambda x, y, count, **options:
            bursts.append({"position": [x, y], "count": count, "options": options}))
        rows = []
        for overrides in sequence:
            inputs = dict(DEFAULTS)
            inputs.update({k: v for k, v in overrides.items() if k not in ("dt", "hit_flash")})
            dt = overrides.get("dt", .016)
            hit_flash = overrides.get("hit_flash", 0.0)
            owner.hero = types.SimpleNamespace(**inputs)
            owner.hit_flash = hit_flash
            previous = owner._swing_seen
            bursts.clear()
            owner._update_state(dt)
            owner.update(dt)
            edge = "start" if owner._swing_seen and not previous else "end" if previous and not owner._swing_seen else ""
            rows.append({"input": {**inputs, "hit_flash": hit_flash}, "dt": dt,
                         "expected": {"state": {k: getattr(owner, k) for k in FIELDS},
                                      "edge": edge, "bursts": list(bursts)}})
        cases.append(rows)
    env = environment()
    config = {"priority": env["ANIM_PRIORITY"], "attack_phases": env["ATTACK_PHASES"]}
    fixture = {"schema": 1, "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
               "scope": "director priority state and swing edges/burst only; not full director/rig",
               "cases": cases}
    return json.loads(json.dumps(fixture)), json.loads(json.dumps(config))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    fixture, config = build()
    for path, value in ((OUTPUT, fixture), (CONFIG, config)):
        text = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.check:
            if not path.exists() or path.read_text() != text:
                parser.exit(1, f"Zephyr director oracle/config drift: {path}\n")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    print("Zephyr director state/swing oracle OK")


if __name__ == "__main__":
    main()
