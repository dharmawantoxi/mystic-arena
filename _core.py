"""
_core.py - inti game (digabung dari 8 file)

  settings.py            level modul (nama-namanya dipakai semua)
  game.py
  menu.py
  game_input.py
  game_ui.py
  game_dev.py
  game_settings.py
  controller_manager.py

Alias modul lama (settings, game, menu, ...) didaftarkan ke
sys.modules di bagian bawah file ini, sehingga semua baris
`from game import Game`, `from settings import *` dll. di file
lain TETAP jalan tanpa perubahan.
"""
import pygame
import math
import random
_globals_before_settings = set(globals())


# ====================================================================
# settings.py
# ====================================================================

# settings.py
TOWER_VISUAL_SCALE = 0.7

# ═══════════════════════════════════════════════════════
# TOWER HP & DEFENSE SYSTEM
# ═══════════════════════════════════════════════════════

# HP Multiplier - increase base HP untuk semua tower
TOWER_HP_MULTIPLIER = 2.5  # 2.5x dari HP original

# Shield System
TOWER_SHIELD_ENABLED = True
TOWER_SHIELD_HP_RATIO = 0.4        # Shield = 40% dari max HP
TOWER_SHIELD_REGEN_DELAY = 180     # 3 detik tanpa damage baru regen (60fps)
TOWER_SHIELD_REGEN_RATE = 1.5      # HP per frame saat regen (cepat)

# HP Regen System (self-heal)
TOWER_HP_REGEN_ENABLED = True
TOWER_HP_REGEN_DELAY = 300         # 5 detik tanpa damage baru regen HP
TOWER_HP_REGEN_RATE = 0.3          # HP per frame (lambat)
TOWER_HP_REGEN_MAX_RATIO = 1.0     # Regen bisa sampai 100% HP

# Shield color per team
SHIELD_COLOR_BLUE = (100, 180, 255)
SHIELD_COLOR_RED = (255, 100, 100)

# ═══════════════════════════════════════
# TOWER REGEN SHIELD (fitur berbayar)
# Tower level 4+ bisa membeli "Regen Shield": sekali diaktifkan, shield
# tower akan REGENERASI otomatis (seperti regen HP). Harga setara tower
# level 5 (lihat ARCHER/CANNON/ICE/MAGE_LEVELS[5]["cost"] = 850).
# Berlaku untuk tower pemain MAUPUN tower AI (parity).
# ═══════════════════════════════════════
TOWER_REGEN_SHIELD_ENABLED = True
TOWER_REGEN_SHIELD_MIN_LEVEL = 4      # baru bisa dibeli saat tower lvl 4+
TOWER_REGEN_SHIELD_COST = 850         # setara upgrade tower ke level 5
TOWER_REGEN_SHIELD_DELAY = 180        # 3 detik tanpa damage -> regen shield
TOWER_REGEN_SHIELD_RATE = 1.8         # shield/frame saat regen

# ── LAYAR ──
def _PANEL_AKTIF():
    """True kalau panel kanan tersedia (layar lebih lebar dari 16:9)."""
    try:
        from mobile import platform_utils as _p
        return _p.get_panel_rect() is not None
    except Exception:
        return False


SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
TOP_BAR_HEIGHT = 40   # top bar height
TITLE = "Mystic Arena"
FPS   = 60

# ── WARNA DASAR ──
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0  )
RED        = (220, 50,  50 )
GREEN      = (50,  200, 50 )
BLUE       = (70,  120, 255)
YELLOW     = (255, 220, 0  )
ORANGE     = (255, 140, 0  )
GRAY       = (150, 150, 150)
DARK_GRAY  = (60,  60,  70 )
LIGHT_GRAY = (200, 200, 200)
BROWN      = (139, 90,  43 )
PURPLE     = (150, 0,   200)
CYAN       = (0,   200, 200)
GOLD       = (255, 200, 50 )

BLUE_TEAM  = (60,  120, 255)
BLUE_DARK  = (30,  70,  180)
BLUE_LIGHT = (150, 200, 255)
RED_TEAM   = (220, 60,  60 )
RED_DARK   = (150, 30,  30 )
RED_LIGHT  = (255, 150, 150)

# ── WARNA MAP ──
GRASS_COLOR  = (55,  95,  55 )
GRASS_DARK   = (35,  65,  40 )
GRASS_LIGHT  = (75,  120, 65 )
PATH_COLOR   = (145, 120, 85 )
PATH_LIGHT   = (170, 145, 105)
PATH_BORDER  = (75,  60,  40 )
STONE_COLOR  = (85,  80,  70 )
STONE_LIGHT  = (115, 110, 95 )
STONE_DARK   = (55,  50,  42 )
WATER_COLOR  = (45,  90,  130)
WATER_LIGHT  = (85,  140, 180)
TREE_DARK    = (25,  55,  30 )
TREE_MID     = (45,  90,  50 )
TREE_LIGHT   = (75,  130, 70 )
BUSH_COLOR   = (40,  80,  45 )

# ── WARNA MINION ──
GOBLIN_COLOR     = (100, 180, 80 )
ORC_COLOR        = (200, 100, 60 )
TROLL_COLOR      = (100, 140, 170)
UNDEAD_COLOR     = (200, 200, 220)
DARK_RIDER_COLOR = (100, 60,  140)

# ── LANE POSITIONS ──
# Sekarang tidak dipakai untuk minions (karena curved),
# tapi masih dipakai untuk kompatibilitas beberapa kode lama
LANE_Y_TOP  = 150
LANE_Y_MID  = 380
LANE_Y_BOT  = 610
LANE_HEIGHT = 55

# ── BASE POSITIONS (DOTA 2 Style) ──
# Blue (Radiant) - kiri bawah
BLUE_BASE_X = 100
BLUE_BASE_Y = 620
# Red (Dire) - kanan atas
RED_BASE_X  = 1180
RED_BASE_Y  = 100
# BASE_Y untuk kompatibilitas kode lama
BASE_Y      = 380

LANE_START_X = 100      # Blue base area
LANE_END_X   = 1180     # Red base area

# ── NPC TOWERS (3 per lane, mengikuti curved path) ──
# Format: (x, y, lane)
# Diletakkan di titik-titik strategis sepanjang curved lane

# BLUE TOWERS (dekat Radiant/Blue base)
BLUE_TOWERS = [
    # TOP LANE (dari base ke atas)
    (120, 500, "top"),      # T1 outer
    (140, 350, "top"),      # T2 mid
    (200, 180, "top"),      # T3 inner (dekat tikungan)

    # MID LANE (diagonal)
    (240, 540, "mid"),      # T1 outer
    (360, 440, "mid"),      # T2 mid
    (500, 340, "mid"),      # T3 inner

    # BOT LANE (dari base ke kanan)
    (240, 650, "bot"),      # T1 outer
    (440, 640, "bot"),      # T2 mid
    (640, 640, "bot"),      # T3 inner
]

# RED TOWERS (dekat Dire/Red base)
RED_TOWERS = [
    # TOP LANE (dari base ke kiri)
    (1050, 100, "top"),     # T1 outer
    (850, 90, "top"),       # T2 mid
    (650, 90, "top"),       # T3 inner

    # MID LANE (diagonal)
    (1050, 200, "mid"),     # T1 outer
    (920, 300, "mid"),      # T2 mid
    (780, 400, "mid"),      # T3 inner

    # BOT LANE (dari base ke bawah)
    (1160, 250, "bot"),     # T1 outer
    (1140, 400, "bot"),     # T2 mid
    (1090, 550, "bot"),     # T3 inner
]

# ── BUILD SLOTS (dekat lane, agak menjauh dari path) ──
# BLUE (Radiant) slots
BUILD_SLOTS_BLUE = []

# RED (Dire) slots
BUILD_SLOTS_RED = []

SLOT_SIZE = 40
BULLET_SPEED = 8
BULLET_RADIUS = 4

# ═══ ECONOMY (Untuk gameplay 12-15 menit) ═══
STARTING_GOLD = 350          # Cukup untuk 3 tower awal
GOLD_PER_SECOND = 3          # 180 gold per menit passive

# ── MINION TYPES (Balanced) ──
MINION_TYPES = {
    "goblin": {
        "name": "Goblin",
        "hp": 45,
        "damage": 5,          # BUFF 3 → 5 (+67%)
        "speed": 1.5,
        "range": 25,
        "attack_cooldown": 45,
        "gold_reward": 8,
        "radius": 9,
        "color": GOBLIN_COLOR
    },
    "orc": {
        "name": "Orc",
        "hp": 110,
        "damage": 13,         # BUFF 8 → 13 (+63%)
        "speed": 0.95,
        "range": 30,
        "attack_cooldown": 60,
        "gold_reward": 18,
        "radius": 12,
        "color": ORC_COLOR
    },
    "troll": {
        "name": "Troll",
        "hp": 320,
        "damage": 18,         # BUFF 11 → 18 (+64%)
        "speed": 0.65,
        "range": 28,
        "attack_cooldown": 75,
        "gold_reward": 45,
        "radius": 14,
        "color": TROLL_COLOR,
        "regen": 0.6
    },
    "undead": {
        "name": "Undead",
        "hp": 65,
        "damage": 11,         # BUFF 7 → 11 (+57%)
        "speed": 0.85,
        "range": 100,
        "attack_cooldown": 60,
        "gold_reward": 16,
        "radius": 10,
        "color": UNDEAD_COLOR
    },
    "dark_rider": {
        "name": "Dark Rider",
        "hp": 280,
        "damage": 32,         # BUFF 20 → 32 (+60%)
        "speed": 2.0,
        "range": 35,
        "attack_cooldown": 50,
        "gold_reward": 65,
        "radius": 13,
        "color": DARK_RIDER_COLOR
    },
}

# ═══ TIMING (Balanced untuk 12-15 min per game) ═══
MINION_WAVE_INTERVAL = 1500    # 25 detik antar wave (dari 900 = 15 detik)
MINION_SPAWN_DELAY = 20        # 0.33 detik antar spawn (dari 25)
FPS = 60

NEXUS_WAVE_COMPOSITION = {
    # ═══ EARLY GAME (Wave 1-3) - Tutorial ═══
    1: ["goblin", "goblin", "goblin"],
    2: ["goblin", "goblin", "goblin", "orc"],
    3: ["goblin", "orc", "goblin", "orc", "undead"],

    # ═══ MID GAME (Wave 4-7) - Buildup ═══
    4: ["orc", "goblin", "orc", "undead", "goblin", "goblin"],
    5: ["orc", "orc", "undead", "troll", "goblin", "goblin"],

    # ═══ LATE GAME (Wave 8-12) - Escalation ═══
    # Note: Level 5 pakai composition ini terus, tapi scale minion naik
    # Kalau castle sudah lvl 5, minion di-scale via minion_scale
}

NEXUS_LEVELS = {
    1: {
        "hp": 4000,             # Naik dari 3000 → 4000
        "damage": 35,           # Turun sedikit
        "range": 150,
        "attack_cooldown": 45,  # Slower attack
        "minion_scale": 1.0,
        "minion_ai_level": 1,
        "upgrade_cost": 500,
        "color_accent": (255, 255, 255),
        "description": "Basic Outpost"
    },
    2: {
        "hp": 6000,             # Naik dari 4500
        "damage": 55,
        "range": 165,
        "attack_cooldown": 40,
        "minion_scale": 1.2,
        "minion_ai_level": 2,
        "upgrade_cost": 900,
        "color_accent": (150, 255, 150),
        "description": "+20% Power"
    },
    3: {
        "hp": 8500,             # Naik dari 6500
        "damage": 80,
        "range": 180,
        "attack_cooldown": 35,
        "minion_scale": 1.4,
        "minion_ai_level": 3,
        "upgrade_cost": 1500,
        "color_accent": (100, 200, 255),
        "description": "+40% Power"
    },
    4: {
        "hp": 11500,            # Naik dari 9000
        "damage": 115,
        "range": 195,
        "attack_cooldown": 30,
        "minion_scale": 1.7,
        "minion_ai_level": 4,
        "upgrade_cost": 2400,
        "color_accent": (255, 100, 255),
        "description": "Elite Stronghold"
    },
    5: {
        "hp": 15000,            # Naik dari 12500
        "damage": 160,
        "range": 210,
        "attack_cooldown": 25,
        "minion_scale": 2.0,    # Turun dari 2.2
        "minion_ai_level": 5,
        "upgrade_cost": 0,
        "color_accent": (255, 200, 50),
        "description": "MAX - Royal Castle"
    },
}

MAX_NEXUS_LEVEL = 5
BASE_RADIUS = 45

# ── TOWER STATS ──
TOWER_STATS = {
    "outer": {"hp": 1500, "damage": 45, "range": 160,
              "attack_cooldown": 35, "gold_reward": 200},
    "inner": {"hp": 2200, "damage": 65, "range": 180,
              "attack_cooldown": 30, "gold_reward": 300},
}

PLAYER_TOWER_TYPES = {}
# ── HERO TYPES (Balanced - Hero range < Tower range) ──
HERO_TYPES = {
    "kaizen": {
        "name": "Kaizen",
        "title": "The Wind Blade",
        "role": "Assassin",
        "cost": 400,
        "hp": 550,             # ← 400 → 550
        "damage": 35,          # ← 25 → 35
        "speed": 2.2,
        "range": 50,
        "attack_cooldown": 32,
        "color": (100, 200, 255),
        "color_dark": (50, 100, 200),
        "skill_name": "Wind Slash",
        "skill_desc": "Dash & slash AOE",
        "skill_cooldown": 300,
        "skill_damage": 65,    # ← 50 → 65
        "skill_range": 100,
        "description": "Agile samurai assassin",
    },
    "grimjaw": {
        "name": "Grimjaw",
        "title": "The Berserker",
        "role": "Fighter",
        "cost": 450,
        "hp": 800,             # ← 600 → 800
        "damage": 30,          # ← 22 → 30
        "speed": 1.6,
        "range": 45,
        "attack_cooldown": 36,
        "color": (200, 80, 40),
        "color_dark": (140, 40, 20),
        "skill_name": "Blade Fury",
        "skill_desc": "Spin AOE damage",
        "skill_cooldown": 420,
        "skill_damage": 22,    # ← 15 → 22
        "skill_range": 70,
        "skill_duration": 120,
        "description": "Berserker spin blade",
    },
    "sylara": {
        "name": "Sylara",
        "title": "The Wind Ranger",
        "role": "Marksman",
        "cost": 380,
        "hp": 450,             # ← 320 → 450
        "damage": 42,          # ← 32 → 42
        "speed": 1.5,
        "range": 130,
        "attack_cooldown": 52,
        "color": (100, 220, 120),
        "color_dark": (50, 140, 70),
        "skill_name": "Focus Fire",
        "skill_desc": "Attack speed buff + piercing shot",
        "skill_cooldown": 360,
        "skill_damage": 90,    # ← 70 → 90
        "skill_range": 180,
        "description": "Mid-range marksman",
    },
    "vex": {
        "name": "Vex",
        "title": "The Void Harbinger",
        "role": "Mage",
        "cost": 420,
        "hp": 500,
        "damage": 30,
        "speed": 1.3,
        "range": 130,
        "attack_cooldown": 46,
        "color": (100, 200, 150),
        "color_dark": (30, 100, 70),
        "skill_name": "Arcane Orb",
        "skill_desc": "Long-range missile + line",
        "skill_cooldown": 330,
        "skill_damage": 85,
        "skill_range": 250,
        "skill_aoe": 80,
        "description": "Void mage, high burst",
    },
    "thorne": {
        "name": "Thorne",
        "title": "The Quill Sprayer",
        "role": "Bruiser",
        "cost": 500,
        "hp": 1400,
        "damage": 28,
        "speed": 1.3,
        "range": 55,
        "attack_cooldown": 40,
        "color": (215, 155, 30),
        "color_dark": (150, 95, 20),
        "skill_name": "Viscous Nose",
        "skill_desc": "Goop cone + slow",
        "skill_cooldown": 300,
        "skill_damage": 60,
        "skill_range": 100,
        "skill_stun_duration": 60,
        "description": "Tanky porcupine warrior",
    },
    "zephyr": {
        "name": "Zephyr",
        "title": "Meander of Mischief",
        "role": "Mage/Trickster",
        "cost": 420,
        "hp": 520,
        "damage": 25,
        "speed": 1.6,
        "range": 130,
        "attack_cooldown": 30,
        "color": (215, 60, 90),
        "color_dark": (100, 20, 40),
        "skill_name": "Bramble Maze",
        "skill_desc": "Thorn trap + slow",
        "skill_cooldown": 300,
        "skill_damage": 65,
        "skill_range": 150,
        "skill_chain_count": 4,
        "description": "Dark fairy trickster",
    },
}
HERO_LEVELS = {
    # Level 1-5: kurva asli (tidak diubah, save lama tetap kompatibel)
    1:  {"hp_mult": 1.0,  "dmg_mult": 1.0,  "skill_mult": 1.0,
         "upgrade_cost": 300},
    2:  {"hp_mult": 1.3,  "dmg_mult": 1.25, "skill_mult": 1.2,
         "upgrade_cost": 500},
    3:  {"hp_mult": 1.65, "dmg_mult": 1.55, "skill_mult": 1.45,
         "upgrade_cost": 800},
    4:  {"hp_mult": 2.1,  "dmg_mult": 1.9,  "skill_mult": 1.75,
         "upgrade_cost": 1200},
    5:  {"hp_mult": 2.7,  "dmg_mult": 2.4,  "skill_mult": 2.1,
         "upgrade_cost": 1800},
    # Level 6-10: lanjutan kurva.
    # Rasio pertumbuhan sengaja melandai (hp ~1.22x -> 1.16x per level)
    # supaya late game tidak jadi one-shot, tapi tetap terasa naik.
    6:  {"hp_mult": 3.35, "dmg_mult": 2.9,  "skill_mult": 2.5,
         "upgrade_cost": 2600},
    7:  {"hp_mult": 4.05, "dmg_mult": 3.45, "skill_mult": 2.95,
         "upgrade_cost": 3600},
    8:  {"hp_mult": 4.8,  "dmg_mult": 4.05, "skill_mult": 3.45,
         "upgrade_cost": 4800},
    9:  {"hp_mult": 5.6,  "dmg_mult": 4.7,  "skill_mult": 4.0,
         "upgrade_cost": 6200},
    10: {"hp_mult": 6.5,  "dmg_mult": 5.4,  "skill_mult": 4.6,
         "upgrade_cost": 8000},
    # Level 11-15: MAX LEVEL diperpanjang dari 10 → 15.
    # Kurva dilanjutkan dengan ritme yang sama (tiap level +~0.9
    # multiplier). Cost naik tajam supaya late-game tetap punya
    # sink emas yang berarti.
    11: {"hp_mult": 7.5,  "dmg_mult": 6.2,  "skill_mult": 5.2,
         "upgrade_cost": 10200},
    12: {"hp_mult": 8.6,  "dmg_mult": 7.0,  "skill_mult": 5.9,
         "upgrade_cost": 12800},
    13: {"hp_mult": 9.8,  "dmg_mult": 7.9,  "skill_mult": 6.6,
         "upgrade_cost": 15800},
    14: {"hp_mult": 11.1, "dmg_mult": 8.9,  "skill_mult": 7.4,
         "upgrade_cost": 19200},
    15: {"hp_mult": 12.5, "dmg_mult": 10.0, "skill_mult": 8.2,
         "upgrade_cost": 0},   # 0 = MAX, tidak bisa upgrade lagi
}
MAX_HERO_LEVEL = 15

BLUE_HERO_SPAWN_X = 160
BLUE_HERO_SPAWN_Y = 600   # dekat blue base baru
RED_HERO_SPAWN_X  = 1120
RED_HERO_SPAWN_Y  = 120   # dekat red base baru
HERO_SPAWN_Y = 600        # default (blue side)

MAX_HEROES_OWNED = 5

# ═══════════════════════════════════════
# BOSS HERO UPGRADE COST POLICY
# Hero unlock (boss/mini/true) punya biaya UPGRADE LEVEL in-game yang
# LEBIH MAHAL daripada starter hero. Multiplier diterapkan di
# Hero.upgrade_cost(). Berlaku sama untuk pemain maupun AI (parity).
# ═══════════════════════════════════════
BOSS_HERO_UPGRADE_COST_MULT = 1.6   # boss hero 60% lebih mahal per level

# ═══════════════════════════════════════
# TOWER SYSTEM (Archer base + 3 upgrade paths)
# ═══════════════════════════════════════

TOWER_MAX_LEVEL = 6

# Tower types & warna
TOWER_TYPE_COLORS = {
    "archer":  {"main": (100, 220, 120), "dark": (50, 140, 70)},   # Green
    "cannon":  {"main": (200, 100, 60),  "dark": (140, 60, 30)},   # Orange
    "ice":     {"main": (120, 200, 255), "dark": (60, 130, 200)},  # Light Blue
    "mage":    {"main": (180, 80, 220),  "dark": (110, 40, 150)},  # Purple
}

# Base tower (Level 1) - Archer default
TOWER_BASE_STATS = {
    "hp": 800,
    "damage": 20,
    "range": 180,
    "attack_cooldown": 35,
    "name": "Archer",
    "type": "archer",
}

# ═══ ARCHER PATH (Balanced DPS single target) ═══
ARCHER_LEVELS = {
    1: {"hp": 800,  "damage": 20,  "range": 180, "cd": 35, "cost": 0,
        "desc": "Basic archer"},
    2: {"hp": 1050, "damage": 32,  "range": 190, "cd": 33, "cost": 175,
        "desc": "Faster arrows"},
    3: {"hp": 1350, "damage": 48,  "range": 200, "cd": 30, "cost": 325,
        "desc": "Better bow"},
    4: {"hp": 1750, "damage": 68,  "range": 210, "cd": 27, "cost": 550,
        "desc": "Elite marksman"},
    5: {"hp": 2200, "damage": 90,  "range": 220, "cd": 24, "cost": 850,
        "desc": "Master archer"},
    6: {"hp": 2800, "damage": 120, "range": 230, "cd": 22, "cost": 1300,
        "desc": "DOUBLE SHOT!", "double_shot": True},
}

# ═══ CANNON PATH (High AOE + BURNING) - BUFFED attack speed slightly ═══
CANNON_LEVELS = {
    2: {"hp": 1200, "damage": 45,  "range": 160, "cd": 44, "cost": 175,
        "desc": "Splash + Burn 8/s", "splash": 45,
        "burn_dps": 8,  "burn_duration": 120},
    3: {"hp": 1500, "damage": 65,  "range": 170, "cd": 40, "cost": 325,
        "desc": "Big Boom + Burn 12/s", "splash": 55,
        "burn_dps": 12, "burn_duration": 150},
    4: {"hp": 1900, "damage": 90,  "range": 180, "cd": 36, "cost": 550,
        "desc": "Heavy Cannon + Burn 16/s", "splash": 65,
        "burn_dps": 16, "burn_duration": 150},
    5: {"hp": 2400, "damage": 125, "range": 190, "cd": 32, "cost": 850,
        "desc": "Siege + Burn 22/s", "splash": 80,
        "burn_dps": 22, "burn_duration": 180},
    6: {"hp": 3000, "damage": 170, "range": 200, "cd": 28, "cost": 1300,
        "desc": "DEVASTATOR! Burn 30/s", "splash": 100,
        "burn_dps": 30, "burn_duration": 180},
}
# ═══ ICE PATH (Crowd Control: movement + attack slow) - BUFFED attack speed ═══
ICE_LEVELS = {
    2: {"hp": 950,  "damage": 22,  "range": 170, "cd": 26, "cost": 175,
        "desc": "Slow 25% & Atk -15%", "slow": 0.25, "slow_duration": 90,
        "atk_slow": 0.15},
    3: {"hp": 1250, "damage": 35,  "range": 180, "cd": 22, "cost": 325,
        "desc": "Slow 35% & Atk -20%", "slow": 0.35, "slow_duration": 100,
        "atk_slow": 0.20},
    4: {"hp": 1600, "damage": 50,  "range": 190, "cd": 18, "cost": 550,
        "desc": "Slow 45% & Atk -25%", "slow": 0.45, "slow_duration": 110,
        "atk_slow": 0.25},
    5: {"hp": 2050, "damage": 70,  "range": 200, "cd": 16, "cost": 850,
        "desc": "Slow 55% & Atk -30%", "slow": 0.55, "slow_duration": 120,
        "atk_slow": 0.30},
    6: {"hp": 2600, "damage": 95,  "range": 220, "cd": 14, "cost": 1300,
        "desc": "FREEZE! AOE + Atk -40%", "slow": 0.65,
        "slow_duration": 150, "slow_aoe": 80, "atk_slow": 0.40},
}
# ═══ MAGE PATH (Chain + Skill Down + Anti-Heal) - BUFFED attack speed ═══
MAGE_LEVELS = {
    2: {"hp": 850,  "damage": 18,  "range": 180, "cd": 20, "cost": 175,
        "desc": "Hit 2, Skill -20%, Heal -40%", "chain": 2,
        "skill_down": 0.20, "anti_heal": 0.40, "debuff_duration": 120},
    3: {"hp": 1100, "damage": 28,  "range": 190, "cd": 18, "cost": 325,
        "desc": "Skill -25%, Heal -50%", "chain": 2,
        "skill_down": 0.25, "anti_heal": 0.50, "debuff_duration": 130},
    4: {"hp": 1450, "damage": 42,  "range": 200, "cd": 16, "cost": 550,
        "desc": "Hit 3, Skill -30%, Heal -60%", "chain": 3,
        "skill_down": 0.30, "anti_heal": 0.60, "debuff_duration": 140},
    5: {"hp": 1850, "damage": 60,  "range": 210, "cd": 14, "cost": 850,
        "desc": "Skill -40%, Heal -75%", "chain": 3,
        "skill_down": 0.40, "anti_heal": 0.75, "debuff_duration": 150},
    6: {"hp": 2350, "damage": 82,  "range": 230, "cd": 12, "cost": 1300,
        "desc": "CHAIN! Skill -50%, Heal -100%", "chain": 4,
        "skill_down": 0.50, "anti_heal": 1.00, "debuff_duration": 180},
}

# Lookup dictionary
TOWER_UPGRADE_PATHS = {
    "archer": ARCHER_LEVELS,
    "cannon": CANNON_LEVELS,
    "ice": ICE_LEVELS,
    "mage": MAGE_LEVELS,
}

# Tower descriptions for UI - English, concise, no overlap
TOWER_TYPE_INFO = {
    "archer": {
        "name": "Archer Tower",
        "icon": "🏹",
        "desc": "Fast single-target. Balanced DPS.",
        "special": "Lv6: Double Shot",
    },
    "cannon": {
        "name": "Cannon Tower",
        "icon": "💣",
        "desc": "AOE + Burning DOT. Buffed speed.",
        "special": "Burn DOT + Splash AOE",
    },
    "ice": {
        "name": "Ice Tower",
        "icon": "❄️",
        "desc": "Slows move & attack speed. CC.",
        "special": "Move + Atk Slow, AOE at max",
    },
    "mage": {
        "name": "Mage Tower",
        "icon": "🔮",
        "desc": "Chain + Skill Down + Anti-Heal.",
        "special": "Skill -50%, Heal block 100%",
    },
}

# ═══════════════════════════════════════
# TOWER DEBUFF / STATUS EFFECT SYSTEM
# ═══════════════════════════════════════
# BUFF menara Ice / Mage / Cannon:
#   ❄  Ice    : debuff movement speed (lama) + debuff ATTACK SPEED (baru)
#   🔮 Mage  : debuff SKILL DAMAGE + ANTI-HEAL (semua heal musuh dipotong)
#   💣 Cannon : BURNING (damage over time) + attack speed menara naik
#
# Efek berlaku untuk SEMUA unit: minion, hero starter, hero unlock,
# mini boss, maupun true boss. Dan karena class Tower/Bullet/Minion/
# Hero/Boss dipakai bersama oleh pemain (blue) maupun AI enemy (red),
# seluruh fitur ini OTOMATIS juga berlaku penuh untuk tower milik AI:
# AI enemy menerima buff yang sama persis seperti pemain.
#
# Mixin di bawah ini dipakai Minion & Hero (_entity.py) serta Boss
# (bosses/base_boss.py lewat `from settings import *`), jadi HARUS
# tetap berada di zona "settings" (sebelum snapshot alias di bawah).

TOWER_DEBUFF_BURN_TICK = 30   # jeda tick damage burn (frame, ~60fps)
TOWER_DEBUFF_FPS = 60.0       # konversi burn_dps -> damage per frame


class TowerDebuffMixin:
    """Status-effect universal (debuff dari menara Ice/Mage/Cannon).

    Menyediakan:
      slow       - movement speed turun        (Ice, kompatibel API lama)
      atk_slow   - attack speed turun          (Ice, BARU)
      skill_down - skill/ability damage turun  (Mage, BARU)
      anti_heal  - heal yang diterima dipotong (Mage, BARU)
      burn       - damage per detik            (Cannon, BARU)

    Anti-heal diimplementasikan lewat property `hp`: SETIAP penulisan
    `unit.hp = ...` yang MENAIKKAN hp saat debuff aktif otomatis dipotong
    (anti_heal 1.0 = heal tidak masuk sama sekali). Ini menangkap semua
    jalur heal: regen minion, heal base/passive hero, skill heal hero di
    hero_skills/, maupun puluhan heal di AI boss - tanpa mengubah satu
    pun call site.
    """

    # ── INIT ──
    def _init_tower_debuffs(self):
        # Movement slow (nama field sama dgn sistem lama Minion)
        self.slow_amount = 0.0
        self.slow_timer = 0
        # Attack speed slow
        self.atk_slow_amount = 0.0
        self.atk_slow_timer = 0
        # Skill damage down
        self.skill_down_amount = 0.0
        self.skill_down_timer = 0
        # Anti-heal (0.0 - 1.0)
        self.anti_heal_amount = 0.0
        self.anti_heal_timer = 0
        # Burning (damage over time)
        self.burn_dps = 0.0
        self.burn_timer = 0
        self.burn_accum = 0.0
        self.burn_tick_cd = TOWER_DEBUFF_BURN_TICK
        self.burn_team = None

    # ── PROPERTY: hp dengan anti-heal ──
    @property
    def hp(self):
        # AttributeError alami kalau belum pernah di-set, supaya pola
        # `hasattr(self, 'hp')` di Hero._apply_level_stats tetap benar.
        return self._hp_value

    @hp.setter
    def hp(self, value):
        old = getattr(self, "_hp_value", None)
        if (old is not None and value > old
                and getattr(self, "anti_heal_timer", 0) > 0):
            # ANTI-HEAL: kenaikan HP dipotong sesuai besar debuff
            value = old + (value - old) * (1.0 - self.anti_heal_amount)
        self._hp_value = value

    # ── APPLY DEBUFF ──
    def apply_slow(self, amount, duration):
        """Debuff movement speed (signature lama, dipakai juga hero skill)."""
        if not getattr(self, "alive", True):
            return
        if amount > getattr(self, "slow_amount", 0.0) or \
                getattr(self, "slow_timer", 0) < duration:
            self.slow_amount = amount
            self.slow_timer = duration

    def apply_debuff(self, kind, amount, duration, source_team=None):
        """Apply debuff menara. Stack rule: terkuat menang, durasi refresh."""
        if not getattr(self, "alive", True):
            return
        if kind == "slow":
            self.apply_slow(amount, duration)
        elif kind == "atk_slow":
            if amount > self.atk_slow_amount or \
                    self.atk_slow_timer < duration:
                self.atk_slow_amount = amount
                self.atk_slow_timer = duration
        elif kind == "skill_down":
            if amount > self.skill_down_amount or \
                    self.skill_down_timer < duration:
                self.skill_down_amount = amount
                self.skill_down_timer = duration
        elif kind == "anti_heal":
            if amount > self.anti_heal_amount or \
                    self.anti_heal_timer < duration:
                self.anti_heal_amount = amount
                self.anti_heal_timer = duration
        elif kind == "burn":
            if self.burn_timer <= 0:
                self.burn_dps = amount
                self.burn_accum = 0.0
                self.burn_tick_cd = TOWER_DEBUFF_BURN_TICK
            else:
                self.burn_dps = max(self.burn_dps, amount)
            self.burn_timer = max(self.burn_timer, duration)
            if source_team is not None:
                self.burn_team = source_team

    def clear_tower_debuffs(self):
        """Reset semua debuff (dipakai saat mati / respawn)."""
        self._init_tower_debuffs()

    # ── HELPER EFEKTIF ──
    def _eff_speed(self):
        """Speed efektif setelah movement slow (dipakai manual di Hero)."""
        sp = self.speed
        if getattr(self, "slow_timer", 0) > 0:
            sp *= (1.0 - getattr(self, "slow_amount", 0.0))
        return sp

    def _eff_attack_cd(self, base_cd):
        """Attack cooldown efektif setelah debuff attack speed (Ice)."""
        if getattr(self, "atk_slow_timer", 0) > 0:
            f = max(0.05, 1.0 - getattr(self, "atk_slow_amount", 0.0))
            return max(1, int(round(base_cd / f)))
        return base_cd

    # ── TICK per frame (dipanggil di update masing-masing class) ──
    def _tick_tower_debuffs(self):
        if self.slow_timer > 0:
            self.slow_timer -= 1
            if self.slow_timer <= 0:
                self.slow_amount = 0.0
        if self.atk_slow_timer > 0:
            self.atk_slow_timer -= 1
            if self.atk_slow_timer <= 0:
                self.atk_slow_amount = 0.0
        if self.skill_down_timer > 0:
            self.skill_down_timer -= 1
            if self.skill_down_timer <= 0:
                self.skill_down_amount = 0.0
        if self.anti_heal_timer > 0:
            self.anti_heal_timer -= 1
            if self.anti_heal_timer <= 0:
                self.anti_heal_amount = 0.0

        # Burning: damage diakumulasi per frame, ditembakkan per tick
        # (bukan tiap frame, supaya damage number tidak spam).
        if self.burn_timer > 0:
            self.burn_timer -= 1
            self.burn_accum += self.burn_dps / TOWER_DEBUFF_FPS
            self.burn_tick_cd -= 1
            if self.burn_tick_cd <= 0:
                self.burn_tick_cd = TOWER_DEBUFF_BURN_TICK
                dmg = int(self.burn_accum)
                if dmg > 0 and getattr(self, "alive", False):
                    self.burn_accum -= dmg
                    self.take_damage(dmg, self.burn_team or self.team,
                                     "fire")
            if self.burn_timer <= 0:
                self.burn_dps = 0.0
                self.burn_accum = 0.0

    # ── VISUAL ringkas: aura api + pip ikon debuff ──
    def _draw_tower_debuff_fx(self, surface, x, y, radius=14,
                              include_rings=True):
        """Gambar indikator debuff. Dipanggil dari draw() tiap class."""
        if not getattr(self, "alive", True):
            return

        x = int(x)
        y = int(y)
        radius = int(radius)

        # ── Ring slow di kaki (hero/boss; minion punya aura es sendiri) ──
        if include_rings and getattr(self, "slow_timer", 0) > 0:
            pygame.draw.ellipse(surface, (150, 220, 255),
                                (x - radius - 2, y + radius - 7,
                                 (radius + 2) * 2, 10), 1)

        # ── BURN: lidah api flicker di sekitar badan ──
        if getattr(self, "burn_timer", 0) > 0:
            anim = getattr(self, "anim_time",
                           getattr(self, "pulse", 0))
            flick = int(1.5 + 1.5 * math.sin(anim * 0.6))
            flames = ((-radius + 2, -radius - 2, 2 + flick),
                      (radius - 2, -radius - 3, 2),
                      (0, -radius - 6, 3 + flick))
            for ox, oy, fr in flames:
                pygame.draw.circle(surface, (255, 140, 40),
                                   (x + ox, y + oy), fr)
                pygame.draw.circle(surface, (255, 220, 90),
                                   (x + ox, y + oy), max(1, fr - 1))

        # ── Pip ikon debuff (baris kecil di bawah kaki) ──
        pips = []
        if getattr(self, "slow_timer", 0) > 0:
            pips.append((150, 220, 255))    # ice - move slow
        if getattr(self, "atk_slow_timer", 0) > 0:
            pips.append((90, 160, 255))     # ice - attack slow
        if getattr(self, "skill_down_timer", 0) > 0:
            pips.append((200, 120, 255))    # mage - skill down
        if getattr(self, "anti_heal_timer", 0) > 0:
            pips.append((255, 90, 140))     # mage - anti heal
        if getattr(self, "burn_timer", 0) > 0:
            pips.append((255, 130, 40))     # cannon - burn
        if pips:
            pip_y = y + radius + 12
            total_w = len(pips) * 5 - 1
            px = x - total_w // 2
            for c in pips:
                pygame.draw.rect(surface, (10, 10, 14),
                                 (px - 1, pip_y - 1, 5, 5))
                pygame.draw.rect(surface, c, (px, pip_y, 4, 4))
                px += 5


