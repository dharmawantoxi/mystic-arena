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
    godot/data/themes.json            (54 palet tema map + dekor; dibaca ArenaMap.gd)

Butuh pygame (THEMES/HERO_TYPES hidup di modul yang meng-import pygame).
Jalankan tanpa display/audio:

    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
        /home/user/.venv-mystic/bin/python tools/convert_to_godot.py

(venv dibuat sekali: python3 -m venv ~/.venv-mystic &&
 ~/.venv-mystic/bin/pip install "pygame-ce==2.5.*")
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


# ════════════════════════════════════════════════════════════════════
#  TEMA MAP (map_components/themes.py -> godot/data/themes.json)
# ════════════════════════════════════════════════════════════════════
#
# ArenaMap.gd dulu hanya punya 4 palet hardcoded (forest/desert/ice/abyss)
# padahal levels.json memakai 54 nama tema, jadi level >= 3 semua jatuh ke
# fallback forest dan terlihat identik. pygame sendiri punya 54 palet di
# map_components/themes.py THEMES (get_theme -> THEMES.get(name, FOREST_THEME)),
# jadi sumber kebenaran warna sudah ada — tinggal diekspor.
#
# PENTING: palet pygame adalah tuple (r, g, b) 0-255. Godot 4 TIDAK bisa
# membaca tuple; Color("#rrggbb") yang bisa, jadi semua nilai di-hex-kan di
# sini (bukan di GDScript) supaya themes.json tetap data murni.
#
# Nama kunci pygame -> nama kunci ArenaMap.gd dipetakan persis seperti 4
# palet hardcoded yang sudah ada di ArenaMap (dicek ulang terhadap
# FOREST_THEME: radiant_grass_1 == grass_dark #1c3720, dst.), jadi hasil
# merge di Godot = palet yang sama, hanya lengkap 54 tema.
#
# Kunci yang TIDAK ada padanannya di pygame (tree/tree_light/stone = dekor
# pohon & batu khas renderer prosedural Godot, dan modulate/light/energy =
# konsep CanvasModulate + Light2D) diturunkan dari palet dengan aturan yang
# ditulis di _derive_theme_extras() supaya tetap konsisten antar tema.

## pygame key -> ArenaMap.gd key (23 warna palet, semua ada di 54 tema)
THEME_KEY_MAP = {
    "radiant_grass_1": "grass_dark",
    "radiant_grass_2": "grass_mid",
    "radiant_grass_3": "grass",
    "radiant_grass_4": "grass_light",
    "radiant_grass_high": "grass_high",
    "radiant_moss": "moss",
    "dire_earth_1": "earth_dark",
    "dire_earth_2": "earth",
    "dire_earth_3": "earth_light",
    "dire_earth_4": "earth_high",
    "dire_ash": "ash",
    "dire_burnt": "burnt",
    "path_stone_1": "path_border",
    "path_stone_2": "path",
    "path_stone_3": "path_light",
    "path_stone_4": "path_bright",
    "path_moss": "path_moss",
    "path_crack": "path_crack",
    "river_deep": "river_dark",
    "river_mid": "river",
    "river_light": "river_light",
    "river_glow": "river_glow",
    "river_foam": "river_foam",
}

def _fog_from_theme(t, out):
    """fog_enabled / fog_color / fog_count pygame -> kunci Godot.

    pygame menyimpan kabut sebagai daftar elips semi-transparan
    (DynamicRenderer._init_fog map_components/_bundle.py:5424-5447 dan
    _draw_fog :5542-5560): fog_color adalah tuple RGBA 0-255 di mana ALPHA
    (elemen ke-4) yang menentukan tebalnya, dan fog_count = jumlah gumpalan.

    Godot Color() dari string hanya menerima '#rrggbb' yang enak dibaca,
    jadi RGB dan alpha DIPISAH di sini: 'fog_color' hex + 'fog_alpha' float
    0..1. Kalau digabung jadi '#rrggbbaa', tiap pembaca di GDScript harus
    tahu urutan alpha Godot vs pygame — dipisah lebih sulit salah.

    Nilai default menyalin default pygame di kedua fungsi itu:
    fog_enabled True, fog_color (80,60,60,30), fog_count 15.
    """
    fog = t.get("fog_color", (80, 60, 60, 30))
    out["fog_enabled"] = bool(t.get("fog_enabled", True))
    out["fog_color"] = _hex(fog, "#503c3c")
    alpha = fog[3] if isinstance(fog, (tuple, list)) and len(fog) > 3 else 30
    out["fog_alpha"] = round(float(alpha) / 255.0, 4)
    out["fog_count"] = int(t.get("fog_count", 15))


## Flag dekorasi yang dipakai ArenaMap._build_decor/_draw_decor untuk memilih
## jenis dekor per tema (pohon / batu / kristal / nisan). pygame memakainya
## di DecorationRenderer; di Godot hanya 4 jenis yang digambar prosedural.
THEME_DECOR_FLAGS = [
    "has_dark_trees", "has_dead_trees", "has_gravestones", "has_bones",
    "has_crystals_blue", "has_crystals_red", "has_ice_crystals",
    "has_rocks_mossy", "has_torch_stones",
]


def _mix(c, amount):
    """Campur warna (r,g,b) ke arah putih (amount>0) atau hitam (amount<0).

    amount 0.10 = 10% lebih terang. Dipakai untuk menurunkan warna dekor dari
    palet pygame (pygame tidak punya warna pohon/batu per tema).
    """
    out = []
    for ch in c[:3]:
        v = float(ch)
        v = v + (255.0 - v) * amount if amount >= 0 else v * (1.0 + amount)
        out.append(int(max(0.0, min(255.0, round(v)))))
    return tuple(out)


