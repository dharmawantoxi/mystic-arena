#!/usr/bin/env python3
"""Sheet before/after penguatan FX skill mini-boss: OLD (git HEAD) vs NEW.

Jalankan: python3 tools/_shot_mini_skills_max.py
Hasil   : tools/mini_skills_before_after.png
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
import bosses.level1 as NEW


def old_module():
    base = subprocess.run(
        ["git", "show", "HEAD:bosses/level1.py"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    tmp = os.path.join(ROOT, "tools", "_old_level1_mini.py")
    with open(tmp, "w") as fh:
        fh.write(base)
    spec = importlib.util.spec_from_file_location("_old_level1_mini", tmp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    os.remove(tmp)
    return mod


OLD = old_module()

BG = (7, 8, 16)
PANEL = (12, 13, 26)
EDGE = (90, 80, 120)
ACCENT = (220, 200, 240)

ROWS = [
    # (label, boss_type, skill, timer)
    ("GORNAK Q impact", "gornak", "q", 6),
    ("GORNAK W arrive", "gornak", "w", 30),
    ("GORNAK E dome", "gornak", "e", 30),
    ("GORNAK R void", "gornak", "r", 36),
    ("GORNAK start", "gornak", "q", 88),
    ("MORGATH Q impact", "morgath", "q", 5),
    ("MORGATH W flux", "morgath", "w", 30),
    ("MORGATH E dome", "morgath", "e", 40),
    ("MORGATH R clone", "morgath", "r", 50),
    ("MORGATH start", "morgath", "q", 47),
    ("DRAKAR Q totem", "drakar", "q", 45),
    ("DRAKAR W helix", "drakar", "w", 20),
    ("DRAKAR E call", "drakar", "e", 25),
    ("DRAKAR R blade", "drakar", "r", 30),
    ("DRAKAR start", "drakar", "e", 57),
]


def probe(btype, skill, timer):
    return SimpleNamespace(boss_type=btype, boss_class="mini", x=0.0, y=0.0,
                           direction=1, pulse=1.2, timer=0, attack_cooldown=46,
                           active_skill=skill, active_skill_timer=timer,
                           target=SimpleNamespace(x=90.0, y=-6.0, alive=True),
                           _render_scale=1.0, hurt_flash_timer=0, alive=True,
                           radius=30, hp=8000, max_hp=8000)


FUNCS_NEW = {"gornak": NEW.draw_gornak, "morgath": NEW.draw_morgath,
             "drakar": NEW.draw_drakar}
FUNCS_OLD = {"gornak": OLD.draw_gornak, "morgath": OLD.draw_morgath,
             "drakar": OLD.draw_drakar}


def frame(fn, boss):
    surf = pygame.Surface((280, 280))
    surf.fill(BG)
    fn(surf, boss, 140, 150)
    crop = surf.subsurface(pygame.Rect(30, 30, 220, 220)).copy()
    return pygame.transform.scale(crop, (300, 300))


def main():
    font = pygame.font.Font(None, 22)
    pw, ph = 320, 330
    sheet = pygame.Surface((2 * pw + 8, len(ROWS) * ph + 30))
    sheet.fill(BG)
    sheet.blit(font.render("OLD (HEAD)", True, ACCENT), (12, 4))
    sheet.blit(font.render("NEW (FX diperkuat & dipertegas)", True, ACCENT),
               (pw + 12, 4))
    for i, (label, btype, skill, timer) in enumerate(ROWS):
        y = 26 + i * ph
        for col, funcs in ((0, FUNCS_OLD), (1, FUNCS_NEW)):
            x = 8 + col * pw
            pygame.draw.rect(sheet, EDGE, (x, y, pw - 8, ph - 8), 1)
            pygame.draw.rect(sheet, PANEL, (x + 1, y + 1, pw - 10, ph - 10))
            sheet.blit(font.render(label, True, ACCENT), (x + 8, y + 6))
            img = frame(funcs[btype], probe(btype, skill, timer))
            sheet.blit(img, (x + (pw - 8) // 2 - 150, y + 26))
    out = os.path.join(ROOT, "tools", "mini_skills_before_after.png")
    pygame.image.save(sheet, out)
    print("saved", out, sheet.get_size())


if __name__ == "__main__":
    main()
