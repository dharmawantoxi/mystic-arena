// ═══ GENERATED — JANGAN SUNTING TANGAN ═══
// Sumber    : levels/level_data.py
// Generator : tools/gen_levels_cpp.py (AST Python -> C++, bukan terjemahan tangan)
// Regenerasi: python3 tools/gen_levels_cpp.py
// Cek CI    : python3 tools/gen_levels_cpp.py --check
// Desain    : docs/LEVELS_GODOTPP.md
#include "levels_processor.h"

using namespace godot;

namespace {

// Satu slot mini boss. Kunci wave STRING (lihat komentar build_row).
struct MiniBossSlot {
    const char *wave;
    const char *boss;
};

// Baris katalog. Kolom = kunci level_data.py (skema dibaca generator dari
// AST, jadi field baru di Python otomatis jadi kolom baru di sini).
// POD murni: tidak ada Variant statis (aman terhadap urutan teardown lib).
struct LevelRow {
    int64_t level_number;
    const char *name;
    const char *description;
    double enemy_hp_mult;
    double enemy_damage_mult;
    double enemy_speed_mult;
    int64_t castle_start_level;
    int64_t starting_gold;
    int64_t starting_castle_level;
    const char *map_theme;
    const char *bgm_track;
    const MiniBossSlot *mini_bosses;
    int64_t mini_bosses_count;
    const char *true_boss;
    int64_t meta_gold_reward_win;
    int64_t meta_gold_reward_replay;
    int64_t meta_gold_reward_lose;
    int64_t unlock_after_level;
    bool has_unlock_after_level;
};

// LEVEL_1 mini_bosses (3 slot) — level_data.py:13
const MiniBossSlot kMini1[] = {
    {"10", "gornak"},
    {"15", "morgath"},
    {"25", "drakar"},
};

// LEVEL_2 mini_bosses (3 slot) — level_data.py:50
const MiniBossSlot kMini2[] = {
    {"10", "razak"},
    {"15", "khalros"},
    {"20", "gorath"},
};

// LEVEL_3 mini_bosses (3 slot) — level_data.py:81
const MiniBossSlot kMini3[] = {
    {"25", "varkul"},
    {"10", "xerathis"},
    {"17", "nyzrak"},
};

// LEVEL_4 mini_bosses (3 slot) — level_data.py:111
const MiniBossSlot kMini4[] = {
    {"10", "zharok"},
    {"17", "pyrenth"},
    {"25", "vokrahn"},
};

// LEVEL_5 mini_bosses (3 slot) — level_data.py:142
const MiniBossSlot kMini5[] = {
    {"10", "nyxara"},
    {"18", "gravefang"},
    {"25", "vhalzun"},
};

// LEVEL_6 mini_bosses (3 slot) — level_data.py:181
const MiniBossSlot kMini6[] = {
    {"10", "gravewake"},
    {"18", "syrentha"},
    {"25", "thalgryn"},
};

// LEVEL_7 mini_bosses (3 slot) — level_data.py:219
const MiniBossSlot kMini7[] = {
    {"10", "malzareth"},
    {"15", "akashari"},
    {"25", "vorenmarr"},
};

// LEVEL_8 mini_bosses (3 slot) — level_data.py:257
const MiniBossSlot kMini8[] = {
    {"10", "xirthalis"},
    {"18", "vhyssarion"},
    {"25", "vaerith"},
};

// LEVEL_9 mini_bosses (3 slot) — level_data.py:297
const MiniBossSlot kMini9[] = {
    {"10", "kenshiro"},
    {"18", "khazan"},
    {"25", "wiro"},
};

// LEVEL_10 mini_bosses (3 slot) — level_data.py:338
const MiniBossSlot kMini10[] = {
    {"10", "krognarr"},
    {"18", "raz"},
    {"25", "vraskhan"},
};

// LEVEL_11 mini_bosses (3 slot) — level_data.py:379
const MiniBossSlot kMini11[] = {
    {"10", "aeralith"},
    {"18", "aurex"},
    {"25", "nyxareva"},
};

// LEVEL_12 mini_bosses (3 slot) — level_data.py:420
const MiniBossSlot kMini12[] = {
    {"10", "aurelix"},
    {"18", "aurelyssa"},
    {"25", "vargrath"},
};

// LEVEL_13 mini_bosses (3 slot) — level_data.py:461
const MiniBossSlot kMini13[] = {
    {"10", "kaeldris"},
    {"18", "pyraklos"},
    {"25", "velmyrth"},
};

// LEVEL_14 mini_bosses (3 slot) — level_data.py:502
const MiniBossSlot kMini14[] = {
    {"10", "azureth"},
    {"18", "luminar"},
    {"25", "solara"},
};

// LEVEL_15 mini_bosses (3 slot) — level_data.py:542
const MiniBossSlot kMini15[] = {
    {"10", "auroth"},
    {"18", "morvein"},
    {"25", "thorvak"},
};

// LEVEL_16 mini_bosses (3 slot) — level_data.py:582
const MiniBossSlot kMini16[] = {
    {"10", "ignirus"},
    {"18", "leoric"},
    {"25", "shirotaka"},
};

// LEVEL_17 mini_bosses (3 slot) — level_data.py:622
const MiniBossSlot kMini17[] = {
    {"10", "kaelthorn"},
    {"18", "solvanth"},
    {"25", "xyrael"},
};

// LEVEL_18 mini_bosses (3 slot) — level_data.py:662
const MiniBossSlot kMini18[] = {
    {"10", "cryssalia"},
    {"18", "kaelthar"},
    {"25", "morkhaera"},
};

// LEVEL_19 mini_bosses (3 slot) — level_data.py:702
const MiniBossSlot kMini19[] = {
    {"10", "akahime"},
    {"18", "nyxthrael"},
    {"25", "sylvantheros"},
};

// LEVEL_20 mini_bosses (3 slot) — level_data.py:742
const MiniBossSlot kMini20[] = {
    {"10", "astraelion"},
    {"18", "morvaenthir"},
    {"25", "thornvaegrim"},
};

// LEVEL_21 mini_bosses (3 slot) — level_data.py:782
const MiniBossSlot kMini21[] = {
    {"10", "kurogari"},
    {"18", "morvekhar"},
    {"25", "vorgath"},
};

// LEVEL_22 mini_bosses (3 slot) — level_data.py:825
const MiniBossSlot kMini22[] = {
    {"10", "grimstalker"},
    {"18", "kryvoxar"},
    {"25", "vargroth"},
};

// LEVEL_23 mini_bosses (3 slot) — level_data.py:868
const MiniBossSlot kMini23[] = {
    {"10", "drav"},
    {"18", "lyrienne"},
    {"25", "valthar"},
};

// LEVEL_24 mini_bosses (3 slot) — level_data.py:911
const MiniBossSlot kMini24[] = {
    {"10", "khalzaredh"},
    {"18", "nyxaroth"},
    {"25", "veshtrax"},
};

// LEVEL_25 mini_bosses (3 slot) — level_data.py:954
const MiniBossSlot kMini25[] = {
    {"10", "grimjack"},
    {"18", "morvaeth"},
    {"25", "vulkareth"},
};

// LEVEL_26 mini_bosses (3 slot) — level_data.py:997
const MiniBossSlot kMini26[] = {
    {"10", "aelyrion"},
    {"18", "kaervosth"},
    {"25", "morvyssk"},
};

// LEVEL_27 mini_bosses (3 slot) — level_data.py:1040
const MiniBossSlot kMini27[] = {
    {"10", "kyumirra"},
    {"18", "morvakhul"},
    {"25", "nyxariel"},
};

// LEVEL_28 mini_bosses (3 slot) — level_data.py:1083
const MiniBossSlot kMini28[] = {
    {"10", "morthyrax"},
    {"18", "sanguiveth"},
    {"25", "xerakhotep"},
};

// LEVEL_29 mini_bosses (3 slot) — level_data.py:1126
const MiniBossSlot kMini29[] = {
    {"10", "ignakhor"},
    {"18", "kazureth"},
    {"25", "sethrakhar"},
};

// LEVEL_30 mini_bosses (3 slot) — level_data.py:1169
const MiniBossSlot kMini30[] = {
    {"10", "kaelvyrn"},
    {"18", "thorvin"},
    {"25", "xaerissa"},
};

// LEVEL_31 mini_bosses (3 slot) — level_data.py:1212
const MiniBossSlot kMini31[] = {
    {"10", "celwynn"},
    {"18", "rynvara"},
    {"25", "syrindra"},
};

// LEVEL_32 mini_bosses (3 slot) — level_data.py:1255
const MiniBossSlot kMini32[] = {
    {"10", "ghrakmaal"},
    {"18", "selunara"},
    {"25", "vessyra"},
};

// LEVEL_33 mini_bosses (3 slot) — level_data.py:1298
const MiniBossSlot kMini33[] = {
    {"10", "rakzhan"},
    {"18", "sirakzan"},
    {"25", "valekris"},
};

// LEVEL_34 mini_bosses (3 slot) — level_data.py:1341
const MiniBossSlot kMini34[] = {
    {"10", "infrakzaar"},
    {"18", "xarnathul"},
    {"25", "zhyrakaan"},
};

// LEVEL_35 mini_bosses (3 slot) — level_data.py:1384
const MiniBossSlot kMini35[] = {
    {"10", "kaerissa"},
    {"18", "thorgaruk"},
    {"25", "zorathiel"},
};

// LEVEL_36 mini_bosses (3 slot) — level_data.py:1427
const MiniBossSlot kMini36[] = {
    {"10", "nyxallaria"},
    {"18", "vhaerinth"},
    {"25", "xharokh"},
};

// LEVEL_37 mini_bosses (3 slot) — level_data.py:1470
const MiniBossSlot kMini37[] = {
    {"10", "kazreth"},
    {"18", "varkuthar"},
    {"25", "zhyvrek"},
};

// LEVEL_38 mini_bosses (3 slot) — level_data.py:1513
const MiniBossSlot kMini38[] = {
    {"10", "azkharion"},
    {"18", "thargoroth"},
    {"25", "zahkareth"},
};

// LEVEL_39 mini_bosses (3 slot) — level_data.py:1556
const MiniBossSlot kMini39[] = {
    {"10", "bhorgathul"},
    {"18", "morkhelvis"},
    {"25", "vorthakul"},
};

// LEVEL_40 mini_bosses (3 slot) — level_data.py:1599
const MiniBossSlot kMini40[] = {
    {"10", "urgharun"},
    {"18", "yhoranth"},
    {"25", "zulkhaven"},
};

// LEVEL_41 mini_bosses (3 slot) — level_data.py:1642
const MiniBossSlot kMini41[] = {
    {"10", "emberwick"},
    {"18", "grondarthul"},
    {"25", "xareth"},
};

// LEVEL_42 mini_bosses (3 slot) — level_data.py:1685
const MiniBossSlot kMini42[] = {
    {"10", "kaedrin"},
    {"18", "morvaeth2"},
    {"25", "vardrok"},
};

// LEVEL_43 mini_bosses (3 slot) — level_data.py:1728
const MiniBossSlot kMini43[] = {
    {"10", "nixweaver"},
    {"18", "nyxraal"},
    {"25", "xarnthuul"},
};

// LEVEL_44 mini_bosses (3 slot) — level_data.py:1771
const MiniBossSlot kMini44[] = {
    {"10", "lyrenya"},
    {"18", "vyraeth"},
    {"25", "zorothrax"},
};

// LEVEL_45 mini_bosses (3 slot) — level_data.py:1814
const MiniBossSlot kMini45[] = {
    {"10", "akiraze"},
    {"18", "brumhar"},
    {"25", "zorashi"},
};

// LEVEL_46 mini_bosses (3 slot) — level_data.py:1857
const MiniBossSlot kMini46[] = {
    {"10", "akaroth"},
    {"18", "kassadin"},
    {"25", "shimorakh"},
};

// LEVEL_47 mini_bosses (3 slot) — level_data.py:1900
const MiniBossSlot kMini47[] = {
    {"10", "kaizoku_raijin"},
    {"18", "korokai"},
    {"25", "verdanix"},
};

// LEVEL_48 mini_bosses (3 slot) — level_data.py:1943
const MiniBossSlot kMini48[] = {
    {"10", "broggmar"},
    {"18", "ursath"},
    {"25", "zhaeris"},
};

// LEVEL_49 mini_bosses (3 slot) — level_data.py:1986
const MiniBossSlot kMini49[] = {
    {"10", "kairenji"},
    {"18", "karzhul"},
    {"25", "xerakkuth"},
};

// LEVEL_50 mini_bosses (3 slot) — level_data.py:2029
const MiniBossSlot kMini50[] = {
    {"10", "kaelthys"},
    {"18", "kaoruken"},
    {"25", "vaelkorr"},
};

// LEVEL_51 mini_bosses (3 slot) — level_data.py:2072
const MiniBossSlot kMini51[] = {
    {"10", "aurelian"},
    {"18", "morvath"},
    {"25", "pyrhaan"},
};

// LEVEL_52 mini_bosses (3 slot) — level_data.py:2115
const MiniBossSlot kMini52[] = {
    {"10", "garumenshi"},
    {"18", "thoraz"},
    {"25", "vhaerith"},
};

// LEVEL_53 mini_bosses (3 slot) — level_data.py:2158
const MiniBossSlot kMini53[] = {
    {"10", "dorakai"},
    {"18", "hitokage"},
    {"25", "kazuren"},
};

// LEVEL_54 mini_bosses (3 slot) — level_data.py:2201
const MiniBossSlot kMini54[] = {
    {"10", "obanai"},
    {"18", "sanguire"},
    {"25", "sasori"},
};

// 54 level — urutan = ALL_LEVELS di level_data.py.
const LevelRow kLevels[] = {
    // LEVEL_1 (level_data.py:13)
    {1, "The Fallen Realm", "Face Abaddon, the Lord of Avernus", 1.0, 1.0, 1.0, 1, 1000, 1, "forest", "bgm_battle.wav", kMini1, 3, "abaddon", 3000, 1500, 0, 0, false},
    // LEVEL_2 (level_data.py:50)
    {2, "Wraith Wastes", "Confront the Phantom King", 1.02, 1.02, 1.02, 1, 1000, 1, "desert", "bgm_battle.wav", kMini2, 3, "alchemist", 3000, 1500, 0, 1, true},
    // LEVEL_3 (level_data.py:81)
    {3, "Infernal Depths", "Face the Flame Emperor", 1.03, 1.03, 1.03, 1, 1000, 1, "ice", "bgm_battle.wav", kMini3, 3, "ancient_apparition", 3000, 1500, 0, 2, true},
    // LEVEL_4 (level_data.py:111)
    {4, "Molten Sanctum", "Face Ignis Drachorn, the Molten Sovereign", 1.04, 1.04, 1.04, 1, 1000, 1, "volcanic", "bgm_battle.wav", kMini4, 3, "ignis_drachorn", 3000, 1500, 0, 3, true},
    // LEVEL_5 (level_data.py:142)
    {5, "The Haunted Veil", "Face Krobellus, the Death Prophet", 1.05, 1.05, 1.05, 1, 1000, 1, "haunted", "bgm_battle.wav", kMini5, 3, "krobellus", 3000, 1500, 0, 4, true},
    // LEVEL_6 (level_data.py:181)
    {6, "Admiral's Cove", "Face Kunkka, the Admiral of the Fleet", 1.06, 1.06, 1.06, 1, 1000, 1, "ocean", "bgm_battle.wav", kMini6, 3, "kunkka", 3000, 1500, 0, 5, true},
    // LEVEL_7 (level_data.py:219)
    {7, "Shadow Abyss", "Face Nyxarath, the Soul Eater", 1.07, 1.07, 1.07, 1, 1000, 1, "abyss", "bgm_battle.wav", kMini7, 3, "nyxarath", 3000, 1500, 0, 6, true},
    // LEVEL_8 (level_data.py:257)
    {8, "Nethervenom Expanse", "Face Vhoreth'zir, the Nethervenom Wyrm", 1.08, 1.08, 1.08, 1, 1000, 1, "nethervenom", "bgm_battle.wav", kMini8, 3, "vhorethzir", 3000, 1500, 0, 7, true},
    // LEVEL_9 (level_data.py:297)
    {9, "Soulforged Expanse", "Face Naraka, the Lost Soul", 1.09, 1.09, 1.09, 1, 1000, 1, "soulforged", "bgm_battle.wav", kMini9, 3, "naraka", 3000, 1500, 0, 8, true},
    // LEVEL_10 (level_data.py:338)
    {10, "Radiant Expanse", "Face Aureth'zar, the Radiant Dawn", 1.1, 1.1, 1.1, 1, 1000, 1, "radiant", "bgm_battle.wav", kMini10, 3, "aurethzar", 3000, 1500, 0, 9, true},
    // LEVEL_11 (level_data.py:379)
    {11, "Abyssal Depths", "Face Thalakryon, the Abyssal Sovereign", 1.11, 1.11, 1.11, 1, 1000, 1, "abyssal", "bgm_battle.wav", kMini11, 3, "thalakryon", 3000, 1500, 0, 10, true},
    // LEVEL_12 (level_data.py:420)
    {12, "Eldritch Depths", "Face Nazulmor, the Deepborn Herald", 1.12, 1.12, 1.12, 1, 1000, 1, "eldritch", "bgm_battle.wav", kMini12, 3, "nazulmor", 3000, 1500, 0, 11, true},
    // LEVEL_13 (level_data.py:461)
    {13, "Silver Sanctum", "Face Solvarin, the Holy Paladin Warden", 1.13, 1.13, 1.13, 1, 1000, 1, "sanctum", "bgm_battle.wav", kMini13, 3, "solvarin", 3000, 1500, 0, 12, true},
    // LEVEL_14 (level_data.py:502)
    {14, "Eternal Flame", "Face Pyraethis, the Eternal Firebird", 1.14, 1.14, 1.14, 1, 1000, 1, "eternalflame", "bgm_battle.wav", kMini14, 3, "pyraethis", 3000, 1500, 0, 13, true},
    // LEVEL_15 (level_data.py:542)
    {15, "Primordial Grove", "Face Yamako, the Primordial Woodshaper", 1.15, 1.15, 1.15, 1, 1000, 1, "primordial", "bgm_battle.wav", kMini15, 3, "yamako", 3000, 1500, 0, 14, true},
    // LEVEL_16 (level_data.py:582)
    {16, "Celestial Peaks", "Face Seiryukong, the Celestial Simian", 1.16, 1.16, 1.16, 1, 1000, 1, "celestialpeaks", "bgm_battle.wav", kMini16, 3, "seiryukong", 3000, 1500, 0, 15, true},
    // LEVEL_17 (level_data.py:622)
    {17, "Cosmic Expanse", "Face Nyxareth, the Cosmic Sovereign", 1.17, 1.17, 1.17, 1, 1000, 1, "cosmic", "bgm_battle.wav", kMini17, 3, "nyxareth", 3000, 1500, 0, 16, true},
    // LEVEL_18 (level_data.py:662)
    {18, "Royal Citadel", "Face Aurelion, the Golden Sovereign", 1.18, 1.18, 1.18, 1, 1000, 1, "royal", "bgm_battle.wav", kMini18, 3, "aurelion", 3000, 1500, 0, 17, true},
    // LEVEL_19 (level_data.py:702)
    {19, "Violet Court", "Face Vaelindra, the Violet Sovereign", 1.19, 1.19, 1.19, 1, 1000, 1, "violet", "bgm_battle.wav", kMini19, 3, "vaelindra", 3000, 1500, 0, 18, true},
    // LEVEL_20 (level_data.py:742)
    {20, "Crimson Dominion", "Face Morthraxis, the Crimson Sovereign", 1.2, 1.2, 1.2, 1, 1000, 1, "crimson", "bgm_battle.wav", kMini20, 3, "morthraxis", 3000, 1500, 0, 19, true},
    // LEVEL_21 (level_data.py:782)
    {21, "The Hollow Veil", "Face Nexthyrius, the Chained Hollow", 1.21, 1.21, 1.21, 1, 1000, 1, "spectral", "bgm_battle.wav", kMini21, 3, "nexthyrius", 3000, 1500, 0, 20, true},
    // LEVEL_22 (level_data.py:825)
    {22, "The Sundered Peak", "Face Molgravar, the Colossus of the Sundered Peak", 1.22, 1.22, 1.22, 1, 1000, 1, "sundered", "bgm_battle.wav", kMini22, 3, "molgravar", 3000, 1500, 0, 21, true},
    // LEVEL_23 (level_data.py:868)
    {23, "The Empyrean Executioner", "Face Seraphienne, the Empyrean Executioner", 1.23, 1.23, 1.23, 1, 1000, 1, "empyrean", "bgm_battle.wav", kMini23, 3, "seraphienne", 3000, 1500, 0, 22, true},
    // LEVEL_24 (level_data.py:911)
    {24, "The Sunborn Herald", "Face Solareth, the Sunborn Herald", 1.24, 1.24, 1.24, 1, 1000, 1, "solaris", "bgm_battle.wav", kMini24, 3, "solareth", 3000, 1500, 0, 23, true},
    // LEVEL_25 (level_data.py:954)
    {25, "The Deepborn Oracle", "Face Okeanora, the Deepborn Oracle", 1.25, 1.25, 1.25, 1, 1000, 1, "abysstide", "bgm_battle.wav", kMini25, 3, "okeanora", 3000, 1500, 0, 24, true},
    // LEVEL_26 (level_data.py:997)
    {26, "The Crimson Matriarch", "Face Vaelmyrra, the Crimson Matriarch", 1.26, 1.26, 1.26, 1, 1000, 1, "crimsonmatriarch", "bgm_battle.wav", kMini26, 3, "vaelmyrra", 3000, 1500, 0, 25, true},
    // LEVEL_27 (level_data.py:1040)
    {27, "The Astral Sovereign", "Face Zarethyr, the Astral Sovereign", 1.27, 1.27, 1.27, 1, 1000, 1, "astral", "bgm_battle.wav", kMini27, 3, "zarethyr", 3000, 1500, 0, 26, true},
    // LEVEL_28 (level_data.py:1083)
    {28, "The Forsaken Empress", "Face Nyreth'zalvarin, the Forsaken Empress of Shadow-Chains", 1.28, 1.28, 1.28, 1, 1000, 1, "shadowchain", "bgm_battle.wav", kMini28, 3, "nyrethzalv", 3000, 1500, 0, 27, true},
    // LEVEL_29 (level_data.py:1126)
    {29, "The Frost-Veiled Huntress", "Face Nyrellieth, the Frost-Veiled Huntress", 1.29, 1.29, 1.29, 1, 1000, 1, "frostveil", "bgm_battle.wav", kMini29, 3, "nyrellieth", 3000, 1500, 0, 28, true},
    // LEVEL_30 (level_data.py:1169)
    {30, "The Shadow of War", "Face Nyxharr, the Shadow of War", 1.3, 1.3, 1.3, 1, 1000, 1, "warshade", "bgm_battle.wav", kMini30, 3, "nyxharr", 3000, 1500, 0, 29, true},
    // LEVEL_31 (level_data.py:1212)
    {31, "The Outlaw King", "Face Ravokkar, the Outlaw King", 1.31, 1.31, 1.31, 1, 1000, 1, "outlaw", "bgm_battle.wav", kMini31, 3, "ravokkar", 3000, 1500, 0, 30, true},
    // LEVEL_32 (level_data.py:1255)
    {32, "The Hexbound Sovereign", "Face Malzeroth, the Hexbound Sovereign", 1.32, 1.32, 1.32, 1, 1000, 1, "hexbound", "bgm_battle.wav", kMini32, 3, "malzeroth", 3000, 1500, 0, 31, true},
    // LEVEL_33 (level_data.py:1298)
    {33, "The Voidbound Sovereign", "Face Zharakzuul, the Voidbound Sovereign", 1.33, 1.33, 1.33, 1, 1000, 1, "voidbound", "bgm_battle.wav", kMini33, 3, "zharakzuul", 3000, 1500, 0, 32, true},
    // LEVEL_34 (level_data.py:1341)
    {34, "The Earthborn", "Face Grondmauris, the Earthborn", 1.34, 1.34, 1.34, 1, 1000, 1, "earthborn", "bgm_battle.wav", kMini34, 3, "grondmauris", 3000, 1500, 0, 33, true},
    // LEVEL_35 (level_data.py:1384)
    {35, "The Heartbane", "Face Lyssarethys, the Heartbane", 1.35, 1.35, 1.35, 1, 1000, 1, "heartbane", "bgm_battle.wav", kMini35, 3, "lyssarethys", 3000, 1500, 0, 34, true},
    // LEVEL_36 (level_data.py:1427)
    {36, "The Sunfist", "Face Kaerinya, the Sunfist", 1.36, 1.36, 1.36, 1, 1000, 1, "sunfist", "bgm_battle.wav", kMini36, 3, "kaerinya", 3000, 1500, 0, 35, true},
    // LEVEL_37 (level_data.py:1470)
    {37, "The Void Sovereign", "Face Xel'Narath, the Void Sovereign", 1.37, 1.37, 1.37, 1, 1000, 1, "voidwing", "bgm_battle.wav", kMini37, 3, "xelnarath", 3000, 1500, 0, 36, true},
    // LEVEL_38 (level_data.py:1513)
    {38, "The Crimson Devourer", "Face Kyrenzai, the Crimson Devourer", 1.38, 1.38, 1.38, 1, 1000, 1, "crimsondevourer", "bgm_battle.wav", kMini38, 3, "kyrenzai", 3000, 1500, 0, 37, true},
    // LEVEL_39 (level_data.py:1556)
    {39, "The Elemental Weaver", "Face Xael'moran, the Elemental Weaver", 1.39, 1.39, 1.39, 1, 1000, 1, "elementweave", "bgm_battle.wav", kMini39, 3, "xaelmoran", 3000, 1500, 0, 38, true},
    // LEVEL_40 (level_data.py:1599)
    {40, "The Tempest Weaver", "Face Thal'ryndel, the Tempest Weaver", 1.4, 1.4, 1.4, 1, 1000, 1, "tempest", "bgm_battle.wav", kMini40, 3, "thalryndel", 3000, 1500, 0, 39, true},
    // LEVEL_41 (level_data.py:1642)
    {41, "The Sawmill Warlord", "Face Grimkor, the Sawmill Warlord", 1.41, 1.41, 1.41, 1, 1000, 1, "sawmill", "bgm_battle.wav", kMini41, 3, "grimkor", 3000, 1500, 0, 40, true},
    // LEVEL_42 (level_data.py:1685)
    {42, "The Crow-Eyed", "Face Kaineroth, the Crow-Eyed", 1.42, 1.42, 1.42, 1, 1000, 1, "croweye", "bgm_battle.wav", kMini42, 3, "kaineroth", 3000, 1500, 0, 41, true},
    // LEVEL_43 (level_data.py:1728)
    {43, "The Stormherald", "Face Zyvareth, the Stormherald", 1.43, 1.43, 1.43, 1, 1000, 1, "crystalstorm", "bgm_battle.wav", kMini43, 3, "zyvareth", 3000, 1500, 0, 42, true},
    // LEVEL_44 (level_data.py:1771)
    {44, "The Eternal Warlord", "Face Kagetsuka, the Eternal Warlord", 1.44, 1.44, 1.44, 1, 1000, 1, "eternalwarlord", "bgm_battle.wav", kMini44, 3, "kagetsuka", 3000, 1500, 0, 43, true},
    // LEVEL_45 (level_data.py:1814)
    {45, "The Explosive Artist", "Face Deidara, the Explosive Artist", 1.45, 1.45, 1.45, 1, 1000, 1, "explosiveart", "bgm_battle.wav", kMini45, 3, "deidara", 3000, 1500, 0, 44, true},
    // LEVEL_46 (level_data.py:1857)
    {46, "The Sand Shadow", "Face Sunakage, the Sand Shadow", 1.46, 1.46, 1.46, 1, 1000, 1, "sandshadow", "bgm_battle.wav", kMini46, 3, "sunakage", 3000, 1500, 0, 45, true},
    // LEVEL_47 (level_data.py:1900)
    {47, "The Emberweaver", "Face Pyraena, the Emberweaver", 1.47, 1.47, 1.47, 1, 1000, 1, "emberweaver", "bgm_battle.wav", kMini47, 3, "pyraena", 3000, 1500, 0, 46, true},
    // LEVEL_48 (level_data.py:1943)
    {48, "The Skyfury", "Face Cogsworth, the Skyfury", 1.48, 1.48, 1.48, 1, 1000, 1, "skyfury", "bgm_battle.wav", kMini48, 3, "cogsworth", 3000, 1500, 0, 47, true},
    // LEVEL_49 (level_data.py:1986)
    {49, "The Moonreaper", "Face Yomigetsu, the Moonreaper", 1.49, 1.49, 1.49, 1, 1000, 1, "moonreaper", "bgm_battle.wav", kMini49, 3, "yomigetsu", 3000, 1500, 0, 48, true},
    // LEVEL_50 (level_data.py:2029)
    {50, "The Moonfang Prince", "Face Akirakumo, the Moonfang Prince", 1.5, 1.5, 1.5, 1, 1000, 1, "moonfang", "bgm_battle.wav", kMini50, 3, "akirakumo", 3000, 1500, 0, 49, true},
    // LEVEL_51 (level_data.py:2072)
    {51, "The Emberlion Ronin", "Face Kaithros, the Emberlion Ronin", 1.51, 1.51, 1.51, 1, 1000, 1, "emberlion", "bgm_battle.wav", kMini51, 3, "kaithros", 3000, 1500, 0, 50, true},
    // LEVEL_52 (level_data.py:2115)
    {52, "The Lunar Herald", "Face Nyxaris, the Lunar Herald", 1.52, 1.52, 1.52, 1, 1000, 1, "lunarherald", "bgm_battle.wav", kMini52, 3, "nyxaris", 3000, 1500, 0, 51, true},
    // LEVEL_53 (level_data.py:2158)
    {53, "The Moon-Born Sovereign", "Face Tsukiyora, the Moon-Born Sovereign", 1.53, 1.53, 1.53, 1, 1000, 1, "moonborn", "bgm_battle.wav", kMini53, 3, "tsukiyora", 3000, 1500, 0, 52, true},
    // LEVEL_54 (level_data.py:2201)
    {54, "The Substitute Shinigami", "Face Kurosaki Hollowbane, the Substitute Shinigami", 1.54, 1.54, 1.54, 1, 1000, 1, "hollowbane", "bgm_battle.wav", kMini54, 3, "hollowbane", 3000, 1500, 0, 53, true},
};

const int64_t kLevelCount = 54;

} // namespace

