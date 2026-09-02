#!/usr/bin/env python3
"""Preview Xerathis V2: idle/walk/attack/flash/skills + live combat FX."""
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

import bosses.level3 as L
from heroes import xerathis_fx as F


def boss(skill=None, timer=0, pulse=1.0, moving=False, attack=False,
         hurt=0, target=True, alive=True):
    b = SimpleNamespace(boss_type="xerathis", boss_class="mini",
                        x=240.0, y=240.0, direction=1, facing=1,
                        pulse=pulse, timer=0, attack_cooldown=59,
                        active_skill=skill, active_skill_timer=timer,
                        target=(SimpleNamespace(x=330.0, y=230.0, alive=True,
                                                radius=12) if target else None),
                        _render_scale=1.0, hurt_flash_timer=hurt,
                        alive=alive, radius=30, hp=9000, max_hp=9000,
                        range=200)
    if moving:
        b._xr_last_x = b.x - 3.0
        b._xr_last_y = b.y
    if attack:
        b._xr_attack_active = True
        b._xr_attack_progress = 0.45
    return b


SCENE = 250
COLS = 6
ROWS = 2
W, H = SCENE * COLS, SCENE * ROWS
canvas = pygame.Surface((W, H), pygame.SRCALPHA)
canvas.fill((18, 22, 38))

top = [
    ("IDLE", boss(pulse=1.0)),
    ("WALK", boss(pulse=1.2, moving=True)),
    ("ATTACK", boss(pulse=1.0, attack=True)),
    ("HURT", boss(pulse=1.0, hurt=8)),
    ("NOVA q", boss(skill="q", timer=48)),
    ("FROSTBITE w", boss(skill="w", timer=38)),
]

bottom = [
    ("AURA e", boss(skill="e", timer=60)),
    ("FIELD r", boss(skill="r", timer=70)),
    ("IMPACT", boss(pulse=1.0)),
    ("SHARD", boss(pulse=1.0)),
    ("SKILL FX", boss(skill="q", timer=18)),
    ("AFTER", boss(skill="r", timer=28)),
]

panels = top + bottom
# simulate a few frames so live particles/projectiles appear
for _ in range(2):
    # impact/shard panels
    F.notify_projectile_cast(bottom[2][1], 240, 240)
    F.notify_skill_impact(bottom[4][1], 240, 240, 48, "q")
    F.notify_skill_impact(bottom[5][1], 240, 240, 110, "r")
    F.tick(1.0 / 60.0)

for i, (label, b) in enumerate(panels):
    col = i % COLS
    row = i // COLS
    panel = pygame.Surface((SCENE, SCENE), pygame.SRCALPHA)
    panel.fill((18, 22, 38))
    L.draw_xerathis(panel, b, 126, 128)
    # label
    try:
        from _render import get_font
        font = get_font(14)
        label_surf = font.render(label, True, (220, 235, 255))
        panel.blit(label_surf, (6, 6))
    except Exception:
        pass
    canvas.blit(panel, (col * SCENE, row * SCENE))

out = os.path.join(ROOT, "docs", "xerathis_v3_combat.png")
pygame.image.save(canvas, out)
print("saved", out, canvas.get_size())
