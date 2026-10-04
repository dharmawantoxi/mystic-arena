"""Read-only source oracle for hero item enemy-unit aura delivery onto bosses.

Executes the real `update_auras`, `_collect_all_units` and `_aura_steel_aegis`
module functions from `hero_items.py`, together with the real
`TowerDebuffMixin.apply_miss_chance`/`_tick_tower_debuffs` (`_core.py`) and the
real `Boss.apply_debuff`/`Boss.apply_slow` from `bosses/base_boss.py` (with
`super().apply_debuff` rewired to the standalone `TowerDebuffMixin.apply_debuff`
store, plus the burn clock constants bound into that namespace).

In Python source:
* `update_auras(all_heroes)` (`hero_items.py:2760-2874`) collects every living
  unit with `all_units = _collect_all_units(all_heroes)` (`hero_items.py:2772`,
  helper at `hero_items.py:2913-2930`, which appends
  `getattr(g, "active_boss", None)` when the boss is alive) and then runs the
  Tier III enemy auras over that list:
  * Everfrost Guard Freezing Aura (`hero_items.py:2826-2844`):
    `u.apply_debuff("atk_slow", f_as, 30)` plus
    `u.apply_debuff("anti_heal", f_heal, 30)`.
  * Solar Brand Scorched Earth (`hero_items.py:2845-2860`):
    `u.apply_debuff("burn", s_burn, 30, source_team=src.team)` plus
    `u.apply_miss_chance(s_blind, 30)` behind `hasattr(u, "apply_miss_chance")`.
  * Searbrand Cauterize (`hero_items.py:2861-2873`):
    `u.apply_debuff("anti_heal", se_heal, 30)` plus
    `u.apply_debuff("burn", se_burn, 30, source_team=src.team)`.
* `Boss.apply_debuff` (`bosses/base_boss.py:540-552`) cuts only `atk_slow` by
  tenacity 0.50 (`min(0.35, amount * (1.0 - tenacity))`,
  `int(duration * (1.0 - tenacity))`) before the `TowerDebuffMixin` store
  (`_core.py:918-947`); its burn branch resets `burn_accum = 0.0` and
  `burn_tick_cd = TOWER_DEBUFF_BURN_TICK` whenever the previous burn already
  expired. `TowerDebuffMixin.apply_miss_chance` (`_core.py:909-916`) stores the
  Solar Brand blind with the strongest-or-longer rule.

Before layer 8y, `PrototypeBattle._update_auras`
(`godot_rebuild/scripts/match/prototype_battle.gd`) sent the Freezing Aura
attack-speed slow to the world-level strongest-wins store, so a boss inside the
300 px radius ran the untempered 0.30 payload for 30 ticks instead of the boss
store's tenacity-cut 0.15/15; and `BattleItemEffects.apply_burn` wrote the boss
burn fields directly, keeping a stale `burn_tick_cd` from an expired burn.

Four scenarios are recorded for each of the 216 boss types (864 cases total),
each carrying `expected` (source `u.apply_debuff` -> `Boss.apply_debuff`) and
`expected_without_boss_store` (the pre-layer native delivery: the world store
for the aura arms, the raw field write for the Brand Burst burn). `--write`
rewrites the fixture.
"""
import ast
import json
import math
import sys
import types
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
    _method_text,
    boss_debuff_functions,
)

FIXTURE = Path(__file__).parent / "fixtures/boss_item_aura_source.json"

SCENARIOS = (
    "everfrost_freezing_aura_on_boss",
    "solar_scorched_earth_on_boss",
    "searbrand_cauterize_on_boss",
    "brand_burst_burn_after_expired_burn",
)

# Source teams are the strings "blue"/"red"; the dummies use the native team ids
# (0/1) so the fixture rows can be replayed verbatim by the GDScript suite. The
# aura only compares team equality and forwards `source_team` verbatim, and the
# `source_team is not None` store guard maps to the native `source_team >= 0`.
BLUE = 0
RED = 1
AURA_DEBUFF_TICKS = 30
BURN_TICK = 30
EXPIRED_BURN_TOTAL = 7
EXPIRED_BURN_TICKS = 7
BRAND_BURST_TICKS = 23


