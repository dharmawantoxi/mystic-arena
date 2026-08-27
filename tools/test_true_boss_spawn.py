"""Uji regresi: true boss harus spawn setelah 6 tower merah hancur.

Bug yang pernah terjadi: syarat ">= 6 tower merah hancur" dihitung
sebagai `jumlah_awal_merah - jumlah_hidup_sekarang`. Itu rusak karena:
  1. tower yang mati DIBUANG dari `Game.towers` tiap akhir frame,
     sehingga kill lama tidak terhitung;
  2. AI terus membangun tower merah baru setelah snapshot awal,
     sehingga selisihnya bisa negatif.
Akibatnya walau pemain menghancurkan 6+ tower dan wave >= 5, true boss
tidak pernah muncul.

Sekarang `Game.red_towers_destroyed` dinaikkan dari EVENT kematian
tower merah. Test ini mensimulasikan skenario yang dulu rusak:
AI membangun tower SETELAH game mulai, pemain menghancurkannya 6,
dan true boss tetap harus spawn di wave >= 5 (serta TIDAK spawn di
wave < 5).
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MYSTIC_FORCE_TOUCH", "0")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

pygame.init()

import _core  # noqa: E402,F401
from _core import Game  # noqa: E402
from _entity import Tower  # noqa: E402


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
    return g


def _spawn_and_kill_red_towers(g, n):
    """Simulasikan AI membangun n tower merah lalu pemain menghancurkannya."""
    for i in range(n):
        t = Tower(900 + i * 10, 200 + i * 10, "red")
        g.towers.append(t)
    g.update()  # AI "melihat" tower baru (snapshot lama tidak dipakai lagi)
    for t in [t for t in g.towers if t.team == "red"]:
        t.hp = 0
        t.alive = False
    g.update()  # loop reward menaikkan counter; tower mati dibuang


def test_counter_naik_dan_boss_spawn():
    g = _fresh_game()
    g.wave_number = 5
    _spawn_and_kill_red_towers(g, 6)
    assert g.red_towers_destroyed >= 6, \
        f"counter {g.red_towers_destroyed} != 6"
    # Boss spawn di frame berikutnya (check berjalan sebelum loop reward)
    for _ in range(3):
        g.update()
    assert g.true_boss_spawned, "true_boss_spawned tetap False"
    assert g.active_boss is not None, "active_boss None walau syarat terpenuhi"
    assert g.active_boss.boss_type == g.level_config.get("true_boss"), \
        "boss yang spawn bukan true boss level ini"


def test_tidak_spawn_sebelum_wave_5():
    g = _fresh_game()
    g.wave_number = 4
    _spawn_and_kill_red_towers(g, 6)
    for _ in range(3):
        g.update()
    assert not g.true_boss_spawned, "true boss spawn padahal wave < 5"
    # Begitu wave naik, boss harus muncul tanpa perlu kill tambahan
    g.wave_number = 5
    for _ in range(3):
        g.update()
    assert g.true_boss_spawned, "true boss tidak spawn setelah wave >= 5"


def test_kurang_dari_6_tidak_spawn():
    g = _fresh_game()
    g.wave_number = 10
    _spawn_and_kill_red_towers(g, 5)
    for _ in range(3):
        g.update()
    assert not g.true_boss_spawned, "true boss spawn padahal kill baru 5"


def main():
    test_counter_naik_dan_boss_spawn()
    test_tidak_spawn_sebelum_wave_5()
    test_kurang_dari_6_tidak_spawn()
    print("HASIL: LULUS. True boss spawn sesuai syarat (6 tower & wave 5+).")


if __name__ == "__main__":
    main()
