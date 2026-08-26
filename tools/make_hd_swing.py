"""Regenerate Thorne's HD swing frames from the HD attack sprite.

Why this exists
---------------
The previous ``assets/heroes/thorne_swing_<N>.png`` frames were baked from the
PROCEDURAL renderer (``_NS_thorne._draw_thorne_body``), a small pixel-art boar.
That clashes badly with the HD ``thorne_idle/walk/attack.png`` sprites (a large
detailed boar-warrior). Because ``_draw_thorne_attack`` prioritizes the swing
frames when they exist, the character visibly "switches" to the crude pixel-art
version during every normal attack and the HD sprite disappears.

This tool rebuilds the swing frames from the HD attack sprite. Each frame slides
the sprite horizontally along the natural swing follow-through (the club and
hand travel across the body from wind-up to recovery), with a subtle vertical bob
and a small forward step. The body itself is NOT rotated here -- the runtime
already leans the whole frame (``tilt``) around its center, so baking rotation in
would double it.

IMPORTANT: all frames are written at the SAME size and share one crop window so
the loader's mid-bottom anchor preserves the horizontal movement between frames.
Feet sit on a fixed ground line (mid-bottom anchor, matching how the loader
blits with ``midbottom``), so the character stays planted while the club swings.

The loader scales every frame to ``THORNE_SPRITE_HEIGHT`` (104) on load, so the
frames are baked at a modest resolution (``BAKE_HEIGHT``) and then uniformly
downscaled. Because all frames share the same size and are scaled by the same
factor, the relative horizontal travel between frames is preserved.

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
# Horizontal follow-through travel amplitude (px in bake space). Keep it
# proportional to the bake height so motion stays the same at any resolution.
FOLLOW_PX = 0.165 * 726          # ~120 px at native attack height
# Small forward step (matches the runtime's `step` in _draw_thorne_attack).
STEP_PX = 3
# Horizontal/vertical padding so the swung sprite never touches the crop edge
# (0 alpha) and the ground line never gets cropped away.
PAD_X = 40
PAD_TOP = 20
PAD_BOTTOM = 10
# Output resolution: the loader scales everything to height 104 anyway, so bake
# at a moderate height to keep PNG size small without losing swing readability.
BAKE_HEIGHT = 340


def swing_offsets(progress):
    """Return (follow, step, bob) for a swing progress in [0, 1].

    follow: wind-up pulls the club back, the sweep drives it forward, recovery
    settles back to neutral.
    step:   small forward lunge, peaking mid-swing.
    bob:    subtle crouch, peaking mid-swing.
    """
    if progress < 0.25:
        t = progress / 0.25
        follow = -FOLLOW_PX * t                       # wind-up: club drawn back
    elif progress < 0.6:
        t = (progress - 0.25) / 0.35
        follow = -FOLLOW_PX + FOLLOW_PX * 2.0 * t     # sweep: drive forward
    else:
        t = (progress - 0.6) / 0.4
        follow = FOLLOW_PX - FOLLOW_PX * t            # recovery: settle back

    step = int(math.sin(progress * math.pi) * STEP_PX)
    bob = int(abs(math.sin(progress * math.pi)) * 8)
    return int(follow), step, bob


def main():
    raw = pygame.image.load(os.path.join(OUT, "thorne_attack.png")).convert_alpha()
    w, h = raw.get_size()

    # Build every frame on a canvas wide enough for the whole follow-through.
    width = w + 2 * (FOLLOW_PX + STEP_PX + PAD_X)
    height = h + PAD_TOP + PAD_BOTTOM
    ground = height - PAD_BOTTOM

    frames = []
    spans = []
    for i in range(N):
        progress = i / (N - 1.0)
        follow, step, bob = swing_offsets(progress)
        canvas = pygame.Surface((width, height), pygame.SRCALPHA)
        rect = raw.get_rect()
        # Character center-x sits at canvas center + follow + step; feet on ground.
        rect.midbottom = (width // 2 + follow + step, ground + bob)
        canvas.blit(raw, rect)
        frames.append(canvas)
        spans.append(canvas.get_bounding_rect())

    # One shared crop window = union of all frames, so every frame is the SAME
    # size. This is what keeps the horizontal swing movement aligned when the
    # loader re-anchors each frame at mid-bottom.
    left = min(r.left for r in spans)
    top = min(r.top for r in spans)
    right = max(r.right for r in spans)
    bottom = max(r.bottom for r in spans)
    crop = pygame.Rect(left, top, right - left, bottom - top)

    # Uniform downscale factor: all frames become the same size and are scaled
    # by the same amount, so the relative travel between frames is preserved.
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
