"""Read-only source oracle for `hero_items.py` (layer 9ck).

`hero_items.py` imports pygame at module import time, so it is never imported:
the catalog/reference constants come from `ai_item_source_oracle.source_namespace`
(which also carries the Forge functions) and the detail-popup label tables plus
`_fmt_mech_value` / `_build_item_mechanics` are exec'd on top of the same
namespace with a `get_language()` stub.

Two artefacts are written:

* `godot_rebuild/data/ui/item_mechanics.json` — the eight mechanics groups of
  every catalog entry, verbatim and in source order, so the Forge detail popup
  can print the same headers and bullets as `_build_item_mechanics`;
* `godot_rebuild/tests/fixtures/hero_items_source.json` — the file inventory,
  the 145-symbol classification (98 callables/classes + 47 module constants),
  the catalog/class/page tables, the label tables and both language renderings
  of every item's mechanics plus one format row per (key, value) pair.

This is test infrastructure, not a runtime converter. Python stays read-only.
"""
import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / "hero_items.py"
MECHANICS_DATA = ROOT / "godot_rebuild/data/ui/item_mechanics.json"
FIXTURE = HERE / "fixtures/hero_items_source.json"

sys.path.insert(0, str(HERE))
from ai_item_source_oracle import source_namespace  # noqa: E402

# Every symbol of the 4133-line module, classified once: `ported` (a native
# function carries it), `data` (baked table), `folded` (absorbed by a different
# native structure), `deviation` (documented difference) or `dead` (never called
# anywhere in the pygame source itself).

