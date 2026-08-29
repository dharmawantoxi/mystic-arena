"""E2E: alur nyata Game.handle_click -> Item Forge -> popup detail item.

Menguji jalur yang dipakai pemain sungguhan (desktop & sentuhan Android,
yang sama-sama berakhir di game.handle_click(pos, button)).
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
import _core  # noqa: E402
from _core import Game  # noqa: E402

pygame.init()
screen = pygame.display.set_mode((_core.SCREEN_WIDTH,
                                  _core.SCREEN_HEIGHT))
g = Game(screen, level_number=1)
# main.py memasang referensi game global ini; panel hero memakainya
# untuk mendaftarkan slot item (hero_item_slot_N).
import __main__
__main__.game_instance = g

# Lewati cinematic level intro (pemain sungguhan juga melewatinya
# dengan satu ketukan sebelum bisa menyentuh UI lain).
g.level_intro = None

# ── 1. Summon starter hero (kaizen auto-grant) ──────────────────────
assert "kaizen" in g.purchased_heroes
g.gold = 20000
g.try_buy_hero("kaizen")
hero = g.heroes[0]
assert hero is not None and hero.alive

# ── 2. Buka Item Forge & gambar 1 frame ─────────────────────────────
g.item_shop_open = True
g.draw()
assert "itemshop_card_dead_edge" in g.ui_buttons, "kartu harus terdaftar"

# ── 3. Ketuk kartu Dead Edge lewat jalur handle_click nyata ─────────
rect = g.ui_buttons["itemshop_card_dead_edge"]
g.handle_click((rect.x + 60, rect.y + 60), 1)
assert g.itemshop_inspect_item == "dead_edge", "ketuk kartu = popup"

# ── 4. Popup modal menggambar dengan tombol X ───────────────────────
g.draw()
assert "itemshop_detail_close" in g.ui_buttons
assert "itemshop_detail_rect" in dir(g)

# ── 5. Tombol X popup menutup detail, toko tetap ────────────────────
crect = g.ui_buttons["itemshop_detail_close"]
g.handle_click((crect.centerx, crect.centery), 1)
assert g.itemshop_inspect_item is None and g.item_shop_open

# ── 6. Beli lewat tombol BUY masih jalan (kartu tidak mencuri klik) ─
g.draw()
buy = g.ui_buttons["itemshop_buy_dead_edge"]
g.handle_click((buy.centerx, buy.centery), 1)
assert hero.items.has("dead_edge"), "BUY harus tetap berfungsi"
g.item_shop_open = False

# ── 7. Dari panel hero: ketuk slot terisi = popup info lengkap ─────
g.selected_hero = hero
hero.selected = True
g.draw()
assert "hero_item_slot_0" in g.ui_buttons
slot = g.ui_buttons["hero_item_slot_0"]
g.handle_click((slot.centerx, slot.centery), 1)
assert g.item_shop_open, "ketuk slot terisi membuka Item Forge"
assert g.itemshop_inspect_item == "dead_edge", \
    "popup detail langsung menampilkan item yang dipegang"

# ── 8. Tutup detail lalu toko lewat X toko ──────────────────────────
g.draw()
close = g.ui_buttons["itemshop_close"]
g.handle_click((close.centerx, close.centery), 1)
assert not g.item_shop_open and g.itemshop_inspect_item is None

print("E2E ITEM FORGE DETAIL LULUS ✔")
