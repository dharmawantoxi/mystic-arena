#!/usr/bin/env python3
"""Ganti lengan & kapak Khalros ke versi doodle. Idempotent via sentinel.
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "bosses", "level2.py")

with io.open(SRC, "r", encoding="utf-8") as fh:
    text = fh.read()

if "_DOODLE_FLAG_ARMS" in text:
    print("SKIP: arms doodle sudah ada")
    raise SystemExit(0)


def replace_fn(text, name, body):
    start = text.index("    def %s(" % name)
    scan = text.index("\n", start) + 1
    lines = text[scan:].split("\n")
    consumed = 0
    for ln in lines:
        if ln.startswith("    def ") or ln.startswith("    # ===") or \
           (ln.strip() and not ln.startswith(" ") and not ln.startswith("#")):
            break
        consumed += 1
    end = scan + len("\n".join(lines[:consumed]))
    nxt = text.find("\n    def ", end)
    if nxt == -1:
        nxt = text.find("\n    # ===", end)
    return text[:start] + body + text[(nxt if nxt != -1 else end):]


ARM_SEG = '''    def _draw_arm_segment(surface, x1, y1, x2, y2, wrap=True, bulk=9):
        """Segmen lengan doodle: sosis flat + outline + lilitan kulit."""
        NS = _NS_khalros
        P = NS.PALETTE
        dx, dy = x2 - x1, y2 - y1
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        a = (x1 + nx * bulk, y1 + ny * bulk)
        b = (x1 - nx * bulk, y1 - ny * bulk)
        c = (x2 - nx * bulk * 0.6, y2 - ny * bulk * 0.6)
        d = (x2 + nx * bulk * 0.6, y2 + ny * bulk * 0.6)
        NS._doodle_poly(surface, P["skin_mid"], P["shadow"],
                        [a, b, c, d], width=5, seed=100, wobble=1.1)
        if wrap:
            for i in range(3):
                t = 0.42 + i * 0.16
                px, py = x1 + dx * t, y1 + dy * t
                NS._doodle_line(surface, P["leather_darkest"],
                                [(px + nx * bulk * .7, py + ny * bulk * .7),
                                 (px - nx * bulk * .7, py - ny * bulk * .7)],
                                3, seed=102 + i, wobble=0.7)

'''

HAND = '''    def _draw_hand(surface, x, y, facing=1, grip=False):
        """Tangan doodle: kepalan bulat + buku jari."""
        NS = _NS_khalros
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        NS._doodle_poly(surface, P["skin_mid"], P["shadow"],
                        [(x - 7, y - 6), (x + 7, y - 6), (x + 8, y + 5),
                         (x - 8, y + 5)], width=4, seed=105, wobble=1.0)
        NS._doodle_dot(surface, P["skin_light"],
                       [(x - 3 * f, y - 2), (x + 2 * f, y - 3),
                        (x, y + 2)], 2)
        if grip:
            NS._doodle_dot(surface, P["gold_light"], [(x + 4 * f, y + 1)], 2)

'''

DELTOID = '''    def _draw_deltoid(surface, x, y, facing=1):
        """Bahu berotot doodle: lingkaran besar + outline tebal."""
        NS = _NS_khalros
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        NS._doodle_poly(surface, P["skin_mid"], P["shadow"],
                        [(x - 9, y - 8), (x + 9, y - 8), (x + 11, y + 2),
                         (x + 5, y + 8), (x - 8, y + 7), (x - 11, y - 1)],
                        width=5, seed=107, wobble=1.2)
        NS._doodle_dot(surface, P["skin_light"],
                       [(x - 4 * f, y - 3), (x - 2, y + 2)], 2)

'''

AXE = '''    def _draw_axe_swinging(surface, hx, hy, facing, angle, size=1.0,
                           hot=0.0):
        """Kapak doodle besar: gagang + bilah kipas + mata emas.

        Cermin horizontal (lihat aturan masterwork): sudut dihitung dari
        (cos*facing, sin) supaya bilah & trail satu arah.
        """
        NS = _NS_khalros
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        ca0, sa0 = math.cos(angle) * f, math.sin(angle)
        ang = math.atan2(sa0, ca0)
        bx, by, nx, ny, L = NS._axe_blade_shape(hx, hy, ang, size)
        tipx, tipy = bx + math.cos(ang) * L, by + math.sin(ang) * L
        # gagang kulit doodle (tebal)
        NS._doodle_line(surface, P["leather_mid"],
                        [(hx - math.cos(ang) * 8 * size,
                          hy - math.sin(ang) * 8 * size), (bx, by)],
                        int(6 * size), seed=110, wobble=0.8)
        NS._doodle_line(surface, P["leather_darkest"],
                        [(hx - math.cos(ang) * 8 * size,
                          hy - math.sin(ang) * 8 * size), (bx, by)],
                        int(2 * size), seed=111, wobble=0.8)
        for i in range(3):
            t = 0.2 + i * 0.22
            px = hx - math.cos(ang) * 8 * size + \
                (bx - hx + math.cos(ang) * 8 * size) * t
            py = hy - math.sin(ang) * 8 * size + \
                (by - hy + math.sin(ang) * 8 * size) * t
            NS._doodle_line(surface, P["leather_light"],
                            [(px + nx * 2, py + ny * 2),
                             (px - nx * 2, py - ny * 2)], 1, seed=112 + i)
        # bilah kipas bergerigi doodle
        half = L * 0.55
        shape = [(bx - nx * half * 0.3, by - ny * half * 0.3),
                 (bx + math.cos(ang) * L * 0.5 + nx * half,
                  by + math.sin(ang) * L * 0.5 + ny * half),
                 (tipx + nx * half * 0.5, tipy + ny * half * 0.5),
                 (tipx - nx * half * 0.4, tipy - ny * half * 0.4),
                 (bx + math.cos(ang) * L * 0.45 - nx * half * 0.9,
                  by + math.sin(ang) * L * 0.45 - ny * half * 0.9)]
        NS._doodle_poly(surface, P["metal_mid"], P["shadow"], shape,
                        width=5, seed=114, wobble=1.2)
        NS._doodle_poly(surface, P["metal_light"], None,
                        [(bx + math.cos(ang) * L * 0.2 + nx * half * 0.4,
                          by + math.sin(ang) * L * 0.2 + ny * half * 0.4),
                         (bx + math.cos(ang) * L * 0.7 + nx * half * 0.5,
                          by + math.sin(ang) * L * 0.7 + ny * half * 0.5),
                         (tipx - nx * half * 0.1, tipy - ny * half * 0.1)],
                        width=0)
        # fuller gelap + tepi tajam
        NS._doodle_line(surface, P["metal_darkest"],
                        [(bx + math.cos(ang) * L * 0.15,
                          by + math.sin(ang) * L * 0.15),
                         (tipx - nx * 2, tipy - ny * 2)], 3, seed=115,
                        wobble=0.6)
        NS._doodle_dot(surface, P["gold_mid"],
                       [(bx + math.cos(ang) * 4 * size,
                         by + math.sin(ang) * 4 * size)], 3)
        # membara saat rage/impact
        if hot > 0.02:
            a = NS._alpha(230 * hot)
            NS._doodle_dot(surface, (*P["fire_glow"], a),
                           [(int(tipx), int(tipy))], 5)
        return tipx, tipy

'''

AXE_HELD = '''    def _draw_axe_held(surface, hx, hy, side, phase, hot=0.0):
        """Kapak cadangan tersandang doodle - kepala bilah di atas bahu."""
        NS = _NS_khalros
        P = NS.PALETTE
        ang = -1.32 + math.sin(phase * 0.5) * 0.03
        f = 1 if side >= 0 else -1
        ca, sa = math.cos(ang) * f, math.sin(ang)
        ang = math.atan2(sa, ca)
        bx, by, nx, ny, L = NS._axe_blade_shape(hx, hy, ang, 0.68)
        NS._doodle_line(surface, P["leather_mid"],
                        [(hx - ca * 10, hy - sa * 10), (bx, by)], 4,
                        seed=118, wobble=0.8)
        shape = [(bx + nx * 6, by + ny * 6), (bx + f * L * 0.5, by - 4),
                 (bx + f * L * 0.78, by + 3), (bx + nx * 2, by + ny * 8),
                 (bx - nx * 5, by - ny * 5)]
        NS._doodle_poly(surface, P["metal_mid"], P["shadow"], shape,
                        width=4, seed=119, wobble=1.0)
        NS._doodle_poly(surface, P["metal_light"], None,
                        [(bx + f, by - 3), (bx + f * L * 0.6, by - 2),
                         (bx + f * L * 0.5, by + 1)], width=0)
        if hot > 0.02:
            NS._doodle_dot(surface, P["fire_glow"],
                           [(int(bx + f * L * 0.5), int(by))], 3)

'''

IDLE_ARMS = '''    def _draw_idle_arms(surface, cx, cy, facing, phase, action="idle",
                        late=False):
        """Dua lengan doodle: depan pegang kapak, belakang kapak cadangan."""
        NS = _NS_khalros
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        sway = int(math.sin(phase * 0.7) * 1.6)
        sh_y = cy - 42
        if late:
            gx, gy = NS._axe_grip_local(action, phase, 0.0, f)
            fx, fy = cx + gx * f, cy + gy
            if action == "cast":
                ang = -0.35 + math.sin(phase * 1.6) * 0.10
                hot = 0.55
            else:
                ang = -1.25 + math.sin(phase * 0.7) * 0.06
                hot = 0.0
            NS._draw_axe_swinging(surface, fx, fy, f, ang, 1.0, hot=hot)
            NS._draw_hand(surface, int(fx), int(fy), f, grip=True)
            return
        # lengan belakang
        be_sx = cx - 22 * f
        be_hx = be_sx - 8 * f
        be_hy = sh_y + 30 + sway
        NS._draw_arm_segment(surface, be_sx, sh_y + 4, be_hx - 2 * f, be_hy,
                             bulk=8)
        NS._draw_hand(surface, int(be_hx - 2 * f), int(be_hy), f)
        NS._draw_axe_held(surface, int(be_hx - 1 * f), int(be_hy - 4), -f,
                          phase)
        # lengan depan -> grip kapak
        gx, gy = NS._axe_grip_local(action, phase, 0.0, f)
        fx, fy = cx + gx * f, cy + gy
        fe_sx = cx + 22 * f
        elbow = ((fe_sx + fx) / 2 + 5 * f, (sh_y + fy) / 2 + 6)
        NS._draw_arm_segment(surface, fe_sx, sh_y + 2, elbow[0], elbow[1],
                             bulk=9)
        NS._draw_arm_segment(surface, elbow[0], elbow[1], fx, fy, bulk=7)
        NS._draw_deltoid(surface, fe_sx, sh_y, f)
        if action == "cast":
            ang = -0.35 + math.sin(phase * 1.6) * 0.10
            hot = 0.55
        else:
            ang = -1.25 + math.sin(phase * 0.7) * 0.06
            hot = 0.0
        NS._draw_axe_swinging(surface, fx, fy, f, ang, 1.0, hot=hot)
        NS._draw_hand(surface, int(fx), int(fy), f, grip=True)

'''

ATTACK_ARMS = '''    def _draw_attack_arms(surface, cx, cy, facing, phase, progress,
                          action="attack", late=False):
        """Lengan saat ayunan doodle (keyframe arm_a menggerakkan kapak)."""
        NS = _NS_khalros
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        pose = NS._attack_pose(progress)
        sh_y = cy - 42
        gx, gy = NS._axe_grip_local(action, phase, progress, f)
        fx, fy = cx + gx * f, cy + gy
        if late:
            NS._draw_axe_swinging(surface, fx, fy, f, pose["arm_a"] + 0.72,
                                  1.0,
                                  hot=pose["impact"] if action == "attack"
                                  else 0.55)
            NS._draw_hand(surface, int(fx), int(fy), f, grip=True)
            return
        fe_sx = cx + 21 * f
        elbow = ((fe_sx + fx) / 2 + 4 * f, (sh_y + fy) / 2 + 4)
        # lengan belakang keseimbangan
        be_sx = cx - 21 * f
        be_hx = be_sx - 13 * f
        be_hy = sh_y + 26 - pose["lean"] * 0.5
        NS._draw_arm_segment(surface, be_sx, sh_y + 3, be_hx, be_hy, bulk=8)
        NS._draw_hand(surface, int(be_hx), int(be_hy), f)
        NS._draw_arm_segment(surface, fe_sx, sh_y + 1, elbow[0], elbow[1],
                             bulk=9)
        NS._draw_arm_segment(surface, elbow[0], elbow[1], fx, fy, bulk=7)
        NS._draw_deltoid(surface, fe_sx, sh_y, f)
        ang = pose["arm_a"] + 0.72
        hot = pose["impact"] if action == "attack" else 0.55
        NS._draw_axe_swinging(surface, fx, fy, f, ang, 1.0, hot=hot)
        NS._draw_hand(surface, int(fx), int(fy), f, grip=True)

'''

for name, body in (("_draw_arm_segment", ARM_SEG), ("_draw_hand", HAND),
                   ("_draw_deltoid", DELTOID),
                   ("_draw_axe_swinging", AXE),
                   ("_draw_axe_held", AXE_HELD),
                   ("_draw_idle_arms", IDLE_ARMS),
                   ("_draw_attack_arms", ATTACK_ARMS)):
    text = replace_fn(text, name, body)

text = text.replace("    # ===================================================================\n    # LENGAN + KAPAK",
                    "    # ===================================================================\n    # LENGAN + KAPAK  _DOODLE_FLAG_ARMS", 1)

with io.open(SRC, "w", encoding="utf-8") as fh:
    fh.write(text)
print("OK: arms doodle diganti")
