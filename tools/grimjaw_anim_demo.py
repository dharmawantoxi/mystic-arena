#!/usr/bin/env python3
# ============================================================
# Demo: sprite-sheet animasi Grimjaw (walk, attack, idle)
# ------------------------------------------------------------
# Render frame-frame animasi rig masterwork Grimjaw asli,
# berdampingan, untuk melihat & membandingkan kualitas animasi.
#
# Jalankan:
#   SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
#     /home/user/.venv/bin/python tools/grimjaw_anim_demo.py
# ============================================================
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import math
import pygame

pygame.init()
pygame.display.set_mode((8, 8))

from heroes import _bundle as _b
gj = _b._NS_grimjaw


def _font(size):
    return pygame.font.SysFont("dejavusans", size, bold=True)


def _label(surface, text, x, y, size=20, color=(235, 235, 235)):
    surf = _font(size).render(text, True, color)
    surface.blit(surf, (x, y))
    return surf.get_size()


def render_frame(action, phase, progress=0.0, facing=1, size=120,
                 spin_phase=0.0):
    """Render satu frame body rig (tanpa efek latar)."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    gj._draw_grimjaw_elite(s, size // 2, size // 2, facing, phase, action,
                           progress, spin_phase, True)
    return s


def render_cycle(action, n_frames, size=120, progress=0.0):
    """Render n frame dari satu siklus. Return (list_surface, list_param)."""
    frames = []
    params = []
    for i in range(n_frames):
        if action == "walk":
            phase = i / n_frames * math.tau
            frames.append(render_frame(action, phase))
            params.append(f"p={i}/{n_frames}")
        elif action == "idle":
            phase = i / n_frames * math.tau
            frames.append(render_frame(action, phase))
            params.append(f"p={i}/{n_frames}")
        elif action == "spin":
            phase = i / n_frames * math.tau
            sp = phase * 6
            frames.append(render_frame(action, phase, spin_phase=sp))
            params.append(f"p={i}/{n_frames}")
        else:  # attack
            prog = i / (n_frames - 1)
            frames.append(render_frame(action, 0.0, progress=prog))
            params.append(f"ap={prog:.2f}")
    return frames, params


def _compose(title, frames, params, size=120, pad=6):
    n = len(frames)
    w = n * (size + pad) + pad
    h = size + pad * 2 + 34
    sheet = pygame.Surface((w, h))
    sheet.fill((26, 28, 38))
    _label(sheet, title, pad, 6, 18, (255, 220, 150))
    for i, f in enumerate(frames):
        sheet.blit(f, (pad + i * (size + pad), pad + 16))
        _label(sheet, params[i], pad + i * (size + pad), size + pad + 12,
               12, (150, 158, 175))
    return sheet


class _FakeHero:
    """Hero palsu untuk jalur skill omnislash (butuh .direction/.pulse)."""
    def __init__(self):
        self.direction = 1
        self.pulse = 0.0


def render_omnislash(n_frames, size=120):
    """Render n frame omnislash penuh (ghost full-rig + body utama)."""
    hero = _FakeHero()
    frames = []
    params = []
    for i in range(n_frames):
        hero.pulse = i / n_frames * math.tau
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        gj._draw_grimjaw_omnislash(s, hero, size // 2, size // 2, 0,
                                   hero.pulse)
        frames.append(s)
        params.append(f"p={i}/{n_frames}")
    return frames, params


def main():
    out = os.path.join(ROOT, "tools", "_out")
    os.makedirs(out, exist_ok=True)

    walk_frames, walk_params = render_cycle("walk", 8)
    atk_frames, atk_params = render_cycle("attack", 8)
    idle_frames, idle_params = render_cycle("idle", 4)
    spin_frames, spin_params = render_cycle("spin", 8)
    omni_frames, omni_params = render_omnislash(8)

    walk_sheet = _compose("WALK (8 fase)", walk_frames, walk_params)
    atk_sheet = _compose("ATTACK (8 fase)", atk_frames, atk_params)
    idle_sheet = _compose("IDLE (4 fase)", idle_frames, idle_params)
    spin_sheet = _compose("SPIN / BLADE FURY (8 fase)", spin_frames, spin_params)
    omni_sheet = _compose("OMNISLASH (8 fase)", omni_frames, omni_params)

    w = max(walk_sheet.get_width(), atk_sheet.get_width(),
            idle_sheet.get_width(), spin_sheet.get_width(),
            omni_sheet.get_width())
    h = (walk_sheet.get_height() + atk_sheet.get_height()
         + idle_sheet.get_height() + spin_sheet.get_height()
         + omni_sheet.get_height() + 50)
    canvas = pygame.Surface((w, h))
    canvas.fill((20, 22, 30))
    canvas.blit(idle_sheet, (0, 0))
    canvas.blit(walk_sheet, (0, idle_sheet.get_height() + 10))
    canvas.blit(atk_sheet, (0, idle_sheet.get_height() + walk_sheet.get_height() + 20))
    canvas.blit(spin_sheet, (0, idle_sheet.get_height() + walk_sheet.get_height()
                             + atk_sheet.get_height() + 30))
    canvas.blit(omni_sheet, (0, idle_sheet.get_height() + walk_sheet.get_height()
                             + atk_sheet.get_height() + spin_sheet.get_height() + 40))

    path = os.path.join(out, "grimjaw_anim_sheet.png")
    pygame.image.save(canvas, path)
    print("saved:", path, "size", canvas.get_size())


if __name__ == "__main__":
    main()