def _compact(text):
    return "".join(text.split())


def _tower_runtime():
    """`TowerDebuffMixin` status clocks plus their two burn constants."""
    tree = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    mixin = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "TowerDebuffMixin"
    )
    wanted = {"apply_miss_chance", "_tick_tower_debuffs"}
    methods = [
        node for node in mixin.body if isinstance(node, ast.FunctionDef) and node.name in wanted
    ]
    assert {node.name for node in methods} == wanted, "tower debuff methods missing"
    constants = []
    for name in ("TOWER_DEBUFF_BURN_TICK", "TOWER_DEBUFF_FPS"):
        constants.append(
            next(
                node
                for node in tree.body
                if isinstance(node, ast.Assign)
                and getattr(node.targets[0], "id", "") == name
            )
        )
    env = {"__builtins__": __builtins__, "math": math}
    module = ast.Module(body=constants + methods, type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), "_tower_debuff_clock", "exec"), env)
    assert env["TOWER_DEBUFF_BURN_TICK"] == BURN_TICK
    assert env["TOWER_DEBUFF_FPS"] == 60.0
    return env


def _build_runtime():
    item_env = item_source_namespace(with_inventory=True)
    _install_effect_stubs(item_env)
    item_env["math"] = math
    catalog = item_env["ITEM_CATALOG"]
    inv_cls = inventory_type(item_env)

    aura_module = ast.Module(
        body=[
            _func_node("update_auras", "hero_items.py"),
            _func_node("_collect_all_units", "hero_items.py"),
        ],
        type_ignores=[],
    )
    ast.fix_missing_locations(aura_module)
    exec(compile(aura_module, "_hero_item_aura_source", "exec"), item_env)

    tower_env = _tower_runtime()
    boss_cls = boss_ability_class()
    debuff_fns = boss_debuff_functions()
    # `TowerDebuffMixin.apply_debuff` reads TOWER_DEBUFF_BURN_TICK from the
    # spliced module globals; bind the real constant so the burn branch runs.
    spliced_globals = debuff_fns["apply_debuff"].__globals__
    spliced_globals["TOWER_DEBUFF_BURN_TICK"] = tower_env["TOWER_DEBUFF_BURN_TICK"]
    spliced_globals["TOWER_DEBUFF_FPS"] = tower_env["TOWER_DEBUFF_FPS"]
    boss_cls.apply_slow = debuff_fns["apply_slow"]
    boss_cls.apply_debuff = debuff_fns["apply_debuff"]
    boss_cls.apply_miss_chance = tower_env["apply_miss_chance"]
    return catalog, inv_cls, boss_cls, debuff_fns, tower_env, item_env


class _FakeGame:
    """Stands in for `__main__.game_instance` in `_collect_all_units`."""

    def __init__(self, minions, boss):
        self.minions = minions
        self.active_boss = boss


class _GameContext:
    def __init__(self, minions):
        self.minions = minions
        self.active_boss = None
        self.module = None
        self.saved = None

    def __enter__(self):
        import __main__

        self.module = __main__
        self.saved = getattr(__main__, "game_instance", None)
        __main__.game_instance = self
        return self

    def __exit__(self, *exc):
        if self.saved is None:
            try:
                delattr(self.module, "game_instance")
            except AttributeError:
                pass
        else:
            self.module.game_instance = self.saved
        return False


class _AuraMinion:
    """Living red minion far from every aura so only the boss is in range."""

    def __init__(self):
        self.id = 2
        self.team = RED
        self.alive = True
        self.x = 900.0
        self.y = 0.0
        self.hp = 5000
        self.max_hp = 5000

    def apply_debuff(self, kind, amount, duration, source_team=None):
        return None

    def apply_slow(self, amount, duration):
        return None


class _AuraOwner:
    """Aura holder hero; the inventory is attached after `add()` runs."""

    def __init__(self, team, x, y):
        self.id = 1
        self.team = team
        self.alive = True
        self.x = x
        self.y = y
        self.hp = 1000
        self.max_hp = 1000
        self.base_max_hp = 1000
        self.facing = 1
        self.role = "Bruiser"
        self.range = 70
        self.is_melee_hero = True
        self.level = 1
        self.kills = 0
        self.target = None


