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
    "get_max_hp", "get_bonus_hp", "get_bonus_damage", "get_hp_pct", "get_armor",
    "get_hp_regen", "get_attack_speed_mult", "get_lifesteal_pct", "get_crit",
    "get_cleave", "get_cooldown_reduction", "get_spell_vamp", "get_skill_amp",
    "get_evasion", "get_move_speed_pct", "get_heal_amp", "get_slow_resist",
    "get_range_bonus", "has_true_strike", "get_reflect_pct", "get_gale_as_bonus",
    "consume_empower_strike", "get_block", "get_armor_shred", "get_on_attack_chain",
    "get_bash", "is_veiled", "is_guarding", "get_rend_crit", "_sum_stat",
    "clear_on_death", "update", "notify_damage_taken",
)

# Pure stat aggregation getters (no RNG). Timer-driven branches are recorded
# too, with every timer still at its __init__ value: the active/passive layer
# has to move them before those branches can fire.
STAT_GETTERS = (
    "get_bonus_damage", "get_bonus_hp", "get_hp_pct", "get_armor", "get_hp_regen",
    "get_max_hp", "get_attack_speed_mult", "get_lifesteal_pct", "get_crit",
    "get_cleave", "get_cooldown_reduction", "get_spell_vamp", "get_skill_amp",
    "get_evasion", "get_move_speed_pct", "get_heal_amp", "get_slow_resist",
    "get_range_bonus", "has_true_strike", "get_reflect_pct", "get_gale_as_bonus",
    "get_block", "get_armor_shred", "get_on_attack_chain", "get_bash",
    "is_veiled", "is_guarding", "get_rend_crit",
)

# (hero spec, loadout). Hero specs cover the melee gate, the ranged gate and
# the source heuristic fallback when `is_melee_hero` is absent.
STAT_CASES = [
    (("Bruiser", 70, True, 620, 5), []),
    (("Bruiser", 70, True, 620, 5), ["dead_edge"]),
    (("Bruiser", 70, True, 620, 5), ["cleave_axe"]),
    (("Bruiser", 70, True, 620, 5), ["demon_maw"]),
    (("Bruiser", 70, True, 620, 5), ["leviathan_heart", "octarine_core"]),
    (("Bruiser", 70, True, 620, 5), ["abyss_breaker"]),
    (("Bruiser", 70, True, 620, 5), ["runic_gavel"]),
    (("Bruiser", 70, True, 620, 5), ["sundering_cudgel"]),
    (("Bruiser", 70, True, 620, 5), ["razor_carapace"]),
    (("Bruiser", 70, True, 620, 5), ["gale_pike"]),
    (("Bruiser", 70, True, 620, 5), ["fenrir_chain"]),
    (("Bruiser", 70, True, 620, 5), ["frostbound_eye"]),
    (("Bruiser", 70, True, 620, 5), ["basilisk_breath"]),
    (("Bruiser", 70, True, 620, 5), ["corroder"]),
    (("Mage", 130, False, 480, 9), ["astral_codex"]),
    (("Mage", 130, False, 480, 9), ["spectral_charm"]),
    (("Bruiser", 70, True, 620, 5), ["scarlet_bulwark", "everfrost_guard",
                                     "steel_aegis", "tempest_vane", "monarch_wings"]),
    (("Bruiser", 70, True, 620, 5), ["thunder_coil", "sanguine_thorn", "moon_shard"]),
    (("Marksman", 130, False, 540, 7), ["dead_edge", "gale_pike", "monarch_wings"]),
    (("Marksman", 130, False, 540, 7), ["frostbound_eye", "basilisk_breath",
                                        "sundering_cudgel"]),
    (("Marksman", 130, False, 540, 7), ["scarlet_bulwark", "everfrost_guard",
                                        "steel_aegis", "tempest_vane", "moon_shard"]),
    (("Mage", 130, False, 480, 9), ["astral_codex", "fulgur_scepter", "sage_scepter",
                                    "hex_idol", "rift_veil", "vital_stone"]),
    (("Mage", 130, False, 480, 9), ["vine_rod", "spectral_charm", "runic_gavel",
                                    "searbrand", "solar_brand", "leviathan_heart"]),
    # No `is_melee_hero` flag: the source falls back to `range < 110`.
    (("Warden", 105, None, 600, 3), ["gale_pike", "dead_edge"]),
    (("Warden", 130, None, 600, 3), ["gale_pike", "dead_edge"]),
]

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
        entry = {
            "name": data["name"],
            "category": data["category"],
            "cost": data["cost"],
            "melee_only": bool(data.get("melee_only", False)),
            "magic_only": bool(data.get("magic_only", False)),
            "drops_on_death": bool(data.get("drops_on_death", False)),
            # Numeric stats the aggregation getters sum, plus the descriptor
            # blocks those getters read verbatim (passive/block/on_attack/
            # bash/active). Presentation keys (icon/color/glow/desc) stay out.
            "stats": dict(data.get("stats", {})),
        }
        for key in ("passive", "block", "on_attack", "bash", "active"):
            if key in data:
                entry[key] = data[key]
        items[item_id] = json.loads(json.dumps(entry))
    return json.loads(json.dumps({
        "max_slots": env["MAX_ITEM_SLOTS"],
        "flat_cost": env["ITEM_FLAT_COST"],
        # category id -> source CATEGORY_* constant name, so the metadata can
        # be validated by category id and still points at the source symbol.
        "categories": {env[name]: name for name in sorted(env)
                       if name.startswith("CATEGORY_")},
        "items": items,
    }))


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


