"""Read-only source oracle for the source Boss entity core.

Executes the real `bosses/base_boss.py` Boss constructor, scaling, tenacity
debuff stores and the numeric tail of `take_damage` (item amp/shred, school
mitigation, inherent resilience, anti-burst cap, defeat flag), plus the
`TowerDebuffMixin` methods Boss inherits. `bosses/boss_data.py` and
`hero_archetypes` are imported unchanged; no pygame/game import happens.

The fixture also renders `data/bosses/boss_stats.json`; `--write` rewrites both
files from the source, `--write-data` only the data file.
"""
import ast
import json
import math
import random
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

FIXTURE = Path(__file__).parent / "fixtures/boss_core_source.json"
DATA = ROOT / "godot_rebuild/data/bosses/boss_stats.json"

from bosses.boss_data import get_all_boss_types  # noqa: E402
import hero_archetypes  # noqa: E402

# Source literals that the oracle asserts against real instances below, so a
# change in bosses/base_boss.py fails here instead of drifting silently.
CAP_PCT = {"mini": 0.12, "true": 0.08}
RESILIENCE = {"mini": 0.20, "true": 0.30}
ENTRANCE_TICKS = {"mini": 120, "true": 180}
TENACITY = 0.50
CLEAVE_RADIUS = 80
CLEAVE_RATIO = 0.40

# Bosses used for the behaviour sections: the four level-1 bosses plus a wider
# sample of abilities/classes so the recorded cases cover both classes.
BEHAVIOUR = ("gornak", "morgath", "drakar", "abaddon", "alchemist", "ancient_apparition")
DAMAGE_CASES = (
    (100, "physical", "normal"),
    (100, "magic", "normal"),
    (100, "neutral", "normal"),
    (500, "physical", "projectile"),
    (50, "magic", "fire"),
    (99999, "physical", "normal"),
    (1, "physical", "normal"),
    (0, "physical", "normal"),
)
BLIND_CASES = (
    (0, 0.0, 1),
    (10, 0.5, 2),
    (10, 0.9, 3),
    (10, 0.1, 4),
)


class SilentSound:
    def play(self, *args, **kwargs):
        pass


def _module(*nodes):
    return compile(
        ast.fix_missing_locations(ast.Module(body=list(nodes), type_ignores=[])),
        "<source boss core>",
        "exec",
    )


def namespace():
    """Module globals the executed source methods read, from real source code."""
    env = {"random": random, "math": math, "SoundManager": SilentSound}
    core = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    for node in core.body:
        if isinstance(node, ast.Assign):
            try:
                value = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    env[target.id] = value
    mixin = next(
        node for node in core.body if isinstance(node, ast.ClassDef) and node.name == "TowerDebuffMixin"
    )
    exec(_module(mixin), env)  # noqa: S102 - executing the original source class
    env["BossBase"] = env["TowerDebuffMixin"]
    entity = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    for name in ("resolve_damage_school", "credit_hero_damage"):
        node = next(
            item for item in entity.body if isinstance(item, ast.FunctionDef) and item.name == name
        )
        exec(_module(node), env)  # noqa: S102
    env["_ACTIVE_HERO"] = [None]
    # Boss.take_damage imports these two helpers lazily (`from _entity import ...`),
    # so the oracle needs a module of that name carrying the real functions.
    stub = sys.modules.setdefault("_entity", ModuleType("_entity"))
    stub.resolve_damage_school = env["resolve_damage_school"]
    stub.credit_hero_damage = env["credit_hero_damage"]
    env["get_all_boss_types"] = get_all_boss_types
    env["hero_archetypes"] = hero_archetypes
    return env


