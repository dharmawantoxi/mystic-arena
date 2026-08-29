"""Headless test paket item TIER II (8 item legendary terinspirasi Dota 2).

Mengetes:
  - integritas katalog (33 item = 8 Tier I + 8 Tier II + 10 Tier III
    + 7 paket MAGIC, ikon ada di disk, field lengkap)
  - pagination toko (tab TIER I / TIER II, BUY per halaman)
  - stat getter inventory (evasion, block, shred, bash, AS, dll.)
  - mekanik via Hero ASLI: evasion, block, veil, shred, rend, stun,
    aura Bulwark Guard, static charge, heal amp
"""
import os
import sys
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

import hero_items as hi  # noqa: E402
from hero_items import (ItemShopUI, HeroItemInventory,  # noqa: E402
                        handle_item_shop_click, ITEM_CATALOG,
                        ITEM_SHOP_ORDER, ITEMS_PER_PAGE, update_auras)

TIER2 = ["scarlet_bulwark", "monarch_wings", "corroder", "tempest_vane",
         "fenrir_chain", "sanguine_thorn", "abyss_breaker", "thunder_coil"]

TIER3 = ["razor_carapace", "everfrost_guard", "sundering_cudgel",
         "frostbound_eye", "gale_pike", "basilisk_breath",
         "solar_brand", "runic_gavel", "searbrand", "astral_codex"]

MAGIC = ["sage_scepter", "fulgur_scepter", "hex_idol", "rift_veil",
         "vital_stone", "vine_rod", "spectral_charm"]

# ── T1: katalog lengkap 33 item + ikon di disk ─────────────
assert len(ITEM_CATALOG) == 33, \
    f"katalog harus 33 item, ada {len(ITEM_CATALOG)}"
assert len(ITEM_SHOP_ORDER) == 33
assert set(ITEM_SHOP_ORDER) == set(ITEM_CATALOG.keys())
assert set(TIER2) | set(TIER3) | set(MAGIC) <= set(ITEM_CATALOG)
# Semua item paket MAGIC harus ber-flag magic_only
for sid in MAGIC:
    assert ITEM_CATALOG[sid].get("magic_only") is True, \
        f"{sid} tidak magic_only"
icons_dir = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "assets", "items")
for sid in ITEM_CATALOG:
    d = ITEM_CATALOG[sid]
    for k in ("name", "cost", "icon", "color", "glow", "stats",
              "desc", "flavor", "category"):
        assert k in d, f"{sid} kurang field {k}"
    ipath = os.path.join(icons_dir, d["icon"])
    assert os.path.exists(ipath), f"ikon {d['icon']} tidak ada"
    # Ikon harus artwork asli (bukan placeholder 64x64 kasar):
    # semua ikon Tier II & Tier III & paket MAGIC minimal 256x256.
    if sid in TIER2 or sid in TIER3 or sid in MAGIC:
        raw = pygame.image.load(ipath)
        assert raw.get_width() >= 256 and raw.get_height() >= 256, \
            f"ikon {d['icon']} masih placeholder kecil {raw.get_size()}"
    # Nama harus berbeda dari nama asli Dota 2 (anti copyright)
    for banned in ("crimson guard", "butterfly", "desolator",
                   "wind waker", "gleipnir", "bloodthorn",
                   "abyssal blade", "mjollnir", "mjolnir"):
        assert d["name"].lower() != banned, f"{sid} memakai nama Dota"
print("T1 OK  - 33 item (paket MAGIC semua magic_only), ikon ada "
      "(Tier II & III & MAGIC >= 256x256), nama bebas copyright")

# ── T2: pagination toko + BUY item Tier II ─────────────────
class FakeHero:
    def __init__(self, name, rng=40):
        self.name = name
        self.level = 3
        self.color = (90, 160, 255)
        self.alive = True
        self.range = rng
        self.damage = 35
        self.base_hp = 800
        self.max_hp = 800
        self.hp = 800
        self.items = HeroItemInventory(self)


