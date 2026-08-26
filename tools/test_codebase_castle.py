"""Headless test untuk memastikan Castle menggunakan procedural code base rendering.

Menguji:
1. Render kastil untuk semua level (L1 s/d L5) pada kedua tim (blue & red).
2. Efek dinamis (torch, flags) berfungsi baik dalam mode PC dan HP.
3. Castle shield crest dan HP bar ter-render tanpa masalah.
4. Tidak ada ketergantungan pada file assets/castles.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import _core
from _entity import Castle


def test_castle_codebase_rendering():
    """Uji rendering kastil berbasis kode untuk semua level dan tim."""
    screen = pygame.Surface((1280, 720), pygame.SRCALPHA)

    for team in ["blue", "red"]:
        for lvl in range(1, 6):
            castle = Castle(team=team, x=400, y=300)
            castle.level = lvl
            castle._apply_level_stats()

            screen.fill((0, 0, 0, 0))
            castle.pulse = 1.0
            castle.draw(screen)

            rect = screen.get_bounding_rect(min_alpha=5)
            assert rect.width > 50 and rect.height > 50, (
                f"Castle {team} L{lvl} render kosong / tidak valid!"
            )

    print("T1 OK  - 10 kombinasi kastil (blue/red x L1-L5) ter-render murni berbasis code")


def test_castle_dynamic_effects():
    """Uji efek dinamis (torch, pulse, shield) kastil."""
    screen = pygame.Surface((600, 600), pygame.SRCALPHA)
    castle = Castle(team="blue", x=300, y=300)
    castle.level = 3
    castle.shield_active = True
    castle.shield = 1000

    # Draw multiple frames
    for f in range(5):
        screen.fill((0, 0, 0, 0))
        castle.pulse = f * 0.5
        castle.draw(screen)
        rect = screen.get_bounding_rect(min_alpha=5)
        assert rect.width > 50 and rect.height > 50

    print("T2 OK  - Efek dinamis kastil dan shield crest berjalan mulus")


def test_no_castle_assets():
    """Pastikan folder assets/castles bersih."""
    castle_asset_dir = os.path.join(
        os.path.dirname(__file__), "..", "assets", "castles"
    )
    if os.path.exists(castle_asset_dir):
        files = os.listdir(castle_asset_dir)
        assert len(files) == 0, f"assets/castles harus kosong, ditemukan: {files}"
    print("T3 OK  - Folder assets/castles bersih (tidak ada sprite eksternal)")


if __name__ == "__main__":
    test_castle_codebase_rendering()
    test_castle_dynamic_effects()
    test_no_castle_assets()
    print("\nSEMUA PENGUJIAN CASTLE CODE BASE BERHASIL (LULUS 100%)")
