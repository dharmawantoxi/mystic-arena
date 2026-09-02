#!/usr/bin/env python3
"""Penjaga regresi: momen TEMPUR di mana karakter Gornak bisa tertutup cahaya.

Sebelum perbaikan, hit flash (lingkaran putih additive r~55, alpha 120)
menutupi ~84% badan pada SETIAP tick damage, dan pilar R (polygon alpha di
buffer scratch yang di-blit BLEND_RGB_ADD -> alpha diabaikan) menjadi
berkas putih jenuh selebar badan selama cast ultimate. Setelah perbaikan,
metrik "piksel putih di dalam bbox badan" harus tetap kecil (< 5%).

Panel:
  1. hit flash (on_hurt, k=1.0) - saat Gornak BARU kena damage
  2. hit flash k=0.5
  3. E Counterspell (kubah) progress 0.5
  4. E Counterspell progress 0.8
  5. R Mana Void aktivasi (progress 0.10)
  6. R Mana Void corong (progress 0.40)
  7. ImpactFX crit power besar di badan (t=0.02s)
  8. ImpactFX blade di badan (t=0.05s)

Semua panel: lane BOSS (draw_gornak tiap frame) dengan lapisan hidup aktif,
zoom 3x, karakter di tengah. Metrik: piksel putih (min(r,g,b)>=235) dalam
bbox badan, dan % area badan yang ketutup piksel sangat terang.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402
import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import heroes  # noqa: E402
from heroes import _ProbeEntity  # noqa: E402
from heroes import combat_feel as FEEL  # noqa: E402
from heroes import gornak_fx as F  # noqa: E402
from bosses.level1 import _NS_gornak as G  # noqa: E402

DT = 1.0 / 60.0
BG = (20, 14, 28)


def hero_at(x, y, **kw):
    h = _ProbeEntity("gornak", x, y)
    h.boss_type = "gornak"
    h.pulse = 1.2
    h.direction = h.facing = 1
    h.attack_cooldown = 38
    h.timer = 0
    h.range = 60
    h.speed = 1.6
    h.hp = h.max_hp = 800
    h.radius = 16
    h.skill_damage = 180
    h.skill_range = 180
    h.hurt_flash_timer = 0
    h.blink_from_x = h.blink_from_y = 0
    h.mana_void_x = h.mana_void_y = 0
    for k, v in kw.items():
        setattr(h, k, v)
    return h


def white_metrics(surf, body_rect):
    """Rasio piksel putih di dalam area badan (bukan seluruh sel)."""
    if body_rect.width <= 0:
        return 0, 0.0
    sub = surf.subsurface(body_rect)
    px = pygame.surfarray.array3d(sub).astype(np.int32)
    al = pygame.surfarray.array_alpha(sub)
    solid = al >= 90
    mn = px.min(axis=2)
    white = int(((mn >= 235) & solid).sum())
    tot = int(solid.sum())
    return white, (100.0 * white / max(1, tot))


def scene_hit_flash(k):
    """Karakter kena damage: hit_flash aktif di lapisan hidup."""
    size = 260
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2 + 26
    F.reset_all()
    h = hero_at(float(cx), float(cy))
    F.attach(h)
    d = F.director_for(h)
    d.on_hurt(0.2)
    d.hit_flash = 0.16 * k               # kendalikan langsung fase flash
    F.tick(0.0001)                        # 1 langkah kecil supaya partikel muncul
    d.hit_flash = 0.16 * k               # tick tidak boleh meluruhkan
    G.draw_gornak(surf, h, cx, cy)
    F.reset_all()
    return surf


def scene_skill(skill, timer):
    size = 300
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2 + 26
    F.reset_all()
    h = hero_at(float(cx), float(cy), active_skill=skill,
                active_skill_timer=timer)
    if skill == "r":
        h.target = _ProbeEntity("dummy", float(cx + 90), float(cy - 18))
        h.target.alive = True
    F.attach(h)
    # jalankan lapisan hidup sampai momen ini supaya SkillFX ikut
    steps = int((F.SKILL_DUR[skill] - timer) / 1.0)
    for _ in range(steps):
        F.tick(DT)
    G.draw_gornak(surf, h, cx, cy)
    F.reset_all()
    return surf


def scene_impact(t_age, crit=False, power=1.8):
    size = 260
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2 + 26
    F.reset_all()
    h = hero_at(float(cx), float(cy))
    F.attach(h)
    d = F.director_for(h)
    d.on_impact(cx, cy - 6, angle=0.3, power=power, crit=crit)
    for _ in range(int(t_age / DT)):
        F.tick(DT)
    G.draw_gornak(surf, h, cx, cy)
    F.reset_all()
    return surf


PANELS = [
    ("1. HIT FLASH k=1.0 (baru kena damage)", lambda: scene_hit_flash(1.0)),
    ("2. HIT FLASH k=0.5", lambda: scene_hit_flash(0.5)),
    ("3. E Counterspell prog~0.30", lambda: scene_skill("e", 42)),
    ("4. E Counterspell prog~0.70", lambda: scene_skill("e", 18)),
    ("5. R Mana Void aktivasi 0.10", lambda: scene_skill("r", 81)),
    ("6. R Mana Void corong 0.40", lambda: scene_skill("r", 54)),
    ("7. IMPACT crit power 1.8 t=0.03s", lambda: scene_impact(0.03, True)),
    ("8. IMPACT blade 1.8 t=0.05s", lambda: scene_impact(0.05, False)),
]

rows = []
for name, fn in PANELS:
    surf = fn()
    # bbox badan: estimasi dari alpha tinggi di sekitar pusat sel
    rect = surf.get_bounding_rect(min_alpha=120)
    w, pct = white_metrics(surf, rect)
    rows.append((name, surf, rect, w, pct))
    print("%-42s bbox=%-26s white px: %5d  (%.1f%% badan)" % (name, rect, w,
                                                              pct))

CW, CH = 320, 360
cols = 4
rows_n = (len(rows) + cols - 1) // cols
sheet = pygame.Surface((cols * CW + 20, rows_n * CH + 50))
sheet.fill(BG)
font = pygame.font.Font(None, 20)
sheet.blit(font.render("GORNAK - momen tempur: mencari efek yang menutupi "
                       "karakter dengan cahaya putih", True,
                       (232, 206, 250)), (12, 12))
for i, (name, surf, rect, w, pct) in enumerate(rows):
    x = 10 + (i % cols) * CW
    y = 44 + (i // cols) * CH
    pygame.draw.rect(sheet, (11, 10, 24), (x, y, CW - 8, CH - 8),
                     border_radius=6)
    pygame.draw.rect(sheet, (86, 52, 128), (x, y, CW - 8, CH - 8), 1,
                     border_radius=6)
    z = 3.2
    big = pygame.transform.scale(surf, (int(surf.get_width() * z),
                                        int(surf.get_height() * z)))
    # crop tengah
    cw2, ch2 = CW - 16, CH - 62
    crop = pygame.Surface((cw2, ch2))
    ox = (big.get_width() - cw2) // 2
    oy = (big.get_height() - ch2) // 2
    crop.blit(big, (0, 0), (ox, oy, cw2, ch2))
    sheet.blit(crop, (x + 8, y + 6))
    sheet.blit(font.render(name, True, (232, 216, 255)), (x + 8, y + CH - 48))
    sheet.blit(font.render("white px: %d (%.1f%% badan)" % (w, pct), True,
                           (255, 226, 150)), (x + 8, y + CH - 28))

out = os.path.join(ROOT, "docs", "gornak_combat_white.png")
pygame.image.save(sheet, out)
print(out)
