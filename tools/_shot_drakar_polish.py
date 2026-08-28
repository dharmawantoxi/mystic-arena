#!/usr/bin/env python3
"""Sheet polesan Drakar: renderer LAMA (dari commit dasar) vs LAMA + POLESAN.

Renderer asli Dipertahankan penuh sesuai masukan; polesan hanya:
  1. Bilah bawah kapak mendapat tepi putih 1 px (sama seperti bilah atas).
  2. Alur darah tipis di kedua bilah - menyala saat menyerang/skill.
Keduanya di kanvas 1x (tanpa zoom) di atas lantai arena.

Jalankan:  python3 tools/_shot_drakar_polish.py
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))
from bosses import level1

BASE_COMMIT = os.environ.get("DRAKAR_BEFORE_REF",
                             "c175e9c859792c900d6e722ac443df8713c095fb")


def load_old_namespace():
    try:
        src = subprocess.run(
            ["git", "-C", ROOT, "show", f"{BASE_COMMIT}:bosses/level1.py"],
            capture_output=True, check=True).stdout.decode("utf-8")
    except Exception as exc:
        print(f"[skip] renderer lama tidak tersedia ({exc})")
        return None
    start = src.index("class _NS_drakar")
    end = src.index("class _NS_abaddon")
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
        fh.write("import math\nimport pygame\n" + src[start:end])
        path = fh.name
    try:
        spec = importlib.util.spec_from_file_location("_drakar_before", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod._NS_drakar
    finally:
        os.unlink(path)


def probe(**kw):
    b = SimpleNamespace(boss_type="drakar", boss_class="mini", x=0.0, y=0.0,
                        direction=1, facing=1, pulse=1.25, timer=20,
                        attack_cooldown=46, active_skill=None,
                        active_skill_timer=0, target=None, _render_scale=1.0,
                        hurt_flash_timer=0, alive=True, radius=32)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def row(draw, with_atk=True):
    """Tiga pose 1x di atas lantai: idle, walk, attack."""
    s = pygame.Surface((560, 240))
    s.fill((24, 22, 34))
    for i in range(0, 560, 40):
        pygame.draw.line(s, (30, 27, 42), (i, 0), (i, 240))
        pygame.draw.line(s, (30, 27, 42), (0, i % 240), (560, i % 240))
    for i, pulse in enumerate((1.0, 2.6, 1.2)):
        cx = 100 + i * 180
        b = probe(pulse=pulse)
        if i == 2 and with_atk:
            b.timer = 25
            b._drk_attack_active = True
            b._drk_attack_progress = 0.5
            b._drk_previous_timer = 20
            b._drk_attack_dir = 1
            b._drk_attack_frame = 22
        draw(s, b, cx, 160)
    return s


old = load_old_namespace()
sheet = pygame.Surface((1160, 580))
sheet.fill((10, 10, 16))
f = pygame.font.Font(None, 30)
fs = pygame.font.Font(None, 22)
sheet.blit(f.render("RENDER LAMA (pilihan) - skala 1x:", True,
                    (235, 130, 130)), (20, 8))
if old is not None:
    sheet.blit(row(old.draw_drakar), (20, 40))
sheet.blit(f.render("LAMA + POLESAN (kapak: tepi putih bilah bawah + "
                    "alur darah saat menyerang) - skala 1x:", True,
                    (140, 200, 250)), (20, 295)
           )
sheet.blit(row(level1.draw_drakar), (20, 327))
sheet.blit(fs.render("kiri: idle | tengah: walk | kanan: attack - ukuran "
                     "piksel asli, tanpa zoom", True, (140, 140, 170)),
           (20, 552))
out = os.path.join(ROOT, "docs", "drakar_polish_preview.png")
pygame.image.save(sheet, out)
print("docs/drakar_polish_preview.png")
