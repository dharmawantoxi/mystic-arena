# ================================
# levels/level_data.py
# Konfigurasi semua level game
#
# CARA TAMBAH LEVEL BARU:
# 1. Copy salah satu LEVEL_X di bawah
# 2. Ubah nomor + boss + parameter
# 3. Append ke ALL_LEVELS
# 4. Done! Auto muncul di menu
# ================================


LEVEL_1 = {
    "level_number": 1,
    "name": "The Fallen Realm",
    "description": "Face Abaddon, the Lord of Avernus",

    # ═══ ENEMY SCALING ═══
    "enemy_hp_mult": 1.0,
    "enemy_damage_mult": 1.0,
    "enemy_speed_mult": 1.0,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    "map_theme": "forest",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    "mini_bosses": {
        1: "gornak",
        2: "morgath",
        3: "drakar",
    },
    "true_boss": "abaddon",

    # ═══ REWARDS ═══
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": None,  # None = default unlock
}


LEVEL_2 = {
    "level_number": 2,
    "name": "Wraith Wastes",
    "description": "Confront the Phantom King",

    "enemy_hp_mult": 1.02,
    "enemy_damage_mult": 1.02,
    "enemy_speed_mult": 1.02,
    "castle_start_level": 1,

    "starting_gold": 1000,
    "starting_castle_level": 1,

    "map_theme": "desert",
    "bgm_track": "bgm_battle.wav",

    "mini_bosses": {
        10: "razak",
        15: "khalros",
        20: "gorath",
    },
    "true_boss": "alchemist",

    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    "unlock_after_level": 1,
}


LEVEL_3 = {
    "level_number": 3,
    "name": "Infernal Depths",
    "description": "Face the Flame Emperor",

    "enemy_hp_mult": 1.03,
    "enemy_damage_mult": 1.03,
    "enemy_speed_mult": 1.03,
    "castle_start_level": 1,

    "starting_gold": 1000,
    "starting_castle_level": 1,

    "map_theme": "ice",
    "bgm_track": "bgm_battle.wav",

    "mini_bosses": {
        25: "varkul",
        10: "xerathis",
        17: "nyzrak",
    },
    "true_boss":  "ancient_apparition",

    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    "unlock_after_level": 2,
}

LEVEL_4 = {
    "level_number": 4,
    "name": "Molten Sanctum",
    "description": "Face Ignis Drachorn, the Molten Sovereign",

    "enemy_hp_mult": 1.04,
    "enemy_damage_mult": 1.04,
    "enemy_speed_mult": 1.04,
    "castle_start_level": 1,

    "starting_gold": 1000,
    "starting_castle_level": 1,

    "map_theme": "volcanic",
    "bgm_track": "bgm_battle.wav",

    # Sementara pakai mini boss existing (level 3 nya)
    "mini_bosses": {
        10: "zharok",      # Wave 10: Zharok (Flaming Skeleton Archer)
        17: "pyrenth",     # Wave 18: Pyrenth (The Devourer)
        25: "vokrahn",     # Wave 25: Vokrahn (The Harbinger of Chaos)
    },
    "true_boss": "ignis_drachorn",

    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    "unlock_after_level": 3,
}

LEVEL_5 = {
    "level_number": 5,
    "name": "The Haunted Veil",
    "description": "Face Krobellus, the Death Prophet",

    # Enemy scaling
    "enemy_hp_mult": 1.05,
    "enemy_damage_mult": 1.05,
    "enemy_speed_mult": 1.05,
    "castle_start_level": 1,

    # Player bonus
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # Map
    "map_theme": "haunted",
    "bgm_track": "bgm_battle.wav",

    # Mini boss sementara dikosongkan
    # Aktifkan setelah 3 mini boss selesai dibuat.
    "mini_bosses": {
    10: "nyxara",
    18: "gravefang",
    25: "vhalzun",
    },

    # True boss
    "true_boss": "krobellus",

    # Reward
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # Unlock
    "unlock_after_level": 4,
}

LEVEL_6 = {
    "level_number": 6,
    "name": "Admiral's Cove",
    "description": "Face Kunkka, the Admiral of the Fleet",

    # Enemy scaling
    "enemy_hp_mult": 1.06,
    "enemy_damage_mult": 1.06,
    "enemy_speed_mult": 1.06,
    "castle_start_level": 1,

    # Player bonus
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # Map
    "map_theme": "ocean",
    "bgm_track": "bgm_battle.wav",

    # Mini boss
    "mini_bosses": {
        10: "gravewake",  # Wave 10: Gravewake (The Tidehunter)
        18: "syrentha",   # Wave 18: Syrentha (The Song of the Seas)
        25: "thalgryn",   # Wave 25: Thalgryn (The Shape of Water)
    },

    # True boss
    "true_boss": "kunkka",

    # Reward
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # Unlock
    "unlock_after_level": 5,
}

