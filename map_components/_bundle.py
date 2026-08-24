"""
map_components/_bundle.py - semua komponen peta

Gabungan dari 7 file:
  - palettes.py              level modul
  - themes.py                level modul
  - generators.py            namespace _NS_generators
  - static_renderer.py       namespace _NS_static_renderer
  - dynamic_renderer.py      level modul
  - decoration_renderer.py   level modul
  - shop_renderer.py         namespace _NS_shop_renderer

Modul yang dibungkus kelas `_NS_<nama>` supaya simbol
bernama sama TIDAK saling menimpa. Ini sudah diukur:
LEVEL_CONFIGS di 4 file tower isinya berbeda semua,
begitu juga PALETTE dan HAS_AACIRCLE di minions.

Modul di level modul (tidak dibungkus) karena kodenya
merujuk simbolnya sendiri saat modul dimuat, sehingga
nama kelas namespace belum terikat:
  palettes, themes, dynamic_renderer, decoration_renderer

File asli tetap ada sebagai jembatan kecil, jadi semua
baris `from map_components.<modul> import ...` yang sudah ada
TETAP JALAN tanpa perubahan apa pun.
"""
import math
import random
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
import pygame


# ====================================================================
# palettes.py  (modul bersama)
# ====================================================================
# map_components/palettes.py
# Dark Fantasy color palettes & constants
# ================================

# ═══════════════════════════════════════════════════════
# DARK FANTASY PALETTES
# ═══════════════════════════════════════════════════════

# RADIANT (Blue) - Enchanted Dark Forest
RADIANT_GRASS_1 = (28, 55, 32)
RADIANT_GRASS_2 = (38, 72, 42)
RADIANT_GRASS_3 = (52, 92, 55)
RADIANT_GRASS_4 = (68, 115, 70)
RADIANT_GRASS_HIGH = (90, 145, 85)
RADIANT_MOSS = (55, 90, 40)

# DIRE (Red) - Cursed Wasteland
DIRE_EARTH_1 = (45, 32, 28)
DIRE_EARTH_2 = (65, 45, 38)
DIRE_EARTH_3 = (85, 60, 48)
DIRE_EARTH_4 = (105, 78, 62)
DIRE_ASH = (60, 55, 50)
DIRE_BURNT = (30, 20, 18)

# TRANSITION (middle)
TRANSITION_1 = (55, 55, 42)
TRANSITION_2 = (75, 68, 50)

# PATH - Ancient Cobblestone
PATH_STONE_1 = (58, 52, 45)
PATH_STONE_2 = (85, 76, 65)
PATH_STONE_3 = (115, 105, 90)
PATH_STONE_4 = (145, 130, 108)
PATH_MOSS = (65, 90, 45)
PATH_CRACK = (30, 25, 20)

# STONE (decoration)
STONE_DARK = (55, 55, 65)
STONE_MID = (95, 95, 105)
STONE_LIGHT = (135, 135, 145)
STONE_HIGH = (175, 175, 185)

# DARK RIVER
RIVER_DEEP = (15, 28, 45)
RIVER_MID = (30, 55, 88)
RIVER_LIGHT = (50, 90, 130)
RIVER_GLOW = (80, 150, 200)
RIVER_FOAM = (180, 210, 230)

# TREES (dark forest)
TREE_TRUNK_D = (32, 20, 15)
TREE_TRUNK_L = (58, 38, 25)
TREE_LEAVES_D = (18, 42, 22)
TREE_LEAVES_M = (32, 65, 35)
TREE_LEAVES_L = (55, 95, 55)
TREE_LEAVES_H = (80, 130, 70)

# DEAD TREES
DEAD_TREE_1 = (28, 20, 18)
DEAD_TREE_2 = (55, 42, 35)
DEAD_TREE_3 = (85, 68, 55)

# CRYSTALS (magical)
CRYSTAL_BLUE_D = (25, 55, 100)
CRYSTAL_BLUE_M = (55, 100, 170)
CRYSTAL_BLUE_L = (100, 170, 240)
CRYSTAL_BLUE_H = (200, 230, 255)

CRYSTAL_RED_D = (100, 20, 30)
CRYSTAL_RED_M = (170, 40, 55)
CRYSTAL_RED_L = (230, 80, 100)
CRYSTAL_RED_H = (255, 180, 200)

# FIRE
FIRE_D = (140, 40, 15)
FIRE_M = (220, 90, 25)
FIRE_L = (255, 180, 60)
FIRE_H = (255, 240, 150)

# UTILITY
OUTLINE = (12, 8, 12)
SHADOW = (0, 0, 0)

TILE_SIZE = 16




# ================================


# ====================================================================
# themes.py  (tidak bisa dibungkus: merujuk 'FOREST_THEME' saat modul dimuat)
# ====================================================================
# map_components/themes.py
# Map theme definitions per level
#
# CARA TAMBAH THEME BARU:
# 1. Copy salah satu theme dict di bawah
# 2. Ubah warna palette + decoration config
# 3. Register di THEMES dict paling bawah
# ================================


# ═══════════════════════════════════════════════════════
# FOREST THEME (Level 1 - existing dark forest)
# ═══════════════════════════════════════════════════════

FOREST_THEME = {
    "name": "Forest",
    "boss_identity": "abaddon",
    "boss_title": "Lord of Avernus",

    # ─── TERRAIN COLORS ───
    "radiant_grass_1": (28, 55, 32),
    "radiant_grass_2": (38, 72, 42),
    "radiant_grass_3": (52, 92, 55),
    "radiant_grass_4": (68, 115, 70),
    "radiant_grass_high": (90, 145, 85),
    "radiant_moss": (55, 90, 40),

    "dire_earth_1": (45, 32, 28),
    "dire_earth_2": (65, 45, 38),
    "dire_earth_3": (85, 60, 48),
    "dire_earth_4": (105, 78, 62),
    "dire_ash": (60, 55, 50),
    "dire_burnt": (30, 20, 18),

    "transition_1": (55, 55, 42),
    "transition_2": (75, 68, 50),

    # ─── PATH ───
    "path_stone_1": (58, 52, 45),
    "path_stone_2": (85, 76, 65),
    "path_stone_3": (115, 105, 90),
    "path_stone_4": (145, 130, 108),
    "path_moss": (65, 90, 45),
    "path_crack": (170, 36, 61),

    # ─── RIVER ───
    "river_deep": (8, 8, 18),
    "river_mid": (35, 12, 34),
    "river_light": (91, 22, 48),
    "river_glow": (177, 46, 75),
    "river_foam": (255, 130, 140),

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,
    "has_dead_trees": True,
    "has_gravestones": True,
    "has_crystals_blue": True,
    "has_crystals_red": True,
    "has_ancient_ruins": True,
    "has_bones": True,
    "has_mushrooms_dark": True,
    "has_rocks_mossy": True,
    "has_dark_bushes": True,
    "has_glow_flowers": True,
    "has_spike_traps": True,
    "has_torch_stones": True,

    # Custom decorations (empty for forest = default)
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    "particle_type": "ash",  # ash/dead knight motes
    "particle_colors_radiant": [
        (150, 52, 66), (210, 74, 86), (120, 110, 120)
    ],
    "particle_colors_dire": [
        (82, 28, 54), (190, 42, 72), (226, 96, 110)
    ],
    "particle_count": 30,

    "fog_enabled": True,
    "fog_color": (80, 60, 60, 40),
    "fog_count": 15,

    # ─── SKY / AMBIENT ───
    "ambient_tint": None,  # None = no tint overlay
}


# ═══════════════════════════════════════════════════════
# DESERT THEME (Level 2 - warm sandy)
# ═══════════════════════════════════════════════════════

DESERT_THEME = {
    "name": "Desert",
    "boss_identity": "alchemist",
    "boss_title": "The Chemical Conqueror",

    # ─── TERRAIN (sand yellow) ───
    "radiant_grass_1": (155, 115, 60),     # dark sand
    "radiant_grass_2": (180, 135, 75),
    "radiant_grass_3": (210, 165, 95),     # main sand
    "radiant_grass_4": (230, 190, 120),
    "radiant_grass_high": (245, 215, 150),  # bright sand
    "radiant_moss": (140, 110, 55),         # dry patch

    "dire_earth_1": (95, 55, 30),           # scorched earth
    "dire_earth_2": (125, 75, 40),
    "dire_earth_3": (150, 95, 55),
    "dire_earth_4": (175, 120, 75),
    "dire_ash": (100, 75, 50),
    "dire_burnt": (60, 35, 20),

    "transition_1": (135, 100, 60),
    "transition_2": (165, 125, 80),

    # ─── PATH (weathered stone) ───
    "path_stone_1": (110, 85, 55),
    "path_stone_2": (145, 115, 75),
    "path_stone_3": (180, 145, 100),
    "path_stone_4": (215, 180, 130),
    "path_moss": (100, 85, 45),
    "path_crack": (60, 40, 20),

    # ─── RIVER (dry riverbed / oasis) ───
    "river_deep": (8, 29, 18),
    "river_mid": (25, 79, 34),
    "river_light": (62, 139, 42),
    "river_glow": (150, 220, 68),
    "river_foam": (220, 255, 160),

    # ─── DECORATION FLAGS ───
    "has_dark_trees": False,         # no dark trees
    "has_dead_trees": True,          # dry dead trees
    "has_gravestones": False,        # no tombstones
    "has_crystals_blue": False,      # no blue crystals
    "has_crystals_red": True,        # amber crystals (recolor)
    "has_ancient_ruins": True,       # desert ruins
    "has_bones": True,               # animal bones
    "has_mushrooms_dark": True,     # no mushrooms
    "has_rocks_mossy": True,         # sandstone rocks
    "has_dark_bushes": False,        # no dark bushes
    "has_glow_flowers": False,       # no glow flowers
    "has_spike_traps": True,
    "has_torch_stones": True,

    # Custom desert decorations
    "has_cactus": True,
    "has_palm_trees": True,
    "has_sand_dunes": True,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    "particle_type": "acid",
    "particle_colors_radiant": [
        (240, 220, 120), (170, 235, 80), (220, 255, 160)
    ],
    "particle_colors_dire": [
        (120, 200, 60), (180, 150, 40), (90, 150, 50)
    ],
    "particle_count": 40,  # more particles for sandstorm

    "fog_enabled": True,
    "fog_color": (200, 170, 110, 30),  # sandy fog
    "fog_count": 20,

    "ambient_tint": (255, 220, 150, 15),  # warm yellow tint
}


# ═══════════════════════════════════════════════════════
# ICE THEME (Level 3 - frozen tundra)
# ═══════════════════════════════════════════════════════

ICE_THEME = {
    "name": "Ice",
    "boss_identity": "ancient_apparition",
    "boss_title": "The Frozen Eternity",

    # ─── TERRAIN (snow + ice) ───
    "radiant_grass_1": (180, 200, 220),    # dark snow
    "radiant_grass_2": (200, 220, 235),
    "radiant_grass_3": (220, 235, 245),    # main snow
    "radiant_grass_4": (235, 245, 250),
    "radiant_grass_high": (250, 253, 255),  # bright snow
    "radiant_moss": (150, 180, 210),        # ice patch

    "dire_earth_1": (60, 80, 105),          # dark frozen ground
    "dire_earth_2": (85, 105, 130),
    "dire_earth_3": (110, 135, 160),
    "dire_earth_4": (140, 165, 185),
    "dire_ash": (95, 115, 140),
    "dire_burnt": (40, 55, 75),

    "transition_1": (120, 145, 170),
    "transition_2": (155, 180, 200),

    # ─── PATH (icy stone) ───
    "path_stone_1": (90, 110, 135),
    "path_stone_2": (125, 145, 170),
    "path_stone_3": (160, 180, 205),
    "path_stone_4": (195, 215, 235),
    "path_moss": (80, 130, 170),
    "path_crack": (40, 55, 75),

    # ─── RIVER (frozen river with ice glow) ───
    "river_deep": (20, 50, 90),
    "river_mid": (50, 100, 150),
    "river_light": (100, 160, 210),
    "river_glow": (170, 220, 255),
    "river_foam": (230, 245, 255),

    # ─── DECORATION FLAGS ───
    "has_dark_trees": False,         # no dark trees
    "has_dead_trees": False,         # replaced with frozen
    "has_gravestones": False,
    "has_crystals_blue": True,       # blue ice crystals
    "has_crystals_red": False,       # no red crystals
    "has_ancient_ruins": True,       # frozen ruins
    "has_bones": True,               # frozen bones
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,         # ice-covered rocks
    "has_dark_bushes": False,
    "has_glow_flowers": True,        # ice glow flowers
    "has_spike_traps": False,        # no spikes
    "has_torch_stones": True,        # blue flame torches

    # Custom ice decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": True,        # extra big ice crystals
    "has_frozen_trees": True,        # replaces dead trees
    "has_snow_drifts": True,

    # ─── ENVIRONMENTAL EFFECTS ───
    "particle_type": "snow",
    "particle_colors_radiant": [
        (255, 255, 255), (220, 240, 255), (180, 220, 255)
    ],
    "particle_colors_dire": [
        (160, 200, 240), (130, 170, 220), (100, 140, 200)
    ],
    "particle_count": 60,  # heavy snowfall

    "fog_enabled": True,
    "fog_color": (200, 220, 240, 40),  # cold fog
    "fog_count": 25,

    "ambient_tint": (150, 200, 255, 20),  # cool blue tint
}

# ═══════════════════════════════════════════════════════
# VOLCANIC THEME (Level 4 - lava/molten)
# ═══════════════════════════════════════════════════════

VOLCANIC_THEME = {
    "name": "Volcanic",
    "boss_identity": "ignis_drachorn",
    "boss_title": "The Molten Sovereign",

    # ─── TERRAIN (charred earth + magma) ───
    "radiant_grass_1": (75, 35, 20),      # dark burnt
    "radiant_grass_2": (100, 50, 28),
    "radiant_grass_3": (130, 65, 35),     # main burnt earth
    "radiant_grass_4": (160, 85, 45),
    "radiant_grass_high": (190, 110, 55),  # highlight
    "radiant_moss": (95, 45, 22),          # scorched patch

    "dire_earth_1": (45, 18, 12),          # deep obsidian
    "dire_earth_2": (65, 28, 18),
    "dire_earth_3": (90, 40, 25),
    "dire_earth_4": (115, 55, 32),
    "dire_ash": (70, 45, 35),
    "dire_burnt": (30, 12, 8),

    "transition_1": (85, 42, 25),
    "transition_2": (110, 58, 35),

    # ─── PATH (basalt stone) ───
    "path_stone_1": (55, 32, 22),
    "path_stone_2": (85, 55, 40),
    "path_stone_3": (115, 78, 55),
    "path_stone_4": (145, 100, 70),
    "path_moss": (95, 45, 22),
    "path_crack": (255, 100, 20),  # glowing lava crack!

    # ─── RIVER (LAVA!) ───
    "river_deep": (80, 15, 8),
    "river_mid": (180, 55, 12),
    "river_light": (240, 120, 30),
    "river_glow": (255, 180, 60),
    "river_foam": (255, 230, 130),

    # ─── DECORATION FLAGS ───
    "has_dark_trees": False,
    "has_dead_trees": True,          # scorched dead trees
    "has_gravestones": False,
    "has_crystals_blue": False,
    "has_crystals_red": True,        # obsidian/ruby crystals
    "has_ancient_ruins": True,       # volcanic ruins
    "has_bones": True,               # charred bones
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,         # obsidian rocks
    "has_dark_bushes": False,
    "has_glow_flowers": True,        # lava flowers
    "has_spike_traps": True,         # lava spikes
    "has_torch_stones": True,        # fire torches

    # Custom desert (not used)
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    "particle_type": "ember",  # rising embers
    "particle_colors_radiant": [
        (255, 180, 50), (255, 130, 30), (255, 220, 100)
    ],
    "particle_colors_dire": [
        (200, 60, 20), (255, 100, 30), (180, 40, 15)
    ],
    "particle_count": 50,      # heavy ember rain

    "fog_enabled": True,
    "fog_color": (120, 40, 20, 45),  # smoky red
    "fog_count": 22,

    "ambient_tint": (255, 100, 40, 20),  # warm orange tint
}


# ═══════════════════════════════════════════════════════
# HAUNTED VEIL THEME (Level 5 - inline theme only)
HAUNTED_THEME = {
    "name": "Haunted Veil",
    "level_identity": "krobellus_death_prophet_necropolis",

    # Domain bawah: bekas Radiant yang sudah dikuasai soul energy.
    "radiant_grass_1": (8, 25, 27),
    "radiant_grass_2": (12, 47, 44),
    "radiant_grass_3": (19, 76, 61),
    "radiant_grass_4": (31, 112, 82),
    "radiant_grass_high": (65, 174, 119),
    "radiant_moss": (25, 105, 80),

    # Domain atas: tanah makam Dire yang terbelah oleh The Veil.
    "dire_earth_1": (10, 7, 19),
    "dire_earth_2": (27, 12, 37),
    "dire_earth_3": (51, 18, 60),
    "dire_earth_4": (82, 31, 85),
    "dire_ash": (54, 38, 65),
    "dire_burnt": (8, 5, 15),

    "transition_1": (25, 25, 35),
    "transition_2": (47, 39, 56),

    # Bone causeway.
    "path_stone_1": (25, 25, 34),
    "path_stone_2": (53, 53, 64),
    "path_stone_3": (88, 86, 94),
    "path_stone_4": (151, 151, 151),
    "path_moss": (35, 117, 91),
    "path_crack": (55, 226, 178),

    # Soulstream.
    "river_deep": (3, 14, 22),
    "river_mid": (7, 54, 61),
    "river_light": (17, 119, 108),
    "river_glow": (48, 205, 177),
    "river_foam": (190, 255, 222),

    # Signature palette Death Prophet.
    "void_black": (7, 6, 16),
    "rift_violet": (151, 57, 190),
    "soul_teal": (48, 205, 177),
    "bone_white": (151, 160, 157),
    "bone_highlight": (221, 238, 218),
    "causeway_dark": (29, 29, 39),
    "causeway_mid": (66, 66, 78),
    "arena_stone": (38, 35, 54),
    "arena_highlight": (101, 74, 121),
    "obelisk_stone": (42, 37, 56),
    "obelisk_highlight": (112, 79, 129),
    "gate_stone": (38, 34, 49),
    "gate_highlight": (106, 83, 119),
    "border_stone": (24, 20, 34),
    "border_highlight": (81, 58, 93),
    "ash_high": (68, 50, 75),

    # Fallback decorations renderer lama tetap kompatibel.
    "has_dark_trees": False,
    "has_dead_trees": True,
    "has_gravestones": True,
    "has_crystals_blue": True,
    "has_crystals_red": False,
    "has_ancient_ruins": True,
    "has_bones": True,
    "has_mushrooms_dark": True,
    "has_rocks_mossy": True,
    "has_dark_bushes": True,
    "has_glow_flowers": True,
    "has_spike_traps": False,
    "has_torch_stones": True,
    "has_ghost_lights": True,
    "has_ectoplasm_pools": True,
    "has_crypt_gates": True,
    "has_spirit_wisps": True,
    "has_cursed_candles": True,

    # Dynamic renderer generik masih aman jika custom renderer belum dipasang.
    "particle_type": "spirit",
    "particle_colors_radiant": [
        (48, 205, 177), (110, 255, 205), (190, 255, 230)
    ],
    "particle_colors_dire": [
        (120, 50, 160), (205, 80, 210), (80, 230, 180)
    ],
    "particle_count": 34,
    "fog_enabled": True,
    "fog_color": (35, 100, 95, 32),
    "fog_count": 12,
    "ambient_tint": (24, 42, 44, 12),
}


# ═══════════════════════════════════════════════════════
# ADMIRAL'S COVE THEME (Level 6 - naval/ocean)
# Theme untuk Kunkka - The Admiral of the Fleet
# Palette: deep naval blue, gold trim, turquoise water, stormy ocean
# ═══════════════════════════════════════════════════════

OCEAN_THEME = {
    "name": "Admiral's Cove",
    "boss_identity": "kunkka",
    "boss_title": "The Admiral of the Fleet",

    # ─── TERRAIN (sandy shore → shallow turquoise → deep ocean) ───
    "radiant_grass_1": (45, 75, 80),       # wet sand / shore edge
    "radiant_grass_2": (75, 110, 105),     # damp sand
    "radiant_grass_3": (100, 145, 135),    # beach grass zone
    "radiant_grass_4": (140, 175, 160),    # dry sand highlight
    "radiant_grass_high": (185, 210, 190),  # bright sand
    "radiant_moss": (60, 105, 100),         # tide pool green

    # Dire side: stormy deep ocean
    "dire_earth_1": (5, 18, 42),            # abyssal deep
    "dire_earth_2": (12, 35, 70),           # deep ocean blue
    "dire_earth_3": (25, 55, 100),          # mid ocean
    "dire_earth_4": (45, 85, 130),          # shallower storm water
    "dire_ash": (30, 50, 75),               # stormy foam gray-blue
    "dire_burnt": (3, 10, 25),              # darkest trench

    "transition_1": (55, 90, 100),          # sand-to-water transition
    "transition_2": (40, 80, 110),          # shallow-to-deep transition

    # ─── PATH (weathered dock planks / sea-worn stone) ───
    "path_stone_1": (45, 35, 25),           # dark weathered wood
    "path_stone_2": (75, 58, 38),           # worn dock plank
    "path_stone_3": (110, 85, 55),          # aged wood
    "path_stone_4": (150, 120, 80),         # sun-bleached plank
    "path_moss": (50, 100, 90),             # seaweed / wet moss
    "path_crack": (40, 130, 200),           # glowing water in cracks

    # ─── RIVER (ocean channel with waves) ───
    "river_deep": (3, 15, 40),              # deep ocean trench
    "river_mid": (15, 55, 105),             # ocean blue
    "river_light": (40, 130, 200),          # turquoise water
    "river_glow": (110, 200, 245),          # bright water surface
    "river_foam": (245, 255, 255),          # white foam / sea spray

    # ─── DECORATION FLAGS ───
    "has_dark_trees": False,         # no forest trees
    "has_dead_trees": True,          # driftwood / dead shore trees
    "has_gravestones": False,
    "has_crystals_blue": True,       # sea glass / blue crystals
    "has_crystals_red": False,
    "has_ancient_ruins": True,       # shipwreck remnants / naval ruins
    "has_bones": True,               # fish bones / skeletal remains
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,         # sea rocks / coral formations
    "has_dark_bushes": False,
    "has_glow_flowers": True,        # bioluminescent tide-pool flowers
    "has_spike_traps": False,
    "has_torch_stones": True,        # lighthouse beacons / naval lanterns

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": True,          # tropical palms near shore
    "has_sand_dunes": True,          # beach sand dunes
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    "particle_type": "mist",         # sea mist / ocean spray
    "particle_colors_radiant": [
        (110, 200, 245), (180, 230, 250), (90, 170, 210)
    ],
    "particle_colors_dire": [
        (40, 130, 200), (15, 55, 105), (200, 240, 255)
    ],
    "particle_count": 45,            # misty ocean atmosphere

    "fog_enabled": True,
    "fog_color": (100, 160, 200, 35),  # sea fog / ocean haze
    "fog_count": 18,

    "ambient_tint": (30, 70, 120, 15),  # cool ocean blue tint
}


# ═══════════════════════════════════════════════════════
# SHADOW ABYSS THEME (Level 7 - dark hellfire/shadow realm)
# Theme untuk Nyxarath - The Soul Eater
# Palette: very dark blacks, deep purples, red hellfire glow, bone white
# ═══════════════════════════════════════════════════════

ABYSS_THEME = {
    "name": "Shadow Abyss",
    "boss_identity": "nyxarath",
    "boss_title": "The Soul Eater",

    # ─── TERRAIN (dark obsidian + scorched earth) ───
    "radiant_grass_1": (5, 4, 6),          # near-black ground
    "radiant_grass_2": (12, 8, 10),        # dark charcoal
    "radiant_grass_3": (22, 14, 16),       # scorched earth
    "radiant_grass_4": (35, 20, 22),       # burnt ground
    "radiant_grass_high": (55, 30, 28),    # ember-tinted highlight
    "radiant_moss": (18, 10, 12),          # dark ash patch

    # Dire side: deepest abyss
    "dire_earth_1": (2, 2, 3),             # shadow pit
    "dire_earth_2": (8, 5, 6),             # shadow black
    "dire_earth_3": (16, 10, 12),          # shadow darkest
    "dire_earth_4": (32, 18, 22),          # shadow dark
    "dire_ash": (20, 12, 14),              # dark ash
    "dire_burnt": (1, 1, 2),               # absolute darkness

    "transition_1": (15, 10, 12),          # dark transition
    "transition_2": (28, 16, 18),          # scorched transition

    # ─── PATH (dark stone with glowing red cracks) ───
    "path_stone_1": (8, 6, 7),             # dark obsidian
    "path_stone_2": (20, 14, 14),          # dark stone
    "path_stone_3": (40, 25, 24),          # worn stone
    "path_stone_4": (65, 40, 35),          # lighter stone
    "path_moss": (16, 10, 12),             # dark ash on path
    "path_crack": (255, 80, 30),           # GLOWING RED lava crack!

    # ─── RIVER (blood/lava stream) ───
    "river_deep": (25, 5, 8),              # dark blood
    "river_mid": (85, 15, 15),             # blood red
    "river_light": (180, 35, 25),          # fire red
    "river_glow": (240, 75, 45),           # bright fire
    "river_foam": (255, 145, 80),          # fire hot foam

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,         # dead shadow trees
    "has_dead_trees": True,         # scorched dead trees
    "has_gravestones": True,        # dark tombstones
    "has_crystals_blue": False,
    "has_crystals_red": True,       # red soul crystals
    "has_ancient_ruins": True,      # dark demonic ruins
    "has_bones": True,              # skeletal remains everywhere
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,        # obsidian rocks
    "has_dark_bushes": True,        # dark thorny bushes
    "has_glow_flowers": True,       # hellfire glow flowers (red)
    "has_spike_traps": True,        # bone spikes
    "has_torch_stones": True,       # red hellfire torches

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    "particle_type": "ember",       # red embers rising
    "particle_colors_radiant": [
        (180, 35, 25), (240, 75, 45), (255, 145, 80)
    ],
    "particle_colors_dire": [
        (95, 15, 12), (180, 35, 25), (35, 5, 5)
    ],
    "particle_count": 55,           # heavy ember rain

    "fog_enabled": True,
    "fog_color": (20, 8, 10, 50),   # dark red shadow fog
    "fog_count": 20,

    "ambient_tint": (40, 10, 10, 20),  # dark red hellfire tint
}


# REGISTRY (tambah theme baru di sini)
# ═══════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════
# NETHERVENOM EXPANSE (Level 8 - Vhoreth'zir)
# Warna diambil dari PALETTE bosses/vhorethzir.py supaya
# map menyatu dengan identitas true boss-nya.
# ═══════════════════════════════════════════════════════
NETHERVENOM_THEME = {
    "name": "Nethervenom Expanse",
    "boss_identity": "vhorethzir",
    "boss_title": "The Nethervenom Wyrm",

    # ─── TERRAIN (rawa racun hijau gelap) ───
    "radiant_grass_1": (6, 16, 8),          # lumpur racun near-black
    "radiant_grass_2": (14, 34, 18),        # scale_dark redup
    "radiant_grass_3": (24, 52, 28),        # rawa hijau gelap
    "radiant_grass_4": (38, 74, 42),        # lumut racun
    "radiant_grass_high": (70, 120, 70),    # sorotan hijau
    "radiant_moss": (20, 44, 22),           # lumut basah

    # Dire side: rawa nether paling dalam (ungu korupsi)
    "dire_earth_1": (4, 4, 10),             # nether_darkest
    "dire_earth_2": (10, 8, 20),            # lumpur nether
    "dire_earth_3": (18, 12, 34),           # ungu gelap
    "dire_earth_4": (30, 18, 55),           # nether_dark
    "dire_ash": (22, 30, 16),               # abu beracun
    "dire_burnt": (2, 2, 5),                # kegelapan pekat

    "transition_1": (14, 26, 16),           # transisi rawa
    "transition_2": (26, 40, 26),           # transisi lumut

    # ─── PATH (batu berlumut + retakan venom menyala) ───
    "path_stone_1": (10, 14, 9),            # batu rawa gelap
    "path_stone_2": (22, 30, 20),           # batu berlumut
    "path_stone_3": (44, 56, 38),           # batu aus
    "path_stone_4": (72, 86, 58),           # batu terang
    "path_moss": (18, 40, 20),              # lumut di jalan
    "path_crack": (200, 245, 80),           # RETAKAN VENOM (toxic_light)

    # ─── RIVER (sungai racun mengalir) ───
    "river_deep": (12, 26, 6),              # toxic_darkest pekat
    "river_mid": (60, 90, 15),              # toxic_dark
    "river_light": (140, 190, 35),          # toxic_mid
    "river_glow": (200, 245, 80),           # toxic_light
    "river_foam": (240, 255, 150),          # toxic_hot

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,         # pohon rawa gelap
    "has_dead_trees": True,         # pohon mati keracunan
    "has_gravestones": True,        # nisan korban racun
    "has_crystals_blue": False,
    "has_crystals_red": False,
    "has_ancient_ruins": True,      # reruntuhan sarang wyrm
    "has_bones": True,              # tulang mangsa
    "has_mushrooms_dark": True,     # jamur beracun
    "has_rocks_mossy": True,        # batu berlumut
    "has_dark_bushes": True,        # semak berduri
    "has_glow_flowers": True,       # bunga venom menyala
    "has_spike_traps": True,        # duri tulang
    "has_torch_stones": True,       # obor api hijau

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # PENTING: particle_type WAJIB salah satu dari
    # firefly / snow / sand / ember. _draw_particles() di
    # dynamic_renderer.py TIDAK punya cabang else, jadi tipe
    # lain membuat partikel tidak tergambar sama sekali.
    # "ember" dipakai agar spora racun melayang NAIK.
    "particle_type": "ember",
    "particle_colors_radiant": [
        (140, 190, 35), (200, 245, 80), (240, 255, 150)
    ],
    "particle_colors_dire": [
        (60, 90, 15), (80, 40, 120), (150, 100, 200)
    ],
    "particle_count": 60,           # spora racun lebat

    "fog_enabled": True,
    "fog_color": (18, 34, 12, 55),  # kabut racun hijau
    "fog_count": 22,

    "ambient_tint": (25, 45, 15, 22),  # semburat hijau racun
}


