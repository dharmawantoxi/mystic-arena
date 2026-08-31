#!/usr/bin/env python3
"""Preview sheets untuk Morgath v2 Pixel Masterwork + v2.1 Skill FX.

Menghasilkan 5 sheet di docs/:
  - docs/morgath_v2_review.png         (7 pose + portrait LOD + zoom)
  - docs/morgath_v2_anim_strip.png     (strip serang 8 frame + walk 8)
  - docs/morgath_v2_ingame.png         (mini boss 1x + lane hero final)
  - docs/morgath_v2_skills.png         (Q/W/E/R x 3 tahap)
  - docs/morgath_v2_before_after.png   (v1 vs v2 + metrik terukur)

Jalankan:  /home/user/.venv/bin/python tools/_shot_morgath_v2.py
"""
import importlib.util as _ilu
import math
import os
import sys
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import heroes
from heroes import _ProbeEntity, _get_hero_scale
from bosses import level1 as L
from bosses.level1 import _NS_morgath as M

_spec = _ilu.spec_from_file_location(
    "_morgath_v1_snapshot",
    os.path.join(ROOT, "tools", "_morgath_v1_snapshot.py"))
_snap = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_snap)
V1 = _snap._NS_morgath

BG = (8, 9, 18)
PANEL = (13, 15, 30)
EDGE = (58, 68, 126)
ACCENT = (140, 190, 250)
SUB = (128, 138, 176)
NOTE = (96, 102, 134)

FONT = None


def F(size=16):
    global FONT
    if FONT is None:
        FONT = pygame.font.Font(None, size)
    return FONT