LEVEL_7 = {
    "level_number": 7,
    "name": "Shadow Abyss",
    "description": "Face Nyxarath, the Soul Eater",

    # Enemy scaling
    "enemy_hp_mult": 1.07,
    "enemy_damage_mult": 1.07,
    "enemy_speed_mult": 1.07,
    "castle_start_level": 1,

    # Player bonus
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # Map
    "map_theme": "abyss",
    "bgm_track": "bgm_battle.wav",

    # Mini boss
    "mini_bosses": {
        1: "malzareth",  # Wave 10: Malzareth (The Chainbound)
        2: "akashari",   # Wave 18: Akashari (The Painbringer)
        3: "vorenmarr",  # Wave 25: Vorenmarr (The Chaos Binder)
    },

    # True boss
    "true_boss": "nyxarath",

    # Reward
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # Unlock
    "unlock_after_level": 6,
}

LEVEL_8 = {
    "level_number": 8,
    "name": "Nethervenom Expanse",
    "description": "Face Vhoreth'zir, the Nethervenom Wyrm",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->7 (1.0 .. 1.07)
    "enemy_hp_mult": 1.08,
    "enemy_damage_mult": 1.08,
    "enemy_speed_mult": 1.08,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    "map_theme": "nethervenom",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # Mini boss terkuat yang tersedia (thalgryn/vorenmarr sudah
    # dipakai di L6/L7, jadi dipilih tiga teratas berikutnya).
    "mini_bosses": {
        10: "xirthalis",
        18: "vhyssarion",
        25: "vaerith",
    },
    "true_boss": "vhorethzir",

    # ═══ REWARDS ═══
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 7,
}


LEVEL_9 = {
    "level_number": 9,
    "name": "Soulforged Expanse",
    "description": "Face Naraka, the Lost Soul",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->8 (1.0 .. 1.08)
    "enemy_hp_mult": 1.09,
    "enemy_damage_mult": 1.09,
    "enemy_speed_mult": 1.09,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Naraka (The Lost Soul):
    # tanah pucat kelabu + energi jiwa cyan, konsisten dengan
    # pola level sebelumnya (tiap level temanya ikut true boss).
    "map_theme": "soulforged",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 9)
    "mini_bosses": {
        10: "kenshiro",
        18: "khazan",
        25: "wiro",
    },
    "true_boss": "naraka",

    # ═══ REWARDS ═══
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 8,
}

LEVEL_10 = {
    "level_number": 10,
    "name": "Radiant Expanse",
    "description": "Face Aureth'zar, the Radiant Dawn",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->9 (1.0 .. 1.09)
    "enemy_hp_mult": 1.10,
    "enemy_damage_mult": 1.10,
    "enemy_speed_mult": 1.10,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Aureth'zar (Radiant Dawn):
    # padang emas surya + retakan/sungai emas menyala, konsisten
    # dengan pola level sebelumnya.
    "map_theme": "radiant",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 10)
    "mini_bosses": {
        10: "krognarr",
        18: "raz",
        25: "vraskhan",
    },
    "true_boss": "aurethzar",

    # ═══ REWARDS ═══
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 9,
}

LEVEL_11 = {
    "level_number": 11,
    "name": "Abyssal Depths",
    "description": "Face Thalakryon, the Abyssal Sovereign",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->10 (1.0 .. 1.10)
    "enemy_hp_mult": 1.11,
    "enemy_damage_mult": 1.11,
    "enemy_speed_mult": 1.11,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Thalakryon (Abyssal Sovereign):
    # dasar laut dalam biru abisal + sisik teal + busa air menyala,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "abyssal",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 11)
    "mini_bosses": {
        10: "aeralith",
        18: "aurex",
        25: "nyxareva",
    },
    "true_boss": "thalakryon",

    # ═══ REWARDS ═══
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 10,
}

LEVEL_12 = {
    "level_number": 12,
    "name": "Eldritch Depths",
    "description": "Face Nazulmor, the Deepborn Herald",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->11 (1.0 .. 1.11)
    "enemy_hp_mult": 1.12,
    "enemy_damage_mult": 1.12,
    "enemy_speed_mult": 1.12,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Nazulmor (Deepborn Herald):
    # jurang eldritch teal + sayap ungu + energi void menyala,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "eldritch",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 12)
    "mini_bosses": {
        10: "aurelix",
        18: "aurelyssa",
        25: "vargrath",
    },
    "true_boss": "nazulmor",

    # ═══ REWARDS ═══
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 11,
}

LEVEL_13 = {
    "level_number": 13,
    "name": "Silver Sanctum",
    "description": "Face Solvarin, the Holy Paladin Warden",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->12 (1.0 .. 1.12)
    "enemy_hp_mult": 1.13,
    "enemy_damage_mult": 1.13,
    "enemy_speed_mult": 1.13,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Solvarin (Holy Paladin Warden):
    # katedral perak-putih + tabard biru + trim emas menyala,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "sanctum",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 13)
    "mini_bosses": {
        10: "kaeldris",
        18: "pyraklos",
        25: "velmyrth",
    },
    "true_boss": "solvarin",

    # ═══ REWARDS ═══
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 12,
}

