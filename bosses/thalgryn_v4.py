# ============================================================================
# bosses/thalgryn_v4.py
# ----------------------------------------------------------------------------
# THALGRYN "THE SHAPE OF WATER" — RENDERER v4 (TOTAL REWRITE FROM ZERO).
#
# Mini boss Level 6 / hero lane. 100% prosedural pixel-art: TIDAK ada PNG,
# sprite sheet, atau pygame.image.load. Seluruh karakter digambar ke sebuah
# BUFFER PIXEL-ART RESOLUSI RENDAH (art-pixel 1:1, tanpa anti-alias) lalu
# di-upscale NEAREST x2 ke layar, sehingga setiap "pixel" benar-benar pixel:
# tepi bersih, kluster terkontrol, outline 1 art-px, dither pemisah material.
#
# ── KENAPA REWRITE ─────────────────────────────────────────────────────────
# Renderer lama (v3) menumpuk lingkaran anti-alias: siluet lembek seperti
# mainan, mata bulat "googly", bilah setipis jarum, rune tanah wireframe
# ellipse yang terbaca sebagai gizmo UI. v4 membuang semuanya dan membangun
# karakter dari layer pixel-art berurutan:
#
#   shadow -> mantle -> tail(vortex) -> body+core -> equipment -> armor ->
#   head -> face -> crown -> arms -> weapon(tide glaive) -> highlight ->
#   outline -> hit flash -> status overlay -> dissolve(death/spawn)
#
# ── ARSITEKTUR MODULAR (tiap bagian editable independen) ──────────────────
#   render_shadow()    contact shadow 2-tone + splash ring berbusa (dunia)
#   render_mantle()    jubah air berlapis di belakang badan (lag gelombang)
#   render_tail()      vortex air pengganti kaki + alur spiral
#   render_body()      torso air 5-band + inti pasang berdenyut + kerah emas
#   render_equipment() sabuk emas, gesper, tatters kain air
#   render_armor()     pauldron asimetris berduri + trim emas
#   render_head()      tengkorak air berahang
#   render_face()      void wajah, mata menyala menyipit, brow, mulut
#   render_crown()     mahkota raja-tenggelam 3 duri + gem pasang
#   render_arms()      lengan air depan/belakang + bracer emas + kepalan
#   render_weapon()    TIDE GLAIVE: haft baja, cincin emas, bilah sabit air
#   render_highlight() specular + rim light (pseudo-3D depth)
#   render_outline()   outline 1 art-px lewat mask 8 arah
#   render_hit_flash() flash putih saat kena damage
#   render_status()    overlay buff morph (rim atribut)
#   render_dissolve()  erosi alpha terkontrol (death / spawn rise)
#   render_orbit()     droplet mengorbit (equipment hidup, ruang dunia)
#
# ── ANIMASI (delta-time, bukan frame-dependent) ───────────────────────────
#   _update_thalgryn_attack_anim(boss) = SATU sumber kebenaran state:
#   IDLE/WALK/RUN/CHARGE/SWING/ATTACK/SKILL/SPECIAL/VICTORY/HURT/SPAWN/DEATH
#   dengan jam ``_th_state_time`` berbasis dt detik. Anticipation (squash
#   mundur), swing (stretch maju), impact pause (hold sudut bilah), recoil,
#   follow-through, dan gerak sekunder ber-lag (mantle/tail/droplet/crown).
#
# ── KONTRAK YANG TIDAK BERUBAH (gameplay & tes regresi) ───────────────────
#   * draw_thalgryn(surface, boss, x, y) entry point tunggal (+ draw_boss).
#   * SKILL_DUR sinkron bosses/base_boss._thalgryn_* & hero_skills/_bundle.
#   * nama atribut animasi lama ``_th_*`` dipertahankan persis.
#   * ATTACK_PHASES / ATTACK_ACTIVE_WINDOW / MELEE_REACH sama.
#   * PALETTE memuat semua key lama (disinkronkan heroes/thalgryn_fx.P).
# ============================================================================

import math
import random

import pygame

# ----------------------------------------------------------------------------
# 1. GEOMETRI BUFFER PIXEL-ART
# ----------------------------------------------------------------------------
#: ukuran buffer art (art-pixel 1:1). AW ganjil supaya flip facing simetris.
AW, AH = 109, 98
#: kolom/titik telapak vortex di koordinat buffer
AX, AY = 54, 78
#: faktor upscale nearest ke layar (jalur boss / mini boss)
PX = 2

HAS_MASK = hasattr(pygame, "mask")
HAS_PXARRAY = hasattr(pygame, "PixelArray")


# ============================================================================
# 2. PALETTE — ramp air 7 band + emas + baja + mata menyala (kontras kuat)
# ============================================================================
PALETTE = {
    # outline & abyss (nilai tergelap)
    "outline":        (5,  12, 20),
    "abyss":          (8,  22, 34),

    # badan air (7 band, gelap -> terang)
    "water_darkest":  (10, 36, 54),
    "water_dark":     (16, 62, 88),
    "water_mid":      (28, 108, 138),
    "water_light":    (58, 160, 186),
    "water_high":     (112, 208, 222),
    "water_shine":    (178, 240, 246),
    "water_white":    (235, 255, 255),

    # inti pasang (core) — nilai TERTERANG badan
    "core_dark":      (22, 96, 128),
    "core_mid":       (52, 176, 205),
    "core_light":     (126, 232, 246),
    "core_hot":       (210, 252, 255),

    # bilah air (weapon)
    "blade_darkest":  (8,  30, 46),
    "blade_dark":     (18, 74, 102),
    "blade_mid":      (40, 138, 168),
    "blade_light":    (96, 202, 220),
    "blade_shine":    (196, 246, 250),

    # baja haft (gagang glaive)
    "steel_dark":     (22, 26, 34),
    "steel_mid":      (52, 58, 70),
    "steel_light":    (98, 106, 122),

    # mata menyala
    "eye_dark":       (26, 110, 138),
    "eye_mid":        (96, 214, 226),
    "eye_bright":     (186, 248, 252),
    "eye_hot":        (240, 255, 255),

    # emas regalia (mahkota / pauldron / sabuk / guard)
    "gold_dark":      (74, 48, 12),
    "gold_mid":       (150, 104, 28),
    "gold_light":     (216, 166, 54),
    "gold_shine":     (255, 226, 122),

    # void wajah
    "face_void":      (4, 10, 16),
    "face_rim":       (18, 48, 66),

    # atribut morph (STR/AGI/INT)
    "str_red":        (200, 40, 40),
    "str_hot":        (255, 100, 90),
    "agi_green":      (60, 190, 70),
    "agi_hot":        (140, 240, 120),
    "int_blue":       (50, 130, 220),
    "int_hot":        (140, 200, 255),

    # misc
    "shadow":         (0, 0, 0),
    "shadow_deep":    (3, 6, 8),
    "white":          (255, 255, 255),
}

_P = PALETTE

# bobot band material untuk px_ramp_h (tepi gelap tipis -> bidang -> cahaya)
_RAMP_W = {
    2: (0.55, 0.45),
    3: (0.30, 0.45, 0.25),
    4: (0.24, 0.34, 0.26, 0.16),
    5: (0.18, 0.26, 0.26, 0.18, 0.12),
}


# ============================================================================
# 3. PIXEL PRIMITIVES — integer saja, tanpa anti-alias
# ============================================================================
def px_rect(surf, color, x, y, w, h):
    """Isi rect integer (kluster pixel terkontrol)."""
    if w <= 0 or h <= 0:
        return
    surf.fill(color, (int(x), int(y), int(w), int(h)))


def px_set(surf, color, x, y):
    """Satu art-pixel (aman di luar bounds: pixel dibuang, bukan crash)."""
    x = int(x)
    y = int(y)
    sw, sh = surf.get_size()
    if 0 <= x < sw and 0 <= y < sh:
        surf.set_at((x, y), color)


def px_line(surf, color, x0, y0, x1, y1):
    """Garis integer 1 px (diagonal jaggy = bahasa pixel-art)."""
    pygame.draw.line(surf, color, (int(x0), int(y0)), (int(x1), int(y1)), 1)