def _prepare_boss(boss_cls, boss_type):
    boss = make_boss(boss_cls, boss_type)
    stats = SOURCE_STATS[boss_type]
    boss.id = 500
    boss.team = RED
    boss.alive = True
    boss.defeated = False
    boss.x = 200.0
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
    boss.burn_tick_cd = BURN_TICK
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
    boss.take_damage = lambda *args, **kwargs: 0
    return boss


def _pre_fix_deliver(boss, kind, amount, duration, source_team, burn_field_write):
    """Pre-8y native delivery for the aura and item-burn arms.

    Aura arms went through the world store (`minion_battle.apply_atk_slow` /
    `apply_anti_heal` / `apply_burn`: strongest-or-longer refresh, and the burn
    clock reset only in the world store), while `BattleItemEffects.apply_burn`
    wrote the boss burn fields directly and never touched the burn clock.
    """
    if kind == "atk_slow":
        if float(amount) > float(boss.atk_slow_amount) or int(boss.atk_slow_timer) < int(
            duration
        ):
            boss.atk_slow_amount = float(amount)
            boss.atk_slow_timer = int(duration)
    elif kind == "anti_heal":
        if float(amount) > float(boss.anti_heal_amount) or int(boss.anti_heal_timer) < int(
            duration
        ):
            boss.anti_heal_amount = float(amount)
            boss.anti_heal_timer = int(duration)
    elif kind == "burn":
        if burn_field_write:
            boss.burn_dps = max(float(boss.burn_dps), float(amount))
            boss.burn_timer = max(int(boss.burn_timer), int(duration))
            boss.burn_team = source_team
            return
        if int(boss.burn_timer) <= 0:
            boss.burn_dps = float(amount)
            boss.burn_accum = 0.0
            boss.burn_tick_cd = BURN_TICK
        else:
            boss.burn_dps = max(float(boss.burn_dps), float(amount))
        boss.burn_timer = max(int(boss.burn_timer), int(duration))
        boss.burn_team = source_team


def _install_recorder(boss, debuff_fns, tower_env, boss_store, burn_field_write):
    calls = {"atk_slow": [], "anti_heal": [], "burn": [], "miss_chance": []}

    def record_debuff(kind, amount, duration, source_team=None):
        if kind == "burn":
            team = -1 if source_team is None else int(source_team)
            calls["burn"].append([round(float(amount), 6), int(duration), team])
        elif kind in ("atk_slow", "anti_heal"):
            calls[kind].append([round(float(amount), 6), int(duration)])
        if boss_store:
            debuff_fns["apply_debuff"](boss, kind, amount, duration, source_team)
        else:
            _pre_fix_deliver(boss, kind, amount, duration, source_team, burn_field_write)

    def record_miss(amount, duration):
        calls["miss_chance"].append([round(float(amount), 6), int(duration)])
        tower_env["apply_miss_chance"](boss, amount, duration)

    boss.apply_debuff = record_debuff
    boss.apply_miss_chance = record_miss
    return calls


