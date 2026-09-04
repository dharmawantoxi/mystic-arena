#!/usr/bin/env python3
"""Audit visual + performansi THALGRYN v4 (renderer pixel-art + FX hidup).

Menghasilkan tiga lembar preview ke docs/:
  * docs/thalgryn_v4_strip.png   — strip pose/animasi karakter
  * docs/thalgryn_v4_skills.png  — sequence 4 fase skill Q/W/E/R
  * docs/thalgryn_v4_combat.png  — tebasan melee (trail) + Water Spear +
                                   impact FX + hit-stop/shake bus

Jalankan:  python3 tools/_shot_thalgryn_v4.py
"""
import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame                                              # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

from heroes import _ProbeEntity                            # noqa: E402
from heroes import combat_feel as FEEL                     # noqa: E402
from heroes import thalgryn_fx as F                         # noqa: E402
from bosses.level6 import _NS_thalgryn as G                # noqa: E402

DT = 1.0 / 60.0
BG = (24, 27, 34, 255)
GROUND = (36, 40, 50, 255)


def mk(x, y, scale=None):
    h = _ProbeEntity("thalgryn", x, y)
    h.boss_type = "thalgryn"
    h.alive = True
    h.pulse = 1.2
    h.direction = h.facing = 1
    h.attack_cooldown = 44
    h.range = 160
    h.speed = 0.9
    h.hp = h.max_hp = 14000
    h.radius = 38
    h.skill_damage = 320
    h.hurt_flash_timer = 0
    if scale is not None:
        h._render_scale = scale
    return h


def frame(surface, h, x, y):
    """Satu frame penuh jalur BOSS: ground FX -> sprite -> live FX.

    ``draw_thalgryn`` sudah memanggil ground layer (lewat ``_live_fx``)
    dan live layer di dalamnya sesuai kontrak render order proyek,
    jadi di sini cukup satu panggilan (sama seperti ``Boss.draw``).
    """
    h.pulse += 0.30
    # pin delta-time ke 1/60 s supaya preview deterministik (loop preview
    # jalan lebih cepat dari wall-clock; controller memakai jam nyata)
    h._th_last_ms = pygame.time.get_ticks() - 17
    G.draw_thalgryn(surface, h, x, y)


def panel(w, hgt, title=None):
    s = pygame.Surface((w, hgt), pygame.SRCALPHA)
    s.fill(BG)
    pygame.draw.rect(s, GROUND, (0, hgt - 46, w, 46))
    return s


