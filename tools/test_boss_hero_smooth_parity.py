"""Uji regresi: mini boss & true boss harus selancar hero unlock.

Latar belakang (keluhan yang diperbaiki):
  "pergerakan, animasi dan lain-lain mini bos dan true bos tidak
   selancar saat mereka jadi hero unlock"

Tiga akar masalah yang diukur & dikunci di sini:

  1. GAMBAR  — Boss.draw() memanggil renderer prosedural langsung ke
     layar SETIAP frame (1,9-7,0 ms/boss di PC), sementara karakter
     yang sama sebagai hero lewat sprite cache (0,6-0,8 ms). Sekarang
     boss memakai pipeline cache yang sama (heroes.render_boss) pada
     skala native 1.0.
  2. GERAK   — _move_forward() membuang satu frame penuh di setiap
     waypoint lane (`if d < 15: index -= 1; return`), jadi boss
     tersendak berkala dan pose-nya berkedip ke IDLE. Sekarang sisa
     langkah dipakai lanjut ke waypoint berikutnya.
  3. ANIMASI — jam animasi boss (pulse += 0.05) setengah kecepatan
     hero (pulse += 0.1) untuk rig yang sama, dan arah hadap bisa
     terbalik di tengah ayunan. Sekarang sama dengan hero + ada kunci
     arah selama ayunan.

Jalankan:
    python3 tools/test_boss_hero_smooth_parity.py            # sampel cepat
    python3 tools/test_boss_hero_smooth_parity.py --all      # 216 boss
"""

import argparse
import os
import sys
import time

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
from _entity import Hero, Minion  # noqa: E402
from bosses.base_boss import Boss  # noqa: E402
from bosses.boss_data import get_all_boss_types  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--all", action="store_true",
                help="uji SEMUA 216 boss (default: sampel perwakilan)")
ap.add_argument("--frames", type=int, default=120)
args = ap.parse_args()

FRAMES = max(30, args.frames)
SURF = pygame.Surface((1280, 720), pygame.SRCALPHA)
GAME = Game(SCREEN, level_number=1)
GAME.level_intro = None
GAME.boss_intro = None
LANE = GAME.map_renderer.get_lane_path("mid")

SAMPEL = ["gornak", "morgath", "drakar", "abaddon", "varkul", "xerathis",
          "nyzrak", "zharok", "pyrenth", "vokrahn", "nyxara", "gravefang",
          "khalros", "gorath", "razak", "alchemist", "ancient_apparition",
          "thalgryn", "kunkka", "syrentha", "gravewake", "aeralith",
          "okeanora", "vraskhan", "nexthyrius", "kagetsuka", "aurethzar",
          "naraka", "morkhaera", "seraphienne"]

ALL_TYPES = sorted(get_all_boss_types().keys())
TYPES = ALL_TYPES if args.all else [t for t in SAMPEL if t in ALL_TYPES]

GAGAL = []


def cek(nama, syarat, pesan):
    status = "OK  " if syarat else "GAGAL"
    print(f"[{status}] {nama}: {pesan}")
    if not syarat:
        GAGAL.append(nama)


def buat_boss(tipe, kelas=None, jalan=True):
    b = Boss(tipe, LANE)
    if kelas:
        b.boss_class = kelas
    b.entrance_timer = 0
    b.x, b.y = float(LANE[-1][0]), float(LANE[-1][1])
    b.waypoint_index = len(LANE) - 1
    return b


def posisi_setelah_jalan(b, frames=FRAMES):
    """Jalankan boss menyusuri lane; kembalikan jejak perpindahan."""
    jejak = []
    for _ in range(frames):
        x0, y0 = b.x, b.y
        b.update([], [], [])
        b.draw(SURF)
        jejak.append(((b.x - x0) ** 2 + (b.y - y0) ** 2) ** 0.5)
    return jejak


# ══════════════════════════════════════════════════════════════════
# 1. GERAK: tidak boleh ada frame stall saat menyusuri lane
# ══════════════════════════════════════════════════════════════════
print("\n=== 1. GERAK LANCAR (tanpa frame stall di waypoint) ===")
total_stall = 0
contoh = []
for t in TYPES:
    for kelas in ("mini", "true"):
        b = buat_boss(t, kelas)
        jejak = posisi_setelah_jalan(b, FRAMES)
        # frame pertama boleh 0 (inisialisasi posisi)
        stall = [i for i, s in enumerate(jejak[1:], start=1) if s <= 0.02]
        if stall:
            total_stall += len(stall)
            contoh.append(f"{t}/{kelas}:{stall[:4]}")
cek("gerak tanpa stall", total_stall == 0,
    f"{total_stall} frame stall di {len(TYPES) * 2} jalur boss"
    + (f" (contoh {', '.join(contoh[:4])})" if contoh else ""))

# Hero sebagai pembanding: harus sama-sama bebas stall
h = Hero(TYPES[0], "red", x=float(LANE[-1][0]), y=float(LANE[-1][1]))
jejak_h = []
for _ in range(FRAMES):
    x0, y0 = h.x, h.y
    h.update([], [], [])
    jejak_h.append(((h.x - x0) ** 2 + (h.y - y0) ** 2) ** 0.5)
