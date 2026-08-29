#!/usr/bin/env python3
# ============================================================
# Demo: sprite-sheet animasi Zephyr (walk, attack, idle)
# ------------------------------------------------------------
# Render frame-frame animasi rig masterwork Zephyr asli.
#
# Jalankan:
#   SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
#     /home/user/.venv/bin/python tools/zephyr_anim_demo.py
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
sy = _b._NS_zephyr


def _font(size):
    return pygame.font.SysFont("dejavusans", size, bold=True)


def _label(surface, text, x, y, size=20, color=(235, 235, 235)):
    surf = _font(size).render(text, True, color)
    surface.blit(surf, (x, y))
    return surf.get_size()


def render_frame(action, phase, progress=0.0, facing=1, size=120):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    sy._draw_zephyr_elite(s, size // 2, size // 2, facing, phase, action,
                          progress, True)
    return s


def render_cycle(action, n_frames, size=120, progress=0.0):
    frames = []
    params = []
    for i in range(n_frames):
        if action == "attack":
            prog = i / (n_frames - 1)
            frames.append(render_frame(action, 0.0, progress=prog))
            params.append(f"ap={prog:.2f}")
        else:
            phase = i / n_frames * math.tau
            frames.append(render_frame(action, phase))
            params.append(f"p={i}/{n_frames}")
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


def main():
    out = os.path.join(ROOT, "tools", "_out")
    os.makedirs(out, exist_ok=True)

    walk_frames, walk_params = render_cycle("walk", 8)
    atk_frames, atk_params = render_cycle("attack", 8)
    idle_frames, idle_params = render_cycle("idle", 6)

    walk_sheet = _compose("WALK (8 fase)", walk_frames, walk_params)
    atk_sheet = _compose("ATTACK (8 fase)", atk_frames, atk_params)
    idle_sheet = _compose("IDLE (6 fase)", idle_frames, idle_params)

    w = max(walk_sheet.get_width(), atk_sheet.get_width(),
            idle_sheet.get_width())
    h = (walk_sheet.get_height() + atk_sheet.get_height()
         + idle_sheet.get_height() + 40)
    canvas = pygame.Surface((w, h))
    canvas.fill((20, 22, 30))
    canvas.blit(idle_sheet, (0, 0))
    canvas.blit(walk_sheet, (0, idle_sheet.get_height() + 10))
    canvas.blit(atk_sheet, (0, idle_sheet.get_height() + walk_sheet.get_height() + 20))

    path = os.path.join(out, "zephyr_anim_sheet.png")
    pygame.image.save(canvas, path)
    print("saved:", path, "size", canvas.get_size())


if __name__ == "__main__":
    main()
