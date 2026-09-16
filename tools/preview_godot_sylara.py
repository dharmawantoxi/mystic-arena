#!/usr/bin/env python3
"""Masterwork elven heroine preview with vertex gradient shading, smooth lighting, and magic."""
import math
import struct
import zlib


class Canvas:
    def __init__(self, w, h, bg=(8, 14, 11, 255)):
        self.w = w
        self.h = h
        self.data = bytearray(w * h * 4)
        for i in range(0, len(self.data), 4):
            self.data[i] = bg[0]
            self.data[i + 1] = bg[1]
            self.data[i + 2] = bg[2]
            self.data[i + 3] = bg[3]

    def set_pixel(self, x, y, r, g, b, a=255):
        if 0 <= x < self.w and 0 <= y < self.h:
            idx = (int(y) * self.w + int(x)) * 4
            src_a = a / 255.0
            dst_a = self.data[idx + 3] / 255.0
            out_a = src_a + dst_a * (1.0 - src_a)
            if out_a > 0.001:
                out_r = (r * src_a + self.data[idx] * dst_a * (1.0 - src_a)) / out_a
                out_g = (g * src_a + self.data[idx + 1] * dst_a * (1.0 - src_a)) / out_a
                out_b = (b * src_a + self.data[idx + 2] * dst_a * (1.0 - src_a)) / out_a
                self.data[idx] = int(min(255, max(0, out_r)))
                self.data[idx + 1] = int(min(255, max(0, out_g)))
                self.data[idx + 2] = int(min(255, max(0, out_b)))
                self.data[idx + 3] = int(min(255, max(0, out_a * 255)))

    def draw_line(self, x0, y0, x1, y1, color, width=1.0):
        cr, cg, cb, ca = color
        dx = x1 - x0
        dy = y1 - y0
        dist = math.hypot(dx, dy)
        if dist < 0.001:
            self.set_pixel(int(x0), int(y0), cr, cg, cb, ca)
            return
        steps = int(dist * 3.0) + 1
        half_w = width * 0.5
        for i in range(steps + 1):
            t = i / steps
            px = x0 + dx * t
            py = y0 + dy * t
            for ox in range(-int(half_w + 0.5), int(half_w + 0.9)):
                for oy in range(-int(half_w + 0.5), int(half_w + 0.9)):
                    if ox * ox + oy * oy <= half_w * half_w + 0.5:
                        self.set_pixel(int(px + ox), int(py + oy), cr, cg, cb, ca)

    def draw_circle(self, cx, cy, r, color):
        cr, cg, cb, ca = color
        x0 = max(0, int(cx - r - 1))
        x1 = min(self.w - 1, int(cx + r + 1))
        y0 = max(0, int(cy - r - 1))
        y1 = min(self.h - 1, int(cy + r + 1))
        r_sq = r * r
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                d_sq = (x - cx) ** 2 + (y - cy) ** 2
                if d_sq <= r_sq:
                    # Antialiased soft edge
                    edge = r - math.sqrt(d_sq)
                    alpha = min(1.0, max(0.0, edge + 0.5)) * (ca / 255.0)
                    self.set_pixel(x, y, cr, cg, cb, int(alpha * 255))

    def draw_polygon_flat(self, pts, color):
        if len(pts) < 3:
            return
        cr, cg, cb, ca = color
        min_y = max(0, int(min(p[1] for p in pts)))
        max_y = min(self.h - 1, int(max(p[1] for p in pts)))
        for y in range(min_y, max_y + 1):
            nodes = []
            j = len(pts) - 1
            for i in range(len(pts)):
                p1 = pts[i]
                p2 = pts[j]
                if (p1[1] < y and p2[1] >= y) or (p2[1] < y and p1[1] >= y):
                    x = p1[0] + (y - p1[1]) / (p2[1] - p1[1]) * (p2[0] - p1[0])
                    nodes.append(x)
                j = i
            nodes.sort()
            for k in range(0, len(nodes) - 1, 2):
                x_start = max(0, int(nodes[k]))
                x_end = min(self.w - 1, int(nodes[k + 1]))
                for x in range(x_start, x_end + 1):
                    self.set_pixel(x, y, cr, cg, cb, ca)

    def draw_polygon_gradient(self, pts, col_top, col_bot):
        if len(pts) < 3:
            return
        min_y = min(p[1] for p in pts)
        max_y = max(p[1] for p in pts)
        h = max(0.001, max_y - min_y)
        im_min_y = max(0, int(min_y))
        im_max_y = min(self.h - 1, int(max_y))
        for y in range(im_min_y, im_max_y + 1):
            t = (y - min_y) / h
            t = max(0.0, min(1.0, t))
            cr = int(col_top[0] + (col_bot[0] - col_top[0]) * t)
            cg = int(col_top[1] + (col_bot[1] - col_top[1]) * t)
            cb = int(col_top[2] + (col_bot[2] - col_top[2]) * t)
            ca = int(col_top[3] + (col_bot[3] - col_top[3]) * t)
            nodes = []
            j = len(pts) - 1
            for i in range(len(pts)):
                p1 = pts[i]
                p2 = pts[j]
                if (p1[1] < y and p2[1] >= y) or (p2[1] < y and p1[1] >= y):
                    x = p1[0] + (y - p1[1]) / (p2[1] - p1[1]) * (p2[0] - p1[0])
                    nodes.append(x)
                j = i
            nodes.sort()
            for k in range(0, len(nodes) - 1, 2):
                x_start = max(0, int(nodes[k]))
                x_end = min(self.w - 1, int(nodes[k + 1]))
                for x in range(x_start, x_end + 1):
                    self.set_pixel(x, y, cr, cg, cb, ca)

    def draw_capsule(self, p0, p1, w, color, outline=True, outline_col=(14, 22, 16, 255)):
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        ln = math.hypot(dx, dy)
        if ln < 0.001:
            dx, dy, ln = 1.0, 0.0, 1.0
        nx = -dy / ln
        ny = dx / ln
        hw = w * 0.5
        pts = [
            (p0[0] + nx * hw, p0[1] + ny * hw),
            (p1[0] + nx * hw, p1[1] + ny * hw),
            (p1[0] - nx * hw, p1[1] - ny * hw),
            (p0[0] - nx * hw, p0[1] - ny * hw),
        ]
        if outline:
            how = hw + 1.2
            opts = [
                (p0[0] + nx * how, p0[1] + ny * how),
                (p1[0] + nx * how, p1[1] + ny * how),
                (p1[0] - nx * how, p1[1] - ny * how),
                (p0[0] - nx * how, p0[1] - ny * how),
            ]
            self.draw_polygon_flat(opts, outline_col)
        self.draw_polygon_flat(pts, color)

    def draw_taper(self, p0, w0, p1, w1, col_top, col_bot, outline=True, outline_col=(14, 22, 16, 255)):
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        ln = math.hypot(dx, dy)
        if ln < 0.001:
            dx, dy, ln = 1.0, 0.0, 1.0
        nx = -dy / ln
        ny = dx / ln
        hw0 = w0 * 0.5
        hw1 = w1 * 0.5
        pts = [
            (p0[0] + nx * hw0, p0[1] + ny * hw0),
            (p1[0] + nx * hw1, p1[1] + ny * hw1),
            (p1[0] - nx * hw1, p1[1] - ny * hw1),
            (p0[0] - nx * hw0, p0[1] - ny * hw0),
        ]
        if outline:
            opts = [
                (p0[0] + nx * (hw0 + 1.2), p0[1] + ny * (hw0 + 1.2)),
                (p1[0] + nx * (hw1 + 1.2), p1[1] + ny * (hw1 + 1.2)),
                (p1[0] - nx * (hw1 + 1.2), p1[1] - ny * (hw1 + 1.2)),
                (p0[0] - nx * (hw0 + 1.2), p0[1] - ny * (hw0 + 1.2)),
            ]
            self.draw_polygon_flat(opts, outline_col)
        self.draw_polygon_gradient(pts, col_top, col_bot)

    def save_png(self, filename):
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)
            raw.extend(self.data[y * self.w * 4 : (y + 1) * self.w * 4])

        def chunk(tag, data):
            crc = zlib.crc32(tag + data) & 0xFFFFFFFF
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

        header = b"\x89PNG\r\n\x1a\n"
        ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 6, 0, 0, 0))
        idat = chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        iend = chunk(b"IEND", b"")
        with open(filename, "wb") as f:
            f.write(header + ihdr + idat + iend)


