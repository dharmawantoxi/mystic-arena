"""Headless test utk Item Forge: grid selalu tampil + BUY FOR hero list."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

import hero_items as hi  # noqa: E402
from hero_items import (ItemShopUI, HeroItemInventory,  # noqa: E402
                        handle_item_shop_click, ITEM_CATALOG,
                        _resolve_shop_target)


class FakeHero:
    def __init__(self, name, rng=40):
        self.name = name
        self.level = 3
        self.color = (90, 160, 255)
        self.alive = True
        self.range = rng
        self.damage = 35
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
        self.gold = 20000
        self.selected_hero = None
        self.item_shop_open = True
        self.itemshop_target_hero = None
        self.ui_buttons = {}
        self.ui = FakeUI()


surf = pygame.Surface((1280, 720))

# ── T1: TANPA hero sama sekali -> grid tetap tampil, BUY mati ──────
g = FakeGame()
ItemShopUI.draw(surf, g)
assert "itemshop_buy_moon_shard" not in g.ui_buttons, \
    "BUY harus nonaktif tanpa hero"
assert "itemshop_close" in g.ui_buttons
print("T1 OK  - grid tampil tanpa hero, BUY dimatikan")

# ── T2: ada hero (belum diklik di peta) -> auto target + strip ──────
h1, h2 = FakeHero("Aldric"), FakeHero("Mirabelle Longname")
g.heroes = [h1, h2]
g.ui_buttons = {}
ItemShopUI.draw(surf, g)
assert g.itemshop_target_hero is h1, "target otomatis = hero hidup #1"
assert "itemshop_buy_moon_shard" in g.ui_buttons, "BUY harus tersedia"
assert "itemshop_hero_0" in g.ui_buttons
assert "itemshop_hero_1" in g.ui_buttons
print("T2 OK  - item tampil walau TIDAK klik hero; strip BUY FOR = 2 chip")

# ── T3: klik chip hero #2 -> target ganti ───────────────────────────
rect = g.ui_buttons["itemshop_hero_1"]
assert handle_item_shop_click(g, rect.centerx, rect.centery, 1)
assert g.itemshop_target_hero is h2
assert any("BUY FOR: Mirabelle" in n for n in g.ui.notes)
print("T3 OK  - klik chip BUY FOR -> target =", h2.name)

# ── T4: beli Moon Shard langsung (selected_hero tetap None!) ────────
g.ui_buttons = {}
g.ui.notes.clear()
ItemShopUI.draw(surf, g)
rect = g.ui_buttons["itemshop_buy_moon_shard"]
assert handle_item_shop_click(g, rect.centerx, rect.centery, 1)
assert h2.items.has("moon_shard"), "Moon Shard harus masuk ke h2"
assert not h1.items.has("moon_shard")
assert g.gold == 20000 - ITEM_CATALOG["moon_shard"]["cost"]
assert any("Mirabelle" in n and "Moon Shard" in n for n in g.ui.notes)
print("T4 OK  - beli Moon Shard langsung utk Mirabelle, gold terpotong")

# ── T5: klik area kosong DI DALAM panel -> toko TIDAK tertutup ──────
ItemShopUI.draw(surf, g)
assert handle_item_shop_click(g, 640, 670, 1)
assert g.item_shop_open, "klik kosong dalam panel tidak boleh nutup"
# klik DI LUAR panel -> tutup
assert handle_item_shop_click(g, 10, 10, 1)
assert not g.item_shop_open
print("T5 OK  - klik dalam panel aman, klik luar panel menutup")

# ── T6: hero target mati -> fallback ke hero hidup lain ─────────────
g.item_shop_open = True
h2.alive = False
g.ui_buttons = {}
ItemShopUI.draw(surf, g)
assert g.itemshop_target_hero is h1, "target harus pindah ke hero hidup"
print("T6 OK  - target mati -> fallback otomatis ke", h1.name)

# ── T7: semua hero mati -> grid tetap tampil, BUY mati ──────────────
h1.alive = False
g.ui_buttons = {}
ItemShopUI.draw(surf, g)
assert not any(k.startswith("itemshop_buy_") for k in g.ui_buttons)
assert g.itemshop_target_hero is None
print("T7 OK  - semua hero mati: item tetap kelihatan, BUY nonaktif")

# ── T8: gold kurang -> tidak ada tombol BUY aktif ───────────────────
h1.alive = True
g.gold = 100
g.ui_buttons = {}
ItemShopUI.draw(surf, g)
assert not any(k.startswith("itemshop_buy_") for k in g.ui_buttons)
print("T8 OK  - gold tidak cukup -> BUY nonaktif")

# ── T9: drop item dari inventory target (bukan selected_hero) ───────
g.gold = 20000
g.ui_buttons = {}
ItemShopUI.draw(surf, g)
rect = g.ui_buttons["itemshop_slot_0"]
# h1 target; beri item manual lalu drop
h1.items.add("dead_edge")
ItemShopUI.draw(surf, g)
rect = g.ui_buttons["itemshop_slot_0"]
assert handle_item_shop_click(g, rect.centerx, rect.centery, 3)
assert not h1.items.has("dead_edge")
print("T9 OK  - drop item dari slot target di toko")

# ── T10: _resolve_shop_target hormati selected_hero ─────────────────
g.selected_hero = h2
h2.alive = True
g.itemshop_target_hero = None
t = _resolve_shop_target(g)
assert t is h2, "selected hero hidup harus jadi target awal"
print("T10 OK - hero terseleksi di peta otomatis jadi target awal")

print("\nSEMUA TEST LULUS ✔")
