#!/usr/bin/env python3
# ============================================================
# Demo: sprite-sheet animasi Grimjaw V1 (idle, walk, attack, spin, death)
# ------------------------------------------------------------
# Render frame-frame animasi rig pixel-art V1 Grimjaw, berdampingan,
# untuk melihat & membandingkan kualitas animasi - pola yang sama
# dengan tools/vex_v1_anim_demo.py.
#
# Jalankan:
#   SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
#     python3 tools/grimjaw_v1_anim_demo.py
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

# Demo ini memotret FALLBACK CANVAS murni (rig + smear in-canvas);
# lapisan hidup 60fps (heroes/grimjaw_fx.py) dimatikan.
try:
    from heroes import grimjaw_fx as _gjfx
    _gjfx.GRIMJAW_FX_ENABLED = False
    gj._LIVE_MOD = False
except Exception:
    pass


def _font(size):
    return pygame.font.SysFont("dejavusans", size, bold=True)


def _label(surface, text, x, y, size=20, color=(235, 235, 235)):
    surf = _font(size).render(text, True, color)
    surface.blit(surf, (x, y))
    return surf.get_size()


def render_frame(action, phase, progress=0.0, facing=1, size=200,
                 spin_phase=0.0, death_frame=3):
    """Render satu frame body rig (tanpa efek latar)."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    gj._draw_grimjaw_elite(s, size // 2, size // 2 + 10, facing,
                           phase, action, progress, spin_phase,
                           detail=True, death_frame=death_frame)
    return s


def render_cycle(action, n_frames, size=200):
    frames = []
    params = []
    for i in range(n_frames):
        if action == "attack":
            prog = i / (n_frames - 1)
            frames.append(render_frame(action, 1.7, progress=prog))
            params.append(f"ap={prog:.2f}")
        elif action == "spin":
            spin = i / n_frames * math.tau * 2
            frames.append(render_frame(action, 0.6 + i * 0.35,
                                       spin_phase=spin))
            params.append(f"sp={spin:.1f}")
        elif action == "death":
            dfr = min(3, i)
            frames.append(render_frame(action, 1.0, death_frame=dfr))
            params.append(f"df={dfr}")
        else:
            phase = i / n_frames * math.tau
            frames.append(render_frame(action, phase))
            params.append(f"p={i}/{n_frames}")
    return frames, params


def _compose(title, frames, params, size=200, pad=6):
    n = len(frames)
    w = n * (size + pad) + pad
    h = size + pad * 2 + 34
    sheet = pygame.Surface((w, h))
    sheet.fill((26, 24, 30))
    _label(sheet, title, pad, 6, 18, (255, 200, 130))
    for i, f in enumerate(frames):
        sheet.blit(f, (pad + i * (size + pad), pad + 16))
        _label(sheet, params[i], pad + i * (size + pad), size + pad + 12,
               12, (170, 160, 150))
    return sheet


def main():
    out = os.path.join(ROOT, "tools", "_out")
    asset_dir = os.path.join(ROOT, "assets", "review")
    os.makedirs(out, exist_ok=True)
    os.makedirs(asset_dir, exist_ok=True)

    idle_frames, idle_params = render_cycle("idle", 6)
    walk_frames, walk_params = render_cycle("walk", 8)
    atk_frames, atk_params = render_cycle("attack", 8)
    spin_frames, spin_params = render_cycle("spin", 6)
    death_frames, death_params = render_cycle("death", 4)

    idle_sheet = _compose("IDLE (6 fase)", idle_frames, idle_params)
    walk_sheet = _compose("WALK (8 fase)", walk_frames, walk_params)
    atk_sheet = _compose("ATTACK (8 fase)", atk_frames, atk_params)
    spin_sheet = _compose("SPIN / BLADE FURY (6 fase)", spin_frames,
                          spin_params)
    death_sheet = _compose("DEATH (4 fase)", death_frames, death_params)

    sheets = (idle_sheet, walk_sheet, atk_sheet, spin_sheet, death_sheet)
    w = max(s.get_width() for s in sheets)
    h = sum(s.get_height() for s in sheets) + 10 * (len(sheets) - 1)
    canvas = pygame.Surface((w, h))
    canvas.fill((20, 18, 24))
    y = 0
    for s in sheets:
        canvas.blit(s, (0, y))
        y += s.get_height() + 10

    out_path = os.path.join(out, "grimjaw_v1_anim_sheet.png")
    asset_path = os.path.join(asset_dir, "grimjaw_v1_anim_sheet.png")
    pygame.image.save(canvas, out_path)
    pygame.image.save(canvas, asset_path)
    print("saved:", out_path, "size", canvas.get_size())
    print("saved:", asset_path)


if __name__ == "__main__":
    main()
