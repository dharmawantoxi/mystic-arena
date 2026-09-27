"""Read-only source oracle for the AI item port (hero_items.py).

hero_items.py imports pygame at module import time, so the module is never
imported: the module-level constants the AI needs (``ITEM_CATALOG`` plus every
constant it references, ``ITEM_FLAT_COST``, ``MAX_ITEM_SLOTS``,
``MAGIC_ROLE_KEYWORDS``) are lifted from the AST and exec'd in a bare
namespace. ``ast.literal_eval`` cannot be used because every catalog entry
stores the ``CATEGORY_*`` name, not its string value.

This is test infrastructure, not a runtime converter. Python stays read-only.
"""
import ast
import contextlib
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "hero_items.py"
DATA = ROOT / "godot_rebuild/data/ai/item_catalog.json"
FIXTURE = Path(__file__).parent / "fixtures/ai_items_source.json"

_NAMES = frozenset({
    "MAX_ITEM_SLOTS", "ITEM_FLAT_COST", "MAGIC_ROLE_KEYWORDS", "ITEM_CATALOG",
})
_FUNCTIONS = ("is_magic_hero", "suggest_item_for_hero")
_LEVEL_MULT = "_hero_level_mult"
# Real HeroItemInventory slot bookkeeping plus the stat chain `_on_item_changed`
# reaches, so the fixture can show exactly what the rebuild does NOT port yet.
_INVENTORY_METHODS = (
    "__init__", "count", "has", "used_slots", "add", "remove", "_on_item_changed",
    "get_max_hp", "get_bonus_hp", "get_hp_pct", "get_heal_amp", "_sum_stat",
    "clear_on_death",
)

# (hero spec, ops). Every op result plus the slot list is recorded; the source
# hero max_hp/hp/heal-amp calls are recorded too, as documented divergence.
INVENTORY_CASES = [
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3, "hp": 500,
      "max_hp": 700}, [
        ["add", "leviathan_heart"], ["add", "cleave_axe"], ["add", "holy_rapier"],
        ["count", "holy_rapier"], ["has", "cleave_axe"], ["used_slots"],
        ["remove", 0], ["add", "leviathan_heart"], ["count", "leviathan_heart"],
        ["clear_on_death"], ["has", "holy_rapier"], ["used_slots"],
    ]),
    ({"role": "Marksman", "range": 130, "base_hp": 540, "level": 5, "hp": 540,
      "max_hp": 800}, [
        ["add", "cleave_axe"], ["add", "dead_edge"], ["remove", -1], ["remove", 6],
        ["remove", 1], ["remove", 0], ["remove", 0], ["used_slots"],
    ]),
    ({"role": "Warrior", "range": 70, "base_hp": 700, "level": 1, "hp": 700,
      "max_hp": 700}, [
        ["add", "astral_codex"], ["add", "vital_stone"], ["add", "steel_aegis"],
        ["add", "not_an_item"], ["add", ""], ["used_slots"],
    ]),
    ({"role": "Mage", "range": 130, "base_hp": 480, "level": 7, "hp": 480,
      "max_hp": 900}, [
        ["add", "astral_codex"], ["add", "vital_stone"], ["add", "abyss_breaker"],
        ["add", "leviathan_heart"], ["used_slots"],
    ]),
    ({"role": "Fighter", "range": 80, "base_hp": 650, "level": 4, "hp": 650,
      "max_hp": 750}, [
        ["add", "searbrand"], ["add", "scarlet_bulwark"], ["add", "everfrost_guard"],
        ["add", "steel_aegis"], ["add", "solar_brand"], ["add", "moon_shard"],
        ["add", "demon_maw"], ["used_slots"],
    ]),
    ({"role": "Ranger", "range": 0, "base_hp": 520, "level": 2, "hp": 520,
      "max_hp": 560}, [
        ["add", "cleave_axe"], ["used_slots"], ["clear_on_death"],
    ]),
    ({"role": "Mage", "range": 130, "base_hp": 480, "level": 6, "hp": 480,
      "max_hp": 880}, [
        ["add", "holy_rapier"], ["add", "runic_gavel"], ["clear_on_death"],
        ["used_slots"], ["has", "runic_gavel"],
    ]),
]

