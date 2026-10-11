"""Layer 9x oracle: the minion basic attack is school-free.

`_entity.py::Minion.update` (`:5568-5580`) attacks with

    self.target.take_damage(self.damage, self.team)

- two positional arguments, no `source=`, no school and no `damage_type`, so
`resolve_damage_school('normal', None, None, target_is_hero=False)` returns
`None` (`_entity.py:106-130`). Every victim of a minion melee hit therefore
lands school-free:

* **tower/nexus** - `Tower.take_damage` skips the `_sch == 'physical'` armour
  branch, so the structure shield/reduction ladder runs without armour;
* **minion** - `Minion.take_damage` skips both the armour and the
  `magic_resist` branch (the Soul Rend amp still applies);
* **hero** - the hero armour is `damage_type != 'fire'` driven, so it still
  lands identically; the sourceless shape only drops the credit
  (`credit_hero_damage(None, ...)`), the Razor Carapace reflect
  (`notify_damage_taken(source=None)` never reflects) and the caster's blind;
* **boss** - `Boss.take_damage` skips armour and magic resist.

The native `apply_hit` (the only production caller of the minion attack, the
AI loop at `minion_battle.gd:186`) handed the attacker id and the declared
`"physical"` school to `_deliver_hit`, so tower armour 3 cut an orc hit 13 -> 11,
troll armour 2 cut it to 12, boss armour/resist cut it, and a hero with Razor
Carapace reflected 85% back to the minion. A **hero** attacker through the same
utility keeps the source `Hero` melee shape (`_entity.py:4371-4373` sends
`source=self` plus the declared school), so that branch is pinned as a control.

`--self-test` verifies the executed ladder against the committed fixture;
`--write` is the only fixture writer.
"""

import argparse
import ast
import json
import textwrap
import types
from pathlib import Path

from hero_skill_sourceless_source_oracle import (  # noqa: E402
    _StubTower,
    _tower_take_damage,
)
from hero_veil_immunity_source_oracle import (  # noqa: E402
    _case as _hero_case,
    _run_case as _hero_run_case,
    _take_damage_callable,
)
from minion_damage_ladder_source_oracle import (  # noqa: E402
    _case as _minion_case,
    _run_case as _minion_run_case,
    _minion_take_damage_callable,
)

FIXTURE = Path(__file__).parent / "fixtures/minion_melee_school_source.json"
ROOT = Path(__file__).resolve().parents[2]
ENTITY = ROOT / "_entity.py"
ORC = ROOT / "godot_rebuild/data/minions/orc.tres"
TROLL = ROOT / "godot_rebuild/data/minions/troll.tres"
ARCHER = ROOT / "godot_rebuild/data/structures/archer_level_1.tres"
CATALOG = ROOT / "godot_rebuild/data/ai/item_catalog.json"
ARMOR_ITEM = "steel_aegis"


def _tres_number(path, key, default=None):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(key + " ="):
            return float(line.split("=", 1)[1].strip())
    if default is not None:
        return default
    raise AssertionError("missing %s in %s" % (key, path))


def _live_stats():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    return {
        "orc_damage": int(_tres_number(ORC, "damage")),
        "orc_attack_range_px": _tres_number(ORC, "attack_range_px"),
        "tower_armor": int(_tres_number(ARCHER, "armor")),
        "troll_armor": int(_tres_number(TROLL, "armor")),
        "troll_magic_resist": _tres_number(TROLL, "magic_resist"),
        "hero_armor": int(catalog["items"][ARMOR_ITEM]["stats"]["armor"]),
    }


def _tower_ladder(payload, school, armor):
    take_damage, _namespace = _tower_take_damage()
    victim = _StubTower(armor)
    ladder = types.MethodType(take_damage, victim)
    hp_before = float(victim.hp)
    ladder(payload, "blue", "normal", source=None, school=school)
    return {"hp_loss": int(round(hp_before - float(victim.hp))), "credited_total": 0}


def _minion_ladder(payload, school, stats):
    take_damage, _resolve, _credits = _minion_take_damage_callable()
    case = _minion_case(
        "minion_melee",
        damage=payload,
        damage_type="normal",
        school=school,
        source_school=None,
        armor=int(stats["troll_armor"]),
        magic_resist=stats["troll_magic_resist"],
    )
    result = _minion_run_case(take_damage, case)
    return {
        "hp_loss": int(result["hp_loss"]),
        "credited_total": sum(
            amount for amount, credited in zip(result["credit"], result["credited"]) if credited
        ),
    }


