#!/usr/bin/env python3
"""Bake Thorne HD walk / swing / skill sprites.

Swing mapping (club MUST move — do not bake 8 copies of the overhead pose):
  0 idle              club at the hip          (wind-up start)
  1 attack.png        club overhead            (raise)
  2 swing_1_raw       club overhead, back      (peak)
  3 swing_5_raw       club vertical in front   (coming down)
  4 swing_4_raw       club smashing forward    (impact)
  5 swing_6_raw       club low-forward         (follow-through)
  6 swing_7_raw       club returning to hip    (recovery)
  7 idle              club at the hip          (rest)

Walk is a 2-frame stride (walk.png <-> idle.png) consumed by the renderer.
Skill FX are painted at 512px so they match the HD body, not the old 210px dots.

Run:  /tmp/thorne-venv/bin/python tools/process_thorne_anim.py
"""
from __future__ import print_function

import math
import os
from collections import deque

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEROES = os.path.join(ROOT, "assets", "heroes")
RAW = os.path.join(HEROES, "_raw")
DOCS = os.path.join(ROOT, "docs")

BAKE_H = 320
SKILL_SIZE = 512
DARK_T = 42


# ---------------------------------------------------------------------------
# Background removal
# ---------------------------------------------------------------------------
def _luma(r, g, b):
    return 0.299 * r + 0.587 * g + 0.114 * b


def _sat(r, g, b):
    mx = max(r, g, b)
    mn = min(r, g, b)
    return 0.0 if mx == 0 else (mx - mn) / float(mx)


def _is_edge_bg(r, g, b, a, paper=False):
    """Dark studio backdrop, or (if paper) cream + gray drop-shadow matte."""
    if a < 20:
        return True
    mx = max(r, g, b)
    if mx < DARK_T:
        return True
    if not paper:
        return False
    luma = _luma(r, g, b)
    sat = _sat(r, g, b)
    if luma > 205 and sat < 0.32:
        return True
    if luma > 95 and sat < 0.20:
        return True
    return False


