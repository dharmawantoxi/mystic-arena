#!/usr/bin/env python3
"""Review sheet Level 2 ORIGINAL-MAX: OLD (git HEAD) vs MAX (current).

Setiap baris = satu pose/skill dari satu boss; kolom kiri OLD (renderer
level2.py dari HEAD), kolom kanan ORIGINAL-MAX (file kerja saat ini).

Jalankan: python3 tools/_shot_level2_max.py
Hasil   : tools/level2_max_before_after.png
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


def old_renderer():
    base = subprocess.run(
        ["git", "show", "main:bosses/level2.py"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    tmp = os.path.join(ROOT, "tools", "_old_level2.py")
    with open(tmp, "w") as fh:
        fh.write(base)
    spec = importlib.util.spec_from_file_location("_old_level2", tmp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    os.remove(tmp)
    return mod


OLD = old_renderer()

BG = (7, 8, 16)
PANEL = (12, 13, 26)
EDGE = (90, 90, 110)


def probe(name, klass, cd, **kw):
    b = SimpleNamespace(boss_type=name, boss_class=klass, x=0.0, y=0.0,
                        direction=1, facing=1, pulse=1.0, timer=0,
                        attack_cooldown=cd, active_skill=None,
                        active_skill_timer=0, target=None, _render_scale=1.0,
                        hurt_flash_timer=0, alive=True, radius=30,
                        hp=9000, max_hp=9000)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def frame(fn, boss, cd, size=300, fill=BG, cy=170):
    surf = pygame.Surface((size, size))
    surf.fill(fill)
    fn(surf, boss, 150, cy)
    crop = surf.subsurface(pygame.Rect(35, 30, 230, 240)).copy()
    return pygame.transform.scale(crop, (340, 360))


def walk(name, klass, cd, pulse):
    b = probe(name, klass, cd, pulse=pulse)
    b._drk_last_x = b.x - 2.0
    b._drk_last_y = b.y
    return b


# (nama baris, boss, fn lama, fn baru, cd)
CASES = [
    ("RAZAK idle", "razak", "mini", 45, probe("razak", "mini", 45, pulse=1.0)),
    ("RAZAK walk", "razak", "mini", 45, walk("razak", "mini", 45, 1.5)),
    ("RAZAK attack", "razak", "mini", 45, probe("razak", "mini", 45, _razak_attack_active=True, _razak_attack_progress=0.5)),
    ("RAZAK Q Sticky Napalm", "razak", "mini", 45, probe("razak", "mini", 45, active_skill="q", active_skill_timer=20, target=SimpleNamespace(x=90.0, y=0.0, alive=True))),
    ("RAZAK W Flamebreak", "razak", "mini", 45, probe("razak", "mini", 45, active_skill="w", active_skill_timer=25, target=SimpleNamespace(x=90.0, y=0.0, alive=True))),
    ("RAZAK R Firestorm", "razak", "mini", 45, probe("razak", "mini", 45, active_skill="r", active_skill_timer=50, target=SimpleNamespace(x=90.0, y=0.0, alive=True))),
    ("RAZAK hurt flash", "razak", "mini", 45, probe("razak", "mini", 45, hurt_flash_timer=6)),
    ("KHALROS idle", "khalros", "mini", 45, probe("khalros", "mini", 45, pulse=1.0)),
    ("KHALROS walk", "khalros", "mini", 45, walk("khalros", "mini", 45, 1.5)),
    ("KHALROS Q Wild Axes", "khalros", "mini", 45, probe("khalros", "mini", 45, active_skill="q", active_skill_timer=25, target=SimpleNamespace(x=90.0, y=0.0, alive=True))),
    ("KHALROS W Call of Wild", "khalros", "mini", 45, probe("khalros", "mini", 45, active_skill="w", active_skill_timer=30, target=SimpleNamespace(x=90.0, y=0.0, alive=True))),
    ("KHALROS E Boar", "khalros", "mini", 45, probe("khalros", "mini", 45, active_skill="e", active_skill_timer=20, target=SimpleNamespace(x=90.0, y=0.0, alive=True))),
    ("KHALROS R Hawk", "khalros", "mini", 45, probe("khalros", "mini", 45, active_skill="r", active_skill_timer=40, target=SimpleNamespace(x=90.0, y=0.0, alive=True))),
    ("GORATH idle", "gorath", "mini", 44, probe("gorath", "mini", 44, pulse=1.0)),
    ("GORATH walk", "gorath", "mini", 44, walk("gorath", "mini", 44, 1.5)),
    ("GORATH Q Bloodrage", "gorath", "mini", 44, probe("gorath", "mini", 44, active_skill="q", active_skill_timer=50, target=SimpleNamespace(x=90.0, y=0.0, alive=True))),
    ("GORATH W Bloodrite", "gorath", "mini", 44, probe("gorath", "mini", 44, active_skill="w", active_skill_timer=30, target=SimpleNamespace(x=90.0, y=0.0, alive=True))),
    ("GORATH E Thirst", "gorath", "mini", 44, probe("gorath", "mini", 44, active_skill="e", active_skill_timer=15, target=SimpleNamespace(x=90.0, y=0.0, alive=True))),
    ("GORATH R Rupture", "gorath", "mini", 44, probe("gorath", "mini", 44, active_skill="r", active_skill_timer=50, target=SimpleNamespace(x=90.0, y=0.0, alive=True))),
    ("ALCHEMIST idle", "alchemist", "true", 50, probe("alchemist", "true", 50, pulse=1.0)),
    ("ALCHEMIST walk", "alchemist", "true", 50, walk("alchemist", "true", 50, 1.5)),
    ("ALCHEMIST Q Acid Spray", "alchemist", "true", 50, probe("alchemist", "true", 50, active_skill="q", active_skill_timer=20, target=SimpleNamespace(x=90.0, y=0.0, alive=True))),
    ("ALCHEMIST W Unstable", "alchemist", "true", 50, probe("alchemist", "true", 50, active_skill="w", active_skill_timer=30, target=SimpleNamespace(x=90.0, y=0.0, alive=True))),
    ("ALCHEMIST E Chem Rage", "alchemist", "true", 50, probe("alchemist", "true", 50, active_skill="e", active_skill_timer=30, target=SimpleNamespace(x=90.0, y=0.0, alive=True))),
    ("ALCHEMIST R Greevil", "alchemist", "true", 50, probe("alchemist", "true", 50, active_skill="r", active_skill_timer=50, target=SimpleNamespace(x=90.0, y=0.0, alive=True))),
    ("ALCHEMIST hurt flash", "alchemist", "true", 50, probe("alchemist", "true", 50, hurt_flash_timer=6)),
]


def main():
    font = pygame.font.Font(None, 22)
    pw, ph = 350, 400
    sheet = pygame.Surface((2 * pw + 8, len(CASES) * ph + 30))
    sheet.fill(BG)
    sheet.blit(font.render("OLD (HEAD)", True, (230, 180, 160)), (12, 4))
    sheet.blit(font.render("ORIGINAL-MAX (hurt flash + shadow reaktif + "
                           "cache + FX skill + shockwave)",
                           True, (180, 230, 180)), (pw + 12, 4))
    for i, (title, name, klass, cd, boss) in enumerate(CASES):
        y = 26 + i * ph
        for col, mod in ((0, OLD), (1, NEW)):
            x = 8 + col * pw
            pygame.draw.rect(sheet, EDGE, (x, y, pw - 8, ph - 8), 1)
            pygame.draw.rect(sheet, PANEL, (x + 1, y + 1, pw - 10, ph - 10))
            sheet.blit(font.render(title, True, (220, 220, 220)), (x + 8, y + 6))
            b2 = SimpleNamespace(**vars(boss))
            fn = getattr(mod, "draw_" + name)
            img = frame(fn, b2, cd)
            sheet.blit(img, (x + (pw - 8) // 2 - 170, y + 32))
    out = os.path.join(ROOT, "tools", "level2_max_before_after.png")
    pygame.image.save(sheet, out)
    print("saved", out)


if __name__ == "__main__":
    main()
