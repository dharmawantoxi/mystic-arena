# map_components/__init__.py
# ================================

# ─── PENGGABUNGAN FILE ───
# Isi palettes.py, themes.py, generators.py, static_renderer.py,
# dynamic_renderer.py, decoration_renderer.py, shop_renderer.py
# sekarang ada di map_components/_bundle.py.
#
# Blok di bawah mendaftarkan nama submodul lama ke sys.modules,
# sehingga baris impor lama tetap jalan tanpa file fisiknya:
#
#     from map_components.palettes import OUTLINE
#     from map_components.themes import get_theme
#
# generators, static_renderer, shop_renderer dibungkus namespace
# (_NS_<nama>) karena simbolnya bentrok dengan modul lain.
#
# palettes, themes, dynamic_renderer, decoration_renderer TIDAK
# dibungkus: kodenya merujuk simbolnya sendiri saat modul dimuat
# (mis. THEMES = {"forest": FOREST_THEME} dan
# DynamicRenderer.update = ...), sehingga tidak bisa berada di dalam
# kelas - nama kelasnya belum terikat saat body dijalankan.
import sys as _sys
import types as _types

from map_components import _bundle as _b

# Simbol yang dulu terlihat di tiap modul (definisi sendiri + yang
# "bocor" lewat import). Didaftarkan ulang supaya isi modul sama
# persis seperti sebelum digabung - tidak lebih, tidak kurang.
_EXTRA = {'generators': ['CRYSTAL_BLUE_L', 'SCREEN_HEIGHT', 'SCREEN_WIDTH', 'TILE_SIZE', 'math', 'random'], 'static_renderer': ['OUTLINE', 'TILE_SIZE', 'math', 'pygame', 'random'], 'shop_renderer': ['CRYSTAL_BLUE_D', 'CRYSTAL_BLUE_H', 'CRYSTAL_BLUE_L', 'CRYSTAL_BLUE_M', 'CRYSTAL_RED_D', 'CRYSTAL_RED_H', 'CRYSTAL_RED_L', 'CRYSTAL_RED_M', 'DEAD_TREE_1', 'DEAD_TREE_2', 'DEAD_TREE_3', 'DIRE_ASH', 'DIRE_BURNT', 'DIRE_EARTH_1', 'DIRE_EARTH_2', 'DIRE_EARTH_3', 'DIRE_EARTH_4', 'FIRE_D', 'FIRE_H', 'FIRE_L', 'FIRE_M', 'OUTLINE', 'PATH_CRACK', 'PATH_MOSS', 'PATH_STONE_1', 'PATH_STONE_2', 'PATH_STONE_3', 'PATH_STONE_4', 'RADIANT_GRASS_1', 'RADIANT_GRASS_2', 'RADIANT_GRASS_3', 'RADIANT_GRASS_4', 'RADIANT_GRASS_HIGH', 'RADIANT_MOSS', 'RIVER_DEEP', 'RIVER_FOAM', 'RIVER_GLOW', 'RIVER_LIGHT', 'RIVER_MID', 'SHADOW', 'STONE_DARK', 'STONE_HIGH', 'STONE_LIGHT', 'STONE_MID', 'TILE_SIZE', 'TRANSITION_1', 'TRANSITION_2', 'TREE_LEAVES_D', 'TREE_LEAVES_H', 'TREE_LEAVES_L', 'TREE_LEAVES_M', 'TREE_TRUNK_D', 'TREE_TRUNK_L', 'pygame']}
_PLAIN_SYMS = {'palettes': ['CRYSTAL_BLUE_D', 'CRYSTAL_BLUE_H', 'CRYSTAL_BLUE_L', 'CRYSTAL_BLUE_M', 'CRYSTAL_RED_D', 'CRYSTAL_RED_H', 'CRYSTAL_RED_L', 'CRYSTAL_RED_M', 'DEAD_TREE_1', 'DEAD_TREE_2', 'DEAD_TREE_3', 'DIRE_ASH', 'DIRE_BURNT', 'DIRE_EARTH_1', 'DIRE_EARTH_2', 'DIRE_EARTH_3', 'DIRE_EARTH_4', 'FIRE_D', 'FIRE_H', 'FIRE_L', 'FIRE_M', 'OUTLINE', 'PATH_CRACK', 'PATH_MOSS', 'PATH_STONE_1', 'PATH_STONE_2', 'PATH_STONE_3', 'PATH_STONE_4', 'RADIANT_GRASS_1', 'RADIANT_GRASS_2', 'RADIANT_GRASS_3', 'RADIANT_GRASS_4', 'RADIANT_GRASS_HIGH', 'RADIANT_MOSS', 'RIVER_DEEP', 'RIVER_FOAM', 'RIVER_GLOW', 'RIVER_LIGHT', 'RIVER_MID', 'SHADOW', 'STONE_DARK', 'STONE_HIGH', 'STONE_LIGHT', 'STONE_MID', 'TILE_SIZE', 'TRANSITION_1', 'TRANSITION_2', 'TREE_LEAVES_D', 'TREE_LEAVES_H', 'TREE_LEAVES_L', 'TREE_LEAVES_M', 'TREE_TRUNK_D', 'TREE_TRUNK_L'], 'themes': ['ABYSSAL_THEME', 'ABYSS_THEME', 'CELESTIALPEAKS_THEME', 'COSMIC_THEME', 'CRIMSON_THEME', 'ELDRITCH_THEME', 'ETERNALFLAME_THEME', 'PRIMORDIAL_THEME', 'ROYAL_THEME', 'SANCTUM_THEME', 'VIOLET_THEME', 'DESERT_THEME', 'FOREST_THEME', 'HAUNTED_THEME', 'ICE_THEME', 'NETHERVENOM_THEME', 'OCEAN_THEME', 'RADIANT_THEME', 'SOULFORGED_THEME', 'THEMES', 'VOLCANIC_THEME', 'get_theme'], 'dynamic_renderer': ['CRYSTAL_BLUE_D', 'CRYSTAL_BLUE_H', 'CRYSTAL_BLUE_L', 'CRYSTAL_BLUE_M', 'CRYSTAL_RED_D', 'CRYSTAL_RED_H', 'CRYSTAL_RED_L', 'CRYSTAL_RED_M', 'DEAD_TREE_1', 'DEAD_TREE_2', 'DEAD_TREE_3', 'DIRE_ASH', 'DIRE_BURNT', 'DIRE_EARTH_1', 'DIRE_EARTH_2', 'DIRE_EARTH_3', 'DIRE_EARTH_4', 'DynamicRenderer', 'FIRE_D', 'FIRE_H', 'FIRE_L', 'FIRE_M', 'OUTLINE', 'PATH_CRACK', 'PATH_MOSS', 'PATH_STONE_1', 'PATH_STONE_2', 'PATH_STONE_3', 'PATH_STONE_4', 'RADIANT_GRASS_1', 'RADIANT_GRASS_2', 'RADIANT_GRASS_3', 'RADIANT_GRASS_4', 'RADIANT_GRASS_HIGH', 'RADIANT_MOSS', 'RIVER_DEEP', 'RIVER_FOAM', 'RIVER_GLOW', 'RIVER_LIGHT', 'RIVER_MID', 'SHADOW', 'STONE_DARK', 'STONE_HIGH', 'STONE_LIGHT', 'STONE_MID', 'TILE_SIZE', 'TRANSITION_1', 'TRANSITION_2', 'TREE_LEAVES_D', 'TREE_LEAVES_H', 'TREE_LEAVES_L', 'TREE_LEAVES_M', 'TREE_TRUNK_D', 'TREE_TRUNK_L', '_boss_draw_particles', '_boss_dynamic_draw', '_boss_init_particles', '_boss_update', '_draw_boss_environment', '_original_dynamic_draw', '_original_dynamic_draw_particles', '_original_dynamic_init_particles', '_original_dynamic_update', 'math', 'pygame', 'random'], 'decoration_renderer': ['CRYSTAL_BLUE_D', 'CRYSTAL_BLUE_H', 'CRYSTAL_BLUE_L', 'CRYSTAL_BLUE_M', 'CRYSTAL_RED_D', 'CRYSTAL_RED_H', 'CRYSTAL_RED_L', 'CRYSTAL_RED_M', 'DEAD_TREE_1', 'DEAD_TREE_2', 'DEAD_TREE_3', 'DIRE_ASH', 'DIRE_BURNT', 'DIRE_EARTH_1', 'DIRE_EARTH_2', 'DIRE_EARTH_3', 'DIRE_EARTH_4', 'DecorationRenderer', 'FIRE_D', 'FIRE_H', 'FIRE_L', 'FIRE_M', 'OUTLINE', 'PATH_CRACK', 'PATH_MOSS', 'PATH_STONE_1', 'PATH_STONE_2', 'PATH_STONE_3', 'PATH_STONE_4', 'RADIANT_GRASS_1', 'RADIANT_GRASS_2', 'RADIANT_GRASS_3', 'RADIANT_GRASS_4', 'RADIANT_GRASS_HIGH', 'RADIANT_MOSS', 'RIVER_DEEP', 'RIVER_FOAM', 'RIVER_GLOW', 'RIVER_LIGHT', 'RIVER_MID', 'SHADOW', 'STONE_DARK', 'STONE_HIGH', 'STONE_LIGHT', 'STONE_MID', 'TILE_SIZE', 'TRANSITION_1', 'TRANSITION_2', 'TREE_LEAVES_D', 'TREE_LEAVES_H', 'TREE_LEAVES_L', 'TREE_LEAVES_M', 'TREE_TRUNK_D', 'TREE_TRUNK_L', '_draw_true_boss_decorations', '_draw_true_boss_decorations_filled', '_original_true_boss_decorations', 'math', 'pygame', 'random']}