def stats(env):
    """Real aggregation getters over fixed loadouts; timers stay at init."""
    rows = []
    with _core_module():
        inv_type = inventory_type(env)
        for spec, loadout in STAT_CASES:
            role, attack_range, is_melee_hero, base_hp, level = spec
            hero = SimpleNamespace(role=role, range=attack_range, base_hp=base_hp,
                                   level=level, hp=100, max_hp=100)
            hero.apply_heal_amp = lambda amount, duration: None
            if is_melee_hero is not None:
                hero.is_melee_hero = is_melee_hero
            inv = inv_type(hero)
            for item_id in loadout:
                assert inv.add(item_id), f"loadout refused {item_id}"
            values = {name: getattr(inv, name)() for name in STAT_GETTERS}
            values["empower_strike"] = inv.consume_empower_strike()
            values["empower_charge"] = inv.empower_charge
            rows.append({
                "hero": {"role": role, "range": attack_range,
                         "is_melee_hero": is_melee_hero, "base_hp": base_hp,
                         "level": level},
                "loadout": list(loadout),
                "slots": list(inv.slots),
                "values": values,
            })
    return rows


# (hero spec, ops). hp always starts full for the level, like spawn_hero.
STAT_APPLICATION_CASES = [
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 1}, [
        "add:leviathan_heart", "upgrade", "upgrade", "add:octarine_core",
        "remove:0", "upgrade"]),
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3}, [
        "add:abyss_breaker", "add:searbrand", "upgrade"]),
    ({"role": "Mage", "range": 130, "base_hp": 480, "level": 1}, [
        "add:vital_stone", "add:leviathan_heart", "add:abyss_breaker",
        "remove:2", "upgrade", "upgrade"]),
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 6}, [
        "remove:0", "add:holy_rapier", "clear_on_death", "upgrade"]),
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 1}, []),
]


# (hero spec, loadout). Death destroys Holy Rapier only, and the source never
# recalculates max HP in that branch.
DEATH_CASES = [
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 4},
     ["holy_rapier", "leviathan_heart", "dead_edge"]),
    ({"role": "Mage", "range": 130, "base_hp": 480, "level": 2},
     ["astral_codex", "holy_rapier"]),
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 1},
     ["leviathan_heart"]),
]


