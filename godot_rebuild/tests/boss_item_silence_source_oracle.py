"""Read-only source oracle for item silence delivery onto active bosses.

Executes the real `_apply_silence_to`, `_apply_amp_to`, `_apply_stun_to`,
`ITEM_CATALOG` and `HeroItemInventory.update` from `hero_items.py`, together
with the real `TowerDebuffMixin.apply_debuff`/`apply_stun` from `_core.py` and
the real `Boss.apply_debuff`/`apply_slow` from `bosses/base_boss.py`.

In Python source:
* `hero_items._apply_silence_to(target, duration)` (`hero_items.py:2693-2697`)
  is called by every item silence proc - `sanguine_thorn` Soul Rend
  (`hero_items.py:2226`), `astral_codex` Arcane Nova (`hero_items.py:2362`) and
  `hex_idol` Hexcraft (`hero_items.py:2390`) - and applies
  `target.apply_debuff("atk_slow", 1.0, duration)` followed by
  `target.apply_debuff("skill_down", 1.0, duration)`.
* `Boss.apply_debuff` (`bosses/base_boss.py:540-552`) cuts `atk_slow` by
  tenacity 0.50 (`amount = min(0.35, amount * (1.0 - tenacity))`,
  `duration = int(duration * (1.0 - tenacity))`) before delegating to
  `TowerDebuffMixin.apply_debuff` (`_core.py:918-947` store rules: strongest
  amount wins, a longer duration refreshes both fields). `skill_down` is NOT
  tenacity-cut, only `atk_slow` is.
* `TowerDebuffMixin._eff_attack_cd` (`_core.py:972-979`) and the
  `Boss.ability_damage` property (`bosses/base_boss.py:362-370`) turn those
  fields into the boss attack cooldown and skill damage.

Before layer 8w, `BattleItemEffects.apply_silence`
(`godot_rebuild/scripts/match/battle_item_effects.gd:35-44`) wrote the raw
fields directly (`atk_slow_amount = 1.0`, `atk_slow_timer =
maxi(timer, duration)` plus the same for `skill_down`), so a silenced boss ran
the untempered 1.0 attack-speed slow for the full item duration.

Four scenarios are recorded for each of the 216 boss types (864 cases total),
each carrying `expected` (source `_apply_silence_to` -> `Boss.apply_debuff`)
and `expected_without_boss_tenacity` (the pre-layer native bus write).
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

FIXTURE = Path(__file__).parent / "fixtures/boss_item_silence_source.json"

SCENARIOS = (
    "sanguine_thorn_soul_rend",
    "astral_codex_arcane_nova",
    "hex_idol_hexcraft",
    "soul_rend_and_arcane_nova_keep_longest_store",
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


def _spliced_boss_debuff():
    """`Boss.apply_debuff` with `super().apply_debuff(...)` bound to the mixin.

    The real body is kept verbatim; only the zero-argument `super()` call is
    rewritten to the standalone `_tower_debuff(self, ...)` mixin method, so the
    tenacity cut still runs through the original `TowerDebuffMixin.apply_debuff`
    store rules.
    """
    node = _method_node("Boss", "apply_debuff", "bosses/base_boss.py")

    class _Splice(ast.NodeTransformer):
        def visit_Call(self, call):
            self.generic_visit(call)
            func = call.func
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "apply_debuff"
                and isinstance(func.value, ast.Call)
                and isinstance(func.value.func, ast.Name)
                and func.value.func.id == "super"
            ):
                call.func = ast.Name(id="_tower_debuff", ctx=ast.Load())
                call.args = [ast.Name(id="self", ctx=ast.Load())] + call.args
            return call

    spliced = _Splice().visit(node)
    ast.fix_missing_locations(spliced)
    return spliced


def _build_runtime():
    item_env = item_source_namespace(with_inventory=True)
    _install_effect_stubs(item_env)
    item_env["math"] = math
    item_env["random"] = _AlwaysProcRandom()
    catalog = item_env["ITEM_CATALOG"]
    inv_cls = inventory_type(item_env)

    update_node = _method_node("HeroItemInventory", "update", "hero_items.py")
    silence_node = _func_node("_apply_silence_to", "hero_items.py")
    amp_node = _func_node("_apply_amp_to", "hero_items.py")
    stun_node = _func_node("_apply_stun_to", "hero_items.py")
    is_magic_hero_node = _func_node("is_magic_hero", "hero_items.py")
    item_module = ast.Module(
        body=[is_magic_hero_node, silence_node, amp_node, stun_node, update_node],
        type_ignores=[],
    )
    ast.fix_missing_locations(item_module)
    exec(compile(item_module, "_hero_item_silence_source", "exec"), item_env)
    inv_cls.update = item_env["update"]

    boss_cls = boss_ability_class()

    tower_debuff_node = _method_node("TowerDebuffMixin", "apply_debuff", "_core.py")
    tower_debuff_node.name = "_tower_debuff"
    tower_stun_node = _method_node("TowerDebuffMixin", "apply_stun", "_core.py")
    tower_amp_node = _method_node("TowerDebuffMixin", "apply_damage_amp", "_core.py")
    eff_cd_node = _method_node("TowerDebuffMixin", "_eff_attack_cd", "_core.py")
    boss_apply_slow_node = _method_node("Boss", "apply_slow", "bosses/base_boss.py")
    boss_debuff_node = _spliced_boss_debuff()
    ability_getter = _method_node("Boss", "ability_damage", "bosses/base_boss.py")
    ability_getter.decorator_list = []
    ability_getter.name = "_ability_damage_getter"

    module = ast.Module(
        body=[
            tower_debuff_node,
            tower_stun_node,
            tower_amp_node,
            eff_cd_node,
            boss_apply_slow_node,
            boss_debuff_node,
            ability_getter,
        ],
        type_ignores=[],
    )
    ast.fix_missing_locations(module)
    env = {"__builtins__": __builtins__, "math": math}
    exec(compile(module, "_boss_item_silence_source", "exec"), env)

    boss_cls.apply_debuff = env["apply_debuff"]
    boss_cls.apply_slow = env["apply_slow"]
    boss_cls.apply_stun = env["apply_stun"]
    boss_cls.apply_damage_amp = env["apply_damage_amp"]
    boss_cls._eff_attack_cd = env["_eff_attack_cd"]
    boss_cls._ability_damage_getter = env["_ability_damage_getter"]

    return catalog, inv_cls, boss_cls, item_env


class _DummyTarget:
    """Second source-free enemy so Arcane Nova's 2+ gate can fire."""

    def __init__(self):
        self.id = 2
        self.team = "red"
        self.alive = True
        self.x = 30.0
        self.y = 0.0
        self.hp = 10000
        self.max_hp = 10000
        self.attack_timer = 0
        self.hits = 0
        self.debuffs = []

    def take_damage(
        self, damage, from_team, damage_type="normal", source=None, school=None
    ):
        if damage > 0:
            self.hp -= damage
            self.hits += 1

    def apply_debuff(self, kind, amount, duration, source_team=None):
        self.debuffs.append([kind, float(amount), int(duration)])

    def apply_slow(self, amount, duration):
        self.debuffs.append(["slow", float(amount), int(duration)])


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
    boss.attack_timer = 0
    boss.attack_cooldown = int(stats.get("attack_cooldown", 60))
    boss.max_hp = int(stats["hp"])
    boss.hp = int(boss.max_hp * 0.25)
    boss._ability_damage_value = int(stats.get("ability_damage", 0))
    boss.tenacity = float(stats.get("tenacity", 0.50))
    boss.slow_amount = 0.0
    boss.slow_timer = 0
    boss.atk_slow_amount = 0.0
    boss.atk_slow_timer = 0
    boss.skill_down_amount = 0.0
    boss.skill_down_timer = 0
    boss.armor_shred_amount = 0.0
    boss.armor_shred_timer = 0
    boss.dmg_amp_amount = 0.0
    boss.dmg_amp_timer = 0
    boss.stun_timer = 0
    boss.take_damage = lambda *args, **kwargs: 0
    return boss