def _image_is_paper(im):
    """True when most edge pixels are light (generated cream/white canvas)."""
    w, h = im.size
    px = im.load()
    light = tot = 0
    for x in range(0, w, max(1, w // 40)):
        for y in (0, h - 1):
            r, g, b, a = px[x, y]
            tot += 1
            if a > 20 and _luma(r, g, b) > 200:
                light += 1
    for y in range(0, h, max(1, h // 40)):
        for x in (0, w - 1):
            r, g, b, a = px[x, y]
            tot += 1
            if a > 20 and _luma(r, g, b) > 200:
                light += 1
    return tot > 0 and (light / float(tot)) > 0.45


def remove_background(im):
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    paper = _image_is_paper(im)

    bg = bytearray(w * h)
    dq = deque()
    neigh = ((1, 0), (-1, 0), (0, 1), (0, -1),
             (1, 1), (-1, -1), (1, -1), (-1, 1))

    def try_push(x, y):
        i = y * w + x
        if bg[i]:
            return
        r, g, b, a = px[x, y]
        if _is_edge_bg(r, g, b, a, paper=paper):
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

    def is_paper_px(r, g, b):
        return _luma(r, g, b) > 210 and min(r, g, b) > 155

    # Eat white sticker outline / cracks that touch transparency.
    # Repeat so a thick halo peels inward without touching tusks
    # (tusks sit inside brown fur, not on the silhouette edge).
    for _pass in range(6):
        changed = 0
        doomed = []
        for y in range(h):
            for x in range(w):
                i = y * w + x
                if not alpha[i]:
                    continue
                r, g, b, a = px[x, y]
                if not is_paper_px(r, g, b):
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < w and 0 <= ny < h) or not alpha[ny * w + nx]:
                        doomed.append(i)
                        break
        for i in doomed:
            if alpha[i]:
                alpha[i] = 0
                changed += 1
        if not changed:
            break

    # 1px feather on remaining bg pixels that touch the body.
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            i = y * w + x
            if alpha[i]:
                continue
            if alpha[i - 1] or alpha[i + 1] or alpha[i - w] or alpha[i + w]:
                r, g, b, a = px[x, y]
                # Don't re-solidify paper leftovers.
                if is_paper_px(r, g, b):
                    continue
                alpha[i] = min(180, max(r, g, b))

    out = Image.new("RGBA", (w, h))
    opx = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            opx[x, y] = (r, g, b, alpha[y * w + x])

    return _fill_white_cracks(out)


def _fill_white_cracks(im):
    w, h = im.size
    px = im.load()
    src = im.copy()
    sp = src.load()

    def paper(r, g, b, a):
        if a < 80:
            return False
        luma = 0.299 * r + 0.587 * g + 0.114 * b
        return luma > 222 and min(r, g, b) > 165

    for y in range(1, h - 1):
        for x in range(1, w - 1):
            r, g, b, a = sp[x, y]
            if not paper(r, g, b, a):
                continue
            white_n = col_n = 0
            cr = cg = cb = 0
            for ny in (y - 1, y, y + 1):
                for nx in (x - 1, x, x + 1):
                    if nx == x and ny == y:
                        continue
                    rr, gg, bb, aa = sp[nx, ny]
                    if aa < 80:
                        continue
                    if paper(rr, gg, bb, aa):
                        white_n += 1
                    else:
                        col_n += 1
                        cr += rr
                        cg += gg
                        cb += bb
            # Thin crack: few white neighbours, some real colour around it.
            if white_n <= 3 and col_n >= 2:
                px[x, y] = (cr // col_n, cg // col_n, cb // col_n, a)
    return im


def median_body_width(im):
    """Typical torso/hip width — used to normalise generated vs original HD."""
    box = im.getbbox()
    if not box:
        return 1
    l, t, r, b = box
    y0 = t + int((b - t) * 0.50)
    y1 = t + int((b - t) * 0.82)
    px = im.load()
    widths = []
    for y in range(y0, max(y0 + 1, y1), 2):
        xs = [x for x in range(l, r) if px[x, y][3] > 80]
        if xs:
            widths.append(max(xs) - min(xs))
    if not widths:
        return max(1, r - l)
    widths.sort()
    return max(1, widths[len(widths) // 2])


def bbox_alpha(im, pad=0):
    box = im.getbbox()
    if not box:
        return None
    l, t, r, b = box
    return (max(0, l - pad), max(0, t - pad),
            min(im.size[0], r + pad), min(im.size[1], b + pad))


def foot_anchor(im):
    """Return (ax, ay) = centroid of opaque pixels in the bottom 14% of the bbox.

    Using the feet (not the full bbox) keeps the body planted when the club
    swings from overhead to the right.
    """
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


def place_on_canvas(im, canvas_w, canvas_h, foot_x, foot_y):
    ax, ay = foot_anchor(im)
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    canvas.alpha_composite(im, (int(foot_x - ax), int(foot_y - ay)))
    return canvas


# ---------------------------------------------------------------------------
# Swing / walk bake
# ---------------------------------------------------------------------------
SWING_SOURCES = [
    ("idle.png",               os.path.join(HEROES, "thorne_idle.png")),
    ("attack.png",             os.path.join(HEROES, "thorne_attack.png")),
    ("swing_1_raw (peak)",     os.path.join(RAW, "thorne_swing_1_raw.png")),
    ("swing_5_raw (down)",     os.path.join(RAW, "thorne_swing_5_raw.png")),
    ("swing_4_raw (impact)",   os.path.join(RAW, "thorne_swing_4_raw.png")),
    ("swing_4_raw (hold)",     os.path.join(RAW, "thorne_swing_4_raw.png")),
    ("idle.png (recover)",     os.path.join(HEROES, "thorne_idle.png")),
    ("idle.png",               os.path.join(HEROES, "thorne_idle.png")),
]


def bake_aligned(sources, out_prefix, bake_h=BAKE_H):
    cleaned = []
    ref_width = None
    for label, path in sources:
        if not os.path.isfile(path):
            raise SystemExit("missing source %s (%s)" % (label, path))
        im = remove_background(Image.open(path))
        box = bbox_alpha(im, pad=2)
        if box:
            im = im.crop(box)
        bw = median_body_width(im)
        if ref_width is None:
            ref_width = float(bw)
        scale = max(0.72, min(1.28, ref_width / float(bw)))
        ow, oh = im.size
        if abs(scale - 1.0) > 0.04:
            nw = max(8, int(round(ow * scale)))
            nh = max(8, int(round(oh * scale)))
            im = im.resize((nw, nh), Image.LANCZOS)
            print("  clean %-28s %dx%d  body_w=%d scale=%.2f -> %dx%d"
                  % (label, ow, oh, bw, scale, nw, nh))
        else:
            print("  clean %-28s %dx%d  body_w=%d" % (label, ow, oh, bw))
        cleaned.append((label, im))

    # Shared canvas large enough for every pose, feet planted on one point.
    max_w = max(im.size[0] for _, im in cleaned)
    max_h = max(im.size[1] for _, im in cleaned)
    cw = max_w + 80
    ch = max_h + 60
    fx, fy = cw // 2, ch - 18

    placed = [place_on_canvas(im, cw, ch, fx, fy) for _, im in cleaned]

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
    crop_h = union[3] - union[1]
    scale = bake_h / float(crop_h)
    out_w = max(8, int(round((union[2] - union[0]) * scale)))
    out_h = max(8, int(round(crop_h * scale)))

    frames = []
    for i, im in enumerate(placed):
        cropped = im.crop(union)
        baked = cropped.resize((out_w, out_h), Image.LANCZOS)
        dest = os.path.join(HEROES, "%s_%d.png" % (out_prefix, i))
        baked.save(dest, "PNG")
        frames.append(baked)
        print("  write %s  %dx%d" % (dest, out_w, out_h))
    return frames


def bake_walk():
    """2-frame stride used by the renderer ping-pong (walk <-> idle)."""
    sources = [
        ("walk.png", os.path.join(HEROES, "thorne_walk.png")),
        ("idle.png", os.path.join(HEROES, "thorne_idle.png")),
    ]
    return bake_aligned(sources, "thorne_walk", bake_h=BAKE_H)


# ---------------------------------------------------------------------------
# HD skill FX (painted, not 8px dots)
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
            t = t * t  # keep the core brighter
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


def _draw_quill(draw, cx, cy, length, angle, thickness, dark, mid, light, tip):
    ca, sa = math.cos(angle), math.sin(angle)
    px, py = -sa, ca
    tip_x = cx + ca * length
    tip_y = cy + sa * length
    base_l = (cx + px * thickness, cy + py * thickness)
    base_r = (cx - px * thickness, cy - py * thickness)
    mid_l = (cx + ca * length * 0.55 + px * thickness * 0.55,
             cy + sa * length * 0.55 + py * thickness * 0.55)
    mid_r = (cx + ca * length * 0.55 - px * thickness * 0.55,
             cy + sa * length * 0.55 - py * thickness * 0.55)
    draw.polygon([base_l, mid_l, (tip_x, tip_y), mid_r, base_r], fill=dark)
    draw.polygon([
        (cx + px * thickness * 0.45, cy + py * thickness * 0.45),
        mid_l,
        (tip_x, tip_y),
        (cx + ca * length * 0.55, cy + sa * length * 0.55),
    ], fill=mid)
    draw.line([(cx, cy), (tip_x, tip_y)], fill=light, width=max(1, thickness // 3))
    r = max(2, thickness // 2)
    draw.ellipse((tip_x - r, tip_y - r, tip_x + r, tip_y + r), fill=tip)


def bake_skill_q():
    """Viscous Nose — glossy green goo glob."""
    s = SKILL_SIZE
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    cx = cy = s // 2
    _gradient_circle(img, cx, cy + 8, 210, (40, 140, 55, 40), (10, 40, 15, 0))
    _gradient_circle(img, cx, cy + 4, 150, (50, 190, 70, 210), (20, 80, 30, 0))
    _gradient_circle(img, cx - 8, cy - 6, 95, (120, 235, 90, 240), (40, 140, 50, 40))
    _gradient_circle(img, cx - 22, cy - 28, 36, (230, 255, 200, 230), (140, 230, 110, 0))
    d = ImageDraw.Draw(img)
    # Drips
    for i, (dx, dy, rad) in enumerate(((18, 110, 22), (-8, 130, 16), (40, 100, 12))):
        _gradient_circle(img, cx + dx, cy + dy, rad,
                         (90, 210, 80, 230), (30, 90, 40, 0))
    d.ellipse((cx - 14, cy - 18, cx + 4, cy), fill=(245, 255, 220, 180))
    return img


def bake_skill_w():
    """Bristleback — radial golden quill burst + aura rings."""
    s = SKILL_SIZE
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    cx = cy = s // 2
    _gradient_circle(img, cx, cy, 240, (255, 200, 60, 50), (120, 70, 10, 0))
    _gradient_circle(img, cx, cy, 150, (255, 220, 90, 90), (180, 120, 20, 0))
    d = ImageDraw.Draw(img)
    for ring, col, wth in ((190, (255, 210, 80, 160), 6),
                           (140, (255, 230, 140, 200), 4),
                           (95, (255, 245, 190, 180), 3)):
        d.ellipse((cx - ring, cy - ring, cx + ring, cy + ring),
                  outline=col, width=wth)
    n = 18
    for i in range(n):
        a = -math.pi / 2 + i * (2 * math.pi / n)
        length = 175 + (8 if i % 2 == 0 else -10)
        bx = cx + math.cos(a) * 55
        by = cy + math.sin(a) * 55
        _draw_quill(d, bx, by, length, a, 9,
                    (140, 85, 20, 255), (210, 155, 40, 255),
                    (245, 205, 75, 255), (255, 240, 160, 255))
    _gradient_circle(img, cx, cy, 48, (255, 250, 210, 200), (255, 200, 80, 0))
    return img


def bake_skill_e():
    """Quill Spray — ring of flying quills with motion streaks."""
    s = SKILL_SIZE
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    cx = cy = s // 2
    _gradient_circle(img, cx, cy, 200, (255, 200, 70, 35), (80, 40, 5, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((cx - 120, cy - 120, cx + 120, cy + 120),
              outline=(255, 210, 80, 200), width=5)
    d.ellipse((cx - 88, cy - 88, cx + 88, cy + 88),
              outline=(255, 230, 140, 140), width=3)
    n = 14
    for i in range(n):
        a = i * (2 * math.pi / n) + 0.2
        # streak
        x0 = cx + math.cos(a) * 70
        y0 = cy + math.sin(a) * 70
        x1 = cx + math.cos(a) * 200
        y1 = cy + math.sin(a) * 200
        d.line([(x0, y0), (x1, y1)], fill=(255, 220, 110, 140), width=3)
        _draw_quill(d, x0, y0, 130, a, 8,
                    (140, 85, 20, 255), (210, 155, 40, 255),
                    (245, 205, 75, 255), (255, 245, 190, 255))
    return img


def bake_skill_r():
    """Warpath — red-orange rage shockwave."""
    s = SKILL_SIZE
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    cx = cy = s // 2
    _gradient_circle(img, cx, cy, 250, (180, 30, 10, 70), (40, 0, 0, 0))
    _gradient_circle(img, cx, cy, 160, (255, 70, 20, 140), (120, 20, 5, 0))
    _gradient_circle(img, cx, cy, 70, (255, 200, 80, 230), (255, 80, 20, 40))
    d = ImageDraw.Draw(img)
    for ring, col, wth in ((220, (255, 90, 30, 170), 8),
                           (170, (255, 140, 50, 190), 6),
                           (120, (255, 190, 80, 200), 5),
                           (78, (255, 230, 140, 220), 4)):
        d.ellipse((cx - ring, cy - ring, cx + ring, cy + ring),
                  outline=col, width=wth)
    # embers
    for i in range(16):
        a = i * (2 * math.pi / 16) + 0.4
        r = 95 + (i % 3) * 28
        x = int(cx + math.cos(a) * r)
        y = int(cy + math.sin(a) * r)
        rad = 7 + (i % 3) * 2
        _gradient_circle(img, x, y, rad,
                         (255, 240, 160, 240), (255, 80, 20, 0))
    return img


def bake_skills():
    makers = {"q": bake_skill_q, "w": bake_skill_w,
              "e": bake_skill_e, "r": bake_skill_r}
    out = {}
    for key, fn in makers.items():
        im = fn()
        dest = os.path.join(HEROES, "thorne_skill_%s.png" % key)
        im.save(dest, "PNG")
        out[key] = im
        print("  write %s  %dx%d" % (dest, im.size[0], im.size[1]))
    return out


# ---------------------------------------------------------------------------
# Preview strips
# ---------------------------------------------------------------------------
def checker(w, h):
    im = Image.new("RGB", (w, h), (18, 16, 28))
    px = im.load()
    for y in range(h):
        for x in range(w):
            if ((x // 16) + (y // 16)) & 1:
                px[x, y] = (28, 24, 40)
    return im


def contact_sheet(frames, labels, cell_w, cell_h, title, path):
    n = len(frames)
    pad = 16
    header = 48
    W = pad + n * (cell_w + pad)
    H = header + cell_h + pad + 28
    sheet = Image.new("RGB", (W, H), (12, 10, 22))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 12), title, fill=(255, 196, 64))
    for i, (fr, lab) in enumerate(zip(frames, labels)):
        x = pad + i * (cell_w + pad)
        y = header
        bg = checker(cell_w, cell_h)
        # fit frame into cell, feet at bottom
        fw, fh = fr.size
        scale = min(cell_w / float(fw), cell_h / float(fh))
        nw, nh = max(1, int(fw * scale)), max(1, int(fh * scale))
        rs = fr.resize((nw, nh), Image.LANCZOS)
        bg.paste(rs, ((cell_w - nw) // 2, cell_h - nh), rs)
        sheet.paste(bg, (x, y))
        d.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), outline=(210, 150, 40))
        d.text((x + 6, y + cell_h + 6), lab, fill=(220, 220, 240))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sheet.save(path, "PNG")
    print("  preview", path)


def main():
    print("== swing frames ==")
    swing = bake_aligned(SWING_SOURCES, "thorne_swing", bake_h=BAKE_H)
    print("== walk frames ==")
    walk = bake_walk()
    print("== skill FX ==")
    skills = bake_skills()

    contact_sheet(
        swing,
        ["0 hip", "1 raise", "2 peak", "3 down",
         "4 impact", "5 hold", "6 recover", "7 rest"],
        140, 160,
        "THORNE  —  HD CLUB SWING  (club moves)",
        os.path.join(DOCS, "thorne_swing_strip.png"),
    )
    contact_sheet(
        walk,
        ["0 stride", "1 plant"],
        160, 180,
        "THORNE  —  WALK CYCLE",
        os.path.join(DOCS, "thorne_walk_strip.png"),
    )
    skill_frames = [skills[k] for k in "qwer"]
    contact_sheet(
        skill_frames,
        ["Q goo", "W bristle", "E spray", "R warpath"],
        180, 180,
        "THORNE  —  HD SKILL FX",
        os.path.join(DOCS, "thorne_skills_hd.png"),
    )
    print("done.")


if __name__ == "__main__":
    main()