class FakeUI:
    def __init__(self):
        self.notes = []

    def add_notification(self, text, color):
        self.notes.append(text)


class FakeGame:
    def __init__(self):
        self.heroes = []
        self.gold = 60000
        self.selected_hero = None
        self.item_shop_open = True
        self.itemshop_target_hero = None
        self.itemshop_page = 0
        self.ui_buttons = {}
        self.ui = FakeUI()


surf = pygame.Surface((1280, 720))
g = FakeGame()
g.heroes = [FakeHero("Aldric")]
ItemShopUI.draw(surf, g)
assert "itemshop_buy_dead_edge" in g.ui_buttons, \
    "halaman 0 = PHYSICAL 1"
assert "itemshop_buy_monarch_wings" in g.ui_buttons, \
    "Monarch Wings (physical) kini ikut halaman 0"
assert "itemshop_buy_sanguine_thorn" not in g.ui_buttons
assert "itemshop_page_0" in g.ui_buttons and "itemshop_page_1" in g.ui_buttons
# pindah ke halaman 2 (PHYSICAL 2)
r = g.ui_buttons["itemshop_page_1"]
assert handle_item_shop_click(g, r.centerx, r.centery, 1)
assert g.itemshop_page == 1
g.ui_buttons = {}
ItemShopUI.draw(surf, g)
assert "itemshop_buy_sanguine_thorn" in g.ui_buttons, \
    "halaman 1 = PHYSICAL 2 (late-game carry)"
assert "itemshop_buy_dead_edge" not in g.ui_buttons
assert "itemshop_buy_monarch_wings" not in g.ui_buttons
# beli Sanguine Thorn
r = g.ui_buttons["itemshop_buy_sanguine_thorn"]
assert handle_item_shop_click(g, r.centerx, r.centery, 1)
assert g.heroes[0].items.has("sanguine_thorn")
assert g.gold == 60000 - ITEM_CATALOG["sanguine_thorn"]["cost"]
print("T2 OK  - tab PHYSICAL 1/2 pindah halaman & beli Sanguine Thorn")

# ── T3: getter stat inventory ──────────────────────────────
h = FakeHero("Melee", rng=40)
inv = h.items
assert inv.add("monarch_wings")
assert abs(inv.get_evasion() - 0.28) < 1e-9
assert inv.get_attack_speed_mult() > 1.25
assert inv.add("corroder")
assert inv.get_armor_shred() == (6, 360)
assert inv.add("scarlet_bulwark")
blk = inv.get_block()
assert blk is not None and blk[1] == 25  # melee block
_mult = hi._hero_level_mult(h)
assert h.max_hp == int(int(800 * _mult) + 250), (h.max_hp, _mult)
assert inv.add("abyss_breaker")
assert abs(inv.get_heal_amp() - 0.16) < 1e-9
assert inv.get_bash()["chance"] == 0.22
h2 = FakeHero("Ranged", rng=400)
inv2 = h2.items
inv2.add("scarlet_bulwark")
assert inv2.get_block()[1] == 14  # ranged block lebih kecil
assert inv2.add("tempest_vane")
assert abs(inv2.get_move_speed_pct() - 0.12) < 1e-9
print("T3 OK  - getter evasion/block/shred/bash/heal-amp/move-speed")

# ── T4 (Hero ASLI): evasion + block + veil + shred + amp ───
from _entity import Hero  # noqa: E402

random.seed(7)
hero = Hero("kaizen", "blue")
foe = Hero("kaizen", "red")

# tanpa item: 30 serangan kecil masuk semua (hero tidak mati)
base = hero.hp
for _ in range(30):
    hero.take_damage(10, "red")
lost_plain = base - hero.hp
assert lost_plain == 300, lost_plain
hero.hp = hero.max_hp

