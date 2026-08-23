# ================================
# bosses/boss_data.py
# Semua boss stats & definitions
# Tambah boss baru = tambah entry di sini
# ================================

# ═══════════════════════════════════════════════════════
# MINI BOSSES (muncul di wave tertentu)
# ═══════════════════════════════════════════════════════

MINI_BOSS_WAVES = {
    5: "gornak",
    10: "morgath",
    15: "drakar",
}

MINI_BOSS_TYPES = {
    "gornak": {
        "name": "Gornak",
        "title": "The Warrior Against Magic",
        "boss_class": "mini",
        "hp": 3000,             # tetap tinggi buat mini boss
        "damage": 55,
        "speed": 1.2,           # fast (attack speed 1.6)
        "range": 50,            # MELEE
        "attack_cooldown": 38,  # fast attack
        "radius": 30,
        "gold_reward": 350,
        "color": (170, 80, 210),      # purple
        "color_dark": (90, 40, 130),
        "ability_cooldown": 240,
        "ability_damage": 100,
        "ability_range": 150,
        "entrance_text": "GORNAK THE ANTI-MAGE APPROACHES!",
        "entrance_color": (170, 80, 210),

        # 4 skills (smart AI)
        "skill_q_damage": 180,      # Mana Break
        "skill_q_cooldown": 180,
        "skill_w_damage": 0,        # Blink (teleport, no damage direct)
        "skill_w_cooldown": 240,
        "skill_e_damage": 150,      # Counterspell
        "skill_e_cooldown": 300,
        "skill_r_damage": 380,      # Mana Void ultimate
        "skill_r_cooldown": 540,

        "hero_unlock": {
            "name": "Gornak",
            "title": "The Warrior Against Magic",
            "role": "Boss/Anti-Mage",
            "cost": 500,
            "hp": 800,
            "damage": 75,
            "speed": 1.6,
            "range": 60,
            "attack_cooldown": 38,
            "color": (170, 80, 210),
            "color_dark": (90, 40, 130),
            "skill_name": "Mana Break",
            "skill_desc": "Purple energy burst + Blink",
            "skill_cooldown": 180,
            "skill_damage": 180,
            "skill_range": 100,
            "description": "Anti-Mage warrior ditaklukkan",
        },
    },

    "morgath": {
        "name": "Morgath",
        "title": "The Temporal Protector",
        "boss_class": "mini",
        "hp": 5000,             # tetap tinggi buat mini boss
        "damage": 60,
        "speed": 0.7,           # slower karena ranged
        "range": 180,           # medium ranged
        "attack_cooldown": 42,  # attack speed 1.4
        "radius": 30,
        "gold_reward": 500,
        "color": (140, 100, 220),      # purple magic
        "color_dark": (65, 40, 130),
        "ability_cooldown": 240,
        "ability_damage": 120,
        "ability_range": 200,
        "entrance_text": "MORGATH THE TEMPORAL PROTECTOR EMERGES!",
        "entrance_color": (140, 100, 220),

        # 4 skills (smart AI - ranged focus)
        "skill_q_damage": 200,      # Spark Wraith
        "skill_q_cooldown": 200,
        "skill_w_damage": 150,      # Flux (DOT)
        "skill_w_cooldown": 300,
        "skill_e_damage": 100,      # Magnetic Field
        "skill_e_cooldown": 360,
        "skill_r_damage": 0,        # Tempest Double (no direct damage)
        "skill_r_cooldown": 720,

        # Ranged AI (kite behavior)
        "prefer_distance": 150,
        "min_distance": 100,

        "hero_unlock": {
            "name": "Morgath",
            "title": "The Temporal Protector",
            "role": "Boss/Temporal Mage",
            "cost": 550,
            "hp": 820,
            "damage": 73,
            "speed": 1.4,
            "range": 180,
            "attack_cooldown": 42,
            "color": (140, 100, 220),
            "color_dark": (65, 40, 130),
            "skill_name": "Spark Wraith",
            "skill_desc": "Purple orb + Tempest Double clones",
            "skill_cooldown": 200,
            "skill_damage": 200,
            "skill_range": 200,
            "description": "Temporal mage ditaklukkan",
        },
    },

    "drakar": {
        "name": "Drakar",
        "title": "The Might of the Red Mist",
        "boss_class": "mini",
        "hp": 8000,             # tetap tanky mini boss
        "damage": 80,
        "speed": 1.0,           # medium speed
        "range": 55,            # MELEE
        "attack_cooldown": 46,  # attack speed 1.3
        "radius": 32,
        "gold_reward": 700,
        "color": (220, 60, 60),      # red skin
        "color_dark": (130, 25, 25),
        "ability_cooldown": 240,
        "ability_damage": 150,
        "ability_range": 120,
        "entrance_text": "DRAKAR THE RED MIST APPROACHES!",
        "entrance_color": (220, 60, 60),

        # 4 skills (smart AI - aggressive melee)
        "skill_q_damage": 0,        # Battle Hunger (buff, no damage)
        "skill_q_cooldown": 420,
        "skill_w_damage": 220,      # Counter Helix
        "skill_w_cooldown": 240,
        "skill_e_damage": 150,      # Berserker's Call
        "skill_e_cooldown": 360,
        "skill_r_damage": 450,      # Culling Blade
        "skill_r_cooldown": 480,

        "hero_unlock": {
            "name": "Drakar",
            "title": "The Might of the Red Mist",
            "role": "Boss/Berserker",
            "cost": 600,
            "hp": 1100,
            "damage": 80,
            "speed": 1.3,
            "range": 55,
            "attack_cooldown": 46,
            "color": (220, 60, 60),
            "color_dark": (130, 25, 25),
            "skill_name": "Counter Helix",
            "skill_desc": "Spin attack + Culling Blade",
            "skill_cooldown": 240,
            "skill_damage": 220,
            "skill_range": 100,
            "description": "Red berserker ditaklukkan",
        },
    },

    "razak": {
        "name": "Razak",
        "title": "The Firestarter",
        "boss_class": "mini",
        "hp": 6200,
        "damage": 68,
        "speed": 0.95,
        "range": 55,
        "attack_cooldown": 40,
        "radius": 34,
        "gold_reward": 550,
        "color": (245, 132, 52),
        "color_dark": (138, 48, 18),
        "ability_cooldown": 220,
        "ability_damage": 180,
        "ability_range": 150,
        "entrance_text": "RAZAK THE FIRESTARTER DESCENDS!",
        "entrance_color": (255, 145, 52),
        "skill_q_damage": 160,
        "skill_q_cooldown": 220,
        "skill_w_damage": 220,
        "skill_w_cooldown": 260,
        "skill_e_damage": 180,
        "skill_e_cooldown": 280,
        "skill_r_damage": 340,
        "skill_r_cooldown": 520,
        "prefer_distance": 60,
        "min_distance": 40,
        "hero_unlock": {
            "name": "Razak",
            "title": "The Firestarter",
            "role": "Boss/Fire Rider",
            "cost": 650,
            "hp": 920,
            "damage": 72,
            "speed": 1.4,
            "range": 55,
            "attack_cooldown": 40,
            "color": (245, 132, 52),
            "color_dark": (138, 48, 18),
            "skill_name": "Sticky Napalm",
            "skill_desc": "Napalm burn + Flamebreak + Firestorm",
            "skill_cooldown": 220,
            "skill_damage": 160,
            "skill_range": 150,
            "description": "Goblin rider pembakar langit",
        },
    },

    "khalros": {
        "name": "Khalros",
        "title": "The Beastlord",
        "boss_class": "mini",
        "hp": 7800,
        "damage": 82,
        "speed": 1.0,
        "range": 70,
        "attack_cooldown": 42,
        "radius": 36,
        "gold_reward": 700,
        "color": (190, 122, 68),
        "color_dark": (92, 58, 28),
        "ability_cooldown": 220,
        "ability_damage": 200,
        "ability_range": 200,
        "entrance_text": "KHALROS THE BEASTLORD ANSWERS THE CALL!",
        "entrance_color": (228, 165, 82),
        "skill_q_damage": 210,
        "skill_q_cooldown": 220,
        "skill_w_damage": 160,
        "skill_w_cooldown": 300,
        "skill_e_damage": 220,
        "skill_e_cooldown": 280,
        "skill_r_damage": 380,
        "skill_r_cooldown": 560,
        "hero_unlock": {
            "name": "Khalros",
            "title": "The Beastlord",
            "role": "Boss/Beast Commander",
            "cost": 700,
            "hp": 1050,
            "damage": 84,
            "speed": 1.25,
            "range": 75,
            "attack_cooldown": 42,
            "color": (190, 122, 68),
            "color_dark": (92, 58, 28),
            "skill_name": "Wild Axes",
            "skill_desc": "Axes + boar charge + hawk storm",
            "skill_cooldown": 220,
            "skill_damage": 210,
            "skill_range": 220,
            "description": "Penguasa binatang liar",
        },
    },

    "gorath": {
        "name": "Gorath",
        "title": "The Bloodwarden",
        "boss_class": "mini",
        "hp": 9300,
        "damage": 94,
        "speed": 1.18,
        "range": 58,
        "attack_cooldown": 38,
        "radius": 36,
        "gold_reward": 850,
        "color": (210, 42, 42),
        "color_dark": (102, 12, 12),
        "ability_cooldown": 240,
        "ability_damage": 220,
        "ability_range": 180,
        "entrance_text": "GORATH THE BLOODWARDEN HUNGERS!",
        "entrance_color": (235, 58, 52),
        "skill_q_damage": 0,
        "skill_q_cooldown": 420,
        "skill_w_damage": 210,
        "skill_w_cooldown": 240,
        "skill_e_damage": 190,
        "skill_e_cooldown": 260,
        "skill_r_damage": 420,
        "skill_r_cooldown": 560,
        "hero_unlock": {
            "name": "Gorath",
            "title": "The Bloodwarden",
            "role": "Boss/Blood Hunter",
            "cost": 750,
            "hp": 1120,
            "damage": 96,
            "speed": 1.5,
            "range": 60,
            "attack_cooldown": 38,
            "color": (210, 42, 42),
            "color_dark": (102, 12, 12),
            "skill_name": "Bloodrage",
            "skill_desc": "Blood buff + dash + rupture",
            "skill_cooldown": 420,
            "skill_damage": 0,
            "skill_range": 180,
            "description": "Pejuang darah haus pembantaian",
        },
    },
    "varkul": {
        "name": "Varkul",
        "title": "The Frostfang",
        "boss_class": "mini",
        "hp": 7500,
        "damage": 72,
        "speed": 0.9,
        "range": 100,
        "attack_cooldown": 42,
        "radius": 35,
        "gold_reward": 700,
        "color": (128, 198, 252),
        "color_dark": (35, 92, 175),
        "ability_cooldown": 220,
        "ability_damage": 200,
        "ability_range": 220,
        "entrance_text": "VARKUL THE FROSTFANG RISES!",
        "entrance_color": (168, 232, 255),
        "skill_q_damage": 220,
        "skill_q_cooldown": 240,
        "skill_w_damage": 280,
        "skill_w_cooldown": 300,
        "skill_e_damage": 160,
        "skill_e_cooldown": 360,
        "skill_r_damage": 380,
        "skill_r_cooldown": 540,
        "prefer_distance": 85,
        "min_distance": 60,
        "hero_unlock": {
            "name": "Varkul",
            "title": "The Frostfang",
            "role": "Boss/Frost Sorcerer",
            "cost": 750,
            "hp": 950,
            "damage": 74,
            "speed": 1.3,
            "range": 100,
            "attack_cooldown": 42,
            "color": (128, 198, 252),
            "color_dark": (35, 92, 175),
            "skill_name": "Frost Blast",
            "skill_desc": "Ice arrow + Frostbite + Chain Frost",
            "skill_cooldown": 240,
            "skill_damage": 220,
            "skill_range": 220,
            "description": "Frostbound sorcerer ditaklukkan",
        },
    },

    "xerathis": {
        "name": "Xerathis",
        "title": "The Shardcaller",
        "boss_class": "mini",
        "hp": 8200,
        "damage": 60,
        "speed": 0.85,
        "range": 100,
        "attack_cooldown": 44,
        "radius": 34,
        "gold_reward": 800,
        "color": (148, 195, 250),
        "color_dark": (25, 55, 128),
        "ability_cooldown": 220,
        "ability_damage": 210,
        "ability_range": 240,
        "entrance_text": "XERATHIS THE SHARDCALLER EMERGES!",
        "entrance_color": (188, 232, 255),
        "skill_q_damage": 200,
        "skill_q_cooldown": 260,
        "skill_w_damage": 280,
        "skill_w_cooldown": 240,
        "skill_e_damage": 0,
        "skill_e_cooldown": 420,
        "skill_r_damage": 360,
        "skill_r_cooldown": 580,
        "prefer_distance": 100,
        "min_distance": 70,
        "hero_unlock": {
            "name": "Xerathis",
            "title": "The Shardcaller",
            "role": "Boss/Crystal Sorceress",
            "cost": 800,
            "hp": 900,
            "damage": 62,
            "speed": 1.25,
            "range": 110,
            "attack_cooldown": 44,
            "color": (148, 195, 250),
            "color_dark": (25, 55, 128),
            "skill_name": "Crystal Nova",
            "skill_desc": "Ice crystals + Freeze beam + Freezing Field",
            "skill_cooldown": 260,
            "skill_damage": 200,
            "skill_range": 240,
            "description": "Crystal sorceress ditaklukkan",
        },
    },

    "nyzrak": {
        "name": "Nyzrak",
        "title": "The Hollow Blizzard",
        "boss_class": "mini",
        "hp": 9500,
        "damage": 88,
        "speed": 1.05,
        "range": 95,
        "attack_cooldown": 40,
        "radius": 38,
        "gold_reward": 950,
        "color": (68, 148, 232),
        "color_dark": (18, 48, 108),
        "ability_cooldown": 240,
        "ability_damage": 240,
        "ability_range": 220,
        "entrance_text": "NYZRAK THE HOLLOW BLIZZARD DESCENDS!",
        "entrance_color": (168, 222, 255),
        "skill_q_damage": 240,
        "skill_q_cooldown": 240,
        "skill_w_damage": 200,
        "skill_w_cooldown": 260,
        "skill_e_damage": 220,
        "skill_e_cooldown": 340,
        "skill_r_damage": 400,
        "skill_r_cooldown": 560,
        "prefer_distance": 90,
        "min_distance": 65,
        "hero_unlock": {
            "name": "Nyzrak",
            "title": "The Hollow Blizzard",
            "role": "Boss/Wyvern Rider",
            "cost": 850,
            "hp": 1150,
            "damage": 92,
            "speed": 1.4,
            "range": 100,
            "attack_cooldown": 40,
            "color": (68, 148, 232),
            "color_dark": (18, 48, 108),
            "skill_name": "Arctic Burn",
            "skill_desc": "Ice beam + Splinter Blast + Cold Embrace",
            "skill_cooldown": 240,
            "skill_damage": 240,
            "skill_range": 220,
            "description": "Wyvern rider dari utara ditaklukkan",
        },
    },
    # ===== ZHAROK - The Emberborn (Mini Boss) =====
    "zharok": {
        "name": "Zharok",
        "title": "The Emberborn",
        "boss_class": "mini",
        "hp": 7000,
        "damage": 75,
        "speed": 1.0,
        "range": 180,  # RANGED (archer)
        "attack_cooldown": 40,
        "radius": 34,
        "gold_reward": 600,
        "color": (200, 150, 80),  # bone yellow
        "color_dark": (100, 70, 40),
        "ability_cooldown": 220,
        "ability_damage": 200,
        "ability_range": 250,
        "entrance_text": "ZHAROK THE EMBERBORN RISES FROM ASHES!",
        "entrance_color": (255, 180, 80),

        # 4 skills (Zharok)
        "skill_q_damage": 220,  # Strafe (multiple arrows)
        "skill_q_cooldown": 200,
        "skill_w_damage": 0,  # Skeleton Walk (stealth)
        "skill_w_cooldown": 300,
        "skill_e_damage": 280,  # Death Pact (explosion)
        "skill_e_cooldown": 280,
        "skill_r_damage": 400,  # Burning Army (summon)
        "skill_r_cooldown": 600,

        "prefer_distance": 250,
        "min_distance": 180,

        "hero_unlock": {
            "name": "Zharok",
            "title": "The Emberborn",
            "role": "Boss/Flaming Archer",
            "cost": 650,
            "hp": 880,
            "damage": 78,
            "speed": 1.4,
            "range": 200,
            "attack_cooldown": 40,
            "color": (200, 150, 80),
            "color_dark": (100, 70, 40),
            "skill_name": "Strafe",
            "skill_desc": "Multiple fire arrows + Burning Army",
            "skill_cooldown": 200,
            "skill_damage": 220,
            "skill_range": 250,
            "description": "Flaming skeleton archer ditaklukkan",
        },
    },

    # ===== PYRENTH - The Devourer (Mini Boss) =====
    "pyrenth": {
        "name": "Pyrenth",
        "title": "The Devourer",
        "boss_class": "mini",
        "hp": 9000,
        "damage": 90,
        "speed": 0.85,
        "range": 55,  # MELEE
        "attack_cooldown": 42,
        "radius": 40,
        "gold_reward": 800,
        "color": (220, 60, 30),  # infernal orange-red
        "color_dark": (100, 25, 10),
        "ability_cooldown": 200,
        "ability_damage": 280,
        "ability_range": 200,
        "entrance_text": "PYRENTH THE DEVOURER DESCENDS!",
        "entrance_color": (255, 150, 50),

        # 4 skills (Pyrenth)
        "skill_q_damage": 320,  # DOOM (chain)
        "skill_q_cooldown": 240,
        "skill_w_damage": 200,  # DEVOUR (soul drain + heal)
        "skill_w_cooldown": 360,
        "skill_e_damage": 380,  # SCORCHED EARTH (AOE eruption)
        "skill_e_cooldown": 300,
        "skill_r_damage": 550,  # INFERNAL BLADE (ultimate slash)
        "skill_r_cooldown": 600,

        "hero_unlock": {
            "name": "Pyrenth",
            "title": "The Devourer",
            "role": "Boss/Demon Lord",
            "cost": 750,
            "hp": 1100,
            "damage": 92,
            "speed": 1.3,
            "range": 60,
            "attack_cooldown": 42,
            "color": (220, 60, 30),
            "color_dark": (100, 25, 10),
            "skill_name": "DOOM",
            "skill_desc": "Fiery chain + devour + scorched earth + infernal blade",
            "skill_cooldown": 240,
            "skill_damage": 320,
            "skill_range": 200,
            "description": "Demon lord of primordial rage ditaklukkan",
        },
    },

    # ===== VOKRAHN - The Harbinger of Chaos (Mini Boss) =====
    "vokrahn": {
        "name": "Vokrahn",
        "title": "The Harbinger of Chaos",
        "boss_class": "mini",
        "hp": 11000,
        "damage": 100,
        "speed": 0.9,
        "range": 55,  # MELEE (knight on horse)
        "attack_cooldown": 44,
        "radius": 40,
        "gold_reward": 1000,
        "color": (180, 40, 30),  # chaos red
        "color_dark": (80, 20, 15),
        "ability_cooldown": 200,
        "ability_damage": 300,
        "ability_range": 220,
        "entrance_text": "VOKRAHN THE HARBINGER OF CHAOS RIDES FORTH!",
        "entrance_color": (255, 100, 50),

        # 4 skills (Chaos Knight)
        "skill_q_damage": 350,  # CHAOS BOLT
        "skill_q_cooldown": 220,
        "skill_w_damage": 250,  # REALM OF CHAOS (AOE)
        "skill_w_cooldown": 300,
        "skill_e_damage": 400,  # CHAOS STRIKE
        "skill_e_cooldown": 280,
        "skill_r_damage": 0,  # PHANTASM (summons illusions)
        "skill_r_cooldown": 600,

        "hero_unlock": {
            "name": "Vokrahn",
            "title": "The Harbinger of Chaos",
            "role": "Boss/Chaos Knight",
            "cost": 850,
            "hp": 1300,
            "damage": 102,
            "speed": 1.4,
            "range": 60,
            "attack_cooldown": 44,
            "color": (180, 40, 30),
            "color_dark": (80, 20, 15),
            "skill_name": "Chaos Bolt",
            "skill_desc": "Chaos bolt + realm + strike + phantasm",
            "skill_cooldown": 220,
            "skill_damage": 350,
            "skill_range": 220,
            "description": "Chaos knight ditaklukkan",
        },
    },

    "nyxara": {
        "name": "Nyxara",
        "title": "The Nether Matron",
        "boss_class": "mini",

        "hp": 6200,
        "damage": 68,
        "speed": 0.9,
        "range": 130,
        "attack_cooldown": 42,
        "radius": 34,
        "gold_reward": 650,

        "color": (125, 205, 24),
        "color_dark": (42, 24, 55),

        "ability_cooldown": 220,
        "ability_damage": 180,
        "ability_range": 240,

        "entrance_text": (
            "NYXARA, THE NETHER MATRON, AWAKENS!"
        ),
        "entrance_color": (200, 245, 62),

        "skill_q_damage": 220,
        "skill_q_cooldown": 220,

        "skill_w_damage": 140,
        "skill_w_cooldown": 300,

        "skill_e_damage": 160,
        "skill_e_cooldown": 280,

        "skill_r_damage": 320,
        "skill_r_cooldown": 560,

        "prefer_distance": 220,
        "min_distance": 130,

        "hero_unlock": {
            "name": "Nyxara",
            "title": "The Nether Matron",
            "role": "Boss/Nether Caster",
            "cost": 950,

            "hp": 900,
            "damage": 76,
            "speed": 1.3,
            "range": 100,
            "attack_cooldown": 42,

            "color": (125, 205, 24),
            "color_dark": (42, 24, 55),

            "skill_name": "Nether Blast",
            "skill_desc": (
                "Toxic orb, ward, decrepify and life drain"
            ),
            "skill_cooldown": 220,
            "skill_damage": 220,
            "skill_range": 300,

            "description": (
                "Nether caster dari Haunted Veil"
            ),
        },
    },

    "gravefang": {
        "name": "Gravefang",
        "title": "The Bone Devourer",
        "boss_class": "mini",
        "hp": 7800,
        "damage": 82,
        "speed": 0.78,
        "range": 65,
        "attack_cooldown": 44,
        "radius": 38,
        "gold_reward": 800,
        "color": (145, 220, 55),
        "color_dark": (48, 57, 64),
        "ability_cooldown": 220,
        "ability_damage": 220,
        "ability_range": 220,
        "entrance_text": "GRAVEFANG, THE BONE DEVOURER, SHAKES THE EARTH!",
        "entrance_color": (150, 245, 65),
        "skill_q_damage": 260,
        "skill_q_cooldown": 240,
        "skill_w_damage": 240,
        "skill_w_cooldown": 300,
        "skill_e_damage": 190,
        "skill_e_cooldown": 280,
        "skill_r_damage": 380,
        "skill_r_cooldown": 620,
        "hero_unlock": {
            "name": "Gravefang",
            "title": "The Bone Devourer",
            "role": "Boss/Earth Guardian",
            "cost": 1100,
            "hp": 1100,
            "damage": 88,
            "speed": 1.05,
            "range": 70,
            "attack_cooldown": 44,
            "color": (145, 220, 55),
            "color_dark": (48, 57, 64),
            "skill_name": "Boulder Smash",
            "skill_desc": "Stone slam, rolling boulder and magnetize",
            "skill_cooldown": 240,
            "skill_damage": 260,
            "skill_range": 220,
            "description": "Stone guardian dari Haunted Veil",
        },
    },

    "vhalzun": {
        "name": "Vhalzun",
        "title": "The Reaper of Souls",
        "boss_class": "mini",
        "hp": 9300,
        "damage": 78,
        "speed": 0.82,
        "range": 150,
        "attack_cooldown": 44,
        "radius": 38,
        "gold_reward": 950,
        "color": (35, 185, 92),
        "color_dark": (18, 44, 48),
        "ability_cooldown": 230,
        "ability_damage": 240,
        "ability_range": 260,
        "entrance_text": "VHALZUN, THE REAPER OF SOULS, DESCENDS!",
        "entrance_color": (120, 245, 125),
        "skill_q_damage": 230,
        "skill_q_cooldown": 220,
        "skill_w_damage": 170,
        "skill_w_cooldown": 300,
        "skill_e_damage": 280,
        "skill_e_cooldown": 320,
        "skill_r_damage": 360,
        "skill_r_cooldown": 620,
        "prefer_distance": 360,
        "min_distance": 220,
        "hero_unlock": {
            "name": "Vhalzun",
            "title": "The Reaper of Souls",
            "role": "Boss/Soul Reaper",
            "cost": 1200,
            "hp": 980,
            "damage": 84,
            "speed": 1.2,
            "range": 130,
            "attack_cooldown": 44,
            "color": (35, 185, 92),
            "color_dark": (18, 44, 48),
            "skill_name": "Death Pulse",
            "skill_desc": "Soul pulse, scythe, aura and ghost shroud",
            "skill_cooldown": 220,
            "skill_damage": 230,
            "skill_range": 500,
            "description": "Soul reaper dari Haunted Veil",
        },
    },

    "gravewake": {
        "name": "Gravewake",
        "title": "The Tidehunter",
        "boss_class": "mini",

        "hp": 11600,
        "damage": 112,
        "speed": 0.82,
        "range": 65,            # MELEE (anchor)
        "attack_cooldown": 46,
        "radius": 40,
        "gold_reward": 950,

        "color": (55, 105, 82),         # kraken green
        "color_dark": (12, 28, 25),     # skin darkest

        "ability_cooldown": 220,
        "ability_damage": 240,
        "ability_range": 220,

        "entrance_text": (
            "GRAVEWAKE, THE TIDEHUNTER, RISES FROM THE DEPTHS!"
        ),
        "entrance_color": (120, 225, 230),

        # Q - Anchor Smash (line AOE in front + slow)
        "skill_q_damage": 280,
        "skill_q_cooldown": 240,

        # W - Tidebringer (anchor totems AOE around target)
        "skill_w_damage": 250,
        "skill_w_cooldown": 300,

        # E - Kraken Shell (defensive barrier + heal)
        "skill_e_damage": 0,        # defensive, no direct damage
        "skill_e_cooldown": 360,

        # R - Ravage (massive AOE water eruption)
        "skill_r_damage": 400,
        "skill_r_cooldown": 600,

        "hero_unlock": {
            "name": "Gravewake",
            "title": "The Tidehunter",
            "role": "Boss/Kraken Tidehunter",
            "cost": 1000,

            "hp": 1200,
            "damage": 108,
            "speed": 1.15,
            "range": 70,
            "attack_cooldown": 46,

            "color": (55, 105, 82),
            "color_dark": (12, 28, 25),

            "skill_name": "Anchor Smash",
            "skill_desc": (
                "Anchor slam + tidebringer totems + kraken shell + ravage"
            ),
            "skill_cooldown": 240,
            "skill_damage": 280,
            "skill_range": 220,

            "description": (
                "Kraken tidehunter dari Admiral's Cove"
            ),
        },
    },

    "syrentha": {
        "name": "Syrentha",
        "title": "The Song of the Seas",
        "boss_class": "mini",

        "hp": 13000,
        "damage": 98,
        "speed": 0.85,
        "range": 120,           # spear reach (hybrid melee/ranged)
        "attack_cooldown": 44,
        "radius": 38,
        "gold_reward": 1000,

        "color": (200, 105, 25),        # orange mane
        "color_dark": (18, 40, 40),     # naga skin darkest

        "ability_cooldown": 220,
        "ability_damage": 230,
        "ability_range": 240,

        "entrance_text": (
            "SYRENTHA, THE SONG OF THE SEAS, BEGINS HER LAMENT!"
        ),
        "entrance_color": (240, 165, 55),

        # Q - Riptide (wave AOE forward + slow)
        "skill_q_damage": 250,
        "skill_q_cooldown": 240,

        # W - Enchanting Song (sleep/stun AOE around boss)
        "skill_w_damage": 180,
        "skill_w_cooldown": 300,

        # E - Mirror Image (illusions + buff)
        "skill_e_damage": 0,        # buff skill, no direct damage
        "skill_e_cooldown": 420,

        # R - Song of the Siren (massive spiral stun AOE)
        "skill_r_damage": 420,
        "skill_r_cooldown": 600,

        # Ranged AI (siren keeps distance, casts spells)
        # prefer_distance HARUS <= range agar boss bisa attack!
        "prefer_distance": 110,
        "min_distance": 80,

        "hero_unlock": {
            "name": "Syrentha",
            "title": "The Song of the Seas",
            "role": "Boss/Naga Siren",
            "cost": 1100,

            "hp": 1050,
            "damage": 95,
            "speed": 1.25,
            "range": 130,
            "attack_cooldown": 44,

            "color": (200, 105, 25),
            "color_dark": (18, 40, 40),

            "skill_name": "Riptide",
            "skill_desc": (
                "Wave slash + enchanting song + mirror image + song of siren"
            ),
            "skill_cooldown": 240,
            "skill_damage": 250,
            "skill_range": 240,

            "description": (
                "Naga siren dari Admiral's Cove"
            ),
        },
    },

    "thalgryn": {
        "name": "Thalgryn",
        "title": "The Shape of Water",
        "boss_class": "mini",

        "hp": 14000,
        "damage": 92,
        "speed": 0.9,
        "range": 160,           # RANGED (water bolt)
        "attack_cooldown": 44,
        "radius": 38,
        "gold_reward": 1100,

        "color": (55, 145, 185),        # water mid
        "color_dark": (10, 40, 68),     # water darkest

        "ability_cooldown": 220,
        "ability_damage": 240,
        "ability_range": 260,

        "entrance_text": (
            "THALGRYN, THE SHAPE OF WATER, FLOWS FORTH!"
        ),
        "entrance_color": (175, 235, 235),

        # Q - Waveform (surge forward, damage in path + teleport)
        "skill_q_damage": 320,
        "skill_q_cooldown": 300,

        # W - Adaptive Strike (big ranged water spear, single target)
        "skill_w_damage": 400,
        "skill_w_cooldown": 260,

        # E - Morph (attribute shift, buff + heal)
        "skill_e_damage": 0,        # buff skill, no direct damage
        "skill_e_cooldown": 360,

        # R - Replicate (water clones, AOE + buff)
        "skill_r_damage": 380,
        "skill_r_cooldown": 600,

        # Ranged AI (water elemental keeps distance)
        # prefer_distance HARUS <= range agar boss bisa attack!
        "prefer_distance": 150,
        "min_distance": 100,

        "hero_unlock": {
            "name": "Thalgryn",
            "title": "The Shape of Water",
            "role": "Boss/Water Elemental",
            "cost": 1200,

            "hp": 1000,
            "damage": 90,
            "speed": 1.3,
            "range": 180,
            "attack_cooldown": 44,

            "color": (55, 145, 185),
            "color_dark": (10, 40, 68),

            "skill_name": "Waveform",
            "skill_desc": (
                "Wave surge + adaptive strike + morph + replicate"
            ),
            "skill_cooldown": 300,
            "skill_damage": 320,
            "skill_range": 260,

            "description": (
                "Water elemental dari Admiral's Cove"
            ),
        },
    },

    "malzareth": {
        "name": "Malzareth",
        "title": "The Chainbound",
        "boss_class": "mini",
        "hp": 12000,
        "damage": 100,
        "speed": 0.85,
        "range": 150,
        "attack_cooldown": 44,
        "radius": 40,
        "gold_reward": 1050,
        "color": (190, 30, 75),
        "color_dark": (10, 6, 12),
        "ability_cooldown": 220,
        "ability_damage": 240,
        "ability_range": 240,
        "entrance_text": "MALZARETH, THE CHAINBOUND, EMERGES FROM THE VOID!",
        "entrance_color": (250, 65, 130),
        "skill_q_damage": 300,
        "skill_q_cooldown": 240,
        "skill_w_damage": 280,
        "skill_w_cooldown": 280,
        "skill_e_damage": 220,
        "skill_e_cooldown": 260,
        "skill_r_damage": 400,
        "skill_r_cooldown": 600,
        "prefer_distance": 140,
        "min_distance": 90,
        "hero_unlock": {
            "name": "Malzareth", "title": "The Chainbound",
            "role": "Boss/Shadow Demon", "cost": 1100,
            "hp": 1100, "damage": 100, "speed": 1.25,
            "range": 160, "attack_cooldown": 44,
            "color": (190, 30, 75), "color_dark": (10, 6, 12),
            "skill_name": "Disruption",
            "skill_desc": "Void portal + soul catcher + shadow poison + disillusion",
            "skill_cooldown": 240, "skill_damage": 300, "skill_range": 240,
            "description": "Shadow demon dari Shadow Abyss",
        },
    },

    "akashari": {
        "name": "Akashari",
        "title": "The Painbringer",
        "boss_class": "mini",
        "hp": 13000,
        "damage": 108,
        "speed": 0.88,
        "range": 140,
        "attack_cooldown": 42,
        "radius": 38,
        "gold_reward": 1100,
        "color": (215, 30, 85),
        "color_dark": (8, 4, 10),
        "ability_cooldown": 220,
        "ability_damage": 250,
        "ability_range": 240,
        "entrance_text": "AKASHARI, THE PAINBRINGER, DESCENDS WITH A SCREAM!",
        "entrance_color": (255, 85, 145),
        "skill_q_damage": 320,
        "skill_q_cooldown": 220,
        "skill_w_damage": 250,
        "skill_w_cooldown": 300,
        "skill_e_damage": 300,
        "skill_e_cooldown": 260,
        "skill_r_damage": 450,
        "skill_r_cooldown": 600,
        "prefer_distance": 130,
        "min_distance": 85,
        "hero_unlock": {
            "name": "Akashari", "title": "The Painbringer",
            "role": "Boss/Queen of Pain", "cost": 1200,
            "hp": 1050, "damage": 105, "speed": 1.3,
            "range": 150, "attack_cooldown": 42,
            "color": (215, 30, 85), "color_dark": (8, 4, 10),
            "skill_name": "Shadow Strike",
            "skill_desc": "Shadow strike + blink + scream of pain + sonic wave",
            "skill_cooldown": 220, "skill_damage": 320, "skill_range": 240,
            "description": "Succubus queen dari Shadow Abyss",
        },
    },

    "vorenmarr": {
        "name": "Vorenmarr",
        "title": "The Chaos Binder",
        "boss_class": "mini",
        "hp": 14000,
        "damage": 95,
        "speed": 0.82,
        "range": 150,
        "attack_cooldown": 46,
        "radius": 40,
        "gold_reward": 1150,
        "color": (200, 40, 25),
        "color_dark": (8, 3, 5),
        "ability_cooldown": 220,
        "ability_damage": 260,
        "ability_range": 240,
        "entrance_text": "VORENMARR, THE CHAOS BINDER, SUMMONS HELLFIRE!",
        "entrance_color": (255, 90, 50),
        "skill_q_damage": 260,
        "skill_q_cooldown": 240,
        "skill_w_damage": 0,
        "skill_w_cooldown": 300,
        "skill_e_damage": 350,
        "skill_e_cooldown": 280,
        "skill_r_damage": 420,
        "skill_r_cooldown": 600,
        "prefer_distance": 140,
        "min_distance": 90,
        "hero_unlock": {
            "name": "Vorenmarr", "title": "The Chaos Binder",
            "role": "Boss/Warlock", "cost": 1300,
            "hp": 1200, "damage": 95, "speed": 1.2,
            "range": 160, "attack_cooldown": 46,
            "color": (200, 40, 25), "color_dark": (8, 3, 5),
            "skill_name": "Fatal Bonds",
            "skill_desc": "Fatal bonds + power coggle + upheaval + chaos golem",
            "skill_cooldown": 240, "skill_damage": 260, "skill_range": 240,
            "description": "Chaos warlock dari Shadow Abyss",
        },
    },

    "vaerith": {
        "name": "Vaerith",
        "title": "The Web Matriarch",
        "boss_class": "mini",
        "hp": 14500,
        "damage": 115,
        "speed": 0.86,
        "range": 60,            # MELEE (fang bite)
        "attack_cooldown": 44,  # HARUS 44 - default di renderer
        "radius": 40,
        "gold_reward": 1300,
        "color": (140, 25, 30),
        "color_dark": (8, 4, 12),
        "ability_cooldown": 220,
        "ability_damage": 260,
        "ability_range": 200,
        "entrance_text": "VAERITH, THE WEB MATRIARCH, SPINS YOUR DOOM!",
        "entrance_color": (255, 90, 85),
        "skill_q_damage": 300,
        "skill_q_cooldown": 200,
        "skill_w_damage": 240,
        "skill_w_cooldown": 300,
        "skill_e_damage": 330,
        "skill_e_cooldown": 260,
        "skill_r_damage": 470,
        "skill_r_cooldown": 620,
        "prefer_distance": 55,
        "min_distance": 35,
        "hero_unlock": {
            "name": "Vaerith", "title": "The Web Matriarch",
            "role": "Boss/Broodmother", "cost": 1200,
            "hp": 1150, "damage": 112, "speed": 1.32,
            "range": 65, "attack_cooldown": 44,
            "color": (140, 25, 30), "color_dark": (8, 4, 12),
            "skill_name": "Spawn Spiderlings",
            "skill_desc": "Spiderling + spin web + insatiable hunger + brood",
            "skill_cooldown": 200, "skill_damage": 300, "skill_range": 200,
            "description": "Web Matriarch dari Nethervenom Expanse",
        },
    },

    "xirthalis": {
        "name": "Xir'thalis",
        "title": "The Timeslip Skitterer",
        "boss_class": "mini",
        "hp": 11500,
        "damage": 96,
        "speed": 1.15,          # tercepat - elusive skitterer
        "range": 62,            # MELEE (claw swipe)
        "attack_cooldown": 36,  # HARUS 36 - default di renderer
        "radius": 34,
        "gold_reward": 1250,
        "color": (60, 180, 230),
        "color_dark": (5, 20, 25),
        "ability_cooldown": 200,
        "ability_damage": 240,
        "ability_range": 210,
        "entrance_text": "XIR'THALIS SLIPS THROUGH TIME ITSELF!",
        "entrance_color": (150, 240, 255),
        "skill_q_damage": 0,        # Shukuchi: mobilitas, tanpa damage
        "skill_q_cooldown": 180,
        "skill_w_damage": 260,
        "skill_w_cooldown": 280,
        "skill_e_damage": 340,
        "skill_e_cooldown": 220,
        "skill_r_damage": 0,        # Time Lapse: heal/rewind, tanpa damage
        "skill_r_cooldown": 600,
        "prefer_distance": 58,
        "min_distance": 36,
        "hero_unlock": {
            "name": "Xir'thalis", "title": "The Timeslip Skitterer",
            "role": "Boss/Weaver", "cost": 1200,
            "hp": 950, "damage": 94, "speed": 1.45,
            "range": 68, "attack_cooldown": 36,
            "color": (60, 180, 230), "color_dark": (5, 20, 25),
            "skill_name": "Time Lapse",
            "skill_desc": "Shukuchi + the swarm + geminate attack + time lapse",
            "skill_cooldown": 180, "skill_damage": 340, "skill_range": 210,
            "description": "Timeslip Skitterer dari Nethervenom Expanse",
        },
    },

    "vhyssarion": {
        "name": "Vhyssarion",
        "title": "The Plague Serpent",
        "boss_class": "mini",
        "hp": 12500,
        "damage": 104,
        "speed": 0.90,
        "range": 150,           # RANGED (poison stinger)
        "attack_cooldown": 44,  # HARUS 44 - default di renderer
        "radius": 38,
        "gold_reward": 1280,
        "color": (140, 190, 35),
        "color_dark": (10, 20, 8),
        "ability_cooldown": 210,
        "ability_damage": 250,
        "ability_range": 230,
        "entrance_text": "VHYSSARION, THE PLAGUE SERPENT, POISONS THE AIR!",
        "entrance_color": (200, 245, 80),
        "skill_q_damage": 280,
        "skill_q_cooldown": 240,
        "skill_w_damage": 350,
        "skill_w_cooldown": 200,
        "skill_e_damage": 300,
        "skill_e_cooldown": 280,
        "skill_r_damage": 430,
        "skill_r_cooldown": 640,
        "prefer_distance": 135,
        "min_distance": 90,
        "hero_unlock": {
            "name": "Vhyssarion", "title": "The Plague Serpent",
            "role": "Boss/Venomancer", "cost": 1200,
            "hp": 1000, "damage": 100, "speed": 1.30,
            "range": 160, "attack_cooldown": 44,
            "color": (140, 190, 35), "color_dark": (10, 20, 8),
            "skill_name": "Poison Nova",
            "skill_desc": "Noxious plague + poison sting + gale + poison nova",
            "skill_cooldown": 240, "skill_damage": 350, "skill_range": 230,
            "description": "Plague Serpent dari Nethervenom Expanse",
        },
    },

    "kenshiro": {
        "name": "Kenshiro",
        "title": "The Wandering Blade",
        "boss_class": "mini",
        "hp": 14000,
        "damage": 115,
        "speed": 1.15,
        "range": 55,            # MELEE (floating ronin)
        "attack_cooldown": 40,
        "radius": 32,
        "gold_reward": 1400,
        "color": (90, 140, 220),       # blue-navy kimono
        "color_dark": (20, 32, 60),
        "ability_cooldown": 210,
        "ability_damage": 280,
        "ability_range": 210,
        "entrance_text": "KENSHIRO, THE WANDERING BLADE, DRAWS NEAR!",
        "entrance_color": (120, 170, 240),

        # 4 skills (smart AI - melee burst)
        "skill_q_damage": 300,      # Swift Slash
        "skill_q_cooldown": 200,
        "skill_w_damage": 340,      # Assault (dash strike)
        "skill_w_cooldown": 260,
        "skill_e_damage": 320,      # Gale Slash (AOE)
        "skill_e_cooldown": 300,
        "skill_r_damage": 520,      # Supreme Gale (ultimate)
        "skill_r_cooldown": 640,

        "hero_unlock": {
            "name": "Kenshiro",
            "title": "The Wandering Blade",
            "role": "Boss/Ronin",
            "cost": 1300,
            "hp": 1050,
            "damage": 110,
            "speed": 1.55,
            "range": 65,
            "attack_cooldown": 40,
            "color": (90, 140, 220),
            "color_dark": (20, 32, 60),
            "skill_name": "Swift Slash",
            "skill_desc": "Swift slash + assault dash + gale AOE + supreme gale",
            "skill_cooldown": 200,
            "skill_damage": 300,
            "skill_range": 130,
            "description": "Ronin mengambang dari Level 9",
        },
    },

    "khazan": {
        "name": "Khazan",
        "title": "The Chained Executioner",
        "boss_class": "mini",
        "hp": 14500,
        "damage": 120,
        "speed": 1.0,
        "range": 60,            # MELEE (chained blade)
        "attack_cooldown": 42,
        "radius": 34,
        "gold_reward": 1450,
        "color": (200, 120, 60),       # chained blade orange
        "color_dark": (70, 30, 15),
        "ability_cooldown": 210,
        "ability_damage": 300,
        "ability_range": 200,
        "entrance_text": "KHAZAN, THE CHAINED EXECUTIONER, ARRIVES!",
        "entrance_color": (230, 150, 80),

        # 4 skills (smart AI - melee lockdown)
        "skill_q_damage": 320,      # Chained Blade
        "skill_q_cooldown": 200,
        "skill_w_damage": 360,      # Leap Smash
        "skill_w_cooldown": 280,
        "skill_e_damage": 340,      # Spin Carnage (AOE)
        "skill_e_cooldown": 300,
        "skill_r_damage": 560,      # Vanishing Execution (ultimate)
        "skill_r_cooldown": 660,

        "hero_unlock": {
            "name": "Khazan",
            "title": "The Chained Executioner",
            "role": "Boss/Executioner",
            "cost": 1350,
            "hp": 1100,
            "damage": 115,
            "speed": 1.5,
            "range": 70,
            "attack_cooldown": 42,
            "color": (200, 120, 60),
            "color_dark": (70, 30, 15),
            "skill_name": "Chained Blade",
            "skill_desc": "Chained blade + leap smash + spin + vanishing execution",
            "skill_cooldown": 200,
            "skill_damage": 320,
            "skill_range": 130,
            "description": "Algojo berantai dari Level 9",
        },
    },

    "wiro": {
        "name": "Wiro",
        "title": "The Storm Fist",
        "boss_class": "mini",
        "hp": 14000,
        "damage": 110,
        "speed": 1.3,
        "range": 55,            # MELEE (wind martial artist)
        "attack_cooldown": 38,
        "radius": 30,
        "gold_reward": 1400,
        "color": (110, 220, 150),       # wind green
        "color_dark": (15, 60, 35),
        "ability_cooldown": 200,
        "ability_damage": 280,
        "ability_range": 210,
        "entrance_text": "WIRO, THE STORM FIST, SWEEPS IN!",
        "entrance_color": (130, 235, 165),

        # 4 skills (smart AI - wind combo)
        "skill_q_damage": 300,      # Wind Cut
        "skill_q_cooldown": 190,
        "skill_w_damage": 340,      # Whirl Kick (AOE)
        "skill_w_cooldown": 260,
        "skill_e_damage": 330,      # Gale Dash
        "skill_e_cooldown": 240,
        "skill_r_damage": 540,      # Typhoon (ultimate)
        "skill_r_cooldown": 620,

        "hero_unlock": {
            "name": "Wiro",
            "title": "The Storm Fist",
            "role": "Boss/Martial Artist",
            "cost": 1300,
            "hp": 1050,
            "damage": 108,
            "speed": 1.6,
            "range": 65,
            "attack_cooldown": 38,
            "color": (110, 220, 150),
            "color_dark": (15, 60, 35),
            "skill_name": "Wind Cut",
            "skill_desc": "Wind cut + whirl kick + gale dash + typhoon",
            "skill_cooldown": 190,
            "skill_damage": 300,
            "skill_range": 130,
            "description": "Pendekar angin dari Level 9",
        },
    },

    "krognarr": {
        "name": "Krognarr",
        "title": "The Crystal Colossus",
        "boss_class": "mini",
        "hp": 15500,
        "damage": 125,
        "speed": 0.85,
        "range": 60,            # MELEE (stone golem)
        "attack_cooldown": 44,
        "radius": 38,
        "gold_reward": 1550,
        "color": (120, 220, 110),       # crystal green
        "color_dark": (15, 60, 35),
        "ability_cooldown": 210,
        "ability_damage": 320,
        "ability_range": 220,
        "entrance_text": "KROGNARR, THE CRYSTAL COLOSSUS, AWAKENS!",
        "entrance_color": (140, 235, 130),

        # 4 skills (smart AI - melee slam)
        "skill_q_damage": 340,      # Stone Strike (projectile)
        "skill_q_cooldown": 210,
        "skill_w_damage": 380,      # Seismic Tremor (shockwave)
        "skill_w_cooldown": 280,
        "skill_e_damage": 300,      # Crystal Rampart (wall)
        "skill_e_cooldown": 320,
        "skill_r_damage": 600,      # Earth Eruption (ultimate)
        "skill_r_cooldown": 660,

        "hero_unlock": {
            "name": "Krognarr",
            "title": "The Crystal Colossus",
            "role": "Boss/Stone Golem",
            "cost": 1400,
            "hp": 1150,
            "damage": 118,
            "speed": 1.35,
            "range": 70,
            "attack_cooldown": 44,
            "color": (120, 220, 110),
            "color_dark": (15, 60, 35),
            "skill_name": "Stone Strike",
            "skill_desc": "Stone strike + seismic tremor + crystal rampart + eruption",
            "skill_cooldown": 210,
            "skill_damage": 340,
            "skill_range": 140,
            "description": "Golem kristal dari Level 10",
        },
    },

    "raz": {
        "name": "Raz",
        "title": "The Heat of Despair",
        "boss_class": "mini",
        "hp": 15000,
        "damage": 120,
        "speed": 1.35,
        "range": 55,            # MELEE (fire monk)
        "attack_cooldown": 38,
        "radius": 30,
        "gold_reward": 1500,
        "color": (240, 120, 40),       # fire orange
        "color_dark": (90, 25, 10),
        "ability_cooldown": 200,
        "ability_damage": 300,
        "ability_range": 220,
        "entrance_text": "RAZ, THE HEAT OF DESPAIR, BURNS THE AIR!",
        "entrance_color": (255, 150, 60),

        # 4 skills (smart AI - fire monk)
        "skill_q_damage": 330,      # Overdrive (fire punch)
        "skill_q_cooldown": 190,
        "skill_w_damage": 360,      # Searing Fist (dash punch)
        "skill_w_cooldown": 260,
        "skill_e_damage": 340,      # Energy Surge (AOE)
        "skill_e_cooldown": 280,
        "skill_r_damage": 580,      # Death Gloom (leap meteor)
        "skill_r_cooldown": 640,

        "hero_unlock": {
            "name": "Raz",
            "title": "The Heat of Despair",
            "role": "Boss/Fire Monk",
            "cost": 1400,
            "hp": 1080,
            "damage": 114,
            "speed": 1.65,
            "range": 65,
            "attack_cooldown": 38,
            "color": (240, 120, 40),
            "color_dark": (90, 25, 10),
            "skill_name": "Overdrive",
            "skill_desc": "Overdrive + searing fist + energy surge + death gloom",
            "skill_cooldown": 190,
            "skill_damage": 330,
            "skill_range": 140,
            "description": "Biksu api dari Level 10",
        },
    },

    "vraskhan": {
        "name": "Vraskhan",
        "title": "The Void Assassin",
        "boss_class": "mini",
        "hp": 14800,
        "damage": 130,
        "speed": 1.45,
        "range": 58,            # MELEE (shadow assassin)
        "attack_cooldown": 36,
        "radius": 30,
        "gold_reward": 1520,
        "color": (150, 90, 220),       # void purple
        "color_dark": (35, 15, 70),
        "ability_cooldown": 200,
        "ability_damage": 310,
        "ability_range": 230,
        "entrance_text": "VRASKHAN, THE VOID ASSASSIN, STALKS THE SHADOWS!",
        "entrance_color": (180, 120, 245),

        # 4 skills (smart AI - shadow assassin)
        "skill_q_damage": 340,      # Thorned Assault (dash line)
        "skill_q_cooldown": 190,
        "skill_w_damage": 360,      # Shadow Leap (teleport)
        "skill_w_cooldown": 260,
        "skill_e_damage": 350,      # Death Slash (3 spin slashes)
        "skill_e_cooldown": 280,
        "skill_r_damage": 590,      # Omni Arms (ultimate)
        "skill_r_cooldown": 650,

        "hero_unlock": {
            "name": "Vraskhan",
            "title": "The Void Assassin",
            "role": "Boss/Shadow Assassin",
            "cost": 1400,
            "hp": 1060,
            "damage": 120,
            "speed": 1.7,
            "range": 68,
            "attack_cooldown": 36,
            "color": (150, 90, 220),
            "color_dark": (35, 15, 70),
            "skill_name": "Thorned Assault",
            "skill_desc": "Thorned assault + shadow leap + death slash + omni arms",
            "skill_cooldown": 190,
            "skill_damage": 340,
            "skill_range": 140,
            "description": "Asesin void dari Level 10",
        },
    },

    "aeralith": {
        "name": "Aeralith",
        "title": "The West Gale",
        "boss_class": "mini",
        "hp": 15800,
        "damage": 120,
        "speed": 1.5,
        "range": 150,           # RANGED (wind crescent)
        "attack_cooldown": 44,
        "radius": 30,
        "gold_reward": 1580,
        "color": (130, 220, 250),       # wind light blue
        "color_dark": (15, 60, 95),
        "ability_cooldown": 200,
        "ability_damage": 320,
        "ability_range": 240,
        "entrance_text": "AERALITH, THE WEST GALE, RIDES THE WIND!",
        "entrance_color": (150, 230, 255),

        # 4 skills (smart AI - ranged wind focus)
        "skill_q_damage": 330,      # Tailwind
        "skill_q_cooldown": 190,
        "skill_w_damage": 350,      # Wind Blade
        "skill_w_cooldown": 260,
        "skill_e_damage": 340,      # Vacuum
        "skill_e_cooldown": 280,
        "skill_r_damage": 570,      # Sky Rider
        "skill_r_cooldown": 630,

        # Ranged AI (kite behavior)
        "prefer_distance": 150,
        "min_distance": 90,

        "hero_unlock": {
            "name": "Aeralith",
            "title": "The West Gale",
            "role": "Boss/Wind Ranger",
            "cost": 1450,
            "hp": 1080,
            "damage": 115,
            "speed": 1.75,
            "range": 150,
            "attack_cooldown": 44,
            "color": (130, 220, 250),
            "color_dark": (15, 60, 95),
            "skill_name": "Tailwind",
            "skill_desc": "Tailwind + wind blade + vacuum + sky rider",
            "skill_cooldown": 190,
            "skill_damage": 330,
            "skill_range": 150,
            "description": "Angin barat dari Level 11",
        },
    },

    "aurex": {
        "name": "Aurex",
        "title": "The Omega Knight",
        "boss_class": "mini",
        "hp": 16500,
        "damage": 130,
        "speed": 1.0,
        "range": 65,            # MELEE (omega hammer)
        "attack_cooldown": 42,
        "radius": 36,
        "gold_reward": 1620,
        "color": (220, 200, 120),       # volt gold
        "color_dark": (70, 55, 20),
        "ability_cooldown": 210,
        "ability_damage": 340,
        "ability_range": 220,
        "entrance_text": "AUREX, THE OMEGA KNIGHT, STANDS UNBROKEN!",
        "entrance_color": (235, 215, 140),

        # 4 skills (smart AI - omega knight)
        "skill_q_damage": 340,      # Shield Crash
        "skill_q_cooldown": 200,
        "skill_w_damage": 370,      # Volt Blast (projectile)
        "skill_w_cooldown": 270,
        "skill_e_damage": 320,      # Aegis Barrier
        "skill_e_cooldown": 300,
        "skill_r_damage": 580,      # Destructive Spin
        "skill_r_cooldown": 650,

        "hero_unlock": {
            "name": "Aurex",
            "title": "The Omega Knight",
            "role": "Boss/Omega Knight",
            "cost": 1500,
            "hp": 1180,
            "damage": 122,
            "speed": 1.45,
            "range": 75,
            "attack_cooldown": 42,
            "color": (220, 200, 120),
            "color_dark": (70, 55, 20),
            "skill_name": "Shield Crash",
            "skill_desc": "Shield crash + volt blast + aegis barrier + destructive spin",
            "skill_cooldown": 200,
            "skill_damage": 340,
            "skill_range": 140,
            "description": "Ksatria omega dari Level 11",
        },
    },

    "nyxareva": {
        "name": "Nyxareva",
        "title": "The Fallen Queen",
        "boss_class": "mini",
        "hp": 16000,
        "damage": 128,
        "speed": 1.4,
        "range": 60,            # MELEE (void blades)
        "attack_cooldown": 38,
        "radius": 32,
        "gold_reward": 1600,
        "color": (170, 90, 230),       # void purple
        "color_dark": (40, 15, 75),
        "ability_cooldown": 200,
        "ability_damage": 330,
        "ability_range": 230,
        "entrance_text": "NYXAREVA, THE FALLEN QUEEN, SPREADS HER SHADOW!",
        "entrance_color": (195, 125, 250),

        # 4 skills (smart AI - fallen queen)
        "skill_q_damage": 340,      # Dark Slash
        "skill_q_cooldown": 190,
        "skill_w_damage": 360,      # Mortal Wound
        "skill_w_cooldown": 260,
        "skill_e_damage": 350,      # Whirling Sacrifice
        "skill_e_cooldown": 280,
        "skill_r_damage": 590,      # Avatar of Nyxareva
        "skill_r_cooldown": 640,

        "hero_unlock": {
            "name": "Nyxareva",
            "title": "The Fallen Queen",
            "role": "Boss/Fallen Queen",
            "cost": 1500,
            "hp": 1120,
            "damage": 120,
            "speed": 1.65,
            "range": 70,
            "attack_cooldown": 38,
            "color": (170, 90, 230),
            "color_dark": (40, 15, 75),
            "skill_name": "Dark Slash",
            "skill_desc": "Dark slash + mortal wound + whirling sacrifice + avatar",
            "skill_cooldown": 190,
            "skill_damage": 340,
            "skill_range": 140,
            "description": "Ratu kegelapan dari Level 11",
        },
    },

    "aurelix": {
        "name": "Aurelix",
        "title": "The Time Sovereign",
        "boss_class": "mini",
        "hp": 16800,
        "damage": 125,
        "speed": 1.3,
        "range": 130,           # RANGED (time magic)
        "attack_cooldown": 42,
        "radius": 32,
        "gold_reward": 1680,
        "color": (240, 210, 90),       # time gold
        "color_dark": (80, 60, 15),
        "ability_cooldown": 200,
        "ability_damage": 340,
        "ability_range": 240,
        "entrance_text": "AURELIX, THE TIME SOVEREIGN, FREEZES THE MOMENT!",
        "entrance_color": (250, 220, 110),

        # 4 skills (smart AI - time magic)
        "skill_q_damage": 350,      # Time Bomb
        "skill_q_cooldown": 200,
        "skill_w_damage": 0,        # Will (shield bubble)
        "skill_w_cooldown": 280,
        "skill_e_damage": 360,      # Shockwave (AOE)
        "skill_e_cooldown": 300,
        "skill_r_damage": 600,      # Transcend (ultimate)
        "skill_r_cooldown": 650,

        # Ranged AI (kite behavior)
        "prefer_distance": 150,
        "min_distance": 90,

        "hero_unlock": {
            "name": "Aurelix",
            "title": "The Time Sovereign",
            "role": "Boss/Time Mage",
            "cost": 1550,
            "hp": 1120,
            "damage": 118,
            "speed": 1.6,
            "range": 130,
            "attack_cooldown": 42,
            "color": (240, 210, 90),
            "color_dark": (80, 60, 15),
            "skill_name": "Time Bomb",
            "skill_desc": "Time bomb + will shield + shockwave + transcend",
            "skill_cooldown": 200,
            "skill_damage": 350,
            "skill_range": 150,
            "description": "Penguasa waktu dari Level 12",
        },
    },

    "aurelyssa": {
        "name": "Aurelyssa",
        "title": "The Golden Blade Dancer",
        "boss_class": "mini",
        "hp": 16200,
        "damage": 135,
        "speed": 1.55,
        "range": 62,            # MELEE (golden blade)
        "attack_cooldown": 36,
        "radius": 30,
        "gold_reward": 1650,
        "color": (255, 215, 100),       # blade gold
        "color_dark": (95, 65, 15),
        "ability_cooldown": 200,
        "ability_damage": 330,
        "ability_range": 220,
        "entrance_text": "AURELYSSA, THE GOLDEN BLADE DANCER, TWIRLS INTO BATTLE!",
        "entrance_color": (255, 230, 140),

        # 4 skills (smart AI - blade dancer)
        "skill_q_damage": 340,      # Whirlwind
        "skill_q_cooldown": 190,
        "skill_w_damage": 360,      # Lightning Sweep
        "skill_w_cooldown": 260,
        "skill_e_damage": 350,      # Golden Wings
        "skill_e_cooldown": 280,
        "skill_r_damage": 590,      # Phantom Assault
        "skill_r_cooldown": 640,

        "hero_unlock": {
            "name": "Aurelyssa",
            "title": "The Golden Blade Dancer",
            "role": "Boss/Blade Dancer",
            "cost": 1550,
            "hp": 1100,
            "damage": 124,
            "speed": 1.8,
            "range": 70,
            "attack_cooldown": 36,
            "color": (255, 215, 100),
            "color_dark": (95, 65, 15),
            "skill_name": "Whirlwind",
            "skill_desc": "Whirlwind + lightning sweep + golden wings + phantom assault",
            "skill_cooldown": 190,
            "skill_damage": 340,
            "skill_range": 140,
            "description": "Penari pedang emas dari Level 12",
        },
    },

    "vargrath": {
        "name": "Vargrath",
        "title": "The Demonic Warlord",
        "boss_class": "mini",
        "hp": 17500,
        "damage": 140,
        "speed": 1.1,
        "range": 65,            # MELEE (demon)
        "attack_cooldown": 40,
        "radius": 36,
        "gold_reward": 1720,
        "color": (220, 70, 60),        # demon red
        "color_dark": (70, 10, 12),
        "ability_cooldown": 210,
        "ability_damage": 360,
        "ability_range": 230,
        "entrance_text": "VARGRATH, THE DEMONIC WARLORD, UNLEASHES HELLFIRE!",
        "entrance_color": (245, 100, 80),

        # 4 skills (smart AI - demon warlord)
        "skill_q_damage": 360,      # Bloodthirst
        "skill_q_cooldown": 200,
        "skill_w_damage": 380,      # Charge
        "skill_w_cooldown": 270,
        "skill_e_damage": 370,      # Devil Strike
        "skill_e_cooldown": 290,
        "skill_r_damage": 620,      # Soul Dom
        "skill_r_cooldown": 660,

        "hero_unlock": {
            "name": "Vargrath",
            "title": "The Demonic Warlord",
            "role": "Boss/Demon Warlord",
            "cost": 1600,
            "hp": 1200,
            "damage": 130,
            "speed": 1.5,
            "range": 75,
            "attack_cooldown": 40,
            "color": (220, 70, 60),
            "color_dark": (70, 10, 12),
            "skill_name": "Bloodthirst",
            "skill_desc": "Bloodthirst + charge + devil strike + soul dom",
            "skill_cooldown": 200,
            "skill_damage": 360,
            "skill_range": 140,
            "description": "Panglima iblis dari Level 12",
        },
    },

    "kaeldris": {
        "name": "Kaeldris",
        "title": "The Warrior Commander",
        "boss_class": "mini",
        "hp": 17800,
        "damage": 140,
        "speed": 1.2,
        "range": 65,            # MELEE (warrior commander)
        "attack_cooldown": 40,
        "radius": 34,
        "gold_reward": 1780,
        "color": (150, 120, 200),       # commander purple
        "color_dark": (45, 30, 75),
        "ability_cooldown": 210,
        "ability_damage": 360,
        "ability_range": 230,
        "entrance_text": "KAELDRIS, THE WARRIOR COMMANDER, MARSHALS THE ONSLAUGHT!",
        "entrance_color": (175, 145, 220),

        # 4 skills (smart AI - warrior commander)
        "skill_q_damage": 360,      # Overwhelming
        "skill_q_cooldown": 200,
        "skill_w_damage": 380,      # Press (dash)
        "skill_w_cooldown": 270,
        "skill_e_damage": 370,      # Moment (AOE)
        "skill_e_cooldown": 290,
        "skill_r_damage": 620,      # Duel (ultimate)
        "skill_r_cooldown": 650,

        "hero_unlock": {
            "name": "Kaeldris",
            "title": "The Warrior Commander",
            "role": "Boss/Commander",
            "cost": 1650,
            "hp": 1200,
            "damage": 130,
            "speed": 1.55,
            "range": 75,
            "attack_cooldown": 40,
            "color": (150, 120, 200),
            "color_dark": (45, 30, 75),
            "skill_name": "Overwhelming",
            "skill_desc": "Overwhelming + press + moment + duel",
            "skill_cooldown": 200,
            "skill_damage": 360,
            "skill_range": 140,
            "description": "Komandan perang dari Level 13",
        },
    },

    "pyraklos": {
        "name": "Pyraklos",
        "title": "The Spartan War Champion",
        "boss_class": "mini",
        "hp": 18200,
        "damage": 145,
        "speed": 1.15,
        "range": 65,            # MELEE (spartan spear)
        "attack_cooldown": 42,
        "radius": 36,
        "gold_reward": 1820,
        "color": (220, 130, 60),       # spartan bronze
        "color_dark": (75, 35, 12),
        "ability_cooldown": 210,
        "ability_damage": 370,
        "ability_range": 220,
        "entrance_text": "PYRAKLOS, THE SPARTAN WAR CHAMPION, STANDS IN THE BREACH!",
        "entrance_color": (240, 160, 90),

        # 4 skills (smart AI - spartan)
        "skill_q_damage": 370,      # Spear of Mars
        "skill_q_cooldown": 200,
        "skill_w_damage": 390,      # Rebuke
        "skill_w_cooldown": 280,
        "skill_e_damage": 0,        # Bulwark (defensive)
        "skill_e_cooldown": 300,
        "skill_r_damage": 640,      # Arena (ultimate)
        "skill_r_cooldown": 660,

        "hero_unlock": {
            "name": "Pyraklos",
            "title": "The Spartan War Champion",
            "role": "Boss/Spartan",
            "cost": 1700,
            "hp": 1250,
            "damage": 135,
            "speed": 1.5,
            "range": 75,
            "attack_cooldown": 42,
            "color": (220, 130, 60),
            "color_dark": (75, 35, 12),
            "skill_name": "Spear of Mars",
            "skill_desc": "Spear of mars + rebuke + bulwark + arena",
            "skill_cooldown": 200,
            "skill_damage": 370,
            "skill_range": 140,
            "description": "Juara spartan dari Level 13",
        },
    },

    "velmyrth": {
        "name": "Velmyrth",
        "title": "The Phantom Assassin",
        "boss_class": "mini",
        "hp": 17200,
        "damage": 150,
        "speed": 1.6,
        "range": 60,            # MELEE (phantom blades)
        "attack_cooldown": 34,
        "radius": 30,
        "gold_reward": 1750,
        "color": (120, 200, 190),       # phantom teal
        "color_dark": (15, 60, 65),
        "ability_cooldown": 200,
        "ability_damage": 350,
        "ability_range": 230,
        "entrance_text": "VELMYRTH, THE PHANTOM ASSASSIN, FADES INTO THE SHADOWS!",
        "entrance_color": (145, 225, 215),

        # 4 skills (smart AI - phantom assassin)
        "skill_q_damage": 360,      # Stifling Dagger
        "skill_q_cooldown": 190,
        "skill_w_damage": 380,      # Phantom Strike (teleport)
        "skill_w_cooldown": 260,
        "skill_e_damage": 370,      # Blur (AOE)
        "skill_e_cooldown": 280,
        "skill_r_damage": 630,      # Coup de Grace (ultimate)
        "skill_r_cooldown": 640,

        "hero_unlock": {
            "name": "Velmyrth",
            "title": "The Phantom Assassin",
            "role": "Boss/Assassin",
            "cost": 1700,
            "hp": 1140,
            "damage": 138,
            "speed": 1.85,
            "range": 70,
            "attack_cooldown": 34,
            "color": (120, 200, 190),
            "color_dark": (15, 60, 65),
            "skill_name": "Stifling Dagger",
            "skill_desc": "Stifling dagger + phantom strike + blur + coup de grace",
            "skill_cooldown": 190,
            "skill_damage": 360,
            "skill_range": 140,
            "description": "Asesin hantu dari Level 13",
        },
    },
    "azureth": {
        "name": "Azureth",
        "title": "The Arcane Sky-Scribe",
        "boss_class": "mini",
        "hp": 18000,
        "damage": 150,
        "speed": 1.1,
        "range": 260,           # RANGED (arcane mage)
        "attack_cooldown": 46,
        "radius": 32,
        "gold_reward": 1800,
        "color": (75, 120, 210),       # arcane blue robe
        "color_dark": (15, 30, 75),
        "ability_cooldown": 210,
        "ability_damage": 380,
        "ability_range": 270,
        "entrance_text": "AZURETH, THE ARCANE SKY-SCRIBE, INSCRIBES THE SKIES!",
        "entrance_color": (130, 180, 250),

        # 4 skills (smart AI - arcane mage)
        "skill_q_damage": 380,      # Arcane Bolt
        "skill_q_cooldown": 200,
        "skill_w_damage": 400,      # Concussive Blast (AOE)
        "skill_w_cooldown": 270,
        "skill_e_damage": 370,      # Ancient Seal (AOE root)
        "skill_e_cooldown": 290,
        "skill_r_damage": 680,      # Mystic Flare (ultimate)
        "skill_r_cooldown": 650,

        # Ranged AI (kite behavior)
        "prefer_distance": 240,
        "min_distance": 120,

        "hero_unlock": {
            "name": "Azureth",
            "title": "The Arcane Sky-Scribe",
            "role": "Boss/Arcane Mage",
            "cost": 1700,
            "hp": 1250,
            "damage": 135,
            "speed": 1.5,
            "range": 240,
            "attack_cooldown": 46,
            "color": (75, 120, 210),
            "color_dark": (15, 30, 75),
            "skill_name": "Arcane Bolt",
            "skill_desc": "Arcane bolt + concussive blast + ancient seal + mystic flare",
            "skill_cooldown": 200,
            "skill_damage": 380,
            "skill_range": 150,
            "description": "Mage arcane dari Level 14",
        },
    },

    "luminar": {
        "name": "Luminar",
        "title": "The Eternal Custodian",
        "boss_class": "mini",
        "hp": 18500,
        "damage": 155,
        "speed": 1.05,
        "range": 270,           # RANGED (light wizard, mounted)
        "attack_cooldown": 47,
        "radius": 36,
        "gold_reward": 1850,
        "color": (160, 185, 235),       # blue-white robe
        "color_dark": (40, 55, 100),
        "ability_cooldown": 215,
        "ability_damage": 390,
        "ability_range": 280,
        "entrance_text": "LUMINAR, THE ETERNAL CUSTODIAN, RIDES FORTH IN LIGHT!",
        "entrance_color": (215, 230, 255),

        # 4 skills (smart AI - light custodian)
        "skill_q_damage": 390,      # Illuminate
        "skill_q_cooldown": 205,
        "skill_w_damage": 410,      # Blinding Light (AOE)
        "skill_w_cooldown": 275,
        "skill_e_damage": 380,      # Wisp (AOE)
        "skill_e_cooldown": 295,
        "skill_r_damage": 700,      # Spirit Form (ultimate)
        "skill_r_cooldown": 660,

        # Ranged AI (kite behavior)
        "prefer_distance": 250,
        "min_distance": 130,

        "hero_unlock": {
            "name": "Luminar",
            "title": "The Eternal Custodian",
            "role": "Boss/Light Custodian",
            "cost": 1750,
            "hp": 1300,
            "damage": 140,
            "speed": 1.45,
            "range": 250,
            "attack_cooldown": 47,
            "color": (160, 185, 235),
            "color_dark": (40, 55, 100),
            "skill_name": "Illuminate",
            "skill_desc": "Illuminate + blinding light + wisp + spirit form",
            "skill_cooldown": 205,
            "skill_damage": 390,
            "skill_range": 150,
            "description": "Penjaga cahaya abadi dari Level 14",
        },
    },

    "solara": {
        "name": "Solara",
        "title": "The Dawnforged Sentinel",
        "boss_class": "mini",
        "hp": 19000,
        "damage": 160,
        "speed": 1.15,
        "range": 70,            # MELEE (dawnforged warhammer)
        "attack_cooldown": 42,
        "radius": 34,
        "gold_reward": 1900,
        "color": (235, 185, 80),       # dawnforged gold armor
        "color_dark": (85, 50, 15),
        "ability_cooldown": 220,
        "ability_damage": 400,
        "ability_range": 240,
        "entrance_text": "SOLARA, THE DAWNFORGED SENTINEL, STANDS AGAINST THE NIGHT!",
        "entrance_color": (255, 220, 130),

        # 4 skills (smart AI - dawnforged sentinel)
        "skill_q_damage": 400,      # Starbreaker
        "skill_q_cooldown": 210,
        "skill_w_damage": 420,      # Celestial Hammer (AOE)
        "skill_w_cooldown": 270,
        "skill_e_damage": 390,      # Luminosity (AOE heal)
        "skill_e_cooldown": 300,
        "skill_r_damage": 720,      # Solar Guardian (ultimate)
        "skill_r_cooldown": 680,

        "hero_unlock": {
            "name": "Solara",
            "title": "The Dawnforged Sentinel",
            "role": "Boss/Dawnforged Sentinel",
            "cost": 1800,
            "hp": 1350,
            "damage": 148,
            "speed": 1.5,
            "range": 80,
            "attack_cooldown": 42,
            "color": (235, 185, 80),
            "color_dark": (85, 50, 15),
            "skill_name": "Starbreaker",
            "skill_desc": "Starbreaker + celestial hammer + luminosity + solar guardian",
            "skill_cooldown": 210,
            "skill_damage": 400,
            "skill_range": 140,
            "description": "Ksatria fajar dari Level 14",
        },
    },
    "auroth": {
        "name": "Auroth",
        "title": "The Celestial Bastion",
        "boss_class": "mini",
        "hp": 19500,
        "damage": 165,
        "speed": 0.9,
        "range": 70,            # MELEE (bastion titan)
        "attack_cooldown": 46,
        "radius": 38,
        "gold_reward": 1950,
        "color": (230, 185, 65),       # celestial gold armor
        "color_dark": (75, 50, 15),
        "ability_cooldown": 220,
        "ability_damage": 410,
        "ability_range": 240,
        "entrance_text": "AUROTH, THE CELESTIAL BASTION, HOLDS THE LINE!",
        "entrance_color": (255, 220, 120),

        # 4 skills (smart AI - celestial bastion)
        "skill_q_damage": 410,      # Ionic Edge
        "skill_q_cooldown": 215,
        "skill_w_damage": 420,      # Ward (defensive AOE)
        "skill_w_cooldown": 280,
        "skill_e_damage": 400,      # Consecration (AOE)
        "skill_e_cooldown": 310,
        "skill_r_damage": 740,      # Guardian (ultimate)
        "skill_r_cooldown": 700,

        "hero_unlock": {
            "name": "Auroth",
            "title": "The Celestial Bastion",
            "role": "Boss/Bastion Titan",
            "cost": 1850,
            "hp": 1400,
            "damage": 152,
            "speed": 1.35,
            "range": 85,
            "attack_cooldown": 46,
            "color": (230, 185, 65),
            "color_dark": (75, 50, 15),
            "skill_name": "Ionic Edge",
            "skill_desc": "Ionic edge + ward + consecration + guardian",
            "skill_cooldown": 215,
            "skill_damage": 410,
            "skill_range": 140,
            "description": "Titan bastion langit dari Level 15",
        },
    },

    "morvein": {
        "name": "Morvein",
        "title": "The Phantom Lancer",
        "boss_class": "mini",
        "hp": 20000,
        "damage": 170,
        "speed": 1.2,
        "range": 75,            # MELEE (phantom lance)
        "attack_cooldown": 42,
        "radius": 34,
        "gold_reward": 2000,
        "color": (95, 110, 155),       # phantom steel blue
        "color_dark": (18, 25, 45),
        "ability_cooldown": 215,
        "ability_damage": 420,
        "ability_range": 250,
        "entrance_text": "MORVEIN, THE PHANTOM LANCER, STRIKES FROM THE MIST!",
        "entrance_color": (160, 175, 220),

        # 4 skills (smart AI - phantom lancer)
        "skill_q_damage": 420,      # Puncture
        "skill_q_cooldown": 215,
        "skill_w_damage": 440,      # Violent Strike (AOE)
        "skill_w_cooldown": 275,
        "skill_e_damage": 410,      # Spectral Charge (dash AOE)
        "skill_e_cooldown": 300,
        "skill_r_damage": 760,      # Phantom Form (ultimate)
        "skill_r_cooldown": 690,

        "hero_unlock": {
            "name": "Morvein",
            "title": "The Phantom Lancer",
            "role": "Boss/Phantom Lancer",
            "cost": 1900,
            "hp": 1450,
            "damage": 158,
            "speed": 1.55,
            "range": 85,
            "attack_cooldown": 42,
            "color": (95, 110, 155),
            "color_dark": (18, 25, 45),
            "skill_name": "Puncture",
            "skill_desc": "Puncture + violent strike + spectral charge + phantom form",
            "skill_cooldown": 215,
            "skill_damage": 420,
            "skill_range": 140,
            "description": "Ksatria tombak hantu dari Level 15",
        },
    },

    "thorvak": {
        "name": "Thorvak",
        "title": "The Ancient Grovewarden",
        "boss_class": "mini",
        "hp": 20500,
        "damage": 160,
        "speed": 0.95,
        "range": 80,            # MELEE (grovewarden treant)
        "attack_cooldown": 44,
        "radius": 40,
        "gold_reward": 2050,
        "color": (130, 220, 90),       # treant nature green
        "color_dark": (20, 70, 25),
        "ability_cooldown": 225,
        "ability_damage": 420,
        "ability_range": 250,
        "entrance_text": "THORVAK, THE ANCIENT GROVEWARDEN, AWAKENS!",
        "entrance_color": (130, 220, 90),

        # 4 skills (smart AI - ancient grovewarden)
        "skill_q_damage": 420,      # Seed
        "skill_q_cooldown": 220,
        "skill_w_damage": 440,      # Nature's Wrath (AOE)
        "skill_w_cooldown": 280,
        "skill_e_damage": 410,      # Vengeance (AOE)
        "skill_e_cooldown": 310,
        "skill_r_damage": 760,      # Dryad (ultimate)
        "skill_r_cooldown": 680,

        "hero_unlock": {
            "name": "Thorvak",
            "title": "The Ancient Grovewarden",
            "role": "Boss/Grovewarden Treant",
            "cost": 1950,
            "hp": 1500,
            "damage": 150,
            "speed": 1.35,
            "range": 90,
            "attack_cooldown": 44,
            "color": (130, 220, 90),
            "color_dark": (20, 70, 25),
            "skill_name": "Seed",
            "skill_desc": "Seed + nature's wrath + vengeance + dryad",
            "skill_cooldown": 220,
            "skill_damage": 420,
            "skill_range": 140,
            "description": "Treant penjaga hutan purba dari Level 15",
        },
    },
    "ignirus": {
        "name": "Ignirus",
        "title": "The Infernal Pyromancer",
        "boss_class": "mini",
        "hp": 21000,
        "damage": 175,
        "speed": 1.1,
        "range": 280,           # RANGED (infernal mage)
        "attack_cooldown": 46,
        "radius": 32,
        "gold_reward": 2100,
        "color": (215, 75, 60),        # infernal robe red
        "color_dark": (75, 15, 20),
        "ability_cooldown": 225,
        "ability_damage": 440,
        "ability_range": 280,
        "entrance_text": "IGNIRUS, THE INFERNAL PYROMANCER, SCORCHES THE SKIES!",
        "entrance_color": (245, 130, 90),

        # 4 skills (smart AI - infernal pyromancer)
        "skill_q_damage": 440,      # Searing Torrent
        "skill_q_cooldown": 225,
        "skill_w_damage": 460,      # Flame Shot (AOE)
        "skill_w_cooldown": 285,
        "skill_e_damage": 430,      # Burst Fireball (AOE)
        "skill_e_cooldown": 315,
        "skill_r_damage": 800,      # Vengeance (ultimate)
        "skill_r_cooldown": 690,

        # Ranged AI (kite behavior)
        "prefer_distance": 250,
        "min_distance": 130,

        "hero_unlock": {
            "name": "Ignirus",
            "title": "The Infernal Pyromancer",
            "role": "Boss/Infernal Mage",
            "cost": 2000,
            "hp": 1550,
            "damage": 162,
            "speed": 1.5,
            "range": 260,
            "attack_cooldown": 46,
            "color": (215, 75, 60),
            "color_dark": (75, 15, 20),
            "skill_name": "Searing Torrent",
            "skill_desc": "Searing torrent + flame shot + burst fireball + vengeance",
            "skill_cooldown": 225,
            "skill_damage": 440,
            "skill_range": 150,
            "description": "Mage api neraka dari Level 16",
        },
    },

    "leoric": {
        "name": "Leoric",
        "title": "The Lionheart Guardian",
        "boss_class": "mini",
        "hp": 21500,
        "damage": 170,
        "speed": 0.95,
        "range": 75,            # MELEE (lionheart guardian)
        "attack_cooldown": 44,
        "radius": 40,
        "gold_reward": 2150,
        "color": (240, 195, 80),       # lionheart gold armor
        "color_dark": (95, 65, 20),
        "ability_cooldown": 225,
        "ability_damage": 450,
        "ability_range": 250,
        "entrance_text": "LEORIC, THE LIONHEART GUARDIAN, ROARS IN DEFIANCE!",
        "entrance_color": (255, 225, 130),

        # 4 skills (smart AI - lionheart guardian)
        "skill_q_damage": 450,      # Fearless Charge (dash)
        "skill_q_cooldown": 225,
        "skill_w_damage": 460,      # Sacred Hammer (AOE)
        "skill_w_cooldown": 280,
        "skill_e_damage": 440,      # Conceal Blast (AOE)
        "skill_e_cooldown": 310,
        "skill_r_damage": 800,      # Immortality (ultimate defensif)
        "skill_r_cooldown": 700,

        "hero_unlock": {
            "name": "Leoric",
            "title": "The Lionheart Guardian",
            "role": "Boss/Lionheart Guardian",
            "cost": 2050,
            "hp": 1600,
            "damage": 156,
            "speed": 1.35,
            "range": 85,
            "attack_cooldown": 44,
            "color": (240, 195, 80),
            "color_dark": (95, 65, 20),
            "skill_name": "Fearless Charge",
            "skill_desc": "Fearless charge + sacred hammer + conceal blast + immortality",
            "skill_cooldown": 225,
            "skill_damage": 450,
            "skill_range": 140,
            "description": "Ksatria hati singa dari Level 16",
        },
    },

    "shirotaka": {
        "name": "Shirotaka",
        "title": "The Tideborn Tactician",
        "boss_class": "mini",
        "hp": 22000,
        "damage": 180,
        "speed": 1.25,
        "range": 80,            # MELEE (tideborn shinobi)
        "attack_cooldown": 40,
        "radius": 34,
        "gold_reward": 2200,
        "color": (75, 100, 165),       # tideborn robe blue
        "color_dark": (15, 25, 60),
        "ability_cooldown": 220,
        "ability_damage": 460,
        "ability_range": 250,
        "entrance_text": "SHIROTAKA, THE TIDEBORN TACTICIAN, STRIKES LIKE THE TIDE!",
        "entrance_color": (135, 165, 220),

        # 4 skills (smart AI - tideborn tactician)
        "skill_q_damage": 460,      # Hiraishin (teleport strike)
        "skill_q_cooldown": 220,
        "skill_w_damage": 470,      # Water Boundary (AOE)
        "skill_w_cooldown": 280,
        "skill_e_damage": 450,      # Shadow Clones (AOE)
        "skill_e_cooldown": 310,
        "skill_r_damage": 820,      # Paper Bomb (ultimate)
        "skill_r_cooldown": 680,

        "hero_unlock": {
            "name": "Shirotaka",
            "title": "The Tideborn Tactician",
            "role": "Boss/Tideborn Shinobi",
            "cost": 2100,
            "hp": 1650,
            "damage": 168,
            "speed": 1.6,
            "range": 90,
            "attack_cooldown": 40,
            "color": (75, 100, 165),
            "color_dark": (15, 25, 60),
            "skill_name": "Hiraishin",
            "skill_desc": "Hiraishin + water boundary + shadow clones + paper bomb",
            "skill_cooldown": 220,
            "skill_damage": 460,
            "skill_range": 140,
            "description": "Shinobi taktik pasang surut dari Level 16",
        },
    },
    "kaelthorn": {
        "name": "Kaelthorn",
        "title": "The Azure Vanguard",
        "boss_class": "mini",
        "hp": 22500,
        "damage": 185,
        "speed": 1.15,
        "range": 80,            # MELEE (azure greatblade)
        "attack_cooldown": 42,
        "radius": 34,
        "gold_reward": 2250,
        "color": (55, 130, 230),       # azure energy blue
        "color_dark": (5, 15, 45),
        "ability_cooldown": 230,
        "ability_damage": 470,
        "ability_range": 250,
        "entrance_text": "KAELTHORN, THE AZURE VANGUARD, BRINGS THE STORM OF STEEL!",
        "entrance_color": (130, 200, 255),

        # 4 skills (smart AI - azure vanguard)
        "skill_q_damage": 470,      # Bravest Fighter (dash)
        "skill_q_cooldown": 230,
        "skill_w_damage": 480,      # Justice Blade (AOE)
        "skill_w_cooldown": 290,
        "skill_e_damage": 460,      # Defender's Assault (spin AOE)
        "skill_e_cooldown": 320,
        "skill_r_damage": 840,      # Chivalry Fists (ultimate)
        "skill_r_cooldown": 690,

        "hero_unlock": {
            "name": "Kaelthorn",
            "title": "The Azure Vanguard",
            "role": "Boss/Azure Warrior",
            "cost": 2150,
            "hp": 1700,
            "damage": 172,
            "speed": 1.55,
            "range": 90,
            "attack_cooldown": 42,
            "color": (55, 130, 230),
            "color_dark": (5, 15, 45),
            "skill_name": "Bravest Fighter",
            "skill_desc": "Bravest fighter + justice blade + defender's assault + chivalry fists",
            "skill_cooldown": 230,
            "skill_damage": 470,
            "skill_range": 140,
            "description": "Ksatria azure dari Level 17",
        },
    },

    "solvanth": {
        "name": "Solvanth",
        "title": "The Radiant Guardian",
        "boss_class": "mini",
        "hp": 23000,
        "damage": 180,
        "speed": 1.1,
        "range": 85,            # MELEE (centaur staff)
        "attack_cooldown": 44,
        "radius": 40,
        "gold_reward": 2300,
        "color": (245, 210, 90),       # radiant gold armor
        "color_dark": (95, 60, 25),
        "ability_cooldown": 235,
        "ability_damage": 480,
        "ability_range": 260,
        "entrance_text": "SOLVANTH, THE RADIANT GUARDIAN, GALLOPS INTO BATTLE!",
        "entrance_color": (245, 215, 110),

        # 4 skills (smart AI - radiant guardian)
        "skill_q_damage": 480,      # Ring Punishment
        "skill_q_cooldown": 235,
        "skill_w_damage": 490,      # Glorious Pathway (AOE)
        "skill_w_cooldown": 290,
        "skill_e_damage": 470,      # Law & Order (smash AOE)
        "skill_e_cooldown": 320,
        "skill_r_damage": 860,      # Wrath (ultimate leap)
        "skill_r_cooldown": 700,

        "hero_unlock": {
            "name": "Solvanth",
            "title": "The Radiant Guardian",
            "role": "Boss/Radiant Centaur",
            "cost": 2200,
            "hp": 1750,
            "damage": 166,
            "speed": 1.45,
            "range": 95,
            "attack_cooldown": 44,
            "color": (245, 210, 90),
            "color_dark": (95, 60, 25),
            "skill_name": "Ring Punishment",
            "skill_desc": "Ring punishment + glorious pathway + law & order + wrath",
            "skill_cooldown": 235,
            "skill_damage": 480,
            "skill_range": 140,
            "description": "Centaur penjaga cahaya dari Level 17",
        },
    },

    "xyrael": {
        "name": "Xy'rael",
        "title": "The Cyan Wraith",
        "boss_class": "mini",
        "hp": 23500,
        "damage": 195,
        "speed": 1.35,
        "range": 75,            # MELEE (crystal katana)
        "attack_cooldown": 40,
        "radius": 32,
        "gold_reward": 2350,
        "color": (90, 200, 230),       # cyan wraith
        "color_dark": (8, 12, 25),
        "ability_cooldown": 225,
        "ability_damage": 490,
        "ability_range": 250,
        "entrance_text": "XY'RAEL, THE CYAN WRAITH, CUTS THROUGH THE MIST!",
        "entrance_color": (140, 220, 240),

        # 4 skills (smart AI - cyan wraith assassin)
        "skill_q_damage": 490,      # Finch (dash)
        "skill_q_cooldown": 225,
        "skill_w_damage": 500,      # Defiant (AOE)
        "skill_w_cooldown": 285,
        "skill_e_damage": 480,      # Tempest (AOE)
        "skill_e_cooldown": 315,
        "skill_r_damage": 880,      # Lightness (ultimate)
        "skill_r_cooldown": 680,

        "hero_unlock": {
            "name": "Xy'rael",
            "title": "The Cyan Wraith",
            "role": "Boss/Cyan Assassin",
            "cost": 2250,
            "hp": 1650,
            "damage": 180,
            "speed": 1.65,
            "range": 85,
            "attack_cooldown": 40,
            "color": (90, 200, 230),
            "color_dark": (8, 12, 25),
            "skill_name": "Finch",
            "skill_desc": "Finch + defiant + tempest + lightness",
            "skill_cooldown": 225,
            "skill_damage": 490,
            "skill_range": 140,
            "description": "Asesin hantu cyan dari Level 17",
        },
    },
    "cryssalia": {
        "name": "Cryssalia",
        "title": "The Glacial Empress",
        "boss_class": "mini",
        "hp": 24000,
        "damage": 190,
        "speed": 1.1,
        "range": 270,           # RANGED (ice queen mage)
        "attack_cooldown": 46,
        "radius": 34,
        "gold_reward": 2400,
        "color": (115, 150, 215),      # glacial ice blue
        "color_dark": (30, 45, 90),
        "ability_cooldown": 235,
        "ability_damage": 500,
        "ability_range": 280,
        "entrance_text": "CRYSSALIA, THE GLACIAL EMPRESS, FREEZES THE BATTLEFIELD!",
        "entrance_color": (150, 200, 255),

        # 4 skills (smart AI - glacial empress)
        "skill_q_damage": 500,      # Frostshock
        "skill_q_cooldown": 235,
        "skill_w_damage": 510,      # Bitter Frost (AOE)
        "skill_w_cooldown": 295,
        "skill_e_damage": 490,      # Frostbites (AOE)
        "skill_e_cooldown": 325,
        "skill_r_damage": 900,      # Coldest (ultimate)
        "skill_r_cooldown": 700,

        # Ranged AI (kite behavior)
        "prefer_distance": 250,
        "min_distance": 130,

        "hero_unlock": {
            "name": "Cryssalia",
            "title": "The Glacial Empress",
            "role": "Boss/Ice Empress",
            "cost": 2300,
            "hp": 1800,
            "damage": 178,
            "speed": 1.5,
            "range": 250,
            "attack_cooldown": 46,
            "color": (115, 150, 215),
            "color_dark": (30, 45, 90),
            "skill_name": "Frostshock",
            "skill_desc": "Frostshock + bitter frost + frostbites + coldest",
            "skill_cooldown": 235,
            "skill_damage": 500,
            "skill_range": 150,
            "description": "Ratu es glasial dari Level 18",
        },
    },

    "kaelthar": {
        "name": "Kaelthar",
        "title": "The Storm Fist",
        "boss_class": "mini",
        "hp": 24500,
        "damage": 200,
        "speed": 1.3,
        "range": 75,            # MELEE (martial artist)
        "attack_cooldown": 40,
        "radius": 32,
        "gold_reward": 2450,
        "color": (250, 210, 80),       # lightning gold
        "color_dark": (55, 30, 20),
        "ability_cooldown": 230,
        "ability_damage": 510,
        "ability_range": 250,
        "entrance_text": "KAELTHAR, THE STORM FIST, SHATTERS THE SKIES!",
        "entrance_color": (255, 235, 130),

        # 4 skills (smart AI - storm fist)
        "skill_q_damage": 510,      # Charging Fist (dash)
        "skill_q_cooldown": 230,
        "skill_w_damage": 520,      # Quake (AOE)
        "skill_w_cooldown": 290,
        "skill_e_damage": 500,      # Fist Crack (AOE)
        "skill_e_cooldown": 320,
        "skill_r_damage": 920,      # Fist Break (ultimate)
        "skill_r_cooldown": 690,

        "hero_unlock": {
            "name": "Kaelthar",
            "title": "The Storm Fist",
            "role": "Boss/Storm Martial",
            "cost": 2350,
            "hp": 1700,
            "damage": 186,
            "speed": 1.6,
            "range": 85,
            "attack_cooldown": 40,
            "color": (250, 210, 80),
            "color_dark": (55, 30, 20),
            "skill_name": "Charging Fist",
            "skill_desc": "Charging fist + quake + fist crack + fist break",
            "skill_cooldown": 230,
            "skill_damage": 510,
            "skill_range": 140,
            "description": "Petarung tinju badai dari Level 18",
        },
    },

    "morkhaera": {
        "name": "Mor'khaera",
        "title": "The Blood-Feather Witch",
        "boss_class": "mini",
        "hp": 25000,
        "damage": 195,
        "speed": 1.1,
        "range": 280,           # RANGED (dark mage)
        "attack_cooldown": 46,
        "radius": 34,
        "gold_reward": 2500,
        "color": (180, 30, 50),        # blood feather crimson
        "color_dark": (60, 55, 75),
        "ability_cooldown": 240,
        "ability_damage": 510,
        "ability_range": 280,
        "entrance_text": "MOR'KHAERA, THE BLOOD-FEATHER WITCH, DESCENDS ON DARK WINGS!",
        "entrance_color": (255, 80, 110),

        # 4 skills (smart AI - blood-feather witch)
        "skill_q_damage": 510,      # Spirit Burst
        "skill_q_cooldown": 235,
        "skill_w_damage": 520,      # Air Strike (AOE)
        "skill_w_cooldown": 295,
        "skill_e_damage": 500,      # Energy Impact (AOE)
        "skill_e_cooldown": 325,
        "skill_r_damage": 920,      # Ethereal (ultimate)
        "skill_r_cooldown": 700,

        # Ranged AI (kite behavior)
        "prefer_distance": 250,
        "min_distance": 130,

        "hero_unlock": {
            "name": "Mor'khaera",
            "title": "The Blood-Feather Witch",
            "role": "Boss/Dark Witch",
            "cost": 2400,
            "hp": 1750,
            "damage": 180,
            "speed": 1.5,
            "range": 260,
            "attack_cooldown": 46,
            "color": (180, 30, 50),
            "color_dark": (60, 55, 75),
            "skill_name": "Spirit Burst",
            "skill_desc": "Spirit burst + air strike + energy impact + ethereal",
            "skill_cooldown": 235,
            "skill_damage": 510,
            "skill_range": 150,
            "description": "Penyihir bulu darah dari Level 18",
        },
    },
    "akahime": {
        "name": "Akahime",
        "title": "The Scarlet Blossom",
        "boss_class": "mini",
        "hp": 25500,
        "damage": 200,
        "speed": 1.3,
        "range": 260,           # RANGED (kunoichi marksman)
        "attack_cooldown": 44,
        "radius": 32,
        "gold_reward": 2550,
        "color": (200, 35, 75),        # scarlet blossom red
        "color_dark": (110, 15, 40),
        "ability_cooldown": 240,
        "ability_damage": 520,
        "ability_range": 270,
        "entrance_text": "AKAHIME, THE SCARLET BLOSSOM, BLOOMS IN BLOOD!",
        "entrance_color": (255, 160, 195),

        # 4 skills (smart AI - scarlet blossom)
        "skill_q_damage": 520,      # Petal Barrage
        "skill_q_cooldown": 240,
        "skill_w_damage": 530,      # Soul Scroll (AOE)
        "skill_w_cooldown": 300,
        "skill_e_damage": 510,      # Shadow (AOE)
        "skill_e_cooldown": 330,
        "skill_r_damage": 950,      # Higanbana (ultimate)
        "skill_r_cooldown": 710,

        # Ranged AI (kite behavior)
        "prefer_distance": 250,
        "min_distance": 130,

        "hero_unlock": {
            "name": "Akahime",
            "title": "The Scarlet Blossom",
            "role": "Boss/Scarlet Kunoichi",
            "cost": 2450,
            "hp": 1850,
            "damage": 188,
            "speed": 1.55,
            "range": 240,
            "attack_cooldown": 44,
            "color": (200, 35, 75),
            "color_dark": (110, 15, 40),
            "skill_name": "Petal Barrage",
            "skill_desc": "Petal barrage + soul scroll + shadow + higanbana",
            "skill_cooldown": 240,
            "skill_damage": 520,
            "skill_range": 150,
            "description": "Kunoichi merah dari Level 19",
        },
    },

    "nyxthrael": {
        "name": "Nyxthrael",
        "title": "The Cursed Executioner",
        "boss_class": "mini",
        "hp": 26000,
        "damage": 205,
        "speed": 1.15,
        "range": 85,            # MELEE (cursed scythe)
        "attack_cooldown": 42,
        "radius": 36,
        "gold_reward": 2600,
        "color": (120, 85, 155),       # cursed cloak purple
        "color_dark": (18, 10, 28),
        "ability_cooldown": 235,
        "ability_damage": 530,
        "ability_range": 260,
        "entrance_text": "NYXTHRAEL, THE CURSED EXECUTIONER, SWINGS THE SCYTHE!",
        "entrance_color": (170, 130, 200),

        # 4 skills (smart AI - cursed executioner)
        "skill_q_damage": 530,      # Ambush (execute)
        "skill_q_cooldown": 235,
        "skill_w_damage": 540,      # Nightfall (AOE)
        "skill_w_cooldown": 295,
        "skill_e_damage": 520,      # Dark Nightfall (AOE)
        "skill_e_cooldown": 325,
        "skill_r_damage": 960,      # Shadowbringer (ultimate)
        "skill_r_cooldown": 700,

        "hero_unlock": {
            "name": "Nyxthrael",
            "title": "The Cursed Executioner",
            "role": "Boss/Cursed Executioner",
            "cost": 2500,
            "hp": 1750,
            "damage": 192,
            "speed": 1.5,
            "range": 95,
            "attack_cooldown": 42,
            "color": (120, 85, 155),
            "color_dark": (18, 10, 28),
            "skill_name": "Ambush",
            "skill_desc": "Ambush + nightfall + dark nightfall + shadowbringer",
            "skill_cooldown": 235,
            "skill_damage": 530,
            "skill_range": 140,
            "description": "Algojo terkutuk dari Level 19",
        },
    },

    "sylvantheros": {
        "name": "Sylvantheros",
        "title": "The Verdant Farseer",
        "boss_class": "mini",
        "hp": 26500,
        "damage": 195,
        "speed": 1.1,
        "range": 275,           # RANGED (farseer staff)
        "attack_cooldown": 46,
        "radius": 34,
        "gold_reward": 2650,
        "color": (110, 175, 85),       # verdant leaf green
        "color_dark": (25, 60, 28),
        "ability_cooldown": 240,
        "ability_damage": 530,
        "ability_range": 280,
        "entrance_text": "SYLVANTHEROS, THE VERDANT FARSEER, WHISPERS TO THE GROVE!",
        "entrance_color": (170, 220, 120),

        # 4 skills (smart AI - verdant farseer)
        "skill_q_damage": 530,      # Sprout
        "skill_q_cooldown": 240,
        "skill_w_damage": 540,      # Teleport (AOE)
        "skill_w_cooldown": 300,
        "skill_e_damage": 520,      # Treants (AOE)
        "skill_e_cooldown": 330,
        "skill_r_damage": 960,      # Wrath (ultimate)
        "skill_r_cooldown": 710,

        # Ranged AI (kite behavior)
        "prefer_distance": 250,
        "min_distance": 130,

        "hero_unlock": {
            "name": "Sylvantheros",
            "title": "The Verdant Farseer",
            "role": "Boss/Verdant Farseer",
            "cost": 2550,
            "hp": 1800,
            "damage": 184,
            "speed": 1.5,
            "range": 255,
            "attack_cooldown": 46,
            "color": (110, 175, 85),
            "color_dark": (25, 60, 28),
            "skill_name": "Sprout",
            "skill_desc": "Sprout + teleport + treants + wrath",
            "skill_cooldown": 240,
            "skill_damage": 530,
            "skill_range": 150,
            "description": "Peramal hijau dari Level 19",
        },
    },
    "astraelion": {
        "name": "Astraelion",
        "title": "The Starlight Swordmaster",
        "boss_class": "mini",
        "hp": 27000,
        "damage": 210,
        "speed": 1.35,
        "range": 80,            # MELEE (starlight sword)
        "attack_cooldown": 40,
        "radius": 32,
        "gold_reward": 2700,
        "color": (150, 180, 230),      # starlight steel blue
        "color_dark": (18, 28, 55),
        "ability_cooldown": 240,
        "ability_damage": 550,
        "ability_range": 260,
        "entrance_text": "ASTRAELION, THE STARLIGHT SWORDMASTER, DANCES BETWEEN STARS!",
        "entrance_color": (200, 220, 255),

        # 4 skills (smart AI - starlight swordmaster)
        "skill_q_damage": 550,      # Swordfall
        "skill_q_cooldown": 240,
        "skill_w_damage": 560,      # Spirit Blade (AOE)
        "skill_w_cooldown": 300,
        "skill_e_damage": 540,      # Force Escape (AOE)
        "skill_e_cooldown": 330,
        "skill_r_damage": 1000,     # Zero Return (ultimate)
        "skill_r_cooldown": 710,

        "hero_unlock": {
            "name": "Astraelion",
            "title": "The Starlight Swordmaster",
            "role": "Boss/Starlight Assassin",
            "cost": 2600,
            "hp": 1900,
            "damage": 196,
            "speed": 1.65,
            "range": 90,
            "attack_cooldown": 40,
            "color": (150, 180, 230),
            "color_dark": (18, 28, 55),
            "skill_name": "Swordfall",
            "skill_desc": "Swordfall + spirit blade + force escape + zero return",
            "skill_cooldown": 240,
            "skill_damage": 550,
            "skill_range": 140,
            "description": "Pedang bintang dari Level 20",
        },
    },

    "morvaenthir": {
        "name": "Morvaenthir",
        "title": "The Soul Reaper",
        "boss_class": "mini",
        "hp": 27500,
        "damage": 205,
        "speed": 1.1,
        "range": 285,           # RANGED (necromancer mage)
        "attack_cooldown": 46,
        "radius": 34,
        "gold_reward": 2750,
        "color": (215, 220, 235),      # soul silver robe
        "color_dark": (18, 25, 38),
        "ability_cooldown": 245,
        "ability_damage": 560,
        "ability_range": 290,
        "entrance_text": "MORVAENTHIR, THE SOUL REAPER, HARVESTS THE FALLEN!",
        "entrance_color": (220, 230, 250),

        # 4 skills (smart AI - soul reaper)
        "skill_q_damage": 560,      # Soul Fragment
        "skill_q_cooldown": 245,
        "skill_w_damage": 570,      # Spirit Bind (AOE)
        "skill_w_cooldown": 305,
        "skill_e_damage": 550,      # Essence (AOE)
        "skill_e_cooldown": 335,
        "skill_r_damage": 1010,     # Shadow Realm (ultimate)
        "skill_r_cooldown": 720,

        # Ranged AI (kite behavior)
        "prefer_distance": 250,
        "min_distance": 130,

        "hero_unlock": {
            "name": "Morvaenthir",
            "title": "The Soul Reaper",
            "role": "Boss/Soul Reaper",
            "cost": 2650,
            "hp": 1850,
            "damage": 190,
            "speed": 1.5,
            "range": 265,
            "attack_cooldown": 46,
            "color": (215, 220, 235),
            "color_dark": (18, 25, 38),
            "skill_name": "Soul Fragment",
            "skill_desc": "Soul fragment + spirit bind + essence + shadow realm",
            "skill_cooldown": 245,
            "skill_damage": 560,
            "skill_range": 150,
            "description": "Penuai jiwa dari Level 20",
        },
    },

    "thornvaegrim": {
        "name": "Thornvaegrim",
        "title": "The Twisted Elderwood",
        "boss_class": "mini",
        "hp": 28000,
        "damage": 200,
        "speed": 0.95,
        "range": 90,            # MELEE (elderwood treant)
        "attack_cooldown": 44,
        "radius": 42,
        "gold_reward": 2800,
        "color": (110, 175, 70),       # elderwood moss green
        "color_dark": (30, 65, 22),
        "ability_cooldown": 245,
        "ability_damage": 560,
        "ability_range": 270,
        "entrance_text": "THORNVAEGRIM, THE TWISTED ELDERWOOD, RISES FROM ROTTEN EARTH!",
        "entrance_color": (160, 210, 100),

        # 4 skills (smart AI - twisted elderwood)
        "skill_q_damage": 560,      # Bramble
        "skill_q_cooldown": 245,
        "skill_w_damage": 570,      # Twisted Advance (AOE)
        "skill_w_cooldown": 300,
        "skill_e_damage": 550,      # Sapling Throw (AOE)
        "skill_e_cooldown": 330,
        "skill_r_damage": 1010,     # Grasp (ultimate)
        "skill_r_cooldown": 710,

        "hero_unlock": {
            "name": "Thornvaegrim",
            "title": "The Twisted Elderwood",
            "role": "Boss/Elderwood Treant",
            "cost": 2700,
            "hp": 1950,
            "damage": 186,
            "speed": 1.35,
            "range": 100,
            "attack_cooldown": 44,
            "color": (110, 175, 70),
            "color_dark": (30, 65, 22),
            "skill_name": "Bramble",
            "skill_desc": "Bramble + twisted advance + sapling throw + grasp",
            "skill_cooldown": 245,
            "skill_damage": 560,
            "skill_range": 140,
            "description": "Treant purba bengkok dari Level 20",
        },
    },
    "kurogari": {
        "name": "Kurogari",
        "title": "The Void Reaper",
        "boss_class": "mini",
        "hp": 28000,
        "damage": 220,
        "speed": 1.4,
        "range": 70,             # MELEE (shadow scythe)
        "attack_cooldown": 36,
        "radius": 30,
        "gold_reward": 2900,
        "color": (140, 85, 175),       # void purple shadow
        "color_dark": (30, 15, 45),
        "ability_cooldown": 245,
        "ability_damage": 580,
        "ability_range": 280,
        "entrance_text": "KUROGARI, THE VOID REAPER, CUTS THROUGH THE SHADOWS!",
        "entrance_color": (240, 60, 130),

        # 4 skills (smart AI - void reaper)
        "skill_q_damage": 580,      # Soul Reap
        "skill_q_cooldown": 250,
        "skill_w_damage": 590,      # Shadow Mist (AOE)
        "skill_w_cooldown": 310,
        "skill_e_damage": 570,      # Pinpoint (AOE)
        "skill_e_cooldown": 340,
        "skill_r_damage": 1050,     # Demonic Feast (ultimate)
        "skill_r_cooldown": 730,

        "hero_unlock": {
            "name": "Kurogari",
            "title": "The Void Reaper",
            "role": "Boss/Shadow Ninja Reaper",
            "cost": 2800,
            "hp": 1900,
            "damage": 205,
            "speed": 1.7,
            "range": 80,
            "attack_cooldown": 36,
            "color": (140, 85, 175),
            "color_dark": (30, 15, 45),
            "skill_name": "Soul Reap",
            "skill_desc": "Soul reap + shadow mist + pinpoint + demonic feast",
            "skill_cooldown": 250,
            "skill_damage": 580,
            "skill_range": 140,
            "description": "Reaper bayangan dari Level 21",
        },
    },
    "morvekhar": {
        "name": "Morvekhar",
        "title": "The Deathforged",
        "boss_class": "mini",
        "hp": 30000,
        "damage": 215,
        "speed": 0.95,
        "range": 60,             # MELEE (iron mace)
        "attack_cooldown": 48,
        "radius": 34,
        "gold_reward": 2950,
        "color": (120, 130, 140),      # forged iron
        "color_dark": (10, 12, 15),
        "ability_cooldown": 255,
        "ability_damage": 585,
        "ability_range": 270,
        "entrance_text": "MORVEKHAR, THE DEATHFORGED, MARCHES WITH IRON SOUL!",
        "entrance_color": (240, 200, 90),

        # 4 skills (smart AI - deathforged)
        "skill_q_damage": 585,      # Soul Cleave
        "skill_q_cooldown": 255,
        "skill_w_damage": 595,      # Ironbound (AOE)
        "skill_w_cooldown": 315,
        "skill_e_damage": 575,      # Juggernaut Dash (AOE)
        "skill_e_cooldown": 345,
        "skill_r_damage": 1060,     # Shadow Realm (ultimate)
        "skill_r_cooldown": 740,

        "hero_unlock": {
            "name": "Morvekhar",
            "title": "The Deathforged",
            "role": "Boss/Iron Juggernaut",
            "cost": 3000,
            "hp": 2300,
            "damage": 200,
            "speed": 1.2,
            "range": 65,
            "attack_cooldown": 48,
            "color": (120, 130, 140),
            "color_dark": (10, 12, 15),
            "skill_name": "Soul Cleave",
            "skill_desc": "Soul cleave + ironbound + juggernaut dash + shadow realm",
            "skill_cooldown": 255,
            "skill_damage": 585,
            "skill_range": 150,
            "description": "Raksasa besi dari Level 21",
        },
    },
    "vorgath": {
        "name": "Vorgath",
        "title": "The Demon Warden",
        "boss_class": "mini",
        "hp": 28500,
        "damage": 225,
        "speed": 1.25,
        "range": 90,             # MELEE (chain ball)
        "attack_cooldown": 42,
        "radius": 32,
        "gold_reward": 2850,
        "color": (150, 115, 165),      # demon warden purple
        "color_dark": (15, 10, 20),
        "ability_cooldown": 250,
        "ability_damage": 590,
        "ability_range": 290,
        "entrance_text": "VORGATH, THE DEMON WARDEN, UNLEASHES HIS CHAINS!",
        "entrance_color": (200, 160, 80),

        # 4 skills (smart AI - demon warden)
        "skill_q_damage": 590,      # Demonic Gaze
        "skill_q_cooldown": 250,
        "skill_w_damage": 600,      # Demonic Impact (AOE)
        "skill_w_cooldown": 315,
        "skill_e_damage": 580,      # Demon Purge (AOE)
        "skill_e_cooldown": 340,
        "skill_r_damage": 1070,     # Demonic Domain (ultimate)
        "skill_r_cooldown": 730,

        "hero_unlock": {
            "name": "Vorgath",
            "title": "The Demon Warden",
            "role": "Boss/Demon Warden",
            "cost": 2900,
            "hp": 2000,
            "damage": 210,
            "speed": 1.5,
            "range": 95,
            "attack_cooldown": 42,
            "color": (150, 115, 165),
            "color_dark": (15, 10, 20),
            "skill_name": "Demonic Gaze",
            "skill_desc": "Demonic gaze + demonic impact + demon purge + demonic domain",
            "skill_cooldown": 250,
            "skill_damage": 590,
            "skill_range": 150,
            "description": "Penjaga iblis dari Level 21",
        },
    },
    "grimstalker": {
        "name": "Grimstalker",
        "title": "The Chembeast of the Depths",
        "boss_class": "mini",
        "hp": 29500,
        "damage": 225,
        "speed": 1.35,
        "range": 70,             # MELEE (toxic claws)
        "attack_cooldown": 38,
        "radius": 30,
        "gold_reward": 3000,
        "color": (90, 200, 70),        # toxic green
        "color_dark": (18, 45, 10),
        "ability_cooldown": 250,
        "ability_damage": 600,
        "ability_range": 290,
        "entrance_text": "GRIMSTALKER, THE CHEMBEAST OF THE DEPTHS, RISES FROM THE TOXIC VOID!",
        "entrance_color": (120, 230, 90),

        # 4 skills (smart AI - chembeast)
        "skill_q_damage": 600,      # Toxic Claw
        "skill_q_cooldown": 255,
        "skill_w_damage": 610,      # Venom Cloud (AOE)
        "skill_w_cooldown": 315,
        "skill_e_damage": 590,      # Chem Rampage (AOE)
        "skill_e_cooldown": 345,
        "skill_r_damage": 1080,     # Bio Doom (ultimate)
        "skill_r_cooldown": 740,

        "hero_unlock": {
            "name": "Grimstalker",
            "title": "The Chembeast of the Depths",
            "role": "Boss/Toxic Werewolf",
            "cost": 2950,
            "hp": 1950,
            "damage": 210,
            "speed": 1.65,
            "range": 80,
            "attack_cooldown": 38,
            "color": (90, 200, 70),
            "color_dark": (18, 45, 10),
            "skill_name": "Toxic Claw",
            "skill_desc": "Toxic claw + venom cloud + chem rampage + bio doom",
            "skill_cooldown": 255,
            "skill_damage": 600,
            "skill_range": 150,
            "description": "Werewolf beracun dari Level 22",
        },
    },
    "kryvoxar": {
        "name": "Kryvoxar",
        "title": "The Crystalborne Wraith",
        "boss_class": "mini",
        "hp": 29000,
        "damage": 220,
        "speed": 1.15,
        "range": 270,            # RANGED (crystal shards)
        "attack_cooldown": 45,
        "radius": 30,
        "gold_reward": 3050,
        "color": (140, 170, 255),      # crystal blue
        "color_dark": (15, 20, 55),
        "ability_cooldown": 255,
        "ability_damage": 605,
        "ability_range": 300,
        "entrance_text": "KRYVOXAR, THE CRYSTALBORNE WRAITH, SHATTERS THE LIGHT!",
        "entrance_color": (190, 210, 255),

        # 4 skills (smart AI - crystal wraith)
        "skill_q_damage": 605,      # Crystal Shard
        "skill_q_cooldown": 255,
        "skill_w_damage": 615,      # Crystal Storm (AOE)
        "skill_w_cooldown": 320,
        "skill_e_damage": 595,      # Phase Shift (AOE)
        "skill_e_cooldown": 350,
        "skill_r_damage": 1090,     # Prism Burst (ultimate)
        "skill_r_cooldown": 745,

        # Ranged AI (kite behavior)
        "prefer_distance": 240,
        "min_distance": 120,

        "hero_unlock": {
            "name": "Kryvoxar",
            "title": "The Crystalborne Wraith",
            "role": "Boss/Crystal Wraith",
            "cost": 3000,
            "hp": 1850,
            "damage": 205,
            "speed": 1.45,
            "range": 250,
            "attack_cooldown": 45,
            "color": (140, 170, 255),
            "color_dark": (15, 20, 55),
            "skill_name": "Crystal Shard",
            "skill_desc": "Crystal shard + crystal storm + phase shift + prism burst",
            "skill_cooldown": 255,
            "skill_damage": 605,
            "skill_range": 160,
            "description": "Wraith kristal dari Level 22",
        },
    },
    "vargroth": {
        "name": "Vargroth",
        "title": "The Bloodmoon Alpha",
        "boss_class": "mini",
        "hp": 30000,
        "damage": 230,
        "speed": 1.45,
        "range": 75,             # MELEE (bloodmoon claws)
        "attack_cooldown": 36,
        "radius": 32,
        "gold_reward": 3100,
        "color": (220, 60, 80),        # bloodmoon red
        "color_dark": (50, 10, 18),
        "ability_cooldown": 260,
        "ability_damage": 610,
        "ability_range": 280,
        "entrance_text": "VARGROTH, THE BLOODMOON ALPHA, HOWLS AT THE CRIMSON MOON!",
        "entrance_color": (255, 110, 130),

        # 4 skills (smart AI - bloodmoon alpha)
        "skill_q_damage": 610,      # Blood Rend
        "skill_q_cooldown": 260,
        "skill_w_damage": 620,      # Moon Howl (AOE)
        "skill_w_cooldown": 320,
        "skill_e_damage": 600,      # Alpha Strike (AOE)
        "skill_e_cooldown": 350,
        "skill_r_damage": 1100,     # Bloodmoon Frenzy (ultimate)
        "skill_r_cooldown": 750,

        "hero_unlock": {
            "name": "Vargroth",
            "title": "The Bloodmoon Alpha",
            "role": "Boss/Bloodmoon Werewolf",
            "cost": 3100,
            "hp": 2000,
            "damage": 215,
            "speed": 1.75,
            "range": 85,
            "attack_cooldown": 36,
            "color": (220, 60, 80),
            "color_dark": (50, 10, 18),
            "skill_name": "Blood Rend",
            "skill_desc": "Blood rend + moon howl + alpha strike + bloodmoon frenzy",
            "skill_cooldown": 260,
            "skill_damage": 610,
            "skill_range": 150,
            "description": "Alpha werewolf dari Level 22",
        },
    },
    "drav": {
        "name": "Drav",
        "title": "The Tideforged Warden",
        "boss_class": "mini",
        "hp": 30500,
        "damage": 230,
        "speed": 1.15,
        "range": 85,             # MELEE (anchor chain)
        "attack_cooldown": 44,
        "radius": 32,
        "gold_reward": 3150,
        "color": (70, 160, 200),       # tide blue
        "color_dark": (10, 30, 55),
        "ability_cooldown": 260,
        "ability_damage": 620,
        "ability_range": 300,
        "entrance_text": "DRAV, THE TIDEFORGED WARDEN, RISES FROM THE DEEP!",
        "entrance_color": (140, 220, 255),

        # 4 skills (smart AI - tideforged warden)
        "skill_q_damage": 620,      # Anchor Slam
        "skill_q_cooldown": 260,
        "skill_w_damage": 630,      # Tidal Wave (AOE)
        "skill_w_cooldown": 320,
        "skill_e_damage": 610,      # Chain Pull (AOE)
        "skill_e_cooldown": 350,
        "skill_r_damage": 1120,     # Ocean's Wrath (ultimate)
        "skill_r_cooldown": 750,

        "hero_unlock": {
            "name": "Drav",
            "title": "The Tideforged Warden",
            "role": "Boss/Tideforged Warden",
            "cost": 3100,
            "hp": 2050,
            "damage": 215,
            "speed": 1.5,
            "range": 95,
            "attack_cooldown": 44,
            "color": (70, 160, 200),
            "color_dark": (10, 30, 55),
            "skill_name": "Anchor Slam",
            "skill_desc": "Anchor slam + tidal wave + chain pull + ocean's wrath",
            "skill_cooldown": 260,
            "skill_damage": 620,
            "skill_range": 160,
            "description": "Penjaga laut dari Level 23",
        },
    },
    "lyrienne": {
        "name": "Lyrienne",
        "title": "The Chorister of Twilight Vespers",
        "boss_class": "mini",
        "hp": 29500,
        "damage": 225,
        "speed": 1.1,
        "range": 280,            # RANGED (twilight magic)
        "attack_cooldown": 46,
        "radius": 30,
        "gold_reward": 3200,
        "color": (180, 120, 230),      # twilight violet
        "color_dark": (30, 15, 60),
        "ability_cooldown": 265,
        "ability_damage": 625,
        "ability_range": 310,
        "entrance_text": "LYRIENNE, THE CHORISTER OF TWILIGHT VESPERS, SINGS THE DUSK!",
        "entrance_color": (220, 170, 255),

        # 4 skills (smart AI - twilight chorister)
        "skill_q_damage": 625,      # Vesper Bolt
        "skill_q_cooldown": 265,
        "skill_w_damage": 635,      # Twilight Chorus (AOE)
        "skill_w_cooldown": 325,
        "skill_e_damage": 615,      # Harmonic Shift (AOE)
        "skill_e_cooldown": 355,
        "skill_r_damage": 1130,     # Symphony of Dusk (ultimate)
        "skill_r_cooldown": 755,

        # Ranged AI (kite behavior)
        "prefer_distance": 250,
        "min_distance": 130,

        "hero_unlock": {
            "name": "Lyrienne",
            "title": "The Chorister of Twilight Vespers",
            "role": "Boss/Twilight Chorister",
            "cost": 3200,
            "hp": 1900,
            "damage": 210,
            "speed": 1.4,
            "range": 260,
            "attack_cooldown": 46,
            "color": (180, 120, 230),
            "color_dark": (30, 15, 60),
            "skill_name": "Vesper Bolt",
            "skill_desc": "Vesper bolt + twilight chorus + harmonic shift + symphony of dusk",
            "skill_cooldown": 265,
            "skill_damage": 625,
            "skill_range": 170,
            "description": "Penyanyi senja dari Level 23",
        },
    },
    "valthar": {
        "name": "Valthar",
        "title": "The Sentinel of Broken Kings",
        "boss_class": "mini",
        "hp": 31000,
        "damage": 235,
        "speed": 1.0,
        "range": 90,             # MELEE (golden greatsword)
        "attack_cooldown": 46,
        "radius": 34,
        "gold_reward": 3250,
        "color": (215, 175, 70),       # royal gold
        "color_dark": (35, 25, 5),
        "ability_cooldown": 270,
        "ability_damage": 630,
        "ability_range": 290,
        "entrance_text": "VALTHAR, THE SENTINEL OF BROKEN KINGS, STANDS ETERNAL!",
        "entrance_color": (255, 220, 120),

        # 4 skills (smart AI - sentinel colossus)
        "skill_q_damage": 630,      # Royal Sunder
        "skill_q_cooldown": 270,
        "skill_w_damage": 640,      # Golden Ward (AOE)
        "skill_w_cooldown": 330,
        "skill_e_damage": 620,      # Crownfall (AOE)
        "skill_e_cooldown": 360,
        "skill_r_damage": 1140,     # Judgment of Kings (ultimate)
        "skill_r_cooldown": 760,

        "hero_unlock": {
            "name": "Valthar",
            "title": "The Sentinel of Broken Kings",
            "role": "Boss/Golden Sentinel",
            "cost": 3300,
            "hp": 2200,
            "damage": 220,
            "speed": 1.35,
            "range": 100,
            "attack_cooldown": 46,
            "color": (215, 175, 70),
            "color_dark": (35, 25, 5),
            "skill_name": "Royal Sunder",
            "skill_desc": "Royal sunder + golden ward + crownfall + judgment of kings",
            "skill_cooldown": 270,
            "skill_damage": 630,
            "skill_range": 170,
            "description": "Penjaga emas dari Level 23",
        },
    },
    "khalzaredh": {
        "name": "Khal'zaredh",
        "title": "The Sandborn Prince",
        "boss_class": "mini",
        "hp": 31500,
        "damage": 235,
        "speed": 1.3,
        "range": 80,             # MELEE (sand blade)
        "attack_cooldown": 40,
        "radius": 32,
        "gold_reward": 3300,
        "color": (225, 180, 110),      # sand gold
        "color_dark": (55, 35, 15),
        "ability_cooldown": 265,
        "ability_damage": 640,
        "ability_range": 300,
        "entrance_text": "KHAL'ZAREDH, THE SANDBORN PRINCE, RISES FROM THE DUNES!",
        "entrance_color": (255, 220, 150),

        # 4 skills (smart AI - sandborn prince)
        "skill_q_damage": 640,      # Sand Slash
        "skill_q_cooldown": 265,
        "skill_w_damage": 650,      # Dune Surge (AOE)
        "skill_w_cooldown": 325,
        "skill_e_damage": 630,      # Sandstorm (AOE)
        "skill_e_cooldown": 355,
        "skill_r_damage": 1160,     # Desert's Wrath (ultimate)
        "skill_r_cooldown": 760,

        "hero_unlock": {
            "name": "Khal'zaredh",
            "title": "The Sandborn Prince",
            "role": "Boss/Sandborn Prince",
            "cost": 3250,
            "hp": 2100,
            "damage": 220,
            "speed": 1.6,
            "range": 90,
            "attack_cooldown": 40,
            "color": (225, 180, 110),
            "color_dark": (55, 35, 15),
            "skill_name": "Sand Slash",
            "skill_desc": "Sand slash + dune surge + sandstorm + desert's wrath",
            "skill_cooldown": 265,
            "skill_damage": 640,
            "skill_range": 160,
            "description": "Pangeran pasir dari Level 24",
        },
    },
    "nyxaroth": {
        "name": "Nyxaroth",
        "title": "The Void-Starweaver",
        "boss_class": "mini",
        "hp": 30500,
        "damage": 230,
        "speed": 1.1,
        "range": 285,            # RANGED (cosmic star magic)
        "attack_cooldown": 47,
        "radius": 30,
        "gold_reward": 3350,
        "color": (150, 120, 255),      # cosmic violet
        "color_dark": (20, 12, 60),
        "ability_cooldown": 270,
        "ability_damage": 645,
        "ability_range": 315,
        "entrance_text": "NYXAROTH, THE VOID-STARWEAVER, UNRAVELS THE COSMOS!",
        "entrance_color": (200, 180, 255),

        # 4 skills (smart AI - void-starweaver)
        "skill_q_damage": 645,      # Star Bolt
        "skill_q_cooldown": 270,
        "skill_w_damage": 655,      # Void Constellation (AOE)
        "skill_w_cooldown": 330,
        "skill_e_damage": 635,      # Starfall (AOE)
        "skill_e_cooldown": 360,
        "skill_r_damage": 1170,     # Singularity (ultimate)
        "skill_r_cooldown": 765,

        # Ranged AI (kite behavior)
        "prefer_distance": 255,
        "min_distance": 135,

        "hero_unlock": {
            "name": "Nyxaroth",
            "title": "The Void-Starweaver",
            "role": "Boss/Void-Starweaver",
            "cost": 3350,
            "hp": 1950,
            "damage": 215,
            "speed": 1.4,
            "range": 265,
            "attack_cooldown": 47,
            "color": (150, 120, 255),
            "color_dark": (20, 12, 60),
            "skill_name": "Star Bolt",
            "skill_desc": "Star bolt + void constellation + starfall + singularity",
            "skill_cooldown": 270,
            "skill_damage": 645,
            "skill_range": 175,
            "description": "Penenun bintang dari Level 24",
        },
    },
    "veshtrax": {
        "name": "Veshtrax",
        "title": "The Sapphire Executor",
        "boss_class": "mini",
        "hp": 32000,
        "damage": 240,
        "speed": 1.25,
        "range": 85,             # MELEE (sapphire rapier)
        "attack_cooldown": 38,
        "radius": 32,
        "gold_reward": 3400,
        "color": (80, 150, 255),       # sapphire blue
        "color_dark": (10, 25, 70),
        "ability_cooldown": 275,
        "ability_damage": 650,
        "ability_range": 290,
        "entrance_text": "VESHTRAX, THE SAPPHIRE EXECUTOR, STRIKES WITH ROYAL FURY!",
        "entrance_color": (150, 200, 255),

        # 4 skills (smart AI - sapphire executor)
        "skill_q_damage": 650,      # Sapphire Lunge
        "skill_q_cooldown": 275,
        "skill_w_damage": 660,      # Royal Barrier (AOE)
        "skill_w_cooldown": 335,
        "skill_e_damage": 640,      # Executioner's Flurry (AOE)
        "skill_e_cooldown": 365,
        "skill_r_damage": 1180,     # Judgment Blade (ultimate)
        "skill_r_cooldown": 770,

        "hero_unlock": {
            "name": "Veshtrax",
            "title": "The Sapphire Executor",
            "role": "Boss/Sapphire Executor",
            "cost": 3400,
            "hp": 2150,
            "damage": 225,
            "speed": 1.55,
            "range": 95,
            "attack_cooldown": 38,
            "color": (80, 150, 255),
            "color_dark": (10, 25, 70),
            "skill_name": "Sapphire Lunge",
            "skill_desc": "Sapphire lunge + royal barrier + executioner's flurry + judgment blade",
            "skill_cooldown": 275,
            "skill_damage": 650,
            "skill_range": 165,
            "description": "Eksekutor bangsawan dari Level 24",
        },
    },
    "grimjack": {
        "name": "Grimjack",
        "title": "The Cackling Fiend",
        "boss_class": "mini",
        "hp": 32500,
        "damage": 240,
        "speed": 1.45,
        "range": 75,             # MELEE (poison daggers)
        "attack_cooldown": 36,
        "radius": 30,
        "gold_reward": 3450,
        "color": (150, 90, 200),       # void purple
        "color_dark": (35, 15, 60),
        "ability_cooldown": 275,
        "ability_damage": 660,
        "ability_range": 300,
        "entrance_text": "GRIMJACK, THE CACKLING FIEND, DANCES IN THE VOID!",
        "entrance_color": (200, 150, 255),

        # 4 skills (smart AI - cackling fiend)
        "skill_q_damage": 660,      # Venom Stab
        "skill_q_cooldown": 275,
        "skill_w_damage": 670,      # Cackling Blight (AOE)
        "skill_w_cooldown": 335,
        "skill_e_damage": 650,      # Shadow Step (AOE)
        "skill_e_cooldown": 365,
        "skill_r_damage": 1200,     # Fiendish Carnival (ultimate)
        "skill_r_cooldown": 775,

        "hero_unlock": {
            "name": "Grimjack",
            "title": "The Cackling Fiend",
            "role": "Boss/Void Assassin",
            "cost": 3450,
            "hp": 2050,
            "damage": 225,
            "speed": 1.75,
            "range": 85,
            "attack_cooldown": 36,
            "color": (150, 90, 200),
            "color_dark": (35, 15, 60),
            "skill_name": "Venom Stab",
            "skill_desc": "Venom stab + cackling blight + shadow step + fiendish carnival",
            "skill_cooldown": 275,
            "skill_damage": 660,
            "skill_range": 165,
            "description": "Iblis cekikikan dari Level 25",
        },
    },
    "morvaeth": {
        "name": "Morvaeth",
        "title": "The Crimson Reaver",
        "boss_class": "mini",
        "hp": 31500,
        "damage": 245,
        "speed": 1.35,
        "range": 80,             # MELEE (crimson scythe)
        "attack_cooldown": 40,
        "radius": 32,
        "gold_reward": 3500,
        "color": (220, 55, 75),        # crimson red
        "color_dark": (55, 8, 15),
        "ability_cooldown": 280,
        "ability_damage": 670,
        "ability_range": 295,
        "entrance_text": "MORVAETH, THE CRIMSON REAVER, HARVESTS IN BLOOD!",
        "entrance_color": (255, 120, 140),

        # 4 skills (smart AI - crimson reaver)
        "skill_q_damage": 670,      # Crimson Slash
        "skill_q_cooldown": 280,
        "skill_w_damage": 680,      # Blood Reap (AOE)
        "skill_w_cooldown": 340,
        "skill_e_damage": 660,      # Reaver's Charge (AOE)
        "skill_e_cooldown": 370,
        "skill_r_damage": 1210,     # Crimson Tempest (ultimate)
        "skill_r_cooldown": 780,

        "hero_unlock": {
            "name": "Morvaeth",
            "title": "The Crimson Reaver",
            "role": "Boss/Crimson Assassin",
            "cost": 3500,
            "hp": 2100,
            "damage": 230,
            "speed": 1.65,
            "range": 90,
            "attack_cooldown": 40,
            "color": (220, 55, 75),
            "color_dark": (55, 8, 15),
            "skill_name": "Crimson Slash",
            "skill_desc": "Crimson slash + blood reap + reaver's charge + crimson tempest",
            "skill_cooldown": 280,
            "skill_damage": 670,
            "skill_range": 170,
            "description": "Perobek merah dari Level 25",
        },
    },
    "vulkareth": {
        "name": "Vulkareth",
        "title": "The Emberborn Titan",
        "boss_class": "mini",
        "hp": 33500,
        "damage": 250,
        "speed": 1.15,
        "range": 90,             # MELEE (dual form, lava fists)
        "attack_cooldown": 46,
        "radius": 36,
        "gold_reward": 3550,
        "color": (255, 130, 40),       # ember orange
        "color_dark": (60, 20, 5),
        "ability_cooldown": 285,
        "ability_damage": 680,
        "ability_range": 290,
        "entrance_text": "VULKARETH, THE EMBERBORN TITAN, IGNITES THE EARTH!",
        "entrance_color": (255, 190, 90),

        # 4 skills (smart AI - emberborn titan)
        "skill_q_damage": 680,      # Ember Fist
        "skill_q_cooldown": 285,
        "skill_w_damage": 690,      # Magma Eruption (AOE)
        "skill_w_cooldown": 345,
        "skill_e_damage": 670,      # Titan Charge (AOE)
        "skill_e_cooldown": 375,
        "skill_r_damage": 1220,     # Emberborn Fury (ultimate)
        "skill_r_cooldown": 785,

        "hero_unlock": {
            "name": "Vulkareth",
            "title": "The Emberborn Titan",
            "role": "Boss/Ember Titan",
            "cost": 3550,
            "hp": 2350,
            "damage": 235,
            "speed": 1.4,
            "range": 100,
            "attack_cooldown": 46,
            "color": (255, 130, 40),
            "color_dark": (60, 20, 5),
            "skill_name": "Ember Fist",
            "skill_desc": "Ember fist + magma eruption + titan charge + emberborn fury",
            "skill_cooldown": 285,
            "skill_damage": 680,
            "skill_range": 175,
            "description": "Titan api dari Level 25",
        },
    },
    "aelyrion": {
        "name": "Aelyrion",
        "title": "The Divine Guardian",
        "boss_class": "mini",
        "hp": 33000,
        "damage": 245,
        "speed": 1.2,
        "range": 80,             # MELEE (steel maiden guardian)
        "attack_cooldown": 42,
        "radius": 32,
        "gold_reward": 3600,
        "color": (200, 220, 255),      # steel white-blue
        "color_dark": (40, 50, 80),
        "ability_cooldown": 280,
        "ability_damage": 690,
        "ability_range": 305,
        "entrance_text": "AELYRION, THE DIVINE GUARDIAN, SHIELDS THE EMPYREAN GATES!",
        "entrance_color": (220, 235, 255),

        # 4 skills (smart AI - divine guardian)
        "skill_q_damage": 690,      # Divine Lance
        "skill_q_cooldown": 285,
        "skill_w_damage": 700,      # Sacred Bulwark (AOE)
        "skill_w_cooldown": 345,
        "skill_e_damage": 680,      # Heaven's Charge (AOE)
        "skill_e_cooldown": 375,
        "skill_r_damage": 1240,     # Gate of Dawn (ultimate)
        "skill_r_cooldown": 790,

        "hero_unlock": {
            "name": "Aelyrion",
            "title": "The Divine Guardian",
            "role": "Boss/Steel Maiden Guardian",
            "cost": 3600,
            "hp": 2150,
            "damage": 230,
            "speed": 1.55,
            "range": 90,
            "attack_cooldown": 42,
            "color": (200, 220, 255),
            "color_dark": (40, 50, 80),
            "skill_name": "Divine Lance",
            "skill_desc": "Divine lance + sacred bulwark + heaven's charge + gate of dawn",
            "skill_cooldown": 285,
            "skill_damage": 690,
            "skill_range": 175,
            "description": "Guardian baja dari Level 26",
        },
    },
    "kaervosth": {
        "name": "Kaervosth",
        "title": "The Stormblade Knight",
        "boss_class": "mini",
        "hp": 32500,
        "damage": 250,
        "speed": 1.3,
        "range": 85,             # MELEE (storm greatsword)
        "attack_cooldown": 40,
        "radius": 34,
        "gold_reward": 3650,
        "color": (150, 170, 255),      # storm blue
        "color_dark": (25, 30, 80),
        "ability_cooldown": 285,
        "ability_damage": 700,
        "ability_range": 300,
        "entrance_text": "KAERVOSTH, THE STORMBLADE KNIGHT, RIDES THE THUNDER!",
        "entrance_color": (200, 210, 255),

        # 4 skills (smart AI - stormblade knight)
        "skill_q_damage": 700,      # Storm Slash
        "skill_q_cooldown": 285,
        "skill_w_damage": 710,      # Thunder Ward (AOE)
        "skill_w_cooldown": 350,
        "skill_e_damage": 690,      # Lightning Charge (AOE)
        "skill_e_cooldown": 380,
        "skill_r_damage": 1250,     # Tempest Blade (ultimate)
        "skill_r_cooldown": 795,

        "hero_unlock": {
            "name": "Kaervosth",
            "title": "The Stormblade Knight",
            "role": "Boss/Stormblade Knight",
            "cost": 3650,
            "hp": 2200,
            "damage": 235,
            "speed": 1.6,
            "range": 95,
            "attack_cooldown": 40,
            "color": (150, 170, 255),
            "color_dark": (25, 30, 80),
            "skill_name": "Storm Slash",
            "skill_desc": "Storm slash + thunder ward + lightning charge + tempest blade",
            "skill_cooldown": 285,
            "skill_damage": 700,
            "skill_range": 180,
            "description": "Ksatria badai dari Level 26",
        },
    },
    "morvyssk": {
        "name": "Morvyssk",
        "title": "The Corrosive Ooze",
        "boss_class": "mini",
        "hp": 34000,
        "damage": 240,
        "speed": 1.1,
        "range": 70,             # MELEE (acid ooze)
        "attack_cooldown": 44,
        "radius": 36,
        "gold_reward": 3700,
        "color": (160, 80, 220),       # toxic purple ooze
        "color_dark": (40, 10, 60),
        "ability_cooldown": 290,
        "ability_damage": 710,
        "ability_range": 295,
        "entrance_text": "MORVYSSK, THE CORROSIVE OOZE, DISSOLVES ALL IN ITS PATH!",
        "entrance_color": (210, 150, 255),

        # 4 skills (smart AI - corrosive ooze)
        "skill_q_damage": 710,      # Acid Splash
        "skill_q_cooldown": 290,
        "skill_w_damage": 720,      # Ooze Bloom (AOE)
        "skill_w_cooldown": 350,
        "skill_e_damage": 700,      # Corrosive Surge (AOE)
        "skill_e_cooldown": 380,
        "skill_r_damage": 1260,     # Devouring Mire (ultimate)
        "skill_r_cooldown": 800,

        "hero_unlock": {
            "name": "Morvyssk",
            "title": "The Corrosive Ooze",
            "role": "Boss/Purple Ooze",
            "cost": 3700,
            "hp": 2300,
            "damage": 225,
            "speed": 1.4,
            "range": 80,
            "attack_cooldown": 44,
            "color": (160, 80, 220),
            "color_dark": (40, 10, 60),
            "skill_name": "Acid Splash",
            "skill_desc": "Acid splash + ooze bloom + corrosive surge + devouring mire",
            "skill_cooldown": 290,
            "skill_damage": 710,
            "skill_range": 170,
            "description": "Lumpur asam dari Level 26",
        },
    },
    "kyumirra": {
        "name": "Kyumirra",
        "title": "The Fox Enchantress",
        "boss_class": "mini",
        "hp": 33500,
        "damage": 245,
        "speed": 1.2,
        "range": 270,            # RANGED (fox magic orbs)
        "attack_cooldown": 44,
        "radius": 30,
        "gold_reward": 3750,
        "color": (255, 170, 90),       # fox orange
        "color_dark": (70, 35, 10),
        "ability_cooldown": 285,
        "ability_damage": 715,
        "ability_range": 310,
        "entrance_text": "KYUMIRRA, THE FOX ENCHANTRESS, WEAVES NINE TAILS OF MAGIC!",
        "entrance_color": (255, 210, 150),

        # 4 skills (smart AI - fox enchantress)
        "skill_q_damage": 715,      # Charm Orb
        "skill_q_cooldown": 290,
        "skill_w_damage": 725,      # Nine-Tail Flare (AOE)
        "skill_w_cooldown": 350,
        "skill_e_damage": 705,      # Foxfire Dash (AOE)
        "skill_e_cooldown": 380,
        "skill_r_damage": 1280,     # Spirit Fox (ultimate)
        "skill_r_cooldown": 805,

        # Ranged AI (kite behavior)
        "prefer_distance": 240,
        "min_distance": 120,

        "hero_unlock": {
            "name": "Kyumirra",
            "title": "The Fox Enchantress",
            "role": "Boss/Nine-Tailed Fox",
            "cost": 3750,
            "hp": 2050,
            "damage": 230,
            "speed": 1.55,
            "range": 250,
            "attack_cooldown": 44,
            "color": (255, 170, 90),
            "color_dark": (70, 35, 10),
            "skill_name": "Charm Orb",
            "skill_desc": "Charm orb + nine-tail flare + foxfire dash + spirit fox",
            "skill_cooldown": 290,
            "skill_damage": 715,
            "skill_range": 180,
            "description": "Rubah sembilan ekor dari Level 27",
        },
    },
    "morvakhul": {
        "name": "Morvakhul",
        "title": "The Undying Executioner",
        "boss_class": "mini",
        "hp": 34500,
        "damage": 255,
        "speed": 1.1,
        "range": 85,             # MELEE (cursed executioner axe)
        "attack_cooldown": 46,
        "radius": 36,
        "gold_reward": 3800,
        "color": (110, 200, 170),      # death green
        "color_dark": (20, 55, 40),
        "ability_cooldown": 290,
        "ability_damage": 725,
        "ability_range": 300,
        "entrance_text": "MORVAKHUL, THE UNDYING EXECUTIONER, SWINGS THE CURSED AXE!",
        "entrance_color": (170, 255, 220),

        # 4 skills (smart AI - undying executioner)
        "skill_q_damage": 725,      # Cursed Cleave
        "skill_q_cooldown": 290,
        "skill_w_damage": 735,      # Death's Grasp (AOE)
        "skill_w_cooldown": 355,
        "skill_e_damage": 715,      # Executioner's March (AOE)
        "skill_e_cooldown": 385,
        "skill_r_damage": 1290,     # Undying Judgment (ultimate)
        "skill_r_cooldown": 810,

        "hero_unlock": {
            "name": "Morvakhul",
            "title": "The Undying Executioner",
            "role": "Boss/Undead Executioner",
            "cost": 3800,
            "hp": 2350,
            "damage": 240,
            "speed": 1.45,
            "range": 95,
            "attack_cooldown": 46,
            "color": (110, 200, 170),
            "color_dark": (20, 55, 40),
            "skill_name": "Cursed Cleave",
            "skill_desc": "Cursed cleave + death's grasp + executioner's march + undying judgment",
            "skill_cooldown": 290,
            "skill_damage": 725,
            "skill_range": 180,
            "description": "Algojo abadi dari Level 27",
        },
    },
    "nyxariel": {
        "name": "Nyxariel",
        "title": "The Abyssal Trickster",
        "boss_class": "mini",
        "hp": 33000,
        "damage": 250,
        "speed": 1.35,
        "range": 80,             # MELEE (abyssal trident)
        "attack_cooldown": 40,
        "radius": 32,
        "gold_reward": 3850,
        "color": (80, 200, 230),       # abyssal aqua
        "color_dark": (15, 45, 65),
        "ability_cooldown": 295,
        "ability_damage": 735,
        "ability_range": 305,
        "entrance_text": "NYXARIEL, THE ABYSSAL TRICKSTER, DANCES WITH THE SHARK!",
        "entrance_color": (160, 235, 255),

        # 4 skills (smart AI - abyssal trickster)
        "skill_q_damage": 735,      # Trident Thrust
        "skill_q_cooldown": 295,
        "skill_w_damage": 745,      # Tide's Jest (AOE)
        "skill_w_cooldown": 355,
        "skill_e_damage": 725,      # Bubbling Escape (AOE)
        "skill_e_cooldown": 385,
        "skill_r_damage": 1300,     # Shark Summon (ultimate)
        "skill_r_cooldown": 815,

        "hero_unlock": {
            "name": "Nyxariel",
            "title": "The Abyssal Trickster",
            "role": "Boss/Abyssal Trickster",
            "cost": 3850,
            "hp": 2100,
            "damage": 235,
            "speed": 1.65,
            "range": 90,
            "attack_cooldown": 40,
            "color": (80, 200, 230),
            "color_dark": (15, 45, 65),
            "skill_name": "Trident Thrust",
            "skill_desc": "Trident thrust + tide's jest + bubbling escape + shark summon",
            "skill_cooldown": 295,
            "skill_damage": 735,
            "skill_range": 180,
            "description": "Trikster abyssal dari Level 27",
        },
    },
    "morthyrax": {
        "name": "Morthyrax",
        "title": "The Ever-Rotting Prophet",
        "boss_class": "mini",
        "hp": 35000,
        "damage": 260,
        "speed": 1.15,
        "range": 85,             # MELEE (decay claws)
        "attack_cooldown": 44,
        "radius": 34,
        "gold_reward": 3950,
        "color": (140, 190, 120),      # rot green
        "color_dark": (25, 55, 25),
        "ability_cooldown": 295,
        "ability_damage": 745,
        "ability_range": 305,
        "entrance_text": "MORTHYRAX, THE EVER-ROTTING PROPHET, PREACHES DECAY!",
        "entrance_color": (190, 240, 160),

        # 4 skills (smart AI - rotting prophet)
        "skill_q_damage": 745,      # Rot Claw
        "skill_q_cooldown": 300,
        "skill_w_damage": 755,      # Plague Breath (AOE)
        "skill_w_cooldown": 360,
        "skill_e_damage": 735,      # Decaying March (AOE)
        "skill_e_cooldown": 390,
        "skill_r_damage": 1320,     # Prophet's Blight (ultimate)
        "skill_r_cooldown": 820,

        "hero_unlock": {
            "name": "Morthyrax",
            "title": "The Ever-Rotting Prophet",
            "role": "Boss/Decay Prophet",
            "cost": 3950,
            "hp": 2300,
            "damage": 245,
            "speed": 1.5,
            "range": 95,
            "attack_cooldown": 44,
            "color": (140, 190, 120),
            "color_dark": (25, 55, 25),
            "skill_name": "Rot Claw",
            "skill_desc": "Rot claw + plague breath + decaying march + prophet's blight",
            "skill_cooldown": 300,
            "skill_damage": 745,
            "skill_range": 185,
            "description": "Nabi pembusuk dari Level 28",
        },
    },
    "sanguiveth": {
        "name": "Sanguiveth",
        "title": "The Bloodbound Famine",
        "boss_class": "mini",
        "hp": 34500,
        "damage": 265,
        "speed": 1.2,
        "range": 90,             # MELEE (blood reaper)
        "attack_cooldown": 42,
        "radius": 36,
        "gold_reward": 4000,
        "color": (225, 60, 75),        # blood red
        "color_dark": (60, 8, 15),
        "ability_cooldown": 300,
        "ability_damage": 755,
        "ability_range": 300,
        "entrance_text": "SANGUIVETH, THE BLOODBOUND FAMINE, DEVOURS THE LIVING!",
        "entrance_color": (255, 130, 140),

        # 4 skills (smart AI - bloodbound famine)
        "skill_q_damage": 755,      # Blood Harvest
        "skill_q_cooldown": 300,
        "skill_w_damage": 765,      # Famine's Grasp (AOE)
        "skill_w_cooldown": 360,
        "skill_e_damage": 745,      # Sanguine Leap (AOE)
        "skill_e_cooldown": 390,
        "skill_r_damage": 1330,     # Starvation (ultimate)
        "skill_r_cooldown": 825,

        "hero_unlock": {
            "name": "Sanguiveth",
            "title": "The Bloodbound Famine",
            "role": "Boss/Blood Reaper",
            "cost": 4000,
            "hp": 2350,
            "damage": 250,
            "speed": 1.55,
            "range": 100,
            "attack_cooldown": 42,
            "color": (225, 60, 75),
            "color_dark": (60, 8, 15),
            "skill_name": "Blood Harvest",
            "skill_desc": "Blood harvest + famine's grasp + sanguine leap + starvation",
            "skill_cooldown": 300,
            "skill_damage": 755,
            "skill_range": 185,
            "description": "Paceklik berdarah dari Level 28",
        },
    },
    "xerakhotep": {
        "name": "Xerakhotep",
        "title": "The Sunborne Sovereign",
        "boss_class": "mini",
        "hp": 34000,
        "damage": 255,
        "speed": 1.15,
        "range": 280,            # RANGED (sun magic)
        "attack_cooldown": 46,
        "radius": 32,
        "gold_reward": 4050,
        "color": (255, 200, 80),       # sun gold
        "color_dark": (70, 45, 8),
        "ability_cooldown": 305,
        "ability_damage": 765,
        "ability_range": 315,
        "entrance_text": "XERAKHOTEP, THE SUNBORNE SOVEREIGN, COMMANDS THE DAWN!",
        "entrance_color": (255, 235, 150),

        # 4 skills (smart AI - sunborne sovereign)
        "skill_q_damage": 765,      # Sun Bolt
        "skill_q_cooldown": 305,
        "skill_w_damage": 775,      # Solar Aegis (AOE)
        "skill_w_cooldown": 365,
        "skill_e_damage": 755,      # Sunfire Charge (AOE)
        "skill_e_cooldown": 395,
        "skill_r_damage": 1340,     # Sovereign's Eclipse (ultimate)
        "skill_r_cooldown": 830,

        # Ranged AI (kite behavior)
        "prefer_distance": 250,
        "min_distance": 130,

        "hero_unlock": {
            "name": "Xerakhotep",
            "title": "The Sunborne Sovereign",
            "role": "Boss/Sun Mage",
            "cost": 4050,
            "hp": 2100,
            "damage": 240,
            "speed": 1.5,
            "range": 260,
            "attack_cooldown": 46,
            "color": (255, 200, 80),
            "color_dark": (70, 45, 8),
            "skill_name": "Sun Bolt",
            "skill_desc": "Sun bolt + solar aegis + sunfire charge + sovereign's eclipse",
            "skill_cooldown": 305,
            "skill_damage": 765,
            "skill_range": 190,
            "description": "Penguasa matahari dari Level 28",
        },
    },
    "ignakhor": {
        "name": "Ignakhor",
        "title": "The Furnace-Wrought Berserker",
        "boss_class": "mini",
        "hp": 35500,
        "damage": 265,
        "speed": 1.2,
        "range": 85,             # MELEE (furnace axes)
        "attack_cooldown": 42,
        "radius": 36,
        "gold_reward": 4150,
        "color": (255, 130, 50),       # furnace orange
        "color_dark": (60, 20, 5),
        "ability_cooldown": 300,
        "ability_damage": 770,
        "ability_range": 310,
        "entrance_text": "IGNAKHOR, THE FURNACE-WROUGHT BERSERKER, BURNS WITH RAGE!",
        "entrance_color": (255, 190, 100),

        # 4 skills (smart AI - furnace berserker)
        "skill_q_damage": 770,      # Furnace Cleave
        "skill_q_cooldown": 305,
        "skill_w_damage": 780,      # Molten Rage (AOE)
        "skill_w_cooldown": 365,
        "skill_e_damage": 760,      # Berserker Charge (AOE)
        "skill_e_cooldown": 395,
        "skill_r_damage": 1360,     # Forge's Wrath (ultimate)
        "skill_r_cooldown": 835,

        "hero_unlock": {
            "name": "Ignakhor",
            "title": "The Furnace-Wrought Berserker",
            "role": "Boss/Furnace Berserker",
            "cost": 4100,
            "hp": 2400,
            "damage": 250,
            "speed": 1.55,
            "range": 95,
            "attack_cooldown": 42,
            "color": (255, 130, 50),
            "color_dark": (60, 20, 5),
            "skill_name": "Furnace Cleave",
            "skill_desc": "Furnace cleave + molten rage + berserker charge + forge's wrath",
            "skill_cooldown": 305,
            "skill_damage": 770,
            "skill_range": 190,
            "description": "Berserker tempa dari Level 29",
        },
    },
    "kazureth": {
        "name": "Kazureth",
        "title": "The Thunder Wielder",
        "boss_class": "mini",
        "hp": 35000,
        "damage": 260,
        "speed": 1.35,
        "range": 80,             # MELEE (lightning katana)
        "attack_cooldown": 40,
        "radius": 34,
        "gold_reward": 4200,
        "color": (255, 215, 80),       # thunder gold
        "color_dark": (70, 50, 8),
        "ability_cooldown": 305,
        "ability_damage": 780,
        "ability_range": 305,
        "entrance_text": "KAZURETH, THE THUNDER WIELDER, STRIKES WITH HONOIKAZUCHI!",
        "entrance_color": (255, 240, 150),

        # 4 skills (smart AI - thunder wielder)
        "skill_q_damage": 780,      # Thunderclap Flash
        "skill_q_cooldown": 305,
        "skill_w_damage": 790,      # Lightning Cloak (AOE)
        "skill_w_cooldown": 365,
        "skill_e_damage": 770,      # Distant Thunder (AOE)
        "skill_e_cooldown": 395,
        "skill_r_damage": 1370,     # Honoikazuchi (ultimate)
        "skill_r_cooldown": 840,

        "hero_unlock": {
            "name": "Kazureth",
            "title": "The Thunder Wielder",
            "role": "Boss/Thunder Samurai",
            "cost": 4200,
            "hp": 2250,
            "damage": 245,
            "speed": 1.65,
            "range": 90,
            "attack_cooldown": 40,
            "color": (255, 215, 80),
            "color_dark": (70, 50, 8),
            "skill_name": "Thunderclap Flash",
            "skill_desc": "Thunderclap flash + lightning cloak + distant thunder + honoikazuchi",
            "skill_cooldown": 305,
            "skill_damage": 780,
            "skill_range": 185,
            "description": "Pendekar petir dari Level 29",
        },
    },
    "sethrakhar": {
        "name": "Seth'rakhaar",
        "title": "The Sunforged Butcher",
        "boss_class": "mini",
        "hp": 36000,
        "damage": 270,
        "speed": 1.1,
        "range": 90,             # MELEE (sunforged cleaver)
        "attack_cooldown": 46,
        "radius": 38,
        "gold_reward": 4250,
        "color": (255, 175, 60),       # sunforged gold
        "color_dark": (75, 40, 8),
        "ability_cooldown": 310,
        "ability_damage": 790,
        "ability_range": 300,
        "entrance_text": "SETH'RAKHAAR, THE SUNFORGED BUTCHER, CARVES IN DAYLIGHT!",
        "entrance_color": (255, 215, 130),

        # 4 skills (smart AI - sunforged butcher)
        "skill_q_damage": 790,      # Sunforged Chop
        "skill_q_cooldown": 310,
        "skill_w_damage": 800,      # Butcher's Fury (AOE)
        "skill_w_cooldown": 370,
        "skill_e_damage": 780,      # Blood Rage March (AOE)
        "skill_e_cooldown": 400,
        "skill_r_damage": 1380,     # Sunforged Judgment (ultimate)
        "skill_r_cooldown": 845,

        "hero_unlock": {
            "name": "Seth'rakhaar",
            "title": "The Sunforged Butcher",
            "role": "Boss/Sunforged Butcher",
            "cost": 4250,
            "hp": 2450,
            "damage": 255,
            "speed": 1.45,
            "range": 100,
            "attack_cooldown": 46,
            "color": (255, 175, 60),
            "color_dark": (75, 40, 8),
            "skill_name": "Sunforged Chop",
            "skill_desc": "Sunforged chop + butcher's fury + blood rage march + sunforged judgment",
            "skill_cooldown": 310,
            "skill_damage": 790,
            "skill_range": 190,
            "description": "Tukang daging matahari dari Level 29",
        },
    },
    "kaelvyrn": {
        "name": "Kaelvyrn",
        "title": "The Gilded Marauder",
        "boss_class": "mini",
        "hp": 36500,
        "damage": 270,
        "speed": 1.3,
        "range": 85,             # MELEE (gilded twin blades)
        "attack_cooldown": 40,
        "radius": 34,
        "gold_reward": 4350,
        "color": (240, 200, 90),       # gilded gold
        "color_dark": (70, 50, 10),
        "ability_cooldown": 310,
        "ability_damage": 795,
        "ability_range": 310,
        "entrance_text": "KAELVYRN, THE GILDED MARAUDER, PLUNDERS THE GOLDEN HORDE!",
        "entrance_color": (255, 230, 150),

        # 4 skills (smart AI - gilded marauder)
        "skill_q_damage": 795,      # Gilded Slash
        "skill_q_cooldown": 315,
        "skill_w_damage": 805,      # Treasure Storm (AOE)
        "skill_w_cooldown": 375,
        "skill_e_damage": 785,      # Marauder's Dash (AOE)
        "skill_e_cooldown": 405,
        "skill_r_damage": 1400,     # Golden Plunder (ultimate)
        "skill_r_cooldown": 850,

        "hero_unlock": {
            "name": "Kaelvyrn",
            "title": "The Gilded Marauder",
            "role": "Boss/Gilded Marauder",
            "cost": 4300,
            "hp": 2450,
            "damage": 255,
            "speed": 1.6,
            "range": 95,
            "attack_cooldown": 40,
            "color": (240, 200, 90),
            "color_dark": (70, 50, 10),
            "skill_name": "Gilded Slash",
            "skill_desc": "Gilded slash + treasure storm + marauder's dash + golden plunder",
            "skill_cooldown": 315,
            "skill_damage": 795,
            "skill_range": 195,
            "description": "Perampok emas dari Level 30",
        },
    },
    "thorvin": {
        "name": "Thorvin",
        "title": "The Ironbound Warden",
        "boss_class": "mini",
        "hp": 37000,
        "damage": 265,
        "speed": 1.05,
        "range": 90,             # MELEE (ironbound hammer)
        "attack_cooldown": 48,
        "radius": 38,
        "gold_reward": 4400,
        "color": (120, 130, 145),      # iron grey
        "color_dark": (15, 18, 22),
        "ability_cooldown": 315,
        "ability_damage": 805,
        "ability_range": 300,
        "entrance_text": "THORVIN, THE IRONBOUND WARDEN, STANDS UNBROKEN!",
        "entrance_color": (190, 205, 220),

        # 4 skills (smart AI - ironbound warden)
        "skill_q_damage": 805,      # Ironbound Slam
        "skill_q_cooldown": 315,
        "skill_w_damage": 815,      # Warden's Bulwark (AOE)
        "skill_w_cooldown": 375,
        "skill_e_damage": 795,      # Fortress March (AOE)
        "skill_e_cooldown": 405,
        "skill_r_damage": 1410,     # Unbreakable Oath (ultimate)
        "skill_r_cooldown": 855,

        "hero_unlock": {
            "name": "Thorvin",
            "title": "The Ironbound Warden",
            "role": "Boss/Ironbound Warden",
            "cost": 4350,
            "hp": 2600,
            "damage": 250,
            "speed": 1.4,
            "range": 100,
            "attack_cooldown": 48,
            "color": (120, 130, 145),
            "color_dark": (15, 18, 22),
            "skill_name": "Ironbound Slam",
            "skill_desc": "Ironbound slam + warden's bulwark + fortress march + unbreakable oath",
            "skill_cooldown": 315,
            "skill_damage": 805,
            "skill_range": 195,
            "description": "Penjaga besi dari Level 30",
        },
    },
    "xaerissa": {
        "name": "Xaerissa",
        "title": "The Weaver of Crimson Silk",
        "boss_class": "mini",
        "hp": 36000,
        "damage": 275,
        "speed": 1.2,
        "range": 290,            # RANGED (crimson silk web)
        "attack_cooldown": 44,
        "radius": 32,
        "gold_reward": 4450,
        "color": (225, 70, 90),        # crimson silk
        "color_dark": (55, 10, 18),
        "ability_cooldown": 320,
        "ability_damage": 815,
        "ability_range": 320,
        "entrance_text": "XAERISSA, THE WEAVER OF CRIMSON SILK, SPINS A BLOOD WEB!",
        "entrance_color": (255, 140, 160),

        # 4 skills (smart AI - crimson weaver)
        "skill_q_damage": 815,      # Silk Thread
        "skill_q_cooldown": 320,
        "skill_w_damage": 825,      # Crimson Cocoon (AOE)
        "skill_w_cooldown": 380,
        "skill_e_damage": 805,      # Web Weaver (AOE)
        "skill_e_cooldown": 410,
        "skill_r_damage": 1420,     # Arachnid Queen (ultimate)
        "skill_r_cooldown": 860,

        # Ranged AI (kite behavior)
        "prefer_distance": 260,
        "min_distance": 140,

        "hero_unlock": {
            "name": "Xaerissa",
            "title": "The Weaver of Crimson Silk",
            "role": "Boss/Crimson Weaver",
            "cost": 4400,
            "hp": 2300,
            "damage": 260,
            "speed": 1.5,
            "range": 270,
            "attack_cooldown": 44,
            "color": (225, 70, 90),
            "color_dark": (55, 10, 18),
            "skill_name": "Silk Thread",
            "skill_desc": "Silk thread + crimson cocoon + web weaver + arachnid queen",
            "skill_cooldown": 320,
            "skill_damage": 815,
            "skill_range": 200,
            "description": "Penenun sutra darah dari Level 30",
        },
    },
    "celwynn": {
        "name": "Celwynn",
        "title": "The Star Caretaker",
        "boss_class": "mini",
        "hp": 37000,
        "damage": 275,
        "speed": 1.15,
        "range": 290,            # RANGED (star magic)
        "attack_cooldown": 46,
        "radius": 32,
        "gold_reward": 4550,
        "color": (160, 200, 255),      # star blue
        "color_dark": (25, 40, 80),
        "ability_cooldown": 320,
        "ability_damage": 830,
        "ability_range": 325,
        "entrance_text": "CELWYNN, THE STAR CARETAKER, TENDS THE CELESTIAL FLAME!",
        "entrance_color": (210, 230, 255),

        # 4 skills (smart AI - star caretaker)
        "skill_q_damage": 830,      # Star Bolt
        "skill_q_cooldown": 320,
        "skill_w_damage": 840,      # Constellation Veil (AOE)
        "skill_w_cooldown": 380,
        "skill_e_damage": 820,      # Meteor Shower (AOE)
        "skill_e_cooldown": 410,
        "skill_r_damage": 1450,     # Celestial Flame (ultimate)
        "skill_r_cooldown": 865,

        # Ranged AI (kite behavior)
        "prefer_distance": 260,
        "min_distance": 140,

        "hero_unlock": {
            "name": "Celwynn",
            "title": "The Star Caretaker",
            "role": "Boss/Star Mage",
            "cost": 4500,
            "hp": 2350,
            "damage": 260,
            "speed": 1.5,
            "range": 270,
            "attack_cooldown": 46,
            "color": (160, 200, 255),
            "color_dark": (25, 40, 80),
            "skill_name": "Star Bolt",
            "skill_desc": "Star bolt + constellation veil + meteor shower + celestial flame",
            "skill_cooldown": 320,
            "skill_damage": 830,
            "skill_range": 205,
            "description": "Penjaga bintang dari Level 31",
        },
    },
    "rynvara": {
        "name": "Rynvara",
        "title": "The Wild Onslaught",
        "boss_class": "mini",
        "hp": 38000,
        "damage": 285,
        "speed": 1.3,
        "range": 85,             # MELEE (primal claws)
        "attack_cooldown": 40,
        "radius": 36,
        "gold_reward": 4600,
        "color": (255, 140, 60),       # wild fire
        "color_dark": (70, 30, 10),
        "ability_cooldown": 325,
        "ability_damage": 845,
        "ability_range": 310,
        "entrance_text": "RYNVARA, THE WILD ONSLAUGHT, STORMS WITH PRIMAL FURY!",
        "entrance_color": (255, 200, 130),

        # 4 skills (smart AI - wild onslaught)
        "skill_q_damage": 845,      # Primal Rend
        "skill_q_cooldown": 325,
        "skill_w_damage": 855,      # Onslaught's Roar (AOE)
        "skill_w_cooldown": 385,
        "skill_e_damage": 835,      # Wild Stampede (AOE)
        "skill_e_cooldown": 415,
        "skill_r_damage": 1460,     # Untamed Wrath (ultimate)
        "skill_r_cooldown": 870,

        "hero_unlock": {
            "name": "Rynvara",
            "title": "The Wild Onslaught",
            "role": "Boss/Primal Beast",
            "cost": 4550,
            "hp": 2500,
            "damage": 270,
            "speed": 1.6,
            "range": 95,
            "attack_cooldown": 40,
            "color": (255, 140, 60),
            "color_dark": (70, 30, 10),
            "skill_name": "Primal Rend",
            "skill_desc": "Primal rend + onslaught's roar + wild stampede + untamed wrath",
            "skill_cooldown": 325,
            "skill_damage": 845,
            "skill_range": 200,
            "description": "Badai liar dari Level 31",
        },
    },
    "syrindra": {
        "name": "Syrindra",
        "title": "The Dark Sovereign",
        "boss_class": "mini",
        "hp": 37500,
        "damage": 280,
        "speed": 1.1,
        "range": 295,            # RANGED (dark magic)
        "attack_cooldown": 48,
        "radius": 34,
        "gold_reward": 4650,
        "color": (140, 90, 220),       # dark violet
        "color_dark": (25, 12, 50),
        "ability_cooldown": 330,
        "ability_damage": 855,
        "ability_range": 330,
        "entrance_text": "SYRINDRA, THE DARK SOVEREIGN, RULES THE SHADOW REALM!",
        "entrance_color": (200, 160, 255),

        # 4 skills (smart AI - dark sovereign)
        "skill_q_damage": 855,      # Dark Bolt
        "skill_q_cooldown": 330,
        "skill_w_damage": 865,      # Sovereign's Wrath (AOE)
        "skill_w_cooldown": 390,
        "skill_e_damage": 845,      # Shadow Court (AOE)
        "skill_e_cooldown": 420,
        "skill_r_damage": 1470,     # Dark Ascension (ultimate)
        "skill_r_cooldown": 875,

        # Ranged AI (kite behavior)
        "prefer_distance": 265,
        "min_distance": 145,

        "hero_unlock": {
            "name": "Syrindra",
            "title": "The Dark Sovereign",
            "role": "Boss/Dark Mage",
            "cost": 4600,
            "hp": 2400,
            "damage": 265,
            "speed": 1.45,
            "range": 275,
            "attack_cooldown": 48,
            "color": (140, 90, 220),
            "color_dark": (25, 12, 50),
            "skill_name": "Dark Bolt",
            "skill_desc": "Dark bolt + sovereign's wrath + shadow court + dark ascension",
            "skill_cooldown": 330,
            "skill_damage": 855,
            "skill_range": 210,
            "description": "Penguasa kegelapan dari Level 31",
        },
    },
    "ghrakmaal": {
        "name": "Ghrakmaal",
        "title": "The Colossus of Sundered Earth",
        "boss_class": "mini",
        "hp": 39000,
        "damage": 290,
        "speed": 1.0,
        "range": 90,             # MELEE (earth-shattering fists)
        "attack_cooldown": 48,
        "radius": 40,
        "gold_reward": 4750,
        "color": (150, 120, 85),       # earth brown
        "color_dark": (40, 28, 15),
        "ability_cooldown": 330,
        "ability_damage": 860,
        "ability_range": 310,
        "entrance_text": "GHRAKMAAL, THE COLOSSUS OF SUNDERED EARTH, TREMBLES THE GROUND!",
        "entrance_color": (210, 185, 150),

        # 4 skills (smart AI - earth colossus)
        "skill_q_damage": 860,      # Earth Shatter
        "skill_q_cooldown": 330,
        "skill_w_damage": 870,      # Sundered Ground (AOE)
        "skill_w_cooldown": 390,
        "skill_e_damage": 850,      # Colossal Charge (AOE)
        "skill_e_cooldown": 420,
        "skill_r_damage": 1500,     # Worldbreaker (ultimate)
        "skill_r_cooldown": 885,

        "hero_unlock": {
            "name": "Ghrakmaal",
            "title": "The Colossus of Sundered Earth",
            "role": "Boss/Earth Colossus",
            "cost": 4700,
            "hp": 2700,
            "damage": 275,
            "speed": 1.35,
            "range": 100,
            "attack_cooldown": 48,
            "color": (150, 120, 85),
            "color_dark": (40, 28, 15),
            "skill_name": "Earth Shatter",
            "skill_desc": "Earth shatter + sundered ground + colossal charge + worldbreaker",
            "skill_cooldown": 330,
            "skill_damage": 860,
            "skill_range": 205,
            "description": "Kolosus bumi dari Level 32",
        },
    },
    "selunara": {
        "name": "Selunara",
        "title": "The Moonbound Huntress",
        "boss_class": "mini",
        "hp": 38000,
        "damage": 285,
        "speed": 1.25,
        "range": 300,            # RANGED (lunar arrows)
        "attack_cooldown": 44,
        "radius": 32,
        "gold_reward": 4800,
        "color": (200, 210, 255),      # moon silver
        "color_dark": (30, 35, 70),
        "ability_cooldown": 335,
        "ability_damage": 870,
        "ability_range": 335,
        "entrance_text": "SELUNARA, THE MOONBOUND HUNTRESS, HUNTS BENEATH THE CRESCENT!",
        "entrance_color": (230, 235, 255),

        # 4 skills (smart AI - moonbound huntress)
        "skill_q_damage": 870,      # Moon Arrow
        "skill_q_cooldown": 335,
        "skill_w_damage": 880,      # Lunar Halo (AOE)
        "skill_w_cooldown": 395,
        "skill_e_damage": 860,      # Crescent Dash (AOE)
        "skill_e_cooldown": 425,
        "skill_r_damage": 1510,     # Eclipse Barrage (ultimate)
        "skill_r_cooldown": 890,

        # Ranged AI (kite behavior)
        "prefer_distance": 270,
        "min_distance": 150,

        "hero_unlock": {
            "name": "Selunara",
            "title": "The Moonbound Huntress",
            "role": "Boss/Moon Archer",
            "cost": 4750,
            "hp": 2450,
            "damage": 270,
            "speed": 1.55,
            "range": 280,
            "attack_cooldown": 44,
            "color": (200, 210, 255),
            "color_dark": (30, 35, 70),
            "skill_name": "Moon Arrow",
            "skill_desc": "Moon arrow + lunar halo + crescent dash + eclipse barrage",
            "skill_cooldown": 335,
            "skill_damage": 870,
            "skill_range": 215,
            "description": "Pemburu bulan dari Level 32",
        },
    },
    "vessyra": {
        "name": "Vessyra",
        "title": "The Gorgon Queen",
        "boss_class": "mini",
        "hp": 38500,
        "damage": 280,
        "speed": 1.1,
        "range": 285,            # RANGED (petrify gaze)
        "attack_cooldown": 48,
        "radius": 34,
        "gold_reward": 4850,
        "color": (120, 190, 120),      # gorgon green
        "color_dark": (20, 50, 25),
        "ability_cooldown": 340,
        "ability_damage": 880,
        "ability_range": 330,
        "entrance_text": "VESSYRA, THE GORGON QUEEN, TURNS HEROES TO STONE!",
        "entrance_color": (180, 240, 180),

        # 4 skills (smart AI - gorgon queen)
        "skill_q_damage": 880,      # Serpent Bite
        "skill_q_cooldown": 340,
        "skill_w_damage": 890,      # Petrify Gaze (AOE)
        "skill_w_cooldown": 400,
        "skill_e_damage": 870,      # Snake Swarm (AOE)
        "skill_e_cooldown": 430,
        "skill_r_damage": 1520,     # Medusa's Wrath (ultimate)
        "skill_r_cooldown": 895,

        # Ranged AI (kite behavior)
        "prefer_distance": 255,
        "min_distance": 135,

        "hero_unlock": {
            "name": "Vessyra",
            "title": "The Gorgon Queen",
            "role": "Boss/Gorgon Queen",
            "cost": 4800,
            "hp": 2400,
            "damage": 265,
            "speed": 1.45,
            "range": 265,
            "attack_cooldown": 48,
            "color": (120, 190, 120),
            "color_dark": (20, 50, 25),
            "skill_name": "Serpent Bite",
            "skill_desc": "Serpent bite + petrify gaze + snake swarm + medusa's wrath",
            "skill_cooldown": 340,
            "skill_damage": 880,
            "skill_range": 210,
            "description": "Ratu gorgon dari Level 32",
        },
    },
    "rakzhan": {
        "name": "Rakzhan",
        "title": "The Emberfist Prodigy",
        "boss_class": "mini",
        "hp": 39500,
        "damage": 295,
        "speed": 1.3,
        "range": 80,             # MELEE (ember fists)
        "attack_cooldown": 40,
        "radius": 34,
        "gold_reward": 4950,
        "color": (255, 150, 60),       # ember orange
        "color_dark": (70, 30, 8),
        "ability_cooldown": 340,
        "ability_damage": 890,
        "ability_range": 315,
        "entrance_text": "RAKZHAN, THE EMBERFIST PRODIGY, IGNITES THE ARENA!",
        "entrance_color": (255, 205, 130),

        # 4 skills (smart AI - emberfist prodigy)
        "skill_q_damage": 890,      # Ember Jab
        "skill_q_cooldown": 340,
        "skill_w_damage": 900,      # Cinder Storm (AOE)
        "skill_w_cooldown": 400,
        "skill_e_damage": 880,      # Blazing Step (AOE)
        "skill_e_cooldown": 430,
        "skill_r_damage": 1540,     # Prodigy's Inferno (ultimate)
        "skill_r_cooldown": 900,

        "hero_unlock": {
            "name": "Rakzhan",
            "title": "The Emberfist Prodigy",
            "role": "Boss/Emberfist Fighter",
            "cost": 4900,
            "hp": 2500,
            "damage": 280,
            "speed": 1.6,
            "range": 90,
            "attack_cooldown": 40,
            "color": (255, 150, 60),
            "color_dark": (70, 30, 8),
            "skill_name": "Ember Jab",
            "skill_desc": "Ember jab + cinder storm + blazing step + prodigy's inferno",
            "skill_cooldown": 340,
            "skill_damage": 890,
            "skill_range": 210,
            "description": "Petarung bara dari Level 33",
        },
    },
    "sirakzan": {
        "name": "Sirakzan",
        "title": "The Blade Rolling Duelist",
        "boss_class": "mini",
        "hp": 39000,
        "damage": 300,
        "speed": 1.4,
        "range": 85,             # MELEE (blade roll)
        "attack_cooldown": 38,
        "radius": 32,
        "gold_reward": 5000,
        "color": (160, 130, 255),      # duelist violet
        "color_dark": (40, 25, 90),
        "ability_cooldown": 345,
        "ability_damage": 900,
        "ability_range": 310,
        "entrance_text": "SIRAKZAN, THE BLADE ROLLING DUELIST, SPINS TO VICTORY!",
        "entrance_color": (215, 195, 255),

        # 4 skills (smart AI - blade duelist)
        "skill_q_damage": 900,      # Blade Roll
        "skill_q_cooldown": 345,
        "skill_w_damage": 910,      # Duelist's Flourish (AOE)
        "skill_w_cooldown": 405,
        "skill_e_damage": 890,      # Spin Slash (AOE)
        "skill_e_cooldown": 435,
        "skill_r_damage": 1550,     # Endless Waltz (ultimate)
        "skill_r_cooldown": 905,

        "hero_unlock": {
            "name": "Sirakzan",
            "title": "The Blade Rolling Duelist",
            "role": "Boss/Blade Duelist",
            "cost": 4950,
            "hp": 2450,
            "damage": 285,
            "speed": 1.7,
            "range": 95,
            "attack_cooldown": 38,
            "color": (160, 130, 255),
            "color_dark": (40, 25, 90),
            "skill_name": "Blade Roll",
            "skill_desc": "Blade roll + duelist's flourish + spin slash + endless waltz",
            "skill_cooldown": 345,
            "skill_damage": 900,
            "skill_range": 210,
            "description": "Duelis berputar dari Level 33",
        },
    },
    "valekris": {
        "name": "Valekris",
        "title": "The Vengeful Wraith",
        "boss_class": "mini",
        "hp": 40000,
        "damage": 290,
        "speed": 1.15,
        "range": 300,            # RANGED (cyan spectre magic)
        "attack_cooldown": 46,
        "radius": 34,
        "gold_reward": 5050,
        "color": (120, 230, 245),      # cyan spectre
        "color_dark": (10, 50, 65),
        "ability_cooldown": 350,
        "ability_damage": 910,
        "ability_range": 340,
        "entrance_text": "VALEKRIS, THE VENGEFUL WRAITH, HAUNTS THE LIVING!",
        "entrance_color": (190, 250, 255),

        # 4 skills (smart AI - vengeful wraith)
        "skill_q_damage": 910,      # Wraith Bolt
        "skill_q_cooldown": 350,
        "skill_w_damage": 920,      # Vengeful Shade (AOE)
        "skill_w_cooldown": 410,
        "skill_e_damage": 900,      # Spectral Veil (AOE)
        "skill_e_cooldown": 440,
        "skill_r_damage": 1560,     # Haunting Revenge (ultimate)
        "skill_r_cooldown": 910,

        # Ranged AI (kite behavior)
        "prefer_distance": 270,
        "min_distance": 150,

        "hero_unlock": {
            "name": "Valekris",
            "title": "The Vengeful Wraith",
            "role": "Boss/Cyan Wraith",
            "cost": 5000,
            "hp": 2350,
            "damage": 275,
            "speed": 1.5,
            "range": 280,
            "attack_cooldown": 46,
            "color": (120, 230, 245),
            "color_dark": (10, 50, 65),
            "skill_name": "Wraith Bolt",
            "skill_desc": "Wraith bolt + vengeful shade + spectral veil + haunting revenge",
            "skill_cooldown": 350,
            "skill_damage": 910,
            "skill_range": 215,
            "description": "Hantu pendendam dari Level 33",
        },
    },
    "infrakzaar": {
        "name": "Infrakzaar",
        "title": "The Emberflesh Pyromancer",
        "boss_class": "mini",
        "hp": 40500,
        "damage": 300,
        "speed": 1.15,
        "range": 305,            # RANGED (ember fire magic)
        "attack_cooldown": 46,
        "radius": 34,
        "gold_reward": 5150,
        "color": (255, 120, 50),       # ember orange
        "color_dark": (70, 25, 8),
        "ability_cooldown": 350,
        "ability_damage": 920,
        "ability_range": 340,
        "entrance_text": "INFRAKZAAR, THE EMBERFLESH PYROMANCER, BURNS THE FLESH!",
        "entrance_color": (255, 185, 120),

        # 4 skills (smart AI - emberflesh pyromancer)
        "skill_q_damage": 920,      # Ember Lance
        "skill_q_cooldown": 350,
        "skill_w_damage": 930,      # Fleshfire Ring (AOE)
        "skill_w_cooldown": 410,
        "skill_e_damage": 910,      # Scorch Step (AOE)
        "skill_e_cooldown": 440,
        "skill_r_damage": 1580,     # Cataclysm Meteor (ultimate)
        "skill_r_cooldown": 915,

        # Ranged AI (kite behavior)
        "prefer_distance": 275,
        "min_distance": 155,

        "hero_unlock": {
            "name": "Infrakzaar",
            "title": "The Emberflesh Pyromancer",
            "role": "Boss/Ember Pyromancer",
            "cost": 5100,
            "hp": 2550,
            "damage": 285,
            "speed": 1.5,
            "range": 285,
            "attack_cooldown": 46,
            "color": (255, 120, 50),
            "color_dark": (70, 25, 8),
            "skill_name": "Ember Lance",
            "skill_desc": "Ember lance + fleshfire ring + scorch step + cataclysm meteor",
            "skill_cooldown": 350,
            "skill_damage": 920,
            "skill_range": 220,
            "description": "Pyromancer bara dari Level 34",
        },
    },
    "xarnathul": {
        "name": "Xarnathul",
        "title": "The Deathsinger",
        "boss_class": "mini",
        "hp": 40000,
        "damage": 295,
        "speed": 1.1,
        "range": 310,            # RANGED (death song magic)
        "attack_cooldown": 48,
        "radius": 34,
        "gold_reward": 5200,
        "color": (170, 110, 230),      # soul violet
        "color_dark": (35, 15, 60),
        "ability_cooldown": 355,
        "ability_damage": 930,
        "ability_range": 345,
        "entrance_text": "XARNATHUL THE DEATHSINGER, SINGS THE FINAL HYMN!",
        "entrance_color": (220, 180, 255),

        # 4 skills (smart AI - deathsinger)
        "skill_q_damage": 930,      # Death Note
        "skill_q_cooldown": 355,
        "skill_w_damage": 940,      # Requiem Ring (AOE)
        "skill_w_cooldown": 415,
        "skill_e_damage": 920,      # Soul Dirge (AOE)
        "skill_e_cooldown": 445,
        "skill_r_damage": 1590,     # Finale of Ruin (ultimate)
        "skill_r_cooldown": 920,

        # Ranged AI (kite behavior)
        "prefer_distance": 280,
        "min_distance": 160,

        "hero_unlock": {
            "name": "Xarnathul",
            "title": "The Deathsinger",
            "role": "Boss/Deathsinger",
            "cost": 5150,
            "hp": 2500,
            "damage": 280,
            "speed": 1.45,
            "range": 290,
            "attack_cooldown": 48,
            "color": (170, 110, 230),
            "color_dark": (35, 15, 60),
            "skill_name": "Death Note",
            "skill_desc": "Death note + requiem ring + soul dirge + finale of ruin",
            "skill_cooldown": 355,
            "skill_damage": 930,
            "skill_range": 225,
            "description": "Penyanyi kematian dari Level 34",
        },
    },
    "zhyrakaan": {
        "name": "Zhyrakaan",
        "title": "The Phantomweave Lancer",
        "boss_class": "mini",
        "hp": 41000,
        "damage": 305,
        "speed": 1.35,
        "range": 90,             # MELEE (phantom lance)
        "attack_cooldown": 40,
        "radius": 36,
        "gold_reward": 5250,
        "color": (140, 220, 255),      # phantom cyan
        "color_dark": (20, 55, 80),
        "ability_cooldown": 360,
        "ability_damage": 940,
        "ability_range": 320,
        "entrance_text": "ZHYRAKAAN, THE PHANTOMWEAVE LANCER, PIERCES THE VEIL!",
        "entrance_color": (210, 245, 255),

        # 4 skills (smart AI - phantomweave lancer)
        "skill_q_damage": 940,      # Phantom Thrust
        "skill_q_cooldown": 360,
        "skill_w_damage": 950,      # Weave Step (AOE)
        "skill_w_cooldown": 420,
        "skill_e_damage": 930,      # Spectral Spiral (AOE)
        "skill_e_cooldown": 450,
        "skill_r_damage": 1600,     # Phantomweave Storm (ultimate)
        "skill_r_cooldown": 925,

        "hero_unlock": {
            "name": "Zhyrakaan",
            "title": "The Phantomweave Lancer",
            "role": "Boss/Phantom Lancer",
            "cost": 5200,
            "hp": 2600,
            "damage": 290,
            "speed": 1.65,
            "range": 100,
            "attack_cooldown": 40,
            "color": (140, 220, 255),
            "color_dark": (20, 55, 80),
            "skill_name": "Phantom Thrust",
            "skill_desc": "Phantom thrust + weave step + spectral spiral + phantomweave storm",
            "skill_cooldown": 360,
            "skill_damage": 940,
            "skill_range": 220,
            "description": "Penombak hantu dari Level 34",
        },
    },
    "kaerissa": {
        "name": "Kaerissa",
        "title": "The Bloodwhirl",
        "boss_class": "mini",
        "hp": 41500,
        "damage": 310,
        "speed": 1.45,
        "range": 80,             # MELEE (blood daggers)
        "attack_cooldown": 36,
        "radius": 32,
        "gold_reward": 5350,
        "color": (230, 60, 90),        # blood red
        "color_dark": (60, 10, 20),
        "ability_cooldown": 360,
        "ability_damage": 950,
        "ability_range": 330,
        "entrance_text": "KAERISSA THE BLOODWHIRL, SPINS A DANCE OF DEATH!",
        "entrance_color": (255, 140, 160),

        # 4 skills (smart AI - bloodwhirl)
        "skill_q_damage": 950,      # Blood Stab
        "skill_q_cooldown": 360,
        "skill_w_damage": 960,      # Whirlwind Blood (AOE)
        "skill_w_cooldown": 420,
        "skill_e_damage": 940,      # Crimson Step (AOE)
        "skill_e_cooldown": 450,
        "skill_r_damage": 1620,     # Bloodwhirl Finale (ultimate)
        "skill_r_cooldown": 930,

        "hero_unlock": {
            "name": "Kaerissa",
            "title": "The Bloodwhirl",
            "role": "Boss/Blood Assassin",
            "cost": 5300,
            "hp": 2600,
            "damage": 295,
            "speed": 1.75,
            "range": 90,
            "attack_cooldown": 36,
            "color": (230, 60, 90),
            "color_dark": (60, 10, 20),
            "skill_name": "Blood Stab",
            "skill_desc": "Blood stab + whirlwind blood + crimson step + bloodwhirl finale",
            "skill_cooldown": 360,
            "skill_damage": 950,
            "skill_range": 225,
            "description": "Pusaran darah dari Level 35",
        },
    },
    "thorgaruk": {
        "name": "Thorgaruk",
        "title": "The Skyhorn",
        "boss_class": "mini",
        "hp": 42000,
        "damage": 315,
        "speed": 1.15,
        "range": 90,             # MELEE (storm axe)
        "attack_cooldown": 46,
        "radius": 40,
        "gold_reward": 5400,
        "color": (170, 200, 255),      # sky blue
        "color_dark": (30, 45, 90),
        "ability_cooldown": 365,
        "ability_damage": 960,
        "ability_range": 325,
        "entrance_text": "THORGARUK THE SKYHORN, CALLS THE STORM FROM ABOVE!",
        "entrance_color": (215, 230, 255),

        # 4 skills (smart AI - skyhorn)
        "skill_q_damage": 960,      # Skyfall Axe
        "skill_q_cooldown": 365,
        "skill_w_damage": 970,      # Thunder Horn (AOE)
        "skill_w_cooldown": 425,
        "skill_e_damage": 950,      # Storm Skewer (AOE)
        "skill_e_cooldown": 455,
        "skill_r_damage": 1630,     # Skyhorn's Judgment (ultimate)
        "skill_r_cooldown": 935,

        "hero_unlock": {
            "name": "Thorgaruk",
            "title": "The Skyhorn",
            "role": "Boss/Skyhorn Warrior",
            "cost": 5350,
            "hp": 2800,
            "damage": 300,
            "speed": 1.45,
            "range": 100,
            "attack_cooldown": 46,
            "color": (170, 200, 255),
            "color_dark": (30, 45, 90),
            "skill_name": "Skyfall Axe",
            "skill_desc": "Skyfall axe + thunder horn + storm skewer + skyhorn's judgment",
            "skill_cooldown": 365,
            "skill_damage": 960,
            "skill_range": 230,
            "description": "Tanduk langit dari Level 35",
        },
    },
    "zorathiel": {
        "name": "Zorathiel",
        "title": "The Arcanist",
        "boss_class": "mini",
        "hp": 41000,
        "damage": 305,
        "speed": 1.15,
        "range": 315,            # RANGED (arcane magic)
        "attack_cooldown": 46,
        "radius": 34,
        "gold_reward": 5450,
        "color": (160, 120, 255),      # arcane violet
        "color_dark": (35, 20, 80),
        "ability_cooldown": 370,
        "ability_damage": 970,
        "ability_range": 350,
        "entrance_text": "ZORATHIEL THE ARCANIST, WEAVES THE FORBIDDEN WEAVE!",
        "entrance_color": (215, 195, 255),

        # 4 skills (smart AI - arcanist)
        "skill_q_damage": 970,      # Arcane Bolt
        "skill_q_cooldown": 370,
        "skill_w_damage": 980,      # Weave Prison (AOE)
        "skill_w_cooldown": 430,
        "skill_e_damage": 960,      # Arcane Travel (AOE)
        "skill_e_cooldown": 460,
        "skill_r_damage": 1640,     # Grand Arcanum (ultimate)
        "skill_r_cooldown": 940,

        # Ranged AI (kite behavior)
        "prefer_distance": 285,
        "min_distance": 165,

        "hero_unlock": {
            "name": "Zorathiel",
            "title": "The Arcanist",
            "role": "Boss/Arcane Mage",
            "cost": 5400,
            "hp": 2600,
            "damage": 290,
            "speed": 1.5,
            "range": 295,
            "attack_cooldown": 46,
            "color": (160, 120, 255),
            "color_dark": (35, 20, 80),
            "skill_name": "Arcane Bolt",
            "skill_desc": "Arcane bolt + weave prison + arcane travel + grand arcanum",
            "skill_cooldown": 370,
            "skill_damage": 970,
            "skill_range": 235,
            "description": "Arcanis dari Level 35",
        },
    },
    "nyxallaria": {
        "name": "Nyxallaria",
        "title": "The Abyssal Sovereign",
        "boss_class": "mini",
        "hp": 42500,
        "damage": 315,
        "speed": 1.15,
        "range": 320,            # RANGED (moonlit abyss magic)
        "attack_cooldown": 46,
        "radius": 34,
        "gold_reward": 5550,
        "color": (150, 120, 255),      # abyssal violet
        "color_dark": (30, 18, 80),
        "ability_cooldown": 375,
        "ability_damage": 980,
        "ability_range": 355,
        "entrance_text": "NYXALLARIA, THE ABYSSAL SOVEREIGN, RULES THE DARK DEPTHS!",
        "entrance_color": (205, 190, 255),

        # 4 skills (smart AI - abyssal sovereign)
        "skill_q_damage": 980,      # Abyss Bolt
        "skill_q_cooldown": 375,
        "skill_w_damage": 990,      # Moonlit Depths (AOE)
        "skill_w_cooldown": 435,
        "skill_e_damage": 970,      # Abyssal Step (AOE)
        "skill_e_cooldown": 465,
        "skill_r_damage": 1660,     # Sovereign's Drown (ultimate)
        "skill_r_cooldown": 950,

        # Ranged AI (kite behavior)
        "prefer_distance": 290,
        "min_distance": 170,

        "hero_unlock": {
            "name": "Nyxallaria",
            "title": "The Abyssal Sovereign",
            "role": "Boss/Abyss Mage",
            "cost": 5500,
            "hp": 2700,
            "damage": 300,
            "speed": 1.5,
            "range": 300,
            "attack_cooldown": 46,
            "color": (150, 120, 255),
            "color_dark": (30, 18, 80),
            "skill_name": "Abyss Bolt",
            "skill_desc": "Abyss bolt + moonlit depths + abyssal step + sovereign's drown",
            "skill_cooldown": 375,
            "skill_damage": 980,
            "skill_range": 240,
            "description": "Penguasa jurang dari Level 36",
        },
    },
    "vhaerinth": {
        "name": "Vhaerinth",
        "title": "The Inkweaver",
        "boss_class": "mini",
        "hp": 42000,
        "damage": 310,
        "speed": 1.2,
        "range": 315,            # RANGED (ink magic)
        "attack_cooldown": 44,
        "radius": 34,
        "gold_reward": 5600,
        "color": (90, 120, 200),       # ink blue
        "color_dark": (15, 25, 55),
        "ability_cooldown": 380,
        "ability_damage": 990,
        "ability_range": 350,
        "entrance_text": "VHAERINTH THE INKWEAVER, PAINTS FATE WITH DARK INK!",
        "entrance_color": (165, 195, 255),

        # 4 skills (smart AI - inkweaver)
        "skill_q_damage": 990,      # Ink Splash
        "skill_q_cooldown": 380,
        "skill_w_damage": 1000,     # Ink Veil (AOE)
        "skill_w_cooldown": 440,
        "skill_e_damage": 980,      # Brushstroke Dash (AOE)
        "skill_e_cooldown": 470,
        "skill_r_damage": 1670,     # Masterpiece of Ruin (ultimate)
        "skill_r_cooldown": 955,

        # Ranged AI (kite behavior)
        "prefer_distance": 285,
        "min_distance": 165,

        "hero_unlock": {
            "name": "Vhaerinth",
            "title": "The Inkweaver",
            "role": "Boss/Ink Mage",
            "cost": 5550,
            "hp": 2650,
            "damage": 295,
            "speed": 1.55,
            "range": 295,
            "attack_cooldown": 44,
            "color": (90, 120, 200),
            "color_dark": (15, 25, 55),
            "skill_name": "Ink Splash",
            "skill_desc": "Ink splash + ink veil + brushstroke dash + masterpiece of ruin",
            "skill_cooldown": 380,
            "skill_damage": 990,
            "skill_range": 240,
            "description": "Penenun tinta dari Level 36",
        },
    },
    "xharokh": {
        "name": "Xharokh",
        "title": "The Voidbinder",
        "boss_class": "mini",
        "hp": 43000,
        "damage": 320,
        "speed": 1.1,
        "range": 310,            # RANGED (void staff)
        "attack_cooldown": 48,
        "radius": 36,
        "gold_reward": 5650,
        "color": (120, 80, 220),       # void violet
        "color_dark": (25, 12, 60),
        "ability_cooldown": 385,
        "ability_damage": 1000,
        "ability_range": 360,
        "entrance_text": "XHAROKH THE VOIDBINDER, CHAINS THE UNIVERSE!",
        "entrance_color": (195, 165, 255),

        # 4 skills (smart AI - voidbinder)
        "skill_q_damage": 1000,     # Void Bind
        "skill_q_cooldown": 385,
        "skill_w_damage": 1010,     # Null Prison (AOE)
        "skill_w_cooldown": 445,
        "skill_e_damage": 990,      # Void Shift (AOE)
        "skill_e_cooldown": 475,
        "skill_r_damage": 1680,     # Binder's Eclipse (ultimate)
        "skill_r_cooldown": 960,

        # Ranged AI (kite behavior)
        "prefer_distance": 280,
        "min_distance": 160,

        "hero_unlock": {
            "name": "Xharokh",
            "title": "The Voidbinder",
            "role": "Boss/Void Mage",
            "cost": 5600,
            "hp": 2750,
            "damage": 305,
            "speed": 1.45,
            "range": 290,
            "attack_cooldown": 48,
            "color": (120, 80, 220),
            "color_dark": (25, 12, 60),
            "skill_name": "Void Bind",
            "skill_desc": "Void bind + null prison + void shift + binder's eclipse",
            "skill_cooldown": 385,
            "skill_damage": 1000,
            "skill_range": 245,
            "description": "Pengikat kekosongan dari Level 36",
        },
    },
    "kazreth": {
        "name": "Kazreth",
        "title": "The Blood Reaver",
        "boss_class": "mini",
        "hp": 43500,
        "damage": 320,
        "speed": 1.3,
        "range": 85,             # MELEE (blood scythe)
        "attack_cooldown": 40,
        "radius": 34,
        "gold_reward": 5750,
        "color": (210, 50, 80),        # blood red
        "color_dark": (55, 8, 18),
        "ability_cooldown": 385,
        "ability_damage": 1000,
        "ability_range": 340,
        "entrance_text": "KAZRETH THE BLOOD REAVER, HARVESTS THE BATTLEFIELD!",
        "entrance_color": (255, 140, 160),

        # 4 skills (smart AI - blood reaver)
        "skill_q_damage": 1000,     # Blood Cleave
        "skill_q_cooldown": 385,
        "skill_w_damage": 1010,     # Reaver's Gash (AOE)
        "skill_w_cooldown": 445,
        "skill_e_damage": 990,      # Blood Wings (AOE)
        "skill_e_cooldown": 475,
        "skill_r_damage": 1700,     # Blood Harvest (ultimate)
        "skill_r_cooldown": 965,

        "hero_unlock": {
            "name": "Kazreth",
            "title": "The Blood Reaver",
            "role": "Boss/Blood Reaver",
            "cost": 5700,
            "hp": 2750,
            "damage": 305,
            "speed": 1.6,
            "range": 95,
            "attack_cooldown": 40,
            "color": (210, 50, 80),
            "color_dark": (55, 8, 18),
            "skill_name": "Blood Cleave",
            "skill_desc": "Blood cleave + reaver's gash + blood wings + blood harvest",
            "skill_cooldown": 385,
            "skill_damage": 1000,
            "skill_range": 245,
            "description": "Perobek darah dari Level 37",
        },
    },
    "varkuthar": {
        "name": "Varkuthar",
        "title": "The Bloodfire Zealot",
        "boss_class": "mini",
        "hp": 44000,
        "damage": 325,
        "speed": 1.15,
        "range": 90,             # MELEE (bloodfire mace)
        "attack_cooldown": 46,
        "radius": 36,
        "gold_reward": 5800,
        "color": (255, 120, 50),       # bloodfire orange
        "color_dark": (70, 22, 8),
        "ability_cooldown": 390,
        "ability_damage": 1010,
        "ability_range": 335,
        "entrance_text": "VARKUTHAR THE BLOODFIRE ZEALOT, BURNS FOR THE BLOOD GOD!",
        "entrance_color": (255, 185, 120),

        # 4 skills (smart AI - bloodfire zealot)
        "skill_q_damage": 1010,     # Bloodfire Smash
        "skill_q_cooldown": 390,
        "skill_w_damage": 1020,     # Zealot's Pyre (AOE)
        "skill_w_cooldown": 450,
        "skill_e_damage": 1000,     # Bloodflame Charge (AOE)
        "skill_e_cooldown": 480,
        "skill_r_damage": 1710,     # Sacred Inferno (ultimate)
        "skill_r_cooldown": 970,

        "hero_unlock": {
            "name": "Varkuthar",
            "title": "The Bloodfire Zealot",
            "role": "Boss/Bloodfire Zealot",
            "cost": 5750,
            "hp": 2850,
            "damage": 310,
            "speed": 1.45,
            "range": 100,
            "attack_cooldown": 46,
            "color": (255, 120, 50),
            "color_dark": (70, 22, 8),
            "skill_name": "Bloodfire Smash",
            "skill_desc": "Bloodfire smash + zealot's pyre + bloodflame charge + sacred inferno",
            "skill_cooldown": 390,
            "skill_damage": 1010,
            "skill_range": 250,
            "description": "Fanatik api darah dari Level 37",
        },
    },
    "zhyvrek": {
        "name": "Zhyvrek",
        "title": "The Void Reaper",
        "boss_class": "mini",
        "hp": 43000,
        "damage": 315,
        "speed": 1.35,
        "range": 80,             # MELEE (void scythe)
        "attack_cooldown": 38,
        "radius": 32,
        "gold_reward": 5850,
        "color": (130, 80, 220),       # void purple
        "color_dark": (30, 12, 65),
        "ability_cooldown": 395,
        "ability_damage": 1020,
        "ability_range": 330,
        "entrance_text": "ZHYVREK THE VOID REAPER, CUTS THROUGH THE DARK!",
        "entrance_color": (200, 165, 255),

        # 4 skills (smart AI - void reaper)
        "skill_q_damage": 1020,     # Void Slash
        "skill_q_cooldown": 395,
        "skill_w_damage": 1030,     # Shadow Reap (AOE)
        "skill_w_cooldown": 455,
        "skill_e_damage": 1010,     # Null Step (AOE)
        "skill_e_cooldown": 485,
        "skill_r_damage": 1720,     # Reaper's Void (ultimate)
        "skill_r_cooldown": 975,

        "hero_unlock": {
            "name": "Zhyvrek",
            "title": "The Void Reaper",
            "role": "Boss/Void Reaper",
            "cost": 5800,
            "hp": 2700,
            "damage": 300,
            "speed": 1.65,
            "range": 90,
            "attack_cooldown": 38,
            "color": (130, 80, 220),
            "color_dark": (30, 12, 65),
            "skill_name": "Void Slash",
            "skill_desc": "Void slash + shadow reap + null step + reaper's void",
            "skill_cooldown": 395,
            "skill_damage": 1020,
            "skill_range": 245,
            "description": "Penebas kekosongan dari Level 37",
        },
    },
    "azkharion": {
        "name": "Azkharion",
        "title": "The Ashen Warlord",
        "boss_class": "mini",
        "hp": 44500,
        "damage": 325,
        "speed": 1.2,
        "range": 90,             # MELEE (ashen greatsword)
        "attack_cooldown": 44,
        "radius": 36,
        "gold_reward": 5950,
        "color": (140, 135, 130),      # ash grey
        "color_dark": (35, 30, 28),
        "ability_cooldown": 400,
        "ability_damage": 1030,
        "ability_range": 345,
        "entrance_text": "AZKHARION THE ASHEN WARLORD, COMMANDS THE BURNT LANDS!",
        "entrance_color": (205, 200, 195),

        # 4 skills (smart AI - ashen warlord)
        "skill_q_damage": 1030,     # Ashen Cleave
        "skill_q_cooldown": 400,
        "skill_w_damage": 1040,     # Cinder Warlord (AOE)
        "skill_w_cooldown": 460,
        "skill_e_damage": 1020,     # Ash March (AOE)
        "skill_e_cooldown": 490,
        "skill_r_damage": 1740,     # Warlord's Pyre (ultimate)
        "skill_r_cooldown": 980,

        "hero_unlock": {
            "name": "Azkharion",
            "title": "The Ashen Warlord",
            "role": "Boss/Ashen Warlord",
            "cost": 5900,
            "hp": 2850,
            "damage": 310,
            "speed": 1.5,
            "range": 100,
            "attack_cooldown": 44,
            "color": (140, 135, 130),
            "color_dark": (35, 30, 28),
            "skill_name": "Ashen Cleave",
            "skill_desc": "Ashen cleave + cinder warlord + ash march + warlord's pyre",
            "skill_cooldown": 400,
            "skill_damage": 1030,
            "skill_range": 255,
            "description": "Tuan perang abu dari Level 38",
        },
    },
    "thargoroth": {
        "name": "Thargoroth",
        "title": "The Primordial Colossus",
        "boss_class": "mini",
        "hp": 45000,
        "damage": 330,
        "speed": 0.95,
        "range": 95,             # MELEE (primordial fists)
        "attack_cooldown": 50,
        "radius": 44,
        "gold_reward": 6000,
        "color": (110, 140, 90),       # primordial green
        "color_dark": (30, 45, 25),
        "ability_cooldown": 405,
        "ability_damage": 1040,
        "ability_range": 340,
        "entrance_text": "THARGOROTH THE PRIMORDIAL COLOSSUS, TRAMPLES THE ANCIENT WORLD!",
        "entrance_color": (175, 210, 150),

        # 4 skills (smart AI - primordial colossus)
        "skill_q_damage": 1040,     # Primordial Slam
        "skill_q_cooldown": 405,
        "skill_w_damage": 1050,     # Ancient Rage (AOE)
        "skill_w_cooldown": 465,
        "skill_e_damage": 1030,     # Colossal Stomp (AOE)
        "skill_e_cooldown": 495,
        "skill_r_damage": 1750,     # World Ender (ultimate)
        "skill_r_cooldown": 985,

        "hero_unlock": {
            "name": "Thargoroth",
            "title": "The Primordial Colossus",
            "role": "Boss/Primordial Colossus",
            "cost": 5950,
            "hp": 3100,
            "damage": 315,
            "speed": 1.3,
            "range": 105,
            "attack_cooldown": 50,
            "color": (110, 140, 90),
            "color_dark": (30, 45, 25),
            "skill_name": "Primordial Slam",
            "skill_desc": "Primordial slam + ancient rage + colossal stomp + world ender",
            "skill_cooldown": 405,
            "skill_damage": 1040,
            "skill_range": 260,
            "description": "Kolosus purba dari Level 38",
        },
    },
    "zahkareth": {
        "name": "Zahkareth",
        "title": "The Golden Tyrant",
        "boss_class": "mini",
        "hp": 44000,
        "damage": 335,
        "speed": 1.25,
        "range": 85,             # MELEE (golden warhammer)
        "attack_cooldown": 42,
        "radius": 36,
        "gold_reward": 6050,
        "color": (240, 205, 90),       # tyrant gold
        "color_dark": (75, 55, 10),
        "ability_cooldown": 410,
        "ability_damage": 1050,
        "ability_range": 335,
        "entrance_text": "ZAHKARETH THE GOLDEN TYRANT, DEMANDS ALL TREASURE!",
        "entrance_color": (255, 235, 150),

        # 4 skills (smart AI - golden tyrant)
        "skill_q_damage": 1050,     # Tyrant's Smash
        "skill_q_cooldown": 410,
        "skill_w_damage": 1060,     # Golden Edict (AOE)
        "skill_w_cooldown": 470,
        "skill_e_damage": 1040,     # Tyrant's March (AOE)
        "skill_e_cooldown": 500,
        "skill_r_damage": 1760,     # Gilded Judgment (ultimate)
        "skill_r_cooldown": 990,

        "hero_unlock": {
            "name": "Zahkareth",
            "title": "The Golden Tyrant",
            "role": "Boss/Golden Tyrant",
            "cost": 6000,
            "hp": 2900,
            "damage": 320,
            "speed": 1.55,
            "range": 95,
            "attack_cooldown": 42,
            "color": (240, 205, 90),
            "color_dark": (75, 55, 10),
            "skill_name": "Tyrant's Smash",
            "skill_desc": "Tyrant's smash + golden edict + tyrant's march + gilded judgment",
            "skill_cooldown": 410,
            "skill_damage": 1050,
            "skill_range": 260,
            "description": "Tiran emas dari Level 38",
        },
    },
    "bhorgathul": {
        "name": "Bhor'gathul",
        "title": "The Earth Render",
        "boss_class": "mini",
        "hp": 45500,
        "damage": 335,
        "speed": 1.1,
        "range": 90,             # MELEE (earth rending claws)
        "attack_cooldown": 46,
        "radius": 38,
        "gold_reward": 6150,
        "color": (150, 110, 70),       # earth brown
        "color_dark": (40, 28, 15),
        "ability_cooldown": 415,
        "ability_damage": 1050,
        "ability_range": 350,
        "entrance_text": "BHOR'GATHUL THE EARTH RENDER, SPLITS THE WORLD!",
        "entrance_color": (215, 185, 150),

        # 4 skills (smart AI - earth render)
        "skill_q_damage": 1050,     # Earth Rend
        "skill_q_cooldown": 415,
        "skill_w_damage": 1060,     # Tectonic Rage (AOE)
        "skill_w_cooldown": 475,
        "skill_e_damage": 1040,     # Render's Charge (AOE)
        "skill_e_cooldown": 505,
        "skill_r_damage": 1780,     # Worldrender (ultimate)
        "skill_r_cooldown": 1000,

        "hero_unlock": {
            "name": "Bhor'gathul",
            "title": "The Earth Render",
            "role": "Boss/Earth Render",
            "cost": 6100,
            "hp": 3000,
            "damage": 320,
            "speed": 1.45,
            "range": 100,
            "attack_cooldown": 46,
            "color": (150, 110, 70),
            "color_dark": (40, 28, 15),
            "skill_name": "Earth Rend",
            "skill_desc": "Earth rend + tectonic rage + render's charge + worldrender",
            "skill_cooldown": 415,
            "skill_damage": 1050,
            "skill_range": 265,
            "description": "Perobek bumi dari Level 39",
        },
    },
    "morkhelvis": {
        "name": "Mor'khelvis",
        "title": "The Necrogargoyle",
        "boss_class": "mini",
        "hp": 45000,
        "damage": 330,
        "speed": 1.05,
        "range": 85,             # MELEE (stone claws)
        "attack_cooldown": 48,
        "radius": 40,
        "gold_reward": 6200,
        "color": (120, 130, 140),      # gargoyle grey
        "color_dark": (20, 22, 28),
        "ability_cooldown": 420,
        "ability_damage": 1060,
        "ability_range": 345,
        "entrance_text": "MOR'KHELVIS THE NECROGARGOYLE, AWAKENS FROM STONE!",
        "entrance_color": (190, 200, 210),

        # 4 skills (smart AI - necrogargoyle)
        "skill_q_damage": 1060,     # Stone Rend
        "skill_q_cooldown": 420,
        "skill_w_damage": 1070,     # Necro Veil (AOE)
        "skill_w_cooldown": 480,
        "skill_e_damage": 1050,     # Gargoyle Dive (AOE)
        "skill_e_cooldown": 510,
        "skill_r_damage": 1790,     # Eternal Statue (ultimate)
        "skill_r_cooldown": 1005,

        "hero_unlock": {
            "name": "Mor'khelvis",
            "title": "The Necrogargoyle",
            "role": "Boss/Necrogargoyle",
            "cost": 6150,
            "hp": 3050,
            "damage": 315,
            "speed": 1.4,
            "range": 95,
            "attack_cooldown": 48,
            "color": (120, 130, 140),
            "color_dark": (20, 22, 28),
            "skill_name": "Stone Rend",
            "skill_desc": "Stone rend + necro veil + gargoyle dive + eternal statue",
            "skill_cooldown": 420,
            "skill_damage": 1060,
            "skill_range": 265,
            "description": "Gargoyle kematian dari Level 39",
        },
    },
    "vorthakul": {
        "name": "Vor'thakul",
        "title": "Terror of the Abyss",
        "boss_class": "mini",
        "hp": 46000,
        "damage": 340,
        "speed": 1.2,
        "range": 320,            # RANGED (abyss void magic)
        "attack_cooldown": 44,
        "radius": 36,
        "gold_reward": 6250,
        "color": (110, 60, 190),       # abyss purple
        "color_dark": (25, 10, 55),
        "ability_cooldown": 425,
        "ability_damage": 1070,
        "ability_range": 360,
        "entrance_text": "VOR'THAKUL, TERROR OF THE ABYSS, RISES FROM THE DEEP!",
        "entrance_color": (185, 145, 255),

        # 4 skills (smart AI - abyss terror)
        "skill_q_damage": 1070,     # Abyss Bolt
        "skill_q_cooldown": 425,
        "skill_w_damage": 1080,     # Terror Wave (AOE)
        "skill_w_cooldown": 485,
        "skill_e_damage": 1060,     # Abyssal Step (AOE)
        "skill_e_cooldown": 515,
        "skill_r_damage": 1800,     # Dread Abyss (ultimate)
        "skill_r_cooldown": 1010,

        # Ranged AI (kite behavior)
        "prefer_distance": 290,
        "min_distance": 170,

        "hero_unlock": {
            "name": "Vor'thakul",
            "title": "Terror of the Abyss",
            "role": "Boss/Abyss Terror",
            "cost": 6200,
            "hp": 2950,
            "damage": 325,
            "speed": 1.5,
            "range": 300,
            "attack_cooldown": 44,
            "color": (110, 60, 190),
            "color_dark": (25, 10, 55),
            "skill_name": "Abyss Bolt",
            "skill_desc": "Abyss bolt + terror wave + abyssal step + dread abyss",
            "skill_cooldown": 425,
            "skill_damage": 1070,
            "skill_range": 270,
            "description": "Teror jurang dari Level 39",
        },
    },
    "urgharun": {
        "name": "Ur'gharun",
        "title": "The Feral Wrath",
        "boss_class": "mini",
        "hp": 46500,
        "damage": 340,
        "speed": 1.35,
        "range": 85,             # MELEE (feral claws)
        "attack_cooldown": 38,
        "radius": 36,
        "gold_reward": 6350,
        "color": (255, 140, 60),       # feral orange
        "color_dark": (70, 30, 10),
        "ability_cooldown": 425,
        "ability_damage": 1060,
        "ability_range": 350,
        "entrance_text": "UR'GHARUN THE FERAL WRATH, RIPS THROUGH THE HORDE!",
        "entrance_color": (255, 200, 130),

        # 4 skills (smart AI - feral wrath)
        "skill_q_damage": 1060,     # Feral Rend
        "skill_q_cooldown": 425,
        "skill_w_damage": 1070,     # Wrath Howl (AOE)
        "skill_w_cooldown": 485,
        "skill_e_damage": 1050,     # Beast Rush (AOE)
        "skill_e_cooldown": 515,
        "skill_r_damage": 1820,     # Feral Cataclysm (ultimate)
        "skill_r_cooldown": 1020,

        "hero_unlock": {
            "name": "Ur'gharun",
            "title": "The Feral Wrath",
            "role": "Boss/Feral Beast",
            "cost": 6300,
            "hp": 3050,
            "damage": 325,
            "speed": 1.65,
            "range": 95,
            "attack_cooldown": 38,
            "color": (255, 140, 60),
            "color_dark": (70, 30, 10),
            "skill_name": "Feral Rend",
            "skill_desc": "Feral rend + wrath howl + beast rush + feral cataclysm",
            "skill_cooldown": 425,
            "skill_damage": 1060,
            "skill_range": 270,
            "description": "Amarah liar dari Level 40",
        },
    },
    "yhoranth": {
        "name": "Yh'oranth",
        "title": "The Unforgiven Wraith",
        "boss_class": "mini",
        "hp": 46000,
        "damage": 335,
        "speed": 1.2,
        "range": 325,            # RANGED (wraith soul magic)
        "attack_cooldown": 44,
        "radius": 34,
        "gold_reward": 6400,
        "color": (140, 160, 255),      # wraith blue
        "color_dark": (25, 35, 90),
        "ability_cooldown": 430,
        "ability_damage": 1070,
        "ability_range": 365,
        "entrance_text": "YH'ORANTH THE UNFORGIVEN WRAITH, HAUNTS THE ETERNAL!",
        "entrance_color": (205, 215, 255),

        # 4 skills (smart AI - unforgiven wraith)
        "skill_q_damage": 1070,     # Wraith Bolt
        "skill_q_cooldown": 430,
        "skill_w_damage": 1080,     # Unforgiven Shade (AOE)
        "skill_w_cooldown": 490,
        "skill_e_damage": 1060,     # Spectral Drift (AOE)
        "skill_e_cooldown": 520,
        "skill_r_damage": 1830,     # Eternal Grudge (ultimate)
        "skill_r_cooldown": 1025,

        # Ranged AI (kite behavior)
        "prefer_distance": 295,
        "min_distance": 175,

        "hero_unlock": {
            "name": "Yh'oranth",
            "title": "The Unforgiven Wraith",
            "role": "Boss/Unforgiven Wraith",
            "cost": 6350,
            "hp": 3000,
            "damage": 320,
            "speed": 1.5,
            "range": 305,
            "attack_cooldown": 44,
            "color": (140, 160, 255),
            "color_dark": (25, 35, 90),
            "skill_name": "Wraith Bolt",
            "skill_desc": "Wraith bolt + unforgiven shade + spectral drift + eternal grudge",
            "skill_cooldown": 430,
            "skill_damage": 1070,
            "skill_range": 275,
            "description": "Hantu tak terampuni dari Level 40",
        },
    },
    "zulkhaven": {
        "name": "Zul'khaven",
        "title": "The Devourer",
        "boss_class": "mini",
        "hp": 47000,
        "damage": 350,
        "speed": 1.15,
        "range": 90,             # MELEE (devouring maw)
        "attack_cooldown": 46,
        "radius": 42,
        "gold_reward": 6450,
        "color": (180, 60, 80),        # devour red
        "color_dark": (50, 10, 18),
        "ability_cooldown": 435,
        "ability_damage": 1080,
        "ability_range": 355,
        "entrance_text": "ZUL'KHAVEN THE DEVOURER, CONSUMES ALL IN ITS PATH!",
        "entrance_color": (255, 150, 160),

        # 4 skills (smart AI - devourer)
        "skill_q_damage": 1080,     # Devour Bite
        "skill_q_cooldown": 435,
        "skill_w_damage": 1090,     # Maw of Ruin (AOE)
        "skill_w_cooldown": 495,
        "skill_e_damage": 1070,     # Hungry Charge (AOE)
        "skill_e_cooldown": 525,
        "skill_r_damage": 1840,     # Endless Feast (ultimate)
        "skill_r_cooldown": 1030,

        "hero_unlock": {
            "name": "Zul'khaven",
            "title": "The Devourer",
            "role": "Boss/Devourer",
            "cost": 6400,
            "hp": 3150,
            "damage": 335,
            "speed": 1.45,
            "range": 100,
            "attack_cooldown": 46,
            "color": (180, 60, 80),
            "color_dark": (50, 10, 18),
            "skill_name": "Devour Bite",
            "skill_desc": "Devour bite + maw of ruin + hungry charge + endless feast",
            "skill_cooldown": 435,
            "skill_damage": 1080,
            "skill_range": 275,
            "description": "Pelahap dari Level 40",
        },
    },
    "emberwick": {
        "name": "Emberwick",
        "title": "The Blazing Matron",
        "boss_class": "mini",
        "hp": 47500,
        "damage": 345,
        "speed": 1.2,
        "range": 315,            # RANGED (fire magic + gnashfang)
        "attack_cooldown": 44,
        "radius": 36,
        "gold_reward": 6550,
        "color": (255, 165, 50),       # fire orange
        "color_dark": (30, 8, 2),
        "ability_cooldown": 435,
        "ability_damage": 1090,
        "ability_range": 365,
        "entrance_text": "MOTHER EMBERWICK THE BLAZING MATRON, BURNS THE WORLD!",
        "entrance_color": (255, 220, 120),

        # 4 skills (smart AI - blazing matron)
        "skill_q_damage": 1090,     # Fire Lance
        "skill_q_cooldown": 435,
        "skill_w_damage": 1100,     # Matron's Pyre (AOE)
        "skill_w_cooldown": 495,
        "skill_e_damage": 1080,     # Gnashfang Bite (AOE)
        "skill_e_cooldown": 525,
        "skill_r_damage": 1860,     # Blazing Judgment (ultimate)
        "skill_r_cooldown": 1040,

        # Ranged AI (kite behavior)
        "prefer_distance": 285,
        "min_distance": 165,

        "hero_unlock": {
            "name": "Emberwick",
            "title": "The Blazing Matron",
            "role": "Boss/Fire Matron",
            "cost": 6500,
            "hp": 3100,
            "damage": 330,
            "speed": 1.5,
            "range": 295,
            "attack_cooldown": 44,
            "color": (255, 165, 50),
            "color_dark": (30, 8, 2),
            "skill_name": "Fire Lance",
            "skill_desc": "Fire lance + matron's pyre + gnashfang bite + blazing judgment",
            "skill_cooldown": 435,
            "skill_damage": 1090,
            "skill_range": 280,
            "description": "Matron api dari Level 41",
        },
    },
    "grondarthul": {
        "name": "Grondarthul",
        "title": "The Troll King",
        "boss_class": "mini",
        "hp": 48000,
        "damage": 350,
        "speed": 1.05,
        "range": 90,             # MELEE (frost troll club)
        "attack_cooldown": 48,
        "radius": 44,
        "gold_reward": 6600,
        "color": (110, 155, 80),       # troll green
        "color_dark": (25, 40, 20),
        "ability_cooldown": 440,
        "ability_damage": 1100,
        "ability_range": 360,
        "entrance_text": "GRONDAR THUL THE TROLL KING, RULES THE FROZEN HILLS!",
        "entrance_color": (170, 210, 130),

        # 4 skills (smart AI - troll king)
        "skill_q_damage": 1100,     # Troll Smash
        "skill_q_cooldown": 440,
        "skill_w_damage": 1110,     # King's Roar (AOE)
        "skill_w_cooldown": 500,
        "skill_e_damage": 1090,     # Frozen Charge (AOE)
        "skill_e_cooldown": 530,
        "skill_r_damage": 1870,     # Troll King's Wrath (ultimate)
        "skill_r_cooldown": 1045,

        "hero_unlock": {
            "name": "Grondarthul",
            "title": "The Troll King",
            "role": "Boss/Troll King",
            "cost": 6550,
            "hp": 3200,
            "damage": 335,
            "speed": 1.4,
            "range": 100,
            "attack_cooldown": 48,
            "color": (110, 155, 80),
            "color_dark": (25, 40, 20),
            "skill_name": "Troll Smash",
            "skill_desc": "Troll smash + king's roar + frozen charge + troll king's wrath",
            "skill_cooldown": 440,
            "skill_damage": 1100,
            "skill_range": 280,
            "description": "Raja troll dari Level 41",
        },
    },
    "xareth": {
        "name": "Xareth",
        "title": "The Timereder",
        "boss_class": "mini",
        "hp": 47000,
        "damage": 340,
        "speed": 1.2,
        "range": 320,            # RANGED (void time magic)
        "attack_cooldown": 44,
        "radius": 34,
        "gold_reward": 6650,
        "color": (150, 100, 230),      # void violet
        "color_dark": (30, 15, 65),
        "ability_cooldown": 445,
        "ability_damage": 1110,
        "ability_range": 370,
        "entrance_text": "XARETH THE TIMERENDER, UNRAVELS FATE ITSELF!",
        "entrance_color": (210, 180, 255),

        # 4 skills (smart AI - timereder)
        "skill_q_damage": 1110,     # Time Bolt
        "skill_q_cooldown": 445,
        "skill_w_damage": 1120,     # Chrono Rupture (AOE)
        "skill_w_cooldown": 505,
        "skill_e_damage": 1100,     # Void Step (AOE)
        "skill_e_cooldown": 535,
        "skill_r_damage": 1880,     # Timebreak (ultimate)
        "skill_r_cooldown": 1050,

        # Ranged AI (kite behavior)
        "prefer_distance": 290,
        "min_distance": 170,

        "hero_unlock": {
            "name": "Xareth",
            "title": "The Timereder",
            "role": "Boss/Time Voidwalker",
            "cost": 6600,
            "hp": 3050,
            "damage": 325,
            "speed": 1.5,
            "range": 300,
            "attack_cooldown": 44,
            "color": (150, 100, 230),
            "color_dark": (30, 15, 65),
            "skill_name": "Time Bolt",
            "skill_desc": "Time bolt + chrono rupture + void step + timebreak",
            "skill_cooldown": 445,
            "skill_damage": 1110,
            "skill_range": 285,
            "description": "Perobek waktu dari Level 41",
        },
    },
    "kaedrin": {
        "name": "Kaedrin",
        "title": "The Moonfang",
        "boss_class": "mini",
        "hp": 48500,
        "damage": 350,
        "speed": 1.3,
        "range": 85,             # MELEE (moonfang blade)
        "attack_cooldown": 40,
        "radius": 34,
        "gold_reward": 6750,
        "color": (180, 200, 255),      # moon silver
        "color_dark": (30, 40, 80),
        "ability_cooldown": 445,
        "ability_damage": 1100,
        "ability_range": 365,
        "entrance_text": "KAEDRIN THE MOONFANG, STRIKES UNDER THE CRESCENT!",
        "entrance_color": (220, 230, 255),

        # 4 skills (smart AI - moonfang)
        "skill_q_damage": 1100,     # Moon Slash
        "skill_q_cooldown": 445,
        "skill_w_damage": 1110,     # Fang Crescent (AOE)
        "skill_w_cooldown": 505,
        "skill_e_damage": 1090,     # Moonstep (AOE)
        "skill_e_cooldown": 535,
        "skill_r_damage": 1900,     # Fang of the Moon (ultimate)
        "skill_r_cooldown": 1055,

        "hero_unlock": {
            "name": "Kaedrin",
            "title": "The Moonfang",
            "role": "Boss/Moonfang Bladebearer",
            "cost": 6700,
            "hp": 3150,
            "damage": 335,
            "speed": 1.6,
            "range": 95,
            "attack_cooldown": 40,
            "color": (180, 200, 255),
            "color_dark": (30, 40, 80),
            "skill_name": "Moon Slash",
            "skill_desc": "Moon slash + fang crescent + moonstep + fang of the moon",
            "skill_cooldown": 445,
            "skill_damage": 1100,
            "skill_range": 285,
            "description": "Taring bulan dari Level 42",
        },
    },
    "morvaeth2": {
        "name": "Morvaeth",
        "title": "The Mirrorborn",
        "boss_class": "mini",
        "hp": 48000,
        "damage": 355,
        "speed": 1.25,
        "range": 90,             # MELEE (mirrorborn demon marauder)
        "attack_cooldown": 42,
        "radius": 36,
        "gold_reward": 6800,
        "color": (230, 70, 80),        # mirror crimson
        "color_dark": (55, 10, 18),
        "ability_cooldown": 450,
        "ability_damage": 1110,
        "ability_range": 360,
        "entrance_text": "MORVAETH THE MIRRORBORN, MARCHES WITH DEMON LEGIONS!",
        "entrance_color": (255, 150, 150),

        # 4 skills (smart AI - mirrorborn)
        "skill_q_damage": 1110,     # Mirror Slash
        "skill_q_cooldown": 450,
        "skill_w_damage": 1120,     # Demon Reflection (AOE)
        "skill_w_cooldown": 510,
        "skill_e_damage": 1100,     # Marauder's March (AOE)
        "skill_e_cooldown": 540,
        "skill_r_damage": 1910,     # Mirrorborn Cataclysm (ultimate)
        "skill_r_cooldown": 1060,

        "hero_unlock": {
            "name": "Morvaeth",
            "title": "The Mirrorborn",
            "role": "Boss/Mirrorborn Marauder",
            "cost": 6750,
            "hp": 3200,
            "damage": 340,
            "speed": 1.55,
            "range": 100,
            "attack_cooldown": 42,
            "color": (230, 70, 80),
            "color_dark": (55, 10, 18),
            "skill_name": "Mirror Slash",
            "skill_desc": "Mirror slash + demon reflection + marauder's march + mirrorborn cataclysm",
            "skill_cooldown": 450,
            "skill_damage": 1110,
            "skill_range": 285,
            "description": "Iblis cermin dari Level 42",
        },
    },
    "vardrok": {
        "name": "Vardrok",
        "title": "The Axe-King",
        "boss_class": "mini",
        "hp": 49000,
        "damage": 360,
        "speed": 1.1,
        "range": 95,             # MELEE (glorious axe)
        "attack_cooldown": 48,
        "radius": 42,
        "gold_reward": 6850,
        "color": (200, 120, 60),       # axe bronze
        "color_dark": (60, 30, 10),
        "ability_cooldown": 455,
        "ability_damage": 1120,
        "ability_range": 355,
        "entrance_text": "VARDROK THE AXE-KING, EXECUTES WITH GLORY!",
        "entrance_color": (255, 200, 130),

        # 4 skills (smart AI - axe-king)
        "skill_q_damage": 1120,     # King's Chop
        "skill_q_cooldown": 455,
        "skill_w_damage": 1130,     # Executioner's Cry (AOE)
        "skill_w_cooldown": 515,
        "skill_e_damage": 1110,     # Axe Charge (AOE)
        "skill_e_cooldown": 545,
        "skill_r_damage": 1920,     # Glorious Guillotine (ultimate)
        "skill_r_cooldown": 1065,

        "hero_unlock": {
            "name": "Vardrok",
            "title": "The Axe-King",
            "role": "Boss/Axe-King",
            "cost": 6800,
            "hp": 3300,
            "damage": 345,
            "speed": 1.45,
            "range": 105,
            "attack_cooldown": 48,
            "color": (200, 120, 60),
            "color_dark": (60, 30, 10),
            "skill_name": "King's Chop",
            "skill_desc": "King's chop + executioner's cry + axe charge + glorious guillotine",
            "skill_cooldown": 455,
            "skill_damage": 1120,
            "skill_range": 290,
            "description": "Raja kapak dari Level 42",
        },
    },
    "nixweaver": {
        "name": "Nixweaver",
        "title": "The Woodland Trickster",
        "boss_class": "mini",
        "hp": 49500,
        "damage": 355,
        "speed": 1.35,
        "range": 315,            # RANGED (woodland trick magic)
        "attack_cooldown": 40,
        "radius": 32,
        "gold_reward": 6950,
        "color": (110, 190, 90),       # woodland green
        "color_dark": (25, 55, 20),
        "ability_cooldown": 455,
        "ability_damage": 1130,
        "ability_range": 370,
        "entrance_text": "NIXWEAVER THE WOODLAND TRICKSTER, PLAYS THE FOREST GAMES!",
        "entrance_color": (180, 240, 160),

        # 4 skills (smart AI - woodland trickster)
        "skill_q_damage": 1130,     # Trick Bolt
        "skill_q_cooldown": 455,
        "skill_w_damage": 1140,     # Forest Mirage (AOE)
        "skill_w_cooldown": 515,
        "skill_e_damage": 1120,     # Leaf Step (AOE)
        "skill_e_cooldown": 545,
        "skill_r_damage": 1940,     # Woodland Carnival (ultimate)
        "skill_r_cooldown": 1075,

        # Ranged AI (kite behavior)
        "prefer_distance": 285,
        "min_distance": 165,

        "hero_unlock": {
            "name": "Nixweaver",
            "title": "The Woodland Trickster",
            "role": "Boss/Woodland Trickster",
            "cost": 6900,
            "hp": 3150,
            "damage": 340,
            "speed": 1.65,
            "range": 295,
            "attack_cooldown": 40,
            "color": (110, 190, 90),
            "color_dark": (25, 55, 20),
            "skill_name": "Trick Bolt",
            "skill_desc": "Trick bolt + forest mirage + leaf step + woodland carnival",
            "skill_cooldown": 455,
            "skill_damage": 1130,
            "skill_range": 290,
            "description": "Trikster hutan dari Level 43",
        },
    },
    "nyxraal": {
        "name": "Nyxraal",
        "title": "The Abyssal Prince",
        "boss_class": "mini",
        "hp": 49000,
        "damage": 360,
        "speed": 1.3,
        "range": 90,             # MELEE (abyssal trident)
        "attack_cooldown": 42,
        "radius": 36,
        "gold_reward": 7000,
        "color": (110, 60, 190),       # abyss purple
        "color_dark": (25, 10, 55),
        "ability_cooldown": 460,
        "ability_damage": 1140,
        "ability_range": 365,
        "entrance_text": "NYXRAAL THE ABYSSAL PRINCE, CLAIMS THE DARK THRONE!",
        "entrance_color": (185, 145, 255),

        # 4 skills (smart AI - abyssal prince)
        "skill_q_damage": 1140,     # Abyss Thrust
        "skill_q_cooldown": 460,
        "skill_w_damage": 1150,     # Prince's Tide (AOE)
        "skill_w_cooldown": 520,
        "skill_e_damage": 1130,     # Dark Charge (AOE)
        "skill_e_cooldown": 550,
        "skill_r_damage": 1950,     # Abyssal Coronation (ultimate)
        "skill_r_cooldown": 1080,

        "hero_unlock": {
            "name": "Nyxraal",
            "title": "The Abyssal Prince",
            "role": "Boss/Abyssal Prince",
            "cost": 6950,
            "hp": 3250,
            "damage": 345,
            "speed": 1.6,
            "range": 100,
            "attack_cooldown": 42,
            "color": (110, 60, 190),
            "color_dark": (25, 10, 55),
            "skill_name": "Abyss Thrust",
            "skill_desc": "Abyss thrust + prince's tide + dark charge + abyssal coronation",
            "skill_cooldown": 460,
            "skill_damage": 1140,
            "skill_range": 290,
            "description": "Pangeran jurang dari Level 43",
        },
    },
    "xarnthuul": {
        "name": "Xarn'thuul",
        "title": "The Void Sovereign",
        "boss_class": "mini",
        "hp": 50000,
        "damage": 350,
        "speed": 1.15,
        "range": 330,            # RANGED (void magic)
        "attack_cooldown": 46,
        "radius": 34,
        "gold_reward": 7050,
        "color": (140, 80, 230),       # void violet
        "color_dark": (30, 12, 65),
        "ability_cooldown": 465,
        "ability_damage": 1150,
        "ability_range": 375,
        "entrance_text": "XARN'THUUL THE VOID SOVEREIGN, RULES THE EMPTY REACH!",
        "entrance_color": (210, 175, 255),

        # 4 skills (smart AI - void sovereign)
        "skill_q_damage": 1150,     # Void Lance
        "skill_q_cooldown": 465,
        "skill_w_damage": 1160,     # Null Throne (AOE)
        "skill_w_cooldown": 525,
        "skill_e_damage": 1140,     # Void Drift (AOE)
        "skill_e_cooldown": 555,
        "skill_r_damage": 1960,     # Sovereign's Void (ultimate)
        "skill_r_cooldown": 1085,

        # Ranged AI (kite behavior)
        "prefer_distance": 300,
        "min_distance": 180,

        "hero_unlock": {
            "name": "Xarn'thuul",
            "title": "The Void Sovereign",
            "role": "Boss/Void Sovereign",
            "cost": 7000,
            "hp": 3100,
            "damage": 335,
            "speed": 1.5,
            "range": 310,
            "attack_cooldown": 46,
            "color": (140, 80, 230),
            "color_dark": (30, 12, 65),
            "skill_name": "Void Lance",
            "skill_desc": "Void lance + null throne + void drift + sovereign's void",
            "skill_cooldown": 465,
            "skill_damage": 1150,
            "skill_range": 295,
            "description": "Penguasa kekosongan dari Level 43",
        },
    },
    "lyrenya": {
        "name": "Lyrenya",
        "title": "The Verdant Whisper",
        "boss_class": "mini",
        "hp": 50500,
        "damage": 360,
        "speed": 1.2,
        "range": 320,            # RANGED (nature magic)
        "attack_cooldown": 44,
        "radius": 34,
        "gold_reward": 7150,
        "color": (110, 190, 110),      # verdant green
        "color_dark": (25, 55, 25),
        "ability_cooldown": 465,
        "ability_damage": 1150,
        "ability_range": 375,
        "entrance_text": "LYRENYA THE VERDANT WHISPER, SPEAKS IN LEAVES AND VINES!",
        "entrance_color": (180, 240, 180),

        # 4 skills (smart AI - verdant whisper)
        "skill_q_damage": 1150,     # Vine Whip
        "skill_q_cooldown": 465,
        "skill_w_damage": 1160,     # Verdant Bloom (AOE)
        "skill_w_cooldown": 525,
        "skill_e_damage": 1140,     # Nature Step (AOE)
        "skill_e_cooldown": 555,
        "skill_r_damage": 1980,     # Whisper of the Forest (ultimate)
        "skill_r_cooldown": 1090,

        # Ranged AI (kite behavior)
        "prefer_distance": 290,
        "min_distance": 170,

        "hero_unlock": {
            "name": "Lyrenya",
            "title": "The Verdant Whisper",
            "role": "Boss/Nature Mage",
            "cost": 7100,
            "hp": 3200,
            "damage": 345,
            "speed": 1.5,
            "range": 300,
            "attack_cooldown": 44,
            "color": (110, 190, 110),
            "color_dark": (25, 55, 25),
            "skill_name": "Vine Whip",
            "skill_desc": "Vine whip + verdant bloom + nature step + whisper of the forest",
            "skill_cooldown": 465,
            "skill_damage": 1150,
            "skill_range": 295,
            "description": "Bisikan hijau dari Level 44",
        },
    },
    "vyraeth": {
        "name": "Vyraeth",
        "title": "The Haunting Wraith",
        "boss_class": "mini",
        "hp": 50000,
        "damage": 355,
        "speed": 1.25,
        "range": 325,            # RANGED (spectral haunt)
        "attack_cooldown": 42,
        "radius": 34,
        "gold_reward": 7200,
        "color": (150, 170, 255),      # spectral blue
        "color_dark": (30, 40, 90),
        "ability_cooldown": 470,
        "ability_damage": 1160,
        "ability_range": 380,
        "entrance_text": "VYRAETH THE HAUNTING WRAITH, WHISPERS FROM THE VEIL!",
        "entrance_color": (215, 225, 255),

        # 4 skills (smart AI - haunting wraith)
        "skill_q_damage": 1160,     # Haunt Bolt
        "skill_q_cooldown": 470,
        "skill_w_damage": 1170,     # Spectral Veil (AOE)
        "skill_w_cooldown": 530,
        "skill_e_damage": 1150,     # Ghost Drift (AOE)
        "skill_e_cooldown": 560,
        "skill_r_damage": 1990,     # Eternal Haunting (ultimate)
        "skill_r_cooldown": 1095,

        # Ranged AI (kite behavior)
        "prefer_distance": 295,
        "min_distance": 175,

        "hero_unlock": {
            "name": "Vyraeth",
            "title": "The Haunting Wraith",
            "role": "Boss/Spectral Wraith",
            "cost": 7150,
            "hp": 3150,
            "damage": 340,
            "speed": 1.55,
            "range": 305,
            "attack_cooldown": 42,
            "color": (150, 170, 255),
            "color_dark": (30, 40, 90),
            "skill_name": "Haunt Bolt",
            "skill_desc": "Haunt bolt + spectral veil + ghost drift + eternal haunting",
            "skill_cooldown": 470,
            "skill_damage": 1160,
            "skill_range": 300,
            "description": "Hantu penghantui dari Level 44",
        },
    },
    "zorothrax": {
        "name": "Zorothrax",
        "title": "The Rune Sovereign",
        "boss_class": "mini",
        "hp": 51000,
        "damage": 365,
        "speed": 1.15,
        "range": 330,            # RANGED (rune magic)
        "attack_cooldown": 46,
        "radius": 36,
        "gold_reward": 7250,
        "color": (190, 150, 255),      # rune violet
        "color_dark": (40, 25, 80),
        "ability_cooldown": 475,
        "ability_damage": 1170,
        "ability_range": 385,
        "entrance_text": "ZOROTHRAX THE RUNE SOVEREIGN, ETCHES THE FATES!",
        "entrance_color": (235, 215, 255),

        # 4 skills (smart AI - rune sovereign)
        "skill_q_damage": 1170,     # Rune Bolt
        "skill_q_cooldown": 475,
        "skill_w_damage": 1180,     # Arcane Rune Field (AOE)
        "skill_w_cooldown": 535,
        "skill_e_damage": 1160,     # Rune Shift (AOE)
        "skill_e_cooldown": 565,
        "skill_r_damage": 2000,     # Sovereign's Rune (ultimate)
        "skill_r_cooldown": 1100,

        # Ranged AI (kite behavior)
        "prefer_distance": 300,
        "min_distance": 180,

        "hero_unlock": {
            "name": "Zorothrax",
            "title": "The Rune Sovereign",
            "role": "Boss/Rune Mage",
            "cost": 7200,
            "hp": 3300,
            "damage": 350,
            "speed": 1.5,
            "range": 310,
            "attack_cooldown": 46,
            "color": (190, 150, 255),
            "color_dark": (40, 25, 80),
            "skill_name": "Rune Bolt",
            "skill_desc": "Rune bolt + arcane rune field + rune shift + sovereign's rune",
            "skill_cooldown": 475,
            "skill_damage": 1170,
            "skill_range": 300,
            "description": "Penguasa rune dari Level 44",
        },
    },
    "akiraze": {
        "name": "Akiraze",
        "title": "The Golden Tempest",
        "boss_class": "mini",
        "hp": 51500,
        "damage": 365,
        "speed": 1.4,
        "range": 85,             # MELEE (golden lightning blades)
        "attack_cooldown": 38,
        "radius": 34,
        "gold_reward": 7350,
        "color": (255, 215, 90),       # golden lightning
        "color_dark": (70, 50, 10),
        "ability_cooldown": 475,
        "ability_damage": 1180,
        "ability_range": 375,
        "entrance_text": "AKIRAZE THE GOLDEN TEMPEST, STRIKES LIKE THUNDER!",
        "entrance_color": (255, 240, 160),

        # 4 skills (smart AI - golden tempest)
        "skill_q_damage": 1180,     # Golden Slash
        "skill_q_cooldown": 475,
        "skill_w_damage": 1190,     # Tempest Flash (AOE)
        "skill_w_cooldown": 535,
        "skill_e_damage": 1170,     # Thunder Step (AOE)
        "skill_e_cooldown": 565,
        "skill_r_damage": 2020,     # Golden Cataclysm (ultimate)
        "skill_r_cooldown": 1110,

        "hero_unlock": {
            "name": "Akiraze",
            "title": "The Golden Tempest",
            "role": "Boss/Golden Ninja",
            "cost": 7300,
            "hp": 3250,
            "damage": 350,
            "speed": 1.7,
            "range": 95,
            "attack_cooldown": 38,
            "color": (255, 215, 90),
            "color_dark": (70, 50, 10),
            "skill_name": "Golden Slash",
            "skill_desc": "Golden slash + tempest flash + thunder step + golden cataclysm",
            "skill_cooldown": 475,
            "skill_damage": 1180,
            "skill_range": 300,
            "description": "Badai emas dari Level 45",
        },
    },
    "brumhar": {
        "name": "Brumhar",
        "title": "The Glacier Reaver",
        "boss_class": "mini",
        "hp": 51000,
        "damage": 370,
        "speed": 1.1,
        "range": 90,             # MELEE (glacier axe)
        "attack_cooldown": 48,
        "radius": 42,
        "gold_reward": 7400,
        "color": (150, 220, 255),      # glacier ice
        "color_dark": (25, 55, 90),
        "ability_cooldown": 480,
        "ability_damage": 1190,
        "ability_range": 370,
        "entrance_text": "BRUMHAR THE GLACIER REAVER, FREEZES THE BATTLEFIELD!",
        "entrance_color": (210, 245, 255),

        # 4 skills (smart AI - glacier reaver)
        "skill_q_damage": 1190,     # Glacier Chop
        "skill_q_cooldown": 480,
        "skill_w_damage": 1200,     # Frozen Wrath (AOE)
        "skill_w_cooldown": 540,
        "skill_e_damage": 1180,     # Ice Reave (AOE)
        "skill_e_cooldown": 570,
        "skill_r_damage": 2030,     # Glacier Cataclysm (ultimate)
        "skill_r_cooldown": 1115,

        "hero_unlock": {
            "name": "Brumhar",
            "title": "The Glacier Reaver",
            "role": "Boss/Glacier Warrior",
            "cost": 7350,
            "hp": 3350,
            "damage": 355,
            "speed": 1.4,
            "range": 100,
            "attack_cooldown": 48,
            "color": (150, 220, 255),
            "color_dark": (25, 55, 90),
            "skill_name": "Glacier Chop",
            "skill_desc": "Glacier chop + frozen wrath + ice reave + glacier cataclysm",
            "skill_cooldown": 480,
            "skill_damage": 1190,
            "skill_range": 305,
            "description": "Perobek gletser dari Level 45",
        },
    },
    "zorashi": {
        "name": "Zorashi",
        "title": "The Serpent Sage",
        "boss_class": "mini",
        "hp": 52000,
        "damage": 360,
        "speed": 1.2,
        "range": 335,            # RANGED (serpent magic)
        "attack_cooldown": 44,
        "radius": 34,
        "gold_reward": 7450,
        "color": (140, 200, 100),      # serpent green
        "color_dark": (30, 55, 20),
        "ability_cooldown": 485,
        "ability_damage": 1200,
        "ability_range": 385,
        "entrance_text": "ZORASHI THE SERPENT SAGE, WHISPERS WITH SNAKES!",
        "entrance_color": (200, 245, 170),

        # 4 skills (smart AI - serpent sage)
        "skill_q_damage": 1200,     # Serpent Fang
        "skill_q_cooldown": 485,
        "skill_w_damage": 1210,     # Snake Storm (AOE)
        "skill_w_cooldown": 545,
        "skill_e_damage": 1190,     # Serpent Step (AOE)
        "skill_e_cooldown": 575,
        "skill_r_damage": 2040,     # Sage's Serpents (ultimate)
        "skill_r_cooldown": 1120,

        # Ranged AI (kite behavior)
        "prefer_distance": 305,
        "min_distance": 185,

        "hero_unlock": {
            "name": "Zorashi",
            "title": "The Serpent Sage",
            "role": "Boss/Serpent Sage",
            "cost": 7400,
            "hp": 3200,
            "damage": 345,
            "speed": 1.55,
            "range": 315,
            "attack_cooldown": 44,
            "color": (140, 200, 100),
            "color_dark": (30, 55, 20),
            "skill_name": "Serpent Fang",
            "skill_desc": "Serpent fang + snake storm + serpent step + sage's serpents",
            "skill_cooldown": 485,
            "skill_damage": 1200,
            "skill_range": 305,
            "description": "Bijak ular dari Level 45",
        },
    },
    "akaroth": {
        "name": "Akaroth",
        "title": "The Crimson Fist",
        "boss_class": "mini",
        "hp": 52500,
        "damage": 370,
        "speed": 1.3,
        "range": 85,             # MELEE (crimson fists)
        "attack_cooldown": 40,
        "radius": 36,
        "gold_reward": 7550,
        "color": (230, 70, 45),        # crimson fist
        "color_dark": (60, 12, 10),
        "ability_cooldown": 485,
        "ability_damage": 1210,
        "ability_range": 380,
        "entrance_text": "AKAROTH THE CRIMSON FIST, SMASHES THROUGH ALL BARRIERS!",
        "entrance_color": (255, 150, 130),

        # 4 skills (smart AI - crimson fist)
        "skill_q_damage": 1210,     # Crimson Jab
        "skill_q_cooldown": 485,
        "skill_w_damage": 1220,     # Fist Storm (AOE)
        "skill_w_cooldown": 545,
        "skill_e_damage": 1200,     # Blood Step (AOE)
        "skill_e_cooldown": 575,
        "skill_r_damage": 2060,     # Crimson Cataclysm (ultimate)
        "skill_r_cooldown": 1125,

        "hero_unlock": {
            "name": "Akaroth",
            "title": "The Crimson Fist",
            "role": "Boss/Crimson Brawler",
            "cost": 7500,
            "hp": 3350,
            "damage": 355,
            "speed": 1.6,
            "range": 95,
            "attack_cooldown": 40,
            "color": (230, 70, 45),
            "color_dark": (60, 12, 10),
            "skill_name": "Crimson Jab",
            "skill_desc": "Crimson jab + fist storm + blood step + crimson cataclysm",
            "skill_cooldown": 485,
            "skill_damage": 1210,
            "skill_range": 310,
            "description": "Tinju merah dari Level 46",
        },
    },
    "kassadin": {
        "name": "Kassadin",
        "title": "The Void Walker",
        "boss_class": "mini",
        "hp": 52000,
        "damage": 365,
        "speed": 1.25,
        "range": 330,            # RANGED (void blade magic)
        "attack_cooldown": 44,
        "radius": 34,
        "gold_reward": 7600,
        "color": (120, 80, 220),       # void purple
        "color_dark": (25, 12, 60),
        "ability_cooldown": 490,
        "ability_damage": 1220,
        "ability_range": 385,
        "entrance_text": "KASSADIN THE VOID WALKER, WALKS BETWEEN DIMENSIONS!",
        "entrance_color": (195, 165, 255),

        # 4 skills (smart AI - void walker)
        "skill_q_damage": 1220,     # Null Blade
        "skill_q_cooldown": 490,
        "skill_w_damage": 1230,     # Void Pulse (AOE)
        "skill_w_cooldown": 550,
        "skill_e_damage": 1210,     # Rift Step (AOE)
        "skill_e_cooldown": 580,
        "skill_r_damage": 2070,     # Voidwalk (ultimate)
        "skill_r_cooldown": 1130,

        # Ranged AI (kite behavior)
        "prefer_distance": 300,
        "min_distance": 180,

        "hero_unlock": {
            "name": "Kassadin",
            "title": "The Void Walker",
            "role": "Boss/Void Walker",
            "cost": 7550,
            "hp": 3250,
            "damage": 350,
            "speed": 1.6,
            "range": 310,
            "attack_cooldown": 44,
            "color": (120, 80, 220),
            "color_dark": (25, 12, 60),
            "skill_name": "Null Blade",
            "skill_desc": "Null blade + void pulse + rift step + voidwalk",
            "skill_cooldown": 490,
            "skill_damage": 1220,
            "skill_range": 310,
            "description": "Pejalan kekosongan dari Level 46",
        },
    },
    "shimorakh": {
        "name": "Shimorakh",
        "title": "The Root of Shadows",
        "boss_class": "mini",
        "hp": 53000,
        "damage": 375,
        "speed": 1.15,
        "range": 320,            # RANGED (shadow root magic)
        "attack_cooldown": 46,
        "radius": 38,
        "gold_reward": 7650,
        "color": (90, 70, 140),        # shadow root
        "color_dark": (20, 12, 40),
        "ability_cooldown": 495,
        "ability_damage": 1230,
        "ability_range": 390,
        "entrance_text": "SHIMORAKH THE ROOT OF SHADOWS, SPREADS DARKNESS BENEATH!",
        "entrance_color": (175, 150, 225),

        # 4 skills (smart AI - root of shadows)
        "skill_q_damage": 1230,     # Shadow Root
        "skill_q_cooldown": 495,
        "skill_w_damage": 1240,     # Dark Bloom (AOE)
        "skill_w_cooldown": 555,
        "skill_e_damage": 1220,     # Root Grasp (AOE)
        "skill_e_cooldown": 585,
        "skill_r_damage": 2080,     # Shadowforest (ultimate)
        "skill_r_cooldown": 1135,

        # Ranged AI (kite behavior)
        "prefer_distance": 290,
        "min_distance": 170,

        "hero_unlock": {
            "name": "Shimorakh",
            "title": "The Root of Shadows",
            "role": "Boss/Shadow Root",
            "cost": 7600,
            "hp": 3400,
            "damage": 360,
            "speed": 1.5,
            "range": 300,
            "attack_cooldown": 46,
            "color": (90, 70, 140),
            "color_dark": (20, 12, 40),
            "skill_name": "Shadow Root",
            "skill_desc": "Shadow root + dark bloom + root grasp + shadowforest",
            "skill_cooldown": 495,
            "skill_damage": 1230,
            "skill_range": 315,
            "description": "Akar bayangan dari Level 46",
        },
    },
    "kaizoku_raijin": {
        "name": "Kaizoku Raijin",
        "title": "The Festival Thunder",
        "boss_class": "mini",
        "hp": 53500,
        "damage": 375,
        "speed": 1.35,
        "range": 85,             # MELEE (lightning festival blades)
        "attack_cooldown": 38,
        "radius": 36,
        "gold_reward": 7750,
        "color": (255, 220, 90),       # festival gold
        "color_dark": (70, 50, 10),
        "ability_cooldown": 495,
        "ability_damage": 1240,
        "ability_range": 385,
        "entrance_text": "KAIZOKU RAIJIN THE FESTIVAL THUNDER, LIGHTS UP THE NIGHT!",
        "entrance_color": (255, 245, 180),

        # 4 skills (smart AI - festival thunder)
        "skill_q_damage": 1240,     # Thunder Blade
        "skill_q_cooldown": 495,
        "skill_w_damage": 1250,     # Festival Storm (AOE)
        "skill_w_cooldown": 555,
        "skill_e_damage": 1230,     # Raijin Step (AOE)
        "skill_e_cooldown": 585,
        "skill_r_damage": 2100,     # Thunder Festival (ultimate)
        "skill_r_cooldown": 1140,

        "hero_unlock": {
            "name": "Kaizoku Raijin",
            "title": "The Festival Thunder",
            "role": "Boss/Lightning Pirate",
            "cost": 7700,
            "hp": 3400,
            "damage": 360,
            "speed": 1.65,
            "range": 95,
            "attack_cooldown": 38,
            "color": (255, 220, 90),
            "color_dark": (70, 50, 10),
            "skill_name": "Thunder Blade",
            "skill_desc": "Thunder blade + festival storm + raijin step + thunder festival",
            "skill_cooldown": 495,
            "skill_damage": 1240,
            "skill_range": 315,
            "description": "Petir festival dari Level 47",
        },
    },
    "korokai": {
        "name": "Korokai",
        "title": "The Mirror Blade",
        "boss_class": "mini",
        "hp": 53000,
        "damage": 380,
        "speed": 1.4,
        "range": 90,             # MELEE (mirror katana)
        "attack_cooldown": 36,
        "radius": 34,
        "gold_reward": 7800,
        "color": (190, 220, 255),      # mirror silver
        "color_dark": (35, 45, 80),
        "ability_cooldown": 500,
        "ability_damage": 1250,
        "ability_range": 380,
        "entrance_text": "KOROKAI THE MIRROR BLADE, REFLECTS ALL THREATS!",
        "entrance_color": (225, 240, 255),

        # 4 skills (smart AI - mirror blade)
        "skill_q_damage": 1250,     # Mirror Slash
        "skill_q_cooldown": 500,
        "skill_w_damage": 1260,     # Reflective Edge (AOE)
        "skill_w_cooldown": 560,
        "skill_e_damage": 1240,     # Shinobi Step (AOE)
        "skill_e_cooldown": 590,
        "skill_r_damage": 2110,     # Mirror World (ultimate)
        "skill_r_cooldown": 1145,

        "hero_unlock": {
            "name": "Korokai",
            "title": "The Mirror Blade",
            "role": "Boss/Mirror Shinobi",
            "cost": 7750,
            "hp": 3350,
            "damage": 365,
            "speed": 1.7,
            "range": 100,
            "attack_cooldown": 36,
            "color": (190, 220, 255),
            "color_dark": (35, 45, 80),
            "skill_name": "Mirror Slash",
            "skill_desc": "Mirror slash + reflective edge + shinobi step + mirror world",
            "skill_cooldown": 500,
            "skill_damage": 1250,
            "skill_range": 315,
            "description": "Pedang cermin dari Level 47",
        },
    },
    "verdanix": {
        "name": "Verdanix",
        "title": "The Verdant Fury",
        "boss_class": "mini",
        "hp": 54000,
        "damage": 370,
        "speed": 1.2,
        "range": 340,            # RANGED (nature wrath magic)
        "attack_cooldown": 46,
        "radius": 36,
        "gold_reward": 7850,
        "color": (120, 200, 90),       # verdant green
        "color_dark": (25, 55, 20),
        "ability_cooldown": 505,
        "ability_damage": 1260,
        "ability_range": 395,
        "entrance_text": "VERDANIX THE VERDANT FURY, STORMS WITH NATURE'S WRATH!",
        "entrance_color": (190, 245, 160),

        # 4 skills (smart AI - verdant fury)
        "skill_q_damage": 1260,     # Nature Bolt
        "skill_q_cooldown": 505,
        "skill_w_damage": 1270,     # Verdant Storm (AOE)
        "skill_w_cooldown": 565,
        "skill_e_damage": 1250,     # Wild Step (AOE)
        "skill_e_cooldown": 595,
        "skill_r_damage": 2120,     # Fury of the Forest (ultimate)
        "skill_r_cooldown": 1150,

        # Ranged AI (kite behavior)
        "prefer_distance": 310,
        "min_distance": 190,

        "hero_unlock": {
            "name": "Verdanix",
            "title": "The Verdant Fury",
            "role": "Boss/Nature Mage",
            "cost": 7800,
            "hp": 3450,
            "damage": 355,
            "speed": 1.5,
            "range": 320,
            "attack_cooldown": 46,
            "color": (120, 200, 90),
            "color_dark": (25, 55, 20),
            "skill_name": "Nature Bolt",
            "skill_desc": "Nature bolt + verdant storm + wild step + fury of the forest",
            "skill_cooldown": 505,
            "skill_damage": 1260,
            "skill_range": 320,
            "description": "Amarah hijau dari Level 47",
        },
    },
    "broggmar": {
        "name": "Broggmar",
        "title": "The Caskbreaker",
        "boss_class": "mini",
        "hp": 54500,
        "damage": 380,
        "speed": 1.15,
        "range": 90,             # MELEE (explosive cask club)
        "attack_cooldown": 46,
        "radius": 42,
        "gold_reward": 7950,
        "color": (170, 100, 40),       # cask copper
        "color_dark": (35, 18, 8),
        "ability_cooldown": 505,
        "ability_damage": 1270,
        "ability_range": 390,
        "entrance_text": "BROGGMAR THE CASKBREAKER, SMASHES WITH EXPLOSIVE FURY!",
        "entrance_color": (255, 210, 140),

        # 4 skills (smart AI - caskbreaker)
        "skill_q_damage": 1270,     # Cask Smash
        "skill_q_cooldown": 505,
        "skill_w_damage": 1280,     # Barrel Blast (AOE)
        "skill_w_cooldown": 565,
        "skill_e_damage": 1260,     # Brew Charge (AOE)
        "skill_e_cooldown": 595,
        "skill_r_damage": 2140,     # Caskbreaker's Boom (ultimate)
        "skill_r_cooldown": 1160,

        "hero_unlock": {
            "name": "Broggmar",
            "title": "The Caskbreaker",
            "role": "Boss/Cask Brawler",
            "cost": 7900,
            "hp": 3500,
            "damage": 365,
            "speed": 1.45,
            "range": 100,
            "attack_cooldown": 46,
            "color": (170, 100, 40),
            "color_dark": (35, 18, 8),
            "skill_name": "Cask Smash",
            "skill_desc": "Cask smash + barrel blast + brew charge + caskbreaker's boom",
            "skill_cooldown": 505,
            "skill_damage": 1270,
            "skill_range": 320,
            "description": "Pemecah tong dari Level 48",
        },
    },
    "ursath": {
        "name": "Ursath",
        "title": "The Wildcaller",
        "boss_class": "mini",
        "hp": 54000,
        "damage": 375,
        "speed": 1.3,
        "range": 335,            # RANGED (nature beast magic)
        "attack_cooldown": 42,
        "radius": 36,
        "gold_reward": 8000,
        "color": (140, 200, 110),      # wild green
        "color_dark": (30, 55, 22),
        "ability_cooldown": 510,
        "ability_damage": 1280,
        "ability_range": 400,
        "entrance_text": "URSATH THORNMANE THE WILDCALLER, SUMMONS THE BEASTS!",
        "entrance_color": (205, 245, 180),

        # 4 skills (smart AI - wildcaller)
        "skill_q_damage": 1280,     # Thorn Roar
        "skill_q_cooldown": 510,
        "skill_w_damage": 1290,     # Beast Stampede (AOE)
        "skill_w_cooldown": 570,
        "skill_e_damage": 1270,     # Wild Step (AOE)
        "skill_e_cooldown": 600,
        "skill_r_damage": 2150,     # Call of the Wild (ultimate)
        "skill_r_cooldown": 1165,

        # Ranged AI (kite behavior)
        "prefer_distance": 305,
        "min_distance": 185,

        "hero_unlock": {
            "name": "Ursath",
            "title": "The Wildcaller",
            "role": "Boss/Wildcaller",
            "cost": 7950,
            "hp": 3450,
            "damage": 360,
            "speed": 1.6,
            "range": 315,
            "attack_cooldown": 42,
            "color": (140, 200, 110),
            "color_dark": (30, 55, 22),
            "skill_name": "Thorn Roar",
            "skill_desc": "Thorn roar + beast stampede + wild step + call of the wild",
            "skill_cooldown": 510,
            "skill_damage": 1280,
            "skill_range": 325,
            "description": "Pemanggil liar dari Level 48",
        },
    },
    "zhaeris": {
        "name": "Zhaeris",
        "title": "The Shadowblade",
        "boss_class": "mini",
        "hp": 55000,
        "damage": 390,
        "speed": 1.45,
        "range": 85,             # MELEE (shadow katana)
        "attack_cooldown": 36,
        "radius": 32,
        "gold_reward": 8050,
        "color": (110, 90, 160),       # shadow violet
        "color_dark": (20, 12, 40),
        "ability_cooldown": 515,
        "ability_damage": 1290,
        "ability_range": 395,
        "entrance_text": "ZHAERIS THE SHADOWBLADE, STRIKES FROM THE DARK!",
        "entrance_color": (185, 165, 235),

        # 4 skills (smart AI - shadowblade)
        "skill_q_damage": 1290,     # Shadow Slash
        "skill_q_cooldown": 515,
        "skill_w_damage": 1300,     # Dark Flurry (AOE)
        "skill_w_cooldown": 575,
        "skill_e_damage": 1280,     # Void Step (AOE)
        "skill_e_cooldown": 605,
        "skill_r_damage": 2160,     # Shadowblade's Dusk (ultimate)
        "skill_r_cooldown": 1170,

        "hero_unlock": {
            "name": "Zhaeris",
            "title": "The Shadowblade",
            "role": "Boss/Shadow Ninja",
            "cost": 8000,
            "hp": 3400,
            "damage": 375,
            "speed": 1.75,
            "range": 95,
            "attack_cooldown": 36,
            "color": (110, 90, 160),
            "color_dark": (20, 12, 40),
            "skill_name": "Shadow Slash",
            "skill_desc": "Shadow slash + dark flurry + void step + shadowblade's dusk",
            "skill_cooldown": 515,
            "skill_damage": 1290,
            "skill_range": 320,
            "description": "Pedang bayangan dari Level 48",
        },
    },
    "kairenji": {
        "name": "Kairenji",
        "title": "The Voidblade",
        "boss_class": "mini",
        "hp": 56000,
        "damage": 395,
        "speed": 1.45,
        "range": 85,             # MELEE (void katana)
        "attack_cooldown": 36,
        "radius": 34,
        "gold_reward": 8150,
        "color": (150, 70, 220),       # void purple
        "color_dark": (15, 5, 30),
        "ability_cooldown": 520,
        "ability_damage": 1300,
        "ability_range": 400,
        "entrance_text": "KAIRENJI THE VOIDBLADE, SLICES FROM THE SHADOWS!",
        "entrance_color": (230, 190, 255),

        # 4 skills (smart AI - voidblade)
        "skill_q_damage": 1300,     # Void Slash
        "skill_q_cooldown": 520,
        "skill_w_damage": 1310,     # Shadowclone Flurry (AOE)
        "skill_w_cooldown": 580,
        "skill_e_damage": 1290,     # Void Step (AOE)
        "skill_e_cooldown": 610,
        "skill_r_damage": 2200,     # Moonless Night (ultimate)
        "skill_r_cooldown": 1170,

        "hero_unlock": {
            "name": "Kairenji",
            "title": "The Voidblade",
            "role": "Boss/Shadow Ninja",
            "cost": 8150,
            "hp": 3500,
            "damage": 385,
            "speed": 1.8,
            "range": 95,
            "attack_cooldown": 36,
            "color": (150, 70, 220),
            "color_dark": (15, 5, 30),
            "skill_name": "Void Slash",
            "skill_desc": "Void slash + shadowclone flurry + void step + moonless night",
            "skill_cooldown": 520,
            "skill_damage": 1300,
            "skill_range": 330,
            "description": "Bayangan void dari Level 49",
        },
    },

    "karzhul": {
        "name": "Karzhul",
        "title": "The Fangreaver",
        "boss_class": "mini",
        "hp": 56500,
        "damage": 400,
        "speed": 1.35,
        "range": 90,             # MELEE (feral claws)
        "attack_cooldown": 40,
        "radius": 40,
        "gold_reward": 8200,
        "color": (185, 185, 200),       # silver wolf
        "color_dark": (18, 18, 22),
        "ability_cooldown": 525,
        "ability_damage": 1310,
        "ability_range": 405,
        "entrance_text": "KARZHUL THE FANGREAVER, HUNTS BENEATH THE FULL MOON!",
        "entrance_color": (245, 245, 250),

        # 4 skills (smart AI - fangreaver)
        "skill_q_damage": 1310,     # Fang Ripper
        "skill_q_cooldown": 525,
        "skill_w_damage": 1320,     # Blood Frenzy (AOE)
        "skill_w_cooldown": 585,
        "skill_e_damage": 1300,     # Wild Leap (AOE)
        "skill_e_cooldown": 615,
        "skill_r_damage": 2210,     # Lunar Rampage (ultimate)
        "skill_r_cooldown": 1175,

        "hero_unlock": {
            "name": "Karzhul",
            "title": "The Fangreaver",
            "role": "Boss/Werewolf",
            "cost": 8200,
            "hp": 3550,
            "damage": 390,
            "speed": 1.7,
            "range": 100,
            "attack_cooldown": 40,
            "color": (185, 185, 200),
            "color_dark": (18, 18, 22),
            "skill_name": "Fang Ripper",
            "skill_desc": "Fang ripper + blood frenzy + wild leap + lunar rampage",
            "skill_cooldown": 525,
            "skill_damage": 1310,
            "skill_range": 335,
            "description": "Serigala pemburu dari Level 49",
        },
    },

    "xerakkuth": {
        "name": "Xerakkuth",
        "title": "The Dunehorror",
        "boss_class": "mini",
        "hp": 55500,
        "damage": 390,
        "speed": 1.2,
        "range": 345,            # RANGED (caustic venom sting)
        "attack_cooldown": 44,
        "radius": 38,
        "gold_reward": 8100,
        "color": (215, 160, 65),       # desert chitin gold
        "color_dark": (25, 15, 5),
        "ability_cooldown": 515,
        "ability_damage": 1290,
        "ability_range": 420,
        "entrance_text": "XERAKKUTH THE DUNEHORROR, RISES FROM THE BURNING SANDS!",
        "entrance_color": (250, 215, 130),

        # 4 skills (smart AI - dunehorror)
        "skill_q_damage": 1290,     # Venom Sting
        "skill_q_cooldown": 515,
        "skill_w_damage": 1300,     # Sandstorm (AOE)
        "skill_w_cooldown": 575,
        "skill_e_damage": 1280,     # Burrow Strike (AOE)
        "skill_e_cooldown": 605,
        "skill_r_damage": 2180,     # Dune Cataclysm (ultimate)
        "skill_r_cooldown": 1160,

        # Ranged AI (kite behavior)
        "prefer_distance": 315,
        "min_distance": 195,

        "hero_unlock": {
            "name": "Xerakkuth",
            "title": "The Dunehorror",
            "role": "Boss/Desert Scorpion",
            "cost": 8100,
            "hp": 3450,
            "damage": 375,
            "speed": 1.5,
            "range": 325,
            "attack_cooldown": 44,
            "color": (215, 160, 65),
            "color_dark": (25, 15, 5),
            "skill_name": "Venom Sting",
            "skill_desc": "Venom sting + sandstorm + burrow strike + dune cataclysm",
            "skill_cooldown": 515,
            "skill_damage": 1290,
            "skill_range": 340,
            "description": "Kalajengking pasir dari Level 49",
        },
    },

    "kaelthys": {
        "name": "Kaelthys",
        "title": "The Stillwater Blade",
        "boss_class": "mini",
        "hp": 57000,
        "damage": 405,
        "speed": 1.35,
        "range": 90,             # MELEE (water slashing blade)
        "attack_cooldown": 40,
        "radius": 36,
        "gold_reward": 8300,
        "color": (140, 200, 235),       # stillwater blue
        "color_dark": (10, 30, 55),
        "ability_cooldown": 530,
        "ability_damage": 1320,
        "ability_range": 410,
        "entrance_text": "KAELTHYS THE STILLWATER BLADE, FLOWS FROM THE DEEP!",
        "entrance_color": (180, 225, 250),

        # 4 skills (smart AI - stillwater)
        "skill_q_damage": 1320,     # Stillwater Slash
        "skill_q_cooldown": 530,
        "skill_w_damage": 1330,     # Waterfall Flurry (AOE)
        "skill_w_cooldown": 590,
        "skill_e_damage": 1310,     # Ripple Step (AOE)
        "skill_e_cooldown": 620,
        "skill_r_damage": 2250,     # Tidal Blade (ultimate)
        "skill_r_cooldown": 1180,

        "hero_unlock": {
            "name": "Kaelthys",
            "title": "The Stillwater Blade",
            "role": "Boss/Water Swordsman",
            "cost": 8300,
            "hp": 3600,
            "damage": 400,
            "speed": 1.7,
            "range": 100,
            "attack_cooldown": 40,
            "color": (140, 200, 235),
            "color_dark": (10, 30, 55),
            "skill_name": "Stillwater Slash",
            "skill_desc": "Stillwater slash + waterfall flurry + ripple step + tidal blade",
            "skill_cooldown": 530,
            "skill_damage": 1320,
            "skill_range": 340,
            "description": "Pedang air dari Level 50",
        },
    },

    "kaoruken": {
        "name": "Kaoruken",
        "title": "The Palmseer",
        "boss_class": "mini",
        "hp": 57500,
        "damage": 410,
        "speed": 1.4,
        "range": 85,             # MELEE (chakra palm strikes)
        "attack_cooldown": 36,
        "radius": 34,
        "gold_reward": 8350,
        "color": (170, 190, 255),       # byakugan pale blue
        "color_dark": (15, 20, 60),
        "ability_cooldown": 535,
        "ability_damage": 1330,
        "ability_range": 415,
        "entrance_text": "KAORUKEN THE PALMSEER, PIERCES WITH THE ALL-SEEING EYE!",
        "entrance_color": (215, 225, 255),

        # 4 skills (smart AI - palmseer)
        "skill_q_damage": 1330,     # Chakra Palm
        "skill_q_cooldown": 535,
        "skill_w_damage": 1340,     # Gentle Fist Flurry (AOE)
        "skill_w_cooldown": 595,
        "skill_e_damage": 1320,     # Byakugan Step (AOE)
        "skill_e_cooldown": 625,
        "skill_r_damage": 2260,     # Eight Trigrams (ultimate)
        "skill_r_cooldown": 1185,

        "hero_unlock": {
            "name": "Kaoruken",
            "title": "The Palmseer",
            "role": "Boss/Chakra Prodigy",
            "cost": 8350,
            "hp": 3650,
            "damage": 405,
            "speed": 1.8,
            "range": 95,
            "attack_cooldown": 36,
            "color": (170, 190, 255),
            "color_dark": (15, 20, 60),
            "skill_name": "Chakra Palm",
            "skill_desc": "Chakra palm + gentle fist flurry + byakugan step + eight trigrams",
            "skill_cooldown": 535,
            "skill_damage": 1330,
            "skill_range": 345,
            "description": "Prodigi chakra dari Level 50",
        },
    },

    "vaelkorr": {
        "name": "Vaelkorr",
        "title": "The Threadbinder Immortal",
        "boss_class": "mini",
        "hp": 56500,
        "damage": 400,
        "speed": 1.2,
        "range": 355,            # RANGED (thread magic bolts)
        "attack_cooldown": 44,
        "radius": 36,
        "gold_reward": 8250,
        "color": (190, 120, 90),       # thread dark red
        "color_dark": (30, 10, 10),
        "ability_cooldown": 525,
        "ability_damage": 1310,
        "ability_range": 430,
        "entrance_text": "VAELKORR THE THREADBINDER IMMORTAL, WEAVES A WEB OF DEATH!",
        "entrance_color": (235, 185, 160),

        # 4 skills (smart AI - threadbinder)
        "skill_q_damage": 1310,     # Thread Lance
        "skill_q_cooldown": 525,
        "skill_w_damage": 1320,     # Stitch Storm (AOE)
        "skill_w_cooldown": 585,
        "skill_e_damage": 1300,     # Thread Step (AOE)
        "skill_e_cooldown": 615,
        "skill_r_damage": 2240,     # Immortal Weave (ultimate)
        "skill_r_cooldown": 1170,

        # Ranged AI (kite behavior)
        "prefer_distance": 325,
        "min_distance": 205,

        "hero_unlock": {
            "name": "Vaelkorr",
            "title": "The Threadbinder Immortal",
            "role": "Boss/Thread Mage",
            "cost": 8250,
            "hp": 3550,
            "damage": 390,
            "speed": 1.5,
            "range": 335,
            "attack_cooldown": 44,
            "color": (190, 120, 90),
            "color_dark": (30, 10, 10),
            "skill_name": "Thread Lance",
            "skill_desc": "Thread lance + stitch storm + thread step + immortal weave",
            "skill_cooldown": 525,
            "skill_damage": 1310,
            "skill_range": 350,
            "description": "Abadi pengikat benang dari Level 50",
        },
    },

    "aurelian": {
        "name": "Aurelian",
        "title": "The Goldspear Sovereign",
        "boss_class": "mini",
        "hp": 58000,
        "damage": 415,
        "speed": 1.25,
        "range": 95,             # MELEE (golden spear strikes)
        "attack_cooldown": 42,
        "radius": 40,
        "gold_reward": 8450,
        "color": (245, 210, 95),       # sovereign gold
        "color_dark": (30, 22, 5),
        "ability_cooldown": 540,
        "ability_damage": 1340,
        "ability_range": 420,
        "entrance_text": "AURELIAN VHORN THE GOLDSPEAR SOVEREIGN, LEADS THE VANGUARD!",
        "entrance_color": (255, 235, 160),

        # 4 skills (smart AI - goldspear)
        "skill_q_damage": 1340,     # Golden Spear
        "skill_q_cooldown": 540,
        "skill_w_damage": 1350,     # Vanguard Banner (AOE)
        "skill_w_cooldown": 600,
        "skill_e_damage": 1330,     # Sovereign Dash (AOE)
        "skill_e_cooldown": 630,
        "skill_r_damage": 2290,     # Cataclysm of Gold (ultimate)
        "skill_r_cooldown": 1190,

        "hero_unlock": {
            "name": "Aurelian",
            "title": "The Goldspear Sovereign",
            "role": "Boss/Fighter-Tank",
            "cost": 8450,
            "hp": 3700,
            "damage": 410,
            "speed": 1.6,
            "range": 105,
            "attack_cooldown": 42,
            "color": (245, 210, 95),
            "color_dark": (30, 22, 5),
            "skill_name": "Golden Spear",
            "skill_desc": "Golden spear + vanguard banner + sovereign dash + cataclysm of gold",
            "skill_cooldown": 540,
            "skill_damage": 1340,
            "skill_range": 350,
            "description": "Sovereign tombak emas dari Level 51",
        },
    },

    "morvath": {
        "name": "Morvath",
        "title": "The Deepmaw Leviathan",
        "boss_class": "mini",
        "hp": 58500,
        "damage": 420,
        "speed": 1.1,
        "range": 100,            # MELEE (great shark blade)
        "attack_cooldown": 48,
        "radius": 44,
        "gold_reward": 8500,
        "color": (60, 130, 160),       # deepmaw teal
        "color_dark": (5, 20, 30),
        "ability_cooldown": 545,
        "ability_damage": 1350,
        "ability_range": 425,
        "entrance_text": "MORVATH THE DEEPMAW LEVIATHAN, RISES FROM THE ABYSSAL TRENCH!",
        "entrance_color": (140, 210, 235),

        # 4 skills (smart AI - deepmaw)
        "skill_q_damage": 1350,     # Shark Blade
        "skill_q_cooldown": 545,
        "skill_w_damage": 1360,     # Water Prison (AOE)
        "skill_w_cooldown": 605,
        "skill_e_damage": 1340,     # Trench Dive (AOE)
        "skill_e_cooldown": 635,
        "skill_r_damage": 2300,     # Leviathan's Wake (ultimate)
        "skill_r_cooldown": 1195,

        "hero_unlock": {
            "name": "Morvath",
            "title": "The Deepmaw Leviathan",
            "role": "Boss/Strength",
            "cost": 8500,
            "hp": 3750,
            "damage": 415,
            "speed": 1.45,
            "range": 110,
            "attack_cooldown": 48,
            "color": (60, 130, 160),
            "color_dark": (5, 20, 30),
            "skill_name": "Shark Blade",
            "skill_desc": "Shark blade + water prison + trench dive + leviathan's wake",
            "skill_cooldown": 545,
            "skill_damage": 1350,
            "skill_range": 355,
            "description": "Leviathan jurang dari Level 51",
        },
    },

    "pyrhaan": {
        "name": "Pyrhaan",
        "title": "The Cinderborn Adept",
        "boss_class": "mini",
        "hp": 57500,
        "damage": 410,
        "speed": 1.4,
        "range": 85,             # MELEE (cinder fists)
        "attack_cooldown": 36,
        "radius": 34,
        "gold_reward": 8400,
        "color": (255, 150, 40),       # cinder orange
        "color_dark": (30, 8, 2),
        "ability_cooldown": 535,
        "ability_damage": 1330,
        "ability_range": 415,
        "entrance_text": "PYRHAAN THE CINDERBORN ADEPT, BURNS WITH RESTLESS FLAME!",
        "entrance_color": (255, 215, 130),

        # 4 skills (smart AI - cinderborn)
        "skill_q_damage": 1330,     # Cinder Fist
        "skill_q_cooldown": 535,
        "skill_w_damage": 1340,     # Flame Guard (AOE)
        "skill_w_cooldown": 595,
        "skill_e_damage": 1320,     # Searing Dash (AOE)
        "skill_e_cooldown": 625,
        "skill_r_damage": 2280,     # Cinder Storm (ultimate)
        "skill_r_cooldown": 1185,

        "hero_unlock": {
            "name": "Pyrhaan",
            "title": "The Cinderborn Adept",
            "role": "Boss/Agility",
            "cost": 8400,
            "hp": 3650,
            "damage": 405,
            "speed": 1.75,
            "range": 95,
            "attack_cooldown": 36,
            "color": (255, 150, 40),
            "color_dark": (30, 8, 2),
            "skill_name": "Cinder Fist",
            "skill_desc": "Cinder fist + flame guard + searing dash + cinder storm",
            "skill_cooldown": 535,
            "skill_damage": 1330,
            "skill_range": 345,
            "description": "Adept api dari Level 51",
        },
    },

    "garumenshi": {
        "name": "Garumenshi",
        "title": "The Sage Toad Hermit",
        "boss_class": "mini",
        "hp": 59000,
        "damage": 420,
        "speed": 1.2,
        "range": 90,             # MELEE (toad strikes)
        "attack_cooldown": 44,
        "radius": 42,
        "gold_reward": 8550,
        "color": (150, 190, 120),       # toad green
        "color_dark": (15, 30, 12),
        "ability_cooldown": 545,
        "ability_damage": 1350,
        "ability_range": 425,
        "entrance_text": "GARUMENSHI THE SAGE TOAD HERMIT, SUMMONS THE TOAD MOUNTAIN!",
        "entrance_color": (205, 235, 185),

        # 4 skills (smart AI - sage toad)
        "skill_q_damage": 1350,     # Toad Strike
        "skill_q_cooldown": 545,
        "skill_w_damage": 1360,     # Oil Splash (AOE)
        "skill_w_cooldown": 605,
        "skill_e_damage": 1340,     # Toad Leap (AOE)
        "skill_e_cooldown": 635,
        "skill_r_damage": 2310,     # Toad Mountain (ultimate)
        "skill_r_cooldown": 1200,

        "hero_unlock": {
            "name": "Garumenshi",
            "title": "The Sage Toad Hermit",
            "role": "Boss/Summoner",
            "cost": 8550,
            "hp": 3800,
            "damage": 415,
            "speed": 1.5,
            "range": 100,
            "attack_cooldown": 44,
            "color": (150, 190, 120),
            "color_dark": (15, 30, 12),
            "skill_name": "Toad Strike",
            "skill_desc": "Toad strike + oil splash + toad leap + toad mountain",
            "skill_cooldown": 545,
            "skill_damage": 1350,
            "skill_range": 355,
            "description": "Pertapa kodok dari Level 52",
        },
    },

    "thoraz": {
        "name": "Thoraz",
        "title": "The Mountainbreaker",
        "boss_class": "mini",
        "hp": 59500,
        "damage": 425,
        "speed": 1.15,
        "range": 100,            # MELEE (mountain hammer)
        "attack_cooldown": 48,
        "radius": 44,
        "gold_reward": 8600,
        "color": (165, 135, 100),       # mountain stone
        "color_dark": (20, 15, 10),
        "ability_cooldown": 550,
        "ability_damage": 1360,
        "ability_range": 430,
        "entrance_text": "THORAZ THE MOUNTAINBREAKER, SHATTERS THE EARTH ITSELF!",
        "entrance_color": (225, 205, 175),

        # 4 skills (smart AI - mountainbreaker)
        "skill_q_damage": 1360,     # Mountain Slam
        "skill_q_cooldown": 550,
        "skill_w_damage": 1370,     # Avalanche (AOE)
        "skill_w_cooldown": 610,
        "skill_e_damage": 1350,     # Charging Boulder (AOE)
        "skill_e_cooldown": 640,
        "skill_r_damage": 2320,     # Cataclysm Break (ultimate)
        "skill_r_cooldown": 1205,

        "hero_unlock": {
            "name": "Thoraz",
            "title": "The Mountainbreaker",
            "role": "Boss/Fighter-Charger",
            "cost": 8600,
            "hp": 3850,
            "damage": 420,
            "speed": 1.45,
            "range": 110,
            "attack_cooldown": 48,
            "color": (165, 135, 100),
            "color_dark": (20, 15, 10),
            "skill_name": "Mountain Slam",
            "skill_desc": "Mountain slam + avalanche + charging boulder + cataclysm break",
            "skill_cooldown": 550,
            "skill_damage": 1360,
            "skill_range": 360,
            "description": "Penghancur gunung dari Level 52",
        },
    },

    "vhaerith": {
        "name": "Vhaerith",
        "title": "The Hollow Reaper",
        "boss_class": "mini",
        "hp": 58500,
        "damage": 415,
        "speed": 1.2,
        "range": 365,            # RANGED (hollow magic)
        "attack_cooldown": 44,
        "radius": 36,
        "gold_reward": 8500,
        "color": (170, 190, 220),       # hollow pale blue
        "color_dark": (15, 20, 40),
        "ability_cooldown": 535,
        "ability_damage": 1330,
        "ability_range": 440,
        "entrance_text": "VHAERITH THE HOLLOW REAPER, HARVESTS THE SCREAMING DARK!",
        "entrance_color": (215, 230, 250),

        # 4 skills (smart AI - hollow reaper)
        "skill_q_damage": 1330,     # Hollow Bolt
        "skill_q_cooldown": 535,
        "skill_w_damage": 1340,     # Reaping Storm (AOE)
        "skill_w_cooldown": 595,
        "skill_e_damage": 1320,     # Hollow Step (AOE)
        "skill_e_cooldown": 625,
        "skill_r_damage": 2300,     # Harvest of the Damned (ultimate)
        "skill_r_cooldown": 1185,

        # Ranged AI (kite behavior)
        "prefer_distance": 335,
        "min_distance": 215,

        "hero_unlock": {
            "name": "Vhaerith",
            "title": "The Hollow Reaper",
            "role": "Boss/Magic",
            "cost": 8500,
            "hp": 3750,
            "damage": 405,
            "speed": 1.5,
            "range": 345,
            "attack_cooldown": 44,
            "color": (170, 190, 220),
            "color_dark": (15, 20, 40),
            "skill_name": "Hollow Bolt",
            "skill_desc": "Hollow bolt + reaping storm + hollow step + harvest of the damned",
            "skill_cooldown": 535,
            "skill_damage": 1330,
            "skill_range": 360,
            "description": "Penuai hampa dari Level 52",
        },
    },

    "dorakai": {
        "name": "Dorakai",
        "title": "The Blood-Drum Oni",
        "boss_class": "mini",
        "hp": 60000,
        "damage": 425,
        "speed": 1.2,
        "range": 370,            # RANGED (blood drum waves)
        "attack_cooldown": 44,
        "radius": 38,
        "gold_reward": 8650,
        "color": (200, 60, 60),       # blood drum red
        "color_dark": (25, 5, 8),
        "ability_cooldown": 550,
        "ability_damage": 1360,
        "ability_range": 445,
        "entrance_text": "DORAKAI THE BLOOD-DRUM ONI, BEATS THE RHYTHM OF RUIN!",
        "entrance_color": (255, 150, 140),

        # 4 skills (smart AI - blood-drum)
        "skill_q_damage": 1360,     # Drum Wave
        "skill_q_cooldown": 550,
        "skill_w_damage": 1370,     # Bloodbeat Storm (AOE)
        "skill_w_cooldown": 610,
        "skill_e_damage": 1350,     # Drum Step (AOE)
        "skill_e_cooldown": 640,
        "skill_r_damage": 2330,     # Oni's War Drum (ultimate)
        "skill_r_cooldown": 1210,

        # Ranged AI (kite behavior)
        "prefer_distance": 340,
        "min_distance": 220,

        "hero_unlock": {
            "name": "Dorakai",
            "title": "The Blood-Drum Oni",
            "role": "Boss/Area Demon",
            "cost": 8650,
            "hp": 3850,
            "damage": 420,
            "speed": 1.5,
            "range": 350,
            "attack_cooldown": 44,
            "color": (200, 60, 60),
            "color_dark": (25, 5, 8),
            "skill_name": "Drum Wave",
            "skill_desc": "Drum wave + bloodbeat storm + drum step + oni's war drum",
            "skill_cooldown": 550,
            "skill_damage": 1360,
            "skill_range": 365,
            "description": "Oni gendang darah dari Level 53",
        },
    },

    "hitokage": {
        "name": "Hitokage",
        "title": "The Sunfire Blade Master",
        "boss_class": "mini",
        "hp": 60500,
        "damage": 430,
        "speed": 1.4,
        "range": 90,             # MELEE (sunfire katana)
        "attack_cooldown": 36,
        "radius": 36,
        "gold_reward": 8700,
        "color": (255, 180, 60),       # sunfire gold
        "color_dark": (40, 15, 2),
        "ability_cooldown": 555,
        "ability_damage": 1370,
        "ability_range": 430,
        "entrance_text": "HITOKAGE THE SUNFIRE BLADE MASTER, BLAZES WITH THE SUN!",
        "entrance_color": (255, 225, 150),

        # 4 skills (smart AI - sunfire)
        "skill_q_damage": 1370,     # Sunfire Slash
        "skill_q_cooldown": 555,
        "skill_w_damage": 1380,     # Rising Sun (AOE)
        "skill_w_cooldown": 615,
        "skill_e_damage": 1360,     # Sun Step (AOE)
        "skill_e_cooldown": 645,
        "skill_r_damage": 2340,     # Sun Dragon (ultimate)
        "skill_r_cooldown": 1215,

        "hero_unlock": {
            "name": "Hitokage",
            "title": "The Sunfire Blade Master",
            "role": "Boss/Sun Swordsman",
            "cost": 8700,
            "hp": 3900,
            "damage": 425,
            "speed": 1.75,
            "range": 100,
            "attack_cooldown": 36,
            "color": (255, 180, 60),
            "color_dark": (40, 15, 2),
            "skill_name": "Sunfire Slash",
            "skill_desc": "Sunfire slash + rising sun + sun step + sun dragon",
            "skill_cooldown": 555,
            "skill_damage": 1370,
            "skill_range": 355,
            "description": "Master pedang matahari dari Level 53",
        },
    },

    "kazuren": {
        "name": "Kazuren",
        "title": "The Shadow of the Void",
        "boss_class": "mini",
        "hp": 59500,
        "damage": 420,
        "speed": 1.45,
        "range": 85,             # MELEE (void blade)
        "attack_cooldown": 36,
        "radius": 34,
        "gold_reward": 8600,
        "color": (120, 80, 160),       # void shadow purple
        "color_dark": (10, 5, 20),
        "ability_cooldown": 540,
        "ability_damage": 1340,
        "ability_range": 420,
        "entrance_text": "KAZUREN THE SHADOW OF THE VOID, ERASES YOU FROM EXISTENCE!",
        "entrance_color": (190, 160, 230),

        # 4 skills (smart AI - void shadow)
        "skill_q_damage": 1340,     # Void Slash
        "skill_q_cooldown": 540,
        "skill_w_damage": 1350,     # Kamui Storm (AOE)
        "skill_w_cooldown": 600,
        "skill_e_damage": 1330,     # Void Phase (AOE)
        "skill_e_cooldown": 630,
        "skill_r_damage": 2320,     # Eye of the Void (ultimate)
        "skill_r_cooldown": 1200,

        "hero_unlock": {
            "name": "Kazuren",
            "title": "The Shadow of the Void",
            "role": "Boss/Shadow Ninja",
            "cost": 8600,
            "hp": 3800,
            "damage": 415,
            "speed": 1.8,
            "range": 95,
            "attack_cooldown": 36,
            "color": (120, 80, 160),
            "color_dark": (10, 5, 20),
            "skill_name": "Void Slash",
            "skill_desc": "Void slash + kamui storm + void phase + eye of the void",
            "skill_cooldown": 540,
            "skill_damage": 1340,
            "skill_range": 350,
            "description": "Bayangan kekosongan dari Level 53",
        },
    },

    "obanai": {
        "name": "Obanai",
        "title": "The Serpent Hashira",
        "boss_class": "mini",
        "hp": 61000,
        "damage": 430,
        "speed": 1.35,
        "range": 90,             # MELEE (serpent sword)
        "attack_cooldown": 40,
        "radius": 36,
        "gold_reward": 8750,
        "color": (150, 130, 200),       # serpent purple
        "color_dark": (20, 10, 35),
        "ability_cooldown": 555,
        "ability_damage": 1370,
        "ability_range": 430,
        "entrance_text": "OBANAI IGURO THE SERPENT HASHIRA, COILS TO STRIKE!",
        "entrance_color": (205, 190, 245),

        # 4 skills (smart AI - serpent)
        "skill_q_damage": 1370,     # Serpent Fang
        "skill_q_cooldown": 555,
        "skill_w_damage": 1380,     # Serpent Coil (AOE)
        "skill_w_cooldown": 615,
        "skill_e_damage": 1360,     # Venom Step (AOE)
        "skill_e_cooldown": 645,
        "skill_r_damage": 2350,     # Serpent Breathing: Final (ultimate)
        "skill_r_cooldown": 1220,

        "hero_unlock": {
            "name": "Obanai",
            "title": "The Serpent Hashira",
            "role": "Boss/Serpent Swordsman",
            "cost": 8750,
            "hp": 3900,
            "damage": 425,
            "speed": 1.7,
            "range": 100,
            "attack_cooldown": 40,
            "color": (150, 130, 200),
            "color_dark": (20, 10, 35),
            "skill_name": "Serpent Fang",
            "skill_desc": "Serpent fang + serpent coil + venom step + serpent breathing final",
            "skill_cooldown": 555,
            "skill_damage": 1370,
            "skill_range": 355,
            "description": "Hashira ular dari Level 54",
        },
    },

    "sanguire": {
        "name": "Sanguire Voxthal",
        "title": "The Blood Manipulator",
        "boss_class": "mini",
        "hp": 60500,
        "damage": 425,
        "speed": 1.2,
        "range": 375,            # RANGED (blood magic bolts)
        "attack_cooldown": 44,
        "radius": 36,
        "gold_reward": 8700,
        "color": (200, 60, 90),       # blood crimson
        "color_dark": (25, 5, 12),
        "ability_cooldown": 545,
        "ability_damage": 1350,
        "ability_range": 450,
        "entrance_text": "SANGUIRE VOXTHAL THE BLOOD MANIPULATOR, BATHES IN CRIMSON!",
        "entrance_color": (255, 150, 170),

        # 4 skills (smart AI - blood)
        "skill_q_damage": 1350,     # Blood Bolt
        "skill_q_cooldown": 545,
        "skill_w_damage": 1360,     # Crimson Storm (AOE)
        "skill_w_cooldown": 605,
        "skill_e_damage": 1340,     # Blood Step (AOE)
        "skill_e_cooldown": 635,
        "skill_r_damage": 2340,     # Blood Ritual (ultimate)
        "skill_r_cooldown": 1205,

        # Ranged AI (kite behavior)
        "prefer_distance": 345,
        "min_distance": 225,

        "hero_unlock": {
            "name": "Sanguire Voxthal",
            "title": "The Blood Manipulator",
            "role": "Boss/Blood Mage",
            "cost": 8700,
            "hp": 3850,
            "damage": 415,
            "speed": 1.5,
            "range": 355,
            "attack_cooldown": 44,
            "color": (200, 60, 90),
            "color_dark": (25, 5, 12),
            "skill_name": "Blood Bolt",
            "skill_desc": "Blood bolt + crimson storm + blood step + blood ritual",
            "skill_cooldown": 545,
            "skill_damage": 1350,
            "skill_range": 370,
            "description": "Pengendali darah dari Level 54",
        },
    },

    "sasori": {
        "name": "Sasori",
        "title": "The Red Sand Puppeteer",
        "boss_class": "mini",
        "hp": 61500,
        "damage": 435,
        "speed": 1.15,
        "range": 95,             # MELEE (puppet strikes)
        "attack_cooldown": 44,
        "radius": 38,
        "gold_reward": 8800,
        "color": (200, 90, 60),       # red sand
        "color_dark": (25, 10, 5),
        "ability_cooldown": 560,
        "ability_damage": 1380,
        "ability_range": 435,
        "entrance_text": "SASORI THE RED SAND PUPPETEER, DANCES WITH A HUNDRED PUPPETS!",
        "entrance_color": (255, 180, 150),

        # 4 skills (smart AI - puppeteer)
        "skill_q_damage": 1380,     # Puppet Slash
        "skill_q_cooldown": 560,
        "skill_w_damage": 1390,     # Puppet Storm (AOE)
        "skill_w_cooldown": 620,
        "skill_e_damage": 1370,     # String Step (AOE)
        "skill_e_cooldown": 650,
        "skill_r_damage": 2360,     # Red Secret Technique (ultimate)
        "skill_r_cooldown": 1225,

        "hero_unlock": {
            "name": "Sasori",
            "title": "The Red Sand Puppeteer",
            "role": "Boss/Puppeteer",
            "cost": 8800,
            "hp": 3950,
            "damage": 430,
            "speed": 1.5,
            "range": 105,
            "attack_cooldown": 44,
            "color": (200, 90, 60),
            "color_dark": (25, 10, 5),
            "skill_name": "Puppet Slash",
            "skill_desc": "Puppet slash + puppet storm + string step + red secret technique",
            "skill_cooldown": 560,
            "skill_damage": 1380,
            "skill_range": 360,
            "description": "Dalang pasir merah dari Level 54",
        },
    },

}
# ═══════════════════════════════════════════════════════
# TRUE BOSSES (muncul saat tower musuh tersisa ≤ 3)
# Setiap level punya 1 true boss
# ═══════════════════════════════════════════════════════

# Level → true boss type
LEVEL_TRUE_BOSS = {
    1: "abaddon",
    2: "alchemist",
    3: "ancient_apparition",
    4: "ignis_drachorn",
    5: "krobellus",
    6: "kunkka",
    7: "nyxarath",
    8: "vhorethzir",
    9: "naraka",
    10: "aurethzar",
    11: "thalakryon",
    12: "nazulmor",
    13: "solvarin",
    14: "pyraethis",
    15: "yamako",
    16: "seiryukong",
    17: "nyxareth",
    18: "aurelion",
    19: "vaelindra",
    20: "morthraxis",
    21: "nexthyrius",
    22: "molgravar",
    23: "seraphienne",
    24: "solareth",
    25: "okeanora",
    26: "vaelmyrra",
    27: "zarethyr",
    28: "nyrethzalv",
    29: "nyrellieth",
    30: "nyxharr",
    31: "ravokkar",
    32: "malzeroth",
    33: "zharakzuul",
    34: "grondmauris",
    35: "lyssarethys",
    36: "kaerinya",
    37: "xelnarath",
    38: "kyrenzai",
    39: "xaelmoran",
    40: "thalryndel",
    41: "grimkor",
    42: "kaineroth",
    43: "zyvareth",
    44: "kagetsuka",
    45: "deidara",
    46: "sunakage",
    47: "pyraena",
    48: "cogsworth",
    49: "yomigetsu",
    50: "akirakumo",
    51: "kaithros",
    52: "nyxaris",
    53: "tsukiyora",
    54: "hollowbane",
}

TRUE_BOSS_TYPES = {
    "abaddon": {
        "name": "Abaddon",
        "title": "Lord of Avernus",
        "boss_class": "true",
        "hp": 15000,
        "damage": 100,
        "speed": 0.85,
        "range": 50,
        "attack_cooldown": 43,  # attack speed 1.4
        "radius": 42,
        "gold_reward": 1500,
        "color": (100, 220, 240),      # teal cyan (glow color)
        "color_dark": (30, 60, 100),   # dark blue
        "ability_cooldown": 180,       # smart AI decides which skill
        "ability_damage": 200,
        "ability_range": 200,
        "entrance_text": "ABADDON, LORD OF AVERNUS RIDES FORTH!",
        "entrance_color": (100, 220, 240),

        # 4 skills (smart AI)
        "skill_q_damage": 250,      # Mist Coil
        "skill_q_cooldown": 240,
        "skill_w_damage": 300,      # Aphotic Shield burst
        "skill_w_shield": 500,
        "skill_w_cooldown": 360,
        "skill_e_damage": 200,      # Darkness Gale
        "skill_e_cooldown": 300,
        "skill_r_damage": 500,      # Death Sever ultimate
        "skill_r_cooldown": 600,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 600,
        "ability2_name": "Death Sever",
        "ability2_heal_pct": 0.3,

        "hero_unlock": {
            "name": "Abaddon",
            "title": "Lord of Avernus",
            "role": "True Boss/Knight",
            "cost": 700,
            "hp": 1300,
            "damage": 100,       # avg 80-120
            "speed": 1.4,
            "range": 60,
            "attack_cooldown": 43,
            "color": (100, 220, 240),
            "color_dark": (30, 60, 100),
            "skill_name": "Mist Coil",
            "skill_desc": "Teal projectile + Aphotic Shield",
            "skill_cooldown": 240,
            "skill_damage": 250,
            "skill_range": 100,
            "description": "Fallen knight ditaklukkan",
    },
},

    "alchemist": {
        "name": "Alchemist",
        "title": "The Greed is Good",
        "boss_class": "true",
        "hp": 20000,
        "damage": 90,
        "speed": 0.75,
        "range": 50,       # MELEE
        "attack_cooldown": 46,  # attack speed 1.3
        "radius": 45,
        "gold_reward": 2500,
        "color": (215, 155, 45),      # ogre yellow
        "color_dark": (140, 90, 20),
        "ability_cooldown": 200,
        "ability_damage": 250,
        "ability_range": 180,
        "entrance_text": "ALCHEMIST DUO ARRIVES FOR GOLD!",
        "entrance_color": (100, 220, 40),

        # 4 skills (smart AI)
        "skill_q_damage": 220,      # Acid Spray
        "skill_q_cooldown": 210,
        "skill_w_damage": 320,      # Unstable Concoction
        "skill_w_cooldown": 300,
        "skill_e_damage": 0,        # Chemical Rage (buff, no damage)
        "skill_e_cooldown": 480,
        "skill_r_damage": 550,      # Greevil's Greed ultimate
        "skill_r_cooldown": 720,

        # Legacy fields
        "ability2_cooldown": 480,
        "ability2_name": "Chemical Rage",
        "ability2_heal_pct": 0.15,

        "hero_unlock": {
            "name": "Alchemist",
            "title": "The Greed is Good",
            "role": "True Boss/Bruiser",
            "cost": 750,
            "hp": 1200,
            "damage": 90,
            "speed": 1.3,
            "range": 125,
            "attack_cooldown": 46,
            "color": (215, 155, 45),
            "color_dark": (140, 90, 20),
            "skill_name": "Acid Spray",
            "skill_desc": "Toxic acid + concoction bomb",
            "skill_cooldown": 210,
            "skill_damage": 220,
            "skill_range": 180,
            "description": "Duo alchemist ditaklukkan",
    },
},

    "ancient_apparition": {
        "name": "Ancient Apparition",
        "title": "The Inscrutable",
        "boss_class": "true",
        "hp": 18000,
        "damage": 80,
        "speed": 0.6,          # slower karena ranged
        "range": 150,           # LONG RANGE!
        "attack_cooldown": 46,  # attack speed 1.3
        "radius": 40,
        "gold_reward": 3000,
        "color": (140, 200, 255),      # ice cyan
        "color_dark": (40, 80, 160),   # deep blue
        "ability_cooldown": 200,
        "ability_damage": 300,
        "ability_range": 250,
        "entrance_text": "ANCIENT APPARITION AWAKENS FROM THE VOID!",
        "entrance_color": (140, 200, 255),

        # 4 skills (smart AI - ranged focus)
        "skill_q_damage": 180,      # Ice Vortex (DOT)
        "skill_q_cooldown": 300,
        "skill_w_damage": 250,      # Chilling Touch (line)
        "skill_w_cooldown": 240,
        "skill_e_damage": 450,      # Ice Blast (single target heavy)
        "skill_e_cooldown": 360,
        "skill_r_damage": 600,      # Cold Feet ultimate (line AOE)
        "skill_r_cooldown": 720,

        # Legacy fields
        "ability2_cooldown": 480,
        "ability2_name": "Cold Feet",
        "ability2_heal_pct": 0.1,

        # Ranged AI
        "prefer_distance": 140,     # jarak ideal dari target (<= range!)
        "min_distance": 90,        # jarak minimum (kite kalau lebih dekat)

        "hero_unlock": {
            "name": "Ancient Apparition",
            "title": "The Inscrutable",
            "role": "True Boss/Ice Mage",
            "cost": 800,
            "hp": 900,
            "damage": 80,
            "speed": 1.3,
            "range": 350,
            "attack_cooldown": 46,
            "color": (140, 200, 255),
            "color_dark": (40, 80, 160),
            "skill_name": "Ice Vortex",
            "skill_desc": "Freeze enemies + AOE ice",
            "skill_cooldown": 300,
            "skill_damage": 180,
            "skill_range": 250,
            "description": "Ancient ice spirit ditaklukkan",
    },
},

    "ignis_drachorn": {
        "name": "Ignis Drachorn",
        "title": "The Molten Sovereign",
        "boss_class": "true",
        "hp": 25000,
        "damage": 120,
        "speed": 0.90,
        "range": 55,           # MELEE
        "attack_cooldown": 42,  # fast attack
        "radius": 45,
        "gold_reward": 4000,
        "color": (255, 130, 30),        # fire orange
        "color_dark": (110, 30, 10),    # deep red
        "ability_cooldown": 200,
        "ability_damage": 280,
        "ability_range": 200,
        "entrance_text":
            "IGNIS DRACHORN, THE MOLTEN SOVEREIGN AWAKENS!",
        "entrance_color": (255, 150, 50),

        # 4 skills (smart AI)
        "skill_q_damage": 320,      # Dragon Breath (line/cone)
        "skill_q_cooldown": 240,
        "skill_w_damage": 380,      # Dragon Tail (AOE sweep)
        "skill_w_cooldown": 300,
        "skill_e_damage": 0,        # Dragon Blood (buff/heal)
        "skill_e_cooldown": 420,
        "skill_r_damage": 600,      # Elder Dragon Form ultimate
        "skill_r_cooldown": 780,

        # Legacy fields
        "ability2_cooldown": 480,
        "ability2_name": "Dragon Blood",
        "ability2_heal_pct": 0.2,

        "hero_unlock": {
            "name": "Ignis Drachorn",
            "title": "The Molten Sovereign",
            "role": "True Boss/Dragon Knight",
            "cost": 850,
            "hp": 1400,
            "damage": 110,
            "speed": 1.3,
            "range": 60,
            "attack_cooldown": 42,
            "color": (255, 130, 30),
            "color_dark": (110, 30, 10),
            "skill_name": "Dragon Breath",
            "skill_desc":
                "Fire cone + tail sweep + dragon form",
            "skill_cooldown": 240,
            "skill_damage": 320,
            "skill_range": 200,
            "description":
                "Dragon knight sovereign ditaklukkan",
        },
    },
    "krobellus": {
        "name": "Krobellus",
        "title": "The Death Prophet",
        "boss_class": "true",

        "hp": 18500,
        "damage": 115,
        "speed": 0.82,
        "range": 150,
        "attack_cooldown": 46,
        "radius": 44,
        "gold_reward": 2100,

        "color": (55, 180, 150),
        "color_dark": (38, 16, 75),

        "ability_cooldown": 180,
        "ability_damage": 260,
        "ability_range": 260,

        "ability2_cooldown": 720,
        "ability2_heal_pct": 0.22,

        "entrance_text": (
            "KROBELLLUS, THE DEATH PROPHET, RISES!"
        ),
        "entrance_color": (100, 255, 200),

        # Q - Exorcism
        "skill_q_damage": 280,
        "skill_q_cooldown": 220,

        # W - Silence
        "skill_w_damage": 180,
        "skill_w_cooldown": 300,

        # E - Spirit Siphon
        "skill_e_damage": 230,
        "skill_e_cooldown": 260,

        # R - Crypt Swarm / Reincarnation
        "skill_r_damage": 440,
        "skill_r_cooldown": 680,

        # Ranged AI
        "prefer_distance": 360,
        "min_distance": 220,

        # Unlock sebagai hero
        "hero_unlock": {
            "name": "Krobellus",
            "title": "The Death Prophet",
            "role": "Boss/Spirit Prophet",
            "cost": 1500,

            "hp": 1250,
            "damage": 96,
            "speed": 1.2,
            "range": 120,
            "attack_cooldown": 46,

            "color": (55, 180, 150),
            "color_dark": (38, 16, 75),

            "skill_name": "Exorcism",
            "skill_desc": (
                "Summons spirits and drains enemy life"
            ),
            "skill_cooldown": 220,
            "skill_damage": 280,
            "skill_range": 260,

            "description": (
                "Death Prophet dari Haunted Veil"
            ),
        },
    },

    "kunkka": {
        "name": "Kunkka",
        "title": "The Admiral of the Fleet",
        "boss_class": "true",

        "hp": 22000,
        "damage": 125,
        "speed": 0.85,
        "range": 55,            # MELEE (cutlass)
        "attack_cooldown": 42,  # fast melee attack
        "radius": 45,
        "gold_reward": 2500,

        "color": (40, 130, 200),         # tide blue
        "color_dark": (8, 30, 62),       # naval coat darkest

        "ability_cooldown": 200,
        "ability_damage": 280,
        "ability_range": 200,

        "ability2_cooldown": 600,
        "ability2_name": "Tidebringer's Resolve",
        "ability2_heal_pct": 0.20,

        "entrance_text": (
            "KUNKKA, THE ADMIRAL OF THE FLEET, SETS SAIL!"
        ),
        "entrance_color": (110, 200, 245),

        # Q - Tide Bringer (cleaving water slash)
        "skill_q_damage": 380,
        "skill_q_cooldown": 240,

        # W - X Marks the Spot (mark + delayed burst)
        "skill_w_damage": 300,
        "skill_w_cooldown": 300,

        # E - Ghost Ship (spectral ship AOE)
        "skill_e_damage": 450,
        "skill_e_cooldown": 480,

        # R - Torrent (rising water column ultimate)
        "skill_r_damage": 650,
        "skill_r_cooldown": 720,

        "hero_unlock": {
            "name": "Kunkka",
            "title": "The Admiral of the Fleet",
            "role": "True Boss/Naval Admiral",
            "cost": 900,

            "hp": 1400,
            "damage": 120,
            "speed": 1.3,
            "range": 60,
            "attack_cooldown": 42,

            "color": (40, 130, 200),
            "color_dark": (8, 30, 62),

            "skill_name": "Tide Bringer",
            "skill_desc": (
                "Cleaving water slash + ghost ship + torrent"
            ),
            "skill_cooldown": 240,
            "skill_damage": 380,
            "skill_range": 200,

            "description": (
                "Admiral of the Fleet dari Admiral's Cove"
            ),
        },
    },

    "nyxarath": {
        "name": "Nyxarath",
        "title": "The Soul Eater",
        "boss_class": "true",

        "hp": 26000,
        "damage": 130,
        "speed": 0.85,
        "range": 160,           # RANGED (soul bolt)
        "attack_cooldown": 44,
        "radius": 45,
        "gold_reward": 5000,

        "color": (180, 35, 25),         # fire mid red
        "color_dark": (8, 5, 6),        # shadow black

        "ability_cooldown": 200,
        "ability_damage": 300,
        "ability_range": 220,

        "ability2_cooldown": 600,
        "ability2_name": "Soul Devour",
        "ability2_heal_pct": 0.12,

        "entrance_text": (
            "NYXARATH, THE SOUL EATER, DEVOURS ALL LIGHT!"
        ),
        "entrance_color": (255, 145, 80),

        # Q - Shadowraze (bright red beam forward, line AOE)
        "skill_q_damage": 380,
        "skill_q_cooldown": 240,

        # W - Necromastery (skulls AOE + damage buff)
        "skill_w_damage": 350,
        "skill_w_cooldown": 300,

        # E - Presence of the Dark Lord (aura debuff + heal)
        "skill_e_damage": 0,        # defensive aura, no direct damage
        "skill_e_cooldown": 420,

        # R - Requiem of Souls (massive AOE pillars ultimate)
        "skill_r_damage": 700,
        "skill_r_cooldown": 780,

        # Ranged AI (soul eater keeps distance, casts hellfire)
        # prefer_distance HARUS <= range agar boss bisa attack!
        "prefer_distance": 150,
        "min_distance": 100,

        "hero_unlock": {
            "name": "Nyxarath",
            "title": "The Soul Eater",
            "role": "True Boss/Shadow Fiend",
            "cost": 1000,

            "hp": 1500,
            "damage": 125,
            "speed": 1.3,
            "range": 170,
            "attack_cooldown": 44,

            "color": (180, 35, 25),
            "color_dark": (8, 5, 6),

            "skill_name": "Shadowraze",
            "skill_desc": (
                "Hellfire beam + necromastery + presence + requiem of souls"
            ),
            "skill_cooldown": 240,
            "skill_damage": 380,
            "skill_range": 220,

            "description": (
                "Soul Eater dari Shadow Abyss"
            ),
        },
    },

    "vhorethzir": {
        "name": "Vhoreth'zir",
        "title": "The Nethervenom Wyrm",
        "boss_class": "true",

        "hp": 28000,
        "damage": 140,
        "speed": 0.82,
        "range": 165,           # RANGED (venom spit dari mulut)
        "attack_cooldown": 48,  # HARUS sama dgn default renderer
        "radius": 46,
        "gold_reward": 5500,

        "color": (140, 190, 35),        # toxic mid green
        "color_dark": (5, 20, 10),      # scale darkest

        "ability_cooldown": 200,
        "ability_damage": 320,
        "ability_range": 230,

        "ability2_cooldown": 600,
        "ability2_name": "Nether Regeneration",
        "ability2_heal_pct": 0.12,

        "entrance_text": (
            "VHORETH'ZIR, THE NETHERVENOM WYRM, POISONS THE SKY!"
        ),
        "entrance_color": (200, 245, 80),

        # Q - Poison Attack (venom orb, single target + splash)
        "skill_q_damage": 400,
        "skill_q_cooldown": 240,

        # W - Nethertoxin (racun area di tanah)
        "skill_w_damage": 360,
        "skill_w_cooldown": 300,

        # E - Corrosive Skin (aura defensif + slow, tanpa damage)
        "skill_e_damage": 0,
        "skill_e_cooldown": 420,

        # R - Viper Strike (beam dari langit, ultimate)
        "skill_r_damage": 720,
        "skill_r_cooldown": 780,

        # Ranged AI. prefer_distance HARUS <= range agar boss bisa attack!
        "prefer_distance": 150,
        "min_distance": 105,

        "hero_unlock": {
            "name": "Vhoreth'zir",
            "title": "The Nethervenom Wyrm",
            "role": "True Boss/Venom Drake",
            "cost": 1000,

            "hp": 1550,
            "damage": 130,
            "speed": 1.28,
            "range": 175,
            "attack_cooldown": 48,

            "color": (140, 190, 35),
            "color_dark": (5, 20, 10),

            "skill_name": "Viper Strike",
            "skill_desc": (
                "Poison attack + nethertoxin + corrosive skin + viper strike"
            ),
            "skill_cooldown": 240,
            "skill_damage": 400,
            "skill_range": 230,

            "description": (
                "Nethervenom Wyrm dari Nethervenom Expanse"
            ),
        },
    },

    "naraka": {
        "name": "Naraka",
        "title": "The Lost Soul",
        "boss_class": "true",
        "hp": 26000,
        "damage": 145,
        "speed": 0.95,
        "range": 65,            # MELEE (cursed dark warrior)
        "attack_cooldown": 40,
        "radius": 46,
        "gold_reward": 3200,
        "color": (110, 220, 235),       # cyan cursed energy
        "color_dark": (15, 40, 60),
        "ability_cooldown": 180,
        "ability_damage": 380,
        "ability_range": 240,
        "entrance_text": "NARAKA, THE LOST SOUL, RISES FROM THE ABYSS!",
        "entrance_color": (110, 220, 235),

        # 4 skills (smart AI - executioner style)
        "skill_q_damage": 380,      # Chaos Strike
        "skill_q_cooldown": 220,
        "skill_w_damage": 400,      # Shadowstep
        "skill_w_cooldown": 260,
        "skill_e_damage": 420,      # Chain Hammer (AOE)
        "skill_e_cooldown": 300,
        "skill_r_damage": 700,      # Final Execution (ultimate)
        "skill_r_cooldown": 640,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 600,
        "ability2_name": "Final Execution",
        "ability2_heal_pct": 0.35,

        "hero_unlock": {
            "name": "Naraka",
            "title": "The Lost Soul",
            "role": "True Boss/Cursed Warrior",
            "cost": 2000,
            "hp": 1600,
            "damage": 135,
            "speed": 1.35,
            "range": 75,
            "attack_cooldown": 40,
            "color": (110, 220, 235),
            "color_dark": (15, 40, 60),
            "skill_name": "Chaos Strike",
            "skill_desc": "Chaos strike + shadowstep + chain hammer + final execution",
            "skill_cooldown": 220,
            "skill_damage": 380,
            "skill_range": 140,
            "description": "Jiwa terkutuk dari Level 9",
        },
    },

    "aurethzar": {
        "name": "Aureth'zar",
        "title": "The Radiant Dawn",
        "boss_class": "true",
        "hp": 28000,
        "damage": 150,
        "speed": 1.0,
        "range": 190,           # RANGED (solar archer)
        "attack_cooldown": 44,
        "radius": 48,
        "gold_reward": 3400,
        "color": (240, 195, 80),       # gold radiant
        "color_dark": (95, 65, 15),
        "ability_cooldown": 180,
        "ability_damage": 400,
        "ability_range": 260,
        "entrance_text": "AURETH'ZAR, THE RADIANT DAWN, ILLUMINATES THE SKY!",
        "entrance_color": (255, 225, 140),

        # 4 skills (smart AI - solar archer)
        "skill_q_damage": 400,      # Marksman (enhanced arrow)
        "skill_q_cooldown": 210,
        "skill_w_damage": 440,      # Piercing Arrow (line)
        "skill_w_cooldown": 260,
        "skill_e_damage": 380,      # Frost Shot (ice arrow)
        "skill_e_cooldown": 280,
        "skill_r_damage": 740,      # Distant Thunder (arrow rain)
        "skill_r_cooldown": 640,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 600,
        "ability2_name": "Distant Thunder",
        "ability2_heal_pct": 0.35,

        # Ranged AI (kite behavior)
        "prefer_distance": 180,
        "min_distance": 120,

        "hero_unlock": {
            "name": "Aureth'zar",
            "title": "The Radiant Dawn",
            "role": "True Boss/Solar Archer",
            "cost": 2100,
            "hp": 1650,
            "damage": 140,
            "speed": 1.4,
            "range": 190,
            "attack_cooldown": 44,
            "color": (240, 195, 80),
            "color_dark": (95, 65, 15),
            "skill_name": "Marksman",
            "skill_desc": "Marksman + piercing arrow + frost shot + distant thunder",
            "skill_cooldown": 210,
            "skill_damage": 400,
            "skill_range": 200,
            "description": "Pemanah surya dari Level 10",
        },
    },

    "thalakryon": {
        "name": "Thalakryon",
        "title": "The Abyssal Sovereign",
        "boss_class": "true",
        "hp": 30000,
        "damage": 155,
        "speed": 1.0,
        "range": 70,            # MELEE (abyssal trident)
        "attack_cooldown": 40,
        "radius": 50,
        "gold_reward": 3600,
        "color": (50, 130, 190),       # abyssal blue
        "color_dark": (5, 20, 45),
        "ability_cooldown": 180,
        "ability_damage": 420,
        "ability_range": 260,
        "entrance_text": "THALAKRYON, THE ABYSSAL SOVEREIGN, RISES FROM THE DEEP!",
        "entrance_color": (140, 210, 240),

        # 4 skills (smart AI - abyssal sovereign)
        "skill_q_damage": 420,      # Abyssal Bolt
        "skill_q_cooldown": 210,
        "skill_w_damage": 0,        # Aqua Shield (defensive)
        "skill_w_cooldown": 260,
        "skill_e_damage": 440,      # Tidal Rage (AOE)
        "skill_e_cooldown": 300,
        "skill_r_damage": 760,      # Metamorph (ultimate)
        "skill_r_cooldown": 640,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 600,
        "ability2_name": "Metamorph",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Thalakryon",
            "title": "The Abyssal Sovereign",
            "role": "True Boss/Mermidon",
            "cost": 2200,
            "hp": 1750,
            "damage": 145,
            "speed": 1.4,
            "range": 80,
            "attack_cooldown": 40,
            "color": (50, 130, 190),
            "color_dark": (5, 20, 45),
            "skill_name": "Abyssal Bolt",
            "skill_desc": "Abyssal bolt + aqua shield + tidal rage + metamorph",
            "skill_cooldown": 210,
            "skill_damage": 420,
            "skill_range": 150,
            "description": "Penguasa abisal dari Level 11",
        },
    },

    "nazulmor": {
        "name": "Nazulmor",
        "title": "The Deepborn Herald",
        "boss_class": "true",
        "hp": 32000,
        "damage": 160,
        "speed": 0.95,
        "range": 75,            # MELEE (eldritch tentacle)
        "attack_cooldown": 40,
        "radius": 52,
        "gold_reward": 3800,
        "color": (45, 110, 105),       # teal eldritch
        "color_dark": (5, 20, 25),
        "ability_cooldown": 180,
        "ability_damage": 440,
        "ability_range": 270,
        "entrance_text": "NAZULMOR, THE DEEPBORN HERALD, WHISPERS FROM THE VOID!",
        "entrance_color": (120, 220, 240),

        # 4 skills (smart AI - eldritch herald)
        "skill_q_damage": 440,      # Typhoon
        "skill_q_cooldown": 210,
        "skill_w_damage": 0,        # Aqua Shield (defensive)
        "skill_w_cooldown": 260,
        "skill_e_damage": 460,      # Tidal Rage (AOE)
        "skill_e_cooldown": 300,
        "skill_r_damage": 800,      # Chaotic (ultimate)
        "skill_r_cooldown": 640,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 600,
        "ability2_name": "Chaotic",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Nazulmor",
            "title": "The Deepborn Herald",
            "role": "True Boss/Eldritch",
            "cost": 2300,
            "hp": 1800,
            "damage": 148,
            "speed": 1.4,
            "range": 85,
            "attack_cooldown": 40,
            "color": (45, 110, 105),
            "color_dark": (5, 20, 25),
            "skill_name": "Typhoon",
            "skill_desc": "Typhoon + aqua shield + tidal rage + chaotic",
            "skill_cooldown": 210,
            "skill_damage": 440,
            "skill_range": 150,
            "description": "Herald dari kedalaman Level 12",
        },
    },

    "solvarin": {
        "name": "Solvarin",
        "title": "The Holy Paladin Warden",
        "boss_class": "true",
        "hp": 34000,
        "damage": 165,
        "speed": 0.95,
        "range": 75,            # MELEE (holy warhammer)
        "attack_cooldown": 42,
        "radius": 54,
        "gold_reward": 4000,
        "color": (215, 220, 230),       # silver armor
        "color_dark": (35, 40, 50),
        "ability_cooldown": 180,
        "ability_damage": 460,
        "ability_range": 280,
        "entrance_text": "SOLVARIN, THE HOLY PALADIN WARDEN, DESCENDS IN LIGHT!",
        "entrance_color": (250, 252, 255),

        # 4 skills (smart AI - holy paladin)
        "skill_q_damage": 460,      # Purification
        "skill_q_cooldown": 210,
        "skill_w_damage": 480,      # Repel
        "skill_w_cooldown": 270,
        "skill_e_damage": 0,        # Degen Aura (defensive DOT)
        "skill_e_cooldown": 300,
        "skill_r_damage": 840,      # Guardian (ultimate)
        "skill_r_cooldown": 640,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 600,
        "ability2_name": "Guardian",
        "ability2_heal_pct": 0.45,

        "hero_unlock": {
            "name": "Solvarin",
            "title": "The Holy Paladin Warden",
            "role": "True Boss/Paladin",
            "cost": 2400,
            "hp": 1850,
            "damage": 152,
            "speed": 1.4,
            "range": 85,
            "attack_cooldown": 42,
            "color": (215, 220, 230),
            "color_dark": (35, 40, 50),
            "skill_name": "Purification",
            "skill_desc": "Purification + repel + degen aura + guardian",
            "skill_cooldown": 210,
            "skill_damage": 460,
            "skill_range": 150,
            "description": "Paladin suci dari Level 13",
        },
    },
    "pyraethis": {
        "name": "Pyraethis",
        "title": "The Eternal Firebird",
        "boss_class": "true",
        "hp": 35000,
        "damage": 175,
        "speed": 1.0,
        "range": 300,           # RANGED (firebird)
        "attack_cooldown": 44,
        "radius": 56,
        "gold_reward": 4200,
        "color": (255, 140, 30),       # phoenix feather light
        "color_dark": (110, 30, 10),
        "ability_cooldown": 185,
        "ability_damage": 480,
        "ability_range": 300,
        "entrance_text": "PYRAETHIS, THE ETERNAL FIREBIRD, RISES IN FLAMES!",
        "entrance_color": (255, 200, 70),

        # 4 skills (smart AI - eternal firebird)
        "skill_q_damage": 480,      # Icarus Dive
        "skill_q_cooldown": 220,
        "skill_w_damage": 500,      # Fire Spirits (AOE)
        "skill_w_cooldown": 280,
        "skill_e_damage": 460,      # Sun Ray (AOE beam)
        "skill_e_cooldown": 310,
        "skill_r_damage": 900,      # Supernova (ultimate)
        "skill_r_cooldown": 660,

        # Ranged AI (kite behavior)
        "prefer_distance": 260,
        "min_distance": 140,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 600,
        "ability2_name": "Supernova",
        "ability2_heal_pct": 0.35,

        "hero_unlock": {
            "name": "Pyraethis",
            "title": "The Eternal Firebird",
            "role": "True Boss/Firebird",
            "cost": 2500,
            "hp": 1900,
            "damage": 160,
            "speed": 1.35,
            "range": 270,
            "attack_cooldown": 44,
            "color": (255, 140, 30),
            "color_dark": (110, 30, 10),
            "skill_name": "Icarus Dive",
            "skill_desc": "Icarus dive + fire spirits + sun ray + supernova",
            "skill_cooldown": 220,
            "skill_damage": 480,
            "skill_range": 160,
            "description": "Burung api abadi dari Level 14",
        },
    },
    "yamako": {
        "name": "Yamako",
        "title": "The Primordial Woodshaper",
        "boss_class": "true",
        "hp": 36000,
        "damage": 180,
        "speed": 1.0,
        "range": 85,            # MELEE (woodshaper blade)
        "attack_cooldown": 42,
        "radius": 58,
        "gold_reward": 4400,
        "color": (85, 140, 90),        # primordial robe green
        "color_dark": (18, 45, 22),
        "ability_cooldown": 190,
        "ability_damage": 500,
        "ability_range": 300,
        "entrance_text": "YAMAKO, THE PRIMORDIAL WOODSHAPER, AWAKENS THE GROVE!",
        "entrance_color": (140, 190, 140),

        # 4 skills (smart AI - primordial woodshaper)
        "skill_q_damage": 500,      # Deep Forest
        "skill_q_cooldown": 225,
        "skill_w_damage": 520,      # Wood Creation (AOE)
        "skill_w_cooldown": 285,
        "skill_e_damage": 480,      # Wood Golem (AOE)
        "skill_e_cooldown": 315,
        "skill_r_damage": 950,      # Kannon (ultimate)
        "skill_r_cooldown": 670,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 600,
        "ability2_name": "Kannon",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Yamako",
            "title": "The Primordial Woodshaper",
            "role": "True Boss/Woodshaper",
            "cost": 2600,
            "hp": 1950,
            "damage": 165,
            "speed": 1.35,
            "range": 95,
            "attack_cooldown": 42,
            "color": (85, 140, 90),
            "color_dark": (18, 45, 22),
            "skill_name": "Deep Forest",
            "skill_desc": "Deep forest + wood creation + wood golem + kannon",
            "skill_cooldown": 225,
            "skill_damage": 500,
            "skill_range": 160,
            "description": "Pembentuk kayu purba dari Level 15",
        },
    },
    "seiryukong": {
        "name": "Seiryukong",
        "title": "The Celestial Simian",
        "boss_class": "true",
        "hp": 37000,
        "damage": 185,
        "speed": 1.05,
        "range": 90,            # MELEE (celestial staff)
        "attack_cooldown": 42,
        "radius": 60,
        "gold_reward": 4600,
        "color": (240, 195, 80),       # celestial gold armor
        "color_dark": (95, 65, 20),
        "ability_cooldown": 195,
        "ability_damage": 520,
        "ability_range": 300,
        "entrance_text": "SEIRYUKONG, THE CELESTIAL SIMIAN, DESCENDS FROM THE CLOUDS!",
        "entrance_color": (255, 225, 130),

        # 4 skills (smart AI - celestial simian)
        "skill_q_damage": 520,      # Boundless
        "skill_q_cooldown": 230,
        "skill_w_damage": 540,      # Tree Dance (AOE)
        "skill_w_cooldown": 290,
        "skill_e_damage": 500,      # Jingu Soldiers (AOE)
        "skill_e_cooldown": 320,
        "skill_r_damage": 1000,     # Wukong (ultimate)
        "skill_r_cooldown": 680,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 600,
        "ability2_name": "Wukong",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Seiryukong",
            "title": "The Celestial Simian",
            "role": "True Boss/Celestial Simian",
            "cost": 2700,
            "hp": 2000,
            "damage": 172,
            "speed": 1.4,
            "range": 100,
            "attack_cooldown": 42,
            "color": (240, 195, 80),
            "color_dark": (95, 65, 20),
            "skill_name": "Boundless",
            "skill_desc": "Boundless + tree dance + jingu soldiers + wukong",
            "skill_cooldown": 230,
            "skill_damage": 520,
            "skill_range": 160,
            "description": "Raja kera langit dari Level 16",
        },
    },
    "nyxareth": {
        "name": "Nyxareth",
        "title": "The Cosmic Sovereign",
        "boss_class": "true",
        "hp": 38000,
        "damage": 190,
        "speed": 1.0,
        "range": 290,           # RANGED (cosmic mage)
        "attack_cooldown": 45,
        "radius": 60,
        "gold_reward": 4800,
        "color": (135, 55, 220),       # cosmic purple
        "color_dark": (10, 5, 25),
        "ability_cooldown": 200,
        "ability_damage": 540,
        "ability_range": 300,
        "entrance_text": "NYXARETH, THE COSMIC SOVEREIGN, UNRAVELS THE STARS!",
        "entrance_color": (200, 130, 255),

        # 4 skills (smart AI - cosmic sovereign)
        # Catatan: renderer nyxareth pakai key skill "1"-"4"
        # (1=Starsplit, 2=Realworld, 3=Spacetime, 4=Astro Realm),
        # jadi smart AI & cast hero menyetel active_skill ke "1"-"4".
        "skill_q_damage": 540,      # Starsplit
        "skill_q_cooldown": 235,
        "skill_w_damage": 560,      # Realworld (AOE)
        "skill_w_cooldown": 295,
        "skill_e_damage": 520,      # Spacetime (AOE)
        "skill_e_cooldown": 325,
        "skill_r_damage": 1050,     # Astro Realm (ultimate)
        "skill_r_cooldown": 690,

        # Ranged AI (kite behavior)
        "prefer_distance": 260,
        "min_distance": 140,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 600,
        "ability2_name": "Astro Realm",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Nyxareth",
            "title": "The Cosmic Sovereign",
            "role": "True Boss/Cosmic Mage",
            "cost": 2800,
            "hp": 2050,
            "damage": 176,
            "speed": 1.4,
            "range": 270,
            "attack_cooldown": 45,
            "color": (135, 55, 220),
            "color_dark": (10, 5, 25),
            "skill_name": "Starsplit",
            "skill_desc": "Starsplit + realworld + spacetime + astro realm",
            "skill_cooldown": 235,
            "skill_damage": 540,
            "skill_range": 160,
            "description": "Penguasa kosmik dari Level 17",
        },
    },
    "aurelion": {
        "name": "Aurelion",
        "title": "The Golden Sovereign",
        "boss_class": "true",
        "hp": 39000,
        "damage": 195,
        "speed": 1.0,
        "range": 90,            # MELEE (royal spear)
        "attack_cooldown": 44,
        "radius": 62,
        "gold_reward": 5000,
        "color": (245, 215, 95),       # golden sovereign armor
        "color_dark": (55, 40, 5),
        "ability_cooldown": 205,
        "ability_damage": 560,
        "ability_range": 300,
        "entrance_text": "AURELION, THE GOLDEN SOVEREIGN, CLAIMS THE BATTLEFIELD!",
        "entrance_color": (255, 245, 180),

        # 4 skills (smart AI - golden sovereign)
        "skill_q_damage": 560,      # Call Courage
        "skill_q_cooldown": 240,
        "skill_w_damage": 580,      # Guardian Assault (AOE)
        "skill_w_cooldown": 300,
        "skill_e_damage": 540,      # King's Command (AOE)
        "skill_e_cooldown": 330,
        "skill_r_damage": 1100,     # King's Summon (ultimate)
        "skill_r_cooldown": 700,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 600,
        "ability2_name": "King's Summon",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Aurelion",
            "title": "The Golden Sovereign",
            "role": "True Boss/Royal King",
            "cost": 2900,
            "hp": 2100,
            "damage": 182,
            "speed": 1.4,
            "range": 100,
            "attack_cooldown": 44,
            "color": (245, 215, 95),
            "color_dark": (55, 40, 5),
            "skill_name": "Call Courage",
            "skill_desc": "Call courage + guardian assault + king's command + king's summon",
            "skill_cooldown": 240,
            "skill_damage": 560,
            "skill_range": 160,
            "description": "Raja emas dari Level 18",
        },
    },
    "vaelindra": {
        "name": "Vaelindra",
        "title": "The Violet Sovereign",
        "boss_class": "true",
        "hp": 40000,
        "damage": 200,
        "speed": 1.0,
        "range": 300,           # RANGED (violet mage)
        "attack_cooldown": 44,
        "radius": 64,
        "gold_reward": 5200,
        "color": (155, 100, 220),      # violet gown
        "color_dark": (40, 15, 80),
        "ability_cooldown": 210,
        "ability_damage": 580,
        "ability_range": 310,
        "entrance_text": "VAELINDRA, THE VIOLET SOVEREIGN, BECKONS FROM BEYOND!",
        "entrance_color": (200, 160, 245),

        # 4 skills (smart AI - violet sovereign)
        "skill_q_damage": 580,      # Energy Wave
        "skill_q_cooldown": 245,
        "skill_w_damage": 600,      # Space Ring (AOE)
        "skill_w_cooldown": 305,
        "skill_e_damage": 560,      # Violet Requiem (AOE)
        "skill_e_cooldown": 335,
        "skill_r_damage": 1150,     # Realm (ultimate)
        "skill_r_cooldown": 710,

        # Ranged AI (kite behavior)
        "prefer_distance": 260,
        "min_distance": 140,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 600,
        "ability2_name": "Realm",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Vaelindra",
            "title": "The Violet Sovereign",
            "role": "True Boss/Violet Mage",
            "cost": 3000,
            "hp": 2150,
            "damage": 190,
            "speed": 1.4,
            "range": 280,
            "attack_cooldown": 44,
            "color": (155, 100, 220),
            "color_dark": (40, 15, 80),
            "skill_name": "Energy Wave",
            "skill_desc": "Energy wave + space ring + violet requiem + realm",
            "skill_cooldown": 245,
            "skill_damage": 580,
            "skill_range": 160,
            "description": "Penguasa violet dari Level 19",
        },
    },
    "morthraxis": {
        "name": "Morthraxis",
        "title": "The Crimson Sovereign",
        "boss_class": "true",
        "hp": 41000,
        "damage": 210,
        "speed": 1.05,
        "range": 290,           # RANGED (vampire bats)
        "attack_cooldown": 44,
        "radius": 66,
        "gold_reward": 5400,
        "color": (220, 50, 90),        # crimson blood
        "color_dark": (80, 10, 25),
        "ability_cooldown": 215,
        "ability_damage": 600,
        "ability_range": 310,
        "entrance_text": "MORTHRAXIS, THE CRIMSON SOVEREIGN, THIRSTS FOR THE NIGHT!",
        "entrance_color": (255, 90, 130),

        # 4 skills (smart AI - crimson sovereign)
        "skill_q_damage": 600,      # Bat Impale
        "skill_q_cooldown": 250,
        "skill_w_damage": 620,      # Sanguine (AOE)
        "skill_w_cooldown": 310,
        "skill_e_damage": 580,      # Phantom Mob (AOE)
        "skill_e_cooldown": 340,
        "skill_r_damage": 1200,     # Baleful (ultimate)
        "skill_r_cooldown": 720,

        # Ranged AI (kite behavior)
        "prefer_distance": 260,
        "min_distance": 140,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 600,
        "ability2_name": "Baleful",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Morthraxis",
            "title": "The Crimson Sovereign",
            "role": "True Boss/Vampire Lord",
            "cost": 3100,
            "hp": 2200,
            "damage": 198,
            "speed": 1.4,
            "range": 270,
            "attack_cooldown": 44,
            "color": (220, 50, 90),
            "color_dark": (80, 10, 25),
            "skill_name": "Bat Impale",
            "skill_desc": "Bat impale + sanguine + phantom mob + baleful",
            "skill_cooldown": 250,
            "skill_damage": 600,
            "skill_range": 160,
            "description": "Raja vampir merah dari Level 20",
        },
    },
    "nexthyrius": {
        "name": "Nexthyrius",
        "title": "The Chained Hollow",
        "boss_class": "true",
        "hp": 45000,
        "damage": 230,
        "speed": 1.0,
        "range": 300,           # RANGED (spectral chains)
        "attack_cooldown": 46,
        "radius": 68,
        "gold_reward": 5800,
        "color": (0, 180, 200),        # spectral teal
        "color_dark": (2, 8, 12),
        "ability_cooldown": 225,
        "ability_damage": 650,
        "ability_range": 330,
        "entrance_text": "NEXTHYRIUS, THE CHAINED HOLLOW, DRAGS ALL SOULS INTO THE VOID!",
        "entrance_color": (80, 240, 200),

        # 4 skills (smart AI - chained hollow)
        "skill_q_damage": 650,      # Chain Hook
        "skill_q_cooldown": 260,
        "skill_w_damage": 660,      # Soul Lantern (AOE)
        "skill_w_cooldown": 320,
        "skill_e_damage": 640,      # Spectral Reap (AOE)
        "skill_e_cooldown": 350,
        "skill_r_damage": 1300,     # Soul Prison (ultimate)
        "skill_r_cooldown": 740,

        # Ranged AI (kite behavior)
        "prefer_distance": 270,
        "min_distance": 150,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 620,
        "ability2_name": "Soul Prison",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Nexthyrius",
            "title": "The Chained Hollow",
            "role": "True Boss/Spectral Chain Warden",
            "cost": 3200,
            "hp": 2350,
            "damage": 210,
            "speed": 1.4,
            "range": 280,
            "attack_cooldown": 46,
            "color": (0, 180, 200),
            "color_dark": (2, 8, 12),
            "skill_name": "Chain Hook",
            "skill_desc": "Chain hook + soul lantern + spectral reap + soul prison",
            "skill_cooldown": 260,
            "skill_damage": 650,
            "skill_range": 170,
            "description": "Penjaga rantai spectral dari Level 21",
        },
    },
    "molgravar": {
        "name": "Molgravar",
        "title": "The Colossus of the Sundered Peak",
        "boss_class": "true",
        "hp": 47000,
        "damage": 240,
        "speed": 0.9,
        "range": 120,           # MELEE (seismic slam, colossus)
        "attack_cooldown": 50,
        "radius": 72,
        "gold_reward": 6100,
        "color": (230, 140, 50),       # lava orange
        "color_dark": (18, 12, 8),
        "ability_cooldown": 235,
        "ability_damage": 680,
        "ability_range": 340,
        "entrance_text": "MOLGRAVAR, THE COLOSSUS OF THE SUNDERED PEAK, SHATTERS THE EARTH!",
        "entrance_color": (255, 190, 80),

        # 4 skills (smart AI - sundered colossus)
        "skill_q_damage": 680,      # Seismic Slam
        "skill_q_cooldown": 270,
        "skill_w_damage": 690,      # Lava Fissure (AOE)
        "skill_w_cooldown": 330,
        "skill_e_damage": 670,      # Boulder Toss (AOE)
        "skill_e_cooldown": 360,
        "skill_r_damage": 1350,     # Unstoppable (ultimate)
        "skill_r_cooldown": 760,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 640,
        "ability2_name": "Unstoppable",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Molgravar",
            "title": "The Colossus of the Sundered Peak",
            "role": "True Boss/Stone Golem",
            "cost": 3300,
            "hp": 2450,
            "damage": 220,
            "speed": 1.3,
            "range": 130,
            "attack_cooldown": 50,
            "color": (230, 140, 50),
            "color_dark": (18, 12, 8),
            "skill_name": "Seismic Slam",
            "skill_desc": "Seismic slam + lava fissure + boulder toss + unstoppable",
            "skill_cooldown": 270,
            "skill_damage": 680,
            "skill_range": 180,
            "description": "Golem batu raksasa dari Level 22",
        },
    },
    "seraphienne": {
        "name": "Seraphienne",
        "title": "The Empyrean Executioner",
        "boss_class": "true",
        "hp": 49000,
        "damage": 245,
        "speed": 1.0,
        "range": 310,           # RANGED (divine light)
        "attack_cooldown": 48,
        "radius": 70,
        "gold_reward": 6400,
        "color": (250, 215, 105),      # divine gold
        "color_dark": (35, 20, 3),
        "ability_cooldown": 240,
        "ability_damage": 700,
        "ability_range": 350,
        "entrance_text": "SERAPHIENNE, THE EMPYREAN EXECUTIONER, DESCENDS IN JUDGMENT!",
        "entrance_color": (255, 240, 170),

        # 4 skills (smart AI - empyrean executioner)
        "skill_q_damage": 700,      # Divine Verdict
        "skill_q_cooldown": 280,
        "skill_w_damage": 710,      # Holy Radiance (AOE)
        "skill_w_cooldown": 340,
        "skill_e_damage": 690,      # Seraph Wings (AOE)
        "skill_e_cooldown": 370,
        "skill_r_damage": 1400,     # Divine Intervention (ultimate)
        "skill_r_cooldown": 780,

        # Ranged AI (kite behavior)
        "prefer_distance": 280,
        "min_distance": 160,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 660,
        "ability2_name": "Divine Intervention",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Seraphienne",
            "title": "The Empyrean Executioner",
            "role": "True Boss/Angelic Warrior",
            "cost": 3400,
            "hp": 2500,
            "damage": 225,
            "speed": 1.4,
            "range": 290,
            "attack_cooldown": 48,
            "color": (250, 215, 105),
            "color_dark": (35, 20, 3),
            "skill_name": "Divine Verdict",
            "skill_desc": "Divine verdict + holy radiance + seraph wings + divine intervention",
            "skill_cooldown": 280,
            "skill_damage": 700,
            "skill_range": 190,
            "description": "Eksekutor surgawi dari Level 23",
        },
    },
    "solareth": {
        "name": "Solareth",
        "title": "The Sunborn Herald",
        "boss_class": "true",
        "hp": 51000,
        "damage": 250,
        "speed": 1.0,
        "range": 130,           # MELEE (solar greatsword, engage tank)
        "attack_cooldown": 46,
        "radius": 72,
        "gold_reward": 6700,
        "color": (255, 210, 90),       # solar gold
        "color_dark": (55, 30, 5),
        "ability_cooldown": 245,
        "ability_damage": 720,
        "ability_range": 340,
        "entrance_text": "SOLARETH, THE SUNBORN HERALD, BLINDS THE WORLD WITH DAWN!",
        "entrance_color": (255, 240, 160),

        # 4 skills (smart AI - sunborn herald)
        "skill_q_damage": 720,      # Solar Cleave
        "skill_q_cooldown": 285,
        "skill_w_damage": 730,      # Radiant Aegis (AOE)
        "skill_w_cooldown": 345,
        "skill_e_damage": 710,      # Sunflare Charge (AOE)
        "skill_e_cooldown": 375,
        "skill_r_damage": 1450,     # Dawn's Judgment (ultimate)
        "skill_r_cooldown": 790,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 670,
        "ability2_name": "Dawn's Judgment",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Solareth",
            "title": "The Sunborn Herald",
            "role": "True Boss/Solar Warrior",
            "cost": 3500,
            "hp": 2600,
            "damage": 230,
            "speed": 1.4,
            "range": 140,
            "attack_cooldown": 46,
            "color": (255, 210, 90),
            "color_dark": (55, 30, 5),
            "skill_name": "Solar Cleave",
            "skill_desc": "Solar cleave + radiant aegis + sunflare charge + dawn's judgment",
            "skill_cooldown": 285,
            "skill_damage": 720,
            "skill_range": 190,
            "description": "Herald matahari dari Level 24",
        },
    },
    "okeanora": {
        "name": "Okeanora",
        "title": "The Deepborn Oracle",
        "boss_class": "true",
        "hp": 53000,
        "damage": 260,
        "speed": 1.0,
        "range": 140,           # MELEE (kraken tentacles)
        "attack_cooldown": 48,
        "radius": 72,
        "gold_reward": 7000,
        "color": (95, 245, 220),       # kraken teal
        "color_dark": (5, 25, 25),
        "ability_cooldown": 250,
        "ability_damage": 740,
        "ability_range": 345,
        "entrance_text": "OKEANORA, THE DEEPBORN ORACLE, SUMMONS THE KRAKEN'S WRATH!",
        "entrance_color": (170, 255, 240),

        # 4 skills (smart AI - deepborn oracle)
        "skill_q_damage": 740,      # Tidal Verdict
        "skill_q_cooldown": 290,
        "skill_w_damage": 750,      # Kraken's Embrace (AOE)
        "skill_w_cooldown": 350,
        "skill_e_damage": 730,      # Abyssal Surge (AOE)
        "skill_e_cooldown": 380,
        "skill_r_damage": 1500,     # Leviathan's Wrath (ultimate)
        "skill_r_cooldown": 800,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 680,
        "ability2_name": "Leviathan's Wrath",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Okeanora",
            "title": "The Deepborn Oracle",
            "role": "True Boss/Kraken Priestess",
            "cost": 3600,
            "hp": 2650,
            "damage": 240,
            "speed": 1.35,
            "range": 150,
            "attack_cooldown": 48,
            "color": (95, 245, 220),
            "color_dark": (5, 25, 25),
            "skill_name": "Tidal Verdict",
            "skill_desc": "Tidal verdict + kraken's embrace + abyssal surge + leviathan's wrath",
            "skill_cooldown": 290,
            "skill_damage": 740,
            "skill_range": 195,
            "description": "Peramal laut dalam dari Level 25",
        },
    },
    "vaelmyrra": {
        "name": "Vaelmyrra",
        "title": "The Crimson Matriarch",
        "boss_class": "true",
        "hp": 55000,
        "damage": 270,
        "speed": 1.05,
        "range": 150,           # MELEE (obsidian warblade)
        "attack_cooldown": 46,
        "radius": 74,
        "gold_reward": 7300,
        "color": (225, 55, 70),       # blood crimson
        "color_dark": (8, 5, 10),
        "ability_cooldown": 255,
        "ability_damage": 760,
        "ability_range": 350,
        "entrance_text": "VAELMYRRA, THE CRIMSON MATRIARCH, CLAIMS THE BLOOD THRONE!",
        "entrance_color": (255, 100, 100),

        # 4 skills (smart AI - crimson matriarch)
        "skill_q_damage": 760,      # Blood Verdict
        "skill_q_cooldown": 295,
        "skill_w_damage": 770,      # Obsidian Aegis (AOE)
        "skill_w_cooldown": 355,
        "skill_e_damage": 750,      # Crimson Charge (AOE)
        "skill_e_cooldown": 385,
        "skill_r_damage": 1550,     # Matriarch's Wrath (ultimate)
        "skill_r_cooldown": 810,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 690,
        "ability2_name": "Matriarch's Wrath",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Vaelmyrra",
            "title": "The Crimson Matriarch",
            "role": "True Boss/Obsidian Warlord",
            "cost": 3700,
            "hp": 2700,
            "damage": 245,
            "speed": 1.4,
            "range": 160,
            "attack_cooldown": 46,
            "color": (225, 55, 70),
            "color_dark": (8, 5, 10),
            "skill_name": "Blood Verdict",
            "skill_desc": "Blood verdict + obsidian aegis + crimson charge + matriarch's wrath",
            "skill_cooldown": 295,
            "skill_damage": 760,
            "skill_range": 200,
            "description": "Matriark darah dari Level 26",
        },
    },
    "zarethyr": {
        "name": "Zarethyr",
        "title": "The Astral Sovereign",
        "boss_class": "true",
        "hp": 57000,
        "damage": 280,
        "speed": 1.05,
        "range": 320,           # RANGED (cosmic magic)
        "attack_cooldown": 48,
        "radius": 74,
        "gold_reward": 7600,
        "color": (130, 200, 255),      # cosmic blue
        "color_dark": (5, 8, 25),
        "ability_cooldown": 260,
        "ability_damage": 780,
        "ability_range": 360,
        "entrance_text": "ZARETHYR, THE ASTRAL SOVEREIGN, COMMANDS THE COSMOS!",
        "entrance_color": (200, 235, 255),

        # 4 skills (smart AI - astral sovereign)
        "skill_q_damage": 780,      # Astral Bolt
        "skill_q_cooldown": 300,
        "skill_w_damage": 790,      # Cosmic Veil (AOE)
        "skill_w_cooldown": 360,
        "skill_e_damage": 770,      # Star Surge (AOE)
        "skill_e_cooldown": 390,
        "skill_r_damage": 1600,     # Sovereign's Nova (ultimate)
        "skill_r_cooldown": 820,

        # Ranged AI (kite behavior)
        "prefer_distance": 290,
        "min_distance": 170,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 700,
        "ability2_name": "Sovereign's Nova",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Zarethyr",
            "title": "The Astral Sovereign",
            "role": "True Boss/Cosmic Mage",
            "cost": 3800,
            "hp": 2750,
            "damage": 255,
            "speed": 1.4,
            "range": 300,
            "attack_cooldown": 48,
            "color": (130, 200, 255),
            "color_dark": (5, 8, 25),
            "skill_name": "Astral Bolt",
            "skill_desc": "Astral bolt + cosmic veil + star surge + sovereign's nova",
            "skill_cooldown": 300,
            "skill_damage": 780,
            "skill_range": 205,
            "description": "Penguasa kosmos dari Level 27",
        },
    },
    "nyrethzalv": {
        "name": "Nyreth'zalvarin",
        "title": "The Forsaken Empress of Shadow-Chains",
        "boss_class": "true",
        "hp": 59000,
        "damage": 290,
        "speed": 1.05,
        "range": 330,           # RANGED (shadow-chain magic)
        "attack_cooldown": 48,
        "radius": 76,
        "gold_reward": 7900,
        "color": (210, 90, 235),       # shadow magenta
        "color_dark": (15, 5, 25),
        "ability_cooldown": 265,
        "ability_damage": 800,
        "ability_range": 370,
        "entrance_text": "NYRETH'ZALVARIN, THE FORSAKEN EMPRESS, UNLEASHES SHADOW-CHAINS!",
        "entrance_color": (240, 140, 255),

        # 4 skills (smart AI - forsaken empress)
        "skill_q_damage": 800,      # Shadow Chain
        "skill_q_cooldown": 305,
        "skill_w_damage": 810,      # Empress's Veil (AOE)
        "skill_w_cooldown": 365,
        "skill_e_damage": 790,      # Forsaken Surge (AOE)
        "skill_e_cooldown": 395,
        "skill_r_damage": 1650,     # Eternal Bond (ultimate)
        "skill_r_cooldown": 830,

        # Ranged AI (kite behavior)
        "prefer_distance": 300,
        "min_distance": 180,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 710,
        "ability2_name": "Eternal Bond",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Nyreth'zalvarin",
            "title": "The Forsaken Empress of Shadow-Chains",
            "role": "True Boss/Shadow Empress",
            "cost": 3900,
            "hp": 2800,
            "damage": 265,
            "speed": 1.4,
            "range": 310,
            "attack_cooldown": 48,
            "color": (210, 90, 235),
            "color_dark": (15, 5, 25),
            "skill_name": "Shadow Chain",
            "skill_desc": "Shadow chain + empress's veil + forsaken surge + eternal bond",
            "skill_cooldown": 305,
            "skill_damage": 800,
            "skill_range": 210,
            "description": "Permaisuri bayangan dari Level 28",
        },
    },
    "nyrellieth": {
        "name": "Nyrellieth",
        "title": "The Frost-Veiled Huntress",
        "boss_class": "true",
        "hp": 61000,
        "damage": 300,
        "speed": 1.1,
        "range": 340,           # RANGED (frost arrows)
        "attack_cooldown": 46,
        "radius": 74,
        "gold_reward": 8200,
        "color": (140, 220, 255),      # ice cyan
        "color_dark": (5, 8, 20),
        "ability_cooldown": 270,
        "ability_damage": 820,
        "ability_range": 380,
        "entrance_text": "NYRELLIETH, THE FROST-VEILED HUNTRESS, FREEZES THE DAWN!",
        "entrance_color": (200, 245, 255),

        # 4 skills (smart AI - frost huntress)
        "skill_q_damage": 820,      # Frost Arrow
        "skill_q_cooldown": 310,
        "skill_w_damage": 830,      # Veil of Frost (AOE)
        "skill_w_cooldown": 370,
        "skill_e_damage": 810,      # Ice Walk (AOE)
        "skill_e_cooldown": 400,
        "skill_r_damage": 1700,     # Eternal Winter (ultimate)
        "skill_r_cooldown": 850,

        # Ranged AI (kite behavior)
        "prefer_distance": 310,
        "min_distance": 190,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 720,
        "ability2_name": "Eternal Winter",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Nyrellieth",
            "title": "The Frost-Veiled Huntress",
            "role": "True Boss/Frost Archer",
            "cost": 4000,
            "hp": 2850,
            "damage": 275,
            "speed": 1.45,
            "range": 320,
            "attack_cooldown": 46,
            "color": (140, 220, 255),
            "color_dark": (5, 8, 20),
            "skill_name": "Frost Arrow",
            "skill_desc": "Frost arrow + veil of frost + ice walk + eternal winter",
            "skill_cooldown": 310,
            "skill_damage": 820,
            "skill_range": 215,
            "description": "Pemburu es dari Level 29",
        },
    },
    "nyxharr": {
        "name": "Nyxharr",
        "title": "The Shadow of War",
        "boss_class": "true",
        "hp": 65000,
        "damage": 310,
        "speed": 1.15,
        "range": 160,           # MELEE (ghost rider charge)
        "attack_cooldown": 44,
        "radius": 80,
        "gold_reward": 9000,
        "color": (90, 225, 245),       # spirit cyan
        "color_dark": (5, 10, 12),
        "ability_cooldown": 275,
        "ability_damage": 850,
        "ability_range": 380,
        "entrance_text": "NYXHARR, THE SHADOW OF WAR, RIDES FROM THE ETERNAL BATTLEFIELD!",
        "entrance_color": (170, 250, 255),

        # 4 skills (smart AI - shadow of war)
        "skill_q_damage": 850,      # Spirit Charge
        "skill_q_cooldown": 315,
        "skill_w_damage": 860,      # War Banner (AOE)
        "skill_w_cooldown": 375,
        "skill_e_damage": 840,      # Ghost Lance (AOE)
        "skill_e_cooldown": 405,
        "skill_r_damage": 1800,     # Eternal War (ultimate)
        "skill_r_cooldown": 870,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 740,
        "ability2_name": "Eternal War",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Nyxharr",
            "title": "The Shadow of War",
            "role": "True Boss/Ghost Rider",
            "cost": 4200,
            "hp": 3000,
            "damage": 290,
            "speed": 1.5,
            "range": 170,
            "attack_cooldown": 44,
            "color": (90, 225, 245),
            "color_dark": (5, 10, 12),
            "skill_name": "Spirit Charge",
            "skill_desc": "Spirit charge + war banner + ghost lance + eternal war",
            "skill_cooldown": 315,
            "skill_damage": 850,
            "skill_range": 220,
            "description": "Bayangan perang dari Level 30",
        },
    },
    "ravokkar": {
        "name": "Ravokkar",
        "title": "The Outlaw King",
        "boss_class": "true",
        "hp": 68000,
        "damage": 320,
        "speed": 1.15,
        "range": 340,           # RANGED (shotgun blasts)
        "attack_cooldown": 46,
        "radius": 78,
        "gold_reward": 9500,
        "color": (215, 75, 75),       # outlaw blood red
        "color_dark": (5, 5, 8),
        "ability_cooldown": 280,
        "ability_damage": 880,
        "ability_range": 390,
        "entrance_text": "RAVOKKAR, THE OUTLAW KING, CLAIMS THE FRONTIER!",
        "entrance_color": (245, 140, 140),

        # 4 skills (smart AI - outlaw king)
        "skill_q_damage": 880,      # Quickdraw Barrage
        "skill_q_cooldown": 320,
        "skill_w_damage": 890,      # Smoke Veil (AOE)
        "skill_w_cooldown": 380,
        "skill_e_damage": 870,      # Dynamite Toss (AOE)
        "skill_e_cooldown": 410,
        "skill_r_damage": 1850,     # Last Stand (ultimate)
        "skill_r_cooldown": 880,

        # Ranged AI (kite behavior)
        "prefer_distance": 310,
        "min_distance": 190,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 750,
        "ability2_name": "Last Stand",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Ravokkar",
            "title": "The Outlaw King",
            "role": "True Boss/Outlaw Gunslinger",
            "cost": 4400,
            "hp": 3100,
            "damage": 300,
            "speed": 1.5,
            "range": 320,
            "attack_cooldown": 46,
            "color": (215, 75, 75),
            "color_dark": (5, 5, 8),
            "skill_name": "Quickdraw Barrage",
            "skill_desc": "Quickdraw barrage + smoke veil + dynamite toss + last stand",
            "skill_cooldown": 320,
            "skill_damage": 880,
            "skill_range": 225,
            "description": "Raja penjahat dari Level 31",
        },
    },
    "malzeroth": {
        "name": "Malzeroth",
        "title": "The Hexbound Sovereign",
        "boss_class": "true",
        "hp": 71000,
        "damage": 330,
        "speed": 1.1,
        "range": 350,           # RANGED (hex magic)
        "attack_cooldown": 48,
        "radius": 78,
        "gold_reward": 10000,
        "color": (140, 60, 200),       # hex purple
        "color_dark": (25, 15, 40),
        "ability_cooldown": 285,
        "ability_damage": 900,
        "ability_range": 400,
        "entrance_text": "MALZEROTH, THE HEXBOUND SOVEREIGN, CURSES ALL WHO DEFY HIM!",
        "entrance_color": (240, 210, 255),

        # 4 skills (smart AI - hexbound sovereign)
        "skill_q_damage": 900,      # Hex Bolt
        "skill_q_cooldown": 330,
        "skill_w_damage": 910,      # Cursed Ground (AOE)
        "skill_w_cooldown": 390,
        "skill_e_damage": 890,      # Hexbound Chains (AOE)
        "skill_e_cooldown": 420,
        "skill_r_damage": 1900,     # Sovereign's Curse (ultimate)
        "skill_r_cooldown": 900,

        # Ranged AI (kite behavior)
        "prefer_distance": 320,
        "min_distance": 200,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 760,
        "ability2_name": "Sovereign's Curse",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Malzeroth",
            "title": "The Hexbound Sovereign",
            "role": "True Boss/Hex Mage",
            "cost": 4600,
            "hp": 3200,
            "damage": 310,
            "speed": 1.45,
            "range": 330,
            "attack_cooldown": 48,
            "color": (140, 60, 200),
            "color_dark": (25, 15, 40),
            "skill_name": "Hex Bolt",
            "skill_desc": "Hex bolt + cursed ground + hexbound chains + sovereign's curse",
            "skill_cooldown": 330,
            "skill_damage": 900,
            "skill_range": 230,
            "description": "Penguasa hex dari Level 32",
        },
    },
    "zharakzuul": {
        "name": "Zharakzuul",
        "title": "The Voidbound Sovereign",
        "boss_class": "true",
        "hp": 74000,
        "damage": 340,
        "speed": 1.1,
        "range": 360,           # RANGED (void magic)
        "attack_cooldown": 48,
        "radius": 80,
        "gold_reward": 10500,
        "color": (175, 55, 235),       # void magenta
        "color_dark": (15, 8, 30),
        "ability_cooldown": 290,
        "ability_damage": 920,
        "ability_range": 410,
        "entrance_text": "ZHARAKZUUL, THE VOIDBOUND SOVEREIGN, COMMANDS THE EMPTY DARK!",
        "entrance_color": (245, 200, 255),

        # 4 skills (smart AI - voidbound sovereign)
        "skill_q_damage": 920,      # Void Lance
        "skill_q_cooldown": 335,
        "skill_w_damage": 930,      # Null Field (AOE)
        "skill_w_cooldown": 395,
        "skill_e_damage": 910,      # Void Step (AOE)
        "skill_e_cooldown": 425,
        "skill_r_damage": 1950,     # Sovereign's Void (ultimate)
        "skill_r_cooldown": 910,

        # Ranged AI (kite behavior)
        "prefer_distance": 330,
        "min_distance": 210,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 770,
        "ability2_name": "Sovereign's Void",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Zharakzuul",
            "title": "The Voidbound Sovereign",
            "role": "True Boss/Void Mage",
            "cost": 4800,
            "hp": 3300,
            "damage": 320,
            "speed": 1.45,
            "range": 340,
            "attack_cooldown": 48,
            "color": (175, 55, 235),
            "color_dark": (15, 8, 30),
            "skill_name": "Void Lance",
            "skill_desc": "Void lance + null field + void step + sovereign's void",
            "skill_cooldown": 335,
            "skill_damage": 920,
            "skill_range": 235,
            "description": "Penguasa kekosongan dari Level 33",
        },
    },
    "grondmauris": {
        "name": "Grondmauris",
        "title": "The Earthborn",
        "boss_class": "true",
        "hp": 77000,
        "damage": 350,
        "speed": 1.0,
        "range": 170,           # MELEE (earth colossus slam)
        "attack_cooldown": 50,
        "radius": 84,
        "gold_reward": 11000,
        "color": (140, 190, 70),       # earth moss green
        "color_dark": (25, 22, 20),
        "ability_cooldown": 295,
        "ability_damage": 940,
        "ability_range": 420,
        "entrance_text": "GRONDMAURIS THE EARTHBORN, AWAKENS FROM THE DEEP!",
        "entrance_color": (200, 255, 180),

        # 4 skills (smart AI - earthborn)
        "skill_q_damage": 940,      # Earth Break
        "skill_q_cooldown": 340,
        "skill_w_damage": 950,      # Moss Bind (AOE)
        "skill_w_cooldown": 400,
        "skill_e_damage": 930,      # Colossus Stampede (AOE)
        "skill_e_cooldown": 430,
        "skill_r_damage": 2000,     # World Awakening (ultimate)
        "skill_r_cooldown": 930,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 780,
        "ability2_name": "World Awakening",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Grondmauris",
            "title": "The Earthborn",
            "role": "True Boss/Earth Colossus",
            "cost": 5000,
            "hp": 3400,
            "damage": 330,
            "speed": 1.35,
            "range": 180,
            "attack_cooldown": 50,
            "color": (140, 190, 70),
            "color_dark": (25, 22, 20),
            "skill_name": "Earth Break",
            "skill_desc": "Earth break + moss bind + colossus stampede + world awakening",
            "skill_cooldown": 340,
            "skill_damage": 940,
            "skill_range": 240,
            "description": "Raksasa bumi dari Level 34",
        },
    },
    "lyssarethys": {
        "name": "Lyssarethys",
        "title": "The Heartbane",
        "boss_class": "true",
        "hp": 80000,
        "damage": 360,
        "speed": 1.15,
        "range": 370,           # RANGED (magenta soul magic)
        "attack_cooldown": 46,
        "radius": 80,
        "gold_reward": 11500,
        "color": (255, 100, 190),      # magenta pink
        "color_dark": (30, 20, 40),
        "ability_cooldown": 300,
        "ability_damage": 960,
        "ability_range": 430,
        "entrance_text": "LYSSARETHYS THE HEARTBANE, BREAKS ALL HEARTS THAT BEHOLD HER!",
        "entrance_color": (255, 180, 230),

        # 4 skills (smart AI - heartbane)
        "skill_q_damage": 960,      # Heartbreak Lance
        "skill_q_cooldown": 345,
        "skill_w_damage": 970,      # Last Caress (AOE)
        "skill_w_cooldown": 405,
        "skill_e_damage": 950,      # Soul Whip (AOE)
        "skill_e_cooldown": 435,
        "skill_r_damage": 2050,     # Heartbane's Embrace (ultimate)
        "skill_r_cooldown": 950,

        # Ranged AI (kite behavior)
        "prefer_distance": 340,
        "min_distance": 220,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 790,
        "ability2_name": "Heartbane's Embrace",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Lyssarethys",
            "title": "The Heartbane",
            "role": "True Boss/Magenta Soul Mage",
            "cost": 5200,
            "hp": 3500,
            "damage": 340,
            "speed": 1.5,
            "range": 350,
            "attack_cooldown": 46,
            "color": (255, 100, 190),
            "color_dark": (30, 20, 40),
            "skill_name": "Heartbreak Lance",
            "skill_desc": "Heartbreak lance + last caress + soul whip + heartbane's embrace",
            "skill_cooldown": 345,
            "skill_damage": 960,
            "skill_range": 250,
            "description": "Pemutus hati dari Level 35",
        },
    },
    "kaerinya": {
        "name": "Kaerinya",
        "title": "The Sunfist",
        "boss_class": "true",
        "hp": 83000,
        "damage": 370,
        "speed": 1.2,
        "range": 180,           # MELEE (fiery golden fists)
        "attack_cooldown": 44,
        "radius": 80,
        "gold_reward": 12000,
        "color": (250, 220, 110),      # fiery gold
        "color_dark": (5, 10, 25),
        "ability_cooldown": 305,
        "ability_damage": 980,
        "ability_range": 440,
        "entrance_text": "KAERINYA THE SUNFIST, STRIKES WITH THE HEART OF THE SUN!",
        "entrance_color": (255, 245, 190),

        # 4 skills (smart AI - sunfist)
        "skill_q_damage": 980,      # Solar Jab
        "skill_q_cooldown": 350,
        "skill_w_damage": 990,      # Blazing Guard (AOE)
        "skill_w_cooldown": 410,
        "skill_e_damage": 970,      # Sunstep (AOE)
        "skill_e_cooldown": 440,
        "skill_r_damage": 2100,     # Sunfist Cataclysm (ultimate)
        "skill_r_cooldown": 960,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 800,
        "ability2_name": "Sunfist Cataclysm",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Kaerinya",
            "title": "The Sunfist",
            "role": "True Boss/Fire Brawler",
            "cost": 5400,
            "hp": 3600,
            "damage": 350,
            "speed": 1.55,
            "range": 190,
            "attack_cooldown": 44,
            "color": (250, 220, 110),
            "color_dark": (5, 10, 25),
            "skill_name": "Solar Jab",
            "skill_desc": "Solar jab + blazing guard + sunstep + sunfist cataclysm",
            "skill_cooldown": 350,
            "skill_damage": 980,
            "skill_range": 255,
            "description": "Tinju matahari dari Level 36",
        },
    },
    "xelnarath": {
        "name": "Xel'Narath",
        "title": "The Void Sovereign",
        "boss_class": "true",
        "hp": 86000,
        "damage": 380,
        "speed": 1.15,
        "range": 380,           # RANGED (void magic)
        "attack_cooldown": 46,
        "radius": 82,
        "gold_reward": 12500,
        "color": (230, 100, 240),      # magenta hot
        "color_dark": (8, 3, 15),
        "ability_cooldown": 310,
        "ability_damage": 1000,
        "ability_range": 450,
        "entrance_text": "XEL'NARATH THE VOID SOVEREIGN, UNFOLDS THE DARK WINGS!",
        "entrance_color": (255, 160, 255),

        # 4 skills (smart AI - void sovereign)
        "skill_q_damage": 1000,     # Void Lance
        "skill_q_cooldown": 355,
        "skill_w_damage": 1010,     # Magenta Eclipse (AOE)
        "skill_w_cooldown": 415,
        "skill_e_damage": 990,      # Void Wing Dive (AOE)
        "skill_e_cooldown": 445,
        "skill_r_damage": 2150,     # Sovereign's Voidfall (ultimate)
        "skill_r_cooldown": 970,

        # Ranged AI (kite behavior)
        "prefer_distance": 350,
        "min_distance": 230,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 810,
        "ability2_name": "Sovereign's Voidfall",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Xel'Narath",
            "title": "The Void Sovereign",
            "role": "True Boss/Void Sovereign",
            "cost": 5600,
            "hp": 3700,
            "damage": 360,
            "speed": 1.5,
            "range": 360,
            "attack_cooldown": 46,
            "color": (230, 100, 240),
            "color_dark": (8, 3, 15),
            "skill_name": "Void Lance",
            "skill_desc": "Void lance + magenta eclipse + void wing dive + sovereign's voidfall",
            "skill_cooldown": 355,
            "skill_damage": 1000,
            "skill_range": 260,
            "description": "Penguasa kekosongan dari Level 37",
        },
    },
    "kyrenzai": {
        "name": "Kyrenzai",
        "title": "The Crimson Devourer",
        "boss_class": "true",
        "hp": 89000,
        "damage": 390,
        "speed": 1.2,
        "range": 390,           # RANGED (kagune blood tentacles)
        "attack_cooldown": 44,
        "radius": 82,
        "gold_reward": 13000,
        "color": (230, 55, 65),       # kagune red
        "color_dark": (5, 3, 5),
        "ability_cooldown": 315,
        "ability_damage": 1020,
        "ability_range": 460,
        "entrance_text": "KYRENZAI THE CRIMSON DEVOURER, FEEDS ON THE LIVING!",
        "entrance_color": (255, 110, 100),

        # 4 skills (smart AI - crimson devourer)
        "skill_q_damage": 1020,     # Kagune Pierce
        "skill_q_cooldown": 360,
        "skill_w_damage": 1030,     # Blood Feast (AOE)
        "skill_w_cooldown": 420,
        "skill_e_damage": 1010,     # Tentacle Sweep (AOE)
        "skill_e_cooldown": 450,
        "skill_r_damage": 2200,     # Devourer's Hunger (ultimate)
        "skill_r_cooldown": 980,

        # Ranged AI (kite behavior)
        "prefer_distance": 360,
        "min_distance": 240,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 820,
        "ability2_name": "Devourer's Hunger",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Kyrenzai",
            "title": "The Crimson Devourer",
            "role": "True Boss/Kagune Ghoul",
            "cost": 5800,
            "hp": 3800,
            "damage": 370,
            "speed": 1.55,
            "range": 370,
            "attack_cooldown": 44,
            "color": (230, 55, 65),
            "color_dark": (5, 3, 5),
            "skill_name": "Kagune Pierce",
            "skill_desc": "Kagune pierce + blood feast + tentacle sweep + devourer's hunger",
            "skill_cooldown": 360,
            "skill_damage": 1020,
            "skill_range": 265,
            "description": "Pelahap merah dari Level 38",
        },
    },
    "xaelmoran": {
        "name": "Xael'moran",
        "title": "The Elemental Weaver",
        "boss_class": "true",
        "hp": 92000,
        "damage": 400,
        "speed": 1.15,
        "range": 400,           # RANGED (quas/wex/exort magic)
        "attack_cooldown": 46,
        "radius": 82,
        "gold_reward": 13500,
        "color": (170, 60, 220),       # wex magenta
        "color_dark": (15, 8, 25),
        "ability_cooldown": 320,
        "ability_damage": 1040,
        "ability_range": 470,
        "entrance_text": "XAEL'MORAN THE ELEMENTAL WEAVER, COMMANDS ALL ELEMENTS!",
        "entrance_color": (240, 200, 90),

        # 4 skills (smart AI - elemental weaver)
        "skill_q_damage": 1040,     # Cold Snap (Quas)
        "skill_q_cooldown": 365,
        "skill_w_damage": 1050,     # Tornado (Wex)
        "skill_w_cooldown": 425,
        "skill_e_damage": 1030,     # Sun Strike (Exort)
        "skill_e_cooldown": 455,
        "skill_r_damage": 2250,     # Cataclysm (ultimate)
        "skill_r_cooldown": 1000,

        # Ranged AI (kite behavior)
        "prefer_distance": 370,
        "min_distance": 250,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 830,
        "ability2_name": "Cataclysm",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Xael'moran",
            "title": "The Elemental Weaver",
            "role": "True Boss/Elemental Mage",
            "cost": 6000,
            "hp": 3900,
            "damage": 380,
            "speed": 1.55,
            "range": 380,
            "attack_cooldown": 46,
            "color": (170, 60, 220),
            "color_dark": (15, 8, 25),
            "skill_name": "Cold Snap",
            "skill_desc": "Cold snap + tornado + sun strike + cataclysm",
            "skill_cooldown": 365,
            "skill_damage": 1040,
            "skill_range": 270,
            "description": "Penenun elemen dari Level 39",
        },
    },
    "thalryndel": {
        "name": "Thal'ryndel",
        "title": "The Tempest Weaver",
        "boss_class": "true",
        "hp": 95000,
        "damage": 410,
        "speed": 1.15,
        "range": 410,           # RANGED (storm/lightning magic)
        "attack_cooldown": 44,
        "radius": 84,
        "gold_reward": 14000,
        "color": (60, 140, 240),       # lightning blue
        "color_dark": (5, 10, 30),
        "ability_cooldown": 325,
        "ability_damage": 1060,
        "ability_range": 480,
        "entrance_text": "THAL'RYNDEL THE TEMPEST WEAVER, COMMANDS THE STORM!",
        "entrance_color": (220, 245, 255),

        # 4 skills (smart AI - tempest weaver)
        "skill_q_damage": 1060,     # Lightning Bolt
        "skill_q_cooldown": 370,
        "skill_w_damage": 1070,     # Storm Veil (AOE)
        "skill_w_cooldown": 430,
        "skill_e_damage": 1050,     # Tempest Step (AOE)
        "skill_e_cooldown": 460,
        "skill_r_damage": 2300,     # Eye of the Storm (ultimate)
        "skill_r_cooldown": 1010,

        # Ranged AI (kite behavior)
        "prefer_distance": 380,
        "min_distance": 260,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 840,
        "ability2_name": "Eye of the Storm",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Thal'ryndel",
            "title": "The Tempest Weaver",
            "role": "True Boss/Storm Mage",
            "cost": 6200,
            "hp": 4000,
            "damage": 390,
            "speed": 1.55,
            "range": 390,
            "attack_cooldown": 44,
            "color": (60, 140, 240),
            "color_dark": (5, 10, 30),
            "skill_name": "Lightning Bolt",
            "skill_desc": "Lightning bolt + storm veil + tempest step + eye of the storm",
            "skill_cooldown": 370,
            "skill_damage": 1060,
            "skill_range": 275,
            "description": "Penenun badai dari Level 40",
        },
    },
    "grimkor": {
        "name": "Grimkor",
        "title": "The Sawmill Warlord",
        "boss_class": "true",
        "hp": 98000,
        "damage": 420,
        "speed": 1.1,
        "range": 190,           # MELEE (sawblade axe)
        "attack_cooldown": 48,
        "radius": 86,
        "gold_reward": 14500,
        "color": (220, 90, 20),       # sawmill fire
        "color_dark": (18, 15, 12),
        "ability_cooldown": 330,
        "ability_damage": 1080,
        "ability_range": 490,
        "entrance_text": "GRIMKOR THE SAWMILL WARLORD, CARVES THROUGH ALL TIMBER AND FLESH!",
        "entrance_color": (255, 220, 120),

        # 4 skills (smart AI - sawmill warlord)
        "skill_q_damage": 1080,     # Sawblade Spin
        "skill_q_cooldown": 375,
        "skill_w_damage": 1090,     # Lumberjack's Wrath (AOE)
        "skill_w_cooldown": 435,
        "skill_e_damage": 1070,     # Timber Charge (AOE)
        "skill_e_cooldown": 465,
        "skill_r_damage": 2350,     # Mill of Ruin (ultimate)
        "skill_r_cooldown": 1020,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 850,
        "ability2_name": "Mill of Ruin",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Grimkor",
            "title": "The Sawmill Warlord",
            "role": "True Boss/Sawmill Warlord",
            "cost": 6400,
            "hp": 4100,
            "damage": 400,
            "speed": 1.5,
            "range": 200,
            "attack_cooldown": 48,
            "color": (220, 90, 20),
            "color_dark": (18, 15, 12),
            "skill_name": "Sawblade Spin",
            "skill_desc": "Sawblade spin + lumberjack's wrath + timber charge + mill of ruin",
            "skill_cooldown": 375,
            "skill_damage": 1080,
            "skill_range": 280,
            "description": "Tuan perang penggergajian dari Level 41",
        },
    },
    "kaineroth": {
        "name": "Kaineroth",
        "title": "The Crow-Eyed",
        "boss_class": "true",
        "hp": 101000,
        "damage": 430,
        "speed": 1.2,
        "range": 420,           # RANGED (sharingan crimson gaze)
        "attack_cooldown": 44,
        "radius": 84,
        "gold_reward": 15000,
        "color": (230, 70, 80),       # crow crimson
        "color_dark": (5, 3, 8),
        "ability_cooldown": 335,
        "ability_damage": 1100,
        "ability_range": 500,
        "entrance_text": "KAINEROTH THE CROW-EYED, SEES ALL WITH CRIMSON GAZE!",
        "entrance_color": (255, 130, 130),

        # 4 skills (smart AI - crow-eyed)
        "skill_q_damage": 1100,     # Crimson Gaze
        "skill_q_cooldown": 380,
        "skill_w_damage": 1110,     # Crow Storm (AOE)
        "skill_w_cooldown": 440,
        "skill_e_damage": 1090,     # Shadow Step (AOE)
        "skill_e_cooldown": 470,
        "skill_r_damage": 2400,     # Crow-Eyed Judgment (ultimate)
        "skill_r_cooldown": 1030,

        # Ranged AI (kite behavior)
        "prefer_distance": 390,
        "min_distance": 270,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 860,
        "ability2_name": "Crow-Eyed Judgment",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Kaineroth",
            "title": "The Crow-Eyed",
            "role": "True Boss/Crimson Prodigy",
            "cost": 6600,
            "hp": 4200,
            "damage": 410,
            "speed": 1.55,
            "range": 400,
            "attack_cooldown": 44,
            "color": (230, 70, 80),
            "color_dark": (5, 3, 8),
            "skill_name": "Crimson Gaze",
            "skill_desc": "Crimson gaze + crow storm + shadow step + crow-eyed judgment",
            "skill_cooldown": 380,
            "skill_damage": 1100,
            "skill_range": 285,
            "description": "Prodigi merah dari Level 42",
        },
    },
    "zyvareth": {
        "name": "Zyvareth",
        "title": "The Stormherald",
        "boss_class": "true",
        "hp": 104000,
        "damage": 440,
        "speed": 1.2,
        "range": 430,           # RANGED (crystal lightning magic)
        "attack_cooldown": 44,
        "radius": 86,
        "gold_reward": 15500,
        "color": (215, 130, 250),      # crystal purple
        "color_dark": (5, 30, 40),
        "ability_cooldown": 340,
        "ability_damage": 1120,
        "ability_range": 510,
        "entrance_text": "ZYVARETH THE STORMHERALD, ROARS WITH CRYSTAL THUNDER!",
        "entrance_color": (245, 195, 255),

        # 4 skills (smart AI - stormherald)
        "skill_q_damage": 1120,     # Crystal Bolt
        "skill_q_cooldown": 385,
        "skill_w_damage": 1130,     # Stormfall (AOE)
        "skill_w_cooldown": 445,
        "skill_e_damage": 1110,     # Thunder Horn (AOE)
        "skill_e_cooldown": 475,
        "skill_r_damage": 2450,     # Crystal Tempest (ultimate)
        "skill_r_cooldown": 1040,

        # Ranged AI (kite behavior)
        "prefer_distance": 400,
        "min_distance": 280,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 870,
        "ability2_name": "Crystal Tempest",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Zyvareth",
            "title": "The Stormherald",
            "role": "True Boss/Crystal Storm Beast",
            "cost": 6800,
            "hp": 4300,
            "damage": 420,
            "speed": 1.55,
            "range": 410,
            "attack_cooldown": 44,
            "color": (215, 130, 250),
            "color_dark": (5, 30, 40),
            "skill_name": "Crystal Bolt",
            "skill_desc": "Crystal bolt + stormfall + thunder horn + crystal tempest",
            "skill_cooldown": 385,
            "skill_damage": 1120,
            "skill_range": 295,
            "description": "Herald badai kristal dari Level 43",
        },
    },
    "kagetsuka": {
        "name": "Kagetsuka",
        "title": "The Eternal Warlord",
        "boss_class": "true",
        "hp": 107000,
        "damage": 450,
        "speed": 1.2,
        "range": 200,           # MELEE (sharingan fire blades)
        "attack_cooldown": 44,
        "radius": 86,
        "gold_reward": 16000,
        "color": (200, 30, 40),       # sharingan red
        "color_dark": (25, 10, 15),
        "ability_cooldown": 345,
        "ability_damage": 1140,
        "ability_range": 520,
        "entrance_text": "KAGETSUKA THE ETERNAL WARLORD, BURNS WITH SHARINGAN FIRE!",
        "entrance_color": (255, 180, 160),

        # 4 skills (smart AI - eternal warlord)
        "skill_q_damage": 1140,     # Crimson Slash
        "skill_q_cooldown": 390,
        "skill_w_damage": 1150,     # Fire Aura (AOE)
        "skill_w_cooldown": 450,
        "skill_e_damage": 1130,     # Warlord's Charge (AOE)
        "skill_e_cooldown": 480,
        "skill_r_damage": 2500,     # Eternal Judgment (ultimate)
        "skill_r_cooldown": 1050,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 880,
        "ability2_name": "Eternal Judgment",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Kagetsuka",
            "title": "The Eternal Warlord",
            "role": "True Boss/Sharingan Warlord",
            "cost": 7000,
            "hp": 4400,
            "damage": 430,
            "speed": 1.55,
            "range": 210,
            "attack_cooldown": 44,
            "color": (200, 30, 40),
            "color_dark": (25, 10, 15),
            "skill_name": "Crimson Slash",
            "skill_desc": "Crimson slash + fire aura + warlord's charge + eternal judgment",
            "skill_cooldown": 390,
            "skill_damage": 1140,
            "skill_range": 300,
            "description": "Tuan perang abadi dari Level 44",
        },
    },
    "deidara": {
        "name": "Deidara",
        "title": "The Explosive Artist",
        "boss_class": "true",
        "hp": 110000,
        "damage": 460,
        "speed": 1.2,
        "range": 440,           # RANGED (clay explosive art)
        "attack_cooldown": 44,
        "radius": 86,
        "gold_reward": 16500,
        "color": (250, 70, 60),       # red cloud
        "color_dark": (5, 5, 8),
        "ability_cooldown": 350,
        "ability_damage": 1160,
        "ability_range": 530,
        "entrance_text": "DEIDARA THE EXPLOSIVE ARTIST, SHOWS HIS ART TO THE WORLD!",
        "entrance_color": (255, 150, 130),

        # 4 skills (smart AI - explosive artist)
        "skill_q_damage": 1160,     # Clay Bird
        "skill_q_cooldown": 395,
        "skill_w_damage": 1170,     # C1 Bomb Cluster (AOE)
        "skill_w_cooldown": 455,
        "skill_e_damage": 1150,     # Artful Step (AOE)
        "skill_e_cooldown": 485,
        "skill_r_damage": 2550,     # C4 Karura (ultimate)
        "skill_r_cooldown": 1060,

        # Ranged AI (kite behavior)
        "prefer_distance": 410,
        "min_distance": 290,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 890,
        "ability2_name": "C4 Karura",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Deidara",
            "title": "The Explosive Artist",
            "role": "True Boss/Explosive Artist",
            "cost": 7200,
            "hp": 4500,
            "damage": 440,
            "speed": 1.55,
            "range": 420,
            "attack_cooldown": 44,
            "color": (250, 70, 60),
            "color_dark": (5, 5, 8),
            "skill_name": "Clay Bird",
            "skill_desc": "Clay bird + c1 bomb cluster + artful step + c4 karura",
            "skill_cooldown": 395,
            "skill_damage": 1160,
            "skill_range": 310,
            "description": "Seniman peledak dari Level 45",
        },
    },
    "sunakage": {
        "name": "Sunakage",
        "title": "The Sand Shadow",
        "boss_class": "true",
        "hp": 113000,
        "damage": 470,
        "speed": 1.2,
        "range": 450,           # RANGED (sand mage magic)
        "attack_cooldown": 44,
        "radius": 88,
        "gold_reward": 17000,
        "color": (230, 70, 45),       # rust sand red
        "color_dark": (25, 8, 10),
        "ability_cooldown": 355,
        "ability_damage": 1180,
        "ability_range": 540,
        "entrance_text": "SUNAKAGE THE SAND SHADOW, COMMANDS THE ENDLESS DUNES!",
        "entrance_color": (250, 150, 100),

        # 4 skills (smart AI - sand shadow)
        "skill_q_damage": 1180,     # Sand Blade
        "skill_q_cooldown": 400,
        "skill_w_damage": 1190,     # Dune Storm (AOE)
        "skill_w_cooldown": 460,
        "skill_e_damage": 1170,     # Sand Step (AOE)
        "skill_e_cooldown": 490,
        "skill_r_damage": 2600,     # Shadow of the Dunes (ultimate)
        "skill_r_cooldown": 1070,

        # Ranged AI (kite behavior)
        "prefer_distance": 420,
        "min_distance": 300,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 900,
        "ability2_name": "Shadow of the Dunes",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Sunakage",
            "title": "The Sand Shadow",
            "role": "True Boss/Sand Mage",
            "cost": 7400,
            "hp": 4600,
            "damage": 450,
            "speed": 1.55,
            "range": 430,
            "attack_cooldown": 44,
            "color": (230, 70, 45),
            "color_dark": (25, 8, 10),
            "skill_name": "Sand Blade",
            "skill_desc": "Sand blade + dune storm + sand step + shadow of the dunes",
            "skill_cooldown": 400,
            "skill_damage": 1180,
            "skill_range": 320,
            "description": "Bayangan pasir dari Level 46",
        },
    },
    "pyraena": {
        "name": "Pyraena",
        "title": "The Emberweaver",
        "boss_class": "true",
        "hp": 116000,
        "damage": 480,
        "speed": 1.2,
        "range": 460,           # RANGED (ember fire magic)
        "attack_cooldown": 44,
        "radius": 88,
        "gold_reward": 17500,
        "color": (255, 165, 60),       # ember orange
        "color_dark": (35, 8, 15),
        "ability_cooldown": 360,
        "ability_damage": 1200,
        "ability_range": 550,
        "entrance_text": "PYRAENA THE EMBERWEAVER, WEAVES DESTINY IN FIRE!",
        "entrance_color": (255, 220, 130),

        # 4 skills (smart AI - emberweaver)
        "skill_q_damage": 1200,     # Ember Lance
        "skill_q_cooldown": 405,
        "skill_w_damage": 1210,     # Flame Weave (AOE)
        "skill_w_cooldown": 465,
        "skill_e_damage": 1190,     # Ember Step (AOE)
        "skill_e_cooldown": 495,
        "skill_r_damage": 2650,     # Emberweaver's Inferno (ultimate)
        "skill_r_cooldown": 1080,

        # Ranged AI (kite behavior)
        "prefer_distance": 430,
        "min_distance": 310,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 910,
        "ability2_name": "Emberweaver's Inferno",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Pyraena",
            "title": "The Emberweaver",
            "role": "True Boss/Fire Mage",
            "cost": 7600,
            "hp": 4700,
            "damage": 460,
            "speed": 1.55,
            "range": 440,
            "attack_cooldown": 44,
            "color": (255, 165, 60),
            "color_dark": (35, 8, 15),
            "skill_name": "Ember Lance",
            "skill_desc": "Ember lance + flame weave + ember step + emberweaver's inferno",
            "skill_cooldown": 405,
            "skill_damage": 1200,
            "skill_range": 330,
            "description": "Penenun bara dari Level 47",
        },
    },
    "cogsworth": {
        "name": "Cogsworth",
        "title": "The Skyfury",
        "boss_class": "true",
        "hp": 119000,
        "damage": 490,
        "speed": 1.2,
        "range": 470,           # RANGED (sky cannon barrage)
        "attack_cooldown": 44,
        "radius": 90,
        "gold_reward": 18000,
        "color": (230, 155, 75),       # sky copper
        "color_dark": (12, 12, 15),
        "ability_cooldown": 365,
        "ability_damage": 1220,
        "ability_range": 560,
        "entrance_text": "COGSWORTH THE SKYFURY, RAINS STEEL FROM THE CLOUDS!",
        "entrance_color": (255, 210, 140),

        # 4 skills (smart AI - skyfury)
        "skill_q_damage": 1220,     # Sky Cannon
        "skill_q_cooldown": 410,
        "skill_w_damage": 1230,     # Copper Storm (AOE)
        "skill_w_cooldown": 470,
        "skill_e_damage": 1210,     # Rocket Dash (AOE)
        "skill_e_cooldown": 500,
        "skill_r_damage": 2700,     # Skyfury Cataclysm (ultimate)
        "skill_r_cooldown": 1090,

        # Ranged AI (kite behavior)
        "prefer_distance": 440,
        "min_distance": 320,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 920,
        "ability2_name": "Skyfury Cataclysm",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Cogsworth",
            "title": "The Skyfury",
            "role": "True Boss/Steampunk Sky Machine",
            "cost": 7800,
            "hp": 4800,
            "damage": 470,
            "speed": 1.55,
            "range": 450,
            "attack_cooldown": 44,
            "color": (230, 155, 75),
            "color_dark": (12, 12, 15),
            "skill_name": "Sky Cannon",
            "skill_desc": "Sky cannon + copper storm + rocket dash + skyfury cataclysm",
            "skill_cooldown": 410,
            "skill_damage": 1220,
            "skill_range": 340,
            "description": "Mesin langit dari Level 48",
        },
    },
    "yomigetsu": {
        "name": "Yomigetsu",
        "title": "The Moonreaper",
        "boss_class": "true",
        "hp": 122000,
        "damage": 500,
        "speed": 1.2,
        "range": 480,           # RANGED (moon crescent slashes)
        "attack_cooldown": 44,
        "radius": 92,
        "gold_reward": 18500,
        "color": (200, 140, 255),       # moon violet
        "color_dark": (15, 5, 40),
        "ability_cooldown": 370,
        "ability_damage": 1240,
        "ability_range": 570,
        "entrance_text": "YOMIGETSU THE MOONREAPER, DESCENDS UNDER THE CRIMSON MOON!",
        "entrance_color": (235, 195, 255),

        # 4 skills (smart AI - moonreaper)
        "skill_q_damage": 1240,     # Crescent Slash
        "skill_q_cooldown": 415,
        "skill_w_damage": 1250,     # Lunar Eclipse (AOE)
        "skill_w_cooldown": 475,
        "skill_e_damage": 1230,     # Moon Step (AOE)
        "skill_e_cooldown": 505,
        "skill_r_damage": 2750,     # Reaper's Moonfall (ultimate)
        "skill_r_cooldown": 1095,

        # Ranged AI (kite behavior)
        "prefer_distance": 450,
        "min_distance": 330,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 930,
        "ability2_name": "Reaper's Moonfall",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Yomigetsu",
            "title": "The Moonreaper",
            "role": "True Boss/Moon Demon Swordsman",
            "cost": 8000,
            "hp": 5000,
            "damage": 490,
            "speed": 1.6,
            "range": 460,
            "attack_cooldown": 44,
            "color": (200, 140, 255),
            "color_dark": (15, 5, 40),
            "skill_name": "Crescent Slash",
            "skill_desc": "Crescent slash + lunar eclipse + moon step + reaper's moonfall",
            "skill_cooldown": 415,
            "skill_damage": 1240,
            "skill_range": 350,
            "description": "Penuai bulan dari Level 49",
        },
    },

    "akirakumo": {
        "name": "Akirakumo",
        "title": "The Moonfang Prince",
        "boss_class": "true",
        "hp": 125000,
        "damage": 510,
        "speed": 1.2,
        "range": 490,           # RANGED (moonfang crescent blades)
        "attack_cooldown": 44,
        "radius": 94,
        "gold_reward": 19000,
        "color": (215, 215, 230),       # moon silver kimono
        "color_dark": (20, 20, 40),
        "ability_cooldown": 375,
        "ability_damage": 1260,
        "ability_range": 580,
        "entrance_text": "AKIRAKUMO THE MOONFANG PRINCE, BOWS TO NO ONE BUT THE MOON!",
        "entrance_color": (235, 238, 245),

        # 4 skills (smart AI - moonfang prince)
        "skill_q_damage": 1260,     # Moonfang Slash
        "skill_q_cooldown": 420,
        "skill_w_damage": 1270,     # Silver Storm (AOE)
        "skill_w_cooldown": 480,
        "skill_e_damage": 1250,     # Fang Step (AOE)
        "skill_e_cooldown": 510,
        "skill_r_damage": 2800,     # Prince's Moonfall (ultimate)
        "skill_r_cooldown": 1100,

        # Ranged AI (kite behavior)
        "prefer_distance": 460,
        "min_distance": 340,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 940,
        "ability2_name": "Prince's Moonfall",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Akirakumo",
            "title": "The Moonfang Prince",
            "role": "True Boss/Moon Demon Prince",
            "cost": 8200,
            "hp": 5200,
            "damage": 500,
            "speed": 1.6,
            "range": 470,
            "attack_cooldown": 44,
            "color": (215, 215, 230),
            "color_dark": (20, 20, 40),
            "skill_name": "Moonfang Slash",
            "skill_desc": "Moonfang slash + silver storm + fang step + prince's moonfall",
            "skill_cooldown": 420,
            "skill_damage": 1260,
            "skill_range": 360,
            "description": "Pangeran serigala bulan dari Level 50",
        },
    },

    "kaithros": {
        "name": "Kaithros",
        "title": "The Emberlion Ronin",
        "boss_class": "true",
        "hp": 128000,
        "damage": 520,
        "speed": 1.25,
        "range": 200,           # MELEE (flame katana lunges)
        "attack_cooldown": 40,
        "radius": 90,
        "gold_reward": 19500,
        "color": (255, 150, 40),       # emberlion flame
        "color_dark": (20, 5, 0),
        "ability_cooldown": 380,
        "ability_damage": 1280,
        "ability_range": 560,
        "entrance_text": "KAITHROS THE EMBERLION RONIN, BLAZES WITH UNQUENCHABLE SPIRIT!",
        "entrance_color": (255, 230, 130),

        # 4 skills (smart AI - emberlion ronin)
        "skill_q_damage": 1280,     # Ember Slash
        "skill_q_cooldown": 425,
        "skill_w_damage": 1290,     # Flame Breathing (AOE)
        "skill_w_cooldown": 485,
        "skill_e_damage": 1270,     # Lion's Step (AOE)
        "skill_e_cooldown": 515,
        "skill_r_damage": 2850,     # Emberlion's Final Flame (ultimate)
        "skill_r_cooldown": 1105,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 950,
        "ability2_name": "Emberlion's Final Flame",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Kaithros",
            "title": "The Emberlion Ronin",
            "role": "True Boss/Flame Swordsman",
            "cost": 8400,
            "hp": 5400,
            "damage": 510,
            "speed": 1.7,
            "range": 220,
            "attack_cooldown": 40,
            "color": (255, 150, 40),
            "color_dark": (20, 5, 0),
            "skill_name": "Ember Slash",
            "skill_desc": "Ember slash + flame breathing + lion's step + emberlion's final flame",
            "skill_cooldown": 425,
            "skill_damage": 1280,
            "skill_range": 250,
            "description": "Ronin singa api dari Level 51",
        },
    },

    "nyxaris": {
        "name": "Nyxaris",
        "title": "The Lunar Herald",
        "boss_class": "true",
        "hp": 131000,
        "damage": 530,
        "speed": 1.2,
        "range": 500,           # RANGED (lunar moonfire shots)
        "attack_cooldown": 44,
        "radius": 92,
        "gold_reward": 20000,
        "color": (200, 235, 255),       # lunar cyan-white
        "color_dark": (10, 8, 15),
        "ability_cooldown": 385,
        "ability_damage": 1300,
        "ability_range": 590,
        "entrance_text": "NYXARIS THE LUNAR HERALD, PROCLAIMS THE MOON'S JUDGMENT!",
        "entrance_color": (240, 250, 255),

        # 4 skills (smart AI - lunar herald)
        "skill_q_damage": 1300,     # Moonfire Shot
        "skill_q_cooldown": 430,
        "skill_w_damage": 1310,     # Crescent Volley (AOE)
        "skill_w_cooldown": 490,
        "skill_e_damage": 1290,     # Lunar Step (AOE)
        "skill_e_cooldown": 520,
        "skill_r_damage": 2900,     # Herald's Eclipse (ultimate)
        "skill_r_cooldown": 1110,

        # Ranged AI (kite behavior)
        "prefer_distance": 470,
        "min_distance": 350,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 960,
        "ability2_name": "Herald's Eclipse",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Nyxaris",
            "title": "The Lunar Herald",
            "role": "True Boss/Marksman",
            "cost": 8600,
            "hp": 5600,
            "damage": 520,
            "speed": 1.6,
            "range": 480,
            "attack_cooldown": 44,
            "color": (200, 235, 255),
            "color_dark": (10, 8, 15),
            "skill_name": "Moonfire Shot",
            "skill_desc": "Moonfire shot + crescent volley + lunar step + herald's eclipse",
            "skill_cooldown": 430,
            "skill_damage": 1300,
            "skill_range": 370,
            "description": "Pembawa pesan bulan dari Level 52",
        },
    },

    "tsukiyora": {
        "name": "Tsukiyora",
        "title": "The Moon-Born Sovereign",
        "boss_class": "true",
        "hp": 134000,
        "damage": 540,
        "speed": 1.2,
        "range": 510,           # RANGED (moon chakra blasts)
        "attack_cooldown": 44,
        "radius": 96,
        "gold_reward": 20500,
        "color": (240, 238, 248),       # moon-born white robe
        "color_dark": (15, 10, 30),
        "ability_cooldown": 390,
        "ability_damage": 1320,
        "ability_range": 600,
        "entrance_text": "TSUKIYORA THE MOON-BORN SOVEREIGN, DECREES THE END OF ALL WORLDS!",
        "entrance_color": (250, 248, 255),

        # 4 skills (smart AI - moon-born)
        "skill_q_damage": 1320,     # Moon Chakra Blast
        "skill_q_cooldown": 435,
        "skill_w_damage": 1330,     # Truth-Seeking Storm (AOE)
        "skill_w_cooldown": 495,
        "skill_e_damage": 1310,     # Lunar Shift (AOE)
        "skill_e_cooldown": 525,
        "skill_r_damage": 2950,     # All-Killing Ash Bone (ultimate)
        "skill_r_cooldown": 1115,

        # Ranged AI (kite behavior)
        "prefer_distance": 480,
        "min_distance": 360,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 970,
        "ability2_name": "All-Killing Ash Bone",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Tsukiyora",
            "title": "The Moon-Born Sovereign",
            "role": "True Boss/Moon Goddess",
            "cost": 8800,
            "hp": 5800,
            "damage": 530,
            "speed": 1.6,
            "range": 490,
            "attack_cooldown": 44,
            "color": (240, 238, 248),
            "color_dark": (15, 10, 30),
            "skill_name": "Moon Chakra Blast",
            "skill_desc": "Moon chakra blast + truth-seeking storm + lunar shift + all-killing ash bone",
            "skill_cooldown": 435,
            "skill_damage": 1320,
            "skill_range": 380,
            "description": "Penguasa lahir-bulan dari Level 53",
        },
    },

    "hollowbane": {
        "name": "Kurosaki Hollowbane",
        "title": "The Substitute Shinigami",
        "boss_class": "true",
        "hp": 137000,
        "damage": 550,
        "speed": 1.25,
        "range": 200,           # MELEE (zanpakuto blade)
        "attack_cooldown": 40,
        "radius": 92,
        "gold_reward": 21000,
        "color": (255, 155, 55),       # getsuga orange
        "color_dark": (10, 10, 15),
        "ability_cooldown": 395,
        "ability_damage": 1340,
        "ability_range": 570,
        "entrance_text": "KUROSAKI HOLLOWBANE THE SUBSTITUTE SHINIGAMI, RELEASES HIS BANKA!",
        "entrance_color": (255, 210, 100),

        # 4 skills (smart AI - substitute shinigami)
        "skill_q_damage": 1340,     # Getsuga Tensho
        "skill_q_cooldown": 440,
        "skill_w_damage": 1350,     # Bankai Storm (AOE)
        "skill_w_cooldown": 500,
        "skill_e_damage": 1330,     # Flash Step (AOE)
        "skill_e_cooldown": 530,
        "skill_r_damage": 3000,     # Final Getsuga (ultimate)
        "skill_r_cooldown": 1120,

        # Legacy fields (untuk compatibility)
        "ability2_cooldown": 980,
        "ability2_name": "Final Getsuga",
        "ability2_heal_pct": 0.4,

        "hero_unlock": {
            "name": "Kurosaki Hollowbane",
            "title": "The Substitute Shinigami",
            "role": "True Boss/Shinigami",
            "cost": 9000,
            "hp": 6000,
            "damage": 540,
            "speed": 1.7,
            "range": 220,
            "attack_cooldown": 40,
            "color": (255, 155, 55),
            "color_dark": (10, 10, 15),
            "skill_name": "Getsuga Tensho",
            "skill_desc": "Getsuga tensho + bankai storm + flash step + final getsuga",
            "skill_cooldown": 440,
            "skill_damage": 1340,
            "skill_range": 260,
            "description": "Shinigami pengganti dari Level 54",
        },
    },

}


def _apply_boss_rebalancing():
    """
    Rebalance semua mini boss dan true boss:
    - Mini Boss: HP & damage di-boost terutama di level awal/menengah agar
      tidak terlalu mudah dikalahkan oleh tower dan hero pemain.
    - True Boss: HP & damage di-boost signifikan agar menjadi pertempuran akhir
      yang epik, menantang, dan seimbang.
    - hero_unlock tetap dipertahankan sesuai aslinya untuk hero unlock pemain.
    """
    # Rebalance Mini Bosses
    for btype, bdata in MINI_BOSS_TYPES.items():
        hu = bdata.get("hero_unlock")
        hp = bdata.get("hp", 3000)
        dmg = bdata.get("damage", 50)
        ab_dmg = bdata.get("ability_damage", 100)

        if hp < 10000:
            new_hp = max(7500, int(hp * 2.2))
        elif hp < 20000:
            new_hp = int(hp * 1.6)
        elif hp < 40000:
            new_hp = int(hp * 1.4)
        else:
            new_hp = int(hp * 1.3)

        if dmg < 100:
            new_dmg = max(85, int(dmg * 1.4))
        elif dmg < 200:
            new_dmg = int(dmg * 1.25)
        else:
            new_dmg = int(dmg * 1.2)

        bdata["hp"] = new_hp
        bdata["damage"] = new_dmg
        bdata["ability_damage"] = max(ab_dmg, int(ab_dmg * 1.25))

        for k in ["skill_q_damage", "skill_w_damage", "skill_e_damage", "skill_r_damage"]:
            if k in bdata and bdata[k] > 0:
                bdata[k] = int(bdata[k] * 1.25)

        if hu:
            bdata["hero_unlock"] = hu

    # Rebalance True Bosses
    for btype, bdata in TRUE_BOSS_TYPES.items():
        hu = bdata.get("hero_unlock")
        hp = bdata.get("hp", 15000)
        dmg = bdata.get("damage", 100)
        ab_dmg = bdata.get("ability_damage", 200)

        if hp < 20000:
            new_hp = max(36000, int(hp * 2.4))
        elif hp < 40000:
            new_hp = int(hp * 2.0)
        elif hp < 70000:
            new_hp = int(hp * 1.6)
        else:
            new_hp = int(hp * 1.45)

        if dmg < 120:
            new_dmg = max(145, int(dmg * 1.5))
        elif dmg < 250:
            new_dmg = int(dmg * 1.3)
        else:
            new_dmg = int(dmg * 1.25)

        bdata["hp"] = new_hp
        bdata["damage"] = new_dmg
        bdata["ability_damage"] = max(ab_dmg, int(ab_dmg * 1.35))

        for k in ["skill_q_damage", "skill_w_damage", "skill_e_damage", "skill_r_damage"]:
            if k in bdata and bdata[k] > 0:
                bdata[k] = int(bdata[k] * 1.35)

        if hu:
            bdata["hero_unlock"] = hu


_apply_boss_rebalancing()


def get_all_boss_types():
    """Get gabungan semua boss types"""
    all_bosses = {}
    all_bosses.update(MINI_BOSS_TYPES)
    all_bosses.update(TRUE_BOSS_TYPES)
    return all_bosses