#!/usr/bin/env python3
"""
Thorne 3D — v3: ART 2D RESMI + KAMERA 3D (software-rendered, pygame saja).

Pendekatan "paper doll":
  - Thorne digambar oleh CODE 2D RESMI dari game
    (heroes._bundle._NS_thorne._draw_thorne_elite) — sprite yang sama
    persis dengan di gameplay, lengkap dengan trail ayunan, impact
    sparks, debu langkah, dan partikel idle.
  - Sprite itu ditempel di sebuah BIDANG DATAR (card) di ruang 3D,
    lalu diproyeksikan oleh kamera yang mengorbit dengan PERSPEKTIF
    NYATA: sisi dekat lebih besar dari sisi jauh (trapezoid), saat
    kamera lewat di belakang card otomatis ter-mirror -> karakter
    terlihat "balik badan".
  - Lantai grid perspektif + bayangan tanah memberi rasa kedalaman.

Semua 3D dirasterisasi manual — homografi bidang datar berbentuk
rasional per-kolom (dipisah per scanline, jadi cepat tanpa numpy),
tanpa OpenGL, tanpa dependensi baru. Render internal resolusi kecil
lalu upscale NEAREST -> tetap terasa pixel-art.

Hanya butuh: Python 3.9+ dan pygame  (pip install pygame).

Jalankan (dari folder root repo mystic-arena):
  python tools/thorne_3d_demo.py           # sheet PNG -> tools/_out/
  python tools/thorne_3d_demo.py --live    # jendela pygame interaktif
    kunci: 1=idle  2=walk  3=attack  ESC=keluar
"""
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame
from heroes._bundle import _NS_thorne as T

FOCAL = 210.0     # panjang fokus kamera (px layar)
TARGET_Y = 1.5    # tinggi titik yang ditatap kamera (tengah badan)

# ────────────────────────────────────────────────────────────────────
# GEOMETRI CARD: kanvas sprite + pemetaan px-sprite -> dunia
# ────────────────────────────────────────────────────────────────────
SPW, SPH = 260, 262   # ukuran kanvas sprite (px, @scale 2)
AX, AY = 130, 175     # anchor _draw_thorne_elite di kanvas
FEET_V = 259          # baris px telapak kaki (= AY + 84 @scale 2)
US = 75.0             # px-sprite per unit dunia (tinggi karakter ~3.2u)


def make_sprite(action, t, ap=0.0):
    """Gambar Thorne dengan rig 2D resmi (visual & animasi 100% game)."""
    s = pygame.Surface((SPW, SPH), pygame.SRCALPHA)
    T._draw_thorne_elite(s, AX, AY, 1, t, action, ap)
    return s


class Cam:
    """Kamera orbit horizontal: eye = (d·sinθ, ty, d·cosθ), menatap
    (0, ty, 0) — tanpa elevasi supaya homografi card terpisah per kolom."""

    __slots__ = ("focal", "theta", "dist", "ty", "st", "ct")

    def __init__(self, focal, theta, dist, ty=TARGET_Y):
        self.focal = focal
        self.theta = theta
        self.dist = dist
        self.ty = ty
        self.st = math.sin(theta)
        self.ct = math.cos(theta)

    def project(self, p, cx, cy):
        """Titik dunia -> layar (x, y); None jika di belakang kamera."""
        dx = p[0] - self.dist * self.st
        dz = p[2] - self.dist * self.ct
        depth = -(dx * self.st + dz * self.ct)
        if depth < 0.15:
            return None
        fx = self.focal / depth
        return (cx + fx * (dx * self.ct - dz * self.st),
                cy - fx * (p[1] - self.ty))