def px_poly(surf, color, pts):
    """Poligon isi integer."""
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
    """Checkerboard 1 art-px: transisi material / busa / bayangan lembut.

    ``masked=True`` hanya menimpa pixel yang SUDAH terisi (alpha>0),
    sehingga dither tidak pernah bocor keluar bentuk (tidak ada
    pixel yatim yang lalu di-outline menjadi blob hitam).
    """
    x = int(x)
    y = int(y)
    w = int(w)
    h = int(h)
    # clip ke bounds surface (bilah terangkat bisa keluar buffer)
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
    """Satu scanline material: ramp gelap->terang horizontal (pembulatan).

    Memberi ilusi bidang membulat (pseudo-3D) tanpa gradien lembut:
    tiap band satu warna solid, lebar terkontrol.
    """
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
        "bob", "lean", "sqx", "sqy",
        "head_dx", "head_dy",
        "mantle", "tail", "droplet",
        "grip_x", "grip_y", "w_ang",
        "core", "eye", "mouth", "crown",
        "flash", "morph", "morph_idx",
        "death", "spawn", "victory",
        "skill", "skill_p", "recoil", "hurt_k",
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
        self.head_dx = 0.0
        self.head_dy = 0.0
        self.mantle = 0.0
        self.tail = 0.0
        self.droplet = 0.0
        self.grip_x = 7.0
        self.grip_y = -26.0
        self.w_ang = -1.13
        self.core = 0.6
        self.eye = 0.85
        self.mouth = 0.0
        self.crown = 0.0
        self.flash = 0.0
        self.morph = 0.0
        self.morph_idx = 0
        self.death = 0.0
        self.spawn = 1.0
        self.victory = 0.0
        self.skill = None
        self.skill_p = 0.0
        self.recoil = 0.0
        self.hurt_k = 0.0


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
# 6. LAYER RENDERERS (modular — masing-masing independen)
#    Semua bekerja di koordinat buffer: (AX, AY) = telapak vortex.
#    Komposisi SELALU menghadap kanan; flip dilakukan saat blit.
# ============================================================================
def render_shadow(surface, x, y, pose, scale=1.0):
    """Contact shadow 2-tone + splash ring berbusa (ruang dunia)."""
    P = _P
    k = scale
    sw = int((19 + 2 * math.sin(pose.phase * 0.9)) * k * pose.sqx)
    sh = max(2, int(6 * k))
    cy = int(y) + 2
    # penumbra lalu inti gelap (contact shadow sungguhan, bukan 1 ellipse)
    px_ellipse(surface, P["shadow"] + (72,),
               (x - sw - 4 * k, cy - sh // 2 - 2, sw * 2 + 8 * k, sh + 4))
    px_ellipse(surface, P["shadow_deep"] + (150,),
               (x - sw, cy - sh // 2, sw * 2, sh))
    # splash ring: cincin busa dither (bukan wireframe)
    rw = int(sw * 1.3)
    rh = max(3, int(sh * 1.4))
    px_ellipse(surface, P["water_darkest"] + (170,),
               (x - rw, cy - rh // 2, rw * 2, rh))
    px_ellipse(surface, P["water_mid"] + (150,),
               (x - rw + 1, cy - rh // 2 + 1, rw * 2 - 2, rh - 2))
    px_ellipse(surface, (0, 0, 0, 0),
               (x - rw + 2, cy - rh // 2 + 2, rw * 2 - 4, rh - 4))
    foam = P["water_mid"] + (190,)
    foam2 = P["water_high"] + (210,)
    for i in range(7):
        a = pose.droplet * 0.8 + i * 0.897
        fx = int(x + math.cos(a) * rw * 0.94)
        fy = int(cy + math.sin(a) * rh * 0.44)
        px_set(surface, foam, fx, fy)
        if i & 1:
            px_set(surface, foam2, fx, fy - 1)


def render_mantle(art, pose):
    """Jubah air berlapis di belakang badan; hem bergerigi ber-lag."""
    P = _P
    ox, oy = AX, AY
    wave = pose.mantle
    ramp = (P["abyss"], P["water_darkest"], P["water_dark"], P["water_mid"])
    for yy in range(-35, -2):
        t = (yy + 35) / 33.0
        half = int(8 + 7 * t)
        back = -4 - int(2.0 * t)
        wob = int(round(math.sin(wave + yy * 0.40) * (0.5 + 1.7 * t)))
        x0 = ox + back - half + wob
        x1 = ox + back + half - 2 + wob
        px_ramp_h(art, ramp, x0, x1, oy + yy,
                  weights=(0.30, 0.30, 0.26, 0.14))
    # hem tatters
    for i in range(4):
        hx = ox - 10 + i * 5 + int(round(math.sin(wave * 1.1 + i) * 1.2))
        hl = 3 + (i & 1) * 2
        px_rect(art, P["water_dark"], hx, oy - 4, 2, hl)
        px_set(art, P["water_mid"], hx, oy - 4 + hl)
    # lipatan jubah: 2 garis gelap vertikal (bukan checker noise)
    for i, dx in enumerate((-9, -5)):
        wob = int(round(math.sin(wave * 0.8 + i * 2.1) * 1.0))
        px_line(art, P["abyss"], ox + dx + wob, oy - 26,
                ox + dx - 1 + wob, oy - 8)


def render_tail(art, pose):
    """Vortex air pengganti kaki: kerucut ber-swirl + alur spiral."""
    P = _P
    ox, oy = AX, AY
    swirl = pose.tail
    sqy = pose.sqy
    ramp = (P["water_darkest"], P["water_dark"], P["water_mid"],
            P["water_light"], P["water_high"])
    for yy in range(0, -17, -1):
        t = (-yy) / 16.0
        half = max(2, int((11 - 6.5 * t) * pose.sqx))
        cx = ox + int(round(math.sin(swirl * 0.9 + t * 3.4) * (2.4 * t)))
        cy = oy + int(yy * sqy)
        px_ramp_h(art, ramp, cx - half, cx + half, cy)
        sx = cx - half + int((0.30 + 0.35 * (0.5 + 0.5 * math.sin(
            swirl + t * 5.0))) * (half * 2))
        if cx - half < sx < cx + half:
            px_set(art, P["water_darkest"], sx, cy)
    px_dither(art, P["water_high"], ox - 8, oy - 1, 16, 1, 1, 3,
                  masked=True)


def render_body(art, pose):
    """Torso air 5-band + inti pasang berdenyut + kerah emas V."""
    P = _P
    ox, oy = AX, AY
    top, bot = -34, -17
    ramp = (P["water_darkest"], P["water_dark"], P["water_mid"],
            P["water_light"], P["water_high"])
    for yy in range(top, bot + 1):
        t = (yy - top) / float(bot - top)
        half = int((8 + 2 * math.sin(t * math.pi)) * pose.sqx)
        cx = ox + int(round(pose.lean * 0.35 * (1.0 - t)))
        cy = oy + int(yy * pose.sqy) + int(pose.bob * 0.35 * (1.0 - t))
        px_ramp_h(art, ramp, cx - half, cx + half, cy)
    # inti pasang: nilai TERTERANG badan, berdenyut
    c = pose.core
    ccx = ox + int(round(pose.lean * 0.3))
    ccy = oy + int(-27 * pose.sqy) + int(pose.bob * 0.2)
    if c > 0.05:
        px_circle(art, P["core_dark"], ccx, ccy, 4)
        px_circle(art, P["core_mid"], ccx, ccy, 3)
        px_circle(art, P["core_light"], ccx, ccy, 2)
        px_circle(art, P["core_hot"], ccx, ccy, 1)
        if c > 0.7:
            px_set(art, P["core_light"], ccx - 4, ccy)
            px_set(art, P["core_light"], ccx + 4, ccy)
            px_set(art, P["core_light"], ccx, ccy - 4)
            px_set(art, P["core_light"], ccx, ccy + 4)
            px_dither(art, P["core_mid"], ccx - 5, ccy - 5, 11, 11, 0, 4,
                      masked=True)
    # kerah emas V
    gx = ox + int(round(pose.lean * 0.3))
    gy = oy + int(-32 * pose.sqy)
    px_line(art, P["gold_mid"], gx - 5, gy - 1, gx, gy + 2)
    px_line(art, P["gold_mid"], gx + 5, gy - 1, gx, gy + 2)
    px_line(art, P["gold_light"], gx - 4, gy - 1, gx, gy + 1)
    px_set(art, P["gold_shine"], gx, gy + 2)


def render_equipment(art, pose):
    """Sabuk emas + gesper + tatters kain air yang melambai."""
    P = _P
    ox, oy = AX, AY
    by = oy + int(-17 * pose.sqy)
    bx = ox + int(round(pose.lean * 0.35))
    px_rect(art, P["gold_dark"], bx - 8, by + 1, 16, 1)
    px_rect(art, P["gold_mid"], bx - 8, by, 16, 1)
    px_rect(art, P["gold_light"], bx - 7, by - 1, 14, 1)
    px_rect(art, P["gold_light"], bx - 2, by - 1, 4, 3)
    px_set(art, P["gold_shine"], bx - 1, by - 1)
    px_set(art, P["core_mid"], bx, by)
    for i, dx in enumerate((-6, -1, 5)):
        ln = 6 + (i & 1) * 3
        wob = int(round(math.sin(pose.mantle * 1.2 + i * 1.7) * 1.4))
        for s in range(ln):
            px_set(art, P["water_dark"] if s & 1 else P["water_mid"],
                   bx + dx + wob * s // ln, by + 2 + s)


def render_armor(art, pose):
    """Pauldron asimetris berduri + trim emas (siluet interest)."""
    P = _P
    ox, oy = AX, AY
    sy = oy + int(-33 * pose.sqy) + int(pose.bob * 0.25)
    sx = ox + int(round(pose.lean * 0.3))
    # ── pauldron BELAKANG: besar, 2 duri emas ──
    bx = sx - 8
    px_poly(art, P["water_darkest"],
            [(bx - 4, sy + 4), (bx - 4, sy - 1), (bx - 1, sy - 4),
             (bx + 4, sy - 3), (bx + 5, sy + 4)])
    px_poly(art, P["water_dark"],
            [(bx - 3, sy + 3), (bx - 3, sy - 1), (bx - 1, sy - 3),
             (bx + 3, sy - 2), (bx + 4, sy + 3)])
    px_rect(art, P["water_mid"], bx - 3, sy - 2, 6, 2)
    px_rect(art, P["water_light"], bx - 2, sy - 3, 4, 1)
    px_set(art, P["water_high"], bx - 1, sy - 3)
    px_poly(art, P["water_darkest"], [(bx - 4, sy - 2), (bx - 5, sy - 8),
                                      (bx - 1, sy - 3)])
    px_poly(art, P["gold_mid"], [(bx - 3, sy - 3), (bx - 5, sy - 8),
                                 (bx - 1, sy - 4)])
    px_poly(art, P["water_darkest"], [(bx, sy - 3), (bx + 1, sy - 9),
                                      (bx + 3, sy - 3)])
    px_poly(art, P["gold_mid"], [(bx + 1, sy - 4), (bx + 1, sy - 9),
                                 (bx + 3, sy - 4)])
    px_line(art, P["gold_light"], bx - 4, sy - 7, bx - 3, sy - 4)
    px_line(art, P["gold_light"], bx + 1, sy - 8, bx + 1, sy - 5)
    px_rect(art, P["gold_dark"], bx - 4, sy + 3, 9, 1)
    px_rect(art, P["gold_mid"], bx - 4, sy + 2, 9, 1)
    # ── pauldron DEPAN: kecil, 1 duri ──
    fx = sx + 7
    px_poly(art, P["water_darkest"],
            [(fx - 3, sy + 3), (fx - 3, sy - 1), (fx, sy - 3),
             (fx + 3, sy - 1), (fx + 3, sy + 3)])
    px_poly(art, P["water_mid"],
            [(fx - 2, sy + 2), (fx - 2, sy - 1), (fx, sy - 2),
             (fx + 2, sy - 1), (fx + 2, sy + 2)])
    px_rect(art, P["water_light"], fx - 1, sy - 2, 3, 1)
    px_set(art, P["water_high"], fx, sy - 2)
    px_poly(art, P["water_darkest"], [(fx - 1, sy - 2), (fx + 2, sy - 7),
                                      (fx + 3, sy - 2)])
    px_poly(art, P["gold_mid"], [(fx, sy - 3), (fx + 2, sy - 7),
                                 (fx + 2, sy - 3)])
    px_line(art, P["gold_light"], fx + 1, sy - 6, fx + 1, sy - 3)
    px_rect(art, P["gold_mid"], fx - 3, sy + 2, 6, 1)


def render_head(art, pose):
    """Tengkorak air berahang + leher. Return (hx, hy) untuk face/crown."""
    P = _P
    ox, oy = AX, AY
    hx = ox + int(round(pose.head_dx + pose.lean * 0.45))
    hy = oy + int(-42 * pose.sqy) + int((pose.bob + pose.head_dy) * 0.5)
    px_rect(art, P["water_dark"], hx - 2, hy + 5, 4, 3)
    px_set(art, P["water_darkest"], hx - 2, hy + 6)
    px_poly(art, P["water_darkest"],
            [(hx - 6, hy + 1), (hx - 6, hy - 3), (hx - 4, hy - 6),
             (hx + 4, hy - 6), (hx + 6, hy - 3), (hx + 6, hy + 1),
             (hx + 4, hy + 5), (hx - 4, hy + 5)])
    px_poly(art, P["water_dark"],
            [(hx - 5, hy + 1), (hx - 5, hy - 3), (hx - 3, hy - 5),
             (hx + 3, hy - 5), (hx + 5, hy - 3), (hx + 5, hy + 1),
             (hx + 3, hy + 4), (hx - 3, hy + 4)])
    px_rect(art, P["water_mid"], hx - 4, hy - 4, 8, 7)
    px_rect(art, P["water_light"], hx + 1, hy - 4, 3, 6)
    px_rect(art, P["water_high"], hx + 3, hy - 4, 1, 5)
    px_set(art, P["water_shine"], hx + 3, hy - 4)
    px_poly(art, P["water_dark"],
            [(hx - 3, hy + 4), (hx, hy + 6), (hx + 3, hy + 4)])
    return hx, hy


def render_face(art, pose, hx, hy):
    """Void wajah + mata menyala menyipit + brow + mulut."""
    P = _P
    vx = hx + 1
    px_poly(art, P["face_void"],
            [(vx - 4, hy - 2), (vx - 3, hy - 4), (vx + 3, hy - 4),
             (vx + 4, hy - 2), (vx + 3, hy + 2), (vx - 3, hy + 2)])
    px_line(art, P["face_rim"], vx - 4, hy + 2, vx + 4, hy + 2)
    px_line(art, P["eye_dark"], vx - 4, hy - 4, vx - 1, hy - 3)
    px_line(art, P["eye_dark"], vx + 4, hy - 4, vx + 1, hy - 3)
    e = pose.eye
    if e > 0.05:
        bright = P["eye_bright"] if e > 0.5 else P["eye_mid"]
        ex = vx + 2
        # mata depan: cyan menyala dengan inti panas (bukan putih polos)
        px_rect(art, P["eye_mid"], ex - 1, hy - 2, 3, 1)
        px_set(art, P["eye_hot"], ex, hy - 2)
        px_set(art, bright, ex + 1, hy - 2)
        px_set(art, P["eye_dark"], ex - 1, hy - 1)
        px_set(art, P["eye_dark"], ex + 1, hy - 3)
        # mata belakang lebih redup (depth)
        ex2 = vx - 3
        px_rect(art, P["eye_dark"], ex2 - 1, hy - 2, 2, 1)
        px_set(art, P["eye_mid"], ex2, hy - 2)
        if e > 0.85:
            px_set(art, P["eye_dark"], ex + 2, hy - 2)
    if pose.mouth > 0.3:
        px_rect(art, P["face_void"], vx - 1, hy + 1, 3, 1)
        px_set(art, P["eye_dark"], vx, hy + 1)
    else:
        px_line(art, P["face_rim"], vx - 1, hy + 1, vx + 2, hy + 1)


def render_crown(art, pose, hx, hy):
    """Mahkota raja-tenggelam: band emas + 3 duri + gem pasang."""
    P = _P
    cy = hy - 6 + int(round(pose.crown))
    px_rect(art, P["gold_dark"], hx - 5, cy - 1, 10, 2)
    px_rect(art, P["gold_mid"], hx - 5, cy - 2, 10, 1)
    px_rect(art, P["gold_light"], hx - 4, cy - 2, 8, 1)
    px_set(art, P["gold_shine"], hx - 2, cy - 2)
    for dx, hgt in ((-3, 4), (0, 6), (3, 4)):
        px_poly(art, P["gold_mid"],
                [(hx + dx - 1, cy - 2), (hx + dx, cy - 2 - hgt),
                 (hx + dx + 1, cy - 2)])
        px_line(art, P["gold_light"], hx + dx - 1, cy - 3,
                hx + dx, cy - 2 - hgt)
        px_set(art, P["gold_shine"], hx + dx, cy - 2 - hgt)
    gy = cy - 3
    px_set(art, P["core_mid"], hx, gy)
    if pose.core > 0.5:
        px_set(art, P["core_hot"], hx, gy)


def render_arms(art, pose):
    """Lengan belakang (siap) + lengan depan (ke grip) + bracer emas."""
    P = _P
    ox, oy = AX, AY
    sy = oy + int(-32 * pose.sqy) + int(pose.bob * 0.25)
    sx = ox + int(round(pose.lean * 0.3))
    swb = math.sin(pose.phase * 1.4) * 1.2
    bx0, by0 = sx - 6, sy + 1
    bx1, by1 = sx - 4 + int(swb), sy + 7
    px_line(art, P["water_darkest"], bx0, by0, bx1, by1)
    px_line(art, P["water_dark"], bx0, by0, bx1 - 1, by1)
    px_rect(art, P["gold_mid"], bx1 - 1, by1 - 2, 3, 2)
    px_set(art, P["gold_light"], bx1 - 1, by1 - 2)
    px_circle(art, P["water_mid"], bx1, by1 + 1, 1)
    gx = ox + int(round(pose.grip_x * pose.sqx + pose.lean * 0.4))
    gy = oy + int(pose.grip_y * pose.sqy) + int(pose.bob * 0.2)
    ex, ey = (sx + 6 + gx) // 2 + 1, (sy + gy) // 2 + 2
    px_line(art, P["water_darkest"], sx + 6, sy + 1, ex, ey)
    px_line(art, P["water_mid"], sx + 6, sy, ex, ey - 1)
    px_line(art, P["water_darkest"], ex, ey, gx, gy)
    px_line(art, P["water_light"], ex, ey - 1, gx, gy - 1)
    px_rect(art, P["gold_dark"], gx - 2, gy - 1, 4, 3)
    px_rect(art, P["gold_mid"], gx - 2, gy - 1, 4, 2)
    px_set(art, P["gold_light"], gx - 1, gy - 1)
    px_circle(art, P["water_mid"], gx, gy, 2)
    px_set(art, P["water_light"], gx, gy - 1)
    return gx, gy


def render_weapon(art, pose, gx, gy):
    """TIDE GLAIVE: haft baja 2-px bercincin emas + bilah sabit air.

    Bilah dibentuk sebagai polygon meruncing (lebar basis -> ujung runcing)
    dengan punggung gelap, badan mid, fuller dither TER-MASK, dan mata
    bilah 1 px TERANG di sisi potong — terbaca sebagai senjata sungguhan,
    bukan kipas / jaring.
    """
    P = _P
    a = pose.w_ang
    ca, sa = math.cos(a), math.sin(a)
    # normal (sisi potong / luar)
    nx, ny = -sa, ca
    haft, blade = 26.0, 16.0
    # ── haft: 2 px solid (gelap + mid) + kilau tipis ──
    x0, y0 = gx - ca * 6, gy - sa * 6
    x1, y1 = gx + ca * haft, gy + sa * haft
    px_line(art, P["steel_dark"], x0, y0, x1, y1)
    px_line(art, P["steel_mid"], x0 + nx, y0 + ny, x1 + nx, y1 + ny)
    for t in (0.2, 0.45, 0.7, 0.9):
        px_set(art, P["steel_light"], x0 + (x1 - x0) * t + nx,
               y0 + (y1 - y0) * t + ny)
    # pommel emas
    px_circle(art, P["gold_mid"], x0, y0, 1)
    px_set(art, P["gold_light"], x0, y0 - 1)
    # cincin emas di haft
    for t in (0.30, 0.64):
        rx, ry = gx + ca * haft * t, gy + sa * haft * t
        px_set(art, P["gold_mid"], rx, ry)
        px_set(art, P["gold_light"], rx + nx, ry + ny)
    # ── collar emas + gem di pangkal bilah ──
    cx, cy = x1, y1
    px_circle(art, P["gold_dark"], cx, cy, 2)
    px_circle(art, P["gold_mid"], cx, cy, 1)
    px_set(art, P["core_light"], cx, cy)
    # duri punggung emas kecil (siluet)
    px_poly(art, P["gold_mid"],
            [(cx - nx * 2 - ca, cy - ny * 2 - sa),
             (cx - nx * 5, cy - ny * 5),
             (cx - nx * 2 + ca, cy - ny * 2 + sa)])
    # ── bilah: rantai disc meruncing melengkung (solid di semua sudut) ──
    edge, back = [], []
    steps = 10
    for i in range(steps + 1):
        t = i / float(steps)
        # garis tengah bilah melengkung (curve ke arah potong)
        along = 2.0 + t * blade
        curve = math.sin(t * math.pi * 0.85) * 3.2
        mx = cx + ca * along + nx * curve
        my = cy + sa * along + ny * curve
        # lebar menurun ke ujung runcing
        wdt = 3.4 * (1.0 - t) ** 0.85 + 0.4
        # badan solid lewat disc (polygon bisa degenerasi di sudut tertentu)
        px_circle(art, P["blade_darkest"], mx, my, int(wdt + 0.9))
        if wdt >= 1.7:
            px_circle(art, P["blade_mid"], mx + nx * 0.4, my + ny * 0.4,
                      int(wdt - 0.6))
        edge.append((mx + nx * wdt, my + ny * wdt))
        back.append((mx - nx * 0.9, my - ny * 0.9))
    # fuller: dither TER-MASK di badan bilah
    xs = [p[0] for p in edge] + [p[0] for p in back]
    ys = [p[1] for p in edge] + [p[1] for p in back]
    px_dither(art, P["blade_light"], min(xs), min(ys),
              max(2, max(xs) - min(xs)), max(2, max(ys) - min(ys)),
              0, 3, masked=True)
    # mata bilah 1 px TERANG di sisi potong
    for i in range(steps):
        px_line(art, P["blade_shine"], edge[i][0], edge[i][1],
                edge[i + 1][0], edge[i + 1][1])
    # punggung gelap
    for i in range(steps):
        px_line(art, P["blade_dark"], back[i][0], back[i][1],
                back[i + 1][0], back[i + 1][1])
    # ujung runcing: pixel putih panas
    px_set(art, P["water_white"], edge[steps][0], edge[steps][1])
    px_set(art, P["blade_shine"], edge[steps - 1][0], edge[steps - 1][1])
    return edge


def render_fist(art, pose, gx, gy):
    """Kepalan air DI ATAS haft (tangan menggenggam, bukan tertimpa)."""
    P = _P
    px_circle(art, P["water_dark"], gx, gy, 2)
    px_circle(art, P["water_mid"], gx, gy, 1)
    px_set(art, P["water_light"], gx, gy - 1)
    px_set(art, P["water_high"], gx + 1, gy - 1)


def render_highlight(art, pose):
    """Rim light + specular (pseudo-3D depth)."""
    P = _P
    ox, oy = AX, AY
    b = int(pose.bob * 0.3)
    hx = ox + int(round(pose.head_dx + pose.lean * 0.45))
    hy = oy + int(-42 * pose.sqy) + int((pose.bob + pose.head_dy) * 0.5)
    px_line(art, P["water_high"], hx - 5, hy - 5, hx - 2, hy - 6)
    px_set(art, P["water_shine"], hx - 4, hy - 5)
    sy = oy + int(-33 * pose.sqy) + b
    sx = ox + int(round(pose.lean * 0.3))
    px_line(art, P["water_high"], sx - 11, sy - 3, sx - 7, sy - 4)
    px_set(art, P["water_shine"], sx - 9, sy - 4)
    if pose.core > 0.6:
        px_set(art, P["core_light"], ox, oy + int(-24 * pose.sqy))
        px_set(art, P["core_mid"], ox, oy + int(-22 * pose.sqy))


def render_outline(art, color=None):
    """Outline 1 art-px lewat mask 8 arah. Return mask (dipakai flash)."""
    if not HAS_MASK:
        return None
    col = color or (_P["outline"] + (255,))
    m = pygame.mask.from_surface(art, 40)
    sil = m.to_surface(setcolor=col, unsetcolor=(0, 0, 0, 0))
    base = pygame.Surface(art.get_size(), pygame.SRCALPHA)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1),
                   (-1, -1), (1, -1), (-1, 1), (1, 1)):
        base.blit(sil, (dx, dy))
    base.blit(art, (0, 0))
    art.blit(base, (0, 0))
    return m


def render_hit_flash(art, mask, amount):
    """Flash putih saat kena damage (silhouette di-tint, bukan overlay)."""
    if mask is None or amount <= 0.02:
        return
    # alpha dijaga <=165 supaya shading & detail tetap terbaca di
    # bawah flash (flash penuh membuat silhouette jadi blob putih)
    a = int(165 * min(1.0, amount))
    flash = mask.to_surface(setcolor=(244, 252, 255, a),
                            unsetcolor=(0, 0, 0, 0))
    art.blit(flash, (0, 0))


def render_status(art, mask, pose):
    """Overlay status: rim atribut saat buff morph aktif."""
    if mask is None or pose.morph <= 0.05:
        return
    cols = (_P["str_hot"], _P["agi_hot"], _P["int_hot"])
    col = cols[pose.morph_idx % 3]
    a = int(70 * pose.morph)
    tint = mask.to_surface(setcolor=col + (a,), unsetcolor=(0, 0, 0, 0))
    art.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)


def render_dissolve(art, k, seed=7):
    """Erosi alpha baris-demi-baris (death collapse / spawn rise).

    Memakai slice PixelArray (C-level) supaya murah: bukan loop per-pixel
    Python. Pola tangga 1/2/3 px menjaga kluster pixel tetap terkontrol.
    """
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


def render_orbit(surface, x, y, pose, scale=1.0):
    """Droplet equipment mengorbit badan (ruang dunia)."""
    P = _P
    for i in range(5):
        a = pose.droplet * 1.3 + i * 1.2566
        r = (15 + 3 * math.sin(pose.droplet + i)) * scale
        dx = int(x + math.cos(a) * r)
        dy = int(y - 22 * scale + math.sin(a) * r * 0.38)
        s = 2 if i & 1 else 1
        px_rect(surface, P["water_mid"] + (200,), dx - s // 2, dy - s // 2,
                s, s)
        px_set(surface, P["water_high"] + (220,), dx, dy - 1)


# ============================================================================
# 7. NAMESPACE: konstanta, controller animasi, geometri, entry point
# ============================================================================
class _NS_thalgryn:
    """Namespace renderer Thalgryn v4 (pixel-art, delta-time)."""

    HAS_AACIRCLE = False          # v4 TIDAK memakai anti-alias sama sekali
    HAS_AALINES = False
    _STATIC_SURFACES = {}

    SCALE = 1.0
    LIFT = 0
    FEET_DY = 0
    GROUND_DY = 0                 # telapak vortex = titik dunia (x, y)

    AW, AH = AW, AH
    AX, AY = AX, AY
    PX = PX

    #: durasi status skill (frame) — SINKRON base_boss & hero_skills
    SKILL_DUR = {"q": 60, "w": 50, "e": 60, "r": 80}

    #: jarak tebasan bilah vs lemparan spear (piksel dunia)
    MELEE_REACH = 78

    ATTACK_ANTICIPATION_END = 0.14
    ATTACK_WINDUP_END = 0.30
    ATTACK_SWING_END = 0.48
    ATTACK_IMPACT_END = 0.62
    ATTACK_FOLLOW_END = 0.82
    ATTACK_ACTIVE_WINDOW = (0.34, 0.62)
    ATTACK_IMPACT_FRAME = 0.52

    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, 0.14),
        ("WINDUP",       0.14, 0.30),
        ("SWING",        0.30, 0.48),
        ("IMPACT",       0.48, 0.62),
        ("FOLLOW",       0.62, 0.82),
        ("RECOVERY",     0.82, 1.00),
    )

    ANIM_STATES = {
        "IDLE": 0,
        "WALK": 10,
        "RUN": 15,
        "CHARGE": 30,
        "CAST": 35,
        "ATTACK": 40,
        "SWING": 45,
        "SKILL": 50,
        "SPECIAL": 55,
        "VICTORY": 58,
        "HIT": 60,
        "HURT": 65,
        "SPAWN": 70,
        "DEATH": 100,
    }

    DEBUG_CHARACTER = False

    PALETTE = PALETTE

    #: modul FX hidup (lazy; False = gagal -> canvas fallback)
    _LIVE_MOD = None

    # ── buffer art bersama + cache frame terakhir per unit ───────────
    _ART_BUF = None
    _LAST_ART = {}

    # ==================================================================
    # FASE / KURVA
    # ==================================================================
    def attack_phases_order():
        return tuple(name for name, _a, _b in _NS_thalgryn.ATTACK_PHASES)

    def attack_phase(progress):
        if progress is None:
            return "NONE"
        p = max(0.0, min(1.0, float(progress)))
        for name, a, b in _NS_thalgryn.ATTACK_PHASES:
            if a <= p < b:
                return name
        return "RECOVERY"

    def _attack_curve(raw):
        """Progress geometri ayunan: ease-in-out (akselerasi di tengah)."""
        t = _clamp(raw)
        return t * t * (3.0 - 2.0 * t)

    # ==================================================================
    # GEOMETRI SENJATA (TIDE GLAIVE) — sumber tunggal rig & FX
    # ==================================================================
    _W_REST = -1.13
    _W_DIP = -1.42
    _W_TOP = -2.18
    _W_HIT = 0.42
    _W_FOLLOW = 1.05
    _HAFT = 26.0
    _BLADE = 18.0

    def _weapon_angle(action, phase, ap, skill=None, skill_p=0.0,
                      victory=0.0):
        G = _NS_thalgryn
        if victory > 0.0:
            k = _ease_out(min(1.0, victory * 2.2))
            return _lerp(G._W_REST, -1.95, k) + math.sin(phase * 2.0) * 0.03
        if skill == "w":
            if skill_p < 0.35:
                return _lerp(G._W_REST, -1.75, _ease_out(skill_p / 0.35))
            if skill_p < 0.55:
                return _lerp(-1.75, -0.15, _ease_in(_seg(skill_p, .35, .55)))
            return _lerp(-0.15, G._W_REST,
                         _ease_in_out(_seg(skill_p, .55, 1)))
        if skill == "q":
            return _lerp(G._W_REST, -0.35, _ease_out(min(1.0, skill_p * 2)))
        if skill == "e":
            return _lerp(G._W_REST, -1.85, _ease_out(min(1.0, skill_p * 1.8)))
        if skill == "r":
            return _lerp(G._W_REST, -2.05,
                         _ease_out(min(1.0, skill_p * 2))) \
                + math.sin(phase * 6.0) * 0.05
        if action != "attack":
            return G._W_REST + math.sin(phase * 0.9) * 0.045
        if ap < 0.14:
            return _lerp(G._W_REST, G._W_DIP, _ease_out(_seg(ap, 0.0, 0.14)))
        if ap < 0.30:
            return _lerp(G._W_DIP, G._W_TOP, _ease_out(_seg(ap, 0.14, 0.30)))
        if ap < 0.48:
            return _lerp(G._W_TOP, G._W_HIT, _ease_in(_seg(ap, 0.30, 0.48)))
        if ap < 0.62:
            # IMPACT HOLD: sudut hampir ditahan -> baca sebagai "bobot"
            return _lerp(G._W_HIT, G._W_HIT + 0.22,
                         _ease_out(_seg(ap, 0.48, 0.62)))
        if ap < 0.82:
            return _lerp(G._W_HIT + 0.22, G._W_FOLLOW,
                         _ease_out(_seg(ap, 0.62, 0.82)))
        return _lerp(G._W_FOLLOW, G._W_REST, _ease_in_out(_seg(ap, 0.82, 1)))

    def _grip_local(action, phase, ap, skill=None, skill_p=0.0,
                    recoil=0.0, lean=0.0):
        gx, gy = 7.0, -26.0
        if action == "attack":
            if ap < 0.30:
                k = _ease_out(_seg(ap, 0.0, 0.30))
                gx = _lerp(7.0, 2.0, k)
                gy = _lerp(-26.0, -30.0, k)
            elif ap < 0.62:
                k = _ease_in(_seg(ap, 0.30, 0.62))
                gx = _lerp(2.0, 10.0, k)
                gy = _lerp(-30.0, -24.0, k)
            else:
                k = _ease_in_out(_seg(ap, 0.62, 1.0))
                gx = _lerp(10.0, 7.0, k)
                gy = _lerp(-24.0, -26.0, k)
        elif skill == "w" and skill_p < 0.55:
            gx = _lerp(7.0, 11.0, _ease_out(min(1.0, skill_p * 2.4)))
            gy = -27.0
        gx -= recoil * 2.0
        return gx + lean * 0.4, gy

    def _tip_local(action, phase, ap, skill=None, skill_p=0.0,
                   victory=0.0, recoil=0.0, lean=0.0):
        G = _NS_thalgryn
        gx, gy = G._grip_local(action, phase, ap, skill, skill_p, recoil,
                               lean)
        a = G._weapon_angle(action, phase, ap, skill, skill_p, victory)
        L = G._HAFT + G._BLADE
        return (gx + math.cos(a) * L, gy + math.sin(a) * L)

    def _blade_mid_local(action, phase, ap, skill=None, skill_p=0.0,
                         victory=0.0, recoil=0.0, lean=0.0):
        G = _NS_thalgryn
        gx, gy = G._grip_local(action, phase, ap, skill, skill_p, recoil,
                               lean)
        a = G._weapon_angle(action, phase, ap, skill, skill_p, victory)
        return (gx + math.cos(a) * (G._HAFT + G._BLADE * 0.5),
                gy + math.sin(a) * (G._HAFT + G._BLADE * 0.5))

    # ==================================================================
    # ANIMATION CONTROLLER (delta-time)
    # ==================================================================
    def _update_thalgryn_attack_anim(boss):
        """SATU sumber kebenaran state animasi Thalgryn (delta-time)."""
        G = _NS_thalgryn
        try:
            now = pygame.time.get_ticks()
        except Exception:                              # pragma: no cover
            now = 0
        prev_ms = getattr(boss, "_th_last_ms", None)
        if prev_ms is None:
            dt = 1.0 / 60.0
        else:
            dt = (now - prev_ms) / 1000.0
            if dt <= 0.0 or dt > 0.05:
                dt = 1.0 / 60.0
        boss._th_last_ms = now
        boss._th_dt = dt
        boss._th_time = float(getattr(boss, "_th_time", 0.0)) + dt

        cooldown = max(2, int(getattr(boss, "attack_cooldown", 44)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_th_previous_timer", 0))
        active = bool(getattr(boss, "_th_attack_active", False))

        triggered = timer >= cooldown - 1 and previous <= 1
        if triggered:
            boss._th_attack_active = True
            boss._th_attack_frame = 0
            boss._th_attack_manual = False
            active = True
        elif active and timer > 0:
            boss._th_attack_frame = int(getattr(boss, "_th_attack_frame",
                                                0)) + 1
            boss._th_attack_manual = False
        elif timer <= 0:
            if active and not getattr(boss, "_th_attack_manual", False) \
                    and float(getattr(boss, "_th_attack_progress", 0.0)) > 0:
                boss._th_attack_manual = True
                active = True
            elif not getattr(boss, "_th_attack_manual", False):
                boss._th_attack_active = False
                boss._th_attack_frame = 0
                active = False
            if not active:
                boss._th_attack_active = False
                boss._th_attack_frame = 0

        boss._th_previous_timer = timer
        frame = int(getattr(boss, "_th_attack_frame", 0)) if active else 0
        span = max(1, cooldown - 1)
        boss._th_attack_frame = frame
        if bool(getattr(boss, "_th_attack_manual", False)) and active:
            progress = min(1.0, max(0.0, float(getattr(
                boss, "_th_attack_progress", 0.0))))
            boss._th_attack_frame = int(round(progress * span))
        else:
            progress = min(1.0, frame / float(span)) if active else 0.0
            boss._th_attack_progress = progress
        boss._th_attack_raw = progress

        if not getattr(boss, "_th_attack_active", False):
            boss._th_attack_active = False
            boss._th_attack_manual = False
            active = False
        phase = G.attack_phase(progress) if active else "NONE"
        boss._th_attack_phase = phase
        lo, hi = G.ATTACK_ACTIVE_WINDOW
        boss._th_hit_active = bool(active and lo <= progress < hi)

        # ── respons kena damage (HURT) ──
        hurt = int(getattr(boss, "_th_hurt_frames", 0))
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        if flash >= 8 and hurt <= 0:
            hurt = 10
        boss._th_hurt_frames = max(0, hurt - 1) if hurt > 0 else 0
        boss._th_hurt_t = max(0.0, min(1.0, hurt / 10.0))

        # ── jam spawn / death / victory ──
        if not getattr(boss, "alive", True):
            boss._th_death_t = min(1.0, float(getattr(boss, "_th_death_t",
                                                      0.0)) + dt / 1.15)
        else:
            boss._th_death_t = 0.0
        sp = getattr(boss, "_th_spawn_t", None)
        if sp is None:
            boss._th_spawn_t = 1.0
            if getattr(boss, "_th_want_spawn", False):
                boss._th_spawn_t = 0.0001
        elif 0.0 < sp < 1.0:
            boss._th_spawn_t = min(1.0, sp + dt / 0.85)
        vic = float(getattr(boss, "_th_victory_t", 0.0))
        if getattr(boss, "_victory", False) or getattr(boss, "victory",
                                                       False):
            vic = min(1.0, vic + dt / 0.7)
        else:
            vic = max(0.0, vic - dt / 0.4)
        boss._th_victory_t = vic

        # ── state machine ber-prioritas ──
        want = G._resolve_anim_state(boss, active, phase)
        cur = getattr(boss, "_th_state", None)
        if cur is None:
            boss._th_state = want
            boss._th_state_prev = want
            boss._th_state_time = 0.0
        elif want != cur:
            cur_p = G.ANIM_STATES.get(cur, 0)
            new_p = G.ANIM_STATES.get(want, 0)
            stime = float(getattr(boss, "_th_state_time", 0.0))
            if cur != "DEATH" and (new_p >= cur_p or stime > 0.08):
                boss._th_state_prev = cur
                boss._th_state = want
                boss._th_state_time = 0.0
            else:
                boss._th_state_time = stime + dt
        else:
            boss._th_state_time = float(getattr(boss, "_th_state_time",
                                                0.0)) + dt

    def _resolve_anim_state(boss, attacking, phase):
        G = _NS_thalgryn
        if not getattr(boss, "alive", True):
            return "DEATH"
        if 0.0 < float(getattr(boss, "_th_spawn_t", 1.0)) < 1.0:
            return "SPAWN"
        if int(getattr(boss, "_th_hurt_frames", 0)) > 0:
            return "HURT"
        if float(getattr(boss, "_th_victory_t", 0.0)) > 0.05:
            return "VICTORY"
        skill = getattr(boss, "active_skill", None)
        if skill:
            return "SPECIAL" if skill == "r" else "SKILL"
        if attacking:
            if phase in ("ANTICIPATION", "WINDUP"):
                return "CHARGE"
            if phase in ("SWING", "IMPACT"):
                return "SWING"
            return "ATTACK"
        if getattr(boss, "_moving_cached", False):
            return "RUN" if float(getattr(boss, "speed", 1.0)) >= 2.2 \
                else "WALK"
        return "IDLE"

    def _detect_moving(boss):
        cur_x = float(getattr(boss, "x", 0.0))
        cur_y = float(getattr(boss, "y", 0.0))
        if not hasattr(boss, "_th_last_x"):
            boss._th_last_x = cur_x
            boss._th_last_y = cur_y
            boss._moving_cached = False
            return False
        moved = abs(cur_x - boss._th_last_x) + abs(cur_y - boss._th_last_y)
        boss._th_last_x = cur_x
        boss._th_last_y = cur_y
        moving = moved > 0.3
        boss._moving_cached = moving
        return moving

    # ==================================================================
    # POSE SOLVER
    # ==================================================================
    def solve_pose(boss, moving=False):
        G = _NS_thalgryn
        p = Pose()
        p.dt = float(getattr(boss, "_th_dt", 1.0 / 60.0))
        p.phase = float(getattr(boss, "pulse", 0.0))
        p.facing = 1 if int(getattr(boss, "direction", 1) or 1) >= 0 else -1
        p.state = getattr(boss, "_th_state", "IDLE")
        p.t = float(getattr(boss, "_th_state_time", 0.0))
        p.flash = float(getattr(boss, "_th_hurt_t", 0.0))
        p.death = float(getattr(boss, "_th_death_t", 0.0))
        p.spawn = float(getattr(boss, "_th_spawn_t", 1.0))
        if p.spawn <= 0.0:
            p.spawn = 1.0
        p.victory = float(getattr(boss, "_th_victory_t", 0.0))
        p.skill = getattr(boss, "active_skill", None)
        if p.skill in G.SKILL_DUR:
            dur = G.SKILL_DUR[p.skill]
            timer = int(getattr(boss, "active_skill_timer", 0))
            p.skill_p = _clamp(1.0 - timer / float(dur))
        else:
            p.skill = None
        p.morph = 1.0 if getattr(boss, "morph_buff_active", False) else 0.0
        p.morph_idx = int(getattr(boss, "morph_cycle", 0) or 0) % 3
        p.hurt_k = p.flash

        active = bool(getattr(boss, "_th_attack_active", False))
        raw = float(getattr(boss, "_th_attack_progress", 0.0)) if active \
            else 0.0
        p.ap = G._attack_curve(raw) if active else 0.0

        tm = float(getattr(boss, "_th_time", 0.0))
        p.mantle = tm * 3.1
        p.tail = tm * 4.3
        p.droplet = tm * 2.2

        st = p.state
        breathe = math.sin(p.phase * 0.9)
        p.bob = breathe * 1.1
        p.sqx = 1.0 + breathe * 0.012
        p.sqy = 1.0 - breathe * 0.016
        p.head_dy = breathe * 0.7
        p.core = 0.55 + 0.25 * (0.5 + 0.5 * math.sin(p.phase * 1.3))
        p.eye = 0.85
        p.crown = breathe * 0.4

        if st in ("WALK", "RUN"):
            fast = 1.55 if st == "RUN" else 1.0
            w = p.phase * 2.1 * fast
            p.bob = -abs(math.sin(w)) * (1.9 if st == "RUN" else 1.2)
            p.lean = 1.6 if st == "RUN" else 0.8
            p.sqx = 1.02
            p.sqy = 0.985
            p.head_dy = math.sin(w * 2.0) * 0.6
            p.head_dx = 0.5
            p.core = 0.75
        elif st == "CHARGE":
            k = _ease_out(_seg(p.ap, 0.0, 0.30))
            p.bob = 1.8 * k
            p.lean = -2.2 * k
            p.sqx = 1.0 + 0.06 * k
            p.sqy = 1.0 - 0.08 * k
            p.head_dx = -0.8 * k
            p.core = 0.6 + 0.5 * k
            p.eye = 1.0
            p.recoil = 0.4 * k
        elif st == "SWING":
            k = _ease_in(_seg(p.ap, 0.30, 0.52))
            h = _ease_out(_seg(p.ap, 0.52, 0.72))
            p.bob = 1.2 * k - 0.8 * h
            p.lean = 3.4 * k - 1.2 * h
            p.sqx = 1.0 - 0.05 * k + 0.07 * h
            p.sqy = 1.0 + 0.07 * k - 0.06 * h
            p.head_dx = 1.4 * k
            p.mouth = 1.0
            p.core = 1.0
            p.eye = 1.0
            p.recoil = 0.8 * h
        elif st == "ATTACK":
            k = _ease_out(_seg(p.ap, 0.62, 1.0))
            p.lean = 2.2 * (1.0 - k)
            p.bob = 0.6 * (1.0 - k)
            p.mouth = 0.5 * (1.0 - k)
            p.core = 0.9 - 0.2 * k
        elif st in ("SKILL", "SPECIAL", "CAST"):
            sp = p.skill_p
            if p.skill == "q":
                k = _ease_out(_seg(sp, 0.0, 0.25))
                p.bob = 2.0 * k
                p.lean = 3.0 * _ease_in(_seg(sp, 0.18, 0.45)) - 1.5 * k
                p.sqy = 1.0 - 0.07 * k
            elif p.skill == "w":
                k = _ease_out(_seg(sp, 0.0, 0.35))
                p.lean = -1.6 * k + 4.0 * _ease_in(_seg(sp, 0.35, 0.6))
                p.bob = 1.0 * k
                p.recoil = 1.0 * _ease_out(_seg(sp, 0.42, 0.62))
            elif p.skill == "e":
                k = _ease_out(_seg(sp, 0.0, 0.4))
                p.bob = -1.6 * k
                p.sqx = 1.0 + 0.05 * k
                p.sqy = 1.0 + 0.06 * k
                p.eye = 1.0
            else:
                k = _ease_out(_seg(sp, 0.0, 0.3))
                p.bob = -2.2 * k
                p.sqy = 1.0 + 0.08 * k
                p.eye = 1.0
                p.mouth = k
            p.core = 1.0
            p.mouth = max(p.mouth, 0.7)
        elif st == "HURT":
            k = p.hurt_k
            p.lean = -3.0 * k
            p.bob = 1.0 * k
            p.head_dx = -1.6 * k
            p.head_dy = -0.6 * k
            p.sqx = 1.0 + 0.05 * k
            p.sqy = 1.0 - 0.05 * k
            p.mouth = 1.0 * k
            p.eye = 0.5
            p.core = 0.4
        elif st == "VICTORY":
            k = _ease_out(min(1.0, p.victory * 1.6))
            p.bob = -1.6 * k + math.sin(p.phase * 2.2) * 0.7 * k
            p.core = 1.0
            p.eye = 1.0
            p.mouth = 0.4 * k
        elif st == "SPAWN":
            k = _ease_out(p.spawn)
            over = math.sin(min(1.0, p.spawn) * math.pi) * 0.10
            p.sqy = 0.35 + 0.65 * k + over
            p.sqx = 1.35 - 0.35 * k - over * 0.6
            p.bob = (1.0 - k) * 10.0
            p.core = k
            p.eye = k
        elif st == "DEATH":
            k = _ease_in_out(p.death)
            p.sqy = max(0.12, 1.0 - 0.95 * k)
            p.sqx = 1.0 + 0.85 * k
            p.bob = 12.0 * k
            p.core = max(0.0, 1.0 - k * 1.4)
            p.eye = max(0.0, 1.0 - k * 1.8)
            p.head_dy = 3.0 * k

        gx, gy = G._grip_local("attack" if active else "idle", p.phase,
                               p.ap, p.skill, p.skill_p, p.recoil, p.lean)
        p.grip_x, p.grip_y = gx, gy
        p.w_ang = G._weapon_angle("attack" if active else "idle", p.phase,
                                  p.ap, p.skill, p.skill_p, p.victory)
        return p

    def _resolve_pose(boss, moving=False):
        """Kompat lama: (action, phase, ap)."""
        G = _NS_thalgryn
        p = getattr(boss, "_th_pose", None)
        if p is None:
            p = G.solve_pose(boss, moving)
        active = bool(getattr(boss, "_th_attack_active", False))
        if p.skill == "q":
            action = "waveform"
        elif p.skill == "w":
            action = "adaptive"
        elif p.skill == "e":
            action = "morph"
        elif p.skill == "r":
            action = "replicate"
        elif active:
            action = "attack"
        elif moving or getattr(boss, "_moving_cached", False):
            action = "walk"
        else:
            action = "idle"
        return action, p.phase, p.ap

    # ==================================================================
    # KONVERSI RUANG (anchor FX eksternal)
    # ==================================================================
    def _fx_scale(boss):
        v = getattr(boss, "_render_scale", None)
        try:
            return float(v) if v else 1.0
        except (TypeError, ValueError):
            return 1.0

    def _ring_r(boss, world_r):
        return max(1, int(round(float(world_r) *
                                _NS_thalgryn._fx_scale(boss))))

    def _local_to_screen(x, y, facing, pose, lx, ly):
        """Local art-px (telapak=0,0) -> piksel dunia."""
        f = 1 if facing >= 0 else -1
        bx = lx * pose.sqx + pose.lean * 0.6
        by = ly * pose.sqy + pose.bob
        return (x + bx * f, y + by)

    def _local(boss, x, y, action, phase, ap, lx, ly):
        G = _NS_thalgryn
        pose = getattr(boss, "_th_pose", None) or Pose()
        return G._local_to_screen(x, y, pose.facing, pose, lx, ly)

    def _world_to_local(boss, x, y, wx, wy):
        pose = getattr(boss, "_th_pose", None) or Pose()
        f = 1 if pose.facing >= 0 else -1
        lx = (wx - x) * f
        ly = (wy - y)
        if abs(pose.sqx) > 1e-4:
            lx = (lx - pose.lean * 0.6) / pose.sqx
        if abs(pose.sqy) > 1e-4:
            ly = (ly - pose.bob) / pose.sqy
        return lx, ly

    def _tip_screen(boss, x, y):
        G = _NS_thalgryn
        pose = getattr(boss, "_th_pose", None)
        if pose is None:
            pose = G.solve_pose(boss)
        lx, ly = G._tip_local("attack" if pose.ap > 0 else "idle",
                              pose.phase, pose.ap, pose.skill, pose.skill_p,
                              pose.victory, pose.recoil, pose.lean)
        return G._local_to_screen(x, y, pose.facing, pose, lx, ly)

    def _grip_screen(boss, x, y):
        G = _NS_thalgryn
        pose = getattr(boss, "_th_pose", None) or G.solve_pose(boss)
        return G._local_to_screen(x, y, pose.facing, pose,
                                  pose.grip_x, pose.grip_y)

    def _head_screen(boss, x, y):
        G = _NS_thalgryn
        pose = getattr(boss, "_th_pose", None) or G.solve_pose(boss)
        return G._local_to_screen(x, y, pose.facing, pose,
                                  pose.head_dx + pose.lean * 0.45, -42)

    def _target_position(boss, x, y):
        t = getattr(boss, "target", None)
        if t is not None and getattr(t, "alive", False):
            return int(getattr(t, "x", x)), int(getattr(t, "y", y))
        f = 1 if int(getattr(boss, "direction", 1) or 1) >= 0 else -1
        return int(x + 160 * f), int(y)

    def _swing_hitbox(boss, cx, cy):
        G = _NS_thalgryn
        if not getattr(boss, "_th_hit_active", False):
            return None
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        scale = G._fx_scale(boss)
        reach = int(58 * scale)
        top = int(cy - 40 * scale)
        h = int(66 * scale)
        left = int(cx) if f > 0 else int(cx) - reach
        return pygame.Rect(left, top, max(8, reach), max(10, h))

    # ==================================================================
    # CACHE
    # ==================================================================
    def _static(key, w, h, painter):
        G = _NS_thalgryn
        s = G._STATIC_SURFACES.get(key)
        if s is None:
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            painter(s)
            if len(G._STATIC_SURFACES) > 48:
                G._STATIC_SURFACES.clear()
            G._STATIC_SURFACES[key] = s
        return s

    def clear_cache():
        _NS_thalgryn._STATIC_SURFACES.clear()
        _NS_thalgryn._LAST_ART.clear()

    def _art_buffer():
        G = _NS_thalgryn
        if G._ART_BUF is None:
            G._ART_BUF = pygame.Surface((AW, AH), pygame.SRCALPHA)
        return G._ART_BUF

    def last_art(boss):
        """Surface art frame terakhir unit ini (dipakai FX clone R)."""
        return _NS_thalgryn._LAST_ART.get(id(boss))

    # ==================================================================
    # COMPOSE satu frame karakter
    # ==================================================================
    def _compose_art(boss, pose):
        G = _NS_thalgryn
        art = G._art_buffer()
        art.fill((0, 0, 0, 0))
        render_mantle(art, pose)
        render_tail(art, pose)
        render_body(art, pose)
        render_equipment(art, pose)
        render_armor(art, pose)
        hx, hy = render_head(art, pose)
        render_face(art, pose, hx, hy)
        render_crown(art, pose, hx, hy)
        gx, gy = render_arms(art, pose)
        render_weapon(art, pose, gx, gy)
        render_fist(art, pose, gx, gy)
        render_highlight(art, pose)
        mask = render_outline(art)
        if pose.flash > 0.02:
            render_hit_flash(art, mask, pose.flash * 0.85)
            # outline gelap ditarik ulang supaya silhouette tetap
            # tajam di atas flash
            mask = render_outline(art)
        if pose.morph > 0.05:
            render_status(art, mask, pose)
        if pose.death > 0.0:
            render_dissolve(art, max(0.0, (pose.death - 0.20) / 0.80),
                            seed=11)
        elif pose.spawn < 1.0:
            render_dissolve(art, max(0.0, 1.0 - pose.spawn * 1.3), seed=5)
        return art

    # ==================================================================
    # MAIN DRAW ENTRY POINT
    # ==================================================================
    def draw_thalgryn(surface, boss, x, y):
        """Entry point Boss.draw() sekaligus heroes.render_hero()."""
        G = _NS_thalgryn
        G._update_thalgryn_attack_anim(boss)
        moving = G._detect_moving(boss)
        pose = G.solve_pose(boss, moving)
        boss._th_pose = pose
        action, phase, ap = G._resolve_pose(boss, moving)
        boss._th_pose_action = action
        portrait = bool(getattr(boss, "_portrait_hd", False))
        hero_lane = hasattr(boss, "_render_scale")
        scale = G._fx_scale(boss)

        live, owned = G._live_fx(boss, surface, x, y,
                                 not hero_lane, portrait)
        boss._th_live_owned = bool(owned)

        # ── lapisan tanah (ruang native: ikut ter-scale pipeline) ──
        # Shadow/orbit digambar pada rasio native yang sama dengan
        # badan (2x buffer), sehingga di hero-lane keseluruhan kanvas
        # di-scale seragam oleh pipeline sprite -- tidak doble scale.
        if not portrait:
            render_shadow(surface, x, y + G.GROUND_DY, pose, 1.0)

        # ── karakter: buffer pixel-art -> upscale nearest -> blit ──
        # Badan SELALU pada resolusi native (PX); pipeline hero-lane
        # yang men-scale sprite terukur, sama seperti boss lain.
        art = G._compose_art(boss, pose)
        G._LAST_ART[id(boss)] = art
        px = G.PX
        big = pygame.transform.scale(art, (AW * px, AH * px))
        if pose.facing < 0:
            big = pygame.transform.flip(big, True, False)
        dx = int(round(x - AX * px))
        dy = int(round(y + G.GROUND_DY - AY * px))
        surface.blit(big, (dx, dy))

        # ── equipment orbit ──
        if not portrait and pose.death < 0.6 and pose.spawn > 0.4:
            render_orbit(surface, x, y, pose, 1.0)

        # ── canvas fallback proyektil/efek bila FX tidak owned ──
        if not portrait:
            if owned:
                if getattr(boss, "_th_projectiles", None):
                    boss._th_projectiles = []
                if getattr(boss, "_th_effects", None):
                    boss._th_effects = []
            else:
                G._maybe_spawn_spear(boss, x, y, action, pose)
                G._manage_projectiles(boss, surface, phase, pose)
                G._manage_effects(boss, surface, phase, pose)

        if live is not None:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass
        if G.DEBUG_CHARACTER and not portrait:
            G._draw_thalgryn_debug(surface, boss, x, y, action, owned)

    # ==================================================================
    # CANVAS FALLBACK
    # ==================================================================
    def _maybe_spawn_spear(boss, x, y, action, pose):
        """Jendela impact + target jauh -> lempar Water Spear (fallback)."""
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
        G = _NS_thalgryn
        active = bool(getattr(boss, "_th_attack_active", False))
        if not active or not getattr(boss, "_th_hit_active", False):
            if not active:
                boss._th_spear_spawned = False
            return
        if getattr(boss, "_th_spear_spawned", False):
            return
        boss._th_spear_spawned = True
        tx, ty = G._target_position(boss, x, y)
        dist = math.hypot(tx - x, ty - y)
        if dist <= G.MELEE_REACH:
            return                      # melee: tebasan, bukan spear
        G._spawn_water_spear_canvas(boss, x, y, heavy=False, pose=pose)

    def _spawn_water_spear_canvas(boss, x, y, heavy=False, pose=None):
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
        G = _NS_thalgryn
        tx, ty = G._target_position(boss, x, y)
        lst = getattr(boss, "_th_projectiles", None)
        if lst is None:
            lst = []
            boss._th_projectiles = lst
        if len(lst) >= 6:
            lst.pop(0)
        gx, gy = G._grip_screen(boss, x, y)
        lst.append({"x": float(gx), "y": float(gy), "tx": float(tx),
                    "ty": float(ty), "t": 0.0,
                    "dur": 0.34 if not heavy else 0.28,
                    "heavy": bool(heavy)})

    def _manage_projectiles(boss, surface, phase, pose=None):
        G = _NS_thalgryn
        lst = getattr(boss, "_th_projectiles", None)
        if not lst:
            return
        dt = float(getattr(boss, "_th_dt", 1.0 / 60.0))
        P = _P
        keep = []
        for p in lst:
            p["t"] += dt
            k = min(1.0, p["t"] / max(0.05, p["dur"]))
            pxx = p["x"] + (p["tx"] - p["x"]) * k
            pyy = p["y"] + (p["ty"] - p["y"]) * k - math.sin(k * math.pi) * 8
            ang = math.atan2(p["ty"] - p["y"], p["tx"] - p["x"])
            ca, sa = math.cos(ang), math.sin(ang)
            for off, col in ((-4, P["blade_dark"]), (0, P["blade_mid"]),
                             (3, P["blade_light"])):
                px_rect(surface, col + (230,), pxx - ca * off - 1,
                        pyy - sa * off - 1, 3, 2)
            px_set(surface, P["water_white"] + (255,), pxx + ca * 5,
                   pyy + sa * 5)
            if k < 1.0:
                keep.append(p)
            else:
                fx = getattr(boss, "_th_effects", None)
                if fx is None:
                    fx = []
                    boss._th_effects = fx
                fx.append({"x": p["tx"], "y": p["ty"], "t": 0.0})
        boss._th_projectiles = keep

    def _manage_effects(boss, surface, phase, pose=None):
        lst = getattr(boss, "_th_effects", None)
        if not lst:
            return
        dt = float(getattr(boss, "_th_dt", 1.0 / 60.0))
        P = _P
        keep = []
        for e in lst:
            e["t"] += dt
            k = e["t"] / 0.3
            if k >= 1.0:
                continue
            r = 4 + int(k * 14)
            a = int(200 * (1.0 - k))
            px_ellipse(surface, P["water_high"] + (a,),
                       (e["x"] - r, e["y"] - r // 2, r * 2, r))
            keep.append(e)
        boss._th_effects = keep

    # ==================================================================
    # LIVE FX WIRING
    # ==================================================================
    def _live_module():
        NS = _NS_thalgryn
        if NS._LIVE_MOD is None:
            try:
                from heroes import thalgryn_fx as mod     # noqa
                NS._LIVE_MOD = mod
            except Exception:
                pass
        return NS._LIVE_MOD or None

    def live_fx_ready():
        return _NS_thalgryn._live_module() is not None

    def _live_fx(boss, surface, x, y, want_draw, portrait):
        NS = _NS_thalgryn
        if portrait:
            return None, False
        mod = NS._live_module()
        if mod is None:
            return None, False
        try:
            if want_draw:
                mod.draw_ground_layer(surface, boss, x, y)
            else:
                mod.attach(boss)
        except Exception:
            return None, False
        try:
            owned = bool(mod.owns(boss))
        except Exception:
            owned = False
        return (mod if want_draw else None), owned

    # ==================================================================
    # DEBUG OVERLAY
    # ==================================================================
    def _draw_thalgryn_debug(surface, boss, x, y, action, owned):
        G = _NS_thalgryn
        r = max(6, int(getattr(boss, "radius", 38) * 0.9 * G._fx_scale(boss)))
        pygame.draw.rect(surface, (80, 170, 255, 150),
                         pygame.Rect(int(x) - r, int(y) - r - 8,
                                     r * 2, r * 2), 1)
        rng = max(10, int(getattr(boss, "range", 160) * G._fx_scale(boss)
                          * 0.9))
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        pygame.draw.line(surface, (255, 210, 60, 150), (int(x), int(y)),
                         (int(x) + int(rng * f), int(y)), 1)
        hb = G._swing_hitbox(boss, x, y)
        if hb is not None:
            pygame.draw.rect(surface, (255, 70, 70, 190), hb, 2)
        tip = G._tip_screen(boss, x, y)
        pygame.draw.circle(surface, (120, 255, 150), (int(tip[0]),
                                                     int(tip[1])), 4, 1)
        prog = float(getattr(boss, "_th_attack_progress", 0.0))
        bar = pygame.Rect(int(x) - 40, int(y) - 116, 80, 5)
        pygame.draw.rect(surface, (30, 10, 40), bar)
        pygame.draw.rect(surface, (255, 140, 220),
                         (bar.x, bar.y, int(80 * prog), 5))
        state = getattr(boss, "_th_state", "IDLE")
        idx = list(G.ANIM_STATES).index(state) \
            if state in G.ANIM_STATES else 0
        pygame.draw.rect(surface, (140, 255, 200),
                         (bar.x, bar.y - 6, 4 + idx * 5, 4))

    def draw_boss(surface, boss, x, y):
        _NS_thalgryn.draw_thalgryn(surface, boss, x, y)

    # helper easing terpanggil lewat namespace (paritas API lama)
    _clamp = staticmethod(_clamp)
    _seg = staticmethod(_seg)
    _lerp = staticmethod(_lerp)
    _ease_in = staticmethod(_ease_in)
    _ease_out = staticmethod(_ease_out)
    _ease_in_out = staticmethod(_ease_in_out)


# ----------------------------------------------------------------------------
# bind fungsi render modular ke namespace (API discoverable & tes)
# ----------------------------------------------------------------------------
def _bind():
    NS = _NS_thalgryn
    for name in ("render_shadow", "render_mantle", "render_tail",
                 "render_body", "render_equipment", "render_armor",
                 "render_head", "render_face", "render_crown",
                 "render_arms", "render_weapon", "render_fist",
                 "render_highlight",
                 "render_outline", "render_hit_flash", "render_status",
                 "render_dissolve", "render_orbit", "px_rect", "px_set",
                 "px_line", "px_poly", "px_circle", "px_ellipse",
                 "px_dither", "px_ramp_h"):
        setattr(NS, name, staticmethod(globals()[name]))


_bind()