def hex_to_rgba(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


INK = hex_to_rgba("0c140e")
SKIN_TOP = hex_to_rgba("fff2e6")
SKIN = hex_to_rgba("f6dac4")
SKIN_SHADOW = hex_to_rgba("cc9274")
SKIN_BLUSH = (235, 120, 110, 110)
HAIR_LIGHT = hex_to_rgba("b86230")
HAIR = hex_to_rgba("823a1a")
HAIR_DARK = hex_to_rgba("4a1e0c")
HOOD_LIGHT = hex_to_rgba("428448")
HOOD = hex_to_rgba("2a5a30")
HOOD_DARK = hex_to_rgba("16341a")
CAPE_LIGHT = hex_to_rgba("3c7c42")
CAPE = hex_to_rgba("26542a")
CAPE_DARK = hex_to_rgba("122c16")
LEATHER_LIGHT = hex_to_rgba("9c6036")
LEATHER = hex_to_rgba("724222")
LEATHER_DARK = hex_to_rgba("462612")
TUNIC_LIGHT = hex_to_rgba("448848")
TUNIC = hex_to_rgba("2e6234")
TUNIC_DARK = hex_to_rgba("183a1c")
PANTS = hex_to_rgba("18321c")
GOLD_BRIGHT = hex_to_rgba("ffe078")
GOLD = hex_to_rgba("dba232")
GOLD_DARK = hex_to_rgba("7c5614")
WOOD = hex_to_rgba("7e522a")
WOOD_LIGHT = hex_to_rgba("ae7846")
STRING = hex_to_rgba("88ffcc")
STRING_GLOW = hex_to_rgba("42ea94", 160)
FEATHER = hex_to_rgba("54dc72")
WIND_BRIGHT = hex_to_rgba("c6ffea", 240)
WIND = hex_to_rgba("4eed98", 180)
WIND_HALO = hex_to_rgba("4eed98", 30)
SHADOW = (4, 10, 6, 95)


def draw_masterwork_sylara(cv, ox, oy, scale=4.0, is_attack=False, bow_draw=0.0):
    def S(x, y):
        return (round(ox + x * scale), round(oy + y * scale))

    # ── 0. AMBIENT WIND COMPASS & GROUND SHADOW ──
    c = S(0, 0)
    cv.draw_circle(c[0], c[1], 24 * scale, WIND_HALO)
    cv.draw_capsule(S(-9, 0), S(9, 0), 6 * scale, SHADOW, outline=False)

    # 3 wind magic arcs orbiting the ground
    for a_off in [0.0, 2.1, 4.2]:
        for st in range(12):
            ang = a_off + st * 0.08
            r = 18.0 * scale
            cv.draw_circle(c[0] + math.cos(ang) * r, c[1] + math.sin(ang) * (r * 0.42), 0.8 * scale, (WIND[0], WIND[1], WIND[2], int(150 * (st / 12.0))))

    # ── 1. FLOWING CAPE (Layered with Gradient Shading) ──
    if is_attack:
        cape_pts = [
            S(-4, -35), S(-2, -35),
            S(-10, -18), S(-16, -18),
            S(-12, -28),
        ]
        cv.draw_polygon_gradient(cape_pts, CAPE_LIGHT, CAPE_DARK)
        cv.draw_line(S(-4, -35)[0], S(-4, -35)[1], S(-16, -18)[0], S(-16, -18)[1], INK, 1.2 * scale)
        cv.draw_line(S(-16, -18)[0], S(-16, -18)[1], S(-10, -18)[0], S(-10, -18)[1], GOLD_BRIGHT, 1.2 * scale)
    else:
        cape_pts = [
            S(-3, -34), S(-1, -34),
            S(-4, -14), S(-9, -14),
            S(-7, -26),
        ]
        cv.draw_polygon_gradient(cape_pts, CAPE_LIGHT, CAPE_DARK)
        cv.draw_line(S(-3, -34)[0], S(-3, -34)[1], S(-9, -14)[0], S(-9, -14)[1], INK, 1.2 * scale)
        cv.draw_line(S(-9, -14)[0], S(-9, -14)[1], S(-4, -14)[0], S(-4, -14)[1], GOLD_BRIGHT, 1.2 * scale)

    # ── 2. AUBURN HAIR BRAID (Cascading with Sheen) ──
    hair_back = [
        S(-3, -38), S(-1.5, -38),
        S(-3.5, -28), S(-6, -28),
    ]
    cv.draw_polygon_gradient(hair_back, HAIR_LIGHT, HAIR_DARK)
    cv.draw_line(S(-2.5, -36)[0], S(-2.5, -36)[1], S(-4.5, -29)[0], S(-4.5, -29)[1], HAIR_LIGHT, 0.9 * scale)

    # ── 3. QUIVER & EMERALD FLETCHING ──
    q_poly = [
        S(-5, -42), S(-3, -42),
        S(-5, -30), S(-7, -30),
    ]
    cv.draw_polygon_gradient(q_poly, LEATHER, LEATHER_DARK)
    cv.draw_line(S(-5, -42)[0], S(-5, -42)[1], S(-3, -42)[0], S(-3, -42)[1], GOLD, 1.1 * scale)
    cv.draw_line(S(-6, -36)[0], S(-6, -36)[1], S(-4, -36)[0], S(-4, -36)[1], GOLD_BRIGHT, 1.0 * scale)
    for i in range(4):
        ax = -6.5 + i * 1.1
        ay = -42.0
        cv.draw_line(S(ax, ay)[0], S(ax, ay)[1], S(ax - 0.5, ay - 4.5)[0], S(ax - 0.5, ay - 4.5)[1], WOOD_LIGHT, 0.9 * scale)
        cv.draw_line(S(ax - 0.5, ay - 4.5)[0], S(ax - 0.5, ay - 4.5)[1], S(ax - 0.8, ay - 3.4)[0], S(ax - 0.8, ay - 3.4)[1], FEATHER, 1.2 * scale)
        cv.draw_line(S(ax - 0.5, ay - 4.5)[0], S(ax - 0.5, ay - 4.5)[1], S(ax - 0.2, ay - 3.4)[0], S(ax - 0.2, ay - 3.4)[1], FEATHER, 1.2 * scale)
        cv.draw_circle(S(ax - 0.5, ay - 4.5)[0], S(ax - 0.5, ay - 4.5)[1], 0.6 * scale, GOLD_BRIGHT)

    # ── 4. LEGS & BOOTS (Shaded elven limbs) ──
    if is_attack:
        cv.draw_taper(S(-2.0, -20), 3.4 * scale, S(-5.0, -10), 2.8 * scale, PANTS, INK)
        cv.draw_taper(S(-5.0, -10), 3.2 * scale, S(-6.5, -1), 2.6 * scale, LEATHER, LEATHER_DARK)
        cv.draw_capsule(S(-8.0, -1), S(-4.0, -1), 2.8 * scale, LEATHER_DARK)

        cv.draw_taper(S(2.0, -20), 3.4 * scale, S(5.0, -10), 2.8 * scale, PANTS, INK)
        cv.draw_taper(S(5.0, -10), 3.4 * scale, S(6.0, -1), 2.8 * scale, LEATHER_LIGHT, LEATHER)
        cv.draw_capsule(S(4.2, -10), S(7.2, -10), 2.2 * scale, LEATHER_LIGHT)
        cv.draw_line(S(4.2, -9.5)[0], S(4.2, -9.5)[1], S(7.2, -9.5)[0], S(7.2, -9.5)[1], GOLD_BRIGHT, 0.8 * scale)
        cv.draw_capsule(S(4.5, -1), S(8.5, -1), 3.0 * scale, LEATHER)
    else:
        cv.draw_taper(S(-1.5, -20), 3.4 * scale, S(-2.0, -10), 2.8 * scale, PANTS, INK)
        cv.draw_taper(S(-2.0, -10), 3.2 * scale, S(-2.5, -1), 2.6 * scale, LEATHER, LEATHER_DARK)
        cv.draw_capsule(S(-3.5, -1), S(0.0, -1), 2.8 * scale, LEATHER_DARK)

        cv.draw_taper(S(2.0, -20), 3.4 * scale, S(2.5, -10), 2.8 * scale, PANTS, INK)
        cv.draw_taper(S(2.5, -10), 3.4 * scale, S(2.8, -1), 2.8 * scale, LEATHER_LIGHT, LEATHER)
        cv.draw_capsule(S(0.8, -10), S(4.2, -10), 2.2 * scale, LEATHER_LIGHT)
        cv.draw_line(S(1.0, -9.5)[0], S(1.0, -9.5)[1], S(4.0, -9.5)[0], S(4.0, -9.5)[1], GOLD_BRIGHT, 0.8 * scale)
        cv.draw_capsule(S(1.0, -1), S(5.2, -1), 3.0 * scale, LEATHER)

    # ── 5. FOREST TUNIC WITH GOLD EMBROIDERY ──
    tunic_poly = [
        S(-3.5, -25), S(3.5, -25),
        S(4.5, -17), S(1.5, -15),
        S(0.0, -17), S(-1.5, -15),
        S(-4.5, -17),
    ]
    cv.draw_polygon_gradient(tunic_poly, TUNIC, TUNIC_DARK)
    cv.draw_line(S(-4.5, -17)[0], S(-4.5, -17)[1], S(-1.5, -15)[0], S(-1.5, -15)[1], GOLD_BRIGHT, 1.0 * scale)
    cv.draw_line(S(-1.5, -15)[0], S(-1.5, -15)[1], S(0.0, -17)[0], S(0.0, -17)[1], GOLD_BRIGHT, 1.0 * scale)
    cv.draw_line(S(0.0, -17)[0], S(0.0, -17)[1], S(1.5, -15)[0], S(1.5, -15)[1], GOLD_BRIGHT, 1.0 * scale)
    cv.draw_line(S(1.5, -15)[0], S(1.5, -15)[1], S(4.5, -17)[0], S(4.5, -17)[1], GOLD_BRIGHT, 1.0 * scale)

    # ── 6. ARCHER'S CORSET & WAIST BELT ──
    cv.draw_capsule(S(-3.5, -22), S(3.5, -22), 2.6 * scale, LEATHER_DARK)
    cv.draw_capsule(S(-0.6, -22), S(1.2, -22), 1.8 * scale, GOLD_BRIGHT)

    corset_poly = [
        S(-3.2, -34), S(3.2, -34),
        S(3.5, -23), S(-3.5, -23),
    ]
    cv.draw_polygon_gradient(corset_poly, LEATHER_LIGHT, LEATHER)
    cv.draw_line(S(-3.2, -34)[0], S(-3.2, -34)[1], S(-3.5, -23)[0], S(-3.5, -23)[1], INK, 1.0 * scale)
    cv.draw_line(S(3.2, -34)[0], S(3.2, -34)[1], S(3.5, -23)[0], S(3.5, -23)[1], INK, 1.0 * scale)

    # Gold cross-straps with metallic highlights
    cv.draw_line(S(-2.4, -33)[0], S(-2.4, -33)[1], S(2.4, -25)[0], S(2.4, -25)[1], LEATHER_DARK, 1.3 * scale)
    cv.draw_line(S(2.4, -33)[0], S(2.4, -33)[1], S(-2.4, -25)[0], S(-2.4, -25)[1], LEATHER_DARK, 1.3 * scale)
    cv.draw_line(S(-0.8, -29)[0], S(-0.8, -29)[1], S(0.8, -29)[0], S(0.8, -29)[1], GOLD_BRIGHT, 1.1 * scale)

    # ── 7. MANTLE & WIND BROOCH ──
    mantle_poly = [
        S(-4.5, -36), S(4.5, -36),
        S(4.8, -32), S(2.5, -31),
        S(-2.5, -31), S(-4.8, -32),
    ]
    cv.draw_polygon_gradient(mantle_poly, HOOD_LIGHT, HOOD)
    cv.draw_line(S(-4.8, -32)[0], S(-4.8, -32)[1], S(-2.5, -31)[0], S(-2.5, -31)[1], GOLD_BRIGHT, 1.1 * scale)
    cv.draw_line(S(-2.5, -31)[0], S(-2.5, -31)[1], S(2.5, -31)[0], S(2.5, -31)[1], GOLD_BRIGHT, 1.1 * scale)
    cv.draw_line(S(2.5, -31)[0], S(2.5, -31)[1], S(4.8, -32)[0], S(4.8, -32)[1], GOLD_BRIGHT, 1.1 * scale)
    # Luminous wind jewel brooch
    cv.draw_circle(S(0.0, -32.5)[0], S(0.0, -32.5)[1], 1.3 * scale, GOLD_BRIGHT)
    cv.draw_circle(S(0.0, -32.5)[0], S(0.0, -32.5)[1], 0.8 * scale, WIND_BRIGHT)

    # ── 8. HOOD & GORGEOUS ELVEN PROFILE ──
    hood_dome = [
        S(-4.8, -37), S(-5.2, -45),
        S(-2.8, -49), S(2.0, -48.5),
        S(3.8, -44), S(2.0, -41),
        S(-2.0, -38),
    ]
    cv.draw_polygon_gradient(hood_dome, HOOD_LIGHT, HOOD_DARK)
    cv.draw_line(S(-5.2, -45)[0], S(-5.2, -45)[1], S(-2.8, -49)[0], S(-2.8, -49)[1], HOOD_LIGHT, 1.2 * scale)
    cv.draw_line(S(-2.8, -49)[0], S(-2.8, -49)[1], S(2.0, -48.5)[0], S(2.0, -48.5)[1], HOOD_LIGHT, 1.2 * scale)

    # Depth cowl shadow inside
    cowl_in = [
        S(-2.6, -46.5), S(1.6, -45.5),
        S(2.4, -41.5), S(-0.4, -39.5),
        S(-2.6, -41.5),
    ]
    cv.draw_polygon_flat(cowl_in, HOOD_DARK)

    # Delicate Elven Face (Warm skin with subtle cheek blush)
    face_poly = [
        S(-0.5, -45.5), S(1.8, -44.5),
        S(3.2, -42.5),
        S(3.5, -40.0),
        S(2.5, -37.8),
        S(1.2, -36.5),
        S(-0.5, -38.0),
    ]
    cv.draw_polygon_gradient(face_poly, SKIN_TOP, SKIN)
    cv.draw_circle(S(2.4, -39.8)[0], S(2.4, -39.8)[1], 1.4 * scale, SKIN_BLUSH)
    cv.draw_line(S(-0.5, -38.0)[0], S(-0.5, -38.0)[1], S(2.0, -37.8)[0], S(2.0, -37.8)[1], SKIN_SHADOW, 0.8 * scale)

    # Slender Pointed Elven Ear with gold cuff
    ear_poly = [
        S(-0.5, -41.5),
        S(-3.8, -43.5),
        S(-0.8, -39.5),
    ]
    cv.draw_polygon_flat(ear_poly, SKIN)
    cv.draw_line(S(-0.5, -41.5)[0], S(-0.5, -41.5)[1], S(-3.8, -43.5)[0], S(-3.8, -43.5)[1], SKIN_TOP, 0.8 * scale)
    cv.draw_line(S(-3.8, -43.5)[0], S(-3.8, -43.5)[1], S(-0.8, -39.5)[0], S(-0.8, -39.5)[1], INK, 0.7 * scale)
    cv.draw_circle(S(-3.0, -42.8)[0], S(-3.0, -42.8)[1], 0.7 * scale, GOLD_BRIGHT)

    # Focused Archer's Emerald Eye
    eye_x = 2.2
    eye_y = -42.0
    cv.draw_capsule(S(eye_x - 0.8, eye_y), S(eye_x + 0.8, eye_y + 0.2), 1.1 * scale, INK, outline=False)
    cv.draw_circle(S(eye_x + 0.1, eye_y + 0.1)[0], S(eye_x + 0.1, eye_y + 0.1)[1], 0.8 * scale, (50, 195, 80, 255))
    cv.draw_circle(S(eye_x + 0.2, eye_y)[0], S(eye_x + 0.2, eye_y)[1], 0.45 * scale, INK)
    cv.draw_circle(S(eye_x + 0.35, eye_y - 0.3)[0], S(eye_x + 0.35, eye_y - 0.3)[1], 0.35 * scale, (255, 255, 255, 255))

    # Cute nose & lips
    cv.draw_line(S(1.4, -38.0)[0], S(1.4, -38.0)[1], S(2.3, -38.0)[0], S(2.3, -38.0)[1], (200, 100, 95, 255), 0.9 * scale)
    cv.draw_circle(S(3.4, -40.0)[0], S(3.4, -40.0)[1], 0.5 * scale, SKIN_TOP)

    # Auburn Hair Framing Cheek & Forehead
    cv.draw_line(S(-0.5, -45.5)[0], S(-0.5, -45.5)[1], S(1.2, -43.5)[0], S(1.2, -43.5)[1], HAIR, 1.3 * scale)
    cv.draw_line(S(-0.5, -41.5)[0], S(-0.5, -41.5)[1], S(0.2, -37.0)[0], S(0.2, -37.0)[1], HAIR, 1.2 * scale)
    cv.draw_line(S(-0.2, -41.0)[0], S(-0.2, -41.0)[1], S(0.4, -37.2)[0], S(0.4, -37.2)[1], HAIR_LIGHT, 0.8 * scale)

    # Gold rim along face opening of hood
    cv.draw_line(S(-2.8, -49)[0], S(-2.8, -49)[1], S(2.0, -48.5)[0], S(2.0, -48.5)[1], GOLD_BRIGHT, 1.1 * scale)
    cv.draw_line(S(2.0, -48.5)[0], S(2.0, -48.5)[1], S(3.8, -44)[0], S(3.8, -44)[1], GOLD_BRIGHT, 1.1 * scale)

    # ── 9. AUTHENTIC ARCHERY KINEMATICS & BOW ──
    if is_attack:
        # ── DRAW STANCE: Extended bow arm at chest height (Y=-38) ──
        grip = S(14.0, -38.0)
        bow_hand = grip

        # Left Bow Arm: straight forward from shoulder (3.5, -34) to grip (14, -38)
        elb_f = S(9.0, -36.5)
        cv.draw_taper(S(3.5, -34.0), 3.2 * scale, elb_f, 2.6 * scale, HOOD_DARK, HOOD)
        cv.draw_taper(elb_f, 2.6 * scale, bow_hand, 2.2 * scale, LEATHER, LEATHER_LIGHT)
        cv.draw_capsule(bow_hand, S(14.8, -37.5), 2.0 * scale, SKIN)

        # Right Drawing Arm: pulled to CHIN/CHEEK ANCHOR POINT! (2.5, -38.5)
        nock = S(2.5 + (1.0 - bow_draw) * 9.0, -38.5)
        elb_b = S(-4.0, -38.0)
        cv.draw_taper(S(-2.5, -34.5), 3.0 * scale, elb_b, 2.5 * scale, HOOD_DARK, HOOD)
        cv.draw_taper(elb_b, 2.5 * scale, nock, 2.2 * scale, SKIN_SHADOW, SKIN)
        cv.draw_circle(nock[0], nock[1], 1.6 * scale, SKIN)

        # Recurve Bow: vertical upright curvature
        tip_up = S(12.5, -62.0)
        ctrl_up = S(19.0, -50.0)
        tip_low = S(12.5, -14.0)
        ctrl_low = S(19.0, -26.0)

        # Recurve upper limb
        steps = 14
        p_prev = grip
        for i in range(1, steps + 1):
            t = i / steps
            pt = (
                (1 - t) ** 2 * grip[0] + 2 * (1 - t) * t * ctrl_up[0] + t ** 2 * tip_up[0],
                (1 - t) ** 2 * grip[1] + 2 * (1 - t) * t * ctrl_up[1] + t ** 2 * tip_up[1],
            )
            cv.draw_line(p_prev[0], p_prev[1], pt[0], pt[1], WOOD, 2.4 * scale)
            cv.draw_line(p_prev[0], p_prev[1], pt[0], pt[1], WOOD_LIGHT, 0.9 * scale)
            p_prev = pt

        # Recurve lower limb
        p_prev = grip
        for i in range(1, steps + 1):
            t = i / steps
            pt = (
                (1 - t) ** 2 * grip[0] + 2 * (1 - t) * t * ctrl_low[0] + t ** 2 * tip_low[0],
                (1 - t) ** 2 * grip[1] + 2 * (1 - t) * t * ctrl_low[1] + t ** 2 * tip_low[1],
            )
            cv.draw_line(p_prev[0], p_prev[1], pt[0], pt[1], WOOD, 2.4 * scale)
            cv.draw_line(p_prev[0], p_prev[1], pt[0], pt[1], WOOD_LIGHT, 0.9 * scale)
            p_prev = pt

        # Ivory Horn Tips
        cv.draw_capsule(tip_up, S(11.0, -63.5), 1.8 * scale, (245, 240, 225, 255))
        cv.draw_capsule(tip_low, S(11.0, -12.5), 1.8 * scale, (245, 240, 225, 255))

        # Luminous Mint Mana String pulled back to the CHIN ANCHOR!
        cv.draw_line(tip_up[0], tip_up[1], nock[0], nock[1], STRING_GLOW, 2.8 * scale)
        cv.draw_line(nock[0], nock[1], tip_low[0], tip_low[1], STRING_GLOW, 2.8 * scale)
        cv.draw_line(tip_up[0], tip_up[1], nock[0], nock[1], STRING, 1.2 * scale)
        cv.draw_line(nock[0], nock[1], tip_low[0], tip_low[1], STRING, 1.2 * scale)

        # Arrow held perfectly horizontal through bow grip
        arrow_head = S(25.0, -38.5)
        cv.draw_line(nock[0], nock[1], arrow_head[0], arrow_head[1], WOOD_LIGHT, 1.4 * scale)
        cv.draw_circle(arrow_head[0], arrow_head[1], 1.8 * scale, (220, 240, 255, 255))
        cv.draw_circle(arrow_head[0], arrow_head[1], 1.0 * scale, (255, 255, 255, 255))
        # Concentrated gale aura at nock
        cv.draw_circle(nock[0], nock[1], 2.4 * scale, WIND_BRIGHT)

    else:
        # ── IDLE STANCE: Relaxed bow at side ──
        elb = S(5.5, -27.0)
        hand = S(7.5, -20.0)
        cv.draw_taper(S(3.5, -33.5), 3.2 * scale, elb, 2.6 * scale, HOOD_DARK, HOOD)
        cv.draw_taper(elb, 2.6 * scale, hand, 2.2 * scale, LEATHER, LEATHER_LIGHT)
        cv.draw_capsule(hand, S(8.2, -19.5), 2.0 * scale, SKIN)

        grip = hand
        tip_up = S(11.0, -39.0)
        ctrl_up = S(14.5, -30.0)
        tip_low = S(11.0, -1.0)
        ctrl_low = S(14.5, -10.0)

        steps = 12
        p_prev = grip
        for i in range(1, steps + 1):
            t = i / steps
            pt = (
                (1 - t) ** 2 * grip[0] + 2 * (1 - t) * t * ctrl_up[0] + t ** 2 * tip_up[0],
                (1 - t) ** 2 * grip[1] + 2 * (1 - t) * t * ctrl_up[1] + t ** 2 * tip_up[1],
            )
            cv.draw_line(p_prev[0], p_prev[1], pt[0], pt[1], WOOD, 2.2 * scale)
            cv.draw_line(p_prev[0], p_prev[1], pt[0], pt[1], WOOD_LIGHT, 0.9 * scale)
            p_prev = pt

        p_prev = grip
        for i in range(1, steps + 1):
            t = i / steps
            pt = (
                (1 - t) ** 2 * grip[0] + 2 * (1 - t) * t * ctrl_low[0] + t ** 2 * tip_low[0],
                (1 - t) ** 2 * grip[1] + 2 * (1 - t) * t * ctrl_low[1] + t ** 2 * tip_low[1],
            )
            cv.draw_line(p_prev[0], p_prev[1], pt[0], pt[1], WOOD, 2.2 * scale)
            cv.draw_line(p_prev[0], p_prev[1], pt[0], pt[1], WOOD_LIGHT, 0.9 * scale)
            p_prev = pt

        cv.draw_capsule(tip_up, S(10.0, -40.0), 1.6 * scale, (245, 240, 225, 255))
        cv.draw_capsule(tip_low, S(10.0, 0.0), 1.6 * scale, (245, 240, 225, 255))
        cv.draw_line(tip_up[0], tip_up[1], tip_low[0], tip_low[1], STRING_GLOW, 2.0 * scale)
        cv.draw_line(tip_up[0], tip_up[1], tip_low[0], tip_low[1], STRING, 1.1 * scale)


def main():
    W, H = 1040, 520
    cv = Canvas(W, H, (10, 15, 12, 255))

    # 1. Arena In-Game Scale (~70px tall, scale=1.4)
    draw_masterwork_sylara(cv, 110, 420, scale=1.4, is_attack=False)

    # 2. Showcase Full Body Idle (scale=3.5)
    draw_masterwork_sylara(cv, 320, 450, scale=3.5, is_attack=False)

    # 3. Masterwork Archery Draw (scale=3.5, authentic chin anchor draw)
    draw_masterwork_sylara(cv, 570, 450, scale=3.5, is_attack=True, bow_draw=0.95)

    # 4. High-Fidelity Portrait (scale=6.5)
    draw_masterwork_sylara(cv, 840, 480, scale=6.5, is_attack=False)

    out = "docs/sylara_godot_new_preview.png"
    cv.save_png(out)
    print("Masterwork preview saved to", out)


if __name__ == "__main__":
    main()
