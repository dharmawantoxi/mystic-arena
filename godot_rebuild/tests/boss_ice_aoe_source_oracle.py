"""Read-only source oracle for the ice-tower freeze AOE reaching the boss.

Executes the real `Bullet._on_hit` ice branch from `_entity.py` (via
`cannon_source_oracle.build_env`, which already AST-extracts `Bullet.__init__`
and `_on_hit` together with the real `Minion.take_damage`), on top of the real
`Boss` entity built by `boss_core_source_oracle`.

The source facts this fixture pins:

* `Tower.update` runs `b.update(all_units)`, and `Game.update` builds
  `all_units = self.minions + all_heroes + [self.active_boss]`, so a live boss
  is one of the AOE candidates of `Bullet._on_hit`;
* the level-6 ice AOE arm is gated by `'slow_aoe' in self.special_data and
  all_units` and keeps every enemy inside `d <= aoe` (inclusive), skipping the
  primary target, allies and corpses;
* the victims are slowed polymorphically - `u.apply_slow(...)` and
  `u.apply_debuff('atk_slow', ...)` - so a boss runs `Boss.apply_slow` /
  `Boss.apply_debuff`, which cut magnitude and duration by tenacity (0.50) and
  cap the magnitude at 0.35;
* below level 6 there is no `slow_aoe` key at all (`Tower._shoot_ice` only adds
  it when `self.slow_aoe > 0`), so an adjacent boss is never touched by an AOE
  arm that does not exist;
* `Castle.update` calls `b.update()` with no `all_units`, so the nexus never has
  AOE candidates at all.

Four scenarios are recorded per boss type. Every row also replays the same
world with the boss left out of `all_units` - the native candidate list before
this layer - so the fixture proves the boss arm is what changes the outcome.
`--write` rewrites the fixture.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

FIXTURE = Path(__file__).parent / "fixtures/boss_ice_aoe_source.json"

# Primary target of the shot: an enemy of the blue tower, at a fixed spot, so
# the boss offset below is exactly the AOE distance the source measures.
MAIN = (560.0, 340.0)
SHOOTER_TEAM = "blue"
VICTIM_TEAM = "red"
AOE_LEVEL = 6
NO_AOE_LEVEL = 5

# (label, tower level, boss distance as a function of the source slow_aoe).
SCENARIOS = (
    ("aoe_inside_half", AOE_LEVEL, lambda aoe: aoe * 0.5),
    ("aoe_edge_inclusive", AOE_LEVEL, lambda aoe: aoe),
    ("aoe_outside", AOE_LEVEL, lambda aoe: aoe + 1.0),
    ("no_aoe_below_level_six", NO_AOE_LEVEL, lambda _aoe: 10.0),
)

EXPECTED = {
    "aoe_inside_half": True,
    "aoe_edge_inclusive": True,
    "aoe_outside": False,
    "no_aoe_below_level_six": False,
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


def _module(*nodes):
    return compile(
        ast.fix_missing_locations(ast.Module(body=list(nodes), type_ignores=[])),
        "<source ice aoe>",
        "exec",
    )


def build_env():
    """Cannon oracle env (real Bullet/Tower/victim) plus the mixin `apply_slow`."""
    from cannon_source_oracle import build_env as cannon_env

    env = cannon_env()
    # `Bullet._on_hit` slows its victims through `apply_slow`, which the cannon
    # oracle never needed; bind the real mixin method onto the victim base.
    node = _method_node("TowerDebuffMixin", "apply_slow", "_core.py")
    exec(_module(node), env)  # noqa: S102 - executing the original source method
    env["SourceDebuffs"].apply_slow = env["apply_slow"]
    return env


def boss_env():
    from boss_core_source_oracle import boss_class, namespace

    env = namespace()
    return env, boss_class(env)


def make_main_victim(env):
    from cannon_source_oracle import make_victim

    return make_victim(env, 1, MAIN[0], MAIN[1], team=VICTIM_TEAM, hp=10000)


def ice_special(env, level):
    """`Tower._shoot_ice` special_data for one ice level, from ICE_LEVELS."""
    stats = env["ICE_LEVELS"][level]
    special = {"slow": stats["slow"], "slow_duration": stats["slow_duration"]}
    if stats.get("atk_slow", 0) > 0:
        special["atk_slow"] = stats["atk_slow"]
    if stats.get("slow_aoe", 0) > 0:
        special["slow_aoe"] = stats["slow_aoe"]
    return special


def make_shot(env, main, level):
    bullet = env["SourceBullet"].__new__(env["SourceBullet"])
    bullet.x, bullet.y = 0.0, 0.0
    bullet.target = main
    bullet.damage = int(env["ICE_LEVELS"][level]["damage"])
    bullet.team = SHOOTER_TEAM
    bullet.speed, bullet.active = 8, True
    bullet.bullet_type = "ice"
    bullet.special_data = ice_special(env, level)
    return bullet


def slow_state(unit):
    return {
        "slow_amount": float(getattr(unit, "slow_amount", 0.0)),
        "slow_timer": int(getattr(unit, "slow_timer", 0)),
        "atk_slow_amount": float(getattr(unit, "atk_slow_amount", 0.0)),
        "atk_slow_timer": int(getattr(unit, "atk_slow_timer", 0)),
    }


def aoe_cases(env, boss_cls):
    from bosses.boss_data import get_all_boss_types

    aoe = float(env["ICE_LEVELS"][AOE_LEVEL]["slow_aoe"])
    cases = []
    for kind in sorted(get_all_boss_types()):
        for label, level, distance_of in SCENARIOS:
            distance = distance_of(aoe)
            main = make_main_victim(env)
            boss = boss_cls(kind, None)
            boss.x = MAIN[0] + distance
            boss.y = MAIN[1]
            make_shot(env, main, level)._on_hit([main, boss])
            without_main = make_main_victim(env)
            without_boss = boss_cls(kind, None)
            without_boss.x = MAIN[0] + distance
            without_boss.y = MAIN[1]
            # Baseline: the boss left out of `all_units`, which is what the
            # native candidate list held before this layer.
            make_shot(env, without_main, level)._on_hit([without_main])
            stores = slow_state(boss)
            baseline = slow_state(without_boss)
            slowed = stores["slow_timer"] > 0
            assert slowed is EXPECTED[label], "%s source AOE drifted" % label
            assert baseline["slow_timer"] == 0, "boss omission case must stay clean"
            cases.append(
                {
                    "boss_type": kind,
                    "label": label,
                    "level": level,
                    "distance": distance,
                    "slow_aoe": float(env["ICE_LEVELS"][level].get("slow_aoe", 0)),
                    "slow_amount_in": float(env["ICE_LEVELS"][level]["slow"]),
                    "slow_duration_in": int(env["ICE_LEVELS"][level]["slow_duration"]),
                    "atk_slow_in": float(env["ICE_LEVELS"][level].get("atk_slow", 0)),
                    "tenacity": float(boss.tenacity),
                    "expected": stores,
                    "expected_without_boss": baseline,
                    "main_slowed": slow_state(main)["slow_timer"] > 0,
                }
            )
    return cases


def on_hit_text():
    return ast.unparse(_method_node("Bullet", "_on_hit"))


def tower_update_text():
    return ast.unparse(_method_node("Tower", "update"))


def castle_update_text():
    return ast.unparse(_method_node("Castle", "update"))


def shoot_ice_text():
    return ast.unparse(_method_node("Tower", "_shoot_ice"))


def game_update_text():
    return ast.unparse(_method_node("Game", "update", "_core.py"))


def boss_apply_slow_text():
    return ast.unparse(_method_node("Boss", "apply_slow", "bosses/base_boss.py"))


SOURCE_FLAGS = {
    "tower_passes_all_units": lambda: "b.update(all_units)" in tower_update_text(),
    "castle_omits_all_units": lambda: "b.update()" in castle_update_text(),
    "all_units_includes_boss": lambda: "all_units = all_units + [self.active_boss]"
    in game_update_text(),
    "ice_aoe_gated": lambda: "if 'slow_aoe' in self.special_data and all_units:" in on_hit_text(),
    "ice_aoe_radius_inclusive": lambda: "if d <= aoe:" in on_hit_text(),
    "ice_aoe_skips_main_allies_dead": lambda: (
        "if u == self.target or u.team == self.team or (not u.alive):" in on_hit_text()
    ),
    "ice_aoe_slow_is_polymorphic": lambda: "u.apply_slow(slow_amount, slow_duration)"
    in on_hit_text(),
    "ice_aoe_atk_slow_is_polymorphic": lambda: (
        "u.apply_debuff('atk_slow', atk_slow, slow_duration)" in on_hit_text()
    ),
    "shoot_ice_gates_aoe": lambda: (
        "if self.slow_aoe > 0:" in shoot_ice_text()
        and "special['slow_aoe'] = self.slow_aoe" in shoot_ice_text()
    ),
    "boss_slow_uses_tenacity": lambda: (
        "min(0.35, amount * (1.0 - tenacity))" in boss_apply_slow_text()
    ),
}


def source_fixture():
    env = build_env()
    _env, boss_cls = boss_env()
    flags = {name: bool(check()) for name, check in SOURCE_FLAGS.items()}
    for name, value in flags.items():
        assert value, "source shape drifted: %s" % name
    levels = {
        str(level): {
            "slow": float(env["ICE_LEVELS"][level]["slow"]),
            "slow_duration": int(env["ICE_LEVELS"][level]["slow_duration"]),
            "atk_slow": float(env["ICE_LEVELS"][level].get("atk_slow", 0)),
            "slow_aoe": float(env["ICE_LEVELS"][level].get("slow_aoe", 0)),
            "damage": int(env["ICE_LEVELS"][level]["damage"]),
        }
        for level in (AOE_LEVEL, NO_AOE_LEVEL)
    }
    return {
        "source": dict(flags, **{"levels": levels, "main": list(MAIN)}),
        "cases": aoe_cases(env, boss_cls),
    }


def main():
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print("WROTE: %s (%d cases)" % (FIXTURE, len(actual["cases"])))
    else:
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), (
            "Boss ice AOE source drift"
        )
        print(
            "PASS: Boss ice AOE — %d cases across %d boss types"
            % (len(actual["cases"]), len({row["boss_type"] for row in actual["cases"]}))
        )


if __name__ == "__main__":
    main()
