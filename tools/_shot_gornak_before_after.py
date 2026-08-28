#!/usr/bin/env python3
"""Sheet sebelum/sesudah untuk Gornak Procedural Masterwork.

Panel "sebelum" dirender dengan renderer lama yang diambil dari commit
`74c0a38` lewat `git show` - jadi sheet ini bisa dibangun ulang kapan pun
tanpa menyimpan salinan kode lama di repo. Kedua baris memakai FAKTOR ZOOM
yang sama persis, sehingga perbedaan ukuran (bukan cuma crop) terlihat.

Jalankan:  python3 tools/_shot_gornak_before_after.py
"""
import importlib.util
import os
import subprocess
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame
from types import SimpleNamespace

BASE_COMMIT = os.environ.get("GORNAK_BEFORE_REF", "74c0a38")

pygame.init()
pygame.display.set_mode((1, 1))
from bosses.level1 import _NS_gornak as NEW


def load_old_namespace():
    """Ambil _NS_gornak versi lama dari git, atau None kalau tidak ada."""
    try:
        src = subprocess.run(
            ["git", "-C", ROOT, "show", f"{BASE_COMMIT}:bosses/level1.py"],
            capture_output=True, check=True).stdout.decode("utf-8")
    except Exception as exc:                      # pragma: no cover
        print(f"[skip] renderer lama tidak tersedia ({exc})")
        return None
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
        fh.write(src)
        path = fh.name
    try:
        spec = importlib.util.spec_from_file_location("_gornak_before", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod._NS_gornak
    finally:
        os.unlink(path)


def probe(**kw):
    b = SimpleNamespace(boss_type="gornak", boss_class="mini", x=0.0, y=0.0,
                        direction=1, facing=1, pulse=0.0, timer=0,
                        attack_cooldown=38, active_skill=None,
                        active_skill_timer=0, target=None, _render_scale=1.0,
                        hurt_flash_timer=0, alive=True, radius=30, speed=1.2,
                        is_retreating=False)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def crop_render(NS, state, size=260):
    """Render 1x lalu crop ke bounding box + margin (ukurannya jujur)."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, int(size * 0.60)
    st = dict(state)
    atk = st.pop("atk", False)
    prog = st.pop("prog", 0.5)
    b = probe(**st)
    if atk:
        b._gnk_attack_active = True
        b._gnk_attack_progress = prog
    if st.get("active_skill") == "r":
        b.target = SimpleNamespace(x=float(cx + 70), y=float(cy - 26),
                                   alive=True)
    b.x, b.y = float(cx), float(cy)
    NS.draw_gornak(surf, b, cx, cy)
    r = surf.get_bounding_rect(min_alpha=1).inflate(28, 28).clip(
        surf.get_rect())
    out = surf.subsurface(r).copy()
    return out, r.h


CASES = [("idle", {"pulse": 1.25}),
         ("attack + slash", {"pulse": 1.0, "timer": 22, "atk": True}),
         ("R mana void", {"pulse": 1.15, "active_skill": "r",
                          "active_skill_timer": 44})]

old_ns = load_old_namespace()
if old_ns is None:
    sys.exit(1)

imgs = {}
for tag, NS in (("SEBELUM", old_ns), ("SESUDAH", NEW)):
    for label, st in CASES:
        imgs[(tag, label)] = crop_render(NS, dict(st))
maxh = max(h for _, h in imgs.values())
scale = min(2.2, 300 / maxh)          # SATU angka untuk semua panel

CW, CH = 400, 340
W, H = 3 * CW + 60, 2 * CH + 150
screen = pygame.Surface((W, H))
screen.fill((6, 7, 15))
ftitle = pygame.font.Font(None, 30)
fsmall = pygame.font.Font(None, 21)
screen.blit(ftitle.render(
    "GORNAK - sebelum vs sesudah (kedua baris memakai FAKTOR ZOOM SAMA, "
    "jadi ukuran aslinya terlihat)", True, (200, 168, 246)), (30, 18))

for row, tag in enumerate(("SEBELUM", "SESUDAH")):
    for col, (label, _) in enumerate(CASES):
        img, _ = imgs[(tag, label)]
        big = pygame.transform.scale(img, (int(img.get_width() * scale),
                                           int(img.get_height() * scale)))
        x = 30 + col * CW
        y = 64 + row * CH
        pygame.draw.rect(screen, (11, 10, 24), (x, y, CW - 12, CH - 16),
                         border_radius=8)
        pygame.draw.rect(screen, (86, 52, 128), (x, y, CW - 12, CH - 16), 1,
                         border_radius=8)
        screen.blit(big, (x + (CW - 12 - big.get_width()) // 2, y + 18))
        screen.blit(fsmall.render(f"{tag} · {label}", True, (232, 216, 255)),
                    (x + 12, y + CH - 40))

screen.blit(fsmall.render(
    "badan padat 87x53 px (W/H 0.61)   ->   115x121 px (W/H 1.05)   ·   "
    "rujukan keluarga: morgath 82x120, drakar 138x190, kaizen 75x83, "
    "grimjaw 74x79", True, (150, 128, 178)), (30, H - 30))

out = os.path.join(ROOT, "docs", "gornak_before_after.png")
pygame.image.save(screen, out)
print(out)
