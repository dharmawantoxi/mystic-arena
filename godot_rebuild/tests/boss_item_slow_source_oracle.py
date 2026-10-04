"""Read-only source oracle for hero item slow/root delivery onto active bosses.

Executes the real `HeroItemInventory.update` and `HeroItemInventory._on_hit_common`
from `hero_items.py`, together with the real `Boss.apply_slow` and
`Boss.apply_debuff` from `bosses/base_boss.py` (bound to the standalone
`TowerDebuffMixin.apply_debuff` store).

In Python source:
* Vine Rod Entangle (`hero_items.py:2652-2663`) sets `self.vine_cd` and calls
  `target.apply_slow(1.0, vr['root_duration'])` behind
  `hasattr(target, 'apply_slow')` - the root is a total (100%) movement slow.
* Everfrost Guard Arctic Blast (`hero_items.py:2283-2293`) slows every enemy in
  its `radius` with `e.apply_slow(act['slow'], act['slow_duration'])`.
* Frostbound Eye Frostbite (`hero_items.py:2589-2600`) applies
  `target.apply_slow(oa['slow'], oa['duration'])` plus
  `target.apply_debuff('atk_slow', ...)` and `apply_debuff('anti_heal', ...)`.
* `Boss.apply_slow` (`bosses/base_boss.py:528-538`) cuts magnitude and duration
  by tenacity 0.50 (`min(0.35, amount * (1.0 - tenacity))`,
  `int(duration * (1.0 - tenacity))`) and stores with the
  amount-greater-or-longer-refresh rule; `Boss.apply_debuff`
  (`bosses/base_boss.py:540-552`) applies the same cut to `atk_slow` only.

Before layer 8x, `BattleItemEffects.apply_slow`
(`godot_rebuild/scripts/match/battle_item_effects.gd`) always wrote the raw
`slow_amount`/`slow_timer` fields (max-wins), and `apply_atk_slow` went through
the world-level strongest-wins store, so a rooted or arctic-blasted boss ran the
untempered magnitude and duration.

Four scenarios are recorded for each of the 216 boss types (864 cases total),
each carrying `expected` (source `target.apply_slow`/`apply_debuff` ->
`Boss.apply_slow`/`apply_debuff`) and `expected_without_boss_tenacity` (the
pre-layer native bus store). `--write` rewrites the fixture.
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
from boss_item_silence_source_oracle import (  # noqa: E402
    _func_node,
    _func_text,
    _method_node,
    _method_text,
    _AlwaysProcRandom,
    boss_debuff_functions,
)

FIXTURE = Path(__file__).parent / "fixtures/boss_item_slow_source.json"

SCENARIOS = (
    "vine_rod_root_on_boss",
    "everfrost_arctic_blast_on_boss",
    "frostbound_frostbite_on_boss",
    "root_then_frostbite_store_rule",
)


def _build_runtime():
    item_env = item_source_namespace(with_inventory=True)
    _install_effect_stubs(item_env)
    item_env["math"] = math
    item_env["random"] = _AlwaysProcRandom()
    catalog = item_env["ITEM_CATALOG"]
    inv_cls = inventory_type(item_env)

    update_node = _method_node("HeroItemInventory", "update", "hero_items.py")
    on_hit_node = _method_node("HeroItemInventory", "_on_hit_common", "hero_items.py")
    silence_node = _func_node("_apply_silence_to", "hero_items.py")
    amp_node = _func_node("_apply_amp_to", "hero_items.py")
    stun_node = _func_node("_apply_stun_to", "hero_items.py")
    is_magic_hero_node = _func_node("is_magic_hero", "hero_items.py")
    item_module = ast.Module(
        body=[
            is_magic_hero_node,
            silence_node,
            amp_node,
            stun_node,
            update_node,
            on_hit_node,
        ],
        type_ignores=[],
    )
    ast.fix_missing_locations(item_module)
    exec(compile(item_module, "_hero_item_slow_source", "exec"), item_env)
    inv_cls.update = item_env["update"]
    inv_cls._on_hit_common = item_env["_on_hit_common"]

    boss_cls = boss_ability_class()
    debuff_fns = boss_debuff_functions()
    boss_cls.apply_slow = debuff_fns["apply_slow"]
    boss_cls.apply_debuff = debuff_fns["apply_debuff"]
    return catalog, inv_cls, boss_cls, debuff_fns, item_env


class _DummyTarget:
    """Second source-free enemy so Arctic Blast's 2+ gate can fire."""

    def __init__(self):
        self.id = 2
        self.team = "red"
        self.alive = True
        self.x = 30.0
        self.y = 0.0
        self.hp = 10000
        self.max_hp = 10000
        self.slows = []
        self.debuffs = []

    def take_damage(
        self, damage, from_team, damage_type="normal", source=None, school=None
    ):
        if damage > 0:
            self.hp -= damage

    def apply_slow(self, amount, duration):
        self.slows.append([float(amount), int(duration)])

    def apply_debuff(self, kind, amount, duration, source_team=None):
        self.debuffs.append([kind, float(amount), int(duration)])


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
    boss.tenacity = float(stats.get("tenacity", 0.50))
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
    boss.take_damage = lambda *args, **kwargs: 0
    return boss


