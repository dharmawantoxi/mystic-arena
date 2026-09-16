#!/usr/bin/env python3
"""Comprehensive preview renderer for Godot Sylara procedural rig showcase."""
import math
import struct
import zlib


class Canvas:
    def __init__(self, w, h, bg=(10, 16, 12, 255)):
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
                    edge = r - math.sqrt(d_sq)
                    alpha = min(1.0, max(0.0, edge + 0.5)) * (ca / 255.0)
                    self.set_pixel(x, y, cr, cg, cb, int(alpha * 255))

    def draw_line(self, x0, y0, x1, y1, color, width=1.0):
        cr, cg, cb, ca = color
        dx = x1 - x0
        dy = y1 - y0
        dist = math.hypot(dx, dy)
        if dist < 0.001:
            self.draw_circle(x0, y0, width * 0.5, color)
            return
        steps = int(dist * 3.5) + 1
        half_w = width * 0.5
        for i in range(steps + 1):
            t = i / steps
            px = x0 + dx * t
            py = y0 + dy * t
            self.draw_circle(px, py, half_w, color)

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

    def draw_bezier(self, p0, p1, p2, color, width=1.0, steps=20):
        prev = p0
        for i in range(1, steps + 1):
            t = i / steps
            curr = (
                (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0],
                (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1],
            )
            self.draw_line(prev[0], prev[1], curr[0], curr[1], color, width)
            prev = curr

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


INK = hex_to_rgba("0c1c10", 255)
INK_SOFT = (15, 30, 20, 130)
SKIN = hex_to_rgba("fae4d4")
SKIN_SHADOW = hex_to_rgba("d69e82")
SKIN_LIGHT = hex_to_rgba("fff5ec")
SKIN_BLUSH = hex_to_rgba("ee8478", 130)
LIP = hex_to_rgba("d66462")
LIP_SHINE = hex_to_rgba("ff9896")
HAIR = hex_to_rgba("7e3518")
HAIR_DARK = hex_to_rgba("461c0a")
HAIR_LIGHT = hex_to_rgba("b65e28")
HAIR_SHINE = hex_to_rgba("e28c50")
CLOTH = hex_to_rgba("2c5a32")
CLOTH_DARK = hex_to_rgba("16381c")
CLOTH_LIGHT = hex_to_rgba("4a8a52")
HOOD = hex_to_rgba("224c28")
HOOD_DARK = hex_to_rgba("122e18")
CAPE = hex_to_rgba("387a3e")
CAPE_DARK = hex_to_rgba("204e26")
CAPE_LIGHT = hex_to_rgba("58a85e")
CAPE_BRIGHT = hex_to_rgba("7ecc82")
WOOD = hex_to_rgba("7c5228")
WOOD_DARK = hex_to_rgba("482c14")
WOOD_LIGHT = hex_to_rgba("a4723e")
WOOD_SHINE = hex_to_rgba("cca05c")
HORN_TIP = hex_to_rgba("ede4d0")
STRING = hex_to_rgba("90ffcc")
STRING_GLOW = hex_to_rgba("40e890", 140)
GOLD = hex_to_rgba("dba232")
GOLD_LIGHT = hex_to_rgba("fcd25a")
GOLD_DARK = hex_to_rgba("7c5614")
LEATHER = hex_to_rgba("704626")
LEATHER_DARK = hex_to_rgba("442612")
LEATHER_LIGHT = hex_to_rgba("9a6438")
FEATHER = hex_to_rgba("5ce078")
WIND = hex_to_rgba("4eed98", 200)
WIND_LIGHT = hex_to_rgba("96ffcc", 180)
WIND_BRIGHT = hex_to_rgba("c6ffea", 230)
LEAF = hex_to_rgba("add834", 180)
LEAF_GOLD = hex_to_rgba("eaf24e", 200)
EYE = hex_to_rgba("38b846")
EYE_DARK = hex_to_rgba("165c22")
EYE_LIGHT = hex_to_rgba("78f060")
EYE_WHITE = hex_to_rgba("f6fbf8")
QUIVER = hex_to_rgba("583c22")
SHADOW_GROUND = (5, 12, 5, 80)