def deaths(env):
    rows = []
    with _core_module():
        inv_type = inventory_type(env)
        for spec, loadout in DEATH_CASES:
            hero = SimpleNamespace(role=spec["role"], range=spec["range"],
                                   base_hp=spec["base_hp"], level=spec["level"],
                                   hp=1000, max_hp=1000)
            hero.apply_heal_amp = lambda amount, duration: None
            inv = inv_type(hero)
            for item_id in loadout:
                assert inv.add(item_id), f"death loadout refused {item_id}"
            before = hero.max_hp
            dropped = inv.clear_on_death()
            rows.append({
                "hero": spec, "loadout": list(loadout), "dropped": dropped,
                "slots": list(inv.slots), "max_hp": hero.max_hp,
                "max_hp_before": before,
            })
    return rows


# (hero spec, loadout, preset timers, ticks). Loadouts stay away from the
# auto-trigger/damage half of update: only the timer state machine is ported.
TIMER_CASES = [
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3}, [],
     {"blood_frenzy_timer": 120, "guard_cd": 40, "static_tick": 7}, 3),
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3},
     ["runic_gavel"], {"empower_charge": 300, "thorn_timer": 5}, 10),
    ({"role": "Mage", "range": 130, "base_hp": 480, "level": 2},
     ["leviathan_heart", "dead_edge"],
     {"rend_timer": 4, "veil_cd": 2, "ghost_timer": 1, "gale_cd": 9}, 5),
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 1},
     ["runic_gavel", "holy_rapier"], {"empower_charge": 2}, 5),
]

# Loadouts that must never auto-trigger inside the ported timer half.
_TIMER_SAFE = frozenset({
    "runic_gavel", "leviathan_heart", "dead_edge", "holy_rapier",
})

# Auto-trigger cases for the update() effect half. Enemy stubs record the
# effects applied; each case runs a preset number of ticks and then records
# the timer state and the stub-recorded effects list.
class _EffectStub:
    def __init__(self, x, y, team, alive=True):
        self.x = x
        self.y = y
        self.team = team
        self.alive = alive
        self.target = None
        self.facing = 1
        self.effects = []
    def _record(self, kind, **kwargs):
        entry = {"kind": kind, "x": self.x, "y": self.y, "team": self.team}
        entry.update(kwargs)
        self.effects.append(entry)
    def take_damage(self, damage, team, school=None):
        self._record("damage", damage=int(damage), dmg_team=team, school=school)
    def apply_slow(self, amount, duration):
        self._record("slow", amount=float(amount), duration=int(duration))
    def apply_debuff(self, name, amount, duration, source_team=None):
        self._record("debuff", name=name, amount=float(amount), duration=int(duration),
                     source_team=source_team)
    def apply_stun(self, duration):
        self._record("stun", duration=int(duration))
    def apply_damage_amp(self, amount, duration):
        self._record("amp", amount=float(amount), duration=int(duration))
    def apply_armor_shred(self, amount, duration):
        self._record("shred", amount=float(amount), duration=int(duration))


def _make_hero(spec, hp_ratio=1.0, target=None, x=0, y=0, team="red", tag="hero"):
    max_hp = 1000
    hero = SimpleNamespace(role=spec["role"], range=spec["range"],
                           base_hp=spec["base_hp"], level=spec["level"],
                           max_hp=max_hp, hp=int(max_hp * hp_ratio),
                           alive=True, facing=1, x=x, y=y, team=team,
                           target=target, _tag=tag)
    hero.apply_heal_amp = lambda amount, duration: None
    return hero


