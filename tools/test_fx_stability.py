#!/usr/bin/env python3
"""Regression test: lapisan FX hero TIDAK BOLEH kedap-kedip.

Keluhan yang dikunci di sini:

    "skill fx sekarang kedap kedip tidak stabil"

Penyebabnya governor beban FX (PR "Perf: FX load governor") yang
menyelingi penggambaran lapisan FX hero antar-frame:

    load >= 0.92  -> gambar tiap frame
    0.60 .. 0.92  -> gambar 1 dari 2 frame
    load <  0.60  -> gambar 1 dari 3 frame  (beban combat ramai)

Karena offset fase-nya ``id(hero) & 0xFFFF``, tiap hero berkedip pada
frame yang berbeda-beda -> terlihat "kedap kedip tidak stabil", bahkan
saat hero sedang cast skill.

Kontrak baru: lapisan FX digambar SETIAP frame, apa pun beban combat.
Penghematan beban dilakukan lewat INTENSITAS (``Quality.particle_ratio``
= preset x ``fx_load()``), bukan lewat frekuensi gambar.

Jalankan:  python3 tools/test_fx_stability.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame                                          # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))

import heroes                                          # noqa: E402
from heroes import _ProbeEntity                        # noqa: E402
from mobile import perf                                # noqa: E402

FRAMES = 24
# Sampel: starter hero (kaizen/gornak) + boss-hero terbaru (level 6).
SAMPLE_HEROES = ("kaizen", "gornak", "thalgryn", "kunkka", "syrentha",
                 "gravewake")


def _casting_hero(hero_type):
    h = _ProbeEntity(hero_type, 200.0, 200.0)
    heroes._adapt_hero_to_boss(h)
    h._render_scale = 1.0
    h.alive = True
    h.radius = 38
    h.range = 160
    # Sedang cast skill: kondisi paling parah kalau FX diselingi.
    h.active_skill = "q"
    h.active_skill_timer = 40
    return h


def _fx_pixels_per_frame(hero_type, load, frames=FRAMES):
    """Jumlah piksel FX yang benar-benar tergambar per frame."""
    mod = heroes._live_fx_module(hero_type)
    if mod is None:                                     # pragma: no cover
        return None
    try:
        mod.reset_all()
    except Exception:
        pass
    h = _casting_hero(hero_type)
    try:
        mod.notify_skill_cast(h, "q")
    except Exception:
        pass

    surf = pygame.Surface((400, 400), pygame.SRCALPHA)
    out = []
    try:
        for _ in range(frames):
            # Governor dinyalakan seperti di Game.draw(), lalu beban
            # dikunci supaya pengukuran tidak digeser smoothing.
            heroes.begin_fx_frame(16)
            perf._FX_LOAD = load
            surf.fill((0, 0, 0, 0))
            heroes._live_fx_pre(hero_type, surf, h, 200, 200)
            heroes._live_fx_post(hero_type, surf, h, 200, 200)
            view = pygame.surfarray.pixels_alpha(surf)
            out.append(int((view > 0).sum()))
            del view
    finally:
        try:
            mod.reset_all()
        except Exception:
            pass
        perf.reset_fx_load()
    return out


# ══════════════════════════════════════════════════════════════════════
# 1. TIDAK ADA LAGI PEMILAHAN FRAME DI JALUR DRAW
# ══════════════════════════════════════════════════════════════════════
def test_tidak_ada_frame_skip_di_jalur_fx():
    src = open(os.path.join(ROOT, "heroes", "__init__.py"),
               encoding="utf-8").read()
    assert "_fx_skip_this_frame" not in src, \
        "layer FX masih diselingi antar-frame -> skill FX kedap-kedip"
    assert not hasattr(heroes, "_fx_skip_this_frame"), \
        "heroes._fx_skip_this_frame masih ada"

    import inspect
    for fn in (heroes._live_fx_pre, heroes._live_fx_post):
        body = inspect.getsource(fn)
        assert "draw_ground_layer" in body or "draw_live_layer" in body
        # tidak boleh ada cabang yang return sebelum menggambar
        assert "% 2" not in body and "% 3" not in body, \
            "%s masih menyelingi frame" % fn.__name__


# ══════════════════════════════════════════════════════════════════════
# 2. LAPISAN FX DIGAMBAR TIAP FRAME, APA PUN BEBAN COMBAT
# ══════════════════════════════════════════════════════════════════════
def test_fx_digambar_setiap_frame_saat_beban_penuh():
    for hero_type in SAMPLE_HEROES:
        got = _fx_pixels_per_frame(hero_type, 1.0)
        if got is None:
            continue
        kosong = [i for i, v in enumerate(got) if v == 0]
        assert not kosong, \
            "%s: frame %s kosong saat beban penuh" % (hero_type, kosong)


def test_fx_tidak_hilang_saat_beban_berat():
    """Beban combat ramai (fx_load 0.35) tidak boleh membuat FX lenyap.

    Di sinilah regresi lama muncul: 16 dari 24 frame kosong.
    """
    for hero_type in SAMPLE_HEROES:
        normal = _fx_pixels_per_frame(hero_type, 1.0)
        berat = _fx_pixels_per_frame(hero_type, 0.35)
        if normal is None or berat is None:
            continue
        kosong_normal = sum(1 for v in normal if v == 0)
        kosong_berat = sum(1 for v in berat if v == 0)
        assert kosong_berat == 0, \
            "%s: %d/%d frame FX kosong pada fx_load=0.35 (kedap-kedip)" % (
                hero_type, kosong_berat, len(berat))
        assert kosong_berat == kosong_normal, \
            "%s: beban combat mengubah jumlah frame yang digambar " \
            "(%d vs %d)" % (hero_type, kosong_berat, kosong_normal)


def test_fx_tidak_berkedip_selang_seling():
    """Pola zero-nonzero berselang = kedip. Harus nol kejadian."""
    for hero_type in SAMPLE_HEROES:
        for load in (0.92, 0.75, 0.55, 0.35):
            got = _fx_pixels_per_frame(hero_type, load)
            if got is None:
                continue
            kedip = sum(1 for a, b in zip(got, got[1:])
                        if (a == 0) != (b == 0))
            assert kedip == 0, \
                "%s @load %.2f: %d transisi nyala/mati (kedap-kedip)" % (
                    hero_type, load, kedip)


# ══════════════════════════════════════════════════════════════════════
# 3. GOVERNOR INTENSITAS TETAP HIDUP (penghematan tidak ikut dibuang)
# ══════════════════════════════════════════════════════════════════════
def test_token_spawn_hanya_saat_governor_aktif():
    """Cap spawn hanya hidup di loop game (begin_fx_frame).

    Tes combat memanggil ParticleSystem.spawn tanpa loop game; kalau
    token selalu dipotong, 280 spawn pertama menghabiskan anggaran
    proses-lebar dan tes hurt/burst berikutnya melihat 0 partikel.
    """
    perf.reset_fx_load()
    for _ in range(400):
        assert perf.claim_fx_particle(), \
            "tanpa begin_fx_frame token spawn tidak boleh habis"
        assert perf.allow_skill_projectile()
    heroes.begin_fx_frame(1)
    n = 0
    while perf.claim_fx_particle():
        n += 1
        if n > 10000:
            break
    assert 50 <= n <= 280, \
        "setelah begin_fx_frame token harus terbatas, dapat %d" % n
    perf.reset_fx_load()
    assert perf.claim_fx_particle()


def test_governor_intensitas_tetap_jalan():
    perf.reset_fx_load()
    assert perf.fx_load() == 1.0
    for _ in range(40):
        heroes.begin_fx_frame(16)          # 16 hero live-FX sibuk
    assert perf.fx_load() < 0.9, \
        "governor beban FX mati: fx_load=%r" % perf.fx_load()
    # Quality.particle_ratio ikut turun -> semua modul FX mengurangi
    # partikel tanpa satu pun frame dilewati.
    assert heroes.count_busy_fx_heroes(
        [_casting_hero(t) for t in SAMPLE_HEROES]) == len(SAMPLE_HEROES)
    perf.reset_fx_load()
    assert perf.fx_load() == 1.0


if __name__ == "__main__":
    gagal = 0
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS %s" % name)
            except AssertionError as exc:
                gagal += 1
                print("FAIL %s: %s" % (name, exc))
    perf.reset_fx_load()
    if gagal:
        print("\n%d test gagal" % gagal)
        sys.exit(1)
    print("\nSemua test kestabilan FX lolos")
    sys.exit(0)
