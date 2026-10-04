"""Read-only source oracle for item stun delivery onto active bosses.

Executes the real `_apply_stun_to`, `ITEM_CATALOG`, `HeroItemInventory.update`,
`HeroItemInventory.on_basic_attack_hit` and `HeroItemInventory._on_hit_common`
from `hero_items.py`, together with the real `TowerDebuffMixin.apply_stun` and
`TowerDebuffMixin._tick_tower_debuffs` from `_core.py` and the real
`Boss.update` from `bosses/base_boss.py`.

In Python source:
* `hero_items._apply_stun_to(target, duration)` (`hero_items.py:2681-2684`)
  checks `fn = getattr(target, "apply_stun", None)` and calls `fn(duration)` on
  any target that implements `apply_stun`.
* `Boss` inherits `TowerDebuffMixin.apply_stun(duration)` (`_core.py:870-879`),
  which cuts stun duration by 55% (`if getattr(self, "boss_class", None):
  duration = int(duration * 0.45)`) and stores `self.stun_timer = max(
  self.stun_timer, duration)`.
* `Boss.update` (`bosses/base_boss.py:595-600`) ticks `self._tick_tower_debuffs()`
  (decrementing `stun_timer` by 1) and immediately gates the entire combat frame
  with `if self.stun_timer > 0: return` before entrance, enrage, true-boss heal,
  target acquisition, basic attack, and smart/generic ability execution.

Before layer 8v, `BattleItemEffects.apply_stun`
(`godot_rebuild/scripts/match/battle_item_effects.gd:20-23`) only checked
`if t is HeroState:` and ignored `BossState`, so none of the item stun procs
(`sundering_cudgel` Piercing Bash, `abyss_breaker` Bash, `abyss_breaker`
Overwhelm, `fenrir_chain` Binding Chains, `hex_idol` Hexcraft) ever set
`active_boss.stun_timer`.

Four scenarios are recorded for each of the 216 boss types (864 cases total),
each carrying `expected` (source `_apply_stun_to` -> `boss.apply_stun`) and
`expected_without_boss_stun` (the pre-layer `HeroState`-only behavior).
`--write` rewrites the fixture.
"""
import ast
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ai_item_source_oracle import (  # noqa: E402
    _core_module,
    _install_effect_stubs,
    inventory_type,
    source_namespace as item_source_namespace,
)
from boss_ability_source_oracle import (  # noqa: E402
    SOURCE_STATS,
    make_boss,
    source_class as boss_ability_class,
)

FIXTURE = Path(__file__).parent / "fixtures/boss_item_stun_source.json"

SCENARIOS = (
    "sundering_cudgel_pierce_bash",
    "abyss_breaker_bash",
    "abyss_breaker_overwhelm",
    "hex_idol_hexcraft",
)


class _AlwaysProcRandom:
    def random(self):
        return 0.01


def _nodes(source_file):
    return ast.parse((ROOT / source_file).read_text(encoding="utf-8")).body