# ────────────────────────────────────────────────────────────────────
# WARP CARD: homografi bidang datar (per kolom, terpisah scanline)
#
# Card di dunia: px-sprite (u, v) -> dunia ((u-AX)/US, (FEET_V-v)/US, 0)
# Proyeksi kamera orbit (diturunkan dari look-at, elevasi 0):
#   X = f·u_w·cosθ / (d − u_w·sinθ)      (X = px layar dari tengah)
#   Y = f·(y_w−ty)·cosθ·d / (f·cosθ + X·sinθ)·(1/f)  ->  lihat di bawah
# Inversnya (per kolom X, lalu linear terhadap y layar):
#   u_w(X) = d·X / (f·cosθ + X·sinθ)
#   v(y)   = vb + (y − H2y)·vs ,  vs = US·d·cosθ / (f·cosθ + X·sinθ)
# Jadi tiap kolom hanya butuh 1 bagi -> sangat murah; kamera di belakang
# (cosθ<0) otomatis menghasilkan card ter-mirror (paper doll).
# ────────────────────────────────────────────────────────────────────
def warp_card(canvas, sprite_bytes, cam, cx, cy):
    w, h = canvas.get_size()
    out = bytearray(w * h * 4)
    sw, sph = SPW, SPH
    sw4 = sw * 4
    f = cam.focal
    fc = f * cam.ct
    d = cam.dist
    vb_base = FEET_V - US * cam.ty
    h2x = w / 2.0
    h2y = h / 2.0
    sb = sprite_bytes
    row_stride = w * 4

    for x in range(w):
        X = x - h2x
        denom = fc + X * cam.st          # f·cosθ + X·sinθ
        if abs(denom) < 0.5:
            continue
        uw = d * X / denom
        u = AX + uw * US
        if u < 0.0 or u >= sw - 1.0:
            continue
        ui4 = (int(u + 0.5)) * 4
        vs = US * d * cam.ct / denom
        # rentang baris y sehingga 0 <= vb + (y-h2y)*vs < sph
        if vs > 0:
            y0 = math.ceil(h2y - vb_base / vs)
            y1 = math.ceil(h2y + (sph - vb_base) / vs)
        else:
            y0 = math.ceil(h2y + (sph - vb_base) / vs)
            y1 = math.ceil(h2y - vb_base / vs)
        if y1 <= 0 or y0 >= h:
            continue
        if y0 < 0:
            y0 = 0
        if y1 > h:
            y1 = h
        v = vb_base + (y0 - h2y) * vs
        o = x * 4 + y0 * row_stride
        for y in range(y0, y1):
            vi = int(v + 0.5)
            if vi >= sph:
                vi = sph - 1
            out[o:o + 4] = sb[vi * sw4 + ui4: vi * sw4 + ui4 + 4]
            v += vs
            o += row_stride

    surf = pygame.image.frombuffer(out, (w, h), "RGBA")
    canvas.blit(surf.convert_alpha(), (0, 0))


# ────────────────────────────────────────────────────────────────────
# LATAR: gradient + glow (di-cache per ukuran)
# ────────────────────────────────────────────────────────────────────
_BG_CACHE = {}


