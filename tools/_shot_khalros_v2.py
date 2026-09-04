#!/usr/bin/env python3
"""Dump PNG referensi untuk renderer KHALROS v2 (dokumentasi).

Dipakai saat menulis `docs/KHALROS_V2_RENDERER.md` dan untuk mata-review
cepat. Tidak ada assertion - kalau ada yang janggal, perbaiki renderer lalu
jalankan ulang.

    python tools/_shot_khalros_v2.py                 # semua sheet
    python tools/_shot_khalros_v2.py poses           # satu sheet saja
    HALFTONE=1 python tools/_shot_khalros_v2.py      # cek palet 8x8
    NO_LIGHT=1 python tools/_shot_khalros_v2.py      # band sebelum lighting

Semua gambar dirender dari kode yang sama dengan game (jalur `draw_khalros`
untuk sheet dunia, `_draw_khalros_body_raw` untuk strip pose) supaya tidak
mungkin ada "renderer dokumen" yang diam-diam lebih bagus.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pygame  # noqa: E402
from types import SimpleNamespace  # noqa: E402

import bosses.level2 as L2  # noqa: E402

NS = L2._NS_khalros
DOCS = os.path.join(_ROOT, "docs")
HALFTONE = os.environ.get("HALFTONE") == "1"
NO_LIGHT = os.environ.get("NO_LIGHT") == "1"


def probe(**kw):
    """Boss dummy dengan semua atribut yang dibaca renderer."""
    b = SimpleNamespace(boss_type="khalros", boss_class="mini", x=0.0, y=0.0,
                        direction=1, facing=1, pulse=1.0, timer=0,
                        attack_cooldown=45, active_skill=None,
                        active_skill_timer=0, target=None, _render_scale=1.0,
                        hurt_flash_timer=0, alive=True, radius=36,
                        hp=7800, max_hp=7800, speed=1.0)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def world_cell(boss, size=230, anchor=None, bg=(24, 21, 28, 255)):
    """Render SATU kasus lewat jalur dunia (`draw_khalros`)."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    s.fill(bg)
    cx, cy = anchor or (size // 2, size // 2 + 6)
    L2.draw_khalros(s, boss, cx, cy)
    return s


def body_cell(action, phase, ap=0.0, facing=1, size=230, zoom=2,
              bg=(30, 27, 34, 255)):
    """Rig via `_draw_khalros_body` (outline + lighting asli) lalu di-zoom.

    ``NO_LIGHT=1`` melepas pass cahaya supaya band ramp palet bisa dinilai
    apa adanya - sama seperti prosedur review razak/gorath.
    """
    raw = pygame.Surface((size, size), pygame.SRCALPHA)
    lit = L2._lighting
    if NO_LIGHT:
        L2._lighting = None
    try:
        NS._draw_khalros_body(raw, size / 2, size / 2 + 6, facing, phase,
                              action, ap)
    finally:
        L2._lighting = lit
    surf = pygame.transform.scale(
        raw, (int(size * zoom), int(size * zoom))) if zoom != 1 else raw
    out = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    out.fill(bg)
    out.blit(surf, (0, 0))
    return out


def grid(cells, cols, titles=None, pad=6, tcol=(255, 236, 150)):
    """Susun sel jadi satu lembar + label kecil di kiri-atas tiap sel."""
    if not cells:
        return None
    w, h = cells[0].get_size()
    rows = (len(cells) + cols - 1) // cols
    th = 14 if titles else 0
    out = pygame.Surface((cols * (w + pad) - pad,
                          rows * (h + th + pad) - pad + th), pygame.SRCALPHA)
    out.fill((12, 11, 15, 255))
    for i, c in enumerate(cells):
        r, k = divmod(i, cols)
        x = k * (w + pad)
        y = th + r * (h + th + pad)
        if titles:
            pygame.draw.line(out, tcol, (x + 2, y - 5),
                             (x + 2 + len(titles[i]) * 6, y - 5), 3)
        out.blit(c, (x, y))
    return out


def save(surf, name):
    path = os.path.join(DOCS, name)
    pygame.image.save(surf, path)
    print("tulis %s  %dx%d" % (path, surf.get_width(), surf.get_height()))


def sheet_poses():
    cases = [("idle-a", "idle", 1.2, 0.0), ("idle-b", "idle", 3.9, 0.0),
             ("walk-a", "walk", 1.5, 0.0), ("walk-b", "walk", 3.1, 0.0),
             ("walk-c", "walk", 4.7, 0.0), ("cast", "cast", 2.0, 0.0),
             ("charge", "charge", 2.0, 0.5), ("back", "idle", 1.2, 0.0)]
    cells, titles = [], []
    for i, (t, a, ph, ap) in enumerate(cases):
        f = -1 if t == "back" else 1
        cells.append(body_cell(a, ph, ap, facing=f))
        titles.append(t)
    return grid(cells, 4, titles)


def sheet_attack():
    prog = (0.0, 0.09, 0.16, 0.30, 0.40, 0.48, 0.54, 0.62, 0.72, 0.84, 1.0)
    cells, titles = [], []
    for p in prog:
        cells.append(body_cell("attack", 1.0 + p * 2.6, p))
        titles.append("%.2f" % p)
    return grid(cells, 4, titles)


def sheet_world():
    cases = [
        ("idle", dict()),
        ("hurt", dict(hurt_flash_timer=7)),
        ("skill-q", dict(active_skill="q", active_skill_timer=40,
                         target=SimpleNamespace(x=58.0, y=6.0, alive=True))),
        ("skill-w", dict(active_skill="w", active_skill_timer=46)),
        ("skill-e", dict(active_skill="e", active_skill_timer=30)),
        ("skill-r", dict(active_skill="r", active_skill_timer=56)),
        ("walk", dict(pulse=2.6, _khal_last_x=-7.0, _khal_last_y=0.0)),
        ("attack", dict(_khal_attack_active=True, _khal_attack_frame=12,
                        timer=32, _khal_prev_timer=45)),
    ]
    cells, titles = [], []
    for t, kw in cases:
        cells.append(world_cell(probe(**kw), size=200))
        titles.append(t)
    return grid(cells, 4, titles)


def sheet_halftone():
    """Cek 8x8: 64 pose/phase berjajar - palet & rim-light harus terbaca."""
    cells = []
    for r in range(8):
        for c in range(8):
            act = ("idle", "walk", "attack", "cast")[c % 4]
            ph = 0.8 + r * 0.55 + c * 0.21
            ap = ((c // 2) % 4) / 4.0
            cells.append(body_cell(act, ph, ap, facing=1 if r % 2 else -1,
                                   size=120, zoom=1))
    return grid(cells, 8)


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    want = sys.argv[1] if len(sys.argv) > 1 else "all"
    todo = {
        "poses": ("khalros_v2_poses.png", sheet_poses),
        "attack": ("khalros_v2_attack_strip.png", sheet_attack),
        "world": ("khalros_v2_skills.png", sheet_world),
        "halftone": ("khalros_v2_halftone.png", sheet_halftone),
    }
    picked = (list(todo.items()) if want == "all"
              else [(k, todo[k]) for k in want.split(",")])
    for key, (name, fn) in picked:
        img = fn()
        if img is not None:
            save(img, name)


if __name__ == "__main__":
    main()
