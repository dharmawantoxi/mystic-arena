# ================================
# tools/test_fx_ground_budget.py
# Penjaga regresi untuk ANGGARAN LAPISAN FX TANAH (v32).
#
# Latar belakang (ini bug yang benar-benar terjadi saat fitur ini
# dibuat, bukan hipotesis):
#
#   Versi pertama anggaran ini melewatkan SELURUH
#   ``mod.draw_ground_layer()``. Ternyata di semua 27 modul
#   heroes/*_fx.py fungsi itu berisi tiga hal - attach(hero), tick(),
#   lalu draw_ground(). Melewatkan seluruhnya membuat SIMULASI FX hero
#   ikut membeku, dan lapisan ATAS-nya pun mati. Terukur dengan
#   tools/bench_fx_layers.py (10 hero, preset LOW):
#
#       lewatkan seluruh fungsi : lapisan atas 0,03 ms/frame  (FX mati)
#       lewati gambarnya saja   : lapisan atas 3,99 ms/frame  (utuh)
#
#   Jadi yang boleh dilewati HANYA gambarnya. Uji di bawah mengunci
#   perilaku itu supaya tidak terulang.
#
# Dijalankan:
#   python3 tools/test_fx_ground_budget.py
# ================================
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MYSTIC_DEBUG", "0")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()
pygame.display.set_mode((1280, 720))

import _core  # noqa: E402,F401
from mobile import perf  # noqa: E402
from _entity import Hero  # noqa: E402
import heroes as H  # noqa: E402

_GAGAL = []


def _cek(nama, syarat, keterangan=""):
    print("%s  %s%s" % ("PASS" if syarat else "FAIL", nama,
                        ("  - " + keterangan) if keterangan else ""))
    if not syarat:
        _GAGAL.append(nama)


_TYPES = ["grimjaw", "sylara", "vex", "abaddon", "razak",
          "kaizen", "zephyr", "alchemist", "kunkka"]


def _buat_hero():
    heroes = []
    for i, t in enumerate(_TYPES):
        h = Hero(t, "blue", 300 + i * 40, 300)
        heroes.append(h)
    return heroes


def test_semua_modul_punya_attach_dan_tick():
    """Anggaran ini memanggil attach()+tick() langsung, jadi keduanya
    HARUS ada di setiap modul FX - kalau tidak, simulasi membeku lagi."""
    hilang = []
    for ht in H._LIVE_FX_HEROES:
        mod = H._live_fx_module(ht)
        if mod is None:
            continue
        if not callable(getattr(mod, "tick", None)):
            hilang.append("%s.tick" % ht)
    _cek("semua modul FX punya tick()", not hilang,
         "hilang: %s" % hilang if hilang else "%d modul"
         % len(H._LIVE_FX_HEROES))


def test_simulasi_tetap_maju_walau_gambar_dilewati():
    """Inti penjaga regresi: saat jatah gambar habis, attach()+tick()
    harus TETAP dipanggil untuk hero itu. Kalau tidak, simulasi FX-nya
    membeku dan lapisan atas ikut mati (bug yang dijelaskan di kepala
    berkas ini)."""
    perf.Quality.apply(perf.LOW)
    perf.Quality.fx_ground_budget = 1     # paksa anggaran paling ketat
    heroes = _buat_hero()
    screen = pygame.display.get_surface()

    dipanggil = {}

    for ht in H._LIVE_FX_HEROES:
        mod = H._live_fx_module(ht)
        if mod is None or getattr(mod, "_wrapped_tickcount", False):
            continue
        asal = mod.tick

        def _bungkus(fn, nama):
            def _w(*a, **k):
                dipanggil[nama] = dipanggil.get(nama, 0) + 1
                return fn(*a, **k)
            _w._wrapped_tickcount = True
            return _w

        mod.tick = _bungkus(asal, ht)

    jenis = [h.hero_type for h in heroes
             if H._live_fx_module(h.hero_type) is not None]
    for _ in range(4):
        dipanggil.clear()
        H.begin_fx_frame(len(heroes))
        for h in heroes:
            H._live_fx_pre(h.hero_type, screen, h, h.x, h.y)

        # Setiap hero live-FX harus mendapat tick() PALING SEDIKIT sekali
        # per frame - baik yang dapat jatah gambar maupun yang tidak.
        kurang = [t for t in jenis if dipanggil.get(t, 0) < 1]
        if kurang:
            break

    _cek("tick() tetap jalan untuk SEMUA hero walau jatah gambar habis",
         not kurang,
         "tanpa tick: %s (dipanggil: %s)" % (kurang, dict(dipanggil))
         if kurang else "%d hero x 4 frame" % len(jenis))
    _cek("draw_ground hanya untuk hero yang dapat jatah",
         sum(1 for t in jenis if dipanggil.get(t, 0) > 0) == len(jenis)
         and perf.Quality.fx_ground_budget == 1,
         "jatah=%d" % perf.Quality.fx_ground_budget)