# ═══════════════════════════════════════════════════════
# SOULFORGED EXPANSE (Level 9 - Naraka)
# Warna diambil dari PALETTE bosses/level9.py (Naraka)
# supaya map menyatu dengan identitas true boss-nya:
# tanah pucat kelabu (kulit terkutuk) + energi jiwa CYAN.
# ═══════════════════════════════════════════════════════
SOULFORGED_THEME = {
    "name": "Soulforged Expanse",
    "boss_identity": "naraka",
    "boss_title": "The Lost Soul",

    # ─── TERRAIN (tanah pucat kelabu - kulit terkutuk Naraka) ───
    "radiant_grass_1": (28, 26, 38),         # abu jiwa near-black
    "radiant_grass_2": (46, 42, 56),         # kulit_dark redup
    "radiant_grass_3": (66, 62, 78),         # abu pucat
    "radiant_grass_4": (90, 84, 102),        # abu terang
    "radiant_grass_high": (130, 122, 145),   # kulit_light
    "radiant_moss": (36, 34, 48),            # abu lumut

    # Dire side: jurang tergelap + korupsi cyan
    "dire_earth_1": (4, 6, 10),              # cloth_darkest
    "dire_earth_2": (8, 12, 20),             # bayangan dalam
    "dire_earth_3": (14, 22, 34),            # biru-hitam
    "dire_earth_4": (22, 36, 52),            # cyan_darkest terang
    "dire_ash": (18, 24, 32),                # abu gelap
    "dire_burnt": (2, 3, 6),                 # kegelapan mutlak

    "transition_1": (24, 28, 38),            # transisi abu
    "transition_2": (40, 46, 60),            # transisi pucat

    # ─── PATH (batu gelap + retakan jiwa CYAN menyala) ───
    "path_stone_1": (12, 14, 20),            # batu gelap
    "path_stone_2": (26, 30, 40),            # batu bayangan
    "path_stone_3": (48, 54, 68),            # batu aus
    "path_stone_4": (74, 82, 96),            # batu terang
    "path_moss": (18, 24, 34),               # lumut bayangan
    "path_crack": (130, 235, 255),           # RETAKAN JIWA (cyan_light)

    # ─── RIVER (sungai energi jiwa) ───
    "river_deep": (5, 40, 60),               # cyan_darkest pekat
    "river_mid": (15, 100, 140),             # cyan_dark
    "river_light": (55, 190, 230),           # cyan_mid
    "river_glow": (130, 235, 255),           # cyan_light
    "river_foam": (200, 250, 255),           # cyan_hot

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,         # pohon bayangan mati
    "has_dead_trees": True,         # pohon mati tanpa jiwa
    "has_gravestones": True,        # nisan jiwa tersesat
    "has_crystals_blue": True,      # kristal jiwa cyan
    "has_crystals_red": False,
    "has_ancient_ruins": True,      # reruntuhan soulforged
    "has_bones": True,              # tulang jiwa terkutuk
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,        # batu abu berlumut
    "has_dark_bushes": True,        # semak bayangan
    "has_glow_flowers": True,       # bunga jiwa menyala
    "has_spike_traps": True,        # duri tulang
    "has_torch_stones": True,       # obor api jiwa CYAN

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "ember" = partikel melayang NAIK (wajib salah satu dari
    # firefly/snow/sand/ember untuk _draw_particles).
    "particle_type": "ember",
    "particle_colors_radiant": [
        (55, 190, 230), (130, 235, 255), (200, 250, 255)
    ],
    "particle_colors_dire": [
        (5, 40, 60), (15, 100, 140), (55, 190, 230)
    ],
    "particle_count": 60,           # wisps jiwa melayang naik

    "fog_enabled": True,
    "fog_color": (16, 28, 38, 55),  # kabut jiwa biru gelap
    "fog_count": 22,

    "ambient_tint": (18, 32, 42, 22),  # semburat cyan gelap
}

# ═══════════════════════════════════════════════════════
# RADIANT EXPANSE (Level 10 - Aureth'zar)
# Warna diambil dari PALETTE bosses/level10.py (Aureth'zar)
# supaya map menyatu dengan identitas true boss-nya:
# padang emas surya + retakan/sungai emas menyala.
# ═══════════════════════════════════════════════════════
RADIANT_THEME = {
    "name": "Radiant Expanse",
    "boss_identity": "aurethzar",
    "boss_title": "The Radiant Dawn",

    # ─── TERRAIN (padang emas surya - gold armor palette) ───
    "radiant_grass_1": (35, 22, 5),          # gold_darkest
    "radiant_grass_2": (70, 46, 10),         # tanah emas gelap
    "radiant_grass_3": (110, 78, 18),        # tanah emas
    "radiant_grass_4": (160, 115, 30),       # emas terang
    "radiant_grass_high": (240, 195, 80),    # gold_light
    "radiant_moss": (52, 34, 8),             # lumut emas gelap

    # Dire side: langit malam (sky palette) - kontras bayangan
    "dire_earth_1": (10, 15, 40),            # sky_dark
    "dire_earth_2": (18, 26, 60),            # malam dalam
    "dire_earth_3": (28, 40, 82),            # malam biru
    "dire_earth_4": (40, 55, 110),           # sky_mid
    "dire_ash": (24, 32, 62),                # abu malam
    "dire_burnt": (6, 9, 22),                # malam pekat

    "transition_1": (48, 32, 10),            # transisi senja
    "transition_2": (90, 62, 18),            # transisi emas

    # ─── PATH (batu senja + retakan emas menyala) ───
    "path_stone_1": (40, 26, 8),             # batu gelap
    "path_stone_2": (72, 48, 14),            # batu senja
    "path_stone_3": (110, 76, 22),           # batu emas
    "path_stone_4": (165, 120, 40),          # batu terang
    "path_moss": (56, 38, 10),               # lumut di jalan
    "path_crack": (255, 225, 140),           # RETAKAN EMAS (gold_edge)

    # ─── RIVER (sungai energi surya) ───
    "river_deep": (130, 75, 15),             # solar_dark
    "river_mid": (200, 130, 30),             # solar menengah
    "river_light": (230, 165, 40),           # solar_mid
    "river_glow": (255, 220, 100),           # solar_light
    "river_foam": (255, 245, 170),           # solar_hot

    # ─── DECORATION FLAGS ───
    "has_dark_trees": False,
    "has_dead_trees": False,
    "has_gravestones": False,
    "has_crystals_blue": False,
    "has_crystals_red": False,
    "has_ancient_ruins": True,      # reruntuhan emas kuno
    "has_bones": False,
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,        # batu emas berlumut
    "has_dark_bushes": False,
    "has_glow_flowers": True,       # bunga surya menyala
    "has_spike_traps": False,
    "has_torch_stones": True,       # obor api emas surya

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": True,         # bukit pasir emas
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "ember" = partikel melayang NAIK (wajib salah satu dari
    # firefly/snow/sand/ember untuk _draw_particles).
    "particle_type": "ember",
    "particle_colors_radiant": [
        (230, 165, 40), (255, 220, 100), (255, 245, 170)
    ],
    "particle_colors_dire": [
        (40, 55, 110), (130, 75, 15), (230, 165, 40)
    ],
    "particle_count": 55,           # debu emas surya

    "fog_enabled": True,
    "fog_color": (120, 80, 25, 45),  # kabut emas hangat
    "fog_count": 18,

    "ambient_tint": (50, 32, 8, 20),  # semburat emas senja
}

# ═══════════════════════════════════════════════════════
# ABYSSAL DEPTHS (Level 11 - Thalakryon)
# Warna diambil dari PALETTE bosses/level11.py (Thalakryon)
# supaya map menyatu dengan identitas true boss-nya:
# dasar laut dalam biru abisal + sisik teal + busa air.
# ═══════════════════════════════════════════════════════
ABYSSAL_THEME = {
    "name": "Abyssal Depths",
    "boss_identity": "thalakryon",
    "boss_title": "The Abyssal Sovereign",

    # ─── TERRAIN (dasar laut abisal - skin palette) ───
    "radiant_grass_1": (5, 15, 30),          # skin_darkest
    "radiant_grass_2": (15, 40, 70),         # skin_dark
    "radiant_grass_3": (35, 85, 130),        # skin_mid
    "radiant_grass_4": (70, 140, 190),       # skin_light
    "radiant_grass_high": (130, 200, 240),   # skin_edge
    "radiant_moss": (20, 60, 55),            # lumut sisik teal

    # Dire side: palung terdalam (azure_darkest)
    "dire_earth_1": (5, 20, 40),             # azure_darkest
    "dire_earth_2": (10, 45, 65),            # fin_dark
    "dire_earth_3": (20, 70, 130),           # azure_dark
    "dire_earth_4": (40, 110, 145),          # fin_mid
    "dire_ash": (15, 40, 70),                # pasir abisal
    "dire_burnt": (2, 8, 16),                # palung pekat

    "transition_1": (30, 55, 65),            # transisi dasar laut
    "transition_2": (70, 110, 130),          # transisi pasir

    # ─── PATH (batu tenggelam + retakan azure menyala) ───
    "path_stone_1": (10, 30, 50),            # batu abisal gelap
    "path_stone_2": (25, 55, 80),            # batu tenggelam
    "path_stone_3": (50, 100, 130),          # batu aus
    "path_stone_4": (85, 150, 180),          # batu terang
    "path_moss": (20, 60, 55),               # lumut sisik
    "path_crack": (180, 240, 255),           # RETAKAN AZURE (fin_glow)

    # ─── RIVER (arus air menyala) ───
    "river_deep": (5, 20, 45),               # water_darkest
    "river_mid": (20, 60, 110),              # water_dark
    "river_light": (50, 130, 190),           # water_mid
    "river_glow": (140, 210, 240),           # water_light
    "river_foam": (230, 250, 255),           # water_foam

    # ─── DECORATION FLAGS ───
    "has_dark_trees": False,
    "has_dead_trees": False,
    "has_gravestones": False,
    "has_crystals_blue": True,       # kristal laut azure
    "has_crystals_red": False,
    "has_ancient_ruins": True,       # reruntuhan kuil tenggelam
    "has_bones": True,               # tulang kapal karam
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,         # batu berkarang
    "has_dark_bushes": False,
    "has_glow_flowers": True,        # anemon laut menyala
    "has_spike_traps": False,
    "has_torch_stones": True,        # obor api azure

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": True,          # bukit pasir dasar laut
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "ember" = partikel melayang NAIK (gelembung air).
    "particle_type": "ember",
    "particle_colors_radiant": [
        (50, 130, 190), (140, 210, 240), (230, 250, 255)
    ],
    "particle_colors_dire": [
        (5, 20, 45), (20, 70, 130), (110, 190, 220)
    ],
    "particle_count": 60,           # gelembung abisal lebat

    "fog_enabled": True,
    "fog_color": (10, 30, 50, 55),  # kabut laut dalam
    "fog_count": 22,

    "ambient_tint": (15, 40, 55, 22),  # semburat biru abisal
}

# ═══════════════════════════════════════════════════════
# ELDRITCH DEPTHS (Level 12 - Nazulmor)
# Warna diambil dari PALETTE bosses/level12.py (Nazulmor)
# supaya map menyatu dengan identitas true boss-nya:
# jurang eldritch teal + sayap ungu + energi void menyala.
# ═══════════════════════════════════════════════════════
ELDRITCH_THEME = {
    "name": "Eldritch Depths",
    "boss_identity": "nazulmor",
    "boss_title": "The Deepborn Herald",

    # ─── TERRAIN (dasar jurang eldritch - skin teal) ───
    "radiant_grass_1": (5, 20, 25),          # skin_darkest
    "radiant_grass_2": (20, 55, 60),         # skin_dark
    "radiant_grass_3": (45, 110, 105),       # skin_mid
    "radiant_grass_4": (95, 175, 155),       # skin_light
    "radiant_grass_high": (160, 220, 190),   # skin_edge
    "radiant_moss": (25, 65, 75),            # lumut sisik

    # Dire side: palung eldritch (abyss purple)
    "dire_earth_1": (8, 3, 20),              # abyss_darkest
    "dire_earth_2": (30, 12, 55),            # abyss_dark
    "dire_earth_3": (70, 35, 110),           # abyss_mid
    "dire_earth_4": (140, 90, 190),          # abyss_light
    "dire_ash": (45, 20, 70),                # wing_dark
    "dire_burnt": (4, 2, 10),                # kegelapan mutlak

    "transition_1": (15, 60, 90),            # transisi void
    "transition_2": (40, 140, 180),          # transisi void terang

    # ─── PATH (batu tenggelam + retakan void menyala) ───
    "path_stone_1": (10, 35, 45),            # batu eldritch gelap
    "path_stone_2": (25, 65, 75),            # batu sisik
    "path_stone_3": (55, 130, 125),          # batu aus
    "path_stone_4": (110, 195, 170),         # batu terang
    "path_moss": (25, 65, 75),               # lumut eldritch
    "path_crack": (120, 220, 240),           # RETAKAN VOID (void_light)

    # ─── RIVER (arus energi void) ───
    "river_deep": (5, 20, 30),               # void_darkest
    "river_mid": (15, 60, 90),               # void_dark
    "river_light": (40, 140, 180),           # void_mid
    "river_glow": (120, 220, 240),           # void_light
    "river_foam": (200, 250, 255),           # void_hot

    # ─── DECORATION FLAGS ───
    "has_dark_trees": False,
    "has_dead_trees": False,
    "has_gravestones": False,
    "has_crystals_blue": True,       # kristal void teal
    "has_crystals_red": False,
    "has_ancient_ruins": True,       # reruntuhan eldritch kuno
    "has_bones": True,               # tulang korban herald
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,         # batu bersisik
    "has_dark_bushes": False,
    "has_glow_flowers": True,        # flora void menyala
    "has_spike_traps": False,
    "has_torch_stones": True,        # obor api void teal

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "ember" = partikel melayang NAIK (wisps void).
    "particle_type": "ember",
    "particle_colors_radiant": [
        (40, 140, 180), (120, 220, 240), (200, 250, 255)
    ],
    "particle_colors_dire": [
        (8, 3, 20), (70, 35, 110), (40, 140, 180)
    ],
    "particle_count": 60,           # wisps eldritch lebat

    "fog_enabled": True,
    "fog_color": (12, 30, 40, 55),  # kabut void
    "fog_count": 22,

    "ambient_tint": (10, 45, 55, 22),  # semburat teal eldritch
}

# ═══════════════════════════════════════════════════════
# SILVER SANCTUM (Level 13 - Solvarin)
# Warna diambil dari PALETTE bosses/level13.py (Solvarin)
# supaya map menyatu dengan identitas true boss-nya:
# katedral perak-putih + tabard biru + trim emas menyala.
# ═══════════════════════════════════════════════════════
SANCTUM_THEME = {
    "name": "Silver Sanctum",
    "boss_identity": "solvarin",
    "boss_title": "The Holy Paladin Warden",

    # ─── TERRAIN (marmer perak-putih - silver armor palette) ───
    "radiant_grass_1": (35, 40, 50),          # silver_darkest
    "radiant_grass_2": (85, 90, 105),         # silver_dark
    "radiant_grass_3": (155, 160, 175),       # silver_mid
    "radiant_grass_4": (215, 220, 230),       # silver_light
    "radiant_grass_high": (250, 252, 255),    # silver_shine
    "radiant_moss": (110, 115, 130),          # lumut marmer

    # Dire side: ruang bawah katedral (blue tabard gelap)
    "dire_earth_1": (10, 20, 45),             # blue_darkest
    "dire_earth_2": (25, 50, 105),            # blue_dark
    "dire_earth_3": (55, 105, 180),           # blue_mid
    "dire_earth_4": (130, 180, 235),          # blue_light
    "dire_ash": (40, 45, 60),                 # abu batu
    "dire_burnt": (5, 10, 22),                # ruang bawah pekat

    "transition_1": (60, 65, 80),             # transisi marmer
    "transition_2": (110, 120, 145),          # transisi perak

    # ─── PATH (batu katedral + retakan emas suci menyala) ───
    "path_stone_1": (30, 35, 45),             # batu gelap
    "path_stone_2": (70, 76, 90),             # batu katedral
    "path_stone_3": (120, 128, 145),          # batu aus
    "path_stone_4": (175, 182, 200),          # batu terang
    "path_moss": (80, 88, 105),               # lumut batu
    "path_crack": (250, 210, 100),            # RETAKAN EMAS SUCI (gold_light)

    # ─── RIVER (arus cahaya suci) ───
    "river_deep": (55, 105, 180),             # blue_mid
    "river_mid": (130, 180, 235),             # blue_light
    "river_light": (200, 225, 250),           # blue_edge
    "river_glow": (255, 245, 180),            # gold_shine
    "river_foam": (255, 255, 230),            # gold_white

    # ─── DECORATION FLAGS ───
    "has_dark_trees": False,
    "has_dead_trees": False,
    "has_gravestones": False,
    "has_crystals_blue": True,       # kristal cahaya biru
    "has_crystals_red": False,
    "has_ancient_ruins": True,       # reruntuhan katedral kuno
    "has_bones": False,
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,         # batu marmer berlumut
    "has_dark_bushes": False,
    "has_glow_flowers": True,        # bunga cahaya suci
    "has_spike_traps": False,
    "has_torch_stones": True,        # obor api emas suci

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "ember" = partikel melayang NAIK (debu cahaya suci).
    "particle_type": "ember",
    "particle_colors_radiant": [
        (215, 220, 230), (250, 210, 100), (255, 245, 180)
    ],
    "particle_colors_dire": [
        (25, 50, 105), (55, 105, 180), (130, 180, 235)
    ],
    "particle_count": 55,           # debu cahaya suci

    "fog_enabled": True,
    "fog_color": (90, 96, 112, 45),  # kabut marmer
    "fog_count": 18,

    "ambient_tint": (40, 45, 60, 20),  # semburat perak suci
}

# ═══════════════════════════════════════════════════════
# ETERNAL FLAME (Level 14 - Pyraethis)
# Warna diambil dari PALETTE bosses/level14.py (Pyraethis)
# supaya map menyatu dengan identitas true boss-nya:
# tanah abu hangus + bara phoenix + semburan api abadi.
# ═══════════════════════════════════════════════════════
ETERNALFLAME_THEME = {
    "name": "Eternal Flame",
    "boss_identity": "pyraethis",
    "boss_title": "The Eternal Firebird",

    # ─── TERRAIN (abu hangus + bara - feather palette) ───
    "radiant_grass_1": (45, 14, 8),           # feather_darkest abu
    "radiant_grass_2": (95, 28, 12),          # feather_dark bara
    "radiant_grass_3": (150, 55, 20),         # feather_mid ember
    "radiant_grass_4": (205, 95, 30),         # feather_light api
    "radiant_grass_high": (255, 150, 45),     # feather_bright pijar
    "radiant_moss": (120, 40, 15),            # lumut bara

    # Dire side: inti api gelap (core & flame dark)
    "dire_earth_1": (25, 4, 2),               # core_darkest
    "dire_earth_2": (60, 12, 4),              # core_dark
    "dire_earth_3": (110, 30, 8),             # core_mid gelap
    "dire_earth_4": (170, 60, 14),            # flame_dark
    "dire_ash": (35, 8, 4),                   # abu vulkanik
    "dire_burnt": (12, 2, 1),                 # hangus pekat

    "transition_1": (70, 22, 8),              # transisi abu
    "transition_2": (130, 45, 14),            # transisi bara

    # ─── PATH (batu hangus + retakan api menyala) ───
    "path_stone_1": (35, 12, 6),              # batu hangus
    "path_stone_2": (70, 25, 10),             # batu bara
    "path_stone_3": (110, 45, 16),            # batu api
    "path_stone_4": (160, 75, 25),            # batu pijar
    "path_moss": (90, 35, 12),                # lumut bara
    "path_crack": (255, 200, 60),             # RETAKAN API (flame_light)

    # ─── RIVER (arus api abadi) ───
    "river_deep": (200, 60, 10),              # core_mid
    "river_mid": (255, 120, 25),              # core_light
    "river_light": (255, 200, 60),            # flame_light
    "river_glow": (255, 240, 130),            # flame_hot
    "river_foam": (255, 253, 220),            # flame_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon hangus
    "has_dead_trees": True,        # pohon mati terbakar
    "has_gravestones": False,
    "has_crystals_blue": False,
    "has_crystals_red": True,      # kristal bara api
    "has_ancient_ruins": True,     # kuil burung api kuno
    "has_bones": False,
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,       # batu berlumut bara
    "has_dark_bushes": True,       # semak hangus
    "has_glow_flowers": True,      # bunga api berpendar
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor api abadi

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "ember" = partikel melayang NAIK (bara api abadi).
    "particle_type": "ember",
    "particle_colors_radiant": [
        (255, 140, 30), (255, 200, 60), (255, 240, 130)
    ],
    "particle_colors_dire": [
        (100, 25, 5), (170, 60, 5), (240, 130, 20)
    ],
    "particle_count": 55,           # bara api abadi

    "fog_enabled": True,
    "fog_color": (70, 40, 25, 45),  # kabut asap api
    "fog_count": 18,

    "ambient_tint": (60, 30, 15, 20),  # semburat bara api
}

# ═══════════════════════════════════════════════════════
# PRIMORDIAL GROVE (Level 15 - Yamako)
# Warna diambil dari PALETTE bosses/level15.py (Yamako)
# supaya map menyatu dengan identitas true boss-nya:
# hutan suci hijau purba + kayu kuno + cahaya daun menyala.
# ═══════════════════════════════════════════════════════
PRIMORDIAL_THEME = {
    "name": "Primordial Grove",
    "boss_identity": "yamako",
    "boss_title": "The Primordial Woodshaper",

    # ─── TERRAIN (lumut hijau purba - robe palette) ───
    "radiant_grass_1": (5, 15, 8),            # robe_darkest
    "radiant_grass_2": (18, 45, 22),          # robe_dark
    "radiant_grass_3": (40, 85, 45),          # robe_mid
    "radiant_grass_4": (85, 140, 90),         # robe_light
    "radiant_grass_high": (140, 190, 140),    # robe_edge
    "radiant_moss": (25, 60, 28),             # lumut purba

    # Dire side: hutan kayu kuno gelap (wood palette)
    "dire_earth_1": (18, 12, 5),              # wood_darkest
    "dire_earth_2": (55, 35, 15),             # wood_dark
    "dire_earth_3": (100, 70, 30),            # wood_mid
    "dire_earth_4": (160, 120, 55),           # wood_light
    "dire_ash": (30, 22, 14),                 # serpihan kayu
    "dire_burnt": (8, 5, 3),                  # akar pekat

    "transition_1": (55, 60, 35),             # transisi lumut
    "transition_2": (95, 105, 60),            # transisi daun

    # ─── PATH (papan kayu purba + retakan cahaya daun) ───
    "path_stone_1": (25, 18, 10),             # kayu gelap
    "path_stone_2": (55, 40, 20),             # kayu kuno
    "path_stone_3": (95, 70, 35),             # kayu aus
    "path_stone_4": (140, 105, 55),           # kayu terang
    "path_moss": (30, 70, 25),                # lumut kayu
    "path_crack": (130, 220, 100),            # RETAKAN CAHAYA DAUN (leaf_light)

    # ─── RIVER (getah suci bercahaya) ───
    "river_deep": (15, 60, 20),               # leaf_dark
    "river_mid": (55, 140, 55),               # leaf_mid
    "river_light": (130, 220, 100),           # leaf_light
    "river_glow": (200, 255, 140),            # nat_hot
    "river_foam": (240, 255, 220),            # eye_glow

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon purba raksasa
    "has_dead_trees": False,
    "has_gravestones": False,
    "has_crystals_blue": False,
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # reruntuhan kuno ditumbuhi
    "has_bones": False,
    "has_mushrooms_dark": True,    # jamur hutan purba
    "has_rocks_mossy": True,       # batu berlumut
    "has_dark_bushes": True,       # semak hutan lebat
    "has_glow_flowers": True,      # bunga cahaya hijau
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor api hijau suci

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = kunang-kunang cahaya daun suci.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (130, 220, 100), (200, 255, 140), (240, 255, 220)
    ],
    "particle_colors_dire": [
        (18, 45, 22), (40, 85, 45), (85, 140, 90)
    ],
    "particle_count": 55,           # kunang-kunang suci

    "fog_enabled": True,
    "fog_color": (20, 45, 25, 45),  # kabut hutan purba
    "fog_count": 18,

    "ambient_tint": (30, 60, 30, 20),  # semburat hijau purba
}

# ═══════════════════════════════════════════════════════
# CELESTIAL PEAKS (Level 16 - Seiryukong)
# Warna diambil dari PALETTE bosses/level16.py (Seiryukong)
# supaya map menyatu dengan identitas true boss-nya:
# kuil emas di atas awan + batu pegunungan + kabut awan.
# ═══════════════════════════════════════════════════════
CELESTIALPEAKS_THEME = {
    "name": "Celestial Peaks",
    "boss_identity": "seiryukong",
    "boss_title": "The Celestial Simian",

    # ─── TERRAIN (batu kuil emas - gold/fur palette) ───
    "radiant_grass_1": (60, 40, 20),           # batu coklat gelap
    "radiant_grass_2": (110, 75, 45),          # batu pegunungan
    "radiant_grass_3": (170, 125, 80),         # batu emas
    "radiant_grass_4": (220, 180, 130),        # batu terang
    "radiant_grass_high": (245, 220, 175),     # fur_shine
    "radiant_moss": (90, 60, 35),              # lumut gunung

    # Dire side: tebing merah langit senja (red palette)
    "dire_earth_1": (25, 10, 8),               # tebing gelap
    "dire_earth_2": (60, 18, 15),              # tebing merah tua
    "dire_earth_3": (110, 30, 25),             # tebing merah
    "dire_earth_4": (170, 55, 45),             # tebing senja
    "dire_ash": (45, 30, 25),                  # abu batu
    "dire_burnt": (10, 5, 4),                  # lembah pekat

    "transition_1": (80, 55, 35),              # transisi batu
    "transition_2": (120, 85, 55),             # transisi emas

    # ─── PATH (undakan kuil + retakan emas langit) ───
    "path_stone_1": (30, 20, 12),              # undakan gelap
    "path_stone_2": (60, 40, 22),              # undakan batu
    "path_stone_3": (95, 65, 35),              # undakan aus
    "path_stone_4": (140, 100, 55),            # undakan terang
    "path_moss": (75, 55, 30),                 # lumut undakan
    "path_crack": (255, 225, 130),             # RETAKAN EMAS LANGIT (gold_edge)

    # ─── RIVER (lautan awan) ───
    "river_deep": (120, 130, 160),             # awan gelap
    "river_mid": (175, 185, 210),              # awan
    "river_light": (225, 230, 245),            # awan terang
    "river_glow": (255, 250, 210),             # gold_shine
    "river_foam": (255, 255, 255),             # putih awan

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pinus pegunungan
    "has_dead_trees": False,
    "has_gravestones": False,
    "has_crystals_blue": True,     # kristal langit
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # reruntuhan kuil langit
    "has_bones": False,
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,       # batu gunung berlumut
    "has_dark_bushes": False,
    "has_glow_flowers": True,      # bunga awan berpendar
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor api emas langit

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "snow" = partikel awan turun perlahan.
    "particle_type": "snow",
    "particle_colors_radiant": [
        (225, 230, 245), (255, 250, 210), (255, 255, 255)
    ],
    "particle_colors_dire": [
        (110, 30, 25), (170, 55, 45), (120, 130, 160)
    ],
    "particle_count": 55,           # serpihan awan

    "fog_enabled": True,
    "fog_color": (200, 200, 215, 40),  # kabut awan
    "fog_count": 18,

    "ambient_tint": (120, 95, 60, 20),  # semburat emas langit
}

# ═══════════════════════════════════════════════════════
# COSMIC EXPANSE (Level 17 - Nyxareth)
# Warna diambil dari PALETTE bosses/level17.py (Nyxareth)
# supaya map menyatu dengan identitas true boss-nya:
# hamparan void kosmik + nebula ungu + bintang berkelip.
# ═══════════════════════════════════════════════════════
COSMIC_THEME = {
    "name": "Cosmic Expanse",
    "boss_identity": "nyxareth",
    "boss_title": "The Cosmic Sovereign",

    # ─── TERRAIN (nebula ungu - cosmic palette) ───
    "radiant_grass_1": (25, 10, 60),           # nebula gelap
    "radiant_grass_2": (60, 25, 120),          # nebula dalam
    "radiant_grass_3": (120, 60, 190),         # nebula
    "radiant_grass_4": (180, 110, 240),        # nebula terang
    "radiant_grass_high": (230, 170, 255),     # cosmic_hot
    "radiant_moss": (45, 15, 90),              # lumut nebula

    # Dire side: void hitam pekat (void palette)
    "dire_earth_1": (5, 0, 15),                # void_darkest
    "dire_earth_2": (15, 8, 35),               # void_dark
    "dire_earth_3": (35, 20, 75),              # void_mid
    "dire_earth_4": (70, 45, 130),             # void_light
    "dire_ash": (25, 15, 50),                  # abu kosmik
    "dire_burnt": (3, 0, 8),                   # void pekat

    "transition_1": (40, 18, 85),              # transisi void
    "transition_2": (80, 40, 140),             # transisi nebula

    # ─── PATH (batu bintang + retakan nebula) ───
    "path_stone_1": (20, 12, 40),              # batu void
    "path_stone_2": (45, 25, 80),              # batu kosmik
    "path_stone_3": (75, 45, 130),             # batu nebula
    "path_stone_4": (110, 70, 180),            # batu terang
    "path_moss": (35, 20, 70),                 # lumut bintang
    "path_crack": (235, 180, 255),             # RETAKAN NEBULA (cosmic_hot)

    # ─── RIVER (arus nebula) ───
    "river_deep": (65, 20, 130),               # cosmic_dark
    "river_mid": (135, 55, 220),               # cosmic_mid
    "river_light": (200, 130, 255),            # cosmic_light
    "river_glow": (235, 180, 255),             # cosmic_hot
    "river_foam": (250, 225, 255),             # cosmic_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": False,
    "has_dead_trees": False,
    "has_gravestones": False,
    "has_crystals_blue": True,     # kristal bintang
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # reruntuhan kuil bintang
    "has_bones": False,
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,       # batu kosmik berlumut
    "has_dark_bushes": False,
    "has_glow_flowers": True,      # bunga bintang berpendar
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor api nebula

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = bintang berkelip di langit kosmik.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (230, 220, 255), (250, 225, 255), (255, 255, 255)
    ],
    "particle_colors_dire": [
        (70, 45, 130), (135, 55, 220), (200, 130, 255)
    ],
    "particle_count": 60,           # bintang berkelip

    "fog_enabled": True,
    "fog_color": (45, 20, 90, 45),  # kabut nebula
    "fog_count": 18,

    "ambient_tint": (35, 15, 70, 20),  # semburat nebula ungu
}

# ═══════════════════════════════════════════════════════
# ROYAL CITADEL (Level 18 - Aurelion)
# Warna diambil dari PALETTE bosses/level18.py (Aurelion)
# supaya map menyatu dengan identitas true boss-nya:
# istana emas + karpet merah kerajaan + parit biru kerajaan.
# ═══════════════════════════════════════════════════════
ROYAL_THEME = {
    "name": "Royal Citadel",
    "boss_identity": "aurelion",
    "boss_title": "The Golden Sovereign",

    # ─── TERRAIN (marmer istana emas - gold/royal palette) ───
    "radiant_grass_1": (80, 55, 10),           # gold_deep
    "radiant_grass_2": (115, 85, 20),          # gold_dark
    "radiant_grass_3": (200, 155, 40),         # gold_mid
    "radiant_grass_4": (245, 215, 95),         # gold_light
    "radiant_grass_high": (255, 245, 180),     # gold_shine
    "radiant_moss": (140, 100, 20),            # royal_dark lumut

    # Dire side: menara gelap kastil (leather palette)
    "dire_earth_1": (25, 15, 8),               # leather_darkest
    "dire_earth_2": (55, 35, 20),              # leather_dark
    "dire_earth_3": (95, 65, 35),              # leather_mid
    "dire_earth_4": (155, 115, 65),            # leather_light
    "dire_ash": (40, 25, 15),                  # abu kastil
    "dire_burnt": (10, 6, 4),                  # ruang bawah pekat

    "transition_1": (60, 42, 15),              # transisi emas
    "transition_2": (115, 85, 35),             # transisi marmer

    # ─── PATH (karpet merah kerajaan + retakan emas) ───
    "path_stone_1": (45, 5, 15),               # cape_darkest
    "path_stone_2": (95, 15, 30),              # cape_dark
    "path_stone_3": (165, 30, 45),             # cape_mid
    "path_stone_4": (215, 60, 80),             # cape_light
    "path_moss": (75, 12, 25),                 # karpet aus
    "path_crack": (255, 245, 180),             # RETAKAN EMAS (gold_shine)

    # ─── RIVER (parit biru kerajaan) ───
    "river_deep": (10, 30, 90),                # blue_dark
    "river_mid": (40, 90, 190),                # blue_mid
    "river_light": (120, 180, 250),            # blue_light
    "river_glow": (245, 215, 95),              # pantulan emas
    "river_foam": (255, 255, 220),             # gold_bright

    # ─── DECORATION FLAGS ───
    "has_dark_trees": False,
    "has_dead_trees": False,
    "has_gravestones": False,
    "has_crystals_blue": True,     # kristal biru kerajaan
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # reruntuhan istana kuno
    "has_bones": False,
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,       # batu istana berlumut
    "has_dark_bushes": False,
    "has_glow_flowers": True,      # bunga emas berpendar
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor api emas kerajaan

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = debu emas berkilau di aula istana.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (245, 215, 95), (255, 245, 180), (255, 255, 220)
    ],
    "particle_colors_dire": [
        (95, 15, 30), (165, 30, 45), (215, 60, 80)
    ],
    "particle_count": 55,           # debu emas

    "fog_enabled": True,
    "fog_color": (120, 90, 40, 40),  # kabut keemasan
    "fog_count": 18,

    "ambient_tint": (90, 60, 20, 20),  # semburat emas kerajaan
}

# ═══════════════════════════════════════════════════════
# VIOLET COURT (Level 19 - Vaelindra)
# Warna diambil dari PALETTE bosses/level19.py (Vaelindra)
# supaya map menyatu dengan identitas true boss-nya:
# istana violet kerajaan + lavender + trim emas menyala.
# ═══════════════════════════════════════════════════════
VIOLET_THEME = {
    "name": "Violet Court",
    "boss_identity": "vaelindra",
    "boss_title": "The Violet Sovereign",

    # ─── TERRAIN (permadani violet - gown palette) ───
    "radiant_grass_1": (15, 5, 35),            # gown_darkest
    "radiant_grass_2": (40, 15, 80),           # gown_dark
    "radiant_grass_3": (85, 40, 155),          # gown_mid
    "radiant_grass_4": (155, 100, 220),        # gown_light
    "radiant_grass_high": (200, 160, 245),     # gown_edge
    "radiant_moss": (60, 25, 110),             # lumut lavender

    # Dire side: sayap ungu gelap (wing palette)
    "dire_earth_1": (20, 5, 45),               # wing_darkest
    "dire_earth_2": (60, 20, 120),             # wing_dark
    "dire_earth_3": (140, 70, 210),            # wing_mid
    "dire_earth_4": (210, 150, 250),           # wing_light
    "dire_ash": (45, 15, 90),                  # abu violet
    "dire_burnt": (8, 2, 20),                  # ruang pekat

    "transition_1": (55, 25, 100),             # transisi violet
    "transition_2": (95, 50, 150),             # transisi lavender

    # ─── PATH (batu lavender + retakan emas) ───
    "path_stone_1": (35, 15, 70),              # batu gelap
    "path_stone_2": (65, 30, 120),             # batu violet
    "path_stone_3": (100, 55, 170),            # batu lavender
    "path_stone_4": (140, 90, 210),            # batu terang
    "path_moss": (50, 25, 100),                # lumut batu
    "path_crack": (255, 245, 200),             # RETAKAN EMAS (gold_shine)

    # ─── RIVER (arus sihir violet) ───
    "river_deep": (30, 5, 55),                 # magic_darkest
    "river_mid": (85, 20, 145),                # magic_dark
    "river_light": (170, 55, 230),             # magic_mid
    "river_glow": (245, 190, 255),             # magic_hot
    "river_foam": (255, 235, 255),             # magic_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": False,
    "has_dead_trees": False,
    "has_gravestones": False,
    "has_crystals_blue": True,     # kristal lavender
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # reruntuhan istana violet
    "has_bones": False,
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,       # batu berlumut violet
    "has_dark_bushes": False,
    "has_glow_flowers": True,      # bunga violet berpendar
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor api violet

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = kelopak sihir berkilau.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (220, 130, 255), (245, 190, 255), (255, 245, 200)
    ],
    "particle_colors_dire": [
        (60, 20, 120), (140, 70, 210), (210, 150, 250)
    ],
    "particle_count": 55,           # kelopak sihir

    "fog_enabled": True,
    "fog_color": (55, 25, 100, 45),  # kabut violet
    "fog_count": 18,

    "ambient_tint": (45, 15, 90, 20),  # semburat violet kerajaan
}

# ═══════════════════════════════════════════════════════
# CRIMSON DOMINION (Level 20 - Morthraxis)
# Warna diambil dari PALETTE bosses/level20.py (Morthraxis)
# supaya map menyatu dengan identitas true boss-nya:
# kastil vampir merah darah + batu gotik gelap + sungai darah.
# ═══════════════════════════════════════════════════════
CRIMSON_THEME = {
    "name": "Crimson Dominion",
    "boss_identity": "morthraxis",
    "boss_title": "The Crimson Sovereign",

    # ─── TERRAIN (batu darah merah - blood palette) ───
    "radiant_grass_1": (30, 5, 10),            # blood_darkest
    "radiant_grass_2": (80, 10, 25),           # blood_dark
    "radiant_grass_3": (160, 25, 50),          # blood_mid
    "radiant_grass_4": (220, 50, 90),          # blood_light
    "radiant_grass_high": (255, 90, 130),      # blood_hot
    "radiant_moss": (55, 8, 20),               # lumut darah

    # Dire side: kastil vampir hitam (cloth palette)
    "dire_earth_1": (8, 5, 12),                # cloth_darkest
    "dire_earth_2": (25, 15, 20),              # batu gotik
    "dire_earth_3": (55, 30, 35),              # batu abu
    "dire_earth_4": (110, 70, 75),             # batu kelabu
    "dire_ash": (40, 15, 20),                  # abu kastil
    "dire_burnt": (5, 3, 6),                   # ruang bawah pekat

    "transition_1": (60, 12, 25),              # transisi darah
    "transition_2": (110, 25, 45),             # transisi kastil

    # ─── PATH (batu darah + retakan emas vampir) ───
    "path_stone_1": (15, 4, 8),                # batu darah gelap
    "path_stone_2": (40, 8, 15),               # batu darah
    "path_stone_3": (90, 15, 30),              # batu aus
    "path_stone_4": (150, 30, 55),             # batu terang
    "path_moss": (45, 8, 18),                  # lumut darah
    "path_crack": (255, 245, 180),             # RETAKAN EMAS (gold_shine)

    # ─── RIVER (sungai darah) ───
    "river_deep": (80, 10, 25),                # blood_dark
    "river_mid": (160, 25, 50),                # blood_mid
    "river_light": (220, 50, 90),              # blood_light
    "river_glow": (255, 90, 130),              # blood_hot
    "river_foam": (255, 180, 200),             # blood_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon mati gotik
    "has_dead_trees": True,        # pohon kering
    "has_gravestones": True,       # kuburan vampir
    "has_crystals_blue": False,
    "has_crystals_red": True,      # kristal darah
    "has_ancient_ruins": True,     # kastil vampir kuno
    "has_bones": True,             # tulang belulang
    "has_mushrooms_dark": True,    # jamur gelap
    "has_rocks_mossy": True,       # batu berlumut darah
    "has_dark_bushes": True,       # semak gelap
    "has_glow_flowers": False,
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor api darah

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan darah berkilau di malam vampir.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (255, 90, 130), (255, 180, 200), (240, 210, 100)
    ],
    "particle_colors_dire": [
        (80, 10, 25), (160, 25, 50), (220, 50, 90)
    ],
    "particle_count": 55,           # percikan darah

    "fog_enabled": True,
    "fog_color": (60, 10, 25, 45),  # kabut darah
    "fog_count": 18,

    "ambient_tint": (30, 5, 12, 20),  # semburat merah darah
}

SPECTRAL_THEME = {
    "name": "The Hollow Veil",
    "boss_identity": "nexthyrius",
    "boss_title": "The Chained Hollow",

    # ─── TERRAIN (tanah spectral teal - ghostly hollow) ───
    "radiant_grass_1": (2, 8, 12),            # spec_darkest
    "radiant_grass_2": (10, 25, 35),          # spec_dark
    "radiant_grass_3": (25, 55, 70),          # spec_mid
    "radiant_grass_4": (55, 100, 120),        # spec_light
    "radiant_grass_high": (100, 160, 180),    # spec_edge
    "radiant_moss": (30, 160, 140),           # lumut soul fire

    # Dire side: kastil hollow nether (rantai besi + ungu nether)
    "dire_earth_1": (5, 10, 12),              # chain_darkest
    "dire_earth_2": (20, 10, 40),             # nether_dark
    "dire_earth_3": (70, 40, 130),            # nether_mid
    "dire_earth_4": (150, 100, 220),          # nether_light
    "dire_ash": (25, 35, 40),                 # abu rantai
    "dire_burnt": (2, 2, 4),                  # ruang bawah pekat

    "transition_1": (15, 40, 45),             # transisi spectral
    "transition_2": (45, 30, 80),             # transisi nether

    # ─── PATH (rantai besi gelap + retakan soul fire) ───
    "path_stone_1": (5, 10, 12),              # chain_darkest
    "path_stone_2": (25, 35, 40),             # chain_dark
    "path_stone_3": (70, 85, 95),             # chain_mid
    "path_stone_4": (150, 170, 180),          # chain_light
    "path_moss": (10, 60, 55),                # lumut soul
    "path_crack": (80, 240, 200),             # RETAKAN SOUL FIRE (soul_light)

    # ─── RIVER (sungai jiwa - soul fire hijau) ───
    "river_deep": (2, 20, 18),                # soul_darkest
    "river_mid": (10, 60, 55),                # soul_dark
    "river_light": (30, 160, 140),            # soul_mid
    "river_glow": (80, 240, 200),             # soul_light
    "river_foam": (230, 255, 245),            # soul_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon mati spectral
    "has_dead_trees": True,        # pohon kering
    "has_gravestones": True,       # kuburan hollow
    "has_crystals_blue": True,     # kristal teal
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # penjara kuno berantai
    "has_bones": True,             # tulang belulang
    "has_mushrooms_dark": True,    # jamur gelap
    "has_rocks_mossy": True,       # batu berlumut soul
    "has_dark_bushes": True,       # semak gelap
    "has_glow_flowers": True,      # bunga api jiwa
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor soul fire

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = roh-roh kecil (soul wisp) melayang di lembah hampa.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (80, 240, 200), (200, 255, 255), (170, 255, 230)
    ],
    "particle_colors_dire": [
        (0, 80, 90), (30, 160, 140), (150, 100, 220)
    ],
    "particle_count": 60,           # soul wisp

    "fog_enabled": True,
    "fog_color": (10, 60, 55, 45),  # kabut soul hijau
    "fog_count": 18,

    "ambient_tint": (5, 25, 30, 20),  # semburat spectral teal
}

