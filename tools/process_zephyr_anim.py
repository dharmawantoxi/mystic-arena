#!/usr/bin/env python3
"""Bake Zephyr HD body + walk / swing / skill sprites (gaya ala Thorne).

Meniru tools/process_thorne_anim.py untuk hero Zephyr.

Sumber
──────
assets/heroes/_raw/zephyr_<pose>_raw.png   →   render digital HD (latar hitam)

Keluaran (semua RGBA transparan, di-trim, di-align)
───────
assets/heroes/zephyr_idle.png              body idle HD
assets/heroes/zephyr_walk.png              body walk HD  (stride)
assets/heroes/zephyr_attack.png            body attack HD (casting)
assets/heroes/zephyr_walk_0.png / _1.png   walk cycle (stride <-> plant)
assets/heroes/zephyr_swing_0..7.png        animasi serangan (staff bergerak)
assets/heroes/zephyr_skill_q/w/e/r.png     efek skill Q/W/E/R (jika bisa di-bake)

Aset __raw__ di-ignore (lihat .gitignore). Kalau file raw hilang, tool ini
tidak merusak apa-apa: renderer Zephyr tetap punya fallback prosedural.

Run:  /tmp/thorne-venv/bin/python tools/process_zephyr_anim.py
"""
from __future__ import print_function

import math
import os
from collections import deque

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEROES = os.path.join(ROOT, "assets", "heroes")
RAW = os.path.join(HEROES, "_raw")
DOCS = os.path.join(ROOT, "docs")

BAKE_H = 320
SKILL_SIZE = 512
DARK_T = 46

BODY_POSES = ("idle", "walk", "attack")

# Body sprite disimpan pada tinggi maksimum ini saja.  Di runtime sprite
# di-scale ke ZEPHYR_SPRITE_HEIGHT (~110 px), jadi menyimpan file 1500-an px
# hanya membuang memori & memperlambat load Android.  Tinggi ~648 px sudah
# jauh lebih besar dari render dan tetap terlihat tajam setelah smoothscale.
BODY_MAX_H = 648


# ---------------------------------------------------------------------------
# Background removal (flood-fill dari tepi; latar hitam studio)
# ---------------------------------------------------------------------------
def _luma(r, g, b):
    return 0.299 * r + 0.587 * g + 0.114 * b


def _is_edge_bg(r, g, b, a):
    if a < 20:
        return True
    return max(r, g, b) < DARK_T


def remove_background(im):
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()

    bg = bytearray(w * h)
    dq = deque()
    neigh = ((1, 0), (-1, 0), (0, 1), (0, -1),
             (1, 1), (-1, -1), (1, -1), (-1, 1))

    def try_push(x, y):
        i = y * w + x
        if bg[i]:
            return
        r, g, b, a = px[x, y]
        if _is_edge_bg(r, g, b, a):
            bg[i] = 1
            dq.append((x, y))

    for x in range(w):
        try_push(x, 0)
        try_push(x, h - 1)
    for y in range(h):
        try_push(0, y)
        try_push(w - 1, y)

    while dq:
        x, y = dq.popleft()
        for dx, dy in neigh:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                try_push(nx, ny)

    alpha = bytearray(w * h)
    for i in range(w * h):
        alpha[i] = 0 if bg[i] else 255

    # Feather 1px pada piksel bg yang menempel foreground (anti garis keras).
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            i = y * w + x
            if alpha[i]:
                continue
            if alpha[i - 1] or alpha[i + 1] or alpha[i - w] or alpha[i + w]:
                r, g, b, a = px[x, y]
                alpha[i] = min(200, max(r, g, b))

    out = Image.new("RGBA", (w, h))
    opx = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            opx[x, y] = (r, g, b, alpha[y * w + x])
    return out


def bbox_alpha(im, pad=0):
    box = im.getbbox()
    if not box:
        return None
    l, t, r, b = box
    return (max(0, l - pad), max(0, t - pad),
            min(im.size[0], r + pad), min(im.size[1], b + pad))