def _bus_slow(boss, amount, duration):
    """Pre-8x `BattleItemEffects.apply_slow`: raw max-wins field write."""
    boss.slow_amount = max(float(boss.slow_amount), float(amount))
    boss.slow_timer = max(int(boss.slow_timer), int(duration))


def _bus_debuff(boss, kind, amount, duration):
    """Pre-8x item/world store: strongest amount wins, longer refresh."""
    if kind == "slow":
        _bus_slow(boss, amount, duration)
    elif kind == "atk_slow":
        if float(amount) > float(boss.atk_slow_amount) or int(boss.atk_slow_timer) < int(
            duration
        ):
            boss.atk_slow_amount = float(amount)
            boss.atk_slow_timer = int(duration)
    elif kind == "anti_heal":
        if float(amount) > float(boss.anti_heal_amount) or int(
            boss.anti_heal_timer
        ) < int(duration):
            boss.anti_heal_amount = float(amount)
            boss.anti_heal_timer = int(duration)


def _install_recorder(boss, delivery_slow, delivery_debuff):
    calls = {"slow": [], "atk_slow": [], "anti_heal": []}

    def record_slow(amount, duration):
        calls["slow"].append([round(float(amount), 6), int(duration)])
        delivery_slow(boss, amount, duration)

    def record_debuff(kind, amount, duration, source_team=None):
        if kind in ("atk_slow", "anti_heal"):
            calls[kind].append([round(float(amount), 6), int(duration)])
        delivery_debuff(boss, kind, amount, duration)

    boss.apply_slow = record_slow
    boss.apply_debuff = record_debuff
    return calls


def _run_scenario(inv_cls, boss_cls, debuff_fns, item_env, boss_type, scenario, tenacity_on):
    boss = _prepare_boss(boss_cls, boss_type)
    extra = _DummyTarget()
    # `vine_rod` is `magic_only`, so its scenarios need the Mage hero for the
    # source `add()` gate (`is_magic_hero(role)`) to accept the item.
    vine_scenarios = ("vine_rod_root_on_boss", "root_then_frostbite_store_rule")
    role = "Mage" if scenario in vine_scenarios else "Bruiser"
    owner = _DummyHeroOwner(role, boss)
    inv = inv_cls(owner)

    if tenacity_on:
        calls = _install_recorder(
            boss,
            lambda b, a, d: debuff_fns["apply_slow"](b, a, d),
            lambda b, k, a, d: debuff_fns["apply_debuff"](b, k, a, d),
        )
    else:
        calls = _install_recorder(boss, _bus_slow, _bus_debuff)

    if scenario == "vine_rod_root_on_boss":
        assert inv.add("vine_rod")
    elif scenario == "everfrost_arctic_blast_on_boss":
        assert inv.add("everfrost_guard")
    elif scenario == "frostbound_frostbite_on_boss":
        assert inv.add("frostbound_eye")
    elif scenario == "root_then_frostbite_store_rule":
        assert inv.add("vine_rod")
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
    # `add()` runs the real `_on_item_changed`, which recomputes the owner max
    # HP from hero stats this dummy does not model; restore the live values so
    # the source `h.alive and h.max_hp > 0` gate in `update` opens.
    owner.hp = 1000
    owner.max_hp = 1000

    if scenario == "vine_rod_root_on_boss":
        inv._on_hit_common(boss, 50, [boss])
    elif scenario == "everfrost_arctic_blast_on_boss":
        inv.update(1, [boss, extra])
    elif scenario == "frostbound_frostbite_on_boss":
        inv._on_hit_common(boss, 50, [boss])
    elif scenario == "root_then_frostbite_store_rule":
        inv._on_hit_common(boss, 50, [boss])
        assert inv.add("frostbound_eye")
        inv._on_hit_common(boss, 50, [boss])

    return {
        "slow_calls": calls["slow"],
        "atk_slow_calls": calls["atk_slow"],
        "anti_heal_calls": calls["anti_heal"],
        "boss_slow_amount": round(float(boss.slow_amount), 6),
        "boss_slow_timer": int(boss.slow_timer),
        "boss_atk_slow_amount": round(float(boss.atk_slow_amount), 6),
        "boss_atk_slow_timer": int(boss.atk_slow_timer),
        "boss_anti_heal_amount": round(float(boss.anti_heal_amount), 6),
        "boss_anti_heal_timer": int(boss.anti_heal_timer),
        "cooldowns": {"vine_rod": int(inv.vine_cd), "everfrost_guard": int(inv.arctic_cd)},
    }