SUNDERED_THEME = {
    "name": "The Sundered Peak",
    "boss_identity": "molgravar",
    "boss_title": "The Colossus of the Sundered Peak",

    # ─── TERRAIN (batu golem abu-cokelat, sisi koloni retak lava) ───
    "radiant_grass_1": (18, 12, 8),            # stone_darkest
    "radiant_grass_2": (48, 34, 22),           # stone_dark
    "radiant_grass_3": (95, 72, 48),           # stone_mid
    "radiant_grass_4": (155, 122, 85),         # stone_light
    "radiant_grass_high": (210, 180, 135),     # stone_shine
    "radiant_moss": (120, 200, 60),            # lumut mata golem

    # Dire side: batu vulkanik pekat + abu + ember lava
    "dire_earth_1": (8, 5, 3),                 # rock_darkest
    "dire_earth_2": (25, 18, 12),              # rock_dark
    "dire_earth_3": (55, 42, 28),              # rock_mid
    "dire_earth_4": (130, 85, 45),             # batu lava
    "dire_ash": (40, 28, 18),                  # abu vulkanik
    "dire_burnt": (5, 3, 2),                   # ruang bawah pekat

    "transition_1": (60, 40, 22),              # transisi batu
    "transition_2": (110, 60, 25),             # transisi lava

    # ─── PATH (batu pecah + retakan lava menyala) ───
    "path_stone_1": (15, 10, 7),               # batu gelap
    "path_stone_2": (45, 32, 20),              # batu
    "path_stone_3": (95, 70, 45),              # batu aus
    "path_stone_4": (160, 125, 88),            # batu terang
    "path_moss": (65, 50, 30),                 # lumut debu
    "path_crack": (255, 230, 130),             # RETAKAN LAVA (lava_hot)

    # ─── RIVER (sungai lava menyala) ───
    "river_deep": (35, 12, 3),                 # lava_darkest
    "river_mid": (95, 40, 8),                  # lava_dark
    "river_light": (200, 100, 25),             # lava_mid
    "river_glow": (255, 180, 60),              # lava_light
    "river_foam": (255, 250, 200),             # lava_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon mati hangus
    "has_dead_trees": True,        # pohon kering
    "has_gravestones": True,       # reruntuhan
    "has_crystals_blue": False,
    "has_crystals_red": True,      # kristal lava
    "has_ancient_ruins": True,     # puncak gunung terbelah
    "has_bones": True,             # tulang belulang
    "has_mushrooms_dark": True,    # jamur gelap
    "has_rocks_mossy": True,       # batu berlumut debu
    "has_dark_bushes": True,       # semak hangus
    "has_glow_flowers": False,
    "has_spike_traps": True,       # duri batu vulkanik
    "has_torch_stones": True,      # obor lava

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan ember lava beterbangan di puncak terbelah.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (255, 180, 60), (255, 230, 130), (255, 250, 200)
    ],
    "particle_colors_dire": [
        (95, 40, 8), (200, 100, 25), (255, 180, 60)
    ],
    "particle_count": 60,           # ember lava

    "fog_enabled": True,
    "fog_color": (55, 42, 28, 45),  # kabut abu vulkanik
    "fog_count": 18,

    "ambient_tint": (40, 18, 6, 20),  # semburat lava oranye
}

EMPYREAN_THEME = {
    "name": "The Empyrean Executioner",
    "boss_identity": "seraphienne",
    "boss_title": "The Empyrean Executioner",

    # ─── TERRAIN (marmar surgawi keemasan, sisi kolom cahaya divine) ───
    "radiant_grass_1": (35, 20, 3),            # gold_darkest
    "radiant_grass_2": (105, 70, 15),          # gold_dark
    "radiant_grass_3": (200, 150, 45),         # gold_mid
    "radiant_grass_4": (250, 215, 105),        # gold_light
    "radiant_grass_high": (255, 240, 170),     # gold_hot
    "radiant_moss": (190, 145, 50),            # lumut feather

    # Dire side: altar surgawi gelap + armor putih bercahaya
    "dire_earth_1": (55, 55, 70),              # armor_darkest
    "dire_earth_2": (110, 110, 130),           # armor_dark
    "dire_earth_3": (175, 175, 195),           # armor_mid
    "dire_earth_4": (230, 230, 240),           # armor_light
    "dire_ash": (90, 80, 60),                  # abu altar
    "dire_burnt": (25, 20, 30),                # ruang bawah pekat

    "transition_1": (110, 90, 40),             # transisi emas
    "transition_2": (200, 170, 90),            # transisi cahaya

    # ─── PATH (marmar emas + retakan cahaya divine) ───
    "path_stone_1": (45, 30, 8),               # batu emas gelap
    "path_stone_2": (120, 85, 25),             # batu emas
    "path_stone_3": (200, 155, 60),            # batu aus
    "path_stone_4": (250, 220, 130),           # batu terang
    "path_moss": (95, 65, 15),                 # lumut debu emas
    "path_crack": (255, 252, 220),             # RETAKAN CAHAYA (gold_shine)

    # ─── RIVER (sungai cahaya divine) ───
    "river_deep": (155, 100, 20),              # divine_dark
    "river_mid": (240, 180, 55),               # divine_mid
    "river_light": (255, 230, 130),            # divine_light
    "river_glow": (255, 250, 200),             # divine_hot
    "river_foam": (255, 255, 255),             # divine_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon perak surgawi
    "has_dead_trees": False,
    "has_gravestones": False,
    "has_crystals_blue": True,     # kristal cahaya
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # reruntuhan katedral
    "has_bones": False,
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,       # batu altar berlumut
    "has_dark_bushes": True,       # semak surgawi
    "has_glow_flowers": True,      # bunga cahaya
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor cahaya divine

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = cahaya divine berkilau (seraph light) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (255, 240, 170), (255, 252, 220), (255, 255, 255)
    ],
    "particle_colors_dire": [
        (200, 150, 45), (250, 215, 105), (255, 230, 130)
    ],
    "particle_count": 60,           # cahaya seraph

    "fog_enabled": True,
    "fog_color": (240, 220, 170, 40),  # kabut emas surgawi
    "fog_count": 16,

    "ambient_tint": (60, 45, 15, 20),  # semburat emas divine
}

SOLARIS_THEME = {
    "name": "The Sunborn Herald",
    "boss_identity": "solareth",
    "boss_title": "The Sunborn Herald",

    # ─── TERRAIN (pasir matahari terbit + altar emas menyala) ───
    "radiant_grass_1": (55, 30, 5),            # gold_darkest
    "radiant_grass_2": (125, 80, 15),          # gold_dark
    "radiant_grass_3": (200, 155, 40),         # gold_mid
    "radiant_grass_4": (245, 210, 85),         # gold_light
    "radiant_grass_high": (255, 235, 140),     # gold_hot
    "radiant_moss": (180, 100, 15),            # lumut solar

    # Dire side: kerajaan matahari merah + jubah merah
    "dire_earth_1": (75, 15, 15),              # red_dark
    "dire_earth_2": (145, 30, 30),             # red_mid
    "dire_earth_3": (200, 65, 55),             # red_light
    "dire_earth_4": (240, 110, 80),            # red_glow
    "dire_ash": (90, 45, 20),                  # abu matahari
    "dire_burnt": (35, 10, 8),                 # ruang bawah pekat

    "transition_1": (120, 70, 18),             # transisi emas
    "transition_2": (220, 130, 45),            # transisi solar

    # ─── PATH (batu emas matahari + retakan sinar) ───
    "path_stone_1": (50, 28, 8),               # batu emas gelap
    "path_stone_2": (130, 82, 18),             # batu emas
    "path_stone_3": (205, 160, 50),            # batu aus
    "path_stone_4": (250, 215, 100),           # batu terang
    "path_moss": (95, 55, 15),                 # lumut debu
    "path_crack": (255, 255, 220),             # RETAKAN SINAR (solar_shine)

    # ─── RIVER (sungai cahaya matahari) ───
    "river_deep": (80, 40, 5),                 # solar_darkest
    "river_mid": (180, 100, 15),               # solar_dark
    "river_light": (240, 165, 40),             # solar_mid
    "river_glow": (255, 210, 90),              # solar_light
    "river_foam": (255, 255, 220),             # solar_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon palem kering
    "has_dead_trees": True,        # pohon mati
    "has_gravestones": True,       # reruntuhan altar
    "has_crystals_blue": False,
    "has_crystals_red": True,      # rubi matahari
    "has_ancient_ruins": True,     # kuil matahari kuno
    "has_bones": True,             # tulang belulang
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,       # batu altar berlumut
    "has_dark_bushes": True,       # semak kering
    "has_glow_flowers": True,      # bunga cahaya matahari
    "has_spike_traps": True,       # duri batu
    "has_torch_stones": True,      # obor sinar matahari

    # Custom decorations
    "has_cactus": True,            # kaktus gurun matahari
    "has_palm_trees": True,        # palem oasis
    "has_sand_dunes": True,        # bukit pasir
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan cahaya matahari (solar spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (255, 210, 90), (255, 240, 160), (255, 255, 220)
    ],
    "particle_colors_dire": [
        (200, 65, 55), (240, 165, 40), (255, 235, 140)
    ],
    "particle_count": 60,           # solar spark

    "fog_enabled": True,
    "fog_color": (240, 190, 90, 40),  # kabut keemasan fajar
    "fog_count": 16,

    "ambient_tint": (70, 45, 10, 20),  # semburat matahari terbit
}

ABYSSTIDE_THEME = {
    "name": "The Deepborn Oracle",
    "boss_identity": "okeanora",
    "boss_title": "The Deepborn Oracle",

    # ─── TERRAIN (dasar laut dalam teal + sisi altar kraken) ───
    "radiant_grass_1": (5, 25, 25),            # cloth_darkest
    "radiant_grass_2": (15, 55, 55),           # cloth_dark
    "radiant_grass_3": (30, 95, 90),           # cloth_mid
    "radiant_grass_4": (60, 145, 135),         # cloth_light
    "radiant_grass_high": (95, 245, 220),      # kraken_light
    "radiant_moss": (15, 100, 90),             # lumut kraken

    # Dire side: jurang abyssal + emas kuil tenggelam
    "dire_earth_1": (5, 30, 30),               # tent_darkest
    "dire_earth_2": (15, 65, 65),              # tent_dark
    "dire_earth_3": (40, 100, 100),            # tent_mid
    "dire_earth_4": (120, 85, 20),             # gold_dark
    "dire_ash": (55, 35, 5),                   # abu emas
    "dire_burnt": (3, 15, 18),                 # jurang pekat

    "transition_1": (20, 60, 58),              # transisi teal
    "transition_2": (60, 120, 105),            # transisi kraken

    # ─── PATH (batu karang + retakan sihir kraken) ───
    "path_stone_1": (6, 28, 28),               # batu karang gelap
    "path_stone_2": (20, 70, 68),              # batu karang
    "path_stone_3": (45, 110, 105),            # batu aus
    "path_stone_4": (85, 160, 150),            # batu terang
    "path_moss": (10, 55, 50),                 # lumut laut
    "path_crack": (170, 255, 240),             # RETAKAN KRAKEN (kraken_hot)

    # ─── RIVER (sungai sihir kraken hijau) ───
    "river_deep": (5, 45, 40),                 # kraken_darkest
    "river_mid": (15, 100, 90),                # kraken_dark
    "river_light": (30, 190, 170),             # kraken_mid
    "river_glow": (95, 245, 220),              # kraken_light
    "river_foam": (225, 255, 250),             # kraken_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # rumput laut raksasa
    "has_dead_trees": False,
    "has_gravestones": True,       # reruntuhan kuil tenggelam
    "has_crystals_blue": True,     # kristal laut
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # kota tenggelam kuno
    "has_bones": True,             # tulang kapal karam
    "has_mushrooms_dark": True,    # jamur bercahaya laut
    "has_rocks_mossy": True,       # karang berlumut
    "has_dark_bushes": True,       # semak karang
    "has_glow_flowers": True,      # plankton bercahaya
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor bioluminesensi

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = plankton bioluminesensi (kraken spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (95, 245, 220), (170, 255, 240), (225, 255, 250)
    ],
    "particle_colors_dire": [
        (15, 100, 90), (30, 190, 170), (60, 145, 135)
    ],
    "particle_count": 60,           # plankton kraken

    "fog_enabled": True,
    "fog_color": (15, 65, 65, 45),  # kabut abyssal hijau
    "fog_count": 18,

    "ambient_tint": (8, 35, 35, 20),  # semburat laut dalam
}

CRIMSONMATRIARCH_THEME = {
    "name": "The Crimson Matriarch",
    "boss_identity": "vaelmyrra",
    "boss_title": "The Crimson Matriarch",

    # ─── TERRAIN (obsidian gelap + darah merah, sisi tahta emas) ───
    "radiant_grass_1": (8, 5, 10),            # armor_darkest
    "radiant_grass_2": (25, 18, 25),          # armor_dark
    "radiant_grass_3": (55, 40, 50),          # armor_mid
    "radiant_grass_4": (100, 80, 90),         # armor_light
    "radiant_grass_high": (170, 150, 160),    # armor_shine
    "radiant_moss": (75, 10, 20),             # lumut darah

    # Dire side: kastil matriark obsidian + emas royal
    "dire_earth_1": (25, 3, 8),               # blood_darkest
    "dire_earth_2": (75, 10, 20),             # blood_dark
    "dire_earth_3": (155, 25, 40),            # blood_mid
    "dire_earth_4": (200, 155, 45),           # gold_mid
    "dire_ash": (45, 30, 5),                  # abu emas
    "dire_burnt": (5, 2, 4),                  # ruang bawah pekat

    "transition_1": (70, 20, 30),             # transisi darah
    "transition_2": (130, 90, 35),            # transisi emas

    # ─── PATH (batu obsidian + retakan darah menyala) ───
    "path_stone_1": (10, 6, 12),              # batu obsidian gelap
    "path_stone_2": (30, 20, 30),             # batu obsidian
    "path_stone_3": (70, 50, 60),             # batu aus
    "path_stone_4": (120, 95, 105),           # batu terang
    "path_moss": (50, 12, 18),                # lumut darah
    "path_crack": (255, 180, 170),            # RETAKAN DARAH (blood_shine)

    # ─── RIVER (sungai darah crimson) ───
    "river_deep": (25, 3, 8),                 # blood_darkest
    "river_mid": (75, 10, 20),                # blood_dark
    "river_light": (155, 25, 40),             # blood_mid
    "river_glow": (225, 55, 70),              # blood_light
    "river_foam": (255, 180, 170),            # blood_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon mati gotik
    "has_dead_trees": True,        # pohon kering
    "has_gravestones": True,       # makam matriark
    "has_crystals_blue": False,
    "has_crystals_red": True,      # kristal darah
    "has_ancient_ruins": True,     # istana obsidian kuno
    "has_bones": True,             # tulang belulang
    "has_mushrooms_dark": True,    # jamur gelap
    "has_rocks_mossy": True,       # batu berlumut darah
    "has_dark_bushes": True,       # semak gelap
    "has_glow_flowers": False,
    "has_spike_traps": True,       # duri besi obsidian
    "has_torch_stones": True,      # obor darah

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan darah crimson berkilau di istana matriark.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (225, 55, 70), (255, 100, 100), (255, 240, 180)
    ],
    "particle_colors_dire": [
        (75, 10, 20), (155, 25, 40), (200, 155, 45)
    ],
    "particle_count": 60,           # percikan darah

    "fog_enabled": True,
    "fog_color": (75, 10, 20, 45),  # kabut darah matriark
    "fog_count": 18,

    "ambient_tint": (40, 8, 12, 20),  # semburat merah darah
}

ASTRAL_THEME = {
    "name": "The Astral Sovereign",
    "boss_identity": "zarethyr",
    "boss_title": "The Astral Sovereign",

    # ─── TERRAIN (navy kosmik + cahaya biru astral, sisi emas royal) ───
    "radiant_grass_1": (5, 8, 25),            # robe_darkest
    "radiant_grass_2": (18, 25, 55),          # robe_dark
    "radiant_grass_3": (40, 55, 100),         # robe_mid
    "radiant_grass_4": (85, 105, 160),        # robe_light
    "radiant_grass_high": (150, 175, 220),    # robe_shine
    "radiant_moss": (15, 55, 145),            # lumut cosmic

    # Dire side: observatorium kosmik + perak bintang
    "dire_earth_1": (5, 15, 55),              # cosmic_darkest
    "dire_earth_2": (15, 55, 145),            # cosmic_dark
    "dire_earth_3": (55, 130, 235),           # cosmic_mid
    "dire_earth_4": (130, 200, 255),          # cosmic_light
    "dire_ash": (95, 105, 130),               # abu perak
    "dire_burnt": (3, 4, 12),                 # ruang angkasa pekat

    "transition_1": (35, 50, 100),            # transisi navy
    "transition_2": (95, 125, 190),           # transisi cosmic

    # ─── PATH (batu kosmik + retakan cahaya bintang) ───
    "path_stone_1": (8, 12, 32),              # batu kosmik gelap
    "path_stone_2": (25, 35, 70),             # batu kosmik
    "path_stone_3": (55, 70, 120),            # batu aus
    "path_stone_4": (100, 120, 175),          # batu terang
    "path_moss": (20, 30, 60),                # lumut debu bintang
    "path_crack": (240, 250, 255),            # RETAKAN BINTANG (cosmic_shine)

    # ─── RIVER (sungai cahaya kosmik) ───
    "river_deep": (5, 15, 55),                # cosmic_darkest
    "river_mid": (15, 55, 145),               # cosmic_dark
    "river_light": (55, 130, 235),            # cosmic_mid
    "river_glow": (130, 200, 255),            # cosmic_light
    "river_foam": (240, 250, 255),            # cosmic_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon perak kosmik
    "has_dead_trees": False,
    "has_gravestones": True,       # reruntuhan observatorium
    "has_crystals_blue": True,     # kristal cosmic
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # menara astral kuno
    "has_bones": False,
    "has_mushrooms_dark": True,    # jamur bercahaya bintang
    "has_rocks_mossy": True,       # batu berlumut kosmik
    "has_dark_bushes": True,       # semak malam
    "has_glow_flowers": True,      # bunga cahaya bintang
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor cahaya astral

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = bintang-bintang kosmik berkilau (star spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (130, 200, 255), (200, 235, 255), (240, 250, 255)
    ],
    "particle_colors_dire": [
        (15, 55, 145), (55, 130, 235), (245, 215, 115)
    ],
    "particle_count": 60,           # bintang kosmik

    "fog_enabled": True,
    "fog_color": (18, 25, 55, 45),  # kabut malam astral
    "fog_count": 16,

    "ambient_tint": (12, 20, 50, 20),  # semburat navy kosmik
}

SHADOWCHAIN_THEME = {
    "name": "The Forsaken Empress",
    "boss_identity": "nyrethzalv",
    "boss_title": "The Forsaken Empress of Shadow-Chains",

    # ─── TERRAIN (ungu gelap shadow + rantai, sisi magenta menyala) ───
    "radiant_grass_1": (15, 5, 25),            # robe_darkest
    "radiant_grass_2": (35, 15, 55),           # robe_dark
    "radiant_grass_3": (70, 35, 100),          # robe_mid
    "radiant_grass_4": (110, 65, 155),         # robe_light
    "radiant_grass_high": (170, 120, 210),     # robe_shine
    "radiant_moss": (65, 15, 90),              # lumut magic

    # Dire side: penjara bayangan + bulu hitam ratu
    "dire_earth_1": (5, 3, 10),                # feather_darkest
    "dire_earth_2": (20, 12, 35),              # feather_dark
    "dire_earth_3": (45, 30, 65),              # feather_mid
    "dire_earth_4": (145, 40, 180),            # magic_mid
    "dire_ash": (30, 12, 45),                  # abu bayangan
    "dire_burnt": (4, 2, 8),                   # ruang bawah pekat

    "transition_1": (40, 20, 70),              # transisi ungu
    "transition_2": (100, 45, 140),            # transisi magenta

    # ─── PATH (rantai besi gelap + retakan magic magenta) ───
    "path_stone_1": (10, 6, 18),               # rantai gelap
    "path_stone_2": (30, 18, 45),              # rantai
    "path_stone_3": (65, 40, 90),              # batu aus
    "path_stone_4": (115, 75, 155),            # batu terang
    "path_moss": (25, 10, 40),                 # lumut bayangan
    "path_crack": (255, 210, 255),             # RETAKAN MAGIC (magic_shine)

    # ─── RIVER (sungai sihir bayangan magenta) ───
    "river_deep": (20, 5, 30),                 # magic_darkest
    "river_mid": (65, 15, 90),                 # magic_dark
    "river_light": (145, 40, 180),             # magic_mid
    "river_glow": (210, 90, 235),              # magic_light
    "river_foam": (255, 210, 255),             # magic_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon mati bayangan
    "has_dead_trees": True,        # pohon kering
    "has_gravestones": True,       # makam permaisuri
    "has_crystals_blue": False,
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # penjara rantai kuno
    "has_bones": True,             # tulang belulang
    "has_mushrooms_dark": True,    # jamur gelap bercahaya
    "has_rocks_mossy": True,       # batu berlumut bayangan
    "has_dark_bushes": True,       # semak gelap
    "has_glow_flowers": True,      # bunga sihir magenta
    "has_spike_traps": True,       # duri besi rantai
    "has_torch_stones": True,      # obor api bayangan

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan sihir bayangan (shadow spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (210, 90, 235), (240, 140, 255), (255, 210, 255)
    ],
    "particle_colors_dire": [
        (35, 15, 55), (70, 35, 100), (170, 120, 210)
    ],
    "particle_count": 60,           # shadow spark

    "fog_enabled": True,
    "fog_color": (35, 15, 55, 45),  # kabut ungu bayangan
    "fog_count": 18,

    "ambient_tint": (30, 10, 45, 20),  # semburat ungu permaisuri
}

FROSTVEIL_THEME = {
    "name": "The Frost-Veiled Huntress",
    "boss_identity": "nyrellieth",
    "boss_title": "The Frost-Veiled Huntress",

    # ─── TERRAIN (tundra beku navy + es cyan, sisi kulit salju) ───
    "radiant_grass_1": (5, 8, 20),            # cape_darkest
    "radiant_grass_2": (15, 22, 45),          # cape_dark
    "radiant_grass_3": (35, 45, 80),          # cape_mid
    "radiant_grass_4": (65, 80, 120),         # cape_light
    "radiant_grass_high": (110, 125, 165),    # cape_edge
    "radiant_moss": (20, 70, 110),            # lumut es

    # Dire side: puncak beku + kulit salju perak
    "dire_earth_1": (5, 25, 45),              # ice_darkest
    "dire_earth_2": (20, 70, 110),            # ice_dark
    "dire_earth_3": (60, 160, 220),           # ice_mid
    "dire_earth_4": (140, 220, 255),          # ice_light
    "dire_ash": (75, 75, 95),                 # abu rambut perak
    "dire_burnt": (3, 4, 10),                 # jurang beku pekat

    "transition_1": (25, 45, 85),             # transisi navy
    "transition_2": (75, 125, 175),           # transisi es

    # ─── PATH (batu beku + retakan es menyala) ───
    "path_stone_1": (7, 10, 25),              # batu beku gelap
    "path_stone_2": (22, 32, 60),             # batu beku
    "path_stone_3": (50, 65, 105),            # batu aus
    "path_stone_4": (90, 110, 150),           # batu terang
    "path_moss": (15, 35, 60),                # lumut es
    "path_crack": (240, 255, 255),            # RETAKAN ES (ice_shine)

    # ─── RIVER (sungai es cyan) ───
    "river_deep": (5, 25, 45),                # ice_darkest
    "river_mid": (20, 70, 110),               # ice_dark
    "river_light": (60, 160, 220),            # ice_mid
    "river_glow": (140, 220, 255),            # ice_light
    "river_foam": (240, 255, 255),            # ice_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon beku gelap
    "has_dead_trees": True,        # pohon mati membeku
    "has_gravestones": True,       # monumen es
    "has_crystals_blue": True,     # kristal es
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # reruntuhan tundra
    "has_bones": True,             # tulang beku
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,       # batu berlumut es
    "has_dark_bushes": True,       # semak beku
    "has_glow_flowers": True,      # bunga es bercahaya
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor es bercahaya

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": True,      # kristal es besar
    "has_frozen_trees": True,      # pohon beku total
    "has_snow_drifts": True,       # tumpukan salju

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = kepingan salju/percikan es (frost spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (140, 220, 255), (200, 245, 255), (240, 255, 255)
    ],
    "particle_colors_dire": [
        (20, 70, 110), (60, 160, 220), (255, 255, 255)
    ],
    "particle_count": 60,           # frost spark

    "fog_enabled": True,
    "fog_color": (20, 70, 110, 40),  # kabut beku
    "fog_count": 16,

    "ambient_tint": (15, 30, 60, 20),  # semburat biru beku
}

WARSHADE_THEME = {
    "name": "The Shadow of War",
    "boss_identity": "nyxharr",
    "boss_title": "The Shadow of War",

    # ─── TERRAIN (medan perang black-teal, sisi roh cyan) ───
    "radiant_grass_1": (5, 10, 12),            # armor_darkest
    "radiant_grass_2": (15, 25, 30),           # armor_dark
    "radiant_grass_3": (35, 55, 65),           # armor_mid
    "radiant_grass_4": (70, 100, 115),         # armor_light
    "radiant_grass_high": (120, 155, 170),     # armor_edge
    "radiant_moss": (10, 65, 80),              # lumut spirit

    # Dire side: kawah perang + api roh cyan
    "dire_earth_1": (2, 20, 25),               # spirit_darkest
    "dire_earth_2": (10, 65, 80),              # spirit_dark
    "dire_earth_3": (30, 155, 180),            # spirit_mid
    "dire_earth_4": (90, 225, 245),            # spirit_light
    "dire_ash": (25, 25, 32),                  # abu metal
    "dire_burnt": (3, 5, 7),                   # medan perang pekat

    "transition_1": (25, 45, 55),              # transisi teal
    "transition_2": (55, 120, 140),            # transisi spirit

    # ─── PATH (batu perang + retakan roh cyan menyala) ───
    "path_stone_1": (6, 11, 14),               # batu perang gelap
    "path_stone_2": (20, 32, 38),              # batu perang
    "path_stone_3": (45, 65, 78),              # batu aus
    "path_stone_4": (80, 110, 125),            # batu terang
    "path_moss": (12, 30, 36),                 # lumut perang
    "path_crack": (230, 255, 255),             # RETAKAN ROH (spirit_shine)

    # ─── RIVER (sungai roh cyan) ───
    "river_deep": (2, 20, 25),                 # spirit_darkest
    "river_mid": (10, 65, 80),                 # spirit_dark
    "river_light": (30, 155, 180),             # spirit_mid
    "river_glow": (90, 225, 245),              # spirit_light
    "river_foam": (230, 255, 255),             # spirit_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon mati perang
    "has_dead_trees": True,        # pohon hangus
    "has_gravestones": True,       # monumen perang
    "has_crystals_blue": True,     # kristal roh
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # reruntuhan benteng perang
    "has_bones": True,             # tulang prajurit
    "has_mushrooms_dark": True,    # jamur gelap perang
    "has_rocks_mossy": True,       # batu berlumut
    "has_dark_bushes": True,       # semak kering perang
    "has_glow_flowers": False,
    "has_spike_traps": True,       # duri besi perang
    "has_torch_stones": True,      # obor api roh

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan roh perang (war spirit) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (90, 225, 245), (170, 250, 255), (230, 255, 255)
    ],
    "particle_colors_dire": [
        (10, 65, 80), (30, 155, 180), (70, 100, 115)
    ],
    "particle_count": 60,           # war spirit

    "fog_enabled": True,
    "fog_color": (10, 65, 80, 45),  # kabut roh perang
    "fog_count": 18,

    "ambient_tint": (8, 25, 30, 20),  # semburat teal perang
}

OUTLAW_THEME = {
    "name": "The Outlaw King",
    "boss_identity": "ravokkar",
    "boss_title": "The Outlaw King",

    # ─── TERRAIN (tanah frontier berdebu + sisi kota outlaw) ───
    "radiant_grass_1": (30, 22, 16),           # tanah frontier gelap
    "radiant_grass_2": (70, 50, 35),           # tanah frontier
    "radiant_grass_3": (120, 85, 55),          # tanah aus
    "radiant_grass_4": (170, 125, 85),         # tanah terang
    "radiant_grass_high": (215, 165, 120),     # skin_light
    "radiant_moss": (75, 45, 30),              # lumut kering

    # Dire side: kota outlaw + cape merah darah
    "dire_earth_1": (30, 8, 10),               # cape_darkest
    "dire_earth_2": (75, 15, 20),              # cape_dark
    "dire_earth_3": (150, 35, 40),             # cape_mid
    "dire_earth_4": (215, 75, 75),             # cape_light
    "dire_ash": (40, 32, 35),                  # abu coat
    "dire_burnt": (5, 5, 8),                   # ruang bawah pekat

    "transition_1": (80, 55, 40),              # transisi frontier
    "transition_2": (140, 85, 60),             # transisi debu

    # ─── PATH (kayu jati kering + retakan debu emas) ───
    "path_stone_1": (22, 16, 12),              # papan gelap
    "path_stone_2": (55, 40, 30),              # papan kayu
    "path_stone_3": (95, 70, 50),              # papan aus
    "path_stone_4": (150, 110, 65),            # leather_light
    "path_moss": (45, 30, 22),                 # lumut kering
    "path_crack": (245, 140, 140),             # RETAKAN DARAH (cape_shine)

    # ─── RIVER (sungai darah outlaw) ───
    "river_deep": (30, 8, 10),                 # cape_darkest
    "river_mid": (75, 15, 20),                 # cape_dark
    "river_light": (150, 35, 40),              # cape_mid
    "river_glow": (215, 75, 75),               # cape_light
    "river_foam": (245, 140, 140),             # cape_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon mati frontier
    "has_dead_trees": True,        # pohon kering
    "has_gravestones": True,       # makam outlaw
    "has_crystals_blue": False,
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # reruntuhan kota barat
    "has_bones": True,             # tulang sapi liar
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,       # batu berlumut kering
    "has_dark_bushes": True,       # semak liar
    "has_glow_flowers": False,
    "has_spike_traps": True,       # kaktus berduri
    "has_torch_stones": True,      # obor kota

    # Custom decorations
    "has_cactus": True,            # kaktus frontier
    "has_palm_trees": False,
    "has_sand_dunes": True,        # bukit pasir debu
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan api rokok/ember (outlaw spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (215, 75, 75), (245, 140, 140), (255, 210, 200)
    ],
    "particle_colors_dire": [
        (75, 15, 20), (150, 35, 40), (170, 125, 85)
    ],
    "particle_count": 60,           # outlaw spark

    "fog_enabled": True,
    "fog_color": (60, 45, 35, 45),  # kabut debu frontier
    "fog_count": 16,

    "ambient_tint": (50, 30, 25, 20),  # semburat debu senja
}

HEXBOUND_THEME = {
    "name": "The Hexbound Sovereign",
    "boss_identity": "malzeroth",
    "boss_title": "The Hexbound Sovereign",

    # ─── TERRAIN (tanah altar ungu iblis + sisi jubah merah) ───
    "radiant_grass_1": (25, 15, 40),           # skin_darkest
    "radiant_grass_2": (55, 35, 80),           # skin_dark
    "radiant_grass_3": (95, 65, 130),          # skin_mid
    "radiant_grass_4": (145, 110, 180),        # skin_light
    "radiant_grass_high": (200, 170, 225),     # skin_shine
    "radiant_moss": (110, 180, 50),            # lumut hex

    # Dire side: altar iblis + jubah merah darah
    "dire_earth_1": (35, 8, 12),               # cloak_darkest
    "dire_earth_2": (75, 18, 25),              # cloak_dark
    "dire_earth_3": (135, 35, 45),             # cloak_mid
    "dire_earth_4": (185, 60, 65),             # cloak_light
    "dire_ash": (85, 55, 15),                  # abu emas
    "dire_burnt": (10, 5, 8),                  # ruang bawah pekat

    "transition_1": (70, 40, 90),              # transisi ungu
    "transition_2": (130, 55, 90),             # transisi merah

    # ─── PATH (batu altar + retakan sihir hex hijau) ───
    "path_stone_1": (18, 10, 30),              # batu altar gelap
    "path_stone_2": (50, 30, 75),              # batu altar
    "path_stone_3": (90, 60, 125),             # batu aus
    "path_stone_4": (145, 105, 175),           # batu terang
    "path_moss": (45, 90, 20),                 # lumut hex
    "path_crack": (180, 240, 100),             # RETAKAN HEX (hex_light)

    # ─── RIVER (sungai sihir hex hijau) ───
    "river_deep": (15, 30, 8),                 # hex_darkest
    "river_mid": (45, 90, 20),                 # hex_dark
    "river_light": (110, 180, 50),             # hex_mid
    "river_glow": (180, 240, 100),             # hex_light
    "river_foam": (220, 255, 170),             # hex_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon mati altar
    "has_dead_trees": True,        # pohon kering
    "has_gravestones": True,       # makam terkutuk
    "has_crystals_blue": False,
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # reruntuhan altar iblis
    "has_bones": True,             # tulang korban
    "has_mushrooms_dark": True,    # jamur gelap
    "has_rocks_mossy": True,       # batu berlumut hex
    "has_dark_bushes": True,       # semak gelap
    "has_glow_flowers": True,      # bunga hex bercahaya
    "has_spike_traps": True,       # duri altar
    "has_torch_stones": True,      # obor api ungu

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan sihir hex (hex spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (140, 60, 200), (200, 130, 245), (180, 240, 100)
    ],
    "particle_colors_dire": [
        (55, 35, 80), (135, 35, 45), (255, 230, 100)
    ],
    "particle_count": 60,           # hex spark

    "fog_enabled": True,
    "fog_color": (55, 35, 80, 45),  # kabut ungu hex
    "fog_count": 18,

    "ambient_tint": (40, 20, 60, 20),  # semburat ungu iblis
}

VOIDBOUND_THEME = {
    "name": "The Voidbound Sovereign",
    "boss_identity": "zharakzuul",
    "boss_title": "The Voidbound Sovereign",

    # ─── TERRAIN (tanah altar void ungu + sisi jubah gelap) ───
    "radiant_grass_1": (15, 8, 30),            # robe_darkest
    "radiant_grass_2": (35, 20, 60),           # robe_dark
    "radiant_grass_3": (70, 40, 110),          # robe_mid
    "radiant_grass_4": (125, 85, 175),         # robe_light
    "radiant_grass_high": (185, 145, 225),     # robe_shine
    "radiant_moss": (85, 20, 145),             # lumut void

    # Dire side: kekosongan void magenta + rambut perak
    "dire_earth_1": (25, 5, 45),               # void_darkest
    "dire_earth_2": (85, 20, 145),             # void_dark
    "dire_earth_3": (175, 55, 235),            # void_mid
    "dire_earth_4": (225, 130, 255),           # void_light
    "dire_ash": (130, 125, 150),               # abu rambut perak
    "dire_burnt": (8, 4, 15),                  # kekosongan pekat

    "transition_1": (50, 28, 90),              # transisi ungu
    "transition_2": (120, 60, 175),            # transisi void

    # ─── PATH (batu altar + retakan void magenta) ───
    "path_stone_1": (12, 7, 25),               # batu void gelap
    "path_stone_2": (40, 22, 70),              # batu void
    "path_stone_3": (80, 45, 125),             # batu aus
    "path_stone_4": (135, 90, 180),            # batu terang
    "path_moss": (30, 12, 55),                 # lumut void
    "path_crack": (255, 240, 255),             # RETAKAN VOID (void_shine)

    # ─── RIVER (sungai sihir void magenta) ───
    "river_deep": (25, 5, 45),                 # void_darkest
    "river_mid": (85, 20, 145),                # void_dark
    "river_light": (175, 55, 235),             # void_mid
    "river_glow": (225, 130, 255),             # void_light
    "river_foam": (255, 240, 255),             # void_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon mati void
    "has_dead_trees": True,        # pohon kering
    "has_gravestones": True,       # monumen void
    "has_crystals_blue": False,
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # reruntuhan altar void
    "has_bones": True,             # tulang belulang
    "has_mushrooms_dark": True,    # jamur gelap bercahaya
    "has_rocks_mossy": True,       # batu berlumut void
    "has_dark_bushes": True,       # semak gelap
    "has_glow_flowers": True,      # bunga void bercahaya
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor api void

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan void (void spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (175, 55, 235), (225, 130, 255), (245, 200, 255)
    ],
    "particle_colors_dire": [
        (35, 20, 60), (85, 20, 145), (255, 240, 255)
    ],
    "particle_count": 60,           # void spark

    "fog_enabled": True,
    "fog_color": (35, 20, 60, 45),  # kabut void
    "fog_count": 18,

    "ambient_tint": (35, 15, 60, 20),  # semburat void
}