# ---------------------------------------------------------------------------
# Body HD pose (idle / walk / attack)
# ---------------------------------------------------------------------------
def bake_body():
    for pose in BODY_POSES:
        src = os.path.join(RAW, "zephyr_%s_raw.png" % pose)
        dst = os.path.join(HEROES, "zephyr_%s.png" % pose)
        if not os.path.isfile(src):
            print("  skip body %s (raw tidak ada)" % pose)
            continue
        im = remove_background(Image.open(src))
        box = bbox_alpha(im, pad=2)
        if box:
            im = im.crop(box)
        im = _normalise_height(im, BODY_MAX_H)
        im.save(dst)
        print("  body %-7s -> %s  %s" % (pose, dst, im.size))


# ---------------------------------------------------------------------------
# Walk cycle (stride <-> plant) — di-align ke foot + tinggi konsisten
# ---------------------------------------------------------------------------
def _foot_anchor(im):
    box = im.getbbox()
    if not box:
        return im.size[0] // 2, im.size[1] - 1
    l, t, r, b = box
    band_top = t + int((b - t) * 0.86)
    px = im.load()
    sx = sy = n = 0
    for y in range(band_top, b):
        for x in range(l, r):
            if px[x, y][3] > 80:
                sx += x
                sy += y
                n += 1
    if n < 8:
        return (l + r) // 2, b - 1
    return sx // n, sy // n


def _normalise_height(im, h):
    w0, h0 = im.size
    if h0 <= 0:
        return im
    scale = h / float(h0)
    return im.resize((max(8, int(round(w0 * scale))), int(round(h))),
                     Image.LANCZOS)


def bake_walk():
    """2 frame: stride (walk) <-> plant (idle)."""
    sources = [("walk", os.path.join(HEROES, "zephyr_walk.png")),
               ("idle", os.path.join(HEROES, "zephyr_idle.png"))]
    placed = []
    for label, path in sources:
        if not os.path.isfile(path):
            print("  skip walk (missing %s)" % path)
            continue
        im = Image.open(path).convert("RGBA")
        im = _normalise_height(im, BAKE_H)
        placed.append(im)
    if len(placed) < 2:
        print("  skip walk cycle")
        return
    # align ke anchor kaki yang sama (pakai frame pertama sbg referensi)
    ax0, ay0 = _foot_anchor(placed[0])
    frames = []
    for im in placed:
        ax, ay = _foot_anchor(im)
        # canvas selebar bbox gabungan, anchor kanan bawah
        maxw = max(im.size[0] for im in placed) + 40
        maxh = max(im.size[1] for im in placed) + 40
        canvas = Image.new("RGBA", (maxw, maxh), (0, 0, 0, 0))
        canvas.alpha_composite(im, (int(maxw * 0.6 - ax),
                                    int(maxh - 8 - ay)))
        frames.append(canvas.crop(bbox_alpha(canvas, pad=2)))
    for i, fr in enumerate(frames):
        dst = os.path.join(HEROES, "zephyr_walk_%d.png" % i)
        fr.save(dst)
        print("  walk_%d -> %s  %s" % (i, dst, fr.size))


# ---------------------------------------------------------------------------
# Swing frames — dari art HD (idle + attack), staff benar-benar bergerak
#
# Thorne meng-bake 8 frame terpisah (pinggul -> overhead -> hantam -> pulang).
# Zephyr menyerang dengan magic staff, jadi 8 frame dibuat dari pose HD idle
# (staff santai di sisi) dan attack (staff ditusuk/teracung ke depan) dengan
# transisi rotasi/lereng/lunge yang halus agar staff terlihat mengayun tanpa
# perlu 8 render art terpisah. Semua frame di-normalisasi ke tinggi yang sama
# dan di-anchor di kaki supaya konsisten dengan idle/walk.
# ---------------------------------------------------------------------------
def _rot_sprite(im, angle):
    if abs(angle) < 0.01:
        return im.copy()
    # expand on rotate agar tidak terpotong
    return im.rotate(angle, resample=Image.BICUBIC, expand=True)