def _run_scenario(
    inv_cls, boss_cls, debuff_fns, tower_env, item_env, boss_type, scenario, boss_store
):
    update_fn = item_env["update_auras"]
    boss = _prepare_boss(boss_cls, boss_type)
    burn_field_write = scenario == "brand_burst_burn_after_expired_burn"
    calls = _install_recorder(
        boss, debuff_fns, tower_env, boss_store, burn_field_write
    )
    burn_damage = 0

    if burn_field_write:
        # Set-up burn (identical in both columns) through the real Boss store,
        # then let it tick out: burn_timer 0, burn_accum 0 and a stale clock.
        debuff_fns["apply_debuff"](boss, "burn", 21.0, EXPIRED_BURN_TICKS, BLUE)
        for _ in range(EXPIRED_BURN_TICKS):
            tower_env["_tick_tower_debuffs"](boss)
        before = {
            "burn_dps": round(float(boss.burn_dps), 6),
            "burn_timer": int(boss.burn_timer),
            "burn_accum": round(float(boss.burn_accum), 6),
            "burn_tick_cd": int(boss.burn_tick_cd),
        }
        # Brand Burst item burn delivery onto the active boss
        # (`hero_items.py:614-622` -> `effects.apply_burn`).
        boss.apply_debuff("burn", 22.0, 180, BLUE)
        delivered = {
            "burn_dps": round(float(boss.burn_dps), 6),
            "burn_timer": int(boss.burn_timer),
            "burn_accum": round(float(boss.burn_accum), 6),
            "burn_tick_cd": int(boss.burn_tick_cd),
            "burn_team": -1 if boss.burn_team is None else int(boss.burn_team),
        }
        taken = []
        boss.take_damage = (
            lambda damage, *args, **kwargs: taken.append(int(damage)) or 0
        )
        for _ in range(BRAND_BURST_TICKS):
            tower_env["_tick_tower_debuffs"](boss)
        burn_damage = sum(taken)
    else:
        before = {}
        delivered = {}
        item_id = {
            "everfrost_freezing_aura_on_boss": "everfrost_guard",
            "solar_scorched_earth_on_boss": "solar_brand",
            "searbrand_cauterize_on_boss": "searbrand",
        }[scenario]
        owner = _AuraOwner(BLUE, 0.0, 0.0)
        inv = inv_cls(owner)
        assert inv.add(item_id), f"{item_id} not equippable by the dummy owner"
        owner.items = inv
        # `add()` runs the real `_on_item_changed`, which recomputes max HP from
        # hero stats this dummy does not model; restore the live values.
        owner.hp = 1000
        owner.max_hp = 1000
        with _GameContext([_AuraMinion()]) as game:
            game.active_boss = boss
            update_fn([owner])

    return {
        "before_delivery": before,
        "after_delivery": delivered,
        "apply_atk_slow_calls": calls["atk_slow"],
        "apply_anti_heal_calls": calls["anti_heal"],
        "apply_burn_calls": calls["burn"],
        "apply_miss_chance_calls": calls["miss_chance"],
        "boss_atk_slow_amount": round(float(boss.atk_slow_amount), 6),
        "boss_atk_slow_timer": int(boss.atk_slow_timer),
        "boss_anti_heal_amount": round(float(boss.anti_heal_amount), 6),
        "boss_anti_heal_timer": int(boss.anti_heal_timer),
        "boss_burn_dps": round(float(boss.burn_dps), 6),
        "boss_burn_timer": int(boss.burn_timer),
        "boss_burn_team": -1 if boss.burn_team is None else int(boss.burn_team),
        "boss_burn_accum": round(float(boss.burn_accum), 6),
        "boss_burn_tick_cd": int(boss.burn_tick_cd),
        "boss_blind_amount": round(float(boss.blind_amount), 6),
        "boss_blind_timer": int(boss.blind_timer),
        "burn_damage_after_23_ticks": int(burn_damage),
    }