EARTHBORN_THEME = {
    "name": "The Earthborn",
    "boss_identity": "grondmauris",
    "boss_title": "The Earthborn",

    # ─── TERRAIN (gunung batu golem + tanah lumut hijau) ───
    "radiant_grass_1": (25, 22, 20),           # stone_darkest
    "radiant_grass_2": (58, 55, 50),           # stone_dark
    "radiant_grass_3": (105, 100, 92),         # stone_mid
    "radiant_grass_4": (165, 158, 145),        # stone_light
    "radiant_grass_high": (205, 198, 182),     # stone_edge
    "radiant_moss": (75, 120, 40),             # lumut moss

    # Dire side: dalam bumi + energi hijau golem
    "dire_earth_1": (10, 8, 6),                # crack_dark
    "dire_earth_2": (35, 30, 25),              # crack_mid
    "dire_earth_3": (45, 32, 20),              # earth_dark
    "dire_earth_4": (95, 72, 45),              # earth_mid
    "dire_ash": (55, 50, 42),                  # abu batu
    "dire_burnt": (5, 4, 3),                   # dalam bumi pekat

    "transition_1": (60, 55, 48),              # transisi batu
    "transition_2": (100, 90, 70),             # transisi tanah

    # ─── PATH (batu golem + retakan energi hijau) ───
    "path_stone_1": (20, 18, 16),              # batu gelap
    "path_stone_2": (55, 52, 46),              # batu
    "path_stone_3": (100, 95, 85),             # batu aus
    "path_stone_4": (160, 152, 138),           # batu terang
    "path_moss": (35, 65, 20),                 # lumut moss
    "path_crack": (240, 255, 220),             # RETAKAN ENERGI (energy_shine)

    # ─── RIVER (sungai energi hijau bumi) ───
    "river_deep": (5, 30, 10),                 # energy_darkest
    "river_mid": (20, 80, 30),                 # energy_dark
    "river_light": (60, 170, 70),              # energy_mid
    "river_glow": (140, 240, 130),             # energy_light
    "river_foam": (240, 255, 220),             # energy_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon purba
    "has_dead_trees": False,
    "has_gravestones": True,       # monumen batu
    "has_crystals_blue": False,
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # reruntuhan golem kuno
    "has_bones": False,
    "has_mushrooms_dark": True,    # jamur lumut
    "has_rocks_mossy": True,       # batu berlumut
    "has_dark_bushes": True,       # semak hijau
    "has_glow_flowers": True,      # bunga energi hijau
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor batu

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan energi hijau (earth spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (140, 240, 130), (200, 255, 180), (240, 255, 220)
    ],
    "particle_colors_dire": [
        (20, 80, 30), (60, 170, 70), (255, 225, 100)
    ],
    "particle_count": 60,           # earth spark

    "fog_enabled": True,
    "fog_color": (35, 65, 20, 40),  # kabut lumut
    "fog_count": 16,

    "ambient_tint": (35, 45, 20, 20),  # semburat hijau bumi
}

HEARTBANE_THEME = {
    "name": "The Heartbane",
    "boss_identity": "lyssarethys",
    "boss_title": "The Heartbane",

    # ─── TERRAIN (istana ungu gelap + sisi magic magenta) ───
    "radiant_grass_1": (30, 20, 40),           # skin_darkest
    "radiant_grass_2": (75, 55, 90),           # skin_dark
    "radiant_grass_3": (130, 105, 145),        # skin_mid
    "radiant_grass_4": (190, 165, 200),        # skin_light
    "radiant_grass_high": (230, 210, 235),     # skin_shine
    "radiant_moss": (110, 15, 70),             # lumut magic

    # Dire side: istana latex ungu + rambut magenta
    "dire_earth_1": (8, 4, 15),                # cloth_darkest
    "dire_earth_2": (28, 18, 40),              # cloth_dark
    "dire_earth_3": (55, 35, 75),              # cloth_mid
    "dire_earth_4": (100, 70, 130),            # cloth_light
    "dire_ash": (55, 8, 35),                   # abu rambut magenta
    "dire_burnt": (5, 2, 8),                   # ruang bawah pekat

    "transition_1": (60, 40, 90),              # transisi ungu
    "transition_2": (140, 60, 130),            # transisi magenta

    # ─── PATH (batu istana + retakan magic pink) ───
    "path_stone_1": (12, 6, 20),               # batu istana gelap
    "path_stone_2": (35, 22, 50),              # batu istana
    "path_stone_3": (70, 45, 95),              # batu aus
    "path_stone_4": (120, 85, 150),            # batu terang
    "path_moss": (45, 15, 60),                 # lumut magenta
    "path_crack": (255, 230, 245),             # RETAKAN MAGIC (magic_shine)

    # ─── RIVER (sungai sihir magenta) ───
    "river_deep": (40, 5, 25),                 # magic_darkest
    "river_mid": (110, 15, 70),                # magic_dark
    "river_light": (200, 40, 130),             # magic_mid
    "river_glow": (255, 100, 190),             # magic_light
    "river_foam": (255, 230, 245),             # magic_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon mati istana
    "has_dead_trees": True,        # pohon kering
    "has_gravestones": True,       # makam patah hati
    "has_crystals_blue": False,
    "has_crystals_red": True,      # kristal magenta
    "has_ancient_ruins": True,     # istana kuno ungu
    "has_bones": True,             # tulang belulang
    "has_mushrooms_dark": True,    # jamur gelap
    "has_rocks_mossy": True,       # batu berlumut ungu
    "has_dark_bushes": True,       # semak gelap
    "has_glow_flowers": True,      # bunga magenta bercahaya
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor api magenta

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan sihir magenta (heart spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (255, 100, 190), (255, 180, 230), (255, 230, 245)
    ],
    "particle_colors_dire": [
        (55, 35, 75), (110, 15, 70), (255, 170, 210)
    ],
    "particle_count": 60,           # heart spark

    "fog_enabled": True,
    "fog_color": (55, 35, 75, 45),  # kabut ungu istana
    "fog_count": 18,

    "ambient_tint": (45, 15, 45, 20),  # semburat magenta gelap
}

SUNFIST_THEME = {
    "name": "The Sunfist",
    "boss_identity": "kaerinya",
    "boss_title": "The Sunfist",

    # ─── TERRAIN (istana biru tua + sisi api emas menyala) ───
    "radiant_grass_1": (5, 10, 25),            # cloth_darkest
    "radiant_grass_2": (18, 30, 55),           # cloth_dark
    "radiant_grass_3": (40, 65, 105),          # cloth_mid
    "radiant_grass_4": (85, 120, 165),         # cloth_light
    "radiant_grass_high": (140, 175, 210),     # cloth_edge
    "radiant_moss": (100, 70, 15),             # lumut emas

    # Dire side: altar api emas + kulit hangat
    "dire_earth_1": (55, 25, 3),               # fire_darkest
    "dire_earth_2": (140, 65, 8),              # fire_dark
    "dire_earth_3": (200, 155, 40),            # gold_mid
    "dire_earth_4": (250, 220, 110),           # gold_light
    "dire_ash": (30, 15, 8),                   # abu rambut auburn
    "dire_burnt": (6, 4, 2),                   # ruang bawah pekat

    "transition_1": (45, 60, 95),              # transisi biru
    "transition_2": (140, 110, 55),            # transisi emas

    # ─── PATH (batu istana + retakan api emas) ───
    "path_stone_1": (10, 16, 32),              # batu istana gelap
    "path_stone_2": (28, 42, 70),              # batu istana
    "path_stone_3": (55, 75, 115),             # batu aus
    "path_stone_4": (95, 130, 170),            # batu terang
    "path_moss": (60, 40, 22),                 # lumut kulit
    "path_crack": (255, 245, 190),             # RETAKAN API (gold_shine)

    # ─── RIVER (sungai api emas) ───
    "river_deep": (55, 25, 3),                 # fire_darkest
    "river_mid": (140, 65, 8),                 # fire_dark
    "river_light": (200, 155, 40),             # gold_mid
    "river_glow": (250, 220, 110),             # gold_light
    "river_foam": (255, 245, 190),             # gold_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon istana
    "has_dead_trees": False,
    "has_gravestones": True,       # monumen istana
    "has_crystals_blue": True,     # kristal biru
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # reruntuhan istana
    "has_bones": False,
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,       # batu berlumut
    "has_dark_bushes": True,       # semak istana
    "has_glow_flowers": True,      # bunga api emas
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor api emas

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan api emas (sun spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (250, 220, 110), (255, 245, 190), (255, 230, 210)
    ],
    "particle_colors_dire": [
        (140, 65, 8), (200, 155, 40), (240, 190, 130)
    ],
    "particle_count": 60,           # sun spark

    "fog_enabled": True,
    "fog_color": (40, 65, 105, 40),  # kabut biru istana
    "fog_count": 16,

    "ambient_tint": (70, 45, 10, 20),  # semburat emas api
}

VOIDWING_THEME = {
    "name": "The Void Sovereign",
    "boss_identity": "xelnarath",
    "boss_title": "The Void Sovereign",

    # ─── TERRAIN (langit kekosongan ungu + sisi sayap void) ───
    "radiant_grass_1": (8, 3, 15),            # void_darkest
    "radiant_grass_2": (25, 10, 45),          # void_dark
    "radiant_grass_3": (55, 25, 90),          # void_mid
    "radiant_grass_4": (100, 55, 155),        # void_light
    "radiant_grass_high": (155, 95, 210),     # void_bright
    "radiant_moss": (90, 20, 110),            # lumut magenta

    # Dire side: jurang kekosongan + membran sayap ungu
    "dire_earth_1": (30, 15, 55),             # membrane_dark
    "dire_earth_2": (75, 40, 120),            # membrane_mid
    "dire_earth_3": (145, 90, 195),           # membrane_light
    "dire_earth_4": (170, 45, 190),           # magenta_mid
    "dire_ash": (20, 20, 45),                 # abu chitin
    "dire_burnt": (4, 2, 8),                  # kekosongan pekat

    "transition_1": (45, 22, 80),             # transisi ungu
    "transition_2": (110, 50, 150),           # transisi magenta

    # ─── PATH (batu chitin + retakan magenta panas) ───
    "path_stone_1": (10, 6, 25),              # batu chitin gelap
    "path_stone_2": (30, 25, 55),             # batu chitin
    "path_stone_3": (65, 55, 100),            # batu aus
    "path_stone_4": (115, 105, 165),          # batu terang
    "path_moss": (55, 25, 90),                # lumut void
    "path_crack": (255, 220, 255),            # RETAKAN MAGENTA (magenta_shine)

    # ─── RIVER (sungai sihir magenta) ───
    "river_deep": (35, 5, 40),                # magenta_darkest
    "river_mid": (90, 20, 110),               # magenta_dark
    "river_light": (170, 45, 190),            # magenta_mid
    "river_glow": (230, 100, 240),            # magenta_light
    "river_foam": (255, 220, 255),            # magenta_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon mati void
    "has_dead_trees": True,        # pohon kering
    "has_gravestones": True,       # monumen kekosongan
    "has_crystals_blue": False,
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # reruntuhan kuil void
    "has_bones": True,             # tulang belulang
    "has_mushrooms_dark": True,    # jamur gelap bercahaya
    "has_rocks_mossy": True,       # batu berlumut void
    "has_dark_bushes": True,       # semak gelap
    "has_glow_flowers": True,      # bunga magenta bercahaya
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor api magenta

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan void magenta (void spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (230, 100, 240), (255, 160, 255), (255, 220, 255)
    ],
    "particle_colors_dire": [
        (25, 10, 45), (55, 25, 90), (255, 240, 180)
    ],
    "particle_count": 60,           # void spark

    "fog_enabled": True,
    "fog_color": (25, 10, 45, 45),  # kabut kekosongan
    "fog_count": 18,

    "ambient_tint": (35, 12, 55, 20),  # semburat ungu void
}

CRIMSONDEVOURER_THEME = {
    "name": "The Crimson Devourer",
    "boss_identity": "kyrenzai",
    "boss_title": "The Crimson Devourer",

    # ─── TERRAIN (distrik gelap hitam + sisi tentakel kagune) ───
    "radiant_grass_1": (5, 3, 5),            # cloth_darkest
    "radiant_grass_2": (18, 12, 18),         # cloth_dark
    "radiant_grass_3": (40, 30, 35),         # cloth_mid
    "radiant_grass_4": (75, 60, 65),         # cloth_light
    "radiant_grass_high": (130, 115, 120),   # cloth_shine
    "radiant_moss": (80, 5, 15),             # lumut kagune

    # Dire side: gang gelap + darah kagune menyala
    "dire_earth_1": (25, 0, 5),              # kagune_darkest
    "dire_earth_2": (80, 5, 15),             # kagune_dark
    "dire_earth_3": (170, 20, 35),           # kagune_mid
    "dire_earth_4": (230, 55, 65),           # kagune_light
    "dire_ash": (8, 5, 8),                   # abu mask
    "dire_burnt": (3, 2, 3),                 # gang pekat

    "transition_1": (45, 30, 38),            # transisi gelap
    "transition_2": (120, 30, 42),           # transisi kagune

    # ─── PATH (batu kota + retakan kagune menyala) ───
    "path_stone_1": (8, 5, 8),               # batu kota gelap
    "path_stone_2": (28, 20, 26),            # batu kota
    "path_stone_3": (55, 45, 52),            # batu aus
    "path_stone_4": (95, 80, 88),            # batu terang
    "path_moss": (50, 15, 22),               # lumut darah
    "path_crack": (255, 200, 180),           # RETAKAN KAGUNE (kagune_shine)

    # ─── RIVER (sungai darah kagune) ───
    "river_deep": (25, 0, 5),                # kagune_darkest
    "river_mid": (80, 5, 15),                # kagune_dark
    "river_light": (170, 20, 35),            # kagune_mid
    "river_glow": (230, 55, 65),             # kagune_light
    "river_foam": (255, 200, 180),           # kagune_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon mati kota
    "has_dead_trees": True,        # pohon kering
    "has_gravestones": True,       # makam kota
    "has_crystals_blue": False,
    "has_crystals_red": True,      # kristal darah
    "has_ancient_ruins": True,     # reruntuhan distrik
    "has_bones": True,             # tulang belulang
    "has_mushrooms_dark": True,    # jamur gelap
    "has_rocks_mossy": True,       # batu berlumut darah
    "has_dark_bushes": True,       # semak gelap
    "has_glow_flowers": True,      # bunga darah bercahaya
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor api merah

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan darah kagune (blood spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (230, 55, 65), (255, 110, 100), (255, 200, 180)
    ],
    "particle_colors_dire": [
        (80, 5, 15), (170, 20, 35), (255, 245, 240)
    ],
    "particle_count": 60,           # blood spark

    "fog_enabled": True,
    "fog_color": (40, 10, 16, 45),  # kabut darah kota
    "fog_count": 18,

    "ambient_tint": (45, 8, 12, 20),  # semburat merah kagune
}

ELEMENTWEAVE_THEME = {
    "name": "The Elemental Weaver",
    "boss_identity": "xaelmoran",
    "boss_title": "The Elemental Weaver",

    # ─── TERRAIN (jubah ungu-emas + sisi sihir Quas biru) ───
    "radiant_grass_1": (15, 8, 25),            # robe_darkest
    "radiant_grass_2": (40, 22, 60),           # robe_dark
    "radiant_grass_3": (75, 45, 105),          # robe_mid
    "radiant_grass_4": (120, 85, 160),         # robe_light
    "radiant_grass_high": (170, 130, 210),     # robe_edge
    "radiant_moss": (80, 20, 130),             # lumut wex

    # Dire side: altar elemen + api Exort
    "dire_earth_1": (5, 15, 40),               # cold_darkest
    "dire_earth_2": (20, 60, 130),             # cold_dark
    "dire_earth_3": (60, 140, 230),            # cold_mid
    "dire_earth_4": (140, 210, 255),           # cold_light
    "dire_ash": (85, 55, 15),                  # abu emas
    "dire_burnt": (8, 5, 15),                  # altar pekat

    "transition_1": (55, 35, 85),              # transisi ungu
    "transition_2": (90, 90, 140),             # transisi elemen

    # ─── PATH (batu altar + retakan sihir elemen) ───
    "path_stone_1": (12, 7, 22),               # batu altar gelap
    "path_stone_2": (40, 24, 60),              # batu altar
    "path_stone_3": (75, 48, 105),             # batu aus
    "path_stone_4": (125, 90, 160),            # batu terang
    "path_moss": (25, 5, 40),                  # lumut magic
    "path_crack": (255, 240, 170),             # RETAKAN EMAS (gold_shine)

    # ─── RIVER (sungai sihir wex magenta) ───
    "river_deep": (25, 5, 40),                 # magic_darkest
    "river_mid": (80, 20, 130),                # magic_dark
    "river_light": (170, 60, 220),             # magic_mid
    "river_glow": (220, 130, 255),             # magic_light
    "river_foam": (255, 230, 255),             # magic_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon altar
    "has_dead_trees": False,
    "has_gravestones": True,       # monumen elemen
    "has_crystals_blue": True,     # kristal quas biru
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # reruntuhan kuil elemen
    "has_bones": False,
    "has_mushrooms_dark": True,    # jamur bercahaya
    "has_rocks_mossy": True,       # batu berlumut
    "has_dark_bushes": True,       # semak altar
    "has_glow_flowers": True,      # bunga elemen bercahaya
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor tiga elemen

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan tiga elemen (element spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (60, 140, 230), (170, 60, 220), (255, 240, 170)
    ],
    "particle_colors_dire": [
        (20, 60, 130), (80, 20, 130), (240, 200, 90)
    ],
    "particle_count": 60,           # element spark

    "fog_enabled": True,
    "fog_color": (40, 22, 60, 45),  # kabut ungu altar
    "fog_count": 18,

    "ambient_tint": (40, 25, 60, 20),  # semburat ungu-emas
}

TEMPEST_THEME = {
    "name": "The Tempest Weaver",
    "boss_identity": "thalryndel",
    "boss_title": "The Tempest Weaver",

    # ─── TERRAIN (langit badai elemental biru + sisi robe biru tua) ───
    "radiant_grass_1": (5, 10, 30),            # robe_darkest
    "radiant_grass_2": (15, 30, 75),           # robe_dark
    "radiant_grass_3": (40, 65, 130),          # robe_mid
    "radiant_grass_4": (85, 120, 190),         # robe_light
    "radiant_grass_high": (140, 175, 230),     # robe_edge
    "radiant_moss": (20, 60, 160),             # lumut light

    # Dire side: badai petir + topi petir biru
    "dire_earth_1": (5, 15, 50),               # light_darkest
    "dire_earth_2": (20, 60, 160),             # light_dark
    "dire_earth_3": (60, 140, 240),            # light_mid
    "dire_earth_4": (170, 220, 245),           # skin_light
    "dire_ash": (35, 25, 5),                   # abu emas
    "dire_burnt": (3, 6, 18),                  # badai pekat

    "transition_1": (30, 55, 110),             # transisi biru
    "transition_2": (60, 105, 170),            # transisi petir

    # ─── PATH (batu badai + retakan petir menyala) ───
    "path_stone_1": (8, 14, 38),               # batu badai gelap
    "path_stone_2": (25, 42, 90),              # batu badai
    "path_stone_3": (50, 78, 145),             # batu aus
    "path_stone_4": (95, 130, 195),            # batu terang
    "path_moss": (18, 40, 100),                # lumut petir
    "path_crack": (255, 245, 180),             # RETAKAN PETIR (gold_shine)

    # ─── RIVER (sungai petir biru) ───
    "river_deep": (5, 15, 50),                 # light_darkest
    "river_mid": (20, 60, 160),                # light_dark
    "river_light": (60, 140, 240),             # light_mid
    "river_glow": (140, 210, 255),             # cold_light
    "river_foam": (240, 255, 255),             # cold_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon tertiup badai
    "has_dead_trees": True,        # pohon hangus petir
    "has_gravestones": True,       # monumen badai
    "has_crystals_blue": True,     # kristal petir
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # reruntuhan kuil badai
    "has_bones": False,
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,       # batu berlumut badai
    "has_dark_bushes": True,       # semak tertiup angin
    "has_glow_flowers": True,      # bunga petir bercahaya
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor petir

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan petir (storm spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (60, 140, 240), (140, 210, 255), (240, 255, 255)
    ],
    "particle_colors_dire": [
        (20, 60, 160), (85, 120, 190), (255, 245, 180)
    ],
    "particle_count": 60,           # storm spark

    "fog_enabled": True,
    "fog_color": (15, 30, 75, 45),  # kabut badai
    "fog_count": 18,

    "ambient_tint": (20, 35, 80, 20),  # semburat biru badai
}

SAWMILL_THEME = {
    "name": "The Sawmill Warlord",
    "boss_identity": "grimkor",
    "boss_title": "The Sawmill Warlord",

    # ─── TERRAIN (tanah hutan penggergajian + sisi besi mesin) ───
    "radiant_grass_1": (25, 40, 20),           # skin_darkest
    "radiant_grass_2": (55, 90, 45),           # skin_dark
    "radiant_grass_3": (110, 155, 80),         # skin_mid
    "radiant_grass_4": (170, 210, 130),        # skin_light
    "radiant_grass_high": (200, 195, 180),     # iron_edge
    "radiant_moss": (60, 68, 85),              # lumut blade

    # Dire side: mesin penggergajian + api tungku
    "dire_earth_1": (18, 15, 12),              # iron_darkest
    "dire_earth_2": (45, 40, 35),              # iron_dark
    "dire_earth_3": (95, 50, 20),              # copper_dark
    "dire_earth_4": (175, 105, 40),            # copper_mid
    "dire_ash": (35, 32, 30),                  # abu smoke
    "dire_burnt": (30, 8, 2),                  # tungku pekat

    "transition_1": (55, 65, 45),              # transisi hutan
    "transition_2": (110, 90, 50),             # transisi besi

    # ─── PATH (papan kayu gergajian + retakan api) ───
    "path_stone_1": (20, 18, 14),              # papan gelap
    "path_stone_2": (55, 48, 40),              # papan kayu
    "path_stone_3": (100, 92, 80),             # papan aus
    "path_stone_4": (155, 148, 135),           # papan terang
    "path_moss": (35, 30, 25),                 # lumut kayu
    "path_crack": (255, 250, 200),             # RETAKAN API (fire_shine)

    # ─── RIVER (sungai api tungku) ───
    "river_deep": (30, 8, 2),                  # fire_darkest
    "river_mid": (110, 30, 8),                 # fire_dark
    "river_light": (220, 90, 20),              # fire_mid
    "river_glow": (255, 165, 50),              # fire_light
    "river_foam": (255, 250, 200),             # fire_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon hutan gergajian
    "has_dead_trees": True,        # tunggul pohon
    "has_gravestones": True,       # makam pekerja
    "has_crystals_blue": False,
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # reruntuhan penggergajian
    "has_bones": True,             # tulang belulang
    "has_mushrooms_dark": True,    # jamur hutan
    "has_rocks_mossy": True,       # batu berlumut
    "has_dark_bushes": True,       # semak hutan
    "has_glow_flowers": False,
    "has_spike_traps": True,       # duri kayu
    "has_torch_stones": True,      # obor api mesin

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan api tungku (sawmill spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (255, 165, 50), (255, 220, 120), (255, 250, 200)
    ],
    "particle_colors_dire": [
        (110, 30, 8), (220, 90, 20), (100, 95, 90)
    ],
    "particle_count": 60,           # sawmill spark

    "fog_enabled": True,
    "fog_color": (55, 50, 45, 45),  # kabut asap mesin
    "fog_count": 18,

    "ambient_tint": (60, 40, 15, 20),  # semburat api tungku
}

CROWEYE_THEME = {
    "name": "The Crow-Eyed",
    "boss_identity": "kaineroth",
    "boss_title": "The Crow-Eyed",

    # ─── TERRAIN (desa ninja gelap + sisi awan merah) ───
    "radiant_grass_1": (5, 3, 8),            # cloak_darkest
    "radiant_grass_2": (18, 12, 22),         # cloak_dark
    "radiant_grass_3": (35, 25, 42),         # cloak_mid
    "radiant_grass_4": (60, 45, 70),         # cloak_light
    "radiant_grass_high": (95, 75, 110),     # cloak_edge
    "radiant_moss": (85, 15, 20),            # lumut cloud

    # Dire side: atap desa + awan merah menyala
    "dire_earth_1": (30, 6, 8),              # cloud_dark
    "dire_earth_2": (85, 15, 20),            # cloud_mid
    "dire_earth_3": (170, 35, 45),           # cloud_light
    "dire_earth_4": (230, 70, 80),           # cloud_edge
    "dire_ash": (20, 15, 25),                # abu rambut
    "dire_burnt": (3, 2, 5),                 # gang pekat

    "transition_1": (40, 28, 50),            # transisi gelap
    "transition_2": (110, 40, 55),           # transisi merah

    # ─── PATH (batu desa + retakan mata merah) ───
    "path_stone_1": (8, 5, 12),              # batu desa gelap
    "path_stone_2": (28, 18, 35),            # batu desa
    "path_stone_3": (55, 38, 65),            # batu aus
    "path_stone_4": (95, 70, 105),           # batu terang
    "path_moss": (50, 20, 30),               # lumut merah
    "path_crack": (255, 130, 130),           # RETAKAN MATA (cloud_edge)

    # ─── RIVER (sungai mata sharingan merah) ───
    "river_deep": (30, 6, 8),                # eye_socket
    "river_mid": (85, 15, 20),               # cloud_dark
    "river_light": (170, 35, 45),            # cloud_mid
    "river_glow": (230, 70, 80),             # cloud_light
    "river_foam": (255, 150, 150),           # cloud_edge

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon desa
    "has_dead_trees": True,        # pohon kering
    "has_gravestones": True,       # makam ninja
    "has_crystals_blue": False,
    "has_crystals_red": True,      # kristal mata merah
    "has_ancient_ruins": True,     # reruntuhan desa ninja
    "has_bones": True,             # tulang belulang
    "has_mushrooms_dark": True,    # jamur gelap
    "has_rocks_mossy": True,       # batu berlumut
    "has_dark_bushes": True,       # semak gelap
    "has_glow_flowers": True,      # bunga mata merah
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor api merah

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan mata sharingan (crow spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (230, 70, 80), (255, 130, 130), (255, 220, 220)
    ],
    "particle_colors_dire": [
        (85, 15, 20), (170, 35, 45), (210, 210, 220)
    ],
    "particle_count": 60,           # crow spark

    "fog_enabled": True,
    "fog_color": (25, 15, 32, 45),  # kabut desa ninja
    "fog_count": 18,

    "ambient_tint": (45, 10, 16, 20),  # semburat mata merah
}

CRYSTALSTORM_THEME = {
    "name": "The Stormherald",
    "boss_identity": "zyvareth",
    "boss_title": "The Stormherald",

    # ─── TERRAIN (langit badai teal + sisi tanduk kristal ungu) ───
    "radiant_grass_1": (5, 30, 40),            # body_darkest
    "radiant_grass_2": (15, 75, 90),           # body_dark
    "radiant_grass_3": (40, 145, 165),         # body_mid
    "radiant_grass_4": (100, 215, 225),        # body_light
    "radiant_grass_high": (170, 245, 250),     # body_edge
    "radiant_moss": (75, 25, 130),             # lumut crystal

    # Dire side: badai kristal + petir ungu
    "dire_earth_1": (25, 5, 55),               # crystal_darkest
    "dire_earth_2": (75, 25, 130),             # crystal_dark
    "dire_earth_3": (155, 60, 220),            # crystal_mid
    "dire_earth_4": (215, 130, 250),           # crystal_light
    "dire_ash": (95, 60, 15),                  # abu emas
    "dire_burnt": (4, 10, 20),                 # badai pekat

    "transition_1": (30, 90, 105),             # transisi teal
    "transition_2": (95, 105, 190),            # transisi kristal

    # ─── PATH (batu badai + retakan kristal ungu) ───
    "path_stone_1": (8, 18, 25),               # batu badai gelap
    "path_stone_2": (25, 55, 70),              # batu badai
    "path_stone_3": (55, 110, 130),            # batu aus
    "path_stone_4": (100, 175, 190),           # batu terang
    "path_moss": (45, 20, 75),                 # lumut kristal
    "path_crack": (255, 240, 255),             # RETAKAN KRISTAL (crystal_shine)

    # ─── RIVER (sungai petir kristal) ───
    "river_deep": (25, 5, 55),                 # crystal_darkest
    "river_mid": (75, 25, 130),                # crystal_dark
    "river_light": (155, 60, 220),             # crystal_mid
    "river_glow": (215, 130, 250),             # crystal_light
    "river_foam": (255, 240, 255),             # crystal_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon tertiup badai
    "has_dead_trees": True,        # pohon hangus petir
    "has_gravestones": True,       # monumen kristal
    "has_crystals_blue": True,     # kristal teal
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # reruntuhan kuil badai
    "has_bones": False,
    "has_mushrooms_dark": True,    # jamur bercahaya
    "has_rocks_mossy": True,       # batu berlumut teal
    "has_dark_bushes": True,       # semak tertiup angin
    "has_glow_flowers": True,      # bunga kristal bercahaya
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor petir kristal

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan kristal petir (storm crystal) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (215, 130, 250), (245, 195, 255), (255, 240, 255)
    ],
    "particle_colors_dire": [
        (75, 25, 130), (155, 60, 220), (100, 215, 225)
    ],
    "particle_count": 60,           # storm crystal

    "fog_enabled": True,
    "fog_color": (15, 75, 90, 45),  # kabut badai teal
    "fog_count": 18,

    "ambient_tint": (25, 40, 75, 20),  # semburat teal-ungu
}

ETERNALWARLORD_THEME = {
    "name": "The Eternal Warlord",
    "boss_identity": "kagetsuka",
    "boss_title": "The Eternal Warlord",

    # ─── TERRAIN (medan perang samurai + sisi armor crimson) ───
    "radiant_grass_1": (25, 10, 15),           # armor_darkest
    "radiant_grass_2": (70, 20, 30),           # armor_dark
    "radiant_grass_3": (130, 40, 50),          # armor_mid
    "radiant_grass_4": (185, 75, 85),          # armor_light
    "radiant_grass_high": (240, 130, 130),     # armor_shine
    "radiant_moss": (110, 10, 20),             # lumut sharingan

    # Dire side: api sharingan + rambut hitam
    "dire_earth_1": (35, 0, 5),                # sharingan_darkest
    "dire_earth_2": (110, 10, 20),             # sharingan_dark
    "dire_earth_3": (200, 30, 40),             # sharingan_mid
    "dire_earth_4": (255, 90, 90),             # sharingan_light
    "dire_ash": (20, 18, 30),                  # abu rambut
    "dire_burnt": (15, 5, 8),                  # medan perang pekat

    "transition_1": (65, 30, 40),              # transisi crimson
    "transition_2": (130, 55, 60),             # transisi api

    # ─── PATH (batu medan perang + retakan sharingan) ───
    "path_stone_1": (16, 8, 12),               # batu perang gelap
    "path_stone_2": (45, 18, 25),              # batu perang
    "path_stone_3": (85, 40, 50),              # batu aus
    "path_stone_4": (135, 75, 85),             # batu terang
    "path_moss": (60, 15, 22),                 # lumut darah
    "path_crack": (255, 180, 160),             # RETAKAN SHARINGAN (sharingan_glow)

    # ─── RIVER (sungai sharingan merah) ───
    "river_deep": (35, 0, 5),                  # sharingan_darkest
    "river_mid": (110, 10, 20),                # sharingan_dark
    "river_light": (200, 30, 40),              # sharingan_mid
    "river_glow": (255, 90, 90),               # sharingan_light
    "river_foam": (255, 180, 160),             # sharingan_glow

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon mati perang
    "has_dead_trees": True,        # pohon hangus
    "has_gravestones": True,       # makam samurai
    "has_crystals_blue": False,
    "has_crystals_red": True,      # kristal sharingan
    "has_ancient_ruins": True,     # reruntuhan kastil samurai
    "has_bones": True,             # tulang prajurit
    "has_mushrooms_dark": True,    # jamur gelap
    "has_rocks_mossy": True,       # batu berlumut
    "has_dark_bushes": True,       # semak perang
    "has_glow_flowers": True,      # bunga api merah
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor api sharingan

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan sharingan api (warlord spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (200, 30, 40), (255, 90, 90), (255, 230, 140)
    ],
    "particle_colors_dire": [
        (110, 10, 20), (130, 45, 10), (95, 90, 115)
    ],
    "particle_count": 60,           # warlord spark

    "fog_enabled": True,
    "fog_color": (45, 12, 18, 45),  # kabut medan perang
    "fog_count": 18,

    "ambient_tint": (55, 12, 16, 20),  # semburat sharingan merah
}

EXPLOSIVEART_THEME = {
    "name": "The Explosive Artist",
    "boss_identity": "deidara",
    "boss_title": "The Explosive Artist",

    # ─── TERRAIN (tanah ledakan cokelat + sisi jubah Akatsuki hitam) ───
    "radiant_grass_1": (5, 5, 8),            # cloak_darkest
    "radiant_grass_2": (18, 18, 24),         # cloak_dark
    "radiant_grass_3": (40, 40, 50),         # cloak_mid
    "radiant_grass_4": (70, 70, 85),         # cloak_light
    "radiant_grass_high": (100, 100, 120),   # cloak_edge
    "radiant_moss": (130, 15, 20),           # lumut cloud

    # Dire side: kawah ledakan + awan merah menyala
    "dire_earth_1": (60, 5, 8),              # cloud_darkest
    "dire_earth_2": (130, 15, 20),           # cloud_dark
    "dire_earth_3": (200, 30, 35),           # cloud_mid
    "dire_earth_4": (250, 70, 60),           # cloud_light
    "dire_ash": (90, 60, 15),                # abu rambut pirang
    "dire_burnt": (10, 6, 10),               # kawah pekat

    "transition_1": (45, 35, 50),            # transisi gelap
    "transition_2": (130, 45, 40),           # transisi merah

    # ─── PATH (batu kawah + retakan ledakan merah) ───
    "path_stone_1": (10, 8, 12),             # batu kawah gelap
    "path_stone_2": (35, 28, 38),            # batu kawah
    "path_stone_3": (70, 60, 75),            # batu aus
    "path_stone_4": (115, 100, 120),         # batu terang
    "path_moss": (55, 12, 16),               # lumut ledakan
    "path_crack": (255, 150, 130),           # RETAKAN LEDAKAN (cloud_shine)

    # ─── RIVER (sungai awan merah) ───
    "river_deep": (60, 5, 8),                # cloud_darkest
    "river_mid": (130, 15, 20),              # cloud_dark
    "river_light": (200, 30, 35),            # cloud_mid
    "river_glow": (250, 70, 60),             # cloud_light
    "river_foam": (255, 150, 130),           # cloud_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon hangus ledakan
    "has_dead_trees": True,        # pohon kering
    "has_gravestones": True,       # makam korban ledakan
    "has_crystals_blue": False,
    "has_crystals_red": True,      # kristal ledakan
    "has_ancient_ruins": True,     # reruntuhan medan perang
    "has_bones": True,             # tulang belulang
    "has_mushrooms_dark": True,    # jamur gelap
    "has_rocks_mossy": True,       # batu berlumut
    "has_dark_bushes": True,       # semak hangus
    "has_glow_flowers": False,
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor api ledakan

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": True,        # bukit pasir tanah liat
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan ledakan (art spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (250, 70, 60), (255, 150, 130), (255, 245, 170)
    ],
    "particle_colors_dire": [
        (130, 15, 20), (200, 30, 35), (100, 100, 120)
    ],
    "particle_count": 60,           # art spark

    "fog_enabled": True,
    "fog_color": (40, 25, 30, 45),  # kabut asap ledakan
    "fog_count": 18,

    "ambient_tint": (55, 15, 15, 20),  # semburat awan merah
}