# (hero spec, loadout, hp_ratio, enemy positions relative to hero at (100,100),
#  target_index (None = no target), ticks). Each enemy is at (100+dx, 100+dy).
AUTO_TRIGGER_CASES = [
    # Demon Maw: blood frenzy at HP < 35%.
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3},
     ["demon_maw"], 0.30, [], None, 3),
    # Scarlet Bulwark: guard at HP < threshold.
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3},
     ["scarlet_bulwark"], 0.20, [], None, 3),
    # Tempest Vane: veil at HP < threshold.
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3},
     ["tempest_vane"], 0.20, [], None, 3),
    # Fenrir Chain: 2+ enemies in trigger_radius.
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3},
     ["fenrir_chain"], 1.0, [(0, 30), (0, -30)], 0, 2),
    # Sanguine Thorn: rend when target is alive enemy.
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3},
     ["sanguine_thorn"], 1.0, [(0, 50)], 0, 2),
    # Abyss Breaker: overwhelm stun on target.
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3},
     ["abyss_breaker"], 1.0, [(0, 50)], 0, 2),
    # Razor Carapace: thornmail at HP < threshold.
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3},
     ["razor_carapace"], 0.20, [], None, 3),
    # Everfrost Guard: arctic blast on 2+ nearby.
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3},
     ["everfrost_guard"], 1.0, [(20, 0), (-20, 0)], 0, 2),
    # Gale Pike: dash away from target at low HP.
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3},
     ["gale_pike"], 0.20, [(0, 50)], 0, 2),
    # Searbrand: burn on 2+ nearby.
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3},
     ["searbrand"], 1.0, [(20, 0), (-20, 0)], 0, 2),
    # Astral Codex: nova + silence on 2+ nearby.
    ({"role": "Mage", "range": 130, "base_hp": 480, "level": 9},
     ["astral_codex"], 1.0, [(20, 0), (-20, 0)], 0, 2),
    # Fulgur Scepter: energy blast on target.
    ({"role": "Mage", "range": 130, "base_hp": 480, "level": 9},
     ["fulgur_scepter"], 1.0, [(0, 50)], 0, 2),
    # Hex Idol: hex stun+silence on target.
    ({"role": "Mage", "range": 130, "base_hp": 480, "level": 9},
     ["hex_idol"], 1.0, [(0, 50)], 0, 2),
    # Rift Veil: discord amp on 2+ nearby.
    ({"role": "Mage", "range": 130, "base_hp": 480, "level": 9},
     ["rift_veil"], 1.0, [(20, 0), (-20, 0)], 0, 2),
    # Vital Stone: heal at low HP.
    ({"role": "Mage", "range": 130, "base_hp": 480, "level": 9},
     ["vital_stone"], 0.20, [], None, 2),
    # Spectral Charm: ghost at low HP.
    ({"role": "Mage", "range": 130, "base_hp": 480, "level": 9},
     ["spectral_charm"], 0.20, [], None, 2),
    # Thunder Coil static charge via notify_damage_taken then zap over ticks.
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3},
     ["thunder_coil"], 1.0, [(0, 50), (0, 80)], 0, 12),
    # Leviathan Heart: out-of-combat regen.
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3},
     ["leviathan_heart"], 0.50, [], None, 10),
]

# (hero spec, loadout, hp_ratio, damage, source_enemy?, rng_seed_for_proc).
NOTIFY_DAMAGE_CASES = [
    # Leviathan reset combat timer.
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3},
     ["leviathan_heart"], 1.0, 100, True, 0),
    # Thunder Coil proc (seeded rng always procs).
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3},
     ["thunder_coil"], 1.0, 50, True, 0),
    # Thunder Coil no proc (high seed).
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3},
     ["thunder_coil"], 1.0, 50, True, 99),
    # Razor Carapace thornmail reflect (requires thorn_timer active).
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3},
     ["razor_carapace"], 0.20, 100, True, 0),
    # No enemy source: no reflect.
    ({"role": "Bruiser", "range": 70, "base_hp": 620, "level": 3},
     ["razor_carapace"], 0.20, 100, False, 0),
]


def timer_attrs():
    """Attribute names the source update() decrements, straight from the AST."""
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body
               if isinstance(n, ast.ClassDef) and n.name == "HeroItemInventory")
    update = next(n for n in cls.body
                  if isinstance(n, ast.FunctionDef) and n.name == "update")
    names = []
    for node in ast.walk(update):
        if isinstance(node, ast.Tuple):
            for elt in node.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    names.append(elt.value)
    assert "guard_timer" in names and "ghost_cd" in names, "timer list not found"
    return names


