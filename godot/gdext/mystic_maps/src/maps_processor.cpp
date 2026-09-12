// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Sumber    : map_components/_bundle.py (palettes, themes, generators)
// Generator : tools/gen_maps_cpp.py (AST Python -> C++, bukan terjemahan tangan)
// Regenerasi: python3 tools/gen_maps_cpp.py
// Cek CI    : python3 tools/gen_maps_cpp.py --check
// Desain    : docs/MAPS_GODOTPP.md
#include "maps_processor.h"

#include <cmath>
#include <cstddef>
#include <cstdint>
#include <vector>

using namespace godot;

namespace {

// ── palettes.py ──
struct PalEntry {
    const char *name;
    int32_t r, g, b;
};

const PalEntry kPalettes[] = {
    {"RADIANT_GRASS_1", 28, 55, 32}, // _bundle.py:45
    {"RADIANT_GRASS_2", 38, 72, 42}, // _bundle.py:46
    {"RADIANT_GRASS_3", 52, 92, 55}, // _bundle.py:47
    {"RADIANT_GRASS_4", 68, 115, 70}, // _bundle.py:48
    {"RADIANT_GRASS_HIGH", 90, 145, 85}, // _bundle.py:49
    {"RADIANT_MOSS", 55, 90, 40}, // _bundle.py:50
    {"DIRE_EARTH_1", 45, 32, 28}, // _bundle.py:53
    {"DIRE_EARTH_2", 65, 45, 38}, // _bundle.py:54
    {"DIRE_EARTH_3", 85, 60, 48}, // _bundle.py:55
    {"DIRE_EARTH_4", 105, 78, 62}, // _bundle.py:56
    {"DIRE_ASH", 60, 55, 50}, // _bundle.py:57
    {"DIRE_BURNT", 30, 20, 18}, // _bundle.py:58
    {"TRANSITION_1", 55, 55, 42}, // _bundle.py:61
    {"TRANSITION_2", 75, 68, 50}, // _bundle.py:62
    {"PATH_STONE_1", 58, 52, 45}, // _bundle.py:65
    {"PATH_STONE_2", 85, 76, 65}, // _bundle.py:66
    {"PATH_STONE_3", 115, 105, 90}, // _bundle.py:67
    {"PATH_STONE_4", 145, 130, 108}, // _bundle.py:68
    {"PATH_MOSS", 65, 90, 45}, // _bundle.py:69
    {"PATH_CRACK", 30, 25, 20}, // _bundle.py:70
    {"STONE_DARK", 55, 55, 65}, // _bundle.py:73
    {"STONE_MID", 95, 95, 105}, // _bundle.py:74
    {"STONE_LIGHT", 135, 135, 145}, // _bundle.py:75
    {"STONE_HIGH", 175, 175, 185}, // _bundle.py:76
    {"RIVER_DEEP", 15, 28, 45}, // _bundle.py:79
    {"RIVER_MID", 30, 55, 88}, // _bundle.py:80
    {"RIVER_LIGHT", 50, 90, 130}, // _bundle.py:81
    {"RIVER_GLOW", 80, 150, 200}, // _bundle.py:82
    {"RIVER_FOAM", 180, 210, 230}, // _bundle.py:83
    {"TREE_TRUNK_D", 32, 20, 15}, // _bundle.py:86
    {"TREE_TRUNK_L", 58, 38, 25}, // _bundle.py:87
    {"TREE_LEAVES_D", 18, 42, 22}, // _bundle.py:88
    {"TREE_LEAVES_M", 32, 65, 35}, // _bundle.py:89
    {"TREE_LEAVES_L", 55, 95, 55}, // _bundle.py:90
    {"TREE_LEAVES_H", 80, 130, 70}, // _bundle.py:91
    {"DEAD_TREE_1", 28, 20, 18}, // _bundle.py:94
    {"DEAD_TREE_2", 55, 42, 35}, // _bundle.py:95
    {"DEAD_TREE_3", 85, 68, 55}, // _bundle.py:96
    {"CRYSTAL_BLUE_D", 25, 55, 100}, // _bundle.py:99
    {"CRYSTAL_BLUE_M", 55, 100, 170}, // _bundle.py:100
    {"CRYSTAL_BLUE_L", 100, 170, 240}, // _bundle.py:101
    {"CRYSTAL_BLUE_H", 200, 230, 255}, // _bundle.py:102
    {"CRYSTAL_RED_D", 100, 20, 30}, // _bundle.py:104
    {"CRYSTAL_RED_M", 170, 40, 55}, // _bundle.py:105
    {"CRYSTAL_RED_L", 230, 80, 100}, // _bundle.py:106
    {"CRYSTAL_RED_H", 255, 180, 200}, // _bundle.py:107
    {"FIRE_D", 140, 40, 15}, // _bundle.py:110
    {"FIRE_M", 220, 90, 25}, // _bundle.py:111
    {"FIRE_L", 255, 180, 60}, // _bundle.py:112
    {"FIRE_H", 255, 240, 150}, // _bundle.py:113
    {"OUTLINE", 12, 8, 12}, // _bundle.py:116
    {"SHADOW", 0, 0, 0}, // _bundle.py:117
};
const int64_t kPaletteCount = 52;
const int64_t kTileSize = 16; // TILE_SIZE — _bundle.py

// ── themes.py ──
// Skema UNION: tiap tema menyimpan entrinya sendiri (urutan = urutan
// literal dict Python tema itu) karena 54 tema TIDAK berskema seragam
// (HAUNTED punya 22 kunci ekstra, kehilangan 8 kunci has_*).
enum ThemeKind : uint8_t {
    KIND_STR = 0,
    KIND_BOOL = 1,
    KIND_INT = 2,
    KIND_COLOR3 = 3,
    KIND_COLOR4 = 4,
    KIND_COLORLIST = 5,
    KIND_NIL = 6,
};

struct ThemeEntry {
    const char *key;
    uint8_t kind;
    int32_t v0, v1, v2, v3; // BOOL/INT: v0; COLOR3: v0..v2; COLOR4: v0..v3
    const char *s;          // STR (nullptr selain itu)
    int32_t list;           // COLORLIST: indeks ke kColorLists (-1 selain itu)
};

// Daftar warna partikel (particle_colors_radiant/dire): 9 int per list,
// 2 list per tema, urutan = urutan THEMES.
const int32_t kColorLists[][9] = {
    {150, 52, 66, 210, 74, 86, 120, 110, 120}, // forest.particle_colors_radiant (#0)
    {82, 28, 54, 190, 42, 72, 226, 96, 110}, // forest.particle_colors_dire (#1)
    {240, 220, 120, 170, 235, 80, 220, 255, 160}, // desert.particle_colors_radiant (#2)
    {120, 200, 60, 180, 150, 40, 90, 150, 50}, // desert.particle_colors_dire (#3)
    {255, 255, 255, 220, 240, 255, 180, 220, 255}, // ice.particle_colors_radiant (#4)
    {160, 200, 240, 130, 170, 220, 100, 140, 200}, // ice.particle_colors_dire (#5)
    {255, 180, 50, 255, 130, 30, 255, 220, 100}, // volcanic.particle_colors_radiant (#6)
    {200, 60, 20, 255, 100, 30, 180, 40, 15}, // volcanic.particle_colors_dire (#7)
    {48, 205, 177, 110, 255, 205, 190, 255, 230}, // haunted.particle_colors_radiant (#8)
    {120, 50, 160, 205, 80, 210, 80, 230, 180}, // haunted.particle_colors_dire (#9)
    {110, 200, 245, 180, 230, 250, 90, 170, 210}, // ocean.particle_colors_radiant (#10)
    {40, 130, 200, 15, 55, 105, 200, 240, 255}, // ocean.particle_colors_dire (#11)
    {180, 35, 25, 240, 75, 45, 255, 145, 80}, // abyss.particle_colors_radiant (#12)
    {95, 15, 12, 180, 35, 25, 35, 5, 5}, // abyss.particle_colors_dire (#13)
    {140, 190, 35, 200, 245, 80, 240, 255, 150}, // nethervenom.particle_colors_radiant (#14)
    {60, 90, 15, 80, 40, 120, 150, 100, 200}, // nethervenom.particle_colors_dire (#15)
    {55, 190, 230, 130, 235, 255, 200, 250, 255}, // soulforged.particle_colors_radiant (#16)
    {5, 40, 60, 15, 100, 140, 55, 190, 230}, // soulforged.particle_colors_dire (#17)
    {230, 165, 40, 255, 220, 100, 255, 245, 170}, // radiant.particle_colors_radiant (#18)
    {40, 55, 110, 130, 75, 15, 230, 165, 40}, // radiant.particle_colors_dire (#19)
    {50, 130, 190, 140, 210, 240, 230, 250, 255}, // abyssal.particle_colors_radiant (#20)
    {5, 20, 45, 20, 70, 130, 110, 190, 220}, // abyssal.particle_colors_dire (#21)
    {40, 140, 180, 120, 220, 240, 200, 250, 255}, // eldritch.particle_colors_radiant (#22)
    {8, 3, 20, 70, 35, 110, 40, 140, 180}, // eldritch.particle_colors_dire (#23)
    {215, 220, 230, 250, 210, 100, 255, 245, 180}, // sanctum.particle_colors_radiant (#24)
    {25, 50, 105, 55, 105, 180, 130, 180, 235}, // sanctum.particle_colors_dire (#25)
    {255, 140, 30, 255, 200, 60, 255, 240, 130}, // eternalflame.particle_colors_radiant (#26)
    {100, 25, 5, 170, 60, 5, 240, 130, 20}, // eternalflame.particle_colors_dire (#27)
    {130, 220, 100, 200, 255, 140, 240, 255, 220}, // primordial.particle_colors_radiant (#28)
    {18, 45, 22, 40, 85, 45, 85, 140, 90}, // primordial.particle_colors_dire (#29)
    {225, 230, 245, 255, 250, 210, 255, 255, 255}, // celestialpeaks.particle_colors_radiant (#30)
    {110, 30, 25, 170, 55, 45, 120, 130, 160}, // celestialpeaks.particle_colors_dire (#31)
    {230, 220, 255, 250, 225, 255, 255, 255, 255}, // cosmic.particle_colors_radiant (#32)
    {70, 45, 130, 135, 55, 220, 200, 130, 255}, // cosmic.particle_colors_dire (#33)
    {245, 215, 95, 255, 245, 180, 255, 255, 220}, // royal.particle_colors_radiant (#34)
    {95, 15, 30, 165, 30, 45, 215, 60, 80}, // royal.particle_colors_dire (#35)
    {220, 130, 255, 245, 190, 255, 255, 245, 200}, // violet.particle_colors_radiant (#36)
    {60, 20, 120, 140, 70, 210, 210, 150, 250}, // violet.particle_colors_dire (#37)
    {255, 90, 130, 255, 180, 200, 240, 210, 100}, // crimson.particle_colors_radiant (#38)
    {80, 10, 25, 160, 25, 50, 220, 50, 90}, // crimson.particle_colors_dire (#39)
    {80, 240, 200, 200, 255, 255, 170, 255, 230}, // spectral.particle_colors_radiant (#40)
    {0, 80, 90, 30, 160, 140, 150, 100, 220}, // spectral.particle_colors_dire (#41)
    {255, 180, 60, 255, 230, 130, 255, 250, 200}, // sundered.particle_colors_radiant (#42)
    {95, 40, 8, 200, 100, 25, 255, 180, 60}, // sundered.particle_colors_dire (#43)
    {255, 240, 170, 255, 252, 220, 255, 255, 255}, // empyrean.particle_colors_radiant (#44)
    {200, 150, 45, 250, 215, 105, 255, 230, 130}, // empyrean.particle_colors_dire (#45)
    {255, 210, 90, 255, 240, 160, 255, 255, 220}, // solaris.particle_colors_radiant (#46)
    {200, 65, 55, 240, 165, 40, 255, 235, 140}, // solaris.particle_colors_dire (#47)
    {95, 245, 220, 170, 255, 240, 225, 255, 250}, // abysstide.particle_colors_radiant (#48)
    {15, 100, 90, 30, 190, 170, 60, 145, 135}, // abysstide.particle_colors_dire (#49)
    {225, 55, 70, 255, 100, 100, 255, 240, 180}, // crimsonmatriarch.particle_colors_radiant (#50)
    {75, 10, 20, 155, 25, 40, 200, 155, 45}, // crimsonmatriarch.particle_colors_dire (#51)
    {130, 200, 255, 200, 235, 255, 240, 250, 255}, // astral.particle_colors_radiant (#52)
    {15, 55, 145, 55, 130, 235, 245, 215, 115}, // astral.particle_colors_dire (#53)
    {210, 90, 235, 240, 140, 255, 255, 210, 255}, // shadowchain.particle_colors_radiant (#54)
    {35, 15, 55, 70, 35, 100, 170, 120, 210}, // shadowchain.particle_colors_dire (#55)
    {140, 220, 255, 200, 245, 255, 240, 255, 255}, // frostveil.particle_colors_radiant (#56)
    {20, 70, 110, 60, 160, 220, 255, 255, 255}, // frostveil.particle_colors_dire (#57)
    {90, 225, 245, 170, 250, 255, 230, 255, 255}, // warshade.particle_colors_radiant (#58)
    {10, 65, 80, 30, 155, 180, 70, 100, 115}, // warshade.particle_colors_dire (#59)
    {215, 75, 75, 245, 140, 140, 255, 210, 200}, // outlaw.particle_colors_radiant (#60)
    {75, 15, 20, 150, 35, 40, 170, 125, 85}, // outlaw.particle_colors_dire (#61)
    {140, 60, 200, 200, 130, 245, 180, 240, 100}, // hexbound.particle_colors_radiant (#62)
    {55, 35, 80, 135, 35, 45, 255, 230, 100}, // hexbound.particle_colors_dire (#63)
    {175, 55, 235, 225, 130, 255, 245, 200, 255}, // voidbound.particle_colors_radiant (#64)
    {35, 20, 60, 85, 20, 145, 255, 240, 255}, // voidbound.particle_colors_dire (#65)
    {140, 240, 130, 200, 255, 180, 240, 255, 220}, // earthborn.particle_colors_radiant (#66)
    {20, 80, 30, 60, 170, 70, 255, 225, 100}, // earthborn.particle_colors_dire (#67)
    {255, 100, 190, 255, 180, 230, 255, 230, 245}, // heartbane.particle_colors_radiant (#68)
    {55, 35, 75, 110, 15, 70, 255, 170, 210}, // heartbane.particle_colors_dire (#69)
    {250, 220, 110, 255, 245, 190, 255, 230, 210}, // sunfist.particle_colors_radiant (#70)
    {140, 65, 8, 200, 155, 40, 240, 190, 130}, // sunfist.particle_colors_dire (#71)
    {230, 100, 240, 255, 160, 255, 255, 220, 255}, // voidwing.particle_colors_radiant (#72)
    {25, 10, 45, 55, 25, 90, 255, 240, 180}, // voidwing.particle_colors_dire (#73)
    {230, 55, 65, 255, 110, 100, 255, 200, 180}, // crimsondevourer.particle_colors_radiant (#74)
    {80, 5, 15, 170, 20, 35, 255, 245, 240}, // crimsondevourer.particle_colors_dire (#75)
    {60, 140, 230, 170, 60, 220, 255, 240, 170}, // elementweave.particle_colors_radiant (#76)
    {20, 60, 130, 80, 20, 130, 240, 200, 90}, // elementweave.particle_colors_dire (#77)
    {60, 140, 240, 140, 210, 255, 240, 255, 255}, // tempest.particle_colors_radiant (#78)
    {20, 60, 160, 85, 120, 190, 255, 245, 180}, // tempest.particle_colors_dire (#79)
    {255, 165, 50, 255, 220, 120, 255, 250, 200}, // sawmill.particle_colors_radiant (#80)
    {110, 30, 8, 220, 90, 20, 100, 95, 90}, // sawmill.particle_colors_dire (#81)
    {230, 70, 80, 255, 130, 130, 255, 220, 220}, // croweye.particle_colors_radiant (#82)
    {85, 15, 20, 170, 35, 45, 210, 210, 220}, // croweye.particle_colors_dire (#83)
    {215, 130, 250, 245, 195, 255, 255, 240, 255}, // crystalstorm.particle_colors_radiant (#84)
    {75, 25, 130, 155, 60, 220, 100, 215, 225}, // crystalstorm.particle_colors_dire (#85)
    {200, 30, 40, 255, 90, 90, 255, 230, 140}, // eternalwarlord.particle_colors_radiant (#86)
    {110, 10, 20, 130, 45, 10, 95, 90, 115}, // eternalwarlord.particle_colors_dire (#87)
    {250, 70, 60, 255, 150, 130, 255, 245, 170}, // explosiveart.particle_colors_radiant (#88)
    {130, 15, 20, 200, 30, 35, 100, 100, 120}, // explosiveart.particle_colors_dire (#89)
    {220, 100, 55, 250, 150, 100, 255, 248, 238}, // sandshadow.particle_colors_radiant (#90)
    {120, 35, 20, 180, 60, 30, 230, 70, 45}, // sandshadow.particle_colors_dire (#91)
    {255, 165, 60, 255, 220, 130, 255, 245, 190}, // emberweaver.particle_colors_radiant (#92)
    {160, 45, 20, 230, 100, 30, 240, 120, 130}, // emberweaver.particle_colors_dire (#93)
    {255, 175, 65, 255, 225, 130, 150, 230, 245}, // skyfury.particle_colors_radiant (#94)
    {140, 45, 15, 230, 105, 30, 75, 75, 85}, // skyfury.particle_colors_dire (#95)
    {200, 140, 255, 150, 180, 255, 250, 235, 255}, // moonreaper.particle_colors_radiant (#96)
    {70, 45, 120, 140, 70, 220, 35, 25, 60}, // moonreaper.particle_colors_dire (#97)
    {235, 238, 245, 205, 180, 240, 245, 240, 165}, // moonfang.particle_colors_radiant (#98)
    {85, 55, 145, 160, 130, 215, 40, 30, 70}, // moonfang.particle_colors_dire (#99)
    {255, 200, 80, 255, 150, 40, 255, 250, 200}, // emberlion.particle_colors_radiant (#100)
    {150, 40, 10, 220, 90, 20, 90, 20, 5}, // emberlion.particle_colors_dire (#101)
    {200, 235, 255, 240, 250, 255, 120, 180, 230}, // lunarherald.particle_colors_radiant (#102)
    {110, 60, 150, 170, 120, 210, 55, 25, 90}, // lunarherald.particle_colors_dire (#103)
    {255, 253, 255, 235, 232, 245, 170, 120, 210}, // moonborn.particle_colors_radiant (#104)
    {110, 65, 155, 200, 50, 45, 25, 15, 40}, // moonborn.particle_colors_dire (#105)
    {255, 155, 45, 255, 210, 100, 255, 245, 200}, // hollowbane.particle_colors_radiant (#106)
    {140, 45, 5, 230, 95, 15, 60, 15, 0}, // hollowbane.particle_colors_dire (#107)
};

// FOREST_THEME (_bundle.py:144) — 55 kunci
const ThemeEntry kTheme0[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Forest", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "abaddon", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "Lord of Avernus", -1},
    {"radiant_grass_1", KIND_COLOR3, 28, 55, 32, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 38, 72, 42, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 52, 92, 55, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 68, 115, 70, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 90, 145, 85, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 55, 90, 40, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 45, 32, 28, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 65, 45, 38, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 85, 60, 48, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 105, 78, 62, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 60, 55, 50, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 30, 20, 18, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 55, 55, 42, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 75, 68, 50, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 58, 52, 45, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 85, 76, 65, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 115, 105, 90, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 145, 130, 108, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 65, 90, 45, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 170, 36, 61, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 8, 8, 18, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 35, 12, 34, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 91, 22, 48, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 177, 46, 75, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 130, 140, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "ash", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 0},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 1},
    {"particle_count", KIND_INT, 30, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 80, 60, 60, 40, nullptr, -1},
    {"fog_count", KIND_INT, 15, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_NIL, 0, 0, 0, 0, nullptr, -1},
};

