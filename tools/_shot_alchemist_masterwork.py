#!/usr/bin/env python3
"""Sheet ALCHEMIST MASTERWORK: OLD (main) vs NEW (worktree) + live FX.

Baris atas  = renderer lama ( ORIGINAL-MAX ) dari HEAD main.
Baris bawah = rig masterwork v2 + lapisan hidup heroes/alchemist_fx
              (trail, botol, semburan, rage, badai koin, impact).

Jalankan: python3 tools/_shot_alchemist_masterwork.py
Hasil   : tools/alchemist_masterwork_before_after.png
"""
import importlib.util
import os
import subprocess
import sys
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))
import bosses.level2 as NEW
import heroes.alchemist_fx as LIVE
from heroes import combat_feel as feel

BG = (16, 18, 26)
ACCENT = (225, 225, 225)


def old_renderer():
    base = subprocess.run(
        ["git", "show", "main:bosses/level2.py"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    tmp = os.path.join(ROOT, "tools", "_old_level2_alch.py")
    with open(tmp, "w") as fh:
        fh.write(base)
    spec = importlib.util.spec_from_file_location(
        "_old_level2_alch", tmp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    os.remove(tmp)
    return mod


OLD = old_renderer()


def probe(**kw):
    b = SimpleNamespace(boss_type="alchemist", boss_class="true",
                        x=0.0, y=0.0, direction=1, facing=1, pulse=1.0,
                        timer=0, attack_cooldown=50, active_skill=None,
                        active_skill_timer=0, target=None,
                        _render_scale=1.0, hurt_flash_timer=0,
                        alive=True, radius=30, hp=9000, max_hp=9000,
                        rage_active=False, speed=0.75)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def frame(fn, boss, cd, w=300, h=300, cx=150, cy=160):
    surf = pygame.Surface((w, h))
    surf.fill(BG)
    fn(surf, boss, cx, cy)
    return surf


def shot_pair(label, **kw):
    """(label, OLD frame, NEW frame)"""
    cd = kw.pop("cd", 50)
    b_old = probe(**kw)
    old = frame(OLD.draw_alchemist, b_old, cd)
    b_new = probe(**kw)
    live = kw.pop("live", None)
    new = frame(NEW.draw_alchemist, b_new, cd)
    if live:
        LIVE.attach(b_new)
        LIVE.tick(1 / 60.0)          # hidupkan edge cast
        for _ in range(live):
            NEW.draw_alchemist(new, b_new, 150, 160)
            LIVE.tick(1 / 60.0)
            if b_new.active_skill_timer:
                b_new.active_skill_timer -= 1
        LIVE.reset_all()
        feel.reset()
    return (label, old, new)


def main():
    tg = SimpleNamespace(x=260.0, y=170.0, alive=True)
    rows = [
        shot_pair("IDLE", pulse=1.2),
        shot_pair("WALK", pulse=2.0, _alch_last_x=-3.0,
                  _alch_last_y=0.0, _alch_moving=True),
        shot_pair("ATTACK windup", pulse=1.0,
                  _alch_attack_active=True, _alch_attack_progress=0.25,
                  timer=50),
        shot_pair("ATTACK impact", pulse=1.0,
                  _alch_attack_active=True, _alch_attack_progress=0.54,
                  timer=50, live=6),
        shot_pair("SKILL Q acid spray", pulse=1.4,
                  active_skill="q", active_skill_timer=26, target=tg,
                  live=14),
        shot_pair("SKILL W concoction", pulse=1.4,
                  active_skill="w", active_skill_timer=30, target=tg,
                  w_target_x=260.0, w_target_y=170.0, live=16),
        shot_pair("SKILL E rage", pulse=1.6,
                  active_skill="e", active_skill_timer=30,
                  rage_active=True, live=12),
        shot_pair("SKILL R greed", pulse=1.6,
                  active_skill="r", active_skill_timer=55, target=tg,
                  live=22),
        shot_pair("HURT", pulse=1.2, hurt_flash_timer=7),
    ]

    CW, CH = 300, 300
    PAD = 8
    W = 2 * CW + PAD * 3
    H = len(rows) * CH + PAD * (len(rows) + 1) + 16 * len(rows)
    out = pygame.Surface((W, H))
    out.fill((9, 10, 15))
    try:
        font = pygame.font.Font(None, 17)
        small = pygame.font.Font(None, 15)
    except Exception:
        font = small = None
    y = PAD
    for label, old, new in rows:
        if font:
            out.blit(font.render("%s  —  OLD (main)  vs  NEW (v2+live)"
                                 % label, True, ACCENT), (PAD, y + 1))
        y += 16
        out.blit(old, (PAD, y))
        out.blit(new, (PAD * 2 + CW, y))
        y += CH + PAD
    if small:
        out.blit(small.render(
            "OLD = rig ORIGINAL-MAX (main)   |   NEW = masterwork v2 + "
            "heroes/alchemist_fx (trail / botol / semburan / rage / koin)",
            True, (150, 160, 150)), (PAD, H - 18))
    path = os.path.join(ROOT, "tools",
                        "alchemist_masterwork_before_after.png")
    pygame.image.save(out, path)
    print("saved", path, out.get_size())


if __name__ == "__main__":
    main()