def draw_sylara(cv, ox, oy, scale=3.5, bow_draw=0.0):
    def S(x, y):
        return (ox + x * scale, oy + y * scale)

    # 0. Ground magic & shadow
    c = S(0, 0)
    cv.draw_circle(c[0], c[1], 22 * scale, (WIND[0], WIND[1], WIND[2], 25))
    cv.draw_circle(c[0], c[1], 14 * scale, SHADOW_GROUND)

    # 1. Flowing Cape
    cape_poly = [
        S(-2.5, -42.0),
        S(-7.5, -34.0),
        S(-13.5, -20.0),
        S(-10.0, -14.0),
        S(-5.0, -26.0),
        S(-1.5, -40.0),
    ]
    cv.draw_polygon(cape_poly, CAPE)
    cv.draw_bezier(S(-2.5, -42.0), S(-8.0, -32.0), S(-13.5, -20.0), CAPE_LIGHT, 1.2 * scale)
    cv.draw_line(S(-13.5, -20.0)[0], S(-13.5, -20.0)[1], S(-10.0, -14.0)[0], S(-10.0, -14.0)[1], GOLD_LIGHT, 1.0 * scale)

    # 2. Flowing Auburn Hair
    hair_back = [
        S(-3.0, -50.0),
        S(-6.0, -42.0),
        S(-6.5, -32.0),
        S(-4.0, -31.0),
        S(-2.8, -42.0),
        S(-1.5, -49.0),
    ]
    cv.draw_polygon(hair_back, HAIR)
    cv.draw_line(S(-3.0, -48.0)[0], S(-3.0, -48.0)[1], S(-5.5, -33.0)[0], S(-5.5, -33.0)[1], HAIR_SHINE, 1.0 * scale)

    # 3. Quiver & Fletching
    q_poly = [
        S(-4.0, -45.0),
        S(-1.5, -46.0),
        S(-3.0, -32.0),
        S(-5.5, -31.0),
    ]
    cv.draw_polygon(q_poly, QUIVER)
    cv.draw_line(S(-4.0, -45.0)[0], S(-4.0, -45.0)[1], S(-5.0, -52.0)[0], S(-5.0, -52.0)[1], (180, 160, 120, 255), 1.0 * scale)
    cv.draw_circle(S(-5.0, -52.0)[0], S(-5.0, -52.0)[1], 1.2 * scale, FEATHER)

    # 4. Athletic Elven Legs & Boots
    # Back leg
    cv.draw_line(S(-2.0, -26.0)[0], S(-2.0, -26.0)[1], S(-4.0, -13.0)[0], S(-4.0, -13.0)[1], CLOTH_DARK, 3.2 * scale)
    cv.draw_line(S(-4.0, -13.0)[0], S(-4.0, -13.0)[1], S(-3.5, -1.0)[0], S(-3.5, -1.0)[1], LEATHER_DARK, 3.4 * scale)
    cv.draw_circle(S(-2.0, 0.0)[0], S(-2.0, 0.0)[1], 2.0 * scale, LEATHER_DARK)
    # Front leg
    cv.draw_line(S(2.0, -26.0)[0], S(2.0, -26.0)[1], S(3.5, -13.0)[0], S(3.5, -13.0)[1], CLOTH, 3.4 * scale)
    cv.draw_line(S(3.5, -13.0)[0], S(3.5, -13.0)[1], S(2.8, -1.0)[0], S(2.8, -1.0)[1], LEATHER, 3.6 * scale)
    # Boot cuff & buckle
    cv.draw_line(S(1.2, -12.0)[0], S(1.2, -12.0)[1], S(5.5, -12.0)[0], S(5.5, -12.0)[1], LEATHER_LIGHT, 1.8 * scale)
    cv.draw_circle(S(4.0, -11.5)[0], S(4.0, -11.5)[1], 0.8 * scale, GOLD_LIGHT)
    cv.draw_circle(S(5.0, 0.0)[0], S(5.0, 0.0)[1], 2.2 * scale, LEATHER)

    # 5. Velvet Forest Tunic (split tails)
    tunic_poly = [
        S(-3.5, -34.0),
        S(3.5, -34.0),
        S(4.5, -23.0),
        S(2.0, -19.5),
        S(0.0, -22.5),
        S(-2.5, -19.5),
        S(-4.5, -23.0),
    ]
    cv.draw_polygon(tunic_poly, CLOTH)
    cv.draw_line(S(-2.5, -19.5)[0], S(-2.5, -19.5)[1], S(0.0, -22.5)[0], S(0.0, -22.5)[1], GOLD_LIGHT, 0.9 * scale)
    cv.draw_line(S(0.0, -22.5)[0], S(0.0, -22.5)[1], S(2.0, -19.5)[0], S(2.0, -19.5)[1], GOLD_LIGHT, 0.9 * scale)

    # 6. Corset & Belt
    cv.draw_line(S(-4.0, -27.0)[0], S(-4.0, -27.0)[1], S(4.0, -27.0)[0], S(4.0, -27.0)[1], LEATHER_DARK, 2.2 * scale)
    cv.draw_circle(S(0.0, -27.0)[0], S(0.0, -27.0)[1], 1.5 * scale, GOLD_LIGHT)

    corset_poly = [
        S(-3.5, -42.0),
        S(3.5, -42.0),
        S(3.0, -29.0),
        S(-3.0, -29.0),
    ]
    cv.draw_polygon(corset_poly, LEATHER)
    for y_off in [-40.0, -36.0]:
        cv.draw_line(S(-1.5, y_off)[0], S(-1.5, y_off)[1], S(1.5, y_off + 2.0)[0], S(1.5, y_off + 2.0)[1], GOLD_LIGHT, 0.9 * scale)
        cv.draw_line(S(-1.5, y_off + 2.0)[0], S(-1.5, y_off + 2.0)[1], S(1.5, y_off)[0], S(1.5, y_off)[1], GOLD_LIGHT, 0.9 * scale)

    # Neck
    cv.draw_line(S(0.5, -46.5)[0], S(0.5, -46.5)[1], S(1.0, -42.5)[0], S(1.0, -42.5)[1], SKIN, 2.6 * scale)

    # Wind Gem Brooch
    cv.draw_circle(S(1.0, -42.5)[0], S(1.0, -42.5)[1], 1.6 * scale, GOLD_LIGHT)
    cv.draw_circle(S(1.0, -42.5)[0], S(1.0, -42.5)[1], 1.0 * scale, WIND_BRIGHT)

    # 7. Rounded Hood Crown & Cowl
    cv.draw_circle(S(-1.0, -56.0)[0], S(-1.0, -56.0)[1], 6.5 * scale, HOOD)
    cv.draw_bezier(S(-6.0, -55.0), S(-1.0, -62.8), S(4.0, -57.5), GOLD_LIGHT, 1.2 * scale)

    cowl_open = [
        S(-2.0, -57.5),
        S(2.0, -57.0),
        S(3.2, -54.0),
        S(0.0, -47.0),
        S(-2.5, -50.0),
    ]
    cv.draw_polygon(cowl_open, HOOD_DARK)

    # 8. Delicate Feminine Elven Face
    face_poly = [
        S(-0.5, -56.5),
        S(2.4, -55.5),
        S(3.8, -53.2),
        S(4.2, -50.5),
        S(3.2, -47.8),
        S(1.6, -46.2),
        S(-0.2, -47.8),
        S(-1.0, -51.5),
    ]
    cv.draw_polygon(face_poly, SKIN)
    cv.draw_line(S(-0.2, -47.5)[0], S(-0.2, -47.5)[1], S(2.8, -47.5)[0], S(2.8, -47.5)[1], SKIN_SHADOW, 0.9 * scale)

    # Slender Pointed Elven Ear
    ear_poly = [
        S(-1.0, -52.0),
        S(-5.5, -54.2),
        S(-1.5, -49.5),
    ]
    cv.draw_polygon(ear_poly, SKIN)
    cv.draw_line(S(-1.0, -52.0)[0], S(-1.0, -52.0)[1], S(-5.5, -54.2)[0], S(-5.5, -54.2)[1], SKIN_LIGHT, 0.8 * scale)
    cv.draw_circle(S(-4.0, -53.5)[0], S(-4.0, -53.5)[1], 0.7 * scale, GOLD_LIGHT)

    # Soft Rosy Cheek Blush
    cv.draw_circle(S(2.5, -50.2)[0], S(2.5, -50.2)[1], 1.5 * scale, SKIN_BLUSH)

    # Beautiful Emerald Anime Eye
    eye_c = S(2.4, -52.6)
    cv.draw_circle(eye_c[0], eye_c[1], 1.6 * scale, EYE_WHITE)
    cv.draw_circle(eye_c[0] + 0.15 * scale, eye_c[1], 1.2 * scale, EYE_DARK)
    cv.draw_circle(eye_c[0] + 0.25 * scale, eye_c[1] + 0.15 * scale, 0.95 * scale, EYE)
    cv.draw_circle(eye_c[0] + 0.35 * scale, eye_c[1] - 0.15 * scale, 0.5 * scale, INK)
    # Double sparkle catchlights
    cv.draw_circle(eye_c[0] + 0.6 * scale, eye_c[1] - 0.5 * scale, 0.5 * scale, (255, 255, 255, 255))
    cv.draw_circle(eye_c[0] - 0.15 * scale, eye_c[1] + 0.4 * scale, 0.3 * scale, (255, 255, 255, 200))
    # Winged eyeliner
    cv.draw_line(S(1.2, -53.6)[0], S(1.2, -53.6)[1], S(3.5, -53.9)[0], S(3.5, -53.9)[1], INK, 1.2 * scale)
    cv.draw_line(S(3.3, -53.9)[0], S(3.3, -53.9)[1], S(4.2, -54.4)[0], S(4.2, -54.4)[1], INK, 0.9 * scale)
    # Arched eyebrow
    cv.draw_line(S(1.2, -55.2)[0], S(1.2, -55.2)[1], S(3.5, -54.9)[0], S(3.5, -54.9)[1], HAIR_DARK, 0.8 * scale)

    # Nose highlight & lips
    cv.draw_circle(S(4.0, -49.8)[0], S(4.0, -49.8)[1], 0.5 * scale, (255, 250, 245, 220))
    cv.draw_line(S(2.2, -48.0)[0], S(2.2, -48.0)[1], S(3.3, -48.0)[0], S(3.3, -48.0)[1], LIP, 1.1 * scale)
    cv.draw_circle(S(2.7, -47.8)[0], S(2.7, -47.8)[1], 0.4 * scale, LIP_SHINE)

    # Bangs & Sidelock
    bang_poly = [
        S(-0.5, -57.0),
        S(1.2, -55.0),
        S(2.2, -56.5),
    ]
    cv.draw_polygon(bang_poly, HAIR_LIGHT)
    sidelock = [
        S(-0.5, -52.0),
        S(0.2, -46.5),
        S(-0.8, -47.0),
        S(-1.5, -51.5),
    ]
    cv.draw_polygon(sidelock, HAIR)
    cv.draw_line(S(-0.3, -51.5)[0], S(-0.3, -51.5)[1], S(0.0, -46.8)[0], S(0.0, -46.8)[1], HAIR_SHINE, 0.8 * scale)

    # 9. Shoulder Pauldron & Bow Arm
    sh_f = S(3.5, -42.0)
    cv.draw_circle(sh_f[0], sh_f[1], 2.6 * scale, LEATHER)
    cv.draw_circle(sh_f[0], sh_f[1], 1.3 * scale, GOLD_LIGHT)

    # Bow Arm
    elb = S(7.5, -38.0)
    hand = S(12.5, -36.5)
    cv.draw_line(sh_f[0], sh_f[1], elb[0], elb[1], CLOTH, 3.0 * scale)
    cv.draw_line(elb[0], elb[1], hand[0], hand[1], LEATHER, 2.8 * scale)
    cv.draw_line(elb[0], elb[1], hand[0], hand[1], LEATHER_LIGHT, 0.9 * scale)
    cv.draw_circle(hand[0], hand[1], 1.8 * scale, SKIN)

    # 10. Recurve Bow & String
    grip = hand
    tip_up = S(17.0, -56.0)
    ctrl_up = S(21.5, -46.0)
    tip_low = S(17.0, -16.0)
    ctrl_low = S(21.5, -26.0)

    # Recurve upper limb
    cv.draw_bezier(grip, ctrl_up, tip_up, WOOD, 2.6 * scale)
    cv.draw_bezier(grip, ctrl_up, tip_up, GOLD_LIGHT, 1.0 * scale)
    # Recurve lower limb
    cv.draw_bezier(grip, ctrl_low, tip_low, WOOD, 2.6 * scale)
    cv.draw_bezier(grip, ctrl_low, tip_low, GOLD_LIGHT, 1.0 * scale)

    # Ivory Horn Tips
    cv.draw_circle(tip_up[0], tip_up[1], 1.5 * scale, HORN_TIP)
    cv.draw_circle(tip_low[0], tip_low[1], 1.5 * scale, HORN_TIP)
    cv.draw_circle(tip_up[0], tip_up[1], 0.9 * scale, GOLD_LIGHT)
    cv.draw_circle(tip_low[0], tip_low[1], 0.9 * scale, GOLD_LIGHT)

    # Luminous Mana String (with bow_draw pull back!)
    if bow_draw > 0.05:
        nock = S(17.0 - bow_draw * 12.0, -36.5)
        # Drawn string
        cv.draw_line(tip_up[0], tip_up[1], nock[0], nock[1], STRING_GLOW, 2.6 * scale)
        cv.draw_line(nock[0], nock[1], tip_low[0], tip_low[1], STRING_GLOW, 2.6 * scale)
        cv.draw_line(tip_up[0], tip_up[1], nock[0], nock[1], STRING, 1.2 * scale)
        cv.draw_line(nock[0], nock[1], tip_low[0], tip_low[1], STRING, 1.2 * scale)
        # Glowing arrow loaded on string!
        arrow_head = S(26.0, -36.5)
        cv.draw_line(nock[0], nock[1], arrow_head[0], arrow_head[1], (200, 175, 130, 255), 1.4 * scale)
        cv.draw_circle(arrow_head[0], arrow_head[1], 1.8 * scale, (210, 230, 255, 255))
        cv.draw_circle(arrow_head[0], arrow_head[1], 1.1 * scale, (255, 255, 255, 255))
        cv.draw_circle(nock[0], nock[1], 2.4 * scale, WIND_BRIGHT)
    else:
        cv.draw_line(tip_up[0], tip_up[1], tip_low[0], tip_low[1], STRING_GLOW, 2.6 * scale)
        cv.draw_line(tip_up[0], tip_up[1], tip_low[0], tip_low[1], STRING, 1.2 * scale)

    # Floating Wind sparkles
    cv.draw_circle(tip_up[0] + 3 * scale, tip_up[1] - 2 * scale, 1.2 * scale, WIND_BRIGHT)
    cv.draw_circle(tip_low[0] + 3 * scale, tip_low[1] + 3 * scale, 1.1 * scale, WIND_BRIGHT)
    cv.draw_circle(S(-8.0, -28.0)[0], S(-8.0, -28.0)[1], 1.0 * scale, LEAF_GOLD)


def main():
    W, H = 1040, 560
    cv = Canvas(W, H, (10, 16, 12, 255))

    # 1. Left: Arena In-Game Scale (~70px tall, scale=1.3)
    draw_sylara(cv, 110, 430, scale=1.3, bow_draw=0.0)

    # 2. Middle-Left: Full Body Idle / Showcase (scale=3.4)
    draw_sylara(cv, 340, 480, scale=3.4, bow_draw=0.0)

    # 3. Middle-Right: Full Body Attack / Powershot Draw (scale=3.4, bow_draw=0.85)
    draw_sylara(cv, 590, 480, scale=3.4, bow_draw=0.85)

    # 4. Right: Close-Up Elven Heroine Portrait (scale=7.0)
    draw_sylara(cv, 870, 680, scale=7.0, bow_draw=0.0)

    out = "docs/sylara_godot_new_preview.png"
    cv.save_png(out)
    print("Preview saved to", out)


if __name__ == "__main__":
    main()