// DESERT_THEME (_bundle.py:228) — 55 kunci
const ThemeEntry kTheme1[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Desert", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "alchemist", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Chemical Conqueror", -1},
    {"radiant_grass_1", KIND_COLOR3, 155, 115, 60, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 180, 135, 75, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 210, 165, 95, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 230, 190, 120, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 245, 215, 150, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 140, 110, 55, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 95, 55, 30, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 125, 75, 40, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 150, 95, 55, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 175, 120, 75, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 100, 75, 50, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 60, 35, 20, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 135, 100, 60, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 165, 125, 80, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 110, 85, 55, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 145, 115, 75, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 180, 145, 100, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 215, 180, 130, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 100, 85, 45, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 60, 40, 20, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 8, 29, 18, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 25, 79, 34, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 62, 139, 42, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 150, 220, 68, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 220, 255, 160, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "acid", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 2},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 3},
    {"particle_count", KIND_INT, 40, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 200, 170, 110, 30, nullptr, -1},
    {"fog_count", KIND_INT, 20, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 255, 220, 150, 15, nullptr, -1},
};

// ICE_THEME (_bundle.py:311) — 55 kunci
const ThemeEntry kTheme2[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Ice", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "ancient_apparition", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Frozen Eternity", -1},
    {"radiant_grass_1", KIND_COLOR3, 180, 200, 220, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 200, 220, 235, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 220, 235, 245, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 235, 245, 250, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 250, 253, 255, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 150, 180, 210, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 60, 80, 105, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 85, 105, 130, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 110, 135, 160, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 140, 165, 185, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 95, 115, 140, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 40, 55, 75, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 120, 145, 170, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 155, 180, 200, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 90, 110, 135, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 125, 145, 170, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 160, 180, 205, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 195, 215, 235, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 80, 130, 170, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 40, 55, 75, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 20, 50, 90, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 50, 100, 150, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 100, 160, 210, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 170, 220, 255, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 230, 245, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "snow", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 4},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 5},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 200, 220, 240, 40, nullptr, -1},
    {"fog_count", KIND_INT, 25, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 150, 200, 255, 20, nullptr, -1},
};

// VOLCANIC_THEME (_bundle.py:393) — 55 kunci
const ThemeEntry kTheme3[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Volcanic", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "ignis_drachorn", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Molten Sovereign", -1},
    {"radiant_grass_1", KIND_COLOR3, 75, 35, 20, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 100, 50, 28, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 130, 65, 35, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 160, 85, 45, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 190, 110, 55, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 95, 45, 22, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 45, 18, 12, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 65, 28, 18, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 90, 40, 25, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 115, 55, 32, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 70, 45, 35, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 30, 12, 8, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 85, 42, 25, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 110, 58, 35, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 55, 32, 22, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 85, 55, 40, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 115, 78, 55, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 145, 100, 70, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 95, 45, 22, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 100, 20, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 80, 15, 8, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 180, 55, 12, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 240, 120, 30, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 255, 180, 60, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 230, 130, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "ember", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 6},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 7},
    {"particle_count", KIND_INT, 50, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 120, 40, 20, 45, nullptr, -1},
    {"fog_count", KIND_INT, 22, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 255, 100, 40, 20, nullptr, -1},
};

// HAUNTED_THEME (_bundle.py:474) — 69 kunci
const ThemeEntry kTheme4[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Haunted Veil", -1},
    {"level_identity", KIND_STR, 0, 0, 0, 0, "krobellus_death_prophet_necropolis", -1},
    {"radiant_grass_1", KIND_COLOR3, 8, 25, 27, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 12, 47, 44, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 19, 76, 61, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 31, 112, 82, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 65, 174, 119, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 25, 105, 80, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 10, 7, 19, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 27, 12, 37, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 51, 18, 60, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 82, 31, 85, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 54, 38, 65, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 8, 5, 15, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 25, 25, 35, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 47, 39, 56, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 25, 25, 34, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 53, 53, 64, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 88, 86, 94, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 151, 151, 151, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 35, 117, 91, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 55, 226, 178, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 3, 14, 22, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 7, 54, 61, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 17, 119, 108, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 48, 205, 177, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 190, 255, 222, 0, nullptr, -1},
    {"void_black", KIND_COLOR3, 7, 6, 16, 0, nullptr, -1},
    {"rift_violet", KIND_COLOR3, 151, 57, 190, 0, nullptr, -1},
    {"soul_teal", KIND_COLOR3, 48, 205, 177, 0, nullptr, -1},
    {"bone_white", KIND_COLOR3, 151, 160, 157, 0, nullptr, -1},
    {"bone_highlight", KIND_COLOR3, 221, 238, 218, 0, nullptr, -1},
    {"causeway_dark", KIND_COLOR3, 29, 29, 39, 0, nullptr, -1},
    {"causeway_mid", KIND_COLOR3, 66, 66, 78, 0, nullptr, -1},
    {"arena_stone", KIND_COLOR3, 38, 35, 54, 0, nullptr, -1},
    {"arena_highlight", KIND_COLOR3, 101, 74, 121, 0, nullptr, -1},
    {"obelisk_stone", KIND_COLOR3, 42, 37, 56, 0, nullptr, -1},
    {"obelisk_highlight", KIND_COLOR3, 112, 79, 129, 0, nullptr, -1},
    {"gate_stone", KIND_COLOR3, 38, 34, 49, 0, nullptr, -1},
    {"gate_highlight", KIND_COLOR3, 106, 83, 119, 0, nullptr, -1},
    {"border_stone", KIND_COLOR3, 24, 20, 34, 0, nullptr, -1},
    {"border_highlight", KIND_COLOR3, 81, 58, 93, 0, nullptr, -1},
    {"ash_high", KIND_COLOR3, 68, 50, 75, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ghost_lights", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ectoplasm_pools", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crypt_gates", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spirit_wisps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cursed_candles", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "spirit", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 8},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 9},
    {"particle_count", KIND_INT, 34, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 35, 100, 95, 32, nullptr, -1},
    {"fog_count", KIND_INT, 12, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 24, 42, 44, 12, nullptr, -1},
};

// OCEAN_THEME (_bundle.py:572) — 55 kunci
const ThemeEntry kTheme5[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Admiral's Cove", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "kunkka", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Admiral of the Fleet", -1},
    {"radiant_grass_1", KIND_COLOR3, 45, 75, 80, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 75, 110, 105, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 100, 145, 135, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 140, 175, 160, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 185, 210, 190, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 60, 105, 100, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 5, 18, 42, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 12, 35, 70, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 25, 55, 100, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 45, 85, 130, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 30, 50, 75, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 3, 10, 25, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 55, 90, 100, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 40, 80, 110, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 45, 35, 25, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 75, 58, 38, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 110, 85, 55, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 150, 120, 80, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 50, 100, 90, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 40, 130, 200, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 3, 15, 40, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 15, 55, 105, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 40, 130, 200, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 110, 200, 245, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 245, 255, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "mist", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 10},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 11},
    {"particle_count", KIND_INT, 45, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 100, 160, 200, 35, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 30, 70, 120, 15, nullptr, -1},
};