LEVEL_14 = {
    "level_number": 14,
    "name": "Eternal Flame",
    "description": "Face Pyraethis, the Eternal Firebird",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->13 (1.0 .. 1.13)
    "enemy_hp_mult": 1.14,
    "enemy_damage_mult": 1.14,
    "enemy_speed_mult": 1.14,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Pyraethis (Eternal Firebird):
    # tanah abu hangus + bara api + semburan api abadi,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "eternalflame",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 14)
    "mini_bosses": {
        10: "azureth",
        18: "luminar",
        25: "solara",
    },
    "true_boss": "pyraethis",

    # ═══ REWARDS ═══
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 13,
}
LEVEL_15 = {
    "level_number": 15,
    "name": "Primordial Grove",
    "description": "Face Yamako, the Primordial Woodshaper",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->14 (1.0 .. 1.14)
    "enemy_hp_mult": 1.15,
    "enemy_damage_mult": 1.15,
    "enemy_speed_mult": 1.15,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Yamako (Primordial Woodshaper):
    # hutan suci hijau purba + kayu kuno + cahaya daun menyala,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "primordial",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 15)
    "mini_bosses": {
        10: "auroth",
        18: "morvein",
        25: "thorvak",
    },
    "true_boss": "yamako",

    # ═══ REWARDS ═══
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 14,
}
LEVEL_16 = {
    "level_number": 16,
    "name": "Celestial Peaks",
    "description": "Face Seiryukong, the Celestial Simian",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->15 (1.0 .. 1.15)
    "enemy_hp_mult": 1.16,
    "enemy_damage_mult": 1.16,
    "enemy_speed_mult": 1.16,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Seiryukong (Celestial Simian):
    # kuil emas di atas awan + batu pegunungan + kabut awan putih,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "celestialpeaks",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 16)
    "mini_bosses": {
        10: "ignirus",
        18: "leoric",
        25: "shirotaka",
    },
    "true_boss": "seiryukong",

    # ═══ REWARDS ═══
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 15,
}
LEVEL_17 = {
    "level_number": 17,
    "name": "Cosmic Expanse",
    "description": "Face Nyxareth, the Cosmic Sovereign",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->16 (1.0 .. 1.16)
    "enemy_hp_mult": 1.17,
    "enemy_damage_mult": 1.17,
    "enemy_speed_mult": 1.17,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Nyxareth (Cosmic Sovereign):
    # hamparan void kosmik + nebula ungu + bintang berkelip,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "cosmic",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 17)
    "mini_bosses": {
        10: "kaelthorn",
        18: "solvanth",
        25: "xyrael",
    },
    "true_boss": "nyxareth",

    # ═══ REWARDS ═══
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 16,
}
LEVEL_18 = {
    "level_number": 18,
    "name": "Royal Citadel",
    "description": "Face Aurelion, the Golden Sovereign",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->17 (1.0 .. 1.17)
    "enemy_hp_mult": 1.18,
    "enemy_damage_mult": 1.18,
    "enemy_speed_mult": 1.18,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Aurelion (Golden Sovereign):
    # istana emas + karpet merah kerajaan + parit biru kerajaan,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "royal",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 18)
    "mini_bosses": {
        10: "cryssalia",
        18: "kaelthar",
        25: "morkhaera",
    },
    "true_boss": "aurelion",

    # ═══ REWARDS ═══
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 17,
}
LEVEL_19 = {
    "level_number": 19,
    "name": "Violet Court",
    "description": "Face Vaelindra, the Violet Sovereign",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->18 (1.0 .. 1.18)
    "enemy_hp_mult": 1.19,
    "enemy_damage_mult": 1.19,
    "enemy_speed_mult": 1.19,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Vaelindra (Violet Sovereign):
    # istana violet kerajaan + lavender + trim emas menyala,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "violet",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 19)
    "mini_bosses": {
        10: "akahime",
        18: "nyxthrael",
        25: "sylvantheros",
    },
    "true_boss": "vaelindra",

    # ═══ REWARDS ═══
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 18,
}
LEVEL_20 = {
    "level_number": 20,
    "name": "Crimson Dominion",
    "description": "Face Morthraxis, the Crimson Sovereign",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->19 (1.0 .. 1.19)
    "enemy_hp_mult": 1.20,
    "enemy_damage_mult": 1.20,
    "enemy_speed_mult": 1.20,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Morthraxis (Crimson Sovereign):
    # kastil vampir merah darah + batu gotik gelap + sungai darah,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "crimson",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 20)
    "mini_bosses": {
        10: "astraelion",
        18: "morvaenthir",
        25: "thornvaegrim",
    },
    "true_boss": "morthraxis",

    # ═══ REWARDS ═══
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 19,
}
LEVEL_21 = {
    "level_number": 21,
    "name": "The Hollow Veil",
    "description": "Face Nexthyrius, the Chained Hollow",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->20 (1.0 .. 1.20)
    "enemy_hp_mult": 1.21,
    "enemy_damage_mult": 1.21,
    "enemy_speed_mult": 1.21,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Nexthyrius (The Chained Hollow):
    # kastil hollow spectral + rantai besi gelap + soul fire hijau,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "spectral",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 21)
    "mini_bosses": {
        10: "kurogari",
        18: "morvekhar",
        25: "vorgath",
    },
    "true_boss": "nexthyrius",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 20,
}


