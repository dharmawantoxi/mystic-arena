#!/usr/bin/env python3
"""Sheet v4 untuk Gornak Procedural Rig "SPELLBREAKER".

Menghasilkan:
  - docs/gornak_v4_before_after.png  (v3 dari git HEAD vs v4, zoom sama)
  - docs/gornak_v4_skills.png        (attack slash + Q/W/E/R jalur boss)
  - docs/gornak_v4_ingame.png        (komposit lane: gornak + keluarga hero)

Panel "sebelum" dirender dengan renderer v3 yang diambil dari commit
HEAD lewat `git show`, jadi sheet bisa dibangun ulang kapan pun tanpa
menyimpan salinan kode lama di repo.

Jalankan:  python3 tools/_shot_gornak_v4.py
"""
import importlib.util
import math
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

BASE_COMMIT = os.environ.get("GORNAK_V3_REF", "HEAD")

pygame.init()
pygame.display.set_mode((1, 1))
from bosses.level1 import _NS_gornak as NEW

ACCENT = (190, 232, 160)
SUB = (140, 150, 130)
NOTE = (120, 130, 112)
PANEL = (12, 14, 12)
PANEL_EDGE = (74, 110, 66)
BG = (8, 10, 9)

font_title = pygame.font.Font(None, 44)
font_label = pygame.font.Font(None, 26)
font_small = pygame.font.Font(None, 19)