# (role, attack range, owned slots). Ranges 70/80 are melee, 81+ is ranged,
# and 0 exercises the source `or 100` fallback.
SUGGESTION_CASES = [
    ("Bruiser", 70, []),
    ("Fighter", 70, []),
    ("Tank", 70, []),
    ("Assassin", 70, []),
    ("Marksman", 130, []),
    ("Assassin", 130, []),
    ("Mage", 130, []),
    ("Mage/Trickster", 130, []),
    ("Sorcerer", 130, []),
    ("Boss/Magic", 130, []),
    ("Anti-Mage", 70, []),
    ("Anti-Mage", 130, ["astral_codex"]),
    ("Ranger", 130, []),
    ("Warrior", 70, []),
    ("", 130, []),
    ("", 70, []),
    ("Warden", 80, []),
    ("Warden", 81, []),
    ("Warden", 0, []),
    ("Bruiser", 70, ["cleave_axe", "leviathan_heart"]),
    ("Bruiser", 70, ["cleave_axe", "leviathan_heart", "scarlet_bulwark"]),
    ("Marksman", 130, ["dead_edge", "basilisk_breath", "gale_pike"]),
    ("Mage", 130, ["astral_codex", "fulgur_scepter", "sage_scepter"]),
    ("Anti-Mage", 130, ["astral_codex", "fulgur_scepter", "sage_scepter"]),
    ("Warrior", 70, ["steel_aegis", "searbrand", "sundering_cudgel"]),
    ("Warrior", 70, ["cleave_axe", "steel_aegis"]),
]

# Every role keyword of MAGIC_ROLE_KEYWORDS plus the documented exceptions.
MAGIC_ROLE_CASES = [
    "Mage", "Mage/Trickster", "Sorceress", "Caster", "Warlock", "Witch",
    "Sage", "Prophet", "High Priestess", "Pyromancer", "Necromancer",
    "Shaman", "Summoner", "Chorister", "Farseer", "Starweaver", "Hexblade",
    "Eldritch Horror", "Boss/Magic", "Anti-Mage", "anti-mage", "Assassin",
    "Bruiser", "Marksman", "Fighter", "Tank", "", "  ", "Paladin",
]
POOL_CASES = sorted({(role, rng) for role, rng, _ in SUGGESTION_CASES} | {
    ("Tank", 130), ("Anti-Mage", 70), ("Sorcerer", 70), ("", 0),
})


def _assignments():
    nodes = []
    for node in ast.parse(SOURCE.read_text(encoding="utf-8")).body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        if isinstance(node.targets[0], ast.Name):
            nodes.append(node)
    return nodes


def source_namespace(with_functions=False, with_inventory=False):
    """Exec only the constant assignments ITEM_CATALOG needs, in source order."""
    nodes = _assignments()
    by_name = {node.targets[0].id: node for node in nodes}
    assert _NAMES <= by_name.keys(), "source constants missing"
    needed = set(_NAMES)
    for ref in ast.walk(by_name["ITEM_CATALOG"].value):
        if isinstance(ref, ast.Name) and ref.id in by_name:
            needed.add(ref.id)
    kept = [node for node in nodes if node.targets[0].id in needed]
    wanted = set()
    if with_functions:
        wanted |= set(_FUNCTIONS)
    if with_inventory:
        wanted.add(_LEVEL_MULT)
    if wanted:
        found = [node for node in ast.parse(SOURCE.read_text(encoding="utf-8")).body
                 if isinstance(node, ast.FunctionDef) and node.name in wanted]
        assert {node.name for node in found} == wanted, "source functions missing"
        kept.extend(found)
    code = ast.fix_missing_locations(ast.Module(body=kept, type_ignores=[]))
    env = {}
    exec(compile(code, "<source hero_items constants>", "exec"), env)
    assert env["ITEM_FLAT_COST"] and env["MAX_ITEM_SLOTS"], "source constants empty"
    return env


