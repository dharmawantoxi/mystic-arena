"""
bosses/level4.py - Semua boss Level 4

Gabungan dari 4 file terpisah:
  - zharok               (mini boss)
  - pyrenth              (mini boss)
  - vokrahn              (mini boss)
  - ignis_drachorn       (TRUE BOSS)

Tiap boss dibungkus dalam kelas namespace `_NS_<nama>`
supaya PALETTE dan fungsi helper-nya TIDAK saling
menimpa - 91 simbol bentrok antar file boss, termasuk
PALETTE, _aacircle, _draw_shadow, _target_position.

Kode di dalam tiap namespace TIDAK diubah isinya;
hanya referensi antar-simbol yang diberi prefix.

Entry point publik ada di bagian paling bawah file.
"""

import math
import random
import pygame

# Penanda: file ini berisi BANYAK boss (1 true + 3 mini).
# Dipakai heroes/__init__.py agar tidak menebak fungsi draw_*
# secara longgar, yang bisa mengembalikan boss yang salah.
_IS_LEVEL_BUNDLE = True



# ====================================================================
# ZHAROK
# ====================================================================
class _NS_zharok:
    """Namespace zharok - PIXEL MASTERWORK v2 + COMBAT FX v3.

    Renderer `_NS_zharok` mengikuti standar **Thorne v2 Pixel Masterwork**
    untuk rig/palet/pose, lalu diangkat ke standar **v3 Combat FX**
    (lihat docs/AUDIT_ULANG_DARI_AWAL.md) dengan:

      * controller animasi ber-delta-time + state/prioritas + fase serangan
      * ARK ayunan stave busur (`BOW_ARC`) sebagai SATU sumber geometri
        senjata yang dipakai renderer DAN lapisan hidup
      * gerbang lapisan hidup `heroes/zharok_fx` (trail, partikel,
        proyektil, skill FX, impact, hit-stop, screen shake)
      * overlay DEBUG_CHARACTER

    Tetap 100% prosedural: tidak ada PNG / sprite-sheet / image.load.
    Seluruh FX canvas v2 dipertahankan sebagai FALLBACK saat modul
    lapisan hidup tidak tersedia.
    """

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    #: Overlay debug renderer (hitbox/hurtbox/state/timer).
    DEBUG_CHARACTER = False

    # ── cache (nama lama dipertahankan) ─────────────────────────────
    _shadow_cache = None
    _aura_cache = None
    _flash_buf = None
    _body_buf = None
    _record_shadow = None

    #: Rig terakhir yang dikomposit (dipakai afterimage lapisan hidup).
    _last_rig = None
    _last_rig_off = (0, 0)

    #: Modul lapisan hidup: None = belum dicari, False = tidak ada.
    _LIVE_MOD = None

    _STATIC_SURFACES = {}

    # ── metrik rig v2 ───────────────────────────────────────────────
    RIG_SCALE = 1.5
    RIG_W, RIG_H = 156, 172
    RIG_OX, RIG_OY = 78, 102

    SCALE = 0.62
    FEET_DY = 62
    GROUND_DY = int(round(FEET_DY * SCALE))

    SKILL_DUR = {"q": 50, "w": 40, "e": 60, "r": 80}
    SKILL_RADIUS = {"q": 250, "w": 200, "e": 150, "r": 220}

    #: Fase serangan (fraksi 0..1 durasi serangan). Nama fase dipakai
    #: renderer, lapisan hidup, dan overlay debug — satu kosakata.
    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, 0.12),
        ("WINDUP",       0.12, 0.30),
        ("SWING",        0.30, 0.50),
        ("IMPACT",       0.50, 0.62),
        ("FOLLOW",       0.62, 0.82),
        ("RECOVERY",     0.82, 1.00),
    )

    #: Jendela hit aktif + frame impact. 0.52 dipertahankan dari timeline
    #: archery v2 (`_attack_pose` memuncak tepat di sana).
    ATTACK_ACTIVE_WINDOW = (0.38, 0.62)
    ATTACK_IMPACT_FRAME = 0.52

    #: Prioritas state animasi. Angka besar menang; DEATH mengunci.
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
        "HIT": 60,
        "HURT": 65,
        "DEATH": 100,
    }

    #: ARK AYUNAN STAVE BUSUR — (t0, t1, theta0, theta1, ease).
    #: theta = sudut stave dari sumbu ATAS (rad); positif berputar ke arah
    #: depan (facing). Busur TIDAK PERNAH melompat: nilai akhir tiap
    #: segmen SAMA dengan nilai awal segmen berikutnya, dan theta(0) ==
    #: theta(1) supaya loop-nya mulus.
    BOW_ARC = (
        (0.00, 0.12,  2.30,  1.92, "out"),   # ANTICIPATION: tarik ke belakang
        (0.12, 0.30,  1.92, -1.16, "io"),    # WIND-UP: angkat tinggi
        (0.30, 0.50, -1.16,  1.74, "oc"),    # SWING: sapuan cepat ke depan
        (0.50, 0.62,  1.74,  2.06, "hold"),  # IMPACT: overshoot + tahan bobot
        (0.62, 0.82,  2.06,  2.64, "io"),    # FOLLOW THROUGH: stave turun
        (0.82, 1.00,  2.64,  2.30, "io"),    # RECOVERY: kembali ke garda
    )

    #: Setengah panjang stave & offset grip dalam koordinat RIG (px rig,
    #: sebelum dikalikan SCALE). Angka ini mengikuti `_draw_flaming_bow`
    #: (limb membentang hy-28 .. hy+28) dan `_draw_bow_attack_arms`
    #: (grip di cx + 24*f, cy) supaya geometri = gambar.
    STAVE_HALF = 28.0
    GRIP_RIG = (24.0, -12.0)

    #: Jarak (px dunia) di mana Zharok beralih dari melepas anak panah ke
    #: MENYABET dengan stave busur yang menyala. Di bawah nilai ini,
    #: menarik busur tidak masuk akal — jadi dia meng-cleave.
    MELEE_REACH = 74.0

    # ---------------------------------------------------------------------------
    # HD Emberborn Palette v2 - Bone Ivory / Hellfire / Obsidian Cloth / Gold
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Bone - skeleton 7-band (bayangan cokelat-ungu dingin -> highlight ivory hangat)
        "bone_darkest":   (32,  22,  16),
        "bone_dark":      (74,  54,  32),
        "bone_mid":       (142, 114,  68),
        "bone_light":     (208, 178, 118),
        "bone_high":      (242, 220, 164),
        "bone_shine":     (255, 246, 212),
        "bone_rim":       (255, 240, 200),

        # Fire / Hellfire 8-band
        "fire_darkest":   (48,  10,   8),
        "fire_dark":      (128,  28,  12),
        "fire_mid":       (210,  68,  18),
        "fire_bright":    (255, 124,  32),
        "fire_hot":       (255, 182,  64),
        "fire_glow":      (255, 224, 128),
        "fire_white":     (255, 252, 220),
        "fire_seam":      (255, 240, 180),

        # Soulfire / Core Heartfire 4-band
        "soul_dark":      (160,  25,  10),
        "soul_mid":       (255,  95,  25),
        "soul_hot":       (255, 205,  80),
        "soul_glow":      (255, 245, 180),

        # Hood / Cape / Cloth 6-band (tattered crimson-charcoal / obsidian cloth)
        "hood_darkest":   (14,   8,  12),
        "hood_dark":      (42,  16,  22),
        "hood_mid":       (88,  30,  36),
        "hood_light":     (148,  54,  52),
        "hood_high":      (198,  86,  76),
        "hood_trim":      (228, 140,  80),

        # Leather / straps 5-band
        "leather_darkest": (16,  10,   8),
        "leather_dark":   (42,  26,  18),
        "leather_mid":    (82,  52,  30),
        "leather_light":  (136,  92,  54),
        "leather_high":   (182, 134,  86),

        # Metal (arrows, fittings, rivets) 6-band
        "metal_darkest":  (16,  14,  18),
        "metal_dark":     (44,  40,  52),
        "metal_mid":      (92,  86, 102),
        "metal_light":    (158, 152, 172),
        "metal_shine":    (214, 208, 226),
        "metal_high":     (242, 238, 250),

        # Gold accents 4-band
        "gold_dark":      (88,  58,  18),
        "gold_mid":       (168, 124,  38),
        "gold_light":     (232, 188,  78),
        "gold_shine":     (255, 232, 142),

        # Wood (bow stave) 4-band
        "wood_dark":      (46,  26,  14),
        "wood_mid":       (90,  54,  28),
        "wood_light":     (144,  98,  52),
        "wood_high":      (192, 142,  82),

        # Eyes (glowing sockets)
        "eye_dark":       (58,  12,   6),
        "eye_bright":     (255, 125,  35),
        "eye_hot":        (255, 205,  95),
        "eye_white":      (255, 245, 215),

        # Smoke / ash / stealth 4-band
        "smoke_dark":     (18,  10,  28),
        "smoke_mid":      (54,  36,  84),
        "smoke_light":    (114,  84, 162),
        "smoke_glow":     (190, 150, 240),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   2,   4),
        "white":          (255, 255, 255),
    }

    # ---------------------------------------------------------------------------
    # Primitif dasar (High-Performance Zero-Allocation)
    # ---------------------------------------------------------------------------
    @staticmethod
    def _static(key, builder):
        """Surface statis ter-cache (dibangun sekali, dipakai ulang)."""
        surf = _NS_zharok._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_zharok._STATIC_SURFACES[key] = surf
        return surf

    _CLAMP_MEMO = {}

    @staticmethod
    def _clamp(color):
        try:
            hit = _NS_zharok._CLAMP_MEMO.get(color)
        except TypeError:
            return tuple(max(0, min(255, int(c))) for c in color)
        if hit is not None:
            return hit
        out = tuple(max(0, min(255, int(c))) for c in color)
        memo = _NS_zharok._CLAMP_MEMO
        if len(memo) > 8192:
            memo.clear()
        memo[color] = out
        return out

    @staticmethod
    def _alpha(v):
        return max(0, min(255, int(v)))

    @staticmethod
    def _mix(a, b, t):
        t = max(0.0, min(1.0, t))
        return _NS_zharok._clamp(
            (a[0] + (b[0] - a[0]) * t,
             a[1] + (b[1] - a[1]) * t,
             a[2] + (b[2] - a[2]) * t))

    @staticmethod
    def _hash01(i):
        x = math.sin(i * 127.1 + 311.7) * 43758.5453
        return x - math.floor(x)

    @staticmethod
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_zharok._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if _NS_zharok.HAS_AACIRCLE and radius > 1 and (len(color) < 4 or color[3] == 255):
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, (cx, cy), radius, width)

    @staticmethod
    def _aaline(surface, color, start, end, width=1):
        color = _NS_zharok._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        pygame.draw.line(surface, color, (sx, sy), (ex, ey), max(1, width))

    @staticmethod
    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_zharok._clamp(color)
        pygame.draw.polygon(surface, color, points)

    @staticmethod
    def _ellipse(surface, color, rect, width=0):
        color = _NS_zharok._clamp(color)
        pygame.draw.ellipse(surface, color, rect, width)

    @staticmethod
    def _rect(surface, color, rect, border_radius=0):
        color = _NS_zharok._clamp(color)
        pygame.draw.rect(surface, color, rect, border_radius=border_radius)

    @staticmethod
    def _ring(surface, center, radius, width, color, alpha):
        alpha = _NS_zharok._alpha(alpha)
        if alpha <= 0:
            return
        cx, cy = int(center[0]), int(center[1])
        r = int(radius)
        if r <= 0:
            return
        _NS_zharok._aacircle(surface, (6, 3, 6, alpha), (cx, cy), r + 1,
                             max(1, width + 2))
        _NS_zharok._aacircle(surface, (*color, alpha), (cx, cy), r,
                             max(1, width))

    # ---------------------------------------------------------------------------
    # Konversi koordinat
    # ---------------------------------------------------------------------------
    @staticmethod
    def _world_to_local(boss, x, y, wx, wy):
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(wx), int(wy)
        scale = float(scale) or 1.0
        ox = (float(wx) - float(getattr(boss, "x", x))) / scale
        oy = (float(wy) - float(getattr(boss, "y", y))) / scale
        rng = int(getattr(boss, "range", 180) or 180)
        half = max(140, int(rng / scale) + 40)
        max_off = half - 20
        d = math.hypot(ox, oy)
        if d > max_off:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    @staticmethod
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return (int(x + 180 / float(getattr(boss, "_render_scale", 1.0) or 1.0)
                    * getattr(boss, "direction", 1)), int(y))

    # ===================================================================
    # SKILL FX PRIMITIVES (standar Thorne v2.1)
    # ===================================================================
    @staticmethod
    def _fx_scale(boss):
        scale = getattr(boss, "_render_scale", None)
        if not scale:
            return 1.0
        return max(1.0, min(2.6, 1.0 / float(scale)))

    @staticmethod
    def _ring_r(boss, world_px, surface):
        scale = getattr(boss, "_render_scale", None)
        r = float(world_px) / float(scale) if scale else float(world_px)
        margin = min(surface.get_width(), surface.get_height()) // 2 - 10
        return int(max(4, min(r, margin)))

    @staticmethod
    def _spark_star(surface, cx, cy, size, color, alpha, spikes=6, rot=0.4, core=None):
        alpha = _NS_zharok._alpha(alpha)
        if alpha <= 0 or size <= 0:
            return
        for k in range(spikes):
            ang = rot + k * math.pi * 2 / spikes
            ln = size * (1.0 if k % 2 == 0 else 0.55)
            _NS_zharok._aaline(surface, (*color, alpha),
                               (int(cx), int(cy)),
                               (int(cx + math.cos(ang) * ln),
                                int(cy + math.sin(ang) * ln * .8)),
                               2 if k % 2 == 0 else 1)
        if core:
            _NS_zharok._aacircle(surface, (*core, alpha), (int(cx), int(cy)),
                                 max(1, int(size * .3)))

    @staticmethod
    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        alpha = _NS_zharok._alpha(alpha)
        if alpha <= 0 or size <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        tipx, tipy = cx + ca * size, cy + sa * size
        for s in (-1, 1):
            _NS_zharok._aaline(
                surface, (*color, alpha),
                (int(cx + px * s * size * .55 - ca * size * .5),
                 int(cy + py * s * size * .55 - sa * size * .5)),
                (int(tipx), int(tipy)), width)

    @staticmethod
    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=10, thick=3, span=0.6, squash=.92):
        alpha = _NS_zharok._alpha(alpha)
        if alpha <= 0 or radius <= 1:
            return
        for i in range(segments):
            a0 = phase + i * math.pi * 2 / segments
            a1 = a0 + math.pi * 2 / segments * span
            p0 = (cx + math.cos(a0) * radius, cy + math.sin(a0) * radius * squash)
            p1 = (cx + math.cos(a1) * radius, cy + math.sin(a1) * radius * squash)
            _NS_zharok._aaline(surface, (*color, alpha), p0, p1, thick)

    @staticmethod
    def _jagged_crack(surface, x0, y0, x1, y1, color, alpha, width=2,
                      segments=4, max_dev=5.0, seed=0):
        alpha = _NS_zharok._alpha(alpha)
        if alpha <= 0:
            return
        dx = x1 - x0
        dy = y1 - y0
        dist = math.hypot(dx, dy)
        if dist < 2.0:
            return
        nx, ny = -dy / dist, dx / dist
        pts = [(x0, y0)]
        for k in range(1, segments):
            t = k / float(segments)
            h = _NS_zharok._hash01(seed + k * 17) * 2.0 - 1.0
            dev = h * max_dev * math.sin(t * math.pi)
            px = x0 + dx * t + nx * dev
            py = y0 + dy * t + ny * dev
            pts.append((px, py))
        pts.append((x1, y1))
        for i in range(len(pts) - 1):
            _NS_zharok._aaline(surface, (*color, alpha), pts[i], pts[i + 1], width)

    @staticmethod
    def _tuft_points(spine, depth=4.0, min_len=4.0, seed=0):
        if len(spine) < 2:
            return list(spine)
        left_pts = []
        right_pts = []
        for i in range(len(spine)):
            x, y = spine[i]
            if i < len(spine) - 1:
                dx = spine[i + 1][0] - x
                dy = spine[i + 1][1] - y
            else:
                dx = x - spine[i - 1][0]
                dy = y - spine[i - 1][1]
            dist = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / dist, dx / dist
            d = depth * (0.6 + 0.4 * _NS_zharok._hash01(seed + i * 19))
            left_pts.append((x - nx * d, y - ny * d))
            right_pts.append((x + nx * d, y + ny * d))
        return left_pts + right_pts[::-1]

    @staticmethod
    def _dither_dots(surface, color, rect, pattern=0):
        color = _NS_zharok._clamp(color)
        rx, ry, rw, rh = rect
        for dy in range(int(rh)):
            for dx in range(int(rw)):
                if (dx + dy + pattern) % 2 == 0:
                    surface.set_at((int(rx + dx), int(ry + dy)), color)

    # -------------------------------------------------------------------
    # DECAL ENGINE (Cached Decals)
    # -------------------------------------------------------------------
    _DECAL_CACHE = {}
    _DECAL_ORDER = []



    @staticmethod
    def _decal(key, size, builder):
        NS = _NS_zharok
        hit = NS._DECAL_CACHE.get(key)
        if hit is not None:
            return hit
        surf = builder(size)
        NS._DECAL_CACHE[key] = surf
        NS._DECAL_ORDER.append(key)
        # Versi PREMULTIPLIED dibuat sekali di sini, berbarengan dengan
        # decal-nya, lalu hidup & mati bersama entri cache yang sama.
        # Itu sebabnya radius yang berdenyut (tiap frame kunci baru)
        # tidak pernah memicu premultiply berulang di jalur gambar.
        NS._PREMUL[id(surf)] = surf.premul_alpha()
        if len(NS._DECAL_ORDER) > 128:
            old = NS._DECAL_ORDER.pop(0)
            dead = NS._DECAL_CACHE.pop(old, None)
            if dead is not None:
                NS._PREMUL.pop(id(dead), None)
        return surf

    #: Decal versi PREMULTIPLIED untuk surface yang TIDAK dibangun lewat
    #: builder ber-`pm` (mis. hasil transform ad-hoc). Kunci id(decal).
    _PREMUL = {}
    #: Varian redup decal KECIL: (id(decal), level) -> (decal, surface).
    _FADE_VARIANT = {}
    _FADE_ORDER = []
    _ADD_LEVELS = 6
    #: Decal yang lebih besar dari ini tidak menyimpan varian redup —
    #: telegraph AoE raksasa memang harus terbaca penuh, dan menyimpan
    #: enam salinan 700x700 per decal akan memakan puluhan MB percuma.
    _ADD_FADE_MAX_PX = 40_000
    _FADE_CAP = 64

    @staticmethod
    def _pmc(col, a, pm, k=255):
        """Warna RGBA untuk builder decal.

        Dua hal dipanggang sekaligus di sini, dan keduanya gratis karena
        fungsi draw pygame MENIMPA piksel (bukan mem-blend):

        * ``pm`` -> RGB dikali alpha (premultiplied). Hasilnya identik
          dengan ``premul_alpha()`` tapi tanpa lintasan tambahan pada
          jalur cache-miss -- jalur yang justru diukur audit v2.
        * ``k``  -> peredupan decal. Blit ber-``special_flags``
          mengabaikan ``set_alpha()``, jadi meredupkan decal additif
          selalu butuh salinan yang dikali. Dipanggang di sini,
          peredupan itu tidak berbiaya sama sekali.
        """
        if k < 255:
            a = a * k / 255.0
        a = 0 if a < 0 else (255 if a > 255 else int(a))
        if not pm:
            return (col[0], col[1], col[2], a)
        return (col[0] * a // 255, col[1] * a // 255, col[2] * a // 255, a)

    @staticmethod
    def _fade_level(alpha, levels=8):
        """Peredupan dibulatkan ke kelipatan tetap supaya kunci cache
        decal berulang, bukan lahir baru tiap frame."""
        alpha = _NS_zharok._alpha(alpha)
        lv = int(alpha * levels / 255.0 + 0.5)
        lv = max(0, min(levels, lv))
        return lv * 255 // levels

    @staticmethod
    def _add_variant(decal, alpha, premul):
        """Surface siap dipakai ``BLEND_RGBA_ADD``.

        Blend additif menambahkan kanal warna **tanpa melihat alpha**,
        jadi decal bergradien yang langsung ditambahkan muncul sebagai
        cakram warna penuh bertepi keras. Sumbernya harus premultiplied.
        Decal dari builder internal sudah lahir premultiplied (`_pmc`);
        surface luar dipremultiply sekali lalu di-cache.
        """
        NS = _NS_zharok
        if premul:
            pm = decal
        else:
            pm = NS._PREMUL.get(id(decal))
            if pm is None or pm.get_size() != decal.get_size():
                pm = decal.premul_alpha()
                # Surface tanpa pemilik yang meng-evict-nya dibatasi keras
                # supaya cache tidak bocor.
                if len(NS._PREMUL) > 192:
                    NS._PREMUL.clear()
                NS._PREMUL[id(decal)] = pm

        w, h = pm.get_size()
        if alpha >= 250 or w * h > NS._ADD_FADE_MAX_PX:
            return pm
        lv = int(alpha * NS._ADD_LEVELS / 255.0 + 0.5)
        lv = max(1, min(NS._ADD_LEVELS, lv))
        if lv >= NS._ADD_LEVELS:
            return pm
        ck = (id(pm), lv)
        got = NS._FADE_VARIANT.get(ck)
        if got is not None and got[0] is pm:
            return got[1]
        k = int(255 * lv / NS._ADD_LEVELS)
        var = pm.copy()
        var.fill((k, k, k, k), special_flags=pygame.BLEND_RGBA_MULT)
        NS._FADE_VARIANT[ck] = (pm, var)
        NS._FADE_ORDER.append(ck)
        while len(NS._FADE_ORDER) > NS._FADE_CAP:
            NS._FADE_VARIANT.pop(NS._FADE_ORDER.pop(0), None)
        return var

    @staticmethod
    def _blit_decal(surface, decal, cx, cy, alpha=255, add=False,
                    premul=False):
        """Blit decal; mode ``add`` MENGHORMATI alpha per-piksel.

        Dua jebakan yang diperbaiki di sini (v2 kena keduanya, dan itulah
        kenapa aura Zharok muncul sebagai cakram oranye pekat bertepi
        keras yang menelan siluetnya):

        1. ``BLEND_RGB_ADD`` / ``BLEND_RGBA_ADD`` menambahkan kanal warna
           **tanpa melihat alpha**. Decal bergradien yang sudah rapi
           (`_build_radial_glow` menurunkan alpha ke 0 di tepi) tetap
           menambahkan warna PENUH sampai ke tepi -> cakram datar bertepi
           keras. Perbaikannya premultiply (RGB dikali alpha) SEBELUM
           ditambahkan. Builder internal sudah memanggangnya lewat
           `_pmc` (ditandai ``premul=True``); surface lain diurus
           `_add_variant`.
        2. ``Surface.set_alpha()`` **diabaikan** oleh blit ber-
           ``special_flags``, jadi peredupan v2 pada mode add tidak
           pernah benar-benar terjadi. Sekarang peredupan dipanggang ke
           dalam varian yang di-cache.

        Mode normal (``add=False``) memakai ``BLEND_RGBA_MULT`` pada
        salinan, karena di sana pun ``set_alpha`` tidak bisa diandalkan
        untuk surface ber-alpha per-piksel.
        """
        NS = _NS_zharok
        alpha = NS._alpha(alpha)
        if alpha <= 0 or decal is None:
            return
        w, h = decal.get_size()
        x0 = int(cx) - w // 2
        y0 = int(cy) - h // 2

        if not add:
            if alpha < 255:
                decal = decal.copy()
                decal.fill((255, 255, 255, alpha),
                           special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(decal, (x0, y0))
            return

        surface.blit(NS._add_variant(decal, alpha, premul), (x0, y0),
                     special_flags=pygame.BLEND_RGBA_ADD)

    @staticmethod
    def _quantize(v, step=6):
        return max(step, int(round(float(v) / step) * step))

    @staticmethod
    def _build_falloff_ring(size, color, core, thickness, softness,
                            inner_glow, pm=False, k=255):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        r_nom = c - softness - 2
        if r_nom < 2:
            return surf
        lo = max(1, int(r_nom - thickness - softness))
        hi = int(r_nom + softness)
        for r in range(lo, hi + 1):
            d = abs(r - r_nom)
            if d <= thickness * 0.5:
                t = 1.0
            else:
                t = max(0.0, 1.0 - (d - thickness * 0.5) / max(1.0, softness))
                t = t * t
            if t <= 0.003:
                continue
            col = _NS_zharok._mix(color, core, min(1.0, max(0.0, t - 0.45) * 1.5))
            pygame.draw.circle(surf, _NS_zharok._pmc(col, 200 * t, pm, k),
                               (c, c), r, 1)
        if inner_glow > 0:
            for r in range(lo, 0, -2):
                t = (r / float(max(1, lo))) ** 2
                a = int(inner_glow * t)
                if a > 1:
                    pygame.draw.circle(surf,
                                       _NS_zharok._pmc(color, a, pm, k),
                                       (c, c), r, 2)
        return surf

    @staticmethod
    def _ground_ring(surface, cx, cy, radius, color, core, alpha,
                     thickness=3, softness=7, inner_glow=0, add=True):
        radius = _NS_zharok._quantize(radius, 6)
        if radius < 6:
            return
        pad = softness + thickness + 3
        size = radius * 2 + pad * 2
        # `add` masuk ke kunci cache: decal untuk blend additif dibangun
        # langsung dalam bentuk premultiplied (lihat `_pmc`).
        # Mode additif: peredupan DIPANGGANG ke dalam decal (`k`) dan
        # ikut jadi kunci cache. Blit ber-special_flags mengabaikan
        # set_alpha, jadi alternatifnya salinan-yang-dikali tiap frame.
        k = _NS_zharok._fade_level(alpha) if add else 255
        if k <= 0:
            return
        key = ("fring", radius, color, core, thickness, softness,
               inner_glow, add, k)
        decal = _NS_zharok._decal(
            key, size,
            lambda n: _NS_zharok._build_falloff_ring(
                n, color, core, thickness, softness, inner_glow,
                pm=add, k=k))
        _NS_zharok._blit_decal(surface, decal, cx, cy,
                               255 if add else alpha, add=add, premul=add)

    @staticmethod
    def _build_arc_ring(size, color, core, segments, span, thickness,
                        softness, taper, pm=False, k=255):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        r_nom = c - softness - thickness - 2
        if r_nom < 3:
            return surf
        step = math.tau / segments
        for i in range(segments):
            a0 = i * step
            a1 = a0 + step * span
            steps = max(3, int(span * 14))
            outer = []
            inner = []
            for s in range(steps + 1):
                u = s / float(steps)
                ang = a0 + (a1 - a0) * u
                mid = 1.0 - abs(u - 0.5) * 2.0
                w = thickness * (0.25 + 0.75 * (mid ** taper))
                ca, sa = math.cos(ang), math.sin(ang)
                outer.append((c + ca * (r_nom + w), c + sa * (r_nom + w)))
                inner.append((c + ca * (r_nom - w), c + sa * (r_nom - w)))
            poly = outer + inner[::-1]
            if len(poly) >= 3:
                pygame.draw.polygon(surf, _NS_zharok._pmc(color, 210, pm, k),
                                    poly)
                if core:
                    core_pts = []
                    for s in range(1, steps):
                        u = s / float(steps)
                        ang = a0 + (a1 - a0) * u
                        ca, sa = math.cos(ang), math.sin(ang)
                        core_pts.append((c + ca * r_nom, c + sa * r_nom))
                    if len(core_pts) >= 2:
                        pygame.draw.lines(surf,
                                          _NS_zharok._pmc(core, 230, pm, k),
                                          False, core_pts, 1)
        return surf

    @staticmethod
    def _rune_ring(surface, cx, cy, radius, color, core, alpha, phase=0.0,
                   segments=8, span=0.65, thickness=3, softness=4,
                   taper=1.2, add=True):
        radius = _NS_zharok._quantize(radius, 8)
        if radius < 8:
            return
        pad = int(thickness) + 8
        size = radius * 2 + pad * 2
        # Rotasi IKUT dipanggang ke dalam kunci cache. Kalau tidak,
        # `transform.rotate` melahirkan surface baru tiap frame: bukan
        # cuma rotasinya yang dibayar ulang, tapi juga premultiply-nya
        # (lihat `_add_variant`) — dan cache premul ikut bocor.
        seg_arc = 360.0 / max(1, segments)
        step = seg_arc / 12.0
        deg = round(((-math.degrees(phase)) % seg_arc) / step) * step
        # Mode additif: peredupan DIPANGGANG ke dalam decal (`k`) dan
        # ikut jadi kunci cache. Blit ber-special_flags mengabaikan
        # set_alpha, jadi alternatifnya salinan-yang-dikali tiap frame.
        k = _NS_zharok._fade_level(alpha) if add else 255
        if k <= 0:
            return
        key = ("rring", radius, color, core, segments, span, thickness,
               softness, taper, round(deg, 2), add, k)
        decal = _NS_zharok._decal(
            key, size,
            lambda n: pygame.transform.rotate(
                _NS_zharok._build_arc_ring(
                    n, color, core, segments, span, thickness, softness,
                    taper, pm=add, k=k),
                deg))
        _NS_zharok._blit_decal(surface, decal, cx, cy,
                               255 if add else alpha, add=add, premul=add)

    @staticmethod
    def _build_zone_fill(size, color, core, falloff_exp, rim_boost,
                         pm=False, k=255):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        r_max = c - 2
        if r_max < 2:
            return surf
        for r in range(1, r_max + 1, 2):
            u = r / float(r_max)
            t = (u ** falloff_exp) * rim_boost
            t = max(0.0, min(1.0, t))
            if t <= 0.005:
                continue
            col = _NS_zharok._mix(color, core, min(1.0, t * 1.3))
            a = int(180 * t)
            if a > 0:
                pygame.draw.circle(surf, _NS_zharok._pmc(col, a, pm, k),
                                   (c, c), r, 2)
        return surf

    @staticmethod
    def _zone_fill(surface, cx, cy, radius, color, core, alpha,
                   falloff_exp=2.2, rim_boost=1.0, add=True):
        radius = _NS_zharok._quantize(radius, 8)
        if radius < 8:
            return
        size = radius * 2 + 4
        # Mode additif: peredupan DIPANGGANG ke dalam decal (`k`) dan
        # ikut jadi kunci cache. Blit ber-special_flags mengabaikan
        # set_alpha, jadi alternatifnya salinan-yang-dikali tiap frame.
        k = _NS_zharok._fade_level(alpha) if add else 255
        if k <= 0:
            return
        key = ("zfill", radius, color, core, falloff_exp, rim_boost, add, k)
        decal = _NS_zharok._decal(
            key, size,
            lambda n: _NS_zharok._build_zone_fill(
                n, color, core, falloff_exp, rim_boost, pm=add, k=k))
        _NS_zharok._blit_decal(surface, decal, cx, cy,
                               255 if add else alpha, add=add, premul=add)

    @staticmethod
    def _build_scorch_patch(size, dark, mid, edge_blobs):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        r_base = c - 6
        if r_base < 3:
            return surf
        pygame.draw.circle(surf, (*dark, 200), (c, c), int(r_base * 0.72))
        pygame.draw.circle(surf, (*mid, 140), (c, c), int(r_base * 0.90), 3)
        for i in range(edge_blobs):
            ang = i * math.tau / edge_blobs + _NS_zharok._hash01(i * 11) * 0.4
            r_blob = r_base * (0.75 + 0.22 * _NS_zharok._hash01(i * 23 + 1))
            bx = c + int(math.cos(ang) * r_blob)
            by = c + int(math.sin(ang) * r_blob)
            br = int(4 + 5 * _NS_zharok._hash01(i * 37 + 2))
            pygame.draw.circle(surf, (*dark, 160), (bx, by), br)
        return surf

    @staticmethod
    def _ground_scorch(surface, cx, cy, radius, alpha=180, dark=None, mid=None,
                       edge_blobs=9):
        P = _NS_zharok.PALETTE
        dark = dark or P["fire_darkest"]
        mid = mid or P["hood_darkest"]
        radius = _NS_zharok._quantize(min(160, radius), 16)
        if radius < 8:
            return
        size = radius * 2 + 12
        key = ("scorch", radius, dark, mid, edge_blobs)
        decal = _NS_zharok._decal(
            key, size,
            lambda n: _NS_zharok._build_scorch_patch(n, dark, mid, edge_blobs))
        _NS_zharok._blit_decal(surface, decal, cx, cy, alpha, add=False)

    @staticmethod
    def _build_radial_glow(size, color, core, pm=False, k=255):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        r_max = c - 2
        if r_max < 2:
            return surf
        for r in range(r_max, 0, -2):
            u = r / float(r_max)
            t = (1.0 - u) ** 1.8
            col = _NS_zharok._mix(color, core, t * t)
            a = int(220 * t)
            if a > 0:
                pygame.draw.circle(surf, _NS_zharok._pmc(col, a, pm, k),
                                   (c, c), r, 2)
        return surf

    @staticmethod
    def _glow(surface, cx, cy, radius, color, core=None, alpha=255, add=True):
        core = core or _NS_zharok.PALETTE["fire_white"]
        radius = _NS_zharok._quantize(radius, 6)
        if radius < 4:
            return
        size = radius * 2 + 4
        # Mode additif: peredupan DIPANGGANG ke dalam decal (`k`) dan
        # ikut jadi kunci cache. Blit ber-special_flags mengabaikan
        # set_alpha, jadi alternatifnya salinan-yang-dikali tiap frame.
        k = _NS_zharok._fade_level(alpha) if add else 255
        if k <= 0:
            return
        key = ("glow", radius, color, core, add, k)
        decal = _NS_zharok._decal(
            key, size,
            lambda n: _NS_zharok._build_radial_glow(n, color, core,
                                                    pm=add, k=k))
        _NS_zharok._blit_decal(surface, decal, cx, cy,
                               255 if add else alpha, add=add, premul=add)

    @staticmethod
    def _draw_shockwave(surface, cx, cy, radius, color, alpha, thickness=3):
        alpha = _NS_zharok._alpha(alpha)
        if alpha <= 0 or radius <= 2:
            return
        _NS_zharok._ground_ring(surface, cx, cy, radius, color,
                                _NS_zharok.PALETTE["fire_white"], alpha,
                                thickness=thickness, softness=4, add=True)

    # ===================================================================
    # GERBANG LAPISAN HIDUP (heroes/zharok_fx)
    #   Trail sabetan, partikel, proyektil, skill FX, impact, hit-stop,
    #   dan screen shake hidup di RUANG LAYAR skala 1:1 supaya tidak ikut
    #   beku / menyusut bersama sprite cache di lane hero. Kalau modulnya
    #   tidak ada, `owns()` False dan renderer menggambar semuanya sendiri
    #   lewat jalur canvas v2 (visual kehilangan polish, TIDAK PERNAH
    #   kehilangan efek).
    # ===================================================================
    @staticmethod
    def _live_module():
        NS = _NS_zharok
        if NS._LIVE_MOD is None:
            try:
                from heroes import zharok_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "ZHAROK_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    @staticmethod
    def live_fx_ready():
        return _NS_zharok._live_module() is not None

    @staticmethod
    def _live_fx(boss, surface, x, y, want_draw, portrait):
        """Pasang/gambar lapisan hidup. Return (mod_untuk_draw, owned)."""
        NS = _NS_zharok
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
            if owned and not want_draw:
                # Lane hero: yang menggambar lapisan hidup adalah pipeline
                # heroes/__init__ (_live_fx_pre/_live_fx_post). Kalau
                # ternyata TIDAK ada yang menggambarnya, jangan matikan
                # fallback canvas - karakter tidak boleh kehilangan FX
                # secara diam-diam.
                checker = getattr(mod, "recently_drawn", None)
                if checker is not None:
                    owned = bool(checker(boss))
        except Exception:
            owned = False
        return (mod if want_draw else None), owned

    # ===================================================================
    # ANIMATION CONTROLLER
    #   Satu-satunya sumber kebenaran state/fase/timing. Lapisan hidup,
    #   overlay debug, dan alat uji semuanya membacanya dari sini.
    # ===================================================================
    @staticmethod
    def _ease(kind, t):
        if t <= 0.0:
            return 0.0
        if t >= 1.0:
            return 1.0
        if kind == "out":
            return 1.0 - (1.0 - t) * (1.0 - t)
        if kind == "oc":                              # out-cubic (cepat)
            return 1.0 - (1.0 - t) ** 3
        if kind == "in":
            return t * t
        if kind == "hold":
            return math.sin(t * math.pi * 0.5)
        return t * t * (3.0 - 2.0 * t)                # in-out (smoothstep)

    @staticmethod
    def attack_phases_order():
        return tuple(name for name, _a, _b in _NS_zharok.ATTACK_PHASES)

    @staticmethod
    def attack_phase(progress):
        """Nama fase serangan untuk progress 0..1."""
        p = max(0.0, min(1.0, float(progress)))
        for name, a, b in _NS_zharok.ATTACK_PHASES:
            if a <= p < b:
                return name
        return "RECOVERY"

    @staticmethod
    def _bow_lift(progress):
        """Ketinggian relatif tangan busur saat mengayun (0..1)."""
        p = max(0.0, min(1.0, float(progress)))
        E = _NS_zharok._ease
        if p < 0.30:
            return E("out", p / 0.30)
        if p < 0.50:
            return 1.0 - E("oc", (p - 0.30) / 0.20) * 0.95
        if p < 0.82:
            return 0.05 + E("io", (p - 0.50) / 0.32) * 0.18
        return 0.23 * (1.0 - E("io", (p - 0.82) / 0.18))

    @staticmethod
    def _bow_arc(progress):
        """(theta, lift) ARK stave busur — SATU sumber kebenaran.

        theta = sudut stave dari sumbu ATAS (rad), positif ke arah facing.
        Tabel bersambung, jadi senjata tidak pernah teleport.
        """
        p = max(0.0, min(1.0, float(progress)))
        NS = _NS_zharok
        for t0, t1, a0, a1, kind in NS.BOW_ARC:
            if t0 <= p < t1 or (p >= 1.0 and t1 >= 1.0):
                e = NS._ease(kind, (p - t0) / max(0.0001, t1 - t0))
                return a0 + (a1 - a0) * e, NS._bow_lift(p)
        return NS.BOW_ARC[0][2], 0.0

    @staticmethod
    def _cleave_offset(progress):
        """Dorongan badan ke depan (px rig) mengikuti bobot ayunan."""
        p = max(0.0, min(1.0, float(progress)))
        E = _NS_zharok._ease
        if p < 0.12:
            return -1.5 * E("out", p / 0.12)          # anticipation mundur
        if p < 0.30:
            return -1.5 - 2.0 * E("io", (p - 0.12) / 0.18)
        if p < 0.50:
            return -3.5 + 12.0 * E("oc", (p - 0.30) / 0.20)
        if p < 0.62:
            return 8.5 + 1.5 * E("hold", (p - 0.50) / 0.12)
        if p < 0.82:
            return 10.0 - 7.0 * E("io", (p - 0.62) / 0.20)
        return 3.0 * (1.0 - E("io", (p - 0.82) / 0.18))

    @staticmethod
    def bow_geometry(facing, action, phase, ap=0.0):
        """(grip, tip_atas, tip_bawah, theta) OFFSET LOKAL dari jangkar.

        Nilai yang dikembalikan sudah dikalikan ``SCALE`` sehingga berada
        di RUANG LAYAR (pada render_scale 1). Dipakai renderer (menggambar
        busur) DAN lapisan hidup (trail + titik lahir proyektil), jadi
        stave dan trail mustahil berbeda satu frame pun.
        """
        NS = _NS_zharok
        f = 1 if facing >= 0 else -1
        L = NS.STAVE_HALF
        gx0, gy0 = NS.GRIP_RIG

        if action in ("melee", "swing", "cleave"):
            theta, lift = NS._bow_arc(ap)
            lunge = NS._cleave_offset(ap)
            gx = f * (gx0 + 4.0 * lift + lunge * 0.55)
            gy = gy0 - 3.0 - 10.0 * lift
        elif action in ("attack", "strafe"):
            pose = NS._attack_pose(ap)
            # busur tetap tegak saat membidik, hanya miring halus mengikuti
            # tarikan tali & recoil pelepasan
            theta = -0.10 * pose["draw"] + 0.26 * pose["impact"]
            lift = 0.0
            gx = f * (gx0 + pose["lunge"] * 0.8)
            gy = gy0 + pose["dip"] * 0.5
        elif action in ("e_cast", "r_cast", "cast", "skill", "charge"):
            theta = 0.16 + math.sin(phase * 2.2) * 0.05
            lift = 0.8
            gx = f * (gx0 - 6.0)
            gy = gy0 - 8.0
        elif action in ("walk", "run"):
            theta = 0.18 + math.sin(phase * 1.1) * 0.08
            lift = 0.05
            gx = f * (gx0 - 1.0)
            gy = gy0 + 1.0
        else:                                          # idle / hurt / death
            theta = 0.10 + math.sin(phase * 0.8) * 0.05
            lift = 0.0
            gx = f * gx0
            gy = gy0 + math.sin(phase * 0.8) * 0.8

        dx = f * math.sin(theta) * L
        dy = -math.cos(theta) * L
        k = NS.SCALE
        return ((gx * k, gy * k),
                ((gx + dx) * k, (gy + dy) * k),
                ((gx - dx) * k, (gy - dy) * k),
                theta)

    @staticmethod
    def _melee_reach(boss):
        """True kalau target cukup dekat untuk sabetan stave (bukan panah).

        Zharok pemanah: pada jarak jauh ia melepas anak panah, tapi kalau
        musuh menempel ia MENYABET dengan stave busur yang menyala.
        """
        tgt = getattr(boss, "target", None)
        if tgt is None or not getattr(tgt, "alive", True):
            return False
        try:
            d = math.hypot(float(getattr(tgt, "x", 0.0))
                           - float(getattr(boss, "x", 0.0)),
                           float(getattr(tgt, "y", 0.0))
                           - float(getattr(boss, "y", 0.0)))
        except (TypeError, ValueError):
            return False
        return d <= _NS_zharok.MELEE_REACH

    @staticmethod
    def _update_zharok_anim(boss, moving=False):
        """Controller: delta time, state + prioritas, timeline serangan."""
        NS = _NS_zharok

        # ── delta time nyata ────────────────────────────────────────
        try:
            now = pygame.time.get_ticks()
        except Exception:                              # pragma: no cover
            now = 0
        prev_ms = getattr(boss, "_zh_last_ms", None)
        if prev_ms is None:
            dt = 1.0 / 60.0
        else:
            dt = (now - prev_ms) / 1000.0
            if dt <= 0.0 or dt > 0.05:
                dt = 1.0 / 60.0
        boss._zh_last_ms = now
        boss._zh_dt = dt

        # ── timeline serangan (timer engine menghitung MUNDUR) ──────
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 40)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_zh_prev_timer", 0))
        active = bool(getattr(boss, "_zh_attack_active", False))

        # serangan baru: timer melonjak naik (di-reset ke cooldown)
        if timer > previous + 1 and timer >= cooldown - 2:
            boss._zh_attack_active = True
            boss._zh_attack_frame = 0
            boss._zh_atk_spawned = False
            boss._zh_melee_swing = NS._melee_reach(boss)
            active = True
        elif active:
            boss._zh_attack_frame = int(
                getattr(boss, "_zh_attack_frame", 0)) + 1
            if boss._zh_attack_frame > cooldown:
                boss._zh_attack_active = False
                boss._zh_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._zh_attack_active = False
            boss._zh_attack_frame = 0
            active = False

        boss._zh_prev_timer = timer
        frame = int(getattr(boss, "_zh_attack_frame", 0))
        # durasi animasi dibatasi supaya tarikan busur tetap punya bobot
        anim_len = max(10, min(cooldown - 1, 30))
        progress = min(1.0, frame / float(anim_len)) if active else 0.0
        boss._zh_attack_progress = progress
        boss._zh_attack_phase = (NS.attack_phase(progress) if active
                                 else "NONE")
        lo, hi = NS.ATTACK_ACTIVE_WINDOW
        boss._zh_hit_window = bool(active and lo <= progress <= hi)
        if not active:
            boss._zh_melee_swing = False

        # ── prioritas state ─────────────────────────────────────────
        skill = getattr(boss, "active_skill", None)
        alive = bool(getattr(boss, "alive", True))
        hurt = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        speed = float(getattr(boss, "_zh_speed", 0.0))
        melee = bool(getattr(boss, "_zh_melee_swing", False))

        if not alive:
            state = "DEATH"
        elif skill == "r":
            state = "SPECIAL"
        elif skill in ("q", "w", "e"):
            state = "SKILL"
        elif active and progress < 0.12:
            state = "CHARGE"
        elif active and progress < 0.30:
            state = "ATTACK"
        elif active:
            if melee:
                state = "SWING" if progress < 0.62 else "ATTACK"
            else:
                state = "CAST" if progress < 0.62 else "ATTACK"
        elif hurt > 0:
            state = "HURT"
        elif moving:
            state = "RUN" if speed > 1.6 else "WALK"
        else:
            state = "IDLE"

        prev_state = getattr(boss, "_zh_state", "IDLE")
        if prev_state != state:
            boss._zh_state_prev = prev_state
            boss._zh_state_time = 0.0
        else:
            boss._zh_state_time = getattr(boss, "_zh_state_time", 0.0) + dt
        boss._zh_state = state
        boss._zh_state_priority = NS.ANIM_STATES.get(state, 0)
        return state

    @staticmethod
    def _resolve_pose(boss, moving):
        """(action, phase, attack_progress) untuk renderer + lapisan hidup."""
        NS = _NS_zharok
        pulse = float(getattr(boss, "pulse", 0.0))
        state = getattr(boss, "_zh_state", "IDLE")
        ap = float(getattr(boss, "_zh_attack_progress", 0.0) or 0.0)
        skill = getattr(boss, "active_skill", None)
        timer = int(getattr(boss, "active_skill_timer", 0))

        if state in ("SKILL", "SPECIAL") and skill in ("q", "w", "e", "r"):
            dur = NS.SKILL_DUR.get(skill, 50)
            prog = max(0.0, min(1.0, 1.0 - timer / float(dur)))
            action = {"q": "strafe", "w": "smoke", "e": "e_cast",
                      "r": "r_cast"}[skill]
            return action, pulse, prog
        if state in ("ATTACK", "SWING", "CHARGE", "CAST"):
            if getattr(boss, "_zh_melee_swing", False):
                return "melee", pulse, ap
            return "attack", pulse, ap
        if state == "RUN":
            return "walk", pulse * 2.6, 0.0
        if state == "WALK":
            return "walk", pulse * 2.3, 0.0
        if state == "DEATH":
            return "death", pulse, 0.0
        if state == "HURT":
            return "hurt", pulse, 0.0
        return "idle", pulse, 0.0

    # ===================================================================
    # ATTACK TIMELINE (7 keyframes + IMPACT frame at 0.52)
    # ===================================================================
    @staticmethod
    def _attack_pose(ap):
        keys = (
            (0.00,  0.0,  0.0,  0.0,  0.0,  0.0, 0, 0.0, 1.00),
            (0.20, -2.5, -4.0,  2.0,  0.6, 12.0, 0, 0.0, 1.15),
            (0.40, -4.0, -6.0,  3.0,  1.0, 20.0, 1, 0.0, 1.35),
            (0.46,  3.0,  4.0, -1.0,  0.4,  4.0, 0, 0.6, 1.25),
            (0.52,  6.5,  7.5,  2.5,  0.0, -3.0, 0, 1.0, 1.45),
            (0.70,  2.0,  3.0,  1.0,  0.0,  0.0, 0, 0.0, 1.10),
            (1.00,  0.0,  0.0,  0.0,  0.0,  0.0, 0, 0.0, 1.00),
        )
        ap = max(0.0, min(1.0, ap))
        for i in range(len(keys) - 1):
            k0, k1 = keys[i], keys[i + 1]
            if k0[0] <= ap <= k1[0]:
                span = max(1e-6, k1[0] - k0[0])
                t = (ap - k0[0]) / span
                t = t * t * (3 - 2 * t)
                vals = tuple(a + (b - a) * t for a, b in zip(k0[1:6], k1[1:6]))
                return {
                    "lunge": vals[0], "lean": vals[1], "dip": vals[2],
                    "draw": vals[3], "pull_px": vals[4],
                    "tremble": 1 if (k0[6] and t < 0.9) else 0,
                    "impact": 1.0 - min(1.0, abs(ap - 0.52) / 0.10),
                    "flare": k0[8] + (k1[8] - k0[8]) * t,
                }
        return {"lunge": 0.0, "lean": 0.0, "dip": 0.0, "draw": 0.0,
                "pull_px": 0.0, "tremble": 0, "impact": 0.0, "flare": 1.0}

    # ===================================================================
    # ANATOMY & RIG DRAWING
    # ===================================================================
    @staticmethod
    def _draw_hood_back(surface, cx, cy, facing, phase, cloth_lag=0.0, f=1):
        P = _NS_zharok.PALETTE
        for idx, (ox_base, w_base, h_base) in enumerate(((-9, 10, 36), (-2, 12, 42), (6, 10, 34))):
            wave = math.sin(phase * 1.8 + idx * 1.2) * (3.0 + idx * 1.2) - cloth_lag * (1.2 + idx * 0.4)
            top_x = cx + ox_base * f
            top_y = cy + 4
            spine = [
                (top_x, top_y),
                (top_x - f * 4 + wave * 0.4, top_y + h_base * 0.4),
                (top_x - f * 7 + wave * 0.8, top_y + h_base * 0.75),
                (top_x - f * 9 + wave, top_y + h_base),
            ]
            shadow_poly = [(p[0] + f, p[1] + 1) for p in _NS_zharok._tuft_points(spine, depth=w_base * 0.5, min_len=4.0, seed=idx * 7)]
            _NS_zharok._poly(surface, P["shadow_deep"], shadow_poly)
            _NS_zharok._poly(surface, P["hood_darkest"], _NS_zharok._tuft_points(spine, depth=w_base * 0.5, min_len=4.0, seed=idx * 7))
            _NS_zharok._poly(surface, P["hood_dark"], _NS_zharok._tuft_points(spine, depth=w_base * 0.38, min_len=4.0, seed=idx * 7 + 1))
            _NS_zharok._poly(surface, P["hood_mid"], _NS_zharok._tuft_points(spine, depth=w_base * 0.25, min_len=4.0, seed=idx * 7 + 2))
            _NS_zharok._poly(surface, P["hood_light"], _NS_zharok._tuft_points(spine, depth=w_base * 0.14, min_len=4.0, seed=idx * 7 + 3))
            if len(spine) >= 3:
                _NS_zharok._aaline(surface, P["hood_high"], spine[0], spine[1], 2)
                _NS_zharok._aaline(surface, P["hood_trim"], spine[1], spine[2], 1)
                _NS_zharok._aacircle(surface, P["hood_trim"], (int(spine[2][0]), int(spine[2][1])), 1)

    @staticmethod
    def _draw_quiver(surface, cx, cy, facing, phase, f=1):
        P = _NS_zharok.PALETTE
        qx = cx - 11 * f
        qy = cy - 10
        pts = [
            (qx - 5 * f, qy - 12),
            (qx + 4 * f, qy - 10),
            (qx + 2 * f, qy + 14),
            (qx - 4 * f, qy + 12),
        ]
        _NS_zharok._poly(surface, P["shadow_deep"], [(p[0] + f, p[1] + 1) for p in pts])
        _NS_zharok._poly(surface, P["leather_darkest"], pts)
        _NS_zharok._poly(surface, P["leather_dark"], [
            (qx - 4 * f, qy - 11),
            (qx + 3 * f, qy - 9),
            (qx + 1 * f, qy + 12),
            (qx - 3 * f, qy + 10),
        ])
        _NS_zharok._poly(surface, P["leather_mid"], [
            (qx - 3 * f, qy - 10),
            (qx + 1 * f, qy - 9),
            (qx + 0 * f, qy + 10),
            (qx - 2 * f, qy + 9),
        ])
        _NS_zharok._poly(surface, P["leather_light"], [
            (qx - 2 * f, qy - 9),
            (qx + 0 * f, qy - 8),
            (qx - 1 * f, qy + 8),
        ])
        _NS_zharok._aaline(surface, P["leather_high"], (qx - 2 * f, qy - 9), (qx - 1 * f, qy + 8), 1)

        _NS_zharok._aaline(surface, P["gold_dark"], (qx - 5 * f, qy - 12), (qx + 4 * f, qy - 10), 3)
        _NS_zharok._aaline(surface, P["gold_light"], (qx - 4 * f, qy - 12), (qx + 3 * f, qy - 10), 1)
        _NS_zharok._aacircle(surface, P["gold_shine"], (int(qx - 2 * f), int(qy - 11)), 1)
        _NS_zharok._aacircle(surface, P["metal_mid"], (int(qx + 2 * f), int(qy + 2)), 2)
        _NS_zharok._aacircle(surface, P["metal_light"], (int(qx + 2 * f), int(qy + 2)), 1)
        _NS_zharok._aacircle(surface, P["metal_high"], (int(qx + 2 * f - f), int(qy + 1)), 1)

        for i, (ox, oy_off, ang_deg) in enumerate(((-3, -16, -15), (0, -20, 0), (3, -17, 12))):
            base_x = qx + ox * f
            base_y = qy - 11
            rad = math.radians(ang_deg * f)
            len_arr = 14 + (i % 2) * 3
            tip_x = base_x - math.sin(rad) * len_arr
            tip_y = base_y - math.cos(rad) * len_arr
            _NS_zharok._aaline(surface, P["shadow_deep"], (base_x + f, base_y + 1), (tip_x + f, tip_y + 1), 2)
            _NS_zharok._aaline(surface, P["wood_dark"], (base_x, base_y), (tip_x, tip_y), 2)
            _NS_zharok._aaline(surface, P["wood_light"], (base_x, base_y), (tip_x, tip_y), 1)
            _NS_zharok._aaline(surface, P["wood_high"], (base_x - f, base_y), (tip_x - f, tip_y), 1)
            perp_x = -math.cos(rad) * f * 3.5
            perp_y = math.sin(rad) * 3.5
            _NS_zharok._poly(surface, P["hood_dark"], [
                (tip_x, tip_y),
                (tip_x + perp_x, tip_y + perp_y + 3),
                (tip_x - perp_x * 0.4, tip_y - perp_y * 0.4 + 4),
            ])
            _NS_zharok._poly(surface, P["hood_light"], [
                (tip_x, tip_y),
                (tip_x - perp_x, tip_y - perp_y + 3),
                (tip_x, tip_y + 4),
            ])
            _NS_zharok._aacircle(surface, P["fire_dark"], (int(tip_x), int(tip_y)), 3)
            _NS_zharok._aacircle(surface, P["fire_bright"], (int(tip_x), int(tip_y)), 2)
            _NS_zharok._aacircle(surface, P["fire_hot"], (int(tip_x), int(tip_y)), 1)
            _NS_zharok._aacircle(surface, P["fire_white"], (int(tip_x), int(tip_y)), 1)

    @staticmethod
    def _draw_pelvis(surface, cx, cy, phase, f=1):
        P = _NS_zharok.PALETTE
        pelvis_pts = [
            (cx - 11 * f, cy + 2),
            (cx + 9 * f, cy + 2),
            (cx + 10 * f, cy + 8),
            (cx + 3 * f, cy + 13),
            (cx - 5 * f, cy + 13),
            (cx - 12 * f, cy + 8),
        ]
        _NS_zharok._poly(surface, P["shadow_deep"], [(p[0] + f, p[1] + 1) for p in pelvis_pts])
        _NS_zharok._poly(surface, P["bone_darkest"], pelvis_pts)
        _NS_zharok._poly(surface, P["bone_dark"], [
            (cx - 10 * f, cy + 3),
            (cx + 8 * f, cy + 3),
            (cx + 8 * f, cy + 7),
            (cx + 2 * f, cy + 11),
            (cx - 4 * f, cy + 11),
            (cx - 10 * f, cy + 7),
        ])
        _NS_zharok._poly(surface, P["bone_mid"], [
            (cx - 8 * f, cy + 3),
            (cx + 6 * f, cy + 3),
            (cx + 5 * f, cy + 6),
            (cx - 1 * f, cy + 9),
            (cx - 8 * f, cy + 6),
        ])
        _NS_zharok._poly(surface, P["bone_light"], [
            (cx - 7 * f, cy + 3),
            (cx + 3 * f, cy + 3),
            (cx - 2 * f, cy + 5),
        ])
        _NS_zharok._poly(surface, P["bone_high"], [
            (cx - 6 * f, cy + 3),
            (cx + 1 * f, cy + 3),
            (cx - 3 * f, cy + 4),
        ])
        _NS_zharok._aaline(surface, P["bone_rim"], (cx - 5 * f, cy + 3), (cx - 1 * f, cy + 3), 1)

        for h_off in (-5, 3):
            _NS_zharok._ellipse(surface, P["shadow_deep"], (cx + h_off * f - 2, cy + 6, 4, 3))

        _NS_zharok._rect(surface, P["shadow_deep"], (cx - 12 * f if f < 0 else cx - 11, cy - 2, 23, 6), border_radius=1)
        _NS_zharok._rect(surface, P["leather_darkest"], (cx - 12 * f if f < 0 else cx - 11, cy - 2, 23, 5), border_radius=1)
        _NS_zharok._rect(surface, P["leather_dark"], (cx - 11 * f if f < 0 else cx - 10, cy - 1, 21, 3))
        _NS_zharok._rect(surface, P["leather_mid"], (cx - 10 * f if f < 0 else cx - 9, cy - 1, 19, 1))
        _NS_zharok._aaline(surface, P["leather_light"], (cx - 8 * f, cy - 1), (cx + 6 * f, cy - 1), 1)

        bx = cx - 1 * f
        by = cy + 1
        _NS_zharok._aacircle(surface, P["gold_dark"], (bx, by), 4)
        _NS_zharok._aacircle(surface, P["gold_mid"], (bx, by), 3)
        _NS_zharok._aacircle(surface, P["gold_light"], (bx - f, by - 1), 2)
        _NS_zharok._aacircle(surface, P["gold_shine"], (bx - f, by - 1), 1)
        _NS_zharok._aacircle(surface, P["fire_bright"], (bx, by), 1)

    @staticmethod
    def _draw_skeleton_legs(surface, cx, cy, facing, phase, action, f=1):
        P = _NS_zharok.PALETTE
        walk = action == "walk"
        speed = 2.4 if walk else 0.8

        for leg_idx, (side_sign, base_x) in enumerate(((-1, -7), (1, 5))):
            ph = phase * speed + (0 if side_sign < 0 else math.pi)
            if walk:
                lift = max(0.0, math.sin(ph)) * 6.0
                stride = math.cos(ph) * 7.0 * f
                knee_fwd = (math.sin(ph) * 3.0 + 2.0) * f
            else:
                lift = abs(math.sin(phase * 0.8 + leg_idx * 1.5)) * 1.0
                stride = 0.0
                knee_fwd = 1.0 * f

            hip_x = cx + base_x * f
            hip_y = cy + 10
            knee_x = hip_x + (stride * 0.4 + knee_fwd)
            knee_y = hip_y + 16 - lift * 0.4
            ankle_x = hip_x + stride
            ankle_y = hip_y + 32 - lift
            toe_x = ankle_x + 6 * f
            toe_y = ankle_y + 2

            if walk and lift < 1.5:
                _NS_zharok._ellipse(surface, P["shadow_deep"], (ankle_x - 5, ankle_y + 1, 10, 4))
                if int(ph * 10) % 3 == 0:
                    _NS_zharok._aacircle(surface, P["fire_dark"], (int(ankle_x - 4 * f), int(ankle_y)), 2)

            _NS_zharok._aaline(surface, P["shadow_deep"], (hip_x + f, hip_y + 1), (knee_x + f, knee_y + 1), 5)
            _NS_zharok._aaline(surface, P["bone_darkest"], (hip_x, hip_y), (knee_x, knee_y), 4)
            _NS_zharok._aaline(surface, P["bone_dark"], (hip_x, hip_y), (knee_x, knee_y), 3)
            _NS_zharok._aaline(surface, P["bone_mid"], (hip_x, hip_y), (knee_x, knee_y), 2)
            _NS_zharok._aaline(surface, P["bone_light"], (hip_x - f, hip_y), (knee_x - f, knee_y), 1)
            _NS_zharok._aaline(surface, P["bone_high"], (hip_x - f, hip_y - 1), (knee_x - f, knee_y - 1), 1)

            _NS_zharok._aacircle(surface, P["shadow_deep"], (knee_x + f, knee_y + 1), 4)
            _NS_zharok._aacircle(surface, P["bone_darkest"], (knee_x, knee_y), 4)
            _NS_zharok._aacircle(surface, P["bone_mid"], (knee_x, knee_y), 3)
            _NS_zharok._aacircle(surface, P["bone_light"], (knee_x - f, knee_y - 1), 2)
            _NS_zharok._aacircle(surface, P["bone_high"], (knee_x - f, knee_y - 1), 1)
            _NS_zharok._aacircle(surface, P["bone_shine"], (knee_x - f, knee_y - 1), 1)

            _NS_zharok._aaline(surface, P["shadow_deep"], (knee_x + f, knee_y + 1), (ankle_x + f, ankle_y + 1), 4)
            _NS_zharok._aaline(surface, P["bone_darkest"], (knee_x, knee_y), (ankle_x, ankle_y), 3)
            _NS_zharok._aaline(surface, P["bone_dark"], (knee_x, knee_y), (ankle_x, ankle_y), 2)
            _NS_zharok._aaline(surface, P["bone_mid"], (knee_x, knee_y), (ankle_x, ankle_y), 1)
            _NS_zharok._aaline(surface, P["bone_rim"], (knee_x - f, knee_y), (ankle_x - f, ankle_y), 1)

            mid_shin_x = (knee_x + ankle_x) * 0.5
            mid_shin_y = (knee_y + ankle_y) * 0.5
            _NS_zharok._rect(surface, P["leather_darkest"], (mid_shin_x - 3, mid_shin_y - 2, 6, 4), border_radius=1)
            _NS_zharok._rect(surface, P["leather_mid"], (mid_shin_x - 2, mid_shin_y - 1, 4, 2))
            _NS_zharok._rect(surface, P["metal_mid"], (mid_shin_x - 1, mid_shin_y - 1, 2, 2))
            _NS_zharok._aacircle(surface, P["gold_light"], (int(mid_shin_x), int(mid_shin_y)), 1)

            foot_pts = [
                (ankle_x - 3 * f, ankle_y),
                (ankle_x + 2 * f, ankle_y - 1),
                (toe_x + 2 * f, toe_y + 1),
                (toe_x - 1 * f, toe_y + 2),
                (ankle_x - 3 * f, ankle_y + 2),
            ]
            _NS_zharok._poly(surface, P["shadow_deep"], [(p[0] + f, p[1] + 1) for p in foot_pts])
            _NS_zharok._poly(surface, P["bone_darkest"], foot_pts)
            _NS_zharok._poly(surface, P["bone_mid"], [
                (ankle_x - 2 * f, ankle_y),
                (ankle_x + 1 * f, ankle_y),
                (toe_x, toe_y + 1),
                (ankle_x - 2 * f, ankle_y + 1),
            ])
            _NS_zharok._poly(surface, P["bone_light"], [
                (ankle_x - 1 * f, ankle_y),
                (toe_x - 1 * f, toe_y),
                (ankle_x - 1 * f, ankle_y + 1),
            ])

    @staticmethod
    def _draw_ribcage(surface, cx, cy, phase, sway=0, f=1):
        P = _NS_zharok.PALETTE
        for s_idx in range(7):
            sy = cy - 14 + s_idx * 4
            _NS_zharok._aacircle(surface, P["shadow_deep"], (cx + f, sy + 1), 3)
            _NS_zharok._aacircle(surface, P["bone_darkest"], (cx, sy), 3)
            _NS_zharok._aacircle(surface, P["bone_dark"], (cx, sy), 2)
            _NS_zharok._aacircle(surface, P["bone_mid"], (cx - f, sy - 1), 1)
            _NS_zharok._aacircle(surface, P["bone_shine"], (cx - f, sy - 1), 1)

        pulse = math.sin(phase * 3.0) * 0.25 + 0.75
        hx, hy = cx - 1 * f, cy - 4
        _NS_zharok._aacircle(surface, P["soul_dark"], (hx, hy), 7)
        _NS_zharok._aacircle(surface, P["soul_mid"], (hx, hy), 5)
        _NS_zharok._aacircle(surface, P["soul_hot"], (hx, hy), 3)
        _NS_zharok._aacircle(surface, P["soul_glow"], (hx, hy), 2)
        _NS_zharok._aacircle(surface, P["fire_seam"], (hx, hy), 1)

        for i, ry_off in enumerate((-12, -8, -4, 0, 4)):
            w_rib = 10 - abs(i - 2) * 1.5
            curve = 2.0 - abs(i - 2) * 0.5
            for side in (-1, 1):
                p0 = (cx + side * 2 * f, cy + ry_off)
                p1 = (cx + side * (w_rib * 0.6) * f, cy + ry_off + curve)
                p2 = (cx + side * w_rib * f, cy + ry_off + curve * 2.2)
                p3 = (cx + side * (w_rib * 0.7) * f, cy + ry_off + curve * 3.0)

                _NS_zharok._aaline(surface, P["shadow_deep"], (p0[0] + f, p0[1] + 1), (p1[0] + f, p1[1] + 1), 3)
                _NS_zharok._aaline(surface, P["shadow_deep"], (p1[0] + f, p1[1] + 1), (p2[0] + f, p2[1] + 1), 3)
                _NS_zharok._aaline(surface, P["shadow_deep"], (p2[0] + f, p2[1] + 1), (p3[0] + f, p3[1] + 1), 2)

                _NS_zharok._aaline(surface, P["bone_darkest"], p0, p1, 3)
                _NS_zharok._aaline(surface, P["bone_darkest"], p1, p2, 3)
                _NS_zharok._aaline(surface, P["bone_darkest"], p2, p3, 2)

                _NS_zharok._aaline(surface, P["bone_dark"], p0, p1, 2)
                _NS_zharok._aaline(surface, P["bone_dark"], p1, p2, 2)
                _NS_zharok._aaline(surface, P["bone_dark"], p2, p3, 1)

                _NS_zharok._aaline(surface, P["bone_mid"], (p0[0] - f, p0[1]), (p1[0] - f, p1[1]), 1)
                _NS_zharok._aaline(surface, P["bone_mid"], (p1[0] - f, p1[1]), (p2[0] - f, p2[1]), 1)
                _NS_zharok._aaline(surface, P["bone_light"], (p0[0] - f, p0[1] - 1), (p1[0] - f, p1[1] - 1), 1)
                _NS_zharok._aaline(surface, P["bone_high"], (p0[0] - f, p0[1] - 1), (p1[0] - f, p1[1] - 1), 1)

                if abs(ry_off - (-4)) <= 4:
                    _NS_zharok._aacircle(surface, P["fire_bright"], (int(p1[0]), int(p1[1])), 1)

        _NS_zharok._aaline(surface, P["shadow_deep"], (cx - 13 * f + f, cy - 14 + 1), (cx + 12 * f + f, cy - 14 + 1), 3)
        _NS_zharok._aaline(surface, P["bone_darkest"], (cx - 13 * f, cy - 14), (cx + 12 * f, cy - 14), 3)
        _NS_zharok._aaline(surface, P["bone_dark"], (cx - 12 * f, cy - 14), (cx + 11 * f, cy - 14), 2)
        _NS_zharok._aaline(surface, P["bone_mid"], (cx - 11 * f, cy - 15), (cx + 10 * f, cy - 15), 1)
        _NS_zharok._aaline(surface, P["bone_light"], (cx - 8 * f, cy - 15), (cx + 6 * f, cy - 15), 1)
        _NS_zharok._aaline(surface, P["bone_shine"], (cx - 7 * f, cy - 15), (cx + 3 * f, cy - 15), 1)

    @staticmethod
    def _draw_hooded_skull(surface, cx, cy, facing, phase, action="idle", f=1, stealth=False, detail=False):
        P = _NS_zharok.PALETTE
        hx = cx
        hy = cy - 4

        hood_outer = [
            (hx - 14 * f, hy + 12),
            (hx - 15 * f, hy - 4),
            (hx - 12 * f, hy - 14),
            (hx - 4 * f, hy - 18),
            (hx + 5 * f, hy - 18),
            (hx + 13 * f, hy - 14),
            (hx + 15 * f, hy - 3),
            (hx + 13 * f, hy + 12),
            (hx + 7 * f, hy + 10),
            (hx - 6 * f, hy + 10),
        ]
        _NS_zharok._poly(surface, P["shadow_deep"], [(p[0] + f, p[1] + 1) for p in hood_outer])
        _NS_zharok._poly(surface, P["hood_darkest"], hood_outer)
        _NS_zharok._poly(surface, P["hood_dark"], [
            (hx - 13 * f, hy + 10),
            (hx - 13 * f, hy - 3),
            (hx - 10 * f, hy - 12),
            (hx - 3 * f, hy - 16),
            (hx + 4 * f, hy - 16),
            (hx + 11 * f, hy - 12),
            (hx + 13 * f, hy - 2),
            (hx + 11 * f, hy + 10),
        ])
        _NS_zharok._poly(surface, P["hood_mid"], [
            (hx - 11 * f, hy + 8),
            (hx - 11 * f, hy - 2),
            (hx - 8 * f, hy - 10),
            (hx, hy - 14),
            (hx + 8 * f, hy - 10),
            (hx + 10 * f, hy - 2),
            (hx + 9 * f, hy + 8),
        ])
        _NS_zharok._poly(surface, P["hood_light"], [
            (hx - 8 * f, hy - 8),
            (hx, hy - 12),
            (hx + 6 * f, hy - 8),
            (hx + 4 * f, hy - 2),
            (hx - 6 * f, hy - 2),
        ])
        _NS_zharok._poly(surface, P["hood_high"], [
            (hx - 6 * f, hy - 10),
            (hx, hy - 13),
            (hx + 4 * f, hy - 10),
        ])
        _NS_zharok._aaline(surface, P["hood_trim"], (hx - 7 * f, hy - 9), (hx + 5 * f, hy - 9), 1)

        _NS_zharok._poly(surface, P["shadow_deep"], [
            (hx - 9 * f, hy - 6),
            (hx + 9 * f, hy - 6),
            (hx + 8 * f, hy + 8),
            (hx, hy + 11),
            (hx - 8 * f, hy + 8),
        ])

        _NS_zharok._aacircle(surface, P["shadow_deep"], (hx + f, hy + 1), 9)
        _NS_zharok._aacircle(surface, P["bone_darkest"], (hx, hy), 9)
        _NS_zharok._aacircle(surface, P["bone_dark"], (hx, hy), 8)
        _NS_zharok._aacircle(surface, P["bone_mid"], (hx - f, hy - 1), 7)
        _NS_zharok._aacircle(surface, P["bone_light"], (hx - 2 * f, hy - 2), 5)
        _NS_zharok._aacircle(surface, P["bone_high"], (hx - 2 * f, hy - 3), 3)
        _NS_zharok._aacircle(surface, P["bone_shine"], (hx - 3 * f, hy - 4), 1)
        _NS_zharok._aacircle(surface, P["bone_rim"], (hx - 3 * f, hy - 5), 1)

        _NS_zharok._aaline(surface, P["shadow_deep"], (hx - 7 * f + f, hy - 4 + 1), (hx + 7 * f + f, hy - 4 + 1), 3)
        _NS_zharok._aaline(surface, P["bone_darkest"], (hx - 7 * f, hy - 4), (hx + 7 * f, hy - 4), 3)
        _NS_zharok._aaline(surface, P["bone_mid"], (hx - 6 * f, hy - 5), (hx + 6 * f, hy - 5), 2)
        _NS_zharok._aaline(surface, P["bone_light"], (hx - 5 * f, hy - 5), (hx + 4 * f, hy - 5), 1)

        eye_pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        for eye_side in (-1, 1):
            ex = hx + (eye_side * 4 + 1) * f
            ey = hy - 1
            _NS_zharok._aacircle(surface, P["shadow_deep"], (ex, ey), 4)
            _NS_zharok._aacircle(surface, P["eye_dark"], (ex, ey), 3)
            _NS_zharok._aacircle(surface, P["fire_dark"], (ex, ey), 4)
            _NS_zharok._aacircle(surface, P["eye_bright"], (ex, ey), 2)
            _NS_zharok._aacircle(surface, P["eye_hot"], (ex, ey), 1)
            _NS_zharok._aacircle(surface, P["eye_white"], (ex - f, ey - 1), 1)

        _NS_zharok._poly(surface, P["shadow_deep"], [
            (hx + 0 * f, hy + 2),
            (hx - 2 * f, hy + 5),
            (hx + 2 * f, hy + 5),
        ])

        _NS_zharok._rect(surface, P["shadow_deep"], (hx - 5 * f if f < 0 else hx - 4, hy + 6, 9, 4), border_radius=1)
        _NS_zharok._rect(surface, P["bone_darkest"], (hx - 5 * f if f < 0 else hx - 4, hy + 6, 9, 3), border_radius=1)
        for tooth in (-4, -2, 0, 2, 4):
            tx = hx + tooth * f
            _NS_zharok._rect(surface, P["bone_high"], (tx, hy + 6, 1, 3))
            _NS_zharok._rect(surface, P["bone_shine"], (tx, hy + 7, 1, 1))

        flame_w = math.sin(phase * 3.5) * 2.0
        plume_spine = [
            (hx, hy - 10),
            (hx - f * 2 + flame_w * 0.5, hy - 20),
            (hx - f * 4 + flame_w, hy - 32),
            (hx - f * 5 + flame_w * 1.5, hy - 44),
        ]
        _NS_zharok._poly(surface, P["fire_darkest"], _NS_zharok._tuft_points(plume_spine, depth=7.0, min_len=4.0, seed=11))
        _NS_zharok._poly(surface, P["fire_dark"], _NS_zharok._tuft_points(plume_spine, depth=5.5, min_len=4.0, seed=12))
        _NS_zharok._poly(surface, P["fire_mid"], _NS_zharok._tuft_points(plume_spine, depth=4.0, min_len=4.0, seed=13))
        _NS_zharok._poly(surface, P["fire_bright"], _NS_zharok._tuft_points(plume_spine, depth=2.5, min_len=4.0, seed=14))
        _NS_zharok._poly(surface, P["fire_hot"], _NS_zharok._tuft_points(plume_spine, depth=1.5, min_len=4.0, seed=15))
        _NS_zharok._poly(surface, P["fire_white"], _NS_zharok._tuft_points(plume_spine, depth=0.8, min_len=4.0, seed=16))

        for s_idx, side_off in enumerate((-6, 5)):
            fw = math.sin(phase * 4.0 + s_idx) * 2.0
            side_spine = [
                (hx + side_off * f, hy - 8),
                (hx + (side_off - 2) * f + fw, hy - 18),
                (hx + (side_off - 4) * f + fw * 1.3, hy - 28),
            ]
            _NS_zharok._poly(surface, P["fire_dark"], _NS_zharok._tuft_points(side_spine, depth=4.0, min_len=3.0, seed=s_idx + 21))
            _NS_zharok._poly(surface, P["fire_bright"], _NS_zharok._tuft_points(side_spine, depth=2.5, min_len=3.0, seed=s_idx + 22))
            _NS_zharok._poly(surface, P["fire_hot"], _NS_zharok._tuft_points(side_spine, depth=1.2, min_len=3.0, seed=s_idx + 23))

    @staticmethod
    def _draw_flaming_bow(surface, hx, hy, facing, pose, phase, pull=0,
                           arrow_x=None, arrow_y=None, ap=0.0):
        P = _NS_zharok.PALETTE
        f = 1 if facing >= 0 else -1

        bow_top_y = hy - 28
        bow_bot_y = hy + 28
        curve_out = 12 * f

        bow_pts = []
        for t_step in range(13):
            u = t_step / 12.0
            y = bow_top_y + (bow_bot_y - bow_top_y) * u
            parab = 1.0 - (u - 0.5) ** 2 * 4.0
            recurve = math.sin(u * math.pi * 2.0) * 2.5 * f
            x = hx + curve_out * parab + recurve
            bow_pts.append((x, y))

        for i in range(len(bow_pts) - 1):
            p0 = bow_pts[i]
            p1 = bow_pts[i + 1]
            _NS_zharok._aaline(surface, P["shadow_deep"], (p0[0] + f, p0[1] + 1), (p1[0] + f, p1[1] + 1), 4)
            _NS_zharok._aaline(surface, P["wood_dark"], p0, p1, 4)
            _NS_zharok._aaline(surface, P["wood_mid"], p0, p1, 3)
            _NS_zharok._aaline(surface, P["wood_light"], (p0[0] - f, p0[1]), (p1[0] - f, p1[1]), 2)
            _NS_zharok._aaline(surface, P["wood_high"], (p0[0] - f, p0[1] - 1), (p1[0] - f, p1[1] - 1), 1)

        for b_idx in (3, 9):
            bx, by = bow_pts[b_idx]
            _NS_zharok._aacircle(surface, P["metal_darkest"], (bx, by), 3)
            _NS_zharok._aacircle(surface, P["metal_mid"], (bx, by), 2)
            _NS_zharok._aacircle(surface, P["gold_mid"], (bx, by), 2)
            _NS_zharok._aacircle(surface, P["gold_shine"], (bx - f, by - 1), 1)

        for tip in (bow_pts[0], bow_pts[-1]):
            _NS_zharok._aacircle(surface, P["metal_darkest"], (tip[0] + f, tip[1] + 1), 3)
            _NS_zharok._aacircle(surface, P["gold_dark"], tip, 3)
            _NS_zharok._aacircle(surface, P["gold_light"], tip, 2)
            _NS_zharok._aacircle(surface, P["gold_shine"], (tip[0] - f, tip[1] - 1), 1)

        top_tip = bow_pts[0]
        bot_tip = bow_pts[-1]

        if arrow_x is not None:
            nock_x = arrow_x
            nock_y = arrow_y
            _NS_zharok._aaline(surface, P["shadow_deep"], (top_tip[0] + f, top_tip[1] + 1), (nock_x + f, nock_y + 1), 2)
            _NS_zharok._aaline(surface, P["metal_mid"], top_tip, (nock_x, nock_y), 2)
            _NS_zharok._aaline(surface, P["fire_glow"], top_tip, (nock_x, nock_y), 1)

            _NS_zharok._aaline(surface, P["shadow_deep"], (bot_tip[0] + f, bot_tip[1] + 1), (nock_x + f, nock_y + 1), 2)
            _NS_zharok._aaline(surface, P["metal_mid"], bot_tip, (nock_x, nock_y), 2)
            _NS_zharok._aaline(surface, P["fire_glow"], bot_tip, (nock_x, nock_y), 1)

            arrow_len = 38 + pull
            tip_arr_x = nock_x + f * arrow_len
            tip_arr_y = nock_y
            _NS_zharok._aaline(surface, P["shadow_deep"], (nock_x + f, nock_y + 1), (tip_arr_x + f, tip_arr_y + 1), 3)
            _NS_zharok._aaline(surface, P["wood_dark"], (nock_x, nock_y), (tip_arr_x, tip_arr_y), 2)
            _NS_zharok._aaline(surface, P["wood_light"], (nock_x, nock_y), (tip_arr_x, tip_arr_y), 1)
            _NS_zharok._aaline(surface, P["wood_high"], (nock_x, nock_y - 1), (tip_arr_x, tip_arr_y - 1), 1)

            _NS_zharok._poly(surface, P["hood_dark"], [
                (nock_x, nock_y),
                (nock_x - f * 5, nock_y - 3),
                (nock_x - f * 2, nock_y),
            ])
            _NS_zharok._poly(surface, P["hood_dark"], [
                (nock_x, nock_y),
                (nock_x - f * 5, nock_y + 3),
                (nock_x - f * 2, nock_y),
            ])

            head_pts = [
                (tip_arr_x + f * 5, tip_arr_y),
                (tip_arr_x - f * 3, tip_arr_y - 3),
                (tip_arr_x - f * 1, tip_arr_y),
                (tip_arr_x - f * 3, tip_arr_y + 3),
            ]
            _NS_zharok._poly(surface, P["shadow_deep"], [(p[0] + f, p[1] + 1) for p in head_pts])
            _NS_zharok._poly(surface, P["metal_darkest"], head_pts)
            _NS_zharok._poly(surface, P["metal_mid"], [
                (tip_arr_x + f * 4, tip_arr_y),
                (tip_arr_x - f * 2, tip_arr_y - 2),
                (tip_arr_x, tip_arr_y),
            ])
            _NS_zharok._aacircle(surface, P["metal_shine"], (int(tip_arr_x + f * 3), int(tip_arr_y)), 1)
            _NS_zharok._aacircle(surface, P["metal_high"], (int(tip_arr_x + f * 4), int(tip_arr_y)), 1)

            _NS_zharok._aacircle(surface, P["fire_dark"], (int(tip_arr_x), int(tip_arr_y)), 5)
            _NS_zharok._aacircle(surface, P["fire_bright"], (int(tip_arr_x), int(tip_arr_y)), 3)
            _NS_zharok._aacircle(surface, P["fire_hot"], (int(tip_arr_x), int(tip_arr_y)), 2)
            _NS_zharok._aacircle(surface, P["fire_white"], (int(tip_arr_x), int(tip_arr_y)), 1)
        else:
            _NS_zharok._aaline(surface, P["shadow_deep"], (top_tip[0] + f, top_tip[1] + 1), (bot_tip[0] + f, bot_tip[1] + 1), 2)
            _NS_zharok._aaline(surface, P["metal_light"], top_tip, bot_tip, 1)
            _NS_zharok._aaline(surface, P["fire_glow"], top_tip, bot_tip, 1)

        for fl_idx, step_val in enumerate((2, 4, 8, 10)):
            fx, fy = bow_pts[step_val]
            fw = math.sin(phase * 4.0 + fl_idx) * 2.0
            _NS_zharok._aacircle(surface, P["fire_dark"], (int(fx + fw), int(fy)), 4)
            _NS_zharok._aacircle(surface, P["fire_bright"], (int(fx + fw), int(fy)), 2)
            _NS_zharok._aacircle(surface, P["fire_hot"], (int(fx + fw), int(fy)), 1)
            _NS_zharok._aacircle(surface, P["fire_white"], (int(fx + fw), int(fy)), 1)

    # ── Arms & Holding Modes ─────────────────────────────────────────
    @staticmethod
    def _draw_bone_arm(surface, x1, y1, x2, y2):
        P = _NS_zharok.PALETTE
        _NS_zharok._aaline(surface, P["shadow_deep"], (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 4)
        _NS_zharok._aaline(surface, P["bone_darkest"], (x1, y1), (x2, y2), 4)
        _NS_zharok._aaline(surface, P["bone_dark"], (x1, y1), (x2, y2), 3)
        _NS_zharok._aaline(surface, P["bone_mid"], (x1, y1), (x2, y2), 2)
        _NS_zharok._aaline(surface, P["bone_light"], (x1 - 1, y1), (x2 - 1, y2), 1)
        _NS_zharok._aaline(surface, P["bone_rim"], (x1 - 1, y1 - 1), (x2 - 1, y2 - 1), 1)

    @staticmethod
    def _draw_skeleton_hand(surface, x, y, facing):
        P = _NS_zharok.PALETTE
        f = 1 if facing >= 0 else -1
        _NS_zharok._aacircle(surface, P["bone_darkest"], (x, y), 3)
        _NS_zharok._aacircle(surface, P["bone_mid"], (x, y), 2)
        _NS_zharok._aacircle(surface, P["bone_light"], (x - f, y - 1), 1)
        _NS_zharok._aacircle(surface, P["bone_shine"], (x - f, y - 1), 1)
        for off in (-2, 0, 2):
            _NS_zharok._aaline(surface, P["bone_mid"], (x, y), (x + f * 4, y + off), 1)
            _NS_zharok._aacircle(surface, P["bone_light"], (x + f * 4, y + off), 1)

    @staticmethod
    def _draw_bow_idle_arms(surface, cx, cy, facing, phase):
        f = 1 if facing >= 0 else -1
        sh_x, sh_y = cx + 8 * f, cy - 8
        grip_x, grip_y = cx + 20 * f, cy + 4
        elbow_x = cx + 16 * f
        elbow_y = cy - 2
        _NS_zharok._draw_bone_arm(surface, sh_x, sh_y, elbow_x, elbow_y)
        _NS_zharok._draw_bone_arm(surface, elbow_x, elbow_y, grip_x, grip_y)
        _NS_zharok._draw_skeleton_hand(surface, grip_x, grip_y, facing)
        _NS_zharok._draw_flaming_bow(surface, grip_x, grip_y, facing, "idle", phase)

    @staticmethod
    def _draw_bow_attack_arms(surface, cx, cy, facing, phase, progress):
        f = 1 if facing >= 0 else -1
        pose = _NS_zharok._attack_pose(progress)
        sh_front_x, sh_front_y = cx + 8 * f, cy - 8
        sh_back_x, sh_back_y = cx - 8 * f, cy - 8

        grip_x = cx + int((24 + pose["lunge"] * 0.8) * f)
        grip_y = cy + int(pose["dip"] * 0.5)
        elbow_front_x = cx + 18 * f
        elbow_front_y = cy - 4
        _NS_zharok._draw_bone_arm(surface, sh_front_x, sh_front_y, elbow_front_x, elbow_front_y)
        _NS_zharok._draw_bone_arm(surface, elbow_front_x, elbow_front_y, grip_x, grip_y)
        _NS_zharok._draw_skeleton_hand(surface, grip_x, grip_y, facing)

        pull_px = pose["pull_px"]
        nock_x = grip_x - int(pull_px * f)
        nock_y = grip_y
        elbow_back_x = cx - int(12 * f)
        elbow_back_y = cy - 6
        _NS_zharok._draw_bone_arm(surface, sh_back_x, sh_back_y, elbow_back_x, elbow_back_y)
        _NS_zharok._draw_bone_arm(surface, elbow_back_x, elbow_back_y, nock_x, nock_y)
        _NS_zharok._draw_skeleton_hand(surface, nock_x, nock_y, -facing)

        if pose["draw"] > 0.05:
            _NS_zharok._draw_flaming_bow(surface, grip_x, grip_y, facing, "drawn", phase,
                                        pull=int(pose["draw"] * 8),
                                        arrow_x=nock_x, arrow_y=nock_y, ap=progress)
        else:
            _NS_zharok._draw_flaming_bow(surface, grip_x, grip_y, facing, "idle", phase, ap=progress)

        if pose["impact"] > 0.1:
            _NS_zharok._draw_bow_release_flash(surface, grip_x + 12 * f, grip_y, pose["impact"])
            _NS_zharok._draw_bow_smear_arc(surface, grip_x, grip_y, facing, progress)

    @staticmethod
    def _draw_bow_strafe_arms(surface, cx, cy, facing, phase, progress=0.0):
        shot_prog = (progress * 6.0) % 1.0
        _NS_zharok._draw_bow_attack_arms(surface, cx, cy, facing, phase, shot_prog)

    # ── MELEE CLEAVE: stave busur dipakai seperti sabit ──────────────
    @staticmethod
    def _draw_cleaving_bow(surface, gx, gy, facing, theta, phase, heat=1.0):
        """Stave busur menyala digambar SEPANJANG sumbu ``theta``.

        Geometrinya diturunkan dari ``bow_geometry`` yang sama yang dibaca
        lapisan hidup, jadi trail sabetan menempel persis di stave.
        """
        P = _NS_zharok.PALETTE
        f = 1 if facing >= 0 else -1
        L = _NS_zharok.STAVE_HALF

        ax, ay = f * math.sin(theta), -math.cos(theta)      # sumbu stave
        nx, ny = f * (-ay), f * ax                          # normal (ke depan)

        pts = []
        for i in range(13):
            u = i / 12.0
            t = (u - 0.5) * 2.0
            parab = 1.0 - t * t
            recurve = math.sin(u * math.pi * 2.0) * 2.5
            along_x = ax * t * L
            along_y = ay * t * L
            bx = gx + along_x + nx * (12.0 * parab + recurve)
            by = gy + along_y + ny * (12.0 * parab + recurve)
            pts.append((bx, by))

        for i in range(len(pts) - 1):
            p0, p1 = pts[i], pts[i + 1]
            _NS_zharok._aaline(surface, P["shadow_deep"],
                               (p0[0] + f, p0[1] + 1), (p1[0] + f, p1[1] + 1), 4)
            _NS_zharok._aaline(surface, P["wood_dark"], p0, p1, 4)
            _NS_zharok._aaline(surface, P["wood_mid"], p0, p1, 3)
            _NS_zharok._aaline(surface, P["wood_light"],
                               (p0[0] - nx, p0[1] - ny), (p1[0] - nx, p1[1] - ny), 2)

        # fitting emas + ujung menyala
        for b_idx in (3, 9):
            bx, by = pts[b_idx]
            _NS_zharok._aacircle(surface, P["metal_darkest"], (bx, by), 3)
            _NS_zharok._aacircle(surface, P["gold_mid"], (bx, by), 2)
            _NS_zharok._aacircle(surface, P["gold_shine"], (bx - nx, by - ny), 1)
        for tip in (pts[0], pts[-1]):
            _NS_zharok._aacircle(surface, P["gold_dark"], tip, 3)
            _NS_zharok._aacircle(surface, P["gold_light"], tip, 2)
            _NS_zharok._aacircle(surface, P["fire_white"], tip, 1)

        # bowstring tegang (garis lurus tip ke tip)
        _NS_zharok._aaline(surface, P["metal_light"], pts[0], pts[-1], 1)
        _NS_zharok._aaline(surface, P["fire_glow"], pts[0], pts[-1], 1)

        # lidah api di sepanjang stave — makin panas saat jendela hit
        span = 3 if heat < 0.5 else 5
        for fl_idx in range(span):
            idx = 2 + fl_idx * 2
            if idx >= len(pts):
                break
            fx, fy = pts[idx]
            wob = math.sin(phase * 4.0 + fl_idx) * 2.0
            r = int(4 + 2 * heat)
            _NS_zharok._aacircle(surface, P["fire_dark"], (fx + wob, fy), r)
            _NS_zharok._aacircle(surface, P["fire_bright"], (fx + wob, fy), max(1, r - 2))
            _NS_zharok._aacircle(surface, P["fire_hot"], (fx + wob, fy), max(1, r - 3))
            _NS_zharok._aacircle(surface, P["fire_white"], (fx + wob, fy), 1)

    @staticmethod
    def _draw_bow_cleave_arms(surface, cx, cy, facing, phase, progress):
        """Lengan sabetan: kedua tangan mengunci grip, badan ikut memutar."""
        NS = _NS_zharok
        f = 1 if facing >= 0 else -1
        theta, lift = NS._bow_arc(progress)
        lunge = NS._cleave_offset(progress)

        gx = cx + (NS.GRIP_RIG[0] + 4.0 * lift + lunge * 0.55) * f
        gy = cy + (NS.GRIP_RIG[1] + 12.0) - 3.0 - 10.0 * lift

        sh_front_x, sh_front_y = cx + 8 * f, cy - 8
        sh_back_x, sh_back_y = cx - 8 * f, cy - 8
        # siku mengikuti arah stave supaya lengan tidak patah tak wajar
        el_x = (sh_front_x + gx) * 0.5 + math.sin(theta) * 5.0 * f
        el_y = (sh_front_y + gy) * 0.5 - 4.0

        NS._draw_bone_arm(surface, sh_back_x, sh_back_y,
                          (sh_back_x + gx) * 0.5 - 4 * f, (sh_back_y + gy) * 0.5)
        NS._draw_bone_arm(surface, (sh_back_x + gx) * 0.5 - 4 * f,
                          (sh_back_y + gy) * 0.5, gx - 4 * f, gy + 2)
        NS._draw_cleaving_bow(surface, gx, gy, facing, theta, phase,
                              heat=1.0 if 0.30 <= progress <= 0.62 else 0.4)
        NS._draw_bone_arm(surface, sh_front_x, sh_front_y, el_x, el_y)
        NS._draw_bone_arm(surface, el_x, el_y, gx, gy)
        NS._draw_skeleton_hand(surface, gx, gy, facing)

        # kilat benturan tepat di frame IMPACT
        impact = 1.0 - min(1.0, abs(progress - NS.ATTACK_IMPACT_FRAME) / 0.10)
        if impact > 0.1:
            tip_x = gx + f * math.sin(theta) * NS.STAVE_HALF
            tip_y = gy - math.cos(theta) * NS.STAVE_HALF
            NS._draw_bow_release_flash(surface, tip_x, tip_y, impact)

    @staticmethod
    def _draw_e_cast_arms(surface, cx, cy, facing, phase):
        f = 1 if facing >= 0 else -1
        for side, sh_off in ((-1, -8), (1, 8)):
            sh_x = cx + sh_off * f
            sh_y = cy - 8
            el_x = cx + (sh_off + side * 4) * f
            el_y = cy - 22
            hand_x = cx + (sh_off + side * 8) * f
            hand_y = cy - 34
            _NS_zharok._draw_bone_arm(surface, sh_x, sh_y, el_x, el_y)
            _NS_zharok._draw_bone_arm(surface, el_x, el_y, hand_x, hand_y)
            _NS_zharok._draw_skeleton_hand(surface, hand_x, hand_y, facing)
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_bright"], (int(hand_x), int(hand_y)), 4)
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_hot"], (int(hand_x), int(hand_y)), 2)

    @staticmethod
    def _draw_r_cast_arms(surface, cx, cy, facing, phase):
        _NS_zharok._draw_e_cast_arms(surface, cx, cy, facing, phase)

    @staticmethod
    def _draw_bow_release_flash(surface, cx, cy, intensity):
        P = _NS_zharok.PALETTE
        alpha = int(255 * intensity)
        _NS_zharok._spark_star(surface, cx, cy, 18 * intensity, P["fire_bright"], alpha, spikes=8, core=P["fire_white"])
        _NS_zharok._aacircle(surface, (*P["fire_hot"], alpha), (int(cx), int(cy)), int(8 * intensity))
        _NS_zharok._aacircle(surface, (*P["fire_white"], alpha), (int(cx), int(cy)), max(1, int(4 * intensity)))

    @staticmethod
    def _draw_bow_smear_arc(surface, cx, cy, facing, progress):
        P = _NS_zharok.PALETTE
        f = 1 if facing >= 0 else -1
        arc_pts = []
        for a_step in range(9):
            u = a_step / 8.0
            ang = (u - 0.5) * 1.4
            r = 30 + math.sin(u * math.pi) * 8
            arc_pts.append((cx + int(math.cos(ang) * r * f), cy + int(math.sin(ang) * r * 0.9)))
        if len(arc_pts) >= 3:
            _NS_zharok._poly(surface, (*P["fire_dark"], 160), arc_pts + [(cx, cy)])
            for i in range(len(arc_pts) - 1):
                _NS_zharok._aaline(surface, (*P["fire_bright"], 220), arc_pts[i], arc_pts[i + 1], 2)
                _NS_zharok._aaline(surface, (*P["fire_hot"], 240), arc_pts[i], arc_pts[i + 1], 1)

    @staticmethod
    def _draw_zharok_masterwork_details(surface, cx, cy, f):
        P = _NS_zharok.PALETTE
        _NS_zharok._aacircle(surface, P["bone_shine"], (int(cx - 3 * f), int(cy - 44)), 1)
        _NS_zharok._aacircle(surface, P["gold_shine"], (int(cx - 1 * f), int(cy + 1)), 1)
        _NS_zharok._aacircle(surface, P["bone_high"], (int(cx - 9 * f), int(cy - 16)), 1)
        _NS_zharok._aacircle(surface, P["bone_rim"], (int(cx + 4 * f), int(cy - 46)), 1)
        _NS_zharok._aacircle(surface, P["metal_shine"], (int(cx - 12 * f), int(cy - 10)), 1)
        _NS_zharok._aacircle(surface, P["metal_high"], (int(cx - 13 * f), int(cy - 8)), 1)
        _NS_zharok._aacircle(surface, P["leather_high"], (int(cx - 8 * f), int(cy + 2)), 1)
        _NS_zharok._aacircle(surface, P["smoke_light"], (int(cx - 10 * f), int(cy - 20)), 1)
        _NS_zharok._aacircle(surface, P["smoke_glow"], (int(cx - 11 * f), int(cy - 22)), 1)

    # ===================================================================
    # BODY RENDERING (Raw -> Composite Buffer)
    # ===================================================================
    @staticmethod
    def _draw_zharok_body_raw(surface, cx, cy, facing, phase, action,
                              attack_progress=0, stealth=False, detail=False):
        f = 1 if facing >= 0 else -1
        walk = action == "walk"
        attack = action == "attack"
        cleave = action in ("melee", "swing", "cleave")
        ap = (max(0.0, min(1.0, attack_progress))
              if (attack or cleave) else 0.0)
        breath = math.sin(phase * 0.8)

        if walk:
            root_y = int(math.sin(phase * 2.4) * 2.5)
            sway = int(math.sin(phase * 1.2) * 2.5)
            lean = 3 * f
            cloth_lag = math.sin(phase * 2.0) * 3.0
            pose = None
        elif cleave:
            # bobot sabetan: badan mundur saat wind-up, menerjang saat swing
            lunge = _NS_zharok._cleave_offset(ap)
            lift = _NS_zharok._bow_lift(ap)
            root_y = int(-2.0 * lift + 1.5 * max(0.0, lunge) * 0.12)
            sway = 0
            lean = int(lunge * 0.42) * f
            cloth_lag = -lunge * 0.55
            pose = None
        elif attack:
            pose = _NS_zharok._attack_pose(ap)
            root_y = int(pose["dip"])
            sway = 1 if (pose["tremble"] and int(phase * 30) % 2) else 0
            lean = int(pose["lean"]) * f
            cloth_lag = -pose["lean"] * 0.8
        elif action == "strafe":
            root_y = int(breath * 1.5)
            sway = int(math.sin(phase * 4.0) * 1.5)
            lean = 2 * f
            cloth_lag = math.sin(phase * 3.0) * 2.0
            pose = None
        else:
            root_y = int(breath * 2.0)
            sway = int(math.sin(phase * 0.5) * 1.5)
            lean = int(math.sin(phase * 0.5 + 1.0) * 1.0)
            cloth_lag = math.sin(phase * 0.6) * 1.5
            pose = None

        off_x = lean + sway
        ox = int(cx) + off_x
        oy = int(cy) + root_y

        leg_action = "attack" if cleave else action
        _NS_zharok._draw_hood_back(surface, ox, oy - 14, facing, phase, cloth_lag=cloth_lag, f=f)
        _NS_zharok._draw_quiver(surface, ox, oy - 14, facing, phase, f=f)
        _NS_zharok._draw_pelvis(surface, ox, oy + 8, phase, f=f)
        _NS_zharok._draw_skeleton_legs(surface, ox, oy + 8, facing, phase, leg_action, f=f)
        _NS_zharok._draw_ribcage(surface, ox, oy - 12, phase, sway=sway, f=f)
        _NS_zharok._draw_hooded_skull(surface, ox, oy - 26, facing, phase, action=action, f=f, stealth=stealth, detail=detail)

        if cleave:
            _NS_zharok._draw_bow_cleave_arms(surface, ox, oy - 12, facing, phase, ap)
        elif attack:
            _NS_zharok._draw_bow_attack_arms(surface, ox, oy - 12, facing, phase, ap)
        elif action == "strafe":
            _NS_zharok._draw_bow_strafe_arms(surface, ox, oy - 12, facing, phase, attack_progress)
        elif action == "e_cast":
            _NS_zharok._draw_e_cast_arms(surface, ox, oy - 12, facing, phase)
        elif action == "r_cast":
            _NS_zharok._draw_r_cast_arms(surface, ox, oy - 12, facing, phase)
        else:
            _NS_zharok._draw_bow_idle_arms(surface, ox, oy - 12, facing, phase)

        if detail:
            _NS_zharok._draw_zharok_masterwork_details(surface, ox, oy, f)

    @staticmethod
    def _draw_zharok_body(surface, cx, cy, facing, phase, action,
                          attack_progress=0, stealth=False, detail=False):
        NS = _NS_zharok
        if NS._body_buf is None:
            NS._body_buf = pygame.Surface((NS.RIG_W, NS.RIG_H), pygame.SRCALPHA)
        buf = NS._body_buf
        buf.fill((0, 0, 0, 0))
        NS._draw_zharok_body_raw(buf, NS.RIG_OX, NS.RIG_OY, facing, phase,
                                 action, attack_progress, stealth=stealth, detail=detail)
        used = buf.get_bounding_rect(min_alpha=1)
        if used.width <= 2 or used.height <= 2:
            return
        used.inflate_ip(4, 4)
        used.clamp_ip(buf.get_rect())
        sub = buf.subsurface(used).copy()
        lx = used.left - NS.RIG_OX
        ly = used.top - NS.RIG_OY

        k = NS.SCALE
        if abs(k - 1.0) >= 0.02:
            tw = max(1, int(round(sub.get_width() * k)))
            th = max(1, int(round(sub.get_height() * k)))
            sub = pygame.transform.smoothscale(sub, (tw, th))
        ox = int(cx) + int(round(lx * k))
        oy = int(cy) + int(round(ly * k))

        edge = sub.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(edge, (ox + ddx, oy + ddy))
        try:
            import lighting as _lighting
            if _lighting is not None:
                _lighting.apply_to_rig(sub, rim_add=(48, 22, 16), shade_mul=168)
        except Exception:
            pass
        surface.blit(sub, (ox, oy))
        # simpan rig terakhir supaya lapisan hidup bisa membuat afterimage
        # tanpa menggambar ulang badan (pose ghost otomatis selalu benar)
        NS._last_rig = sub
        NS._last_rig_off = (ox - int(cx), oy - int(cy))

    @staticmethod
    def _draw_zharok_elite(surface, cx, cy, facing=1, phase=0.0, action="idle",
                           progress=0.0, detail=False, stealth=False):
        _NS_zharok._draw_zharok_body(surface, cx, cy, facing, phase, action,
                                     progress, stealth=stealth, detail=detail)

    @staticmethod
    def _draw_zh_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        _NS_zharok._draw_zharok_body(surface, cx, cy, facing, phase, action,
                                     attack_progress, stealth=(action=="smoke" or action=="stealth"))

    # ===================================================================
    # PROJECTILES & WEAPONS
    # ===================================================================
    class FireArrow:
        """High-definition multi-layer flaming arrow projectile."""
        def __init__(self, sx, sy, tx, ty, speed=10.0):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.trail = []
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)

        def update(self):
            if not self.alive:
                return
            self.age += 1
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.hypot(dx, dy)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((float(self.x), float(self.y)))
            if len(self.trail) > 16:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            P = _NS_zharok.PALETTE
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(30 + (i / max(1, len(self.trail))) * 200)
                r = max(1, int(5 * (i / max(1, len(self.trail)))))
                _NS_zharok._aacircle(surface, (*P["fire_darkest"], alpha), (int(tx), int(ty)), r + 2)
                _NS_zharok._aacircle(surface, (*P["fire_mid"], alpha), (int(tx), int(ty)), r)
                _NS_zharok._aacircle(surface, (*P["fire_hot"], alpha), (int(tx), int(ty)), max(1, r - 1))

            if self.alive:
                px, py = int(self.x), int(self.y)
                dx = math.cos(self.angle)
                dy = math.sin(self.angle)
                perp_x = -dy
                perp_y = dx

                shaft_len = 16
                sx = px - int(dx * shaft_len)
                sy = py - int(dy * shaft_len)
                _NS_zharok._aaline(surface, P["shadow_deep"], (sx + 1, sy + 1), (px + 1, py + 1), 3)
                _NS_zharok._aaline(surface, P["wood_dark"], (sx, sy), (px, py), 2)
                _NS_zharok._aaline(surface, P["wood_light"], (sx, sy), (px, py), 1)

                for side in (-1, 1):
                    f_tip_x = sx - int(dx * 4) + int(perp_x * side * 4)
                    f_tip_y = sy - int(dy * 4) + int(perp_y * side * 4)
                    _NS_zharok._poly(surface, P["hood_dark"], [(sx, sy), (f_tip_x, f_tip_y), (sx - int(dx * 2), sy - int(dy * 2))])
                    _NS_zharok._poly(surface, P["hood_light"], [(sx, sy), (f_tip_x, f_tip_y), (sx, sy)])

                tip_x = px + int(dx * 6)
                tip_y = py + int(dy * 6)
                head_pts = [
                    (tip_x, tip_y),
                    (px + int(perp_x * 4), py + int(perp_y * 4)),
                    (px - int(dx * 2), py - int(dy * 2)),
                    (px - int(perp_x * 4), py - int(perp_y * 4)),
                ]
                _NS_zharok._poly(surface, P["shadow_deep"], [(p[0] + 1, p[1] + 1) for p in head_pts])
                _NS_zharok._poly(surface, P["metal_darkest"], head_pts)
                _NS_zharok._poly(surface, P["metal_mid"], head_pts)
                _NS_zharok._poly(surface, P["metal_shine"], [
                    (tip_x, tip_y),
                    (px + int(perp_x * 2), py + int(perp_y * 2)),
                    (px, py),
                ])

                for fl_i in range(5):
                    t = 0.2 + fl_i * 0.18
                    fl_x = int(sx + (px - sx) * t + perp_x * math.sin(phase * 4.0 + fl_i) * 2.5)
                    fl_y = int(sy + (py - sy) * t + perp_y * math.sin(phase * 4.0 + fl_i) * 2.5)
                    _NS_zharok._aacircle(surface, P["fire_dark"], (fl_x, fl_y), 4)
                    _NS_zharok._aacircle(surface, P["fire_bright"], (fl_x, fl_y), 2)
                    _NS_zharok._aacircle(surface, P["fire_hot"], (fl_x, fl_y), 1)

                _NS_zharok._spark_star(surface, tip_x, tip_y, 8, P["fire_hot"], 240, spikes=4, rot=phase * 2.0, core=P["fire_white"])

    class BurningSkull:
        """Orbiting burning skull minion."""
        def __init__(self, x, y, orbit_center_x, orbit_center_y, orbit_radius=55,
                     orbit_speed=0.05, orbit_offset=0, life=200):
            self.x = float(x)
            self.y = float(y)
            self.ocx = orbit_center_x
            self.ocy = orbit_center_y
            self.orbit_radius = orbit_radius
            self.orbit_speed = orbit_speed
            self.orbit_offset = orbit_offset
            self.life = life
            self.age = 0
            self.alive = True

        def update(self, boss_x=None, boss_y=None):
            self.age += 1
            if self.age >= self.life:
                self.alive = False
            if boss_x is not None:
                self.ocx = boss_x
                self.ocy = boss_y
            angle = self.age * self.orbit_speed + self.orbit_offset
            self.x = self.ocx + math.cos(angle) * self.orbit_radius
            self.y = self.ocy + math.sin(angle) * self.orbit_radius * 0.5 - 20

        def draw(self, surface, phase):
            t = self.age / self.life
            alpha = int(255 * (t / 0.15)) if t < 0.15 else (255 if t < 0.85 else int(255 * (1.0 - (t - 0.85) / 0.15)))
            px, py = int(self.x), int(self.y)

            for i in range(4):
                bx = px - int(math.cos(self.orbit_offset + self.age * self.orbit_speed) * (i * 5))
                by = py - int(math.sin(self.orbit_offset + self.age * self.orbit_speed) * (i * 3))
                _NS_zharok._draw_ember(surface, bx, by, max(1, 3 - i), alpha // (i + 1))

            _NS_zharok._draw_mini_skull(surface, px, py, phase, alpha)
            _NS_zharok._draw_flame_tuft(surface, px, py - 6, 4, phase, alpha)

    @staticmethod
    def _draw_mini_skull(surface, cx, cy, phase, alpha=255):
        P = _NS_zharok.PALETTE
        alpha = _NS_zharok._alpha(alpha)
        _NS_zharok._aacircle(surface, (*P["shadow_deep"], alpha), (cx + 1, cy + 1), 7)
        _NS_zharok._aacircle(surface, (*P["bone_darkest"], alpha), (cx, cy), 7)
        _NS_zharok._aacircle(surface, (*P["bone_dark"], alpha), (cx - 1, cy - 1), 6)
        _NS_zharok._aacircle(surface, (*P["bone_mid"], alpha), (cx - 1, cy - 2), 4)
        _NS_zharok._aacircle(surface, (*P["bone_light"], alpha), (cx - 2, cy - 3), 2)

        eye_pulse = math.sin(phase * 3.0) * 0.3 + 0.7
        for side in (-1, 1):
            ex = cx + side * 3
            ey = cy - 1
            _NS_zharok._aacircle(surface, (*P["shadow_deep"], alpha), (ex, ey), 2)
            _NS_zharok._aacircle(surface, (*P["fire_bright"], int(alpha * eye_pulse)), (ex, ey), 2)
            _NS_zharok._aacircle(surface, (*P["fire_hot"], int(alpha * eye_pulse)), (ex, ey), 1)

        _NS_zharok._rect(surface, (*P["shadow_deep"], alpha), (cx - 3, cy + 4, 6, 2))
        for tooth in (-2, 0, 2):
            _NS_zharok._aacircle(surface, (*P["bone_high"], alpha), (cx + tooth, cy + 5), 1)

    @staticmethod
    def _draw_ember(surface, cx, cy, size=2, alpha=255):
        P = _NS_zharok.PALETTE
        alpha = _NS_zharok._alpha(alpha)
        _NS_zharok._aacircle(surface, (*P["fire_dark"], alpha), (cx, cy), size + 1)
        _NS_zharok._aacircle(surface, (*P["fire_bright"], alpha), (cx, cy), size)
        _NS_zharok._aacircle(surface, (*P["fire_hot"], alpha), (cx, cy), max(1, size - 1))
        _NS_zharok._aacircle(surface, (*P["fire_glow"], min(255, alpha)), (cx, cy), 1)

    @staticmethod
    def _draw_flame(surface, cx, cy, size, phase, alpha=255):
        P = _NS_zharok.PALETTE
        alpha = _NS_zharok._alpha(alpha)
        _NS_zharok._aacircle(surface, (*P["fire_dark"], alpha), (cx, cy), size + 2)
        _NS_zharok._aacircle(surface, (*P["fire_bright"], alpha), (cx, cy), size)
        _NS_zharok._aacircle(surface, (*P["fire_hot"], alpha), (cx, cy), max(1, size - 1))
        _NS_zharok._aacircle(surface, (*P["fire_glow"], alpha), (cx, cy - 2), max(1, size - 2))

    @staticmethod
    def _draw_flame_tuft(surface, cx, cy, size, phase, alpha=255):
        P = _NS_zharok.PALETTE
        alpha = _NS_zharok._alpha(alpha)
        _NS_zharok._aacircle(surface, (*P["fire_darkest"], alpha), (cx, cy), size + 1)
        _NS_zharok._aacircle(surface, (*P["fire_bright"], alpha), (cx, cy), size)
        _NS_zharok._aacircle(surface, (*P["fire_hot"], alpha), (cx, cy - 1), max(1, size - 1))
        _NS_zharok._aacircle(surface, (*P["fire_white"], alpha), (cx, cy - 2), 1)

    # ── Projectile & Skill Spawners ──────────────────────────────────
    @staticmethod
    def _detect_moving(boss):
        x = getattr(boss, "x", 0)
        y = getattr(boss, "y", 0)
        lx = getattr(boss, "_zh_last_x", x)
        ly = getattr(boss, "_zh_last_y", y)
        boss._zh_last_x = x
        boss._zh_last_y = y
        dx = abs(x - lx)
        dy = abs(y - ly)
        boss._zh_speed = dx + dy
        return (dx + dy) > 0.3

    @staticmethod
    def _update_attack_anim(boss):
        """API LAMA — dipertahankan untuk kompatibilitas mundur.

        Sekarang mendelegasikan ke controller animasi v3 supaya tidak ada
        dua sumber kebenaran yang saling menimpa `_zh_attack_progress`.
        """
        return _NS_zharok._update_zharok_anim(
            boss, moving=(float(getattr(boss, "_zh_speed", 0.0)) > 0.3))

    @staticmethod
    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_zh_arrows"):
            boss._zh_arrows = []
        if not hasattr(boss, "_zh_skulls"):
            boss._zh_skulls = []

        active_arrows = []
        for arrow in boss._zh_arrows:
            arrow.update()
            arrow.draw(surface, phase)
            if arrow.alive:
                active_arrows.append(arrow)
        boss._zh_arrows = active_arrows

        bx = getattr(boss, "x", 0)
        by = getattr(boss, "y", 0)
        active_skulls = []
        for skull in boss._zh_skulls:
            skull.update(bx, by)
            skull.draw(surface, phase)
            if skull.alive:
                active_skulls.append(skull)
        boss._zh_skulls = active_skulls

    @staticmethod
    def _spawn_fire_arrow(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_zh_arrows"):
            boss._zh_arrows = []
        boss._zh_arrows.append(_NS_zharok.FireArrow(sx, sy, tx, ty))

    @staticmethod
    def _spawn_burning_skulls(boss, x, y, count=5):
        if not hasattr(boss, "_zh_skulls"):
            boss._zh_skulls = []
        for i in range(count):
            offset = i * (math.tau / count)
            boss._zh_skulls.append(_NS_zharok.BurningSkull(
                x, y, x, y, orbit_radius=60, orbit_speed=0.045, orbit_offset=offset, life=220))

    # ===================================================================
    # SKILL FX & POSE MODES
    # ===================================================================
    @staticmethod
    def _draw_shadow(surface, x, y, lift=0):
        P = _NS_zharok.PALETTE
        w = max(10, int(72 * (1.0 - lift * 0.03)))
        h = max(4, int(18 * (1.0 - lift * 0.03)))
        alpha = max(0, min(255, int(180 * (1.0 - lift * 0.04))))
        _NS_zharok._ellipse(surface, (0, 0, 0, alpha), (x - w // 2, y - h // 2, w, h))
        _NS_zharok._ellipse(surface, (*P["fire_dark"], alpha // 2), (x - w // 3, y - h // 3, w * 2 // 3, h * 2 // 3))

    @staticmethod
    def _draw_fire_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        P = _NS_zharok.PALETTE
        strength = 1.5 if intense else 1.0
        for i in range(6):
            ang = phase * 1.5 + i * math.tau / 6.0
            r = 22 + int(math.sin(phase * 2.0 + i) * 6)
            sx = cx + int(math.cos(ang) * r)
            sy = cy + int(math.sin(ang) * 8) - int((phase * 15 + i * 8) % 24)
            _NS_zharok._draw_ember(surface, sx, sy, 2, int(210 * strength))

    @staticmethod
    def _draw_fire_aura(surface, x, y, phase, active_skill):
        P = _NS_zharok.PALETTE
        strength = 1.6 if active_skill else 1.0
        pulse = math.sin(phase * 1.2) * 0.2 + 0.8
        _NS_zharok._glow(surface, x, y, 70 * strength * pulse, P["fire_dark"], core=P["fire_bright"], alpha=int(70 * pulse))

    @staticmethod
    def _draw_ground_runes(surface, x, y, phase, active_skill):
        if active_skill in ("e", "r"):
            return
        P = _NS_zharok.PALETTE
        pulse = math.sin(phase * 1.5) * 0.25 + 0.75
        _NS_zharok._rune_ring(surface, x, y, 42, P["fire_dark"], P["fire_bright"], int(140 * pulse), phase=phase * 0.4)
        if active_skill:
            _NS_zharok._ground_ring(surface, x, y, 48, P["fire_mid"], P["fire_white"], int(180 * pulse), thickness=2)

    # ── Pose Modes ───────────────────────────────────────────────────
    @staticmethod
    def _draw_zh_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 2 * _NS_zharok.SCALE)
        _NS_zharok._draw_shadow(surface, x, y + _NS_zharok.GROUND_DY)
        _NS_zharok._draw_fire_wisps(surface, x, y + 20, boss.pulse)
        _NS_zharok._draw_zharok_body(surface, x, y + bob, getattr(boss, "direction", 1), boss.pulse, "idle")

    @staticmethod
    def _draw_zh_walk(surface, boss, x, y):
        phase = boss.pulse * 2.3
        k = _NS_zharok.SCALE
        bob = int(abs(math.sin(phase * 1.2)) * 3 * k)
        sway = int(math.sin(phase * 0.6) * 2 * k)
        _NS_zharok._draw_shadow(surface, x + sway, y + _NS_zharok.GROUND_DY)
        _NS_zharok._draw_fire_wisps(surface, x + sway, y + 20, phase, trail=True, facing=getattr(boss, "direction", 1))
        _NS_zharok._draw_zharok_body(surface, x + sway, y - bob, getattr(boss, "direction", 1), phase, "walk")

    @staticmethod
    def _draw_zh_attack(surface, boss, x, y):
        progress = getattr(boss, "_zh_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        facing = getattr(boss, "direction", 1)
        phase = getattr(boss, "pulse", 0.0)
        pose = _NS_zharok._attack_pose(progress)
        lunge = int(pose["lunge"] * _NS_zharok.SCALE) * facing

        # Proyektil canvas HANYA dipakai kalau lapisan hidup tidak
        # mengambil alih (di sana anak panahnya jauh lebih kaya).
        if not getattr(boss, "_zh_suppress_canvas_fx", False):
            if 0.45 < progress < 0.55 and not getattr(boss, "_zh_atk_spawned", False):
                tx, ty = _NS_zharok._target_position(boss, x, y)
                sx = x + 24 * facing
                sy = y - 4
                _NS_zharok._spawn_fire_arrow(boss, sx, sy, tx, ty)
                boss._zh_atk_spawned = True
            if progress < 0.1 or progress > 0.9:
                boss._zh_atk_spawned = False

        _NS_zharok._draw_shadow(surface, x + lunge, y + _NS_zharok.GROUND_DY)
        _NS_zharok._draw_fire_wisps(surface, x + lunge, y + 20, phase, intense=True)
        _NS_zharok._draw_zharok_body(surface, x + lunge, y, facing, phase, "attack", progress)

    @staticmethod
    def _draw_zh_melee(surface, boss, x, y):
        """Sabetan stave busur (Ember Cleave) — pose berbasis ARK.

        Senjata TIDAK dipindahkan langsung dari posisi awal ke akhir:
        seluruh sudutnya berasal dari `BOW_ARC` yang bersambung, jadi
        gerakannya benar-benar melengkung dan punya momentum.
        """
        progress = max(0.0, min(1.0, getattr(boss, "_zh_attack_progress", 0.0)))
        facing = getattr(boss, "direction", 1)
        phase = getattr(boss, "pulse", 0.0)
        lunge = int(_NS_zharok._cleave_offset(progress) * _NS_zharok.SCALE) * facing

        _NS_zharok._draw_shadow(surface, x + lunge, y + _NS_zharok.GROUND_DY)
        _NS_zharok._draw_fire_wisps(surface, x + lunge, y + 20, phase, intense=True)
        _NS_zharok._draw_zharok_body(surface, x + lunge, y, facing, phase,
                                     "melee", progress)

    @staticmethod
    def _draw_zh_strafe(surface, boss, x, y, timer):
        phase = getattr(boss, "pulse", 0.0)
        dur = _NS_zharok.SKILL_DUR["q"]
        prog = max(0.0, min(1.0, 1.0 - timer / float(dur)))
        _NS_zharok._draw_shadow(surface, x, y + _NS_zharok.GROUND_DY)
        _NS_zharok._draw_fire_wisps(surface, x, y + 20, phase, intense=True)
        _NS_zharok._draw_zharok_body(surface, x, y, getattr(boss, "direction", 1), phase, "strafe", attack_progress=prog)

    @staticmethod
    def _draw_zh_ecast(surface, boss, x, y, timer):
        phase = getattr(boss, "pulse", 0.0)
        dur = _NS_zharok.SKILL_DUR["e"]
        prog = max(0.0, min(1.0, 1.0 - timer / float(dur)))
        _NS_zharok._draw_shadow(surface, x, y + _NS_zharok.GROUND_DY)
        _NS_zharok._draw_fire_wisps(surface, x, y + 20, phase, intense=True)
        _NS_zharok._draw_zharok_body(surface, x, y, getattr(boss, "direction", 1), phase, "e_cast", attack_progress=prog)

    @staticmethod
    def _draw_zh_rcast(surface, boss, x, y, timer):
        phase = getattr(boss, "pulse", 0.0)
        dur = _NS_zharok.SKILL_DUR["r"]
        prog = max(0.0, min(1.0, 1.0 - timer / float(dur)))
        _NS_zharok._draw_shadow(surface, x, y + _NS_zharok.GROUND_DY)
        _NS_zharok._draw_fire_wisps(surface, x, y + 20, phase, intense=True)
        _NS_zharok._draw_zharok_body(surface, x, y, getattr(boss, "direction", 1), phase, "r_cast", attack_progress=prog)

    # ── Q - Strafe (Multi-Arrow Barrage) ─────────────────────────────
    @staticmethod
    def _draw_strafe_ground(surface, boss, x, y, timer, phase):
        P = _NS_zharok.PALETTE
        fs = _NS_zharok._fx_scale(boss)
        dur = _NS_zharok.SKILL_DUR["q"]
        age = dur - timer
        prog = max(0.0, min(1.0, age / float(dur)))
        ground_y = y + _NS_zharok.GROUND_DY

        if age < 12:
            sw_t = age / 12.0
            _NS_zharok._draw_shockwave(surface, x, ground_y, int((20 + sw_t * 50) * fs), P["fire_bright"], int(240 * (1.0 - sw_t)))

        r_world = _NS_zharok.SKILL_RADIUS["q"]
        r_px = _NS_zharok._ring_r(boss, r_world, surface)
        ring_alpha = int((160 - prog * 40) * (0.8 + 0.2 * math.sin(phase * 4.0 + prog * 6.0)))
        _NS_zharok._ground_ring(surface, x, ground_y, r_px, P["fire_mid"], P["fire_white"], ring_alpha, thickness=2)

        tx, ty = _NS_zharok._target_position(boss, x, y)
        ang = math.atan2(ty - y, tx - x)
        dist = math.hypot(tx - x, ty - y)
        steps = max(3, int(dist / 35))
        for k in range(1, steps):
            u = k / float(steps)
            cx_line = x + math.cos(ang) * (dist * u)
            cy_line = y + math.sin(ang) * (dist * u)
            chev_alpha = int(220 * (1.0 - abs(u - (prog * 1.5 % 1.0))))
            _NS_zharok._chevron(surface, cx_line, cy_line, ang, 8 * fs, P["fire_bright"], chev_alpha)

        reticle_r = int((26 + math.sin(prog * 12.0) * 6) * fs)
        _NS_zharok._ground_ring(surface, tx, ty + 10, reticle_r, P["fire_hot"], P["fire_white"], int(220 * (1.0 - prog * 0.4)), thickness=2)
        _NS_zharok._spark_star(surface, tx, ty + 10, int(18 * fs), P["fire_bright"], int(240 * (1.0 - prog * 0.4)), spikes=4, rot=phase * 2.0 + prog * 4.0)

    @staticmethod
    def _draw_strafe_foreground(surface, boss, x, y, timer, phase):
        P = _NS_zharok.PALETTE
        fs = _NS_zharok._fx_scale(boss)
        dur = _NS_zharok.SKILL_DUR["q"]
        age = dur - timer
        prog = max(0.0, min(1.0, age / float(dur)))
        f = getattr(boss, "direction", 1)

        if 0.15 < prog < 0.85:
            burst_x = x + int(28 * f)
            burst_y = y - 4
            _NS_zharok._spark_star(surface, burst_x, burst_y, (18 + math.sin(prog * 20.0) * 8) * fs, P["fire_hot"], 240, spikes=6, core=P["fire_white"])
            _NS_zharok._aacircle(surface, (*P["fire_white"], 220), (burst_x, burst_y), int(5 * fs))

    # ── W - Skeleton Walk (Stealth / Smoke Cloak) ────────────────────
    @staticmethod
    def _draw_zh_smoke(surface, boss, x, y, timer, phase):
        P = _NS_zharok.PALETTE
        fs = _NS_zharok._fx_scale(boss)
        dur = _NS_zharok.SKILL_DUR["w"]
        age = dur - timer
        prog = max(0.0, min(1.0, age / float(dur)))
        ground_y = y + _NS_zharok.GROUND_DY

        # Stage 1: Burst shockwave and ash cloud
        if age < 14:
            sw_t = age / 14.0
            sw_r = int((20 + sw_t * 60) * fs)
            _NS_zharok._draw_shockwave(surface, x, ground_y, sw_r, P["fire_bright"], int(240 * (1.0 - sw_t)))
            _NS_zharok._spark_star(surface, x, y, 28 * fs * (1.0 - sw_t), P["fire_hot"], int(255 * (1.0 - sw_t)), spikes=8, core=P["fire_white"])
        # Stage 3: Emergence shockwave & condensation sparks
        elif prog > 0.7:
            em_t = (prog - 0.7) / 0.3
            em_r = int((15 + em_t * 45) * fs)
            _NS_zharok._draw_shockwave(surface, x, ground_y, em_r, P["smoke_light"], int(220 * (1.0 - em_t)))
            _NS_zharok._spark_star(surface, x, y, 20 * fs * em_t, P["fire_bright"], int(230 * em_t), spikes=6, core=P["fire_white"])

        smoke_alpha = int(220 * (1.0 - abs(prog - 0.5) * 1.2))
        smoke_alpha = max(60, min(255, smoke_alpha))
        smoke_r = int((32 + math.sin(phase * 3.0 + prog * 6.0) * 8 + prog * 12) * fs)
        _NS_zharok._rune_ring(surface, x, ground_y, smoke_r, P["smoke_mid"], P["fire_mid"], smoke_alpha, phase=phase * 2.0 + prog * 3.0)
        _NS_zharok._ground_scorch(surface, x, ground_y, smoke_r * 0.8, alpha=int(smoke_alpha * 0.8), dark=P["smoke_dark"], mid=P["fire_darkest"])

        num_wisps = 8 if prog <= 0.7 else max(3, int(8 * (1.0 - (prog - 0.7) / 0.3)))
        for i in range(num_wisps):
            ang = phase * 3.0 + prog * 4.0 + i * math.tau / float(num_wisps)
            r_wisp = int((20 + math.sin(phase * 2.0 + i + prog * 5.0) * 12) * fs)
            wx = x + int(math.cos(ang) * r_wisp)
            wy = y - 10 + int(math.sin(ang) * (r_wisp * 0.4))
            _NS_zharok._aacircle(surface, (*P["smoke_light"], smoke_alpha), (wx, wy), int(5 * fs))
            _NS_zharok._aacircle(surface, (*P["fire_bright"], min(255, smoke_alpha + 40)), (wx, wy), int(2 * fs))

        _NS_zharok._draw_zharok_body(surface, x, y, getattr(boss, "direction", 1), phase + prog * 2.0, "idle", stealth=True)

    # ── E - Death Pact (Hellfire Sacrifice / Soul Eruption) ───────────
    @staticmethod
    def _draw_death_pact_ground(surface, boss, x, y, timer, phase):
        P = _NS_zharok.PALETTE
        fs = _NS_zharok._fx_scale(boss)
        dur = _NS_zharok.SKILL_DUR["e"]
        age = dur - timer
        prog = max(0.0, min(1.0, age / float(dur)))
        r_world = _NS_zharok.SKILL_RADIUS["e"]
        r_px = _NS_zharok._ring_r(boss, r_world, surface)
        ground_y = y + _NS_zharok.GROUND_DY

        _NS_zharok._ground_scorch(surface, x, ground_y, r_px, alpha=int(180 * (0.6 + 0.4 * prog)))
        _NS_zharok._zone_fill(surface, x, ground_y, r_px, P["fire_dark"], P["fire_mid"], alpha=int(140 * (0.5 + 0.5 * math.sin(prog * math.pi))))

        _NS_zharok._ground_ring(surface, x, ground_y, r_px, P["fire_bright"], P["fire_white"], alpha=220, thickness=3)
        _NS_zharok._rune_ring(surface, x, ground_y, int(r_px * 0.75), P["fire_dark"], P["fire_hot"], alpha=180, phase=-phase * 1.5 + prog * 3.0)

        conv_t = (prog * 3.0) % 1.0
        conv_r = _NS_zharok._quantize(int(r_px * (1.0 - conv_t)), 12)
        if conv_r > 8:
            _NS_zharok._ground_ring(surface, x, ground_y, conv_r, P["fire_hot"], P["fire_white"], int(190 * (1.0 - conv_t)), thickness=2)

        for k in range(4):
            ang = k * math.pi * 0.5 + prog * 1.5
            chev_x = x + math.cos(ang) * (r_px - 8)
            chev_y = ground_y + math.sin(ang) * (r_px - 8)
            _NS_zharok._chevron(surface, chev_x, chev_y, ang + math.pi, 10 * fs, P["fire_hot"], 220)

        for i in range(5):
            ang1 = phase * 0.2 + prog * 2.0 + i * math.tau / 5.0
            ang2 = ang1 + math.pi * 0.8
            p1_x = x + int(math.cos(ang1) * (r_px * 0.85))
            p1_y = ground_y + int(math.sin(ang1) * (r_px * 0.85))
            p2_x = x + int(math.cos(ang2) * (r_px * 0.85))
            p2_y = ground_y + int(math.sin(ang2) * (r_px * 0.85))
            _NS_zharok._aaline(surface, (*P["fire_bright"], 200), (p1_x, p1_y), (p2_x, p2_y), 2)
            _NS_zharok._aaline(surface, (*P["fire_white"], 240), (p1_x, p1_y), (p2_x, p2_y), 1)

    @staticmethod
    def _draw_death_pact_foreground(surface, boss, x, y, timer, phase):
        P = _NS_zharok.PALETTE
        fs = _NS_zharok._fx_scale(boss)
        dur = _NS_zharok.SKILL_DUR["e"]
        age = dur - timer
        prog = max(0.0, min(1.0, age / float(dur)))
        ground_y = y + _NS_zharok.GROUND_DY

        if age < 16:
            sw_t = age / 16.0
            _NS_zharok._draw_shockwave(surface, x, ground_y, int((30 + sw_t * 90) * fs), P["fire_bright"], int(240 * (1.0 - sw_t)))
            _NS_zharok._spark_star(surface, x, y, 36 * fs * (1.0 - sw_t), P["fire_bright"], int(255 * (1.0 - sw_t)), spikes=8, core=P["fire_white"])

        skull_alpha = 255 if 0.2 <= prog <= 0.85 else int(255 * (prog / 0.2 if prog < 0.2 else (1.0 - prog) / 0.15))
        skull_y = y - int((70 + math.sin(phase * 2.0 + prog * 4.0) * 6) * fs)

        _NS_zharok._aacircle(surface, (*P["shadow_deep"], skull_alpha), (x + 2, skull_y + 2), int(22 * fs))
        _NS_zharok._aacircle(surface, (*P["bone_darkest"], skull_alpha), (x, skull_y), int(22 * fs))
        _NS_zharok._aacircle(surface, (*P["bone_dark"], skull_alpha), (x - 2, skull_y - 2), int(19 * fs))
        _NS_zharok._aacircle(surface, (*P["bone_mid"], skull_alpha), (x - 3, skull_y - 4), int(15 * fs))
        _NS_zharok._aacircle(surface, (*P["bone_light"], skull_alpha), (x - 4, skull_y - 6), int(10 * fs))

        eye_pulse = math.sin(phase * 4.0 + prog * 8.0) * 0.3 + 0.7
        for side in (-1, 1):
            ex = x + int(side * 8 * fs)
            ey = skull_y - int(3 * fs)
            _NS_zharok._aacircle(surface, (*P["shadow_deep"], skull_alpha), (ex, ey), int(7 * fs))
            _NS_zharok._aacircle(surface, (*P["fire_bright"], int(skull_alpha * eye_pulse)), (ex, ey), int(5 * fs))
            _NS_zharok._aacircle(surface, (*P["fire_hot"], int(skull_alpha * eye_pulse)), (ex, ey), int(3 * fs))
            _NS_zharok._aacircle(surface, (*P["fire_white"], int(skull_alpha * eye_pulse)), (ex, ey), int(1 * fs))

        _NS_zharok._rect(surface, (*P["shadow_deep"], skull_alpha), (x - int(12 * fs), skull_y + int(8 * fs), int(24 * fs), int(8 * fs)))
        for tooth in (-8, -4, 0, 4, 8):
            _NS_zharok._rect(surface, (*P["bone_high"], skull_alpha), (x + int(tooth * fs), skull_y + int(8 * fs), int(3 * fs), int(6 * fs)))

        _NS_zharok._draw_flame(surface, x, skull_y - int(20 * fs), int(10 * fs), phase + prog * 3.0, skull_alpha)
        _NS_zharok._draw_flame(surface, x - int(8 * fs), skull_y - int(16 * fs), int(6 * fs), phase + prog * 3.0 + 1, skull_alpha)
        _NS_zharok._draw_flame(surface, x + int(8 * fs), skull_y - int(16 * fs), int(6 * fs), phase + prog * 3.0 + 2, skull_alpha)

        for i in range(4):
            t_cond = (phase * 1.5 + prog * 2.0 + i * 0.25) % 1.0
            cx_cond = x + int(math.sin(t_cond * math.pi) * (12 * fs) * ((i % 2) * 2 - 1))
            cy_cond = skull_y + int((y - skull_y) * t_cond)
            _NS_zharok._aacircle(surface, (*P["fire_bright"], int(220 * skull_alpha / 255)), (cx_cond, cy_cond), int(4 * fs))
            _NS_zharok._aacircle(surface, (*P["fire_hot"], int(240 * skull_alpha / 255)), (cx_cond, cy_cond), int(2 * fs))

    # ── R - Burning Army (Inferno Summoning) ──────────────────────────
    @staticmethod
    def _draw_burning_army_ground(surface, boss, x, y, timer, phase):
        P = _NS_zharok.PALETTE
        fs = _NS_zharok._fx_scale(boss)
        dur = _NS_zharok.SKILL_DUR["r"]
        age = dur - timer
        prog = max(0.0, min(1.0, age / float(dur)))
        r_world = _NS_zharok.SKILL_RADIUS["r"]
        r_px = _NS_zharok._ring_r(boss, r_world, surface)
        ground_y = y + _NS_zharok.GROUND_DY

        _NS_zharok._ground_scorch(surface, x, ground_y, r_px, alpha=int(200 * (0.7 + 0.3 * prog)))
        _NS_zharok._zone_fill(surface, x, ground_y, r_px, P["fire_dark"], P["fire_bright"], alpha=int(150 * (0.6 + 0.4 * math.sin(prog * math.pi))))

        _NS_zharok._ground_ring(surface, x, ground_y, r_px, P["fire_bright"], P["fire_white"], alpha=240, thickness=4)
        _NS_zharok._rune_ring(surface, x, ground_y, int(r_px * 0.65), P["fire_dark"], P["fire_hot"], alpha=200, phase=phase * 1.2 + prog * 2.0)
        _NS_zharok._ground_ring(surface, x, ground_y, int(r_px * 0.35), P["fire_mid"], P["fire_white"], alpha=180, thickness=2)

        crack_len_ratio = min(1.0, prog / 0.3) if prog < 0.3 else 1.0
        for k in range(6):
            ang = phase * 0.1 + prog * 0.5 + k * math.tau / 6.0
            cx1 = x + int(math.cos(ang) * (r_px * 0.95 * crack_len_ratio))
            cy1 = ground_y + int(math.sin(ang) * (r_px * 0.95 * crack_len_ratio))
            _NS_zharok._jagged_crack(surface, x, ground_y, cx1, cy1, P["fire_dark"], 220, width=3, seed=k * 13)
            _NS_zharok._jagged_crack(surface, x, ground_y, cx1, cy1, P["fire_bright"], 240, width=1, seed=k * 13)

        if age < 24:
            pil_t = age / 24.0
            pil_h = min(240, int(180 * fs))
            pil_w = int(28 * fs * (1.0 - pil_t * 0.5))
            pil_alpha = int(240 * (1.0 - pil_t))
            for pw, pcol in ((pil_w + 8, P["fire_darkest"]), (pil_w + 4, P["fire_dark"]), (pil_w, P["fire_bright"]), (pil_w // 2, P["fire_white"])):
                _NS_zharok._rect(surface, (*pcol, pil_alpha), (x - pw // 2, ground_y - pil_h, pw, pil_h))

    # ── Main Entry Points ────────────────────────────────────────────
    @staticmethod
    def _handle_skill_projectiles(boss, x, y, active_skill, timer):
        tx, ty = _NS_zharok._target_position(boss, x, y)
        if active_skill == "q":
            dur = _NS_zharok.SKILL_DUR["q"]
            prog = max(0.0, min(1.0, 1.0 - timer / float(dur)))
            if 0.15 < prog < 0.85:
                frames_since = int(getattr(boss, "_zh_strafe_frame_count", 0))
                boss._zh_strafe_frame_count = frames_since + 1
                if frames_since % 7 == 0:
                    sx = x + 24 * getattr(boss, "direction", 1)
                    sy = y - 4
                    spread = ((frames_since // 7) - 2) * 14
                    _NS_zharok._spawn_fire_arrow(boss, sx, sy, tx + spread, ty)
            else:
                boss._zh_strafe_frame_count = 0
        elif active_skill == "r":
            dur = _NS_zharok.SKILL_DUR["r"]
            prog = max(0.0, min(1.0, 1.0 - timer / float(dur)))
            if 0.25 < prog < 0.35 and not getattr(boss, "_zh_r_spawned", False):
                _NS_zharok._spawn_burning_skulls(boss, x, y, count=5)
                boss._zh_r_spawned = True
            if prog > 0.6:
                boss._zh_r_spawned = False

    @staticmethod
    def draw_zharok(surface, boss, x, y):
        """Entry point Boss.draw() sekaligus jalur hero-lane.

        Urutan render:
          GROUND -> GROUND FX -> SHADOW -> BACK PARTICLES -> BODY/ARMOR/
          HEAD/WEAPON -> ATTACK TRAIL -> PROJECTILE -> FRONT PARTICLES ->
          SKILL FX -> IMPACT FX -> DEBUG.

        Trail / partikel / proyektil / impact / hit-stop / shake hidup di
        ``heroes/zharok_fx`` (ruang layar 1:1); canvas hanya fallback bila
        modul itu tidak tersedia.
        """
        NS = _NS_zharok
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        portrait = bool(getattr(boss, "_portrait_hd", False))
        hero_lane = hasattr(boss, "_render_scale")

        # ── CONTROLLER ANIMASI ─────────────────────────────────────
        moving = NS._detect_moving(boss)
        NS._update_zharok_anim(boss, moving)
        action, phase, ap = NS._resolve_pose(boss, moving)
        boss._zh_pose_action = action
        boss._zh_phase = phase

        # ── LAPISAN HIDUP (ground) ─────────────────────────────────
        live, owned = NS._live_fx(boss, surface, x, y, not hero_lane,
                                  portrait)
        boss._zh_suppress_canvas_fx = owned

        # ── GROUND FX / AURA ───────────────────────────────────────
        if not portrait:
            NS._draw_fire_aura(surface, x, y, pulse, active_skill)
            NS._draw_ground_runes(surface, x, y + NS.GROUND_DY, pulse,
                                  active_skill)
            if not owned:
                if active_skill == "q":
                    NS._draw_strafe_ground(surface, boss, x, y, skill_timer,
                                           pulse)
                elif active_skill == "e":
                    NS._draw_death_pact_ground(surface, boss, x, y,
                                               skill_timer, pulse)
                elif active_skill == "r":
                    NS._draw_burning_army_ground(surface, boss, x, y,
                                                 skill_timer, pulse)

        # ── BADAN (shadow -> rig -> senjata, satu komposit) ────────
        if action == "smoke":
            NS._draw_zh_smoke(surface, boss, x, y, skill_timer, pulse)
        elif action == "melee":
            NS._draw_zh_melee(surface, boss, x, y)
        elif action == "attack":
            NS._draw_zh_attack(surface, boss, x, y)
        elif action == "strafe":
            NS._draw_zh_strafe(surface, boss, x, y, skill_timer)
        elif action == "e_cast":
            NS._draw_zh_ecast(surface, boss, x, y, skill_timer)
        elif action == "r_cast":
            NS._draw_zh_rcast(surface, boss, x, y, skill_timer)
        elif action == "walk":
            NS._draw_zh_walk(surface, boss, x, y)
        else:
            NS._draw_zh_idle(surface, boss, x, y)

        # ── PROYEKTIL + SKILL FX DEPAN (fallback canvas) ───────────
        if not portrait and not owned:
            NS._handle_skill_projectiles(boss, x, y, active_skill,
                                         skill_timer)
            NS._manage_projectiles(boss, surface, pulse)
            if active_skill == "q":
                NS._draw_strafe_foreground(surface, boss, x, y, skill_timer,
                                           pulse)
            elif active_skill == "e":
                NS._draw_death_pact_foreground(surface, boss, x, y,
                                               skill_timer, pulse)

        # ── LAPISAN HIDUP DI ATAS (trail/proyektil/impact/skill) ───
        if live is not None:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass

        # ── DEBUG ──────────────────────────────────────────────────
        if NS.DEBUG_CHARACTER and not portrait:
            NS._draw_zharok_debug(surface, boss, x, y)

        _ = ap

    # ===================================================================
    # OVERLAY DEBUG RENDERER (DEBUG_CHARACTER = True)
    # ===================================================================
    _DBG_FONT = None

    @staticmethod
    def _dbg_font():
        NS = _NS_zharok
        if NS._DBG_FONT is None:
            try:
                if not pygame.font.get_init():
                    pygame.font.init()
                NS._DBG_FONT = pygame.font.SysFont("consolas,monospace", 11)
            except Exception:                          # pragma: no cover
                NS._DBG_FONT = False
        return NS._DBG_FONT or None

    @staticmethod
    def _draw_zharok_debug(surface, boss, x, y):
        """Hitbox stave, hurtbox, attack range, radius skill, state, FPS,
        jumlah partikel, timer serangan — semuanya dari controller."""
        NS = _NS_zharok
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        ap = float(getattr(boss, "_zh_attack_progress", 0.0) or 0.0)
        lo, hi = NS.ATTACK_ACTIVE_WINDOW
        active = bool(getattr(boss, "_zh_hit_window", False))
        action = getattr(boss, "_zh_pose_action", "idle")
        phase = float(getattr(boss, "_zh_phase", getattr(boss, "pulse", 0.0)))

        # jangkauan serangan (elips tanah)
        rng = float(getattr(boss, "range", 180) or 180) / max(0.05, scale)
        pygame.draw.ellipse(surface, (90, 200, 255),
                            pygame.Rect(int(x - rng), int(y + NS.GROUND_DY
                                                          - rng * 0.4),
                                        int(rng * 2), int(rng * 0.8)), 1)
        # jangkauan sabetan stave
        mr = NS.MELEE_REACH / max(0.05, scale)
        pygame.draw.ellipse(surface, (255, 160, 80),
                            pygame.Rect(int(x - mr), int(y + NS.GROUND_DY
                                                         - mr * 0.4),
                                        int(mr * 2), int(mr * 0.8)), 1)
        # radius skill aktif
        skill = getattr(boss, "active_skill", None)
        if skill in NS.SKILL_RADIUS:
            rr = NS.SKILL_RADIUS[skill] / max(0.05, scale)
            pygame.draw.ellipse(surface, (255, 120, 120),
                                pygame.Rect(int(x - rr),
                                            int(y + NS.GROUND_DY - rr * 0.4),
                                            int(rr * 2), int(rr * 0.8)), 1)
        # hurtbox
        pygame.draw.rect(surface, (70, 240, 120),
                         pygame.Rect(int(x - 26), int(y - 56), 52, 92), 1)
        # hitbox stave (grip -> tip)
        grip, tip_hi, tip_lo, _theta = NS.bow_geometry(facing, action, phase, ap)
        col = (255, 80, 80) if active else (150, 150, 160)
        pygame.draw.line(surface, col, (int(x + tip_lo[0]), int(y + tip_lo[1])),
                         (int(x + tip_hi[0]), int(y + tip_hi[1])),
                         2 if active else 1)
        pygame.draw.circle(surface, col,
                           (int(x + tip_hi[0]), int(y + tip_hi[1])), 12, 1)
        pygame.draw.circle(surface, (240, 240, 90),
                           (int(x + grip[0]), int(y + grip[1])), 2, 1)
        # proyektil canvas fallback
        for arrow in getattr(boss, "_zh_arrows", ()) or ():
            pygame.draw.circle(surface, (255, 220, 90),
                               (int(getattr(arrow, "x", x)),
                                int(getattr(arrow, "y", y))), 6, 1)

        font = NS._dbg_font()
        if font is None:
            return
        parts = 0
        proj = len(getattr(boss, "_zh_arrows", ()) or ())
        try:
            mod = NS._live_module()
            if mod is not None:
                st = mod.stats()
                parts = st.get("particles", 0)
                proj += st.get("projectiles", 0)
        except Exception:                              # pragma: no cover
            pass
        dt = float(getattr(boss, "_zh_dt", 1.0 / 60.0)) or (1.0 / 60.0)
        lines = [
            "ZHAROK [renderer debug]",
            "state %s <- %s (p%d)" % (
                getattr(boss, "_zh_state", "?"),
                getattr(boss, "_zh_state_prev", "-"),
                int(getattr(boss, "_zh_state_priority", 0))),
            "pose %s  dt %.4f  fps %.0f" % (action, dt, 1.0 / max(1e-4, dt)),
            "attack %.2f %s%s" % (ap,
                                  getattr(boss, "_zh_attack_phase", "NONE"),
                                  "  <HIT>" if active else ""),
            "window %.2f-%.2f  impact %.2f" % (lo, hi,
                                               NS.ATTACK_IMPACT_FRAME),
            "swing %s  timer %s cd %s" % (
                "MELEE" if getattr(boss, "_zh_melee_swing", False) else "BOW",
                getattr(boss, "timer", "-"),
                getattr(boss, "attack_cooldown", "-")),
            "skill %s t%s  live %s" % (
                skill or "-", getattr(boss, "active_skill_timer", "-"),
                "ON" if getattr(boss, "_zh_suppress_canvas_fx", False)
                else "off"),
            "part %d  proj %d" % (parts, proj),
        ]
        pad = 4
        w = max(font.size(t)[0] for t in lines) + pad * 2
        h = len(lines) * 13 + pad * 2
        box = pygame.Surface((w, h), pygame.SRCALPHA)
        box.fill((10, 8, 12, 190))
        pygame.draw.rect(box, (255, 140, 60, 200), box.get_rect(), 1)
        for i, t in enumerate(lines):
            box.blit(font.render(t, True, (255, 224, 190)),
                     (pad, pad + i * 13))
        surface.blit(box, (int(x) - w - 46, int(y) - 100))

    @staticmethod
    def draw_boss(surface, boss, x, y):
        _NS_zharok.draw_zharok(surface, boss, x, y)



# ====================================================================
# PYRENTH
# ====================================================================
class _NS_pyrenth:
    """Namespace pyrenth — PIXEL MASTERWORK + COMBAT FX v3.

    Rewrite penuh renderer + sistem tempur **PYRENTH, THE DEVOURER**
    (mini-boss level 4).

    Pembagian kerja:

      RENDERER (file ini)                  LAPISAN HIDUP (heroes/pyrenth_fx.py)
      -----------------------------------  ------------------------------------------
      rig demon lord bersayap + pedang     trail ayunan (histori posisi bilah NYATA)
        api, 100% prosedural               particle system (bara/asap/jiwa/serpihan)
      palette + outline + rim light        Doom Bolt / Soul Ember modular
      ANIMATION CONTROLLER (state,         (SPAWN->TRAVEL->TRAIL->HIT->IMPACT)
        fase, hit window, delta time)      IMPACT FX + hit-stop + screen shake
      ARK ayunan bilah (BLADE_ARC)         SkillFX q/w/e/r lifecycle penuh
      telegraph tanah q/w/e/r              overlay DEBUG_CHARACTER
      fallback penuh saat modul FX         -- semua di luar cache sprite --
        tidak tersedia

    100% PROSEDURAL: tidak ada PNG / JPG / GIF / sprite-sheet, dan tidak
    ada pemuat gambar eksternal apa pun.
    """

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    #: flag debug global (hitbox/hurtbox/range/state/frame/FPS/partikel/
    #: skill state/attack timer).  Diubah dari luar:
    #:   ``bosses.level4._NS_pyrenth.DEBUG_CHARACTER = True``
    DEBUG_CHARACTER = False

    # ── STATE LAPISAN HIDUP ───────────────────────────────────────
    _LIVE_MOD = None
    _last_rig = None                 # rig terakhir (untuk afterimage FX)
    _last_rig_off = (0, 0)
    _body_buf = None
    RIG_W, RIG_H = 320, 240
    RIG_OX, RIG_OY = 160, 140
    GROUND_DY = 58

    # ── KONSTANTA TEMPUR (dikontrakkan dengan AI di base_boss) ──
    #: durasi skill dalam FRAME engine (active_skill_timer) — SAMA PERSIS
    #: dengan yang di-set ``_cast_pyrenth_*`` di bosses/base_boss.py.
    SKILL_DUR = {"q": 50, "w": 40, "e": 60, "r": 70}
    #: radius damage DUNIA (px) — sama dengan cek jarak di AI.
    SKILL_RADIUS = {"q": 200, "w": 200, "e": 180, "r": 220}
    #: jangkauan tebasan pedang api (px dunia) untuk overlay debug & tes.
    MELEE_REACH = 96

    #: jendela hit aktif (progress 0..1) + frame impact. ``0.52`` dipakai
    #: renderer (puncak ayunan BLADE_ARC) DAN lapisan hidup (momen impact)
    #: — satu angka, satu detak.
    ATTACK_ACTIVE_WINDOW = (0.38, 0.62)
    ATTACK_IMPACT_FRAME = 0.52

    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, 0.12),
        ("WINDUP",       0.12, 0.30),
        ("SWING",        0.30, 0.50),
        ("IMPACT",       0.50, 0.62),
        ("FOLLOW",       0.62, 0.82),
        ("RECOVERY",     0.82, 1.00),
    )

    #: prioritas state (besar menang) — dibaca controller + debug + FX.
    ANIM_STATES = {
        "IDLE": 0, "WALK": 10, "RUN": 15, "CHARGE": 30, "CAST": 35,
        "ATTACK": 40, "SWING": 45, "SKILL": 50, "SPECIAL": 55,
        "HIT": 60, "HURT": 65, "DEATH": 100,
    }

    # ── ARK BILAH: SATU SUMBER KEBENARAN ──────────────────────────
    # (t0, t1, phi0, phi1, ease).  Konvensi ruang layar (y ke bawah):
    #   tip = grip + (facing * cos(phi) * L, -sin(phi) * L)
    # guard phi = 0.96 rad (~55° depan-atas).  Ayunan: guard -> wind-up
    # ke atas-belakang (2.18-2.88) -> tebasan cepat ke bawah (2.88 ->
    # -1.31, melewati 0.52 = IMPACT) -> follow-through -> kembali ke
    # guard.  Loop TERTUTUP: phi(0) == phi(1), dan tidak ada satu pun
    # segmen yang melompat — bilah tidak pernah teleport.  Lapisan hidup
    # heroes/pyrenth_fx.py menyimpan tabel cadangan IDENTIK dan selalu
    # membaca fungsi di sini bila tersedia.
    BLADE_ARC = (
        (0.00, 0.12,  0.96,  2.18, "out"),
        (0.12, 0.30,  2.18,  2.88, "io"),
        (0.30, 0.50,  2.88, -1.31, "oc"),
        (0.50, 0.62, -1.31, -1.05, "hold"),
        (0.62, 0.82, -1.05, -0.44, "io"),
        (0.82, 1.00, -0.44,  0.96, "io"),
    )
    _BLADE_HALF = 34.0           # panjang bilah (px, skala layar 1)
    _GRIP = (26.0, -8.7)         # grip diam (relatif jangkar badan)

    # ---------------------------------------------------------------------------
    # HD Demon Palette - Dark red skin / orange fire / black armor
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Demon skin - dark red / molten
        "skin_darkest":   (25,   8,   8),
        "skin_dark":      (75,  22,  18),
        "skin_mid":       (135, 45,  25),
        "skin_light":     (195, 85,  35),
        "skin_high":      (235, 135, 55),
        "skin_shine":     (255, 190, 100),

        # Molten cracks (glowing)
        "molten_dark":    (155, 45,  10),
        "molten_mid":     (230, 90,  15),
        "molten_bright":  (255, 145, 40),
        "molten_hot":     (255, 200, 80),
        "molten_glow":    (255, 235, 145),

        # Fire (orange/yellow)
        "fire_darkest":   (60,  15,   5),
        "fire_dark":      (140, 35,  10),
        "fire_mid":       (220, 75,  20),
        "fire_bright":    (255, 125, 35),
        "fire_hot":       (255, 180, 65),
        "fire_glow":      (255, 220, 130),
        "fire_white":     (255, 250, 210),

        # Armor - black metal with red trim
        "arm_darkest":    (8,    8,  12),
        "arm_dark":       (28,  25,  32),
        "arm_mid":        (60,  55,  65),
        "arm_light":      (110, 105, 118),
        "arm_shine":      (170, 165, 178),

        # Wing membrane (dark red-black)
        "wing_darkest":   (18,   8,  10),
        "wing_dark":      (55,  20,  22),
        "wing_mid":       (100, 40,  35),
        "wing_light":     (155, 70,  50),

        # Horns / bone (dark)
        "horn_darkest":   (25,  18,  15),
        "horn_dark":      (55,  42,  35),
        "horn_mid":       (95,  78,  62),
        "horn_light":     (150, 130, 100),
        "horn_shine":     (210, 195, 165),

        # Metal (sword)
        "metal_darkest":  (18,  15,  18),
        "metal_dark":     (48,  45,  55),
        "metal_mid":      (100, 95, 110),
        "metal_light":    (170, 165, 180),
        "metal_shine":    (225, 220, 235),
        "metal_edge":     (250, 250, 255),

        # Gold accents
        "gold_dark":      (95,  62,  15),
        "gold_mid":       (180, 130, 40),
        "gold_light":     (235, 190, 80),
        "gold_shine":     (255, 230, 140),

        # Eyes - glowing orange
        "eye_dark":       (75,  20,   5),
        "eye_bright":     (255, 140, 40),
        "eye_hot":        (255, 220, 130),

        # Loincloth (dark)
        "cloth_darkest":  (15,   8,   8),
        "cloth_dark":     (45,  22,  18),
        "cloth_mid":      (85,  40,  25),

        # Chains (dark metal)
        "chain_dark":     (25,  18,  20),
        "chain_mid":      (65,  55,  60),
        "chain_light":    (130, 118, 125),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (3,   2,   3),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_pyrenth._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_pyrenth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_pyrenth._clamp(color)
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
        color = _NS_pyrenth._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)


    def _ellipse(surface, color, rect, width=0):
        color = _NS_pyrenth._clamp(color)
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
        color = _NS_pyrenth._clamp(color)
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
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # DENGAN kompensasi scale. Hero di-render ke canvas
            # offscreen lalu di-scale saat blit (heroes/__init__.py),
            # jadi titik canvas harus = (delta dunia)/scale supaya
            # beam/proyektil mendarat TEPAT di target setelah blit.
            # Boss yang digambar langsung di layar tidak terpengaruh
            # (scale = 1).
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return int(x + 220 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Fire particle helpers
    # ---------------------------------------------------------------------------
    def _draw_ember(surface, cx, cy, size=2, alpha=255):
        _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_dark"], alpha), (cx, cy), size + 1)
        _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_bright"], alpha), (cx, cy), size)
        _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_hot"], alpha), (cx, cy), max(1, size - 1))
        _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_glow"], min(255, alpha)), (cx, cy), 1)


    def _draw_flame(surface, cx, cy, size, phase, alpha=255):
        """Rising flame."""
        height = int(size * 2.5)
        for h in range(height):
            t = h / max(1, height)
            w = int(size * (1 - t * 0.7))
            fx = cx + int(math.sin(phase * 3 + t * 4) * 2)
            fy = cy - h
            a = int(alpha * (1 - t * 0.4))
            if t < 0.3:
                color = _NS_pyrenth.PALETTE["fire_darkest"]
            elif t < 0.55:
                color = _NS_pyrenth.PALETTE["fire_mid"]
            elif t < 0.8:
                color = _NS_pyrenth.PALETTE["fire_bright"]
            else:
                color = _NS_pyrenth.PALETTE["fire_hot"]
            _NS_pyrenth._aacircle(surface, (*color, a), (fx, fy), max(1, w))
        _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_glow"], alpha), (cx, cy - height // 3), size // 2)
        _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_white"], alpha),
                  (cx, cy - height // 4), max(1, size // 4))


    def _draw_fire_spike(surface, cx, base_y, tip_y, width=4, alpha=255, phase=0):
        """Fire-based spike rising from ground."""
        _NS_pyrenth._poly(surface, (*_NS_pyrenth.PALETTE["shadow_deep"], alpha), [
            (cx - width + 1, base_y + 1),
            (cx + width + 1, base_y + 1),
            (cx + 1, tip_y + 1),
        ])
        _NS_pyrenth._poly(surface, (*_NS_pyrenth.PALETTE["fire_darkest"], alpha), [
            (cx - width, base_y),
            (cx + width, base_y),
            (cx, tip_y),
        ])
        _NS_pyrenth._poly(surface, (*_NS_pyrenth.PALETTE["fire_dark"], alpha), [
            (cx - width + 1, base_y - 1),
            (cx + width - 1, base_y - 1),
            (cx, tip_y + 2),
        ])
        _NS_pyrenth._poly(surface, (*_NS_pyrenth.PALETTE["fire_mid"], alpha), [
            (cx - width + 2, base_y - 1),
            (cx + width - 2, base_y - 1),
            (cx, tip_y + 4),
        ])
        _NS_pyrenth._poly(surface, (*_NS_pyrenth.PALETTE["fire_bright"], alpha), [
            (cx - width + 3, base_y - 1),
            (cx + width - 3, base_y - 1),
            (cx, tip_y + 6),
        ])
        _NS_pyrenth._poly(surface, (*_NS_pyrenth.PALETTE["fire_hot"], alpha), [
            (cx - 1, base_y - 1),
            (cx + 1, base_y - 1),
            (cx, tip_y + 8),
        ])
        _NS_pyrenth._aaline(surface, (*_NS_pyrenth.PALETTE["fire_glow"], alpha),
                (cx, base_y - 2), (cx, tip_y + 3), 1)
        _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_white"], alpha), (cx, tip_y + 1), 1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM
    # ---------------------------------------------------------------------------
    class DoomChain:
        """Q - Fire chain link to target (like Doom's doom chain)."""
        def __init__(self, sx, sy, tx, ty, life=60):
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
            t = self.age / self.life
            # Fade in/out
            if t < 0.15:
                alpha_scale = t / 0.15
            elif t < 0.75:
                alpha_scale = 1.0
            else:
                alpha_scale = 1 - (t - 0.75) / 0.25

            dx = self.tx - self.sx
            dy = self.ty - self.sy
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 1:
                return

            # Chain grows toward target
            if t < 0.25:
                chain_len = dist * (t / 0.25)
            else:
                chain_len = dist

            dir_x = dx / dist
            dir_y = dy / dist

            # Draw chain links (interlocking circles)
            num_links = int(chain_len / 8)
            for i in range(num_links):
                t_pos = i / max(1, num_links)
                lx = int(self.sx + dir_x * chain_len * t_pos)
                ly = int(self.sy + dir_y * chain_len * t_pos)

                # Alternate link orientation
                if i % 2 == 0:
                    _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["shadow_deep"], int(220 * alpha_scale)),
                              (lx + 1, ly + 1), 4)
                    _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["chain_dark"], int(240 * alpha_scale)),
                              (lx, ly), 4)
                    _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["chain_mid"], int(240 * alpha_scale)),
                              (lx, ly), 3, 1)
                else:
                    _NS_pyrenth._ellipse(surface, (*_NS_pyrenth.PALETTE["shadow_deep"], int(220 * alpha_scale)),
                             (lx - 5 + 1, ly - 3 + 1, 10, 6))
                    _NS_pyrenth._ellipse(surface, (*_NS_pyrenth.PALETTE["chain_dark"], int(240 * alpha_scale)),
                             (lx - 5, ly - 3, 10, 6))
                    _NS_pyrenth._ellipse(surface, (*_NS_pyrenth.PALETTE["chain_mid"], int(240 * alpha_scale)),
                             (lx - 5, ly - 3, 10, 6), 1)

                # Fire glow on link
                _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_bright"], int(150 * alpha_scale)),
                          (lx, ly), 5)
                _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_hot"], int(180 * alpha_scale)),
                          (lx, ly), 2)

            # Bright fire at target end (doomed marker)
            if t > 0.3 and t < 0.85:
                impact_intensity = math.sin((t - 0.3) / 0.55 * math.pi) * 0.5 + 0.5
                ex = int(self.sx + dir_x * chain_len)
                ey = int(self.sy + dir_y * chain_len)

                r = int(12 * impact_intensity)
                _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_darkest"], int(200 * alpha_scale)),
                          (ex, ey), r + 4)
                _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_bright"], int(230 * alpha_scale)),
                          (ex, ey), r)
                _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_hot"], int(255 * alpha_scale)),
                          (ex, ey), max(1, r - 4))
                _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_glow"], int(255 * alpha_scale)),
                          (ex, ey), max(1, r - 8))

                # Fire particles rising from target
                for i in range(5):
                    pt = (phase * 0.6 + i * 0.2) % 1.0
                    px = ex + int(math.sin(phase * 3 + i) * 5)
                    py = ey - int(pt * 25)
                    pa = int(255 * (1 - pt) * alpha_scale)
                    _NS_pyrenth._draw_ember(surface, px, py, 2, pa)


    class InfernalArc:
        """R - Big fire slash arc."""
        def __init__(self, x, y, facing, life=35, radius=100):
            self.x = x
            self.y = y
            self.facing = facing
            self.life = life
            self.age = 0
            self.radius = radius
            self.alive = True

        def update(self):
            self.age += 1
            if self.age >= self.life:
                self.alive = False

        def draw(self, surface, phase):
            t = self.age / self.life
            visibility = math.sin(t * math.pi)  # peak at middle

            # Big fire arc sweep
            arc_pts = []
            for i in range(25):
                u = i / 24
                angle = -math.pi * 0.7 + u * math.pi * 1.4
                r = self.radius * (0.5 + t * 0.5)
                px = self.x + int(math.cos(angle) * r) * self.facing
                py = self.y + int(math.sin(angle) * r * 0.7)
                arc_pts.append((px, py, angle))

            # Draw many flame balls along the arc
            for i, (px, py, angle) in enumerate(arc_pts):
                alpha = int(230 * visibility)
                # size varies
                size = int(8 + math.sin(t * 5 + i * 0.5) * 4)

                _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_darkest"], alpha), (px, py), size + 2)
                _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_dark"], alpha), (px, py), size)
                _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_mid"], alpha), (px, py), max(1, size - 2))
                _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_bright"], alpha), (px, py), max(1, size - 4))
                _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_hot"], alpha), (px, py), max(1, size - 6))
                _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_glow"], alpha), (px, py), max(1, size - 8))

            # Rising flame tips at outer edge
            for i in range(0, 25, 3):
                px, py, angle = arc_pts[i]
                _NS_pyrenth._draw_flame(surface, px, py, 4, phase + i, int(230 * visibility))

            # Trailing embers behind arc
            for i in range(15):
                u = i / 14
                angle = -math.pi * 0.7 + u * math.pi * 1.4
                r = self.radius * 0.7
                px = self.x + int(math.cos(angle) * r) * self.facing
                py = self.y + int(math.sin(angle) * r * 0.7)
                _NS_pyrenth._draw_ember(surface, px + int(math.sin(phase + i) * 5),
                            py + int(math.cos(phase + i) * 3),
                            2, int(200 * visibility))


    # ===================================================================
    # GERBANG LAPISAN HIDUP (heroes/pyrenth_fx)
    #   Trail sabetan, partikel, proyektil, skill FX, impact, hit-stop,
    #   dan screen shake hidup di RUANG LAYAR skala 1:1 supaya tidak ikut
    #   beku / menyusut bersama sprite cache di lane hero. Kalau modulnya
    #   tidak ada, owns() False dan renderer menggambar semuanya sendiri
    #   lewat jalur canvas (visual kehilangan polish, TIDAK PERNAH
    #   kehilangan efek).
    # ===================================================================
    @staticmethod
    def _live_module():
        NS = _NS_pyrenth
        if NS._LIVE_MOD is None:
            try:
                from heroes import pyrenth_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "PYRENTH_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    @staticmethod
    def live_fx_ready():
        return _NS_pyrenth._live_module() is not None

    @staticmethod
    def _live_fx(boss, surface, x, y, want_draw, portrait):
        """Pasang/gambar lapisan hidup. Return (mod_untuk_draw, owned)."""
        NS = _NS_pyrenth
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
            if owned and not want_draw:
                # Lane hero: yang menggambar lapisan hidup adalah pipeline
                # heroes/__init__ (_live_fx_pre/_live_fx_post). Kalau
                # ternyata TIDAK ada yang menggambarnya, jangan matikan
                # fallback canvas — karakter tidak boleh kehilangan FX
                # secara diam-diam.
                checker = getattr(mod, "recently_drawn", None)
                if checker is not None:
                    owned = bool(checker(boss))
        except Exception:
            owned = False
        return (mod if want_draw else None), owned

    # ===================================================================
    # ANIMATION CONTROLLER
    #   Satu-satunya sumber kebenaran state/fase/timing. Lapisan hidup,
    #   overlay debug, dan alat uji semuanya membacanya dari sini.
    # ===================================================================
    @staticmethod
    def _ease(kind, t):
        if t <= 0.0:
            return 0.0
        if t >= 1.0:
            return 1.0
        if kind == "out":
            return 1.0 - (1.0 - t) * (1.0 - t)
        if kind == "oc":                              # out-cubic (cepat)
            return 1.0 - (1.0 - t) ** 3
        if kind == "in":
            return t * t
        if kind == "hold":
            return math.sin(t * math.pi * 0.5)
        return t * t * (3.0 - 2.0 * t)                # in-out (smoothstep)

    @staticmethod
    def attack_phases_order():
        return tuple(name for name, _a, _b in _NS_pyrenth.ATTACK_PHASES)

    @staticmethod
    def attack_phase(progress):
        """Nama fase serangan untuk progress 0..1."""
        p = max(0.0, min(1.0, float(progress)))
        for name, a, b in _NS_pyrenth.ATTACK_PHASES:
            if a <= p < b:
                return name
        return "RECOVERY"

    # ── GEOMETRI BILAH (dipakai canvas, trail, & hitbox) ──────────
    @staticmethod
    def _blade_lift(progress):
        """Kenaikan grip (0..1) saat ayunan.

        Bilah tidak hanya BERPUTAR — grip-nya juga naik saat wind-up dan
        menghunjam turun saat impact.  Itu yang memberi bobot: tangan
        ikut bergerak, bukan cuma pedangnya yang berotasi di tempat.
        Lapisan hidup punya fallback identik di
        ``heroes/pyrenth_fx._fallback_lift``.
        """
        NS = _NS_pyrenth
        p = max(0.0, min(1.0, float(progress)))
        E = NS._ease
        if p < 0.12:
            return 0.5 * E("out", p / 0.12)
        if p < 0.30:
            return 0.5 + 0.4 * E("io", (p - 0.12) / 0.18)
        if p < 0.50:
            return 0.9 - 0.9 * E("oc", (p - 0.30) / 0.20)
        if p < 0.62:
            return -0.12 * E("hold", (p - 0.50) / 0.12)
        if p < 0.82:
            return -0.12 + 0.17 * E("io", (p - 0.62) / 0.20)
        return 0.05 * (1.0 - E("io", (p - 0.82) / 0.18))

    @staticmethod
    def _blade_arc(progress):
        """``(phi, lift)`` ARK bilah — SATU sumber kebenaran."""
        NS = _NS_pyrenth
        p = max(0.0, min(1.0, float(progress)))
        for t0, t1, a0, a1, kind in NS.BLADE_ARC:
            if t0 <= p < t1 or (p >= 1.0 and t1 >= 1.0):
                e = NS._ease(kind, (p - t0) / max(0.0001, t1 - t0))
                return a0 + (a1 - a0) * e, NS._blade_lift(p)
        return NS.BLADE_ARC[0][2], 0.0

    @staticmethod
    def blade_geometry(facing, action, phase, attack_progress):
        """``(grip, tip_atas, ujung_bawah, phi)`` bilah — lokal badan.

        Titik-titik RELATIF jangkar badan ``(cx, cy)`` di skala layar 1.
        Inilah satu-satunya fungsi yang menghitung posisi pedang:
        canvas menggambar bilahnya, lapisan hidup mengukur trail &
        hitbox-nya, overlay debug menggambar rentang-nya.
        """
        NS = _NS_pyrenth
        ap = max(0.0, min(1.0, float(attack_progress)))
        if action in ("swing", "attack", "melee"):
            phi, lift = NS._blade_arc(ap)
        elif action == "r_cast":
            # INFERNAL BLADE: ayunan ultimate memakai ARK yang sama,
            # jadi bilah ultimate juga tidak pernah teleport.
            phi, lift = NS._blade_arc(ap)
            lift += 0.25
        elif action == "q_cast":
            phi, lift = 0.20 + 0.05 * math.sin(phase), 0.10   # menuding
        elif action == "w_cast":
            phi, lift = 1.15, -0.10          # bilah turun, cakar bekerja
        elif action == "e_cast":
            phi, lift = 1.75 + 0.08 * math.sin(phase * 0.8), 0.55
        elif action == "death":
            phi, lift = 0.30, -0.15          # bilah terkulai
        else:
            phi = 0.96 + 0.06 * math.sin(phase * 0.8)
            lift = 0.0
        gx = facing * (NS._GRIP[0] + 5.0 * lift)
        gy = NS._GRIP[1] - 9.0 * lift
        L = NS._BLADE_HALF
        dx = facing * math.cos(phi) * L
        dy = -math.sin(phi) * L
        return ((gx, gy),
                (gx + dx, gy + dy),
                (gx + facing * math.cos(phi) * L * 0.55,
                 gy - math.sin(phi) * L * 0.55),
                phi)

    # ── TERJANGAN (skill R) ───────────────────────────────────────
    @staticmethod
    def _lunge_offset(progress):
        """Geser visual terjangan Infernal Blade (px dunia, arah facing).

        Puncak (46 px) jatuh di engine progress 0.302-0.605.  Lapisan
        hidup membaca fungsi INI (bukan tabel sendiri) lewat
        ``heroes/pyrenth_fx.lunge_offset``.
        """
        NS = _NS_pyrenth
        p = max(0.0, min(1.0, float(progress)))
        if p < 0.302:
            return 46.0 * NS._ease("oc", p / 0.302)
        if p < 0.605:
            return 46.0
        if p < 1.0:
            return 46.0 * (1.0 - NS._ease("io", (p - 0.605) / 0.395))
        return 0.0

    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    @staticmethod
    def _detect_moving(boss):
        x = getattr(boss, "x", 0)
        y = getattr(boss, "y", 0)
        lx = getattr(boss, "_pyr_last_x", x)
        ly = getattr(boss, "_pyr_last_y", y)
        boss._pyr_last_x = x
        boss._pyr_last_y = y
        dx = abs(x - lx)
        dy = abs(y - ly)
        boss._pyr_speed = dx + dy
        return (dx + dy) > 0.3

    @staticmethod
    def _update_pyr_anim(boss, moving=False):
        """Controller: delta time, state + prioritas, timeline serangan.

        Pyrenth SELALU melee (pedang api) — tidak ada mode jarak jauh,
        jadi tidak ada percabangan swing/tembak.
        """
        NS = _NS_pyrenth

        # ── delta time nyata ────────────────────────────────────────
        try:
            now = pygame.time.get_ticks()
        except Exception:                              # pragma: no cover
            now = 0
        prev_ms = getattr(boss, "_pyr_last_ms", None)
        if prev_ms is None:
            dt = 1.0 / 60.0
        else:
            dt = (now - prev_ms) / 1000.0
            if dt <= 0.0 or dt > 0.05:
                dt = 1.0 / 60.0
        boss._pyr_last_ms = now
        boss._pyr_dt = dt

        # ── timeline serangan (timer engine menghitung MUNDUR) ─────
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 42)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_pyr_prev_timer", 0))
        active = bool(getattr(boss, "_pyr_attack_active", False))

        # serangan baru: timer melonjak naik (di-reset ke cooldown)
        if timer > previous + 1 and timer >= cooldown - 2:
            boss._pyr_attack_active = True
            boss._pyr_attack_frame = 0
            active = True
        elif active:
            boss._pyr_attack_frame = int(
                getattr(boss, "_pyr_attack_frame", 0)) + 1
            if boss._pyr_attack_frame > cooldown:
                boss._pyr_attack_active = False
                boss._pyr_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._pyr_attack_active = False
            boss._pyr_attack_frame = 0
            active = False

        boss._pyr_prev_timer = timer
        frame = int(getattr(boss, "_pyr_attack_frame", 0))
        # durasi animasi dibatasi supaya tebasan berat tetap berbobot
        anim_len = max(10, min(cooldown - 1, 30))
        progress = min(1.0, frame / float(anim_len)) if active else 0.0
        boss._pyr_attack_progress = progress
        boss._pyr_attack_phase = (NS.attack_phase(progress) if active
                                  else "NONE")
        lo, hi = NS.ATTACK_ACTIVE_WINDOW
        boss._pyr_hit_window = bool(active and lo <= progress <= hi)

        # ── prioritas state ─────────────────────────────────────────
        skill = getattr(boss, "active_skill", None)
        alive = bool(getattr(boss, "alive", True))
        hurt = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        speed = float(getattr(boss, "_pyr_speed", 0.0))

        if not alive:
            state = "DEATH"
        elif skill == "r":
            state = "SPECIAL"
        elif skill in ("q", "w", "e"):
            state = "SKILL"
        elif active and progress < 0.12:
            state = "CHARGE"
        elif active and progress < 0.30:
            state = "ATTACK"
        elif active:
            state = "SWING" if progress < 0.62 else "ATTACK"
        elif hurt > 0:
            state = "HURT"
        elif moving:
            state = "RUN" if speed > 1.2 else "WALK"
        else:
            state = "IDLE"

        prev_state = getattr(boss, "_pyr_state", "IDLE")
        if prev_state != state:
            boss._pyr_state_prev = prev_state
            boss._pyr_state_time = 0.0
        else:
            boss._pyr_state_time = getattr(boss, "_pyr_state_time", 0.0) + dt
        boss._pyr_state = state
        boss._pyr_state_priority = NS.ANIM_STATES.get(state, 0)
        return state

    @staticmethod
    def _update_attack_anim(boss):
        """API LAMA — dipertahankan untuk kompatibilitas mundur.

        Mendelegasikan ke controller animasi v3 supaya tidak ada dua
        sumber kebenaran yang saling menimpa ``_pyr_attack_progress``.
        """
        return _NS_pyrenth._update_pyr_anim(
            boss, moving=(float(getattr(boss, "_pyr_speed", 0.0)) > 0.3))

    @staticmethod
    def _resolve_pose_pyr(boss, moving):
        """(action, phase, attack_progress) untuk renderer + lapisan hidup."""
        NS = _NS_pyrenth
        pulse = float(getattr(boss, "pulse", 0.0))
        state = getattr(boss, "_pyr_state", "IDLE")
        ap = float(getattr(boss, "_pyr_attack_progress", 0.0) or 0.0)
        skill = getattr(boss, "active_skill", None)
        timer = int(getattr(boss, "active_skill_timer", 0))

        if state in ("SKILL", "SPECIAL") and skill in ("q", "w", "e", "r"):
            dur = NS.SKILL_DUR.get(skill, 50)
            prog = max(0.0, min(1.0, 1.0 - timer / float(dur)))
            action = {"q": "q_cast", "w": "w_cast",
                      "e": "e_cast", "r": "r_cast"}[skill]
            return action, pulse, prog
        if state in ("ATTACK", "SWING", "CHARGE"):
            return "attack", pulse, ap
        if state == "RUN":
            return "run", pulse * 2.6, 0.0
        if state == "WALK":
            return "walk", pulse * 2.3, 0.0
        if state == "DEATH":
            return "death", pulse, 0.0
        if state == "HURT":
            return "hurt", pulse, 0.0
        return "idle", pulse, 0.0



    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_pyr_chains"):
            boss._pyr_chains = []
        if not hasattr(boss, "_pyr_arcs"):
            boss._pyr_arcs = []

        for c in boss._pyr_chains:
            c.update()
            c.draw(surface, phase)
        boss._pyr_chains = [c for c in boss._pyr_chains if c.alive]

        for a in boss._pyr_arcs:
            a.update()
            a.draw(surface, phase)
        boss._pyr_arcs = [a for a in boss._pyr_arcs if a.alive]


    def _spawn_doom_chain(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_pyr_chains"):
            boss._pyr_chains = []
        boss._pyr_chains.append(_NS_pyrenth.DoomChain(sx, sy, tx, ty, life=80))


    def _spawn_infernal_arc(boss, x, y, facing):
        if not hasattr(boss, "_pyr_arcs"):
            boss._pyr_arcs = []
        boss._pyr_arcs.append(_NS_pyrenth.InfernalArc(x, y, facing, life=40, radius=90))


    # ===================================================================
    # MAIN ENTRY
    # ===================================================================
    def draw_pyrenth(surface, boss, x, y):
        """Entry point Boss.draw() sekaligus jalur hero-lane.

        Urutan render:
          GROUND -> GROUND FX -> SHADOW -> BACK PARTICLES -> BODY/ARMOR/
          HEAD/WEAPON -> ATTACK TRAIL -> PROJECTILE -> FRONT PARTICLES ->
          SKILL FX -> IMPACT FX -> DEBUG.

        Trail / partikel / proyektil / impact / hit-stop / shake hidup di
        ``heroes/pyrenth_fx`` (ruang layar 1:1); canvas hanya fallback
        bila modul itu tidak tersedia.
        """
        NS = _NS_pyrenth
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        portrait = bool(getattr(boss, "_portrait_hd", False))
        hero_lane = hasattr(boss, "_render_scale")
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        hurt = int(getattr(boss, "hurt_flash_timer", 0) or 0)

        # ── CONTROLLER ANIMASI ─────────────────────────────────────
        moving = NS._detect_moving(boss)
        NS._update_pyr_anim(boss, moving)
        action, phase, ap = NS._resolve_pose_pyr(boss, moving)
        boss._pyr_pose_action = action
        boss._pyr_phase = phase

        # ── LAPISAN HIDUP (ground) ─────────────────────────────────
        live, owned = NS._live_fx(boss, surface, x, y, not hero_lane,
                                  portrait)
        boss._pyr_suppress_canvas_fx = owned

        # ── GESER VISUAL (terjangan R / lunge tebas / flinch) ──────
        if action == "r_cast":
            dx = int(NS._lunge_offset(ap) * facing)
        elif action in ("attack", "swing", "melee"):
            dx = int(math.sin(ap * math.pi) * 5) * facing
        elif action == "q_cast":
            dx = int(math.sin(ap * math.pi * 2) * 2) * -facing
        elif hurt > 0:
            dx = int(min(3, hurt * 0.5)) * -facing
        else:
            dx = 0
        bx, by = x + dx, y

        # ── GROUND FX / AURA ───────────────────────────────────────
        if not portrait:
            NS._draw_hellfire_aura(surface, x, y, pulse, active_skill)
            NS._draw_ground_runes(surface, x, y + 46, pulse, active_skill)
            if not owned and active_skill == "e":
                NS._draw_scorched_earth_ground(surface, boss, x, y,
                                               skill_timer, pulse)

        # ── BADAN (shadow -> wisps -> rig+pedang, satu komposit) ──
        bob = 0
        if action in ("idle", "q_cast", "w_cast", "r_cast"):
            bob = int(math.sin(pulse * 0.7) * 2)
        elif action in ("walk", "run"):
            bob = int(abs(math.sin(phase * 1.2)) * 3)
        NS._draw_shadow(surface, bx, y + NS.GROUND_DY)
        NS._draw_hellfire_wisps(surface, bx, y + 42, pulse,
                                trail=action in ("walk", "run"),
                                facing=facing,
                                intense=(action in ("attack", "swing",
                                                    "melee", "q_cast",
                                                    "w_cast", "e_cast",
                                                    "r_cast")))
        NS._draw_pyr_body(surface, bx, by + bob, facing, phase, action,
                          ap, hurt=hurt)

        # ── PROYEKTIL + SKILL FX DEPAN (fallback canvas) ───────────
        if not portrait and not owned:
            if action in ("attack", "swing", "melee", "r_cast"):
                NS._draw_sword_swing_arc(surface, bx, by, facing, ap)
                NS._draw_swing_impact(surface, bx, by, facing, ap)
            NS._handle_skill_projectiles(boss, x, y, active_skill,
                                         skill_timer)
            NS._manage_projectiles(boss, surface, pulse)
            if active_skill == "e":
                NS._draw_scorched_earth(surface, boss, x, y, skill_timer,
                                        pulse)
            elif active_skill == "w":
                NS._draw_devour_effect(surface, boss, x, y, skill_timer,
                                       pulse)

        # ── LAPISAN HIDUP DI ATAS (trail/proyektil/impact/skill) ──
        if live is not None:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass

        # ── DEBUG ──────────────────────────────────────────────────
        if getattr(NS, "DEBUG_CHARACTER", False) and not portrait:
            NS._draw_pyrenth_debug(surface, boss, x, y)


    def _handle_skill_projectiles(boss, x, y, active_skill, timer):
        """Fallback canvas: lahirkan rantai Q / busur R sekali per cast.

        Dipakai HANYA saat lapisan hidup tidak tersedia; durasi diambil
        dari ``SKILL_DUR`` supaya tidak pernah menyimpang dari AI.
        """
        NS = _NS_pyrenth
        tx, ty = NS._target_position(boss, x, y)
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1

        if active_skill == "q":
            duration = NS.SKILL_DUR["q"]
            progress = max(0.0, min(1.0, 1 - timer / float(duration)))
            if 0.25 < progress < 0.35 and not getattr(boss,
                                                      "_pyr_q_spawned",
                                                      False):
                NS._spawn_doom_chain(boss, x + 20 * facing, y - 5, tx, ty)
                boss._pyr_q_spawned = True
            if progress > 0.7:
                boss._pyr_q_spawned = False

        elif active_skill == "r":
            duration = NS.SKILL_DUR["r"]
            progress = max(0.0, min(1.0, 1 - timer / float(duration)))
            if 0.35 < progress < 0.45 and not getattr(boss,
                                                      "_pyr_r_spawned",
                                                      False):
                NS._spawn_infernal_arc(boss, x + 15 * facing, y, facing)
                boss._pyr_r_spawned = True
            if progress > 0.7:
                boss._pyr_r_spawned = False

        else:
            boss._pyr_q_spawned = False
            boss._pyr_r_spawned = False


    # ===================================================================
    # POSE MODES — API LAMA
    #   Dipertahankan supaya integrasi lama (alat uji, portrait, kode
    #   pemanggil langsung) tidak patah. Semuanya kini mendelegasikan ke
    #   pipeline komposit v3, jadi tidak ada dua jalur gambar yang bisa
    #   menyimpang.
    # ===================================================================
    def _draw_pyr_idle(surface, boss, x, y):
        NS = _NS_pyrenth
        pulse = float(getattr(boss, "pulse", 0.0))
        bob = int(math.sin(pulse * 0.8) * 3)
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        NS._draw_shadow(surface, x, y + NS.GROUND_DY)
        NS._draw_hellfire_wisps(surface, x, y + 42, pulse)
        NS._draw_pyr_body(surface, x, y + bob, facing, pulse, "idle")


    def _draw_pyr_walk(surface, boss, x, y):
        NS = _NS_pyrenth
        phase = float(getattr(boss, "pulse", 0.0)) * 2.2
        bob = int(math.sin(phase * 1.2) * 4)
        sway = int(math.sin(phase * 0.5) * 2)
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        NS._draw_shadow(surface, x + sway, y + NS.GROUND_DY)
        NS._draw_hellfire_wisps(surface, x + sway, y + 42, phase,
                                trail=True, facing=facing)
        NS._draw_pyr_body(surface, x + sway, y - bob, facing, phase, "walk")


    def _draw_pyr_attack(surface, boss, x, y):
        NS = _NS_pyrenth
        pulse = float(getattr(boss, "pulse", 0.0))
        progress = max(0.0, min(1.0, getattr(boss, "_pyr_attack_progress",
                                             0.0)))
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        lunge = int(math.sin(progress * math.pi) * 5) * facing
        NS._draw_shadow(surface, x + lunge, y + NS.GROUND_DY)
        NS._draw_hellfire_wisps(surface, x + lunge, y + 42, pulse,
                                intense=True)
        NS._draw_pyr_body(surface, x + lunge, y, facing, pulse, "attack",
                          progress)
        if not getattr(boss, "_pyr_suppress_canvas_fx", False):
            NS._draw_sword_swing_arc(surface, x + lunge, y, facing,
                                     progress)
            NS._draw_swing_impact(surface, x + lunge, y, facing, progress)


    def _draw_pyr_cast(surface, boss, x, y, timer, key):
        """Pose cast generik untuk q/w/e/r (durasi dari SKILL_DUR)."""
        NS = _NS_pyrenth
        pulse = float(getattr(boss, "pulse", 0.0))
        duration = NS.SKILL_DUR.get(key, 50)
        progress = max(0.0, min(1.0, 1 - timer / float(duration)))
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        shift = (int(NS._lunge_offset(progress) * facing) if key == "r"
                 else 0)
        bob = int(math.sin(pulse * 0.7) * 2) if key != "r" else 0
        NS._draw_shadow(surface, x + shift, y + NS.GROUND_DY)
        NS._draw_hellfire_wisps(surface, x + shift, y + 42, pulse,
                                intense=True)
        NS._draw_pyr_body(surface, x + shift, y + bob, facing, pulse,
                          key + "_cast", progress)


    def _draw_pyr_qcast(surface, boss, x, y, timer):
        _NS_pyrenth._draw_pyr_cast(surface, boss, x, y, timer, "q")


    def _draw_pyr_wcast(surface, boss, x, y, timer):
        _NS_pyrenth._draw_pyr_cast(surface, boss, x, y, timer, "w")


    def _draw_pyr_ecast(surface, boss, x, y, timer):
        _NS_pyrenth._draw_pyr_cast(surface, boss, x, y, timer, "e")


    def _draw_pyr_rcast(surface, boss, x, y, timer):
        _NS_pyrenth._draw_pyr_cast(surface, boss, x, y, timer, "r")


    def _draw_pyr_body_raw(buf, ox, oy, facing, phase, action,
                           attack_progress=0):
        """Gambar iblis lengkap ke buffer — URUTAN LAYER v3.

            sayap (back limb) -> ekor -> tubuh bawah -> torso -> armor
            -> lengan + pedang -> kepala

        Semua lengan mengambil posisi tangan dari ``blade_geometry()``
        sehingga bilah, tangan, trail, dan hitbox mustahil berbeda.
        """
        NS = _NS_pyrenth
        is_casting = action.endswith("_cast")

        # 1) sayap (paling belakang)
        NS._draw_wings(buf, ox, oy - 5, facing, phase, action)
        # 2) ekor
        NS._draw_tail(buf, ox, oy + 15, facing, phase)
        # 3) tubuh bawah (cawat + sabuk)
        NS._draw_lower_body(buf, ox, oy + 12, phase)
        # 4) torso (dada berotot + armor dada)
        NS._draw_torso(buf, ox, oy - 5, phase, is_casting)
        # 5) pauldron
        NS._draw_pauldrons(buf, ox, oy - 15, phase)
        # 6) lengan + pedang api
        if action in ("attack", "swing", "melee"):
            NS._draw_attack_arms(buf, ox, oy - 5, facing, phase,
                                 attack_progress)
        elif action == "r_cast":
            NS._draw_r_arms(buf, ox, oy - 5, facing, phase,
                            attack_progress)
        elif action == "q_cast":
            NS._draw_q_cast_arms(buf, ox, oy - 5, facing, phase)
        elif action == "w_cast":
            NS._draw_w_cast_arms(buf, ox, oy - 5, facing, phase,
                                 attack_progress)
        elif action == "e_cast":
            NS._draw_e_cast_arms(buf, ox, oy - 5, facing, phase)
        else:
            NS._draw_idle_arms(buf, ox, oy - 5, facing, phase, action)
        # 7) kepala bertanduk
        NS._draw_pyr_head(buf, ox, oy - 30, facing, phase, is_casting)


    def _draw_pyr_body(surface, cx, cy, facing, phase, action,
                       attack_progress=0, hurt=0):
        """Pipeline rig: buffer -> crop -> hit flash -> outline -> blit.

        Menggambar ke buffer sekali lalu meng-outline hasil crop-nya
        memberi SILUET 4-arah yang solid — jauh lebih terbaca daripada
        meng-outline tiap bagian satu per satu, dan jauh lebih murah.
        Rig hasilnya disimpan sebagai ``_last_rig`` supaya lapisan hidup
        bisa membuat afterimage TANPA menggambar ulang badan.
        """
        NS = _NS_pyrenth
        if NS._body_buf is None:
            NS._body_buf = pygame.Surface((NS.RIG_W, NS.RIG_H),
                                          pygame.SRCALPHA)
        buf = NS._body_buf
        buf.fill((0, 0, 0, 0))
        NS._draw_pyr_body_raw(buf, NS.RIG_OX, NS.RIG_OY, facing, phase,
                              action, attack_progress)
        used = buf.get_bounding_rect(min_alpha=1)
        if used.width <= 2 or used.height <= 2:
            return
        used.inflate_ip(4, 4)
        used.clamp_ip(buf.get_rect())
        sub = buf.subsurface(used).copy()
        ox = int(cx) - NS.RIG_OX + used.left
        oy = int(cy) - NS.RIG_OY + used.top

        # hit flash: rig memutih pudar saat baru terkena damage
        if hurt > 0:
            flash = sub.copy()
            flash.fill((255, 240, 235, 255),
                       special_flags=pygame.BLEND_RGB_MAX)
            flash.set_alpha(min(210, int(hurt) * 30))
            sub.blit(flash, (0, 0))

        # outline 4-arah (siluet kuat, gaya pixel-art)
        edge = sub.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(edge, (ox + ddx, oy + ddy))
        try:
            import lighting as _lighting
            if _lighting is not None:
                _lighting.apply_to_rig(sub, rim_add=(52, 22, 12),
                                       shade_mul=170)
        except Exception:
            pass
        surface.blit(sub, (ox, oy))
        # simpan rig terakhir untuk afterimage FX
        NS._last_rig = sub
        NS._last_rig_off = (ox - int(cx), oy - int(cy))


    def _draw_wings(surface, cx, cy, facing, phase, action):
        """Two large bat wings spread out."""
        flap_speed = 1.0
        if action == "walk":
            flap_speed = 2.0
        elif action in ("r_cast", "attack"):
            flap_speed = 2.5
        flap = math.sin(phase * flap_speed) * 0.3

        for side in (-1, 1):
            wing_base_x = cx + side * 12
            wing_base_y = cy - 8

            # Wing extends up and out
            tip_x = cx + side * (42 + int(math.cos(flap) * 5))
            tip_y = cy - 30 + int(math.sin(flap) * 10)

            # Multiple finger struts
            finger1_x = cx + side * 38
            finger1_y = cy - 15 + int(math.sin(flap) * 8)
            finger2_x = cx + side * 34
            finger2_y = cy - 2 + int(math.sin(flap) * 6)
            finger3_x = cx + side * 26
            finger3_y = cy + 12 + int(math.sin(flap) * 4)

            # Wing membrane
            wing_shape = [
                (wing_base_x, wing_base_y),
                (cx + side * 20, cy - 28 + int(math.sin(flap) * 8)),
                (tip_x, tip_y),
                (cx + side * 36, cy - 20 + int(math.sin(flap) * 7)),
                (finger1_x, finger1_y),
                (cx + side * 32, cy - 8 + int(math.sin(flap) * 6)),
                (finger2_x, finger2_y),
                (cx + side * 30, cy + 5 + int(math.sin(flap) * 5)),
                (finger3_x, finger3_y),
                (cx + side * 10, cy + 8),
            ]

            # Shadow
            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["shadow_deep"],
                  [(p[0] + 2, p[1] + 2) for p in wing_shape])
            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["wing_darkest"], wing_shape)

            # Inner
            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["wing_dark"], [
                (wing_base_x + side, wing_base_y + 1),
                (cx + side * 19, cy - 26 + int(math.sin(flap) * 7)),
                (tip_x - side * 2, tip_y + 1),
                (finger1_x - side, finger1_y),
                (finger2_x - side, finger2_y),
                (finger3_x - side, finger3_y - 1),
                (cx + side * 10, cy + 7),
            ])
            # Mid tone
            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["wing_mid"], [
                (wing_base_x + side * 2, wing_base_y + 2),
                (cx + side * 25, cy - 20 + int(math.sin(flap) * 6)),
                (cx + side * 28, cy - 8 + int(math.sin(flap) * 5)),
                (cx + side * 24, cy + 5 + int(math.sin(flap) * 4)),
                (cx + side * 10, cy + 5),
            ])

            # Wing bones (finger struts)
            _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["wing_darkest"],
                    (wing_base_x, wing_base_y), (tip_x, tip_y), 2)
            _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["wing_darkest"],
                    (wing_base_x, wing_base_y), (finger1_x, finger1_y), 2)
            _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["wing_darkest"],
                    (wing_base_x, wing_base_y), (finger2_x, finger2_y), 2)
            _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["wing_darkest"],
                    (wing_base_x, wing_base_y), (finger3_x, finger3_y), 2)

            # Highlights on bones
            _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["wing_light"],
                    (wing_base_x + side, wing_base_y - 1),
                    (tip_x - side * 2, tip_y - 1), 1)

            # Claws at finger tips
            for tx, ty in [(tip_x, tip_y), (finger1_x, finger1_y),
                            (finger2_x, finger2_y), (finger3_x, finger3_y)]:
                _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_darkest"], [
                    (tx, ty),
                    (tx + side * 3, ty - 2),
                    (tx + side, ty + 1),
                ])
                _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_mid"], [
                    (tx, ty),
                    (tx + side * 2, ty - 1),
                    (tx + side, ty + 1),
                ])
                _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["horn_light"], (tx + side * 3, ty - 2), 1)


    def _draw_tail(surface, cx, cy, facing, phase):
        """Long spike-tipped demon tail."""
        tail_wave = math.sin(phase * 0.9) * 3
        tail_wave2 = math.sin(phase * 1.1 + 0.5) * 2

        # Tail curves back
        segments = [
            (cx, cy),
            (cx - facing * 8, cy + 4 + int(tail_wave)),
            (cx - facing * 16, cy + 6 + int(tail_wave * 1.5)),
            (cx - facing * 22, cy + 3 + int(tail_wave2)),
            (cx - facing * 26, cy - 5 + int(tail_wave)),
            (cx - facing * 24, cy - 13 + int(tail_wave2)),
        ]

        for i in range(len(segments) - 1):
            thickness = 6 - i
            x1, y1 = segments[i]
            x2, y2 = segments[i + 1]
            _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["shadow_deep"],
                    (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), thickness + 2)
            _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["skin_darkest"], (x1, y1), (x2, y2), thickness + 1)
            _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["skin_dark"], (x1, y1), (x2, y2), thickness)
            _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["skin_mid"], (x1, y1), (x2, y2), max(1, thickness - 2))
            _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["skin_light"], (x1 - 1, y1), (x2 - 1, y2), 1)

        # Tail spike at end
        tip_x, tip_y = segments[-1]
        spike_pts = [
            (tip_x + facing * 2, tip_y),
            (tip_x - facing * 4, tip_y - 8),
            (tip_x + facing * 1, tip_y - 3),
            (tip_x + facing * 4, tip_y - 6),
            (tip_x + facing * 2, tip_y + 2),
        ]
        _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_darkest"], spike_pts)
        _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_dark"], [
            (tip_x + facing, tip_y - 1),
            (tip_x - facing * 3, tip_y - 7),
            (tip_x + facing * 3, tip_y - 5),
        ])
        _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_mid"], [
            (tip_x + facing, tip_y - 1),
            (tip_x - facing * 2, tip_y - 6),
            (tip_x + facing * 2, tip_y - 4),
        ])
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["horn_light"], (tip_x - facing * 2, tip_y - 6), 1)


    def _draw_lower_body(surface, cx, cy, phase):
        """Belt + loincloth."""
        # Belt (metal)
        _NS_pyrenth._rect(surface, _NS_pyrenth.PALETTE["shadow_deep"], (cx - 20 + 1, cy - 4 + 1, 40, 8),
              border_radius=1)
        _NS_pyrenth._rect(surface, _NS_pyrenth.PALETTE["arm_darkest"], (cx - 20, cy - 4, 40, 8),
              border_radius=1)
        _NS_pyrenth._rect(surface, _NS_pyrenth.PALETTE["arm_dark"], (cx - 19, cy - 3, 38, 6))
        _NS_pyrenth._rect(surface, _NS_pyrenth.PALETTE["arm_mid"], (cx - 18, cy - 3, 36, 3))

        # Belt buckle - demon skull emblem
        _NS_pyrenth._rect(surface, _NS_pyrenth.PALETTE["fire_darkest"], (cx - 6, cy - 5, 12, 10),
              border_radius=2)
        _NS_pyrenth._rect(surface, _NS_pyrenth.PALETTE["fire_dark"], (cx - 5, cy - 4, 10, 8), border_radius=1)
        _NS_pyrenth._rect(surface, _NS_pyrenth.PALETTE["fire_mid"], (cx - 4, cy - 3, 8, 6))
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_bright"], (cx, cy), 3)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_hot"], (cx, cy), 2)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_glow"], (cx, cy - 1), 1)
        # Horn shapes on buckle
        _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["fire_darkest"], [
            (cx - 4, cy - 4), (cx - 5, cy - 6), (cx - 3, cy - 3),
        ])
        _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["fire_darkest"], [
            (cx + 4, cy - 4), (cx + 5, cy - 6), (cx + 3, cy - 3),
        ])

        # Rivets on belt
        for rx in (-15, -10, 10, 15):
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["arm_light"], (cx + rx, cy - 1), 1)

        # Loincloth strips
        for i, offset in enumerate([-14, -7, 0, 7, 14]):
            wave = math.sin(phase * 1.2 + i) * 2
            length = 22 + (i % 2) * 3
            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["shadow_deep"], [
                (cx + offset - 4, cy + 3),
                (cx + offset + 4, cy + 3),
                (cx + offset + 3 + int(wave), cy + length),
                (cx + offset - 3 + int(wave), cy + length),
            ])
            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["cloth_darkest"], [
                (cx + offset - 4, cy + 2),
                (cx + offset + 4, cy + 2),
                (cx + offset + 3 + int(wave), cy + length - 1),
                (cx + offset - 3 + int(wave), cy + length - 1),
            ])
            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["cloth_dark"], [
                (cx + offset - 3, cy + 3),
                (cx + offset + 3, cy + 3),
                (cx + offset + 2 + int(wave), cy + length - 3),
                (cx + offset - 2 + int(wave), cy + length - 3),
            ])
            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["cloth_mid"], [
                (cx + offset - 2, cy + 4),
                (cx + offset + 2, cy + 4),
                (cx + offset + 1 + int(wave), cy + length - 5),
                (cx + offset - 1 + int(wave), cy + length - 5),
            ])


    def _draw_torso(surface, cx, cy, phase, is_casting):
        """Massive muscular demon torso."""
        intensity = 1.3 if is_casting else 1.0

        # Shadow
        _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["shadow_deep"], [
            (cx - 16 + 2, cy - 10 + 2), (cx + 16 + 2, cy - 10 + 2),
            (cx + 15 + 2, cy + 16 + 2), (cx - 15 + 2, cy + 16 + 2),
        ])

        # Main torso
        torso = [
            (cx - 16, cy - 10),
            (cx + 16, cy - 10),
            (cx + 15, cy + 16),
            (cx - 15, cy + 16),
        ]
        _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["skin_darkest"], torso)
        _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["skin_dark"], [
            (cx - 14, cy - 8),
            (cx + 14, cy - 8),
            (cx + 13, cy + 14),
            (cx - 13, cy + 14),
        ])
        _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["skin_mid"], [
            (cx - 11, cy - 5),
            (cx + 11, cy - 5),
            (cx + 10, cy + 10),
            (cx - 10, cy + 10),
        ])

        # Chest muscles (pectorals)
        for side in (-1, 1):
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["skin_light"],
                      (cx + side * 6, cy - 2), 5)
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["skin_high"],
                      (cx + side * 6 - 1, cy - 4), 2)

        # Ab lines
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["skin_darkest"], (cx, cy + 2), (cx, cy + 15), 1)
        for yoff in (4, 8, 12):
            _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["skin_darkest"],
                    (cx - 6, cy + yoff), (cx + 6, cy + yoff), 1)

        # MOLTEN CRACKS glowing (Doom signature)
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        crack_alpha = int(255 * pulse * intensity)

        # Horizontal crack across chest
        _NS_pyrenth._aaline(surface, (*_NS_pyrenth.PALETTE["molten_dark"], crack_alpha),
                (cx - 10, cy), (cx + 10, cy + 2), 2)
        _NS_pyrenth._aaline(surface, (*_NS_pyrenth.PALETTE["molten_mid"], crack_alpha),
                (cx - 9, cy), (cx + 9, cy + 2), 1)
        _NS_pyrenth._aaline(surface, (*_NS_pyrenth.PALETTE["molten_bright"], crack_alpha),
                (cx - 7, cy + 1), (cx + 7, cy + 2), 1)

        # Vertical crack down center
        _NS_pyrenth._aaline(surface, (*_NS_pyrenth.PALETTE["molten_dark"], crack_alpha),
                (cx, cy - 5), (cx - 2, cy + 12), 2)
        _NS_pyrenth._aaline(surface, (*_NS_pyrenth.PALETTE["molten_bright"], crack_alpha),
                (cx, cy - 4), (cx - 1, cy + 11), 1)
        _NS_pyrenth._aaline(surface, (*_NS_pyrenth.PALETTE["molten_hot"], crack_alpha),
                (cx, cy - 3), (cx - 1, cy + 8), 1)

        # Diagonal cracks
        _NS_pyrenth._aaline(surface, (*_NS_pyrenth.PALETTE["molten_dark"], crack_alpha),
                (cx - 10, cy + 6), (cx - 5, cy + 12), 1)
        _NS_pyrenth._aaline(surface, (*_NS_pyrenth.PALETTE["molten_mid"], crack_alpha),
                (cx + 8, cy + 5), (cx + 4, cy + 13), 1)

        # Spikes on shoulders/upper chest (bone spikes)
        for side_off, xoff in [(-1, -10), (1, 10)]:
            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_darkest"], [
                (cx + xoff, cy - 8),
                (cx + xoff + side_off * 2, cy - 15),
                (cx + xoff - side_off, cy - 10),
            ])
            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_dark"], [
                (cx + xoff, cy - 8),
                (cx + xoff + side_off * 2, cy - 13),
                (cx + xoff, cy - 10),
            ])
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["horn_light"], (cx + xoff + side_off * 2, cy - 15), 1)

        # Chest armor plate on lower half
        _NS_pyrenth._rect(surface, _NS_pyrenth.PALETTE["arm_darkest"], (cx - 11, cy + 6, 22, 10),
              border_radius=2)
        _NS_pyrenth._rect(surface, _NS_pyrenth.PALETTE["arm_dark"], (cx - 10, cy + 7, 20, 8),
              border_radius=1)
        _NS_pyrenth._rect(surface, _NS_pyrenth.PALETTE["arm_mid"], (cx - 9, cy + 7, 18, 3))

        # Central demon emblem on armor
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_darkest"], (cx, cy + 11), 3)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_bright"], (cx, cy + 11), 2)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_hot"], (cx, cy + 10), 1)

        # Rivets on armor
        for rx in (-8, -4, 4, 8):
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["arm_light"], (cx + rx, cy + 8), 1)
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["arm_light"], (cx + rx, cy + 14), 1)


    def _draw_pauldrons(surface, cx, cy, phase):
        """Massive spiked shoulder armor."""
        for side in (-1, 1):
            sx = cx + side * 17
            # Shadow
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["shadow_deep"], (sx + 2, cy + 2), 12)
            # Main pauldron
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["arm_darkest"], (sx, cy), 11)
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["arm_dark"], (sx - side, cy - 1), 9)
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["arm_mid"], (sx - side * 2, cy - 2), 7)
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["arm_light"], (sx - side * 3, cy - 4), 3)

            # Multiple spikes on top
            for i, spike_angle in enumerate([-0.6, -0.2, 0.2]):
                spike_x = sx + int(math.sin(spike_angle) * 8) * side
                spike_y = cy + int(math.cos(spike_angle) * 8) - 10
                _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_darkest"], [
                    (spike_x - 2, cy - 5),
                    (spike_x + 2, cy - 5),
                    (spike_x, spike_y - 8),
                ])
                _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_dark"], [
                    (spike_x - 1, cy - 5),
                    (spike_x + 1, cy - 5),
                    (spike_x, spike_y - 6),
                ])
                _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["horn_light"], (spike_x, spike_y - 8), 1)
                _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_hot"], (spike_x, spike_y - 7), 1)

            # Molten crack on pauldron
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["molten_dark"], (sx, cy + 2), 3)
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["molten_bright"], (sx, cy + 2), 2)
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["molten_hot"], (sx, cy + 2), 1)

            # Rivets
            for i in range(4):
                angle = i * math.pi / 2
                rx = sx + int(math.cos(angle) * 6)
                ry = cy + int(math.sin(angle) * 6)
                _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["arm_light"], (rx, ry), 1)


    def _draw_pyr_head(surface, cx, cy, facing, phase, is_casting):
        """Demon head with MASSIVE curved horns."""
        intensity = 1.3 if is_casting else 1.0

        # Shadow
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["shadow_deep"], (cx + 2, cy + 2), 12)

        # Head base
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["skin_darkest"], (cx, cy), 11)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["skin_dark"], (cx - 1, cy - 1), 9)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["skin_mid"], (cx - 2, cy - 2), 7)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["skin_light"], (cx - 3, cy - 4), 3)

        # Molten crack on forehead
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        crack_alpha = int(220 * pulse * intensity)
        _NS_pyrenth._aaline(surface, (*_NS_pyrenth.PALETTE["molten_dark"], crack_alpha),
                (cx - 5, cy - 5), (cx + 5, cy - 4), 2)
        _NS_pyrenth._aaline(surface, (*_NS_pyrenth.PALETTE["molten_bright"], crack_alpha),
                (cx - 4, cy - 5), (cx + 4, cy - 4), 1)
        _NS_pyrenth._aaline(surface, (*_NS_pyrenth.PALETTE["molten_hot"], crack_alpha),
                (cx - 3, cy - 5), (cx + 3, cy - 4), 1)

        # GLOWING ORANGE EYES
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for side in (-1, 1):
            ex = cx + side * 4
            ey = cy - 1
            # Socket
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["shadow_deep"], (ex, ey), 3)
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["eye_dark"], (ex, ey), 2)
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["eye_bright"], (ex, ey),
                      max(1, int(2 * eye_pulse * intensity)))
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["eye_hot"], (ex, ey), 1)
            # Halo
            _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["eye_bright"], int(120 * eye_pulse * intensity)),
                      (ex, ey), 5)

        # Angry brows
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["skin_darkest"],
                (cx - 7, cy - 4), (cx - 2, cy - 3), 2)
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["skin_darkest"],
                (cx + 2, cy - 3), (cx + 7, cy - 4), 2)

        # Snout / nose
        _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["skin_dark"], [
            (cx, cy + 1),
            (cx - 2, cy + 5),
            (cx + 2, cy + 5),
        ])
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["shadow_deep"], (cx - 1, cy + 4), 1)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["shadow_deep"], (cx + 1, cy + 4), 1)

        # Fanged mouth
        _NS_pyrenth._rect(surface, _NS_pyrenth.PALETTE["shadow_deep"], (cx - 5, cy + 6, 10, 3))
        # Fangs
        for tooth in (-4, -2, 0, 2, 4):
            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_light"], [
                (cx + tooth, cy + 6),
                (cx + tooth + 1, cy + 9),
                (cx + tooth + 2, cy + 6),
            ])
        # Lower fangs
        _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_light"], [
            (cx - 3, cy + 9),
            (cx - 2, cy + 6),
            (cx - 1, cy + 9),
        ])
        _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_light"], [
            (cx + 1, cy + 9),
            (cx + 2, cy + 6),
            (cx + 3, cy + 9),
        ])

        # MASSIVE HORNS (Doom signature - curved outward and up)
        for side in (-1, 1):
            # Horn base attaches to head side
            hb_x = cx + side * 7
            hb_y = cy - 3

            # Curve horn outward and up, with slight backward hook
            # Base is thick, tip is sharp
            horn_shape = [
                (hb_x, hb_y + 4),
                (hb_x + side * 5, hb_y + 2),
                (hb_x + side * 12, hb_y - 5),
                (hb_x + side * 18, hb_y - 15),
                (hb_x + side * 20, hb_y - 22),
                (hb_x + side * 16, hb_y - 20),
                (hb_x + side * 10, hb_y - 12),
                (hb_x + side * 4, hb_y - 4),
                (hb_x + side, hb_y),
            ]
            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["shadow_deep"], [(p[0] + 1, p[1] + 1) for p in horn_shape])
            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_darkest"], horn_shape)

            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_dark"], [
                (hb_x + side, hb_y + 3),
                (hb_x + side * 5, hb_y + 1),
                (hb_x + side * 11, hb_y - 5),
                (hb_x + side * 17, hb_y - 14),
                (hb_x + side * 19, hb_y - 21),
                (hb_x + side * 15, hb_y - 19),
                (hb_x + side * 9, hb_y - 11),
                (hb_x + side * 3, hb_y - 3),
            ])
            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_mid"], [
                (hb_x + side * 2, hb_y + 2),
                (hb_x + side * 5, hb_y),
                (hb_x + side * 10, hb_y - 5),
                (hb_x + side * 15, hb_y - 13),
                (hb_x + side * 17, hb_y - 19),
                (hb_x + side * 13, hb_y - 17),
                (hb_x + side * 8, hb_y - 10),
            ])

            # Highlight along outer curve
            _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["horn_light"],
                    (hb_x + side * 5, hb_y - 1),
                    (hb_x + side * 18, hb_y - 18), 1)
            _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["horn_shine"],
                    (hb_x + side * 15, hb_y - 15),
                    (hb_x + side * 19, hb_y - 21), 1)

            # Sharp tip glow
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["horn_shine"], (hb_x + side * 20, hb_y - 22), 1)
            _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_hot"], 180),
                      (hb_x + side * 20, hb_y - 22), 2)

            # Horn ridges (bumps along horn)
            for i in range(3):
                t = 0.2 + i * 0.25
                rx = hb_x + side * int(5 + t * 15)
                ry = hb_y + int(1 - t * 20)
                _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["horn_darkest"], (rx, ry), 2)
                _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["horn_dark"], (rx, ry), 1)


    # ===================================================================
    # LENGAN — SEMUA posisi tangan berasal dari blade_geometry()
    #   Tidak ada satu pun lengan yang menghitung sudut pedangnya
    #   sendiri; itu sebabnya bilah, tangan, trail, dan hitbox tidak
    #   pernah bisa melenceng satu frame pun.
    # ===================================================================
    @staticmethod
    def _grip_screen(cx, cy, facing, action, phase, progress):
        """Titik grip (tangan senjata) dalam ruang buffer badan.

        ``blade_geometry`` bekerja relatif JANGKAR BADAN, sedangkan
        fungsi lengan dipanggil dengan jangkar bahu ``(cx, cy)`` =
        jangkar badan + (0, -5).  Offset itu dikompensasi di sini.
        """
        NS = _NS_pyrenth
        grip, tip_hi, tip_lo, phi = NS.blade_geometry(facing, action,
                                                      phase, progress)
        return ((cx + grip[0], cy + 5 + grip[1]),
                (cx + tip_hi[0], cy + 5 + tip_hi[1]),
                (cx + tip_lo[0], cy + 5 + tip_lo[1]), phi)

    @staticmethod
    def _draw_weapon_arm(surface, sh_x, sh_y, hand_x, hand_y, facing):
        """Lengan dua ruas yang membengkok WAJAR ke tangan senjata.

        Siku ditempatkan di tengah lalu digeser tegak lurus, jadi lengan
        melengkung mengikuti ayunan alih-alih menjadi tongkat lurus.
        """
        NS = _NS_pyrenth
        dx = hand_x - sh_x
        dy = hand_y - sh_y
        L = math.hypot(dx, dy) or 1.0
        # geser siku tegak lurus: makin panjang jangkauan, makin lurus
        bend = max(0.0, 1.0 - L / 44.0) * 9.0 + 3.0
        mx = sh_x + dx * 0.5 - (dy / L) * bend * facing
        my = sh_y + dy * 0.5 + (dx / L) * bend * facing
        NS._draw_pyr_arm(surface, sh_x, sh_y, mx, my)
        NS._draw_pyr_arm(surface, mx, my, hand_x, hand_y)
        NS._draw_claw_hand(surface, int(hand_x), int(hand_y), facing)

    @staticmethod
    def _draw_off_arm(surface, cx, cy, facing, phase, lift=0.0,
                      reach=0.0):
        """Lengan bebas (tanpa senjata) — menggantung / terangkat."""
        NS = _NS_pyrenth
        side = -facing
        sway = math.sin(phase * 0.7) * 2
        sh_x = cx + side * 16
        sh_y = cy - 2
        elbow_x = sh_x + side * (8 + reach * 0.4)
        elbow_y = cy + 10 - lift * 16 + sway
        hand_x = elbow_x + side * (4 + reach * 0.6)
        hand_y = elbow_y + 10 - lift * 14
        NS._draw_pyr_arm(surface, sh_x, sh_y, elbow_x, elbow_y)
        NS._draw_pyr_arm(surface, elbow_x, elbow_y, hand_x, hand_y)
        NS._draw_claw_hand(surface, int(hand_x), int(hand_y), side)
        return hand_x, hand_y

    def _draw_idle_arms(surface, cx, cy, facing, phase, action="idle"):
        """IDLE / WALK: lengan bebas menggantung, pedang ikut bernapas."""
        NS = _NS_pyrenth
        NS._draw_off_arm(surface, cx, cy, facing, phase)
        grip, tip_hi, _lo, _phi = NS._grip_screen(cx, cy, facing, action,
                                                  phase, 0.0)
        NS._draw_weapon_arm(surface, cx + facing * 16, cy - 2,
                            grip[0], grip[1], facing)
        NS._draw_flaming_sword_line(surface, grip[0], grip[1], tip_hi[0],
                                    tip_hi[1], facing, phase)


    def _draw_attack_arms(surface, cx, cy, facing, phase, progress):
        """ATTACK: tebasan overhead — bilah MENGIKUTI BLADE_ARC.

        Bilah tidak pernah dipindah dari pose A ke pose B; posisinya
        selalu titik pada ARK, jadi ayunannya melengkung dan berbobot.
        """
        NS = _NS_pyrenth
        # lengan bebas menahan keseimbangan (ikut tertarik saat impact)
        lift = 0.25 * math.sin(max(0.0, min(1.0, progress)) * math.pi)
        NS._draw_off_arm(surface, cx, cy, facing, phase, lift=lift)
        grip, tip_hi, _lo, _phi = NS._grip_screen(cx, cy, facing, "attack",
                                                  phase, progress)
        NS._draw_weapon_arm(surface, cx + facing * 16, cy - 2,
                            grip[0], grip[1], facing)
        NS._draw_flaming_sword_line(surface, grip[0], grip[1], tip_hi[0],
                                    tip_hi[1], facing, phase)


    def _draw_r_arms(surface, cx, cy, facing, phase, progress):
        """R — INFERNAL BLADE: ARK yang sama, bilah lebih besar."""
        NS = _NS_pyrenth
        NS._draw_off_arm(surface, cx, cy, facing, phase, lift=0.35)
        grip, tip_hi, _lo, _phi = NS._grip_screen(cx, cy, facing, "r_cast",
                                                  phase, progress)
        NS._draw_weapon_arm(surface, cx + facing * 16, cy - 2,
                            grip[0], grip[1], facing)
        NS._draw_flaming_sword_line(surface, grip[0], grip[1], tip_hi[0],
                                    tip_hi[1], facing, phase, size=1.3)


    def _draw_q_cast_arms(surface, cx, cy, facing, phase):
        """Q — DOOM: bilah MENUDING ke target, cakar bebas mengepal."""
        NS = _NS_pyrenth
        NS._draw_off_arm(surface, cx, cy, facing, phase, lift=0.15)
        grip, tip_hi, _lo, _phi = NS._grip_screen(cx, cy, facing, "q_cast",
                                                  phase, 0.0)
        NS._draw_weapon_arm(surface, cx + facing * 16, cy - 2,
                            grip[0], grip[1], facing)
        NS._draw_flaming_sword_line(surface, grip[0], grip[1], tip_hi[0],
                                    tip_hi[1], facing, phase)
        # muatan doom di ujung bilah
        pulse = math.sin(phase * 4) * 0.3 + 0.7
        r = int(6 * pulse)
        tipx, tipy = int(tip_hi[0]), int(tip_hi[1])
        NS._aacircle(surface, (*NS.PALETTE["fire_darkest"], 150),
                     (tipx, tipy), r + 4)
        NS._aacircle(surface, NS.PALETTE["fire_mid"], (tipx, tipy), r + 2)
        NS._aacircle(surface, NS.PALETTE["fire_bright"], (tipx, tipy), r)
        NS._aacircle(surface, NS.PALETTE["fire_hot"], (tipx, tipy),
                     max(1, r - 2))
        NS._aacircle(surface, NS.PALETTE["fire_glow"], (tipx, tipy),
                     max(1, r - 4))


    def _draw_w_cast_arms(surface, cx, cy, facing, phase, progress):
        """W — DEVOUR: cakar depan MENJULUR menyedot jiwa."""
        NS = _NS_pyrenth
        # bilah turun ke sisi belakang (tangan senjata tidak menganggur)
        grip, tip_hi, _lo, _phi = NS._grip_screen(cx, cy, -facing, "w_cast",
                                                  phase, 0.0)
        NS._draw_weapon_arm(surface, cx - facing * 16, cy - 2,
                            grip[0], grip[1], -facing)
        NS._draw_flaming_sword_line(surface, grip[0], grip[1], tip_hi[0],
                                    tip_hi[1], -facing, phase)

        # cakar depan menjulur — jangkauan berdenyut mengikuti sedotan
        reach = 15 + math.sin(max(0.0, min(1.0, progress)) * math.pi) * 5
        fs_x = cx + facing * 16
        fs_y = cy - 2
        fe_x = fs_x + facing * 10
        fe_y = cy
        fh_x = fs_x + facing * (10 + reach)
        fh_y = cy - 2
        NS._draw_pyr_arm(surface, fs_x, fs_y, fe_x, fe_y)
        NS._draw_pyr_arm(surface, fe_x, fe_y, fh_x, fh_y)
        NS._draw_big_claw(surface, int(fh_x), int(fh_y), facing, phase)


    def _draw_e_cast_arms(surface, cx, cy, facing, phase):
        """E — SCORCHED EARTH: bilah teracung, cakar bebas terangkat."""
        NS = _NS_pyrenth
        NS._draw_off_arm(surface, cx, cy, facing, phase, lift=0.9)
        grip, tip_hi, _lo, _phi = NS._grip_screen(cx, cy, facing, "e_cast",
                                                  phase, 0.0)
        NS._draw_weapon_arm(surface, cx + facing * 16, cy - 2,
                            grip[0], grip[1], facing)
        NS._draw_flaming_sword_line(surface, grip[0], grip[1], tip_hi[0],
                                    tip_hi[1], facing, phase)
        # api terkumpul di kedua tangan
        for hx, hy, sd in ((tip_hi[0], tip_hi[1], 1),
                           (cx - facing * 25, cy - 12, -1)):
            pulse = math.sin(phase * 4 + sd) * 0.3 + 0.7
            r = int(7 * pulse)
            hx, hy = int(hx), int(hy)
            NS._aacircle(surface, (*NS.PALETTE["fire_darkest"], 150),
                         (hx, hy), r + 4)
            NS._aacircle(surface, NS.PALETTE["fire_mid"], (hx, hy), r + 2)
            NS._aacircle(surface, NS.PALETTE["fire_bright"], (hx, hy), r)
            NS._aacircle(surface, NS.PALETTE["fire_hot"], (hx, hy),
                         max(1, r - 2))
            NS._aacircle(surface, NS.PALETTE["fire_glow"], (hx, hy),
                         max(1, r - 4))


    def _draw_pyr_arm(surface, x1, y1, x2, y2):
        """Massive muscular arm."""
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["shadow_deep"], (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 10)
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["skin_darkest"], (x1, y1), (x2, y2), 9)
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["skin_dark"], (x1, y1), (x2, y2), 7)
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["skin_mid"], (x1, y1), (x2, y2), 4)
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["skin_light"], (x1 - 1, y1), (x2 - 1, y2), 1)


    def _draw_claw_hand(surface, x, y, facing):
        """Clawed demon hand."""
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["shadow_deep"], (x + 1, y + 1), 5)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["skin_darkest"], (x, y), 5)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["skin_dark"], (x, y), 4)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["skin_mid"], (x - 1, y - 1), 3)

        # 3 sharp claws pointing forward
        for i, off in enumerate((-2, 0, 2)):
            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_darkest"], [
                (x + off, y + 2),
                (x + off + facing * 5, y + 3 + off // 2),
                (x + off + 1, y + 4),
            ])
            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_mid"], [
                (x + off, y + 2),
                (x + off + facing * 4, y + 3 + off // 2),
                (x + off + 1, y + 4),
            ])
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["horn_light"],
                      (x + off + facing * 5, y + 3 + off // 2), 1)


    def _draw_big_claw(surface, x, y, facing, phase):
        """Extended grasping claw for Devour."""
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["shadow_deep"], (x + 1, y + 1), 8)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["skin_darkest"], (x, y), 7)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["skin_dark"], (x, y), 6)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["skin_mid"], (x - 1, y - 1), 4)

        # 4 huge claws in grasping shape
        for i, angle_off in enumerate((-0.5, -0.15, 0.15, 0.5)):
            angle = angle_off * facing
            tip_x = x + int(math.cos(angle) * 14) * facing
            tip_y = y + int(math.sin(angle) * 8)
            base_x = x + int(math.cos(angle) * 5) * facing
            base_y = y + int(math.sin(angle) * 5)

            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["shadow_deep"], [
                (base_x - 2 + 1, base_y + 1),
                (base_x + 2 + 1, base_y + 1),
                (tip_x + 1, tip_y + 1),
            ])
            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_darkest"], [
                (base_x - 2, base_y),
                (base_x + 2, base_y),
                (tip_x, tip_y),
            ])
            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_dark"], [
                (base_x - 1, base_y),
                (base_x + 1, base_y),
                (tip_x - facing, tip_y - 1),
            ])
            _NS_pyrenth._poly(surface, _NS_pyrenth.PALETTE["horn_mid"], [
                (base_x, base_y),
                (base_x + 1, base_y),
                (tip_x - facing, tip_y - 2),
            ])
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["horn_light"], (tip_x, tip_y), 1)
            # Fire tip
            _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_hot"], 200), (tip_x, tip_y), 2)


    def _draw_flaming_sword(surface, hx, hy, facing, pose, phase):
        """Long flaming sword."""
        if pose == "forward":
            end_x = hx + facing * 28
            end_y = hy
        else:  # down
            end_x = hx + facing * 15
            end_y = hy + 24
        _NS_pyrenth._draw_flaming_sword_line(surface, hx, hy, end_x, end_y, facing, phase)


    def _draw_flaming_sword_angled(surface, hx, hy, facing, angle, phase, size=1.0):
        """Sword at specific angle."""
        sword_len = int(32 * size)
        dx = math.cos(angle) * facing
        dy = math.sin(angle)
        end_x = hx + int(dx * sword_len)
        end_y = hy + int(dy * sword_len)
        _NS_pyrenth._draw_flaming_sword_line(surface, hx, hy, end_x, end_y, facing, phase, size)


    def _draw_flaming_sword_line(surface, hx, hy, end_x, end_y, facing, phase, size=1.0):
        """Sword with handle, guard, blade, and flames."""
        dx = end_x - hx
        dy = end_y - hy
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 1:
            return
        dir_x = dx / dist
        dir_y = dy / dist
        perp_x = -dir_y
        perp_y = dir_x

        # Handle (short section)
        handle_len = int(5 * size)
        hx2 = hx + int(dir_x * handle_len)
        hy2 = hy + int(dir_y * handle_len)
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["shadow_deep"], (hx + 1, hy + 1), (hx2 + 1, hy2 + 1), 4)
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["arm_darkest"], (hx, hy), (hx2, hy2), 4)
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["arm_dark"], (hx, hy), (hx2, hy2), 3)
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["gold_mid"], (hx, hy), (hx2, hy2), 1)

        # Cross-guard
        guard_len = int(5 * size)
        g1_x = hx2 + int(perp_x * guard_len)
        g1_y = hy2 + int(perp_y * guard_len)
        g2_x = hx2 - int(perp_x * guard_len)
        g2_y = hy2 - int(perp_y * guard_len)
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["shadow_deep"], (g1_x + 1, g1_y + 1), (g2_x + 1, g2_y + 1), 5)
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["arm_darkest"], (g1_x, g1_y), (g2_x, g2_y), 4)
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["gold_dark"], (g1_x, g1_y), (g2_x, g2_y), 3)
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["gold_mid"], (g1_x, g1_y), (g2_x, g2_y), 2)
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["gold_light"], (g1_x, g1_y), (g2_x, g2_y), 1)
        # Guard tips with fire gems
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_bright"], (g1_x, g1_y), 2)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_hot"], (g1_x, g1_y), 1)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_bright"], (g2_x, g2_y), 2)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_hot"], (g2_x, g2_y), 1)

        # Blade
        blade_start_x = hx2
        blade_start_y = hy2
        blade_end_x = end_x
        blade_end_y = end_y

        # Shadow
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["shadow_deep"],
                (blade_start_x + 1, blade_start_y + 1),
                (blade_end_x + 1, blade_end_y + 1), int(5 * size))

        # Blade layers - dark metal core with fire
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["arm_darkest"],
                (blade_start_x, blade_start_y), (blade_end_x, blade_end_y), int(5 * size))
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["arm_dark"],
                (blade_start_x, blade_start_y), (blade_end_x, blade_end_y), int(4 * size))
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["fire_dark"],
                (blade_start_x, blade_start_y), (blade_end_x, blade_end_y), int(3 * size))
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["fire_mid"],
                (blade_start_x, blade_start_y), (blade_end_x, blade_end_y), int(2 * size))
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["fire_bright"],
                (blade_start_x, blade_start_y), (blade_end_x, blade_end_y), 1)

        # Bright edge glow
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["fire_hot"],
                (blade_start_x + int(perp_x), blade_start_y + int(perp_y)),
                (blade_end_x + int(perp_x), blade_end_y + int(perp_y)), 1)
        _NS_pyrenth._aaline(surface, _NS_pyrenth.PALETTE["fire_glow"],
                (blade_start_x - int(perp_x), blade_start_y - int(perp_y)),
                (blade_end_x - int(perp_x), blade_end_y - int(perp_y)), 1)

        # Sharp bright tip
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_white"], (blade_end_x, blade_end_y), 2)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_hot"], (blade_end_x, blade_end_y), 1)

        # FLAMES rising from blade
        for i in range(int(7 * size)):
            t = 0.15 + (i / max(1, int(7 * size))) * 0.75
            base_x = int(blade_start_x + (blade_end_x - blade_start_x) * t)
            base_y = int(blade_start_y + (blade_end_y - blade_start_y) * t)
            flame_off = int(math.sin(phase * 3 + i) * 2)
            flame_x = base_x + int(perp_x * flame_off)
            flame_y = base_y + int(perp_y * flame_off)
            flame_size = int((3 + (i % 2)) * size)

            _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_dark"], 200),
                      (flame_x, flame_y), flame_size + 1)
            _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_bright"], 220),
                      (flame_x, flame_y), flame_size)
            _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_hot"], 240),
                      (flame_x, flame_y), max(1, flame_size - 1))
            _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_glow"], 255),
                      (flame_x, flame_y), max(1, flame_size - 2))

        # Overall blade glow
        mid_x = (blade_start_x + blade_end_x) // 2
        mid_y = (blade_start_y + blade_end_y) // 2
        _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_bright"], 100),
                  (mid_x, mid_y), int(dist * 0.5))
        _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_hot"], 80),
                  (mid_x, mid_y), int(dist * 0.3))


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_hellfire_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Hellfire wisps beneath boss."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((160, 48), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(40, 3, -4):
            alpha = int((40 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_pyrenth.PALETTE["fire_darkest"], min(255, alpha)),
                    (80 - radius * 2, 24 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 80, cy - 12))

        # Rising flames
        for i, offset in enumerate((-26, -12, 8, 24)):
            t = (phase * 0.6 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 30)
            alpha = max(0, min(255, int(230 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_darkest"], alpha), (sx, sy), 6)
            _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_dark"], alpha), (sx, sy - 1), 4)
            _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_bright"], alpha), (sx, sy - 2), 3)
            _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_hot"], alpha), (sx, sy - 3), 2)
            _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_glow"], alpha), (sx, sy - 3), 1)

        # Embers orbiting
        for i in range(8):
            angle = phase * 0.9 + i * math.pi * 2 / 8
            r = 26 + int(math.sin(phase + i * 1.3) * 6)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 10)
            _NS_pyrenth._draw_ember(surface, sx, sy, 2, 220)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = max(0, 160 - i * 25)
                _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_dark"], alpha),
                          (sx, sy), max(2, 6 - i))
                _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_bright"], alpha),
                          (sx, sy), max(1, 4 - i))
                _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_hot"], alpha),
                          (sx, sy), max(1, 2 - i))


    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((130, 24), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 14)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (12 - radius, 12 - radius, 106 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_pyrenth.PALETTE["fire_dark"], 80), (10, 6, 110, 12))
        surface.blit(shadow, (x - 65, y - 12))


    def _draw_hellfire_aura(surface, x, y, phase, active_skill):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.6 if active_skill in ("q", "w", "e", "r") else 1.0
        aura = pygame.Surface((240, 220), pygame.SRCALPHA)
        for radius in range(100, 5, -4):
            alpha = int((100 - radius) * 1.3 * pulse * strength)
            if alpha > 0:
                _NS_pyrenth._aacircle(aura, (*_NS_pyrenth.PALETTE["fire_darkest"], min(255, alpha)),
                          (120, 110), radius)
        surface.blit(aura, (x - 120, y - 110))


    def _draw_ground_runes(surface, x, y, phase, active_skill):
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_pyrenth.PALETTE["fire_dark"], 160),
                            (5, 10, 150, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_pyrenth.PALETTE["fire_mid"], 190),
                            (20, 14, 120, 22), 2)

        for i in range(10):
            angle = phase * 0.15 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 38)
            y1 = 25 + int(math.sin(angle) * 9)
            x2 = 80 + int(math.cos(angle) * 70)
            y2 = 25 + int(math.sin(angle) * 13)
            pygame.draw.line(ring, (*_NS_pyrenth.PALETTE["fire_hot"], 180),
                             (x1, y1), (x2, y2), 1)

        if active_skill:
            pygame.draw.ellipse(ring, (*_NS_pyrenth.PALETTE["fire_glow"], int(80 * pulse)),
                                (15, 8, 130, 34), 1)

        # Center emblem (demon symbol)
        for i in range(6):
            angle = i * math.pi / 3
            ex1 = 80 + int(math.cos(angle) * 6)
            ey1 = 25 + int(math.sin(angle) * 2)
            ex2 = 80 + int(math.cos(angle) * 10)
            ey2 = 25 + int(math.sin(angle) * 3)
            pygame.draw.line(ring, (*_NS_pyrenth.PALETTE["fire_hot"], 200),
                             (ex1, ey1), (ex2, ey2), 1)

        surface.blit(ring, (x - 80, y - 25))


    def _draw_sword_swing_arc(surface, x, y, facing, progress):
        """FALLBACK canvas: pita sabetan yang MENGIKUTI BLADE_ARC.

        Dipakai hanya saat ``heroes/pyrenth_fx`` tidak tersedia.  Bedanya
        dengan versi lama: titik-titiknya diambil dari ARK yang sama yang
        dipakai bilah, jadi pita selalu menempel pada mata pedang alih-
        alih menjadi busur hias yang berdiri sendiri.
        """
        NS = _NS_pyrenth
        if progress < 0.24 or progress > 0.82:
            return
        if progress < 0.52:
            visibility = (progress - 0.24) / 0.28
        else:
            visibility = 1.0 - (progress - 0.52) / 0.30
        visibility = max(0.0, min(1.0, visibility))
        if visibility <= 0.02:
            return

        # histori 10 pose ARK di BELAKANG progress sekarang
        samples = []
        for i in range(10):
            p = progress - i * 0.026
            if p < 0.0:
                break
            grip, tip_hi, _lo, _phi = NS.blade_geometry(facing, "attack",
                                                        0.0, p)
            samples.append(((x + grip[0], y + grip[1]),
                            (x + tip_hi[0], y + tip_hi[1])))
        if len(samples) < 3:
            return

        n = len(samples)
        for i in range(n - 1):
            f = (1.0 - i / float(n - 1)) * visibility
            if f <= 0.03:
                continue
            (r0, t0) = samples[i]
            (r1, t1) = samples[i + 1]
            # kuadrilateral hanya menutup bagian TERLUAR bilah supaya
            # tidak menelan siluet karakter
            k = 0.58
            i0 = (r0[0] + (t0[0] - r0[0]) * k, r0[1] + (t0[1] - r0[1]) * k)
            i1 = (r1[0] + (t1[0] - r1[0]) * k, r1[1] + (t1[1] - r1[1]) * k)
            NS._poly(surface, (*NS.PALETTE["fire_darkest"], int(70 * f)),
                     [t0, t1, i1, i0])
            NS._poly(surface, (*NS.PALETTE["fire_mid"], int(120 * f)),
                     [t0, t1,
                      (i1[0] + (t1[0] - i1[0]) * 0.45,
                       i1[1] + (t1[1] - i1[1]) * 0.45),
                      (i0[0] + (t0[0] - i0[0]) * 0.45,
                       i0[1] + (t0[1] - i0[1]) * 0.45)])
            NS._aaline(surface, (*NS.PALETTE["fire_bright"], int(235 * f)),
                       t0, t1, 2)
            NS._aaline(surface, (*NS.PALETTE["fire_glow"], int(210 * f)),
                       t0, t1, 1)


    def _draw_swing_impact(surface, x, y, facing, progress):
        """FALLBACK canvas: kilat benturan di UJUNG BILAH saat impact."""
        NS = _NS_pyrenth
        lo, hi = NS.ATTACK_ACTIVE_WINDOW
        if progress < lo or progress > hi + 0.2:
            return
        t = (progress - lo) / max(0.01, (hi + 0.2) - lo)
        intensity = math.sin(max(0.0, min(1.0, t)) * math.pi)
        if intensity <= 0.02:
            return

        _grip, tip_hi, _lo2, _phi = NS.blade_geometry(facing, "attack", 0.0,
                                                      progress)
        impact_x = int(x + tip_hi[0])
        impact_y = int(y + tip_hi[1])
        alpha = int(240 * intensity)
        radius = int(10 + intensity * 22)

        NS._aacircle(surface, (*NS.PALETTE["fire_dark"], alpha // 2),
                     (impact_x, impact_y), radius + 5)
        NS._aacircle(surface, (*NS.PALETTE["fire_bright"], alpha),
                     (impact_x, impact_y), radius, 3)
        NS._aacircle(surface, (*NS.PALETTE["fire_hot"], alpha),
                     (impact_x, impact_y), max(1, radius - 6), 2)
        NS._aacircle(surface, (*NS.PALETTE["fire_glow"], alpha),
                     (impact_x, impact_y), max(1, radius - 12))
        for i in range(12):
            angle = i * math.pi / 6 + progress * 3
            dx = impact_x + int(math.cos(angle) * radius * 1.3)
            dy = impact_y + int(math.sin(angle) * radius * 0.9)
            NS._draw_ember(surface, dx, dy, 2, alpha)


    # ===================================================================
    # SKILL E: SCORCHED EARTH
    # ===================================================================
    def _draw_scorched_earth_ground(surface, boss, x, y, timer, phase):
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        radius = int(60 + progress * 20)
        _NS_pyrenth._ellipse(surface, (*_NS_pyrenth.PALETTE["fire_darkest"], int(200 * pulse)),
                 (x - radius, y + 45 - radius // 3, radius * 2, radius // 1.5), 3)
        _NS_pyrenth._ellipse(surface, (*_NS_pyrenth.PALETTE["fire_dark"], int(180 * pulse)),
                 (x - radius + 5, y + 45 - radius // 3 + 2,
                  radius * 2 - 10, radius // 1.5 - 4), 2)


    def _draw_scorched_earth(surface, boss, x, y, timer, phase):
        """Fire spikes rising around self."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.15:
            return

        # Erupt phase
        if progress < 0.5:
            erupt_t = (progress - 0.15) / 0.35
        else:
            erupt_t = 1.0 - (progress - 0.7) / 0.3 if progress > 0.7 else 1.0
        erupt_t = max(0.0, min(1.0, erupt_t))

        # Outer ring of fire spikes
        ring_r = 60
        num_spikes = 14
        for i in range(num_spikes):
            angle = i * math.pi * 2 / num_spikes + phase * 0.05
            sx = x + int(math.cos(angle) * ring_r)
            sy = y + 45 + int(math.sin(angle) * ring_r * 0.5)
            spike_h = int(30 * erupt_t) + (i % 3) * 3

            _NS_pyrenth._draw_fire_spike(surface, sx, sy, sy - spike_h, 5, 250, phase)

        # Inner ring
        inner_r = 40
        for i in range(10):
            angle = (i + 0.5) * math.pi * 2 / 10 + phase * 0.1
            sx = x + int(math.cos(angle) * inner_r)
            sy = y + 45 + int(math.sin(angle) * inner_r * 0.5)
            spike_h = int(22 * erupt_t)
            _NS_pyrenth._draw_fire_spike(surface, sx, sy, sy - spike_h, 4, 240, phase)

        # Rising embers everywhere
        for i in range(15):
            angle = phase * 1.5 + i * math.pi / 7.5
            r = 30 + int(math.sin(phase * 2 + i) * 25)
            t_up = (phase * 0.5 + i * 0.06) % 1.0
            sx = x + int(math.cos(angle) * r)
            sy = y + 45 - int(t_up * 40)
            _NS_pyrenth._draw_ember(surface, sx, sy, 2, int(255 * (1 - t_up) * erupt_t))


    # ===================================================================
    # SKILL W: DEVOUR
    # ===================================================================
    def _draw_devour_effect(surface, boss, x, y, timer, pulse_phase):
        """Devour - fire gathering at reach hand + target consumed."""
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))

        tx, ty = _NS_pyrenth._target_position(boss, x, y)

        # Line of fire particles from boss to target
        if progress > 0.2:
            sx = x + 40 * boss.direction
            sy = y - 5

            dx = tx - sx
            dy = ty - sy
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 1:
                return
            dir_x = dx / dist
            dir_y = dy / dist

            # Fire pulling from target to boss (devouring effect)
            for i in range(int(dist / 6)):
                t = 1.0 - ((i / max(1, int(dist / 6))) - (progress * 0.5)) % 1.0
                px = int(sx + dir_x * dist * t)
                py = int(sy + dir_y * dist * t)
                alpha = int(200 * (1 - abs(t - 0.5) * 2))
                _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_bright"], alpha), (px, py), 4)
                _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_hot"], alpha), (px, py), 2)
                _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_glow"], alpha), (px, py), 1)

        # Fire consuming at target
        if progress > 0.3:
            consume_t = min(1.0, (progress - 0.3) / 0.5)
            radius = int(20 * consume_t)
            pulse = math.sin(pulse_phase * 4) * 0.3 + 0.7

            _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_dark"], int(200 * pulse)),
                      (tx, ty), radius + 4)
            _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_bright"], int(230 * pulse)),
                      (tx, ty), radius)
            _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_hot"], int(255 * pulse)),
                      (tx, ty), max(1, radius - 4))
            _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_glow"], 255),
                      (tx, ty), max(1, radius - 8))

            # Rising flames from target
            for i in range(4):
                t = (pulse_phase * 0.6 + i * 0.25) % 1.0
                fx = tx + int(math.sin(pulse_phase * 3 + i) * 4)
                fy = ty - int(t * 25)
                fa = int(255 * (1 - t) * consume_t)
                _NS_pyrenth._draw_ember(surface, fx, fy, 2, fa)


    # ===================================================================
    # OVERLAY DEBUG RENDERER (DEBUG_CHARACTER = True)
    # ===================================================================
    _DBG_FONT = None

    @staticmethod
    def _dbg_font():
        NS = _NS_pyrenth
        if NS._DBG_FONT is None:
            try:
                if not pygame.font.get_init():
                    pygame.font.init()
                NS._DBG_FONT = pygame.font.SysFont("consolas,monospace", 11)
            except Exception:                          # pragma: no cover
                NS._DBG_FONT = False
        return NS._DBG_FONT or None

    @staticmethod
    def _draw_pyrenth_debug(surface, boss, x, y):
        """Hitbox bilah, hurtbox, attack range, radius skill, state,
        FPS, jumlah partikel, timer serangan — dari controller."""
        NS = _NS_pyrenth
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        ap = float(getattr(boss, "_pyr_attack_progress", 0.0) or 0.0)
        lo, hi = NS.ATTACK_ACTIVE_WINDOW
        active = bool(getattr(boss, "_pyr_hit_window", False))
        action = getattr(boss, "_pyr_pose_action", "idle")
        phase = float(getattr(boss, "_pyr_phase",
                              getattr(boss, "pulse", 0.0)))

        # jangkauan serangan (elips tanah)
        rng = float(getattr(boss, "attack_range",
                            getattr(boss, "range", 55)) or 55)
        rng = rng / max(0.05, scale)
        pygame.draw.ellipse(surface, (90, 200, 255),
                            pygame.Rect(int(x - rng),
                                        int(y + NS.GROUND_DY - rng * 0.4),
                                        int(rng * 2), int(rng * 0.8)), 1)
        # jangkauan tebasan pedang api
        mr = NS.MELEE_REACH / max(0.05, scale)
        pygame.draw.ellipse(surface, (255, 160, 80),
                            pygame.Rect(int(x - mr),
                                        int(y + NS.GROUND_DY - mr * 0.4),
                                        int(mr * 2), int(mr * 0.8)), 1)
        # radius skill aktif
        skill = getattr(boss, "active_skill", None)
        if skill in NS.SKILL_RADIUS:
            rr = NS.SKILL_RADIUS[skill] / max(0.05, scale)
            pygame.draw.ellipse(surface, (255, 120, 120),
                                pygame.Rect(int(x - rr),
                                            int(y + NS.GROUND_DY
                                                      - rr * 0.4),
                                            int(rr * 2), int(rr * 0.8)), 1)
        # hurtbox
        pygame.draw.rect(surface, (70, 240, 120),
                         pygame.Rect(int(x - 26), int(y - 56), 52, 92), 1)
        # hitbox bilah (grip -> tip)
        grip, tip_hi, tip_lo, _phi = NS.blade_geometry(facing, action,
                                                       phase, ap)
        col = (255, 80, 80) if active else (150, 150, 160)
        pygame.draw.line(surface, col,
                         (int(x + tip_lo[0]), int(y + tip_lo[1])),
                         (int(x + tip_hi[0]), int(y + tip_hi[1])),
                         2 if active else 1)
        pygame.draw.circle(surface, col,
                           (int(x + tip_hi[0]), int(y + tip_hi[1])), 13, 1)
        pygame.draw.circle(surface, (240, 240, 90),
                           (int(x + grip[0]), int(y + grip[1])), 2, 1)
        # proyektil canvas fallback
        for ch in getattr(boss, "_pyr_chains", ()) or ():
            pygame.draw.line(surface, (255, 220, 90),
                             (int(ch.sx), int(ch.sy)),
                             (int(ch.tx), int(ch.ty)), 1)
        for arc in getattr(boss, "_pyr_arcs", ()) or ():
            pygame.draw.circle(surface, (255, 220, 90),
                               (int(arc.x), int(arc.y)),
                               max(2, int(getattr(arc, "radius", 10))), 1)

        font = NS._dbg_font()
        if font is None:
            return
        parts = 0
        proj = (len(getattr(boss, "_pyr_chains", ()) or ())
                + len(getattr(boss, "_pyr_arcs", ()) or ()))
        try:
            mod = NS._live_module()
            if mod is not None:
                st = mod.stats()
                parts = st.get("particles", 0)
                proj += st.get("projectiles", 0)
        except Exception:                              # pragma: no cover
            pass
        dt = float(getattr(boss, "_pyr_dt", 1.0 / 60.0)) or (1.0 / 60.0)
        lines = [
            "PYRENTH [renderer debug]",
            "state %s <- %s (p%d)" % (
                getattr(boss, "_pyr_state", "?"),
                getattr(boss, "_pyr_state_prev", "-"),
                int(getattr(boss, "_pyr_state_priority", 0))),
            "pose %s  dt %.4f  fps %.0f" % (action, dt, 1.0 / max(1e-4, dt)),
            "attack %.2f %s%s" % (ap,
                                  getattr(boss, "_pyr_attack_phase", "NONE"),
                                  "  <HIT>" if active else ""),
            "window %.2f-%.2f  impact %.2f" % (lo, hi,
                                               NS.ATTACK_IMPACT_FRAME),
            "swing MELEE  timer %s cd %s" % (
                getattr(boss, "timer", "-"),
                getattr(boss, "attack_cooldown", "-")),
            "skill %s t%s  live %s" % (
                skill or "-", getattr(boss, "active_skill_timer", "-"),
                "ON" if getattr(boss, "_pyr_suppress_canvas_fx", False)
                else "off"),
            "part %d  proj %d" % (parts, proj),
        ]
        pad = 4
        w = max(font.size(t)[0] for t in lines) + pad * 2
        h = len(lines) * 13 + pad * 2
        box = pygame.Surface((w, h), pygame.SRCALPHA)
        box.fill((10, 8, 12, 190))
        pygame.draw.rect(box, (255, 150, 90, 200), box.get_rect(), 1)
        for i, t in enumerate(lines):
            box.blit(font.render(t, True, (255, 224, 190)),
                     (pad, pad + i * 13))
        surface.blit(box, (int(x) - w - 46, int(y) - 100))

    # ===================================================================
    # Backward compatible alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_pyrenth.draw_pyrenth(surface, boss, x, y)



# ====================================================================
# VOKRAHN
# ====================================================================
class _NS_vokrahn:
    """Namespace vokrahn - PIXEL MASTERWORK v2 + COMBAT FX v3.

    Rewrite penuh renderer + sistem tempur **VOKRAHN, THE HARBINGER OF
    CHAOS** (mini-boss level 4) mengikuti standar v3 Combat FX (lihat
    docs/AUDIT_ULANG_DARI_AWAL.md).

    Pembagian kerja:

      RENDERER (file ini)                  LAPISAN HIDUP (heroes/vokrahn_fx.py)
      -----------------------------------  ------------------------------------------
      rig ksatria gelap + kuda jelaga +    trail ayunan greatsword (histori nyata)
        pedang api, 100% prosedural        particle system (bara/asap/serpihan)
      palette + outline + rim light        Chaos Bolt / Chaos Brand modular
      ANIMATION CONTROLLER (state,         (SPAUN->TRAVEL->TRAIL->HIT->IMPACT)
        fase, hit window, delta time)      IMPACT FX + hit-stop + screen shake
      ark ayunan pedang (SWORD_ARC)        SkillFX q/w/e/r lifecycle penuh
      telegraph tanah q/w/e/r              overlay DEBUG_CHARACTER
      fallback penuh saat modul FX         -- semua di luar cache sprite --
        tidak tersedia

    100% PROSEDURAL: tidak ada PNG / JPG / GIF / sprite-sheet, dan tidak
    ada pemuat gambar eksternal apa pun. Semua bentuk dari
    pygame.Surface + pygame.draw + pygame.transform + pygame.mask.
    """

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    #: flag debug global (hitbox/hurtbox/range/state/frame/FPS/partikel/
    #: skill state/attack timer).  Diubah dari luar:
    #:   ``bosses.level4._NS_vokrahn.DEBUG_CHARACTER = True``
    DEBUG_CHARACTER = False

    # ── STATE LAPISAN HIDUP ───────────────────────────────────────
    _LIVE_MOD = None
    _last_rig = None                 # rig terakhir (untuk afterimage FX)
    _last_rig_off = (0, 0)
    _body_buf = None
    RIG_W, RIG_H = 320, 240
    RIG_OX, RIG_OY = 160, 140
    GROUND_DY = 58

    # ── KONSTANTA TEMPUR (dikontrakkan dengan AI di base_boss) ──
    #: durasi skill dalam FRAME engine (active_skill_timer) — SAMA PERSIS
    #: dengan yang di-set ``_cast_vokrahn_*`` di bosses/base_boss.py.
    SKILL_DUR = {"q": 50, "w": 60, "e": 50, "r": 80}
    #: radius damage DUNIA (px) — sama dengan cek jarak di AI.
    SKILL_RADIUS = {"q": 250, "w": 220, "e": 150, "r": 220}
    #: jangkauan tebasan greatsword (px dunia) untuk overlay debug & tes.
    MELEE_REACH = 96

    #: jendela hit aktif (progress 0..1) + frame impact. ``0.52`` dipakai
    #: renderer (puncak ayunan SWORD_ARC) DAN lapisan hidup (momen impact)
    #: — satu angka, satu detak.
    ATTACK_ACTIVE_WINDOW = (0.38, 0.62)
    ATTACK_IMPACT_FRAME = 0.52

    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, 0.12),
        ("WINDUP",       0.12, 0.30),
        ("SWING",        0.30, 0.50),
        ("IMPACT",       0.50, 0.62),
        ("FOLLOW",       0.62, 0.82),
        ("RECOVERY",     0.82, 1.00),
    )

    #: prioritas state (besar menang) — dibaca controller + debug + FX.
    ANIM_STATES = {
        "IDLE": 0, "WALK": 10, "RUN": 15, "CHARGE": 30, "CAST": 35,
        "ATTACK": 40, "SWING": 45, "SKILL": 50, "SPECIAL": 55,
        "HIT": 60, "HURT": 65, "DEATH": 100,
    }

    # ── ARK PEDANG: SATU SUMBER KE BENARAN ────────────────────────
    # (t0, t1, phi0, phi1, ease).  Konvensi ruang layar (y ke bawah):
    #   tip = grip + (facing * cos(phi) * L, -sin(phi) * L)
    # guard phi = 0.96 (rad, ~55deg ke depan-atas).  Ayunan: guard ->
    # wind-up ke atas-belakang (2.18-2.88) -> tebasan cepat ke bawah
    # (2.88 -> -1.31, melewati 0.52 = IMPACT) -> follow-through ->
    # kembali ke guard.  Lapisan hidup heroes/vokrahn_fx.py menyimpan
    # tabel cadangan IDENTIK dan selalu membaca fungsi di sini bila
    # tersedia — tidak ada dua tabel yang bisa menyimpang.
    SWORD_ARC = (
        (0.00, 0.12,  0.96,  2.18, "out"),
        (0.12, 0.30,  2.18,  2.88, "io"),
        (0.30, 0.50,  2.88, -1.31, "oc"),
        (0.50, 0.62, -1.31, -1.05, "hold"),
        (0.62, 0.82, -1.05, -0.44, "io"),
        (0.82, 1.00, -0.44,  0.96, "io"),
    )
    _SWORD_HALF = 48.0           # panjang bilah (px, skala layar 1)
    _GRIP = (26.0, -8.7)         # grip diam (relatif jangkar badan)

    PALETTE = {
        # Armor - dark metal with red accents
        "arm_darkest":    (5,    3,   6),
        "arm_dark":       (22,  15,  22),
        "arm_mid":        (48,  35,  42),
        "arm_light":      (85,  65,  72),
        "arm_high":       (140, 110, 115),
        "arm_shine":      (200, 175, 175),

        # Red trim / crimson
        "red_darkest":    (25,   5,   5),
        "red_dark":       (75,  10,  10),
        "red_mid":        (150, 20,  15),
        "red_bright":     (220, 45,  30),
        "red_hot":        (255, 90,  50),
        "red_glow":       (255, 145, 100),

        # Fire orange (sword blade)
        "fire_darkest":   (55,  10,   5),
        "fire_dark":      (135, 25,   8),
        "fire_mid":       (215, 65,  15),
        "fire_bright":    (255, 120, 30),
        "fire_hot":       (255, 175, 60),
        "fire_glow":      (255, 220, 130),
        "fire_white":     (255, 250, 210),

        # Cape / cloth (dark red)
        "cape_darkest":   (18,   5,   8),
        "cape_dark":      (50,  12,  15),
        "cape_mid":       (95,  22,  25),
        "cape_light":     (150, 40,  35),

        # Horse - dark charcoal with red mane
        "horse_darkest":  (5,    5,   8),
        "horse_dark":     (20,  18,  22),
        "horse_mid":      (45,  40,  45),
        "horse_light":    (80,  72,  75),
        "horse_high":     (125, 115, 115),

        # Horse mane/tail - red
        "mane_darkest":   (30,   5,   3),
        "mane_dark":      (85,  15,  10),
        "mane_mid":       (155, 30,  15),
        "mane_bright":    (220, 55,  25),
        "mane_hot":       (255, 110, 50),

        # Metal (weapons, ornaments)
        "metal_darkest":  (12,  10,  15),
        "metal_dark":     (35,  32,  40),
        "metal_mid":      (75,  72,  85),
        "metal_light":    (130, 128, 145),
        "metal_shine":    (185, 185, 200),
        "metal_edge":     (240, 240, 250),

        # Gold accents (small)
        "gold_dark":      (85,  55,  15),
        "gold_mid":       (165, 120, 35),
        "gold_light":     (225, 180, 75),

        # Eyes - glowing red
        "eye_dark":       (60,   5,   5),
        "eye_bright":     (255, 60,  30),
        "eye_hot":        (255, 180, 130),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (3,   2,   3),
        "white":          (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vokrahn._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_vokrahn.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_vokrahn._clamp(color)
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
        color = _NS_vokrahn._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)


    def _ellipse(surface, color, rect, width=0):
        color = _NS_vokrahn._clamp(color)
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
        color = _NS_vokrahn._clamp(color)
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
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # DENGAN kompensasi scale. Hero di-render ke canvas
            # offscreen lalu di-scale saat blit (heroes/__init__.py),
            # jadi titik canvas harus = (delta dunia)/scale supaya
            # beam/proyektil mendarat TEPAT di target setelah blit.
            # Boss yang digambar langsung di layar tidak terpengaruh
            # (scale = 1).
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return int(x + 200 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Chaos spike helpers
    # ---------------------------------------------------------------------------
    def _draw_chaos_spike(surface, cx, base_y, tip_y, width=4, alpha=255):
        """Red chaos spike rising from ground."""
        _NS_vokrahn._poly(surface, (*_NS_vokrahn.PALETTE["shadow_deep"], alpha), [
            (cx - width + 1, base_y + 1),
            (cx + width + 1, base_y + 1),
            (cx + 1, tip_y + 1),
        ])
        _NS_vokrahn._poly(surface, (*_NS_vokrahn.PALETTE["arm_darkest"], alpha), [
            (cx - width, base_y),
            (cx + width, base_y),
            (cx, tip_y),
        ])
        _NS_vokrahn._poly(surface, (*_NS_vokrahn.PALETTE["red_darkest"], alpha), [
            (cx - width + 1, base_y - 1),
            (cx + width - 1, base_y - 1),
            (cx, tip_y + 2),
        ])
        _NS_vokrahn._poly(surface, (*_NS_vokrahn.PALETTE["red_dark"], alpha), [
            (cx - width + 2, base_y - 1),
            (cx + width - 2, base_y - 1),
            (cx, tip_y + 4),
        ])
        _NS_vokrahn._poly(surface, (*_NS_vokrahn.PALETTE["red_mid"], alpha), [
            (cx - width + 3, base_y - 1),
            (cx + width - 3, base_y - 1),
            (cx, tip_y + 6),
        ])
        _NS_vokrahn._poly(surface, (*_NS_vokrahn.PALETTE["red_bright"], alpha), [
            (cx - 1, base_y),
            (cx + 1, base_y),
            (cx, tip_y + 8),
        ])
        _NS_vokrahn._aaline(surface, (*_NS_vokrahn.PALETTE["red_hot"], alpha),
                (cx, base_y - 2), (cx, tip_y + 3), 1)
        _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_glow"], alpha), (cx, tip_y + 1), 1)


    def _draw_ember(surface, cx, cy, size=2, alpha=255):
        _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["fire_dark"], alpha), (cx, cy), size + 1)
        _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["fire_bright"], alpha), (cx, cy), size)
        _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["fire_hot"], alpha), (cx, cy), max(1, size - 1))
        _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["fire_glow"], min(255, alpha)), (cx, cy), 1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM
    # ---------------------------------------------------------------------------
    class ChaosBolt:
        """Q - Red arrow-like chaos projectile."""
        def __init__(self, sx, sy, tx, ty, speed=8.0):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.trail = []
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)

        def update(self):
            if not self.alive:
                return
            self.age += 1
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 14:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            # Long fire trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(50 + i * 14)
                r = max(1, 5 - (len(self.trail) - i))
                _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["fire_darkest"], alpha), (tx, ty), r + 2)
                _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_bright"], alpha), (tx, ty), r)
                _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_hot"], alpha), (tx, ty), max(1, r - 1))
                _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["fire_glow"], alpha // 2), (tx, ty), max(1, r - 2))

            if self.alive:
                px, py = int(self.x), int(self.y)
                dx = math.cos(self.angle)
                dy = math.sin(self.angle)
                perp_x = -dy
                perp_y = dx

                # Arrow-like shape (elongated)
                arrow = [
                    (px + int(dx * 14), py + int(dy * 14)),  # tip
                    (px + int(perp_x * 4), py + int(perp_y * 4)),
                    (px + int(-dx * 6 + perp_x * 2), py + int(-dy * 6 + perp_y * 2)),
                    (px + int(-dx * 4), py + int(-dy * 4)),
                    (px + int(-dx * 6 - perp_x * 2), py + int(-dy * 6 - perp_y * 2)),
                    (px - int(perp_x * 4), py - int(perp_y * 4)),
                ]
                _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["shadow_deep"],
                      [(p[0] + 1, p[1] + 1) for p in arrow])
                _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["red_darkest"], arrow)
                _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["red_dark"], [
                    (px + int(dx * 13), py + int(dy * 13)),
                    (px + int(perp_x * 3), py + int(perp_y * 3)),
                    (px + int(-dx * 5), py + int(-dy * 5)),
                    (px - int(perp_x * 3), py - int(perp_y * 3)),
                ])
                _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["red_mid"], [
                    (px + int(dx * 12), py + int(dy * 12)),
                    (px + int(perp_x * 2), py + int(perp_y * 2)),
                    (px + int(-dx * 4), py + int(-dy * 4)),
                    (px - int(perp_x * 2), py - int(perp_y * 2)),
                ])
                _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["red_bright"], [
                    (px + int(dx * 10), py + int(dy * 10)),
                    (px + int(perp_x), py + int(perp_y)),
                    (px + int(-dx * 3), py + int(-dy * 3)),
                    (px - int(perp_x), py - int(perp_y)),
                ])
                # Sharp glowing line down center
                _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["red_hot"],
                        (px + int(dx * 12), py + int(dy * 12)),
                        (px - int(dx * 4), py - int(dy * 4)), 1)
                _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["fire_glow"],
                        (px + int(dx * 10), py + int(dy * 10)),
                        (px - int(dx * 2), py - int(dy * 2)), 1)

                # Glow
                _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_bright"], 120), (px, py), 12)
                _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["fire_hot"], 80), (px, py), 8)

                # Trailing fire particles
                for i in range(3):
                    a = phase * 4 + i * math.pi * 2 / 3
                    ex = px + int(math.cos(a) * 6) - int(dx * 8)
                    ey = py + int(math.sin(a) * 4) - int(dy * 8)
                    _NS_vokrahn._draw_ember(surface, ex, ey, 2, 200)


    class ImpactBurst:
        """Explosion burst — e.g., at Chaos Strike or Chaos Bolt impact."""
        def __init__(self, x, y, life=25, size=25):
            self.x = x
            self.y = y
            self.life = life
            self.age = 0
            self.size = size
            self.alive = True

        def update(self):
            self.age += 1
            if self.age >= self.life:
                self.alive = False

        def draw(self, surface, phase):
            t = self.age / self.life
            if t < 0.5:
                radius = int(self.size * (t / 0.5))
                alpha = int(255 * (t / 0.5))
            else:
                radius = self.size
                alpha = int(255 * (1 - (t - 0.5) / 0.5))

            if radius <= 0 or alpha <= 0:
                return

            # Expanding ring
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_dark"], alpha), (self.x, self.y),
                      radius + 4, 3)
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_bright"], alpha), (self.x, self.y),
                      radius, 3)
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["fire_hot"], alpha), (self.x, self.y),
                      max(1, radius - 4), 2)

            # Erupting spikes outward
            for i in range(8):
                angle = i * math.pi / 4
                spike_h = int(radius * 1.2 * t)
                base_x = self.x + int(math.cos(angle) * radius * 0.3)
                base_y = self.y + int(math.sin(angle) * radius * 0.3)
                tip_x = self.x + int(math.cos(angle) * (radius + spike_h))
                tip_y = self.y + int(math.sin(angle) * (radius + spike_h))
                _NS_vokrahn._aaline(surface, (*_NS_vokrahn.PALETTE["red_darkest"], alpha),
                        (base_x, base_y), (tip_x, tip_y), 4)
                _NS_vokrahn._aaline(surface, (*_NS_vokrahn.PALETTE["red_bright"], alpha),
                        (base_x, base_y), (tip_x, tip_y), 2)
                _NS_vokrahn._aaline(surface, (*_NS_vokrahn.PALETTE["fire_glow"], alpha),
                        (base_x, base_y), (tip_x, tip_y), 1)

            # Center bright core
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["fire_bright"], alpha),
                      (self.x, self.y), max(1, radius // 3))
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["fire_hot"], alpha),
                      (self.x, self.y), max(1, radius // 4))
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["fire_glow"], min(255, alpha)),
                      (self.x, self.y), max(1, radius // 6))

            # Sparks
            for i in range(10):
                a = i * math.pi / 5
                r = radius + int(math.sin(phase * 3 + i) * 5)
                ex = self.x + int(math.cos(a) * r)
                ey = self.y + int(math.sin(a) * r)
                _NS_vokrahn._draw_ember(surface, ex, ey, 2, alpha)


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_vok_projectiles"):
            boss._vok_projectiles = []
        if not hasattr(boss, "_vok_bursts"):
            boss._vok_bursts = []

        for proj in boss._vok_projectiles:
            proj.update()
            if not proj.alive and proj.age > 0:
                # Spawn impact burst at landing
                boss._vok_bursts.append(_NS_vokrahn.ImpactBurst(int(proj.tx), int(proj.ty),
                                                    life=25, size=30))
                proj.age = -1
            if proj.age >= 0:
                proj.draw(surface, phase)
        boss._vok_projectiles = [p for p in boss._vok_projectiles if p.alive]

        for burst in boss._vok_bursts:
            burst.update()
            burst.draw(surface, phase)
        boss._vok_bursts = [b for b in boss._vok_bursts if b.alive]


    def _spawn_chaos_bolt(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_vok_projectiles"):
            boss._vok_projectiles = []
        boss._vok_projectiles.append(_NS_vokrahn.ChaosBolt(sx, sy, tx, ty))


    def _spawn_burst(boss, x, y, size=30, life=25):
        if not hasattr(boss, "_vok_bursts"):
            boss._vok_bursts = []
        boss._vok_bursts.append(_NS_vokrahn.ImpactBurst(x, y, life=life, size=size))


    # ===================================================================
    # MAIN ENTRY
    # ===================================================================
    # ===================================================================
    # GERBANG LAPISAN HIDUP (heroes/vokrahn_fx)
    #   Trail sabetan, partikel, proyektil, skill FX, impact, hit-stop,
    #   dan screen shake hidup di RUANG LAYAR skala 1:1 supaya tidak ikut
    #   beku / menyusut bersama sprite cache di lane hero. Kalau modulnya
    #   tidak ada, owns() False dan renderer menggambar semuanya sendiri
    #   lewat jalur canvas (visual kehilangan polish, TIDAK PERNAH
    #   kehilangan efek).
    # ===================================================================
    @staticmethod
    def _live_module():
        NS = _NS_vokrahn
        if NS._LIVE_MOD is None:
            try:
                from heroes import vokrahn_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "VOKRAHN_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    @staticmethod
    def live_fx_ready():
        return _NS_vokrahn._live_module() is not None

    @staticmethod
    def _live_fx(boss, surface, x, y, want_draw, portrait):
        """Pasang/gambar lapisan hidup. Return (mod_untuk_draw, owned)."""
        NS = _NS_vokrahn
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
            if owned and not want_draw:
                # Lane hero: yang menggambar lapisan hidup adalah pipeline
                # heroes/__init__ (_live_fx_pre/_live_fx_post). Kalau
                # ternyata TIDAK ada yang menggambarnya, jangan matikan
                # fallback canvas — karakter tidak boleh kehilangan FX
                # secara diam-diam.
                checker = getattr(mod, "recently_drawn", None)
                if checker is not None:
                    owned = bool(checker(boss))
        except Exception:
            owned = False
        return (mod if want_draw else None), owned

    # ===================================================================
    # ANIMATION CONTROLLER
    #   Satu-satunya sumber kebenaran state/fase/timing. Lapisan hidup,
    #   overlay debug, dan alat uji semuanya membacanya dari sini.
    # ===================================================================
    @staticmethod
    def _ease(kind, t):
        if t <= 0.0:
            return 0.0
        if t >= 1.0:
            return 1.0
        if kind == "out":
            return 1.0 - (1.0 - t) * (1.0 - t)
        if kind == "oc":                              # out-cubic (cepat)
            return 1.0 - (1.0 - t) ** 3
        if kind == "in":
            return t * t
        if kind == "hold":
            return math.sin(t * math.pi * 0.5)
        return t * t * (3.0 - 2.0 * t)                # in-out (smoothstep)

    @staticmethod
    def attack_phases_order():
        return tuple(name for name, _a, _b in _NS_vokrahn.ATTACK_PHASES)

    @staticmethod
    def attack_phase(progress):
        """Nama fase serangan untuk progress 0..1."""
        p = max(0.0, min(1.0, float(progress)))
        for name, a, b in _NS_vokrahn.ATTACK_PHASES:
            if a <= p < b:
                return name
        return "RECOVERY"

    # ── GEOMETRI PEDANG (dipakai canvas, trail, & hitbox) ─────────
    @staticmethod
    def _sword_lift(progress):
        """Kenaikan grip (0..1) saat ayunan — SANGGUP dibaca FX lewat
        fallback identik di heroes/vokrahn_fx._fallback_lift."""
        NS = _NS_vokrahn
        p = max(0.0, min(1.0, float(progress)))
        E = NS._ease
        if p < 0.12:
            return 0.5 * E("out", p / 0.12)
        if p < 0.30:
            return 0.5 + 0.4 * E("io", (p - 0.12) / 0.18)
        if p < 0.50:
            return 0.9 - 0.9 * E("oc", (p - 0.30) / 0.20)
        if p < 0.62:
            return -0.12 * E("hold", (p - 0.50) / 0.12)
        if p < 0.82:
            return -0.12 + 0.17 * E("io", (p - 0.62) / 0.20)
        return 0.05 * (1.0 - E("io", (p - 0.82) / 0.18))

    @staticmethod
    def _sword_arc(progress):
        """``(phi, lift)`` ARK pedang — SATU sumber kebenaran."""
        NS = _NS_vokrahn
        p = max(0.0, min(1.0, float(progress)))
        for t0, t1, a0, a1, kind in NS.SWORD_ARC:
            if t0 <= p < t1 or (p >= 1.0 and t1 >= 1.0):
                e = NS._ease(kind, (p - t0) / max(0.0001, t1 - t0))
                return a0 + (a1 - a0) * e, NS._sword_lift(p)
        return NS.SWORD_ARC[0][2], 0.0

    @staticmethod
    def sword_geometry(facing, action, phase, attack_progress):
        """``(grip, tip_atas, ujung_bawah, phi)`` pedang — lokal badan.

        Titik-titik RELATIF jangkar badan ``(cx, cy)`` di skala layar 1.
        Inilah satu-satunya fungsi yang menghitung posisi pedang:
        canvas menggambar bilahnya, lapisan hidup mengukur trail &
        hitbox-nya, overlay debug menggambar rentang-nya.
        """
        NS = _NS_vokrahn
        ap = max(0.0, min(1.0, float(attack_progress)))
        if action in ("swing", "attack", "melee"):
            phi, lift = NS._sword_arc(ap)
        elif action == "e_cast":
            phi, lift = 0.22, 0.05                 # pedang teracung ke depan
        elif action == "q_cast":
            phi, lift = 1.9 + 0.10 * math.sin(phase), 0.35   # ke atas-bidik
        elif action == "r_cast":
            phi, lift = 2.0 + 0.08 * math.sin(phase * 0.7), 0.40
        elif action == "w_cast":
            phi, lift = 0.35, 0.0                  # pedang diayunkan rendah
        elif action == "death":
            phi, lift = 0.30, -0.15                # pedang terkulai
        else:
            phi = 0.96 + 0.06 * math.sin(phase * 0.8)
            lift = 0.0
        gx = facing * (NS._GRIP[0] + 5.0 * lift)
        gy = NS._GRIP[1] - 9.0 * lift
        L = NS._SWORD_HALF
        dx = facing * math.cos(phi) * L
        dy = -math.sin(phi) * L
        return ((gx, gy),
                (gx + dx, gy + dy),
                (gx + facing * math.cos(phi) * L * 0.55,
                 gy - math.sin(phi) * L * 0.55),
                phi)

    # ── DASH (skill E) ────────────────────────────────────────────
    @staticmethod
    def _dash_offset(progress):
        """Geser visual dash Chaos Strike (px dunia, arah facing).

        Puncak (80 px) jatuh di engine progress 0.302-0.605 — selaras
        dengan pose E lama (keluar 0.3, kembali 0.6 dari 50 frame) tapi
        dengan easing halus. Lapisan hidup membaca fungsi INI (bukan
        tabel sendiri) lewat heroes/vokrahn_fx.dash_offset.
        """
        NS = _NS_vokrahn
        p = max(0.0, min(1.0, float(progress)))
        if p < 0.302:
            return 80.0 * NS._ease("oc", p / 0.302)
        if p < 0.605:
            return 80.0
        if p < 1.0:
            return 80.0 * (1.0 - NS._ease("io", (p - 0.605) / 0.395))
        return 0.0

    @staticmethod
    def _detect_moving(boss):
        x = getattr(boss, "x", 0)
        y = getattr(boss, "y", 0)
        lx = getattr(boss, "_vok_last_x", x)
        ly = getattr(boss, "_vok_last_y", y)
        boss._vok_last_x = x
        boss._vok_last_y = y
        dx = abs(x - lx)
        dy = abs(y - ly)
        boss._vok_speed = dx + dy
        return (dx + dy) > 0.3

    @staticmethod
    def _update_vok_anim(boss, moving=False):
        """Controller: delta time, state + prioritas, timeline serangan.

        Vokrahn SELALU melee (greatsword) — tidak ada mode jarak jauh,
        jadi tidak ada percabangan swing/tembak seperti Zharok.
        """
        NS = _NS_vokrahn

        # ── delta time nyata ────────────────────────────────────────
        try:
            now = pygame.time.get_ticks()
        except Exception:                              # pragma: no cover
            now = 0
        prev_ms = getattr(boss, "_vok_last_ms", None)
        if prev_ms is None:
            dt = 1.0 / 60.0
        else:
            dt = (now - prev_ms) / 1000.0
            if dt <= 0.0 or dt > 0.05:
                dt = 1.0 / 60.0
        boss._vok_last_ms = now
        boss._vok_dt = dt

        # ── timeline serangan (timer engine menghitung MUNDUR) ─────
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 44)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vok_prev_timer", 0))
        active = bool(getattr(boss, "_vok_attack_active", False))

        # serangan baru: timer melonjak naik (di-reset ke cooldown)
        if timer > previous + 1 and timer >= cooldown - 2:
            boss._vok_attack_active = True
            boss._vok_attack_frame = 0
            active = True
        elif active:
            boss._vok_attack_frame = int(
                getattr(boss, "_vok_attack_frame", 0)) + 1
            if boss._vok_attack_frame > cooldown:
                boss._vok_attack_active = False
                boss._vok_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._vok_attack_active = False
            boss._vok_attack_frame = 0
            active = False

        boss._vok_prev_timer = timer
        frame = int(getattr(boss, "_vok_attack_frame", 0))
        # durasi animasi dibatasi supaya tebasan berat tetap berbobot
        anim_len = max(10, min(cooldown - 1, 30))
        progress = min(1.0, frame / float(anim_len)) if active else 0.0
        boss._vok_attack_progress = progress
        boss._vok_attack_phase = (NS.attack_phase(progress) if active
                                  else "NONE")
        lo, hi = NS.ATTACK_ACTIVE_WINDOW
        boss._vok_hit_window = bool(active and lo <= progress <= hi)

        # ── prioritas state ─────────────────────────────────────────
        skill = getattr(boss, "active_skill", None)
        alive = bool(getattr(boss, "alive", True))
        hurt = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        speed = float(getattr(boss, "_vok_speed", 0.0))

        if not alive:
            state = "DEATH"
        elif skill == "r":
            state = "SPECIAL"
        elif skill in ("q", "w", "e"):
            state = "SKILL"
        elif active and progress < 0.12:
            state = "CHARGE"
        elif active and progress < 0.30:
            state = "ATTACK"
        elif active:
            state = "SWING" if progress < 0.62 else "ATTACK"
        elif hurt > 0:
            state = "HURT"
        elif moving:
            state = "RUN" if speed > 1.2 else "WALK"
        else:
            state = "IDLE"

        prev_state = getattr(boss, "_vok_state", "IDLE")
        if prev_state != state:
            boss._vok_state_prev = prev_state
            boss._vok_state_time = 0.0
        else:
            boss._vok_state_time = getattr(boss, "_vok_state_time", 0.0) + dt
        boss._vok_state = state
        boss._vok_state_priority = NS.ANIM_STATES.get(state, 0)
        return state

    @staticmethod
    def _update_attack_anim(boss):
        """API LAMA — dipertahankan untuk kompatibilitas mundur.

        Mendelegasikan ke controller animasi v3 supaya tidak ada dua
        sumber kebenaran yang saling menimpa ``_vok_attack_progress``.
        """
        return _NS_vokrahn._update_vok_anim(
            boss, moving=(float(getattr(boss, "_vok_speed", 0.0)) > 0.3))

    @staticmethod
    def _resolve_pose_vok(boss, moving):
        """(action, phase, attack_progress) untuk renderer + lapisan hidup."""
        NS = _NS_vokrahn
        pulse = float(getattr(boss, "pulse", 0.0))
        state = getattr(boss, "_vok_state", "IDLE")
        ap = float(getattr(boss, "_vok_attack_progress", 0.0) or 0.0)
        skill = getattr(boss, "active_skill", None)
        timer = int(getattr(boss, "active_skill_timer", 0))

        if state in ("SKILL", "SPECIAL") and skill in ("q", "w", "e", "r"):
            dur = NS.SKILL_DUR.get(skill, 50)
            prog = max(0.0, min(1.0, 1.0 - timer / float(dur)))
            action = {"q": "q_cast", "w": "w_cast",
                      "e": "e_cast", "r": "r_cast"}[skill]
            return action, pulse, prog
        if state in ("ATTACK", "SWING", "CHARGE"):
            return "swing", pulse, ap
        if state == "RUN":
            return "run", pulse * 2.6, 0.0
        if state == "WALK":
            return "walk", pulse * 2.3, 0.0
        if state == "DEATH":
            return "death", pulse, 0.0
        if state == "HURT":
            return "hurt", pulse, 0.0
        return "idle", pulse, 0.0

    # ===================================================================
    # BADAN — komposit rig (buffer -> crop -> outline -> blit)
    #   Badan + pedang digambar ke buffer sekali, di-crop, diberi outline
    #   4-arah + rim light, lalu di-blit. Hasilnya disimpan sebagai
    #   ``_last_rig`` supaya lapisan hidup bisa membuat afterimage /
    #   hantu Phantasm TANPA menggambar ulang (murah + selalu sinkron).
    # ===================================================================
    @staticmethod
    def _draw_vok_body_raw(buf, ox, oy, facing, phase, action,
                           attack_progress):
        """Gambar ksatria + kuda + pedang (urutan layer v3)."""
        NS = _NS_vokrahn
        # 1) jubah (paling belakang)
        NS._draw_cape(buf, ox - 6 * facing, oy - 20, facing, phase, action)
        # 2) ekor kuda
        NS._draw_horse_tail(buf, ox, oy + 12, facing, phase, action)
        # 3) badan kuda
        NS._draw_horse_body(buf, ox, oy + 8, facing, phase)
        # 4) kaki kuda
        NS._draw_horse_legs(buf, ox, oy + 22, facing, phase, action)
        # 5) kepala kuda
        NS._draw_horse_head(buf, ox + 20 * facing, oy + 5, facing, phase)
        # 6) surai
        NS._draw_horse_mane(buf, ox + 8 * facing, oy - 2, facing, phase)
        # 7) ksatria penunggang (termasuk lengan + pedang)
        NS._draw_knight_rider(buf, ox - 3 * facing, oy - 20, facing, phase,
                              action, attack_progress)

    @staticmethod
    def _draw_vok_body(surface, cx, cy, facing, phase, action,
                       attack_progress=0, hurt=0):
        """Pipeline rig: buffer -> crop -> flash -> outline -> blit."""
        NS = _NS_vokrahn
        if NS._body_buf is None:
            NS._body_buf = pygame.Surface((NS.RIG_W, NS.RIG_H),
                                          pygame.SRCALPHA)
        buf = NS._body_buf
        buf.fill((0, 0, 0, 0))
        NS._draw_vok_body_raw(buf, NS.RIG_OX, NS.RIG_OY, facing, phase,
                              action, attack_progress)
        used = buf.get_bounding_rect(min_alpha=1)
        if used.width <= 2 or used.height <= 2:
            return
        used.inflate_ip(4, 4)
        used.clamp_ip(buf.get_rect())
        sub = buf.subsurface(used).copy()
        ox = int(cx) - NS.RIG_OX + used.left
        oy = int(cy) - NS.RIG_OY + used.top

        # hit flash: rig putih pudar saat baru terkena damage
        if hurt > 0:
            flash = sub.copy()
            flash.fill((255, 240, 235, 255),
                       special_flags=pygame.BLEND_RGB_MAX)
            flash.set_alpha(min(210, int(hurt) * 30))
            sub.blit(flash, (0, 0))

        # outline 4-arah (siluet kuat, gaya pixel-art)
        edge = sub.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(edge, (ox + ddx, oy + ddy))
        try:
            import lighting as _lighting
            if _lighting is not None:
                _lighting.apply_to_rig(sub, rim_add=(46, 20, 16),
                                       shade_mul=170)
        except Exception:
            pass
        surface.blit(sub, (ox, oy))
        # simpan rig terakhir untuk afterimage/hantu FX
        NS._last_rig = sub
        NS._last_rig_off = (ox - int(cx), oy - int(cy))

    # ===================================================================
    # LERENGAN Ksatria — semua posisi tangan mengikuti sword_geometry()
    #   (satu sumber; lengan tidak pernah melenceng dari bilah)
    # ===================================================================
    @staticmethod
    def _draw_knight_rider(surface, cx, cy, facing, phase, action,
                           attack_progress):
        """Ksatria berat bertengger di punggung kuda.

        ``(cx, cy)`` = JANGKAR KSATRIA (badan + (3f, 20)).
        """
        NS = _NS_vokrahn
        sway = int(math.sin(phase * 0.6) * 1)
        if action in ("walk", "run"):
            sway += int(math.sin(phase * 2) * 1)

        # Kaki (berlengan) menunggang kuda
        for side in (-1, 1):
            lx = cx + side * 4
            ly = cy + 12
            NS._rect(surface, NS.PALETTE["shadow_deep"], (lx - 2 + 1, ly + 1,
                                                          4, 7),
                     border_radius=1)
            NS._rect(surface, NS.PALETTE["arm_darkest"], (lx - 2, ly, 4, 7),
                     border_radius=1)
            NS._rect(surface, NS.PALETTE["arm_dark"], (lx - 2, ly, 4, 5))
            NS._rect(surface, NS.PALETTE["arm_mid"], (lx - 1, ly + 1, 2, 3))
            # trim merah
            NS._rect(surface, NS.PALETTE["red_mid"], (lx - 2, ly + 6, 4, 1))
            # sepatu logam
            NS._rect(surface, NS.PALETTE["metal_darkest"],
                     (lx - 3, ly + 7, 6, 3), border_radius=1)
            NS._rect(surface, NS.PALETTE["metal_dark"], (lx - 2, ly + 7,
                                                         4, 2))
            NS._rect(surface, NS.PALETTE["metal_light"], (lx - 2, ly + 7,
                                                          4, 1))

        kx = cx + sway
        NS._draw_knight_torso(surface, kx, cy, facing, phase)
        NS._draw_shield(surface, kx, cy - 2, facing, phase)
        NS._draw_knight_head(surface, kx, cy - 12, facing, phase)

        # lengan + pedang (selalu lewat sword_geometry)
        if action in ("swing", "attack", "melee"):
            NS._draw_knight_swing_arms(surface, cx, cy, facing, phase,
                                       attack_progress)
        elif action == "e_cast":
            NS._draw_knight_thrust_arms(surface, cx, cy, facing, phase)
        elif action == "q_cast":
            NS._draw_knight_cast_arms(surface, cx, cy, facing, phase)
        elif action == "w_cast":
            NS._draw_knight_wcast_arms(surface, cx, cy, facing, phase)
        elif action == "r_cast":
            NS._draw_knight_rcast_arms(surface, cx, cy, facing, phase)
        elif action == "death":
            NS._draw_knight_death_arms(surface, cx, cy, facing, phase)
        else:
            NS._draw_knight_idle_arms(surface, cx, cy, facing, phase)

    @staticmethod
    def _knight_grip(surface_unused, cx, cy, facing, phase, action, ap):
        """Grip & ujung pedang dalam KOORDINAT LOKAL ksatria.

        Jangkar ksatria = jangkar badan + (3f, 20), jadi posisi lokal
        (dari sword_geometry, relatif badan) digeser ke balik itu.
        """
        grip, tip_hi, tip_lo, phi = _NS_vokrahn.sword_geometry(
            facing, action, phase, ap)
        gx = cx + 3 * facing + grip[0]
        gy = cy + 20 + grip[1]
        return (gx, gy), (cx + 3 * facing + tip_hi[0],
                          cy + 20 + tip_hi[1]), phi

    @staticmethod
    def _draw_knight_arm_pair(surface, cx, cy, facing, phase, action, ap,
                              both=False, back_offset=(-6.0, 3.0)):
        """Lengan depan (dan opsional belakang) memegang grip + pedang."""
        NS = _NS_vokrahn
        (gx, gy), (tx, ty), _phi = NS._knight_grip(None, cx, cy, facing,
                                                   phase, action, ap)
        # bahu lengan depan
        sh_x = cx + facing * 10
        sh_y = cy - 4
        ex = sh_x + (gx - sh_x) * 0.5
        ey = sh_y + (gy - sh_y) * 0.5 + 2
        NS._draw_knight_arm(surface, sh_x, sh_y, ex, ey)
        NS._draw_knight_arm(surface, ex, ey, gx, gy)
        NS._draw_gauntlet(surface, gx, gy)

        if both:
            sh_x2 = cx - facing * 10
            sh_y2 = cy - 4
            bx = gx + back_offset[0] * facing
            by = gy + back_offset[1]
            NS._draw_knight_arm(surface, sh_x2, sh_y2,
                                (sh_x2 + bx) / 2, (sh_y2 + by) / 2 + 2)
            NS._draw_knight_arm(surface, (sh_x2 + bx) / 2,
                                (sh_y2 + by) / 2 + 2, bx, by)
            NS._draw_gauntlet(surface, bx, by)

        # pedang: dari grip ke ujung (bentuk api v2 — satu fungsi lama)
        NS._draw_flaming_sword_line(surface, gx, gy, tx, ty, facing, phase)

    @staticmethod
    def _draw_knight_back_arm(surface, cx, cy, facing):
        """Lengan belakang tetap di perisai."""
        NS = _NS_vokrahn
        sh_x2 = cx - facing * 10
        sh_y2 = cy - 4
        hand_x2 = sh_x2 - facing * 3
        hand_y2 = cy + 4
        NS._draw_knight_arm(surface, sh_x2, sh_y2, hand_x2, hand_y2)
        NS._draw_gauntlet(surface, hand_x2, hand_y2)

    @staticmethod
    def _draw_knight_idle_arms(surface, cx, cy, facing, phase):
        NS = _NS_vokrahn
        NS._draw_knight_back_arm(surface, cx, cy, facing)
        NS._draw_knight_arm_pair(surface, cx, cy, facing, phase, "idle", 0.0)

    @staticmethod
    def _draw_knight_swing_arms(surface, cx, cy, facing, phase, ap):
        NS = _NS_vokrahn
        NS._draw_knight_back_arm(surface, cx, cy, facing)
        NS._draw_knight_arm_pair(surface, cx, cy, facing, phase, "swing", ap)

    @staticmethod
    def _draw_knight_thrust_arms(surface, cx, cy, facing, phase):
        """Dash: kedua tangan mengacungkan pedang ke depan."""
        NS = _NS_vokrahn
        NS._draw_knight_arm_pair(surface, cx, cy, facing, phase, "e_cast",
                                 0.0, both=True, back_offset=(-5.0, 1.0))

    @staticmethod
    def _draw_knight_cast_arms(surface, cx, cy, facing, phase):
        """Q: satu tangan mengangkat pedang ke atas-bidik."""
        NS = _NS_vokrahn
        NS._draw_knight_back_arm(surface, cx, cy, facing)
        NS._draw_knight_arm_pair(surface, cx, cy, facing, phase, "q_cast",
                                 0.0)

    @staticmethod
    def _draw_knight_wcast_arms(surface, cx, cy, facing, phase):
        """W: kedua tangan menggenggam pedang di depan bawah."""
        NS = _NS_vokrahn
        NS._draw_knight_arm_pair(surface, cx, cy, facing, phase, "w_cast",
                                 0.0, both=True, back_offset=(-6.0, 1.0))

    @staticmethod
    def _draw_knight_rcast_arms(surface, cx, cy, facing, phase):
        """R: kedua tangan mengangkat pedang ke atas (memanggil hantu)."""
        NS = _NS_vokrahn
        NS._draw_knight_arm_pair(surface, cx, cy, facing, phase, "r_cast",
                                 0.0, both=True, back_offset=(-5.0, 0.0))

    @staticmethod
    def _draw_knight_death_arms(surface, cx, cy, facing, phase):
        NS = _NS_vokrahn
        NS._draw_knight_back_arm(surface, cx, cy, facing)
        NS._draw_knight_arm_pair(surface, cx, cy, facing, phase, "death",
                                 0.0)

    def _draw_cape(surface, cx, cy, facing, phase, action):
        """Tattered red cape behind knight."""
        wave = math.sin(phase * 0.8) * 3
        wave2 = math.sin(phase * 1.2 + 0.5) * 2

        # Cape spreads down and back
        cape_pts = [
            (cx - facing * 6, cy - 8),
            (cx - facing * 10, cy - 4),
            (cx - facing * 16 - int(wave), cy + 8),
            (cx - facing * 20 - int(wave2), cy + 20),
            (cx - facing * 16 - int(wave), cy + 32),
            (cx - facing * 10, cy + 38),
            (cx - facing * 2, cy + 36),
            (cx + facing * 2, cy + 30),
            (cx + facing * 4, cy + 5),
        ]
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["shadow_deep"], [(p[0] + 2, p[1] + 2) for p in cape_pts])
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["cape_darkest"], cape_pts)
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["cape_dark"], [
            (cx - facing * 5, cy - 7),
            (cx - facing * 9, cy - 3),
            (cx - facing * 14 - int(wave * 0.7), cy + 9),
            (cx - facing * 17 - int(wave2 * 0.7), cy + 20),
            (cx - facing * 14 - int(wave * 0.7), cy + 30),
            (cx - facing * 9, cy + 35),
            (cx - facing * 2, cy + 33),
            (cx + facing * 2, cy + 28),
            (cx + facing * 3, cy + 5),
        ])
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["cape_mid"], [
            (cx - facing * 4, cy - 5),
            (cx - facing * 8, cy - 2),
            (cx - facing * 11 - int(wave * 0.5), cy + 10),
            (cx - facing * 13 - int(wave2 * 0.5), cy + 20),
            (cx - facing * 11 - int(wave * 0.5), cy + 28),
            (cx - facing * 7, cy + 31),
            (cx - facing * 2, cy + 30),
            (cx + facing * 1, cy + 25),
            (cx + facing * 2, cy + 5),
        ])

        # Tattered edges - jagged bottom
        for i in range(5):
            edge_x = cx - facing * (16 - i * 3) - int(wave)
            edge_y = cy + 38 + int(math.sin(phase + i) * 3)
            _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["cape_darkest"], [
                (edge_x - 2, cy + 30),
                (edge_x + 2, cy + 30),
                (edge_x, edge_y),
            ])
            _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["cape_dark"], [
                (edge_x - 1, cy + 30),
                (edge_x + 1, cy + 30),
                (edge_x, edge_y - 2),
            ])

        # Red highlights on cape (flame-like)
        for i in range(3):
            t = (phase * 0.4 + i * 0.3) % 1.0
            hx = cx - facing * (14 - int(t * 8))
            hy = cy - 4 + int(t * 40)
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_mid"], 120), (hx, hy), 3)
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_bright"], 100), (hx, hy), 2)


    def _draw_horse_tail(surface, cx, cy, facing, phase, action):
        """Wispy red flame tail."""
        tail_wave = math.sin(phase * 1.2) * 4

        # Base tail flowing back
        tail_pts = [
            (cx - facing * 15, cy - 3),
            (cx - facing * 20, cy - 5 + int(tail_wave)),
            (cx - facing * 26, cy - 2 + int(tail_wave * 1.5)),
            (cx - facing * 30, cy + 4 + int(tail_wave)),
            (cx - facing * 32, cy + 12 + int(tail_wave * 0.5)),
            (cx - facing * 28, cy + 18),
            (cx - facing * 22, cy + 15),
            (cx - facing * 16, cy + 5),
        ]
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["shadow_deep"], [(p[0] + 1, p[1] + 1) for p in tail_pts])
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["mane_darkest"], tail_pts)
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["mane_dark"], [
            (cx - facing * 14, cy - 2),
            (cx - facing * 19, cy - 4 + int(tail_wave)),
            (cx - facing * 24, cy - 1 + int(tail_wave)),
            (cx - facing * 28, cy + 5),
            (cx - facing * 30, cy + 12),
            (cx - facing * 26, cy + 16),
            (cx - facing * 21, cy + 13),
            (cx - facing * 15, cy + 4),
        ])
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["mane_mid"], [
            (cx - facing * 14, cy),
            (cx - facing * 18, cy - 1),
            (cx - facing * 22, cy + 2),
            (cx - facing * 25, cy + 8),
            (cx - facing * 22, cy + 13),
            (cx - facing * 17, cy + 10),
            (cx - facing * 14, cy + 3),
        ])

        # Bright flame streaks
        for i in range(4):
            t = i / 3
            sx = cx - facing * int(16 + t * 15)
            sy = cy - 2 + int(t * 15) + int(tail_wave * (1 - t))
            _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["mane_bright"],
                    (sx, sy), (sx - facing * 3, sy + 3), 1)
            _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["mane_hot"], (sx, sy), 1)


    def _draw_horse_body(surface, cx, cy, facing, phase):
        """Dark demonic horse body."""
        # Shadow
        _NS_vokrahn._ellipse(surface, _NS_vokrahn.PALETTE["shadow_deep"], (cx - 18, cy - 3, 36, 22))

        # Main body
        _NS_vokrahn._ellipse(surface, _NS_vokrahn.PALETTE["horse_darkest"], (cx - 17, cy - 5, 34, 20))
        _NS_vokrahn._ellipse(surface, _NS_vokrahn.PALETTE["horse_dark"], (cx - 15, cy - 4, 30, 17))
        _NS_vokrahn._ellipse(surface, _NS_vokrahn.PALETTE["horse_mid"], (cx - 13, cy - 3, 26, 13))
        _NS_vokrahn._ellipse(surface, _NS_vokrahn.PALETTE["horse_light"], (cx - 10, cy - 4, 20, 6))
        _NS_vokrahn._ellipse(surface, _NS_vokrahn.PALETTE["horse_high"], (cx - 6, cy - 4, 12, 3))

        # Belly (darker)
        _NS_vokrahn._ellipse(surface, _NS_vokrahn.PALETTE["horse_darkest"], (cx - 12, cy + 8, 24, 6))
        _NS_vokrahn._ellipse(surface, _NS_vokrahn.PALETTE["horse_dark"], (cx - 10, cy + 8, 20, 4))

        # Armor plate on side of horse
        _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["arm_darkest"], (cx - 10, cy + 2, 20, 8),
              border_radius=1)
        _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["arm_dark"], (cx - 9, cy + 3, 18, 6))
        _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["arm_mid"], (cx - 8, cy + 3, 16, 3))

        # Red trim on armor
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["red_mid"], (cx - 9, cy + 9), (cx + 9, cy + 9), 1)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["red_bright"], (cx - 8, cy + 10), (cx + 8, cy + 10), 1)

        # Chaos rune on armor (small)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_dark"], (cx, cy + 6), 3)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_mid"], (cx, cy + 6), 2)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_hot"], (cx, cy + 6), 1)

        # Rivets on armor
        for rx in (-7, -3, 3, 7):
            _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["metal_darkest"], (cx + rx, cy + 4), 1)
            _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["metal_shine"], (cx + rx, cy + 4), 1)


    def _draw_horse_legs(surface, cx, cy, facing, phase, action):
        """4 armored horse legs."""
        walk_phase = phase * 3 if action == "walk" else 0
        if action == "dash":
            walk_phase = phase * 5

        # 4 legs
        for i, (leg_x, leg_off) in enumerate([(-10, 0), (-4, math.pi),
                                                (4, math.pi / 2), (10, 3 * math.pi / 2)]):
            lx = cx + leg_x * facing
            lift = int(math.sin(walk_phase + leg_off) * 2) if action == "walk" else 0
            lift = int(math.sin(walk_phase + leg_off) * 4) if action == "dash" else lift

            # Upper leg (armored)
            _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["shadow_deep"], (lx - 3 + 1, cy - lift + 1, 6, 8),
                  border_radius=1)
            _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["arm_darkest"], (lx - 3, cy - lift, 6, 8),
                  border_radius=1)
            _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["arm_dark"], (lx - 2, cy - lift + 1, 4, 6))
            _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["arm_mid"], (lx - 2, cy - lift + 1, 4, 2))
            # Red trim
            _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["red_mid"], (lx - 3, cy - lift + 7, 6, 1))

            # Lower leg (dark)
            _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["shadow_deep"], (lx + 1, cy + 8 - lift),
                    (lx + 1, cy + 15 - lift), 3)
            _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["horse_darkest"], (lx, cy + 8 - lift),
                    (lx, cy + 15 - lift), 3)
            _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["horse_dark"], (lx, cy + 8 - lift),
                    (lx, cy + 14 - lift), 2)

            # Hoof
            _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["metal_darkest"], (lx - 3, cy + 14 - lift, 6, 3),
                  border_radius=1)
            _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["metal_dark"], (lx - 2, cy + 14 - lift, 4, 2))
            _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["metal_mid"], (lx - 2, cy + 14 - lift, 4, 1))


    def _draw_horse_head(surface, cx, cy, facing, phase):
        """Demonic horse head with red eyes and armor."""
        # Shadow
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["shadow_deep"], (cx + 1, cy + 1), 9)

        # Head base
        _NS_vokrahn._ellipse(surface, _NS_vokrahn.PALETTE["horse_darkest"], (cx - 8, cy - 6, 16, 14))
        _NS_vokrahn._ellipse(surface, _NS_vokrahn.PALETTE["horse_dark"], (cx - 7, cy - 5, 14, 12))
        _NS_vokrahn._ellipse(surface, _NS_vokrahn.PALETTE["horse_mid"], (cx - 6, cy - 4, 12, 9))
        _NS_vokrahn._ellipse(surface, _NS_vokrahn.PALETTE["horse_light"], (cx - 5, cy - 4, 8, 4))

        # Snout extending forward
        snout = [
            (cx + facing * 1, cy - 2),
            (cx + facing * 9, cy - 3),
            (cx + facing * 12, cy + 1),
            (cx + facing * 9, cy + 5),
            (cx + facing * 1, cy + 5),
        ]
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["shadow_deep"], [(p[0] + 1, p[1] + 1) for p in snout])
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["horse_darkest"], snout)
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["horse_dark"], [
            (cx + facing * 2, cy - 1),
            (cx + facing * 8, cy - 2),
            (cx + facing * 11, cy + 1),
            (cx + facing * 8, cy + 4),
            (cx + facing * 2, cy + 4),
        ])
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["horse_mid"], [
            (cx + facing * 3, cy),
            (cx + facing * 7, cy - 1),
            (cx + facing * 9, cy + 1),
            (cx + facing * 7, cy + 3),
        ])

        # Nostril flaring (with red glow)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["shadow_deep"], (cx + facing * 9, cy + 1), 1)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_hot"], (cx + facing * 9, cy + 1), 1)

        # Fierce mouth with fangs
        _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["shadow_deep"], (cx + facing * 5, cy + 3, 4, 2))
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["metal_light"], [
            (cx + facing * 6, cy + 3),
            (cx + facing * 6, cy + 5),
            (cx + facing * 7, cy + 3),
        ])
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["metal_light"], [
            (cx + facing * 7, cy + 3),
            (cx + facing * 8, cy + 5),
            (cx + facing * 8, cy + 3),
        ])

        # Glowing red eye
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["shadow_deep"], (cx + facing * 3, cy - 3), 2)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["eye_dark"], (cx + facing * 3, cy - 3), 2)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["eye_bright"], (cx + facing * 3, cy - 3),
                  max(1, int(2 * eye_pulse)))
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["eye_hot"], (cx + facing * 3, cy - 3), 1)
        # Eye halo glow
        _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["eye_bright"], int(100 * eye_pulse)),
                  (cx + facing * 3, cy - 3), 5)

        # Armor plate on face (horse chanfron)
        _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["arm_darkest"], (cx - 4, cy - 5, 8, 6), border_radius=1)
        _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["arm_dark"], (cx - 3, cy - 4, 6, 4))
        _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["arm_mid"], (cx - 3, cy - 4, 6, 1))
        # Red gem in center
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_dark"], (cx, cy - 2), 2)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_bright"], (cx, cy - 2), 1)

        # Armor ears (metal spikes instead of ears)
        for side_off in (-3, 3):
            _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["arm_darkest"], [
                (cx + side_off - 1, cy - 5),
                (cx + side_off + 1, cy - 5),
                (cx + side_off, cy - 12),
            ])
            _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["arm_dark"], [
                (cx + side_off, cy - 5),
                (cx + side_off + 1, cy - 5),
                (cx + side_off, cy - 11),
            ])
            _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_hot"], (cx + side_off, cy - 12), 1)

        # Face straps
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["metal_darkest"], (cx - 5, cy), (cx + facing * 10, cy + 2), 1)


    def _draw_horse_mane(surface, cx, cy, facing, phase):
        """Red flowing mane along horse neck."""
        for i in range(7):
            offset = i * 2 - 6
            wave = math.sin(phase * 0.8 + i * 0.5) * 2
            mx = cx - facing * (i * 2) + int(wave)
            my = cy - i // 2

            # Mane strand
            _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["mane_darkest"], [
                (mx - 1, my),
                (mx + 1, my),
                (mx + int(wave), my + 8),
            ])
            _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["mane_dark"], [
                (mx - 1, my),
                (mx + 1, my),
                (mx + int(wave), my + 6),
            ])
            _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["mane_mid"], [
                (mx, my),
                (mx + 1, my),
                (mx + int(wave), my + 5),
            ])
            # Flame tip
            _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["mane_bright"], (mx + int(wave), my + 4), 1)


    def _draw_knight_torso(surface, cx, cy, facing, phase):
        """Heavy armored torso."""
        # Shadow
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["shadow_deep"], [
            (cx - 9 + 1, cy - 6 + 1),
            (cx + 9 + 1, cy - 6 + 1),
            (cx + 8 + 1, cy + 10 + 1),
            (cx - 8 + 1, cy + 10 + 1),
        ])

        # Torso base
        torso = [
            (cx - 9, cy - 6),
            (cx + 9, cy - 6),
            (cx + 8, cy + 10),
            (cx - 8, cy + 10),
        ]
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["arm_darkest"], torso)
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["arm_dark"], [
            (cx - 8, cy - 5),
            (cx + 8, cy - 5),
            (cx + 7, cy + 9),
            (cx - 7, cy + 9),
        ])
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["arm_mid"], [
            (cx - 6, cy - 3),
            (cx + 6, cy - 3),
            (cx + 5, cy + 7),
            (cx - 5, cy + 7),
        ])

        # Chest plate detail - diagonal lines
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["arm_light"], (cx - 7, cy - 4), (cx, cy + 8), 1)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["arm_light"], (cx + 7, cy - 4), (cx, cy + 8), 1)

        # Red trim on shoulders
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["red_mid"], (cx - 9, cy - 6), (cx + 9, cy - 6), 2)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["red_bright"], (cx - 8, cy - 5), (cx + 8, cy - 5), 1)

        # Chaos symbol on chest
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_darkest"], (cx, cy + 2), 4)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_dark"], (cx, cy + 2), 3)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_bright"], (cx, cy + 2), 2)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_hot"], (cx, cy + 2), 1)

        # Arrow-like chaos symbol pointing outward (8 directions)
        for i in range(4):
            angle = i * math.pi / 4
            ex = cx + int(math.cos(angle) * 4)
            ey = cy + 2 + int(math.sin(angle) * 4)
            _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["red_mid"], (cx, cy + 2), (ex, ey), 1)

        # Shoulder pauldrons
        for side in (-1, 1):
            sx = cx + side * 11
            _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["shadow_deep"], (sx + 1, cy - 6 + 1), 7)
            _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["arm_darkest"], (sx, cy - 6), 7)
            _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["arm_dark"], (sx - side, cy - 7), 6)
            _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["arm_mid"], (sx - side * 2, cy - 8), 4)
            _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["arm_light"], (sx - side * 3, cy - 9), 2)
            # Red trim
            _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_mid"], (sx, cy - 6), 7, 1)
            # Spike on top
            _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["arm_darkest"], [
                (sx - 2, cy - 12),
                (sx + 2, cy - 12),
                (sx, cy - 18),
            ])
            _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["arm_dark"], [
                (sx - 1, cy - 12),
                (sx + 1, cy - 12),
                (sx, cy - 16),
            ])
            _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_hot"], (sx, cy - 18), 1)


    def _draw_shield(surface, cx, cy, facing, phase):
        """Shield on back side (drawn behind knight but visible)."""
        shield_side = -facing
        sx = cx + shield_side * 10
        sy = cy + 4

        # Shield shape (kite shape)
        shield_pts = [
            (sx, sy - 8),
            (sx + shield_side * 5, sy - 4),
            (sx + shield_side * 6, sy + 4),
            (sx + shield_side * 3, sy + 10),
            (sx - shield_side * 3, sy + 10),
            (sx - shield_side * 6, sy + 4),
            (sx - shield_side * 5, sy - 4),
        ]
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["shadow_deep"], [(p[0] + 1, p[1] + 1) for p in shield_pts])
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["arm_darkest"], shield_pts)
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["arm_dark"], [
            (sx, sy - 7),
            (sx + shield_side * 4, sy - 3),
            (sx + shield_side * 5, sy + 4),
            (sx + shield_side * 2, sy + 9),
            (sx - shield_side * 2, sy + 9),
            (sx - shield_side * 5, sy + 4),
            (sx - shield_side * 4, sy - 3),
        ])

        # Red trim
        for i in range(len(shield_pts)):
            p1 = shield_pts[i]
            p2 = shield_pts[(i + 1) % len(shield_pts)]
            _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["red_mid"], p1, p2, 1)

        # Chaos symbol on shield
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_darkest"], (sx, sy + 2), 4)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_mid"], (sx, sy + 2), 3)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_bright"], (sx, sy + 2), 2)
        # 4 arrows
        for i in range(4):
            angle = i * math.pi / 2 + math.pi / 4
            ex = sx + int(math.cos(angle) * 4)
            ey = sy + 2 + int(math.sin(angle) * 4)
            _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["red_hot"], (sx, sy + 2), (ex, ey), 1)


    def _draw_knight_head(surface, cx, cy, facing, phase):
        """Helmed head with horns and glowing red visor."""
        # Shadow
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["shadow_deep"], (cx + 1, cy + 1), 8)

        # Helmet base
        helm = [
            (cx - 7, cy + 6),
            (cx - 8, cy - 3),
            (cx - 5, cy - 8),
            (cx + 5, cy - 8),
            (cx + 8, cy - 3),
            (cx + 7, cy + 6),
        ]
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["arm_darkest"], helm)
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["arm_dark"], [
            (cx - 6, cy + 5),
            (cx - 7, cy - 2),
            (cx - 4, cy - 7),
            (cx + 4, cy - 7),
            (cx + 7, cy - 2),
            (cx + 6, cy + 5),
        ])
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["arm_mid"], [
            (cx - 4, cy + 4),
            (cx - 5, cy - 2),
            (cx - 3, cy - 5),
            (cx + 3, cy - 5),
            (cx + 5, cy - 2),
            (cx + 4, cy + 4),
        ])

        # Highlight
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["arm_high"], (cx - 4, cy - 6), (cx + 4, cy - 6), 1)

        # Visor (dark horizontal slit)
        _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["shadow_deep"], (cx - 6, cy - 1, 12, 3), border_radius=1)
        _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["arm_darkest"], (cx - 5, cy - 1, 10, 2))

        # GLOWING RED EYES in visor
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for side in (-1, 1):
            ex = cx + side * 3
            ey = cy
            _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["eye_bright"], (ex, ey),
                      max(1, int(2 * eye_pulse)))
            _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["eye_hot"], (ex, ey), 1)
            # Halo
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["eye_bright"], int(120 * eye_pulse)),
                      (ex, ey), 4)

        # Red band across visor
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["red_bright"], (cx - 5, cy + 3), (cx + 5, cy + 3), 1)

        # BIG HORNS on helmet (Chaos Knight signature)
        for side in (-1, 1):
            # Base
            _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["shadow_deep"], [
                (cx + side * 5 + 1, cy - 6 + 1),
                (cx + side * 13 + 1, cy - 10 + 1),
                (cx + side * 16 + 1, cy - 4 + 1),
                (cx + side * 12 + 1, cy - 3 + 1),
            ])
            # Main horn (curving outward and up)
            _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["arm_darkest"], [
                (cx + side * 5, cy - 6),
                (cx + side * 13, cy - 10),
                (cx + side * 16, cy - 4),
                (cx + side * 12, cy - 3),
            ])
            _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["arm_dark"], [
                (cx + side * 6, cy - 6),
                (cx + side * 12, cy - 9),
                (cx + side * 15, cy - 5),
                (cx + side * 11, cy - 3),
            ])
            _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["arm_mid"], [
                (cx + side * 7, cy - 6),
                (cx + side * 11, cy - 8),
                (cx + side * 13, cy - 5),
                (cx + side * 10, cy - 4),
            ])
            # Highlight
            _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["arm_light"],
                    (cx + side * 8, cy - 7),
                    (cx + side * 13, cy - 6), 1)
            # Sharp tip
            _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["metal_shine"],
                      (cx + side * 16, cy - 4), 1)
            # Red glow on tip
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_hot"], 200),
                      (cx + side * 16, cy - 4), 2)

        # Small middle spike on top of helm
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["arm_darkest"], [
            (cx - 1, cy - 8),
            (cx + 1, cy - 8),
            (cx, cy - 13),
        ])
        _NS_vokrahn._poly(surface, _NS_vokrahn.PALETTE["arm_dark"], [
            (cx, cy - 8),
            (cx + 1, cy - 8),
            (cx, cy - 12),
        ])
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_hot"], (cx, cy - 13), 1)


    def _draw_knight_arm(surface, x1, y1, x2, y2):
        """Armored arm segment."""
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["shadow_deep"], (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 6)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["arm_darkest"], (x1, y1), (x2, y2), 5)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["arm_dark"], (x1, y1), (x2, y2), 4)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["arm_mid"], (x1, y1), (x2, y2), 2)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["arm_light"], (x1 - 1, y1), (x2 - 1, y2), 1)


    def _draw_gauntlet(surface, x, y):
        """Armored fist."""
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["shadow_deep"], (x + 1, y + 1), 4)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["arm_darkest"], (x, y), 4)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["arm_dark"], (x, y), 3)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["arm_mid"], (x - 1, y - 1), 2)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["arm_light"], (x - 1, y - 1), 1)
        # Red trim
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_mid"], (x, y), 4, 1)


    def _draw_flaming_sword_line(surface, hx, hy, end_x, end_y, facing, phase):
        """Sword line with handle, guard, and flaming blade."""
        # Direction
        dx = end_x - hx
        dy = end_y - hy
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 1:
            return
        dir_x = dx / dist
        dir_y = dy / dist
        perp_x = -dir_y
        perp_y = dir_x

        # Handle (short section near hand)
        handle_len = 4
        hx2 = hx + int(dir_x * handle_len)
        hy2 = hy + int(dir_y * handle_len)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["shadow_deep"], (hx + 1, hy + 1), (hx2 + 1, hy2 + 1), 4)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["cape_dark"], (hx, hy), (hx2, hy2), 4)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["cape_mid"], (hx, hy), (hx2, hy2), 2)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["red_mid"], (hx, hy), (hx2, hy2), 1)

        # Cross-guard (perpendicular)
        guard_len = 4
        g1_x = hx2 + int(perp_x * guard_len)
        g1_y = hy2 + int(perp_y * guard_len)
        g2_x = hx2 - int(perp_x * guard_len)
        g2_y = hy2 - int(perp_y * guard_len)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["shadow_deep"], (g1_x + 1, g1_y + 1), (g2_x + 1, g2_y + 1), 4)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["metal_darkest"], (g1_x, g1_y), (g2_x, g2_y), 3)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["metal_dark"], (g1_x, g1_y), (g2_x, g2_y), 2)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["metal_light"], (g1_x, g1_y), (g2_x, g2_y), 1)
        # Guard tips with red gems
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_bright"], (g1_x, g1_y), 2)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_hot"], (g1_x, g1_y), 1)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_bright"], (g2_x, g2_y), 2)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_hot"], (g2_x, g2_y), 1)

        # Blade (rest of length)
        blade_start_x = hx2
        blade_start_y = hy2
        blade_end_x = end_x
        blade_end_y = end_y

        # Shadow
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["shadow_deep"],
                (blade_start_x + 1, blade_start_y + 1),
                (blade_end_x + 1, blade_end_y + 1), 5)

        # Blade layers (dark red core)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["red_darkest"], (blade_start_x, blade_start_y),
                (blade_end_x, blade_end_y), 4)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["red_dark"], (blade_start_x, blade_start_y),
                (blade_end_x, blade_end_y), 3)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["red_mid"], (blade_start_x, blade_start_y),
                (blade_end_x, blade_end_y), 2)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["red_bright"], (blade_start_x, blade_start_y),
                (blade_end_x, blade_end_y), 1)

        # Bright edge
        edge_perp_x = perp_x * 1
        edge_perp_y = perp_y * 1
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["fire_hot"],
                (blade_start_x + int(edge_perp_x), blade_start_y + int(edge_perp_y)),
                (blade_end_x + int(edge_perp_x), blade_end_y + int(edge_perp_y)), 1)
        _NS_vokrahn._aaline(surface, _NS_vokrahn.PALETTE["fire_glow"],
                (blade_start_x - int(edge_perp_x), blade_start_y - int(edge_perp_y)),
                (blade_end_x - int(edge_perp_x), blade_end_y - int(edge_perp_y)), 1)

        # Sharp tip
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["fire_white"], (blade_end_x, blade_end_y), 2)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["fire_hot"], (blade_end_x, blade_end_y), 1)

        # FLAMES rising from blade
        for i in range(6):
            t = 0.2 + (i / 6) * 0.7
            base_x = int(blade_start_x + (blade_end_x - blade_start_x) * t)
            base_y = int(blade_start_y + (blade_end_y - blade_start_y) * t)
            flame_off = int(math.sin(phase * 3 + i) * 2)
            flame_x = base_x + int(perp_x * flame_off)
            flame_y = base_y + int(perp_y * flame_off)
            flame_size = 3 + (i % 2)

            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["fire_dark"], 200),
                      (flame_x, flame_y), flame_size + 1)
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["fire_bright"], 220),
                      (flame_x, flame_y), flame_size)
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["fire_hot"], 240),
                      (flame_x, flame_y), max(1, flame_size - 1))
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["fire_glow"], 255),
                      (flame_x, flame_y), max(1, flame_size - 2))

        # Overall blade glow
        mid_x = (blade_start_x + blade_end_x) // 2
        mid_y = (blade_start_y + blade_end_y) // 2
        _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_bright"], 100),
                  (mid_x, mid_y), int(dist * 0.5))
        _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["fire_hot"], 80),
                  (mid_x, mid_y), int(dist * 0.3))


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_chaos_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Chaos red wisps beneath boss."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((160, 46), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(38, 3, -4):
            alpha = int((38 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_vokrahn.PALETTE["red_darkest"], min(255, alpha)),
                    (80 - radius * 2, 23 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 80, cy - 11))

        # Rising red wisps
        for i, offset in enumerate((-26, -10, 10, 26)):
            t = (phase * 0.6 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 30)
            alpha = max(0, min(255, int(220 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_darkest"], alpha), (sx, sy), 5)
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_dark"], alpha), (sx, sy - 2), 3)
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_bright"], alpha), (sx, sy - 3), 2)
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_hot"], alpha), (sx, sy - 3), 1)

        # Embers orbiting
        for i in range(7):
            angle = phase * 0.8 + i * math.pi * 2 / 7
            r = 26 + int(math.sin(phase + i * 1.3) * 6)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 10)
            _NS_vokrahn._draw_ember(surface, sx, sy, 2, 200)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 13 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = max(0, 150 - i * 25)
                _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_dark"], alpha),
                          (sx, sy), max(2, 6 - i))
                _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_bright"], alpha),
                          (sx, sy), max(1, 4 - i))


    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((130, 24), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 14)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (12 - radius, 12 - radius, 106 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_vokrahn.PALETTE["red_darkest"], 80), (10, 6, 110, 12))
        surface.blit(shadow, (x - 65, y - 12))


    def _draw_chaos_aura(surface, x, y, phase, active_skill):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.6 if active_skill in ("q", "w", "e", "r") else 1.0
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(90, 5, -4):
            alpha = int((90 - radius) * 1.4 * pulse * strength)
            if alpha > 0:
                _NS_vokrahn._aacircle(aura, (*_NS_vokrahn.PALETTE["red_darkest"], min(255, alpha)),
                          (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))


    def _draw_ground_runes(surface, x, y, phase, active_skill):
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((150, 48), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_vokrahn.PALETTE["red_dark"], 160),
                            (5, 10, 140, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_vokrahn.PALETTE["red_mid"], 190),
                            (20, 14, 110, 20), 2)

        # Chaos rune marks
        for i in range(8):
            angle = phase * 0.15 + i * math.pi / 4
            x1 = 75 + int(math.cos(angle) * 35)
            y1 = 24 + int(math.sin(angle) * 8)
            x2 = 75 + int(math.cos(angle) * 65)
            y2 = 24 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_vokrahn.PALETTE["red_bright"], 180),
                             (x1, y1), (x2, y2), 1)

        if active_skill:
            pygame.draw.ellipse(ring, (*_NS_vokrahn.PALETTE["red_hot"], int(80 * pulse)),
                                (15, 8, 120, 32), 1)

        # Central chaos symbol
        for i in range(8):
            angle = i * math.pi / 4
            ex1 = 75 + int(math.cos(angle) * 8)
            ey1 = 24 + int(math.sin(angle) * 3)
            ex2 = 75 + int(math.cos(angle) * 12)
            ey2 = 24 + int(math.sin(angle) * 4)
            pygame.draw.line(ring, (*_NS_vokrahn.PALETTE["red_bright"], 200),
                             (ex1, ey1), (ex2, ey2), 1)

        surface.blit(ring, (x - 75, y - 24))


    def _draw_sword_swing_arc(surface, x, y, facing, progress):
        """Fire trail from sword swing."""
        if progress < 0.28 or progress > 0.75:
            return
        if progress < 0.5:
            visibility = (progress - 0.28) / 0.22
        else:
            visibility = 1.0 - (progress - 0.5) / 0.25
        visibility = max(0.0, min(1.0, visibility))

        arc = pygame.Surface((160, 120), pygame.SRCALPHA)
        for i in range(20):
            t = i / 19
            angle = -math.pi * 0.9 + t * math.pi * 1.1
            px = 80 + int(math.cos(angle) * 60) * facing
            py = 60 + int(math.sin(angle) * 44)
            alpha = int((220 - i * 10) * visibility)
            if alpha <= 0:
                continue
            _NS_vokrahn._aacircle(arc, (*_NS_vokrahn.PALETTE["fire_darkest"], alpha), (px, py), 10)
            _NS_vokrahn._aacircle(arc, (*_NS_vokrahn.PALETTE["red_dark"], alpha), (px, py), 7)
            _NS_vokrahn._aacircle(arc, (*_NS_vokrahn.PALETTE["red_bright"], alpha), (px, py), 5)
            _NS_vokrahn._aacircle(arc, (*_NS_vokrahn.PALETTE["fire_hot"], alpha), (px, py), 3)
            _NS_vokrahn._aacircle(arc, (*_NS_vokrahn.PALETTE["fire_glow"], min(255, alpha)), (px, py), 1)
        surface.blit(arc, (x - 80, y - 60))


    def _draw_swing_impact(surface, x, y, facing, progress):
        if progress < 0.5 or progress > 0.85:
            return
        t = (progress - 0.5) / 0.35
        intensity = math.sin(t * math.pi)

        impact_x = x + 42 * facing
        impact_y = y + 5
        alpha = int(230 * intensity)
        radius = int(10 + intensity * 22)

        _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_dark"], alpha // 2),
                  (impact_x, impact_y), radius + 4)
        _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_bright"], alpha),
                  (impact_x, impact_y), radius, 3)
        _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["fire_hot"], alpha),
                  (impact_x, impact_y), max(1, radius - 6), 2)
        _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["fire_glow"], alpha),
                  (impact_x, impact_y), max(1, radius - 10))

        # Sparks
        for i in range(10):
            angle = i * math.pi / 5 + progress * 3
            dx = impact_x + int(math.cos(angle) * radius * 1.3)
            dy = impact_y + int(math.sin(angle) * radius * 0.9)
            _NS_vokrahn._draw_ember(surface, dx, dy, 2, alpha)


    # ===================================================================
    # SKILL CANVAS — FALLBACK saat lapisan hidup tidak tersedia
    #   Semua durasi di SINI memakai NS.SKILL_DUR (dikunci ke AI): Q 50,
    #   W 60, E 50, R 80 frame. (Renderer lama punya bug: Q pakai 55 &
    #   W/R pakai 80/90 — dikoreksi di sini.)
    # ===================================================================
    @staticmethod
    def _handle_skill_projectiles(boss, x, y, active_skill, timer):
        """Bolt Q versi canvas (dipanggil entry hanya kalau not owned)."""
        NS = _NS_vokrahn
        if active_skill == "q":
            duration = int(NS.SKILL_DUR["q"])
            progress = max(0.0, min(1.0, 1 - timer / duration))
            if 0.35 < progress < 0.45 and not getattr(boss, "_vok_q_spawned",
                                                      False):
                tx, ty = NS._target_position(boss, x, y)
                sx = x + 25 * boss.direction
                sy = y - 15
                NS._spawn_chaos_bolt(boss, sx, sy, tx, ty)
                boss._vok_q_spawned = True
            if progress > 0.7:
                boss._vok_q_spawned = False

    @staticmethod
    def _draw_q_charge_glow(surface, boss, x, y, timer, phase):
        """Muatan chaos berkumpul di ujung bilah sebelum Q lepas."""
        NS = _NS_vokrahn
        progress = max(0.0, min(1.0, 1 - timer / int(NS.SKILL_DUR["q"])))
        if progress < 0.10 or progress > 0.45:
            return
        pulse = NS._resolve_pose_vok(boss, False)
        _action, _ph, _ap = pulse
        grip, tip_hi, _lo, _phi = NS.sword_geometry(boss.direction, "q_cast",
                                                    phase, 0.0)
        tx = x + tip_hi[0]
        ty = y + tip_hi[1]
        grow = min(1.0, max(0.0, (progress - 0.10) / 0.25))
        s = int((4 + 8 * grow) * (0.85 + 0.15 * math.sin(phase * 3)))
        if s < 1:
            return
        NS._aacircle(surface, (*NS.PALETTE["red_dark"], 90), (tx, ty),
                     s + 4)
        NS._aacircle(surface, (*NS.PALETTE["red_bright"], 140), (tx, ty),
                     s + 2)
        NS._aacircle(surface, (*NS.PALETTE["red_hot"], 200), (tx, ty), s)
        NS._aacircle(surface, (*NS.PALETTE["red_glow"], 235), (tx, ty),
                     max(1, s - 2))
        _ = grip

    @staticmethod
    def _draw_realm_of_chaos_ground(surface, boss, x, y, timer, phase):
        """Telegraph W: LINGKARAN PENUH radius dunia 220 (kontrak)."""
        NS = _NS_vokrahn
        progress = max(0.0, min(1.0, 1 - timer / int(NS.SKILL_DUR["w"])))
        # damage W jatuh saat cast -> lingkaran penuh sejak 20 % pertama
        grow = min(1.0, progress / 0.20)
        fade = 1.0 - max(0.0, (progress - 0.70) / 0.28)
        if fade <= 0.02 or grow <= 0.02:
            return
        pulse = math.sin(phase * 2) * 0.2 + 0.8
        r = int(220 * grow)
        # cincin luar penuh (radius damage)
        NS._ellipse(surface,
                    (*NS.PALETTE["red_bright"],
                     int(190 * pulse * fade * grow)),
                    (x - r, y + 45 - r // 2, r * 2, r), 2)
        # gerigi duri di pinggir (dekorasi, bukan lingkaran polos)
        num = 14
        for i in range(num):
            angle = i * math.pi * 2 / num + phase * 0.15
            sx = x + int(math.cos(angle) * r)
            sy = y + 45 + int(math.sin(angle) * r * 0.5)
            NS._aaline(surface,
                       (*NS.PALETTE["red_hot"], int(150 * fade)),
                       (sx, sy),
                       (x + int(math.cos(angle) * r * 1.12),
                        y + 45 + int(math.sin(angle) * r * 0.56)), 2)
        # rune runik berputar di dalam
        for i in range(8):
            angle = phase * 0.5 + i * math.pi / 4
            x1 = x + int(math.cos(angle) * r * 0.72)
            y1 = y + 45 + int(math.sin(angle) * r * 0.36)
            x2 = x + int(math.cos(angle) * r * 0.86)
            y2 = y + 45 + int(math.sin(angle) * r * 0.43)
            NS._aaline(surface,
                       (*NS.PALETTE["red_glow"], int(130 * fade)),
                       (x1, y1), (x2, y2), 1)
        # genangan chaos di tengah
        NS._ellipse(surface,
                    (*NS.PALETTE["red_darkest"], int(110 * fade * grow)),
                    (x - r // 2, y + 45 - r // 6, r, r // 3), 0)

    @staticmethod
    def _draw_realm_of_chaos(surface, boss, x, y, timer, phase):
        """Ledakan duri W — DEPAN badan (momentum damage, awal jendela)."""
        NS = _NS_vokrahn
        progress = max(0.0, min(1.0, 1 - timer / int(NS.SKILL_DUR["w"])))
        if progress < 0.16:
            return
        if progress < 0.62:
            erupt_t = (progress - 0.16) / 0.46
        else:
            erupt_t = 1.0 - (progress - 0.62) / 0.28
        erupt_t = max(0.0, min(1.0, erupt_t))
        if erupt_t <= 0.02:
            return
        # duri di sepanjang cincin radius dunia
        ring_r = 205
        num_spikes = 14
        for i in range(num_spikes):
            angle = i * math.pi * 2 / num_spikes + phase * 0.05
            sx = x + int(math.cos(angle) * ring_r)
            sy = y + 45 + int(math.sin(angle) * ring_r * 0.5)
            spike_h = int(25 * erupt_t) + (i % 3) * 3
            NS._draw_chaos_spike(surface, sx, sy, sy - spike_h, 4, 240)
        # duri dalam
        inner_r = 120
        for i in range(10):
            angle = (i + 0.5) * math.pi * 2 / 10 + phase * 0.1
            sx = x + int(math.cos(angle) * inner_r)
            sy = y + 45 + int(math.sin(angle) * inner_r * 0.5)
            spike_h = int(18 * erupt_t)
            NS._draw_chaos_spike(surface, sx, sy, sy - spike_h, 3, 220)
        # duri pusat
        center_h = int(35 * erupt_t)
        NS._draw_chaos_spike(surface, x, y + 45, y + 45 - center_h, 5, 250)
        # percikan
        for i in range(10):
            angle = phase * 2 + i * math.pi / 5
            r = ring_r + int(math.sin(phase * 3 + i) * 6)
            sx = x + int(math.cos(angle) * r)
            sy = (y + 45 + int(math.sin(angle) * r * 0.5)
                  - int(erupt_t * 12))
            NS._draw_ember(surface, sx, sy, 2, int(230 * erupt_t))

    @staticmethod
    def _draw_phantasm_ground(surface, boss, x, y, timer, phase):
        """Telegraph R: LINGKARAN PENUH radius dunia 220 + rune."""
        NS = _NS_vokrahn
        progress = max(0.0, min(1.0, 1 - timer / int(NS.SKILL_DUR["r"])))
        grow = min(1.0, progress / 0.20)
        fade = 1.0 - max(0.0, (progress - 0.75) / 0.23)
        if fade <= 0.02 or grow <= 0.02:
            return
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        r = int(220 * grow)
        NS._ellipse(surface,
                    (*NS.PALETTE["red_mid"], int(190 * pulse * fade * grow)),
                    (x - r, y + 45 - r // 2, r * 2, r), 2)
        # rune lingkaran
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            x1 = x + int(math.cos(angle) * r * 0.78)
            y1 = y + 45 + int(math.sin(angle) * r * 0.39)
            x2 = x + int(math.cos(angle) * r * 0.92)
            y2 = y + 45 + int(math.sin(angle) * r * 0.46)
            NS._aaline(surface,
                       (*NS.PALETTE["red_hot"], int(200 * fade * pulse)),
                       (x1, y1), (x2, y2), 1)
        # bintang chaos 8 titik di tengah (bukan lingkaran)
        star_r = int(r * 0.5)
        if star_r > 8:
            pts = []
            for i in range(16):
                a = phase * 0.5 + i * math.pi / 8
                rr = star_r if i % 2 == 0 else star_r * 0.45
                pts.append((x + int(math.cos(a) * rr),
                            y + 45 + int(math.sin(a) * rr * 0.5)))
            NS._poly(surface, (*NS.PALETTE["red_darkest"], int(90 * fade)),
                     pts)

    @staticmethod
    def _draw_phantasm_illusions(surface, boss, x, y, timer, phase):
        """2 hantu Phantasm (versi canvas, bila lapisan hidup absent)."""
        NS = _NS_vokrahn
        progress = max(0.0, min(1.0, 1 - timer / int(NS.SKILL_DUR["r"])))
        if progress < 0.16:
            return
        fade_t = min(1.0, (progress - 0.16) / 0.25)
        alpha = int(180 * fade_t)
        positions = [
            (x - 55 * boss.direction, y),
            (x - 30 * boss.direction, y + 8),
        ]
        for i, (ix, iy) in enumerate(positions):
            if NS._body_buf is None:
                NS._body_buf = pygame.Surface((NS.RIG_W, NS.RIG_H),
                                              pygame.SRCALPHA)
            buf = NS._body_buf
            buf.fill((0, 0, 0, 0))
            NS._draw_vok_body_raw(buf, NS.RIG_OX, NS.RIG_OY,
                                  boss.direction, phase + i, "idle", 0.0)
            used = buf.get_bounding_rect(min_alpha=1)
            if used.width <= 2 or used.height <= 2:
                continue
            illusion = buf.subsurface(used).copy()
            # tint merah gelap
            overlay = pygame.Surface(illusion.get_size(), pygame.SRCALPHA)
            overlay.fill((*NS.PALETTE["red_dark"], 110))
            illusion.blit(overlay, (0, 0),
                          special_flags=pygame.BLEND_RGBA_MULT)
            illusion.set_alpha(alpha)
            bob = int(math.sin(phase * 2 + i * 2) * 3)
            surface.blit(illusion, (ix - used.width // 2,
                                    iy - used.height // 2 + bob))
            NS._aacircle(surface,
                         (*NS.PALETTE["red_bright"],
                          int(60 * fade_t * (1 - progress * 0.5))),
                         (ix, iy), 40)

    @staticmethod
    def _draw_dash_trail_fx(surface, x, y, facing, progress):
        """Jalur api dash E versi canvas (nama baru, isi lama)."""
        NS = _NS_vokrahn
        if 0.1 < progress < 0.75:
            for i in range(5):
                bx = x - facing * (i + 1) * 14
                by = y + int(math.sin(progress * 9 + i) * 3)
                a = int(120 - i * 20)
                if a > 10:
                    NS._aacircle(surface,
                                 (*NS.PALETTE["red_dark"], a), (bx, by + 8),
                                 10 - i)
                    NS._aacircle(surface,
                                 (*NS.PALETTE["red_mid"],
                                  int(a * 0.8)), (bx, by + 8), 6 - i)
    # ===================================================================
    # MAIN ENTRY — urutan render v3
    #   CONTROLLER -> LAPISAN HIDUP (ground) -> AURA/RUNE -> TELEGRAPH
    #   SKILL (canvas bila not owned) -> HANTU R (belakang) -> BADAN
    #   (shadow + rig + pedang) -> PROYEKTIL/SKILL FX DEPAN (canvas bila
    #   not owned) -> LAPISAN HIDUP (depan) -> DEBUG.
    # ===================================================================
    def draw_vokrahn(surface, boss, x, y):
        """Entry point Boss.draw() sekaligus jalur hero-lane.

        Urutan render:
          GROUND -> GROUND FX -> SHADOW -> BACK PARTICLES -> BODY/ARMOR/
          HEAD/WEAPON -> ATTACK TRAIL -> PROJECTILE -> FRONT PARTICLES ->
          SKILL FX -> IMPACT FX -> DEBUG.

        Trail / partikel / proyektil / impact / hit-stop / shake hidup di
        ``heroes/vokrahn_fx`` (ruang layar 1:1); canvas hanya fallback
        bila modul itu tidak tersedia.
        """
        NS = _NS_vokrahn
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        portrait = bool(getattr(boss, "_portrait_hd", False))
        hero_lane = hasattr(boss, "_render_scale")
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        hurt = int(getattr(boss, "hurt_flash_timer", 0) or 0)

        # ── CONTROLLER ANIMASI ─────────────────────────────────────
        moving = NS._detect_moving(boss)
        NS._update_vok_anim(boss, moving)
        action, phase, ap = NS._resolve_pose_vok(boss, moving)
        boss._vok_pose_action = action
        boss._vok_phase = phase

        # ── LAPISAN HIDUP (ground) ─────────────────────────────────
        live, owned = NS._live_fx(boss, surface, x, y, not hero_lane,
                                  portrait)
        boss._vok_suppress_canvas_fx = owned

        # ── GESESER VISUAL (dash E / lunge tebas / flinch) ─────────
        if action == "e_cast":
            dx = int(NS._dash_offset(ap) * facing)
        elif action in ("swing", "attack", "melee"):
            dx = int(math.sin(ap * math.pi) * 5) * facing
        elif action == "q_cast":
            dx = int(math.sin(ap * math.pi * 2) * 2) * -facing
        elif hurt > 0:
            dx = int(min(3, hurt * 0.5)) * -facing
        else:
            dx = 0
        bx, by = x + dx, y

        # ── GROUND FX / AURA ───────────────────────────────────────
        if not portrait:
            NS._draw_chaos_aura(surface, x, y, pulse, active_skill)
            NS._draw_ground_runes(surface, x, y + NS.GROUND_DY, pulse,
                                  active_skill)
            if not owned:
                if active_skill == "w":
                    NS._draw_realm_of_chaos_ground(surface, boss, x, y,
                                                   skill_timer, pulse)
                elif active_skill == "r":
                    NS._draw_phantasm_ground(surface, boss, x, y,
                                             skill_timer, pulse)

        # ── HANTU R (DI BELAKANG BADAN; canvas fallback) ──────────
        if not portrait and not owned and active_skill == "r":
            NS._draw_phantasm_illusions(surface, boss, x, y, skill_timer,
                                        pulse)

        # ── BADAN (shadow -> wisps -> rig+pedang, satu komposit) ──
        bob = 0
        if action in ("idle", "q_cast", "w_cast", "r_cast"):
            bob = int(math.sin(pulse * 0.7) * 2)
        elif action in ("walk", "run"):
            bob = int(abs(math.sin(phase * 1.2)) * 3)
        NS._draw_shadow(surface, bx, y + NS.GROUND_DY)
        NS._draw_chaos_wisps(surface, bx, y + 44, pulse,
                             trail=action in ("walk", "run", "dash"),
                             facing=facing,
                             intense=(action in ("swing", "attack", "melee",
                                                 "e_cast", "q_cast",
                                                 "w_cast", "r_cast")))
        NS._draw_vok_body(surface, bx, by + bob, facing, phase, action,
                          ap, hurt=hurt)

        # ── PROYEKTIL + SKILL FX DEPAN (fallback canvas) ───────────
        if not portrait and not owned:
            if action in ("swing", "attack", "melee"):
                NS._draw_sword_swing_arc(surface, bx, by, facing, ap)
                NS._draw_swing_impact(surface, bx, by, facing, ap)
            if action == "e_cast":
                NS._draw_dash_trail_fx(surface, bx, by, facing, ap)
            NS._handle_skill_projectiles(boss, x, y, active_skill,
                                         skill_timer)
            NS._manage_projectiles(boss, surface, pulse)
            if active_skill == "q":
                NS._draw_q_charge_glow(surface, boss, x, y, skill_timer,
                                       pulse)
            elif active_skill == "w":
                NS._draw_realm_of_chaos(surface, boss, x, y, skill_timer,
                                        pulse)

        # ── LAPISAN HIDUP DI ATAS (trail/proyektil/impact/skill) ──
        if live is not None:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass

        # ── DEBUG ──────────────────────────────────────────────────
        if getattr(NS, "DEBUG_CHARACTER", False) and not portrait:
            NS._draw_vokrahn_debug(surface, boss, x, y)

    # ===================================================================
    # OVERLAY DEBUG RENDERER (DEBUG_CHARACTER = True)
    # ===================================================================
    _DBG_FONT = None

    @staticmethod
    def _dbg_font():
        NS = _NS_vokrahn
        if NS._DBG_FONT is None:
            try:
                if not pygame.font.get_init():
                    pygame.font.init()
                NS._DBG_FONT = pygame.font.SysFont("consolas,monospace", 11)
            except Exception:                          # pragma: no cover
                NS._DBG_FONT = False
        return NS._DBG_FONT or None

    @staticmethod
    def _draw_vokrahn_debug(surface, boss, x, y):
        """Hitbox pedang, hurtbox, attack range, radius skill, state,
        FPS, jumlah partikel, timer serangan — dari controller."""
        NS = _NS_vokrahn
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        ap = float(getattr(boss, "_vok_attack_progress", 0.0) or 0.0)
        lo, hi = NS.ATTACK_ACTIVE_WINDOW
        active = bool(getattr(boss, "_vok_hit_window", False))
        action = getattr(boss, "_vok_pose_action", "idle")
        phase = float(getattr(boss, "_vok_phase",
                              getattr(boss, "pulse", 0.0)))

        # jangkauan serangan (elips tanah)
        rng = float(getattr(boss, "attack_range",
                            getattr(boss, "range", 55)) or 55)
        rng = rng / max(0.05, scale)
        pygame.draw.ellipse(surface, (90, 200, 255),
                            pygame.Rect(int(x - rng),
                                        int(y + NS.GROUND_DY - rng * 0.4),
                                        int(rng * 2), int(rng * 0.8)), 1)
        # jangkauan tebasan greatsword
        mr = NS.MELEE_REACH / max(0.05, scale)
        pygame.draw.ellipse(surface, (255, 160, 80),
                            pygame.Rect(int(x - mr),
                                        int(y + NS.GROUND_DY - mr * 0.4),
                                        int(mr * 2), int(mr * 0.8)), 1)
        # radius skill aktif
        skill = getattr(boss, "active_skill", None)
        if skill in NS.SKILL_RADIUS:
            rr = NS.SKILL_RADIUS[skill] / max(0.05, scale)
            pygame.draw.ellipse(surface, (255, 120, 120),
                                pygame.Rect(int(x - rr),
                                            int(y + NS.GROUND_DY
                                                      - rr * 0.4),
                                            int(rr * 2), int(rr * 0.8)), 1)
        # hurtbox
        pygame.draw.rect(surface, (70, 240, 120),
                         pygame.Rect(int(x - 26), int(y - 56), 52, 92), 1)
        # hitbox pedang (grip -> tip)
        grip, tip_hi, tip_lo, _phi = NS.sword_geometry(facing, action, phase,
                                                       ap)
        col = (255, 80, 80) if active else (150, 150, 160)
        pygame.draw.line(surface, col,
                         (int(x + tip_lo[0]), int(y + tip_lo[1])),
                         (int(x + tip_hi[0]), int(y + tip_hi[1])),
                         2 if active else 1)
        pygame.draw.circle(surface, col,
                           (int(x + tip_hi[0]), int(y + tip_hi[1])), 13, 1)
        pygame.draw.circle(surface, (240, 240, 90),
                           (int(x + grip[0]), int(y + grip[1])), 2, 1)
        # proyektil canvas fallback
        for bolt in getattr(boss, "_vok_projectiles", ()) or ():
            pygame.draw.circle(surface, (255, 220, 90),
                               (int(bolt.x), int(bolt.y)), 8, 1)

        font = NS._dbg_font()
        if font is None:
            return
        parts = 0
        proj = len(getattr(boss, "_vok_projectiles", ()) or ())
        try:
            mod = NS._live_module()
            if mod is not None:
                st = mod.stats()
                parts = st.get("particles", 0)
                proj += st.get("projectiles", 0)
        except Exception:                              # pragma: no cover
            pass
        dt = float(getattr(boss, "_vok_dt", 1.0 / 60.0)) or (1.0 / 60.0)
        lines = [
            "VOKRAHN [renderer debug]",
            "state %s <- %s (p%d)" % (
                getattr(boss, "_vok_state", "?"),
                getattr(boss, "_vok_state_prev", "-"),
                int(getattr(boss, "_vok_state_priority", 0))),
            "pose %s  dt %.4f  fps %.0f" % (action, dt, 1.0 / max(1e-4, dt)),
            "attack %.2f %s%s" % (ap,
                                  getattr(boss, "_vok_attack_phase", "NONE"),
                                  "  <HIT>" if active else ""),
            "window %.2f-%.2f  impact %.2f" % (lo, hi,
                                               NS.ATTACK_IMPACT_FRAME),
            "swing MELEE  timer %s cd %s" % (
                getattr(boss, "timer", "-"),
                getattr(boss, "attack_cooldown", "-")),
            "skill %s t%s  live %s" % (
                skill or "-", getattr(boss, "active_skill_timer", "-"),
                "ON" if getattr(boss, "_vok_suppress_canvas_fx", False)
                else "off"),
            "part %d  proj %d" % (parts, proj),
        ]
        pad = 4
        w = max(font.size(t)[0] for t in lines) + pad * 2
        h = len(lines) * 13 + pad * 2
        box = pygame.Surface((w, h), pygame.SRCALPHA)
        box.fill((10, 8, 12, 190))
        pygame.draw.rect(box, (255, 120, 160, 200), box.get_rect(), 1)
        for i, t in enumerate(lines):
            box.blit(font.render(t, True, (255, 224, 190)),
                     (pad, pad + i * 13))
        surface.blit(box, (int(x) - w - 46, int(y) - 100))

    @staticmethod
    def draw_boss(surface, boss, x, y):
        _NS_vokrahn.draw_vokrahn(surface, boss, x, y)


# ====================================================================
# IGNIS_DRACHORN
# ====================================================================
class _NS_ignis_drachorn:
    """Namespace ignis_drachorn - PIXEL MASTERWORK v2 + COMBAT FX v3.

    Rewrite penuh renderer + sistem tempur **IGNIS DRACHORN, THE MOLTEN
    SOVEREIGN** (true boss level 4) mengikuti standar Thorne v2 Pixel
    Masterwork + v3 Combat FX (lihat docs/AUDIT_ULANG_DARI_AWAL.md).

    Pembagian kerja:

      RENDERER (file ini)                LAPISAN HIDUP (heroes/ignis_drachorn_fx.py)
      ---------------------------------  ------------------------------------------
      rig dragon knight berlapis         trail ayunan greatsword (histori nyata)
      palette + outline + rim light      particle system (ember/asap/debris)
      ANIMATION CONTROLLER (state,       proyektil Fire Orb / Meteor modular
        fase, hit window, delta time)    IMPACT FX + hit-stop + screen shake
      ark ayunan pedang (SWORD_ARC)      SkillFX q/w/e/r lifecycle penuh
      telegraph tanah q/w/e/r            overlay DEBUG_CHARACTER
      elder dragon form (R)              -- semua di luar cache sprite --
      fallback penuh saat modul FX
        tidak tersedia

    100% PROSEDURAL: tidak ada PNG / JPG / GIF / sprite-sheet, dan tidak
    ada pemuat gambar eksternal apa pun. Semua bentuk dari pygame.Surface +
    pygame.draw + pygame.transform + pygame.Vector2 + pygame.mask.
    """

    # ---------------------------------------------------------------------------
    # 0. KONFIGURASI
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    #: Debug visual karakter: hitbox, hurtbox, attack range, tabrakan
    #: proyektil, state animasi, frame, FPS, jumlah partikel, state skill,
    #: dan timer serangan.
    DEBUG_CHARACTER = False

    # ── cache (nama lama dipertahankan) ─────────────────────────────
    _shadow_cache = None
    _aura_cache = None
    _flash_buf = None
    _body_buf = None
    _record_shadow = None
    _STATIC_SURFACES = {}
    _LIVE_MOD = None
    _premul_buf = None               # buffer premultiply decal additif
    _last_rig = None                 # rig terakhir (untuk afterimage FX)
    _last_rig_off = (0, 0)

    # ── metrik rig ──────────────────────────────────────────────────
    # Rig di-author 1:1 pada resolusi tampil (chunky pixel, hard edge,
    # tanpa smoothscale) supaya piksel tetap tajam. Buffer badan dipakai
    # untuk outline siluet + pass pencahayaan.
    RIG_W, RIG_H = 220, 230
    RIG_OX, RIG_OY = 110, 132
    SCALE = 1.0
    FEET_DY = 48
    GROUND_DY = FEET_DY

    #: Durasi pose skill (frame sim) — SINKRON dengan
    #: base_boss._cast_q/w/e/r_* (active_skill_timer).
    SKILL_DUR = {"q": 45, "w": 40, "e": 60, "r": 90}

    #: Radius efek di ruang DUNIA (px). Dipakai telegraph & FX.
    SKILL_RADIUS = {"q": 250, "w": 130, "e": 110, "r": 220}

    #: Fase serangan (fraksi 0..1 durasi serangan). Nama fase dipakai
    #: renderer, lapisan hidup, dan overlay debug — satu kosakata.
    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, 0.12),
        ("WINDUP",       0.12, 0.30),
        ("SWING",        0.30, 0.50),
        ("IMPACT",       0.50, 0.62),
        ("FOLLOW",       0.62, 0.82),
        ("RECOVERY",     0.82, 1.00),
    )

    #: Jendela hit aktif + frame impact (dibaca FX & debug).
    ATTACK_ACTIVE_WINDOW = (0.36, 0.62)
    ATTACK_IMPACT_FRAME = 0.52

    #: Prioritas state animasi. Angka besar menang; DEATH mengunci.
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
        "HIT": 60,
        "HURT": 65,
        "DEATH": 100,
    }

    #: ARK AYUNAN GREATSWORD — (t0, t1, theta0, theta1, ease).
    #: theta = sudut bilah dari sumbu ATAS (rad); positif berputar ke
    #: arah depan (facing). Pedang TIDAK PERNAH melompat: tiap fase
    #: bersambung dengan fase berikutnya (a1 == a0 fase sesudahnya).
    SWORD_ARC = (
        (0.00, 0.12,  2.42,  2.00, "out"),    # ANTICIPATION: angkat tip dari tanah
        (0.12, 0.30,  2.00, -1.30, "io"),     # WIND-UP: putar tinggi ke belakang
        (0.30, 0.50, -1.30,  1.80, "oc"),     # SWING: tebasan cepat ke depan
        (0.50, 0.62,  1.80,  2.12, "hold"),   # IMPACT: overshoot + tahan bobot
        (0.62, 0.82,  2.12,  2.72, "io"),     # FOLLOW THROUGH: bilah turun
        (0.82, 1.00,  2.72,  2.42, "io"),     # RECOVERY: kembali ke garda
    )

    #: Panjang bilah (px lokal) & offset grip idle.
    BLADE_LEN = 56.0
    GRIP_LOCAL = (16.0, -6.0)

    # ---------------------------------------------------------------------------
    # 1. HD PALETTE — Molten Sovereign
    #    Obsidian plate + magma seam + crimson cloth + gold dragon trim.
    #    Tiap material adalah RAMP 4-8 band dengan hue-shift (bayangan
    #    condong ungu-dingin, highlight condong kuning-panas) supaya
    #    volume terbaca walau palette-nya terbatas.
    # ---------------------------------------------------------------------------
    PALETTE = {
        # ── kontrak 9 kunci karakter ────────────────────────────────
        "outline":        (6,    3,   6),
        "shadow":         (0,    0,   0),
        "dark":           (28,   16,  20),
        "body":           (58,   36,  40),
        "mid":            (96,   62,  62),
        "light":          (150,  108, 100),
        "highlight":      (226,  200, 188),
        "weapon":         (255,  150,  46),
        "fx":             (255,  196,  78),

        # Armor obsidian - 6 band (dark steel dengan pantulan merah)
        "armor_darkest":  (18,   12,  14),
        "armor_dark":     (42,   28,  30),
        "armor_mid":      (75,   52,  55),
        "armor_light":    (120,  90,  90),
        "armor_high":     (170, 140, 138),
        "armor_shine":    (215, 195, 190),

        # Obsidian pelat berat (siluet luar) - 5 band
        "obsidian_darkest": (10,   7,  11),
        "obsidian_dark":    (26,  18,  24),
        "obsidian_mid":     (48,  34,  42),
        "obsidian_light":   (82,  60,  70),
        "obsidian_high":    (128, 100, 110),

        # Magma seam (retakan menyala di pelat) - 5 band
        "magma_dark":     (96,   16,   6),
        "magma_mid":      (192,  56,  12),
        "magma_hot":      (255, 128,  28),
        "magma_bright":   (255, 190,  76),
        "magma_white":    (255, 246, 208),

        # Red cloth / cape - 6 band
        "red_darkest":    (45,    8,  10),
        "red_dark":       (90,   18,  22),
        "red_mid":        (140,  30,  35),
        "red_light":      (185,  55,  55),
        "red_high":       (220,  90,  80),
        "red_shine":      (250, 145, 120),

        # Gold trim - 5 band
        "gold_darkest":   (58,   36,   8),
        "gold_dark":      (95,   62,  15),
        "gold_mid":       (170, 125,  35),
        "gold_light":     (230, 190,  75),
        "gold_shine":     (255, 235, 150),

        # Fire - 7 band
        "fire_darkest":   (60,   12,   4),
        "fire_dark":      (135,  35,   8),
        "fire_mid":       (215,  80,  15),
        "fire_light":     (250, 145,  30),
        "fire_bright":    (255, 200,  65),
        "fire_hot":       (255, 235, 140),
        "fire_white":     (255, 250, 220),

        # Dragon scale - 6 band
        "dragon_darkest": (25,    8,  10),
        "dragon_dark":    (60,   18,  20),
        "dragon_mid":     (105,  30,  32),
        "dragon_light":   (155,  55,  50),
        "dragon_high":    (200, 100,  80),
        "dragon_rim":     (240, 160, 120),

        # Sword blade - fiery steel 5 band
        "blade_dark":     (120,  60,  25),
        "blade_mid":      (200, 130,  55),
        "blade_light":    (245, 195, 100),
        "blade_hot":      (255, 235, 170),
        "blade_core":     (255, 252, 232),

        # Wing membrane - 4 band
        "wing_dark":      (52,   14,  20),
        "wing_mid":       (92,   26,  30),
        "wing_light":     (146,  48,  44),
        "wing_glow":      (226, 108,  62),

        # Horn / claw / bone - 4 band
        "horn_dark":      (36,   26,  26),
        "horn_mid":       (78,   62,  58),
        "horn_light":     (140, 120, 108),
        "horn_shine":     (206, 190, 170),

        # Leather strap - 4 band
        "leather_dark":   (34,   20,  16),
        "leather_mid":    (72,   44,  28),
        "leather_light":  (118,  78,  46),
        "leather_high":   (162, 118,  74),

        # Ash / smoke - 4 band
        "smoke_dark":     (24,   18,  22),
        "smoke_mid":      (58,   46,  50),
        "smoke_light":    (104,  88,  90),
        "smoke_glow":     (168, 142, 132),

        # Misc
        "shadow_deep":    (8,     4,   6),
        "white":          (255, 255, 255),

        # Eye glow - 4 band
        "eye_dark":       (100,  20,   5),
        "eye_mid":        (220,  90,  15),
        "eye_bright":     (255, 180,  60),
        "eye_hot":        (255, 240, 180),
    }

    # ---------------------------------------------------------------------------
    # 2. PRIMITIF (zero-allocation bila memungkinkan)
    # ---------------------------------------------------------------------------
    _CLAMP_MEMO = {}

    @staticmethod
    def _static(key, builder):
        """Surface statis ter-cache (dibangun sekali, dipakai ulang)."""
        surf = _NS_ignis_drachorn._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_ignis_drachorn._STATIC_SURFACES[key] = surf
        return surf

    @staticmethod
    def _clamp(color):
        try:
            hit = _NS_ignis_drachorn._CLAMP_MEMO.get(color)
        except TypeError:
            return tuple(max(0, min(255, int(c))) for c in color)
        if hit is not None:
            return hit
        out = tuple(max(0, min(255, int(c))) for c in color)
        memo = _NS_ignis_drachorn._CLAMP_MEMO
        if len(memo) > 8192:
            memo.clear()
        memo[color] = out
        return out

    @staticmethod
    def _alpha(v):
        return max(0, min(255, int(v)))

    @staticmethod
    def _mix(a, b, t):
        t = max(0.0, min(1.0, t))
        return _NS_ignis_drachorn._clamp(
            (a[0] + (b[0] - a[0]) * t,
             a[1] + (b[1] - a[1]) * t,
             a[2] + (b[2] - a[2]) * t))

    @staticmethod
    def _hash01(i):
        """Hash deterministik kecil -> [0,1). Dipakai bentuk bergerigi."""
        x = math.sin(i * 127.1 + 311.7) * 43758.5453
        return x - math.floor(x)

    @staticmethod
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_ignis_drachorn._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4),
                                  pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2),
                               radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_ignis_drachorn.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius,
                                     width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)

    @staticmethod
    def _aaline(surface, color, start, end, width=1):
        color = _NS_ignis_drachorn._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width * 2
            min_y = min(sy, ey) - width * 2
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey),
                         max(1, width))

    @staticmethod
    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_ignis_drachorn._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = int(min(xs)) - 2, int(min(ys)) - 2
            w = int(max(xs)) - min_x + 4
            h = int(max(ys)) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)

    @staticmethod
    def _ellipse(surface, color, rect, width=0):
        color = _NS_ignis_drachorn._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, int(rw), int(rh)), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)

    @staticmethod
    def _rect(surface, color, rect, border_radius=0):
        color = _NS_ignis_drachorn._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, int(rw), int(rh)),
                             border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect,
                         border_radius=border_radius)

    @staticmethod
    def _ring(surface, center, radius, width, color, alpha):
        """Cincin dua lapis (gelap di luar) supaya tidak jadi kawat 1 px."""
        alpha = _NS_ignis_drachorn._alpha(alpha)
        if alpha <= 0:
            return
        cx, cy = int(center[0]), int(center[1])
        r = int(radius)
        if r <= 0:
            return
        _NS_ignis_drachorn._aacircle(surface, (10, 4, 4, alpha // 2),
                                     (cx, cy), r + 1, max(1, width + 2))
        _NS_ignis_drachorn._aacircle(surface, (*color, alpha), (cx, cy), r,
                                     max(1, width))

    @staticmethod
    def _spark_star(surface, cx, cy, size, color, alpha, spikes=8, rot=0.3,
                    core=None):
        """Bintang percikan (bukan lingkaran) untuk flash & impact."""
        alpha = _NS_ignis_drachorn._alpha(alpha)
        if alpha <= 0 or size <= 0:
            return
        for k in range(spikes):
            ang = rot + k * math.pi * 2 / spikes
            ln = size * (1.0 if k % 2 == 0 else 0.5)
            _NS_ignis_drachorn._aaline(
                surface, (*color, alpha), (int(cx), int(cy)),
                (int(cx + math.cos(ang) * ln),
                 int(cy + math.sin(ang) * ln * 0.85)),
                2 if k % 2 == 0 else 1)
        if core:
            _NS_ignis_drachorn._aacircle(surface, (*core, alpha),
                                         (int(cx), int(cy)),
                                         max(1, int(size * 0.28)))

    @staticmethod
    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        """Chevron terarah — telegraph yang bukan lingkaran."""
        alpha = _NS_ignis_drachorn._alpha(alpha)
        if alpha <= 0 or size <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        tipx, tipy = cx + ca * size, cy + sa * size
        for s in (-1, 1):
            _NS_ignis_drachorn._aaline(
                surface, (*color, alpha),
                (int(cx + px * s * size * 0.55 - ca * size * 0.5),
                 int(cy + py * s * size * 0.55 - sa * size * 0.5)),
                (int(tipx), int(tipy)), width)

    @staticmethod
    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=10, thick=3, span=0.6, squash=0.42):
        """Cincin tanah putus-putus (perspektif pipih)."""
        alpha = _NS_ignis_drachorn._alpha(alpha)
        if alpha <= 0 or radius <= 1:
            return
        for i in range(segments):
            a0 = phase + i * math.pi * 2 / segments
            a1 = a0 + math.pi * 2 / segments * span
            p0 = (cx + math.cos(a0) * radius,
                  cy + math.sin(a0) * radius * squash)
            p1 = (cx + math.cos(a1) * radius,
                  cy + math.sin(a1) * radius * squash)
            _NS_ignis_drachorn._aaline(surface, (*color, alpha), p0, p1,
                                       thick)

    @staticmethod
    def _jagged_crack(surface, x0, y0, x1, y1, color, alpha, width=2,
                      segments=4, max_dev=5.0, seed=0):
        """Retakan magma bergerigi deterministik."""
        alpha = _NS_ignis_drachorn._alpha(alpha)
        if alpha <= 0:
            return
        dx = x1 - x0
        dy = y1 - y0
        dist = math.hypot(dx, dy)
        if dist < 2.0:
            return
        nx, ny = -dy / dist, dx / dist
        pts = [(x0, y0)]
        for k in range(1, segments):
            t = k / float(segments)
            h = _NS_ignis_drachorn._hash01(seed + k * 17) * 2.0 - 1.0
            dev = h * max_dev * math.sin(t * math.pi)
            pts.append((x0 + dx * t + nx * dev, y0 + dy * t + ny * dev))
        pts.append((x1, y1))
        for i in range(len(pts) - 1):
            _NS_ignis_drachorn._aaline(surface, (*color, alpha), pts[i],
                                       pts[i + 1], width)

    @staticmethod
    def _tuft_points(spine, depth=4.0, seed=0):
        """Ubah tulang punggung jadi poligon compang-camping (jubah)."""
        if len(spine) < 2:
            return list(spine)
        left_pts = []
        right_pts = []
        for i in range(len(spine)):
            x, y = spine[i]
            if i < len(spine) - 1:
                dx = spine[i + 1][0] - x
                dy = spine[i + 1][1] - y
            else:
                dx = x - spine[i - 1][0]
                dy = y - spine[i - 1][1]
            dist = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / dist, dx / dist
            d = depth * (0.6 + 0.4 * _NS_ignis_drachorn._hash01(seed + i * 19))
            left_pts.append((x - nx * d, y - ny * d))
            right_pts.append((x + nx * d, y + ny * d))
        return left_pts + right_pts[::-1]

    @staticmethod
    def _dither_dots(surface, color, rect, pattern=0):
        """Band dither 2x2 — transisi nilai ala pixel art."""
        color = _NS_ignis_drachorn._clamp(color)
        rx, ry, rw, rh = int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])
        sw, sh = surface.get_size()
        for dy in range(rh):
            yy = ry + dy
            if yy < 0 or yy >= sh:
                continue
            for dx in range(rw):
                xx = rx + dx
                if xx < 0 or xx >= sw:
                    continue
                if (dx + dy + pattern) % 2 == 0:
                    surface.set_at((xx, yy), color)

    # ---------------------------------------------------------------------------
    # 3. KONVERSI KOORDINAT (hero-lane aware)
    # ---------------------------------------------------------------------------
    @staticmethod
    def _target_position(boss, x, y):
        """Posisi target dalam ruang gambar (kompensasi _render_scale)."""
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return (int(x + 200 / scale * getattr(boss, "direction", 1)), int(y))

    @staticmethod
    def _world_to_local(boss, x, y, wx, wy):
        """Titik DUNIA -> ruang gambar, dibatasi agar tidak keluar canvas."""
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(wx), int(wy)
        scale = float(scale) or 1.0
        ox = (float(wx) - float(getattr(boss, "x", x))) / scale
        oy = (float(wy) - float(getattr(boss, "y", y))) / scale
        rng = int(getattr(boss, "range", 180) or 180)
        half = max(140, int(rng / scale) + 40)
        max_off = half - 20
        d = math.hypot(ox, oy)
        if d > max_off and d > 0.001:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    @staticmethod
    def _fx_scale(boss):
        """Pengali ukuran FX supaya efek tidak menyusut di hero-lane."""
        scale = getattr(boss, "_render_scale", None)
        if not scale:
            return 1.0
        return max(1.0, min(2.6, 1.0 / float(scale)))

    @staticmethod
    def _ring_r(boss, world_px, surface):
        """Radius dunia -> radius gambar, di-clamp ke ukuran canvas."""
        scale = getattr(boss, "_render_scale", None)
        r = float(world_px) / float(scale) if scale else float(world_px)
        margin = min(surface.get_width(), surface.get_height()) // 2 - 10
        return int(max(4, min(r, margin)))

    # ---------------------------------------------------------------------------
    # 4. DECAL ENGINE (primitif tanah ber-cache)
    # ---------------------------------------------------------------------------
    _DECAL_CACHE = {}
    _DECAL_ORDER = []

    @staticmethod
    def _decal(key, size, builder):
        hit = _NS_ignis_drachorn._DECAL_CACHE.get(key)
        if hit is not None:
            return hit
        surf = builder(size)
        _NS_ignis_drachorn._DECAL_CACHE[key] = surf
        _NS_ignis_drachorn._DECAL_ORDER.append(key)
        if len(_NS_ignis_drachorn._DECAL_ORDER) > 96:
            old = _NS_ignis_drachorn._DECAL_ORDER.pop(0)
            _NS_ignis_drachorn._DECAL_CACHE.pop(old, None)
        return surf

    @staticmethod
    def _blit_decal(surface, decal, cx, cy, alpha=255, add=False):
        """Blit decal; mode ``add`` MENGHORMATI alpha per-piksel.

        ``BLEND_RGB_ADD`` mengabaikan kanal alpha, jadi decal bergradien
        yang langsung di-ADD akan muncul sebagai cakram warna penuh
        bertepi keras. Untuk mode add decal di-"premultiply" dulu (blit
        normal ke atas hitam) supaya cahayanya benar-benar meluruh.
        """
        NS = _NS_ignis_drachorn
        alpha = NS._alpha(alpha)
        if alpha <= 0 or decal is None:
            return
        w, h = decal.get_size()
        x0 = int(cx) - w // 2
        y0 = int(cy) - h // 2
        if not add:
            if alpha < 255:
                decal = decal.copy()
                decal.set_alpha(alpha)
            surface.blit(decal, (x0, y0))
            return
        buf = NS._premul_buf
        if buf is None or buf.get_width() < w or buf.get_height() < h:
            buf = pygame.Surface((max(w, 256), max(h, 256)))
            NS._premul_buf = buf
        sub = buf.subsurface((0, 0, w, h))
        sub.fill((0, 0, 0))
        sub.blit(decal, (0, 0))
        if alpha < 255:
            sub.fill((alpha, alpha, alpha, 255),
                     special_flags=pygame.BLEND_RGB_MULT)
        surface.blit(sub, (x0, y0), special_flags=pygame.BLEND_RGB_ADD)

    @staticmethod
    def _glow_decal(radius, color):
        """Cahaya radial lembut ter-cache (falloff kuadratik)."""
        radius = max(3, int(radius))
        key = ("glow", radius, tuple(color[:3]))

        def build(_r):
            surf = pygame.Surface((radius * 2 + 2, radius * 2 + 2),
                                  pygame.SRCALPHA)
            c = radius + 1
            steps = max(4, radius // 2)
            for i in range(steps, 0, -1):
                t = i / float(steps)
                a = int(150 * (1.0 - t) ** 2)
                if a <= 0:
                    continue
                pygame.draw.circle(surf, (*color[:3], a), (c, c),
                                   max(1, int(radius * t)))
            return surf

        return _NS_ignis_drachorn._decal(key, radius, build)

    @staticmethod
    def _ground_pool_decal(radius, color):
        """Genangan cahaya PIPIH di tanah (elips, bukan bola merah)."""
        radius = max(4, int(radius))
        key = ("pool", radius, tuple(color[:3]))

        def build(_r):
            w = radius * 2 + 4
            h = int(radius * 0.7) + 4
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            steps = max(4, radius // 3)
            for i in range(steps, 0, -1):
                t = i / float(steps)
                a = int(90 * (1.0 - t) ** 1.7)
                if a <= 0:
                    continue
                rw = int(radius * t)
                rh = max(1, int(radius * 0.32 * t))
                pygame.draw.ellipse(surf, (*color[:3], a),
                                    (w // 2 - rw, h // 2 - rh, rw * 2,
                                     rh * 2))
            return surf

        return _NS_ignis_drachorn._decal(key, radius, build)

    @staticmethod
    def _ground_ring_decal(radius, color, thick=3):
        """Cincin tanah pipih dengan falloff (anti kawat 1 px)."""
        radius = max(4, int(radius))
        key = ("gring", radius, tuple(color[:3]), int(thick))

        def build(_r):
            w = radius * 2 + 6
            h = int(radius * 0.9) + 6
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            for i in range(thick, 0, -1):
                a = int(200 * (i / float(thick)) ** 0.6)
                rr = radius - (thick - i)
                pygame.draw.ellipse(
                    surf, (*color[:3], a),
                    (w // 2 - rr, h // 2 - int(rr * 0.36),
                     rr * 2, int(rr * 0.72)), 1)
            return surf

        return _NS_ignis_drachorn._decal(key, radius, build)

    @staticmethod
    def _scorch_decal(radius, seed=0):
        """Patch tanah hangus organik (blob deterministik)."""
        radius = max(6, int(radius))
        key = ("scorch", radius, int(seed))
        P = _NS_ignis_drachorn.PALETTE

        def build(_r):
            w = radius * 2 + 8
            h = int(radius * 1.0) + 8
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            cx, cy = w // 2, h // 2
            for i in range(12):
                a = _NS_ignis_drachorn._hash01(seed * 31 + i) * math.tau
                d = _NS_ignis_drachorn._hash01(seed * 17 + i * 7) * radius * 0.7
                rr = int(radius * (0.28 + 0.3 *
                                   _NS_ignis_drachorn._hash01(seed + i * 13)))
                pygame.draw.ellipse(
                    surf, (*P["smoke_dark"], 150),
                    (int(cx + math.cos(a) * d) - rr,
                     int(cy + math.sin(a) * d * 0.45) - rr // 2,
                     rr * 2, rr))
            for i in range(7):
                a = _NS_ignis_drachorn._hash01(seed * 7 + i * 3) * math.tau
                d = radius * (0.2 + 0.55 *
                              _NS_ignis_drachorn._hash01(seed + i * 5))
                pygame.draw.line(
                    surf, (*P["magma_mid"], 130),
                    (cx, cy),
                    (int(cx + math.cos(a) * d),
                     int(cy + math.sin(a) * d * 0.45)), 2)
            return surf

        return _NS_ignis_drachorn._decal(key, radius, build)

    # ---------------------------------------------------------------------------
    # 5. JEMBATAN KE LAPISAN HIDUP (heroes/ignis_drachorn_fx.py)
    # ---------------------------------------------------------------------------
    @staticmethod
    def _live_module():
        """Muat ``heroes.ignis_drachorn_fx`` sekali; None kalau tak ada."""
        NS = _NS_ignis_drachorn
        if NS._LIVE_MOD is None:
            try:
                from heroes import ignis_drachorn_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "IGNIS_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    @staticmethod
    def live_fx_ready():
        return _NS_ignis_drachorn._live_module() is not None

    @staticmethod
    def _live_fx(boss, surface, x, y, want_draw, portrait):
        """Pasang/gambar lapisan hidup. Return (mod_untuk_draw, owned)."""
        NS = _NS_ignis_drachorn
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

    # ---------------------------------------------------------------------------
    # 6. ANIMATION CONTROLLER
    #    Satu-satunya sumber kebenaran state/fase/timing. Lapisan hidup,
    #    overlay debug, dan alat uji membacanya dari sini.
    # ---------------------------------------------------------------------------
    @staticmethod
    def _detect_moving(boss):
        if not hasattr(boss, "_ign_last_x"):
            boss._ign_last_x = boss.x
            boss._ign_last_y = boss.y
            boss._ign_speed = 0.0
            return False
        dx = abs(boss.x - boss._ign_last_x)
        dy = abs(boss.y - boss._ign_last_y)
        boss._ign_last_x = boss.x
        boss._ign_last_y = boss.y
        boss._ign_speed = dx + dy
        return (dx + dy) > 0.3

    @staticmethod
    def _ease(kind, t):
        if t <= 0.0:
            return 0.0
        if t >= 1.0:
            return 1.0
        if kind == "out":
            return 1.0 - (1.0 - t) * (1.0 - t)
        if kind == "oc":                              # out-cubic (cepat)
            return 1.0 - (1.0 - t) ** 3
        if kind == "in":
            return t * t
        if kind == "hold":
            return math.sin(t * math.pi * 0.5)
        return t * t * (3.0 - 2.0 * t)                # in-out (smoothstep)

    @staticmethod
    def attack_phases_order():
        return tuple(name for name, _a, _b in
                     _NS_ignis_drachorn.ATTACK_PHASES)

    @staticmethod
    def attack_phase(progress):
        """Nama fase serangan untuk progress 0..1."""
        p = max(0.0, min(1.0, float(progress)))
        for name, a, b in _NS_ignis_drachorn.ATTACK_PHASES:
            if a <= p < b:
                return name
        return "RECOVERY"

    @staticmethod
    def _sword_lift(progress):
        """Ketinggian relatif kedua tangan saat mengayun (0..1)."""
        p = max(0.0, min(1.0, float(progress)))
        E = _NS_ignis_drachorn._ease
        if p < 0.30:
            return E("out", p / 0.30)
        if p < 0.50:
            return 1.0 - E("oc", (p - 0.30) / 0.20) * 0.95
        if p < 0.82:
            return 0.05 + E("io", (p - 0.50) / 0.32) * 0.18
        return 0.23 * (1.0 - E("io", (p - 0.82) / 0.18))

    @staticmethod
    def _sword_arc(progress):
        """(theta, lift) ark greatsword — SATU sumber kebenaran.

        theta = sudut bilah dari sumbu ATAS (rad), positif ke arah facing.
        Tabel bersambung, jadi tidak pernah ada teleport senjata.
        """
        p = max(0.0, min(1.0, float(progress)))
        NS = _NS_ignis_drachorn
        for t0, t1, a0, a1, kind in NS.SWORD_ARC:
            if t0 <= p < t1 or (p >= 1.0 and t1 >= 1.0):
                e = NS._ease(kind, (p - t0) / max(0.0001, t1 - t0))
                return a0 + (a1 - a0) * e, NS._sword_lift(p)
        return NS.SWORD_ARC[0][2], 0.0

    @staticmethod
    def _lunge_offset(progress):
        """Dorongan badan ke depan (px) mengikuti bobot ayunan."""
        p = max(0.0, min(1.0, float(progress)))
        E = _NS_ignis_drachorn._ease
        if p < 0.12:
            return -1.5 * E("out", p / 0.12)          # anticipation mundur
        if p < 0.30:
            return -1.5 - 2.0 * E("io", (p - 0.12) / 0.18)
        if p < 0.50:
            return -3.5 + 12.0 * E("oc", (p - 0.30) / 0.20)
        if p < 0.62:
            return 8.5 + 1.5 * E("hold", (p - 0.50) / 0.12)
        if p < 0.82:
            return 10.0 - 7.0 * E("io", (p - 0.62) / 0.20)
        return 3.0 * (1.0 - E("io", (p - 0.82) / 0.18))

    @staticmethod
    def sword_geometry(facing, action, phase, ap=0.0):
        """(grip, tip, theta) sebagai OFFSET lokal dari jangkar badan.

        Dipakai renderer (menggambar pedang) DAN lapisan hidup (trail +
        titik lahir proyektil) supaya bilah dan trail tidak mungkin
        berbeda satu frame pun.
        """
        NS = _NS_ignis_drachorn
        f = 1 if facing >= 0 else -1
        L = NS.BLADE_LEN

        if action in ("melee", "attack", "swing"):
            theta, lift = NS._sword_arc(ap)
            lunge = NS._lunge_offset(ap)
            gx = f * (NS.GRIP_LOCAL[0] + 7.0 * lift + lunge * 0.55)
            gy = NS.GRIP_LOCAL[1] - 4.0 - 15.0 * lift
        elif action == "ranged":
            t = max(0.0, min(1.0, ap))
            theta = 1.15 - 0.55 * math.sin(t * math.pi)
            lift = 0.55 + 0.25 * math.sin(t * math.pi)
            gx = f * (NS.GRIP_LOCAL[0] + 8.0)
            gy = NS.GRIP_LOCAL[1] - 16.0
        elif action in ("cast", "skill", "charge"):
            sway = math.sin(phase * 2.2) * 0.06
            theta = 0.10 + sway
            lift = 0.9
            gx = f * 10.0
            gy = -18.0
        elif action in ("walk", "run"):
            sway = math.sin(phase * 1.1) * 0.10
            theta = 2.30 + sway
            lift = 0.08
            gx = f * (NS.GRIP_LOCAL[0] + 1.0)
            gy = NS.GRIP_LOCAL[1] + 1.0
        else:                                          # idle / hurt / death
            sway = math.sin(phase * 0.8) * 0.05
            theta = 2.42 + sway
            lift = 0.0
            gx = f * NS.GRIP_LOCAL[0]
            gy = NS.GRIP_LOCAL[1] + math.sin(phase * 0.8) * 0.8

        tx = gx + f * math.sin(theta) * L
        ty = gy - math.cos(theta) * L
        return (gx, gy), (tx, ty), theta

    @staticmethod
    def _update_ignis_anim(boss, moving=False):
        """Controller: delta time, state + prioritas, timeline serangan."""
        NS = _NS_ignis_drachorn

        # ── delta time nyata ────────────────────────────────────────
        try:
            now = pygame.time.get_ticks()
        except Exception:                              # pragma: no cover
            now = 0
        prev_ms = getattr(boss, "_ign_last_ms", None)
        if prev_ms is None:
            dt = 1.0 / 60.0
        else:
            dt = (now - prev_ms) / 1000.0
            if dt <= 0.0 or dt > 0.05:
                dt = 1.0 / 60.0
        boss._ign_last_ms = now
        boss._ign_dt = dt

        # ── timeline serangan (timer engine menghitung MUNDUR) ──────
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 42)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_ign_prev_timer", 0))
        active = bool(getattr(boss, "_ign_attack_active", False))

        # serangan baru: timer melonjak naik (di-reset ke cooldown)
        if timer > previous + 1 and timer >= cooldown - 2:
            boss._ign_attack_active = True
            boss._ign_attack_frame = 0
            boss._ign_proj_spawned = False
            active = True
        elif active:
            boss._ign_attack_frame = int(
                getattr(boss, "_ign_attack_frame", 0)) + 1
            if boss._ign_attack_frame > cooldown:
                boss._ign_attack_active = False
                boss._ign_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._ign_attack_active = False
            boss._ign_attack_frame = 0
            active = False

        boss._ign_prev_timer = timer
        frame = int(getattr(boss, "_ign_attack_frame", 0))
        # durasi animasi serangan dibatasi agar ayunan tetap punya bobot
        anim_len = max(10, min(cooldown - 1, 34))
        progress = min(1.0, frame / float(anim_len)) if active else 0.0
        boss._ign_attack_progress = progress
        boss._ign_attack_phase = (NS.attack_phase(progress) if active
                                  else "NONE")
        lo, hi = NS.ATTACK_ACTIVE_WINDOW
        boss._ign_hit_window = bool(active and lo <= progress <= hi)

        # ── prioritas state ─────────────────────────────────────────
        skill = getattr(boss, "active_skill", None)
        alive = bool(getattr(boss, "alive", True))
        hurt = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        speed = float(getattr(boss, "_ign_speed", 0.0))

        if not alive:
            state = "DEATH"
        elif skill == "r":
            state = "SPECIAL"
        elif skill in ("q", "w", "e"):
            state = "SKILL"
        elif active and progress < 0.30:
            state = "CHARGE" if progress < 0.12 else "ATTACK"
        elif active:
            state = "SWING" if progress < 0.62 else "ATTACK"
        elif hurt > 0:
            state = "HURT"
        elif moving:
            state = "RUN" if speed > 1.6 else "WALK"
        else:
            state = "IDLE"

        prev_state = getattr(boss, "_ign_state", "IDLE")
        if prev_state != state:
            boss._ign_state_prev = prev_state
            boss._ign_state_time = 0.0
        else:
            boss._ign_state_time = getattr(boss, "_ign_state_time", 0.0) + dt
        boss._ign_state = state
        boss._ign_state_priority = NS.ANIM_STATES.get(state, 0)
        return state

    @staticmethod
    def _resolve_pose(boss, moving):
        """(action, phase, attack_progress) untuk renderer + FX."""
        NS = _NS_ignis_drachorn
        pulse = float(getattr(boss, "pulse", 0.0))
        state = getattr(boss, "_ign_state", "IDLE")
        ap = float(getattr(boss, "_ign_attack_progress", 0.0) or 0.0)
        skill = getattr(boss, "active_skill", None)
        attack_range = float(getattr(boss, "attack_range",
                                     getattr(boss, "range", 55)) or 55)

        if state in ("SKILL", "SPECIAL"):
            return "cast", pulse, 0.0
        if state in ("ATTACK", "SWING", "CHARGE"):
            if attack_range > 120:
                return "ranged", pulse, ap
            return "melee", pulse, ap
        if state == "RUN":
            return "run", pulse * 2.6, 0.0
        if state == "WALK":
            return "walk", pulse * 2.2, 0.0
        if state == "DEATH":
            return "death", pulse, 0.0
        if state == "HURT":
            return "hurt", pulse, 0.0
        _ = skill
        return "idle", pulse, 0.0

    # ---------------------------------------------------------------------------
    # 7. PROJECTILE (fallback canvas — dipakai bila lapisan hidup absen)
    # ---------------------------------------------------------------------------
    class FireProjectile:
        """Bola api dari pedang.

        Lifecycle: SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT FX -> DESTROY.
        Atribut wajib lengkap (position/velocity/speed/damage/lifetime/
        target/radius/rotation/trail/particles/active) supaya API-nya sama
        dengan proyektil di lapisan hidup.
        """

        def __init__(self, sx, sy, tx, ty, speed=5.5, damage=0, target=None,
                     radius=7.0):
            self.position = pygame.Vector2(float(sx), float(sy))
            dx, dy = float(tx) - float(sx), float(ty) - float(sy)
            L = math.hypot(dx, dy) or 1.0
            self.velocity = pygame.Vector2(dx / L, dy / L)
            self.speed = float(speed)
            self.damage = damage
            self.target = target
            self.radius = float(radius)
            self.rotation = math.atan2(dy, dx)
            self.lifetime = 180
            self.trail = []
            self.particles = []
            self.active = True
            # kompatibilitas nama lama
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.alive = True
            self.age = 0
            self.impact = 0

        def update(self):
            if not self.active:
                if self.impact > 0:
                    self.impact -= 1
                return
            self.age += 1
            if self.age > self.lifetime:
                self._destroy()
                return
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.hypot(dx, dy)
            if dist < self.speed + 4:
                self._destroy()
                return
            self.trail.append((self.x, self.y))
            if len(self.trail) > 12:
                self.trail.pop(0)
            self.velocity.update(dx / dist, dy / dist)
            self.rotation = math.atan2(dy, dx)
            self.x += self.velocity.x * self.speed
            self.y += self.velocity.y * self.speed
            self.position.update(self.x, self.y)

        def _destroy(self):
            self.active = False
            self.alive = False
            self.impact = 10

        def draw(self, surface, phase):
            NS = _NS_ignis_drachorn
            P = NS.PALETTE
            n = len(self.trail)
            for i, (tx, ty) in enumerate(self.trail):
                t = (i + 1) / max(1, n)
                alpha = int(30 + 150 * t)
                r = max(1, int(1 + 4 * t))
                NS._aacircle(surface, (*P["fire_darkest"], alpha // 2),
                             (int(tx), int(ty)), r + 2)
                NS._aacircle(surface, (*P["fire_mid"], alpha),
                             (int(tx), int(ty)), r)
                NS._aacircle(surface, (*P["fire_hot"], alpha),
                             (int(tx), int(ty)), max(1, r - 2))

            if self.active:
                px, py = int(self.x), int(self.y)
                ca, sa = math.cos(self.rotation), math.sin(self.rotation)
                # bentuk terarah (tetesan api) — bukan lingkaran polos
                nose = (px + ca * 13, py + sa * 13)
                tail = (px - ca * 15, py - sa * 15)
                perp = (-sa * 6.0, ca * 6.0)
                NS._poly(surface, P["fire_dark"],
                         [nose, (px + perp[0], py + perp[1]), tail,
                          (px - perp[0], py - perp[1])])
                NS._poly(surface, P["fire_mid"],
                         [(px + ca * 10, py + sa * 10),
                          (px + perp[0] * 0.6, py + perp[1] * 0.6),
                          (px - ca * 10, py - sa * 10),
                          (px - perp[0] * 0.6, py - perp[1] * 0.6)])
                NS._draw_flame_puff(surface, px, py, 6, phase, 235)
                NS._aacircle(surface, P["fire_white"],
                             (int(px + ca * 4), int(py + sa * 4)), 2)
                for i in range(3):
                    angle = phase * 5 + i * math.pi * 2 / 3
                    sx = px + int(math.cos(angle) * 9)
                    sy = py + int(math.sin(angle) * 9)
                    NS._aacircle(surface, P["fire_hot"], (sx, sy), 1)
            elif self.impact > 0:
                t = self.impact / 10.0
                px, py = int(self.x), int(self.y)
                NS._spark_star(surface, px, py, int(6 + 16 * (1 - t)),
                               P["fire_bright"], int(220 * t), 8,
                               0.4, P["fire_white"])
                NS._ring(surface, (px, py), int(6 + 18 * (1 - t)), 2,
                         P["fire_light"], int(180 * t))

    # ── state proyektil fallback ────────────────────────────────────
    @staticmethod
    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_ign_projectiles"):
            boss._ign_projectiles = []
        for proj in boss._ign_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._ign_projectiles = [p for p in boss._ign_projectiles
                                 if p.active or p.impact > 0]
        if len(boss._ign_projectiles) > 16:
            del boss._ign_projectiles[:-16]

    @staticmethod
    def _spawn_fire_projectile(boss, x, y):
        NS = _NS_ignis_drachorn
        if not hasattr(boss, "_ign_projectiles"):
            boss._ign_projectiles = []
        tx, ty = NS._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        action = getattr(boss, "_ign_pose_action", "ranged")
        ap = float(getattr(boss, "_ign_attack_progress", 0.0) or 0.0)
        phase = float(getattr(boss, "pulse", 0.0))
        _grip, tip, _th = NS.sword_geometry(facing, action, phase, ap)
        boss._ign_projectiles.append(
            NS.FireProjectile(x + tip[0], y + tip[1], tx, ty, speed=6.2,
                              target=getattr(boss, "target", None)))

    @staticmethod
    def _update_attack_anim(boss):
        """Kompatibilitas API lama — delegasi ke controller baru."""
        _NS_ignis_drachorn._update_ignis_anim(
            boss, bool(getattr(boss, "_ign_speed", 0.0) > 0.3))

    # ---------------------------------------------------------------------------
    # 8. FLAME HELPER
    # ---------------------------------------------------------------------------
    @staticmethod
    def _draw_flame_puff(surface, x, y, size, phase, alpha=255):
        """Kepulan api berlapis (chunky, bukan gradasi halus)."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        flick = math.sin(phase * 3 + x * 0.07) * 0.15 + 1.0
        s = int(size * flick)
        if s < 1:
            return
        x, y = int(x), int(y)
        NS._aacircle(surface, (*P["fire_darkest"], alpha // 3), (x, y), s + 3)
        NS._aacircle(surface, (*P["fire_dark"], alpha // 2), (x, y), s + 1)
        NS._aacircle(surface, (*P["fire_mid"], alpha), (x, y), s)
        NS._aacircle(surface, (*P["fire_light"], alpha), (x, y - 1),
                     max(1, s - 2))
        NS._aacircle(surface, (*P["fire_bright"], min(255, alpha)),
                     (x, y - 2), max(1, s - 4))
        if s > 4:
            NS._aacircle(surface, (*P["fire_hot"], min(255, alpha)),
                         (x, y - 3), max(1, s - 6))
        if s > 7:
            NS._aacircle(surface, (*P["fire_white"], min(255, alpha)),
                         (x, y - 4), max(1, s - 9))

    @staticmethod
    def _flame_tongue(surface, x, y, h, phase, seed=0, alpha=255,
                      width=None):
        """Lidah api bergerigi (poligon), bukan lingkaran bertumpuk."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        h = max(3, int(h))
        w = float(width if width is not None else h * 0.55)
        wob = math.sin(phase * 3.4 + seed) * (w * 0.35)
        wob2 = math.sin(phase * 5.1 + seed * 1.7) * (w * 0.22)
        pts = [
            (x - w, y),
            (x - w * 0.55, y - h * 0.32),
            (x - w * 0.75 + wob2, y - h * 0.6),
            (x + wob, y - h),
            (x + w * 0.72 + wob2, y - h * 0.58),
            (x + w * 0.5, y - h * 0.3),
            (x + w, y),
        ]
        NS._poly(surface, (*P["fire_dark"], alpha), pts)
        inner = [(x + (px - x) * 0.62, y + (py - y) * 0.72) for px, py in pts]
        NS._poly(surface, (*P["fire_mid"], alpha), inner)
        core = [(x + (px - x) * 0.34, y + (py - y) * 0.5) for px, py in pts]
        NS._poly(surface, (*P["fire_bright"], alpha), core)
        NS._aacircle(surface, (*P["fire_hot"], alpha),
                     (int(x + wob * 0.4), int(y - h * 0.48)),
                     max(1, int(w * 0.3)))

    # ---------------------------------------------------------------------------
    # 9. GROUND / AURA LAYERS
    # ---------------------------------------------------------------------------
    @staticmethod
    def _draw_shadow(surface, x, y, width=54):
        NS = _NS_ignis_drachorn
        w = int(width)
        h = max(6, int(w * 0.26))
        rect = (int(x) - w // 2, int(y) - h // 2, w, h)
        NS._ellipse(surface, (0, 0, 0, 118), rect)
        NS._ellipse(surface, (0, 0, 0, 70),
                    (rect[0] - 4, rect[1] + 1, w + 8, h))
        if NS._record_shadow is not None:
            NS._record_shadow.append(pygame.Rect(rect[0] - 5, rect[1] - 1,
                                                 w + 10, h + 3))

    @staticmethod
    def _draw_fire_aura(surface, x, y, phase, skill=None):
        """Aura panas di sekitar sovereign (additive, murah, ter-cache)."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        pulse = math.sin(phase * 1.6) * 0.18 + 0.82
        boost = 1.3 if skill else 1.0
        pool = NS._ground_pool_decal(int(34 * boost), P["fire_dark"])
        NS._blit_decal(surface, pool, x, y + 44,
                       int(120 * pulse * boost), add=True)
        pool2 = NS._ground_pool_decal(int(18 * boost), P["magma_dark"])
        NS._blit_decal(surface, pool2, x, y + 46,
                       int(110 * pulse * boost), add=True)
        # panas tipis di belakang badan (tidak menutupi siluet)
        NS._blit_decal(surface, NS._glow_decal(14, P["fire_darkest"]),
                       x, y - 6, int(26 * pulse * boost), add=True)

    @staticmethod
    def _draw_ground_embers(surface, x, y, phase, skill=None):
        """Bara & retakan magma yang merayap di tanah bawah kaki."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        pulse = math.sin(phase * 2.0) * 0.25 + 0.75
        r = 30 if not skill else 40
        NS._blit_decal(surface, NS._scorch_decal(r, seed=3), x, y,
                       int(120 * pulse))
        for i in range(6):
            a = phase * 0.5 + i * math.pi / 3
            ex = x + int(math.cos(a) * (r * 0.72))
            ey = y + int(math.sin(a) * (r * 0.3))
            fl = (math.sin(phase * 4 + i * 1.7) * 0.5 + 0.5)
            NS._aacircle(surface, (*P["magma_hot"], int(120 + 100 * fl)),
                         (ex, ey), 1 + int(fl * 1.6))
        NS._dashed_ring(surface, x, y, r, P["magma_mid"],
                        int(80 * pulse), phase * 0.35, 9, 2, 0.45)

    @staticmethod
    def _draw_floating_flames(surface, cx, cy, phase, trail=False, facing=1,
                              intense=False):
        """Api melayang di sekitar kaki (legacy signature dipertahankan)."""
        NS = _NS_ignis_drachorn
        count = 5 if intense else 3
        for i in range(count):
            t = (phase * 0.7 + i * 0.9) % 2.4
            a = i * 2.399 + phase * 0.5
            rad = 8 + i * 4
            fx = cx + int(math.cos(a) * rad) - (int(t * 5) * facing
                                                if trail else 0)
            fy = cy + 6 - int(t * 8) + int(math.sin(a) * 2)
            alpha = int(max(0, 190 * (1.0 - t / 2.4)))
            if alpha <= 6:
                continue
            NS._flame_tongue(surface, fx, fy,
                             (6 if intense else 4) + int((2.4 - t) * 1.2),
                             phase, seed=i * 3, alpha=alpha, width=2.6)

    @staticmethod
    def _draw_body_fire_particles(surface, cx, cy, phase):
        """Bara yang naik dari pelat badan (legacy name)."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        for i in range(6):
            t = (phase * 0.8 + i * 0.62) % 1.0
            a = i * 1.9 + phase * 0.35
            px = cx + int(math.cos(a) * (12 + i * 2))
            py = cy + 10 - int(t * 42)
            alpha = int(200 * (1.0 - t))
            if alpha <= 5:
                continue
            NS._aacircle(surface, (*P["fire_dark"], alpha // 2), (px, py), 2)
            NS._aacircle(surface, (*P["fire_bright"], alpha), (px, py), 1)

    # ---------------------------------------------------------------------------
    # 10. ANATOMI — dragon knight sovereign
    # ---------------------------------------------------------------------------
    @staticmethod
    def _draw_back_wing(surface, cx, cy, facing, phase, spread=0.0):
        """Sayap naga terlipat di punggung — penguat siluet."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        f = facing
        flap = math.sin(phase * 1.1) * 2.0 + spread * 8.0
        base_x = cx - f * 8
        base_y = cy - 20

        # tulang sayap (3 jari)
        joints = [
            (base_x - f * (12 + spread * 6), base_y - 12 - flap),
            (base_x - f * (22 + spread * 12), base_y + 2 - flap * 0.6),
            (base_x - f * (18 + spread * 10), base_y + 16 + flap * 0.3),
        ]
        membrane = [(base_x, base_y + 4)] + joints + [
            (base_x - f * 10, base_y + 18)]
        NS._poly(surface, P["wing_dark"], membrane)
        inner = [(base_x + (px - base_x) * 0.78,
                  base_y + (py - base_y) * 0.78) for px, py in membrane]
        NS._poly(surface, P["wing_mid"], inner)
        # urat membran menyala
        for jx, jy in joints:
            NS._aaline(surface, P["wing_light"], (base_x, base_y + 2),
                       (int(jx), int(jy)), 2)
            NS._aaline(surface, P["magma_dark"], (base_x, base_y + 2),
                       (int(jx), int(jy)), 1)
        # tepi bergerigi + cakar ujung
        for jx, jy in joints:
            NS._aacircle(surface, P["horn_dark"], (int(jx), int(jy)), 2)
            NS._aacircle(surface, P["horn_mid"], (int(jx), int(jy) - 1), 1)
        NS._poly(surface, P["wing_glow"], [
            (base_x - f * 4, base_y - 1),
            (base_x - f * 10, base_y - 7),
            (base_x - f * 7, base_y + 2)])

    @staticmethod
    def _draw_cape(surface, cx, cy, facing, phase, action):
        """Jubah crimson compang-camping — MENYAPU KE BELAKANG.

        Jubah sengaja asimetris (hanya sisi -facing) supaya siluet depan
        tetap dibaca sebagai pelat baja, bukan gumpalan bundar.
        """
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        wave = math.sin(phase * 0.9) * 3.0
        wave2 = math.sin(phase * 1.4 + 0.7) * 2.0
        gust = 7 if action in ("walk", "run") else 0
        gust += 5 if action in ("melee", "swing", "cast") else 0

        # tulang punggung jubah: dari bahu -> menyapu ke belakang-bawah
        spine = [
            (cx - f * 9, cy - 15),
            (cx - f * (15 + gust * 0.3), cy + 2 + wave2),
            (cx - f * (23 + gust * 0.7), cy + 20 + wave),
            (cx - f * (28 + gust), cy + 36 + wave2),
            (cx - f * (26 + gust * 1.2), cy + 47),
        ]
        outer = NS._tuft_points(spine, depth=10.0, seed=7)
        NS._poly(surface, P["red_darkest"], outer)
        mid = NS._tuft_points(
            [(cx + (px - cx) * 0.86, cy + (py - cy) * 0.92)
             for px, py in spine], depth=7.0, seed=13)
        NS._poly(surface, P["red_dark"], mid)
        inner = NS._tuft_points(
            [(cx + (px - cx) * 0.62, cy + (py - cy) * 0.8)
             for px, py in spine], depth=4.0, seed=21)
        NS._poly(surface, P["red_mid"], inner)

        # lipatan kain + dither transisi
        for i in range(len(spine) - 1):
            NS._aaline(surface, P["red_light"],
                       (spine[i][0] + f * 2, spine[i][1]),
                       (spine[i + 1][0] + f * 2, spine[i + 1][1]), 1)
        NS._aaline(surface, P["red_high"], (cx - f * 8, cy - 12),
                   (cx - f * 14, cy + 12), 1)
        NS._dither_dots(surface, P["red_dark"],
                        (cx - f * 20 - 4, cy + 14, 9, 7), 0)

        # ujung robek (segitiga tajam) di tepi bawah
        for i in range(4):
            bx = cx - f * (14 + i * 6)
            by = cy + 38 + i * 2 + wave2
            d = 5 + int(NS._hash01(i * 9 + 5) * 8)
            NS._poly(surface, P["red_darkest"],
                     [(bx - 4, by), (bx + 4, by), (bx - f * 1, by + d)])

        # mantel bahu (menutupi pangkal jubah) + trim emas
        NS._poly(surface, P["red_dark"], [
            (cx - 15, cy - 17), (cx + 15, cy - 17),
            (cx + 12, cy - 6), (cx - 12, cy - 6)])
        NS._poly(surface, P["red_mid"], [
            (cx - 13, cy - 16), (cx + 13, cy - 16),
            (cx + 10, cy - 8), (cx - 10, cy - 8)])
        NS._rect(surface, P["gold_darkest"], (cx - 16, cy - 18, 32, 4))
        NS._rect(surface, P["gold_dark"], (cx - 15, cy - 17, 30, 3))
        NS._rect(surface, P["gold_mid"], (cx - 14, cy - 17, 28, 2))
        NS._rect(surface, P["gold_light"], (cx - 10, cy - 17, 20, 1))
        # bros kepala naga di bahu depan
        NS._aacircle(surface, P["gold_dark"], (cx + f * 12, cy - 13), 4)
        NS._aacircle(surface, P["gold_mid"], (cx + f * 12, cy - 13), 3)
        NS._aacircle(surface, P["magma_hot"], (cx + f * 12, cy - 13), 1)

    @staticmethod
    def _draw_tail(surface, cx, cy, facing, phase):
        """Ekor naga pendek yang menjuntai ke belakang-bawah.

        Sengaja tidak horizontal: ekor mendatar membuat siluet terbaca
        sebagai "tongkat", jadi ekor dibuat melengkung turun di belakang
        kaki dan sebagian besar tertutup jubah.
        """
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        px, py = cx - f * 8, cy + 16
        pts = [(px, py)]
        for i in range(1, 5):
            t = i / 4.0
            sway = math.sin(phase * 1.2 - i * 0.7) * (1.5 + i * 0.8)
            pts.append((px - f * (5 + int(7 * t)) - f * int(sway),
                        py + int(30 * t * t + 6 * t)))
        for i in range(len(pts) - 1):
            th = max(2, 8 - i * 2)
            NS._aaline(surface, P["dragon_darkest"], pts[i], pts[i + 1],
                       th + 2)
            NS._aaline(surface, P["dragon_dark"], pts[i], pts[i + 1], th)
            NS._aaline(surface, P["dragon_mid"],
                       (pts[i][0] - 1, pts[i][1]),
                       (pts[i + 1][0] - 1, pts[i + 1][1]), max(1, th - 3))
        for i in range(1, 4):
            sx, sy = pts[i]
            NS._poly(surface, P["horn_dark"], [
                (sx - 3, sy - 1), (sx + 1, sy - 2), (sx - f * 5, sy - 6)])
        tipx, tipy = pts[-1]
        NS._poly(surface, P["horn_mid"], [
            (tipx - 3, tipy - 2), (tipx + 3, tipy - 1),
            (tipx - f * 4, tipy + 7)])
        NS._aacircle(surface, (*P["magma_mid"], 190),
                     (int(tipx), int(tipy)), 2)

    @staticmethod
    def _draw_leg(surface, hx, hy, knee_x, knee_y, foot_x, foot_y, facing,
                  shade=0):
        """Kaki berpelat: paha -> lutut berduri -> tulang kering -> cakar."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        dark = (P["obsidian_darkest"] if shade else P["obsidian_dark"])
        mid = (P["obsidian_dark"] if shade else P["obsidian_mid"])
        light = (P["obsidian_mid"] if shade else P["obsidian_light"])

        NS._aaline(surface, P["shadow_deep"], (hx + 1, hy + 1),
                   (knee_x + 1, knee_y + 1), 11)
        NS._aaline(surface, dark, (hx, hy), (knee_x, knee_y), 10)
        NS._aaline(surface, mid, (hx, hy), (knee_x, knee_y), 7)
        NS._aaline(surface, light, (hx - 1, hy), (knee_x - 1, knee_y), 3)

        NS._aaline(surface, dark, (knee_x, knee_y), (foot_x, foot_y), 8)
        NS._aaline(surface, mid, (knee_x, knee_y), (foot_x, foot_y), 5)
        NS._aaline(surface, light, (knee_x - 1, knee_y),
                   (foot_x - 1, foot_y), 2)

        # pelat lutut berduri
        NS._aacircle(surface, P["obsidian_darkest"], (knee_x, knee_y), 6)
        NS._aacircle(surface, mid, (knee_x, knee_y), 5)
        NS._aacircle(surface, P["gold_dark"], (knee_x, knee_y), 3)
        NS._poly(surface, P["horn_dark"], [
            (knee_x - 3, knee_y - 1), (knee_x + 3, knee_y - 1),
            (knee_x + facing * 8, knee_y - 6)])
        NS._poly(surface, P["horn_light"], [
            (knee_x - 1, knee_y - 2), (knee_x + 2, knee_y - 2),
            (knee_x + facing * 6, knee_y - 5)])

        # sabaton bercakar
        NS._poly(surface, P["obsidian_darkest"], [
            (foot_x - 6, foot_y - 4), (foot_x + 7, foot_y - 4),
            (foot_x + facing * 11, foot_y + 2), (foot_x + 6, foot_y + 4),
            (foot_x - 7, foot_y + 4)])
        NS._poly(surface, mid, [
            (foot_x - 4, foot_y - 3), (foot_x + 5, foot_y - 3),
            (foot_x + facing * 8, foot_y + 1), (foot_x + 4, foot_y + 2),
            (foot_x - 5, foot_y + 2)])
        for c in (-3, 0, 3):
            NS._poly(surface, P["horn_light"], [
                (foot_x + c, foot_y + 1), (foot_x + c + 2, foot_y + 1),
                (foot_x + c + facing * 4, foot_y + 4)])
        # seam magma di tulang kering
        NS._aaline(surface, P["magma_mid"],
                   (knee_x + facing, knee_y + 3),
                   (foot_x + facing, foot_y - 4), 1)

    @staticmethod
    def _draw_lower_body(surface, cx, cy, phase, facing=1, action="idle",
                         step=0.0):
        """Pinggul + rok pelat naga + kedua kaki (legacy name)."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        sway = int(math.sin(phase * 0.7) * 2)
        f = 1 if facing >= 0 else -1

        # ── kaki (di belakang rok) ─────────────────────────────────
        if action in ("walk", "run"):
            sw = math.sin(step)
            back = (int(-sw * 9), int(abs(math.sin(step + math.pi)) * -6))
            front = (int(sw * 9), int(abs(math.sin(step)) * -6))
        elif action in ("melee", "swing"):
            back = (-8, 0)
            front = (10, 0)
        elif action == "ranged":
            back = (-6, 0)
            front = (7, 0)
        else:
            back = (-5, 0)
            front = (6, 0)

        hipy = cy + 6
        NS._draw_leg(surface, cx - 7, hipy,
                     cx - 8 + int(back[0] * 0.6) - f * 1, hipy + 17,
                     cx - 8 + back[0], hipy + 34 + back[1], f, shade=1)
        NS._draw_leg(surface, cx + 7, hipy,
                     cx + 8 + int(front[0] * 0.6) + f * 1, hipy + 17,
                     cx + 8 + front[0], hipy + 34 + front[1], f, shade=0)

        # ── rok pelat (pendek: kaki harus terbaca di siluet) ───────
        skirt = [
            (cx - 16, cy - 2), (cx + 16, cy - 2),
            (cx + 18 + sway, cy + 8), (cx + 12, cy + 17),
            (cx + 5, cy + 21), (cx - 5, cy + 21),
            (cx - 12, cy + 17), (cx - 18 - sway, cy + 8),
        ]
        NS._poly(surface, P["shadow_deep"],
                 [(p[0] + 2, p[1] + 2) for p in skirt])
        NS._poly(surface, P["obsidian_darkest"], skirt)
        NS._poly(surface, P["obsidian_dark"], [
            (cx - 14, cy), (cx + 14, cy),
            (cx + 15 + sway, cy + 8), (cx + 10, cy + 15),
            (cx + 4, cy + 18), (cx - 4, cy + 18),
            (cx - 10, cy + 15), (cx - 15 - sway, cy + 8)])
        NS._poly(surface, P["obsidian_mid"], [
            (cx - 10, cy + 2), (cx + 10, cy + 2),
            (cx + 11 + sway, cy + 8), (cx + 6, cy + 13),
            (cx - 6, cy + 13), (cx - 11 - sway, cy + 8)])

        # bilah tasset (pelat paha) — memecah rok jadi lempeng terbaca
        for side in (-1, 1):
            tx = cx + side * 12
            NS._poly(surface, P["obsidian_darkest"], [
                (tx - 4, cy + 3), (tx + 4, cy + 3),
                (tx + 3, cy + 16), (tx - 3, cy + 16)])
            NS._poly(surface, P["obsidian_light"], [
                (tx - 3, cy + 4), (tx - 1, cy + 4),
                (tx - 1, cy + 14), (tx - 3, cy + 14)])
            NS._aaline(surface, P["gold_dark"], (tx - 4, cy + 16),
                       (tx + 4, cy + 16), 2)

        # sisik naga pada rok (2 baris, offset selang-seling)
        for row in range(2):
            for col in range(-1, 2):
                sx = cx + col * 6 + (row % 2) * 3
                sy = cy + 4 + row * 5
                NS._aacircle(surface, P["dragon_dark"], (sx, sy), 3)
                NS._aacircle(surface, P["dragon_mid"], (sx, sy - 1), 2)
                NS._aacircle(surface, P["dragon_light"], (sx, sy - 1), 1)
        # seam magma antar pelat
        glow = int(150 + 80 * math.sin(phase * 2.2))
        NS._jagged_crack(surface, cx - 12, cy + 14, cx + 11, cy + 12,
                         P["magma_hot"], glow, 1, 4, 2.0, seed=11)

        # sabuk emas + gesper kepala naga
        NS._rect(surface, P["gold_darkest"], (cx - 20, cy - 2, 40, 7))
        NS._rect(surface, P["gold_dark"], (cx - 19, cy - 1, 38, 5))
        NS._rect(surface, P["gold_mid"], (cx - 17, cy, 34, 3))
        NS._rect(surface, P["gold_light"], (cx - 14, cy + 1, 28, 1))
        NS._poly(surface, P["dragon_darkest"], [
            (cx - 5, cy - 1), (cx + 5, cy - 1),
            (cx + 4, cy + 5), (cx, cy + 7), (cx - 4, cy + 5)])
        NS._poly(surface, P["dragon_mid"], [
            (cx - 4, cy), (cx + 4, cy),
            (cx + 3, cy + 4), (cx, cy + 6), (cx - 3, cy + 4)])
        eye_a = int(190 + 60 * math.sin(phase * 3.0))
        NS._aacircle(surface, (*P["eye_bright"], eye_a), (cx - 2, cy + 2), 1)
        NS._aacircle(surface, (*P["eye_bright"], eye_a), (cx + 2, cy + 2), 1)

    @staticmethod
    def _draw_torso(surface, cx, cy, phase, facing=1, breath=0.0):
        """Kuras dada obsidian + emblem naga + retakan magma."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        b = int(breath)

        NS._poly(surface, P["shadow_deep"], [
            (cx - 12, cy - 8), (cx + 16, cy - 8),
            (cx + 14, cy + 16), (cx + 7, cy + 21),
            (cx - 3, cy + 21), (cx - 10, cy + 16)])

        chest = [
            (cx - 15, cy - 11 - b), (cx + 15, cy - 11 - b),
            (cx + 13, cy + 14), (cx + 5, cy + 19),
            (cx - 5, cy + 19), (cx - 13, cy + 14),
        ]
        NS._poly(surface, P["obsidian_darkest"], chest)
        NS._poly(surface, P["obsidian_dark"], [
            (cx - 13, cy - 9 - b), (cx + 13, cy - 9 - b),
            (cx + 11, cy + 12), (cx + 4, cy + 16),
            (cx - 4, cy + 16), (cx - 11, cy + 12)])
        NS._poly(surface, P["obsidian_mid"], [
            (cx - 10, cy - 6 - b), (cx + 10, cy - 6 - b),
            (cx + 8, cy + 9), (cx + 3, cy + 13),
            (cx - 3, cy + 13), (cx - 8, cy + 9)])
        NS._poly(surface, P["obsidian_light"], [
            (cx - 8, cy - 4 - b), (cx - 2, cy - 5 - b),
            (cx - 3, cy + 6), (cx - 7, cy + 5)])
        NS._dither_dots(surface, P["obsidian_mid"],
                        (cx - 8, cy + 4, 7, 6), 1)

        # trim emas mengelilingi kuras
        for i in range(len(chest)):
            NS._aaline(surface, P["gold_darkest"], chest[i],
                       chest[(i + 1) % len(chest)], 3)
        for i in range(len(chest)):
            NS._aaline(surface, P["gold_dark"], chest[i],
                       chest[(i + 1) % len(chest)], 2)
        for i in range(len(chest)):
            NS._aaline(surface, P["gold_mid"], chest[i],
                       chest[(i + 1) % len(chest)], 1)

        # retakan magma di pelat (denyut jantung naga)
        pulse = math.sin(phase * 2.4) * 0.5 + 0.5
        glow = int(120 + 120 * pulse)
        NS._jagged_crack(surface, cx - 9, cy - 6, cx - 2, cy + 10,
                         P["magma_mid"], glow, 2, 4, 2.4, seed=5)
        NS._jagged_crack(surface, cx + 9, cy - 4, cx + 3, cy + 12,
                         P["magma_mid"], glow, 2, 4, 2.2, seed=9)
        NS._jagged_crack(surface, cx - 9, cy - 6, cx - 2, cy + 10,
                         P["magma_bright"], int(glow * 0.7), 1, 4, 2.4,
                         seed=5)

        # emblem naga (berlian merah dengan inti magma)
        NS._poly(surface, P["red_darkest"], [
            (cx, cy - 5), (cx + 7, cy + 4), (cx, cy + 13), (cx - 7, cy + 4)])
        NS._poly(surface, P["red_dark"], [
            (cx, cy - 3), (cx + 5, cy + 4), (cx, cy + 11), (cx - 5, cy + 4)])
        NS._poly(surface, P["red_mid"], [
            (cx, cy - 1), (cx + 3, cy + 4), (cx, cy + 9), (cx - 3, cy + 4)])
        core = int(150 + 105 * pulse)
        NS._aacircle(surface, (*P["magma_hot"], core), (cx, cy + 4), 3)
        NS._aacircle(surface, (*P["magma_bright"], core), (cx, cy + 4), 2)
        NS._aacircle(surface, (*P["magma_white"], core), (cx, cy + 3), 1)

        # gorget / kerah
        NS._poly(surface, P["obsidian_darkest"], [
            (cx - 9, cy - 12 - b), (cx + 9, cy - 12 - b),
            (cx + 7, cy - 7 - b), (cx - 7, cy - 7 - b)])
        NS._poly(surface, P["gold_dark"], [
            (cx - 7, cy - 11 - b), (cx + 7, cy - 11 - b),
            (cx + 6, cy - 9 - b), (cx - 6, cy - 9 - b)])
        NS._aacircle(surface, P["gold_light"], (cx, cy - 10 - b), 1)
        _ = facing

    @staticmethod
    def _draw_pauldrons(surface, cx, cy, phase, facing=1):
        """Bahu berkubah bertanduk — bagian terkuat dari siluet.

        Dibuat sebagai KUBAH (poligon membulat) dengan dua lame di
        bawahnya, bukan balok lebar: balok membuat bahu menyatu jadi
        satu palang gelap dan menelan kepala.
        """
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        breathe = int(math.sin(phase * 1.2) * 1)
        fdir = 1 if facing >= 0 else -1
        for side in (-1, 1):
            big = 1.18 if side == fdir else 1.0
            w = 10.0 * big
            h = 9.0 * big
            sx = cx + side * (14 + w * 0.35)
            sy = cy + breathe

            def dome(scale, dy=0.0):
                pts = []
                for k in range(9):
                    a = math.pi + k * math.pi / 8
                    pts.append((sx + math.cos(a) * w * scale * side * -1.0,
                                sy + math.sin(a) * h * scale + dy))
                pts.append((sx + w * scale * 0.9, sy + h * 0.55 + dy))
                pts.append((sx - w * scale * 0.9, sy + h * 0.55 + dy))
                return pts

            NS._poly(surface, P["shadow_deep"],
                     [(px + 2, py + 2) for px, py in dome(1.0)])
            NS._poly(surface, P["obsidian_darkest"], dome(1.0))
            NS._poly(surface, P["obsidian_dark"], dome(0.86))
            NS._poly(surface, P["obsidian_mid"], dome(0.62))
            NS._poly(surface, P["obsidian_light"], [
                (sx - w * 0.55, sy - h * 0.42),
                (sx - w * 0.12, sy - h * 0.62),
                (sx - w * 0.05, sy - h * 0.28),
                (sx - w * 0.5, sy - h * 0.1)])
            NS._aacircle(surface, P["obsidian_high"],
                         (int(sx - w * 0.42), int(sy - h * 0.45)), 1)

            # lame bawah (dua tingkat) menutupi pangkal lengan
            for k in range(2):
                ly = sy + h * 0.55 + k * 4
                lw = w * (0.92 - k * 0.18)
                NS._poly(surface, P["obsidian_darkest"], [
                    (sx - lw, ly), (sx + lw, ly),
                    (sx + lw * 0.85, ly + 4), (sx - lw * 0.85, ly + 4)])
                NS._poly(surface, P["obsidian_mid"], [
                    (sx - lw + 1, ly + 1), (sx + lw - 1, ly + 1),
                    (sx + lw * 0.8, ly + 3), (sx - lw * 0.8, ly + 3)])
                NS._aaline(surface, P["gold_dark"], (sx - lw, ly + 4),
                           (sx + lw, ly + 4), 1)

            # tanduk pendek menyapu ke belakang
            NS._poly(surface, P["horn_dark"], [
                (sx + side * w * 0.55, sy - h * 0.55),
                (sx + side * w * 0.95, sy - h * 0.25),
                (sx + side * (w + 6), sy - h - 5)])
            NS._poly(surface, P["horn_mid"], [
                (sx + side * w * 0.62, sy - h * 0.5),
                (sx + side * w * 0.85, sy - h * 0.3),
                (sx + side * (w + 4.5), sy - h - 4)])
            NS._aacircle(surface, P["horn_shine"],
                         (int(sx + side * (w + 4.5)), int(sy - h - 4)), 1)

            # trim emas + rivet + seam magma
            NS._aaline(surface, P["gold_dark"],
                       (sx - w * 0.95, sy + h * 0.5),
                       (sx + w * 0.95, sy + h * 0.5), 2)
            NS._aaline(surface, P["gold_mid"],
                       (sx - w * 0.85, sy + h * 0.5),
                       (sx + w * 0.85, sy + h * 0.5), 1)
            for r in (-1, 1):
                NS._aacircle(surface, P["gold_light"],
                             (int(sx + r * w * 0.6), int(sy - h * 0.15)), 1)
            NS._aaline(surface, P["magma_mid"],
                       (sx - w * 0.5, sy + h * 0.2),
                       (sx + w * 0.5, sy + h * 0.28), 1)

    @staticmethod
    def _draw_shield(surface, cx, cy, side, phase):
        """Perisai kepala naga di tangan lepas (legacy signature)."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        sx = cx + side * 22
        sy = cy + 2 + int(math.sin(phase * 0.9) * 1)
        pts = [
            (sx - 9, sy - 15), (sx + 9, sy - 15),
            (sx + 11, sy - 2), (sx + 7, sy + 12),
            (sx, sy + 18), (sx - 7, sy + 12), (sx - 11, sy - 2),
        ]
        NS._poly(surface, P["shadow_deep"], [(p[0] + 2, p[1] + 2)
                                             for p in pts])
        NS._poly(surface, P["obsidian_darkest"], pts)
        NS._poly(surface, P["obsidian_dark"],
                 [(sx + (p[0] - sx) * 0.86, sy + (p[1] - sy) * 0.86)
                  for p in pts])
        NS._poly(surface, P["obsidian_mid"],
                 [(sx + (p[0] - sx) * 0.62, sy + (p[1] - sy) * 0.62)
                  for p in pts])
        # bos tengah = kepala naga
        NS._aacircle(surface, P["gold_dark"], (sx, sy - 1), 6)
        NS._aacircle(surface, P["gold_mid"], (sx, sy - 1), 5)
        NS._poly(surface, P["dragon_darkest"], [
            (sx - 4, sy - 4), (sx + 4, sy - 4),
            (sx + 3, sy + 2), (sx, sy + 4), (sx - 3, sy + 2)])
        NS._poly(surface, P["dragon_mid"], [
            (sx - 3, sy - 3), (sx + 3, sy - 3),
            (sx + 2, sy + 1), (sx, sy + 3), (sx - 2, sy + 1)])
        e = int(180 + 70 * math.sin(phase * 2.6))
        NS._aacircle(surface, (*P["eye_bright"], e), (sx - 2, sy - 1), 1)
        NS._aacircle(surface, (*P["eye_bright"], e), (sx + 2, sy - 1), 1)
        # trim tepi + rivet
        for i in range(len(pts)):
            NS._aaline(surface, P["gold_dark"], pts[i],
                       pts[(i + 1) % len(pts)], 2)
            NS._aaline(surface, P["gold_mid"], pts[i],
                       pts[(i + 1) % len(pts)], 1)
        NS._aacircle(surface, P["gold_light"], (sx - 6, sy - 11), 1)
        NS._aacircle(surface, P["gold_light"], (sx + 6, sy - 11), 1)

    @staticmethod
    def _draw_head(surface, cx, cy, facing, phase, roar=0.0):
        """Helm naga: moncong, tanduk melengkung, jambul api."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        nod = int(math.sin(phase * 0.9) * 1)
        cy = cy + nod

        # tempurung helm — POLIGON bersudut (bukan lingkaran) supaya
        # siluetnya terbaca sebagai kepala naga berbaja, bukan bola.
        skull = [
            (cx - f * 12, cy - 8), (cx - f * 7, cy - 14),
            (cx + f * 4, cy - 15), (cx + f * 11, cy - 9),
            (cx + f * 13, cy - 1), (cx + f * 9, cy + 7),
            (cx + f * 1, cy + 11), (cx - f * 8, cy + 8),
            (cx - f * 13, cy + 1),
        ]
        NS._poly(surface, P["shadow_deep"],
                 [(px + 2, py + 2) for px, py in skull])
        NS._poly(surface, P["obsidian_darkest"], skull)
        NS._poly(surface, P["obsidian_dark"],
                 [(cx + (px - cx) * 0.86, cy + (py - cy) * 0.86)
                  for px, py in skull])
        NS._poly(surface, P["obsidian_mid"],
                 [(cx + (px - cx) * 0.62, cy + (py - cy) * 0.66)
                  for px, py in skull])
        # bidang cahaya kiri-atas
        NS._poly(surface, P["obsidian_light"], [
            (cx - f * 8, cy - 5), (cx - f * 3, cy - 9),
            (cx - f * 2, cy - 4), (cx - f * 7, cy - 1)])
        NS._aacircle(surface, P["obsidian_high"],
                     (int(cx - f * 6), int(cy - 6)), 1)

        # moncong naga menonjol ke arah hadap
        snout = [
            (cx + f * 4, cy - 4), (cx + f * 15, cy - 1 + int(roar * 2)),
            (cx + f * 16, cy + 4 + int(roar * 3)),
            (cx + f * 5, cy + 7),
        ]
        NS._poly(surface, P["obsidian_darkest"], snout)
        NS._poly(surface, P["obsidian_mid"], [
            (cx + f * 5, cy - 3), (cx + f * 13, cy - 1),
            (cx + f * 13, cy + 3), (cx + f * 6, cy + 5)])
        NS._aaline(surface, P["obsidian_high"], (cx + f * 6, cy - 2),
                   (cx + f * 12, cy - 1), 1)
        # taring
        for t in (0, 1):
            tx = cx + f * (10 + t * 3)
            NS._poly(surface, P["horn_shine"], [
                (tx, cy + 4), (tx + f * 2, cy + 4), (tx + f, cy + 8)])
        # nostril menyala
        NS._aacircle(surface, (*P["magma_hot"],
                               int(160 + 80 * math.sin(phase * 3))),
                     (cx + f * 13, cy), 1)

        # trim emas mengikuti tepi helm
        for i in range(len(skull)):
            NS._aaline(surface, P["gold_darkest"], skull[i],
                       skull[(i + 1) % len(skull)], 2)
        for i in range(len(skull)):
            NS._aaline(surface, P["gold_dark"], skull[i],
                       skull[(i + 1) % len(skull)], 1)

        # brow ridge + celah mata MIRING yang menyala (bukan dua titik)
        NS._poly(surface, P["shadow_deep"], [
            (cx - f * 9, cy - 3), (cx + f * 9, cy - 5),
            (cx + f * 9, cy - 1), (cx - f * 9, cy + 1)])
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        eye_a = int(190 + 60 * pulse)
        for k, ex in enumerate((-6, 2)):
            x0 = cx + f * ex
            y0 = cy - 2 + k * 1
            slit = [(x0, y0 + 2), (x0 + f * 6, y0 - 1),
                    (x0 + f * 6, y0 + 1), (x0, y0 + 3)]
            NS._poly(surface, (*P["eye_dark"], 255), slit)
            NS._aaline(surface, (*P["eye_mid"], eye_a), (x0, y0 + 2),
                       (x0 + f * 6, y0), 2)
            NS._aaline(surface, (*P["eye_bright"], eye_a),
                       (x0 + f, y0 + 2), (x0 + f * 5, y0), 1)
            NS._aacircle(surface, (*P["eye_hot"], eye_a),
                         (int(x0 + f * 5), int(y0)), 1)
        # brow spike besi di atas mata
        NS._poly(surface, P["obsidian_darkest"], [
            (cx - f * 10, cy - 5), (cx + f * 9, cy - 7),
            (cx + f * 8, cy - 4), (cx - f * 9, cy - 3)])
        NS._aaline(surface, P["obsidian_high"], (cx - f * 9, cy - 5),
                   (cx + f * 8, cy - 6), 1)

        # circlet emas
        NS._rect(surface, P["gold_darkest"], (cx - 9, cy - 11, 18, 4))
        NS._rect(surface, P["gold_dark"], (cx - 9, cy - 11, 18, 3))
        NS._rect(surface, P["gold_mid"], (cx - 8, cy - 10, 16, 2))
        NS._aacircle(surface, P["gold_shine"], (cx - 1, cy - 10), 1)

        # tanduk besar melengkung ke belakang
        for side in (-1, 1):
            base_x = cx + side * 10
            base_y = cy - 9
            seg = [(base_x, base_y)]
            for i in range(1, 6):
                t = i / 5.0
                seg.append((base_x + side * int(7 * t + 9 * t * t),
                            base_y - int(18 * t) + int(9 * t * t)))
            for i in range(len(seg) - 1):
                th = max(2, 7 - i)
                NS._aaline(surface, P["horn_dark"], seg[i], seg[i + 1],
                           th + 1)
                NS._aaline(surface, P["horn_mid"], seg[i], seg[i + 1], th)
                NS._aaline(surface, P["horn_light"],
                           (seg[i][0] - 1, seg[i][1]),
                           (seg[i + 1][0] - 1, seg[i + 1][1]),
                           max(1, th - 3))
            NS._aacircle(surface, P["horn_shine"],
                         (int(seg[-1][0]), int(seg[-1][1])), 1)
            # cincin emas pangkal tanduk
            NS._aaline(surface, P["gold_mid"],
                       (base_x - side * 2, base_y - 1),
                       (base_x + side * 3, base_y - 2), 2)

        # jambul api di puncak helm
        for i, off in enumerate((-5, 0, 5)):
            h = 12 - abs(off)
            NS._flame_tongue(surface, cx + off, cy - 15, h + 5, phase,
                             seed=i * 5, alpha=230, width=3.6)

    @staticmethod
    def _draw_arm_segment(surface, x1, y1, x2, y2, thick=7):
        """Segmen lengan berpelat + sendi emas."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        NS._aaline(surface, P["shadow_deep"], (x1 + 2, y1 + 2),
                   (x2 + 2, y2 + 2), thick + 1)
        NS._aaline(surface, P["obsidian_darkest"], (x1, y1), (x2, y2), thick)
        NS._aaline(surface, P["obsidian_dark"], (x1, y1), (x2, y2),
                   max(1, thick - 2))
        NS._aaline(surface, P["obsidian_mid"], (x1, y1), (x2, y2),
                   max(1, thick - 4))
        NS._aaline(surface, P["obsidian_light"], (x1, y1 - 1), (x2, y2 - 1),
                   1)
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        NS._aacircle(surface, P["gold_dark"], (mx, my), 4)
        NS._aacircle(surface, P["gold_mid"], (mx, my), 3)
        NS._aacircle(surface, P["gold_light"], (mx - 1, my - 1), 1)

    @staticmethod
    def _draw_hand_to(surface, cx, cy, facing, hx, hy, back=False):
        """Rantai bahu -> siku -> tangan menuju titik grip."""
        NS = _NS_ignis_drachorn
        f = 1 if facing >= 0 else -1
        side = -f if back else f
        sx = cx + side * 15
        sy = cy + 2
        mx = (sx + hx) * 0.5 + side * 3
        my = (sy + hy) * 0.5 + 5
        NS._draw_arm_segment(surface, int(sx), int(sy), int(mx), int(my),
                             8 if not back else 7)
        NS._draw_arm_segment(surface, int(mx), int(my), int(hx), int(hy),
                             7 if not back else 6)
        # sarung tangan bercakar
        NS._aacircle(surface, NS.PALETTE["obsidian_darkest"],
                     (int(hx), int(hy)), 5)
        NS._aacircle(surface, NS.PALETTE["obsidian_mid"],
                     (int(hx), int(hy)), 4)
        NS._aacircle(surface, NS.PALETTE["gold_dark"],
                     (int(hx), int(hy)), 2)

    @staticmethod
    def _draw_flame_sword(surface, hx, hy, facing, phase, angle=0,
                          intense=False, theta=None, tip=None):
        """Greatsword magma: bilah bergerigi, fuller menyala, api hidup.

        Kompatibel dengan signature lama (``angle`` = sudut radian gaya
        lama); kalau ``theta``/``tip`` diberikan (ark baru) keduanya
        dipakai apa adanya supaya identik dengan lapisan hidup.
        """
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        L = NS.BLADE_LEN

        if tip is not None:
            tip_x, tip_y = int(tip[0]), int(tip[1])
        elif theta is not None:
            tip_x = int(hx + f * math.sin(theta) * L)
            tip_y = int(hy - math.cos(theta) * L)
        else:
            tip_x = int(hx + math.cos(angle) * L * f)
            tip_y = int(hy + math.sin(angle) * L)

        hx, hy = int(hx), int(hy)
        dx, dy = tip_x - hx, tip_y - hy
        dist = math.hypot(dx, dy) or 1.0
        ux, uy = dx / dist, dy / dist
        px, py = -uy, ux

        # pangkal bilah sedikit di atas grip (ricasso)
        bx = hx + ux * 8
        by = hy + uy * 8

        def _p(t, w):
            return (bx + ux * (dist - 8) * t + px * w,
                    by + uy * (dist - 8) * t + py * w)

        # siluet bilah (bergerigi: dua takik di tepi belakang)
        blade = [
            _p(0.0, 5.2), _p(0.30, 4.6), _p(0.44, 6.0), _p(0.58, 4.2),
            _p(0.74, 5.0), _p(0.88, 3.0), _p(1.0, 0.0),
            _p(0.88, -3.0), _p(0.70, -4.4), _p(0.40, -4.8), _p(0.0, -5.2),
        ]
        NS._poly(surface, P["shadow_deep"],
                 [(p[0] + 2, p[1] + 2) for p in blade])
        NS._poly(surface, P["armor_darkest"], blade)
        NS._poly(surface, P["blade_dark"],
                 [_p(0.0, 4.0), _p(0.5, 3.6), _p(1.0, 0.0),
                  _p(0.5, -3.6), _p(0.0, -4.0)])
        NS._poly(surface, P["blade_mid"],
                 [_p(0.02, 2.6), _p(0.55, 2.2), _p(0.98, 0.0),
                  _p(0.55, -2.2), _p(0.02, -2.6)])
        # fuller magma
        NS._aaline(surface, P["magma_mid"], (bx, by), (tip_x, tip_y), 3)
        NS._aaline(surface, P["blade_light"], (bx, by), (tip_x, tip_y), 2)
        NS._aaline(surface, P["blade_hot"], (bx, by), (tip_x, tip_y), 1)
        NS._aaline(surface, P["blade_core"],
                   (bx + ux * dist * 0.25, by + uy * dist * 0.25),
                   (tip_x, tip_y), 1)

        # api yang menjilat sepanjang bilah
        flames = 6 if not intense else 8
        for i in range(flames):
            t = 0.12 + (i / float(flames)) * 0.9
            fxp = bx + ux * (dist - 8) * t
            fyp = by + uy * (dist - 8) * t
            flick = math.sin(phase * 4.5 + i * 1.3)
            size = (3.0 if intense else 2.2) + flick * 1.0
            NS._flame_tongue(surface, fxp + px * (5.0 + flick),
                             fyp + py * (5.0 + flick),
                             max(3, int(size * 1.9)), phase, seed=i * 4,
                             alpha=185 if intense else 140,
                             width=max(1.6, size * 0.7))
        NS._draw_flame_puff(surface, tip_x, tip_y, 5 if intense else 4,
                            phase, 225)

        # crossguard sayap naga
        gx1, gy1 = hx + px * 11, hy + py * 11
        gx2, gy2 = hx - px * 11, hy - py * 11
        NS._aaline(surface, P["gold_darkest"], (gx1, gy1), (gx2, gy2), 6)
        NS._aaline(surface, P["gold_dark"], (gx1, gy1), (gx2, gy2), 4)
        NS._aaline(surface, P["gold_mid"], (gx1, gy1), (gx2, gy2), 2)
        for s in (1, -1):
            wx = hx + px * s * 12 + ux * 5
            wy = hy + py * s * 12 + uy * 5
            NS._poly(surface, P["gold_dark"], [
                (hx + px * s * 8, hy + py * s * 8), (wx, wy),
                (hx + px * s * 10 - ux * 5, hy + py * s * 10 - uy * 5)])
            NS._aacircle(surface, P["gold_shine"], (int(wx), int(wy)), 1)

        # gagang + pommel permata
        hx2 = hx - ux * 9
        hy2 = hy - uy * 9
        NS._aaline(surface, P["leather_dark"], (hx, hy), (hx2, hy2), 5)
        NS._aaline(surface, P["leather_mid"], (hx, hy), (hx2, hy2), 3)
        NS._aaline(surface, P["leather_high"], (hx, hy), (hx2, hy2), 1)
        px2, py2 = int(hx - ux * 12), int(hy - uy * 12)
        NS._aacircle(surface, P["gold_dark"], (px2, py2), 4)
        NS._aacircle(surface, P["gold_mid"], (px2, py2), 3)
        NS._aacircle(surface, P["red_dark"], (px2, py2), 2)
        NS._aacircle(surface, (*P["magma_bright"],
                               int(180 + 70 * math.sin(phase * 3))),
                     (px2, py2), 1)

    # ── set lengan per aksi (nama lama dipertahankan) ───────────────
    @staticmethod
    def _draw_idle_arms(surface, cx, cy, facing, phase):
        NS = _NS_ignis_drachorn
        grip, tip, theta = NS.sword_geometry(facing, "idle", phase, 0.0)
        hx, hy = cx + grip[0], cy + grip[1] + 8
        NS._draw_hand_to(surface, cx, cy, facing,
                         cx - (1 if facing >= 0 else -1) * 20, cy + 14,
                         back=True)
        NS._draw_hand_to(surface, cx, cy, facing, hx, hy, back=False)
        NS._draw_flame_sword(surface, hx, hy, facing, phase, theta=theta,
                             tip=(cx + tip[0], cy + tip[1] + 8))

    @staticmethod
    def _draw_walk_arms(surface, cx, cy, facing, phase):
        NS = _NS_ignis_drachorn
        swing = math.sin(phase) * 4
        grip, tip, theta = NS.sword_geometry(facing, "walk", phase, 0.0)
        hx, hy = cx + grip[0], cy + grip[1] + 8 + swing * 0.4
        NS._draw_hand_to(surface, cx, cy, facing,
                         cx - (1 if facing >= 0 else -1) * (20 + swing),
                         cy + 14 - swing * 0.3, back=True)
        NS._draw_hand_to(surface, cx, cy, facing, hx, hy, back=False)
        NS._draw_flame_sword(surface, hx, hy, facing, phase, theta=theta,
                             tip=(cx + tip[0], cy + tip[1] + 8 + swing * 0.4))

    @staticmethod
    def _draw_melee_arms(surface, cx, cy, facing, phase, progress):
        """Ayunan dua tangan mengikuti ark — bukan lompatan pose."""
        NS = _NS_ignis_drachorn
        grip, tip, theta = NS.sword_geometry(facing, "melee", phase, progress)
        hx, hy = cx + grip[0], cy + grip[1] + 8
        tx, ty = cx + tip[0], cy + tip[1] + 8
        # tangan belakang ikut memegang gagang (grip dua tangan)
        f = 1 if facing >= 0 else -1
        back_hx = hx - f * 7 - math.sin(theta) * f * 4
        back_hy = hy + 5 + math.cos(theta) * 3
        NS._draw_hand_to(surface, cx, cy, facing, back_hx, back_hy, back=True)
        NS._draw_hand_to(surface, cx, cy, facing, hx, hy, back=False)
        NS._draw_flame_sword(surface, hx, hy, facing, phase, theta=theta,
                             tip=(tx, ty),
                             intense=(0.30 <= progress <= 0.66))

    @staticmethod
    def _draw_ranged_arms(surface, cx, cy, facing, phase, progress):
        NS = _NS_ignis_drachorn
        grip, tip, theta = NS.sword_geometry(facing, "ranged", phase,
                                             progress)
        hx, hy = cx + grip[0], cy + grip[1] + 8
        NS._draw_hand_to(surface, cx, cy, facing,
                         cx - (1 if facing >= 0 else -1) * 18, cy + 10,
                         back=True)
        NS._draw_hand_to(surface, cx, cy, facing, hx, hy, back=False)
        NS._draw_flame_sword(surface, hx, hy, facing, phase, theta=theta,
                             tip=(cx + tip[0], cy + tip[1] + 8),
                             intense=(0.20 < progress < 0.55))

    @staticmethod
    def _draw_cast_arms(surface, cx, cy, facing, phase):
        """Pedang diangkat vertikal, dua tangan — pose CAST/SKILL."""
        NS = _NS_ignis_drachorn
        grip, tip, theta = NS.sword_geometry(facing, "cast", phase, 0.0)
        hx, hy = cx + grip[0], cy + grip[1] + 8
        f = 1 if facing >= 0 else -1
        NS._draw_hand_to(surface, cx, cy, facing, hx - f * 6, hy + 6,
                         back=True)
        NS._draw_hand_to(surface, cx, cy, facing, hx, hy, back=False)
        NS._draw_flame_sword(surface, hx, hy, facing, phase, theta=theta,
                             tip=(cx + tip[0], cy + tip[1] + 8), intense=True)

    # ---------------------------------------------------------------------------
    # 11. KOMPOSISI BADAN (layer order + outline + pass pencahayaan)
    # ---------------------------------------------------------------------------
    @staticmethod
    def _draw_ignis_body_raw(surface, ox, oy, facing, phase, action,
                             attack_progress=0.0):
        """Urutan layer: BACK WING -> CAPE -> TAIL -> BACK LIMB -> BODY ->
        ARMOR -> HEAD -> WEAPON/FRONT LIMB -> HIGHLIGHT."""
        NS = _NS_ignis_drachorn
        f = 1 if facing >= 0 else -1
        ap = max(0.0, min(1.0, float(attack_progress)))

        breath = math.sin(phase * 1.1) * 1.2
        spread = 0.0
        if action in ("cast", "melee") and (action == "cast" or ap > 0.3):
            spread = 0.55 if action == "cast" else 0.35 * math.sin(ap * math.pi)

        # ── BACK LAYER ─────────────────────────────────────────────
        NS._draw_back_wing(surface, ox, oy, f, phase, spread)
        NS._draw_tail(surface, ox, oy, f, phase)
        NS._draw_cape(surface, ox, oy, f, phase, action)

        # ── BODY / ARMOR ───────────────────────────────────────────
        step = phase if action in ("walk", "run") else 0.0
        NS._draw_lower_body(surface, ox, oy + 5, phase, f, action, step)
        NS._draw_torso(surface, ox, oy - 8, phase, f, breath)

        # perisai: di belakang badan kecuali saat menghunus ke depan
        shield_front = (action in ("melee",) and ap >= 0.30)
        if not shield_front:
            NS._draw_shield(surface, ox, oy - 5, -f, phase)

        NS._draw_pauldrons(surface, ox, oy - 16, phase, f)

        roar = 0.0
        if action == "cast":
            roar = 0.5 + 0.5 * math.sin(phase * 3.0)
        elif action in ("melee", "ranged") and 0.3 < ap < 0.7:
            roar = 1.0
        NS._draw_head(surface, ox, oy - 35, f, phase, roar)

        # ── WEAPON + FRONT LIMB ────────────────────────────────────
        if action in ("melee", "swing"):
            NS._draw_melee_arms(surface, ox, oy - 8, f, phase, ap)
        elif action == "ranged":
            NS._draw_ranged_arms(surface, ox, oy - 8, f, phase, ap)
        elif action in ("cast", "skill", "charge"):
            NS._draw_cast_arms(surface, ox, oy - 8, f, phase)
        elif action in ("walk", "run"):
            NS._draw_walk_arms(surface, ox, oy - 8, f, phase)
        else:
            NS._draw_idle_arms(surface, ox, oy - 8, f, phase)

        if shield_front:
            NS._draw_shield(surface, ox, oy - 5, -f, phase)

        # ── HIGHLIGHT PASS ─────────────────────────────────────────
        NS._draw_body_fire_particles(surface, ox, oy, phase)

    @staticmethod
    def _draw_ignis_body(surface, cx, cy, facing, phase, action,
                         attack_progress=0):
        """Komposit: buffer tetap -> crop -> outline 1 px -> rim light."""
        NS = _NS_ignis_drachorn
        if NS._body_buf is None:
            NS._body_buf = pygame.Surface((NS.RIG_W, NS.RIG_H),
                                          pygame.SRCALPHA)
        buf = NS._body_buf
        buf.fill((0, 0, 0, 0))
        NS._draw_ignis_body_raw(buf, NS.RIG_OX, NS.RIG_OY, facing, phase,
                                action, attack_progress)
        used = buf.get_bounding_rect(min_alpha=1)
        if used.width <= 2 or used.height <= 2:
            return
        used.inflate_ip(4, 4)
        used.clamp_ip(buf.get_rect())
        sub = buf.subsurface(used).copy()
        ox = int(cx) - NS.RIG_OX + used.left
        oy = int(cy) - NS.RIG_OY + used.top

        edge = sub.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(edge, (ox + ddx, oy + ddy))
        try:
            import lighting as _lighting
            if _lighting is not None:
                _lighting.apply_to_rig(sub, rim_add=(52, 24, 14),
                                       shade_mul=170, gradient=False,
                                       two_band=False)
        except Exception:
            pass
        surface.blit(sub, (ox, oy))
        # Simpan rig terakhir supaya lapisan hidup bisa membuat AFTERIMAGE
        # tanpa menggambar ulang badan (murah + selalu sinkron pose).
        NS._last_rig = sub
        NS._last_rig_off = (ox - int(cx), oy - int(cy))

    # ---------------------------------------------------------------------------
    # 12. POSE MODES
    # ---------------------------------------------------------------------------
    @staticmethod
    def _draw_ignis_idle(surface, boss, x, y):
        NS = _NS_ignis_drachorn
        phase = float(getattr(boss, "pulse", 0.0))
        bob = int(math.sin(phase * 0.8) * 2)
        NS._draw_shadow(surface, x, y + NS.FEET_DY)
        NS._draw_floating_flames(surface, x, y + 35, phase)
        NS._draw_ignis_body(surface, x, y + bob, boss.direction, phase,
                            "idle")

    @staticmethod
    def _draw_ignis_walk(surface, boss, x, y, run=False):
        NS = _NS_ignis_drachorn
        phase = float(getattr(boss, "pulse", 0.0)) * (2.6 if run else 2.2)
        bob = int(abs(math.sin(phase * 1.3)) * (4 if run else 3))
        sway = int(math.sin(phase) * 2)
        NS._draw_shadow(surface, x + sway, y + NS.FEET_DY)
        NS._draw_floating_flames(surface, x + sway, y + 35, phase, trail=True,
                                 facing=boss.direction)
        NS._draw_ignis_body(surface, x + sway, y - bob, boss.direction, phase,
                            "run" if run else "walk")

    @staticmethod
    def _draw_ignis_melee_attack(surface, boss, x, y):
        NS = _NS_ignis_drachorn
        phase = float(getattr(boss, "pulse", 0.0))
        progress = max(0.0, min(1.0,
                                getattr(boss, "_ign_attack_progress", 0.0)))
        f = getattr(boss, "direction", 1)
        lunge = int(NS._lunge_offset(progress)) * f

        NS._draw_shadow(surface, x + lunge, y + NS.FEET_DY)
        NS._draw_floating_flames(surface, x + lunge, y + 35, phase,
                                 intense=True)
        NS._draw_ignis_body(surface, x + lunge, y, f, phase, "melee",
                            progress)
        if not getattr(boss, "_ign_suppress_canvas_fx", False):
            NS._draw_sword_swing_trail(surface, x + lunge, y, f, progress)

    @staticmethod
    def _draw_ignis_ranged_attack(surface, boss, x, y):
        NS = _NS_ignis_drachorn
        phase = float(getattr(boss, "pulse", 0.0))
        progress = max(0.0, min(1.0,
                                getattr(boss, "_ign_attack_progress", 0.0)))
        f = getattr(boss, "direction", 1)

        if 0.28 < progress < 0.36 and not getattr(boss, "_ign_proj_spawned",
                                                  False):
            if getattr(boss, "_ign_suppress_canvas_fx", False):
                try:
                    from heroes import ignis_drachorn_fx as _ifx
                    _ifx.notify_projectile_cast(boss, x, y)
                except Exception:
                    pass
            else:
                NS._spawn_fire_projectile(boss, x, y)
            boss._ign_proj_spawned = True
        if progress < 0.1 or progress > 0.9:
            boss._ign_proj_spawned = False

        recoil = int(math.sin(progress * math.pi) * 3) * -f
        NS._draw_shadow(surface, x + recoil, y + NS.FEET_DY)
        NS._draw_floating_flames(surface, x + recoil, y + 35, phase,
                                 intense=True)
        NS._draw_ignis_body(surface, x + recoil, y, f, phase, "ranged",
                            progress)
        if not getattr(boss, "_ign_suppress_canvas_fx", False):
            NS._draw_sword_charge_flash(surface, x + recoil, y, f, progress)

    @staticmethod
    def _draw_ignis_cast(surface, boss, x, y):
        NS = _NS_ignis_drachorn
        phase = float(getattr(boss, "pulse", 0.0))
        skill = getattr(boss, "active_skill", None)
        bob = int(math.sin(phase * 1.4) * 2)
        NS._draw_shadow(surface, x, y + NS.FEET_DY)
        NS._draw_floating_flames(surface, x, y + 35, phase,
                                 intense=(skill in ("e", "r")))
        NS._draw_ignis_body(surface, x, y - bob, boss.direction, phase,
                            "cast")

    @staticmethod
    def _draw_ignis_hurt(surface, boss, x, y):
        NS = _NS_ignis_drachorn
        phase = float(getattr(boss, "pulse", 0.0))
        f = getattr(boss, "direction", 1)
        flinch = int(min(3, getattr(boss, "hurt_flash_timer", 0) * 0.5)) * -f
        NS._draw_shadow(surface, x + flinch, y + NS.FEET_DY)
        NS._draw_ignis_body(surface, x + flinch, y + 1, f, phase, "idle")

    @staticmethod
    def _draw_ignis_death(surface, boss, x, y):
        NS = _NS_ignis_drachorn
        phase = float(getattr(boss, "pulse", 0.0))
        NS._draw_shadow(surface, x, y + NS.FEET_DY, 62)
        NS._draw_ignis_body(surface, x, y + 2, boss.direction, phase, "idle")

    # ---------------------------------------------------------------------------
    # 13. ATTACK FX FALLBACK (canvas) — trail & muzzle flash
    # ---------------------------------------------------------------------------
    @staticmethod
    def _draw_sword_swing_trail(surface, x, y, facing, progress):
        """Sabit trail dari ARK pedang (sampel posisi lampau).

        Pita hanya menutupi 45% ujung bilah supaya tidak jadi kipas
        raksasa yang menelan karakter, dan digambar ADDITIVE agar terasa
        seperti bara, bukan cat.
        """
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        if progress < 0.28 or progress > 0.74:
            return
        f = 1 if facing >= 0 else -1
        samples = []
        for i in range(5):
            pr = progress - i * 0.030
            if pr < 0.24:
                break
            grip, tip, _t = NS.sword_geometry(f, "melee", 0.0, pr)
            gx, gy = x + grip[0], y + grip[1]
            tx, ty = x + tip[0], y + tip[1]
            samples.append(((gx + (tx - gx) * 0.74, gy + (ty - gy) * 0.74),
                            (tx, ty)))
        if len(samples) < 3:
            return
        strength = math.sin(min(1.0, (progress - 0.28) / 0.46) * math.pi)

        xs = [p[0] for s2 in samples for p in s2]
        ys = [p[1] for s2 in samples for p in s2]
        minx, miny = int(min(xs)) - 6, int(min(ys)) - 6
        w = int(max(xs)) - minx + 12
        h = int(max(ys)) - miny + 12
        if w <= 0 or h <= 0 or w > 520 or h > 520:
            return
        buf = pygame.Surface((w, h), pygame.SRCALPHA)

        def sh(pt):
            return (pt[0] - minx, pt[1] - miny)

        band = [sh(s2[1]) for s2 in samples] + \
               [sh(s2[0]) for s2 in reversed(samples)]
        pygame.draw.polygon(buf, (*P["fire_dark"], int(46 * strength)), band)
        inner = []
        for a, b in samples:
            inner.append(sh((a[0] + (b[0] - a[0]) * 0.98,
                             a[1] + (b[1] - a[1]) * 0.98)))
        for a, b in reversed(samples):
            inner.append(sh((a[0] + (b[0] - a[0]) * 0.72,
                             a[1] + (b[1] - a[1]) * 0.72)))
        pygame.draw.polygon(buf, (*P["fire_mid"], int(62 * strength)), inner)

        pts = [sh(s2[1]) for s2 in samples]
        for i in range(len(pts) - 1):
            pygame.draw.line(buf, (*P["fire_hot"], int(140 * strength)),
                             pts[i], pts[i + 1], 2)
            pygame.draw.line(buf, (*P["fire_white"], int(110 * strength)),
                             pts[i], pts[i + 1], 1)
        surface.blit(buf, (minx, miny), special_flags=pygame.BLEND_RGB_ADD)

        # percikan piksel di ujung terdepan
        for i, (px_, py_) in enumerate(pts[:3]):
            NS._aacircle(surface,
                         (*P["fire_white"],
                          int(220 * strength * (1 - i * 0.25))),
                         (int(px_ + minx * 0), int(py_ + miny * 0)) if False
                         else (int(samples[i][1][0]), int(samples[i][1][1])),
                         max(1, 3 - i))

    @staticmethod
    def _draw_sword_charge_flash(surface, x, y, facing, progress):
        """Kilatan muzzle di ujung pedang saat melepas bola api."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        if not (0.20 < progress < 0.58):
            return
        f = 1 if facing >= 0 else -1
        _g, tip, theta = NS.sword_geometry(f, "ranged", 0.0, progress)
        tx, ty = int(x + tip[0]), int(y + tip[1])
        t = (progress - 0.20) / 0.38
        strength = math.sin(t * math.pi)
        NS._blit_decal(surface, NS._glow_decal(18, P["fire_mid"]), tx, ty,
                       int(200 * strength), add=True)
        NS._spark_star(surface, tx, ty, int(10 + 12 * strength),
                       P["fire_bright"], int(230 * strength), 8,
                       theta, P["fire_white"])
        for i in range(5):
            a = theta + (i - 2) * 0.32
            r = 10 + 16 * strength
            NS._aacircle(surface,
                         (*P["fire_hot"], int(190 * strength)),
                         (int(tx + math.cos(a) * r * f),
                          int(ty + math.sin(a) * r)), 2)

    # ---------------------------------------------------------------------------
    # 14. SKILL Q — DRAGON BREATH (kerucut api, 3 tahap)
    # ---------------------------------------------------------------------------
    @staticmethod
    def _skill_progress(boss, skill, timer):
        dur = float(_NS_ignis_drachorn.SKILL_DUR.get(skill, 45))
        return max(0.0, min(1.0, 1.0 - float(timer) / dur))

    @staticmethod
    def _draw_dragon_breath_ground(surface, boss, x, y, timer, phase):
        """Tahap 1: tanah hangus + chevron telegraph ke arah target."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        progress = NS._skill_progress(boss, "q", timer)
        f = getattr(boss, "direction", 1)
        tx, ty = NS._target_position(boss, x, y)
        ang = math.atan2(ty - y, tx - x)
        reach = NS._ring_r(boss, NS.SKILL_RADIUS["q"], surface)

        for i in range(6):
            t = (i + 1) / 6.0
            sx = int(x + math.cos(ang) * reach * t)
            sy = int(y + math.sin(ang) * reach * t * 0.55) + 38
            a = int(150 * progress * (1.0 - t * 0.45))
            NS._blit_decal(surface, NS._scorch_decal(10 + int(t * 16),
                                                     seed=i + 2),
                           sx, sy, a)
        for i in range(4):
            t = 0.25 + i * 0.22
            NS._chevron(surface, x + math.cos(ang) * reach * t,
                        y + 34 + math.sin(ang) * reach * t * 0.5, ang,
                        11 + i * 2, P["magma_hot"],
                        int(190 * progress * (1.0 - i * 0.18)), 3)
        _ = f

    @staticmethod
    def _draw_dragon_breath(surface, boss, x, y, timer, phase):
        """Tahap 2-3: semburan kerucut + inti putih + ledakan ujung."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        progress = NS._skill_progress(boss, "q", timer)
        f = getattr(boss, "direction", 1)
        tx, ty = NS._target_position(boss, x, y)
        ang = math.atan2(ty - (y - 25), tx - (x + f * 15))
        ca, sa = math.cos(ang), math.sin(ang)
        px_, py_ = -sa, ca

        origin_x = x + f * 15
        origin_y = y - 25
        reach = NS._ring_r(boss, NS.SKILL_RADIUS["q"], surface) * 0.78
        length = reach * min(1.0, progress * 2.2)
        fade = 1.0 if progress < 0.75 else max(0.0, 1.0 - (progress - 0.75) / 0.25)

        for i in range(18):
            t = i / 18.0
            base_x = origin_x + ca * length * t
            base_y = origin_y + sa * length * t
            width = 7 + t * 34
            for j in range(4):
                off = (j - 1.5) * width / 3.0
                wob = math.sin(phase * 4 + i * 0.7 + j) * 3.0
                fx = base_x + px_ * (off + wob)
                fy = base_y + py_ * (off + wob)
                alpha = int(225 * fade * (1.0 - t * 0.55))
                size = int(6 + t * 8 + math.sin(phase * 5 + i * 0.3) * 2)
                NS._draw_flame_puff(surface, fx, fy, size, phase, alpha)

        for i in range(14):
            t = i / 14.0
            cx2 = origin_x + ca * length * t
            cy2 = origin_y + sa * length * t + math.sin(phase * 4 + i) * 2
            size = max(2, int(6 - t * 3))
            NS._aacircle(surface, (*P["fire_bright"], int(230 * fade)),
                         (int(cx2), int(cy2)), size)
            NS._aacircle(surface, (*P["fire_hot"], int(240 * fade)),
                         (int(cx2), int(cy2)), max(1, size - 1))
            NS._aacircle(surface, (*P["fire_white"], int(250 * fade)),
                         (int(cx2), int(cy2)), max(1, size - 2))

        if progress > 0.3:
            ex = int(origin_x + ca * length)
            ey = int(origin_y + sa * length)
            r = int(18 + math.sin(phase * 3) * 5)
            NS._draw_flame_puff(surface, ex, ey, r, phase, int(240 * fade))
            NS._spark_star(surface, ex, ey, r + 10, P["fire_bright"],
                           int(200 * fade), 8, phase * 0.6, P["fire_white"])
            for i in range(8):
                a = phase * 2 + i * math.pi / 4
                NS._aacircle(surface, (*P["fire_hot"], int(220 * fade)),
                             (int(ex + math.cos(a) * r * 1.5),
                              int(ey + math.sin(a) * r * 1.2)), 2)

    # ---------------------------------------------------------------------------
    # 15. SKILL W — DRAGON TAIL (sapuan 360 derajat)
    # ---------------------------------------------------------------------------
    @staticmethod
    def _draw_dragon_tail_ground(surface, boss, x, y, timer, phase):
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        progress = NS._skill_progress(boss, "w", timer)
        r = NS._ring_r(boss, NS.SKILL_RADIUS["w"], surface)
        gy = y + 34
        NS._blit_decal(surface, NS._ground_ring_decal(int(r * progress),
                                                      P["magma_hot"], 3),
                       x, gy, int(220 * (1.0 - progress * 0.4)), add=True)
        NS._dashed_ring(surface, x, gy, int(r * 0.72), P["fire_bright"],
                        int(180 * (1.0 - progress * 0.5)), -phase * 0.8,
                        12, 3, 0.5)
        for i in range(6):
            a = -phase * 1.6 + i * math.pi / 3
            NS._jagged_crack(surface, x, gy,
                             x + math.cos(a) * r * progress,
                             gy + math.sin(a) * r * progress * 0.45,
                             P["magma_mid"], int(200 * (1 - progress * 0.5)),
                             2, 4, 5.0, seed=i * 13)

    @staticmethod
    def _draw_dragon_tail(surface, boss, x, y, timer, phase):
        """Ekor naga raksasa menyapu + gelombang kejut."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        progress = NS._skill_progress(boss, "w", timer)
        f = getattr(boss, "direction", 1)
        r = NS._ring_r(boss, NS.SKILL_RADIUS["w"], surface)
        sweep = -math.pi * 0.25 + progress * math.pi * 2.1 * f
        fade = 1.0 if progress < 0.8 else max(0.0, 1.0 - (progress - 0.8) / 0.2)

        # ekor: rantai segmen menebal dari pusat ke ujung
        pts = []
        for i in range(9):
            t = i / 8.0
            a = sweep - t * 0.55 * f
            rr = r * t
            pts.append((x + math.cos(a) * rr,
                        y + 12 + math.sin(a) * rr * 0.5 - t * 8))
        for i in range(len(pts) - 1):
            t = i / float(len(pts) - 1)
            th = max(3, int(14 * (1.0 - t * 0.75)))
            NS._aaline(surface, (*P["dragon_darkest"], int(235 * fade)),
                       pts[i], pts[i + 1], th + 2)
            NS._aaline(surface, (*P["dragon_dark"], int(235 * fade)),
                       pts[i], pts[i + 1], th)
            NS._aaline(surface, (*P["dragon_mid"], int(220 * fade)),
                       (pts[i][0], pts[i][1] - 1),
                       (pts[i + 1][0], pts[i + 1][1] - 1), max(1, th - 4))
            NS._aaline(surface, (*P["magma_mid"], int(190 * fade)),
                       (pts[i][0], pts[i][1] + 1),
                       (pts[i + 1][0], pts[i + 1][1] + 1), 1)
        # duri sepanjang ekor
        for i in range(2, len(pts) - 1, 2):
            sx, sy = pts[i]
            NS._poly(surface, (*P["horn_dark"], int(230 * fade)),
                     [(sx - 4, sy), (sx + 4, sy), (sx, sy - 11)])
            NS._poly(surface, (*P["horn_light"], int(230 * fade)),
                     [(sx - 1, sy - 1), (sx + 2, sy - 1), (sx, sy - 9)])
        # ujung berduri
        tipx, tipy = pts[-1]
        for k in range(3):
            a = sweep + (k - 1) * 0.5
            NS._poly(surface, (*P["horn_mid"], int(230 * fade)), [
                (tipx, tipy),
                (tipx + math.cos(a) * 16, tipy + math.sin(a) * 12),
                (tipx + math.cos(a + 0.3) * 8, tipy + math.sin(a + 0.3) * 6)])
        # gelombang kejut mengikuti ujung
        NS._ring(surface, (int(tipx), int(tipy)), int(10 + 16 * progress), 3,
                 P["fire_bright"], int(200 * fade))
        NS._spark_star(surface, tipx, tipy, 14, P["fire_hot"],
                       int(210 * fade), 6, sweep, P["fire_white"])

    # ---------------------------------------------------------------------------
    # 16. SKILL E — DRAGON BLOOD (buff: aura darah naga)
    # ---------------------------------------------------------------------------
    @staticmethod
    def _draw_dragon_blood_ground(surface, boss, x, y, timer, phase):
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        progress = NS._skill_progress(boss, "e", timer)
        r = NS._ring_r(boss, NS.SKILL_RADIUS["e"], surface)
        gy = y + 36
        pulse = math.sin(phase * 3.0) * 0.25 + 0.75
        NS._blit_decal(surface, NS._ground_ring_decal(r, P["red_light"], 3),
                       x, gy, int(190 * pulse), add=True)
        # rune pentagram (garis lurus, bukan lingkaran)
        n = 5
        rr = r * 0.72
        star = []
        for i in range(n):
            a = -math.pi / 2 + phase * 0.25 + i * math.tau * 2 / n
            star.append((x + math.cos(a) * rr, gy + math.sin(a) * rr * 0.45))
        for i in range(n):
            NS._aaline(surface, (*P["magma_hot"], int(170 * pulse)),
                       star[i], star[(i + 1) % n], 2)
        for i in range(8):
            a = -phase * 0.5 + i * math.pi / 4
            d = rr * (0.35 + 0.5 * progress)
            NS._aacircle(surface, (*P["fire_bright"], int(200 * pulse)),
                         (int(x + math.cos(a) * d),
                          int(gy + math.sin(a) * d * 0.45)), 2)

    @staticmethod
    def _draw_dragon_blood_foreground(surface, boss, x, y, timer, phase):
        """Darah naga mendidih: pilar api naik + siluet naga hantu."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        progress = NS._skill_progress(boss, "e", timer)
        fade = 1.0 if progress < 0.7 else max(0.0, 1.0 - (progress - 0.7) / 0.3)
        rise = progress * 60.0

        for i in range(10):
            a = phase * 1.6 + i * math.tau / 10
            rr = 22 + math.sin(phase * 2 + i) * 5
            fx = x + math.cos(a) * rr
            fy = y + 30 - (rise + i * 3) % 70
            NS._flame_tongue(surface, fx, fy, 10 + int(math.sin(a) * 3),
                             phase, seed=i * 3, alpha=int(200 * fade))
        # aliran magma naik di badan
        for i in range(5):
            t = (phase * 0.7 + i * 0.2) % 1.0
            NS._aacircle(surface, (*P["magma_bright"], int(220 * fade *
                                                           (1 - t))),
                         (int(x + math.sin(i * 2.1 + phase) * 14),
                          int(y + 20 - t * 56)), 2)
        # kepala naga hantu di atas kepala
        hy = y - 62 - int(math.sin(phase * 1.6) * 3)
        NS._blit_decal(surface, NS._glow_decal(24, P["red_mid"]), x, hy,
                       int(150 * fade), add=True)
        NS._draw_dragon_head(surface, x, hy, getattr(boss, "direction", 1),
                             phase)

    # ---------------------------------------------------------------------------
    # 17. SKILL R — ELDER DRAGON FORM
    # ---------------------------------------------------------------------------
    @staticmethod
    def _draw_elder_form_ground(surface, boss, x, y, timer, phase):
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        progress = NS._skill_progress(boss, "r", timer)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        r = NS._ring_r(boss, NS.SKILL_RADIUS["r"], surface)
        gy = y + 36
        NS._blit_decal(surface, NS._scorch_decal(int(r * 0.85), seed=21),
                       x, gy, int(190 * pulse))
        NS._blit_decal(surface, NS._ground_ring_decal(int(r * min(1.0, progress * 1.6)),
                                                      P["magma_hot"], 4),
                       x, gy, int(230 * pulse), add=True)
        NS._dashed_ring(surface, x, gy, int(r * 0.62), P["fire_bright"],
                        int(200 * pulse), phase * 0.4, 10, 3, 0.55)
        for i in range(8):
            a = phase * 0.4 + i * math.pi / 4
            rx = x + int(math.cos(a) * (r * 0.8))
            ry = gy + int(math.sin(a) * (r * 0.36))
            NS._spark_star(surface, rx, ry, 6, P["fire_bright"],
                           int(220 * pulse), 6, a, P["fire_hot"])
        for i in range(6):
            a = i * math.tau / 6 - phase * 0.3
            NS._jagged_crack(surface, x, gy,
                             x + math.cos(a) * r * 0.9,
                             gy + math.sin(a) * r * 0.4,
                             P["magma_mid"], int(200 * pulse), 2, 5, 6.0,
                             seed=i * 23)

    @staticmethod
    def _draw_dragon_wing(surface, cx, cy, side, facing, flap, phase):
        """Sayap naga besar (legacy signature dipertahankan)."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        base_x = cx + side * 8
        base_y = cy
        span = 52 + flap * 16
        joints = [
            (base_x + side * span * 0.45, base_y - 30 - flap * 10),
            (base_x + side * span, base_y - 12 - flap * 14),
            (base_x + side * span * 0.85, base_y + 18 - flap * 6),
            (base_x + side * span * 0.45, base_y + 26),
        ]
        membrane = [(base_x, base_y - 6)] + joints + [(base_x, base_y + 14)]
        NS._poly(surface, P["shadow_deep"],
                 [(p[0] + 3, p[1] + 3) for p in membrane])
        NS._poly(surface, P["wing_dark"], membrane)
        NS._poly(surface, P["wing_mid"],
                 [(base_x + (p[0] - base_x) * 0.82,
                   base_y + (p[1] - base_y) * 0.82) for p in membrane])
        NS._poly(surface, P["wing_light"],
                 [(base_x + (p[0] - base_x) * 0.5,
                   base_y + (p[1] - base_y) * 0.5) for p in membrane])
        for jx, jy in joints:
            NS._aaline(surface, P["dragon_darkest"], (base_x, base_y - 4),
                       (jx, jy), 4)
            NS._aaline(surface, P["dragon_mid"], (base_x, base_y - 4),
                       (jx, jy), 2)
            NS._aacircle(surface, P["horn_mid"], (int(jx), int(jy)), 3)
            NS._aacircle(surface, P["horn_light"], (int(jx), int(jy) - 1), 1)
        # membran menyala di tepi
        for i in range(len(joints) - 1):
            NS._aaline(surface, (*P["wing_glow"],
                                 int(150 + 70 * math.sin(phase * 2 + i))),
                       joints[i], joints[i + 1], 2)

    @staticmethod
    def _draw_dragon_head(surface, cx, cy, facing, phase):
        """Kepala naga (dipakai R & E) — moncong panjang bertanduk."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        skull = [
            (cx - f * 12, cy - 8), (cx + f * 6, cy - 11),
            (cx + f * 20, cy - 4), (cx + f * 22, cy + 3),
            (cx + f * 6, cy + 8), (cx - f * 10, cy + 6),
        ]
        NS._poly(surface, P["shadow_deep"],
                 [(p[0] + 2, p[1] + 2) for p in skull])
        NS._poly(surface, P["dragon_darkest"], skull)
        NS._poly(surface, P["dragon_dark"],
                 [(cx + (p[0] - cx) * 0.86, cy + (p[1] - cy) * 0.86)
                  for p in skull])
        NS._poly(surface, P["dragon_mid"],
                 [(cx + (p[0] - cx) * 0.6, cy + (p[1] - cy) * 0.6)
                  for p in skull])
        # rahang terbuka + api di mulut
        NS._poly(surface, P["dragon_darkest"], [
            (cx + f * 6, cy + 5), (cx + f * 21, cy + 4),
            (cx + f * 18, cy + 11), (cx + f * 5, cy + 10)])
        NS._draw_flame_puff(surface, cx + f * 20, cy + 5, 5, phase, 230)
        # taring
        for t in range(3):
            tx = cx + f * (10 + t * 4)
            NS._poly(surface, P["horn_shine"], [
                (tx, cy + 4), (tx + f * 2, cy + 4), (tx + f, cy + 9)])
        # tanduk
        for side in (-1, 1):
            hx = cx - f * 6
            hy = cy - 8 + side * 2
            NS._aaline(surface, P["horn_dark"], (hx, hy),
                       (hx - f * 14, hy - 12 + side * 5), 5)
            NS._aaline(surface, P["horn_mid"], (hx, hy),
                       (hx - f * 14, hy - 12 + side * 5), 3)
            NS._aacircle(surface, P["horn_light"],
                         (int(hx - f * 14), int(hy - 12 + side * 5)), 1)
        # mata menyala
        e = int(190 + 65 * math.sin(phase * 3))
        NS._aacircle(surface, (*P["eye_dark"], e), (cx + f * 8, cy - 4), 3)
        NS._aacircle(surface, (*P["eye_bright"], e), (cx + f * 8, cy - 4), 2)
        NS._aacircle(surface, (*P["eye_hot"], e), (cx + f * 8, cy - 5), 1)

    @staticmethod
    def _draw_elder_dragon_form(surface, boss, x, y, timer, pulse):
        """Bentuk R: Ignis meledak jadi NAGA PURBA yang berdiri tegak.

        Digambar lewat jalur komposit yang sama dengan badan normal
        (buffer -> crop -> outline siluet 1 px -> rim light) supaya
        siluetnya tetap kokoh dan tidak jadi gumpalan merah.
        """
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        f = 1 if getattr(boss, "direction", 1) >= 0 else -1
        bob = math.sin(pulse * 0.9) * 3.0
        rise = min(1.0, max(0.0, (90 - int(timer)) / 12.0))   # bangkit

        # ── tanah: bayangan besar + genangan magma ─────────────────
        NS._draw_shadow(surface, x, y + NS.FEET_DY + 2, 120)
        NS._blit_decal(surface, NS._ground_pool_decal(58, P["magma_dark"]),
                       x, y + NS.FEET_DY, 150, add=True)
        NS._blit_decal(surface, NS._ground_pool_decal(34, P["fire_dark"]),
                       x, y + NS.FEET_DY + 2, 130, add=True)

        # ── badan naga lewat buffer komposit ───────────────────────
        if NS._body_buf is None:
            NS._body_buf = pygame.Surface((NS.RIG_W, NS.RIG_H),
                                          pygame.SRCALPHA)
        buf = NS._body_buf
        buf.fill((0, 0, 0, 0))
        NS._draw_elder_form_raw(buf, NS.RIG_OX, NS.RIG_OY - int(bob), f,
                                pulse, rise)
        used = buf.get_bounding_rect(min_alpha=1)
        if used.width <= 2 or used.height <= 2:
            return
        used.inflate_ip(4, 4)
        used.clamp_ip(buf.get_rect())
        sub = buf.subsurface(used).copy()
        ox = int(x) - NS.RIG_OX + used.left
        oy = int(y) - NS.RIG_OY + used.top

        edge = sub.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(edge, (ox + ddx, oy + ddy))
        try:
            import lighting as _lighting
            if _lighting is not None:
                _lighting.apply_to_rig(sub, rim_add=(70, 30, 16),
                                       shade_mul=170, gradient=False,
                                       two_band=False)
        except Exception:
            pass
        surface.blit(sub, (ox, oy))
        NS._last_rig = sub
        NS._last_rig_off = (ox - int(x), oy - int(y))

        # ── bara mengorbit (di depan, ruang layar) ─────────────────
        for i in range(8):
            a = pulse * 1.2 + i * math.tau / 8
            rr = 52 + math.sin(pulse * 2 + i) * 7
            px = int(x + math.cos(a) * rr)
            py = int(y - 18 + math.sin(a) * rr * 0.5)
            NS._aacircle(surface, (*P["fire_bright"],
                                   int(150 + 90 * math.sin(pulse * 3 + i))),
                         (px, py), 2)

    @staticmethod
    def _draw_elder_form_raw(surf, ox, oy, f, pulse, rise=1.0):
        """Rig naga purba. Urutan: sayap jauh -> ekor -> kaki belakang ->
        badan -> sisik -> sayap dekat -> leher -> kepala -> cakar depan."""
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        flap = math.sin(pulse * 2.0) * 0.32
        body_y = oy - 12 - int(10 * rise)          # naga berdiri tegak

        # ── 1. SAYAP JAUH (di belakang badan) ──────────────────────
        NS._draw_elder_wing(surf, ox - f * 6, body_y - 16, -1, f,
                            flap * 0.7, pulse, far=True)

        # ── 2. EKOR: melengkung ke belakang-bawah ──────────────────
        px_, py_ = ox - f * 20, body_y + 16
        pts = []
        for i in range(1, 10):
            t = i / 9.0
            tx = px_ - f * (58 * t)
            ty = body_y + 16 + math.sin(t * 2.2 + pulse * 0.9) * 9 + 20 * t
            pts.append((tx, ty))
        prev = (px_, py_)
        for i, (tx, ty) in enumerate(pts):
            t = (i + 1) / 9.0
            th = max(2, int(13 * (1.0 - t * 0.82)))
            NS._aaline(surf, P["dragon_darkest"], prev, (tx, ty), th + 2)
            NS._aaline(surf, P["dragon_dark"], prev, (tx, ty), th)
            NS._aaline(surf, P["dragon_mid"], (prev[0], prev[1] - 1),
                       (tx, ty - 1), max(1, th - 3))
            if i % 2 == 0 and i < 7:               # duri punggung ekor
                NS._poly(surf, P["horn_dark"], [
                    (tx, ty - th * 0.5), (tx + f * 3, ty - th * 0.5 - 7),
                    (tx + f * 6, ty - th * 0.5)])
            prev = (tx, ty)
        tipx, tipy = prev
        NS._poly(surf, P["horn_mid"], [
            (tipx + f * 4, tipy - 6), (tipx - f * 13, tipy),
            (tipx + f * 4, tipy + 6)])
        NS._poly(surf, P["horn_light"], [
            (tipx + f * 2, tipy - 3), (tipx - f * 8, tipy),
            (tipx + f * 2, tipy + 3)])

        # ── 3. KAKI BELAKANG (paha tebal + cakar) ──────────────────
        for side, depth in ((-1, 0), (1, 1)):
            lx = ox + f * (side * 13)
            hip = body_y + 14
            knee = (lx - f * 7, hip + 20)
            foot = (lx + f * 4, oy + NS.FEET_DY - 4)
            col_a = P["dragon_darkest"] if depth == 0 else P["dragon_dark"]
            col_b = P["dragon_dark"] if depth == 0 else P["dragon_mid"]
            NS._poly(surf, col_a, [
                (lx - f * 11, hip - 6), (lx + f * 10, hip - 4),
                (knee[0] + f * 7, knee[1]), (knee[0] - f * 7, knee[1])])
            NS._aaline(surf, col_a, knee, foot, 9)
            NS._aaline(surf, col_b, (knee[0], knee[1] - 1),
                       (foot[0], foot[1] - 1), 5)
            NS._poly(surf, col_a, [
                (foot[0] - f * 8, foot[1] - 3),
                (foot[0] + f * 11, foot[1] - 2),
                (foot[0] + f * 11, foot[1] + 4),
                (foot[0] - f * 8, foot[1] + 4)])
            for c in (-5, 0, 5):
                NS._poly(surf, P["horn_light"], [
                    (foot[0] + f * 10, foot[1] + c * 0.5 - 1),
                    (foot[0] + f * 17, foot[1] + c * 0.4 + 1),
                    (foot[0] + f * 10, foot[1] + c * 0.5 + 3)])

        # ── 4. BADAN: dada bidang + perut berpelat ─────────────────
        body_pts = [
            (ox - f * 26, body_y + 12), (ox - f * 28, body_y - 10),
            (ox - f * 16, body_y - 26), (ox + f * 6, body_y - 31),
            (ox + f * 24, body_y - 22), (ox + f * 30, body_y - 2),
            (ox + f * 24, body_y + 16), (ox + f * 4, body_y + 22),
            (ox - f * 16, body_y + 20),
        ]
        NS._poly(surf, P["dragon_darkest"], body_pts)
        NS._poly(surf, P["dragon_dark"],
                 [(ox + (p[0] - ox) * 0.9, body_y + (p[1] - body_y) * 0.9)
                  for p in body_pts])
        NS._poly(surf, P["dragon_mid"],
                 [(ox + (p[0] - ox) * 0.62, body_y + (p[1] - body_y) * 0.66)
                  for p in body_pts])
        # pelat perut (garis horizontal terang -> arah jelas)
        for i in range(4):
            py = body_y + 2 + i * 6
            w = 17 - i * 3
            NS._poly(surf, P["dragon_light"], [
                (ox + f * (2 - w), py), (ox + f * (2 + w), py - 1),
                (ox + f * (2 + w - 2), py + 3), (ox + f * (2 - w + 2),
                                                 py + 4)])
        # sisik punggung (baris berselang)
        for row in range(3):
            for col in range(-2, 4):
                sx = ox + f * (col * 8 + (row % 2) * 4)
                sy = body_y - 22 + row * 7
                NS._poly(surf, P["dragon_dark"],
                         [(sx, sy - 4), (sx + 4, sy), (sx, sy + 4),
                          (sx - 4, sy)])
                NS._poly(surf, P["dragon_light"],
                         [(sx, sy - 2), (sx + 2, sy - 1), (sx, sy + 1),
                          (sx - 2, sy - 1)])
        # inti magma di dada (denyut)
        glow = int(180 + 70 * math.sin(pulse * 2.6))
        NS._jagged_crack(surf, ox - f * 13, body_y - 14, ox + f * 17,
                         body_y + 6, P["magma_hot"], glow, 3, 5, 4.0,
                         seed=31)
        NS._poly(surf, (*P["magma_bright"], glow), [
            (ox + f * 2, body_y - 12), (ox + f * 9, body_y - 4),
            (ox + f * 2, body_y + 5), (ox - f * 5, body_y - 4)])
        NS._poly(surf, (*P["magma_white"], min(255, glow + 40)), [
            (ox + f * 2, body_y - 7), (ox + f * 5, body_y - 4),
            (ox + f * 2, body_y + 1), (ox - f * 1, body_y - 4)])

        # ── 5. SAYAP DEKAT (di depan badan) ────────────────────────
        NS._draw_elder_wing(surf, ox + f * 2, body_y - 18, 1, f, flap,
                            pulse, far=False)

        # ── 6. LEHER melengkung + KEPALA ───────────────────────────
        nx0, ny0 = ox + f * 14, body_y - 24
        nx1, ny1 = ox + f * 30, body_y - 44
        nx2, ny2 = ox + f * 40, body_y - 60
        for w, col in ((15, P["dragon_darkest"]), (12, P["dragon_dark"]),
                       (7, P["dragon_mid"])):
            NS._aaline(surf, col, (nx0, ny0), (nx1, ny1), w)
            NS._aaline(surf, col, (nx1, ny1), (nx2, ny2),
                       max(2, int(w * 0.82)))
        for i in range(4):                          # duri leher
            t = i / 3.0
            sx = nx0 + (nx2 - nx0) * t
            sy = ny0 + (ny2 - ny0) * t
            NS._poly(surf, P["horn_dark"], [
                (sx - f * 5, sy), (sx - f * 12, sy - 8),
                (sx - f * 3, sy - 4)])
        NS._draw_dragon_head(surf, nx2 + f * 8, ny2 - 4, f, pulse)

        # ── 7. CAKAR DEPAN (menjulur ke arah hadap) ────────────────
        for side, depth in ((-1, 0), (1, 1)):
            sx = ox + f * (16 + side * 3)
            sy = body_y - 8 + side * 6
            elbow = (sx + f * 14, sy + 16)
            paw = (sx + f * 26, sy + 26)
            col_a = P["dragon_darkest"] if depth == 0 else P["dragon_dark"]
            col_b = P["dragon_dark"] if depth == 0 else P["dragon_mid"]
            NS._aaline(surf, col_a, (sx, sy), elbow, 10)
            NS._aaline(surf, col_b, (sx, sy - 1), (elbow[0], elbow[1] - 1), 6)
            NS._aaline(surf, col_a, elbow, paw, 8)
            NS._aaline(surf, col_b, (elbow[0], elbow[1] - 1),
                       (paw[0], paw[1] - 1), 4)
            for c in (-6, -1, 4):
                NS._poly(surf, P["horn_light"], [
                    (paw[0], paw[1] + c * 0.5),
                    (paw[0] + f * 11, paw[1] + c * 0.4 + 2),
                    (paw[0], paw[1] + c * 0.5 + 4)])

    @staticmethod
    def _draw_elder_wing(surf, bx, by, side, f, flap, pulse, far=False):
        """Sayap naga purba: 4 jari mengipas + membran berlekuk.

        ``far`` = sayap seberang (lebih kecil, lebih gelap, digambar
        sebelum badan) supaya ada kedalaman, bukan dua bentuk kembar.
        """
        NS = _NS_ignis_drachorn
        P = NS.PALETTE
        depth = 0.74 if far else 1.0
        spread = (1.0 + flap * 0.30) * depth
        shoulder = (bx, by)
        elbow = (bx - f * 30 * spread, by - (22 + 12 * flap) * spread)
        wrist = (bx - f * 54 * spread, by - (40 + 16 * flap) * spread)

        # jari mengipas dari pergelangan: dari atas-belakang ke bawah
        fingers = []
        base = 2.05                                   # rad, mengarah ke -f
        for i in range(4):
            t = i / 3.0
            a = base + (-0.62 + 1.55 * t)
            ln = (58 - 12 * t) * spread
            fingers.append((wrist[0] + f * math.cos(a) * ln * -1.0,
                            wrist[1] - math.sin(a) * ln * -1.0
                            + math.sin(pulse * 2.0 + i) * 2.0))

        if far:
            memb_out, memb_in, vein = (P["shadow_deep"],
                                       P["dragon_darkest"], P["dragon_dark"])
            bone_a, bone_b = P["horn_dark"], P["horn_dark"]
        else:
            memb_out, memb_in, vein = (P["dragon_darkest"],
                                       P["dragon_dark"], P["dragon_mid"])
            bone_a, bone_b = P["horn_dark"], P["horn_mid"]

        # membran: tepi luar melewati ujung jari, dengan LEKUK di antaranya
        memb = [shoulder, elbow, wrist]
        for i, fg in enumerate(fingers):
            memb.append(fg)
            if i < len(fingers) - 1:
                nx_ = (fg[0] + fingers[i + 1][0]) * 0.5
                ny_ = (fg[1] + fingers[i + 1][1]) * 0.5
                memb.append((nx_ + (wrist[0] - nx_) * 0.30,
                             ny_ + (wrist[1] - ny_) * 0.30))
        memb.append((shoulder[0] - f * 4, shoulder[1] + 16 * depth))
        NS._poly(surf, memb_out, memb)
        NS._poly(surf, memb_in,
                 [(wrist[0] + (p[0] - wrist[0]) * 0.80,
                   wrist[1] + (p[1] - wrist[1]) * 0.80) for p in memb])

        # urat membran dari pergelangan ke tiap ujung jari
        for fg in fingers:
            NS._aaline(surf, vein, wrist, fg, 2)
        NS._aaline(surf, vein, elbow, fingers[0], 1)

        # tulang lengan + jari
        NS._aaline(surf, bone_a, shoulder, elbow, 7 if not far else 5)
        NS._aaline(surf, bone_a, elbow, wrist, 6 if not far else 4)
        NS._aaline(surf, bone_b, (shoulder[0], shoulder[1] - 1),
                   (elbow[0], elbow[1] - 1), 3 if not far else 2)
        NS._aaline(surf, bone_b, (elbow[0], elbow[1] - 1),
                   (wrist[0], wrist[1] - 1), 3 if not far else 2)
        for i, fg in enumerate(fingers):
            NS._aaline(surf, bone_a, wrist, fg, 4 if not far else 3)
            NS._aaline(surf, bone_b, (wrist[0], wrist[1] - 1),
                       (fg[0], fg[1] - 1), 2 if not far else 1)

        # cakar di pergelangan + bara di tepi depan (hanya sayap dekat)
        NS._poly(surf, P["horn_mid"], [
            (wrist[0], wrist[1] - 3), (wrist[0] - f * 12, wrist[1] - 10),
            (wrist[0] + f * 2, wrist[1] + 3)])
        NS._poly(surf, P["horn_light"], [
            (wrist[0] - f * 1, wrist[1] - 3),
            (wrist[0] - f * 8, wrist[1] - 7),
            (wrist[0] + f * 1, wrist[1])])
        if not far:
            for i in range(3):
                t = (i + 1) / 4.0
                ex = shoulder[0] + (wrist[0] - shoulder[0]) * t
                ey = shoulder[1] + (wrist[1] - shoulder[1]) * t
                NS._aacircle(surf, (*P["magma_hot"],
                                    int(150 + 90 * math.sin(pulse * 3 + i))),
                             (int(ex), int(ey - 4)), 2)

    # ---------------------------------------------------------------------------
    # 18. DEBUG OVERLAY
    # ---------------------------------------------------------------------------
    @staticmethod
    def _debug_font():
        try:
            from _render import get_font
            return get_font(14)
        except Exception:
            try:
                return pygame.font.Font(None, 16)
            except Exception:                          # pragma: no cover
                return None

    @staticmethod
    def _draw_ignis_debug(surface, boss, x, y):
        """hitbox / hurtbox / range / proyektil / state / FPS / partikel."""
        NS = _NS_ignis_drachorn
        r = max(8, int(getattr(boss, "radius", 45)))
        f = getattr(boss, "direction", 1)

        pygame.draw.rect(surface, (80, 200, 255),
                         (x - r, y - r, r * 2, r * 2), 1)          # hurtbox
        pygame.draw.circle(surface, (255, 220, 60), (int(x), int(y)),
                           int(getattr(boss, "range", 55)), 1)     # range
        # hitbox ayunan (aktif hanya di jendela hit)
        if getattr(boss, "_ign_hit_window", False):
            grip, tip, _t = NS.sword_geometry(
                f, "melee", 0.0,
                float(getattr(boss, "_ign_attack_progress", 0.0)))
            pygame.draw.line(surface, (255, 60, 60),
                             (x + grip[0], y + grip[1]),
                             (x + tip[0], y + tip[1]), 2)
            pygame.draw.circle(surface, (255, 60, 60),
                               (int(x + tip[0]), int(y + tip[1])), 10, 1)
        for p in getattr(boss, "_ign_projectiles", ()):
            pygame.draw.circle(surface, (255, 80, 220),
                               (int(p.x), int(p.y)), int(p.radius), 1)

        font = NS._debug_font()
        if font is None:
            return
        try:
            fps = int(pygame.time.Clock().get_fps())
        except Exception:                              # pragma: no cover
            fps = 0
        particles = len(getattr(boss, "_ign_projectiles", ()))
        try:
            from heroes import ignis_drachorn_fx as _ifx
            particles += int(_ifx.total_particles())
        except Exception:
            pass
        lines = [
            "state=%s prio=%d" % (getattr(boss, "_ign_state", "?"),
                                  int(getattr(boss, "_ign_state_priority",
                                              0))),
            "phase=%s ap=%.2f" % (getattr(boss, "_ign_attack_phase", "NONE"),
                                  float(getattr(boss, "_ign_attack_progress",
                                                0.0))),
            "frame=%d timer=%d" % (int(getattr(boss, "_ign_attack_frame", 0)),
                                   int(getattr(boss, "timer", 0))),
            "skill=%s t=%d" % (getattr(boss, "active_skill", None),
                               int(getattr(boss, "active_skill_timer", 0))),
            "fps=%d particles=%d" % (fps, particles),
        ]
        for i, line in enumerate(lines):
            try:
                img = font.render(line, True, (255, 235, 190))
                surface.blit(img, (int(x) - 60, int(y) - r - 78 + i * 15))
            except Exception:                          # pragma: no cover
                break

    # ===================================================================
    # 19. MAIN DRAW ENTRY POINT
    # ===================================================================
    @staticmethod
    def draw_ignis(surface, boss, x, y):
        """Entry point Boss.draw() sekaligus jalur hero-lane.

        Urutan render:
          GROUND -> GROUND FX -> SHADOW -> BACK PARTICLES -> BODY/ARMOR/
          HEAD/WEAPON -> ATTACK TRAIL -> PROJECTILE -> FRONT PARTICLES ->
          SKILL FX -> IMPACT FX -> DEBUG.
        Trail/partikel/proyektil/impact/hit-stop/shake hidup di
        ``heroes/ignis_drachorn_fx`` (skala layar 1:1); canvas hanya
        fallback bila modul itu tidak tersedia.
        """
        NS = _NS_ignis_drachorn
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        portrait = bool(getattr(boss, "_portrait_hd", False))
        hero_lane = hasattr(boss, "_render_scale")
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)

        moving = NS._detect_moving(boss)
        NS._update_ignis_anim(boss, moving)
        action, phase, ap = NS._resolve_pose(boss, moving)
        boss._ign_pose_action = action
        boss._ign_phase = phase

        # ── lapisan hidup ──────────────────────────────────────────
        live, owned = NS._live_fx(boss, surface, x, y, not hero_lane,
                                  portrait)
        boss._ign_suppress_canvas_fx = owned

        # ── GROUND / AURA ──────────────────────────────────────────
        if not portrait:
            NS._draw_fire_aura(surface, x, y, pulse, active_skill)
            NS._draw_ground_embers(surface, x, y + 38, pulse, active_skill)
            if not owned:
                if active_skill == "q":
                    NS._draw_dragon_breath_ground(surface, boss, x, y,
                                                  skill_timer, pulse)
                elif active_skill == "w":
                    NS._draw_dragon_tail_ground(surface, boss, x, y,
                                                skill_timer, pulse)
                elif active_skill == "e":
                    NS._draw_dragon_blood_ground(surface, boss, x, y,
                                                 skill_timer, pulse)
                elif active_skill == "r":
                    NS._draw_elder_form_ground(surface, boss, x, y,
                                               skill_timer, pulse)

        # ── BADAN (dengan hurt-flash mask) ─────────────────────────
        tgt, tx_, ty_ = surface, x, y
        if flash > 0 and not portrait:
            if NS._flash_buf is None:
                NS._flash_buf = pygame.Surface((240, 260), pygame.SRCALPHA)
            NS._flash_buf.fill((0, 0, 0, 0))
            NS._record_shadow = []
            tgt, tx_, ty_ = NS._flash_buf, 120, 130

        if active_skill == "r" and skill_timer > 10:
            NS._draw_elder_dragon_form(tgt, boss, tx_, ty_, skill_timer,
                                       pulse)
        elif action == "cast":
            NS._draw_ignis_cast(tgt, boss, tx_, ty_)
        elif action == "melee":
            NS._draw_ignis_melee_attack(tgt, boss, tx_, ty_)
        elif action == "ranged":
            NS._draw_ignis_ranged_attack(tgt, boss, tx_, ty_)
        elif action == "run":
            NS._draw_ignis_walk(tgt, boss, tx_, ty_, run=True)
        elif action == "walk":
            NS._draw_ignis_walk(tgt, boss, tx_, ty_)
        elif action == "death":
            NS._draw_ignis_death(tgt, boss, tx_, ty_)
        elif action == "hurt":
            NS._draw_ignis_hurt(tgt, boss, tx_, ty_)
        else:
            NS._draw_ignis_idle(tgt, boss, tx_, ty_)

        if flash > 0 and not portrait:
            surface.blit(NS._flash_buf, (x - tx_, y - ty_))
            w = int(235 * min(1.0, flash / 8.0))
            try:
                m = pygame.mask.from_surface(NS._flash_buf, 50)
                wht = m.to_surface(setcolor=(w, int(w * 0.72), int(w * 0.5),
                                             255),
                                   unsetcolor=(0, 0, 0, 0))
                for rect in (NS._record_shadow or ()):
                    wht.fill((0, 0, 0, 0), rect)
                surface.blit(wht, (x - tx_, y - ty_),
                             special_flags=pygame.BLEND_RGB_ADD)
            except Exception:                          # pragma: no cover
                pass
            NS._record_shadow = None

        # ── PROYEKTIL + SKILL FX (fallback canvas) ─────────────────
        if not portrait and not owned:
            NS._manage_projectiles(boss, surface, pulse)
            if active_skill == "q":
                NS._draw_dragon_breath(surface, boss, x, y, skill_timer,
                                       pulse)
            elif active_skill == "w":
                NS._draw_dragon_tail(surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "e":
                NS._draw_dragon_blood_foreground(surface, boss, x, y,
                                                 skill_timer, pulse)

        # ── LAPISAN HIDUP DI ATAS (trail/proyektil/impact/skill) ───
        if live is not None:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass

        # ── DEBUG ──────────────────────────────────────────────────
        if NS.DEBUG_CHARACTER and not portrait:
            NS._draw_ignis_debug(surface, boss, x, y)

        _ = ap

    @staticmethod
    def draw_boss(surface, boss, x, y):
        _NS_ignis_drachorn.draw_ignis(surface, boss, x, y)

    @staticmethod
    def draw_ignis_drachorn(surface, boss, x, y):
        """Entry point resmi untuk Ignis Drachorn."""
        _NS_ignis_drachorn.draw_ignis(surface, boss, x, y)


# ====================================================================
# ENTRY POINT PUBLIK (dipanggil base_boss.Boss.draw)
# ====================================================================

def draw_zharok(surface, boss, x, y):
    """Entry point zharok."""
    return _NS_zharok.draw_zharok(surface, boss, x, y)

def draw_pyrenth(surface, boss, x, y):
    """Entry point pyrenth."""
    return _NS_pyrenth.draw_pyrenth(surface, boss, x, y)

def draw_vokrahn(surface, boss, x, y):
    """Entry point vokrahn."""
    return _NS_vokrahn.draw_vokrahn(surface, boss, x, y)

def draw_ignis_drachorn(surface, boss, x, y):
    """Entry point ignis_drachorn."""
    return _NS_ignis_drachorn.draw_ignis_drachorn(surface, boss, x, y)
