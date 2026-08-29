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

# ── T6: hero mati tetap bisa dipilih dan item masuk antrean ─────────
g.item_shop_open = True
h2.alive = False
g.ui_buttons = {}
ItemShopUI.draw(surf, g)
assert g.itemshop_target_hero is h2, "target mati tidak boleh diganti otomatis"
rect = g.ui_buttons["itemshop_buy_dead_edge"]
gold_before = g.gold
assert handle_item_shop_click(g, rect.centerx, rect.centery, 1)
assert not h2.items.has("dead_edge"), "item belum masuk sebelum respawn"
assert h2._pending_forge_items == ["dead_edge"]
assert g.gold == gold_before - ITEM_CATALOG["dead_edge"]["cost"]
print("T6 OK  - item hero mati diantrikan sampai respawn")

# ── T7: semua hero mati tetap dapat forge untuk antrean ──────────────
h1.alive = False
g.ui_buttons = {}
ItemShopUI.draw(surf, g)
assert any(k.startswith("itemshop_buy_") for k in g.ui_buttons)
assert g.itemshop_target_hero is h2
print("T7 OK  - semua hero mati: forge tetap aktif untuk antrean")

# ── T8: gold kurang -> tidak ada tombol BUY aktif ───────────────────
h1.alive = True
g.gold = 100
g.ui_buttons = {}
ItemShopUI.draw(surf, g)
assert not any(k.startswith("itemshop_buy_") for k in g.ui_buttons)
print("T8 OK  - gold tidak cukup -> BUY nonaktif")

# ── T9: item antrean dikirim setelah respawn ─────────────────────────
from hero_items import deliver_pending_forge_items
delivered = deliver_pending_forge_items(h2)
assert delivered == ["dead_edge"]
assert h2.items.has("dead_edge")
print("T9 OK  - item antrean masuk inventory setelah respawn")

# ── T10: drop item dari inventory target (bukan selected_hero) ──────
g.gold = 20000
g.itemshop_target_hero = h1
h1.items.add("dead_edge")
g.ui_buttons = {}
ItemShopUI.draw(surf, g)
rect = g.ui_buttons["itemshop_slot_0"]
assert handle_item_shop_click(g, rect.centerx, rect.centery, 3)
assert not h1.items.has("dead_edge")
print("T10 OK - drop item dari slot target di toko")

# ── T11: _resolve_shop_target hormati selected_hero ─────────────────
g.selected_hero = h2
h2.alive = True
g.itemshop_target_hero = None
t = _resolve_shop_target(g)
assert t is h2, "selected hero hidup harus jadi target awal"
print("T11 OK - hero terseleksi di peta otomatis jadi target awal")

# ═══ BAGIAN BARU: POPUP DETAIL ITEM (info lengkap) ═══

# ── T12: ketuk kartu item -> popup detail terbuka ─────────────────
g.item_shop_open = True
g.itemshop_inspect_item = None
g.gold = 20000
g.ui_buttons = {}
ItemShopUI.draw(surf, g)
rect = g.ui_buttons["itemshop_card_dead_edge"]
assert handle_item_shop_click(g, rect.x + 40, rect.y + 40, 1)
assert g.itemshop_inspect_item == "dead_edge"
ItemShopUI.draw(surf, g)
assert "itemshop_detail_close" in g.ui_buttons, \
    "popup detail harus punya tombol X"
assert "itemshop_detail_rect" in dir(g) or \
    getattr(g, "itemshop_detail_rect", None) is not None
print("T12 OK - ketuk kartu item membuka popup detail")

# ── T13: saat popup terbuka, klik BUY di belakangnya TIDAK tembus ──
g.gold = 20000
gold_before = g.gold
ItemShopUI.draw(surf, g)
buy = g.ui_buttons["itemshop_buy_dead_edge"]
assert handle_item_shop_click(g, buy.centerx, buy.centery, 1)
assert g.gold == gold_before, "popup modal harus menahan klik BUY"
assert g.itemshop_inspect_item == "dead_edge"
print("T13 OK - klik BUY di belakang popup tidak menembus")

# ── T14: klik di luar popup -> detail tertutup, toko tetap buka ────
assert handle_item_shop_click(g, 640, 700, 1)
assert g.itemshop_inspect_item is None
assert g.item_shop_open, "toko tidak boleh ikut tertutup"
print("T14 OK - klik luar popup menutup detail, toko tetap buka")

# ── T15: X popup menutup detail saja; X toko menutup semuanya ──────
g.itemshop_inspect_item = "dead_edge"
g.ui_buttons = {}
ItemShopUI.draw(surf, g)
crect = g.ui_buttons["itemshop_detail_close"]
assert handle_item_shop_click(g, crect.centerx, crect.centery, 1)
assert g.itemshop_inspect_item is None and g.item_shop_open
g.itemshop_inspect_item = "dead_edge"
g.ui_buttons = {}
ItemShopUI.draw(surf, g)
crect = g.ui_buttons["itemshop_close"]
assert handle_item_shop_click(g, crect.centerx, crect.centery, 1)
assert g.itemshop_inspect_item is None and not g.item_shop_open
print("T15 OK - tombol X popup & X toko berperilaku benar")

# ── T16: klik kanan kartu juga buka detail (bukan tutup toko) ──────
g.item_shop_open = True
g.itemshop_inspect_item = None
g.ui_buttons = {}
ItemShopUI.draw(surf, g)
rect = g.ui_buttons["itemshop_card_moon_shard"]
assert handle_item_shop_click(g, rect.centerx, rect.centery, 3)
assert g.itemshop_inspect_item == "moon_shard" and g.item_shop_open
g.itemshop_inspect_item = None
print("T16 OK - klik kanan kartu membuka detail")

# ── T17: ketuk slot inventory terisi = info; kanan/tahan = drop ────
h1.alive = True
h1.items.add("dead_edge")
g.itemshop_target_hero = h1
g.item_shop_open = True
g.itemshop_inspect_item = None
g.ui_buttons = {}
ItemShopUI.draw(surf, g)
rect = g.ui_buttons["itemshop_slot_0"]
assert handle_item_shop_click(g, rect.centerx, rect.centery, 1)
assert g.itemshop_inspect_item == "dead_edge", "ketuk slot = info"
assert h1.items.has("dead_edge"), "ketuk kiri TIDAK boleh drop"
g.itemshop_inspect_item = None
g.ui_buttons = {}
ItemShopUI.draw(surf, g)
rect = g.ui_buttons["itemshop_slot_0"]
assert handle_item_shop_click(g, rect.centerx, rect.centery, 3)
assert not h1.items.has("dead_edge"), "klik kanan = drop"
print("T17 OK - ketuk slot = info lengkap, kanan/tahan = drop")

# ── T18: popup detail SEMUA item render tanpa error ────────────────
from hero_items import _build_item_mechanics
for sid in ITEM_CATALOG:
    g.itemshop_inspect_item = sid
    g.ui_buttons = {}
    ItemShopUI.draw(surf, g)
    assert "itemshop_detail_close" in g.ui_buttons, f"popup {sid}"
    mech = _build_item_mechanics(ITEM_CATALOG[sid])
    assert any(k == "bullet" for k, _ in mech), \
        f"mekanik item {sid} kosong"
print("T18 OK - popup detail render untuk semua 33 item")

print("\nSEMUA TEST LULUS ✔")
