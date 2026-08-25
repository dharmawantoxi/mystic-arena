"""Uji regresi: sell tower tidak boleh crash.

Kasus yang dulunya membuat game force-close:
  1. Tower hancur (alive=False) saat popup masih terbuka -> di akhir
     frame `Game.update()` membuang tower dari `g.towers`, lalu pemain
     menekan SELL -> `g.towers.remove(tower)` melempar ValueError.
  2. (Terkait) Popup tidak otomatis tertutup saat towernya mati,
     sehingga tombol SELL/UPGRADE menyentuh tower "hantu".

Test ini memastikan:
  - sell setelah tower mati TIDAK crash (popup ditutup dengan aman);
  - sell normal tetap berfungsi (gold bertambah, tower hilang, slot
    build kosong lagi);
  - popup otomatis tertutup begitu tower yang dipilih mati.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

import _core  # noqa: E402,F401
from game import Game  # noqa: E402


def _fresh_game():
    g = Game(pygame.display.set_mode((1280, 720)), level_number=1)
    g.level_intro = None
    g.boss_intro = None
    for _ in range(200):
        g.update()
    return g


def _free_slot(g):
    return next(s for s in g.build_slots_blue if not s['taken'])


def test_sell_after_tower_destroyed():
    g = _fresh_game()
    slot = _free_slot(g)
    g.build_popup_slot = slot
    g.gold = 10**9
    g.try_build_tower("archer")
    tw = g.towers[-1]
    g.open_popup(tw, "tower")

    # Tower hancur saat popup terbuka, lalu filter akhir frame jalan
    tw.hp = 0
    tw.alive = False
    g.towers = [t for t in g.towers if t.alive]
    assert tw not in g.towers

    # SELL tidak boleh crash
    g.input._try_sell_tower()
    assert g.selected_tower is None
    assert g.popup_target is None
    print("  ✔ sell setelah tower mati tidak crash")


def test_normal_sell_works():
    g = _fresh_game()
    slot = _free_slot(g)
    g.build_popup_slot = slot
    g.gold = 1000
    g.try_build_tower("archer")
    tw = g.towers[-1]
    g.open_popup(tw, "tower")
    assert slot['taken'] is True

    before_gold = g.gold
    g.input._try_sell_tower()

    assert tw not in g.towers          # tower hilang
    assert slot['taken'] is False      # slot kosong lagi
    assert g.gold > before_gold        # refund masuk
    assert g.selected_tower is None
    assert g.popup_target is None
    print("  ✔ sell normal berfungsi (refund + slot kosong)")


def test_popup_auto_close_on_death():
    g = _fresh_game()
    slot = _free_slot(g)
    g.build_popup_slot = slot
    g.gold = 1000
    g.try_build_tower("archer")
    tw = g.towers[-1]
    g.open_popup(tw, "tower")

    tw.hp = 0
    tw.alive = False
    g.update()  # filter + auto-close popup

    assert g.popup_target is None
    assert g.selected_tower is None
    print("  ✔ popup otomatis tertutup saat tower mati")


def main():
    print("test_sell_tower.py")
    test_sell_after_tower_destroyed()
    test_normal_sell_works()
    test_popup_auto_close_on_death()
    print("\nHASIL: LULUS. Sell tower tidak crash.")


if __name__ == "__main__":
    main()