def _method_node(class_name, method_name, source_file):
    original = next(
        node
        for node in _nodes(source_file)
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    return next(
        node
        for node in original.body
        if isinstance(node, ast.FunctionDef) and node.name == method_name
    )


def _func_node(func_name, source_file):
    return next(
        node
        for node in _nodes(source_file)
        if isinstance(node, ast.FunctionDef) and node.name == func_name
    )


def _method_text(class_name, method_name, source_file):
    return ast.unparse(_method_node(class_name, method_name, source_file))


def _func_text(func_name, source_file):
    return ast.unparse(_func_node(func_name, source_file))


def _build_runtime():
    item_env = item_source_namespace(with_inventory=True)
    _install_effect_stubs(item_env)
    item_env["math"] = math
    item_env["random"] = _AlwaysProcRandom()
    catalog = item_env["ITEM_CATALOG"]
    inv_cls = inventory_type(item_env)

    on_basic_node = _method_node(
        "HeroItemInventory", "on_basic_attack_hit", "hero_items.py"
    )
    on_hit_common_node = _method_node(
        "HeroItemInventory", "_on_hit_common", "hero_items.py"
    )
    apply_stun_to_node = _func_node("_apply_stun_to", "hero_items.py")
    is_magic_hero_node = _func_node("is_magic_hero", "hero_items.py")
    item_module = ast.Module(
        body=[
            is_magic_hero_node,
            apply_stun_to_node,
            on_basic_node,
            on_hit_common_node,
        ],
        type_ignores=[],
    )
    ast.fix_missing_locations(item_module)
    exec(compile(item_module, "_hero_item_stun_source", "exec"), item_env)
    inv_cls.on_basic_attack_hit = item_env["on_basic_attack_hit"]
    inv_cls._on_hit_common = item_env["_on_hit_common"]

    boss_cls = boss_ability_class()

    apply_stun_node = _method_node("TowerDebuffMixin", "apply_stun", "_core.py")
    tick_debuffs_node = _method_node(
        "TowerDebuffMixin", "_tick_tower_debuffs", "_core.py"
    )
    eff_cd_node = _method_node(
        "TowerDebuffMixin", "_eff_attack_cd", "_core.py"
    )
    boss_update_node = _method_node("Boss", "update", "bosses/base_boss.py")
    boss_heal_node = _method_node(
        "Boss", "_use_heal_ability", "bosses/base_boss.py"
    )

    mixin_ns = {
        "__builtins__": __builtins__,
        "math": math,
        "TOWER_DEBUFF_BURN_TICK": 30,
        "TOWER_DEBUFF_FPS": 60.0,
    }
    mixin_module = ast.Module(
        body=[
            apply_stun_node,
            tick_debuffs_node,
            eff_cd_node,
            boss_update_node,
            boss_heal_node,
        ],
        type_ignores=[],
    )
    ast.fix_missing_locations(mixin_module)
    exec(compile(mixin_module, "_boss_item_stun_source", "exec"), mixin_ns)

    boss_cls.apply_stun = mixin_ns["apply_stun"]
    boss_cls._tick_tower_debuffs = mixin_ns["_tick_tower_debuffs"]
    boss_cls._eff_attack_cd = mixin_ns["_eff_attack_cd"]
    boss_cls._full_update = mixin_ns["update"]
    boss_cls._use_heal_ability = mixin_ns["_use_heal_ability"]

    def _begin_motion_tick(self):
        moved = math.hypot(self.x - self._prev_x, self.y - self._prev_y)
        self._prev_x = self.x
        self._prev_y = self.y
        self.is_moving = moved > 0.05
        self._moved = self.is_moving
        if getattr(self, "_attack_lock_timer", 0) > 0:
            self._attack_lock_timer -= 1
            if self._attack_lock_timer <= 0:
                self._attack_facing = 0

    def _face(self, dx, dy):
        if getattr(self, "_attack_lock_timer", 0) > 0:
            return
        if abs(dx) < 0.35 * max(1e-6, abs(dy)):
            return
        self.direction = 1 if dx > 0 else -1
        self.facing = self.direction

    boss_cls._begin_motion_tick = _begin_motion_tick
    boss_cls._face = _face
    boss_cls._move_forward = lambda self: None
    boss_cls._move_towards = lambda self, tx, ty: None
    boss_cls._move_ranged_kite = lambda self, tx, ty, d: None
    boss_cls._suara_serangan = lambda self: "hero_melee"

    return catalog, inv_cls, boss_cls, item_env


class _DummyTarget:
    def __init__(self):
        self.id = 1
        self.team = "blue"
        self.alive = True
        self.x = 20.0
        self.y = 0.0
        self.hp = 10000
        self.max_hp = 10000
        self.attack_timer = 0
        self.hits = 0

    def take_damage(
        self, damage, from_team, damage_type="normal", source=None, school=None
    ):
        if damage > 0:
            self.hp -= damage
            self.hits += 1

    def apply_slow(self, amount, duration):
        pass


class _DummyHeroOwner:
    def __init__(self, role, target):
        self.id = 1
        self.team = "blue"
        self.alive = True
        self.x = 20.0
        self.y = 0.0
        self.hp = 1000
        self.max_hp = 1000
        self.facing = 1
        self.role = role
        self.range = 70
        self.is_melee_hero = True
        self.level = 1
        self.kills = 0
        self.base_max_hp = 1000
        self.target = target


def _prepare_boss(boss_cls, boss_type):
    boss = make_boss(boss_cls, boss_type)
    stats = SOURCE_STATS[boss_type]
    boss.id = 500
    boss.team = "red"
    boss.alive = True
    boss.defeated = False
    boss.x = 0.0
    boss.y = 0.0
    boss._prev_x = 0.0
    boss._prev_y = 0.0
    boss.is_moving = False
    boss._moved = False
    boss._attack_lock_timer = 0
    boss._attack_facing = 0
    boss.direction = 1
    boss.facing = 1
    boss.anim_time = 0
    boss.pulse = 0.0
    boss.hurt_flash_timer = 0
    boss.entrance_timer = 0
    boss.enrage_triggered = False
    boss.is_enraged = False
    boss.enrage_pulse = 0.0
    boss.speed = float(stats["speed"])
    boss.base_speed = float(stats["speed"])
    boss.damage = int(stats["damage"])
    boss.base_damage = int(stats["damage"])
    boss.attack_cooldown = int(stats["attack_cooldown"])
    boss.range = float(stats["range"])
    boss.timer = 0
    boss.ability_timer = 0
    boss.ability_cooldown_max = int(stats.get("ability_cooldown", 300))
    boss.ability_active = False
    boss.ability_active_timer = 0
    boss.ability2_cooldown_max = int(stats.get("ability2_cooldown", 0))
    boss.ability2_heal_pct = float(stats.get("ability2_heal_pct", 0.0))
    boss.ability2_timer = 0
    boss.max_hp = int(stats["hp"])
    boss.hp = int(boss.max_hp * 0.25)
    boss.slow_amount = 0.0
    boss.slow_timer = 0
    boss.atk_slow_amount = 0.0
    boss.atk_slow_timer = 0
    boss.skill_down_amount = 0.0
    boss.skill_down_timer = 0
    boss.anti_heal_amount = 0.0
    boss.anti_heal_timer = 0
    boss.burn_dps = 0.0
    boss.burn_timer = 0
    boss.burn_accum = 0.0
    boss.burn_tick_cd = 30
    boss.burn_team = None
    boss.stun_timer = 0
    boss.armor_shred_amount = 0.0
    boss.armor_shred_timer = 0
    boss.dmg_amp_amount = 0.0
    boss.dmg_amp_timer = 0
    boss.heal_amp_amount = 0.0
    boss.heal_amp_timer = 0
    boss.blind_amount = 0.0
    boss.blind_timer = 0
    boss.cleave_pct = float(
        stats.get("cleave_pct", 0.50 if boss.boss_class == "true" else 0.35)
    )
    boss.cleave_radius = float(
        stats.get("cleave_radius", 110 if boss.boss_class == "true" else 85)
    )
    boss.tenacity = float(stats.get("tenacity", 0.50))
    def _apply_debuff(kind, amount, duration, source_team=None):
        if kind == "atk_slow":
            boss.atk_slow_amount = float(amount)
            boss.atk_slow_timer = max(boss.atk_slow_timer, int(duration))
        elif kind == "skill_down":
            boss.skill_down_amount = float(amount)
            boss.skill_down_timer = max(boss.skill_down_timer, int(duration))

    boss.take_damage = lambda *args, **kwargs: 0
    boss.apply_debuff = _apply_debuff
    boss.apply_armor_shred = lambda *args, **kwargs: None
    boss.apply_damage_amp = lambda *args, **kwargs: None
    return boss


def _run_scenario(
    catalog, inv_cls, boss_cls, item_env, boss_type, scenario, allow_boss_stun
):
    boss = _prepare_boss(boss_cls, boss_type)
    target = _DummyTarget()
    role = "Mage" if scenario == "hex_idol_hexcraft" else "Bruiser"
    owner = _DummyHeroOwner(role, boss)
    inv = inv_cls(owner)

    orig_apply_stun_to = item_env["_apply_stun_to"]
    orig_random = item_env["random"]
    item_env["random"] = _AlwaysProcRandom()
    if not allow_boss_stun:
        item_env["_apply_stun_to"] = lambda tgt, dur: None

    try:
        if scenario == "sundering_cudgel_pierce_bash":
            assert inv.add("sundering_cudgel")
            raw_stun = int(catalog["sundering_cudgel"]["bash"]["stun"])
            inv.on_basic_attack_hit(boss, 50, [boss])
            item_cooldown = int(inv.pierce_bash_cd)
        elif scenario == "abyss_breaker_bash":
            assert inv.add("abyss_breaker")
            raw_stun = int(catalog["abyss_breaker"]["bash"]["stun"])
            inv.on_basic_attack_hit(boss, 50, [boss])
            item_cooldown = int(inv.bash_cd)
        elif scenario == "abyss_breaker_overwhelm":
            assert inv.add("abyss_breaker")
            raw_stun = int(catalog["abyss_breaker"]["active"]["stun"])
            inv.update(1, [boss])
            item_cooldown = int(inv.overwhelm_cd)
        elif scenario == "hex_idol_hexcraft":
            assert inv.add("hex_idol")
            raw_stun = int(catalog["hex_idol"]["active"]["stun"])
            inv.update(1, [boss])
            item_cooldown = int(inv.hex_cd)
        else:
            raise ValueError(f"Unknown scenario: {scenario}")
    finally:
        item_env["_apply_stun_to"] = orig_apply_stun_to
        item_env["random"] = orig_random

    stun_on_apply = int(boss.stun_timer)

    boss._full_update([target], [], [])
    stun_after_step = int(boss.stun_timer)
    boss_enraged = bool(boss.is_enraged)
    boss_basic_attack_fired = target.hits > 0
    boss_timer_after = int(boss.timer)
    boss_ability2_timer_after = int(boss.ability2_timer)

    if stun_after_step > 0:
        for _ in range(stun_after_step):
            boss._full_update([target], [], [])
    stun_on_resume = int(boss.stun_timer)
    boss_enraged_on_resume = bool(boss.is_enraged)
    boss_basic_attack_fired_on_resume = target.hits > 0
    boss_timer_on_resume = int(boss.timer)
    boss_ability2_timer_on_resume = int(boss.ability2_timer)

    return {
        "raw_stun": raw_stun,
        "stun_on_apply": stun_on_apply,
        "item_cooldown": item_cooldown,
        "stun_after_step": stun_after_step,
        "boss_enraged": boss_enraged,
        "boss_basic_attack_fired": boss_basic_attack_fired,
        "boss_timer_after": boss_timer_after,
        "boss_ability2_timer_after": boss_ability2_timer_after,
        "stun_on_resume": stun_on_resume,
        "boss_enraged_on_resume": boss_enraged_on_resume,
        "boss_basic_attack_fired_on_resume": boss_basic_attack_fired_on_resume,
        "boss_timer_on_resume": boss_timer_on_resume,
        "boss_ability2_timer_on_resume": boss_ability2_timer_on_resume,
    }


def generate_fixture():
    with _core_module():
        catalog, inv_cls, boss_cls, item_env = _build_runtime()
        apply_stun_src = _method_text("TowerDebuffMixin", "apply_stun", "_core.py")
        boss_update_src = _method_text("Boss", "update", "bosses/base_boss.py")
        apply_stun_to_src = _func_text("_apply_stun_to", "hero_items.py")

        cases = []
        for boss_type in sorted(SOURCE_STATS):
            stats = SOURCE_STATS[boss_type]
            for scenario in SCENARIOS:
                expected = _run_scenario(
                    catalog,
                    inv_cls,
                    boss_cls,
                    item_env,
                    boss_type,
                    scenario,
                    allow_boss_stun=True,
                )
                without_stun = _run_scenario(
                    catalog,
                    inv_cls,
                    boss_cls,
                    item_env,
                    boss_type,
                    scenario,
                    allow_boss_stun=False,
                )
                assert expected["stun_on_apply"] == int(expected["raw_stun"] * 0.45)
                assert expected["stun_after_step"] == expected["stun_on_apply"] - 1
                assert not expected["boss_enraged"]
                assert not expected["boss_basic_attack_fired"]
                assert expected["boss_timer_after"] == 0
                assert expected["boss_ability2_timer_after"] == 0
                assert expected["stun_on_resume"] == 0
                assert expected["boss_enraged_on_resume"]
                assert expected["boss_basic_attack_fired_on_resume"]
                assert expected["boss_timer_on_resume"] > 0
                if str(stats["boss_class"]) == "true":
                    assert expected["boss_ability2_timer_on_resume"] > 0
                assert without_stun["stun_on_apply"] == 0
                assert without_stun["stun_after_step"] == 0
                assert without_stun["boss_enraged"]
                assert without_stun["boss_basic_attack_fired"]
                assert without_stun["boss_timer_after"] > 0
                cases.append(
                    {
                        "boss_type": boss_type,
                        "boss_class": str(stats["boss_class"]),
                        "scenario": scenario,
                        "expected": expected,
                        "expected_without_boss_stun": without_stun,
                    }
                )

    return {
        "source": {
            "apply_stun_to_uses_getattr_apply_stun": (
                'getattr(target, "apply_stun", None)' in apply_stun_to_src
                or "getattr(target, 'apply_stun', None)" in apply_stun_to_src
            ),
            "boss_apply_stun_scales_by_0_45": (
                'getattr(self, "boss_class", None)' in apply_stun_src
                or "getattr(self, 'boss_class', None)" in apply_stun_src
            )
            and "int(duration * 0.45)" in apply_stun_src,
            "boss_apply_stun_uses_max_timer": "if duration > self.stun_timer:"
            in apply_stun_src,
            "boss_update_ticks_debuffs_before_stun_gate": (
                boss_update_src.index("self._tick_tower_debuffs()")
                < boss_update_src.index("if self.stun_timer > 0:")
            ),
            "boss_update_stun_gate_returns_before_combat": (
                boss_update_src.index("if self.stun_timer > 0:")
                < boss_update_src.index("if self.entrance_timer > 0:")
            ),
            "sundering_cudgel_stun_ticks": int(
                catalog["sundering_cudgel"]["bash"]["stun"]
            ),
            "sundering_cudgel_cooldown": int(
                catalog["sundering_cudgel"]["bash"]["cooldown"]
            ),
            "abyss_breaker_bash_stun_ticks": int(
                catalog["abyss_breaker"]["bash"]["stun"]
            ),
            "abyss_breaker_bash_cooldown": int(
                catalog["abyss_breaker"]["bash"]["cooldown"]
            ),
            "abyss_breaker_overwhelm_stun_ticks": int(
                catalog["abyss_breaker"]["active"]["stun"]
            ),
            "abyss_breaker_overwhelm_cooldown": int(
                catalog["abyss_breaker"]["active"]["cooldown"]
            ),
            "fenrir_chain_root_duration": int(
                catalog["fenrir_chain"]["active"]["root_duration"]
            ),
            "fenrir_chain_cooldown": int(
                catalog["fenrir_chain"]["active"]["cooldown"]
            ),
            "hex_idol_stun_ticks": int(catalog["hex_idol"]["active"]["stun"]),
            "hex_idol_cooldown": int(catalog["hex_idol"]["active"]["cooldown"]),
        },
        "scenarios": list(SCENARIOS),
        "boss_type_count": len(SOURCE_STATS),
        "case_count": len(cases),
        "cases": cases,
    }


def main():
    fixture = generate_fixture()
    text = json.dumps(fixture, indent=2) + "\n"
    if "--write" in sys.argv:
        FIXTURE.write_text(text, encoding="utf-8")
        print(f"Wrote {FIXTURE} ({fixture['case_count']} cases)")
        return
    current = FIXTURE.read_text(encoding="utf-8")
    if current != text:
        raise SystemExit(
            f"{FIXTURE} is out of date; run boss_item_stun_source_oracle.py --write"
        )
    print(f"Verified {FIXTURE} ({fixture['case_count']} cases)")


source_fixture = generate_fixture


if __name__ == "__main__":
    main()
