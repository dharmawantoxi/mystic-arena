"""
bosses/razak_v4.py — RAZAK PIXEL MASTERWORK v4

Goblin rider on a crimson fire-bat. Flamethrower + burning machete.
100% procedural (no PNG / image.load).

Public namespace `_NS_razak` is re-exported from bosses/level2.py so
heroes/__init__.py (`"razak": ("bosses.level2", "_NS_razak", ...)`)
and the level-2 family tests keep working. Stats / AI / damage live in
bosses/base_boss.py and are not touched here.

Identity
--------
  * Mount : red-orange fire bat (membranous wings, ember eyes, flame tail)
  * Rider : olive goblin in leather, signature blue goggles, twin brass tanks
  * Arms  : brass flamethrower (front) + fire-edge machete (swing)

Contracts locked by tools/test_razak_v3_combat.py, test_level2_masterwork.py,
test_grimjaw_masterwork.py, test_razak_no_white_cover.py:
  SCALE=0.62  GROUND_DY=52  SKILL_DUR q40/w50/e35/r90
  SKILL_RADIUS q75/w95/e80/r180  ATTACK_PHASES 6 named windows
  world-space telegraph, 3 skill phases, no additive white-out.
"""

import math
import pygame

try:
    import lighting as _lighting
except Exception:  # pragma: no cover
    _lighting = None


