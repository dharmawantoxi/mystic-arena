"""9o: source oracle for item-arm damage onto TOWERS and CASTLES.

Every on-hit item arm that lands bonus damage calls the victim's `take_damage`
with no `source=`:

    target.take_damage(bash["damage"], h.team)             # hero_items.py:2542
    target.take_damage(b[0], h.team, "magic")              # hero_items.py:2589

so a structure victim runs `Tower.take_damage` (`_entity.py:1053`) or
`Castle.take_damage` (`:1758`) with `source=None` and `school=None`:

* `resolve_damage_school(damage_type, None, None, target_is_hero=False)`
  returns `None`, so the tower armour branch never runs and the whole bonus
  lands raw (the castle never has one);
* `credit_hero_damage(None, amount)` records nothing, so the ATTACK DAMAGE
  DEALER picker never sees the arm's damage;
* the castle still absorbs through its shield and applies the 0.88 reduction
  while `shield_active`.

The native bus delivered these arms as
`effects.deal_damage*(target_id, hero_team, amount, school)` with the dealing
hero as `_deliver_hit` source, so a tower cut the bonus with its armour and
the hero was credited. Each row therefore carries `expected` (source shape,
executed through the real inventory arm and the real structure ladder) and
`native_old` (the pre-9o native shape).

`--self-test` verifies the executed ladder against the committed fixture;
`--write` is the only fixture writer.
"""
import argparse
import ast
import json
import sys
import textwrap
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from boss_item_cleave_chain_source_oracle import _DummyOwner, _build_runtime  # noqa: E402
from hero_skill_sourceless_source_oracle import _StubTower, _tower_take_damage  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures/item_structure_arm_source.json"
ENTITY = ROOT / "_entity.py"
BLUE = "blue"
RED = "red"
MAIN_TARGET_ID = 10
BASIC_DAMAGE = 50
BASH_ITEM = "abyss_breaker"
PIERCE_ITEM = "sundering_cudgel"
# Live structure stats: archer_level_1 armour, nexus_level_1 shield.
TOWER_ARMOR = 3.0
CASTLE_SHIELD_MAX = 4000.0
CASTLE_SHIELD = 20.0
CASTLE_REDUCTION = 0.88


def _core_constant(name):
    """Read a module-level constant from `_core.py` without importing pygame."""
    tree = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            getattr(target, "id", None) == name for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("missing _core constant " + name)


def _castle_take_damage():
    """Compile the real `Castle.take_damage` into a plain callable."""

    text = ENTITY.read_text(encoding="utf-8")
    tree = ast.parse(text)
    holder = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Castle")
    method = next(
        node for node in holder.body if isinstance(node, ast.FunctionDef) and node.name == "take_damage"
    )
    helper = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "resolve_damage_school"
    )
    credits = []
    namespace = {
        "credit_hero_damage": lambda source, amount: credits.append([source is not None, int(amount)]),
        "CASTLE_SHIELD_DAMAGE_REDUCTION": _core_constant("CASTLE_SHIELD_DAMAGE_REDUCTION"),
        "SoundManager": type("SoundManager", (), {"play": lambda self, *_a, **_k: None}),
        "_ACTIVE_HERO": [None],
        "_credits": credits,
    }
    exec(compile(textwrap.dedent(ast.get_source_segment(text, helper)), "<entity>", "exec"), namespace)
    exec(compile(textwrap.dedent(ast.get_source_segment(text, method)), "<entity>", "exec"), namespace)
    return namespace["take_damage"], namespace


class _StubCastle:
    def __init__(self, *, shield=0.0, shield_active=True, hp=4000.0):
        self.armor = 0.0
        self.magic_resist = 0.0
        self.hp = float(hp)
        self.max_hp = 4000.0
        self.shield_max = CASTLE_SHIELD_MAX
        self.shield = float(shield)
        self.shield_active = bool(shield_active)
        self.shield_no_damage_timer = 0
        self.shield_regen_flash = 0
        self.alive = True
        self.team = RED
        self.x = 0.0
        self.y = 0.0

    def apply_debuff(self, *_args, **_kwargs):
        return None

    def apply_stun(self, *_args, **_kwargs):
        return None


def _victim(kind, scenario):
    """Structure stub wired to the real ladder; returns (victim, namespace)."""
    if kind == "tower":
        take_damage, namespace = _tower_take_damage()
        tower = _StubTower(TOWER_ARMOR)
        tower.apply_debuff = lambda *_a, **_k: None
        tower.apply_stun = lambda *_a, **_k: None
        tower.team = RED
        tower.id = 500
        tower.alive = True
        tower.take_damage = types.MethodType(take_damage, tower)
        return tower, namespace
    take_damage, namespace = _castle_take_damage()
    castle = _StubCastle(
        shield=scenario.get("castle_shield", 0.0),
        shield_active=bool(scenario.get("castle_shield_active", True)),
    )
    castle.id = 500
    castle.take_damage = types.MethodType(take_damage, castle)
    return castle, namespace


