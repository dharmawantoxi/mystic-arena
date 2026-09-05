#!/usr/bin/env python3
"""Ganti fungsi anatomi Khalros (cape/elang/kaki/cawat/torso/bahu/kepala/
helm) ke versi doodle. Idempotent via penanda sentinel.
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "bosses", "level2.py")

with io.open(SRC, "r", encoding="utf-8") as fh:
    text = fh.read()

if "_DOODLE_FLAG_TORSO" in text:
    print("SKIP: anatomi doodle sudah ada")
    raise SystemExit(0)


def replace_fn(text, name, body):
    """Ganti isi `def <name>(...):` sampai `def` berikutnya (4-spasi)."""
    start = text.index("    def %s(" % name)
    # cari akhir fungsi: baris `    def ` berikutnya ATAU baris pertama yg
    # tidak ber-4-spasi & tidak kosong dalam rentang ini.
    scan = text.index("\n", start) + 1
    lines = text[scan:].split("\n")
    consumed = 0
    for ln in lines:
        # hentikan kalau bertemu def top-level kelas (4 spasi) yg baru
        if ln.startswith("    def ") or ln.startswith("    # ===") or \
           (ln.strip() and not ln.startswith(" ") and not ln.startswith("#")):
            break
        consumed += 1
    end = scan + len("\n".join(lines[:consumed]))
    # pastikan akhir fungsi = awal def berikutnya
    nxt = text.find("\n    def ", end)
    if nxt == -1:
        nxt = text.find("\n    # ===", end)
    replace_span = (start, nxt if nxt != -1 else end)
    return text[:start] + body + text[replace_span[1]:]


# ── CAPE ────────────────────────────────────────────────────────────
CAPE = '''    def _draw_beast_cape(surface, cx, cy, facing, phase, action, lag=0.0):
        """Jubah serigala doodle: blok flat biru-abu + outline tebal + arsir.

        Menjulur ke belakang (berlawanan arah hadap), ikut inersia `lag`.
        """
        NS = _NS_khalros
        P = NS.PALETTE
        f = facing
        sway = lag + math.sin(phase * 0.65) * 2.0
        top = cy - 46
        hem = cy + 12 + abs(lag) * 0.6
        pts = [(cx - 4 * f, top), (cx - 28 * f, top + 8),
               (cx - 31 * f + sway, cy - 12),
               (cx - 22 * f + sway * 1.4, hem - 4),
               (cx - 11 * f + sway * 1.6, hem),
               (cx + 3 * f + sway * 1.2, hem - 3),
               (cx + 13 * f, cy - 6), (cx + 16 * f, top + 8)]
        # isi flat + outline spidol tebal
        NS._doodle_poly(surface, P["wolf_mid"], P["shadow"], pts,
                        width=5, seed=19, wobble=1.5)
        # bayangan sisi dalam
        NS._doodle_poly(surface, P["wolf_dark"], None,
                        [(cx + (p[0] - cx) * 0.78, cy + (p[1] - cy) * 0.82)
                         for p in pts], width=0)
        # arsir bulu
        NS._doodle_hatch(surface, P["wolf_high"],
                         [(cx - 26 * f, top + 10), (cx - 28 * f, cy - 8),
                          (cx - 14 * f, cy - 4), (cx - 10 * f, top + 12)],
                         spacing=6, alpha=120)
        # kepala serigala sebagai penutup bahu + telinga
        hx, hy = cx + 7 * f, top - 3
        head = [(hx, hy - 10), (hx + 12 * f, hy - 6),
                (hx + 10 * f, hy + 6), (hx - 3 * f, hy + 5)]
        NS._doodle_poly(surface, P["wolf_dark"], P["shadow"], head,
                        width=4, seed=20)
        NS._doodle_dot(surface, P["fire_glow"], [(hx + 6 * f, hy - 2)], 2)
        # jahitan melintang (garis putus doodle)
        for i in range(4):
            yy = top + 9 + i * 10
            NS._doodle_line(surface, P["bone_mid"],
                            [(cx - (23 - i) * f, yy),
                             (cx - (16 - i) * f, yy + 2)], 2, seed=21 + i)

'''

# ── HAWK ────────────────────────────────────────────────────────────
HAWK = '''    def _draw_hawk_companion(surface, cx, cy, facing, phase, action, rage):
        """Elang pendamping doodle di bahu belakang - kepak & kedip."""
        NS = _NS_khalros
        P = NS.PALETTE
        f = facing
        blink = int(phase * 1.7) % 11 == 0
        ruffle = math.sin(phase * 1.9) * (1.6 if action == "idle" else 2.4)
        flap = math.sin(phase * (2.6 if rage else 1.2)) * (5 if rage else 2)
        # sayap terlipat doodle
        wing = [(cx - 5 * f, cy - 2), (cx - 15 * f, cy - 1 - ruffle * .5),
                (cx - 18 * f, cy + 7), (cx - 4 * f, cy + 7)]
        NS._doodle_poly(surface, P["hawk_mid"], P["shadow"], wing,
                        width=3, seed=24)
        if flap > 0.4:   # regang saat rage
            NS._doodle_poly(surface, P["hawk_light"], None,
                            [(cx - 8 * f, cy - 2),
                             (cx - 20 * f, cy - 7 - flap),
                             (cx - 15 * f, cy + 1)], width=0)
        # badan + dada
        body = [(cx - 6 * f, cy - 9), (cx + 6 * f, cy - 7),
                (cx + 5 * f, cy + 4), (cx - 5 * f, cy + 4)]
        NS._doodle_poly(surface, P["hawk_dark"], P["shadow"], body,
                        width=3, seed=25)
        # kepala + paruh + mata
        hx, hy = cx + 4 * f, cy - 7
        NS._doodle_poly(surface, P["hawk_light"], P["shadow"],
                        [(hx - 4 * f, hy - 4), (hx + 4 * f, hy - 4),
                         (hx + 4 * f, hy + 3), (hx - 4 * f, hy + 3)],
                        width=3, seed=26)
        NS._doodle_poly(surface, P["hawk_beak"], P["shadow"],
                        [(hx + 3 * f, hy), (hx + 8 * f, hy + 2),
                         (hx + 3 * f, hy + 3)], width=2, seed=27)
        if blink:
            NS._doodle_line(surface, P["shadow"],
                            [(hx - 2 * f, hy - 1), (hx + 2 * f, hy - 1)],
                            2, seed=28)
        else:
            NS._doodle_dot(surface, P["fire_glow"], [(hx + f, hy - 2)], 2)
        # tungging bulu di kepala
        NS._doodle_line(surface, P["hawk_darkest"],
                        [(hx - 3 * f, hy - 4), (hx - 8 * f, hy - 9)], 3,
                        seed=29)

'''

# ── LEGS ────────────────────────────────────────────────────────────
LEGS = '''    def _draw_legs(surface, cx, cy, facing, phase, action, stride):
        """Kaki barbar doodle: chunky, boot besar, outline tebal flat.

        Jangkar vertikal dijaga (paha cy+8, lutut cy+30, pergelangan
        cy+48, sol cy+60..66) supaya GROUND_DY & bayangan tetap menapak.
        """
        NS = _NS_khalros
        P = NS.PALETTE
        f = facing
        sw_a, sw_b, lift_a, lift_b, _contact = stride
        for i, (swing, lift, back) in enumerate(((sw_a, lift_a, 1),
                                                 (sw_b, lift_b, 0))):
            fill = P["skin_dark"] if back else P["skin_mid"]
            boot = P["leather_dark"] if back else P["leather_mid"]
            fill2 = P["leaf"] if False else P["leather_mid"]
            k = 0.92 if back else 1.0
            hipx = cx + (14 - i * 28) * f * 0.46
            hipy = cy + 8
            kx = hipx + swing * 12 * f
            ky = cy + 30 - lift * 0.8
            ax = hipx + swing * 17 * f
            ay = cy + 48 - lift
            my = (ky + ay) / 2.0
            th, an = 12.5 * k, 8.0 * k
            # paha kuadrisep doodle
            thigh = [(hipx - th, hipy - 3), (kx - an, ky - 1),
                     (kx + an, ky - 1), (hipx + th, hipy - 3)]
            NS._doodle_poly(surface, fill, P["shadow"], thigh,
                            width=4, seed=30 + i)
            # betis doodle
            shin = [(kx - an + 1, ky), (ax - an, ay - 2),
                    (ax + an, ay - 2), (kx + an - 1, ky)]
            NS._doodle_poly(surface, fill, P["shadow"], shin,
                            width=4, seed=32 + i)
            # pelindung lutut kulit + paku
            knee = [(kx - 6.5 * k, ky - 4), (kx + 6.5 * k, ky - 4),
                    (kx + 5.0 * k, ky + 4), (kx - 5.0 * k, ky + 4)]
            NS._doodle_poly(surface, boot, P["shadow"], knee,
                            width=3, seed=34 + i)
            NS._doodle_dot(surface, P["gold_light"],
                           [(kx - 3 * f, ky - 1), (kx + 3 * f, ky + 1)], 1)
            # otot paha garis
            NS._doodle_line(surface, P["skin_light"],
                            [(hipx - 4 * f, hipy), (kx - 4 * f, ky - 3)],
                            2, seed=36 + i)
            # boot fur doodle (melebar)
            bx0 = ax - an - 3 * k
            bx1 = ax + an + 3 * k
            toe = 10.5 * k * f
            boot_pts = [(bx0, ay - 4), (bx1, ay - 4),
                        (ax + toe, ay + 12), (ax - toe, ay + 12)]
            NS._doodle_poly(surface, boot, P["shadow"], boot_pts,
                            width=4, seed=38 + i)
            NS._doodle_line(surface, P["leather_light"],
                            [(bx0 + 2, ay - 1), (bx1 - 2, ay - 1)], 2,
                            seed=40 + i)
            # sol + cakar (garis kuku)
            heel = 9.0 * k
            sole_x = ax - (heel if f > 0 else 10.5 * k)
            sole_w = heel + 10.5 * k
            NS._doodle_poly(surface, P["metal_dark"], P["shadow"],
                            [(sole_x, ay + 12), (sole_x + sole_w, ay + 12),
                             (sole_x + sole_w, ay + 15),
                             (sole_x, ay + 15)], width=2, seed=42 + i)
            for c in range(4):
                NS._doodle_line(surface, P["bone_light"],
                                [(ax + (7 - c * 4.6) * f, ay + 13),
                                 (ax + (10.5 - c * 4.6) * f, ay + 16)],
                                2, seed=44 + i, wobble=0.6)

'''

# ── LOINCLOTH ───────────────────────────────────────────────────────
LOIN = '''    def _draw_loincloth(surface, cx, cy, phase, sway, action="idle"):
        """Cawat babi hutan doodle: blok bulu + ikat pinggang tulang."""
        NS = _NS_khalros
        P = NS.PALETTE
        lag = math.sin(phase * 0.9) * (2.0 if action == "walk" else 0.8)
        # panel depan ber-hem
        pts = [(cx - 17, cy + 2), (cx - 19, cy + 16),
               (cx - 9, cy + 24 + lag), (cx, cy + 26 + lag * 1.2),
               (cx + 9, cy + 24 + lag), (cx + 19, cy + 16),
               (cx + 17, cy + 2)]
        NS._doodle_poly(surface, P["boar_mid"], P["shadow"], pts,
                        width=4, seed=50, wobble=1.4)
        NS._doodle_poly(surface, P["boar_light"], None,
                        [(cx - 11, cy + 4), (cx + 8, cy + 4),
                         (cx + 6, cy + 15), (cx - 9, cy + 15)], width=0)
        NS._doodle_hatch(surface, P["boar_high"],
                         [(cx - 14, cy + 6), (cx + 14, cy + 6),
                          (cx + 6, cy + 20), (cx - 6, cy + 20)],
                         spacing=6, angle=0.4, alpha=110)
        # dua untai bulu menggantung
        for sgn in (-1, 1):
            strand = [(cx + sgn * 16, cy + 4),
                      (cx + sgn * 21, cy + 15 + lag),
                      (cx + sgn * 18, cy + 25 + lag * 1.4)]
            NS._doodle_poly(surface, P["leather_darkest"], P["shadow"],
                            strand, width=3, seed=52 + sgn)
        # ikat pinggang doodle
        belt = [(cx - 20, cy - 6), (cx + 20, cy - 6), (cx + 20, cy + 1),
                (cx - 20, cy + 1)]
        NS._doodle_poly(surface, P["leather_dark"], P["shadow"], belt,
                        width=3, seed=54)
        for i in range(5):
            xx = cx - 14 + i * 7
            NS._doodle_poly(surface, P["bone_light"], P["shadow"],
                            [(xx, cy + 1), (xx + 3, cy + 1),
                             (xx + 1, cy + 6)], width=1, seed=56 + i)
        NS._doodle_poly(surface, P["gold_mid"], P["shadow"],
                        [(cx - 5, cy - 4), (cx + 5, cy - 4),
                         (cx + 4, cy + 1), (cx - 4, cy + 1)],
                        width=2, seed=58)

'''

# ── TORSO ───────────────────────────────────────────────────────────
TORSO = '''    def _draw_torso(surface, cx, cy, phase, sway, action="idle", rage=False,
                    ap=0.0):
        """Torso barbar doodle: dada lebar flat + otot garis + war paint."""
        NS = _NS_khalros
        P = NS.PALETTE
        breath = math.sin(phase * 0.72) * (1.4 if action != "attack" else 0.7)
        sh_y = cy - 38
        waist = cy
        # dada trapezoid doodle
        pts = [(cx - 30, sh_y - 3), (cx + 30, sh_y - 3),
               (cx + 22, sh_y + 16), (cx + 12, waist),
               (cx - 12, waist), (cx - 22, sh_y + 16)]
        NS._doodle_poly(surface, P["skin_mid"], P["shadow"], pts,
                        width=5, seed=60, wobble=1.4)
        # highlight dada (sisi cahaya kiri-atas)
        NS._doodle_poly(surface, P["skin_light"], None,
                        [(cx - 25, sh_y), (cx + 24, sh_y),
                         (cx + 14, sh_y + 15), (cx - 17, sh_y + 15)],
                        width=0)
        # bayangan bawah perut
        NS._doodle_poly(surface, P["skin_dark"], None,
                        [(cx - 11, waist - 8), (cx + 11, waist - 8),
                         (cx + 8, waist + 1), (cx - 8, waist + 1)],
                        width=0)
        # garis dada tengah + otot perut
        NS._doodle_line(surface, P["skin_darkest"],
                        [(cx, sh_y + 3), (cx, waist - 6)], 2, seed=61)
        for i in range(3):
            yy = sh_y + 19 + i * 5
            w = 10 - i * 2
            NS._doodle_line(surface, P["skin_darkest"],
                            [(cx - w, yy), (cx + w, yy)], 2, seed=62 + i,
                            wobble=0.7)
        # harness silang + rivet
        NS._doodle_line(surface, P["leather_darkest"],
                        [(cx - 24, sh_y), (cx + 13, waist - 4)], 4,
                        seed=66, wobble=0.9)
        NS._doodle_line(surface, P["leather_darkest"],
                        [(cx + 24, sh_y), (cx - 12, waist - 3)], 4,
                        seed=67, wobble=0.9)
        # war paint merah
        NS._doodle_poly(surface, P["red_mid"], None,
                        [(cx - 17, sh_y + 6), (cx - 8, sh_y + 4),
                         (cx - 7, sh_y + 15), (cx - 16, sh_y + 17)],
                        width=0)
        NS._doodle_poly(surface, P["red_mid"], None,
                        [(cx + 8, sh_y + 5), (cx + 16, sh_y + 7),
                         (cx + 15, sh_y + 16), (cx + 9, sh_y + 14)],
                        width=0)
        # kalung taring
        for i in range(5):
            tx = cx - 10 + i * 5
            NS._doodle_poly(surface, P["bone_light"], P["shadow"],
                            [(tx, sh_y + 1), (tx + 3, sh_y + 1),
                             (tx + 1, sh_y + 6)], width=1, seed=70 + i)

'''

# ── SHOULDERS ───────────────────────────────────────────────────────
SHOULDERS = '''    def _draw_shoulders(surface, cx, cy, phase, facing=1, action="idle",
                        rage=False):
        """Pauldron doodle: bulu babi berduri (depan) + pelat besi (blk)."""
        NS = _NS_khalros
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        sh_y = cy - 36
        for side in (1, -1):
            front = side > 0
            bx = cx + side * 28 * f * (1 if front else 0.92)
            by = sh_y + (0 if front else 1)
            if front:
                # bulu babi doodle + duri tulang
                pts = [(bx - 12, by - 6), (bx + 10, by - 9),
                       (bx + 15, by + 2), (bx + 7, by + 11),
                       (bx - 11, by + 8)]
                NS._doodle_poly(surface, P["boar_mid"], P["shadow"], pts,
                                width=4, seed=72, wobble=1.5)
                # duri tulang
                NS._doodle_poly(surface, P["bone_light"], P["shadow"],
                                [(bx + 4, by - 7), (bx + 13, by - 18),
                                 (bx + 9, by - 6)], width=2, seed=73)
                NS._doodle_poly(surface, P["bone_light"], P["shadow"],
                                [(bx - 5, by - 5), (bx + 1, by - 15),
                                 (bx - 1, by - 4)], width=2, seed=74)
                # rivet emas
                NS._doodle_dot(surface, P["gold_light"],
                               [(bx - 5 + i * 6, by + 6) for i in range(3)],
                               2)
            else:
                # pelat besi doodle
                pts = [(bx - 13, by - 5), (bx + 10, by - 8),
                       (bx + 13, by + 4), (bx + 3, by + 11),
                       (bx - 12, by + 8)]
                NS._doodle_poly(surface, P["metal_mid"], P["shadow"], pts,
                                width=4, seed=75, wobble=1.4)
                NS._doodle_poly(surface, P["metal_light"], None,
                                [(bx - 9, by - 2), (bx + 4, by - 5),
                                 (bx + 2, by + 2), (bx - 8, by + 3)],
                                width=0)
                for i in range(3):
                    NS._doodle_dot(surface, P["metal_shine"],
                                   [(bx - 6 + i * 6, by + 6)], 1)

'''

# ── HEAD ────────────────────────────────────────────────────────────
HEAD = '''    def _draw_khalros_head(surface, cx, cy, facing, phase, action="idle",
                           rage=False, beard_lag=0.0, ap=0.0):
        """Kepala barbar doodle: helm bertanduk + mata nyala + janggut."""
        NS = _NS_khalros
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        growl = 1.0 if action == "attack" else (0.6 if rage else 0.0)
        tilt = -2 if action == "attack" else 0
        ey = cy + tilt

        # leher doodle
        NS._doodle_poly(surface, P["skin_dark"], P["shadow"],
                        [(cx - 9, ey + 8), (cx + 9, ey + 8),
                         (cx + 11, ey + 18), (cx - 11, ey + 18)],
                        width=3, seed=78, wobble=0.8)
        # tengkorak doodle (blok flat)
        skull = [(cx - 13 * f, ey - 10), (cx + 13 * f, ey - 12),
                 (cx + 15 * f, ey - 1), (cx + 9 * f, ey + 11),
                 (cx - 7 * f, ey + 13), (cx - 14 * f, ey + 2)]
        NS._doodle_poly(surface, P["skin_mid"], P["shadow"], skull,
                        width=4, seed=79, wobble=1.3)
        NS._doodle_poly(surface, P["skin_light"], None,
                        [(cx - 10 * f, ey - 7), (cx + 7 * f, ey - 9),
                         (cx + 5 * f, ey + 2), (cx - 9 * f, ey + 3)],
                        width=0)
        # rahang + geretan gigi
        jaw_drop = int(1 + growl * 2)
        NS._doodle_poly(surface, P["skin_darkest"], P["shadow"],
                        [(cx + 2 * f, ey + 6), (cx + 13 * f, ey + 4),
                         (cx + 12 * f, ey + 10 + jaw_drop),
                         (cx + 2 * f, ey + 12 + jaw_drop)],
                        width=3, seed=80)
        for i in range(2):
            tx = cx + (4 + i * 6) * f
            NS._doodle_poly(surface, P["bone_light"], P["shadow"],
                            [(tx, ey + 6), (tx + 2 * f, ey + 6),
                             (tx + f, ey + 10)], width=1, seed=81 + i)
        # kumis doodle
        NS._doodle_poly(surface, P["hair_mid"], P["shadow"],
                        [(cx + 6 * f, ey + 1), (cx + 17 * f, ey + 2),
                         (cx + 14 * f, ey + 7), (cx + 5 * f, ey + 5)],
                        width=3, seed=83)
        # janggut berkepang (blok + arsir)
        bL = beard_lag
        beard = [(cx + 1 * f, ey + 9), (cx + 12 * f, ey + 13),
                 (cx + 9 * f + bL, ey + 23),
                 (cx + 2 * f + bL * 1.4, ey + 31),
                 (cx - 7 * f + bL * 1.2, ey + 25),
                 (cx - 10 * f, ey + 13)]
        NS._doodle_poly(surface, P["hair_dark"], P["shadow"], beard,
                        width=4, seed=84, wobble=1.3)
        NS._doodle_hatch(surface, P["hair_mid"], beard, spacing=6,
                         angle=0.6, alpha=110)
        NS._doodle_dot(surface, P["gold_light"],
                       [(cx + 2 * f + bL * 1.2, ey + 29)], 2)
        # mata nyala di celah helm
        eye_x, eye_y = cx + 9 * f, ey - 3
        blink = int(phase * 1.55) % 13 == 0 and not growl
        if blink:
            NS._doodle_line(surface, P["shadow"],
                            [(eye_x - 3, eye_y), (eye_x + 3, eye_y)],
                            2, seed=85)
        else:
            col = P["eye_hot"] if (growl or rage) else P["eye_bright"]
            NS._doodle_dot(surface, col, [(eye_x, eye_y)], 4)
            NS._doodle_dot(surface, P["fire_glow"], [(eye_x - 1, eye_y - 1)],
                           2)
        # helm doodle
        NS._draw_helm(surface, cx, ey, f, phase, action=action, rage=rage)

'''

# ── HELM ────────────────────────────────────────────────────────────
HELM = '''    def _draw_helm(surface, cx, cy, facing=1, phase=0.0, action="idle",
                   rage=False):
        """Helm doodle bertanduk babi: kubah baja + dua taring melengkung."""
        NS = _NS_khalros
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        crown = cy - 10
        # kubah baja doodle
        dome = [(cx - 14, crown + 2), (cx - 10, crown - 7),
                (cx, crown - 10), (cx + 10, crown - 7),
                (cx + 14, crown + 2), (cx + 12, crown + 7),
                (cx - 12, crown + 7)]
        NS._doodle_poly(surface, P["metal_mid"], P["shadow"], dome,
                        width=4, seed=87, wobble=1.3)
        NS._doodle_poly(surface, P["metal_light"], None,
                        [(cx - 9, crown - 2), (cx - 1, crown - 7),
                         (cx - 2, crown + 4), (cx - 8, crown + 4)],
                        width=0)
        # palang tengah + rivet
        NS._doodle_line(surface, P["metal_darkest"],
                        [(cx, crown - 8), (cx, crown + 6)], 3, seed=88)
        NS._doodle_dot(surface, P["gold_light"],
                       [(cx - 10 + i * 5, crown + 5) for i in range(5)], 1)
        # linggis hidung
        NS._doodle_poly(surface, P["metal_dark"], P["shadow"],
                        [(cx + 8 * f, crown + 5), (cx + 15 * f, crown + 6),
                         (cx + 14 * f, crown + 14), (cx + 8 * f, crown + 12)],
                        width=2, seed=89)
        # dua taring babi (tanduk) doodle
        for sgn in (-1, 1):
            bx = cx + sgn * 12
            by = crown - 2
            horn = [(bx - sgn * 3, by + 3), (bx + sgn * 11, by - 10),
                    (bx + sgn * 18, by - 23), (bx + sgn * 22, by - 21),
                    (bx + sgn * 15, by - 6), (bx + sgn * 4, by + 6)]
            NS._doodle_poly(surface, P["bone_mid"], P["shadow"], horn,
                            width=4, seed=90 + sgn, wobble=1.4)
            NS._doodle_poly(surface, P["bone_light"], None,
                            [(bx + sgn * 1, by), (bx + sgn * 12, by - 11),
                             (bx + sgn * 16, by - 19),
                             (bx + sgn * 13, by - 7), (bx + sgn * 3, by + 2)],
                            width=0)
            NS._doodle_line(surface, P["bone_darkest"],
                            [(bx + sgn * 4, by - 2),
                             (bx + sgn * 12, by - 15)], 2,
                            seed=92 + sgn, wobble=0.7)
        # bulu elang di punggungan bergoyang
        sway = math.sin(phase * 1.4) * 2
        NS._doodle_line(surface, P["hawk_dark"],
                        [(cx, crown - 8), (cx - 10 * f + sway,
                                           crown - 22)], 4, seed=94,
                        wobble=0.8)
        NS._doodle_poly(surface, P["hawk_light"], None,
                        [(cx - 2 * f + sway, crown - 12),
                         (cx - 11 * f + sway * 1.4, crown - 24),
                         (cx - 16 * f + sway * 1.5, crown - 18)],
                        width=0)

'''

for name, body in (("_draw_beast_cape", CAPE), ("_draw_hawk_companion", HAWK),
                   ("_draw_legs", LEGS), ("_draw_loincloth", LOIN),
                   ("_draw_torso", TORSO), ("_draw_shoulders", SHOULDERS),
                   ("_draw_khalros_head", HEAD), ("_draw_helm", HELM)):
    text = replace_fn(text, name, body)

# Tandai idempotent
text = text.replace("    # ===================================================================\n    # ANATOMI (ruang native rig 1.5x)",
                    "    # ===================================================================\n    # ANATOMI DOODLE (ruang native rig 1.5x)  _DOODLE_FLAG_TORSO\n", 1)

with io.open(SRC, "w", encoding="utf-8") as fh:
    fh.write(text)
print("OK: anatomi doodle diganti")