def generate_fixture():
    with _core_module():
        catalog, inv_cls, boss_cls, debuff_fns, item_env = _build_runtime()
        slow_src = _method_text("Boss", "apply_slow", "bosses/base_boss.py")
        debuff_src = _method_text("Boss", "apply_debuff", "bosses/base_boss.py")
        on_hit_src = _method_text("HeroItemInventory", "_on_hit_common", "hero_items.py")
        update_src = _method_text("HeroItemInventory", "update", "hero_items.py")

        cases = []
        for boss_type in sorted(SOURCE_STATS):
            tenacity = float(SOURCE_STATS[boss_type].get("tenacity", 0.50))
            for scenario in SCENARIOS:
                expected = _run_scenario(
                    inv_cls, boss_cls, debuff_fns, item_env, boss_type, scenario, True
                )
                without_tenacity = _run_scenario(
                    inv_cls, boss_cls, debuff_fns, item_env, boss_type, scenario, False
                )
                assert expected["slow_calls"] == without_tenacity["slow_calls"]
                assert expected["slow_calls"], "item slow arm did not reach the boss"
                raw_amount, raw_duration = expected["slow_calls"][-1]
                assert expected["boss_slow_amount"] == round(
                    min(0.35, raw_amount * (1.0 - tenacity)), 6
                )
                assert expected["boss_slow_timer"] == int(raw_duration * (1.0 - tenacity))
                if expected["atk_slow_calls"]:
                    raw_atk, raw_atk_duration = expected["atk_slow_calls"][-1]
                    assert expected["boss_atk_slow_amount"] == round(
                        min(0.35, raw_atk * (1.0 - tenacity)), 6
                    )
                    assert expected["boss_atk_slow_timer"] == int(
                        raw_atk_duration * (1.0 - tenacity)
                    )
                    assert expected["boss_anti_heal_amount"] == round(
                        expected["anti_heal_calls"][-1][0], 6
                    )
                    assert expected["boss_anti_heal_timer"] == int(
                        expected["anti_heal_calls"][-1][1]
                    )
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
            "vine_rod_roots_with_full_slow": (
                "target.apply_slow(1.0, vr['root_duration'])" in on_hit_src
                and "hasattr(target, 'apply_slow')" in on_hit_src
            ),
            "vine_rod_cooldown_armed_before_root": (
                "self.vine_cd = vr['cooldown']" in on_hit_src
            ),
            "arctic_blast_slows_each_nearby_enemy": (
                "e.apply_slow(act['slow'], act['slow_duration'])" in update_src
            ),
            "arctic_blast_uses_hasattr_gate": (
                "if hasattr(e, 'apply_slow'):" in update_src
            ),
            "frostbite_slows_target": (
                "target.apply_slow(oa['slow'], oa['duration'])" in on_hit_src
            ),
            "frostbite_applies_atk_slow_and_anti_heal": (
                "target.apply_debuff('atk_slow', oa['atk_slow'], oa['duration'])"
                in on_hit_src
                and "target.apply_debuff('anti_heal', oa['anti_heal'], oa['duration'])"
                in on_hit_src
            ),
            "boss_apply_slow_cuts_by_tenacity": (
                "min(0.35, amount * (1.0 - tenacity))" in slow_src
                and "int(duration * (1.0 - tenacity))" in slow_src
            ),
            "boss_apply_slow_uses_amount_or_timer_store": (
                "if reduced_amount > getattr(self, 'slow_amount', 0.0) or"
                in slow_src
            ),
            "boss_apply_debuff_cuts_only_atk_slow": (
                "kind == 'atk_slow'" in debuff_src
                and "kind == 'skill_down'" not in debuff_src
            ),
            "vine_rod_root_magnitude": 1.0,
            "vine_rod_root_duration": int(catalog["vine_rod"]["on_attack"]["root_duration"]),
            "vine_rod_cooldown": int(catalog["vine_rod"]["on_attack"]["cooldown"]),
            "everfrost_slow": float(catalog["everfrost_guard"]["active"]["slow"]),
            "everfrost_slow_duration": int(
                catalog["everfrost_guard"]["active"]["slow_duration"]
            ),
            "everfrost_radius": float(catalog["everfrost_guard"]["active"]["radius"]),
            "everfrost_trigger_enemies": int(
                catalog["everfrost_guard"]["active"]["trigger_enemies"]
            ),
            "everfrost_cooldown": int(catalog["everfrost_guard"]["active"]["cooldown"]),
            "frostbound_slow": float(catalog["frostbound_eye"]["on_attack"]["slow"]),
            "frostbound_atk_slow": float(
                catalog["frostbound_eye"]["on_attack"]["atk_slow"]
            ),
            "frostbound_anti_heal": float(
                catalog["frostbound_eye"]["on_attack"]["anti_heal"]
            ),
            "frostbound_duration": int(catalog["frostbound_eye"]["on_attack"]["duration"]),
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
            f"{FIXTURE} is out of date; run boss_item_slow_source_oracle.py --write"
        )
    print(f"Verified {FIXTURE} ({fixture['case_count']} cases)")


source_fixture = generate_fixture


if __name__ == "__main__":
    main()
