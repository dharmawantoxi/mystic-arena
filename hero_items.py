"""
hero_items.py - HERO ITEM SYSTEM (Mystic Arena)

Menambahkan 8 item peningkat hero yang terinspirasi dari item-item legendaris
MOBA. STAT & VISUAL diusahakan sama dengan acuan, NAMA diganti supaya bebas
hak cipta:

  1. Dead Edge        (terinspirasi dari Daedalus)
  2. Holy Rapier      (terinspirasi dari Divine Rapier)
  3. Demon Maw        (terinspirasi dari Satanic)
  4. Leviathan Heart  (terinspirasi dari Heart of Tarrasque)
  5. Cleave Axe       (terinspirasi dari Battle Fury)
  6. Steel Aegis      (terinspirasi dari Assault Cuirass)
  7. Moon Shard       (nama generik, terinspirasi dari Moon Shard)
  8. Octarine Core    (nama generik, terinspirasi dari Octarine Core)

Paket item LEGENDARY (Tier II) - 8 item tambahan terinspirasi Dota 2,
nama diganti supaya bebas hak cipta, stat & pasif direbalance ke
ekonomi game ini:

  9. Scarlet Bulwark  (terinspirasi dari Crimson Guard)
 10. Monarch Wings    (terinspirasi dari Butterfly)
 11. Corroder         (terinspirasi dari Desolator)
 12. Tempest Vane     (terinspirasi dari Wind Waker)
 13. Fenrir Chain     (terinspirasi dari Gleipnir)
 14. Sanguine Thorn   (terinspirasi dari Bloodthorn)
 15. Abyss Breaker    (terinspirasi dari Abyssal Blade)
 16. Thunder Coil     (terinspirasi dari Mjollnir)

Paket item MYTHIC (Tier III) - 8 item tambahan terinspirasi Dota 2,
nama diganti supaya bebas hak cipta, stat & pasif direbalance ke
ekonomi game ini:

 17. Razor Carapace   (terinspirasi dari Blade Mail)
 18. Everfrost Guard  (terinspirasi dari Shiva's Guard)
 19. Sundering Cudgel (terinspirasi dari Monkey King Bar)
 20. Frostbound Eye   (terinspirasi dari Eye of Skadi)
 21. Gale Pike        (terinspirasi dari Hurricane Pike)
 22. Basilisk Breath  (terinspirasi dari Hydra's Breath)
 23. Solar Brand      (terinspirasi dari Radiance)
 24. Runic Gavel      (terinspirasi dari Khanda)

Item ORISINAL (bukan adaptasi Dota) - kemampuan inti anti-heal:

 25. Searbrand        - aura Cauterize 300px: musuh di dekat HILANG
                        50% kemampuan heal-nya (anti-heal permanen)
                        + bakar 6 dmg/dtk; Brand Burst saat >=2 musuh
                        dekat (110 magic dmg + bakar 22 dmg/dtk 3 dtk).

Crimson Guard TIDAK diduplikasi: di Tier II sudah ada "Scarlet
Bulwark" yang merupakan adaptasi langsung item tersebut.

Toko ITEM FORGE kini 4 halaman (tab TIER I / TIER II / TIER III di
bawah info hero) karena katalog berisi 25 item.

ITEM FORGE tidak lagi mewajibkan klik hero di peta dulu: grid item
selalu ditampilkan, dan ada strip "BUY FOR" berisi daftar hero yang
sudah di-summon (masih hidup). Klik chip hero di strip untuk memilih
siapa penerima pembelian berikutnya - jadi Moon Shard dkk. bisa dibeli
langsung dari toko untuk hero mana pun.

Tiap hero punya 3 slot item. Item beli pakai GOLD in-game, bisa didrop
(klik kanan slot di panel item), dan HILANG saat hero mati KECUALI Holy
Rapier yang memang rontok (tidak balik).

Modul ini menengahi:
  - ITEM_CATALOG       data stat/harga/deskripsi
  - HeroItemInventory  logika stat + pasif
  - ItemShopUI         overlay toko item (bisa tanpa hero terseleksi)
  - HeroItemRenderer   gambar 3 slot di HeroPanel
"""

import os
import math
import random

import pygame
from localization import tr, get_language

# Konstanta gameplay
MAX_ITEM_SLOTS = 6
# Harga semua item diseragamkan (4500G - sebanding dengan upgrade
# hero level 7-8, terjangkau di mid-late game 12-15 menit).
ITEM_FLAT_COST = 4500

# Kategori item (dipakai AI & sorting UI)
CATEGORY_CRIT     = "crit"
CATEGORY_DAMAGE   = "damage"
CATEGORY_LIFESTEAL= "lifesteal"
CATEGORY_TANK     = "tank"
CATEGORY_SPLASH   = "splash"
CATEGORY_AS_ARMOR = "as_armor"
CATEGORY_AS       = "attack_speed"
CATEGORY_CASTER   = "caster"
# Kategori Tier II (paket legendary)
CATEGORY_GUARD    = "guard"      # block + proteksi tim
CATEGORY_AGILITY  = "agility"    # evasion + attack speed
CATEGORY_SHRED    = "shred"      # pengurang armor musuh
CATEGORY_UTILITY  = "utility"    # mobilitas / kebal sesaat
CATEGORY_CONTROL  = "control"    # stun / root
CATEGORY_BURST    = "burst"      # amplifikasi damage
CATEGORY_STATIC   = "static"     # sambaran petir
# Kategori Tier III (paket mythic - terinspirasi Dota 2, nama orisinal)
CATEGORY_THORN    = "thorn"      # balikin damage (Blade Mail)
CATEGORY_FROST    = "frost"      # armor + slow aura (Shiva's Guard)
CATEGORY_PIERCE   = "pierce"     # tembus evasion + mini stun (MKB)
CATEGORY_ICE      = "ice"        # slow + anti-heal on-hit (Eye of Skadi)
CATEGORY_REACH    = "reach"      # jarak tembak + mobilitas (Hurricane Pike)
CATEGORY_POISON   = "poison"     # racun % HP + multi-tembak (Hydra's Breath)
CATEGORY_INFERNO  = "inferno"    # bakar area (Radiance)
CATEGORY_ARCANE   = "arcane"     # damage + CDR + proc magic (Khanda)
CATEGORY_MORTAL   = "mortal"     # anti-heal area (Searbrand - orisinal)

# ════════════════════════════════════════════════════════════
# MIASMA TRACKER (Basilisk Breath - racun % Max HP per tick)
# Disimpan di module-level keyed by id(target) supaya tidak perlu
# menambah field apa pun ke Hero/Minion/Boss. Setiap tracker
# memiliki: source (pemilik item), timer, tick_cd, damage.
# ════════════════════════════════════════════════════════════
_MIASMA = {}


def _apply_miasma(target, source, data):
    """Pasang/perbarui racun Miasma pada ``target``."""
    if target is None or not getattr(target, "alive", False):
        return
    key = id(target)
    prev = _MIASMA.get(key)
    dmg = int(getattr(target, "max_hp", 0)
              * data["max_hp_pct_per_tick"])
    dmg = max(6, min(data.get("cap_damage", 9999), dmg))
    if prev is None:
        _MIASMA[key] = {"target": target, "source": source,
                        "damage": dmg, "timer": data["duration"],
                        "tick_cd": data["tick"]}
    else:
        prev["source"] = source
        prev["damage"] = max(prev["damage"], dmg)
        prev["timer"] = max(prev["timer"], data["duration"])
        prev["tick_cd"] = min(prev["tick_cd"], data["tick"])


def _tick_miasma(dt=1):
    """Kurangi timer semua racun aktif & terapkan damage per tick."""
    if not _MIASMA:
        return
    expired = []
    for key, m in _MIASMA.items():
        tgt = m["target"]
        if tgt is None or not getattr(tgt, "alive", False):
            expired.append(key)
            continue
        m["timer"] -= dt
        m["tick_cd"] -= dt
        if m["tick_cd"] <= 0:
            m["tick_cd"] = 30
            src = m["source"]
            team = getattr(src, "team", None)
            try:
                tgt.take_damage(m["damage"], team, "magic")
            except TypeError:
                tgt.take_damage(m["damage"], team)
            _fx_notify(tgt, "POISON", (140, 220, 90))
        if m["timer"] <= 0:
            expired.append(key)
    for key in expired:
        _MIASMA.pop(key, None)


