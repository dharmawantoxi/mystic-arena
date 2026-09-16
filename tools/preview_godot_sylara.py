#!/usr/bin/env python3
"""Pixel-art fantasy elven heroine preview renderer matching Kaizen & sprite benchmark."""
import math
import struct
import zlib


class Canvas:
    def __init__(self, w, h, bg=(10, 15, 12, 255)):
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
        steps = int(dist * 2.5) + 1
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
                    self.set_pixel(x, y, cr, cg, cb, ca)

    def draw_polygon(self, pts, color):
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

    def draw_capsule(self, p0, p1, w, color, outline=True, outline_col=(18, 26, 20, 255)):
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
            self.draw_polygon(opts, outline_col)
        self.draw_polygon(pts, color)

    def draw_taper(self, p0, w0, p1, w1, color, outline=True, outline_col=(18, 26, 20, 255)):
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
            self.draw_polygon(opts, outline_col)
        self.draw_polygon(pts, color)

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


INK = hex_to_rgba("121a14")
SKIN = hex_to_rgba("fae4d4")
SKIN_SHADOW = hex_to_rgba("d69e82")
SKIN_LIGHT = hex_to_rgba("fff5ec")
HAIR = hex_to_rgba("7e3518")
HAIR_DARK = hex_to_rgba("461c0a")
HAIR_LIGHT = hex_to_rgba("b65e28")
HOOD = hex_to_rgba("224c28")
HOOD_DARK = hex_to_rgba("122e18")
HOOD_LIGHT = hex_to_rgba("387842")
CAPE = hex_to_rgba("1e421e")
CAPE_DARK = hex_to_rgba("102410")
CAPE_LIGHT = hex_to_rgba("2e602c")
LEATHER = hex_to_rgba("704626")
LEATHER_DARK = hex_to_rgba("442612")
LEATHER_LIGHT = hex_to_rgba("9a6438")
TUNIC = hex_to_rgba("2c5a32")
PANTS = hex_to_rgba("16381c")
GOLD = hex_to_rgba("dba232")
GOLD_LIGHT = hex_to_rgba("fcd25a")
GOLD_DARK = hex_to_rgba("7c5614")
WOOD = hex_to_rgba("7c5228")
WOOD_DARK = hex_to_rgba("482c14")
WOOD_LIGHT = hex_to_rgba("a4723e")
STRING = hex_to_rgba("90ffcc")
STRING_GLOW = hex_to_rgba("40e890", 140)
FEATHER = hex_to_rgba("5ce078")
WIND = hex_to_rgba("4eed98", 200)
WIND_BRIGHT = hex_to_rgba("c6ffea", 230)
SHADOW = (6, 12, 8, 85)


