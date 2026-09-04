"""Cek kliping canvas cache boss + potret banding jalur lama vs baru.

  python3 tools/_diag_boss_cache_visual.py [tipe ...]

Menghasilkan docs/_boss_cache_<tipe>.png: kiri = jalur langsung (lama),
kanan = jalur cache (baru), pada pose yang sama.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.getcwd())
import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1280, 720))
from mobile import perf  # noqa: E402

perf.install_font_cache()
perf.Quality.apply("high")
import heroes  # noqa: E402
import _core  # noqa: E402,F401
from _core import Game  # noqa: E402
from bosses.base_boss import Boss, _get_boss_draw_func  # noqa: E402
from bosses.boss_data import get_all_boss_types  # noqa: E402
from _entity import Minion  # noqa: E402

g = Game(pygame.display.set_mode((1280, 720)), level_number=1)
g.level_intro = None
g.boss_intro = None
LANE = g.map_renderer.get_lane_path("mid")

TYPES = sys.argv[1:] or ["gornak", "varkul", "abaddon", "morgath", "drakar",
                         "aeralith", "okeanora", "nexthyrius", "kagetsuka",
                         "naraka", "aurethzar", "thalgryn"]

# ── 1. cek kliping untuk semua boss ───────────────────────────────
print("cek kliping canvas (konten menyentuh tepi = FX terpotong)...")
SIZE = 1400
C = SIZE // 2
big = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
klip = []
for t in sorted(get_all_boss_types()):
    b = Boss(t, LANE)
    b.entrance_timer = 0
    b.x, b.y = 640.0, 360.0
    foe = Minion("orc", "blue", "mid")
    foe.x, foe.y = b.x - min(150, b.range), b.y
    KIND = ("idle", "idle", "atk", "skill")
    worst = 0
    worst_fase = -1
    for fase in range(4):
        for _ in range(10):
            foe.hp = foe.max_hp
            b.update([foe] if fase >= 2 else [], [], [])
            if fase == 1:
                b.x += 2.0
            if fase == 3:
                b.active_skill = "q"
                b.active_skill_timer = 20
        big.fill((0, 0, 0, 0))
        b._render_scale = 1.0
        b._boss_native_cache = True
        try:
            _get_boss_draw_func(t)(big, b, C, C)
        except Exception:
            pass
        finally:
            b._boss_native_cache = False
            del b._render_scale
        r = big.get_bounding_rect(min_alpha=8)
        need = max(abs(r.left - C), abs(r.right - C), abs(r.top - C),
                   abs(r.bottom - C))
        if need > worst:
            worst, worst_fase = need, fase
    half = heroes._boss_geom(t, KIND[worst_fase], b)[0]
    if worst > half:
        klip.append((t, half, worst, worst_fase))
NAMA_FASE = ("idle", "walk", "attack", "skill")
print(f"  canvas kurang besar untuk {len(klip)} boss "
      f"(batas atas half={heroes.BOSS_CANVAS_MAX_HALF}, "
      f"di atas itu pose digambar langsung):")
for t, half, need, fase in sorted(klip, key=lambda z: -(z[2] - z[1]))[:20]:
    tag = "JALUR LANGSUNG" if need > heroes.BOSS_CANVAS_MAX_HALF \
        else "canvas membesar"
    print(f"    {t:20s} half={half} butuh={need} (+{need-half}) "
          f"@{NAMA_FASE[fase]:6s} {tag}")

# ── 2. potret banding ────────────────────────────────────────────
fx_asli = set(heroes._LIVE_FX_HEROES)
heroes._LIVE_FX_HEROES.clear()      # samakan: tanpa partikel lapisan hidup
# Boss digambar di TENGAH panel (dulu di 640,360 pada panel 460 px ->
# badan berada DI LUAR panel dan kedua potret kosong: banding jadi
# vacuous). Panel 560 px cukup untuk pose serangan + aura.
PANEL = 560
CX = CY = PANEL // 2
kosong = []
terbesar = 0.0
for t in TYPES:
    b = Boss(t, LANE)
    b.entrance_timer = 0
    b.x, b.y = float(CX), float(CY)
    foe = Minion("orc", "blue", "mid")
    foe.x, foe.y = b.x - min(120, b.range), b.y
    for _ in range(30):
        foe.hp = foe.max_hp
        b.update([foe], [], [])
    b.pulse = 2.3
    b.timer = max(1, int(b.attack_cooldown * 0.7))   # pose serangan
    shots = []
    for mode in ("lama", "baru"):
        s = pygame.Surface((PANEL, PANEL), pygame.SRCALPHA)
        s.fill((24, 20, 30, 255))
        heroes.clear_boss_sprite_cache()
        heroes.BOSS_CACHE_ENABLED = (mode == "baru")
        b._moving_cached = False
        b.draw(s)
        shots.append(s)
    heroes.BOSS_CACHE_ENABLED = True
    a = pygame.surfarray.array3d(shots[0]).astype(int)
    bb = pygame.surfarray.array3d(shots[1]).astype(int)
    # Panel diisi warna latar OPAK, jadi "kosong" diukur sebagai
    # selisih terhadap warna latar (bukan bounding rect alpha).
    isi = [float(abs(arr - [24, 20, 30]).mean()) for arr in (a, bb)]
    if isi[0] < 0.01 or isi[1] < 0.01:
        kosong.append(t)
        print(f"  {t:16s} !! POTRET KOSONG "
              f"(isi lama {isi[0]:.3f}, baru {isi[1]:.3f})")
        continue
    diff = float(abs(a - bb).mean())
    terbesar = max(terbesar, diff)
    out = pygame.Surface((PANEL * 2 + 12, PANEL + 26))
    out.fill((12, 10, 16))
    out.blit(shots[0], (0, 26))
    out.blit(shots[1], (PANEL + 12, 26))
    from _render import get_font
    f = get_font(18, "body_bold")
    out.blit(f.render(f"{t} — jalur LAMA (langsung)", True, (255, 190, 90)),
             (6, 4))
    out.blit(f.render("jalur BARU (cache sprite)", True, (140, 230, 150)),
             (PANEL + 18, 4))
    path = f"docs/_boss_cache_{t}.png"
    pygame.image.save(out, path)
    print(f"  {t:16s} -> {path}  (rata-rata selisih piksel {diff:.3f})")
heroes._LIVE_FX_HEROES.update(fx_asli)
print(f"  ringkasan: {len(TYPES) - len(kosong)} potret terisi, "
      f"selisih terbesar {terbesar:.3f}"
      + (f", KOSONG: {kosong}" if kosong else ""))