# ── AI SETTINGS ──
AI_THINK_INTERVAL = 90
AI_MIN_GOLD_RESERVE = 50
AI_UPGRADE_TOWER_CHANCE = 0.30
AI_SELL_HP_THRESHOLD = 0.15
AI_NEXUS_UPGRADE_PRIORITY = 0.35
AI_HERO_BUY_PRIORITY = 0.45
AI_HERO_UPGRADE_PRIORITY = 0.40
AI_SKILL_USE_MIN_ENEMIES = 2
AI_HERO_PREFERENCES = ["thorne", "grimjaw", "vex", "sylara", "kaizen", "zephyr"]
AI_MAX_HEROES = 5  # AI max 5 heroes (including boss heroes) - matches player limit

# ═══════════════════════════════════════
# CASTLE SHIELD SYSTEM (Anti-smurf / anti-premature destruction)
# Before wave 10, castle has protective shield that reduces damage
# ═══════════════════════════════════════
CASTLE_SHIELD_ENABLED = True
CASTLE_SHIELD_WAVE_THRESHOLD = 10      # Shield active before wave 10
CASTLE_SHIELD_DAMAGE_REDUCTION = 0.75 # 75% damage reduction before wave 10
CASTLE_SHIELD_HP_RATIO = 0.6          # Shield HP = 60% max HP
CASTLE_SHIELD_REGEN_DELAY = 120       # 2 sec no damage -> regen
CASTLE_SHIELD_REGEN_RATE = 2.0        # Shield regen per frame
CASTLE_SHIELD_COLOR_BLUE = (100, 200, 255)
CASTLE_SHIELD_COLOR_RED = (255, 120, 120)

# ═══════════════════════════════════════
# CASTLE ALIAS (nama baru untuk Nexus)
# ═══════════════════════════════════════
CASTLE_LEVELS = NEXUS_LEVELS
MAX_CASTLE_LEVEL = MAX_NEXUS_LEVEL
CASTLE_WAVE_COMPOSITION = NEXUS_WAVE_COMPOSITION
CASTLE_RADIUS = BASE_RADIUS

# Castle names per level (untuk display di UI)
CASTLE_NAMES = {
    1: "OUTPOST",
    2: "WATCHTOWER",
    3: "FORTRESS",
    4: "STRONGHOLD",
    5: "ROYAL CASTLE",
}
# ═══════════════════════════════════════
# HERO REGISTRY HELPERS
# ═══════════════════════════════════════

def _default_hero_unlock_cost(hero_type, stats,
                              is_boss_hero=False,
                              boss_class="mini"):
    """
    Meta unlock cost (main menu shop).
    Ini BUKAN cost summon in-game.
    """
    if is_boss_hero:
        return 2200 if boss_class == "true" else 1200

    base_cost = stats.get("cost", 400)
    return max(600, int(base_cost * 1.8))


def get_all_hero_types():
    """
    Return semua hero yang valid:
    - hero normal dari HERO_TYPES
    - hero boss dari bosses.boss_data[*]['hero_unlock']
    """
    all_heroes = {}

    # Base heroes
    for hero_type, stats in HERO_TYPES.items():
        data = dict(stats)
        data.setdefault(
            "unlock_cost",
            _default_hero_unlock_cost(hero_type, data)
        )
        data.setdefault("unlock_require_boss", None)
        data.setdefault("is_boss_hero", False)
        all_heroes[hero_type] = data

    # Boss heroes
    try:
        from bosses.boss_data import MINI_BOSS_TYPES, TRUE_BOSS_TYPES

        boss_tables = [
            ("mini", MINI_BOSS_TYPES),
            ("true", TRUE_BOSS_TYPES),
        ]

        for boss_class, table in boss_tables:
            for boss_type, boss_data in table.items():
                hero_unlock = boss_data.get("hero_unlock")
                if not hero_unlock:
                    continue

                data = dict(hero_unlock)
                data.setdefault(
                    "unlock_cost",
                    _default_hero_unlock_cost(
                        boss_type, data,
                        is_boss_hero=True,
                        boss_class=boss_class
                    )
                )
                data["unlock_require_boss"] = boss_type
                data["is_boss_hero"] = True
                data["boss_class"] = boss_class
                data["source_boss_name"] = boss_data.get(
                    "name", boss_type.title()
                )

                all_heroes[boss_type] = data
    except Exception:
        pass

    return all_heroes


def get_hero_shop_order():
    """Order tampilan hero di shop."""
    ordered = list(HERO_TYPES.keys())
    try:
        from bosses.boss_data import MINI_BOSS_TYPES, TRUE_BOSS_TYPES
        ordered.extend(list(MINI_BOSS_TYPES.keys()))
        ordered.extend(list(TRUE_BOSS_TYPES.keys()))
    except Exception:
        pass
    return ordered



# ================================


# HERO SHOP PRICE POLICY
# Starter gratis; mini boss & true boss harganya sama (4500).
# Dev switch: set True kalau mau semua hero gratis saat testing.
DEV_UNLIMITED_HERO_GOLD = False
STARTER_HERO_UNLOCK_COST = 0
MINI_BOSS_HERO_UNLOCK_COST = 4500
TRUE_BOSS_HERO_UNLOCK_COST = 4500

_original_get_all_hero_types_shop_prices = get_all_hero_types


def get_all_hero_types():
    """Hero catalog with final main-menu unlock prices."""
    catalog = _original_get_all_hero_types_shop_prices()
    for _hero_type, _stats in catalog.items():
        if _stats.get("is_boss_hero"):
            if _stats.get("boss_class") == "true":
                _stats["unlock_cost"] = TRUE_BOSS_HERO_UNLOCK_COST
            else:
                _stats["unlock_cost"] = MINI_BOSS_HERO_UNLOCK_COST
        else:
            _stats["unlock_cost"] = STARTER_HERO_UNLOCK_COST
    return catalog


# ═══════════════════════════════════════════════════════
# ALIAS "settings" (DINI)
# Paket lain (map_components, ui_components, bosses, ...)
# mengimpor settings di level modul. Alias dipasang sekarang,
# HANYA berisi nama publik milik settings.py, supaya
# `from settings import *` berperilaku persis seperti dulu.
# ═══════════════════════════════════════════════════════
import sys as _sys
import types as _types

_settings_public = {
    _k: _v for _k, _v in globals().items()
    if _k not in _globals_before_settings and not _k.startswith("_")
}
_settings_alias = _types.ModuleType("settings")
_settings_alias.__doc__ = "settings.py (digabung ke _core.py)"
for _k, _v in _settings_public.items():
    setattr(_settings_alias, _k, _v)
_sys.modules.setdefault("settings", _settings_alias)
del _globals_before_settings


# ═══ IMPOR ANTAR-BUNDLE (setelah settings siap) ═══
from _system import SoundManager, FrustumCuller, update_spatial_grid
from _render import MapRenderer, EffectManager, clear_cache, get_font, title_font
from _entity import Minion, Tower, Castle, Hero, AIPlayer


# ====================================================================
# game.py
# ====================================================================

# GAME.PY - Full Screen Minimalist UI
# ================================

import pygame
import math
from _entity import Minion
from _entity import Tower
from _entity import Castle
from _entity import Hero
from _entity import AIPlayer
from _render import MapRenderer
from _system import SoundManager
from _render import EffectManager
from _system import FrustumCuller, update_spatial_grid
from _render import clear_cache, get_font


class Game:
    def __init__(self, screen, level_number=1, is_replay=False):
        self.screen = screen
        self.is_replay = is_replay
        # Cinematics
        self.boss_intro = None
        self.boss_death = None
        self.level_intro = None
        self.level_number = level_number
        # Load level config
        from levels import get_level_config
        self.level_config = get_level_config(level_number)
        if not self.level_config:
            print(f"[WARNING] Level {level_number} not found, using level 1")
            self.level_config = get_level_config(1)
            self.level_number = 1

        # Load map dengan theme dari level config
        theme = self.level_config.get("map_theme", "forest")
        self.map_renderer = MapRenderer(screen, theme_name=theme)
        self.animation_time = 0
        # ═══ TAMBAH: Effects Manager ═══
        self.effects = EffectManager()
        # ═══ UI STATE ═══
        self.shop_open = False
        self.popup_target = None
        self.popup_type = None
        self.ui_buttons = {}
        # ════════════════
        # ═══ TIER 3: Hover states ═══
        self.mouse_x = 0
        self.mouse_y = 0
        self.hovered_tower = None
        self.hovered_slot = None
        # ═══ TIER 3: Achievement tracking ═══
        self.achievements_unlocked = set()
        self.first_blood = False
        self.total_kills = 0
        self.max_combo = 0
        # ═══ DEVELOPER MODE (dari game_dev.py) ═══
        self.dev = DevMode(self)
        # ═══ INPUT HANDLER (dari game_input.py) ═══
        self.input = InputHandler(self)
        # ═══ UI RENDERER (dari game_ui.py) ═══
        self.ui = UIRenderer(self)

        self.reset()


    def reset(self):
        cfg = self.level_config

        # Bersihkan cache sprite antar-level supaya memori tidak
        # menumpuk (tiap level punya hero/boss berbeda).
        try:
            from heroes import clear_hero_sprite_cache
            clear_hero_sprite_cache()
        except Exception:
            pass

        self.gold = cfg["starting_gold"]
        self.score = 0
        self.ai = AIPlayer("red", level_number=self.level_number)
        self.gold_timer = 0
        self.minions = []
        self.towers = []
        self.heroes = []

        clear_cache()
        from _render import clear_sprite_cache
        clear_sprite_cache()


        # Generate BUILD SLOTS
        self._generate_build_slots_from_lanes()

        self.blue_base = Castle(BLUE_BASE_X, BLUE_BASE_Y, "blue")
        self.red_base = Castle(RED_BASE_X, RED_BASE_Y, "red")

        # Apply castle levels dari config
        while self.blue_base.level < cfg["starting_castle_level"]:
            self.blue_base.upgrade()
        while self.red_base.level < cfg["castle_start_level"]:
            self.red_base.upgrade()

        self.bases = [self.blue_base, self.red_base]
        self._blue_nexus_last_hp = self.blue_base.hp
        self.wave_number = 0
        self.wave_timer = 300
        # Initialize castle shields (active before wave 10)
        try:
            self.blue_base.set_wave(self.wave_number)
            self.red_base.set_wave(self.wave_number)
        except Exception:
            pass
        self.spawn_queue_blue = []
        self.spawn_queue_red = []
        self.spawn_timer_blue = 0
        self.spawn_timer_red = 0

        self.selected_tower = None
        self.selected_hero = None
        self.placing_tower_type = None
        self.shop_open = False
        self.popup_target = None
        self.popup_type = None
        self.ui_buttons = {}

        self.hero_respawn_timers = {}
        self.state = "playing"
        self.wave_notification_timer = 0
        self.wave_notification_text = ""
        self.build_popup_slot = None
        self.achievements_unlocked = set()
        self.first_blood = False
        self.total_kills = 0
        self.max_combo = 0
        # ═══ MATCH STATS TRACKING (untuk level stats) ═══
        import time as _time
        self.match_start_time = _time.time()
        self.match_stats_saved = False
        self.new_best_score = False
        self.new_best_time = False

        # ═══ BOSS SYSTEM ═══
        self.active_boss = None
        self.pending_mini_bosses = []
        self.true_boss_spawned = False
        # ═══ ACAK KEMUNCULAN MINI BOSS ═══
        # Alih-alih wave tetap (10/18/25), wave kemunculan diacak tiap run.
        # Jumlah & tipe boss tetap, hanya nomor wave-nya yang berubah.
        self._mini_boss_schedule = self._roll_mini_boss_schedule()

        # ═══ LEVEL SYSTEM ═══
        self.meta_reward_earned = 0
        self._meta_reward_granted = False
        self.return_to_menu_requested = False
        self.next_level_requested = False
        self.replay_requested = False
        self.bosses_defeated_this_run = 0

        # Load save
        from _system import SaveManager
        self.save_data = SaveManager.load()
        self.unlocked_bosses = self.save_data.get('unlocked_bosses', [])
        self.purchased_heroes = self.save_data.get('purchased_heroes', [])

        # AUTO-GRANT STARTER HERO
        if not self.purchased_heroes:
            self.purchased_heroes.append('kaizen')
            self.save_data['purchased_heroes'] = self.purchased_heroes
            SaveManager.save(self.save_data)
            print("[STARTER] Kaizen granted as starter hero!")

        clear_cache()
        # ═══ TRIGGER LEVEL INTRO ═══
        from _render import LevelIntroScreen
        self.level_intro = LevelIntroScreen(
            self.level_config, SCREEN_WIDTH, SCREEN_HEIGHT)

    def open_build_popup(self, slot):
        """Buka popup pilih tipe tower untuk build"""
        self.close_popup()
        self.build_popup_slot = slot
        SoundManager().play('ui_click', volume_mult=0.5)

    def close_build_popup(self):
        """Tutup build popup"""
        self.build_popup_slot = None

    def try_build_tower(self, tower_type):
        """Build tower di slot terpilih"""
        if not self.build_popup_slot:
            return

        slot = self.build_popup_slot

        # Cost: base tower L1 = 100G (murah biar early game asik)
        cost = 100

        if self.gold < cost:
            SoundManager().play('ui_error')
            return

        # Build tower
        self.gold -= cost
        slot['taken'] = True

        # Create tower
        new_tower = Tower(slot['x'], slot['y'], "blue",
                          "outer", slot['lane'])

        # Set tower type (kalau bukan archer, langsung upgrade)
        if tower_type != "archer":
            new_tower.tower_type = tower_type
            new_tower.level = 1
            new_tower._apply_level_stats()

        self.towers.append(new_tower)
        self.close_build_popup()

        SoundManager().play('ui_buy')

    def _generate_build_slots_from_lanes(self):
        """
        Generate build slot positions per lane per team.
        Slot ini kosong, tower dibuild oleh player/AI dengan gold.
        """
        self.build_slots_blue = []  # list of (x, y, lane, taken)
        self.build_slots_red = []

        lanes = ["top", "mid", "bot"]

        lane_positions = {
            "top": {
                "blue": [0.15, 0.30, 0.45],
                "red": [0.85, 0.70, 0.55],
            },
            "mid": {
                "blue": [0.10, 0.25, 0.40],
                "red": [0.90, 0.75, 0.60],
            },
            "bot": {
                "blue": [0.15, 0.30, 0.45],
                "red": [0.85, 0.70, 0.55],
            },
        }

        for lane in lanes:
            path = self.map_renderer.get_lane_path(lane)
            if not path:
                continue

            total_points = len(path)
            positions = lane_positions[lane]

            # Blue slots
            for pct in positions["blue"]:
                idx = int(total_points * pct)
                if idx >= total_points:
                    idx = total_points - 1
                x, y = path[idx]
                self.build_slots_blue.append({
                    'x': x, 'y': y, 'lane': lane, 'taken': False
                })

            # Red slots
            for pct in positions["red"]:
                idx = int(total_points * pct)
                if idx >= total_points:
                    idx = total_points - 1
                x, y = path[idx]
                self.build_slots_red.append({
                    'x': x, 'y': y, 'lane': lane, 'taken': False
                })

    def get_all_heroes(self):
        return self.heroes + self.ai.heroes

    def update_waves(self):
        # ══════════════════════════════════════════════════
        # BUG LAMA: `return` di sini memblokir SELURUH proses spawn
        # selama wave_timer berjalan (1500 frame = 25 DETIK).
        # Akibatnya banner "WAVE N" muncul, lalu layar sepi 25 detik,
        # baru minionnya menetes satu per satu - dan kalau wave
        # berikutnya keburu dipicu, hanya sebagian kecil (kadang 1)
        # minion yang sempat keluar.
        #
        # Sekarang wave_timer hanya menahan MAJUNYA WAVE BERIKUTNYA;
        # antrean spawn tetap jalan sehingga minion langsung keluar
        # setelah banner.
        # ══════════════════════════════════════════════════
        if self.wave_timer > 0:
            self.wave_timer -= 1
        elif len(self.spawn_queue_blue) == 0 and len(self.spawn_queue_red) == 0:
            # ═══ SINKRON WAVE ═══
            # Wave baru hanya maju kalau wave sebelumnya sudah bersih
            # dari layar, supaya banner "WAVE N" selalu muncul
            # berbarengan dengan minion wave N yang benar-benar
            # muncul (bukan saat minion wave lama masih bertarung).
            field_clear = not any(m.alive for m in self.minions)
            if field_clear:
                self.wave_number += 1
                # Update castle shield status based on new wave
                try:
                    self.blue_base.set_wave(self.wave_number)
                    self.red_base.set_wave(self.wave_number)
                    if self.wave_number == CASTLE_SHIELD_WAVE_THRESHOLD:
                        # Shield just expired - notify player
                        self.effects.unlock_achievement(
                            "Castle Shield Down!",
                            f"Wave {self.wave_number}: Castles vulnerable!",
                            "shield")
                except Exception:
                    pass
                SoundManager().play('wave_start', volume_mult=0.6)
                # ═══ MINI BOSS CHECK (pending-safe, WAVE DIACAK) ═══
                # Wave kemunculan mini boss diacak tiap run (lihat
                # _roll_mini_boss_schedule di reset). Jumlah & tipe boss
                # tetap sama, hanya WAVE-nya yang berubah.
                mini_bosses = getattr(self, "_mini_boss_schedule", None)
                if not mini_bosses:
                    mini_bosses = self.level_config.get("mini_bosses", {})
                if self.wave_number in mini_bosses:
                    self.pending_mini_bosses.append(
                        (self.wave_number, mini_bosses[self.wave_number]))
                self._try_spawn_pending_mini_boss()
                # ═══ AUTO CASTLE LEVEL UP untuk AI berdasarkan wave ═══
                self._auto_scale_ai_castle()
                # ═══ TAMBAH: Wave Announcer (Tier 2) ═══
                self.effects.announce_wave(self.wave_number)
                # ═══ TAMBAH: Show path preview ═══
                lane_paths = [
                    self.map_renderer.get_lane_path("top"),
                    self.map_renderer.get_lane_path("mid"),
                    self.map_renderer.get_lane_path("bot"),
                ]
                self.effects.show_path_preview(lane_paths)
                # ═══════════════════════════════════════
                # ═══ WAVE COMPOSITION (dengan scaling late-game) ═══
                blue_comp = self._get_wave_composition("blue")
                red_comp = self._get_wave_composition("red")
                for lane in ["top", "mid", "bot"]:
                    for mtype in blue_comp:
                        self.spawn_queue_blue.append((mtype, lane))
                    for mtype in red_comp:
                        self.spawn_queue_red.append((mtype, lane))
                self.wave_timer = MINION_WAVE_INTERVAL

        self.spawn_timer_blue += 1
        if self.spawn_timer_blue >= MINION_SPAWN_DELAY and self.spawn_queue_blue:
            self.spawn_timer_blue = 0
            mtype, lane = self.spawn_queue_blue.pop(0)
            lane_path = self.map_renderer.get_lane_path(lane)
            m = Minion(mtype, "blue", lane,
                       self.blue_base.level, lane_path)
            self.minions.append(m)

        self.spawn_timer_red += 1
        if self.spawn_timer_red >= MINION_SPAWN_DELAY and self.spawn_queue_red:
            self.spawn_timer_red = 0
            mtype, lane = self.spawn_queue_red.pop(0)
            lane_path = self.map_renderer.get_lane_path(lane)
            m = Minion(mtype, "red", lane,
                       self.red_base.level, lane_path)

            # ═══ APPLY LEVEL SCALING (enemy only) ═══
            cfg = self.level_config
            m.max_hp = int(m.max_hp * cfg["enemy_hp_mult"])
            m.hp = m.max_hp
            m.damage = int(m.damage * cfg["enemy_damage_mult"])
            m.speed *= cfg["enemy_speed_mult"]
            m.base_speed = m.speed

            self.minions.append(m)

            # ═══ TAMBAH: Wave achievements ═══
        if self.wave_number == 5:
            self._unlock_achievement(
                "wave_5", "Survivor",
                "Reached wave 5", "shield")
        elif self.wave_number == 10:
            self._unlock_achievement(
                "wave_10", "Veteran",
                "Reached wave 10", "shield")
        elif self.wave_number == 20:
            self._unlock_achievement(
                "wave_20", "Endless Warrior",
                "Reached wave 20", "shield")

    def _try_spawn_pending_mini_boss(self):
        """Spawn mini boss tertunda saat boss sebelumnya sudah selesai.

        Wave tidak diulang dan mini boss tidak hilang hanya karena true boss
        atau mini boss lain masih aktif.
        """
        if self.active_boss is not None:
            if getattr(self.active_boss, "alive", True):
                return
            self.active_boss = None

        if not self.pending_mini_bosses:
            return

        _wave, boss_type = self.pending_mini_bosses.pop(0)
        from bosses.base_boss import Boss
        lane_path = self.map_renderer.get_lane_path("mid")
        self.active_boss = Boss(boss_type, lane_path)

        from _render import BossIntroCinematic
        self.boss_intro = BossIntroCinematic(
            self.active_boss, SCREEN_WIDTH, SCREEN_HEIGHT)
        print(f"[MINI BOSS] {self.active_boss.name} spawned")

    def _roll_mini_boss_schedule(self):
        """Acak wave kemunculan mini boss tiap run.

        Jumlah & TIPE boss mengikuti level config (biasanya 3 mini boss),
        tapi NOMOR WAVE-nya diacak di rentang 6..30 (tidak lagi tetap
        10/18/25). Boss terkuat tetap muncul di wave terakhir dari jadwal
        supaya progresif. True boss (level config) tidak terkena ini.
        """
        import random as _r
        src = self.level_config.get("mini_bosses", {})
        if not src:
            return {}
        bosses = list(src.values())   # tipe boss dipertahankan urutannya
        n = len(bosses)
        low, high = 6, 30
        # Pastikan rentang cukup untuk N wave berbeda
        if high - low + 1 < n:
            high = low + n * 5
        waves = sorted(_r.sample(range(low, high + 1), n))
        return dict(zip(waves, bosses))

    def _auto_scale_ai_castle(self):
        """
        AI castle auto-upgrade berdasarkan wave untuk balancing.
        Player harus proactive upgrade sendiri.
        """
        target_level = 1
        if self.wave_number >= 4:
            target_level = 2
        if self.wave_number >= 7:
            target_level = 3
        if self.wave_number >= 10:
            target_level = 4
        if self.wave_number >= 13:
            target_level = 5

        # Upgrade AI castle jika belum lvl target
        while self.red_base.level < target_level:
            self.red_base.upgrade()

    def _get_wave_composition(self, team):
        """
        Get minion composition dengan dynamic scaling.
        Wave 1-5: dari NEXUS_WAVE_COMPOSITION
        Wave 6+: extended waves dengan lebih banyak elite
        """
        base = self.blue_base if team == "blue" else self.red_base
        castle_level = base.level

        # Base composition dari castle level
        base_comp = NEXUS_WAVE_COMPOSITION[castle_level].copy()

        # ═══ SCALING per WAVE NUMBER ═══
        if self.wave_number <= 3:
            # Wave 1-3: seperti biasa
            return base_comp

        elif self.wave_number <= 6:
            # Wave 4-6: +1 unit lagi
            base_comp.append("orc")
            return base_comp

        elif self.wave_number <= 9:
            # Wave 7-9: +2 units, tambah undead
            base_comp.append("orc")
            base_comp.append("undead")
            return base_comp

        elif self.wave_number <= 12:
            # Wave 10-12: +3 units, ada troll & dark rider
            base_comp.append("troll")
            base_comp.append("dark_rider")
            base_comp.append("undead")
            return base_comp

        else:
            # Wave 13+: BOSS WAVE! elite units
            base_comp.append("troll")
            base_comp.append("troll")
            base_comp.append("dark_rider")
            base_comp.append("dark_rider")
            base_comp.append("undead")
            return base_comp

    def update(self):
        if self.state != "playing":
            return

        # ═══ GAME SPEED (dari settings) ═══
        # Skip cinematic - cinematic tetap normal speed
        if not (self.boss_intro and self.boss_intro.is_active()) and \
                not (self.level_intro and self.level_intro.is_active()):
            _settings = GameSettings()
            speed_mult = _settings.game_speed

            # Kalau speed != 1.0, run update multiple times (untuk speed up)
            # atau skip frames (untuk slow down)
            if speed_mult > 1.0:
                # Run extra updates (2x, 3x, dll)
                extra_updates = int(speed_mult) - 1
                for _ in range(extra_updates):
                    self._update_gameplay()
            elif speed_mult < 1.0:
                # Skip frame (0.5x = update tiap 2 frame)
                if not hasattr(self, '_speed_skip_counter'):
                    self._speed_skip_counter = 0
                self._speed_skip_counter += 1
                if self._speed_skip_counter % 2 == 0:
                    return  # skip this update
        # ═══ PAUSE GAMEPLAY saat level intro aktif ═══
        if self.level_intro and self.level_intro.is_active():
            self.level_intro.update()
            self.animation_time += 1
            return

            # Reset level_intro kalau sudah selesai
        if self.level_intro and not self.level_intro.is_active():
            self.level_intro = None

        # ═══ BOSS INTRO (banner ringkas, TIDAK pause gameplay) ═══
        if self.boss_intro:
            if self.boss_intro.is_active():
                self.boss_intro.update()
            else:
                self.boss_intro = None

        # ═══ PAUSE GAMEPLAY saat boss death animation aktif ═══
        if self.boss_death and self.boss_death.is_death_active():
            self.boss_death.update()
            self.animation_time += 1
            return

        # Update celebration tapi tidak pause gameplay
        if self.boss_death and not self.boss_death.is_active():
            self.boss_death = None
        elif self.boss_death:
            self.boss_death.update()

        self.animation_time += 1
        if self.animation_time % 2 == 0:
            spatial_heroes = self.get_all_heroes()
            if self.active_boss and self.active_boss.alive:
                spatial_heroes = spatial_heroes + [self.active_boss]
            update_spatial_grid(
                self.minions,
                spatial_heroes,
                self.towers
            )

        # ═══ TAMBAH: Track mouse & hover ═══
        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
        self.ui.update_hover_states()
        # ═══ TAMBAH: Update popup animation ═══
        if hasattr(self, 'popup_anim'):
            self.popup_anim.update()

        self.gold_timer += 1
        if self.gold_timer >= 60:
            self.gold_timer = 0
            self.gold += GOLD_PER_SECOND
            # AI income naik tiap wave supaya AI bisa menabung untuk
            # membeli boss hero dari level-level di bawahnya.
            # AI gets same base income + wave bonus to afford boss heroes (parity)
            self.ai.gold += GOLD_PER_SECOND + max(0, self.wave_number)
        # ═══ TAMBAH: Gold achievements ═══
        if self.gold >= 1000:
            self._unlock_achievement(
                "gold_1000", "Wealthy",
                "Accumulated 1000 gold", "gold")
        if self.gold >= 5000:
            self._unlock_achievement(
                "gold_5000", "Rich",
                "Accumulated 5000 gold", "gold")
        self.update_waves()

        all_heroes = self.get_all_heroes()

        # ═══ BUILD UNIT LIST (termasuk boss!) ═══
        all_units = self.minions + all_heroes
        if self.active_boss and self.active_boss.alive:
            all_units = all_units + [self.active_boss]

        # ═══ UPDATE ENTITIES ═══
        for m in self.minions:
            m.update(all_units, self.towers, self.bases)

        for t in self.towers:
            t.update(all_units, self.towers, self.bases)

        for b in self.bases:
            b.update(all_units)

        for h in all_heroes:
            h.update(all_units, self.towers, self.bases)

        # ═══ TRUE BOSS CHECK (dari level config) ═══
        if not self.true_boss_spawned and self.wave_number >= 5:
            red_towers_alive = sum(1 for t in self.towers
                                   if t.team == "red" and t.alive)
            if red_towers_alive <= 3 and not self.active_boss:
                true_boss_type = self.level_config.get("true_boss")
                if true_boss_type:
                    from bosses.base_boss import Boss
                    lane_path = self.map_renderer.get_lane_path("mid")
                    self.active_boss = Boss(true_boss_type, lane_path)
                    self.true_boss_spawned = True
                    print(f"[TRUE BOSS Lv.{self.level_number}] "
                          f"{self.active_boss.name} spawned!")

                    # ═══ TRIGGER BOSS INTRO (TRUE BOSS) ═══
                    from _render import BossIntroCinematic
                    self.boss_intro = BossIntroCinematic(
                        self.active_boss, SCREEN_WIDTH, SCREEN_HEIGHT)

        # ═══ BOSS UPDATE (DI LUAR loop!) ═══
        if self.active_boss and self.active_boss.alive:
            self.active_boss.update(
                all_units, self.towers, self.bases)

        # ═══ BOSS DEFEATED → UNLOCK HERO (DI LUAR loop!) ═══
        if self.active_boss and not self.active_boss.alive \
                and self.active_boss.defeated:
            boss = self.active_boss
            boss_type = boss.boss_type

            # ═══ TRIGGER DEATH ANIMATION ═══
            from _render import BossDeathAnimation
            self.boss_death = BossDeathAnimation(
                boss, SCREEN_WIDTH, SCREEN_HEIGHT)

            self.gold += boss.gold_reward
            self.score += boss.gold_reward
            self.effects.add_gold_popup(
                boss.x, boss.y, boss.gold_reward)
            ...

            if boss_type not in self.unlocked_bosses:
                self.unlocked_bosses.append(boss_type)

                prefix = "TRUE BOSS" if boss.boss_class == "true" \
                    else "BOSS"
                self.effects.unlock_achievement(
                    f"{prefix}: {boss.name} Defeated!",
                    f"{boss.name} unlocked as hero!",
                    "skull")

                from _system import SaveManager
                self.save_data['unlocked_bosses'] = self.unlocked_bosses
                SaveManager.save(self.save_data)

            self.effects.register_kill(
                killer_name="Blue Team",
                victim_name=f"BOSS {boss.name}",
                killer_team="blue")

            self.active_boss = None
            self._try_spawn_pending_mini_boss()

        for h in all_heroes:
            if not h.alive and h not in self.hero_respawn_timers:
                self.hero_respawn_timers[h] = 600

        to_respawn = []
        for h, timer in list(self.hero_respawn_timers.items()):
            timer -= 1
            if timer <= 0:
                to_respawn.append(h)
            else:
                self.hero_respawn_timers[h] = timer

        for h in to_respawn:
            h.respawn()
            del self.hero_respawn_timers[h]

        for m in self.minions:
            if not m.alive and not getattr(m, "_rewarded", False):
                m._rewarded = True
                if m.team == "red":
                    self.gold += m.gold_reward
                    self.score += m.gold_reward
                    self.effects.add_gold_popup(m.x, m.y, m.gold_reward)
                    # ═══ ACHIEVEMENT TRACKING ═══
                    self.total_kills += 1

                    # First Blood
                    if not self.first_blood:
                        self.first_blood = True
                        self._unlock_achievement(
                            "first_blood",
                            "First Blood!",
                            "Killed your first enemy",
                            "sword")

                    # Kill milestones
                    if self.total_kills == 10:
                        self._unlock_achievement(
                            "10_kills", "Getting Started",
                            "Killed 10 enemies", "skull")
                    elif self.total_kills == 50:
                        self._unlock_achievement(
                            "50_kills", "Slayer",
                            "Killed 50 enemies", "skull")
                    elif self.total_kills == 100:
                        self._unlock_achievement(
                            "100_kills", "Executioner",
                            "Killed 100 enemies", "skull")
                    elif self.total_kills == 250:
                        self._unlock_achievement(
                            "250_kills", "Warlord",
                            "Killed 250 enemies", "skull")

                    # Combo tracking
                    current_combo = self.effects.combo_counter.count
                    if current_combo > self.max_combo:
                        self.max_combo = current_combo
                        # (notifikasi combo dikirim dari
                        #  ComboCounter.add_kill di _render.py, di
                        #  ambang tier saja - lihat komentar di sana)

                        if current_combo == 5:
                            self._unlock_achievement(
                                "combo_5", "Combo Master",
                                "Achieved 5 kill combo", "star")
                        elif current_combo == 10:
                            self._unlock_achievement(
                                "combo_10", "Killing Spree",
                                "Achieved 10 kill combo", "star")
                        elif current_combo == 20:
                            self._unlock_achievement(
                                "combo_20", "GODLIKE!",
                                "Achieved 20 kill combo!", "star")

                    # ═══ TAMBAH: Combo & Kill Feed ═══
                    minion_names = {
                        'goblin': 'Goblin',
                        'orc': 'Orc',
                        'troll': 'Troll',
                        'undead': 'Undead',
                        'dark_rider': 'Dark Rider',
                    }
                    victim_name = minion_names.get(m.minion_type,
                                                   m.minion_type.title())
                    self.effects.register_kill(
                        killer_name="Blue Tower",
                        victim_name=victim_name,
                        killer_team="blue")
                else:
                    self.ai.gold += m.gold_reward
                    # AI kill feed
                    minion_names = {
                        'goblin': 'Goblin', 'orc': 'Orc',
                        'troll': 'Troll', 'undead': 'Undead',
                        'dark_rider': 'Dark Rider',
                    }
                    victim_name = minion_names.get(m.minion_type,
                                                   m.minion_type.title())
                    self.effects.register_kill(
                        killer_name="Red Tower",
                        victim_name=victim_name,
                        killer_team="red")

        for t in self.towers:
            if not t.alive and not getattr(t, "_rewarded", False):
                t._rewarded = True
                if t.team == "red":
                    self.gold += t.gold_reward
                    self.score += t.gold_reward
                else:
                    self.ai.gold += t.gold_reward

        for h in all_heroes:
            if not h.alive and not getattr(h, "_rewarded", False):
                h._rewarded = True
                hero_reward = 150
                if h.team == "red":
                    self.gold += hero_reward
                    self.score += hero_reward
                else:
                    self.ai.gold += hero_reward
        # ═══ TAMBAH: Update effects ═══
        self.effects.update()

        self.minions = [m for m in self.minions
                        if m.alive or (hasattr(m, 'death_anim') and m.death_anim > 0)]
        self.towers = [t for t in self.towers if t.alive]

        for h in all_heroes:
            if h.alive and getattr(h, "_rewarded", False):
                h._rewarded = False

        # Pass reference towers list ke AI (untuk build)
        self.ai._towers_ref = self.towers

        self.ai.update(
            self.towers, self.minions, all_heroes,
            self.red_base, self.bases,
            build_slots=self.build_slots_red)

        if self.blue_base.hp < self._blue_nexus_last_hp:
            SoundManager().play('nexus_hit', volume_mult=0.7)
            # Controller rumble saat castle kena damage
            if hasattr(self, 'controller_mgr') and self.controller_mgr:
                self.controller_mgr.rumble(0.6, 15)
        self._blue_nexus_last_hp = self.blue_base.hp

        if not self.blue_base.alive and self.state == "playing":
            self.state = "defeat"
            self._grant_meta_reward(victory=False)
            SoundManager().stop_bgm(fade_ms=500)
            SoundManager().play('defeat')

        elif not self.red_base.alive and self.state == "playing":
            self.state = "victory"
            self._grant_meta_reward(victory=True)
            SoundManager().stop_bgm(fade_ms=500)
            SoundManager().play('victory')

    def _update_gameplay(self):
        """
        Run gameplay update sekali (untuk speed multiplier).
        Simplified version - update entities saja tanpa UI.
        """
        all_heroes = self.get_all_heroes()
        all_units = self.minions + all_heroes
        if self.active_boss and self.active_boss.alive:
            all_units = all_units + [self.active_boss]

        # Update entities
        for m in self.minions:
            m.update(all_units, self.towers, self.bases)
        for t in self.towers:
            t.update(all_units, self.towers, self.bases)
        for b in self.bases:
            b.update(all_units)
        for h in all_heroes:
            h.update(all_units, self.towers, self.bases)
        if self.active_boss and self.active_boss.alive:
            self.active_boss.update(
                all_units, self.towers, self.bases)

    def _grant_meta_reward(self, victory):
        if self._meta_reward_granted:
            return

        # ═══ KEBIJAKAN REWARD (flat untuk SEMUA level) ═══
        # - Kalah                          : 0 gold
        # - Menang pertama kali level ini  : 3000 gold (dari level config)
        # - Replay menang (pertama kali)   : 1500 gold (sekali saja)
        # - Replay menang berikutnya       : 0 gold
        if not victory:
            reward = 0
        else:
            cfg = self.level_config or {}
            win_reward = int(cfg.get("meta_gold_reward_win", 3000))
            replay_reward = int(cfg.get("meta_gold_reward_replay", 1500))
            completed = self.save_data.setdefault('completed_levels', [])
            replay_counts = self.save_data.setdefault(
                "replay_reward_counts", {})
            replay_key = str(self.level_number)
            replay_count = int(replay_counts.get(replay_key, 0))
            if getattr(self, "is_replay", False) or \
                    self.level_number in completed:
                reward = replay_reward if replay_count == 0 else 0
                replay_counts[replay_key] = replay_count + 1
            else:
                reward = win_reward

        self.meta_reward_earned = reward
        self.save_data['meta_gold'] = self.save_data.get(
            'meta_gold', 0) + reward

        # ═══ MARK LEVEL AS COMPLETED (if victory) ═══
        if victory:
            completed = self.save_data.setdefault('completed_levels', [])
            if self.level_number not in completed:
                completed.append(self.level_number)
                print(f"[LEVEL] Level {self.level_number} completed!")

            # Update last played level
            self.save_data['last_played_level'] = self.level_number

        # ═══ SAVE LEVEL STATS ═══
        import time as _time
        from _system import SaveManager

        match_time = int(_time.time() - self.match_start_time)

        match_stats = {
            'won': victory,
            'score': self.score,
            'time_seconds': match_time,
            'kills': self.total_kills,
            'combo': self.max_combo,
            'playtime_seconds': match_time,
        }

        result = SaveManager.update_level_stats(
            self.save_data, self.level_number, match_stats)

        # Save flags for UI display
        self.new_best_score = result['is_new_best_score']
        self.new_best_time = result['is_new_best_time']

        SaveManager.save(self.save_data)

        self._meta_reward_granted = True

    def _unlock_achievement(self, achievement_id, title, description,
                            icon="star"):
        """Unlock achievement if not already unlocked"""
        if achievement_id in self.achievements_unlocked:
            return
        self.achievements_unlocked.add(achievement_id)
        self.effects.unlock_achievement(title, description, icon)
        SoundManager().play('ui_upgrade', volume_mult=0.5)

    def handle_click(self, pos, button):
        """Delegate ke InputHandler"""
        # ═══ SCROLL WHEEL untuk Hero Shop ═══
        # `_shop_scroll` baru dibuat di fungsi draw shop. Kalau event
        # scroll datang lebih dulu, dulu scroll-nya hilang diam-diam.
        # Sekarang atributnya dibuat di sini kalau belum ada.
        if self.shop_open and button in (4, 5):
            if not hasattr(self, '_shop_scroll'):
                self._shop_scroll = 0
            if button == 4:
                self._shop_scroll = max(0, self._shop_scroll - 50)
            else:
                self._shop_scroll += 50
            return

        # ═══ LEVEL INTRO SKIP ═══
        if self.level_intro and self.level_intro.is_active():
            if self.level_intro.handle_skip(click=True):
                return
        # ═══ BOSS INTRO SKIP ═══
        if self.boss_intro and self.boss_intro.is_active():
            if self.boss_intro.handle_skip(click=True):
                return
        # ═══ BOSS DEATH CELEBRATION SKIP ═══
        if self.boss_death and self.boss_death.celebration_active:
            if self.boss_death.handle_skip(click=True):
                return

        self.input.handle_click(pos, button)

    def open_popup(self, target, ptype):
        self.close_popup()
        self.popup_target = target
        self.popup_type = ptype
        # ═══ TAMBAH: Popup animation ═══
        if not hasattr(self, 'popup_anim'):
            from _render import PopupAnimation
            self.popup_anim = PopupAnimation()
        self.popup_anim.show()
        if ptype == "tower":
            target.selected = True
            self.selected_tower = target

    def close_popup(self):
        if self.selected_tower:
            self.selected_tower.selected = False
            self.selected_tower = None
        self.popup_target = None
        self.popup_type = None
        # Hide animation
        if hasattr(self, 'popup_anim'):
            self.popup_anim.hide()

    def try_buy_hero(self, hero_type):
        all_heroes = get_all_hero_types()

        # Validasi: hero harus sudah di-unlock permanen
        if hero_type not in self.purchased_heroes:
            SoundManager().play('ui_error')
            return

        # Cek duplikat
        if any(h.hero_type == hero_type for h in self.heroes):
            SoundManager().play('ui_error')
            return

        # Cek max heroes
        if len(self.heroes) >= MAX_HEROES_OWNED:
            SoundManager().play('ui_error')
            return

        stats = all_heroes[hero_type]

        # ═══ CEK GOLD IN-GAME ═══
        cost = stats.get("cost", 400)
        if self.gold < cost:
            SoundManager().play('ui_error')
            return

        # ═══ BAYAR GOLD ═══
        self.gold -= cost

        # ═══ SUMMON HERO ═══
        shop_pos = self.map_renderer.radiant_shop_pos
        offset = len(self.heroes) * 30 - 30
        new_hero = Hero(hero_type, "blue",
                        shop_pos[0] + 80 + offset,
                        shop_pos[1] + 10)
        self.heroes.append(new_hero)
        self.shop_open = False
        SoundManager().play('ui_buy')
        SoundManager().play('hero_spawn')

    def try_upgrade_nexus(self):
        if self.blue_base.level >= MAX_NEXUS_LEVEL:
            SoundManager().play('ui_error')
            return
        cost = self.blue_base.upgrade_cost()
        if self.gold >= cost:
            if self.blue_base.upgrade():
                self.gold -= cost
                SoundManager().play('ui_upgrade')
        else:
            SoundManager().play('ui_error')

    def handle_key(self, key):
        """Delegate ke DevMode dulu, lalu InputHandler"""
        # ═══ LEVEL INTRO SKIP ═══
        if self.level_intro and self.level_intro.is_active():
            if self.level_intro.handle_skip(key=key):
                return
        # ═══ BOSS INTRO SKIP ═══
        if self.boss_intro and self.boss_intro.is_active():
            if self.boss_intro.handle_skip(key=key):
                return
        # ═══ BOSS DEATH CELEBRATION SKIP ═══
        if self.boss_death and self.boss_death.celebration_active:
            if self.boss_death.handle_skip(key=key):
                return

        # Dev hotkeys punya prioritas
        if self.dev.handle_hotkey(key):
            return

        # Normal keys
        self.input.handle_key(key)

    def _draw_input_hints(self, surface):
        """
        Hint bar tombol di bawah layar.

        Hanya digambar saat controller mode (pemain keyboard sudah
        hafal QWER dan hint bar cuma menuhin layar). Bisa dimatikan
        lewat self.show_input_hints = False.
        """
        if not getattr(self, 'show_input_hints', True):
            return

        mgr = getattr(self, 'controller_mgr', None)
        if mgr is None or not mgr.is_controller_mode():
            return

        # Cinematic aktif -> prompt skip sudah digambar sendiri
        if self.level_intro and self.level_intro.is_active():
            return
        if self.boss_intro and self.boss_intro.is_active():
            return
        if self.boss_death and self.boss_death.celebration_active:
            return

        if self.state == "victory":
            ctx = 'victory'
        elif self.state == "defeat":
            ctx = 'defeat'
        elif self.shop_open:
            ctx = 'shop'
        else:
            ctx = 'game'

        try:
            mgr.draw_hint_bar(surface, context=ctx)
        except Exception:
            pass

    def _input_label(self, gameplay_action):
        """
        Label tombol untuk sebuah aksi, otomatis ikut input mode.

        Controller aktif -> 'A' / 'RB' / 'VIEW'
        Keyboard         -> 'N' / 'R'  / 'ESC'
        """
        mgr = getattr(self, 'controller_mgr', None)
        if mgr is not None:
            try:
                return mgr.get_action_label(gameplay_action)
            except Exception:
                pass
        fallback = {'replay': 'R', 'next_level': 'N',
                    'to_menu': 'ESC', 'shop': 'H',
                    'skip': 'SPACE', 'pause': 'ESC'}
        return fallback.get(gameplay_action, '?')

    def _draw_gold_hud(self, surface):
        """Gold HUD - English, fixed no overlap, responsive width"""
        x, y = 18, 22
        # Dynamic width based on gold amount
        gold_str = f"{self.gold:,}"
        font = get_font(20)
        # Calculate needed width: icon 30 + text width + padding
        needed_w = 40 + font.size(gold_str)[0] + 20
        width = max(140, min(200, needed_w))
        height = 42

        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        panel.fill((8, 7, 12, 225))
        pygame.draw.rect(panel, (125, 90, 25), panel.get_rect(), 2, border_radius=8)
        pygame.draw.rect(panel, (255, 205, 70), (2, 2, width - 4, 2), border_radius=3)

        # Coin icon
        pygame.draw.circle(panel, (110, 70, 12), (20, 20), 11)
        pygame.draw.circle(panel, (245, 190, 52), (19, 19), 9)
        pygame.draw.circle(panel, (255, 235, 125), (16, 16), 3)
        pygame.draw.line(panel, (167, 112, 24), (19, 13), (19, 26), 2)

        small_font = get_font(12)
        gold_text = font.render(gold_str, True, (255, 231, 133))
        surface.blit(panel, (x, y))
        surface.blit(gold_text, (x + 38, y + 5))

        # Income on second line, left aligned under gold
        income = small_font.render(f"+{GOLD_PER_SECOND}/s income", True, (196, 241, 168))
        surface.blit(income, (x + 38, y + 26))

    def draw(self):
        """Main draw method - delegate ke UI Renderer"""
        # Get shake offset
        shake_x, shake_y = self.effects.get_shake_offset()

        # Setup draw target (dengan shake support)
        # Surface shake dipakai ulang, bukan alokasi baru tiap frame
        # (alokasi 1280x720 ~0.4 ms, sia-sia saat layar bergetar).
        if shake_x != 0 or shake_y != 0:
            if getattr(self, '_shake_surface', None) is None or \
                    self._shake_surface.get_size() != \
                    self.screen.get_size():
                # Ikut jalur cepat alpha kalau aktif, supaya saat layar
                # bergetar performanya tidak jatuh kembali.
                try:
                    from mobile import fastblit
                    self._shake_surface = fastblit.bungkus_seperti(
                        self.screen)
                except Exception:
                    self._shake_surface = pygame.Surface(
                        self.screen.get_size())
            temp_surface = self._shake_surface
            draw_target = temp_surface
        else:
            draw_target = self.screen

        # ═══ WORLD LAYER (kena shake) ═══
        from mobile.perf import PHASES as _PH
        _PH.mark("bg.fill")
        # Peta statis menutupi SELURUH layar, jadi fill ini tidak
        # pernah terlihat - murni 3 ms/frame terbuang di HP.
        # Tetap dijalankan sekali di awal untuk jaga-jaga.
        if getattr(self, "_bg_filled_once", 0) < 3:
            draw_target.fill(GRASS_DARK)
            self._bg_filled_once = getattr(self, "_bg_filled_once", 0) + 1
        _PH.mark("map")
        self.map_renderer.draw(draw_target, self.animation_time)

        # Build slots
        _PH.mark("slots")
        self.ui_buttons = {}
        self.ui.draw_build_slots(draw_target)

        # Entities (dipecah supaya ketahuan siapa yang mahal)
        _PH.mark("e.base")
        for b in self.bases:
            b.draw(draw_target)
        _PH.mark("e.tower")
        for t in self.towers:
            t.draw(draw_target)
        _PH.mark("e.minion")
        for m in self.minions:
            if FrustumCuller.is_visible(m.x, m.y, m.radius):
                m.draw(draw_target)
        _PH.mark("e.hero")
        for h in self.get_all_heroes():
            if FrustumCuller.is_visible(h.x, h.y, h.radius):
                h.draw(draw_target)

        _PH.mark("e.boss")
        # ═══ DRAW BOSS (di luar hero loop!) ═══
        if self.active_boss and self.active_boss.alive:
            if FrustumCuller.is_visible(self.active_boss.x,
                                        self.active_boss.y,
                                        self.active_boss.radius):
                self.active_boss.draw(draw_target)

        # Effects
        _PH.mark("effects")
        self.effects.draw(draw_target, self.animation_time)
        _PH.mark("hover")
        self.ui.draw_hover_indicators(draw_target)

        # Apply shake
        if shake_x != 0 or shake_y != 0:
            self.screen.fill((0, 0, 0))
            self.screen.blit(temp_surface, (shake_x, shake_y))

        # ═══ UI LAYER (tanpa shake) ═══
        _PH.mark("ui.hints")
        self.ui.draw_shop_hints(self.screen)
        _PH.mark("ui.gold")
        # Kalau panel kanan aktif, emas & wave sudah tampil di sana.
        # Panel melayang di atas peta jadi mubazir dan menutupi arena.
        if not _PANEL_AKTIF():
            self._draw_gold_hud(self.screen)
        _PH.mark("ui.rest")
        # Boss intro banner (ringkas, di atas) digambar SEBELUM
        # effects.draw_ui supaya wave announcer tidak pernah
        # tertutup banner boss.
        if self.boss_intro and self.boss_intro.is_active():
            self.boss_intro.draw(self.screen)
        self.effects.draw_ui(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT)

        # Popups
        if self.popup_target is not None:
            self.ui.draw_popup(self.screen)
        if self.build_popup_slot is not None:
            self.ui.draw_build_popup(self.screen)
        if self.shop_open:
            self.ui.draw_hero_shop(self.screen)
        if self.selected_hero and self.selected_hero.alive:
            self.ui.draw_hero_info(self.screen)

        # Dev UI (paling atas)
        _PH.mark("dev")
        self.dev.draw(self.screen)
        _PH.mark("tail")   # overlay menang/kalah, hint bar, intro, dst

        if self.state == "victory":
            from levels import get_next_level
            has_next = get_next_level(self.level_number) is not None

            # Label tombol ikut input mode (keyboard vs controller)
            nx = self._input_label('next_level')
            rp = self._input_label('replay')
            mn = self._input_label('to_menu')

            if has_next:
                action_text = (f"[{nx}] Next Level  [{rp}] Replay  "
                               f"[{mn}] Menu")
            else:
                action_text = (f"[{rp}] Replay  [{mn}] Menu  "
                               f"(You cleared all levels!)")

            self.ui.draw_overlay(
                self.screen,
                f"VICTORY! LV.{self.level_number}",
                GOLD,
                f"Score: {self.score} | +{self.meta_reward_earned} Hero Gold",
                action_text
            )

        elif self.state == "defeat":
            self.ui.draw_overlay(
                self.screen,
                f"DEFEAT LV.{self.level_number}",
                RED,
                f"Score: {self.score} | +{self.meta_reward_earned} Hero Gold",
                (f"[{self._input_label('replay')}] Retry  "
                 f"[{self._input_label('to_menu')}] Menu")
            )

        # ═══ HINT BAR TOMBOL (paling bawah layar) ═══
        # Otomatis menampilkan label keyboard atau controller.
        self._draw_input_hints(self.screen)

        # ═══ LEVEL INTRO SCREEN (paling atas dari yang lain) ═══
        if self.level_intro and self.level_intro.is_active():
            self.level_intro.draw(self.screen)
        # (Boss intro banner sudah digambar di UI layer di atas)
        # ═══ BOSS DEATH ANIMATION + CELEBRATION ═══
        if self.boss_death and self.boss_death.is_active():
            self.boss_death.draw(self.screen)
        _PH.end()