LEVEL_22 = {
    "level_number": 22,
    "name": "The Sundered Peak",
    "description": "Face Molgravar, the Colossus of the Sundered Peak",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->21 (1.0 .. 1.21)
    "enemy_hp_mult": 1.22,
    "enemy_damage_mult": 1.22,
    "enemy_speed_mult": 1.22,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Molgravar (Colossus of the Sundered Peak):
    # puncak gunung terbelah + batu golem + retakan lava menyala,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "sundered",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 22)
    "mini_bosses": {
        10: "grimstalker",
        18: "kryvoxar",
        25: "vargroth",
    },
    "true_boss": "molgravar",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 21,
}


LEVEL_23 = {
    "level_number": 23,
    "name": "The Empyrean Executioner",
    "description": "Face Seraphienne, the Empyrean Executioner",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->22 (1.0 .. 1.22)
    "enemy_hp_mult": 1.23,
    "enemy_damage_mult": 1.23,
    "enemy_speed_mult": 1.23,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Seraphienne (Empyrean Executioner):
    # langit surgawi keemasan + kolom cahaya divine + armor putih,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "empyrean",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 23)
    "mini_bosses": {
        10: "drav",
        18: "lyrienne",
        25: "valthar",
    },
    "true_boss": "seraphienne",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 22,
}


LEVEL_24 = {
    "level_number": 24,
    "name": "The Sunborn Herald",
    "description": "Face Solareth, the Sunborn Herald",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->23 (1.0 .. 1.23)
    "enemy_hp_mult": 1.24,
    "enemy_damage_mult": 1.24,
    "enemy_speed_mult": 1.24,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Solareth (Sunborn Herald):
    # kerajaan matahari terbit + armor emas menyala + jubah merah,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "solaris",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 24)
    "mini_bosses": {
        10: "khalzaredh",
        18: "nyxaroth",
        25: "veshtrax",
    },
    "true_boss": "solareth",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 23,
}


LEVEL_25 = {
    "level_number": 25,
    "name": "The Deepborn Oracle",
    "description": "Face Okeanora, the Deepborn Oracle",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->24 (1.0 .. 1.24)
    "enemy_hp_mult": 1.25,
    "enemy_damage_mult": 1.25,
    "enemy_speed_mult": 1.25,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Okeanora (Deepborn Oracle):
    # laut dalam + tentakel kraken + sihir hijau abyssal,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "abysstide",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 25)
    "mini_bosses": {
        10: "grimjack",
        18: "morvaeth",
        25: "vulkareth",
    },
    "true_boss": "okeanora",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 24,
}


LEVEL_26 = {
    "level_number": 26,
    "name": "The Crimson Matriarch",
    "description": "Face Vaelmyrra, the Crimson Matriarch",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->25 (1.0 .. 1.25)
    "enemy_hp_mult": 1.26,
    "enemy_damage_mult": 1.26,
    "enemy_speed_mult": 1.26,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Vaelmyrra (Crimson Matriarch):
    # tahta darah obsidian + armor crimson + emas kerajaan,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "crimsonmatriarch",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 26)
    "mini_bosses": {
        10: "aelyrion",
        18: "kaervosth",
        25: "morvyssk",
    },
    "true_boss": "vaelmyrra",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 25,
}


LEVEL_27 = {
    "level_number": 27,
    "name": "The Astral Sovereign",
    "description": "Face Zarethyr, the Astral Sovereign",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->26 (1.0 .. 1.26)
    "enemy_hp_mult": 1.27,
    "enemy_damage_mult": 1.27,
    "enemy_speed_mult": 1.27,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Zarethyr (Astral Sovereign):
    # jubah navy kosmik + cahaya biru astral + trim emas,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "astral",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 27)
    "mini_bosses": {
        10: "kyumirra",
        18: "morvakhul",
        25: "nyxariel",
    },
    "true_boss": "zarethyr",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 26,
}


LEVEL_28 = {
    "level_number": 28,
    "name": "The Forsaken Empress",
    "description": "Face Nyreth'zalvarin, the Forsaken Empress of Shadow-Chains",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->27 (1.0 .. 1.27)
    "enemy_hp_mult": 1.28,
    "enemy_damage_mult": 1.28,
    "enemy_speed_mult": 1.28,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Nyreth'zalvarin (Forsaken Empress):
    # jubah ungu gelap + rantai bayangan + sihir magenta,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "shadowchain",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 28)
    "mini_bosses": {
        10: "morthyrax",
        18: "sanguiveth",
        25: "xerakhotep",
    },
    "true_boss": "nyrethzalv",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 27,
}