SCENARIOS = (
    {
        "name": "bash_on_tower_sourceless",
        "kind": "tower",
        "item": BASH_ITEM,
        "arm": "bash",
        "native_damage_type": "normal",
        "native_school": "physical",
    },
    {
        "name": "pierce_bash_on_tower_sourceless",
        "kind": "tower",
        "item": PIERCE_ITEM,
        "arm": "bash",
        "native_damage_type": "magic",
        "native_school": "magic",
    },
    {
        "name": "bash_on_castle_shielded",
        "kind": "castle",
        "item": BASH_ITEM,
        "arm": "bash",
        "native_damage_type": "normal",
        "native_school": "physical",
        "castle_shield": CASTLE_SHIELD,
        "castle_shield_active": True,
    },
    {
        "name": "bash_on_castle_shield_down",
        "kind": "castle",
        "item": BASH_ITEM,
        "arm": "bash",
        "native_damage_type": "normal",
        "native_school": "physical",
        "castle_shield": 0.0,
        "castle_shield_active": False,
    },
)


def _prepare_owner(inventory_class, target):
    owner = _DummyOwner(target)
    owner.id = 7
    owner.team = BLUE
    owner.kills = 0
    owner.name = "Kaizen"
    owner.hero_type = "kaizen"
    owner.skills = ["q", "w", "e", "r"]
    inventory = inventory_class(owner)
    owner.items = inventory
    return owner, inventory


def _run_case(catalog, inventory_class, scenario, native_old):
    victim, namespace = _victim(str(scenario["kind"]), scenario)
    owner, inventory = _prepare_owner(inventory_class, victim)
    assert inventory.add(str(scenario["item"])), "cannot equip " + str(scenario["item"])
    arm_damage = int(catalog[str(scenario["item"])][str(scenario["arm"])]["damage"])

    if native_old:
        real_take_damage = victim.take_damage

        def native_arm(damage, from_team=None, damage_type="normal", source=None, school=None):
            # Pre-9o native bus: the arm carried the dealing hero as source and
            # the declared school.
            return real_take_damage(
                damage,
                from_team,
                damage_type,
                source=owner,
                school=str(scenario["native_school"]),
            )

        victim.take_damage = native_arm
    namespace["_credits"].clear()

    hp_before = float(victim.hp)
    inventory.on_basic_attack_hit(victim, BASIC_DAMAGE, [victim, owner])
    credits = list(namespace["_credits"])
    return {
        "arm_damage": arm_damage,
        "hp_loss": int(round(hp_before - float(victim.hp))),
        "credits": credits,
        "credited_total": _credited_total(credits),
    }


def _credited_total(credits) -> int:
    """`credit_hero_damage` skips the credit when `source is None`."""
    return sum(row[1] for row in credits if row[0])


def source_fixture():
    catalog, inventory_class, _unused_boss = _build_runtime()
    cases = []
    for scenario in SCENARIOS:
        expected = _run_case(catalog, inventory_class, scenario, native_old=False)
        native_old = _run_case(catalog, inventory_class, scenario, native_old=True)
        cases.append(
            {
                "name": scenario["name"],
                "structure_kind": scenario["kind"],
                "item": scenario["item"],
                "castle_shield": float(scenario.get("castle_shield", 0.0)),
                "castle_shield_active": bool(scenario.get("castle_shield_active", True)),
                "tower_armor": TOWER_ARMOR if scenario["kind"] == "tower" else 0.0,
                "expected": expected,
                "native_old": native_old,
            }
        )
    return {
        "source": (
            "_entity.py::Tower.take_damage :1053 / Castle.take_damage :1758 via the"
            " un-sourced item arms of hero_items.py"
        ),
        "native_old_model": (
            "pre-9o native bus: `deal_damage(target_id, hero_team, amount, school)`"
            " kept the dealing hero as source and the declared school"
        ),
        "arm_sources": {
            "bash": "hero_items.py:2542 abyss_breaker",
            "pierce_bash": "hero_items.py:2589 sundering_cudgel",
        },
        "live_stats": {
            "tower_armor": TOWER_ARMOR,
            "castle_shield_max": CASTLE_SHIELD_MAX,
            "castle_reduction": CASTLE_REDUCTION,
        },
        "cases": cases,
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
    print("item structure arm oracle self-test passed: %d cases" % len(fixture["cases"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