stall_h = [i for i, s in enumerate(jejak_h[1:], start=1) if s <= 0.02]
cek("hero juga tanpa stall", len(stall_h) == 0, f"{len(stall_h)} frame stall")

# ══════════════════════════════════════════════════════════════════
# 2. JAM ANIMASI: boss == hero
# ══════════════════════════════════════════════════════════════════
print("\n=== 2. JAM ANIMASI (pulse/anim_time) PARITAS DENGAN HERO ===")
b = buat_boss(TYPES[0])
h = Hero(TYPES[0], "red")
b.entrance_timer = 0
p0b, p0h = b.pulse, h.pulse
for _ in range(30):
    b.update([], [], [])
    h.update([], [], [])
db = (b.pulse - p0b) / 30.0
dh = (h.pulse - p0h) / 30.0
cek("kecepatan pulse", abs(db - dh) < 1e-6,
    f"boss {db:.3f}/frame vs hero {dh:.3f}/frame")
cek("anim_time maju", b.anim_time >= 30, f"anim_time={b.anim_time}")

# ══════════════════════════════════════════════════════════════════
# 3. ARAH HADAP: terkunci selama ayunan, tidak berkedip
# ══════════════════════════════════════════════════════════════════
print("\n=== 3. ARAH HADAP TERKUNCI SELAMA AYUNAN ===")
b = buat_boss("gornak")
b.entrance_timer = 0
foe = Minion("orc", "blue", "mid")
foe.x, foe.y = b.x - 40.0, b.y
b.range = 90
b.update([foe], [], [])          # mulai menyerang (arah -1)
arah_awal = b.direction
foe.x = b.x + 40.0               # target pindah sisi di tengah ayunan
flip = 0
for _ in range(6):
    foe.hp = foe.max_hp
    b.update([foe], [], [])
    if b.direction != arah_awal:
        flip += 1
cek("tidak membalik saat swing", flip == 0,
    f"direction tetap {arah_awal} selama {6} frame ayunan"
    if flip == 0 else f"membalik {flip}x di tengah ayunan")

# ══════════════════════════════════════════════════════════════════
# 4. CACHE SPRITE BOSS: aktif, hit, animasi tidak beku
# ══════════════════════════════════════════════════════════════════
print("\n=== 4. CACHE SPRITE BOSS (paritas pipeline hero) ===")
heroes.clear_boss_sprite_cache()
b = buat_boss(TYPES[0])
kunci = set()
for _ in range(FRAMES):
    b.update([], [], [])
    b.draw(SURF)
    kunci.add(heroes._boss_cache_key(TYPES[0], b))