# ================================


# ====================================================================
# menu.py
# ====================================================================

# MENU.PY - Main Menu & Pause Menu
# ================================

import pygame
import math
import sys
from _system import SoundManager
from _system import SaveManager
from ui_components.hero_portraits import HeroPortraits

# Compatibility defaults agar menu tidak crash jika settings.py lama masih dipakai.
DEV_UNLIMITED_HERO_GOLD = globals().get("DEV_UNLIMITED_HERO_GOLD", False)
DEV_TOPUP_ENABLED = globals().get("DEV_TOPUP_ENABLED", False)

class MenuState:
    """State constants untuk menu"""
    MAIN = "main"
    HOW_TO_PLAY = "how_to_play"
    SETTINGS = "settings"
    CREDITS = "credits"
    PAUSE = "pause"
    HERO_SHOP = "hero_shop"
    LEVEL_SELECT = "level_select"
    SLOT_SELECT = "slot_select"


class Menu:
    """
    Handle semua menu system:
    - Main menu (before game)
    - Pause menu (during game)
    - Settings, credits, how to play
    """

    def __init__(self, screen):
        self.screen = screen

        # Fonts (profesional: Cinzel judul, Barlow body)
        # 72 = ukuran aman utk layar 1280x720 (Cinzel 96 terlalu besar
        # & membuat teks keluar layar / bertabrakan)
        self.font_title = title_font(72)
        self.font_subtitle = get_font(32, "body_semibold")
        self.font_button = get_font(42, "body_bold")
        self.font_medium = get_font(26, "body_semibold")
        self.font_small = get_font(20, "body_medium")
        self.font_tiny = get_font(16, "body")

        self.controller_mgr = None
        self.save_data = SaveManager.load()
        self.meta_gold = self.save_data.get("meta_gold", 0)
        self.selected_level = 1  # level yang dipilih user
        self.slot_delete_confirm = None  # slot yang mau dihapus (None kalau tidak ada)
        self.reset_confirm = False

        # State
        self.state = MenuState.MAIN
        self.active = True  # menu aktif atau tidak
        self.pause_mode = False  # true kalau pause menu (bukan main menu)

        # Animation
        self.animation_time = 0
        self.hover_button = None

        # Buttons cache
        self.buttons = {}

        # Result untuk komunikasi dengan main.py
        self.action = None  # "play", "quit", "resume", "main_menu"

        # Particles background
        self.particles = self._init_particles()

    def _draw_slot_select(self):
        """Slot selection screen"""
        from _system import SaveManager, NUM_SLOTS

        cx = SCREEN_WIDTH // 2

        # ═══ TITLE ═══
        title = self.font_title.render(
            "SELECT SAVE GAME", True, (255, 220, 100))
        title_rect = title.get_rect(center=(cx, 60))
        self._blit_shadow(self.screen, title, title_rect.topleft)
        self.screen.blit(title, title_rect)

        # ═══ SUBTITLE ═══
        subtitle = self.font_small.render(
            "Choose a save game to continue or start new",
            True, (180, 200, 220))
        subtitle_rect = subtitle.get_rect(center=(cx, 135))
        self.screen.blit(subtitle, subtitle_rect)

        # ═══ SLOT CARDS ═══
        all_slots = SaveManager.get_all_slot_info()

        card_w = 320
        card_h = 460
        gap_x = 30

        total_w = NUM_SLOTS * card_w + (NUM_SLOTS - 1) * gap_x
        start_x = cx - total_w // 2
        start_y = 170

        for i in range(NUM_SLOTS):
            slot_num = i + 1
            slot_info = all_slots[i]
            x = start_x + i * (card_w + gap_x)
            y = start_y

            self._draw_slot_card(slot_num, slot_info, x, y,
                                 card_w, card_h)

        # ═══ BACK BUTTON ═══
        self._draw_menu_button("slot_back", "BACK",
                               cx, SCREEN_HEIGHT - 40,
                               (150, 150, 150),
                               width=220, height=42)

        # ═══ DELETE CONFIRMATION DIALOG ═══
        if self.slot_delete_confirm is not None:
            self._draw_delete_confirm_dialog()

    def _draw_slot_card(self, slot_num, slot_info, x, y, w, h):
        """Draw single slot card"""
        from _system import SaveManager

        is_empty = slot_info is None

        # Hover detection
        mx, my = pygame.mouse.get_pos()
        card_rect = pygame.Rect(x, y, w, h)
        is_hover = card_rect.collidepoint(mx, my)

        # ═══ CARD BG ═══
        if is_empty:
            bg_color = (35, 40, 55)
            border_color = (100, 130, 170)
        else:
            bg_color = (30, 45, 30)
            border_color = (100, 220, 100)

        # Shadow
        shadow_surf = pygame.Surface((w + 8, h + 8), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 150),
                         (4, 4, w, h), border_radius=12)
        self.screen.blit(shadow_surf, (x - 4, y - 4))

        pygame.draw.rect(self.screen, bg_color,
                         (x, y, w, h), border_radius=12)

        # Hover glow
        if is_hover:
            glow_surf = pygame.Surface((w + 20, h + 20),
                                       pygame.SRCALPHA)
            pygame.draw.rect(glow_surf,
                             (*border_color, 80),
                             (0, 0, w + 20, h + 20),
                             border_radius=15)
            self.screen.blit(glow_surf, (x - 10, y - 10))
            border_color = (255, 255, 255)

        # Border
        border_w = 3 if is_hover else 2
        pygame.draw.rect(self.screen, border_color,
                         (x, y, w, h), border_w, border_radius=12)

        # ═══ SAVE GAME LABEL (big top) ═══
        # Small "SAVE GAME" label
        label_font = get_font(24)
        label_text = label_font.render(
            "SAVE GAME", True,
            (150, 170, 200) if is_empty else (200, 180, 100))
        label_rect = label_text.get_rect(
            center=(x + w // 2, y + 26))
        self.screen.blit(label_text, label_rect)

        # Big number (lebih ramah: font 90 terlalu tinggi -> tabrakan)
        num_font = get_font(58, 'body_bold')

        if is_empty:
            num_color = (100, 130, 170)
        else:
            num_color = (255, 220, 100)

        # Shadow
        num_shadow = num_font.render(
            str(slot_num), True, (0, 0, 0))
        num_shadow_rect = num_shadow.get_rect(
            center=(x + w // 2, y + 78))
        self.screen.blit(num_shadow,
                         (num_shadow_rect.x + 2,
                          num_shadow_rect.y + 2))

        num_text = num_font.render(
            str(slot_num), True, num_color)
        num_rect = num_text.get_rect(center=(x + w // 2, y + 78))
        self.screen.blit(num_text, num_rect)

        # ═══ DECORATIVE LINE ═══
        pygame.draw.line(self.screen, border_color,
                         (x + 30, y + 132),
                         (x + w - 30, y + 132), 2)

        # ═══ SLOT CONTENT ═══
        if is_empty:
            # ═══ EMPTY SLOT ═══
            self._draw_empty_slot_content(x, y, w, h)
        else:
            # ═══ EXISTING SLOT INFO ═══
            self._draw_slot_content(x, y, w, h, slot_info)

        # ═══ ACTION BUTTONS ═══
        self._draw_slot_action_buttons(slot_num, slot_info, x, y, w, h)

    def _draw_empty_slot_content(self, x, y, w, h):
        """Draw content untuk empty slot"""
        cx = x + w // 2

        # Empty icon (plus symbol)
        icon_y = y + 210
        icon_size = 60

        # Circle bg
        pygame.draw.circle(self.screen, (60, 70, 90),
                           (cx, icon_y), icon_size // 2)
        pygame.draw.circle(self.screen, (100, 130, 170),
                           (cx, icon_y), icon_size // 2, 2)

        # Plus symbol
        plus_thick = 4
        pygame.draw.rect(self.screen, (150, 180, 220),
                         (cx - 15, icon_y - plus_thick // 2,
                          30, plus_thick))
        pygame.draw.rect(self.screen, (150, 180, 220),
                         (cx - plus_thick // 2, icon_y - 15,
                          plus_thick, 30))

        # Text
        empty_font = get_font(28)
        empty_text = empty_font.render(
            "EMPTY", True, (150, 180, 220))
        empty_rect = empty_text.get_rect(
            center=(cx, y + 290))
        self.screen.blit(empty_text, empty_rect)

        # Sub text
        hint_font = get_font(18)
        hint_text = hint_font.render(
            "Tap to start new game",
            True, (120, 140, 170))
        hint_rect = hint_text.get_rect(
            center=(cx, y + 318))
        self.screen.blit(hint_text, hint_rect)

    def _draw_slot_content(self, x, y, w, h, slot_info):
        """Draw content untuk slot yang ada save"""
        from _system import SaveManager
        from levels import get_level_config

        cx = x + w // 2
        content_y = y + 150

        # ═══ HIGHEST LEVEL ═══
        highest_lvl = slot_info['highest_level']
        if highest_lvl > 0:
            level_config = get_level_config(highest_lvl)
            level_name = level_config['name'] if level_config \
                else "Unknown"

            lvl_label = get_font(15).render(
                "HIGHEST LEVEL COMPLETED", True, (150, 170, 190))
            lvl_label_rect = lvl_label.get_rect(
                center=(cx, content_y))
            self.screen.blit(lvl_label, lvl_label_rect)

            lvl_num_font = get_font(30, 'body_bold')
            lvl_num_text = lvl_num_font.render(
                f"LV. {highest_lvl}", True, (255, 220, 100))
            lvl_num_rect = lvl_num_text.get_rect(
                center=(cx, content_y + 36))
            self.screen.blit(lvl_num_text, lvl_num_rect)

            # Nama level (truncate supaya muat di kartu 320px)
            lvl_name_font = get_font(17, 'body_medium')
            lvl_name_show = level_name
            if lvl_name_font.size(lvl_name_show)[0] > w - 40:
                while lvl_name_font.size(lvl_name_show + "...")[0] > w - 40                         and len(lvl_name_show) > 6:
                    lvl_name_show = lvl_name_show[:-1]
                lvl_name_show += "..."
            lvl_name_text = lvl_name_font.render(
                lvl_name_show, True, (200, 220, 240))
            lvl_name_rect = lvl_name_text.get_rect(
                center=(cx, content_y + 66))
            self.screen.blit(lvl_name_text, lvl_name_rect)
        else:
            # Belum ada level yang selesai
            no_progress = self.font_small.render(
                "No levels completed yet",
                True, (150, 170, 190))
            no_progress_rect = no_progress.get_rect(
                center=(cx, content_y + 35))
            self.screen.blit(no_progress, no_progress_rect)

        # ═══ META GOLD ═══
        gold_y = content_y + 102

        # Coin icon
        coin_x = cx - 60
        pygame.draw.circle(self.screen, (255, 200, 50),
                           (coin_x, gold_y + 3), 10)
        pygame.draw.circle(self.screen, (200, 150, 30),
                           (coin_x, gold_y + 3), 10, 2)

        coin_font = get_font(16)
        dollar = coin_font.render("$", True, (100, 60, 10))
        dollar_rect = dollar.get_rect(center=(coin_x, gold_y + 3))
        self.screen.blit(dollar, dollar_rect)

        # Gold amount
        gold_text = self.font_medium.render(
            f"{slot_info['meta_gold']:,} Gold",
            True, (255, 220, 100))
        self.screen.blit(gold_text, (coin_x + 15, gold_y - 5))

        # ═══ HEROES UNLOCKED ═══
        heroes_y = gold_y + 35
        heroes_count = len(slot_info['purchased_heroes'])
        heroes_text = self.font_small.render(
            f"⚔ Heroes: {heroes_count}",
            True, (150, 220, 255))
        heroes_rect = heroes_text.get_rect(center=(cx, heroes_y))
        self.screen.blit(heroes_text, heroes_rect)

        # ═══ BOSSES DEFEATED ═══
        bosses_y = heroes_y + 25
        bosses_count = len(slot_info['unlocked_bosses'])
        bosses_text = self.font_small.render(
            f"💀 Bosses: {bosses_count}",
            True, (255, 150, 150))
        bosses_rect = bosses_text.get_rect(center=(cx, bosses_y))
        self.screen.blit(bosses_text, bosses_rect)

        # ═══ LAST PLAYED ═══
        last_played_y = bosses_y + 30

        last_played_font = get_font(15)
        last_played_label = last_played_font.render(
            "LAST PLAYED", True, (140, 160, 180))
        last_played_label_rect = last_played_label.get_rect(
            center=(cx, last_played_y))
        self.screen.blit(last_played_label, last_played_label_rect)

        last_played_str = SaveManager.format_last_played(
            slot_info['slot_last_played'])
        last_played_text = get_font(18).render(
            last_played_str, True, (200, 200, 220))
        last_played_rect = last_played_text.get_rect(
            center=(cx, last_played_y + 18))
        self.screen.blit(last_played_text, last_played_rect)

    def _draw_slot_action_buttons(self, slot_num, slot_info, x, y, w, h):
        """Draw play/delete buttons di card"""
        is_empty = slot_info is None

        # ═══ PLAY / CONTINUE BUTTON ═══
        play_btn_y = y + h - 85
        play_btn_rect = pygame.Rect(
            x + 20, play_btn_y, w - 40, 34)

        # Hover
        mx, my = pygame.mouse.get_pos()
        play_hover = play_btn_rect.collidepoint(mx, my)

        if is_empty:
            btn_color = (30, 100, 160) if play_hover else (25, 80, 130)
            border_col = (100, 180, 255) if play_hover else (80, 140, 200)
            btn_label = "START NEW GAME"
        else:
            btn_color = (40, 160, 60) if play_hover else (30, 130, 50)
            border_col = (120, 240, 130) if play_hover else (100, 200, 110)
            btn_label = "CONTINUE"

        # Glow if hover
        if play_hover:
            glow_surf = pygame.Surface(
                (play_btn_rect.width + 10, play_btn_rect.height + 10),
                pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*border_col, 100),
                             (0, 0, play_btn_rect.width + 10,
                              play_btn_rect.height + 10),
                             border_radius=8)
            self.screen.blit(glow_surf,
                             (play_btn_rect.x - 5,
                              play_btn_rect.y - 5))

        pygame.draw.rect(self.screen, btn_color,
                         play_btn_rect, border_radius=6)
        pygame.draw.rect(self.screen, border_col,
                         play_btn_rect, 2, border_radius=6)

        play_text = self.font_small.render(
            btn_label, True, (255, 255, 255))

        # Shadow
        play_shadow = self.font_small.render(
            btn_label, True, (0, 0, 0))
        play_rect = play_text.get_rect(center=play_btn_rect.center)
        self.screen.blit(play_shadow,
                         (play_rect.x + 1, play_rect.y + 1))
        self.screen.blit(play_text, play_rect)

        self.buttons[f"slot_select_{slot_num}"] = play_btn_rect

        # ═══ DELETE BUTTON (kalau ada save) ═══
        if not is_empty:
            del_btn_y = y + h - 40
            del_btn_rect = pygame.Rect(
                x + 20, del_btn_y, w - 40, 26)

            del_hover = del_btn_rect.collidepoint(mx, my)

            del_color = (140, 40, 40) if del_hover else (100, 30, 30)
            del_border = (220, 80, 80) if del_hover else (180, 60, 60)

            pygame.draw.rect(self.screen, del_color,
                             del_btn_rect, border_radius=5)
            pygame.draw.rect(self.screen, del_border,
                             del_btn_rect, 2, border_radius=5)

            del_font = get_font(18)
            del_text = del_font.render(
                "🗑  DELETE SAVE", True, (255, 200, 200))
            del_rect = del_text.get_rect(center=del_btn_rect.center)
            self.screen.blit(del_text, del_rect)

            self.buttons[f"slot_delete_{slot_num}"] = del_btn_rect

    def _draw_delete_confirm_dialog(self):
        """Confirm dialog untuk delete slot"""
        slot_num = self.slot_delete_confirm

        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        # ═══ DARK OVERLAY (block interaction) ═══
        from mobile.perf import darken
        darken(self.screen, 200)

        # ═══ DIALOG BOX ═══
        dialog_w = 500
        dialog_h = 240
        dialog_x = cx - dialog_w // 2
        dialog_y = cy - dialog_h // 2

        # Shadow
        shadow_surf = pygame.Surface(
            (dialog_w + 10, dialog_h + 10), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 150),
                         (5, 5, dialog_w, dialog_h), border_radius=12)
        self.screen.blit(shadow_surf, (dialog_x - 5, dialog_y - 5))

        # Bg
        pygame.draw.rect(self.screen, (40, 25, 30),
                         (dialog_x, dialog_y, dialog_w, dialog_h),
                         border_radius=12)
        pygame.draw.rect(self.screen, (220, 60, 60),
                         (dialog_x, dialog_y, dialog_w, dialog_h),
                         3, border_radius=12)

        # ═══ WARNING ICON ═══
        icon_font = get_font(48)
        warning_text = icon_font.render(
            "⚠  DELETE SLOT?", True, (255, 100, 100))
        warning_rect = warning_text.get_rect(
            center=(cx, dialog_y + 45))
        self.screen.blit(warning_text, warning_rect)

        # ═══ MESSAGE ═══
        msg_text = self.font_medium.render(
            f"Delete SLOT {slot_num}?", True, (255, 255, 255))
        msg_rect = msg_text.get_rect(center=(cx, dialog_y + 95))
        self.screen.blit(msg_text, msg_rect)

        warn_text = self.font_small.render(
            "This action cannot be undone!",
            True, (220, 180, 180))
        warn_rect = warn_text.get_rect(
            center=(cx, dialog_y + 125))
        self.screen.blit(warn_text, warn_rect)

        # ═══ BUTTONS ═══
        btn_y = dialog_y + dialog_h - 55
        btn_w = 200
        btn_h = 40
        btn_gap = 20

        # YES button (red - destructive)
        yes_x = cx - btn_w - btn_gap // 2
        yes_rect = pygame.Rect(yes_x, btn_y, btn_w, btn_h)

        mx, my = pygame.mouse.get_pos()
        yes_hover = yes_rect.collidepoint(mx, my)

        yes_color = (200, 50, 50) if yes_hover else (160, 40, 40)
        yes_border = (255, 100, 100) if yes_hover else (200, 80, 80)

        pygame.draw.rect(self.screen, yes_color,
                         yes_rect, border_radius=6)
        pygame.draw.rect(self.screen, yes_border,
                         yes_rect, 2, border_radius=6)

        yes_text = self.font_medium.render(
            "YES, DELETE", True, (255, 255, 255))
        yes_text_rect = yes_text.get_rect(center=yes_rect.center)
        self.screen.blit(yes_text, yes_text_rect)

        self.buttons["slot_delete_yes"] = yes_rect

        # NO button (gray - safe)
        no_x = cx + btn_gap // 2
        no_rect = pygame.Rect(no_x, btn_y, btn_w, btn_h)

        no_hover = no_rect.collidepoint(mx, my)

        no_color = (80, 100, 120) if no_hover else (60, 80, 100)
        no_border = (150, 180, 200) if no_hover else (120, 150, 180)

        pygame.draw.rect(self.screen, no_color,
                         no_rect, border_radius=6)
        pygame.draw.rect(self.screen, no_border,
                         no_rect, 2, border_radius=6)

        no_text = self.font_medium.render(
            "CANCEL", True, (255, 255, 255))
        no_text_rect = no_text.get_rect(center=no_rect.center)
        self.screen.blit(no_text, no_text_rect)

        self.buttons["slot_delete_no"] = no_rect

    def reload_progress(self):
        self.save_data = SaveManager.load()
        self.meta_gold = self.save_data.get("meta_gold", 0)
        # Auto set selected_level ke last_played
        self.selected_level = self.save_data.get("last_played_level", 1)

    def _init_particles(self):
        """Init floating particles: ember naik + arcane melayang (mystic)."""
        import random
        particles = []
        for _ in range(64):
            kind = 'ember' if random.random() < 0.55 else 'arcane'
            if kind == 'ember':
                # bara api naik dari bawah (theme arena)
                particles.append({
                    'kind': 'ember',
                    'x': random.uniform(0, SCREEN_WIDTH),
                    'y': random.uniform(SCREEN_HEIGHT * 0.4, SCREEN_HEIGHT),
                    'vx': random.uniform(-0.35, 0.35),
                    'vy': random.uniform(-0.9, -0.35),
                    'size': random.randint(1, 3),
                    'color': random.choice([
                        (255, 190, 80), (255, 220, 120),
                        (255, 150, 50), (255, 235, 160),
                    ]),
                    'alpha': random.randint(80, 180),
                    'ph': random.uniform(0, 6.28),
                })
            else:
                # partikel arcane melayang lambat
                particles.append({
                    'kind': 'arcane',
                    'x': random.uniform(0, SCREEN_WIDTH),
                    'y': random.uniform(0, SCREEN_HEIGHT),
                    'vx': random.uniform(-0.2, 0.2),
                    'vy': random.uniform(-0.35, -0.05),
                    'size': random.randint(1, 2),
                    'color': random.choice([
                        (160, 130, 255), (120, 190, 255),
                        (230, 180, 255), (140, 220, 255),
                    ]),
                    'alpha': random.randint(60, 150),
                    'ph': random.uniform(0, 6.28),
                })
        return particles
    def _update_particles(self):
        """Update floating particles (ember naik & arcane melayang)"""
        import random
        for p in self.particles:
            # drift halus (arcane bergoyang)
            if p.get('kind') == 'arcane':
                p['x'] += p['vx'] + math.sin(p.get('ph', 0)) * 0.08
                p['ph'] = p.get('ph', 0) + 0.01
            else:
                p['x'] += p['vx']
            p['y'] += p['vy']

            # Wrap around screen
            if p['y'] < -10:
                p['y'] = SCREEN_HEIGHT + 10
                p['x'] = random.uniform(0, SCREEN_WIDTH)
            if p['x'] < -10:
                p['x'] = SCREEN_WIDTH + 10
            elif p['x'] > SCREEN_WIDTH + 10:
                p['x'] = -10

    # ═══════════════════════════════════════
    # MAIN UPDATE & DRAW
    # ═══════════════════════════════════════

    @staticmethod
    def _kena(rect, mx, my, longgar=22):
        """
        Uji sentuh dengan pelonggaran.

        Sama seperti helper di InputHandler. Tombol menu dibuat 300x55
        sehingga pelonggaran hanya memperbesar area tujuannya sedikit,
        memudahkan ketukan jari di layar sentuh.
        """
        return rect.inflate(longgar, longgar).collidepoint(mx, my)

    def update(self):
        """Update menu logic"""
        self.animation_time += 1
        self._update_particles()

        # Hover detection
        mx, my = pygame.mouse.get_pos()
        self.hover_button = None
        for btn_id, rect in self.buttons.items():
            if self._kena(rect, mx, my):
                self.hover_button = btn_id
                break

    def draw(self):
        """Draw current menu state"""
        # Update input button label
        try:
            from mobile import platform_utils as _plat
            _touch_mode = _plat.TOUCH_MODE
        except Exception:
            _touch_mode = False
        if _touch_mode:
            self._input_label = "INPUT: TOUCHSCREEN"
        elif hasattr(self, 'controller_mgr') and self.controller_mgr:
            if self.controller_mgr.is_controller_mode():
                info = self.controller_mgr.get_controller_info()
                ctrl_name = info.get('type', 'generic').upper()
                self._input_label = f"INPUT: {ctrl_name} CONTROLLER"
            else:
                self._input_label = "INPUT: KEYBOARD + MOUSE"
        else:
            self._input_label = "INPUT: KEYBOARD + MOUSE"
        # Background
        if self.pause_mode:
            self._draw_pause_background()
        else:
            self._draw_main_background()

        # Clear buttons cache
        self.buttons = {}

        # Draw state-specific
        if self.state == MenuState.MAIN:
            self._draw_main_menu()
        elif self.state == MenuState.HOW_TO_PLAY:
            self._draw_how_to_play()
        elif self.state == MenuState.SETTINGS:
            self._draw_settings()
        elif self.state == MenuState.CREDITS:
            self._draw_credits()
        elif self.state == MenuState.PAUSE:
            self._draw_pause_menu()
        elif self.state == MenuState.HERO_SHOP:
            self._draw_hero_shop()
        elif self.state == MenuState.LEVEL_SELECT:
            self._draw_level_select()
        elif self.state == MenuState.SLOT_SELECT:
            self._draw_slot_select()

    # ================================
    # Di menu.py → handle_click(), TAMBAHKAN:
    # ================================

    def handle_click(self, pos, button):
        """Handle mouse click"""
        # ═══ SCROLL WHEEL ═══
        # Dulu dibungkus `if hasattr(...)`, padahal atribut scroll baru
        # dibuat di dalam fungsi DRAW. Kalau event scroll datang sebelum
        # layar sempat digambar, scroll diabaikan diam-diam. Sekarang
        # atributnya dibuat di sini kalau belum ada.
        if self.state == MenuState.LEVEL_SELECT:
            if button in (4, 5):
                if not hasattr(self, '_level_scroll'):
                    self._level_scroll = 0
                if button == 4:
                    self._level_scroll = max(0, self._level_scroll - 60)
                else:
                    self._level_scroll += 60
                return

        # ═══ HERO SHOP SCROLL ═══
        if self.state == MenuState.HERO_SHOP:
            if button in (4, 5):
                if not hasattr(self, '_meta_shop_scroll'):
                    self._meta_shop_scroll = 0
                if button == 4:
                    self._meta_shop_scroll = max(
                        0, self._meta_shop_scroll - 50)
                else:
                    self._meta_shop_scroll += 50
                return

        # Scroll di layar lain: abaikan, jangan diteruskan jadi klik.
        if button in (4, 5):
            return

        if button != 1:
            return

        mx, my = pos
        for btn_id, rect in self.buttons.items():
            if self._kena(rect, mx, my):
                self._on_button_click(btn_id)
                SoundManager().play('ui_click', volume_mult=0.6)
                return
    # ================================
    # GANTI method _draw_level_select() di menu.py
    # ================================

    def _draw_level_select(self):
        """Level select screen - RESPONSIVE GRID"""
        from levels import ALL_LEVELS, is_level_unlocked

        cx = SCREEN_WIDTH // 2
        completed = self.save_data.get("completed_levels", [])

        # ═══ TITLE (lebih kecil & atas) ═══
        _tf_lvl = title_font(72)
        title = _tf_lvl.render("SELECT LEVEL", True, (255, 220, 100))
        title_rect = title.get_rect(center=(cx, 60))
        self._blit_shadow(self.screen, title, title_rect.topleft)
        self.screen.blit(title, title_rect)

        # ═══ PROGRESS INFO ═══
        total = len(ALL_LEVELS)
        done_count = len(completed)
        progress_text = self.font_small.render(
            f"COMPLETED: {done_count} / {total}",
            True, (150, 220, 255))
        progress_rect = progress_text.get_rect(center=(cx, 140))
        self.screen.blit(progress_text, progress_rect)

        # Progress bar
        bar_w = 300
        bar_h = 6
        bx = cx - bar_w // 2
        by = 155

        pygame.draw.rect(self.screen, (40, 45, 60),
                         (bx, by, bar_w, bar_h), border_radius=3)
        fill_w = int(bar_w * (done_count / max(1, total)))
        if fill_w > 0:
            pygame.draw.rect(self.screen, (100, 220, 100),
                             (bx, by, fill_w, bar_h), border_radius=3)
        pygame.draw.rect(self.screen, (100, 130, 180),
                         (bx, by, bar_w, bar_h), 1, border_radius=3)

        # ═══ SCROLL STATE ═══
        if not hasattr(self, '_level_scroll'):
            self._level_scroll = 0

        # ═══ LAYOUT CALCULATION ═══
        card_w = 280
        card_h = 290  # ← LEBIH PENDEK (dari 380)
        gap_x = 22
        gap_y = 18
        cols = min(4, len(ALL_LEVELS))  # Max 4 kolom

        # Kalau 4 level, pakai 4 kolom. Kalau 5+, pakai 3 kolom + scroll
        if len(ALL_LEVELS) <= 4:
            cols = len(ALL_LEVELS)
        else:
            cols = 3

        total_cards_w = cols * card_w + (cols - 1) * gap_x
        start_x = cx - total_cards_w // 2

        # Content area
        content_top = 180
        content_bottom = SCREEN_HEIGHT - 60  # Ruang untuk BACK button
        content_height = content_bottom - content_top

        # Calculate rows
        total_rows = (len(ALL_LEVELS) + cols - 1) // cols
        total_content_h = total_rows * (card_h + gap_y)
        max_scroll = max(0, total_content_h - content_height)

        # Clamp scroll
        self._level_scroll = max(0, min(max_scroll, self._level_scroll))

        # ═══ CLIP AREA ═══
        clip_rect = pygame.Rect(0, content_top,
                                SCREEN_WIDTH, content_height)
        old_clip = self.screen.get_clip()
        self.screen.set_clip(clip_rect)

        # ═══ DRAW CARDS ═══
        for i, level in enumerate(ALL_LEVELS):
            col = i % cols
            row = i // cols

            card_x = start_x + col * (card_w + gap_x)
            card_y = content_top + row * (card_h + gap_y) - self._level_scroll

            # Skip jika di luar visible area
            if card_y + card_h < content_top or card_y > content_bottom:
                continue

            self._draw_level_card(level, card_x, card_y,
                                  card_w, card_h, completed)

        # Reset clip
        self.screen.set_clip(old_clip)

        # ═══ SCROLL INDICATOR ═══
        if max_scroll > 0:
            self._draw_level_scroll_indicator(
                SCREEN_WIDTH - 25, content_top,
                content_height, self._level_scroll, max_scroll)

        # ═══ BACK BUTTON (fixed di bawah) ═══
        self._draw_menu_button("level_back", "BACK",
                               cx, SCREEN_HEIGHT - 32,
                               (150, 150, 150),
                               width=200, height=38)

    def _draw_level_scroll_indicator(self, x, y, height,
                                     scroll_pos, max_scroll):
        """Draw scroll indicator untuk level select"""
        # Track
        pygame.draw.rect(self.screen, (30, 35, 50),
                         (x, y, 8, height), border_radius=4)
        pygame.draw.rect(self.screen, (60, 70, 90),
                         (x, y, 8, height), 1, border_radius=4)

        # Thumb
        if max_scroll > 0:
            thumb_ratio = height / (height + max_scroll)
            thumb_h = max(20, int(height * thumb_ratio))
            thumb_y = y + int((height - thumb_h) *
                              (scroll_pos / max_scroll))

            pygame.draw.rect(self.screen, (100, 130, 180),
                             (x, thumb_y, 8, thumb_h), border_radius=4)
            pygame.draw.rect(self.screen, (150, 180, 220),
                             (x + 1, thumb_y + 1, 6, thumb_h - 2),
                             border_radius=3)

    # ================================
    # GANTI method _draw_level_card() di menu.py
    # COMPACT VERSION - tinggi 290px (dari 380px)
    # ================================

    def _draw_level_card(self, level, x, y, w, h, completed):
        """Draw single level card - COMPACT"""
        from levels import is_level_unlocked

        lvl_num = level["level_number"]
        is_unlocked = is_level_unlocked(lvl_num, completed)
        is_completed = lvl_num in completed

        # Hover
        mx, my = pygame.mouse.get_pos()
        card_rect = pygame.Rect(x, y, w, h)
        is_hover = card_rect.collidepoint(mx, my) and is_unlocked

        # ═══ CARD BG ═══
        if not is_unlocked:
            bg_color = (30, 20, 25)
            border_color = (100, 60, 60)
        elif is_completed:
            bg_color = (20, 45, 30)
            border_color = (100, 220, 100)
        else:
            bg_color = (25, 35, 55)
            border_color = (100, 200, 255)

        # Shadow
        shadow_surf = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 130),
                         (3, 3, w, h), border_radius=10)
        self.screen.blit(shadow_surf, (x - 3, y - 3))

        # BG
        pygame.draw.rect(self.screen, bg_color,
                         (x, y, w, h), border_radius=10)

        # Hover glow
        if is_hover:
            glow_surf = pygame.Surface((w + 16, h + 16), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*border_color, 70),
                             (0, 0, w + 16, h + 16), border_radius=13)
            self.screen.blit(glow_surf, (x - 8, y - 8))
            border_color = (255, 255, 255)

        # Border
        border_w = 3 if is_hover else 2
        pygame.draw.rect(self.screen, border_color,
                         (x, y, w, h), border_w, border_radius=10)

        # ═══ TOP SECTION: Level number + name (compact, rapi) ═══
        # "LEVEL" label
        label = self.font_tiny.render("LEVEL", True, (150, 160, 180))
        label_rect = label.get_rect(center=(x + w // 2, y + 14))
        self.screen.blit(label, label_rect)

        # Level number (lebih kecil agar tidak bertabrakan)
        lvl_font = get_font(34, 'body_bold')
        lvl_color = (150, 150, 150) if not is_unlocked else (
            (100, 255, 100) if is_completed else (255, 220, 100))

        lvl_shadow = lvl_font.render(f"{lvl_num}", True, (0, 0, 0))
        lvl_rect = lvl_shadow.get_rect(center=(x + w // 2, y + 48))
        self.screen.blit(lvl_shadow, (lvl_rect.x + 2, lvl_rect.y + 2))

        lvl_text = lvl_font.render(f"{lvl_num}", True, lvl_color)
        self.screen.blit(lvl_text, lvl_rect)

        # Level name (font lebih kecil + truncate supaya tidak meluber)
        name_color = (200, 200, 220) if is_unlocked else (100, 100, 110)
        name_font = get_font(22, 'body_semibold')
        name_text = str(level["name"])
        if name_font.size(name_text)[0] > w - 30:
            while name_font.size(name_text + "...")[0] > w - 30 and len(name_text) > 5:
                name_text = name_text[:-1]
            name_text += "..."
        name = name_font.render(name_text, True, name_color)
        name_rect = name.get_rect(center=(x + w // 2, y + 82))
        self.screen.blit(name, name_rect)

        # Description (1 line, truncated)
        desc_font = get_font(14)
        desc_text = level["description"]
        if desc_font.size(desc_text)[0] > w - 30:
            while desc_font.size(desc_text + "...")[0] > w - 30 and len(desc_text) > 10:
                desc_text = desc_text[:-1]
            desc_text += "..."
        desc_surf = desc_font.render(
            desc_text, True,
            (170, 180, 200) if is_unlocked else (80, 80, 100))
        desc_rect = desc_surf.get_rect(center=(x + w // 2, y + 106))
        self.screen.blit(desc_surf, desc_rect)

        # ═══ STATUS BADGE (top-right) ═══
        if is_completed:
            badge_rect = pygame.Rect(x + w - 55, y + 8, 45, 18)
            pygame.draw.rect(self.screen, (40, 100, 40),
                             badge_rect, border_radius=9)
            pygame.draw.rect(self.screen, (100, 220, 100),
                             badge_rect, 1, border_radius=9)
            chk = self.font_tiny.render("✓ DONE", True, WHITE)
            chk_rect = chk.get_rect(center=badge_rect.center)
            self.screen.blit(chk, chk_rect)

        # ═══ SEPARATOR ═══
        sep_y = y + 122
        pygame.draw.line(self.screen, (60, 70, 90),
                         (x + 15, sep_y), (x + w - 15, sep_y), 1)

        # ═══ INFO SECTION (kalau unlocked) ═══
        if is_unlocked:
            info_y = sep_y + 8

            # Difficulty
            diff_label = self.font_tiny.render(
                "DIFFICULTY", True, (150, 160, 180))
            self.screen.blit(diff_label, (x + 15, info_y))

            hp_mult = level.get("enemy_hp_mult", 1.0)
            diff_level = min(5, int(hp_mult * 2.5))

            for i in range(5):
                bar_x = x + 15 + i * 18
                bar_y_pos = info_y + 16
                if i < diff_level:
                    bar_col = (255, 100, 80) if i >= 3 else (
                        (255, 200, 80) if i >= 1 else (100, 220, 100))
                else:
                    bar_col = (50, 50, 60)
                pygame.draw.rect(self.screen, bar_col,
                                 (bar_x, bar_y_pos, 14, 6),
                                 border_radius=2)

            # ═══ STATS (compact 2-column) ═══
            from _system import SaveManager
            level_stats = SaveManager.get_level_stats(
                self.save_data, lvl_num)

            stats_y = info_y + 32

            if level_stats['total_attempts'] > 0:
                # Row 1 & 2 - fixed layout, no overlap, English
                stat_font = get_font(11)
                val_font = get_font(14)
                val_font_bold = get_font(15, 'body_bold')

                # Best Score (left)
                self.screen.blit(stat_font.render("BEST SCORE", True, (130, 140, 160)), (x + 12, stats_y))
                score_val = level_stats['best_score']
                # Format to avoid overflow: 12345 -> 12.3K
                if score_val >= 10000:
                    score_str = f"{score_val/1000:.1f}K"
                else:
                    score_str = f"{score_val:,}"
                if val_font.size(score_str)[0] > w//2 - 20:
                    score_str = score_str[:8]
                self.screen.blit(val_font_bold.render(score_str, True, (255, 220, 100)), (x + 12, stats_y + 12))

                # Best Time (right) - ensure not overlapping
                self.screen.blit(stat_font.render("BEST TIME", True, (130, 140, 160)), (x + w//2 + 8, stats_y))
                time_str = SaveManager.format_time(level_stats['best_time_seconds'])
                if val_font.size(time_str)[0] > w//2 - 20:
                    time_str = time_str[:8]
                self.screen.blit(val_font.render(time_str, True, (100, 220, 255)), (x + w//2 + 8, stats_y + 12))

                # Row 2: Attempts + Win Rate - more spacing
                row2_y = stats_y + 32

                wins = level_stats['wins']
                attempts = level_stats['total_attempts']
                win_rate = int((wins / attempts) * 100) if attempts > 0 else 0

                self.screen.blit(stat_font.render("ATTEMPTS", True, (130, 140, 160)), (x + 12, row2_y))
                attempt_str = f"{wins}W/{attempts}"
                self.screen.blit(val_font.render(attempt_str, True, (200, 220, 240)), (x + 12, row2_y + 12))

                self.screen.blit(stat_font.render("WIN RATE", True, (130, 140, 160)), (x + w//2 + 8, row2_y))
                wr_color = (100, 255, 100) if win_rate >= 75 else ((255, 220, 100) if win_rate >= 50 else (255, 150, 100))
                self.screen.blit(val_font_bold.render(f"{win_rate}%", True, wr_color), (x + w//2 + 8, row2_y + 12))
            else:
                no_stats = self.font_tiny.render("No stats yet", True, (120, 140, 160))
                no_rect = no_stats.get_rect(center=(x + w // 2, stats_y + 14))
                self.screen.blit(no_stats, no_rect)

        elif not is_unlocked:
            # Locked message
            lock_y = sep_y + 30
            lock_font = get_font(28)
            lock_text = lock_font.render("🔒 LOCKED", True, (180, 100, 100))
            lock_rect = lock_text.get_rect(center=(x + w // 2, lock_y))
            self.screen.blit(lock_text, lock_rect)

            req_text = self.font_tiny.render(
                f"Complete Level {level.get('unlock_after_level', '?')} first",
                True, (150, 120, 120))
            req_rect = req_text.get_rect(center=(x + w // 2, lock_y + 25))
            self.screen.blit(req_text, req_rect)

        # ═══ PLAY BUTTON (di bawah card) ═══
        btn_y = y + h - 38
        btn_rect = pygame.Rect(x + 15, btn_y, w - 30, 28)

        if not is_unlocked:
            pygame.draw.rect(self.screen, (50, 25, 25),
                             btn_rect, border_radius=5)
            pygame.draw.rect(self.screen, (120, 60, 60),
                             btn_rect, 2, border_radius=5)
            btn_txt = self.font_small.render("LOCKED", True, (180, 120, 120))
            btn_txt_rect = btn_txt.get_rect(center=btn_rect.center)
            self.screen.blit(btn_txt, btn_txt_rect)
        else:
            btn_color = (50, 180, 80) if is_hover else (40, 140, 60)
            border = (150, 255, 150) if is_hover else (100, 220, 100)

            pygame.draw.rect(self.screen, btn_color,
                             btn_rect, border_radius=5)
            pygame.draw.rect(self.screen, border,
                             btn_rect, 2, border_radius=5)

            label_text = "REPLAY" if is_completed else "PLAY"
            btn_txt = self.font_small.render(label_text, True, WHITE)
            btn_txt_rect = btn_txt.get_rect(center=btn_rect.center)
            self.screen.blit(btn_txt, btn_txt_rect)

            self.buttons[f"level_{lvl_num}"] = card_rect

    def handle_key(self, key):
        """Handle keyboard"""
        if key == pygame.K_ESCAPE:
            if self.state == MenuState.MAIN:
                self.action = "quit"
            elif self.state in [MenuState.HOW_TO_PLAY,
                                MenuState.SETTINGS,
                                MenuState.CREDITS,
                                MenuState.LEVEL_SELECT,
                                MenuState.HERO_SHOP,
                                MenuState.SLOT_SELECT]:
                # Cancel delete confirm dulu kalau ada
                if hasattr(self, 'slot_delete_confirm') and \
                        self.slot_delete_confirm is not None:
                    self.slot_delete_confirm = None
                    return

                # Cancel reset confirm dulu kalau ada
                if getattr(self, 'reset_confirm', False):
                    self.reset_confirm = False
                    return

                self.state = MenuState.MAIN
                SoundManager().play('ui_click', volume_mult=0.4)
            elif self.state == MenuState.PAUSE:
                self.action = "resume"

    # ═══════════════════════════════════════
    # BACKGROUND
    # ═══════════════════════════════════════

    def _draw_main_background(self):
        """Background MYSTIC ARENA (cache statis + kabut parallax + partikel)."""
        if getattr(self, '_bg_cache', None) is None:
            self._bg_cache = self._build_main_background()
            self._fog_layers = self._build_menu_fog()
        self.screen.blit(self._bg_cache, (0, 0))

        t = getattr(self, 'animation_time', 0)

        # ── Kabut bergerak (2 lapis parallax) ──
        # PENYEBAB UTAMA LAG DI HP: tiap lapis di-blit 2x (untuk
        # sambungan) dan lebarnya ~1,5x layar -> 4 alpha blit x
        # 667.000 piksel = 2,7 juta piksel = 593 ms/frame.
        # Latar statisnya sendiri sudah di-cache dan tetap tampil.
        from mobile.perf import Quality as _Qb
        if _Qb.cheap_alpha:
            for li, (fog, speed, alpha) in enumerate(self._fog_layers):
                fw = fog.get_width()
                off = int((t * speed) % fw)
                fog.set_alpha(max(8, min(80, alpha + int(5 * math.sin(t * 0.008 + li * 2)))))
                self.screen.blit(fog, (-off, 0))
                self.screen.blit(fog, (fw - off, 0))

        # ── Partikel (ember naik + arcane melayang, glow lembut) ──
        for p in self.particles:
            s = p['size']
            # deny halus (alpha berdenyut pelan)
            a = p['alpha']
            if p.get('kind') == 'ember':
                a = int(p['alpha'] * (0.75 + 0.25 * math.sin(t * 0.05 + p['ph'])))
            glow = pygame.Surface((s * 6, s * 6), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*p['color'], a // 4),
                               (s * 3, s * 3), s * 2)
            pygame.draw.circle(glow, (*p['color'], a),
                               (s * 3, s * 3), s)
            self.screen.blit(glow, (int(p['x']) - s * 3,
                                    int(p['y']) - s * 3))

    def _build_main_background(self):
        """Pre-render latar menu 'MYSTIC ARENA': langit malam mystic,
        nebula, bulan besar, pegunungan, magic rune, lane bercahaya,
        nexus, grid, dan vignette (sekali saja)."""
        W, H = SCREEN_WIDTH, SCREEN_HEIGHT
        import random
        rng = random.Random(2026)
        bg = pygame.Surface((W, H))

        # ── 1. Gradient langit malam (indigo dalam -> ungu -> horizon hangat) ──
        for y in range(H):
            t = y / H
            r = int(6 + t * 18)
            g = int(10 + t * 22)
            b = int(32 + t * 50)
            if t > 0.62:
                warm = (t - 0.62) / 0.38
                r = int(r + 26 * warm)
                g = int(g + 14 * warm)
            pygame.draw.line(bg, (r, g, b), (0, y), (W, y))

        # ── 2. Nebula / aurora (lapis lembut ber-alpha) ──
        neb = pygame.Surface((W, H), pygame.SRCALPHA)
        for _ in range(8):
            nx = rng.uniform(0, W)
            ny = rng.uniform(0, H * 0.55)
            nr = rng.randint(90, 250)
            col = rng.choice([(120, 70, 200), (60, 90, 200), (200, 90, 60),
                              (150, 60, 165), (70, 120, 220)])
            for rad in range(nr, 0, -8):
                a = int(7 * (1 - rad / nr))
                pygame.draw.circle(neb, (*col, a), (int(nx), int(ny)), rad)
        bg.blit(neb, (0, 0))

        # ── 3. Bintang (banyak + twinkle) ──
        stars = pygame.Surface((W, H), pygame.SRCALPHA)
        for _ in range(170):
            sx = rng.uniform(0, W)
            sy = rng.uniform(0, H * 0.6)
            rad = rng.choice([1, 1, 1, 2])
            col = rng.choice([(200, 220, 255), (255, 240, 200),
                              (220, 200, 255), (160, 200, 255)])
            pygame.draw.circle(stars, (*col, rng.randint(40, 170)),
                               (int(sx), int(sy)), rad)
            if rad == 2:
                pygame.draw.circle(stars, (*col, 32),
                                   (int(sx), int(sy)), 5, 1)
        bg.blit(stars, (0, 0))

        # ── 4. Bulan mistik besar (kiri-atas) ──
        moon_x, moon_y, moon_r = int(W * 0.22), int(H * 0.16), 48
        moon_glow = pygame.Surface((moon_r * 6, moon_r * 6), pygame.SRCALPHA)
        for rad in range(moon_r * 3, 0, -4):
            a = int(11 * (1 - rad / (moon_r * 3)))
            pygame.draw.circle(moon_glow, (225, 210, 255, a),
                               (moon_r * 3, moon_r * 3), rad)
        bg.blit(moon_glow, (moon_x - moon_r * 3, moon_y - moon_r * 3))
        pygame.draw.circle(bg, (238, 230, 250), (moon_x, moon_y), moon_r)
        pygame.draw.circle(bg, (210, 200, 238), (moon_x, moon_y), moon_r, 1)
        for cx, cy, cr in ((moon_x - 14, moon_y - 12, 9),
                           (moon_x + 12, moon_y - 8, 7),
                           (moon_x, moon_y + 14, 10),
                           (moon_x - 6, moon_y + 4, 5)):
            pygame.draw.circle(bg, (205, 195, 232), (cx, cy), cr)

        # ── 5. Glow radial (arcane di belakang judul + emas horizon) ──
        glow = pygame.Surface((W, H), pygame.SRCALPHA)
        for rad in range(390, 0, -6):
            a = int(15 * (1 - rad / 390))
            pygame.draw.circle(glow, (115, 70, 200, a), (W // 2, 220), rad)
        for rad in range(330, 0, -6):
            a = int(11 * (1 - rad / 330))
            pygame.draw.circle(glow, (255, 200, 90, a), (W // 2, 650), rad)
        bg.blit(glow, (0, 0))

        # ── 6. Magic rune ring (di belakang judul) ──
        ring = pygame.Surface((W, H), pygame.SRCALPHA)
        cx, cy = W // 2, 218
        for rr, aa, wdt in ((158, 26, 2), (136, 15, 1), (180, 11, 1)):
            pygame.draw.circle(ring, (175, 135, 255, aa), (cx, cy), rr, wdt)
        for i in range(12):
            ang = i * (2 * math.pi / 12)
            rx = cx + int(math.cos(ang) * 158)
            ry = cy + int(math.sin(ang) * 158)
            pygame.draw.circle(ring, (205, 165, 255, 42), (rx, ry), 3)
        for i in range(4):
            ang = i * (2 * math.pi / 4) + math.pi / 4
            rx = cx + int(math.cos(ang) * 136)
            ry = cy + int(math.sin(ang) * 136)
            pygame.draw.line(ring, (175, 135, 255, 26),
                             (cx, cy), (rx, ry), 1)
        bg.blit(ring, (0, 0))

        # ── 7. Pegunungan siluet (2 lapis) ──
        def _mountains(color, seed, base_y, amp, step):
            r2 = random.Random(seed)
            pts = [(0, H)]
            x = 0
            while x <= W:
                y = base_y - r2.uniform(amp * 0.4, amp)
                pts.append((x, int(y)))
                x += step
            pts.append((W, H))
            pygame.draw.polygon(bg, color, pts)

        _mountains((11, 13, 28), 7, int(H * 0.74), 62, 46)
        _mountains((6, 8, 21), 21, int(H * 0.83), 44, 34)

        # ── 8. Jalur lane (3 lengkung, tepi glow mystic) ──
        def lane_curve(p0, p1, p2, n=90):
            pts = []
            for i in range(n + 1):
                t = i / n
                x = ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0]
                     + t * t * p2[0])
                y = ((1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1]
                     + t * t * p2[1])
                pts.append((int(x), int(y)))
            return pts

        lanes = [
            ((90, 670), (520, 430), (1210, 150)),
            ((150, 730), (560, 500), (1150, 240)),
            ((40, 560), (480, 340), (1180, 60)),
        ]
        lane_glows = [(95, 115, 255), (125, 85, 225), (70, 155, 255)]
        for idx, pts in enumerate(lanes):
            lg = pygame.Surface((W, H), pygame.SRCALPHA)
            pygame.draw.lines(lg, (*lane_glows[idx], 26), False, pts, 72)
            bg.blit(lg, (0, 0))
            pygame.draw.lines(bg, (10, 13, 28), False, pts, 44)
            pygame.draw.lines(bg, (16, 20, 40), False, pts, 36)
            for i in range(0, len(pts) - 8, 12):
                pygame.draw.line(bg, (62, 57, 46), pts[i], pts[i + 6], 2)
            pygame.draw.lines(bg, (95, 92, 150), False, pts, 1)

        # ── 9. Portal mystic (pengganti nexus - bersih, tanpa kotak) ──
        self._draw_portal(bg, 120, 612, (150, 130, 255), (95, 150, 255))
        self._draw_portal(bg, 1135, 168, (255, 205, 120), (255, 150, 90))

        # ── 10. Kristal rune di sepanjang lane (pengganti tower) ──
        crystal_cols = [(140, 170, 255), (180, 140, 255), (120, 200, 255)]
        for li, pts in enumerate(lanes):
            for frac in (0.3, 0.55, 0.8):
                i = int(len(pts) * frac)
                self._draw_rune_crystal(bg, pts[i][0], pts[i][1] - 46,
                                        crystal_cols[li % len(crystal_cols)])

        # ── 10. Grid perspektif halus ──
        grid = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(1, 9):
            y = 440 + i * 40
            pygame.draw.line(grid, (255, 255, 255, 9), (0, y), (W, y))
        for i in range(-8, 17):
            x = W // 2 + i * 90
            pygame.draw.line(grid, (255, 255, 255, 7), (x, 450),
                             (W // 2 + i * 55, H))
        bg.blit(grid, (0, 0))

        # ── 11. Vignette radial halus (mulus, BUKAN kotak hitam) ──
        # Dibuat dari surface kecil lalu diperbesar (smooth), sehingga
        # penggelapan di tepi adalah gradasi lembut — sudut tidak hitam pekat.
        _sw, _sh = W // 40, H // 40
        _vig = pygame.Surface((_sw, _sh), pygame.SRCALPHA)
        for _vy in range(_sh):
            for _vx in range(_sw):
                _nx = _vx / _sw - 0.5
                _ny = _vy / _sh - 0.5
                _d = math.hypot(_nx * 2, _ny * 2)
                _a = int(max(0, min(52, (_d - 0.6) * 130)))
                _vig.set_at((_vx, _vy), (12, 9, 26, _a))
        bg.blit(pygame.transform.smoothscale(_vig, (W, H)), (0, 0))

        # ── 12. Tint ungu mistik halus ──
        tint = pygame.Surface((W, H), pygame.SRCALPHA)
        tint.fill((60, 30, 110, 12))
        bg.blit(tint, (0, 0))
        return bg

    def _build_menu_fog(self):
        """Kabut bergerak (2 lapis parallax) - surface dibuat sekali."""
        W, H = SCREEN_WIDTH, SCREEN_HEIGHT
        layers = []
        rng = random.Random(99)
        for li, (spd, alp, n_blobs) in enumerate(((0.35, 26, 9),
                                                  (0.6, 18, 7))):
            fw = W + 220
            fog = pygame.Surface((fw, H), pygame.SRCALPHA)
            col = (205, 205, 255) if li == 0 else (180, 190, 235)
            for _ in range(n_blobs):
                bx = rng.uniform(0, fw)
                by = rng.uniform(H * 0.55, H)
                br = rng.randint(60, 160)
                for rad in range(br, 0, -10):
                    a = int(15 * (1 - rad / br))
                    pygame.draw.circle(fog, (*col, a),
                                       (int(bx), int(by)), rad)
            layers.append((fog, spd, alp))
        return layers

    def _draw_portal(self, bg, x, y, color, color2):
        """Portal mystic bulat bercahaya (pengganti nexus - elegan,
        tanpa kotak, tanpa warna merah/biru mencolok)."""
        # Lingkaran luar (glow berlapis)
        glow = pygame.Surface((150, 150), pygame.SRCALPHA)
        for rad in range(74, 0, -3):
            a = int(10 * (1 - rad / 74))
            pygame.draw.circle(glow, (*color, a), (75, 75), rad)
        bg.blit(glow, (x - 75, y - 75))

        # Ring utama (dua cincin halus)
        pygame.draw.circle(bg, tuple(int(c * 0.45) for c in color),
                           (x, y), 42, 3)
        pygame.draw.circle(bg, color, (x, y), 36, 2)

        # Pusat portal (isi lembut + inti terang)
        core = pygame.Surface((72, 72), pygame.SRCALPHA)
        for rad in range(35, 0, -3):
            a = int(9 * (1 - rad / 35))
            pygame.draw.circle(core, (*color, a), (36, 36), rad)
        bg.blit(core, (x - 36, y - 36))
        pygame.draw.circle(bg, color2, (x, y), 10)
        pygame.draw.circle(bg, (255, 255, 255), (x, y), 4)

        # Rune kecil mengorbit
        import math as _m
        for i in range(6):
            ang = i * (_m.pi * 2 / 6)
            rx = x + int(_m.cos(ang) * 30)
            ry = y + int(_m.sin(ang) * 30)
            pygame.draw.circle(bg, (*color, 200), (rx, ry), 2)

    def _draw_rune_crystal(self, bg, x, y, color):
        """Kristal rune kecil bercahaya (pengganti tower - mulus & cantik)."""
        # Glow lembut
        glow = pygame.Surface((54, 54), pygame.SRCALPHA)
        for rad in range(26, 0, -3):
            a = int(8 * (1 - rad / 26))
            pygame.draw.circle(glow, (*color, a), (27, 27), rad)
        bg.blit(glow, (x - 27, y - 27))

        # Badan kristal (belah ketupat mulus, bukan kotak)
        dark = tuple(int(c * 0.5) for c in color)
        pygame.draw.polygon(bg, dark,
                            [(x, y - 16), (x + 10, y - 4), (x, y + 12),
                             (x - 10, y - 4)])
        pygame.draw.polygon(bg, color,
                            [(x, y - 16), (x + 10, y - 4), (x, y + 12),
                             (x - 10, y - 4)], 1)
        # Sorot
        pygame.draw.line(bg, tuple(min(255, c + 60) for c in color),
                         (x - 4, y - 10), (x - 2, y - 2), 2)
        # Inti rune
        pygame.draw.circle(bg, (255, 255, 255), (x, y - 2), 2)
    def _draw_pause_background(self):
        """Dark overlay untuk pause menu (game masih visible di background)"""
        # Alokasi + blit alpha layar penuh = ~244 ms/frame di HP.
        from mobile.perf import Quality as _Qp, darken
        if _Qp.cheap_alpha:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT),
                                     pygame.SRCALPHA)
            overlay.fill((10, 10, 20, 200))
            self.screen.blit(overlay, (0, 0))
        else:
            darken(self.screen, 200)

    # ═══════════════════════════════════════
    # MAIN MENU
    # ═══════════════════════════════════════

    def _render_gradient_text(self, font, text, top_color, bottom_color):
        """Render teks dengan gradasi warna vertikal."""
        base = font.render(text, True, (255, 255, 255))
        grad = pygame.Surface(base.get_size(), pygame.SRCALPHA)
        h = base.get_height()
        for y in range(h):
            t = y / max(1, h - 1)
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
            pygame.draw.line(grad, (r, g, b, 255), (0, y),
                             (base.get_width(), y))
        grad.blit(base, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return grad

    def _draw_main_menu(self):
        """Draw main menu screen (tema dark-fantasy TD)."""
        cx = SCREEN_WIDTH // 2
        t = self.animation_time * 0.02

        try:
            from levels import get_level_count
            lvl_count = get_level_count()
        except Exception:
            lvl_count = 20
        try:
            hero_count = len(get_all_hero_types())
        except Exception:
            hero_count = 86

        # (Badge jumlah level/hero & HERO GOLD TIDAK tampil di main menu.
        #  HERO GOLD hanya muncul di layar HERO SHOP.)

        # ═══ TITLE (gradasi emas + glow + outline) ═══
        title_y = 124 + int(math.sin(t) * 3)
        from mobile.perf import Quality as _Qt2
        if _Qt2.cheap_alpha:
            glow_t = pygame.Surface((640, 130), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_t,
                                (255, 205, 100, int(46 + 22 * math.sin(t))),
                                (0, 12, 640, 104))
            self.screen.blit(glow_t, (cx - 320, title_y - 62))
        out = self.font_title.render("MYSTIC ARENA", True, (12, 10, 24))
        o_rect = out.get_rect(center=(cx, title_y))
        # outline 8 arah = 8 alpha blit teks besar (224.000 px = 50 ms)
        if _Qt2.cheap_alpha:
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2),
                           (-2, -2), (2, 2), (-2, 2), (2, -2)):
                self.screen.blit(out, (o_rect.x + dx, o_rect.y + dy))
        grad = self._render_gradient_text(
            self.font_title, "MYSTIC ARENA",
            (255, 242, 175), (196, 138, 40))
        self.screen.blit(grad, grad.get_rect(center=(cx, title_y)))

        # ═══ SUBTITLE PLATE ═══
        sub = self.font_subtitle.render(
            "B A T T L E   A R E N A", True, (150, 195, 255))
        plate = pygame.Rect(cx - (sub.get_width() + 56) // 2,
                            title_y + 66,
                            sub.get_width() + 56,
                            sub.get_height() + 14)
        pygame.draw.rect(self.screen, (14, 18, 34), plate,
                         border_radius=10)
        pygame.draw.rect(self.screen, (255, 220, 100), plate, 1,
                         border_radius=10)
        self.screen.blit(sub, sub.get_rect(center=plate.center))

        # Tagline (tanpa angka level/hero)
        tag = self.font_small.render(
            "Dark Fantasy MOBA  -  Battle Arena",
            True, (150, 160, 185))
        self.screen.blit(tag, tag.get_rect(center=(cx, plate.bottom + 20)))

        # ═══ FLOURISH (garis - wajik - garis) ═══
        fy = plate.bottom + 46
        pygame.draw.line(self.screen, (255, 220, 100),
                         (cx - 220, fy), (cx - 18, fy), 2)
        pygame.draw.line(self.screen, (255, 220, 100),
                         (cx + 18, fy), (cx + 220, fy), 2)
        pygame.draw.polygon(self.screen, (255, 220, 100),
                            [(cx - 8, fy), (cx, fy - 7),
                             (cx + 8, fy), (cx, fy + 7)])
        pygame.draw.circle(self.screen, (255, 240, 180),
                           (cx - 230, fy), 3)
        pygame.draw.circle(self.screen, (255, 240, 180),
                           (cx + 230, fy), 3)

        # ═══ BUTTONS ═══
        # Baris pertama: CONTINUE (kiri) + PLAY GAME (kanan) sejajar
        self._draw_menu_button("continue", "CONTINUE", cx - 170, 336,
                               (140, 225, 255), width=300, height=50,
                               icon="play", label_font_size=36)
        self._draw_menu_button("play", "PLAY GAME", cx + 170, 336,
                               (100, 220, 110), width=300, height=50,
                               icon="play", label_font_size=36)

        # Baris berikutnya (tidak bergeser dari layout sebelumnya)
        buttons_data = [
            ("hero_shop", "HERO SHOP", (255, 220, 100), "coin"),
            ("input_select", "INPUT", (100, 200, 220), "pad"),
            ("how_to_play", "HOW TO PLAY", (110, 180, 255), "help"),
            ("settings", "SETTINGS", (205, 180, 105), "gear"),
            ("credits", "CREDITS", (200, 130, 210), "star"),
            ("quit", "QUIT GAME", (225, 90, 90), "quit"),
        ]
        button_y_start = 336 + 53
        button_gap = 53
        for i, (btn_id, label, color, icon) in enumerate(buttons_data):
            y = button_y_start + i * button_gap
            self._draw_menu_button(btn_id, label, cx, y, color,
                                   width=360, height=50, icon=icon)

        # Input mode (kiri bawah) + version (kanan bawah)
        mode = self.font_tiny.render(
            getattr(self, '_input_label', 'INPUT: KEYBOARD + MOUSE'),
            True, (110, 200, 210))
        self.screen.blit(mode, (24, SCREEN_HEIGHT - 28))
        version = self.font_tiny.render(
            "v2.0  -  MOBA Tower Defense", True, (105, 110, 140))
        self.screen.blit(version, version.get_rect(
            center=(cx, SCREEN_HEIGHT - 20)))
    def _draw_hero_shop(self):
        cx = SCREEN_WIDTH // 2

        # Init tab state
        if not hasattr(self, 'shop_tab'):
            self.shop_tab = 'starter'
        if not hasattr(self, '_meta_shop_scroll'):
            self._meta_shop_scroll = 0

        # ═══ TITLE (compact) ═══
        _tf_shop = title_font(72)
        title = _tf_shop.render("HERO SHOP", True, (255, 220, 100))
        title_rect = title.get_rect(center=(cx, 55))
        self._blit_shadow(self.screen, title, title_rect.topleft)
        self.screen.blit(title, title_rect)

        # ═══ TOP BADGES (lebih kecil) ═══
        # Gold (kiri)
        gold_bg = pygame.Rect(30, 20, 200, 28)
        pygame.draw.rect(self.screen, (40, 30, 10), gold_bg,
                         border_radius=14)
        pygame.draw.rect(self.screen, GOLD, gold_bg, 2,
                         border_radius=14)
        pygame.draw.circle(self.screen, (255, 200, 50),
                           (gold_bg.x + 18, gold_bg.centery), 8)
        pygame.draw.circle(self.screen, (200, 150, 30),
                           (gold_bg.x + 18, gold_bg.centery), 8, 2)
        dollar = self.font_tiny.render("$", True, (100, 60, 10))
        dollar_rect = dollar.get_rect(
            center=(gold_bg.x + 18, gold_bg.centery))
        self.screen.blit(dollar, dollar_rect)
        gold_text = self.font_small.render(
            f"HERO GOLD: {self.meta_gold:,}", True, GOLD)
        self.screen.blit(gold_text, (gold_bg.x + 32, gold_bg.y + 6))

        # Bosses (kanan)
        boss_count = len(self.save_data.get("unlocked_bosses", []))
        boss_bg = pygame.Rect(SCREEN_WIDTH - 240, 20, 210, 28)
        pygame.draw.rect(self.screen, (20, 20, 40), boss_bg,
                         border_radius=14)
        pygame.draw.rect(self.screen, (150, 200, 255), boss_bg, 2,
                         border_radius=14)
        boss_text = self.font_small.render(
            f"BOSSES DEFEATED: {boss_count}", True, (180, 220, 255))
        self.screen.blit(boss_text, (boss_bg.x + 12, boss_bg.y + 6))

        # ═══ TABS (compact) ═══
        tab_y = 78
        tab_h = 32
        tabs = [
            ('starter', 'STARTER HEROES', (100, 200, 255)),
            ('mini_boss', 'MINI BOSSES', (255, 150, 100)),
            ('true_boss', 'TRUE BOSSES', (255, 80, 100)),
        ]

        tab_w = 200
        total_w = tab_w * len(tabs) + 8 * (len(tabs) - 1)
        tab_start_x = cx - total_w // 2

        for i, (tab_id, tab_label, tab_color) in enumerate(tabs):
            tx = tab_start_x + i * (tab_w + 8)
            tab_rect = pygame.Rect(tx, tab_y, tab_w, tab_h)

            is_active = self.shop_tab == tab_id
            is_hover = self.hover_button == f'tab_{tab_id}'

            if is_active:
                pygame.draw.rect(self.screen, (40, 50, 80),
                                 tab_rect, border_radius=6)
                pygame.draw.rect(self.screen, tab_color,
                                 tab_rect, 3, border_radius=6)
            else:
                bg = (30, 35, 55) if is_hover else (20, 25, 40)
                pygame.draw.rect(self.screen, bg,
                                 tab_rect, border_radius=6)
                pygame.draw.rect(self.screen, (80, 90, 110),
                                 tab_rect, 2, border_radius=6)

            text_color = tab_color if is_active else (150, 160, 180)
            tab_text = self.font_small.render(tab_label, True, text_color)
            tab_text_rect = tab_text.get_rect(center=tab_rect.center)
            self.screen.blit(tab_text, tab_text_rect)

            self.buttons[f'tab_{tab_id}'] = tab_rect

        # ═══ CONTENT PANEL ═══
        panel_w = 1220
        panel_h = SCREEN_HEIGHT - 170  # Dynamic height
        panel_x = cx - panel_w // 2
        panel_y = 118

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (20, 25, 40, 225),
                         (0, 0, panel_w, panel_h), border_radius=12)
        self.screen.blit(panel, (panel_x, panel_y))

        tab_border_color = {
            'starter': (100, 200, 255),
            'mini_boss': (255, 150, 100),
            'true_boss': (255, 80, 100),
        }[self.shop_tab]
        pygame.draw.rect(self.screen, tab_border_color,
                         (panel_x, panel_y, panel_w, panel_h),
                         2, border_radius=12)

        # ═══ DEVELOPER TOP UP (testing only) ═══
        if DEV_TOPUP_ENABLED:
            topup_title = get_font(14).render(
                "DEV TOP UP", True, (255, 190, 80))
            topup_x = panel_x + panel_w - 355
            topup_y = panel_y + 7
            self.screen.blit(topup_title, (topup_x, topup_y + 5))
            for i, amount in enumerate((1000, 10000, 100000)):
                bx = topup_x + 70 + i * 86
                rect = pygame.Rect(bx, topup_y, 80, 25)
                pygame.draw.rect(self.screen, (65, 45, 15), rect,
                                 border_radius=5)
                pygame.draw.rect(self.screen, (255, 200, 80), rect,
                                 1, border_radius=5)
                text = self.font_tiny.render(
                    f"+{amount:,}", True, (255, 230, 135))
                self.screen.blit(text, text.get_rect(center=rect.center))
                self.buttons[f"dev_topup_{amount}"] = rect

        # ═══ FILTER HEROES ═══
        hero_catalog = get_all_hero_types()
        filtered_heroes = []

        for hero_type, stats in hero_catalog.items():
            if self.shop_tab == 'starter':
                if not stats.get("is_boss_hero"):
                    filtered_heroes.append((hero_type, stats))
            elif self.shop_tab == 'mini_boss':
                if stats.get("is_boss_hero") and \
                        stats.get("boss_class") == "mini":
                    filtered_heroes.append((hero_type, stats))
            elif self.shop_tab == 'true_boss':
                if stats.get("is_boss_hero") and \
                        stats.get("boss_class") == "true":
                    filtered_heroes.append((hero_type, stats))

        # ═══ SECTION HEADER ═══
        section_titles = {
            'starter': 'Base Heroes - Available from the start',
            'mini_boss': 'Mini Boss Heroes - Defeat wave bosses to unlock',
            'true_boss': 'True Boss Heroes - Ultimate endgame rewards',
        }
        section_desc = self.font_tiny.render(
            section_titles[self.shop_tab], True, (180, 190, 210))
        self.screen.blit(section_desc, (panel_x + 20, panel_y + 12))

        pygame.draw.line(self.screen, (60, 70, 90),
                         (panel_x + 15, panel_y + 30),
                         (panel_x + panel_w - 15, panel_y + 30), 1)

        # ═══ EMPTY STATE ═══
        if not filtered_heroes:
            no_hero = self.font_medium.render(
                "No heroes in this category yet.",
                True, (150, 150, 170))
            no_hero_rect = no_hero.get_rect(
                center=(cx, panel_y + panel_h // 2))
            self.screen.blit(no_hero, no_hero_rect)
        else:
            # ═══ CARDS GRID (compact) ═══
            card_w = 380
            card_h = 145  # ← COMPACT! (dari 200)
            gap_x = 15
            gap_y = 12
            cols = 3

            total_cards_w = cols * card_w + (cols - 1) * gap_x
            cards_start_x = cx - total_cards_w // 2

            # Content area inside panel
            content_top = panel_y + 38
            content_bottom = panel_y + panel_h - 5
            content_height = content_bottom - content_top

            # Calculate scroll
            total_rows = (len(filtered_heroes) + cols - 1) // cols
            total_content_h = total_rows * (card_h + gap_y)
            max_scroll = max(0, total_content_h - content_height)

            # Reset scroll saat ganti tab
            self._meta_shop_scroll = max(0,
                                         min(max_scroll, self._meta_shop_scroll))

            # Clip area
            clip_rect = pygame.Rect(panel_x, content_top,
                                    panel_w, content_height)
            old_clip = self.screen.get_clip()
            self.screen.set_clip(clip_rect)

            for i, (hero_type, stats) in enumerate(filtered_heroes):
                col = i % cols
                row = i // cols
                card_x = cards_start_x + col * (card_w + gap_x)
                card_y = content_top + row * (card_h + gap_y) \
                         - self._meta_shop_scroll

                # Skip off-screen
                if card_y + card_h < content_top or card_y > content_bottom:
                    continue

                self._draw_meta_hero_card(hero_type, stats,
                                          card_x, card_y,
                                          card_w, card_h)

            self.screen.set_clip(old_clip)

            # Scroll indicator
            if max_scroll > 0:
                self._draw_meta_scroll_indicator(
                    panel_x + panel_w - 18, content_top,
                    content_height,
                    self._meta_shop_scroll, max_scroll)

        # ═══ BACK BUTTON (fixed) ═══
        self._draw_menu_button("back_to_main", "BACK",
                               cx, SCREEN_HEIGHT - 32,
                               (150, 150, 150),
                               width=200, height=38)

    def _draw_meta_scroll_indicator(self, x, y, height,
                                    scroll_pos, max_scroll):
        """Scroll indicator untuk meta hero shop"""
        pygame.draw.rect(self.screen, (30, 35, 50),
                         (x, y, 6, height), border_radius=3)
        if max_scroll > 0:
            thumb_ratio = height / (height + max_scroll)
            thumb_h = max(18, int(height * thumb_ratio))
            thumb_y = y + int((height - thumb_h) *
                              (scroll_pos / max_scroll))
            pygame.draw.rect(self.screen, (100, 130, 180),
                             (x, thumb_y, 6, thumb_h), border_radius=3)
            pygame.draw.rect(self.screen, (150, 180, 220),
                             (x + 1, thumb_y + 1, 4, thumb_h - 2),
                             border_radius=2)

    # ================================
    # GANTI method _draw_meta_hero_card() di menu.py
    # COMPACT HORIZONTAL CARD (tinggi 145px)
    # ================================

    def _draw_meta_hero_card(self, hero_type, stats, x, y, w, h):
        """Compact horizontal hero card for meta shop"""
        purchased = hero_type in self.save_data.get("purchased_heroes", [])
        boss_req = stats.get("unlock_require_boss")
        boss_ready = boss_req is None or \
                     boss_req in self.save_data.get("unlocked_bosses", [])
        unlock_cost = stats.get("unlock_cost", 600)
        can_unlock = (
            DEV_UNLIMITED_HERO_GOLD
            or self.meta_gold >= unlock_cost
        )

        color_main = stats["color"]
        color_dark = stats["color_dark"]

        # ═══ CARD BG ═══
        if purchased:
            bg_color = (25, 42, 30)
        elif not boss_ready:
            bg_color = (42, 22, 28)
        else:
            bg_color = (25, 28, 48)

        # Shadow
        shadow_surf = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 100),
                         (3, 3, w, h), border_radius=8)
        self.screen.blit(shadow_surf, (x - 3, y - 3))

        pygame.draw.rect(self.screen, bg_color,
                         (x, y, w, h), border_radius=8)

        # Border
        if purchased:
            border_color = (100, 220, 100)
        elif not boss_ready:
            border_color = (200, 80, 80)
        elif can_unlock:
            border_color = (255, 220, 100)
        else:
            border_color = (100, 130, 180)

        pygame.draw.rect(self.screen, border_color,
                         (x, y, w, h), 2, border_radius=8)

        # ═══ LEFT: PORTRAIT (kecil) ═══
        portrait_size = 72
        portrait_x = x + 10
        portrait_y = y + (h - portrait_size) // 2

        # Portrait bg
        pygame.draw.rect(self.screen, (12, 18, 28),
                         (portrait_x, portrait_y,
                          portrait_size, portrait_size),
                         border_radius=4)
        portrait_border = color_main if boss_ready else (80, 80, 80)
        pygame.draw.rect(self.screen, portrait_border,
                         (portrait_x, portrait_y,
                          portrait_size, portrait_size),
                         1, border_radius=4)

        HeroPortraits.draw(
            self.screen, hero_type,
            portrait_x + portrait_size // 2,
            portrait_y + portrait_size // 2 + 3,
            stats, owned=(not boss_ready))

        # ═══ CENTER: INFO ═══
        info_x = x + 10 + portrait_size + 10
        info_y = y + 8

        # Name
        name_color = (255, 255, 255) if boss_ready else (160, 160, 160)
        name_font = get_font(22)
        name = name_font.render(stats["name"], True, name_color)
        self.screen.blit(name, (info_x, info_y))

        # Title
        title = self.font_tiny.render(stats["title"], True, (180, 190, 210))
        self.screen.blit(title, (info_x, info_y + 20))

        # Role badge (compact)
        role_bg = pygame.Rect(info_x, info_y + 38, 120, 18)
        pygame.draw.rect(self.screen, (0, 0, 0), role_bg, border_radius=9)
        pygame.draw.rect(self.screen, border_color, role_bg, 1,
                         border_radius=9)
        role_font = get_font(13)
        role = role_font.render(stats["role"].upper(), True, border_color)
        role_rect = role.get_rect(center=role_bg.center)
        self.screen.blit(role, role_rect)

        # Category tag
        if stats.get("is_boss_hero"):
            if stats.get("boss_class") == "true":
                tag_text = "★ TRUE BOSS"
                tag_color = (255, 100, 100)
            else:
                tag_text = "◆ MINI BOSS"
                tag_color = (255, 180, 100)
        else:
            tag_text = "STARTER"
            tag_color = (150, 200, 255)

        tag_surf = self.font_tiny.render(tag_text, True, tag_color)
        self.screen.blit(tag_surf, (info_x, info_y + 62))

        # ═══ STATUS + COST (di bawah info) ═══
        status_y = info_y + 82

        if purchased:
            status_text = self.font_small.render(
                "✓ UNLOCKED", True, (100, 255, 100))
            self.screen.blit(status_text, (info_x, status_y))

        elif not boss_ready:
            req_name = stats.get("source_boss_name", hero_type.title())
            lock_text = self.font_small.render(
                "🔒 LOCKED", True, (255, 120, 120))
            self.screen.blit(lock_text, (info_x, status_y))

            req_font = get_font(14)
            req_text = req_font.render(
                f"Defeat: {req_name}", True, (200, 160, 160))
            self.screen.blit(req_text, (info_x, status_y + 18))

        else:
            cost_label = get_font(13).render(
                "UNLOCK COST", True, (140, 150, 170))
            self.screen.blit(cost_label, (info_x, status_y))

            cost_color = (120, 255, 150) if can_unlock else (160, 160, 160)
            if DEV_UNLIMITED_HERO_GOLD:
                cost_label_text = "DEV: UNLIMITED"
            elif unlock_cost <= 0:
                cost_label_text = "FREE"
            else:
                cost_label_text = f"{unlock_cost:,} G"
            cost_val = self.font_small.render(cost_label_text, True, cost_color)
            self.screen.blit(cost_val, (info_x, status_y + 14))

        # ═══ RIGHT: BUTTON (kecil, vertical center) ═══
        btn_w = 100
        btn_h = 30
        btn_x = x + w - btn_w - 12
        btn_y = y + (h - btn_h) // 2

        btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

        if purchased:
            pygame.draw.rect(self.screen, (35, 90, 35), btn_rect,
                             border_radius=5)
            pygame.draw.rect(self.screen, (100, 200, 100), btn_rect,
                             2, border_radius=5)
            txt = self.font_small.render("OWNED", True, (180, 255, 180))
            txt_rect = txt.get_rect(center=btn_rect.center)
            self.screen.blit(txt, txt_rect)

        elif not boss_ready:
            pygame.draw.rect(self.screen, (65, 25, 25), btn_rect,
                             border_radius=5)
            pygame.draw.rect(self.screen, (160, 70, 70), btn_rect,
                             2, border_radius=5)
            txt = self.font_small.render("LOCKED", True, (200, 140, 140))
            txt_rect = txt.get_rect(center=btn_rect.center)
            self.screen.blit(txt, txt_rect)

        else:
            is_hover = self.hover_button == f"meta_unlock_{hero_type}"

            if can_unlock:
                if is_hover:
                    glow_surf = pygame.Surface(
                        (btn_w + 8, btn_h + 8), pygame.SRCALPHA)
                    pygame.draw.rect(glow_surf, (100, 255, 100, 90),
                                     (0, 0, btn_w + 8, btn_h + 8),
                                     border_radius=7)
                    self.screen.blit(glow_surf,
                                     (btn_rect.x - 4, btn_rect.y - 4))

                btn_color = (45, 170, 50) if is_hover else (35, 130, 40)
                border = (140, 255, 140) if is_hover else (100, 210, 100)
            else:
                btn_color = (55, 55, 55)
                border = (110, 110, 110)

            pygame.draw.rect(self.screen, btn_color, btn_rect,
                             border_radius=5)
            pygame.draw.rect(self.screen, border, btn_rect, 2,
                             border_radius=5)

            button_label = "DEV UNLOCK" if DEV_UNLIMITED_HERO_GOLD else (
                "FREE" if unlock_cost <= 0 else "UNLOCK"
            )
            txt = self.font_small.render(button_label, True, WHITE)
            txt_rect = txt.get_rect(center=btn_rect.center)
            self.screen.blit(txt, txt_rect)

            self.buttons[f"meta_unlock_{hero_type}"] = btn_rect

    def _unlock_hero_in_meta_shop(self, hero_type):
        hero_catalog = get_all_hero_types()
        if hero_type not in hero_catalog:
            SoundManager().play('ui_error', volume_mult=0.4)
            return

        stats = hero_catalog[hero_type]
        purchased = self.save_data.setdefault("purchased_heroes", [])
        unlocked_bosses = self.save_data.setdefault("unlocked_bosses", [])

        if hero_type in purchased:
            SoundManager().play('ui_error', volume_mult=0.4)
            return

        boss_req = stats.get("unlock_require_boss")
        if boss_req and boss_req not in unlocked_bosses:
            SoundManager().play('ui_error', volume_mult=0.4)
            return

        cost = stats.get("unlock_cost", 600)
        if not DEV_UNLIMITED_HERO_GOLD and self.meta_gold < cost:
            SoundManager().play('ui_error', volume_mult=0.4)
            return

        if not DEV_UNLIMITED_HERO_GOLD:
            self.meta_gold -= cost
        purchased.append(hero_type)
        self.save_data["meta_gold"] = self.meta_gold

        SaveManager.save(self.save_data)
        SoundManager().play('ui_buy', volume_mult=0.7)

    def _dev_topup_gold(self, amount):
        """Testing-only top up. Tidak tersedia jika flag dimatikan."""
        if not DEV_TOPUP_ENABLED or amount <= 0:
            return
        self.meta_gold += int(amount)
        self.save_data["meta_gold"] = self.meta_gold
        SaveManager.save(self.save_data)
        SoundManager().play('ui_buy', volume_mult=0.5)
        print(f"[DEV TOP UP] +{amount:,} Hero Gold")

    def _blit_shadow(self, surf, text_surf, topleft, offset=(2, 2)):
        """Blit teks dengan bayangan gelap lembut di belakangnya."""
        sh = text_surf.copy()
        sh.fill((0, 0, 0, 150), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(sh, (topleft[0] + offset[0], topleft[1] + offset[1]))

    def _draw_menu_button(self, btn_id, label, cx, cy,
                          color, width=300, height=55, icon=None,
                          label_font_size=None):
        """Tombol menu dark-fantasy: panel kaca gelap + aksen warna +
        ikon primitif + sudut emas, dengan efek hover glow.
        label_font_size: opsional, ukuran font label (default font_button)."""
        from mobile.perf import Quality as _Qg
        is_hover = self.hover_button == btn_id

        rect = pygame.Rect(cx - width // 2, cy - height // 2,
                           width, height)
        if is_hover:
            rect.inflate_ip(18, 8)

        # ── Glow hover ──
        if is_hover:
            if _Qg.cheap_alpha:
                glow = pygame.Surface((rect.width + 28, rect.height + 28),
                                      pygame.SRCALPHA)
                pygame.draw.rect(glow, (*color, 70),
                                 (0, 0, glow.get_width(),
                                  glow.get_height()),
                                 border_radius=16)
                self.screen.blit(glow, (rect.x - 14, rect.y - 14))
            else:
                pygame.draw.rect(self.screen, color,
                                 rect.inflate(10, 10), 2, border_radius=14)

        # ── Shadow ──
        sh = rect.copy()
        sh.move_ip(4, 5)
        if _Qg.cheap_alpha:
            shadow_surf = pygame.Surface((sh.width, sh.height),
                                         pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 110),
                             (0, 0, sh.width, sh.height), border_radius=12)
            self.screen.blit(shadow_surf, sh.topleft)
        else:
            pygame.draw.rect(self.screen, (8, 6, 14), sh, border_radius=12)

        # ── Panel ──
        base = (26, 32, 52) if is_hover else (17, 21, 36)
        pygame.draw.rect(self.screen, base, rect, border_radius=12)
        hl = pygame.Surface((rect.width - 8, 6), pygame.SRCALPHA)
        hl.fill((255, 255, 255, 36))
        self.screen.blit(hl, (rect.x + 4, rect.y + 3))

        # Aksen kiri warna identitas
        pygame.draw.rect(self.screen, color,
                         (rect.x + 6, rect.y + 10, 4,
                          rect.height - 20), border_radius=2)

        # Border
        bcol = color if is_hover else (95, 105, 135)
        pygame.draw.rect(self.screen, bcol, rect,
                         2 if is_hover else 1, border_radius=12)

        # ── Sudut emas ──
        gold = (255, 220, 100)
        c_len = 10
        for (ax, ay, dx, dy) in ((rect.x + 2, rect.y + 2, 1, 1),
                                 (rect.right - 2, rect.bottom - 2, -1, -1)):
            pygame.draw.line(self.screen, gold,
                             (ax, ay), (ax + dx * c_len, ay), 2)
            pygame.draw.line(self.screen, gold,
                             (ax, ay), (ax, ay + dy * c_len), 2)

        # ── Ikon badge ──
        if icon is not None:
            ic_x = rect.x + 34
            ic_y = rect.centery
            pygame.draw.circle(self.screen, (10, 12, 22), (ic_x, ic_y), 17)
            pygame.draw.circle(self.screen, color, (ic_x, ic_y), 17, 2)
            self._draw_button_icon(self.screen, icon, ic_x, ic_y, color)
            text_cx = rect.x + width // 2 + 14
        else:
            text_cx = rect.centerx

        # ── Label (font bisa di-override per tombol) ──
        label_font = self.font_button
        if label_font_size:
            label_font = get_font(label_font_size, "body_bold")
        if _Qg.cheap_alpha:
            sh_text = label_font.render(label, True, (0, 0, 0))
            self.screen.blit(sh_text, sh_text.get_rect(
                center=(text_cx + 2, rect.centery + 2)))
        text = label_font.render(label, True, WHITE)
        self.screen.blit(text, text.get_rect(
            center=(text_cx, rect.centery)))

        self.buttons[btn_id] = rect

    def _draw_button_icon(self, surface, icon, cx, cy, color):
        """Ikon tombol menu (digambar dengan primitif pygame)."""
        if icon == "play":
            pygame.draw.polygon(surface, color,
                                [(cx - 7, cy - 11), (cx - 7, cy + 11),
                                 (cx + 10, cy)])
        elif icon == "coin":
            pygame.draw.circle(surface, (255, 200, 60), (cx, cy), 9)
            pygame.draw.circle(surface, (200, 140, 30), (cx, cy), 9, 2)
            pygame.draw.circle(surface, (200, 140, 30), (cx, cy), 4)
            pygame.draw.line(surface, (200, 140, 30),
                             (cx, cy - 4), (cx, cy + 4), 2)
        elif icon == "pad":
            pygame.draw.rect(surface, color,
                             (cx - 12, cy - 8, 24, 16), border_radius=7)
            pygame.draw.circle(surface, (10, 12, 22), (cx - 7, cy + 7), 4)
            pygame.draw.circle(surface, (10, 12, 22), (cx + 7, cy + 7), 4)
        elif icon == "help":
            txt = self.font_small.render("?", True, color)
            surface.blit(txt, txt.get_rect(center=(cx, cy)))
        elif icon == "gear":
            pygame.draw.circle(surface, color, (cx, cy), 8, 2)
            for i in range(6):
                a = i * math.pi / 3
                pygame.draw.line(
                    surface, color,
                    (cx + int(math.cos(a) * 8), cy + int(math.sin(a) * 8)),
                    (cx + int(math.cos(a) * 12), cy + int(math.sin(a) * 12)),
                    2)
        elif icon == "star":
            for (dx, dy) in ((1, 0), (0, 1), (1, 1), (1, -1)):
                pygame.draw.line(surface, color,
                                 (cx - dx * 9, cy - dy * 9),
                                 (cx + dx * 9, cy + dy * 9), 2)
            pygame.draw.circle(surface, color, (cx, cy), 3)
        elif icon == "quit":
            pygame.draw.line(surface, color,
                             (cx - 7, cy - 7), (cx + 7, cy + 7), 3)
            pygame.draw.line(surface, color,
                             (cx + 7, cy - 7), (cx - 7, cy + 7), 3)
    def _draw_how_to_play(self):
        """Tutorial screen"""
        cx = SCREEN_WIDTH // 2

        # Title
        title = self.font_title.render("HOW TO PLAY", True, (100, 200, 255))
        title_rect = title.get_rect(center=(cx, 80))
        self._blit_shadow(self.screen, title, title_rect.topleft)
        self.screen.blit(title, title_rect)

        # Content panel - larger, English, no overlap
        panel_w = 900
        panel_h = 500
        panel_x = cx - panel_w // 2
        panel_y = 130

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (20, 25, 40, 220),
                         (0, 0, panel_w, panel_h),
                         border_radius=12)
        self.screen.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(self.screen, (100, 200, 255),
                         (panel_x, panel_y, panel_w, panel_h),
                         2, border_radius=12)

        sections = [
            ("OBJECTIVE",
             "Destroy the enemy castle before they destroy yours!",
             (255, 220, 100)),
            ("BUILDING TOWERS",
             "Tap empty build slots (+) to build towers. Cost: 100 gold.",
             (100, 200, 255)),
            ("HEROES",
             "Buy heroes from Hero Shop. Tap to select, tap enemy to attack.",
             (100, 255, 100)),
            ("SKILLS",
             "Q,W,E,R auto-cast when enemies nearby. R = Ultimate!",
             (255, 150, 100)),
            ("UPGRADES",
             "Tap towers, castle, or hero to upgrade. Stronger = win!",
             (200, 150, 255)),
            ("CASTLE SHIELD",
             "Castle has shield before Wave 10. Prevents early loss.",
             (100, 220, 255)),
        ]

        y = panel_y + 20
        for icon_title, desc, color in sections:
            title_text = self.font_medium.render(icon_title, True, color)
            self.screen.blit(title_text, (panel_x + 30, y))
            y += 26

            words = desc.split()
            line = ""
            line_y = y
            for word in words:
                test_line = line + word + " "
                if self.font_small.size(test_line)[0] > panel_w - 80:
                    text = self.font_small.render(line, True, (200, 200, 220))
                    self.screen.blit(text, (panel_x + 40, line_y))
                    line_y += 20
                    line = word + " "
                else:
                    line = test_line
            if line:
                text = self.font_small.render(line, True, (200, 200, 220))
                self.screen.blit(text, (panel_x + 40, line_y))
                line_y += 20

            y = line_y + 12

        # Back button
        self._draw_menu_button("back_to_main", "BACK", cx,
                                SCREEN_HEIGHT - 60,
                                (150, 150, 150),
                                width=200, height=45)

    # ═══════════════════════════════════════
    # SETTINGS
    # ═══════════════════════════════════════

    def _draw_settings(self):
        """Settings screen dengan categorized sections"""
        cx = SCREEN_WIDTH // 2

        # Title
        title = self.font_title.render(
            "SETTINGS", True, (200, 180, 100))
        title_rect = title.get_rect(center=(cx, 58))
        self._blit_shadow(self.screen, title, title_rect.topleft)
        self.screen.blit(title, title_rect)

        # Panel
        panel_w = 900
        panel_h = 570
        panel_x = cx - panel_w // 2
        panel_y = 118

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (20, 25, 40, 225),
                         (0, 0, panel_w, panel_h),
                         border_radius=12)
        self.screen.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(self.screen, (200, 180, 100),
                         (panel_x, panel_y, panel_w, panel_h),
                         2, border_radius=12)

        # Split into 2 columns
        col1_x = panel_x + 40
        col2_x = panel_x + panel_w // 2 + 20

        # ═══ COLUMN 1: AUDIO SETTINGS ═══
        audio_y = panel_y + 30
        self._draw_settings_section_header(
            col1_x, audio_y, "🔊 AUDIO", (100, 220, 255))

        sound_mgr = SoundManager()
        audio_settings = [
            ("Master Volume", sound_mgr.master_volume, "master"),
            ("SFX Volume", sound_mgr.sfx_volume, "sfx"),
            ("Music Volume", sound_mgr.bgm_volume, "bgm"),
            ("Voice Volume", sound_mgr.voice_volume, "voice"),
        ]

        y = audio_y + 45
        for label, value, setting_id in audio_settings:
            self._draw_volume_slider(
                col1_x, y, 340,
                label, value, setting_id)
            y += 65

        # ═══ COLUMN 2: GAMEPLAY SETTINGS ═══
        gameplay_y = panel_y + 30
        self._draw_settings_section_header(
            col2_x, gameplay_y, "⚔ GAMEPLAY", (100, 255, 150))

        settings = GameSettings()

        # Screen Shake toggle
        y = gameplay_y + 45
        self._draw_toggle_setting(
            col2_x, y, 340,
            "Screen Shake",
            settings.screen_shake_enabled,
            "toggle_shake")

        # Damage Numbers toggle
        y += 50
        self._draw_toggle_setting(
            col2_x, y, 340,
            "Damage Numbers",
            settings.damage_numbers_enabled,
            "toggle_damage")

        # Game Speed
        y += 60
        self._draw_option_setting(
            col2_x, y, 340,
            "Game Speed",
            settings.get_speed_label(),
            "speed")

        # ═══ GRAPHICS SECTION ═══
        graphics_y = gameplay_y + 240
        self._draw_settings_section_header(
            col2_x, graphics_y, "🖥 GRAPHICS", (255, 180, 100))

        # FPS Limit
        y = graphics_y + 45
        self._draw_option_setting(
            col2_x, y, 340,
            "FPS Limit",
            settings.get_fps_label(),
            "fps")

        # ═══ DANGER ZONE SECTION ═══
        danger_y = panel_y + panel_h - 100
        self._draw_settings_section_header(
            col1_x, danger_y, "⚠  DANGER ZONE", (255, 100, 100))

        # Reset button
        reset_btn_rect = pygame.Rect(
            col1_x, danger_y + 40, 340, 40)

        mx, my = pygame.mouse.get_pos()
        reset_hover = reset_btn_rect.collidepoint(mx, my)

        reset_color = (180, 40, 40) if reset_hover else (140, 30, 30)
        reset_border = (255, 100, 100) if reset_hover \
            else (200, 80, 80)

        pygame.draw.rect(self.screen, reset_color,
                         reset_btn_rect, border_radius=6)
        pygame.draw.rect(self.screen, reset_border,
                         reset_btn_rect, 2, border_radius=6)

        reset_text = self.font_small.render(
            "RESET SAVE SLOT",
            True, (255, 220, 220))
        reset_text_rect = reset_text.get_rect(
            center=reset_btn_rect.center)
        self.screen.blit(reset_text, reset_text_rect)

        self.buttons['reset_save'] = reset_btn_rect

        # Back button
        self._draw_menu_button("back_to_main", "BACK", cx,
                               SCREEN_HEIGHT - 40,
                               (150, 150, 150),
                               width=200, height=42)

        # Reset confirmation dialog (kalau ada)
        if hasattr(self, 'reset_confirm') and self.reset_confirm:
            self._draw_reset_confirm_dialog()

    def _draw_settings_section_header(self, x, y, title, color):
        """Draw section header dengan garis dekoratif"""
        # Title
        header_text = self.font_medium.render(title, True, color)
        self.screen.blit(header_text, (x, y))

        # Underline
        text_width = self.font_medium.size(title)[0]
        pygame.draw.line(self.screen, color,
                         (x, y + 30),
                         (x + text_width + 10, y + 30), 2)

    def _draw_toggle_setting(self, x, y, width, label, is_on,
                             setting_id):
        """Draw toggle switch setting"""
        # Label
        label_text = self.font_small.render(label, True, WHITE)
        self.screen.blit(label_text, (x, y + 10))

        # Toggle switch (di kanan)
        toggle_w = 60
        toggle_h = 26
        toggle_x = x + width - toggle_w
        toggle_y = y + 8

        toggle_rect = pygame.Rect(
            toggle_x, toggle_y, toggle_w, toggle_h)

        # Hover
        mx, my = pygame.mouse.get_pos()
        is_hover = toggle_rect.collidepoint(mx, my)

        # Bg color
        if is_on:
            bg_color = (60, 180, 80) if not is_hover else (80, 220, 100)
            border_col = (100, 220, 100) if not is_hover \
                else (150, 255, 150)
        else:
            bg_color = (80, 80, 80) if not is_hover else (100, 100, 100)
            border_col = (150, 150, 150) if not is_hover \
                else (200, 200, 200)

        pygame.draw.rect(self.screen, bg_color,
                         toggle_rect, border_radius=13)
        pygame.draw.rect(self.screen, border_col,
                         toggle_rect, 2, border_radius=13)

        # Knob
        knob_size = 20
        if is_on:
            knob_x = toggle_x + toggle_w - knob_size - 3
        else:
            knob_x = toggle_x + 3
        knob_y = toggle_y + 3

        pygame.draw.circle(self.screen, WHITE,
                           (knob_x + knob_size // 2,
                            knob_y + knob_size // 2),
                           knob_size // 2)

        # ON/OFF text
        on_off_text = get_font(14).render(
            "ON" if is_on else "OFF", True, WHITE)
        on_off_rect = on_off_text.get_rect(center=toggle_rect.center)
        self.screen.blit(on_off_text, on_off_rect)

        self.buttons[setting_id] = toggle_rect

    def _draw_option_setting(self, x, y, width, label, current_value,
                             setting_id):
        """Draw option cycler setting (dengan tombol < >)"""
        # Label
        label_text = self.font_small.render(label, True, WHITE)
        self.screen.blit(label_text, (x, y + 10))

        # Value display (tengah)
        value_bg_w = 120
        value_bg_h = 30
        value_bg_x = x + width - value_bg_w - 40
        value_bg_y = y + 6

        pygame.draw.rect(self.screen, (30, 40, 60),
                         (value_bg_x, value_bg_y,
                          value_bg_w, value_bg_h),
                         border_radius=4)
        pygame.draw.rect(self.screen, (100, 130, 180),
                         (value_bg_x, value_bg_y,
                          value_bg_w, value_bg_h),
                         2, border_radius=4)

        value_text = self.font_small.render(
            current_value, True, (255, 220, 100))
        value_text_rect = value_text.get_rect(
            center=(value_bg_x + value_bg_w // 2,
                    value_bg_y + value_bg_h // 2))
        self.screen.blit(value_text, value_text_rect)

        # Left arrow (<)
        left_rect = pygame.Rect(
            value_bg_x - 32, value_bg_y, 26, value_bg_h)

        mx, my = pygame.mouse.get_pos()
        left_hover = left_rect.collidepoint(mx, my)

        left_color = (100, 130, 180) if left_hover else (60, 80, 110)
        pygame.draw.rect(self.screen, left_color,
                         left_rect, border_radius=4)
        pygame.draw.rect(self.screen, (150, 180, 220),
                         left_rect, 1, border_radius=4)

        left_arrow = self.font_medium.render("<", True, WHITE)
        left_arrow_rect = left_arrow.get_rect(center=left_rect.center)
        self.screen.blit(left_arrow, left_arrow_rect)

        self.buttons[f'{setting_id}_prev'] = left_rect

        # Right arrow (>)
        right_rect = pygame.Rect(
            value_bg_x + value_bg_w + 6, value_bg_y,
            26, value_bg_h)

        right_hover = right_rect.collidepoint(mx, my)
        right_color = (100, 130, 180) if right_hover else (60, 80, 110)

        pygame.draw.rect(self.screen, right_color,
                         right_rect, border_radius=4)
        pygame.draw.rect(self.screen, (150, 180, 220),
                         right_rect, 1, border_radius=4)

        right_arrow = self.font_medium.render(">", True, WHITE)
        right_arrow_rect = right_arrow.get_rect(
            center=right_rect.center)
        self.screen.blit(right_arrow, right_arrow_rect)

        self.buttons[f'{setting_id}_next'] = right_rect

    def _draw_reset_confirm_dialog(self):
        """Confirmation dialog untuk reset save"""
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        # Dark overlay
        from mobile.perf import darken
        darken(self.screen, 200)

        # Dialog box
        dialog_w = 500
        dialog_h = 260
        dialog_x = cx - dialog_w // 2
        dialog_y = cy - dialog_h // 2

        # Shadow
        shadow_surf = pygame.Surface(
            (dialog_w + 10, dialog_h + 10), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 150),
                         (5, 5, dialog_w, dialog_h), border_radius=12)
        self.screen.blit(shadow_surf, (dialog_x - 5, dialog_y - 5))

        # Bg
        pygame.draw.rect(self.screen, (40, 25, 30),
                         (dialog_x, dialog_y, dialog_w, dialog_h),
                         border_radius=12)
        pygame.draw.rect(self.screen, (220, 60, 60),
                         (dialog_x, dialog_y, dialog_w, dialog_h),
                         3, border_radius=12)

        # Warning
        icon_font = get_font(48)
        warning_text = icon_font.render(
            "⚠  RESET SAVE?", True, (255, 100, 100))
        warning_rect = warning_text.get_rect(
            center=(cx, dialog_y + 45))
        self.screen.blit(warning_text, warning_rect)

        # Get current slot
        from _system import SaveManager
        current_slot = SaveManager.get_current_slot()

        # Message
        msg_text = self.font_medium.render(
            f"Reset SAVE GAME {current_slot}?",
            True, (255, 255, 255))
        msg_rect = msg_text.get_rect(center=(cx, dialog_y + 95))
        self.screen.blit(msg_text, msg_rect)

        warn_text = self.font_small.render(
            "All progress, gold, and heroes will be lost!",
            True, (220, 180, 180))
        warn_rect = warn_text.get_rect(center=(cx, dialog_y + 125))
        self.screen.blit(warn_text, warn_rect)

        warn2_text = self.font_small.render(
            "This action cannot be undone.",
            True, (220, 180, 180))
        warn2_rect = warn2_text.get_rect(
            center=(cx, dialog_y + 148))
        self.screen.blit(warn2_text, warn2_rect)

        # Buttons
        btn_y = dialog_y + dialog_h - 55
        btn_w = 200
        btn_h = 40
        btn_gap = 20

        # YES (destructive)
        yes_x = cx - btn_w - btn_gap // 2
        yes_rect = pygame.Rect(yes_x, btn_y, btn_w, btn_h)

        mx, my = pygame.mouse.get_pos()
        yes_hover = yes_rect.collidepoint(mx, my)

        yes_color = (200, 50, 50) if yes_hover else (160, 40, 40)
        yes_border = (255, 100, 100) if yes_hover else (200, 80, 80)

        pygame.draw.rect(self.screen, yes_color,
                         yes_rect, border_radius=6)
        pygame.draw.rect(self.screen, yes_border,
                         yes_rect, 2, border_radius=6)

        yes_text = self.font_medium.render(
            "YES, RESET", True, (255, 255, 255))
        yes_text_rect = yes_text.get_rect(center=yes_rect.center)
        self.screen.blit(yes_text, yes_text_rect)

        self.buttons["reset_confirm_yes"] = yes_rect

        # NO (safe)
        no_x = cx + btn_gap // 2
        no_rect = pygame.Rect(no_x, btn_y, btn_w, btn_h)

        no_hover = no_rect.collidepoint(mx, my)
        no_color = (80, 100, 120) if no_hover else (60, 80, 100)
        no_border = (150, 180, 200) if no_hover else (120, 150, 180)

        pygame.draw.rect(self.screen, no_color,
                         no_rect, border_radius=6)
        pygame.draw.rect(self.screen, no_border,
                         no_rect, 2, border_radius=6)

        no_text = self.font_medium.render(
            "CANCEL", True, (255, 255, 255))
        no_text_rect = no_text.get_rect(center=no_rect.center)
        self.screen.blit(no_text, no_text_rect)

        self.buttons["reset_confirm_no"] = no_rect

    def _draw_volume_slider(self, x, y, width, label, value, setting_id):
        """Draw volume slider dengan buttons +/-"""
        # Label
        label_text = self.font_small.render(label, True, WHITE)
        self.screen.blit(label_text, (x, y))

        # Value text
        value_text = self.font_small.render(
            f"{int(value * 100)}%", True, (255, 220, 100))
        value_rect = value_text.get_rect(topright=(x + width, y))
        self.screen.blit(value_text, value_rect)

        # Slider bar
        bar_y = y + 30
        bar_h = 8
        pygame.draw.rect(self.screen, (60, 60, 70),
                         (x, bar_y, width - 100, bar_h),
                         border_radius=4)

        # Fill
        fill_w = int((width - 100) * value)
        if fill_w > 0:
            pygame.draw.rect(self.screen, (100, 200, 255),
                             (x, bar_y, fill_w, bar_h),
                             border_radius=4)

        # Border
        pygame.draw.rect(self.screen, WHITE,
                         (x, bar_y, width - 100, bar_h),
                         1, border_radius=4)

        # Slider knob
        knob_x = x + fill_w
        pygame.draw.circle(self.screen, WHITE,
                           (knob_x, bar_y + bar_h // 2), 10)
        pygame.draw.circle(self.screen, (100, 200, 255),
                           (knob_x, bar_y + bar_h // 2), 8)

        # Minus button
        minus_rect = pygame.Rect(x + width - 80, bar_y - 6, 25, 25)
        is_hover_minus = self.hover_button == f'vol_{setting_id}_minus'
        color_minus = (255, 100, 100) if is_hover_minus else (200, 80, 80)
        pygame.draw.rect(self.screen, color_minus, minus_rect,
                         border_radius=4)
        pygame.draw.rect(self.screen, WHITE, minus_rect, 1,
                         border_radius=4)
        minus_t = self.font_medium.render("-", True, WHITE)
        minus_text_rect = minus_t.get_rect(center=minus_rect.center)
        self.screen.blit(minus_t, minus_text_rect)
        self.buttons[f'vol_{setting_id}_minus'] = minus_rect

        # Plus button
        plus_rect = pygame.Rect(x + width - 40, bar_y - 6, 25, 25)
        is_hover_plus = self.hover_button == f'vol_{setting_id}_plus'
        color_plus = (100, 255, 100) if is_hover_plus else (80, 200, 80)
        pygame.draw.rect(self.screen, color_plus, plus_rect,
                         border_radius=4)
        pygame.draw.rect(self.screen, WHITE, plus_rect, 1,
                         border_radius=4)
        plus_t = self.font_medium.render("+", True, WHITE)
        plus_text_rect = plus_t.get_rect(center=plus_rect.center)
        self.screen.blit(plus_t, plus_text_rect)
        self.buttons[f'vol_{setting_id}_plus'] = plus_rect

    # ═══════════════════════════════════════
    # CREDITS
    # ═══════════════════════════════════════

    def _draw_credits(self):
        """Credits screen"""
        cx = SCREEN_WIDTH // 2

        # Title
        title = self.font_title.render("CREDITS", True, (200, 120, 200))
        title_rect = title.get_rect(center=(cx, 80))
        self._blit_shadow(self.screen, title, title_rect.topleft)
        self.screen.blit(title, title_rect)

        # Panel
        panel_w = 700
        panel_h = 450
        panel_x = cx - panel_w // 2
        panel_y = 150

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (20, 25, 40, 220),
                         (0, 0, panel_w, panel_h),
                         border_radius=12)
        self.screen.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(self.screen, (200, 120, 200),
                         (panel_x, panel_y, panel_w, panel_h),
                         2, border_radius=12)

        # Credits content
        credits = [
            ("Tower Defense Battle Arena", (255, 220, 100), self.font_medium),
            ("", None, None),
            ("Game Design & Programming", (100, 200, 255), self.font_small),
            ("Dharmawan Toxi", WHITE, self.font_medium),
            ("", None, None),
            ("Art Direction", (100, 200, 255), self.font_small),
            ("Retro Pixel Style", WHITE, self.font_medium),
            ("", None, None),
            ("Sound Effects & Music", (100, 200, 255), self.font_small),
            ("Custom SFX Library", WHITE, self.font_medium),
            ("", None, None),
            ("Special Thanks", (100, 200, 255), self.font_small),
            ("Pygame Community", WHITE, self.font_medium),
            ("Python 3.10+", WHITE, self.font_medium),
            ("", None, None),
            ("Made with ❤️ using Pygame", (255, 150, 200), self.font_small),
        ]

        y = panel_y + 30
        for text, color, font in credits:
            if not text or not font:
                y += 15
                continue
            surf = font.render(text, True, color)
            rect = surf.get_rect(center=(cx, y))
            self.screen.blit(surf, rect)
            y += 30

        # Back button
        self._draw_menu_button("back_to_main", "BACK", cx,
                                SCREEN_HEIGHT - 60,
                                (150, 150, 150),
                                width=200, height=45)

    # ═══════════════════════════════════════
    # PAUSE MENU
    # ═══════════════════════════════════════

    def _draw_pause_menu(self):
        """In-game pause menu"""
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        # Pause panel
        panel_w = 400
        panel_h = 400
        panel_x = cx - panel_w // 2
        panel_y = cy - panel_h // 2

        # Shadow
        shadow = pygame.Surface((panel_w + 10, panel_h + 10),
                                 pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 150),
                         (5, 5, panel_w, panel_h),
                         border_radius=15)
        self.screen.blit(shadow, (panel_x - 5, panel_y - 5))

        # Panel background
        pygame.draw.rect(self.screen, (25, 30, 45),
                         (panel_x, panel_y, panel_w, panel_h),
                         border_radius=15)
        pygame.draw.rect(self.screen, (255, 220, 100),
                         (panel_x, panel_y, panel_w, panel_h),
                         3, border_radius=15)

        # Title
        title = self.font_title.render("PAUSED", True, (255, 220, 100))
        title_rect = title.get_rect(center=(cx, panel_y + 62))
        self._blit_shadow(self.screen, title, title_rect.topleft)
        self.screen.blit(title, title_rect)

        # Decorative line
        pygame.draw.line(self.screen, (255, 220, 100),
                         (panel_x + 40, panel_y + 122),
                         (panel_x + panel_w - 40, panel_y + 122), 2)

        # Buttons
        button_y_start = panel_y + 160
        button_gap = 60

        buttons_data = [
            ("resume", "RESUME", (100, 200, 100)),
            ("settings_pause", "SETTINGS", (200, 180, 100)),
            ("main_menu", "MAIN MENU", (100, 180, 255)),
            ("quit", "QUIT GAME", (220, 80, 80)),
        ]

        for i, (btn_id, label, color) in enumerate(buttons_data):
            y = button_y_start + i * button_gap
            self._draw_menu_button(btn_id, label, cx, y, color,
                                    width=280, height=45)

    # ═══════════════════════════════════════
    # BUTTON ACTIONS
    # ═══════════════════════════════════════

    def _get_continue_level(self):
        """Level untuk tombol CONTINUE:
        - level berikutnya setelah level tertinggi yang sudah diselesaikan
        - kalau sudah tamat semua, replay level terakhir
        - kalau belum ada yang selesai, pakai last_played_level (default 1)
        """
        try:
            from levels import get_next_level
            completed = self.save_data.get("completed_levels", [])
            if completed:
                highest = max(completed)
                nxt = get_next_level(highest)
                return nxt if nxt else highest
            last = self.save_data.get("last_played_level", 1)
            return last if isinstance(last, int) and last >= 1 else 1
        except Exception:
            return 1

    def _on_button_click(self, btn_id):
        """Handle button click actions"""
        if btn_id == "continue":
            # Lanjut dari level terakhir (bypass slot select)
            self.selected_level = self._get_continue_level()
            self.action = "play"
        elif btn_id == "play":
            self.state = MenuState.SLOT_SELECT
        elif btn_id == "input_select":
            # Toggle input mode (keyboard <-> controller)
            if hasattr(self, 'controller_mgr') and self.controller_mgr:
                if self.controller_mgr.is_controller_mode():
                    self.controller_mgr.set_mode('keyboard')
                else:
                    self.controller_mgr.rescan()
                    if self.controller_mgr.connected:
                        self.controller_mgr.debug_print()
                        self.controller_mgr.set_mode('controller')
                    else:
                        print("[INPUT] No controller detected!")
                        print("[INPUT] Pastikan controller ON")
                        print("[INPUT] Di ROG Ally: enable Gamepad mode")
        elif btn_id == "level_back":
            self.state = MenuState.MAIN

        elif btn_id.startswith("level_"):
            try:
                lvl_num = int(btn_id.replace("level_", ""))
            except ValueError:
                return
            # Cek unlock status
            from levels import is_level_unlocked
            completed = self.save_data.get("completed_levels", [])
            if is_level_unlocked(lvl_num, completed):
                self.selected_level = lvl_num
                self.action = "play"
            else:
                SoundManager().play('ui_error', volume_mult=0.4)

        elif btn_id == "level_back":
            self.state = MenuState.MAIN
        elif btn_id == "how_to_play":
            self.state = MenuState.HOW_TO_PLAY
        elif btn_id == "settings":
            self.state = MenuState.SETTINGS
        elif btn_id == "settings_pause":
            self.state = MenuState.SETTINGS
        elif btn_id == "credits":
            self.state = MenuState.CREDITS
        elif btn_id == "quit":
            self.action = "quit"
        elif btn_id == "resume":
            self.action = "resume"
        elif btn_id == "main_menu":
            self.action = "main_menu"
        elif btn_id == "back_to_main":
            if self.pause_mode:
                self.state = MenuState.PAUSE
            else:
                self.state = MenuState.MAIN
        elif btn_id == "hero_shop":
            self.reload_progress()
            self.shop_tab = 'starter'  # ← RESET tab saat masuk shop
            self.state = MenuState.HERO_SHOP

        elif btn_id.startswith("tab_"):
            self.shop_tab = btn_id.replace("tab_", "")
            self._meta_shop_scroll = 0  # ← RESET scroll saat ganti tab
            SoundManager().play('ui_click', volume_mult=0.4)

        elif btn_id.startswith("meta_unlock_"):
            hero_type = btn_id.replace("meta_unlock_", "")
            self._unlock_hero_in_meta_shop(hero_type)
        elif btn_id.startswith("dev_topup_"):
            try:
                amount = int(btn_id.replace("dev_topup_", ""))
                self._dev_topup_gold(amount)
            except ValueError:
                pass

        # ═══ TOGGLES ═══
        elif btn_id == "toggle_shake":
            settings = GameSettings()
            settings.set_screen_shake(not settings.screen_shake_enabled)
            # Sync ke game yang sedang jalan supaya efeknya langsung
            # terasa tanpa restart level.
            try:
                import __main__
                gi = getattr(__main__, 'game_instance', None)
                if gi is not None and getattr(gi, 'effects', None):
                    gi.effects.sync_settings()
            except Exception:
                pass
            SoundManager().play('ui_click', volume_mult=0.4)

        elif btn_id == "toggle_damage":
            settings = GameSettings()
            settings.set_damage_numbers(
                not settings.damage_numbers_enabled)
            SoundManager().play('ui_click', volume_mult=0.4)

        # ═══ GAME SPEED CYCLER ═══
        elif btn_id == "speed_prev":
            settings = GameSettings()
            speeds = [0.5, 1.0, 1.5, 2.0]
            try:
                idx = speeds.index(settings.game_speed)
                new_idx = (idx - 1) % len(speeds)
                settings.set_game_speed(speeds[new_idx])
            except ValueError:
                settings.set_game_speed(1.0)
            SoundManager().play('ui_click', volume_mult=0.4)

        elif btn_id == "speed_next":
            settings = GameSettings()
            speeds = [0.5, 1.0, 1.5, 2.0]
            try:
                idx = speeds.index(settings.game_speed)
                new_idx = (idx + 1) % len(speeds)
                settings.set_game_speed(speeds[new_idx])
            except ValueError:
                settings.set_game_speed(1.0)
            SoundManager().play('ui_click', volume_mult=0.4)

        # ═══ FPS LIMIT CYCLER ═══
        elif btn_id == "fps_prev":
            settings = GameSettings()
            fps_options = [30, 60, 120, 0]  # 0 = unlimited
            try:
                idx = fps_options.index(settings.fps_limit)
                new_idx = (idx - 1) % len(fps_options)
                settings.set_fps_limit(fps_options[new_idx])
            except ValueError:
                settings.set_fps_limit(60)
            SoundManager().play('ui_click', volume_mult=0.4)

        elif btn_id == "fps_next":
            settings = GameSettings()
            fps_options = [30, 60, 120, 0]
            try:
                idx = fps_options.index(settings.fps_limit)
                new_idx = (idx + 1) % len(fps_options)
                settings.set_fps_limit(fps_options[new_idx])
            except ValueError:
                settings.set_fps_limit(60)
            SoundManager().play('ui_click', volume_mult=0.4)

        # ═══ RESET SAVE ═══
        elif btn_id == "reset_save":
            self.reset_confirm = True
            SoundManager().play('ui_click', volume_mult=0.4)

        elif btn_id == "reset_confirm_yes":
            # Delete current slot
            from _system import SaveManager
            current_slot = SaveManager.get_current_slot()
            SaveManager.delete_slot(current_slot)
            self.reset_confirm = False
            self.reload_progress()
            SoundManager().play('ui_upgrade', volume_mult=0.6)

        elif btn_id == "reset_confirm_no":
            self.reset_confirm = False
            SoundManager().play('ui_click', volume_mult=0.4)

        # Volume adjustments
        elif btn_id.startswith('vol_') and btn_id.endswith('_plus'):
            self._adjust_volume(btn_id[4:-5], 0.1)
        elif btn_id.startswith('vol_') and btn_id.endswith('_minus'):
            self._adjust_volume(btn_id[4:-6], -0.1)
        elif btn_id == "slot_delete_yes":
            if hasattr(self, 'slot_delete_confirm') and \
                    self.slot_delete_confirm is not None:
                from _system import SaveManager
                SaveManager.delete_slot(self.slot_delete_confirm)
                self.slot_delete_confirm = None
                SoundManager().play('ui_upgrade', volume_mult=0.5)

        elif btn_id == "slot_delete_no":
            self.slot_delete_confirm = None
            SoundManager().play('ui_click', volume_mult=0.4)

        elif btn_id.startswith("slot_select_"):
            try:
                slot_num = int(btn_id.replace("slot_select_", ""))
            except ValueError:
                return
            from _system import SaveManager
            SaveManager.set_current_slot(slot_num)
            self.reload_progress()
            self.state = MenuState.LEVEL_SELECT
            SoundManager().play('ui_click', volume_mult=0.6)

        elif btn_id.startswith("slot_delete_"):
            try:
                slot_num = int(btn_id.replace("slot_delete_", ""))
            except ValueError:
                return
            # Set confirming state (tampil confirm dialog)
            self.slot_delete_confirm = slot_num
            SoundManager().play('ui_click', volume_mult=0.4)

        elif btn_id == "slot_back":
            self.state = MenuState.MAIN
            SoundManager().play('ui_click', volume_mult=0.4)

    def _toggle_input_mode(self):
        """Toggle antara keyboard & controller"""
        if not hasattr(self, 'controller_mgr') or not self.controller_mgr:
            return

        if self.controller_mgr.is_controller_mode():
            self.controller_mgr.set_mode('keyboard')
        else:
            if self.controller_mgr.connected:
                self.controller_mgr.set_mode('controller')
            else:
                # No controller detected, rescan
                self.controller_mgr.rescan()
                if self.controller_mgr.connected:
                    self.controller_mgr.set_mode('controller')
                else:
                    print("[INPUT] No controller detected!")

    def _adjust_volume(self, setting_id, delta):
        """Adjust volume setting"""
        sound_mgr = SoundManager()

        if setting_id == "master":
            new_val = max(0.0, min(1.0, sound_mgr.master_volume + delta))
            sound_mgr.set_master_volume(new_val)
        elif setting_id == "sfx":
            sound_mgr.sfx_volume = max(0.0, min(1.0,
                                                sound_mgr.sfx_volume + delta))
        elif setting_id == "bgm":
            sound_mgr.bgm_volume = max(0.0, min(1.0,
                                                sound_mgr.bgm_volume + delta))
            sound_mgr.update_bgm_volume()
        elif setting_id == "voice":
            sound_mgr.voice_volume = max(0.0, min(1.0,
                                                   sound_mgr.voice_volume + delta))

    # ═══════════════════════════════════════
    # UTILITY
    # ═══════════════════════════════════════

    def reset(self):
        self.reload_progress()
        self.state = MenuState.MAIN
        self.action = None
        self.pause_mode = False

    def show_pause(self):
        """Trigger pause menu"""
        self.state = MenuState.PAUSE
        self.pause_mode = True
        self.action = None

    def show_main(self):
        """Trigger main menu"""
        self.reload_progress()
        self.state = MenuState.MAIN
        self.pause_mode = False
        self.action = None




# ================================


# ====================================================================
# game_input.py
# ====================================================================

# ================================
# GAME_INPUT.PY - Input Handler
# Semua click & keyboard handling ada disini
# ================================

import pygame
import math
from _system import SoundManager


class InputHandler:
    """
    Handle semua input dari player:
    - Mouse click (kiri, kanan)
    - Keyboard input
    - UI button click detection
    """

    def __init__(self, game):
        self.game = game

    # ═══════════════════════════════════════
    # MAIN CLICK DISPATCHER
    # ═══════════════════════════════════════

    def handle_click(self, pos, button):
        """
        Main entry untuk mouse click.
        Prioritas:
        1. Panel hero info (paling prioritas)
        2. Shop overlay
        3. Build popup
        4. Tower/Nexus popup
        5. World click (build slot, hero, tower, dll)
        """
        mx, my = pos
        g = self.game
        # ═══ VICTORY SCREEN: PLAY NEXT LEVEL BUTTON ═══
        if g.state == "victory" and 'play_next_level' in g.ui_buttons:
            btn_rect = g.ui_buttons['play_next_level']
            if btn_rect.collidepoint(mx, my):
                from levels import get_next_level
                next_lvl = get_next_level(g.level_number)
                if next_lvl:
                    g.next_level_requested = True
                    from _system import SoundManager
                    SoundManager().play('ui_click', volume_mult=0.7)
                    return

        # ═══ 0. Panel hero info (paling prioritas) ═══
        if g.selected_hero and g.selected_hero.alive:
            # Posisi diambil dari yang BENAR-BENAR digambar
            # (lihat HeroPanel.draw). Angka tetap di bawah hanya
            # cadangan untuk frame pertama sebelum panel sempat
            # digambar sekali.
            _hp = getattr(g, "ui_rects", {}).get("hero_panel")
            if _hp is None:
                _hp = pygame.Rect(20, SCREEN_HEIGHT - 185, 260, 165)

            if _hp.collidepoint(mx, my):
                if self.handle_hero_panel_click(mx, my, button):
                    return
                return  # klik di panel = jangan trigger yang lain

        # ═══ Shop overlay ═══
        if g.shop_open:
            self.handle_shop_click(mx, my, button)
            return

        # ═══ SCROLL saat popup terbuka ═══
        # Event scroll (4/5) tidak di-handle oleh handler popup, jadi
        # dulu langsung jatuh ke close_popup() -> popup "muncul lalu
        # hilang". Di mode controller ini parah karena stick kanan
        # mengirim event scroll terus-menerus.
        # Scroll tidak ada artinya untuk popup, jadi cukup diabaikan.
        if button in (4, 5):
            if (g.build_popup_slot is not None
                    or g.popup_target is not None):
                return

        # ═══ Build popup ═══
        if g.build_popup_slot is not None:
            if self.handle_build_popup_click(mx, my, button):
                return
            g.close_build_popup()

        # ═══ Tower/Nexus popup ═══
        if g.popup_target is not None:
            if self.handle_popup_click(mx, my, button):
                return
            g.close_popup()

        # ═══ WORLD CLICKS ═══
        if button == 1:
            self._handle_left_click(mx, my)
        elif button == 3:
            self._handle_right_click(mx, my)

    # ═══════════════════════════════════════
    # LEFT CLICK (button 1)
    # ═══════════════════════════════════════

    def _handle_left_click(self, mx, my):
        # ═══ KLIK DI LUAR ARENA DIABAIKAN ═══
        # Dipanggil SETELAH semua tombol UI (popup upgrade, popup
        # tower, popup castle) diperiksa di handle_click. Kalau sampai
        # ke sini berarti ketukan mengenai ruang kosong; kalau itu ada
        # di panel kanan, jangan diartikan sebagai perintah gerak hero.
        if mx >= SCREEN_WIDTH or my >= SCREEN_HEIGHT:
            return
        """Handle klik kiri di world"""
        g = self.game

        # 1. Shop building
        if g.map_renderer.is_click_on_shop(mx, my):
            g.shop_open = True
            SoundManager().play('ui_click', volume_mult=0.5)
            return

        # 2. Build slot
        clicked_slot = self._get_clicked_build_slot(mx, my)
        if clicked_slot:
            g.open_build_popup(clicked_slot)
            return

        # 3. Nexus (blue)
        dist_blue = math.hypot(BLUE_BASE_X - mx, BLUE_BASE_Y - my)
        if dist_blue <= 80:
            g.open_popup(g.blue_base, "nexus_blue")
            return

        # 4. Nexus (red)
        dist_red = math.hypot(RED_BASE_X - mx, RED_BASE_Y - my)
        if dist_red <= 80:
            g.open_popup(g.red_base, "nexus_red")
            return

        # 5. Hero click (select/switch)
        clicked_hero = self._get_clicked_hero(mx, my)
        if clicked_hero:
            self._select_hero(clicked_hero)
            return

        # 6. Hero command (attack/move)
        if g.selected_hero and g.selected_hero.alive:
            self._handle_hero_command(mx, my)
            return

        # 7. Tower click (no hero selected)
        clicked_tower = self._get_clicked_tower(mx, my)
        if clicked_tower and clicked_tower.team == "blue":
            g.open_popup(clicked_tower, "tower")
            return

        # 8. Klik di kosong = deselect
        if g.selected_hero:
            g.selected_hero.selected = False
            g.selected_hero = None

    def _select_hero(self, hero):
        """Select hero (dengan proper deselection)"""
        g = self.game

        if g.selected_tower:
            g.selected_tower.selected = False
            g.selected_tower = None
        if g.selected_hero and g.selected_hero != hero:
            g.selected_hero.selected = False

        hero.selected = True
        g.selected_hero = hero

    def _handle_hero_command(self, mx, my):
        """Command hero yang selected (attack/move)"""
        g = self.game

        # Cek klik musuh
        enemies = ([m for m in g.minions if m.team == "red"] +
                   [t for t in g.towers if t.team == "red"] +
                   [h for h in g.ai.heroes if h.alive])

        clicked_enemy = None
        for e in enemies:
            hit_radius = getattr(e, 'radius', 25)
            dist = math.hypot(e.x - mx, e.y - my)
            if dist <= hit_radius + 8:
                clicked_enemy = e
                break

        if clicked_enemy:
            # Attack enemy
            g.selected_hero.follow_target = clicked_enemy
            g.selected_hero.destination = None
            g.selected_hero.is_retreating = False
            return

        # Cek klik tower blue
        clicked_tower = self._get_clicked_tower(mx, my)
        if clicked_tower and clicked_tower.team == "blue":
            g.selected_hero.selected = False
            g.selected_hero = None
            g.open_popup(clicked_tower, "tower")
            return

        # Klik area kosong = MOVE
        g.selected_hero.move_to(mx, my)

    # ═══════════════════════════════════════
    # RIGHT CLICK (button 3)
    # ═══════════════════════════════════════

    def _handle_right_click(self, mx, my):
        """Handle klik kanan"""
        g = self.game
        g.close_popup()

        if g.selected_hero and g.selected_hero.alive:
            g.selected_hero.move_to(mx, my)

    # ═══════════════════════════════════════
    # POPUP HANDLERS
    # ═══════════════════════════════════════

    @staticmethod
    def _kena(rect, mx, my, longgar=22):
        """
        Uji sentuh dengan pelonggaran.

        Beberapa tombol popup sangat kecil - tombol tutup (X) hanya
        20x20 px, sekitar 12dp, jauh di bawah standar sentuh 48dp.
        Melebarkan area ujinya jauh lebih aman daripada mengubah
        gambarnya satu per satu.
        """
        return rect.inflate(longgar, longgar).collidepoint(mx, my)

    def handle_hero_panel_click(self, mx, my, button):
        """Klik di panel hero info (bottom-left)"""
        if button != 1:
            return False

        g = self.game

        for btn_id, rect in list(g.ui_buttons.items()):
            # Close button (X)
            if btn_id == 'hero_close':
                if self._kena(rect, mx, my):
                    if g.selected_hero:
                        g.selected_hero.selected = False
                        g.selected_hero = None
                        SoundManager().play('ui_click', volume_mult=0.4)
                    return True

            # Upgrade button
            elif btn_id == 'popup_upgrade_hero':
                if self._kena(rect, mx, my):
                    self._try_upgrade_hero()
                    return True

            # ═══ AUTO-CAST TOGGLE ═══
            elif btn_id == 'toggle_autocast':
                # ═══ TIDAK LAGI BISA DIMATIKAN (v29) ═══
                # Tombol Q/W/E/R sudah dihapus, jadi mematikan
                # auto-cast akan membuat skill hero tidak pernah
                # keluar sama sekali - jebakan, bukan pilihan.
                # Tombolnya dipertahankan sebagai penanda status.
                if self._kena(rect, mx, my):
                    if g.selected_hero:
                        g.selected_hero.auto_cast_enabled = True
                    return True

        return False

    def _try_upgrade_hero(self):
        """Coba upgrade hero (dengan cek gold)"""
        g = self.game

        if not (g.selected_hero and g.selected_hero.alive):
            return
        if g.selected_hero.level >= MAX_HERO_LEVEL:
            return

        cost = g.selected_hero.upgrade_cost()
        if cost <= 0:
            return  # ← TAMBAH: block kalau cost 0 (sudah max)

        if g.gold >= cost:
            if g.selected_hero.upgrade():
                g.gold -= cost
                SoundManager().play('ui_upgrade')
                g.effects.add_damage_number(
                    int(g.selected_hero.x),
                    int(g.selected_hero.y - 30),
                    f"LV.{g.selected_hero.level}!",
                    is_critical=True)
        else:
            SoundManager().play('ui_error')

    def handle_build_popup_click(self, mx, my, button):
        """Klik di build popup"""
        if button != 1:
            return False

        g = self.game

        for btn_id, rect in list(g.ui_buttons.items()):
            if not btn_id.startswith('build_'):
                continue
            if self._kena(rect, mx, my):
                action = btn_id.replace('build_', '')

                if action == 'close':
                    g.close_build_popup()
                    return True
                elif action in ['archer', 'cannon', 'ice', 'mage']:
                    g.try_build_tower(action)
                    return True

        return False

    def handle_popup_click(self, mx, my, button):
        """Klik di tower/nexus popup"""
        if button != 1:
            return False

        g = self.game

        for btn_id, rect in list(g.ui_buttons.items()):
            if not btn_id.startswith('popup_'):
                continue
            if self._kena(rect, mx, my):
                action = btn_id.replace('popup_', '')

                if action == 'close':
                    g.close_popup()
                    return True

                elif action == 'upgrade_nexus':
                    g.try_upgrade_nexus()
                    return True

                elif action == 'upgrade_tower':
                    self._try_upgrade_tower()
                    return True

                elif action.startswith('upgrade_path_'):
                    path_type = action.replace('upgrade_path_', '')
                    self._try_upgrade_tower_path(path_type)
                    return True

                elif action == 'sell_tower':
                    self._try_sell_tower()
                    return True

                elif action == 'regen_shield':
                    self._try_activate_regen_shield()
                    return True

                elif action == 'upgrade_hero':
                    self._try_upgrade_hero()
                    return True

                return False
        return False

    def _try_upgrade_tower(self):
        """Upgrade tower (linear)"""
        g = self.game

        if not (g.selected_tower and g.selected_tower.is_player_built):
            return

        cost = g.selected_tower.upgrade_cost()
        if g.gold >= cost:
            if g.selected_tower.upgrade():
                g.gold -= cost
                SoundManager().play('ui_upgrade')
        else:
            SoundManager().play('ui_error')

    def _try_upgrade_tower_path(self, path_type):
        """Upgrade tower dengan path (untuk lvl 1→2)"""
        g = self.game

        if not (g.selected_tower and g.selected_tower.is_player_built):
            return

        cost = g.selected_tower.upgrade_cost(path_type)
        if g.gold >= cost:
            if g.selected_tower.upgrade(path_type):
                g.gold -= cost
                SoundManager().play('ui_upgrade')
        else:
            SoundManager().play('ui_error')

    def _try_sell_tower(self):
        """Jual tower yang selected"""
        g = self.game

        if not (g.selected_tower and g.selected_tower.is_player_built):
            return

        sell_val = g.selected_tower.sell_value()
        if sell_val == 0:
            sell_val = 50  # refund 50% dari 100G
        g.gold += sell_val

        # Mark slot as available lagi
        for slot in g.build_slots_blue:
            if slot['x'] == g.selected_tower.x and \
                    slot['y'] == g.selected_tower.y:
                slot['taken'] = False
                break

        g.towers.remove(g.selected_tower)
        SoundManager().play('ui_sell')
        g.close_popup()

    def _try_activate_regen_shield(self):
        """Beli & aktifkan Regen Shield untuk tower yang dipilih."""
        g = self.game

        if not (g.selected_tower and g.selected_tower.is_player_built):
            return
        tower = g.selected_tower
        if not tower.can_activate_regen_shield():
            SoundManager().play('ui_error')
            return

        cost = tower.regen_shield_cost()
        if g.gold < cost:
            SoundManager().play('ui_error')
            return

        if tower.activate_regen_shield():
            g.gold -= cost
            SoundManager().play('ui_upgrade')
            try:
                g.effects.add_damage_number(
                    int(tower.x), int(tower.y - 30),
                    "REGEN SHIELD!", is_critical=True)
            except Exception:
                pass

    def handle_shop_click(self, mx, my, button):
        """Klik di hero shop — pakai registered buttons"""
        g = self.game

        # Cek semua button di ui_buttons
        for btn_id, rect in list(g.ui_buttons.items()):
            if not rect.collidepoint(mx, my):
                continue

            # Close button
            if btn_id == 'shop_close':
                g.shop_open = False
                SoundManager().play('ui_click', volume_mult=0.4)
                return

            # ═══ TAB SWITCH ═══
            if btn_id.startswith('shop_tab_'):
                tab_id = btn_id.replace('shop_tab_', '')
                g._shop_tab = tab_id
                SoundManager().play('ui_click', volume_mult=0.4)
                return

            # ═══ SCROLL ═══
            if btn_id == 'shop_scroll_up':
                g._shop_scroll = max(0, g._shop_scroll - 80)
                return
            if btn_id == 'shop_scroll_down':
                g._shop_scroll += 80
                return

            # Buy button
            if btn_id.startswith('shop_buy_'):
                hero_type = btn_id.replace('shop_buy_', '')
                self._try_buy_hero(hero_type)
                return

        # Klik kanan atau di luar card = tutup shop
        if button == 3:
            g.shop_open = False

    def _try_buy_hero(self, hero_type):
        """Helper - summon hero pakai gold in-game"""
        g = self.game

        # Validasi: sudah unlock permanen?
        if hero_type not in g.purchased_heroes:
            SoundManager().play('ui_error', volume_mult=0.4)
            return

        # Cek duplikat
        if any(h.hero_type == hero_type for h in g.heroes):
            SoundManager().play('ui_error', volume_mult=0.4)
            return

        # Cek max heroes
        if len(g.heroes) >= MAX_HEROES_OWNED:
            SoundManager().play('ui_error', volume_mult=0.4)
            return

        # Cek gold
        all_heroes = get_all_hero_types()
        stats = all_heroes.get(hero_type, {})
        cost = stats.get("cost", 400)
        if g.gold < cost:
            SoundManager().play('ui_error', volume_mult=0.4)
            return

        # SUMMON (gold dipotong di try_buy_hero)
        g.try_buy_hero(hero_type)
    # ═══════════════════════════════════════
    # KEYBOARD INPUT
    # ═══════════════════════════════════════

    def handle_key(self, key):
        g = self.game

        # ═══ RESTART / BACK TO MENU (setelah victory/defeat) ═══
        if g.state != "playing":
            if key == pygame.K_r:
                # REPLAY current level
                g.replay_requested = True
            elif key == pygame.K_n and g.state == "victory":
                # NEXT LEVEL (only after victory)
                from levels import get_next_level
                next_lvl = get_next_level(g.level_number)
                if next_lvl:
                    g.next_level_requested = True
            elif key == pygame.K_ESCAPE:
                g.return_to_menu_requested = True
            return

        # ═══ GAMEPLAY KEYS ═══
        if key == pygame.K_h:
            # Toggle shop
            g.shop_open = not g.shop_open

        # ═══ HERO SKILLS (Q, W, E, R) ═══
        elif key == pygame.K_q:
            self._cast_hero_skill('q')

        elif key == pygame.K_w:
            self._cast_hero_skill('w')

        elif key == pygame.K_e:
            self._cast_hero_skill('e')

        elif key == pygame.K_r:
            self._cast_hero_skill('r')

    def _cast_hero_skill(self, skill_key):
        """Cast hero skill dengan sound feedback"""
        g = self.game

        if not (g.selected_hero and g.selected_hero.alive):
            return

        # ═══ MUSUH = minion + hero + BOSS AKTIF ═══
        # Mini/true boss adalah musuh tim merah juga. Sebelumnya
        # boss TIDAK ikut daftar musuh di cast manual, akibatnya
        # guard anti-buang-skill menolak cast saat musuh terdekat
        # hanyalah sang boss (hero "tidak bisa cast skill").
        units = g.minions + g.get_all_heroes()
        if g.active_boss and g.active_boss.alive:
            units = units + [g.active_boss]

        result = g.selected_hero.cast_skill(
            units, g.towers, g.bases,
            skill_key=skill_key)

        if result:
            # Volume berdasarkan skill (R = paling keras)
            volume = {'q': 0.8, 'w': 0.6, 'e': 0.7, 'r': 1.0}
            SoundManager().play('hero_skill',
                                 volume_mult=volume.get(skill_key, 0.7))
            # Screen shake untuk ultimate
            if skill_key == 'r':
                g.effects.shake_screen(15)
        else:
            SoundManager().play('ui_error', volume_mult=0.3)

    # ═══════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════

    def _get_clicked_tower(self, mx, my):
        """Cari tower yang di-klik"""
        for t in self.game.towers:
            dist = math.hypot(t.x - mx, t.y - my)
            if dist <= 25:
                return t
        return None

    def _get_clicked_build_slot(self, mx, my):
        """Cari build slot yang di-klik (blue team saja)"""
        for slot in self.game.build_slots_blue:
            if slot['taken']:
                continue
            dist = math.hypot(slot['x'] - mx, slot['y'] - my)
            if dist <= 20:
                return slot
        return None

    def _get_clicked_hero(self, mx, my):
        """Cari hero yang di-klik (blue team saja)"""
        for h in self.game.heroes:
            if not h.alive:
                continue
            dist = math.hypot(h.x - mx, h.y - my)
            if dist <= h.radius + 5:
                return h
        return None


# ====================================================================
# game_ui.py
# ====================================================================

# ================================
# GAME_UI.PY - UI Coordinator
# ================================
#
# Coordinator untuk semua UI rendering.
# Delegate ke components di ui_components/
#
# CARA TAMBAH UI COMPONENT BARU:
# ------------------------------
# 1. Buat file baru di ui_components/nama_component.py
# 2. Inherit dari BaseUIComponent:
#      class MyComponent(BaseUIComponent):
#          def draw(self, surface):
#              # ... logic
# 3. Register di ui_components/__init__.py:
#      try:
#          from ui_components.nama_component import MyComponent
#      except ImportError:
#          MyComponent = None
# 4. Init di UIRenderer.__init__:
#      self.my_component = MyComponent(self) if MyComponent else None
# 5. Buat delegate method:
#      def draw_my_thing(self, surface):
#          if self.my_component:
#              self.my_component.draw(surface)
#
# DONE! Component baru siap dipakai.
# ================================

import pygame


class UIRenderer:
    """
    Main UI coordinator.
    Semua UI rendering di-delegate ke component di ui_components/.
    """

    def __init__(self, game):
        self.game = game

        # ═══ INIT FONTS (shared across components) ═══
        self._init_fonts()

        # ═══ INIT UI COMPONENTS ═══
        self._init_components()

    def _init_fonts(self):
        """Init shared fonts untuk semua UI (profesional)"""
        self.font_huge = title_font(72)
        self.font_big = title_font(42)
        self.font_medium = get_font(26, "body_semibold")
        self.font_small = get_font(20, "body_medium")
        self.font_tiny = get_font(16, "body")

    def _init_components(self):
        """Init semua UI components"""
        from ui_components import (
            HoverIndicators,
            BuildSlots,
            ShopHints,
            BuildPopup,
            PopupRenderer,
            HeroPanel,
            Overlay,
            HeroShop,
            Notification,
        )

        # Components (lazy init - None kalau import fail)
        self.hover_component = HoverIndicators(self) if HoverIndicators else None
        self.build_slots_component = BuildSlots(self) if BuildSlots else None
        self.shop_hints_component = ShopHints(self) if ShopHints else None
        self.build_popup_component = BuildPopup(self) if BuildPopup else None
        self.popup_component = PopupRenderer(self) if PopupRenderer else None
        self.hero_panel_component = HeroPanel(self) if HeroPanel else None
        self.overlay_component = Overlay(self) if Overlay else None
        self.hero_shop_component = HeroShop(self) if HeroShop else None
        self.notification_component = Notification(self) if Notification else None

    # ═══════════════════════════════════════
    # HOVER STATES & INDICATORS
    # ═══════════════════════════════════════

    def update_hover_states(self):
        """Update mouse hover detection"""
        if self.hover_component:
            self.hover_component.update()

    def draw_hover_indicators(self, surface):
        """Draw hover indicators (range circle, slot glow, tooltips)"""
        if self.hover_component:
            self.hover_component.draw(surface)

    # ═══════════════════════════════════════
    # BUILD SLOTS
    # ═══════════════════════════════════════

    def draw_build_slots(self, surface):
        """Draw empty build slot markers (+)"""
        if self.build_slots_component:
            self.build_slots_component.draw(surface)

    # ═══════════════════════════════════════
    # SHOP HINTS
    # ═══════════════════════════════════════

    def draw_shop_hints(self, surface):
        """Draw floating hint di atas shop buildings"""
        if self.shop_hints_component:
            self.shop_hints_component.draw(surface)

    # ═══════════════════════════════════════
    # POPUPS
    # ═══════════════════════════════════════

    def draw_build_popup(self, surface):
        """Popup untuk pilih tipe tower saat build"""
        if self.build_popup_component:
            self.build_popup_component.draw(surface)

    def draw_popup(self, surface):
        """Main popup dispatcher (tower/nexus)"""
        if self.popup_component:
            self.popup_component.draw(surface)

    # ═══════════════════════════════════════
    # HERO UI
    # ═══════════════════════════════════════

    def draw_hero_info(self, surface):
        """Panel hero info di bottom-left saat hero selected"""
        if self.hero_panel_component:
            self.hero_panel_component.draw(surface)

    def draw_hero_shop(self, surface):
        """Modern hero shop overlay"""
        if self.hero_shop_component:
            self.hero_shop_component.draw(surface)

    # ═══════════════════════════════════════
    # OVERLAY (Victory/Defeat)
    # ═══════════════════════════════════════

    def draw_overlay(self, surface, title, color, subtitle, action):
        """Victory/Defeat elaborate overlay"""
        if self.overlay_component:
            self.overlay_component.draw(surface, title, color,
                                         subtitle, action)

    def draw_notifications(self, surface):
        """Draw notification popups"""
        if self.notification_component:
            self.notification_component.draw(surface)

    def add_notification(self, text, color=(255, 255, 255)):
        """
        Tambahkan notifikasi.

        Kalau panel kanan tersedia, notifikasi dikirim ke sana supaya
        tidak lagi melintas menutupi arena. Di layar tanpa panel,
        perilakunya persis seperti semula.
        """
        try:
            from mobile import sidepanel as _sp
            if _sp.beri_tahu_global(text, color):
                return
        except Exception:
            pass
        if self.notification_component:
            self.notification_component.add_notification(text, color)


# ====================================================================
# game_dev.py
# ====================================================================

# ================================
# GAME_DEV.PY - Developer Mode & Cheats
# ================================

import pygame
import math
from _entity import Minion


class DevMode:
    """
    Handle developer mode: cheats, debug info, dev panel.
    Semua fitur developer tools ada disini.
    """

    def __init__(self, game):
        self.game = game
        self.enabled = False
        self.panel_open = False
        self.show_debug = False

    # ═══════════════════════════════════════
    # HOTKEY HANDLING
    # ═══════════════════════════════════════

    def handle_hotkey(self, key):
        """
        Handle F1-F12 dan cheat keys.
        Return True kalau key di-handle.
        """
        # ─── TOGGLE KEYS (selalu aktif) ───
        if key == pygame.K_F1:
            self.enabled = not self.enabled
            status = "ON" if self.enabled else "OFF"
            print(f"[DEV MODE] {status}")
            return True

        if key == pygame.K_F2:
            self.panel_open = not self.panel_open
            return True

        if key == pygame.K_F3:
            self.show_debug = not self.show_debug
            return True

        # ─── CHEAT KEYS (hanya jika dev mode ON) ───
        if not self.enabled or self.game.state != "playing":
            return False

        # Gold cheats
        if key == pygame.K_F5:
            self.game.gold += 500
            print(f"[CHEAT] +500 Gold | Total: {self.game.gold}")
            return True
        elif key == pygame.K_F6:
            self.game.gold += 2000
            print(f"[CHEAT] +2000 Gold | Total: {self.game.gold}")
            return True
        elif key == pygame.K_F7:
            self.game.gold += 10000
            print(f"[CHEAT] +10000 Gold | Total: {self.game.gold}")
            return True
        elif key == pygame.K_F8:
            self.game.ai.gold += 2000
            print(f"[CHEAT] AI +2000 Gold | AI Total: {self.game.ai.gold}")
            return True

        # Gameplay cheats
        elif key == pygame.K_F9:
            self.game.wave_timer = 0
            print(f"[CHEAT] Skip to next wave!")
            return True

        elif key == pygame.K_F10:
            count = 0
            for t in self.game.towers:
                if t.team == "blue" and t.is_player_built:
                    while t.can_upgrade():
                        if t.level == 1:
                            t.upgrade("cannon")
                        else:
                            t.upgrade()
                        count += 1
            print(f"[CHEAT] Upgraded {count} tower levels!")
            return True

        elif key == pygame.K_F11:
            while self.game.blue_base.level < MAX_NEXUS_LEVEL:
                self.game.blue_base.upgrade()
            self.game.blue_base.hp = self.game.blue_base.max_hp
            print(f"[CHEAT] Blue Castle MAX Level!")
            return True

        elif key == pygame.K_F12:
            for h in self.game.heroes:
                while h.level < MAX_HERO_LEVEL:
                    h.upgrade()
                h.hp = h.max_hp
            print(f"[CHEAT] All heroes MAX level & full HP!")
            return True

        # Combat cheats
        elif key == pygame.K_k:
            count = 0
            for m in self.game.minions:
                if m.team == "red" and m.alive:
                    m.take_damage(99999, "blue")
                    count += 1
            for t in self.game.towers:
                if t.team == "red" and t.alive:
                    t.take_damage(99999, "blue")
                    count += 1
            print(f"[CHEAT] Killed {count} enemies!")
            return True

        elif key == pygame.K_t:
            for lane in ["top", "mid", "bot"]:
                lane_path = self.game.map_renderer.get_lane_path(lane)
                for _ in range(5):
                    self.game.minions.append(Minion(
                        "goblin", "red", lane,
                        self.game.red_base.level, lane_path))
            print(f"[CHEAT] Spawned test wave!")
            return True

        elif key == pygame.K_b:
            lane_path = self.game.map_renderer.get_lane_path("mid")
            self.game.minions.append(Minion(
                "troll", "red", "mid",
                5, lane_path))
            print(f"[CHEAT] Spawned test boss!")
            return True

        elif key == pygame.K_h and pygame.key.get_mods() & pygame.KMOD_SHIFT:
            self.game.blue_base.hp = self.game.blue_base.max_hp
            for t in self.game.towers:
                if t.team == "blue":
                    t.hp = t.max_hp
            for h in self.game.heroes:
                if h.alive:
                    h.hp = h.max_hp
            print(f"[CHEAT] Full heal all blue units!")
            return True

        elif key == pygame.K_g:
            if not hasattr(self, '_god_mode'):
                self._god_mode = False
            self._god_mode = not self._god_mode
            if self._god_mode:
                self.game.blue_base.max_hp = 999999
                self.game.blue_base.hp = 999999
                print(f"[CHEAT] GOD MODE ON - Castle invincible!")
            else:
                self.game.blue_base._apply_level_stats()
                print(f"[CHEAT] GOD MODE OFF")
            return True

        elif key == pygame.K_v:
            self.game.red_base.hp = 1
            self.game.red_base.take_damage(1, "blue")
            print(f"[CHEAT] Instant Victory!")
            return True

        elif key == pygame.K_l:
            self.game.blue_base.hp = 1
            self.game.blue_base.take_damage(1, "red")
            print(f"[CHEAT] Instant Defeat!")
            return True

        # ─── BOSS DEBUG ───
        elif key == pygame.K_F4:
            # Print boss status
            red_towers = sum(1 for t in self.game.towers
                             if t.team == "red" and t.alive)
            red_slots = sum(1 for s in self.game.build_slots_red
                            if s['taken'])
            print(f"[BOSS DEBUG]")
            print(f"  Wave: {self.game.wave_number}")
            print(f"  Red towers alive: {red_towers}")
            print(f"  Red slots taken: {red_slots}")
            print(f"  Total red defense: {red_towers + red_slots}")
            print(f"  Active boss: {self.game.active_boss}")
            print(f"  True boss spawned: {self.game.true_boss_spawned}")
            print(f"  Unlocked bosses: {self.game.unlocked_bosses}")
            # Controller debug juga
            if hasattr(self.game, 'controller_mgr') and \
                    self.game.controller_mgr:
                self.game.controller_mgr.rescan()
                self.game.controller_mgr.debug_print()
            return True

        return False
    # ═══════════════════════════════════════
    # DRAWING
    # ═══════════════════════════════════════

    def draw(self, surface):
        """Draw semua dev UI"""
        self._draw_indicator(surface)
        self._draw_panel(surface)
        self._draw_debug_info(surface)

    def _draw_indicator(self, surface):
        """Small badge di corner kalau dev mode ON"""
        if not self.enabled:
            return

        pulse = math.sin(self.game.animation_time * 0.1) * 0.3 + 0.7

        ind_font = get_font(18)
        text = ind_font.render("🔧 DEV MODE", True, (0, 255, 100))
        text_rect = text.get_rect()

        bg_rect = text_rect.inflate(16, 8)
        bg_rect.topleft = (10, 10)

        bg = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(bg, (0, 40, 20, int(200 * pulse)),
                         (0, 0, bg_rect.width, bg_rect.height),
                         border_radius=4)
        pygame.draw.rect(bg, (0, 255, 100, int(255 * pulse)),
                         (0, 0, bg_rect.width, bg_rect.height),
                         2, border_radius=4)
        surface.blit(bg, bg_rect.topleft)

        text_rect.center = bg_rect.center
        surface.blit(text, text_rect)

    def _draw_panel(self, surface):
        """Full dev control panel"""
        if not self.panel_open:
            return

        panel_w = 320
        panel_h = 500
        px = SCREEN_WIDTH - panel_w - 10
        py = 100

        # Shadow
        shadow = pygame.Surface((panel_w + 10, panel_h + 10),
                                pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 180),
                         (5, 5, panel_w, panel_h),
                         border_radius=8)
        surface.blit(shadow, (px - 5, py - 5))

        # Background
        pygame.draw.rect(surface, (20, 25, 40),
                         (px, py, panel_w, panel_h),
                         border_radius=8)
        pygame.draw.rect(surface, (0, 255, 100),
                         (px, py, panel_w, panel_h),
                         2, border_radius=8)

        # Title
        title_font = get_font(28)
        title = title_font.render("🔧 DEV PANEL", True, (0, 255, 100))
        surface.blit(title, (px + 15, py + 12))

        # Status
        status_font = get_font(16)
        status_text = "DEV MODE: ON" if self.enabled else "DEV MODE: OFF"
        status_color = (100, 255, 100) if self.enabled else (255, 100, 100)
        status = status_font.render(status_text, True, status_color)
        surface.blit(status, (px + 15, py + 40))

        pygame.draw.line(surface, (60, 80, 100),
                         (px + 10, py + 60),
                         (px + panel_w - 10, py + 60), 1)

        # Cheat list
        cheats = [
            ("═══ HOTKEYS ═══", (255, 200, 50), True),
            ("F1 - Toggle Dev Mode", (255, 255, 255), False),
            ("F2 - Toggle This Panel", (255, 255, 255), False),
            ("F3 - Toggle Debug Info", (255, 255, 255), False),
            ("", None, False),
            ("═══ GOLD (need dev) ═══", (255, 200, 50), True),
            ("F5 - +500 Gold", (100, 255, 100), False),
            ("F6 - +2000 Gold", (100, 255, 100), False),
            ("F7 - +10000 Gold", (100, 255, 100), False),
            ("F8 - AI +2000 Gold", (255, 150, 150), False),
            ("", None, False),
            ("═══ GAMEPLAY ═══", (255, 200, 50), True),
            ("F9 - Skip Wave", (150, 200, 255), False),
            ("F10 - Max All Towers", (150, 200, 255), False),
            ("F11 - Max Castle", (150, 200, 255), False),
            ("F12 - Max All Heroes", (150, 200, 255), False),
            ("", None, False),
            ("═══ COMBAT ═══", (255, 200, 50), True),
            ("K - Kill All Enemies", (255, 100, 100), False),
            ("T - Spawn Test Wave", (255, 150, 100), False),
            ("B - Spawn Boss (Troll)", (255, 100, 200), False),
            ("Shift+H - Heal All Blue", (100, 255, 200), False),
            ("G - Toggle God Mode", (255, 255, 100), False),
            ("", None, False),
            ("═══ WIN/LOSE ═══", (255, 200, 50), True),
            ("V - Instant Victory", (100, 255, 100), False),
            ("L - Instant Defeat", (255, 100, 100), False),
        ]

        y = py + 75
        line_font = get_font(15)
        header_font = get_font(16)

        for text, color, is_header in cheats:
            if not text:
                y += 6
                continue

            font = header_font if is_header else line_font
            text_surf = font.render(text, True, color)
            surface.blit(text_surf, (px + 15, y))
            y += 15

    def _draw_debug_info(self, surface):
        """Debug info overlay (bottom-left)"""
        if not self.show_debug:
            return

        g = self.game
        info_lines = [
            f"FPS: {int(pygame.time.Clock().get_fps())}",
            f"Minions: {len(g.minions)}",
            f"Towers: {len(g.towers)}",
            f"Heroes (Blue): {len(g.heroes)}",
            f"Heroes (Red): {len(g.ai.heroes)}",
            f"Bullets: {sum(len(t.bullets) for t in g.towers)}",
            f"Effects: {len(g.effects.floating_texts)} texts, "
            f"{len(g.effects.particles)} particles",
            f"Wave: {g.wave_number}",
            f"Player Gold: {g.gold}",
            f"AI Gold: {g.ai.gold}",
            f"Kills: {g.total_kills}",
            f"Max Combo: {g.max_combo}",
            f"State: {g.state}",
            f"Blue Castle HP: {g.blue_base.hp}/{g.blue_base.max_hp}",
            f"Red Castle HP: {g.red_base.hp}/{g.red_base.max_hp}",
        ]

        box_w = 260
        box_h = len(info_lines) * 16 + 20
        box_x = 10
        box_y = SCREEN_HEIGHT - box_h - 10

        bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (0, 0, 0, 180),
                         (0, 0, box_w, box_h),
                         border_radius=5)
        pygame.draw.rect(bg, (0, 255, 100, 200),
                         (0, 0, box_w, box_h),
                         1, border_radius=5)
        surface.blit(bg, (box_x, box_y))

        title_font = get_font(16)
        title = title_font.render("🔧 DEBUG INFO", True, (0, 255, 100))
        surface.blit(title, (box_x + 8, box_y + 5))

        info_font = get_font(14)
        for i, line in enumerate(info_lines):
            text = info_font.render(line, True, (200, 255, 200))
            surface.blit(text, (box_x + 8, box_y + 22 + i * 16))


# ====================================================================
# game_settings.py
# ====================================================================

# ================================
# game_settings.py
# Global game settings (persistent)
# ================================

import json
import os


SETTINGS_FILE = os.path.join("saves", "settings.json")


class GameSettings:
    """
    Persistent global settings (bukan per-save-slot).
    Singleton pattern.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_defaults()
            cls._instance._load()
        return cls._instance

    def _init_defaults(self):
        """Default settings"""
        # Audio (di-load dari SoundManager, ini backup)
        self.master_volume = 0.7
        self.sfx_volume = 0.6
        self.bgm_volume = 0.35
        self.voice_volume = 0.5

        # Gameplay
        # Screen shake DEFAULT OFF: efeknya menambah ~1.3-1.8 ms
        # per frame (render lewat Surface perantara + blit ulang
        # full-screen). Bisa dinyalakan lagi di menu Settings.
        self.screen_shake_enabled = False
        self.damage_numbers_enabled = True
        self.game_speed = 1.0  # 0.5, 1.0, 1.5, 2.0

        # Graphics
        self.fps_limit = 60  # 30, 60, 120 (0 = unlimited)

    def _load(self):
        """Load settings dari file"""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    data = json.load(f)

                # Load all fields with fallback to defaults
                self.master_volume = data.get(
                    'master_volume', 0.7)
                self.sfx_volume = data.get('sfx_volume', 0.6)
                self.bgm_volume = data.get('bgm_volume', 0.35)
                self.voice_volume = data.get('voice_volume', 0.5)

                self.screen_shake_enabled = data.get(
                    'screen_shake_enabled', False)
                self.damage_numbers_enabled = data.get(
                    'damage_numbers_enabled', True)
                self.game_speed = data.get('game_speed', 1.0)

                self.fps_limit = data.get('fps_limit', 60)

                print("[SETTINGS] Loaded")
        except Exception as e:
            print(f"[SETTINGS] Load failed: {e}")

    def save(self):
        """Save settings ke file"""
        try:
            os.makedirs("saves", exist_ok=True)

            data = {
                'master_volume': self.master_volume,
                'sfx_volume': self.sfx_volume,
                'bgm_volume': self.bgm_volume,
                'voice_volume': self.voice_volume,
                'screen_shake_enabled': self.screen_shake_enabled,
                'damage_numbers_enabled':
                    self.damage_numbers_enabled,
                'game_speed': self.game_speed,
                'fps_limit': self.fps_limit,
            }

            with open(SETTINGS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            print("[SETTINGS] Saved")
        except Exception as e:
            print(f"[SETTINGS] Save failed: {e}")

    # ═══════════════════════════════════════
    # SETTERS (dengan auto-save)
    # ═══════════════════════════════════════

    def set_screen_shake(self, enabled):
        self.screen_shake_enabled = enabled
        self.save()

    def set_damage_numbers(self, enabled):
        self.damage_numbers_enabled = enabled
        self.save()

    def set_game_speed(self, speed):
        self.game_speed = max(0.5, min(2.0, speed))
        self.save()

    def set_fps_limit(self, fps):
        # Valid: 30, 60, 120, 0 (unlimited)
        if fps in [30, 60, 120, 0]:
            self.fps_limit = fps
            self.save()

    # ═══════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════

    def get_fps_label(self):
        if self.fps_limit == 0:
            return "Unlimited"
        return f"{self.fps_limit} FPS"

    def get_speed_label(self):
        return f"{self.game_speed}x"


# ====================================================================
# controller_manager.py
# ====================================================================

# ================================
# CONTROLLER_MANAGER.PY
# Xbox, PlayStation, Generic Controller Support
# OPTIMIZED - Lazy init, no polling saat keyboard mode
# ================================

import pygame
import math


class InputMode:
    KEYBOARD = "keyboard"
    CONTROLLER = "controller"


# Button mappings
#   back        = tombol View/Select/Share  -> back / kembali ke menu
#   stick_left  = klik stick kiri (L3)      -> toggle FPS counter
#   stick_right = klik stick kanan (R3)     -> snap cursor ke tombol UI
XBOX_MAP = {
    'name': 'Xbox', 'confirm': 0, 'cancel': 1,
    'skill_q': 2, 'skill_w': 3, 'skill_e': 4, 'skill_r': 5,
    'start': 7, 'back': 6, 'shop': 9,
    'stick_left': 8, 'stick_right': 9,
    'left_stick_x': 0, 'left_stick_y': 1,
    'right_stick_x': 2, 'right_stick_y': 3,
    'left_trigger': 4, 'right_trigger': 5,
}

PS_MAP = {
    'name': 'PlayStation', 'confirm': 0, 'cancel': 1,
    'skill_q': 3, 'skill_w': 2, 'skill_e': 4, 'skill_r': 5,
    'start': 9, 'back': 8, 'shop': 11,
    'stick_left': 10, 'stick_right': 11,
    'left_stick_x': 0, 'left_stick_y': 1,
    'right_stick_x': 2, 'right_stick_y': 3,
    'left_trigger': 4, 'right_trigger': 5,
}

GENERIC_MAP = {
    'name': 'Generic', 'confirm': 0, 'cancel': 1,
    'skill_q': 2, 'skill_w': 3, 'skill_e': 4, 'skill_r': 5,
    'start': 7, 'back': 6, 'shop': 9,
    'stick_left': 8, 'stick_right': 9,
    'left_stick_x': 0, 'left_stick_y': 1,
    'right_stick_x': 2, 'right_stick_y': 3,
    'left_trigger': 4, 'right_trigger': 5,
}


class ControllerManager:
    """
    Controller support - LAZY INIT.
    Joystick hanya di-init saat user pilih controller mode.
    ZERO overhead saat keyboard mode.
    """

    def __init__(self):
        # TIDAK init joystick di sini (avoid lag)
        self.initialized = False
        self.active_mode = InputMode.KEYBOARD
        self.joystick = None
        self.controller_type = None
        self.button_map = None
        self.connected = False

        # Virtual cursor
        self.cursor_x = SCREEN_WIDTH // 2
        self.cursor_y = SCREEN_HEIGHT // 2
        self.cursor_speed = 12.0        # Base speed (naik dari 8)
        self.cursor_max_speed = 25.0    # Max speed saat stick full
        self.cursor_acceleration = 1.5  # Multiplier acceleration
        self.cursor_visible = False
        self.deadzone = 0.25

        # Button edge detection
        self._prev_buttons = {}
        self._prev_hat = (0, 0)
        self._left_trigger_pressed = False
        self._right_trigger_pressed = False
        self._rumble_timer = 0

        # D-pad auto-repeat (tahan arah = jalan terus)
        self._hat_hold_frames = 0
        self._hat_repeat_dir = (0, 0)
        self.hat_repeat_delay = 22    # frame sebelum mulai repeat
        self.hat_repeat_rate = 5      # frame antar repeat

        # Right stick = scroll (shop / list panjang)
        self._scroll_accum = 0.0
        self.scroll_step = 1.0        # threshold accum -> 1 tick scroll
        self.scroll_speed = 0.55      # makin besar = scroll makin cepat
        self.scroll_deadzone = 0.18   # lebih kecil dari deadzone cursor
        self._scroll_axis = None      # hasil auto-detect, di-cache
        self._axis_rest = {}          # nilai diam tiap axis (kalibrasi)

    # ═══════════════════════════════════════
    # LAZY INIT (hanya saat dibutuhkan)
    # ═══════════════════════════════════════

    def init_joystick(self):
        """Init joystick - HANYA dipanggil saat switch ke controller"""
        if self.initialized:
            return self.connected

        try:
            pygame.joystick.init()
            self.initialized = True
            self._scan_controllers()
        except Exception as e:
            print(f"[CONTROLLER] Init failed: {e}")
            self.connected = False

        return self.connected

    def _scan_controllers(self):
        """Scan controllers"""
        count = pygame.joystick.get_count()
        if count == 0:
            self.connected = False
            self.joystick = None
            return

        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        self.connected = True

        name = self.joystick.get_name().lower()
        guid = ''
        try:
            guid = self.joystick.get_guid().lower()
        except Exception:
            pass

        num_buttons = self.joystick.get_numbuttons()
        num_axes = self.joystick.get_numaxes()

        print(f"[CONTROLLER] Found: {self.joystick.get_name()}")
        print(f"[CONTROLLER] GUID: {guid}")
        print(f"[CONTROLLER] Buttons: {num_buttons}, Axes: {num_axes}")

        # ═══ DETECTION (broader matching) ═══

        # Xbox / XInput compatible (termasuk ROG Ally, Steam Deck, dll)
        xbox_keywords = [
            'xbox', 'xinput', 'x-box', 'microsoft',
            'x360', '360', 'xone', 'xb1',
            'rog', 'asus', 'ally',          # ROG Ally
            'steam', 'valve',                # Steam Deck
            'gamesir', 'razer', '8bitdo',    # Third party Xbox-style
            'logitech', 'thrustmaster',
        ]

        # PlayStation keywords
        ps_keywords = [
            'playstation', 'ps4', 'ps5', 'ps3',
            'dualshock', 'dualsense', 'sony',
            'wireless controller',  # PS4 via bluetooth
        ]

        # Check Xbox first (more common on PC/UMPC)
        is_xbox = any(kw in name for kw in xbox_keywords)

        # Check PlayStation
        is_ps = any(kw in name for kw in ps_keywords)

        # Check GUID for XInput (more reliable)
        is_xinput_guid = 'xinput' in guid or '78696e70' in guid

        if is_ps and not is_xbox:
            self.controller_type = 'ps'
            self.button_map = PS_MAP.copy()
            print(f"[CONTROLLER] Type: PlayStation")

        elif is_xbox or is_xinput_guid:
            self.controller_type = 'xbox'
            self.button_map = XBOX_MAP.copy()
            print(f"[CONTROLLER] Type: Xbox/XInput")

        else:
            # ═══ AUTO-DETECT by button/axis count ═══
            # Kebanyakan XInput punya 11+ buttons, 6+ axes
            # PS punya 13-17 buttons, 6 axes
            if num_buttons >= 11 and num_axes >= 4:
                # Kemungkinan besar XInput compatible
                self.controller_type = 'xbox'
                self.button_map = XBOX_MAP.copy()
                print(f"[CONTROLLER] Type: Xbox (auto-detected by layout)")
            else:
                self.controller_type = 'generic'
                self.button_map = GENERIC_MAP.copy()
                print(f"[CONTROLLER] Type: Generic")

        self._prev_buttons = {}
        for i in range(self.joystick.get_numbuttons()):
            self._prev_buttons[i] = False

    def debug_print(self):
        """Print semua info controller untuk debugging"""
        if not self.connected or not self.joystick:
            print("[CONTROLLER DEBUG] No controller connected")
            return

        print("=" * 50)
        print(f"[CONTROLLER DEBUG]")
        print(f"  Name: {self.joystick.get_name()}")
        try:
            print(f"  GUID: {self.joystick.get_guid()}")
        except Exception:
            print(f"  GUID: (not available)")
        print(f"  Buttons: {self.joystick.get_numbuttons()}")
        print(f"  Axes: {self.joystick.get_numaxes()}")
        print(f"  Hats: {self.joystick.get_numhats()}")
        print(f"  Detected as: {self.controller_type}")
        print(f"  Mode: {self.active_mode}")

        # Print semua button states
        print(f"\n  Button states:")
        for i in range(self.joystick.get_numbuttons()):
            state = self.joystick.get_button(i)
            if state:
                print(f"    Button {i}: PRESSED")

        # Print semua axis values
        print(f"\n  Axis values:")
        for i in range(self.joystick.get_numaxes()):
            val = self.joystick.get_axis(i)
            if abs(val) > 0.1:
                print(f"    Axis {i}: {val:.3f}")

        print("=" * 50)

    def rescan(self):
        """Rescan controllers"""
        if not self.initialized:
            self.init_joystick()
            return

        try:
            pygame.joystick.quit()
            pygame.joystick.init()
            self._scan_controllers()
        except Exception:
            self.connected = False

    # ═══════════════════════════════════════
    # MODE SWITCHING
    # ═══════════════════════════════════════

    def set_mode(self, mode):
        """Switch input mode"""
        if mode == InputMode.CONTROLLER:
            # Lazy init
            if not self.init_joystick():
                print("[CONTROLLER] No controller found!")
                return False

            self.active_mode = InputMode.CONTROLLER
            self.cursor_visible = True
            self.cursor_x = SCREEN_WIDTH // 2
            self.cursor_y = SCREEN_HEIGHT // 2
            print(f"[INPUT] Controller mode ({self.controller_type})")
            return True
        else:
            self.active_mode = InputMode.KEYBOARD
            self.cursor_visible = False
            print("[INPUT] Keyboard mode")
            return True

    def is_controller_mode(self):
        return self.active_mode == InputMode.CONTROLLER

    # ═══════════════════════════════════════
    # UPDATE (HANYA saat controller mode)
    # ═══════════════════════════════════════

    def update(self):
        """Update - SKIP kalau keyboard mode"""
        if self.active_mode != InputMode.CONTROLLER:
            return
        if not self.connected or not self.joystick:
            return

        # Rumble timer
        if self._rumble_timer > 0:
            self._rumble_timer -= 1
            if self._rumble_timer <= 0:
                try:
                    self.joystick.stop_rumble()
                except Exception:
                    pass

        # Update cursor dengan acceleration
        try:
            axis_x = self.joystick.get_axis(
                self.button_map['left_stick_x'])
            axis_y = self.joystick.get_axis(
                self.button_map['left_stick_y'])

            if abs(axis_x) < self.deadzone:
                axis_x = 0
            if abs(axis_y) < self.deadzone:
                axis_y = 0

            # Acceleration: semakin jauh stick, semakin cepat
            magnitude = math.sqrt(axis_x * axis_x + axis_y * axis_y)
            if magnitude > 0:
                # Normalize + apply acceleration curve
                speed = self.cursor_speed + \
                        (self.cursor_max_speed - self.cursor_speed) * \
                        (magnitude ** self.cursor_acceleration)

                self.cursor_x += axis_x * speed
                self.cursor_y += axis_y * speed

            self.cursor_x = max(0, min(SCREEN_WIDTH, self.cursor_x))
            self.cursor_y = max(0, min(SCREEN_HEIGHT, self.cursor_y))
        except Exception:
            pass

    # ═══════════════════════════════════════
    # GET PRESSED ACTIONS
    # ═══════════════════════════════════════

    def get_pressed_actions(self):
        """Get actions - SKIP kalau keyboard mode"""
        if self.active_mode != InputMode.CONTROLLER:
            return []
        if not self.connected or not self.joystick:
            return []

        actions = []

        # Buttons
        btn_actions = {
            'confirm': self.button_map['confirm'],
            'cancel': self.button_map['cancel'],
            'skill_q': self.button_map['skill_q'],
            'skill_w': self.button_map['skill_w'],
            'skill_e': self.button_map['skill_e'],
            'skill_r': self.button_map['skill_r'],
            'start': self.button_map['start'],
            'back': self.button_map.get('back'),
            'stick_left': self.button_map.get('stick_left'),
            'stick_right': self.button_map.get('stick_right'),
        }
        btn_actions = {k: v for k, v in btn_actions.items()
                       if v is not None}

        try:
            num_buttons = self.joystick.get_numbuttons()

            for action, btn_id in btn_actions.items():
                if btn_id >= num_buttons:
                    continue
                current = self.joystick.get_button(btn_id)
                prev = self._prev_buttons.get(btn_id, False)
                if current and not prev:
                    actions.append(action)
                self._prev_buttons[btn_id] = current

            # D-Pad (dengan auto-repeat kalau ditahan)
            if self.joystick.get_numhats() > 0:
                hat = self.joystick.get_hat(0)

                fresh = []
                if hat[1] == 1 and self._prev_hat[1] != 1:
                    fresh.append('dpad_up')
                if hat[1] == -1 and self._prev_hat[1] != -1:
                    fresh.append('dpad_down')
                if hat[0] == -1 and self._prev_hat[0] != -1:
                    fresh.append('dpad_left')
                if hat[0] == 1 and self._prev_hat[0] != 1:
                    fresh.append('dpad_right')
                actions.extend(fresh)

                # Auto-repeat: tahan arah -> ulang otomatis
                if hat == (0, 0):
                    self._hat_hold_frames = 0
                    self._hat_repeat_dir = (0, 0)
                else:
                    if hat != self._hat_repeat_dir:
                        self._hat_repeat_dir = hat
                        self._hat_hold_frames = 0
                    else:
                        self._hat_hold_frames += 1
                        past = self._hat_hold_frames - \
                            self.hat_repeat_delay
                        if past >= 0 and \
                                past % self.hat_repeat_rate == 0:
                            if hat[1] == 1:
                                actions.append('dpad_up')
                            elif hat[1] == -1:
                                actions.append('dpad_down')
                            if hat[0] == -1:
                                actions.append('dpad_left')
                            elif hat[0] == 1:
                                actions.append('dpad_right')

                self._prev_hat = hat

            # Triggers
            num_axes = self.joystick.get_numaxes()
            lt = self.button_map.get('left_trigger')
            rt = self.button_map.get('right_trigger')

            if lt is not None and lt < num_axes:
                lt_pressed = self.joystick.get_axis(lt) > 0.5
                if lt_pressed and not self._left_trigger_pressed:
                    actions.append('left_trigger')
                self._left_trigger_pressed = lt_pressed

            if rt is not None and rt < num_axes:
                rt_pressed = self.joystick.get_axis(rt) > 0.5
                if rt_pressed and not self._right_trigger_pressed:
                    actions.append('right_trigger')
                self._right_trigger_pressed = rt_pressed

            # Right stick vertikal = scroll (shop / list panjang)
            #
            # Index axis stick kanan beda-beda antar driver:
            #   Xbox/XInput  -> 3 (kadang 4)
            #   DInput/PS    -> 3, sebagian 2 atau 5
            # Kalau index dari button_map tidak masuk akal, cari
            # axis lain yang sedang digerakkan supaya scroll tetap
            # jalan di controller apa pun.
            rsy = self._resolve_scroll_axis(num_axes)
            if rsy is not None:
                axis = self.joystick.get_axis(rsy)
                if abs(axis) > self.scroll_deadzone:
                    self._scroll_accum += axis * self.scroll_speed
                    guard = 0
                    while self._scroll_accum >= self.scroll_step \
                            and guard < 8:
                        actions.append('scroll_down')
                        self._scroll_accum -= self.scroll_step
                        guard += 1
                    guard = 0
                    while self._scroll_accum <= -self.scroll_step \
                            and guard < 8:
                        actions.append('scroll_up')
                        self._scroll_accum += self.scroll_step
                        guard += 1
                else:
                    self._scroll_accum = 0.0

        except Exception:
            pass

        return actions

    def _resolve_scroll_axis(self, num_axes):
        """
        Tentukan axis mana yang dipakai untuk scroll (stick kanan Y).

        Urutan:
        1. Index dari button_map, kalau valid DAN sedang digerakkan.
        2. Kandidat umum (3, 2, 4, 5) yang sedang digerakkan.

        Axis yang mentok di |1.0| dilewati (itu ciri trigger idle).
        Hasil di-cache begitu ketemu.

        Catatan: kalau stick kanan controller-mu tetap tidak
        terdeteksi, D-PAD ATAS/BAWAH juga men-scroll saat shop
        terbuka, jadi navigasi tetap bisa jalan.
        """
        if self._scroll_axis is not None:
            return self._scroll_axis

        lx = self.button_map.get('left_stick_x')
        ly = self.button_map.get('left_stick_y')

        def _read(idx):
            if idx is None or idx < 0 or idx >= num_axes:
                return None
            if idx in (lx, ly):
                return None
            try:
                return self.joystick.get_axis(idx)
            except Exception:
                return None

        mapped = self.button_map.get('right_stick_y')

        # Kandidat: mapped dulu, lalu index umum
        candidates = [mapped] + [c for c in (3, 2, 4, 5)
                                 if c != mapped]

        for idx in candidates:
            val = _read(idx)
            if val is None:
                continue
            # Trigger idle mentok di -1.0 / 1.0 -> bukan stick
            if abs(val) > 0.95:
                continue
            if abs(val) > self.scroll_deadzone:
                self._scroll_axis = idx
                if idx != mapped:
                    print(f"[CONTROLLER] Scroll axis terdeteksi: "
                          f"axis {idx}")
                return idx

        # Belum ada yang digerakkan: pakai mapped kalau wajar,
        # supaya frame berikutnya langsung responsif.
        val = _read(mapped)
        if val is not None and abs(val) <= 0.95:
            return mapped

        return None

    def get_cursor_pos(self):
        return (int(self.cursor_x), int(self.cursor_y))

    # ═══════════════════════════════════════
    # RUMBLE
    # ═══════════════════════════════════════

    def rumble(self, intensity=0.5, duration_frames=15):
        if not self.connected or not self.joystick:
            return
        if self.active_mode != InputMode.CONTROLLER:
            return
        try:
            duration_ms = int(duration_frames * 16.67)
            self.joystick.rumble(intensity, intensity * 0.7,
                                 duration_ms)
            self._rumble_timer = duration_frames
        except Exception:
            pass

    # ═══════════════════════════════════════
    # CURSOR DRAW
    # ═══════════════════════════════════════

    def draw_cursor(self, surface, animation_time=0,
                    hover_rect=None):
        """
        Draw cursor. Kalau hover_rect diberikan (rect UI yang lagi di-hover),
        tambah highlight box di sekitarnya.
        """
        if not self.cursor_visible:
            return
        if self.active_mode != InputMode.CONTROLLER:
            return

        cx = int(self.cursor_x)
        cy = int(self.cursor_y)

        pulse = math.sin(animation_time * 0.1) * 0.3 + 0.7

        # ═══ HIGHLIGHT BOX (kalau hover UI element) ═══
        if hover_rect:
            # Glow around rect
            glow_rect = hover_rect.inflate(20, 20)
            glow_surf = pygame.Surface(
                (glow_rect.width, glow_rect.height),
                pygame.SRCALPHA)
            pygame.draw.rect(glow_surf,
                             (255, 255, 100, int(80 * pulse)),
                             (0, 0, glow_rect.width, glow_rect.height),
                             border_radius=12)
            surface.blit(glow_surf, glow_rect.topleft)

            # Bright border on the rect
            pygame.draw.rect(surface, (255, 255, 200),
                             hover_rect, 3, border_radius=8)

            # Corner brackets (JRPG style)
            bracket_len = 12
            bracket_color = (255, 255, 100)
            # Top-left
            pygame.draw.line(surface, bracket_color,
                             (hover_rect.left - 5, hover_rect.top - 5),
                             (hover_rect.left + bracket_len,
                              hover_rect.top - 5), 3)
            pygame.draw.line(surface, bracket_color,
                             (hover_rect.left - 5, hover_rect.top - 5),
                             (hover_rect.left - 5,
                              hover_rect.top + bracket_len), 3)
            # Top-right
            pygame.draw.line(surface, bracket_color,
                             (hover_rect.right + 5, hover_rect.top - 5),
                             (hover_rect.right - bracket_len,
                              hover_rect.top - 5), 3)
            pygame.draw.line(surface, bracket_color,
                             (hover_rect.right + 5, hover_rect.top - 5),
                             (hover_rect.right + 5,
                              hover_rect.top + bracket_len), 3)
            # Bottom-left
            pygame.draw.line(surface, bracket_color,
                             (hover_rect.left - 5,
                              hover_rect.bottom + 5),
                             (hover_rect.left + bracket_len,
                              hover_rect.bottom + 5), 3)
            pygame.draw.line(surface, bracket_color,
                             (hover_rect.left - 5,
                              hover_rect.bottom + 5),
                             (hover_rect.left - 5,
                              hover_rect.bottom - bracket_len), 3)
            # Bottom-right
            pygame.draw.line(surface, bracket_color,
                             (hover_rect.right + 5,
                              hover_rect.bottom + 5),
                             (hover_rect.right - bracket_len,
                              hover_rect.bottom + 5), 3)
            pygame.draw.line(surface, bracket_color,
                             (hover_rect.right + 5,
                              hover_rect.bottom + 5),
                             (hover_rect.right + 5,
                              hover_rect.bottom - bracket_len), 3)

        # ═══ CURSOR (crosshair) ═══
        # Glow
        glow_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf,
                           (255, 255, 100, int(60 * pulse)),
                           (15, 15), 12)
        surface.blit(glow_surf, (cx - 15, cy - 15))

        # Crosshair
        pygame.draw.line(surface, (255, 255, 200),
                         (cx - 8, cy), (cx - 3, cy), 2)
        pygame.draw.line(surface, (255, 255, 200),
                         (cx + 3, cy), (cx + 8, cy), 2)
        pygame.draw.line(surface, (255, 255, 200),
                         (cx, cy - 8), (cx, cy - 3), 2)
        pygame.draw.line(surface, (255, 255, 200),
                         (cx, cy + 3), (cx, cy + 8), 2)

        # Center
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 2)
        pygame.draw.circle(surface, (255, 200, 50), (cx, cy), 1)

    def find_ui_button_at_cursor(self, ui_buttons):
        """
        Cari button di ui_buttons yang cursor lagi hover.

        Args:
            ui_buttons: dict {button_id: pygame.Rect}

        Returns:
            pygame.Rect atau None
        """
        if not self.is_controller_mode():
            return None

        cx = int(self.cursor_x)
        cy = int(self.cursor_y)

        for btn_id, rect in ui_buttons.items():
            if rect.collidepoint(cx, cy):
                return rect

        return None

    def snap_to_nearest_button(self, ui_buttons):
        """
        Snap cursor ke button terdekat.
        Berguna saat UI berubah (misal masuk screen baru).
        """
        if not self.is_controller_mode() or not ui_buttons:
            return

        cx = int(self.cursor_x)
        cy = int(self.cursor_y)

        nearest_rect = None
        nearest_dist = float('inf')

        for btn_id, rect in ui_buttons.items():
            rect_cx = rect.centerx
            rect_cy = rect.centery
            dist = math.hypot(rect_cx - cx, rect_cy - cy)

            if dist < nearest_dist:
                nearest_dist = dist
                nearest_rect = rect

        if nearest_rect:
            self.cursor_x = nearest_rect.centerx
            self.cursor_y = nearest_rect.centery

    # ═══════════════════════════════════════
    # INFO
    # ═══════════════════════════════════════

    def get_controller_info(self):
        if not self.connected:
            return {'connected': False, 'name': 'None',
                    'type': 'none'}
        return {
            'connected': True,
            'name': self.joystick.get_name(),
            'type': self.controller_type,
        }

    # ══════════════════════════════════════
    # BUTTON LABELS & HINTS
    # ══════════════════════════════════════

    _LABELS = {
        'xbox': {
            'confirm': 'A', 'cancel': 'B',
            'skill_q': 'X', 'skill_w': 'Y',
            'skill_e': 'LB', 'skill_r': 'RB',
            'start': 'MENU', 'back': 'VIEW',
            'left_trigger': 'LT', 'right_trigger': 'RT',
            'stick_left': 'L3', 'stick_right': 'R3',
            'dpad': 'D-PAD', 'left_stick': 'L-STICK',
            'right_stick': 'R-STICK',
        },
        'ps': {
            'confirm': 'X', 'cancel': 'O',
            'skill_q': 'SQUARE', 'skill_w': 'TRIANGLE',
            'skill_e': 'L1', 'skill_r': 'R1',
            'start': 'OPTIONS', 'back': 'SHARE',
            'left_trigger': 'L2', 'right_trigger': 'R2',
            'stick_left': 'L3', 'stick_right': 'R3',
            'dpad': 'D-PAD', 'left_stick': 'L-STICK',
            'right_stick': 'R-STICK',
        },
        'generic': {
            'confirm': 'BTN1', 'cancel': 'BTN2',
            'skill_q': 'BTN3', 'skill_w': 'BTN4',
            'skill_e': 'L1', 'skill_r': 'R1',
            'start': 'START', 'back': 'SELECT',
            'left_trigger': 'L2', 'right_trigger': 'R2',
            'stick_left': 'L3', 'stick_right': 'R3',
            'dpad': 'D-PAD', 'left_stick': 'L-STICK',
            'right_stick': 'R-STICK',
        },
    }

    # Label keyboard/mouse untuk aksi yang sama.
    _KEY_LABELS = {
        'confirm': 'CLICK', 'cancel': 'ESC',
        'skill_q': 'Q', 'skill_w': 'W',
        'skill_e': 'E', 'skill_r': 'R',
        'start': 'ESC', 'back': 'ESC',
        'left_trigger': 'H', 'right_trigger': 'R-CLICK',
        'stick_left': 'F8', 'stick_right': 'TAB',
        'dpad': 'ARROWS', 'left_stick': 'MOUSE',
        'right_stick': 'WHEEL',
        'replay': 'R', 'next_level': 'N',
        'skip': 'SPACE', 'shop': 'H',
    }

    # Aksi gameplay -> tombol yang dipakai.
    # Dipakai untuk generate hint bar otomatis.
    ACTION_BINDINGS = {
        'skip':        'confirm',
        'shop':        'left_trigger',
        'move_hero':   'right_trigger',
        'select':      'confirm',
        'back':        'cancel',
        'pause':       'start',
        'to_menu':     'back',
        'replay':      'skill_q',
        'next_level':  'skill_r',
        'fps':         'stick_left',
        'snap':        'stick_right',
        'scroll':      'right_stick',
        'cursor':      'left_stick',
    }

    def get_button_label(self, action):
        """
        Label tombol untuk sebuah action.

        Otomatis menyesuaikan: kalau controller mode aktif -> label
        controller (A / X / LB ...), kalau keyboard -> label keyboard
        (CLICK / Q / H ...). Jadi UI cukup panggil ini, tidak perlu
        cek mode sendiri.
        """
        if not self.is_controller_mode():
            return self._KEY_LABELS.get(action, '?')

        ctype = self.controller_type or 'generic'
        table = self._LABELS.get(ctype, self._LABELS['generic'])
        return table.get(action, self._KEY_LABELS.get(action, '?'))

    def get_action_label(self, gameplay_action):
        """
        Label untuk aksi gameplay (bukan nama tombol).

        Contoh: get_action_label('shop') -> 'LT' di Xbox,
                                            'H'  di keyboard.
        """
        if not self.is_controller_mode():
            return self._KEY_LABELS.get(
                gameplay_action,
                self._KEY_LABELS.get(
                    self.ACTION_BINDINGS.get(gameplay_action, ''), '?'))

        btn = self.ACTION_BINDINGS.get(gameplay_action)
        if btn is None:
            return '?'
        return self.get_button_label(btn)

    def get_hints(self, context='game'):
        """
        List of (label, description) for hint bar.
        All English, clean layout.
        """
        A = self.get_action_label

        if context == 'cinematic':
            return [(A('skip'), 'Skip')]

        if context == 'menu':
            return [
                (A('select'), 'Select'),
                (A('back'), 'Back'),
                (self.get_button_label('dpad'), 'Navigate'),
            ]

        if context == 'pause':
            return [
                (A('select'), 'Select'),
                (A('pause'), 'Resume'),
            ]

        if context == 'shop':
            if self.is_controller_mode():
                return [
                    (A('select'), 'Buy'),
                    (A('back'), 'Close'),
                    (self.get_button_label('right_stick') + '/' +
                     self.get_button_label('dpad'), 'Scroll'),
                    (A('snap'), 'Snap'),
                ]
            return [
                (A('select'), 'Buy'),
                (A('back'), 'Close'),
                (A('scroll'), 'Scroll'),
                (A('snap'), 'Snap'),
            ]

        if context == 'victory':
            return [
                (A('next_level'), 'Next Level'),
                (A('replay'), 'Replay'),
                (A('to_menu'), 'Menu'),
            ]

        if context == 'defeat':
            return [
                (A('replay'), 'Replay'),
                (A('to_menu'), 'Menu'),
            ]

        # default: gameplay - English
        return [
            (self.get_button_label('skill_q'), 'Q'),
            (self.get_button_label('skill_w'), 'W'),
            (self.get_button_label('skill_e'), 'E'),
            (self.get_button_label('skill_r'), 'R'),
            (A('shop'), 'Shop'),
            (A('move_hero'), 'Move Hero'),
            (A('pause'), 'Pause'),
        ]

    def draw_hint_bar(self, surface, context='game', y=None,
                      font=None, align='center'):
        """
        Gambar hint bar tombol di layar.

        Dipanggil dari UI mana pun; otomatis menampilkan label
        keyboard atau controller sesuai mode aktif.
        """
        hints = self.get_hints(context)
        if not hints:
            return

        if font is None:
            try:
                font = get_font(19)
            except Exception:
                return

        if y is None:
            y = SCREEN_HEIGHT - 30

        pad_x, gap, key_pad = 7, 16, 5
        items = []
        total_w = 0
        for label, desc in hints:
            ls = font.render(label, True, (255, 235, 140))
            ds = font.render(desc, True, (205, 210, 225))
            w = ls.get_width() + key_pad * 2 + 5 + ds.get_width()
            items.append((ls, ds, w))
            total_w += w + gap
        total_w = max(0, total_w - gap)

        if align == 'center':
            x = (SCREEN_WIDTH - total_w) // 2
        elif align == 'right':
            x = SCREEN_WIDTH - total_w - 20
        else:
            x = 20

        h = font.get_height() + 8
        bg = pygame.Surface((total_w + pad_x * 2, h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        surface.blit(bg, (x - pad_x, y - 4))

        for ls, ds, w in items:
            kw = ls.get_width() + key_pad * 2
            kh = font.get_height() + 2
            pygame.draw.rect(surface, (48, 52, 70),
                             (x, y - 1, kw, kh), border_radius=4)
            pygame.draw.rect(surface, (120, 130, 165),
                             (x, y - 1, kw, kh), 1, border_radius=4)
            surface.blit(ls, (x + key_pad, y))
            surface.blit(ds, (x + kw + 5, y))
            x += w + gap


# ═══════════════════════════════════════════════════════
# ALIAS MODUL LAMA
# Semua nama file lama didaftarkan ke sys.modules supaya
# baris import di file lain (`from game import Game`,
# `from performance import FrustumCuller`, dll.) tetap jalan
# tanpa perubahan. Dipasang otomatis saat _core di-import.
# ═══════════════════════════════════════════════════════
import sys as _sys
import types as _types

_CORE_MOD = _sys.modules[__name__]


def _install_root_aliases():
    import _system as _s
    import _render as _r
    import _entity as _e

    # "settings" sudah dipasang lebih awal (dini) supaya paket lain
    # (map_components, ui_components, bosses, ...) yang mengimpor
    # settings di level modul tetap jalan saat bundle sedang dimuat.
    _map = {
        # inti
        "game": _CORE_MOD,
        "menu": _CORE_MOD,
        "game_input": _CORE_MOD,
        "game_ui": _CORE_MOD,
        "game_dev": _CORE_MOD,
        "game_settings": _CORE_MOD,
        "controller_manager": _CORE_MOD,
        # entity
        "hero": _e,
        "minion": _e,
        "tower": _e,
        "castle": _e,
        "ai_player": _e,
        # render & efek
        "map_renderer": _r,
        "effects": _r,
        "effects_death": _r,
        "effects_intro": _r,
        "effects_level_intro": _r,
        "sprite_cache": _r,
        "render_cache": _r,
        # performa & sistem
        "performance": _s,
        "fps_counter": _s,
        "fps_limiter": _s,
        "sound_manager": _s,
        "save_manager": _s,
    }
    for _k, _v in _map.items():
        _sys.modules.setdefault(_k, _v)


_install_root_aliases()


def install_aliases():
    # Idempoten - aman dipanggil ulang (untuk kompatibilitas).
    _install_root_aliases()