class _NS_razak:
    """Namespace razak — PIXEL MASTERWORK v4 + SKILL FX v4.

    Goblin rider on a crimson fire-bat. Flamethrower + burning machete.
    100% procedural: no PNG / sprite-sheet / image.load.

    v4 rewrite (from zero, same public names): denser fire-bat silhouette
    (ember veins on membrane, flame mane along the spine, fire-tipped
    tail and wing claws), juicier idle/attack secondary motion, and
    world-space skill FX that stay in lockstep with base_boss.py.

    Apa yang naik dibanding v1
    --------------------------
    1. RIG ~1.5x LEBIH BESAR di resolusi native (mahkota helm goblin
       y=-72, cakar/api bawah +40) lalu ditampilkan lewat SATU
       `SCALE = 0.62` untuk semua jalur (boss langsung, lane hero,
       portrait). Ukuran DI LAYAR tetap sekelas keluarga level-2
       (alchemist true boss >= razak mini); yang berubah adalah
       KEPADATAN detail per piksel layar.
    2. DISIPLIN PIXEL-ART: tiap material 4-6 nilai ramp dengan
       hue-shift (bayangan kulit bat didorong ungu dingin, highlight
       oranye hangat; goblin hijau -> kuning hangat), selout (salinan
       shadow_deep hanya di sisi bayangan), siluet bergerigi lewat
       `_tuft_points` (tepi belakang sayap ber-scallop, syal pilot
       robek), specular cluster 1-2 px (goggle, tangki brass, edge
       machete), dither band (`_dither_dots`) di perut bat & membran
       sayap. Key light kiri-atas konsisten lighting.py.
    3. ANATOMI: bat api bersisik dengan sayap membran 4-band + tulang
       jari + cakar, kepala naga (mata membara + kedip, moncong,
       taring, 3 tanduk, lubang hidung mendengus), ekor berujung
       panah dengan inersia; rider goblin: goggles biru khas
       (specular cluster), helm kulit ber-rivet, syal robek
       berkibar, rompi + strap X ber-jahitan, tangki bahan bakar
       brass ganda + selang + gauge, FLAMETHROWER brass ber-moncong
       flare + pilot flame flicker, MACHETE api 5-band ber-fuller.
    4. ANIMASI: wing-beat solver (downstroke memicu gust ring di
       bawah + hover bob mengikuti kepakan - pengganti foot solver
       untuk unit terbang), inersia ekor/syal/api (secondary motion),
       idle hidup (napas, kedip bat & goblin, dengus, gauge bergetar,
       pilot flame flicker), serangan 7 keyframe dengan frame IMPACT
       tersendiri di ap=0.54 (squash, bintang 6 spike, shockwave,
       smear sabit api 3 lapis) + fireball ranged tetap spawn di
       puncak ayunan.
    5. SKILL FX world-space (`_fx_scale`, cap 2.6) dengan 3 tahap
       (AKTIVASI / STEADY / TELEGRAPH) dan radius telegraph TEPAT
       dalam px dunia = radius gameplay base_boss.py:
         Q Sticky Napalm  75 px dunia DI TARGET
         W Flamebreak     95 px dunia DI TARGET
         E Firefly        80 px dunia (AOE pendaratan dash)
         R Firestorm     180 px dunia DI CASTER (bukan target - AI
                          memukul sekitar DIRI, telegraph mengikuti).
    """

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    # ── cache (nama lama dipertahankan) ─────────────────────────────
    _shadow_cache = None
    _aura_cache = None
    _flame_cache = {}
    _flash_buf = None
    _record_shadow = None
    _body_buf = None        # buffer badan untuk outline+lighting

    # Surface statis (aura/mist/platform) dibangun SEKALI lalu
    # dipakai ulang - tidak ada alokasi surface per frame.
    _STATIC_SURFACES = {}

    # ── metrik rig v2 ───────────────────────────────────────────────
    # Faktor pertumbuhan terhadap rig v1 (dokumentasi + dipakai audit).
    RIG_SCALE = 1.5
    # v4 density token (native pixels already 1.5x v1; screen SCALE 0.62).
    PIXEL = 2
    # Buffer badan: dibatasi dari extents TERUKUR semua pose (idle/
    # walk/attack x 7 keyframe/dash, dua arah hadap): sayap +-62,
    # helm -72, cakar bawah +40, + margin smear machete.
    RIG_W, RIG_H = 176, 152
    RIG_OX, RIG_OY = 88, 92

    # Satu SCALE untuk SEMUA jalur (boss langsung, lane hero, portrait).
    # PERINGATAN: jangan pisahkan SCALE per jalur; itu merusak
    # normalisasi _measure_native_size di heroes/__init__.py.
    SCALE = 0.62
    # Garis tanah dunia relatif jangkar (bayangan/patch/telegraph).
    GROUND_DY = 52

    # Durasi visual skill (frame) - HARUS sama dengan active_skill_timer
    # yang diisi AI di bosses/base_boss.py (_razak_q/w/e/r).
    SKILL_DUR = {"q": 40, "w": 50, "e": 35, "r": 90}

    # Radius gameplay tiap skill dalam PX DUNIA (bosses/base_boss.py):
    #   q -> AOE 75 di target, w -> AOE 95 di target,
    #   e -> AOE 80 setelah dash, r -> AOE 180 di sekitar DIRI.
    # Telegraph digambar TEPAT di angka ini lewat _ring_r (world-space).
    SKILL_RADIUS = {"q": 75, "w": 95, "e": 80, "r": 180}

    # ── v3 COMBAT FX: debug & animation controller ────────────────────
    #: Overlay debug (hitbox, hurtbox, jangkauan, state/frame, FPS,
    #: partikel). Sama dengan karakter v3 lain - renderer & lapisan
    #: hidup masing-masing punya flag, dua-duanya mati secara default.
    DEBUG_CHARACTER = False

    #: Prioritas state animasi (angka besar = lebih penting; DEATH
    #: mengunci). Dipakai state machine cermin di heroes/razak_fx.py.
    ANIM_PRIORITY = {
        "IDLE": 10, "WALK": 20, "RUN": 25, "CHARGE": 40,
        "ATTACK": 45, "SWING": 50, "CAST": 55, "SKILL": 56,
        "SPECIAL": 60, "HIT": 62, "HURT": 65, "DEATH": 100,
    }

    #: Timeline serangan (fraksi progress 0..1). Keyframe renderer:
    #: 0.14 wind-up, 0.30 tension, 0.48 strike, 0.54 IMPACT, 0.72
    #: follow, 1.0 recover. Fase di bawah dipakai controller renderer
    #: DAN lapisan hidup (satu sumber kebenaran).
    ATTACK_WINDUP_END = 0.30
    ATTACK_IMPACT = 0.54
    ATTACK_SWING_END = 0.62
    ATTACK_FOLLOW_END = 0.80
    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, 0.09),
        ("WINDUP",       0.09, 0.30),
        ("SWING",        0.30, 0.50),
        ("IMPACT",       0.50, 0.62),
        ("FOLLOW",       0.62, 0.80),
        ("RECOVERY",     0.80, 1.00),
    )

    #: Geometri machete (ruang native rig v2; dipakai FX hidup).
    MACHETE_LEN = 28
    MACHETE_ARM_LEN = 14
    MACHETE_BLADE_TIP = 26       # titik bintang impact v2

    # ---------------------------------------------------------------------------
    # HD Palette v2 - fire orange / green goblin / red bat mount.
    # Semua kunci lama dipertahankan (nilai dituning ulang dengan
    # hue-shift) + kunci baru untuk rim, smoke, dan gold.
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Goblin skin - green (bayangan didorong biru-hijau dingin,
        # highlight kuning hangat)
        "gob_darkest":    (22,  42,  26),
        "gob_dark":       (52,  92,  42),
        "gob_mid":        (95, 145,  55),
        "gob_light":      (140, 190, 78),
        "gob_high":       (188, 224, 112),
        "gob_shine":      (228, 250, 168),
        "gob_rim":        (240, 255, 196),

        # Bat/dragon mount - red-orange (bayangan ungu dingin)
        "bat_darkest":    (36,  14,  20),
        "bat_dark":       (92,  30,  24),
        "bat_mid":        (155, 62,  25),
        "bat_light":      (210, 95,  38),
        "bat_high":       (242, 142, 66),
        "bat_shine":      (255, 184, 104),
        "bat_rim":        (255, 214, 150),

        # Bat belly (lighter)
        "belly_dark":     (112, 56,  32),
        "belly_mid":      (170, 105, 55),
        "belly_light":    (216, 156, 88),

        # Wing membrane (bayangan maroon-ungu)
        "wing_darkest":   (32,  12,  16),
        "wing_dark":      (74,  24,  20),
        "wing_mid":       (135, 45,  22),
        "wing_light":     (190, 78,  35),
        "wing_high":      (228, 118, 56),

        # Leather / gear
        "leather_darkest": (24, 15,  10),
        "leather_dark":   (52,  33,  19),
        "leather_mid":    (95,  62,  32),
        "leather_light":  (150, 100, 55),
        "leather_high":   (196, 144, 88),

        # Metal
        "metal_darkest":  (18,  15,  20),
        "metal_dark":     (48,  42,  50),
        "metal_mid":      (95,  88,  98),
        "metal_light":    (160, 152, 165),
        "metal_shine":    (225, 220, 228),

        # Brass / bronze (gun & tanks)
        "brass_dark":     (82,  50,  16),
        "brass_mid":      (155, 108, 40),
        "brass_light":    (212, 170, 78),
        "brass_shine":    (250, 222, 138),

        # Fire - orange/yellow
        "fire_darkest":   (55,  12,   5),
        "fire_dark":      (135, 30,   8),
        "fire_mid":       (215, 80,  15),
        "fire_bright":    (255, 130, 30),
        "fire_hot":       (255, 180, 60),
        "fire_glow":      (255, 220, 130),
        "fire_white":     (255, 250, 210),

        # Blue (goggles - signature)
        "blue_dark":      (15,  35,  75),
        "blue_mid":       (45,  95, 165),
        "blue_light":     (95, 165, 230),
        "blue_shine":     (176, 224, 255),

        # Eyes
        "eye_dark":       (78,  20,   6),
        "eye_bright":     (255, 220, 100),
        "eye_hot":        (255, 250, 200),

        # Teeth / claws
        "bone_dark":      (110, 95,  70),
        "bone_light":     (222, 212, 178),
        "bone_shine":     (246, 240, 218),

        # Smoke (knalpot flamethrower)
        "smoke_dark":     (38,  30,  30),
        "smoke_mid":      (76,  60,  56),

        # Gold trim (gesper, gauge)
        "gold_dark":      (96,  64,  20),
        "gold_mid":       (178, 132, 46),
        "gold_light":     (240, 200, 98),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (5,   3,   3),
        "white":          (255, 255, 255),
    }

    # ---------------------------------------------------------------------------
    # Primitif dasar (standar keluarga masterwork)
    # ---------------------------------------------------------------------------
    def _static(key, builder):
        """Surface statis ter-cache (dibangun sekali, dipakai ulang)."""
        surf = _NS_razak._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_razak._STATIC_SURFACES[key] = surf
        return surf

    _CLAMP_MEMO = {}

    def _clamp(color):
        """Clamp color channels, supports both RGB and RGBA (memo)."""
        try:
            hit = _NS_razak._CLAMP_MEMO.get(color)
        except TypeError:
            return tuple(max(0, min(255, int(c))) for c in color)
        if hit is not None:
            return hit
        out = tuple(max(0, min(255, int(c))) for c in color)
        memo = _NS_razak._CLAMP_MEMO
        if len(memo) > 8192:
            memo.clear()
        memo[color] = out
        return out

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _mix(a, b, t):
        """Blend linear dua warna palette (t=0 -> a, t=1 -> b)."""
        t = max(0.0, min(1.0, t))
        return _NS_razak._clamp(
            (a[0] + (b[0] - a[0]) * t,
             a[1] + (b[1] - a[1]) * t,
             a[2] + (b[2] - a[2]) * t))

    def _hash01(i):
        """Pseudo-random deterministik 0..1 (stabil antar frame & cache)."""
        x = math.sin(i * 127.1 + 311.7) * 43758.5453
        return x - math.floor(x)

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_razak._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4),
                                  pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_razak.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_razak._clamp(color)
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
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_razak._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((int(w), int(h)), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)

    def _ellipse(surface, color, rect, width=0):
        color = _NS_razak._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, int(rw), int(rh)), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3],
                            (rect[0], rect[1], int(rect[2]), int(rect[3])),
                            width)

    def _rect(surface, color, rect, border_radius=0):
        color = _NS_razak._clamp(color)
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

    def _ring(surface, center, radius, width, color, alpha):
        """Cincin skill: stroke gelap di belakang + cincin terang di atas."""
        alpha = _NS_razak._alpha(alpha)
        if alpha <= 0:
            return
        cx, cy = int(center[0]), int(center[1])
        r = int(radius)
        if r <= 0:
            return
        _NS_razak._aacircle(surface, (6, 3, 3, alpha), (cx, cy), r + 1,
                            max(1, width + 2))
        _NS_razak._aacircle(surface, (*color, alpha), (cx, cy), r,
                            max(1, width))

    # ---------------------------------------------------------------------------
    # Konversi ruang dunia <-> canvas renderer
    # ---------------------------------------------------------------------------
    def _world_to_local(boss, x, y, wx, wy):
        """Titik DUNIA -> ruang gambar renderer (kompensasi _render_scale)."""
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(wx), int(wy)
        scale = float(scale) or 1.0
        ox = (float(wx) - float(getattr(boss, "x", x))) / scale
        oy = (float(wy) - float(getattr(boss, "y", y))) / scale
        rng = int(getattr(boss, "range", 130) or 130)
        half = max(120, int(rng / scale) + 40)
        max_off = half - 20
        d = math.hypot(ox, oy)
        if d > max_off:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # DENGAN kompensasi scale supaya beam/proyektil mendarat
            # TEPAT di target setelah blit.
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return (int(x + 200 / float(getattr(boss, "_render_scale", 1.0) or 1.0)
                    * getattr(boss, "direction", 1)), int(y))

    # ===================================================================
    # SKILL FX PRIMITIVES (standar Thorne v2.1)
    # ===================================================================
    def _fx_scale(boss):
        """Faktor skala efek skill (world-space).

        Hero dirender ke canvas lalu dikecilkan ``_render_scale`` saat
        di-blit -> efek (cincin, retakan, kobaran) ikut menyusut. Dengan
        faktor 1/_render_scale (cap 2.6 supaya tetap muat di canvas
        cache) ukuran efek DI LAYAR setara boss asli. Boss asli (tanpa
        _render_scale) = 1.0.
        """
        scale = getattr(boss, "_render_scale", None)
        if not scale:
            return 1.0
        return max(1.0, min(2.6, 1.0 / float(scale)))

    def _ring_r(boss, world_px, surface):
        """Radius dunia (px) -> px canvas, di-clamp ke dalam canvas.

        Dipakai untuk telegraph yang HARUS sama dengan radius gameplay
        (Q 75 / W 95 / E 80 / R 180 px dunia).
        """
        scale = getattr(boss, "_render_scale", None)
        r = float(world_px) / float(scale) if scale else float(world_px)
        margin = min(surface.get_width(), surface.get_height()) // 2 - 10
        return int(max(4, min(r, margin)))

    def _spark_star(surface, cx, cy, size, color, alpha, spikes=6, rot=0.4,
                    core=None):
        """Bintang kilat: spike panjang-pendek selang-seling + inti."""
        alpha = _NS_razak._alpha(alpha)
        if alpha <= 0 or size <= 0:
            return
        for k in range(spikes):
            ang = rot + k * math.pi * 2 / spikes
            ln = size * (1.0 if k % 2 == 0 else 0.55)
            _NS_razak._aaline(surface, (*color, alpha),
                              (int(cx), int(cy)),
                              (int(cx + math.cos(ang) * ln),
                               int(cy + math.sin(ang) * ln * .8)),
                              2 if k % 2 == 0 else 1)
        if core:
            _NS_razak._aacircle(surface, (*core, alpha), (int(cx), int(cy)),
                                max(1, int(size * .3)))

    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        """Satu panah '>' menghadap arah ``ang`` (telegraph bergerak)."""
        alpha = _NS_razak._alpha(alpha)
        if alpha <= 0 or size <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        tipx, tipy = cx + ca * size, cy + sa * size
        for s in (-1, 1):
            _NS_razak._aaline(
                surface, (*color, alpha),
                (int(cx + px * s * size * .55 - ca * size * .5),
                 int(cy + py * s * size * .55 - sa * size * .5)),
                (int(tipx), int(tipy)), width)

    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=10, thick=3, span=0.6, squash=.92):
        """Cincin putus-putus yang berputar (marker AOE / rune ring)."""
        alpha = _NS_razak._alpha(alpha)
        if alpha <= 0 or radius <= 1:
            return
        for i in range(segments):
            a0 = phase + i * math.pi * 2 / segments
            a1 = a0 + math.pi * 2 / segments * span
            p0 = (cx + math.cos(a0) * radius, cy + math.sin(a0) * radius * squash)
            p1 = (cx + math.cos(a1) * radius, cy + math.sin(a1) * radius * squash)
            _NS_razak._aaline(surface, (*color, alpha), p0, p1, thick)

    # -------------------------------------------------------------------
    # DECAL TANAH (standar keluarga: dibangun sekali per (radius, gaya))
    # -------------------------------------------------------------------
    _DECAL_CACHE = {}
    _DECAL_ORDER = []

    def _decal(key, size, builder):
        """Surface decal ter-cache; LRU sederhana supaya memori terbatas."""
        hit = _NS_razak._DECAL_CACHE.get(key)
        if hit is not None:
            return hit
        surf = builder(size)
        _NS_razak._DECAL_CACHE[key] = surf
        _NS_razak._DECAL_ORDER.append(key)
        if len(_NS_razak._DECAL_ORDER) > 48:
            old = _NS_razak._DECAL_ORDER.pop(0)
            _NS_razak._DECAL_CACHE.pop(old, None)
        return surf

    def _blit_decal(surface, decal, cx, cy, alpha=255, add=False):
        """Blit decal ter-pusat di (cx, cy) dengan alpha & mode opsional."""
        alpha = _NS_razak._alpha(alpha)
        if alpha <= 0:
            return
        w, h = decal.get_size()
        decal.set_alpha(alpha)
        flags = pygame.BLEND_RGBA_ADD if add else 0
        surface.blit(decal, (int(cx) - w // 2, int(cy) - h // 2),
                     special_flags=flags)
        decal.set_alpha(255)

    def _quantize(v, step=6):
        """Bulatkan radius ke kelipatan `step` supaya decal cache nyangkut."""
        return max(step, int(round(float(v) / step) * step))

    def _build_falloff_ring(size, color, core, thickness, softness,
                            inner_glow):
        """Cincin ber-gradien: inti terang -> falloff halus ke luar."""
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
            col = _NS_razak._mix(color, core, min(1.0, max(0.0, t - 0.45)
                                                  * 1.5))
            pygame.draw.circle(surf, (*col, int(200 * t)), (c, c), r, 1)
        if inner_glow > 0:
            for r in range(lo, 0, -2):
                t = (r / float(max(1, lo))) ** 2
                a = int(inner_glow * t)
                if a > 1:
                    pygame.draw.circle(surf, (*color, a), (c, c), r, 2)
        return surf

    def _ground_ring(surface, cx, cy, radius, color, core, alpha,
                     thickness=3, softness=7, inner_glow=0, add=True):
        """Cincin AOE kelas produksi: decal ber-falloff, additive."""
        radius = _NS_razak._quantize(radius, 6)
        if radius < 6:
            return
        pad = softness + thickness + 3
        size = radius * 2 + pad * 2
        key = ("fring", radius, color, core, thickness, softness, inner_glow)
        decal = _NS_razak._decal(
            key, size,
            lambda n: _NS_razak._build_falloff_ring(
                n, color, core, thickness, softness, inner_glow))
        _NS_razak._blit_decal(surface, decal, cx, cy, alpha, add=add)

    def _build_arc_ring(size, color, core, segments, span, thickness,
                        softness, taper):
        """Cincin busur: tiap segmen meruncing di kedua ujung."""
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
            outer, inner = [], []
            for k in range(steps + 1):
                t = k / steps
                ang = a0 + (a1 - a0) * t
                w = thickness * (taper + (1 - taper) *
                                 math.sin(t * math.pi))
                outer.append((c + math.cos(ang) * (r_nom + w * .5),
                              c + math.sin(ang) * (r_nom + w * .5)))
                inner.append((c + math.cos(ang) * (r_nom - w * .5),
                              c + math.sin(ang) * (r_nom - w * .5)))
            pts = outer + inner[::-1]
            pygame.draw.polygon(surf, (*color, 150), pts)
            mid = [(c + (px - c) * .997, c + (py - c) * .997)
                   for px, py in outer[1:-1]] + \
                  [(c + (px - c) * 1.003, c + (py - c) * 1.003)
                   for px, py in inner[1:-1]][::-1]
            if len(mid) >= 3:
                pygame.draw.polygon(surf, (*core, 205), mid)
        return surf

    def _rune_ring(surface, cx, cy, radius, color, core, alpha, spin,
                   segments=12, span=0.42, thickness=3.0, taper=0.85):
        """Cincin busur berputar (telegraph 'rune terbakar')."""
        radius = _NS_razak._quantize(radius, 8)
        if radius < 8:
            return
        pad = int(thickness) + 8
        size = radius * 2 + pad * 2
        key = ("arcring", radius, color, core, segments, round(span, 2),
               round(thickness, 1), round(taper, 2))
        decal = _NS_razak._decal(
            key, size,
            lambda n: _NS_razak._build_arc_ring(
                n, color, core, segments, span, thickness, 6, taper))
        deg = -math.degrees(spin) % (360.0 / max(1, segments))
        rot = pygame.transform.rotate(decal, deg)
        _NS_razak._blit_decal(surface, rot, cx, cy, alpha, add=True)

    def _build_scorch(size, color, edge, seed):
        """Noda gosong tanah: gumpalan lembut ber-tepi tidak beraturan."""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        r = c - 2
        for i in range(r, 0, -2):
            t = 1.0 - i / float(r)
            a = int(120 * (t ** 1.6))
            if a > 1:
                col = _NS_razak._mix(edge, color, t)
                pygame.draw.circle(surf, (*col, a), (c, c), i)
        for i in range(20):
            ang = _NS_razak._hash01(seed * 31 + i) * math.tau
            rr = r * (0.80 + 0.16 * _NS_razak._hash01(seed * 17 + i))
            br = max(3, int(r * 0.15 * (0.5 +
                     _NS_razak._hash01(seed * 7 + i))))
            bx = int(c + math.cos(ang) * rr)
            by = int(c + math.sin(ang) * rr)
            for k in range(br, 0, -1):
                a = int(70 * (1.0 - k / float(br)) ** 1.5)
                if a > 1:
                    pygame.draw.circle(surf, (*edge, a), (bx, by), k)
        return surf

    def _ground_scorch(surface, cx, cy, radius, color, edge, alpha, seed=1):
        """Alas gosong ter-cache di bawah telegraph."""
        radius = _NS_razak._quantize(radius, 10)
        if radius < 8:
            return
        size = radius * 2 + 6
        key = ("scorch", radius, color, edge, seed)
        decal = _NS_razak._decal(
            key, size,
            lambda n: _NS_razak._build_scorch(n, color, edge, seed))
        _NS_razak._blit_decal(surface, decal, cx, cy, alpha)

    def _build_zone_fill(size, color, edge_bias):
        """Isi zona AOE: paling pekat DI DEKAT TEPI, memudar ke tengah."""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        r = c - 1
        for i in range(r, 0, -1):
            t = i / float(r)
            v = t ** edge_bias
            a = int(115 * v)
            if a > 1:
                pygame.draw.circle(surf, (*color, a), (c, c), i)
        return surf

    def _zone_fill(surface, cx, cy, radius, color, alpha, edge_bias=3.2):
        """Wash zona AOE ter-cache (additive lembut)."""
        radius = _NS_razak._quantize(radius, 8)
        if radius < 6:
            return
        decal = _NS_razak._decal(
            ("zone", radius, color, round(edge_bias, 1)), radius * 2,
            lambda n: _NS_razak._build_zone_fill(n, color, edge_bias))
        _NS_razak._blit_decal(surface, decal, cx, cy, alpha, add=True)

    def _build_radial_grad(size, color):
        """Gradien radial lembut (glow / pilar bawah)."""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        for i in range(c, 0, -1):
            t = 1.0 - i / float(c)
            a = int(190 * (t ** 2.2))
            if a > 1:
                pygame.draw.circle(surf, (*color, a), (c, c), i)
        return surf

    def _glow(surface, cx, cy, radius, color, alpha):
        """Glow radial additive ter-cache (pengganti tumpukan aacircle)."""
        radius = _NS_razak._quantize(radius, 8)
        if radius < 4:
            return
        size = radius * 2
        decal = _NS_razak._decal(
            ("glow", radius, color), size,
            lambda n: _NS_razak._build_radial_grad(n, color))
        _NS_razak._blit_decal(surface, decal, cx, cy, alpha, add=True)

    def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                      width=3):
        """Retakan tanah berzigzag (3 segmen) dengan seam menyala."""
        alpha = _NS_razak._alpha(alpha)
        if alpha <= 0 or length <= 0:
            return
        x, y, a = cx, cy, ang
        pts = [(x, y)]
        for i in range(3):
            a += (_NS_razak._hash01(seed * 7 + i * 13) - .5) * .8
            seg = length / 3.0
            x += math.cos(a) * seg
            y += math.sin(a) * seg * .55      # perspektif tanah
            pts.append((x, y))
        for i in range(len(pts) - 1):
            _NS_razak._aaline(surface, (*colors[0], alpha),
                              pts[i], pts[i + 1], width + 2)
            _NS_razak._aaline(surface, (*colors[1], alpha),
                              pts[i], pts[i + 1], width)

    def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
        """Ubah spine halus jadi tepi bergerigi (kain robek / membran).

        Deterministik (hash) - aman untuk cache sprite.
        """
        out = [spine[0]]
        for i in range(len(spine) - 1):
            ax, ay = spine[i]
            bx, by = spine[i + 1]
            seg = math.hypot(bx - ax, by - ay)
            n = max(1, int(seg / min_len))
            nx, ny = (by - ay), -(bx - ax)
            ln = math.hypot(nx, ny) or 1.0
            nx, ny = nx / ln, ny / ln
            for j in range(n):
                t = (j + 0.5) / n
                px, py = ax + (bx - ax) * t, ay + (by - ay) * t
                d = depth * (0.55 + 0.45 * _NS_razak._hash01(i * 7 + j * 13 + seed))
                if j % 2 == 0:
                    out.append((px + nx * d, py + ny * d))
                else:
                    out.append((px - nx * d * 0.45, py - ny * d * 0.45))
            out.append((bx, by))
        return out

    def _dither_dots(surface, color, points, alpha=80):
        """Dither band 50% klasik (bertahan setelah downscale)."""
        col = (*color, _NS_razak._alpha(alpha))
        for i, (px, py) in enumerate(points):
            if i % 2 == 0:
                _NS_razak._aacircle(surface, col, (int(px), int(py)), 1)
    # ---------------------------------------------------------------------------
    # FIRE PARTICLE / FLAME DRAWING (nama lama dipertahankan)
    # ---------------------------------------------------------------------------
    def _draw_flame(surface, cx, cy, size, phase, alpha=255):
        """Api tunggal ber-lapis (di-cache per size/phase-bucket/alpha)."""
        NS = _NS_razak
        height = int(size * 2)
        pb = int(phase * 4) % 8
        ab = int(alpha / 32) * 32
        key = (int(size), pb, ab)
        spr = NS._flame_cache.get(key)
        if spr is None:
            spr = pygame.Surface((int(size * 2) + 6, height + 4),
                                 pygame.SRCALPHA)
            base = int(size) + 3
            for h in range(height):
                t = h / max(1, height)
                w = int(size * (1 - t * 0.7))
                fx = base + int(math.sin((pb / 4.0) * 3 + t * 4) * 2)
                fy = height + 1 - h
                a = int(ab * (1 - t * 0.4))
                if t < 0.3:
                    color = NS.PALETTE["fire_darkest"]
                elif t < 0.55:
                    color = NS.PALETTE["fire_mid"]
                elif t < 0.8:
                    color = NS.PALETTE["fire_bright"]
                else:
                    color = NS.PALETTE["fire_hot"]
                NS._aacircle(spr, (*color, a), (fx, fy), max(1, w))
            NS._aacircle(spr, (*NS.PALETTE["fire_glow"], ab),
                         (base, height + 1 - height // 3), size // 2)
            NS._aacircle(spr, (*NS.PALETTE["fire_white"], ab),
                         (base, height + 1 - height // 4), max(1, size // 4))
            NS._flame_cache[key] = spr
        surface.blit(spr, (cx - (spr.get_width() // 2), cy - (height + 1)))

    _PILLAR_CACHE = {}

    def _draw_fire_pillar(surface, cx, cy, height, width, phase):
        """Kolom api vertikal ter-cache per (height, width, phase-bucket).

        Pengganti tumpukan aacircle ber-alpha per frame (hot spot skill
        R). Sway sub-piksel dikunci ke 6 bucket fase; gerak besar
        (tinggi pilar tumbuh/susut) tetap kontinu karena height masuk
        kunci cache setelah dikuantisasi 4 px.
        """
        NS = _NS_razak
        P = NS.PALETTE
        height = max(4, int(height))
        width = max(2, int(width))
        hq = (height // 4) * 4
        pb = int(phase * 3) % 6
        key = (hq, width, pb)
        spr = NS._PILLAR_CACHE.get(key)
        if spr is None:
            w_s = width * 2 + 8
            spr = pygame.Surface((w_s, hq + 6), pygame.SRCALPHA)
            base_x = w_s // 2
            for h in range(0, hq, 2):
                t = h / max(1, hq)
                w = max(1, int(width * (1 - t * 0.5)))
                fxp = base_x + int(math.sin(pb * 1.05 + h * 0.3) * 2)
                fyp = hq + 2 - h
                alpha = int(245 * (1 - t * 0.3))
                if t < 0.25:
                    color = P["fire_darkest"]
                elif t < 0.5:
                    color = P["fire_mid"]
                elif t < 0.75:
                    color = P["fire_bright"]
                else:
                    color = P["fire_hot"]
                pygame.draw.circle(spr, (*color, alpha), (fxp, fyp), w)
            if len(NS._PILLAR_CACHE) > 96:
                NS._PILLAR_CACHE.clear()
            NS._PILLAR_CACHE[key] = spr
        surface.blit(spr, (int(cx) - spr.get_width() // 2,
                           int(cy) + 2 - spr.get_height()))

    def _draw_ember(surface, cx, cy, size=2, alpha=255):
        NS = _NS_razak
        NS._aacircle(surface, (*NS.PALETTE["fire_dark"], alpha), (cx, cy), size + 1)
        NS._aacircle(surface, (*NS.PALETTE["fire_bright"], alpha), (cx, cy), size)
        NS._aacircle(surface, (*NS.PALETTE["fire_hot"], alpha), (cx, cy),
                     max(1, size - 1))
        NS._aacircle(surface, (*NS.PALETTE["fire_glow"], min(255, alpha)),
                     (cx, cy), 1)

    def _draw_fire_ground_patch(surface, cx, cy, radius, phase, alpha=255):
        """Patch napalm menyala di tanah - scorch decal + api + bara."""
        NS = _NS_razak
        # alas gosong ter-cache (menempel di tanah, bukan overlay UI)
        NS._ground_scorch(surface, cx, cy, int(radius * 1.15),
                          NS.PALETTE["fire_darkest"],
                          NS.PALETTE["shadow_deep"],
                          int(alpha * 0.85), seed=3)
        # kolam bara: wash zona pekat di tepi
        NS._zone_fill(surface, cx, cy, radius, NS.PALETTE["fire_dark"],
                      int(alpha * 0.5), edge_bias=2.4)
        # api keliling
        flame_count = max(3, int(radius) // 5)
        for i in range(flame_count):
            angle = i * math.pi * 2 / flame_count + phase * 0.3
            r = radius - 4
            fx = cx + int(math.cos(angle) * r)
            fy = cy + int(math.sin(angle) * r // 3)
            size = 3 + (i % 3)
            NS._draw_flame(surface, fx, fy, size, phase + i, alpha=alpha)
        # bara kecil yang naik (deterministik)
        for i in range(4):
            t = (phase * 0.5 + NS._hash01(i * 9)) % 1.0
            ex = cx + int((NS._hash01(i * 5) - 0.5) * radius * 1.4)
            ey = cy - int(t * 18)
            ea = int(alpha * (1 - t) * 0.8)
            if ea > 8:
                NS._draw_ember(surface, ex, ey, 1, ea)

    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM
    # ---------------------------------------------------------------------------
    class NapalmProjectile:
        """Sticky napalm - botol molotov berputar dengan busur parabola.

        v2: proyektil SESUAI KARAKTER - botol kaca brass berisi api
        (bukan bola generik): badan botol berputar, sumbu menyala di
        ekor, trail api 2-tone + asap, glint kaca berputar.
        """
        def __init__(self, sx, sy, tx, ty, arc_height=40):
            self.start_x = float(sx)
            self.start_y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.arc_height = arc_height
            self.alive = True
            self.age = 0
            self.max_age = 40
            self.x = float(sx)
            self.y = float(sy)
            self.spin = 0.0
            self.trail = []

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.spin += 0.34
            t = self.age / self.max_age
            if t >= 1.0:
                self.alive = False
                self.x, self.y = self.tx, self.ty
                return
            self.x = self.start_x + (self.tx - self.start_x) * t
            arc = -4 * self.arc_height * t * (1 - t)
            self.y = self.start_y + (self.ty - self.start_y) * t + arc
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 10:
                self.trail.pop(0)

        def draw(self, surface, phase):
            NS = _NS_razak
            # Trail api 2-tone + asap di ekor terjauh
            n = len(self.trail)
            for i, (tx, ty) in enumerate(self.trail):
                k = i / max(1, n - 1)
                alpha = int(40 + k * 150)
                r = max(1, int(2 + k * 4))
                if k < 0.45:            # asap dingin di ujung ekor
                    NS._aacircle(surface, (*NS.PALETTE["smoke_dark"],
                                           int(alpha * 0.7)), (tx, ty), r + 1)
                    NS._aacircle(surface, (*NS.PALETTE["smoke_mid"],
                                           int(alpha * 0.5)), (tx, ty - 1), r)
                else:                   # api panas dekat botol
                    NS._aacircle(surface, (*NS.PALETTE["fire_dark"], alpha),
                                 (tx, ty), r + 1)
                    NS._aacircle(surface, (*NS.PALETTE["fire_bright"], alpha),
                                 (tx, ty), r)
                    NS._aacircle(surface, (*NS.PALETTE["fire_hot"],
                                           int(alpha * 0.8)),
                                 (tx, ty - 1), max(1, r - 2))
            if not self.alive:
                return
            px, py = int(self.x), int(self.y)
            # kilau panas di sekitar botol
            NS._glow(surface, px, py, 16, NS.PALETTE["fire_mid"], 130)
            # badan botol brass berputar (ellipse sumbu spin)
            ca = abs(math.cos(self.spin))
            bw = max(2, int(6 * ca) + 2)
            NS._ellipse(surface, (*NS.PALETTE["shadow_deep"], 200),
                        (px - bw + 1, py - 5 + 1, bw * 2, 10))
            NS._ellipse(surface, NS.PALETTE["brass_dark"],
                        (px - bw, py - 5, bw * 2, 10))
            NS._ellipse(surface, NS.PALETTE["brass_mid"],
                        (px - bw + 1, py - 4, max(1, bw * 2 - 2), 8))
            NS._ellipse(surface, NS.PALETTE["brass_light"],
                        (px - bw + 1, py - 4, max(1, bw * 2 - 3), 4))
            # glint kaca berputar (specular cluster 1-2 px)
            ga = self.spin * 1.7
            gx = px + int(math.cos(ga) * (bw - 1))
            gy = py - 2 + int(math.sin(ga) * 2)
            NS._aacircle(surface, NS.PALETTE["brass_shine"], (gx, gy), 1)
            # sumbu menyala di ekor botol (arah berlawanan gerak)
            dxn = self.tx - self.start_x
            dyn = self.ty - self.start_y
            dd = math.hypot(dxn, dyn) or 1.0
            wx = px - int(dxn / dd * 8)
            wy = py - int(dyn / dd * 8) - 2
            NS._aacircle(surface, (*NS.PALETTE["fire_bright"], 240),
                         (wx, wy), 3)
            NS._aacircle(surface, (*NS.PALETTE["fire_hot"], 255), (wx, wy), 2)
            NS._aacircle(surface, (*NS.PALETTE["fire_white"], 255),
                         (wx, wy - 1), 1)
            # lidah api mengelilingi botol
            for i in range(3):
                angle = self.spin + i * math.pi * 2 / 3
                fx = px + int(math.cos(angle) * 6)
                fy = py + int(math.sin(angle) * 4)
                NS._draw_ember(surface, fx, fy, 2, 220)

    class NapalmPatch:
        """Persistent burning ground patch."""
        def __init__(self, x, y, radius=25, life=90):
            self.x = x
            self.y = y
            self.radius = radius
            self.age = 0
            self.life = life
            self.alive = True

        def update(self):
            self.age += 1
            if self.age >= self.life:
                self.alive = False

        def draw(self, surface, phase):
            t = self.age / self.life
            if t < 0.15:
                r = int(self.radius * (t / 0.15))
                alpha = int(255 * (t / 0.15))
            elif t < 0.7:
                r = self.radius
                alpha = 255
            else:
                r = self.radius
                alpha = int(255 * (1 - (t - 0.7) / 0.3))
            if r <= 0 or alpha <= 0:
                return
            _NS_razak._draw_fire_ground_patch(surface, self.x, self.y, r,
                                              phase, alpha=alpha)

    # ---------------------------------------------------------------------------
    # State management (nama & pola lama dipertahankan)
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_razak_last_x"):
            boss._razak_last_x = boss.x
            boss._razak_last_y = boss.y
            return False
        dx = abs(boss.x - boss._razak_last_x)
        dy = abs(boss.y - boss._razak_last_y)
        boss._razak_last_x = boss.x
        boss._razak_last_y = boss.y
        return dx + dy > 0.3

    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_razak_prev_timer", 0))
        active = bool(getattr(boss, "_razak_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._razak_attack_active = True
            boss._razak_attack_frame = 0
            active = True
        elif active:
            boss._razak_attack_frame = int(getattr(boss, "_razak_attack_frame", 0)) + 1
            if boss._razak_attack_frame > cooldown:
                boss._razak_attack_active = False
                boss._razak_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._razak_attack_active = False
            boss._razak_attack_frame = 0
            active = False

        boss._razak_prev_timer = timer
        boss._razak_attack_progress = (
            min(1.0, getattr(boss, "_razak_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

        # ── v3: delta-time + fase bernama (dipakai state machine FX) ──
        try:
            from heroes import combat_feel as _cf
            boss._razak_dt = float(_cf.frame_dt())
        except Exception:
            boss._razak_dt = 1.0 / 60.0
        if not (0.0 < boss._razak_dt <= 0.05):
            boss._razak_dt = 1.0 / 60.0
        boss._razak_attack_phase = (
            _NS_razak.attack_phase(boss._razak_attack_progress)
            if active else "NONE"
        )

    def attack_phase(progress):
        """Nama fase serangan bernama (ANTICIPATION..RECOVERY)."""
        p = max(0.0, min(1.0, float(progress)))
        for name, a, b in _NS_razak.ATTACK_PHASES:
            if a <= p < b:
                return name
        return "RECOVERY"

    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_razak_projectiles"):
            boss._razak_projectiles = []
        if not hasattr(boss, "_razak_patches"):
            boss._razak_patches = []

        for proj in boss._razak_projectiles:
            proj.update()
            if not proj.alive:
                boss._razak_patches.append(
                    _NS_razak.NapalmPatch(int(proj.x), int(proj.y),
                                          radius=28, life=100))
            proj.draw(surface, phase)
        boss._razak_projectiles = [p for p in boss._razak_projectiles
                                   if p.alive or p.age < 3]

        for patch in boss._razak_patches:
            patch.update()
            patch.draw(surface, phase)
        boss._razak_patches = [p for p in boss._razak_patches if p.alive]

    def _spawn_napalm(boss, sx, sy, tx, ty, arc_height=40):
        """Spawn napalm. Jalur lapisan hidup mengambil alih kalau aktif:
        renderer hanya memicu timing lewat _razak_proj_spawned, lapisan
        hidup yang melempar molotov di koordinat layar (1:1). Kalau
        lapisan hidup tidak ada, molotov v2 lama dipakai (fallback)."""
        if _NS_razak._fx_owned(boss):
            boss._razak_live_proj_window = True
            return
        if not hasattr(boss, "_razak_projectiles"):
            boss._razak_projectiles = []
        boss._razak_projectiles.append(
            _NS_razak.NapalmProjectile(sx, sy, tx, ty, arc_height=arc_height))

    # ===================================================================
    # v3 POSES & GEOMETRI  (satu sumber kebenaran untuk lapisan hidup)
    # ===================================================================
    def _resolve_pose(boss, moving=False):
        """(action, phase, ap) persis sama dengan dispatch draw_razak.

        Murni / tanpa efek samping: boleh dipanggil ulang oleh fungsi
        efek. ``ap`` = progress serangan MENTAH (keyframe _attack_pose
        menginterpolasi sendiri), jadi bilah, trail, dan badan tidak
        mungkin berbeda frame.
        """
        skill = getattr(boss, "active_skill", None)
        attacking = (
            getattr(boss, "_razak_attack_active", False)
            or getattr(boss, "timer", 0)
            > getattr(boss, "attack_cooldown", 45) - 15
        )
        if skill == "e":
            action = "dash"
        elif attacking:
            action = "attack"
        elif moving:
            action = "walk"
        else:
            action = "idle"
        phase = float(getattr(boss, "pulse", 0.0) or 0.0)
        ap = 0.0
        if action == "attack":
            ap = max(0.0, min(1.0, float(
                getattr(boss, "_razak_attack_progress", 0.0) or 0.0)))
        return action, phase, ap

    def _body_offset(action, phase, ap, facing=1):
        """(dx, dy) layar yang dipakai draw_razak_* sebelum _draw_razak_full."""
        f = 1 if facing >= 0 else -1
        if action == "attack":
            pose = _NS_razak._attack_pose(ap)
            bob = int(math.sin(phase * 0.8) * 2)
            lunge = int(pose["lunge"] * _NS_razak.SCALE) * f
            return lunge, bob
        if action == "walk":
            pw = phase * 2.5
            return int(math.sin(pw * 0.5) * 2), int(math.sin(pw * 1.2) * 4)
        if action == "dash":
            return 0, int(math.sin(phase * 1.5) * 2)
        return 0, int(math.sin(phase * 1.2) * 3) - 1

    def _raw_shift(action, phase, ap, facing=1):
        """(lean_f, root_y, tremble, sway) ruang native _draw_razak_full_raw.

        ``lean_f`` SUDAH dikali arah hadap (sama dengan draw), jadi
        pemetaan lokal->layar tinggal menambahkan angka ini apa adanya.
        """
        f = 1 if facing >= 0 else -1
        breath = math.sin(phase * 0.75)
        sway = int(math.sin(phase * 0.6) * 1)
        if action == "attack":
            pose = _NS_razak._attack_pose(ap)
            tremble = 1 if (pose["tremble"] and int(phase * 30) % 2) else 0
            return int(pose["lean"]) * f, int(pose["dip"]), tremble, sway
        if action == "walk":
            return 3 * f, int(breath * 1.6), 0, \
                int(math.sin(phase * 0.6) * 1) + int(math.sin(phase * 2) * 1)
        if action == "dash":
            return 6 * f, int(breath * 1.6), 0, int(math.sin(phase * 0.6) * 1)
        return int(math.sin(phase * 0.5 + 1.1) * 1.5), \
            int(breath * 1.6), 0, sway

    def _local_to_screen(cx, cy, facing, lean_f, root_y, tremble, sway,
                         lx, ly):
        """SATU pemetaan lokal badan -> layar (dipakai FX eksternal).

        Ruang lokal: (0, 0) = jangkar badan _draw_razak_full (x maju,
        y turun, ruang native 1.5x). Fungsi ini menambahkan shift badan
        raw (lean/tremble/root_y/sway) lalu mengalikan SCALE — jadi
        sebuah titik lokal tidak mungkin lepas dari badan.
        """
        k = _NS_razak.SCALE
        return (int(cx + (lx + lean_f + tremble + sway) * k),
                int(cy + (ly + root_y) * k))

    def _local(boss, x, y, action, phase, ap, lx, ly):
        """Ruang lokal badan rig -> piksel surface (dipakai FX eksternal)."""
        facing = getattr(boss, "direction", 1) or 1
        dx, dy = _NS_razak._body_offset(action, phase, ap, facing)
        lean_f, root_y, tremble, sway = _NS_razak._raw_shift(
            action, phase, ap, facing)
        return _NS_razak._local_to_screen(x + dx, y + dy, facing,
                                          lean_f, root_y, tremble, sway,
                                          lx, ly)

    def _machete_grip_local(action, phase, ap, facing=1):
        """Pergelangan tangan depan (grip machete), ruang lokal badan.

        Kembaran matematis dari _draw_goblin_attack_arms: lengan depan
        (keyframe arm_a) relatif titik jangkar badan. x > 0 = arah
        hadap (sudah mengikuti facing), y > 0 = turun.
        """
        f = 1 if facing >= 0 else -1
        if action == "attack":
            pose = _NS_razak._attack_pose(ap)
            arm_a = pose["arm_a"]
            fx = f * 4 + int(math.cos(arm_a)
                             * _NS_razak.MACHETE_ARM_LEN) * f
            fy = -26 + int(math.sin(arm_a) * _NS_razak.MACHETE_ARM_LEN)
            return fx, fy
        # idle/walk/dash: machete istirahat di tangan belakang
        sway_arm = int(math.sin(phase * 0.7) * 1.5)
        return -f * 16, -22 + sway_arm

    def _machete_tip_local(action, phase, ap, facing=1):
        """Ujung bilah machete, ruang lokal badan (kembaran draw)."""
        f = 1 if facing >= 0 else -1
        gx, gy = _NS_razak._machete_grip_local(action, phase, ap, facing)
        if action == "attack":
            pose = _NS_razak._attack_pose(ap)
            blade = pose["arm_a"] + math.pi / 4 * f
            dx = int(math.cos(blade) * _NS_razak.MACHETE_LEN) * f
            dy = int(math.sin(blade) * _NS_razak.MACHETE_LEN)
        else:
            dx = -f * 20
            dy = -9
        return gx + dx, gy + dy

    def _gun_end_local(action, phase, ap, facing=1):
        """Moncong flamethrower, ruang lokal badan (Q/W origin api)."""
        f = 1 if facing >= 0 else -1
        sway_arm = int(math.sin(phase * 0.7) * 1.5)
        if action in ("q_cast", "w_cast"):
            return f * 41, -25
        if action == "attack":
            return f * 8, -22
        return f * 38, -25 + sway_arm

    def _grip_screen(boss, x, y):
        """Grip machete dalam piksel layar (dipakai FX/trail)."""
        action, phase, ap = _NS_razak._resolve_pose(
            boss, bool(getattr(boss, "_razak_moving", False)))
        facing = getattr(boss, "direction", 1) or 1
        lx, ly = _NS_razak._machete_grip_local(action, phase, ap, facing)
        return _NS_razak._local(boss, x, y, action, phase, ap, lx, ly)

    def _tip_screen(boss, x, y):
        """Ujung bilah machete dalam piksel layar (dipakai FX/trail)."""
        action, phase, ap = _NS_razak._resolve_pose(
            boss, bool(getattr(boss, "_razak_moving", False)))
        facing = getattr(boss, "direction", 1) or 1
        lx, ly = _NS_razak._machete_tip_local(action, phase, ap, facing)
        return _NS_razak._local(boss, x, y, action, phase, ap, lx, ly)

    def _gun_end_screen(boss, x, y):
        """Moncong flamethrower dalam piksel layar."""
        action, phase, ap = _NS_razak._resolve_pose(
            boss, bool(getattr(boss, "_razak_moving", False)))
        facing = getattr(boss, "direction", 1) or 1
        lx, ly = _NS_razak._gun_end_local(action, phase, ap, facing)
        return _NS_razak._local(boss, x, y, action, phase, ap, lx, ly)

    def _swing_hitbox(boss, x, y):
        """Rect AABB jendela hit aktif (SWING/IMPACT) untuk debug."""
        action, phase, ap = _NS_razak._resolve_pose(
            boss, bool(getattr(boss, "_razak_moving", False)))
        if action != "attack" or not (0.30 <= ap <= 0.78):
            return None
        facing = getattr(boss, "direction", 1) or 1
        gx, gy = _NS_razak._grip_screen(boss, x, y)
        tx, ty = _NS_razak._tip_screen(boss, x, y)
        pad = 10
        left = min(gx, tx) - pad
        right = max(gx, tx) + pad
        top = min(gy, ty) - pad
        bottom = max(gy, ty) + pad
        if facing < 0 and right > x:
            right = x if right > x else right
        return pygame.Rect(int(left), int(top), int(right - left),
                           int(bottom - top))

    # ===================================================================
    # LAPISAN FX HIDUP  (heroes/razak_fx.py)
    # ===================================================================
    #: Modul FX layar (diisi malas). False = gagal -> jalur canvas.
    _LIVE_MOD = None

    def _live_module():
        """Muat ``heroes.razak_fx`` sekali; None kalau tidak tersedia."""
        NS = _NS_razak
        if NS._LIVE_MOD is None:
            try:
                from heroes import razak_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "RAZAK_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    def live_fx_ready():
        """True kalau lapisan hidup Razak bisa dipakai (dipakai tooling)."""
        return _NS_razak._live_module() is not None

    def _live_fx(boss, surface, x, y, want_draw, portrait):
        """Lapisan hidup untuk unit ini. Return ``(mod, owned)``.

        ``want_draw`` True pada jalur BOSS (draw tiap frame, tanpa cache
        sprite): lapisan digambar langsung dari sini. Pada jalur HERO
        penggambaran dilakukan heroes/__init__.py via _LIVE_FX_HEROES,
        jadi di sini hanya dipasang penanda "diambil alih".
        """
        NS = _NS_razak
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

    def _fx_owned(boss):
        """True kalau lapisan hidup sudah mengambil alih efek unit ini."""
        mod = _NS_razak._live_module()
        if mod is None:
            return False
        try:
            return bool(mod.owns(boss))
        except Exception:
            return False


    # ===================================================================
    # MAIN ENTRY
    # ===================================================================
    def draw_razak(surface, boss, x, y):
        """Entry point Boss.draw() sekaligus heroes.render_hero().

        Urutan lapisan: aura panas & patch tanah -> telegraph skill ->
        badan (rig native 1.5x -> SCALE -> selout -> lighting) ->
        proyektil -> FX skill foreground. Semua FX skill world-space
        lewat `_fx_scale`.
        """
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_razak._detect_moving(boss)
        _NS_razak._update_attack_anim(boss)
        boss._razak_moving = moving
        portrait = bool(getattr(boss, "_portrait_hd", False))
        in_cache = bool(getattr(boss, "_skip_renderer_projectiles", False))

        attacking = (
            getattr(boss, "_razak_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 45) - 15
        )

        # ── Lapisan hidup (heroes/razak_fx.py). Jalur boss digambar
        #    tiap frame dari sini; jalur lane (render_hero) dipicu
        #    heroes/__init__.py supaya tetap 60 fps walau sprite cache.
        hero_lane = hasattr(boss, "_render_scale")
        live, owned = _NS_razak._live_fx(boss, surface, x, y,
                                         not hero_lane, portrait)

        # ---------- Background layers ----------
        if not portrait:
            _NS_razak._draw_fire_aura(surface, x, y, pulse, active_skill)

            # Ground patches (behind character). Saat render ke canvas
            # cache hero, patch TIDAK digambar supaya tidak terpanggang
            # beku di sekitar sprite (lihat _park_renderer_fx). Patch
            # burnout diambil alih lapisan hidup -> cukup sekali.
            if not owned and not in_cache and hasattr(boss, "_razak_patches"):
                for patch in boss._razak_patches:
                    patch.draw(surface, pulse)

            # ---------- Skill ground telegraph ----------
            if active_skill == "q":
                _NS_razak._draw_napalm_ground(surface, boss, x, y,
                                              skill_timer, pulse)
            elif active_skill == "w":
                _NS_razak._draw_flamebreak_ground(surface, boss, x, y,
                                                  skill_timer, pulse)
            elif active_skill == "e":
                _NS_razak._draw_firefly_ground(surface, boss, x, y,
                                               skill_timer, pulse)
            elif active_skill == "r":
                _NS_razak._draw_firestorm_ground(surface, boss, x, y,
                                                 skill_timer, pulse)

            # AKTIVASI: gelombang kejut + bintang (12 frame pertama).
            # Saat lapisan hidup mengambil alih, shockwave digambar di
            # sana (SkillFX) supaya tidak dobel & tetap 60 fps.
            if not owned and active_skill in ("q", "w", "e", "r"):
                dur = _NS_razak.SKILL_DUR[active_skill]
                age = dur - skill_timer
                if 0 <= age < 12:
                    _NS_razak._draw_shockwave(
                        surface, x, y + _NS_razak.GROUND_DY, age, 12,
                        _NS_razak.PALETTE["fire_hot"],
                        _NS_razak.PALETTE["fire_glow"],
                        fs=_NS_razak._fx_scale(boss))

        # ORIGINAL-MAX hurt flash: badan dibanjiri putih-hangat,
        # bayangan tanah TIDAK ikut menyala.
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        _tgt, _tx, _ty = surface, x, y
        if flash > 0:
            B = _NS_razak
            if B._flash_buf is None:
                B._flash_buf = pygame.Surface((240, 260), pygame.SRCALPHA)
            B._flash_buf.fill((0, 0, 0, 0))
            B._record_shadow = []
            _tgt, _tx, _ty = B._flash_buf, 120, 135

        # ---------- Character ----------
        if active_skill == "e":
            _NS_razak._draw_razak_dashing(_tgt, boss, _tx, _ty, skill_timer,
                                          pulse)
        elif attacking:
            _NS_razak._draw_razak_attack(_tgt, boss, _tx, _ty)
        elif moving:
            _NS_razak._draw_razak_walk(_tgt, boss, _tx, _ty)
        else:
            _NS_razak._draw_razak_idle(_tgt, boss, _tx, _ty)

        if flash > 0:
            B = _NS_razak
            surface.blit(B._flash_buf, (x - _tx, y - _ty))
            w = int(235 * min(1.0, flash / 8.0))
            m = pygame.mask.from_surface(B._flash_buf, 50)
            wht = m.to_surface(setcolor=(w, int(w * 0.9), int(w * 0.8), 255),
                               unsetcolor=(0, 0, 0, 0))
            for rect in (B._record_shadow or ()):
                wht.fill((0, 0, 0, 0), rect)
            surface.blit(wht, (x - _tx, y - _ty),
                         special_flags=pygame.BLEND_RGB_ADD)
            B._record_shadow = None

        # ---------- Projectiles ----------
        # Mojotov v2 tetap dipakai sebagai fallback; lapisan hidup
        # memakai sistem proyektil sendiri (spawn_napalm sudah dialihkan).
        if not owned:
            _NS_razak._manage_projectiles_no_patches(boss, surface, pulse)

        # ---------- Foreground skill effects ----------
        # Saat lapisan hidup mengambil alih, foreground skill digambar
        # di sana (SkillFX) - lebih kaya + tidak terikat kuantisasi cache.
        if not portrait and not owned:
            if active_skill == "q":
                _NS_razak._draw_sticky_napalm(surface, boss, x, y,
                                              skill_timer, pulse)
            elif active_skill == "w":
                _NS_razak._draw_flamebreak(surface, boss, x, y,
                                           skill_timer, pulse)
            elif active_skill == "r":
                _NS_razak._draw_firestorm(surface, boss, x, y,
                                          skill_timer, pulse)

        # ---------- Lapisan hidup bagian ATAS + debug ----------
        if live is not None:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass

    def _draw_shockwave(surface, x, y, age, total, c1, c2, fs=1.0):
        """Gelombang kejut aktivasi skill - 12 frame pertama.

        World-space: radius dikalikan ``fs`` (= 1/_render_scale) supaya
        ukurannya DI LAYAR setara boss asli.
        """
        t = age / float(total)
        if t >= 1.0:
            return
        P = _NS_razak.PALETTE
        ease = 1 - (1 - t) ** 2
        r = int((14 + ease * 58) * fs)
        a = _NS_razak._alpha(235 * (1 - t))
        _NS_razak._ground_ring(surface, x, y, r, c1, c2, a,
                               thickness=max(1.5, 5 - ease * 3.5),
                               softness=10)
        _NS_razak._ground_ring(surface, x, y, int(r * 0.72), c2, P["white"],
                               int(a * 0.55),
                               thickness=max(1.0, 3 - ease * 2), softness=7)
        _NS_razak._glow(surface, x, y, max(6, int(r * 0.5)), c1,
                        int(a * 0.75 * (1 - ease * 0.6)))
        _NS_razak._spark_star(surface, x, y, int(20 * fs), c2, a,
                              spikes=8, rot=t * 2.2, core=P["white"])

    def _manage_projectiles_no_patches(boss, surface, phase):
        """Proyektil digambar di sini; patch dirawat terpisah."""
        if not hasattr(boss, "_razak_projectiles"):
            boss._razak_projectiles = []
        if not hasattr(boss, "_razak_patches"):
            boss._razak_patches = []

        for proj in boss._razak_projectiles:
            proj.update()
            if not proj.alive and proj.age > 0:
                boss._razak_patches.append(
                    _NS_razak.NapalmPatch(int(proj.tx), int(proj.ty),
                                          radius=30, life=100))
                proj.age = -1  # prevent re-spawn
            if proj.age >= 0:
                proj.draw(surface, phase)
        boss._razak_projectiles = [p for p in boss._razak_projectiles
                                   if p.alive]

        for patch in boss._razak_patches:
            patch.update()
        boss._razak_patches = [p for p in boss._razak_patches if p.alive]
    # ===================================================================
    # POSE MODES  (jangkar tanah = +GROUND_DY; ground FX mengikuti)
    # ===================================================================
    def _draw_razak_idle(surface, boss, x, y):
        phase = float(getattr(boss, "pulse", 0.0))
        # hover bob mengikuti wing-beat (downstroke mengangkat badan)
        flap = math.sin(phase * 1.2)
        bob = int(flap * 3) - 1
        portrait = bool(getattr(boss, "_portrait_hd", False))
        if not portrait:
            _NS_razak._draw_shadow(surface, x, y + _NS_razak.GROUND_DY,
                                   lift=max(0, -int(flap * 2)))
            _NS_razak._draw_fire_wisps(surface, x, y + 36, phase)
        _NS_razak._draw_razak_full(surface, x, y + bob,
                                   getattr(boss, "direction", 1), phase,
                                   "idle", boss=boss)

    def _draw_razak_walk(surface, boss, x, y):
        phase = float(getattr(boss, "pulse", 0.0)) * 2.5
        flap = math.sin(phase * 1.2)
        bob = int(flap * 4)
        sway = int(math.sin(phase * 0.5) * 2)
        portrait = bool(getattr(boss, "_portrait_hd", False))
        if not portrait:
            _NS_razak._draw_shadow(surface, x + sway,
                                   y + _NS_razak.GROUND_DY,
                                   lift=max(0, -int(flap * 2)))
            _NS_razak._draw_fire_wisps(surface, x + sway, y + 36, phase,
                                       trail=True,
                                       facing=getattr(boss, "direction", 1))
        _NS_razak._draw_razak_full(surface, x + sway, y + bob,
                                   getattr(boss, "direction", 1), phase,
                                   "walk", boss=boss)

    def _draw_razak_attack(surface, boss, x, y):
        progress = getattr(boss, "_razak_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        phase = float(getattr(boss, "pulse", 0.0))
        facing = getattr(boss, "direction", 1)
        pose = _NS_razak._attack_pose(progress)
        bob = int(math.sin(phase * 0.8) * 2)
        lunge = int(pose["lunge"] * _NS_razak.SCALE) * facing

        # ─── Fireball serangan biasa (unit RANGED) ───
        # Spawn molotov kecil di puncak ayunan, pola boss ranged lain.
        if 0.34 < progress < 0.46 and not getattr(
                boss, "_razak_proj_spawned", False):
            tx, ty = _NS_razak._target_position(boss, x, y)
            sx = x + 20 * facing + lunge
            sy = y + bob - 6
            _NS_razak._spawn_napalm(boss, sx, sy, tx, ty, arc_height=22)
            boss._razak_proj_spawned = True
        if progress < 0.12 or progress > 0.9:
            boss._razak_proj_spawned = False

        portrait = bool(getattr(boss, "_portrait_hd", False))
        if not portrait:
            _NS_razak._draw_shadow(surface, x + lunge,
                                   y + _NS_razak.GROUND_DY)
            _NS_razak._draw_fire_wisps(surface, x + lunge, y + 36, phase,
                                       intense=True)
        _NS_razak._draw_razak_full(surface, x + lunge, y + bob, facing,
                                   phase, "attack", progress, boss=boss)
        # Pita ayunan di-canvas HANYA kalau lapisan hidup tidak mengambil
        # alih: trail layar memakai histori posisi bilah yang sebenarnya
        # (lihat heroes/razak_fx.SwingTrail).
        if not _NS_razak._fx_owned(boss):
            _NS_razak._draw_machete_swing_arc(surface, x + lunge, y + bob,
                                              facing, progress)

    def _draw_razak_dashing(surface, boss, x, y, timer, phase):
        """Firefly dash - bat melesat dengan trail api + afterimage."""
        bob = int(math.sin(phase * 1.5) * 2)
        facing = getattr(boss, "direction", 1)
        portrait = bool(getattr(boss, "_portrait_hd", False))
        if not portrait:
            _NS_razak._draw_shadow(surface, x, y + _NS_razak.GROUND_DY,
                                   lift=4)
            _NS_razak._draw_fire_wisps(surface, x, y + 36, phase,
                                       intense=True)

        # Motion blur belakang: SATU ghost dirender lalu di-blit 4x
        # dengan alpha menurun (4x lebih murah dari me-render ulang rig).
        temp = pygame.Surface((200, 200), pygame.SRCALPHA)
        _NS_razak._draw_razak_dash_ghost(temp, 100, 100, facing, phase)
        for i in range(4):
            offset = (i + 1) * 9 * -facing
            temp.set_alpha(int(140 - i * 30))
            surface.blit(temp, (x + offset - 100, y + bob - 100))
        temp.set_alpha(255)

        # bara terlempar di belakang jalur dash
        for i in range(5):
            ex = x - (14 + i * 13) * facing
            ey = y + bob + int(math.sin(phase * 2 + i * 1.7) * 8)
            ea = max(0, 190 - i * 36)
            _NS_razak._draw_ember(surface, ex, ey, max(1, 3 - i // 2), ea)

        _NS_razak._draw_razak_full(surface, x, y + bob, facing, phase,
                                   "dash", boss=boss)

    def _draw_razak_dash_ghost(surface, cx, cy, facing, phase):
        """Afterimage dash: rig native diturunkan ke SCALE tanpa pass."""
        NS = _NS_razak
        buf = pygame.Surface((NS.RIG_W, NS.RIG_H), pygame.SRCALPHA)
        NS._draw_razak_full_raw(buf, NS.RIG_OX, NS.RIG_OY, facing, phase,
                                "dash")
        k = NS.SCALE
        tw = max(1, int(buf.get_width() * k))
        th = max(1, int(buf.get_height() * k))
        small = pygame.transform.smoothscale(buf, (tw, th))
        surface.blit(small, (cx - int(NS.RIG_OX * k),
                             cy - int(NS.RIG_OY * k)))

    # ===================================================================
    # ATTACK TIMELINE (7 keyframe + frame IMPACT tersendiri)
    # ===================================================================
    def _attack_pose(ap):
        """Interpolasi keyframe serang -> dict pose.

        Keyframe: (progress, lunge, lean, dip, arm_a, flare, tremble)
          0.14  wind-up   : machete ditarik ke belakang atas, badan mundur
          0.30  tension   : gemetar 1 px, syal & ekor tertinggal
          0.48  strike    : ayunan tercepat (smear sabit api aktif)
          0.54  IMPACT    : squash + bintang + shockwave kecil
          0.72  follow    : rebound overshoot
          1.00  recover   : kembali ke pose istirahat
        """
        keys = (
            (0.00, 0.0,  0.0, 0.0, -1.30, 1.00, 0),
            (0.14, -3.0, -5.0, 2.0, -2.10, 1.12, 0),
            (0.30, -4.0, -6.0, 3.0, -2.35, 1.20, 1),
            (0.48, 7.0,  6.0, -2.0, 0.85, 1.08, 0),
            (0.54, 9.0,  8.0, 3.0,  1.25, 1.02, 0),
            (0.72, 3.0,  3.0, 1.0,  0.55, 1.00, 0),
            (1.00, 0.0,  0.0, 0.0, -1.30, 1.00, 0),
        )
        ap = max(0.0, min(1.0, ap))
        for i in range(len(keys) - 1):
            k0, k1 = keys[i], keys[i + 1]
            if k0[0] <= ap <= k1[0]:
                span = max(1e-6, k1[0] - k0[0])
                t = (ap - k0[0]) / span
                t = t * t * (3 - 2 * t)          # smoothstep
                vals = tuple(a + (b - a) * t for a, b in zip(k0[1:6], k1[1:6]))
                return {
                    "lunge": vals[0], "lean": vals[1], "dip": vals[2],
                    "arm_a": vals[3], "flare": vals[4],
                    "tremble": 1 if (k0[6] and t < 0.9) else 0,
                    "impact": 1.0 - min(1.0, abs(ap - 0.54) / 0.10),
                }
        return {"lunge": 0.0, "lean": 0.0, "dip": 0.0, "arm_a": -1.30,
                "flare": 1.0, "tremble": 0, "impact": 0.0}

    # ===================================================================
    # FULL COMPOSITE
    # ===================================================================
    def _draw_razak_full_raw(surface, cx, cy, facing, phase, action,
                             attack_progress=0, boss=None):
        """Rig masterwork v2 - bat api + goblin rider, 100% prosedural.

        Semua koordinat lokal ~1.5x versi lama: (0, 0) = jangkar pusat
        badan bat, x maju (facing), y ke bawah. Helm goblin memuncak
        di -72, cakar bat +40, ujung sayap +-62.

        ``boss`` dipakai hanya untuk supresi FX impact saat lapisan
        hidup mengambil alih (None = jalur canvas penuh).
        """
        f = 1 if facing >= 0 else -1
        attack = action == "attack"
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0
        pose = _NS_razak._attack_pose(ap) if attack else None
        breath = math.sin(phase * 0.75)

        # ═══ gerak badan: wing-beat bob + lean + inersia ═══
        if action == "walk":
            flap_speed = 2.5
            lean = 3 * f
            tail_lag = math.sin(phase + 2.2) * 0.35
            scarf_lag = 4.5
        elif action == "dash":
            flap_speed = 4.0
            lean = 6 * f
            tail_lag = 0.8
            scarf_lag = 9.0
        elif attack:
            flap_speed = 1.6
            lean = int(pose["lean"]) * f
            tail_lag = -pose["lean"] * 0.05
            scarf_lag = -pose["lean"] * 0.7
        else:
            flap_speed = 1.2
            lean = int(math.sin(phase * 0.5 + 1.1) * 1.5)
            tail_lag = math.sin(phase * 0.6) * 0.18
            scarf_lag = math.sin(phase * 0.55) * 2.2

        flap = math.sin(phase * flap_speed) * (0.5 if action == "dash"
                                               else 0.35)
        tremble = 0
        if attack and pose["tremble"]:
            tremble = 1 if int(phase * 30) % 2 else 0
        root_y = int(pose["dip"]) if attack else int(breath * 1.6)

        ox = int(cx) + lean + tremble
        oy = int(cy) + root_y

        # ═══ lapisan belakang -> depan ═══
        # sayap belakang (kanan-layar jauh)
        _NS_razak._draw_bat_wings(surface, ox, oy, f, phase, action,
                                  flap=flap)
        # ekor dengan inersia
        _NS_razak._draw_bat_tail(surface, ox, oy + 8, f, phase, tail_lag)
        # badan bat + kaki/cakar
        _NS_razak._draw_bat_body(surface, ox, oy + 7, f, phase)
        # kepala naga bat
        _NS_razak._draw_bat_head(surface, ox + 27 * f, oy + 4, f, phase)
        # rider goblin di punggung
        _NS_razak._draw_goblin_rider(surface, ox - 3 * f, oy - 18, f, phase,
                                     action, ap, scarf_lag=scarf_lag,
                                     boss=boss)
        # sayap depan overlay saat serang
        if attack:
            _NS_razak._draw_bat_wings_front(surface, ox, oy, f, phase)

    def _draw_razak_full(surface, cx, cy, facing, phase, action,
                         attack_progress=0, boss=None):
        """Komposit badan: rig native (1.5x) -> buffer -> turun ke SCALE ->
        outline siluet gelap 1 px -> pass cahaya (rim/shade) -> blit.

        Outline & lighting dikerjakan SETELAH penskalaan supaya tetap
        setebal 1 px di layar (konvensi _finish_hd_sprite).
        """
        NS = _NS_razak
        if NS._body_buf is None:
            NS._body_buf = pygame.Surface((NS.RIG_W, NS.RIG_H),
                                          pygame.SRCALPHA)
        buf = NS._body_buf
        buf.fill((0, 0, 0, 0))
        NS._draw_razak_full_raw(buf, NS.RIG_OX, NS.RIG_OY, facing, phase,
                                action, attack_progress, boss=boss)
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
        if _lighting is not None:
            _lighting.apply_to_rig(sub, rim_add=(38, 26, 18), shade_mul=168)
        surface.blit(sub, (ox, oy))
    # ===================================================================
    # ANATOMI BAT MOUNT (rig native 1.5x)
    # ===================================================================
    def _draw_bat_wings(surface, cx, cy, facing, phase, action, flap=None):
        """Sayap membran bat: 4-band + tulang jari + scallop bergerigi.

        Tepi bawah membran digerigi `_tuft_points` (siluet pixel-art),
        downstroke memicu gust kecil di bawah sayap.
        """
        NS = _NS_razak
        P = NS.PALETTE
        if flap is None:
            flap = math.sin(phase * (2.5 if action == "walk" else 1.2)) * 0.35
            if action == "dash":
                flap = math.sin(phase * 4) * 0.5
        fs = math.sin(flap * 3.0)          # -1..1 posisi kepakan

        for side in (-1, 1):
            base_x = cx + side * 12
            base_y = cy - 4
            # sendi tengah & ujung mengikuti kepakan
            tip_x = cx + side * (48 + int(math.cos(flap) * 9))
            tip_y = cy - 24 + int(fs * 14)
            mid_x = cx + side * 36
            mid_y = cy - 10 + int(fs * 9)
            low_x = cx + side * 30
            low_y = cy + 17 + int(fs * 5)

            # spine tepi bawah membran -> scallop bergerigi
            spine = [(tip_x, tip_y),
                     (cx + side * 44, cy - 5 + int(fs * 7)),
                     (mid_x, mid_y + 12),
                     (cx + side * 40, cy + 6 + int(fs * 6)),
                     (low_x, low_y),
                     (cx + side * 6, cy + 12)]
            edge = NS._tuft_points(spine, depth=3.5, min_len=8.0,
                                   seed=7 + side)
            shape = [(base_x, base_y)] + edge

            # selout: salinan shadow_deep di sisi bayangan (kanan-bawah)
            NS._poly(surface, P["shadow_deep"],
                     [(p[0] + 2, p[1] + 2) for p in shape])
            # membran 4-band
            NS._poly(surface, P["wing_darkest"], shape)
            inner = [(base_x + side, base_y + 2)] + \
                    [(cx + (p[0] - cx) * 0.93, cy + (p[1] - cy) * 0.93)
                     for p in edge]
            NS._poly(surface, P["wing_dark"], inner)
            inner2 = [(base_x + side * 2, base_y + 3)] + \
                     [(cx + (p[0] - cx) * 0.82, cy + (p[1] - cy) * 0.82)
                      for p in edge[::2]]
            if len(inner2) >= 3:
                NS._poly(surface, P["wing_mid"], inner2)
            # band terang hanya di sisi cahaya (kiri-atas)
            lit = [(base_x, base_y),
                   (tip_x - side * 4, tip_y + 3),
                   (mid_x - side * 3, mid_y + 2),
                   (base_x + side * 4, base_y + 6)]
            NS._poly(surface, P["wing_light"], lit)

            # dither band transisi membran (bertahan setelah downscale)
            dith = [((base_x + tip_x) / 2 + side * k * 3,
                     (base_y + tip_y) / 2 + 6 + (k % 3))
                    for k in range(6)]
            NS._dither_dots(surface, P["wing_high"], dith, alpha=110)

            # tulang jari (3 strut) + sendi
            for jx, jy in ((tip_x, tip_y), (mid_x, mid_y), (low_x, low_y)):
                NS._aaline(surface, P["wing_darkest"],
                           (base_x, base_y), (jx, jy), 3)
                NS._aaline(surface, P["bat_dark"],
                           (base_x, base_y), (jx, jy), 1)
            NS._aacircle(surface, P["bat_dark"], (base_x, base_y), 3)
            NS._aacircle(surface, P["bat_mid"], (base_x - 1, base_y - 1), 2)

            # cakar ujung sayap ivory 3-band
            NS._poly(surface, P["bone_dark"], [
                (tip_x, tip_y),
                (tip_x + side * 5, tip_y - 4),
                (tip_x + side * 2, tip_y + 2),
            ])
            NS._poly(surface, P["bone_light"], [
                (tip_x + side, tip_y - 1),
                (tip_x + side * 4, tip_y - 3),
                (tip_x + side * 2, tip_y + 1),
            ])
            NS._aacircle(surface, P["bone_shine"],
                         (tip_x + side * 3, tip_y - 2), 1)
            # v4: fire-tipped claws + ember vein along trailing membrane
            flick = 0.55 + 0.45 * abs(math.sin(phase * 3.4 + side))
            NS._aacircle(surface, (*P["fire_bright"], int(170 * flick)),
                         (tip_x, tip_y), 3)
            NS._aacircle(surface, (*P["fire_hot"], int(210 * flick)),
                         (tip_x, tip_y), 2)
            NS._aacircle(surface, (*P["fire_glow"], 240),
                         (tip_x, tip_y - 1), 1)
            for k in range(3):
                t = 0.28 + k * 0.22
                fx = int(base_x + (low_x - base_x) * t)
                fy = int(base_y + (low_y - base_y) * t)
                NS._aacircle(surface, (*P["fire_mid"], int(110 * flick)),
                             (fx, fy), 2)

    def _draw_bat_wings_front(surface, cx, cy, facing, phase):
        """Overlay highlight sayap saat serang (rim tipis sisi cahaya)."""
        NS = _NS_razak
        for side in (-1, 1):
            NS._aaline(surface, NS.PALETTE["wing_light"],
                       (cx + side * 14, cy - 2),
                       (cx + side * 38, cy - 13), 2)
            NS._aaline(surface, NS.PALETTE["wing_high"],
                       (cx + side * 20, cy - 6),
                       (cx + side * 34, cy - 12), 1)

    def _draw_bat_tail(surface, cx, cy, facing, phase, lag=0.0):
        """Ekor berujung panah dengan inersia (secondary motion)."""
        NS = _NS_razak
        P = NS.PALETTE
        f = facing
        # spine ekor 3 segmen; segmen jauh makin tertinggal (lag)
        sx, sy = cx - f * 16, cy + 2
        seg = []
        ang = math.pi if f > 0 else 0.0
        for i in range(3):
            ang += (0.22 + lag * (i + 1) * 0.4) * (1 if f > 0 else -1) * 0.6
            ln = 9 - i
            nx = seg[-1][0] if seg else sx
            ny = seg[-1][1] if seg else sy
            seg.append((nx + math.cos(ang) * ln,
                        ny + math.sin(ang) * ln * 0.5 + 1.5))
        prev = (sx, sy)
        for i, p in enumerate(seg):
            NS._aaline(surface, P["shadow_deep"],
                       (prev[0] + 1, prev[1] + 2), (p[0] + 1, p[1] + 2),
                       6 - i)
            NS._aaline(surface, P["bat_darkest"], prev, p, 5 - i)
            NS._aaline(surface, P["bat_dark"], prev, p, max(1, 3 - i))
            prev = p
        tex, tey = seg[-1]
        # ujung panah 3-band
        NS._poly(surface, P["bat_darkest"], [
            (tex, tey - 4), (tex - f * 7, tey), (tex, tey + 4)])
        NS._poly(surface, P["bat_mid"], [
            (tex, tey - 2), (tex - f * 5, tey), (tex, tey + 2)])
        NS._aacircle(surface, P["bat_light"], (int(tex - f * 2), int(tey)), 1)
        # v4: fire-tipped tail
        flick = 0.6 + 0.4 * abs(math.sin(phase * 3.7))
        NS._aacircle(surface, (*P["fire_bright"], int(190 * flick)),
                     (int(tex), int(tey)), 3)
        NS._aacircle(surface, (*P["fire_hot"], int(220 * flick)),
                     (int(tex), int(tey)), 2)
        NS._aacircle(surface, (*P["fire_glow"], 255),
                     (int(tex - f), int(tey - 1)), 1)

    def _draw_bat_body(surface, cx, cy, facing, phase):
        """Badan bat merah: 5-band + sisik punggung + perut dither + cakar."""
        NS = _NS_razak
        P = NS.PALETTE
        breath = math.sin(phase * 0.75) * 1.2

        # selout bayangan
        NS._ellipse(surface, P["shadow_deep"], (cx - 21, cy - 6, 47, 29))
        # badan 5-band (bayangan ungu -> highlight oranye, key kiri-atas)
        NS._ellipse(surface, P["bat_darkest"], (cx - 21, cy - 8, 45, 27))
        NS._ellipse(surface, P["bat_dark"], (cx - 19, cy - 7, 41, 24))
        NS._ellipse(surface, P["bat_mid"], (cx - 16, cy - 6, 35, 19 + breath))
        NS._ellipse(surface, P["bat_light"], (cx - 13, cy - 7, 27, 12))
        NS._ellipse(surface, P["bat_high"], (cx - 10, cy - 7, 18, 6))
        # specular cluster 2 px di punggung sisi cahaya
        NS._aacircle(surface, P["bat_shine"], (cx - 7, cy - 5), 1)
        NS._aacircle(surface, P["bat_shine"], (cx - 4, cy - 6), 1)
        NS._aacircle(surface, P["bat_rim"], (cx - 6, cy - 7), 1)

        # perut terang + dither band transisi
        NS._ellipse(surface, P["belly_dark"], (cx - 12, cy + 9, 27, 9))
        NS._ellipse(surface, P["belly_mid"], (cx - 9, cy + 10, 21, 6))
        NS._ellipse(surface, P["belly_light"], (cx - 6, cy + 11, 15, 3))
        NS._dither_dots(surface, P["belly_light"],
                        [(cx - 10 + i * 4, cy + 8 + (i % 2)) for i in range(6)],
                        alpha=120)

        # sisik/duri punggung bergerigi (siluet)
        for i, sx_off in enumerate((-12, -6, 0, 6, 11)):
            h = 6 + (i % 2) * 2
            NS._poly(surface, P["bat_darkest"], [
                (cx + sx_off - 2, cy - 6),
                (cx + sx_off + 2, cy - 6),
                (cx + sx_off, cy - 6 - h),
            ])
            NS._poly(surface, P["bat_mid"], [
                (cx + sx_off - 1, cy - 6),
                (cx + sx_off + 1, cy - 6),
                (cx + sx_off, cy - 5 - h),
            ])
            NS._aacircle(surface, P["bat_light"],
                         (cx + sx_off, cy - 4 - h), 1)
            # v4: flame mane along the dorsal ridge
            flick = int(math.sin(phase * 3.2 + i) * 2)
            NS._aacircle(surface, (*P["fire_bright"], 170),
                         (cx + sx_off, cy - 8 - h + flick), 2)
            NS._aacircle(surface, (*P["fire_hot"], 210),
                         (cx + sx_off, cy - 9 - h + flick), 1)

        # kaki tuck + cakar 3 jari
        for side in (-1, 1):
            lx = cx + side * 10
            ly = cy + 16
            NS._aacircle(surface, P["shadow_deep"], (lx + 1, ly + 1), 5)
            NS._aacircle(surface, P["bat_darkest"], (lx, ly), 4)
            NS._aacircle(surface, P["bat_dark"], (lx - 1, ly - 1), 3)
            NS._aacircle(surface, P["bat_mid"], (lx - 1, ly - 2), 2)
            for c in (-2, 0, 2):
                NS._poly(surface, P["bone_dark"], [
                    (lx + c - 1, ly + 3),
                    (lx + c + 1, ly + 3),
                    (lx + c + side, ly + 7),
                ])
                NS._aacircle(surface, P["bone_light"],
                             (lx + c + side, ly + 6), 1)

    def _draw_bat_head(surface, cx, cy, facing, phase):
        """Kepala naga bat: moncong + taring + 3 tanduk + mata membara."""
        NS = _NS_razak
        P = NS.PALETTE
        f = facing

        # selout
        NS._aacircle(surface, P["shadow_deep"], (cx + 2, cy + 2), 12)
        # tengkorak 5-band
        NS._ellipse(surface, P["bat_darkest"], (cx - 11, cy - 8, 22, 19))
        NS._ellipse(surface, P["bat_dark"], (cx - 10, cy - 7, 20, 16))
        NS._ellipse(surface, P["bat_mid"], (cx - 8, cy - 6, 16, 12))
        NS._ellipse(surface, P["bat_light"], (cx - 7, cy - 6, 12, 7))
        NS._aacircle(surface, P["bat_high"], (cx - 4, cy - 4), 2)
        NS._aacircle(surface, P["bat_rim"], (cx - 5, cy - 5), 1)

        # moncong maju
        snout = [
            (cx, cy - 2),
            (cx + f * 12, cy - 3),
            (cx + f * 15, cy + 1),
            (cx + f * 12, cy + 5),
            (cx, cy + 5),
        ]
        NS._poly(surface, P["shadow_deep"],
                 [(p[0] + 1, p[1] + 2) for p in snout])
        NS._poly(surface, P["bat_darkest"], snout)
        NS._poly(surface, P["bat_dark"], [
            (cx + 1, cy - 1), (cx + f * 11, cy - 2),
            (cx + f * 13, cy + 1), (cx + f * 11, cy + 4), (cx + 1, cy + 4)])
        NS._poly(surface, P["bat_mid"], [
            (cx + 2, cy - 1), (cx + f * 9, cy - 1),
            (cx + f * 12, cy + 1), (cx + f * 9, cy + 3)])
        NS._aaline(surface, P["bat_light"],
                   (cx + 2, cy - 1), (cx + f * 10, cy - 1), 1)

        # lubang hidung + dengus (sniff berkala, deterministik)
        NS._aacircle(surface, P["shadow_deep"], (cx + f * 12, cy - 1), 1)
        sniff = math.sin(phase * 0.9 + 1.0)
        if sniff > 0.86:
            k = (sniff - 0.86) / 0.14
            NS._aacircle(surface, (*P["smoke_mid"], int(120 * k)),
                         (cx + f * (15 + int(k * 4)), cy - 2 - int(k * 3)), 2)

        # rahang bawah + taring ivory 3-band
        NS._poly(surface, P["bat_darkest"], [
            (cx + 1, cy + 5), (cx + f * 11, cy + 5),
            (cx + f * 9, cy + 8), (cx + 1, cy + 8)])
        for tooth_off in (2, 6):
            bx = cx + f * (3 + tooth_off)
            NS._poly(surface, P["bone_dark"], [
                (bx - 1, cy + 4), (bx + 1, cy + 4), (bx + f, cy + 9)])
            NS._poly(surface, P["bone_light"], [
                (bx - 1, cy + 4), (bx, cy + 4), (bx + f, cy + 8)])
            NS._aacircle(surface, P["bone_shine"], (bx, cy + 5), 1)

        # mata membara + blink deterministik (~2.4 dtk)
        blink = math.sin(phase * 0.42 + 0.7) > 0.97
        ex, ey = cx + f * 3, cy - 3
        NS._aacircle(surface, P["shadow_deep"], (ex, ey), 3)
        if blink:
            NS._aaline(surface, P["fire_dark"], (ex - 2, ey), (ex + 2, ey), 2)
        else:
            eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
            NS._aacircle(surface, P["fire_dark"], (ex, ey), 3)
            NS._aacircle(surface, P["fire_bright"], (ex, ey), 2)
            NS._aacircle(surface, P["fire_hot"], (ex, ey),
                         max(1, int(2 * eye_pulse)))
            NS._aacircle(surface, P["fire_glow"], (ex - 1, ey - 1), 1)

        # 3 tanduk/telinga runcing dengan twitch
        tw = 1 if math.sin(phase * 0.36 + 2.0) > 0.94 else 0
        for i, off in enumerate((-5, 0, 5)):
            h = 9 + (i % 2) * 3 + (tw if i == 2 else 0)
            NS._poly(surface, P["shadow_deep"], [
                (cx + off, cy - 6), (cx + off + 3, cy - 6),
                (cx + off + 2, cy - 6 - h)])
            NS._poly(surface, P["bat_darkest"], [
                (cx + off - 1, cy - 6), (cx + off + 2, cy - 6),
                (cx + off + 1, cy - 6 - h)])
            NS._poly(surface, P["bat_mid"], [
                (cx + off, cy - 6), (cx + off + 1, cy - 6),
                (cx + off, cy - 5 - h)])
            NS._aacircle(surface, P["bat_light"],
                         (cx + off + 1, cy - 4 - h), 1)
        # v4: ember crown between the horns
        NS._aacircle(surface, (*P["fire_hot"], 200), (cx, cy - 14), 2)
        NS._aacircle(surface, (*P["fire_glow"], 240), (cx, cy - 15), 1)
    # ===================================================================
    # GOBLIN RIDER (rig native 1.5x)
    # ===================================================================
    def _draw_goblin_rider(surface, cx, cy, facing, phase, action,
                           attack_progress, scarf_lag=0.0, boss=None):
        """Goblin pilot di punggung bat: kaki straddle, torso, kepala,
        tangki bahan bakar, syal berkibar, lengan + senjata."""
        NS = _NS_razak
        sway = int(math.sin(phase * 0.6) * 1)
        if action == "walk":
            sway += int(math.sin(phase * 2) * 1)

        # syal robek berkibar DI BELAKANG badan (inersia scarf_lag)
        NS._draw_goblin_scarf(surface, cx + sway - facing * 6, cy - 8,
                              facing, phase, scarf_lag)

        # kaki straddle
        for side in (-1, 1):
            lx = cx + side * 7
            ly = cy + 15
            NS._rect(surface, NS.PALETTE["shadow_deep"],
                     (lx - 3 + 1, ly + 1, 6, 9), border_radius=1)
            NS._rect(surface, NS.PALETTE["leather_darkest"],
                     (lx - 3, ly, 6, 9), border_radius=1)
            NS._rect(surface, NS.PALETTE["leather_dark"], (lx - 3, ly, 6, 7))
            NS._rect(surface, NS.PALETTE["leather_mid"], (lx - 2, ly + 1, 4, 4))
            NS._rect(surface, NS.PALETTE["leather_light"], (lx - 2, ly + 1, 2, 2))
            # boot + gesper brass
            NS._rect(surface, NS.PALETTE["leather_darkest"],
                     (lx - 4, ly + 9, 9, 6), border_radius=1)
            NS._rect(surface, NS.PALETTE["leather_dark"], (lx - 4, ly + 9, 9, 4))
            NS._rect(surface, NS.PALETTE["leather_mid"], (lx - 3, ly + 10, 6, 2))
            NS._rect(surface, NS.PALETTE["brass_mid"], (lx - 4, ly + 9, 9, 1))
            NS._aacircle(surface, NS.PALETTE["brass_shine"], (lx, ly + 9), 1)

        # tangki bahan bakar (di belakang torso)
        NS._draw_fuel_tanks(surface, cx + sway - facing * 9, cy - 5, phase)

        # torso
        NS._draw_goblin_torso(surface, cx + sway, cy, facing, phase)

        # kepala
        NS._draw_goblin_head(surface, cx + sway, cy - 17, facing, phase)

        # lengan + senjata
        if action == "attack":
            NS._draw_goblin_attack_arms(surface, cx + sway, cy - 5, facing,
                                        phase, attack_progress, boss=boss)
        elif action in ("q_cast", "w_cast"):
            NS._draw_goblin_gun_arms(surface, cx + sway, cy - 5, facing,
                                     phase)
        else:
            NS._draw_goblin_idle_arms(surface, cx + sway, cy - 5, facing,
                                      phase)

    def _draw_goblin_scarf(surface, sx, sy, facing, phase, lag=0.0):
        """Syal pilot robek berkibar - tepi digerigi _tuft_points."""
        NS = _NS_razak
        P = NS.PALETTE
        f = facing
        wave = math.sin(phase * 1.6) * 3 + lag
        spine = [(sx, sy),
                 (sx - f * 8, sy + 2 + wave * 0.4),
                 (sx - f * 16, sy + 5 + wave * 0.8),
                 (sx - f * 23, sy + 9 + wave)]
        edge = NS._tuft_points(spine, depth=3.0, min_len=6.0, seed=11)
        lower = [(p[0], p[1] + 5 + i * 0.3) for i, p in enumerate(spine)]
        shape = edge + lower[::-1]
        if len(shape) >= 3:
            NS._poly(surface, P["shadow_deep"],
                     [(p[0] + 1, p[1] + 2) for p in shape])
            NS._poly(surface, P["fire_dark"], shape)
            inner = [(p[0], p[1] + 1) for p in spine] + \
                    [(p[0], p[1] + 4) for p in spine][::-1]
            NS._poly(surface, P["fire_mid"], inner)
            NS._aaline(surface, P["fire_bright"], spine[0],
                       (spine[1][0], spine[1][1] + 1), 1)

    def _draw_goblin_torso(surface, cx, cy, facing, phase):
        """Torso goblin: kulit hijau 4-band + rompi + strap X ber-jahitan."""
        NS = _NS_razak
        P = NS.PALETTE
        breath = math.sin(phase * 0.75) * 0.8

        # selout
        NS._poly(surface, P["shadow_deep"], [
            (cx - 10 + 2, cy - 8 + 2), (cx + 10 + 2, cy - 8 + 2),
            (cx + 9 + 2, cy + 14 + 2), (cx - 9 + 2, cy + 14 + 2)])
        # kulit hijau 4-band
        NS._poly(surface, P["gob_darkest"], [
            (cx - 10, cy - 8), (cx + 10, cy - 8),
            (cx + 9, cy + 14), (cx - 9, cy + 14)])
        NS._poly(surface, P["gob_dark"], [
            (cx - 9, cy - 7), (cx + 9, cy - 7),
            (cx + 8, cy + 13), (cx - 8, cy + 13)])
        NS._poly(surface, P["gob_mid"], [
            (cx - 7, cy - 6 + breath), (cx + 7, cy - 6 + breath),
            (cx + 6, cy + 10), (cx - 6, cy + 10)])
        NS._poly(surface, P["gob_light"], [
            (cx - 6, cy - 5), (cx + 1, cy - 5),
            (cx, cy + 3), (cx - 5, cy + 3)])
        # specular cluster bahu kiri-atas
        NS._aacircle(surface, P["gob_high"], (cx - 4, cy - 4), 1)
        NS._aacircle(surface, P["gob_shine"], (cx - 5, cy - 5), 1)

        # rompi kulit
        NS._rect(surface, P["leather_darkest"], (cx - 11, cy - 3, 22, 12),
                 border_radius=2)
        NS._rect(surface, P["leather_dark"], (cx - 10, cy - 2, 20, 10),
                 border_radius=1)
        NS._rect(surface, P["leather_mid"], (cx - 9, cy - 1, 18, 5))
        NS._rect(surface, P["leather_light"], (cx - 8, cy, 7, 2))
        # dither transisi rompi
        NS._dither_dots(surface, P["leather_light"],
                        [(cx - 7 + i * 3, cy + 4) for i in range(5)],
                        alpha=110)

        # strap X ber-jahitan
        NS._aaline(surface, P["leather_darkest"], (cx - 9, cy - 4),
                   (cx + 9, cy + 6), 3)
        NS._aaline(surface, P["leather_darkest"], (cx + 9, cy - 4),
                   (cx - 9, cy + 6), 3)
        NS._aaline(surface, P["leather_mid"], (cx - 9, cy - 4),
                   (cx + 9, cy + 6), 1)
        NS._aaline(surface, P["leather_mid"], (cx + 9, cy - 4),
                   (cx - 9, cy + 6), 1)
        # jahitan (dither di sepanjang strap)
        for k in range(4):
            t = 0.2 + k * 0.2
            jx = cx - 9 + int(18 * t)
            jy = cy - 4 + int(10 * t)
            NS._aacircle(surface, (*P["leather_high"], 150), (jx, jy - 1), 1)

        # gesper emas pusat + rivet
        NS._aacircle(surface, P["gold_dark"], (cx, cy + 1), 3)
        NS._aacircle(surface, P["gold_mid"], (cx, cy + 1), 2)
        NS._aacircle(surface, P["gold_light"], (cx - 1, cy), 1)

    def _draw_goblin_head(surface, cx, cy, facing, phase):
        """Kepala goblin: goggles biru signature + helm rivet + telinga."""
        NS = _NS_razak
        P = NS.PALETTE
        f = facing

        # selout
        NS._aacircle(surface, P["shadow_deep"], (cx + 2, cy + 2), 11)
        # tengkorak 4-band
        NS._aacircle(surface, P["gob_darkest"], (cx, cy), 10)
        NS._aacircle(surface, P["gob_dark"], (cx - 1, cy - 1), 9)
        NS._aacircle(surface, P["gob_mid"], (cx - 1, cy - 2), 7)
        NS._aacircle(surface, P["gob_light"], (cx - 3, cy - 4), 4)
        NS._aacircle(surface, P["gob_high"], (cx - 4, cy - 5), 2)

        # telinga panjang runcing (twitch berkala)
        tw = 1 if math.sin(phase * 0.44 + 1.3) > 0.94 else 0
        for side in (-1, 1):
            NS._poly(surface, P["shadow_deep"], [
                (cx + side * 8 + 1, cy - 1 + 1),
                (cx + side * 17 + 1, cy - 6 - (tw if side == f else 0) + 1),
                (cx + side * 10 + 1, cy + 3 + 1)])
            NS._poly(surface, P["gob_darkest"], [
                (cx + side * 8, cy - 1),
                (cx + side * 17, cy - 6 - (tw if side == f else 0)),
                (cx + side * 10, cy + 3)])
            NS._poly(surface, P["gob_dark"], [
                (cx + side * 8, cy),
                (cx + side * 14, cy - 4),
                (cx + side * 10, cy + 2)])
            NS._poly(surface, P["gob_mid"], [
                (cx + side * 9, cy),
                (cx + side * 12, cy - 3),
                (cx + side * 10, cy + 1)])

        # hidung besar goblin
        NS._poly(surface, P["gob_dark"], [
            (cx + f * 3, cy), (cx + f * 8, cy + 2),
            (cx + f * 8, cy + 5), (cx + f * 3, cy + 5)])
        NS._poly(surface, P["gob_mid"], [
            (cx + f * 3, cy + 1), (cx + f * 6, cy + 3), (cx + f * 3, cy + 3)])
        NS._aacircle(surface, P["gob_light"], (cx + f * 4, cy + 1), 1)

        # mulut + gigi taring
        NS._rect(surface, P["shadow_deep"], (cx - 3, cy + 6, 7, 2))
        grin = math.sin(phase * 0.7) > 0.5
        NS._poly(surface, P["bone_light"], [
            (cx + 2, cy + 6), (cx + 4, cy + (9 if grin else 8)),
            (cx + 4, cy + 6)])
        NS._poly(surface, P["bone_light"], [
            (cx - 2, cy + 6), (cx - 3, cy + 8), (cx - 1, cy + 6)])

        # goggles biru signature (2 lensa + strap + specular cluster)
        NS._rect(surface, P["leather_darkest"], (cx - 9, cy - 8, 18, 6),
                 border_radius=2)
        NS._rect(surface, P["leather_dark"], (cx - 8, cy - 7, 16, 4))
        for gx in (-4, 4):
            NS._aacircle(surface, P["metal_dark"], (cx + gx, cy - 5), 4)
            NS._aacircle(surface, P["blue_dark"], (cx + gx, cy - 5), 3)
            NS._aacircle(surface, P["blue_mid"], (cx + gx, cy - 5), 2)
            NS._aacircle(surface, P["blue_light"], (cx + gx - 1, cy - 6), 1)
            NS._aacircle(surface, P["blue_shine"], (cx + gx - 2, cy - 7), 1)

        # helm kulit ber-rivet
        NS._poly(surface, P["shadow_deep"], [
            (cx - 10 + 1, cy - 8 + 1), (cx - 7 + 1, cy - 13 + 1),
            (cx + 7 + 1, cy - 13 + 1), (cx + 10 + 1, cy - 8 + 1)])
        NS._poly(surface, P["leather_darkest"], [
            (cx - 10, cy - 8), (cx - 7, cy - 13),
            (cx + 7, cy - 13), (cx + 10, cy - 8)])
        NS._poly(surface, P["leather_dark"], [
            (cx - 9, cy - 8), (cx - 6, cy - 12),
            (cx + 6, cy - 12), (cx + 9, cy - 8)])
        NS._poly(surface, P["leather_mid"], [
            (cx - 8, cy - 8), (cx - 5, cy - 11),
            (cx + 4, cy - 11), (cx + 7, cy - 8)])
        NS._poly(surface, P["leather_light"], [
            (cx - 7, cy - 9), (cx - 5, cy - 10), (cx - 2, cy - 10),
            (cx - 4, cy - 9)])
        # rivet brass + antena kecil
        NS._aacircle(surface, P["brass_mid"], (cx - 6, cy - 10), 1)
        NS._aacircle(surface, P["brass_shine"], (cx - 6, cy - 11), 1)
        NS._aacircle(surface, P["brass_mid"], (cx + 6, cy - 10), 1)
        NS._aaline(surface, P["metal_mid"], (cx + 7, cy - 12),
                   (cx + 9, cy - 17), 1)
        NS._aacircle(surface, P["fire_bright"], (cx + 9, cy - 17), 1)

    def _draw_fuel_tanks(surface, cx, cy, phase):
        """Tangki bahan bakar brass ganda + selang + gauge bergetar."""
        NS = _NS_razak
        P = NS.PALETTE
        for i, off in enumerate((-3, 3)):
            NS._rect(surface, P["shadow_deep"],
                     (cx - 3 + off + 1, cy - 6 + 1, 5, 15), border_radius=2)
            NS._rect(surface, P["brass_dark"], (cx - 3 + off, cy - 6, 5, 15),
                     border_radius=2)
            NS._rect(surface, P["brass_mid"], (cx - 2 + off, cy - 5, 3, 13))
            NS._rect(surface, P["brass_light"], (cx - 2 + off, cy - 5, 1, 10))
            NS._aacircle(surface, P["brass_shine"], (cx - 2 + off, cy - 4), 1)
            # cap logam + valve
            NS._rect(surface, P["metal_dark"], (cx - 3 + off, cy - 8, 5, 3))
            NS._rect(surface, P["metal_light"], (cx - 3 + off, cy - 8, 5, 1))
            NS._aacircle(surface, P["metal_mid"], (cx - 1 + off, cy - 9), 1)
            # band pengikat
            NS._rect(surface, P["leather_darkest"], (cx - 3 + off, cy, 5, 2))

        # selang penghubung + ke gun
        NS._aaline(surface, P["leather_darkest"], (cx - 2, cy - 4),
                   (cx + 4, cy - 3), 2)
        NS._aaline(surface, P["smoke_dark"], (cx + 3, cy + 2),
                   (cx + 9, cy + 6), 2)
        NS._aaline(surface, P["smoke_mid"], (cx + 3, cy + 2),
                   (cx + 9, cy + 6), 1)

        # gauge tekanan (jarum bergetar - idle hidup)
        gx, gy = cx, cy + 6
        NS._aacircle(surface, P["metal_dark"], (gx, gy), 3)
        NS._aacircle(surface, P["bone_light"], (gx, gy), 2)
        na = -0.8 + math.sin(phase * 5.0) * 0.25
        NS._aaline(surface, P["fire_dark"], (gx, gy),
                   (gx + math.cos(na) * 2, gy + math.sin(na) * 2), 1)
        NS._aacircle(surface, P["gold_mid"], (gx, gy), 3, 1)
    # ===================================================================
    # LENGAN & SENJATA
    # ===================================================================
    def _draw_goblin_idle_arms(surface, cx, cy, facing, phase):
        """Idle - machete di tangan belakang, flamethrower di depan."""
        NS = _NS_razak
        sway = math.sin(phase * 0.7) * 1.5

        back_side = -facing
        bs_x = cx + back_side * 7
        bs_y = cy - 3
        bh_x = bs_x + back_side * 6
        bh_y = cy + 6 + int(sway)
        NS._draw_goblin_arm(surface, bs_x, bs_y, bh_x, bh_y)
        NS._draw_machete_held(surface, bh_x, bh_y, back_side, phase)

        fs_x = cx + facing * 7
        fs_y = cy - 3
        fh_x = fs_x + facing * 11
        fh_y = cy - 1 + int(sway)
        NS._draw_goblin_arm(surface, fs_x, fs_y, fh_x, fh_y)
        NS._draw_flame_gun(surface, fh_x, fh_y, facing, phase)

    def _draw_goblin_gun_arms(surface, cx, cy, facing, phase):
        """Both arms holding gun forward, firing."""
        NS = _NS_razak
        fs_x = cx + facing * 7
        fs_y = cy - 3
        fh_x = fs_x + facing * 14
        fh_y = cy - 1
        NS._draw_goblin_arm(surface, fs_x, fs_y, fh_x, fh_y)

        bs_x = cx - facing * 4
        bs_y = cy - 2
        bh_x = fh_x - facing * 6
        bh_y = fh_y
        NS._draw_goblin_arm(surface, bs_x, bs_y, bh_x, bh_y)

        NS._draw_flame_gun(surface, fh_x, fh_y, facing, phase, firing=True)

    def _draw_goblin_attack_arms(surface, cx, cy, facing, phase, progress,
                                 boss=None):
        """Lengan depan ayun machete (7 keyframe), belakang pegang gun."""
        NS = _NS_razak
        pose = NS._attack_pose(progress)

        # lengan belakang - gun istirahat
        back_side = -facing
        bs_x = cx + back_side * 4
        bs_y = cy - 3
        bh_x = bs_x + back_side * 8
        bh_y = cy + 2
        NS._draw_goblin_arm(surface, bs_x, bs_y, bh_x, bh_y)
        NS._draw_flame_gun(surface, bh_x, bh_y, back_side, phase)

        # lengan depan - machete mengikuti kurva keyframe
        fs_x = cx + facing * 7
        fs_y = cy - 3
        arm_angle = pose["arm_a"]
        arm_len = 14
        fh_x = fs_x + int(math.cos(arm_angle) * arm_len) * facing
        fh_y = fs_y + int(math.sin(arm_angle) * arm_len)
        NS._draw_goblin_arm(surface, fs_x, fs_y, fh_x, fh_y)

        blade_angle = arm_angle + math.pi / 4 * facing
        NS._draw_machete_swinging(surface, fh_x, fh_y, facing, blade_angle)

        # frame IMPACT: bintang + serpihan bara di ujung machete
        # (fallback canvas saja - lapisan hidup punya ImpactFX penuh).
        if pose["impact"] > 0.05 and not NS._fx_owned(boss):
            k = pose["impact"]
            tipx = fh_x + int(math.cos(blade_angle) * 26) * facing
            tipy = fh_y + int(math.sin(blade_angle) * 26)
            NS._spark_star(surface, tipx, tipy, int(14 * k),
                           NS.PALETTE["fire_hot"], int(240 * k), spikes=6,
                           rot=progress * 4, core=NS.PALETTE["fire_white"])
            for i in range(4):
                a = progress * 6 + i * math.pi / 2
                NS._draw_ember(surface, tipx + int(math.cos(a) * 10 * k),
                               tipy + int(math.sin(a) * 7 * k), 1,
                               int(220 * k))

    def _draw_goblin_arm(surface, x1, y1, x2, y2):
        """Lengan goblin 4-band + tangan."""
        NS = _NS_razak
        P = NS.PALETTE
        NS._aaline(surface, P["shadow_deep"], (x1 + 1, y1 + 2),
                   (x2 + 1, y2 + 2), 6)
        NS._aaline(surface, P["gob_darkest"], (x1, y1), (x2, y2), 5)
        NS._aaline(surface, P["gob_dark"], (x1, y1), (x2, y2), 4)
        NS._aaline(surface, P["gob_mid"], (x1, y1), (x2, y2), 2)
        NS._aaline(surface, P["gob_light"], (x1, y1),
                   ((x1 + x2) // 2, (y1 + y2) // 2), 1)
        NS._aacircle(surface, P["gob_darkest"], (x2, y2), 3)
        NS._aacircle(surface, P["gob_mid"], (x2, y2), 2)
        NS._aacircle(surface, P["gob_light"], (x2 - 1, y2 - 1), 1)

    def _draw_flame_gun(surface, hx, hy, facing, phase, firing=False):
        """Flamethrower brass: grip + barrel + moncong flare + pilot flame."""
        NS = _NS_razak
        P = NS.PALETTE

        # grip kulit
        NS._rect(surface, P["leather_darkest"], (hx - 2, hy - 2, 4, 7),
                 border_radius=1)
        NS._rect(surface, P["leather_dark"], (hx - 2, hy - 2, 4, 5))
        NS._rect(surface, P["leather_mid"], (hx - 1, hy - 1, 2, 3))

        # barrel brass 4-band
        barrel_len = 17
        end_x = hx + facing * barrel_len
        bx0 = min(hx, end_x)
        NS._rect(surface, P["shadow_deep"],
                 (bx0 + 1, hy - 4 + 1, barrel_len, 7), border_radius=2)
        NS._rect(surface, P["brass_dark"], (bx0, hy - 4, barrel_len, 7),
                 border_radius=2)
        NS._rect(surface, P["brass_mid"], (bx0, hy - 3, barrel_len, 5))
        NS._rect(surface, P["brass_light"], (bx0, hy - 3, barrel_len, 2))
        NS._aacircle(surface, P["brass_shine"],
                     (hx + facing * 5, hy - 3), 1)
        NS._aacircle(surface, P["brass_shine"],
                     (hx + facing * 9, hy - 3), 1)
        # ring baja + rivet di tengah barrel
        NS._rect(surface, P["metal_dark"],
                 (hx + facing * 7 - (2 if facing < 0 else 0), hy - 4, 2, 7))
        NS._aacircle(surface, P["metal_light"],
                     (hx + facing * 8, hy - 4), 1)

        # moncong flare 3-band
        NS._poly(surface, P["brass_dark"], [
            (end_x, hy - 5), (end_x + facing * 6, hy - 7),
            (end_x + facing * 6, hy + 5), (end_x, hy + 3)])
        NS._poly(surface, P["brass_mid"], [
            (end_x, hy - 4), (end_x + facing * 5, hy - 5),
            (end_x + facing * 5, hy + 3), (end_x, hy + 2)])
        NS._poly(surface, P["brass_light"], [
            (end_x + facing, hy - 3), (end_x + facing * 4, hy - 4),
            (end_x + facing * 4, hy + 1)])
        NS._aacircle(surface, P["brass_shine"],
                     (end_x + facing * 3, hy - 3), 1)

        # pilot flame flicker (idle hidup)
        if not firing:
            px = end_x + facing * 7
            py = hy - 1
            fl = 0.6 + 0.4 * abs(math.sin(phase * 3.1))
            NS._aacircle(surface, (*P["fire_bright"], int(200 * fl)),
                         (px, py), 2)
            NS._aacircle(surface, (*P["fire_hot"], int(230 * fl)), (px, py), 1)
            NS._aacircle(surface, (*P["fire_glow"], 255),
                         (px, py - 1), 1)

    def _draw_machete_held(surface, hx, hy, side, phase):
        """Machete istirahat: bilah 5-band + fuller + grip kulit."""
        NS = _NS_razak
        P = NS.PALETTE
        blade_end_x = hx + side * 20
        blade_end_y = hy - 9

        NS._aaline(surface, P["shadow_deep"], (hx + 1, hy + 2),
                   (blade_end_x + 1, blade_end_y + 2), 6)
        # bilah 5-band
        NS._poly(surface, P["metal_darkest"], [
            (hx, hy - 2), (hx + side * 4, hy - 4),
            (blade_end_x, blade_end_y),
            (blade_end_x - side * 3, blade_end_y + 4), (hx, hy + 1)])
        NS._poly(surface, P["metal_dark"], [
            (hx + side, hy - 2), (hx + side * 4, hy - 3),
            (blade_end_x - side, blade_end_y + 1), (hx + side, hy)])
        NS._poly(surface, P["metal_mid"], [
            (hx + side * 3, hy - 2),
            (blade_end_x - side * 3, blade_end_y + 2), (hx + side * 3, hy)])
        # fuller gelap di tengah bilah
        NS._aaline(surface, P["metal_darkest"],
                   (hx + side * 5, hy - 2),
                   (blade_end_x - side * 4, blade_end_y + 2), 1)
        # edge highlight + specular cluster
        NS._aaline(surface, P["metal_light"],
                   (hx + side * 4, hy - 3),
                   (blade_end_x - side, blade_end_y + 1), 1)
        NS._aacircle(surface, P["metal_shine"],
                     (hx + side * 8, hy - 4), 1)
        NS._aacircle(surface, P["metal_shine"],
                     (hx + side * 13, hy - 6), 1)

        # grip kulit berlilit + pommel brass
        NS._rect(surface, P["leather_darkest"], (hx - 2, hy, 4, 6))
        NS._rect(surface, P["leather_dark"], (hx - 1, hy, 2, 5))
        NS._aaline(surface, P["leather_mid"], (hx - 2, hy + 2),
                   (hx + 2, hy + 3), 1)
        NS._aacircle(surface, P["brass_mid"], (hx, hy + 6), 2)
        NS._aacircle(surface, P["brass_shine"], (hx - 1, hy + 5), 1)

    def _draw_machete_swinging(surface, hx, hy, facing, angle):
        """Machete in motion - bilah 5-band + api di edge."""
        NS = _NS_razak
        P = NS.PALETTE
        blade_len = 28
        dx = math.cos(angle) * facing
        dy = math.sin(angle)
        perp_x = -math.sin(angle)
        perp_y = math.cos(angle) * facing

        end_x = hx + int(dx * blade_len)
        end_y = hy + int(dy * blade_len)

        NS._aaline(surface, P["shadow_deep"], (hx + 2, hy + 3),
                   (end_x + 2, end_y + 3), 6)

        blade_pts = [
            (hx + int(perp_x * 3), hy + int(perp_y * 3)),
            (hx + int(dx * blade_len * 0.5) + int(perp_x * 4),
             hy + int(dy * blade_len * 0.5) + int(perp_y * 4)),
            (end_x, end_y),
            (hx + int(dx * blade_len * 0.5) - int(perp_x * 2),
             hy + int(dy * blade_len * 0.5) - int(perp_y * 2)),
            (hx - int(perp_x * 2), hy - int(perp_y * 2)),
        ]
        NS._poly(surface, P["metal_darkest"], blade_pts)
        NS._poly(surface, P["metal_dark"], [
            (hx + int(perp_x * 2), hy + int(perp_y * 2)),
            (hx + int(dx * blade_len * 0.5) + int(perp_x * 3),
             hy + int(dy * blade_len * 0.5) + int(perp_y * 3)),
            (end_x, end_y),
            (hx + int(dx * blade_len * 0.5), hy + int(dy * blade_len * 0.5)),
        ])
        NS._poly(surface, P["metal_mid"], [
            (hx + int(perp_x * 3), hy + int(perp_y * 3)),
            (hx + int(dx * blade_len * 0.4) + int(perp_x * 3),
             hy + int(dy * blade_len * 0.4) + int(perp_y * 3)),
            (end_x, end_y),
        ])
        # fuller
        NS._aaline(surface, P["metal_darkest"],
                   (hx + int(dx * 6), hy + int(dy * 6)),
                   (hx + int(dx * blade_len * 0.8),
                    hy + int(dy * blade_len * 0.8)), 1)
        # edge highlight
        NS._aaline(surface, P["metal_shine"],
                   (hx + int(perp_x * 4), hy + int(perp_y * 4)),
                   (end_x, end_y), 1)

        # api di bilah (machete Batrider terbakar!)
        NS._aacircle(surface, (*P["fire_bright"], 180), (end_x, end_y), 6)
        NS._aacircle(surface, (*P["fire_hot"], 220), (end_x, end_y), 4)
        NS._aacircle(surface, (*P["fire_glow"], 255), (end_x, end_y), 2)
        NS._aacircle(surface, (*P["fire_white"], 255),
                     (end_x - 1, end_y - 1), 1)
        # lidah api sepanjang edge
        for k in (0.45, 0.7):
            fx = hx + int(dx * blade_len * k) + int(perp_x * 4)
            fy = hy + int(dy * blade_len * k) + int(perp_y * 4)
            NS._aacircle(surface, (*P["fire_bright"], 160), (fx, fy), 2)
            NS._aacircle(surface, (*P["fire_hot"], 200), (fx, fy), 1)
    # ===================================================================
    # EFFECTS - Wisps, aura, shadow, swing trail
    # ===================================================================
    def _draw_fire_wisps(surface, cx, cy, phase, trail=False, facing=1,
                         intense=False):
        """Fire wisps di bawah bat (pengganti kaki) - mist ter-cache."""
        NS = _NS_razak
        P = NS.PALETTE
        strength = 1.5 if intense else 1.0

        def build():
            mist = pygame.Surface((150, 48), pygame.SRCALPHA)
            for radius in range(36, 3, -4):
                alpha = int((36 - radius) * 2.4)
                if alpha > 0:
                    pygame.draw.ellipse(
                        mist, (*P["fire_darkest"], min(255, alpha)),
                        (75 - radius * 2, 24 - radius // 3,
                         radius * 4, max(3, radius // 2)))
            return mist

        mist = NS._static("wisp_mist", build)
        pulse = math.sin(phase * 1.5) * 0.25 + 0.75
        spr = mist.copy() if strength != 1.0 else mist
        spr.set_alpha(int(255 * min(1.0, pulse * strength)))
        surface.blit(spr, (cx - 75, cy - 12))
        spr.set_alpha(255)

        # wisp api naik
        for i, offset in enumerate((-26, -11, 7, 22)):
            t = (phase * 0.6 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 4 - int(t * 28)
            alpha = max(0, min(255, int(220 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            NS._aacircle(surface, (*P["fire_dark"], alpha), (sx, sy), 5)
            NS._aacircle(surface, (*P["fire_bright"], alpha), (sx, sy - 2), 3)
            NS._aacircle(surface, (*P["fire_hot"], alpha), (sx, sy - 3), 2)
            NS._aacircle(surface, (*P["fire_glow"], alpha), (sx, sy - 3), 1)

        # bara orbit
        for i in range(7):
            angle = phase * 1.0 + i * math.pi * 2 / 7
            r = 27 + int(math.sin(phase + i * 1.3) * 6)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 8)
            NS._draw_ember(surface, sx, sy, 2, 200)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = max(0, 150 - i * 25)
                NS._aacircle(surface, (*P["fire_dark"], alpha),
                             (sx, sy), max(2, 6 - i))
                NS._aacircle(surface, (*P["fire_bright"], alpha),
                             (sx, sy), max(1, 4 - i))
                NS._aacircle(surface, (*P["fire_hot"], alpha // 2),
                             (sx, sy), max(1, 2 - i))

    def _draw_shadow(surface, x, y, lift=0):
        """Bayangan tanah ter-cache; menyusut saat lift, dasar menapak."""
        NS = _NS_razak
        if NS._shadow_cache is None:
            shadow = pygame.Surface((110, 22), pygame.SRCALPHA)
            for radius in range(11, 0, -1):
                alpha = max(0, (11 - radius) * 15)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (11 - radius, 11 - radius, 88 + radius * 2, radius * 2),
                )
            pygame.draw.ellipse(shadow, (*NS.PALETTE["fire_dark"], 60),
                                (10, 5, 90, 12))
            NS._shadow_cache = shadow
        spr = NS._shadow_cache
        w = spr.get_width()
        h = spr.get_height()
        if lift:
            k = max(0.12, 1.0 - lift * 0.05)
            w = max(6, int(w * k))
            h = max(2, int(h * k))
            spr = pygame.transform.smoothscale(spr, (w, h))
        bx = x - w // 2
        by = (y + 11) - h          # bottom tetap di y+11 (menapak)
        surface.blit(spr, (bx, by))
        if NS._record_shadow is not None:
            NS._record_shadow.append(pygame.Rect(bx, by, w, h))

    def _draw_fire_aura(surface, x, y, phase, active_skill):
        """Aura panas ambient ter-cache; menguat saat skill aktif."""
        NS = _NS_razak
        if NS._aura_cache is None:
            aura = pygame.Surface((200, 170), pygame.SRCALPHA)
            for radius in range(80, 5, -4):
                alpha = int((80 - radius) * 1.2)
                if alpha > 0:
                    NS._aacircle(aura, (*NS.PALETTE["fire_darkest"],
                                        min(255, alpha)), (100, 85), radius)
            NS._aura_cache = aura
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.6 if active_skill in ("q", "w", "r") else 1.0
        a = int(255 * min(1.0, pulse * strength))
        spr = NS._aura_cache.copy()
        spr.set_alpha(a)
        surface.blit(spr, (x - 100, y - 85))

    def _draw_machete_swing_arc(surface, x, y, facing, progress):
        """Swing trail machete: smear sabit api 3 lapis + leading edge.

        SESUAI KARAKTER: trail-nya API (bukan garis logam) - sabit
        fire_dark -> fire_bright -> fire_hot dengan tepi depan menyala
        putih dan bara terlempar dari busur.
        """
        NS = _NS_razak
        P = NS.PALETTE
        if progress < 0.28 or progress > 0.78:
            return
        if progress < 0.5:
            vis = (progress - 0.28) / 0.22
        else:
            vis = 1.0 - (progress - 0.5) / 0.28
        vis = max(0.0, min(1.0, vis))

        arc = pygame.Surface((170, 130), pygame.SRCALPHA)
        acx, acy = 85, 62
        # sabit smear: 3 pita mengikuti busur ayunan, lebar menipis di ekor
        sweep = min(1.0, (progress - 0.24) / 0.34)
        a_end = -math.pi * 0.95 + sweep * math.pi * 1.25
        n = 16
        for band, (col, rr, wid) in enumerate((
                (P["fire_dark"], 56, 9),
                (P["fire_bright"], 52, 6),
                (P["fire_hot"], 49, 3))):
            pts_o, pts_i = [], []
            for i in range(n + 1):
                t = i / n
                ang = a_end - t * math.pi * 0.85
                w = wid * (1.0 - t * 0.75)
                ca = math.cos(ang) * facing
                sa = math.sin(ang) * 0.78
                pts_o.append((acx + ca * (rr + w), acy + sa * (rr + w)))
                pts_i.append((acx + ca * (rr - w), acy + sa * (rr - w)))
            pts = pts_o + pts_i[::-1]
            alpha = int((150 - band * 25) * vis)
            NS._poly(arc, (*col, alpha), pts)
        # leading edge putih menyala
        ca = math.cos(a_end) * facing
        sa = math.sin(a_end) * 0.78
        lx, ly = acx + ca * 52, acy + sa * 52
        NS._aaline(arc, (*P["fire_white"], int(230 * vis)),
                   (acx + ca * 42, acy + sa * 42),
                   (acx + ca * 62, acy + sa * 62), 3)
        NS._aacircle(arc, (*P["fire_glow"], int(240 * vis)),
                     (int(lx), int(ly)), 4)
        NS._aacircle(arc, (*P["fire_white"], int(255 * vis)),
                     (int(lx), int(ly)), 2)
        # bara terlempar dari busur (deterministik)
        for i in range(5):
            t = 0.15 + 0.17 * i
            ang = a_end - t * math.pi * 0.8
            rr = 58 + NS._hash01(i * 13) * 12
            ex = acx + math.cos(ang) * facing * rr
            ey = acy + math.sin(ang) * 0.78 * rr
            ea = int(200 * vis * (1 - t))
            if ea > 10:
                NS._draw_ember(arc, int(ex), int(ey), 1, ea)
        surface.blit(arc, (x - 85, y - 62))
    # ===================================================================
    # SKILL GROUND TELEGRAPHS (world-space, radius = gameplay px dunia)
    # ===================================================================
    def _draw_napalm_ground(surface, boss, x, y, timer, phase):
        """Q telegraph: ring 75 px dunia DI TARGET + jalur lempar."""
        NS = _NS_razak
        P = NS.PALETTE
        duration = NS.SKILL_DUR["q"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        fs = NS._fx_scale(boss)
        tx, ty = NS._target_position(boss, x, y)
        r = NS._ring_r(boss, NS.SKILL_RADIUS["q"], surface)
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7

        # alas gosong + wash zona (pekat di tepi)
        NS._ground_scorch(surface, tx, ty, int(r * 1.05), P["fire_darkest"],
                          P["shadow_deep"], int(150 * pulse), seed=5)
        NS._zone_fill(surface, tx, ty, r, P["fire_dark"],
                      int(90 * pulse), edge_bias=3.0)
        # ring jangkauan TEPAT di radius gameplay
        NS._ground_ring(surface, tx, ty, r, P["fire_bright"], P["fire_glow"],
                        int(215 * pulse), thickness=3, softness=8,
                        inner_glow=26)
        # rune ring berputar di dalam
        NS._rune_ring(surface, tx, ty, int(r * 0.72), P["fire_mid"],
                      P["fire_hot"], int(170 * pulse), phase * 0.9,
                      segments=10, span=0.45)
        # ring konvergen ("incoming") mengecil ke titik jatuh
        conv = 1.0 - (progress * 1.6 % 1.0)
        NS._ground_ring(surface, tx, ty, max(6, int(r * conv)),
                        P["fire_hot"], P["fire_white"],
                        int(160 * (1 - conv)), thickness=2, softness=5)
        # chevron berbaris dari caster menuju target
        dx, dy = tx - x, ty - (y + NS.GROUND_DY)
        ang = math.atan2(dy, dx)
        for i in range(3):
            t = ((phase * 0.4 + i / 3.0) % 1.0)
            px = x + dx * t
            py = (y + NS.GROUND_DY) + dy * t
            NS._chevron(surface, px, py, ang, 7 * fs, P["fire_hot"],
                        int(200 * (1 - t) * pulse), width=3)
        # splat marker pusat
        NS._spark_star(surface, tx, ty, int(9 * fs), P["fire_glow"],
                       int(210 * pulse), spikes=4, rot=phase * 1.3,
                       core=P["fire_white"])

    def _draw_flamebreak_ground(surface, boss, x, y, timer, phase):
        """W telegraph: ring 95 px dunia DI TARGET + kerucut semburan."""
        NS = _NS_razak
        P = NS.PALETTE
        tx, ty = NS._target_position(boss, x, y)
        r = NS._ring_r(boss, NS.SKILL_RADIUS["w"], surface)
        pulse = math.sin(phase * 2.2) * 0.3 + 0.7

        NS._ground_scorch(surface, tx, ty, int(r * 1.02), P["fire_darkest"],
                          P["shadow_deep"], int(140 * pulse), seed=9)
        NS._zone_fill(surface, tx, ty, r, P["fire_mid"],
                      int(80 * pulse), edge_bias=3.2)
        NS._ground_ring(surface, tx, ty, r, P["fire_bright"], P["fire_glow"],
                        int(220 * pulse), thickness=3, softness=8,
                        inner_glow=22)
        # dua rune ring berputar berlawanan arah
        NS._rune_ring(surface, tx, ty, int(r * 0.8), P["fire_mid"],
                      P["fire_hot"], int(160 * pulse), phase * 1.1,
                      segments=12, span=0.4)
        NS._rune_ring(surface, tx, ty, int(r * 0.55), P["fire_bright"],
                      P["fire_glow"], int(130 * pulse), -phase * 1.5,
                      segments=8, span=0.5)
        # retakan magma dari pusat (zigzag deterministik)
        for i in range(5):
            ang = i * math.tau / 5 + 0.5
            NS._jagged_crack(surface, tx, ty, ang, r * 0.7,
                             (P["fire_darkest"], P["fire_bright"]),
                             int(170 * pulse), seed=17 + i, width=2)

    def _draw_firefly_ground(surface, boss, x, y, timer, phase):
        """E telegraph: ring pendaratan 80 px dunia + jejak dash."""
        NS = _NS_razak
        P = NS.PALETTE
        duration = NS.SKILL_DUR["e"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        fs = NS._fx_scale(boss)
        gy = y + NS.GROUND_DY
        r = NS._ring_r(boss, NS.SKILL_RADIUS["e"], surface)
        pulse = math.sin(phase * 3.0) * 0.3 + 0.7

        # AOE pendaratan di posisi diri (AI memindahkan boss dulu)
        NS._ground_scorch(surface, x, gy, int(r * 1.0), P["fire_darkest"],
                          P["shadow_deep"], int(130 * pulse), seed=13)
        NS._zone_fill(surface, x, gy, r, P["fire_dark"],
                      int(85 * pulse), edge_bias=3.0)
        NS._ground_ring(surface, x, gy, r, P["fire_bright"], P["fire_glow"],
                        int(210 * pulse), thickness=3, softness=7,
                        inner_glow=20)
        NS._dashed_ring(surface, x, gy, int(r * 0.8), P["fire_hot"],
                        int(150 * pulse), phase * 2.0 + progress * 3.0,
                        segments=12, thick=2, span=0.5, squash=1.0)
        # ring konvergen mengecil seiring progress (fase terbaca)
        conv = 1.0 - (progress * 1.4 % 1.0)
        NS._ground_ring(surface, x, gy, max(6, int(r * conv)),
                        P["fire_hot"], P["fire_white"],
                        int(150 * (1 - conv)), thickness=2, softness=5)
        # jejak api di belakang arah dash - memudar seiring progress
        f = getattr(boss, "direction", 1)
        tfade = max(0.0, 1.0 - progress * 1.1)
        for i in range(4):
            px = x - (18 + i * 16) * fs * f
            a = int(160 * (1 - i / 4.0) * pulse * (0.35 + 0.65 * tfade))
            NS._glow(surface, px, gy, int(10 * fs), P["fire_mid"], a)
        # bintang hentak saat mendarat (awal skill)
        if progress < 0.3:
            k = 1 - progress / 0.3
            NS._spark_star(surface, x, gy, int(16 * fs * k), P["fire_hot"],
                           int(240 * k), spikes=8, rot=progress * 5,
                           core=P["fire_white"])

    def _draw_firestorm_ground(surface, boss, x, y, timer, phase):
        """R telegraph: ring ultimate 180 px dunia DI CASTER.

        AI (_razak_r) memukul semua musuh <= 180 px dari DIRI - maka
        telegraph diletakkan di caster (v1 salah menaruhnya di target).
        """
        NS = _NS_razak
        P = NS.PALETTE
        duration = NS.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        fs = NS._fx_scale(boss)
        gy = y + NS.GROUND_DY
        r = NS._ring_r(boss, NS.SKILL_RADIUS["r"], surface)
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # alas gosong besar + wash zona
        NS._ground_scorch(surface, x, gy, int(r * 1.03), P["fire_darkest"],
                          P["shadow_deep"], int(160 * pulse), seed=21)
        NS._zone_fill(surface, x, gy, r, P["fire_dark"],
                      int(95 * pulse), edge_bias=3.4)
        # ring jangkauan tepat 180 px dunia
        NS._ground_ring(surface, x, gy, r, P["fire_bright"], P["fire_glow"],
                        int(230 * pulse), thickness=4, softness=9,
                        inner_glow=30)
        # rune ring ganda berlawanan arah
        NS._rune_ring(surface, x, gy, int(r * 0.85), P["fire_mid"],
                      P["fire_hot"], int(170 * pulse), phase * 0.8,
                      segments=14, span=0.4)
        NS._rune_ring(surface, x, gy, int(r * 0.62), P["fire_bright"],
                      P["fire_glow"], int(140 * pulse), -phase * 1.2,
                      segments=10, span=0.46)
        # retakan magma radial ber-seam menyala
        for i in range(7):
            ang = i * math.tau / 7 + 0.3
            NS._jagged_crack(surface, x, gy, ang, r * 0.8,
                             (P["fire_darkest"], P["fire_bright"]),
                             int(190 * pulse), seed=31 + i, width=3)
        # ring konvergen membaca "erupsi memuncak"
        conv = 1.0 - (progress * 1.3 % 1.0)
        NS._ground_ring(surface, x, gy, max(8, int(r * conv)),
                        P["fire_hot"], P["fire_white"],
                        int(150 * (1 - conv)), thickness=2, softness=6)
        # chevron kardinal mengarah keluar (bahaya menyebar)
        for i in range(4):
            ang = i * math.pi / 2 + phase * 0.3
            px = x + math.cos(ang) * r * 0.94
            py = gy + math.sin(ang) * r * 0.94 * 0.92
            NS._chevron(surface, px, py, ang, 8 * fs, P["fire_glow"],
                        int(190 * pulse), width=3)

    # ===================================================================
    # SKILL Q: STICKY NAPALM (arcing molotov + splat)
    # ===================================================================
    def _draw_sticky_napalm(surface, boss, x, y, timer, phase):
        duration = 40
        NS = _NS_razak
        P = NS.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / duration))
        fs = NS._fx_scale(boss)
        tx, ty = NS._target_position(boss, x, y)

        # Spawn projectile at start
        if progress < 0.15 and not getattr(boss, "_razak_napalm_spawned",
                                           False):
            sx = x + 18 * boss.direction
            sy = y - 5
            NS._spawn_napalm(boss, sx, sy, tx, ty)
            boss._razak_napalm_spawned = True
        if progress > 0.7:
            boss._razak_napalm_spawned = False

        # AKTIVASI: muzzle vortex - dua arc berlawanan + droplet orbit
        if progress < 0.3:
            k = 1 - progress / 0.3
            fx = x + int(20 * fs) * boss.direction
            fy = y - int(6 * fs)
            alpha = int(255 * k)
            NS._glow(surface, fx, fy, int(20 * fs), P["fire_mid"],
                     int(180 * k))
            NS._aacircle(surface, (*P["fire_bright"], alpha), (fx, fy),
                         int(9 * fs))
            NS._aacircle(surface, (*P["fire_hot"], alpha), (fx, fy),
                         int(6 * fs))
            NS._aacircle(surface, (*P["fire_glow"], alpha), (fx, fy),
                         int(3 * fs))
            NS._aacircle(surface, (*P["fire_white"], min(255, alpha)),
                         (fx, fy), max(1, int(2 * fs)))
            NS._dashed_ring(surface, fx, fy, int(14 * fs), P["fire_hot"],
                            int(220 * k), phase * 3.0, segments=6,
                            thick=2, span=0.55, squash=1.0)
            NS._dashed_ring(surface, fx, fy, int(19 * fs), P["fire_bright"],
                            int(160 * k), -phase * 2.2, segments=8,
                            thick=2, span=0.5, squash=1.0)
            NS._spark_star(surface, fx, fy, int(13 * fs), P["fire_glow"],
                           alpha, spikes=6, rot=progress * 8,
                           core=P["fire_white"])
            # droplet api orbit
            for i in range(6):
                angle = progress * 7 + i * math.tau / 6
                ex = fx + int(math.cos(angle) * 14 * fs)
                ey = fy + int(math.sin(angle) * 10 * fs)
                NS._draw_ember(surface, ex, ey, 2, alpha)

        # IMPACT di target: splat ganda + bintang + kipasan droplet
        if 0.55 < progress < 0.95:
            imp = 1 - abs(progress - 0.73) / 0.20
            imp = max(0.0, min(1.0, imp))
            ir = int((8 + imp * 26) * fs)
            ia = int(230 * imp)
            NS._glow(surface, tx, ty, int(24 * fs), P["fire_mid"],
                     int(150 * imp))
            NS._ground_ring(surface, tx, ty, ir, P["fire_bright"],
                            P["fire_glow"], ia, thickness=3, softness=7)
            NS._ground_ring(surface, tx, ty, int(ir * 0.55), P["fire_hot"],
                            P["fire_white"], int(ia * 0.7),
                            thickness=2, softness=5)
            NS._spark_star(surface, tx, ty, int(15 * fs * imp),
                           P["fire_hot"], ia, spikes=8, rot=progress * 5,
                           core=P["fire_white"])
            # kipasan droplet napalm keluar dari titik jatuh
            for i in range(7):
                a = i * math.tau / 7 + 0.4
                d = (10 + 16 * imp) * fs
                dxp = tx + int(math.cos(a) * d)
                dyp = ty + int(math.sin(a) * d * 0.6)
                NS._draw_ember(surface, dxp, dyp, 2, int(ia * 0.85))

    # ===================================================================
    # SKILL W: FLAMEBREAK (flame cone/stream)
    # ===================================================================
    def _draw_flamebreak(surface, boss, x, y, timer, phase):
        duration = 50
        NS = _NS_razak
        P = NS.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / duration))
        fs = NS._fx_scale(boss)
        tx, ty = NS._target_position(boss, x, y)

        # Continuous flame stream forward
        if progress < 0.85:
            start_x = x + 22 * boss.direction
            start_y = y - 5

            dx = tx - start_x
            dy = ty - start_y
            dist = math.hypot(dx, dy) or 1.0
            dir_x = dx / dist
            dir_y = dy / dist
            perp_x = -dir_y
            perp_y = dir_x

            # panjang kerucut menuju target (bukan fixed 180 canvas px)
            full_len = dist
            if progress < 0.2:
                flame_len = full_len * (progress / 0.2)
            else:
                flame_len = full_len

            # partikel api kerucut - 2 lapis luar/dalam
            for i in range(35):
                t = i / 35
                base_x = start_x + dir_x * flame_len * t
                base_y = start_y + dir_y * flame_len * t
                spread = t * 16 * fs
                offset = math.sin(phase * 4 + i * 1.7) * spread
                fxp = int(base_x + perp_x * offset)
                fyp = int(base_y + perp_y * offset)

                size = int((5 + t * 4) * fs)
                alpha = int(220 * (1 - t * 0.3))

                if t < 0.15:
                    color_outer = P["fire_white"]
                    color_inner = P["fire_glow"]
                elif t < 0.4:
                    color_outer = P["fire_hot"]
                    color_inner = P["fire_bright"]
                elif t < 0.75:
                    color_outer = P["fire_bright"]
                    color_inner = P["fire_mid"]
                else:
                    color_outer = P["fire_dark"]
                    color_inner = P["fire_darkest"]

                NS._aacircle(surface, (*color_outer, alpha), (fxp, fyp), size)
                NS._aacircle(surface, (*color_inner, alpha), (fxp, fyp),
                             max(1, size - 2))

            # asap tersapu di tepi kerucut
            for i in range(6):
                t = 0.35 + i * 0.11
                sxp = int(start_x + dir_x * flame_len * t +
                          perp_x * t * 22 * fs *
                          (1 if i % 2 == 0 else -1))
                syp = int(start_y + dir_y * flame_len * t +
                          perp_y * t * 22 * fs *
                          (1 if i % 2 == 0 else -1))
                NS._aacircle(surface, (*P["smoke_mid"], int(90 * (1 - t))),
                             (sxp, syp), int(4 * fs))

            # inti terang di muzzle
            NS._glow(surface, int(start_x), int(start_y), int(14 * fs),
                     P["fire_hot"], 200)
            NS._aacircle(surface, (*P["fire_white"], 255),
                         (int(start_x), int(start_y)), int(4 * fs))
            NS._aacircle(surface, (*P["fire_glow"], 255),
                         (int(start_x + dir_x * 5), int(start_y + dir_y * 5)),
                         int(3 * fs))

            # impact ring menyala di target
            it = 1 - abs(progress - 0.5) / 0.3
            it = max(0.0, min(1.0, it))
            ir = int((8 + it * 28) * fs)
            ia = int(230 * it)
            NS._glow(surface, tx, ty, int(26 * fs), P["fire_mid"],
                     int(140 * it))
            NS._ground_ring(surface, tx, ty, ir, P["fire_bright"],
                            P["fire_white"], ia, thickness=3, softness=7)
            NS._spark_star(surface, tx, ty, int(13 * fs * it),
                           P["fire_hot"], ia, spikes=6, rot=phase * 2,
                           core=P["fire_white"])

    # ===================================================================
    # SKILL R: FIRESTORM (pilar api di sekitar CASTER)
    # ===================================================================
    def _draw_firestorm(surface, boss, x, y, timer, phase):
        """Pilar api mengelilingi CASTER (AOE 180 dunia) + erupsi pusat."""
        duration = 90
        NS = _NS_razak
        P = NS.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / duration))
        fs = NS._fx_scale(boss)
        gy = y + NS.GROUND_DY

        # AKTIVASI: bintang saja (TANPA pilar cahaya)
        # Pilar 4-lapis setinggi 110 px di sumbu badan DIBUANG: kolom
        # itu menutupi Razak selama Firestorm di-cast.
        if progress < 0.14:
            k = progress / 0.14
            ease = 1 - (1 - k) ** 2
            NS._spark_star(surface, x, y - int(20 * fs), int(24 * fs),
                           P["fire_glow"], int(240 * (1 - ease * 0.4)),
                           spikes=8, rot=k * 3, core=P["fire_white"])

        if progress < 0.12:
            return

        # 8 pilar api mengorbit caster di radius telegraph.
        # Kolom api digambar lewat SPRITE ter-cache (_pillar_sprite) -
        # tanpa ratusan aacircle ber-alpha per frame; wobble besar tetap
        # kontinu lewat offset blit + phase-bucket kecil di sprite.
        r_orbit = NS._ring_r(boss, NS.SKILL_RADIUS["r"] * 0.62, surface)
        for i in range(8):
            angle = i * math.tau / 8 + phase * 0.15
            px = x + int(math.cos(angle) * r_orbit)
            py = gy + int(math.sin(angle) * r_orbit * 0.45)

            pillar_progress = (progress - 0.12 - i * 0.04) / 0.55
            if pillar_progress <= 0:
                continue
            pillar_progress = min(1.0, pillar_progress)

            if pillar_progress < 0.3:
                height_ratio = pillar_progress / 0.3
            elif pillar_progress < 0.7:
                height_ratio = 1.0
            else:
                height_ratio = 1.0 - (pillar_progress - 0.7) / 0.3

            pillar_h = int(64 * fs * height_ratio)
            if pillar_h <= 0:
                continue

            NS._draw_fire_pillar(surface, px, py, pillar_h,
                                 int(8 * fs), phase + i * 0.8)
            NS._aacircle(surface, (*P["fire_glow"], 240),
                         (px, py - pillar_h // 2), int(4 * fs))
            NS._aacircle(surface, (*P["fire_white"], 255),
                         (px, py - pillar_h // 3), int(3 * fs))
            # dasar pilar: glow + bara
            NS._glow(surface, px, py, int(12 * fs), P["fire_mid"], 150)
            for j in range(2):
                ea = phase * 2 + j * 3 + i
                ex = px + int(math.cos(ea) * 8 * fs)
                ey = py + int(math.sin(ea) * 3 * fs)
                NS._draw_ember(surface, ex, ey, 2, 200)

        # gelombang kejut susulan saat pilar meletus
        if progress > 0.15:
            ring_t = min(1.0, (progress - 0.15) / 0.35)
            ring_t = 1 - (1 - ring_t) ** 2
            rr = int((12 + ring_t * 55) * fs)
            ra = int(230 * (1 - ring_t * 0.4))
            NS._ground_ring(surface, x, gy, rr, P["fire_bright"],
                            P["fire_white"], ra, thickness=3, softness=8)
            NS._ground_ring(surface, x, gy, int(rr * 0.7), P["fire_hot"],
                            P["fire_glow"], int(ra * 0.6),
                            thickness=2, softness=6)

        # erupsi pusat: kolom api besar di caster + wisp spiral
        center_h = int(70 * fs * min(1.0, progress / 0.4) *
                       (1.0 if progress < 0.7 else
                        1 - (progress - 0.7) / 0.3))
        if center_h > 0:
            NS._draw_fire_pillar(surface, x, y + 8, center_h,
                                 int(9 * fs), phase * 0.9)
            NS._aacircle(surface, (*P["fire_glow"], 255),
                         (x, y + 8 - center_h // 2), int(5 * fs))
            NS._aacircle(surface, (*P["fire_white"], 255),
                         (x, y + 8 - center_h // 3), int(3 * fs))
            # wisp spiral 2 lengan naik mengelilingi kolom
            for arm in (0, math.pi):
                for k in range(4):
                    t = (phase * 0.5 + k / 4.0) % 1.0
                    a = arm + t * 5.0
                    wx = x + int(math.cos(a) * (12 + t * 10) * fs)
                    wy = y + 8 - int(t * center_h)
                    wa = int(190 * (1 - t))
                    if wa > 12:
                        NS._aacircle(surface, (*P["fire_hot"], wa),
                                     (wx, wy), max(1, int(2 * fs)))
    # ===================================================================
    # Backward compatible alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_razak.draw_razak(surface, boss, x, y)
