#!/usr/bin/env python3
# ============================================================
# Demo: sprite-sheet animasi Sylara V1
#        (idle, walk, attack, swing, windrun, hurt, death)
# ------------------------------------------------------------
# Render frame-frame animasi rig pixel-art V1 Sylara, berdampingan,
# untuk melihat & membandingkan kualitas animasi - pola yang sama
# dengan tools/vex_v1_anim_demo.py / tools/grimjaw_v1_anim_demo.py.
#
# Semua pose berasal dari SATU rig prosedural yang sama (bukan
# sticker per state): idle napas, walk 4-beat, attack 8 fase dengan
# busur yang benar-benar ditarik, sapuan busur melee, dash windrun,
# hurt recoil, dan 4 fase roboh.
#
# Jalankan:
#   SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
#     python3 tools/sylara_v1_anim_demo.py
# ============================================================
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import math  # noqa: E402

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((8, 8))

from heroes import _bundle as _b  # noqa: E402

sy = _b._NS_sylara

# Demo ini memotret FALLBACK CANVAS murni (rig + smear in-canvas);
# lapisan hidup 60fps (heroes/sylara_fx.py) dimatikan.
try:
    from heroes import sylara_fx as _syfx
    _syfx.SYLARA_FX_ENABLED = False
    sy._LIVE_MOD = False
except Exception:
    pass


def _font(size):
    try:
        return pygame.font.SysFont("dejavusans", size, bold=True)
    except Exception:                      # pragma: no cover - CI minimal
        return pygame.font.Font(None, size)


def _label(surface, text, x, y, size=20, color=(235, 235, 235)):
    surf = _font(size).render(text, True, color)
    surface.blit(surf, (x, y))
    return surf.get_size()


def render_frame(action, phase, progress=0.0, facing=1, size=170,
                 death_frame=0):
    """Render satu frame body rig (fallback canvas, tanpa FX hidup)."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    sy._draw_sylara_elite(s, size // 2, size // 2 + 14, facing, phase, action,
                          progress, detail=True, death_frame=death_frame)
    return s


def render_cycle(action, n_frames, size=170):
    frames = []
    params = []
    for i in range(n_frames):
        if action in ("attack", "swing"):
            prog = i / float(n_frames - 1)
            frames.append(render_frame(action, 1.4, progress=prog))
            params.append("ap=%.2f" % prog)
        elif action == "death":
            dfr = min(3, i)
            frames.append(render_frame(action, 1.0, death_frame=dfr))
            params.append("df=%d" % dfr)
        else:
            phase = i / float(n_frames) * math.tau
            frames.append(render_frame(action, phase))
            params.append("p=%d/%d" % (i, n_frames))
    return frames, params


def _compose(title, frames, params, size=170, pad=6):
    n = len(frames)
    w = n * (size + pad) + pad
    h = size + pad * 2 + 34
    sheet = pygame.Surface((w, h))
    sheet.fill((24, 30, 24))
    _label(sheet, title, pad, 6, 18, (214, 236, 160))
    for i, f in enumerate(frames):
        sheet.blit(f, (pad + i * (size + pad), pad + 16))
        _label(sheet, params[i], pad + i * (size + pad), size + pad + 12,
               12, (150, 175, 150))
    return sheet


def main():
    out = os.path.join(ROOT, "tools", "_out")
    asset_dir = os.path.join(ROOT, "assets", "review")
    os.makedirs(out, exist_ok=True)
    os.makedirs(asset_dir, exist_ok=True)

    idle_f, idle_p = render_cycle("idle", 6)
    walk_f, walk_p = render_cycle("walk", 8)
    atk_f, atk_p = render_cycle("attack", 8)
    sw_f, sw_p = render_cycle("swing", 8)
    wind_f, wind_p = render_cycle("windrun", 6)
    hurt_f, hurt_p = render_cycle("hurt", 3)
    death_f, death_p = render_cycle("death", 4)

    sheets = (
        _compose("IDLE (6 fase)", idle_f, idle_p),
        _compose("WALK (8 fase)", walk_f, walk_p),
        _compose("ATTACK / TEMBAK (8 fase)", atk_f, atk_p),
        _compose("SWING / SAPUAN BUSUR MELEE (8 fase)", sw_f, sw_p),
        _compose("WINDRUN / DASH (6 fase)", wind_f, wind_p),
        _compose("HURT (3 fase)", hurt_f, hurt_p),
        _compose("DEATH (4 fase)", death_f, death_p),
    )

    w = max(s.get_width() for s in sheets)
    h = sum(s.get_height() for s in sheets) + 10 * (len(sheets) - 1)
    canvas = pygame.Surface((w, h))
    canvas.fill((18, 22, 18))
    y = 0
    for s in sheets:
        canvas.blit(s, (0, y))
        y += s.get_height() + 10

    out_path = os.path.join(out, "sylara_v1_anim_sheet.png")
    asset_path = os.path.join(asset_dir, "sylara_v1_anim_sheet.png")
    pygame.image.save(canvas, out_path)
    pygame.image.save(canvas, asset_path)
    print("saved:", out_path, "size", canvas.get_size())
    print("saved:", asset_path)


if __name__ == "__main__":
    main()
