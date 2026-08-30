#!/usr/bin/env python3
"""Filmstrip animasi Level 2 ORIGINAL-MAX.

Bukti kontinuitas per-frame (idle/walk/attack + satu skill per boss):
tiap frame = render kontinu (tanpa bucket stepping). Baris OLD vs NEW
dipakai untuk memastikan identitas seni tetap & gerak mulus.

Jalankan: python3 tools/_shot_level2_anim.py
Hasil   : tools/level2_anim_filmstrip.png
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
    tmp = os.path.join(ROOT, "tools", "_old_level2_anim.py")
    with open(tmp, "w") as fh:
        fh.write(base)
    spec = importlib.util.spec_from_file_location("_old_level2_anim", tmp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    os.remove(tmp)
    return mod


OLD = old_renderer()
BG = (7, 8, 16)
CD = {"razak": 45, "khalros": 45, "gorath": 44, "alchemist": 50}
DUR = {"razak": ("r", 90), "khalros": ("r", 70), "gorath": ("q", 90),
       "alchemist": ("r", 90)}


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


def cell(fn, boss, cd, size=80):
    surf = pygame.Surface((size, size))
    surf.fill(BG)
    fn(surf, boss, size // 2, size // 2 + 6)
    return surf


def frames_for(name, klass, fn, cd):
    """Kembalikan list (label, [boss frames]) untuk idle/walk/attack/skill."""
    rows = []

    def idle(p):
        return probe(name, klass, cd, pulse=p)

    rows.append(("idle", [idle(0.5 + i * 0.18) for i in range(10)]))

    def wk(p):
        b = probe(name, klass, cd, pulse=p)
        b._drk_last_x = b.x - 2.0
        b._drk_last_y = b.y
        return b

    rows.append(("walk", [wk(0.4 + i * 0.22) for i in range(10)]))

    def atk(p):
        b = probe(name, klass, cd, timer=int((1.0 - p) * (cd - 1)),
                  direction=1)
        b._drk_attack_active = True
        b._drk_attack_dir = 1
        b._drk_previous_timer = int((1.0 - p) * (cd - 1)) + 1
        return b

    rows.append(("attack", [atk(i / 10.0) for i in range(10)]))

    sk, dur = DUR[name]
    rows.append((f"skill-{sk}",
                 [probe(name, klass, cd, active_skill=sk,
                        active_skill_timer=dur - 2 - i * max(1, dur // 10),
                        target=SimpleNamespace(x=40.0, y=0.0, alive=True))
                  for i in range(10)]))
    return rows


def main():
    font = pygame.font.Font(None, 20)
    cw, ch = 82, 82
    bosses = ("razak", "khalros", "gorath", "alchemist")
    ncols = 10 + 1  # 10 frame + label
    sheet = pygame.Surface((ncols * cw, len(bosses) * 4 * ch + 30))
    sheet.fill(BG)
    sheet.blit(font.render("FILMSTRIP LEVEL2 ORIGINAL-MAX "
                           "(kontinuitas per-frame)", True, (220, 220, 220)),
               (12, 4))
    r = 0
    for name in bosses:
        klass = "true" if name == "alchemist" else "mini"
        for label, frames in frames_for(name, klass, getattr(NEW, "draw_" + name),
                                        CD[name]):
            y = 30 + r * ch
            sheet.blit(font.render(f"{name[:4]}.{label}", True,
                                   (200, 200, 200)), (6, y + 32))
            for i, boss in enumerate(frames):
                x = 82 + i * cw
                img = cell(getattr(NEW, "draw_" + name), boss, CD[name])
                sheet.blit(img, (x, y))
            r += 1
    out = os.path.join(ROOT, "tools", "level2_anim_filmstrip.png")
    pygame.image.save(sheet, out)
    print("saved", out)


if __name__ == "__main__":
    main()