def generate_fixture():
    with _core_module():
        catalog, inv_cls, boss_cls, debuff_fns, tower_env, item_env = _build_runtime()
        debuff_src = _method_text("Boss", "apply_debuff", "bosses/base_boss.py")
        tower_src = _method_text("TowerDebuffMixin", "apply_debuff", "_core.py")
        update_src = _func_text("update_auras", "hero_items.py")
        collect_src = _func_text("_collect_all_units", "hero_items.py")
        update_flat = _compact(update_src)
        collect_flat = _compact(collect_src)

        cases = []
        for boss_type in sorted(SOURCE_STATS):
            tenacity = float(SOURCE_STATS[boss_type].get("tenacity", 0.50))
            for scenario in SCENARIOS:
                expected = _run_scenario(
                    inv_cls,
                    boss_cls,
                    debuff_fns,
                    tower_env,
                    item_env,
                    boss_type,
                    scenario,
                    True,
                )
                without = _run_scenario(
                    inv_cls,
                    boss_cls,
                    debuff_fns,
                    tower_env,
                    item_env,
                    boss_type,
                    scenario,
                    False,
                )
                assert (
                    expected["apply_atk_slow_calls"] == without["apply_atk_slow_calls"]
                ), "the aura atk_slow payload must reach the boss in both columns"
                assert (
                    expected["apply_anti_heal_calls"] == without["apply_anti_heal_calls"]
                )
                assert expected["apply_burn_calls"] == without["apply_burn_calls"]
                if scenario == "everfrost_freezing_aura_on_boss":
                    raw_amount, raw_duration = expected["apply_atk_slow_calls"][-1]
                    assert raw_amount == 0.30 and raw_duration == AURA_DEBUFF_TICKS
                    assert expected["boss_atk_slow_amount"] == round(
                        min(0.35, raw_amount * (1.0 - tenacity)), 6
                    )
                    assert expected["boss_atk_slow_timer"] == int(
                        raw_duration * (1.0 - tenacity)
                    )
                    assert without["boss_atk_slow_amount"] == raw_amount
                    assert without["boss_atk_slow_timer"] == raw_duration
                    assert expected["boss_atk_slow_amount"] < without["boss_atk_slow_amount"]
                    assert expected["boss_atk_slow_timer"] < without["boss_atk_slow_timer"]
                    # Anti-heal is not tenacity-cut in either delivery.
                    assert expected["boss_anti_heal_amount"] == 0.40
                    assert expected["boss_anti_heal_timer"] == AURA_DEBUFF_TICKS
                    assert (
                        expected["boss_anti_heal_amount"]
                        == without["boss_anti_heal_amount"]
                    )
                    assert expected["boss_anti_heal_timer"] == without["boss_anti_heal_timer"]
                elif scenario == "solar_scorched_earth_on_boss":
                    assert expected["apply_burn_calls"] == [[28.0, 30, BLUE]]
                    assert expected["boss_burn_dps"] == 28.0
                    assert expected["boss_burn_timer"] == AURA_DEBUFF_TICKS
                    assert expected["boss_burn_team"] == BLUE
                    assert expected["boss_burn_tick_cd"] == BURN_TICK
                    assert expected["boss_blind_amount"] == 0.18
                    assert expected["boss_blind_timer"] == AURA_DEBUFF_TICKS
                    assert expected["boss_burn_dps"] == without["boss_burn_dps"]
                    assert expected["boss_burn_tick_cd"] == without["boss_burn_tick_cd"]
                    assert expected["boss_blind_amount"] == without["boss_blind_amount"]
                elif scenario == "searbrand_cauterize_on_boss":
                    assert expected["apply_anti_heal_calls"] == [[0.50, 30]]
                    assert expected["apply_burn_calls"] == [[6.0, 30, BLUE]]
                    assert expected["boss_anti_heal_amount"] == 0.50
                    assert expected["boss_anti_heal_timer"] == AURA_DEBUFF_TICKS
                    assert expected["boss_burn_dps"] == 6.0
                    assert expected["boss_burn_timer"] == AURA_DEBUFF_TICKS
                    assert expected["boss_burn_team"] == BLUE
                    assert (
                        expected["boss_anti_heal_amount"]
                        == without["boss_anti_heal_amount"]
                    )
                    assert expected["boss_burn_dps"] == without["boss_burn_dps"]
                else:
                    assert expected["before_delivery"] == {
                        "burn_dps": 0.0,
                        "burn_timer": 0,
                        "burn_accum": 0.0,
                        "burn_tick_cd": 23,
                    }
                    assert expected["apply_burn_calls"] == [[22.0, 180, BLUE]]
                    assert expected["after_delivery"]["burn_tick_cd"] == BURN_TICK
                    assert expected["after_delivery"]["burn_accum"] == 0.0
                    assert expected["after_delivery"]["burn_dps"] == 22.0
                    assert expected["after_delivery"]["burn_timer"] == 180
                    assert expected["after_delivery"]["burn_team"] == BLUE
                    assert expected["burn_damage_after_23_ticks"] == 0
                    assert without["after_delivery"]["burn_tick_cd"] == 23
                    assert (
                        without["burn_damage_after_23_ticks"]
                        == int(22.0 / 60.0 * BRAND_BURST_TICKS)
                    )
                    assert expected["burn_damage_after_23_ticks"] < without[
                        "burn_damage_after_23_ticks"
                    ]
                cases.append(
                    {
                        "boss_type": boss_type,
                        "boss_class": str(SOURCE_STATS[boss_type]["boss_class"]),
                        "scenario": scenario,
                        "pre_fix_delivery": (
                            "burn_field_write"
                            if scenario == "brand_burst_burn_after_expired_burn"
                            else "world_store"
                        ),
                        "expected": expected,
                        "expected_without_boss_store": without,
                    }
                )

    return {
        "source": {
            "auras_loop_over_collected_units": (
                "all_units = _collect_all_units(all_heroes)" in update_src
                and "for u in all_units:" in update_src
            ),
            "collect_all_units_appends_live_boss": (
                "boss = getattr(g, 'active_boss', None)" in collect_src
                and "units.append(boss)" in collect_src
            ),
            "collect_all_units_requires_alive_boss": (
                "getattr(boss, 'alive', False)" in collect_src
            ),
            "everfrost_aura_applies_atk_slow_and_anti_heal": (
                "u.apply_debuff('atk_slow', f_as, 30)" in update_src
                and "u.apply_debuff('anti_heal', f_heal, 30)" in update_src
            ),
            "solar_aura_burns_with_source_team": (
                _compact("u.apply_debuff('burn', s_burn, 30, source_team=src.team)")
                in update_flat
            ),
            "solar_aura_blinds_via_miss_chance": (
                "if hasattr(u, 'apply_miss_chance'):" in update_src
                and "u.apply_miss_chance(s_blind, 30)" in update_src
            ),
            "searbrand_aura_applies_anti_heal_and_burn": (
                "u.apply_debuff('anti_heal', se_heal, 30)" in update_src
                and _compact("u.apply_debuff('burn', se_burn, 30, source_team=src.team)")
                in update_flat
            ),
            "aura_arms_skip_the_source_team": (
                "if u_team == src.team:" in update_src
            ),
            "boss_apply_debuff_cuts_only_atk_slow": (
                "kind == 'atk_slow'" in debuff_src
                and "min(0.35, amount * (1.0 - tenacity))" in debuff_src
                and "kind == 'burn'" not in debuff_src
            ),
            "tower_store_resets_expired_burn_clock": (
                "self.burn_accum = 0.0" in tower_src
                and "self.burn_tick_cd = TOWER_DEBUFF_BURN_TICK" in tower_src
            ),
            "everfrost_aura_radius": int(catalog["everfrost_guard"]["aura"]["enemy_radius"]),
            "everfrost_aura_atk_slow": float(
                catalog["everfrost_guard"]["aura"]["enemy_atk_slow"]
            ),
            "everfrost_aura_anti_heal": float(
                catalog["everfrost_guard"]["aura"]["enemy_anti_heal"]
            ),
            "solar_aura_radius": int(catalog["solar_brand"]["aura"]["enemy_radius"]),
            "solar_aura_burn_dps": float(catalog["solar_brand"]["aura"]["burn_dps"]),
            "solar_aura_blind": float(catalog["solar_brand"]["aura"]["blind"]),
            "searbrand_aura_radius": int(catalog["searbrand"]["aura"]["enemy_radius"]),
            "searbrand_aura_anti_heal": float(
                catalog["searbrand"]["aura"]["enemy_anti_heal"]
            ),
            "searbrand_aura_burn_dps": float(catalog["searbrand"]["aura"]["burn_dps"]),
            "searbrand_burst_burn_dps": float(catalog["searbrand"]["active"]["burn_dps"]),
            "searbrand_burst_burn_duration": int(
                catalog["searbrand"]["active"]["burn_duration"]
            ),
            "aura_debuff_ticks": AURA_DEBUFF_TICKS,
            "burn_tick": BURN_TICK,
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
            f"{FIXTURE} is out of date; run boss_item_aura_source_oracle.py --write"
        )
    print(f"Verified {FIXTURE} ({fixture['case_count']} cases)")


source_fixture = generate_fixture


if __name__ == "__main__":
    main()