def _hero_ladder(payload, school, armor):
    take_damage, _credits = _take_damage_callable()
    case = _hero_case(
        "minion_melee",
        damage=payload,
        damage_type="normal",
        school=school,
        source_school=None,
        armor=int(armor),
        draws=[0.90],
    )
    result = _hero_run_case(take_damage, case)
    return {
        "hp_loss": int(result["hp_loss"]),
        "credited_total": sum(
            amount for credited, amount in ((bool(row[0]), int(row[1])) for row in result["credits"]) if credited
        ),
    }


def _source_call_shape():
    """The two positional arguments of `Minion.update`, plus the hero contrast."""
    text = ENTITY.read_text(encoding="utf-8")
    tree = ast.parse(text)
    minion = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Minion")
    hero = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Hero")

    def collect(holder):
        rows = []
        for node in ast.walk(holder):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute) or node.func.attr != "take_damage":
                continue
            rows.append(
                {
                    "args": len(node.args),
                    "kwargs": sorted(kw.arg for kw in node.keywords),
                    "sourced": any(kw.arg == "source" for kw in node.keywords),
                }
            )
        return rows

    minion_calls = collect(minion)
    two_positional = [row for row in minion_calls if row["args"] == 2 and not row["kwargs"]]
    return {
        "minion_take_damage_calls": len(minion_calls),
        "minion_two_positional_bare": len(two_positional),
        "minion_sourced_calls": sum(1 for row in minion_calls if row["sourced"]),
        "hero_sourced_calls": sum(1 for row in collect(hero) if row["sourced"]),
        "minion_attack_source_line": "self.target.take_damage(self.damage, self.team)"
        in textwrap.dedent(ast.get_source_segment(text, minion) or ""),
    }


def source_fixture():
    stats = _live_stats()
    payload = stats["orc_damage"]
    rows = (
        {
            "name": "orc_melee_on_tower",
            "victim_kind": "tower",
            "expect_divergence": True,
            "expected": _tower_ladder(payload, None, stats["tower_armor"]),
            "native_old": _tower_ladder(payload, "physical", stats["tower_armor"]),
        },
        {
            "name": "orc_melee_on_troll",
            "victim_kind": "minion",
            "expect_divergence": True,
            "expected": _minion_ladder(payload, None, stats),
            "native_old": _minion_ladder(payload, "physical", stats),
        },
        {
            "name": "orc_melee_on_armoured_hero",
            "victim_kind": "hero",
            "expect_divergence": False,
            "expected": _hero_ladder(payload, None, stats["hero_armor"]),
            "native_old": _hero_ladder(payload, "physical", stats["hero_armor"]),
        },
    )
    for row in rows:
        row["payload"] = payload
    return {
        "source": (
            "`_entity.py::Minion.update` melee attack (`self.target.take_damage(self.damage,"
            " self.team)`) run through the real `Tower.take_damage`, `Minion.take_damage` and"
            " `Hero.take_damage`"
        ),
        "native_old_model": (
            "pre-9x native arm: `apply_hit` -> `_deliver_hit(attacker.id, attacker.team, target,"
            " attacker.definition.damage, \"physical\", attacker.position)`"
        ),
        "callsite": "godot_rebuild/scripts/combat/minion_battle.gd::apply_hit",
        "hero_contrast": "`_entity.py::Hero` melee branch sends `source=self` plus `school=self.dmg_school`",
        "armor_item": ARMOR_ITEM,
        "live_stats": stats,
        "shape": _source_call_shape(),
        "cases": list(rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if not (args.self_test or args.write):
        parser.error("one of the arguments --self-test --write is required")
    fixture = source_fixture()
    if args.write:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
        print("wrote %s (%d cases)" % (FIXTURE.name, len(fixture["cases"])))
        return 0
    committed = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if committed != fixture:
        print("FAIL: fixture drift vs %s" % FIXTURE)
        return 1
    print("minion melee school oracle self-test passed: %d cases" % len(fixture["cases"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