def timers(env):
    """Real HeroItemInventory.update timer state machine, dt ticks per case."""
    env.setdefault("_tick_miasma", lambda dt=1: None)
    env.setdefault("_fx_notify", lambda *args, **kwargs: None)
    env.setdefault("math", __import__("math"))
    env.setdefault("random", __import__("random"))
    rows = []
    with _core_module():
        inv_type = inventory_type(env)
        attrs = timer_attrs()
        for spec, loadout, preset, ticks in TIMER_CASES:
            assert set(loadout) <= _TIMER_SAFE, "unsafe loadout for the timer half"
            hero = SimpleNamespace(role=spec["role"], range=spec["range"],
                                   base_hp=spec["base_hp"], level=spec["level"],
                                   alive=True, hp=1000, max_hp=1000, x=0, y=0,
                                   team="red")
            hero.apply_heal_amp = lambda amount, duration: None
            inv = inv_type(hero)
            for item_id in loadout:
                assert inv.add(item_id), f"timer loadout refused {item_id}"
            for attr, value in preset.items():
                setattr(inv, attr, value)
            log = []
            for _ in range(ticks):
                inv.update(1, None)
                state = {attr: getattr(inv, attr, 0) for attr in attrs}
                for extra in ("blood_frenzy_timer", "blood_frenzy_cd",
                              "last_damage_timer", "empower_charge"):
                    state[extra] = getattr(inv, extra)
                state["rend_target"] = inv.rend_target
                log.append(state)
            rows.append({"hero": spec, "loadout": list(loadout),
                         "preset": preset, "ticks": ticks, "log": log})
    return rows


def hero_stat_type(env):
    """Real Hero HP recalc/level-up plus the _core heal-amp debuff setter."""
    entity_tree = ast.parse((ROOT / "_entity.py").read_text(encoding="utf-8"))
    hero_node = next(n for n in entity_tree.body
                     if isinstance(n, ast.ClassDef) and n.name == "Hero")
    names = {"_recalc_item_stats", "_apply_level_stats", "upgrade"}
    body = [n for n in hero_node.body
            if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in body} == names, "hero stat methods missing"
    core_tree = ast.parse((ROOT / "_core.py").read_text(encoding="utf-8"))
    for node in ast.walk(core_tree):
        if isinstance(node, ast.FunctionDef) and node.name == "apply_heal_amp":
            body.append(node)
    assert any(n.name == "apply_heal_amp" for n in body), "apply_heal_amp missing"
    cls = ast.ClassDef(name="SourceHeroStats", bases=[], keywords=[],
                       decorator_list=[], body=body)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])),
                 "<source hero item stats>", "exec"), env)
    return env["SourceHeroStats"]