// ABYSS_THEME (_bundle.py:658) — 55 kunci
const ThemeEntry kTheme6[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Shadow Abyss", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "nyxarath", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Soul Eater", -1},
    {"radiant_grass_1", KIND_COLOR3, 5, 4, 6, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 12, 8, 10, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 22, 14, 16, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 35, 20, 22, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 55, 30, 28, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 18, 10, 12, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 2, 2, 3, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 8, 5, 6, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 16, 10, 12, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 32, 18, 22, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 20, 12, 14, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 1, 1, 2, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 15, 10, 12, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 28, 16, 18, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 8, 6, 7, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 20, 14, 14, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 40, 25, 24, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 65, 40, 35, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 16, 10, 12, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 80, 30, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 25, 5, 8, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 85, 15, 15, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 180, 35, 25, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 240, 75, 45, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 145, 80, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "ember", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 12},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 13},
    {"particle_count", KIND_INT, 55, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 20, 8, 10, 50, nullptr, -1},
    {"fog_count", KIND_INT, 20, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 40, 10, 10, 20, nullptr, -1},
};

// NETHERVENOM_THEME (_bundle.py:746) — 55 kunci
const ThemeEntry kTheme7[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Nethervenom Expanse", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "vhorethzir", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Nethervenom Wyrm", -1},
    {"radiant_grass_1", KIND_COLOR3, 6, 16, 8, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 14, 34, 18, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 24, 52, 28, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 38, 74, 42, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 70, 120, 70, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 20, 44, 22, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 4, 4, 10, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 10, 8, 20, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 18, 12, 34, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 30, 18, 55, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 22, 30, 16, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 2, 2, 5, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 14, 26, 16, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 26, 40, 26, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 10, 14, 9, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 22, 30, 20, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 44, 56, 38, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 72, 86, 58, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 18, 40, 20, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 200, 245, 80, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 12, 26, 6, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 60, 90, 15, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 140, 190, 35, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 200, 245, 80, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 240, 255, 150, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "ember", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 14},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 15},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 18, 34, 12, 55, nullptr, -1},
    {"fog_count", KIND_INT, 22, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 25, 45, 15, 22, nullptr, -1},
};

// SOULFORGED_THEME (_bundle.py:837) — 55 kunci
const ThemeEntry kTheme8[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Soulforged Expanse", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "naraka", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Lost Soul", -1},
    {"radiant_grass_1", KIND_COLOR3, 28, 26, 38, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 46, 42, 56, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 66, 62, 78, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 90, 84, 102, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 130, 122, 145, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 36, 34, 48, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 4, 6, 10, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 8, 12, 20, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 14, 22, 34, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 22, 36, 52, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 18, 24, 32, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 2, 3, 6, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 24, 28, 38, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 40, 46, 60, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 12, 14, 20, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 26, 30, 40, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 48, 54, 68, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 74, 82, 96, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 18, 24, 34, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 130, 235, 255, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 5, 40, 60, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 15, 100, 140, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 55, 190, 230, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 130, 235, 255, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 200, 250, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "ember", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 16},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 17},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 16, 28, 38, 55, nullptr, -1},
    {"fog_count", KIND_INT, 22, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 18, 32, 42, 22, nullptr, -1},
};

// RADIANT_THEME (_bundle.py:924) — 55 kunci
const ThemeEntry kTheme9[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Radiant Expanse", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "aurethzar", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Radiant Dawn", -1},
    {"radiant_grass_1", KIND_COLOR3, 35, 22, 5, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 70, 46, 10, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 110, 78, 18, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 160, 115, 30, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 240, 195, 80, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 52, 34, 8, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 10, 15, 40, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 18, 26, 60, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 28, 40, 82, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 40, 55, 110, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 24, 32, 62, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 6, 9, 22, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 48, 32, 10, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 90, 62, 18, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 40, 26, 8, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 72, 48, 14, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 110, 76, 22, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 165, 120, 40, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 56, 38, 10, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 225, 140, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 130, 75, 15, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 200, 130, 30, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 230, 165, 40, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 255, 220, 100, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 245, 170, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "ember", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 18},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 19},
    {"particle_count", KIND_INT, 55, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 120, 80, 25, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 50, 32, 8, 20, nullptr, -1},
};

// ABYSSAL_THEME (_bundle.py:1011) — 55 kunci
const ThemeEntry kTheme10[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Abyssal Depths", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "thalakryon", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Abyssal Sovereign", -1},
    {"radiant_grass_1", KIND_COLOR3, 5, 15, 30, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 15, 40, 70, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 35, 85, 130, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 70, 140, 190, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 130, 200, 240, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 20, 60, 55, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 5, 20, 40, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 10, 45, 65, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 20, 70, 130, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 40, 110, 145, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 15, 40, 70, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 2, 8, 16, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 30, 55, 65, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 70, 110, 130, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 10, 30, 50, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 25, 55, 80, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 50, 100, 130, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 85, 150, 180, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 20, 60, 55, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 180, 240, 255, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 5, 20, 45, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 20, 60, 110, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 50, 130, 190, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 140, 210, 240, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 230, 250, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "ember", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 20},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 21},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 10, 30, 50, 55, nullptr, -1},
    {"fog_count", KIND_INT, 22, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 15, 40, 55, 22, nullptr, -1},
};

// ELDRITCH_THEME (_bundle.py:1097) — 55 kunci
const ThemeEntry kTheme11[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Eldritch Depths", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "nazulmor", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Deepborn Herald", -1},
    {"radiant_grass_1", KIND_COLOR3, 5, 20, 25, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 20, 55, 60, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 45, 110, 105, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 95, 175, 155, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 160, 220, 190, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 25, 65, 75, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 8, 3, 20, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 30, 12, 55, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 70, 35, 110, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 140, 90, 190, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 45, 20, 70, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 4, 2, 10, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 15, 60, 90, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 40, 140, 180, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 10, 35, 45, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 25, 65, 75, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 55, 130, 125, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 110, 195, 170, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 25, 65, 75, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 120, 220, 240, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 5, 20, 30, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 15, 60, 90, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 40, 140, 180, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 120, 220, 240, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 200, 250, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "ember", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 22},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 23},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 12, 30, 40, 55, nullptr, -1},
    {"fog_count", KIND_INT, 22, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 10, 45, 55, 22, nullptr, -1},
};

// SANCTUM_THEME (_bundle.py:1183) — 55 kunci
const ThemeEntry kTheme12[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Silver Sanctum", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "solvarin", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Holy Paladin Warden", -1},
    {"radiant_grass_1", KIND_COLOR3, 35, 40, 50, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 85, 90, 105, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 155, 160, 175, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 215, 220, 230, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 250, 252, 255, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 110, 115, 130, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 10, 20, 45, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 25, 50, 105, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 55, 105, 180, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 130, 180, 235, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 40, 45, 60, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 5, 10, 22, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 60, 65, 80, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 110, 120, 145, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 30, 35, 45, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 70, 76, 90, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 120, 128, 145, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 175, 182, 200, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 80, 88, 105, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 250, 210, 100, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 55, 105, 180, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 130, 180, 235, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 200, 225, 250, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 255, 245, 180, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 255, 230, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "ember", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 24},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 25},
    {"particle_count", KIND_INT, 55, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 90, 96, 112, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 40, 45, 60, 20, nullptr, -1},
};

// ETERNALFLAME_THEME (_bundle.py:1269) — 55 kunci
const ThemeEntry kTheme13[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Eternal Flame", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "pyraethis", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Eternal Firebird", -1},
    {"radiant_grass_1", KIND_COLOR3, 45, 14, 8, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 95, 28, 12, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 150, 55, 20, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 205, 95, 30, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 255, 150, 45, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 120, 40, 15, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 25, 4, 2, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 60, 12, 4, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 110, 30, 8, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 170, 60, 14, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 35, 8, 4, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 12, 2, 1, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 70, 22, 8, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 130, 45, 14, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 35, 12, 6, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 70, 25, 10, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 110, 45, 16, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 160, 75, 25, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 90, 35, 12, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 200, 60, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 200, 60, 10, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 255, 120, 25, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 255, 200, 60, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 255, 240, 130, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 253, 220, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "ember", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 26},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 27},
    {"particle_count", KIND_INT, 55, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 70, 40, 25, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 60, 30, 15, 20, nullptr, -1},
};

// PRIMORDIAL_THEME (_bundle.py:1355) — 55 kunci
const ThemeEntry kTheme14[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Primordial Grove", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "yamako", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Primordial Woodshaper", -1},
    {"radiant_grass_1", KIND_COLOR3, 5, 15, 8, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 18, 45, 22, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 40, 85, 45, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 85, 140, 90, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 140, 190, 140, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 25, 60, 28, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 18, 12, 5, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 55, 35, 15, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 100, 70, 30, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 160, 120, 55, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 30, 22, 14, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 8, 5, 3, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 55, 60, 35, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 95, 105, 60, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 25, 18, 10, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 55, 40, 20, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 95, 70, 35, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 140, 105, 55, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 30, 70, 25, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 130, 220, 100, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 15, 60, 20, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 55, 140, 55, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 130, 220, 100, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 200, 255, 140, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 240, 255, 220, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 28},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 29},
    {"particle_count", KIND_INT, 55, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 20, 45, 25, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 30, 60, 30, 20, nullptr, -1},
};

// CELESTIALPEAKS_THEME (_bundle.py:1441) — 55 kunci
const ThemeEntry kTheme15[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Celestial Peaks", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "seiryukong", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Celestial Simian", -1},
    {"radiant_grass_1", KIND_COLOR3, 60, 40, 20, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 110, 75, 45, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 170, 125, 80, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 220, 180, 130, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 245, 220, 175, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 90, 60, 35, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 25, 10, 8, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 60, 18, 15, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 110, 30, 25, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 170, 55, 45, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 45, 30, 25, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 10, 5, 4, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 80, 55, 35, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 120, 85, 55, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 30, 20, 12, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 60, 40, 22, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 95, 65, 35, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 140, 100, 55, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 75, 55, 30, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 225, 130, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 120, 130, 160, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 175, 185, 210, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 225, 230, 245, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 255, 250, 210, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 255, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "snow", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 30},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 31},
    {"particle_count", KIND_INT, 55, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 200, 200, 215, 40, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 120, 95, 60, 20, nullptr, -1},
};

// COSMIC_THEME (_bundle.py:1527) — 55 kunci
const ThemeEntry kTheme16[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Cosmic Expanse", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "nyxareth", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Cosmic Sovereign", -1},
    {"radiant_grass_1", KIND_COLOR3, 25, 10, 60, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 60, 25, 120, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 120, 60, 190, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 180, 110, 240, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 230, 170, 255, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 45, 15, 90, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 5, 0, 15, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 15, 8, 35, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 35, 20, 75, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 70, 45, 130, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 25, 15, 50, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 3, 0, 8, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 40, 18, 85, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 80, 40, 140, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 20, 12, 40, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 45, 25, 80, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 75, 45, 130, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 110, 70, 180, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 35, 20, 70, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 235, 180, 255, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 65, 20, 130, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 135, 55, 220, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 200, 130, 255, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 235, 180, 255, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 250, 225, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 32},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 33},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 45, 20, 90, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 35, 15, 70, 20, nullptr, -1},
};

// ROYAL_THEME (_bundle.py:1613) — 55 kunci
const ThemeEntry kTheme17[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Royal Citadel", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "aurelion", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Golden Sovereign", -1},
    {"radiant_grass_1", KIND_COLOR3, 80, 55, 10, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 115, 85, 20, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 200, 155, 40, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 245, 215, 95, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 255, 245, 180, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 140, 100, 20, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 25, 15, 8, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 55, 35, 20, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 95, 65, 35, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 155, 115, 65, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 40, 25, 15, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 10, 6, 4, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 60, 42, 15, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 115, 85, 35, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 45, 5, 15, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 95, 15, 30, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 165, 30, 45, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 215, 60, 80, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 75, 12, 25, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 245, 180, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 10, 30, 90, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 40, 90, 190, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 120, 180, 250, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 245, 215, 95, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 255, 220, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 34},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 35},
    {"particle_count", KIND_INT, 55, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 120, 90, 40, 40, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 90, 60, 20, 20, nullptr, -1},
};

// VIOLET_THEME (_bundle.py:1699) — 55 kunci
const ThemeEntry kTheme18[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Violet Court", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "vaelindra", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Violet Sovereign", -1},
    {"radiant_grass_1", KIND_COLOR3, 15, 5, 35, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 40, 15, 80, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 85, 40, 155, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 155, 100, 220, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 200, 160, 245, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 60, 25, 110, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 20, 5, 45, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 60, 20, 120, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 140, 70, 210, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 210, 150, 250, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 45, 15, 90, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 8, 2, 20, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 55, 25, 100, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 95, 50, 150, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 35, 15, 70, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 65, 30, 120, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 100, 55, 170, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 140, 90, 210, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 50, 25, 100, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 245, 200, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 30, 5, 55, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 85, 20, 145, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 170, 55, 230, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 245, 190, 255, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 235, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 36},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 37},
    {"particle_count", KIND_INT, 55, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 55, 25, 100, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 45, 15, 90, 20, nullptr, -1},
};

// CRIMSON_THEME (_bundle.py:1785) — 55 kunci
const ThemeEntry kTheme19[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "Crimson Dominion", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "morthraxis", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Crimson Sovereign", -1},
    {"radiant_grass_1", KIND_COLOR3, 30, 5, 10, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 80, 10, 25, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 160, 25, 50, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 220, 50, 90, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 255, 90, 130, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 55, 8, 20, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 8, 5, 12, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 25, 15, 20, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 55, 30, 35, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 110, 70, 75, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 40, 15, 20, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 5, 3, 6, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 60, 12, 25, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 110, 25, 45, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 15, 4, 8, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 40, 8, 15, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 90, 15, 30, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 150, 30, 55, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 45, 8, 18, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 245, 180, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 80, 10, 25, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 160, 25, 50, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 220, 50, 90, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 255, 90, 130, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 180, 200, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 38},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 39},
    {"particle_count", KIND_INT, 55, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 60, 10, 25, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 30, 5, 12, 20, nullptr, -1},
};

