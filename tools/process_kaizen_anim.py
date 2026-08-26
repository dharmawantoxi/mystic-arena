#!/usr/bin/env python3
"""Bake Kaizen HD body + walk / swing / skill sprites (gaya ala Thorne).

Meniru tools/process_zephyr_anim.py (yang meniru tools/process_thorne_anim.py)
untuk hero Kaizen, sang Wind Blade Assassin.

Sumber
──────
assets/heroes/_raw/kaizen_<pose>_raw.png   →   render digital HD (latar hitam)

Keluaran (semua RGBA transparan, di-trim, di-align)
───────
assets/heroes/kaizen_idle.png              body idle HD
assets/heroes/kaizen_walk.png              body walk HD  (stride)
assets/heroes/kaizen_attack.png            body attack HD (iai slash)
assets/heroes/kaizen_walk_0.png / _1.png   walk cycle (stride <-> plant)
assets/heroes/kaizen_swing_0..7.png        animasi serangan (katana bergerak)
assets/heroes/kaizen_skill_q/w/e/r.png     efek skill Q/W/E/R (baked 512px)

Aset __raw__ di-ignore (lihat .gitignore). Kalau file raw hilang, tool ini
tidak merusak apa-apa: renderer Kaizen tetap punya fallback prosedural.

Run:  /tmp/kaizen-venv/bin/python tools/process_kaizen_anim.py
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
# di-scale ke KAIZEN_SPRITE_HEIGHT (~110 px), jadi menyimpan file 1500-an px
# hanya membuang memori & memperlambat load Android.  Tinggi ~648 px sudah
# jauh lebih besar dari render dan tetap terlihat tajam setelah smoothscale.
BODY_MAX_H = 648

# Palet wind Kaizen (harus sama dgn _NS_kaizen.PALETTE di heroes/_bundle.py)
WIND_DARKEST = (30, 60, 110, 255)
WIND_DARK = (55, 110, 175, 255)
WIND_MID = (110, 175, 230, 255)
WIND_LIGHT = (175, 220, 250, 255)
WIND_BRIGHT = (215, 240, 255, 255)
WIND_WHITE = (245, 252, 255, 255)
STEEL_DARK = (90, 105, 125, 255)
STEEL_MID = (155, 170, 190, 255)
STEEL_LIGHT = (210, 220, 235, 255)
STEEL_SHINE = (245, 250, 255, 255)
SCARF_DARK = (40, 70, 140, 255)
SCARF_MID = (75, 120, 200, 255)
SCARF_LIGHT = (130, 175, 240, 255)


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
        src = os.path.join(RAW, "kaizen_%s_raw.png" % pose)
        dst = os.path.join(HEROES, "kaizen_%s.png" % pose)
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
    sources = [("walk", os.path.join(HEROES, "kaizen_walk.png")),
               ("idle", os.path.join(HEROES, "kaizen_idle.png"))]
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
        dst = os.path.join(HEROES, "kaizen_walk_%d.png" % i)
        fr.save(dst)
        print("  walk_%d -> %s  %s" % (i, dst, fr.size))


# ---------------------------------------------------------------------------
# Swing frames — dari art HD (idle + attack), katana benar-benar mengayun
#
# Thorne meng-bake 8 frame terpisah (pinggul -> overhead -> hantam -> pulang).
# Zephyr meng-bake 8 frame staff cast dari idle + attack.  Kaizen menyerang
# dengan katana (iai slash diagonal), jadi 8 frame dibuat dari pose HD idle
# (katana santai di sisi) dan attack (slash dua tangan + trail angin) dengan
# transisi rotasi/windup/lunge yang halus agar pedang terlihat mengayun tanpa
# perlu 8 render art terpisah.  Semua frame di-normalisasi ke tinggi yang sama
# dan di-anchor di kaki supaya konsisten dengan idle/walk.
# ---------------------------------------------------------------------------
def _rot_sprite(im, angle):
    if abs(angle) < 0.01:
        return im.copy()
    # expand on rotate agar tidak terpotong
    return im.rotate(angle, resample=Image.BICUBIC, expand=True)


def swing_frames():
    """Bake 8-frame iai slash dari HD idle + attack, kaki di-anchor sama."""
    idle_path = os.path.join(HEROES, "kaizen_idle.png")
    attack_path = os.path.join(HEROES, "kaizen_attack.png")
    if not (os.path.isfile(idle_path) and os.path.isfile(attack_path)):
        print("  skip swing (butuh kaizen_idle.png & kaizen_attack.png)")
        return []

    # Mapping pose + rotasi (sudut kecil; positif = condong ke belakang /
    # windup, negatif = lunge ke depan saat slash).
    #  0 idle   | katana santai di sisi (rest)
    #  1 idle   | tarik napas, sedikit condong ke belakang (breathe)
    #  2 attack | windup: pedang terangkat ke belakang
    #  3 attack | puncak windup (peak)
    #  4 attack | slash ke depan (impact)
    #  5 attack | follow-through
    #  6 idle   | kembali (recovery)
    #  7 idle   | istirahat (rest)
    plan = [
        ("idle",   0.0),
        ("idle",   3.5),
        ("attack",  5.0),
        ("attack",  2.0),
        ("attack", -3.0),
        ("attack", -7.0),
        ("idle",  -3.5),
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
        dst = os.path.join(HEROES, "kaizen_swing_%d.png" % i)
        baked.save(dst)
        print("  swing_%d -> %s  %dx%d" % (i, dst, baked.size[0], baked.size[1]))
        out.append(baked)
    return out


# ---------------------------------------------------------------------------
# Skill FX (Q/W/E/R) — efek angin karakter-sentris dilukis pada 512px,
# palet cyan/putih sama dengan _NS_kaizen.PALETTE ("wind_*").
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


def _draw_crescent(img, cx, cy, radius, a0, a1, thick, col_dark, col_mid,
                   col_light, squash=0.35):
    """Crescent slash arc (bilah angin melengkung)."""
    d = ImageDraw.Draw(img)
    steps = max(12, int(abs(a1 - a0) * 24))
    pts_out, pts_in = [], []
    for i in range(steps + 1):
        t = i / float(steps)
        a = a0 + (a1 - a0) * t
        th = thick * math.sin(t * math.pi) ** 0.7
        xo = cx + math.cos(a) * radius
        yo = cy + math.sin(a) * radius * squash
        xi = cx + math.cos(a) * (radius - th)
        yi = cy + math.sin(a) * (radius - th) * squash
        pts_out.append((xo, yo))
        pts_in.append((xi, yi))
    d.polygon(pts_out + pts_in[::-1], fill=col_dark)
    # inner bright edge
    pts_out2, pts_in2 = [], []
    for i in range(steps + 1):
        t = i / float(steps)
        a = a0 + (a1 - a0) * t
        th = thick * math.sin(t * math.pi) ** 0.7
        xo = cx + math.cos(a) * (radius - th * 0.25)
        yo = cy + math.sin(a) * (radius - th * 0.25) * squash
        xi = cx + math.cos(a) * (radius - th * 0.75)
        yi = cy + math.sin(a) * (radius - th * 0.75) * squash
        pts_out2.append((xo, yo))
        pts_in2.append((xi, yi))
    d.polygon(pts_out2 + pts_in2[::-1], fill=col_mid)
    # thin hot edge
    pts_out3, pts_in3 = [], []
    for i in range(steps + 1):
        t = i / float(steps)
        a = a0 + (a1 - a0) * t
        th = thick * math.sin(t * math.pi) ** 0.7
        xo = cx + math.cos(a) * (radius - th * 0.05)
        yo = cy + math.sin(a) * (radius - th * 0.05) * squash
        xi = cx + math.cos(a) * (radius - th * 0.30)
        yi = cy + math.sin(a) * (radius - th * 0.30) * squash
        pts_out3.append((xo, yo))
        pts_in3.append((xi, yi))
    d.polygon(pts_out3 + pts_in3[::-1], fill=col_light)


def _draw_swirl(img, cx, cy, r, color, width, turns=1.0, phase=0.0):
    """Spiral wind swirl."""
    d = ImageDraw.Draw(img)
    steps = max(10, int(turns * 36))
    pts = []
    for i in range(steps + 1):
        t = i / float(steps)
        a = phase + t * turns * 2 * math.pi
        rr = r * (0.25 + 0.75 * t)
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.85))
    d.line(pts, fill=color, width=width, joint="curve")


def bake_skill_q():
    """Steel Wind / Dash Strike — triple crescent slash + speed lines."""
    s = SKILL_SIZE
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    cx, cy = s // 2, s // 2
    # core glow horizontal (dash direction)
    _gradient_circle(img, cx, cy, 240, (40, 110, 180, 60), (10, 30, 70, 0))
    _gradient_circle(img, cx, cy, 150, (110, 175, 230, 110), (30, 60, 110, 0))
    d = ImageDraw.Draw(img)
    # horizontal speed streaks
    for i in range(9):
        yy = cy + (i - 4) * 22
        ln = 320 - abs(i - 4) * 44
        x0 = cx - ln // 2 + (i % 2) * 18
        col = (WIND_BRIGHT if i % 2 == 0 else WIND_LIGHT)
        a = 150 + (4 - abs(i - 4)) * 18
        d.line((x0, yy, x0 + ln, yy), fill=(*col[:3], min(235, a)),
               width=5 if i % 2 == 0 else 3)
    # triple crescent slashes (steel wind combo)
    for k, (dx, rad, th) in enumerate(((-95, 120, 26), (0, 150, 32), (95, 120, 26))):
        _draw_crescent(img, cx + dx, cy, rad,
                       math.pi * 1.12, math.pi * 1.88, th,
                       (25, 55, 105, 210), WIND_MID, WIND_WHITE)
    # steel glints
    for gx, gy in ((cx - 150, cy - 40), (cx + 150, cy - 40),
                   (cx - 150, cy + 46), (cx + 150, cy + 46)):
        d.line((gx - 14, gy, gx + 14, gy), fill=STEEL_SHINE, width=3)
        d.line((gx, gy - 8, gx, gy + 8), fill=STEEL_LIGHT, width=2)
    _gradient_circle(img, cx, cy, 52, (255, 255, 255, 200),
                     (110, 175, 230, 0))
    return img


def bake_skill_w():
    """Wind Wall — dinding angin vertikal berputar."""
    s = SKILL_SIZE
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    cx, cy = s // 2, s // 2
    _gradient_circle(img, cx, cy, 250, (40, 110, 180, 55), (10, 30, 70, 0))
    d = ImageDraw.Draw(img)
    # wall body: kolom swirl vertikal (3 kolom x 5 lingkar)
    for col in range(3):
        wx = cx + (col - 1) * 92
        for row in range(5):
            wy = cy - 176 + row * 88
            r = 44 if col == 1 else 36
            col_a = 205 - row * 12
            _draw_swirl(img, wx, wy, r, (*WIND_DARK[:3], col_a - 60), 7,
                        turns=1.15, phase=row * 1.3 + col * 0.9)
            _draw_swirl(img, wx, wy, r - 12, (*WIND_MID[:3], col_a), 5,
                        turns=1.0, phase=row * 1.3 + col * 0.9 + 0.7)
            _draw_swirl(img, wx, wy, r - 24, (*WIND_LIGHT[:3], col_a), 3,
                        turns=0.85, phase=row * 1.3 + col * 0.9 + 1.4)
    # vertical streaks
    for i in range(7):
        sx = cx - 150 + i * 50
        y0 = cy - 200 + ((i * 37) % 80)
        y1 = y0 + 300
        d.line((sx, y0, sx, y1), fill=(*WIND_LIGHT[:3], 150), width=3)
        d.line((sx + 3, y0 + 12, sx + 3, y1 - 12), fill=(*WIND_WHITE[:3], 190),
               width=2)
    # energy caps
    for cyy in (cy - 208, cy + 208):
        d.ellipse((cx - 26, cyy - 13, cx + 26, cyy + 13),
                  outline=(*WIND_BRIGHT[:3], 230), width=5)
        d.ellipse((cx - 12, cyy - 6, cx + 12, cyy + 6),
                  fill=(*WIND_WHITE[:3], 240))
    return img


def bake_skill_e():
    """Sweep — AOE jump: ring tanah + bilah angin naik ke atas."""
    s = SKILL_SIZE
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    cx, cy = s // 2, s // 2
    gy = cy + 90
    _gradient_circle(img, cx, gy, 220, (40, 110, 180, 70), (10, 30, 70, 0))
    d = ImageDraw.Draw(img)
    # ground rings (perspective ellipse)
    for ring, col, wth in ((195, (*WIND_MID[:3], 190), 7),
                           (150, (*WIND_BRIGHT[:3], 210), 5),
                           (105, (*WIND_WHITE[:3], 190), 3)):
        d.ellipse((cx - ring, gy - ring * 0.42,
                   cx + ring, gy + ring * 0.42), outline=col, width=wth)
    # rising wind blades around ring
    n = 12
    for i in range(n):
        a = i * 2 * math.pi / n
        r = 160
        bx = cx + math.cos(a) * r
        by = gy + math.sin(a) * r * 0.42
        hgt = 120 + (26 if i % 2 == 0 else -18)
        # tapered spike going up
        top = (bx + math.cos(a) * 14, by - hgt)
        d.polygon([(bx - 11, by), (bx + 11, by), top],
                  fill=(*WIND_DARK[:3], 210))
        d.polygon([(bx - 5, by), (bx + 5, by),
                   (bx + math.cos(a) * 8, by - hgt + 14)],
                  fill=(*WIND_MID[:3], 235))
        d.line((bx, by - 8, top[0], top[1] + 12),
               fill=(*WIND_WHITE[:3], 240), width=2)
        # swirl base
        _draw_swirl(img, bx, by - 4, 20, (*WIND_LIGHT[:3], 170), 3,
                    turns=0.8, phase=a)
    # central burst
    _gradient_circle(img, cx, gy - 20, 60, (255, 255, 255, 190),
                     (110, 175, 230, 0))
    _draw_crescent(img, cx, gy - 30, 120, math.pi * 1.1, math.pi * 1.9, 22,
                   (25, 55, 105, 190), WIND_MID, WIND_WHITE, squash=0.6)
    return img


def bake_skill_r():
    """Tornado — ultimate vortex raksasa."""
    s = SKILL_SIZE
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    cx = s // 2
    base_y = s - 60
    _gradient_circle(img, cx, base_y - 150, 235, (40, 110, 180, 55),
                     (10, 30, 70, 0))
    d = ImageDraw.Draw(img)
    # stacked rotating rings: sempit di bawah, lebar di atas
    layers = 11
    for i in range(layers):
        t = i / float(layers - 1)
        ly = base_y - t * 340
        r = 26 + t * 148
        swirl = math.sin(t * 9.0) * 14
        lx = cx + swirl
        d.ellipse((lx - r, ly - r * 0.22, lx + r, ly + r * 0.22),
                  outline=(*WIND_DARK[:3], 175), width=7)
        d.ellipse((lx - r + 6, ly - r * 0.22 + 2, lx + r - 6, ly + r * 0.22 - 2),
                  outline=(*WIND_MID[:3], 205), width=4)
        if i % 2 == 0:
            d.ellipse((lx - r + 14, ly - r * 0.22 + 4, lx + r - 14,
                       ly + r * 0.22 - 4),
                      outline=(*WIND_BRIGHT[:3], 185), width=2)
    # bright core
    for i in range(layers * 2):
        t = i / float(layers * 2 - 1)
        ly = base_y - t * 330
        rr = 8 + t * 60
        d.line((cx - rr * 0.5, ly, cx + rr * 0.5, ly),
               fill=(*WIND_LIGHT[:3], 120), width=3)
    d.line((cx, base_y - 8, cx + math.sin(1.2) * 10, base_y - 340),
           fill=(*WIND_WHITE[:3], 200), width=4)
    # top opening flare
    _gradient_circle(img, cx, base_y - 348, 70, (255, 255, 255, 210),
                     (110, 175, 230, 0))
    d.ellipse((cx - 40, base_y - 366, cx + 40, base_y - 330),
              outline=(*WIND_BRIGHT[:3], 220), width=5)
    # base dust
    d.ellipse((cx - 90, base_y - 14, cx + 90, base_y + 22),
              fill=(*WIND_DARKEST[:3], 190))
    d.ellipse((cx - 66, base_y - 10, cx + 66, base_y + 16),
              outline=(*WIND_MID[:3], 220), width=4)
    # debris swirls
    for i in range(10):
        t = (i / 10.0)
        ly = base_y - t * 300
        r = 30 + t * 130
        a = i * 1.7
        px_ = cx + math.cos(a) * r
        py_ = ly + math.sin(a) * r * 0.22
        d.ellipse((px_ - 4, py_ - 4, px_ + 4, py_ + 4),
                  fill=(*WIND_WHITE[:3], 215))
    return img


def bake_skills():
    makers = {"q": bake_skill_q, "w": bake_skill_w,
              "e": bake_skill_e, "r": bake_skill_r}
    for key, fn in makers.items():
        im = fn()
        dst = os.path.join(HEROES, "kaizen_skill_%s.png" % key)
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
    sheet = I.new("RGB", (W, H), (12, 14, 22))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 12), title, fill=(110, 200, 255))

    def checker(w, h):
        im = I.new("RGB", (w, h), (16, 18, 28))
        p = im.load()
        for y in range(h):
            for x in range(w):
                if ((x // 16) + (y // 16)) & 1:
                    p[x, y] = (26, 30, 44)
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
        d.rectangle((x, y, x + cell_w - 1, y + cell_h - 1),
                    outline=(90, 160, 220))
        d.text((x + 6, y + cell_h + 6), lab, fill=(230, 235, 245))
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
            ["0 rest", "1 wind", "2 raise", "3 peak",
             "4 slash", "5 through", "6 back", "7 hold"],
            150, 170,
            "KAIZEN  —  HD KATANA IAI SLASH  (blade moves)",
            os.path.join(DOCS, "kaizen_swing_strip.png"),
        )
    skill_frames = []
    for k in "qwer":
        p = os.path.join(HEROES, "kaizen_skill_%s.png" % k)
        if os.path.isfile(p):
            skill_frames.append(Image.open(p).convert("RGBA"))
    if skill_frames:
        contact_sheet(
            skill_frames, ["Q steel wind", "W wind wall",
                           "E sweep", "R tornado"],
            180, 180,
            "KAIZEN  —  HD SKILL FX",
            os.path.join(DOCS, "kaizen_skill_preview.png"),
        )
    body = []
    for pose in ("idle", "walk", "attack"):
        p = os.path.join(HEROES, "kaizen_%s.png" % pose)
        if os.path.isfile(p):
            body.append(Image.open(p).convert("RGBA"))
    if body:
        contact_sheet(
            body, ["idle", "walk", "attack"], 170, 190,
            "KAIZEN  —  HD BODY POSES",
            os.path.join(DOCS, "kaizen_body_preview.png"),
        )
    print("done ->", HEROES)


if __name__ == "__main__":
    main()