def swing_frames():
    """Bake 8-frame staff cast dari HD idle + attack, kaki di-anchor sama.

    Mengikuti pola bake_aligned milik Thorne: semua pose dipasang di satu
    canvas dengan foot_anchor di titik yang sama, lalu di-crop ke bbox
    gabungan dan di-scale ke tinggi konsisten.  Dengan begitu saat diblit
    dengan mid-bottom di (x, foot_y), kaki tidak pernah terlihat
    melompat-lompat antar frame.
    """
    idle_path = os.path.join(HEROES, "zephyr_idle.png")
    attack_path = os.path.join(HEROES, "zephyr_attack.png")
    if not (os.path.isfile(idle_path) and os.path.isfile(attack_path)):
        print("  skip swing (butuh zephyr_idle.png & zephyr_attack.png)")
        return []

    # Mapping pose + rotasi (sudut kecil, CCW positif = condong ke kanan).
    #  0 idle   | staff santai di sisi
    #  1 idle   | angkat awal (windup)
    #  2 attack | staff teracung naik
    #  3 attack | puncak (peak)
    #  4 attack | tusuk ke depan (impact)
    #  5 attack | follow-through
    #  6 idle   | kembali (recovery)
    #  7 idle   | istirahat (rest)
    plan = [
        ("idle",   0.0),
        ("idle",  -6.0),
        ("attack", -5.0),
        ("attack",  0.0),
        ("attack",  5.0),
        ("attack",  9.0),
        ("idle",   5.0),
        ("idle",   0.0),
    ]

    # Normalisasi tinggi + anchor kaki di canvas bersama (seperti Thorne).
    frames = []
    for i, (pose, ang) in enumerate(plan):
        src = idle_path if pose == "idle" else attack_path
        im = _normalise_height(Image.open(src).convert("RGBA"), BAKE_H)
        fr = _rot_sprite(im, ang)
        box = bbox_alpha(fr, pad=2)
        if box:
            fr = fr.crop(box)
        frames.append(fr)

    max_w = max(f.size[0] for f in frames)
    max_h = max(f.size[1] for f in frames)
    cw = max_w + 80
    ch = max_h + 60
    fx, fy = cw // 2, ch - 16

    def place(im):
        # pasang di canvas dengan foot_anchor di (fx, fy)
        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        ax, ay = _foot_anchor(im)
        canvas.alpha_composite(im, (int(fx - ax), int(fy - ay)))
        return canvas

    placed = [place(f) for f in frames]

    union = None
    for im in placed:
        box = im.getbbox()
        if box is None:
            continue
        if union is None:
            union = list(box)
        else:
            union[0] = min(union[0], box[0])
            union[1] = min(union[1], box[1])
            union[2] = max(union[2], box[2])
            union[3] = max(union[3], box[3])
    union = tuple(union)
    crop_h = max(1, union[3] - union[1])
    scale = BAKE_H / float(crop_h)
    out_w = max(8, int(round((union[2] - union[0]) * scale)))
    out_h = max(8, int(round(crop_h * scale)))

    out = []
    for i, im in enumerate(placed):
        cropped = im.crop(union)
        baked = cropped.resize((out_w, out_h), Image.LANCZOS)
        dst = os.path.join(HEROES, "zephyr_swing_%d.png" % i)
        baked.save(dst)
        print("  swing_%d -> %s  %dx%d" % (i, dst, baked.size[0], baked.size[1]))
        out.append(baked)
    return out