# pasang Monarch Wings (28% evasion) -> sebagian MISS
hero.items.add("monarch_wings")
hits = 0
for _ in range(200):
    hero.hp = hero.max_hp
    hero.alive = True
    hp0 = hero.hp
    hero.take_damage(10, "red")
    if hero.hp < hp0:
        hits += 1
assert 0 < hits < 200, f"evasion tidak bekerja (hits={hits})"
print(f"T4a OK - evasion: {200 - hits} MISS dari 200 serangan")

# Scarlet Bulwark: block pasif mengurangi damage fisik
hero2 = Hero("kaizen", "blue")
hero2.items.add("scarlet_bulwark")
# Scarlet Bulwark juga +6 armor, jadi hit penuh = 100 dipotong
# reduksi armor; hit terblok = (100 - 25) dipotong reduksi yang sama.
losses = []
for _ in range(100):
    hp0 = hero2.hp
    if hp0 <= 150:
        hero2.hp = hero2.max_hp
        hp0 = hero2.hp
    hero2.take_damage(100, "red")
    losses.append(hp0 - hero2.hp)
uniq = sorted(set(losses))
assert len(uniq) == 2, f"harus ada 2 hasil (blok/tidak): {uniq}"
full_lost, blocked_lost = uniq[1], uniq[0]
assert full_lost - blocked_lost == 25, uniq  # block melee 25
assert losses.count(blocked_lost) > 0
assert losses.count(full_lost) > 0
print(f"T4b OK - block: {losses.count(blocked_lost)} terblok / "
      f"{losses.count(full_lost)} penuh dari 100 hit "
      f"(-{full_lost - blocked_lost} dmg per blok)")

# Tempest Veil: kebal total saat aktif
hero3 = Hero("kaizen", "blue")
hero3.items.add("tempest_vane")
hero3.items.veil_timer = 100
hp0 = hero3.hp
hero3.take_damage(999, "red")
assert hero3.hp == hp0, "veil harus kebal semua damage"
hero3.items.veil_timer = 0
# auto-trigger saat HP kritis
hero3.hp = int(hero3.max_hp * 0.30)
hero3.items.update(1)
assert hero3.items.veil_timer > 0, "veil auto saat HP<40%"
print("T4c OK - Tempest Veil kebal + auto-trigger HP kritis")

# Corroder: armor target terkikis -> damage membesar 36%
hero4 = Hero("kaizen", "blue")
foe4 = Hero("kaizen", "red")
hero4.items.add("corroder")
foe4.apply_armor_shred(6, 360)
hp0 = foe4.hp
foe4.take_damage(100, "blue")
lost = hp0 - foe4.hp
assert lost == 136, f"shred -6 armor harus = x1.36, dapat {lost}"
# Soul Rend amp +30%
foe4b = Hero("kaizen", "red")
foe4b.apply_damage_amp(0.30, 300)
hp0 = foe4b.hp
foe4b.take_damage(100, "blue")
assert hp0 - foe4b.hp == 130
print("T4d OK - Corroder shred x1.36 & Soul Rend amp x1.30")

# ── T5: stun menghambat gerak/serang (hero + mixin) ────────
hero5 = Hero("kaizen", "blue")
foe5 = Hero("kaizen", "red")
foe5.x, foe5.y = hero5.x + 20, hero5.y
hero5.target = foe5
hp0 = foe5.hp
hero5.apply_stun(60)
assert hero5.stun_timer == 60
assert hero5._eff_speed() == 0
assert hero5._eff_attack_cd(30) == 9999
hero5._do_attack()
assert foe5.hp == hp0, "hero stun tidak boleh menyerang"
# boss punya resist: durasi dipotong 55%
class FakeBoss:
    boss_class = "true"
    alive = True
    stun_timer = 0
    def _init_tower_debuffs(self):
        from _core import TowerDebuffMixin
        TowerDebuffMixin._init_tower_debuffs(self)
