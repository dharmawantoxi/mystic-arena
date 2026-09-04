"""Ukur selisih piksel jalur LAMA (render langsung) vs BARU (cache sprite).

Metode: setiap potret dibuat dari INSTANCE BOSS SEGAR dengan urutan update
yang sama, supaya renderer yang stateful (proyektil maju tiap draw) tidak
mengotori perbandingan. ``drift`` = selisih dua potret jalur lama dari dua
instance segar (ambang noise alami); ``lama-vs-baru`` = regresi visual.

Jalankan:
    python3 tools/_diag_boss_pixel_parity.py [tipe...]
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame  # noqa: E402

pygame.init()
SCREEN = pygame.display.set_mode((1280, 720))

from mobile import perf  # noqa: E402

perf.install_font_cache()
perf.Quality.apply("high")

import heroes  # noqa: E402
import _core  # noqa: E402,F401
from _core import Game  # noqa: E402
from _entity import Minion  # noqa: E402
from bosses.base_boss import Boss  # noqa: E402

GAME = Game(SCREEN, level_number=1)
GAME.reset()
GAME.level_intro = None
GAME.boss_intro = None
LANE = GAME.map_renderer.get_lane_path("mid")
PANEL = 320

# FX hidup TIDAK dimatikan: tipe yang lapisan hidupnya terdaftar memang
# harus menggambarnya tiap frame di kedua jalur. Noise acaknya diukur
# sebagai "drift lama" (dua potret jalur lama dari instance segar) dan
# dipakai sebagai lantai untuk menilai lama-vs-baru.

TIPE = sys.argv[1:] or [
    "gornak", "varkul", "abaddon", "morgath", "drakar", "aeralith",
    "okeanora", "nexthyrius", "kagetsuka", "naraka", "aurethzar",
    "thalgryn", "gravefang", "krobellus", "nyxara", "vhalzun",
    "gravewake", "kunkka", "syrentha", "nyzrak", "kairenji", "morvyssk"]


# JAM VIRTUAL: sebagian renderer (krobellus, gornak) menggerakkan
# animasinya dari pygame.time.get_ticks() (dinding-waktu). Membandingkan
# dua shot yang diambil berjeda sekian milidetik (probe + numpy) akan
# selalu "berbeda" walau keduanya benar. Dengan jam virtual yang maju
# tetap 16 ms per langkah, kedua jalur melihat waktu animasi yang sama.
_VT = [0]
pygame.time.get_ticks = lambda: _VT[0]


def _tick(n=16):
    _VT[0] += n


def buat(tipe):
    _VT[0] = 0            # jam virtual di-reset per instance
    b = Boss(tipe, LANE)
    b.entrance_timer = 0
    b.x = b.y = float(PANEL // 2)
    foe = Minion("orc", "blue", "mid")
    foe.x, foe.y = b.x - min(120, b.range), b.y
    for _ in range(30):
        foe.hp = foe.max_hp
        _tick()
        b.update([foe], [], [])
    b.pulse = 2.3
    # Timer serangan dipatok ke BATAS kuantisasi pose cache: kalau tidak,
    # sprite cache (pose terkuantisasi tiap BOSS_ATK_QUANT*_q frame)
    # dibandingkan dengan pose langsung di tengah langkah animasi —
    # selisih fase animasi, bukan selisih cache.
    _qnt = 4
    _tmr = max(1, int(b.attack_cooldown * 0.7))
    b.timer = max(1, _tmr - (_tmr % _qnt))
    b._moving_cached = False
    return b


LIVE_ASLI = set(heroes._LIVE_FX_HEROES)


def shot(boss, mode):
    s = pygame.Surface((PANEL, PANEL), pygame.SRCALPHA)
    s.fill((24, 20, 30, 255))
    heroes.clear_boss_sprite_cache()
    heroes.BOSS_CACHE_ENABLED = (mode == "baru")
    # Jam disetel ke titik yang SAMA untuk setiap shot: renderer ber-jam
    # dinding (krobellus/vhalzun) altrimenti tidak bisa dibandingkan antar
    # waktu. Urutan jam per shot jadi identik: reset di buat(), lalu satu
    # langkah tetap di sini.
    _VT[0] = 500000
    _tick()
    boss.draw(s)
    heroes.BOSS_CACHE_ENABLED = True
    return pygame.surfarray.array3d(s).astype(int)


print(f"{'tipe':14s} {'lama-vs-baru':>13s} {'drift lama':>11s}  keterangan")
buruk = []
for t in TIPE:
    # Tipe ber-lapisan-hidup: bandingkan BADAN saja (lapisan hidup
    # dimatikan di kedua jalur) — pertukaran FX baked->hidup adalah
    # perilaku paritas-hero yang disengaja, bukan regresi cache.
    heroes._LIVE_FX_HEROES.discard(t)
    # Warm-up DULU (geometri canvas tumbuh), lalu kedua jalur diukur
    # dengan JARAK state yang sama: a1 diambil satu shot setelah
    # pemanasan, b1 satu shot setelah a1 — jadi keduanya melihat state
    # modul FX yang berjarak satu langkah, persis seperti pasangan
    # drift lama-vs-lama. (Sebelumnya b1 berjarak tiga langkah dari a1,
    # sehingga FX stateful seperti orb krobellus terlihat "bergeser".)
    shot(buat(t), "baru")          # warm-up: geometri canvas bisa tumbuh
    a1 = shot(buat(t), "lama")
    a2 = shot(buat(t), "lama")
    b1 = shot(buat(t), "baru")
    d = float(abs(a1 - b1).mean())
    dr = float(abs(a1 - a2).mean())
    tag = ""
    if d > max(0.5, dr * 3):
        tag = "<== BEDA NYATA"
        buruk.append((t, d))
    print(f"{t:14s} {d:13.3f} {dr:11.3f}  {tag}")
    heroes._LIVE_FX_HEROES.update(LIVE_ASLI & {t})
heroes._LIVE_FX_HEROES.update(LIVE_ASLI)
print(f"\nregresi visual nyata: {len(buruk)} dari {len(TIPE)}"
      + (f" -> {[x[0] for x in buruk]}" if buruk else " (tidak ada)"))
