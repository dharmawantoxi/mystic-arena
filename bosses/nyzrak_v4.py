# ============================================================================
# bosses/nyzrak_v4.py
# ----------------------------------------------------------------------------
# NYZRAK "THE HOLLOW BLIZZARD" — RENDERER v4 (TOTAL REWRITE FROM ZERO).
#
# Mini boss Level 3 / hero lane. Ice wyvern rider (teal/frost/spear).
# 100% prosedural pixel-art: TIDAK ada PNG, sprite sheet, atau
# pygame.image.load. Karakter digambar ke BUFFER PIXEL-ART resolusi rendah
# (art-pixel 1:1, tanpa anti-alias pada badan) lalu di-upscale NEAREST x2
# ke layar: tepi keras, kluster terkontrol, outline 1 art-px.
#
# ── ARSITEKTUR MODULAR ────────────────────────────────────────────────────
#   render_shadow()       contact shadow 2-tone + frost ring (dunia)
#   render_back_wing()    sayap belakang (membrane 4-band + tulang)
#   render_tail()         ekor bersegmen + spatade es
#   render_legs()         kaki belakang gantung
#   render_body()         torso wyvern 5-band + perut + duri + pauldron es
#   render_head()         tengkorak wyvern + moncong + tanduk
#   render_face()         mata oranye, rahang, napas dingin
#   render_rider_cloak()  jubah rider + bulu
#   render_rider_armor()  torso, pauldron es, sabuk
#   render_rider_head()   hood + wajah + mata menyala
#   render_weapon()       tombak es (poros baja + mata kristal)
#   render_front_wing()   sayap depan (lebih terang)
#   render_highlight()    rim light punggung + kilau es
#   render_outline()      outline 1 art-px lewat mask 8 arah
#   render_hit_flash()    flash siluet saat kena damage
#   render_status()       overlay buff (rim es)
#   render_dissolve()     erosi alpha (death / spawn)
#
# ── ANIMASI (delta-time) ──────────────────────────────────────────────────
#   IDLE/WALK/RUN/ATTACK/SWING/SKILL/HURT/SPAWN/VICTORY/DEATH
#   _update_attack_anim = sumber kebenaran serangan (timer simulasi + dt).
#   Pose solver menambah squash/stretch, lag sayap/ekor, bob napas.
#
# ── KONTRAK YANG TIDAK BERUBAH ────────────────────────────────────────────
#   * draw_nyzrak / draw_boss entry; PIXEL=2, RIG_SIZE=110, GROUND_DY=55.
#   * _NyzAnimController, ATTACK_PHASES, ATTACK_ACTIVE, ATTACK_RELEASE.
#   * SKILL_DUR q/w/e/r = 50/50/70/90 (sinkron AI + nyzrak_fx).
#   * _spear_pose_geom / _spear_state / _draw_swing_arc (tes arc).
#   * PALETTE keys lama (disinkronkan heroes/nyzrak_fx.P).
#   * atribut _nyz_* dipertahankan.
# ============================================================================

import math
import random

import pygame

# ----------------------------------------------------------------------------
# 1. GEOMETRI BUFFER PIXEL-ART
# ----------------------------------------------------------------------------
AW, AH = 110, 110
AX, AY = 55, 55
PX = 2

HAS_MASK = hasattr(pygame, "mask")
HAS_PXARRAY = hasattr(pygame, "PixelArray")
HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")


# ============================================================================
# 2. PALETTE — wyvern teal + es + jubah ungu + tombak (SEMUA key lama)
# ============================================================================
PALETTE = {
    # Wyvern body - teal/cyan
    "wy_darkest":     (5,   30,  40),
    "wy_dark":        (18,  70,  90),
    "wy_mid":         (45, 135, 155),
    "wy_light":       (95, 190, 210),
    "wy_high":        (155, 225, 235),
    "wy_shine":       (215, 245, 250),

    # Wyvern belly (lighter)
    "belly_dark":     (85, 140, 155),
    "belly_mid":      (140, 195, 210),
    "belly_light":    (200, 235, 245),

    # Wing membrane (blue-purple)
    "wing_darkest":   (18,  20,  55),
    "wing_dark":      (45,  55, 115),
    "wing_mid":       (85, 100, 175),
    "wing_light":     (140, 165, 220),

    # Rider - purple/blue robe
    "robe_darkest":   (25,  20,  55),
    "robe_dark":      (55,  50, 105),
    "robe_mid":       (95,  90, 155),
    "robe_light":     (150, 145, 200),
    "robe_high":      (200, 195, 235),

    # Fur trim (white)
    "fur_dark":       (155, 165, 185),
    "fur_mid":        (210, 220, 235),
    "fur_light":      (245, 250, 255),

    # Rider skin (fair)
    "skin_dark":      (185, 145, 130),
    "skin_mid":       (230, 195, 175),
    "skin_light":     (250, 225, 210),

    # Hair (blonde/white)
    "hair_dark":      (185, 155, 100),
    "hair_mid":       (225, 200, 145),
    "hair_light":     (250, 235, 190),

    # Ice / crystal
    "ice_darkest":    (8,   35,  75),
    "ice_dark":       (30,  85, 155),
    "ice_mid":        (75, 155, 220),
    "ice_light":      (150, 210, 245),
    "ice_bright":     (200, 235, 250),
    "ice_hot":        (230, 245, 255),
    "ice_pure":       (250, 253, 255),

    # Purple frost (Q skill)
    "frost_darkest":  (25,  10,  60),
    "frost_dark":     (65,  30, 130),
    "frost_mid":      (125, 75, 200),
    "frost_light":    (175, 130, 240),
    "frost_bright":   (215, 180, 255),
    "frost_hot":      (240, 220, 255),

    # Metal (spear/armor)
    "metal_darkest":  (18,  18,  25),
    "metal_dark":     (48,  55,  70),
    "metal_mid":      (105, 115, 135),
    "metal_light":    (170, 180, 200),
    "metal_shine":    (225, 230, 245),

    # Gold accents
    "gold_dark":      (140, 105,  30),
    "gold_mid":       (200, 165,  60),
    "gold_light":     (240, 210, 110),

    # Eyes
    "eye_dark":       (10,  30,  60),
    "eye_bright":     (140, 210, 255),
    "eye_hot":        (220, 240, 255),

    # Wyvern eye (orange/red - fierce)
    "wy_eye_dark":    (85,  25,  10),
    "wy_eye_bright":  (255, 130,  40),
    "wy_eye_hot":     (255, 210, 120),

    # Teeth
    "bone_dark":      (155, 145, 115),
    "bone_light":     (240, 230, 200),

    # Misc / outline
    "outline":        (3,   5,  10),
    "shadow":         (0,   0,   0),
    "shadow_deep":    (3,   5,  10),
    "white":          (255, 255, 255),
}

_P = PALETTE

_RAMP_W = {
    2: (0.55, 0.45),
    3: (0.30, 0.45, 0.25),
    4: (0.24, 0.34, 0.26, 0.16),
    5: (0.18, 0.26, 0.26, 0.18, 0.12),
}


# ============================================================================
# 3. PIXEL PRIMITIVES — integer, tanpa anti-alias pada badan
# ============================================================================
def px_rect(surf, color, x, y, w, h):
    if w <= 0 or h <= 0:
        return
    surf.fill(color, (int(x), int(y), int(w), int(h)))


def px_set(surf, color, x, y):
    x = int(x)
    y = int(y)
    sw, sh = surf.get_size()
    if 0 <= x < sw and 0 <= y < sh:
        surf.set_at((x, y), color)


def px_line(surf, color, x0, y0, x1, y1, w=1):
    pygame.draw.line(surf, color, (int(x0), int(y0)), (int(x1), int(y1)),
                     max(1, int(w)))


def px_poly(surf, color, pts):
    if len(pts) < 3:
        return
    pygame.draw.polygon(surf, color, [(int(p[0]), int(p[1])) for p in pts])


def px_circle(surf, color, cx, cy, r):
    if r <= 0:
        return
    pygame.draw.circle(surf, color, (int(cx), int(cy)), int(r))


def px_ellipse(surf, color, rect):
    pygame.draw.ellipse(surf, color,
                        (int(rect[0]), int(rect[1]), int(rect[2]),
                         int(rect[3])))