def load_old_namespace():
    """Ambil _NS_gornak v3 dari git, atau None kalau tidak ada."""
    try:
        src = subprocess.run(
            ["git", "-C", ROOT, "show", f"{BASE_COMMIT}:bosses/level1.py"],
            capture_output=True, check=True).stdout.decode("utf-8")
    except Exception as exc:                      # pragma: no cover
        print(f"[skip] renderer v3 tidak tersedia ({exc})")
        return None
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
        fh.write(src)
        path = fh.name
    try:
        spec = importlib.util.spec_from_file_location("_gornak_v3", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod._NS_gornak
    finally:
        os.unlink(path)


def probe(cx=0.0, cy=0.0, **kw):
    b = SimpleNamespace(boss_type="gornak", boss_class="mini", x=float(cx),
                        y=float(cy), direction=1, facing=1, pulse=0.0,
                        timer=0, attack_cooldown=38, active_skill=None,
                        active_skill_timer=0, target=None, _render_scale=1.0,
                        hurt_flash_timer=0, alive=True, radius=30, speed=1.2)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def crop_render(NS, state, size=300):
    """Render 1x lalu crop ke bounding box + margin (ukurannya jujur)."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, int(size * 0.60)
    st = dict(state)
    atk = st.pop("atk", False)
    prog = st.pop("prog", 0.5)
    b = probe(cx, cy, **st)
    if atk:
        b._gnk_attack_active = True
        b._gnk_attack_progress = prog
    if st.get("active_skill") in ("q", "r"):
        b.target = SimpleNamespace(x=float(cx + 80), y=float(cy - 20),
                                   alive=True)
    NS.draw_gornak(surf, b, cx, cy)
    r = surf.get_bounding_rect(min_alpha=1).inflate(26, 26).clip(
        surf.get_rect())
    return surf.subsurface(r).copy(), r.h


def scale2x(surf, zoom=2.0):
    return pygame.transform.scale(
        surf, (max(1, int(surf.get_width() * zoom)),
               max(1, int(surf.get_height() * zoom))))


# ══════════════════════════════════════════════════════════════════
# Sheet 1 - sebelum (v3) / sesudah (v4), zoom identik
# ══════════════════════════════════════════════════════════════════
OLD = load_old_namespace()
W, H = 1280, 760
screen = pygame.Surface((W, H))
screen.fill(BG)
screen.blit(font_title.render(
    "GORNAK — REWRITE v4 “SPELLBREAKER” (kiri: v3 lama, kanan: v4)",
    True, ACCENT), (34, 16))
screen.blit(font_small.render(
    "v3: kulit sawo + mohawk + jenggot kepang + sirklet + dua pedang "
    "panjang + 5 lapis aksesori  ·  v4: ork hijau, mata menyala, SATU "
    "cleaver + belati, tiga titik fokus, tiga nilai per bidang",
    True, SUB), (36, 60))

if OLD is not None:
    CASES = [("idle", {"pulse": 1.25}),
             ("attack", {"pulse": 1.0, "atk": True, "prog": 0.52}),
             ("E counterspell", {"pulse": 1.2, "active_skill": "e",
                                 "active_skill_timer": 40}),
             ("R mana void", {"pulse": 1.15, "active_skill": "r",
                              "active_skill_timer": 44})]
    col_w = 620
    for i, (label, state) in enumerate(CASES):
        x = 30 + (i % 2) * (col_w + 16)
        y = 96 + (i // 2) * 316
        for j, (NS, tag, edge) in enumerate(((OLD, "v3", (120, 74, 74)),
                                              (NEW, "v4", (110, 170, 90)))):
            px = x + j * (col_w // 2 + 8)
            rect = pygame.Rect(px, y, col_w // 2 - 8, 292)
            pygame.draw.rect(screen, PANEL, rect, border_radius=10)
            pygame.draw.rect(screen, edge, rect, 2, border_radius=10)
            img, h = crop_render(NS, state)
            img = scale2x(img, 1.6)
            screen.blit(img, (rect.x + (rect.width - img.get_width()) // 2,
                              rect.y + 26))
            screen.blit(font_label.render(f"{tag} · {label}", True,
                                          (226, 232, 220)),
                        (rect.x + 12, rect.y + 6))

    out = os.path.join(ROOT, "docs", "gornak_v4_before_after.png")
    pygame.image.save(screen, out)
    print(out)

# ══════════════════════════════════════════════════════════════════
# Sheet 2 - skill FX v4 (jalur boss, 1x + zoom)
# ══════════════════════════════════════════════════════════════════
SW, SH = 1280, 700
sheet = pygame.Surface((SW, SH))
sheet.fill(BG)
sheet.blit(font_title.render("GORNAK v4 — SKILL FX (world-space)",
                             True, ACCENT), (34, 16))
sheet.blit(font_small.render(
    "Attack slash dari trail ujung cleaver · Q telegraph di ujung bilah "
    "→ bolt kristal · W implosion · E ring 100 px · R seal 180 px di caster",
    True, SUB), (36, 58))

SK = [("ATTACK", {"pulse": 1.0, "atk": True, "prog": 0.50}),
      ("Q MANA BREAK", {"pulse": 1.3, "active_skill": "q",
                        "active_skill_timer": 14}),
      ("W BLINK", {"pulse": 1.3, "active_skill": "w",
                   "active_skill_timer": 6}),
      ("E COUNTERSPELL", {"pulse": 1.3, "active_skill": "e",
                          "active_skill_timer": 40}),
      ("R MANA VOID", {"pulse": 1.3, "active_skill": "r",
                       "active_skill_timer": 46}),
      ("PORTRAIT LOD", {"pulse": 1.3, "_portrait_hd": True})]
for i, (label, state) in enumerate(SK):
    x = 34 + (i % 3) * 410
    y = 96 + (i // 3) * 300
    rect = pygame.Rect(x, y, 392, 280)
    pygame.draw.rect(sheet, PANEL, rect, border_radius=10)
    pygame.draw.rect(sheet, PANEL_EDGE, rect, 2, border_radius=10)
    img, _h = crop_render(NEW, state, size=340)
    img = scale2x(img, 0.82)
    sheet.blit(img, (rect.x + (rect.width - img.get_width()) // 2,
                     rect.y + 30))
    sheet.blit(font_label.render(label, True, (226, 232, 220)),
               (rect.x + 12, rect.y + 8))

out = os.path.join(ROOT, "docs", "gornak_v4_skills.png")
pygame.image.save(sheet, out)
print(out)

# ══════════════════════════════════════════════════════════════════
# Sheet 3 - komposit "in-game": lane + paritas keluarga
# ══════════════════════════════════════════════════════════════════
IW, IH = 1280, 560
game = pygame.Surface((IW, IH))
game.fill((22, 26, 20))
# "tanah" sederhana ala lane
for gy in range(IH // 2, IH, 26):
    shade = 16 + (gy * 7) % 14
    pygame.draw.line(game, (shade, shade + 5, shade - 2), (0, gy),
                     (IW, gy), 2)
for gx in range(0, IW, 64):
    pygame.draw.line(game, (30, 34, 26), (gx, IH // 2), (gx, IH), 1)
game.blit(font_title.render(
    "GORNAK v4 — DI LANE (paritas ukuran dengan keluarga)", True, ACCENT),
    (34, 14))
game.blit(font_small.render(
    "Kolom: gornak (v4) · morgath · kaizen · vex · abaddon — semua lewat "
    "pipeline render yang sama seperti game", True, SUB), (36, 56))

from heroes import _ProbeEntity, render_hero as RH, clear_hero_sprite_cache

clear_hero_sprite_cache()
names = ("gornak", "morgath", "kaizen", "vex", "abaddon")
for i, name in enumerate(names):
    hx = 190 + i * 230
    hy = 360
    h = _ProbeEntity(name, hx, hy)
    h.pulse = 1.35
    h.direction = 1
    h.team = "blue"
    pygame.draw.ellipse(game, (0, 0, 0), (hx - 34, hy + 14, 68, 14))
    RH(name, game, h, hx, hy)
    pygame.draw.rect(game, (40, 0, 0), (hx - 30, hy - 78, 60, 7))
    pygame.draw.rect(game, (100, 220, 100), (hx - 30, hy - 78, 44, 7))
    pygame.draw.rect(game, (255, 200, 50), (hx - 30, hy - 78, 60, 7), 1)
    lbl = font_label.render(name, True, (235, 240, 225))
    game.blit(lbl, lbl.get_rect(center=(hx, hy + 44)))

out = os.path.join(ROOT, "docs", "gornak_v4_ingame.png")
pygame.image.save(game, out)
print(out)