def catalog(env=None):
    """Shippable metadata: only the fields the AI adapter reads."""
    env = source_namespace() if env is None else env
    items = {}
    for item_id, data in env["ITEM_CATALOG"].items():
        items[item_id] = {
            "name": data["name"],
            "category": data["category"],
            "cost": data["cost"],
            "melee_only": bool(data.get("melee_only", False)),
            "magic_only": bool(data.get("magic_only", False)),
            "drops_on_death": bool(data.get("drops_on_death", False)),
        }
    return {
        "max_slots": env["MAX_ITEM_SLOTS"],
        "flat_cost": env["ITEM_FLAT_COST"],
        # category id -> source CATEGORY_* constant name, so the metadata can
        # be validated by category id and still points at the source symbol.
        "categories": {env[name]: name for name in sorted(env)
                       if name.startswith("CATEGORY_")},
        "items": items,
    }


def magic_roles(env):
    """is_magic_hero for every source role keyword and its exceptions."""
    return [{"role": role, "is_magic": env["is_magic_hero"](SimpleNamespace(role=role))}
            for role in MAGIC_ROLE_CASES]


def suggestions(env):
    """suggest_item_for_hero for a fixed (role, range, owned) grid."""
    rows = []
    for role, attack_range, owned in SUGGESTION_CASES:
        hero = SimpleNamespace(role=role, range=attack_range)
        rows.append({
            "role": role, "range": attack_range, "owned": list(owned),
            "is_magic": env["is_magic_hero"](hero),
            "suggestion": env["suggest_item_for_hero"](hero, set(owned)),
        })
    return rows


def pools(env):
    """Full purchase sequence per role/range: the pool order the source walks."""
    rows = []
    for role, attack_range in POOL_CASES:
        hero = SimpleNamespace(role=role, range=attack_range)
        owned = []
        while True:
            item_id = env["suggest_item_for_hero"](hero, set(owned))
            if item_id is None:
                break
            owned.append(item_id)
        rows.append({"role": role, "range": attack_range, "order": owned,
                     "is_magic": env["is_magic_hero"](hero)})
    return rows


@contextlib.contextmanager
def _core_module():
    """`_hero_level_mult` imports HERO_LEVELS from _core, which needs pygame."""
    from structure_source_oracle import namespace as core_namespace
    stub = types.ModuleType("_core")
    stub.HERO_LEVELS = core_namespace()["HERO_LEVELS"]
    saved = sys.modules.get("_core")
    sys.modules["_core"] = stub
    try:
        yield stub
    finally:
        if saved is None:
            sys.modules.pop("_core", None)
        else:
            sys.modules["_core"] = saved


def inventory_type(env):
    """Exec the real slot/stat methods of HeroItemInventory, unchanged."""
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    original = next(n for n in tree.body
                    if isinstance(n, ast.ClassDef) and n.name == "HeroItemInventory")
    selected = [n for n in original.body
                if isinstance(n, ast.FunctionDef) and n.name in _INVENTORY_METHODS]
    assert {n.name for n in selected} == set(_INVENTORY_METHODS), "inventory methods missing"
    node = ast.ClassDef(name="HeroItemInventory", bases=[], keywords=[],
                        decorator_list=[], body=selected)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                 "<source HeroItemInventory slots>", "exec"), env)
    return env["HeroItemInventory"]


