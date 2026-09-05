#!/usr/bin/env python3
"""Contact sheet Gornak v5 — renderer modular + lapisan hidup ter-sintesis.

Menghasilkan:
  - docs/gornak_v5_poses.png      (pose strip: idle..death, jalur boss)
  - docs/gornak_v5_fx.png         (lapisan hidup per fase skill Q/W/E/R:
                                   charge -> release -> area -> impact,
                                   dirender lewat director sungguhan)
  - docs/gornak_v5_lanes.png      (lane boss vs lane hero 0.7x, ayunan
                                   dengan trail + partikel)

Jalankan:  python3 tools/_shot_gornak_v5.py
"""
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

import heroes                                    # noqa: E402
from bosses.level1 import _NS_gornak as G       # noqa: E402
from heroes import gornak_fx as F               # noqa: E402

DT = 1.0 / 60.0
BG = (10, 9, 16)
PANEL = (16, 13, 26)
EDGE = (96, 62, 148)
LABEL = (188, 150, 236)
font_t = pygame.font.Font(None, 34)
font_l = pygame.font.Font(None, 22)


def probe(x=0.0, y=0.0, scale=None):
    h = SimpleNamespace(
        x=x, y=y, alive=True, boss_type="gornak", pulse=1.2,
        direction=1, facing=1, timer=0, attack_cooldown=38,
        speed=1.6, range=60, radius=16, hp=800, max_hp=800,
        hurt_flash_timer=0, blink_from_x=0, blink_from_y=0,
        mana_void_x=0, mana_void_y=0, active_skill=None,
        active_skill_timer=0, target=None, crit=False,
        _gnk_attack_active=False, _gnk_attack_manual=False,
        _gnk_attack_progress=0.0, _gnk_attack_phase="NONE",
        _gnk_previous_timer=0, _gnk_attack_frame=0,
    )
    if scale is not None:
        h._render_scale = scale
    return h


def draw_boss(surf, h, cx, cy):
    G.draw_gornak(surf, h, int(cx), int(cy))


def draw_live(surf, h, cx, cy):
    F.draw_ground_layer(surf, h, h.x, h.y)
    F.draw_live_layer(surf, h, h.x, h.y)