from _core import TowerDebuffMixin  # noqa: E402
fb = FakeBoss()
fb._init_tower_debuffs()
TowerDebuffMixin.apply_stun(fb, 100)
assert fb.stun_timer == 45, fb.stun_timer
print("T5 OK  - stun: speed 0, atk cd 9999, boss resist 55%")

# ── T6: aura Bulwark Guard ke sekutu dekat ─────────────────
a = Hero("kaizen", "blue")
b = Hero("kaizen", "blue")
a.x, a.y = 500, 300
b.x, b.y = 560, 300   # jarak 60 < 320
a.items.add("scarlet_bulwark")
a.items.guard_timer = 100
update_auras([a, b])
assert a.items.aura_guard_block > 0
assert b.items.aura_guard_block > 0
exp = 35 + int(a.max_hp * 0.02)
assert b.items.aura_guard_block == exp, \
    (b.items.aura_guard_block, exp)
print(f"T6 OK  - Bulwark Guard aura block {exp} ke sekutu dekat")

# ── T7: Static Charge proc saat dipukul + zap musuh ────────
random.seed(3)
hero7 = Hero("kaizen", "blue")
foe7 = Hero("kaizen", "red")
foe7.x, foe7.y = hero7.x + 50, hero7.y
hero7.items.add("thunder_coil")
for _ in range(200):
    hero7.items.notify_damage_taken()
    if hero7.items.static_timer > 0:
        break
assert hero7.items.static_timer > 0, "static charge tidak pernah proc"
hp0 = foe7.hp
hero7.items.update(1, enemies=[foe7])
# zap pertama butuh tick; paksa tick
hero7.items.static_tick = 1
hero7.items.update(1, enemies=[foe7])
assert foe7.hp < hp0, "static charge tidak men-zap musuh"
print("T7 OK  - Static Charge proc & zap musuh terdekat")

# ── T8: Soul Rend -> crit pasti 150% di _do_attack ─────────
hero8 = Hero("kaizen", "blue")
foe8 = Hero("kaizen", "red")
hero8.items.add("sanguine_thorn")
hero8.items.rend_timer = 100
hero8.items.rend_target = foe8
hero8.target = foe8
foe8.x, foe8.y = hero8.x + 20, hero8.y  # dalam range melee
foe8.hp = foe8.max_hp
hero8.attack_timer = 0
hero8._do_attack()
# damage = base + bonus item (+25 dari Sanguine Thorn), lalu x1.5
dmg_expect = int((hero8.damage
                  + hero8.items.get_bonus_damage()) * 1.5)
lost = foe8.max_hp - foe8.hp
assert lost == dmg_expect, (lost, dmg_expect)
print(f"T8 OK  - Soul Rend crit pasti: {dmg_expect} damage")

# ── T9: AI suggestion mencakup item Tier II ────────────────
class RoleHero:
    role = "marksman"
    range = 400
    alive = True
sug = hi.suggest_item_for_hero(RoleHero(), set())
assert sug in ITEM_CATALOG
pool_seen = set()
for role in ("tank", "marksman", "mage", "support"):
    rh = RoleHero()
    rh.role = role
    owned = set()
    for _ in range(9):
        s = hi.suggest_item_for_hero(rh, owned)
        if not s:
            break
        owned.add(s)
        pool_seen.add(s)
assert pool_seen & set(TIER2), "AI tidak pernah menyarankan Tier II"
print("T9 OK  - AI menyarankan item Tier II:",
      sorted(pool_seen & set(TIER2)))

# ── T10: heal amp memperbesar heal (hp setter) ─────────────
u = TowerDebuffMixin()
u.alive = True
u._init_tower_debuffs()
u.max_hp = 1000
u.hp = 500
u.apply_heal_amp(0.16, 999999)
u.hp = 600   # heal 100 -> jadi 116
assert u.hp == 616, u.hp
print("T10 OK - heal amp +16% memperbesar heal")

print("\nSEMUA TEST TIER II LULUS ✔")
