#!/usr/bin/env python3
"""Export hero_items.py to the active Godot project without pygame at runtime.

Python remains the item oracle. The exporter imports the real module with
lightweight UI stubs, writes the native catalog/shop contract, and writes a
parity fixture for role gates, item class/pages, mechanics text, inventory
getters, deterministic auto-triggers, auras, on-hit effects and AI suggestions.
--check is a fail-closed exact-byte gate.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
SOURCE = ROOT / "hero_items.py"
CONTRACT = PROJECT / "data/hero_items.json"
FIXTURE = PROJECT / "tests/fixtures/hero_items_parity.json"
sys.path.insert(0, str(ROOT / "tools"))
import prepare_godot_core as core_prep  # noqa: E402


def _jsonable(value, float_digits: int | None = None):
    if isinstance(value, tuple):
        return [_jsonable(v, float_digits) for v in value]
    if isinstance(value, (list, set, frozenset)):
        return [_jsonable(v, float_digits) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v, float_digits) for k, v in value.items()}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise AssertionError(f"Non-finite item value: {value!r}")
        if float_digits is not None:
            return round(value, float_digits)
    return value


def _text(value: dict, float_digits: int | None = None) -> str:
    return json.dumps(_jsonable(value, float_digits), ensure_ascii=False, indent=2,
                      allow_nan=False, sort_keys=True) + "\n"


@contextlib.contextmanager
def source_module():
    """Import hero_items with UI-only dependencies stubbed (no pygame call)."""
    levels = core_prep.assignments(ROOT / "_core.py", upper_only=True)["HERO_LEVELS"]
    stubs = {
        "pygame": types.ModuleType("pygame"),
        "ui_theme": types.ModuleType("ui_theme"),
        "localization": types.ModuleType("localization"),
        "_core": types.ModuleType("_core"),
    }
    stubs["pygame"].font = types.SimpleNamespace(Font=lambda *a, **k: None)
    stubs["localization"].tr = lambda key, **kw: key
    stubs["localization"].get_language = lambda: "id"
    stubs["_core"].HERO_LEVELS = levels
    stubs["_core"].get_font = lambda *a, **k: None
    stubs["_core"].title_font = lambda *a, **k: None
    old = {name: sys.modules.get(name) for name in stubs}
    sys.modules.update(stubs)
    try:
        spec = importlib.util.spec_from_file_location("mystic_items_export", SOURCE)
        if spec is None or spec.loader is None:
            raise AssertionError(f"Cannot load {SOURCE}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        yield module
    finally:
        for name, value in old.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value


def build_contract(module) -> dict:
    catalog = module.ITEM_CATALOG
    if len(catalog) != 33:
        raise AssertionError(f"Unexpected item coverage: {len(catalog)}")
    core = json.loads((PROJECT / "data/core_data.json").read_text(encoding="utf-8"))
    if _jsonable(catalog) != core.get("items", {}):
        raise AssertionError("Stale core item catalog; run tools/prepare_godot_core.py")
    pages, meta = module._build_shop_pages()
    # JSON sort-keys removes Python dict insertion order; mechanics text must
    # preserve the source field order, so export it explicitly.
    mech_field_order = {}
    for sid, data in catalog.items():
        groups = {}
        for gkey in module._MECH_GROUPS:
            group = data.get(gkey)
            if isinstance(group, dict) and group:
                groups[gkey] = list(group.keys())
        mech_field_order[sid] = groups
    mech_value_types = {}
    for sid, data in catalog.items():
        groups = {}
        for gkey in module._MECH_GROUPS:
            group = data.get(gkey)
            if isinstance(group, dict) and group:
                types = {}
                for key, value in group.items():
                    if isinstance(value, bool):
                        types[key] = "bool"
                    elif isinstance(value, int):
                        types[key] = "int"
                    elif isinstance(value, float):
                        types[key] = "float"
                    elif isinstance(value, str):
                        types[key] = "str"
                    else:
                        types[key] = type(value).__name__
                groups[gkey] = types
        mech_value_types[sid] = groups
    return _jsonable({
        "schema": 1,
        "source": "hero_items.py",
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "max_item_slots": module.MAX_ITEM_SLOTS,
        "item_flat_cost": module.ITEM_FLAT_COST,
        "magic_role_keywords": list(module.MAGIC_ROLE_KEYWORDS),
        "catalog": catalog,
        "classes": {"physical": module.CLASS_PHYSICAL, "magic": module.CLASS_MAGIC, "tank": module.CLASS_TANK},
        "class_info": module.ITEM_CLASS_INFO,
        "class_overrides": module._ITEM_CLASS_OVERRIDES,
        "category_to_class": module._MAP_CATEGORY_TO_CLASS,
        "class_item_order": module.CLASS_ITEM_ORDER,
        "items_per_page": module.ITEMS_PER_PAGE,
        "shop_pages": pages,
        "shop_page_meta": meta,
        "item_shop_order": module.ITEM_SHOP_ORDER,
        "category_info": module.CATEGORY_INFO,
        "field_labels": module._FIELD_LABELS,
        "group_labels": module._GROUP_LABELS,
        "mech_groups": list(module._MECH_GROUPS),
        "mech_field_order": mech_field_order,
        "mech_value_types": mech_value_types,
        "pct_keys": sorted(module._PCT_KEYS),
        "frame_keys": sorted(module._FRAME_KEYS),
    })


class _Unit:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        self.debuffs = []
        self.slows = []
        self.stuns = []
        self.silences = []
        self.shreds = []
        self.amps = []
        self.misses = []
        self.damage = []
        self.heals = []

    def apply_debuff(self, kind, amount, duration, source_team=None):
        self.debuffs.append([kind, amount, duration, source_team])

    def apply_slow(self, amount, duration):
        self.slows.append([amount, duration])

    def apply_stun(self, duration):
        self.stuns.append(duration)

    def apply_silence(self, duration):
        self.silences.append(duration)

    def apply_armor_shred(self, amount, duration):
        self.shreds.append([amount, duration])

    def apply_damage_amp(self, amount, duration):
        self.amps.append([amount, duration])

    def apply_miss_chance(self, amount, duration):
        self.misses.append([amount, duration])

    def apply_heal_amp(self, amount, duration):
        self.heals.append([amount, duration])

    def take_damage(self, amount, team=None, kind=None, source=None):
        self.damage.append([amount, team, kind])
        self.hp = max(0, getattr(self, "hp", 0) - amount)
        return amount


def _hero(module, role="Fighter", rng=70, hp=1000, level=1, team="blue", x=0, y=0):
    h = _Unit(role=role, range=rng, base_hp=hp, hp=hp, max_hp=hp, level=level,
              team=team, x=x, y=y, alive=True, facing=1, target=None,
              is_melee_hero=rng <= 80)
    h.items = module.HeroItemInventory(h)
    return h


def _snapshot_inv(inv):
    keys = ["blood_frenzy_timer", "blood_frenzy_cd", "last_damage_timer", "guard_timer", "guard_cd",
            "aura_guard_block", "veil_timer", "veil_cd", "chains_cd", "rend_timer", "rend_cd",
            "bash_cd", "overwhelm_cd", "static_timer", "static_cd", "static_tick", "thorn_timer",
            "thorn_cd", "arctic_cd", "gale_timer", "gale_cd", "pierce_bash_cd", "searbrand_cd",
            "arcane_cd", "fulgur_cd", "hex_cd", "rift_cd", "pact_cd", "vine_cd", "ghost_timer",
            "ghost_cd", "empower_charge", "aura_armor", "aura_as", "aura_armor_reduction"]
    return {key: getattr(inv, key, 0) for key in keys}


def _getters(inv):
    cleave = inv.get_cleave()
    block = inv.get_block()
    shred = inv.get_armor_shred()
    chain = inv.get_on_attack_chain()
    bash = inv.get_bash()
    return {
        "bonus_damage": inv.get_bonus_damage(), "bonus_hp": inv.get_bonus_hp(), "hp_pct": inv.get_hp_pct(),
        "armor": inv.get_armor(), "hp_regen": inv.get_hp_regen(), "max_hp": inv.get_max_hp(),
        "attack_speed_mult": inv.get_attack_speed_mult(), "lifesteal": inv.get_lifesteal_pct(),
        "crit": list(inv.get_crit()), "cleave": list(cleave) if cleave else None,
        "cooldown_reduction": inv.get_cooldown_reduction(), "spell_vamp": inv.get_spell_vamp(),
        "skill_amp": inv.get_skill_amp(), "evasion": inv.get_evasion(), "move_speed_pct": inv.get_move_speed_pct(),
        "heal_amp": inv.get_heal_amp(), "slow_resist": inv.get_slow_resist(), "range_bonus": inv.get_range_bonus(),
        "true_strike": inv.has_true_strike(), "reflect_pct": inv.get_reflect_pct(),
        "gale_as_bonus": inv.get_gale_as_bonus(), "block": list(block) if block else None,
        "armor_shred": list(shred) if shred else None, "on_attack_chain": chain, "bash": bash,
        "veiled": inv.is_veiled(), "guarding": inv.is_guarding(), "rend_crit": inv.get_rend_crit(),
    }


def build_oracle(module) -> dict:
    catalog = module.ITEM_CATALOG
    ids = list(catalog)
    roles = ["", "Mage", "Mage/Trickster", "Boss/Magic", "Sorcerer", "Caster", "Warlock", "Witch",
             "Sage", "Prophet", "Priestess", "Pyromancer", "Necromancer", "Shaman", "Summoner",
             "Chorister", "Farseer", "Starweaver", "Hexblade", "Eldritch Knight", "Anti-Mage",
             "Fighter", "Tank", "Marksman", "Assassin"]
    role_cases = [{"role": role, "magic": module.is_magic_hero(types.SimpleNamespace(role=role))} for role in roles]
    class_cases = {sid: module.get_item_class(sid) for sid in ids}
    class_cases["missing_item"] = module.get_item_class("missing_item")
    mechanics = {}
    for lang in ("id", "en"):
        module.get_language = lambda lang=lang: lang
        mechanics[lang] = {sid: module._build_item_mechanics(catalog[sid]) for sid in ids}
    module.get_language = lambda: "id"

    loadouts = [
        ("empty", "Fighter", 70, []), ("dead_edge", "Marksman", 150, ["dead_edge"]),
        ("demon_maw", "Fighter", 70, ["demon_maw"]), ("leviathan", "Tank", 70, ["leviathan_heart"]),
        ("moon_shard", "Marksman", 150, ["moon_shard", "moon_shard"]),
        ("astral", "Mage", 150, ["astral_codex", "sage_scepter"]),
        ("spectral", "Mage", 150, ["spectral_charm"]), ("gale", "Marksman", 150, ["gale_pike"]),
        ("razor", "Tank", 70, ["razor_carapace"]), ("runic", "Mage", 150, ["runic_gavel"]),
        ("block_melee", "Tank", 70, ["steel_aegis", "scarlet_bulwark"]),
        ("block_ranged", "Marksman", 150, ["steel_aegis", "scarlet_bulwark"]),
        ("corroder", "Fighter", 70, ["corroder"]), ("fenrir", "Fighter", 70, ["fenrir_chain"]),
        ("abyss", "Tank", 70, ["abyss_breaker", "sundering_cudgel"]),
        ("frost_miasma", "Marksman", 150, ["frostbound_eye", "basilisk_breath"]),
        ("vine", "Mage", 150, ["vine_rod"]), ("caps", "Mage", 150, ["octarine_core", "astral_codex", "monarch_wings", "monarch_wings"]),
    ]
    getter_cases = []
    for name, role, rng, items in loadouts:
        h = _hero(module, role, rng)
        for sid in items:
            h.items.add(sid)
        if name == "demon_maw":
            h.items.blood_frenzy_timer = 120
        if name == "spectral":
            h.items.ghost_timer = 90
        if name == "gale":
            h.items.gale_timer = 90
        if name == "razor":
            h.items.thorn_timer = 90
        if name == "runic":
            h.items.empower_charge = 0
        if name == "block_melee":
            h.items.aura_guard_block = 40
        h.items.aura_armor = 3
        h.items.aura_as = 10
        h.items.aura_armor_reduction = 1
        getter_cases.append({"name": name, "role": role, "range": rng, "items": items,
                             "getters": _getters(h.items), "state": _snapshot_inv(h.items)})

    # Deterministic auto-trigger scenarios (no RNG in update()).
    trigger_cases = []
    trigger_items = ["demon_maw", "scarlet_bulwark", "tempest_vane", "fenrir_chain", "sanguine_thorn",
                     "abyss_breaker", "thunder_coil", "razor_carapace", "everfrost_guard", "gale_pike",
                     "searbrand", "astral_codex", "fulgur_scepter", "hex_idol", "rift_veil",
                     "vital_stone", "spectral_charm", "leviathan_heart", "runic_gavel"]
    for sid in trigger_items:
        h = _hero(module, "Mage" if catalog[sid].get("magic_only") else "Fighter", 150 if catalog[sid].get("magic_only") else 70, hp=1000)
        h.items.add(sid)
        h.hp = 200
        h.max_hp = 1000
        target = _Unit(alive=True, team="red", x=120, y=0, hp=800, max_hp=800, range=100)
        h.target = target
        enemies = [target, _Unit(alive=True, team="red", x=160, y=0, hp=800, max_hp=800, range=100)]
        if sid == "thunder_coil":
            h.items.static_timer = 60
            h.items.static_tick = 1
        if sid == "runic_gavel":
            h.items.empower_charge = 5
        before = _snapshot_inv(h.items)
        h.items.update(1, enemies)
        trigger_cases.append({"item": sid, "before": before, "after": _snapshot_inv(h.items),
                              "hero_hp": h.hp, "hero_x": h.x, "hero_y": h.y,
                              "target_debuffs": target.debuffs, "target_slows": target.slows,
                              "target_stuns": target.stuns, "target_silences": target.silences,
                              "target_damage": target.damage,
                              "enemy_damage": [e.damage for e in enemies]})

    # Auras: two allies + enemy hero/minion/boss, Steel Aegis + Guard + Frost/Solar/Sear.
    aura_heroes = []
    for name, role, team, x, items in [
        ("aegis", "Tank", "blue", 0, ["steel_aegis"]),
        ("guard", "Tank", "blue", 40, ["scarlet_bulwark"]),
        ("frost", "Mage", "blue", 80, ["everfrost_guard", "solar_brand", "searbrand"]),
        ("enemy", "Fighter", "red", 120, []),
    ]:
        h = _hero(module, role, 70, team=team, x=x)
        for sid in items:
            h.items.add(sid)
        if name == "guard":
            h.items.guard_timer = 100
            h.max_hp = 2000
        aura_heroes.append(h)
    minion = _Unit(alive=True, team="red", x=140, y=0, hp=300, max_hp=300)
    boss = _Unit(alive=True, team="red", x=160, y=0, hp=5000, max_hp=5000)
    main_mod = sys.modules["__main__"]
    old_game = getattr(main_mod, "game_instance", None)
    main_mod.game_instance = types.SimpleNamespace(minions=[minion], active_boss=boss)
    try:
        module.update_auras(aura_heroes)
    finally:
        if old_game is None:
            del main_mod.game_instance
        else:
            main_mod.game_instance = old_game
    aura_case = {"heroes": [{"aura_armor": h.items.aura_armor, "aura_as": h.items.aura_as,
                              "aura_armor_reduction": h.items.aura_armor_reduction,
                              "aura_guard_block": h.items.aura_guard_block} for h in aura_heroes],
                 "minion_debuffs": minion.debuffs, "minion_misses": minion.misses,
                 "boss_debuffs": boss.debuffs}

    # On-hit with procs forced deterministic by temporarily setting chances to 1.
    saved = copy.deepcopy(catalog)
    try:
        for sid in ("fenrir_chain", "thunder_coil", "corroder", "basilisk_breath"):
            if "on_attack" in catalog[sid]:
                catalog[sid]["on_attack"]["chance"] = 1.0
        for sid in ("abyss_breaker", "sundering_cudgel"):
            if "bash" in catalog[sid]:
                catalog[sid]["bash"]["chance"] = 1.0
        catalog["basilisk_breath"]["multishot"]["chance"] = 1.0
        catalog["thunder_coil"]["active"]["proc_chance"] = 1.0
        on_hit_cases = []
        for sid in ["corroder", "abyss_breaker", "fenrir_chain", "sundering_cudgel", "frostbound_eye",
                    "basilisk_breath", "runic_gavel", "vine_rod", "demon_maw", "cleave_axe"]:
            h = _hero(module, "Mage" if catalog[sid].get("magic_only") else "Fighter",
                      150 if sid in ("basilisk_breath", "frostbound_eye") else 70)
            h.items.add(sid)
            if sid == "runic_gavel":
                h.items.empower_charge = 0
            target = _Unit(alive=True, team="red", x=100, y=0, hp=800, max_hp=800, range=100)
            extra = _Unit(alive=True, team="red", x=140, y=0, hp=800, max_hp=800, range=100)
            h.items.on_basic_attack_hit(target, 100, [target, extra])
            on_hit_cases.append({"item": sid, "hero_hp": h.hp, "state": _snapshot_inv(h.items),
                                 "target_debuffs": target.debuffs, "target_slows": target.slows,
                                 "target_stuns": target.stuns, "target_damage": target.damage,
                                 "extra_damage": extra.damage, "extra_debuffs": extra.debuffs})
    finally:
        catalog.clear()
        catalog.update(saved)

    suggest_cases = []
    for role, rng in [("Tank", 70), ("Bruiser", 70), ("Fighter", 70), ("Marksman", 150),
                      ("Assassin", 150), ("Mage", 150), ("Trickster", 150), ("Boss/Magic", 150),
                      ("Anti-Mage", 150), ("Summoner", 150), ("Unknown", 70)]:
        h = types.SimpleNamespace(role=role, range=rng)
        for owned in ([], ["leviathan_heart"], ["cleave_axe", "holy_rapier"]):
            suggest_cases.append({"role": role, "range": rng, "owned": owned,
                                  "suggestion": module.suggest_item_for_hero(h, set(owned))})

    return _jsonable({
        "schema": 1,
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "role_cases": role_cases,
        "class_cases": class_cases,
        "mechanics": mechanics,
        "getter_cases": getter_cases,
        "trigger_cases": trigger_cases,
        "aura_case": aura_case,
        "on_hit_cases": on_hit_cases,
        "suggest_cases": suggest_cases,
    }, float_digits=12)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        with source_module() as module:
            contract = build_contract(module)
            oracle = build_oracle(module)
        outputs = {CONTRACT: _text(contract), FIXTURE: _text(oracle, float_digits=12)}
        if args.check:
            stale = [str(path.relative_to(ROOT)) for path, text in outputs.items()
                     if not path.is_file() or path.read_text(encoding="utf-8") != text]
            if stale:
                parser.exit(1, "Stale item data: %s; run tools/prepare_godot_items.py\n" % ", ".join(stale))
        else:
            for path, text in outputs.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_suffix(path.suffix + ".tmp")
                temporary.write_text(text, encoding="utf-8")
                temporary.replace(path)
    except (AssertionError, ValueError, TypeError, KeyError, OSError, ImportError) as exc:
        parser.exit(1, f"Item preparation failed: {exc}\n")
    digest = hashlib.sha256(outputs[CONTRACT].encode()).hexdigest()[:12]
    print(f"{'Verified' if args.check else 'Prepared'} hero items: {len(contract['catalog'])} items, "
          f"{len(contract['shop_pages'])} shop pages; sha256={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
