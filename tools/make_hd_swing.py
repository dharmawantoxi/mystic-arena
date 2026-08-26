"""Regenerate Thorne's HD swing frames from the HD attack sprite.

Why this exists
---------------
The previous ``assets/heroes/thorne_swing_<N>.png`` frames were baked from the
PROCEDURAL renderer (``_NS_thorne._draw_thorne_body``), a small pixel-art boar.
That clashes badly with the HD ``thorne_idle/walk/attack.png`` sprites (a large
detailed boar-warrior). Because ``_draw_thorne_attack`` prioritizes the swing
frames when they exist, the character visibly "switches" to the crude pixel-art
version during every normal attack and the HD sprite disappears.

This tool rebuilds the swing frames from the HD attack sprite and creates a real
SWING arc:

  * The whole body is ROTATED about a pivot near the feet so the character leans
    back on the wind-up, whips forward through the sweep, and settles on the
    recovery -- the club travels in a genuine arc, not just a horizontal slide.
  * A small forward ``step`` (matching the runtime's ``step`` in
    ``_draw_thorne_attack``) adds momentum.

The runtime additionally leans each frame (``tilt``) around its own center when
blitting, so keep the baked lean modest to avoid doubling it.

IMPORTANT: all frames are written at the SAME size and share one crop window so
the loader's mid-bottom anchor preserves the relative transform between frames.
Feet sit on a fixed ground line (mid-bottom anchor, matching how the loader
blits with ``midbottom``), so the character stays planted while it swings.

The loader scales every frame to ``THORNE_SPRITE_HEIGHT`` (104) on load, so the
frames are baked at a modest resolution and then uniformly downscaled; because
all frames share one size and one scale factor, the relative motion is preserved.

Run:  python tools/make_hd_swing.py
Output: assets/heroes/thorne_swing_<0..N>.png  (transparent, trimmed, same size)
"""
import os
import math

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "heroes")

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1200, 1000))

N = 8
# Pivot: fraction of the sprite width/height. Near the feet/centre so the
# character leans about its base and the feet stay planted.
PIVOT_X = 0.50
PIVOT_Y = 0.95
# Lean angle (degrees). The loader's own `tilt` is small (6 deg peak), so a
# slightly larger baked arc reads clearly without looking broken.
WINDUP_DEG = -10.0   # club drawn back (wind-up)
SWEEP_DEG = 16.0     # whipped forward (sweep)
# Small forward step (matches the runtime's `step` in _draw_thorne_attack).
STEP_PX = 4
# Padding so the swung sprite never touches the crop edge (0 alpha).
PAD_X = 40
PAD_TOP = 20
PAD_BOTTOM = 10
# Output resolution: the loader scales everything to height 104 anyway, so bake
# at a moderate height to keep PNG size small without losing swing readability.
BAKE_HEIGHT = 340


def lean_angle(progress):
    """Body lean in degrees over a swing progress in [0, 1]."""
    if progress < 0.25:
        t = progress / 0.25
        return WINDUP_DEG * t                    # wind-up: draw back
    if progress < 0.6:
        t = (progress - 0.25) / 0.35
        return WINDUP_DEG + (SWEEP_DEG - WINDUP_DEG) * t   # sweep: whip forward
    t = (progress - 0.6) / 0.4
    return SWEEP_DEG * (1.0 - t)                 # recovery: settle back


def rot_at_about(src, angle, pivot_xy):
    """Rotate a SRCALPHA surface about a pivot (px in source coords), returning
    (rotated_surface, pivot_pos_in_rotated)."""
    pw, ph = pivot_xy
    ox, oy = src.get_size()[0] / 2.0, src.get_size()[1] / 2.0
    dx, dy = pw - ox, ph - oy
    rot = pygame.transform.rotozoom(src, angle, 1.0)
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    ndx = dx * ca + dy * sa
    ndy = -dx * sa + dy * ca
    return rot, (rot.get_width() / 2.0 + ndx, rot.get_height() / 2.0 + ndy)


def trim(surf):
    bbox = surf.get_bounding_rect()
    if bbox is None or bbox.w <= 0 or bbox.h <= 0:
        return surf
    return surf.subsurface(bbox).copy()


def main():
    raw = pygame.image.load(os.path.join(OUT, "thorne_attack.png")).convert_alpha()
    src = trim(raw)
    w, h = src.get_size()
    pivot = (w * PIVOT_X, h * PIVOT_Y)

    # Build every frame on a canvas large enough for the rotate + step.
    width = w + 2 * (PAD_X + STEP_PX + int(w * 0.2))
    height = h + PAD_TOP + PAD_BOTTOM + int(h * 0.2)
    ground = height - PAD_BOTTOM

    frames = []
    spans = []
    for i in range(N):
        progress = i / (N - 1.0)
        angle = lean_angle(progress)
        rot, pivot_pos = rot_at_about(src, angle, pivot)
        step = int(math.sin(progress * math.pi) * STEP_PX)

        canvas = pygame.Surface((width, height), pygame.SRCALPHA)
        # Place the pivot so the feet land on the ground line at canvas centre-x
        # (+ step). This plants the feet while the body leans around them.
        bx = int(width / 2.0 + step - pivot_pos[0])
        by = int(ground - pivot_pos[1])
        canvas.blit(rot, (bx, by))
        frames.append(canvas)
        spans.append(canvas.get_bounding_rect())

    # One shared crop window = union of all frames, so every frame is the SAME
    # size. This keeps the swing motion aligned when the loader re-anchors each
    # frame at mid-bottom.
    left = min(r.left for r in spans)
    top = min(r.top for r in spans)
    right = max(r.right for r in spans)
    bottom = max(r.bottom for r in spans)
    crop = pygame.Rect(left, top, right - left, bottom - top)

    # Uniform downscale factor so PNGs stay small.
    scale = BAKE_HEIGHT / float(crop.height)
    out_w = max(1, int(round(crop.width * scale)))
    out_h = max(1, int(round(crop.height * scale)))

    for i, canvas in enumerate(frames):
        cropped = canvas.subsurface(crop).copy()
        if abs(scale - 1.0) >= 0.01:
            cropped = pygame.transform.smoothscale(cropped, (out_w, out_h))
        path = os.path.join(OUT, "thorne_swing_%d.png" % i)
        pygame.image.save(cropped, path)
        print("  swing %d/%d -> %s (%dx%d)" % (i + 1, N, path,
                                               cropped.get_width(),
                                               cropped.get_height()))


if __name__ == "__main__":
    main()