def probe(cx=0.0, cy=0.0, **kw):
    b = SimpleNamespace(boss_type="morgath", boss_class="mini", x=float(cx),
                        y=float(cy), direction=1, facing=1, pulse=1.25,
                        timer=0, attack_cooldown=48, active_skill=None,
                        active_skill_timer=0, target=None, _render_scale=1.0,
                        hurt_flash_timer=0, alive=True, radius=51)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def label(surf, text, pos, color=SUB, size=16, center=False):
    img = F(size).render(text, True, color)
    if center:
        pos = (pos[0] - img.get_width() // 2, pos[1])
    surf.blit(img, pos)


def panel(surf, rect, title=None):
    pygame.draw.rect(surf, PANEL, rect)
    pygame.draw.rect(surf, EDGE, rect, 1)
    if title:
        label(surf, title, (rect[0] + 8, rect[1] + 4), ACCENT, 15)


def blit_alpha(surf, sprite, pos, zoom=1, alpha=255):
    if zoom != 1:
        sprite = pygame.transform.scale(
            sprite, (int(sprite.get_width() * zoom),
                     int(sprite.get_height() * zoom)))
    if alpha < 255:
        sprite = sprite.copy()
        sprite.set_alpha(alpha)
    surf.blit(sprite, pos)


def rig_sprite(action, phase, ap=0.0, detail=False, size=190):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    M._draw_mor_rig(s, size // 2, size // 2 - 8, 1, phase, action, ap,
                    detail)
    return s


# ═══ 1. REVIEW ═══════════════════════════════════════════════════
def shot_review():
    W, H = 1320, 560
    surf = pygame.Surface((W, H))
    surf.fill(BG)
    label(surf, "MORGATH v2 - PIXEL MASTERWORK REVIEW", (24, 12), ACCENT, 26)
    poses = (("idle", 0.0), ("walk", 0.0), ("attack", 0.9), ("point", 0.0),
             ("channel", 0.0), ("erect", 0.0), ("ascend", 0.0))
    names = ("IDLE", "WALK", "ATTACK", "Q POINT", "W CHANNEL", "E ERECT",
             "R ASCEND")
    for i, ((action, ap), name) in enumerate(zip(poses, names)):
        x = 24 + i * 178
        rect = (x, 52, 168, 210)
        panel(surf, rect)
        label(surf, name, (rect[0], rect[2] + 72), SUB, 15, center=True)
        s = rig_sprite(action, 1.25, ap)
        blit_alpha(surf, s, (x + 84 - 68, rect[1] + 30), 0.72)
    # portrait LOD
    rect = (24, 300, 300, 240)
    panel(surf, rect, "PORTRAIT LOD (Hero Shop)")
    s = rig_sprite("idle", 1.25, detail=True, size=260)
    blit_alpha(surf, s, (rect[0] + 20, rect[1] + 4), 0.9)
    label(surf, "detail mikro + warna baru (dihitung sekali, dicache)",
          (rect[0] + 10, rect[1] + 216), NOTE, 14)
    # zoom material
    rect = (348, 300, 460, 240)
    panel(surf, rect, "ZOOM 2X - ORB + ANTENA + PAULDRON")
    s = rig_sprite("idle", 1.25, size=190)
    blit_alpha(surf, s, (rect[0] + 40, rect[1] - 30), 1.4)
    # metrics
    rect = (832, 300, 464, 240)
    panel(surf, rect, "METRIK")
    lines = (
        "rig native 154x117 (v1: 74x100)",
        "badan padat ~103 px (v1: ~55 px)",
        "skala lane %.3f -> final ~51 px" % _get_hero_scale("morgath"),
        "warna idle 68 / portrait 78",
        "render idle ~1.1 ms (budget 3.5 ms)",
        "skill Q/W/E/R world-space (1/_render_scale)",
        "E=90 px dunia, R=+-60 px dunia, W di target",
        "100% prosedural, tanpa image.load",
    )
    for i, t in enumerate(lines):
        label(surf, t, (rect[0] + 14, rect[1] + 34 + i * 24), SUB, 16)
    pygame.image.save(surf, os.path.join(ROOT, "docs", "morgath_v2_review.png"))


# ═══ 2. ANIM STRIP ═══════════════════════════════════════════════
def shot_anim():
    W, H = 1240, 480
    surf = pygame.Surface((W, H))
    surf.fill(BG)
    label(surf, "MORGATH v2 - ANIMATION STRIP", (24, 12), ACCENT, 26)
    # attack 8 frame
    label(surf, "ATTACK: anticipation -> thrust -> IMPACT hold -> release",
          (24, 46), SUB, 16)
    aps = (0.0, 0.14, 0.35, 0.62, 0.90, 0.96, 1.0, 0.90)
    for i, ap in enumerate(aps):
        x = 24 + i * 150
        rect = (x, 74, 142, 190)
        panel(surf, rect)
        s = rig_sprite("attack", 1.25, ap)
        blit_alpha(surf, s, (x + 71 - 60, rect[1] + 26), 0.62)
        label(surf, f"ap={ap:.2f}" + ("  IMPACT" if 0.86 <= ap <= 0.98 else ""),
              (x, rect[1] + 172), ACCENT if 0.86 <= ap <= 0.98 else NOTE, 13,
              center=True)
    # walk 8 frame
    label(surf, "WALK: foot solver + inertia cape/tassel (8 frame unik)",
          (24, 282), SUB, 16)
    for i in range(8):
        x = 24 + i * 150
        rect = (x, 310, 142, 150)
        panel(surf, rect)
        s = rig_sprite("walk", i * 0.785)
        blit_alpha(surf, s, (x + 71 - 60, rect[1] + 4), 0.62)
        label(surf, f"ph={i * 0.785:.2f}", (x, rect[1] + 130), NOTE, 13,
              center=True)
    pygame.image.save(surf,
                      os.path.join(ROOT, "docs", "morgath_v2_anim_strip.png"))


# ═══ 3. IN-GAME ══════════════════════════════════════════════════
def shot_ingame():
    W, H = 1180, 430
    surf = pygame.Surface((W, H))
    surf.fill(BG)
    label(surf, "MORGATH v2 - IN-GAME (mini boss 1x + lane hero)",
          (24, 12), ACCENT, 26)
    # mini boss (arena 460, HP bar + nama)
    rect = (24, 52, 560, 360)
    panel(surf, rect, "MINI BOSS ARENA (skala 1.0)")
    arena = pygame.Surface((460, 300), pygame.SRCALPHA)
    b = probe(230, 150)
    L.draw_morgath(arena, b, 230, 150)
    blit_alpha(surf, arena, (rect[0] + 50, rect[1] + 30), 1.0)
    # HP bar mini boss (y-r-15 = 150-51-15 = 84)
    pygame.draw.rect(surf, (52, 10, 10), (rect[0] + 230 - 90,
                                          rect[1] + 84, 180, 8))
    pygame.draw.rect(surf, (180, 40, 40), (rect[0] + 230 - 90,
                                           rect[1] + 84, 118, 8))
    label(surf, "MORGATH", (rect[0] + 230, rect[1] + 62), (220, 200, 160),
          16, center=True)
    # lane hero (render_hero final)
    rect = (608, 52, 548, 360)
    panel(surf, rect, "LANE HERO (pipeline: canvas -> smoothscale -> HD)")
    lane = pygame.Surface((500, 300))
    lane.fill((10, 11, 22))
    for i in range(0, 500, 24):
        pygame.draw.line(lane, (16, 18, 34), (i, 0), (i, 300))
    h = _ProbeEntity("morgath", 250, 150)
    h.pulse = 1.35
    h.direction = 1
    h.team = "blue"
    heroes.render_hero("morgath", lane, h, 250, 150)
    blit_alpha(surf, lane, (rect[0] + 24, rect[1] + 26), 1.0)
    label(surf, "badan final ~51 px (normalisasi pipeline)",
          (rect[0] + 24, rect[1] + 330), NOTE, 15)
    pygame.image.save(surf,
                      os.path.join(ROOT, "docs", "morgath_v2_ingame.png"))


# ═══ 4. SKILLS ═══════════════════════════════════════════════════
def shot_skills():
    W, H = 1680, 560
    surf = pygame.Surface((W, H))
    surf.fill(BG)
    label(surf, "MORGATH v2.1 - SKILL FX (3 FASE: TELEGRAPH / AKTIVASI / STEADY)",
          (24, 12), ACCENT, 26)
    skills = ("q", "w", "e", "r")
    names = {"q": "Q SPARK WRAITH", "w": "W FLUX", "e": "E MAGNETIC FIELD",
             "r": "R TEMPEST DOUBLE"}
    stages = ((18, "TELEGRAPH"), (10, "AKTIVASI"), (30, "STEADY"))
    timers = {"q": {"TELEGRAPH": 48, "AKTIVASI": 41, "STEADY": 25},
              "w": {"TELEGRAPH": 38, "AKTIVASI": 34, "STEADY": 20},
              "e": {"TELEGRAPH": 88, "AKTIVASI": 78, "STEADY": 45},
              "r": {"TELEGRAPH": 57, "AKTIVASI": 50, "STEADY": 30}}
    for si, skill in enumerate(skills):
        for ci, (dur_off, sname) in enumerate(stages):
            x = 24 + ci * 540
            y = 56 + si * 128
            rect = (x, y, 520, 120)
            panel(surf, rect)
            arena = pygame.Surface((520, 120), pygame.SRCALPHA)
            b = probe(260, 62, active_skill=skill,
                      active_skill_timer=timers[skill][sname])
            if skill == "w":
                b.target = SimpleNamespace(x=380.0, y=70.0, alive=True)
            L.draw_morgath(arena, b, 260, 62)
            blit_alpha(surf, arena, (x, y), 1.0)
            label(surf, sname, (x + 6, y + 2), ACCENT, 14)
            label(surf, names[skill] if ci == 0 else "",
                  (x + 6, y + 100), SUB, 14)
    # legenda
    label(surf, "TELEGRAPH: ring konvergen/chevron/retakan | AKTIVASI: burst+bintang+pilar | STEADY: aura berlapis+ring berputar",
          (24, 528), NOTE, 16)
    pygame.image.save(surf,
                      os.path.join(ROOT, "docs", "morgath_v2_skills.png"))


# ═══ 5. BEFORE/AFTER ═════════════════════════════════════════════
def shot_before_after():
    W, H = 1200, 520
    surf = pygame.Surface((W, H))
    surf.fill(BG)
    label(surf, "MORGATH - BEFORE (v1) / AFTER (v2 PIXEL MASTERWORK)",
          (24, 12), ACCENT, 26)
    # v1
    rect = (24, 52, 460, 380)
    panel(surf, rect, "V1 (74x100, badan ~55 px)")
    s1 = pygame.Surface((360, 300), pygame.SRCALPHA)
    b1 = probe(180, 150)
    _snap.draw_morgath_v1(s1, b1, 180, 150)
    blit_alpha(surf, s1, (rect[0] + 50, rect[1] + 30), 1.0)
    # v2
    rect = (508, 52, 460, 380)
    panel(surf, rect, "V2 (154x117, badan ~103 px, 2.8x warna)")
    s2 = pygame.Surface((360, 300), pygame.SRCALPHA)
    b2 = probe(180, 150)
    L.draw_morgath(s2, b2, 180, 150)
    blit_alpha(surf, s2, (rect[0] + 50, rect[1] + 30), 1.0)
    # metrics panel
    rect = (992, 52, 184, 380)
    panel(surf, rect, "DELTA")
    lines = ("badan", "55 -> 103 px", "", "warna", "27 -> 75", "", "render",
             "~1.1 ms", "", "skill FX", "canvas px ->", "world-space", "",
             "density", "1.65x luas", "", "procedural", "100%")
    for i, t in enumerate(lines):
        label(surf, t, (rect[0] + 10, rect[1] + 28 + i * 20), SUB, 14)
    pygame.image.save(
        surf, os.path.join(ROOT, "docs", "morgath_v2_before_after.png"))


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    shot_review()
    print("OK morgath_v2_review.png")
    shot_anim()
    print("OK morgath_v2_anim_strip.png")
    shot_ingame()
    print("OK morgath_v2_ingame.png")
    shot_skills()
    print("OK morgath_v2_skills.png")
    shot_before_after()
    print("OK morgath_v2_before_after.png")