LEVEL_29 = {
    "level_number": 29,
    "name": "The Frost-Veiled Huntress",
    "description": "Face Nyrellieth, the Frost-Veiled Huntress",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->28 (1.0 .. 1.28)
    "enemy_hp_mult": 1.29,
    "enemy_damage_mult": 1.29,
    "enemy_speed_mult": 1.29,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Nyrellieth (Frost-Veiled Huntress):
    # tundra beku + cape navy + sihir es cyan,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "frostveil",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 29)
    "mini_bosses": {
        10: "ignakhor",
        18: "kazureth",
        25: "sethrakhar",
    },
    "true_boss": "nyrellieth",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 28,
}


LEVEL_30 = {
    "level_number": 30,
    "name": "The Shadow of War",
    "description": "Face Nyxharr, the Shadow of War",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->29 (1.0 .. 1.29)
    "enemy_hp_mult": 1.30,
    "enemy_damage_mult": 1.30,
    "enemy_speed_mult": 1.30,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Nyxharr (Shadow of War):
    # medan perang abadi + armor black-teal + roh kuda cyan,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "warshade",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 30)
    "mini_bosses": {
        10: "kaelvyrn",
        18: "thorvin",
        25: "xaerissa",
    },
    "true_boss": "nyxharr",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 29,
}


LEVEL_31 = {
    "level_number": 31,
    "name": "The Outlaw King",
    "description": "Face Ravokkar, the Outlaw King",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->30 (1.0 .. 1.30)
    "enemy_hp_mult": 1.31,
    "enemy_damage_mult": 1.31,
    "enemy_speed_mult": 1.31,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Ravokkar (Outlaw King):
    # frontier liar + cape merah darah + kulit gelap + debu,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "outlaw",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 31)
    "mini_bosses": {
        10: "celwynn",
        18: "rynvara",
        25: "syrindra",
    },
    "true_boss": "ravokkar",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 30,
}


LEVEL_32 = {
    "level_number": 32,
    "name": "The Hexbound Sovereign",
    "description": "Face Malzeroth, the Hexbound Sovereign",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->31 (1.0 .. 1.31)
    "enemy_hp_mult": 1.32,
    "enemy_damage_mult": 1.32,
    "enemy_speed_mult": 1.32,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Malzeroth (Hexbound Sovereign):
    # altar iblis ungu + jubah merah + sihir hex hijau,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "hexbound",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 32)
    "mini_bosses": {
        10: "ghrakmaal",
        18: "selunara",
        25: "vessyra",
    },
    "true_boss": "malzeroth",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 31,
}


LEVEL_33 = {
    "level_number": 33,
    "name": "The Voidbound Sovereign",
    "description": "Face Zharakzuul, the Voidbound Sovereign",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->32 (1.0 .. 1.32)
    "enemy_hp_mult": 1.33,
    "enemy_damage_mult": 1.33,
    "enemy_speed_mult": 1.33,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Zharakzuul (Voidbound Sovereign):
    # altar kekosongan ungu + jubah gelap + sihir void magenta,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "voidbound",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 33)
    "mini_bosses": {
        10: "rakzhan",
        18: "sirakzan",
        25: "valekris",
    },
    "true_boss": "zharakzuul",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 32,
}


LEVEL_34 = {
    "level_number": 34,
    "name": "The Earthborn",
    "description": "Face Grondmauris, the Earthborn",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->33 (1.0 .. 1.33)
    "enemy_hp_mult": 1.34,
    "enemy_damage_mult": 1.34,
    "enemy_speed_mult": 1.34,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Grondmauris (The Earthborn):
    # gunung golem batu + lumut hijau + mata emas menyala,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "earthborn",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 34)
    "mini_bosses": {
        10: "infrakzaar",
        18: "xarnathul",
        25: "zhyrakaan",
    },
    "true_boss": "grondmauris",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 33,
}


LEVEL_35 = {
    "level_number": 35,
    "name": "The Heartbane",
    "description": "Face Lyssarethys, the Heartbane",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->34 (1.0 .. 1.34)
    "enemy_hp_mult": 1.35,
    "enemy_damage_mult": 1.35,
    "enemy_speed_mult": 1.35,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Lyssarethys (The Heartbane):
    # istana kegelapan ungu + rambut magenta + sihir pink menyala,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "heartbane",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 35)
    "mini_bosses": {
        10: "kaerissa",
        18: "thorgaruk",
        25: "zorathiel",
    },
    "true_boss": "lyssarethys",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 34,
}


LEVEL_36 = {
    "level_number": 36,
    "name": "The Sunfist",
    "description": "Face Kaerinya, the Sunfist",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->35 (1.0 .. 1.35)
    "enemy_hp_mult": 1.36,
    "enemy_damage_mult": 1.36,
    "enemy_speed_mult": 1.36,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Kaerinya (The Sunfist):
    # istana biru tua + tinju api emas menyala,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "sunfist",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 36)
    "mini_bosses": {
        10: "nyxallaria",
        18: "vhaerinth",
        25: "xharokh",
    },
    "true_boss": "kaerinya",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 35,
}


