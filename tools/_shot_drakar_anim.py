"""Filmstrip animasi Drakar (kontinu, tanpa bucket cache).

4 baris x 16 frame, dikomposit ke latar gelap (glow ADD butuh latar).
Baris: idle (napas), walk (langkah), attack (swing), helix (spin 4 putaran).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame.init()
pygame.display.set_mode((1, 1))

import bosses.level1 as l1  # noqa: E402

NS = l1._NS_drakar
FRAMES = 16
CW, CH = 250, 250
font = pygame.font.SysFont("monospace", 16)


def probe(**kw):
    from types import SimpleNamespace
    b = SimpleNamespace(boss_type="drakar", boss_class="mini", x=300.0,
                        y=300.0, direction=1, facing=1, pulse=1.2, timer=0,
                        attack_cooldown=46, active_skill=None,
                        active_skill_timer=0, target=None, _render_scale=1.0,
                        hurt_flash_timer=0, alive=True, radius=32,
                        hp=8000, max_hp=8000)
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def frame(boss, tag):
    s = pygame.Surface((CW, CH), pygame.SRCALPHA)
    s.fill((7, 8, 16, 255))
    NS.draw_drakar(s, boss, CW // 2, CH // 2 + 20)
    lab = pygame.Surface((CW, 20), pygame.SRCALPHA)
    lab.fill((0, 0, 0, 170))
    lab.blit(font.render(tag, True, (200, 205, 220)), (4, 2))
    s.blit(lab, (0, 0))
    return s


def row(bosses_tags):
    r = pygame.Surface((CW * FRAMES, CH), pygame.SRCALPHA)
    for i, (b, tag) in enumerate(bosses_tags):
        r.blit(frame(b, tag), (i * CW, 0))
    return r


def main():
    idle = [(probe(pulse=i * 0.39), f"idle {i}") for i in range(FRAMES)]
    walk = []
    for i in range(FRAMES):
        b = probe(pulse=i * 0.34)
        b._drk_last_x = b.x - 2.0
        b._drk_last_y = b.y
        walk.append((b, f"walk {i}"))
    atk = []
    for i in range(FRAMES):
        b = probe()
        b._drk_attack_active = True
        b.timer = 45 - int(i * 45 / FRAMES)   # atk_p = (45-t)/45
        b._drk_attack_dir = 1
        atk.append((b, f"atk {i}"))
    hel = []
    for i in range(FRAMES):
        b = probe(active_skill="w", active_skill_timer=44 - int(i * 44 / FRAMES))
        hel.append((b, f"helix {i}"))

    rows = [row(idle), row(walk), row(atk), row(hel)]
    sheet = pygame.Surface((CW * FRAMES, CH * len(rows)), pygame.SRCALPHA)
    sheet.fill((7, 8, 16, 255))
    for ri, r in enumerate(rows):
        sheet.blit(r, (0, ri * CH))
    pygame.image.save(sheet, "/home/user/mystic-arena/tools/drakar_anim_filmstrip.png")
    print("saved filmstrip", sheet.get_size())


if __name__ == "__main__":
    main()