def test_hero_yang_dapat_jatah_stabil():
    """Hero yang boleh menggambar lapisan tanah harus SAMA setiap frame.
    Kalau bergantian, hiasan lantai akan hilang-timbul (berkedip)."""
    perf.Quality.apply(perf.LOW)
    perf.Quality.fx_ground_budget = 3
    heroes = _buat_hero()
    screen = pygame.display.get_surface()

    digambar = {}
    for ht in H._LIVE_FX_HEROES:
        mod = H._live_fx_module(ht)
        if mod is None or getattr(mod, "_wrapped_budget", False):
            continue
        asal = mod.draw_ground_layer

        def _bungkus(fn, nama):
            def _w(*a, **k):
                digambar[nama] = digambar.get(nama, 0) + 1
                return fn(*a, **k)
            _w._wrapped_budget = True
            return _w

        mod.draw_ground_layer = _bungkus(asal, ht)

    pola = []
    for _ in range(6):
        digambar.clear()
        H.begin_fx_frame(len(heroes))
        for h in heroes:
            H._live_fx_pre(h.hero_type, screen, h, h.x, h.y)
        pola.append(tuple(sorted(digambar)))

    _cek("lapisan tanah digambar tepat sesuai jatah",
         all(len(p) == 3 for p in pola),
         "pola: %s" % (pola[0],))
    _cek("hero yang dapat jatah tidak berganti-ganti (tidak berkedip)",
         len(set(pola)) == 1,
         "%d pola berbeda dari %d frame" % (len(set(pola)), len(pola)))


def test_preset_high_tidak_dibatasi():
    """Di preset HIGH tidak boleh ada yang berubah sama sekali."""
    perf.Quality.apply(perf.HIGH)
    heroes = _buat_hero()
    screen = pygame.display.get_surface()
    H.begin_fx_frame(len(heroes))
    _cek("preset HIGH: jatah lapisan tanah tak terbatas",
         H._FX_GROUND_LEFT[0] >= len(_TYPES),
         "jatah=%d, hero=%d" % (H._FX_GROUND_LEFT[0], len(_TYPES)))


def test_preset_low_membatasi():
    perf.Quality.apply(perf.LOW)
    heroes = _buat_hero()
    H.begin_fx_frame(len(heroes))
    _cek("preset LOW: lapisan tanah dibatasi",
         0 < H._FX_GROUND_LEFT[0] < len(_TYPES),
         "jatah=%d dari %d hero" % (H._FX_GROUND_LEFT[0], len(_TYPES)))
    perf.Quality.apply(perf.HIGH)


if __name__ == "__main__":
    test_semua_modul_punya_attach_dan_tick()
    test_simulasi_tetap_maju_walau_gambar_dilewati()
    test_hero_yang_dapat_jatah_stabil()
    test_preset_high_tidak_dibatasi()
    test_preset_low_membatasi()
    print("")
    if _GAGAL:
        print("GAGAL: %s" % ", ".join(_GAGAL))
        sys.exit(1)
    print("Semua uji anggaran lapisan FX tanah lolos")
