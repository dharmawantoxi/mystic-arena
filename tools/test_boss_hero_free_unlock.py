"""Uji regresi: boss hero (mini/true) otomatis GRATIS di Hero Shop.

Aturan:
  - Kalahkan mini boss / true boss di match  -> dicatat.
  - Match MENANG (castle musuh hancur)       -> boss itu langsung masuk
    purchased_heroes tanpa memotong Hero Gold (tampil OWNED di shop).
  - Match KALAH                              -> tidak dibuka gratis
    (tetap harus dibeli dengan harga normal).
"""
import os
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MYSTIC_FORCE_TOUCH", "0")
os.environ["MYSTIC_SAVE_DIR"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

pygame.init()

import _core  # noqa: E402
from _core import Game  # noqa: E402
from _system import SaveManager  # noqa: E402


def _fresh_game():
    g = Game(pygame.display.set_mode(
        (_core.SCREEN_WIDTH, _core.SCREEN_HEIGHT)), level_number=1)
    for nm in ("level_intro", "boss_intro"):
        o = getattr(g, nm, None)
        if o is not None and hasattr(o, "handle_skip"):
            try:
                o.handle_skip(key=pygame.K_SPACE)
            except Exception:
                pass
    g.save_data['purchased_heroes'] = ['kaizen']
    g.save_data['unlocked_bosses'] = []
    g.purchased_heroes = g.save_data['purchased_heroes']
    g.unlocked_bosses = g.save_data['unlocked_bosses']
    g.save_data['meta_gold'] = 0
    return g


def _defeat_boss(g, boss_type):
    """Simulasi boss dikalahkan (lewat jalur di update loop)."""
    from bosses.base_boss import Boss
    lane_path = g.map_renderer.get_lane_path("mid")
    b = Boss(boss_type, lane_path)
    b.hp = 0
    b.alive = False
    b.defeated = True
    g.active_boss = b
    g.boss_death = None  # anggap animasi kematian boss sebelumnya selesai
    g.state = "playing"
    # Jalankan satu tick update supaya blok "BOSS DEFEATED" berjalan.
    g.update()
    assert g.active_boss is None, "boss defeated block tidak jalan"


def test_win_unlocks_free():
    g = _fresh_game()
    mini = list(g._mini_boss_schedule.values())[0]
    true_boss = g.level_config.get("true_boss")
    _defeat_boss(g, mini)
    assert mini in g.bosses_defeated_this_match
    assert mini not in g.purchased_heroes, "belum menang, tidak boleh owned"
    if true_boss:
        _defeat_boss(g, true_boss)

    gold_before = g.save_data['meta_gold']
    g.boss_death = None
    g.red_base.hp = 0
    g.red_base.alive = False
    g.state = "playing"
    g.update()
    assert g.state == "victory"
    assert mini in g.save_data['purchased_heroes'], "mini boss harus OWNED"
    if true_boss:
        assert true_boss in g.save_data['purchased_heroes'], \
            "true boss harus OWNED"
    assert g.save_data['meta_gold'] >= gold_before, "gold tidak boleh dipotong"
    assert mini in g.heroes_unlocked_this_match
    print(f"  [OK] win -> {g.heroes_unlocked_this_match} gratis")


def test_lose_does_not_unlock():
    g = _fresh_game()
    mini = list(g._mini_boss_schedule.values())[0]
    _defeat_boss(g, mini)
    g.boss_death = None
    g.blue_base.hp = 0
    g.blue_base.alive = False
    g.state = "playing"
    g.update()
    assert g.state == "defeat"
    assert mini not in g.save_data['purchased_heroes'], \
        "kalah -> boss tidak boleh gratis"
    assert mini in g.save_data['unlocked_bosses'], \
        "boss defeated tetap tercatat (bisa dibeli normal)"
    print("  [OK] lose -> tidak dibuka gratis")


if __name__ == "__main__":
    test_win_unlocks_free()
    test_lose_does_not_unlock()
    print("ALL PASSED")
