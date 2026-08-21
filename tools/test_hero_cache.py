"""
tools/test_hero_cache.py

Mengukur AKIBAT dari `Quality.cheap_alpha` terhadap cache sprite hero.

Kenapa ini penting
──────────────────
Di v22 saya menyalakan `cheap_alpha = True` begitu jalur cepat alpha
aktif. Akibatnya di perangkat:

    v21  hemat:ON    e.hero   2 ms  (1 hero)
    v22  hemat:off   e.hero 294 ms  (3 hero)  = 98 ms per hero

Dugaan penyebabnya bukan efek grafisnya, melainkan satu baris di
heroes/__init__.py:

    _q = 1 if _Qk.cheap_alpha else 2

`_q` adalah pengali kuantisasi kunci cache. Dengan _q=1 jumlah kunci
berlipat, cache meleset terus, dan setiap meleset berarti render penuh
+ get_bounding_rect + smoothscale.

Skrip ini membuktikan dugaan itu dengan angka, bukan argumen.

Jalankan:  python3 tools/test_hero_cache.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame                                            # noqa: E402

pygame.init()
pygame.display.set_mode((1280, 720))

import heroes                                            # noqa: E402
from mobile.perf import Quality                          # noqa: E402

TIPE = ["grimjaw", "sylara", "kaizen"]
FPS_GAMBAR = 8               # seperti di HP
LANGKAH_PER_FRAME = 60 // FPS_GAMBAR
FRAME = 150


class FakeHero:
    def __init__(self, tipe):
        self.hero_type = tipe
        self.attack_cooldown = 40
        self.attack_timer = 0
        self.timer = 0
        self.x = 640.0
        self.y = 360.0
        self.facing = 1
        self.direction = 1
        self.alive = True
        self.hp = 100
        self.max_hp = 100
        self.level = 3
        self.radius = 16
        self.pulse = 0.0
        self.active_skill = None
        self.active_skill_timer = 0
        self.team = "blue"
        self.projectiles = []
        self.target = None
        self.damage = 10
        self.range = 90


def jalankan(cheap_alpha):
    Quality.cheap_alpha = cheap_alpha
    Quality.use_colorkey_sprites = False
    heroes.clear_hero_sprite_cache()
    heroes._hero_cache_stats["hits"] = 0
    heroes._hero_cache_stats["misses"] = 0

    surf = pygame.Surface((1280, 720), 0, 32,
                          (0x00FF0000, 0x0000FF00, 0x000000FF, 0))
    pahlawan = [FakeHero(t) for t in TIPE]

    t0 = time.perf_counter()
    for _ in range(FRAME):
        for _ in range(LANGKAH_PER_FRAME):
            for h in pahlawan:
                h.pulse += 0.08
                if h.attack_timer > 0:
                    h.attack_timer -= 1
                else:
                    h.attack_timer = h.attack_cooldown
                h.timer = h.attack_timer
        for h in pahlawan:
            heroes.render_hero(h.hero_type, surf, h, 640, 360)
    dt = time.perf_counter() - t0

    st = heroes.hero_cache_stats()
    total = st["hits"] + st["misses"]
    hit = 100.0 * st["hits"] / total if total else 0.0
    per_hero_ms = dt * 1000.0 / (FRAME * len(pahlawan))
    return hit, st["misses"], per_hero_ms, st.get("entries", 0)


def main():
    print("%d frame gambar @ %d FPS, %d hero, kuantisasi animasi berbeda.\n"
          % (FRAME, FPS_GAMBAR, len(TIPE)))
    print("  %-28s %-9s %-8s %-12s %s"
          % ("mode", "hit rate", "miss", "ms/hero", "entri cache"))

    hasil = {}
    for label, ca in (("cheap_alpha=True  (v22)", True),
                      ("cheap_alpha=False (v23)", False)):
        hit, miss, ms, entri = jalankan(ca)
        hasil[ca] = (hit, miss, ms)
        print("  %-28s %6.1f%%   %-8d %-12.2f %d"
              % (label, hit, miss, ms, entri))

    print()
    lambat = hasil[True][2]
    cepat = hasil[False][2]
    if cepat <= 0:
        print("HASIL: pengukuran tidak valid.")
        return 1
    print("Mode hemat membuat gambar hero %.1fx lebih murah "
          "(%.2f ms -> %.2f ms per hero)." % (lambat / cepat, lambat, cepat))
    if lambat > cepat:
        print("HASIL: TERBUKTI - cheap_alpha=True adalah penyebab "
              "regresi e.hero di v22.")
        return 0
    print("HASIL: tidak terbukti pada mesin ini "
          "(cache mungkin sudah panas / hero tidak beranimasi).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