def _install_aliases():
    """Daftarkan map_components.<modul> ke sys.modules."""
    for _name in ['generators', 'static_renderer', 'shop_renderer']:
        _full = __name__ + "." + _name
        if _full in _sys.modules:
            continue
        _ns = getattr(_b, "_NS_" + _name)
        _mod = _types.ModuleType(_full)
        _mod.__doc__ = "map_components/%s.py (digabung)" % _name
        for _k in dir(_ns):
            if not _k.startswith("__"):
                setattr(_mod, _k, getattr(_ns, _k))
        for _k in _EXTRA.get(_name, ()):
            if not hasattr(_mod, _k) and hasattr(_b, _k):
                setattr(_mod, _k, getattr(_b, _k))
        _sys.modules[_full] = _mod
        setattr(_sys.modules[__name__], _name, _mod)

    for _name in ['palettes', 'themes', 'dynamic_renderer', 'decoration_renderer']:
        _full = __name__ + "." + _name
        if _full in _sys.modules:
            continue
        _mod = _types.ModuleType(_full)
        _mod.__doc__ = "map_components/%s.py (digabung)" % _name
        for _k in _PLAIN_SYMS.get(_name, ()):
            if hasattr(_b, _k):
                setattr(_mod, _k, getattr(_b, _k))
        _sys.modules[_full] = _mod
        setattr(_sys.modules[__name__], _name, _mod)


_install_aliases()

try:
    from map_components.palettes import *
except ImportError as e:
    print(f"[MAP WARNING] palettes failed: {e}")

try:
    from map_components.generators import PathGenerator, DecorationGenerator
except ImportError as e:
    print(f"[MAP WARNING] generators failed: {e}")

try:
    from map_components.dynamic_renderer import DynamicRenderer
except ImportError as e:
    print(f"[MAP WARNING] DynamicRenderer failed: {e}")

try:
    from map_components.shop_renderer import ShopRenderer
except ImportError as e:
    print(f"[MAP WARNING] ShopRenderer failed: {e}")

try:
    from map_components.static_renderer import StaticRenderer
except ImportError as e:
    print(f"[MAP WARNING] StaticRenderer failed: {e}")

try:
    from map_components.decoration_renderer import DecorationRenderer
except ImportError as e:
    print(f"[MAP WARNING] DecorationRenderer failed: {e}")




# ================================