// SPECTRAL_THEME (_bundle.py:1865) — 55 kunci
const ThemeEntry kTheme20[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Hollow Veil", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "nexthyrius", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Chained Hollow", -1},
    {"radiant_grass_1", KIND_COLOR3, 2, 8, 12, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 10, 25, 35, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 25, 55, 70, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 55, 100, 120, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 100, 160, 180, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 30, 160, 140, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 5, 10, 12, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 20, 10, 40, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 70, 40, 130, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 150, 100, 220, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 25, 35, 40, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 2, 2, 4, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 15, 40, 45, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 45, 30, 80, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 5, 10, 12, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 25, 35, 40, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 70, 85, 95, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 150, 170, 180, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 10, 60, 55, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 80, 240, 200, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 2, 20, 18, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 10, 60, 55, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 30, 160, 140, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 80, 240, 200, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 230, 255, 245, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 40},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 41},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 10, 60, 55, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 5, 25, 30, 20, nullptr, -1},
};

// SUNDERED_THEME (_bundle.py:1945) — 55 kunci
const ThemeEntry kTheme21[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Sundered Peak", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "molgravar", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Colossus of the Sundered Peak", -1},
    {"radiant_grass_1", KIND_COLOR3, 18, 12, 8, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 48, 34, 22, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 95, 72, 48, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 155, 122, 85, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 210, 180, 135, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 120, 200, 60, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 8, 5, 3, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 25, 18, 12, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 55, 42, 28, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 130, 85, 45, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 40, 28, 18, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 5, 3, 2, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 60, 40, 22, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 110, 60, 25, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 15, 10, 7, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 45, 32, 20, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 95, 70, 45, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 160, 125, 88, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 65, 50, 30, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 230, 130, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 35, 12, 3, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 95, 40, 8, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 200, 100, 25, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 255, 180, 60, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 250, 200, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 42},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 43},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 55, 42, 28, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 40, 18, 6, 20, nullptr, -1},
};

// EMPYREAN_THEME (_bundle.py:2025) — 55 kunci
const ThemeEntry kTheme22[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Empyrean Executioner", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "seraphienne", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Empyrean Executioner", -1},
    {"radiant_grass_1", KIND_COLOR3, 35, 20, 3, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 105, 70, 15, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 200, 150, 45, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 250, 215, 105, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 255, 240, 170, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 190, 145, 50, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 55, 55, 70, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 110, 110, 130, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 175, 175, 195, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 230, 230, 240, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 90, 80, 60, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 25, 20, 30, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 110, 90, 40, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 200, 170, 90, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 45, 30, 8, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 120, 85, 25, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 200, 155, 60, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 250, 220, 130, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 95, 65, 15, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 252, 220, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 155, 100, 20, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 240, 180, 55, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 255, 230, 130, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 255, 250, 200, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 255, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 44},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 45},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 240, 220, 170, 40, nullptr, -1},
    {"fog_count", KIND_INT, 16, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 60, 45, 15, 20, nullptr, -1},
};

// SOLARIS_THEME (_bundle.py:2105) — 55 kunci
const ThemeEntry kTheme23[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Sunborn Herald", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "solareth", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Sunborn Herald", -1},
    {"radiant_grass_1", KIND_COLOR3, 55, 30, 5, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 125, 80, 15, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 200, 155, 40, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 245, 210, 85, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 255, 235, 140, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 180, 100, 15, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 75, 15, 15, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 145, 30, 30, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 200, 65, 55, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 240, 110, 80, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 90, 45, 20, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 35, 10, 8, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 120, 70, 18, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 220, 130, 45, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 50, 28, 8, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 130, 82, 18, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 205, 160, 50, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 250, 215, 100, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 95, 55, 15, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 255, 220, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 80, 40, 5, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 180, 100, 15, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 240, 165, 40, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 255, 210, 90, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 255, 220, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 46},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 47},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 240, 190, 90, 40, nullptr, -1},
    {"fog_count", KIND_INT, 16, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 70, 45, 10, 20, nullptr, -1},
};

// ABYSSTIDE_THEME (_bundle.py:2185) — 55 kunci
const ThemeEntry kTheme24[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Deepborn Oracle", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "okeanora", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Deepborn Oracle", -1},
    {"radiant_grass_1", KIND_COLOR3, 5, 25, 25, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 15, 55, 55, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 30, 95, 90, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 60, 145, 135, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 95, 245, 220, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 15, 100, 90, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 5, 30, 30, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 15, 65, 65, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 40, 100, 100, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 120, 85, 20, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 55, 35, 5, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 3, 15, 18, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 20, 60, 58, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 60, 120, 105, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 6, 28, 28, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 20, 70, 68, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 45, 110, 105, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 85, 160, 150, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 10, 55, 50, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 170, 255, 240, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 5, 45, 40, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 15, 100, 90, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 30, 190, 170, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 95, 245, 220, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 225, 255, 250, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 48},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 49},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 15, 65, 65, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 8, 35, 35, 20, nullptr, -1},
};

// CRIMSONMATRIARCH_THEME (_bundle.py:2265) — 55 kunci
const ThemeEntry kTheme25[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Crimson Matriarch", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "vaelmyrra", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Crimson Matriarch", -1},
    {"radiant_grass_1", KIND_COLOR3, 8, 5, 10, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 25, 18, 25, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 55, 40, 50, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 100, 80, 90, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 170, 150, 160, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 75, 10, 20, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 25, 3, 8, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 75, 10, 20, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 155, 25, 40, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 200, 155, 45, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 45, 30, 5, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 5, 2, 4, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 70, 20, 30, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 130, 90, 35, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 10, 6, 12, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 30, 20, 30, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 70, 50, 60, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 120, 95, 105, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 50, 12, 18, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 180, 170, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 25, 3, 8, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 75, 10, 20, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 155, 25, 40, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 225, 55, 70, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 180, 170, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 50},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 51},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 75, 10, 20, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 40, 8, 12, 20, nullptr, -1},
};

// ASTRAL_THEME (_bundle.py:2345) — 55 kunci
const ThemeEntry kTheme26[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Astral Sovereign", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "zarethyr", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Astral Sovereign", -1},
    {"radiant_grass_1", KIND_COLOR3, 5, 8, 25, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 18, 25, 55, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 40, 55, 100, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 85, 105, 160, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 150, 175, 220, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 15, 55, 145, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 5, 15, 55, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 15, 55, 145, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 55, 130, 235, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 130, 200, 255, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 95, 105, 130, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 3, 4, 12, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 35, 50, 100, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 95, 125, 190, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 8, 12, 32, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 25, 35, 70, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 55, 70, 120, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 100, 120, 175, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 20, 30, 60, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 240, 250, 255, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 5, 15, 55, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 15, 55, 145, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 55, 130, 235, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 130, 200, 255, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 240, 250, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 52},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 53},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 18, 25, 55, 45, nullptr, -1},
    {"fog_count", KIND_INT, 16, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 12, 20, 50, 20, nullptr, -1},
};

// SHADOWCHAIN_THEME (_bundle.py:2425) — 55 kunci
const ThemeEntry kTheme27[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Forsaken Empress", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "nyrethzalv", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Forsaken Empress of Shadow-Chains", -1},
    {"radiant_grass_1", KIND_COLOR3, 15, 5, 25, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 35, 15, 55, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 70, 35, 100, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 110, 65, 155, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 170, 120, 210, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 65, 15, 90, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 5, 3, 10, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 20, 12, 35, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 45, 30, 65, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 145, 40, 180, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 30, 12, 45, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 4, 2, 8, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 40, 20, 70, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 100, 45, 140, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 10, 6, 18, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 30, 18, 45, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 65, 40, 90, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 115, 75, 155, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 25, 10, 40, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 210, 255, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 20, 5, 30, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 65, 15, 90, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 145, 40, 180, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 210, 90, 235, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 210, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 54},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 55},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 35, 15, 55, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 30, 10, 45, 20, nullptr, -1},
};

// FROSTVEIL_THEME (_bundle.py:2505) — 55 kunci
const ThemeEntry kTheme28[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Frost-Veiled Huntress", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "nyrellieth", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Frost-Veiled Huntress", -1},
    {"radiant_grass_1", KIND_COLOR3, 5, 8, 20, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 15, 22, 45, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 35, 45, 80, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 65, 80, 120, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 110, 125, 165, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 20, 70, 110, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 5, 25, 45, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 20, 70, 110, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 60, 160, 220, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 140, 220, 255, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 75, 75, 95, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 3, 4, 10, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 25, 45, 85, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 75, 125, 175, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 7, 10, 25, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 22, 32, 60, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 50, 65, 105, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 90, 110, 150, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 15, 35, 60, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 240, 255, 255, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 5, 25, 45, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 20, 70, 110, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 60, 160, 220, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 140, 220, 255, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 240, 255, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 56},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 57},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 20, 70, 110, 40, nullptr, -1},
    {"fog_count", KIND_INT, 16, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 15, 30, 60, 20, nullptr, -1},
};

// WARSHADE_THEME (_bundle.py:2585) — 55 kunci
const ThemeEntry kTheme29[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Shadow of War", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "nyxharr", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Shadow of War", -1},
    {"radiant_grass_1", KIND_COLOR3, 5, 10, 12, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 15, 25, 30, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 35, 55, 65, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 70, 100, 115, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 120, 155, 170, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 10, 65, 80, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 2, 20, 25, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 10, 65, 80, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 30, 155, 180, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 90, 225, 245, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 25, 25, 32, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 3, 5, 7, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 25, 45, 55, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 55, 120, 140, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 6, 11, 14, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 20, 32, 38, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 45, 65, 78, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 80, 110, 125, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 12, 30, 36, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 230, 255, 255, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 2, 20, 25, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 10, 65, 80, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 30, 155, 180, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 90, 225, 245, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 230, 255, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 58},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 59},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 10, 65, 80, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 8, 25, 30, 20, nullptr, -1},
};

// OUTLAW_THEME (_bundle.py:2665) — 55 kunci
const ThemeEntry kTheme30[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Outlaw King", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "ravokkar", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Outlaw King", -1},
    {"radiant_grass_1", KIND_COLOR3, 30, 22, 16, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 70, 50, 35, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 120, 85, 55, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 170, 125, 85, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 215, 165, 120, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 75, 45, 30, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 30, 8, 10, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 75, 15, 20, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 150, 35, 40, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 215, 75, 75, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 40, 32, 35, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 5, 5, 8, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 80, 55, 40, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 140, 85, 60, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 22, 16, 12, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 55, 40, 30, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 95, 70, 50, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 150, 110, 65, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 45, 30, 22, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 245, 140, 140, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 30, 8, 10, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 75, 15, 20, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 150, 35, 40, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 215, 75, 75, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 245, 140, 140, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 60},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 61},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 60, 45, 35, 45, nullptr, -1},
    {"fog_count", KIND_INT, 16, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 50, 30, 25, 20, nullptr, -1},
};

// HEXBOUND_THEME (_bundle.py:2745) — 55 kunci
const ThemeEntry kTheme31[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Hexbound Sovereign", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "malzeroth", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Hexbound Sovereign", -1},
    {"radiant_grass_1", KIND_COLOR3, 25, 15, 40, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 55, 35, 80, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 95, 65, 130, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 145, 110, 180, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 200, 170, 225, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 110, 180, 50, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 35, 8, 12, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 75, 18, 25, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 135, 35, 45, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 185, 60, 65, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 85, 55, 15, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 10, 5, 8, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 70, 40, 90, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 130, 55, 90, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 18, 10, 30, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 50, 30, 75, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 90, 60, 125, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 145, 105, 175, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 45, 90, 20, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 180, 240, 100, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 15, 30, 8, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 45, 90, 20, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 110, 180, 50, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 180, 240, 100, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 220, 255, 170, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 62},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 63},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 55, 35, 80, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 40, 20, 60, 20, nullptr, -1},
};

// VOIDBOUND_THEME (_bundle.py:2825) — 55 kunci
const ThemeEntry kTheme32[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Voidbound Sovereign", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "zharakzuul", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Voidbound Sovereign", -1},
    {"radiant_grass_1", KIND_COLOR3, 15, 8, 30, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 35, 20, 60, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 70, 40, 110, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 125, 85, 175, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 185, 145, 225, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 85, 20, 145, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 25, 5, 45, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 85, 20, 145, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 175, 55, 235, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 225, 130, 255, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 130, 125, 150, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 8, 4, 15, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 50, 28, 90, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 120, 60, 175, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 12, 7, 25, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 40, 22, 70, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 80, 45, 125, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 135, 90, 180, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 30, 12, 55, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 240, 255, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 25, 5, 45, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 85, 20, 145, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 175, 55, 235, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 225, 130, 255, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 240, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 64},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 65},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 35, 20, 60, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 35, 15, 60, 20, nullptr, -1},
};

// EARTHBORN_THEME (_bundle.py:2905) — 55 kunci
const ThemeEntry kTheme33[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Earthborn", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "grondmauris", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Earthborn", -1},
    {"radiant_grass_1", KIND_COLOR3, 25, 22, 20, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 58, 55, 50, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 105, 100, 92, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 165, 158, 145, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 205, 198, 182, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 75, 120, 40, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 10, 8, 6, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 35, 30, 25, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 45, 32, 20, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 95, 72, 45, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 55, 50, 42, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 5, 4, 3, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 60, 55, 48, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 100, 90, 70, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 20, 18, 16, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 55, 52, 46, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 100, 95, 85, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 160, 152, 138, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 35, 65, 20, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 240, 255, 220, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 5, 30, 10, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 20, 80, 30, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 60, 170, 70, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 140, 240, 130, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 240, 255, 220, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 66},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 67},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 35, 65, 20, 40, nullptr, -1},
    {"fog_count", KIND_INT, 16, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 35, 45, 20, 20, nullptr, -1},
};