# ── 1. strip pose (jalur boss) ───────────────────────────────────────
def sheet_poses(path):
    F.reset_all()
    cols = [
        ("IDLE", lambda h: None),
        ("WALK", lambda h: _set_gait(h, 1.6)),
        ("RUN", lambda h: _set_gait(h, 2.6)),
        ("ATK wind", lambda h: _set_swing(h, 0.22)),
        ("ATK swing", lambda h: _set_swing(h, 0.42)),
        ("ATK impact", lambda h: _set_swing(h, 0.55)),
        ("Q", lambda h: _set_skill(h, "q", 30)),
        ("W", lambda h: _set_skill(h, "w", 18)),
        ("E", lambda h: _set_skill(h, "e", 40)),
        ("R", lambda h: _set_skill(h, "r", 70)),
        ("HURT", lambda h: setattr(h, "hurt_flash_timer", 6)),
        ("DEATH", lambda h: setattr(h, "alive", False)),
    ]
    cw, chh = 132, 168
    sheet = pygame.Surface((cw * len(cols), chh + 64), pygame.SRCALPHA)
    sheet.fill(BG)
    for i, (name, setup) in enumerate(cols):
        px = i * cw
        panel = pygame.Surface((cw - 8, chh - 8), pygame.SRCALPHA)
        panel.fill(PANEL)
        h = probe(px + cw // 2, 120)
        h._prev_x = None
        setup(h)
        for _ in range(6):
            G._update_gnk_attack_anim(h)
        if getattr(h, "_walk", False):
            # pemanasan: renderer merekam _moving_cached dari delta x
            draw_boss(pygame.Surface((8, 8), pygame.SRCALPHA), h,
                      panel.get_width() // 2 - 12, 118)
            h.x += 18.0
            draw_boss(pygame.Surface((8, 8), pygame.SRCALPHA), h,
                      panel.get_width() // 2 - 4, 118)
            h.x += 8.0
        draw_boss(panel, h, panel.get_width() // 2, 118)
        sheet.blit(panel, (px + 4, 54))
        t = font_l.render(name, True, LABEL)
        sheet.blit(t, (px + 8, 30))
        pygame.draw.rect(sheet, EDGE, (px + 4, 54, cw - 8, chh - 8), 1)
    ttl = font_t.render("Gornak v5 - pose router (boss lane, 100% procedural)",
                        True, (240, 230, 255))
    sheet.blit(ttl, (10, 4))
    pygame.image.save(sheet, path)
    print("saved", path)


def _set_gait(h, speed):
    """Gerak horizontal: satu draw pemanasan supaya _detect_moving aktif."""
    h.speed = speed
    h._walk = True


def _set_swing(h, p):
    h._gnk_attack_active = True
    h._gnk_attack_manual = True
    h._gnk_attack_progress = p


def _set_skill(h, k, timer):
    h.active_skill = k
    h.active_skill_timer = timer


# ── 2. lapisan hidup: 4 fase x 4 skill ───────────────────────────────
def sheet_fx(path):
    F.reset_all()
    phases = (("charge", 0.02), ("release", 0.30), ("area", 0.52),
              ("impact", 0.74))
    cw, chh = 168, 132
    sheet = pygame.Surface((cw * len(phases) + 60, chh * 4 + 58),
                           pygame.SRCALPHA)
    sheet.fill(BG)
    for r, skill in enumerate(("q", "w", "e", "r")):
        for c, (pname, frac) in enumerate(phases):
            px, py = 60 + c * cw, 40 + r * chh
            F.reset_all()
            h = probe(90, 74)
            h.target = probe(220, 60)
            h.target.radius = 12
            F.attach(h)
            d = F.director_for(h)
            total = F.SkillFX.TIMELINE[skill]
            dur = sum(total)
            h.active_skill = skill
            h.active_skill_timer = max(1, int(dur * 60 * (1 - frac)))
            if skill == "r" and frac > 0.5:
                h.mana_void_x, h.mana_void_y = 250.0, 90.0
            if skill == "w" and frac > 0.3:
                h.blink_from_x, h.blink_from_y = 20.0, 70.0
            d.emit_cast(h.x, h.y, skill)
            # jalankan timeline sampai frac yang diminta
            target_s = dur * frac
            steps = max(1, int(target_s / DT))
            for i in range(steps):
                F.tick(DT)
            panel = pygame.Surface((cw - 8, chh - 8), pygame.SRCALPHA)
            G.draw_gornak(panel, h, 90, 100)
            draw_live(panel, h, 90, 100)
            sheet.blit(panel, (px, py))
            pygame.draw.rect(sheet, EDGE, (px, py, cw - 8, chh - 8), 1)
            lab = font_l.render("%s %d p%d" % (pname,
                                               d.particles.count(),
                                               len(d.impacts)),
                                True, (150, 150, 170))
            sheet.blit(lab, (px + 2, py + chh - 24))
        sk = font_l.render(skill.upper(), True, LABEL)
        sheet.blit(sk, (8, 40 + r * chh + chh // 2 - 10))
    ttl = font_t.render("gornak_fx v5 - SkillFX 4-fase x lapisan hidup",
                        True, (240, 230, 255))
    sheet.blit(ttl, (10, 4))
    pygame.image.save(sheet, path)
    print("saved", path)


# ── 3. dua lane saat ayunan ──────────────────────────────────────────
def sheet_lanes(path):
    F.reset_all()
    sheet = pygame.Surface((420, 236), pygame.SRCALPHA)
    sheet.fill(BG)
    panel = pygame.Surface((420, 200), pygame.SRCALPHA)
    panel.fill((24, 20, 34))
    cells = (("BOSS lane", None, (110, 110)),
             ("HERO lane 0.7x", 0.72, (310, 110)))
    for title, scale, (cx, cy) in cells:
        F.reset_all()
        h = probe(cx, cy, scale=scale)
        h.target = probe(cx + 120, cy - 4)
        h.target.radius = 12
        F.attach(h)
        d = F.director_for(h)
        pygame.draw.circle(panel, (60, 52, 78), (cx, cy), 62, 1)
        # 26 frame ayunan manual -> trail + gust
        h._gnk_attack_active = True
        h._gnk_attack_manual = True
        for i in range(26):
            h._gnk_attack_progress = 0.18 + i * 0.02
            G._update_gnk_attack_anim(h)
            F.tick(DT)
        if scale is None:
            draw_boss(panel, h, cx, cy)
        else:
            heroes.clear_hero_sprite_cache()
            heroes.render_hero("gornak", panel, h, cx, cy)
        draw_live(panel, h, cx, cy)
        lab = font_l.render(title, True, LABEL)
        panel.blit(lab, (cx - lab.get_width() // 2, 6))
        pygame.draw.rect(sheet, EDGE, (0, 0, 420, 200), 1)
    sheet.blit(panel, (0, 0))
    stats = d.stats()
    st = font_l.render("live-layer stats: particles %d / trail %d / "
                       "dropped %d" % (stats["particles"], stats["trail"],
                                       stats["dropped"]),
                       True, (150, 150, 170))
    sheet.blit(st, (12, 206))
    F.reset_all()
    pygame.image.save(sheet, path)
    print("saved", path)


if __name__ == "__main__":
    out = os.path.join(ROOT, "docs")
    os.makedirs(out, exist_ok=True)
    sheet_poses(os.path.join(out, "gornak_v5_poses.png"))
    sheet_fx(os.path.join(out, "gornak_v5_fx.png"))
    sheet_lanes(os.path.join(out, "gornak_v5_lanes.png"))