def stat_application(env):
    """Equip/drop/level sequences with the real HP recalc and heal amp."""
    from structure_source_oracle import namespace as core_namespace

    core = core_namespace()
    env["HERO_LEVELS"] = core["HERO_LEVELS"]
    env["MAX_HERO_LEVEL"] = core["MAX_HERO_LEVEL"]
    rows = []
    with _core_module():
        inv_type = inventory_type(env)
        hero_type = hero_stat_type(env)
        for spec, ops in STAT_APPLICATION_CASES:
            start_max = int(spec["base_hp"] * core["HERO_LEVELS"][spec["level"]]["hp_mult"])
            # A real SourceHeroStats instance: _recalc_item_stats,
            # _apply_level_stats, upgrade and apply_heal_amp all run unchanged.
            hero = hero_type()
            for key, value in (("role", spec["role"]), ("range", spec["range"]),
                               ("base_hp", spec["base_hp"]), ("level", spec["level"]),
                               ("base_damage", 100), ("skill_damage_base", 50),
                               ("alive", True), ("hp", start_max), ("max_hp", start_max),
                               ("heal_amp_amount", 0.0), ("heal_amp_timer", 0)):
                setattr(hero, key, value)
            hero.items = inv_type(hero)
            log = []
            for op in ops:
                kind, _, arg = op.partition(":")
                if kind == "add":
                    assert hero.items.add(arg), f"equip refused {arg}"
                    hero.items._on_item_changed()
                elif kind == "remove":
                    hero.items.remove(int(arg))
                    hero.items._on_item_changed()
                elif kind == "clear_on_death":
                    hero.items.clear_on_death()
                    hero.items._on_item_changed()
                else:
                    assert hero.upgrade(), "upgrade refused"
                log.append({
                    "op": op, "max_hp": hero.max_hp, "hp": hero.hp,
                    "heal_amp_amount": hero.heal_amp_amount,
                    "heal_amp_timer": hero.heal_amp_timer,
                    "slots": list(hero.items.slots),
                })
            rows.append({"hero": spec, "start": [start_max, start_max], "log": log})
    return rows


def _install_effect_stubs(env):
    env["math"] = __import__("math")
    env["random"] = __import__("random")
    notifications = []
    def _fx_notify(unit, text, color=(255, 255, 255)):
        notifications.append({"unit_tag": getattr(unit, "_tag", id(unit)),
                              "text": str(text), "color": tuple(color)})
    chains = []
    def _fx_chain(source, targets, color):
        chains.append({"source_tag": getattr(source, "_tag", id(source)),
                       "target_tags": [getattr(t, "_tag", id(t)) for t in targets],
                       "color": tuple(color)})
    def _tick_miasma(dt=1):
        pass
    def _apply_stun_to(target, duration):
        fn = getattr(target, "apply_stun", None)
        if fn is not None:
            fn(duration)
        else:
            try:
                target.apply_slow(1.0, duration)
            except Exception:
                pass
    def _apply_silence_to(target, duration):
        try:
            target.apply_debuff("atk_slow", 1.0, duration)
            target.apply_debuff("skill_down", 1.0, duration)
        except Exception:
            pass
    def _apply_shred_to(target, amount, duration):
        fn = getattr(target, "apply_armor_shred", None)
        if fn is not None:
            fn(amount, duration)
    def _apply_amp_to(target, amount, duration):
        fn = getattr(target, "apply_damage_amp", None)
        if fn is not None:
            fn(amount, duration)
    env["_fx_notify"] = _fx_notify
    env["_fx_chain"] = _fx_chain
    env["_tick_miasma"] = _tick_miasma
    env["_apply_stun_to"] = _apply_stun_to
    env["_apply_silence_to"] = _apply_silence_to
    env["_apply_shred_to"] = _apply_shred_to
    env["_apply_amp_to"] = _apply_amp_to
    return notifications, chains


