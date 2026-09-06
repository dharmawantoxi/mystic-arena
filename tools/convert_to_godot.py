#!/usr/bin/env python3
"""
convert_to_godot.py — Export data pygame -> Godot JSON + Resource

Menjalankan ini menghasilkan res://data/*.json yang dibaca HeroDB/BossDB Godot.
Tanpa ini, Godot pakai fallback hardcode 6 hero.

Usage:
    python tools/convert_to_godot.py

Output:
    godot/data/heroes.json            (+ field skill_* untuk SkillBook.gd)
    godot/data/bosses.json
    godot/data/levels.json
    godot/data/hero_archetypes.json
    godot/data/items.json
    godot/data/items_meta.json        (slot, harga flat, urutan toko)
    godot/data/towers.json            (ARCHER/CANNON/ICE/MAGE_LEVELS + konstanta)
    godot/data/nexus.json             (NEXUS_LEVELS + castle shield)
    godot/data/economy.json           (gold/s, bonus level, multiplier difficulty, wave)
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
                # ── Skill Q/W/E/R (dibaca SkillBook.gd) ──
                # pygame: HERO_TYPES[*]["skill_*"] + hero_skills/_bundle.py
                "skill_name": v.get("skill_name", ""),
                "skill_desc": v.get("skill_desc", ""),
                "skill_cooldown": v.get("skill_cooldown", 300),
                "skill_range": v.get("skill_range", 100),
                "skill_duration": v.get("skill_duration", 0),
                # ── HERO SHOP meta (dibaca MainMenu.gd; paritas
                #    _unlock_hero_in_meta_shop _core.py:5298-5328) ──
                # unlock_cost = harga meta gold final (starter 0 / boss 4500 —
                # STARTER/MINI/TRUE_BOSS_HERO_UNLOCK_COST _core.py:1248-1250),
                # unlock_require_boss = boss yang harus dikalahkan dulu,
                # boss_class = tab shop (mini/true).
                "unlock_cost": int(v.get("unlock_cost", 600)),
                "unlock_require_boss": v.get("unlock_require_boss"),
                "boss_class": v.get("boss_class", ""),
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


def _hex(c, fallback="#ffffff"):
    """(r,g,b) tuple pygame -> '#rrggbb' (Color('#..') wajib di Godot)."""
    if isinstance(c, (tuple, list)) and len(c) >= 3:
        return "#%02x%02x%02x" % (int(c[0]) & 255, int(c[1]) & 255, int(c[2]) & 255)
    if isinstance(c, str):
        return c if c.startswith("#") else "#" + c
    return fallback


def export_items_meta():
    """Slot/harga/urutan toko item — dibaca ItemDB.gd + ShopPanel.gd."""
    try:
        import hero_items as hi
        cat_info = {}
        for k, v in getattr(hi, "CATEGORY_INFO", {}).items():
            cat_info[k] = {"label": v[0], "color": _hex(v[1])}
        out = {
            "max_slots": hi.MAX_ITEM_SLOTS,
            "flat_cost": hi.ITEM_FLAT_COST,
            "shop_order": hi.ITEM_SHOP_ORDER,
            "categories": cat_info,
        }
        write_json("items_meta.json", out)
    except Exception as e:
        print(f"[convert] items_meta failed: {e}", file=sys.stderr)


def export_hero_levels():
    """Kurva level hero (HERO_LEVELS) — dibaca HeroDB.gd untuk upgrade hero."""
    try:
        import _core
        levels = {str(lv): dict(d) for lv, d in _core.HERO_LEVELS.items()}
        out = {
            "max_level": _core.MAX_HERO_LEVEL,
            "boss_hero_upgrade_cost_mult": float(
                getattr(_core, "BOSS_HERO_UPGRADE_COST_MULT", 1.0)),
            "levels": levels,
        }
        write_json("hero_levels.json", out)
    except Exception as e:
        print(f"[convert] hero_levels failed: {e}", file=sys.stderr)


def export_towers():
    """Tabel upgrade 4 jalur menara + konstanta — dibaca TowerDB.gd."""
    try:
        import _core
        paths = {}
        for ttype, levels in _core.TOWER_UPGRADE_PATHS.items():
            paths[ttype] = {str(lv): dict(stats) for lv, stats in levels.items()}
        colors = {}
        for ttype, c in _core.TOWER_TYPE_COLORS.items():
            colors[ttype] = {"main": _hex(c["main"]), "dark": _hex(c["dark"])}
        out = {
            "max_level": _core.TOWER_MAX_LEVEL,
            "hp_multiplier": _core.TOWER_HP_MULTIPLIER,
            "shield_hp_ratio": _core.TOWER_SHIELD_HP_RATIO,
            # paritas Game.try_build_tower: menara L1 (archer) = 100 gold
            "build_cost": 100,
            "slot_size": _core.SLOT_SIZE,
            "bullet_speed": _core.BULLET_SPEED,
            "bullet_radius": _core.BULLET_RADIUS,
            "regen_shield_cost": _core.TOWER_REGEN_SHIELD_COST,
            "regen_shield_min_level": _core.TOWER_REGEN_SHIELD_MIN_LEVEL,
            # Fitur berbayar: shield menara ikut regen setelah jeda tanpa damage
            # (paritas Tower.activate_regen_shield + blok REGEN SHIELD di update)
            "regen_shield": {
                "enabled": _core.TOWER_REGEN_SHIELD_ENABLED,
                "delay_frames": _core.TOWER_REGEN_SHIELD_DELAY,
                "rate_per_frame": _core.TOWER_REGEN_SHIELD_RATE,
            },
            "hp_regen": {
                "enabled": _core.TOWER_HP_REGEN_ENABLED,
                "delay_frames": _core.TOWER_HP_REGEN_DELAY,
                "rate_per_frame": _core.TOWER_HP_REGEN_RATE,
                "max_ratio": _core.TOWER_HP_REGEN_MAX_RATIO,
            },
            "colors": colors,
            "info": _core.TOWER_TYPE_INFO,
            "paths": paths,
        }
        write_json("towers.json", out)
    except Exception as e:
        print(f"[convert] towers failed: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()


def export_nexus():
    """NEXUS_LEVELS (castle) + castle shield — dibaca Nexus.gd."""
    try:
        import _core
        levels = {}
        for lv, data in _core.NEXUS_LEVELS.items():
            d = dict(data)
            if "color_accent" in d:
                d["color_accent"] = _hex(d["color_accent"])
            levels[str(lv)] = d
        out = {
            "levels": levels,
            "max_level": _core.MAX_NEXUS_LEVEL,
            "base_radius": _core.BASE_RADIUS,
            "shield": {
                "enabled": _core.CASTLE_SHIELD_ENABLED,
                "free_waves": _core.CASTLE_SHIELD_FREE_WAVES,
                "cost": _core.CASTLE_SHIELD_COST,
                "damage_reduction": _core.CASTLE_SHIELD_DAMAGE_REDUCTION,
                "hp_ratio": _core.CASTLE_SHIELD_HP_RATIO,
                "regen_delay_frames": _core.CASTLE_SHIELD_REGEN_DELAY,
                "regen_rate_per_frame": _core.CASTLE_SHIELD_REGEN_RATE,
                "color_blue": _hex(_core.CASTLE_SHIELD_COLOR_BLUE, "#64c8ff"),
                "color_red": _hex(_core.CASTLE_SHIELD_COLOR_RED, "#ff7878"),
            },
        }
        write_json("nexus.json", out)
    except Exception as e:
        print(f"[convert] nexus failed: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()


def export_economy():
    """Konstanta ekonomi + wave — dibaca GameManager.gd (paritas _core.py)."""
    try:
        import _core
        minions = {}
        for k, v in _core.MINION_TYPES.items():
            d = dict(v)
            if "color" in d:
                d["color"] = _hex(d["color"], "#c8c8c8")
            minions[k] = d
        out = {
            "starting_gold": _core.STARTING_GOLD,
            "gold_per_second": _core.GOLD_PER_SECOND,
            "gold_per_second_level_bonus": _core.GOLD_PER_SECOND_LEVEL_BONUS,
            "gold_per_level_bonus": _core.GOLD_PER_LEVEL_BONUS,
            "difficulty_gold_mult": _core.DIFFICULTY_GOLD_MULT,
            "minion_wave_interval_frames": _core.MINION_WAVE_INTERVAL,
            "wave_composition": {str(k): list(v)
                                 for k, v in _core.NEXUS_WAVE_COMPOSITION.items()},
            "minion_types": minions,
        }
        write_json("economy.json", out)
    except Exception as e:
        print(f"[convert] economy failed: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()


def export_sounds():
    """Salin 24 file .wav assets/sounds/ -> godot/assets/sounds/.

    AudioManager.gd memuat dari res://assets/sounds/ — res:// tidak bisa
    keluar dari root project Godot, jadi aset harus diduplikasi. Folder
    tujuan sengaja di-gitignore (duplikat 15 MB; sumber kebenaran tetap
    assets/sounds/ pygame). Jalankan converter = audio siap dipakai.
    """
    import shutil
    src_dir = os.path.join(ROOT, "assets", "sounds")
    dst_dir = os.path.join(ROOT, "godot", "assets", "sounds")
    if not os.path.isdir(src_dir):
        print("[convert] sounds: assets/sounds/ tidak ada — dilewati", file=sys.stderr)
        return
    os.makedirs(dst_dir, exist_ok=True)
    copied = 0
    for fname in sorted(os.listdir(src_dir)):
        src = os.path.join(src_dir, fname)
        dst = os.path.join(dst_dir, fname)
        if os.path.isfile(src) and fname.lower().endswith((".wav", ".txt", ".ogg")):
            shutil.copy2(src, dst)
            copied += 1
    print(f"[convert] sounds: {copied} file -> {dst_dir}")


if __name__ == "__main__":
    export_heroes()
    export_bosses()
    export_levels()
    export_archetypes()
    export_items()
    export_items_meta()
    export_hero_levels()
    export_towers()
    export_nexus()
    export_economy()
    export_sounds()
    print("[convert] Done. Copy godot/data/*.json ke Godot res://data/")