def inventory(env):
    """Real add/remove/count/has/clear_on_death runs, per op snapshots."""
    rows = []
    with _core_module():
        inv_type = inventory_type(env)
        for spec, ops in INVENTORY_CASES:
            heal_calls = []
            hero = SimpleNamespace(role=spec["role"], range=spec["range"],
                                   base_hp=spec["base_hp"], level=spec["level"],
                                   hp=spec["hp"], max_hp=spec["max_hp"])
            hero.apply_heal_amp = lambda amount, duration: heal_calls.append(
                [amount, duration])
            inv = inv_type(hero)
            log = []
            for op in ops:
                if op[0] == "clear_on_death":
                    result = inv.clear_on_death()
                elif op[0] == "used_slots":
                    result = inv.used_slots()
                else:
                    result = getattr(inv, op[0])(op[1])
                log.append({
                    "op": op,
                    "result": result,
                    "slots": list(inv.slots),
                    "used": inv.used_slots(),
                    # Source-only: `_on_item_changed` recomputes max HP and
                    # re-applies heal amp. The rebuild does not port this yet.
                    "max_hp": hero.max_hp,
                    "hp": hero.hp,
                    "heal_calls": [list(call) for call in heal_calls],
                })
            rows.append({"hero": spec, "start": [spec["max_hp"], spec["hp"]], "log": log})
    return rows


# (heroes, gold, reserve). Hero roles/ranges are the six playable starter
# definitions so the native suite can rebuild the exact same candidates:
# kaizen Assassin/70, thorne Bruiser/70, grimjaw Fighter/70, sylara
# Marksman/130, vex Mage/130, zephyr Mage/Trickster/130.
BUY_CASES = [
    ({"heroes": [("Assassin", 70, 0, 1, True, []), ("Bruiser", 70, 0, 1, True, []),
                 ("Marksman", 130, 0, 1, True, [])], "gold": 13500, "reserve": 0}),
    ({"heroes": [("Assassin", 70, 1, 2, True, []), ("Bruiser", 70, 5, 2, True, []),
                 ("Marksman", 130, 3, 2, True, [])], "gold": 13500, "reserve": 0}),
    ({"heroes": [("Assassin", 70, 4, 1, True, []), ("Bruiser", 70, 4, 3, True, []),
                 ("Fighter", 70, 4, 2, True, []), ("Mage", 130, 4, 4, True, [])],
      "gold": 13500, "reserve": 0}),
    # Zephyr suggests Astral Codex (6000): unaffordable, so the next candidate
    # with a 4500 suggestion pays instead.
    ({"heroes": [("Mage/Trickster", 130, 9, 5, True, []), ("Assassin", 70, 0, 1, True, [])],
      "gold": 5000, "reserve": 0}),
    ({"heroes": [("Bruiser", 70, 9, 5, False, []), ("Assassin", 70, 0, 1, True, [])],
      "gold": 9000, "reserve": 0}),
    ({"heroes": [("Assassin", 70, 9, 5, True,
                  ["cleave_axe", "dead_edge", "basilisk_breath", "gale_pike",
                   "frostbound_eye", "sundering_cudgel"]),
                 ("Bruiser", 70, 0, 1, True, [])], "gold": 9000, "reserve": 0}),
    # 4800 pays a 4500 item only when nothing is reserved for the draft.
    ({"heroes": [("Assassin", 70, 0, 1, True, ["cleave_axe", "dead_edge"]),
                 ("Bruiser", 70, 0, 1, True, [])], "gold": 4800, "reserve": 400}),
    ({"heroes": [("Assassin", 70, 0, 1, True, ["cleave_axe", "dead_edge"]),
                 ("Bruiser", 70, 0, 1, True, [])], "gold": 4800, "reserve": 0}),
    ({"heroes": [("Mage", 130, 2, 1, True, []), ("Mage/Trickster", 130, 2, 1, True, []),
                 ("Fighter", 70, 1, 6, True, [])], "gold": 10500, "reserve": 0}),
]


@contextlib.contextmanager
def _hero_items_module(env):
    """`_try_buy_item` imports hero_items, which needs pygame: serve the exec'd
    source objects through a stub module instead."""
    stub = types.ModuleType("hero_items")
    stub.ITEM_CATALOG = env["ITEM_CATALOG"]
    stub.MAX_ITEM_SLOTS = env["MAX_ITEM_SLOTS"]
    stub.suggest_item_for_hero = env["suggest_item_for_hero"]
    # Superset of the kaizen oracle stub, which only provides a fake inventory.
    stub.HeroItemInventory = inventory_type(env)
    saved = sys.modules.get("hero_items")
    sys.modules["hero_items"] = stub
    try:
        yield stub
    finally:
        if saved is None:
            sys.modules.pop("hero_items", None)
        else:
            sys.modules["hero_items"] = saved