def boss_class(env):
    """Exec the real Boss methods kept for the entity core; no other method runs."""
    module = ast.parse((ROOT / "bosses/base_boss.py").read_text(encoding="utf-8"))
    original = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == "Boss")
    wanted = {
        "__init__",
        "apply_scaling",
        "apply_slow",
        "apply_debuff",
        "take_damage",
        "speed",
        "ability_damage",
    }
    body = [node for node in original.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
    assert len(body) == 9, "Re-audit Boss core methods before trusting this oracle"
    cls = ast.ClassDef(
        name="SourceBoss",
        bases=[ast.Name(id="BossBase", ctx=ast.Load())],
        keywords=[],
        body=body,
        decorator_list=[],
    )
    exec(_module(cls), env)  # noqa: S102
    return env["SourceBoss"]


def row_of(boss):
    return {
        "name": boss.name,
        "title": boss.title,
        "boss_class": boss.boss_class,
        "max_hp": int(boss.max_hp),
        "damage": int(boss.damage),
        "speed": float(boss.speed),
        "attack_range": int(boss.range),
        "attack_cooldown": int(boss.attack_cooldown),
        "min_distance": int(get_all_boss_types()[boss.boss_type].get("min_distance", 200)),
        "prefer_distance": int(get_all_boss_types()[boss.boss_type].get("prefer_distance", 280)),
        "radius": int(boss.radius),
        "gold_reward": int(boss.gold_reward),
        "ability_cooldown": int(boss.ability_cooldown_max),
        "ability_damage": int(boss.ability_damage),
        "ability_range": int(boss.ability_range),
        "ability2_cooldown": int(boss.ability2_cooldown_max),
        "ability2_heal_pct": float(boss.ability2_heal_pct),
        "armor": int(boss.armor),
        "magic_resist": float(boss.magic_resist),
        "resist_profile": str(boss.resist_profile),
        "damage_reduction": float(boss.damage_reduction),
        "max_damage_per_hit": int(boss.max_damage_per_hit),
        "entrance_ticks": int(boss.entrance_timer),
        "entrance_text": boss.entrance_text,
        "color": [int(part) for part in boss.color],
        "color_dark": [int(part) for part in boss.color_dark],
        "entrance_color": [int(part) for part in boss.entrance_color],
    }


def snapshots_of(boss):
    return {
        "slow_amount": float(boss.slow_amount),
        "slow_timer": int(boss.slow_timer),
        "eff_speed": float(boss.speed),
        "atk_slow_amount": float(boss.atk_slow_amount),
        "atk_slow_timer": int(boss.atk_slow_timer),
        "skill_down_amount": float(boss.skill_down_amount),
        "skill_down_timer": int(boss.skill_down_timer),
        "anti_heal_amount": float(boss.anti_heal_amount),
        "anti_heal_timer": int(boss.anti_heal_timer),
        "burn_dps": float(boss.burn_dps),
        "burn_timer": int(boss.burn_timer),
        "burn_accum": float(boss.burn_accum),
        "burn_tick_cd": int(boss.burn_tick_cd),
        "burn_team_set": boss.burn_team is not None,
        "ability_damage": int(boss.ability_damage),
        "stun_timer": int(boss.stun_timer),
        "armor_shred_amount": float(boss.armor_shred_amount),
        "armor_shred_timer": int(boss.armor_shred_timer),
        "dmg_amp_amount": float(boss.dmg_amp_amount),
        "dmg_amp_timer": int(boss.dmg_amp_timer),
        "blind_amount": float(boss.blind_amount),
        "blind_timer": int(boss.blind_timer),
    }


def data_of(env, boss_cls, lane_path):
    rules = {
        "tenacity": TENACITY,
        "cleave_radius": CLEAVE_RADIUS,
        "cleave_ratio": CLEAVE_RATIO,
        "burn_tick": int(env["TOWER_DEBUFF_BURN_TICK"]),
        "fallback_position": [float(env["RED_BASE_X"] - 50), float(env["RED_BASE_Y"])],
        "blue_base_position": [float(env["BLUE_BASE_X"]), float(env["BLUE_BASE_Y"])],
        "damage_reduction": dict(RESILIENCE),
        "max_damage_per_hit_pct": dict(CAP_PCT),
        "entrance_ticks": dict(ENTRANCE_TICKS),
    }
    bosses = {}
    for kind in get_all_boss_types():
        boss = boss_cls(kind, lane_path)
        row = row_of(boss)
        assert float(boss.tenacity) == rules["tenacity"], "Boss tenacity changed"
        assert int(boss.cleave_radius) == rules["cleave_radius"], "Boss cleave radius changed"
        assert float(boss.cleave_ratio) == rules["cleave_ratio"], "Boss cleave ratio changed"
        assert row["damage_reduction"] == rules["damage_reduction"][row["boss_class"]], kind
        assert row["max_damage_per_hit"] == int(
            row["max_hp"] * rules["max_damage_per_hit_pct"][row["boss_class"]]
        ), kind
        assert row["entrance_ticks"] == rules["entrance_ticks"][row["boss_class"]], kind
        bosses[kind] = row
    return {"rules": rules, "bosses": bosses}


def positions(env, boss_cls, lane_path):
    result = {}
    for kind in ("gornak", "morgath", "drakar", "abaddon"):
        with_path = boss_cls(kind, lane_path)
        without = boss_cls(kind, None)
        result[kind] = {
            "path": [float(with_path.x), float(with_path.y)],
            "waypoint_index": int(with_path.waypoint_index),
            "direction": int(with_path.direction),
            "fallback": [float(without.x), float(without.y)],
            "fallback_waypoint_index": int(without.waypoint_index),
        }
    return result


def scaling(env, boss_cls, lane_path):
    result = []
    for kind in BEHAVIOUR:
        for hp_mult, dmg_mult, spd_mult in ((1.0, 1.0, 1.0), (1.15, 1.10, 1.0), (2.0, 1.5, 0.5)):
            boss = boss_cls(kind, lane_path)
            boss.apply_scaling(hp_mult, dmg_mult, spd_mult)
            result.append(
                {
                    "type": kind,
                    "hp_mult": hp_mult,
                    "dmg_mult": dmg_mult,
                    "spd_mult": spd_mult,
                    "max_hp": int(boss.max_hp),
                    "hp": int(boss.hp),
                    "damage": int(boss.damage),
                    "base_damage": int(boss.base_damage),
                    "ability_damage": int(boss.ability_damage),
                    "speed": float(boss.speed),
                    "base_speed": float(boss.base_speed),
                    "max_damage_per_hit": int(boss.max_damage_per_hit),
                    "hp_scaling_mult": float(boss.hp_scaling_mult),
                    "dmg_scaling_mult": float(boss.dmg_scaling_mult),
                    "spd_scaling_mult": float(boss.spd_scaling_mult),
                }
            )
    return result


def debuff_runs(env, boss_cls, lane_path):
    ops = [
        ("apply_slow", [0.5, 60]),
        ("apply_slow", [0.2, 240]),
        ("apply_debuff", ["atk_slow", 0.6, 90]),
        ("apply_debuff", ["skill_down", 0.4, 45]),
        ("apply_debuff", ["anti_heal", 0.5, 120]),
        ("apply_debuff", ["burn", 12, 300, 1]),
        ("apply_debuff", ["burn", 4, 900, 0]),
        ("apply_stun", [60]),
        ("clear_tower_debuffs", []),
    ]
    result = []
    for kind in BEHAVIOUR:
        boss = boss_cls(kind, lane_path)
        run = {"type": kind, "ops": [{"call": name, "args": args} for name, args in ops], "snapshots": []}
        for name, args in ops:
            getattr(boss, name)(*args)
            run["snapshots"].append(snapshots_of(boss))
        result.append(run)
    return result


def damage_cases(env, boss_cls, lane_path):
    result = []
    for kind in BEHAVIOUR:
        for raw, school, damage_type in DAMAGE_CASES:
            for amp, shred in ((None, None), (0.5, None), (None, 4), (0.5, 4)):
                boss = boss_cls(kind, lane_path)
                if amp is not None:
                    boss.apply_damage_amp(amp, 300)
                if shred is not None:
                    boss.apply_armor_shred(shred, 300)
                before = int(boss.hp)
                boss.take_damage(raw, "blue", damage_type=damage_type, source=None, school=school)
                result.append(
                    {
                        "type": kind,
                        "raw": raw,
                        "school": school,
                        "damage_type": damage_type,
                        "amp": amp,
                        "shred": shred,
                        "hp_before": before,
                        "hp_after": int(boss.hp),
                        "dealt": before - int(boss.hp),
                        "alive": bool(boss.alive),
                        "defeated": bool(boss.defeated),
                        "hurt_flash_timer": int(boss.hurt_flash_timer),
                    }
                )
    return result


def blind_cases(env, boss_cls, lane_path):
    result = []
    for kind in BEHAVIOUR:
        for blind_timer, blind_amount, seed in BLIND_CASES:
            for true_strike in (False, True):
                boss = boss_cls(kind, lane_path)
                source = SimpleNamespace(
                    team="blue",
                    alive=True,
                    blind_timer=blind_timer,
                    blind_amount=blind_amount,
                    items=SimpleNamespace(has_true_strike=lambda: true_strike),
                )
                random.seed(seed)
                roll = random.random()
                random.seed(seed)
                before = int(boss.hp)
                boss.take_damage(100, "blue", damage_type="normal", source=source, school="physical")
                result.append(
                    {
                        "type": kind,
                        "blind_timer": blind_timer,
                        "blind_amount": blind_amount,
                        "seed": seed,
                        "roll": roll,
                        "true_strike": true_strike,
                        "hp_before": before,
                        "hp_after": int(boss.hp),
                        "dealt": before - int(boss.hp),
                    }
                )
    return result


def defeat_cases(env, boss_cls, lane_path):
    """A killing blow: defeated flag set and every tower debuff cleared."""
    result = []
    for kind in BEHAVIOUR:
        boss = boss_cls(kind, lane_path)
        boss.hp = 10
        boss.apply_slow(0.5, 60)
        boss.apply_debuff("burn", 12, 300, 1)
        before = int(boss.hp)
        boss.take_damage(40, "blue", damage_type="physical", source=None, school="physical")
        result.append(
            {
                "type": kind,
                "hp_before": before,
                "hp_after": int(boss.hp),
                "dealt": before - int(boss.hp),
                "alive": bool(boss.alive),
                "defeated": bool(boss.defeated),
                "cleared": snapshots_of(boss),
                "hurt_flash_timer": int(boss.hurt_flash_timer),
            }
        )
    return result


def source_fixture():
    env = namespace()
    boss_cls = boss_class(env)
    from check_source_contract import source_lanes

    lane_path = source_lanes()["mid"]
    return {
        "data": data_of(env, boss_cls, lane_path),
        "positions": positions(env, boss_cls, lane_path),
        "scaling": scaling(env, boss_cls, lane_path),
        "debuff_runs": debuff_runs(env, boss_cls, lane_path),
        "damage": damage_cases(env, boss_cls, lane_path),
        "blind": blind_cases(env, boss_cls, lane_path),
        "defeat": defeat_cases(env, boss_cls, lane_path),
    }


def write_files():
    fixture = source_fixture()
    FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(fixture["data"], indent=2) + "\n", encoding="utf-8")
    return fixture


if __name__ == "__main__":
    if "--write" in sys.argv or "--write-data" in sys.argv:
        written = write_files()
        print(
            "WROTE: %d bosses, %d scaling, %d debuff runs, %d damage, %d blind"
            % (
                len(written["data"]["bosses"]),
                len(written["scaling"]),
                len(written["debuff_runs"]),
                len(written["damage"]),
                len(written["blind"]),
            )
        )
    else:
        actual = source_fixture()
        assert actual == json.loads(FIXTURE.read_text(encoding="utf-8")), "Boss core source drift"
        assert actual["data"] == json.loads(DATA.read_text(encoding="utf-8")), \
            "data/bosses/boss_stats.json drifted from source boss tables"
        print(
            "PASS: Boss core — %d bosses, %d damage cases, %d blind cases"
            % (len(actual["data"]["bosses"]), len(actual["damage"]), len(actual["blind"]))
        )
