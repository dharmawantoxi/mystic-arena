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
import json
import sys
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


def source_namespace(with_functions=False):
    """Exec only the constant assignments ITEM_CATALOG needs, in source order."""
    nodes = _assignments()
    by_name = {node.targets[0].id: node for node in nodes}
    assert _NAMES <= by_name.keys(), "source constants missing"
    needed = set(_NAMES)
    for ref in ast.walk(by_name["ITEM_CATALOG"].value):
        if isinstance(ref, ast.Name) and ref.id in by_name:
            needed.add(ref.id)
    kept = [node for node in nodes if node.targets[0].id in needed]
    if with_functions:
        found = [node for node in ast.parse(SOURCE.read_text(encoding="utf-8")).body
                 if isinstance(node, ast.FunctionDef) and node.name in _FUNCTIONS]
        assert {node.name for node in found} == set(_FUNCTIONS), "source functions missing"
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
        "categories": {name: env[name] for name in sorted(env)
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


def source_fixture():
    env = source_namespace(with_functions=True)
    # Normalise through JSON so tuples/floats compare like the stored fixture.
    return json.loads(json.dumps({
        "catalog": catalog(env),
        "magic_roles": magic_roles(env),
        "suggestions": suggestions(env),
        "pools": pools(env),
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