def purchases(env):
    """Run the real AIPlayer._try_buy_item until it refuses to buy."""
    from ai_upgrade_source_oracle import compile_subset
    from kaizen_source_oracle import build_hero_env

    # build_hero_env installs its own hero_items stub, so run it first and let
    # the context manager replace that stub with the exec'd source objects.
    ai_env = build_hero_env()
    rows = []
    with _core_module(), _hero_items_module(env):
        tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
        ai_type = compile_subset(tree, "AIPlayer",
                                 ("__init__", "_ai_reserve", "_try_buy_item"), ai_env)
        inv_type = inventory_type(env)
        for case in BUY_CASES:
            heroes = []
            for tag, spec in enumerate(case["heroes"]):
                role, attack_range, kills, level, alive, owned = spec
                hero = SimpleNamespace(role=role, range=attack_range, kills=kills,
                                       level=level, alive=alive, base_hp=600,
                                       hp=600, max_hp=600, _tag=tag)
                hero.apply_heal_amp = lambda amount, duration: None
                hero.items = inv_type(hero)
                for item_id in owned:
                    assert hero.items.add(item_id), f"pre-owned {item_id} refused"
                heroes.append(hero)
            player = ai_type()
            player.gold = case["gold"]
            player.heroes = heroes
            player._hero_purchase_target = "kaizen" if case["reserve"] else None
            player._hero_purchase_target_cost = case["reserve"]
            start = player.gold
            calls = []
            for _ in range(len(heroes) * 7):
                before = [hero.items.used_slots() for hero in heroes]
                success = player._try_buy_item()
                entry = {"success": success, "gold": player.gold, "tag": -1, "item": None}
                if success:
                    for hero in heroes:
                        if hero.items.used_slots() > before[hero._tag]:
                            entry["tag"] = hero._tag
                            entry["item"] = [sid for sid in hero.items.slots
                                             if sid is not None][-1]
                calls.append(entry)
                if not success:
                    break
            rows.append({
                "heroes": [{"role": s[0], "range": s[1], "kills": s[2], "level": s[3],
                            "alive": s[4], "owned": list(s[5])} for s in case["heroes"]],
                "gold": case["gold"], "reserve": case["reserve"],
                "calls": calls, "spent": start - player.gold,
                "slots": [list(hero.items.slots) for hero in heroes],
            })
    return rows


def source_fixture():
    env = source_namespace(with_functions=True, with_inventory=True)
    # Normalise through JSON so tuples/floats compare like the stored fixture.
    return json.loads(json.dumps({
        "catalog": catalog(env),
        "magic_roles": magic_roles(env),
        "suggestions": suggestions(env),
        "pools": pools(env),
        "inventory": inventory(env),
        "purchases": purchases(env),
    }))


if __name__ == "__main__":
    env = source_namespace()
    if "--write-data" in sys.argv:
        DATA.write_text(json.dumps(catalog(env), indent=2) + "\n", encoding="utf-8")
    if "--write" in sys.argv:
        FIXTURE.write_text(json.dumps(source_fixture(), indent=2) + "\n",
                           encoding="utf-8")
    else:
        assert source_fixture() == json.loads(FIXTURE.read_text(encoding="utf-8")), \
            "AI item catalog source drift"
        assert catalog(env) == json.loads(DATA.read_text(encoding="utf-8")), \
            "data/ai/item_catalog.json drifted from ITEM_CATALOG"
    entries = env["ITEM_CATALOG"]
    print("PASS: AI item catalog — %d items, flat cost %d, %d slots, %d melee-only, "
          "%d magic-only, %d drops on death" % (
              len(entries), env["ITEM_FLAT_COST"], env["MAX_ITEM_SLOTS"],
              sum(1 for d in entries.values() if d.get("melee_only")),
              sum(1 for d in entries.values() if d.get("magic_only")),
              sum(1 for d in entries.values() if d.get("drops_on_death"))))