Dictionary MysticLevels::build_row(int64_t index) {
    if (index < 0 || index >= kLevelCount) {
        return Dictionary();
    }
    const LevelRow &r = kLevels[index];
    Dictionary d;
    d["level_number"] = (int64_t)r.level_number;
    d["name"] = String(r.name);
    d["description"] = String(r.description);
    d["enemy_hp_mult"] = r.enemy_hp_mult;
    d["enemy_damage_mult"] = r.enemy_damage_mult;
    d["enemy_speed_mult"] = r.enemy_speed_mult;
    d["castle_start_level"] = (int64_t)r.castle_start_level;
    d["starting_gold"] = (int64_t)r.starting_gold;
    d["starting_castle_level"] = (int64_t)r.starting_castle_level;
    d["map_theme"] = String(r.map_theme);
    d["bgm_track"] = String(r.bgm_track);
    {
        Dictionary mini_bosses;
        for (int64_t i = 0; i < r.mini_bosses_count; i++) {
            // Kunci wave = STRING: kunci objek JSON selalu string, jadi
            // levels.json (backend GDScript) dan pemakai Godot memakai "10",
            // bukan int 10 seperti di Python. URUTAN insert dipertahankan
            // (Dictionary Godot ordered) — level 3 memang 25, 10, 17.
            mini_bosses[String(r.mini_bosses[i].wave)] = String(r.mini_bosses[i].boss);
        }
        d["mini_bosses"] = mini_bosses;
    }
    d["true_boss"] = String(r.true_boss);
    d["meta_gold_reward_win"] = (int64_t)r.meta_gold_reward_win;
    d["meta_gold_reward_replay"] = (int64_t)r.meta_gold_reward_replay;
    d["meta_gold_reward_lose"] = (int64_t)r.meta_gold_reward_lose;
    if (r.has_unlock_after_level) {
        d["unlock_after_level"] = (int64_t)r.unlock_after_level;
    } else {
        d["unlock_after_level"] = Variant(); // Python: None
    }
    return d;
}