def get_bg(w, h):
    key = (w, h)
    bg = _BG_CACHE.get(key)
    if bg is not None:
        return bg
    bg = pygame.Surface((w, h))
    for y in range(h):
        t = y / h
        pygame.draw.line(bg, (int(12 + 11 * t), int(15 + 11 * t),
                              int(24 + 15 * t)), (0, y), (w, y))
    glow = pygame.Surface((w, h), pygame.SRCALPHA)
    maxr = max(w, h) // 2
    for rr in range(maxr, 0, -6):
        pygame.draw.circle(glow, (255, 180, 95, 3), (w // 2, int(h * 0.45)),
                           rr)
    bg.blit(glow, (0, 0))
    _BG_CACHE[key] = bg
    return bg


# ────────────────────────────────────────────────────────────────────
# LANTAI GRID PERSPEKTIF + BAYANGAN
# ────────────────────────────────────────────────────────────────────
_GRID_SEGS = []
_G = 6.0
for _i in range(int(_G / 1.5) + 1):
    _v = -_G + _i * 1.5
    _GRID_SEGS.append(((-_G, 0.0, _v), (_G, 0.0, _v)))
    _GRID_SEGS.append(((_v, 0.0, -_G), (_v, 0.0, _G)))


def draw_grid(canvas, cam, cx, cy):
    bgc = (14, 17, 26)
    lnc = (46, 56, 78)
    for a, b in _GRID_SEGS:
        n = 8
        pa = cam.project(a, cx, cy)
        for i in range(1, n + 1):
            tt = i / n
            pb = cam.project((a[0] + (b[0] - a[0]) * tt, 0.0,
                              a[2] + (b[2] - a[2]) * tt), cx, cy)
            if pa is None or pb is None:
                pa = pb
                continue
            mx = (pa[0] + pb[0]) / 2
            my = (pa[1] + pb[1]) / 2
            md = math.hypot(mx, my + cam.ty)   # kedalaman kira-kira
            fade = min(1.0, max(0.10, 1.35 - md / 12.0))
            col = (int(bgc[0] + (lnc[0] - bgc[0]) * fade),
                   int(bgc[1] + (lnc[1] - bgc[1]) * fade),
                   int(bgc[2] + (lnc[2] - bgc[2]) * fade))
            pygame.draw.line(canvas, col, (int(pa[0]), int(pa[1])),
                             (int(pb[0]), int(pb[1])), 1)
            pa = pb


def draw_shadow(canvas, cam, cx, cy):
    pts = []
    for i in range(24):
        a = i / 24 * math.tau
        wpt = (0.15 + 1.05 * math.cos(a), 0.02, 0.50 * math.sin(a))
        p = cam.project(wpt, cx, cy)
        if p is None:
            return
        pts.append((int(p[0]), int(p[1])))
    tmp = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(tmp, (0, 0, 0, 80), pts)
    canvas.blit(tmp, (0, 0))


# ────────────────────────────────────────────────────────────────────
# RENDER SATU FRAME
# ────────────────────────────────────────────────────────────────────
_SPRITE_CACHE = {}


def render_frame(w, h, theta, dist, action, t, ap=0.0):
    canvas = pygame.Surface((w, h))
    canvas.blit(get_bg(w, h), (0, 0))
    cx, cy = w / 2.0, h * 0.5
    cam = Cam(FOCAL, theta, dist)
    draw_grid(canvas, cam, cx, cy)
    draw_shadow(canvas, cam, cx, cy)
    key = (action, round(t, 3), round(ap, 3))
    spr = _SPRITE_CACHE.get(key)
    if spr is None:
        if len(_SPRITE_CACHE) > 24:
            _SPRITE_CACHE.clear()
        spr = make_sprite(action, t, ap)
        _SPRITE_CACHE[key] = spr
    warp_card(canvas, pygame.image.tobytes(spr, "RGBA"), cam, cx, cy)
    return canvas


# ────────────────────────────────────────────────────────────────────
# SHEET DEMO
# ────────────────────────────────────────────────────────────────────
def _label(sheet, text, x, y, size=22, color=(235, 235, 235)):
    # Font(None, ...) = font bawaan pygame -> ada di semua OS
    font = pygame.font.Font(None, size + 4)
    surf = font.render(text, True, color)
    sheet.blit(surf, (x, y))
    return surf.get_size()


def make_sheets(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    frame_w, frame_h = 128, 140
    scale = 2
    fw, fh = frame_w * scale, frame_h * scale

    def cell(theta, dist, action, t, ap=0.0):
        img = render_frame(frame_w, frame_h, theta, dist, action, t, ap)
        return pygame.transform.scale(img, (fw, fh))

    t0 = time.perf_counter()

    # ── Sheet 1: KAMERA ORBIT 360° (idle, card ter-mirror di belakang) ──
    n = 12
    sheet = pygame.Surface((n * fw + 40, fh + 90))
    sheet.fill((12, 14, 20))
    _label(sheet, "THORNE 3D — KAMERA ORBIT 360°", 20, 14, 26,
           (255, 205, 120))
    _label(sheet, "karakter = art 2D resmi • kamera 3D perspektif • "
           "di belakang -> card ter-mirror (balik badan)", 20, 46, 15,
           (150, 158, 175))
    for i in range(n):
        theta = (i + 0.5) / n * math.tau
        sheet.blit(cell(theta, 6.2, "idle", 0.9), (20 + i * fw, 70))
    dt_spin = (time.perf_counter() - t0) / n * 1000
    p1 = os.path.join(out_dir, "thorne_3d_spin.png")
    pygame.image.save(sheet, p1)
    print(p1)

    # ── Sheet 2: animasi 2D dengan kamera 3D 3/4 ──
    rows = (("IDLE", 6, "idle"), ("WALK", 8, "walk"),
            ("ATTACK", 8, "attack"))
    H = 90 + 3 * (fh + 60)
    W = max(8 * fw + 150, 900)
    sheet = pygame.Surface((W, H))
    sheet.fill((12, 14, 20))
    _label(sheet, "THORNE 3D — ANIMASI RIG 2D • KAMERA 3/4", 20, 14, 26,
           (255, 205, 120))
    _label(sheet, "trail ayunan, sparks, debu & motes = efek 2D asli "
           "(bukan tiruan 3D)", 20, 46, 15, (150, 158, 175))
    theta34 = 0.55
    t0 = time.perf_counter()
    for row, (label, count, action) in enumerate(rows):
        top = 70 + row * (fh + 60)
        _label(sheet, label, 30, top + fh // 2 - 10, 20, (255, 199, 130))
        for i in range(count):
            if action == "attack":
                img = cell(theta34, 6.0, action, 0.0, ap=i / (count - 1))
            else:
                img = cell(theta34, 6.0, action, (i / count) * math.tau)
            sheet.blit(img, (150 + i * fw, top))
    dt_anim = (time.perf_counter() - t0) / 22 * 1000
    p2 = os.path.join(out_dir, "thorne_3d_anim.png")
    pygame.image.save(sheet, p2)
    print(p2)

    # ── Sheet 3: close-up (kamera dekat) 4x ──
    img = render_frame(150, 165, 0.42, 4.4, "idle", 0.9)
    big = pygame.transform.scale(img, (img.get_width() * 4,
                                       img.get_height() * 4))
    p3 = os.path.join(out_dir, "thorne_3d_closeup.png")
    pygame.image.save(big, p3)
    print(p3)
    print(f"render ~{dt_spin:.2f} ms/frame (orbit)  "
          f"~{dt_anim:.2f} ms/frame (anim)")


# ────────────────────────────────────────────────────────────────────
# MODE LIVE
# ────────────────────────────────────────────────────────────────────
def run_live():
    try:
        screen = pygame.display.set_mode((760, 560))
    except pygame.error as e:
        print(f"Gagal membuka jendela: {e}")
        print("Pastikan laptop punya display & driver graphics —")
        print("atau jalankan mode sheet:  python tools/thorne_3d_demo.py")
        raise
    pygame.display.set_caption(
        "Thorne 3D — art 2D resmi + kamera 3D (1 idle / 2 walk / 3 attack / "
        "ESC keluar)")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 22)
    t = 0.0
    seq = 0          # 0 idle, 1 walk, 2 attack
    ap = 0.0
    theta = 0.55
    frames = 0
    t_fps = time.perf_counter()
    W, H = 128, 140
    sc = min(760 / W, 520 / H)
    sw, sh = int(W * sc), int(H * sc)
    ox, oy = (760 - sw) // 2, (560 - sh) // 2 - 8
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_1,
                                                        pygame.K_2,
                                                        pygame.K_3):
                seq = ev.key - pygame.K_1
                ap = 0.0
        dt = min(clock.tick(60) / 1000.0, 0.05)
        t += dt
        theta += dt * 0.45
        if seq == 2:
            ap += dt / 1.1
            if ap > 1.02:
                ap = 0.0
        if seq == 0:
            img = render_frame(W, H, theta, 6.2, "idle", t)
            label = "IDLE  (1 idle / 2 walk / 3 attack / ESC quit)"
        elif seq == 1:
            img = render_frame(W, H, theta, 6.2, "walk", t * 2.0)
            label = "WALK"
        else:
            img = render_frame(W, H, theta, 6.2, "attack", t, min(1.0, ap))
            label = f"ATTACK {ap:.2f}"
        scr = pygame.display.get_surface()
        scr.fill((10, 13, 20))
        scr.blit(pygame.transform.scale(img, (sw, sh)), (ox, oy))
        scr.blit(font.render(label, True, (255, 205, 120)), (20, 14))
        scr.blit(font.render(
            f"kamera {math.degrees(theta % math.tau):.0f}°  "
            "(orbit 360° otomatis)", True, (150, 158, 175)), (20, 38))
        pygame.display.flip()
        frames += 1
        now = time.perf_counter()
        if now - t_fps >= 1.0:
            print(f"FPS: {frames:.0f}  kamera {math.degrees(theta % math.tau):.0f}°")
            frames = 0
            t_fps = now


if __name__ == "__main__":
    LIVE = "--live" in sys.argv
    if not LIVE:
        # Sheet: render tanpa jendela (aman di terminal/CI)
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    # --live: biarkan driver asli (jendela sungguhan di laptop)
    pygame.init()
    pygame.display.set_mode((8, 8))
    if LIVE:
        run_live()
    else:
        out = os.path.join(ROOT, "tools", "_out")
        make_sheets(out)