def draw_sylara_heroine(cv, ox, oy, scale=4.0, bow_draw=0.0):
    def S(x, y):
        return (round(ox + x * scale), round(oy + y * scale))

    # 0. Ground Shadow & Magic Ring
    cv.draw_capsule(S(-8, 0), S(8, 0), 6 * scale, SHADOW, outline=False)

    # 1. Flowing Cape Behind Body
    cape_pts = [
        S(-3, -34), S(-1, -34),
        S(-4, -14), S(-9, -14),
        S(-7, -26),
    ]
    cv.draw_polygon(cape_pts, CAPE)
    cv.draw_line(S(-3, -34)[0], S(-3, -34)[1], S(-9, -14)[0], S(-9, -14)[1], CAPE_DARK, 1.2 * scale)
    cv.draw_line(S(-9, -14)[0], S(-9, -14)[1], S(-4, -14)[0], S(-4, -14)[1], GOLD_DARK, 1.0 * scale)

    # 2. Back Hair Braid
    hair_back = [
        S(-3, -38), S(-2, -38),
        S(-4, -28), S(-6, -28),
    ]
    cv.draw_polygon(hair_back, HAIR)
    cv.draw_line(S(-3, -38)[0], S(-3, -38)[1], S(-5, -28)[0], S(-5, -28)[1], HAIR_DARK, 1.0 * scale)

    # 3. Quiver with Arrows
    q_poly = [
        S(-5, -42), S(-3, -42),
        S(-5, -30), S(-7, -30),
    ]
    cv.draw_polygon(q_poly, LEATHER_DARK)
    cv.draw_line(S(-5, -42)[0], S(-5, -42)[1], S(-3, -42)[0], S(-3, -42)[1], GOLD_DARK, 1.0 * scale)
    for i in range(4):
        ax = -6.5 + i * 1.1
        ay = -42.0
        cv.draw_line(S(ax, ay)[0], S(ax, ay)[1], S(ax - 0.5, ay - 4.5)[0], S(ax - 0.5, ay - 4.5)[1], WOOD_LIGHT, 0.8 * scale)
        cv.draw_line(S(ax - 0.5, ay - 4.5)[0], S(ax - 0.5, ay - 4.5)[1], S(ax - 0.8, ay - 3.5)[0], S(ax - 0.8, ay - 3.5)[1], FEATHER, 1.2 * scale)
        cv.draw_line(S(ax - 0.5, ay - 4.5)[0], S(ax - 0.5, ay - 4.5)[1], S(ax - 0.2, ay - 3.5)[0], S(ax - 0.2, ay - 3.5)[1], FEATHER, 1.2 * scale)

    # 4. Legs & Boots (Slender elven legs, folded boots)
    # Back leg
    cv.draw_taper(S(-1.5, -20), 3.4 * scale, S(-2.0, -10), 2.8 * scale, PANTS)
    cv.draw_taper(S(-2.0, -10), 3.2 * scale, S(-2.5, -1), 2.6 * scale, LEATHER_DARK)
    cv.draw_capsule(S(-3.5, -1), S(0.0, -1), 2.8 * scale, LEATHER_DARK)
    # Front leg
    cv.draw_taper(S(2.0, -20), 3.4 * scale, S(2.5, -10), 2.8 * scale, PANTS)
    cv.draw_taper(S(2.5, -10), 3.4 * scale, S(2.8, -1), 2.8 * scale, LEATHER)
    # Boot cuff & strap
    cv.draw_capsule(S(0.8, -10), S(4.2, -10), 2.2 * scale, LEATHER_LIGHT)
    cv.draw_line(S(1.0, -9.5)[0], S(1.0, -9.5)[1], S(4.0, -9.5)[0], S(4.0, -9.5)[1], GOLD, 0.8 * scale)
    cv.draw_capsule(S(1.0, -1), S(5.2, -1), 3.0 * scale, LEATHER)

    # 5. Forest Tunic (Peeking out under corset)
    tunic_poly = [
        S(-3.5, -25), S(3.5, -25),
        S(4.5, -17), S(1.5, -15),
        S(0.0, -17), S(-1.5, -15),
        S(-4.5, -17),
    ]
    cv.draw_polygon(tunic_poly, TUNIC)
    cv.draw_line(S(-4.5, -17)[0], S(-4.5, -17)[1], S(-1.5, -15)[0], S(-1.5, -15)[1], GOLD, 0.9 * scale)
    cv.draw_line(S(-1.5, -15)[0], S(-1.5, -15)[1], S(0.0, -17)[0], S(0.0, -17)[1], GOLD, 0.9 * scale)
    cv.draw_line(S(0.0, -17)[0], S(0.0, -17)[1], S(1.5, -15)[0], S(1.5, -15)[1], GOLD, 0.9 * scale)
    cv.draw_line(S(1.5, -15)[0], S(1.5, -15)[1], S(4.5, -17)[0], S(4.5, -17)[1], GOLD, 0.9 * scale)

    # 6. Leather Archer's Corset & Belt
    cv.draw_capsule(S(-3.5, -22), S(3.5, -22), 2.6 * scale, LEATHER_DARK)
    cv.draw_capsule(S(-0.6, -22), S(1.2, -22), 1.8 * scale, GOLD)

    corset_poly = [
        S(-3.2, -34), S(3.2, -34),
        S(3.5, -23), S(-3.5, -23),
    ]
    cv.draw_polygon(corset_poly, LEATHER)
    cv.draw_line(S(-3.2, -34)[0], S(-3.2, -34)[1], S(-3.5, -23)[0], S(-3.5, -23)[1], LEATHER_DARK, 1.0 * scale)
    cv.draw_line(S(3.2, -34)[0], S(3.2, -34)[1], S(3.5, -23)[0], S(3.5, -23)[1], LEATHER_LIGHT, 1.0 * scale)
    cv.draw_line(S(-2.5, -33)[0], S(-2.5, -33)[1], S(2.5, -25)[0], S(2.5, -25)[1], LEATHER_DARK, 1.2 * scale)
    cv.draw_line(S(2.5, -33)[0], S(2.5, -33)[1], S(-2.5, -25)[0], S(-2.5, -25)[1], LEATHER_DARK, 1.2 * scale)
    cv.draw_line(S(-0.8, -29)[0], S(-0.8, -29)[1], S(0.8, -29)[0], S(0.8, -29)[1], GOLD_LIGHT, 1.0 * scale)

    # 7. Mantle / Shoulder Cowl with Gold Trim
    mantle_poly = [
        S(-4.5, -36), S(4.5, -36),
        S(4.8, -32), S(2.5, -31),
        S(-2.5, -31), S(-4.8, -32),
    ]
    cv.draw_polygon(mantle_poly, HOOD)
    cv.draw_line(S(-4.8, -32)[0], S(-4.8, -32)[1], S(-2.5, -31)[0], S(-2.5, -31)[1], GOLD, 1.0 * scale)
    cv.draw_line(S(-2.5, -31)[0], S(-2.5, -31)[1], S(2.5, -31)[0], S(2.5, -31)[1], GOLD, 1.0 * scale)
    cv.draw_line(S(2.5, -31)[0], S(2.5, -31)[1], S(4.8, -32)[0], S(4.8, -32)[1], GOLD, 1.0 * scale)
    cv.draw_circle(S(0.0, -32.5)[0], S(0.0, -32.5)[1], 1.2 * scale, GOLD_LIGHT)
    cv.draw_circle(S(0.0, -32.5)[0], S(0.0, -32.5)[1], 0.7 * scale, WIND_BRIGHT)

    # 8. Hood & Head (Sculpted elven cowl framing the face)
    hood_dome = [
        S(-4.5, -37), S(-5.0, -45),
        S(-2.5, -49), S(2.0, -48.5),
        S(3.8, -44), S(2.0, -41),
        S(-2.0, -38),
    ]
    cv.draw_polygon(hood_dome, HOOD)
    cv.draw_line(S(-5.0, -45)[0], S(-5.0, -45)[1], S(-2.5, -49)[0], S(-2.5, -49)[1], HOOD_LIGHT, 1.2 * scale)
    cv.draw_line(S(-2.5, -49)[0], S(-2.5, -49)[1], S(2.0, -48.5)[0], S(2.0, -48.5)[1], HOOD_LIGHT, 1.2 * scale)

    cowl_in = [
        S(-2.5, -46), S(1.5, -45),
        S(2.2, -41), S(-0.5, -39),
        S(-2.5, -41),
    ]
    cv.draw_polygon(cowl_in, HOOD_DARK)

    # Delicate Elven Face (3/4 Profile)
    face_poly = [
        S(-0.5, -45.5), S(1.8, -44.5),
        S(3.2, -42.5),
        S(3.5, -40.0),
        S(2.5, -37.8),
        S(1.2, -36.5),
        S(-0.5, -38.0),
    ]
    cv.draw_polygon(face_poly, SKIN)
    cv.draw_line(S(-0.5, -38.0)[0], S(-0.5, -38.0)[1], S(2.0, -37.8)[0], S(2.0, -37.8)[1], SKIN_SHADOW, 0.8 * scale)

    # Pointed Elven Ear
    ear_poly = [
        S(-0.5, -41.5),
        S(-3.5, -43.2),
        S(-0.8, -39.5),
    ]
    cv.draw_polygon(ear_poly, SKIN)
    cv.draw_line(S(-0.5, -41.5)[0], S(-0.5, -41.5)[1], S(-3.5, -43.2)[0], S(-3.5, -43.2)[1], SKIN_LIGHT, 0.7 * scale)
    cv.draw_circle(S(-2.8, -42.5)[0], S(-2.8, -42.5)[1], 0.6 * scale, GOLD_LIGHT)

    # Focused Archer's Eye
    cv.draw_capsule(S(1.4, -42.0), S(2.8, -41.8), 1.0 * scale, INK, outline=False)
    cv.draw_capsule(S(1.8, -41.8), S(2.5, -41.7), 0.7 * scale, (60, 190, 80, 255), outline=False)
    cv.draw_capsule(S(2.2, -41.8), S(2.4, -41.8), 0.4 * scale, (255, 255, 255, 255), outline=False)

    # Lips & Nose
    cv.draw_line(S(1.4, -38.0)[0], S(1.4, -38.0)[1], S(2.4, -38.0)[0], S(2.4, -38.0)[1], (190, 100, 90, 255), 0.8 * scale)
    cv.draw_line(S(3.2, -41.0)[0], S(3.2, -41.0)[1], S(3.4, -39.8)[0], S(3.4, -39.8)[1], SKIN_LIGHT, 0.7 * scale)

    # Auburn Hair Framing Cheek & Forehead
    cv.draw_line(S(-0.5, -45.5)[0], S(-0.5, -45.5)[1], S(1.2, -43.5)[0], S(1.2, -43.5)[1], HAIR, 1.2 * scale)
    cv.draw_line(S(-0.5, -41.5)[0], S(-0.5, -41.5)[1], S(0.2, -37.0)[0], S(0.2, -37.0)[1], HAIR, 1.1 * scale)
    cv.draw_line(S(-0.2, -41.0)[0], S(-0.2, -41.0)[1], S(0.4, -37.2)[0], S(0.4, -37.2)[1], HAIR_LIGHT, 0.7 * scale)

    # Gold rim along face opening of hood
    cv.draw_line(S(-2.5, -49)[0], S(-2.5, -49)[1], S(2.0, -48.5)[0], S(2.0, -48.5)[1], GOLD_LIGHT, 1.0 * scale)
    cv.draw_line(S(2.0, -48.5)[0], S(2.0, -48.5)[1], S(3.8, -44)[0], S(3.8, -44)[1], GOLD_LIGHT, 1.0 * scale)

    # 9. Shoulder Pauldron & Bow Arm
    cv.draw_capsule(S(2.5, -34.5), S(4.5, -33.0), 3.0 * scale, HOOD)
    cv.draw_line(S(2.8, -35.5)[0], S(2.8, -35.5)[1], S(4.8, -34.0)[0], S(4.8, -34.0)[1], GOLD, 0.8 * scale)

    elb = S(5.5, -27.0)
    hand = S(7.5, -19.0)
    cv.draw_taper(S(3.5, -33.5), 3.2 * scale, elb, 2.6 * scale, HOOD_DARK)
    cv.draw_taper(elb, 2.6 * scale, hand, 2.2 * scale, LEATHER)
    cv.draw_capsule(hand, S(8.2, -18.5), 2.0 * scale, SKIN)

    # 10. Recurve Bow (Graceful authentic elven recurve)
    grip = hand
    tip_up = S(11.0, -38.0)
    ctrl_up = S(14.5, -29.0)
    tip_low = S(11.0, 0.0)
    ctrl_low = S(14.5, -9.0)

    # Upper limb
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

    # Lower limb
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

    # Tips & String
    cv.draw_capsule(tip_up, S(10.0, -39.0), 1.6 * scale, (240, 235, 220, 255))
    cv.draw_capsule(tip_low, S(10.0, 1.0), 1.6 * scale, (240, 235, 220, 255))

    if bow_draw > 0.05:
        nock = S(11.0 - bow_draw * 10.0, -19.0)
        cv.draw_line(tip_up[0], tip_up[1], nock[0], nock[1], STRING_GLOW, 2.4 * scale)
        cv.draw_line(nock[0], nock[1], tip_low[0], tip_low[1], STRING_GLOW, 2.4 * scale)
        cv.draw_line(tip_up[0], tip_up[1], nock[0], nock[1], STRING, 1.1 * scale)
        cv.draw_line(nock[0], nock[1], tip_low[0], tip_low[1], STRING, 1.1 * scale)

        arrow_tip = S(18.0, -19.0)
        cv.draw_line(nock[0], nock[1], arrow_tip[0], arrow_tip[1], WOOD_LIGHT, 1.3 * scale)
        cv.draw_circle(arrow_tip[0], arrow_tip[1], 1.6 * scale, (220, 240, 255, 255))
        cv.draw_circle(nock[0], nock[1], 2.2 * scale, WIND_BRIGHT)
    else:
        cv.draw_line(tip_up[0], tip_up[1], tip_low[0], tip_low[1], STRING_GLOW, 2.0 * scale)
        cv.draw_line(tip_up[0], tip_up[1], tip_low[0], tip_low[1], STRING, 1.1 * scale)


def main():
    W, H = 1040, 520
    cv = Canvas(W, H, (12, 17, 14, 255))

    # 1. Left: Arena In-Game Scale (~70px, scale=1.4)
    draw_sylara_heroine(cv, 110, 420, scale=1.4, bow_draw=0.0)

    # 2. Middle-Left: Full Body Idle / Showcase (scale=3.5)
    draw_sylara_heroine(cv, 340, 450, scale=3.5, bow_draw=0.0)

    # 3. Middle-Right: Full Body Attack / Powershot Draw (scale=3.5, bow_draw=0.85)
    draw_sylara_heroine(cv, 590, 450, scale=3.5, bow_draw=0.85)

    # 4. Right: High Fidelity Close-Up (scale=6.5)
    draw_sylara_heroine(cv, 860, 480, scale=6.5, bow_draw=0.0)

    out = "docs/sylara_godot_new_preview.png"
    cv.save_png(out)
    print("Saved to", out)


if __name__ == "__main__":
    main()
