"""Read-only source oracle for the cannon splash/burn arm reaching the boss.

Executes the real `Bullet._on_hit` cannon branch from `_entity.py` (via
`cannon_source_oracle.build_env`) with the real `Boss` from
`boss_core_source_oracle` as a SECONDARY victim standing next to the primary
target, which is the shape the source splash loop actually runs in.

The source facts this fixture pins:

* `Tower.update` hands `all_units` to its bullets and `Game.update` ends that
  list with the live boss, so the boss is one of the splash candidates;
* the splash loop keeps every enemy inside `d <= splash_radius` (inclusive),
  skipping the primary target, allies and corpses, and hits with
  `u.take_damage(int(self.damage * 0.6), self.team)` - no `school=`, no
  `source=`, so `Boss.take_damage` skips armor/magic-resist mitigation;
* a splashed victim also burns through `u.apply_debuff('burn', ...,
  source_team=self.team)`, which for a boss is `Boss.apply_debuff` ->
  `TowerDebuffMixin.apply_debuff` (strongest wins, duration refresh, burn team
  recorded);
* a lethal splash writes `self._killed_by = source`, and `source` is `None`
  here, so a splash kill credits nobody - the hero that wounded the boss before
  is NOT kept.

Four scenarios are recorded per boss type, each with the same world replayed
without the boss in `all_units` (the native candidate list before this layer)
and with the splash delivered under a declared physical school (what a port that
forgets `resolve_damage_school` would produce). `--write` rewrites the fixture.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

FIXTURE = Path(__file__).parent / "fixtures/boss_cannon_splash_source.json"

MAIN = (560.0, 340.0)
SHOOTER_TEAM = "blue"
VICTIM_TEAM = "red"
CANNON_TABLE = "CANNON_LEVELS"
CANNON_LEVEL = 6

# (label, boss distance as a function of the source splash radius, forced hp).
SCENARIOS = (
    ("splash_inside_half", lambda radius: radius * 0.5, None),
    ("splash_edge_inclusive", lambda radius: radius, None),
    ("splash_outside", lambda radius: radius + 1.0, None),
    ("splash_lethal_no_source", lambda radius: radius * 0.5, 1.0),
)

EXPECTED_HIT = {
    "splash_inside_half": True,
    "splash_edge_inclusive": True,
    "splash_outside": False,
    "splash_lethal_no_source": True,
}


def _nodes(source_file):
    return ast.parse((ROOT / source_file).read_text(encoding="utf-8")).body


def _method_node(class_name, method_name, source_file="_entity.py"):
    original = next(
        node for node in _nodes(source_file) if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    return next(
        node
        for node in original.body
        if isinstance(node, ast.FunctionDef) and node.name == method_name
    )


def on_hit_text():
    return ast.unparse(_method_node("Bullet", "_on_hit"))


def boss_take_damage_text():
    return ast.unparse(_method_node("Boss", "take_damage", "bosses/base_boss.py"))


def game_update_text():
    return ast.unparse(_method_node("Game", "update", "_core.py"))


def tower_update_text():
    return ast.unparse(_method_node("Tower", "update"))


def build_env():
    from cannon_source_oracle import build_env as cannon_env

    return cannon_env()


def boss_env():
    from boss_core_source_oracle import boss_class, namespace

    env = namespace()
    return env, boss_class(env)


def make_main(env):
    from cannon_source_oracle import make_victim

    return make_victim(env, 1, MAIN[0], MAIN[1], team=VICTIM_TEAM, hp=100000)


def make_shot(env, main):
    stats = env[CANNON_TABLE][CANNON_LEVEL]
    bullet = env["SourceBullet"].__new__(env["SourceBullet"])
    bullet.x, bullet.y = 0.0, 0.0
    bullet.target = main
    bullet.damage = int(stats["damage"])
    bullet.team = SHOOTER_TEAM
    bullet.speed, bullet.active = 8, True
    bullet.bullet_type = "cannon"
    bullet.special_data = {
        "splash": stats["splash"],
        "burn_dps": stats["burn_dps"],
        "burn_duration": stats["burn_duration"],
    }
    return bullet


def boss_state(boss):
    return {
        "hp": float(boss.hp),
        "alive": bool(boss.alive),
        "burn_dps": float(getattr(boss, "burn_dps", 0.0)),
        "burn_timer": int(getattr(boss, "burn_timer", 0)),
        "burn_team": str(getattr(boss, "burn_team", None)),
        "killed_by_none": getattr(boss, "_killed_by", "unset") is None,
    }


def splash_cases(env, boss_cls):
    from bosses.boss_data import get_all_boss_types

    stats = env[CANNON_TABLE][CANNON_LEVEL]
    radius = float(stats["splash"])
    splash_damage = int(int(stats["damage"]) * 0.6)
    cases = []
    for kind in sorted(get_all_boss_types()):
        for label, distance_of, forced_hp in SCENARIOS:
            distance = distance_of(radius)
            main = make_main(env)
            boss = boss_cls(kind, None)
            boss.x = MAIN[0] + distance
            boss.y = MAIN[1]
            if forced_hp is not None:
                boss.hp = forced_hp
            hp_before = float(boss.hp)
            make_shot(env, main)._on_hit([main, boss])
            # Same world, boss left out of all_units: the pre-layer native list.
            without_main = make_main(env)
            without_boss = boss_cls(kind, None)
            without_boss.x = MAIN[0] + distance
            without_boss.y = MAIN[1]
            if forced_hp is not None:
                without_boss.hp = forced_hp
            make_shot(env, without_main)._on_hit([without_main])
            # What a declared-school splash would have taken off instead.
            contrast = boss_cls(kind, None)
            if forced_hp is not None:
                contrast.hp = forced_hp
            contrast.take_damage(
                splash_damage, SHOOTER_TEAM, damage_type="normal", school="physical"
            )
            hit = boss_state(boss)
            baseline = boss_state(without_boss)
            assert (hit["hp"] < hp_before) is EXPECTED_HIT[label], (
                "%s source splash drifted" % label
            )
            assert baseline["hp"] == hp_before, "boss omission case must stay untouched"
            cases.append(
                {
                    "boss_type": kind,
                    "label": label,
                    "distance": distance,
                    "splash_radius": radius,
                    "raw_damage": int(stats["damage"]),
                    "splash_damage": splash_damage,
                    "burn_dps_in": float(stats["burn_dps"]),
                    "burn_duration_in": int(stats["burn_duration"]),
                    "hp_before": hp_before,
                    "expected": hit,
                    "expected_without_boss": baseline,
                    "expected_physical_hp_after": float(contrast.hp),
                }
            )
    return cases


SOURCE_FLAGS = {
    "tower_passes_all_units": lambda: "b.update(all_units)" in tower_update_text(),
    "all_units_includes_boss": lambda: "all_units = all_units + [self.active_boss]"
    in game_update_text(),
    "splash_damage_scale": lambda: "u.take_damage(int(self.damage * 0.6), self.team)"
    in on_hit_text(),
    "splash_radius_inclusive": lambda: "if d <= splash_radius:" in on_hit_text(),
    "splash_skips_main_allies_dead": lambda: (
        "if u == self.target or u.team == self.team or (not u.alive):" in on_hit_text()
    ),
    "splash_hit_has_no_source": lambda: "source=" not in on_hit_text(),
    "splash_burn_uses_source_team": lambda: (
        "u.apply_debuff('burn', burn_dps, burn_duration, source_team=self.team)" in on_hit_text()
    ),
    "burn_gated_by_dps": lambda: "if burn_dps > 0 and hasattr(u, 'apply_debuff'):" in on_hit_text(),
    "kill_credit_written_on_lethal": lambda: "self._killed_by = source"
    in boss_take_damage_text(),
}


def source_fixture():
    env = build_env()
    _env, boss_cls = boss_env()
    flags = {name: bool(check()) for name, check in SOURCE_FLAGS.items()}
    for name, value in flags.items():
        assert value, "source shape drifted: %s" % name
    stats = env[CANNON_TABLE][CANNON_LEVEL]
    return {
        "source": dict(
            flags,
            **{
                "cannon": {
                    "level": CANNON_LEVEL,
                    "damage": int(stats["damage"]),
                    "splash": float(stats["splash"]),
                    "burn_dps": float(stats["burn_dps"]),
                    "burn_duration": int(stats["burn_duration"]),
                    "splash_damage": int(int(stats["damage"]) * 0.6),
                }
            },
        ),
        "cases": splash_cases(env, boss_cls),
    }


def main():
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print("WROTE: %s (%d cases)" % (FIXTURE, len(actual["cases"])))
    else:
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), (
            "Boss cannon splash source drift"
        )
        print(
            "PASS: Boss cannon splash — %d cases across %d boss types"
            % (len(actual["cases"]), len({row["boss_type"] for row in actual["cases"]}))
        )


if __name__ == "__main__":
    main()