# ---------------------------------------------------------------------------
# Skill FX (Q/W/E/R) — base-layer art dilukis langsung pada 512px (bukan
# snapshot renderer kecil), supaya saat di-scale ke tingi render tetap besar
# dan tajam seperti skill Thorne.  Pola Thorne: sprite HD diblit sebagai base
# layer, lalu efek animasi prosedural (proyektil/lingkaran) digambar di atas.
# ---------------------------------------------------------------------------
def _gradient_circle(img, cx, cy, radius, inner, outer):
    px = img.load()
    w, h = img.size
    r0 = max(1, int(radius))
    x0 = max(0, cx - r0)
    x1 = min(w, cx + r0 + 1)
    y0 = max(0, cy - r0)
    y1 = min(h, cy + r0 + 1)
    ir, ig, ib, ia = inner
    or_, og, ob, oa = outer
    r2 = r0 * r0
    for y in range(y0, y1):
        dy = y - cy
        for x in range(x0, x1):
            dx = x - cx
            d2 = dx * dx + dy * dy
            if d2 > r2:
                continue
            t = math.sqrt(d2) / float(r0)
            t = t * t  # keep core brighter
            a = int(ia + (oa - ia) * t)
            if a <= 0:
                continue
            r = int(ir + (or_ - ir) * t)
            g = int(ig + (og - ig) * t)
            b = int(ib + (ob - ib) * t)
            pr, pg, pb, pa = px[x, y]
            out_a = a + pa * (255 - a) // 255
            if out_a <= 0:
                continue
            px[x, y] = (
                (r * a + pr * pa * (255 - a) // 255) // out_a,
                (g * a + pg * pa * (255 - a) // 255) // out_a,
                (b * a + pb * pa * (255 - a) // 255) // out_a,
                out_a,
            )


def _draw_spike(draw, cx, cy, length, angle, thick, dark, mid, light, tip):
    ca, sa = math.cos(angle), math.sin(angle)
    px, py = -sa, ca
    tip_x = cx + ca * length
    tip_y = cy + sa * length
    base_l = (cx + px * thick, cy + py * thick)
    base_r = (cx - px * thick, cy - py * thick)
    mid_l = (cx + ca * length * 0.55 + px * thick * 0.55,
             cy + sa * length * 0.55 + py * thick * 0.55)
    mid_r = (cx + ca * length * 0.55 - px * thick * 0.55,
             cy + sa * length * 0.55 - py * thick * 0.55)
    draw.polygon([base_l, mid_l, (tip_x, tip_y), mid_r, base_r], fill=dark)
    draw.polygon([
        (cx + px * thick * 0.45, cy + py * thick * 0.45),
        mid_l, (tip_x, tip_y),
        (cx + ca * length * 0.55, cy + sa * length * 0.55),
    ], fill=mid)
    draw.line([(cx, cy), (tip_x, tip_y)], fill=light, width=max(1, thick // 3))
    r = max(2, thick // 2)
    draw.ellipse((tip_x - r, tip_y - r, tip_x + r, tip_y + r), fill=tip)


def _small_fairy(draw, cx, cy, s, color, light):
    # wings
    for side in (-1, 1):
        draw.polygon([(cx, cy - s),
                      (cx + side * s, cy - s * 2),
                      (cx + side * s // 2, cy - s)], fill=color)
    # body skirt
    draw.polygon([(cx - s // 2, cy - s),
                  (cx + s // 2, cy - s),
                  (cx + s // 2, cy + s // 2),
                  (cx - s // 2, cy + s // 2)], fill=color)
    # head
    draw.ellipse((cx - s // 2, cy - s * 2 - 1,
                  cx + s // 2, cy - s - 1), fill=light)


def bake_skill_q():
    """Bramble Maze — ring of thorny brambles erupting from centre."""
    s = SKILL_SIZE
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    cx, cy = s // 2, s // 2
    _gradient_circle(img, cx, cy, 250, (120, 15, 95, 55), (40, 5, 40, 0))
    _gradient_circle(img, cx, cy, 150, (220, 40, 160, 110), (90, 20, 80, 0))
    d = ImageDraw.Draw(img)
    # concentric ground rings
    for ring, col, wth in ((200, (200, 40, 150, 170), 6),
                           (150, (230, 80, 175, 200), 4),
                           (100, (255, 130, 205, 180), 3)):
        d.ellipse((cx - ring, cy - ring * 0.5,
                   cx + ring, cy + ring * 0.5), outline=col, width=wth)
    # thorny vines radiating upward/outward
    n = 14
    for i in range(n):
        a = -math.pi / 2 + (i - (n - 1) / 2.0) * (math.pi / n) * 1.3
        bx = cx + math.cos(a) * 40
        by = cy - math.sin(a) * 35
        length = 130 + (14 if i % 2 == 0 else -10)
        _draw_spike(d, bx, by, length, a + math.pi, 10,
                    (60, 10, 65, 255), (120, 35, 120, 255),
                    (200, 80, 170, 255), (255, 130, 205, 255))
        # smaller thorns on each vine
        for th in (0.35, 0.6):
            tx = bx + math.cos(a + math.pi) * length * th
            ty = by + math.sin(a + math.pi) * length * th
            for da in (-0.5, 0.5):
                _draw_spike(d, tx, ty, 22 + th * 10, a + math.pi + da, 4,
                            (60, 10, 65, 255), (120, 35, 120, 255),
                            (200, 80, 170, 255), (255, 150, 215, 255))
    _gradient_circle(img, cx, cy, 55, (255, 200, 235, 200), (230, 60, 170, 0))
    # butterflies floating out
    for i in range(5):
        a = i * (2 * math.pi / 5) + 0.3
        r = 120 + (i % 2) * 30
        fx = int(cx + math.cos(a) * r)
        fy = int(cy + math.sin(a) * r * 0.5)
        s2 = 9 + (i % 3) * 2
        for side in (-1, 1):
            d.polygon([(fx, fy), (fx + side * s2 * 2, fy - s2 - 2),
                       (fx + side * s2, fy)], fill=(190, 60, 165, 220))
            d.polygon([(fx, fy), (fx + side * s2, fy + s2 + 1),
                       (fx + side * s2 // 2, fy)], fill=(150, 40, 130, 200))
    return img


def bake_skill_w():
    """Shadow Realm — translucent purple bubble prison."""
    s = SKILL_SIZE
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    cx, cy = s // 2, s // 2
    _gradient_circle(img, cx, cy, 240, (130, 40, 150, 60), (50, 10, 60, 0))
    R = 190
    d = ImageDraw.Draw(img)
    # bubble rings
    for r_off in (0, 6, 12):
        col = (200, 120, 220, 140 - r_off * 25)
        d.ellipse((cx - R + r_off, cy - R + r_off,
                   cx + R - r_off, cy + R - r_off), outline=col, width=5)
    # inner shading
    _gradient_circle(img, cx, cy, R - 10, (110, 30, 120, 40), (40, 8, 50, 0))
    # swirling energy
    for i in range(6):
        a = i * math.pi / 3
        px = cx + math.cos(a) * (R - 40)
        py = cy + math.sin(a) * (R - 40)
        d.ellipse((px - 8, py - 8, px + 8, py + 8), fill=(255, 150, 220, 200))
    # runes around rim
    for i in range(10):
        a = i * 2 * math.pi / 10
        rx = cx + math.cos(a) * (R - 6)
        ry = cy + math.sin(a) * (R - 6)
        d.ellipse((rx - 6, ry - 6, rx + 6, ry + 6), fill=(180, 80, 190, 230))
        d.ellipse((rx - 3, ry - 3, rx + 3, ry + 3), fill=(255, 200, 235, 240))
    # bright highlight (top-left)
    hx, hy = cx - R // 2, cy - R // 2
    _gradient_circle(img, hx, hy, 55, (255, 210, 245, 210), (200, 120, 220, 0))
    _gradient_circle(img, hx, hy, 26, (255, 245, 255, 255), (255, 180, 240, 0))
    return img


def bake_skill_e():
    """Casket Curse — ghostly skull casket with feathery flame."""
    s = SKILL_SIZE
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    cx, cy = s // 2, s // 2
    _gradient_circle(img, cx, cy, 220, (150, 20, 110, 55), (50, 5, 45, 0))
    _gradient_circle(img, cx, cy, 130, (230, 50, 165, 120), (100, 20, 85, 0))
    d = ImageDraw.Draw(img)
    # feathery flame petals radiating (casket is thrown as a skull)
    n = 16
    for i in range(n):
        a = i * 2 * math.pi / n + 0.2
        length = 100 + (16 if i % 2 == 0 else -12)
        _draw_spike(d, cx + math.cos(a) * 30, cy + math.sin(a) * 30,
                    length, a, 7,
                    (70, 15, 70, 255), (140, 40, 130, 255),
                    (220, 90, 180, 255), (255, 160, 220, 255))
    # skull dome
    _gradient_circle(img, cx, cy + 4, 96, (255, 180, 220, 255), (150, 50, 130, 255))
    _gradient_circle(img, cx, cy - 6, 78, (255, 210, 235, 255), (200, 90, 175, 255))
    # eye sockets
    for side in (-1, 1):
        ex = cx + side * 34
        _gradient_circle(img, ex, cy - 2, 20, (30, 5, 35, 255), (90, 20, 80, 255))
        # glow inside
        _gradient_circle(img, ex, cy - 2, 9, (255, 120, 200, 255), (200, 40, 150, 255))
    # jaw teeth
    for i in range(-2, 3):
        tx = cx + i * 16
        d.rectangle((tx - 4, cy + 54, tx + 4, cy + 78), fill=(235, 150, 205, 230))
    # top flame petals
    for i in range(5):
        a = -math.pi / 2 + (i - 2) * 0.35
        _draw_spike(d, cx, cy - 40, 60 + abs(2 - i) * 8, a, 6,
                    (90, 20, 80, 255), (170, 60, 130, 255),
                    (240, 120, 190, 255), (255, 200, 235, 255))
    return img


def bake_skill_r():
    """Bedlam — mini-fairy duplicates orbiting in a swirl."""
    s = SKILL_SIZE
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    cx, cy = s // 2, s // 2
    _gradient_circle(img, cx, cy, 250, (150, 25, 110, 55), (50, 5, 45, 0))
    d = ImageDraw.Draw(img)
    # orbit rings
    for ring, col, wth in ((210, (210, 60, 155, 170), 6),
                           (160, (240, 110, 185, 200), 4),
                           (110, (255, 160, 215, 170), 3)):
        d.ellipse((cx - ring, cy - ring * 0.45,
                   cx + ring, cy + ring * 0.45), outline=col, width=wth)
    # swirl arcs connecting duplicates
    for i in range(3):
        a0 = i * 2 * math.pi / 3
        for seg in range(16):
            t1 = seg / 16.0
            t2 = (seg + 1) / 16.0
            ang1 = a0 + t1 * math.pi * 1.3
            ang2 = a0 + t2 * math.pi * 1.3
            R = 185
            x1 = cx + math.cos(ang1) * R
            y1 = cy + math.sin(ang1) * R * 0.45
            x2 = cx + math.cos(ang2) * R
            y2 = cy + math.sin(ang2) * R * 0.45
            d.line([(x1, y1), (x2, y2)], fill=(255, 150, 215, 200), width=3)
    # mini-fairies on the orbit
    N = 6
    for i in range(N):
        a = i * 2 * math.pi / N + 0.4
        R = 165
        fx = int(cx + math.cos(a) * R)
        fy = int(cy + math.sin(a) * R * 0.45)
        _small_fairy(d, fx, fy, 14, (190, 55, 165, 240), (255, 160, 215, 255))
    # sparkles
    for i in range(14):
        a = i * 2 * math.pi / 14 + 0.1
        r = 90 + (i % 3) * 25
        sx = cx + math.cos(a) * r
        sy = cy + math.sin(a) * r * 0.5
        d.ellipse((sx - 5, sy - 5, sx + 5, sy + 5), fill=(255, 180, 225, 220))
        d.ellipse((sx - 2, sy - 2, sx + 2, sy + 2), fill=(255, 240, 250, 255))
    # centre glow
    _gradient_circle(img, cx, cy, 48, (255, 200, 235, 210), (230, 60, 170, 0))
    return img


def bake_skills():
    makers = {"q": bake_skill_q, "w": bake_skill_w,
              "e": bake_skill_e, "r": bake_skill_r}
    for key, fn in makers.items():
        im = fn()
        dst = os.path.join(HEROES, "zephyr_skill_%s.png" % key)
        im.save(dst, "PNG")
        print("  skill %s -> %s  %dx%d" % (key, dst, im.size[0], im.size[1]))


# ---------------------------------------------------------------------------
# Preview contact sheet (untuk inspeksi visual di docs/)
# ---------------------------------------------------------------------------
def contact_sheet(frames, labels, cell_w, cell_h, title, path):
    n = len(frames)
    pad = 16
    header = 48
    W = pad + n * (cell_w + pad)
    H = header + cell_h + pad + 28
    import PIL.Image as I
    sheet = I.new("RGB", (W, H), (14, 12, 22))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 12), title, fill=(255, 120, 190))
    def checker(w, h):
        im = I.new("RGB", (w, h), (18, 16, 28))
        p = im.load()
        for y in range(h):
            for x in range(w):
                if ((x // 16) + (y // 16)) & 1:
                    p[x, y] = (30, 24, 40)
        return im
    for i, (fr, lab) in enumerate(zip(frames, labels)):
        x = pad + i * (cell_w + pad)
        y = header
        bg = checker(cell_w, cell_h)
        fw, fh = fr.size
        scale = min(cell_w / float(fw), cell_h / float(fh))
        nw, nh = max(1, int(fw * scale)), max(1, int(fh * scale))
        rs = fr.resize((nw, nh), I.LANCZOS)
        bg.paste(rs, ((cell_w - nw) // 2, cell_h - nh), rs)
        sheet.paste(bg, (x, y))
        d.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), outline=(220, 90, 160))
        d.text((x + 6, y + cell_h + 6), lab, fill=(230, 225, 240))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sheet.save(path, "PNG")
    print("  preview", path)


def main():
    print("== body HD ==")
    bake_body()
    print("== walk cycle ==")
    bake_walk()
    print("== swing frames ==")
    swing = swing_frames()
    print("== skill FX (karakter-sentris) ==")
    bake_skills()

    # Preview strips untuk inspeksi visual
    if swing:
        contact_sheet(
            swing,
            ["0 idle", "1 wind", "2 raise", "3 peak",
             "4 impact", "5 hold", "6 back", "7 rest"],
            150, 170,
            "ZEPHYR  —  HD STAFF CAST  (staff moves)",
            os.path.join(DOCS, "zephyr_swing_strip.png"),
        )
    for k in "qwer":
        p = os.path.join(HEROES, "zephyr_skill_%s.png" % k)
        if os.path.isfile(p):
            try:
                im = Image.open(p).convert("RGBA")
                contact_sheet([im], [k.upper()], 180, 180,
                              "ZEPHYR  —  HD SKILL %s" % k.upper(),
                              os.path.join(DOCS, "zephyr_skill_preview.png"))
                break
            except Exception as e:
                print("  preview skip:", e)
    print("done ->", HEROES)


if __name__ == "__main__":
    main()
