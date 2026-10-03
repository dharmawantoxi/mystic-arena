"""Read-only source oracle for tower/nexus projectile damage against the boss.

Executes the real `Bullet._on_hit` from `_entity.py` (via
`cannon_source_oracle.build_env`, which AST-extracts `Bullet.__init__` and
`_on_hit`) with the real `Boss` from `boss_core_source_oracle` as the PRIMARY
target, once per bullet kind the source can fire at a boss.

The source facts this fixture pins:

* `Bullet._on_hit` damages its target with
  `self.target.take_damage(self.damage, self.team, damage_type='projectile')`
  - no `school=` and no `source=` argument, for every bullet kind;
* `Boss.take_damage` resolves the school through
  `_entity.resolve_damage_school(damage_type, source, school)`, and that
  resolver returns `None` for `damage_type='projectile'` with no source, so the
  armor and magic-resist branches never run on a tower hit;
* the same resolver DOES return `'physical'`/`'magic'` when an explicit school
  or an attacker `dmg_school` is present - which is exactly the value the native
  structure path used to pass, so the fixture records that column too
  (`expected_physical`) as the pre-layer native result;
* only resilience (`damage_reduction`) and the anti-burst cap still apply to a
  tower hit.

Four scenarios are recorded per boss type: the four bullet kinds a structure can
put on the boss. `--write` rewrites the fixture.
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

FIXTURE = Path(__file__).parent / "fixtures/boss_tower_damage_source.json"

SHOOTER_TEAM = "blue"
BOSS_AT = (560.0, 340.0)

# (label, bullet_type, level table, level). Every row is a real structure shot.
SCENARIOS = (
    ("archer_level_one", "normal", "ARCHER_LEVELS", 1),
    ("cannon_level_six", "cannon", "CANNON_LEVELS", 6),
    ("ice_level_six", "ice", "ICE_LEVELS", 6),
    ("mage_level_six", "mage", "MAGE_LEVELS", 6),
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


def _function_node(method_name, source_file="_entity.py"):
    return next(
        node
        for node in _nodes(source_file)
        if isinstance(node, ast.FunctionDef) and node.name == method_name
    )


def _module(*nodes):
    return compile(
        ast.fix_missing_locations(ast.Module(body=list(nodes), type_ignores=[])),
        "<source tower damage>",
        "exec",
    )


def build_env():
    from cannon_source_oracle import build_env as cannon_env

    env = cannon_env()
    entity = _function_node("resolve_damage_school")
    exec(_module(entity), env)  # noqa: S102 - executing the original source resolver
    return env


def boss_env():
    from boss_core_source_oracle import boss_class, namespace

    env = namespace()
    return env, boss_class(env)


def special_data(env, table, level, bullet_type):
    """special_data exactly as the matching `Tower._shoot_*` builds it."""
    stats = env[table][level]
    if bullet_type == "cannon":
        special = {"splash": stats["splash"]}
        if stats.get("burn_dps", 0) > 0:
            special["burn_dps"] = stats["burn_dps"]
            special["burn_duration"] = stats["burn_duration"]
        return special
    if bullet_type == "ice":
        special = {"slow": stats["slow"], "slow_duration": stats["slow_duration"]}
        if stats.get("atk_slow", 0) > 0:
            special["atk_slow"] = stats["atk_slow"]
        if stats.get("slow_aoe", 0) > 0:
            special["slow_aoe"] = stats["slow_aoe"]
        return special
    if bullet_type == "mage":
        special = {}
        if stats.get("skill_down", 0) > 0:
            special["skill_down"] = stats["skill_down"]
        if stats.get("anti_heal", 0) > 0:
            special["anti_heal"] = stats["anti_heal"]
        if special:
            special["debuff_duration"] = stats["debuff_duration"]
        return special
    return {}


def make_shot(env, target, table, level, bullet_type):
    bullet = env["SourceBullet"].__new__(env["SourceBullet"])
    bullet.x, bullet.y = 0.0, 0.0
    bullet.target = target
    bullet.damage = int(env[table][level]["damage"])
    bullet.team = SHOOTER_TEAM
    bullet.speed, bullet.active = 8, True
    bullet.bullet_type = bullet_type
    bullet.special_data = special_data(env, table, level, bullet_type)
    return bullet


def on_hit_text():
    return ast.unparse(_method_node("Bullet", "_on_hit"))


def boss_take_damage_text():
    return ast.unparse(_method_node("Boss", "take_damage", "bosses/base_boss.py"))


def resolver_text():
    return ast.unparse(_function_node("resolve_damage_school"))


def damage_cases(env, boss_cls):
    from bosses.boss_data import get_all_boss_types

    cases = []
    for kind in sorted(get_all_boss_types()):
        for label, bullet_type, table, level in SCENARIOS:
            raw = int(env[table][level]["damage"])
            boss = boss_cls(kind, None)
            boss.x, boss.y = BOSS_AT
            hp_before = float(boss.hp)
            # Real structure hit: no school, no source -> no school mitigation.
            make_shot(env, boss, table, level, bullet_type)._on_hit([boss])
            hp_after = float(boss.hp)
            # What the native structure path produced before this layer: the
            # same raw damage delivered with the caller-declared school.
            contrast = boss_cls(kind, None)
            contrast.take_damage(raw, SHOOTER_TEAM, damage_type="normal", school="physical")
            physical_after = float(contrast.hp)
            assert hp_after <= physical_after, (
                "%s school-free hit can never leave more hp than the mitigated one" % label
            )
            cases.append(
                {
                    "boss_type": kind,
                    "label": label,
                    "bullet_type": bullet_type,
                    "raw_damage": raw,
                    "hp_before": hp_before,
                    "expected_hp_after": hp_after,
                    "expected_physical_hp_after": physical_after,
                    "armor": int(boss.armor),
                    "damage_reduction": float(boss.damage_reduction),
                    "max_damage_per_hit": int(boss.max_damage_per_hit),
                    "alive": bool(boss.alive),
                }
            )
    return cases


def source_flags(env):
    class _PhysicalHero:
        dmg_school = "physical"

    resolve = env["resolve_damage_school"]
    return {
        "main_hit_is_projectile": (
            "self.target.take_damage(self.damage, self.team, damage_type='projectile')"
            in on_hit_text()
        ),
        "hit_passes_no_school": "school=" not in on_hit_text(),
        "resolver_none_for_projectile": resolve("projectile", None, None) is None,
        "resolver_rejects_unknown_school": resolve("normal", None, "bogus") is None,
        "resolver_reads_source_school": resolve("normal", _PhysicalHero(), None) == "physical",
        "boss_mitigation_gated_by_school": (
            "if damage > 0 and _sch == 'physical' and (self.armor > 0):" in boss_take_damage_text()
            and "elif damage > 0 and _sch == 'magic' and (self.magic_resist > 0):"
            in boss_take_damage_text()
        ),
        "resolver_documented_none": "return None" in resolver_text(),
    }


def source_fixture():
    env = build_env()
    _env, boss_cls = boss_env()
    flags = {name: bool(value) for name, value in source_flags(env).items()}
    for name, value in flags.items():
        assert value, "source shape drifted: %s" % name
    cases = damage_cases(env, boss_cls)
    assert any(
        case["expected_hp_after"] != case["expected_physical_hp_after"] for case in cases
    ), "armor must make the source school-free tower hit land harder somewhere"
    return {
        "source": dict(
            flags,
            **{
                "levels": {
                    "%s_%d" % (table.lower(), level): int(env[table][level]["damage"])
                    for _label, _kind, table, level in SCENARIOS
                }
            },
        ),
        "cases": cases,
    }


def main():
    actual = source_fixture()
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
        print("WROTE: %s (%d cases)" % (FIXTURE, len(actual["cases"])))
    else:
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), (
            "Boss tower damage source drift"
        )
        print(
            "PASS: Boss tower damage — %d cases across %d boss types"
            % (len(actual["cases"]), len({row["boss_type"] for row in actual["cases"]}))
        )


if __name__ == "__main__":
    main()