def _native_bus_silence(target, duration):
    """Pre-8w `BattleItemEffects.apply_silence`: raw field writes, no tenacity."""
    duration = int(duration)
    target.atk_slow_amount = 1.0
    target.atk_slow_timer = max(int(getattr(target, "atk_slow_timer", 0)), duration)
    target.skill_down_amount = 1.0
    target.skill_down_timer = max(int(getattr(target, "skill_down_timer", 0)), duration)


def _run_scenario(inv_cls, boss_cls, item_env, boss_type, scenario, tenacity_on):
    boss = _prepare_boss(boss_cls, boss_type)
    extra = _DummyTarget()
    role = "Bruiser" if scenario == "sanguine_thorn_soul_rend" else "Mage"
    owner = _DummyHeroOwner(role, boss)
    inv = inv_cls(owner)

    original_silence = item_env["_apply_silence_to"]
    delivery = original_silence if tenacity_on else _native_bus_silence
    calls = []

    def recording_silence(target, duration):
        calls.append({"duration": int(duration), "is_boss": target is boss})
        delivery(target, duration)

    item_env["_apply_silence_to"] = recording_silence
    try:
        if scenario == "sanguine_thorn_soul_rend":
            assert inv.add("sanguine_thorn")
            enemies = [boss]
        elif scenario == "astral_codex_arcane_nova":
            assert inv.add("astral_codex")
            enemies = [boss, extra]
        elif scenario == "hex_idol_hexcraft":
            assert inv.add("hex_idol")
            enemies = [boss]
        elif scenario == "soul_rend_and_arcane_nova_keep_longest_store":
            assert inv.add("sanguine_thorn")
            assert inv.add("astral_codex")
            enemies = [boss, extra]
        else:
            raise ValueError(f"Unknown scenario: {scenario}")
        # `add()` runs the real `_on_item_changed`, which recomputes the owner
        # max HP from hero stats this dummy does not model; restore the live
        # values so the source Tier II gate (`h.alive and h.max_hp > 0`) opens.
        owner.hp = 1000
        owner.max_hp = 1000
        inv.update(1, enemies)
    finally:
        item_env["_apply_silence_to"] = original_silence

    return {
        "raw_silence_durations": [call["duration"] for call in calls],
        "boss_silenced": any(call["is_boss"] for call in calls),
        "atk_slow_amount": round(float(boss.atk_slow_amount), 6),
        "atk_slow_timer": int(boss.atk_slow_timer),
        "skill_down_amount": round(float(boss.skill_down_amount), 6),
        "skill_down_timer": int(boss.skill_down_timer),
        "stun_timer": int(boss.stun_timer),
        "attack_cooldown_ticks": int(
            boss_cls._eff_attack_cd(boss, int(boss.attack_cooldown))
        ),
        "ability_damage_after": int(boss_cls._ability_damage_getter(boss)),
        "cooldowns": {
            "sanguine_thorn": int(inv.rend_cd),
            "astral_codex": int(inv.arcane_cd),
            "hex_idol": int(inv.hex_cd),
        },
    }


