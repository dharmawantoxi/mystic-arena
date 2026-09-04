#!/usr/bin/env python3
"""Benchmark biaya draw FX tiap hero (heroes/*_fx.py).

Output utama:
  - ms/frame rata-rata untuk FX seorang hero (ground + live layer)
  - jumlah partikel hidup
  - perkiraan berapa banyak hero sekaligus yang masih muat di budget 16.7 ms

Dipakai untuk menjawab pertanyaan: "FX mana yang paling banyak
berpengaruh ke lag?" Angka di PC headless bersifat relatif (bukan
angka HP), tapi cukup untuk membandingkan modul FX satu sama lain.

Jalankan:
    python3 tools/bench_fx_heroes.py --frames 60
    python3 tools/bench_fx_heroes.py --frames 60 --multi 4
"""

import argparse
import importlib
import math
import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

ap = argparse.ArgumentParser()
ap.add_argument("--frames", type=int, default=60)
ap.add_argument("--multi", type=int, default=1,
                help="jumlah hero live-FX berbarengan untuk tiap modul")
ap.add_argument("--quality", default="high",
                choices=["low", "medium", "high"])
ap.add_argument("--load", type=float, default=1.0,
                help="fx_load() yang dikunci (1.0 penuh, 0.35 beban berat)")
ap.add_argument("--profile", default=None,
                help="profil hero tertentu lalu cetak 20 fungsi terpanas")
args = ap.parse_args()

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

from mobile import perf  # noqa: E402

perf.install_font_cache()
perf.Quality.apply(args.quality)
perf._FX_LOAD = float(args.load)

import heroes  # noqa: E402
from heroes import _ProbeEntity  # noqa: E402

FRAMES = max(10, int(args.frames))
MULTI = max(1, int(args.multi))
SURF_W, SURF_H = 1280, 720
SURF = pygame.Surface((SURF_W, SURF_H), pygame.SRCALPHA)
BUDGET_MS = 16.7

# Zephyr tidak menerima dt di tick() sehingga kita kendalikan jam SDL.
_FAKE_TICKS = {"now": 1000}


def _fake_get_ticks():
    return int(_FAKE_TICKS["now"])


_ORIG_GET_TICKS = pygame.time.get_ticks
pygame.time.get_ticks = _fake_get_ticks


def _cast_hero(hero_type):
    h = _ProbeEntity(hero_type, 320.0, 360.0)
    heroes._adapt_hero_to_boss(h)
    h._render_scale = 1.0
    h.alive = True
    h.radius = 38
    h.range = 160
    h.active_skill = "q"
    h.active_skill_timer = 40
    return h


def _notify_all(mod, h):
    """Cast seluruh skill + beberapa impact supaya skenario paling padat."""
    for skill in ("q", "w", "e", "r"):
        try:
            mod.notify_skill_cast(h, skill)
        except TypeError:
            mod.notify_skill_cast(h, skill, x=h.x, y=h.y)
        except Exception:
            pass
    for skill in ("q", "w"):
        try:
            mod.notify_skill_impact(h, h.x + 80, h.y, radius=70, skill=skill)
        except TypeError:
            mod.notify_skill_impact(h, h.x + 80, h.y, radius=70)
        except Exception:
            pass


def _tick_module(mod, dt):
    try:
        mod.tick(dt)
    except TypeError:
        # modul tanpa argumen dt (mis. zephyr) memakai jam SDL yang kita
        # naikkan satu langkah justru di luar.
        try:
            mod.tick()
        except Exception:
            pass
    except Exception:
        pass