SANDSHADOW_THEME = {
    "name": "The Sand Shadow",
    "boss_identity": "sunakage",
    "boss_title": "The Sand Shadow",

    # ─── TERRAIN (gurun pasir merah + sisi jubah marun) ───
    "radiant_grass_1": (25, 8, 10),            # robe_darkest
    "radiant_grass_2": (65, 18, 22),           # robe_dark
    "radiant_grass_3": (110, 30, 35),          # robe_mid
    "radiant_grass_4": (160, 55, 60),          # robe_light
    "radiant_grass_high": (200, 90, 90),       # robe_shine
    "radiant_moss": (170, 30, 20),             # lumut tattoo

    # Dire side: badai pasir + rambut rust merah
    "dire_earth_1": (55, 15, 8),               # hair_darkest
    "dire_earth_2": (120, 35, 20),             # hair_dark
    "dire_earth_3": (180, 60, 30),             # hair_mid
    "dire_earth_4": (220, 100, 55),            # hair_light
    "dire_ash": (90, 15, 10),                  # abu tattoo
    "dire_burnt": (12, 5, 7),                  # gurun pekat

    "transition_1": (90, 30, 32),              # transisi marun
    "transition_2": (150, 55, 40),             # transisi pasir

    # ─── PATH (batu gurun + retakan rune merah) ───
    "path_stone_1": (22, 10, 12),              # batu gurun gelap
    "path_stone_2": (60, 25, 28),              # batu gurun
    "path_stone_3": (105, 45, 48),             # batu aus
    "path_stone_4": (155, 80, 80),             # batu terang
    "path_moss": (70, 18, 16),                 # lumut rune
    "path_crack": (250, 150, 100),             # RETAKAN RUNE (hair_shine)

    # ─── RIVER (sungai pasir merah) ───
    "river_deep": (55, 15, 8),                 # hair_darkest
    "river_mid": (120, 35, 20),                # hair_dark
    "river_light": (180, 60, 30),              # hair_mid
    "river_glow": (220, 100, 55),              # hair_light
    "river_foam": (250, 150, 100),             # hair_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon kering gurun
    "has_dead_trees": True,        # pohon mati
    "has_gravestones": True,       # makam gurun
    "has_crystals_blue": False,
    "has_crystals_red": True,      # kristal pasir merah
    "has_ancient_ruins": True,     # reruntuhan kuil pasir
    "has_bones": True,             # tulang gurun
    "has_mushrooms_dark": False,
    "has_rocks_mossy": True,       # batu berlumut
    "has_dark_bushes": True,       # semak kering
    "has_glow_flowers": False,
    "has_spike_traps": True,       # duri gurun
    "has_torch_stones": True,      # obor pasir merah

    # Custom decorations
    "has_cactus": True,            # kaktus gurun
    "has_palm_trees": True,        # palem oasis
    "has_sand_dunes": True,        # bukit pasir
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan pasir merah (sand spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (220, 100, 55), (250, 150, 100), (255, 248, 238)
    ],
    "particle_colors_dire": [
        (120, 35, 20), (180, 60, 30), (230, 70, 45)
    ],
    "particle_count": 60,           # sand spark

    "fog_enabled": True,
    "fog_color": (120, 50, 35, 45),  # kabut debu gurun
    "fog_count": 16,

    "ambient_tint": (75, 30, 20, 20),  # semburat pasir merah
}

EMBERWEAVER_THEME = {
    "name": "The Emberweaver",
    "boss_identity": "pyraena",
    "boss_title": "The Emberweaver",

    # ─── TERRAIN (istana api + sisi gaun crimson) ───
    "radiant_grass_1": (35, 8, 15),            # dress_darkest
    "radiant_grass_2": (85, 20, 30),           # dress_dark
    "radiant_grass_3": (145, 35, 50),          # dress_mid
    "radiant_grass_4": (200, 60, 80),          # dress_light
    "radiant_grass_high": (240, 120, 130),     # dress_shine
    "radiant_moss": (230, 100, 30),            # lumut hair

    # Dire side: tungku bara + rambut api oranye
    "dire_earth_1": (85, 20, 10),              # hair_darkest
    "dire_earth_2": (160, 45, 20),             # hair_dark
    "dire_earth_3": (230, 100, 30),            # hair_mid
    "dire_earth_4": (255, 165, 60),            # hair_light
    "dire_ash": (95, 65, 15),                  # abu emas
    "dire_burnt": (18, 5, 8),                  # tungku pekat

    "transition_1": (110, 35, 45),             # transisi crimson
    "transition_2": (180, 80, 45),             # transisi bara

    # ─── PATH (batu istana + retakan emas) ───
    "path_stone_1": (22, 8, 14),               # batu istana gelap
    "path_stone_2": (60, 20, 30),              # batu istana
    "path_stone_3": (110, 40, 55),             # batu aus
    "path_stone_4": (165, 70, 85),             # batu terang
    "path_moss": (80, 15, 25),                 # lumut bara
    "path_crack": (255, 245, 190),             # RETAKAN EMAS (gold_shine)

    # ─── RIVER (sungai bara api) ───
    "river_deep": (85, 20, 10),                # hair_darkest
    "river_mid": (160, 45, 20),                # hair_dark
    "river_light": (230, 100, 30),             # hair_mid
    "river_glow": (255, 165, 60),              # hair_light
    "river_foam": (255, 220, 130),             # hair_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon hangus
    "has_dead_trees": True,        # pohon kering
    "has_gravestones": True,       # makam istana
    "has_crystals_blue": False,
    "has_crystals_red": True,      # kristal bara
    "has_ancient_ruins": True,     # reruntuhan istana api
    "has_bones": True,             # tulang belulang
    "has_mushrooms_dark": True,    # jamur gelap
    "has_rocks_mossy": True,       # batu berlumut
    "has_dark_bushes": True,       # semak hangus
    "has_glow_flowers": True,      # bunga bara bercahaya
    "has_spike_traps": False,
    "has_torch_stones": True,      # obor api bara

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan bara api (ember spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (255, 165, 60), (255, 220, 130), (255, 245, 190)
    ],
    "particle_colors_dire": [
        (160, 45, 20), (230, 100, 30), (240, 120, 130)
    ],
    "particle_count": 60,           # ember spark

    "fog_enabled": True,
    "fog_color": (85, 30, 30, 45),  # kabut asap api
    "fog_count": 18,

    "ambient_tint": (85, 25, 20, 20),  # semburat bara api
}

SKYFURY_THEME = {
    "name": "The Skyfury",
    "boss_identity": "cogsworth",
    "boss_title": "The Skyfury",

    # ─── TERRAIN (langit steampunk + sisi kapal tembaga) ───
    "radiant_grass_1": (12, 12, 15),           # iron_darkest
    "radiant_grass_2": (35, 35, 42),           # iron_dark
    "radiant_grass_3": (75, 75, 85),           # iron_mid
    "radiant_grass_4": (135, 135, 148),        # iron_light
    "radiant_grass_high": (200, 200, 215),     # iron_shine
    "radiant_moss": (35, 120, 145),            # lumut teal

    # Dire side: langit senja + api roket
    "dire_earth_1": (35, 18, 8),               # copper_darkest
    "dire_earth_2": (90, 50, 20),              # copper_dark
    "dire_earth_3": (170, 100, 40),            # copper_mid
    "dire_earth_4": (230, 155, 75),            # copper_light
    "dire_ash": (45, 15, 5),                   # abu fire
    "dire_burnt": (8, 8, 10),                  # langit pekat

    "transition_1": (60, 55, 60),              # transisi besi
    "transition_2": (110, 90, 45),             # transisi tembaga

    # ─── PATH (papan besi + retakan api roket) ───
    "path_stone_1": (10, 10, 14),              # papan besi gelap
    "path_stone_2": (32, 32, 40),              # papan besi
    "path_stone_3": (70, 70, 82),              # papan aus
    "path_stone_4": (120, 120, 135),           # papan terang
    "path_moss": (25, 25, 32),                 # lumut besi
    "path_crack": (255, 250, 210),             # RETAKAN API (fire_shine)

    # ─── RIVER (sungai api roket) ───
    "river_deep": (45, 15, 5),                 # fire_darkest
    "river_mid": (140, 45, 15),                # fire_dark
    "river_light": (230, 105, 30),             # fire_mid
    "river_glow": (255, 175, 65),              # fire_light
    "river_foam": (255, 250, 210),             # fire_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,        # pohon besi
    "has_dead_trees": True,        # pohon kering
    "has_gravestones": True,       # makam teknisi
    "has_crystals_blue": True,     # kristal teal
    "has_crystals_red": False,
    "has_ancient_ruins": True,     # reruntuhan pabrik langit
    "has_bones": False,
    "has_mushrooms_dark": True,    # jamur gelap
    "has_rocks_mossy": True,       # batu berlumut
    "has_dark_bushes": True,       # semak besi
    "has_glow_flowers": True,      # bunga mekanik bercahaya
    "has_spike_traps": True,       # roda bergerigi
    "has_torch_stones": True,      # obor api roket

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = percikan api mesin (sky spark) melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (255, 175, 65), (255, 225, 130), (150, 230, 245)
    ],
    "particle_colors_dire": [
        (140, 45, 15), (230, 105, 30), (75, 75, 85)
    ],
    "particle_count": 60,           # sky spark

    "fog_enabled": True,
    "fog_color": (45, 45, 55, 45),  # kabut asap mesin
    "fog_count": 18,

    "ambient_tint": (60, 40, 20, 20),  # semburat senja tembaga
}

MOONREAPER_THEME = {
    "name": "The Moonreaper",
    "boss_identity": "yomigetsu",
    "boss_title": "The Moonreaper",

    # ─── TERRAIN (medan kuil bulan - cahaya bulan perak di sisi terang) ───
    "radiant_grass_1": (25, 22, 45),            # tanah malam biru-ungu gelap
    "radiant_grass_2": (45, 42, 70),            # moonlight dark
    "radiant_grass_3": (75, 72, 105),           # moonlight mid
    "radiant_grass_4": (110, 105, 145),         # moonlight light
    "radiant_grass_high": (150, 145, 185),      # sorot cahaya bulan
    "radiant_moss": (70, 55, 110),              # lumut ungu

    # Dire side: alam bayangan ungu (kimono gelap)
    "dire_earth_1": (18, 10, 30),               # kimono_darkest
    "dire_earth_2": (40, 25, 60),               # kimono_dark
    "dire_earth_3": (70, 45, 100),              # kimono_mid
    "dire_earth_4": (105, 70, 140),             # kimono_light
    "dire_ash": (35, 20, 55),                   # abu ungu
    "dire_burnt": (8, 5, 15),                   # langit pekat

    "transition_1": (50, 45, 75),               # transisi malam
    "transition_2": (85, 70, 115),              # transisi ungu

    # ─── PATH (batu kuil bulan) ───
    "path_stone_1": (35, 30, 55),               # batu gelap
    "path_stone_2": (60, 55, 90),               # batu kuil
    "path_stone_3": (95, 90, 135),              # batu aus
    "path_stone_4": (140, 135, 180),            # batu terang
    "path_moss": (60, 45, 90),                  # lumut bulan
    "path_crack": (250, 235, 255),              # RETAKAN CAHAYA SABIT (moon_shine)

    # ─── RIVER (sungai cahaya bulan violet) ───
    "river_deep": (15, 5, 40),                  # moon_darkest
    "river_mid": (55, 20, 110),                 # moon_dark
    "river_light": (140, 70, 220),              # moon_mid
    "river_glow": (200, 140, 255),              # moon_light
    "river_foam": (250, 235, 255),              # moon_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,         # pohon bayangan
    "has_dead_trees": True,         # pohon kering
    "has_gravestones": False,       # makam tua (kuil)
    "has_crystals_blue": True,      # kristal ungu-biru
    "has_crystals_red": False,
    "has_ancient_ruins": True,      # reruntuhan kuil bulan
    "has_bones": False,
    "has_mushrooms_dark": True,     # jamur malam
    "has_rocks_mossy": True,        # batu berlumut bulan
    "has_dark_bushes": True,        # semak bayangan
    "has_glow_flowers": True,       # bunga cahaya bulan
    "has_spike_traps": True,        # perangkap bayangan
    "has_torch_stones": True,       # obor ungu

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = cahaya bulan ungu melayang di udara malam.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (200, 140, 255), (150, 180, 255), (250, 235, 255)
    ],
    "particle_colors_dire": [
        (70, 45, 120), (140, 70, 220), (35, 25, 60)
    ],
    "particle_count": 50,           # cahaya bulan melayang

    "fog_enabled": True,
    "fog_color": (40, 25, 70, 40),  # kabut ungu malam
    "fog_count": 16,

    "ambient_tint": (45, 30, 80, 25),  # semburat bulan ungu
}


MOONFANG_THEME = {
    "name": "The Moonfang Prince",
    "boss_identity": "akirakumo",
    "boss_title": "The Moonfang Prince",

    # ─── TERRAIN (kuil bulan perak - sisi terang bersalju perak) ───
    "radiant_grass_1": (35, 40, 60),            # armor_dark biru baja gelap
    "radiant_grass_2": (60, 68, 90),            # armor_mid
    "radiant_grass_3": (110, 118, 140),         # armor_light
    "radiant_grass_4": (160, 165, 185),         # perak terang
    "radiant_grass_high": (210, 212, 225),      # kimono_shine putih perak
    "radiant_moss": (85, 55, 145),              # lumut ungu (sash)

    # Dire side: bayangan kuil ungu + aksen emas
    "dire_earth_1": (30, 18, 55),               # sash_dark ungu tua
    "dire_earth_2": (65, 45, 115),              # sash_mid
    "dire_earth_3": (115, 85, 175),             # sash_light
    "dire_earth_4": (160, 130, 215),            # sash_shine
    "dire_ash": (45, 35, 70),                   # abu ungu
    "dire_burnt": (12, 10, 22),                 # malam pekat

    "transition_1": (60, 60, 80),               # transisi perak
    "transition_2": (90, 75, 130),              # transisi ungu-perak

    # ─── PATH (batu kuil bulan bersalju) ───
    "path_stone_1": (45, 48, 62),               # batu gelap
    "path_stone_2": (80, 85, 105),              # batu kuil
    "path_stone_3": (130, 135, 155),            # batu aus
    "path_stone_4": (185, 188, 205),            # batu terang
    "path_moss": (75, 55, 115),                 # lumut bulan
    "path_crack": (255, 240, 165),              # RETAKAN EMAS (gold_shine)

    # ─── RIVER (sungai cahaya bulan ungu) ───
    "river_deep": (25, 15, 50),                 # sash_dark
    "river_mid": (70, 45, 125),                 # sash_mid
    "river_light": (140, 105, 195),             # sash_light
    "river_glow": (205, 180, 240),              # sash_shine
    "river_foam": (250, 245, 252),              # skin_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,         # pohon perak
    "has_dead_trees": True,         # pohon kering bulan
    "has_gravestones": False,       # kuil suci
    "has_crystals_blue": True,      # kristal perak-biru
    "has_crystals_red": False,
    "has_ancient_ruins": True,      # reruntuhan kuil bulan
    "has_bones": False,
    "has_mushrooms_dark": True,     # jamur malam
    "has_rocks_mossy": True,        # batu berlumut
    "has_dark_bushes": True,        # semak bayangan
    "has_glow_flowers": True,       # bunga cahaya bulan
    "has_spike_traps": True,        # perangkap bayangan
    "has_torch_stones": True,       # obor emas

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = cahaya bulan perak-ungu melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (235, 238, 245), (205, 180, 240), (245, 240, 165)
    ],
    "particle_colors_dire": [
        (85, 55, 145), (160, 130, 215), (40, 30, 70)
    ],
    "particle_count": 55,           # cahaya bulan melayang

    "fog_enabled": True,
    "fog_color": (60, 55, 85, 40),  # kabut perak-ungu
    "fog_count": 17,

    "ambient_tint": (65, 60, 95, 22),  # semburat bulan perak-ungu
}


EMBERLION_THEME = {
    "name": "The Emberlion Ronin",
    "boss_identity": "kaithros",
    "boss_title": "The Emberlion Ronin",

    # ─── TERRAIN (medan dojo api - sisi terang haori putih & api) ───
    "radiant_grass_1": (35, 30, 28),            # uniform_darkest hitam kebiruan
    "radiant_grass_2": (60, 55, 50),            # haori_shadow abu hangat
    "radiant_grass_3": (110, 100, 90),          # haori_dark
    "radiant_grass_4": (170, 160, 150),         # haori_mid
    "radiant_grass_high": (235, 225, 215),      # haori_light putih
    "radiant_moss": (200, 90, 25),              # lumut api

    # Dire side: medan terbakar + api
    "dire_earth_1": (30, 8, 2),                 # fire_darkest
    "dire_earth_2": (85, 20, 8),                # fire_dark
    "dire_earth_3": (150, 45, 15),              # fire_deep
    "dire_earth_4": (220, 90, 25),              # fire_mid
    "dire_ash": (45, 15, 5),                    # abu api
    "dire_burnt": (10, 4, 2),                   # hangus

    "transition_1": (80, 70, 60),               # transisi abu-hangat
    "transition_2": (150, 95, 40),              # transisi api

    # ─── PATH (papan dojo kayu terbakar) ───
    "path_stone_1": (30, 25, 22),               # papan gelap
    "path_stone_2": (65, 58, 50),               # papan dojo
    "path_stone_3": (115, 105, 92),             # papan aus
    "path_stone_4": (175, 165, 150),            # papan terang
    "path_moss": (150, 60, 15),                 # lumut api
    "path_crack": (255, 250, 200),              # RETAKAN API (fire_shine)

    # ─── RIVER (sungai api) ───
    "river_deep": (30, 5, 0),                   # fire_darkest
    "river_mid": (90, 20, 5),                   # fire_dark
    "river_light": (220, 90, 20),               # fire_mid
    "river_glow": (255, 150, 40),               # fire_bright
    "river_foam": (255, 250, 200),              # fire_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,         # pohon hangus
    "has_dead_trees": True,         # pohon mati
    "has_gravestones": False,       # dojo suci
    "has_crystals_blue": False,
    "has_crystals_red": True,       # kristal api
    "has_ancient_ruins": True,      # reruntuhan dojo
    "has_bones": False,
    "has_mushrooms_dark": True,     # jamur bara
    "has_rocks_mossy": True,        # batu berlumut
    "has_dark_bushes": True,        # semak api
    "has_glow_flowers": True,       # bunga bara bercahaya
    "has_spike_traps": True,        # perangkap api
    "has_torch_stones": True,       # obor api

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "ember" = bara api membumbung (rising embers).
    "particle_type": "ember",
    "particle_colors_radiant": [
        (255, 200, 80), (255, 150, 40), (255, 250, 200)
    ],
    "particle_colors_dire": [
        (150, 40, 10), (220, 90, 20), (90, 20, 5)
    ],
    "particle_count": 50,           # bara api

    "fog_enabled": True,
    "fog_color": (45, 20, 10, 40),  # kabut asap api
    "fog_count": 16,

    "ambient_tint": (80, 40, 15, 22),  # semburat senja api
}


LUNARHERALD_THEME = {
    "name": "The Lunar Herald",
    "boss_identity": "nyxaris",
    "boss_title": "The Lunar Herald",

    # ─── TERRAIN (malam gelap - sisi terang cahaya bulan cyan) ───
    "radiant_grass_1": (12, 16, 28),            # coat_darkest ungu-hitam
    "radiant_grass_2": (28, 34, 52),            # coat_dark
    "radiant_grass_3": (60, 70, 100),           # armor_mid metal gelap
    "radiant_grass_4": (110, 120, 155),         # armor_light
    "radiant_grass_high": (175, 190, 220),      # armor_shine
    "radiant_moss": (120, 180, 230),            # lumut cahaya bulan cyan

    # Dire side: sihir bulan ungu + aksen crimson
    "dire_earth_1": (25, 8, 40),                # purple_darkest
    "dire_earth_2": (55, 25, 90),               # purple_dark
    "dire_earth_3": (110, 60, 150),             # purple_mid
    "dire_earth_4": (170, 120, 210),            # purple_light
    "dire_ash": (35, 15, 45),                   # abu ungu
    "dire_burnt": (10, 8, 15),                  # malam pekat

    "transition_1": (45, 48, 70),               # transisi metal gelap
    "transition_2": (85, 70, 120),              # transisi ungu-bulan

    # ─── PATH (batu altar bulan) ───
    "path_stone_1": (18, 20, 32),               # batu gelap
    "path_stone_2": (45, 50, 72),               # batu altar
    "path_stone_3": (90, 95, 125),              # batu aus
    "path_stone_4": (150, 155, 190),            # batu terang
    "path_moss": (50, 90, 140),                 # lumut bulan
    "path_crack": (240, 250, 255),              # RETAKAN CAHAYA BULAN (moon_white)

    # ─── RIVER (sungai cahaya bulan cyan) ───
    "river_deep": (20, 35, 60),                 # moon_darkest
    "river_mid": (50, 90, 140),                 # moon_dark
    "river_light": (120, 180, 230),             # moon_mid
    "river_glow": (200, 235, 255),              # moon_light
    "river_foam": (240, 250, 255),              # moon_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,         # pohon malam
    "has_dead_trees": True,         # pohon kering
    "has_gravestones": False,       # altar suci
    "has_crystals_blue": True,      # kristal bulan cyan
    "has_crystals_red": False,
    "has_ancient_ruins": True,      # reruntuhan altar bulan
    "has_bones": False,
    "has_mushrooms_dark": True,     # jamur malam
    "has_rocks_mossy": True,        # batu berlumut
    "has_dark_bushes": True,        # semak bayangan
    "has_glow_flowers": True,       # bunga cahaya bulan
    "has_spike_traps": True,        # perangkap bayangan
    "has_torch_stones": True,       # obor bulan

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = cahaya bulan cyan-putih melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (200, 235, 255), (240, 250, 255), (120, 180, 230)
    ],
    "particle_colors_dire": [
        (110, 60, 150), (170, 120, 210), (55, 25, 90)
    ],
    "particle_count": 55,           # cahaya bulan melayang

    "fog_enabled": True,
    "fog_color": (30, 40, 65, 42),  # kabut malam biru
    "fog_count": 17,

    "ambient_tint": (35, 50, 80, 22),  # semburat bulan cyan
}


MOONBORN_THEME = {
    "name": "The Moon-Born Sovereign",
    "boss_identity": "tsukiyora",
    "boss_title": "The Moon-Born Sovereign",

    # ─── TERRAIN (kuil bulan putih - sisi terang kimono putih perak) ───
    "radiant_grass_1": (35, 33, 45),            # robe_darkest abu-ungu
    "radiant_grass_2": (70, 66, 85),            # robe_dark
    "radiant_grass_3": (130, 125, 145),         # robe_mid
    "radiant_grass_4": (190, 186, 205),         # robe_light
    "radiant_grass_high": (240, 238, 248),      # robe_shine putih
    "radiant_moss": (110, 65, 155),             # lumut ungu (trim)

    # Dire side: mata ketiga merah + void hitam
    "dire_earth_1": (25, 8, 12),                # third_eye_dark merah gelap
    "dire_earth_2": (70, 18, 25),               # third_eye_dark
    "dire_earth_3": (150, 35, 42),              # third_eye_mid
    "dire_earth_4": (215, 70, 60),              # third_eye_light
    "dire_ash": (30, 15, 25),                   # abu merah
    "dire_burnt": (6, 3, 10),                   # void_darkest hitam pekat

    "transition_1": (70, 65, 85),               # transisi putih-abu
    "transition_2": (120, 90, 130),             # transisi ungu

    # ─── PATH (batu kuil bulan) ───
    "path_stone_1": (40, 38, 55),               # batu gelap
    "path_stone_2": (80, 78, 100),              # batu kuil
    "path_stone_3": (135, 132, 158),            # batu aus
    "path_stone_4": (195, 192, 215),            # batu terang
    "path_moss": (60, 35, 95),                  # lumut trim
    "path_crack": (255, 253, 255),              # RETAKAN CAHAYA PUTIH (hair_shine)

    # ─── RIVER (sungai chakra bulan ungu) ───
    "river_deep": (25, 15, 40),                 # trim_darkest
    "river_mid": (60, 35, 95),                  # trim_dark
    "river_light": (110, 65, 155),              # trim_mid
    "river_glow": (170, 120, 210),              # trim_light
    "river_foam": (255, 253, 255),              # putih bulan

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,         # pohon kuil
    "has_dead_trees": True,         # pohon kering
    "has_gravestones": False,       # kuil suci
    "has_crystals_blue": True,      # kristal bulan
    "has_crystals_red": True,       # kristal mata ketiga
    "has_ancient_ruins": True,      # reruntuhan kuil
    "has_bones": False,
    "has_mushrooms_dark": True,     # jamur malam
    "has_rocks_mossy": True,        # batu berlumut
    "has_dark_bushes": True,        # semak bayangan
    "has_glow_flowers": True,       # bunga cahaya bulan
    "has_spike_traps": True,        # perangkap bayangan
    "has_torch_stones": True,       # obor putih

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "firefly" = cahaya bulan putih-ungu melayang.
    "particle_type": "firefly",
    "particle_colors_radiant": [
        (255, 253, 255), (235, 232, 245), (170, 120, 210)
    ],
    "particle_colors_dire": [
        (110, 65, 155), (200, 50, 45), (25, 15, 40)
    ],
    "particle_count": 55,           # cahaya bulan melayang

    "fog_enabled": True,
    "fog_color": (55, 50, 70, 40),  # kabut kuil ungu
    "fog_count": 17,

    "ambient_tint": (70, 60, 90, 20),  # semburat kuil bulan ungu
}


HOLLOWBANE_THEME = {
    "name": "The Substitute Shinigami",
    "boss_identity": "hollowbane",
    "boss_title": "The Substitute Shinigami",

    # ─── TERRAIN (kota malam shinigami - sisi terang robe hitam biru) ───
    "radiant_grass_1": (8, 10, 18),             # robe_darkest hitam kebiruan
    "radiant_grass_2": (22, 24, 36),            # robe_dark
    "radiant_grass_3": (48, 50, 66),            # robe_mid
    "radiant_grass_4": (80, 82, 100),           # robe_light
    "radiant_grass_high": (120, 122, 142),      # robe_edge
    "radiant_moss": (220, 110, 25),             # lumut oranye (Getsuga)

    # Dire side: spiritual energy Getsuga oranye
    "dire_earth_1": (60, 15, 0),                # spirit_darkest
    "dire_earth_2": (140, 45, 5),               # spirit_dark
    "dire_earth_3": (230, 95, 15),              # spirit_mid
    "dire_earth_4": (255, 155, 45),             # spirit_light
    "dire_ash": (80, 30, 8),                    # abu api spiritual
    "dire_burnt": (8, 6, 12),                   # malam pekat

    "transition_1": (45, 46, 62),               # transisi hitam-biru
    "transition_2": (130, 80, 35),              # transisi oranye

    # ─── PATH (batu jalan kota malam) ───
    "path_stone_1": (15, 16, 26),               # batu gelap
    "path_stone_2": (40, 42, 60),               # batu jalan
    "path_stone_3": (78, 80, 102),              # batu aus
    "path_stone_4": (130, 132, 158),            # batu terang
    "path_moss": (180, 70, 20),                 # lumut Getsuga
    "path_crack": (255, 245, 200),              # RETAKAN ENERGI GETSUGA (spirit_shine)

    # ─── RIVER (sungai spiritual energy oranye) ───
    "river_deep": (60, 15, 0),                  # spirit_darkest
    "river_mid": (140, 45, 5),                  # spirit_dark
    "river_light": (230, 95, 15),               # spirit_mid
    "river_glow": (255, 155, 45),               # spirit_light
    "river_foam": (255, 245, 200),              # spirit_shine

    # ─── DECORATION FLAGS ───
    "has_dark_trees": True,         # pohon kota malam
    "has_dead_trees": True,         # pohon kering
    "has_gravestones": False,       # medan pertarungan
    "has_crystals_blue": True,      # kristal spiritual
    "has_crystals_red": True,       # kristal hollow merah
    "has_ancient_ruins": True,      # reruntuhan kota
    "has_bones": False,
    "has_mushrooms_dark": True,     # jamur malam
    "has_rocks_mossy": True,        # batu berlumut
    "has_dark_bushes": True,        # semak bayangan
    "has_glow_flowers": True,       # bunga spiritual bercahaya
    "has_spike_traps": True,        # perangkap bayangan
    "has_torch_stones": True,       # obor Getsuga

    # Custom decorations
    "has_cactus": False,
    "has_palm_trees": False,
    "has_sand_dunes": False,
    "has_ice_crystals": False,
    "has_frozen_trees": False,
    "has_snow_drifts": False,

    # ─── ENVIRONMENTAL EFFECTS ───
    # "ember" = energi spiritual Getsuga membumbung.
    "particle_type": "ember",
    "particle_colors_radiant": [
        (255, 155, 45), (255, 210, 100), (255, 245, 200)
    ],
    "particle_colors_dire": [
        (140, 45, 5), (230, 95, 15), (60, 15, 0)
    ],
    "particle_count": 55,           # energi spiritual

    "fog_enabled": True,
    "fog_color": (30, 28, 40, 45),  # kabut malam spiritual
    "fog_count": 17,

    "ambient_tint": (70, 45, 25, 20),  # semburat senja Getsuga
}


THEMES = {
    "forest": FOREST_THEME,
    "desert": DESERT_THEME,
    "ice": ICE_THEME,
    "volcanic": VOLCANIC_THEME,
    "haunted": HAUNTED_THEME,
    "ocean": OCEAN_THEME,
    "abyss": ABYSS_THEME,
    "nethervenom": NETHERVENOM_THEME,
    "soulforged": SOULFORGED_THEME,
    "radiant": RADIANT_THEME,
    "abyssal": ABYSSAL_THEME,
    "eldritch": ELDRITCH_THEME,
    "sanctum": SANCTUM_THEME,
    "eternalflame": ETERNALFLAME_THEME,
    "primordial": PRIMORDIAL_THEME,
    "celestialpeaks": CELESTIALPEAKS_THEME,
    "cosmic": COSMIC_THEME,
    "royal": ROYAL_THEME,
    "violet": VIOLET_THEME,
    "crimson": CRIMSON_THEME,
    "spectral": SPECTRAL_THEME,
    "sundered": SUNDERED_THEME,
    "empyrean": EMPYREAN_THEME,
    "solaris": SOLARIS_THEME,
    "abysstide": ABYSSTIDE_THEME,
    "crimsonmatriarch": CRIMSONMATRIARCH_THEME,
    "astral": ASTRAL_THEME,
    "shadowchain": SHADOWCHAIN_THEME,
    "frostveil": FROSTVEIL_THEME,
    "warshade": WARSHADE_THEME,
    "outlaw": OUTLAW_THEME,
    "hexbound": HEXBOUND_THEME,
    "voidbound": VOIDBOUND_THEME,
    "earthborn": EARTHBORN_THEME,
    "heartbane": HEARTBANE_THEME,
    "sunfist": SUNFIST_THEME,
    "voidwing": VOIDWING_THEME,
    "crimsondevourer": CRIMSONDEVOURER_THEME,
    "elementweave": ELEMENTWEAVE_THEME,
    "tempest": TEMPEST_THEME,
    "sawmill": SAWMILL_THEME,
    "croweye": CROWEYE_THEME,
    "crystalstorm": CRYSTALSTORM_THEME,
    "eternalwarlord": ETERNALWARLORD_THEME,
    "explosiveart": EXPLOSIVEART_THEME,
    "sandshadow": SANDSHADOW_THEME,
    "emberweaver": EMBERWEAVER_THEME,
    "skyfury": SKYFURY_THEME,
    "moonreaper": MOONREAPER_THEME,
    "moonfang": MOONFANG_THEME,
    "emberlion": EMBERLION_THEME,
    "lunarherald": LUNARHERALD_THEME,
    "moonborn": MOONBORN_THEME,
    "hollowbane": HOLLOWBANE_THEME,
}


def get_theme(theme_name):
    """Get theme config, fallback ke forest kalau tidak ditemukan"""
    return THEMES.get(theme_name, FOREST_THEME)