def _lum(c):
    """Luminance perseptual 0..1 (ITU-R BT.601) — untuk energi DirectionalLight2D."""
    return (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255.0


def _derive_theme_extras(t, out):
    """Isi kunci khas Godot yang tidak ada di palet pygame.

    ArenaMap.gd menggambar fallback prosedural (pohon/batu) + memakai
    CanvasModulate & DirectionalLight2D, tiga hal yang di pygame dikerjakan
    DecorationRenderer/fog/ambient_tint. Aturannya:

      tree       = radiant_grass_1 digelapkan 10%  (kanopi selalu lebih gelap
                   dari rumput sekitarnya — sama seperti 4 palet hardcoded)
      tree_light = radiant_moss                    (highlight kanopi)
      stone      = path_stone_2 diterangkan 8%     (batu dekor ~= batu jalur)
      light      = rona rata-rata palet, dinormalisasi lalu 45% ke arah putih
      energy     = 0.55 + 0.75 * luminance palet terang (map salju/neraka
                   punya pencahayaan berbeda, bukan cuma warna berbeda)
      modulate   = ambient_tint pygame (alpha kecil -> pergeseran halus)
    """
    grass1 = t["radiant_grass_1"]
    out["tree"] = _hex(_mix(grass1, -0.10), "#19371e")
    out["tree_light"] = _hex(t["radiant_moss"], "#2d5a32")
    out["stone"] = _hex(_mix(t["path_stone_2"], 0.08), "#555046")

    # ── DirectionalLight2D: rona + energi dari palet ──
    samples = [t["radiant_grass_3"], t["radiant_grass_4"], t["dire_earth_3"],
               t["path_stone_3"], t["river_glow"]]
    avg = tuple(sum(s[i] for s in samples) / len(samples) for i in range(3))
    peak = max(1.0, float(max(avg)))
    norm = tuple(v / peak for v in avg)
    light = tuple(1.0 - (1.0 - v) * 0.45 for v in norm)   # 45% ke arah putih
    bright = max(_lum(t["radiant_grass_3"]), _lum(t["radiant_grass_4"]))
    out["light"] = "#%02x%02x%02x" % tuple(
        int(round(v * 255.0)) for v in light)
    out["energy"] = round(max(0.55, min(1.25, 0.55 + 0.75 * bright)), 3)

    # ── CanvasModulate: ambient_tint pygame (None = tanpa semburat) ──
    tint = t.get("ambient_tint")
    mod = [255, 255, 255]
    if isinstance(tint, (tuple, list)) and len(tint) >= 4:
        # alpha pygame 15-25/255 = semburat halus; diperkuat 3x supaya di
        # Godot (yang tidak punya lapisan fog per tema) tetap terasa bedanya.
        a = min(0.35, (float(tint[3]) / 255.0) * 3.0)
        mod = [int(round(255.0 - (255.0 - float(tint[i])) * a)) for i in range(3)]
    out["modulate"] = "#%02x%02x%02x" % (mod[0], mod[1], mod[2])


def export_themes():
    """54 palet tema map_components/themes.py -> godot/data/themes.json.

    Dibaca ArenaMap._ready(): palet ini di-merge ke const THEMES, jadi 54
    level punya warna sendiri-sendiri (sebelumnya cuma 4).

    Butuh pygame karena THEMES hidup di modul yang meng-import pygame;
    jalankan dengan SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy supaya tidak
    butuh display/perangkat audio:
        SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
            /home/user/.venv-mystic/bin/python tools/convert_to_godot.py
    """
    try:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        # _core di-import LEBIH DULU: dialah yang memasang modul alias
        # "settings" di sys.modules (_core.py:1283-1287); tanpa itu
        # map_components/_bundle.py gagal `from settings import SCREEN_WIDTH`.
        import _core  # noqa: F401  (efek samping: alias settings)
        import pygame  # noqa: F401  (dipakai _bundle saat modul dimuat)
        from map_components import _bundle as mc

        themes_out = {}
        missing = []
        for name, t in mc.THEMES.items():
            entry = {"name": str(t.get("name", name))}
            for src, dst in THEME_KEY_MAP.items():
                if src in t:
                    entry[dst] = _hex(t[src], "#345c37")
                else:
                    missing.append("%s.%s" % (name, src))
            for flag in THEME_DECOR_FLAGS:
                entry[flag] = bool(t.get(flag, False))
            # particle_type: jenis partikel atmosfer (firefly/snow/sand/
            # ember/ash/spirit/mist/acid). Dipakai ArenaMap._apply_weather()
            # untuk memilih arah gerak partikel, bukan cuma warnanya.
            entry["particle_type"] = str(t.get("particle_type", "ash"))
            entry["particle_count"] = int(t.get("particle_count", 40))
            _fog_from_theme(t, entry)
            _derive_theme_extras(t, entry)
            themes_out[name] = entry

        out = {
            "_generated_by": "tools/convert_to_godot.py export_themes()",
            "_source": "map_components/themes.py THEMES (pygame, %d tema)"
                       % len(mc.THEMES),
            "_note": "Nilai warna '#rrggbb' (Color() Godot). Kunci tanpa "
                     "padanan pygame (tree/tree_light/stone/light/energy/"
                     "modulate) diturunkan — lihat _derive_theme_extras(). "
                     "fog_color dipisah jadi hex + fog_alpha 0..1 "
                     "(pygame menyimpan RGBA 0-255).",
            "fallback": "forest",
            "themes": themes_out,
        }
        write_json("themes.json", out)
        print("[convert] themes: %d tema (%s ... %s)"
              % (len(themes_out), next(iter(themes_out)),
                 next(reversed(themes_out))))
        if missing:
            print("[convert] themes: %d kunci pygame hilang (pakai default): %s"
                  % (len(missing), ", ".join(missing[:5])), file=sys.stderr)
    except Exception as e:
        # themes.json lama TIDAK dihapus: ArenaMap tetap jalan dengan 4 palet
        # const THEMES, sama seperti sebelum fitur ini ada.
        print(f"[convert] themes failed: {e}", file=sys.stderr)
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


# ═══════════════════════════════════════════════════════════════════
# FASE 5 (Opsi A) — BAKE STRIP PNG PER UNIT DARI RENDERER PYGAME
# ═══════════════════════════════════════════════════════════════════
#
# Mengapa bake PNG, bukan port renderer prosedural per-hero ke GDScript?
#   1. Skala: 216 renderer boss (bosses/level1..54.py) + 6 hero masterwork
#      (heroes/_bundle.py 16.723 baris) adalah ~ratusan ribu baris kode
#      gambar. Port 1:1 ke GDScript butuh berbulan-bulan dan tidak bisa
#      diverifikasi paritas tanpa me-render keduanya. Bake memakai
#      RENDERER ASLI sebagai sumber kebenaran — geometri/warna/pose
#      identik karena melewati choke point yang sama dengan cache sprite
#      game (_call_renderer_on_canvas heroes/__init__.py:1729, termasuk
#      _park_renderer_fx :1671 yang memark proyektil renderer).
#   2. Struktur Godot yang ada memang data-driven: RendererRegistry.gd
#      memetakkan unit_type -> PackedScene, jadi cukup SATU scene generik
#      BakedSprite.tscn + manifest JSON; tidak perlu 222 file .tres.
#
# Rekam jejak pose (semua sitasi = sumber pygame):
#   * idle/walk : fase = int(pulse*2.0) % 8 (HERO_ANIM_PHASES = 8,
#      heroes/__init__.py:1483; kunci cache idle heroes/__init__.py:1777-
#      1781). Hero menambah pulse 0.05/frame (_entity.py:1681) -> fase
#      baru tiap 10 frame = 6 fps; boss 0.1/frame (base_boss.py:580) ->
#      5 frame/fase = 12 fps. Keduanya disimpan di manifest, Godot
#      memilih sesuai jenis node.
#   * walk      : _detect_moving membandingkan delta posisi > 0.3 px
#      (bosses/level1.py:947-962) — probe digeser 1.4 px antar frame.
#   * attack    : pose serang dijalankan lewat MODE MANUAL yang memang
#      disediakan untuk alat preview/tes: set _<prefix>_attack_active
#      = True + _<prefix>_attack_progress = p dengan timer 0, controller
#      menghormati nilai pemanggil (bosses/level1.py:873-880 deteksi
#      manual, :892-898 "Alat preview / tes menggerakkan ... jangan
#      dilawan"). Unit tanpa controller pose-nya murni fungsi timer —
#      jendela serang `timer > attack_cooldown - 15` (bosses/level1.py:
#      983-985) di-sweep langsung.
#   * beam      : morgath melewatkan pass beam (_skip_beam) sama seperti
#      jalur cache hero (heroes/__init__.py:2149-2151, _BEAM_PASS_HEROES
#      :607) supaya beam jarak jauh tidak ikut membeku di strip.
#
# Output:
#   godot/assets/units/<type>.png   strip horizontal idle|walk|attack
#   godot/data/baked_units.json     manifest (frame, anchor, skala, fps)
#
# Determinisme: random di-seed per frame; dt controller ter-jepit 1/60
# (bosses/level1.py:824-826) untuk panggilan cepat beruntun, jadi dua
# kali bake menghasilkan PNG identik (diverifikasi lewat hash).

UNIT_CANVAS = 512          # kanvas bake; crop bbox dipakai untuk strip
UNIT_SEED = 20260907       # seed deterministik bake
UNIT_IDLE_FRAMES = 8       # = HERO_ANIM_PHASES (heroes/__init__.py:1483)
UNIT_WALK_FRAMES = 8       # kuantisasi sama dengan idle (kunci :1777)
UNIT_ATTACK_FRAMES = 8     # > HERO_ATK_QUANT 4 (:1496) -> lebih halus,
                           # tapi pose tetap dari kurva timeline yang sama
UNIT_SKILL_FRAMES = 6      # sampel timeline per skill q/w/e/r (Fase 5c).
                           # = HERO_SKILL_QUANT (:1497): game sendiri hanya
                           # menunjukkan pose skill baru tiap 6 frame,
                           # jadi 6 sampel menangkap ketukan visual yang
                           # sama (awal/akhir + transisi) tanpa strip
                           # raksasa (skill 240 frame -> 40 frame kalau
                           # di-sweep per kuantum).
# Padding antar sel di strip. Shader outline Godot (BakedSprite.tscn)
# sampling 4 tetangga ±1 px untuk garis tepi; tanpa padding, sampling di
# tepi sel bisa menyentuh frame SEBELAHNYA di strip (AtlasTexture satu
# tekstur besar) dan menghasilkan artefak garis. 2 px cukup untuk
# outline_width 1.0 + anti-blur import.
UNIT_CELL_PAD = 2
# Frame per baris strip. 24 frame berjajar = sampai 6.648 px lebar
# (akiraze) — melewati batas tekstur 4096 px GPU mobile low-end, lihat
# docs/PERF_ANDROID_LOWEND.md. Dibungkus 8 frame per baris, lebar
# maksimum turun ke ~2,2 ribu px (aman) dan tinggi cuma 3 baris.
UNIT_FRAMES_PER_ROW = 8


def _unit_probe(hero_type, stats):
    """Entity probe + stat asli dari boss_data (radius/range/cooldown)."""
    from heroes import _ProbeEntity, _adapt_hero_to_boss
    probe = _ProbeEntity(hero_type, UNIT_CANVAS // 2, UNIT_CANVAS // 2)
    if stats:
        # Stat asli supaya proporsi rig (jangkauan ayunan, ukuran)
        # sama dengan yang digambar game — _ProbeEntity cuma default.
        probe.radius = int(stats.get("radius", probe.radius))
        probe.range = int(stats.get("range", probe.range))
        probe.attack_cooldown = max(2, int(stats.get(
            "attack_cooldown", probe.attack_cooldown)))
        probe.speed = float(stats.get("speed", probe.speed))
        probe.damage = int(stats.get("damage", probe.damage))
    probe.boss_class = str(stats.get("boss_class", "mini")) if stats else "mini"
    probe.facing = 1
    probe.direction = 1
    _adapt_hero_to_boss(probe)
    return probe


def _render_unit_frame(renderer, probe):
    """Satu render ke canvas SRCALPHA, lalu crop bbox (alpha>=8).

    Crop mengikuti _blit_scaled (heroes/__init__.py:2282) dan
    _measure_native_size (:1393): min_alpha=8 membuang area kosong
    tanpa memotong tinta lembut.
    """
    import pygame
    import random
    random.seed(UNIT_SEED)
    c = UNIT_CANVAS // 2
    canvas = pygame.Surface((UNIT_CANVAS, UNIT_CANVAS), pygame.SRCALPHA)
    probe.x = probe.y = c
    probe._render_scale = 1.0
    from heroes import _call_renderer_on_canvas, _BEAM_PASS_HEROES
    # Beam morgath TIDAK ikut strip — di pygame digambar live tiap frame
    # pada skala 1.0 (heroes/__init__.py:2149-2151). Godot menirunya
    # lewat TowerBullet/SkillProjectile, bukan sprite badan.
    probe._skip_beam = probe.hero_type in _BEAM_PASS_HEROES
    try:
        _call_renderer_on_canvas(renderer, canvas, probe, c, c)
    finally:
        probe._skip_beam = False
    return canvas.get_bounding_rect(min_alpha=8), canvas


def _find_attack_attrs(probe):
    """Cari pasangan atribut pose serang manual (mode preview/tes).

    Controller menulis _<prefix>_attack_progress (mis. _gnk_, _ab_,
    _kz_) — bosses/level1.py:800-804. Ambil nama terpanjang supaya
    bentuk umum `_attack_progress` kalah dari yang spesifik.
    """
    names = [n for n in vars(probe)
             if n.endswith("_attack_progress") and n != "_attack_raw"]
    if not names:
        return None, None
    prog = max(names, key=len)
    act = prog[:-len("progress")] + "active"
    return prog, act


def _bake_unit_frames(hero_type, renderer, stats, setup=None):
    """Render daftar (rect, canvas) untuk idle/walk/attack.

    Return (frames, info). frames = list (rect, surface-crop). Setiap
    elemen SUDAH dicrop ke bbox masing-masing; perataan anchor (kaki)
    dilakukan saat menyusun strip.

    setup(probe) opsional (Fase 5c): dipanggil sekali setelah probe
    lahir untuk menyalakan flag varian (mis. rage_active=True untuk
    strip rage). Default None = perilaku Fase 5, byte strip dasar
    tidak berubah.
    """
    import pygame
    probe = _unit_probe(hero_type, stats)
    if setup is not None:
        setup(probe)
    frames = []

    # ── IDLE: pulse dirata-rata 8 fase (int(pulse*2)%8, :1777) ──
    for k in range(UNIT_IDLE_FRAMES):
        probe.pulse = (k + 0.5) / 2.0
        probe.timer = 0
        probe.attack_timer = 0
        probe.active_skill = None
        probe.active_skill_timer = 0
        # Frame pertama double-render: panggilan pertama memasang
        # baseline _detect_moving (bosses/level1.py:950-954) sehingga
        # frame berikut benar-benar "tidak bergerak".
        _render_unit_frame(renderer, probe)
        rect, canvas = _render_unit_frame(renderer, probe)
        frames.append(("idle", rect, canvas.subsurface(rect)))

    # ── WALK: probe digeser 1.4 px per frame (> ambang 0.3 px, :958) ──
    for k in range(UNIT_WALK_FRAMES):
        probe.pulse = (k + 0.5) / 2.0
        probe.timer = 0
        probe.attack_timer = 0
        probe.active_skill = None
        probe.active_skill_timer = 0
        probe.x = UNIT_CANVAS // 2 + 1 + k * 1.4
        probe.y = UNIT_CANVAS // 2
        rect, canvas = _render_unit_frame(renderer, probe)
        frames.append(("walk", rect, canvas.subsurface(rect)))

    # ── ATTACK: mode manual preview (bosses/level1.py:873-898) ──
    prog_attr, act_attr = None, None
    probe.x = probe.y = UNIT_CANVAS // 2
    probe.pulse = 1.0
    # Warm-up: panggilan pertama membuat atribut controller lahir
    # (_gnk_previous_timer dsb.) sehingga _find_attack_attrs bisa melihat
    # pasangan progress/active milik unit ini.
    _render_unit_frame(renderer, probe)
    prog_attr, act_attr = _find_attack_attrs(probe)
    for k in range(UNIT_ATTACK_FRAMES):
        p = (k + 0.5) / float(UNIT_ATTACK_FRAMES)
        probe.timer = 0
        probe.attack_timer = 0
        probe.active_skill = None
        probe.active_skill_timer = 0
        if prog_attr is not None:
            # Mode manual: timer 0 + active + progress>0 -> controller
            # menghormati nilai pemanggil (bosses/level1.py:873-880).
            setattr(probe, act_attr, True)
            setattr(probe, prog_attr, p)
        else:
            # Tanpa controller: pose murni fungsi timer — sweep jendela
            # serang `timer > cooldown-15` (bosses/level1.py:983-985).
            cd = int(probe.attack_cooldown)
            probe.timer = max(1, int(round(cd - 14 + 13.999 * p)))
            probe.attack_timer = probe.timer
        rect, canvas = _render_unit_frame(renderer, probe)
        frames.append(("attack", rect, canvas.subsurface(rect)))
    return frames, {"prog_attr": prog_attr}


def _compose_strip(hero_type, frames):
    """Susun crop ber-anchor kaki menjadi strip (8 frame per baris).

    Anchor = titik (c, c) kanvas bake (telapak kaki). Tiap crop
    diletakkan di sel seragam sehingga SEMUA frame punya anchor sel
    yang sama — AnimatedSprite2D hanya punya satu offset untuk semua
    frame, jadi perataan ini wajib dilakukan saat bake, bukan runtime.

    Multi-baris (UNIT_FRAMES_PER_ROW): satu baris 24 frame melebihi
    4096 px untuk unit besar; GPU mobile low-end bisa menolak tekstur
    sebesar itu. Indeks frame global (dipakai manifest) = urutan
    raster: baris * UNIT_FRAMES_PER_ROW + kolom.
    """
    import pygame
    c = UNIT_CANVAS // 2
    left_pad = max(c - r.x for _, r, _ in frames)
    right_pad = max(r.right - c for _, r, _ in frames)
    top_pad = max(c - r.y for _, r, _ in frames)
    bottom_pad = max(r.bottom - c for _, r, _ in frames)
    cell_w = max(1, left_pad + right_pad) + UNIT_CELL_PAD * 2
    cell_h = max(1, top_pad + bottom_pad) + UNIT_CELL_PAD * 2
    rows = (len(frames) + UNIT_FRAMES_PER_ROW - 1) // UNIT_FRAMES_PER_ROW
    strip = pygame.Surface((cell_w * UNIT_FRAMES_PER_ROW, cell_h * rows),
                           pygame.SRCALPHA)
    for i, (_, rect, crop) in enumerate(frames):
        col = i % UNIT_FRAMES_PER_ROW
        row = i // UNIT_FRAMES_PER_ROW
        ox = col * cell_w + UNIT_CELL_PAD + (left_pad - (c - rect.x))
        oy = row * cell_h + UNIT_CELL_PAD + (top_pad - (c - rect.y))
        strip.blit(crop, (ox, oy))
    # Anchor sel = kaki + padding (offset Godot dipakai untuk ini).
    return strip, cell_w, cell_h, left_pad + UNIT_CELL_PAD, \
        top_pad + UNIT_CELL_PAD


def _frame_diff(a, b):
    """Rata selisih kecerahan per piksel (detektor pose beku).

    Dipakai gerbang kualitas: frame attack yang identik dengan idle
    berarti pose serang gagal dipicu (lihat laporan distribusi).
    """
    w = min(a.get_width(), b.get_width())
    h = min(a.get_height(), b.get_height())
    if w <= 0 or h <= 0:
        return 0.0
    step = 3
    total = n = 0
    for y in range(0, h, step):
        for x in range(0, w, step):
            ar, ag, ab, aa = a.get_at((x, y))
            br, bg, bb, ba = b.get_at((x, y))
            total += abs(ar - br) + abs(ag - bg) + abs(ab - bb)
            total += abs(aa - ba)
            n += 1
    return total / float(max(1, n * 4))


def _aligned_diff(rect_a, crop_a, rect_b, crop_b):
    """Rata selisih piksel pada UNION bbox yang selaras jangkar.

    Kenapa tidak memakai _frame_diff untuk gerbang skill/rage: _frame_diff
    membandingkan persegi min(w,h) dari SUDUT KIRI-ATAS kedua crop —
    dua crop beda ukuran = dua bagian badan yang BERBEDA (jangkar kaki
    tidak segaris). Akibat fatalnya: skill yang badannya identik tapi
    MENAMBAH FX di tepi bbox (lingkar tanah R, telegraf) justru terukur
    ~0 (tumpang-tindihnya = badan yang sama; FX-nya di luar min-h/w dan
    tidak ikut dibandingkan) lalu ter-DROP — Godot kehilangan visual
    skill itu sepenuhnya. Diukur saat pengembangan: 44 skill ke-drop
    oleh _frame_diff, mayoritas FX-tepi semacam ini.

    Di sini kedua crop dipetakan kembali ke koordinat KANVAS via rect
    (semua render bake memakai jangkar kaki yang sama di tengah kanvas
    512) lalu union-nya disampel; di luar crop = transparan. Ambang
    tetap 1.0 (satuan sama dengan _frame_diff: rata selisih kanal
    0..255 per piksel).

    Gerbang attack Fase 5 SENGAJA tetap memakai _frame_diff (semantik
    historisnya tidak diubah; pose serang menggerakkan badan DI DALAM
    bbox yang mirip sehingga tumpang-tindihnya valid).
    """
    ux0 = min(rect_a.x, rect_b.x)
    uy0 = min(rect_a.y, rect_b.y)
    ux1 = max(rect_a.x + rect_a.width, rect_b.x + rect_b.width)
    uy1 = max(rect_a.y + rect_a.height, rect_b.y + rect_b.height)
    if ux1 <= ux0 or uy1 <= uy0:
        return 0.0
    step = 3
    total = n = 0
    for y in range(uy0, uy1, step):
        for x in range(ux0, ux1, step):
            if rect_a.collidepoint(x, y):
                ar, ag, ab, aa = crop_a.get_at(
                    (x - rect_a.x, y - rect_a.y))
            else:
                ar = ag = ab = aa = 0
            if rect_b.collidepoint(x, y):
                br, bg, bb, ba = crop_b.get_at(
                    (x - rect_b.x, y - rect_b.y))
            else:
                br = bg = bb = ba = 0
            total += abs(ar - br) + abs(ag - bg) + abs(ab - bb)
            total += abs(aa - ba)
            n += 1
    return total / float(max(1, n * 4))


def _save_strip(strip, png_path):
    """Simpan strip PNG — 256 warna palet + alpha diperbaiki per entri.

    Kenapa palet (PNG8): strip RGBA penuh = 21 MB untuk 222 unit; palet
    256 warna memangkasnya ~4-5x TANPA mengubah piksel RGB yang terlihat
    (prosedural pygame per unit memakai jauh lebih sedikit dari 256
    warna). Jebakannya: kuantisasi FASTOCTREE RGBA membocorkan alpha
    samar (1..15) ke entri palet yang dipakai area pad transparan ->
    halo kotak samar di arena. Perbaikannya: entri palet dengan alpha
    < 16 dipaksa 0 (ambang sama dengan min_alpha=8 crop + guard, lihat
    _render_unit_frame); alpha 16..255 (aura lembut) tetap utuh.

    Pillow opsional: kalau tidak ada, fallback pygame.image.save penuh
    (file lebih besar tapi identik secara visual — bukan error).
    """
    import pygame
    try:
        from PIL import Image
        pil = Image.frombytes("RGBA", strip.get_size(),
                              pygame.image.tobytes(strip, "RGBA"))
        q = pil.quantize(colors=256, method=Image.FASTOCTREE)
        pal = bytearray(q.getpalette(rawmode="RGBA"))
        for i in range(len(pal) // 4):
            if pal[i * 4 + 3] < 16:
                pal[i * 4 + 3] = 0
        q.putpalette(bytes(pal), rawmode="RGBA")
        q.save(png_path, optimize=True)
    except ImportError:
        pygame.image.save(strip, png_path)


# ═══════════════════════════════════════════════════════════════════
# FASE 5c — POSE SKILL q/w/e/r + VARIAN RAGE (tutup 2 deviasi Fase 5)
# ═══════════════════════════════════════════════════════════════════
#
# 1. POSE SKILL. pygame meng-drive-nya via active_skill + countdown
#    active_skill_timer (di-tick Hero.update, kunci cache skill
#    heroes/__init__.py:1750-1766). Bake = sweep timer dari DURASI
#    CAST turun ke 1 (progress renderer 0->1 dihitung sendiri oleh
#    renderer via 1-timer/dur, mis. _NS_kaizen._skill_progress
#    heroes/_bundle.py:6807-6811).
#
#    Kenapa durasi CAST (sisi AI), bukan durasi RENDER (sisi namespace
#    _NS_* SKILL_VISUAL_DURATION)? Karena countdown game memakai angka
#    cast — renderer me-CLAMP progress ke 0..1 kalau angkanya beda.
#    Contoh nyata: Kaizen Q di-cast 60 frame (KaizenSkills.
#    SKILL_VISUAL_DURATION hero_skills/_bundle.py:3979) tapi renderer
#    memakai dur 39 (_NS_kaizen.SKILL_VISUAL_DURATION
#    heroes/_bundle.py:6140) — 21 frame pertama cast di pygame
#    MENAMPILKAN pose awal beku. Sweep durasi cast mereproduksi bingkai
#    game persis (termasuk beku awal itu); sweep durasi render malah
#    menunjukkan gerakan di jendela yang di pygame beku = divergensi.
#    Sumber durasi cast:
#      * 6 hero starter: <X>Skills.SKILL_VISUAL_DURATION
#        (hero_skills/_bundle.py:3751/3979/4171/4491/4730/4990),
#      * boss hero: BossHeroSkills._SKILL_REGISTRY :483 (66 boss) ->
#        nama method _cast_* -> AST `h.active_skill_timer = N`,
#      * sisanya: _fallback_cast :968 (timer 40 semua kunci).
#    Sweep per skill = UNIT_SKILL_FRAMES (6) sampel timer dur->1.
#
#    Flag buff yang DITETAPKAN oleh cast itu sendiri (mis. drakar Q
#    menyalakan rage_active 300 frame, hero_skills/_bundle.py:1119-1122)
#    ikut dipasang di probe saat bake skill itu — di game flag-nya
#    memang menyala selama cast (renderer drakar menggambar glow rage
#    bosses/level1.py:7714 hanya kalau flag menyala). Flag dibaca dari
#    AST method cast yang sama (rage_active/defense_boost = True).
#
#    Unit berlapisan hidup (heroes/*_fx.py) TIDAK diperlakukan khusus:
#    bake memanggil renderer lewat choke point cache yang sama
#    (_call_renderer_on_canvas) sehingga yang terekam = mode fallback
#    canvas-nya saja, persis seperti strip dasar Fase 5. Lapisan hidup
#    60fps tetap urusan SkillProjectile/FX Godot (Fase 5b).
#
# 2. VARIAN RAGE ("bentuk elite"). Penyelidikan atribut pemicu (semua
#    getattr non-underscore di bosses/level*.py + heroes/_bundle.py):
#      * `_draw_*_elite` BUKAN varian level — itu nama rig masterwork
#        yang SELALU dipakai (mis. _draw_grimjaw_body mendelegasikan
#        ke _draw_grimjaw_elite, heroes/_bundle.py:1405-1411).
#      * `level`/`boss_class` TIDAK DIBACA renderer mana pun (hanya
#        jadi kunci cache defensif heroes/__init__.py:1752/:2629; dan
#        MINI vs TRUE tidak bertindih — tiap tipe satu kelas).
#      * `cataclysm_form`, `current_element`, `tough_shield_active`
#        TIDAK PERNAH di-set di mana pun (hanya getattr default) =
#        jalur mati; vulkareth cataclysm tetap kena bake lewat skill R
#        (level25.py:3155-3157: is_cataclysm = skill r ATAU flag).
#      * `is_enraged` hanya mengganti NAMA state RUN vs WALK di level5
#        (:542/:2092/:3689); pose bake-nya tetap "walk" (diukur: diff
#        maks 0.31 < gerbang 1.0 -> tidak dibake).
#      * `ability_active` dipetakan ke pose skill 'q' (level5.py:506) =
#        tercakup bake skill.
#    Yang TERSISA dan lolos gerbang empiris (diff >= 1.0, ambang sama
#    dengan WARNING atk Fase 5): drakar + rage_active (badan rage_mode
#    + glow merah, bosses/level1.py:7638/7714; buff Q 300 frame
#    _cast_q_battle_hunger bosses/base_boss.py:2905-2912 — JAUH lebih
#    lama dari visual cast 90 frame, jadi varian terpisah memang
#    dibutuhkan). Alchemist rage (mata + uap asam) & drakar
#    defense_boost (4 dot orbit) diukur sub-ambang -> tidak dibake,
#    dicatat di README sebagai residu.
#    Strip rage = layout SAMA dengan strip dasar ([idle 8|walk 8|
#    attack 8]) supaya BakedSprite.gd tinggal mengganti nama anim
#    (rage_idle/...) tanpa logika indeks baru.
#
# Output (semua ADDITIF — 222 PNG Fase 5 tidak diubah):
#   godot/assets/units/<type>.skill.png  strip skill (hanya skill yang
#                                        lolos gerbang; 6 frame/skill)
#   godot/assets/units/<type>.rage.png   strip rage (hanya unit yang
#                                        lolos gerbang rage)
#   godot/data/baked_units.json          skema 2 (kunci baru opsional,
#                                        pembaca skema 1 mengabaikannya)
#
# Renderer pygame yang RUSAK di jalur skill (terbukti lewat bake):
#   * sasori E: NameError `random` (bosses/level54.py:3278 — modul
#     tidak mengimpor random). Di game jatuh ke _draw_generic_hero
#     (heroes/__init__.py:2109-2156: _hero_render_sprite menangkap
#     SEMUA exception renderer).
#   * vex Q: IndexError pts[i+1] (heroes/_bundle.py:13231-13238: loop
#     6 di atas list 6 elemen) — sama, jatuh ke hero generik.
#   Keduanya TIDAK dibake (Godot memakai fallback pose attack, sesuai
#   kontrak lama README) dan dilaporkan di ringkasan + README.


def _parse_cast_method(src_tree, method_name):
    """Intip method _cast_* hero_skills: (timer, flags, buff_dur).

    timer = N dari `h.active_skill_timer = N` (int harfiah) atau
    ("defer", kunci) dari `self._set_active_skill(kunci[, N])` yang
    nanti diselesaikan via BOSS_HERO_VISUAL_DURATION/default.
    flags = {"rage_active": True, ...} dari assignment True harfiah
    (buff yang menyala selama cast — ikut dipasang di probe bake).
    buff_dur = {"rage": N} dari `h.rage_timer = N` (durasi buff untuk
    manifest -> Godot is_raging()).
    Return None kalau method tidak ketemu (pemanggil memakai fallback).
    """
    import ast as _ast
    target = None
    for node in _ast.walk(src_tree):
        if isinstance(node, _ast.FunctionDef) and node.name == method_name:
            target = node
            break
    if target is None:
        return None
    timer = None
    flags = {}
    buff_dur = {}
    for node in _ast.walk(target):
        if isinstance(node, _ast.Assign):
            for t in node.targets:
                if not isinstance(t, _ast.Attribute):
                    continue
                if t.attr == "active_skill_timer" and timer is None \
                        and isinstance(node.value, _ast.Constant) \
                        and isinstance(node.value.value, int):
                    timer = int(node.value.value)
                elif t.attr in ("rage_active", "defense_boost") \
                        and isinstance(node.value, _ast.Constant) \
                        and node.value.value is True:
                    flags[t.attr] = True
                elif t.attr == "rage_timer" \
                        and isinstance(node.value, _ast.Constant) \
                        and isinstance(node.value.value, int):
                    buff_dur["rage"] = int(node.value.value)
                elif t.attr == "defense_timer" \
                        and isinstance(node.value, _ast.Constant) \
                        and isinstance(node.value.value, int):
                    buff_dur["defense"] = int(node.value.value)
        elif isinstance(node, _ast.Call) \
                and isinstance(node.func, _ast.Attribute) \
                and node.func.attr == "_set_active_skill" \
                and timer is None:
            args = node.args
            if len(args) >= 2 and isinstance(args[1], _ast.Constant) \
                    and isinstance(args[1].value, int):
                timer = int(args[1].value)
            elif len(args) >= 1 and isinstance(args[0], _ast.Constant):
                timer = ("defer", str(args[0].value))
    return timer, flags, buff_dur


def _skill_cast_table():
    """Tabel (durasi cast, flag buff) per (unit, kunci skill).

    Return (durs, cast_flags, rage_info):
      durs[unit][kunci]      = countdown frame di game (sumber sweep
                               bake + Godot _visual_duration),
      cast_flags[unit][kunci]= {"rage_active": True} dsb. (dipasang di
                               probe selama bake skill itu),
      rage_info[unit]        = {"skill": kunci, "duration": N} kalau
                               salah satu cast menyalakan rage (sumber
                               Godot is_raging; dipakai hanya kalau
                               strip rage lolos gerbang).
    """
    import ast as _ast
    from hero_skills import _bundle as _hsb
    with open(os.path.join(ROOT, "hero_skills", "_bundle.py"),
              encoding="utf-8") as f:
        tree = _ast.parse(f.read())
    boss_cls = _hsb._NS_boss_hero_skills.BossHeroSkills
    registry = boss_cls._SKILL_REGISTRY
    per_hero = boss_cls.BOSS_HERO_VISUAL_DURATION
    default = dict(_hsb.BaseSkill._DEFAULT_VISUAL_DURATION)
    starter = {
        "grimjaw": _hsb._NS_grimjaw_skills.GrimjawSkills.SKILL_VISUAL_DURATION,
        "kaizen": _hsb._NS_kaizen_skills.KaizenSkills.SKILL_VISUAL_DURATION,
        "sylara": _hsb._NS_sylara_skills.SylaraSkills.SKILL_VISUAL_DURATION,
        "thorne": _hsb._NS_thorne_skills.ThorneSkills.SKILL_VISUAL_DURATION,
        "vex": _hsb._NS_vex_skills.VexSkills.SKILL_VISUAL_DURATION,
        "zephyr": _hsb._NS_zephyr_skills.ZephyrSkills.SKILL_VISUAL_DURATION,
    }
    durs, cast_flags, rage_info = {}, {}, {}
    for unit in set(registry) | set(starter):
        durs[unit] = {}
        cast_flags[unit] = {}
        for key in "qwer":
            if unit in starter and starter[unit].get(key):
                # 6 hero starter: durasi kelas skill-nya sendiri.
                durs[unit][key] = int(starter[unit][key])
                continue
            method = registry.get(unit, {}).get(key)
            parsed = _parse_cast_method(tree, method) if method else None
            if parsed is None:
                # Boss tanpa recipe: _fallback_cast (timer 40 semua
                # kunci, hero_skills/_bundle.py:968).
                durs[unit][key] = 40
                continue
            timer, flags, buff = parsed
            if isinstance(timer, tuple):
                # _set_active_skill(kunci) tanpa N: presedensi =
                # override per-hero -> default (BossHeroSkills.
                # _get_visual_duration, hero_skills/_bundle.py:473-482).
                timer = per_hero.get(unit, {}).get(key,
                                                   default.get(key, 60))
            durs[unit][key] = max(2, int(timer or 40))
            if flags:
                cast_flags[unit][key] = dict(flags)
            if flags.get("rage_active") and buff.get("rage"):
                rage_info[unit] = {"skill": key,
                                   "duration": int(buff["rage"])}
    # Unit di luar registry + starter (150 boss): fallback 40.
    return durs, cast_flags, rage_info, dict(default)


# Jam virtual bake (determinisme hash PNG).
#
# Beberapa renderer membaca JAM DINDING absolut:
#   * mulut emberwick: mouth_open = f(get_ticks()) saat attack
#     (bosses/level41.py:476) — tiap run dapat nilai 0..3 berbeda
#     (cabang line-vs-polygon!), terukur 4 hash berbeda;
#   * controller thalgryn: dt = get_ticks()-terakhir
#     (bosses/thalgryn_v4.py:1019-1031; pola sama di level1.py:817
#     untuk gornak dkk.) — render yang mengangkangi batas milidetik
#     memakai dt terukur, yang tidak memakai 1/60.
# Tanpa jam beku, byte PNG unit-unit ini BERBEDA setiap run.
#
# Perbaikannya DARI SISI BAKE (bosses/*.py tidak boleh diubah) dengan
# meniru pola RESMI game: probe paritas sprite-nya sendiri membekukan
# get_ticks() ke tick virtual selama render referensi
# (heroes/__init__.py:3085-3103, _PROBE_TICK) supaya "renderer
# ber-jam dinding dibandingkan secara adil". Bake memakai nilai yang
# SAMA (_PROBE_TICK) selama SELURUH ekspor — bukan per unit — supaya
# kebal terhadap SEMUA pembaca jam absolut, termasuk yang belum
# ditemukan. Controller dt-delta (gornak dkk.) selalu memakai cabang
# dt=1/60 — dt normal game — dan byte 220 unit lain terbukti tidak
# berubah (mereka memang selalu jatuh di cabang itu).
_VIRTUAL_CLOCK_SAVED = [None]


def _freeze_clock():
    """Bekukan pygame.time.get_ticks() -> _PROBE_TICK (lihat atas)."""
    import pygame.time as _pt
    if _VIRTUAL_CLOCK_SAVED[0] is None:
        try:
            from heroes import _PROBE_TICK as _vt
        except ImportError:
            _vt = 1000000
        _VIRTUAL_CLOCK_SAVED[0] = _pt.get_ticks
        _pt.get_ticks = lambda: _vt


def _thaw_clock():
    """Kembalikan get_ticks() asli."""
    import pygame.time as _pt
    if _VIRTUAL_CLOCK_SAVED[0] is not None:
        _pt.get_ticks = _VIRTUAL_CLOCK_SAVED[0]
        _VIRTUAL_CLOCK_SAVED[0] = None


def _bake_unit_idle_ref(renderer, stats, hero_type):
    """Satu frame idle (probe segar, pulse 1.0) sebagai acuan gerbang.

    Probe SEGAR per kondisi itu wajib: state controller (_detect_moving
    baseline, state FX) berdifusi antar render berurutan pada satu
    probe — survei Fase 5c mengukur hollowbane 23.2 untuk SEMUA flag
    sebelum diperbaiki (drift state, bukan efek flag). A/B yang valid
    = kondisi berbeda pada JEJAK state yang identik.
    """
    probe = _unit_probe(hero_type, stats)
    probe.pulse = 1.0
    probe.timer = 0
    probe.attack_timer = 0
    probe.active_skill = None
    probe.active_skill_timer = 0
    _render_unit_frame(renderer, probe)   # warm-up: controller lahir
    rect, canvas = _render_unit_frame(renderer, probe)
    return rect, canvas.subsurface(rect).copy()


def _bake_unit_skills(hero_type, renderer, stats, cast_table):
    """Bake pose skill q/w/e/r (probe segar per skill).

    Return (frames, kept, fail, diffs). frames = [(kunci, rect, crop)]
    HANYA untuk skill yang lolos gerbang (maks diff 6 frame vs idle
    >= 1.0 — ambang sama dengan WARNING atk Fase 5 — dan tanpa
    exception renderer). kept = [kunci...] urutan qwer; fail =
    [(kunci, pesan)] untuk laporan; diffs[kunci] = maks diff.
    """
    durs, cast_flags, _rage, _default = cast_table
    unit_durs = durs.get(hero_type, {})
    idle_rect, idle_crop = _bake_unit_idle_ref(renderer, stats, hero_type)
    frames, kept, fail, diffs = [], [], [], {}
    for key in "qwer":
        dur = max(2, int(unit_durs.get(key, 40)))
        flags = cast_flags.get(hero_type, {}).get(key, {})
        try:
            skill_frames = []
            for k in range(UNIT_SKILL_FRAMES):
                # Sweep countdown dur->1 (progress renderer 0->1);
                # probe SEGAR per FRAME supaya jejak controller tiap
                # sampel identik (difusi state = pose terkontaminasi
                # urutan bake, lihat _bake_unit_idle_ref).
                probe = _unit_probe(hero_type, stats)
                for fname in flags:
                    setattr(probe, fname, True)
                probe.pulse = 1.0   # pose murni fungsi timer skill,
                probe.timer = 0     # bukan pulse (preseden: bake
                probe.attack_timer = 0  # attack Fase 5 memakai 1.0)
                probe.active_skill = key
                probe.active_skill_timer = max(
                    1, int(round(dur - (dur - 1.0) * k
                               / float(UNIT_SKILL_FRAMES - 1))))
                _render_unit_frame(renderer, probe)   # warm-up
                for fname in flags:
                    setattr(probe, fname, True)
                probe.active_skill = key
                probe.active_skill_timer = max(
                    1, int(round(dur - (dur - 1.0) * k
                               / float(UNIT_SKILL_FRAMES - 1))))
                rect, canvas = _render_unit_frame(renderer, probe)
                crop = canvas.subsurface(rect).copy()
                skill_frames.append((key, rect, crop))
            best = max(_aligned_diff(rect, crop, idle_rect, idle_crop)
                       for _, rect, crop in skill_frames)
            diffs[key] = best
            if best < 1.0:
                # Pose statis (renderer tidak menggambar apa-apa untuk
                # kunci ini, mis. skill FX-nya 100% lapisan hidup) —
                # Godot memakai fallback pose attack (kontrak README).
                continue
            frames.extend(skill_frames)
            kept.append(key)
        except Exception as e:
            # Renderer rusak di jalur skill (sasori E / vex Q —
            # lihat catatan Fase 5c): di game jatuh ke hero generik,
            # di sini skill-nya absen -> fallback attack di Godot.
            fail.append((key, "%s: %s" % (type(e).__name__, e)))
    return frames, kept, fail, diffs


def export_unit_sprites(only=None):
    """Bake strip PNG 222 unit -> godot/assets/units/ + manifest JSON.

    Jalankan: SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
        ~/.venv-mystic/bin/python tools/convert_to_godot.py --units-png
    """
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    # _core DULU (aturan port): memasang alias modul "settings"
    # (_core.py:1283-1287) yang dibutuhkan map_components/_bundle.
    import _core  # noqa: F401
    import pygame
    pygame.init()
    pygame.display.set_mode((1, 1))
    import random
    from heroes import HERO_RENDERERS, BOSS_RENDERERS, _get_hero_scale
    from bosses.boss_data import MINI_BOSS_TYPES, TRUE_BOSS_TYPES

    stats_all = {}
    stats_all.update(MINI_BOSS_TYPES)
    stats_all.update(TRUE_BOSS_TYPES)

    # Semesta bake = renderer yang benar-benar terdaftar (6 hero
    # masterwork + 216 boss) — persis himpunan yang bisa digambar game.
    types = sorted(set(HERO_RENDERERS) | set(BOSS_RENDERERS))
    if only:
        types = [t for t in types if t in set(only)]

    out_dir = os.path.join(ROOT, "godot", "assets", "units")
    os.makedirs(out_dir, exist_ok=True)

    # Tabel durasi cast sisi-AI (Fase 5c): dibaca SEKALI per run —
    # AST hero_skills/_bundle.py + dict SKILL_VISUAL_DURATION.
    cast_table = _skill_cast_table()
    _cast_durs, _cast_flags, _rage_info, _cast_default = cast_table

    manifest = {}
    report = {"fail": [], "static_attack": [], "bytes": [],
              "opaque": [], "atk_diff": [], "manual": 0, "timer_sweep": 0,
              "skill_bytes": [], "skill_diff": [], "skill_kept": 0,
              "skill_drop": [], "skill_fail": [], "rage": []}
    import time as _time
    t0 = _time.time()
    # Jam virtual selama SELURUH ekspor (lihat catatan _freeze_clock):
    # semua render referensi melihat get_ticks() yang sama.
    _freeze_clock()
    try:
        _export_unit_sprites_frozen(types, stats_all, out_dir, cast_table,
                                    manifest, report, only, _time.time())
    finally:
        _thaw_clock()


def _export_unit_sprites_frozen(types, stats_all, out_dir, cast_table,
                                manifest, report, only, t0):
    """Badan loop bake per unit (dipanggil dengan jam virtual menyala)."""
    import pygame
    import random
    import time as _time
    from heroes import HERO_RENDERERS, BOSS_RENDERERS, _get_hero_scale
    _cast_durs, _cast_flags, _rage_info, _cast_default = cast_table
    for idx, t in enumerate(types):
        renderer = HERO_RENDERERS.get(t) or BOSS_RENDERERS.get(t)
        try:
            frames, info = _bake_unit_frames(t, renderer, stats_all.get(t))
            if not frames:
                raise RuntimeError("0 frame")
            strip, cw, ch, ax, ay = _compose_strip(t, frames)
            png = os.path.join(out_dir, t + ".png")
            _save_strip(strip, png)
            entry = {
                "png": "res://assets/units/%s.png" % t,
                "frame_w": cw,
                "frame_h": ch,
                # Grid 8 frame per baris (bukan 1 baris panjang) —
                # aman untuk batas tekstur GPU mobile 4096 px.
                "frames_per_row": UNIT_FRAMES_PER_ROW,
                "anchor": [ax, ay],
                # Skala tampilan per peran, paritas pygame: hero lane
                # di-scale _get_hero_scale (heroes/__init__.py:2148),
                # boss native 1.0 (heroes/__init__.py:2873-2878).
                "hero_scale": round(float(_get_hero_scale(t)), 4),
                "boss_scale": 1.0,
                # fps loop idle/walk: fase baru tiap 10 frame hero /
                # 5 frame boss (pulse 0.05 vs 0.1 — _entity.py:1681,
                # bosses/base_boss.py:580; kunci 8 fase :1777-1781).
                "fps_hero": 6,
                "fps_boss": 12,
                "anims": {
                    "idle":   [0, UNIT_IDLE_FRAMES],
                    "walk":   [UNIT_IDLE_FRAMES, UNIT_WALK_FRAMES],
                    "attack": [UNIT_IDLE_FRAMES + UNIT_WALK_FRAMES,
                               UNIT_ATTACK_FRAMES],
                },
                "boss_class": str(stats_all.get(t, {}).get(
                    "boss_class", "mini")),
                "renderer": "hero" if t in HERO_RENDERERS else "boss",
            }
            # ── Fase 5c: durasi cast SEMUA kunci (Godot butuh ini
            # untuk active_skill_timer walau pose-nya tidak kebake,
            # mis. vex Q: pose attack selama 40 frame).
            entry["skill_dur"] = {
                k: max(2, int(_cast_durs.get(t, {}).get(
                    k, _cast_default.get(k, 40)))) for k in "qwer"}

            # ── Fase 5c: strip skill (file TERPISAH supaya 222 PNG
            # Fase 5 tidak berubah hash-nya; geometri sendiri karena
            # FX skill (lingkar tanah R dsb.) melampaui bbox badan).
            sframes, kept, sfail, sdiffs = _bake_unit_skills(
                t, renderer, stats_all.get(t), cast_table)
            for key in "qwer":
                if key in sdiffs:
                    report["skill_diff"].append(sdiffs[key])
            report["skill_kept"] += len(kept)
            _failed_keys = [f[0] for f in sfail]
            report["skill_drop"].extend(
                "%s/%s" % (t, k) for k in "qwer"
                if k not in kept and k not in _failed_keys)
            report["skill_fail"].extend(
                "%s/%s(%s)" % (t, k, msg) for k, msg in sfail)
            if sframes:
                sstrip, scw, sch, sax, say = _compose_strip(t, sframes)
                spng = os.path.join(out_dir, t + ".skill.png")
                _save_strip(sstrip, spng)
                report["skill_bytes"].append(os.path.getsize(spng))
                anims = {}
                for i, key in enumerate(kept):
                    anims[key] = [i * UNIT_SKILL_FRAMES,
                                  UNIT_SKILL_FRAMES]
                entry["skills_png"] = "res://assets/units/%s.skill.png" % t
                entry["skill_frame_w"] = scw
                entry["skill_frame_h"] = sch
                entry["skill_frames_per_row"] = UNIT_FRAMES_PER_ROW
                entry["skill_anchor"] = [sax, say]
                entry["skill_anims"] = anims

            # ── Fase 5c: strip rage ("bentuk elite"). Varian penuh
            # 24 frame (layout = strip dasar) dengan rage_active=True;
            # gerbang: idle rage vs idle dasar >= 1.0 (kalau renderer
            # tidak membaca flag-nya, strip tidak ditulis).
            if t in _rage_info:
                _rprobe = _unit_probe(t, stats_all.get(t))
                _rprobe.pulse = 1.0
                _rprobe.rage_active = True
                _render_unit_frame(renderer, _rprobe)   # warm-up
                _rprobe.rage_active = True
                _rrect, _rcanvas = _render_unit_frame(renderer, _rprobe)
                _rcrop = _rcanvas.subsurface(_rrect).copy()
                _brect, _bcrop = _bake_unit_idle_ref(
                    renderer, stats_all.get(t), t)
                _rdiff = _aligned_diff(_rrect, _rcrop, _brect, _bcrop)
                if _rdiff >= 1.0:
                    def _rage_setup(p):
                        p.rage_active = True
                    rframes, _rinfo = _bake_unit_frames(
                        t, renderer, stats_all.get(t), setup=_rage_setup)
                    rstrip, rcw, rch, rax, ray = _compose_strip(t, rframes)
                    rpng = os.path.join(out_dir, t + ".rage.png")
                    _save_strip(rstrip, rpng)
                    entry["rage_png"] = \
                        "res://assets/units/%s.rage.png" % t
                    entry["rage_frame_w"] = rcw
                    entry["rage_frame_h"] = rch
                    entry["rage_frames_per_row"] = UNIT_FRAMES_PER_ROW
                    entry["rage_anchor"] = [rax, ray]
                    # Pemicu + durasi buff (Godot is_raging()).
                    entry["rage"] = dict(_rage_info[t])
                    report["rage"].append("%s(%.1f)" % (t, _rdiff))
            manifest[t] = entry

            # ── Gerbang kualitas (distribusi dicetak di ringkasan) ──
            report["bytes"].append(os.path.getsize(png))
            idle_surf = frames[0][2]
            atk_surf = frames[-1][2]
            report["atk_diff"].append(_frame_diff(idle_surf, atk_surf))
            if info["prog_attr"]:
                report["manual"] += 1
            else:
                report["timer_sweep"] += 1
            opaque = 0
            n = 0
            for y in range(0, idle_surf.get_height(), 3):
                for x in range(0, idle_surf.get_width(), 3):
                    opaque += 1 if idle_surf.get_at((x, y))[3] > 200 else 0
                    n += 1
            report["opaque"].append(100.0 * opaque / max(1, n))
        except Exception as e:
            report["fail"].append((t, "%s: %s" % (type(e).__name__, e)))
        if (idx + 1) % 40 == 0:
            print("[convert] units %d/%d (%.1fs)"
                  % (idx + 1, len(types), _time.time() - t0))

    total_kb = sum(report["bytes"]) / 1024.0
    print("[convert] units: %d strip OK, %d gagal, %.1f KB total (%.1fs)"
          % (len(manifest), len(report["fail"]), total_kb,
             _time.time() - t0))
    # Distribusi gerbang kualitas — cetak eksplisit supaya regresi
    # (strip kosong / pose beku / ukuran membengkak) terlihat saat PR.
    for key in ("bytes", "opaque", "atk_diff"):
        vals = sorted(report[key])
        if vals:
            print("[convert]   %s: min=%.1f p50=%.1f max=%.1f"
                  % (key, vals[0], vals[len(vals) // 2], vals[-1]))
    print("[convert]   attack pose: %d mode-manual, %d timer-sweep"
          % (report["manual"], report["timer_sweep"]))
    # Deteksi attack yang mirip idle (kemungkinan pose tidak terpicu).
    # report["atk_diff"] sejajar urutan `types` (iterasi yang sama dengan
    # pengisian di atas), bukan urutan kunci manifest.
    static_list = [t for t, d in zip(types, report["atk_diff"]) if d < 1.0]
    if static_list:
        print("[convert]   WARNING attack~idle (<1.0): %s"
              % ", ".join(static_list[:12]))
    if report["fail"]:
        print("[convert]   GAGAL: %s"
              % ", ".join("%s(%s)" % fv for fv in report["fail"][:12]),
              file=sys.stderr)
    # ── Ringkasan Fase 5c (gerbang skill + rage) ──
    svals = sorted(report["skill_diff"])
    skb = sum(report["skill_bytes"]) / 1024.0
    print("[convert] skills: %d pose kept, %d drop(statis), %d fail "
          "(%.1f KB strip skill)"
          % (report["skill_kept"], len(report["skill_drop"]),
             len(report["skill_fail"]), skb))
    if svals:
        print("[convert]   skill_diff: min=%.1f p50=%.1f max=%.1f"
              % (svals[0], svals[len(svals) // 2], svals[-1]))
    if report["skill_drop"]:
        print("[convert]   drop: %s"
              % ", ".join(report["skill_drop"][:16]))
    if report["skill_fail"]:
        print("[convert]   skill GAGAL (renderer rusak, fallback attack): "
              "%s" % ", ".join(report["skill_fail"][:16]))
    print("[convert] rage: %d strip (%s)"
          % (len(report["rage"]),
             ", ".join(report["rage"][:8]) if report["rage"] else "-"))

    if only:
        # Mode --only = kalibrasi/debug satu unit: JANGAN menimpa
        # manifest 222 unit dengan 4 entri (pernah terjadi — manifest
        # penuh harus dibake ulang). PNG tetap ditulis supaya bisa
        # dilihat, manifestnya tidak.
        print("[convert] units: mode --only — baked_units.json TIDAK "
              "ditulis ulang (manifest penuh dari run tanpa --only)")
        return
    out = {
        "_generated_by": "tools/convert_to_godot.py export_unit_sprites()",
        "_source": "renderer pygame via HERO_RENDERERS/BOSS_RENDERERS "
                   "(heroes/__init__.py) — pose idle/walk/attack + "
                   "skill q/w/e/r (Fase 5c) + varian rage",
        "_note": "Strip per unit: grid [idle 8 | walk 8 | attack 8] "
                 "frame seragam, 8 frame per baris (batas tekstur GPU "
                 "mobile), anchor = telapak kaki. Attack Godot di-drive "
                 "dari attack_progress (bukan playback). Skill: strip "
                 "terpisah <type>.skill.png (6 frame/pose, hanya pose "
                 "yang lolos gerbang diff>=1.0); skill_dur = countdown "
                 "cast sisi-AI (Godot active_skill_timer + fps playback). "
                 "Rage: strip <type>.rage.png + pemicu (hanya unit yang "
                 "lolos gerbang). Kunci Fase 5c opsional — pembaca "
                 "skema 1 mengabaikannya (backward-compatible).",
        "schema": 2,
        "frame_counts": {"idle": UNIT_IDLE_FRAMES, "walk": UNIT_WALK_FRAMES,
                         "attack": UNIT_ATTACK_FRAMES,
                         "skill": UNIT_SKILL_FRAMES},
        "units": manifest,
    }
    write_json("baked_units.json", out)


if __name__ == "__main__":
    _argv = sys.argv[1:]
    if "--units-png" in _argv:
        # Fase 5 Opsi A: bake strip PNG saja (data JSON tidak disentuh).
        _only = None
        if "--only" in _argv:
            _val = _argv[_argv.index("--only") + 1]
            _only = [s.strip() for s in _val.split(",") if s.strip()]
        export_unit_sprites(only=_only)
    else:
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
        export_themes()
        export_sounds()
        print("[convert] Done. Copy godot/data/*.json ke Godot res://data/")
