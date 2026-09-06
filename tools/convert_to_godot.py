#!/usr/bin/env python3
"""
convert_to_godot.py — Export data pygame -> Godot JSON + Resource

Menjalankan ini menghasilkan res://data/*.json yang dibaca HeroDB/BossDB Godot.
Tanpa ini, Godot pakai fallback hardcode 6 hero.

Usage:
    python tools/convert_to_godot.py

Output:
    godot/data/heroes.json
    godot/data/bosses.json
    godot/data/levels.json
    godot/data/hero_archetypes.json
    godot/data/items.json
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GODOT_DATA = os.path.join(ROOT, "godot", "data")
os.makedirs(GODOT_DATA, exist_ok=True)

# Tambah root ke path supaya bisa import _core tanpa pygame display
sys.path.insert(0, ROOT)

def write_json(fname, data):
    path = os.path.join(GODOT_DATA, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[convert] {fname}: {len(data) if isinstance(data,(dict,list)) else 1} entries -> {path}")

def export_heroes():
    try:
        from _core import get_all_hero_types
        heroes = get_all_hero_types()
        # Sederhanakan untuk Godot: hanya field yang dipakai Hero.gd
        simple = {}
        for k, v in heroes.items():
            simple[k] = {
                "name": v.get("name", k),
                "title": v.get("title", ""),
                "role": v.get("role", "Fighter"),
                "hp": v.get("hp", 800),
                "damage": v.get("damage", 65),
                "speed": v.get("speed", 2.5),
                "range": v.get("range", 70),
                "attack_cooldown": v.get("attack_cooldown", 38),
                "skill_damage": v.get("skill_damage", 80),
                "color": "#%02x%02x%02x" % v.get("color", (200,200,200)),
                "color_dark": "#%02x%02x%02x" % v.get("color_dark", (100,100,100)),
                "cost": v.get("cost", 400),
                "is_boss_hero": v.get("is_boss_hero", False),
                "dmg_type": v.get("dmg_type", "PHYSICAL"),
                "description": v.get("description", ""),
            }
        write_json("heroes.json", simple)
    except Exception as e:
        print(f"[convert] heroes failed: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()

def export_bosses():
    try:
        import bosses.boss_data as bd
        bosses = {}
        bosses.update(getattr(bd, "MINI_BOSS_TYPES", {}))
        bosses.update(getattr(bd, "TRUE_BOSS_TYPES", getattr(bd, "BOSS_TYPES", {})))
        # Jika TRUE_BOSS_TYPES tidak ada, coba scan semua atribut
        if not bosses:
            for name in dir(bd):
                v = getattr(bd, name)
                if isinstance(v, dict) and "hp" in v and "boss_class" in str(v):
                    bosses[name.lower()] = v
        simple = {}
        for k, v in bosses.items():
            if not isinstance(v, dict): continue
            simple[k] = {
                "name": v.get("name", k),
                "title": v.get("title", ""),
                "hp": v.get("hp", 3000),
                "damage": v.get("damage", 60),
                "speed": v.get("speed", 1.0),
                "range": v.get("range", 50),
                "attack_cooldown": v.get("attack_cooldown", 40),
                "boss_class": v.get("boss_class", "mini"),
                "color": "#%02x%02x%02x" % v.get("color", (150,100,200)) if isinstance(v.get("color"), tuple) else v.get("color","#aaaaaa"),
                "entrance_color": "#%02x%02x%02x" % v.get("entrance_color", (200,150,255)) if isinstance(v.get("entrance_color"), tuple) else v.get("entrance_color","#ffffff"),
            }
        write_json("bosses.json", simple)
    except Exception as e:
        print(f"[convert] bosses failed: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()

def export_levels():
    try:
        import levels.level_data as ld
        levels = getattr(ld, "ALL_LEVELS", getattr(ld, "LEVELS", getattr(ld, "LEVEL_DATA", [])))
        if isinstance(levels, dict):
            levels = list(levels.values())
        write_json("levels.json", levels)
    except Exception as e:
        print(f"[convert] levels failed: {e} (coba export manual)", file=sys.stderr)
        # Fallback: buat 54 level dummy
        levels = [{"level_number": i+1, "name": f"Level {i+1}", "starting_gold": 1000+i*50, "gold_per_second": 2.0+i*0.05} for i in range(54)]
        write_json("levels.json", levels)

def export_archetypes():
    try:
        import hero_archetypes
        arch = getattr(hero_archetypes, "ARCHETYPES", {})
        write_json("hero_archetypes.json", arch)
    except Exception as e:
        print(f"[convert] archetypes failed: {e}", file=sys.stderr)

def export_items():
    try:
        from hero_items import ITEM_CATALOG
        write_json("items.json", ITEM_CATALOG)
    except Exception as e:
        print(f"[convert] items failed: {e}", file=sys.stderr)

if __name__ == "__main__":
    export_heroes()
    export_bosses()
    export_levels()
    export_archetypes()
    export_items()
    print("[convert] Done. Copy godot/data/*.json ke Godot res://data/")