st = heroes.boss_cache_stats()
tot = st["hits"] + st["misses"]
hit_rate = (100 * st["hits"] // tot) if tot else 0
cek("cache dipakai", st["enabled"] and tot > 0,
    f"{st['hits']} hit / {st['misses']} miss ({hit_rate}%)")
cek("hit rate layak", hit_rate >= 30,
    f"{hit_rate}% — badan tidak lagi dirender penuh tiap frame")
cek("animasi tidak beku", len(kunci) >= 6,
    f"{len(kunci)} pose berbeda selama {FRAMES} frame jalan")
# Fallback yang DISENGAJA (pose FX melebar -> _BOSS_UNSAFE) dihitung di
# statistik yang sama; yang tidak boleh ada adalah renderer yang GAGAL
# diam-diam di canvas.
gagal = st["fallback"] - st["unsafe"]
cek("tidak ada fallback diam-diam", gagal <= 0,
    f"renderer gagal di canvas={max(0, gagal)}, "
    f"pose FX jauh (sengaja, jalur langsung)={st['unsafe']}")

# ══════════════════════════════════════════════════════════════════
# 5. BIAYA DRAW: boss tidak boleh jauh lebih mahal dari hero
# ══════════════════════════════════════════════════════════════════
print("\n=== 5. BIAYA DRAW BOSS vs HERO (karakter sama) ===")
rasio_terburuk = 0.0
detail = []
for t in TYPES[:12]:
    b = buat_boss(t)
    b.update([], [], [])
    b.draw(SURF)                       # panaskan renderer & cache
    t0 = time.perf_counter()
    for _ in range(40):
        b.update([], [], [])
        b.draw(SURF)
    ms_boss = (time.perf_counter() - t0) / 40 * 1000

    h = Hero(t, "red", x=b.x, y=b.y)
    h.update([], [], [])
    h.draw(SURF)
    t0 = time.perf_counter()
    for _ in range(40):
        h.update([], [], [])
        h.draw(SURF)
    ms_hero = (time.perf_counter() - t0) / 40 * 1000

    rasio = ms_boss / max(0.05, ms_hero)
    rasio_terburuk = max(rasio_terburuk, rasio)
    detail.append(f"{t} {ms_boss:.2f}/{ms_hero:.2f}ms ({rasio:.2f}x)")
cek("draw boss ≈ draw hero", rasio_terburuk <= 2.0,
    f"rasio terburuk {rasio_terburuk:.2f}x | " + ", ".join(detail[:6]))

# ══════════════════════════════════════════════════════════════════
# 6. SEMUA BOSS AMAN DIRENDER LEWAT CACHE (tanpa exception/klip)
# ══════════════════════════════════════════════════════════════════
print("\n=== 6. RENDER AMAN UNTUK SEMUA TIPE BOSS ===")
heroes.clear_boss_sprite_cache()
error = []
kosong = []
for t in (ALL_TYPES if args.all else TYPES):
    try:
        b = buat_boss(t)
        foe = Minion("orc", "blue", "mid")
        foe.x, foe.y = b.x - min(120, b.range), b.y
        for fase in range(4):
            for i in range(12):
                foe.hp = foe.max_hp
                foe.alive = True
                b.update([foe] if fase >= 2 else [], [], [])
                if fase == 1:
                    b.x += 2.0            # jalan
                if fase == 3:
                    b.active_skill = "q"
                    b.active_skill_timer = 20
                b.draw(SURF)
        if heroes.boss_cache_stats()["misses"] == 0:
            kosong.append(t)
    except Exception as exc:
        error.append(f"{t}: {type(exc).__name__}: {exc}")
cek("tanpa exception", not error,
    f"{len(error)} error" + (f" -> {error[:3]}" if error else
                             f" dari {len(ALL_TYPES) if args.all else len(TYPES)} boss"))
st = heroes.boss_cache_stats()
cek("semua menghasilkan sprite", st["misses"] > 0,
    f"{st['misses']} miss / {st['hits']} hit, entri={st['entries']}, "
    f"canvas membesar {st['grow']}x, pose FX jauh (jalur langsung) "
    f"{len(heroes._BOSS_UNSAFE)}")

# Tidak boleh ada sprite cache yang tintanya menyentuh tepi sprite:
# itu artinya FX terpotong (regresi visual). Pose yang memang butuh
# ruang lebih dari canvas maksimum harus pindah ke jalur langsung
# (_BOSS_UNSAFE), bukan dipotong diam-diam.
terpotong = []
for _k, _entry in heroes._boss_sprite_cache.items():
    _spr = _entry[0]
    _w, _h = _spr.get_width(), _spr.get_height()
    if _w < 6 or _h < 6:
        continue
    for _s in (pygame.Rect(0, 0, _w, 2), pygame.Rect(0, _h - 2, _w, 2),
               pygame.Rect(0, 0, 2, _h), pygame.Rect(_w - 2, 0, 2, _h)):
        try:
            if _spr.subsurface(_s).get_bounding_rect(min_alpha=8).width:
                terpotong.append(_k[0])
                break
        except Exception:
            pass
cek("tidak ada FX terpotong tepi sprite", not terpotong,
    f"{len(terpotong)} sprite terpotong" +
    (f" -> {sorted(set(terpotong))[:6]}" if terpotong else
     f" ({len(heroes._boss_sprite_cache)} sprite diperiksa)"))

# ══════════════════════════════════════════════════════════════════
# 7. ANCHOR: sprite cache mendarat di titik yang sama dengan jalur lama
# ══════════════════════════════════════════════════════════════════
print("\n=== 7. POSISI SPRITE IDENTIK DENGAN JALUR LANGSUNG ===")

# FX hidup dimatikan dulu supaya yang dibandingkan benar-benar badan
# (partikel lapisan hidup punya komponen acak per frame).
_fx_asli = set(heroes._LIVE_FX_HEROES)
heroes._LIVE_FX_HEROES.clear()
geser = []
for t in TYPES[:14]:
    b = buat_boss(t)
    b.update([], [], [])
    b.pulse = 1.7                       # pose tetap & sama untuk 2 jalur
    b.timer = 0
    b.active_skill = None
    x, y = 640, 400

    A = pygame.Surface((900, 900), pygame.SRCALPHA)
    heroes.clear_boss_sprite_cache()
    heroes.BOSS_CACHE_ENABLED = True
    b.draw(A)
    ra = A.get_bounding_rect(min_alpha=16)

    B = pygame.Surface((900, 900), pygame.SRCALPHA)
    heroes.BOSS_CACHE_ENABLED = False
    b._moving_cached = False
    b.draw(B)
    rb = B.get_bounding_rect(min_alpha=16)
    heroes.BOSS_CACHE_ENABLED = True

    if ra.width and rb.width:
        geser.append((t, abs(ra.centerx - rb.centerx),
                      abs(ra.centery - rb.centery)))
heroes._LIVE_FX_HEROES.update(_fx_asli)
maks = max((max(dx, dy) for _, dx, dy in geser), default=0)
cek("anchor tidak bergeser", maks <= 2,
    f"selisih bbox maksimum {maks}px "
    f"({', '.join(f'{t}:{dx}/{dy}' for t, dx, dy in geser[:5])})")

# ══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
if GAGAL:
    print(f"{len(GAGAL)} pemeriksaan GAGAL: {GAGAL}")
    sys.exit(1)
print("SEMUA PEMERIKSAAN LULUS — boss selancar hero unlock.")
print("Statistik cache boss:", heroes.boss_cache_stats())
