"""Regenerate Thorne's HD swing frames from the HD attack sprite.

Context
-------
The previous ``assets/heroes/thorne_swing_<N>.png`` frames were baked from the
PROCEDURAL renderer (``_NS_thorne._draw_thorne_body``), a small pixel-art boar.
That clashes badly with the HD ``thorne_idle/walk/attack.png`` sprites (a large
detailed boar-warrior). Because ``_draw_thorne_attack`` prioritizes the swing
frames when they exist, the character visibly "switches" to the crude pixel-art
version during every normal attack.

The HD ``thorne_attack.png`` is a single STATIC frame (club raised overhead,
body hunched into the strike). It cannot be re-posed into a real club swing by
rotating or sliding the sprite -- rotating the whole body reads as "pecking the
ground", rotating the top band clips the club into the head, and moving only the
club detaches it from the hands. The genuine swing motion is supplied by the
RUNTIME: ``_draw_thorne_attack`` leans each frame with ``tilt``, lunges it with a
forward ``step``, and draws a yellow ``_draw_club_swing_trail`` crescent over the
body during the sweep.

So these frames keep the HD pose exactly and animate the TRANSLATION of the
whole character across the swing:
  * a forward lunge (the character plants forward on the sweep), and
  * a subtle vertical bob (crouch on impact).
Together with the runtime tilt + swing-trail this reads as a weighty HD club
swing, and every frame genuinely differs (the character visibly travels).

IMPORTANT: all frames are written at the SAME size and share one crop window so
the loader's mid-bottom anchor keeps the horizontal travel aligned between
frames.

The loader scales every frame to ``THORNE_SPRITE_HEIGHT`` (104) on load, so the
frames are baked at a modest resolution and then uniformly downscaled; because
all frames share one size and one scale factor, they stay consistent.

Run:  python tools/make_hd_swing.py
Output: assets/heroes/thorne_swing_<0..N>.png  (transparent, trimmed, same size)
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "heroes")

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1100, 900))

N = 8

# Forward lunge of the whole character per frame (px). Wind-up pulls back, the
# sweep drives forward, recovery settles back to neutral. In source space.
FOLLOW = (-22, -14, -5, 4, 11, 9, 4, 0)
# Vertical crouch/bob per frame (px), peaking at the sweep.
BOB = (0, 2, 3, 4, 3, 2, 1, 0)

# Output resolution: the loader scales everything to height 104 anyway, so bake
# at a moderate height to keep PNG size small.
BAKE_HEIGHT = 300


def trim(surf):
    bbox = surf.get_bounding_rect()
    if bbox is None or bbox.w <= 0 or bbox.h <= 0:
        return surf
    return surf.subsurface(bbox).copy()


def main():
    raw = pygame.image.load(os.path.join(OUT, "thorne_attack.png")).convert_alpha()
    src = trim(raw)
    w, h = src.get_size()

    # Canvas wide/tall enough for the whole lunge + bob, plus padding so the
    # swung sprite never touches the crop edge (0 alpha).
    pad_x = 40
    pad_top = 20
    pad_bottom = 10
    width = w + 2 * (max(FOLLOW) - min(FOLLOW) + pad_x)
    height = h + pad_top + pad_bottom
    ground = height - pad_bottom

    frames = []
    spans = []
    for i in range(N):
        canvas = pygame.Surface((width, height), pygame.SRCALPHA)
        rect = src.get_rect(midbottom=(width // 2 + FOLLOW[i], ground + BOB[i]))
        canvas.blit(src, rect)
        frames.append(canvas)
        spans.append(canvas.get_bounding_rect())

    # One shared crop window = union of all frames, so every frame is the SAME
    # size. This keeps the travel aligned when the loader re-anchors each frame at
    # mid-bottom.
    left = min(r.left for r in spans)
    top = min(r.top for r in spans)
    right = max(r.right for r in spans)
    bottom = max(r.bottom for r in spans)
    crop = pygame.Rect(left, top, right - left, bottom - top)

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