# ====================================================================
# generators.py
# ====================================================================
class _NS_generators:
    """Namespace generators - isi asli tidak diubah."""

    # map_components/generators.py
    # Lane path, river, decoration position generation
    # ================================



    class PathGenerator:
        """Generate curved lane paths & river"""

        @staticmethod
        def make_curved_path(waypoints, smoothness=5):
            """Catmull-Rom spline interpolation"""
            if len(waypoints) < 2:
                return waypoints
            points = []
            pts = [waypoints[0]] + list(waypoints) + [waypoints[-1]]
            for i in range(len(pts) - 3):
                p0, p1, p2, p3 = pts[i], pts[i + 1], pts[i + 2], pts[i + 3]
                for step in range(smoothness):
                    t = step / smoothness
                    t2, t3 = t * t, t * t * t
                    x = 0.5 * ((2 * p1[0]) +
                               (-p0[0] + p2[0]) * t +
                               (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                               (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
                    y = 0.5 * ((2 * p1[1]) +
                               (-p0[1] + p2[1]) * t +
                               (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                               (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
                    points.append((int(x), int(y)))
            points.append(waypoints[-1])
            return points

        @staticmethod
        def generate_lanes(map_w, map_h):
            """Generate 3 lane paths (top, mid, bot)"""
            make = _NS_generators.PathGenerator.make_curved_path

            top = make([
                (90, map_h - 130), (85, map_h - 260), (95, map_h - 380),
                (120, map_h - 500), (170, 180), (240, 100),
                (380, 75), (550, 70), (720, 75),
                (880, 85), (1030, 110), (map_w - 100, 180),
            ], smoothness=10)

            bot = make([
                (130, map_h - 90), (260, map_h - 70), (420, map_h - 60),
                (600, map_h - 60), (780, map_h - 65), (940, map_h - 75),
                (1070, map_h - 100), (map_w - 110, map_h - 220),
                (map_w - 90, map_h - 380), (map_w - 85, 250),
                (map_w - 100, 180),
            ], smoothness=10)

            mid = make([
                (170, map_h - 170), (300, map_h - 300), (440, map_h - 400),
                (map_w // 2 - 60, map_h // 2 + 40), (map_w // 2, map_h // 2),
                (map_w // 2 + 60, map_h // 2 - 40), (map_w - 440, 400),
                (map_w - 300, 300), (map_w - 170, 170),
            ], smoothness=8)

            return top, mid, bot

        @staticmethod
        def generate_river(map_w, map_h):
            """Generate river path"""
            return _NS_generators.PathGenerator.make_curved_path([
                (0, 200), (150, 270), (350, 350),
                (map_w // 2, map_h // 2),
                (map_w - 350, map_h - 350),
                (map_w - 150, map_h - 270),
                (map_w, map_h - 200),
            ], smoothness=10)


    class DecorationGenerator:
        """Generate decoration positions"""

        def __init__(self, map_w, map_h, lane_points, river_points,
                     shop_positions):
            self.map_w = map_w
            self.map_h = map_h
            self.lane_points = lane_points
            self.river_points = river_points
            self.shop_positions = shop_positions

        def generate_all(self):
            """Generate semua decoration positions. Return dict."""
            random.seed(42)

            data = {
                'dark_trees': [],
                'dead_trees': [],
                'gravestones': [],
                'crystals_blue': [],
                'crystals_red': [],
                'ancient_ruins': [],
                'bones': [],
                'mushrooms_dark': [],
                'rocks_mossy': [],
                'dark_bushes': [],
                'glow_flowers': [],
                'spike_traps': [],
                'torch_stones': [],
                # Extra true-boss landmarks placed only in safe empty areas.
                'boss_landmarks': [],
            }

            # ─── DARK TREES (radiant side) ───
            for _ in range(45):
                x = random.randint(2, self.map_w // TILE_SIZE - 3) * TILE_SIZE
                y = random.randint(2, self.map_h // TILE_SIZE - 3) * TILE_SIZE
                if self._is_valid(x, y) and self._is_radiant(x, y):
                    size = random.choice([16, 20, 24])
                    variant = random.choice([0, 0, 1, 1, 2])
                    data['dark_trees'].append((x, y, size, variant))

            # ─── DEAD TREES (dire side) ───
            for _ in range(35):
                x = random.randint(2, self.map_w // TILE_SIZE - 3) * TILE_SIZE
                y = random.randint(2, self.map_h // TILE_SIZE - 3) * TILE_SIZE
                if self._is_valid(x, y) and self._is_dire(x, y):
                    size = random.choice([14, 18, 22])
                    data['dead_trees'].append((x, y, size))

            # ─── GRAVESTONES (dire side) ───
            for _ in range(12):
                x = random.randint(3, self.map_w // TILE_SIZE - 3) * TILE_SIZE
                y = random.randint(3, self.map_h // TILE_SIZE - 3) * TILE_SIZE
                if self._is_valid(x, y) and self._is_dire(x, y):
                    data['gravestones'].append((x, y))

            # ─── BLUE CRYSTALS (radiant) ───
            for _ in range(15):
                x = random.randint(3, self.map_w // TILE_SIZE - 3) * TILE_SIZE
                y = random.randint(3, self.map_h // TILE_SIZE - 3) * TILE_SIZE
                if self._is_valid(x, y) and self._is_radiant(x, y):
                    size = random.randint(8, 14)
                    data['crystals_blue'].append((x, y, size))

            # ─── RED CRYSTALS (dire) ───
            for _ in range(12):
                x = random.randint(3, self.map_w // TILE_SIZE - 3) * TILE_SIZE
                y = random.randint(3, self.map_h // TILE_SIZE - 3) * TILE_SIZE
                if self._is_valid(x, y) and self._is_dire(x, y):
                    size = random.randint(6, 12)
                    data['crystals_red'].append((x, y, size))

            # ─── ANCIENT RUINS ───
            for _ in range(10):
                x = random.randint(3, self.map_w // TILE_SIZE - 3) * TILE_SIZE
                y = random.randint(3, self.map_h // TILE_SIZE - 3) * TILE_SIZE
                if self._is_valid(x, y, min_lane=60):
                    variant = random.choice(['pillar', 'arch', 'wall'])
                    data['ancient_ruins'].append((x, y, variant))

            # ─── BONES (dire) ───
            for _ in range(15):
                x = random.randint(3, self.map_w // TILE_SIZE - 3) * TILE_SIZE
                y = random.randint(3, self.map_h // TILE_SIZE - 3) * TILE_SIZE
                if self._is_valid(x, y) and self._is_dire(x, y):
                    bone_type = random.choice(['skull', 'rib', 'skeleton'])
                    data['bones'].append((x, y, bone_type))

            # ─── DARK MUSHROOMS ───
            for _ in range(25):
                x = random.randint(3, self.map_w // TILE_SIZE - 3) * TILE_SIZE
                y = random.randint(3, self.map_h // TILE_SIZE - 3) * TILE_SIZE
                if self._is_valid(x, y):
                    if self._is_dire(x, y):
                        color = random.choice([
                            (140, 30, 30), (100, 20, 60), (80, 40, 80)])
                    else:
                        color = random.choice([
                            (60, 80, 150), (100, 60, 130), (140, 50, 100)])
                    data['mushrooms_dark'].append((x, y, color))

            # ─── MOSSY ROCKS ───
            for _ in range(20):
                x = random.randint(2, self.map_w // TILE_SIZE - 2) * TILE_SIZE
                y = random.randint(2, self.map_h // TILE_SIZE - 2) * TILE_SIZE
                if self._is_valid(x, y):
                    size = random.choice([12, 16, 20])
                    has_moss = self._is_radiant(x, y)
                    data['rocks_mossy'].append((x, y, size, has_moss))

            # ─── DARK BUSHES ───
            for _ in range(20):
                x = random.randint(2, self.map_w // TILE_SIZE - 2) * TILE_SIZE
                y = random.randint(2, self.map_h // TILE_SIZE - 2) * TILE_SIZE
                if self._is_valid(x, y) and self._is_radiant(x, y):
                    data['dark_bushes'].append(
                        (x, y, random.choice([12, 16])))

            # ─── GLOWING FLOWERS (radiant) ───
            for _ in range(20):
                x = random.randint(3, self.map_w // TILE_SIZE - 3) * TILE_SIZE
                y = random.randint(3, self.map_h // TILE_SIZE - 3) * TILE_SIZE
                if self._is_valid(x, y) and self._is_radiant(x, y):
                    color = random.choice([
                        CRYSTAL_BLUE_L, (150, 100, 200),
                        (100, 200, 150), (255, 200, 100)])
                    data['glow_flowers'].append((x, y, color))

            # ─── SPIKE TRAPS (dire) ───
            for _ in range(8):
                x = random.randint(3, self.map_w // TILE_SIZE - 3) * TILE_SIZE
                y = random.randint(3, self.map_h // TILE_SIZE - 3) * TILE_SIZE
                if self._is_valid(x, y) and self._is_dire(x, y):
                    data['spike_traps'].append((x, y))

            # ─── TRUE BOSS LANDMARK FIELD ───
            # Mengisi ruang kosong tanpa mengganggu lane, river, base, atau shop.
            landmark_attempts = 0
            while len(data['boss_landmarks']) < 30 and landmark_attempts < 240:
                landmark_attempts += 1
                x = random.randint(3, self.map_w // TILE_SIZE - 3) * TILE_SIZE
                y = random.randint(3, self.map_h // TILE_SIZE - 3) * TILE_SIZE
                if self._is_valid(x, y, min_lane=74):
                    data['boss_landmarks'].append((x, y,
                                                   random.choice([0, 1, 2, 3])))

            # ─── TORCH STONES (border) ───
            for x in range(120, self.map_w - 80, 200):
                data['torch_stones'].append((x, 32))
                data['torch_stones'].append((x, self.map_h - 32))
            for y in range(120, self.map_h - 80, 200):
                data['torch_stones'].append((32, y))
                data['torch_stones'].append((self.map_w - 32, y))

            random.seed()
            return data

        # ═══ VALIDATION HELPERS ═══

        def _is_valid(self, x, y, min_lane=50):
            if self._too_close_to_lane(x, y, min_lane):
                return False
            if self._too_close_to_river(x, y, 25):
                return False
            if self._too_close_to_base(x, y):
                return False
            if self._too_close_to_shop(x, y):
                return False
            return True

        def _too_close_to_lane(self, x, y, min_dist=45):
            import math as _m
            for lx, ly in self.lane_points:
                if _m.hypot(x - lx, y - ly) < min_dist:
                    return True
            return False

        def _too_close_to_river(self, x, y, min_dist=35):
            import math as _m
            for rx, ry in self.river_points:
                if _m.hypot(x - rx, y - ry) < min_dist:
                    return True
            return False

        def _too_close_to_base(self, x, y):
            import math as _m
            if _m.hypot(x - 120,
                         self.map_h - 120 - (self.map_h - y)) < 120:
                return True
            if _m.hypot(x - (self.map_w - 120), y - 120) < 120:
                return True
            return False

        def _too_close_to_shop(self, x, y, min_dist=70):
            import math as _m
            for pos in self.shop_positions:
                if _m.hypot(x - pos[0], y - pos[1]) < min_dist:
                    return True
            return False

        def _is_radiant(self, x, y):
            threshold_y = 200 + (self.map_h - 400) * x / self.map_w
            return y > threshold_y + 20

        def _is_dire(self, x, y):
            threshold_y = 200 + (self.map_h - 400) * x / self.map_w
            return y < threshold_y - 20



    # ================================


# ====================================================================
# static_renderer.py
# ====================================================================
class _NS_static_renderer:
    """Namespace static_renderer - isi asli tidak diubah."""

    # map_components/static_renderer.py
    # Terrain, river, lanes, border rendering (multi-theme)
    # ================================



    class StaticRenderer:
        """
        Render static map elements dengan theme support.
        Semua method sekarang terima `theme` dict.
        """

        # ═══════════════════════════════════════
        # TERRAIN
        # ═══════════════════════════════════════

        @staticmethod
        def draw_terrain(surf, map_w, map_h, theme):
            """Terrain base dengan diagonal split radiant/dire"""
            # Extract colors from theme
            rg1 = theme["radiant_grass_1"]
            rg2 = theme["radiant_grass_2"]
            rg3 = theme["radiant_grass_3"]
            rg4 = theme["radiant_grass_4"]
            rgh = theme["radiant_grass_high"]
            r_moss = theme["radiant_moss"]

            de1 = theme["dire_earth_1"]
            de2 = theme["dire_earth_2"]
            de3 = theme["dire_earth_3"]
            de4 = theme["dire_earth_4"]
            d_ash = theme["dire_ash"]
            d_burnt = theme["dire_burnt"]

            t1 = theme["transition_1"]
            t2 = theme["transition_2"]

            for ty in range(0, map_h, TILE_SIZE):
                for tx in range(0, map_w, TILE_SIZE):
                    threshold_y = 200 + (map_h - 400) * tx / map_w

                    if ty > threshold_y + 20:
                        base, mid, light, dark = rg2, rg3, rg4, rg1
                        side = 'radiant'
                    elif ty < threshold_y - 20:
                        base, mid, light, dark = de2, de3, de4, de1
                        side = 'dire'
                    else:
                        base, mid, light, dark = t1, t2, t2, t1
                        side = 'transition'

                    pygame.draw.rect(surf, base,
                                     (tx, ty, TILE_SIZE, TILE_SIZE))
                    variant = (tx * 7 + ty * 13) % 100

                    if side == 'radiant':
                        if variant < 20:
                            for i in range(3):
                                gx = tx + 2 + i * 5
                                gy = ty + 8 + (i % 2) * 3
                                pygame.draw.rect(surf, mid,
                                                 (gx, gy, 1, 3))
                                pygame.draw.rect(surf, light,
                                                 (gx, gy, 1, 1))
                        elif variant < 35:
                            pygame.draw.rect(surf, dark,
                                             (tx + 3, ty + 4, 8, 4))
                        elif variant < 45:
                            pygame.draw.rect(surf, r_moss,
                                             (tx + 5, ty + 6, 6, 4))
                        elif variant < 55:
                            pygame.draw.rect(surf, rgh,
                                             (tx + 6, ty + 4, 2, 2))
                    elif side == 'dire':
                        if variant < 20:
                            pygame.draw.line(surf, d_burnt,
                                             (tx + 2, ty + 6),
                                             (tx + 10, ty + 8), 1)
                            pygame.draw.line(surf, d_burnt,
                                             (tx + 6, ty + 4),
                                             (tx + 8, ty + 12), 1)
                        elif variant < 35:
                            pygame.draw.rect(surf, d_ash,
                                             (tx + 3, ty + 5, 5, 3))
                        elif variant < 50:
                            for _ in range(2):
                                px = tx + random.randint(2, TILE_SIZE - 3)
                                py = ty + random.randint(2, TILE_SIZE - 3)
                                pygame.draw.rect(surf, (60, 60, 70),
                                                 (px, py, 2, 2))
                        elif variant < 60:
                            pygame.draw.rect(surf, d_burnt,
                                             (tx + 4, ty + 6, 4, 3))
                        elif variant < 68:
                            pygame.draw.rect(surf, light,
                                             (tx + 5, ty + 3, 3, 2))
                    else:
                        if variant < 30:
                            pygame.draw.rect(surf, dark,
                                             (tx + 4, ty + 6, 4, 2))

        @staticmethod
        def draw_terrain_details(surf, map_w, map_h, theme):
            """Additional terrain overlay"""
            rg1 = theme["radiant_grass_1"]
            de1 = theme["dire_earth_1"]
            d_burnt = theme["dire_burnt"]

            random.seed(100)
            for _ in range(50):
                x = random.randint(0, map_w)
                y = random.randint(map_h // 2, map_h)
                if random.random() > 0.7:
                    pygame.draw.circle(surf, rg1, (x, y), 3)
            for _ in range(40):
                x = random.randint(0, map_w)
                y = random.randint(0, map_h // 2)
                if random.random() > 0.6:
                    pygame.draw.circle(surf, d_burnt, (x, y), 4)
                    pygame.draw.circle(surf, de1, (x - 1, y - 1), 2)
            random.seed()

        # ═══════════════════════════════════════
        # RIVER
        # ═══════════════════════════════════════

        @staticmethod
        def draw_river(surf, river_points, map_w, map_h, theme):
            """River dengan theme colors"""
            r_deep = theme["river_deep"]
            r_mid = theme["river_mid"]
            r_glow = theme["river_glow"]
            r_foam = theme["river_foam"]

            river_width = 44
            for i, (rx, ry) in enumerate(river_points):
                for dy in range(-river_width // 2,
                                river_width // 2, TILE_SIZE):
                    for dx in range(-river_width // 2,
                                    river_width // 2, TILE_SIZE):
                        tx = ((rx + dx) // TILE_SIZE) * TILE_SIZE
                        ty = ((ry + dy) // TILE_SIZE) * TILE_SIZE
                        dist = math.hypot(
                            tx + TILE_SIZE // 2 - rx,
                            ty + TILE_SIZE // 2 - ry)
                        if dist > river_width // 2:
                            continue
                        if tx < 0 or ty < 0 or \
                                tx >= map_w or ty >= map_h:
                            continue
                        if dist < river_width // 2 - 6:
                            pygame.draw.rect(surf, r_deep,
                                             (tx, ty, TILE_SIZE,
                                              TILE_SIZE))
                            for ddy in range(0, TILE_SIZE, 4):
                                for ddx in range(0, TILE_SIZE, 4):
                                    if (ddx + ddy) % 8 == 0:
                                        pygame.draw.rect(
                                            surf, r_mid,
                                            (tx + ddx, ty + ddy, 2, 2))
                            if (tx * ty) % 137 == 0:
                                pygame.draw.rect(surf, r_glow,
                                                 (tx + 6, ty + 6, 3, 3))
                                pygame.draw.rect(surf, r_foam,
                                                 (tx + 7, ty + 7, 1, 1))
                        else:
                            pygame.draw.rect(surf, r_mid,
                                             (tx, ty, TILE_SIZE,
                                              TILE_SIZE))

            # River banks
            for i in range(0, len(river_points), 3):
                rx, ry = river_points[i]
                if i < len(river_points) - 1:
                    next_pt = river_points[i + 1]
                    ddx = next_pt[0] - rx
                    ddy = next_pt[1] - ry
                    length = math.hypot(ddx, ddy)
                    if length > 0:
                        perp_x = -ddy / length
                        perp_y = ddx / length
                        for side in [1, -1]:
                            bx = int(rx + perp_x * side *
                                     (river_width // 2 + 2))
                            by = int(ry + perp_y * side *
                                     (river_width // 2 + 2))
                            if 0 <= bx < map_w and 0 <= by < map_h:
                                pygame.draw.rect(surf, (55, 55, 65),
                                                 (bx - 3, by - 3, 6, 6))
                                pygame.draw.rect(surf, (95, 95, 105),
                                                 (bx - 2, by - 2, 4, 4))
                                pygame.draw.rect(surf, (135, 135, 145),
                                                 (bx - 2, by - 2, 2, 2))
                                pygame.draw.rect(surf, OUTLINE,
                                                 (bx - 3, by - 3, 6, 6),
                                                 1)

        # ═══════════════════════════════════════
        # LANE (cobblestone path)
        # ═══════════════════════════════════════

        @staticmethod
        def draw_lane(surf, lane_points, map_w, map_h, theme):
            """Cobblestone path dengan theme"""
            lane_width = 42
            drawn_tiles = set()
            for lx, ly in lane_points:
                for dy in range(-lane_width, lane_width, TILE_SIZE):
                    for dx in range(-lane_width, lane_width, TILE_SIZE):
                        tx = ((lx + dx) // TILE_SIZE) * TILE_SIZE
                        ty = ((ly + dy) // TILE_SIZE) * TILE_SIZE
                        if (tx, ty) in drawn_tiles:
                            continue
                        dist = math.hypot(
                            tx + TILE_SIZE // 2 - lx,
                            ty + TILE_SIZE // 2 - ly)
                        if dist > lane_width // 2 + 4:
                            continue
                        if tx < 0 or ty < 0 or \
                                tx >= map_w or ty >= map_h:
                            continue
                        drawn_tiles.add((tx, ty))
                        _NS_static_renderer.StaticRenderer._draw_cobblestone_tile(
                            surf, tx, ty, theme)

            # Border stones
            for i in range(0, len(lane_points), 6):
                lx, ly = lane_points[i]
                if i < len(lane_points) - 1:
                    next_pt = lane_points[i + 1]
                    ddx = next_pt[0] - lx
                    ddy = next_pt[1] - ly
                    length = math.hypot(ddx, ddy)
                    if length > 0:
                        perp_x = -ddy / length
                        perp_y = ddx / length
                        for side in [1, -1]:
                            bx = int(lx + perp_x * side *
                                     (lane_width // 2 + 2))
                            by = int(ly + perp_y * side *
                                     (lane_width // 2 + 2))
                            if 5 < bx < map_w - 5 and \
                                    5 < by < map_h - 5:
                                _NS_static_renderer.StaticRenderer._draw_lane_border_stone(
                                    surf, bx, by, theme)

        @staticmethod
        def _draw_cobblestone_tile(surf, tx, ty, theme):
            ps1 = theme["path_stone_1"]
            ps2 = theme["path_stone_2"]
            ps3 = theme["path_stone_3"]
            ps4 = theme["path_stone_4"]
            p_moss = theme["path_moss"]
            p_crack = theme["path_crack"]

            pygame.draw.rect(surf, ps1,
                             (tx, ty, TILE_SIZE, TILE_SIZE))
            variant = (tx * 3 + ty * 7) % 100
            if variant < 40:
                pygame.draw.rect(surf, ps2,
                                 (tx + 1, ty + 1,
                                  TILE_SIZE - 2, TILE_SIZE - 2))
                pygame.draw.rect(surf, ps3,
                                 (tx + 2, ty + 2,
                                  TILE_SIZE - 4, TILE_SIZE - 4))
                pygame.draw.rect(surf, ps4,
                                 (tx + 2, ty + 2,
                                  TILE_SIZE - 4, 2))
            elif variant < 70:
                pygame.draw.rect(surf, ps2,
                                 (tx + 1, ty + 1,
                                  TILE_SIZE - 2, TILE_SIZE // 2 - 1))
                pygame.draw.rect(surf, ps3,
                                 (tx + 2, ty + 2,
                                  TILE_SIZE - 4, TILE_SIZE // 2 - 3))
                pygame.draw.rect(surf, ps4,
                                 (tx + 2, ty + 2,
                                  TILE_SIZE - 4, 1))
                pygame.draw.rect(surf, ps2,
                                 (tx + 1, ty + TILE_SIZE // 2 + 1,
                                  TILE_SIZE - 2, TILE_SIZE // 2 - 2))
                pygame.draw.rect(surf, ps3,
                                 (tx + 2, ty + TILE_SIZE // 2 + 2,
                                  TILE_SIZE - 4, TILE_SIZE // 2 - 4))
            else:
                for sy_off in [0, TILE_SIZE // 2]:
                    for sx_off in [0, TILE_SIZE // 2]:
                        pygame.draw.rect(
                            surf, ps2,
                            (tx + sx_off + 1, ty + sy_off + 1,
                             TILE_SIZE // 2 - 2, TILE_SIZE // 2 - 2))
                        pygame.draw.rect(
                            surf, ps3,
                            (tx + sx_off + 2, ty + sy_off + 2,
                             TILE_SIZE // 2 - 4, TILE_SIZE // 2 - 4))
                        pygame.draw.rect(
                            surf, ps4,
                            (tx + sx_off + 2, ty + sy_off + 2,
                             TILE_SIZE // 2 - 4, 1))

            if (tx + ty) % 7 == 0:
                pygame.draw.line(surf, p_crack,
                                 (tx + 3, ty + 4),
                                 (tx + 10, ty + 7), 1)
            if variant > 85:
                pygame.draw.rect(surf, p_moss,
                                 (tx + 3, ty + 3, 3, 2))
                pygame.draw.rect(surf, theme["radiant_moss"],
                                 (tx + 3, ty + 3, 2, 1))

        @staticmethod
        def _draw_lane_border_stone(surf, bx, by, theme):
            pygame.draw.rect(surf, OUTLINE, (bx - 5, by - 4, 10, 9))
            pygame.draw.rect(surf, (55, 55, 65),
                             (bx - 4, by - 3, 8, 7))
            pygame.draw.rect(surf, (95, 95, 105),
                             (bx - 3, by - 2, 6, 5))
            pygame.draw.rect(surf, (135, 135, 145),
                             (bx - 3, by - 2, 6, 2))
            pygame.draw.rect(surf, (175, 175, 185),
                             (bx - 3, by - 2, 3, 1))

        # ═══════════════════════════════════════
        # BORDER WALL
        # ═══════════════════════════════════════

        @staticmethod
        def draw_border_wall(surf, map_w, map_h, theme):
            """Border wall - theme parameter untuk future customization"""
            thickness = 20
            for x in range(0, map_w, TILE_SIZE):
                _NS_static_renderer.StaticRenderer._draw_dark_stone_block(
                    surf, x, 0, TILE_SIZE, thickness)
                _NS_static_renderer.StaticRenderer._draw_dark_stone_block(
                    surf, x, map_h - thickness, TILE_SIZE, thickness)
            for y in range(thickness, map_h - thickness, TILE_SIZE):
                _NS_static_renderer.StaticRenderer._draw_dark_stone_block(
                    surf, 0, y, thickness, TILE_SIZE)
                _NS_static_renderer.StaticRenderer._draw_dark_stone_block(
                    surf, map_w - thickness, y, thickness, TILE_SIZE)
            for x in range(30, map_w - 30, 40):
                _NS_static_renderer.StaticRenderer._draw_wall_spike(surf, x, thickness)

        @staticmethod
        def _draw_dark_stone_block(surf, x, y, w, h):
            pygame.draw.rect(surf, OUTLINE, (x, y, w, h))
            pygame.draw.rect(surf, (55, 55, 65),
                             (x + 1, y + 1, w - 2, h - 2))
            pygame.draw.rect(surf, (95, 95, 105),
                             (x + 2, y + 2, w - 4, h - 4))
            pygame.draw.rect(surf, (135, 135, 145),
                             (x + 2, y + 2, w - 4, 2))
            pygame.draw.rect(surf, (175, 175, 185),
                             (x + 2, y + 2, 4, 1))

        @staticmethod
        def _draw_wall_spike(surf, x, y):
            pygame.draw.polygon(surf, OUTLINE, [
                (x - 3, y), (x + 3, y), (x, y + 6)])
            pygame.draw.polygon(surf, (95, 95, 105), [
                (x - 2, y + 1), (x + 2, y + 1), (x, y + 5)])
            pygame.draw.line(surf, (135, 135, 145),
                             (x, y + 1), (x, y + 4), 1)





    # ================================


# ====================================================================
# dynamic_renderer.py  (tidak bisa dibungkus: merujuk 'DynamicRenderer' saat modul dimuat)
# ====================================================================
# map_components/dynamic_renderer.py
# Dynamic animated elements (theme-aware)
# ================================



class DynamicRenderer:
    """
    Dynamic (per-frame) elements dengan theme awareness:
    - Particles (fireflies/snow/sand/ember)
    - Fog
    - Torches
    - River animation
    - Shop glow & smoke
    """

    def __init__(self, map_renderer):
        self.mr = map_renderer
        self.theme = map_renderer.theme
        self._init_particles()
        self._init_fog()
        # Cache surface kecil (fog/glow/smoke) supaya tidak dialokasi
        # ulang tiap frame - hemat ratusan alokasi Surface per detik.
        self._surf_cache = {}

    def _cached_surf(self, key, builder):
        s = self._surf_cache.get(key)
        if s is None:
            s = builder()
            if len(self._surf_cache) > 400:
                self._surf_cache.pop(next(iter(self._surf_cache)))
            self._surf_cache[key] = s
        return s

    # ═══════════════════════════════════════
    # INIT
    # ═══════════════════════════════════════

    def _init_particles(self):
        """Init particles berdasarkan theme"""
        self.particles = []
        count = self.theme.get("particle_count", 30)
        # ── Preset kualitas Android: LOW 35%, MEDIUM 65%, HIGH 100% ──
        try:
            from mobile.perf import Quality
            if not Quality.particles:
                count = 0
            else:
                count = max(4, int(count * Quality.particle_ratio))
        except Exception:
            pass
        particle_type = self.theme.get("particle_type", "firefly")

        colors_radiant = self.theme.get(
            "particle_colors_radiant",
            [(100, 200, 255), (150, 255, 200), (255, 220, 100)])
        colors_dire = self.theme.get(
            "particle_colors_dire",
            [(255, 100, 50), (200, 50, 200), (255, 50, 100)])

        for _ in range(count):
            x = random.uniform(50, self.mr.map_width - 50)
            y = random.uniform(50, self.mr.map_height - 50)

            if y > self.mr.map_height * 0.5:
                color = random.choice(colors_radiant)
            else:
                color = random.choice(colors_dire)

            # Velocity per particle type
            if particle_type == "snow":
                # Snow falls down slowly
                vx = random.uniform(-0.3, 0.3)
                vy = random.uniform(0.3, 0.8)
            elif particle_type == "sand":
                # Sand swirls horizontal
                vx = random.uniform(0.5, 1.5)
                vy = random.uniform(-0.2, 0.2)
            elif particle_type == "ember":
                # Embers rise up
                vx = random.uniform(-0.3, 0.3)
                vy = random.uniform(-0.8, -0.3)
            else:
                # Firefly (default)
                vx = random.uniform(-0.4, 0.4)
                vy = random.uniform(-0.4, 0.4)

            self.particles.append({
                'x': x, 'y': y,
                'vx': vx, 'vy': vy,
                'phase': random.uniform(0, math.pi * 2),
                'color': color,
                'size': random.choice([1, 1, 2]),
                'type': particle_type,
            })

    def _init_fog(self):
        """Init fog dengan theme color"""
        self.fog_particles = []
        if not self.theme.get("fog_enabled", True):
            return

        fog_count = self.theme.get("fog_count", 15)
        try:
            from mobile.perf import Quality
            if not Quality.fog:
                return
            fog_count = max(3, int(fog_count * Quality.particle_ratio))
        except Exception:
            pass
        fog_color = self.theme.get("fog_color", (80, 60, 60, 30))

        for _ in range(fog_count):
            self.fog_particles.append({
                'x': random.uniform(0, self.mr.map_width),
                'y': random.uniform(0, self.mr.map_height * 0.5),
                'size': random.randint(30, 60),
                'vx': random.uniform(-0.1, 0.1),
                'color': fog_color,
                'alpha': fog_color[3] if len(fog_color) > 3 else 30,
            })

    # ═══════════════════════════════════════
    # UPDATE
    # ═══════════════════════════════════════

    def update(self, t):
        """Update all dynamic elements per frame"""
        particle_type = self.theme.get("particle_type", "firefly")

        for f in self.particles:
            f['x'] += f['vx']
            f['y'] += f['vy']
            f['phase'] += 0.08

            # Bounce logic per type
            if particle_type == "firefly":
                if f['x'] < 30 or f['x'] > self.mr.map_width - 30:
                    f['vx'] *= -1
                if f['y'] < 30 or f['y'] > self.mr.map_height - 30:
                    f['vy'] *= -1
                if random.random() < 0.02:
                    f['vx'] = random.uniform(-0.4, 0.4)
                    f['vy'] = random.uniform(-0.4, 0.4)

            elif particle_type == "snow":
                # Snow: wrap around screen top when reaches bottom
                if f['y'] > self.mr.map_height + 10:
                    f['y'] = -10
                    f['x'] = random.uniform(0, self.mr.map_width)
                # Slight swaying
                f['x'] += math.sin(f['phase']) * 0.2

            elif particle_type == "sand":
                # Sand: wrap horizontally
                if f['x'] > self.mr.map_width + 20:
                    f['x'] = -20
                    f['y'] = random.uniform(50,
                                            self.mr.map_height - 50)
                if f['x'] < -20:
                    f['x'] = self.mr.map_width + 20
                # Vertical wave
                f['y'] += math.sin(f['phase'] * 2) * 0.3

            elif particle_type == "ember":
                # Ember: rise up, wrap to bottom
                if f['y'] < -10:
                    f['y'] = self.mr.map_height + 10
                    f['x'] = random.uniform(0, self.mr.map_width)
                # Slight swaying
                f['x'] += math.sin(f['phase']) * 0.15

        # Fog
        for fog in self.fog_particles:
            fog['x'] += fog['vx']
            if fog['x'] < -100:
                fog['x'] = self.mr.map_width + 100
            elif fog['x'] > self.mr.map_width + 100:
                fog['x'] = -100

    # ═══════════════════════════════════════
    # DRAW ALL
    # ═══════════════════════════════════════

    def draw(self, surface, t):
        """Draw all dynamic elements"""
        try:
            from mobile.perf import Quality
        except Exception:
            Quality = None

        self.update(t)

        # LOW = hanya lapisan yang memengaruhi keterbacaan gameplay.
        # Kabut, animasi sungai, kilau & asap toko, partikel, dan obor
        # semuanya murni dekoratif: dimatikan di HP kelas bawah.
        _low = Quality is not None and Quality.level == "low"

        if Quality is None or Quality.fog:
            self._draw_fog(surface, t)
        if not _low:
            self._draw_river_animation(surface, t)
            self._draw_shop_glow(surface, t)
        if Quality is None or Quality.floating_decor:
            self._draw_shop_smoke(surface, t)
        if Quality is None or Quality.particles:
            self._draw_particles(surface, t)
        if not _low:
            self._draw_torches(surface, t)

    # ═══════════════════════════════════════
    # FOG
    # ═══════════════════════════════════════

    def _draw_fog(self, surface, t):
        """Fog dengan theme color (surface di-cache)"""
        for fog in self.fog_particles:
            color = fog.get('color', (80, 60, 60, 30))
            if len(color) == 3:
                color = (*color, fog.get('alpha', 30))
            size = fog['size']
            key = ("fog", size, color)

            def build():
                s = pygame.Surface((size * 2, size), pygame.SRCALPHA)
                pygame.draw.ellipse(s, color, (0, 0, size * 2, size))
                return s

            fog_surf = self._cached_surf(key, build)
            surface.blit(fog_surf,
                         (int(fog['x']) - size,
                          int(fog['y']) - size // 2))

    # ═══════════════════════════════════════
    # RIVER ANIMATION
    # ═══════════════════════════════════════

    def _draw_river_animation(self, surface, t):
        """Animated glowing runes di river"""
        # River glow color from theme
        glow_color = self.theme.get("river_glow", (80, 150, 200))
        foam_color = self.theme.get("river_foam", (180, 210, 230))

        for i, (rx, ry) in enumerate(self.mr.river_points):
            if i % 10 == 0:
                pulse = (math.sin(t * 0.05 + i) + 1) / 2
                if pulse > 0.5:
                    # Kuantisasi pulse supaya cache terbatas
                    pq = round(pulse * 10) / 10
                    r = max(1, int(pq * 4))
                    key = ("river", pq, glow_color, foam_color)

                    def build():
                        s = pygame.Surface((r * 4, r * 4),
                                           pygame.SRCALPHA)
                        pygame.draw.circle(s,
                                           (*glow_color,
                                            int(150 * pq)),
                                           (r * 2, r * 2), r * 2)
                        pygame.draw.circle(s,
                                           (*foam_color,
                                            int(200 * pq)),
                                           (r * 2, r * 2), r)
                        return s

                    glow_surf = self._cached_surf(key, build)
                    surface.blit(glow_surf,
                                 (rx - r * 2, ry - r * 2))

    # ═══════════════════════════════════════
    # SHOP EFFECTS
    # ═══════════════════════════════════════

    def _draw_shop_glow(self, surface, t):
        """Mystical glow around shops"""
        for shop_pos, side in [(self.mr.radiant_shop_pos, 'radiant'),
                               (self.mr.dire_shop_pos, 'dire')]:
            cx, cy = shop_pos
            pulse = (math.sin(t * 0.05) + 1) / 2

            glow_r = 45 + int(pulse * 8)
            color = (100, 200, 255) if side == 'radiant' \
                else (255, 80, 80)
            key = ("shopglow", glow_r, color)

            def build():
                s = pygame.Surface((glow_r * 2, glow_r * 2),
                                   pygame.SRCALPHA)
                for r in range(glow_r, 15, -4):
                    alpha = int((glow_r - r) * 2)
                    if alpha > 0:
                        pygame.draw.circle(s, (*color, alpha),
                                           (glow_r, glow_r), r)
                return s

            glow_surf = self._cached_surf(key, build)
            surface.blit(glow_surf,
                         (cx - glow_r, cy - glow_r - 5))

    def _draw_shop_smoke(self, surface, t):
        """Chimney smoke"""
        for shop_pos in [self.mr.radiant_shop_pos,
                         self.mr.dire_shop_pos]:
            cx, cy = shop_pos
            chim_x = cx + 19
            chim_y = cy - 32

            for i in range(3):
                phase = (t * 0.03 + i * 2) % 6
                sy = chim_y - int(phase * 8)
                sx = chim_x + int(math.sin(phase * 2 + i) * 3)
                size = 3 - int(phase / 2)
                if size > 0:
                    alpha = int(180 - phase * 25)
                    if alpha > 0:
                        ab = (alpha // 8) * 8  # bucket 8 langkah
                        key = ("smoke", size, ab)

                        def build():
                            s = pygame.Surface((size * 4, size * 4),
                                               pygame.SRCALPHA)
                            pygame.draw.circle(s, (100, 100, 110, ab),
                                               (size * 2, size * 2),
                                               size * 2)
                            pygame.draw.circle(s, (150, 150, 160, ab),
                                               (size * 2, size * 2),
                                               size)
                            return s

                        smoke_surf = self._cached_surf(key, build)
                        surface.blit(smoke_surf,
                                     (sx - size * 2,
                                      sy - size * 2))

    # ═══════════════════════════════════════
    # PARTICLES (theme-aware)
    # ═══════════════════════════════════════

    def _draw_particles(self, surface, t):
        """Particles dengan style per theme"""
        particle_type = self.theme.get("particle_type", "firefly")

        for f in self.particles:
            fx, fy = int(f['x']), int(f['y'])

            if particle_type == "firefly":
                # Firefly: pulsing brightness
                brightness = (math.sin(f['phase']) + 1) / 2
                if brightness < 0.3:
                    continue

                if brightness > 0.7:
                    glow_r = f['size'] + 2
                    col3 = f['color'][:3]
                    key = ("firefly", glow_r, col3)

                    def build():
                        s = pygame.Surface((glow_r * 4, glow_r * 4),
                                           pygame.SRCALPHA)
                        pygame.draw.circle(s, (*col3, 60),
                                           (glow_r * 2, glow_r * 2),
                                           glow_r * 2)
                        pygame.draw.circle(s, (*col3, 120),
                                           (glow_r * 2, glow_r * 2),
                                           glow_r)
                        return s

                    glow_surf = self._cached_surf(key, build)
                    surface.blit(glow_surf,
                                 (fx - glow_r * 2,
                                  fy - glow_r * 2))

                pygame.draw.rect(surface, f['color'],
                                 (fx, fy, f['size'], f['size']))
                pygame.draw.rect(surface, (255, 255, 255),
                                 (fx, fy, 1, 1))

            elif particle_type == "snow":
                # Snow: white flake with soft trail
                pygame.draw.rect(surface, f['color'],
                                 (fx, fy, f['size'] + 1,
                                  f['size'] + 1))
                pygame.draw.rect(surface, (255, 255, 255),
                                 (fx, fy, 1, 1))
                # Small glow
                if f['size'] >= 2:
                    glow_surf = pygame.Surface(
                        (6, 6), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf,
                                       (*f['color'][:3], 80),
                                       (3, 3), 2)
                    surface.blit(glow_surf, (fx - 2, fy - 2))

            elif particle_type == "sand":
                # Sand: streak/dust particles
                pygame.draw.rect(surface, f['color'],
                                 (fx, fy, f['size'] + 1, 1))
                pygame.draw.rect(surface, f['color'],
                                 (fx - 1, fy, 1, 1))

            elif particle_type == "ember":
                # Ember: fiery glow rising
                pygame.draw.rect(surface, f['color'],
                                 (fx, fy, f['size'], f['size']))
                # Warm glow
                glow_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf,
                                   (*f['color'][:3], 100),
                                   (4, 4), 3)
                surface.blit(glow_surf, (fx - 3, fy - 3))

    # ═══════════════════════════════════════
    # TORCHES (theme-aware color)
    # ═══════════════════════════════════════

    def _draw_torches(self, surface, t):
        """Torches dengan theme color"""
        # Ice theme: blue flames instead of orange
        theme_name = self.theme.get("name", "Forest")

        if theme_name == "Ice":
            fire_d = (30, 100, 180)
            fire_m = (80, 160, 240)
            fire_l = (150, 210, 255)
            fire_h = (220, 245, 255)
            glow_color = (100, 180, 255, 25)
        elif theme_name == "Desert":
            fire_d = (200, 100, 20)
            fire_m = (255, 170, 40)
            fire_l = (255, 220, 100)
            fire_h = (255, 250, 200)
            glow_color = (255, 200, 100, 25)
        elif theme_name == "Soulforged Expanse":
            # Api jiwa CYAN (identitas Naraka - The Lost Soul)
            fire_d = (5, 40, 60)
            fire_m = (15, 100, 140)
            fire_l = (55, 190, 230)
            fire_h = (200, 250, 255)
            glow_color = (55, 190, 230, 25)
        elif theme_name == "Radiant Expanse":
            # Api emas surya (identitas Aureth'zar - The Radiant Dawn)
            fire_d = (130, 75, 15)
            fire_m = (200, 130, 30)
            fire_l = (255, 220, 100)
            fire_h = (255, 245, 170)
            glow_color = (255, 220, 100, 25)
        elif theme_name == "Abyssal Depths":
            # Api azure abisal (identitas Thalakryon - The Abyssal Sovereign)
            fire_d = (5, 20, 45)
            fire_m = (20, 70, 130)
            fire_l = (110, 190, 220)
            fire_h = (230, 250, 255)
            glow_color = (110, 190, 220, 25)
        elif theme_name == "Eldritch Depths":
            # Api void teal (identitas Nazulmor - The Deepborn Herald)
            fire_d = (5, 20, 30)
            fire_m = (15, 60, 90)
            fire_l = (40, 140, 180)
            fire_h = (200, 250, 255)
            glow_color = (40, 140, 180, 25)
        elif theme_name == "Silver Sanctum":
            # Api emas suci (identitas Solvarin - The Holy Paladin Warden)
            fire_d = (110, 75, 15)
            fire_m = (200, 150, 45)
            fire_l = (250, 210, 100)
            fire_h = (255, 245, 180)
            glow_color = (250, 210, 100, 25)
        elif theme_name == "Eternal Flame":
            # Api abadi (identitas Pyraethis - The Eternal Firebird)
            fire_d = (170, 60, 5)
            fire_m = (240, 130, 20)
            fire_l = (255, 200, 60)
            fire_h = (255, 240, 130)
            glow_color = (255, 200, 60, 25)
        elif theme_name == "Primordial Grove":
            # Api hijau suci (identitas Yamako - The Primordial Woodshaper)
            fire_d = (20, 70, 25)
            fire_m = (60, 155, 50)
            fire_l = (130, 220, 100)
            fire_h = (200, 255, 140)
            glow_color = (130, 220, 100, 25)
        elif theme_name == "Celestial Peaks":
            # Api emas langit (identitas Seiryukong - The Celestial Simian)
            fire_d = (95, 65, 20)
            fire_m = (180, 130, 40)
            fire_l = (240, 195, 80)
            fire_h = (255, 250, 210)
            glow_color = (240, 195, 80, 25)
        elif theme_name == "Cosmic Expanse":
            # Api nebula (identitas Nyxareth - The Cosmic Sovereign)
            fire_d = (65, 20, 130)
            fire_m = (135, 55, 220)
            fire_l = (200, 130, 255)
            fire_h = (235, 180, 255)
            glow_color = (200, 130, 255, 25)
        elif theme_name == "Royal Citadel":
            # Api emas kerajaan (identitas Aurelion - The Golden Sovereign)
            fire_d = (115, 85, 20)
            fire_m = (200, 155, 40)
            fire_l = (245, 215, 95)
            fire_h = (255, 245, 180)
            glow_color = (245, 215, 95, 25)
        elif theme_name == "Violet Court":
            # Api violet (identitas Vaelindra - The Violet Sovereign)
            fire_d = (85, 20, 145)
            fire_m = (170, 55, 230)
            fire_l = (220, 130, 255)
            fire_h = (245, 190, 255)
            glow_color = (220, 130, 255, 25)
        elif theme_name == "Crimson Dominion":
            # Api darah (identitas Morthraxis - The Crimson Sovereign)
            fire_d = (160, 25, 50)
            fire_m = (220, 50, 90)
            fire_l = (255, 90, 130)
            fire_h = (255, 180, 200)
            glow_color = (255, 90, 130, 25)
        else:  # Forest
            fire_d = FIRE_D
            fire_m = FIRE_M
            fire_l = FIRE_L
            fire_h = FIRE_H
            glow_color = (255, 180, 80, 25)

        # Seluruh torch (batu + tiang + api + glow) di-pre-render per
        # (theme, frame animasi) -> 1 blit per torch per frame,
        # bukan puluhan draw call.
        fire_key = (fire_d, fire_m, fire_l, fire_h, glow_color)
        for i, (tx, ty) in enumerate(self.mr.torch_stones):
            frame = (t // 6 + i) % 4
            key = ("torch", fire_key, frame)

            def build():
                s = pygame.Surface((60, 60), pygame.SRCALPHA)
                ox, oy = 30, 26  # lokal (tx, ty) -> (30, 26)
                # Stone bracket
                pygame.draw.rect(s, OUTLINE, (ox - 3, oy + 2, 6, 8))
                pygame.draw.rect(s, STONE_DARK, (ox - 3, oy + 2, 6, 7))
                pygame.draw.rect(s, STONE_MID, (ox - 2, oy + 3, 4, 5))
                # Torch pole
                pygame.draw.rect(s, OUTLINE, (ox - 1, oy - 2, 2, 4))
                pygame.draw.rect(s, (60, 40, 20), (ox - 1, oy - 2, 2, 4))
                # Flame
                if frame == 0:
                    self._draw_flame_a(s, ox, oy - 2,
                                       fire_d, fire_m, fire_l, fire_h)
                elif frame == 1:
                    self._draw_flame_b(s, ox, oy - 2,
                                       fire_d, fire_m, fire_l, fire_h)
                elif frame == 2:
                    self._draw_flame_c(s, ox, oy - 2,
                                       fire_d, fire_m, fire_l, fire_h)
                else:
                    self._draw_flame_b(s, ox, oy - 2,
                                       fire_d, fire_m, fire_l, fire_h)
                # Glow
                glow_size = 22 + (frame % 2) * 3
                for r in range(glow_size, 0, -4):
                    alpha = 25 - r
                    if alpha > 0:
                        pygame.draw.circle(s, glow_color,
                                           (ox, oy - 6), r)
                return s

            torch_surf = self._cached_surf(key, build)
            surface.blit(torch_surf, (tx - 30, ty - 26))

    def _draw_flame_a(self, surface, tx, ty, d, m, l, h):
        pygame.draw.rect(surface, d, (tx - 4, ty - 6, 8, 8))
        pygame.draw.rect(surface, d, (tx - 3, ty - 10, 6, 4))
        pygame.draw.rect(surface, d, (tx - 2, ty - 14, 4, 4))
        pygame.draw.rect(surface, m, (tx - 3, ty - 5, 6, 6))
        pygame.draw.rect(surface, m, (tx - 2, ty - 9, 4, 4))
        pygame.draw.rect(surface, l, (tx - 2, ty - 4, 4, 4))
        pygame.draw.rect(surface, l, (tx - 1, ty - 8, 2, 4))
        pygame.draw.rect(surface, h, (tx - 1, ty - 3, 2, 2))

    def _draw_flame_b(self, surface, tx, ty, d, m, l, h):
        pygame.draw.rect(surface, d, (tx - 4, ty - 7, 8, 8))
        pygame.draw.rect(surface, d, (tx - 3, ty - 11, 6, 4))
        pygame.draw.rect(surface, m, (tx - 3, ty - 6, 6, 6))
        pygame.draw.rect(surface, m, (tx - 2, ty - 10, 4, 4))
        pygame.draw.rect(surface, l, (tx - 2, ty - 5, 4, 4))
        pygame.draw.rect(surface, h, (tx - 1, ty - 4, 2, 2))

    def _draw_flame_c(self, surface, tx, ty, d, m, l, h):
        pygame.draw.rect(surface, d, (tx - 4, ty - 6, 8, 8))
        pygame.draw.rect(surface, d, (tx - 3, ty - 10, 6, 4))
        pygame.draw.rect(surface, m, (tx - 3, ty - 5, 6, 6))
        pygame.draw.rect(surface, l, (tx - 2, ty - 4, 4, 4))
        pygame.draw.rect(surface, h, (tx - 1, ty - 3, 2, 2))


# ================================


# ================================================================
# TRUE BOSS ENVIRONMENT EFFECTS - ORIGINAL DYNAMIC PIPELINE
# ================================================================

_original_dynamic_init_particles = DynamicRenderer._init_particles
_original_dynamic_update = DynamicRenderer.update
_original_dynamic_draw_particles = DynamicRenderer._draw_particles
_original_dynamic_draw = DynamicRenderer.draw


def _boss_init_particles(self):
    _original_dynamic_init_particles(self)
    particle_type = self.theme.get("particle_type", "firefly")
    for f in self.particles:
        if particle_type == "acid":
            f['vx'] = random.uniform(-0.15, 0.15)
            f['vy'] = random.uniform(-0.45, -0.15)
            f['size'] = random.choice([1, 2, 2])
        elif particle_type == "ash":
            f['vx'] = random.uniform(-0.22, 0.22)
            f['vy'] = random.uniform(0.18, 0.55)
            f['size'] = random.choice([1, 1, 2])
        elif particle_type == "spirit":
            f['vx'] = random.uniform(-0.16, 0.16)
            f['vy'] = random.uniform(-0.55, -0.20)
            f['size'] = random.choice([1, 2, 2])


def _boss_update(self, t):
    _original_dynamic_update(self, t)
    particle_type = self.theme.get("particle_type", "firefly")
    w, h = self.mr.map_width, self.mr.map_height
    for f in self.particles:
        if particle_type == "acid":
            if f['y'] < 30:
                f['y'] = h - 25
                f['x'] = random.uniform(30, w - 30)
            f['x'] += math.sin(f['phase']) * .18
        elif particle_type == "ash":
            if f['y'] > h - 20:
                f['y'] = 28
                f['x'] = random.uniform(30, w - 30)
            f['x'] += math.sin(f['phase'] * .7) * .12
        elif particle_type == "spirit":
            if f['y'] < 28:
                f['y'] = h - 30
                f['x'] = random.uniform(30, w - 30)
            f['x'] += math.sin(f['phase']) * .22


def _boss_draw_particles(self, surface, t):
    particle_type = self.theme.get("particle_type", "firefly")
    if particle_type not in ("acid", "ash", "spirit"):
        return _original_dynamic_draw_particles(self, surface, t)

    for f in self.particles:
        x, y = int(f['x']), int(f['y'])
        color = f['color'][:3]
        if particle_type == "acid":
            # Droplet acid dengan satu highlight.
            pygame.draw.circle(surface, color, (x, y), max(1, f['size'] + 1))
            pygame.draw.rect(surface, (225, 255, 150), (x, y - 1, 1, 1))
        elif particle_type == "ash":
            # Ash motes: kecil, gelap, sesekali disinari merah.
            pygame.draw.rect(surface, color, (x, y, f['size'] + 1, f['size'] + 1))
            if math.sin(f['phase'] * 1.7) > .7:
                pygame.draw.rect(surface, (235, 100, 115), (x, y, 1, 1))
        else:
            # Spirit: soft orb + short vertical tail.
            glow = pygame.Surface((16, 22), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*color, 35), (2, 4, 12, 14))
            pygame.draw.circle(glow, (*color, 130), (8, 9), 3)
            pygame.draw.circle(glow, (220, 255, 240, 180), (7, 8), 1)
            surface.blit(glow, (x - 8, y - 10))


def _draw_boss_environment(self, surface, t):
    identity = self.theme.get("boss_identity", "")
    if self.theme.get("name") == "Haunted Veil":
        identity = "krobellus"

    if identity == "abaddon":
        for i, entry in enumerate(getattr(self.mr, "bones", [])[:10]):
            x, y = entry[0], entry[1]
            phase = t * .035 + i
            sx = int(x + math.sin(phase) * 5)
            sy = int(y - 20 + math.sin(phase * 1.4) * 4)
            pygame.draw.circle(surface, (200, 65, 85), (sx, sy), 2)
            pygame.draw.arc(surface, (117, 35, 65),
                            (sx - 7, sy - 10, 14, 16),
                            .2, 2.8, 1)

    elif identity == "alchemist":
        for i, entry in enumerate(getattr(self.mr, "rocks_mossy", [])[:12]):
            x, y = entry[0], entry[1]
            phase = (t * .025 + i * 17) % 55
            bx = int(x + math.sin(t * .03 + i) * 4)
            by = int(y - 8 - phase)
            pygame.draw.circle(surface, (157, 230, 67), (bx, by), 2, 1)
            if i % 3 == 0:
                pygame.draw.circle(surface, (225, 255, 150), (bx - 1, by - 1), 1)

    elif identity == "ignis_drachorn":
        points = getattr(self.mr, "river_points", [])
        for i in range(3, len(points), 11):
            x, y = points[(i + int(t * .025)) % len(points)]
            rise = int((t * .18 + i * 7) % 18)
            pygame.draw.circle(surface, (255, 145, 35),
                               (int(x), int(y - rise)), 2)
            pygame.draw.line(surface, (255, 230, 110),
                             (int(x), int(y - rise)),
                             (int(x + 2), int(y - rise - 5)), 1)

    elif identity == "krobellus":
        for i, entry in enumerate(getattr(self.mr, "gravestones", [])[:10]):
            x, y = entry
            phase = t * .025 + i * 1.4
            sx = int(x + math.sin(phase) * 6)
            sy = int(y - 18 - (math.sin(phase * .8) + 1) * 3)
            pygame.draw.circle(surface, (84, 230, 190), (sx, sy), 2)
            pygame.draw.arc(surface, (177, 88, 224),
                            (sx - 8, sy - 10, 16, 16), 0.2, 2.7, 1)


def _boss_dynamic_draw(self, surface, t):
    _original_dynamic_draw(self, surface, t)
    _draw_boss_environment(self, surface, t)


DynamicRenderer._init_particles = _boss_init_particles
DynamicRenderer.update = _boss_update
DynamicRenderer._draw_particles = _boss_draw_particles
DynamicRenderer.draw = _boss_dynamic_draw


# ====================================================================
# decoration_renderer.py  (tidak bisa dibungkus: merujuk 'DecorationRenderer' saat modul dimuat)
# ====================================================================
# map_components/decoration_renderer.py
# All map decorations (trees, crystals, bones, etc)
# ================================



class DecorationRenderer:
    """
    Draw semua static decorations:
    - Dark trees (pine, oak, twisted)
    - Dead trees
    - Gravestones, bones
    - Blue & red crystals
    - Ancient ruins
    - Mossy rocks, dark bushes
    - Mushrooms, glow flowers
    - Spike traps
    """

    @staticmethod
    def draw_all(surf, mr):
        """Draw semua decorations dengan theme filter"""
        theme = mr.theme

        # Base decorations (filter per theme)
        if theme.get("has_ancient_ruins"):
            DecorationRenderer._draw_ancient_ruins(surf, mr.ancient_ruins)
        if theme.get("has_rocks_mossy"):
            DecorationRenderer._draw_rocks(surf, mr.rocks_mossy, theme)
        if theme.get("has_gravestones"):
            DecorationRenderer._draw_gravestones(surf, mr.gravestones)
        if theme.get("has_bones"):
            DecorationRenderer._draw_bones(surf, mr.bones)
        if theme.get("has_dark_bushes"):
            DecorationRenderer._draw_dark_bushes(surf, mr.dark_bushes)
        if theme.get("has_spike_traps"):
            DecorationRenderer._draw_spike_traps(surf, mr.spike_traps)

        # Dead/frozen trees (theme-specific rendering)
        if theme.get("has_frozen_trees"):
            DecorationRenderer._draw_frozen_trees(surf, mr.dead_trees)
        elif theme.get("has_dead_trees"):
            DecorationRenderer._draw_dead_trees(surf, mr.dead_trees, theme)

        # Dark trees only in forest
        if theme.get("has_dark_trees"):
            DecorationRenderer._draw_dark_trees(surf, mr.dark_trees)

        # Mushrooms
        if theme.get("has_mushrooms_dark"):
            DecorationRenderer._draw_mushrooms(surf, mr.mushrooms_dark)

        # Crystals
        if theme.get("has_crystals_blue"):
            DecorationRenderer._draw_crystals_blue(surf, mr.crystals_blue)
        if theme.get("has_crystals_red"):
            # Desert: recolor red crystals to amber
            if theme["name"] == "Desert":
                DecorationRenderer._draw_crystals_amber(surf, mr.crystals_red)
            else:
                DecorationRenderer._draw_crystals_red(surf, mr.crystals_red)

        # Glow flowers
        if theme.get("has_glow_flowers"):
            DecorationRenderer._draw_glow_flowers(surf, mr.glow_flowers)

        # ═══ THEME-SPECIFIC DECORATIONS ═══
        # Desert
        if theme.get("has_cactus"):
            DecorationRenderer._draw_cactus(surf, mr.dark_trees)
        if theme.get("has_palm_trees"):
            DecorationRenderer._draw_palm_trees(surf, mr.dark_bushes)
        if theme.get("has_sand_dunes"):
            DecorationRenderer._draw_sand_dunes(surf, mr.rocks_mossy)

        # Ice
        if theme.get("has_ice_crystals"):
            DecorationRenderer._draw_ice_crystals(surf, mr.crystals_blue)
        if theme.get("has_snow_drifts"):
            DecorationRenderer._draw_snow_drifts(surf, mr.dark_bushes)

        # True-boss environmental dressing. Static and sparse: the original
        # map decoration pipeline remains intact.
        DecorationRenderer._draw_true_boss_decorations(surf, mr)
    # ═══════════════════════════════════════
    # TREES
    # ═══════════════════════════════════════

    @staticmethod
    def _draw_dark_trees(surf, trees):
        for x, y, size, variant in trees:
            pygame.draw.ellipse(surf, (0, 0, 0, 100),
                                (x - size, y + size // 2 - 2, size * 2, size))
            if variant == 0:
                DecorationRenderer._draw_dark_pine(surf, x, y, size)
            elif variant == 1:
                DecorationRenderer._draw_dark_oak(surf, x, y, size)
            else:
                DecorationRenderer._draw_twisted_tree(surf, x, y, size)

    @staticmethod
    def _draw_dark_pine(surf, x, y, size):
        trunk_w = 5
        pygame.draw.rect(surf, OUTLINE, (x - trunk_w // 2 - 1, y - 1, trunk_w + 2, size // 2 + 2))
        pygame.draw.rect(surf, TREE_TRUNK_D, (x - trunk_w // 2, y, trunk_w, size // 2))
        pygame.draw.rect(surf, TREE_TRUNK_L, (x - trunk_w // 2, y, 2, size // 2))
        for i in range(3):
            layer_size = size - i * 4
            layer_y = y - i * (size // 2)
            steps = 5
            for s in range(steps):
                w = int(layer_size * (steps - s) / steps)
                py = layer_y - int(layer_size * s / steps)
                pygame.draw.rect(surf, TREE_LEAVES_D, (x - w, py, w * 2, layer_size // steps + 1))
                pygame.draw.rect(surf, TREE_LEAVES_M, (x - w + 1, py + 1, w * 2 - 2, layer_size // steps - 1))
                if s < steps - 1:
                    pygame.draw.rect(surf, TREE_LEAVES_L, (x - w + 2, py + 2, w - 2, 2))
            for s in range(steps):
                w = int(layer_size * (steps - s) / steps)
                py = layer_y - int(layer_size * s / steps)
                pygame.draw.rect(surf, OUTLINE, (x - w, py, w * 2, layer_size // steps + 1), 1)

    @staticmethod
    def _draw_dark_oak(surf, x, y, size):
        trunk_w = 7
        pygame.draw.rect(surf, OUTLINE, (x - trunk_w // 2 - 1, y - 1, trunk_w + 2, size // 2 + 2))
        pygame.draw.rect(surf, TREE_TRUNK_D, (x - trunk_w // 2, y, trunk_w, size // 2))
        pygame.draw.rect(surf, TREE_TRUNK_L, (x - trunk_w // 2, y, 3, size // 2))
        foliage_y = y - size // 2
        clusters = [(0, 0, size), (-size // 3, -size // 4, size * 2 // 3),
                     (size // 3, -size // 4, size * 2 // 3), (0, -size // 2, size * 2 // 3)]
        for cx_off, cy_off, csize in clusters:
            pygame.draw.circle(surf, OUTLINE, (x + cx_off, foliage_y + cy_off), csize)
            pygame.draw.circle(surf, TREE_LEAVES_D, (x + cx_off, foliage_y + cy_off), csize - 1)
            pygame.draw.circle(surf, TREE_LEAVES_M, (x + cx_off - csize // 4, foliage_y + cy_off - csize // 4), csize * 2 // 3)
            pygame.draw.circle(surf, TREE_LEAVES_L, (x + cx_off - csize // 3, foliage_y + cy_off - csize // 3), csize // 3)

    @staticmethod
    def _draw_twisted_tree(surf, x, y, size):
        trunk_w = 6
        for i in range(size // 2):
            offset = int(math.sin(i * 0.3) * 2)
            pygame.draw.rect(surf, OUTLINE, (x - trunk_w // 2 - 1 + offset, y - i, trunk_w + 2, 2))
            pygame.draw.rect(surf, TREE_TRUNK_D, (x - trunk_w // 2 + offset, y - i, trunk_w, 1))
        foliage_y = y - size // 2
        pygame.draw.circle(surf, OUTLINE, (x, foliage_y), size // 2 + 1)
        pygame.draw.circle(surf, TREE_LEAVES_D, (x, foliage_y), size // 2)
        pygame.draw.circle(surf, TREE_LEAVES_M, (x - size // 4, foliage_y - size // 4), size // 3)
        pygame.draw.circle(surf, (255, 100, 100), (x - 2, foliage_y - 2), 1)
        pygame.draw.circle(surf, (255, 100, 100), (x + 2, foliage_y - 2), 1)

    @staticmethod
    def _draw_dead_trees(surf, trees, theme=None):
        """Dead trees dengan theme-aware color"""
        from map_components.palettes import (
            DEAD_TREE_1, DEAD_TREE_2, OUTLINE)

        # Desert: lighter tan color untuk dry trees
        if theme and theme.get("name") == "Desert":
            d1 = (85, 55, 30)
            d2 = (140, 100, 60)
        else:
            d1 = DEAD_TREE_1
            d2 = DEAD_TREE_2

        for x, y, size in trees:
            pygame.draw.ellipse(surf, (0, 0, 0, 80),
                                (x - size // 2, y + size // 3 - 2,
                                 size, size // 3))
            trunk_w = 4
            pygame.draw.rect(surf, OUTLINE,
                             (x - trunk_w // 2 - 1, y - size,
                              trunk_w + 2, size + 1))
            pygame.draw.rect(surf, d1,
                             (x - trunk_w // 2, y - size, trunk_w, size))
            pygame.draw.rect(surf, d2,
                             (x - trunk_w // 2, y - size, 2, size))
            branches = [
                ((x, y - size // 2),
                 (x - size // 2, y - size + 4), 3),
                ((x, y - size // 2 + 4),
                 (x + size // 2, y - size + 4), 3),
                ((x, y - size + 4),
                 (x - size // 3, y - size - 4), 2),
                ((x, y - size + 4),
                 (x + size // 3, y - size - 2), 2)]
            for (sx, sy), (ex, ey), w in branches:
                pygame.draw.line(surf, d1, (sx, sy), (ex, ey), w)
                pygame.draw.line(surf, OUTLINE, (sx, sy), (ex, ey), 1)
                pygame.draw.line(surf, d1, (ex, ey),
                                 (ex + random.randint(-3, 3),
                                  ey + random.randint(-4, 0)), 1)
    # ═══════════════════════════════════════
    # GRAVESTONES & BONES
    # ═══════════════════════════════════════

    @staticmethod
    def _draw_gravestones(surf, gravestones):
        for x, y in gravestones:
            pygame.draw.ellipse(surf, (0, 0, 0, 100), (x - 6, y + 5, 12, 4))
            pygame.draw.rect(surf, STONE_DARK, (x - 5, y + 4, 10, 3))
            pygame.draw.rect(surf, STONE_MID, (x - 5, y + 4, 10, 2))
            pygame.draw.rect(surf, OUTLINE, (x - 4, y - 6, 8, 10))
            pygame.draw.rect(surf, STONE_MID, (x - 4, y - 5, 8, 9))
            pygame.draw.rect(surf, STONE_LIGHT, (x - 4, y - 5, 3, 9))
            pygame.draw.rect(surf, STONE_HIGH, (x - 4, y - 5, 1, 5))
            pygame.draw.circle(surf, OUTLINE, (x, y - 6), 4)
            pygame.draw.circle(surf, STONE_MID, (x, y - 5), 3)
            pygame.draw.circle(surf, STONE_LIGHT, (x - 1, y - 6), 2)
            pygame.draw.rect(surf, OUTLINE, (x - 1, y - 3, 2, 5))
            pygame.draw.rect(surf, OUTLINE, (x - 2, y - 2, 4, 2))
            pygame.draw.line(surf, STONE_DARK, (x - 2, y - 1), (x + 1, y + 2), 1)

    @staticmethod
    def _draw_bones(surf, bones):
        BONE_C = (220, 210, 190)
        BONE_D = (160, 150, 130)
        for x, y, bone_type in bones:
            if bone_type == 'skull':
                pygame.draw.circle(surf, OUTLINE, (x, y), 5)
                pygame.draw.circle(surf, BONE_C, (x, y), 4)
                pygame.draw.circle(surf, BONE_D, (x, y + 1), 3)
                pygame.draw.rect(surf, OUTLINE, (x - 2, y - 1, 2, 2))
                pygame.draw.rect(surf, OUTLINE, (x + 1, y - 1, 2, 2))
                pygame.draw.rect(surf, BONE_C, (x - 3, y + 2, 6, 2))
                pygame.draw.line(surf, OUTLINE, (x - 1, y + 2), (x - 1, y + 4), 1)
                pygame.draw.line(surf, OUTLINE, (x + 1, y + 2), (x + 1, y + 4), 1)
            elif bone_type == 'rib':
                pygame.draw.line(surf, BONE_D, (x - 5, y), (x + 5, y), 2)
                pygame.draw.line(surf, BONE_C, (x - 5, y), (x + 5, y), 1)
                for rib_x in range(-4, 5, 2):
                    pygame.draw.line(surf, BONE_D, (x + rib_x, y - 2), (x + rib_x, y + 2), 1)
            else:
                pygame.draw.circle(surf, BONE_C, (x, y - 3), 3)
                pygame.draw.rect(surf, BONE_D, (x - 3, y, 6, 4))
                pygame.draw.line(surf, BONE_D, (x - 4, y + 2), (x - 2, y + 5), 1)
                pygame.draw.line(surf, BONE_D, (x + 4, y + 2), (x + 2, y + 5), 1)

    # ═══════════════════════════════════════
    # RUINS, ROCKS, BUSHES
    # ═══════════════════════════════════════

    @staticmethod
    def _draw_ancient_ruins(surf, ruins):
        for x, y, variant in ruins:
            if variant == 'pillar':
                pygame.draw.rect(surf, OUTLINE, (x - 4, y - 15, 8, 17))
                pygame.draw.rect(surf, STONE_DARK, (x - 3, y - 14, 6, 15))
                pygame.draw.rect(surf, STONE_MID, (x - 3, y - 14, 6, 12))
                pygame.draw.rect(surf, STONE_LIGHT, (x - 3, y - 14, 2, 12))
                pygame.draw.polygon(surf, OUTLINE, [(x - 4, y - 15), (x - 2, y - 18), (x + 1, y - 16), (x + 3, y - 19), (x + 4, y - 15)])
                pygame.draw.rect(surf, OUTLINE, (x - 6, y, 12, 4))
                pygame.draw.rect(surf, STONE_MID, (x - 5, y + 1, 10, 3))
            elif variant == 'arch':
                pygame.draw.rect(surf, OUTLINE, (x - 8, y - 10, 3, 12))
                pygame.draw.rect(surf, STONE_MID, (x - 7, y - 9, 2, 11))
                pygame.draw.rect(surf, OUTLINE, (x + 5, y - 10, 3, 12))
                pygame.draw.rect(surf, STONE_MID, (x + 6, y - 9, 2, 11))
                pygame.draw.rect(surf, OUTLINE, (x - 8, y - 12, 5, 3))
                pygame.draw.rect(surf, STONE_MID, (x - 7, y - 11, 3, 2))
            else:
                pygame.draw.rect(surf, OUTLINE, (x - 6, y - 8, 12, 10))
                pygame.draw.rect(surf, STONE_DARK, (x - 5, y - 7, 10, 9))
                pygame.draw.rect(surf, STONE_MID, (x - 5, y - 7, 10, 6))
                pygame.draw.rect(surf, STONE_LIGHT, (x - 5, y - 7, 4, 6))
                pygame.draw.line(surf, OUTLINE, (x - 3, y - 5), (x + 2, y), 1)
                pygame.draw.line(surf, OUTLINE, (x, y - 3), (x - 3, y + 1), 1)

    @staticmethod
    def _draw_rocks(surf, rocks, theme):
        """Rocks dengan theme-aware moss color"""
        from map_components.palettes import (
            STONE_DARK, STONE_MID, STONE_LIGHT, STONE_HIGH, OUTLINE)

        # Theme-specific moss color
        theme_name = theme.get("name", "Forest")
        if theme_name == "Desert":
            moss_color = (140, 110, 55)  # dry
            moss_light = (170, 140, 75)
        elif theme_name == "Ice":
            moss_color = (150, 180, 210)  # ice
            moss_light = (200, 220, 240)
        else:
            moss_color = theme.get("radiant_moss", (55, 90, 40))
            moss_light = (140, 175, 90)

        for x, y, size, has_moss in rocks:
            pygame.draw.ellipse(surf, (0, 0, 0, 80),
                                (x - size, y + size // 2 - 2,
                                 size * 2, size // 2))
            pygame.draw.rect(surf, OUTLINE,
                             (x - size, y - size + 4,
                              size * 2, size * 2 - 4))
            pygame.draw.rect(surf, STONE_DARK,
                             (x - size + 1, y - size + 5,
                              size * 2 - 2, size * 2 - 6))
            pygame.draw.rect(surf, STONE_MID,
                             (x - size + 2, y - size + 6,
                              size * 2 - 4, size * 2 - 8))
            pygame.draw.rect(surf, STONE_LIGHT,
                             (x - size + 2, y - size + 6, size, size))
            pygame.draw.rect(surf, STONE_HIGH,
                             (x - size + 3, y - size + 7,
                              size // 2, size // 2))
            if has_moss:
                pygame.draw.rect(surf, moss_color,
                                 (x - size + 2, y - size + 5, size, 3))
                pygame.draw.rect(surf, moss_light,
                                 (x - size + 2, y - size + 5, size, 2))
                for drip_i in range(3):
                    dx = x - size + 4 + drip_i * (size // 2)
                    dy = y - size + 6
                    pygame.draw.rect(surf, moss_color, (dx, dy, 1, 3))

    @staticmethod
    def _draw_dark_bushes(surf, bushes):
        for x, y, size in bushes:
            pygame.draw.ellipse(surf, (0, 0, 0, 80), (x - size, y + size - 2, size * 2, size // 2))
            clusters = [(x - size + 4, y - 2, size, size), (x - 2, y - size + 2, size, size - 2), (x + 2, y - 4, size - 4, size + 2)]
            for cx, cy, cw, ch in clusters:
                pygame.draw.circle(surf, OUTLINE, (cx, cy), cw // 2 + 1)
                pygame.draw.circle(surf, TREE_LEAVES_D, (cx, cy), cw // 2)
                pygame.draw.circle(surf, TREE_LEAVES_M, (cx - 2, cy - 2), cw // 3)
            if random.Random(x * y).random() > 0.5:
                for _ in range(3):
                    bx = x + random.Random(x + y).randint(-size // 2, size // 2)
                    by = y + random.Random(x - y).randint(-size // 3, size // 3)
                    pygame.draw.circle(surf, (100, 20, 40), (bx, by), 2)
                    pygame.draw.rect(surf, (200, 80, 120), (bx, by - 1, 1, 1))

    @staticmethod
    def _draw_spike_traps(surf, traps):
        for x, y in traps:
            pygame.draw.ellipse(surf, OUTLINE, (x - 8, y - 2, 16, 6))
            pygame.draw.ellipse(surf, DIRE_BURNT, (x - 7, y - 1, 14, 5))
            for spike_i in range(4):
                sx = x - 6 + spike_i * 4
                pygame.draw.polygon(surf, OUTLINE, [(sx - 2, y), (sx + 2, y), (sx, y - 7)])
                pygame.draw.polygon(surf, STONE_MID, [(sx - 1, y - 1), (sx + 1, y - 1), (sx, y - 6)])
                pygame.draw.rect(surf, (150, 20, 20), (sx, y - 6, 1, 2))

    # ═══════════════════════════════════════
    # MUSHROOMS, CRYSTALS, FLOWERS
    # ═══════════════════════════════════════

    @staticmethod
    def _draw_mushrooms(surf, mushrooms):
        for x, y, color in mushrooms:
            pygame.draw.rect(surf, (100, 90, 80), (x - 2, y - 1, 4, 6))
            pygame.draw.rect(surf, (60, 55, 50), (x - 2, y - 1, 1, 6))
            pygame.draw.rect(surf, OUTLINE, (x - 5, y - 5, 10, 4))
            pygame.draw.rect(surf, color, (x - 4, y - 4, 8, 3))
            lighter = tuple(min(255, c + 60) for c in color)
            pygame.draw.rect(surf, lighter, (x - 4, y - 4, 4, 2))
            pygame.draw.rect(surf, (240, 230, 210), (x - 2, y - 3, 2, 1))
            pygame.draw.rect(surf, (240, 230, 210), (x + 1, y - 2, 1, 1))

    @staticmethod
    def _draw_crystals_blue(surf, crystals):
        for x, y, size in crystals:
            for r in range(size + 6, size - 2, -2):
                alpha = 30 - (size + 6 - r) * 5
                if alpha > 0:
                    glow_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (*CRYSTAL_BLUE_L[:3], alpha), (r, r), r)
                    surf.blit(glow_surf, (x - r, y - r))
            pygame.draw.ellipse(surf, OUTLINE, (x - size - 1, y + 1, size * 2 + 2, 5))
            pygame.draw.ellipse(surf, STONE_DARK, (x - size, y + 1, size * 2, 4))
            pts = [(x, y - size), (x + size // 2, y - size // 2), (x + size // 3, y + 2), (x - size // 3, y + 2), (x - size // 2, y - size // 2)]
            pygame.draw.polygon(surf, OUTLINE, pts)
            inner_pts = [(x, y - size + 1), (x + size // 2 - 1, y - size // 2), (x + size // 3 - 1, y + 1), (x - size // 3 + 1, y + 1), (x - size // 2 + 1, y - size // 2)]
            pygame.draw.polygon(surf, CRYSTAL_BLUE_M, inner_pts)
            pygame.draw.polygon(surf, CRYSTAL_BLUE_L, [(x, y - size + 1), (x - size // 4, y - size // 3), (x - size // 3 + 1, y + 1), (x - size // 2 + 1, y - size // 2)])
            pygame.draw.polygon(surf, CRYSTAL_BLUE_H, [(x, y - size + 1), (x - size // 4, y - size // 3), (x - size // 6, y - size // 4), (x - size // 5, y - size // 5)])
            pygame.draw.rect(surf, (255, 255, 255), (x - size // 4, y - size // 2, 1, 1))
            for side_off in [-1, 1]:
                sx = x + side_off * (size // 2 + 2)
                sy = y + 1
                pygame.draw.polygon(surf, OUTLINE, [(sx, sy - size // 2), (sx + 2, sy - 1), (sx - 2, sy - 1)])
                pygame.draw.polygon(surf, CRYSTAL_BLUE_M, [(sx, sy - size // 2 + 1), (sx + 1, sy - 1), (sx - 1, sy - 1)])

    @staticmethod
    def _draw_crystals_red(surf, crystals):
        for x, y, size in crystals:
            for r in range(size + 6, size - 2, -2):
                alpha = 40 - (size + 6 - r) * 6
                if alpha > 0:
                    glow_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (*CRYSTAL_RED_L[:3], alpha), (r, r), r)
                    surf.blit(glow_surf, (x - r, y - r))
            pygame.draw.ellipse(surf, OUTLINE, (x - size - 1, y + 1, size * 2 + 2, 5))
            pygame.draw.ellipse(surf, DIRE_BURNT, (x - size, y + 1, size * 2, 4))
            pts = [(x, y - size), (x + size // 3, y - size // 2), (x + size // 2, y - 2), (x + size // 4, y + 2), (x - size // 4, y + 2), (x - size // 2, y - 2), (x - size // 3, y - size // 2)]
            pygame.draw.polygon(surf, OUTLINE, pts)
            inner_pts = [(px + (1 if px < x else -1), py + (1 if py < y else -1)) for px, py in pts]
            pygame.draw.polygon(surf, CRYSTAL_RED_M, inner_pts)
            pygame.draw.polygon(surf, CRYSTAL_RED_L, [(x, y - size + 1), (x - size // 4, y - size // 3), (x - size // 3 + 1, y - 2), (x - size // 2 + 1, y - size // 2)])
            pygame.draw.polygon(surf, CRYSTAL_RED_H, [(x, y - size + 1), (x - size // 5, y - size // 3), (x - size // 6, y - size // 4)])
            pygame.draw.line(surf, OUTLINE, (x, y - size + 2), (x + 1, y), 1)

    @staticmethod
    def _draw_glow_flowers(surf, flowers):
        for x, y, color in flowers:
            for r in range(6, 2, -1):
                alpha = 40 - r * 5
                if alpha > 0:
                    glow_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (*color[:3], alpha), (r, r), r)
                    surf.blit(glow_surf, (x - r, y - r))
            pygame.draw.rect(surf, (30, 60, 30), (x, y - 4, 1, 5))
            pygame.draw.rect(surf, (60, 100, 50), (x - 2, y - 1, 3, 2))
            pygame.draw.rect(surf, color, (x - 2, y - 6, 5, 2))
            pygame.draw.rect(surf, color, (x - 1, y - 8, 3, 5))
            lighter = tuple(min(255, c + 60) for c in color[:3])
            pygame.draw.rect(surf, lighter, (x - 1, y - 7, 2, 2))
            pygame.draw.rect(surf, (255, 240, 100), (x, y - 6, 1, 1))

    # ═══════════════════════════════════════
    # DESERT-SPECIFIC DECORATIONS
    # ═══════════════════════════════════════

    @staticmethod
    def _draw_cactus(surf, positions):
        """Cactus di posisi dark_trees (desert)"""
        from map_components.palettes import OUTLINE

        cactus_dark = (35, 75, 40)
        cactus_mid = (60, 115, 55)
        cactus_light = (95, 155, 75)
        cactus_high = (140, 195, 110)
        spike_color = (255, 240, 180)

        for x, y, size, variant in positions:
            # Main body (tall vertical)
            body_h = size + 8
            body_w = max(6, size // 3)

            # Shadow
            pygame.draw.ellipse(surf, (0, 0, 0, 100),
                                (x - body_w, y + size // 2 - 2,
                                 body_w * 2, size // 2))

            # Outline
            pygame.draw.rect(surf, OUTLINE,
                             (x - body_w - 1, y - body_h + 2,
                              body_w * 2 + 2, body_h))

            # Main body
            pygame.draw.rect(surf, cactus_dark,
                             (x - body_w, y - body_h + 2,
                              body_w * 2, body_h))
            pygame.draw.rect(surf, cactus_mid,
                             (x - body_w, y - body_h + 2,
                              body_w * 2 - 1, body_h - 1))
            pygame.draw.rect(surf, cactus_light,
                             (x - body_w, y - body_h + 2,
                              body_w, body_h - 2))
            pygame.draw.rect(surf, cactus_high,
                             (x - body_w, y - body_h + 2, 2, body_h - 3))

            # Vertical ridges
            for ridge_x in range(-body_w + 2, body_w, 3):
                pygame.draw.line(surf, cactus_dark,
                                 (x + ridge_x, y - body_h + 3),
                                 (x + ridge_x, y - 2), 1)

            # 2 arms (kiri kanan)
            if variant == 0 or variant == 1:
                # Left arm
                arm_y = y - body_h // 2
                pygame.draw.rect(surf, OUTLINE,
                                 (x - body_w - 5, arm_y - 1, 5, 6))
                pygame.draw.rect(surf, cactus_dark,
                                 (x - body_w - 4, arm_y, 4, 5))
                pygame.draw.rect(surf, cactus_mid,
                                 (x - body_w - 4, arm_y, 3, 4))

                # Arm goes up
                pygame.draw.rect(surf, OUTLINE,
                                 (x - body_w - 5, arm_y - 8,
                                  5, 9))
                pygame.draw.rect(surf, cactus_dark,
                                 (x - body_w - 4, arm_y - 7,
                                  4, 8))
                pygame.draw.rect(surf, cactus_mid,
                                 (x - body_w - 4, arm_y - 7,
                                  3, 7))
                pygame.draw.rect(surf, cactus_light,
                                 (x - body_w - 4, arm_y - 7,
                                  1, 7))

            if variant == 0 or variant == 2:
                # Right arm
                arm_y = y - body_h // 2 - 3
                pygame.draw.rect(surf, OUTLINE,
                                 (x + body_w, arm_y - 1, 5, 6))
                pygame.draw.rect(surf, cactus_dark,
                                 (x + body_w, arm_y, 4, 5))
                pygame.draw.rect(surf, cactus_mid,
                                 (x + body_w + 1, arm_y, 2, 4))

                # Arm goes up
                pygame.draw.rect(surf, OUTLINE,
                                 (x + body_w, arm_y - 10,
                                  5, 11))
                pygame.draw.rect(surf, cactus_dark,
                                 (x + body_w, arm_y - 9,
                                  4, 10))
                pygame.draw.rect(surf, cactus_mid,
                                 (x + body_w + 1, arm_y - 9,
                                  2, 9))

            # Spikes/thorns (small dots)
            for _ in range(6):
                sx = x + random.randint(-body_w, body_w)
                sy = y - random.randint(2, body_h - 2)
                pygame.draw.rect(surf, spike_color, (sx, sy, 1, 1))

            # Flower on top (opsional)
            if variant == 1:
                pygame.draw.circle(surf, (255, 100, 100),
                                   (x, y - body_h), 2)
                pygame.draw.rect(surf, (255, 220, 100),
                                 (x, y - body_h, 1, 1))

    @staticmethod
    def _draw_palm_trees(surf, positions):
        """Palm trees (di posisi dark_bushes untuk desert)"""
        from map_components.palettes import OUTLINE

        trunk_dark = (70, 45, 25)
        trunk_mid = (110, 75, 45)
        trunk_light = (150, 105, 65)
        leaf_dark = (45, 90, 35)
        leaf_mid = (75, 135, 55)
        leaf_light = (110, 175, 85)

        for x, y, size in positions:
            # Shadow
            pygame.draw.ellipse(surf, (0, 0, 0, 100),
                                (x - size, y + size - 2,
                                 size * 2, size // 2))

            # Trunk (curved)
            trunk_h = size + 12
            trunk_w = 3

            for i in range(trunk_h):
                curve = int(math.sin(i * 0.15) * 2)
                ty = y - i
                tx = x + curve

                pygame.draw.rect(surf, OUTLINE,
                                 (tx - trunk_w - 1, ty,
                                  trunk_w * 2 + 2, 1))
                pygame.draw.rect(surf, trunk_dark,
                                 (tx - trunk_w, ty,
                                  trunk_w * 2, 1))
                pygame.draw.rect(surf, trunk_mid,
                                 (tx - trunk_w + 1, ty,
                                  trunk_w * 2 - 2, 1))
                pygame.draw.rect(surf, trunk_light,
                                 (tx - trunk_w + 1, ty, 1, 1))

            # Trunk rings
            for ring_i in range(1, trunk_h // 4):
                ry = y - ring_i * 4
                curve = int(math.sin(ring_i * 4 * 0.15) * 2)
                pygame.draw.line(surf, trunk_dark,
                                 (x + curve - trunk_w, ry),
                                 (x + curve + trunk_w, ry), 1)

            # Palm leaves (fronds spreading out from top)
            top_x = x + int(math.sin(trunk_h * 0.15) * 2)
            top_y = y - trunk_h

            leaves = [
                # (angle_deg, length)
                (-90, 12),
                (-60, 14),
                (-30, 12),
                (0, 14),
                (30, 12),
                (60, 14),
                (90, 12),
                (120, 14),
                (150, 12),
                (180, 14),
                (-150, 12),
                (-120, 14),
            ]

            for angle_deg, length in leaves:
                angle = math.radians(angle_deg - 90)
                for step in range(length):
                    lx = top_x + int(math.cos(angle) * step)
                    ly_start = top_y
                    ly_end = top_y + int(math.sin(angle) * step)

                    # Add downward droop
                    droop = int(step * step * 0.05)
                    ly_end += droop

                    # Draw leaf pixel
                    pygame.draw.rect(surf, leaf_dark,
                                     (lx, ly_end, 2, 2))
                    if step < length - 2:
                        pygame.draw.rect(surf, leaf_mid,
                                         (lx, ly_end, 2, 1))
                    if step < length // 2:
                        pygame.draw.rect(surf, leaf_light,
                                         (lx, ly_end, 1, 1))

    @staticmethod
    def _draw_sand_dunes(surf, positions):
        """Sand dunes (di posisi rocks untuk desert)"""
        sand_dark = (155, 115, 60)
        sand_mid = (195, 160, 100)
        sand_light = (230, 200, 140)
        sand_high = (250, 225, 170)

        for x, y, size, has_moss in positions[:12]:  # limit
            # Dune shape (elongated ellipse)
            dune_w = size * 2 + 5
            dune_h = size

            # Base shadow
            pygame.draw.ellipse(surf, (0, 0, 0, 60),
                                (x - dune_w // 2, y + 2,
                                 dune_w, dune_h // 2))

            # Dune layers
            pygame.draw.ellipse(surf, sand_dark,
                                (x - dune_w // 2, y - 2,
                                 dune_w, dune_h))
            pygame.draw.ellipse(surf, sand_mid,
                                (x - dune_w // 2 + 1, y - 1,
                                 dune_w - 2, dune_h - 2))
            pygame.draw.ellipse(surf, sand_light,
                                (x - dune_w // 2 + 2, y - 1,
                                 dune_w - 4, dune_h // 2))
            pygame.draw.ellipse(surf, sand_high,
                                (x - dune_w // 2 + 3, y - 1,
                                 dune_w // 2, 3))

    @staticmethod
    def _draw_crystals_amber(surf, crystals):
        """Amber/orange crystals (untuk desert)"""
        from map_components.palettes import OUTLINE

        amber_dark = (140, 70, 20)
        amber_mid = (210, 140, 40)
        amber_light = (245, 200, 100)
        amber_high = (255, 240, 180)

        for x, y, size in crystals:
            # Glow
            for r in range(size + 4, size - 2, -2):
                alpha = 30 - (size + 4 - r) * 5
                if alpha > 0:
                    glow_surf = pygame.Surface(
                        (r * 2, r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf,
                                       (*amber_mid, alpha),
                                       (r, r), r)
                    surf.blit(glow_surf, (x - r, y - r))

            # Base
            pygame.draw.ellipse(surf, OUTLINE,
                                (x - size - 1, y + 1,
                                 size * 2 + 2, 5))
            pygame.draw.ellipse(surf, (95, 55, 20),
                                (x - size, y + 1, size * 2, 4))

            # Crystal shape
            pts = [
                (x, y - size),
                (x + size // 3, y - size // 2),
                (x + size // 2, y - 2),
                (x + size // 4, y + 2),
                (x - size // 4, y + 2),
                (x - size // 2, y - 2),
                (x - size // 3, y - size // 2),
            ]
            pygame.draw.polygon(surf, OUTLINE, pts)

            inner_pts = [(px + (1 if px < x else -1),
                          py + (1 if py < y else -1))
                         for px, py in pts]
            pygame.draw.polygon(surf, amber_mid, inner_pts)

            # Highlight
            pygame.draw.polygon(surf, amber_light, [
                (x, y - size + 1),
                (x - size // 4, y - size // 3),
                (x - size // 3 + 1, y - 2),
                (x - size // 2 + 1, y - size // 2),
            ])

            # Sharp shine
            pygame.draw.polygon(surf, amber_high, [
                (x, y - size + 1),
                (x - size // 5, y - size // 3),
                (x - size // 6, y - size // 4),
            ])
            pygame.draw.rect(surf, (255, 255, 200),
                             (x, y - size + 2, 1, 1))

    # ═══════════════════════════════════════
    # ICE-SPECIFIC DECORATIONS
    # ═══════════════════════════════════════

    @staticmethod
    def _draw_frozen_trees(surf, trees):
        """Frozen dead trees (Ice theme replacement)"""
        from map_components.palettes import OUTLINE

        trunk_dark = (60, 80, 105)
        trunk_mid = (100, 130, 160)
        trunk_light = (150, 180, 205)
        ice_color = (180, 220, 245)
        ice_bright = (230, 245, 255)

        for x, y, size in trees:
            pygame.draw.ellipse(surf, (0, 0, 0, 80),
                                (x - size // 2, y + size // 3 - 2,
                                 size, size // 3))

            # Trunk
            trunk_w = 4
            pygame.draw.rect(surf, OUTLINE,
                             (x - trunk_w // 2 - 1, y - size,
                              trunk_w + 2, size + 1))
            pygame.draw.rect(surf, trunk_dark,
                             (x - trunk_w // 2, y - size,
                              trunk_w, size))
            pygame.draw.rect(surf, trunk_mid,
                             (x - trunk_w // 2, y - size, 2, size))
            pygame.draw.rect(surf, trunk_light,
                             (x - trunk_w // 2, y - size, 1, size))

            # Ice covering trunk
            for i in range(0, size, 4):
                ice_y = y - i
                pygame.draw.rect(surf, ice_color,
                                 (x - trunk_w // 2 - 1, ice_y, 2, 2))

            # Frozen branches
            branches = [
                ((x, y - size // 2),
                 (x - size // 2, y - size + 4), 3),
                ((x, y - size // 2 + 4),
                 (x + size // 2, y - size + 4), 3),
                ((x, y - size + 4),
                 (x - size // 3, y - size - 4), 2),
                ((x, y - size + 4),
                 (x + size // 3, y - size - 2), 2)]

            for (sx, sy), (ex, ey), w in branches:
                # Base branch
                pygame.draw.line(surf, trunk_dark,
                                 (sx, sy), (ex, ey), w)
                pygame.draw.line(surf, OUTLINE,
                                 (sx, sy), (ex, ey), 1)

                # Ice coating (bright)
                pygame.draw.line(surf, ice_color,
                                 (sx, sy - 1), (ex, ey - 1), 1)

                # Icicles hanging (some branches)
                if random.random() > 0.5:
                    icicle_x = (sx + ex) // 2
                    icicle_y = max(sy, ey) + 1
                    icicle_h = random.randint(3, 6)
                    pygame.draw.polygon(surf, ice_color, [
                        (icicle_x - 1, icicle_y),
                        (icicle_x, icicle_y + icicle_h),
                        (icicle_x + 1, icicle_y),
                    ])
                    pygame.draw.polygon(surf, ice_bright, [
                        (icicle_x, icicle_y),
                        (icicle_x, icicle_y + icicle_h - 1),
                        (icicle_x + 1, icicle_y),
                    ])

            # Snow on top
            pygame.draw.rect(surf, ice_bright,
                             (x - trunk_w // 2, y - size - 1,
                              trunk_w, 2))

    @staticmethod
    def _draw_ice_crystals(surf, crystals):
        """Extra big ice crystals cluster (Ice theme bonus)"""
        from map_components.palettes import OUTLINE

        ice_darkest = (25, 55, 100)
        ice_dark = (55, 100, 165)
        ice_mid = (100, 160, 220)
        ice_light = (160, 210, 245)
        ice_bright = (220, 240, 255)
        ice_core = (250, 253, 255)

        # Extra crystal cluster (top of existing crystals)
        for i, (x, y, size) in enumerate(crystals[:8]):
            # Extra spike beside main crystal
            extra_x = x + (10 if i % 2 == 0 else -10)
            extra_size = size - 2

            if extra_size < 4:
                continue

            # Glow
            for r in range(extra_size + 4, extra_size - 2, -2):
                alpha = 40 - (extra_size + 4 - r) * 6
                if alpha > 0:
                    glow_surf = pygame.Surface(
                        (r * 2, r * 3), pygame.SRCALPHA)
                    pygame.draw.ellipse(glow_surf,
                                        (*ice_light, alpha),
                                        (0, 0, r * 2, r * 3))
                    surf.blit(glow_surf,
                              (extra_x - r, y - r * 3 + extra_size))

            # Crystal shape (tall spike)
            pts = [
                (extra_x - extra_size // 2, y),
                (extra_x, y - extra_size * 2),
                (extra_x + extra_size // 2, y),
            ]

            # Shadow
            shadow_pts = [(p[0] + 1, p[1] + 1) for p in pts]
            pygame.draw.polygon(surf, (10, 20, 40), shadow_pts)

            # Layers
            pygame.draw.polygon(surf, ice_darkest, pts)
            pygame.draw.polygon(surf, ice_dark, [
                (extra_x - extra_size // 2 + 1, y),
                (extra_x, y - extra_size * 2 + 1),
                (extra_x + extra_size // 2 - 1, y),
            ])
            pygame.draw.polygon(surf, ice_mid, [
                (extra_x - extra_size // 3, y - 1),
                (extra_x, y - extra_size * 2 + 2),
                (extra_x + extra_size // 3, y - 1),
            ])

            # Highlight
            pygame.draw.polygon(surf, ice_light, [
                (extra_x - extra_size // 3, y - 1),
                (extra_x, y - extra_size * 2 + 2),
                (extra_x - 1, y - extra_size),
                (extra_x - 2, y - 2),
            ])

            # Sharp tip
            pygame.draw.rect(surf, ice_core,
                             (extra_x, y - extra_size * 2 + 1, 1, 3))
            pygame.draw.rect(surf, ice_bright,
                             (extra_x, y - extra_size * 2 + 1, 1, 1))

    @staticmethod
    def _draw_snow_drifts(surf, positions):
        """Snow drifts (di posisi dark_bushes untuk ice)"""
        snow_shadow = (180, 200, 220)
        snow_mid = (220, 235, 245)
        snow_light = (240, 250, 255)
        snow_bright = (255, 255, 255)

        for x, y, size in positions:
            # Elongated snow pile
            drift_w = size * 2 + 4
            drift_h = size + 2

            # Shadow base
            pygame.draw.ellipse(surf, (0, 0, 0, 60),
                                (x - drift_w // 2, y,
                                 drift_w, drift_h // 2))

            # Snow layers
            pygame.draw.ellipse(surf, snow_shadow,
                                (x - drift_w // 2, y - drift_h // 2,
                                 drift_w, drift_h))
            pygame.draw.ellipse(surf, snow_mid,
                                (x - drift_w // 2 + 1,
                                 y - drift_h // 2 + 1,
                                 drift_w - 2, drift_h - 2))
            pygame.draw.ellipse(surf, snow_light,
                                (x - drift_w // 2 + 2,
                                 y - drift_h // 2 + 1,
                                 drift_w - 4, drift_h // 2))
            pygame.draw.ellipse(surf, snow_bright,
                                (x - drift_w // 2 + 3,
                                 y - drift_h // 2 + 1,
                                 drift_w // 2, 2))

            # Sparkles on snow
            for _ in range(3):
                sx = x + random.randint(-drift_w // 2 + 2,
                                         drift_w // 2 - 2)
                sy = y + random.randint(-drift_h // 2 + 1, 0)
                pygame.draw.rect(surf, snow_bright, (sx, sy, 1, 1))



# ================================


# ================================================================
# TRUE BOSS ENVIRONMENTAL DRESSING - ORIGINAL MAP PIPELINE
# ================================================================

def _draw_true_boss_decorations(surf, mr):
    theme = mr.theme
    identity = theme.get("boss_identity", "")
    if theme.get("name") == "Haunted Veil":
        identity = "krobellus"

    if identity == "abaddon":
        remains = getattr(mr, "bones", [])[:12]
        for x, y, _bone_type in remains:
            # Fallen dead knight: helmet, rib cage, broken sword.
            pygame.draw.ellipse(surf, (7, 5, 10), (x - 12, y + 3, 24, 7))
            pygame.draw.circle(surf, (54, 48, 57), (x - 3, y - 2), 6)
            pygame.draw.rect(surf, (35, 30, 42), (x - 8, y - 5, 10, 6))
            pygame.draw.line(surf, (151, 131, 137), (x + 3, y - 4),
                             (x + 12, y - 19), 2)
            pygame.draw.line(surf, (203, 62, 78), (x + 9, y - 14),
                             (x + 14, y - 18), 1)
            pygame.draw.line(surf, (127, 111, 120), (x - 5, y + 2),
                             (x + 6, y + 2), 1)
            pygame.draw.line(surf, (127, 111, 120), (x - 3, y - 1),
                             (x - 4, y + 4), 1)
            pygame.draw.line(surf, (127, 111, 120), (x + 2, y - 1),
                             (x + 2, y + 4), 1)

    elif identity == "alchemist":
        rocks = getattr(mr, "rocks_mossy", [])[:14]
        for i, (x, y, size, _has_moss) in enumerate(rocks):
            radius = max(8, int(size * .75))
            pygame.draw.ellipse(surf, (8, 25, 14),
                                (x - radius - 3, y + 3, radius * 2 + 6, 8))
            pygame.draw.ellipse(surf, (35, 104, 42),
                                (x - radius, y - radius // 3,
                                 radius * 2, max(8, radius)))
            pygame.draw.ellipse(surf, (110, 190, 53),
                                (x - radius + 3, y - radius // 3 + 2,
                                 max(5, radius), max(3, radius // 3)))
            if i % 2 == 0:
                pygame.draw.circle(surf, (205, 255, 104),
                                   (x - 3, y - radius // 4), 2)
                pygame.draw.circle(surf, (143, 226, 61),
                                   (x + 5, y - radius // 2), 1)

    elif identity == "ignis_drachorn":
        rocks = getattr(mr, "rocks_mossy", [])[:14]
        for i, (x, y, size, _has_moss) in enumerate(rocks):
            r = max(7, int(size * .65))
            pygame.draw.ellipse(surf, (20, 5, 5), (x - r - 3, y + 3, r * 2 + 6, 8))
            pygame.draw.polygon(surf, (48, 18, 17), [
                (x - r, y + 3), (x - r // 2, y - r),
                (x + r, y - r // 2), (x + r // 2, y + 5),
            ])
            pygame.draw.line(surf, (235, 61, 16), (x - r // 2, y),
                             (x + r // 2, y - r // 2), 2)
            if i % 3 == 0:
                pygame.draw.circle(surf, (255, 180, 50), (x, y - r // 2), 2)

    elif identity == "ancient_apparition":
        # Existing ice decorations are already strong; add a few frost sigils.
        crystals = getattr(mr, "crystals_blue", [])[:10]
        for x, y, size in crystals:
            pygame.draw.circle(surf, (150, 230, 255), (x, y - size - 3), 2, 1)
            pygame.draw.line(surf, (220, 250, 255),
                             (x - 3, y - size - 3),
                             (x + 3, y - size - 3), 1)

    elif identity == "krobellus":
        gravestones = getattr(mr, "gravestones", [])[:12]
        for i, (x, y) in enumerate(gravestones):
            if i % 2:
                pygame.draw.circle(surf, (75, 220, 190), (x, y - 20), 3, 1)
                pygame.draw.arc(surf, (148, 77, 206),
                                (x - 8, y - 28, 16, 16), 0.2, 2.5, 1)


DecorationRenderer._draw_true_boss_decorations = staticmethod(
    _draw_true_boss_decorations
)


# Fill safe empty spaces with readable, low-density true-boss landmarks.
_original_true_boss_decorations = DecorationRenderer._draw_true_boss_decorations


def _draw_true_boss_decorations_filled(surf, mr):
    _original_true_boss_decorations(surf, mr)
    theme = mr.theme
    identity = theme.get("boss_identity", "")
    if theme.get("name") == "Haunted Veil":
        identity = "krobellus"

    for index, (x, y, variant) in enumerate(
            getattr(mr, "boss_landmarks", [])):
        x, y = int(x), int(y)

        if identity == "abaddon":
            # Dead knight remains: larger than a particle, smaller than a unit.
            pygame.draw.ellipse(surf, (6, 5, 10), (x - 13, y + 4, 26, 7))
            pygame.draw.ellipse(surf, (52, 43, 53), (x - 9, y - 4, 18, 9))
            pygame.draw.circle(surf, (70, 61, 71), (x - 8, y - 8), 5)
            pygame.draw.rect(surf, (31, 25, 35), (x - 12, y - 12, 8, 6))
            pygame.draw.line(surf, (161, 139, 145), (x + 2, y - 2),
                             (x + 13, y - 20), 2)
            pygame.draw.line(surf, (195, 55, 73), (x + 9, y - 14),
                             (x + 15, y - 19), 1)
            if variant == 0:
                pygame.draw.line(surf, (120, 104, 112), (x - 5, y - 1),
                                 (x + 7, y - 1), 1)
                pygame.draw.line(surf, (120, 104, 112), (x - 2, y - 4),
                                 (x - 4, y + 4), 1)
            if index % 6 == 0:
                pygame.draw.line(surf, (89, 24, 43), (x - 16, y - 1),
                                 (x - 16, y - 27), 2)
                pygame.draw.polygon(surf, (132, 25, 47), [
                    (x - 16, y - 26), (x - 2, y - 21),
                    (x - 16, y - 15),
                ])

        elif identity == "alchemist":
            # Acid puddle plus a small broken flask/pipe.
            pygame.draw.ellipse(surf, (8, 24, 13), (x - 15, y + 4, 30, 8))
            pygame.draw.ellipse(surf, (55, 133, 40), (x - 12, y, 24, 9))
            pygame.draw.ellipse(surf, (158, 226, 64), (x - 8, y + 1, 16, 4))
            pygame.draw.circle(surf, (218, 255, 128), (x - 5, y - 5), 2, 1)
            pygame.draw.circle(surf, (142, 226, 61), (x + 6, y - 10), 2, 1)
            if variant == 1:
                pygame.draw.line(surf, (117, 80, 38), (x + 11, y + 2),
                                 (x + 11, y - 18), 2)
                pygame.draw.circle(surf, (205, 239, 101), (x + 11, y - 20), 4, 1)

        elif identity == "ancient_apparition":
            # Frost marker / small crystal cluster.
            size = 7 + (variant % 3) * 2
            pygame.draw.ellipse(surf, (5, 17, 33), (x - 12, y + 4, 24, 7))
            pygame.draw.polygon(surf, (55, 123, 176), [
                (x, y - size), (x + size // 2, y + 3),
                (x, y + 7), (x - size // 2, y + 3),
            ])
            pygame.draw.line(surf, (220, 250, 255), (x, y - size + 2),
                             (x, y + 3), 1)
            if variant == 3:
                pygame.draw.polygon(surf, (147, 225, 255), [
                    (x - 10, y - 3), (x - 6, y - 14),
                    (x - 2, y - 3),
                ])

        elif identity == "ignis_drachorn":
            # Obsidian magma vent.
            r = 9 + variant * 2
            pygame.draw.ellipse(surf, (16, 4, 5), (x - r - 4, y + 3, r * 2 + 8, 8))
            pygame.draw.polygon(surf, (49, 18, 17), [
                (x - r, y + 3), (x - r // 2, y - r),
                (x + r, y - r // 2), (x + r // 2, y + 4),
            ])
            pygame.draw.line(surf, (241, 62, 17), (x - r // 2, y),
                             (x + r // 2, y - r // 2), 2)
            pygame.draw.circle(surf, (255, 174, 45), (x, y - r // 2), 2)
            if variant % 2 == 0:
                pygame.draw.line(surf, (255, 220, 98), (x, y - r),
                                 (x + 3, y - r - 7), 1)

        elif identity == "krobellus":
            # Compact soul marker around otherwise empty grave soil.
            pygame.draw.ellipse(surf, (5, 5, 13), (x - 12, y + 3, 24, 7))
            pygame.draw.circle(surf, (53, 161, 143), (x, y - 6), 7, 1)
            pygame.draw.circle(surf, (190, 255, 220), (x - 2, y - 8), 2)
            pygame.draw.arc(surf, (145, 70, 202),
                            (x - 13, y - 19, 26, 24), .2, 2.8, 1)

DecorationRenderer._draw_true_boss_decorations = staticmethod(
    _draw_true_boss_decorations_filled
)


# ====================================================================
# shop_renderer.py
# ====================================================================
class _NS_shop_renderer:
    """Namespace shop_renderer - isi asli tidak diubah."""

    # map_components/shop_renderer.py
    # Shop building renderer
    # ================================



    class ShopRenderer:
        """Draw shop buildings (dark fantasy style)

        radiant_pos -> ITEM FORGE (ungu, toko item hero)
        dire_pos    -> HERO SHOP  (merah, toko hero)
        """

        @staticmethod
        def draw(surf, radiant_pos, dire_pos):
            """Draw both shop buildings"""
            _NS_shop_renderer.ShopRenderer._draw_building(
                surf, radiant_pos, 'item')
            _NS_shop_renderer.ShopRenderer._draw_building(
                surf, dire_pos, 'hero')

        @staticmethod
        def _draw_building(surf, pos, kind):
            """Single dark fantasy shop building.

            kind: 'hero'  -> Dire/HERO SHOP (tampilan asli merah)
                  'item'  -> Radiant/ITEM FORGE (tampilan ungu)
            """
            cx, cy = pos

            # Warna tema per jenis toko
            if kind == 'item':
                roof_color = (70, 40, 100)
                roof_light = (120, 70, 160)
                win_color = (180, 120, 255)
                sign_color = (180, 120, 255)
                sign_text = "ITEM"
            else:
                roof_color = (80, 30, 30)
                roof_light = (130, 50, 50)
                win_color = (255, 100, 100)
                sign_color = (200, 160, 40)
                sign_text = "SHOP"

            # Ground platform
            platform_w = 70
            pygame.draw.rect(surf, OUTLINE,
                             (cx - platform_w // 2, cy + 22,
                              platform_w, 14))
            pygame.draw.rect(surf, STONE_DARK,
                             (cx - platform_w // 2 + 1, cy + 23,
                              platform_w - 2, 12))
            pygame.draw.rect(surf, STONE_MID,
                             (cx - platform_w // 2 + 2, cy + 24,
                              platform_w - 4, 3))
            for tx in range(-30, 30, 8):
                pygame.draw.rect(surf, STONE_DARK,
                                 (cx + tx, cy + 28, 1, 6))
            pygame.draw.rect(surf, OUTLINE,
                             (cx - platform_w // 2, cy + 22,
                              platform_w, 14), 2)

            # Wall (dark wood)
            wall_w = 56
            wall_h = 32
            wall_x = cx - wall_w // 2
            wall_y = cy - 10

            pygame.draw.rect(surf, OUTLINE,
                             (wall_x - 2, wall_y - 2,
                              wall_w + 4, wall_h + 4))
            pygame.draw.rect(surf, (60, 40, 30),
                             (wall_x, wall_y, wall_w, wall_h))
            pygame.draw.rect(surf, (90, 60, 40),
                             (wall_x, wall_y, 4, wall_h))
            pygame.draw.rect(surf, (120, 80, 55),
                             (wall_x, wall_y, 2, wall_h))

            # Wood planks
            for i in range(1, 4):
                plank_y = wall_y + i * 8
                pygame.draw.line(surf, (40, 25, 20),
                                 (wall_x, plank_y),
                                 (wall_x + wall_w, plank_y), 1)

            # Door
            door_w = 14
            door_h = 22
            door_x = cx - door_w // 2
            door_y = wall_y + wall_h - door_h
            pygame.draw.rect(surf, OUTLINE,
                             (door_x - 1, door_y - 1,
                              door_w + 2, door_h + 1))
            pygame.draw.rect(surf, (40, 25, 15),
                             (door_x, door_y, door_w, door_h))
            pygame.draw.rect(surf, (70, 45, 30),
                             (door_x + 1, door_y + 1,
                              door_w - 2, door_h - 2))
            pygame.draw.line(surf, (30, 15, 10),
                             (cx, door_y), (cx, door_y + door_h), 1)
            # Handle
            pygame.draw.rect(surf, (200, 160, 40),
                             (door_x + door_w - 4,
                              door_y + door_h // 2, 2, 3))
            pygame.draw.rect(surf, OUTLINE,
                             (door_x, door_y, door_w, door_h), 2)

            # Windows
            for wx_offset in [-18, 18]:
                win_x = cx + wx_offset - 4
                win_y = wall_y + 6
                pygame.draw.rect(surf, OUTLINE,
                                 (win_x - 1, win_y - 1, 10, 10))

                win_color_local = win_color

                pygame.draw.rect(surf, win_color_local,
                                 (win_x, win_y, 8, 8))
                pygame.draw.rect(surf, (255, 255, 255),
                                 (win_x, win_y, 4, 4))
                pygame.draw.line(surf, (30, 25, 20),
                                 (win_x + 4, win_y),
                                 (win_x + 4, win_y + 8), 1)
                pygame.draw.line(surf, (30, 25, 20),
                                 (win_x, win_y + 4),
                                 (win_x + 8, win_y + 4), 1)

            # Roof
            roof_h = 24
            roof_top_y = wall_y - roof_h

            # Shadow
            pygame.draw.polygon(surf, OUTLINE, [
                (wall_x - 6, wall_y + 2),
                (cx + 2, roof_top_y + 2),
                (wall_x + wall_w + 8, wall_y + 2)])

            # Main roof
            pygame.draw.polygon(surf, roof_color, [
                (wall_x - 4, wall_y),
                (cx, roof_top_y),
                (wall_x + wall_w + 4, wall_y)])
            pygame.draw.polygon(surf, roof_light, [
                (wall_x - 4, wall_y),
                (cx, roof_top_y),
                (cx, wall_y)])

            # Roof tiles
            for row in range(0, roof_h, 4):
                for col_offset in range(-30 + row, 32 - row, 6):
                    tile_y = wall_y - row
                    tile_x = cx + col_offset
                    pygame.draw.rect(surf, OUTLINE,
                                     (tile_x, tile_y, 4, 2))

            pygame.draw.polygon(surf, OUTLINE, [
                (wall_x - 4, wall_y),
                (cx, roof_top_y),
                (wall_x + wall_w + 4, wall_y)], 2)

            # Chimney
            chim_x = cx + 15
            chim_y = wall_y - 18
            pygame.draw.rect(surf, OUTLINE,
                             (chim_x - 1, chim_y - 2, 10, 3))
            pygame.draw.rect(surf, STONE_DARK,
                             (chim_x, chim_y, 8, 12))
            pygame.draw.rect(surf, STONE_MID,
                             (chim_x + 1, chim_y + 1, 6, 10))

            # Signboard "SHOP"
            sign_w = 40
            sign_h = 14
            sign_x = cx - sign_w // 2
            sign_y = roof_top_y - 24

            pygame.draw.line(surf, (60, 40, 30),
                             (sign_x + 6, sign_y),
                             (sign_x + 6, sign_y - 8), 2)
            pygame.draw.line(surf, (60, 40, 30),
                             (sign_x + sign_w - 6, sign_y),
                             (sign_x + sign_w - 6, sign_y - 8), 2)

            pygame.draw.rect(surf, OUTLINE,
                             (sign_x - 1, sign_y - 1,
                              sign_w + 2, sign_h + 2))
            if kind == 'item':
                pygame.draw.rect(surf, (40, 25, 60),
                                 (sign_x, sign_y, sign_w, sign_h))
                pygame.draw.rect(surf, (70, 45, 110),
                                 (sign_x, sign_y, sign_w, 3))
            else:
                pygame.draw.rect(surf, (60, 40, 30),
                                 (sign_x, sign_y, sign_w, sign_h))
                pygame.draw.rect(surf, (90, 60, 40),
                                 (sign_x, sign_y, sign_w, 3))

            text_y = sign_y + 4
            _NS_shop_renderer.ShopRenderer._draw_pixel_text(
                surf, sign_text, sign_x + 6, text_y, sign_color)

            pygame.draw.rect(surf, OUTLINE,
                             (sign_x, sign_y, sign_w, sign_h), 2)

        @staticmethod
        def _draw_pixel_text(surf, text, x, y, color):
            """Pixel text renderer"""
            letters = {
                'S': [(0, 0, 1, 1, 1), (1, 0, 0, 0, 0),
                      (0, 1, 1, 1, 0), (0, 0, 0, 0, 1),
                      (1, 1, 1, 1, 0)],
                'H': [(1, 0, 0, 0, 1), (1, 0, 0, 0, 1),
                      (1, 1, 1, 1, 1), (1, 0, 0, 0, 1),
                      (1, 0, 0, 0, 1)],
                'O': [(0, 1, 1, 1, 0), (1, 0, 0, 0, 1),
                      (1, 0, 0, 0, 1), (1, 0, 0, 0, 1),
                      (0, 1, 1, 1, 0)],
                'P': [(1, 1, 1, 1, 0), (1, 0, 0, 0, 1),
                      (1, 1, 1, 1, 0), (1, 0, 0, 0, 0),
                      (1, 0, 0, 0, 0)],
                'I': [(1, 1, 1, 1, 1), (0, 0, 1, 0, 0),
                      (0, 0, 1, 0, 0), (0, 0, 1, 0, 0),
                      (1, 1, 1, 1, 1)],
                'T': [(1, 1, 1, 1, 1), (0, 0, 1, 0, 0),
                      (0, 0, 1, 0, 0), (0, 0, 1, 0, 0),
                      (0, 0, 1, 0, 0)],
                'E': [(1, 1, 1, 1, 1), (1, 0, 0, 0, 0),
                      (1, 1, 1, 1, 0), (1, 0, 0, 0, 0),
                      (1, 1, 1, 1, 1)],
                'M': [(1, 0, 0, 0, 1), (1, 1, 0, 1, 1),
                      (1, 0, 1, 0, 1), (1, 0, 0, 0, 1),
                      (1, 0, 0, 0, 1)],
            }
            for i, char in enumerate(text):
                if char in letters:
                    pattern = letters[char]
                    for row_i, row in enumerate(pattern):
                        for col_i, val in enumerate(row):
                            if val:
                                pygame.draw.rect(
                                    surf, color,
                                    (x + i * 7 + col_i,
                                     y + row_i, 1, 1))





    # ================================