Array MysticLevels::all_levels() {
    // ALL_LEVELS Python: list 54 dict. Array dibangun segar tiap panggilan;
    // cache katalog dipegang LevelDBLoader.gd (satu kali per backend).
    Array out;
    out.resize(kLevelCount);
    for (int64_t i = 0; i < kLevelCount; i++) {
        out[i] = build_row(i);
    }
    return out;
}

int64_t MysticLevels::row_index(int64_t level_number) {
    for (int64_t i = 0; i < kLevelCount; i++) {
        if (kLevels[i].level_number == level_number) {
            return i;
        }
    }
    return -1;
}

Variant MysticLevels::get_level_config(int64_t level_number) {
    // Python: return None kalau tidak ketemu -> Variant() (NIL).
    int64_t index = row_index(level_number);
    if (index < 0) {
        return Variant();
    }
    return build_row(index);
}

int64_t MysticLevels::get_level_count() {
    return kLevelCount; // len(ALL_LEVELS)
}

bool MysticLevels::py_contains(const Array &haystack, const Variant &needle) {
    // Python `x in list` memakai ==, jadi 1 cocok dengan 1.0. Array.has()
    // Godot memakai hash_compare yang MEMBEDAKAN tipe (variant.cpp:3309) —
    // itu sebabnya save hasil JSON.parse_string (SEMUA angka jadi float,
    // json.cpp:341) membuat `3 in [3.0]` false di GDScript naif dan level
    // tampak terkunci lagi setelah restart.
    for (int64_t i = 0; i < haystack.size(); i++) {
        bool valid = false;
        Variant equal;
        Variant::evaluate(Variant::OP_EQUAL, haystack[i], needle, equal, valid);
        if (valid && bool(equal)) {
            return true;
        }
        // valid == false: pasangan tipe tanpa evaluator == (mis. bool vs
        // int). Python menganggap True == 1; deviasi itu dicatat di
        // docs/LEVELS_GODOTPP.md dan tidak terjadi di produksi (save Godot
        // hanya menyimpan int/float). Tidak pernah error/crash di sini.
    }
    return false;
}