LEVEL_37 = {
    "level_number": 37,
    "name": "The Void Sovereign",
    "description": "Face Xel'Narath, the Void Sovereign",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->36 (1.0 .. 1.36)
    "enemy_hp_mult": 1.37,
    "enemy_damage_mult": 1.37,
    "enemy_speed_mult": 1.37,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Xel'Narath (Void Sovereign):
    # langit kekosongan ungu + sayap void + sihir magenta panas,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "voidwing",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 37)
    "mini_bosses": {
        10: "kazreth",
        18: "varkuthar",
        25: "zhyvrek",
    },
    "true_boss": "xelnarath",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 36,
}


LEVEL_38 = {
    "level_number": 38,
    "name": "The Crimson Devourer",
    "description": "Face Kyrenzai, the Crimson Devourer",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->37 (1.0 .. 1.37)
    "enemy_hp_mult": 1.38,
    "enemy_damage_mult": 1.38,
    "enemy_speed_mult": 1.38,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Kyrenzai (Crimson Devourer):
    # distrik gelap + pakaian hitam + tentakel kagune merah,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "crimsondevourer",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 38)
    "mini_bosses": {
        10: "azkharion",
        18: "thargoroth",
        25: "zahkareth",
    },
    "true_boss": "kyrenzai",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 37,
}


LEVEL_39 = {
    "level_number": 39,
    "name": "The Elemental Weaver",
    "description": "Face Xael'moran, the Elemental Weaver",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->38 (1.0 .. 1.38)
    "enemy_hp_mult": 1.39,
    "enemy_damage_mult": 1.39,
    "enemy_speed_mult": 1.39,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Xael'moran (Elemental Weaver):
    # jubah ungu-emas + sihir elemen (Quas biru, Wex magenta, Exort api),
    # konsisten dengan pola level sebelumnya.
    "map_theme": "elementweave",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 39)
    "mini_bosses": {
        10: "bhorgathul",
        18: "morkhelvis",
        25: "vorthakul",
    },
    "true_boss": "xaelmoran",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 38,
}


LEVEL_40 = {
    "level_number": 40,
    "name": "The Tempest Weaver",
    "description": "Face Thal'ryndel, the Tempest Weaver",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->39 (1.0 .. 1.39)
    "enemy_hp_mult": 1.40,
    "enemy_damage_mult": 1.40,
    "enemy_speed_mult": 1.40,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Thal'ryndel (Tempest Weaver):
    # langit badai elemental biru + jubah biru tua + petir menyala,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "tempest",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 40)
    "mini_bosses": {
        10: "urgharun",
        18: "yhoranth",
        25: "zulkhaven",
    },
    "true_boss": "thalryndel",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 39,
}


LEVEL_41 = {
    "level_number": 41,
    "name": "The Sawmill Warlord",
    "description": "Face Grimkor, the Sawmill Warlord",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->40 (1.0 .. 1.40)
    "enemy_hp_mult": 1.41,
    "enemy_damage_mult": 1.41,
    "enemy_speed_mult": 1.41,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Grimkor (Sawmill Warlord):
    # hutan penggergajian + besi tembaga + api mesin,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "sawmill",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 41)
    "mini_bosses": {
        10: "emberwick",
        18: "grondarthul",
        25: "xareth",
    },
    "true_boss": "grimkor",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 40,
}


LEVEL_42 = {
    "level_number": 42,
    "name": "The Crow-Eyed",
    "description": "Face Kaineroth, the Crow-Eyed",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->41 (1.0 .. 1.41)
    "enemy_hp_mult": 1.42,
    "enemy_damage_mult": 1.42,
    "enemy_speed_mult": 1.42,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Kaineroth (The Crow-Eyed):
    # desa ninja gelap + cloak hitam + awan merah + mata sharingan,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "croweye",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 42)
    "mini_bosses": {
        10: "kaedrin",
        18: "morvaeth2",
        25: "vardrok",
    },
    "true_boss": "kaineroth",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 41,
}


LEVEL_43 = {
    "level_number": 43,
    "name": "The Stormherald",
    "description": "Face Zyvareth, the Stormherald",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->42 (1.0 .. 1.42)
    "enemy_hp_mult": 1.43,
    "enemy_damage_mult": 1.43,
    "enemy_speed_mult": 1.43,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Zyvareth (The Stormherald):
    # langit badai teal + tanduk kristal ungu + petir menyala,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "crystalstorm",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 43)
    "mini_bosses": {
        10: "nixweaver",
        18: "nyxraal",
        25: "xarnthuul",
    },
    "true_boss": "zyvareth",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 42,
}


LEVEL_44 = {
    "level_number": 44,
    "name": "The Eternal Warlord",
    "description": "Face Kagetsuka, the Eternal Warlord",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->43 (1.0 .. 1.43)
    "enemy_hp_mult": 1.44,
    "enemy_damage_mult": 1.44,
    "enemy_speed_mult": 1.44,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Kagetsuka (The Eternal Warlord):
    # medan perang samurai + armor crimson + mata sharingan api,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "eternalwarlord",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 44)
    "mini_bosses": {
        10: "lyrenya",
        18: "vyraeth",
        25: "zorothrax",
    },
    "true_boss": "kagetsuka",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 43,
}


