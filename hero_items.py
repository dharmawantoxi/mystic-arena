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

Tiap hero punya 3 slot item. Item beli pakai GOLD in-game, bisa didrop
(klik kanan slot di panel item), dan HILANG saat hero mati KECUALI Holy
Rapier yang memang rontok (tidak balik).

Modul ini menengahi:
  - ITEM_CATALOG       data stat/harga/deskripsi
  - HeroItemInventory  logika stat + pasif
  - ItemShopUI         panel toko item di dalam HeroPanel
  - HeroItemRenderer   gambar 3 slot di HeroPanel
"""

import os
import math
import random

import pygame

# Konstanta gameplay
MAX_ITEM_SLOTS = 3
# Harga semua item diseragamkan (12000G)
ITEM_FLAT_COST = 12000

# Kategori item (dipakai AI & sorting UI)
CATEGORY_CRIT     = "crit"
CATEGORY_DAMAGE   = "damage"
CATEGORY_LIFESTEAL= "lifesteal"
CATEGORY_TANK     = "tank"
CATEGORY_SPLASH   = "splash"
CATEGORY_AS_ARMOR = "as_armor"
CATEGORY_AS       = "attack_speed"
CATEGORY_CASTER   = "caster"

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
            "damage": 80,
            "crit_chance": 0.30,
            "crit_mult": 2.25,
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": "+80 Damage. 30% peluang Critical Strike (225% damage).",
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
            "damage": 300,
        },
        "melee_only": False,
        # Rapier suci RONTOK saat pemilik tumbang - tidak bisa diambil
        # kembali (sesuai sifat aslinya).
        "drops_on_death": True,
        "desc": "+300 Damage. HILANG saat hero mati (tidak dijatuhkan).",
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
            "damage": 25,
            "armor": 5,
            "lifesteal": 0.25,
        },
        "active": {
            # Unholy Rage otomatis menyala saat HP kritis
            "name": "Blood Frenzy",
            "hp_threshold": 0.35,
            "lifesteal_bonus": 1.50,   # total 25% + 150% = 175%
            "duration": 300,           # 5 detik
            "cooldown": 1500,          # 25 detik
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+25 Damage, +5 Armor, 25% Lifesteal. "
                 "Saat HP < 35%: aktif Blood Frenzy, lifesteal 175% "
                 "selama 5 detik."),
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
            "hp": 1000,
            "hp_regen": 8.0,
        },
        # Pasif kedua: regen besar (2% max HP/detik) jika tidak
        # menerima damage selama 5 detik.
        "passive": {
            "name": "Leviathan Vitality",
            "out_of_combat_regen_pct": 0.02,
            "combat_timeout": 300,
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+1000 HP, +8 HP/reg. Di luar pertempuran (5 dtk tanpa "
                 "damage): regenerasi 2% Max HP per detik."),
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
            "damage": 55,
            "hp_regen": 4.0,
        },
        "passive": {
            "name": "Cleave",
            "cleave_pct": 0.60,
            "cleave_radius": 120,
        },
        "melee_only": True,
        "drops_on_death": False,
        "desc": ("+55 Damage, +4 HP/reg. Serangan melee membelah: 60% "
                 "damage ke musuh dalam radius 120 (hanya melee)."),
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
            "armor": 6,
            "attack_speed": 45,
        },
        "aura": {
            # Aura diratakan oleh update_auras()
            "name": "Steel Aura",
            "ally_radius": 350,
            "ally_armor": 2,
            "ally_attack_speed": 15,
            "enemy_radius": 350,
            "enemy_armor_reduction": 3,
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+6 Armor, +45 Attack Speed. Aura: sekutu di dekat "
                 "dapat +2 Armor & +15 AS; musuh di dekat kehilangan "
                 "3 Armor."),
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
            "attack_speed": 120,
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": "+120 Attack Speed. Serangan secepat cahaya bulan.",
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
            "hp": 450,
            "cooldown_reduction": 0.20,
            "spell_vamp": 0.15,
            "hp_regen": 2.0,
        },
        "melee_only": False,
        "drops_on_death": False,
        "desc": ("+450 HP, +2 HP/reg, 20% Cooldown Reduction, 15% Spell "
                 "Lifesteal (heal = 15% damage skill yang dikeluarkan)."),
        "flavor": "Inti ungu yang berputar dengan kekuatan arcane.",
    },
}

# Urutan tampil di toko (sama dengan urutan permintaan pengguna)
ITEM_SHOP_ORDER = [
    "dead_edge",
    "holy_rapier",
    "demon_maw",
    "leviathan_heart",
    "cleave_axe",
    "steel_aegis",
    "moon_shard",
    "octarine_core",
]

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
            f = pygame.font.Font(None, 11)
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

    # ── Manajemen slot ────────────────────────────────────
    def count(self, item_id):
        return sum(1 for s in self.slots if s == item_id)

    def has(self, item_id):
        return item_id in self.slots

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

    def clear_on_death(self):
        """Dipanggil saat hero mati - Holy Rapier hilang permanen."""
        dropped_rapier = False
        for i in range(MAX_ITEM_SLOTS):
            if self.slots[i] == "holy_rapier":
                self.slots[i] = None
                dropped_rapier = True
        # Reset timer aktif
        self.blood_frenzy_timer = 0
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
        return self._sum_stat("hp")

    def get_armor(self):
        return (self._sum_stat("armor")
                + getattr(self, "aura_armor", 0)
                - getattr(self, "aura_armor_reduction", 0))

    def get_hp_regen(self):
        return self._sum_stat("hp_regen")

    def get_max_hp(self):
        """Max HP = base (setelah level) + bonus item."""
        base = int(getattr(self.hero, "base_hp", 0)
                   * _hero_level_mult(self.hero))
        return base + self.get_bonus_hp()

    def get_attack_speed_mult(self):
        """Pengali attack speed (1.0 = normal).

        Dota: 1 attack speed = +1% lebih cepat. Kita cap 2.0
        (setara +100 AS) supaya attack_cooldown tidak jadi 1.
        """
        as_total = (self._sum_stat("attack_speed")
                    + getattr(self, "aura_as", 0))
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

    # ── Update per-frame ─────────────────────────────────
    def update(self, dt=1):
        # Timer aktif
        if self.blood_frenzy_timer > 0:
            self.blood_frenzy_timer -= dt
        if self.blood_frenzy_cd > 0:
            self.blood_frenzy_cd -= dt
        if self.last_damage_timer > 0:
            self.last_damage_timer -= dt

        # Auto-trigger Blood Frenzy saat HP kritis
        if self.has("demon_maw") and self.blood_frenzy_cd <= 0:
            h = self.hero
            if h.alive and h.max_hp > 0 and h.hp / h.max_hp < 0.35:
                act = ITEM_CATALOG["demon_maw"]["active"]
                self.blood_frenzy_timer = act["duration"]
                self.blood_frenzy_cd = act["cooldown"]

        # HP regen (base item regen + Leviathan out-of-combat +
        # Octarine small regen sudah termasuk angka stat).
        h = self.hero
        if h.alive and h.max_hp > 0 and h.hp < h.max_hp:
            regen = self.get_hp_regen()
            # Leviathan Heart pasif
            if self.has("leviathan_heart"):
                p = ITEM_CATALOG["leviathan_heart"]["passive"]
                if self.last_damage_timer <= 0:
                    regen += h.max_hp * p["out_of_combat_regen_pct"] / 60.0
            if regen > 0:
                h.hp = min(h.max_hp, h.hp + regen)

    def notify_damage_taken(self):
        """Dipanggil dari Hero.take_damage untuk reset timer combat."""
        if self.has("leviathan_heart"):
            p = ITEM_CATALOG["leviathan_heart"]["passive"]
            self.last_damage_timer = p["combat_timeout"]

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

    if "tank" in role or "bruiser" in role or "fighter" in role:
        pool = ["leviathan_heart", "steel_aegis", "demon_maw",
                "octarine_core", "moon_shard"]
    elif "marksman" in role or "assassin" in role:
        pool = ["dead_edge", "moon_shard", "demon_maw",
                "octarine_core", "steel_aegis"]
    elif "mage" in role or "trickster" in role:
        pool = ["octarine_core", "moon_shard", "steel_aegis",
                "demon_maw", "dead_edge"]
    else:
        pool = ["steel_aegis", "moon_shard", "demon_maw",
                "leviathan_heart", "octarine_core", "dead_edge"]

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
                # Glow kalau item aktif
                if sid == "demon_maw" and inv.blood_frenzy_timer > 0:
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


# ════════════════════════════════════════════════════════════
# UI: ITEM SHOP OVERLAY (dibuka dari tombol di HeroPanel)
# ════════════════════════════════════════════════════════════
class ItemShopUI:
    """Overlay toko item yang berhubungan dengan hero terpilih.

    Pemakaian:
        game.item_shop_open = True/False
        game.ui.draw_item_shop(screen)
    """

    PANEL_W = 980
    PANEL_H = 640

    @classmethod
    def draw(cls, surface, game):
        if not getattr(game, "item_shop_open", False):
            return
        hero = game.selected_hero

        # Overlay gelap
        from mobile.perf import darken
        darken(surface, 215)

        px = (1280 - cls.PANEL_W) // 2
        py = (720 - cls.PANEL_H) // 2

        # Panel
        cls._draw_panel(surface, px, py)
        cls._draw_header(surface, game, px, py)
        if hero is not None and getattr(hero, "alive", False):
            cls._draw_hero_info(surface, hero, px, py)
            cls._draw_item_grid(surface, game, hero, px, py)
            cls._draw_owned_slots(surface, hero, px, py)
        else:
            cls._draw_no_hero(surface, game, px, py)
        cls._draw_close(surface, game, px, py)

    @classmethod
    def _draw_no_hero(cls, surface, game, px, py):
        """Ditampilkan kalau pemain mengetuk ITEM FORGE tanpa memilih
        hero dulu. Jendela langsung menutup sendiri saat pemain
        meng-klik di mana pun (ditangani handle_item_shop_click)."""
        f = pygame.font.Font(None, 28)
        t1 = f.render("PILIH HERO DULU", True, (255, 200, 200))
        surface.blit(t1, t1.get_rect(
            center=(px + cls.PANEL_W // 2, py + cls.PANEL_H // 2 - 16)))
        sf = pygame.font.Font(None, 18)
        t2 = sf.render(
            "Klik hero di peta, lalu ketuk bangunan ITEM FORGE lagi.",
            True, (200, 210, 230))
        surface.blit(t2, t2.get_rect(
            center=(px + cls.PANEL_W // 2, py + cls.PANEL_H // 2 + 16)))

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
        # Judul
        f = pygame.font.Font(None, 38)
        t = f.render("ITEM FORGE", True, (255, 220, 100))
        surface.blit(t, t.get_rect(center=(px + cls.PANEL_W // 2,
                                           py + 32)))
        # Gold badge kiri
        gold_bg = pygame.Rect(px + 20, py + 18, 180, 28)
        pygame.draw.rect(surface, (40, 30, 10), gold_bg, border_radius=14)
        pygame.draw.rect(surface, (255, 200, 50), gold_bg, 2,
                         border_radius=14)
        pygame.draw.circle(surface, (255, 200, 50),
                           (px + 38, py + 32), 7)
        gf = pygame.font.Font(None, 20)
        gt = gf.render(f"GOLD: {game.gold:,}", True, (255, 220, 100))
        surface.blit(gt, (px + 52, py + 24))

    @classmethod
    def _draw_hero_info(cls, surface, hero, px, py):
        # Kotak info hero di bawah header
        box = pygame.Rect(px + 20, py + 60, cls.PANEL_W - 40, 50)
        pygame.draw.rect(surface, (30, 36, 58), box, border_radius=8)
        pygame.draw.rect(surface, hero.color, box, 2, border_radius=8)
        f = pygame.font.Font(None, 22)
        name = f.render(f"{hero.name}  Lv.{hero.level}", True,
                        hero.color)
        surface.blit(name, (box.x + 12, box.y + 6))
        sf = pygame.font.Font(None, 18)
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
        info = (f"{kind}   DMG {dmg}->{total_dmg}   HP {total_hp}   "
                f"Armor {armor}   AS x{as_mult:.2f}   LS {ls}%   "
                f"CDR {cdr}%")
        it = sf.render(info, True, (200, 210, 230))
        surface.blit(it, (box.x + 12, box.y + 28))

    @classmethod
    def _draw_owned_slots(cls, surface, hero, px, py):
        # 6 slot dimiliki di bawah panel
        inv = hero.items
        size = 44
        gap = 6
        total_w = size * MAX_ITEM_SLOTS + gap * (MAX_ITEM_SLOTS - 1)
        sx = px + (cls.PANEL_W - total_w) // 2
        sy = py + cls.PANEL_H - 68

        f = pygame.font.Font(None, 18)
        label = f.render("INVENTORY  (click a slot to drop it)", True,
                         (180, 190, 220))
        surface.blit(label, label.get_rect(
            center=(px + cls.PANEL_W // 2, sy - 14)))

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
            # Daftarkan klik untuk drop
            g = _get_game()
            if g is not None:
                g.ui_buttons[f"itemshop_slot_{i}"] = rect

    @classmethod
    def _draw_close(cls, surface, game, px, py):
        size = 32
        rect = pygame.Rect(px + cls.PANEL_W - size - 12,
                           py - 14, size, size)
        mx, my = pygame.mouse.get_pos()
        hover = rect.collidepoint(mx, my)
        glow = (255, 90, 90) if hover else (180, 60, 60)
        pygame.draw.circle(surface, glow, rect.center, size // 2)
        pygame.draw.circle(surface, (255, 255, 255), rect.center,
                           size // 2, 2)
        xf = pygame.font.Font(None, 22)
        xt = xf.render("X", True, (255, 255, 255))
        surface.blit(xt, xt.get_rect(center=rect.center))
        game.ui_buttons["itemshop_close"] = rect

    @classmethod
    def _draw_item_grid(cls, surface, game, hero, px, py):
        # Grid 4 kolom x 2 baris
        cols = 4
        card_w = 225
        card_h = 190
        gap_x = 10
        gap_y = 12
        grid_w = cols * card_w + (cols - 1) * gap_x
        start_x = px + (cls.PANEL_W - grid_w) // 2
        start_y = py + 125

        inv = hero.items
        rng = getattr(hero, "range", 0) or 0
        is_melee = rng <= 80

        for idx, sid in enumerate(ITEM_SHOP_ORDER):
            row = idx // cols
            col = idx % cols
            x = start_x + col * (card_w + gap_x)
            y = start_y + row * (card_h + gap_y)
            data = ITEM_CATALOG[sid]
            owned_count = inv.count(sid)
            can_afford = game.gold >= data["cost"]
            slot_full = all(s is not None for s in inv.slots)
            melee_ok = (not data.get("melee_only")) or is_melee
            can_buy = can_afford and not slot_full and melee_ok
            cls._draw_item_card(surface, game, data, sid, x, y,
                                card_w, card_h, owned_count, can_buy,
                                is_melee)

    @classmethod
    def _draw_item_card(cls, surface, game, data, sid, x, y, w, h,
                         owned_count, can_buy, is_melee):
        # Card
        bg = (28, 33, 54) if can_buy else (24, 22, 30)
        pygame.draw.rect(surface, bg, (x, y, w, h), border_radius=8)
        border = data["color"] if can_buy else (70, 70, 80)
        pygame.draw.rect(surface, border, (x, y, w, h), 2,
                         border_radius=8)

        # Icon
        icon_size = 52
        icon = get_icon(sid, icon_size)
        if icon is not None:
            surface.blit(icon, (x + 10, y + 10))

        # Nama
        nf = pygame.font.Font(None, 22)
        nt = nf.render(data["name"], True, data["glow"])
        surface.blit(nt, (x + icon_size + 18, y + 12))

        # Category badge
        cat_label, cat_color = CATEGORY_INFO[data["category"]]
        cf = pygame.font.Font(None, 15)
        ct = cf.render(cat_label, True, cat_color)
        surface.blit(ct, (x + icon_size + 18, y + 36))

        # Harga
        costf = pygame.font.Font(None, 20)
        cost_color = (255, 220, 100) if can_buy else (200, 80, 80)
        costt = costf.render(f"{data['cost']}G", True, cost_color)
        surface.blit(costt, (x + icon_size + 18, y + 54))

        # Owned count
        if owned_count > 0:
            of = pygame.font.Font(None, 16)
            ot = of.render(f"Owned: {owned_count}", True,
                           (150, 255, 170))
            surface.blit(ot, (x + w - 80, y + 56))

        # Deskripsi (wrap sederhana)
        df = pygame.font.Font(None, 15)
        lines = cls._wrap_text(data["desc"], df, w - 20)
        ty = y + 74
        for line in lines[:4]:
            t = df.render(line, True, (200, 210, 230))
            surface.blit(t, (x + 10, ty))
            ty += 15

        # Tombol BUY
        btn_rect = pygame.Rect(x + 10, y + h - 30, w - 20, 24)
        melee_warn = data.get("melee_only") and not is_melee
        if melee_warn:
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
        bf = pygame.font.Font(None, 18)
        bt = bf.render(label, True, label_color)
        surface.blit(bt, bt.get_rect(center=btn_rect.center))
        # Daftarkan tombol (hanya kalau bisa di-klik)
        if can_buy:
            game.ui_buttons[f"itemshop_buy_{sid}"] = btn_rect

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
def handle_item_shop_click(game, mx, my, button):
    """Proses klik di toko item. Return True kalau klik tertangani."""
    if not getattr(game, "item_shop_open", False):
        return False

    for btn_id, rect in list(game.ui_buttons.items()):
        if not rect.collidepoint(mx, my):
            continue
        if btn_id == "itemshop_close":
            game.item_shop_open = False
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
    # Klik di luar panel / kanan = tutup. Pada "pilih hero dulu"
    # layar apa pun klik menutup.
    if button in (1, 3):
        game.item_shop_open = False
        return True
    return False


def _try_buy(game, sid):
    hero = game.selected_hero
    if hero is None or not hero.alive:
        return
    data = ITEM_CATALOG.get(sid)
    if not data:
        return
    if game.gold < data["cost"]:
        _play_error()
        return
    if not hero.items.add(sid):
        _play_error()
        return
    game.gold -= data["cost"]
    _play_buy()
    _notify(game, f"{hero.name} membeli {data['name']}!", data["glow"])


def _try_drop(game, slot_index):
    hero = game.selected_hero
    if hero is None:
        return
    dropped = hero.items.remove(slot_index)
    if dropped:
        data = ITEM_CATALOG.get(dropped, {})
        _notify(game,
                f"Melepas {data.get('name', 'item')} (tanpa refund)",
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