bool MysticLevels::is_level_unlocked(int64_t level_number, const Array &completed_levels) {
    int64_t index = row_index(level_number);
    if (index < 0) {
        return false; // Python: `if not config: return False`
    }
    const LevelRow &r = kLevels[index];
    if (!r.has_unlock_after_level) {
        return true; // Python: required is None -> selalu terbuka
    }
    return py_contains(completed_levels, Variant((int64_t)r.unlock_after_level));
}

Variant MysticLevels::get_next_level(int64_t current_level) {
    int64_t next_level = current_level + 1;
    if (next_level > kLevelCount) {
        return Variant(); // Python: None (sudah level terakhir)
    }
    if (row_index(next_level) < 0) {
        return Variant(); // Python: config level berikutnya tidak ada
    }
    return Variant(next_level);
}

String MysticLevels::catalog_signature() {
    // Ringkasan murah untuk harness: jumlah level + nomor pertama/terakhir +
    // total slot mini boss. Bukan hash kriptografis — tujuannya membuktikan
    // lib yang termuat memuat tabel generasi yang sama dengan data repo.
    int64_t mini_total = 0;
    for (int64_t i = 0; i < kLevelCount; i++) {
        mini_total += kLevels[i].mini_bosses_count;
    }
    String sig = String::num_int64(kLevelCount) + ":";
    if (kLevelCount > 0) {
        sig += String::num_int64(kLevels[0].level_number) + "-"
             + String::num_int64(kLevels[kLevelCount - 1].level_number);
    }
    sig += ":" + String::num_int64(mini_total);
    return sig;
}

void MysticLevels::_bind_methods() {
    ClassDB::bind_static_method("MysticLevels", D_METHOD("all_levels"), &MysticLevels::all_levels);
    ClassDB::bind_static_method("MysticLevels", D_METHOD("get_level_config", "level_number"), &MysticLevels::get_level_config);
    ClassDB::bind_static_method("MysticLevels", D_METHOD("get_level_count"), &MysticLevels::get_level_count);
    ClassDB::bind_static_method("MysticLevels", D_METHOD("is_level_unlocked", "level_number", "completed_levels"), &MysticLevels::is_level_unlocked);
    ClassDB::bind_static_method("MysticLevels", D_METHOD("get_next_level", "current_level"), &MysticLevels::get_next_level);
    ClassDB::bind_static_method("MysticLevels", D_METHOD("build_row", "index"), &MysticLevels::build_row);
    ClassDB::bind_static_method("MysticLevels", D_METHOD("row_index", "level_number"), &MysticLevels::row_index);
    ClassDB::bind_static_method("MysticLevels", D_METHOD("py_contains", "haystack", "needle"), &MysticLevels::py_contains);
    ClassDB::bind_static_method("MysticLevels", D_METHOD("catalog_signature"), &MysticLevels::catalog_signature);
}