LEVEL_45 = {
    "level_number": 45,
    "name": "The Explosive Artist",
    "description": "Face Deidara, the Explosive Artist",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->44 (1.0 .. 1.44)
    "enemy_hp_mult": 1.45,
    "enemy_damage_mult": 1.45,
    "enemy_speed_mult": 1.45,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Deidara (Explosive Artist):
    # medan ledakan + jubah Akatsuki hitam + awan merah + tanah liat,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "explosiveart",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 45)
    "mini_bosses": {
        10: "akiraze",
        18: "brumhar",
        25: "zorashi",
    },
    "true_boss": "deidara",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 44,
}


LEVEL_46 = {
    "level_number": 46,
    "name": "The Sand Shadow",
    "description": "Face Sunakage, the Sand Shadow",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->45 (1.0 .. 1.45)
    "enemy_hp_mult": 1.46,
    "enemy_damage_mult": 1.46,
    "enemy_speed_mult": 1.46,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Sunakage (The Sand Shadow):
    # gurun pasir merah + jubah marun + rune tattoo merah,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "sandshadow",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 46)
    "mini_bosses": {
        10: "akaroth",
        18: "kassadin",
        25: "shimorakh",
    },
    "true_boss": "sunakage",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 45,
}


LEVEL_47 = {
    "level_number": 47,
    "name": "The Emberweaver",
    "description": "Face Pyraena, the Emberweaver",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->46 (1.0 .. 1.46)
    "enemy_hp_mult": 1.47,
    "enemy_damage_mult": 1.47,
    "enemy_speed_mult": 1.47,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Pyraena (The Emberweaver):
    # istana api + gaun crimson + rambut bara + trim emas,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "emberweaver",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 47)
    "mini_bosses": {
        10: "kaizoku_raijin",
        18: "korokai",
        25: "verdanix",
    },
    "true_boss": "pyraena",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 46,
}


LEVEL_48 = {
    "level_number": 48,
    "name": "The Skyfury",
    "description": "Face Cogsworth, the Skyfury",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->47 (1.0 .. 1.47)
    "enemy_hp_mult": 1.48,
    "enemy_damage_mult": 1.48,
    "enemy_speed_mult": 1.48,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Cogsworth (The Skyfury):
    # langit steampunk + kapal tembaga + pelat besi + api roket,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "skyfury",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 48)
    "mini_bosses": {
        10: "broggmar",
        18: "ursath",
        25: "zhaeris",
    },
    "true_boss": "cogsworth",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 47,
}


LEVEL_49 = {
    "level_number": 49,
    "name": "The Moonreaper",
    "description": "Face Yomigetsu, the Moonreaper",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->48 (1.0 .. 1.48)
    "enemy_hp_mult": 1.49,
    "enemy_damage_mult": 1.49,
    "enemy_speed_mult": 1.49,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Yomigetsu (The Moonreaper):
    # langit bulan crimson + kimono ungu + sabit cahaya bulan,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "moonreaper",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 49)
    "mini_bosses": {
        10: "kairenji",
        18: "karzhul",
        25: "xerakkuth",
    },
    "true_boss": "yomigetsu",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 48,
}


LEVEL_50 = {
    "level_number": 50,
    "name": "The Moonfang Prince",
    "description": "Face Akirakumo, the Moonfang Prince",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->49 (1.0 .. 1.49)
    "enemy_hp_mult": 1.5,
    "enemy_damage_mult": 1.5,
    "enemy_speed_mult": 1.5,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Akirakumo (The Moonfang Prince):
    # kuil bulan perak + kimono putih + sash ungu + aksen emas,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "moonfang",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 50)
    "mini_bosses": {
        10: "kaelthys",
        18: "kaoruken",
        25: "vaelkorr",
    },
    "true_boss": "akirakumo",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 49,
}


LEVEL_51 = {
    "level_number": 51,
    "name": "The Emberlion Ronin",
    "description": "Face Kaithros, the Emberlion Ronin",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->50 (1.0 .. 1.50)
    "enemy_hp_mult": 1.51,
    "enemy_damage_mult": 1.51,
    "enemy_speed_mult": 1.51,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Kaithros (The Emberlion Ronin):
    # api ronin + haori putih + mane api oranye,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "emberlion",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 51)
    "mini_bosses": {
        10: "aurelian",
        18: "morvath",
        25: "pyrhaan",
    },
    "true_boss": "kaithros",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 50,
}


LEVEL_52 = {
    "level_number": 52,
    "name": "The Lunar Herald",
    "description": "Face Nyxaris, the Lunar Herald",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->51 (1.0 .. 1.51)
    "enemy_hp_mult": 1.52,
    "enemy_damage_mult": 1.52,
    "enemy_speed_mult": 1.52,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Nyxaris (The Lunar Herald):
    # malam gelap + mantel ungu + sihir bulan cyan-putih + aksen crimson,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "lunarherald",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 52)
    "mini_bosses": {
        10: "garumenshi",
        18: "thoraz",
        25: "vhaerith",
    },
    "true_boss": "nyxaris",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 51,
}


