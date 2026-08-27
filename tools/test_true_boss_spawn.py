"""Uji regresi: true boss spawn begitu 6 tower merah hancur (tanpa syarat wave).

Sejarah:
  1. Bug lama: syarat kill dihitung sebagai selisih jumlah tower hidup,
     rusak karena tower mati dibuang dari list dan AI terus membangun.
  2. Dulu ada syarat tambahan wave >= 5; dihapus sesuai permintaan -
     sekarang CUKUP 6 tower merah hancur, berapa pun wave-nya.

Test ini memastikan:
  - 6 tower merah hancur di wave awal (bahkan sebelum wave 5) ->
    true boss langsung spawn;
  - baru 5 tower hancur -> true boss belum spawn;
  - counter `red_towers_destroyed` menghitung event kematian.
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
    g.update()
    for t in [t for t in g.towers if t.team == "red"]:
        t.hp = 0
        t.alive = False
    g.update()  # loop reward menaikkan counter; tower mati dibuang


def test_6_kill_spawn_di_wave_awal():
    g = _fresh_game()
    # JANGAN set wave_number: syaratnya sekarang memang tidak ada wave.
    assert g.wave_number < 5, "prekondisi: masih wave awal"
    _spawn_and_kill_red_towers(g, 6)
    assert g.red_towers_destroyed >= 6, \
        f"counter {g.red_towers_destroyed} != 6"
    # Boss spawn di frame berikutnya (check berjalan sebelum loop reward)
    for _ in range(3):
        g.update()
    assert g.true_boss_spawned, \
        "true_boss_spawned tetap False walau 6 tower hancur"
    assert g.active_boss is not None, "active_boss None walau syarat terpenuhi"
    assert g.active_boss.boss_type == g.level_config.get("true_boss"), \
        "boss yang spawn bukan true boss level ini"


def test_kurang_dari_6_tidak_spawn():
    g = _fresh_game()
    _spawn_and_kill_red_towers(g, 5)
    for _ in range(3):
        g.update()
    assert not g.true_boss_spawned, "true boss spawn padahal kill baru 5"
    # Kill ke-6 -> baru spawn
    t = Tower(950, 250, "red")
    g.towers.append(t)
    g.update()
    t.hp = 0
    t.alive = False
    for _ in range(3):
        g.update()
    assert g.true_boss_spawned, "true boss tidak spawn setelah kill ke-6"


def main():
    test_6_kill_spawn_di_wave_awal()
    test_kurang_dari_6_tidak_spawn()
    print("HASIL: LULUS. True boss spawn cukup dengan 6 tower merah hancur.")


if __name__ == "__main__":
    main()
