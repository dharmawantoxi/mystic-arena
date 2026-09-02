#!/usr/bin/env python3
"""Screenshot Ancient Apparition v3 — semua mode, lapisan hidup nyala.

Hasil: tools/_aa_v3_shots/*.png (idle/walk/run/attack/cast/hurt/skill).
100% prosedural — screenshot hanya untuk inspeksi visual manusia.
"""
import os
import sys
import time
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from heroes import ancient_apparition_fx as F
from bosses.level3 import _NS_ancient_apparition as G

F.reset_all()
SIZE = 460
C = SIZE // 2
BG = (16, 14, 22)
DT = 1.0 / 60.0


def probe(**kw):
    b = SimpleNamespace(
        boss_type="ancient_apparition", boss_class="true",
        x=float(C), y=float(C), direction=1, facing=1, pulse=1.2,
        timer=0, attack_cooldown=61, active_skill=None,
        active_skill_timer=0, target=None, hurt_flash_timer=0,
        alive=True, radius=30, hp=9000, max_hp=9000)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def shoot(b, name, settle=0.0, move=0.0, after=0.0):
    """Render settle detik dulu (FX hidup mengendap), lalu simpan."""
    s = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    for _ in range(int(settle / DT)):
        b.pulse += 0.05
        if move:
            b.x += move
        G.draw_apparition(s, b, int(b.x), C)
    for _ in range(int(after / DT)):
        b.pulse += 0.05
    out = pygame.Surface((SIZE, SIZE))
    out.fill(BG)
    G.draw_apparition(out, b, int(b.x), C)
    pygame.image.save(out, name)
    print("saved", os.path.basename(name))
    F.reset_all()


def main():
    outdir = os.path.join(ROOT, "tools", "_aa_v3_shots")
    os.makedirs(outdir, exist_ok=True)
    os.chdir(outdir)
    tgt = SimpleNamespace(x=C + 120.0, y=float(C), alive=True)

    b = probe()
    shoot(b, "01_idle.png", settle=1.2)

    b = probe()
    shoot(b, "02_walk.png", settle=0.9, move=0.9)

    b = probe()
    shoot(b, "03_run.png", settle=0.7, move=2.2)

    # attack: anticipation, wind-up, impact (swing), follow-through
    for name, prog in (("04_attack_anticipation", 0.12),
                       ("05_attack_windup", 0.32),
                       ("06_attack_impact", 0.50),
                       ("07_attack_follow", 0.62)):
        b = probe(_aa_attack_active=True, _aa_attack_progress=prog,
                  target=tgt)
        shoot(b, name + ".png", settle=0.25)

    for sk in "qwer":
        b = probe(active_skill=sk, active_skill_timer=30, target=tgt)
        shoot(b, f"08_skill_{sk}.png", settle=0.5)

    b = probe(hurt_flash_timer=6)
    shoot(b, "09_hurt.png", settle=0.1)

    b = probe()
    d = F.director_for(b)
    d.on_impact(C + 90, C - 10, 0.2, 1.6, True, "blast")
    s = pygame.Surface((SIZE, SIZE))
    s.fill(BG)
    d.draw_ground(s, C, C)
    d.draw_front(s, C, C)
    pygame.image.save(s, "10_impact_blast.png")
    print("saved 10_impact_blast.png")

    F.reset_all()
    print("done")


if __name__ == "__main__":
    main()