def px_dither(surf, color, x, y, w, h, phase=0, step=2, masked=False):
    x = int(x)
    y = int(y)
    w = int(w)
    h = int(h)
    sw, sh = surf.get_size()
    if x < 0:
        w += x
        x = 0
    if y < 0:
        h += y
        y = 0
    w = min(w, sw - x)
    h = min(h, sh - y)
    if w <= 0 or h <= 0:
        return
    if masked:
        for yy in range(y, y + h):
            off = ((yy + phase) & 1) * (step // 2)
            for xx in range(x + off, x + w, step):
                if surf.get_at((xx, yy))[3] > 0:
                    surf.set_at((xx, yy), color)
        return
    for yy in range(y, y + h):
        off = ((yy + phase) & 1) * (step // 2)
        for xx in range(x + off, x + w, step):
            surf.set_at((xx, yy), color)


def px_ramp_h(surf, ramp, x0, x1, y, weights=None):
    x0 = int(x0)
    x1 = int(x1)
    width = x1 - x0 + 1
    if width <= 0:
        return
    n = len(ramp)
    wts = weights or _RAMP_W.get(n)
    if wts is None:
        wts = tuple([1.0 / n] * n)
    y = int(y)
    pos = x0
    for i, col in enumerate(ramp):
        if i == n - 1:
            ww = x1 - pos + 1
        else:
            ww = max(1, int(round(width * wts[i])))
            ww = min(ww, x1 - pos + 1)
        if ww <= 0:
            continue
        surf.fill(col, (pos, y, ww, 1))
        pos += ww
        if pos > x1:
            break


# ============================================================================
# 4. POSE struct (hasil solver animasi)
# ============================================================================
class Pose(object):
    __slots__ = (
        "state", "t", "dt", "phase", "ap", "facing",
        "bob", "lean", "sqx", "sqy", "rear", "pitch",
        "flap", "flap_amp", "tail", "legs", "charge",
        "variant", "death", "spawn", "victory",
        "flash", "skill", "skill_p", "hurt_k",
        "head_dx", "head_dy", "mouth", "eye",
        "grip_x", "grip_y", "w_ang", "reach",
        "action",
    )

    def __init__(self):
        self.state = "IDLE"
        self.t = 0.0
        self.dt = 1.0 / 60.0
        self.phase = 0.0
        self.ap = 0.0
        self.facing = 1
        self.bob = 0.0
        self.lean = 0.0
        self.sqx = 1.0
        self.sqy = 1.0
        self.rear = 0.0
        self.pitch = 0.0
        self.flap = 0.0
        self.flap_amp = 0.42
        self.tail = 0.0
        self.legs = 0.0
        self.charge = 0.0
        self.variant = "thrust"
        self.death = 0.0
        self.spawn = 1.0
        self.victory = 0.0
        self.flash = 0.0
        self.skill = None
        self.skill_p = 0.0
        self.hurt_k = 0.0
        self.head_dx = 0.0
        self.head_dy = 0.0
        self.mouth = 0.0
        self.eye = 0.85
        self.grip_x = 7.0
        self.grip_y = -22.0
        self.w_ang = -62.0
        self.reach = 22.0
        self.action = "idle"


# ============================================================================
# 5. EASING
# ============================================================================
def _clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else (hi if v > hi else v)


def _ease_out(t):
    t = _clamp(t)
    return 1.0 - (1.0 - t) * (1.0 - t)


def _ease_in(t):
    t = _clamp(t)
    return t * t


def _ease_in_out(t):
    t = _clamp(t)
    return t * t * (3.0 - 2.0 * t)


def _seg(p, a, b):
    if b <= a:
        return 0.0
    return _clamp((p - a) / (b - a))


def _lerp(a, b, t):
    return a + (b - a) * t


# ============================================================================
# 6. LAYER RENDERERS (koordinat buffer, origin = pusat badan)
# ============================================================================
def render_shadow(surface, x, y, lift=0, phase=0.0):
    """Contact shadow 2-tone + cincin beku (ruang dunia)."""
    P = _P
    k = max(0.12, 1.0 - lift * 0.05)
    sw = int(50 * k)
    sh = max(2, int(8 * k))
    cy = int(y)
    px_ellipse(surface, P["shadow"] + (70,),
               (x - sw - 6, cy - sh // 2 - 2, sw * 2 + 12, sh + 4))
    px_ellipse(surface, P["shadow_deep"] + (140,),
               (x - sw, cy - sh // 2, sw * 2, sh))
    rw = int(sw * 1.15)
    rh = max(3, int(sh * 1.3))
    px_ellipse(surface, P["ice_darkest"] + (110,),
               (x - rw, cy - rh // 2, rw * 2, rh))
    px_ellipse(surface, P["ice_dark"] + (90,),
               (x - rw + 2, cy - rh // 2 + 1, rw * 2 - 4, rh - 2))
    px_ellipse(surface, (0, 0, 0, 0),
               (x - rw + 4, cy - rh // 2 + 2, rw * 2 - 8, rh - 4))
    for i in range(6):
        a = phase * 0.7 + i * 1.047
        fx = int(x + math.cos(a) * rw * 0.9)
        fy = int(cy + math.sin(a) * rh * 0.4)
        px_set(surface, P["ice_mid"] + (180,), fx, fy)
        if i & 1:
            px_set(surface, P["ice_light"] + (200,), fx, fy - 1)


def render_back_wing(art, sx, sy, facing, flap, amp, spread=0.92):
    """Sayap belakang: membrane 4-band gelap + tulang."""
    _wing(art, sx, sy, facing, flap, amp, back=True, spread=spread)


def render_front_wing(art, sx, sy, facing, flap, amp, spread=1.0):
    """Sayap depan: membrane lebih terang + cakar es."""
    _wing(art, sx, sy, facing, flap, amp, back=False, spread=spread)


def _wing(art, sx, sy, facing, flap, amp, back=False, spread=1.0):
    """Sayap layar: ke ATAS+BELAKANG (menuju ekor), bukan menutupi rider.

    Lokal: +x = ke kepala, +y = ke bawah. Jari sayap dx negatif.
    """
    P = _P
    rot = flap * amp * (0.65 if back else 1.0)
    c, s = math.cos(rot), math.sin(rot)
    F = 1 if facing >= 0 else -1

    def pt(dx, dy):
        dx = dx * spread
        rx = dx * c - dy * s
        ry = dx * s + dy * c
        return (int(sx + rx * F), int(sy + ry))

    # Empat jari: puncak hampir vertikal, sisanya ke belakang.
    if back:
        fingers = ((-4, -22), (-14, -12), (-22, 0), (-18, 10))
        mem = (P["wing_darkest"], P["wing_dark"], P["wing_mid"])
        bone, bone_hi = P["wy_darkest"], P["wy_dark"]
    else:
        fingers = ((4, -28), (-8, -16), (-18, -2), (-14, 10))
        mem = (P["wing_darkest"], P["wing_dark"], P["wing_mid"], P["wing_light"])
        bone, bone_hi = P["wy_darkest"], P["wy_mid"]

    root = (int(sx), int(sy))
    tips = [pt(dx, dy) for dx, dy in fingers]
    sc = []
    for i in range(len(fingers) - 1):
        ax, ay = fingers[i]
        bx, by_ = fingers[i + 1]
        sc.append(pt((ax + bx) * 0.5 - 6, (ay + by_) * 0.5 + 3))

    sail = [root]
    for i, t in enumerate(tips):
        sail.append(t)
        if i < len(sc):
            sail.append(sc[i])
    px_poly(art, mem[0], sail)

    # Panel antar-jari (bukan satu blob): tiap selaput 2 nada.
    for i in range(len(tips) - 1):
        mid = ((root[0] * 2 + tips[i][0] + tips[i + 1][0]) // 4,
               (root[1] * 2 + tips[i][1] + tips[i + 1][1]) // 4)
        col = mem[1] if (i & 1) else mem[min(2, len(mem) - 1)]
        px_poly(art, col, [root, tips[i], sc[i], tips[i + 1]])
        px_set(art, mem[1], mid[0], mid[1])

    if not back:
        lead = pt(1, -12)
        px_poly(art, mem[3], [
            root, lead, ((root[0] + lead[0]) // 2, (root[1] + lead[1]) // 2 + 3),
        ])

    for t in tips:
        px_line(art, bone, root[0], root[1], t[0], t[1], 1)
    px_line(art, bone_hi, root[0], root[1], tips[0][0], tips[0][1], 1)

    t1 = tips[0]
    px_poly(art, P["ice_darkest"], [
        t1, (t1[0] + 2 * F, t1[1] - 4), (t1[0] - F, t1[1] + 1),
    ])
    px_set(art, P["ice_hot"], t1[0] + 2 * F, t1[1] - 4)
    px_set(art, P["ice_bright"], t1[0] + F, t1[1] - 2)


def render_tail(art, x, y, facing, wave, death_t):
    """Ekor 7 segmen + spatade es berfaset."""
    P = _P
    px, py = float(x), float(y)
    for i in range(7):
        t = i / 6.0
        curve = math.sin(t * 2.4 + wave * 0.5)
        step = 5.2 - t * 1.8
        px += -facing * step * (0.85 + 0.32 * curve)
        py += step * 0.35 * curve + (step * 0.32 if death_t > 0 else 0.0)
        w = max(2, 7 - i)
        col = P["wy_dark"] if i % 2 else P["wy_darkest"]
        px_rect(art, col, int(px - w // 2), int(py - w // 2), w, w)
        if i in (1, 3):
            px_rect(art, P["wy_mid"], int(px - w // 2), int(py - w // 2) - 1,
                    max(1, w - 1), 1)
        if i == 4:
            px_set(art, P["ice_mid"], int(px), int(py - 2))
    tx, ty = int(px), int(py)
    px_poly(art, P["ice_darkest"], [
        (tx - 4, ty), (tx + 4, ty),
        (tx + 3 * facing, ty - 8), (tx - 2 * facing, ty - 8),
    ])
    px_poly(art, P["ice_dark"], [
        (tx - 2, ty - 1), (tx + 2, ty - 1),
        (tx + facing, ty - 7), (tx - facing, ty - 7),
    ])
    px_poly(art, P["ice_mid"], [
        (tx - 1, ty - 1), (tx + 1, ty - 1), (tx, ty - 6),
    ])
    px_rect(art, P["ice_light"], tx - 1, ty - 7, 1, 4)
    px_set(art, P["ice_pure"], tx + facing, ty - 8)


def render_legs(art, x, y, facing, cycle):
    """Dua kaki belakang: paha + cakar tulang."""
    P = _P
    for side, ph in ((-1, 0.0), (1, math.pi)):
        swing = math.sin(cycle + ph)
        lx = x + side * 5 * facing
        ly = y + int(swing * 2)
        px_rect(art, P["wy_darkest"], lx - 2, ly, 4, 7)
        px_rect(art, P["wy_dark"], lx - 1, ly, 2, 6)
        px_rect(art, P["wy_mid"], lx - 1, ly, 1, 4)
        for c in (-2, 0, 2):
            px_poly(art, P["bone_dark"], [
                (lx + c, ly + 7), (lx + c + 2, ly + 7),
                (lx + c + 1, ly + 10),
            ])
        px_set(art, P["bone_light"], lx, ly + 7)
        px_set(art, P["ice_mid"], lx + facing, ly + 9)


def render_body(art, x, y, facing, pitch, pose=None):
    """Torso wyvern 5-band + perut pelat + duri + pauldron es."""
    P = _P
    sqx = 1.0 if pose is None else float(pose.get("sqx", 1.0))
    rows = [
        (-10, 24, (P["wy_darkest"], P["wy_dark"], P["wy_mid"])),
        (-8,  30, (P["wy_darkest"], P["wy_dark"], P["wy_mid"], P["wy_light"])),
        (-6,  38, (P["wy_darkest"], P["wy_dark"], P["wy_mid"], P["wy_light"])),
        (-4,  42, (P["wy_dark"], P["wy_mid"], P["wy_light"])),
        (-2,  44, (P["wy_dark"], P["wy_mid"], P["wy_light"])),
        (0,   44, (P["wy_mid"], P["belly_dark"], P["belly_mid"])),
        (2,   42, (P["belly_dark"], P["belly_mid"], P["belly_light"])),
        (5,   38, (P["belly_dark"], P["belly_mid"], P["belly_light"])),
        (8,   30, (P["belly_dark"], P["belly_mid"])),
        (11,  20, (P["belly_mid"], P["belly_light"])),
        (13,  12, (P["belly_light"],)),
    ]
    for dy, w, ramp in rows:
        wy = y + dy + int(pitch * (1.0 if dy < 0 else 0.4))
        ww = max(2, int(w * sqx))
        x0 = x - ww // 2 + 2 * facing
        if len(ramp) == 1:
            px_rect(art, ramp[0], x0, wy, ww, 3)
        else:
            for i in range(3):
                px_ramp_h(art, ramp, x0, x0 + ww - 1, wy + i)
    # neck two segments
    px_rect(art, P["wy_darkest"], x + 12 * facing, y - 11, 7, 7)
    px_rect(art, P["wy_dark"], x + 13 * facing, y - 11, 5, 6)
    px_rect(art, P["wy_dark"], x + 16 * facing, y - 16, 7, 7)
    px_rect(art, P["wy_mid"], x + 17 * facing, y - 16, 4, 5)
    px_rect(art, P["wy_light"], x + 18 * facing, y - 16, 2, 3)
    # back spines with ice tips
    for i, dx in enumerate((-18, -12, -6, 0, 6, 12)):
        sxp = x + dx * facing
        syp = y - 10 - int(pitch * 1.2)
        h = 4 - (i % 2)
        px_poly(art, P["wy_darkest"], [
            (sxp - 2, syp + 1), (sxp + 2, syp + 1), (sxp, syp - h),
        ])
        px_set(art, P["wy_light"], sxp, syp - h)
        if i % 2 == 0:
            px_set(art, P["ice_hot"], sxp, syp - h - 1)
    # belly plates
    for i in range(4):
        gy = y + 2 + i * 3
        px_rect(art, P["belly_dark"], x - 13 + 2 * facing, gy, 28, 1)
        px_set(art, P["belly_light"], x + 4 * facing, gy)
    # ice pauldron on shoulder
    px_rect(art, P["ice_darkest"], x - 8 * facing, y - 9, 14, 4)
    px_rect(art, P["ice_dark"], x - 7 * facing, y - 9, 12, 2)
    px_rect(art, P["ice_mid"], x - 6 * facing, y - 9, 6, 1)
    px_set(art, P["ice_bright"], x - 4 * facing, y - 9)
    # sisik punggung: bar 1px (bukan dither mosaik)
    for i, dx in enumerate((-14, -8, -2, 4, 10)):
        px_rect(art, P["wy_darkest"], x + dx * facing, y - 7, 3, 1)


def render_head(art, x, y, facing, phase, action):
    """Tengkorak wyvern chunky: blok + moncong + tanduk tulang/es."""
    P = _P
    F = facing
    px_rect(art, P["wy_darkest"], x - 5 * F, y - 7, 12, 10)
    px_rect(art, P["wy_dark"], x - 4 * F, y - 6, 10, 8)
    px_rect(art, P["wy_mid"], x - 4 * F, y - 6, 5, 4)
    px_rect(art, P["wy_light"], x - 3 * F, y - 6, 3, 2)
    # snout
    px_rect(art, P["wy_darkest"], x + 6 * F, y - 4, 10, 6)
    px_rect(art, P["wy_dark"], x + 6 * F, y - 4, 8, 4)
    px_rect(art, P["wy_mid"], x + 7 * F, y - 4, 4, 2)
    px_set(art, P["wy_light"], x + 8 * F, y - 4)
    # nostril
    px_set(art, P["shadow_deep"], x + 13 * F, y - 2)
    # skull fin
    px_poly(art, P["wing_dark"], [
        (x - 5 * F, y - 6), (x - 11 * F, y - 11), (x - 9 * F, y - 3),
    ])
    px_poly(art, P["wing_mid"], [
        (x - 5 * F, y - 6), (x - 10 * F, y - 10), (x - 8 * F, y - 4),
    ])
    # twin horns
    for side in (0, 3):
        hx = x + (side - 1) * F
        px_line(art, P["bone_dark"], hx, y - 7, hx - 4 * F, y - 16, 2)
        px_line(art, P["bone_light"], hx, y - 7, hx - 3 * F, y - 14, 1)
        px_set(art, P["ice_hot"], hx - 4 * F, y - 17)
        px_set(art, P["ice_bright"], hx - 3 * F, y - 15)


def render_face(art, x, y, facing, phase, action):
    """Mata oranye garang, rahang, taring, napas dingin."""
    P = _P
    F = facing
    open_j = 4 if (action == "attack" or str(action).startswith("cast")) else 2
    px_poly(art, P["shadow_deep"], [
        (x + 6 * F, y + 2), (x + 14 * F, y + 2),
        (x + 13 * F, y + 2 + open_j), (x + 6 * F, y + 3),
    ])
    px_poly(art, P["wy_darkest"], [
        (x + 6 * F, y + 2 + open_j), (x + 14 * F, y + 2 + open_j),
        (x + 14 * F, y + 5 + open_j), (x + 7 * F, y + 5 + open_j),
    ])
    for tx in (8, 11):
        px_poly(art, P["bone_light"], [
            (x + tx * F, y + 2), (x + (tx + 1) * F, y + 2),
            (x + (tx + 1) * F, y + 5),
        ])
    bp = int(math.sin(phase * 3.0) * 1.2)
    px_rect(art, P["ice_light"], x + 15 * F, y + bp, 2, 2)
    px_set(art, P["ice_hot"], x + 17 * F, y + bp + 1)
    # eye
    px_rect(art, P["wy_eye_dark"], x + F, y - 5, 4, 3)
    glow = 0.6 + 0.4 * math.sin(phase * 2.2)
    px_rect(art, P["wy_eye_bright"] if glow > 0.55 else P["wy_eye_dark"],
            x + 2 * F, y - 4, 2, 1)
    px_set(art, P["wy_eye_hot"], x + 2 * F, y - 4)
    px_rect(art, P["wy_darkest"], x + F, y - 7, 7, 1)  # brow


def render_rider_cloak(art, rx, ry, facing):
    """Jubah bawah + bulu tepi."""
    P = _P
    F = facing
    px_poly(art, P["robe_darkest"], [
        (rx - 8 * F, ry - 4), (rx + 8 * F, ry - 4),
        (rx + 11 * F, ry + 9), (rx + 4 * F, ry + 13),
        (rx - 4 * F, ry + 13), (rx - 11 * F, ry + 9),
    ])
    px_poly(art, P["robe_dark"], [
        (rx - 6 * F, ry - 3), (rx + 6 * F, ry - 3),
        (rx + 8 * F, ry + 8), (rx - 8 * F, ry + 8),
    ])
    px_poly(art, P["robe_mid"], [
        (rx - 4 * F, ry - 2), (rx + 4 * F, ry - 2),
        (rx + 5 * F, ry + 6), (rx - 5 * F, ry + 6),
    ])
    for i in range(-3, 4):
        px_rect(art, P["fur_dark"], rx + i * 3 * F - 1, ry + 11, 2, 2)
        px_rect(art, P["fur_mid"], rx + i * 3 * F - 1, ry + 10, 2, 1)
        if i % 2 == 0:
            px_set(art, P["fur_light"], rx + i * 3 * F, ry + 10)


def render_rider_armor(art, rx, ry, facing):
    """Torso, pauldron es, kerah bulu, sabuk + permata."""
    P = _P
    F = facing
    px_rect(art, P["robe_darkest"], rx - 5 * F, ry - 13, 11, 10)
    px_rect(art, P["robe_dark"], rx - 4 * F, ry - 12, 9, 8)
    px_rect(art, P["robe_mid"], rx - 3 * F, ry - 12, 6, 5)
    px_rect(art, P["robe_light"], rx - 2 * F, ry - 12, 3, 2)
    # ice pauldrons
    px_rect(art, P["ice_darkest"], rx - 7 * F, ry - 14, 6, 4)
    px_rect(art, P["ice_dark"], rx - 6 * F, ry - 14, 4, 2)
    px_rect(art, P["ice_mid"], rx - 6 * F, ry - 14, 2, 1)
    px_rect(art, P["ice_darkest"], rx + 2 * F, ry - 14, 5, 4)
    px_rect(art, P["ice_dark"], rx + 2 * F, ry - 14, 3, 2)
    px_set(art, P["ice_bright"], rx + 3 * F, ry - 14)
    # fur collar
    px_rect(art, P["fur_dark"], rx - 5 * F, ry - 15, 11, 3)
    px_rect(art, P["fur_mid"], rx - 4 * F, ry - 15, 9, 1)
    px_rect(art, P["fur_light"], rx - 3 * F, ry - 16, 5, 1)
    # belt + ice gem
    px_rect(art, P["metal_darkest"], rx - 5 * F, ry - 4, 11, 2)
    px_rect(art, P["metal_dark"], rx - 4 * F, ry - 4, 9, 1)
    px_rect(art, P["gold_mid"], rx - 5 * F, ry - 4, 2, 2)
    px_rect(art, P["ice_dark"], rx - F, ry - 5, 3, 3)
    px_set(art, P["ice_bright"], rx - F, ry - 5)


def render_rider_head(art, rx, ry, facing, phase):
    """Hood + void wajah + mata menyala + rambut."""
    P = _P
    F = facing
    hyy = ry - 21
    px_poly(art, P["robe_darkest"], [
        (rx - 5 * F, hyy + 5), (rx + 5 * F, hyy + 5),
        (rx + 5 * F, hyy - 3), (rx + 2 * F, hyy - 7),
        (rx - 2 * F, hyy - 7), (rx - 5 * F, hyy - 3),
    ])
    px_poly(art, P["robe_dark"], [
        (rx - 3 * F, hyy + 4), (rx + 3 * F, hyy + 4),
        (rx + 3 * F, hyy - 2), (rx + F, hyy - 6),
        (rx - F, hyy - 6), (rx - 3 * F, hyy - 2),
    ])
    px_rect(art, P["shadow_deep"], rx + F, hyy - 2, 3, 5)
    if (int(phase * 2.0) % 7) != 0:
        px_rect(art, P["eye_bright"], rx + F, hyy - 1, 2, 1)
    px_set(art, P["eye_hot"], rx + 2 * F, hyy - 1)
    px_rect(art, P["hair_dark"], rx - 2 * F, hyy + 3, 2, 4)
    px_rect(art, P["hair_mid"], rx - 2 * F, hyy + 3, 1, 3)
    px_set(art, P["ice_mid"], rx - F, hyy - 6)


def render_rider_arms(art, rx, ry, facing, phase, action, grip):
    """Lengan tombak 2-segmen + lengan depan (cast orb)."""
    P = _P
    F = facing
    shx, shy = rx + 4 * F, ry - 11
    hx, hy = grip
    ex = shx + (hx - shx) * 0.45
    ey = shy + (hy - shy) * 0.45 - 2
    px_line(art, P["robe_darkest"], shx, shy, ex, ey, 3)
    px_line(art, P["robe_dark"], shx, shy, ex, ey, 2)
    px_line(art, P["robe_darkest"], ex, ey, hx, hy, 3)
    px_line(art, P["robe_dark"], ex, ey, hx, hy, 2)
    px_circle(art, P["robe_darkest"], hx + 1, hy + 1, 2)
    px_circle(art, P["skin_dark"], hx, hy, 2)
    px_set(art, P["skin_mid"], hx - 1, hy - 1)
    if str(action).startswith("cast"):
        fx2, fy2 = rx + 6 * F, ry - 9
    else:
        fx2 = rx - 5 * F
        fy2 = ry - 2 + int(math.sin(phase * 1.1))
    px_line(art, P["robe_dark"], rx - 3 * F, ry - 10, fx2, fy2, 2)
    px_line(art, P["robe_mid"], rx - 3 * F, ry - 10, fx2, fy2, 1)
    px_circle(art, P["skin_dark"], fx2, fy2, 2)
    px_set(art, P["skin_mid"], fx2 - 1, fy2 - 1)
    if str(action).startswith("cast"):
        pk = 0.6 + 0.4 * math.sin(phase * 5)
        r = max(1, int(2 * pk))
        col = P["frost_bright"] if action == "cast_q" else P["ice_bright"]
        dark = P["frost_dark"] if action == "cast_q" else P["ice_dark"]
        px_circle(art, dark, fx2 + F, fy2 - 1, r + 1)
        px_circle(art, col, fx2 + F, fy2 - 1, r)
        px_set(art, P["ice_pure"], fx2 + F, fy2 - 1)


def render_weapon(art, gx, gy, facing, angle, reach, charge):
    """Tombak es: poros 2px, cincin emas, mata kristal 4 faset."""
    P = _P
    F = facing
    dx, dy = math.cos(angle) * F, math.sin(angle)
    tipx, tipy = gx + dx * reach, gy + dy * reach
    nx, ny = -dy, dx
    px_poly(art, P["metal_darkest"], [
        (int(gx - nx), int(gy - ny)), (int(tipx - nx), int(tipy - ny)),
        (int(tipx + nx), int(tipy + ny)), (int(gx + nx), int(gy + ny)),
    ])
    px_line(art, P["metal_dark"], gx, gy, tipx, tipy, 1)
    px_line(art, P["metal_light"], gx - nx, gy - ny, tipx - nx, tipy - ny, 1)
    # pommel
    px_circle(art, P["gold_mid"], gx - dx * 2, gy - dy * 2, 2)
    px_set(art, P["gold_light"], int(gx - dx * 2), int(gy - dy * 2 - 1))
    for t in (0.28, 0.55, 0.78):
        rxp, ryp = gx + dx * reach * t, gy + dy * reach * t
        px_line(art, P["gold_mid"], rxp - nx * 2, ryp - ny * 2,
                rxp + nx * 2, ryp + ny * 2, 2)
        px_set(art, P["gold_light"], int(rxp) - 1, int(ryp) - 1)
    bx, by = tipx, tipy
    p_tip = (int(bx + dx * 10), int(by + dy * 10))
    p_up = (int(bx - nx * 5 + dx * 2), int(by - ny * 5 + dy * 2))
    p_dn = (int(bx + nx * 5 + dx * 2), int(by + ny * 5 + dy * 2))
    p_base = (int(bx - dx * 2), int(by - dy * 2))
    px_poly(art, P["ice_darkest"], [p_base, p_up, p_tip, p_dn])
    px_poly(art, P["ice_dark"], [
        p_base,
        (p_up[0] - (p_up[0] - p_tip[0]) // 3,
         p_up[1] - (p_up[1] - p_tip[1]) // 3),
        (int(p_tip[0] - dx), int(p_tip[1] - dy)),
        (p_dn[0] - (p_dn[0] - p_tip[0]) // 3,
         p_dn[1] - (p_dn[1] - p_tip[1]) // 3),
    ])
    px_poly(art, P["ice_mid"], [
        p_base, ((p_up[0] + p_tip[0]) // 2, (p_up[1] + p_tip[1]) // 2), p_tip,
    ])
    px_set(art, P["ice_bright"], int(bx + dx * 3), int(by + dy * 3))
    px_set(art, P["ice_pure"], p_tip[0], p_tip[1])
    if charge > 0.05:
        r = 2 + int(charge * 3)
        px_circle(art, P["ice_bright"], int(tipx), int(tipy), r)
        px_circle(art, P["ice_hot"], int(tipx), int(tipy), max(1, r - 2))


def render_highlight(art, x, y, facing, phase):
    """Rim cahaya dingin di punggung + kilau pauldron."""
    P = _P
    F = facing
    tw = 0.6 + 0.4 * math.sin(phase * 1.7)
    for i, (dx, dy) in enumerate(((-20, -9), (-14, -11), (-8, -12),
                                  (-2, -12), (4, -11), (10, -9))):
        if (i % 2) == 0 or tw > 0.75:
            px_rect(art, P["wy_high"] if tw > 0.75 else P["wy_light"],
                    x + dx * F, y + dy, 2, 1)
    px_rect(art, P["ice_light"], x - 5 * F, y - 9, 3, 1)
    px_set(art, P["ice_pure"], x - 4 * F, y - 9)


def render_outline(art, color=None):
    """Outline 1 art-px lewat mask 8 arah. Return mask (untuk flash)."""
    if not HAS_MASK:
        return None
    # Hitam murni: konvensi level3 (tes outline menghitung piksel (0,0,0)).
    col = color or (_P["shadow"] + (255,))
    m = pygame.mask.from_surface(art, 40)
    sil = m.to_surface(setcolor=col, unsetcolor=(0, 0, 0, 0))
    base = pygame.Surface(art.get_size(), pygame.SRCALPHA)
    # 4 arah: outline 1 art-px tanpa penebalan diagonal (halo "sensor").
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        base.blit(sil, (dx, dy))
    base.blit(art, (0, 0))
    art.blit(base, (0, 0))
    return m


def render_hit_flash(art, mask, amount):
    if mask is None or amount <= 0.02:
        return
    a = int(150 * min(1.0, amount))
    flash = mask.to_surface(setcolor=(230, 245, 255, a),
                            unsetcolor=(0, 0, 0, 0))
    art.blit(flash, (0, 0))


def render_status(art, mask, amount=0.0, color=None):
    if mask is None or amount <= 0.05:
        return
    col = color or _P["ice_bright"]
    a = int(70 * amount)
    tint = mask.to_surface(setcolor=col + (a,), unsetcolor=(0, 0, 0, 0))
    art.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)


def render_dissolve(art, k, seed=7):
    if k <= 0.0 or not HAS_PXARRAY:
        return
    k = min(1.0, k)
    h = art.get_height()
    cut = int(h * k)
    if cut <= 0:
        return
    rnd = random.Random(seed)
    arr = pygame.PixelArray(art)
    try:
        for yy in range(0, min(h, cut + 5)):
            if yy < cut:
                fade = 1.0
            else:
                fade = 1.0 - (yy - cut) / 5.0
            if fade <= 0.05:
                continue
            step = 1 if fade > 0.7 else (2 if fade > 0.35 else 4)
            off = rnd.randint(0, step - 1)
            arr[off::step, yy] = 0
    finally:
        del arr


class _NS_nyzrak:
    """Namespace nyzrak v4 — pixel-art buffer, dt pose, modular layers."""

    # ── Buffer cache (dibangun lazy, dipakai ulang antar frame) ──────
    _body_buf = None        # canvas komposit 220x220 (outline+lighting)
    _rig_buf = None         # canvas rig low-res (pixel-art asli)
    _scale_buf = None       # target scale 2x (dipakai ulang, tanpa alloc)
    _flash_buf = None       # buffer hurt-flash
    _record_shadow = None   # rect bayangan -> dikecualikan dari flash
    _shadow_cache = None
    _aura_cache = None
    _ground_cache = None
    _mist_cache = None

    #: Ukuran "fat pixel" — rig digambar setengah resolusi lalu di-scale.
    PIXEL = 2
    RIG_SIZE = 110          # sisi canvas rig low-res
    GROUND_DY = 55          # jangkar -> garis tanah (piksel layar)
    LIFT = 4                # tinggi hover wyvern di atas bayangan

    #: Penanda varian serangan aktif untuk _spear_pose_geom (stateless).
    _pose_variant_now = "thrust"

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # PALETTE — winter wyvern (satu sumber kebenaran warna untuk rig,
    # FX canvas, dan heroes/nyzrak_fx.py via _sync_palette)
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Wyvern body - teal/cyan
        "wy_darkest":     (5,   30,  40),
        "wy_dark":        (18,  70,  90),
        "wy_mid":         (45, 135, 155),
        "wy_light":       (95, 190, 210),
        "wy_high":        (155, 225, 235),
        "wy_shine":       (215, 245, 250),

        # Wyvern belly (lighter)
        "belly_dark":     (85, 140, 155),
        "belly_mid":      (140, 195, 210),
        "belly_light":    (200, 235, 245),

        # Wing membrane (blue-purple)
        "wing_darkest":   (18,  20,  55),
        "wing_dark":      (45,  55, 115),
        "wing_mid":       (85, 100, 175),
        "wing_light":     (140, 165, 220),

        # Rider - purple/blue robe
        "robe_darkest":   (25,  20,  55),
        "robe_dark":      (55,  50, 105),
        "robe_mid":       (95,  90, 155),
        "robe_light":     (150, 145, 200),
        "robe_high":      (200, 195, 235),

        # Fur trim (white)
        "fur_dark":       (155, 165, 185),
        "fur_mid":        (210, 220, 235),
        "fur_light":      (245, 250, 255),

        # Rider skin (fair)
        "skin_dark":      (185, 145, 130),
        "skin_mid":       (230, 195, 175),
        "skin_light":     (250, 225, 210),

        # Hair (blonde/white)
        "hair_dark":      (185, 155, 100),
        "hair_mid":       (225, 200, 145),
        "hair_light":     (250, 235, 190),

        # Ice / crystal
        "ice_darkest":    (8,   35,  75),
        "ice_dark":       (30,  85, 155),
        "ice_mid":        (75, 155, 220),
        "ice_light":      (150, 210, 245),
        "ice_bright":     (200, 235, 250),
        "ice_hot":        (230, 245, 255),
        "ice_pure":       (250, 253, 255),

        # Purple frost (Q skill)
        "frost_darkest":  (25,  10,  60),
        "frost_dark":     (65,  30, 130),
        "frost_mid":      (125, 75, 200),
        "frost_light":    (175, 130, 240),
        "frost_bright":   (215, 180, 255),
        "frost_hot":      (240, 220, 255),

        # Metal (spear/armor)
        "metal_darkest":  (18,  18,  25),
        "metal_dark":     (48,  55,  70),
        "metal_mid":      (105, 115, 135),
        "metal_light":    (170, 180, 200),
        "metal_shine":    (225, 230, 245),

        # Gold accents (small)
        "gold_mid":       (200, 165,  60),
        "gold_light":     (240, 210, 110),

        # Eyes
        "eye_dark":       (10,  30,  60),
        "eye_bright":     (140, 210, 255),
        "eye_hot":        (220, 240, 255),

        # Wyvern eye (orange/red - fierce)
        "wy_eye_dark":    (85,  25,  10),
        "wy_eye_bright":  (255, 130,  40),
        "wy_eye_hot":     (255, 210, 120),

        # Teeth
        "bone_dark":      (155, 145, 115),
        "bone_light":     (240, 230, 200),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (3,   5,  10),
        "white":          (255, 255, 255),
    }

    # ===================================================================
    # ANIMATION CONTROLLER
    #
    # Pose adalah fungsi MURNI dari atribut simulasi — pipeline hero
    # meng-cache sprite, jadi controller tidak boleh menyimpan state
    # antar-gambar.  "Delta time" = langkah tetap 1/60 s yang sudah
    # diintegrasi game ke boss.pulse (+0.05/step), timer serangan, dan
    # timer skill (frame @60fps).
    # ===================================================================
    STATE_IDLE = "IDLE"
    STATE_WALK = "WALK"
    STATE_RUN = "RUN"
    STATE_ATTACK = "ATTACK"      # varian thrust (ranged)
    STATE_SWING = "SWING"        # varian sweep (melee)
    STATE_CAST = "CAST"
    STATE_SKILL = "SKILL"
    STATE_HIT = "HIT"
    STATE_HURT = "HURT"
    STATE_DEATH = "DEATH"
    STATE_CHARGE = "CHARGE"
    STATE_SPECIAL = "SPECIAL"
    STATE_SPAWN = "SPAWN"
    STATE_VICTORY = "VICTORY"

    #: Prioritas — state bernilai tinggi menang selama durasinya.
    STATE_PRIORITY = {
        "IDLE": 0, "WALK": 10, "RUN": 20, "CHARGE": 45, "CAST": 50,
        "ATTACK": 55, "SWING": 60, "SPECIAL": 65, "SKILL": 70,
        "HIT": 80, "HURT": 90, "SPAWN": 95, "VICTORY": 58,
        "DEATH": 100,
    }

    #: Durasi bingkai (detik) per state untuk frame-index controller.
    FRAME_DUR = {
        "IDLE": 0.125, "WALK": 0.083, "RUN": 0.058, "ATTACK": 0.016,
        "SWING": 0.016, "CAST": 0.10, "SKILL": 0.033, "CHARGE": 0.066,
        "HIT": 0.033, "HURT": 0.10, "DEATH": 0.05, "SPECIAL": 0.033,
    }
    FRAME_COUNT = {"IDLE": 8, "WALK": 8, "RUN": 8}

    #: Timing serangan (progress 0..1).  Jendela ACTIVE = hitbox hidup.
    ATTACK_PHASES = (
        ("anticipation", 0.00, 0.22),   # coil: badan mundur, tombak naik
        ("windup",       0.22, 0.40),   # hold di apex, embun beku mengumpul
        ("swing",        0.40, 0.56),   # sapuan/entakan cepat (aktif)
        ("impact",       0.56, 0.64),   # bingkai benturan + recoil
        ("follow",       0.64, 0.80),   # momentum terbawa melewati target
        ("recovery",     0.80, 1.00),   # kembali ke pose siaga
    )
    #: Jendela hit aktif (inklusif) — dipakai swing hitbox & debug.
    ATTACK_ACTIVE = (0.40, 0.64)
    #: Progres saat proyektil dasar diluncurkan (varian thrust).
    ATTACK_RELEASE = 0.46

    #: Durasi skill (frame @60fps) — identik dengan AI base_boss.
    SKILL_DUR = {"q": 50, "w": 50, "e": 70, "r": 90}

    #: Sub-fase lifecycle skill: cast->charge->release->area->after.
    SKILL_PHASES = (
        ("cast",    0.00, 0.18),
        ("charge",  0.18, 0.38),
        ("release", 0.38, 0.50),
        ("area",    0.50, 0.78),
        ("after",   0.78, 1.00),
    )

    class _NyzAnimController:
        """Controller animasi stateless untuk Nyzrak.

        resolve() memetakan atribut unit -> dict pose.  Tidak ada
        mutasi boss di sini (aman untuk render ter-cache); penulisan
        atribut kerja hanya terjadi di _update_attack_anim /
        _detect_moving yang dipanggil sekali per draw jalur boss.
        """

        #: Transisi yang diizinkan (dokumentasi & debug overlay).
        TRANSITIONS = {
            "IDLE":    {"WALK", "RUN", "ATTACK", "SWING", "CAST", "SKILL",
                        "HIT", "HURT", "DEATH", "CHARGE", "SPECIAL"},
            "WALK":    {"IDLE", "RUN", "ATTACK", "SWING", "CAST", "SKILL",
                        "HIT", "HURT", "DEATH"},
            "RUN":     {"IDLE", "WALK", "ATTACK", "SWING", "CAST", "SKILL",
                        "HIT", "HURT", "DEATH"},
            "CHARGE":  {"SKILL", "CAST", "IDLE", "HIT", "HURT", "DEATH"},
            "CAST":    {"SKILL", "IDLE", "WALK", "HIT", "HURT", "DEATH"},
            "ATTACK":  {"IDLE", "WALK", "RUN", "SWING", "HIT", "DEATH"},
            "SWING":   {"IDLE", "WALK", "RUN", "ATTACK", "HIT", "DEATH"},
            "SPECIAL": {"IDLE", "WALK", "SKILL", "HIT", "DEATH"},
            "SKILL":   {"IDLE", "WALK", "RUN", "HIT", "DEATH"},
            "HIT":     {"IDLE", "WALK", "RUN", "HURT", "DEATH"},
            "HURT":    {"IDLE", "WALK", "HIT", "DEATH"},
            "DEATH":   set(),
            "SPAWN":   {"IDLE", "WALK", "HIT", "HURT", "DEATH"},
            "VICTORY": {"IDLE", "HIT", "DEATH"},
        }

        @classmethod
        def frame_index(cls, state, phase):
            """Index bingkai animasi looping (idle/walk/run)."""
            n = _NS_nyzrak.FRAME_COUNT.get(state, 1)
            dur = max(1e-3, _NS_nyzrak.FRAME_DUR.get(state, 0.1))
            t = (phase * 0.05) / dur          # pulse: +0.05 per 1/60 s
            return int(t * n) % n

        @classmethod
        def attack_stage(cls, ap):
            """(nama_subfase, t_lokal) dari progress serangan 0..1."""
            ap = min(1.0, max(0.0, ap))
            for name, a, b in _NS_nyzrak.ATTACK_PHASES:
                if ap < b:
                    return name, min(1.0, max(0.0, (ap - a) / max(1e-3, b - a)))
            return "recovery", 1.0

        @classmethod
        def attack_active(cls, ap):
            a0, a1 = _NS_nyzrak.ATTACK_ACTIVE
            return a0 <= ap <= a1

        @classmethod
        def skill_stage(cls, t01):
            """(nama_subfase, t_lokal) dari progress skill 0..1."""
            t01 = min(1.0, max(0.0, t01))
            for name, a, b in _NS_nyzrak.SKILL_PHASES:
                if t01 < b:
                    return name, min(1.0, max(0.0, (t01 - a) / max(1e-3, b - a)))
            return "after", 1.0

        @classmethod
        def resolve(cls, boss, moving=False, run=False):
            """Resolve pose saat ini dari atribut sim."""
            phase = float(getattr(boss, "pulse", 0.0) or 0.0)
            ap = min(1.0, max(0.0,
                       float(getattr(boss, "_nyz_attack_progress", 0.0) or 0.0)))
            attack_on = bool(getattr(boss, "_nyz_attack_active", False))
            skill = getattr(boss, "active_skill", None)
            skill_timer = int(getattr(boss, "active_skill_timer", 0) or 0)
            hurt = int(getattr(boss, "hurt_flash_timer", 0) or 0)
            alive = bool(getattr(boss, "alive", True))
            hp = float(getattr(boss, "hp", 1.0) or 0.0)

            if not alive or hp <= 0.0:
                death_t = min(1.0,
                              float(getattr(boss, "_nyz_death_age", 0)) / 60.0)
                return {"state": "DEATH", "action": "death", "phase": phase,
                        "ap": death_t, "skill": None, "skill_t01": 0.0,
                        "stage": "collapse", "death_t": death_t,
                        "spawn_t": 1.0}
            spawn_t = float(getattr(boss, "_nyz_spawn_t", 1.0) or 1.0)
            if 0.0 < spawn_t < 1.0:
                return {"state": "SPAWN", "action": "idle", "phase": phase,
                        "ap": spawn_t, "skill": None, "skill_t01": 0.0,
                        "stage": "rise", "death_t": 0.0, "spawn_t": spawn_t}
            if hurt > 0:
                return {"state": "HIT", "action": "hit", "phase": phase,
                        "ap": min(1.0, hurt / 8.0), "skill": None,
                        "skill_t01": 0.0, "stage": "flinch", "death_t": 0.0}
            if skill in ("q", "w", "e", "r"):
                dur = float(_NS_nyzrak.SKILL_DUR.get(skill, 50))
                t01 = min(1.0, max(0.0, 1.0 - skill_timer / dur))
                stage, _t = cls.skill_stage(t01)
                return {"state": "SKILL", "action": "cast_" + skill,
                        "phase": phase, "ap": t01, "skill": skill,
                        "skill_t01": t01, "stage": stage, "death_t": 0.0}
            if attack_on:
                variant = "sweep" if int(getattr(boss, "_pose_variant", 0) or 0) == 1 else "thrust"
                stage, _t = cls.attack_stage(ap)
                return {"state": "SWING" if variant == "sweep" else "ATTACK",
                        "action": "attack", "phase": phase, "ap": ap,
                        "skill": None, "skill_t01": 0.0, "stage": stage,
                        "death_t": 0.0}
            if moving and run:
                return {"state": "RUN", "action": "run", "phase": phase,
                        "ap": 0.0, "skill": None, "skill_t01": 0.0,
                        "stage": "stride", "death_t": 0.0}
            if moving:
                return {"state": "WALK", "action": "walk", "phase": phase,
                        "ap": 0.0, "skill": None, "skill_t01": 0.0,
                        "stage": "step", "death_t": 0.0}
            if float(getattr(boss, "_nyz_victory_t", 0.0) or 0.0) > 0.05:
                return {"state": "VICTORY", "action": "idle", "phase": phase,
                        "ap": float(getattr(boss, "_nyz_victory_t", 0.0)),
                        "skill": None, "skill_t01": 0.0,
                        "stage": "pose", "death_t": 0.0, "spawn_t": 1.0}
            return {"state": "IDLE", "action": "idle", "phase": phase,
                    "ap": 0.0, "skill": None, "skill_t01": 0.0,
                    "stage": "breathe", "death_t": 0.0, "spawn_t": 1.0}

    # ===================================================================
    # MATEMATIKA EASING & GEOMETRI SERANGAN (arc, bukan teleport)
    # ===================================================================
    @staticmethod
    def _ease_out_cubic(t):
        t = min(1.0, max(0.0, t))
        return 1.0 - (1.0 - t) ** 3

    @staticmethod
    def _ease_in_out(t):
        t = min(1.0, max(0.0, t))
        return t * t * (3.0 - 2.0 * t)

    @staticmethod
    def _seg_t(ap, a, b):
        """t lokal 0..1 di dalam segmen [a, b)."""
        if ap <= a:
            return 0.0
        if ap >= b:
            return 1.0
        return (ap - a) / max(1e-3, b - a)

    @staticmethod
    def _spear_pose_geom(action, ap, phase):
        """Geometri tombak (rig-local, y ke bawah) untuk pose ini.

        Return (angle_deg, reach_px, grip_dx, grip_dy).
        angle 0 = lurus ke depan; negatif = terangkat ke atas.
        """
        NS = _NS_nyzrak
        base_ang, base_reach = -62.0, 22.0
        grip_x, grip_y = 7.0, -22.0

        if action == "attack":
            variant = getattr(NS, "_pose_variant_now", "thrust")
            if variant == "sweep":
                # ── sapuan melee: arc lewat atas lalu menghunjam ──
                if ap < 0.22:            # anticipation
                    t = NS._ease_out_cubic(ap / 0.22)
                    ang = -20.0 - 95.0 * t
                    reach = base_reach + 2.0 * t
                    grip_x = 7.0 - 3.0 * t
                elif ap < 0.40:          # windup: apex + tremor es
                    ang = -115.0 + math.sin(phase * 26.0) * 2.5
                    reach = 24.0
                    grip_x = 4.0
                elif ap < 0.56:          # swing: sapuan cepat (AKTIF)
                    t = NS._ease_out_cubic((ap - 0.40) / 0.16)
                    ang = -115.0 + 155.0 * t
                    reach = 24.0 + 6.0 * t
                    grip_x = 4.0 + 5.0 * t
                elif ap < 0.64:          # impact: recoil
                    t = (ap - 0.56) / 0.08
                    ang = 40.0 - 7.0 * t
                    reach = 30.0 - 1.0 * t
                    grip_x = 9.0
                elif ap < 0.80:          # follow: momentum terbawa
                    t = NS._ease_in_out((ap - 0.64) / 0.16)
                    ang = 33.0 + 10.0 * t
                    reach = 29.0 - 2.0 * t
                    grip_x = 9.0 - 2.0 * t
                else:                    # recovery
                    t = NS._ease_in_out((ap - 0.80) / 0.20)
                    ang = 43.0 + (base_ang - 43.0) * t
                    reach = 27.0 + (base_reach - 27.0) * t
                    grip_x = 7.0
                return ang, reach, grip_x, grip_y
            # ── thrust ranged: tarik -> entak -> tahan -> kembali ──
            if ap < 0.22:
                t = NS._ease_out_cubic(ap / 0.22)
                ang = -62.0 - 28.0 * t
                reach = 22.0 - 6.0 * t
                grip_x = 7.0 - 4.0 * t
            elif ap < 0.40:
                ang = -90.0 + 4.0 * math.sin(phase * 22.0)
                reach = 16.0
                grip_x = 3.0
            elif ap < 0.56:
                t = NS._ease_out_cubic((ap - 0.40) / 0.16)
                ang = -90.0 + 86.0 * t
                reach = 16.0 + 16.0 * t
                grip_x = 3.0 + 7.0 * t
            elif ap < 0.64:
                t = (ap - 0.56) / 0.08
                ang = -4.0 - 3.0 * t
                reach = 32.0 - 1.5 * t
                grip_x = 10.0 - t
            elif ap < 0.80:
                t = (ap - 0.64) / 0.16
                ang = -7.0 - 2.0 * t
                reach = 30.5 - 2.5 * t
                grip_x = 9.0 - t
            else:
                t = NS._ease_in_out((ap - 0.80) / 0.20)
                ang = -9.0 + (base_ang + 9.0) * t
                reach = 28.0 + (base_reach - 28.0) * t
                grip_x = 8.0 - t
            return ang, reach, grip_x, grip_y

        if action == "cast_q":         # Arctic Burn: bidik + recoil
            if ap < 0.38:
                k = NS._ease_out_cubic(ap / 0.38)
                ang = -62.0 + 54.0 * k
                reach = 22.0 + 9.0 * k
                grip_x = 7.0 + 2.0 * k
            else:
                rec = math.sin(min(1.0, (ap - 0.38) / 0.2) * math.pi) * 6.0
                ang = -8.0 + rec * 0.4
                reach = 31.0 - rec * 0.3
                grip_x = 9.0
            return ang, reach, grip_x, grip_y
        if action == "cast_w":         # Splinter Blast: kibasan keluar
            if ap < 0.35:
                t = NS._ease_out_cubic(ap / 0.35)
                ang = -62.0 - 58.0 * t
                reach = 22.0 - 5.0 * t
                grip_x = 7.0 - 4.0 * t
            else:
                t = NS._ease_out_cubic((ap - 0.35) / 0.15)
                ang = -120.0 + 112.0 * t
                reach = 17.0 + 13.0 * t
                grip_x = 3.0 + 6.0 * t
            return ang, reach, grip_x, grip_y
        if action == "cast_e":         # Winter's Curse: angkat tinggi
            if ap < 0.3:
                t = NS._ease_out_cubic(ap / 0.3)
                ang = -62.0 - 48.0 * t
                reach = 22.0 + 3.0 * t
                grip_x = 7.0 + t
            elif ap < 0.5:
                ang = -110.0 + 3.0 * math.sin(phase * 18.0)
                reach = 25.0
                grip_x = 8.0
            else:
                t = NS._ease_in_out((ap - 0.5) / 0.5)
                ang = -110.0 + 48.0 * t
                reach = 25.0 - 3.0 * t
                grip_x = 8.0 - t
            return ang, reach, grip_x, grip_y
        if action == "cast_r":         # Cold Embrace: angkat -> tebar
            if ap < 0.25:
                t = NS._ease_out_cubic(ap / 0.25)
                ang = -62.0 - 38.0 * t
                reach = 22.0 + 2.0 * t
                grip_x = 7.0 + t
            elif ap < 0.42:
                ang = -100.0 - 4.0 * math.sin(phase * 14.0)
                reach = 24.0
                grip_x = 8.0
            elif ap < 0.55:
                t = NS._ease_out_cubic((ap - 0.42) / 0.13)
                ang = -100.0 + 82.0 * t
                reach = 24.0 + 6.0 * t
                grip_x = 8.0 + 2.0 * t
            else:
                t = NS._ease_in_out((ap - 0.55) / 0.45)
                ang = -18.0 + (base_ang + 18.0) * t
                reach = 30.0 + (base_reach - 30.0) * t
                grip_x = 10.0 - 3.0 * t
            return ang, reach, grip_x, grip_y
        if action == "hit":
            flinch = math.sin(min(1.0, ap) * math.pi)
            return (base_ang - 14.0 * flinch,
                    base_reach - 3.0 * flinch,
                    7.0 - 2.0 * flinch, grip_y)
        if action == "death":
            return base_ang + 55.0, base_reach - 6.0, 5.0, -18.0
        if action == "run":
            return (base_ang + 12.0 + math.sin(phase * 2.4) * 7.0,
                    base_reach + 1.0, 8.0, -21.0)
        if action == "walk":
            return (base_ang + math.sin(phase * 1.6) * 2.0,
                    base_reach, 7.0, -22.0)
        # idle: napas + ayunan senjata halus
        return base_ang + math.sin(phase * 0.9) * 3.0, base_reach, 7.0, -22.0

    # ===================================================================
    # RIG POSE — seluruh parameter gerak satu bingkai rig
    # ===================================================================
    @staticmethod
    def _rig_pose(action, phase, ap):
        """Hitung pose rig (unit rig low-res, y ke bawah)."""
        NS = _NS_nyzrak
        pose = {
            "bob": 0, "lean": 0, "pitch": 0, "rear": 0.0,
            "flap": math.sin(phase * 1.3), "flap_amp": 0.28,
            "tail": phase * 0.8, "legs": phase * 2.2, "charge": 0.0,
            "variant": "thrust", "death_t": 0.0,
            "sqx": 1.0, "sqy": 1.0,
        }
        breathe = math.sin(phase * 0.8)
        pose["sqx"] = 1.0 + breathe * 0.012
        pose["sqy"] = 1.0 - breathe * 0.016
        if action == "idle":
            pose["bob"] = math.sin(phase * 0.8) * 1.2      # breathing
            pose["tail"] = phase * 0.6
        elif action == "walk":
            pose["bob"] = math.sin(phase * 1.2) * 1.6
            pose["flap"] = math.sin(phase * 2.1)
            pose["flap_amp"] = 0.38
            pose["tail"] = phase * 1.1
            pose["legs"] = phase * 3.0
        elif action == "run":
            pose["bob"] = math.sin(phase * 2.2) * 2.0
            pose["lean"] = 2
            pose["flap"] = math.sin(phase * 3.4)
            pose["flap_amp"] = 0.48
            pose["tail"] = phase * 1.8
            pose["legs"] = phase * 4.4
        elif action == "attack":
            pose["variant"] = getattr(NS, "_pose_variant_now", "thrust")
            if pose["variant"] == "sweep":
                if ap < 0.22:
                    t = ap / 0.22
                    pose["rear"] = -0.35 * t
                    pose["flap"] = 0.5 + 0.5 * t
                    pose["flap_amp"] = 0.36
                    pose["sqx"] = 1.0 + 0.06 * t
                    pose["sqy"] = 1.0 - 0.08 * t
                elif ap < 0.40:
                    pose["rear"] = -0.35
                    pose["flap"] = 1.0
                    pose["flap_amp"] = 0.3
                elif ap < 0.64:
                    t = NS._ease_out_cubic((ap - 0.40) / 0.24)
                    pose["rear"] = -0.35 + 0.75 * t
                    pose["lean"] = int(3 * t)
                    pose["flap"] = 1.0 - 1.6 * t
                    pose["flap_amp"] = 0.55
                    pose["sqx"] = 1.0 - 0.05 * t
                    pose["sqy"] = 1.0 + 0.07 * t
                else:
                    t = NS._ease_in_out((ap - 0.64) / 0.36)
                    pose["rear"] = 0.4 - 0.4 * t
                    pose["lean"] = int(3 * (1 - t))
                    pose["flap"] = -0.6 + 0.6 * t
                    pose["flap_amp"] = 0.5
            else:
                if ap < 0.22:
                    t = ap / 0.22
                    pose["rear"] = -0.3 * t
                    pose["flap"] = 0.4 + 0.6 * t
                elif ap < 0.40:
                    pose["rear"] = -0.3
                    pose["flap"] = 1.0
                    pose["flap_amp"] = 0.32
                    pose["charge"] = (ap - 0.22) / 0.18
                elif ap < 0.64:
                    t = NS._ease_out_cubic((ap - 0.40) / 0.24)
                    pose["rear"] = -0.3 + 0.6 * t
                    pose["lean"] = int(4 * t)
                    pose["flap"] = 1.0 - 1.4 * t
                    pose["flap_amp"] = 0.5
                    pose["charge"] = max(0.0, 1.0 - (ap - 0.40) / 0.08)
                else:
                    t = NS._ease_in_out((ap - 0.64) / 0.36)
                    pose["rear"] = 0.3 - 0.3 * t
                    pose["lean"] = int(4 * (1 - t))
                    pose["flap"] = -0.4 + 0.4 * t
        elif action.startswith("cast"):
            pose["flap"] = math.sin(phase * 1.7)
            pose["flap_amp"] = 0.55
            pose["bob"] = math.sin(phase * 1.0) * 1.4
            if action in ("cast_q", "cast_w"):
                if ap < 0.38:
                    pose["charge"] = ap / 0.38
                    pose["rear"] = -0.2 * pose["charge"]
                else:
                    pose["rear"] = -0.2 + 0.35 * NS._ease_out_cubic(
                        (ap - 0.38) / 0.2)
                    pose["lean"] = 2
            elif action == "cast_e":
                pose["charge"] = min(1.0, ap / 0.3)
            else:  # cast_r
                if ap < 0.42:
                    pose["charge"] = ap / 0.42
                    pose["rear"] = -0.25 * pose["charge"]
                elif ap < 0.55:
                    pose["rear"] = 0.5
                    pose["flap"] = 1.2
                    pose["flap_amp"] = 0.7
                else:
                    t = NS._ease_in_out((ap - 0.55) / 0.45)
                    pose["rear"] = 0.5 - 0.5 * t
        elif action == "hit":
            flinch = math.sin(min(1.0, ap) * math.pi)
            pose["rear"] = -0.3 * flinch
            pose["flap"] = -0.9 * flinch
            pose["flap_amp"] = 0.6
        elif action == "death":
            pose["death_t"] = min(1.0, ap)
            pose["flap"] = -0.4
            pose["flap_amp"] = 0.2
            pose["rear"] = -0.5 + 0.2 * pose["death_t"]
            pose["bob"] = 6.0 * pose["death_t"]
        return pose

    # ===================================================================
    # HELPERS GAMBAR RIG (low-res, koordinat int, tepi keras)
    # ===================================================================
    @staticmethod
    def _rp(surface, color, points):
        if len(points) >= 3:
            pygame.draw.polygon(surface, color, points)

    @staticmethod
    def _rc(surface, color, c, r):
        if r >= 1:
            pygame.draw.circle(surface, color, (int(c[0]), int(c[1])), int(r))

    @staticmethod
    def _rl(surface, color, rect):
        x, y, w, h = rect
        w = max(1, int(w))
        h = max(1, int(h))
        if w > 0 and h > 0:
            pygame.draw.rect(surface, color, (int(x), int(y), w, h))

    @staticmethod
    def _rline(surface, color, a, b, w=1):
        pygame.draw.line(surface, color, (int(a[0]), int(a[1])),
                         (int(b[0]), int(b[1])), max(1, int(w)))

    # ---------------------------------------------------------------------------
    # DRAW PRIMITIVES (layar, alpha-safe) — FX canvas fallback
    # ---------------------------------------------------------------------------
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_nyzrak._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_nyzrak.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_nyzrak._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width - 2
            min_y = min(sy, ey) - width - 2
            w = abs(ex - sx) + width * 4 + 8
            h = abs(ey - sy) + width * 4 + 8
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color, (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_nyzrak._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = int(max(xs) - min_x + 4)
            h = int(max(ys) - min_y + 4)
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)


    def _ellipse(surface, color, rect, width=0):
        color = _NS_nyzrak._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, int(rw), int(rh)), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3],
                            (rect[0], rect[1], int(rect[2]), int(rect[3])), width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_nyzrak._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, int(rw), int(rh)),
                             border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3],
                         (rect[0], rect[1], int(rect[2]), int(rect[3])),
                         border_radius=border_radius)


    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return int(x + 220 / float(getattr(boss, "_render_scale", 1.0) or 1.0)
                   * getattr(boss, "direction", 1)), int(y)


    @staticmethod
    def _melee_variant(boss):
        """True kalau target cukup dekat untuk sapuan melee."""
        tgt = getattr(boss, "target", None)
        if tgt is None or not getattr(tgt, "alive", False):
            return False
        try:
            d = math.hypot(tgt.x - getattr(boss, "x", 0),
                           tgt.y - getattr(boss, "y", 0))
        except Exception:
            return False
        return d <= 115.0

    # ===================================================================
    # RIG PIXEL-ART — komposit wyvern + rider per layer
    # ===================================================================
    @staticmethod

    # ===================================================================
    # RIG PIXEL-ART v4 — layer modular (wyvern + rider)
    # ===================================================================
    @staticmethod
    def _draw_rig(surface, cx, cy, facing, pose, action, phase, ap):
        """Gambar seluruh rig ke canvas low-res (hadap sesuai facing).

        Urutan layer:
            back wing -> tail -> hind legs -> body -> head/face ->
            front wing (di BELAKANG rider) -> rider -> weapon -> highlight
        """
        NS = _NS_nyzrak
        F = 1 if facing >= 0 else -1

        def mx(dx):
            return cx + int(dx) * F

        bob = int(pose.get("bob", 0))
        lean = int(pose.get("lean", 0)) * F
        rear = float(pose.get("rear", 0.0))
        pitch = float(pose.get("pitch", 0.0)) + rear * 6.0
        by = cy + bob + int(-rear * 3)

        ang_deg, reach, gx, gy = NS._spear_pose_geom(action, ap, phase)
        grip_ax = mx(gx) + lean
        grip_ay = cy + gy + bob

        render_back_wing(surface, mx(-10) + lean, by - 6, F,
                         pose["flap"], pose["flap_amp"], spread=0.88)
        render_tail(surface, mx(-16) + lean, by + 2, F,
                    pose["tail"], pose.get("death_t", 0.0))
        render_legs(surface, mx(-6) + lean, by + 12, F, pose["legs"])
        render_body(surface, mx(0) + lean, by, F, pitch, pose)

        head_lunge = 0.0
        if action == "attack":
            head_lunge = NS._ease_out_cubic(NS._seg_t(ap, 0.40, 0.64)) \
                - NS._seg_t(ap, 0.80, 1.0) * 0.8
        elif str(action).startswith("cast"):
            head_lunge = 0.3 * NS._seg_t(ap, 0.38, 0.55)
        hx = mx(16) + lean + int(head_lunge * 5) * F
        hy = by - 6 + int(-rear * 4)
        render_head(surface, hx, hy, F, phase, action)
        render_face(surface, hx, hy, F, phase, action)

        # Sayap dekat: bahu, ke atas-belakang — SEBELUM rider.
        render_front_wing(surface, mx(-4) + lean, by - 8, F,
                          pose["flap"], pose["flap_amp"], spread=0.95)

        rx = mx(-2) + lean
        ry = by - 18 + int(math.sin(phase * 0.8))
        render_rider_cloak(surface, rx, ry, F)
        render_rider_armor(surface, rx, ry, F)
        render_rider_head(surface, rx, ry, F, phase)
        render_rider_arms(surface, rx, ry, F, phase, action,
                          (grip_ax, grip_ay))

        render_weapon(surface, grip_ax, grip_ay, F,
                      math.radians(ang_deg), reach,
                      pose.get("charge", 0.0))
        render_highlight(surface, mx(0) + lean, by, F, phase)

    @staticmethod
    def _draw_wing(surface, sx, sy, facing, flap, amp, back=False,
                   spread=1.0):
        _wing(surface, sx, sy, facing, flap, amp, back=back, spread=spread)

    @staticmethod
    def _draw_tail(surface, x, y, facing, wave, death_t):
        render_tail(surface, x, y, facing, wave, death_t)

    @staticmethod
    def _draw_legs(surface, x, y, facing, cycle):
        render_legs(surface, x, y, facing, cycle)

    @staticmethod
    def _draw_wy_body(surface, x, y, facing, pitch):
        render_body(surface, x, y, facing, pitch, None)

    @staticmethod
    def _draw_wy_head(surface, x, y, facing, phase, action):
        render_head(surface, x, y, facing, phase, action)
        render_face(surface, x, y, facing, phase, action)

    @staticmethod
    def _draw_rider(surface, cx, cy, facing, phase, action, grip):
        rx, ry = cx, cy + int(math.sin(phase * 0.8))
        render_rider_cloak(surface, rx, ry, facing)
        render_rider_armor(surface, rx, ry, facing)
        render_rider_head(surface, rx, ry, facing, phase)
        render_rider_arms(surface, rx, ry, facing, phase, action, grip)

    @staticmethod
    def _draw_spear(surface, gx, gy, facing, angle, reach, charge):
        render_weapon(surface, gx, gy, facing, angle, reach, charge)

    @staticmethod
    def _draw_rim_highlights(surface, x, y, facing, phase):
        render_highlight(surface, x, y, facing, phase)

    def _detect_moving(boss):
        if not hasattr(boss, "_nyz_last_x"):
            boss._nyz_last_x = boss.x
            boss._nyz_last_y = boss.y
            return False
        dx = abs(boss.x - boss._nyz_last_x)
        dy = abs(boss.y - boss._nyz_last_y)
        mag = dx + dy
        boss._nyz_last_x = boss.x
        boss._nyz_last_y = boss.y
        boss._nyz_move_mag = mag
        return mag > 0.3

    def _update_attack_anim(boss):
        """Kemajuan serangan dari timer simulasi (frame @60fps) + jam dt."""
        try:
            now = pygame.time.get_ticks()
        except Exception:
            now = 0
        prev_ms = getattr(boss, "_nyz_last_ms", None)
        if prev_ms is None:
            dt = 1.0 / 60.0
        else:
            dt = (now - prev_ms) / 1000.0
            if dt <= 0.0 or dt > 0.05:
                dt = 1.0 / 60.0
        boss._nyz_last_ms = now
        boss._nyz_dt = dt
        boss._nyz_time = float(getattr(boss, "_nyz_time", 0.0)) + dt
        sp = getattr(boss, "_nyz_spawn_t", None)
        if sp is None:
            boss._nyz_spawn_t = 1.0
            if getattr(boss, "_nyz_want_spawn", False):
                boss._nyz_spawn_t = 0.0001
        elif 0.0 < float(sp) < 1.0:
            boss._nyz_spawn_t = min(1.0, float(sp) + dt / 0.85)
        vic = float(getattr(boss, "_nyz_victory_t", 0.0) or 0.0)
        if getattr(boss, "_victory", False) or getattr(boss, "victory", False):
            vic = min(1.0, vic + dt / 0.7)
        else:
            vic = max(0.0, vic - dt / 0.4)
        boss._nyz_victory_t = vic
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_nyz_prev_timer", 0))
        active = bool(getattr(boss, "_nyz_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._nyz_attack_active = True
            boss._nyz_attack_frame = 0
            boss._pose_variant = 1 if _NS_nyzrak._melee_variant(boss) else 0
            active = True
        elif active:
            boss._nyz_attack_frame = int(getattr(boss, "_nyz_attack_frame", 0)) + 1
            if boss._nyz_attack_frame > cooldown:
                boss._nyz_attack_active = False
                boss._nyz_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._nyz_attack_active = False
            boss._nyz_attack_frame = 0
            active = False

        boss._nyz_prev_timer = timer
        boss._nyz_attack_progress = (
            min(1.0, getattr(boss, "_nyz_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
        boss._pose_variant_now = \
            "sweep" if int(getattr(boss, "_pose_variant", 0) or 0) == 1 else "thrust"
        if not getattr(boss, "alive", True) or getattr(boss, "hp", 1) <= 0:
            boss._nyz_death_age = int(getattr(boss, "_nyz_death_age", 0)) + 1
        else:
            boss._nyz_death_age = 0

    @staticmethod
    def _resolve_pose(boss):
        """(action, phase, ap) pose SAAT INI — dipakai fx layer & debug."""
        moving = bool(getattr(boss, "_nyz_move_mag", 0) > 0.3)
        run = float(getattr(boss, "_nyz_move_mag", 0)) > 2.4
        info = _NS_nyzrak._NyzAnimController.resolve(boss, moving, run)
        _NS_nyzrak._pose_variant_now = \
            "sweep" if int(getattr(boss, "_pose_variant", 0) or 0) == 1 else "thrust"
        return info["action"], info["phase"], info["ap"]

    @staticmethod
    def _spear_state(boss, x, y):
        """Geometri tombak layar-lokal untuk lapisan FX (trail/muzzle)."""
        NS = _NS_nyzrak
        action, phase, ap = NS._resolve_pose(boss)
        facing = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        ang_deg, reach, gx, gy = NS._spear_pose_geom(action, ap, phase)
        ang = math.radians(ang_deg)
        scale = NS.render_scale_of(boss)
        grip = pygame.Vector2(x + gx * NS.PIXEL * facing * scale,
                              y + gy * NS.PIXEL * scale)
        d = pygame.Vector2(math.cos(ang) * facing, math.sin(ang))
        tip = grip + d * (reach * NS.PIXEL * scale)
        active = (action == "attack"
                  and NS.ATTACK_ACTIVE[0] <= ap <= NS.ATTACK_ACTIVE[1])
        return {"grip": grip, "tip": tip, "angle": ang, "action": action,
                "ap": ap, "facing": facing, "active": active}

    @staticmethod
    def render_scale_of(boss):
        """Faktor skala pipeline hero (jalur boss = 1.0)."""
        v = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return max(0.05, min(1.6, v if v > 0.02 else 1.0))

    # ===================================================================
    # PROJECTILE CANVAS FALLBACK (hidup saat modul FX tak tersedia)
    # ===================================================================
    class IceProjectile:
        """Pecahan es berputar — serangan dasar (fallback canvas)."""
        def __init__(self, sx, sy, tx, ty, speed=7.0):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.trail = []
            self.spin = 0.0
            self.angle = math.atan2(ty - sy, tx - sx)

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.spin += 0.4
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.hypot(dx, dy)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 8:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            NS = _NS_nyzrak
            P = NS.PALETTE
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 18)
                NS._aacircle(surface, (*P["ice_dark"], alpha), (tx, ty), 2)
                NS._aacircle(surface, (*P["ice_light"], alpha), (tx, ty), 1)
            if not self.alive:
                return
            px, py = int(self.x), int(self.y)
            dx, dy = math.cos(self.angle), math.sin(self.angle)
            nx, ny = -dy, dx
            NS._poly(surface, P["ice_darkest"], [
                (px + int(dx * 8), py + int(dy * 8)),
                (px + int(nx * 3), py + int(ny * 3)),
                (px - int(dx * 3), py - int(dy * 3)),
                (px - int(nx * 3), py - int(ny * 3)),
            ])
            NS._poly(surface, P["ice_mid"], [
                (px + int(dx * 6), py + int(dy * 6)),
                (px + int(nx * 2), py + int(ny * 2)),
                (px - int(dx * 2), py - int(dy * 2)),
                (px - int(nx * 2), py - int(ny * 2)),
            ])
            NS._poly(surface, P["ice_bright"], [
                (px + int(dx * 5), py + int(dy * 5)),
                (px, py), (px - dx, py - dy),
            ])
            NS._draw_snowflake(surface, px, py, 4, 200, rotate=self.spin)


    class SplinterShard:
        """Splinter Blast (W) — serpihan cepat keluar (fallback canvas)."""
        def __init__(self, x, y, dir_x, dir_y, speed=6.0, life=25):
            self.x = float(x)
            self.y = float(y)
            self.dir_x = dir_x
            self.dir_y = dir_y
            self.speed = speed
            self.life = life
            self.age = 0
            self.alive = True
            self.angle = math.atan2(dir_y, dir_x)
            self.trail = []

        def update(self):
            self.age += 1
            if self.age >= self.life:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 5:
                self.trail.pop(0)
            self.x += self.dir_x * self.speed
            self.y += self.dir_y * self.speed

        def draw(self, surface, phase):
            NS = _NS_nyzrak
            P = NS.PALETTE
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 22)
                NS._aacircle(surface, (*P["ice_light"], alpha), (tx, ty), 1)
            if not self.alive:
                return
            px, py = int(self.x), int(self.y)
            dx, dy = self.dir_x, self.dir_y
            nx, ny = -dy, dx
            NS._poly(surface, P["ice_darkest"], [
                (px + int(dx * 8), py + int(dy * 8)),
                (px + int(nx * 2), py + int(ny * 2)),
                (px - int(dx * 4), py - int(dy * 4)),
                (px - int(nx * 2), py - int(ny * 2)),
            ])
            NS._poly(surface, P["ice_dark"], [
                (px + int(dx * 7), py + int(dy * 7)),
                (px + int(nx), py + int(ny)),
                (px - int(dx * 3), py - int(dy * 3)),
                (px - int(nx), py - int(ny)),
            ])
            NS._poly(surface, P["ice_bright"], [
                (px + int(dx * 6), py + int(dy * 6)),
                (px, py), (px - int(dx * 2), py - int(dy * 2)),
            ])


    class ArcticBurnBeam:
        """Q — beam frost ungu menerjang target (fallback canvas)."""
        def __init__(self, sx, sy, tx, ty, life=45):
            self.sx = sx
            self.sy = sy
            self.tx = tx
            self.ty = ty
            self.life = life
            self.age = 0
            self.alive = True

        def update(self):
            self.age += 1
            if self.age >= self.life:
                self.alive = False

        def draw(self, surface, phase):
            NS = _NS_nyzrak
            P = NS.PALETTE
            t = self.age / self.life
            if t < 0.15:
                a_scale = t / 0.15
            elif t < 0.75:
                a_scale = 1.0
            else:
                a_scale = 1 - (t - 0.75) / 0.25
            dx = self.tx - self.sx
            dy = self.ty - self.sy
            dist = math.hypot(dx, dy)
            if dist < 1:
                return
            ux, uy = dx / dist, dy / dist
            nx, ny = -uy, ux
            beam_len = dist * min(1.0, t / 0.3)
            steps = max(2, int(beam_len / 5))
            edge_top, edge_bot, core = [], [], []
            for i in range(steps + 1):
                tp = i / steps
                w = 3.0 + 2.0 * math.sin(phase * 6 + tp * 9)
                wav = math.sin(phase * 6 + tp * 12) * 2.0
                bx = self.sx + ux * beam_len * tp
                by = self.sy + uy * beam_len * tp
                edge_top.append((bx + nx * (w + wav), by + ny * (w + wav)))
                edge_bot.append((bx - nx * (w - wav), by - ny * (w - wav)))
                core.append((bx, by))
            NS._poly(surface, (*P["frost_dark"], int(150 * a_scale)),
                     edge_top + edge_bot[::-1])
            NS._poly(surface, (*P["frost_mid"], int(190 * a_scale)),
                     [(cx_ + nx * 1.6, cy_ + ny * 1.6) for cx_, cy_ in core]
                     + [(cx_ - nx * 1.6, cy_ - ny * 1.6)
                        for cx_, cy_ in core[::-1]])
            NS._poly(surface, (*P["frost_hot"], int(220 * a_scale)),
                     [(cx_ + nx * 0.7, cy_ + ny * 0.7) for cx_, cy_ in core]
                     + [(cx_ - nx * 0.7, cy_ - ny * 0.7)
                        for cx_, cy_ in core[::-1]])
            for i in range(5):
                tp = (phase * 0.5 + i * 0.2) % 1.0
                if tp > beam_len / dist:
                    continue
                fx = self.sx + ux * dist * tp + nx * 6
                fy = self.sy + uy * dist * tp + ny * 6
                NS._draw_snowflake(surface, int(fx), int(fy), 2,
                                   int(210 * a_scale), rotate=phase * 2 + i)
            if 0.3 < t < 0.85:
                k = math.sin((t - 0.3) / 0.55 * math.pi)
                ex = int(self.sx + ux * beam_len)
                ey = int(self.sy + uy * beam_len)
                for r, col in ((18, "frost_dark"), (11, "frost_bright"),
                               (5, "ice_pure")):
                    NS._aacircle(surface, (*P[col], int(200 * k)),
                                 (ex, ey), max(1, int(r * k)))
                for i in range(6):
                    a = i * math.pi / 3 + phase
                    cx2 = ex + int(math.cos(a) * 14)
                    cy2 = ey + int(math.sin(a) * 7)
                    NS._draw_crystal_spike(surface, cx2, cy2,
                                           cy2 - max(2, int(13 * k)), 2,
                                           int(220 * k), "frost")

    # ------------------------------------------------------------------
    # Manajemen projectile canvas fallback
    # ------------------------------------------------------------------
    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_nyz_projectiles"):
            boss._nyz_projectiles = []
        if not hasattr(boss, "_nyz_shards"):
            boss._nyz_shards = []
        if not hasattr(boss, "_nyz_beams"):
            boss._nyz_beams = []

        for p in boss._nyz_projectiles:
            p.update()
            p.draw(surface, phase)
        boss._nyz_projectiles = [p for p in boss._nyz_projectiles
                                 if p.alive or p.age < 3]

        for s in boss._nyz_shards:
            s.update()
            s.draw(surface, phase)
        boss._nyz_shards = [s for s in boss._nyz_shards if s.alive]

        for b in boss._nyz_beams:
            b.update()
            b.draw(surface, phase)
        boss._nyz_beams = [b for b in boss._nyz_beams if b.alive]


    def _spawn_ice_projectile(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_nyz_projectiles"):
            boss._nyz_projectiles = []
        boss._nyz_projectiles.append(_NS_nyzrak.IceProjectile(sx, sy, tx, ty))


    def _spawn_splinter_burst(boss, x, y, count=8):
        if not hasattr(boss, "_nyz_shards"):
            boss._nyz_shards = []
        for i in range(count):
            angle = i * math.pi * 2 / count
            boss._nyz_shards.append(_NS_nyzrak.SplinterShard(
                x, y, math.cos(angle), math.sin(angle) * 0.7, speed=5.5, life=28
            ))


    def _spawn_arctic_burn(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_nyz_beams"):
            boss._nyz_beams = []
        boss._nyz_beams.append(_NS_nyzrak.ArcticBurnBeam(sx, sy, tx, ty))

    # ===================================================================
    # SNOWFLAKE / CRYSTAL HELPERS
    # ===================================================================
    @staticmethod
    def _draw_snowflake(surface, cx, cy, size=3, alpha=255, rotate=0.0):
        """Bintang salju 6 lengan — 1px, alpha-safe."""
        P = _NS_nyzrak.PALETTE
        cx, cy = int(cx), int(cy)
        for i in range(6):
            a = rotate + i * math.pi / 3
            ex = cx + int(math.cos(a) * size)
            ey = cy + int(math.sin(a) * size)
            _NS_nyzrak._aaline(surface, (*P["ice_hot"], alpha), (cx, cy),
                               (ex, ey), 1)
            mx = cx + int(math.cos(a) * max(1, size - 1))
            my = cy + int(math.sin(a) * max(1, size - 1))
            tt = a + math.pi / 2
            _NS_nyzrak._aaline(surface, (*P["ice_bright"], alpha),
                               (mx, my),
                               (mx + int(math.cos(tt)), my + int(math.sin(tt))),
                               1)
        pygame.draw.rect(surface, (*P["ice_pure"], alpha), (cx, cy, 1, 1))


    @staticmethod
    def _draw_crystal_spike(surface, cx, base_y, tip_y, width=4, alpha=255,
                            color_set="ice"):
        """Paku kristal es tumbuh ke atas — band 3 nada."""
        if color_set == "ice":
            colors = ["ice_darkest", "ice_dark", "ice_mid", "ice_light",
                      "ice_bright"]
        else:
            colors = ["frost_darkest", "frost_dark", "frost_mid",
                      "frost_light", "frost_bright"]
        P = _NS_nyzrak.PALETTE
        _NS_nyzrak._poly(surface, (*P["shadow_deep"], alpha), [
            (cx - width + 1, base_y + 1), (cx + width + 1, base_y + 1),
            (cx + 1, tip_y + 1),
        ])
        _NS_nyzrak._poly(surface, (*P[colors[0]], alpha), [
            (cx - width, base_y), (cx + width, base_y), (cx, tip_y),
        ])
        _NS_nyzrak._poly(surface, (*P[colors[1]], alpha), [
            (cx - max(1, width - 1), base_y), (cx + max(1, width - 1), base_y),
            (cx, tip_y + (base_y - tip_y) // 4),
        ])
        _NS_nyzrak._poly(surface, (*P[colors[2]], alpha), [
            (cx - max(1, width // 2), base_y), (cx + 1, base_y),
            (cx, tip_y + (base_y - tip_y) // 2),
        ])
        _NS_nyzrak._poly(surface, (*P[colors[4]], alpha), [
            (cx, tip_y), (cx + 1, tip_y + (base_y - tip_y) // 3), (cx, base_y),
        ])

    # ===================================================================
    # GROUND / SHADOW / AURA (ruang layar)
    # ===================================================================
    def _draw_shadow(surface, x, y, lift=0):
        """Bayangan kontak reaktif: mengecil saat terangkat, dasar menapak.

        Elips integer (tanpa smoothscale) supaya tepi tetap keras.
        """
        NS = _NS_nyzrak
        k = max(0.12, 1.0 - lift * 0.05)
        w = max(8, int(100 * k))
        h = max(3, int(14 * k))
        bx = int(x - w // 2)
        by = int((y + 11) - h)     # dasar tetap menapak di y+11
        NS._ellipse(surface, (0, 0, 0, 90), (bx, by, w, h))
        NS._ellipse(surface, (0, 0, 0, 130),
                    (bx + w // 6, by + h // 3, max(4, w * 2 // 3),
                     max(2, h // 2)))
        NS._ellipse(surface, (*NS.PALETTE["ice_dark"], 70),
                    (bx, by, w, h), 1)
        if NS._record_shadow is not None:
            NS._record_shadow.append(pygame.Rect(bx, by, w, h))


    def _draw_frost_aura(surface, x, y, phase, active_skill):
        """Cincin es 1px di tanah — bukan halo radial (itu yang 'sensor')."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        pulse = 0.55 + 0.45 * math.sin(phase * 0.5)
        if active_skill in ("q", "w", "e", "r"):
            col = P["frost_mid"] if active_skill == "q" else P["ice_mid"]
            a = int(110 * pulse)
            rw, rh = 48, 14
        else:
            col = P["ice_dark"]
            a = int(55 * pulse)
            rw, rh = 40, 11
        NS._ellipse(surface, (*col, a),
                    (x - rw, y + 28, rw * 2, rh), 1)


    def _draw_ground_frost(surface, x, y, phase, active_skill):
        """Beku tanah chunky: patch es + kristal kecil (cached)."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        if NS._ground_cache is None:
            g = pygame.Surface((150, 40), pygame.SRCALPHA)
            for i, (dx, w) in enumerate(((-48, 16), (-28, 22), (-4, 26),
                                         (24, 18), (46, 12))):
                yy = 18 + (i % 2) * 3
                pygame.draw.rect(g, (*P["ice_darkest"], 90),
                                 (75 + dx, yy, w, 2))
                pygame.draw.rect(g, (*P["ice_dark"], 120),
                                 (75 + dx + 2, yy, w - 4, 1))
            for dx, h in ((-40, 5), (-10, 7), (18, 6), (40, 4)):
                pygame.draw.polygon(g, (*P["ice_mid"], 150),
                                    [(75 + dx - 2, 20), (75 + dx + 2, 20),
                                     (75 + dx, 20 - h)])
            NS._ground_cache = g
        spr = NS._ground_cache
        pulse = math.sin(phase * 0.9) * 0.25 + 0.75
        spr.set_alpha(int(255 * pulse * (1.5 if active_skill else 1.0)))
        surface.blit(spr, (x - 75, y - 10))


    def _draw_frost_wisps(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        """Salju 1px di bawah wyvern — tanpa kabut elips."""
        NS = _NS_nyzrak
        strength = 1.35 if intense else 0.85
        for i in range(4):
            t = (phase * 0.4 + i * 0.22) % 1.0
            angle = phase * 0.45 + i * math.pi * 2 / 4
            r = 20 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 7) - int(t * 10)
            alpha = int(200 * (1 - t * 0.55) * strength)
            NS._draw_snowflake(surface, sx, sy, 2,
                               max(0, min(255, alpha)), rotate=phase + i)
        if trail:
            for i in range(3):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = max(0, 120 - i * 30)
                NS._aacircle(surface, (*NS.PALETTE["ice_mid"], alpha),
                             (sx, sy), max(1, 3 - i))


    def _draw_cast_flash(surface, x, y, facing, progress):
        """Kilat lepas serangan: bintang 4 arah chunky."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        k = 0.0
        if 0.40 <= progress <= 0.64:
            k = math.sin((progress - 0.40) / 0.24 * math.pi)
        if k <= 0.02:
            return
        fx = x + 26 * facing
        fy = y - 12
        for r, col in ((10, "ice_dark"), (6, "ice_bright")):
            NS._aacircle(surface, (*P[col], int(120 * k)), (fx, fy),
                         max(1, int(r * k)))
        for a in (0, math.pi / 2, math.pi, math.pi * 1.5):
            ex = fx + int(math.cos(a) * 14 * k)
            ey = fy + int(math.sin(a) * 14 * k)
            NS._aaline(surface, (*P["ice_hot"], int(200 * k)), (fx, fy),
                       (ex, ey), 2)

    # ===================================================================
    # SWING ARC TRAIL — fallback canvas (deterministik dari kurva arc)
    # ===================================================================
    def _draw_swing_arc(surface, boss, x, y, action, ap, phase, facing):
        """Jejak sapuan tombak (canvas fallback, tanpa histori runtime).

        Posisi blade dihitung dari kurva _spear_pose_geom pada progress
        lampau -> quad sapuan memudar mengikuti arah serangan.
        """
        NS = _NS_nyzrak
        if action != "attack":
            return
        a0, a1 = NS.ATTACK_ACTIVE
        if not (a0 <= ap <= a1 + 0.12):
            return
        scale = NS.render_scale_of(boss)
        samples = []
        for i in range(6):
            back_ap = ap - i * 0.035
            if back_ap < a0:
                break
            ang_deg, reach, gx, gy = NS._spear_pose_geom(action, back_ap,
                                                         phase)
            ang = math.radians(ang_deg)
            grip = pygame.Vector2(x + gx * NS.PIXEL * facing * scale,
                                  y + gy * NS.PIXEL * scale)
            d = pygame.Vector2(math.cos(ang) * facing, math.sin(ang))
            samples.append(grip + d * (reach * NS.PIXEL * scale))
        if len(samples) < 3:
            return
        P = NS.PALETTE
        for i in range(len(samples) - 1):
            k = 1.0 - i / float(len(samples))
            p0, p1 = samples[i], samples[i + 1]
            nx = -(p1.y - p0.y)
            ny = (p1.x - p0.x)
            ln = max(1.0, math.hypot(nx, ny))
            nx, ny = nx / ln * 3.0, ny / ln * 3.0
            NS._poly(surface, (*P["ice_mid"], int(90 * k)), [
                (p0.x + nx, p0.y + ny), (p1.x + nx, p1.y + ny),
                (p1.x - nx, p1.y - ny), (p0.x - nx, p0.y - ny),
            ])
            NS._poly(surface, (*P["ice_bright"], int(150 * k)), [
                (p0.x + nx * 0.4, p0.y + ny * 0.4),
                (p1.x + nx * 0.4, p1.y + ny * 0.4),
                (p1.x - nx * 0.4, p1.y - ny * 0.4),
                (p0.x - nx * 0.4, p0.y - ny * 0.4),
            ])

    # ===================================================================
    # SKILL FX CANVAS — telegraph tanah + foreground (fallback)
    # ===================================================================
    def _draw_winters_curse_ground(surface, boss, x, y, timer, phase):
        """E: telegraph tanah — cincin es dash chunky menyempit."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        tx, ty = NS._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        radius = int(25 + progress * 12)
        for i in range(12):
            a = i * math.pi * 2 / 12 + phase * 0.6
            ex = tx + math.cos(a) * radius
            ey = ty + math.sin(a) * radius * 0.45
            dx = -math.sin(a) * 3
            dy = math.cos(a) * 1.4
            NS._aaline(surface, (*P["ice_dark"], int(160 * pulse)),
                       (ex - dx, ey - dy), (ex + dx, ey + dy), 2)
        NS._ellipse(surface, (*P["ice_mid"], int(90 * pulse)),
                    (tx - radius, ty - radius // 3, radius * 2,
                     radius // 1.5), 2)


    def _draw_winters_curse_foreground(surface, boss, x, y, timer, phase):
        """E: penjara es kristal di sekitar target."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        tx, ty = NS._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.15:
            for i in range(10):
                angle = phase * 2 + i * math.pi / 5
                r = 46 * (1 - progress / 0.15)
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.5)
                NS._draw_snowflake(surface, sx, sy, 2, 200,
                                   rotate=phase * 4)
            return

        form_t = min(1.0, (progress - 0.15) / 0.3)
        tomb_w = int(26 * form_t)
        tomb_h = int(42 * form_t)
        if tomb_h <= 0:
            return
        NS._poly(surface, (*P["ice_darkest"], 200), [
            (tx - tomb_w, ty + 5), (tx - tomb_w, ty - tomb_h + 7),
            (tx - tomb_w // 2, ty - tomb_h), (tx + tomb_w // 2, ty - tomb_h),
            (tx + tomb_w, ty - tomb_h + 7), (tx + tomb_w, ty + 5),
        ])
        NS._poly(surface, (*P["ice_dark"], 180), [
            (tx - tomb_w + 2, ty + 4), (tx - tomb_w + 2, ty - tomb_h + 9),
            (tx - tomb_w // 2 + 2, ty - tomb_h + 2),
            (tx + tomb_w // 2 - 2, ty - tomb_h + 2),
            (tx + tomb_w - 2, ty - tomb_h + 9), (tx + tomb_w - 2, ty + 4),
        ])
        NS._poly(surface, (*P["ice_mid"], 150), [
            (tx - tomb_w + 4, ty + 3), (tx - tomb_w + 4, ty - tomb_h + 12),
            (tx - tomb_w // 2 + 4, ty - tomb_h + 5),
            (tx + tomb_w // 2 - 4, ty - tomb_h + 5),
            (tx + tomb_w - 6, ty - tomb_h + 12), (tx + tomb_w - 6, ty + 3),
        ])
        for i in range(3):
            NS._aaline(surface, (*P["ice_light"], 170),
                       (tx - tomb_w + 4, ty - i * 10),
                       (tx - tomb_w // 2, ty - tomb_h + i * 5 + 4), 1)
            NS._aaline(surface, (*P["ice_light"], 170),
                       (tx + tomb_w - 4, ty - i * 10),
                       (tx + tomb_w // 2, ty - tomb_h + i * 5 + 4), 1)
        NS._aaline(surface, (*P["ice_hot"], 220),
                   (tx, ty - tomb_h + 3), (tx, ty - 4), 1)
        for off in (-tomb_w + 2, 0, tomb_w - 2):
            NS._draw_crystal_spike(surface, tx + off, ty - tomb_h + 4,
                                   ty - tomb_h - 10, 3, 240, "ice")
        for i in range(5):
            angle = phase + i * math.pi * 2 / 5
            r = tomb_w + 5
            sx = tx + int(math.cos(angle) * r)
            sy = ty - tomb_h // 2 + int(math.sin(angle) * tomb_h // 2)
            NS._draw_snowflake(surface, sx, sy, 2, 220,
                               rotate=phase * 2 + i)


    def _draw_cold_embrace_ground(surface, boss, x, y, timer, phase):
        """R: lingkaran tanah 3 cincin dash chunky."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        duration = 90
        # Guard lifecycle: jangan menggambar di luar durasi skill AI.
        if timer <= 0 or timer > duration:
            return
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for i in range(3):
            r = int(48 + i * 12 + math.sin(phase + i) * 4)
            segs = 14 + i * 4
            for s in range(segs):
                a = s * math.pi * 2 / segs - phase * (0.4 + i * 0.2)
                ex = x + math.cos(a) * r
                ey = (y + 45) + math.sin(a) * r * 0.32
                dx = -math.sin(a) * 3
                dy = math.cos(a)
                NS._aaline(surface, (*P["ice_bright"], int(110 * pulse)),
                           (ex - dx, ey - dy), (ex + dx, ey + dy), 1)


    def _draw_cold_embrace_foreground(surface, boss, x, y, timer, phase):
        """R: cincin paku kristal + kubah faset + ledakan salju."""
        NS = _NS_nyzrak
        P = NS.PALETTE
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        rise_t = min(1.0, progress / 0.3)
        ring_radius = 52

        for i in range(12):
            angle = i * math.pi * 2 / 12
            sxp = x + int(math.cos(angle) * ring_radius)
            syp = y + 18 + int(math.sin(angle) * ring_radius * 0.3)
            h = int(22 * rise_t * (0.7 + 0.3 * math.sin(i * 2.4)))
            NS._draw_crystal_spike(surface, sxp, syp, syp - h, 3,
                                   int(230 * (1 - progress * 0.5)), "ice")
        if progress > 0.25:
            dome_k = min(1.0, (progress - 0.25) / 0.2)
            fade = max(0.0, 1.0 - max(0.0, (progress - 0.75) / 0.25))
            R = int(46 * dome_k)
            if R > 4 and fade > 0:
                for i in range(7):
                    a0 = i * math.pi / 7
                    a1 = (i + 1) * math.pi / 7
                    p0 = (x + int(math.cos(a0) * R),
                          y - 6 + int(math.sin(a0) * R * 0.9))
                    p1 = (x + int(math.cos(a1) * R),
                          y - 6 + int(math.sin(a1) * R * 0.9))
                    col = P["ice_dark"] if i % 2 else P["ice_mid"]
                    NS._poly(surface, (*col, int(70 * fade)),
                             [(x, y - 6), p0, p1])
                NS._ellipse(surface, (*P["ice_bright"], int(90 * fade)),
                            (x - R, y - 6 - int(R * 0.92), R * 2,
                             int(R * 1.84)), 2)
        if 0.38 < progress < 0.7:
            k = 1 - (progress - 0.38) / 0.32
            for i in range(8):
                a = i * math.pi / 4 + phase * 0.8
                rr = 30 + (1 - k) * 60
                sx = x + int(math.cos(a) * rr)
                sy = y - 8 + int(math.sin(a) * rr * 0.5)
                NS._draw_snowflake(surface, sx, sy, 3, int(230 * k),
                                   rotate=phase * 3 + i)

    # ===================================================================
    # LIVE FX BRIDGE — heroes/nyzrak_fx.py (lazy, opsional)
    # ===================================================================
    _live_mod = None

    @staticmethod
    def _live_module():
        """Modul FX hidup atau None (lazy import + fail-safe)."""
        NS = _NS_nyzrak
        if NS._live_mod is None:
            try:
                from heroes import nyzrak_fx as mod
                NS._live_mod = mod
            except Exception:
                NS._live_mod = False
        return NS._live_mod or None

    # ===================================================================
    # SKILL SPAWN (canvas fallback — dilewati jika FX hidup mengambil alih)
    # ===================================================================
    def _handle_skill_projectiles(boss, x, y, active_skill, timer, owned):
        """Pemicu proyektil skill Q/W pada progres yang tepat."""
        NS = _NS_nyzrak
        tx, ty = NS._target_position(boss, x, y)

        if active_skill == "q":
            duration = 50
            progress = max(0.0, min(1.0, 1 - timer / duration))
            if 0.35 < progress < 0.45 and not getattr(boss, "_nyz_q_spawned", False):
                if not owned:
                    NS._spawn_arctic_burn(boss, x + 25 * boss.direction,
                                          y - 15, tx, ty)
                boss._nyz_q_spawned = True
            if progress > 0.7:
                boss._nyz_q_spawned = False

        elif active_skill == "w":
            duration = 50
            progress = max(0.0, min(1.0, 1 - timer / duration))
            if 0.35 < progress < 0.45 and not getattr(boss, "_nyz_w_spawned", False):
                sx = x + 25 * boss.direction
                sy = y - 10
                base_angle = math.atan2(ty - sy, (tx - sx) or 1)
                if not owned:
                    for i in range(5):
                        spread = (i - 2) * 0.25
                        a = base_angle + spread
                        if not hasattr(boss, "_nyz_shards"):
                            boss._nyz_shards = []
                        boss._nyz_shards.append(NS.SplinterShard(
                            sx, sy, math.cos(a), math.sin(a), speed=6.0,
                            life=35))
                boss._nyz_w_spawned = True
            if progress > 0.7:
                boss._nyz_w_spawned = False

    # ===================================================================
    # MAIN ENTRY
    # ===================================================================

    # ===================================================================
    # MAIN ENTRY
    # ===================================================================
    def draw_nyzrak(surface, boss, x, y):
        """Entry point render Nyzrak (jalur boss & pipeline hero)."""
        NS = _NS_nyzrak
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = NS._detect_moving(boss)
        NS._update_attack_anim(boss)

        portrait = bool(getattr(boss, "_portrait_hd", False))
        canvas_pass = bool(getattr(boss, "_skip_renderer_projectiles", False))
        facing = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1

        info = NS._NyzAnimController.resolve(
            boss, moving, float(getattr(boss, "_nyz_move_mag", 0)) > 2.4)
        action, ap = info["action"], info["ap"]
        boss._nyz_pose_info = info

        owned = False
        live = None
        if not portrait and not canvas_pass:
            live = NS._live_module()
            if live is not None:
                try:
                    live.draw_ground_layer(surface, boss, x, y)
                    owned = bool(live.owns(boss))
                except Exception:
                    owned = False

        NS._draw_frost_aura(surface, x, y, pulse, active_skill)
        NS._draw_ground_frost(surface, x, y + 46, pulse, active_skill)
        if active_skill == "e":
            NS._draw_winters_curse_ground(surface, boss, x, y,
                                          skill_timer, pulse)
        elif active_skill == "r":
            NS._draw_cold_embrace_ground(surface, boss, x, y,
                                         skill_timer, pulse)

        lift = NS.LIFT + (2.0 if action in ("run", "attack") else 0.0)
        NS._draw_shadow(surface, x, y + NS.GROUND_DY - 2, int(lift))
        NS._draw_frost_wisps(surface, x, y + 40, pulse,
                             trail=(action in ("walk", "run")),
                             facing=facing,
                             intense=(action == "attack"
                                      or action.startswith("cast")))

        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        NS._draw_nyz_full(surface, x, y, facing, pulse, action, ap,
                          flash=flash, info=info)

        if not owned and not canvas_pass:
            NS._draw_swing_arc(surface, boss, x, y, action, ap, pulse, facing)
            if action == "attack":
                NS._draw_cast_flash(surface, x, y, facing, ap)
                if (0.44 <= ap <= 0.50
                        and not getattr(boss, "_nyz_atk_spawned", False)
                        and getattr(NS, "_pose_variant_now", "thrust") == "thrust"):
                    txx, tyy = NS._target_position(boss, x, y)
                    spear = NS._spear_state(boss, x, y)
                    tip = spear["tip"]
                    NS._spawn_ice_projectile(boss, tip.x, tip.y, txx, tyy)
                    boss._nyz_atk_spawned = True
                if ap < 0.1 or ap > 0.9:
                    boss._nyz_atk_spawned = False

        NS._handle_skill_projectiles(boss, x, y, active_skill, skill_timer,
                                     owned)

        if not owned and not canvas_pass:
            NS._manage_projectiles(boss, surface, pulse)

        if not owned:
            if active_skill == "e":
                NS._draw_winters_curse_foreground(surface, boss, x, y,
                                                  skill_timer, pulse)
            elif active_skill == "r":
                NS._draw_cold_embrace_foreground(surface, boss, x, y,
                                                 skill_timer, pulse)

        if live is not None and not portrait and not canvas_pass:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass

    # ===================================================================
    # KOMPOSIT BADAN v4 (buffer -> outline -> flash -> dissolve -> scale)
    # ===================================================================
    def _draw_nyz_full(surface, cx, cy, facing, phase, action,
                       attack_progress=0.0, flash=0, info=None):
        """Komposit pixel-art: rig low-res + outline + flash + nearest x2."""
        NS = _NS_nyzrak
        art = NS._compose_art(facing, phase, action, attack_progress,
                              flash=flash, info=info)
        big_w = NS.RIG_SIZE * NS.PIXEL
        if NS._scale_buf is None:
            NS._scale_buf = pygame.Surface((big_w, big_w), pygame.SRCALPHA)
        pygame.transform.scale(art, (big_w, big_w), NS._scale_buf)
        surface.blit(NS._scale_buf, (int(cx) - big_w // 2, int(cy) - big_w // 2))

    def _draw_nyz_full_raw(surface, cx, cy, facing, phase, action,
                           attack_progress=0.0):
        """Raw rig (tanpa outline) — dipakai tes / debug."""
        NS = _NS_nyzrak
        if NS._rig_buf is None:
            NS._rig_buf = pygame.Surface((NS.RIG_SIZE, NS.RIG_SIZE),
                                         pygame.SRCALPHA)
        rig = NS._rig_buf
        rig.fill((0, 0, 0, 0))
        pose = NS._rig_pose(action, phase, attack_progress)
        NS._draw_rig(rig, NS.RIG_SIZE // 2, NS.RIG_SIZE // 2, facing, pose,
                     action, phase, attack_progress)
        big = NS.RIG_SIZE * NS.PIXEL
        if NS._scale_buf is None:
            NS._scale_buf = pygame.Surface((big, big), pygame.SRCALPHA)
        pygame.transform.scale(rig, (big, big), NS._scale_buf)
        surface.blit(NS._scale_buf, (cx - big // 2, cy - big // 2))

    def _compose_art(facing, phase, action, ap, flash=0, info=None):
        NS = _NS_nyzrak
        if NS._rig_buf is None:
            NS._rig_buf = pygame.Surface((NS.RIG_SIZE, NS.RIG_SIZE),
                                         pygame.SRCALPHA)
        art = NS._rig_buf
        art.fill((0, 0, 0, 0))
        pose = NS._rig_pose(action, phase, ap)
        NS._draw_rig(art, NS.RIG_SIZE // 2, NS.RIG_SIZE // 2, facing, pose,
                     action, phase, ap)
        mask = render_outline(art)
        if flash > 0:
            render_hit_flash(art, mask, min(1.0, flash / 8.0))
            mask = render_outline(art)
        if action and str(action).startswith("cast"):
            render_status(art, mask, 0.35, _P["frost_bright"]
                          if action == "cast_q" else _P["ice_bright"])
        death_t = 0.0
        spawn_t = 1.0
        if info is not None:
            death_t = float(info.get("death_t", 0.0) or 0.0)
            spawn_t = float(info.get("spawn_t", 1.0) or 1.0)
        if death_t > 0.0:
            render_dissolve(art, max(0.0, (death_t - 0.15) / 0.85), seed=11)
        elif 0.0 < spawn_t < 1.0:
            render_dissolve(art, max(0.0, 1.0 - spawn_t * 1.3), seed=5)
        return art

    def draw_boss(surface, boss, x, y):
        _NS_nyzrak.draw_nyzrak(surface, boss, x, y)


# ----------------------------------------------------------------------------
# bind fungsi render modular ke namespace (API discoverable)
# ----------------------------------------------------------------------------
def _bind():
    NS = _NS_nyzrak
    for name in ("render_shadow", "render_back_wing", "render_front_wing",
                 "render_tail", "render_legs", "render_body", "render_head",
                 "render_face", "render_rider_cloak", "render_rider_armor",
                 "render_rider_head", "render_rider_arms", "render_weapon",
                 "render_highlight", "render_outline", "render_hit_flash",
                 "render_status", "render_dissolve",
                 "px_rect", "px_set", "px_line", "px_poly", "px_circle",
                 "px_ellipse", "px_dither", "px_ramp_h"):
        setattr(NS, name, staticmethod(globals()[name]))
    NS.PALETTE = PALETTE
    NS.AW = AW
    NS.AH = AH
    NS.AX = AX
    NS.AY = AY
    NS.PX = PX


_bind()
