"""Read-only source oracle for hero item cleave/chain secondary targets.

Executes the real `HeroItemInventory.on_basic_attack_hit` and
`HeroItemInventory._on_hit_common` from `hero_items.py` (plus the real
`get_cleave` / `get_on_attack_chain` getters) over the candidate list that the
source hero builds for on-hit items, with a real `Boss` from
`bosses/boss_data.py` standing in as `game.active_boss`.

In Python source:
* The melee on-hit call site builds `_all_units = list(gi.minions) +
  list(gi.get_all_heroes())` and then `_all_units.append(gi.active_boss)` when
  `gi.active_boss` is alive (`_entity.py:4401-4410`); the ranged call site uses
  `Hero._collect_onhit_units()` (`_entity.py:4215-4232`), which appends the
  living boss the same way, and both pass that list to the inventory.
* Cleave (`hero_items.py:2504-2518`) iterates `for u in all_units:` and splashes
  `int(damage * pct)` on every living enemy unit with
  `math.hypot(u.x - target.x, u.y - target.y) <= radius` (inclusive).
* Arc chain (`hero_items.py:2552-2560`) starts from `hit = [target]`, appends
  every living enemy unit inside `chain["radius"]` in list order, breaks as soon
  as `len(hit) >= chain["targets"]`, and then damages every entry with
  `u.take_damage(chain["damage"], h.team, "magic")`.

Because the boss is part of `all_units`, the boss is a legal secondary target of
both effects. Before layer 8z the native bus scanned only `world.units`
(`godot_rebuild/scripts/match/battle_item_effects.gd`:
`cleave_splash` / `chain_targets`), and the registry never holds the boss
(`active_boss` only lives in `_by_id`), so a boss standing inside the cleave
radius or the arc radius never took splash or chain damage.

Four scenarios are recorded for each of the 216 boss types (864 cases total),
each carrying `expected` (source list, boss included) and
`expected_without_boss` (the same selection over `world.units` only). `--write`
rewrites the fixture.
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
    _install_effect_stubs,
    inventory_type,
    source_namespace as item_source_namespace,
)
from boss_ability_source_oracle import (  # noqa: E402
    SOURCE_STATS,
    make_boss,
    source_class as boss_ability_class,
)

FIXTURE = Path(__file__).parent / "fixtures/boss_item_cleave_chain_source.json"

SCENARIOS = (
    "cleave_splashes_boss_inside_radius",
    "cleave_skips_boss_outside_radius",
    "fenrir_chain_hits_boss",
    "chain_slots_fill_before_boss",
)

# Source teams are the strings "blue"/"red"; the dummies use the native team ids
# (0/1) so the GDScript suite can replay the rows verbatim.
BLUE = 0
RED = 1
MAIN_TARGET_ID = 10
NEAR_MINION_ID = 11
FAR_MINION_ID = 12
FILL_MINION_ID = 12
OWNER_ID = 7
BASIC_DAMAGE = 50

CLEAVE_ITEM = "cleave_axe"
CHAIN_ITEM = "fenrir_chain"

# Per-scenario world layout, replayed verbatim by the native suite.
LAYOUT = {
    "cleave_splashes_boss_inside_radius": {
        "item": CLEAVE_ITEM,
        "boss_offset": 60.0,
        "minions": [[NEAR_MINION_ID, 30.0], [FAR_MINION_ID, 900.0]],
    },
    "cleave_skips_boss_outside_radius": {
        "item": CLEAVE_ITEM,
        "boss_offset": 140.0,
        "minions": [[NEAR_MINION_ID, 30.0], [FAR_MINION_ID, 900.0]],
    },
    "fenrir_chain_hits_boss": {
        "item": CHAIN_ITEM,
        "boss_offset": 200.0,
        "minions": [[NEAR_MINION_ID, 30.0], [FAR_MINION_ID, 900.0]],
    },
    "chain_slots_fill_before_boss": {
        "item": CHAIN_ITEM,
        "boss_offset": 200.0,
        "minions": [[NEAR_MINION_ID, 10.0], [FILL_MINION_ID, 20.0]],
    },
}


def _class_node(class_name, source_file):
    tree = ast.parse((ROOT / source_file).read_text(encoding="utf-8"))
    return next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )


def _method_node(class_name, method_name, source_file):
    cls = _class_node(class_name, source_file)
    return next(
        node
        for node in cls.body
        if isinstance(node, ast.FunctionDef) and node.name == method_name
    )


def _method_text(class_name, method_name, source_file):
    return ast.unparse(_method_node(class_name, method_name, source_file))


def _func_node(func_name, source_file):
    tree = ast.parse((ROOT / source_file).read_text(encoding="utf-8"))
    return next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == func_name
    )


def _func_text(func_name, source_file):
    return ast.unparse(_func_node(func_name, source_file))


def _compact(text):
    return "".join(text.split())


class _AlwaysRandom:
    """`random.random()` always succeeds, so the on-hit rolls always fire."""

    def random(self):
        return 0.0


class _DummyUnit:
    """Minion / hero stand-in; records every `take_damage` call."""

    def __init__(self, unit_id, team, x, y=0.0):
        self.id = unit_id
        self.team = team
        self.alive = True
        self.x = x
        self.y = y
        self.hp = 5000
        self.max_hp = 5000
        self.hits = []

    def take_damage(self, damage, from_team=None, damage_type="normal", school="neutral"):
        self.hits.append(int(damage))
        return int(damage)

    def apply_armor_shred(self, *args, **kwargs):
        return None

    def apply_damage_amp(self, *args, **kwargs):
        return None

    def apply_debuff(self, *args, **kwargs):
        return None


class _DummyOwner:
    """Melee blue hero holding the item inventory."""

    def __init__(self, target):
        self.id = OWNER_ID
        self.team = BLUE
        self.alive = True
        self.x = 0.0
        self.y = 0.0
        self.hp = 1000
        self.max_hp = 1000
        self.base_max_hp = 1000
        self.facing = 1
        self.role = "Bruiser"
        self.range = 70
        self.is_melee_hero = True
        self.level = 1
        self.kills = 0
        self.target = target


def _build_runtime():
    item_env = item_source_namespace(with_inventory=True)
    _install_effect_stubs(item_env)
    item_env["math"] = math
    item_env["random"] = _AlwaysRandom()
    catalog = item_env["ITEM_CATALOG"]
    inv_cls = inventory_type(item_env)

    item_module = ast.Module(
        body=[
            _method_node("HeroItemInventory", "on_basic_attack_hit", "hero_items.py"),
            _method_node("HeroItemInventory", "_on_hit_common", "hero_items.py"),
            _method_node("HeroItemInventory", "get_cleave", "hero_items.py"),
            _method_node("HeroItemInventory", "get_on_attack_chain", "hero_items.py"),
        ],
        type_ignores=[],
    )
    ast.fix_missing_locations(item_module)
    exec(compile(item_module, "_hero_item_cleave_chain_source", "exec"), item_env)
    inv_cls.on_basic_attack_hit = item_env["on_basic_attack_hit"]
    inv_cls._on_hit_common = item_env["_on_hit_common"]
    inv_cls.get_cleave = item_env["get_cleave"]
    inv_cls.get_on_attack_chain = item_env["get_on_attack_chain"]

    boss_cls = boss_ability_class()
    return catalog, inv_cls, boss_cls


def _prepare_boss(boss_cls, boss_type, x):
    boss = make_boss(boss_cls, boss_type)
    boss.id = 500
    boss.team = RED
    boss.alive = True
    boss.defeated = False
    boss.x = float(x)
    boss.y = 0.0
    boss.hits = []
    boss.take_damage = _boss_recorder(boss)
    return boss


def _boss_recorder(boss):
    def _take_damage(damage, from_team=None, damage_type="normal", school="neutral"):
        if not getattr(boss, "alive", False):
            return 0
        boss.hits.append(int(damage))
        return int(damage)

    return _take_damage


def _run_scenario(catalog, inv_cls, boss_cls, boss_type, scenario, with_boss):
    layout = LAYOUT[scenario]
    boss = _prepare_boss(boss_cls, boss_type, layout["boss_offset"])
    target = _DummyUnit(MAIN_TARGET_ID, RED, 0.0)
    owner = _DummyOwner(target)
    minions = [
        _DummyUnit(int(minion_id), RED, float(offset))
        for minion_id, offset in layout["minions"]
    ]
    # Source order: `list(gi.minions) + list(gi.get_all_heroes())` then the boss.
    all_units = list(minions) + [owner]
    if with_boss:
        all_units.append(boss)

    inv = inv_cls(owner)
    assert inv.add(layout["item"]), f"cannot equip {layout['item']}"
    inv.on_basic_attack_hit(target, BASIC_DAMAGE, all_units)

    near = minions[0]
    chain = catalog[CHAIN_ITEM]["on_attack"]
    if layout["item"] == CLEAVE_ITEM:
        pct = float(catalog[CLEAVE_ITEM]["passive"]["cleave_pct"])
        splash = int(BASIC_DAMAGE * pct)
        chain_roles = []
        chain_damage_type = ""
    else:
        splash = int(chain["damage"])
        # Rebuild the source hit list from the recorded damage: `hit` starts with
        # the main target and then holds every appended unit in `all_units` order
        # (minions, heroes, boss last), and each entry is damaged exactly once.
        chain_roles = []
        if target.hits:
            chain_roles.append("target")
        for minion in minions:
            if minion.hits:
                chain_roles.append("minion")
        if boss.hits:
            chain_roles.append("boss")
        # Source passes "magic" as the third positional arg of
        # `u.take_damage(chain["damage"], h.team, "magic")`; the native replay
        # delivers the same arm through `effects.deal_damage(..., "magic")`.
        chain_damage_type = "magic"
    return {
        "splash_damage": splash,
        "target_hits": list(target.hits),
        "minion_hits": list(near.hits),
        "boss_hits": list(boss.hits),
        "chain_roles": chain_roles,
        "chain_damage_type": chain_damage_type,
    }


def generate_fixture():
    catalog, inv_cls, boss_cls = _build_runtime()
    onhit_src = _method_text("HeroItemInventory", "on_basic_attack_hit", "hero_items.py")
    common_src = _method_text("HeroItemInventory", "_on_hit_common", "hero_items.py")
    melee_call_src = _compact(_method_text("Hero", "_do_attack", "_entity.py"))
    collect_src = _compact(_method_text("Hero", "_collect_onhit_units", "_entity.py"))
    cleave_pct = float(catalog[CLEAVE_ITEM]["passive"]["cleave_pct"])
    cleave_radius = float(catalog[CLEAVE_ITEM]["passive"]["cleave_radius"])
    chain = catalog[CHAIN_ITEM]["on_attack"]
    coil = catalog["thunder_coil"]["on_attack"]

    cases = []
    for boss_type in sorted(SOURCE_STATS):
        for scenario in SCENARIOS:
            expected = _run_scenario(
                catalog, inv_cls, boss_cls, boss_type, scenario, True
            )
            without = _run_scenario(
                catalog, inv_cls, boss_cls, boss_type, scenario, False
            )
            assert expected["minion_hits"] == without["minion_hits"], (
                "the regular-unit arm of cleave/chain must not change"
            )
            if scenario == "cleave_splashes_boss_inside_radius":
                splash = int(BASIC_DAMAGE * cleave_pct)
                assert expected["boss_hits"] == [splash]
                assert expected["minion_hits"] == [splash]
                assert without["boss_hits"] == []
            elif scenario == "cleave_skips_boss_outside_radius":
                assert expected["boss_hits"] == []
                assert without["boss_hits"] == []
                assert expected["minion_hits"] == [int(BASIC_DAMAGE * cleave_pct)]
            elif scenario == "fenrir_chain_hits_boss":
                damage = int(chain["damage"])
                assert expected["boss_hits"] == [damage]
                assert expected["minion_hits"] == [damage]
                assert expected["target_hits"] == [damage]
                assert expected["chain_roles"] == ["target", "minion", "boss"]
                assert without["boss_hits"] == []
                assert without["chain_roles"] == ["target", "minion"]
            else:
                assert expected["boss_hits"] == []
                assert without["boss_hits"] == []
                assert expected["chain_roles"] == ["target", "minion", "minion"]
                assert without["chain_roles"] == ["target", "minion", "minion"]
            cases.append(
                {
                    "boss_type": boss_type,
                    "boss_class": str(SOURCE_STATS[boss_type]["boss_class"]),
                    "scenario": scenario,
                    "item": LAYOUT[scenario]["item"],
                    "expected": expected,
                    "expected_without_boss": without,
                }
            )

    return {
        "source": {
            "melee_onhit_list_appends_live_boss": (
                "_all_units.append(gi.active_boss)" in melee_call_src
                and "gi.active_boss.alive" in melee_call_src
            ),
            "collect_onhit_units_appends_live_boss": (
                "units.append(gi.active_boss)" in collect_src
                and "getattr(gi.active_boss,'alive',False)" in collect_src
            ),
            "cleave_iterates_all_units": (
                "for u in all_units:" in onhit_src
                and _compact("u.take_damage(splash, h.team)") in _compact(onhit_src)
            ),
            "cleave_radius_is_inclusive": "if d <= radius:" in onhit_src,
            "cleave_skips_same_team": "if u.team == h.team:" in onhit_src,
            "cleave_skips_the_main_target": "if u is target or not getattr(u, 'alive', False):"
            in onhit_src,
            "chain_iterates_all_units": "for u in all_units:" in common_src,
            "chain_appends_inside_radius": _compact("hit.append(u)") in _compact(common_src),
            "chain_breaks_when_slots_are_full": _compact(
                "if len(hit) >= chain['targets']:"
            )
            in _compact(common_src),
            "chain_damage_is_magic": _compact(
                "u.take_damage(chain['damage'], h.team, 'magic')"
            )
            in _compact(common_src),
            "cleave_pct": cleave_pct,
            "cleave_radius": cleave_radius,
            "chain_chance": float(chain["chance"]),
            "chain_damage": int(chain["damage"]),
            "chain_targets": int(chain["targets"]),
            "chain_radius": float(chain["radius"]),
            "coil_damage": int(coil["damage"]),
            "coil_targets": int(coil["targets"]),
            "coil_radius": float(coil["radius"]),
            "basic_damage": BASIC_DAMAGE,
            "scenario_layout": {
                name: {
                    "item": LAYOUT[name]["item"],
                    "boss_offset": float(LAYOUT[name]["boss_offset"]),
                    "minion_offsets": [
                        [int(minion_id), float(offset)]
                        for minion_id, offset in LAYOUT[name]["minions"]
                    ],
                }
                for name in SCENARIOS
            },
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
            f"{FIXTURE} is out of date; run boss_item_cleave_chain_source_oracle.py --write"
        )
    print(f"Verified {FIXTURE} ({fixture['case_count']} cases)")


source_fixture = generate_fixture


if __name__ == "__main__":
    main()