def bench_one(hero_type):
    mod = heroes._live_fx_module(hero_type)
    if mod is None:
        return None
    try:
        mod.reset_all()
    except Exception:
        pass

    heroes_units = [_cast_hero(hero_type) for _ in range(MULTI)]
    for h in heroes_units:
        _notify_all(mod, h)

    # Pemanasan: buat state FX matang (partikel sudah menyebar),
    # lalu ukur pada kondisi rata-rata (bukan ledakan awal yang ekstrem).
    for _ in range(30):
        _FAKE_TICKS["now"] += 17
        _tick_module(mod, 1.0 / 60.0)
        SURF.fill((0, 0, 0, 0))
        for h in heroes_units:
            try:
                mod.draw_ground_layer(SURF, h, int(h.x), int(h.y))
                mod.draw_live_layer(SURF, h, int(h.x), int(h.y))
            except Exception:
                pass

    n = 0
    t0 = time.perf_counter()
    for _ in range(FRAMES):
        _FAKE_TICKS["now"] += 17
        SURF.fill((0, 0, 0, 0))
        # update sekali per frame, lalu gambar. draw_ground_layer pada
        # sebagian modul memanggil tick() sendiri, tapi guard jam membuatnya
        # tidak menggandakan langkah.
        _tick_module(mod, 1.0 / 60.0)
        for h in heroes_units:
            try:
                mod.draw_ground_layer(SURF, h, int(h.x), int(h.y))
                mod.draw_live_layer(SURF, h, int(h.x), int(h.y))
            except Exception:
                pass
        n += 1
    dt_ms = (time.perf_counter() - t0) / n * 1000.0

    particles = getattr(mod, "total_particles", lambda: 0)()
    projectiles = 0
    stats = getattr(mod, "stats", None)
    if callable(stats):
        try:
            st = stats()
            projectiles = int(st.get("projectiles", 0))
        except Exception:
            pass

    try:
        mod.reset_all()
    except Exception:
        pass

    per_hero = dt_ms / max(1, MULTI)
    room = BUDGET_MS / max(dt_ms, 0.0001) if dt_ms > 0 else 999
    return {
        "hero": hero_type,
        "ms_frame": dt_ms,
        "ms_per_hero": per_hero,
        "particles": particles,
        "projectiles": projectiles,
        "units": MULTI,
        "budget_room": room,
    }


def profile_hero(hero_type, frames=60):
    import cProfile
    import io
    from pstats import Stats

    mod = heroes._live_fx_module(hero_type)
    if mod is None:
        return
    try:
        mod.reset_all()
    except Exception:
        pass
    heroes_units = [_cast_hero(hero_type) for _ in range(MULTI)]
    for h in heroes_units:
        _notify_all(mod, h)
    for _ in range(30):
        _FAKE_TICKS["now"] += 17
        _tick_module(mod, 1.0 / 60.0)
        SURF.fill((0, 0, 0, 0))
        for h in heroes_units:
            try:
                mod.draw_ground_layer(SURF, h, int(h.x), int(h.y))
                mod.draw_live_layer(SURF, h, int(h.x), int(h.y))
            except Exception:
                pass

    pr = cProfile.Profile()
    pr.enable()
    for _ in range(frames):
        _FAKE_TICKS["now"] += 17
        SURF.fill((0, 0, 0, 0))
        _tick_module(mod, 1.0 / 60.0)
        for h in heroes_units:
            try:
                mod.draw_ground_layer(SURF, h, int(h.x), int(h.y))
                mod.draw_live_layer(SURF, h, int(h.x), int(h.y))
            except Exception:
                pass
    pr.disable()
    s = io.StringIO()
    Stats(pr, stream=s).sort_stats("tottime").print_stats(22)
    print(s.getvalue())
    try:
        mod.reset_all()
    except Exception:
        pass


def main():
    if args.profile:
        print("PROFIL %s (units=%d, frames=%d)" % (
            args.profile, MULTI, args.frames))
        profile_hero(args.profile, max(30, args.frames))
        pygame.time.get_ticks = _ORIG_GET_TICKS
        return
    rows = []
    for hero_type in sorted(heroes._LIVE_FX_HEROES):
        r = bench_one(hero_type)
        if r is None:
            continue
        rows.append(r)
        print(("%-22s  %7.3f ms  (%5.3f ms/hero)  "
               "partikel=%5d  proyektil=%3d  muat-budget=%5.2fx"
               % (hero_type, r["ms_frame"], r["ms_per_hero"],
                  r["particles"], r["projectiles"], r["budget_room"])))

    print("\n=== RANGKUMAN ===")
    print("quality=%s  fx_load=%.2f  units/modul=%d  frames=%d  surf=%dx%d"
          % (args.quality, perf._FX_LOAD, MULTI, FRAMES, SURF_W, SURF_H))
    rows.sort(key=lambda r: r["ms_frame"], reverse=True)
    top = 12
    print("\nTop %d FX paling berat (ms/frame):" % min(top, len(rows)))
    for i, r in enumerate(rows[:top], 1):
        print("%2d. %-22s %7.3f ms  (%5.3f ms/hero, %d partikel)"
              % (i, r["hero"], r["ms_frame"], r["ms_per_hero"],
                 r["particles"]))

    if args.load != 1.0:
        print("\nCatatan: beban diukur pada fx_load=%.2f."
              % args.load)

    pygame.time.get_ticks = _ORIG_GET_TICKS


if __name__ == "__main__":
    main()