// HEARTBANE_THEME (_bundle.py:2985) — 55 kunci
const ThemeEntry kTheme34[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Heartbane", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "lyssarethys", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Heartbane", -1},
    {"radiant_grass_1", KIND_COLOR3, 30, 20, 40, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 75, 55, 90, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 130, 105, 145, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 190, 165, 200, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 230, 210, 235, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 110, 15, 70, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 8, 4, 15, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 28, 18, 40, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 55, 35, 75, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 100, 70, 130, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 55, 8, 35, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 5, 2, 8, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 60, 40, 90, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 140, 60, 130, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 12, 6, 20, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 35, 22, 50, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 70, 45, 95, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 120, 85, 150, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 45, 15, 60, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 230, 245, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 40, 5, 25, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 110, 15, 70, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 200, 40, 130, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 255, 100, 190, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 230, 245, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 68},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 69},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 55, 35, 75, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 45, 15, 45, 20, nullptr, -1},
};

// SUNFIST_THEME (_bundle.py:3065) — 55 kunci
const ThemeEntry kTheme35[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Sunfist", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "kaerinya", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Sunfist", -1},
    {"radiant_grass_1", KIND_COLOR3, 5, 10, 25, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 18, 30, 55, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 40, 65, 105, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 85, 120, 165, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 140, 175, 210, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 100, 70, 15, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 55, 25, 3, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 140, 65, 8, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 200, 155, 40, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 250, 220, 110, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 30, 15, 8, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 6, 4, 2, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 45, 60, 95, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 140, 110, 55, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 10, 16, 32, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 28, 42, 70, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 55, 75, 115, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 95, 130, 170, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 60, 40, 22, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 245, 190, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 55, 25, 3, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 140, 65, 8, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 200, 155, 40, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 250, 220, 110, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 245, 190, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 70},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 71},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 40, 65, 105, 40, nullptr, -1},
    {"fog_count", KIND_INT, 16, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 70, 45, 10, 20, nullptr, -1},
};

// VOIDWING_THEME (_bundle.py:3145) — 55 kunci
const ThemeEntry kTheme36[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Void Sovereign", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "xelnarath", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Void Sovereign", -1},
    {"radiant_grass_1", KIND_COLOR3, 8, 3, 15, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 25, 10, 45, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 55, 25, 90, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 100, 55, 155, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 155, 95, 210, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 90, 20, 110, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 30, 15, 55, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 75, 40, 120, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 145, 90, 195, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 170, 45, 190, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 20, 20, 45, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 4, 2, 8, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 45, 22, 80, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 110, 50, 150, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 10, 6, 25, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 30, 25, 55, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 65, 55, 100, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 115, 105, 165, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 55, 25, 90, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 220, 255, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 35, 5, 40, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 90, 20, 110, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 170, 45, 190, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 230, 100, 240, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 220, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 72},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 73},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 25, 10, 45, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 35, 12, 55, 20, nullptr, -1},
};

// CRIMSONDEVOURER_THEME (_bundle.py:3225) — 55 kunci
const ThemeEntry kTheme37[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Crimson Devourer", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "kyrenzai", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Crimson Devourer", -1},
    {"radiant_grass_1", KIND_COLOR3, 5, 3, 5, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 18, 12, 18, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 40, 30, 35, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 75, 60, 65, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 130, 115, 120, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 80, 5, 15, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 25, 0, 5, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 80, 5, 15, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 170, 20, 35, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 230, 55, 65, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 8, 5, 8, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 3, 2, 3, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 45, 30, 38, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 120, 30, 42, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 8, 5, 8, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 28, 20, 26, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 55, 45, 52, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 95, 80, 88, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 50, 15, 22, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 200, 180, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 25, 0, 5, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 80, 5, 15, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 170, 20, 35, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 230, 55, 65, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 200, 180, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 74},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 75},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 40, 10, 16, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 45, 8, 12, 20, nullptr, -1},
};

// ELEMENTWEAVE_THEME (_bundle.py:3305) — 55 kunci
const ThemeEntry kTheme38[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Elemental Weaver", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "xaelmoran", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Elemental Weaver", -1},
    {"radiant_grass_1", KIND_COLOR3, 15, 8, 25, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 40, 22, 60, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 75, 45, 105, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 120, 85, 160, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 170, 130, 210, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 80, 20, 130, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 5, 15, 40, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 20, 60, 130, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 60, 140, 230, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 140, 210, 255, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 85, 55, 15, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 8, 5, 15, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 55, 35, 85, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 90, 90, 140, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 12, 7, 22, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 40, 24, 60, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 75, 48, 105, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 125, 90, 160, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 25, 5, 40, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 240, 170, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 25, 5, 40, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 80, 20, 130, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 170, 60, 220, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 220, 130, 255, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 230, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 76},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 77},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 40, 22, 60, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 40, 25, 60, 20, nullptr, -1},
};

// TEMPEST_THEME (_bundle.py:3385) — 55 kunci
const ThemeEntry kTheme39[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Tempest Weaver", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "thalryndel", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Tempest Weaver", -1},
    {"radiant_grass_1", KIND_COLOR3, 5, 10, 30, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 15, 30, 75, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 40, 65, 130, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 85, 120, 190, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 140, 175, 230, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 20, 60, 160, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 5, 15, 50, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 20, 60, 160, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 60, 140, 240, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 170, 220, 245, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 35, 25, 5, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 3, 6, 18, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 30, 55, 110, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 60, 105, 170, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 8, 14, 38, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 25, 42, 90, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 50, 78, 145, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 95, 130, 195, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 18, 40, 100, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 245, 180, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 5, 15, 50, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 20, 60, 160, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 60, 140, 240, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 140, 210, 255, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 240, 255, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 78},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 79},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 15, 30, 75, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 20, 35, 80, 20, nullptr, -1},
};

// SAWMILL_THEME (_bundle.py:3465) — 55 kunci
const ThemeEntry kTheme40[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Sawmill Warlord", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "grimkor", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Sawmill Warlord", -1},
    {"radiant_grass_1", KIND_COLOR3, 25, 40, 20, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 55, 90, 45, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 110, 155, 80, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 170, 210, 130, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 200, 195, 180, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 60, 68, 85, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 18, 15, 12, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 45, 40, 35, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 95, 50, 20, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 175, 105, 40, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 35, 32, 30, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 30, 8, 2, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 55, 65, 45, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 110, 90, 50, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 20, 18, 14, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 55, 48, 40, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 100, 92, 80, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 155, 148, 135, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 35, 30, 25, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 250, 200, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 30, 8, 2, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 110, 30, 8, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 220, 90, 20, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 255, 165, 50, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 250, 200, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 80},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 81},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 55, 50, 45, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 60, 40, 15, 20, nullptr, -1},
};

// CROWEYE_THEME (_bundle.py:3545) — 55 kunci
const ThemeEntry kTheme41[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Crow-Eyed", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "kaineroth", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Crow-Eyed", -1},
    {"radiant_grass_1", KIND_COLOR3, 5, 3, 8, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 18, 12, 22, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 35, 25, 42, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 60, 45, 70, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 95, 75, 110, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 85, 15, 20, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 30, 6, 8, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 85, 15, 20, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 170, 35, 45, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 230, 70, 80, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 20, 15, 25, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 3, 2, 5, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 40, 28, 50, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 110, 40, 55, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 8, 5, 12, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 28, 18, 35, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 55, 38, 65, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 95, 70, 105, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 50, 20, 30, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 130, 130, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 30, 6, 8, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 85, 15, 20, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 170, 35, 45, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 230, 70, 80, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 150, 150, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 82},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 83},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 25, 15, 32, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 45, 10, 16, 20, nullptr, -1},
};

// CRYSTALSTORM_THEME (_bundle.py:3625) — 55 kunci
const ThemeEntry kTheme42[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Stormherald", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "zyvareth", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Stormherald", -1},
    {"radiant_grass_1", KIND_COLOR3, 5, 30, 40, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 15, 75, 90, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 40, 145, 165, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 100, 215, 225, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 170, 245, 250, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 75, 25, 130, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 25, 5, 55, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 75, 25, 130, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 155, 60, 220, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 215, 130, 250, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 95, 60, 15, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 4, 10, 20, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 30, 90, 105, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 95, 105, 190, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 8, 18, 25, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 25, 55, 70, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 55, 110, 130, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 100, 175, 190, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 45, 20, 75, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 240, 255, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 25, 5, 55, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 75, 25, 130, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 155, 60, 220, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 215, 130, 250, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 240, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 84},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 85},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 15, 75, 90, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 25, 40, 75, 20, nullptr, -1},
};

// ETERNALWARLORD_THEME (_bundle.py:3705) — 55 kunci
const ThemeEntry kTheme43[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Eternal Warlord", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "kagetsuka", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Eternal Warlord", -1},
    {"radiant_grass_1", KIND_COLOR3, 25, 10, 15, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 70, 20, 30, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 130, 40, 50, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 185, 75, 85, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 240, 130, 130, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 110, 10, 20, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 35, 0, 5, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 110, 10, 20, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 200, 30, 40, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 255, 90, 90, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 20, 18, 30, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 15, 5, 8, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 65, 30, 40, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 130, 55, 60, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 16, 8, 12, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 45, 18, 25, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 85, 40, 50, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 135, 75, 85, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 60, 15, 22, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 180, 160, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 35, 0, 5, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 110, 10, 20, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 200, 30, 40, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 255, 90, 90, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 180, 160, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 86},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 87},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 45, 12, 18, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 55, 12, 16, 20, nullptr, -1},
};

// EXPLOSIVEART_THEME (_bundle.py:3785) — 55 kunci
const ThemeEntry kTheme44[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Explosive Artist", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "deidara", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Explosive Artist", -1},
    {"radiant_grass_1", KIND_COLOR3, 5, 5, 8, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 18, 18, 24, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 40, 40, 50, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 70, 70, 85, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 100, 100, 120, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 130, 15, 20, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 60, 5, 8, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 130, 15, 20, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 200, 30, 35, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 250, 70, 60, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 90, 60, 15, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 10, 6, 10, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 45, 35, 50, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 130, 45, 40, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 10, 8, 12, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 35, 28, 38, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 70, 60, 75, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 115, 100, 120, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 55, 12, 16, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 150, 130, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 60, 5, 8, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 130, 15, 20, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 200, 30, 35, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 250, 70, 60, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 150, 130, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 88},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 89},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 40, 25, 30, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 55, 15, 15, 20, nullptr, -1},
};

// SANDSHADOW_THEME (_bundle.py:3865) — 55 kunci
const ThemeEntry kTheme45[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Sand Shadow", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "sunakage", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Sand Shadow", -1},
    {"radiant_grass_1", KIND_COLOR3, 25, 8, 10, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 65, 18, 22, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 110, 30, 35, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 160, 55, 60, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 200, 90, 90, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 170, 30, 20, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 55, 15, 8, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 120, 35, 20, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 180, 60, 30, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 220, 100, 55, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 90, 15, 10, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 12, 5, 7, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 90, 30, 32, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 150, 55, 40, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 22, 10, 12, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 60, 25, 28, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 105, 45, 48, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 155, 80, 80, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 70, 18, 16, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 250, 150, 100, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 55, 15, 8, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 120, 35, 20, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 180, 60, 30, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 220, 100, 55, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 250, 150, 100, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 90},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 91},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 120, 50, 35, 45, nullptr, -1},
    {"fog_count", KIND_INT, 16, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 75, 30, 20, 20, nullptr, -1},
};

// EMBERWEAVER_THEME (_bundle.py:3945) — 55 kunci
const ThemeEntry kTheme46[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Emberweaver", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "pyraena", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Emberweaver", -1},
    {"radiant_grass_1", KIND_COLOR3, 35, 8, 15, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 85, 20, 30, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 145, 35, 50, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 200, 60, 80, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 240, 120, 130, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 230, 100, 30, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 85, 20, 10, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 160, 45, 20, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 230, 100, 30, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 255, 165, 60, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 95, 65, 15, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 18, 5, 8, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 110, 35, 45, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 180, 80, 45, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 22, 8, 14, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 60, 20, 30, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 110, 40, 55, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 165, 70, 85, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 80, 15, 25, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 245, 190, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 85, 20, 10, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 160, 45, 20, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 230, 100, 30, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 255, 165, 60, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 220, 130, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 92},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 93},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 85, 30, 30, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 85, 25, 20, 20, nullptr, -1},
};

// SKYFURY_THEME (_bundle.py:4025) — 55 kunci
const ThemeEntry kTheme47[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Skyfury", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "cogsworth", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Skyfury", -1},
    {"radiant_grass_1", KIND_COLOR3, 12, 12, 15, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 35, 35, 42, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 75, 75, 85, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 135, 135, 148, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 200, 200, 215, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 35, 120, 145, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 35, 18, 8, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 90, 50, 20, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 170, 100, 40, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 230, 155, 75, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 45, 15, 5, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 8, 8, 10, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 60, 55, 60, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 110, 90, 45, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 10, 10, 14, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 32, 32, 40, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 70, 70, 82, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 120, 120, 135, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 25, 25, 32, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 250, 210, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 45, 15, 5, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 140, 45, 15, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 230, 105, 30, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 255, 175, 65, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 250, 210, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 94},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 95},
    {"particle_count", KIND_INT, 60, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 45, 45, 55, 45, nullptr, -1},
    {"fog_count", KIND_INT, 18, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 60, 40, 20, 20, nullptr, -1},
};

