#!/usr/bin/env python3
"""Sheet SEBELUM / SESUDAH arah tebasan basic attack Grimjaw.

Latar belakang
--------------
Basic attack Grimjaw sebelumnya terbaca sebagai ayunan DARI BAWAH KE
ATAS: sudut pedang justru membesar (-1.55 -> +1.35 rad) sehingga ujung
pedang lewat BAWAH badan dan NAIK di akhir ayunan, sementara crescent
api digambar penuh sejak awal dengan titik paling terang di ujung
ATAS-nya.  Sesudah perbaikan, pedang diangkat ke atas-belakang kepala
lalu menebas TURUN ke depan-bawah dan crescent api mengikuti jalur
tersebut (kepala = posisi pedang saat ini, ekor memudar ke atas).

Baris "SEBELUM" dirender dari renderer LAMA yang diambil langsung dari
git (`git show <ref>:heroes/_bundle.py`), jadi sheet ini bisa dibangun
ulang kapan pun tanpa menyimpan salinan kode lama di repo.

Titik hijau di setiap panel menandai UJUNG PEDANG pada frame itu -
urutkan titik-titik itu dari kiri ke kanan untuk melihat arah ayunan.

Jalankan:  python3 tools/_shot_grimjaw_swing_ab.py
"""
import importlib.util
import os
import subprocess
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame                                             # noqa: E402
from types import SimpleNamespace                         # noqa: E402

# Commit dasar cabang kerja - renderer Grimjaw SEBELUM perbaikan arah tebasan.
BASE_REF = os.environ.get("GRIMJAW_BEFORE_REF",
                          "dc4e8313a8742a636c066c8f980d289d40cc927c")

pygame.init()
pygame.display.set_mode((1, 1))
from heroes._bundle import _NS_grimjaw as NEW              # noqa: E402


def load_old_namespace():
    """Ambil _NS_grimjaw versi lama dari git, atau None kalau tidak ada."""
    try:
        src = subprocess.run(
            ["git", "-C", ROOT, "show", f"{BASE_REF}:heroes/_bundle.py"],
            capture_output=True, check=True).stdout.decode("utf-8")
    except Exception as exc:                               # pragma: no cover
        print(f"[skip] renderer lama tidak tersedia ({exc})")
        return None
    fh = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False)
    fh.write(src)
    fh.close()
    try:
        spec = importlib.util.spec_from_file_location(
            "_bundle_before", fh.name)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod._NS_grimjaw
    finally:
        os.unlink(fh.name)


def probe():
    return SimpleNamespace(
        x=0.0, y=0.0, pulse=0.0, direction=1, facing=1, timer=0,
        attack_cooldown=40, active_skill=None, active_skill_timer=0,
        target=None, _portrait_hd=False, alive=True,
        _gj_attack_active=True, _gj_attack_progress=0.0,
        _gj_crit_active=False)


FRAMES = [0.15, 0.25, 0.35, 0.45, 0.55, 0.62, 0.72, 0.85]
CW, CH = 176, 196
CANVAS = CW


def render_cell(NS, progress):
    """Satu frame basic attack + penanda ujung pedang."""
    hero = probe()
    hero._gj_attack_progress = progress
    surf = pygame.Surface((CANVAS, CANVAS), pygame.SRCALPHA)
    cx, cy = CANVAS // 2 - 8, CH // 2 + 16
    NS._draw_grimjaw_attack(surf, hero, cx, cy)
    tip = NS._blade_tip_local(0.0, "attack", progress)
    pygame.draw.circle(surf, (60, 255, 120), (cx + tip[0], cy + tip[1]), 4)
    pygame.draw.circle(surf, (10, 40, 20), (cx + tip[0], cy + tip[1]), 4, 1)
    # Garis setinggi pusat badan: acuan "atas vs bawah".
    pygame.draw.line(surf, (90, 110, 150), (0, cy), (CANVAS, cy), 1)
    return surf


def main():
    old_ns = load_old_namespace()
    if old_ns is None:
        return 1
    if not hasattr(old_ns, "_blade_tip_local"):            # pragma: no cover
        print("[skip] renderer lama tidak punya _blade_tip_local")
        return 1

    pad = 8
    W = pad + len(FRAMES) * (CW + pad)
    H = 96 + 2 * (CH + pad) + 46
    screen = pygame.Surface((W, H))
    screen.fill((10, 11, 20))
    ft = pygame.font.Font(None, 30)
    fs = pygame.font.Font(None, 20)
    fxs = pygame.font.Font(None, 17)

    screen.blit(ft.render(
        "GRIMJAW - arah tebasan basic attack (titik hijau = ujung pedang)",
        True, (255, 196, 120)), (pad, 14))
    screen.blit(fxs.render(
        "SEBELUM: pedang lewat BAWAH dan ujungnya NAIK di akhir ayunan, "
        "crescent api paling terang di ATAS  ->  terbaca bawah ke atas",
        True, (232, 140, 140)), (pad, 48))
    screen.blit(fxs.render(
        "SESUDAH: pedang diangkat ke atas-belakang kepala lalu menebas "
        "TURUN ke depan-bawah  ->  terbaca atas ke bawah",
        True, (150, 235, 160)), (pad, 70))

    for row, (tag, NS, color) in enumerate(
            (("SEBELUM", old_ns, (170, 90, 90)),
             ("SESUDAH", NEW, (80, 150, 90)))):
        for col, progress in enumerate(FRAMES):
            x = pad + col * (CW + pad)
            y = 96 + row * (CH + pad)
            pygame.draw.rect(screen, (18, 19, 30),
                             (x, y, CW, CH), border_radius=6)
            pygame.draw.rect(screen, color, (x, y, CW, CH), 1,
                             border_radius=6)
            cell = render_cell(NS, progress)
            screen.blit(cell, (x + (CW - CANVAS) // 2, y + 22))
            screen.blit(fs.render(f"p={progress:.2f}", True, (225, 225, 235)),
                        (x + 10, y + 4))
        screen.blit(fs.render(tag, True, color),
                    (pad, 96 + row * (CH + pad) + CH // 2))

    screen.blit(fxs.render(
        "garis biru tipis = setinggi pusat badan (acuan atas/bawah)",
        True, (130, 140, 175)), (pad, H - 30))

    out = os.path.join(ROOT, "docs", "grimjaw_swing_before_after.png")
    pygame.image.save(screen, out)
    print(out, screen.get_size())
    return 0


if __name__ == "__main__":
    sys.exit(main())
