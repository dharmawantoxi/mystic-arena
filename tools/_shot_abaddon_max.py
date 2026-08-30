#!/usr/bin/env python3
"""Review sheet Abaddon ORIGINAL-MAX: OLD (git HEAD) vs MAX (current).

Jalankan: python3 tools/_shot_abaddon_max.py
Hasil   : tools/abaddon_max_before_after.png
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


def old_renderer():
    base = subprocess.run(
        ["git", "show", "HEAD:bosses/level1.py"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    tmp = os.path.join(ROOT, "tools", "_old_level1_abaddon.py")
    with open(tmp, "w") as fh:
        fh.write(base)
    spec = importlib.util.spec_from_file_location("_old_level1_abaddon", tmp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    os.remove(tmp)
    return mod.draw_abaddon


OLD = old_renderer()

BG = (7, 8, 16)
PANEL = (12, 13, 26)
EDGE = (70, 90, 120)
ACCENT = (150, 210, 230)


def probe(**kw):
    b = SimpleNamespace(boss_type="abaddon", boss_class="mini", x=0.0, y=0.0,
                        direction=1, pulse=1.0, timer=0, attack_cooldown=50,
                        active_skill=None, active_skill_timer=0, target=None,
                        _render_scale=1.0, alive=True, radius=30, hp=9000,
                        max_hp=9000, hurt_flash_timer=0,
                        _ab_attack_active=False, _ab_attack_progress=0.0)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def walk(pulse):
    b = probe(pulse=pulse)
    b._drk_last_x = b.x - 2.0
    b._drk_last_y = b.y
    return b


def frame(fn, boss):
    surf = pygame.Surface((300, 300))
    surf.fill(BG)
    fn(surf, boss, 150, 170)
    crop = surf.subsurface(pygame.Rect(40, 40, 220, 220)).copy()
    return pygame.transform.scale(crop, (336, 336))


def main():
    font = pygame.font.Font(None, 22)
    poses = [
        ("idle", probe(pulse=1.0)),
        ("walk", walk(1.5)),
        ("melee 50%", probe(_ab_attack_active=True, _ab_attack_progress=0.5)),
        ("Q Mist Coil", probe(active_skill="q", active_skill_timer=45)),
        ("W Aphotic Shield", probe(active_skill="w",
                                   active_skill_timer=22)),
        ("E Darkness Gale", probe(active_skill="e", active_skill_timer=20)),
        ("R Death Sever", probe(active_skill="r", active_skill_timer=32,
                                 target=SimpleNamespace(x=90.0, y=0.0,
                                                        alive=True))),
        ("hurt flash (kena hit)", probe(hurt_flash_timer=6)),
    ]
    pw, ph = 350, 380
    sheet = pygame.Surface((2 * pw + 8, len(poses) * ph + 30))
    sheet.fill(BG)
    sheet.blit(font.render("OLD (HEAD)", True, ACCENT), (12, 4))
    sheet.blit(font.render("ORIGINAL-MAX (flame cache+aura+flash+shadow)",
                           True, ACCENT), (pw + 12, 4))
    for i, (title, boss) in enumerate(poses):
        y = 26 + i * ph
        for col, fn in ((0, OLD), (1, NEW.draw_abaddon)):
            x = 8 + col * pw
            pygame.draw.rect(sheet, EDGE, (x, y, pw - 8, ph - 8), 1)
            pygame.draw.rect(sheet, PANEL, (x + 1, y + 1, pw - 10, ph - 10))
            sheet.blit(font.render(title, True, ACCENT), (x + 8, y + 6))
            b2 = SimpleNamespace(**vars(boss))
            img = frame(fn, b2)
            sheet.blit(img, (x + (pw - 8) // 2 - 168, y + 30))
    out = os.path.join(ROOT, "tools", "abaddon_max_before_after.png")
    pygame.image.save(sheet, out)
    print("saved", out)


if __name__ == "__main__":
    main()