def auto_triggers(env):
    """Real update() auto-trigger half: enemies are _EffectStubs."""
    notifications, chains = _install_effect_stubs(env)
    rows = []
    with _core_module():
        inv_type = inventory_type(env)
        for spec, loadout, hp_ratio, deltas, target_idx, ticks in AUTO_TRIGGER_CASES:
            # Thunder Coil needs notify_damage_taken to start the static timer.
            notifications.clear()
            chains.clear()
            enemies = []
            for idx, (dx, dy) in enumerate(deltas):
                e = _EffectStub(100 + dx, 100 + dy, "blue", alive=True)
                e._tag = "e%d" % idx
                enemies.append(e)
            target = enemies[target_idx] if target_idx is not None else None
            hero = _make_hero(spec, hp_ratio=hp_ratio, target=target,
                              x=100, y=100)
            inv = inv_type(hero)
            for item_id in loadout:
                assert inv.add(item_id), f"auto-trigger loadout refused {item_id}"
            # Thunder Coil needs a seed proc. Always fire a damage notify first
            # so static_timer starts; later ticks should zap.
            if "thunder_coil" in loadout:
                source = enemies[0] if enemies else _EffectStub(200, 100, "blue")
                # Deterministic proc: rng.random() always below proc_chance.
                rng = __import__("random").Random(0)
                inv.notify_damage_taken(rng=rng, damage=50, source=source)
            hero_start_x = hero.x
            hero_start_y = hero.y
            log = []
            for _ in range(ticks):
                notifications.clear()
                chains.clear()
                for e in enemies:
                    e.effects.clear()
                inv.update(1, enemies)
                state = {attr: getattr(inv, attr, 0) for attr in timer_attrs()}
                for extra in ("blood_frenzy_timer", "blood_frenzy_cd",
                              "last_damage_timer", "empower_charge",
                              "static_timer", "static_tick", "static_cd",
                              "thorn_timer", "thorn_cd"):
                    state[extra] = getattr(inv, extra)
                state["hp"] = hero.hp
                state["x"] = hero.x
                state["y"] = hero.y
                log.append({
                    "state": state,
                    "effects": [list(e.effects) for e in enemies],
                    "notifications": [dict(n) for n in notifications],
                    "chains": [dict(c) for c in chains],
                })
            rows.append({
                "hero": spec, "loadout": list(loadout), "hp_ratio": hp_ratio,
                "enemy_deltas": [list(d) for d in deltas],
                "target_idx": target_idx, "ticks": ticks,
                "start_pos": [hero_start_x, hero_start_y],
                "log": log,
            })
    return rows


def notify_damage(env):
    """Real notify_damage_taken: combat timer reset, Static Charge, reflect."""
    notifications, chains = _install_effect_stubs(env)
    rows = []
    with _core_module():
        inv_type = inventory_type(env)
        for spec, loadout, hp_ratio, damage, has_source, seed in NOTIFY_DAMAGE_CASES:
            notifications.clear()
            chains.clear()
            # Razor Carapace needs thorn_timer active before notify_damage_taken
            # can reflect; low-HP update primes it.
            hero = _make_hero(spec, hp_ratio=hp_ratio, x=100, y=100)
            inv = inv_type(hero)
            for item_id in loadout:
                assert inv.add(item_id), f"notify loadout refused {item_id}"
            # Prime thorn timer if razors are present at low hp.
            if "razor_carapace" in loadout and hp_ratio < 0.5:
                inv.update(1, [])
            source = None
            source_effects = []
            if has_source:
                source = _EffectStub(150, 100, "blue", alive=True)
                source._tag = "source"
                source_effects = source.effects
            rng = __import__("random").Random(seed)
            before = {attr: getattr(inv, attr, 0) for attr in timer_attrs()}
            for extra in ("blood_frenzy_timer", "blood_frenzy_cd",
                          "last_damage_timer", "empower_charge",
                          "static_timer", "static_tick", "static_cd",
                          "thorn_timer", "thorn_cd"):
                before[extra] = getattr(inv, extra)
            inv.notify_damage_taken(rng=rng, damage=damage, source=source)
            after = {attr: getattr(inv, attr, 0) for attr in timer_attrs()}
            for extra in ("blood_frenzy_timer", "blood_frenzy_cd",
                          "last_damage_timer", "empower_charge",
                          "static_timer", "static_tick", "static_cd",
                          "thorn_timer", "thorn_cd"):
                after[extra] = getattr(inv, extra)
            rows.append({
                "hero": spec, "loadout": list(loadout), "hp_ratio": hp_ratio,
                "damage": damage, "has_source": has_source, "seed": seed,
                "before": before, "after": after,
                "source_effects": list(source_effects),
                "notifications": [dict(n) for n in notifications],
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
        "stats": stats(env),
        "stat_application": stat_application(env),
        "deaths": deaths(env),
        "timer_attrs": timer_attrs(),
        "timers": timers(env),
        "auto_triggers": auto_triggers(env),
        "notify_damage": notify_damage(env),
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