# ════════════════════════════════════════════════════════════
# KATALOG ITEM
# Catatan keseimbangan: hero starter punya ~30-45 damage,
# 450-1400 HP, attack_cooldown 30-52 frame. Harga item
# disesuaikan ekonomi game (pasif gold 180/menit, reward kill
# ~8-65 gold, hero reward 150).
# ════════════════════════════════════════════════════════════
ITEM_CATALOG = {
    "dead_edge": {
        "name": "Dead Edge",
        "category": CATEGORY_CRIT,
        "cost": ITEM_FLAT_COST,
        "icon": "dead_edge.png",
        "color": (220, 60, 60),
        "glow": (255, 90, 90),
        "stats": {
            "damage": 45,
            "crit_chance": 0.25,
            "crit_mult": 2.0,
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": "+45 Damage. 25% peluang Critical Strike (200% damage).",
        "desc_en": "+45 Damage. 25% chance to Critical Strike (200% damage).",
        "flavor": "Tebasan maut yang berdentang di ujung setiap medan tempur.",
    },

    "holy_rapier": {
        "name": "Holy Rapier",
        "category": CATEGORY_DAMAGE,
        "cost": ITEM_FLAT_COST,
        "icon": "holy_rapier.png",
        "color": (255, 220, 80),
        "glow": (255, 245, 150),
        "stats": {
            "damage": 120,
        },
        "melee_only": False,
        # Rapier suci RONTOK saat pemilik tumbang - tidak bisa diambil
        # kembali (sesuai sifat aslinya).
        "drops_on_death": True,
        "desc": "+120 Damage. HILANG saat hero mati (tidak dijatuhkan).",
        "desc_en": "+120 Damage. LOST when the hero dies (not dropped).",
        "flavor": "Kilau cahaya yang hanya pantas dipegang oleh yang hidup.",
    },

    "demon_maw": {
        "name": "Demon Maw",
        "category": CATEGORY_LIFESTEAL,
        "cost": ITEM_FLAT_COST,
        "icon": "demon_maw.png",
        "color": (180, 30, 30),
        "glow": (255, 70, 70),
        "stats": {
            "damage": 20,
            "armor": 4,
            "lifesteal": 0.20,
        },
        "active": {
            # Unholy Rage otomatis menyala saat HP kritis
            "name": "Blood Frenzy",
            "hp_threshold": 0.35,
            "lifesteal_bonus": 1.20,   # total 20% + 120% = 140%
            "duration": 300,           # 5 detik
            "cooldown": 1500,          # 25 detik
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+20 Damage, +4 Armor, 20% Lifesteal. "
                 "Saat HP < 35%: aktif Blood Frenzy, lifesteal 140% "
                 "selama 5 detik."),
        "desc_en": ("+20 Damage, +4 Armor, 20% Lifesteal. "
                    "Below 35% HP: Blood Frenzy activates, "
                    "140% lifesteal for 5 seconds."),
        "flavor": "Topeng iblis yang lapar akan darah lawan.",
    },

    "leviathan_heart": {
        "name": "Leviathan Heart",
        "category": CATEGORY_TANK,
        "cost": ITEM_FLAT_COST,
        "icon": "leviathan_heart.png",
        "color": (80, 220, 120),
        "glow": (130, 255, 160),
        "stats": {
            "hp_pct": 0.35,
            "hp_regen": 6.0,
        },
        # Pasif kedua: regen besar (1.5% max HP/detik) jika tidak
        # menerima damage selama 5 detik.
        "passive": {
            "name": "Leviathan Vitality",
            "out_of_combat_regen_pct": 0.015,
            "combat_timeout": 300,
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+35% Max HP, +6 HP/reg. Di luar pertempuran (5 dtk "
                 "tanpa damage): regenerasi 1.5% Max HP per detik."),
        "desc_en": ("+35% Max HP, +6 HP regen. Out of combat (5s "
                    "without damage): regenerate 1.5% Max HP per "
                    "second."),
        "flavor": "Jantung purba yang berdegup menyamai lautan.",
    },

    "cleave_axe": {
        "name": "Cleave Axe",
        "category": CATEGORY_SPLASH,
        "cost": ITEM_FLAT_COST,
        "icon": "cleave_axe.png",
        "color": (200, 220, 240),
        "glow": (150, 210, 255),
        "stats": {
            "damage": 30,
            "hp_regen": 3.0,
        },
        "passive": {
            "name": "Cleave",
            "cleave_pct": 0.50,
            "cleave_radius": 110,
        },
        "melee_only": True,
        "drops_on_death": False,
        "desc": ("+30 Damage, +3 HP/reg. Serangan melee membelah: 50% "
                 "damage ke musuh dalam radius 110 (hanya melee)."),
        "desc_en": ("+30 Damage, +3 HP regen. Melee attacks cleave: "
                    "50% damage to enemies within 110 radius (melee "
                    "only)."),
        "flavor": "Kapak berukir yang menebas apapun di depannya.",
    },

    "steel_aegis": {
        "name": "Steel Aegis",
        "category": CATEGORY_AS_ARMOR,
        "cost": ITEM_FLAT_COST,
        "icon": "steel_aegis.png",
        "color": (180, 200, 230),
        "glow": (120, 170, 255),
        "stats": {
            "armor": 4,
            "attack_speed": 30,
        },
        "aura": {
            # Aura diratakan oleh update_auras()
            "name": "Steel Aura",
            "ally_radius": 320,
            "ally_armor": 2,
            "ally_attack_speed": 10,
            "enemy_radius": 320,
            "enemy_armor_reduction": 2,
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+4 Armor, +30 Attack Speed. Aura: sekutu di dekat "
                 "dapat +2 Armor & +10 AS; musuh di dekat kehilangan "
                 "2 Armor."),
        "desc_en": ("+4 Armor, +30 Attack Speed. Aura: nearby allies "
                    "gain +2 Armor & +10 AS; nearby enemies lose 2 "
                    "Armor."),
        "flavor": "Zirah baja yang berdenyut memberi semangat kawan.",
    },

    "moon_shard": {
        "name": "Moon Shard",
        "category": CATEGORY_AS,
        "cost": ITEM_FLAT_COST,
        "icon": "moon_shard.png",
        "color": (130, 220, 255),
        "glow": (180, 240, 255),
        "stats": {
            "attack_speed": 60,
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": "+60 Attack Speed. Serangan secepat cahaya bulan.",
        "desc_en": "+60 Attack Speed. Strikes as fast as moonlight.",
        "flavor": "Serpihan rembulan yang membeku jadi kristal.",
    },

    "octarine_core": {
        "name": "Octarine Core",
        "category": CATEGORY_CASTER,
        "cost": ITEM_FLAT_COST,
        "icon": "octarine_core.png",
        "color": (180, 80, 230),
        "glow": (220, 130, 255),
        "stats": {
            "hp": 300,
            "cooldown_reduction": 0.15,
            "spell_vamp": 0.10,
            "hp_regen": 2.0,
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+300 HP, +2 HP/reg, 15% Cooldown Reduction, 10% Spell "
                 "Lifesteal (heal = 10% damage skill yang dikeluarkan)."),
        "desc_en": ("+300 HP, +2 HP regen, 15% Cooldown Reduction, 10% "
                    "Spell Lifesteal (heal = 10% of skill damage "
                    "dealt)."),
        "flavor": "Inti ungu yang berputar dengan kekuatan arcane.",
    },

    # ════════════════════════════════════════════════════════
    # TIER II - ITEM LEGENDARY (paket Dota 2, direbalance)
    # ════════════════════════════════════════════════════════
    "scarlet_bulwark": {
        "name": "Scarlet Bulwark",
        "category": CATEGORY_GUARD,
        "cost": 5000,
        "icon": "scarlet_bulwark.png",
        "color": (200, 60, 60),
        "glow": (255, 110, 110),
        "stats": {
            "hp": 250,
            "hp_regen": 8,
            "armor": 6,
        },
        # Damage Block pasif (warisan Vanguard): peluang memblokir
        # sejumlah damage fisik per serangan yang diterima.
        "block": {
            "chance": 0.55,
            "melee_block": 25,
            "ranged_block": 14,
        },
        "active": {
            # Bulwark Guard: auto saat HP kritis - diri sendiri +
            # sekutu dekat memblokir damage tetap per serangan.
            "name": "Bulwark Guard",
            "hp_threshold": 0.45,
            "ally_radius": 320,
            "base_block": 35,
            "max_hp_block_pct": 0.02,
            "duration": 420,       # 7 detik
            "cooldown": 2400,      # 40 detik
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+250 HP, +8 HP/reg, +6 Armor. Blok pasif 55% (25 "
                 "dmg). Saat HP < 45%: Guard 7 dtk, kamu & sekutu "
                 "dekat blokir 35+2% Max HP per serangan."),
        "desc_en": ("+250 HP, +8 HP regen, +6 Armor. Passive block 55% "
                    "(25 dmg). Below 45% HP: Guard for 7s, you & "
                    "nearby allies block 35 + 2% Max HP per attack."),
        "flavor": "Perisai kirmizi penahan amukan Tahun Kegelapan.",
    },

    "monarch_wings": {
        "name": "Monarch Wings",
        "category": CATEGORY_AGILITY,
        "cost": 5000,
        "icon": "monarch_wings.png",
        "color": (230, 140, 220),
        "glow": (255, 190, 250),
        "stats": {
            "damage": 35,
            "attack_speed": 30,
            "evasion": 0.28,
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+35 Damage, +30 Attack Speed, 28% Evasion (peluang "
                 "menghindari serangan fisik sepenuhnya)."),
        "desc_en": ("+35 Damage, +30 Attack Speed, 28% Evasion (chance "
                    "to fully dodge physical attacks)."),
        "flavor": "Sayap raja kupu-kupu yang menolak setiap bilah.",
    },

    "corroder": {
        "name": "Corroder",
        "category": CATEGORY_SHRED,
        "cost": 4500,
        "icon": "corroder.png",
        "color": (140, 220, 90),
        "glow": (190, 255, 140),
        "stats": {
            "damage": 42,
        },
        "passive": {
            # Serangan mengikis armor target (negatif = damage
            # diterima lebih besar, rumus sama dengan armor).
            "name": "Corrosion",
            "armor_shred": 6,
            "duration": 360,       # 6 detik
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+42 Damage. Serangan mengikis 6 Armor target "
                 "selama 6 detik (target menerima damage lebih "
                 "besar)."),
        "desc_en": ("+42 Damage. Attacks shred 6 Armor from the target "
                    "for 6 seconds (target takes more damage)."),
        "flavor": "Bilah berkarat yang melarutkan zirah dan daging.",
    },

    "tempest_vane": {
        "name": "Tempest Vane",
        "category": CATEGORY_UTILITY,
        "cost": 5500,
        "icon": "tempest_vane.png",
        "color": (120, 210, 230),
        "glow": (180, 240, 255),
        "stats": {
            "hp": 250,
            "hp_regen": 4,
            "move_speed_pct": 0.12,
        },
        "active": {
            # Tempest Veil: auto saat HP kritis - kebal semua
            # damage & tidak bisa menyerang (layaknya Cyclone).
            "name": "Tempest Veil",
            "hp_threshold": 0.40,
            "duration": 150,       # 2.5 detik
            "cooldown": 1800,      # 30 detik
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+250 HP, +4 HP/reg, +12% Move Speed. Saat HP < "
                 "40%: kebal semua damage 2.5 dtk (tidak bisa "
                 "menyerang), cooldown 30 dtk."),
        "desc_en": ("+250 HP, +4 HP regen, +12% Move Speed. Below 40% "
                    "HP: immune to all damage for 2.5s (cannot "
                    "attack), 30s cooldown."),
        "flavor": "Baling-baling angin yang menyembunyikan pemakainya.",
    },

    "fenrir_chain": {
        "name": "Fenrir Chain",
        "category": CATEGORY_CONTROL,
        "cost": 5250,
        "icon": "fenrir_chain.png",
        "color": (240, 190, 90),
        "glow": (255, 230, 150),
        "stats": {
            "damage": 30,
            "attack_speed": 30,
            "hp": 250,
        },
        "on_attack": {
            # Arc Chain (pasif Maelstrom): peluang sambaran listrik
            # yang melompat ke musuh sekitar.
            "name": "Arc Chain",
            "chance": 0.20,
            "damage": 45,
            "targets": 3,
            "radius": 240,
        },
        "active": {
            # Binding Chains (Eternal Chains): auto saat >= 2 musuh
            # dekat - root + damage area.
            "name": "Binding Chains",
            "trigger_enemies": 2,
            "trigger_radius": 220,
            "root_radius": 220,
            "root_duration": 72,   # 1.2 detik
            "damage": 80,
            "cooldown": 1080,      # 18 detik
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+30 Damage, +30 AS, +250 HP. 20% serangan menyambar "
                 "3 musuh (45 dmg). Saat >=2 musuh dekat: rantai "
                 "mengikat mereka 1.2 dtk + 80 dmg."),
        "desc_en": ("+30 Damage, +30 AS, +250 HP. 20% of attacks chain "
                    "to 3 enemies (45 dmg). When 2+ enemies are near: "
                    "chains root them for 1.2s + 80 dmg."),
        "flavor": "Rantai para dewa yang membelenggu serigala purba.",
    },

    "sanguine_thorn": {
        "name": "Sanguine Thorn",
        "category": CATEGORY_BURST,
        "cost": 6000,
        "icon": "sanguine_thorn.png",
        "color": (230, 60, 110),
        "glow": (255, 120, 160),
        "stats": {
            "damage": 25,
            "attack_speed": 60,
            "hp_regen": 5,
        },
        "active": {
            # Soul Rend: auto saat menyerang - target ter-silence,
            # semua seranganmu ke target crit 150%, target menerima
            # +30% damage.
            "name": "Soul Rend",
            "duration": 300,       # 5 detik
            "crit_mult": 1.5,
            "damage_amp": 0.30,
            "cooldown": 1080,      # 18 detik
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+25 Damage, +60 AS, +5 HP/reg. Soul Rend (auto): "
                 "silence target 5 dtk, seranganmu ke target crit "
                 "150%, target menerima +30% damage."),
        "desc_en": ("+25 Damage, +60 AS, +5 HP regen. Soul Rend (auto): "
                    "silences the target for 5s, your attacks on it "
                    "crit for 150%, target takes +30% damage."),
        "flavor": "Duri darah yang menagih nyawa setiap korbannya.",
    },

    "abyss_breaker": {
        "name": "Abyss Breaker",
        "category": CATEGORY_CONTROL,
        "cost": 5500,
        "icon": "abyss_breaker.png",
        "color": (90, 130, 220),
        "glow": (140, 180, 255),
        "stats": {
            "damage": 35,
            "hp": 300,
            "hp_regen": 3,
            "heal_amp": 0.16,
            "slow_resist": 0.30,
        },
        "bash": {
            # Bash pasif: peluang stun + bonus damage per serangan.
            "chance": 0.22,
            "damage": 55,
            "stun": 54,            # 0.9 detik
            "cooldown": 140,       # 2.3 detik internal
        },
        "active": {
            # Overwhelm: auto saat menyerang - stun penuh target.
            "name": "Overwhelm",
            "stun": 72,            # 1.2 detik
            "cooldown": 1500,      # 25 detik
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+35 Damage, +300 HP, +16% heal diterima, +30% "
                 "tahan slow. Bash 22%: stun 0.9 dtk + 55 dmg. "
                 "Overwhelm (auto): stun target 1.2 dtk."),
        "desc_en": ("+35 Damage, +300 HP, +16% incoming heal, +30% "
                    "slow resist. Bash 22%: stun 0.9s + 55 dmg. "
                    "Overwhelm (auto): stuns the target for 1.2s."),
        "flavor": "Pedang Komandan Jurang yang memutus jiwa.",
    },

    "thunder_coil": {
        "name": "Thunder Coil",
        "category": CATEGORY_STATIC,
        "cost": 5250,
        "icon": "thunder_coil.png",
        "color": (250, 220, 90),
        "glow": (255, 245, 160),
        "stats": {
            "damage": 25,
            "attack_speed": 65,
        },
        "on_attack": {
            # Arc Lightning pasif: peluang sambaran berantai.
            "name": "Arc Lightning",
            "chance": 0.22,
            "damage": 40,
            "targets": 3,
            "radius": 240,
        },
        "active": {
            # Static Charge: 20% saat menerima damage -> perisai
            # bermuatan yang menyambar musuh sekitar tiap 0.5 dtk.
            "name": "Static Charge",
            "proc_chance": 0.20,
            "duration": 480,       # 8 detik
            "tick": 30,            # zap tiap 0.5 detik
            "damage": 65,
            "targets": 4,
            "radius": 260,
            "cooldown": 1200,      # 20 detik
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+25 Damage, +65 AS. 22% serangan menyambar 3 musuh "
                 "(40 dmg). Saat dipukul: 20% perisai statis 8 dtk, "
                 "menyambar 4 musuh tiap 0.5 dtk (65 dmg)."),
        "desc_en": ("+25 Damage, +65 AS. 22% of attacks chain to 3 "
                    "enemies (40 dmg). When hit: 20% chance of a "
                    "static shield for 8s, zapping 4 enemies every "
                    "0.5s (65 dmg)."),
        "flavor": "Kumparan badai yang ditempa palu dewa guntur.",
    },

    # ════════════════════════════════════════════════════════
    # TIER III - ITEM MYTHIC (paket Dota 2 7.41, direbalance)
    # Catatan: Crimson Guard SUDAH ada sebagai "Scarlet Bulwark"
    # di Tier II, jadi tidak diduplikasi di sini.
    # ════════════════════════════════════════════════════════
    "razor_carapace": {
        "name": "Razor Carapace",
        "category": CATEGORY_THORN,
        "cost": 5000,
        "icon": "razor_carapace.png",
        "color": (180, 180, 200),
        "glow": (230, 230, 255),
        "stats": {
            "damage": 18,
            "armor": 8,
            "cooldown_reduction": 0.10,
        },
        "active": {
            # Thornmail: otomatis menyala saat HP < 55% - semua
            # damage yang DITERIMA dipantulkan 85% ke penyerang
            # (magic damage, dikurangi per perhitungan game ini).
            "name": "Thornmail",
            "hp_threshold": 0.55,
            "reflect_pct": 0.85,
            "duration": 270,       # 4.5 detik
            "cooldown": 1500,      # 25 detik
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+18 Damage, +8 Armor, 10% CDR. Saat HP < 55%: "
                 "Thornmail 4.5 dtk - pantulkan 85% damage yang "
                 "kamu terima ke penyerang."),
        "desc_en": ("+18 Damage, +8 Armor, 10% CDR. Below 55% HP: "
                    "Thornmail for 4.5s - reflect 85% of damage you "
                    "take back to the attacker."),
        "flavor": "Cangkang bergerigi yang membalas setiap luka.",
    },

    "everfrost_guard": {
        "name": "Everfrost Guard",
        "category": CATEGORY_FROST,
        "cost": 5500,
        "icon": "everfrost_guard.png",
        "color": (120, 190, 230),
        "glow": (180, 230, 255),
        "stats": {
            "armor": 10,
            "hp_regen": 5,
            "cooldown_reduction": 0.10,
        },
        "aura": {
            # Freezing Aura: musuh di dekat lambat attack speed &
            # heal-nya dipotong (tanpa mengubah kode inti).
            "name": "Freezing Aura",
            "enemy_radius": 300,
            "enemy_atk_slow": 0.30,
            "enemy_anti_heal": 0.40,
        },
        "active": {
            # Arctic Blast: otomatis saat >= 2 musuh dekat -
            # ledakan es yang melukai + memperlambat.
            "name": "Arctic Blast",
            "trigger_enemies": 2,
            "radius": 280,
            "damage": 130,
            "slow": 0.45,
            "slow_duration": 210,  # 3.5 detik
            "cooldown": 1440,      # 24 detik
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+10 Armor, +5 HP/reg, 10% CDR. Aura: musuh "
                 "dekat -30% AS & heal -40%. Saat >=2 musuh dekat: "
                 "Arctic Blast 130 dmg + slow 45% (3.5 dtk)."),
        "desc_en": ("+10 Armor, +5 HP regen, 10% CDR. Aura: "
                    "nearby enemies lose 30% AS & 40% healing. When "
                    "2+ enemies are near: Arctic Blast 130 dmg + 45% "
                    "slow for 3.5s."),
        "flavor": "Bongkahan es abadi yang membekukan setiap denyut nadi.",
    },

    "sundering_cudgel": {
        "name": "Sundering Cudgel",
        "category": CATEGORY_PIERCE,
        "cost": 5000,
        "icon": "sundering_cudgel.png",
        "color": (230, 180, 70),
        "glow": (255, 220, 130),
        "stats": {
            "damage": 45,
            "attack_speed": 25,
        },
        "bash": {
            # Piercing Bash: peluang mini-stun + bonus damage.
            # TRUE STRIKE (tembus evasion) selalu aktif di pemilik.
            "name": "Piercing Bash",
            "chance": 0.28,
            "damage": 55,
            "stun": 15,            # 0.25 detik
            "cooldown": 120,       # 2 detik internal
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+45 Damage, +25 AS. Serangan TIDAK PERNAH meleset "
                 "(True Strike). 28% serangan memukul mundir target: "
                 "stun 0.25 dtk + 55 dmg (CD 2 dtk)."),
        "desc_en": ("+45 Damage, +25 AS. Your attacks NEVER miss "
                    "(True Strike). 28% of attacks bash the target: "
                    "0.25s stun + 55 dmg (2s cooldown)."),
        "flavor": "Tongkat pemukul legendaris yang menembus segala kilah.",
    },

    "frostbound_eye": {
        "name": "Frostbound Eye",
        "category": CATEGORY_ICE,
        "cost": 5250,
        "icon": "frostbound_eye.png",
        "color": (120, 200, 220),
        "glow": (180, 240, 255),
        "stats": {
            "damage": 20,
            "hp": 250,
            "hp_regen": 4,
        },
        "on_attack": {
            # Frostbite: tiap serangan basic memperlambat target &
            # memotong heal yang diterimanya.
            "name": "Frostbite",
            "slow": 0.28,
            "atk_slow": 0.28,
            "anti_heal": 0.45,
            "duration": 180,       # 3 detik
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+20 Damage, +250 HP, +4 HP/reg. Tiap serangan "
                 "memperlambat 28% (gerak & serang) + anti-heal 45% "
                 "selama 3 detik."),
        "desc_en": ("+20 Damage, +250 HP, +4 HP regen. Each attack "
                    "slows by 28% (move & attack) and applies 45% "
                    "anti-heal for 3 seconds."),
        "flavor": "Mata es yang membekukan darah di setiap luka.",
    },

    "gale_pike": {
        "name": "Gale Pike",
        "category": CATEGORY_REACH,
        "cost": 5250,
        "icon": "gale_pike.png",
        "color": (150, 230, 200),
        "glow": (200, 255, 230),
        "stats": {
            "damage": 18,
            "attack_speed": 25,
            "hp": 200,
            "hp_regen": 3,
            "range_bonus": 90,     # hanya untuk hero ranged
                 # (dulu 130 - terlalu OP untuk hero ranged; di-nerf)
        },
        "active": {
            # Gale Leap: otomatis saat HP < 40% - dorong diri ke
            # arah berlawanan target (mundur) + bonus attack speed.
            "name": "Gale Leap",
            "hp_threshold": 0.40,
            "dash_distance": 130,
            "as_bonus": 55,
            "duration": 180,       # 3 detik
            "cooldown": 1500,      # 25 detik
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+18 Damage, +25 AS, +200 HP, +3 HP/reg, +90 "
                 "jangkauan (ranged). Saat HP < 40%: Gale Leap - "
                 "mundur 130px + +55 AS selama 3 dtk (CD 25 dtk)."),
        "desc_en": ("+18 Damage, +25 AS, +200 HP, +3 HP regen, +90 "
                    "attack range (ranged). Below 40% HP: Gale Leap - "
                    "dash back 130px + +55 AS for 3s (25s CD)."),
        "flavor": "Tombak angin yang mengulur jarak secepat kilat.",
    },

    "basilisk_breath": {
        "name": "Basilisk Breath",
        "category": CATEGORY_POISON,
        "cost": 5750,
        "icon": "basilisk_breath.png",
        "color": (140, 210, 90),
        "glow": (190, 255, 130),
        "stats": {
            "damage": 22,
            "attack_speed": 30,
            "hp": 180,
            "range_bonus": 120,    # hanya untuk hero ranged
        },
        "on_attack": {
            # Miasma: racun yang berdenyut berdasarkan Max HP
            # target. Tick 0.5 dtk, dibatasi 60/tick supaya boss
            # tidak meleleh seketika.
            "name": "Miasma",
            "max_hp_pct_per_tick": 0.022,
            "tick": 30,            # 0.5 detik
            "duration": 180,       # 3 detik
            "cap_damage": 60,
        },
        "multishot": {
            # Polycephaly: peluang menembak 2 musuh lain di dekat
            # target dengan 70% damage (magic). Hanya ranged.
            "name": "Polycephaly",
            "chance": 0.30,
            "targets": 2,
            "radius": 200,
            "damage_pct": 0.70,
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+22 Damage, +30 AS, +180 HP, +120 jangkauan "
                 "(ranged). Serangan meracuni: 2.2% Max HP/0.5 dtk "
                 "selama 3 dtk (maks 60/tick). 30% tembakan menyambar "
                 "2 musuh lain (70% dmg)."),
        "desc_en": ("+22 Damage, +30 AS, +180 HP, +120 range (ranged). "
                    "Attacks poison: 2.2% Max HP per 0.5s for 3s (cap "
                    "60/tick). 30% of shots hit 2 other enemies (70% "
                    "damage)."),
        "flavor": "Embun racun hydra yang merayap di setiap anak panah.",
    },

    "solar_brand": {
        "name": "Solar Brand",
        "category": CATEGORY_INFERNO,
        "cost": 5500,
        "icon": "solar_brand.png",
        "color": (255, 190, 60),
        "glow": (255, 230, 140),
        "stats": {
            "damage": 30,
            "hp": 280,
            "hp_regen": 5,
        },
        "aura": {
            # Scorched Earth: bakar musuh di dekat tiap 0.5 dtk &
            # kecilkan peluang serangannya (buta ringan).
            "name": "Scorched Earth",
            "enemy_radius": 280,
            "burn_dps": 28,
            "blind": 0.18,
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+30 Damage, +280 HP, +5 HP/reg. Aura: musuh dalam "
                 "280px terbakar 28 dmg/dtk & serangannya 18% lebih "
                 "sering meleset."),
        "desc_en": ("+30 Damage, +280 HP, +5 HP regen. Aura: enemies "
                    "within 280px burn for 28 dmg/s and have 18% more "
                    "chance to miss."),
        "flavor": "Cap matahari yang membakar apa pun yang mendekat.",
    },

    "runic_gavel": {
        "name": "Runic Gavel",
        "category": CATEGORY_ARCANE,
        "cost": 5250,
        "icon": "runic_gavel.png",
        "color": (200, 130, 240),
        "glow": (235, 180, 255),
        "stats": {
            "damage": 28,
            "hp": 250,
            "hp_regen": 4,
            "cooldown_reduction": 0.15,
        },
        "passive": {
            # Empower Strike: serangan berikutnya setiap 9 detik
            # menambah damage sihir ke target (versi sederhana dari
            # Empower Spell Khanda, tanpa mengubah rumus skill).
            "name": "Empower Strike",
            "charge_time": 540,     # 9 detik
            "damage": 130,
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+28 Damage, +250 HP, +4 HP/reg, 15% CDR. Setiap 9 "
                 "dtk: serangan berikutnya menambah 130 magic damage "
                 "ke target (Empower Strike)."),
        "desc_en": ("+28 Damage, +250 HP, +4 HP regen, 15% CDR. Every "
                    "9s your next attack adds 130 magic damage to the "
                    "target (Empower Strike)."),
        "flavor": "Palu runik yang menyimpan muatan sihir tiap hembusan.",
    },

    # ════════════════════════════════════════════════════════
    # ITEM ORISINAL (bukan adaptasi Dota): Searbrand
    # Kemampuan inti: MENGHAPUS HEAL musuh (anti-heal area).
    # ════════════════════════════════════════════════════════
    "searbrand": {
        "name": "Searbrand",
        "category": CATEGORY_MORTAL,
        "cost": 5750,
        "icon": "searbrand.png",
        "color": (235, 95, 60),
        "glow": (255, 150, 110),
        "stats": {
            "damage": 12,
            "hp": 320,
            "hp_regen": 6,
            "cooldown_reduction": 0.15,
        },
        "aura": {
            # Cauterize (KEMAMPUAN UTAMA): musuh di sekitar
            # KEHILANGAN 50% kemampuan heal-nya. Berlaku pasif
            # terus-menerus, tanpa syarat & tanpa cooldown.
            "name": "Cauterize",
            "enemy_radius": 300,
            "enemy_anti_heal": 0.50,
            "burn_dps": 6,
        },
        "active": {
            # Brand Burst: ledakan api area saat >=2 musuh dekat
            # (damage + burn lanjutan). Anti-heal UTAMA sudah
            # ditanggung aura Cauterize.
            "name": "Brand Burst",
            "trigger_enemies": 2,
            "radius": 320,
            "damage": 110,
            "burn_dps": 22,
            "burn_duration": 180,  # 3 detik
            "cooldown": 1080,      # 18 detik
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+12 Damage, +320 HP, +6 HP/reg, 15% CDR. AURA "
                 "CAUTERIZE (300px): musuh di dekat HILANG 50% "
                 "kemampuan heal-nya + bakar 6 dmg/dtk. Saat >=2 "
                 "musuh dekat: Brand Burst, 110 magic dmg + bakar "
                 "22 dmg/dtk selama 3 dtk (CD 18 dtk)."),
        "desc_en": ("+12 Damage, +320 HP, +6 HP regen, 15% CDR. "
                    "CAUTERIZE AURA (300px): nearby enemies LOSE 50% "
                    "of their healing + take 6 dmg/s burn. When 2+ "
                    "enemies are near: Brand Burst deals 110 magic "
                    "dmg and burns 22 dmg/s for 3s (18s CD)."),
        "flavor": ("Besi berpijar yang mencauter luka - apa pun yang "
                   "menerima bekasnya tak akan pernah utuh kembali."),
    },
}

# Urutan tampil di toko (sama dengan urutan permintaan pengguna)
ITEM_SHOP_ORDER = [
    # ── Halaman 1 (TIER I) ──
    "dead_edge",
    "holy_rapier",
    "demon_maw",
    "leviathan_heart",
    "cleave_axe",
    "steel_aegis",
    "moon_shard",
    "octarine_core",
    # ── Halaman 2 (TIER II - paket legendary) ──
    "scarlet_bulwark",
    "monarch_wings",
    "corroder",
    "tempest_vane",
    "fenrir_chain",
    "sanguine_thorn",
    "abyss_breaker",
    "thunder_coil",
    # ── Halaman 3 (TIER III - paket mythic) ──
    "razor_carapace",
    "everfrost_guard",
    "sundering_cudgel",
    "frostbound_eye",
    "gale_pike",
    "basilisk_breath",
    "solar_brand",
    "runic_gavel",
    # ── Halaman 4 (TIER III - lanjutan) ──
    "searbrand",
]

# Jumlah item per halaman toko (grid 4x2). 16 item = 2 halaman.
ITEMS_PER_PAGE = 8

# Kategori -> label & warna aksen di UI
CATEGORY_INFO = {
    CATEGORY_CRIT:      ("CRIT",       (255, 100, 100)),
    CATEGORY_DAMAGE:    ("DAMAGE",     (255, 200, 80)),
    CATEGORY_LIFESTEAL: ("LIFESTEAL",  (200, 60, 60)),
    CATEGORY_TANK:      ("TANK",       (90, 200, 120)),
    CATEGORY_SPLASH:    ("CLEAVE",     (150, 200, 255)),
    CATEGORY_AS_ARMOR:  ("AURA",       (130, 170, 255)),
    CATEGORY_AS:        ("SPEED",      (130, 220, 255)),
    CATEGORY_CASTER:    ("CASTER",     (190, 120, 255)),
    CATEGORY_GUARD:     ("GUARD",      (255, 120, 120)),
    CATEGORY_AGILITY:   ("AGILITY",    (255, 190, 250)),
    CATEGORY_SHRED:     ("SHRED",      (190, 255, 140)),
    CATEGORY_UTILITY:   ("UTILITY",    (180, 240, 255)),
    CATEGORY_CONTROL:   ("CONTROL",    (255, 200, 110)),
    CATEGORY_BURST:     ("BURST",      (255, 120, 160)),
    CATEGORY_STATIC:    ("STATIC",     (255, 245, 160)),
    CATEGORY_THORN:     ("THORN",      (230, 230, 255)),
    CATEGORY_FROST:     ("FROST",      (180, 230, 255)),
    CATEGORY_PIERCE:    ("PIERCE",     (255, 220, 130)),
    CATEGORY_ICE:       ("ICE",        (180, 240, 255)),
    CATEGORY_REACH:     ("REACH",      (200, 255, 230)),
    CATEGORY_POISON:    ("POISON",     (190, 255, 130)),
    CATEGORY_INFERNO:   ("INFERNO",    (255, 210, 120)),
    CATEGORY_ARCANE:    ("ARCANE",     (235, 180, 255)),
    CATEGORY_MORTAL:    ("MORTAL",     (255, 140, 100)),
}


# ════════════════════════════════════════════════════════════
# ICON LOADING & CACHE
# ════════════════════════════════════════════════════════════
_ITEMS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "assets", "items")

_ICON_CACHE = {}


def get_icon(item_id, size=48):
    """Kembalikan pygame.Surface icon item (di-cache).

    Kalau file PNG tidak ada, buat ikon prosedural sederhana supaya
    game tetap jalan (berguna untuk build tanpa aset).
    """
    cache_key = (item_id, size)
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    data = ITEM_CATALOG.get(item_id)
    if not data:
        return None

    surf = None
    path = os.path.join(_ITEMS_DIR, data["icon"])
    if os.path.exists(path):
        try:
            raw = pygame.image.load(path).convert_alpha()
            # Kotak ikon sedikit lebih besar dari size supaya border
            # bisa digambar di atasnya.
            surf = pygame.transform.smoothscale(raw, (size, size))
        except Exception:
            surf = None

    if surf is None:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(surf, data["color"], (2, 2, size - 4, size - 4),
                         border_radius=6)
        pygame.draw.rect(surf, data["glow"],
                         (2, 2, size - 4, size - 4), 2, border_radius=6)
        try:
            f = pygame.font.Font(None, 16)  # 11->16 agar kebaca
            t = f.render(data["name"][:5], True, (255, 255, 255))
            surf.blit(t, t.get_rect(center=(size // 2, size // 2)))
        except Exception:
            pass

    _ICON_CACHE[cache_key] = surf
    return surf


# ════════════════════════════════════════════════════════════
# INVENTARY per-hero
# ════════════════════════════════════════════════════════════
class HeroItemInventory:
    """Logika item per-hero: agregasi stat, pasif, lifesteal, dll.

    Diinstansiasi di Hero.__init__ sebagai ``self.items``.
    """

    def __init__(self, hero):
        self.hero = hero
        # List of item_id (str) atau None untuk slot kosong
        self.slots = [None] * MAX_ITEM_SLOTS
        # Timer aktif Demon Maw
        self.blood_frenzy_timer = 0
        self.blood_frenzy_cd = 0
        # Timer 'combat' untuk Leviathan Heart
        self.last_damage_timer = 0
        # Aura yang sedang diterima hero (di-set global oleh
        # update_auras() setiap frame)
        self.aura_armor = 0
        self.aura_as = 0
        self.aura_armor_reduction = 0
        # ═══ TIER II: timer aktif/pasif item legendary ═══
        # Scarlet Bulwark (Guard)
        self.guard_timer = 0
        self.guard_cd = 0
        # Block dari aura Guard yang diterima hero ini (di-set
        # update_auras)
        self.aura_guard_block = 0
        # Tempest Vane (Veil / kebal)
        self.veil_timer = 0
        self.veil_cd = 0
        # Fenrir Chain (Binding Chains)
        self.chains_cd = 0
        # Sanguine Thorn (Soul Rend)
        self.rend_timer = 0
        self.rend_cd = 0
        self.rend_target = None
        # Abyss Breaker (Bash internal + Overwhelm)
        self.bash_cd = 0
        self.overwhelm_cd = 0
        # Thunder Coil (Static Charge)
        self.static_timer = 0
        self.static_cd = 0
        self.static_tick = 0
        # ═══ TIER III: timer item mythic ═══
        # Razor Carapace (Thornmail - pantulkan damage)
        self.thorn_timer = 0
        self.thorn_cd = 0
        # Everfrost Guard (Arctic Blast)
        self.arctic_cd = 0
        self.arctic_aura_tick = 0
        # Sundering Cudgel (Piercing Bash internal cooldown)
        self.pierce_bash_cd = 0
        # Gale Pike (Gale Leap)
        self.gale_timer = 0       # buff AS aktif
        self.gale_cd = 0
        # Basilisk Breath (Polycephaly tidak punya CD; Miasma
        # disimpan per-target lewat _MiasmaTracker)
        # Solar Brand (aura Scorched Earth - diterapkan via
        # update_auras supaya menara & boss juga bisa kena)
        self.scorch_tick = 0
        # Runic Gavel (Empower Strike charge)
        self.empower_charge = ITEM_CATALOG["runic_gavel"]["passive"][
            "charge_time"]
        # Searbrand (Brand Burst)
        self.searbrand_cd = 0

    # ── Manajemen slot ────────────────────────────────────
    def count(self, item_id):
        return sum(1 for s in self.slots if s == item_id)

    def has(self, item_id):
        return item_id in self.slots

    def used_slots(self):
        """Jumlah slot yang terisi (0..MAX_ITEM_SLOTS)."""
        return sum(1 for s in self.slots if s is not None)

    def add(self, item_id):
        """Tambah item ke slot kosong. Return True jika berhasil."""
        data = ITEM_CATALOG.get(item_id)
        if not data:
            return False
        # Melee-only check
        if data.get("melee_only"):
            rng = getattr(self.hero, "range", 100)
            if rng and rng > 80:
                return False
        for i in range(MAX_ITEM_SLOTS):
            if self.slots[i] is None:
                self.slots[i] = item_id
                self._on_item_changed()
                return True
        return False

    def remove(self, slot_index):
        """Lepas item di slot (drop - TIDAK refund gold)."""
        if 0 <= slot_index < MAX_ITEM_SLOTS:
            old = self.slots[slot_index]
            if old is not None:
                self.slots[slot_index] = None
                self._on_item_changed()
                return old
        return None

    def _on_item_changed(self):
        # Terapkan ulang max HP dengan item. HP hero langsung
        # ditambah sebesar bonus HP baru supaya terasa.
        h = self.hero
        new_max = self.get_max_hp()
        old_max = getattr(h, "max_hp", new_max)
        h.max_hp = new_max
        if new_max > old_max:
            h.hp = min(new_max, h.hp + (new_max - old_max))
        elif h.hp > new_max:
            h.hp = new_max
        # ═══ HEAL AMP (Abyss Breaker) pada pemilik ═══
        amp = self.get_heal_amp()
        try:
            if amp > 0:
                h.apply_heal_amp(amp, 999999)
        except Exception:
            pass

    def clear_on_death(self):
        """Dipanggil saat hero mati - Holy Rapier hilang permanen."""
        dropped_rapier = False
        for i in range(MAX_ITEM_SLOTS):
            if self.slots[i] == "holy_rapier":
                self.slots[i] = None
                dropped_rapier = True
        # Reset timer aktif
        self.blood_frenzy_timer = 0
        # Reset timer Tier II (kebal / rend / static / guard) supaya
        # tidak terbawa ke kehidupan berikutnya.
        self.guard_timer = 0
        self.guard_cd = 0
        self.veil_timer = 0
        self.veil_cd = 0
        self.rend_timer = 0
        self.rend_cd = 0
        self.rend_target = None
        self.static_timer = 0
        self.static_cd = 0
        # Tier III
        self.thorn_timer = 0
        self.thorn_cd = 0
        self.arctic_cd = 0
        self.gale_timer = 0
        self.gale_cd = 0
        self.pierce_bash_cd = 0
        self.searbrand_cd = 0
        if self.has("runic_gavel"):
            self.empower_charge = ITEM_CATALOG["runic_gavel"][
                "passive"]["charge_time"]
        return dropped_rapier

    # ── Agregasi stat ─────────────────────────────────────
    def _sum_stat(self, key):
        total = 0
        for sid in self.slots:
            if sid is None:
                continue
            total += ITEM_CATALOG[sid].get("stats", {}).get(key, 0) or 0
        return total

    def get_bonus_damage(self):
        return self._sum_stat("damage")

    def get_bonus_hp(self):
        """Bonus HP flat dari item (tidak termasuk persentase)."""
        return self._sum_stat("hp")

    def get_hp_pct(self):
        """Total bonus HP persentase dari item (mis. Leviathan Heart)."""
        return self._sum_stat("hp_pct")

    def get_armor(self):
        return (self._sum_stat("armor")
                + getattr(self, "aura_armor", 0)
                - getattr(self, "aura_armor_reduction", 0))

    def get_hp_regen(self):
        return self._sum_stat("hp_regen")

    def get_max_hp(self):
        """Max HP = (base setelah level + bonus flat) * (1 + hp_pct).

        Bonus persentase (Leviathan Heart 35%) ikut membesar saat
        hero naik level, sesuai desain item pertahanan berskala.
        """
        base = int(getattr(self.hero, "base_hp", 0)
                   * _hero_level_mult(self.hero))
        flat = self.get_bonus_hp()
        pct = self.get_hp_pct()
        return int((base + flat) * (1.0 + pct))

    def get_attack_speed_mult(self):
        """Pengali attack speed (1.0 = normal).

        Dota: 1 attack speed = +1% lebih cepat. Kita cap 2.0
        (setara +100 AS) supaya attack_cooldown tidak jadi 1.
        """
        as_total = (self._sum_stat("attack_speed")
                    + getattr(self, "aura_as", 0)
                    + self.get_gale_as_bonus())
        mult = 1.0 + as_total / 100.0
        return max(0.2, min(2.5, mult))

    def get_lifesteal_pct(self):
        ls = self._sum_stat("lifesteal")
        if self.blood_frenzy_timer > 0:
            ls += 1.50  # Demon Maw active
        return min(1.75, ls)

    def get_crit(self):
        """Return (chance, mult) agregat. Cuma Dead Edge yang
        punya crit, tapi digabung jaga-jaga."""
        chance = 0.0
        mult = 2.0
        for sid in self.slots:
            if sid is None:
                continue
            s = ITEM_CATALOG[sid].get("stats", {})
            if "crit_chance" in s:
                chance = max(chance, s["crit_chance"])
                mult = max(mult, s.get("crit_mult", 2.25))
        return chance, mult

    def get_cleave(self):
        """Return (pct, radius) kalau ada Cleave Axe, else None."""
        for sid in self.slots:
            if sid is None:
                continue
            p = ITEM_CATALOG[sid].get("passive")
            if p and p.get("name") == "Cleave":
                return p["cleave_pct"], p["cleave_radius"]
        return None

    def get_cooldown_reduction(self):
        return min(0.5, self._sum_stat("cooldown_reduction"))

    def get_spell_vamp(self):
        return self._sum_stat("spell_vamp")

    # ── Getter stat Tier II ──────────────────────────────
    def get_evasion(self):
        """Peluang menghindari serangan fisik (cap 50%)."""
        return min(0.5, self._sum_stat("evasion"))

    def get_move_speed_pct(self):
        """Bonus persen movement speed (cap 40%)."""
        return min(0.40, self._sum_stat("move_speed_pct"))

    def get_heal_amp(self):
        """Pengali heal yang diterima (+16% Abyss Breaker)."""
        return min(0.5, self._sum_stat("heal_amp"))

    def get_slow_resist(self):
        """Pengurang besar slow yang diterima (cap 60%)."""
        return min(0.6, self._sum_stat("slow_resist"))

    # ── Getter stat Tier III ──
    def get_range_bonus(self):
        """Bonus jangkauan serang (hanya berlaku untuk hero ranged)."""
        rng = getattr(self.hero, "range", 100) or 100
        if rng <= 80:
            return 0
        return self._sum_stat("range_bonus")

    def has_true_strike(self):
        """True kalau pemilik punya Sundering Cudgel (tidak miss)."""
        return self.has("sundering_cudgel")

    def get_reflect_pct(self):
        """Persen pantulan damage saat Thornmail aktif."""
        if self.thorn_timer > 0 and self.has("razor_carapace"):
            return ITEM_CATALOG["razor_carapace"]["active"][
                "reflect_pct"]
        return 0.0

    def get_gale_as_bonus(self):
        """Bonus attack speed sementara dari Gale Leap."""
        if self.gale_timer > 0 and self.has("gale_pike"):
            return ITEM_CATALOG["gale_pike"]["active"]["as_bonus"]
        return 0

    def consume_empower_strike(self):
        """Kembalikan bonus magic damage Runic Gavel & reset charge."""
        if self.has("runic_gavel") and self.empower_charge <= 0:
            dmg = ITEM_CATALOG["runic_gavel"]["passive"]["damage"]
            self.empower_charge = ITEM_CATALOG["runic_gavel"]["passive"][
                "charge_time"]
            return dmg
        return 0

    def get_block(self):
        """Return (chance, amount) damage block pasif, atau None.

        Amount bergantung melee/ranged pemilik. Kalau ada beberapa
        sumber block, ambil peluang & angka tertinggi.
        """
        h = self.hero
        rng = getattr(h, "range", 100) or 100
        is_melee = rng <= 80
        best = None
        for sid in self.slots:
            if sid is None:
                continue
            b = ITEM_CATALOG[sid].get("block")
            if not b:
                continue
            amt = b["melee_block"] if is_melee else b["ranged_block"]
            if best is None or b["chance"] > best[0] or amt > best[1]:
                best = (b["chance"], amt)
        return best

    def get_armor_shred(self):
        """Return (amount, duration) pengikis armor pasif (Corroder)."""
        for sid in self.slots:
            if sid is None:
                continue
            p = ITEM_CATALOG[sid].get("passive")
            if p and p.get("armor_shred"):
                return p["armor_shred"], p.get("duration", 300)
        return None

    def get_on_attack_chain(self):
        """Return dict pasif sambaran listrik (Fenrir/Thunder)."""
        for sid in self.slots:
            if sid is None:
                continue
            c = ITEM_CATALOG[sid].get("on_attack")
            if c:
                return c
        return None

    def get_bash(self):
        """Return dict bash pasif (Abyss Breaker) atau None."""
        for sid in self.slots:
            if sid is None:
                continue
            b = ITEM_CATALOG[sid].get("bash")
            if b:
                return b
        return None

    def is_veiled(self):
        """True saat Tempest Veil aktif (kebal semua damage)."""
        return self.veil_timer > 0

    def is_guarding(self):
        return self.guard_timer > 0

    def get_rend_crit(self):
        """Pengali crit pasti selama Soul Rend aktif, else None."""
        if self.rend_timer > 0 and self.has("sanguine_thorn"):
            return ITEM_CATALOG["sanguine_thorn"]["active"]["crit_mult"]
        return None

    # ── Update per-frame ─────────────────────────────────
    def update(self, dt=1, enemies=None):
        # Timer aktif
        if self.blood_frenzy_timer > 0:
            self.blood_frenzy_timer -= dt
        if self.blood_frenzy_cd > 0:
            self.blood_frenzy_cd -= dt
        if self.last_damage_timer > 0:
            self.last_damage_timer -= dt

        # Timer Tier II
        for attr in ("guard_timer", "guard_cd", "veil_timer", "veil_cd",
                     "chains_cd", "rend_timer", "rend_cd", "bash_cd",
                     "overwhelm_cd", "static_timer", "static_cd",
                     "static_tick",
                     # Tier III
                     "thorn_timer", "thorn_cd", "arctic_cd",
                     "gale_timer", "gale_cd", "pierce_bash_cd",
                     "searbrand_cd"):
            if getattr(self, attr, 0) > 0:
                setattr(self, attr, getattr(self, attr) - dt)
        if self.rend_timer <= 0:
            self.rend_target = None

        # Runic Gavel charge (terisi otomatis seiring waktu)
        if self.has("runic_gavel") and self.empower_charge > 0:
            self.empower_charge = max(0, self.empower_charge - dt)

        # Tick racun Miasma (Basilisk Breath)
        _tick_miasma(dt)

        h = self.hero

        # Auto-trigger Blood Frenzy saat HP kritis
        if self.has("demon_maw") and self.blood_frenzy_cd <= 0:
            if h.alive and h.max_hp > 0 and h.hp / h.max_hp < 0.35:
                act = ITEM_CATALOG["demon_maw"]["active"]
                self.blood_frenzy_timer = act["duration"]
                self.blood_frenzy_cd = act["cooldown"]

        # ═══ TIER II AUTO-TRIGGERS ═══
        if h.alive and h.max_hp > 0:
            ratio = h.hp / h.max_hp
            # Scarlet Bulwark - Bulwark Guard saat HP kritis
            if self.has("scarlet_bulwark") and self.guard_cd <= 0:
                act = ITEM_CATALOG["scarlet_bulwark"]["active"]
                if ratio < act["hp_threshold"]:
                    self.guard_timer = act["duration"]
                    self.guard_cd = act["cooldown"]
                    _fx_notify(h, "BULWARK GUARD!",
                               ITEM_CATALOG["scarlet_bulwark"]["glow"])
            # Tempest Vane - Veil kebal saat HP kritis
            if self.has("tempest_vane") and self.veil_cd <= 0:
                act = ITEM_CATALOG["tempest_vane"]["active"]
                if ratio < act["hp_threshold"]:
                    self.veil_timer = act["duration"]
                    self.veil_cd = act["cooldown"]
                    _fx_notify(h, "TEMPEST VEIL!",
                               ITEM_CATALOG["tempest_vane"]["glow"])
            # Fenrir Chain - Binding Chains saat >=2 musuh dekat
            if self.has("fenrir_chain") and self.chains_cd <= 0 \
                    and enemies:
                act = ITEM_CATALOG["fenrir_chain"]["active"]
                near = [e for e in enemies
                        if getattr(e, "alive", False)
                        and math.hypot(e.x - h.x, e.y - h.y)
                        <= act["trigger_radius"]]
                if len(near) >= act["trigger_enemies"]:
                    self.chains_cd = act["cooldown"]
                    for e in near:
                        if math.hypot(e.x - h.x, e.y - h.y) \
                                <= act["root_radius"]:
                            _apply_stun_to(e, act["root_duration"])
                        try:
                            e.take_damage(act["damage"], h.team,
                                          "magic")
                        except TypeError:
                            e.take_damage(act["damage"], h.team)
                    _fx_notify(h, "BINDING CHAINS!",
                               ITEM_CATALOG["fenrir_chain"]["glow"])
                    _fx_chain(h, near,
                              ITEM_CATALOG["fenrir_chain"]["color"])
            # Sanguine Thorn - Soul Rend saat menyerang target hidup
            if self.has("sanguine_thorn") and self.rend_cd <= 0:
                tgt = getattr(h, "target", None)
                if tgt is not None and getattr(tgt, "alive", False) \
                        and getattr(tgt, "team", None) != h.team:
                    act = ITEM_CATALOG["sanguine_thorn"]["active"]
                    self.rend_timer = act["duration"]
                    self.rend_cd = act["cooldown"]
                    self.rend_target = tgt
                    _apply_silence_to(tgt, act["duration"])
                    _apply_amp_to(tgt, act["damage_amp"],
                                  act["duration"])
                    _fx_notify(tgt, "SOUL REND!",
                               ITEM_CATALOG["sanguine_thorn"]["glow"])
            # Abyss Breaker - Overwhelm stun saat menyerang
            if self.has("abyss_breaker") and self.overwhelm_cd <= 0:
                tgt = getattr(h, "target", None)
                if tgt is not None and getattr(tgt, "alive", False) \
                        and getattr(tgt, "team", None) != h.team:
                    act = ITEM_CATALOG["abyss_breaker"]["active"]
                    self.overwhelm_cd = act["cooldown"]
                    _apply_stun_to(tgt, act["stun"])
                    _fx_notify(tgt, "OVERWHELM!",
                               ITEM_CATALOG["abyss_breaker"]["glow"])
            # Thunder Coil - Static Charge zap berkala
            if self.static_timer > 0 and self.has("thunder_coil") \
                    and enemies:
                act = ITEM_CATALOG["thunder_coil"]["active"]
                self.static_tick -= dt
                if self.static_tick <= 0:
                    self.static_tick = act["tick"]
                    near = sorted(
                        [e for e in enemies
                         if getattr(e, "alive", False)
                         and math.hypot(e.x - h.x, e.y - h.y)
                         <= act["radius"]],
                        key=lambda e: math.hypot(e.x - h.x,
                                                 e.y - h.y))
                    for e in near[:act["targets"]]:
                        try:
                            e.take_damage(act["damage"], h.team,
                                          "magic")
                        except TypeError:
                            e.take_damage(act["damage"], h.team)
                    if near:
                        _fx_chain(h, near[:act["targets"]],
                                  ITEM_CATALOG["thunder_coil"]["color"])

            # ═══ TIER III AUTO-TRIGGERS ═══
            # Razor Carapace - Thornmail saat HP kritis
            if self.has("razor_carapace") and self.thorn_cd <= 0:
                act = ITEM_CATALOG["razor_carapace"]["active"]
                if ratio < act["hp_threshold"]:
                    self.thorn_timer = act["duration"]
                    self.thorn_cd = act["cooldown"]
                    _fx_notify(h, "THORNMAIL!",
                               ITEM_CATALOG["razor_carapace"]["glow"])
            # Everfrost Guard - Arctic Blast saat >=2 musuh dekat
            if self.has("everfrost_guard") and self.arctic_cd <= 0 \
                    and enemies:
                act = ITEM_CATALOG["everfrost_guard"]["active"]
                near = [e for e in enemies
                        if getattr(e, "alive", False)
                        and math.hypot(e.x - h.x, e.y - h.y)
                        <= act["radius"]]
                if len(near) >= act["trigger_enemies"]:
                    self.arctic_cd = act["cooldown"]
                    for e in near:
                        try:
                            e.take_damage(act["damage"], h.team,
                                          "magic")
                        except TypeError:
                            e.take_damage(act["damage"], h.team)
                        if hasattr(e, "apply_slow"):
                            e.apply_slow(act["slow"],
                                         act["slow_duration"])
                    _fx_notify(h, "ARCTIC BLAST!",
                               ITEM_CATALOG["everfrost_guard"]["glow"])
                    _fx_chain(h, near,
                              ITEM_CATALOG["everfrost_guard"]["color"])
            # Gale Pike - Gale Leap saat HP kritis (mundur)
            if self.has("gale_pike") and self.gale_cd <= 0:
                act = ITEM_CATALOG["gale_pike"]["active"]
                if ratio < act["hp_threshold"]:
                    self.gale_timer = act["duration"]
                    self.gale_cd = act["cooldown"]
                    tgt = getattr(h, "target", None)
                    if tgt is not None and getattr(tgt, "alive",
                                                   False):
                        dx = h.x - tgt.x
                        dy = h.y - tgt.y
                        d = math.hypot(dx, dy) or 1.0
                        h.x += dx / d * act["dash_distance"]
                        h.y += dy / d * act["dash_distance"]
                    else:
                        # Tidak ada target: dorong ke belakang
                        # sesuai arah hadap.
                        h.x -= h.facing * act["dash_distance"]
                    _fx_notify(h, "GALE LEAP!",
                               ITEM_CATALOG["gale_pike"]["glow"])
            # Searbrand - Brand Burst saat >=2 musuh dekat
            if self.has("searbrand") and self.searbrand_cd <= 0 \
                    and enemies:
                act = ITEM_CATALOG["searbrand"]["active"]
                near = [e for e in enemies
                        if getattr(e, "alive", False)
                        and math.hypot(e.x - h.x, e.y - h.y)
                        <= act["radius"]]
                if len(near) >= act["trigger_enemies"]:
                    self.searbrand_cd = act["cooldown"]
                    for e in near:
                        try:
                            e.take_damage(act["damage"], h.team,
                                          "magic")
                        except TypeError:
                            e.take_damage(act["damage"], h.team)
                        try:
                            e.apply_debuff("burn",
                                           act["burn_dps"],
                                           act["burn_duration"],
                                           source_team=h.team)
                        except Exception:
                            pass
                    _fx_notify(h, "BRAND BURST!",
                               ITEM_CATALOG["searbrand"]["glow"])
                    _fx_chain(h, near,
                              ITEM_CATALOG["searbrand"]["color"])

        # HP regen (base item regen + Leviathan out-of-combat +
        # Octarine small regen sudah termasuk angka stat).
        if h.alive and h.max_hp > 0 and h.hp < h.max_hp:
            regen = self.get_hp_regen()
            # Leviathan Heart pasif
            if self.has("leviathan_heart"):
                p = ITEM_CATALOG["leviathan_heart"]["passive"]
                if self.last_damage_timer <= 0:
                    regen += h.max_hp * p["out_of_combat_regen_pct"] / 60.0
            if regen > 0:
                h.hp = min(h.max_hp, h.hp + regen)

    def notify_damage_taken(self, rng=None, damage=0, source=None):
        """Dipanggil dari Hero.take_damage untuk reset timer combat,
        peluang Static Charge (Thunder Coil) DAN pantulan Thornmail
        (Razor Carapace). ``damage`` adalah damage SETELAH armor/block
        yang benar-benar mengurangi HP pemilik.
        """
        if self.has("leviathan_heart"):
            p = ITEM_CATALOG["leviathan_heart"]["passive"]
            self.last_damage_timer = p["combat_timeout"]

        if self.has("thunder_coil") and self.static_cd <= 0:
            act = ITEM_CATALOG["thunder_coil"]["active"]
            r = rng.random() if rng is not None else random.random()
            if r < act["proc_chance"]:
                self.static_timer = act["duration"]
                self.static_tick = act["tick"]
                self.static_cd = act["cooldown"]
                _fx_notify(self.hero, "STATIC CHARGE!",
                           ITEM_CATALOG["thunder_coil"]["glow"])

        # ═══ RAZOR CARAPACE: Thornmail reflect ═══
        refl = self.get_reflect_pct()
        if (refl > 0 and damage > 0 and source is not None
                and getattr(source, "alive", False)
                and getattr(source, "team", self.hero.team)
                != self.hero.team):
            dmg = int(damage * refl)
            if dmg > 0:
                try:
                    source.take_damage(dmg, self.hero.team, "magic")
                except TypeError:
                    source.take_damage(dmg, self.hero.team)
                _fx_notify(source, f"-{dmg}",
                           ITEM_CATALOG["razor_carapace"]["glow"])

    # ── Helper on-hit (crit/lifesteal/cleave) ─────────────
    def roll_crit(self, rng=None):
        chance, mult = self.get_crit()
        if chance <= 0:
            return False, 1.0
        r = rng.random() if rng is not None else random.random()
        if r < chance:
            return True, mult
        return False, 1.0

    def on_basic_attack_hit(self, target, damage, all_units=None):
        """Dipanggil setelah basic attack kena.

        - Lifesteal (semua damage, melee/ranged).
        - Cleave (melee only - kalau hero range tidak punya
          Cleave Axe karena aturan melee_only).
        """
        h = self.hero
        if not h.alive:
            return
        ls = self.get_lifesteal_pct()
        if ls > 0 and damage > 0:
            h.hp = min(h.max_hp, h.hp + damage * ls)

        # ═══ TIER II ON-HIT (juga dipakai ranged via
        # on_ranged_attack_hit) ═══
        self._on_hit_common(target, damage, all_units)

        # Cleave
        cleave = self.get_cleave()
        if cleave and all_units is not None and damage > 0:
            pct, radius = cleave
            splash = int(damage * pct)
            if splash > 0:
                for u in all_units:
                    if u is target or not getattr(u, "alive", False):
                        continue
                    if u.team == h.team:
                        continue
                    d = math.hypot(u.x - target.x, u.y - target.y)
                    if d <= radius:
                        try:
                            u.take_damage(splash, h.team)
                        except Exception:
                            pass

    def _on_hit_common(self, target, damage, all_units=None):
        """Efek on-hit Tier II yang berlaku untuk melee & ranged:
        Corrosion (shred armor), Bash (stun), Arc chain (petir)."""
        h = self.hero

        # ── Corroder: kikis armor target ──
        shred = self.get_armor_shred()
        if shred and target is not None:
            _apply_shred_to(target, shred[0], shred[1])

        # ── Sanguine Thorn: serangan ke target Soul Rend selalu
        #    crit 150% (ditangani _do_attack untuk angka damage;
        #    di sini tidak menambah apa-apa). ──

        # ── Abyss Breaker: Bash ──
        bash = self.get_bash()
        if bash and self.bash_cd <= 0 and target is not None \
                and getattr(target, "alive", False):
            if random.random() < bash["chance"]:
                self.bash_cd = bash["cooldown"]
                _apply_stun_to(target, bash["stun"])
                try:
                    target.take_damage(bash["damage"], h.team)
                except Exception:
                    pass
                _fx_notify(target, "BASH!",
                           ITEM_CATALOG["abyss_breaker"]["glow"])

        # ── Fenrir Chain / Thunder Coil: sambaran berantai ──
        chain = self.get_on_attack_chain()
        if chain and all_units is not None and target is not None \
                and random.random() < chain["chance"]:
            hit = [target] if getattr(target, "alive", False) else []
            for u in all_units:
                if u is target or not getattr(u, "alive", False):
                    continue
                if getattr(u, "team", None) == h.team:
                    continue
                if math.hypot(u.x - target.x, u.y - target.y) \
                        <= chain["radius"]:
                    hit.append(u)
                if len(hit) >= chain["targets"]:
                    break
            for u in hit:
                try:
                    u.take_damage(chain["damage"], h.team, "magic")
                except TypeError:
                    u.take_damage(chain["damage"], h.team)
                except Exception:
                    pass
            if hit:
                _fx_chain(h, hit, ITEM_CATALOG[
                    "thunder_coil" if self.has("thunder_coil")
                    else "fenrir_chain"]["color"])

        # ═══ TIER III ON-HIT ═══
        if target is None or not getattr(target, "alive", False):
            return

        # ── Sundering Cudgel: Piercing Bash (mini stun) ──
        if self.has("sundering_cudgel") and self.pierce_bash_cd <= 0:
            b = ITEM_CATALOG["sundering_cudgel"]["bash"]
            if random.random() < b["chance"]:
                self.pierce_bash_cd = b["cooldown"]
                _apply_stun_to(target, b["stun"])
                try:
                    target.take_damage(b["damage"], h.team, "magic")
                except TypeError:
                    target.take_damage(b["damage"], h.team)
                _fx_notify(target, "PIERCE!",
                           ITEM_CATALOG["sundering_cudgel"]["glow"])

        # ── Frostbound Eye: Frostbite (slow + anti-heal) ──
        if self.has("frostbound_eye"):
            oa = ITEM_CATALOG["frostbound_eye"]["on_attack"]
            if hasattr(target, "apply_slow"):
                target.apply_slow(oa["slow"], oa["duration"])
            try:
                target.apply_debuff("atk_slow", oa["atk_slow"],
                                    oa["duration"])
                target.apply_debuff("anti_heal", oa["anti_heal"],
                                    oa["duration"])
            except Exception:
                pass

        # ── Basilisk Breath: Miasma (racun % Max HP) ──
        if self.has("basilisk_breath"):
            _apply_miasma(target, h,
                          ITEM_CATALOG["basilisk_breath"]["on_attack"])
            # Polycephaly: tembakan ekstra ke musuh terdekat
            ms = ITEM_CATALOG["basilisk_breath"]["multishot"]
            is_ranged = (getattr(h, "range", 100) or 100) > 80
            if is_ranged and all_units is not None \
                    and random.random() < ms["chance"]:
                extras = []
                for u in all_units:
                    if u is target or not getattr(u, "alive",
                                                  False):
                        continue
                    if getattr(u, "team", None) == h.team:
                        continue
                    d = math.hypot(u.x - target.x, u.y - target.y)
                    if d <= ms["radius"]:
                        extras.append((d, u))
                extras.sort(key=lambda x: x[0])
                for _, u in extras[:ms["targets"]]:
                    dmg = int(damage * ms["damage_pct"])
                    try:
                        u.take_damage(dmg, h.team, "magic")
                    except TypeError:
                        u.take_damage(dmg, h.team)
                    _apply_miasma(u, h, ITEM_CATALOG[
                        "basilisk_breath"]["on_attack"])
                if extras:
                    _fx_chain(h, [u for _, u in
                                  extras[:ms["targets"]]],
                              ITEM_CATALOG["basilisk_breath"]["color"])

        # ── Runic Gavel: Empower Strike (bonus magic damage) ──
        if self.has("runic_gavel") and self.empower_charge <= 0:
            bonus = self.consume_empower_strike()
            if bonus > 0:
                try:
                    target.take_damage(bonus, h.team, "magic")
                except TypeError:
                    target.take_damage(bonus, h.team)
                _fx_notify(target, "EMPOWER!",
                           ITEM_CATALOG["runic_gavel"]["glow"])

    def on_ranged_attack_hit(self, target, damage, all_units=None):
        """On-hit Tier II untuk hero ranged (tanpa lifesteal/cleave -
        keduanya sudah ditangani saat proyektil dilepas)."""
        h = self.hero
        if not h.alive:
            return
        self._on_hit_common(target, damage, all_units)


# ════════════════════════════════════════════════════════════
# Helper status ke target (stun/silence/shred/amp) - aman untuk
# Hero, Minion, maupun Boss (semuanya pakai TowerDebuffMixin).
# ════════════════════════════════════════════════════════════
def _apply_stun_to(target, duration):
    fn = getattr(target, "apply_stun", None)
    if fn is not None:
        fn(duration)
    else:
        # Unit tanpa mixin: fallback ke slow total
        try:
            target.apply_slow(1.0, duration)
        except Exception:
            pass


def _apply_silence_to(target, duration):
    try:
        target.apply_debuff("atk_slow", 1.0, duration)
        target.apply_debuff("skill_down", 1.0, duration)
    except Exception:
        pass


def _apply_shred_to(target, amount, duration):
    fn = getattr(target, "apply_armor_shred", None)
    if fn is not None:
        fn(amount, duration)


def _apply_amp_to(target, amount, duration):
    fn = getattr(target, "apply_damage_amp", None)
    if fn is not None:
        fn(amount, duration)


def _fx_notify(unit, text, color=(255, 255, 255)):
    """Floating text + notifikasi kecil (pakai damage_type magic
    untuk warna ungu/biru yang kontras)."""
    try:
        import __main__
        g = getattr(__main__, "game_instance", None)
        if g is None:
            return
        g.effects.add_damage_number(
            unit.x, unit.y - getattr(unit, "radius", 16) - 14,
            text, is_critical=False, damage_type="magic")
    except Exception:
        pass


def _fx_chain(source, targets, color):
    """Efek petir sederhana: partikel di tiap target + garis kilat
    via hit particles berwarna tim."""
    try:
        import __main__
        g = getattr(__main__, "game_instance", None)
        if g is None:
            return
        for t in targets:
            g.effects.add_hit_particles(t.x, t.y, team="blue", count=6)
        g.effects.add_damage_number(
            source.x, source.y - getattr(source, "radius", 16) - 26,
            "ZAP!", is_critical=False, damage_type="magic")
    except Exception:
        pass


# ════════════════════════════════════════════════════════════
# Helper level multiplier (sama dengan HERO_LEVELS logic)
# ════════════════════════════════════════════════════════════
def _hero_level_mult(hero):
    try:
        from _core import HERO_LEVELS
        lvl = getattr(hero, "level", 1)
        return HERO_LEVELS[lvl]["hp_mult"]
    except Exception:
        return 1.0


# ════════════════════════════════════════════════════════════
# AURA UPDATE (dipanggil sekali per frame dari Game.update)
# ════════════════════════════════════════════════════════════
def update_auras(all_heroes):
    # Reset aura di tiap hero
    for h in all_heroes:
        inv = getattr(h, "items", None)
        if inv is not None:
            inv.aura_armor = 0
            inv.aura_as = 0
            inv.aura_armor_reduction = 0
            inv.aura_guard_block = 0

    # Kumpulkan SEMUA unit hidup (minion + hero + boss) supaya aura
    # milik item Tier III bisa mengenai lebih dari sekadar hero.
    all_units = _collect_all_units(all_heroes)

    # ═══ SCARLET BULWARK: aura Bulwark Guard ═══
    # (dihitung DULUAN - tidak tergantung aura Steel Aegis)
    guards = [h for h in all_heroes
              if getattr(h, "alive", False)
              and getattr(h, "items", None) is not None
              and h.items.has("scarlet_bulwark")
              and h.items.guard_timer > 0]
    if guards:
        act = ITEM_CATALOG["scarlet_bulwark"]["active"]
        g_r = act["ally_radius"]
        for h in all_heroes:
            if not getattr(h, "alive", False):
                continue
            inv = getattr(h, "items", None)
            if inv is None:
                continue
            for src in guards:
                if src.team != h.team:
                    continue
                d = math.hypot(h.x - src.x, h.y - src.y)
                if d <= g_r:
                    blk = act["base_block"] + int(
                        getattr(src, "max_hp", 0)
                        * act["max_hp_block_pct"])
                    if blk > inv.aura_guard_block:
                        inv.aura_guard_block = blk

    # ═══ EVERFROST GUARD: Freezing Aura (musuh: atk slow + heal
    #     reduction), SOLAR BRAND: Scorched Earth (bakar + blind),
    #     SEARBRAND: Cauterize (anti-heal 50% + bakar ringan).
    #     Aura ini mengenai SEMUA unit musuh (minion/hero/boss),
    #     bukan hanya hero, jadi ditaruh di loop terpisah. ═══
    frost_sources = [h for h in all_heroes
                     if getattr(h, "alive", False)
                     and getattr(h, "items", None) is not None
                     and h.items.has("everfrost_guard")]
    solar_sources = [h for h in all_heroes
                     if getattr(h, "alive", False)
                     and getattr(h, "items", None) is not None
                     and h.items.has("solar_brand")]
    sear_sources = [h for h in all_heroes
                    if getattr(h, "alive", False)
                    and getattr(h, "items", None) is not None
                    and h.items.has("searbrand")]
    if frost_sources or solar_sources or sear_sources:
        f_r = ITEM_CATALOG["everfrost_guard"]["aura"]["enemy_radius"]
        f_as = ITEM_CATALOG["everfrost_guard"]["aura"][
            "enemy_atk_slow"]
        f_heal = ITEM_CATALOG["everfrost_guard"]["aura"][
            "enemy_anti_heal"]
        s_r = ITEM_CATALOG["solar_brand"]["aura"]["enemy_radius"]
        s_burn = ITEM_CATALOG["solar_brand"]["aura"]["burn_dps"]
        s_blind = ITEM_CATALOG["solar_brand"]["aura"]["blind"]
        se_r = ITEM_CATALOG["searbrand"]["aura"]["enemy_radius"]
        se_heal = ITEM_CATALOG["searbrand"]["aura"]["enemy_anti_heal"]
        se_burn = ITEM_CATALOG["searbrand"]["aura"]["burn_dps"]
        for u in all_units:
            if not getattr(u, "alive", False):
                continue
            u_team = getattr(u, "team", None)
            # Everfrost
            for src in frost_sources:
                if u_team == src.team:
                    continue
                if math.hypot(u.x - src.x, u.y - src.y) <= f_r:
                    try:
                        u.apply_debuff("atk_slow", f_as, 30)
                        u.apply_debuff("anti_heal", f_heal, 30)
                    except Exception:
                        pass
                    break
            # Solar Brand - burn tick (28 dps, refresh 30 frame)
            for src in solar_sources:
                if u_team == src.team:
                    continue
                if math.hypot(u.x - src.x, u.y - src.y) <= s_r:
                    try:
                        u.apply_debuff("burn", s_burn, 30,
                                       source_team=src.team)
                    except Exception:
                        pass
                    # Blind: tandai lewat atk_slow kecil yang
                    # dipakai bersama; dipisah atribut kalau ada.
                    if hasattr(u, "apply_miss_chance"):
                        try:
                            u.apply_miss_chance(s_blind, 30)
                        except Exception:
                            pass
                    break
            # Searbrand - Cauterize (anti-heal 50% + bakar ringan)
            for src in sear_sources:
                if u_team == src.team:
                    continue
                if math.hypot(u.x - src.x, u.y - src.y) <= se_r:
                    try:
                        u.apply_debuff("anti_heal", se_heal, 30)
                        u.apply_debuff("burn", se_burn, 30,
                                       source_team=src.team)
                    except Exception:
                        pass
                    break

    # Cari semua pemegang Steel Aegis
    sources = [h for h in all_heroes
               if getattr(h, "alive", False)
               and getattr(h, "items", None) is not None
               and h.items.has("steel_aegis")]
    if not sources:
        return

    data = ITEM_CATALOG["steel_aegis"]["aura"]
    ally_r = data["ally_radius"]
    enemy_r = data["enemy_radius"]
    a_armor = data["ally_armor"]
    a_as = data["ally_attack_speed"]
    e_red = data["enemy_armor_reduction"]

    for h in all_heroes:
        if not getattr(h, "alive", False):
            continue
        inv = getattr(h, "items", None)
        if inv is None:
            continue
        for src in sources:
            if src is h:
                # Pemegang aura TIDAK dapat aura sekutu dari
                # dirinya sendiri - stat base-nya sudah mencakup
                # efek itu.
                continue
            d = math.hypot(h.x - src.x, h.y - src.y)
            if h.team == src.team:
                if d <= ally_r:
                    inv.aura_armor += a_armor
                    inv.aura_as += a_as
            else:
                if d <= enemy_r:
                    inv.aura_armor_reduction += e_red


def _collect_all_units(all_heroes):
    """Kumpulkan semua unit hidup (hero + minion + boss) untuk
    perhitungan aura Tier III. Aman dipanggil tanpa konteks game.
    """
    units = list(all_heroes)
    try:
        import __main__
        g = getattr(__main__, "game_instance", None)
        if g is not None:
            for m in getattr(g, "minions", []) or []:
                if m is not None:
                    units.append(m)
            boss = getattr(g, "active_boss", None)
            if boss is not None and getattr(boss, "alive", False):
                units.append(boss)
    except Exception:
        pass
    return units


# ════════════════════════════════════════════════════════════
# AI HELPER: saran item untuk hero
# ════════════════════════════════════════════════════════════
def suggest_item_for_hero(hero, owned):
    """Pilih item terbaik berikutnya untuk hero AI.

    owned = set item_id yang sudah dimiliki hero.
    Return item_id atau None.
    """
    if hero is None:
        return None
    rng = getattr(hero, "range", 100) or 100
    is_melee = rng <= 80

    # Priority berdasarkan peran
    role = (getattr(hero, "role", "") or "").lower()

    # Urut prioritas: tank/figther, marksman, mage
    pool = []

    # Tier II ikut masuk pool sesuai peran, supaya AI juga membeli
    # item legendary baru (Scarlet Bulwark, Monarch Wings, dst.).
    if "tank" in role or "bruiser" in role or "fighter" in role:
        pool = ["leviathan_heart", "scarlet_bulwark", "searbrand",
                "razor_carapace", "everfrost_guard", "steel_aegis",
                "abyss_breaker", "solar_brand", "demon_maw",
                "corroder", "fenrir_chain", "octarine_core",
                "moon_shard"]
    elif "marksman" in role or "assassin" in role:
        pool = ["dead_edge", "basilisk_breath", "gale_pike",
                "frostbound_eye", "sundering_cudgel", "searbrand",
                "monarch_wings", "thunder_coil", "sanguine_thorn",
                "moon_shard", "runic_gavel", "corroder", "demon_maw",
                "octarine_core", "steel_aegis"]
    elif "mage" in role or "trickster" in role:
        pool = ["octarine_core", "runic_gavel", "searbrand",
                "solar_brand", "frostbound_eye", "everfrost_guard",
                "tempest_vane", "corroder", "moon_shard",
                "thunder_coil", "steel_aegis", "demon_maw",
                "dead_edge"]
    else:
        pool = ["steel_aegis", "searbrand", "sundering_cudgel",
                "frostbound_eye", "razor_carapace", "moon_shard",
                "demon_maw", "leviathan_heart", "scarlet_bulwark",
                "solar_brand", "thunder_coil", "monarch_wings",
                "octarine_core", "gale_pike", "dead_edge", "corroder",
                "everfrost_guard"]

    if is_melee:
        # Masukkan cleave & rapier di urutan belakang
        pool = ["cleave_axe"] + pool + ["holy_rapier"]
    else:
        pool = pool + ["holy_rapier"]

    for sid in pool:
        if sid in owned:
            continue
        data = ITEM_CATALOG[sid]
        if data.get("melee_only") and not is_melee:
            continue
        return sid
    return None


# ════════════════════════════════════════════════════════════
# UI: RENDERER 6 SLOT di HeroPanel
# ════════════════════════════════════════════════════════════
class HeroItemRenderer:
    """Menggambar 6 slot item di HeroPanel (baris tipis di atas
    tombol upgrade). Juga mendeteksi klik kanan untuk drop."""

    SLOT_SIZE = 30
    SLOT_GAP = 4

    @classmethod
    def width(cls):
        return cls.SLOT_SIZE * MAX_ITEM_SLOTS + cls.SLOT_GAP * (MAX_ITEM_SLOTS - 1)

    @classmethod
    def draw(cls, surface, hero, px, py, panel_w):
        """Gambar slot. Rata tengah di dalam panel (px..px+panel_w)."""
        if hero is None or getattr(hero, "items", None) is None:
            return
        inv = hero.items
        total_w = cls.width()
        sx = px + (panel_w - total_w) // 2
        sy = py
        for i in range(MAX_ITEM_SLOTS):
            rect = pygame.Rect(sx + i * (cls.SLOT_SIZE + cls.SLOT_GAP),
                               sy, cls.SLOT_SIZE, cls.SLOT_SIZE)
            # Background
            pygame.draw.rect(surface, (20, 24, 38), rect, border_radius=4)
            border = (80, 90, 120)
            sid = inv.slots[i]
            if sid is not None:
                data = ITEM_CATALOG[sid]
                border = data["color"]
                # Glow kalau item aktif (Tier I & Tier II)
                _active = (
                    (sid == "demon_maw" and inv.blood_frenzy_timer > 0)
                    or (sid == "scarlet_bulwark" and inv.guard_timer > 0)
                    or (sid == "tempest_vane" and inv.veil_timer > 0)
                    or (sid == "thunder_coil" and inv.static_timer > 0)
                    or (sid == "sanguine_thorn" and inv.rend_timer > 0)
                    or (sid == "razor_carapace" and inv.thorn_timer > 0)
                    or (sid == "gale_pike" and inv.gale_timer > 0)
                    or (sid == "searbrand" and inv.searbrand_cd > 0
                        and inv.searbrand_cd
                        > ITEM_CATALOG["searbrand"]["active"]["cooldown"]
                        - 30))
                if _active:
                    g = pygame.Surface(
                        (cls.SLOT_SIZE + 6, cls.SLOT_SIZE + 6),
                        pygame.SRCALPHA)
                    pygame.draw.rect(g, (*data["glow"], 130),
                                     (0, 0, cls.SLOT_SIZE + 6,
                                      cls.SLOT_SIZE + 6),
                                     border_radius=6)
                    surface.blit(g, (rect.x - 3, rect.y - 3))
                # Icon
                icon = get_icon(sid, cls.SLOT_SIZE - 4)
                if icon is not None:
                    surface.blit(icon, (rect.x + 2, rect.y + 2))
                # Cooldown lingkaran kecil untuk blood frenzy
                if sid == "demon_maw" and inv.blood_frenzy_cd > 0:
                    ratio = inv.blood_frenzy_cd / 1500.0
                    if ratio > 0:
                        cd_h = int(cls.SLOT_SIZE * ratio)
                        cd_surf = pygame.Surface(
                            (cls.SLOT_SIZE, cd_h), pygame.SRCALPHA)
                        cd_surf.fill((0, 0, 0, 150))
                        surface.blit(cd_surf,
                                     (rect.x, rect.y + cls.SLOT_SIZE - cd_h))
            pygame.draw.rect(surface, border, rect, 2, border_radius=4)

        # Daftarkan slot untuk drop detection
        try:
            g = _get_game()
            if g is not None:
                for i in range(MAX_ITEM_SLOTS):
                    rect = pygame.Rect(
                        sx + i * (cls.SLOT_SIZE + cls.SLOT_GAP),
                        sy, cls.SLOT_SIZE, cls.SLOT_SIZE)
                    g.ui_buttons[f"hero_item_slot_{i}"] = rect
        except Exception:
            pass

    @classmethod
    def slot_index_at(cls, hero, mx, my, px, py, panel_w):
        """Return index slot yang diklik, atau -1."""
        if hero is None:
            return -1
        total_w = cls.width()
        sx = px + (panel_w - total_w) // 2
        sy = py
        for i in range(MAX_ITEM_SLOTS):
            rect = pygame.Rect(sx + i * (cls.SLOT_SIZE + cls.SLOT_GAP),
                               sy, cls.SLOT_SIZE, cls.SLOT_SIZE)
            if rect.collidepoint(mx, my):
                return i
        return -1


def _get_game():
    try:
        import __main__
        return getattr(__main__, "game_instance", None)
    except Exception:
        return None


def _player_heroes(game):
    """Semua hero pemain yang sudah di-summon, hidup maupun mati."""
    return list(getattr(game, "heroes", []))


def _alive_player_heroes(game):
    """Compatibility helper untuk pemanggil lama yang hanya perlu hero hidup."""
    return [h for h in _player_heroes(game) if getattr(h, "alive", False)]


def pending_forge_items(hero):
    """Antrian item yang dibeli saat ``hero`` mati.

    Antrian melekat pada hero agar item tidak pernah tertukar dengan hero
    lain dan baru dipindahkan ke inventory setelah respawn.
    """
    pending = getattr(hero, "_pending_forge_items", None)
    if pending is None:
        pending = []
        setattr(hero, "_pending_forge_items", pending)
    return pending


def deliver_pending_forge_items(hero):
    """Kirim semua pesanan Forge tertunda ke inventory hero.

    Dipanggil tepat setelah respawn. Return daftar ID item yang berhasil
    dikirim; item yang tidak muat tetap diantrikan sebagai pengaman.
    """
    pending = pending_forge_items(hero)
    delivered = []
    while pending and hero.items.add(pending[0]):
        delivered.append(pending.pop(0))
    return delivered


def _resolve_shop_target(game, heroes=None):
    """Tentukan penerima pembelian, termasuk hero yang sedang mati.

    Prioritas target tersimpan → hero terseleksi → hero hidup pertama →
    hero mati pertama. Membeli untuk hero mati membuat pesanan tertunda
    yang otomatis dikirim ketika ia respawn.
    """
    if heroes is None:
        heroes = _player_heroes(game)
    if not heroes:
        return None
    saved = getattr(game, "itemshop_target_hero", None)
    if saved in heroes:
        return saved
    sel = getattr(game, "selected_hero", None)
    if sel in heroes:
        return sel
    return next((h for h in heroes if getattr(h, "alive", False)), heroes[0])


# ════════════════════════════════════════════════════════════
# UI: ITEM SHOP OVERLAY (bisa dibuka kapan pun - tanpa klik hero)
# ════════════════════════════════════════════════════════════
class ItemShopUI:
    """Overlay toko item.

    Grid item SELALU ditampilkan, walau pemain belum meng-klik hero di
    peta. Hero penerima item dipilih lewat strip "BUY FOR" di bawah
    judul (daftar semua hero yang sudah di-summon & hidup); bila ada
    hero terseleksi di peta, dia otomatis jadi target awal.

    Pemakaian:
        game.item_shop_open = True/False
        game.ui.draw_item_shop(screen)
    """

    PANEL_W = 1100  # 980->1100 agar muat font besar & card 250px
    PANEL_H = 720   # 640->720

    @classmethod
    def draw(cls, surface, game):
        if not getattr(game, "item_shop_open", False):
            return

        # ═══ TARGET PEMBELIAN (tidak wajib klik hero dulu) ═══
        heroes = _player_heroes(game)
        hero = _resolve_shop_target(game, heroes)
        try:
            # Disinkronkan sekali per frame supaya handler klik memakai
            # hero yang sama dengan yang digambar.
            game.itemshop_target_hero = hero
        except Exception:
            pass

        # Overlay gelap
        from mobile.perf import darken
        darken(surface, 215)

        px = (1280 - cls.PANEL_W) // 2
        py = (720 - cls.PANEL_H) // 2

        # Panel
        cls._draw_panel(surface, px, py)
        cls._draw_header(surface, game, px, py)
        cls._draw_hero_strip(surface, game, heroes, hero, px, py)
        if hero is not None:
            cls._draw_hero_info(surface, hero, px, py)
        else:
            cls._draw_no_hero_banner(surface, game, px, py)
        # Tab halaman TIER I / TIER II (16 item = 2 halaman).
        cls._draw_page_tabs(surface, game, px, py)
        # Item SELALU digambar - walau belum memilih hero.
        cls._draw_item_grid(surface, game, hero, px, py)
        if hero is not None:
            cls._draw_owned_slots(surface, game, hero, px, py)
        cls._draw_close(surface, game, px, py)

    @classmethod
    def _draw_hero_strip(cls, surface, game, heroes, target, px, py):
        """Bar pilih hero penerima item (daftar 'BUY FOR') - FONT DIPERBESAR."""
        lf = pygame.font.Font(None, 26)  # 20->26
        lt = lf.render("BUY FOR:", True, (255, 220, 100))
        surface.blit(lt, (px + 22, py + 62))

        if not heroes:
            sf = pygame.font.Font(None, 22)  # 18->22
            t = sf.render(
                tr("shop_no_hero_yet"),
                True, (255, 150, 150))
            surface.blit(t, (px + 112, py + 63))
            return

        n = len(heroes)
        area_x = px + 112
        area_w = px + cls.PANEL_W - 20 - area_x
        gap = 8
        chip_w = max(110, min(180, (area_w - gap * (n - 1)) // n))
        chip_h = 48  # 42->48
        cy = py + 54
        for i, h in enumerate(heroes):
            x = area_x + i * (chip_w + gap)
            rect = pygame.Rect(x, cy, chip_w, chip_h)
            is_target = (h is target)
            bg = (48, 64, 100) if is_target else (26, 30, 48)
            border = h.color if is_target else (70, 80, 110)
            pygame.draw.rect(surface, bg, rect, border_radius=8)
            pygame.draw.rect(surface, border, rect, 2, border_radius=8)
            pygame.draw.circle(surface, h.color,
                               (rect.x + 14, rect.centery), 6)
            # Nama (dipangkas kalau kepanjangan) - DIPERBESAR
            nf = pygame.font.Font(None, 24)  # 19->24
            nm_txt = h.name
            while nf.size(nm_txt)[0] > chip_w - 52 and len(nm_txt) > 3:
                nm_txt = nm_txt[:-1]
            if nm_txt != h.name:
                nm_txt += "…"
            nt = nf.render(nm_txt, True, (240, 245, 255))
            surface.blit(nt, (rect.x + 26, rect.y + 4))
            inv = getattr(h, "items", None)
            used = inv.used_slots() if inv is not None else 0
            sf2 = pygame.font.Font(None, 20)  # 15->20
            pending = len(pending_forge_items(h))
            is_dead = not getattr(h, "alive", False)
            status = tr("dead") if is_dead else f"Lv.{h.level}"
            queue = f" {tr('queued', count=pending)}" if pending else ""
            st = sf2.render(
                f"{status}  Item {used}/{MAX_ITEM_SLOTS}{queue}",
                True, (255, 175, 175) if is_dead else (170, 180, 205))
            surface.blit(st, (rect.x + 26, rect.y + 24))
            game.ui_buttons[f"itemshop_hero_{i}"] = rect

    @classmethod
    def _draw_no_hero_banner(cls, surface, game, px, py):
        """Banner kecil saat TIDAK ada hero hidup sama sekali - DIPERBESAR."""
        box = pygame.Rect(px + 20, py + 96, cls.PANEL_W - 40, 52)
        pygame.draw.rect(surface, (40, 28, 28), box, border_radius=8)
        pygame.draw.rect(surface, (200, 90, 90), box, 2, border_radius=8)
        f = pygame.font.Font(None, 26)  # 20->26
        t = f.render(tr("shop_no_hero_banner"),
                     True, (255, 190, 190))
        surface.blit(t, t.get_rect(center=box.center))

    # ── Helpers ──────────────────────────────────────────
    @classmethod
    def _draw_panel(cls, surface, px, py):
        # Shadow
        sh = pygame.Surface((cls.PANEL_W + 20, cls.PANEL_H + 20),
                            pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 160),
                         (10, 10, cls.PANEL_W, cls.PANEL_H),
                         border_radius=15)
        surface.blit(sh, (px - 10, py - 10))
        # BG
        pygame.draw.rect(surface, (22, 26, 44),
                         (px, py, cls.PANEL_W, cls.PANEL_H),
                         border_radius=14)
        # Gold border
        pygame.draw.rect(surface, (255, 200, 50),
                         (px, py, cls.PANEL_W, cls.PANEL_H),
                         3, border_radius=14)
        pygame.draw.rect(surface, (180, 140, 60),
                         (px + 3, py + 3, cls.PANEL_W - 6,
                          cls.PANEL_H - 6), 1, border_radius=12)

    @classmethod
    def _draw_header(cls, surface, game, px, py):
        # Judul - DIPERBESAR
        f = pygame.font.Font(None, 46)  # 38->46
        t = f.render("ITEM FORGE", True, (255, 220, 100))
        surface.blit(t, t.get_rect(center=(px + cls.PANEL_W // 2,
                                           py + 32)))
        # Gold badge kiri
        gold_bg = pygame.Rect(px + 20, py + 18, 200, 32)
        pygame.draw.rect(surface, (40, 30, 10), gold_bg, border_radius=14)
        pygame.draw.rect(surface, (255, 200, 50), gold_bg, 2,
                         border_radius=14)
        pygame.draw.circle(surface, (255, 200, 50),
                           (px + 38, py + 32), 7)
        gf = pygame.font.Font(None, 26)  # 20->26
        gt = gf.render(f"GOLD: {game.gold:,}", True, (255, 220, 100))
        surface.blit(gt, (px + 52, py + 24))

    @classmethod
    def _draw_hero_info(cls, surface, hero, px, py):
        # Kotak info hero (target BUY FOR) di bawah strip hero - FONT DIPERBESAR
        box = pygame.Rect(px + 20, py + 96, cls.PANEL_W - 40, 56)
        pygame.draw.rect(surface, (30, 36, 58), box, border_radius=8)
        pygame.draw.rect(surface, hero.color, box, 2, border_radius=8)
        f = pygame.font.Font(None, 28)  # 22->28
        name = f.render(f"{hero.name}  Lv.{hero.level}", True,
                        hero.color)
        surface.blit(name, (box.x + 12, box.y + 6))
        sf = pygame.font.Font(None, 22)  # 18->22
        rng = getattr(hero, "range", 0) or 0
        kind = "MELEE" if rng <= 80 else "RANGED"
        dmg = int(hero.damage)
        hp = int(hero.max_hp)
        inv = hero.items
        total_dmg = dmg + inv.get_bonus_damage()
        total_hp = hp
        armor = inv.get_armor()
        ls = int(inv.get_lifesteal_pct() * 100)
        as_mult = inv.get_attack_speed_mult()
        cdr = int(inv.get_cooldown_reduction() * 100)
        range_bonus = inv.get_range_bonus()
        range_txt = f"   RNG +{range_bonus}" if range_bonus > 0 else ""
        info = (f"{kind}   DMG {dmg}->{total_dmg}   HP {total_hp}   "
                f"Armor {armor}   AS x{as_mult:.2f}   LS {ls}%   "
                f"CDR {cdr}%{range_txt}")
        it = sf.render(info, True, (200, 210, 230))
        surface.blit(it, (box.x + 12, box.y + 32))
        if not getattr(hero, "alive", False):
            pending = len(pending_forge_items(hero))
            qf = pygame.font.Font(None, 22)  # 18->22
            msg = tr("dead_delivery_hint")
            if pending:
                msg += " " + tr("queued_item_count", count=pending)
            qt = qf.render(msg, True, (255, 175, 175))
            surface.blit(qt, (box.right - qt.get_width() - 12, box.y + 6))

    @classmethod
    def _draw_owned_slots(cls, surface, game, hero, px, py):
        # 6 slot dimiliki di bawah panel - FONT DIPERBESAR
        inv = hero.items
        size = 54  # 50->54 sedikit lebih besar
        gap = 8
        total_w = size * MAX_ITEM_SLOTS + gap * (MAX_ITEM_SLOTS - 1)
        sx = px + (cls.PANEL_W - total_w) // 2
        sy = py + cls.PANEL_H - 72

        f = pygame.font.Font(None, 22)  # 18->22
        label = f.render("INVENTORY  (click a slot to drop it)", True,
                         (180, 190, 220))
        surface.blit(label, label.get_rect(
            center=(px + cls.PANEL_W // 2, sy - 16)))

        for i in range(MAX_ITEM_SLOTS):
            rect = pygame.Rect(sx + i * (size + gap), sy, size, size)
            pygame.draw.rect(surface, (20, 24, 38), rect,
                             border_radius=5)
            sid = inv.slots[i]
            border = (80, 90, 120)
            if sid is not None:
                data = ITEM_CATALOG[sid]
                border = data["color"]
                icon = get_icon(sid, size - 6)
                if icon is not None:
                    surface.blit(icon, (rect.x + 3, rect.y + 3))
            pygame.draw.rect(surface, border, rect, 2, border_radius=5)
            # Daftarkan klik untuk drop (langsung di game yang digambar)
            if game is not None:
                game.ui_buttons[f"itemshop_slot_{i}"] = rect

    @classmethod
    def _draw_close(cls, surface, game, px, py):
        size = 44
        rect = pygame.Rect(px + cls.PANEL_W - size - 12,
                           py - 14, size, size)
        mx, my = pygame.mouse.get_pos()
        hover = rect.collidepoint(mx, my)
        glow = (255, 90, 90) if hover else (180, 60, 60)
        pygame.draw.circle(surface, glow, rect.center, size // 2)
        pygame.draw.circle(surface, (255, 255, 255), rect.center,
                           size // 2, 2)
        xf = pygame.font.Font(None, 28)  # 22->28
        xt = xf.render("X", True, (255, 255, 255))
        surface.blit(xt, xt.get_rect(center=rect.center))
        game.ui_buttons["itemshop_close"] = rect

    @classmethod
    def _page_count(cls):
        return max(1, (len(ITEM_SHOP_ORDER) + ITEMS_PER_PAGE - 1)
                   // ITEMS_PER_PAGE)

    @classmethod
    def _draw_page_tabs(cls, surface, game, px, py):
        """Tab TIER I / TIER II di bawah info hero (16 item = 2 hal) - DIPERBESAR."""
        pages = cls._page_count()
        if pages <= 1:
            return
        cur = getattr(game, "itemshop_page", 0)
        if not (0 <= cur < pages):
            cur = 0
        tw = 180  # 150->180
        th = 36   # 30->36
        gap = 10
        total = pages * tw + (pages - 1) * gap
        sx = px + (cls.PANEL_W - total) // 2
        sy = py + 156  # 144->156 karena hero_info box lebih tinggi
        for i in range(pages):
            rect = pygame.Rect(sx + i * (tw + gap), sy, tw, th)
            active = (i == cur)
            bg = (70, 55, 25) if active else (26, 30, 48)
            border = (255, 200, 50) if active else (70, 80, 110)
            pygame.draw.rect(surface, bg, rect, border_radius=6)
            pygame.draw.rect(surface, border, rect, 2,
                             border_radius=6)
            lf = pygame.font.Font(None, 24)  # 19->24
            label = "TIER I - CORE" if i == 0 else \
                    "TIER II - LEGENDARY" if i == 1 \
                    else "TIER III - MYTHIC" if i in (2, 3) \
                    else tr("shop_page_label", page=i + 1)
            t = lf.render(label, True, (255, 225, 130) if active
                          else (170, 180, 205))
            surface.blit(t, t.get_rect(center=rect.center))
            game.ui_buttons[f"itemshop_page_{i}"] = rect

    @classmethod
    def _draw_item_grid(cls, surface, game, hero, px, py):
        # Grid 4 kolom x 2 baris per HALAMAN - SELALU digambar - DIPERBESAR
        cols = 4
        card_w = 250  # 225->250 agar muat font besar
        card_h = 210  # 178->210
        gap_x = 12
        gap_y = 14
        grid_w = cols * card_w + (cols - 1) * gap_x
        start_x = px + (cls.PANEL_W - grid_w) // 2
        start_y = py + 200  # 172->200 karena tab lebih besar

        pages = cls._page_count()
        cur = getattr(game, "itemshop_page", 0)
        if not (0 <= cur < pages):
            cur = 0
            try:
                game.itemshop_page = 0
            except Exception:
                pass
        page_items = ITEM_SHOP_ORDER[cur * ITEMS_PER_PAGE:
                                     (cur + 1) * ITEMS_PER_PAGE]

        inv = None
        is_melee = False
        if hero is not None:
            inv = getattr(hero, "items", None)
            rng = getattr(hero, "range", 0) or 0
            is_melee = rng <= 80

        for idx, sid in enumerate(page_items):
            row = idx // cols
            col = idx % cols
            x = start_x + col * (card_w + gap_x)
            y = start_y + row * (card_h + gap_y)
            data = ITEM_CATALOG[sid]
            owned_count = inv.count(sid) if inv is not None else 0
            can_afford = game.gold >= data["cost"]
            queued = len(pending_forge_items(hero)) if hero is not None else 0
            slot_full = (inv is not None
                         and inv.used_slots() + queued >= MAX_ITEM_SLOTS)
            melee_ok = (not data.get("melee_only")) or is_melee
            can_buy = (inv is not None and can_afford
                       and not slot_full and melee_ok)
            cls._draw_item_card(surface, game, data, sid, x, y,
                                card_w, card_h, owned_count, can_buy,
                                is_melee, has_hero=inv is not None)

    @classmethod
    def _draw_item_card(cls, surface, game, data, sid, x, y, w, h,
                         owned_count, can_buy, is_melee, has_hero=True):
        # Card - DIPERBESAR
        bg = (28, 33, 54) if can_buy else (24, 22, 30)
        pygame.draw.rect(surface, bg, (x, y, w, h), border_radius=8)
        border = data["color"] if can_buy else (70, 70, 80)
        pygame.draw.rect(surface, border, (x, y, w, h), 2,
                         border_radius=8)

        # Icon - sedikit lebih besar
        icon_size = 56  # 52->56
        icon = get_icon(sid, icon_size)
        if icon is not None:
            surface.blit(icon, (x + 10, y + 10))

        # Nama - DIPERBESAR 25->32
        nf = pygame.font.Font(None, 32)
        nt = nf.render(data["name"], True, data["glow"])
        surface.blit(nt, (x + icon_size + 18, y + 12))

        # Category badge - DIPERBESAR 17->22
        cat_label, cat_color = CATEGORY_INFO[data["category"]]
        cf = pygame.font.Font(None, 22)
        ct = cf.render(cat_label, True, cat_color)
        surface.blit(ct, (x + icon_size + 18, y + 38))

        # Harga - DIPERBESAR 22->28
        costf = pygame.font.Font(None, 28)
        cost_color = (255, 220, 100) if can_buy else (200, 80, 80)
        costt = costf.render(f"{data['cost']}G", True, cost_color)
        surface.blit(costt, (x + icon_size + 18, y + 60))

        # Owned count - DIPERBESAR 16->22
        if owned_count > 0:
            of = pygame.font.Font(None, 22)
            ot = of.render(f"Owned: {owned_count}", True,
                           (150, 255, 170))
            surface.blit(ot, (x + w - 90, y + 62))

        # Deskripsi (wrap sederhana) - ikuti bahasa aktif (id/en) - DIPERBESAR 16->22
        df = pygame.font.Font(None, 22)
        lines = cls._wrap_text(cls._localized_desc(data), df, w - 20)
        ty = y + 88
        for line in lines[:4]:
            t = df.render(line, True, (200, 210, 230))
            surface.blit(t, (x + 10, ty))
            ty += 20  # 15->20

        # Tombol BUY - DIPERBESAR
        btn_rect = pygame.Rect(x + 10, y + h - 44, w - 20, 40)
        melee_warn = has_hero and data.get("melee_only") and not is_melee
        if not has_hero:
            btn_color = (60, 60, 70)
            label = "NEED HERO"
            label_color = (220, 150, 150)
        elif melee_warn:
            btn_color = (90, 60, 60)
            label = "MELEE ONLY"
            label_color = (255, 180, 180)
        elif not can_buy:
            btn_color = (60, 60, 70)
            label = "BUY"
            label_color = (160, 160, 170)
        else:
            btn_color = (50, 150, 80)
            label = "BUY"
            label_color = (255, 255, 255)
        pygame.draw.rect(surface, btn_color, btn_rect, border_radius=4)
        pygame.draw.rect(surface, (255, 255, 255), btn_rect, 1,
                         border_radius=4)
        bf = pygame.font.Font(None, 26)  # 21->26
        bt = bf.render(label, True, label_color)
        surface.blit(bt, bt.get_rect(center=btn_rect.center))
        # Daftarkan tombol (hanya kalau bisa di-klik)
        if can_buy:
            game.ui_buttons[f"itemshop_buy_{sid}"] = btn_rect

    @staticmethod
    def _localized_desc(data):
        """Deskripsi item sesuai bahasa aktif (en -> desc_en)."""
        if get_language() == "en":
            return data.get("desc_en") or data.get("desc", "")
        return data.get("desc", "")

    @staticmethod
    def _wrap_text(text, font, max_w):
        words = text.split()
        lines = []
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines


# ════════════════════════════════════════════════════════════
# CLICK HANDLER untuk ItemShopUI (dipanggil dari InputHandler)
# ════════════════════════════════════════════════════════════
def _touch_hit(rect, mx, my, minimum=48, padding=6):
    """Target sentuh minimum 48px untuk kontrol Item Forge."""
    width = max(rect.width + padding * 2, minimum)
    height = max(rect.height + padding * 2, minimum)
    hit = pygame.Rect(0, 0, width, height)
    hit.center = rect.center
    return hit.collidepoint(mx, my)


def handle_item_shop_click(game, mx, my, button):
    """Proses klik di toko item. Return True kalau klik tertangani."""
    if not getattr(game, "item_shop_open", False):
        return False

    for btn_id, rect in list(game.ui_buttons.items()):
        if not _touch_hit(rect, mx, my):
            continue
        if btn_id == "itemshop_close":
            game.item_shop_open = False
            _play_click()
            return True
        if btn_id.startswith("itemshop_hero_"):
            # ═══ PILIH HERO PENERIMA (BUY FOR list) ═══
            try:
                idx = int(btn_id.replace("itemshop_hero_", ""))
            except ValueError:
                return True
            heroes = _player_heroes(game)
            if 0 <= idx < len(heroes):
                game.itemshop_target_hero = heroes[idx]
                target = heroes[idx]
                _play_click()
                suffix = " " + tr("delivery_after_respawn") if not getattr(target, "alive", False) else ""
                _notify(game, f"BUY FOR: {target.name}{suffix}",
                        getattr(target, "color", (255, 220, 100)))
            return True
        if btn_id.startswith("itemshop_page_"):
            # ═══ GANTI HALAMAN TIER I / TIER II ═══
            try:
                idx = int(btn_id.replace("itemshop_page_", ""))
            except ValueError:
                return True
            if 0 <= idx < ItemShopUI._page_count():
                game.itemshop_page = idx
                _play_click()
            return True
        if btn_id.startswith("itemshop_buy_"):
            sid = btn_id.replace("itemshop_buy_", "")
            _try_buy(game, sid)
            return True
        if btn_id.startswith("itemshop_slot_"):
            idx = int(btn_id.replace("itemshop_slot_", ""))
            # Klik kanan untuk drop; klik kiri info (saat ini drop juga
            # untuk kemudahan mobile).
            if button in (1, 3):
                _try_drop(game, idx)
            return True

    # Klik kanan di mana pun = tutup.
    if button == 3:
        game.item_shop_open = False
        return True
    # Klik kiri di DALAM panel = tetap di toko (aman untuk sekadar
    # melihat-lihat item walau belum punya hero). Klik DI LUAR panel
    # = tutup.
    if button == 1:
        px = (1280 - ItemShopUI.PANEL_W) // 2
        py = (720 - ItemShopUI.PANEL_H) // 2
        panel = pygame.Rect(px, py, ItemShopUI.PANEL_W,
                            ItemShopUI.PANEL_H)
        if not panel.collidepoint(mx, my):
            game.item_shop_open = False
        return True
    return False


def _try_buy(game, sid):
    """Beli langsung untuk hero hidup atau antrekan untuk hero mati."""
    hero = _resolve_shop_target(game, _player_heroes(game))
    if hero is None:
        _play_error()
        _notify(game, tr("no_hero"), (255, 150, 150))
        return
    data = ITEM_CATALOG.get(sid)
    if not data:
        return
    if game.gold < data["cost"]:
        _play_error()
        return
    if hero.items.used_slots() + len(pending_forge_items(hero)) >= MAX_ITEM_SLOTS:
        _play_error()
        _notify(game, tr("inventory_full", hero=hero.name), (255, 150, 150))
        return
    if data.get("melee_only") and (getattr(hero, "range", 0) or 0) > 80:
        _play_error()
        return
    if getattr(hero, "alive", False):
        if not hero.items.add(sid):
            _play_error()
            return
        message = tr("forge_purchase", hero=hero.name, item=data["name"])
    else:
        pending_forge_items(hero).append(sid)
        message = tr("forge_queued", hero=hero.name, item=data["name"])
    game.gold -= data["cost"]
    game.itemshop_target_hero = hero
    _play_buy()
    _notify(game, message, data["glow"])


def _try_drop(game, slot_index):
    hero = getattr(game, "itemshop_target_hero", None)
    heroes = _player_heroes(game)
    if hero not in heroes:
        hero = _resolve_shop_target(game, heroes)
    if hero is None:
        return
    dropped = hero.items.remove(slot_index)
    if dropped:
        data = ITEM_CATALOG.get(dropped, {})
        _notify(game,
                tr("item_dropped", item=data.get("name", "item")),
                (255, 200, 120))
        _play_click()


def _notify(game, text, color):
    """Kirim notifikasi ke UI (game.ui.add_notification)."""
    try:
        ui = getattr(game, "ui", None)
        if ui is not None and hasattr(ui, "add_notification"):
            ui.add_notification(text, color)
    except Exception:
        pass


def _play_click():
    try:
        from _system import SoundManager
        SoundManager().play('ui_click', volume_mult=0.4)
    except Exception:
        pass


def _play_buy():
    try:
        from _system import SoundManager
        SoundManager().play('ui_buy', volume_mult=0.6)
    except Exception:
        pass


def _play_error():
    try:
        from _system import SoundManager
        SoundManager().play('ui_error', volume_mult=0.4)
    except Exception:
        pass
