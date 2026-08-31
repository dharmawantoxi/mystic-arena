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
    """Namespace zharok - PIXEL MASTERWORK v2 + SKILL FX v2.1.

    Rewrite penuh renderer `_NS_zharok` mengikuti standar
    **Thorne v2 Pixel Masterwork + Thorne v2.1 Skill FX**
    (lihat docs/THORNE_V2_RENDERER.md). Tetap 100% prosedural:
    tidak ada PNG / sprite-sheet / image.load.
    """

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    # ── cache (nama lama dipertahankan) ─────────────────────────────
    _shadow_cache = None
    _aura_cache = None
    _flash_buf = None
    _body_buf = None
    _record_shadow = None

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
        hit = _NS_zharok._DECAL_CACHE.get(key)
        if hit is not None:
            return hit
        surf = builder(size)
        _NS_zharok._DECAL_CACHE[key] = surf
        _NS_zharok._DECAL_ORDER.append(key)
        if len(_NS_zharok._DECAL_ORDER) > 128:
            old = _NS_zharok._DECAL_ORDER.pop(0)
            _NS_zharok._DECAL_CACHE.pop(old, None)
        return surf

    @staticmethod
    def _blit_decal(surface, decal, cx, cy, alpha=255, add=False):
        alpha = _NS_zharok._alpha(alpha)
        if alpha <= 0:
            return
        w, h = decal.get_size()
        x0 = int(cx) - w // 2
        y0 = int(cy) - h // 2
        flags = pygame.BLEND_RGBA_ADD if add else 0
        if alpha < 255:
            decal.set_alpha(alpha)
            surface.blit(decal, (x0, y0), special_flags=flags)
            decal.set_alpha(255)
        else:
            surface.blit(decal, (x0, y0), special_flags=flags)

    @staticmethod
    def _quantize(v, step=6):
        return max(step, int(round(float(v) / step) * step))

    @staticmethod
    def _build_falloff_ring(size, color, core, thickness, softness, inner_glow):
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
            pygame.draw.circle(surf, (*col, int(200 * t)), (c, c), r, 1)
        if inner_glow > 0:
            for r in range(lo, 0, -2):
                t = (r / float(max(1, lo))) ** 2
                a = int(inner_glow * t)
                if a > 1:
                    pygame.draw.circle(surf, (*color, a), (c, c), r, 2)
        return surf

    @staticmethod
    def _ground_ring(surface, cx, cy, radius, color, core, alpha,
                     thickness=3, softness=7, inner_glow=0, add=True):
        radius = _NS_zharok._quantize(radius, 6)
        if radius < 6:
            return
        pad = softness + thickness + 3
        size = radius * 2 + pad * 2
        key = ("fring", radius, color, core, thickness, softness, inner_glow)
        decal = _NS_zharok._decal(
            key, size,
            lambda n: _NS_zharok._build_falloff_ring(
                n, color, core, thickness, softness, inner_glow))
        _NS_zharok._blit_decal(surface, decal, cx, cy, alpha, add=add)

    @staticmethod
    def _build_arc_ring(size, color, core, segments, span, thickness, softness, taper):
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
                pygame.draw.polygon(surf, (*color, 210), poly)
                if core:
                    core_pts = []
                    for s in range(1, steps):
                        u = s / float(steps)
                        ang = a0 + (a1 - a0) * u
                        ca, sa = math.cos(ang), math.sin(ang)
                        core_pts.append((c + ca * r_nom, c + sa * r_nom))
                    if len(core_pts) >= 2:
                        pygame.draw.lines(surf, (*core, 230), False, core_pts, 1)
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
        key = ("rring", radius, color, core, segments, span, thickness, softness, taper)
        decal = _NS_zharok._decal(
            key, size,
            lambda n: _NS_zharok._build_arc_ring(
                n, color, core, segments, span, thickness, softness, taper))
        deg = -math.degrees(phase) % (360.0 / max(1, segments))
        rot = pygame.transform.rotate(decal, deg)
        _NS_zharok._blit_decal(surface, rot, cx, cy, alpha, add=add)

    @staticmethod
    def _build_zone_fill(size, color, core, falloff_exp, rim_boost):
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
                pygame.draw.circle(surf, (*col, a), (c, c), r, 2)
        return surf

    @staticmethod
    def _zone_fill(surface, cx, cy, radius, color, core, alpha,
                   falloff_exp=2.2, rim_boost=1.0, add=True):
        radius = _NS_zharok._quantize(radius, 8)
        if radius < 8:
            return
        size = radius * 2 + 4
        key = ("zfill", radius, color, core, falloff_exp, rim_boost)
        decal = _NS_zharok._decal(
            key, size,
            lambda n: _NS_zharok._build_zone_fill(
                n, color, core, falloff_exp, rim_boost))
        _NS_zharok._blit_decal(surface, decal, cx, cy, alpha, add=add)

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
    def _build_radial_glow(size, color, core):
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
                pygame.draw.circle(surf, (*col, a), (c, c), r, 2)
        return surf

    @staticmethod
    def _glow(surface, cx, cy, radius, color, core=None, alpha=255, add=True):
        core = core or _NS_zharok.PALETTE["fire_white"]
        radius = _NS_zharok._quantize(radius, 6)
        if radius < 4:
            return
        size = radius * 2 + 4
        key = ("glow", radius, color, core)
        decal = _NS_zharok._decal(
            key, size,
            lambda n: _NS_zharok._build_radial_glow(n, color, core))
        _NS_zharok._blit_decal(surface, decal, cx, cy, alpha, add=add)

    @staticmethod
    def _draw_shockwave(surface, cx, cy, radius, color, alpha, thickness=3):
        alpha = _NS_zharok._alpha(alpha)
        if alpha <= 0 or radius <= 2:
            return
        _NS_zharok._ground_ring(surface, cx, cy, radius, color,
                                _NS_zharok.PALETTE["fire_white"], alpha,
                                thickness=thickness, softness=4, add=True)

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
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0
        breath = math.sin(phase * 0.8)

        if walk:
            root_y = int(math.sin(phase * 2.4) * 2.5)
            sway = int(math.sin(phase * 1.2) * 2.5)
            lean = 3 * f
            cloth_lag = math.sin(phase * 2.0) * 3.0
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

        _NS_zharok._draw_hood_back(surface, ox, oy - 14, facing, phase, cloth_lag=cloth_lag, f=f)
        _NS_zharok._draw_quiver(surface, ox, oy - 14, facing, phase, f=f)
        _NS_zharok._draw_pelvis(surface, ox, oy + 8, phase, f=f)
        _NS_zharok._draw_skeleton_legs(surface, ox, oy + 8, facing, phase, action, f=f)
        _NS_zharok._draw_ribcage(surface, ox, oy - 12, phase, sway=sway, f=f)
        _NS_zharok._draw_hooded_skull(surface, ox, oy - 26, facing, phase, action=action, f=f, stealth=stealth, detail=detail)

        if attack:
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
        return (abs(x - lx) + abs(y - ly)) > 0.3

    @staticmethod
    def _update_attack_anim(boss):
        active = getattr(boss, "_zh_attack_active", False)
        cd = max(2, int(getattr(boss, "attack_cooldown", 40)))
        timer = int(getattr(boss, "timer", 0))

        if timer >= cd - 15 and not active:
            boss._zh_attack_active = True
            boss._zh_attack_progress = 0.0

        if getattr(boss, "_zh_attack_active", False):
            boss._zh_attack_progress = getattr(boss, "_zh_attack_progress", 0.0) + 1.0 / 15.0
            if boss._zh_attack_progress >= 1.0:
                boss._zh_attack_active = False
                boss._zh_attack_progress = 0.0

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
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_zharok._detect_moving(boss)
        _NS_zharok._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_zh_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        portrait = bool(getattr(boss, "_portrait_hd", False))

        if not portrait:
            _NS_zharok._draw_fire_aura(surface, x, y, pulse, active_skill)
            _NS_zharok._draw_ground_runes(surface, x, y + _NS_zharok.GROUND_DY, pulse, active_skill)

            if active_skill == "q":
                _NS_zharok._draw_strafe_ground(surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "e":
                _NS_zharok._draw_death_pact_ground(surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "r":
                _NS_zharok._draw_burning_army_ground(surface, boss, x, y, skill_timer, pulse)

        if active_skill == "w":
            _NS_zharok._draw_zh_smoke(surface, boss, x, y, skill_timer, pulse)
        else:
            if attacking:
                _NS_zharok._draw_zh_attack(surface, boss, x, y)
            elif active_skill == "q":
                _NS_zharok._draw_zh_strafe(surface, boss, x, y, skill_timer)
            elif active_skill == "e":
                _NS_zharok._draw_zh_ecast(surface, boss, x, y, skill_timer)
            elif active_skill == "r":
                _NS_zharok._draw_zh_rcast(surface, boss, x, y, skill_timer)
            elif moving:
                _NS_zharok._draw_zh_walk(surface, boss, x, y)
            else:
                _NS_zharok._draw_zh_idle(surface, boss, x, y)

        if not portrait:
            _NS_zharok._handle_skill_projectiles(boss, x, y, active_skill, skill_timer)
            _NS_zharok._manage_projectiles(boss, surface, pulse)

            if active_skill == "q":
                _NS_zharok._draw_strafe_foreground(surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "e":
                _NS_zharok._draw_death_pact_foreground(surface, boss, x, y, skill_timer, pulse)

    @staticmethod
    def draw_boss(surface, boss, x, y):
        _NS_zharok.draw_zharok(surface, boss, x, y)



# ====================================================================
# PYRENTH
# ====================================================================
class _NS_pyrenth:
    """Namespace pyrenth - isi asli tidak diubah."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

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


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_pyr_last_x"):
            boss._pyr_last_x = boss.x
            boss._pyr_last_y = boss.y
            return False
        dx = abs(boss.x - boss._pyr_last_x)
        dy = abs(boss.y - boss._pyr_last_y)
        boss._pyr_last_x = boss.x
        boss._pyr_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_pyr_prev_timer", 0))
        active = bool(getattr(boss, "_pyr_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._pyr_attack_active = True
            boss._pyr_attack_frame = 0
            active = True
        elif active:
            boss._pyr_attack_frame = int(getattr(boss, "_pyr_attack_frame", 0)) + 1
            if boss._pyr_attack_frame > cooldown:
                boss._pyr_attack_active = False
                boss._pyr_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._pyr_attack_active = False
            boss._pyr_attack_frame = 0
            active = False

        boss._pyr_prev_timer = timer
        boss._pyr_attack_progress = (
            min(1.0, getattr(boss, "_pyr_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


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
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_pyrenth._detect_moving(boss)
        _NS_pyrenth._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_pyr_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # BG aura
        _NS_pyrenth._draw_hellfire_aura(surface, x, y, pulse, active_skill)
        _NS_pyrenth._draw_ground_runes(surface, x, y + 46, pulse, active_skill)

        # Skill ground effects
        if active_skill == "e":
            _NS_pyrenth._draw_scorched_earth_ground(surface, boss, x, y, skill_timer, pulse)

        # Character
        if attacking:
            _NS_pyrenth._draw_pyr_attack(surface, boss, x, y)
        elif active_skill == "q":
            _NS_pyrenth._draw_pyr_qcast(surface, boss, x, y, skill_timer)
        elif active_skill == "w":
            _NS_pyrenth._draw_pyr_wcast(surface, boss, x, y, skill_timer)
        elif active_skill == "e":
            _NS_pyrenth._draw_pyr_ecast(surface, boss, x, y, skill_timer)
        elif active_skill == "r":
            _NS_pyrenth._draw_pyr_rcast(surface, boss, x, y, skill_timer)
        elif moving:
            _NS_pyrenth._draw_pyr_walk(surface, boss, x, y)
        else:
            _NS_pyrenth._draw_pyr_idle(surface, boss, x, y)

        # Skill triggers
        _NS_pyrenth._handle_skill_projectiles(boss, x, y, active_skill, skill_timer)

        # Projectiles/effects
        _NS_pyrenth._manage_projectiles(boss, surface, pulse)

        # Foreground skill effects
        if active_skill == "e":
            _NS_pyrenth._draw_scorched_earth(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_pyrenth._draw_devour_effect(surface, boss, x, y, skill_timer, pulse)


    def _handle_skill_projectiles(boss, x, y, active_skill, timer):
        tx, ty = _NS_pyrenth._target_position(boss, x, y)

        if active_skill == "q":
            duration = 70
            progress = max(0.0, min(1.0, 1 - timer / duration))
            if 0.25 < progress < 0.35 and not getattr(boss, "_pyr_q_spawned", False):
                sx = x + 20 * boss.direction
                sy = y - 5
                _NS_pyrenth._spawn_doom_chain(boss, sx, sy, tx, ty)
                boss._pyr_q_spawned = True
            if progress > 0.7:
                boss._pyr_q_spawned = False

        elif active_skill == "r":
            duration = 60
            progress = max(0.0, min(1.0, 1 - timer / duration))
            if 0.35 < progress < 0.45 and not getattr(boss, "_pyr_r_spawned", False):
                _NS_pyrenth._spawn_infernal_arc(boss, x + 15 * boss.direction, y, boss.direction)
                boss._pyr_r_spawned = True
            if progress > 0.7:
                boss._pyr_r_spawned = False


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_pyr_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 3)
        _NS_pyrenth._draw_shadow(surface, x, y + 58)
        _NS_pyrenth._draw_hellfire_wisps(surface, x, y + 42, boss.pulse)
        _NS_pyrenth._draw_pyr_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_pyr_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(math.sin(phase * 1.2) * 4)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_pyrenth._draw_shadow(surface, x + sway, y + 58)
        _NS_pyrenth._draw_hellfire_wisps(surface, x + sway, y + 42, phase, trail=True,
                             facing=boss.direction)
        _NS_pyrenth._draw_pyr_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_pyr_attack(surface, boss, x, y):
        progress = getattr(boss, "_pyr_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        lunge = int(math.sin(progress * math.pi) * 5) * boss.direction

        _NS_pyrenth._draw_shadow(surface, x + lunge, y + 58)
        _NS_pyrenth._draw_hellfire_wisps(surface, x + lunge, y + 42, boss.pulse, intense=True)
        _NS_pyrenth._draw_pyr_body(surface, x + lunge, y, boss.direction, boss.pulse,
                       "attack", progress)
        _NS_pyrenth._draw_sword_swing_arc(surface, x + lunge, y, boss.direction, progress)
        _NS_pyrenth._draw_swing_impact(surface, x + lunge, y, boss.direction, progress)


    def _draw_pyr_qcast(surface, boss, x, y, timer):
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        _NS_pyrenth._draw_shadow(surface, x, y + 58)
        _NS_pyrenth._draw_hellfire_wisps(surface, x, y + 42, boss.pulse, intense=True)
        _NS_pyrenth._draw_pyr_body(surface, x, y + bob, boss.direction, boss.pulse,
                       "q_cast", progress)


    def _draw_pyr_wcast(surface, boss, x, y, timer):
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        _NS_pyrenth._draw_shadow(surface, x, y + 58)
        _NS_pyrenth._draw_hellfire_wisps(surface, x, y + 42, boss.pulse, intense=True)
        _NS_pyrenth._draw_pyr_body(surface, x, y + bob, boss.direction, boss.pulse,
                       "w_cast", progress)


    def _draw_pyr_ecast(surface, boss, x, y, timer):
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        _NS_pyrenth._draw_shadow(surface, x, y + 58)
        _NS_pyrenth._draw_hellfire_wisps(surface, x, y + 42, boss.pulse, intense=True)
        _NS_pyrenth._draw_pyr_body(surface, x, y + bob, boss.direction, boss.pulse,
                       "e_cast", progress)


    def _draw_pyr_rcast(surface, boss, x, y, timer):
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        lunge = int(math.sin(progress * math.pi) * 8) * boss.direction

        _NS_pyrenth._draw_shadow(surface, x + lunge, y + 58)
        _NS_pyrenth._draw_hellfire_wisps(surface, x + lunge, y + 42, boss.pulse, intense=True)
        _NS_pyrenth._draw_pyr_body(surface, x + lunge, y, boss.direction, boss.pulse,
                       "r_cast", progress)


    # ===================================================================
    # BODY RENDERING
    # ===================================================================
    def _draw_pyr_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Full demon composition."""
        is_casting = action.endswith("_cast")

        # Wings drawn first (spread wide behind)
        _NS_pyrenth._draw_wings(surface, cx, cy - 5, facing, phase, action)

        # Tail (behind)
        _NS_pyrenth._draw_tail(surface, cx, cy + 15, facing, phase)

        # Lower body (loincloth + belt)
        _NS_pyrenth._draw_lower_body(surface, cx, cy + 12, phase)

        # Torso (huge muscular chest with armor)
        _NS_pyrenth._draw_torso(surface, cx, cy - 5, phase, is_casting)

        # Shoulder pauldrons
        _NS_pyrenth._draw_pauldrons(surface, cx, cy - 15, phase)

        # Arms + sword
        if action == "attack":
            _NS_pyrenth._draw_attack_arms(surface, cx, cy - 5, facing, phase, attack_progress)
        elif action == "r_cast":
            _NS_pyrenth._draw_r_arms(surface, cx, cy - 5, facing, phase, attack_progress)
        elif action == "q_cast":
            _NS_pyrenth._draw_q_cast_arms(surface, cx, cy - 5, facing, phase)
        elif action == "w_cast":
            _NS_pyrenth._draw_w_cast_arms(surface, cx, cy - 5, facing, phase, attack_progress)
        elif action == "e_cast":
            _NS_pyrenth._draw_e_cast_arms(surface, cx, cy - 5, facing, phase)
        else:
            _NS_pyrenth._draw_idle_arms(surface, cx, cy - 5, facing, phase)

        # Head with horns
        _NS_pyrenth._draw_pyr_head(surface, cx, cy - 30, facing, phase, is_casting)


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


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Sword in front hand, other arm at side."""
        sway = math.sin(phase * 0.7) * 2

        # Back arm - hanging
        back_side = -facing
        sh_x = cx + back_side * 16
        sh_y = cy - 2
        elbow_x = sh_x + back_side * 8
        elbow_y = cy + 10 + int(sway)
        hand_x = elbow_x + back_side * 4
        hand_y = elbow_y + 10

        _NS_pyrenth._draw_pyr_arm(surface, sh_x, sh_y, elbow_x, elbow_y)
        _NS_pyrenth._draw_pyr_arm(surface, elbow_x, elbow_y, hand_x, hand_y)
        _NS_pyrenth._draw_claw_hand(surface, hand_x, hand_y, back_side)

        # Front arm - holding sword
        fs_x = cx + facing * 16
        fs_y = cy - 2
        fe_x = fs_x + facing * 8
        fe_y = cy + 10 + int(sway)
        fh_x = fe_x + facing * 4
        fh_y = fe_y + 10

        _NS_pyrenth._draw_pyr_arm(surface, fs_x, fs_y, fe_x, fe_y)
        _NS_pyrenth._draw_pyr_arm(surface, fe_x, fe_y, fh_x, fh_y)
        _NS_pyrenth._draw_claw_hand(surface, fh_x, fh_y, facing)

        # Flaming sword held down/forward
        _NS_pyrenth._draw_flaming_sword(surface, fh_x, fh_y, facing, "down", phase)


    def _draw_attack_arms(surface, cx, cy, facing, phase, progress):
        """Overhead sword swing."""
        # Back arm at side
        back_side = -facing
        sh_x = cx + back_side * 16
        sh_y = cy - 2
        elbow_x = sh_x + back_side * 6
        elbow_y = cy + 8
        hand_x = elbow_x + back_side * 3
        hand_y = elbow_y + 8
        _NS_pyrenth._draw_pyr_arm(surface, sh_x, sh_y, elbow_x, elbow_y)
        _NS_pyrenth._draw_pyr_arm(surface, elbow_x, elbow_y, hand_x, hand_y)
        _NS_pyrenth._draw_claw_hand(surface, hand_x, hand_y, back_side)

        # Front arm swings
        fs_x = cx + facing * 16
        fs_y = cy - 2

        if progress < 0.25:
            t = progress / 0.25
            t = t * t * (3 - 2 * t)
            arm_angle = -1.4 + 0.2 * t
        elif progress < 0.55:
            t = (progress - 0.25) / 0.30
            t = 1 - (1 - t) ** 3
            arm_angle = -1.2 + 2.4 * t
        else:
            t = (progress - 0.55) / 0.45
            arm_angle = 1.2 - 0.9 * t

        arm_len = 18
        fh_x = fs_x + int(math.cos(arm_angle) * arm_len) * facing
        fh_y = fs_y + int(math.sin(arm_angle) * arm_len)
        elbow_x2 = fs_x + int(math.cos(arm_angle) * arm_len * 0.55) * facing
        elbow_y2 = fs_y + int(math.sin(arm_angle) * arm_len * 0.55)

        _NS_pyrenth._draw_pyr_arm(surface, fs_x, fs_y, elbow_x2, elbow_y2)
        _NS_pyrenth._draw_pyr_arm(surface, elbow_x2, elbow_y2, fh_x, fh_y)
        _NS_pyrenth._draw_claw_hand(surface, fh_x, fh_y, facing)

        # Sword swinging
        sword_angle = arm_angle + math.pi / 4 * facing
        _NS_pyrenth._draw_flaming_sword_angled(surface, fh_x, fh_y, facing, sword_angle, phase)


    def _draw_r_arms(surface, cx, cy, facing, phase, progress):
        """R - Infernal Blade huge swing."""
        # Similar to attack but bigger arc
        back_side = -facing
        sh_x = cx + back_side * 16
        sh_y = cy - 2
        hand_x = sh_x + back_side * 5
        hand_y = cy + 10
        _NS_pyrenth._draw_pyr_arm(surface, sh_x, sh_y, hand_x, hand_y)
        _NS_pyrenth._draw_claw_hand(surface, hand_x, hand_y, back_side)

        fs_x = cx + facing * 16
        fs_y = cy - 2

        if progress < 0.3:
            t = progress / 0.3
            arm_angle = -1.6 + 0.4 * t
        elif progress < 0.6:
            t = (progress - 0.3) / 0.3
            arm_angle = -1.2 + 2.8 * t
        else:
            t = (progress - 0.6) / 0.4
            arm_angle = 1.6 - 1.2 * t

        arm_len = 20
        fh_x = fs_x + int(math.cos(arm_angle) * arm_len) * facing
        fh_y = fs_y + int(math.sin(arm_angle) * arm_len)
        elbow_x = fs_x + int(math.cos(arm_angle) * arm_len * 0.55) * facing
        elbow_y = fs_y + int(math.sin(arm_angle) * arm_len * 0.55)

        _NS_pyrenth._draw_pyr_arm(surface, fs_x, fs_y, elbow_x, elbow_y)
        _NS_pyrenth._draw_pyr_arm(surface, elbow_x, elbow_y, fh_x, fh_y)
        _NS_pyrenth._draw_claw_hand(surface, fh_x, fh_y, facing)

        sword_angle = arm_angle + math.pi / 4 * facing
        _NS_pyrenth._draw_flaming_sword_angled(surface, fh_x, fh_y, facing, sword_angle, phase,
                                    size=1.3)


    def _draw_q_cast_arms(surface, cx, cy, facing, phase):
        """Q cast - front arm extended forward, sword pointing."""
        # Back arm
        back_side = -facing
        sh_x = cx + back_side * 16
        sh_y = cy - 2
        hand_x = sh_x + back_side * 5
        hand_y = cy + 8
        _NS_pyrenth._draw_pyr_arm(surface, sh_x, sh_y, hand_x, hand_y)
        _NS_pyrenth._draw_claw_hand(surface, hand_x, hand_y, back_side)

        # Front arm extended forward with pointing gesture
        fs_x = cx + facing * 16
        fs_y = cy - 2
        fe_x = fs_x + facing * 10
        fe_y = cy - 2
        fh_x = fe_x + facing * 12
        fh_y = fe_y

        _NS_pyrenth._draw_pyr_arm(surface, fs_x, fs_y, fe_x, fe_y)
        _NS_pyrenth._draw_pyr_arm(surface, fe_x, fe_y, fh_x, fh_y)
        _NS_pyrenth._draw_claw_hand(surface, fh_x, fh_y, facing)

        # Fire energy at pointing hand
        pulse = math.sin(phase * 4) * 0.3 + 0.7
        r = int(6 * pulse)
        _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_darkest"], 150),
                  (fh_x + facing * 3, fh_y), r + 4)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_mid"], (fh_x + facing * 3, fh_y), r + 2)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_bright"], (fh_x + facing * 3, fh_y), r)
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_hot"], (fh_x + facing * 3, fh_y), max(1, r - 2))
        _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_glow"], (fh_x + facing * 3, fh_y), max(1, r - 4))


    def _draw_w_cast_arms(surface, cx, cy, facing, phase, progress):
        """W - Devour, reach out with claw."""
        # Back arm holds sword
        back_side = -facing
        sh_x = cx + back_side * 16
        sh_y = cy - 2
        elbow_x = sh_x + back_side * 6
        elbow_y = cy + 8
        hand_x = elbow_x + back_side * 4
        hand_y = elbow_y + 8
        _NS_pyrenth._draw_pyr_arm(surface, sh_x, sh_y, elbow_x, elbow_y)
        _NS_pyrenth._draw_pyr_arm(surface, elbow_x, elbow_y, hand_x, hand_y)
        _NS_pyrenth._draw_claw_hand(surface, hand_x, hand_y, back_side)
        _NS_pyrenth._draw_flaming_sword(surface, hand_x, hand_y, back_side, "down", phase)

        # Front arm reaches forward with big claw
        fs_x = cx + facing * 16
        fs_y = cy - 2
        # Extended
        reach = int(15 + math.sin(progress * math.pi) * 5)
        fe_x = fs_x + facing * 10
        fe_y = cy
        fh_x = fs_x + facing * (10 + reach)
        fh_y = cy - 2

        _NS_pyrenth._draw_pyr_arm(surface, fs_x, fs_y, fe_x, fe_y)
        _NS_pyrenth._draw_pyr_arm(surface, fe_x, fe_y, fh_x, fh_y)

        # Big grasping claw
        _NS_pyrenth._draw_big_claw(surface, fh_x, fh_y, facing, phase)


    def _draw_e_cast_arms(surface, cx, cy, facing, phase):
        """E - Scorched Earth, both arms raised."""
        for side in (-1, 1):
            sh_x = cx + side * 16
            sh_y = cy - 2
            # Both raised up
            elbow_x = sh_x + side * 8
            elbow_y = cy - 6
            hand_x = elbow_x + side * 5
            hand_y = cy - 14

            _NS_pyrenth._draw_pyr_arm(surface, sh_x, sh_y, elbow_x, elbow_y)
            _NS_pyrenth._draw_pyr_arm(surface, elbow_x, elbow_y, hand_x, hand_y)
            _NS_pyrenth._draw_claw_hand(surface, hand_x, hand_y, side)

            # Fire energy in both hands
            pulse = math.sin(phase * 4 + side) * 0.3 + 0.7
            r = int(7 * pulse)
            _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_darkest"], 150), (hand_x, hand_y), r + 4)
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_mid"], (hand_x, hand_y), r + 2)
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_bright"], (hand_x, hand_y), r)
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_hot"], (hand_x, hand_y), max(1, r - 2))
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_glow"], (hand_x, hand_y), max(1, r - 4))
            _NS_pyrenth._aacircle(surface, _NS_pyrenth.PALETTE["fire_white"], (hand_x, hand_y), max(1, r - 5))


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
        """Fire trail from sword swing."""
        if progress < 0.28 or progress > 0.75:
            return
        if progress < 0.5:
            visibility = (progress - 0.28) / 0.22
        else:
            visibility = 1.0 - (progress - 0.5) / 0.25
        visibility = max(0.0, min(1.0, visibility))

        arc = pygame.Surface((180, 130), pygame.SRCALPHA)
        for i in range(22):
            t = i / 21
            angle = -math.pi * 0.9 + t * math.pi * 1.1
            px = 90 + int(math.cos(angle) * 65) * facing
            py = 65 + int(math.sin(angle) * 48)
            alpha = int((220 - i * 9) * visibility)
            if alpha <= 0:
                continue
            _NS_pyrenth._aacircle(arc, (*_NS_pyrenth.PALETTE["fire_darkest"], alpha), (px, py), 11)
            _NS_pyrenth._aacircle(arc, (*_NS_pyrenth.PALETTE["fire_dark"], alpha), (px, py), 8)
            _NS_pyrenth._aacircle(arc, (*_NS_pyrenth.PALETTE["fire_mid"], alpha), (px, py), 6)
            _NS_pyrenth._aacircle(arc, (*_NS_pyrenth.PALETTE["fire_bright"], alpha), (px, py), 4)
            _NS_pyrenth._aacircle(arc, (*_NS_pyrenth.PALETTE["fire_hot"], alpha), (px, py), 2)
            _NS_pyrenth._aacircle(arc, (*_NS_pyrenth.PALETTE["fire_glow"], min(255, alpha)), (px, py), 1)
        surface.blit(arc, (x - 90, y - 65))


    def _draw_swing_impact(surface, x, y, facing, progress):
        if progress < 0.5 or progress > 0.85:
            return
        t = (progress - 0.5) / 0.35
        intensity = math.sin(t * math.pi)

        impact_x = x + 45 * facing
        impact_y = y + 5
        alpha = int(240 * intensity)
        radius = int(12 + intensity * 25)

        _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_dark"], alpha // 2),
                  (impact_x, impact_y), radius + 5)
        _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_bright"], alpha),
                  (impact_x, impact_y), radius, 3)
        _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_hot"], alpha),
                  (impact_x, impact_y), max(1, radius - 6), 2)
        _NS_pyrenth._aacircle(surface, (*_NS_pyrenth.PALETTE["fire_glow"], alpha),
                  (impact_x, impact_y), max(1, radius - 12))

        for i in range(12):
            angle = i * math.pi / 6 + progress * 3
            dx = impact_x + int(math.cos(angle) * radius * 1.3)
            dy = impact_y + int(math.sin(angle) * radius * 0.9)
            _NS_pyrenth._draw_ember(surface, dx, dy, 2, alpha)


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
    # Backward compatible alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_pyrenth.draw_pyrenth(surface, boss, x, y)


# ====================================================================
# VOKRAHN
# ====================================================================
class _NS_vokrahn:
    """Namespace vokrahn - isi asli tidak diubah."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Chaos Palette - Black armor / red flame / dark horse
    # ---------------------------------------------------------------------------
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
    def _detect_moving(boss):
        if not hasattr(boss, "_vok_last_x"):
            boss._vok_last_x = boss.x
            boss._vok_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vok_last_x)
        dy = abs(boss.y - boss._vok_last_y)
        boss._vok_last_x = boss.x
        boss._vok_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vok_prev_timer", 0))
        active = bool(getattr(boss, "_vok_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._vok_attack_active = True
            boss._vok_attack_frame = 0
            active = True
        elif active:
            boss._vok_attack_frame = int(getattr(boss, "_vok_attack_frame", 0)) + 1
            if boss._vok_attack_frame > cooldown:
                boss._vok_attack_active = False
                boss._vok_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._vok_attack_active = False
            boss._vok_attack_frame = 0
            active = False

        boss._vok_prev_timer = timer
        boss._vok_attack_progress = (
            min(1.0, getattr(boss, "_vok_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


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
    def draw_vokrahn(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_vokrahn._detect_moving(boss)
        _NS_vokrahn._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_vok_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # BG aura
        _NS_vokrahn._draw_chaos_aura(surface, x, y, pulse, active_skill)
        _NS_vokrahn._draw_ground_runes(surface, x, y + 48, pulse, active_skill)

        # Ground skill effects
        if active_skill == "w":
            _NS_vokrahn._draw_realm_of_chaos_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vokrahn._draw_phantasm_ground(surface, boss, x, y, skill_timer, pulse)

        # Phantasm illusions (behind main body)
        if active_skill == "r":
            _NS_vokrahn._draw_phantasm_illusions(surface, boss, x, y, skill_timer, pulse)

        # Character
        if active_skill == "e":
            _NS_vokrahn._draw_vok_dashing(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_vokrahn._draw_vok_attack(surface, boss, x, y)
        elif active_skill == "q":
            _NS_vokrahn._draw_vok_qcast(surface, boss, x, y, skill_timer)
        elif moving:
            _NS_vokrahn._draw_vok_walk(surface, boss, x, y)
        else:
            _NS_vokrahn._draw_vok_idle(surface, boss, x, y)

        # Skill projectile triggers
        _NS_vokrahn._handle_skill_projectiles(boss, x, y, active_skill, skill_timer)

        # Projectiles
        _NS_vokrahn._manage_projectiles(boss, surface, pulse)

        # Foreground skill effects
        if active_skill == "w":
            _NS_vokrahn._draw_realm_of_chaos(surface, boss, x, y, skill_timer, pulse)


    def _handle_skill_projectiles(boss, x, y, active_skill, timer):
        tx, ty = _NS_vokrahn._target_position(boss, x, y)

        if active_skill == "q":
            duration = 55
            progress = max(0.0, min(1.0, 1 - timer / duration))
            if 0.35 < progress < 0.45 and not getattr(boss, "_vok_q_spawned", False):
                sx = x + 25 * boss.direction
                sy = y - 15
                _NS_vokrahn._spawn_chaos_bolt(boss, sx, sy, tx, ty)
                boss._vok_q_spawned = True
            if progress > 0.7:
                boss._vok_q_spawned = False


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_vok_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        _NS_vokrahn._draw_shadow(surface, x, y + 58)
        _NS_vokrahn._draw_chaos_wisps(surface, x, y + 44, boss.pulse)
        _NS_vokrahn._draw_vok_full(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_vok_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_vokrahn._draw_shadow(surface, x + sway, y + 58)
        _NS_vokrahn._draw_chaos_wisps(surface, x + sway, y + 44, phase, trail=True,
                         facing=boss.direction)
        _NS_vokrahn._draw_vok_full(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_vok_attack(surface, boss, x, y):
        progress = getattr(boss, "_vok_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        lunge = int(math.sin(progress * math.pi) * 5) * boss.direction

        _NS_vokrahn._draw_shadow(surface, x + lunge, y + 58)
        _NS_vokrahn._draw_chaos_wisps(surface, x + lunge, y + 44, boss.pulse, intense=True)
        _NS_vokrahn._draw_vok_full(surface, x + lunge, y, boss.direction, boss.pulse,
                       "attack", progress)
        _NS_vokrahn._draw_sword_swing_arc(surface, x + lunge, y, boss.direction, progress)
        _NS_vokrahn._draw_swing_impact(surface, x + lunge, y, boss.direction, progress)


    def _draw_vok_qcast(surface, boss, x, y, timer):
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        recoil = int(math.sin(progress * math.pi * 2) * 2) * -boss.direction
        _NS_vokrahn._draw_shadow(surface, x + recoil, y + 58)
        _NS_vokrahn._draw_chaos_wisps(surface, x + recoil, y + 44, boss.pulse, intense=True)
        _NS_vokrahn._draw_vok_full(surface, x + recoil, y + bob, boss.direction, boss.pulse,
                       "q_cast", progress)


    def _draw_vok_dashing(surface, boss, x, y, timer, phase):
        """E - Chaos Strike dash forward with motion blur."""
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        bob = int(math.sin(phase * 1.5) * 2)

        # Dash offset - moves toward target then back
        if progress < 0.3:
            offset = int(80 * (progress / 0.3)) * boss.direction
        elif progress < 0.6:
            offset = int(80 * boss.direction)
            # Spawn impact burst at peak
            if not getattr(boss, "_vok_e_burst", False):
                tx, ty = _NS_vokrahn._target_position(boss, x, y)
                _NS_vokrahn._spawn_burst(boss, x + offset, y, size=35, life=25)
                boss._vok_e_burst = True
        else:
            t = (progress - 0.6) / 0.4
            offset = int(80 * (1 - t)) * boss.direction

        if progress < 0.1:
            boss._vok_e_burst = False

        _NS_vokrahn._draw_shadow(surface, x + offset, y + 58)
        _NS_vokrahn._draw_chaos_wisps(surface, x + offset, y + 44, phase, intense=True)

        # Motion blur behind
        if 0.15 < progress < 0.65:
            for i in range(4):
                blur_offset = (i + 1) * -12 * boss.direction + offset
                alpha = int(140 - i * 30)
                temp = pygame.Surface((180, 180), pygame.SRCALPHA)
                _NS_vokrahn._draw_vok_full(temp, 90, 90, boss.direction, phase, "dash")
                temp.set_alpha(alpha)
                surface.blit(temp, (x + blur_offset - 90, y + bob - 90))

        _NS_vokrahn._draw_vok_full(surface, x + offset, y + bob, boss.direction, phase, "dash")

        # Sword trail
        _NS_vokrahn._draw_dash_trail(surface, x + offset, y, boss.direction, progress)


    # ===================================================================
    # FULL COMPOSITE - Horse + Knight rider
    # ===================================================================
    def _draw_vok_full(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Cape drawn first (behind everything)
        _NS_vokrahn._draw_cape(surface, cx - 6 * facing, cy - 20, facing, phase, action)

        # Horse tail (behind body)
        _NS_vokrahn._draw_horse_tail(surface, cx, cy + 12, facing, phase, action)

        # Horse body
        _NS_vokrahn._draw_horse_body(surface, cx, cy + 8, facing, phase)

        # Horse legs
        _NS_vokrahn._draw_horse_legs(surface, cx, cy + 22, facing, phase, action)

        # Horse head (front)
        _NS_vokrahn._draw_horse_head(surface, cx + 20 * facing, cy + 5, facing, phase)

        # Horse mane (behind rider)
        _NS_vokrahn._draw_horse_mane(surface, cx + 8 * facing, cy - 2, facing, phase)

        # KNIGHT rider on top
        _NS_vokrahn._draw_knight_rider(surface, cx - 3 * facing, cy - 20, facing, phase, action,
                           attack_progress)


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


    def _draw_knight_rider(surface, cx, cy, facing, phase, action, attack_progress):
        """Heavy armored knight rider."""
        sway = int(math.sin(phase * 0.6) * 1)
        if action == "walk":
            sway += int(math.sin(phase * 2) * 1)

        # Legs (armored) straddling horse
        for side in (-1, 1):
            lx = cx + side * 4
            ly = cy + 12
            _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["shadow_deep"], (lx - 2 + 1, ly + 1, 4, 7),
                  border_radius=1)
            _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["arm_darkest"], (lx - 2, ly, 4, 7), border_radius=1)
            _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["arm_dark"], (lx - 2, ly, 4, 5))
            _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["arm_mid"], (lx - 1, ly + 1, 2, 3))
            # Red trim
            _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["red_mid"], (lx - 2, ly + 6, 4, 1))
            # Metal boot
            _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["metal_darkest"], (lx - 3, ly + 7, 6, 3), border_radius=1)
            _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["metal_dark"], (lx - 2, ly + 7, 4, 2))
            _NS_vokrahn._rect(surface, _NS_vokrahn.PALETTE["metal_light"], (lx - 2, ly + 7, 4, 1))

        # Torso
        _NS_vokrahn._draw_knight_torso(surface, cx + sway, cy, facing, phase)

        # Shield (back arm side)
        _NS_vokrahn._draw_shield(surface, cx + sway, cy - 2, facing, phase)

        # Head with helmet
        _NS_vokrahn._draw_knight_head(surface, cx + sway, cy - 12, facing, phase)

        # Arms + sword
        if action == "attack":
            _NS_vokrahn._draw_knight_attack_arms(surface, cx + sway, cy, facing, phase,
                                      attack_progress)
        elif action == "dash":
            _NS_vokrahn._draw_knight_dash_arms(surface, cx + sway, cy, facing, phase)
        elif action == "q_cast":
            _NS_vokrahn._draw_knight_cast_arms(surface, cx + sway, cy, facing, phase)
        else:
            _NS_vokrahn._draw_knight_idle_arms(surface, cx + sway, cy, facing, phase)


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


    def _draw_knight_idle_arms(surface, cx, cy, facing, phase):
        """One arm holding sword, other resting on shield."""
        sway = math.sin(phase * 0.7) * 1

        # Sword arm (front, facing)
        sword_side = facing
        sh_x = cx + sword_side * 10
        sh_y = cy - 4
        elbow_x = sh_x + sword_side * 4
        elbow_y = cy + 4 + int(sway)
        hand_x = elbow_x + sword_side * 2
        hand_y = elbow_y + 6

        _NS_vokrahn._draw_knight_arm(surface, sh_x, sh_y, elbow_x, elbow_y)
        _NS_vokrahn._draw_knight_arm(surface, elbow_x, elbow_y, hand_x, hand_y)
        _NS_vokrahn._draw_gauntlet(surface, hand_x, hand_y)

        # Sword held pointing down/forward
        _NS_vokrahn._draw_flaming_sword(surface, hand_x, hand_y, facing, "down", phase)

        # Back arm (shield-holding)
        other_side = -facing
        sh_x2 = cx + other_side * 10
        sh_y2 = cy - 4
        hand_x2 = sh_x2 + other_side * 3
        hand_y2 = cy + 4 + int(sway)
        _NS_vokrahn._draw_knight_arm(surface, sh_x2, sh_y2, hand_x2, hand_y2)
        _NS_vokrahn._draw_gauntlet(surface, hand_x2, hand_y2)


    def _draw_knight_attack_arms(surface, cx, cy, facing, phase, progress):
        """Overhead sword swing."""
        # Back arm - stays with shield
        other_side = -facing
        sh_x2 = cx + other_side * 10
        sh_y2 = cy - 4
        hand_x2 = sh_x2 + other_side * 3
        hand_y2 = cy + 4
        _NS_vokrahn._draw_knight_arm(surface, sh_x2, sh_y2, hand_x2, hand_y2)
        _NS_vokrahn._draw_gauntlet(surface, hand_x2, hand_y2)

        # Sword arm - overhead swing
        sword_side = facing
        sh_x = cx + sword_side * 10
        sh_y = cy - 4

        if progress < 0.25:
            # Wind up (raise sword back)
            t = progress / 0.25
            t = t * t * (3 - 2 * t)
            arm_angle = -1.4 + 0.2 * t
        elif progress < 0.55:
            # Swing down (fast)
            t = (progress - 0.25) / 0.30
            t = 1 - (1 - t) ** 3
            arm_angle = -1.2 + 2.4 * t
        else:
            # Recovery
            t = (progress - 0.55) / 0.45
            arm_angle = 1.2 - 0.9 * t

        arm_len = 14
        hand_x = sh_x + int(math.cos(arm_angle) * arm_len) * facing
        hand_y = sh_y + int(math.sin(arm_angle) * arm_len)
        elbow_x = sh_x + int(math.cos(arm_angle) * arm_len * 0.55) * facing
        elbow_y = sh_y + int(math.sin(arm_angle) * arm_len * 0.55)

        _NS_vokrahn._draw_knight_arm(surface, sh_x, sh_y, elbow_x, elbow_y)
        _NS_vokrahn._draw_knight_arm(surface, elbow_x, elbow_y, hand_x, hand_y)
        _NS_vokrahn._draw_gauntlet(surface, hand_x, hand_y)

        # Sword angled
        sword_angle = arm_angle + math.pi / 4 * facing
        _NS_vokrahn._draw_flaming_sword_angled(surface, hand_x, hand_y, facing, sword_angle, phase)


    def _draw_knight_dash_arms(surface, cx, cy, facing, phase):
        """Dash pose - sword extended forward."""
        # Back arm - shield
        other_side = -facing
        sh_x2 = cx + other_side * 10
        sh_y2 = cy - 4
        hand_x2 = sh_x2 + other_side * 3
        hand_y2 = cy + 3
        _NS_vokrahn._draw_knight_arm(surface, sh_x2, sh_y2, hand_x2, hand_y2)
        _NS_vokrahn._draw_gauntlet(surface, hand_x2, hand_y2)

        # Sword arm - extended forward
        sword_side = facing
        sh_x = cx + sword_side * 10
        sh_y = cy - 4
        elbow_x = sh_x + sword_side * 6
        elbow_y = cy - 2
        hand_x = elbow_x + sword_side * 8
        hand_y = cy - 3

        _NS_vokrahn._draw_knight_arm(surface, sh_x, sh_y, elbow_x, elbow_y)
        _NS_vokrahn._draw_knight_arm(surface, elbow_x, elbow_y, hand_x, hand_y)
        _NS_vokrahn._draw_gauntlet(surface, hand_x, hand_y)

        # Sword forward
        _NS_vokrahn._draw_flaming_sword(surface, hand_x, hand_y, facing, "forward", phase)


    def _draw_knight_cast_arms(surface, cx, cy, facing, phase):
        """Q cast - sword pointing forward, energy gathering."""
        # Back arm - shield
        other_side = -facing
        sh_x2 = cx + other_side * 10
        sh_y2 = cy - 4
        hand_x2 = sh_x2 + other_side * 3
        hand_y2 = cy + 3
        _NS_vokrahn._draw_knight_arm(surface, sh_x2, sh_y2, hand_x2, hand_y2)
        _NS_vokrahn._draw_gauntlet(surface, hand_x2, hand_y2)

        # Sword forward
        sword_side = facing
        sh_x = cx + sword_side * 10
        sh_y = cy - 4
        elbow_x = sh_x + sword_side * 5
        elbow_y = cy - 4
        hand_x = elbow_x + sword_side * 8
        hand_y = cy - 6

        _NS_vokrahn._draw_knight_arm(surface, sh_x, sh_y, elbow_x, elbow_y)
        _NS_vokrahn._draw_knight_arm(surface, elbow_x, elbow_y, hand_x, hand_y)
        _NS_vokrahn._draw_gauntlet(surface, hand_x, hand_y)

        _NS_vokrahn._draw_flaming_sword(surface, hand_x, hand_y, facing, "forward", phase)

        # Energy gathering at sword tip
        tip_x = hand_x + facing * 24
        tip_y = hand_y - 8
        pulse = math.sin(phase * 4) * 0.3 + 0.7
        r = int(6 * pulse)
        _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_dark"], 150), (tip_x, tip_y), r + 4)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_mid"], (tip_x, tip_y), r + 2)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_bright"], (tip_x, tip_y), r)
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["red_hot"], (tip_x, tip_y), max(1, r - 2))
        _NS_vokrahn._aacircle(surface, _NS_vokrahn.PALETTE["fire_glow"], (tip_x, tip_y), max(1, r - 4))


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


    def _draw_flaming_sword(surface, hx, hy, facing, pose, phase):
        """Long flaming sword."""
        if pose == "forward":
            # Handle horizontal
            end_x = hx + facing * 24
            end_y = hy
            _NS_vokrahn._draw_flaming_sword_line(surface, hx, hy, end_x, end_y, facing, phase)
        elif pose == "down":
            # Handle diagonal down/forward
            end_x = hx + facing * 12
            end_y = hy + 20
            _NS_vokrahn._draw_flaming_sword_line(surface, hx, hy, end_x, end_y, facing, phase)


    def _draw_flaming_sword_angled(surface, hx, hy, facing, angle, phase):
        """Sword at specific angle."""
        sword_len = 28
        dx = math.cos(angle) * facing
        dy = math.sin(angle)
        end_x = hx + int(dx * sword_len)
        end_y = hy + int(dy * sword_len)
        _NS_vokrahn._draw_flaming_sword_line(surface, hx, hy, end_x, end_y, facing, phase)


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


    def _draw_dash_trail(surface, x, y, facing, progress):
        """Trail of fire during dash."""
        for i in range(6):
            offset = -(i + 1) * 15 * facing
            alpha = max(0, 200 - i * 30)
            r = 5 - i // 2
            px = x + offset
            py = y + 5 + int(math.sin(progress * 5 + i) * 3)
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_dark"], alpha), (px, py), r + 2)
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_bright"], alpha), (px, py), r)
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["fire_hot"], alpha), (px, py), max(1, r - 2))


    # ===================================================================
    # SKILL W: REALM OF CHAOS
    # ===================================================================
    def _draw_realm_of_chaos_ground(surface, boss, x, y, timer, phase):
        """Ground rune warning."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        radius = int(60 + progress * 20)
        _NS_vokrahn._ellipse(surface, (*_NS_vokrahn.PALETTE["red_darkest"], int(200 * pulse)),
                 (x - radius, y + 45 - radius // 3, radius * 2, radius // 1.5), 3)
        _NS_vokrahn._ellipse(surface, (*_NS_vokrahn.PALETTE["red_dark"], int(180 * pulse)),
                 (x - radius + 5, y + 45 - radius // 3 + 2,
                  radius * 2 - 10, radius // 1.5 - 4), 2)

        # Rune symbols
        for i in range(6):
            angle = phase * 0.3 + i * math.pi / 3
            rx = x + int(math.cos(angle) * (radius - 6))
            ry = y + 45 + int(math.sin(angle) * (radius // 3 - 3))
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_hot"], int(200 * pulse)), (rx, ry), 2)


    def _draw_realm_of_chaos(surface, boss, x, y, timer, phase):
        """Ring of chaos spikes rising around boss."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.15:
            return

        # Erupt phase
        if progress < 0.5:
            erupt_t = (progress - 0.15) / 0.35
        else:
            erupt_t = 1.0 - (progress - 0.7) / 0.3 if progress > 0.7 else 1.0
        erupt_t = max(0.0, min(1.0, erupt_t))

        # Ring of spikes
        ring_r = 60
        num_spikes = 14
        for i in range(num_spikes):
            angle = i * math.pi * 2 / num_spikes + phase * 0.05
            sx = x + int(math.cos(angle) * ring_r)
            sy = y + 45 + int(math.sin(angle) * ring_r * 0.5)
            spike_h = int(25 * erupt_t) + (i % 3) * 3

            _NS_vokrahn._draw_chaos_spike(surface, sx, sy, sy - spike_h, 4, 240)

        # Inner ring - smaller spikes
        inner_r = 40
        for i in range(10):
            angle = (i + 0.5) * math.pi * 2 / 10 + phase * 0.1
            sx = x + int(math.cos(angle) * inner_r)
            sy = y + 45 + int(math.sin(angle) * inner_r * 0.5)
            spike_h = int(18 * erupt_t)
            _NS_vokrahn._draw_chaos_spike(surface, sx, sy, sy - spike_h, 3, 220)

        # Center big spike
        center_h = int(35 * erupt_t)
        _NS_vokrahn._draw_chaos_spike(surface, x, y + 45, y + 45 - center_h, 5, 250)

        # Sparks around
        for i in range(10):
            angle = phase * 2 + i * math.pi / 5
            r = ring_r + int(math.sin(phase * 3 + i) * 6)
            sx = x + int(math.cos(angle) * r)
            sy = y + 45 + int(math.sin(angle) * r * 0.5) - int(erupt_t * 12)
            _NS_vokrahn._draw_ember(surface, sx, sy, 2, int(230 * erupt_t))


    # ===================================================================
    # SKILL R: PHANTASM (illusions)
    # ===================================================================
    def _draw_phantasm_ground(surface, boss, x, y, timer, phase):
        """Ground summon circle for phantasm."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 3) * 0.3 + 0.7

        for i in range(3):
            r = int(60 + i * 15 + math.sin(phase + i) * 4)
            _NS_vokrahn._ellipse(surface, (*_NS_vokrahn.PALETTE["red_mid"], int(140 * pulse)),
                     (x - r, y + 45 - r // 3, r * 2, r // 1.5), 2)

        # Runic circle
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            r1 = 55
            r2 = 68
            x1 = x + int(math.cos(angle) * r1)
            y1 = y + 45 + int(math.sin(angle) * r1 * 0.5)
            x2 = x + int(math.cos(angle) * r2)
            y2 = y + 45 + int(math.sin(angle) * r2 * 0.5)
            _NS_vokrahn._aaline(surface, (*_NS_vokrahn.PALETTE["red_hot"], int(200 * pulse)),
                    (x1, y1), (x2, y2), 1)


    def _draw_phantasm_illusions(surface, boss, x, y, timer, phase):
        """Draw 2 illusion copies of boss behind/beside main body."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.25:
            return

        fade_t = min(1.0, (progress - 0.25) / 0.3)
        alpha = int(180 * fade_t)

        # Positions of illusions (left and right of main)
        positions = [
            (x - 55 * boss.direction, y),  # behind
            (x - 30 * boss.direction, y + 8),  # slightly behind
        ]

        for i, (ix, iy) in enumerate(positions):
            # Draw illusion on transparent surface
            illusion = pygame.Surface((200, 200), pygame.SRCALPHA)
            _NS_vokrahn._draw_vok_full(illusion, 100, 100, boss.direction, phase + i, "idle")
            # Tint red
            red_overlay = pygame.Surface((200, 200), pygame.SRCALPHA)
            red_overlay.fill((*_NS_vokrahn.PALETTE["red_dark"], 80))
            illusion.blit(red_overlay, (0, 0),
                          special_flags=pygame.BLEND_RGBA_MULT)
            illusion.set_alpha(alpha)
            surface.blit(illusion, (ix - 100, iy - 100))

            # Red glow behind illusion
            _NS_vokrahn._aacircle(surface, (*_NS_vokrahn.PALETTE["red_bright"], int(60 * fade_t)),
                      (ix, iy), 40)


    # ===================================================================
    # Backward compatible alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_vokrahn.draw_vokrahn(surface, boss, x, y)


# ====================================================================
# IGNIS_DRACHORN
# ====================================================================
class _NS_ignis_drachorn:
    """Namespace ignis_drachorn - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Dragon Knight inspired crimson / gold / fire
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Armor - dark steel with red tint
        "armor_darkest":  (18,  12,  14),
        "armor_dark":     (42,  28,  30),
        "armor_mid":      (75,  52,  55),
        "armor_light":    (120, 90,  90),
        "armor_high":     (170, 140, 138),
        "armor_shine":    (215, 195, 190),

        # Red cloth / cape
        "red_darkest":    (45,   8,  10),
        "red_dark":       (90,  18,  22),
        "red_mid":        (140, 30,  35),
        "red_light":      (185, 55,  55),
        "red_high":       (220, 90,  80),
        "red_shine":      (250, 145, 120),

        # Gold trim
        "gold_dark":      (95,  62,  15),
        "gold_mid":       (170, 125, 35),
        "gold_light":     (230, 190, 75),
        "gold_shine":     (255, 235, 150),

        # Fire - orange/red flame
        "fire_darkest":   (60,  12,   4),
        "fire_dark":      (135, 35,   8),
        "fire_mid":       (215, 80,  15),
        "fire_light":     (250, 145, 30),
        "fire_bright":    (255, 200, 65),
        "fire_hot":       (255, 235, 140),
        "fire_white":     (255, 250, 220),

        # Dragon scale - deep red/black
        "dragon_darkest": (25,  8,   10),
        "dragon_dark":    (60,  18,  20),
        "dragon_mid":     (105, 30,  32),
        "dragon_light":   (155, 55,  50),
        "dragon_high":    (200, 100, 80),

        # Sword blade - fiery steel
        "blade_dark":     (120, 60,  25),
        "blade_mid":      (200, 130, 55),
        "blade_light":    (245, 195, 100),
        "blade_hot":      (255, 235, 170),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (8,   4,   6),
        "white":          (255, 255, 255),

        # Eye glow
        "eye_dark":       (100, 20,   5),
        "eye_mid":        (220, 90,  15),
        "eye_bright":     (255, 180, 60),
        "eye_hot":        (255, 240, 180),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_ignis_drachorn._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_ignis_drachorn.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_ignis_drachorn._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
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
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_ignis_drachorn._clamp(color)
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
        color = _NS_ignis_drachorn._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_ignis_drachorn._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh), border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)


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
    # Fire particle helper
    # ---------------------------------------------------------------------------
    def _draw_flame_puff(surface, x, y, size, phase, alpha=255):
        """Draw a puff of flame with multiple layers."""
        flick = math.sin(phase * 3) * 0.15 + 1.0
        s = int(size * flick)
        if s < 1:
            return
        _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_darkest"], alpha // 3), (x, y), s + 3)
        _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_dark"], alpha // 2), (x, y), s + 1)
        _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_mid"], alpha), (x, y), s)
        _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_light"], alpha), (x, y - 1), max(1, s - 2))
        _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_bright"], min(255, alpha)),
                  (x, y - 2), max(1, s - 4))
        if s > 4:
            _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_hot"], min(255, alpha)),
                      (x, y - 3), max(1, s - 6))


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM - Fire orb from sword
    # ---------------------------------------------------------------------------
    class FireProjectile:
        """A fire orb that travels toward a target (used for melee-ish ranged)."""
        def __init__(self, sx, sy, tx, ty, speed=5.5):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.trail = []

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
            if len(self.trail) > 10:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(50 + i * 15)
                r = max(1, 5 - (len(self.trail) - i))
                _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_dark"], alpha), (tx, ty), r + 2)
                _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_mid"], alpha), (tx, ty), r)

            if self.alive:
                px, py = int(self.x), int(self.y)
                _NS_ignis_drachorn._draw_flame_puff(surface, px, py, 7, phase, 240)
                # Trailing sparks
                for i in range(3):
                    angle = phase * 5 + i * math.pi * 2 / 3
                    sx = px + int(math.cos(angle) * 8)
                    sy = py + int(math.sin(angle) * 8)
                    _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["fire_hot"], (sx, sy), 1)


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_ign_last_x"):
            boss._ign_last_x = boss.x
            boss._ign_last_y = boss.y
            return False
        dx = abs(boss.x - boss._ign_last_x)
        dy = abs(boss.y - boss._ign_last_y)
        boss._ign_last_x = boss.x
        boss._ign_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_ign_prev_timer", 0))
        active = bool(getattr(boss, "_ign_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._ign_attack_active = True
            boss._ign_attack_frame = 0
            active = True
        elif active:
            boss._ign_attack_frame = int(getattr(boss, "_ign_attack_frame", 0)) + 1
            if boss._ign_attack_frame > cooldown:
                boss._ign_attack_active = False
                boss._ign_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._ign_attack_active = False
            boss._ign_attack_frame = 0
            active = False

        boss._ign_prev_timer = timer
        boss._ign_attack_progress = (
            min(1.0, getattr(boss, "_ign_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_ign_projectiles"):
            boss._ign_projectiles = []
        for proj in boss._ign_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._ign_projectiles = [p for p in boss._ign_projectiles if p.alive or p.age < 8]


    def _spawn_fire_projectile(boss, x, y):
        if not hasattr(boss, "_ign_projectiles"):
            boss._ign_projectiles = []
        tx, ty = _NS_ignis_drachorn._target_position(boss, x, y)
        sx = x + 28 * getattr(boss, "direction", 1)
        sy = y - 15
        boss._ign_projectiles.append(_NS_ignis_drachorn.FireProjectile(sx, sy, tx, ty, speed=5.5))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_ignis(surface, boss, x, y):
        """Entry point for Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_ignis_drachorn._detect_moving(boss)
        _NS_ignis_drachorn._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_ign_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # Determine attack type - if boss has attack_range > 100, treat as ranged
        attack_range = getattr(boss, "attack_range", 150)
        is_ranged_attack = attack_range > 120

        # ---------- Background layers ----------
        _NS_ignis_drachorn._draw_fire_aura(surface, x, y, pulse)
        _NS_ignis_drachorn._draw_ground_embers(surface, x, y + 38, pulse, active_skill)

        # ---------- Skill ground effects ----------
        if active_skill == "q":
            _NS_ignis_drachorn._draw_dragon_breath_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_ignis_drachorn._draw_dragon_tail_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_ignis_drachorn._draw_dragon_blood_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_ignis_drachorn._draw_elder_form_ground(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if active_skill == "r" and skill_timer > 10:
            _NS_ignis_drachorn._draw_elder_dragon_form(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            if is_ranged_attack:
                _NS_ignis_drachorn._draw_ignis_ranged_attack(surface, boss, x, y)
            else:
                _NS_ignis_drachorn._draw_ignis_melee_attack(surface, boss, x, y)
        elif moving:
            _NS_ignis_drachorn._draw_ignis_walk(surface, boss, x, y)
        else:
            _NS_ignis_drachorn._draw_ignis_idle(surface, boss, x, y)

        # ---------- Projectiles ----------
        _NS_ignis_drachorn._manage_projectiles(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "q":
            _NS_ignis_drachorn._draw_dragon_breath(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_ignis_drachorn._draw_dragon_tail(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_ignis_drachorn._draw_dragon_blood_foreground(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_ignis_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_ignis_drachorn._draw_shadow(surface, x, y + 48)
        _NS_ignis_drachorn._draw_floating_flames(surface, x, y + 35, boss.pulse)
        _NS_ignis_drachorn._draw_ignis_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_ignis_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(abs(math.sin(phase * 1.3)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_ignis_drachorn._draw_shadow(surface, x + sway, y + 48)
        _NS_ignis_drachorn._draw_floating_flames(surface, x + sway, y + 35, phase, trail=True,
                              facing=boss.direction)
        _NS_ignis_drachorn._draw_ignis_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_ignis_melee_attack(surface, boss, x, y):
        progress = getattr(boss, "_ign_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        lunge = int(math.sin(progress * math.pi) * 5) * boss.direction
        _NS_ignis_drachorn._draw_shadow(surface, x + lunge, y + 48)
        _NS_ignis_drachorn._draw_floating_flames(surface, x + lunge, y + 35, boss.pulse, intense=True)
        _NS_ignis_drachorn._draw_ignis_body(surface, x + lunge, y, boss.direction, boss.pulse,
                         "melee", progress)
        _NS_ignis_drachorn._draw_sword_swing_trail(surface, x + lunge, y, boss.direction, progress)


    def _draw_ignis_ranged_attack(surface, boss, x, y):
        progress = getattr(boss, "_ign_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        if 0.28 < progress < 0.35 and not getattr(boss, "_ign_proj_spawned", False):
            _NS_ignis_drachorn._spawn_fire_projectile(boss, x, y)
            boss._ign_proj_spawned = True
        if progress < 0.1 or progress > 0.9:
            boss._ign_proj_spawned = False

        recoil = int(math.sin(progress * math.pi) * 3) * -boss.direction
        _NS_ignis_drachorn._draw_shadow(surface, x + recoil, y + 48)
        _NS_ignis_drachorn._draw_floating_flames(surface, x + recoil, y + 35, boss.pulse, intense=True)
        _NS_ignis_drachorn._draw_ignis_body(surface, x + recoil, y, boss.direction, boss.pulse,
                         "ranged", progress)
        _NS_ignis_drachorn._draw_sword_charge_flash(surface, x + recoil, y, boss.direction, progress)


    # ===================================================================
    # BODY RENDERING – HD detailed Dragon Knight
    # ===================================================================
    def _draw_ignis_body(surface, cx, cy, facing, phase, action,
                         attack_progress=0):
        """Main body composition."""
        # Cape behind
        _NS_ignis_drachorn._draw_cape(surface, cx, cy, facing, phase, action)

        # Lower body (floating robes with dragon scales)
        _NS_ignis_drachorn._draw_lower_body(surface, cx, cy + 5, phase)

        # Torso plate armor
        _NS_ignis_drachorn._draw_torso(surface, cx, cy - 8, phase)

        # Shield on off-hand
        if action != "melee" or attack_progress < 0.3:
            _NS_ignis_drachorn._draw_shield(surface, cx, cy - 5, -facing, phase)

        # Pauldrons
        _NS_ignis_drachorn._draw_pauldrons(surface, cx, cy - 16, phase)

        # Sword arm and shield arm
        if action == "melee":
            _NS_ignis_drachorn._draw_melee_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        elif action == "ranged":
            _NS_ignis_drachorn._draw_ranged_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        else:
            _NS_ignis_drachorn._draw_idle_arms(surface, cx, cy - 8, facing, phase)

        # Shield on top for depth (front layer when melee attacking)
        if action == "melee" and attack_progress >= 0.3:
            _NS_ignis_drachorn._draw_shield(surface, cx, cy - 5, -facing, phase)

        # Head with dragon helm
        _NS_ignis_drachorn._draw_head(surface, cx, cy - 30, facing, phase)

        # Fire particles around body
        _NS_ignis_drachorn._draw_body_fire_particles(surface, cx, cy, phase)


    def _draw_cape(surface, cx, cy, facing, phase, action):
        """Red cape flowing behind character."""
        wave = math.sin(phase * 0.8) * 3
        wave2 = math.sin(phase * 1.2 + 0.5) * 2

        cape_outer = [
            (cx - 14, cy - 14),
            (cx - 20, cy + 5),
            (cx - 26 - int(wave), cy + 30),
            (cx - 20 - int(wave2), cy + 44),
            (cx - 5, cy + 47 + int(abs(wave))),
            (cx + 5, cy + 47 + int(abs(wave))),
            (cx + 20 + int(wave2), cy + 44),
            (cx + 26 + int(wave), cy + 30),
            (cx + 20, cy + 5),
            (cx + 14, cy - 14),
        ]
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["red_darkest"], cape_outer)

        cape_mid = [
            (cx - 12, cy - 12),
            (cx - 17, cy + 5),
            (cx - 22 - int(wave * 0.7), cy + 28),
            (cx - 15 - int(wave2 * 0.7), cy + 40),
            (cx - 3, cy + 42),
            (cx + 3, cy + 42),
            (cx + 15 + int(wave2 * 0.7), cy + 40),
            (cx + 22 + int(wave * 0.7), cy + 28),
            (cx + 17, cy + 5),
            (cx + 12, cy - 12),
        ]
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["red_dark"], cape_mid)

        cape_inner = [
            (cx - 9, cy - 8),
            (cx - 13, cy + 5),
            (cx - 16 - int(wave * 0.4), cy + 22),
            (cx - 8, cy + 34),
            (cx, cy + 36),
            (cx + 8, cy + 34),
            (cx + 16 + int(wave * 0.4), cy + 22),
            (cx + 13, cy + 5),
            (cx + 9, cy - 8),
        ]
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["red_mid"], cape_inner)

        # Highlights on cape folds
        _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["red_light"],
                (cx - 8, cy - 5), (cx - 12, cy + 20), 1)
        _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["red_light"],
                (cx + 8, cy - 5), (cx + 12, cy + 20), 1)

        # Gold trim at top of cape
        _NS_ignis_drachorn._rect(surface, _NS_ignis_drachorn.PALETTE["gold_dark"], (cx - 14, cy - 15, 28, 3))
        _NS_ignis_drachorn._rect(surface, _NS_ignis_drachorn.PALETTE["gold_mid"], (cx - 13, cy - 14, 26, 2))


    def _draw_lower_body(surface, cx, cy, phase):
        """Armored lower body/skirt with dragon scale texture."""
        sway = int(math.sin(phase * 0.7) * 2)

        # Outer skirt
        skirt = [
            (cx - 18, cy),
            (cx + 18, cy),
            (cx + 22 + sway, cy + 14),
            (cx + 16, cy + 24),
            (cx + 8, cy + 30),
            (cx + 3, cy + 32),
            (cx - 3, cy + 32),
            (cx - 8, cy + 30),
            (cx - 16, cy + 24),
            (cx - 22 - sway, cy + 14),
        ]
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["shadow_deep"], [(p[0] + 2, p[1] + 2) for p in skirt])
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["armor_darkest"], skirt)

        skirt_mid = [
            (cx - 15, cy + 2),
            (cx + 15, cy + 2),
            (cx + 18 + sway, cy + 14),
            (cx + 12, cy + 22),
            (cx + 5, cy + 27),
            (cx - 5, cy + 27),
            (cx - 12, cy + 22),
            (cx - 18 - sway, cy + 14),
        ]
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["armor_dark"], skirt_mid)

        skirt_inner = [
            (cx - 11, cy + 4),
            (cx + 11, cy + 4),
            (cx + 14 + sway, cy + 14),
            (cx + 8, cy + 20),
            (cx - 8, cy + 20),
            (cx - 14 - sway, cy + 14),
        ]
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["armor_mid"], skirt_inner)

        # Dragon scale pattern on skirt
        for row in range(3):
            for col in range(-2, 3):
                sx = cx + col * 6 + (row % 2) * 3
                sy = cy + 6 + row * 5
                _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["dragon_dark"], (sx, sy), 3)
                _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["dragon_mid"], (sx, sy - 1), 2)
                _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["dragon_light"], (sx, sy - 1), 1)

        # Gold belt
        _NS_ignis_drachorn._rect(surface, _NS_ignis_drachorn.PALETTE["gold_dark"], (cx - 19, cy - 1, 38, 5))
        _NS_ignis_drachorn._rect(surface, _NS_ignis_drachorn.PALETTE["gold_mid"], (cx - 17, cy, 34, 3))
        _NS_ignis_drachorn._rect(surface, _NS_ignis_drachorn.PALETTE["gold_light"], (cx - 14, cy + 1, 28, 1))

        # Dragon head belt buckle
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["dragon_darkest"], [
            (cx - 5, cy - 1), (cx + 5, cy - 1),
            (cx + 4, cy + 5), (cx, cy + 7), (cx - 4, cy + 5),
        ])
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["dragon_mid"], [
            (cx - 4, cy), (cx + 4, cy),
            (cx + 3, cy + 4), (cx, cy + 6), (cx - 3, cy + 4),
        ])
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["eye_bright"], (cx - 2, cy + 2), 1)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["eye_bright"], (cx + 2, cy + 2), 1)


    def _draw_torso(surface, cx, cy, phase):
        """Chest armor with dragon emblem."""
        # Shadow
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["shadow_deep"], [
            (cx - 14 + 2, cy - 10 + 2), (cx + 14 + 2, cy - 10 + 2),
            (cx + 12 + 2, cy + 14 + 2), (cx + 5 + 2, cy + 19 + 2),
            (cx - 5 + 2, cy + 19 + 2), (cx - 12 + 2, cy + 14 + 2),
        ])

        chest = [
            (cx - 14, cy - 10), (cx + 14, cy - 10),
            (cx + 12, cy + 14), (cx + 5, cy + 19),
            (cx - 5, cy + 19), (cx - 12, cy + 14),
        ]
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["armor_darkest"], chest)
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["armor_dark"], [
            (cx - 12, cy - 8), (cx + 12, cy - 8),
            (cx + 10, cy + 12), (cx + 4, cy + 16),
            (cx - 4, cy + 16), (cx - 10, cy + 12),
        ])
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["armor_mid"], [
            (cx - 9, cy - 5), (cx + 9, cy - 5),
            (cx + 7, cy + 9), (cx + 3, cy + 13),
            (cx - 3, cy + 13), (cx - 7, cy + 9),
        ])
        # Highlight
        _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["armor_light"],
                (cx - 7, cy - 4), (cx - 5, cy + 8), 1)

        # Gold trim around chest
        for i in range(len(chest)):
            p1 = chest[i]
            p2 = chest[(i + 1) % len(chest)]
            _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["gold_dark"], p1, p2, 2)
        for i in range(len(chest)):
            p1 = chest[i]
            p2 = chest[(i + 1) % len(chest)]
            _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["gold_mid"], p1, p2, 1)

        # Central dragon emblem (red diamond shape)
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["red_darkest"], [
            (cx, cy - 4), (cx + 6, cy + 4),
            (cx, cy + 12), (cx - 6, cy + 4),
        ])
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["red_dark"], [
            (cx, cy - 3), (cx + 5, cy + 4),
            (cx, cy + 11), (cx - 5, cy + 4),
        ])
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["red_mid"], [
            (cx, cy - 1), (cx + 4, cy + 4),
            (cx, cy + 9), (cx - 4, cy + 4),
        ])

        # Dragon symbol on emblem
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["fire_bright"], (cx, cy + 4),
                  int(2 * pulse) + 1)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["fire_hot"], (cx, cy + 4), 1)

        # Wing marks on emblem
        _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["gold_light"], (cx - 3, cy + 3), (cx - 1, cy + 5), 1)
        _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["gold_light"], (cx + 3, cy + 3), (cx + 1, cy + 5), 1)


    def _draw_pauldrons(surface, cx, cy, phase):
        """Shoulder pauldrons with dragon spikes."""
        for side in (-1, 1):
            sx = cx + side * 16
            # Shadow
            _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["shadow_deep"], (sx + 2, cy + 2), 11)
            # Main pauldron
            _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["armor_darkest"], (sx, cy), 10)
            _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["armor_dark"], (sx - side, cy - 1), 8)
            _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["armor_mid"], (sx - side * 2, cy - 2), 6)
            _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["armor_light"], (sx - side * 3, cy - 4), 3)

            # Gold trim ring
            _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["gold_dark"], (sx, cy), 10, 2)
            _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["gold_mid"], (sx, cy), 9, 1)

            # Dragon spike on top
            _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["dragon_darkest"], [
                (sx - 3, cy - 8),
                (sx + 3, cy - 8),
                (sx + side * 3, cy - 18),
            ])
            _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["dragon_mid"], [
                (sx - 2, cy - 8),
                (sx + 2, cy - 8),
                (sx + side * 2, cy - 16),
            ])
            # Ember on spike tip
            _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["fire_light"],
                      (sx + side * 3, cy - 18), 2)
            _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["fire_hot"],
                      (sx + side * 3, cy - 18), 1)

            # Small side spike
            _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["dragon_dark"], [
                (sx + side * 8, cy - 3),
                (sx + side * 12, cy - 5),
                (sx + side * 9, cy + 2),
            ])


    def _draw_shield(surface, cx, cy, side, phase):
        """Dragon knight shield."""
        shx = cx + side * 18
        shy = cy + 4

        # Shield shadow
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["shadow_deep"], [
            (shx - 8 + 2, shy - 10 + 2),
            (shx + 8 + 2, shy - 10 + 2),
            (shx + 10 + 2, shy + 5 + 2),
            (shx + 2, shy + 14 + 2),
            (shx - 10 + 2, shy + 5 + 2),
        ])

        # Shield body
        shield_pts = [
            (shx - 8, shy - 10),
            (shx + 8, shy - 10),
            (shx + 10, shy + 5),
            (shx, shy + 14),
            (shx - 10, shy + 5),
        ]
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["red_darkest"], shield_pts)
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["red_dark"], [
            (shx - 7, shy - 9),
            (shx + 7, shy - 9),
            (shx + 9, shy + 4),
            (shx, shy + 12),
            (shx - 9, shy + 4),
        ])
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["red_mid"], [
            (shx - 5, shy - 7),
            (shx + 5, shy - 7),
            (shx + 7, shy + 3),
            (shx, shy + 10),
            (shx - 7, shy + 3),
        ])

        # Gold trim
        for i in range(len(shield_pts)):
            p1 = shield_pts[i]
            p2 = shield_pts[(i + 1) % len(shield_pts)]
            _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["gold_dark"], p1, p2, 2)
        for i in range(len(shield_pts)):
            p1 = shield_pts[i]
            p2 = shield_pts[(i + 1) % len(shield_pts)]
            _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["gold_mid"], p1, p2, 1)

        # Dragon emblem on shield
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["gold_dark"], (shx, shy - 1), 5)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["gold_mid"], (shx, shy - 1), 4)

        # Simplified dragon head
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["dragon_darkest"], [
            (shx - 3, shy - 3),
            (shx + 3, shy - 3),
            (shx + 2, shy + 2),
            (shx, shy + 3),
            (shx - 2, shy + 2),
        ])
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["dragon_mid"], [
            (shx - 2, shy - 2),
            (shx + 2, shy - 2),
            (shx + 1, shy + 1),
            (shx, shy + 2),
            (shx - 1, shy + 1),
        ])
        # Dragon eyes
        pulse = math.sin(phase * 2) * 0.4 + 0.6
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["eye_bright"],
                  (shx - 1, shy - 1), max(1, int(pulse)))
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["eye_bright"],
                  (shx + 1, shy - 1), max(1, int(pulse)))


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Both arms in resting position with sword and shield ready."""
        sway = math.sin(phase * 0.7) * 2

        # Sword arm (facing side)
        ss_x = cx + facing * 14
        ss_y = cy + 2
        se_x = ss_x + facing * 6
        se_y = cy + 12 + int(sway)
        sh_x = se_x + facing * 3
        sh_y = se_y + 10

        _NS_ignis_drachorn._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_ignis_drachorn._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        # Sword pointing down/forward
        _NS_ignis_drachorn._draw_flame_sword(surface, sh_x, sh_y, facing, phase, angle=-0.3)

        # Shield arm (opposite side) - hand supports shield
        bs_x = cx + (-facing) * 14
        bs_y = cy + 2
        be_x = bs_x + (-facing) * 4
        be_y = cy + 10
        bh_x = be_x + (-facing) * 3
        bh_y = be_y + 6
        _NS_ignis_drachorn._draw_arm_segment(surface, bs_x, bs_y, be_x, be_y)
        _NS_ignis_drachorn._draw_arm_segment(surface, be_x, be_y, bh_x, bh_y)


    def _draw_melee_arms(surface, cx, cy, facing, phase, progress):
        """Sword swing animation."""
        # Shield arm stays relatively stable
        bs_x = cx + (-facing) * 14
        bs_y = cy + 2
        be_x = bs_x + (-facing) * 4
        be_y = cy + 10
        bh_x = be_x + (-facing) * 3
        bh_y = be_y + 6
        _NS_ignis_drachorn._draw_arm_segment(surface, bs_x, bs_y, be_x, be_y)
        _NS_ignis_drachorn._draw_arm_segment(surface, be_x, be_y, bh_x, bh_y)

        # Sword arm - swing animation
        ss_x = cx + facing * 14
        ss_y = cy + 2

        # Wind up (0-0.3): raise sword back
        # Swing (0.3-0.6): swing forward
        # Recovery (0.6-1.0): return
        if progress < 0.3:
            t = progress / 0.3
            arm_angle = -1.2 + (-0.8) * t  # from -1.2 to -2.0
        elif progress < 0.6:
            t = (progress - 0.3) / 0.3
            arm_angle = -2.0 + 3.0 * t  # swing forward from -2.0 to 1.0
        else:
            t = (progress - 0.6) / 0.4
            arm_angle = 1.0 - 1.3 * t  # return to -0.3

        se_x = ss_x + int(math.cos(arm_angle) * 12) * facing
        se_y = ss_y + int(math.sin(arm_angle) * 12)
        sh_x = se_x + int(math.cos(arm_angle) * 10) * facing
        sh_y = se_y + int(math.sin(arm_angle) * 10)

        _NS_ignis_drachorn._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_ignis_drachorn._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        # Sword with rotation
        sword_angle = arm_angle + (0.3 if facing > 0 else -0.3)
        _NS_ignis_drachorn._draw_flame_sword(surface, sh_x, sh_y, facing, phase, angle=sword_angle,
                         intense=(0.3 < progress < 0.7))


    def _draw_ranged_arms(surface, cx, cy, facing, phase, progress):
        """Ranged attack - raise sword and shoot fire projectile."""
        # Shield arm stable
        bs_x = cx + (-facing) * 14
        bs_y = cy + 2
        be_x = bs_x + (-facing) * 4
        be_y = cy + 10
        bh_x = be_x + (-facing) * 3
        bh_y = be_y + 6
        _NS_ignis_drachorn._draw_arm_segment(surface, bs_x, bs_y, be_x, be_y)
        _NS_ignis_drachorn._draw_arm_segment(surface, be_x, be_y, bh_x, bh_y)

        # Sword arm - point forward
        ss_x = cx + facing * 14
        ss_y = cy + 2

        if progress < 0.3:
            t = progress / 0.3
            arm_angle = -0.3 - 0.8 * t
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            arm_angle = -1.1 + 1.4 * t
        else:
            t = (progress - 0.5) / 0.5
            arm_angle = 0.3 - 0.6 * t

        se_x = ss_x + int(math.cos(arm_angle) * 12) * facing
        se_y = ss_y + int(math.sin(arm_angle) * 12)
        sh_x = se_x + int(math.cos(arm_angle) * 10) * facing
        sh_y = se_y + int(math.sin(arm_angle) * 10)

        _NS_ignis_drachorn._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_ignis_drachorn._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        sword_angle = arm_angle
        _NS_ignis_drachorn._draw_flame_sword(surface, sh_x, sh_y, facing, phase, angle=sword_angle,
                         intense=(0.2 < progress < 0.5))


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Armored arm segment."""
        _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["shadow_deep"], (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 8)
        _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["armor_darkest"], (x1, y1), (x2, y2), 7)
        _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["armor_dark"], (x1, y1), (x2, y2), 5)
        _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["armor_mid"], (x1, y1), (x2, y2), 3)
        _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["armor_light"], (x1, y1 - 1), (x2, y2 - 1), 1)
        # Gold joint
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["gold_dark"], (mx, my), 4)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["gold_mid"], (mx, my), 3)


    def _draw_flame_sword(surface, hx, hy, facing, phase, angle=0, intense=False):
        """Fiery sword extending from hand."""
        # Sword pointing in direction determined by angle
        length = 32
        tip_x = hx + int(math.cos(angle) * length) * facing
        tip_y = hy + int(math.sin(angle) * length)

        # Perpendicular for blade width
        perp_angle = angle + math.pi / 2
        px = math.cos(perp_angle) * facing
        py = math.sin(perp_angle)

        # Blade shadow
        blade_pts = [
            (hx + int(px * 3), hy + int(py * 3)),
            (hx - int(px * 3), hy - int(py * 3)),
            (tip_x, tip_y),
        ]
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in blade_pts])

        # Blade layers (fiery)
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["fire_darkest"], blade_pts)
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["fire_dark"], [
            (hx + int(px * 2.5), hy + int(py * 2.5)),
            (hx - int(px * 2.5), hy - int(py * 2.5)),
            (tip_x, tip_y),
        ])
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["fire_mid"], [
            (hx + int(px * 2), hy + int(py * 2)),
            (hx - int(px * 2), hy - int(py * 2)),
            (tip_x, tip_y),
        ])
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["fire_light"], [
            (hx + int(px * 1), hy + int(py * 1)),
            (hx - int(px * 1), hy - int(py * 1)),
            (tip_x, tip_y),
        ])

        # Bright core line
        _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["fire_hot"], (hx, hy), (tip_x, tip_y), 2)
        _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["fire_white"], (hx, hy), (tip_x, tip_y), 1)

        # Flames on the blade
        flame_count = 6
        for i in range(flame_count):
            t = i / flame_count
            bx = int(hx + (tip_x - hx) * t)
            by = int(hy + (tip_y - hy) * t)
            flick = math.sin(phase * 4 + i) * 2
            size = 3 + int(flick) if intense else 2 + int(flick * 0.5)
            _NS_ignis_drachorn._draw_flame_puff(surface, bx + int(py * flick), by - int(px * flick),
                             size, phase, 200)

        # Sword tip flame
        tip_size = 6 if intense else 4
        _NS_ignis_drachorn._draw_flame_puff(surface, tip_x, tip_y, tip_size, phase, 240)

        # Guard (crossguard)
        guard_perp_x = int(px * 8)
        guard_perp_y = int(py * 8)
        _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["gold_dark"],
                (hx + guard_perp_x, hy + guard_perp_y),
                (hx - guard_perp_x, hy - guard_perp_y), 4)
        _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["gold_mid"],
                (hx + guard_perp_x, hy + guard_perp_y),
                (hx - guard_perp_x, hy - guard_perp_y), 3)
        _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["gold_light"],
                (hx + int(guard_perp_x * 0.7), hy + int(guard_perp_y * 0.7)),
                (hx - int(guard_perp_x * 0.7), hy - int(guard_perp_y * 0.7)), 1)

        # Pommel gem
        pommel_x = hx - int(math.cos(angle) * 6) * facing
        pommel_y = hy - int(math.sin(angle) * 6)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["gold_dark"], (pommel_x, pommel_y), 3)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["red_dark"], (pommel_x, pommel_y), 2)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["red_high"], (pommel_x, pommel_y), 1)


    def _draw_head(surface, cx, cy, facing, phase):
        """Dragon knight helm."""
        # Shadow
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["shadow_deep"], (cx + 2, cy + 2), 13)

        # Helm base
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["armor_darkest"], (cx, cy), 12)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["armor_dark"], (cx - 1, cy - 1), 10)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["armor_mid"], (cx - 2, cy - 2), 7)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["armor_light"], (cx - 3, cy - 4), 4)

        # Gold helm trim
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["gold_dark"], (cx, cy), 12, 2)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["gold_mid"], (cx, cy), 11, 1)

        # Visor - T-shape opening
        # Vertical slit
        _NS_ignis_drachorn._rect(surface, _NS_ignis_drachorn.PALETTE["shadow_deep"], (cx - 1, cy - 6, 3, 12))
        # Horizontal slit
        _NS_ignis_drachorn._rect(surface, _NS_ignis_drachorn.PALETTE["shadow_deep"], (cx - 7, cy - 2, 14, 4))

        # Eye glow inside visor
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        eye_size = max(1, int(2 * pulse))
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["eye_dark"], (cx - 4, cy), eye_size + 1)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["eye_mid"], (cx - 4, cy), eye_size)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["eye_bright"], (cx - 4, cy), max(1, eye_size - 1))
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["eye_dark"], (cx + 4, cy), eye_size + 1)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["eye_mid"], (cx + 4, cy), eye_size)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["eye_bright"], (cx + 4, cy), max(1, eye_size - 1))

        # Gold crown/circlet band
        _NS_ignis_drachorn._rect(surface, _NS_ignis_drachorn.PALETTE["gold_dark"], (cx - 11, cy - 9, 22, 3))
        _NS_ignis_drachorn._rect(surface, _NS_ignis_drachorn.PALETTE["gold_mid"], (cx - 10, cy - 8, 20, 2))

        # Dragon horns on helm (large curved horns)
        for side in (-1, 1):
            # Base
            _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["dragon_darkest"], [
                (cx + side * 6, cy - 8),
                (cx + side * 10, cy - 8),
                (cx + side * 14, cy - 18),
                (cx + side * 16, cy - 22),
                (cx + side * 13, cy - 20),
                (cx + side * 9, cy - 12),
            ])
            _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["dragon_mid"], [
                (cx + side * 7, cy - 8),
                (cx + side * 9, cy - 8),
                (cx + side * 13, cy - 17),
                (cx + side * 14, cy - 20),
                (cx + side * 12, cy - 18),
                (cx + side * 8, cy - 11),
            ])
            # Horn tip highlight
            _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["dragon_high"],
                      (cx + side * 15, cy - 21), 1)

            # Fire ember at horn tips
            _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_mid"], 180),
                      (cx + side * 16, cy - 22), 3)
            _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["fire_bright"],
                      (cx + side * 16, cy - 22), 1)

        # Center crown spike
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["dragon_darkest"], [
            (cx - 2, cy - 10),
            (cx + 2, cy - 10),
            (cx, cy - 16),
        ])
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["gold_mid"], [
            (cx - 1, cy - 10),
            (cx + 1, cy - 10),
            (cx, cy - 15),
        ])

        # Chin/mouth guard
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["armor_darkest"], [
            (cx - 6, cy + 6),
            (cx + 6, cy + 6),
            (cx + 4, cy + 12),
            (cx, cy + 14),
            (cx - 4, cy + 12),
        ])
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["armor_dark"], [
            (cx - 4, cy + 7),
            (cx + 4, cy + 7),
            (cx + 2, cy + 11),
            (cx, cy + 12),
            (cx - 2, cy + 11),
        ])

        # Small fangs
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["armor_shine"], [
            (cx - 2, cy + 8), (cx - 1, cy + 8), (cx - 1, cy + 10)
        ])
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["armor_shine"], [
            (cx + 1, cy + 8), (cx + 2, cy + 8), (cx + 1, cy + 10)
        ])


    def _draw_body_fire_particles(surface, cx, cy, phase):
        """Fire embers around body."""
        for i in range(10):
            angle = phase * 0.5 + i * math.pi / 5
            radius = 28 + int(math.sin(phase * 0.9 + i) * 6)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.4)
            alpha = int(120 + math.sin(phase + i * 0.7) * 60)
            _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_dark"], alpha), (px, py), 2)
            _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_bright"], alpha // 2), (px, py), 1)

        # Rising embers
        for i in range(6):
            t = (phase * 0.4 + i * 0.17) % 1.0
            px = cx + int(math.sin(phase + i) * 20) + (i - 3) * 3
            py = cy + 20 - int(t * 60)
            alpha = int(200 * (1 - t))
            if alpha > 0:
                _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_light"], alpha), (px, py), 1)
                _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_hot"], alpha), (px, py - 1), 1)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_flames(surface, cx, cy, phase, trail=False,
                              facing=1, intense=False):
        """Fire mist below floating Ignis."""
        strength = 1.5 if intense else 1.0

        # Fire base mist
        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(30, 3, -4):
            alpha = int((30 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_ignis_drachorn.PALETTE["fire_dark"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising flame wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.6 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 22)
            alpha = max(0, min(255, int(220 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            size = int(5 * (1 - t * 0.5))
            _NS_ignis_drachorn._draw_flame_puff(surface, sx, sy, size, phase, alpha)

        # Ember orbits
        for i in range(5):
            angle = phase * 1.1 + i * math.pi * 2 / 5
            r = 22 + int(math.sin(phase + i * 1.3) * 4)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 6)
            _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["fire_mid"], (sx, sy), 2)
            _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["fire_bright"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 140 - i * 25)
                _NS_ignis_drachorn._draw_flame_puff(surface, sx, sy, max(2, 5 - i), phase, alpha)


    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_ignis_drachorn.PALETTE["fire_darkest"], 60), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_fire_aura(surface, x, y, phase):
        """Warm background aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(72, 5, -4):
            alpha = int((72 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_ignis_drachorn._aacircle(aura, (*_NS_ignis_drachorn.PALETTE["fire_darkest"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))


    def _draw_ground_embers(surface, x, y, phase, skill):
        """Fire runes on ground."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_ignis_drachorn.PALETTE["fire_dark"], 140),
                            (5, 10, 120, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_ignis_drachorn.PALETTE["fire_mid"], 170),
                            (20, 14, 90, 16), 2)

        for i in range(10):
            angle = phase * 0.2 + i * math.pi / 5
            x1 = 65 + int(math.cos(angle) * 30)
            y1 = 22 + int(math.sin(angle) * 6)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_ignis_drachorn.PALETTE["fire_light"], 160),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_ignis_drachorn.PALETTE["fire_bright"], int(80 * pulse)),
                                (15, 8, 100, 28), 1)

        surface.blit(ring, (x - 65, y - 22))


    def _draw_sword_swing_trail(surface, x, y, facing, progress):
        """Arc trail during sword swing."""
        if progress < 0.3 or progress > 0.7:
            return

        t = (progress - 0.3) / 0.4
        # Draw arc trail
        center_x = x + facing * 5
        center_y = y - 8
        radius = 40

        start_angle = -math.pi / 2 - 0.5
        end_angle = math.pi / 4

        current_angle = start_angle + (end_angle - start_angle) * t

        # Multiple arc segments for trail
        trail_length = 1.5
        segments = 12
        for i in range(segments):
            seg_t = i / segments
            angle = current_angle - trail_length * seg_t
            if angle < start_angle:
                continue

            ax = center_x + int(math.cos(angle) * radius) * facing
            ay = center_y + int(math.sin(angle) * radius)

            alpha_seg = int(200 * (1 - seg_t))
            size = int(6 * (1 - seg_t * 0.5))
            _NS_ignis_drachorn._draw_flame_puff(surface, ax, ay, size, progress * 10, alpha_seg)

        # Slash mark at current position
        slash_x = center_x + int(math.cos(current_angle) * radius) * facing
        slash_y = center_y + int(math.sin(current_angle) * radius)
        _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_hot"], 220), (slash_x, slash_y), 8)
        _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_white"], 240), (slash_x, slash_y), 4)


    def _draw_sword_charge_flash(surface, x, y, facing, progress):
        """Flash effect during ranged attack."""
        if progress < 0.2 or progress > 0.65:
            return
        t = (progress - 0.2) / 0.45
        intensity = math.sin(t * math.pi)

        flash_x = x + 28 * facing
        flash_y = y - 15

        alpha = int(180 * intensity)
        radius = int(8 + intensity * 15)

        _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_mid"], alpha // 2),
                  (flash_x, flash_y), radius + 8)
        _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_light"], alpha),
                  (flash_x, flash_y), radius)
        _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_bright"], alpha),
                  (flash_x, flash_y), radius // 2)
        _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_hot"], min(255, alpha)),
                  (flash_x, flash_y), max(1, radius // 4))

        # Fire sparks
        for i in range(5):
            angle = progress * 6 + i * math.pi * 2 / 5
            ex = flash_x + int(math.cos(angle) * radius * 1.3)
            ey = flash_y + int(math.sin(angle) * radius * 1.3)
            _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_hot"], alpha), (ex, ey), 2)


    # ===================================================================
    # SKILL Q: DRAGON BREATH - Cone of fire
    # ===================================================================
    def _draw_dragon_breath_ground(surface, boss, x, y, timer, phase):
        """Scorched ground where breath will hit."""
        progress = max(0.0, min(1.0, 1 - timer / 80))
        facing = boss.direction

        # Scorch marks growing
        for i in range(5):
            t = i / 5
            sx = x + facing * (30 + i * 25)
            sy = y + 40
            alpha = int(120 * progress * (1 - t * 0.5))
            _NS_ignis_drachorn._ellipse(surface, (*_NS_ignis_drachorn.PALETTE["fire_darkest"], alpha),
                     (sx - 15, sy - 5, 30, 10))


    def _draw_dragon_breath(surface, boss, x, y, timer, phase):
        """Cone of fire from mouth/sword."""
        progress = max(0.0, min(1.0, 1 - timer / 80))
        facing = boss.direction

        # Fire origin at head
        origin_x = x + facing * 15
        origin_y = y - 25

        # Cone parameters
        max_length = 180
        length = int(max_length * min(1.0, progress * 2))

        # Draw cone of flames
        for i in range(20):
            t = i / 20
            # Position along cone
            px = origin_x + facing * int(length * t)
            py = origin_y + int(math.sin(phase * 3 + i) * 3)

            # Width increases along cone
            width = int(8 + t * 35)

            # Multiple flame puffs across cone width
            for j in range(4):
                offset = (j - 1.5) * width / 3
                wobble = math.sin(phase * 4 + i + j) * 3
                fx = px
                fy = py + int(offset) + int(wobble)

                alpha = int(220 * (1 - t * 0.6))
                size = int(6 + t * 8 + math.sin(phase * 5 + i * 0.3) * 2)
                _NS_ignis_drachorn._draw_flame_puff(surface, fx, fy, size, phase, alpha)

        # Very bright core stream
        for i in range(15):
            t = i / 15
            px = origin_x + facing * int(length * t)
            py = origin_y + int(math.sin(phase * 4 + i) * 2)
            size = max(2, int(5 - t * 3))
            _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_bright"], 220), (px, py), size)
            _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_hot"], 240), (px, py), max(1, size - 1))
            _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_white"], 250), (px, py), max(1, size - 2))

        # Impact explosion at end
        if progress > 0.3:
            end_x = origin_x + facing * length
            end_y = origin_y
            explosion_r = int(20 + math.sin(phase * 3) * 5)
            _NS_ignis_drachorn._draw_flame_puff(surface, end_x, end_y, explosion_r, phase, 240)
            # Radial sparks
            for i in range(8):
                angle = phase * 2 + i * math.pi / 4
                sx = end_x + int(math.cos(angle) * explosion_r * 1.5)
                sy = end_y + int(math.sin(angle) * explosion_r * 1.5)
                _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["fire_bright"], (sx, sy), 3)
                _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["fire_hot"], (sx, sy), 1)


    # ===================================================================
    # SKILL W: DRAGON TAIL - Whip attack
    # ===================================================================
    def _draw_dragon_tail_ground(surface, boss, x, y, timer, phase):
        """Ground shockwave from tail strike."""
        progress = max(0.0, min(1.0, 1 - timer / 60))
        facing = boss.direction

        if progress > 0.4:
            # Shockwave
            wave_r = int((progress - 0.4) * 100)
            wave_x = x + facing * 60
            wave_y = y + 40
            alpha = int(180 * (1 - (progress - 0.4) / 0.6))
            _NS_ignis_drachorn._ellipse(surface, (*_NS_ignis_drachorn.PALETTE["fire_dark"], alpha),
                     (wave_x - wave_r, wave_y - wave_r // 3,
                      wave_r * 2, wave_r * 2 // 3), 3)
            _NS_ignis_drachorn._ellipse(surface, (*_NS_ignis_drachorn.PALETTE["fire_mid"], alpha),
                     (wave_x - wave_r + 3, wave_y - wave_r // 3 + 2,
                      wave_r * 2 - 6, wave_r * 2 // 3 - 4), 2)


    def _draw_dragon_tail(surface, boss, x, y, timer, phase):
        """Dragon tail whipping out."""
        progress = max(0.0, min(1.0, 1 - timer / 60))
        facing = boss.direction

        # Tail base
        base_x = x + facing * 8
        base_y = y - 5

        # Whip motion
        if progress < 0.3:
            t = progress / 0.3
            max_angle = -1.2 * t
        elif progress < 0.6:
            t = (progress - 0.3) / 0.3
            max_angle = -1.2 + 2.4 * t
        else:
            t = (progress - 0.6) / 0.4
            max_angle = 1.2 * (1 - t)

        # Draw tail as chain of segments
        segments = 12
        tail_length = 60 + int(progress * 40)
        prev_x, prev_y = base_x, base_y

        for i in range(1, segments + 1):
            t_seg = i / segments
            # Curved tail path
            angle_offset = max_angle * (t_seg ** 0.7)
            seg_x = base_x + int(facing * tail_length * t_seg * math.cos(angle_offset))
            seg_y = base_y + int(tail_length * t_seg * math.sin(angle_offset))

            # Segment thickness decreases toward tip
            thickness = max(2, int(8 * (1 - t_seg * 0.8)))

            # Draw segment (dragon scale look)
            _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["shadow_deep"],
                    (prev_x + 1, prev_y + 1), (seg_x + 1, seg_y + 1), thickness + 2)
            _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["dragon_darkest"],
                    (prev_x, prev_y), (seg_x, seg_y), thickness + 1)
            _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["dragon_dark"],
                    (prev_x, prev_y), (seg_x, seg_y), thickness)
            _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["dragon_mid"],
                    (prev_x, prev_y), (seg_x, seg_y), max(1, thickness - 2))

            # Scale segments (small circles)
            if i % 2 == 0:
                _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["dragon_dark"],
                          (seg_x, seg_y), thickness // 2 + 1)
                _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["dragon_mid"],
                          (seg_x, seg_y - 1), thickness // 2)
                _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["dragon_light"],
                          (seg_x, seg_y - 1), max(1, thickness // 2 - 1))

            # Fire embers along tail
            if i % 3 == 0:
                _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_mid"], 180),
                          (seg_x, seg_y - thickness), 2)
                _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["fire_bright"],
                          (seg_x, seg_y - thickness), 1)

            prev_x, prev_y = seg_x, seg_y

        # Spiked club at tail tip
        tip_x, tip_y = prev_x, prev_y
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["shadow_deep"], (tip_x + 2, tip_y + 2), 9)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["dragon_darkest"], (tip_x, tip_y), 8)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["dragon_dark"], (tip_x, tip_y), 6)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["dragon_mid"], (tip_x - 1, tip_y - 1), 4)

        # Spikes on tip
        for spike_angle in range(0, 360, 60):
            rad = math.radians(spike_angle) + phase * 0.5
            spike_x = tip_x + int(math.cos(rad) * 12)
            spike_y = tip_y + int(math.sin(rad) * 12)
            _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["dragon_darkest"], [
                (tip_x + int(math.cos(rad) * 6), tip_y + int(math.sin(rad) * 6)),
                (tip_x + int(math.cos(rad + 0.3) * 6),
                 tip_y + int(math.sin(rad + 0.3) * 6)),
                (spike_x, spike_y),
            ])

        # Fire on tip
        _NS_ignis_drachorn._draw_flame_puff(surface, tip_x, tip_y - 5, 8, phase, 220)


    # ===================================================================
    # SKILL E: DRAGON BLOOD - Fire armor buff
    # ===================================================================
    def _draw_dragon_blood_ground(surface, boss, x, y, timer, phase):
        """Ground fire ring."""
        progress = max(0.0, min(1.0, 1 - timer / 90))
        pulse = math.sin(phase * 2) * 0.2 + 0.8
        radius = int(40 + progress * 20)

        _NS_ignis_drachorn._ellipse(surface, (*_NS_ignis_drachorn.PALETTE["fire_dark"], int(120 * pulse)),
                 (x - radius, y + 32 - radius // 4, radius * 2, radius // 2), 3)
        _NS_ignis_drachorn._ellipse(surface, (*_NS_ignis_drachorn.PALETTE["fire_mid"], int(100 * pulse)),
                 (x - radius + 4, y + 34 - radius // 4,
                  radius * 2 - 8, radius // 2 - 4), 2)


    def _draw_dragon_blood_foreground(surface, boss, x, y, timer, phase):
        """Fire aura enveloping the body."""
        progress = max(0.0, min(1.0, 1 - timer / 90))
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7

        # Large fire aura around body
        aura_layers = [
            (55, _NS_ignis_drachorn.PALETTE["fire_darkest"], 80),
            (48, _NS_ignis_drachorn.PALETTE["fire_dark"], 100),
            (40, _NS_ignis_drachorn.PALETTE["fire_mid"], 90),
            (32, _NS_ignis_drachorn.PALETTE["fire_light"], 70),
        ]
        for radius, color, alpha in aura_layers:
            a = int(alpha * pulse * progress)
            _NS_ignis_drachorn._aacircle(surface, (*color, a), (x, y - 10), radius)

        # Rising flames from body
        for i in range(12):
            angle = phase * 1.5 + i * math.pi / 6
            base_r = 25
            # Flame goes upward and outward
            wobble = math.sin(phase * 3 + i) * 3
            fx = x + int(math.cos(angle) * base_r) + int(wobble)
            fy = y - 15 + int(math.sin(angle) * base_r * 0.5)

            # Rising trail
            for j in range(4):
                rise_t = j / 4
                ry = fy - int(rise_t * 20)
                rx = fx + int(math.sin(phase * 4 + j) * 2)
                size = max(1, int(5 * (1 - rise_t)))
                alpha = int(200 * (1 - rise_t) * pulse)
                _NS_ignis_drachorn._draw_flame_puff(surface, rx, ry, size, phase, alpha)

        # Bright core flames near body
        for i in range(8):
            angle = phase * 2 + i * math.pi / 4
            r = 20 + int(math.sin(phase * 3 + i) * 3)
            fx = x + int(math.cos(angle) * r)
            fy = y - 10 + int(math.sin(angle) * r * 0.6)
            _NS_ignis_drachorn._draw_flame_puff(surface, fx, fy, 5, phase, 200)


    # ===================================================================
    # SKILL R: ELDER DRAGON FORM
    # ===================================================================
    def _draw_elder_form_ground(surface, boss, x, y, timer, phase):
        """Massive fire circle for transformation."""
        progress = max(0.0, min(1.0, 1 - timer / 120))
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        radius = int(60 + progress * 20)

        _NS_ignis_drachorn._ellipse(surface, (*_NS_ignis_drachorn.PALETTE["fire_darkest"], int(180 * pulse)),
                 (x - radius, y + 32 - radius // 3, radius * 2, radius * 2 // 3), 4)
        _NS_ignis_drachorn._ellipse(surface, (*_NS_ignis_drachorn.PALETTE["fire_dark"], int(150 * pulse)),
                 (x - radius + 5, y + 34 - radius // 3,
                  radius * 2 - 10, radius * 2 // 3 - 6), 3)
        _NS_ignis_drachorn._ellipse(surface, (*_NS_ignis_drachorn.PALETTE["fire_mid"], int(120 * pulse)),
                 (x - radius + 10, y + 36 - radius // 3,
                  radius * 2 - 20, radius * 2 // 3 - 12), 2)

        # Runes in circle
        for i in range(8):
            angle = phase * 0.4 + i * math.pi / 4
            rx = x + int(math.cos(angle) * (radius - 8))
            ry = y + 38 + int(math.sin(angle) * (radius // 3 - 4))
            _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["fire_bright"], (rx, ry), 3)
            _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["fire_hot"], (rx, ry), 1)


    def _draw_elder_dragon_form(surface, boss, x, y, timer, pulse):
        """Ignis transformed into elder red dragon."""
        facing = boss.direction
        bob = int(math.sin(pulse * 0.8) * 3)
        cy = y + bob

        # Shadow (larger)
        _NS_ignis_drachorn._draw_shadow(surface, x, y + 48)
        _NS_ignis_drachorn._ellipse(surface, (*_NS_ignis_drachorn.PALETTE["shadow"], 100),
                 (x - 60, y + 46, 120, 12))

        # Fire aura
        for radius in range(70, 20, -5):
            alpha = int((70 - radius) * 2)
            _NS_ignis_drachorn._aacircle(surface, (*_NS_ignis_drachorn.PALETTE["fire_darkest"], alpha),
                      (x, cy - 10), radius)

        # ===== DRAGON BODY =====
        body_y = cy - 5

        # Body (large elongated)
        body_pts = [
            (x - 30 * facing, body_y + 5),
            (x - 25 * facing, body_y - 15),
            (x - 5 * facing, body_y - 22),
            (x + 15 * facing, body_y - 20),
            (x + 30 * facing, body_y - 10),
            (x + 35 * facing, body_y + 5),
            (x + 25 * facing, body_y + 15),
            (x, body_y + 20),
            (x - 20 * facing, body_y + 15),
        ]
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["shadow_deep"], [(p[0] + 3, p[1] + 3) for p in body_pts])
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["dragon_darkest"], body_pts)

        body_inner = [
            (x - 26 * facing, body_y + 3),
            (x - 22 * facing, body_y - 12),
            (x - 5 * facing, body_y - 18),
            (x + 12 * facing, body_y - 16),
            (x + 26 * facing, body_y - 8),
            (x + 30 * facing, body_y + 3),
            (x + 20 * facing, body_y + 12),
            (x, body_y + 16),
            (x - 18 * facing, body_y + 12),
        ]
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["dragon_dark"], body_inner)
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["dragon_mid"], [
            (x - 20 * facing, body_y),
            (x - 15 * facing, body_y - 10),
            (x + 5 * facing, body_y - 14),
            (x + 20 * facing, body_y - 5),
            (x + 22 * facing, body_y + 5),
            (x + 10 * facing, body_y + 10),
            (x - 10 * facing, body_y + 8),
        ])

        # Body scales
        for row in range(3):
            for col in range(-3, 4):
                sx = x + col * 7 * facing + (row % 2) * 3 * facing
                sy = body_y - 5 + row * 6
                if abs(sy - body_y) < 15 and abs(sx - x) < 28:
                    _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["dragon_dark"], (sx, sy), 3)
                    _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["dragon_mid"], (sx, sy - 1), 2)
                    _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["dragon_light"], (sx - 1, sy - 2), 1)

        # ===== WINGS =====
        wing_flap = math.sin(pulse * 2) * 0.3
        for side in (-1, 1):
            _NS_ignis_drachorn._draw_dragon_wing(surface, x, body_y - 10, side, facing, wing_flap, pulse)

        # ===== TAIL =====
        tail_curve = math.sin(pulse * 1.2) * 8
        tail_base_x = x - 25 * facing
        tail_base_y = body_y + 5
        tail_segments = 8
        prev_tx, prev_ty = tail_base_x, tail_base_y
        for i in range(1, tail_segments + 1):
            t = i / tail_segments
            tx = tail_base_x - facing * int(45 * t)
            ty = tail_base_y + int(math.sin(t * 3 + pulse) * (10 + int(tail_curve)))
            thickness = max(2, int(10 * (1 - t * 0.8)))

            _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["dragon_darkest"],
                    (prev_tx, prev_ty), (tx, ty), thickness + 1)
            _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["dragon_dark"],
                    (prev_tx, prev_ty), (tx, ty), thickness)
            _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["dragon_mid"],
                    (prev_tx, prev_ty), (tx, ty), max(1, thickness - 2))
            prev_tx, prev_ty = tx, ty

        # Tail tip spikes
        for i in range(3):
            angle = math.pi / 4 * i
            sx = prev_tx + int(math.cos(angle) * 8)
            sy = prev_ty - int(math.sin(angle) * 8)
            _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["dragon_darkest"], [
                (prev_tx, prev_ty - 2), (prev_tx, prev_ty + 2), (sx, sy)
            ])

        # ===== HEAD =====
        head_x = x + 25 * facing
        head_y = body_y - 15
        _NS_ignis_drachorn._draw_dragon_head(surface, head_x, head_y, facing, pulse)

        # Fire breathing effect (constant during elder form)
        breath_x = head_x + facing * 15
        breath_y = head_y + 3
        for i in range(8):
            t = i / 8
            bx = breath_x + facing * int(t * 40)
            by = breath_y + int(math.sin(pulse * 3 + i) * 4)
            size = int(4 + t * 3)
            alpha = int(220 * (1 - t * 0.5))
            _NS_ignis_drachorn._draw_flame_puff(surface, bx, by, size, pulse, alpha)


    def _draw_dragon_wing(surface, cx, cy, side, facing, flap, phase):
        """Draw one dragon wing."""
        wing_side = side * facing
        base_x = cx
        base_y = cy

        # Wing spans outward and upward
        tip_x = base_x + wing_side * 50
        tip_y = base_y - 20 + int(flap * 15)

        # Wing membrane (large triangle-ish shape)
        wing_pts = [
            (base_x, base_y),
            (base_x + wing_side * 15, base_y - 25 + int(flap * 10)),
            (base_x + wing_side * 35, base_y - 30 + int(flap * 15)),
            (tip_x, tip_y),
            (base_x + wing_side * 40, base_y - 5 + int(flap * 8)),
            (base_x + wing_side * 25, base_y + 5),
            (base_x + wing_side * 10, base_y + 3),
        ]

        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["red_darkest"], wing_pts)

        # Inner membrane
        wing_inner = [
            (base_x + wing_side * 3, base_y - 2),
            (base_x + wing_side * 15, base_y - 22 + int(flap * 10)),
            (base_x + wing_side * 33, base_y - 27 + int(flap * 15)),
            (base_x + wing_side * 46, tip_y + 3),
            (base_x + wing_side * 37, base_y - 3 + int(flap * 8)),
            (base_x + wing_side * 22, base_y + 3),
            (base_x + wing_side * 8, base_y + 1),
        ]
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["red_dark"], wing_inner)

        # Wing bones (finger structure)
        bone_ends = [
            (base_x + wing_side * 15, base_y - 25 + int(flap * 10)),
            (base_x + wing_side * 35, base_y - 30 + int(flap * 15)),
            (tip_x, tip_y),
            (base_x + wing_side * 40, base_y - 5 + int(flap * 8)),
        ]
        for be in bone_ends:
            _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["dragon_darkest"], (base_x, base_y), be, 3)
            _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["dragon_dark"], (base_x, base_y), be, 2)
            _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["dragon_mid"], (base_x, base_y), be, 1)

        # Wing outline
        for i in range(len(wing_pts)):
            p1 = wing_pts[i]
            p2 = wing_pts[(i + 1) % len(wing_pts)]
            _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["dragon_darkest"], p1, p2, 2)


    def _draw_dragon_head(surface, cx, cy, facing, phase):
        """Elder dragon head."""
        # Head main shape (elongated snout)
        head_pts = [
            (cx - 12 * facing, cy - 8),
            (cx + 5 * facing, cy - 10),
            (cx + 15 * facing, cy - 5),
            (cx + 18 * facing, cy + 2),
            (cx + 15 * facing, cy + 7),
            (cx + 5 * facing, cy + 8),
            (cx - 10 * facing, cy + 6),
            (cx - 14 * facing, cy),
        ]
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["shadow_deep"], [(p[0] + 2, p[1] + 2) for p in head_pts])
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["dragon_darkest"], head_pts)
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["dragon_dark"], [
            (cx - 10 * facing, cy - 7),
            (cx + 4 * facing, cy - 8),
            (cx + 13 * facing, cy - 4),
            (cx + 16 * facing, cy + 1),
            (cx + 13 * facing, cy + 6),
            (cx + 4 * facing, cy + 7),
            (cx - 8 * facing, cy + 5),
            (cx - 12 * facing, cy),
        ])
        _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["dragon_mid"], [
            (cx - 6 * facing, cy - 4),
            (cx + 2 * facing, cy - 5),
            (cx + 10 * facing, cy - 2),
            (cx + 12 * facing, cy + 2),
            (cx + 8 * facing, cy + 4),
            (cx - 4 * facing, cy + 3),
        ])

        # Horns swept back
        for horn_y_off in (-6, -2):
            hx1 = cx - 5 * facing
            hy1 = cy + horn_y_off
            hx2 = cx - 18 * facing
            hy2 = cy - 12 + horn_y_off
            _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["dragon_darkest"], (hx1, hy1), (hx2, hy2), 4)
            _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["dragon_dark"], (hx1, hy1), (hx2, hy2), 3)
            _NS_ignis_drachorn._aaline(surface, _NS_ignis_drachorn.PALETTE["dragon_mid"], (hx1, hy1), (hx2, hy2), 1)
            _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["dragon_darkest"], (hx2, hy2), 2)

        # Glowing eye
        eye_pulse = math.sin(phase * 3) * 0.3 + 0.7
        eye_x = cx + 2 * facing
        eye_y = cy - 3
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["eye_dark"], (eye_x, eye_y), 3)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["eye_mid"], (eye_x, eye_y), 2)
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["eye_bright"], (eye_x, eye_y),
                  max(1, int(2 * eye_pulse)))
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["eye_hot"], (eye_x, eye_y), 1)

        # Nostril
        _NS_ignis_drachorn._aacircle(surface, _NS_ignis_drachorn.PALETTE["shadow_deep"],
                  (cx + 13 * facing, cy + 1), 1)

        # Teeth
        for i in range(3):
            tx = cx + (10 + i * 2) * facing
            ty = cy + 5
            _NS_ignis_drachorn._poly(surface, _NS_ignis_drachorn.PALETTE["white"], [
                (tx, ty), (tx + facing, ty + 3), (tx + facing * 2, ty)
            ])


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_ignis_drachorn.draw_ignis(surface, boss, x, y)

    # ===================================================================
    # ALIAS - nama fungsi yang dipakai registry heroes/__init__.py
    # ===================================================================
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
