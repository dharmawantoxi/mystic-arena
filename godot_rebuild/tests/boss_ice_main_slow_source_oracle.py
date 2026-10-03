"""Read-only source oracle for the ice main-target slow on a boss.

Executes the real `Bullet._on_hit` ice branch from `_entity.py` (via
`cannon_source_oracle.build_env`) with the real `Boss` from
`boss_core_source_oracle` as the PRIMARY target of the shot, which is the arm
the source runs before any AOE:

    if hasattr(self.target, 'apply_slow'):
        self.target.apply_slow(slow_amount, slow_duration)
    if atk_slow > 0 and hasattr(self.target, 'apply_debuff'):
        self.target.apply_debuff('atk_slow', atk_slow, slow_duration)

Both calls are polymorphic, so a boss runs `Boss.apply_slow` /
`Boss.apply_debuff`: tenacity (0.50) cuts magnitude AND duration, the magnitude
is capped at 0.35, and only then does the `TowerDebuffMixin` store rule apply
(strongest wins, a longer duration refreshes both fields). A minion or hero
runs the mixin rule instead, which stores the raw values.

Every scenario therefore records two columns from real source code:

* `expected` - the Boss rule (what the native boss path must produce);
* `expected_mixin` - the mixin rule on a real `SourceVictim`, which is what the
  native world-level `apply_slow`/`apply_atk_slow` store did before this layer.

Four scenarios are recorded per boss type, covering both ice levels in play and
both directions of the store rule. `--write` rewrites the fixture.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

FIXTURE = Path(__file__).parent / "fixtures/boss_ice_main_slow_source.json"

MAIN = (560.0, 340.0)
SHOOTER_TEAM = "blue"
VICTIM_TEAM = "red"

# (label, ice levels fired in order at the same primary target).
SCENARIOS = (
    ("level_six_single", (6,)),
    ("level_five_single", (5,)),
    ("strong_then_weak_keeps_strongest", (6, 5)),
    ("weak_then_strong_refreshes", (2, 6)),
)


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
        "<source ice main slow>",
        "exec",
    )


def build_env():
    from cannon_source_oracle import build_env as cannon_env

    env = cannon_env()
    # `Bullet._on_hit` slows through `apply_slow`; bind the real mixin method so
    # the non-boss column runs source code too.
    node = _method_node("TowerDebuffMixin", "apply_slow", "_core.py")
    exec(_module(node), env)  # noqa: S102 - executing the original source method
    env["SourceDebuffs"].apply_slow = env["apply_slow"]
    return env


def boss_env():
    from boss_core_source_oracle import boss_class, namespace

    env = namespace()
    return env, boss_class(env)


def make_main(env):
    from cannon_source_oracle import make_victim

    return make_victim(env, 1, MAIN[0], MAIN[1], team=VICTIM_TEAM, hp=100000)


def make_shot(env, target, level):
    stats = env["ICE_LEVELS"][level]
    bullet = env["SourceBullet"].__new__(env["SourceBullet"])
    bullet.x, bullet.y = 0.0, 0.0
    bullet.target = target
    bullet.damage = int(stats["damage"])
    bullet.team = SHOOTER_TEAM
    bullet.speed, bullet.active = 8, True
    bullet.bullet_type = "ice"
    special = {"slow": stats["slow"], "slow_duration": stats["slow_duration"]}
    if stats.get("atk_slow", 0) > 0:
        special["atk_slow"] = stats["atk_slow"]
    if stats.get("slow_aoe", 0) > 0:
        special["slow_aoe"] = stats["slow_aoe"]
    bullet.special_data = special
    return bullet


def stores(unit):
    return {
        "slow_amount": float(getattr(unit, "slow_amount", 0.0)),
        "slow_timer": int(getattr(unit, "slow_timer", 0)),
        "atk_slow_amount": float(getattr(unit, "atk_slow_amount", 0.0)),
        "atk_slow_timer": int(getattr(unit, "atk_slow_timer", 0)),
    }


def slow_cases(env, boss_cls):
    from bosses.boss_data import get_all_boss_types

    cases = []
    for kind in sorted(get_all_boss_types()):
        for label, levels in SCENARIOS:
            boss = boss_cls(kind, None)
            boss.x, boss.y = MAIN
            for level in levels:
                make_shot(env, boss, level)._on_hit([boss])
            stub = make_main(env)
            for level in levels:
                make_shot(env, stub, level)._on_hit([stub])
            expected = stores(boss)
            mixin = stores(stub)
            assert expected["slow_timer"] > 0, "%s must slow the boss" % label
            assert mixin["slow_amount"] > expected["slow_amount"], (
                "%s tenacity must cut the boss slow below the mixin store" % label
            )
            cases.append(
                {
                    "boss_type": kind,
                    "label": label,
                    "levels": list(levels),
                    "tenacity": float(boss.tenacity),
                    "inputs": [
                        {
                            "level": level,
                            "slow": float(env["ICE_LEVELS"][level]["slow"]),
                            "slow_duration": int(env["ICE_LEVELS"][level]["slow_duration"]),
                            "atk_slow": float(env["ICE_LEVELS"][level].get("atk_slow", 0)),
                        }
                        for level in levels
                    ],
                    "expected": expected,
                    "expected_mixin": mixin,
                }
            )
    return cases


def on_hit_text():
    return ast.unparse(_method_node("Bullet", "_on_hit"))


def boss_apply_slow_text():
    return ast.unparse(_method_node("Boss", "apply_slow", "bosses/base_boss.py"))


def boss_apply_debuff_text():
    return ast.unparse(_method_node("Boss", "apply_debuff", "bosses/base_boss.py"))


def mixin_apply_slow_text():
    return ast.unparse(_method_node("TowerDebuffMixin", "apply_slow", "_core.py"))


SOURCE_FLAGS = {
    "main_slow_is_polymorphic": lambda: "self.target.apply_slow(slow_amount, slow_duration)"
    in on_hit_text(),
    "main_atk_slow_is_polymorphic": lambda: (
        "self.target.apply_debuff('atk_slow', atk_slow, slow_duration)" in on_hit_text()
    ),
    "main_atk_slow_gated": lambda: (
        "if atk_slow > 0 and hasattr(self.target, 'apply_debuff'):" in on_hit_text()
    ),
    "boss_slow_requires_alive": lambda: "if not getattr(self, 'alive', True):"
    in boss_apply_slow_text(),
    "boss_slow_uses_tenacity": lambda: "min(0.35, amount * (1.0 - tenacity))"
    in boss_apply_slow_text(),
    "boss_slow_cuts_duration": lambda: "int(duration * (1.0 - tenacity))"
    in boss_apply_slow_text(),
    "boss_atk_slow_uses_tenacity": lambda: "min(0.35, amount * (1.0 - tenacity))"
    in boss_apply_debuff_text(),
    "mixin_slow_has_no_tenacity": lambda: "tenacity" not in mixin_apply_slow_text()
    and "self.slow_amount = amount" in mixin_apply_slow_text(),
}


def source_fixture():
    env = build_env()
    _env, boss_cls = boss_env()
    flags = {name: bool(check()) for name, check in SOURCE_FLAGS.items()}
    for name, value in flags.items():
        assert value, "source shape drifted: %s" % name
    return {
        "source": dict(
            flags,
            **{
                "levels": {
                    str(level): {
                        "slow": float(env["ICE_LEVELS"][level]["slow"]),
                        "slow_duration": int(env["ICE_LEVELS"][level]["slow_duration"]),
                        "atk_slow": float(env["ICE_LEVELS"][level].get("atk_slow", 0)),
                        "damage": int(env["ICE_LEVELS"][level]["damage"]),
                    }
                    for level in (2, 5, 6)
                }
            },
        ),
        "cases": slow_cases(env, boss_cls),
    }


def main():
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print("WROTE: %s (%d cases)" % (FIXTURE, len(actual["cases"])))
    else:
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), (
            "Boss ice main slow source drift"
        )
        print(
            "PASS: Boss ice main slow — %d cases across %d boss types"
            % (len(actual["cases"]), len({row["boss_type"] for row in actual["cases"]}))
        )


if __name__ == "__main__":
    main()
