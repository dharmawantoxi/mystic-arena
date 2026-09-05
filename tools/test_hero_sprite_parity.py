# ================================
# tools/test_hero_sprite_parity.py
# Uji paritas: sprite hero hasil jalur v32 (canvas dipelajari + kotak
# crop di-cache) harus IDENTIK piksel-per-piksel dengan jalur lama
# (canvas sebesar jangkauan serang + get_bounding_rect tiap miss).
#
# Kenapa uji ini ada: optimasi v32 memperkecil canvas sprite hero dari
# "sebesar jangkauan serang" (rata-rata 434x434) menjadi "sebesar isi
# yang benar-benar tergambar". Kalau perhitungan ukurannya salah, FX
# hero akan TERPOTONG tepi canvas - kerusakan visual yang tidak
# ditangkap oleh pengukur kecepatan mana pun.
#
#   python3 tools/test_hero_sprite_parity.py
#   python3 tools/test_hero_sprite_parity.py --quality high
# ================================
import os
import sys
import argparse

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MYSTIC_DEBUG", "0")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ap = argparse.ArgumentParser()
ap.add_argument("--quality", default="low",
                choices=["low", "medium", "high"])
ap.add_argument("--poses", type=int, default=8)
ap.add_argument("--bosses", type=int, default=24,
                help="berapa boss-as-hero (BOSS_RENDERERS) ikut diuji; "
                     "0 = hanya hero unlock")
a = ap.parse_args()

import pygame  # noqa: E402
pygame.init()
pygame.display.set_mode((1280, 720))

import _core  # noqa: E402,F401
from mobile import perf  # noqa: E402
perf.install_font_cache()
perf.Quality.apply(a.quality)
from _entity import Hero  # noqa: E402
import heroes as H  # noqa: E402


class _Target:
    alive = True

    def __init__(self, x, y):
        self.x, self.y = x, y


def _siapkan(hero_type, pose):
    """Satu hero pada satu pose tertentu (idle / attack / skill)."""
    h = Hero(hero_type, "blue", 640, 360)
    kind = pose % 3
    h.pulse = 0.13 * pose
    h.attack_timer = 0
    h.active_skill = None
    h.active_skill_timer = 0
    h._pose_variant = pose % 2
    if kind == 1:
        h.attack_timer = 3 + (pose % 11)
    elif kind == 2:
        h.active_skill = "q"
        h.active_skill_timer = 12 + pose * 9
    # Beri FX hidup supaya lapisan tanah/atas ikut tergambar ke canvas.
    mod = H._live_fx_module(hero_type)
    if mod is not None:
        for hook in ("notify_melee_impact", "notify_projectile_impact"):
            fn = getattr(mod, hook, None)
            if fn is not None:
                try:
                    fn(h, _Target(h.x + 24, h.y - 6), damage=90)
                except TypeError:
                    try:
                        fn(h, h.x + 24, h.y - 6, 0.7, 120)
                    except Exception:
                        pass
                except Exception:
                    pass
    return h


def _render(hero_type, hero, pose):
    key = (hero_type, "blue", 1, 1, "skill" if hero.active_skill
           else ("atk" if hero.attack_timer else "idle"), pose)
    renderer = (H.HERO_RENDERERS.get(hero_type)
                or H.BOSS_RENDERERS.get(hero_type))
    if renderer is None:
        return None
    out = H._hero_render_sprite(key, hero_type, hero, renderer)
    if out is False or out is None:
        return None
    return out


def main():
    types = sorted(H.HERO_RENDERERS)
    if not types:
        print("tidak ada renderer hero - uji dilewati")
        return 0
    # Boss yang bisa dibuka jadi hero memakai renderer boss. Diambil
    # sampel merata supaya 216 boss tidak membuat uji ini berjam-jam.
    ekstra = sorted(set(H.BOSS_RENDERERS) - set(H.HERO_RENDERERS))
    if a.bosses > 0 and ekstra:
        langkah = max(1, len(ekstra) // a.bosses)
        types = types + ekstra[::langkah][:a.bosses]

    beda = []
    diperiksa = 0
    for ht in types:
        for pose in range(a.poses):
            # ── jalur BARU (v32) ──
            H._HERO_GEOM_ON = True
            H._HERO_CANVAS_LEARN_ON = True
            H.clear_hero_geom_cache()
            baru = _render(ht, _siapkan(ht, pose), pose)

            # ── jalur LAMA: canvas penuh + bounding rect tiap miss ──
            H._HERO_GEOM_ON = False
            H._HERO_CANVAS_LEARN_ON = False
            H.clear_hero_geom_cache()
            lama = _render(ht, _siapkan(ht, pose), pose)

            H._HERO_GEOM_ON = True
            H._HERO_CANVAS_LEARN_ON = True

            if baru is None and lama is None:
                continue
            diperiksa += 1
            if (baru is None) != (lama is None):
                beda.append("%s pose %d: salah satu jalur kosong" % (ht, pose))
                continue
            s_baru, ax_b, ay_b = baru
            s_lama, ax_l, ay_l = lama
            if s_baru.get_size() != s_lama.get_size():
                beda.append("%s pose %d: ukuran beda %s vs %s"
                            % (ht, pose, s_baru.get_size(),
                               s_lama.get_size()))
                continue
            if (int(ax_b), int(ay_b)) != (int(ax_l), int(ay_l)):
                beda.append("%s pose %d: anchor beda (%.1f,%.1f) vs (%.1f,%.1f)"
                            % (ht, pose, ax_b, ay_b, ax_l, ay_l))
                continue
            # Bandingkan piksel (termasuk kanal alpha).
            import numpy as np
            arr_b = pygame.surfarray.pixels_alpha(s_baru).copy()
            arr_l = pygame.surfarray.pixels_alpha(s_lama).copy()
            rgb_b = pygame.surfarray.array3d(s_baru)
            rgb_l = pygame.surfarray.array3d(s_lama)
            selisih = int(np.abs(rgb_b.astype(int) - rgb_l.astype(int)).max())
            selisih_a = int(np.abs(arr_b.astype(int) - arr_l.astype(int)).max())
            if selisih > 0 or selisih_a > 0:
                beda.append("%s pose %d: piksel beda (rgb %d, alpha %d)"
                            % (ht, pose, selisih, selisih_a))

    print("")
    print("kualitas=%s  %d tipe hero x %d pose = %d kombinasi diperiksa"
          % (a.quality, len(types), a.poses, diperiksa))
    hemat = sorted(H._HERO_CANVAS_HALF.items(), key=lambda kv: kv[1])
    if hemat:
        print("canvas v32 : %d-%d px   (jalur lama: %d-%d px)"
              % (hemat[0][1] * 2, hemat[-1][1] * 2,
                 min(H._canvas_size_for(Hero(t, "blue", 0, 0))
                     for t in types[:12]),
                 max(H._canvas_size_for(Hero(t, "blue", 0, 0))
                     for t in types[:12])))
    if beda:
        print("")
        for b in beda[:25]:
            print("  BEDA  %s" % b)
        print("GAGAL: %d dari %d kombinasi berbeda" % (len(beda), diperiksa))
        return 1
    print("OK - sprite hero IDENTIK dengan jalur lama di semua kombinasi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
