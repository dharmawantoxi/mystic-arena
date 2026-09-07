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


def _bake_unit_frames(hero_type, renderer, stats):
    """Render daftar (rect, canvas) untuk idle/walk/attack.

    Return (frames, info). frames = list (rect, surface-crop). Setiap
    elemen SUDAH dicrop ke bbox masing-masing; perataan anchor (kaki)
    dilakukan saat menyusun strip.
    """
    import pygame
    probe = _unit_probe(hero_type, stats)
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

    manifest = {}
    report = {"fail": [], "static_attack": [], "bytes": [],
              "opaque": [], "atk_diff": [], "manual": 0, "timer_sweep": 0}
    import time as _time
    t0 = _time.time()
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
                   "(heroes/__init__.py) — pose idle/walk/attack",
        "_note": "Strip per unit: grid [idle 8 | walk 8 | attack 8] "
                 "frame seragam, 8 frame per baris (batas tekstur GPU "
                 "mobile), anchor = telapak kaki. Attack Godot di-drive "
                 "dari attack_progress (bukan playback). Skill pose belum "
                 "dibake (fase lanjutan); selama cast dipakai pose "
                 "attack terakhir + FX proyektil Godot.",
        "frame_counts": {"idle": UNIT_IDLE_FRAMES, "walk": UNIT_WALK_FRAMES,
                         "attack": UNIT_ATTACK_FRAMES},
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
