"""One-off: bake Thorne swing + skill FX menjadi sprite PNG transparan.

Tulis  assets/heroes/thorne_swing_<0..N>.png   (frame animasi swing)
Tulis  assets/heroes/thorne_skill_<q/w/e/r>.png (efek skill Q/W/E/R)

Sumber gambar = renderer prosedural lama (heroes/_bundle.py -> _NS_thorne).
Hasilnya sprite transparan dengan gaya yang sama seperti aset hero HD /
icon item, sehingga di runtime di-load lewat cache + fallback prosedural.

Frame swing di-trim (buang border transparan) lalu di-scale ke tinggi
THORNE_SPRITE_HEIGHT saat di-load, jadi konsisten dgn sprite idle/walk.
Efek skill TIDAK di-trim supaya anchor (pusat) tetap sejajar saat
kita blit di (x, y) karakter.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((240, 240))

import heroes._bundle as _b  # noqa: E402

NS = _b._NS_thorne

OUT = os.path.join(ROOT, "assets", "heroes")
SWING_FRAMES = 8
CAN = 210


class ProbeSkill:
    """Objek mirip Hero secukupnya untuk efek skill Thorne."""

    def __init__(self, direction=1):
        self.x = 0.0
        self.y = 0.0
        self.pulse = 12.0
        self.direction = direction
        self.facing = direction
        self.target = None
        self._th_spray_last = -100
        self._th_goo_spawned = False
        self._th_projectiles = []
        self.range = 60


def trim(surf):
    bbox = surf.get_bounding_rect()
    if bbox is None or bbox.w <= 0 or bbox.h <= 0:
        return surf
    return surf.subsurface(bbox).copy()


def make_swing_frames():
    cx, cy = CAN // 2, CAN // 2
    make_dir = os.path.join(OUT, "hero_swing_tmp")
    if not os.path.isdir(OUT):
        os.makedirs(OUT, exist_ok=True)
    for i in range(SWING_FRAMES):
        prog = i / float(SWING_FRAMES - 1)
        surf = pygame.Surface((CAN, CAN), pygame.SRCALPHA)
        NS._draw_thorne_body(surf, cx, cy, 1, 12.0, "attack", prog, False)
        cropped = trim(surf)
        path = os.path.join(OUT, "thorne_swing_%d.png" % i)
        pygame.image.save(cropped, path)
        print("  swing frame %d/%d -> %s  (%dx%d)" % (i + 1, SWING_FRAMES, path,
                                                      cropped.get_width(), cropped.get_height()))


def make_skill_sprites():
    cx, cy = CAN // 2, CAN // 2
    probe = ProbeSkill(1)
    specs = [
        # (key, draw_func, timer, dur)
        ("q", ["_draw_viscous_charge"], 30, 40),
        ("w", ["_draw_bristleback_effect"], 50, 100),
        ("e", ["_handle_quill_spray_skill"], 40, 60),
        ("r", ["_draw_warpath_effect"], 60, 120),
    ]
    for key, func_names, timer, dur in specs:
        surf = pygame.Surface((CAN, CAN), pygame.SRCALPHA)
        for fn in func_names:
            getattr(NS, fn)(surf, probe, cx, cy, timer, 12.0)
        # Jangan trim: pertahankan anchor (cx,cy) => blit center di (x,y).
        path = os.path.join(OUT, "thorne_skill_%s.png" % key)
        pygame.image.save(surf, path)
        print("  skill %s -> %s  (%dx%d)" % (key, path, surf.get_width(), surf.get_height()))


def main():
    print("Bake Thorne swing frames (%d) ..." % SWING_FRAMES)
    make_swing_frames()
    print("Bake Thorne skill FX (q/w/e/r) ...")
    make_skill_sprites()
    print("Selesai ->", OUT)


if __name__ == "__main__":
    main()