// MOONREAPER_THEME (_bundle.py:4105) — 55 kunci
const ThemeEntry kTheme48[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Moonreaper", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "yomigetsu", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Moonreaper", -1},
    {"radiant_grass_1", KIND_COLOR3, 25, 22, 45, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 45, 42, 70, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 75, 72, 105, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 110, 105, 145, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 150, 145, 185, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 70, 55, 110, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 18, 10, 30, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 40, 25, 60, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 70, 45, 100, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 105, 70, 140, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 35, 20, 55, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 8, 5, 15, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 50, 45, 75, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 85, 70, 115, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 35, 30, 55, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 60, 55, 90, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 95, 90, 135, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 140, 135, 180, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 60, 45, 90, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 250, 235, 255, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 15, 5, 40, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 55, 20, 110, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 140, 70, 220, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 200, 140, 255, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 250, 235, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 96},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 97},
    {"particle_count", KIND_INT, 50, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 40, 25, 70, 40, nullptr, -1},
    {"fog_count", KIND_INT, 16, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 45, 30, 80, 25, nullptr, -1},
};

// MOONFANG_THEME (_bundle.py:4186) — 55 kunci
const ThemeEntry kTheme49[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Moonfang Prince", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "akirakumo", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Moonfang Prince", -1},
    {"radiant_grass_1", KIND_COLOR3, 35, 40, 60, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 60, 68, 90, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 110, 118, 140, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 160, 165, 185, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 210, 212, 225, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 85, 55, 145, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 30, 18, 55, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 65, 45, 115, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 115, 85, 175, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 160, 130, 215, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 45, 35, 70, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 12, 10, 22, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 60, 60, 80, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 90, 75, 130, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 45, 48, 62, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 80, 85, 105, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 130, 135, 155, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 185, 188, 205, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 75, 55, 115, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 240, 165, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 25, 15, 50, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 70, 45, 125, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 140, 105, 195, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 205, 180, 240, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 250, 245, 252, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 98},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 99},
    {"particle_count", KIND_INT, 55, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 60, 55, 85, 40, nullptr, -1},
    {"fog_count", KIND_INT, 17, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 65, 60, 95, 22, nullptr, -1},
};

// EMBERLION_THEME (_bundle.py:4267) — 55 kunci
const ThemeEntry kTheme50[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Emberlion Ronin", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "kaithros", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Emberlion Ronin", -1},
    {"radiant_grass_1", KIND_COLOR3, 35, 30, 28, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 60, 55, 50, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 110, 100, 90, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 170, 160, 150, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 235, 225, 215, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 200, 90, 25, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 30, 8, 2, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 85, 20, 8, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 150, 45, 15, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 220, 90, 25, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 45, 15, 5, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 10, 4, 2, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 80, 70, 60, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 150, 95, 40, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 30, 25, 22, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 65, 58, 50, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 115, 105, 92, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 175, 165, 150, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 150, 60, 15, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 250, 200, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 30, 5, 0, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 90, 20, 5, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 220, 90, 20, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 255, 150, 40, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 250, 200, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "ember", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 100},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 101},
    {"particle_count", KIND_INT, 50, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 45, 20, 10, 40, nullptr, -1},
    {"fog_count", KIND_INT, 16, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 80, 40, 15, 22, nullptr, -1},
};

// LUNARHERALD_THEME (_bundle.py:4348) — 55 kunci
const ThemeEntry kTheme51[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Lunar Herald", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "nyxaris", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Lunar Herald", -1},
    {"radiant_grass_1", KIND_COLOR3, 12, 16, 28, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 28, 34, 52, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 60, 70, 100, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 110, 120, 155, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 175, 190, 220, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 120, 180, 230, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 25, 8, 40, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 55, 25, 90, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 110, 60, 150, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 170, 120, 210, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 35, 15, 45, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 10, 8, 15, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 45, 48, 70, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 85, 70, 120, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 18, 20, 32, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 45, 50, 72, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 90, 95, 125, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 150, 155, 190, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 50, 90, 140, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 240, 250, 255, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 20, 35, 60, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 50, 90, 140, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 120, 180, 230, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 200, 235, 255, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 240, 250, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 102},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 103},
    {"particle_count", KIND_INT, 55, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 30, 40, 65, 42, nullptr, -1},
    {"fog_count", KIND_INT, 17, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 35, 50, 80, 22, nullptr, -1},
};

// MOONBORN_THEME (_bundle.py:4429) — 55 kunci
const ThemeEntry kTheme52[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Moon-Born Sovereign", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "tsukiyora", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Moon-Born Sovereign", -1},
    {"radiant_grass_1", KIND_COLOR3, 35, 33, 45, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 70, 66, 85, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 130, 125, 145, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 190, 186, 205, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 240, 238, 248, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 110, 65, 155, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 25, 8, 12, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 70, 18, 25, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 150, 35, 42, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 215, 70, 60, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 30, 15, 25, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 6, 3, 10, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 70, 65, 85, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 120, 90, 130, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 40, 38, 55, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 80, 78, 100, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 135, 132, 158, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 195, 192, 215, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 60, 35, 95, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 253, 255, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 25, 15, 40, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 60, 35, 95, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 110, 65, 155, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 170, 120, 210, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 253, 255, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "firefly", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 104},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 105},
    {"particle_count", KIND_INT, 55, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 55, 50, 70, 40, nullptr, -1},
    {"fog_count", KIND_INT, 17, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 70, 60, 90, 20, nullptr, -1},
};

// HOLLOWBANE_THEME (_bundle.py:4510) — 55 kunci
const ThemeEntry kTheme53[] = {
    {"name", KIND_STR, 0, 0, 0, 0, "The Substitute Shinigami", -1},
    {"boss_identity", KIND_STR, 0, 0, 0, 0, "hollowbane", -1},
    {"boss_title", KIND_STR, 0, 0, 0, 0, "The Substitute Shinigami", -1},
    {"radiant_grass_1", KIND_COLOR3, 8, 10, 18, 0, nullptr, -1},
    {"radiant_grass_2", KIND_COLOR3, 22, 24, 36, 0, nullptr, -1},
    {"radiant_grass_3", KIND_COLOR3, 48, 50, 66, 0, nullptr, -1},
    {"radiant_grass_4", KIND_COLOR3, 80, 82, 100, 0, nullptr, -1},
    {"radiant_grass_high", KIND_COLOR3, 120, 122, 142, 0, nullptr, -1},
    {"radiant_moss", KIND_COLOR3, 220, 110, 25, 0, nullptr, -1},
    {"dire_earth_1", KIND_COLOR3, 60, 15, 0, 0, nullptr, -1},
    {"dire_earth_2", KIND_COLOR3, 140, 45, 5, 0, nullptr, -1},
    {"dire_earth_3", KIND_COLOR3, 230, 95, 15, 0, nullptr, -1},
    {"dire_earth_4", KIND_COLOR3, 255, 155, 45, 0, nullptr, -1},
    {"dire_ash", KIND_COLOR3, 80, 30, 8, 0, nullptr, -1},
    {"dire_burnt", KIND_COLOR3, 8, 6, 12, 0, nullptr, -1},
    {"transition_1", KIND_COLOR3, 45, 46, 62, 0, nullptr, -1},
    {"transition_2", KIND_COLOR3, 130, 80, 35, 0, nullptr, -1},
    {"path_stone_1", KIND_COLOR3, 15, 16, 26, 0, nullptr, -1},
    {"path_stone_2", KIND_COLOR3, 40, 42, 60, 0, nullptr, -1},
    {"path_stone_3", KIND_COLOR3, 78, 80, 102, 0, nullptr, -1},
    {"path_stone_4", KIND_COLOR3, 130, 132, 158, 0, nullptr, -1},
    {"path_moss", KIND_COLOR3, 180, 70, 20, 0, nullptr, -1},
    {"path_crack", KIND_COLOR3, 255, 245, 200, 0, nullptr, -1},
    {"river_deep", KIND_COLOR3, 60, 15, 0, 0, nullptr, -1},
    {"river_mid", KIND_COLOR3, 140, 45, 5, 0, nullptr, -1},
    {"river_light", KIND_COLOR3, 230, 95, 15, 0, nullptr, -1},
    {"river_glow", KIND_COLOR3, 255, 155, 45, 0, nullptr, -1},
    {"river_foam", KIND_COLOR3, 255, 245, 200, 0, nullptr, -1},
    {"has_dark_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dead_trees", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_gravestones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_crystals_blue", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_crystals_red", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_ancient_ruins", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_bones", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_mushrooms_dark", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_rocks_mossy", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_dark_bushes", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_glow_flowers", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_spike_traps", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_torch_stones", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"has_cactus", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_palm_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_sand_dunes", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_ice_crystals", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_frozen_trees", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"has_snow_drifts", KIND_BOOL, 0, 0, 0, 0, nullptr, -1},
    {"particle_type", KIND_STR, 0, 0, 0, 0, "ember", -1},
    {"particle_colors_radiant", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 106},
    {"particle_colors_dire", KIND_COLORLIST, 0, 0, 0, 0, nullptr, 107},
    {"particle_count", KIND_INT, 55, 0, 0, 0, nullptr, -1},
    {"fog_enabled", KIND_BOOL, 1, 0, 0, 0, nullptr, -1},
    {"fog_color", KIND_COLOR4, 30, 28, 40, 45, nullptr, -1},
    {"fog_count", KIND_INT, 17, 0, 0, 0, nullptr, -1},
    {"ambient_tint", KIND_COLOR4, 70, 45, 25, 20, nullptr, -1},
};

// Urutan = THEMES di _bundle.py.
const char *const kThemeNames[] = {
    "forest",
    "desert",
    "ice",
    "volcanic",
    "haunted",
    "ocean",
    "abyss",
    "nethervenom",
    "soulforged",
    "radiant",
    "abyssal",
    "eldritch",
    "sanctum",
    "eternalflame",
    "primordial",
    "celestialpeaks",
    "cosmic",
    "royal",
    "violet",
    "crimson",
    "spectral",
    "sundered",
    "empyrean",
    "solaris",
    "abysstide",
    "crimsonmatriarch",
    "astral",
    "shadowchain",
    "frostveil",
    "warshade",
    "outlaw",
    "hexbound",
    "voidbound",
    "earthborn",
    "heartbane",
    "sunfist",
    "voidwing",
    "crimsondevourer",
    "elementweave",
    "tempest",
    "sawmill",
    "croweye",
    "crystalstorm",
    "eternalwarlord",
    "explosiveart",
    "sandshadow",
    "emberweaver",
    "skyfury",
    "moonreaper",
    "moonfang",
    "emberlion",
    "lunarherald",
    "moonborn",
    "hollowbane",
};
const ThemeEntry *const kThemes[] = {
    kTheme0,
    kTheme1,
    kTheme2,
    kTheme3,
    kTheme4,
    kTheme5,
    kTheme6,
    kTheme7,
    kTheme8,
    kTheme9,
    kTheme10,
    kTheme11,
    kTheme12,
    kTheme13,
    kTheme14,
    kTheme15,
    kTheme16,
    kTheme17,
    kTheme18,
    kTheme19,
    kTheme20,
    kTheme21,
    kTheme22,
    kTheme23,
    kTheme24,
    kTheme25,
    kTheme26,
    kTheme27,
    kTheme28,
    kTheme29,
    kTheme30,
    kTheme31,
    kTheme32,
    kTheme33,
    kTheme34,
    kTheme35,
    kTheme36,
    kTheme37,
    kTheme38,
    kTheme39,
    kTheme40,
    kTheme41,
    kTheme42,
    kTheme43,
    kTheme44,
    kTheme45,
    kTheme46,
    kTheme47,
    kTheme48,
    kTheme49,
    kTheme50,
    kTheme51,
    kTheme52,
    kTheme53,
};
const int64_t kThemeEntryCounts[] = {
    55,
    55,
    55,
    55,
    69,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
    55,
};
const int64_t kThemeCount = 54;
const int64_t kForestIndex = 0; // THEMES.get(nama, FOREST_THEME)

// ═══ Replika CPython `random` (dipakai DecorationGenerator) ═══
// MT19937 manual + init_by_array untuk seed int — std::mt19937(seed) SALAH
// untuk keperluan ini (spike: draw pertama 1608637542 vs 2746317213 Python).
// getrandbits/randbelow/randint/choice meniru Modules/_randommodule.c +
// Lib/random.py (_randbelow: rejection sampling, k = bit_length).
struct PyMt {
    static const int N = 624;
    static const int M = 397;
    uint32_t mt[624];
    int mti;

    void init_genrand(uint32_t s) {
        mt[0] = s;
        for (mti = 1; mti < N; mti++) {
            mt[mti] = (1812433253UL * (mt[mti - 1] ^ (mt[mti - 1] >> 30)) + (uint32_t)mti);
            mt[mti] &= 0xffffffffUL;
        }
    }

    void init_by_array(const uint32_t *init_key, int key_length) {
        init_genrand(19650218UL);
        int i = 1;
        int j = 0;
        int k = (N > key_length ? N : key_length);
        for (; k; k--) {
            mt[i] = (mt[i] ^ ((mt[i - 1] ^ (mt[i - 1] >> 30)) * 1664525UL)) + init_key[j] + (uint32_t)j;
            mt[i] &= 0xffffffffUL;
            i++;
            j++;
            if (i >= N) { mt[0] = mt[N - 1]; i = 1; }
            if (j >= key_length) { j = 0; }
        }
        for (k = N - 1; k; k--) {
            mt[i] = (mt[i] ^ ((mt[i - 1] ^ (mt[i - 1] >> 30)) * 1566083941UL)) - (uint32_t)i;
            mt[i] &= 0xffffffffUL;
            i++;
            if (i >= N) { mt[0] = mt[N - 1]; i = 1; }
        }
        mt[0] = 0x80000000UL;
    }

    void seed_int(uint32_t n) {
        const uint32_t key[1] = { n };
        init_by_array(key, 1);
    }

    uint32_t genrand_int32() {
        static const uint32_t mag01[2] = { 0x0UL, 0x9908b0dfUL };
        if (mti >= N) {
            int kk;
            for (kk = 0; kk < N - M; kk++) {
                uint32_t y = (mt[kk] & 0x80000000UL) | (mt[kk + 1] & 0x7fffffffUL);
                mt[kk] = mt[kk + M] ^ (y >> 1) ^ mag01[y & 0x1UL];
            }
            for (; kk < N - 1; kk++) {
                uint32_t y = (mt[kk] & 0x80000000UL) | (mt[kk + 1] & 0x7fffffffUL);
                mt[kk] = mt[kk + (M - N)] ^ (y >> 1) ^ mag01[y & 0x1UL];
            }
            uint32_t y = (mt[N - 1] & 0x80000000UL) | (mt[0] & 0x7fffffffUL);
            mt[N - 1] = mt[M - 1] ^ (y >> 1) ^ mag01[y & 0x1UL];
            mti = 0;
        }
        uint32_t y = mt[mti++];
        y ^= (y >> 11);
        y ^= (y << 7) & 0x9d2c5680UL;
        y ^= (y << 15) & 0xefc60000UL;
        y ^= (y >> 18);
        return y;
    }

    // getrandbits(k), k <= 32 — persis _randommodule.c.
    uint32_t getrandbits(int k) {
        int words = (k + 31) / 32;
        uint64_t r = 0;
        for (int i = 0; i < words; i++) {
            r = (r << 32) | genrand_int32();
        }
        r >>= words * 32 - k;
        return (uint32_t)r;
    }

    // _randbelow(n) — Lib/random.py: k = bit_length, rejection loop.
    uint32_t randbelow(uint32_t n) {
        int k = 0;
        for (uint32_t t = n; t; t >>= 1) {
            k++;
        }
        uint32_t r = getrandbits(k);
        while (r >= n) {
            r = getrandbits(k);
        }
        return r;
    }

    // randint(a, b) = randrange(a, b+1) = _randbelow(b-a+1)+a.
    int64_t randint(int64_t a, int64_t b) {
        return a + (int64_t)randbelow((uint32_t)(b - a + 1));
    }

    // choice(seq) = seq[_randbelow(len(seq))] — indeksnya saja.
    int64_t choice_idx(int64_t n) {
        return (int64_t)randbelow((uint32_t)n);
    }
};

// ═══ Helper DecorationGenerator (port generate_all + validator) ═══
// Urutan draw RNG, ambang jarak, dan jumlah attempt = persis
// _bundle.py; dicek struktural tools/test_godot_map_data_parity.py dan
// dikunci perilaku oleh fixture map_data.json.
static double lane_threshold_y(int64_t x, int64_t map_w, int64_t map_h) {
    // threshold_y = 200 + (map_h - 400) * x / map_w — perkalian int
    // eksak lalu SATU pembulatan divisi, persis urutan Python.
    return 200.0 + (double)((map_h - 400) * x) / (double)map_w;
}

static bool is_radiant(int64_t x, int64_t y, int64_t map_w, int64_t map_h) {
    return (double)y > lane_threshold_y(x, map_w, map_h) + 20.0;
}

static bool is_dire(int64_t x, int64_t y, int64_t map_w, int64_t map_h) {
    return (double)y < lane_threshold_y(x, map_w, map_h) - 20.0;
}

static bool too_close_to_lane(const PackedVector2Array &lane_points, int64_t x, int64_t y, double min_dist) {
    for (int64_t i = 0; i < lane_points.size(); i++) {
        const Vector2 p = lane_points[i];
        if (std::hypot((double)x - (double)p.x, (double)y - (double)p.y) < min_dist) {
            return true;
        }
    }
    return false;
}

static bool too_close_to_river(const PackedVector2Array &river_points, int64_t x, int64_t y, double min_dist) {
    for (int64_t i = 0; i < river_points.size(); i++) {
        const Vector2 p = river_points[i];
        if (std::hypot((double)x - (double)p.x, (double)y - (double)p.y) < min_dist) {
            return true;
        }
    }
    return false;
}

static bool too_close_to_base(int64_t x, int64_t y, int64_t map_w, int64_t map_h) {
    // BUG ASLI DIREPLIKA: suku kedua = map_h - 120 - (map_h - y) = y - 120,
    // jadi lingkaran pertama berpusat di (120, 120) — sudut kiri-atas —
    // BUKAN di base Radiant (120, map_h-120). Jangan "diperbaiki": paritas
    // berarti dekor Python dan C++ lolos filter yang SAMA.
    if (std::hypot((double)(x - 120), (double)(map_h - 120 - (map_h - y))) < 120.0) {
        return true;
    }
    if (std::hypot((double)(x - (map_w - 120)), (double)(y - 120)) < 120.0) {
        return true;
    }
    return false;
}

static bool too_close_to_shop(const Array &shop_positions, int64_t x, int64_t y, double min_dist) {
    for (int64_t i = 0; i < shop_positions.size(); i++) {
        const Vector2 p = shop_positions[i];
        if (std::hypot((double)x - (double)p.x, (double)y - (double)p.y) < min_dist) {
            return true;
        }
    }
    return false;
}

static bool is_valid_spot(const PackedVector2Array &lane_points,
        const PackedVector2Array &river_points, const Array &shop_positions,
        int64_t map_w, int64_t map_h, int64_t x, int64_t y, double min_lane) {
    if (too_close_to_lane(lane_points, x, y, min_lane)) {
        return false;
    }
    if (too_close_to_river(river_points, x, y, 25.0)) {
        return false;
    }
    if (too_close_to_base(x, y, map_w, map_h)) {
        return false;
    }
    if (too_close_to_shop(shop_positions, x, y, 70.0)) {
        return false;
    }
    return true;
}

// Opsi random.choice generate_all — urutan = urutan kemunculan di _bundle.py.
// (Oracle membandingkan sekuens literal ini dengan AST Python.)
static const int64_t kChDarkTreeSize[] = { 16, 20, 24 };
static const int64_t kChDarkTreeVariant[] = { 0, 0, 1, 1, 2 };
static const int64_t kChDeadTreeSize[] = { 14, 18, 22 };
static const char *const kChRuinVariant[] = { "pillar", "arch", "wall" };
static const char *const kChBoneType[] = { "skull", "rib", "skeleton" };
static const int32_t kChMushDire[][3] = { { 140, 30, 30 }, { 100, 20, 60 }, { 80, 40, 80 } };
static const int32_t kChMushRadiant[][3] = { { 60, 80, 150 }, { 100, 60, 130 }, { 140, 50, 100 } };
static const int64_t kChRockSize[] = { 12, 16, 20 };
static const int64_t kChBushSize[] = { 12, 16 };
static const int32_t kChFlower[][3] = { { 100, 170, 240 }, { 150, 100, 200 },
        { 100, 200, 150 }, { 255, 200, 100 } }; // [0] = CRYSTAL_BLUE_L palettes.py
static const int64_t kChLandmark[] = { 0, 1, 2, 3 };

static Color rgb(int32_t r, int32_t g, int32_t b) {
    return Color((float)r / 255.0f, (float)g / 255.0f, (float)b / 255.0f);
}

static void push_point(Array &out, int64_t x, int64_t y) {
    Array e; e.resize(2); e[0] = x; e[1] = y; out.push_back(e);
}

} // namespace

