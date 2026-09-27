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

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "hero_items.py"
DATA = ROOT / "godot_rebuild/data/ai/item_catalog.json"
FIXTURE = Path(__file__).parent / "fixtures/ai_items_source.json"

_NAMES = frozenset({
    "MAX_ITEM_SLOTS", "ITEM_FLAT_COST", "MAGIC_ROLE_KEYWORDS", "ITEM_CATALOG",
})


def _assignments():
    nodes = []
    for node in ast.parse(SOURCE.read_text(encoding="utf-8")).body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        if isinstance(node.targets[0], ast.Name):
            nodes.append(node)
    return nodes


def source_namespace():
    """Exec only the constant assignments ITEM_CATALOG needs, in source order."""
    nodes = _assignments()
    by_name = {node.targets[0].id: node for node in nodes}
    assert _NAMES <= by_name.keys(), "source constants missing"
    needed = set(_NAMES)
    for ref in ast.walk(by_name["ITEM_CATALOG"].value):
        if isinstance(ref, ast.Name) and ref.id in by_name:
            needed.add(ref.id)
    kept = [node for node in nodes if node.targets[0].id in needed]
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


def source_fixture():
    env = source_namespace()
    # Normalise through JSON so tuples/floats compare like the stored fixture.
    return json.loads(json.dumps({"catalog": catalog(env)}))


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