CLASSIFICATION = {
    'is_magic_hero': ('ported', 'scripts/match/hero_items.gd', 'func is_magic_hero('),
    '_apply_miasma': ('ported', 'scripts/match/hero_item_inventory.gd', 'func apply_miasma('),
    '_tick_miasma': ('ported', 'scripts/match/hero_item_inventory.gd', 'func tick_miasma('),
    'get_item_class': ('ported', 'scripts/match/item_shop_ui.gd', 'func item_class('),
    '_build_shop_pages': ('ported', 'scripts/match/item_shop_ui.gd', 'func _build_shop_pages('),
    '_fmt_mech_value': ('ported', 'scripts/match/item_mechanics.gd', 'func fmt_value('),
    '_build_item_mechanics': ('ported', 'scripts/match/item_mechanics.gd', 'func build('),
    'get_icon': ('ported', 'scripts/ui/item_forge_panel.gd', 'func _icon('),
    'HeroItemInventory': ('ported', 'scripts/match/hero_item_inventory.gd', 'func tick_auto('),
    'HeroItemInventory.__init__': ('ported', 'scripts/match/hero_item_inventory.gd', 'func _init('),
    'HeroItemInventory.count': ('ported', 'scripts/match/hero_item_inventory.gd', 'func count('),
    'HeroItemInventory.has': ('ported', 'scripts/match/hero_item_inventory.gd', 'func has('),
    'HeroItemInventory.used_slots': ('ported', 'scripts/match/hero_item_inventory.gd', 'func used_slots('),
    'HeroItemInventory.add': ('ported', 'scripts/match/hero_item_inventory.gd', 'func add('),
    'HeroItemInventory.remove': ('ported', 'scripts/match/hero_item_inventory.gd', 'func remove('),
    'HeroItemInventory._on_item_changed': ('ported', 'scripts/match/forge.gd', 'hero.apply_item_change()'),
    'HeroItemInventory.clear_on_death': ('ported', 'scripts/match/hero_item_inventory.gd', 'func clear_on_death('),
    'HeroItemInventory._sum_stat': ('ported', 'scripts/match/hero_item_inventory.gd', 'func sum_stat('),
    'HeroItemInventory.get_bonus_damage': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_bonus_damage('),
    'HeroItemInventory.get_bonus_hp': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_bonus_hp('),
    'HeroItemInventory.get_hp_pct': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_hp_pct('),
    'HeroItemInventory.get_armor': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_armor('),
    'HeroItemInventory.get_hp_regen': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_hp_regen('),
    'HeroItemInventory.get_max_hp': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_max_hp('),
    'HeroItemInventory.get_attack_speed_mult': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_attack_speed_mult('),
    'HeroItemInventory.get_lifesteal_pct': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_lifesteal_pct('),
    'HeroItemInventory.get_crit': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_crit('),
    'HeroItemInventory.get_cleave': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_cleave('),
    'HeroItemInventory.get_cooldown_reduction': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_cooldown_reduction('),
    'HeroItemInventory.get_spell_vamp': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_spell_vamp('),
    'HeroItemInventory.get_skill_amp': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_skill_amp('),
    'HeroItemInventory.get_evasion': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_evasion('),
    'HeroItemInventory.get_move_speed_pct': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_move_speed_pct('),
    'HeroItemInventory.get_heal_amp': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_heal_amp('),
    'HeroItemInventory.get_slow_resist': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_slow_resist('),
    'HeroItemInventory.get_range_bonus': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_range_bonus('),
    'HeroItemInventory.has_true_strike': ('ported', 'scripts/match/hero_item_inventory.gd', 'func has_true_strike('),
    'HeroItemInventory.get_reflect_pct': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_reflect_pct('),
    'HeroItemInventory.get_gale_as_bonus': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_gale_as_bonus('),
    'HeroItemInventory.consume_empower_strike': ('ported', 'scripts/match/hero_item_inventory.gd', 'func consume_empower_strike('),
    'HeroItemInventory.get_block': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_block('),
    'HeroItemInventory.get_armor_shred': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_armor_shred('),
    'HeroItemInventory.get_on_attack_chain': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_on_attack_chain('),
    'HeroItemInventory.get_bash': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_bash('),
    'HeroItemInventory.is_veiled': ('ported', 'scripts/match/hero_item_inventory.gd', 'func is_veiled('),
    'HeroItemInventory.is_guarding': ('dead', '', ''),
    'HeroItemInventory.get_rend_crit': ('ported', 'scripts/match/hero_item_inventory.gd', 'func get_rend_crit('),
    'HeroItemInventory.update': ('ported', 'scripts/match/hero_item_inventory.gd', 'func tick_timers('),
    'HeroItemInventory.notify_damage_taken': ('ported', 'scripts/match/hero_item_inventory.gd', 'func notify_damage_taken('),
    'HeroItemInventory.roll_crit': ('ported', 'scripts/match/hero_item_inventory.gd', 'func roll_crit('),
    'HeroItemInventory.on_basic_attack_hit': ('ported', 'scripts/match/hero_item_inventory.gd', 'func on_basic_attack_hit('),
    'HeroItemInventory._on_hit_common': ('ported', 'scripts/match/hero_item_inventory.gd', 'func _on_hit_common('),
    'HeroItemInventory.on_ranged_attack_hit': ('ported', 'scripts/match/hero_item_inventory.gd', 'func on_ranged_attack_hit('),
    '_apply_stun_to': ('ported', 'scripts/match/battle_item_effects.gd', '`_apply_stun_to(target, duration)`'),
    '_apply_silence_to': ('ported', 'scripts/match/battle_item_effects.gd', '`_apply_silence_to(target, duration)`'),
    '_apply_shred_to': ('ported', 'scripts/match/battle_item_effects.gd', 'func apply_armor_shred('),
    '_apply_amp_to': ('ported', 'scripts/match/battle_item_effects.gd', 'func apply_damage_amp('),
    '_fx_notify': ('ported', 'scripts/match/item_effects.gd', 'func notify('),
    '_fx_chain': ('ported', 'scripts/match/item_effects.gd', 'func chain_fx('),
    '_hero_level_mult': ('ported', 'scripts/match/hero_item_inventory.gd', 'func level_hp_mult('),
    'update_auras': ('ported', 'scripts/match/prototype_battle.gd', 'func _update_auras('),
    '_collect_all_units': ('ported', 'scripts/match/prototype_battle.gd', 'func _collect_all_units('),
    'suggest_item_for_hero': ('ported', 'scripts/match/hero_items.gd', 'func suggest_item_for_hero('),
    'HeroItemRenderer': ('ported', 'scripts/ui/hero_panel_layout.gd', 'func _item_slots('),
    'HeroItemRenderer.width': ('ported', 'scripts/ui/hero_panel_layout.gd', 'static func item_slot_rect('),
    'HeroItemRenderer.draw': ('ported', 'scripts/ui/hero_panel_layout.gd', 'func _draw_item_icon('),
    'HeroItemRenderer.slot_index_at': ('dead', '', ''),
    '_get_game': ('deviation', '', ''),
    '_player_heroes': ('ported', 'scripts/match/forge.gd', 'func _player_heroes('),
    '_alive_player_heroes': ('dead', '', ''),
    'pending_forge_items': ('ported', 'scripts/match/forge.gd', 'func pending_forge_items('),
    'deliver_pending_forge_items': ('ported', 'scripts/match/forge.gd', 'func deliver_pending_forge_items('),
    '_resolve_shop_target': ('ported', 'scripts/match/forge.gd', 'func resolve_target('),
    'ItemShopUI': ('ported', 'scripts/ui/item_forge_panel.gd', 'func _build_chrome('),
    'ItemShopUI.draw': ('ported', 'scripts/ui/item_forge_panel.gd', 'func refresh('),
    'ItemShopUI._draw_hero_strip': ('ported', 'scripts/ui/item_forge_panel.gd', 'func _build_hero_chips('),
    'ItemShopUI._draw_no_hero_banner': ('ported', 'scripts/ui/item_forge_panel.gd', '"no_hero_banner"'),
    'ItemShopUI._draw_panel': ('ported', 'scripts/ui/item_forge_panel.gd', 'func _build_chrome('),
    'ItemShopUI._draw_header': ('ported', 'scripts/ui/item_forge_panel.gd', '"ITEM FORGE"'),
    'ItemShopUI._draw_hero_info': ('ported', 'scripts/match/item_shop_ui.gd', 'func hero_chips('),
    'ItemShopUI._draw_owned_slots': ('ported', 'scripts/ui/item_forge_panel.gd', 'func _build_slots('),
    'ItemShopUI._draw_close': ('ported', 'scripts/ui/item_forge_panel.gd', '"close"'),
    'ItemShopUI._detail_rect': ('ported', 'scripts/ui/item_forge_panel.gd', 'const DETAIL_RECT'),
    'ItemShopUI._draw_detail_popup': ('ported', 'scripts/ui/item_forge_panel.gd', 'func _build_detail_content('),
    'ItemShopUI._page_count': ('ported', 'scripts/match/item_shop_ui.gd', 'func page_count('),
    'ItemShopUI._draw_page_tabs': ('ported', 'scripts/ui/item_forge_panel.gd', 'func _build_page_tabs('),
    'ItemShopUI._draw_item_grid': ('ported', 'scripts/ui/item_forge_panel.gd', 'func _build_cards('),
    'ItemShopUI._draw_item_card': ('ported', 'scripts/ui/item_forge_panel.gd', 'func _card_style('),
    'ItemShopUI._localized_desc': ('ported', 'scripts/ui/item_forge_panel.gd', 'func _description('),
    'ItemShopUI._wrap_text': ('ported', 'scripts/ui/item_forge_panel.gd', 'AUTOWRAP_WORD_SMART'),
    '_touch_hit': ('ported', 'scripts/ui/item_forge_panel.gd', 'func _input('),
    'handle_item_shop_click': ('ported', 'scripts/match/item_shop_ui.gd', 'func handle_click('),
    '_try_buy': ('ported', 'scripts/match/forge.gd', 'func buy('),
    '_try_drop': ('ported', 'scripts/match/forge.gd', 'func drop('),
    '_notify': ('ported', 'scripts/match/item_shop_ui.gd', 'func notice_text('),
    '_play_click': ('ported', 'scripts/match/item_shop_ui.gd', '"ui_click"'),
    '_play_buy': ('ported', 'scripts/match/item_shop_ui.gd', '"ui_buy"'),
    '_play_error': ('ported', 'scripts/match/item_shop_ui.gd', '"ui_error"'),
    'MAX_ITEM_SLOTS': ('data', 'data/ai/item_catalog.json', '"max_slots": 6'),
    'ITEM_FLAT_COST': ('data', 'data/ai/item_catalog.json', '"flat_cost": 4500'),
    'CATEGORY_CRIT': ('data', 'data/ui/item_shop_presentation.json', '"category": "crit"'),
    'CATEGORY_DAMAGE': ('data', 'data/ui/item_shop_presentation.json', '"category": "damage"'),
    'CATEGORY_LIFESTEAL': ('data', 'data/ui/item_shop_presentation.json', '"category": "lifesteal"'),
    'CATEGORY_TANK': ('data', 'data/ui/item_shop_presentation.json', '"category": "tank"'),
    'CATEGORY_SPLASH': ('data', 'data/ui/item_shop_presentation.json', '"category": "splash"'),
    'CATEGORY_AS_ARMOR': ('data', 'data/ui/item_shop_presentation.json', '"category": "as_armor"'),
    'CATEGORY_AS': ('data', 'data/ui/item_shop_presentation.json', '"category": "attack_speed"'),
    'CATEGORY_CASTER': ('data', 'data/ui/item_shop_presentation.json', '"category": "caster"'),
    'CATEGORY_GUARD': ('data', 'data/ui/item_shop_presentation.json', '"category": "guard"'),
    'CATEGORY_AGILITY': ('data', 'data/ui/item_shop_presentation.json', '"category": "agility"'),
    'CATEGORY_SHRED': ('data', 'data/ui/item_shop_presentation.json', '"category": "shred"'),
    'CATEGORY_UTILITY': ('data', 'data/ui/item_shop_presentation.json', '"category": "utility"'),
    'CATEGORY_CONTROL': ('data', 'data/ui/item_shop_presentation.json', '"category": "control"'),
    'CATEGORY_BURST': ('data', 'data/ui/item_shop_presentation.json', '"category": "burst"'),
    'CATEGORY_STATIC': ('data', 'data/ui/item_shop_presentation.json', '"category": "static"'),
    'CATEGORY_THORN': ('data', 'data/ui/item_shop_presentation.json', '"category": "thorn"'),
    'CATEGORY_FROST': ('data', 'data/ui/item_shop_presentation.json', '"category": "frost"'),
    'CATEGORY_PIERCE': ('data', 'data/ui/item_shop_presentation.json', '"category": "pierce"'),
    'CATEGORY_ICE': ('data', 'data/ui/item_shop_presentation.json', '"category": "ice"'),
    'CATEGORY_REACH': ('data', 'data/ui/item_shop_presentation.json', '"category": "reach"'),
    'CATEGORY_POISON': ('data', 'data/ui/item_shop_presentation.json', '"category": "poison"'),
    'CATEGORY_INFERNO': ('data', 'data/ui/item_shop_presentation.json', '"category": "inferno"'),
    'CATEGORY_ARCANE': ('data', 'data/ui/item_shop_presentation.json', '"category": "arcane"'),
    'CATEGORY_MORTAL': ('data', 'data/ui/item_shop_presentation.json', '"category": "mortal"'),
    'CATEGORY_MYSTIC': ('data', 'data/ui/item_shop_presentation.json', '"category": "mystic"'),
    'MAGIC_ROLE_KEYWORDS': ('data', 'scripts/match/hero_items.gd', 'const MAGIC_ROLE_KEYWORDS'),
    '_MIASMA': ('ported', 'scripts/match/hero_item_inventory.gd', 'func apply_miasma('),
    'ITEM_CATALOG': ('data', 'data/ai/item_catalog.json', '"dead_edge"'),
    'CLASS_PHYSICAL': ('data', 'scripts/match/item_shop_ui.gd', 'const CLASS_PHYSICAL'),
    'CLASS_MAGIC': ('data', 'scripts/match/item_shop_ui.gd', 'const CLASS_MAGIC'),
    'CLASS_TANK': ('data', 'scripts/match/item_shop_ui.gd', 'const CLASS_TANK'),
    'ITEM_CLASS_INFO': ('data', 'scripts/match/item_shop_ui.gd', 'const CLASS_LABELS'),
    '_ITEM_CLASS_OVERRIDES': ('data', 'scripts/match/item_shop_ui.gd', 'const CLASS_OVERRIDES'),
    '_MAP_CATEGORY_TO_CLASS': ('data', 'scripts/match/item_shop_ui.gd', 'const CATEGORY_TO_CLASS'),
    'ITEMS_PER_PAGE': ('data', 'scripts/match/item_shop_ui.gd', 'const ITEMS_PER_PAGE'),
    'CLASS_ITEM_ORDER': ('data', 'scripts/match/item_shop_ui.gd', 'const CLASS_ITEM_ORDER'),
    'ITEM_SHOP_ORDER': ('folded', 'scripts/match/item_shop_ui.gd', 'func _build_shop_pages('),
    'CATEGORY_INFO': ('data', 'data/ui/item_shop_presentation.json', '"category_color"'),
    '_FIELD_LABELS': ('data', 'scripts/match/item_mechanics.gd', 'const FIELD_LABELS'),
    '_GROUP_LABELS': ('data', 'scripts/match/item_mechanics.gd', 'const GROUP_LABELS'),
    '_MECH_GROUPS': ('data', 'scripts/match/item_mechanics.gd', 'const MECH_GROUPS'),
    '_PCT_KEYS': ('data', 'scripts/match/item_mechanics.gd', 'const PCT_KEYS'),
    '_FRAME_KEYS': ('data', 'scripts/match/item_mechanics.gd', 'const FRAME_KEYS'),
    '_ITEMS_DIR': ('deviation', '', ''),
    '_ICON_CACHE': ('deviation', '', ''),
}

TARGET_SOURCE_ONLY = {"dead", "deviation"}
DEAD_SYMBOLS = ["HeroItemInventory.is_guarding", "HeroItemRenderer.slot_index_at",
                "_alive_player_heroes"]
DEVIATION_SYMBOLS = ["_get_game", "_ICON_CACHE", "_ITEMS_DIR"]
LABEL_NAMES = {"_FIELD_LABELS", "_GROUP_LABELS", "_MECH_GROUPS", "_PCT_KEYS",
               "_FRAME_KEYS"}
MECH_FUNCTIONS = ("_fmt_mech_value", "_build_item_mechanics")
MECH_KEYS = ("stats", "passive", "active", "aura", "block", "on_attack",
             "multishot", "bash")
BANNER = re.compile(r"^# (═{10,})$")

# Heroes that exercise the magic gate: the keyword list plus the "Anti-Mage"
# exception and the empty/mixed roles.
MAGIC_ROLES = ["Mage", "Frost Mage", "Warlock", "Anti-Mage", "Mage Hunter",
               "Anti-Mage Mage", "Marskman", "Tank", "", "Starweaver",
               "Hex Priestess", "Eldritch Shaman", "Pyromancer", "Farseer"]


def _sections(text):
    """Every `# ==== / title / ====` banner: the file's own section index."""
    lines = text.split("\n")
    rows = []
    index = 0
    while index + 2 < len(lines):
        if BANNER.match(lines[index]) and BANNER.match(lines[index + 2]):
            rows.append({
                "line": index + 2,
                "name": lines[index + 1].lstrip("# ").strip(),
            })
            index += 3
            continue
        index += 1
    return rows


def _labels_namespace(env):
    """Exec the label tables and the mechanics builders into the catalog env."""
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    nodes = [
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in LABEL_NAMES
    ]
    nodes += [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in MECH_FUNCTIONS
    ]
    assert len(nodes) == len(LABEL_NAMES) + len(MECH_FUNCTIONS), "labels missing"
    nodes.sort(key=lambda node: node.lineno)
    env["get_language"] = lambda: "id"
    code = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(code, "<hero_items labels>", "exec"), env)
    return env


def mechanics_groups(env):
    """The eight mechanics groups of every item, verbatim from the catalog."""
    rows = {}
    for item_id, data in env["ITEM_CATALOG"].items():
        groups = {}
        for key in MECH_KEYS:
            group = data.get(key)
            if isinstance(group, dict) and group:
                groups[key] = dict(group)
        rows[item_id] = groups
    return rows


def mechanics_lines(env, language):
    env["get_language"] = lambda: language
    build = env["_build_item_mechanics"]
    return {item_id: [list(row) for row in build(data)]
            for item_id, data in env["ITEM_CATALOG"].items()}


def format_rows(env):
    """One row per (key, value) the popup formats, in both languages."""
    rows = []
    seen = set()
    for data in env["ITEM_CATALOG"].values():
        for key in MECH_KEYS:
            group = data.get(key)
            if not isinstance(group, dict):
                continue
            for field, value in group.items():
                if field == "name" or (field, value) in seen:
                    continue
                seen.add((field, value))
                rows.append({
                    "key": field,
                    "value": value,
                    "kind": "float" if isinstance(value, float) else "int",
                    "id": env["_fmt_mech_value"](field, value, False),
                    "en": env["_fmt_mech_value"](field, value, True),
                })
    rows.sort(key=lambda row: (row["key"], str(row["value"])))
    return rows


def catalog_rows(env):
    """Catalog identity plus the class/page routing the Forge uses."""
    items = {}
    for item_id, data in env["ITEM_CATALOG"].items():
        items[item_id] = {
            "name": data["name"],
            "category": data["category"],
            "cost": data["cost"],
            "class": env["get_item_class"](item_id),
            "melee_only": bool(data.get("melee_only", False)),
            "magic_only": bool(data.get("magic_only", False)),
            "drops_on_death": bool(data.get("drops_on_death", False)),
        }
    pages, meta = env["_build_shop_pages"]()
    return {
        "count": len(items),
        "items": items,
        "flat_cost": env["ITEM_FLAT_COST"],
        "max_slots": env["MAX_ITEM_SLOTS"],
        "items_per_page": env["ITEMS_PER_PAGE"],
        "class_overrides": dict(env["_ITEM_CLASS_OVERRIDES"]),
        "magic_only": sorted(item_id for item_id, data in items.items()
                             if data["magic_only"]),
        "class_order": {key: list(value) for key, value in
                        env["CLASS_ITEM_ORDER"].items()},
        "pages": [list(page) for page in pages],
        "page_meta": [list(row) for row in meta],
        "shop_order": [sid for page in pages for sid in page],
    }


def payload(env):
    text = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    functions = [node.name for node in tree.body
                 if isinstance(node, ast.FunctionDef)]
    classes = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes[node.name] = [child.name for child in node.body
                                  if isinstance(child, ast.FunctionDef)]
    assigns = [target.id for node in tree.body if isinstance(node, ast.Assign)
               for target in node.targets if isinstance(target, ast.Name)]
    symbols = list(functions) + [
        name for name, methods in classes.items() for name in [name] + [
            "%s.%s" % (name, method) for method in methods
        ]
    ]
    kinds = {}
    for symbol in symbols + assigns:
        kind = CLASSIFICATION[symbol][0]
        kinds[kind] = kinds.get(kind, 0) + 1
    labels = env["_FIELD_LABELS"]
    groups = env["_GROUP_LABELS"]
    return {
        "file": {
            "file": "hero_items.py",
            "lines": len(text.splitlines()),
            "classes": len(classes),
            "functions": len(functions),
            "methods": sum(len(methods) for methods in classes.values()),
            "assigns": len(assigns),
            "symbols": len(symbols),
        },
        "sections": _sections(text),
        "class_methods": classes,
        "symbols": {
            "count": len(symbols),
            "items": symbols,
            "kinds": kinds,
            "dead": DEAD_SYMBOLS,
            "deviations": DEVIATION_SYMBOLS,
        },
        "classification": {
            symbol: {"kind": CLASSIFICATION[symbol][0],
                     "target": CLASSIFICATION[symbol][1],
                     "token": CLASSIFICATION[symbol][2]}
            for symbol in symbols + assigns
        },
        "catalog": catalog_rows(env),
        "labels": {
            "field": {key: list(value) for key, value in labels.items()},
            "group": {key: list(value) for key, value in groups.items()},
            "groups": list(env["_MECH_GROUPS"]),
            "pct": sorted(env["_PCT_KEYS"]),
            "frame": sorted(env["_FRAME_KEYS"]),
        },
        "format": format_rows(env),
        "mechanics": {
            "id": mechanics_lines(env, "id"),
            "en": mechanics_lines(env, "en"),
        },
        "magic": {role: bool(env["is_magic_hero"](
            type("Hero", (), {"role": role})())) for role in MAGIC_ROLES},
    }


def build_fixture():
    """The two artefacts, computed live (shared with validate_project)."""
    env = _labels_namespace(source_namespace(with_functions=True, with_forge=True))
    return payload(env), mechanics_groups(env)


def main(argv):
    data, groups = build_fixture()
    mech_text = json.dumps(groups, indent=1, ensure_ascii=False) + "\n"
    fix_text = json.dumps(data, indent=1, ensure_ascii=False) + "\n"
    if "--write" in argv:
        MECHANICS_DATA.write_text(mech_text, encoding="utf-8")
        FIXTURE.write_text(fix_text, encoding="utf-8")
        print("wrote %s (%d items)" % (MECHANICS_DATA.name, len(groups)))
        print("wrote %s (%d symbols)" % (FIXTURE.name, data["symbols"]["count"]))
        return 0
    ok = True
    for path, text in ((MECHANICS_DATA, mech_text), (FIXTURE, fix_text)):
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current != text:
            ok = False
            print("MISMATCH %s" % path)
    print("OK (fixture matches the source)" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