# ══════════════════════════════════════════════════════════════════════════
# 1. STRIP POSE / ANIMASI
# ══════════════════════════════════════════════════════════════════════════
def strip():
    poses = [
        ("idle", None, 1),
        ("walk", lambda h, i: setattr(h, "_moving_cached", True), 1),
        ("run", lambda h, i: (setattr(h, "_moving_cached", True),
                              setattr(h, "speed", 2.6)), 1),
        ("charge", lambda h, i: (setattr(h, "_th_attack_active", True),
                                 setattr(h, "_th_attack_manual", True),
                                 setattr(h, "_th_attack_progress", 0.22)), 8),
        ("swing", lambda h, i: (setattr(h, "_th_attack_active", True),
                                setattr(h, "_th_attack_manual", True),
                                setattr(h, "_th_attack_progress", 0.42)), 18),
        ("impact", lambda h, i: (setattr(h, "_th_attack_active", True),
                                 setattr(h, "_th_attack_manual", True),
                                 setattr(h, "_th_attack_progress", 0.55)), 24),
        ("follow", lambda h, i: (setattr(h, "_th_attack_active", True),
                                 setattr(h, "_th_attack_manual", True),
                                 setattr(h, "_th_attack_progress", 0.72)), 31),
        ("hurt", lambda h, i: (setattr(h, "_th_hurt_frames", 8),
                               setattr(h, "hurt_flash_timer", 9)), 1),
        ("spawn", lambda h, i: setattr(h, "_th_spawn_t", 0.45), 30),
        ("victory", lambda h, i: setattr(h, "_victory", True), 50),
        ("death", lambda h, i: setattr(h, "alive", False), 75),
    ]
    cw, ch = 150, 190
    sheet = pygame.Surface((cw * len(poses), ch), pygame.SRCALPHA)
    sheet.fill(BG)
    fnt = pygame.font.SysFont(None, 16)
    for i, (name, mut, frames) in enumerate(poses):
        p = panel(cw, ch)
        h = mk(cw // 2, ch - 52)
        F.reset_all()
        FEEL.HITSTOP.clear()
        FEEL.SHAKE.clear()
        F.attach(h)
        for k in range(frames):
            if mut:
                mut(h, k)
            p.fill(BG)
            pygame.draw.rect(p, GROUND, (0, ch - 46, cw, 46))
            frame(p, h, cw // 2, ch - 52)
        sheet.blit(p, (i * cw, 0))
        sheet.blit(fnt.render(name, True, (210, 235, 245)),
                   (i * cw + 8, ch - 18))
    pygame.image.save(sheet, os.path.join(ROOT, "docs",
                                          "thalgryn_v4_strip.png"))
    return sheet


# ══════════════════════════════════════════════════════════════════════════
# 2. SEQUENCE SKILL 4 FASE
# ══════════════════════════════════════════════════════════════════════════
def skills_sequence():
    """Sequence jujur: cast -> travel -> impact -> recovery (dengan notify)."""
    cw, ch = 190, 175
    sheet = pygame.Surface((cw * 6, ch * 4), pygame.SRCALPHA)
    sheet.fill(BG)
    fnt = pygame.font.SysFont(None, 15)
    for r, key in enumerate("qwer"):
        h = mk(60, ch - 52)
        h.target = mk(60 + 100, ch - 52)
        F.reset_all()
        FEEL.HITSTOP.clear()
        FEEL.SHAKE.clear()
        F.attach(h)
        dur = F.SKILL_DUR[key]
        cast_at = 1
        impact_at = int(dur * 0.42)
        snaps = [3, 9, 15, 21, 27, 36]
        shots = {}
        for i in range(max(snaps) + 4):
            h.active_skill = key
            h.active_skill_timer = max(0, dur - i)
            if h.active_skill_timer == 0:
                h.active_skill = None
            if i == cast_at:
                F.notify_skill_cast(h, key)
            if i == impact_at:
                F.notify_skill_impact(h, h.x + 100, h.y, None, key)
            p = panel(cw, ch)
            frame(p, h, 60, ch - 52)
            for s in snaps:
                if i == s:
                    shots[s] = p.copy()
        for c, s in enumerate(snaps):
            sheet.blit(shots[s], (c * cw, r * ch))
        sheet.blit(fnt.render("%s: ant>cast>impact>rec" % key.upper(),
                              True, (255, 226, 122)), (4, r * ch + 4))
    pygame.image.save(sheet, os.path.join(ROOT, "docs",
                                          "thalgryn_v4_skill_sequence.png"))
    return sheet


# ══════════════════════════════════════════════════════════════════════════
# 3. COMBAT: melee trail + spear + impact
# ══════════════════════════════════════════════════════════════════════════
def combat():
    cw, ch = 200, 180
    sheet = pygame.Surface((cw * 6, ch * 2), pygame.SRCALPHA)
    sheet.fill(BG)
    fnt = pygame.font.SysFont(None, 15)
    # baris 1: melee swing (trail + whoosh)
    h = mk(70, ch - 55)
    tgt = mk(70 + 52, ch - 55)
    h.target = tgt
    F.reset_all()
    FEEL.HITSTOP.clear()
    FEEL.SHAKE.clear()
    F.attach(h)
    snaps = [6, 14, 19, 24, 30, 40]
    shots = {}
    for i in range(max(snaps) + 3):
        h._th_attack_active = True
        h._th_attack_manual = True
        h._th_attack_progress = min(1.0, i / 43.0)
        if i == 22:
            F.notify_melee_impact(h, tgt, 95, True)
        p = panel(cw, ch)
        pygame.draw.circle(p, (150, 70, 70, 255), (70 + 52, ch - 62), 9)
        frame(p, h, 70, ch - 55)
        for s in snaps:
            if i == s:
                shots[s] = p.copy()
    for c, s in enumerate(snaps):
        sheet.blit(shots[s], (c * cw, 0))
    sheet.blit(fnt.render("MELEE: trail+impact", True, (255, 226, 122)),
               (4, 4))
    # baris 2: ranged spear
    h2 = mk(40, ch - 55)
    t2 = mk(40 + 130, ch - 55)
    h2.target = t2
    F.reset_all()
    FEEL.HITSTOP.clear()
    FEEL.SHAKE.clear()
    F.attach(h2)
    shots = {}
    snaps2 = [4, 9, 14, 19, 24, 32]
    spawned = False
    for i in range(max(snaps2) + 3):
        h2._th_attack_active = True
        h2._th_attack_manual = True
        h2._th_attack_progress = min(1.0, i / 43.0)
        if i == 22 and not spawned:
            spawned = True
            d = F.director_for(h2)
            gx, gy = F.tip_screen(h2, h2.x, h2.y)
            d.projectiles.spawn(gx, gy, t2.x, t2.y - 8, speed=430.0)
        p = panel(cw, ch)
        pygame.draw.circle(p, (150, 70, 70, 255), (40 + 130, ch - 62), 9)
        frame(p, h2, 40, ch - 55)
        for s in snaps2:
            if i == s:
                shots[s] = p.copy()
    for c, s in enumerate(snaps2):
        sheet.blit(shots[s], (c * cw, ch))
    sheet.blit(fnt.render("RANGED: Water Spear", True, (255, 226, 122)),
               (4, ch + 4))
    pygame.image.save(sheet, os.path.join(ROOT, "docs",
                                          "thalgryn_v4_combat.png"))
    return sheet


# ══════════════════════════════════════════════════════════════════════════
# 4. PERF
# ══════════════════════════════════════════════════════════════════════════
def perf():
    h = mk(200.0, 200.0)
    h.target = mk(340.0, 200.0)
    surf = pygame.Surface((640, 400), pygame.SRCALPHA)
    F.reset_all()
    F.attach(h)
    # panaskan
    for i in range(40):
        h._th_attack_active = True
        h._th_attack_progress = (i % 44) / 44.0
        surf.fill((0, 0, 0, 0))
        frame(surf, h, 200, 200)
    t0 = time.perf_counter()
    n = 120
    for i in range(n):
        h._th_attack_active = True
        h._th_attack_progress = (i % 44) / 44.0
        if i % 12 == 0:
            F.notify_projectile_impact(h, 340.0, 200.0, 0.0, 90, False)
        surf.fill((0, 0, 0, 0))
        frame(surf, h, 200, 200)
    ms = (time.perf_counter() - t0) / n * 1000.0
    t0 = time.perf_counter()
    for _ in range(120):
        h.pulse += 0.3
        surf.fill((0, 0, 0, 0))
        G.draw_thalgryn(surf, h, 200, 200)
    ms2 = (time.perf_counter() - t0) / 120.0 * 1000.0
    print("full frame (ground+sprite+live, combat) : %.2f ms" % ms)
    print("draw_thalgryn lane boss               : %.2f ms" % ms2)
    print("partikel aktif                        : %d" % F.total_particles())
    F.reset_all()


if __name__ == "__main__":
    strip()
    skills_sequence()
    combat()
    perf()
    print("preview tersimpan di docs/thalgryn_v4_*.png")
