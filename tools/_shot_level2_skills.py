#!/usr/bin/env python3
"""Sheet FX skill Level 2 ORIGINAL-MAX: OLD (HEAD) vs NEW.

Fokus pada FX skill Q/W/E/R (orb/impact/ring/gelombang kejut): kolom OLD
vs NEW per skill per boss. Skill target-anchored di-crop mengikuti target.

Jalankan: python3 tools/_shot_level2_skills.py
Hasil   : tools/level2_skills_before_after.png
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
        ["git", "show", "HEAD:bosses/level2.py"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    tmp = os.path.join(ROOT, "tools", "_old_level2_skills.py")
    with open(tmp, "w") as fh:
        fh.write(base)
    spec = importlib.util.spec_from_file_location("_old_level2_skills", tmp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    os.remove(tmp)
    return mod


OLD = old_renderer()
BG = (6, 7, 14)
ACCENT = (225, 225, 225)

# skill AI durations (untuk memilih frame mid-cast)
DUR = {
    ("razak", "q"): 40, ("razak", "w"): 50, ("razak", "r"): 90,
    ("khalros", "q"): 50, ("khalros", "w"): 60, ("khalros", "e"): 45,
    ("khalros", "r"): 70,
    ("gorath", "q"): 90, ("gorath", "w"): 60, ("gorath", "e"): 35,
    ("gorath", "r"): 90,
    ("alchemist", "q"): 40, ("alchemist", "w"): 60, ("alchemist", "e"): 60,
    ("alchemist", "r"): 90,
}

CD = {"razak": 45, "khalros": 45, "gorath": 44, "alchemist": 50}


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


def frame(fn, boss, cd):
    # frame luas (crop mengikuti FX target di kanan)
    surf = pygame.Surface((340, 340))
    surf.fill(BG)
    fn(surf, boss, 150, 170)
    crop = surf.subsurface(pygame.Rect(20, 30, 300, 280)).copy()
    return pygame.transform.scale(crop, (330, 300))


def main():
    font = pygame.font.Font(None, 22)
    pw, ph = 350, 320
    rows = []
    for boss in ("razak", "khalros", "gorath", "alchemist"):
        klass = "true" if boss == "alchemist" else "mini"
        for sk in ("q", "w", "e", "r"):
            if (boss, sk) not in DUR:
                continue
            dur = DUR[(boss, sk)]
            timer = max(0, dur // 2 - 2)
            b = probe(boss, klass, CD[boss], active_skill=sk,
                      active_skill_timer=timer,
                      target=SimpleNamespace(x=110.0, y=0.0, alive=True))
            rows.append((f"{boss.upper()} {sk.upper()}", boss, sk, b))

    sheet = pygame.Surface((2 * pw + 8, len(rows) * ph + 30))
    sheet.fill(BG)
    sheet.blit(font.render("FX OLD (HEAD)", True, (230, 180, 160)), (12, 4))
    sheet.blit(font.render("FX ORIGINAL-MAX (lebih besar/terang + impact ring)",
                           True, (180, 230, 180)), (pw + 12, 4))
    for i, (title, name, sk, boss) in enumerate(rows):
        y = 26 + i * ph
        for col, mod in ((0, OLD), (1, NEW)):
            x = 8 + col * pw
            pygame.draw.rect(sheet, (60, 60, 80), (x, y, pw - 8, ph - 8), 1)
            pygame.draw.rect(sheet, (12, 12, 22), (x + 1, y + 1, pw - 10, ph - 10))
            sheet.blit(font.render(title, True, ACCENT), (x + 8, y + 6))
            b2 = SimpleNamespace(**vars(boss))
            fn = getattr(mod, "draw_" + name)
            img = frame(fn, b2, CD[name])
            sheet.blit(img, (x + (pw - 8) // 2 - 165, y + 20))
    out = os.path.join(ROOT, "tools", "level2_skills_before_after.png")
    pygame.image.save(sheet, out)
    print("saved", out)


if __name__ == "__main__":
    main()