LEVEL_53 = {
    "level_number": 53,
    "name": "The Moon-Born Sovereign",
    "description": "Face Tsukiyora, the Moon-Born Sovereign",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->52 (1.0 .. 1.52)
    "enemy_hp_mult": 1.53,
    "enemy_damage_mult": 1.53,
    "enemy_speed_mult": 1.53,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Tsukiyora (The Moon-Born Sovereign):
    # kuil bulan putih + kimono putih + trim ungu + mata ketiga merah,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "moonborn",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 53)
    "mini_bosses": {
        10: "dorakai",
        18: "hitokage",
        25: "kazuren",
    },
    "true_boss": "tsukiyora",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 52,
}


LEVEL_54 = {
    "level_number": 54,
    "name": "The Substitute Shinigami",
    "description": "Face Kurosaki Hollowbane, the Substitute Shinigami",

    # ═══ ENEMY SCALING ═══
    # Melanjutkan pola kenaikan level 1->53 (1.0 .. 1.53)
    "enemy_hp_mult": 1.54,
    "enemy_damage_mult": 1.54,
    "enemy_speed_mult": 1.54,
    "castle_start_level": 1,

    # ═══ PLAYER STARTING BONUS ═══
    "starting_gold": 1000,
    "starting_castle_level": 1,

    # ═══ ENVIRONMENT ═══
    # Tema khusus mengikuti true boss Kurosaki Hollowbane (The Substitute Shinigami):
    # langit malam shinigami + robe hitam + rambut oranye + energi Getsuga,
    # konsisten dengan pola level sebelumnya.
    "map_theme": "hollowbane",
    "bgm_track": "bgm_battle.wav",

    # ═══ BOSSES ═══
    # 3 mini boss baru + 1 true boss baru (level 54)
    "mini_bosses": {
        10: "obanai",
        18: "sanguire",
        25: "sasori",
    },
    "true_boss": "hollowbane",

    # ═══ REWARDS ═══
    # Flat untuk semua level: menang 3000G, replay 1500G (sekali), kalah 0G
    "meta_gold_reward_win": 3000,
    "meta_gold_reward_replay": 1500,  # replay (sekali saja)
    "meta_gold_reward_lose": 0,

    # ═══ UNLOCK CONDITION ═══
    "unlock_after_level": 53,
}


# ═══ REGISTRY - Tambahkan level baru di sini ═══
ALL_LEVELS = [
    LEVEL_1,
    LEVEL_2,
    LEVEL_3,
    LEVEL_4,
    LEVEL_5,
    LEVEL_6,
    LEVEL_7,
    LEVEL_8,
    LEVEL_9,
    LEVEL_10,
    LEVEL_11,
    LEVEL_12,
    LEVEL_13,
    LEVEL_14,
    LEVEL_15,
    LEVEL_16,
    LEVEL_17,
    LEVEL_18,
    LEVEL_19,
    LEVEL_20,
    LEVEL_21,
    LEVEL_22,
    LEVEL_23,
    LEVEL_24,
    LEVEL_25,
    LEVEL_26,
    LEVEL_27,
    LEVEL_28,
    LEVEL_29,
    LEVEL_30,
    LEVEL_31,
    LEVEL_32,
    LEVEL_33,
    LEVEL_34,
    LEVEL_35,
    LEVEL_36,
    LEVEL_37,
    LEVEL_38,
    LEVEL_39,
    LEVEL_40,
    LEVEL_41,
    LEVEL_42,
    LEVEL_43,
    LEVEL_44,
    LEVEL_45,
    LEVEL_46,
    LEVEL_47,
    LEVEL_48,
    LEVEL_49,
    LEVEL_50,
    LEVEL_51,
    LEVEL_52,
    LEVEL_53,
    LEVEL_54,
]
# ═══════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════

def get_level_config(level_number):
    """Get config untuk level tertentu"""
    for lvl in ALL_LEVELS:
        if lvl["level_number"] == level_number:
            return lvl
    return None


def get_level_count():
    """Total level yang ada"""
    return len(ALL_LEVELS)


def is_level_unlocked(level_number, completed_levels):
    """
    Cek apakah level tertentu sudah unlock.

    Args:
        level_number: int, level yang mau di-cek
        completed_levels: list of int, level yang sudah dimenangkan
    """
    config = get_level_config(level_number)
    if not config:
        return False

    required = config.get("unlock_after_level")

    # Level 1 selalu unlock
    if required is None:
        return True

    # Level lain: butuh level sebelumnya sudah menang
    return required in completed_levels


def get_next_level(current_level):
    """Return next level number, atau None kalau sudah level terakhir"""
    next_lvl = current_level + 1
    if next_lvl > get_level_count():
        return None
    if get_level_config(next_lvl) is None:
        return None
    return next_lvl