static void push_theme_entry(Dictionary &d, const ThemeEntry &e) {
    const String key(e.key);
    switch (e.kind) {
        case KIND_STR: d[key] = String(e.s); break;
        case KIND_BOOL: d[key] = (e.v0 != 0); break;
        case KIND_INT: d[key] = (int64_t)e.v0; break;
        case KIND_COLOR3: d[key] = rgb(e.v0, e.v1, e.v2); break;
        case KIND_COLOR4:
            d[key] = Color((float)e.v0 / 255.0f, (float)e.v1 / 255.0f,
                    (float)e.v2 / 255.0f, (float)e.v3 / 255.0f);
            break;
        case KIND_COLORLIST: {
            PackedColorArray cols;
            cols.resize(3);
            for (int64_t i = 0; i < 3; i++) {
                cols[i] = rgb(kColorLists[e.list][i * 3],
                        kColorLists[e.list][i * 3 + 1], kColorLists[e.list][i * 3 + 2]);
            }
            d[key] = cols;
            break;
        }
        case KIND_NIL: d[key] = Variant(); break; // Python: None
    }
}

int64_t MysticMaps::tile_size() {
    return kTileSize;
}

Dictionary MysticMaps::palettes() {
    Dictionary d;
    for (int64_t i = 0; i < kPaletteCount; i++) {
        d[String(kPalettes[i].name)] = rgb(kPalettes[i].r, kPalettes[i].g, kPalettes[i].b);
    }
    return d;
}

Dictionary MysticMaps::build_theme(int64_t index) {
    if (index < 0 || index >= kThemeCount) {
        return Dictionary();
    }
    Dictionary d;
    for (int64_t i = 0; i < kThemeEntryCounts[index]; i++) {
        push_theme_entry(d, kThemes[index][i]);
    }
    return d;
}

int64_t MysticMaps::theme_index(const String &theme_name) {
    for (int64_t i = 0; i < kThemeCount; i++) {
        if (theme_name == String(kThemeNames[i])) {
            return i;
        }
    }
    return -1;
}

Array MysticMaps::theme_names() {
    Array out;
    out.resize(kThemeCount);
    for (int64_t i = 0; i < kThemeCount; i++) {
        out[i] = String(kThemeNames[i]);
    }
    return out;
}

int64_t MysticMaps::theme_count() {
    return kThemeCount;
}

Dictionary MysticMaps::get_theme(const String &theme_name) {
    // THEMES.get(theme_name, FOREST_THEME) — selalu Dictionary segar
    // (Python mengembalikan objek live yang BISA dimutasi; tidak ada
    // konsumen Godot yang memutasi — diaudit saat migrasi).
    const int64_t index = theme_index(theme_name);
    return build_theme(index < 0 ? kForestIndex : index);
}

Dictionary MysticMaps::all_themes() {
    Dictionary d;
    for (int64_t i = 0; i < kThemeCount; i++) {
        d[String(kThemeNames[i])] = build_theme(i);
    }
    return d;
}

String MysticMaps::catalog_signature() {
    // "<jumlah>:<awal>-<akhir>:<total entri>" — bukti lib memuat tabel
    // generasi yang sama dengan data repo.
    int64_t total = 0;
    for (int64_t i = 0; i < kThemeCount; i++) {
        total += kThemeEntryCounts[i];
    }
    String sig = String::num_int64(kThemeCount) + ":";
    if (kThemeCount > 0) {
        sig += String(kThemeNames[0]) + "-" + String(kThemeNames[kThemeCount - 1]);
    }
    sig += ":" + String::num_int64(total);
    return sig;
}

PackedVector2Array MysticMaps::make_curved_path(const PackedVector2Array &waypoints, int64_t smoothness) {
    // Catmull-Rom — port make_curved_path: urutan operasi double SAMA
    // persis (t3 = t*t*t, bukan t2*t), lalu int() = trunc ke nol.
    if (waypoints.size() < 2) {
        return waypoints; // Python: objek SAMA; di sini salinan (deviasi)
    }
    std::vector<Vector2> pts;
    pts.reserve((size_t)waypoints.size() + 2);
    pts.push_back(waypoints[0]);
    for (int64_t i = 0; i < waypoints.size(); i++) {
        pts.push_back(waypoints[i]);
    }
    pts.push_back(waypoints[waypoints.size() - 1]);
    PackedVector2Array out;
    for (size_t i = 0; i + 3 < pts.size(); i++) { // range(len(pts) - 3)
        const Vector2 p0 = pts[i];
        const Vector2 p1 = pts[i + 1];
        const Vector2 p2 = pts[i + 2];
        const Vector2 p3 = pts[i + 3];
        for (int64_t step = 0; step < smoothness; step++) {
            const double t = (double)step / (double)smoothness;
            const double t2 = t * t;
            const double t3 = t * t * t;
            const double x = 0.5 * ((2.0 * (double)p1.x) +
                    (-(double)p0.x + (double)p2.x) * t +
                    (2.0 * (double)p0.x - 5.0 * (double)p1.x + 4.0 * (double)p2.x - (double)p3.x) * t2 +
                    (-(double)p0.x + 3.0 * (double)p1.x - 3.0 * (double)p2.x + (double)p3.x) * t3);
            const double y = 0.5 * ((2.0 * (double)p1.y) +
                    (-(double)p0.y + (double)p2.y) * t +
                    (2.0 * (double)p0.y - 5.0 * (double)p1.y + 4.0 * (double)p2.y - (double)p3.y) * t2 +
                    (-(double)p0.y + 3.0 * (double)p1.y - 3.0 * (double)p2.y + (double)p3.y) * t3);
            out.append(Vector2((float)(int32_t)x, (float)(int32_t)y));
        }
    }
    out.append(waypoints[waypoints.size() - 1]);
    return out;
}

