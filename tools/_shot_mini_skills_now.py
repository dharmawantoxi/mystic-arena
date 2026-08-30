"""Audit cepat FX skill mini-boss (gornak/morgath/drakar) di latar gelap."""
import os
import sys
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame

pygame.init()
pygame.display.set_mode((1, 1))
import bosses.level1 as L

CW, CH = 240, 240
SKILLS = ["q", "w", "e", "r"]
TIMERS = {"q": 30, "w": 20, "e": 25, "r": 30}


def probe(btype, skill):
    b = SimpleNamespace(boss_type=btype, boss_class="mini", x=0.0, y=0.0,
                        direction=1, pulse=1.2, timer=0, attack_cooldown=46,
                        active_skill=skill, active_skill_timer=TIMERS[skill],
                        target=SimpleNamespace(x=90.0, y=-10.0, alive=True),
                        _render_scale=1.0, hurt_flash_timer=0, alive=True,
                        radius=30, hp=8000, max_hp=8000)
    return b


FUNCS = {"gornak": L.draw_gornak, "morgath": L.draw_morgath,
         "drakar": L.draw_drakar}

rows = []
for name, fn in FUNCS.items():
    cells = []
    for sk in SKILLS:
        s = pygame.Surface((CW, CH))
        s.fill((7, 8, 16))
        fn(s, probe(name, sk), CW // 2, CH // 2 + 10)
        cells.append(s)
    rows.append((name, cells))

sheet = pygame.Surface((CW * 4, CH * 3 + 60))
sheet.fill((7, 8, 16))
font = pygame.font.Font(None, 20)
for ri, (name, cells) in enumerate(rows):
    sheet.blit(font.render(name.upper(), True, (220, 220, 230)),
               (4, ri * (CH + 20)))
    for ci, c in enumerate(cells):
        sheet.blit(c, (ci * CW, ri * (CH + 20) + 20))
        sheet.blit(font.render(SKILLS[ci].upper(), True, (180, 180, 200)),
                   (ci * CW + 4, ri * (CH + 20) + 22))
pygame.image.save(sheet, os.path.join(ROOT, "tools", "_mini_skills_now.png"))
print("saved")