def generate_fixture():
    with _core_module():
        catalog, inv_cls, boss_cls, item_env = _build_runtime()
        silence_src = _func_text("_apply_silence_to", "hero_items.py")
        boss_debuff_src = _method_text("Boss", "apply_debuff", "bosses/base_boss.py")
        tower_debuff_src = _method_text("TowerDebuffMixin", "apply_debuff", "_core.py")

        cases = []
        for boss_type in sorted(SOURCE_STATS):
            for scenario in SCENARIOS:
                expected = _run_scenario(
                    inv_cls, boss_cls, item_env, boss_type, scenario, tenacity_on=True
                )
                without_tenacity = _run_scenario(
                    inv_cls, boss_cls, item_env, boss_type, scenario, tenacity_on=False
                )
                assert expected["boss_silenced"]
                assert without_tenacity["boss_silenced"]
                assert expected["raw_silence_durations"] == (
                    without_tenacity["raw_silence_durations"]
                )
                # Tenacity cuts only atk_slow; skill_down keeps the raw payload.
                assert expected["skill_down_amount"] == 1.0
                assert expected["atk_slow_amount"] == 0.35
                assert expected["atk_slow_amount"] < without_tenacity["atk_slow_amount"]
                assert expected["atk_slow_timer"] < without_tenacity["atk_slow_timer"]
                cases.append(
                    {
                        "boss_type": boss_type,
                        "boss_class": str(SOURCE_STATS[boss_type]["boss_class"]),
                        "scenario": scenario,
                        "expected": expected,
                        "expected_without_boss_tenacity": without_tenacity,
                    }
                )

    return {
        "source": {
            "silence_applies_atk_slow_then_skill_down": (
                "apply_debuff('atk_slow', 1.0, duration)" in silence_src
                and "apply_debuff('skill_down', 1.0, duration)" in silence_src
                and silence_src.index("'atk_slow'") < silence_src.index("'skill_down'")
            ),
            "silence_uses_apply_debuff_branch": (
                "target.apply_debuff(" in silence_src
                and "target.apply_slow(" not in silence_src
            ),
            "boss_debuff_cuts_atk_slow_by_tenacity": (
                "min(0.35, amount * (1.0 - tenacity))" in boss_debuff_src
                and "int(duration * (1.0 - tenacity))" in boss_debuff_src
            ),
            "boss_debuff_leaves_skill_down_untouched": (
                "kind == 'skill_down'" not in boss_debuff_src
                and "kind == 'atk_slow'" in boss_debuff_src
            ),
            "boss_debuff_delegates_to_mixin_store": (
                "super().apply_debuff(kind, amount, duration, source_team=source_team)"
                in boss_debuff_src
            ),
            "mixin_store_is_strongest_wins": (
                "if amount > self.atk_slow_amount or self.atk_slow_timer < duration:"
                in tower_debuff_src
                and "if amount > self.skill_down_amount"
                in tower_debuff_src
            ),
            "sanguine_thorn_silence_duration": int(
                catalog["sanguine_thorn"]["active"]["duration"]
            ),
            "sanguine_thorn_cooldown": int(
                catalog["sanguine_thorn"]["active"]["cooldown"]
            ),
            "sanguine_thorn_damage_amp": float(
                catalog["sanguine_thorn"]["active"]["damage_amp"]
            ),
            "astral_codex_silence_duration": int(
                catalog["astral_codex"]["active"]["silence_duration"]
            ),
            "astral_codex_trigger_enemies": int(
                catalog["astral_codex"]["active"]["trigger_enemies"]
            ),
            "astral_codex_cooldown": int(
                catalog["astral_codex"]["active"]["cooldown"]
            ),
            "hex_idol_silence_ticks": int(catalog["hex_idol"]["active"]["silence"]),
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
            f"{FIXTURE} is out of date; run boss_item_silence_source_oracle.py --write"
        )
    print(f"Verified {FIXTURE} ({fixture['case_count']} cases)")


source_fixture = generate_fixture


if __name__ == "__main__":
    main()