Dictionary MysticMaps::generate_lanes(int64_t map_w, int64_t map_h) {
    PackedVector2Array lane_top;
    lane_top.append(Vector2((float)(90), (float)((map_h - 130))));
    lane_top.append(Vector2((float)(85), (float)((map_h - 260))));
    lane_top.append(Vector2((float)(95), (float)((map_h - 380))));
    lane_top.append(Vector2((float)(120), (float)((map_h - 500))));
    lane_top.append(Vector2((float)(170), (float)(180)));
    lane_top.append(Vector2((float)(240), (float)(100)));
    lane_top.append(Vector2((float)(380), (float)(75)));
    lane_top.append(Vector2((float)(550), (float)(70)));
    lane_top.append(Vector2((float)(720), (float)(75)));
    lane_top.append(Vector2((float)(880), (float)(85)));
    lane_top.append(Vector2((float)(1030), (float)(110)));
    lane_top.append(Vector2((float)((map_w - 100)), (float)(180)));
    PackedVector2Array lane_mid;
    lane_mid.append(Vector2((float)(170), (float)((map_h - 170))));
    lane_mid.append(Vector2((float)(300), (float)((map_h - 300))));
    lane_mid.append(Vector2((float)(440), (float)((map_h - 400))));
    lane_mid.append(Vector2((float)(((map_w / 2) - 60)), (float)(((map_h / 2) + 40))));
    lane_mid.append(Vector2((float)((map_w / 2)), (float)((map_h / 2))));
    lane_mid.append(Vector2((float)(((map_w / 2) + 60)), (float)(((map_h / 2) - 40))));
    lane_mid.append(Vector2((float)((map_w - 440)), (float)(400)));
    lane_mid.append(Vector2((float)((map_w - 300)), (float)(300)));
    lane_mid.append(Vector2((float)((map_w - 170)), (float)(170)));
    PackedVector2Array lane_bot;
    lane_bot.append(Vector2((float)(130), (float)((map_h - 90))));
    lane_bot.append(Vector2((float)(260), (float)((map_h - 70))));
    lane_bot.append(Vector2((float)(420), (float)((map_h - 60))));
    lane_bot.append(Vector2((float)(600), (float)((map_h - 60))));
    lane_bot.append(Vector2((float)(780), (float)((map_h - 65))));
    lane_bot.append(Vector2((float)(940), (float)((map_h - 75))));
    lane_bot.append(Vector2((float)(1070), (float)((map_h - 100))));
    lane_bot.append(Vector2((float)((map_w - 110)), (float)((map_h - 220))));
    lane_bot.append(Vector2((float)((map_w - 90)), (float)((map_h - 380))));
    lane_bot.append(Vector2((float)((map_w - 85)), (float)(250)));
    lane_bot.append(Vector2((float)((map_w - 100)), (float)(180)));
    Dictionary d;
    d["top"] = make_curved_path(lane_top, 10);
    d["mid"] = make_curved_path(lane_mid, 8);
    d["bot"] = make_curved_path(lane_bot, 10);
    return d;
}

PackedVector2Array MysticMaps::generate_river(int64_t map_w, int64_t map_h) {
    PackedVector2Array pts;
    pts.append(Vector2((float)(0), (float)(200)));
    pts.append(Vector2((float)(150), (float)(270)));
    pts.append(Vector2((float)(350), (float)(350)));
    pts.append(Vector2((float)((map_w / 2)), (float)((map_h / 2))));
    pts.append(Vector2((float)((map_w - 350)), (float)((map_h - 350))));
    pts.append(Vector2((float)((map_w - 150)), (float)((map_h - 270))));
    pts.append(Vector2((float)(map_w), (float)((map_h - 200))));
    return make_curved_path(pts, 10);
}

Dictionary MysticMaps::generate_decorations(int64_t map_w, int64_t map_h,
        const PackedVector2Array &lane_points, const PackedVector2Array &river_points,
        const Array &shop_positions) {
    // Port generate_all: seed 42 -> 14 loop -> random.seed() akhir (no-op
    // yang TIDAK direplika: state RNG lokal per panggilan, efek globalnya
    // tak teramati dari output). TILE_SIZE = kTileSize.
    PyMt rng;
    rng.seed_int(42);
    const int64_t TS = kTileSize;
    const int64_t nx = map_w / TS - 3;
    const int64_t nx2 = map_w / TS - 2;
    const int64_t ny = map_h / TS - 3;
    const int64_t ny2 = map_h / TS - 2;
    Array dark_trees; Array dead_trees; Array gravestones;
    Array crystals_blue; Array crystals_red; Array ancient_ruins;
    Array bones; Array mushrooms_dark; Array rocks_mossy;
    Array dark_bushes; Array glow_flowers; Array spike_traps;
    Array torch_stones; Array boss_landmarks;
    // ─── DARK TREES (radiant) — 45 attempt ───
    for (int64_t attempt = 0; attempt < 45; attempt++) {
        const int64_t x = rng.randint(2, nx) * TS;
        const int64_t y = rng.randint(2, ny) * TS;
        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)
                && is_radiant(x, y, map_w, map_h)) {
            const int64_t size = kChDarkTreeSize[rng.choice_idx(3)];
            const int64_t variant = kChDarkTreeVariant[rng.choice_idx(5)];
            Array e; e.resize(4); e[0] = x; e[1] = y; e[2] = size; e[3] = variant;
            dark_trees.push_back(e);
        }
    }
    // ─── DEAD TREES (dire) — 35 attempt ───
    for (int64_t attempt = 0; attempt < 35; attempt++) {
        const int64_t x = rng.randint(2, nx) * TS;
        const int64_t y = rng.randint(2, ny) * TS;
        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)
                && is_dire(x, y, map_w, map_h)) {
            const int64_t size = kChDeadTreeSize[rng.choice_idx(3)];
            Array e; e.resize(3); e[0] = x; e[1] = y; e[2] = size;
            dead_trees.push_back(e);
        }
    }
    // ─── GRAVESTONES (dire) — 12 attempt ───
    for (int64_t attempt = 0; attempt < 12; attempt++) {
        const int64_t x = rng.randint(3, nx) * TS;
        const int64_t y = rng.randint(3, ny) * TS;
        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)
                && is_dire(x, y, map_w, map_h)) {
            push_point(gravestones, x, y);
        }
    }
    // ─── BLUE CRYSTALS (radiant) — 15 attempt ───
    for (int64_t attempt = 0; attempt < 15; attempt++) {
        const int64_t x = rng.randint(3, nx) * TS;
        const int64_t y = rng.randint(3, ny) * TS;
        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)
                && is_radiant(x, y, map_w, map_h)) {
            const int64_t size = rng.randint(8, 14);
            Array e; e.resize(3); e[0] = x; e[1] = y; e[2] = size;
            crystals_blue.push_back(e);
        }
    }
    // ─── RED CRYSTALS (dire) — 12 attempt ───
    for (int64_t attempt = 0; attempt < 12; attempt++) {
        const int64_t x = rng.randint(3, nx) * TS;
        const int64_t y = rng.randint(3, ny) * TS;
        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)
                && is_dire(x, y, map_w, map_h)) {
            const int64_t size = rng.randint(6, 12);
            Array e; e.resize(3); e[0] = x; e[1] = y; e[2] = size;
            crystals_red.push_back(e);
        }
    }
    // ─── ANCIENT RUINS — 10 attempt, min_lane 60 ───
    for (int64_t attempt = 0; attempt < 10; attempt++) {
        const int64_t x = rng.randint(3, nx) * TS;
        const int64_t y = rng.randint(3, ny) * TS;
        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 60.0)) {
            Array e; e.resize(3); e[0] = x; e[1] = y;
            e[2] = String(kChRuinVariant[rng.choice_idx(3)]);
            ancient_ruins.push_back(e);
        }
    }
    // ─── BONES (dire) — 15 attempt ───
    for (int64_t attempt = 0; attempt < 15; attempt++) {
        const int64_t x = rng.randint(3, nx) * TS;
        const int64_t y = rng.randint(3, ny) * TS;
        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)
                && is_dire(x, y, map_w, map_h)) {
            Array e; e.resize(3); e[0] = x; e[1] = y;
            e[2] = String(kChBoneType[rng.choice_idx(3)]);
            bones.push_back(e);
        }
    }
    // ─── DARK MUSHROOMS — 25 attempt (warna ikut sisi) ───
    for (int64_t attempt = 0; attempt < 25; attempt++) {
        const int64_t x = rng.randint(3, nx) * TS;
        const int64_t y = rng.randint(3, ny) * TS;
        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)) {
            const int64_t pick = rng.choice_idx(3);
            Array e; e.resize(3); e[0] = x; e[1] = y;
            if (is_dire(x, y, map_w, map_h)) {
                e[2] = rgb(kChMushDire[pick][0], kChMushDire[pick][1], kChMushDire[pick][2]);
            } else {
                e[2] = rgb(kChMushRadiant[pick][0], kChMushRadiant[pick][1], kChMushRadiant[pick][2]);
            }
            mushrooms_dark.push_back(e);
        }
    }
    // ─── MOSSY ROCKS — 20 attempt (batas -2, bukan -3) ───
    for (int64_t attempt = 0; attempt < 20; attempt++) {
        const int64_t x = rng.randint(2, nx2) * TS;
        const int64_t y = rng.randint(2, ny2) * TS;
        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)) {
            const int64_t size = kChRockSize[rng.choice_idx(3)];
            const bool has_moss = is_radiant(x, y, map_w, map_h);
            Array e; e.resize(4); e[0] = x; e[1] = y; e[2] = size; e[3] = has_moss;
            rocks_mossy.push_back(e);
        }
    }
    // ─── DARK BUSHES (radiant) — 20 attempt ───
    for (int64_t attempt = 0; attempt < 20; attempt++) {
        const int64_t x = rng.randint(2, nx2) * TS;
        const int64_t y = rng.randint(2, ny2) * TS;
        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)
                && is_radiant(x, y, map_w, map_h)) {
            const int64_t size = kChBushSize[rng.choice_idx(2)];
            Array e; e.resize(3); e[0] = x; e[1] = y; e[2] = size;
            dark_bushes.push_back(e);
        }
    }
    // ─── GLOWING FLOWERS (radiant) — 20 attempt ───
    for (int64_t attempt = 0; attempt < 20; attempt++) {
        const int64_t x = rng.randint(3, nx) * TS;
        const int64_t y = rng.randint(3, ny) * TS;
        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)
                && is_radiant(x, y, map_w, map_h)) {
            const int64_t pick = rng.choice_idx(4);
            Array e; e.resize(3); e[0] = x; e[1] = y;
            e[2] = rgb(kChFlower[pick][0], kChFlower[pick][1], kChFlower[pick][2]);
            glow_flowers.push_back(e);
        }
    }
    // ─── SPIKE TRAPS (dire) — 8 attempt ───
    for (int64_t attempt = 0; attempt < 8; attempt++) {
        const int64_t x = rng.randint(3, nx) * TS;
        const int64_t y = rng.randint(3, ny) * TS;
        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 50.0)
                && is_dire(x, y, map_w, map_h)) {
            push_point(spike_traps, x, y);
        }
    }
    // ─── BOSS LANDMARKS — while <30, maks 240 attempt, min_lane 74 ───
    int64_t landmark_attempts = 0;
    while (boss_landmarks.size() < 30 && landmark_attempts < 240) {
        landmark_attempts++;
        const int64_t x = rng.randint(3, nx) * TS;
        const int64_t y = rng.randint(3, ny) * TS;
        if (is_valid_spot(lane_points, river_points, shop_positions, map_w, map_h, x, y, 74.0)) {
            const int64_t variant = kChLandmark[rng.choice_idx(4)];
            Array e; e.resize(3); e[0] = x; e[1] = y; e[2] = variant;
            boss_landmarks.push_back(e);
        }
    }
    // ─── TORCH STONES (border, tanpa RNG) ───
    for (int64_t x = 120; x < map_w - 80; x += 200) {
        push_point(torch_stones, x, 32);
        push_point(torch_stones, x, map_h - 32);
    }
    for (int64_t y = 120; y < map_h - 80; y += 200) {
        push_point(torch_stones, 32, y);
        push_point(torch_stones, map_w - 32, y);
    }
    // Urutan kunci = urutan literal `data` generate_all Python.
    Dictionary d;
    d["dark_trees"] = dark_trees;
    d["dead_trees"] = dead_trees;
    d["gravestones"] = gravestones;
    d["crystals_blue"] = crystals_blue;
    d["crystals_red"] = crystals_red;
    d["ancient_ruins"] = ancient_ruins;
    d["bones"] = bones;
    d["mushrooms_dark"] = mushrooms_dark;
    d["rocks_mossy"] = rocks_mossy;
    d["dark_bushes"] = dark_bushes;
    d["glow_flowers"] = glow_flowers;
    d["spike_traps"] = spike_traps;
    d["torch_stones"] = torch_stones;
    d["boss_landmarks"] = boss_landmarks;
    return d;
}

void MysticMaps::_bind_methods() {
    ClassDB::bind_static_method("MysticMaps", D_METHOD("tile_size"), &MysticMaps::tile_size);
    ClassDB::bind_static_method("MysticMaps", D_METHOD("palettes"), &MysticMaps::palettes);
    ClassDB::bind_static_method("MysticMaps", D_METHOD("theme_names"), &MysticMaps::theme_names);
    ClassDB::bind_static_method("MysticMaps", D_METHOD("theme_count"), &MysticMaps::theme_count);
    ClassDB::bind_static_method("MysticMaps", D_METHOD("get_theme", "theme_name"), &MysticMaps::get_theme);
    ClassDB::bind_static_method("MysticMaps", D_METHOD("all_themes"), &MysticMaps::all_themes);
    ClassDB::bind_static_method("MysticMaps", D_METHOD("catalog_signature"), &MysticMaps::catalog_signature);
    ClassDB::bind_static_method("MysticMaps", D_METHOD("make_curved_path", "waypoints", "smoothness"), &MysticMaps::make_curved_path);
    ClassDB::bind_static_method("MysticMaps", D_METHOD("generate_lanes", "map_w", "map_h"), &MysticMaps::generate_lanes);
    ClassDB::bind_static_method("MysticMaps", D_METHOD("generate_river", "map_w", "map_h"), &MysticMaps::generate_river);
    ClassDB::bind_static_method("MysticMaps", D_METHOD("generate_decorations", "map_w", "map_h", "lane_points", "river_points", "shop_positions"), &MysticMaps::generate_decorations);
    ClassDB::bind_static_method("MysticMaps", D_METHOD("build_theme", "index"), &MysticMaps::build_theme);
    ClassDB::bind_static_method("MysticMaps", D_METHOD("theme_index", "theme_name"), &MysticMaps::theme_index);
}
