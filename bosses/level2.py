"""
bosses/level2.py - Semua boss Level 2

Gabungan dari 4 file terpisah:
  - razak                (mini boss)
  - khalros              (mini boss)
  - gorath               (mini boss)
  - alchemist            (TRUE BOSS)

Tiap boss dibungkus dalam kelas namespace `_NS_<nama>`
supaya PALETTE dan fungsi helper-nya TIDAK saling
menimpa - 91 simbol bentrok antar file boss, termasuk
PALETTE, _aacircle, _draw_shadow, _target_position.

Kode di dalam tiap namespace TIDAK diubah isinya;
hanya referensi antar-simbol yang diberi prefix.

Entry point publik ada di bagian paling bawah file.
"""

import math
import pygame

try:                     # pass cahaya bersama; opsional supaya file boss
    import lighting as _lighting          # tetap bisa di-load sendiri
except Exception:        # pragma: no cover
    _lighting = None

# Penanda: file ini berisi BANYAK boss (1 true + 3 mini).
# Dipakai heroes/__init__.py agar tidak menebak fungsi draw_*
# secara longgar, yang bisa mengembalikan boss yang salah.
_IS_LEVEL_BUNDLE = True



# ====================================================================
# RAZAK
# ====================================================================
class _NS_razak:
    """Namespace razak - PIXEL MASTERWORK v2 + SKILL FX v2.1.

    Rewrite penuh renderer `_NS_razak` mengikuti standar
    **Thorne v2 Pixel Masterwork + Thorne v2.1 Skill FX**
    (lihat docs/THORNE_V2_RENDERER.md) - pola yang sama dengan
    `_NS_gorath` di file ini. Tetap 100% prosedural: tidak ada
    PNG / sprite-sheet / image.load.

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

        # AKTIVASI: pilar cahaya 4-lapis + bintang (12 frame pertama)
        if progress < 0.14:
            k = progress / 0.14
            ease = 1 - (1 - k) ** 2
            ph = min(int(110 * fs), 230)
            top = y - ph
            for w, col, a in ((int(20 * fs), P["fire_dark"], 90),
                              (int(14 * fs), P["fire_bright"], 130),
                              (int(8 * fs), P["fire_hot"], 180),
                              (int(3 * fs), P["fire_white"], 240)):
                aa = int(a * (1 - ease * 0.5))
                NS._rect(surface, (*col, aa),
                         (x - w // 2, top, w, gy - top))
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


# ====================================================================
# KHALROS
# ====================================================================
class _NS_khalros:
    """Namespace khalros - isi asli tidak diubah."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    # ── ORIGINAL-MAX cache (piksel-identik, dibangun lazy) ──────────
    _shadow_cache = None
    _aura_cache = None
    _flash_buf = None
    _body_buf = None        # buffer badan untuk outline+lighting
    _record_shadow = None

    # ---------------------------------------------------------------------------
    # HD Palette - Rustic barbarian browns / orange fire
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin - rugged tan
        "skin_darkest":   (55,  30,  20),
        "skin_dark":      (115, 68,  45),
        "skin_mid":       (170, 108, 72),
        "skin_light":     (215, 158, 108),
        "skin_high":      (240, 200, 155),
        "skin_shine":     (255, 230, 195),

        # Hair - dark brown
        "hair_darkest":   (18,  12,   8),
        "hair_dark":      (48,  32,  20),
        "hair_mid":       (85,  58,  35),
        "hair_high":      (135, 95,  55),

        # Leather / clothing
        "leather_darkest": (25, 15,  8),
        "leather_dark":   (55,  32,  15),
        "leather_mid":    (95,  62,  32),
        "leather_light":  (150, 100, 55),
        "leather_high":   (200, 148, 88),

        # Metal (axes, buckles)
        "metal_darkest":  (18,  16,  18),
        "metal_dark":     (52,  48,  55),
        "metal_mid":      (105, 100, 108),
        "metal_light":    (170, 165, 175),
        "metal_shine":    (225, 220, 225),
        "metal_edge":     (250, 245, 250),

        # Gold accents
        "gold_dark":      (90,  60,  15),
        "gold_mid":       (170, 130, 40),
        "gold_light":     (230, 190, 80),
        "gold_shine":     (255, 230, 150),

        # Fire / rage - orange
        "fire_dark":      (75,  20,   5),
        "fire_mid":       (185, 60,  15),
        "fire_bright":    (235, 120, 30),
        "fire_hot":       (255, 180, 60),
        "fire_glow":      (255, 220, 130),
        "fire_white":     (255, 245, 200),

        # Red horns / warpaint
        "red_dark":       (85,  15,  12),
        "red_mid":        (170, 30,  25),
        "red_bright":     (225, 55,  45),
        "red_hot":        (255, 100, 80),

        # Beast fur - boar (dark brown)
        "boar_darkest":   (30,  18,  12),
        "boar_dark":      (65,  40,  22),
        "boar_mid":       (110, 72,  42),
        "boar_light":     (160, 110, 68),
        "boar_high":      (200, 150, 100),

        # Beast fur - wolf (gray)
        "wolf_darkest":   (25,  22,  25),
        "wolf_dark":      (55,  52,  58),
        "wolf_mid":       (95,  92, 100),
        "wolf_light":     (150, 148, 155),
        "wolf_high":      (200, 198, 205),

        # Hawk (brown/tan)
        "hawk_darkest":   (28,  18,  12),
        "hawk_dark":      (65,  42,  22),
        "hawk_mid":       (120, 78,  42),
        "hawk_light":     (175, 128, 78),
        "hawk_high":      (225, 180, 130),
        "hawk_beak":      (245, 210, 100),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (5,   3,   3),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_khalros._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_khalros.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_khalros._clamp(color)
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
        color = _NS_khalros._clamp(color)
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
        color = _NS_khalros._clamp(color)
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
        color = _NS_khalros._clamp(color)
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
        return int(x + 150 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM (Wild Axes + Hawk)
    # ---------------------------------------------------------------------------
    class AxeProjectile:
        """Spinning axe projectile."""
        def __init__(self, sx, sy, tx, ty, speed=7.0, facing=1):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.facing = facing
            self.alive = True
            self.age = 0
            self.spin = 0.0
            self.trail = []

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.spin += 0.55
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 8:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            # Trail (fire streak)
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(60 + i * 15)
                r = max(1, 4 - (len(self.trail) - i))
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_dark"], alpha), (tx, ty), r + 2)
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_bright"], alpha), (tx, ty), r)
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_hot"], alpha), (tx, ty), max(1, r - 1))

            if self.alive:
                px, py = int(self.x), int(self.y)
                _NS_khalros._draw_spinning_axe(surface, px, py, self.spin, size=1.0)

                # Fire glow
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_dark"], 120), (px, py), 12)
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_bright"], 80), (px, py), 8)


    class HawkProjectile:
        """Diving hawk projectile."""
        def __init__(self, sx, sy, tx, ty, speed=5.0):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.wing_phase = 0.0
            self.trail = []

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.wing_phase += 0.4
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < self.speed + 6:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 6:
                self.trail.pop(0)
            # Curve path slightly (predator style)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed + math.sin(self.age * 0.2) * 0.8

        def draw(self, surface, phase):
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 15)
                r = max(1, 3 - (len(self.trail) - i))
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["hawk_dark"], alpha), (tx, ty), r)

            if self.alive:
                dx = self.tx - self.x
                facing = 1 if dx > 0 else -1
                _NS_khalros._draw_flying_hawk(surface, int(self.x), int(self.y),
                                  facing, self.wing_phase, size=1.0)


    def _draw_spinning_axe(surface, cx, cy, spin, size=1.0):
        """A thrown axe that spins."""
        handle_len = int(10 * size)
        head_size = int(7 * size)

        # Handle
        ex = cx + int(math.cos(spin) * handle_len)
        ey = cy + int(math.sin(spin) * handle_len)
        hx = cx - int(math.cos(spin) * handle_len * 0.5)
        hy = cy - int(math.sin(spin) * handle_len * 0.5)

        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_darkest"], (hx, hy), (ex, ey), 4)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_dark"], (hx, hy), (ex, ey), 3)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_mid"], (hx, hy), (ex, ey), 1)

        # Axe head
        perp_x = -math.sin(spin)
        perp_y = math.cos(spin)

        axe_pts = [
            (ex + int(perp_x * head_size), ey + int(perp_y * head_size)),
            (ex + int(math.cos(spin) * head_size * 0.6) + int(perp_x * head_size * 0.6),
             ey + int(math.sin(spin) * head_size * 0.6) + int(perp_y * head_size * 0.6)),
            (ex + int(math.cos(spin) * head_size * 0.6) - int(perp_x * head_size * 0.6),
             ey + int(math.sin(spin) * head_size * 0.6) - int(perp_y * head_size * 0.6)),
            (ex - int(perp_x * head_size), ey - int(perp_y * head_size)),
            (ex - int(math.cos(spin) * head_size * 0.3), ey - int(math.sin(spin) * head_size * 0.3)),
        ]
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_darkest"], axe_pts)
        # Inner brighter
        inner_pts = [
            (ex + int(perp_x * (head_size - 2)), ey + int(perp_y * (head_size - 2))),
            (ex, ey),
            (ex - int(perp_x * (head_size - 2)), ey - int(perp_y * (head_size - 2))),
        ]
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_mid"], inner_pts)

        # Sharp edge
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["metal_shine"],
                (ex + int(perp_x * head_size), ey + int(perp_y * head_size)),
                (ex - int(perp_x * head_size), ey - int(perp_y * head_size)), 1)

        # Fire trailing on axe
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_bright"], 200), (ex, ey), 3)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_hot"], 220), (ex, ey), 1)


    def _draw_flying_hawk(surface, cx, cy, facing, wing_phase, size=1.0):
        """Draw a hawk in flight."""
        wing_y_off = int(math.sin(wing_phase) * 5)

        # Body
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["shadow_deep"], (cx + 1, cy + 1), int(5 * size))
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["hawk_darkest"], (cx, cy), int(5 * size))
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["hawk_dark"], (cx - 1, cy - 1), int(4 * size))
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["hawk_mid"], (cx - 1, cy - 1), int(3 * size))
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["hawk_light"], (cx - 2, cy - 2), int(2 * size))

        # Head (small, forward)
        hx = cx + int(4 * facing * size)
        hy = cy - 1
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["hawk_dark"], (hx, hy), int(3 * size))
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["hawk_mid"], (hx, hy), int(2 * size))
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["hawk_light"], (hx - int(facing), hy - 1), 1)

        # Beak
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hawk_beak"], [
            (hx + int(3 * facing), hy),
            (hx + int(6 * facing), hy + 1),
            (hx + int(3 * facing), hy + 2),
        ])

        # Eye
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["fire_hot"], (hx + int(facing), hy - 1), 1)

        # Wings (top view / spread)
        # Upper wing
        wing_upper = [
            (cx, cy - 2),
            (cx - int(12 * size), cy - 4 + wing_y_off),
            (cx - int(9 * size), cy + wing_y_off),
            (cx, cy + 1),
        ]
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hawk_darkest"], wing_upper)
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hawk_dark"], [
            (cx, cy - 1),
            (cx - int(10 * size), cy - 2 + wing_y_off),
            (cx - int(7 * size), cy + 1 + wing_y_off),
            (cx, cy + 1),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hawk_mid"], [
            (cx, cy),
            (cx - int(7 * size), cy - 1 + wing_y_off),
            (cx - int(5 * size), cy + 1 + wing_y_off),
        ])

        # Lower / other wing
        wing_lower = [
            (cx, cy - 1),
            (cx + int(10 * size) * facing - int(3 * facing), cy - 3 - wing_y_off),
            (cx + int(7 * size) * facing - int(2 * facing), cy - wing_y_off),
            (cx, cy + 1),
        ]
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hawk_darkest"], wing_lower)
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hawk_dark"], [
            (cx, cy),
            (cx + int(8 * size) * facing - int(3 * facing), cy - 1 - wing_y_off),
            (cx + int(5 * size) * facing - int(2 * facing), cy + 1 - wing_y_off),
        ])

        # Tail feathers
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hawk_dark"], [
            (cx - int(3 * facing), cy + 1),
            (cx - int(7 * facing), cy + 3),
            (cx - int(5 * facing), cy + 1),
        ])


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_khal_last_x"):
            boss._khal_last_x = boss.x
            boss._khal_last_y = boss.y
            return False
        dx = abs(boss.x - boss._khal_last_x)
        dy = abs(boss.y - boss._khal_last_y)
        boss._khal_last_x = boss.x
        boss._khal_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_khal_prev_timer", 0))
        active = bool(getattr(boss, "_khal_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._khal_attack_active = True
            boss._khal_attack_frame = 0
            active = True
        elif active:
            boss._khal_attack_frame = int(getattr(boss, "_khal_attack_frame", 0)) + 1
            if boss._khal_attack_frame > cooldown:
                boss._khal_attack_active = False
                boss._khal_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._khal_attack_active = False
            boss._khal_attack_frame = 0
            active = False

        boss._khal_prev_timer = timer
        boss._khal_attack_progress = (
            min(1.0, getattr(boss, "_khal_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_khal_projectiles"):
            boss._khal_projectiles = []
        for proj in boss._khal_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._khal_projectiles = [p for p in boss._khal_projectiles
                                   if p.alive or p.age < 5]


    def _spawn_axe(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_khal_projectiles"):
            boss._khal_projectiles = []
        boss._khal_projectiles.append(
            _NS_khalros.AxeProjectile(sx, sy, tx, ty, speed=7.0, facing=boss.direction))


    def _spawn_hawk(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_khal_projectiles"):
            boss._khal_projectiles = []
        boss._khal_projectiles.append(_NS_khalros.HawkProjectile(sx, sy, tx, ty, speed=5.5))


    # ===================================================================
    # MAIN ENTRY
    # ===================================================================
    def draw_khalros(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_khalros._detect_moving(boss)
        _NS_khalros._update_attack_anim(boss)
        # ekspos state bergerak ke lapisan FX hidup (heroes/khalros_fx)
        try:
            boss._khal_moving = moving
        except Exception:
            pass

        attacking = (
            getattr(boss, "_khal_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 45) - 15
        )

        _NS_khalros._draw_primal_aura(surface, x, y, pulse, active_skill)
        _NS_khalros._draw_ground_runes(surface, x, y + 40, pulse, active_skill)

        # Ground skill effects
        if active_skill == "w":
            _NS_khalros._draw_call_of_wild_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_khalros._draw_boar_ground(surface, boss, x, y, skill_timer, pulse)

        # PERTAGAS: gelombang kejut aktivasi skill (12 frame pertama)
        if active_skill in ("q", "w", "e", "r"):
            dur = {"q": 50, "w": 60, "e": 45, "r": 70}[active_skill]
            age = dur - skill_timer
            if 0 <= age < 12:
                _NS_khalros._draw_shockwave(surface, x, y + 48, age, 12,
                                            _NS_khalros.PALETTE["fire_hot"],
                                            _NS_khalros.PALETTE["fire_glow"])

        # ────────────────────────────────────────────────────────────
        # LAPISAN FX HIDUP KHALROS (heroes/khalros_fx.py)
        # Render badan prosedural + swing trail + proyektil + skill FX +
        # partikel + impact + screen-shake + hit-stop hidup di sini,
        # di luar cache sprite supaya tetap 60 fps. Bila modul tak
        # tersedia / gagal, kode inline di bawah tetap jalan (fallback
        # aman - game tidak ikut rusak).
        # ────────────────────────────────────────────────────────────
        try:
            from heroes import khalros_fx as _kfx
            if _kfx.KHALROS_FX_ENABLED and _kfx.render_khalros(
                    surface, boss, x, y):
                return
        except Exception:
            pass

        # ORIGINAL-MAX hurt flash: badan dibanjiri putih-hangat, bayangan
        # tanah tidak ikut menyala (rect shadow direkam lalu dikeluarkan).
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        _tgt, _tx, _ty = surface, x, y
        if flash > 0:
            B = _NS_khalros
            if B._flash_buf is None:
                B._flash_buf = pygame.Surface((240, 260), pygame.SRCALPHA)
            B._flash_buf.fill((0, 0, 0, 0))
            B._record_shadow = []
            _tgt, _tx, _ty = B._flash_buf, 120, 135

        # Character
        if attacking:
            _NS_khalros._draw_khalros_attack(_tgt, boss, _tx, _ty)
        elif moving:
            _NS_khalros._draw_khalros_walk(_tgt, boss, _tx, _ty)
        else:
            _NS_khalros._draw_khalros_idle(_tgt, boss, _tx, _ty)

        if flash > 0:
            B = _NS_khalros
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

        _NS_khalros._manage_projectiles(boss, surface, pulse)

        # Foreground skill effects
        if active_skill == "q":
            _NS_khalros._draw_wild_axes(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_khalros._draw_call_of_wild(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_khalros._draw_boar_charge(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_khalros._draw_hawk_summon(surface, boss, x, y, skill_timer, pulse)


    def _draw_shockwave(surface, x, y, age, total, c1, c2):
        """Gelombang kejut aktivasi skill - 12 frame pertama."""
        t = age / float(total)
        ease = 1 - (1 - t) ** 2
        r = int(14 + ease * 58)
        a = max(0, min(255, int(235 * (1 - t))))
        pygame.draw.ellipse(surface, (*c1, a),
                            (x - r, y - r // 3, r * 2, r * 2 // 3), 2)
        pygame.draw.ellipse(surface, (*c2, a),
                            (x - r // 2, y - r // 6, r, r // 3), 1)
        ri = max(3, r // 2)
        _NS_khalros._aacircle(surface, (*c1, int(a * 0.8)),
                              (x, y - (r // 6)), ri)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_khalros_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        _NS_khalros._draw_shadow(surface, x, y + 48)
        _NS_khalros._draw_wild_wisps(surface, x, y + 32, boss.pulse)
        _NS_khalros._draw_khalros_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_khalros_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(abs(math.sin(phase * 1.3)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_khalros._draw_shadow(surface, x + sway, y + 48)
        _NS_khalros._draw_wild_wisps(surface, x + sway, y + 32, phase, trail=True,
                         facing=boss.direction)
        _NS_khalros._draw_khalros_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_khalros_attack(surface, boss, x, y):
        progress = getattr(boss, "_khal_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        lunge = int(math.sin(progress * math.pi) * 5) * boss.direction

        _NS_khalros._draw_shadow(surface, x + lunge, y + 48)
        _NS_khalros._draw_wild_wisps(surface, x + lunge, y + 32, boss.pulse, intense=True)
        _NS_khalros._draw_khalros_body(surface, x + lunge, y, boss.direction, boss.pulse,
                           "attack", progress)
        _NS_khalros._draw_axe_swing_arc(surface, x + lunge, y, boss.direction, progress)
        _NS_khalros._draw_swing_impact(surface, x + lunge, y, boss.direction, progress)


    # ===================================================================
    # BODY RENDERING
    # ===================================================================
    def _draw_khalros_body_raw(surface, cx, cy, facing, phase, action, attack_progress=0):
        sway = int(math.sin(phase * 0.6) * (2 if action != "idle" else 1))

        _NS_khalros._draw_loincloth(surface, cx, cy + 8, phase, sway)
        _NS_khalros._draw_torso(surface, cx, cy - 5, phase, sway)
        _NS_khalros._draw_shoulders(surface, cx, cy - 12, phase)

        if action == "attack":
            _NS_khalros._draw_attack_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        else:
            _NS_khalros._draw_idle_arms(surface, cx, cy - 8, facing, phase)

        _NS_khalros._draw_khalros_head(surface, cx, cy - 26, facing, phase)

    def _draw_khalros_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Komposit ORIGINAL-MAX: badan -> buffer tetap -> outline siluet
        gelap 1 px + pass pencahayaan (rim/shade) -> blit posisi dunia sama."""
        NS = _NS_khalros
        B = 200
        if NS._body_buf is None:
            NS._body_buf = pygame.Surface((B, B), pygame.SRCALPHA)
        buf = NS._body_buf
        buf.fill((0, 0, 0, 0))
        NS._draw_khalros_body_raw(buf, B // 2, B // 2, facing, phase, action, attack_progress)
        used = buf.get_bounding_rect(min_alpha=1)
        if used.width <= 2 or used.height <= 2:
            return
        used.inflate_ip(4, 4)
        used.clamp_ip(buf.get_rect())
        sub = buf.subsurface(used).copy()
        ox = int(cx) - (B // 2) + used.left
        oy = int(cy) - (B // 2) + used.top
        edge = sub.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(edge, (ox + ddx, oy + ddy))
        if _lighting is not None:
            _lighting.apply_to_rig(sub, rim_add=(40, 28, 16), shade_mul=168)
        surface.blit(sub, (ox, oy))


    def _draw_loincloth(surface, cx, cy, phase, sway):
        """Tattered fur / leather loincloth."""
        # Belt
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["leather_darkest"], (cx - 16, cy - 4, 32, 7))
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["leather_dark"], (cx - 15, cy - 3, 30, 5))
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["leather_mid"], (cx - 14, cy - 2, 28, 3))

        # Belt buckle - gold beast head
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["gold_dark"], (cx, cy - 1), 5)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["gold_mid"], (cx, cy - 1), 4)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["gold_light"], (cx - 1, cy - 2), 2)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["gold_shine"], (cx - 1, cy - 2), 1)
        # Buckle horns
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["gold_dark"], [
            (cx - 5, cy - 2), (cx - 7, cy - 5), (cx - 3, cy - 3),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["gold_dark"], [
            (cx + 5, cy - 2), (cx + 7, cy - 5), (cx + 3, cy - 3),
        ])

        # Fur strips
        for i, offset in enumerate([-12, -6, 0, 6, 12]):
            wave = math.sin(phase * 1.2 + i) * 2
            length = 22 + (i % 2) * 3

            # Base strip
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["shadow_deep"], [
                (cx + offset - 4, cy + 3),
                (cx + offset + 4, cy + 3),
                (cx + offset + 3 + int(wave), cy + length),
                (cx + offset - 3 + int(wave), cy + length),
            ])
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["leather_darkest"], [
                (cx + offset - 4, cy + 2),
                (cx + offset + 4, cy + 2),
                (cx + offset + 3 + int(wave), cy + length - 1),
                (cx + offset - 3 + int(wave), cy + length - 1),
            ])
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["leather_dark"], [
                (cx + offset - 3, cy + 3),
                (cx + offset + 3, cy + 3),
                (cx + offset + 2 + int(wave), cy + length - 3),
                (cx + offset - 2 + int(wave), cy + length - 3),
            ])
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["leather_mid"], [
                (cx + offset - 2, cy + 4),
                (cx + offset + 2, cy + 4),
                (cx + offset + 1 + int(wave), cy + length - 5),
                (cx + offset - 1 + int(wave), cy + length - 5),
            ])
            # Fur tuft highlight
            _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_high"],
                    (cx + offset, cy + 5),
                    (cx + offset + int(wave * 0.5), cy + length - 6), 1)


    def _draw_torso(surface, cx, cy, phase, sway):
        """Muscular torso with leather chest strap."""
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["shadow_deep"], [
            (cx - 14 + 2, cy - 8 + 2), (cx + 14 + 2, cy - 8 + 2),
            (cx + 13 + 2, cy + 14 + 2), (cx + 6 + 2, cy + 18 + 2),
            (cx - 6 + 2, cy + 18 + 2), (cx - 13 + 2, cy + 14 + 2),
        ])

        torso = [
            (cx - 14, cy - 8), (cx + 14, cy - 8),
            (cx + 13, cy + 14), (cx + 6, cy + 18),
            (cx - 6, cy + 18), (cx - 13, cy + 14),
        ]
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["skin_darkest"], torso)
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["skin_dark"], [
            (cx - 12, cy - 7), (cx + 12, cy - 7),
            (cx + 11, cy + 12), (cx + 5, cy + 16),
            (cx - 5, cy + 16), (cx - 11, cy + 12),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["skin_mid"], [
            (cx - 9, cy - 5), (cx + 9, cy - 5),
            (cx + 8, cy + 10), (cx + 3, cy + 14),
            (cx - 3, cy + 14), (cx - 8, cy + 10),
        ])

        # Chest highlights (pectorals)
        for side in (-1, 1):
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_light"],
                      (cx + side * 5, cy - 2), 4)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_high"],
                      (cx + side * 5 - 1, cy - 3), 2)

        # Abs
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["skin_darkest"], (cx, cy + 2), (cx, cy + 14), 1)
        for yoff in (4, 8, 12):
            _NS_khalros._aaline(surface, _NS_khalros.PALETTE["skin_darkest"],
                    (cx - 5, cy + yoff), (cx + 5, cy + yoff), 1)

        # Leather chest strap (diagonal)
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["leather_darkest"], [
            (cx - 12, cy - 4), (cx - 9, cy - 6),
            (cx + 12, cy + 10), (cx + 9, cy + 12),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["leather_dark"], [
            (cx - 11, cy - 4), (cx - 9, cy - 5),
            (cx + 11, cy + 9), (cx + 9, cy + 10),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["leather_mid"], [
            (cx - 10, cy - 3), (cx - 9, cy - 4),
            (cx + 10, cy + 8), (cx + 9, cy + 9),
        ])

        # Chest emblem - beast head badge
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["leather_darkest"], (cx - 4, cy + 4, 8, 9),
              border_radius=2)
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["leather_dark"], (cx - 3, cy + 5, 6, 7),
              border_radius=1)
        # Red beast face
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["red_dark"], (cx, cy + 8), 3)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["red_mid"], (cx, cy + 8), 2)
        # Beast horns
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["red_mid"], (cx - 3, cy + 6, 1, 2))
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["red_mid"], (cx + 2, cy + 6, 1, 2))


    def _draw_shoulders(surface, cx, cy, phase):
        """Muscular shoulders with fur pauldrons."""
        for side in (-1, 1):
            sx = cx + side * 14
            # Shadow
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["shadow_deep"], (sx + 2, cy + 2), 10)

            # Fur pauldron (spiky)
            for i in range(4):
                fx = sx + side * (i - 2) - side * 3
                fy = cy - 4 + (i % 2) * 2
                _NS_khalros._poly(surface, _NS_khalros.PALETTE["leather_darkest"], [
                    (fx - 3, fy + 3),
                    (fx + 3, fy + 3),
                    (fx + int(math.sin(phase * 0.5 + i) * 1), fy - 4),
                ])
                _NS_khalros._poly(surface, _NS_khalros.PALETTE["leather_dark"], [
                    (fx - 2, fy + 3),
                    (fx + 2, fy + 3),
                    (fx + int(math.sin(phase * 0.5 + i) * 1), fy - 3),
                ])
                _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_high"],
                        (fx, fy + 2), (fx, fy - 3), 1)

            # Shoulder muscle
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_darkest"], (sx, cy + 2), 8)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_dark"], (sx - side, cy + 1), 7)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_mid"], (sx - side * 2, cy), 5)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_light"], (sx - side * 3, cy - 1), 3)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_high"], (sx - side * 3, cy - 2), 1)

            # Metal band on upper arm
            _NS_khalros._rect(surface, _NS_khalros.PALETTE["metal_darkest"], (sx - 5, cy + 4, 10, 3),
                  border_radius=1)
            _NS_khalros._rect(surface, _NS_khalros.PALETTE["metal_mid"], (sx - 4, cy + 5, 8, 1))
            _NS_khalros._rect(surface, _NS_khalros.PALETTE["gold_mid"], (sx - 1, cy + 5, 2, 1))


    def _draw_khalros_head(surface, cx, cy, facing, phase):
        """Barbarian head with horned helm and beard."""
        # Neck
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["skin_darkest"], (cx - 4, cy + 8, 8, 6))
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["skin_dark"], (cx - 3, cy + 8, 6, 5))
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["skin_mid"], (cx - 2, cy + 8, 4, 3))

        # Head shadow
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["shadow_deep"], (cx + 2, cy + 2), 12)

        # Head base
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_darkest"], (cx, cy), 11)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_dark"], (cx - 1, cy - 1), 9)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_mid"], (cx - 2, cy - 2), 7)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_light"], (cx - 3, cy - 4), 3)

        # Beard (bushy, lower half of face)
        beard = [
            (cx - 9, cy + 1),
            (cx - 10, cy + 6),
            (cx - 6, cy + 12),
            (cx, cy + 14),
            (cx + 6, cy + 12),
            (cx + 10, cy + 6),
            (cx + 9, cy + 1),
        ]
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hair_darkest"], beard)
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hair_dark"], [
            (cx - 8, cy + 2),
            (cx - 9, cy + 6),
            (cx - 5, cy + 11),
            (cx, cy + 13),
            (cx + 5, cy + 11),
            (cx + 9, cy + 6),
            (cx + 8, cy + 2),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["hair_mid"], [
            (cx - 6, cy + 3),
            (cx - 6, cy + 6),
            (cx - 3, cy + 10),
            (cx, cy + 11),
            (cx + 3, cy + 10),
            (cx + 6, cy + 6),
            (cx + 6, cy + 3),
        ])

        # Beard hair strands highlight
        for xoff in (-5, -2, 2, 5):
            _NS_khalros._aaline(surface, _NS_khalros.PALETTE["hair_high"],
                    (cx + xoff, cy + 4), (cx + xoff, cy + 10), 1)

        # Fierce eyes (small red glow)
        for side in (-1, 1):
            ex = cx + side * 3
            ey = cy - 1
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["shadow_deep"], (ex, ey), 2)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["red_dark"], (ex, ey), 1)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["red_hot"], (ex, ey), 1)
            # Angry eyebrow above
            _NS_khalros._aaline(surface, _NS_khalros.PALETTE["hair_darkest"],
                    (ex - 2, ey - 3), (ex + 2, ey - 2), 2)

        # Nose
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["skin_dark"], [
            (cx, cy + 1),
            (cx - 2, cy + 4),
            (cx + 2, cy + 4),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["skin_mid"], [
            (cx, cy + 2),
            (cx - 1, cy + 4),
            (cx + 1, cy + 4),
        ])

        # HELM with horns (Beastmaster signature)
        _NS_khalros._draw_helm(surface, cx, cy - 5, phase)

        # Red war paint stripe on forehead
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["red_dark"], (cx - 4, cy - 4, 8, 2))
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["red_bright"], (cx - 3, cy - 4, 6, 1))


    def _draw_helm(surface, cx, cy, phase):
        """Horned barbarian helm."""
        # Helm cap
        helm = [
            (cx - 11, cy + 2),
            (cx - 9, cy - 4),
            (cx - 3, cy - 7),
            (cx + 3, cy - 7),
            (cx + 9, cy - 4),
            (cx + 11, cy + 2),
        ]
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["shadow_deep"], [(p[0] + 1, p[1] + 1) for p in helm])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_darkest"], helm)
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_dark"], [
            (cx - 10, cy + 1),
            (cx - 8, cy - 3),
            (cx - 3, cy - 6),
            (cx + 3, cy - 6),
            (cx + 8, cy - 3),
            (cx + 10, cy + 1),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_mid"], [
            (cx - 8, cy),
            (cx - 6, cy - 3),
            (cx - 2, cy - 5),
            (cx + 2, cy - 5),
            (cx + 6, cy - 3),
            (cx + 8, cy),
        ])
        # Helm highlight
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["metal_light"],
                (cx - 5, cy - 4), (cx + 5, cy - 4), 1)

        # Gold trim rim
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["gold_mid"], (cx - 11, cy + 2), (cx + 11, cy + 2), 1)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["gold_light"], (cx - 10, cy + 2), (cx + 10, cy + 2), 1)

        # HORNS (huge bull-like horns going outward)
        for side in (-1, 1):
            # Horn base
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["shadow_deep"], [
                (cx + side * 8 + 1, cy - 3 + 1),
                (cx + side * 16 + 1, cy - 8 + 1),
                (cx + side * 20 + 1, cy - 4 + 1),
                (cx + side * 15 + 1, cy - 1 + 1),
            ])
            # Main horn
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["hair_darkest"], [
                (cx + side * 8, cy - 3),
                (cx + side * 16, cy - 8),
                (cx + side * 20, cy - 4),
                (cx + side * 15, cy - 1),
            ])
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["hair_dark"], [
                (cx + side * 9, cy - 3),
                (cx + side * 15, cy - 7),
                (cx + side * 18, cy - 4),
                (cx + side * 14, cy - 1),
            ])
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["bone_dark" if False else "leather_high"], [
                (cx + side * 10, cy - 3),
                (cx + side * 14, cy - 6),
                (cx + side * 16, cy - 4),
                (cx + side * 13, cy - 2),
            ]) if False else None

            # Highlight on horn
            _NS_khalros._aaline(surface, _NS_khalros.PALETTE["hair_mid"],
                    (cx + side * 10, cy - 4),
                    (cx + side * 18, cy - 5), 1)

            # Horn tip (sharper, lighter)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["hair_high"], (cx + side * 20, cy - 4), 1)

        # HAIR (spiky mohawk between horns)
        for i in range(3):
            sx = cx - 3 + i * 3
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["hair_darkest"], [
                (sx - 2, cy - 6),
                (sx + 2, cy - 6),
                (sx + int(math.sin(phase * 0.3 + i) * 1), cy - 13),
            ])
            _NS_khalros._poly(surface, _NS_khalros.PALETTE["hair_dark"], [
                (sx - 1, cy - 6),
                (sx + 1, cy - 6),
                (sx + int(math.sin(phase * 0.3 + i) * 1), cy - 12),
            ])


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Arms holding axes at ready."""
        sway = math.sin(phase * 0.7) * 2
        for side in (-1, 1):
            sh_x = cx + side * 13
            sh_y = cy + 2
            elbow_x = sh_x + side * 10
            elbow_y = cy + 12 + int(sway)
            hand_x = elbow_x + side * 6
            hand_y = elbow_y + 10

            _NS_khalros._draw_arm_segment(surface, sh_x, sh_y, elbow_x, elbow_y)
            _NS_khalros._draw_arm_segment(surface, elbow_x, elbow_y, hand_x, hand_y)
            _NS_khalros._draw_hand(surface, hand_x, hand_y)
            # Axe held vertically
            _NS_khalros._draw_axe_held(surface, hand_x, hand_y, side, phase)


    def _draw_attack_arms(surface, cx, cy, facing, phase, progress):
        """One arm swings axe."""

        # Back arm - just holds axe
        back_side = -facing
        bs_x = cx + back_side * 13
        bs_y = cy + 2
        be_x = bs_x + back_side * 8
        be_y = cy + 12
        bh_x = be_x + back_side * 6
        bh_y = be_y + 9
        _NS_khalros._draw_arm_segment(surface, bs_x, bs_y, be_x, be_y)
        _NS_khalros._draw_arm_segment(surface, be_x, be_y, bh_x, bh_y)
        _NS_khalros._draw_hand(surface, bh_x, bh_y)
        _NS_khalros._draw_axe_held(surface, bh_x, bh_y, back_side, phase)

        # Front arm swings
        fs_x = cx + facing * 13
        fs_y = cy + 2

        if progress < 0.25:
            # Wind up
            t = progress / 0.25
            t = t * t * (3 - 2 * t)
            arm_angle = -1.4 + 0.2 * t
        elif progress < 0.55:
            # Swing
            t = (progress - 0.25) / 0.30
            t = 1 - (1 - t) ** 3
            arm_angle = -1.2 + 2.4 * t
        else:
            # Recovery
            t = (progress - 0.55) / 0.45
            arm_angle = 1.2 - 0.9 * t

        arm_len = 16
        fe_x = fs_x + int(math.cos(arm_angle) * arm_len) * facing
        fe_y = fs_y + int(math.sin(arm_angle) * arm_len)
        fh_x = fe_x + int(math.cos(arm_angle) * 10) * facing
        fh_y = fe_y + int(math.sin(arm_angle) * 10)

        _NS_khalros._draw_arm_segment(surface, fs_x, fs_y, fe_x, fe_y)
        _NS_khalros._draw_arm_segment(surface, fe_x, fe_y, fh_x, fh_y)
        _NS_khalros._draw_hand(surface, fh_x, fh_y)

        # Large swinging axe
        axe_angle = arm_angle + math.pi / 4 * facing
        _NS_khalros._draw_axe_swinging(surface, fh_x, fh_y, facing, axe_angle, size=1.2)


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["shadow_deep"], (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 8)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["skin_darkest"], (x1, y1), (x2, y2), 7)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["skin_dark"], (x1, y1), (x2, y2), 5)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["skin_mid"], (x1, y1), (x2, y2), 3)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["skin_light"], (x1 - 1, y1), (x2 - 1, y2), 1)


    def _draw_hand(surface, x, y):
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["shadow_deep"], (x + 1, y + 1), 5)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_darkest"], (x, y), 4)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_dark"], (x, y), 3)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["skin_mid"], (x - 1, y - 1), 2)
        # Leather wrap
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["leather_dark"], (x - 4, y - 5, 8, 3),
              border_radius=1)
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["leather_mid"], (x - 3, y - 5, 6, 1))
        _NS_khalros._rect(surface, _NS_khalros.PALETTE["red_mid"], (x - 3, y - 4, 6, 1))


    def _draw_axe_held(surface, hx, hy, side, phase):
        """Axe held vertically at rest."""
        # Handle (down from hand)
        handle_bot_x = hx + int(side * 1)
        handle_bot_y = hy + 16
        handle_top_y = hy - 12

        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["shadow_deep"],
                (hx + 1, handle_top_y + 1), (handle_bot_x + 1, handle_bot_y + 1), 4)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_darkest"],
                (hx, handle_top_y), (handle_bot_x, handle_bot_y), 3)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_dark"],
                (hx, handle_top_y), (handle_bot_x, handle_bot_y), 2)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_mid"],
                (hx, handle_top_y), (handle_bot_x, handle_bot_y), 1)

        # Red wrap on handle
        for i in range(3):
            wy = hy - 6 + i * 5
            _NS_khalros._rect(surface, _NS_khalros.PALETTE["red_dark"], (hx - 2, wy, 4, 2))
            _NS_khalros._rect(surface, _NS_khalros.PALETTE["red_mid"], (hx - 1, wy, 3, 1))

        # Axe head at top
        ax = hx
        ay = handle_top_y

        # Main axe head (large curved blade)
        head_pts = [
            (ax - side * 2, ay + 2),
            (ax - side * 8, ay - 2),
            (ax - side * 10, ay - 6),
            (ax - side * 8, ay - 10),
            (ax - side * 3, ay - 8),
            (ax, ay - 4),
        ]
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["shadow_deep"],
              [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_darkest"], head_pts)
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_dark"], [
            (ax - side * 3, ay + 1),
            (ax - side * 7, ay - 2),
            (ax - side * 9, ay - 6),
            (ax - side * 7, ay - 9),
            (ax - side * 3, ay - 7),
            (ax - side * 1, ay - 4),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_mid"], [
            (ax - side * 4, ay),
            (ax - side * 6, ay - 3),
            (ax - side * 7, ay - 6),
            (ax - side * 6, ay - 8),
            (ax - side * 4, ay - 7),
        ])

        # Sharp edge highlight
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["metal_shine"],
                (ax - side * 8, ay - 2), (ax - side * 8, ay - 10), 1)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["metal_edge"],
                (ax - side * 9, ay - 6), (ax - side * 9, ay - 8), 1)

        # Handle top cap
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["metal_darkest"], (ax, ay - 1), 2)
        _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["metal_mid"], (ax, ay - 1), 1)


    def _draw_axe_swinging(surface, hx, hy, facing, angle, size=1.0):
        """Big axe in motion — angled."""
        handle_len = int(20 * size)
        dx = math.cos(angle) * facing
        dy = math.sin(angle)

        # Handle from hand to axe head
        head_x = hx + int(dx * handle_len)
        head_y = hy + int(dy * handle_len)

        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["shadow_deep"],
                (hx + 2, hy + 2), (head_x + 2, head_y + 2), 5)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_darkest"], (hx, hy), (head_x, head_y), 4)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_dark"], (hx, hy), (head_x, head_y), 3)
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["leather_mid"], (hx, hy), (head_x, head_y), 1)

        # Red wraps
        for i in range(3):
            t = 0.3 + i * 0.2
            wx = hx + int(dx * handle_len * t)
            wy = hy + int(dy * handle_len * t)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["red_dark"], (wx, wy), 2)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["red_mid"], (wx, wy), 1)

        # Axe head
        perp_x = -math.sin(angle)
        perp_y = math.cos(angle) * facing
        head_size = int(11 * size)

        head_pts = [
            (head_x + int(perp_x * head_size), head_y + int(perp_y * head_size)),
            (head_x + int(dx * head_size * 0.4) + int(perp_x * head_size * 0.9),
             head_y + int(dy * head_size * 0.4) + int(perp_y * head_size * 0.9)),
            (head_x + int(dx * head_size * 0.4) - int(perp_x * head_size * 0.9),
             head_y + int(dy * head_size * 0.4) - int(perp_y * head_size * 0.9)),
            (head_x - int(perp_x * head_size), head_y - int(perp_y * head_size)),
            (head_x - int(dx * head_size * 0.3), head_y - int(dy * head_size * 0.3)),
        ]

        _NS_khalros._poly(surface, _NS_khalros.PALETTE["shadow_deep"], [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_darkest"], head_pts)
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_dark"], [
            (head_x + int(perp_x * (head_size - 2)), head_y + int(perp_y * (head_size - 2))),
            (head_x + int(dx * head_size * 0.3), head_y + int(dy * head_size * 0.3)),
            (head_x - int(perp_x * (head_size - 2)), head_y - int(perp_y * (head_size - 2))),
        ])
        _NS_khalros._poly(surface, _NS_khalros.PALETTE["metal_mid"], [
            (head_x + int(perp_x * (head_size - 4)), head_y + int(perp_y * (head_size - 4))),
            (head_x, head_y),
            (head_x - int(perp_x * (head_size - 4)), head_y - int(perp_y * (head_size - 4))),
        ])

        # Sharp edge highlight
        _NS_khalros._aaline(surface, _NS_khalros.PALETTE["metal_shine"],
                (head_x + int(perp_x * head_size), head_y + int(perp_y * head_size)),
                (head_x - int(perp_x * head_size), head_y - int(perp_y * head_size)), 1)

        # Fire aura on head
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_bright"], 150), (head_x, head_y), 4)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_hot"], 180), (head_x, head_y), 2)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_wild_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Primal dust wisps."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(30, 3, -4):
            alpha = int((30 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_khalros.PALETTE["leather_darkest"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising fire/energy wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 24)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_dark"], alpha), (sx, sy), 5)
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_bright"], alpha), (sx, sy - 2), 3)
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_hot"], alpha), (sx, sy - 3), 1)

        # Ember particles
        for i in range(5):
            angle = phase * 0.9 + i * math.pi * 2 / 5
            r = 22 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 8)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["fire_bright"], (sx, sy), 2)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["fire_hot"], (sx, sy), 1)

        if trail:
            for i in range(4):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 130 - i * 22)
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["leather_dark"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y, lift=0):
        # ORIGINAL-MAX: cache tekstur + reaktif (menyusut saat badan
        # terangkat, dasar tetap menapak tanah).
        NS = _NS_khalros
        if NS._shadow_cache is None:
            shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
            for radius in range(10, 0, -1):
                alpha = max(0, (10 - radius) * 16)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
                )
            pygame.draw.ellipse(shadow, (*NS.PALETTE["fire_dark"], 60),
                                (8, 4, 84, 10))
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
        by = (y + 10) - h          # bottom tetap di y+10
        surface.blit(spr, (bx, by))
        if NS._record_shadow is not None:
            NS._record_shadow.append(pygame.Rect(bx, by, w, h))


    def _draw_primal_aura(surface, x, y, phase, active_skill):
        """Background aura."""
        NS = _NS_khalros
        if NS._aura_cache is None:
            aura = pygame.Surface((180, 160), pygame.SRCALPHA)
            for radius in range(72, 5, -4):
                alpha = int((72 - radius) * 1.2)
                if alpha > 0:
                    NS._aacircle(aura, (*NS.PALETTE["fire_dark"],
                                        min(255, alpha)), (90, 80), radius)
            NS._aura_cache = aura
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.4 if active_skill in ("q", "r") else 1.0
        a = int(255 * min(1.0, pulse * strength))
        spr = NS._aura_cache.copy()
        spr.set_alpha(a)
        surface.blit(spr, (x - 90, y - 80))


    def _draw_ground_runes(surface, x, y, phase, active_skill):
        """Ground runes."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_khalros.PALETTE["fire_dark"], 140),
                            (5, 10, 120, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_khalros.PALETTE["fire_mid"], 170),
                            (20, 14, 90, 16), 2)

        # Tribal rune marks
        for i in range(8):
            angle = phase * 0.15 + i * math.pi / 4
            x1 = 65 + int(math.cos(angle) * 30)
            y1 = 22 + int(math.sin(angle) * 6)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_khalros.PALETTE["fire_hot"], 160),
                             (x1, y1), (x2, y2), 1)

        if active_skill:
            pygame.draw.ellipse(ring, (*_NS_khalros.PALETTE["fire_bright"], int(80 * pulse)),
                                (15, 8, 100, 28), 1)

        surface.blit(ring, (x - 65, y - 22))


    def _draw_axe_swing_arc(surface, x, y, facing, progress):
        """Axe swing motion trail (fire orange)."""
        if progress < 0.28 or progress > 0.75:
            return
        if progress < 0.5:
            visibility = (progress - 0.28) / 0.22
        else:
            visibility = 1.0 - (progress - 0.5) / 0.25
        visibility = max(0.0, min(1.0, visibility))

        arc = pygame.Surface((140, 110), pygame.SRCALPHA)
        for i in range(16):
            t = i / 15
            angle = -math.pi * 0.9 + t * math.pi * 1.1
            px = 70 + int(math.cos(angle) * 52) * facing
            py = 55 + int(math.sin(angle) * 40)
            alpha = int((200 - i * 10) * visibility)
            if alpha <= 0:
                continue
            _NS_khalros._aacircle(arc, (*_NS_khalros.PALETTE["fire_dark"], alpha), (px, py), 8)
            _NS_khalros._aacircle(arc, (*_NS_khalros.PALETTE["fire_bright"], alpha), (px, py), 5)
            _NS_khalros._aacircle(arc, (*_NS_khalros.PALETTE["fire_hot"], alpha), (px, py), 3)
            _NS_khalros._aacircle(arc, (*_NS_khalros.PALETTE["fire_glow"], min(255, alpha)), (px, py), 1)
        surface.blit(arc, (x - 70, y - 55))


    def _draw_swing_impact(surface, x, y, facing, progress):
        if progress < 0.45 or progress > 0.85:
            return
        t = (progress - 0.45) / 0.40
        intensity = math.sin(t * math.pi)

        impact_x = x + 38 * facing
        impact_y = y + 3
        alpha = int(230 * intensity)
        radius = int(8 + intensity * 22)

        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_dark"], alpha // 2),
                  (impact_x, impact_y), radius + 4)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_bright"], alpha),
                  (impact_x, impact_y), radius, 3)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_hot"], alpha),
                  (impact_x, impact_y), max(1, radius - 5), 2)

        # Sparks
        for i in range(10):
            angle = i * math.pi / 5 + progress * 3
            dx = impact_x + int(math.cos(angle) * radius * 1.3)
            dy = impact_y + int(math.sin(angle) * radius * 0.9)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["fire_hot"], (dx, dy), 2)
            _NS_khalros._aacircle(surface, _NS_khalros.PALETTE["fire_glow"], (dx, dy), 1)


    # ===================================================================
    # SKILL Q: WILD AXES
    # ===================================================================
    def _draw_wild_axes(surface, boss, x, y, timer, phase):
        """Two axes thrown - spawn projectiles."""
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_khalros._target_position(boss, x, y)

        if progress < 0.15 and not getattr(boss, "_khal_axes_spawned", False):
            # Spawn 2 axes with slight spread
            for i, offset in enumerate((-10, 10)):
                sx = x + 12 * boss.direction
                sy = y - 10 + offset
                _NS_khalros._spawn_axe(boss, sx, sy, tx + offset * 0.5, ty)
            boss._khal_axes_spawned = True
        if progress > 0.5:
            boss._khal_axes_spawned = False

        # Aim line
        if progress < 0.4:
            alpha = int(150 * (1 - progress / 0.4))
            start_x = x + 15 * boss.direction
            start_y = y - 10
            for i in range(0, 100, 8):
                t = i / 100
                px = int(start_x + (tx - start_x) * t)
                py = int(start_y + (ty - start_y) * t)
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_bright"], alpha), (px, py), 2)

            # ORIGINAL-MAX: orb target menyala saat pelemparan
            orb_pulse = 0.6 + 0.4 * math.sin(phase * 6)
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_dark"], int(180 * orb_pulse)),
                                  (int(tx), int(ty)), 10)
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_bright"], int(230 * orb_pulse)),
                                  (int(tx), int(ty)), 7)
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_hot"], int(255 * orb_pulse)),
                                  (int(tx), int(ty)), 4)
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_white"], 255),
                                  (int(tx), int(ty)), 2)


    # ===================================================================
    # SKILL W: CALL OF THE WILD (Summon boar + wolf)
    # ===================================================================
    def _draw_call_of_wild_ground(surface, boss, x, y, timer, phase):
        """Summon circles beside Khalros."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        for side, off in [(-1, -40), (1, 40)]:
            sx = x + off
            sy = y + 32
            radius = int(20 + progress * 10)
            _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["fire_dark"], int(180 * pulse)),
                     (sx - radius, sy - radius // 3, radius * 2, radius // 1.5))
            _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["fire_bright"], int(150 * pulse)),
                     (sx - radius + 4, sy - radius // 3 + 2,
                      radius * 2 - 8, radius // 1.5 - 4))

            # Rune symbols
            for i in range(4):
                angle = phase * 0.3 + i * math.pi / 2
                rx = sx + int(math.cos(angle) * (radius - 3))
                ry = sy + int(math.sin(angle) * (radius // 3))
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_hot"], int(200 * pulse)),
                          (rx, ry), 2)


    def _draw_call_of_wild(surface, boss, x, y, timer, phase):
        """Boar (left) and wolf (right) rising from summon circles."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Boar on left
        boar_x = x - 40
        boar_y = y + 20
        if progress > 0.2:
            rise_t = min(1.0, (progress - 0.2) / 0.5)
            _NS_khalros._draw_boar(surface, boar_x, boar_y - int(20 * rise_t),
                       -1, phase, alpha=int(255 * rise_t))

        # Wolf on right
        wolf_x = x + 40
        wolf_y = y + 20
        if progress > 0.3:
            rise_t = min(1.0, (progress - 0.3) / 0.5)
            _NS_khalros._draw_wolf(surface, wolf_x, wolf_y - int(20 * rise_t),
                       1, phase, alpha=int(255 * rise_t))


    def _draw_boar(surface, cx, cy, facing, phase, alpha=255):
        """Draw a boar creature."""
        # Body shadow
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["shadow_deep"], alpha),
                 (cx - 16, cy - 4, 32, 16))

        # Body
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["boar_darkest"], alpha),
                 (cx - 15, cy - 6, 30, 15))
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["boar_dark"], alpha),
                 (cx - 13, cy - 5, 26, 12))
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["boar_mid"], alpha),
                 (cx - 11, cy - 4, 22, 9))
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["boar_light"], alpha),
                 (cx - 9, cy - 5, 18, 5))

        # Head (front)
        hx = cx + facing * 13
        hy = cy - 3
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["boar_darkest"], alpha), (hx, hy), 6)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["boar_dark"], alpha), (hx, hy), 5)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["boar_mid"], alpha), (hx - facing, hy - 1), 3)

        # Snout
        _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["boar_darkest"], alpha), [
            (hx + facing * 4, hy - 1),
            (hx + facing * 8, hy),
            (hx + facing * 8, hy + 3),
            (hx + facing * 4, hy + 2),
        ])
        _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["boar_dark"], alpha), [
            (hx + facing * 5, hy),
            (hx + facing * 7, hy + 1),
            (hx + facing * 7, hy + 2),
            (hx + facing * 5, hy + 2),
        ])

        # Tusks (curved white)
        for side_off in (-1, 1):
            tusk_y = hy + 1 + side_off
            _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["metal_light"], alpha), [
                (hx + facing * 6, tusk_y),
                (hx + facing * 10, tusk_y - 2 * side_off),
                (hx + facing * 8, tusk_y - side_off),
            ])
            _NS_khalros._aaline(surface, (*_NS_khalros.PALETTE["metal_shine"], alpha),
                    (hx + facing * 7, tusk_y - side_off),
                    (hx + facing * 9, tusk_y - 2 * side_off), 1)

        # Eye
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_hot"], alpha), (hx - facing, hy - 2), 1)

        # Ears
        _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["boar_darkest"], alpha), [
            (hx - facing * 2, hy - 5),
            (hx + facing, hy - 8),
            (hx + facing * 3, hy - 5),
        ])

        # Legs
        for lx in (cx - 8, cx - 4, cx + 4, cx + 8):
            offset_y = int(math.sin(phase * 2 + lx) * 1)
            _NS_khalros._rect(surface, (*_NS_khalros.PALETTE["boar_darkest"], alpha),
                  (lx - 1, cy + 6, 3, 6 + offset_y))
            _NS_khalros._rect(surface, (*_NS_khalros.PALETTE["boar_dark"], alpha),
                  (lx, cy + 6, 2, 5 + offset_y))

        # Spiky back mane
        for i, mx in enumerate([-8, -4, 0, 4, 8]):
            _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["hair_darkest"], alpha), [
                (cx + mx - 1, cy - 6),
                (cx + mx + 1, cy - 6),
                (cx + mx, cy - 10 - (i % 2)),
            ])

        # Tail
        _NS_khalros._aaline(surface, (*_NS_khalros.PALETTE["boar_darkest"], alpha),
                (cx - facing * 14, cy - 2),
                (cx - facing * 18, cy - 5), 2)


    def _draw_wolf(surface, cx, cy, facing, phase, alpha=255):
        """Draw a wolf creature."""
        # Body shadow
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["shadow_deep"], alpha),
                 (cx - 15, cy - 3, 30, 14))

        # Body (leaner than boar)
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["wolf_darkest"], alpha),
                 (cx - 14, cy - 5, 28, 13))
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["wolf_dark"], alpha),
                 (cx - 12, cy - 4, 24, 10))
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["wolf_mid"], alpha),
                 (cx - 10, cy - 3, 20, 7))
        _NS_khalros._ellipse(surface, (*_NS_khalros.PALETTE["wolf_light"], alpha),
                 (cx - 8, cy - 4, 16, 4))

        # Head
        hx = cx + facing * 12
        hy = cy - 3
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["wolf_darkest"], alpha), (hx, hy), 6)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["wolf_dark"], alpha), (hx, hy), 5)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["wolf_mid"], alpha), (hx - facing, hy - 1), 3)

        # Snout (pointier than boar)
        _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["wolf_darkest"], alpha), [
            (hx + facing * 3, hy),
            (hx + facing * 9, hy),
            (hx + facing * 8, hy + 3),
            (hx + facing * 3, hy + 2),
        ])
        _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["wolf_dark"], alpha), [
            (hx + facing * 4, hy + 1),
            (hx + facing * 8, hy + 1),
            (hx + facing * 7, hy + 2),
            (hx + facing * 4, hy + 2),
        ])

        # Nose
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["shadow_deep"], alpha),
                  (hx + facing * 8, hy + 1), 1)

        # Fangs
        _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["white"], alpha), [
            (hx + facing * 5, hy + 2),
            (hx + facing * 6, hy + 4),
            (hx + facing * 7, hy + 2),
        ])

        # Glowing red eye (feral)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_hot"], alpha), (hx - facing, hy - 2), 1)
        _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["red_bright"], alpha), (hx - facing, hy - 2), 1)

        # Pointy ears
        for ear_off in (-3, 1):
            _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["wolf_darkest"], alpha), [
                (hx + facing * ear_off, hy - 5),
                (hx + facing * (ear_off + 1), hy - 9),
                (hx + facing * (ear_off + 3), hy - 5),
            ])
            _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["wolf_dark"], alpha), [
                (hx + facing * (ear_off + 1), hy - 5),
                (hx + facing * (ear_off + 2), hy - 8),
                (hx + facing * (ear_off + 3), hy - 5),
            ])

        # Legs (longer than boar)
        for lx in (cx - 8, cx - 3, cx + 3, cx + 8):
            offset_y = int(math.sin(phase * 2.5 + lx) * 1)
            _NS_khalros._rect(surface, (*_NS_khalros.PALETTE["wolf_darkest"], alpha),
                  (lx - 1, cy + 5, 3, 7 + offset_y))
            _NS_khalros._rect(surface, (*_NS_khalros.PALETTE["wolf_dark"], alpha),
                  (lx, cy + 5, 2, 6 + offset_y))

        # Bushy tail
        _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["wolf_darkest"], alpha), [
            (cx - facing * 12, cy - 2),
            (cx - facing * 20, cy - 4),
            (cx - facing * 18, cy + 2),
            (cx - facing * 12, cy),
        ])
        _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["wolf_dark"], alpha), [
            (cx - facing * 13, cy - 2),
            (cx - facing * 18, cy - 3),
            (cx - facing * 16, cy + 1),
            (cx - facing * 13, cy),
        ])

        # Fur tuft on back
        _NS_khalros._aaline(surface, (*_NS_khalros.PALETTE["wolf_high"], alpha),
                (cx - 5, cy - 5), (cx + 5, cy - 5), 1)


    # ===================================================================
    # SKILL E: BOAR (fast charging boar)
    # ===================================================================
    def _draw_boar_ground(surface, boss, x, y, timer, phase):
        """Trail of dust as boar charges."""
        tx, ty = _NS_khalros._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 45))

        # Charging trail
        start_x = x + 15 * boss.direction
        start_y = y + 25
        for i in range(6):
            t = max(0, progress - i * 0.08)
            px = int(start_x + (tx - start_x) * t)
            py = int(start_y + (ty - start_y) * t)
            alpha = int(150 - i * 22)
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["leather_dark"], alpha), (px, py), 5)
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["leather_mid"], alpha), (px, py), 3)


    def _draw_boar_charge(surface, boss, x, y, timer, phase):
        """Boar charging toward target."""
        tx, ty = _NS_khalros._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 45))
        start_x = x + 15 * boss.direction
        start_y = y + 25

        bx = int(start_x + (tx - start_x) * progress)
        by = int(start_y + (ty - start_y) * progress)

        facing = 1 if tx > x else -1

        # Trail of dust/sparks
        for i in range(5):
            trail_t = max(0.0, progress - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_dark"], 150 - i * 25),
                      (px, py), max(2, 6 - i))
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_bright"], 100 - i * 15),
                      (px, py), max(1, 4 - i))

        # The boar itself
        _NS_khalros._draw_boar(surface, bx, by, facing, phase * 2)

        # Impact at end
        if progress > 0.85:
            t = (progress - 0.85) / 0.15
            intensity = 1 - t
            radius = int(20 * intensity)
            _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_hot"], int(230 * intensity)),
                      (tx, ty), radius, 3)
            for i in range(8):
                angle = i * math.pi / 4
                ex = tx + int(math.cos(angle) * radius)
                ey = ty + int(math.sin(angle) * radius)
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["fire_bright"], int(200 * intensity)),
                          (ex, ey), 2)


    # ===================================================================
    # SKILL R: HAWK (flying projectile)
    # ===================================================================
    def _draw_hawk_summon(surface, boss, x, y, timer, phase):
        """Hawk flies from Khalros toward target."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_khalros._target_position(boss, x, y)

        # Spawn hawk projectile at start
        if progress < 0.1 and not getattr(boss, "_khal_hawk_spawned", False):
            sx = x + 5 * boss.direction
            sy = y - 30
            _NS_khalros._spawn_hawk(boss, sx, sy, tx, ty - 20)
            boss._khal_hawk_spawned = True
        if progress > 0.5:
            boss._khal_hawk_spawned = False

        # Feathers falling from spawn point
        if progress < 0.4:
            for i in range(3):
                angle = phase + i * math.pi * 2 / 3
                fx = x + int(math.cos(angle) * 20)
                fy = y - 30 + int(progress * 30) + int(math.sin(angle) * 5)
                alpha = int(180 * (1 - progress / 0.4))
                _NS_khalros._poly(surface, (*_NS_khalros.PALETTE["hawk_dark"], alpha), [
                    (fx, fy),
                    (fx + 2, fy + 4),
                    (fx - 2, fy + 4),
                ])
                _NS_khalros._aacircle(surface, (*_NS_khalros.PALETTE["hawk_mid"], alpha), (fx, fy + 2), 1)


    # ===================================================================
    # Backward compatible alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_khalros.draw_khalros(surface, boss, x, y)


# ====================================================================
# GORATH
# ====================================================================
class _NS_gorath:
    """Namespace gorath - PIXEL MASTERWORK v2 + SKILL FX v2.1.

    Rewrite penuh renderer `_NS_gorath` mengikuti standar
    **Thorne v2 Pixel Masterwork + Thorne v2.1 Skill FX**
    (lihat docs/THORNE_V2_RENDERER.md). Tetap 100% prosedural:
    tidak ada PNG / sprite-sheet / image.load.

    Apa yang naik dibanding v1
    --------------------------
    1. RIG ~1.5x LEBIH BESAR di resolusi native (puncak rambut y=-76,
       hem loincloth y=+58). Pipeline hero (heroes/__init__.py) mengukur
       badan lalu men-scale agar tinggi di lane tetap ~51 px, jadi
       memperbesar rig TIDAK memperbesar hero di arena - melainkan
       memberi ~1.5x piksel native per piksel layar sehingga ramp,
       cluster, dan wajah tetap tajam setelah smoothscale.
    2. DISIPLIN PIXEL-ART: tiap material 4-5 nilai ramp dengan
       hue-shift (bayangan daging didorong dingin ungu-merah, highlight
       hangat koral), selout (outline gelap hanya di sisi bayangan),
       siluet bergerigi lewat `_tuft_points` (hem loincloth, lidah
       kabut darah), specular sebagai cluster 1-2 px, dither band
       (`_dither_dots`) di perut & sisi bayangan loincloth. Key light
       kiri-atas, konsisten dengan lighting.py (LIGHT_DIR = (-1, -1)).
    3. ANATOMI: tengkorak demon underbite (brow berat, socket mata
       cekung + iris menyala + kedip), war-paint darah melintang mata,
       tanduk pendek, rambut liar 3 lapis ber-ujung darah, torso
       berotot ber-rune darah, kalung trofi tulang, harness X kulit,
       pauldron tulang ber-duri, sabuk + gesper emas ber-sigil, 6 helai
       loincloth robek, dan sepasang **kukri melengkung** ber-fuller
       (5 band + darah + glint).
    4. ANIMASI: float solver (dua plume kabut darah bergantian menapak,
       riak darah saat kontak), inersia rambut/loincloth/bilah
       (secondary motion), idle hidup (napas, kedip, tetes darah,
       denyut rune), serangan 7 keyframe dengan frame IMPACT
       tersendiri (squash, bintang, shockwave, smear sabit 3 lapis).
    5. SKILL FX world-space (`_fx_scale`, cap 2.6) dengan 3 fase:
       AKTIVASI (pilar + shockwave + bintang), STEADY (aura berlapis +
       partikel + ring berputar), TELEGRAPH (ring jangkauan TEPAT dalam
       px dunia + ring konvergen + chevron + retakan tanah).
       Badan ikut bereaksi ke state skill (rune & mata menyala,
       bilah berlumur darah panas).
    """

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    # ── cache (nama lama dipertahankan) ─────────────────────────────
    _shadow_cache = None
    _aura_cache = None
    _flash_buf = None
    _body_buf = None        # buffer badan untuk outline+lighting
    _record_shadow = None

    # Surface statis (aura/mist/pool/platform) dibangun SEKALI lalu
    # dipakai ulang - tidak ada alokasi surface per frame.
    _STATIC_SURFACES = {}

    # ── metrik rig v2 ───────────────────────────────────────────────
    # Faktor pertumbuhan terhadap rig v1 (dokumentasi + dipakai audit).
    RIG_SCALE = 1.5
    # Buffer badan: dibatasi dari extents TERUKUR semua pose (idle/walk/
    # attack x 7 keyframe, dua arah hadap, rage on/off, portrait LOD):
    # anchor -> kiri -61, atas -89, kanan +61, bawah +52, + margin.
    # Buffer sekecil mungkin karena outline siluet meng-copy-nya 5x per
    # frame dan get_bounding_rect memindai seluruh isinya.
    RIG_W, RIG_H = 140, 156
    RIG_OX, RIG_OY = 70, 98

    # Satu SCALE untuk SEMUA jalur (boss langsung, lane hero, portrait).
    # Rig di-author 1.5x lebih besar lalu ditampilkan lewat SCALE ini,
    # sehingga: (a) kerapatan detail naik 1.5x di resolusi native,
    # (b) ukuran DI LAYAR tetap sekelas keluarga level-2 (alchemist true
    # boss harus tetap >= gorath mini - lihat tools/test_level2_masterwork).
    # PERINGATAN: jangan pisahkan SCALE per jalur; itu merusak
    # normalisasi _measure_native_size di heroes/__init__.py.
    SCALE = 0.62
    # Jarak jangkar -> garis tanah dalam PX LOKAL rig (= batas bawah
    # siluet terukur: plume kabut saat kontak penuh).
    FEET_DY = 52
    # Garis tanah dunia relatif jangkar (bayangan/pool/retakan).
    GROUND_DY = int(round(FEET_DY * SCALE))

    # Durasi visual skill (frame) - HARUS sama dengan active_skill_timer
    # yang diisi AI di bosses/base_boss.py (_gorath_q/w/e/r).
    SKILL_DUR = {"q": 90, "w": 60, "e": 35, "r": 90}

    # Radius gameplay tiap skill dalam PX DUNIA (bosses/base_boss.py):
    #   w -> AOE 150 di sekitar diri, e -> AOE 85 setelah lompat,
    #   r -> AOE 190 di sekitar diri. Telegraph digambar TEPAT di angka
    #   ini lewat _ring_r (world-space), bukan px canvas mentah.
    SKILL_RADIUS = {"w": 150, "e": 85, "r": 190}

    # ---------------------------------------------------------------------------
    # HD Blood Palette v2 - deep crimson / demon flesh / bone / steel
    # Semua kunci lama dipertahankan (nilai dituning ulang dengan
    # hue-shift) + kunci baru untuk rune, emas, dan rim.
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin - reddish demon flesh (bayangan dingin ungu, highlight koral)
        "skin_darkest":   (32,  10,  16),
        "skin_dark":      (76,  22,  28),
        "skin_mid":       (126, 46,  40),
        "skin_light":     (176, 80,  58),
        "skin_high":      (216, 132, 92),
        "skin_shine":     (246, 188, 144),
        "skin_rim":       (255, 214, 178),

        # Blood
        "blood_darkest":  (24,   3,   6),
        "blood_dark":     (72,   6,  12),
        "blood_mid":      (136, 15,  22),
        "blood_bright":   (196, 26,  32),
        "blood_hot":      (236, 56,  50),
        "blood_glow":     (255, 102, 86),
        "blood_light":    (255, 166, 142),
        "blood_seam":     (255, 214, 190),

        # Hair - dark spiky (bayangan biru-ungu)
        "hair_darkest":   (10,   8,  14),
        "hair_dark":      (28,  22,  34),
        "hair_mid":       (56,  46,  62),
        "hair_high":      (98,  84, 106),

        # Leather / cloth
        "leather_darkest": (18, 12,  9),
        "leather_dark":   (46,  28,  19),
        "leather_mid":    (86,  56,  31),
        "leather_light":  (136, 92,  52),
        "leather_high":   (186, 138, 84),

        # Bone / claws
        "bone_darkest":   (54,  44,  36),
        "bone_dark":      (114, 100, 80),
        "bone_mid":       (176, 161, 132),
        "bone_light":     (221, 211, 182),
        "bone_shine":     (246, 241, 222),

        # Metal (blades)
        "metal_darkest":  (17,  15,  20),
        "metal_dark":     (48,  43,  52),
        "metal_mid":      (96,  89,  99),
        "metal_light":    (156, 149, 160),
        "metal_shine":    (218, 213, 222),

        # Eyes - glowing red
        "eye_dark":       (78,   5,  10),
        "eye_mid":        (180, 20,  26),
        "eye_bright":     (240, 56,  50),
        "eye_hot":        (255, 132, 102),
        "eye_white":      (255, 222, 202),

        # Gold - gesper, sigil, ornamen
        "gold_dark":      (92,  62,  20),
        "gold_mid":       (176, 130, 44),
        "gold_light":     (238, 198, 96),

        # Rune darah di dada (menyala saat skill aktif)
        "rune_dark":      (66,   6,  14),
        "rune_mid":       (188, 26,  38),
        "rune_light":     (255, 118, 96),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (5,   2,   3),
        "white":          (255, 255, 255),
    }

    # ---------------------------------------------------------------------------
    # Primitif dasar
    # ---------------------------------------------------------------------------
    def _static(key, builder):
        """Surface statis ter-cache (dibangun sekali, dipakai ulang)."""
        surf = _NS_gorath._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_gorath._STATIC_SURFACES[key] = surf
        return surf

    _CLAMP_MEMO = {}

    def _clamp(color):
        """Clamp color channels, supports both RGB and RGBA.

        Jalur cepat: warna palette sudah berupa tuple int 0..255, jadi
        dikembalikan apa adanya. Sisanya (hasil hitung alpha float)
        di-memo - primitif ini dipanggil puluhan ribu kali per detik dan
        versi genexpr-nya adalah hot spot profil nomor satu.
        """
        try:
            hit = _NS_gorath._CLAMP_MEMO.get(color)
        except TypeError:
            return tuple(max(0, min(255, int(c))) for c in color)
        if hit is not None:
            return hit
        out = tuple(max(0, min(255, int(c))) for c in color)
        memo = _NS_gorath._CLAMP_MEMO
        if len(memo) > 8192:
            memo.clear()
        memo[color] = out
        return out

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _mix(a, b, t):
        """Blend linear dua warna palette (t=0 -> a, t=1 -> b)."""
        t = max(0.0, min(1.0, t))
        return _NS_gorath._clamp(
            (a[0] + (b[0] - a[0]) * t,
             a[1] + (b[1] - a[1]) * t,
             a[2] + (b[2] - a[2]) * t))

    def _hash01(i):
        """Pseudo-random deterministik 0..1 (stabil antar frame & cache)."""
        x = math.sin(i * 127.1 + 311.7) * 43758.5453
        return x - math.floor(x)

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_gorath._clamp(color)
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
        if _NS_gorath.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_gorath._clamp(color)
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
        color = _NS_gorath._clamp(color)
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
        color = _NS_gorath._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, int(rw), int(rh)), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)

    def _rect(surface, color, rect, border_radius=0):
        color = _NS_gorath._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, int(rw), int(rh)),
                             border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)

    def _ring(surface, center, radius, width, color, alpha):
        """Cincin skill: stroke gelap di belakang + cincin terang di atas.

        Tanpa stroke gelap, cincin tipis semi-transparan tenggelam di
        terrain terang (standar keluarga masterwork).
        """
        alpha = _NS_gorath._alpha(alpha)
        if alpha <= 0:
            return
        cx, cy = int(center[0]), int(center[1])
        r = int(radius)
        if r <= 0:
            return
        _NS_gorath._aacircle(surface, (6, 3, 6, alpha), (cx, cy), r + 1,
                             max(1, width + 2))
        _NS_gorath._aacircle(surface, (*color, alpha), (cx, cy), r,
                             max(1, width))

    # ---------------------------------------------------------------------------
    # Konversi ruang dunia <-> canvas renderer
    # ---------------------------------------------------------------------------
    def _world_to_local(boss, x, y, wx, wy):
        """Titik DUNIA -> ruang gambar renderer.

        Saat dirender sebagai HERO (heroes/__init__.py) renderer
        dipanggil di pusat canvas lalu canvas di-scale _render_scale,
        jadi 1 px canvas = _render_scale px dunia. Boss asli tidak punya
        _render_scale -> dikembalikan apa adanya.
        """
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
        return (int(x + 150 / float(getattr(boss, "_render_scale", 1.0) or 1.0)
                    * getattr(boss, "direction", 1)), int(y))

    # ===================================================================
    # SKILL FX PRIMITIVES (standar Thorne v2.1)
    # ===================================================================
    def _fx_scale(boss):
        """Faktor skala efek skill (world-space).

        Hero dirender ke canvas lalu dikecilkan ``_render_scale`` saat
        di-blit -> efek (cincin, retakan, duri) ikut menyusut. Dengan
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
        (W 150 / E 85 / R 190 px dunia). Clamp menjaga efek tidak
        terpotong di tepi cache canvas hero.
        """
        scale = getattr(boss, "_render_scale", None)
        r = float(world_px) / float(scale) if scale else float(world_px)
        margin = min(surface.get_width(), surface.get_height()) // 2 - 10
        return int(max(4, min(r, margin)))

    def _spark_star(surface, cx, cy, size, color, alpha, spikes=6, rot=0.4,
                    core=None):
        """Bintang kilat: spike panjang-pendek selang-seling + inti."""
        alpha = _NS_gorath._alpha(alpha)
        if alpha <= 0 or size <= 0:
            return
        for k in range(spikes):
            ang = rot + k * math.pi * 2 / spikes
            ln = size * (1.0 if k % 2 == 0 else 0.55)
            _NS_gorath._aaline(surface, (*color, alpha),
                               (int(cx), int(cy)),
                               (int(cx + math.cos(ang) * ln),
                                int(cy + math.sin(ang) * ln * .8)),
                               2 if k % 2 == 0 else 1)
        if core:
            _NS_gorath._aacircle(surface, (*core, alpha), (int(cx), int(cy)),
                                 max(1, int(size * .3)))

    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        """Satu panah '>' menghadap arah ``ang`` (telegraph bergerak)."""
        alpha = _NS_gorath._alpha(alpha)
        if alpha <= 0 or size <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        tipx, tipy = cx + ca * size, cy + sa * size
        for s in (-1, 1):
            _NS_gorath._aaline(
                surface, (*color, alpha),
                (int(cx + px * s * size * .55 - ca * size * .5),
                 int(cy + py * s * size * .55 - sa * size * .5)),
                (int(tipx), int(tipy)), width)

    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=10, thick=3, span=0.6, squash=.92):
        """Cincin putus-putus yang berputar (marker AOE / rune ring)."""
        alpha = _NS_gorath._alpha(alpha)
        if alpha <= 0 or radius <= 1:
            return
        for i in range(segments):
            a0 = phase + i * math.pi * 2 / segments
            a1 = a0 + math.pi * 2 / segments * span
            p0 = (cx + math.cos(a0) * radius, cy + math.sin(a0) * radius * squash)
            p1 = (cx + math.cos(a1) * radius, cy + math.sin(a1) * radius * squash)
            _NS_gorath._aaline(surface, (*color, alpha), p0, p1, thick)

    # -------------------------------------------------------------------
    # DECAL TANAH (pengganti cincin stroke)
    # -------------------------------------------------------------------
    # Cincin stroke 1-4 px terbaca "basic" karena tiga alasan: tepinya
    # keras, nilainya rata sepanjang keliling, dan bidangnya campur aduk
    # (lingkaran sempurna ditumpuk elips squash .42 -> dua perspektif di
    # tanah yang sama). Penggantinya: DECAL yang dibangun sekali per
    # (radius, gaya) lalu di-blit + di-set_alpha per frame.
    #
    # Radius gameplay itu euclidean (dist <= 150), jadi bidang decal
    # LINGKARAN PENUH - satu perspektif konsisten untuk semua FX tanah.

    _DECAL_CACHE = {}
    _DECAL_ORDER = []

    def _decal(key, size, builder):
        """Surface decal ter-cache; LRU sederhana supaya memori terbatas."""
        hit = _NS_gorath._DECAL_CACHE.get(key)
        if hit is not None:
            return hit
        surf = builder(size)
        _NS_gorath._DECAL_CACHE[key] = surf
        _NS_gorath._DECAL_ORDER.append(key)
        if len(_NS_gorath._DECAL_ORDER) > 48:
            old = _NS_gorath._DECAL_ORDER.pop(0)
            _NS_gorath._DECAL_CACHE.pop(old, None)
        return surf

    def _blit_decal(surface, decal, cx, cy, alpha=255, add=False):
        """Blit decal ter-pusat di (cx, cy) dengan alpha & mode opsional."""
        alpha = _NS_gorath._alpha(alpha)
        if alpha <= 0:
            return
        w, h = decal.get_size()
        decal.set_alpha(alpha)
        flags = pygame.BLEND_RGBA_ADD if add else 0
        surface.blit(decal, (int(cx) - w // 2, int(cy) - h // 2),
                     special_flags=flags)
        decal.set_alpha(255)

    def _quantize(v, step=6):
        """Bulatkan radius ke kelipatan `step` supaya decal cache nyangkut.

        Tanpa ini radius yang berubah tiap frame (ring konvergen) akan
        membangun surface baru terus-menerus.
        """
        return max(step, int(round(float(v) / step) * step))

    def _build_falloff_ring(size, color, core, thickness, softness,
                            inner_glow):
        """Cincin ber-gradien: inti terang -> falloff halus ke luar.

        Dibangun dari banyak lingkaran 1 px dengan alpha mengikuti kurva
        jarak ke radius nominal, jadi tepinya lembut dan nilainya
        bertingkat - bukan stroke datar.
        """
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
                t = t * t                       # falloff kuadratik
            if t <= 0.003:
                continue
            # inti hanya muncul di puncak kurva; additive blending sudah
            # menaikkan luminansi, jadi campuran ke `core` ditahan.
            col = _NS_gorath._mix(color, core, min(1.0, max(0.0, t - 0.45)
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
        """Cincin AOE kelas produksi: decal ber-falloff, additive.

        Menggantikan stroke `_ring`. Radius di-quantize supaya decal
        dipakai ulang; blit additive membuatnya membara di atas terrain
        gelap tanpa terlihat seperti garis vektor.
        """
        radius = _NS_gorath._quantize(radius, 6)
        if radius < 6:
            return
        pad = softness + thickness + 3
        size = radius * 2 + pad * 2
        key = ("fring", radius, color, core, thickness, softness, inner_glow)
        decal = _NS_gorath._decal(
            key, size,
            lambda n: _NS_gorath._build_falloff_ring(
                n, color, core, thickness, softness, inner_glow))
        _NS_gorath._blit_decal(surface, decal, cx, cy, alpha, add=add)

    def _build_arc_ring(size, color, core, segments, span, thickness,
                        softness, taper):
        """Cincin busur: tiap segmen meruncing di kedua ujung.

        Dibangun sebagai poligon lengkung (bukan garis lurus antar dua
        titik), sehingga mengikuti kelengkungan cincin dan ujungnya
        menipis - kesan 'rune terbakar', bukan strip putus-putus.
        """
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
                # meruncing: tebal penuh di tengah busur, tipis di ujung
                w = thickness * (1.0 - taper * abs(t - 0.5) * 2) ** 1.5
                w = max(0.6, w)
                ca, sa = math.cos(ang), math.sin(ang)
                outer.append((c + ca * (r_nom + w), c + sa * (r_nom + w)))
                inner.append((c + ca * (r_nom - w), c + sa * (r_nom - w)))
            poly = outer + inner[::-1]
            # satu halo tipis di belakang, lalu isi segmen.
            halo = []
            for (px, py) in poly:
                dx, dy = px - c, py - c
                halo.append((c + dx * 1.012, c + dy * 1.012))
            pygame.draw.polygon(surf, (*color, 70), halo)
            pygame.draw.polygon(surf, (*color, 190), poly)
            # kilau inti hanya di sepertiga tengah busur (bukan seluruhnya)
            n = len(outer)
            q0, q1 = int(n * 0.34), int(n * 0.66)
            if q1 > q0 + 1:
                mid = outer[q0:q1] + inner[q0:q1][::-1]
                pygame.draw.polygon(surf, (*core, 205), mid)
        return surf

    def _rune_ring(surface, cx, cy, radius, color, core, alpha, spin,
                   segments=12, span=0.42, thickness=3.0, taper=0.85):
        """Cincin busur berputar (telegraph 'rune terbakar').

        Decal dibangun sekali lalu DIPUTAR lewat transform.rotate, jadi
        rotasi mulus tanpa membangun ulang geometri tiap frame.
        """
        radius = _NS_gorath._quantize(radius, 8)
        if radius < 8:
            return
        pad = int(thickness) + 8
        size = radius * 2 + pad * 2
        key = ("arcring", radius, color, core, segments, round(span, 2),
               round(thickness, 1), round(taper, 2))
        decal = _NS_gorath._decal(
            key, size,
            lambda n: _NS_gorath._build_arc_ring(
                n, color, core, segments, span, thickness, 6, taper))
        deg = -math.degrees(spin) % (360.0 / max(1, segments))
        rot = pygame.transform.rotate(decal, deg)
        _NS_gorath._blit_decal(surface, rot, cx, cy, alpha, add=True)

    def _build_scorch(size, color, edge, seed):
        """Noda gosong tanah: gumpalan lembut ber-tepi tidak beraturan.

        Dipakai sebagai alas semua telegraph supaya efek 'menempel' di
        tanah, bukan melayang seperti overlay UI.
        """
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        r = c - 2
        # tubuh gosong: lingkaran ber-alpha menurun
        for i in range(r, 0, -2):
            t = 1.0 - i / float(r)
            a = int(120 * (t ** 1.6))
            if a > 1:
                col = _NS_gorath._mix(edge, color, t)
                pygame.draw.circle(surf, (*col, a), (c, c), i)
        # tepi tidak beraturan: tiap gumpalan JUGA ber-falloff, kalau
        # tidak, lingkaran keras terbaca sebagai kotak gelap di layar.
        for i in range(20):
            ang = _NS_gorath._hash01(seed * 31 + i) * math.tau
            rr = r * (0.80 + 0.16 * _NS_gorath._hash01(seed * 17 + i))
            br = max(3, int(r * 0.15 * (0.5 +
                     _NS_gorath._hash01(seed * 7 + i))))
            bx = int(c + math.cos(ang) * rr)
            by = int(c + math.sin(ang) * rr)
            for k in range(br, 0, -1):
                a = int(70 * (1.0 - k / float(br)) ** 1.5)
                if a > 1:
                    pygame.draw.circle(surf, (*edge, a), (bx, by), k)
        return surf

    def _ground_scorch(surface, cx, cy, radius, color, edge, alpha, seed=1):
        """Alas gosong ter-cache di bawah telegraph."""
        radius = _NS_gorath._quantize(radius, 10)
        if radius < 8:
            return
        size = radius * 2 + 6
        key = ("scorch", radius, color, edge, seed)
        decal = _NS_gorath._decal(
            key, size,
            lambda n: _NS_gorath._build_scorch(n, color, edge, seed))
        _NS_gorath._blit_decal(surface, decal, cx, cy, alpha)

    def _build_zone_fill(size, color, edge_bias):
        """Isi zona AOE: paling pekat DI DEKAT TEPI, memudar ke tengah.

        Pola ini (bukan glow tengah) yang dipakai game aksi modern:
        pemain membaca BATAS zona, sementara tengahnya tetap bening
        supaya karakter & pertarungan tidak tertutup.
        """
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        r = c - 1
        for i in range(r, 0, -1):
            t = i / float(r)
            # kurva: naik tajam mendekati tepi
            v = t ** edge_bias
            a = int(115 * v)
            if a > 1:
                pygame.draw.circle(surf, (*color, a), (c, c), i)
        return surf

    def _zone_fill(surface, cx, cy, radius, color, alpha, edge_bias=3.2):
        """Wash zona AOE ter-cache (additive lembut)."""
        radius = _NS_gorath._quantize(radius, 8)
        if radius < 6:
            return
        decal = _NS_gorath._decal(
            ("zone", radius, color, round(edge_bias, 1)), radius * 2,
            lambda n: _NS_gorath._build_zone_fill(n, color, edge_bias))
        _NS_gorath._blit_decal(surface, decal, cx, cy, alpha, add=True)

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
        radius = _NS_gorath._quantize(radius, 8)
        if radius < 4:
            return
        size = radius * 2
        decal = _NS_gorath._decal(
            ("glow", radius, color), size,
            lambda n: _NS_gorath._build_radial_grad(n, color))
        _NS_gorath._blit_decal(surface, decal, cx, cy, alpha, add=True)

    def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                      width=3):
        """Retakan tanah berzigzag (3 segmen) dengan seam menyala."""
        alpha = _NS_gorath._alpha(alpha)
        if alpha <= 0 or length <= 0:
            return
        x, y, a = cx, cy, ang
        pts = [(x, y)]
        for i in range(3):
            a += (_NS_gorath._hash01(seed * 7 + i * 13) - .5) * .8
            seg = length / 3.0
            x += math.cos(a) * seg
            y += math.sin(a) * seg * .55      # perspektif tanah
            pts.append((x, y))
        for i in range(len(pts) - 1):
            _NS_gorath._aaline(surface, (*colors[0], alpha),
                               pts[i], pts[i + 1], width + 2)
            _NS_gorath._aaline(surface, (*colors[1], alpha),
                               pts[i], pts[i + 1], width)

    def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
        """Ubah spine halus jadi tepi bergerigi (kain robek / kabut).

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
                d = depth * (0.55 + 0.45 * _NS_gorath._hash01(i * 7 + j * 13 + seed))
                if j % 2 == 0:
                    out.append((px + nx * d, py + ny * d))
                else:
                    out.append((px - nx * d * 0.45, py - ny * d * 0.45))
            out.append((bx, by))
        return out

    def _dither_dots(surface, color, points, alpha=80):
        """Dither band 50% klasik (bertahan setelah downscale)."""
        col = (*color, _NS_gorath._alpha(alpha))
        for i, (px, py) in enumerate(points):
            if i % 2 == 0:
                _NS_gorath._aacircle(surface, col, (int(px), int(py)), 1)

    # ---------------------------------------------------------------------------
    # Blood splatter & droplet helpers (nama lama dipertahankan)
    # ---------------------------------------------------------------------------
    def _draw_blood_splatter(surface, cx, cy, size=8, seed=0, alpha=255):
        """Cipratan darah kacau: inti 3 band + satelit deterministik."""
        alpha = _NS_gorath._alpha(alpha)
        color_outer = (*_NS_gorath.PALETTE["blood_dark"], alpha)
        color_inner = (*_NS_gorath.PALETTE["blood_bright"], alpha)
        color_hot = (*_NS_gorath.PALETTE["blood_hot"], alpha)

        _NS_gorath._aacircle(surface, color_outer, (cx, cy), size)
        _NS_gorath._aacircle(surface, color_inner, (cx - 1, cy - 1), max(1, size - 2))
        _NS_gorath._aacircle(surface, color_hot, (cx - 1, cy - 2), max(1, size - 4))

        for i in range(6):
            angle = (seed * 0.7 + i * math.pi / 3) % (math.pi * 2)
            dist = size + 2 + (i % 3) * 2
            dx = cx + int(math.cos(angle) * dist)
            dy = cy + int(math.sin(angle) * dist)
            r = max(1, 3 - i % 3)
            _NS_gorath._aacircle(surface, color_outer, (dx, dy), r)
            _NS_gorath._aacircle(surface, color_inner, (dx, dy), max(1, r - 1))

    def _draw_blood_droplet(surface, x, y, size=3, alpha=255):
        """Tetes darah (teardrop) 4 band + kilau 1 px."""
        alpha = _NS_gorath._alpha(alpha)
        _NS_gorath._poly(surface, (*_NS_gorath.PALETTE["blood_darkest"], alpha), [
            (x, y - size),
            (x - size, y + size),
            (x + size, y + size),
        ])
        _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_mid"], alpha),
                             (x, y + size // 2), size)
        _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], alpha),
                             (x, y + size // 2), max(1, size - 1))
        _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_hot"], alpha),
                             (x - 1, y + size // 2 - 1), max(1, size - 2))

    def _draw_blood_streak(surface, sx, sy, ex, ey, width=3, alpha=255):
        """Garis darah menetes (3 band)."""
        alpha = _NS_gorath._alpha(alpha)
        _NS_gorath._aaline(surface, (*_NS_gorath.PALETTE["blood_darkest"], alpha),
                           (sx, sy), (ex, ey), width + 2)
        _NS_gorath._aaline(surface, (*_NS_gorath.PALETTE["blood_mid"], alpha),
                           (sx, sy), (ex, ey), width)
        _NS_gorath._aaline(surface, (*_NS_gorath.PALETTE["blood_bright"], alpha),
                           (sx, sy), (ex, ey), max(1, width - 1))

    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM (Bloodrite / Thirst)
    # ---------------------------------------------------------------------------
    class BloodProjectile:
        """Proyektil darah: trail berlapis 2-tone + glint berputar di ujung."""

        def __init__(self, sx, sy, tx, ty, speed=7.0):
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
            if len(self.trail) > 12:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            P = _NS_gorath.PALETTE
            n = max(1, len(self.trail))
            # trail 2-tone berlapis (gelap lebar -> terang sempit)
            for i, (tx, ty) in enumerate(self.trail):
                t = (i + 1) / n
                alpha = int(40 + 170 * t)
                r = max(1, int(2 + 5 * t))
                _NS_gorath._aacircle(surface, (*P["blood_dark"], int(alpha * .55)),
                                     (tx, ty), r + 2)
                _NS_gorath._aacircle(surface, (*P["blood_bright"], alpha), (tx, ty), r)
                if i % 3 == 0:
                    _NS_gorath._aacircle(surface, (*P["blood_hot"], alpha),
                                         (tx, ty - 1), max(1, r - 2))
            if self.alive:
                px, py = int(self.x), int(self.y)
                _NS_gorath._aacircle(surface, (*P["blood_dark"], 110), (px, py), 11)
                _NS_gorath._aacircle(surface, (*P["blood_mid"], 190), (px, py), 8)
                _NS_gorath._aacircle(surface, (*P["blood_bright"], 235), (px, py), 5)
                _NS_gorath._aacircle(surface, (*P["blood_hot"], 252), (px, py), 3)
                _NS_gorath._aacircle(surface, (*P["blood_light"], 255), (px - 1, py - 1), 1)
                # glint berputar di ujung
                g = self.age * 0.4 + phase
                _NS_gorath._spark_star(surface, px, py, 9, P["blood_glow"], 210,
                                       spikes=4, rot=g, core=P["blood_seam"])

    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_gor_last_x"):
            boss._gor_last_x = boss.x
            boss._gor_last_y = boss.y
            return False
        dx = abs(boss.x - boss._gor_last_x)
        dy = abs(boss.y - boss._gor_last_y)
        boss._gor_last_x = boss.x
        boss._gor_last_y = boss.y
        moving = dx + dy > 0.3
        boss._moving_cached = moving
        return moving

    # ===================================================================
    # CONTROLLER ANIMASI v3 — state, fase, timing, delta-time, jendela hit
    # ===================================================================
    # Batas fase = fraksi 0..1 dari DURASI SERANGAN (progress mentah, sama
    # dengan timeline engine). Batasnya sengaja jatuh di sekitar keyframe
    # _attack_pose (0.14 wind-up, 0.30 tension, 0.48 strike, 0.54 IMPACT,
    # 0.72 follow) supaya nama fase dan pose tidak pernah berbeda satu
    # frame.
    ATTACK_ANTICIPATION_END = 0.16      # counter-motion kecil ke belakang
    ATTACK_WINDUP_END = 0.30            # bilah ditarik + TAHAN (tension)
    ATTACK_SWING_END = 0.46             # tebasan turun (paling cepat)
    ATTACK_IMPACT_END = 0.60            # HOLD impact -> freeze 1-2 frame
    ATTACK_FOLLOW_END = 0.80            # follow-through
    #: jendela di mana bilah secara geometris menyapu depan badan
    ATTACK_ACTIVE_WINDOW = (0.40, 0.66)
    #: puncak benturan (dipakai FX untuk memicu spark "di udara")
    ATTACK_IMPACT_FRAME = 0.54

    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, 0.16),
        ("WINDUP",       0.16, 0.30),
        ("SWING",        0.30, 0.46),
        ("IMPACT",       0.46, 0.60),
        ("FOLLOW",       0.60, 0.80),
        ("RECOVERY",     0.80, 1.00),
    )

    #: Prioritas state. Angka besar menang; DEATH mengunci.
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

    #: Aktifkan untuk melihat hitbox/hurtbox/jangkauan/state di arena
    #: (jalur boss 1:1). Untuk lane hero, overlay yang sama tersedia di
    #: heroes/gorath_fx.DEBUG_CHARACTER.
    DEBUG_CHARACTER = False

    #: LIFT pemetaan lokal -> layar (gorath: jangkar badan = titik gambar).
    LIFT = 0

    def attack_phases_order():
        """Urutan nama fase (dipakai test & alat audit)."""
        return tuple(name for name, _a, _b in _NS_gorath.ATTACK_PHASES)

    def attack_phase(progress):
        """Nama fase serangan untuk progress 0..1 (None di luar serangan)."""
        if progress is None:
            return "NONE"
        p = max(0.0, min(1.0, float(progress)))
        for name, a, b in _NS_gorath.ATTACK_PHASES:
            if a <= p < b:
                return name
        return "RECOVERY"

    def _resolve_anim_state(boss, attacking, phase):
        """Tentukan state animasi yang DIINGINKAN frame ini."""
        if not getattr(boss, "alive", True):
            return "DEATH"
        if int(getattr(boss, "_gor_hurt_frames", 0)) > 0:
            return "HURT"
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

    def _swing_hitbox(boss, cx, cy):
        """Rect hitbox ayunan (ruang permukaan) saat jendela hit aktif.

        Dipakai overlay debug dan alat audit; return None di luar jendela
        hit supaya tidak pernah terlihat seperti "kukri menembus tembok".
        """
        if not getattr(boss, "_gor_hit_active", False):
            return None
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        scale = _NS_gorath._fx_scale(boss)
        reach = int(58 * scale)
        top = int(cy - 34 * scale)
        h = int(64 * scale)
        left = int(cx) if f > 0 else int(cx) - reach
        return pygame.Rect(left, top, max(8, reach), max(10, h))

    def _attack_curve(ap):
        """Remap progres mentah (0..1) -> waktu pose (0..1), MONOTON naik.

        Keyframe _attack_pose sudah punya anticipation & impact; kurva ini
        menambah yang belum ada: (a) wind-up yang sedikit diperlambat
        (counter-motion makin terbaca), (b) tebasan yang "memukul masuk"
        (akselerasi menjelang impact), (c) HOLD 1-2 frame di keyframe
        IMPACT 0.54 (pose squash + bintang + shockwave ikut membeku),
        lalu (d) follow-through yang tidak langsung ditarik balik.
        Nilai di titik kunci fase nyaris identik dengan input mentah,
        sehingga pose _attack_pose(0.30/0.48/0.54/0.72) tetap berada di
        tempat yang sama pada timeline raw.
        """
        if ap <= 0.0:
            return 0.0
        if ap >= 1.0:
            return 1.0
        if ap < 0.44:                       # anticipation + wind-up
            t = ap / 0.44
            return 0.44 * (t ** 0.94)
        if ap < 0.52:                       # tebasan: dipercepat
            t = (ap - 0.44) / 0.08
            return 0.44 + 0.10 * (t ** 1.30)
        if ap < 0.64:                       # IMPACT HOLD (nyaris beku)
            t = (ap - 0.52) / 0.12
            return 0.54 + 0.02 * t
        t = (ap - 0.64) / 0.36              # follow-through -> siap
        return 0.56 + 0.44 * (t ** 0.85)

    def _update_gorath_attack_anim(boss):
        """ANIMATION CONTROLLER GORATH - state, fase, timing, delta-time.

        Satu-satunya sumber kebenaran state karakter. Nama lama tetap
        diisi supaya renderer v2, portrait, dan tools/_audit_gorath_v2.py
        tidak perlu berubah:

        * ``_gor_dt``              delta-time nyata (detik, dijepit)
        * ``_gor_attack_active``   serangan sedang berjalan   (nama lama)
        * ``_gor_attack_frame``    frame ke-n dalam serangan   (nama lama)
        * ``_gor_attack_progress`` 0..1 sepanjang serangan     (nama lama)
        * ``_gor_attack_raw``      progress sebelum kurva
        * ``_gor_attack_phase``    ANTICIPATION/.../RECOVERY
        * ``_gor_hit_active``      True hanya di jendela hit aktif
        * ``_gor_frame_duration``  lama 1 langkah simulasi (untuk HUD)
        * ``_gor_state`` / ``_gor_state_prev`` / ``_gor_state_time``
        * ``_gor_hurt_frames``     sisa frame respons kena damage
        * ``_gor_attack_manual``   mode alat preview: pemanggil menggerakkan
                                   ``_gor_attack_progress`` sendiri
        """
        G = _NS_gorath

        # ── delta time nyata (dipakai FX & transisi state) ───────────
        try:
            now = pygame.time.get_ticks()
        except Exception:                      # pragma: no cover
            now = 0
        prev_ms = getattr(boss, "_gor_last_ms", None)
        if prev_ms is None:
            dt = 1.0 / 60.0
        else:
            dt = (now - prev_ms) / 1000.0
            if dt <= 0.0 or dt > 0.05:
                dt = 1.0 / 60.0
        boss._gor_last_ms = now
        boss._gor_dt = dt

        # ── timeline serangan (kontrak lama: frame engine) ───────────
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 44)))
        span = max(1, cooldown - 1)
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_gor_prev_timer", 0))
        active = bool(getattr(boss, "_gor_attack_active", False))

        # Serangan dikenali dari lompatan timer ke atas (cooldown dipasang
        # saat attack mendarat) ATAU dari detak jam (timer turun ke 0).
        triggered = timer >= cooldown - 1 and previous <= 1
        if triggered:
            boss._gor_attack_active = True
            boss._gor_attack_frame = 0
            boss._gor_attack_manual = False
            active = True
        elif active and not getattr(boss, "_gor_attack_manual", False):
            boss._gor_attack_frame = int(getattr(boss, "_gor_attack_frame",
                                                 0)) + 1
            if boss._gor_attack_frame > cooldown:
                boss._gor_attack_active = False
                boss._gor_attack_frame = 0
                active = False
        elif timer <= 0:
            if active and (getattr(boss, "_gor_attack_manual", False)
                           or float(getattr(boss, "_gor_attack_progress",
                                            0.0)) > 0.0):
                # Mode preview/test (atau serangan yang diaktifkan TANPA
                # menyentuh timer engine): hormati, tandai manual, dan
                # jangan dimatikan di sini.
                boss._gor_attack_manual = True
                active = True
            else:
                boss._gor_attack_active = False
                boss._gor_attack_frame = 0
                active = False

        boss._gor_prev_timer = timer
        frame = int(getattr(boss, "_gor_attack_frame", 0)) if active else 0
        boss._gor_attack_frame = frame
        boss._gor_frame_duration = dt
        if bool(getattr(boss, "_gor_attack_manual", False)) and active:
            # Alat preview / tes menggerakkan progress sendiri: biarkan
            # angka pemanggil dipakai, tetap turunkan fase + jendela hit
            # darinya supaya pose, FX, dan debug membaca sumber yang sama.
            progress = min(1.0, max(0.0, float(getattr(
                boss, "_gor_attack_progress", 0.0))))
            boss._gor_attack_frame = int(round(progress * span))
        else:
            progress = min(1.0, frame / float(span)) if active else 0.0
            boss._gor_attack_progress = progress

        if not getattr(boss, "_gor_attack_active", False):
            boss._gor_attack_manual = False
            active = False
        boss._gor_attack_raw = progress if active else 0.0
        phase = G.attack_phase(progress) if active else "NONE"
        boss._gor_attack_phase = phase
        lo, hi = G.ATTACK_ACTIVE_WINDOW
        boss._gor_hit_active = bool(active and lo <= progress < hi)

        # ── respons kena damage (HURT) ──────────────────────────────
        hurt = int(getattr(boss, "_gor_hurt_frames", 0))
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        if flash >= 8 and hurt <= 0:
            hurt = 10                       # flash baru -> minimal 10 frame
        boss._gor_hurt_frames = max(0, hurt - 1) if hurt > 0 else 0

        # ── state machine ber-prioritas ─────────────────────────────
        want = G._resolve_anim_state(boss, active, phase)
        cur = getattr(boss, "_gor_state", None)
        if cur is None:
            boss._gor_state = want
            boss._gor_state_prev = want
            boss._gor_state_time = 0.0
        elif want != cur:
            cur_p = G.ANIM_STATES.get(cur, 0)
            new_p = G.ANIM_STATES.get(want, 0)
            stime = float(getattr(boss, "_gor_state_time", 0.0))
            if cur != "DEATH" and (new_p >= cur_p or stime > 0.08):
                boss._gor_state_prev = cur
                boss._gor_state = want
                boss._gor_state_time = 0.0
            else:
                boss._gor_state_time = stime + dt
        else:
            boss._gor_state_time = float(getattr(boss, "_gor_state_time",
                                                 0.0)) + dt

    # alias nama lama (dipakai tooling & test v2)
    def _update_attack_anim(boss):
        _NS_gorath._update_gorath_attack_anim(boss)

    def _resolve_pose(boss, moving=False):
        """(action, phase, ap) - dipakai rig DAN anchor FX agar sinkron.

        Murni/tanpa efek samping: boleh dipanggil ulang oleh fungsi efek.
        ``ap`` untuk serangan adalah WAKTU POSE (sudah lewat _attack_curve),
        jadi bilah, trail, dan badan tidak mungkin berbeda frame.
        """
        attacking = (
            getattr(boss, "_gor_attack_active", False)
            or getattr(boss, "timer", 0) >
            getattr(boss, "attack_cooldown", 44) - 15
        )
        if attacking:
            action = "attack"
        elif moving:
            action = "walk"
        else:
            action = "idle"

        phase = float(getattr(boss, "pulse", 0.0))
        if action == "walk":
            phase *= 2.2
        ap = 0.0
        if action == "attack":
            raw = max(0.0, min(1.0, float(getattr(boss, "_gor_attack_raw",
                                                  0.0))))
            ap = _NS_gorath._attack_curve(raw)
        return action, phase, ap

    # ── Pemetaan ruang lokal rig -> layar (dipakai FX eksternal) ─────
    def _rig_shift(action, phase, ap):
        """(lean, root_y) gerak badan dalam ruang lokal (belum * facing)."""
        if action == "attack":
            pose = _NS_gorath._attack_pose(ap)
            sway = 1 if (pose["tremble"] and int(phase * 30) % 2) else 0
            return int(pose["lean"]) + sway, int(pose["dip"])
        if action == "walk":
            return int(math.sin(phase) * 3.0) + 4, \
                int(math.sin(phase * 2.0) * 2.5) - 2
        breath = math.sin(phase * 0.75)
        return int(math.sin(phase * 0.5 + 1.2) * 1.5) + \
            int(math.sin(phase * 0.5) * 2.0), int(breath * 2.2)

    def _local_to_screen(cx, cy, facing, lean, root_y, lx, ly):
        """SATU pemetaan lokal -> layar: skala, arah hadap, bob/lean."""
        f = 1 if facing >= 0 else -1
        k = _NS_gorath.SCALE
        return (int(cx + (lx * f + lean * f) * k),
                int(cy - _NS_gorath.LIFT + (ly + root_y) * k))

    def _local(boss, x, y, action, phase, ap, lx, ly):
        """Ruang lokal rig -> piksel surface (dipakai FX eksternal)."""
        facing = getattr(boss, "direction", 1) or 1
        lean, root_y = _NS_gorath._rig_shift(action, phase, ap)
        return _NS_gorath._local_to_screen(x, y, facing, lean, root_y,
                                           lx, ly)

    # ── Anchor bilah: kembaran matematis dari _draw_attack_arms /
    #    _draw_back_arm / _draw_idle_arms supaya trail & proyektil lahir
    #    PERSIS dari ujung kukri yang sedang digambar badan.
    def _blade_len(action, back=False):
        """Panjang bilah kukri dalam ruang lokal (sama dengan draw)."""
        if action == "attack":
            return 30 * (0.85 if back else 1.15)
        return 30 * (0.85 if back else 1.0)

    def _blade_angle_local(action, phase, ap=0.0, back=False):
        """Sudut bilah (rad) dalam ruang lokal (belum * facing)."""
        if action == "attack":
            pose = _NS_gorath._attack_pose(ap)
            return pose["blade_a"] if back else pose["blade_b"]
        if action == "walk":
            return (1.15, 0.85)[back]
        return (1.05, 0.75)[back]

    def _front_grip_local(action, ap=0.0, phase=0.0):
        """Pergelangan tangan depan (kukri utama), ruang lokal."""
        if action == "attack":
            ang = _NS_gorath._attack_pose(ap)["blade_b"]
            reach = 20 + 10 * math.sin(min(1.0, ap * 1.6) * math.pi)
            return (int(20 + math.cos(ang) * reach),
                    int(-26 + math.sin(ang) * reach + 6))
        if action == "walk":
            swing = math.sin(phase + math.pi) * 8
            return (int(26 + swing), 4)
        bob = math.sin(phase * 0.75 + 0.6) * 1.8
        return (27, int(4 + bob))

    def _back_grip_local(action, ap=0.0, phase=0.0):
        """Pergelangan tangan belakang (kukri kedua), ruang lokal."""
        if action == "attack":
            ang = _NS_gorath._attack_pose(ap)["blade_a"]
            return (int(-20 + math.cos(ang) * 22),
                    int(-26 + math.sin(ang) * 20 + 10))
        if action == "walk":
            swing = math.sin(phase) * 7
            return (int(-24 + swing), 4)
        bob = math.sin(phase * 0.75) * 1.5
        return (-25, int(4 + bob))

    def _tip_local(action, phase, ap=0.0, back=False):
        """Ujung bilah dalam ruang lokal (rig & FX pakai angka yang sama)."""
        grip = (_NS_gorath._back_grip_local(action, ap, phase) if back
                else _NS_gorath._front_grip_local(action, ap, phase))
        ang = _NS_gorath._blade_angle_local(action, phase, ap, back)
        L = _NS_gorath._blade_len(action, back)
        return (int(grip[0] + math.cos(ang) * L),
                int(grip[1] + math.sin(ang) * L))

    def _tip_screen(boss, x, y, back=False):
        """Ujung bilah dalam piksel layar (dipakai FX eksternal)."""
        action, phase, ap = _NS_gorath._resolve_pose(
            boss, bool(getattr(boss, "_moving_cached", False)))
        lx, ly = _NS_gorath._tip_local(action, phase, ap, back)
        return _NS_gorath._local(boss, x, y, action, phase, ap, lx, ly)

    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_gor_projectiles"):
            boss._gor_projectiles = []
        for proj in boss._gor_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._gor_projectiles = [p for p in boss._gor_projectiles
                                 if p.alive or p.age < 8]

    def _spawn_projectile(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_gor_projectiles"):
            boss._gor_projectiles = []
        boss._gor_projectiles.append(
            _NS_gorath.BloodProjectile(sx, sy, tx, ty, speed=6.5))

    # ===================================================================
    # LAPISAN FX HIDUP (heroes/gorath_fx)
    # ===================================================================
    #: Modul FX layar (diisi malas). False = percobaan gagal -> jalur canvas.
    _LIVE_MOD = None

    def _live_module():
        """Muat ``heroes.gorath_fx`` sekali; None kalau tidak tersedia.

        Impor dilakukan DI SINI (bukan di kepala modul) supaya modul boss
        besar tidak menarik paket hero saat build hanya-butuh-renderer, dan
        supaya karakter FX bisa di-matikan lewat satu flag tanpa merusak
        jalur render.
        """
        NS = _NS_gorath
        if NS._LIVE_MOD is None:
            try:
                from heroes import gorath_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "GORATH_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    def live_fx_ready():
        """True kalau lapisan hidup Gorath bisa dipakai (dipakai tooling)."""
        return _NS_gorath._live_module() is not None

    def _live_fx(boss, surface, x, y, want_draw, portrait):
        """Lapisan hidup untuk unit ini.

        Return ``(mod, owned)``:
          * ``mod``   - modulnya (None = jangan gambar lapisan hidup),
          * ``owned`` - True kalau efek ayunan/skill sudah diambil alih
            lapisan hidup, jadi renderer boleh melewati salinan di-canvas.

        ``want_draw`` True pada jalur BOSS (draw dipanggil tiap frame,
        tidak lewat cache sprite). Pada jalur HERO penggambaran dilakukan
        heroes/__init__.py (``_LIVE_FX_HEROES``) supaya lapisan tetap hidup
        walau sprite sedang di-cache - di sini hanya dipasang penanda
        "diambil alih" agar tidak ada efek yang digambar dua kali.
        """
        NS = _NS_gorath
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

    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_gorath(surface, boss, x, y):
        """Entry point Boss.draw() sekaligus heroes.render_hero().

        Urutan lapisan mengikuti kontrak render order proyek:

            GROUND FX -> SHADOW -> BACK PARTICLES -> BODY/ARMOR/HEAD ->
            WEAPON -> ATTACK TRAIL -> PROJECTILE -> FRONT PARTICLES ->
            SKILL FX -> IMPACT FX -> DEBUG

        Trail ayunan, partikel, proyektil darah, impact, screen shake dan
        hit-stop hidup di ``heroes/gorath_fx.py`` (lapisan layar 1:1, di
        luar sprite cache). Semua nama publik lama tetap ada; kalau modul
        FX tidak dimuat, renderer kembali menggambar semuanya di-canvas
        (jalur fallback).
        """
        NS = _NS_gorath
        # jalur hero (lane): heroes/__init__ men-set _render_scale sebelum
        # memanggil renderer, dan sprite-nya di-smoothscale -> pass FX
        # hidup dilakukan heroes/__init__; di sini hanya penanda.
        hero_lane = hasattr(boss, "_render_scale")
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = NS._detect_moving(boss)
        NS._update_gorath_attack_anim(boss)
        action, phase, ap = NS._resolve_pose(boss, moving)
        boss._gor_pose_action = action
        portrait = bool(getattr(boss, "_portrait_hd", False))

        attacking = (
            getattr(boss, "_gor_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 44) - 15
        )

        # Badan ikut bereaksi ke state skill:
        #   q (Bloodrage) -> rune & mata membara, bilah berlumur darah panas
        #   e (Thirst)    -> mata menyala berburu (fokus)
        rage = active_skill in ("q", "r")
        hunting = active_skill in ("e", "w")

        # Jalur boss digambar tiap frame TANPA cache -> lapisan hidup
        # dipicu dari sini. Jalur lane sudah dipicu heroes/__init__.
        live, owned = NS._live_fx(boss, surface, x, y,
                                  not hero_lane, portrait)

        # ---------- Background layers (dibuang di portrait LOD) ----------
        if not portrait:
            NS._draw_blood_aura(surface, x, y, pulse, active_skill)
            NS._draw_ground_blood_pool(surface, x,
                                       y + NS.GROUND_DY - 4,
                                       pulse, active_skill)

            # ---------- Skill ground telegraph ----------
            if active_skill == "q":
                NS._draw_bloodrage_ground(surface, boss, x, y,
                                          skill_timer, pulse)
            elif active_skill == "w":
                NS._draw_bloodrite_ground(surface, boss, x, y,
                                          skill_timer, pulse)
            elif active_skill == "e":
                NS._draw_thirst_ground(surface, boss, x, y,
                                       skill_timer, pulse)
            elif active_skill == "r":
                NS._draw_rupture_ground(surface, boss, x, y,
                                        skill_timer, pulse)

            # AKTIVASI: gelombang kejut + bintang (12 frame pertama).
            # Saat lapisan hidup mengambil alih (owned), gelombang yang
            # hidup digambar oleh lapisan 1:1 — yang di-canvas ini dilewati
            # supaya tidak ada efek ganda.
            if active_skill in ("q", "w", "e", "r") and not owned:
                dur = NS.SKILL_DUR[active_skill]
                age = dur - skill_timer
                if 0 <= age < 12:
                    NS._draw_shockwave(
                        surface, x, y + NS.GROUND_DY, age, 12,
                        NS.PALETTE["blood_hot"],
                        NS.PALETTE["blood_light"],
                        fs=NS._fx_scale(boss))

        # ORIGINAL-MAX hurt flash: badan dibanjiri putih-hangat, bayangan
        # tanah tidak ikut menyala.
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        _tgt, _tx, _ty = surface, x, y
        if flash > 0:
            B = NS
            if B._flash_buf is None:
                B._flash_buf = pygame.Surface((B.RIG_W, B.RIG_H),
                                              pygame.SRCALPHA)
            B._flash_buf.fill((0, 0, 0, 0))
            B._record_shadow = []
            _tgt, _tx, _ty = B._flash_buf, B.RIG_OX, B.RIG_OY

        # ---------- Character ----------
        if attacking:
            _raw = getattr(boss, "_gor_attack_raw", None)
            NS._draw_gorath_attack(_tgt, boss, _tx, _ty, rage=rage,
                                   hunting=hunting, ap=ap, raw=_raw)
        elif moving:
            NS._draw_gorath_walk(_tgt, boss, _tx, _ty,
                                 rage=rage, hunting=hunting)
        else:
            NS._draw_gorath_idle(_tgt, boss, _tx, _ty,
                                 rage=rage, hunting=hunting)

        if flash > 0:
            B = NS
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
        if not portrait:
            NS._manage_projectiles(boss, surface, pulse)

            # ---------- Foreground skill effects (fallback canvas) ----------
            if not owned:
                if active_skill == "q":
                    NS._draw_bloodrage(surface, boss, x, y, skill_timer,
                                       pulse)
                elif active_skill == "w":
                    NS._draw_bloodrite(surface, boss, x, y, skill_timer,
                                       pulse)
                elif active_skill == "e":
                    NS._draw_thirst(surface, boss, x, y, skill_timer, pulse)
                elif active_skill == "r":
                    NS._draw_rupture(surface, boss, x, y, skill_timer, pulse)

        # ── Lapisan hidup bagian ATAS + debug
        if live is not None:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass
        if NS.DEBUG_CHARACTER and not portrait:
            NS._draw_gorath_debug(surface, boss, x, y, action, owned)

    # ===================================================================
    # DEBUG OVERLAY  (DEBUG_CHARACTER = True)
    # ===================================================================
    def _draw_gorath_debug(surface, boss, x, y, action, owned):
        """Hitbox, hurtbox, jangkauan, state/frame, FPS, jumlah partikel.

        Tidak menyentuh gameplay: semua angka dibaca dari state yang sudah
        ada, dan overlay digambar PALING AKHIR supaya tidak pernah tertutup.
        """
        NS = _NS_gorath
        import pygame as _pg

        # ── hurtbox = lingkaran radius unit ─────────────────────────
        r = max(6, int(getattr(boss, "radius", 16) * 0.9 * NS.SCALE))
        _pg.draw.rect(surface, (80, 170, 255, 150),
                      _pg.Rect(int(x) - r, int(y) - r - 8, r * 2, r * 2), 1)

        # ── jangkauan serangan ──────────────────────────────────────
        rng = max(10, int(getattr(boss, "range", 60) * NS.SCALE * 0.9))
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        _pg.draw.line(surface, (255, 210, 60, 150), (int(x), int(y)),
                      (int(x) + int(rng * f), int(y)), 1)
        _pg.draw.rect(surface, (255, 210, 60, 110),
                      _pg.Rect(int(x + rng * f) - 5, int(y) - 7, 10, 14), 1)

        # ── hitbox ayunan (hanya saat jendela hit aktif) ─────────────
        hb = NS._swing_hitbox(boss, x, y)
        if hb is not None:
            _pg.draw.rect(surface, (255, 70, 70, 190), hb, 2)
            _pg.draw.rect(surface, (255, 70, 70, 60), hb)

        # ── tabrakan proyektil milik lapisan hidup ──────────────────
        if owned:
            try:
                mod = NS._LIVE_MOD
                for p in mod.projectiles_for(boss):
                    rr = max(3, int(p.hit_radius))
                    _pg.draw.circle(surface, (255, 120, 255, 170),
                                    (int(p.sx), int(p.sy)), rr, 1)
            except Exception:
                pass

        # ── panel teks ──────────────────────────────────────────────
        fps = getattr(boss, "_gor_fps", None)
        if fps is None:
            boss._gor_fps = 60.0
            fps = 60.0
        else:
            dt = float(getattr(boss, "_gor_dt", 1.0 / 60.0))
            inst = 1.0 / dt if dt > 0 else 60.0
            boss._gor_fps = fps + (inst - fps) * 0.1
            fps = boss._gor_fps
        state = getattr(boss, "_gor_state", "IDLE")
        phase = getattr(boss, "_gor_attack_phase", "NONE")
        frames = int(getattr(boss, "_gor_attack_frame", 0))
        prog = getattr(boss, "_gor_attack_progress", 0.0)
        hit = "HIT" if getattr(boss, "_gor_hit_active", False) else "-"
        skill = getattr(boss, "active_skill", None) or "-"
        stime = getattr(boss, "_gor_state_time", 0.0)
        pc = "-"
        try:
            mod = NS._live_module()
            if mod is not None:
                pc = str(mod.total_particles())
        except Exception:
            pass
        lines = [
            f"GORATH  {state} {stime:.2f}s",
            f"anim    {action}  phase {phase}  f{frames}  p{prog:.2f}",
            f"hit     {hit}  skill {skill}  owned {int(bool(owned))}",
            f"fps     {fps:5.1f}  particles {pc}",
        ]
        try:
            font = pygame.font.SysFont("consolas", 13, bold=True)
        except Exception:                      # pragma: no cover
            font = pygame.font.Font(None, 18)
        yy = int(y) - 120
        xx = int(x) + 30
        for i, ln in enumerate(lines):
            img = font.render(ln, True, (255, 240, 120))
            _pg.draw.rect(surface, (10, 8, 12, 170),
                          (xx - 4, yy + i * 15 - 2,
                           img.get_width() + 8, 15))
            surface.blit(img, (xx, yy + i * 15))

    def _draw_shockwave(surface, x, y, age, total, c1, c2, fs=1.0):
        """Gelombang kejut aktivasi skill - 12 frame pertama.

        World-space: radius dikalikan ``fs`` (= 1/_render_scale) supaya
        ukurannya DI LAYAR setara boss asli.
        """
        t = age / float(total)
        if t >= 1.0:
            return
        P = _NS_gorath.PALETTE
        ease = 1 - (1 - t) ** 2
        r = int((14 + ease * 58) * fs)
        a = _NS_gorath._alpha(235 * (1 - t))
        # muka gelombang: cincin ber-falloff yang MENIPIS saat mengembang
        _NS_gorath._ground_ring(surface, x, y, r, c1, c2, a,
                                thickness=max(1.5, 5 - ease * 3.5),
                                softness=10)
        # kilau susulan di belakang muka gelombang
        _NS_gorath._ground_ring(surface, x, y, int(r * 0.72), c2, P["white"],
                                int(a * 0.55),
                                thickness=max(1.0, 3 - ease * 2), softness=7)
        # kilatan pusat yang cepat padam
        _NS_gorath._glow(surface, x, y, max(6, int(r * 0.5)), c1,
                         int(a * 0.75 * (1 - ease * 0.6)))
        _NS_gorath._spark_star(surface, x, y, int(20 * fs),
                               c2, a, spikes=8, rot=t * 2.2,
                               core=P["white"])

    # ===================================================================
    # POSE MODES  (jangkar tanah = +GROUND_DY; ground FX mengikuti)
    # ===================================================================
    def _draw_gorath_idle(surface, boss, x, y, rage=False, hunting=False):
        phase = float(getattr(boss, "pulse", 0.0))
        bob = int(math.sin(phase * 0.7) * 3 * _NS_gorath.SCALE)
        portrait = bool(getattr(boss, "_portrait_hd", False))
        if not portrait:
            _NS_gorath._draw_shadow(surface, x, y + _NS_gorath.GROUND_DY)
            _NS_gorath._draw_blood_wisps(surface, x, y + 16, phase)
        _NS_gorath._draw_gorath_body(surface, x, y + bob,
                                     getattr(boss, "direction", 1), phase,
                                     "idle", 0, rage=rage, hunting=hunting,
                                     detail=portrait)

    def _draw_gorath_walk(surface, boss, x, y, rage=False, hunting=False):
        phase = float(getattr(boss, "pulse", 0.0)) * 2.2
        k = _NS_gorath.SCALE
        bob = int(abs(math.sin(phase * 1.3)) * 4 * k)
        sway = int(math.sin(phase) * 3 * k)
        portrait = bool(getattr(boss, "_portrait_hd", False))
        if not portrait:
            _NS_gorath._draw_shadow(surface, x + sway,
                                    y + _NS_gorath.GROUND_DY)
            _NS_gorath._draw_blood_wisps(surface, x + sway, y + 16, phase,
                                         trail=True,
                                         facing=getattr(boss, "direction", 1))
        _NS_gorath._draw_gorath_body(surface, x + sway, y - bob,
                                     getattr(boss, "direction", 1), phase,
                                     "walk", 0, rage=rage, hunting=hunting,
                                     detail=portrait)
        if not portrait:
            _NS_gorath._draw_blood_trail(surface, x + sway,
                                         y + _NS_gorath.GROUND_DY - 4, phase,
                                         getattr(boss, "direction", 1))

    def _draw_gorath_attack(surface, boss, x, y, rage=False, hunting=False,
                            ap=None, raw=None):
        """Pose serangan - pose-time (sudah lewat _attack_curve) bila `ap`
        diberikan; fallback ke progress mentah (kontrak v2)."""
        if ap is None:
            progress = getattr(boss, "_gor_attack_progress", 0.0)
            progress = max(0.0, min(1.0, progress))
            raw = progress
            ap = _NS_gorath._attack_curve(progress)
        else:
            progress = max(0.0, min(1.0, float(ap)))
            if raw is None:
                raw = progress
        facing = getattr(boss, "direction", 1)
        phase = float(getattr(boss, "pulse", 0.0))
        pose = _NS_gorath._attack_pose(progress)
        lunge = int(pose["lunge"] * _NS_gorath.SCALE) * facing
        portrait = bool(getattr(boss, "_portrait_hd", False))

        if not portrait:
            _NS_gorath._draw_shadow(surface, x + lunge,
                                    y + _NS_gorath.GROUND_DY)
            _NS_gorath._draw_blood_wisps(surface, x + lunge, y + 16, phase,
                                         intense=True)
        _NS_gorath._draw_gorath_body(surface, x + lunge, y, facing, phase,
                                     "attack", progress, rage=rage,
                                     hunting=hunting, detail=portrait)
        _NS_gorath._draw_blade_swing_arc(surface, x + lunge, y, facing, raw)
        _NS_gorath._draw_swing_impact(surface, x + lunge, y, facing, raw)

    # ===================================================================
    # ATTACK TIMELINE (7 keyframe + frame IMPACT tersendiri)
    # ===================================================================
    def _attack_pose(ap):
        """Interpolasi keyframe serang -> dict pose.

        Keyframe: (progress, lunge, lean, torso_dip, blade_a, blade_b,
                   flare, tremble)
          0.14  wind-up   : bilah ditarik ke belakang, badan mundur
          0.30  tension   : gemetar 1 px, rambut/loincloth tertinggal
          0.48  strike    : ayunan tercepat (smear sabit aktif)
          0.54  IMPACT    : squash + bintang + shockwave + serpihan
          0.72  follow    : rebound overshoot
          1.00  recover   : kembali ke pose istirahat
        """
        keys = (
            (0.00, 0.0,  0.0, 0.0, -0.55, 0.75, 1.00, 0),
            (0.14, -3.0, -5.0, 3.0, -2.25, -1.15, 1.16, 0),
            (0.30, -4.0, -6.0, 4.0, -2.55, -1.45, 1.22, 1),
            (0.48, 7.0,  7.0, -2.0, 0.55, 1.65, 1.10, 0),
            (0.54, 9.0,  9.0, 4.0, 0.95, 2.05, 1.04, 0),
            (0.72, 3.0,  4.0, 1.0, 0.20, 1.25, 1.00, 0),
            (1.00, 0.0,  0.0, 0.0, -0.55, 0.75, 1.00, 0),
        )
        ap = max(0.0, min(1.0, ap))
        for i in range(len(keys) - 1):
            k0, k1 = keys[i], keys[i + 1]
            if k0[0] <= ap <= k1[0]:
                span = max(1e-6, k1[0] - k0[0])
                t = (ap - k0[0]) / span
                t = t * t * (3 - 2 * t)          # smoothstep
                vals = tuple(a + (b - a) * t for a, b in zip(k0[1:7], k1[1:7]))
                return {
                    "lunge": vals[0], "lean": vals[1], "dip": vals[2],
                    "blade_a": vals[3], "blade_b": vals[4],
                    "flare": vals[5],
                    "tremble": 1 if (k0[7] and t < 0.9) else 0,
                    "impact": 1.0 - min(1.0, abs(ap - 0.54) / 0.10),
                }
        return {"lunge": 0.0, "lean": 0.0, "dip": 0.0, "blade_a": -0.55,
                "blade_b": 0.75, "flare": 1.0, "tremble": 0, "impact": 0.0}

    # ===================================================================
    # BODY RENDERING
    # ===================================================================
    def _draw_gorath_body_raw(surface, cx, cy, facing, phase, action,
                              attack_progress=0, rage=False, hunting=False,
                              detail=False):
        """Rig masterwork v2 - demon bloodwarden melayang, 100% prosedural.

        Semua koordinat lokal: (0, 0) = jangkar pinggul, x maju (facing),
        y ke bawah. Rambut memuncak di -74, hem loincloth +32, kabut
        darah menggantikan kaki. Rig ~1.5x versi lama di ruang lokal.
        """
        f = 1 if facing >= 0 else -1
        walk = action == "walk"
        attack = action == "attack"
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0
        breath = math.sin(phase * 0.75)

        # ═══ 1. GERAK BADAN: root / lean / sway + inersia sekunder ═══
        if walk:
            root_y = int(math.sin(phase * 2.0) * 2.5) - 2
            sway = int(math.sin(phase) * 3.0)
            lean = 4 * f
            hair_lag = math.sin(phase + 2.5) * 0.16
            cloth_lag = math.sin(phase + 2.1) * 3.2
            pose = None
        elif attack:
            pose = _NS_gorath._attack_pose(ap)
            root_y = int(pose["dip"])
            sway = 1 if (pose["tremble"] and int(phase * 30) % 2) else 0
            lean = int(pose["lean"]) * f
            hair_lag = -pose["lean"] * 0.035
            cloth_lag = -pose["lean"] * 0.9
        else:
            root_y = int(breath * 2.2)
            sway = int(math.sin(phase * 0.5) * 2.0)
            lean = int(math.sin(phase * 0.5 + 1.2) * 1.5)
            hair_lag = math.sin(phase * 0.6) * 0.05
            cloth_lag = math.sin(phase * 0.55) * 1.6
            pose = None

        off_x = lean + sway
        ox = int(cx) + off_x
        oy = int(cy) + root_y

        # ═══ 2. LAPISAN BELAKANG -> DEPAN ═══
        # kabut darah pengganti kaki (bagian badan, ikut hurt flash).
        # Digambar paling belakang TAPI cukup rendah + lebar agar keluar
        # dari balik hem loincloth - inilah "kaki" siluetnya.
        _NS_gorath._draw_float_plumes(surface, ox, oy + 34, phase, f, action)
        # rambut belakang + loincloth (di belakang torso)
        # Sabuk sedikit di bawah hem torso supaya gesper emas tidak
        # tertutup badan (torso digambar setelahnya).
        _NS_gorath._draw_loincloth(surface, ox, oy + 14, phase, cloth_lag,
                                   rage=rage)
        _NS_gorath._draw_spiky_hair(surface, ox, oy - 52, phase,
                                    lag=hair_lag, back=True, f=f)
        # lengan belakang
        _NS_gorath._draw_back_arm(surface, ox, oy - 30, f, phase, action, ap,
                                  pose, rage=rage)
        # torso -> bahu -> kepala
        _NS_gorath._draw_torso(surface, ox, oy - 14, phase, sway, f=f,
                               rage=rage)
        _NS_gorath._draw_shoulders(surface, ox, oy - 30, phase, f=f)
        _NS_gorath._draw_gorath_head(surface, ox, oy - 52, facing, phase,
                                     rage=rage, hunting=hunting)
        # lengan depan (paling depan) + bilah
        if attack:
            _NS_gorath._draw_attack_arms(surface, ox, oy - 26, facing, phase,
                                         ap, rage=rage)
        else:
            _NS_gorath._draw_idle_arms(surface, ox, oy - 26, facing, phase,
                                       walk=walk, rage=rage)
        # darah menetes dari badan
        _NS_gorath._draw_body_blood_drips(surface, ox, oy, phase)
        if detail:
            _NS_gorath._draw_gorath_masterwork_details(surface, ox, oy, f)

    def _draw_gorath_body(surface, cx, cy, facing, phase, action,
                          attack_progress=0, rage=False, hunting=False,
                          detail=False):
        """Komposit badan: rig native (1.5x) -> buffer -> turun ke SCALE ->
        outline siluet gelap 1 px -> pass cahaya (rim/shade) -> blit.

        Urutan penting: outline & lighting dikerjakan SETELAH penskalaan
        supaya tetap setebal 1 px di layar (konvensi `_finish_hd_sprite`
        di heroes/__init__.py).
        """
        NS = _NS_gorath
        if NS._body_buf is None:
            NS._body_buf = pygame.Surface((NS.RIG_W, NS.RIG_H),
                                          pygame.SRCALPHA)
        buf = NS._body_buf
        buf.fill((0, 0, 0, 0))
        NS._draw_gorath_body_raw(buf, NS.RIG_OX, NS.RIG_OY, facing, phase,
                                 action, attack_progress, rage=rage,
                                 hunting=hunting, detail=detail)
        used = buf.get_bounding_rect(min_alpha=1)
        if used.width <= 2 or used.height <= 2:
            return
        used.inflate_ip(4, 4)
        used.clamp_ip(buf.get_rect())
        sub = buf.subsurface(used).copy()
        # offset jangkar -> sudut kiri-atas crop, dalam px lokal
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
            _lighting.apply_to_rig(sub, rim_add=(46, 18, 16), shade_mul=168)
        surface.blit(sub, (ox, oy))

    # ------------------------------------------------------------------
    # FLOAT SOLVER - dua plume kabut darah bergantian "menapak"
    # ------------------------------------------------------------------
    def _draw_float_plumes(surface, cx, cy, phase, f, action):
        """Pengganti kaki: dua kolom kabut darah dengan siklus kontak.

        Plume kiri/kanan bergantian memanjang & menyentuh tanah
        (`contact`), menghasilkan riak darah - foot solver versi hantu.
        """
        P = _NS_gorath.PALETTE
        speed = 2.2 if action == "walk" else 0.9
        for side in (-1, 1):
            ph = phase * speed + (0 if side < 0 else math.pi)
            contact = (math.sin(ph) + 1) * 0.5          # 0..1
            bx = cx + side * 21
            top = cy - 12
            # kontak penuh -> ujung plume menyentuh FEET_DY (garis tanah)
            length = 16 + contact * 14
            # kolom kabut 3 band (bergerigi -> siluet pixel-art)
            spine = [(bx, top),
                     (bx + side * 5, top + length * .5),
                     (bx + side * (2 if action == "walk" else 4),
                      top + length)]
            for w, col, al in ((15, P["blood_darkest"], 165),
                               (10, P["blood_dark"], 180),
                               (5, P["blood_mid"], 165)):
                pts = _NS_gorath._tuft_points(spine, depth=w * .45,
                                              min_len=6.0,
                                              seed=int(side * 3 + w))
                half = max(1.0, w * .38)
                m = max(1, len(pts) - 1)
                left, right = [], []
                for j, (px, py) in enumerate(pts):
                    # kabut MELEBAR ke bawah (menyebar di tanah)
                    hw = half * (0.45 + 0.55 * j / m)
                    left.append((px - hw, py))
                    right.append((px + hw, py))
                _NS_gorath._poly(surface, (*col, al), left + right[::-1])
            # kabut halo di pangkal plume (menyatukan dua kolom)
            _NS_gorath._aacircle(surface, (*P["blood_darkest"], 120),
                                 (int(bx), int(top + 6)),
                                 int(11 + contact * 3))
            _NS_gorath._aacircle(surface, (*P["blood_dark"], 110),
                                 (int(bx), int(top + 10)),
                                 int(8 + contact * 3))
            # riak darah saat plume menyentuh tanah
            if contact > 0.72:
                a = int(180 * (contact - 0.72) / 0.28)
                rr = int(6 + 7 * contact)
                _NS_gorath._ellipse(surface, (*P["blood_dark"], a),
                                    (bx - rr, int(top + length) - 3,
                                     rr * 2, max(3, rr)), 1)
                _NS_gorath._draw_blood_droplet(surface, bx + side * 3,
                                               int(top + length) - 2, 2, a)

    # ------------------------------------------------------------------
    # LOINCLOTH (hem robek + dither + noda darah)
    # ------------------------------------------------------------------
    def _draw_loincloth(surface, cx, cy, phase, sway, rage=False):
        """Sabuk + gesper emas ber-sigil + 6 helai kain robek."""
        P = _NS_gorath.PALETTE
        # ── sabuk 4 band + selout ──
        _NS_gorath._rect(surface, P["shadow_deep"], (cx - 23, cy - 5, 47, 11))
        _NS_gorath._rect(surface, P["leather_darkest"], (cx - 22, cy - 5, 45, 10))
        _NS_gorath._rect(surface, P["leather_dark"], (cx - 21, cy - 4, 43, 7))
        _NS_gorath._rect(surface, P["leather_mid"], (cx - 20, cy - 3, 41, 3))
        _NS_gorath._aaline(surface, P["leather_light"], (cx - 19, cy - 4),
                           (cx + 8, cy - 4), 1)
        # stud sabuk
        for i in range(-3, 4):
            _NS_gorath._aacircle(surface, P["bone_dark"], (cx + i * 6, cy - 1), 1)
        # ── gesper emas ber-sigil darah ──
        _NS_gorath._aacircle(surface, P["shadow_deep"], (cx + 1, cy + 1), 7)
        _NS_gorath._aacircle(surface, P["gold_dark"], (cx, cy), 6)
        _NS_gorath._aacircle(surface, P["gold_mid"], (cx, cy), 5)
        _NS_gorath._aacircle(surface, P["gold_light"], (cx - 1, cy - 2), 2)
        glow = P["blood_glow"] if rage else P["blood_mid"]
        _NS_gorath._aacircle(surface, P["blood_darkest"], (cx, cy), 3)
        _NS_gorath._aacircle(surface, glow, (cx, cy - 1), 2)
        _NS_gorath._aacircle(surface, P["blood_light"], (cx - 1, cy - 1), 1)

        # ── 6 helai kain robek (hem bergerigi + dither band) ──
        # Tiap helai digambar sebagai POLIGON per band (bukan polyline
        # per-segmen): satu helai = 4 draw call, bukan ~24. Ini bagian
        # terberat rig, jadi bentuknya dijaga tapi jumlah call ditekan.
        for i, offset in enumerate((-18, -11, -4, 3, 10, 17)):
            wave = math.sin(phase * 1.2 + i * .8) * 2.8 + sway * .5
            length = 22 + (i % 3) * 7
            tipx = cx + offset + wave
            spine = [(cx + offset, cy + 4), (cx + offset + wave * .5,
                                             cy + length * .6),
                     (tipx, cy + length)]
            hem = _NS_gorath._tuft_points(spine, depth=2.6, min_len=8.0,
                                          seed=i * 5)

            n_hem = max(1, len(hem) - 1)

            def ribbon(half, off=0):
                """Poligon helai, MERUNCING ke ujung (kain robek).

                Lebar mengecil linear dari pangkal ke ujung supaya
                siluetnya tetap tajam, bukan balok cokelat.
                """
                left, right = [], []
                for j, (px, py) in enumerate(hem):
                    w = half * (1.0 - 0.72 * j / n_hem)
                    left.append((px - w + off, py + off))
                    right.append((px + w + off, py + off))
                return left + right[::-1]

            _NS_gorath._poly(surface, P["shadow_deep"], ribbon(3.2, 1))
            _NS_gorath._poly(surface, P["leather_darkest"], ribbon(2.8))
            _NS_gorath._poly(surface, P["leather_dark"], ribbon(1.9))
            _NS_gorath._poly(surface, P["leather_mid"], ribbon(0.9))
            if i in (1, 4):
                _NS_gorath._aaline(surface, P["leather_light"],
                                   (cx + offset - 1, cy + 6),
                                   (tipx - 1, cy + length - 3), 1)
            # dither band transisi
            _NS_gorath._dither_dots(
                surface, P["leather_light"],
                [(cx + offset + 1, cy + 8 + k * 4) for k in range(4)], 70)
            # noda darah
            if i % 2 == 0:
                _NS_gorath._aacircle(surface, P["blood_darkest"],
                                     (int(cx + offset), cy + length - 8), 3)
                _NS_gorath._aacircle(surface, P["blood_dark"],
                                     (int(cx + offset), cy + length - 8), 2)
                _NS_gorath._aacircle(surface, P["blood_mid"],
                                     (int(cx + offset), cy + length - 9), 1)

    # ------------------------------------------------------------------
    # TORSO (otot + rune darah + kalung trofi + harness X)
    # ------------------------------------------------------------------
    def _draw_torso(surface, cx, cy, phase, sway, f=1, rage=False):
        """Torso berotot 5 band, rune darah berdenyut, harness kulit."""
        P = _NS_gorath.PALETTE
        pulse = math.sin(phase * 1.6) * .5 + .5

        torso = [(cx - 21, cy - 20), (cx + 21, cy - 20),
                 (cx + 20, cy + 16), (cx + 9, cy + 24),
                 (cx - 9, cy + 24), (cx - 20, cy + 16)]
        # selout (sisi bayangan)
        _NS_gorath._poly(surface, P["shadow_deep"],
                         [(px + f, py + 2) for px, py in torso])
        _NS_gorath._poly(surface, P["skin_darkest"], torso)
        _NS_gorath._poly(surface, P["skin_dark"], [
            (cx - 18, cy - 18), (cx + 18, cy - 18),
            (cx + 17, cy + 14), (cx + 7, cy + 21),
            (cx - 7, cy + 21), (cx - 17, cy + 14)])
        _NS_gorath._poly(surface, P["skin_mid"], [
            (cx - 14, cy - 15), (cx + 14, cy - 15),
            (cx + 12, cy + 11), (cx + 4, cy + 17),
            (cx - 4, cy + 17), (cx - 12, cy + 11)])
        # sisi cahaya (kiri-atas) lebih terang
        _NS_gorath._poly(surface, P["skin_light"], [
            (cx - 13, cy - 14), (cx - 3, cy - 14),
            (cx - 4, cy + 8), (cx - 11, cy + 6)])

        # pectoral cluster + specular 1-2 px
        for side in (-1, 1):
            _NS_gorath._aacircle(surface, P["skin_light"],
                                 (cx + side * 8, cy - 6), 6)
            _NS_gorath._aacircle(surface, P["skin_high"],
                                 (cx + side * 8 - 2, cy - 8), 3)
            _NS_gorath._aacircle(surface, P["skin_shine"],
                                 (cx + side * 8 - 3, cy - 10), 1)
        # alur otot + abs
        _NS_gorath._aaline(surface, P["skin_darkest"], (cx, cy - 1),
                           (cx, cy + 19), 1)
        for k, yoff in enumerate((3, 8, 13, 17)):
            _NS_gorath._aaline(surface, P["skin_darkest"],
                               (cx - 8 + k, cy + yoff),
                               (cx + 8 - k, cy + yoff), 1)
        # dither band perut (klasik pixel-art)
        _NS_gorath._dither_dots(surface, P["skin_high"],
                                [(cx - 6 + i * 4, cy + 6) for i in range(5)], 90)

        # ── rune darah di dada (menyala saat skill rage) ──
        rune_c = P["rune_light"] if rage else P["rune_mid"]
        ra = int((150 if not rage else 220) + 60 * pulse)
        for i in range(3):
            ry = cy + 2 + i * 5
            _NS_gorath._aaline(surface, (*P["rune_dark"], 220),
                               (cx - 7 + i, ry), (cx + 7 - i, ry), 3)
            _NS_gorath._aaline(surface, (*rune_c, _NS_gorath._alpha(ra)),
                               (cx - 6 + i, ry), (cx + 6 - i, ry), 1)
        if rage:
            _NS_gorath._aacircle(surface, (*P["blood_glow"],
                                           _NS_gorath._alpha(120 * pulse)),
                                 (cx, cy + 7), 9)

        # ── harness X kulit ber-jahitan ──
        for s in (-1, 1):
            _NS_gorath._aaline(surface, P["leather_darkest"],
                               (cx - s * 17, cy - 18), (cx + s * 12, cy + 20), 6)
            _NS_gorath._aaline(surface, P["leather_dark"],
                               (cx - s * 17, cy - 18), (cx + s * 12, cy + 20), 4)
            _NS_gorath._aaline(surface, P["leather_mid"],
                               (cx - s * 17, cy - 18), (cx + s * 12, cy + 20), 2)
        for i in range(4):
            _NS_gorath._aacircle(surface, P["leather_high"],
                                 (cx - 10 + i * 7, cy - 10 + i * 3), 1)

        # ── noda darah lama di dada ──
        _NS_gorath._aacircle(surface, P["blood_darkest"], (cx - 6, cy + 12), 3)
        _NS_gorath._aacircle(surface, P["blood_dark"], (cx - 6, cy + 12), 2)
        _NS_gorath._aacircle(surface, P["blood_bright"], (cx + 9, cy + 7), 2)

        # ── kalung trofi tulang ──
        _NS_gorath._aaline(surface, P["bone_darkest"], (cx - 12, cy - 17),
                           (cx + 12, cy - 17), 1)
        for i, xoff in enumerate((-9, -3, 3, 9)):
            _NS_gorath._aacircle(surface, P["bone_darkest"],
                                 (cx + xoff + 1, cy - 13), 3)
            _NS_gorath._aacircle(surface, P["bone_dark"], (cx + xoff, cy - 14), 3)
            _NS_gorath._aacircle(surface, P["bone_mid"], (cx + xoff, cy - 14), 2)
            _NS_gorath._aacircle(surface, P["bone_light"],
                                 (cx + xoff - 1, cy - 15), 1)

    # ------------------------------------------------------------------
    # SHOULDERS (pauldron tulang ber-duri)
    # ------------------------------------------------------------------
    def _draw_shoulders(surface, cx, cy, phase, f=1):
        """Bahu berotot + pauldron tulang ber-duri (5 band + specular)."""
        P = _NS_gorath.PALETTE
        for side in (-1, 1):
            sx = cx + side * 20
            _NS_gorath._aacircle(surface, P["shadow_deep"], (sx + f, cy + 2), 12)
            _NS_gorath._aacircle(surface, P["skin_darkest"], (sx, cy), 12)
            _NS_gorath._aacircle(surface, P["skin_dark"], (sx - side, cy - 1), 10)
            _NS_gorath._aacircle(surface, P["skin_mid"], (sx - side * 2, cy - 3), 8)
            _NS_gorath._aacircle(surface, P["skin_light"], (sx - side * 3, cy - 5), 4)
            _NS_gorath._aacircle(surface, P["skin_high"], (sx - side * 4, cy - 6), 2)

            # pauldron tulang (cangkang 4 band)
            cap = [(sx - 11, cy - 3), (sx - 8, cy - 11), (sx + 8, cy - 11),
                   (sx + 11, cy - 3), (sx + 7, cy + 2), (sx - 7, cy + 2)]
            _NS_gorath._poly(surface, P["shadow_deep"],
                             [(px + f, py + 1) for px, py in cap])
            _NS_gorath._poly(surface, P["bone_darkest"], cap)
            _NS_gorath._poly(surface, P["bone_dark"], [
                (sx - 9, cy - 3), (sx - 6, cy - 9), (sx + 6, cy - 9),
                (sx + 9, cy - 3), (sx + 6, cy + 1), (sx - 6, cy + 1)])
            _NS_gorath._poly(surface, P["bone_mid"], [
                (sx - 7, cy - 4), (sx - 4, cy - 8), (sx + 3, cy - 8),
                (sx + 5, cy - 4), (sx + 2, cy - 1), (sx - 5, cy - 1)])
            _NS_gorath._aacircle(surface, P["bone_light"], (sx - 4, cy - 6), 2)
            _NS_gorath._aacircle(surface, P["bone_shine"], (sx - 5, cy - 7), 1)
            # duri tulang 3 buah
            for k, (dx, dl) in enumerate(((-6, 9), (0, 12), (6, 9))):
                tipx, tipy = sx + dx + side * 2, cy - 10 - dl
                _NS_gorath._poly(surface, P["shadow_deep"],
                                 [(sx + dx - 3 + f, cy - 8 + 1),
                                  (sx + dx + 3 + f, cy - 8 + 1),
                                  (tipx + f, tipy + 1)])
                _NS_gorath._poly(surface, P["bone_dark"],
                                 [(sx + dx - 3, cy - 8), (sx + dx + 3, cy - 8),
                                  (tipx, tipy)])
                _NS_gorath._poly(surface, P["bone_mid"],
                                 [(sx + dx - 2, cy - 8), (sx + dx + 1, cy - 8),
                                  (tipx, tipy + 2)])
                _NS_gorath._aaline(surface, P["bone_light"],
                                   (sx + dx - 1, cy - 9), (tipx, tipy + 1), 1)
            # tetes darah dari pauldron belakang
            if side == -1:
                _NS_gorath._draw_blood_streak(surface, sx - 3, cy + 7,
                                              sx - 4, cy + 17, 2, 200)

    # ------------------------------------------------------------------
    # HEAD (tengkorak demon underbite + war-paint + mata menyala)
    # ------------------------------------------------------------------
    def _draw_gorath_head(surface, cx, cy, facing, phase, rage=False,
                          hunting=False):
        """Kepala demon: brow berat, socket cekung, iris menyala + kedip,
        underbite bertaring, tanduk pendek, war-paint darah."""
        P = _NS_gorath.PALETTE
        f = 1 if facing >= 0 else -1
        pulse = math.sin(phase * 2.2) * .5 + .5
        # kedip deterministik: tertutup ~4 frame tiap ~2.6 detik
        blink = (phase % 6.4) < 0.22

        # leher
        _NS_gorath._rect(surface, P["shadow_deep"], (cx - 6 + f, cy + 11, 13, 10))
        _NS_gorath._rect(surface, P["skin_darkest"], (cx - 6, cy + 11, 12, 9))
        _NS_gorath._rect(surface, P["skin_dark"], (cx - 5, cy + 11, 10, 8))
        _NS_gorath._rect(surface, P["skin_mid"], (cx - 3, cy + 11, 6, 5))

        # tengkorak (selout + 4 band)
        _NS_gorath._aacircle(surface, P["shadow_deep"], (cx + f * 2, cy + 2), 16)
        _NS_gorath._aacircle(surface, P["skin_darkest"], (cx, cy), 16)
        _NS_gorath._aacircle(surface, P["skin_dark"], (cx - 1, cy - 1), 14)
        _NS_gorath._aacircle(surface, P["skin_mid"], (cx - 3, cy - 3), 11)
        _NS_gorath._aacircle(surface, P["skin_light"], (cx - 5, cy - 6), 5)
        _NS_gorath._aacircle(surface, P["skin_high"], (cx - 6, cy - 8), 2)

        # ── rahang underbite (dagu maju) + rongga mulut gelap ──
        # Mulut sengaja DI BAWAH garis mata (bukan sejajar) supaya wajah
        # terbaca: brow -> socket -> moncong -> dagu.
        jaw = [(cx - 11, cy + 6), (cx + 13 * f, cy + 5),
               (cx + 14 * f, cy + 14), (cx + 3 * f, cy + 18), (cx - 9, cy + 15)]
        _NS_gorath._poly(surface, P["skin_darkest"], jaw)
        _NS_gorath._poly(surface, P["skin_dark"], [
            (cx - 9, cy + 7), (cx + 11 * f, cy + 6), (cx + 12 * f, cy + 13),
            (cx + 2 * f, cy + 16), (cx - 7, cy + 14)])
        _NS_gorath._aaline(surface, P["skin_mid"], (cx - 7, cy + 8),
                           (cx + 8 * f, cy + 7), 1)
        # rongga mulut gelap (celah underbite)
        _NS_gorath._poly(surface, P["shadow_deep"], [
            (cx - 7, cy + 9), (cx + 11 * f, cy + 8),
            (cx + 10 * f, cy + 12), (cx - 6, cy + 12)])
        # gigi bawah kecil (rapat, 1-2 px - jangan mendominasi wajah)
        for i in range(4):
            tx = cx + (-4 + i * 4) * f
            _NS_gorath._poly(surface, P["bone_mid"],
                             [(tx - 1, cy + 12), (tx + 1, cy + 12),
                              (tx, cy + 9)])
            _NS_gorath._aacircle(surface, P["bone_light"], (tx, cy + 11), 1)
        # taring besar 2 buah, mencuat KE ATAS dari rahang bawah
        for sx2, ln in ((-4, 6), (8, 7)):
            bx = cx + sx2 * f
            _NS_gorath._poly(surface, P["shadow_deep"],
                             [(bx - 2 + f, cy + 13), (bx + 2 + f, cy + 13),
                              (bx + f, cy + 13 - ln)])
            _NS_gorath._poly(surface, P["bone_dark"],
                             [(bx - 2, cy + 12), (bx + 2, cy + 12),
                              (bx, cy + 12 - ln)])
            _NS_gorath._poly(surface, P["bone_light"],
                             [(bx - 1, cy + 12), (bx + 1, cy + 12),
                              (bx, cy + 13 - ln)])
            _NS_gorath._aacircle(surface, P["bone_shine"],
                                 (bx, cy + 13 - ln), 1)

        # war-paint darah: pita tipis di DAHI (di atas mata) + guratan pipi,
        # jadi mata tetap jadi titik fokus.
        paint = [(cx - 13, cy - 12), (cx + 13, cy - 12),
                 (cx + 12, cy - 7), (cx - 12, cy - 7)]
        _NS_gorath._poly(surface, P["blood_darkest"], paint)
        _NS_gorath._poly(surface, P["blood_dark"], [
            (cx - 11, cy - 11), (cx + 11, cy - 11),
            (cx + 10, cy - 8), (cx - 10, cy - 8)])
        _NS_gorath._aaline(surface, P["blood_mid"], (cx - 9, cy - 10),
                           (cx + 8, cy - 10), 1)
        # guratan pipi (dua sisi, melewati socket bukan menutupinya)
        for sxx in (-12, 11):
            _NS_gorath._aaline(surface, P["blood_darkest"],
                               (cx + sxx, cy - 6), (cx + sxx, cy + 4), 3)
            _NS_gorath._aaline(surface, P["blood_mid"],
                               (cx + sxx, cy - 5), (cx + sxx, cy + 2), 1)
        # tetes turun dari pita dahi
        for i, dx in enumerate((-8, 0, 7)):
            dl = 3 + int((math.sin(phase * 0.8 + i) * .5 + .5) * 4)
            _NS_gorath._aaline(surface, P["blood_dark"],
                               (cx + dx, cy - 7), (cx + dx, cy - 7 + dl), 2)
            _NS_gorath._aacircle(surface, P["blood_bright"],
                                 (cx + dx, cy - 7 + dl), 1)

        # brow ridge berat menggantung di atas socket (selout dalam)
        _NS_gorath._poly(surface, P["skin_darkest"], [
            (cx - 14, cy - 7), (cx + 14, cy - 7),
            (cx + 12, cy - 4), (cx - 12, cy - 4)])
        _NS_gorath._aaline(surface, P["skin_light"], (cx - 12, cy - 7),
                           (cx + 4, cy - 8), 1)

        # ── mata: socket cekung + iris menyala + kedip ──
        eye_c = P["eye_hot"] if (rage or hunting) else P["eye_bright"]
        glow_a = _NS_gorath._alpha((130 if (rage or hunting) else 70)
                                   + 60 * pulse)
        for exx in (-7, 6):
            ex = cx + exx * f
            ey = cy - 3
            # socket cekung (lebih gelap dari kulit -> mata "masuk")
            _NS_gorath._aacircle(surface, P["skin_darkest"], (ex, ey), 4)
            _NS_gorath._aacircle(surface, P["eye_dark"], (ex, ey), 3)
            if blink:
                _NS_gorath._aaline(surface, P["skin_dark"], (ex - 3, ey),
                                   (ex + 3, ey), 3)
                continue
            _NS_gorath._aacircle(surface, (*eye_c, glow_a), (ex, ey), 5)
            _NS_gorath._aacircle(surface, eye_c, (ex, ey), 2)
            _NS_gorath._aacircle(surface, P["eye_white"], (ex - 1, ey - 1), 1)

        # hidung / lubang napas (di moncong, bukan di antara mata)
        _NS_gorath._aacircle(surface, P["skin_darkest"], (cx + 7 * f, cy + 2), 2)
        _NS_gorath._aacircle(surface, P["skin_darkest"], (cx + 11 * f, cy + 3), 1)
        _NS_gorath._aaline(surface, P["skin_light"], (cx + 5 * f, cy),
                           (cx + 8 * f, cy + 1), 1)

        # tanduk pendek 2 buah (ivory 3 band, melengkung ke belakang)
        for k, (hx, hy, ang, ln) in enumerate(((-11, -11, -2.45, 15),
                                               (7, -13, -1.15, 13))):
            bx, by = cx + hx * f, cy + hy
            a = ang if f > 0 else math.pi - ang
            _NS_gorath._draw_horn(surface, bx, by, a, ln)

        # rambut depan (di atas dahi)
        _NS_gorath._draw_spiky_hair(surface, cx, cy, phase, lag=0.0,
                                    back=False, f=f)

    def _draw_horn(surface, bx, by, ang, ln):
        """Tanduk ivory melengkung: 3 band + groove + kilau ujung."""
        P = _NS_gorath.PALETTE
        pts = []
        a = ang
        x, y = bx, by
        for i in range(4):
            pts.append((x, y))
            a += 0.22
            step = ln / 4.0
            x += math.cos(a) * step
            y += math.sin(a) * step
        pts.append((x, y))
        for w, col in ((6, P["shadow_deep"]), (5, P["bone_darkest"]),
                       (4, P["bone_dark"]), (2, P["bone_mid"])):
            for i in range(len(pts) - 1):
                off = 1 if col is P["shadow_deep"] else 0
                _NS_gorath._aaline(surface, col,
                                   (pts[i][0] + off, pts[i][1] + off),
                                   (pts[i + 1][0] + off, pts[i + 1][1] + off),
                                   max(1, int(w * (1 - i * 0.12))))
        _NS_gorath._aacircle(surface, P["bone_light"],
                             (int(pts[-1][0]), int(pts[-1][1])), 2)
        _NS_gorath._aacircle(surface, P["bone_shine"],
                             (int(pts[-1][0]) - 1, int(pts[-1][1]) - 1), 1)

    # ------------------------------------------------------------------
    # HAIR (3 lapis, siluet bergerigi, ujung berdarah)
    # ------------------------------------------------------------------
    def _draw_spiky_hair(surface, cx, cy, phase, lag=0.0, back=True, f=1):
        """Rambut liar: lapis belakang (volume) + depan (jambul).

        ``lag`` = inersia (rambut tertinggal dari akselerasi badan).
        """
        P = _NS_gorath.PALETTE
        if back:
            spikes = ((-2.95, 22, 7), (-2.68, 26, 7), (-2.42, 29, 6),
                      (-2.15, 30, 6), (-1.90, 29, 6), (-1.62, 26, 5),
                      (-1.35, 23, 5), (-1.08, 19, 4))
            bands = ((P["hair_darkest"], P["hair_dark"], P["hair_mid"]))
            base_y = 2
        else:
            spikes = ((-2.30, 17, 5), (-2.02, 20, 5), (-1.74, 21, 5),
                      (-1.46, 19, 4), (-1.18, 16, 4))
            bands = ((P["hair_dark"], P["hair_mid"], P["hair_high"]))
            base_y = -6

        for i, (ang, ln, wd) in enumerate(spikes):
            a = (ang + lag * (1 + i * .12))
            a = a if f > 0 else math.pi - a
            bx = cx + math.cos(a) * 6
            by = cy + base_y + math.sin(a) * 4
            wob = math.sin(phase * 1.4 + i * .7) * 0.06
            a += wob
            tipx = bx + math.cos(a) * ln
            tipy = by + math.sin(a) * ln
            px, py = -math.sin(a) * wd, math.cos(a) * wd
            # selout
            _NS_gorath._poly(surface, P["shadow_deep"],
                             [(bx + px + f, by + py + 1),
                              (bx - px + f, by - py + 1),
                              (tipx + f, tipy + 1)])
            _NS_gorath._poly(surface, bands[0],
                             [(bx + px, by + py), (bx - px, by - py),
                              (tipx, tipy)])
            _NS_gorath._poly(surface, bands[1],
                             [(bx + px * .6, by + py * .6),
                              (bx - px * .6, by - py * .6),
                              (tipx - math.cos(a) * 2, tipy - math.sin(a) * 2)])
            _NS_gorath._aaline(surface, bands[2],
                               (bx - px * .5, by - py * .5),
                               (tipx - math.cos(a) * 3, tipy - math.sin(a) * 3), 1)
            # ujung berdarah (helai selang-seling)
            if i % 2 == 0:
                _NS_gorath._aacircle(surface, P["blood_dark"],
                                     (int(tipx), int(tipy)), 2)
                _NS_gorath._aacircle(surface, P["blood_bright"],
                                     (int(tipx), int(tipy)), 1)

    # ------------------------------------------------------------------
    # ARMS + KUKRI
    # ------------------------------------------------------------------
    def _draw_arm_segment(surface, x1, y1, x2, y2, w=7):
        """Segmen lengan berotot: selout + 3 band + rim kiri-atas."""
        P = _NS_gorath.PALETTE
        _NS_gorath._aaline(surface, P["shadow_deep"], (x1 + 1, y1 + 1),
                           (x2 + 1, y2 + 1), w + 2)
        _NS_gorath._aaline(surface, P["skin_darkest"], (x1, y1), (x2, y2), w)
        _NS_gorath._aaline(surface, P["skin_dark"], (x1, y1), (x2, y2), w - 2)
        _NS_gorath._aaline(surface, P["skin_mid"], (x1 - 1, y1 - 1),
                           (x2 - 1, y2 - 1), max(1, w - 4))
        _NS_gorath._aaline(surface, P["skin_light"], (x1 - 2, y1 - 1),
                           (x2 - 2, y2 - 1), 1)

    def _draw_hand(surface, x, y):
        """Kepalan + wrist wrap kulit."""
        P = _NS_gorath.PALETTE
        _NS_gorath._aacircle(surface, P["shadow_deep"], (x + 1, y + 1), 7)
        _NS_gorath._aacircle(surface, P["skin_darkest"], (x, y), 6)
        _NS_gorath._aacircle(surface, P["skin_dark"], (x, y), 5)
        _NS_gorath._aacircle(surface, P["skin_mid"], (x - 1, y - 1), 3)
        _NS_gorath._aacircle(surface, P["skin_high"], (x - 2, y - 2), 1)
        _NS_gorath._rect(surface, P["leather_darkest"], (x - 6, y - 8, 13, 5),
                         border_radius=1)
        _NS_gorath._rect(surface, P["leather_dark"], (x - 5, y - 7, 11, 3))
        _NS_gorath._rect(surface, P["leather_mid"], (x - 4, y - 7, 9, 1))

    def _draw_back_arm(surface, cx, cy, f, phase, action, ap, pose,
                       rage=False):
        """Lengan belakang + kukri kedua (digambar di balik torso)."""
        sx, sy = cx - 20 * f, cy
        if action == "attack" and pose is not None:
            ang = pose["blade_a"]
            ex, ey = sx - 8 * f, sy + 16
            hx, hy = sx + int(math.cos(ang) * 22) * f, sy + int(math.sin(ang) * 20) + 10
        elif action == "walk":
            swing = math.sin(phase) * 7
            ex, ey = sx - 6 * f, sy + 16
            hx, hy = sx - 4 * f + int(swing), sy + 30
            ang = 1.15
        else:
            bob = math.sin(phase * 0.75) * 1.5
            ex, ey = sx - 6 * f, sy + 16
            hx, hy = sx - 5 * f, int(sy + 30 + bob)
            ang = 1.05
        _NS_gorath._draw_arm_segment(surface, sx, sy, ex, ey, 8)
        _NS_gorath._draw_arm_segment(surface, ex, ey, hx, hy, 7)
        _NS_gorath._draw_hand(surface, hx, hy)
        _NS_gorath._draw_curved_blade_angled(surface, hx, hy, -f, ang, phase,
                                             size=0.85, rage=rage)

    def _draw_idle_arms(surface, cx, cy, facing, phase, walk=False,
                        rage=False):
        """Lengan depan saat idle/walk: kukri utama menggantung siaga."""
        f = 1 if facing >= 0 else -1
        sx, sy = cx + 20 * f, cy
        if walk:
            swing = math.sin(phase + math.pi) * 8
            ex, ey = sx + 8 * f, sy + 15
            hx, hy = sx + int(6 * f + swing), sy + 30
            ang = 0.85
        else:
            bob = math.sin(phase * 0.75 + 0.6) * 1.8
            ex, ey = sx + 8 * f, sy + 15
            hx, hy = sx + 7 * f, int(sy + 30 + bob)
            ang = 0.75
        _NS_gorath._draw_arm_segment(surface, sx, sy, ex, ey, 9)
        _NS_gorath._draw_arm_segment(surface, ex, ey, hx, hy, 8)
        _NS_gorath._draw_hand(surface, hx, hy)
        _NS_gorath._draw_curved_blade(surface, hx, hy, f, ang, phase,
                                      rage=rage)

    def _draw_attack_arms(surface, cx, cy, facing, phase, progress,
                          rage=False):
        """Lengan depan saat menyerang - pose-driven dari _attack_pose."""
        f = 1 if facing >= 0 else -1
        pose = _NS_gorath._attack_pose(progress)
        ang = pose["blade_b"]
        sx, sy = cx + 20 * f, cy
        reach = 20 + 10 * math.sin(min(1.0, progress * 1.6) * math.pi)
        ex = sx + int(math.cos(ang - .6) * 16) * f
        ey = sy + int(math.sin(ang - .6) * 14) + 6
        hx = sx + int(math.cos(ang) * reach) * f
        hy = sy + int(math.sin(ang) * reach) + 6
        _NS_gorath._draw_arm_segment(surface, sx, sy, ex, ey, 9)
        _NS_gorath._draw_arm_segment(surface, ex, ey, hx, hy, 8)
        _NS_gorath._draw_hand(surface, hx, hy)
        _NS_gorath._draw_curved_blade_angled(surface, hx, hy, f, ang, phase,
                                             size=1.15, rage=rage,
                                             impact=pose["impact"])

    def _draw_curved_blade(surface, hx, hy, side, tilt, phase, rage=False):
        """Kukri melengkung (pose idle) - 5 band + fuller + darah menetes."""
        _NS_gorath._draw_curved_blade_angled(surface, hx, hy, side, tilt,
                                             phase, size=1.0, rage=rage)

    def _draw_curved_blade_angled(surface, hx, hy, facing, angle, phase,
                                  size=1.0, rage=False, impact=0.0):
        """Kukri: gagang kulit + guard tulang + bilah crescent 5 band,
        fuller gelap, edge highlight, darah, dan glint specular."""
        P = _NS_gorath.PALETTE
        f = 1 if facing >= 0 else -1
        blade_len = 30 * size
        curve = 12 * size
        A = angle if f > 0 else math.pi - angle
        dx, dy = math.cos(A), math.sin(A)
        px, py = -dy, dx

        # ── gagang kulit + pommel tulang ──
        gx, gy = hx - dx * 9, hy - dy * 9
        _NS_gorath._aaline(surface, P["shadow_deep"], (gx + 1, gy + 1),
                           (hx + 1, hy + 1), 7)
        _NS_gorath._aaline(surface, P["leather_darkest"], (gx, gy), (hx, hy), 6)
        _NS_gorath._aaline(surface, P["leather_dark"], (gx, gy), (hx, hy), 4)
        for i in range(3):
            wx = gx + dx * (2 + i * 3)
            wy = gy + dy * (2 + i * 3)
            _NS_gorath._aaline(surface, P["leather_mid"],
                               (wx - px * 3, wy - py * 3),
                               (wx + px * 3, wy + py * 3), 1)
        _NS_gorath._aacircle(surface, P["bone_dark"], (int(gx), int(gy)), 4)
        _NS_gorath._aacircle(surface, P["bone_mid"], (int(gx), int(gy)), 3)
        _NS_gorath._aacircle(surface, P["bone_light"],
                             (int(gx) - 1, int(gy) - 1), 1)
        # guard tulang melintang
        _NS_gorath._aaline(surface, P["bone_darkest"],
                           (hx - px * 7, hy - py * 7),
                           (hx + px * 7, hy + py * 7), 5)
        _NS_gorath._aaline(surface, P["bone_mid"],
                           (hx - px * 6, hy - py * 6),
                           (hx + px * 6, hy + py * 6), 3)
        _NS_gorath._aacircle(surface, P["bone_shine"],
                             (int(hx - px * 5), int(hy - py * 5)), 1)

        # ── bilah crescent ──
        b1 = (hx + px * 4, hy + py * 4)
        b2 = (hx - px * 4, hy - py * 4)
        mid = (hx + dx * blade_len * .55 + px * curve,
               hy + dy * blade_len * .55 + py * curve)
        mid_in = (hx + dx * blade_len * .55 + px * curve * .35,
                  hy + dy * blade_len * .55 + py * curve * .35)
        tip = (hx + dx * blade_len, hy + dy * blade_len)

        _NS_gorath._poly(surface, P["shadow_deep"],
                         [(b1[0] + f, b1[1] + 2), (mid[0] + f, mid[1] + 2),
                          (tip[0] + f, tip[1] + 2), (b2[0] + f, b2[1] + 2)])
        _NS_gorath._poly(surface, P["metal_darkest"], [b1, mid, tip, b2])
        _NS_gorath._poly(surface, P["metal_dark"], [
            (b1[0] - px, b1[1] - py), (mid[0] - px * .7, mid[1] - py * .7),
            tip, b2])
        _NS_gorath._poly(surface, P["metal_mid"], [
            (b1[0] - px * 2, b1[1] - py * 2),
            (mid_in[0], mid_in[1]), tip])
        # fuller gelap (alur bilah)
        _NS_gorath._aaline(surface, P["metal_darkest"],
                           (hx + dx * 8 + px * 2, hy + dy * 8 + py * 2),
                           (hx + dx * blade_len * .8 + px * 3,
                            hy + dy * blade_len * .8 + py * 3), 2)
        # edge highlight (sisi cahaya)
        _NS_gorath._aaline(surface, P["metal_light"],
                           (b1[0] - px * 2, b1[1] - py * 2), tip, 2)
        _NS_gorath._aaline(surface, P["metal_shine"],
                           (mid_in[0], mid_in[1]), tip, 1)
        # specular cluster
        _NS_gorath._aacircle(surface, P["metal_shine"],
                             (int(hx + dx * 14 - px * 2),
                              int(hy + dy * 14 - py * 2)), 2)

        # ── darah di bilah (lebih panas saat rage / impact) ──
        blood_a = 235 if rage else 200
        _NS_gorath._aaline(surface, (*P["blood_darkest"], blood_a),
                           (hx + dx * 10, hy + dy * 10), tip, 3)
        _NS_gorath._aaline(surface, (*(P["blood_hot"] if rage
                                       else P["blood_bright"]), blood_a),
                           (mid[0], mid[1]), tip, 2)
        _NS_gorath._aacircle(surface, P["blood_bright"],
                             (int(mid[0]), int(mid[1])), 3)
        _NS_gorath._aacircle(surface, P["blood_hot"],
                             (int(mid[0]), int(mid[1])), 1)
        _NS_gorath._draw_blood_droplet(surface, int(mid[0]),
                                       int(mid[1]) + 7, 2, 210)
        if impact > 0.05:
            _NS_gorath._spark_star(surface, int(tip[0]), int(tip[1]),
                                   int(14 * impact + 4), P["blood_glow"],
                                   int(230 * impact), spikes=6,
                                   rot=phase, core=P["white"])

    # ------------------------------------------------------------------
    # BODY BLOOD DRIPS / PORTRAIT DETAIL
    # ------------------------------------------------------------------
    def _draw_body_blood_drips(surface, cx, cy, phase):
        """Tetes darah jatuh dari badan (siklus deterministik)."""
        drips = ((-12, 6, 0.0), (10, 12, 0.3), (-5, -10, 0.6), (15, -4, 0.9))
        for dx, dy, offset in drips:
            t = (phase * 0.5 + offset) % 1.0
            drip_y = dy + int(t * 22)
            alpha = int(255 * (1 - t))
            if alpha > 20:
                _NS_gorath._draw_blood_droplet(surface, cx + dx, cy + drip_y,
                                               2, alpha)

    def _draw_gorath_masterwork_details(surface, cx, cy, f):
        """Micro-detail khusus portrait LOD (hilang di skala arena)."""
        P = _NS_gorath.PALETTE
        mix = _NS_gorath._mix
        # pori & scar wajah
        for i in range(5):
            _NS_gorath._aaline(surface, P["skin_high"],
                               (cx - 10 + i * 5, cy - 62),
                               (cx - 8 + i * 5, cy - 58), 1)
        _NS_gorath._aaline(surface, mix(P["skin_shine"], P["white"], .4),
                           (cx - 12, cy - 58), (cx - 4, cy - 60), 1)
        # ukiran rune pada tanduk & taring
        _NS_gorath._aaline(surface, P["bone_shine"], (cx - 14, cy - 62),
                           (cx - 12, cy - 66), 1)
        # jahitan harness
        for i in range(5):
            xx = cx - 14 + i * 7
            _NS_gorath._aaline(surface, P["leather_high"], (cx - 14 + i * 7,
                                                            cy - 18 + i * 2),
                               (xx + 3, cy - 15 + i * 2), 1)
        # kilau gesper & stud sabuk
        _NS_gorath._aacircle(surface, mix(P["gold_light"], P["white"], .5),
                             (cx - 2, cy + 6), 1)
        # serat kain loincloth
        for i in range(4):
            _NS_gorath._aaline(surface, P["leather_light"],
                               (cx - 12 + i * 8, cy + 16),
                               (cx - 11 + i * 8, cy + 26), 1)
        # kabut napas dari mulut
        _NS_gorath._aacircle(surface, (*P["blood_light"], 110),
                             (cx + 18 * f, cy - 40), 2)
        _NS_gorath._aacircle(surface, (*P["blood_light"], 70),
                             (cx + 22 * f, cy - 43), 1)

    # ===================================================================
    # AMBIENT / GROUND FX  (surface statis di-cache)
    # ===================================================================
    def _draw_blood_wisps(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        """Kabut darah naik di bawah badan + droplet orbit (cached mist)."""
        P = _NS_gorath.PALETTE
        strength = 1.5 if intense else 1.0

        def build():
            mist = pygame.Surface((112, 38), pygame.SRCALPHA)
            for radius in range(30, 2, -3):
                alpha = int((30 - radius) * 3.4)
                if alpha > 0:
                    pygame.draw.ellipse(
                        mist, (*P["blood_dark"], min(255, alpha)),
                        (56 - radius * 2, 19 - radius // 3,
                         radius * 4, max(3, radius // 2)))
            return mist
        mist = _NS_gorath._static("wisp_mist", build)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        a = _NS_gorath._alpha(255 * min(1.0, pulse * strength))
        mist.set_alpha(a)
        surface.blit(mist, (cx - 56, cy - 10))
        mist.set_alpha(255)

        # lidah kabut naik (siluet bergerigi)
        for i, offset in enumerate((-18, -7, 7, 18)):
            t = (phase * 0.6 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 22)
            alpha = _NS_gorath._alpha(200 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_gorath._aacircle(surface, (*P["blood_darkest"], alpha), (sx, sy), 4)
            _NS_gorath._aacircle(surface, (*P["blood_dark"], alpha), (sx, sy - 2), 3)
            _NS_gorath._aacircle(surface, (*P["blood_bright"], alpha), (sx, sy - 3), 1)

        # droplet orbit
        for i in range(6):
            angle = phase * 0.7 + i * math.pi / 3
            r = 18 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 7)
            _NS_gorath._draw_blood_droplet(surface, sx, sy, 2, 200)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 9 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 140 - i * 25)
                _NS_gorath._aacircle(surface, (*P["blood_dark"], alpha),
                                     (sx, sy), max(2, 5 - i))
                _NS_gorath._aacircle(surface, (*P["blood_bright"], alpha // 2),
                                     (sx, sy), max(1, 3 - i))

    def _draw_blood_trail(surface, cx, cy, phase, facing):
        """Cipratan darah di tanah saat berjalan."""
        for i in range(4):
            sx = cx - (i + 1) * 14 * facing
            sy = cy + int(math.cos(phase + i) * 2)
            alpha = max(0, 180 - i * 30)
            _NS_gorath._draw_blood_splatter(surface, sx, sy, max(2, 6 - i),
                                            seed=i, alpha=alpha)

    def _draw_shadow(surface, x, y, lift=0):
        """Bayangan tanah (cached + reaktif: menyusut saat badan naik,
        dasar tetap menapak)."""
        NS = _NS_gorath
        if NS._shadow_cache is None:
            shadow = pygame.Surface((78, 20), pygame.SRCALPHA)
            for radius in range(10, 0, -1):
                alpha = max(0, (10 - radius) * 18)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (10 - radius, 10 - radius, 58 + radius * 2, radius * 2))
            pygame.draw.ellipse(shadow, (*NS.PALETTE["blood_darkest"], 100),
                                (7, 4, 64, 10))
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
        by = (y + 10) - h          # bottom tetap di y+10
        surface.blit(spr, (bx, by))
        if NS._record_shadow is not None:
            NS._record_shadow.append(pygame.Rect(bx, by, w, h))

    def _draw_blood_aura(surface, x, y, phase, active_skill):
        """Aura darah latar (cached, berdenyut lewat set_alpha)."""
        NS = _NS_gorath
        if NS._aura_cache is None:
            aura = pygame.Surface((166, 154), pygame.SRCALPHA)
            for radius in range(66, 4, -3):
                alpha = int((66 - radius) * 1.7)
                if alpha > 0:
                    NS._aacircle(aura, (*NS.PALETTE["blood_darkest"],
                                        min(255, alpha)), (83, 77), radius)
            NS._aura_cache = aura
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.5 if active_skill in ("q", "r") else 1.0
        a = _NS_gorath._alpha(255 * min(1.0, pulse * strength))
        spr = NS._aura_cache
        spr.set_alpha(a)
        surface.blit(spr, (x - 83, y - 77))
        spr.set_alpha(255)

    def _draw_ground_blood_pool(surface, x, y, phase, active_skill):
        """Kolam darah + cincin tanah (cached; hanya denyut per frame)."""
        NS = _NS_gorath
        P = NS.PALETTE

        def build():
            pool = pygame.Surface((124, 42), pygame.SRCALPHA)
            pygame.draw.ellipse(pool, (*P["blood_darkest"], 200), (8, 11, 108, 20))
            pygame.draw.ellipse(pool, (*P["blood_dark"], 180), (19, 14, 86, 14))
            pygame.draw.ellipse(pool, (*P["blood_mid"], 120), (29, 17, 66, 9))
            pygame.draw.ellipse(pool, (*P["blood_darkest"], 190), (6, 9, 112, 24), 2)
            # cipratan tepi
            for i in range(10):
                angle = i * math.pi / 5
                px = 62 + int(math.cos(angle) * 49)
                py = 21 + int(math.sin(angle) * 12)
                r = 2 + (i % 3)
                pygame.draw.ellipse(pool, (*P["blood_dark"], 180),
                                    (px - r, py - r // 2, r * 2, max(2, r)))
            return pool
        pool = _NS_gorath._static("ground_pool", build)
        pulse = math.sin(phase * 0.8) * 0.15 + 0.85
        a = _NS_gorath._alpha(255 * pulse)
        pool.set_alpha(a)
        surface.blit(pool, (x - 62, y - 21))
        pool.set_alpha(255)

        # quill/serpihan tulang kecil tertanam di cincin
        for i in range(8):
            angle = phase * 0.18 + i * math.pi / 4
            sx = x + int(math.cos(angle) * 50)
            sy = y + int(math.sin(angle) * 11)
            _NS_gorath._aaline(surface, (*P["bone_dark"], 190), (sx, sy),
                               (sx + int(math.cos(angle) * 5),
                                sy - 5), 2)
            _NS_gorath._aacircle(surface, (*P["bone_light"], 190),
                                 (sx + int(math.cos(angle) * 5), sy - 5), 1)

        if active_skill:
            # Rim mengikuti bentuk KOLAM (elips), bukan lingkaran AOE.
            # Bayangan/kolam karakter memang digambar pipih; telegraph
            # jangkauan yang lingkaran penuh adalah bidang berbeda.
            color = (P["blood_glow"] if active_skill in ("q", "r")
                     else P["blood_bright"])
            a = int(150 * pulse)
            for k, (grow, al) in enumerate(((6, .35), (3, .65), (0, 1.0))):
                _NS_gorath._ellipse(
                    surface, (*_NS_gorath._mix(P["blood_mid"], color, al),
                              int(a * al)),
                    (x - 56 - grow, y - 19 - grow // 2,
                     112 + grow * 2, 38 + grow), 2)

    # ===================================================================
    # MELEE SWING FX (smear sabit 3 lapis + IMPACT)
    # ===================================================================
    def _draw_blade_swing_arc(surface, x, y, facing, progress):
        """Smear sabit ayunan: 3 lapis (gelap lebar -> panas sempit)."""
        if progress < 0.24 or progress > 0.78:
            return
        P = _NS_gorath.PALETTE
        if progress < 0.52:
            visibility = (progress - 0.24) / 0.28
        else:
            visibility = 1.0 - (progress - 0.52) / 0.26
        visibility = max(0.0, min(1.0, visibility))
        f = 1 if facing >= 0 else -1
        k = _NS_gorath.SCALE

        for lap, (rad, wid, col, base_a) in enumerate((
                (58 * k, max(3, int(11 * k)), P["blood_darkest"], 190),
                (54 * k, max(2, int(7 * k)), P["blood_mid"], 210),
                (50 * k, max(1, int(4 * k)), P["blood_bright"], 230))):
            pts = []
            for i in range(15):
                t = i / 14.0
                angle = -math.pi * 0.95 + t * math.pi * 1.15
                pts.append((x + math.cos(angle) * rad * f,
                            y + math.sin(angle) * rad * .78 + 4))
            a = _NS_gorath._alpha(base_a * visibility)
            for i in range(len(pts) - 1):
                _NS_gorath._aaline(surface, (*col, a), pts[i], pts[i + 1], wid)
        # leading edge panas
        te = -math.pi * 0.95 + (0.55 + 0.35 * visibility) * math.pi * 1.15
        _NS_gorath._aacircle(surface, (*P["blood_hot"],
                                       _NS_gorath._alpha(240 * visibility)),
                             (int(x + math.cos(te) * 50 * k * f),
                              int(y + math.sin(te) * 39 * k + 4)),
                             max(2, int(4 * k)))

    def _draw_swing_impact(surface, x, y, facing, progress):
        """Frame IMPACT: ring + bintang + serpihan + cipratan."""
        if progress < 0.46 or progress > 0.84:
            return
        P = _NS_gorath.PALETTE
        t = (progress - 0.46) / 0.38
        intensity = math.sin(t * math.pi)
        f = 1 if facing >= 0 else -1
        k = _NS_gorath.SCALE

        ix = int(x + 42 * k * f)
        iy = int(y + 6 * k)
        alpha = _NS_gorath._alpha(235 * intensity)
        radius = max(3, int((10 + intensity * 26) * k))

        _NS_gorath._glow(surface, ix, iy, radius + 6, P["blood_dark"],
                         int(alpha * 0.7))
        _NS_gorath._ground_ring(surface, ix, iy, radius, P["blood_mid"],
                                P["blood_hot"], alpha,
                                thickness=max(1.5, 3.5 - intensity * 1.5),
                                softness=7)
        _NS_gorath._spark_star(surface, ix, iy, int(radius * 1.25),
                               P["blood_hot"], alpha, spikes=8,
                               rot=progress * 3, core=P["white"])
        # serpihan batu / percikan
        for i in range(8):
            angle = i * math.pi / 4 + progress * 3
            dx = ix + int(math.cos(angle) * radius * 1.25)
            dy = iy + int(math.sin(angle) * radius * 0.9)
            _NS_gorath._draw_blood_droplet(surface, dx, dy, 3, alpha)
        # retakan tanah pendek
        for i in range(3):
            _NS_gorath._jagged_crack(surface, ix, iy + 8,
                                     (i - 1) * .7 + (0 if f > 0 else math.pi),
                                     max(4, int(20 * intensity * k)),
                                     (P["blood_darkest"], P["blood_mid"]),
                                     alpha, seed=i + 11, width=2)

    # ===================================================================
    # SKILL Q: BLOODRAGE (self-buff, 90 frame)
    #   AKTIVASI : pilar darah + shockwave ganda + bintang
    #   STEADY   : aura 3 lapis + mahkota api darah + bara naik + glint
    #   TELEGRAPH: rune ring ganda berlawanan + retakan radial
    # ===================================================================
    def _draw_bloodrage_ground(surface, boss, x, y, timer, phase):
        """Telegraph tanah Q: rune ring ganda + retakan magma darah."""
        P = _NS_gorath.PALETTE
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        fs = _NS_gorath._fx_scale(boss)
        pulse = math.sin(phase * 3) * .5 + .5
        gy = y + _NS_gorath.GROUND_DY

        # rune ring ganda berputar berlawanan arah; ring luar MENGEMBANG
        # seiring buff naik supaya 3 tahap (aktivasi/steady/telegraph)
        # terbaca jelas walau ini skill self-buff.
        grow = 0.55 + 0.45 * progress
        # alas gosong: buff "membakar" tanah di bawah kaki
        _NS_gorath._ground_scorch(surface, x, gy, int(50 * fs * grow),
                                  P["blood_darkest"], P["shadow_deep"],
                                  int(110 + 60 * progress), seed=6)
        _NS_gorath._rune_ring(surface, x, gy, int(46 * fs * grow),
                              P["blood_bright"], P["blood_glow"],
                              int(160 + 60 * pulse),
                              phase * 1.3 + progress * 2.4,
                              segments=12, span=.46, thickness=3.2)
        _NS_gorath._rune_ring(surface, x, gy, int(34 * fs * grow),
                              P["blood_glow"], P["white"],
                              int(140 + 60 * pulse),
                              -phase * 1.8 - progress * 3.1,
                              segments=8, span=.5, thickness=2.4)
        # chevron berbaris ke dalam (telegraph "buff mengunci")
        for k in range(4):
            da = k * math.pi / 2 + progress * 1.1
            _NS_gorath._chevron(surface,
                                x + math.cos(da) * 40 * fs * grow,
                                gy + math.sin(da) * 17 * fs * grow,
                                da + math.pi, max(6, int(8 * fs)),
                                P["blood_light"], int(120 + 90 * pulse), 3)
        # retakan magma darah radial (memanjang mengikuti progress)
        for i in range(6):
            ang = i * math.pi * 2 / 6 + .3
            _NS_gorath._jagged_crack(surface, x, gy, ang,
                                     int((30 + (i % 3) * 10) * fs * grow),
                                     (P["blood_darkest"], P["blood_mid"]),
                                     130 + int(60 * pulse), seed=i + 2, width=2)
        # glow lantai hangat (radial ter-cache, bukan elips datar)
        _NS_gorath._glow(surface, x, gy, int(56 * fs * grow),
                         P["blood_dark"], int(90 + 50 * pulse))

    def _draw_bloodrage(surface, boss, x, y, timer, phase):
        """Q foreground: pilar aktivasi, mahkota api darah, bara, glint."""
        P = _NS_gorath.PALETTE
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        fs = _NS_gorath._fx_scale(boss)
        cx, cy = x, y - 12

        # ── AKTIVASI: pilar darah 4 lapis + shockwave ganda + bintang ──
        if progress < 0.18:
            t = progress / 0.18
            top = int(cy - min(100 * fs, 240) * (0.6 + 0.4 * (1 - t)))
            for wd, col, al in ((32, P["blood_darkest"], 110),
                                (20, P["blood_dark"], 150),
                                (11, P["blood_bright"], 190),
                                (4, P["blood_glow"], 220)):
                _NS_gorath._aaline(surface, (*col, int(al * (1 - t))),
                                   (cx, top), (cx, cy), wd)
            _NS_gorath._aaline(surface, (*P["blood_seam"], int(200 * (1 - t))),
                               (cx, top), (cx, cy), 2)
            for k, rmax in ((0, 120), (1, 86)):
                r = int((16 + t * rmax) * fs)
                # gelombang menipis saat mengembang (thickness ikut t)
                _NS_gorath._ground_ring(
                    surface, cx, cy, r,
                    P["blood_mid"] if k == 0 else P["blood_bright"],
                    P["blood_hot"] if k == 0 else P["white"],
                    int((225 if k == 0 else 155) * (1 - t)),
                    thickness=max(1.5, 4 - t * 2.5), softness=9)
            _NS_gorath._spark_star(surface, cx, cy, int(32 * (1 - t * .4)),
                                   P["blood_glow"], int(235 * (1 - t)),
                                   8, rot=.3, core=P["white"])

        # ── STEADY: mahkota api darah 2 ring ──
        for ring_i, (n, r0, sc) in enumerate(((10, 34, 1.0), (7, 22, .72))):
            for i in range(n):
                ang = i * math.pi * 2 / n + phase * (.5 if ring_i else .85)
                r = r0 * fs
                px = cx + math.cos(ang) * r
                py = cy + 14 + math.sin(ang) * r * .55
                for h in range(3):
                    fy = py - h * 7 - int((phase * 26 + i * 3) % 20)
                    alpha = _NS_gorath._alpha(210 * (1 - h / 3) * pulse)
                    rad = max(1, int((4 - h) * sc))
                    _NS_gorath._aacircle(surface, (*P["blood_bright"], alpha),
                                         (int(px), int(fy)), rad)
                    _NS_gorath._aacircle(surface, (*P["blood_hot"], alpha),
                                         (int(px), int(fy)), max(1, 2 - h // 2))

        # ── STEADY: aura berlapis (glow radial, bukan 3 stroke cincin) ──
        breathe = math.sin(phase * 2) * 4
        _NS_gorath._glow(surface, cx, cy, int((46 + breathe) * fs),
                         P["blood_dark"], int(120 * (0.7 + 0.3 * pulse)))
        _NS_gorath._glow(surface, cx, cy, int((30 + breathe * .6) * fs),
                         P["blood_glow"], int(150 * (0.7 + 0.3 * pulse)))

        # ── STEADY: kolom bara naik (sway per-ember) ──
        for i in range(10):
            t = (phase * .35 + i / 10.0) % 1.0
            ex = cx + math.sin(i * 2.1 + phase) * (12 + i * 4) * fs * .5
            ey = cy + 20 - t * 96 * fs
            _NS_gorath._aacircle(surface, (*P["blood_hot"],
                                           _NS_gorath._alpha(210 * (1 - t))),
                                 (int(ex), int(ey)), 2 if i % 2 else 1)

        # ── STEADY: glint orbit ──
        for i in range(5):
            a = phase * 1.9 + i * math.pi * 2 / 5
            rr = 40 * fs
            _NS_gorath._spark_star(surface, cx + math.cos(a) * rr,
                                   cy + math.sin(a) * rr * .55, 7,
                                   P["blood_light"], 190, spikes=4,
                                   rot=a, core=P["white"])

        # ── denyut pusat (inti membara ber-falloff) ──
        _NS_gorath._glow(surface, cx, cy + 6, int((24 + 6 * pulse) * fs),
                         P["blood_bright"], int(185 * pulse))
        _NS_gorath._glow(surface, cx, cy + 6, int((11 + 4 * pulse) * fs),
                         P["blood_glow"], int(225 * pulse))

    # ===================================================================
    # SKILL W: BLOODRITE (AOE 150 px dunia di sekitar diri, 60 frame)
    #   TELEGRAPH: ring jangkauan TEPAT 150 + ring konvergen + chevron
    #   AKTIVASI : shockwave ganda + bintang di pusat
    #   STEADY   : hujan duri darah + splat marker
    # ===================================================================
    def _draw_bloodrite_ground(surface, boss, x, y, timer, phase):
        """Telegraph W: cincin jangkauan world-space (150 px dunia)."""
        P = _NS_gorath.PALETTE
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        gy = y + _NS_gorath.GROUND_DY - 8
        rng = _NS_gorath._ring_r(boss, _NS_gorath.SKILL_RADIUS["w"], surface)

        # 1) ALAS: tanah gosong -> telegraph menempel, bukan overlay UI
        _NS_gorath._ground_scorch(surface, x, gy, rng, P["blood_darkest"],
                                  P["shadow_deep"],
                                  int(120 + 40 * progress), seed=4)
        # 2) wash zona: pekat di tepi, bening di tengah -> badan tetap
        #    terbaca sementara batas jangkauan jelas
        _NS_gorath._zone_fill(surface, x, gy, rng, P["blood_dark"],
                              int(90 + 90 * progress))
        # 3) BATAS jangkauan: cincin ber-falloff, bukan stroke datar
        _NS_gorath._ground_ring(surface, x, gy, rng, P["blood_mid"],
                                P["blood_hot"], int(150 + 70 * pulse),
                                thickness=3, softness=8)
        # 4) rune ring berputar tepat di dalam batas
        _NS_gorath._rune_ring(surface, x, gy, int(rng * .87), P["blood_bright"],
                              P["blood_glow"], int(160 + 60 * pulse),
                              phase * 1.1, segments=14, span=.34,
                              thickness=3.0)
        # 5) sapuan konvergen TIPIS: hanya muncul di paruh akhir cast,
        #    jadi tidak menambah "cincin ketiga" sepanjang durasi.
        if progress > 0.45:
            ct = (progress - 0.45) / 0.55
            conv = rng * (1 - ct * .82)
            _NS_gorath._ground_ring(surface, x, gy, max(10, int(conv)),
                                    P["blood_bright"], P["blood_light"],
                                    int(70 + 150 * ct),
                                    thickness=1.5, softness=4)
        # 6) chevron kardinal (tetap vektor: bentuknya memang tajam)
        for da in (0, math.pi / 2, math.pi, math.pi * 1.5):
            _NS_gorath._chevron(surface,
                                x + math.cos(da) * rng * .62,
                                gy + math.sin(da) * rng * .62,
                                da + math.pi, max(8, int(rng * .11)),
                                P["blood_light"], 195, 3)
        # 7) marker target: reticle ber-glow
        tx, ty = _NS_gorath._target_position(boss, x, y)
        _NS_gorath._glow(surface, tx, ty, int(24 + progress * 10),
                         P["blood_dark"], int(150 * pulse))
        _NS_gorath._ground_ring(surface, tx, ty, int(20 + progress * 12),
                                P["blood_hot"], P["blood_light"],
                                int(210 * pulse), thickness=2, softness=5)

    def _draw_bloodrite(surface, boss, x, y, timer, phase):
        """W foreground: voli proyektil + duri darah meletus di target."""
        P = _NS_gorath.PALETTE
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        fs = _NS_gorath._fx_scale(boss)
        tx, ty = _NS_gorath._target_position(boss, x, y)

        # spawn proyektil di awal + muzzle star
        if progress < 0.1 and not getattr(boss, "_gor_bloodrite_spawned", False):
            for i in range(3):
                offset_x = (i - 1) * 25
                _NS_gorath._spawn_projectile(boss, x, y - 16, tx + offset_x, ty)
            boss._gor_bloodrite_spawned = True
            _NS_gorath._spark_star(surface, x, y - 16, int(18 * fs),
                                   P["blood_glow"], 235, 7, rot=phase,
                                   core=P["white"])
        if progress > 0.4:
            boss._gor_bloodrite_spawned = False

        # duri darah meletus di target
        if progress > 0.4:
            erupt_t = min(1.0, (progress - 0.4) / 0.3)
            radius = int(50 * fs)
            for i in range(12):
                angle = i * math.pi * 2 / 12
                spike_x = tx + int(math.cos(angle) * radius * 0.7)
                spike_y = ty + int(math.sin(angle) * radius * 0.4)
                spike_h = int(24 * erupt_t)
                _NS_gorath._poly(surface, P["shadow_deep"], [
                    (spike_x - 3, spike_y + 1), (spike_x + 4, spike_y + 1),
                    (spike_x + 1, spike_y - spike_h)])
                _NS_gorath._poly(surface, P["blood_darkest"], [
                    (spike_x - 3, spike_y), (spike_x + 3, spike_y),
                    (spike_x, spike_y - spike_h)])
                _NS_gorath._poly(surface, P["blood_dark"], [
                    (spike_x - 2, spike_y), (spike_x + 2, spike_y),
                    (spike_x, spike_y - spike_h + 2)])
                _NS_gorath._poly(surface, P["blood_bright"], [
                    (spike_x - 1, spike_y), (spike_x + 1, spike_y),
                    (spike_x, spike_y - spike_h + 4)])
                _NS_gorath._aacircle(surface, P["blood_hot"],
                                     (spike_x, spike_y - spike_h + 2), 1)

            # duri pusat (lebih besar) + bintang impact
            big_h = int(36 * erupt_t)
            _NS_gorath._poly(surface, P["blood_darkest"], [
                (tx - 6, ty), (tx + 6, ty), (tx, ty - big_h)])
            _NS_gorath._poly(surface, P["blood_mid"], [
                (tx - 4, ty), (tx + 4, ty), (tx, ty - big_h + 3)])
            _NS_gorath._poly(surface, P["blood_bright"], [
                (tx - 2, ty), (tx + 2, ty), (tx, ty - big_h + 5)])
            _NS_gorath._spark_star(surface, tx, ty - big_h,
                                   int(16 * erupt_t * fs), P["blood_glow"],
                                   int(230 * erupt_t), spikes=6, rot=phase,
                                   core=P["white"])
            # splat marker 2 cincin
            _NS_gorath._ground_ring(surface, tx, ty, int(radius * .8),
                                    P["blood_mid"], P["blood_hot"],
                                    int(210 * erupt_t),
                                    thickness=2.5, softness=6)
            _NS_gorath._rune_ring(surface, tx, ty, int(radius * 1.05),
                                  P["blood_light"], P["white"],
                                  int(180 * erupt_t), -phase * 2.0,
                                  segments=10, span=.46, thickness=2.4)
            # cipratan
            for i in range(8):
                angle = i * math.pi / 4 + phase
                px = tx + int(math.cos(angle) * 34 * erupt_t * fs)
                py = ty + int(math.sin(angle) * 17 * erupt_t * fs) - 5
                _NS_gorath._draw_blood_droplet(surface, px, py, 2,
                                               int(255 * erupt_t))

    # ===================================================================
    # SKILL E: THIRST (leap AOE 85 px dunia, 35 frame)
    #   TELEGRAPH: ring AOE 85 di target + chevron berbaris di jalur
    #   AKTIVASI : garis lompat + bintang
    #   STEADY   : crosshair berdenyut + partikel pelacak
    # ===================================================================
    def _draw_thirst_ground(surface, boss, x, y, timer, phase):
        """Telegraph E: ring AOE 85 px dunia di target + chevron jalur."""
        P = _NS_gorath.PALETTE
        duration = 35
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 3.2) * 0.3 + 0.7
        tx, ty = _NS_gorath._target_position(boss, x, y)
        rng = _NS_gorath._ring_r(boss, _NS_gorath.SKILL_RADIUS["e"], surface)

        # alas gosong + area membara di titik pendaratan
        _NS_gorath._ground_scorch(surface, tx, ty, rng, P["blood_darkest"],
                                  P["shadow_deep"],
                                  int(130 + 50 * progress), seed=9)
        _NS_gorath._zone_fill(surface, tx, ty, rng, P["blood_dark"],
                              int(100 + 110 * progress))
        # batas AOE tepat di radius gameplay (falloff, additive)
        _NS_gorath._ground_ring(surface, tx, ty, rng, P["blood_mid"],
                                P["blood_hot"], int(160 + 70 * pulse),
                                thickness=3, softness=8)
        _NS_gorath._rune_ring(surface, tx, ty, int(rng * .82),
                              P["blood_bright"], P["blood_glow"],
                              int(165 + 60 * pulse), phase * 1.6,
                              segments=10, span=.44, thickness=3.2)
        # sapuan konvergen -> "hentakan datang" (hanya paruh akhir)
        if progress > 0.4:
            ct = (progress - 0.4) / 0.6
            conv = rng * (1 - ct * .85)
            _NS_gorath._ground_ring(surface, tx, ty, max(8, int(conv)),
                                    P["blood_bright"], P["blood_light"],
                                    int(80 + 160 * ct),
                                    thickness=1.5, softness=4)
        # retakan pendaratan
        for i in range(5):
            ang = i * math.pi * 2 / 5 + .4
            _NS_gorath._jagged_crack(surface, tx, ty, ang, int(rng * .55),
                                     (P["blood_darkest"], P["blood_mid"]),
                                     int(120 + 70 * progress), seed=i + 5,
                                     width=2)
        # chevron berbaris di jalur lompat
        sx, sy = x, y - 12
        dxx, dyy = tx - sx, ty - sy
        dist = math.hypot(dxx, dyy) or 1.0
        ang = math.atan2(dyy, dxx)
        n = max(2, min(7, int(dist / 34)))
        for i in range(n):
            t = ((i + 1) / (n + 1) + phase * 0.16) % 1.0
            _NS_gorath._chevron(surface, sx + dxx * t, sy + dyy * t, ang,
                                11, P["blood_light"],
                                int(120 + 110 * (1 - abs(t - .5) * 2)), 3)

    def _draw_thirst(surface, boss, x, y, timer, phase):
        """E foreground: beam pelacak, crosshair, dan partikel darah."""
        P = _NS_gorath.PALETTE
        duration = 35
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        fs = _NS_gorath._fx_scale(boss)
        tx, ty = _NS_gorath._target_position(boss, x, y)

        start_x = x + 8 * getattr(boss, "direction", 1)
        start_y = y - 16

        # AKTIVASI: kilat lompat
        if progress < 0.22:
            t = progress / 0.22
            _NS_gorath._aaline(surface, (*P["blood_glow"], int(220 * (1 - t))),
                               (start_x, start_y), (tx, ty), int(7 * (1 - t)) + 2)
            _NS_gorath._spark_star(surface, start_x, start_y,
                                   int(22 * fs * (1 - t * .5)), P["blood_hot"],
                                   int(235 * (1 - t)), 8, rot=phase,
                                   core=P["white"])

        # beam pelacak 3 lapis
        for i in range(3):
            offset = (i - 1) * 2
            alpha = int(90 - i * 22)
            _NS_gorath._aaline(surface, (*P["blood_bright"], alpha),
                               (start_x, start_y + offset), (tx, ty + offset), 2)
        _NS_gorath._aaline(surface, (*P["blood_hot"], 205),
                           (start_x, start_y), (tx, ty), 1)

        # crosshair berdenyut
        marker_r = int((16 + math.sin(phase * 3) * 3) * fs)
        _NS_gorath._glow(surface, tx, ty, marker_r + 6, P["blood_dark"],
                         int(150 * pulse))
        _NS_gorath._ground_ring(surface, tx, ty, marker_r, P["blood_bright"],
                                P["blood_hot"], int(235 * pulse),
                                thickness=2, softness=5)
        for angle in (0, math.pi / 2, math.pi, math.pi * 1.5):
            x1 = tx + int(math.cos(angle) * (marker_r - 3))
            y1 = ty + int(math.sin(angle) * (marker_r - 3))
            x2 = tx + int(math.cos(angle) * (marker_r + 7))
            y2 = ty + int(math.sin(angle) * (marker_r + 7))
            _NS_gorath._aaline(surface, P["blood_bright"], (x1, y1), (x2, y2), 2)
            _NS_gorath._aaline(surface, P["blood_hot"], (x1, y1), (x2, y2), 1)
        _NS_gorath._aacircle(surface, P["blood_hot"], (tx, ty), 3)
        _NS_gorath._aacircle(surface, P["blood_light"], (tx, ty), 1)

        # partikel pelacak mengalir ke target + glint
        for i in range(6):
            t = (phase * 0.5 + i * 0.16) % 1.0
            px = int(start_x + (tx - start_x) * t)
            py = int(start_y + (ty - start_y) * t)
            _NS_gorath._aacircle(surface, (*P["blood_bright"], 210), (px, py), 3)
            _NS_gorath._aacircle(surface, (*P["blood_hot"], 245), (px, py), 1)
            if i % 3 == 0:
                _NS_gorath._spark_star(surface, px, py, 6, P["blood_light"],
                                       180, spikes=4, rot=phase + i)

    # ===================================================================
    # SKILL R: RUPTURE (ultimate, AOE 190 px dunia, 90 frame)
    #   TELEGRAPH: ring 190 px dunia + chevron kardinal + retakan
    #   AKTIVASI : pilar cahaya darah + shockwave ganda + bintang
    #   STEADY   : rantai darah ke target + ledakan + duri + wisp spiral
    # ===================================================================
    def _draw_rupture_ground(surface, boss, x, y, timer, phase):
        """Telegraph R: ring AOE 190 px dunia di CASTER + retakan magma."""
        P = _NS_gorath.PALETTE
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.2 + 0.8
        fs = _NS_gorath._fx_scale(boss)
        gy = y + _NS_gorath.GROUND_DY
        rng = _NS_gorath._ring_r(boss, _NS_gorath.SKILL_RADIUS["r"], surface)

        # alas gosong besar + inti membara (ultimate = paling "berat")
        _NS_gorath._ground_scorch(surface, x, gy, rng, P["blood_darkest"],
                                  P["shadow_deep"],
                                  int(140 + 50 * progress), seed=2)
        _NS_gorath._zone_fill(surface, x, gy, rng, P["blood_dark"],
                              int(110 + 110 * progress))
        # batas jangkauan tepat di radius gameplay
        _NS_gorath._ground_ring(surface, x, gy, rng, P["blood_mid"],
                                P["blood_hot"], int(155 + 70 * pulse),
                                thickness=4, softness=10)
        # SATU rune ring di dalam batas (dua ring berputar berlawanan
        # arah saling bersaing dan membuat area terbaca sebagai target
        # practice, bukan telegraph).
        _NS_gorath._rune_ring(surface, x, gy, int(rng * .86), P["blood_bright"],
                              P["blood_glow"], int(155 + 60 * pulse),
                              phase * .9, segments=16, span=.36,
                              thickness=3.4)
        # sapuan konvergen hanya di paruh akhir
        if progress > 0.5:
            ct = (progress - 0.5) / 0.5
            conv = rng * (1 - ct * .74)
            _NS_gorath._ground_ring(surface, x, gy, max(12, int(conv)),
                                    P["blood_bright"], P["blood_light"],
                                    int(80 + 150 * ct),
                                    thickness=2, softness=5)
        # chevron kardinal + diagonal
        for k in range(6):
            da = k * math.pi / 3
            _NS_gorath._chevron(surface,
                                x + math.cos(da) * rng * .58,
                                gy + math.sin(da) * rng * .35,
                                da + math.pi, max(8, int(rng * .09)),
                                P["blood_light"], 190, 3)
        # 6 retakan magma radial + seam menyala di 2 cabang
        for i in range(6):
            ang = i * math.pi * 2 / 6 + .35
            _NS_gorath._jagged_crack(surface, x, gy, ang,
                                     int((42 + (i % 3) * 14) * fs),
                                     (P["blood_darkest"], P["blood_mid"]), 145,
                                     seed=i + 3, width=3)
        seam = int(120 + 110 * pulse)
        for i in (0, 3):
            ang = i * math.pi * 2 / 6 + .35
            _NS_gorath._jagged_crack(surface, x, gy, ang,
                                     int((28 + (i % 3) * 12) * fs),
                                     (P["blood_mid"], P["blood_glow"]), seam,
                                     seed=i + 3, width=1)
        # kolam darah membesar di pusat
        radius = int((22 + progress * 26) * fs)
        _NS_gorath._ellipse(surface, (*P["blood_darkest"], int(200 * pulse)),
                            (x - radius, gy - radius // 3, radius * 2,
                             max(4, int(radius / 1.5))))
        _NS_gorath._ellipse(surface, (*P["blood_dark"], int(180 * pulse)),
                            (x - radius + 5, gy - radius // 3 + 2,
                             max(4, radius * 2 - 10),
                             max(3, int(radius / 1.5) - 4)))

    def _draw_rupture(surface, boss, x, y, timer, phase):
        """R foreground: pilar aktivasi, rantai darah, ledakan target,
        duri menyembur, wisp spiral."""
        P = _NS_gorath.PALETTE
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 4) * 0.3 + 0.7
        fs = _NS_gorath._fx_scale(boss)
        tx, ty = _NS_gorath._target_position(boss, x, y)
        cx, cy = x, y - 14

        # ── AKTIVASI: pilar cahaya darah 4 lapis + shockwave ganda ──
        if progress < 0.16:
            t = progress / 0.16
            top = int(cy - min(100 * fs, 240) * (0.6 + 0.4 * (1 - t)))
            for wd, col, al in ((34, P["blood_darkest"], 120),
                                (22, P["blood_dark"], 155),
                                (12, P["blood_bright"], 195),
                                (5, P["blood_glow"], 225)):
                _NS_gorath._aaline(surface, (*col, int(al * (1 - t))),
                                   (cx, top), (cx, cy), wd)
            _NS_gorath._aaline(surface, (*P["blood_seam"], int(210 * (1 - t))),
                               (cx, top), (cx, cy), 3)
            for k, rmax in ((0, 130), (1, 92)):
                r = int((18 + t * rmax) * fs)
                _NS_gorath._ground_ring(
                    surface, cx, cy, r,
                    P["blood_mid"] if k == 0 else P["blood_bright"],
                    P["blood_hot"] if k == 0 else P["white"],
                    int((230 if k == 0 else 160) * (1 - t)),
                    thickness=max(1.5, 4.5 - t * 3), softness=10)
            _NS_gorath._spark_star(surface, cx, cy, int(36 * (1 - t * .4)),
                                   P["blood_glow"], int(240 * (1 - t)),
                                   8, rot=.3, core=P["white"])

        # ── rantai darah bergelombang ke target ──
        start_x = cx + 14 * getattr(boss, "direction", 1)
        start_y = cy
        segments = 9
        prev = (start_x, start_y)
        for i in range(1, segments + 1):
            t = i / segments
            mx = start_x + (tx - start_x) * t
            my = start_y + (ty - start_y) * t
            wiggle = math.sin(phase * 3 + i) * 3
            mx += wiggle if i < segments else 0
            curr = (int(mx), int(my))
            _NS_gorath._aaline(surface, P["blood_darkest"], prev, curr, 6)
            _NS_gorath._aaline(surface, P["blood_mid"], prev, curr, 4)
            _NS_gorath._aaline(surface, P["blood_bright"], prev, curr, 2)
            if i % 3 == 0:
                _NS_gorath._aacircle(surface, P["blood_dark"], curr, 5)
                _NS_gorath._aacircle(surface, P["blood_bright"], curr, 3)
                _NS_gorath._aacircle(surface, P["blood_hot"], curr, 1)
                _NS_gorath._spark_star(surface, curr[0], curr[1], 7,
                                       P["blood_light"], 180, spikes=4,
                                       rot=phase + i)
            prev = curr

        # ── wisp spiral 2 lengan di sekitar caster ──
        for arm in range(2):
            for j in range(6):
                a = phase * 2.2 + arm * math.pi + j * .52
                rr = (14 + j * 7) * fs
                al = _NS_gorath._alpha(150 * (1 - j / 6))
                _NS_gorath._aacircle(surface, (*P["blood_glow"], al),
                                     (int(cx + math.cos(a) * rr),
                                      int(cy + math.sin(a) * rr * .55)), 2)

        # ── ledakan di target ──
        if progress > 0.4:
            explosion_t = min(1.0, (progress - 0.4) / 0.5)
            radius = int((16 + explosion_t * 32) * fs)
            _NS_gorath._glow(surface, tx, ty, radius + 8, P["blood_darkest"],
                             int(210 * pulse))
            _NS_gorath._glow(surface, tx, ty, radius, P["blood_mid"],
                             int(225 * pulse))
            _NS_gorath._glow(surface, tx, ty, max(3, radius - 8),
                             P["blood_bright"], int(240 * pulse))
            _NS_gorath._glow(surface, tx, ty, max(2, radius - 15),
                             P["blood_hot"], int(255 * pulse))
            _NS_gorath._spark_star(surface, tx, ty, int(radius * 1.2),
                                   P["blood_glow"], int(235 * explosion_t),
                                   spikes=8, rot=phase * .6, core=P["white"])
            _NS_gorath._rune_ring(surface, tx, ty, int(radius * 1.4),
                                  P["blood_light"], P["white"],
                                  int(200 * explosion_t), -phase * 2.4,
                                  segments=12, span=.46, thickness=2.6)
            # duri menyembur keluar
            for i in range(10):
                angle = i * math.pi / 5 + phase * 0.5
                sp_len = int(radius * 1.35)
                sx1 = tx + int(math.cos(angle) * radius * 0.5)
                sy1 = ty + int(math.sin(angle) * radius * 0.5)
                sx2 = tx + int(math.cos(angle) * sp_len)
                sy2 = ty + int(math.sin(angle) * sp_len)
                _NS_gorath._aaline(surface, P["blood_darkest"], (sx1, sy1),
                                   (sx2, sy2), 4)
                _NS_gorath._aaline(surface, P["blood_bright"], (sx1, sy1),
                                   (sx2, sy2), 2)
                _NS_gorath._draw_blood_droplet(surface, sx2, sy2, 2, 220)

        # ── denyut pusat (inti membara ber-falloff) ──
        _NS_gorath._glow(surface, cx, cy, int((26 + 6 * pulse) * fs),
                         P["blood_bright"], int(190 * pulse))
        _NS_gorath._glow(surface, cx, cy, int((12 + 4 * pulse) * fs),
                         P["blood_glow"], int(230 * pulse))

    # ===================================================================
    # Backward compatible alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_gorath.draw_gorath(surface, boss, x, y)


# ====================================================================
# ALCHEMIST
# ====================================================================
class _NS_alchemist:
    """Namespace ALCHEMIST — PIXEL MASTERWORK v2 + COMBAT FX v3.

    FULL REWRITE dari rig ORIGINAL-MAX lama, mengikuti standar
    **Gorath v2 Pixel Masterwork + Razak v3 Combat FX**
    (docs/GORATH_V2_RENDERER.md, docs/RAZAK_V3_COMBAT_FX.md).
    Tetap 100% prosedural: tidak ada file gambar / sprite-sheet /
    pemuatan aset eksternal. Semua bentuk lahir dari pygame.draw +
    Surface + transform + mask.

    Apa yang naik dibanding rig lama
    --------------------------------
    1. RIG LEBIH BESAR & BERLAPIS (shadow -> back limb -> body -> armor
       -> head -> weapon -> front limb -> highlights). Ogre duo (ogre
       + goblin rider) tinggi ~150 px di jalur boss: true boss level-2
       kembali paling besar di keluarganya (test_level2_masterwork).
       Siluet kuat: massa ogre + dua cleaver + backpack botol + topi
       goblin mudah dikenali dari kejauhan.
    2. ANIMATION CONTROLLER: state ANIM_PRIORITY (IDLE..DEATH), delta
       time nyata (bus heroes/combat_feel), kurva pose MONOTON
       (_attack_curve) dengan anticipation / wind-up / swing / IMPACT
       hold / follow-through / recovery, jendela hit aktif
       (_alch_hit_active), transisi antar state berprioritas.
    3. SWING ARC-BASED: cleaver bergerak menyusui busur (sudut ->
       posisi), bukan lerp posisi awal->akhir; keyframe 7 titik +
       tremble wind-up + squash IMPACT + canvas trail fallback.
    4. SKILL FX world-space: telegraph digambar TEPAT di radius
       gameplay (Q cone / W 100 / E 90 / R 200 px dunia) lewat
       _ring_r, memakai decal ber-falloff yang DI-CACHE
       (_ground_ring / _zone_fill / _DECAL_CACHE, LRU 48).
    5. PERFORMANCE: stamp lingkaran-alpha di-cache (bukan Surface baru
       per panggilan), aura/mist/rune/arc statis di _STATIC_SURFACES,
       pose badan di-cache per kuantum pose (LRU) lalu satu blit,
       outline siluet tetap 1 px. Budget: < 2.2 ms/frame (mobile).
    6. LAPISAN HIDUP heroes/alchemist_fx.py: trail cleaver 60 fps,
       partikel, proyektil botol asam, impact FX, hit-stop 0.03-0.08 s,
       screen shake, skill lifecycle CAST->..->FADE, overlay DEBUG.
       Renderer memicu timingnya; kalau modul itu tidak ada, semua FX
       kembali digambar di canvas (jalur fallback lengkap).
    """

    # ------------------------------------------------------------------
    # Compatibility / konfigurasi umum
    # ------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    # ── cache (nama lama dipertahankan) ─────────────────────────────
    _shadow_cache = None
    _aura_cache = {}        # key: "acid"/"gold"
    _flash_buf = None
    _body_buf = None        # buffer badan untuk outline+lighting
    _record_shadow = None
    _STATIC_SURFACES = {}   # stamp statis (mist/rune/arc/pile)
    _CIRCLE_STAMPS = {}     # stamp lingkaran alpha (radius, width, rgba)
    _DECAL_CACHE = {}       # decal tanah (ground ring / zone fill)
    _DECAL_ORDER = []
    _POSE_CACHE = {}        # pose badan komposit (key -> (surf, ax, ay))
    _POSE_ORDER = []

    #: Overlay debug renderer (hitbox/hurtbox/jangkauan/state/FPS).
    DEBUG_CHARACTER = False

    #: Ukuran buffer badan & jangkar. Extents terukur dari semua pose:
    #: botol W -77 (glow), e_cast hop -83, kaki +60, bayangan +73,
    #: wisps mist +73, swing lunge +-88 -> buffer 180x166 berpusat
    #: di (90, 86).
    RIG_W, RIG_H = 180, 166
    RIG_OX, RIG_OY = 90, 86

    #: Rig di-author di RUANG LAYAR (SCALE 1.0) — jalur boss langsung
    #: 1:1; jalur hero di-normalisasi heroes/__init__ lewat pengukuran
    #: native, jadi satu-satunya skala tetap 1.0 di sini.
    SCALE = 1.0

    #: Garis tanah dunia relatif jangkar (kaki / bayangan / decal).
    GROUND_DY = 62

    #: Durasi visual skill (frame) - HARUS sama dengan active_skill_timer
    #: yang diisi AI (bosses/base_boss.py & hero_skills/_bundle.py).
    SKILL_DUR = {"q": 40, "w": 60, "e": 60, "r": 90}

    #: Radius gameplay tiap skill dalam PX DUNIA:
    #:   q -> cone + genangan di target (visual ~100),
    #:   w -> AOE 100 di titik target (base_boss: <= 100),
    #:   e -> buff diri (denyut ~90 visual),
    #:   r -> AOE 200 di sekitar DIRI (base_boss: <= 200).
    SKILL_RADIUS = {"q": 100, "w": 100, "e": 90, "r": 200}

    #: Prioritas state animasi (angka besar menang; DEATH mengunci).
    #: Cermin tabel di heroes/alchemist_fx.py (satu bahasa state).
    ANIM_PRIORITY = {
        "IDLE": 10, "WALK": 20, "RUN": 25, "CHARGE": 40,
        "ATTACK": 45, "SWING": 50, "CAST": 55, "SKILL": 56,
        "SPECIAL": 60, "HIT": 62, "HURT": 65, "DEATH": 100,
    }

    #: Timeline serangan (fraksi progress mentah 0..1). Satu sumber
    #: kebenaran untuk renderer, canvas trail, lapisan hidup, dan
    #: overlay debug. 0.30 wind-up penuh, 0.54 IMPACT (damage AI
    #: mendarat di frame-0; pose impact ditaruh DINI supaya pembacaan
    #: "pukulan -> efek" tetap rapat).
    ATTACK_WINDUP_END = 0.30
    ATTACK_IMPACT = 0.54
    ATTACK_SWING_END = 0.62
    ATTACK_FOLLOW_END = 0.80
    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, 0.10),
        ("WINDUP",       0.10, 0.30),
        ("SWING",        0.30, 0.46),
        ("IMPACT",       0.46, 0.62),
        ("FOLLOW",       0.62, 0.80),
        ("RECOVERY",     0.80, 1.00),
    )

    #: Geometri cleaver (px layar; dipakai FX hidup & canvas trail).
    CLEAVER_BLADE = 26
    CLEAVER_HANDLE = 9

    #: Modul FX hidup (diisi malas; False = gagal -> jalur canvas).
    _LIVE_MOD = None

    # ------------------------------------------------------------------
    # PALETTE — dark fantasy ogre chemist: orange ogre / ungu goblin /
    # acid green / gold / kuningan / kulit samak / baja. Semua kunci
    # lama dipertahankan; kunci baru untuk ramp rage & decal.
    # ------------------------------------------------------------------
    PALETTE = {
        # Ogre skin - orange/yellow (bayangan didorong coklat-ungu)
        "ogre_darkest":   (38,  20,   8),
        "ogre_dark":      (96,  52,  16),
        "ogre_mid":       (158, 98,  32),
        "ogre_light":     (205, 143, 52),
        "ogre_high":      (232, 182, 92),
        "ogre_shine":     (250, 222, 140),
        "ogre_rim":       (255, 238, 178),

        # Goblin (rider) - purple (bayangan biru gelap)
        "gob_darkest":    (24,  14,  38),
        "gob_dark":       (58,  34,  88),
        "gob_mid":        (104, 66, 140),
        "gob_light":      (156, 110, 192),
        "gob_high":       (204, 162, 230),
        "gob_rim":        (232, 198, 248),

        # Acid green
        "acid_darkest":   (12,  36,   8),
        "acid_dark":      (40,  88,  16),
        "acid_mid":       (86, 156,  24),
        "acid_bright":    (150, 222,  46),
        "acid_hot":       (198, 246,  84),
        "acid_glow":      (232, 255, 150),
        "acid_white":     (246, 255, 214),

        # Gold (Greevil's Greed)
        "gold_darkest":   (48,  30,   8),
        "gold_dark":      (116,  76,  12),
        "gold_mid":       (196, 150,  34),
        "gold_light":     (244, 208,  78),
        "gold_shine":     (255, 242, 160),

        # Leather / straps
        "leather_darkest": (18,  11,   6),
        "leather_dark":   (44,  28,  15),
        "leather_mid":    (86,  57,  29),
        "leather_light":  (138,  96,  52),
        "leather_high":   (182, 136,  84),

        # Metal (cleavers, armor)
        "metal_darkest":  (14,  14,  17),
        "metal_dark":     (40,  40,  47),
        "metal_mid":      (82,  82,  94),
        "metal_light":    (142, 140, 156),
        "metal_shine":    (204, 204, 218),
        "metal_edge":     (244, 244, 255),

        # Brass
        "brass_dark":     (72,  46,  12),
        "brass_mid":      (148, 104, 36),
        "brass_light":    (208, 166, 74),
        "brass_shine":    (246, 218, 132),

        # Bottle glass
        "glass_dark":     (18,  46,  14),
        "glass_mid":      (50, 104,  26),
        "glass_light":    (112, 178,  54),
        "glass_shine":    (188, 236, 128),

        # Teeth / tusks
        "bone_dark":      (96,  82,  58),
        "bone_mid":       (172, 156, 116),
        "bone_light":     (228, 216, 178),

        # Eyes
        "eye_dark":       (5,  35,   5),
        "eye_hot":        (255, 240, 100),
        "eye_rage":       (140, 255,  70),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (5,   3,   3),
        "white":          (255, 255, 255),
        "red":            (200, 40,  30),
    }

    # ==================================================================
    # PRIMITIF PIXEL — clamp + stamp cache (tidak ada Surface baru
    # per panggilan untuk lingkaran alpha; inilah sumber frame-time
    # rig lama yang bocor).
    # ==================================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _circle_stamp(radius, width, color):
        """Lingkaran alpha SIAP-BLIT, di-cache per (r, w, rgba)."""
        NS = _NS_alchemist
        key = (radius, width, color)
        stamp = NS._CIRCLE_STAMPS.get(key)
        if stamp is None:
            d = radius * 2 + 2
            stamp = pygame.Surface((d, d), pygame.SRCALPHA)
            pygame.draw.circle(stamp, color, (radius + 1, radius + 1),
                               radius, width)
            if len(NS._CIRCLE_STAMPS) >= 320:
                NS._CIRCLE_STAMPS.pop(next(iter(NS._CIRCLE_STAMPS)))
            NS._CIRCLE_STAMPS[key] = stamp
        return stamp

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_alchemist._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            stamp = _NS_alchemist._circle_stamp(radius, max(1, width),
                                                color)
            surface.blit(stamp, (cx - radius - 1, cy - radius - 1))
            return
        if _NS_alchemist.HAS_AACIRCLE and radius > 2:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy),
                                     radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_alchemist._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            # garis alpha pendek: poligon 4 titik (tanpa Surface baru)
            import math as _m
            ang = _m.atan2(ey - sy, ex - sx)
            px, py = -_m.sin(ang), _m.cos(ang)
            hw = max(1, width) / 2.0
            pts = [(sx + px * hw, sy + py * hw),
                   (ex + px * hw, ey + py * hw),
                   (ex - px * hw, ey - py * hw),
                   (sx - px * hw, sy - py * hw)]
            _NS_alchemist._poly(surface, color, pts)
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey),
                         max(1, width))

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_alchemist._clamp(color)
        pts = [(int(p[0]), int(p[1])) for p in points]
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            min_x, min_y = min(xs) - 1, min(ys) - 1
            w = max(xs) - min_x + 2
            h = max(ys) - min_y + 2
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in pts]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], pts)

    def _ellipse(surface, color, rect, width=0):
        color = _NS_alchemist._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw, rh), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (0, 0, rw - 1, rh - 1),
                                width)
            surface.blit(temp, (rx, ry))
            return
        pygame.draw.ellipse(surface, color[:3],
                            (int(rect[0]), int(rect[1]), int(rect[2]),
                             int(rect[3])), width)

    def _rect(surface, color, rect, border_radius=0):
        color = _NS_alchemist._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw, rh), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (0, 0, rw - 1, rh - 1),
                             border_radius=border_radius)
            surface.blit(temp, (rx, ry))
            return
        pygame.draw.rect(surface, color[:3], rect,
                         border_radius=border_radius)

    # ── fx scale: efek world-space di jalur hero (canvas di-scale) ──
    def _fx_scale(boss):
        """Faktor skala efek skill (world-space). Jalur boss = 1.0."""
        scale = getattr(boss, "_render_scale", None)
        if not scale:
            return 1.0
        return max(1.0, min(2.6, 1.0 / float(scale)))

    def _ring_r(boss, world_px, surface):
        """Radius dunia (px) -> px canvas, di-clamp ke dalam canvas."""
        scale = getattr(boss, "_render_scale", None)
        r = float(world_px) / float(scale) if scale else float(world_px)
        margin = min(surface.get_width(), surface.get_height()) // 2 - 10
        return int(max(4, min(r, margin)))

    # ==================================================================
    # DECAL TANAH TER-CACHE  (soft falloff, bukan stroke keras)
    # ==================================================================
    def _decal(w, h, builder):
        """Surface decal (w,h) dibangun sekali oleh builder lalu LRU."""
        NS = _NS_alchemist
        key = (w, h, id(builder))
        surf = NS._DECAL_CACHE.get(key)
        if surf is None:
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            builder(surf, w, h)
            NS._DECAL_CACHE[key] = surf
            NS._DECAL_ORDER.append(key)
            while len(NS._DECAL_ORDER) > 48:
                old = NS._DECAL_ORDER.pop(0)
                NS._DECAL_CACHE.pop(old, None)
        return surf

    def _blit_decal(surface, decal, cx, cy, alpha=255):
        if alpha <= 2:
            return
        if alpha >= 250:
            surface.blit(decal, (int(cx - decal.get_width() / 2),
                                 int(cy - decal.get_height() / 2)))
            return
        tmp = decal.copy()
        tmp.fill((255, 255, 255, int(alpha)),
                 special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(tmp, (int(cx - tmp.get_width() / 2),
                           int(cy - tmp.get_height() / 2)))

    def _ground_ring(surface, cx, cy, radius, c1, c2, alpha,
                     thickness=3, softness=7):
        """Cincin AOE ber-gradien (tepi lunak) — decal ter-cache."""
        NS = _NS_alchemist
        radius = max(3, int(radius))
        pad = softness + thickness + 3

        def build(s, w, h):
            steps = softness + thickness + softness
            for i in range(steps):
                t = i / float(max(1, steps - 1))     # 0 luar -> 1 dalam
                # radius band: mulai di radius-softness naik ke
                # radius+thickness lalu turun -> profil falloff lunak
                r = radius - softness + t * (softness * 2 + thickness)
                a = int(max(0.0, 1.0 - abs(r - radius - thickness / 2.0)
                            / (softness + thickness / 2.0)) * alpha)
                if a <= 2:
                    continue
                col = c2 if r < radius else c1
                NS._aacircle(s, (*col, a), (w // 2, h // 2),
                             max(1, int(r)))

        d = radius + pad
        decal = NS._decal(d * 2, d * 2, build)
        NS._blit_decal(surface, decal, cx, cy)

    def _zone_fill(surface, cx, cy, radius, color, alpha):
        """Wash zona: pekat di TEPI, bening di tengah (badan terbaca)."""
        NS = _NS_alchemist
        radius = max(3, int(radius))

        def build(s, w, h):
            steps = 7
            for i in range(steps):
                t = i / float(steps)               # 0 tepi -> 1 tengah
                r = radius * (1.0 - t * 0.86)
                a = int(alpha * (1.0 - t) ** 1.5)
                if a <= 2:
                    continue
                NS._aacircle(s, (*color, a), (w // 2, h // 2),
                             max(1, int(r)))

        d = radius + 3
        decal = NS._decal(d * 2, d * 2, build)
        NS._blit_decal(surface, decal, cx, cy)

    def _ground_glow(surface, cx, cy, radius, color, alpha):
        """Genangan cahaya di tanah (falloff pusat->tepi)."""
        NS = _NS_alchemist
        radius = max(3, int(radius))

        def build(s, w, h):
            for i in range(8):
                t = i / 8.0
                a = int(alpha * (1.0 - t) ** 1.7)
                if a <= 2:
                    continue
                NS._aacircle(s, (*color, a), (w // 2, h // 2),
                             max(1, int(radius * (1.0 - t))))

        d = radius + 2
        decal = NS._decal(d * 2, d * 2, build)
        NS._blit_decal(surface, decal, cx, cy)

    # ==================================================================
    # AIM & STATE
    # ==================================================================
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return int(x + 200 / float(getattr(boss, "_render_scale", 1.0)
                                   or 1.0)
                   * getattr(boss, "direction", 1)), int(y)

    def _detect_moving(boss):
        if not hasattr(boss, "_alch_last_x"):
            boss._alch_last_x = boss.x
            boss._alch_last_y = boss.y
            return False
        dx = abs(boss.x - boss._alch_last_x)
        dy = abs(boss.y - boss._alch_last_y)
        boss._alch_last_x = boss.x
        boss._alch_last_y = boss.y
        return dx + dy > 0.3

    def attack_phase(progress):
        """Nama fase serangan (ANTICIPATION..RECOVERY); NONE di luar."""
        if progress is None:
            return "NONE"
        p = max(0.0, min(1.0, float(progress)))
        for name, a, b in _NS_alchemist.ATTACK_PHASES:
            if a <= p < b:
                return name
        return "RECOVERY"

    def attack_phases_order():
        return tuple(n for n, _a, _b in _NS_alchemist.ATTACK_PHASES)

    def _attack_curve(ap):
        """Remap progres mentah (0..1) -> waktu pose (0..1), MONOTON.

        (a) wind-up melambat (counter-motion terbaca), (b) tebasan
        menajam menjelang impact, (c) HOLD ~2 frame di keyframe IMPACT
        0.54 (squash + bintang + shockwave ikut membeku), (d) follow-
        through lepas perlahan. Nilai kunci nyaris identik dengan input
        mentah sehingga keyframe pose tetap di timeline yang sama.
        """
        if ap <= 0.0:
            return 0.0
        if ap >= 1.0:
            return 1.0
        if ap < 0.44:
            t = ap / 0.44
            return 0.44 * (t ** 0.94)
        if ap < 0.52:
            t = (ap - 0.44) / 0.08
            return 0.44 + 0.10 * (t ** 1.30)
        if ap < 0.64:
            t = (ap - 0.52) / 0.12
            return 0.54 + 0.02 * t
        t = (ap - 0.64) / 0.36
        return 0.56 + 0.44 * (t ** 0.85)

    def _attack_pose(ap):
        """Interpolasi keyframe serang -> dict pose (ARC-BASED).

        Keyframe: (progress, lunge, lean, dip, blade_f, blade_b, flare,
                   tremble)
          0.10  anticipation : cleaver diangkat sedikit, badan mundur
          0.30  wind-up      : cleaver di belakang kepala, gemetar
          0.46  swing        : sapuan tercepat (busur melengkung)
          0.54  IMPACT       : squash + lunge + bintang + shockwave
          0.72  follow       : rebound overshoot
          1.00  recovery     : kembali ke pose istirahat
        Sudut dalam rad ruang layar (y ke bawah); blade_f menyapu
        -2.30 -> 0.72 MELALUI busur atas -> depan, bukan lerp posisi.
        blade_b (cleaver belakang) mengayun berlawanan: 2.79 -> 2.84.
        """
        keys = (
            (0.00,  0.0,  0.0,  0.0,  0.95, 2.79, 1.00, 0),
            (0.10, -2.0, -3.0,  2.0,  0.38, 2.59, 1.06, 0),
            (0.30, -5.0, -6.0,  3.0, -2.30, 2.30, 1.18, 1),
            (0.46,  5.0,  5.0, -2.0, -0.10, 2.64, 1.10, 0),
            (0.54,  9.0,  8.0,  5.0,  0.72, 2.84, 1.04, 0),
            (0.72,  3.0,  4.0,  1.0,  1.12, 2.74, 1.00, 0),
            (1.00,  0.0,  0.0,  0.0,  0.95, 2.79, 1.00, 0),
        )
        ap = max(0.0, min(1.0, ap))
        for i in range(len(keys) - 1):
            k0, k1 = keys[i], keys[i + 1]
            if k0[0] <= ap <= k1[0]:
                span = max(1e-6, k1[0] - k0[0])
                t = (ap - k0[0]) / span
                t = t * t * (3 - 2 * t)              # smoothstep
                vals = tuple(a + (b - a) * t
                             for a, b in zip(k0[1:7], k1[1:7]))
                return {
                    "lunge": vals[0], "lean": vals[1], "dip": vals[2],
                    "blade_f": vals[3], "blade_b": vals[4],
                    "flare": vals[5],
                    "tremble": 1 if (k0[7] and t < 0.9) else 0,
                    "impact": 1.0 - min(1.0, abs(ap - 0.54) / 0.10),
                }
        return {"lunge": 0.0, "lean": 0.0, "dip": 0.0, "blade_f": 0.95,
                "blade_b": 2.79, "flare": 1.0, "tremble": 0,
                "impact": 0.0}

    def _update_attack_anim(boss):
        """ANIMATION CONTROLLER ALCHEMIST — state, fase, timing, dt.

        Satu-satunya sumber kebenaran state karakter. Nama field lama
        tetap diisi supaya tooling lama tidak berubah:

        * ``_alch_attack_active``    serangan sedang berjalan (lama)
        * ``_alch_attack_frame``     frame ke-n dalam serangan (lama)
        * ``_alch_attack_progress``  0..1 mentah sepanjang serangan
        * ``_alch_attack_phase``     ANTICIPATION/.../RECOVERY / NONE
        * ``_alch_ap``               progress setelah _attack_curve
        * ``_alch_hit_active``       True hanya di jendela hit aktif
        * ``_alch_dt``               delta-time nyata (detik, dijepit)
        * ``_alch_state`` / ``_alch_state_prev`` / ``_alch_state_time``
        * ``_alch_moving``           hasil _detect_moving terakhir
        """
        NS = _NS_alchemist
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_alch_prev_timer", 0))
        active = bool(getattr(boss, "_alch_attack_active", False))

        # ── delta time nyata dari bus game-feel ─────────────────────
        try:
            from heroes import combat_feel as _cf
            dt = float(_cf.frame_dt())
        except Exception:
            dt = 1.0 / 60.0
        if not (0.0 < dt <= 0.05):
            dt = 1.0 / 60.0
        boss._alch_dt = dt

        if timer >= cooldown - 1 and previous <= 1:
            boss._alch_attack_active = True
            boss._alch_attack_frame = 0
            active = True
        elif active:
            boss._alch_attack_frame = int(
                getattr(boss, "_alch_attack_frame", 0)) + 1
            if boss._alch_attack_frame > cooldown:
                boss._alch_attack_active = False
                boss._alch_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._alch_attack_active = False
            boss._alch_attack_frame = 0
            active = False

        boss._alch_prev_timer = timer
        raw = (min(1.0, getattr(boss, "_alch_attack_frame", 0)
                   / max(1, cooldown - 1)) if active else 0.0)
        boss._alch_attack_progress = raw
        boss._alch_attack_phase = (NS.attack_phase(raw)
                                   if active else "NONE")
        boss._alch_ap = NS._attack_curve(raw)
        boss._alch_hit_active = bool(
            active and 0.30 <= raw <= 0.62)

        # ── state machine (prioritas; DEATH mengunci) ───────────────
        want = NS._resolve_want_state(boss, active)
        if not hasattr(boss, "_alch_state"):
            boss._alch_state = want
            boss._alch_state_prev = want
            boss._alch_state_time = 0.0
        prev = str(getattr(boss, "_alch_state", want))
        if want != prev:
            cur_p = NS.ANIM_PRIORITY.get(prev, 0)
            new_p = NS.ANIM_PRIORITY.get(want, 0)
            if prev != "DEATH" and (new_p >= cur_p
                                    or float(getattr(boss,
                                                     "_alch_state_time",
                                                     0.0)) > 0.05):
                boss._alch_state_prev = prev
                boss._alch_state = want
                boss._alch_state_time = 0.0
        boss._alch_state_time = (float(getattr(boss, "_alch_state_time",
                                               0.0)) + dt)

    def _resolve_want_state(boss, active):
        """State yang DIINGINKAN frame ini (tanpa efek samping)."""
        if not getattr(boss, "alive", True):
            return "DEATH"
        if int(getattr(boss, "hurt_flash_timer", 0) or 0) > 0:
            return "HURT"
        skill = getattr(boss, "active_skill", None)
        if skill == "r":
            return "SPECIAL"
        if skill in ("q", "w", "e"):
            return "CAST" if skill != "e" else "SKILL"
        if active:
            ph = _NS_alchemist.attack_phase(
                getattr(boss, "_alch_attack_progress", 0.0))
            if ph in ("ANTICIPATION", "WINDUP"):
                return "CHARGE"
            if ph in ("SWING", "IMPACT"):
                return "SWING"
            return "ATTACK"
        if bool(getattr(boss, "_alch_moving", False)):
            return "RUN" if float(getattr(boss, "speed", 1.0) or
                                  1.0) >= 1.1 else "WALK"
        return "IDLE"

    def _resolve_pose(boss, moving=False):
        """(action, phase, ap) — pose yang SEDANG digambar badan.

        Murni/tanpa efek samping: dipanggil renderer DAN lapisan hidup
        supaya trail, proyektil, dan badan tidak mungkin berbeda frame.
        ``ap`` = waktu pose (sudah lewat _attack_curve).
        """
        active_skill = getattr(boss, "active_skill", None)
        attacking = (
            getattr(boss, "_alch_attack_active", False)
            or getattr(boss, "timer", 0) >
            getattr(boss, "attack_cooldown", 50) - 15
        )
        if attacking:
            action = "attack"
        elif active_skill == "q":
            action = "q_cast"
        elif active_skill == "w":
            action = "w_cast"
        elif active_skill == "e":
            action = "e_cast"
        elif active_skill == "r":
            action = "r_cast"
        elif moving:
            action = "walk"
        else:
            action = "idle"

        phase = float(getattr(boss, "pulse", 0.0))
        if action == "walk":
            phase *= 2.4
        ap = 0.0
        if action == "attack":
            raw = max(0.0, min(1.0, float(
                getattr(boss, "_alch_attack_progress", 0.0))))
            ap = _NS_alchemist._attack_curve(raw)
        return action, phase, ap

    # ── pemetaan ruang lokal rig -> layar (FX hidup memakai ini) ────
    def _rig_shift(action, phase, ap):
        """(lean, root_y) gerak badan (belum dikali facing)."""
        if action == "attack":
            pose = _NS_alchemist._attack_pose(ap)
            sway = 1 if (pose["tremble"]
                         and int(phase * 30) % 2) else 0
            return int(pose["lean"]) + sway, int(pose["dip"])
        if action == "walk":
            return int(math.sin(phase) * 3.0) + 3, \
                int(math.sin(phase * 2.0) * 2.5) - 2
        if action in ("q_cast", "w_cast"):
            return -3, int(math.sin(phase * 0.8) * 1.5)
        if action == "e_cast":
            return 2, int(-4.0 * math.sin(min(1.0, phase * 0.02) *
                                           math.pi))
        if action == "r_cast":
            return -4, int(math.sin(phase * 1.4) * 2.0) - 2
        breath = math.sin(phase * 0.7)
        return int(math.sin(phase * 0.5 + 1.2) * 1.5), int(breath * 2.2)

    def _local_to_screen(cx, cy, facing, lean, root_y, lx, ly):
        """SATU pemetaan lokal -> layar (SCALE, facing, bob/lean)."""
        f = 1 if facing >= 0 else -1
        k = _NS_alchemist.SCALE
        return (int(cx + (lx * f + lean * f) * k),
                int(cy + (ly + root_y) * k))

    def _local(boss, x, y, action, phase, ap, lx, ly):
        """Ruang lokal rig -> piksel surface (dipakai FX eksternal)."""
        facing = getattr(boss, "direction", 1) or 1
        lean, root_y = _NS_alchemist._rig_shift(action, phase, ap)
        return _NS_alchemist._local_to_screen(x, y, facing, lean,
                                              root_y, lx, ly)

    def _cleaver_grip_local(action, phase, ap=0.0, back=False):
        """Pergelangan tangan (grip cleaver) ruang lokal."""
        if action == "attack":
            pose = _NS_alchemist._attack_pose(ap)
            ang = pose["blade_b"] if back else pose["blade_f"]
            reach = 20 + 10 * math.sin(min(1.0, ap * 1.6) * math.pi)
            sx = -16 if back else 16
            return (int(sx + math.cos(ang) * reach),
                    int(-30 + math.sin(ang) * reach + 8))
        if action == "walk":
            swing = math.sin(phase + (math.pi if back else 0.0)) * 7
            return (int((-16 if back else 17) + swing), 2)
        if action == "q_cast":
            return (18, 6) if not back else (-22, 6)
        if action == "w_cast":
            return (14, -18) if not back else (-14, -18)
        if action == "e_cast":
            return (26, -4) if not back else (-26, -4)
        if action == "r_cast":
            return (16, -28) if not back else (-16, -28)
        bob = math.sin(phase * 0.7 + (0.9 if back else 0.4)) * 1.8
        return (-25 if back else 24, int(4 + bob))

    def _cleaver_angle_local(action, phase, ap=0.0, back=False):
        """Sudut cleaver (rad) ruang lokal — ARC tunggal, bukan snap."""
        if action == "attack":
            pose = _NS_alchemist._attack_pose(ap)
            return pose["blade_b"] if back else pose["blade_f"]
        if action == "walk":
            return (2.79 if back else 0.95) + \
                math.sin(phase + (math.pi if back else 0.0)) * 0.10
        if action == "q_cast":
            return (2.30 if back else 1.05)
        if action == "w_cast":
            return (-1.90 if back else -1.20) + \
                math.sin(phase * 2.0) * 0.05
        if action == "e_cast":
            return (1.95 if back else 1.35) + \
                math.sin(phase * 3.0) * 0.06
        if action == "r_cast":
            return (-1.95 if back else -1.60) + \
                math.sin(phase * 1.2) * 0.08
        return (2.79 if back else 0.95) + \
            math.sin(phase * 0.8 + (0.7 if back else 0.0)) * 0.05

    def _tip_local(action, phase, ap=0.0, back=False):
        """Ujung bilah ruang lokal (rig & FX pakai angka sama)."""
        grip = _NS_alchemist._cleaver_grip_local(action, phase, ap,
                                                 back)
        ang = _NS_alchemist._cleaver_angle_local(action, phase, ap,
                                                 back)
        L = _NS_alchemist.CLEAVER_BLADE + _NS_alchemist.CLEAVER_HANDLE
        return (int(grip[0] + math.cos(ang) * L),
                int(grip[1] + math.sin(ang) * L))

    def _grip_screen(boss, x, y, back=False):
        action, phase, ap = _NS_alchemist._resolve_pose(
            boss, bool(getattr(boss, "_alch_moving", False)))
        lx, ly = _NS_alchemist._cleaver_grip_local(action, phase, ap,
                                                   back)
        return _NS_alchemist._local(boss, x, y, action, phase, ap,
                                    lx, ly)

    def _tip_screen(boss, x, y, back=False):
        action, phase, ap = _NS_alchemist._resolve_pose(
            boss, bool(getattr(boss, "_alch_moving", False)))
        lx, ly = _NS_alchemist._tip_local(action, phase, ap, back)
        return _NS_alchemist._local(boss, x, y, action, phase, ap,
                                    lx, ly)

    def _gun_end_screen(boss, x, y):
        """Moncong acid gun goblin dalam piksel layar (kembaran
        matematis dari rig supaya muzzle FX lahir PERSIS di laras)."""
        action, phase, ap = _NS_alchemist._resolve_pose(
            boss, bool(getattr(boss, "_alch_moving", False)))
        facing = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        g = _NS_alchemist._local(boss, x, y, action, phase, ap,
                                 -13, -44)
        if action == "q_cast":
            hx, hy = g[0] + facing * 8, g[1] - 6
            tx, ty = _NS_alchemist._target_position(boss, x, y)
            ang = math.atan2(ty - hy, tx - hx)
        else:
            hx, hy = g[0] + facing * 8, g[1] - 8
            ang = -0.55 + math.sin(phase * 0.9) * 0.08
        return (int(hx + math.cos(ang) * 13),
                int(hy + math.sin(ang) * 13))

    def _bottle_hand_screen(boss, x, y):
        """Tangan botol goblin (pose W) dalam piksel layar."""
        action, phase, ap = _NS_alchemist._resolve_pose(
            boss, bool(getattr(boss, "_alch_moving", False)))
        lx, ly = -11, -74
        if action == "w_cast":
            lx, ly = -11, -74
        return _NS_alchemist._local(boss, x, y, action, phase, ap,
                                    lx, ly)

    def _swing_hitbox(boss, x, y):
        """Rect AABB jendela hit aktif (SWING..IMPACT) untuk debug."""
        action, phase, ap = _NS_alchemist._resolve_pose(
            boss, bool(getattr(boss, "_alch_moving", False)))
        if action != "attack" or not (0.30 <= ap <= 0.78):
            return None
        gx, gy = _NS_alchemist._grip_screen(boss, x, y)
        tx, ty = _NS_alchemist._tip_screen(boss, x, y)
        pad = 10
        left = min(gx, tx) - pad
        right = max(gx, tx) + pad
        top = min(gy, ty) - pad
        bottom = max(gy, ty) + pad
        return pygame.Rect(int(left), int(top), int(right - left),
                           int(bottom - top))

    # ==================================================================
    # PROJECTILE CANVAS (fallback bila lapisan hidup tidak aktif)
    # Lifecycle: SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT FX -> DESTROY
    # ==================================================================
    class AcidBottle:
        """Botol asam melempar busur (canvas fallback).

        Hidup di layar boss 1:1; pada jalur hero lapisan hidup
        (heroes/alchemist_fx) yang melempar supaya tetap 60 fps —
        renderer hanya memicu timing lewat ``_alch_wcast_spawned``.
        """
        __slots__ = ("start_x", "start_y", "tx", "ty", "arc_height",
                     "alive", "age", "max_age", "x", "y", "spin",
                     "trail", "_landed")

        def __init__(self, sx, sy, tx, ty, arc_height=50):
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
            self._landed = False

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.spin += 0.38
            t = self.age / self.max_age
            if t >= 1.0:
                self.alive = False
                self.x, self.y = self.tx, self.ty
                return
            self.x = self.start_x + (self.tx - self.start_x) * t
            arc = -4 * self.arc_height * t * (1 - t)
            self.y = self.start_y + (self.ty - self.start_y) * t + arc
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 9:
                self.trail.pop(0)

        def draw(self, surface, phase):
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(70 + i * 15)
                _NS_alchemist._draw_acid_droplet(
                    surface, tx, ty, max(1, 3 - (len(self.trail) - i)),
                    alpha)
            if self.alive:
                _NS_alchemist._draw_bottle_spinning(
                    surface, int(self.x), int(self.y), self.spin)

    class AcidPatch:
        """Genangan asam persisten (canvas fallback)."""
        __slots__ = ("x", "y", "radius", "age", "life", "alive")

        def __init__(self, x, y, radius=30, life=90):
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
            NS = _NS_alchemist
            t = self.age / self.life
            if t < 0.1:
                r = int(self.radius * (t / 0.1))
                alpha = int(255 * (t / 0.1))
            elif t < 0.7:
                r = self.radius
                alpha = 255
            else:
                r = self.radius
                alpha = int(255 * (1 - (t - 0.7) / 0.3))
            if r <= 0 or alpha <= 0:
                return
            P = NS.PALETTE
            NS._ellipse(surface, (*P["acid_darkest"], int(alpha * 0.9)),
                        (self.x - r, self.y - r // 3, r * 2, r // 1.5))
            NS._ellipse(surface, (*P["acid_dark"], int(alpha * 0.85)),
                        (self.x - r + 3, self.y - r // 3 + 2,
                         r * 2 - 6, r // 1.5 - 4))
            NS._ellipse(surface, (*P["acid_mid"], int(alpha * 0.7)),
                        (self.x - r + 6, self.y - r // 3 + 4,
                         r * 2 - 12, r // 1.5 - 8))
            NS._ellipse(surface, (*P["acid_bright"], int(alpha * 0.5)),
                        (self.x - r + 10, self.y - r // 4 + 2,
                         r * 2 - 20, r // 3))
            for i in range(6):
                angle = phase * 0.5 + i * math.pi / 3
                bx = self.x + int(math.cos(angle) * (r - 5))
                by = self.y + int(math.sin(angle) * (r // 3 - 2))
                NS._aacircle(surface, (*P["acid_bright"], alpha),
                             (bx, by), 2)
                NS._aacircle(surface, (*P["acid_glow"], alpha),
                             (bx, by - 1), 1)
            for i in range(3):
                wt = (phase * 0.6 + i * 0.33) % 1.0
                wx = self.x - r // 2 + i * (r // 3) + \
                    int(math.sin(phase + i) * 3)
                wy = self.y - int(wt * 20)
                wa = int(alpha * (1 - wt) * 0.6)
                NS._aacircle(surface, (*P["acid_mid"], wa), (wx, wy), 3)
                NS._aacircle(surface, (*P["acid_bright"], wa),
                             (wx, wy), 2)

    def _draw_bottle_spinning(surface, cx, cy, spin):
        """Botol ramuan berputar di udara (core + glow + sumbu bara)."""
        NS = _NS_alchemist
        P = NS.PALETTE
        dx = math.cos(spin)
        dy = math.sin(spin)
        perp_x, perp_y = -dy, dx
        body_h, body_w = 8, 5
        p1 = (cx + int(dx * body_h + perp_x * body_w),
              cy + int(dy * body_h + perp_y * body_w))
        p2 = (cx + int(dx * body_h - perp_x * body_w),
              cy + int(dy * body_h - perp_y * body_w))
        p3 = (cx + int(-dx * body_h - perp_x * body_w),
              cy + int(-dy * body_h - perp_y * body_w))
        p4 = (cx + int(-dx * body_h + perp_x * body_w),
              cy + int(-dy * body_h + perp_y * body_w))
        NS._poly(surface, P["shadow_deep"],
                 [(p[0] + 1, p[1] + 1) for p in (p1, p2, p3, p4)])
        NS._poly(surface, P["glass_dark"], [p1, p2, p3, p4])
        NS._poly(surface, P["glass_mid"], [
            (cx + int(dx * (body_h - 1) + perp_x * (body_w - 1)),
             cy + int(dy * (body_h - 1) + perp_y * (body_w - 1))),
            (cx + int(dx * (body_h - 1) - perp_x * (body_w - 1)),
             cy + int(dy * (body_h - 1) - perp_y * (body_w - 1))),
            (cx + int(-dx * (body_h - 1) - perp_x * (body_w - 2)),
             cy + int(-dy * (body_h - 1) - perp_y * (body_w - 2))),
            (cx + int(-dx * (body_h - 1) + perp_x * (body_w - 2)),
             cy + int(-dy * (body_h - 1) + perp_y * (body_w - 2))),
        ])
        cork_x = cx + int(dx * (body_h + 3))
        cork_y = cy + int(dy * (body_h + 3))
        NS._aacircle(surface, P["leather_dark"], (cork_x, cork_y), 3)
        NS._aacircle(surface, P["leather_mid"], (cork_x, cork_y), 2)
        NS._aacircle(surface, P["acid_bright"], (cx, cy), 3)
        NS._aacircle(surface, P["acid_hot"], (cx, cy), 2)
        NS._aacircle(surface, P["acid_glow"], (cx, cy), 1)
        NS._aacircle(surface, (*P["acid_bright"], 120), (cx, cy), 10)

    # ── manajemen proyektil + koin canvas ───────────────────────────
    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_alch_projectiles"):
            boss._alch_projectiles = []
        if not hasattr(boss, "_alch_patches"):
            boss._alch_patches = []
        if not hasattr(boss, "_alch_coins"):
            boss._alch_coins = []

        for proj in boss._alch_projectiles:
            proj.update()
            if not proj.alive and proj.age > 0:
                boss._alch_patches.append(
                    _NS_alchemist.AcidPatch(int(proj.tx), int(proj.ty),
                                            radius=32, life=100))
                proj.age = -1
            if proj.age >= 0:
                proj.draw(surface, phase)
        boss._alch_projectiles = [p for p in boss._alch_projectiles
                                  if p.alive]

        for patch in boss._alch_patches:
            patch.update()
        boss._alch_patches = [p for p in boss._alch_patches if p.alive]

    def _spawn_acid_bottle(boss, sx, sy, tx, ty):
        """Lempar botol asam (canvas fallback).

        Jalur lapisan hidup mengambil alih kalau aktif: renderer hanya
        menyalakan ``_alch_live_proj_window``, lapisan hidup yang
        melempar di koordinat layar 1:1.
        """
        NS = _NS_alchemist
        if NS._fx_owned(boss):
            boss._alch_live_proj_window = True
            return
        if not hasattr(boss, "_alch_projectiles"):
            boss._alch_projectiles = []
        boss._alch_projectiles.append(
            NS.AcidBottle(sx, sy, tx, ty))

    def _spawn_coin(boss, x, y):
        if not hasattr(boss, "_alch_coins"):
            boss._alch_coins = []
        boss._alch_coins.append({
            "x": x, "y": y - 5,
            "vx": (hash((x, y, len(boss._alch_coins))) % 40 - 20) / 10.0,
            "vy": -3 - (hash((x, y, "vy")) % 20) / 10.0,
            "life": 60,
            "age": 0,
            "spin": 0.0,
            "spin_speed": 0.3 + (hash((x, y, "s")) % 30) / 100.0,
        })

    # ==================================================================
    # ACID PARTICLE HELPERS (stamp kecil, dipakai canvas & fallback)
    # ==================================================================
    def _draw_acid_splash(surface, cx, cy, size=8, phase=0, alpha=255):
        """Cipratan asam berbusa (ramp 6 band + gelembung)."""
        NS = _NS_alchemist
        P = NS.PALETTE
        NS._aacircle(surface, (*P["acid_darkest"], alpha), (cx, cy), size)
        NS._aacircle(surface, (*P["acid_dark"], alpha), (cx, cy),
                     max(1, size - 1))
        NS._aacircle(surface, (*P["acid_mid"], alpha), (cx, cy),
                     max(1, size - 3))
        NS._aacircle(surface, (*P["acid_bright"], alpha),
                     (cx - 1, cy - 1), max(1, size - 4))
        NS._aacircle(surface, (*P["acid_hot"], alpha),
                     (cx - 1, cy - 2), max(1, size - 6))
        NS._aacircle(surface, (*P["acid_glow"], min(255, alpha)),
                     (cx - 1, cy - 2), max(1, size - 7))
        for i in range(4):
            angle = phase * 0.5 + i * math.pi / 2
            bx = cx + int(math.cos(angle) * (size - 2))
            by = cy + int(math.sin(angle) * (size - 2))
            NS._aacircle(surface, (*P["acid_bright"], alpha),
                         (bx, by), 1)

    def _draw_acid_droplet(surface, x, y, size=3, alpha=255):
        """Tetes asam (bentuk tear + glow)."""
        NS = _NS_alchemist
        P = NS.PALETTE
        NS._poly(surface, (*P["acid_darkest"], alpha), [
            (x, y - size),
            (x - size, y + size),
            (x + size, y + size),
        ])
        NS._aacircle(surface, (*P["acid_dark"], alpha),
                     (x, y + size // 2), size)
        NS._aacircle(surface, (*P["acid_bright"], alpha),
                     (x, y + size // 2), max(1, size - 1))
        NS._aacircle(surface, (*P["acid_glow"], alpha),
                     (x - 1, y + size // 2 - 1), max(1, size - 2))

    # ==================================================================
    # SHADOW / AURA / GROUND FX  (cached — tanpa Surface baru/frame)
    # ==================================================================
    def _draw_shadow(surface, x, y, lift=0):
        """Bayangan kontak reaktif (menyusut saat terangkat, dasar
        menapak). Rect-nya dicatat ke _record_shadow supaya hurt flash
        TIDAK ikut menerangi tanah."""
        NS = _NS_alchemist
        if NS._shadow_cache is None:
            shadow = pygame.Surface((120, 22), pygame.SRCALPHA)
            for radius in range(11, 0, -1):
                alpha = max(0, (11 - radius) * 15)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (11 - radius, 11 - radius, 98 + radius * 2,
                     radius * 2))
            pygame.draw.ellipse(shadow,
                                (*NS.PALETTE["acid_dark"], 60),
                                (10, 5, 100, 12))
            NS._shadow_cache = shadow
        spr = NS._shadow_cache
        w, h = spr.get_width(), spr.get_height()
        if lift:
            k = max(0.12, 1.0 - lift * 0.05)
            w = max(6, int(w * k))
            h = max(2, int(h * k))
            spr = pygame.transform.scale(spr, (w, h))
        bx = x - w // 2
        by = (y + 11) - h
        surface.blit(spr, (bx, by))
        if NS._record_shadow is not None:
            NS._record_shadow.append(pygame.Rect(bx, by, w, h))

    def _draw_alch_aura(surface, x, y, phase, active_skill):
        """Aura latar (acid/gold) — stamp ter-cache, alpha lewat
        set_alpha pada stamp bersama (tanpa .copy() per frame)."""
        NS = _NS_alchemist
        P = NS.PALETTE
        key = "gold" if active_skill in ("r",) else "acid"
        if key not in NS._aura_cache:
            aura = pygame.Surface((220, 190), pygame.SRCALPHA)
            color = (P["acid_darkest"] if key == "acid"
                     else P["gold_darkest"])
            for radius in range(88, 5, -4):
                alpha = int((88 - radius) * 1.2)
                if alpha > 0:
                    pygame.draw.circle(
                        aura, (*color, min(255, alpha)), (110, 95),
                        radius)
            NS._aura_cache[key] = aura
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.6 if active_skill in ("e", "r") else 1.0
        a = int(255 * min(1.0, pulse * strength))
        spr = NS._aura_cache[key]
        spr.set_alpha(a)
        surface.blit(spr, (x - 110, y - 95))

    def _draw_ground_runes(surface, x, y, phase, active_skill):
        """Rune alkemi di tanah: cincin dasar ter-cache + jari-jari
        berputar + denyut skill (murah, tanpa alokasi per frame)."""
        NS = _NS_alchemist
        P = NS.PALETTE
        key = "rune_gold" if active_skill == "r" else "rune_acid"
        if key not in NS._STATIC_SURFACES:
            ring = pygame.Surface((140, 46), pygame.SRCALPHA)
            c1 = (*P["gold_dark"], 150) if active_skill == "r" else \
                (*P["acid_dark"], 140)
            c2 = (*P["gold_mid"], 170) if active_skill == "r" else \
                (*P["acid_mid"], 170)
            pygame.draw.ellipse(ring, c1, (5, 10, 130, 26), 3)
            pygame.draw.ellipse(ring, c2, (20, 14, 100, 18), 2)
            # simbol alkemi (segitiga + lingkaran kecil)
            sx = (*P["gold_light"], 190) if active_skill == "r" else \
                (*P["acid_bright"], 170)
            pygame.draw.polygon(ring, sx, [(70, 16), (62, 30),
                                           (78, 30)], 1)
            pygame.draw.circle(ring, sx, (70, 24), 4, 1)
            NS._STATIC_SURFACES[key] = ring
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = NS._STATIC_SURFACES[key]
        ring.set_alpha(int(150 + 90 * pulse))
        surface.blit(ring, (x - 70, y - 23))
        c3 = P["gold_light"] if active_skill == "r" else \
            P["acid_bright"]
        for i in range(10):
            angle = phase * 0.15 + i * math.pi / 5
            x1 = x + int(math.cos(angle) * 32)
            y1 = y + int(math.sin(angle) * 7)
            x2 = x + int(math.cos(angle) * 60)
            y2 = y + int(math.sin(angle) * 11)
            NS._aaline(surface, (*c3, int(150 * pulse)),
                       (x1, y1), (x2, y2), 1)

    def _draw_alch_wisps(surface, cx, cy, phase, trail=False, facing=1,
                         intense=False):
        """Uap asap naik + gelembung mengorbit (mist ter-cache)."""
        NS = _NS_alchemist
        P = NS.PALETTE
        strength = 1.5 if intense else 1.0
        mist_key = "wisps_mist"
        if mist_key not in NS._STATIC_SURFACES:
            mist = pygame.Surface((150, 44), pygame.SRCALPHA)
            for radius in range(38, 3, -4):
                alpha = int((38 - radius) * 2.2)
                if alpha > 0:
                    pygame.draw.ellipse(
                        mist, (*P["acid_darkest"],
                               min(255, alpha)),
                        (75 - radius * 2, 22 - radius // 3,
                         radius * 4, max(3, radius // 2)))
            NS._STATIC_SURFACES[mist_key] = mist
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        mist = NS._STATIC_SURFACES[mist_key]
        mist.set_alpha(int(255 * min(1.0, pulse * strength)))
        surface.blit(mist, (cx - 75, cy - 11))

        for i, offset in enumerate((-25, -10, 8, 24)):
            t = (phase * 0.55 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 26)
            alpha = max(0, min(255, int(210 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            NS._aacircle(surface, (*P["acid_darkest"], alpha),
                         (sx, sy), 5)
            NS._aacircle(surface, (*P["acid_mid"], alpha), (sx, sy - 2),
                         3)
            NS._aacircle(surface, (*P["acid_bright"], alpha),
                         (sx, sy - 3), 2)
            NS._aacircle(surface, (*P["acid_hot"], alpha),
                         (sx, sy - 3), 1)
        for i in range(7):
            angle = phase * 0.7 + i * math.pi * 2 / 7
            r = 25 + int(math.sin(phase + i * 1.3) * 6)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 9)
            NS._aacircle(surface, P["acid_mid"], (sx, sy), 2)
            NS._aacircle(surface, P["acid_bright"], (sx, sy), 1)
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 13 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = max(0, 140 - i * 25)
                NS._aacircle(surface, (*P["acid_dark"], alpha),
                             (sx, sy), max(2, 6 - i))
                NS._aacircle(surface, (*P["acid_bright"], alpha),
                             (sx, sy), max(1, 3 - i))

    def _draw_shockwave(surface, x, y, age, total, c1, c2, fs=1.0):
        """Gelombang kejut aktivasi skill (12 frame pertama)."""
        NS = _NS_alchemist
        t = age / float(total)
        ease = 1 - (1 - t) ** 2
        r = int((16 + ease * 66) * fs)
        a = max(0, min(255, int(235 * (1 - t))))
        if r <= 0 or a <= 0:
            return
        NS._ellipse(surface, (*c1, a),
                    (x - r, y - r // 3, r * 2, r * 2 // 3), 2)
        NS._ellipse(surface, (*c2, a),
                    (x - r // 2, y - r // 6, r, r // 3), 1)
        ri = max(3, r // 2)
        NS._aacircle(surface, (*c1, int(a * 0.8)),
                     (x, y - (r // 6)), ri)

    # ==================================================================
    # RIG PIXEL-ART v2 — ogre chemist + goblin rider (ruang lokal).
    # Konvensi: (0,0) = jangkar pinggul; +x maju (dikali facing); y ke
    # bawah. Semua bentuk poligon/ellipse keras + ramp 4-6 band.
    # ==================================================================
    def _draw_cleaver(surface, gx, gy, ang, f, phase=0.0, glow=0.0):
        """Cleaver jagal berputar mengikuti SUDUT (arc-based).

        gx,gy = layar; ang = sudut layar (0 maju, pi/2 bawah).
        Bilah = poligon dari basis ke ujung memakai cos/sin — tidak
        pernah ada lerp posisi awal->akhir.
        """
        NS = _NS_alchemist
        P = NS.PALETTE
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        H = NS.CLEAVER_HANDLE
        B = NS.CLEAVER_BLADE

        def pt(dist, side):
            return (int(gx + ca * dist + px * side),
                    int(gy + sa * dist + py * side))

        h0, h1 = pt(0, 0), pt(H, 0)                      # gagang
        NS._poly(surface, P["leather_darkest"], [
            pt(0, -2), pt(H, -2), pt(H, 2), pt(0, 2)])
        NS._poly(surface, P["leather_mid"], [
            pt(0, -1), pt(H - 1, -1), pt(H - 1, 1), pt(0, 1)])
        b0s, b0e = pt(H, -3), pt(H, 4)                   # basis bilah
        b1s, b1e = pt(H + B, -2), pt(H + B, 6)           # ujung bilah
        # selout sisi bayangan
        NS._poly(surface, P["shadow_deep"],
                 [(b0s[0] + 1, b0s[1] + 1), (b0e[0] + 1, b0e[1] + 1),
                  (b1e[0] + 1, b1e[1] + 1), (b1s[0] + 1, b1s[1] + 1)])
        # badan bilah
        NS._poly(surface, P["metal_darkest"],
                 [b0s, b0e, b1e, b1s])
        NS._poly(surface, P["metal_dark"],
                 [pt(H + 1, -2), pt(H + 1, 4), pt(H + B - 1, 5),
                  pt(H + B - 1, -1)])
        NS._poly(surface, P["metal_mid"],
                 [pt(H + 2, -2), pt(H + 2, 2), pt(H + B - 2, 3),
                  pt(H + B - 2, -1)])
        # band specular sepanjang tulang (3 cluster, bukan garis penuh)
        for t in (0.25, 0.55, 0.85):
            d = H + 2 + int(t * (B - 5))
            NS._poly(surface, P["metal_light"],
                     [pt(d, -2), pt(d + 2, -2), pt(d + 2, 0),
                      pt(d, 0)])
        # mata tebang (edge) + etching asam
        NS._aaline(surface, P["metal_edge"], pt(H + 1, 4),
                   pt(H + B, 6), 1)
        NS._aaline(surface, P["acid_dark"], pt(H + 6, 1),
                   pt(H + B - 4, 3), 1)
        NS._aacircle(surface, P["brass_mid"], (h0[0], h0[1]), 2)
        NS._aacircle(surface, P["brass_light"],
                     (h0[0] - f, h0[1] - 1), 1)
        # glint periodik di ujung bilah
        if math.sin(phase * 2.6 + ang) > 0.90:
            tip = pt(H + B - 2, 4)
            NS._aacircle(surface, P["metal_edge"],
                         (tip[0], tip[1]), 1)
            NS._aacircle(surface, P["white"],
                         (tip[0] - f, tip[1] - 1), 1)
        if glow > 0.02:
            g = int(150 * min(1.0, glow))
            NS._aacircle(surface, (*P["acid_bright"], g),
                         (h1[0], h1[1]), 5)
            NS._aacircle(surface, (*P["acid_hot"], g),
                         (h1[0], h1[1]), 3)

    def _draw_ogre_arm(surface, sx, sy, gx, gy, f, back=False,
                       flex=0.0):
        """Lengan ogre chunky: bahu -> siku (droop) -> pergelangan."""
        NS = _NS_alchemist
        P = NS.PALETTE
        mx, my = (sx + gx) / 2.0, (sy + gy) / 2.0 + 6 - flex * 4
        c_dark = P["ogre_dark"] if back else P["ogre_mid"]
        c_mid = P["ogre_mid"] if back else P["ogre_light"]
        c_hi = P["ogre_light"] if back else P["ogre_high"]
        # selout
        NS._poly(surface, P["shadow_deep"], [
            (sx + 1, sy + 2), (mx + 1, my + 3), (gx + 1, gy + 2),
            (gx - 2, gy + 1), (mx - 3, my + 1), (sx - 3, sy)])
        # lengan atas + bawah sebagai poligon tebal 2 band
        NS._poly(surface, c_dark, [
            (sx - 4, sy - 2), (mx - 4, my), (gx - 3, gy - 1),
            (gx + 3, gy + 2), (mx + 4, my + 3), (sx + 4, sy + 3)])
        NS._poly(surface, c_mid, [
            (sx - 3, sy - 2), (mx - 3, my - 1), (gx - 2, gy - 1),
            (gx + 2, gy + 1), (mx + 3, my + 2), (sx + 3, sy + 2)])
        # highlight atas
        NS._aaline(surface, c_hi, (sx - 2, sy - 2), (mx - 2, my - 2), 1)
        NS._aaline(surface, c_hi, (mx - 2, my - 2), (gx - 1, gy - 1), 1)
        # bahu berotot + pergelangan
        NS._aacircle(surface, c_dark, (sx, sy), 7 if not back else 6)
        NS._aacircle(surface, c_mid, (sx - f, sy - 1), 5 if not back
                     else 4)
        NS._aacircle(surface, c_hi, (sx - f * 2, sy - 2), 2)
        NS._aacircle(surface, P["ogre_dark"], (gx, gy), 5)
        NS._aacircle(surface, c_mid, (gx - f, gy - 1), 4)
        NS._aacircle(surface, c_hi, (gx - f * 2, gy - 2), 1)
        # sarung tangan kulit
        NS._aacircle(surface, P["leather_dark"],
                     (gx + f, gy + 2), 3)
        NS._aacircle(surface, P["leather_mid"],
                     (gx + f, gy + 1), 2)

    def _draw_ogre_leg(surface, hipx, hipy, ang, lift, front, f):
        """Satu kaki ogre: paha -> lutut -> kaki (foot plant timing)."""
        NS = _NS_alchemist
        P = NS.PALETTE
        ca, sa = math.cos(ang), math.sin(ang)
        kx = hipx + ca * 15
        ky = hipy + sa * 20
        ax = kx + ca * 12
        ay = ky + 16 - lift
        c_base = P["ogre_mid"] if front else P["ogre_dark"]
        c_hi = P["ogre_light"] if front else P["ogre_mid"]
        # selout
        NS._poly(surface, P["shadow_deep"], [
            (hipx + 2, hipy + 3), (kx + 2, ky + 3), (ax + 2, ay + 2),
            (ax - 2, ay + 1), (kx - 3, ky), (hipx - 3, hipy)])
        # paha + betis
        NS._poly(surface, P["ogre_dark"], [
            (hipx - 6, hipy - 2), (kx - 5, ky), (ax - 4, ay - 1),
            (ax + 4, ay + 1), (kx + 5, ky + 3), (hipx + 6, hipy + 3)])
        NS._poly(surface, c_base, [
            (hipx - 5, hipy - 2), (kx - 4, ky - 1), (ax - 3, ay - 1),
            (ax + 3, ay), (kx + 4, ky + 2), (hipx + 5, hipy + 2)])
        NS._aaline(surface, c_hi, (hipx - 3, hipy), (kx - 3, ky), 2)
        NS._aacircle(surface, c_base, (kx, ky), 5)
        # kaki (sepatu kulit besar) menapak tanah
        fy = ay + 2
        NS._ellipse(surface, P["leather_darkest"],
                    (ax - 7, fy - 3, 14 + (4 if front else 2), 7))
        NS._ellipse(surface, P["leather_dark"],
                    (ax - 6, fy - 3, 12 + (4 if front else 2), 5))
        NS._ellipse(surface, P["leather_mid"],
                    (ax - 5, fy - 2, 8, 2))
        # jahitan boot
        NS._aaline(surface, P["leather_high"],
                   (ax - 3, fy + 2), (ax + 4, fy + 2), 1)

    def _draw_ogre_torso(surface, ox, oy, phase, flare, rage, f):
        """Torso massive: perut barel + dada + pektoral + collar."""
        NS = _NS_alchemist
        P = NS.PALETTE
        fl = max(0.9, min(1.3, flare))
        bw = int(23 * fl)
        bh = int(26 / fl)
        # selout seluruh massa
        NS._ellipse(surface, P["shadow_deep"],
                    (ox - bw - 2, oy - bh - 2 + 14,
                     bw * 2 + 4, bh * 2 + 4))
        # perut (barel) — ramp 4 band dengan dither band tengah
        NS._ellipse(surface, P["ogre_darkest"],
                    (ox - bw, oy - bh + 14, bw * 2, bh * 2))
        NS._ellipse(surface, P["ogre_dark"],
                    (ox - bw + 2, oy - bh + 16, bw * 2 - 4, bh * 2 - 4))
        NS._ellipse(surface, P["ogre_mid"],
                    (ox - bw + 5, oy - bh + 19, bw * 2 - 10,
                     bh * 2 - 10))
        NS._ellipse(surface, P["ogre_light"],
                    (ox - bw + 9, oy - bh + 23, bw * 2 - 19,
                     bh * 2 - 17))
        # dada atas
        NS._ellipse(surface, P["ogre_dark"],
                    (ox - 16, oy - 22, 32, 20))
        NS._ellipse(surface, P["ogre_mid"],
                    (ox - 14, oy - 21, 28, 17))
        NS._ellipse(surface, P["ogre_light"],
                    (ox - 10, oy - 19, 18, 11))
        # pektoral kiri-kanan (arc bawah)
        NS._aaline(surface, P["ogre_dark"],
                   (ox - 11, oy - 12), (ox - 2, oy - 9), 2)
        NS._aaline(surface, P["ogre_dark"],
                   (ox + 2, oy - 9), (ox + 11, oy - 12), 2)
        # specular cluster (kiri-atas, konsisten key light)
        NS._aacircle(surface, P["ogre_high"],
                     (ox - bw + 12, oy - bh + 26), 3)
        NS._aacircle(surface, P["ogre_shine"],
                     (ox - bw + 13, oy - bh + 25), 1)
        NS._aacircle(surface, P["ogre_high"],
                     (ox - 8, oy - 18), 2)
        # dither band perut (transisi mid->light)
        for i in range(5):
            dx = ox - bw + 10 + i * 5
            dy = oy - bh + 22 + (i % 2)
            NS._aacircle(surface, P["ogre_mid"], (dx, dy), 1)
        # pusar + bulu dada
        NS._aacircle(surface, P["ogre_darkest"], (ox + 2, oy + 12), 2)
        NS._aacircle(surface, P["ogre_dark"], (ox - 4, oy - 8), 1)
        NS._aacircle(surface, P["ogre_dark"], (ox + 5, oy - 6), 1)
        NS._aacircle(surface, P["ogre_dark"], (ox, oy - 2), 1)
        # denyut vena saat rage
        if rage:
            pul = 0.5 + 0.5 * math.sin(phase * 6.0)
            NS._aaline(surface, (*P["acid_mid"], int(120 + 100 * pul)),
                       (ox - 8, oy - 4), (ox - 2, oy + 2), 1)
            NS._aaline(surface, (*P["acid_mid"], int(120 + 100 * pul)),
                       (ox + 6, oy - 8), (ox + 9, oy - 1), 1)

    def _draw_ogre_armor(surface, ox, oy, phase, f, rage):
        """Harness X + pauldron baja + sabuk kuningan."""
        NS = _NS_alchemist
        P = NS.PALETTE
        # harness diagonal (dua tali kulit berjahit)
        for sgn in (1, -1):
            x0 = ox - sgn * 15
            y0 = oy - 22
            x1 = ox + sgn * 14
            y1 = oy + 8
            NS._aaline(surface, P["leather_darkest"],
                       (x0 - f, y0), (x1 - f, y1), 4)
            NS._aaline(surface, P["leather_mid"], (x0 - f, y0),
                       (x1 - f, y1), 2)
            for t in (0.3, 0.55, 0.8):
                sxp = int(x0 + (x1 - x0) * t) - f
                syp = int(y0 + (y1 - y0) * t)
                NS._aacircle(surface, P["leather_light"],
                             (sxp, syp), 1)
        # gesper tengah (brass + sigil gold)
        NS._rect(surface, P["brass_dark"],
                 (ox - 4 - f, oy - 9, 8, 8), border_radius=1)
        NS._rect(surface, P["brass_mid"],
                 (ox - 3 - f, oy - 8, 6, 6), border_radius=1)
        NS._aacircle(surface, P["gold_light"], (ox - f, oy - 5), 2)
        NS._aacircle(surface, P["gold_shine"], (ox - f - 1, oy - 6), 1)
        # pauldron bahu depan (plat baja berpaku)
        px, py = ox + f * 17, oy - 30
        NS._ellipse(surface, P["metal_darkest"],
                    (px - 9, py - 5, 18, 13))
        NS._ellipse(surface, P["metal_dark"],
                    (px - 7, py - 4, 14, 10))
        NS._ellipse(surface, P["metal_mid"],
                    (px - 5, py - 3, 9, 6))
        NS._aacircle(surface, P["metal_light"], (px - 3, py - 2), 2)
        for rv in ((-5, -3), (3, -3), (0, 1)):
            NS._aacircle(surface, P["metal_shine"],
                         (px + rv[0], py + rv[1]), 1)
        # baut rage menyala
        if rage:
            pul = 0.5 + 0.5 * math.sin(phase * 5.0)
            NS._aacircle(surface, (*P["acid_hot"],
                                   int(120 + 120 * pul)),
                         (px, py - 1), 2)
        # sabuk pinggang + gesper besar
        NS._rect(surface, P["leather_darkest"],
                 (ox - 21, oy + 14, 42, 9))
        NS._rect(surface, P["leather_dark"],
                 (ox - 19, oy + 15, 38, 6))
        NS._rect(surface, P["leather_mid"],
                 (ox - 17, oy + 16, 34, 3))
        NS._rect(surface, P["brass_dark"],
                 (ox - 6, oy + 14, 12, 9), border_radius=1)
        NS._rect(surface, P["brass_mid"],
                 (ox - 5, oy + 15, 10, 7), border_radius=1)
        NS._rect(surface, P["brass_light"],
                 (ox - 4, oy + 15, 8, 2))
        NS._aacircle(surface, P["gold_shine"], (ox, oy + 18), 2)
        NS._aacircle(surface, P["gold_light"], (ox, oy + 18), 1)

    def _draw_backpack(surface, bx, by, phase, f, rage):
        """Rangka kayu + 3 botol ramuan berkilau di punggung ogre."""
        NS = _NS_alchemist
        P = NS.PALETTE
        # rangka kulit-kayu
        NS._poly(surface, P["shadow_deep"],
                 [(bx - 9, by - 12), (bx + 9, by - 12), (bx + 9, by + 12),
                  (bx - 9, by + 12)])
        NS._poly(surface, P["leather_darkest"],
                 [(bx - 8, by - 11), (bx + 8, by - 11), (bx + 8, by + 11),
                  (bx - 8, by + 11)])
        NS._poly(surface, P["leather_dark"],
                 [(bx - 6, by - 9), (bx + 6, by - 9), (bx + 6, by + 9),
                  (bx - 6, by + 9)])
        NS._aaline(surface, P["leather_mid"],
                   (bx - 6, by), (bx + 6, by), 1)
        # tali silang
        NS._aaline(surface, P["leather_darkest"],
                   (bx - 6, by - 9), (bx + 6, by + 9), 1)
        NS._aaline(surface, P["leather_darkest"],
                   (bx + 6, by - 9), (bx - 6, by + 9), 1)
        # 3 botol: asam (hijau), ramuan (ungu), emas
        contents = (
            (P["glass_dark"], P["glass_mid"], P["glass_light"],
             P["acid_hot"]),
            (P["gob_darkest"], P["gob_dark"], P["gob_mid"],
             P["gob_high"]),
            (P["gold_darkest"], P["gold_dark"], P["gold_mid"],
             P["gold_light"]),
        )
        for i, (dar, mid, lig, hot) in enumerate(contents):
            bxx = bx - 5 + i * 5
            byy = by - 5 + (i % 2) * 4
            slosh = int(math.sin(phase * 1.6 + i * 2.1) * 1)
            NS._rect(surface, dar, (bxx - 2, byy - 3, 4, 8),
                     border_radius=1)
            NS._rect(surface, mid, (bxx - 1, byy - 2 + slosh, 2, 6),
                     border_radius=1)
            NS._aacircle(surface, lig, (bxx, byy + 3 - slosh), 1)
            NS._aacircle(surface, P["leather_dark"],
                         (bxx, byy - 4), 1)
            if rage and i == 0:
                NS._aacircle(surface, (*P["acid_bright"], 160),
                             (bxx, byy), 4)
        # gelembung asam kecil naik dari botol hijau
        bt = (phase * 0.7) % 1.0
        NS._aacircle(surface, (*P["acid_bright"],
                               int(180 * (1 - bt))),
                     (bx - 5, by - 6 - int(bt * 6)), 1)

    def _draw_ogre_head(surface, hx, hy, f, phase, action, rage):
        """Kepala ogre: brow berat, underbite bertaring, telinga,
        ikat kain, war-paint asam, mata menyala saat rage."""
        NS = _NS_alchemist
        P = NS.PALETTE
        nod = int(math.sin(phase * 0.9) * 1) if action == "idle" else 0
        hy += nod
        # tengkorak
        NS._ellipse(surface, P["shadow_deep"],
                    (hx - 12, hy - 11 + 2, 24, 22))
        NS._ellipse(surface, P["ogre_darkest"],
                    (hx - 11, hy - 10 + 2, 22, 20))
        NS._ellipse(surface, P["ogre_dark"],
                    (hx - 9, hy - 8 + 2, 18, 16))
        NS._ellipse(surface, P["ogre_mid"],
                    (hx - 6, hy - 6 + 2, 12, 11))
        # moncong / rahang underbite
        NS._ellipse(surface, P["ogre_dark"],
                    (hx + f * 3 - 6, hy + 3, 13, 8))
        NS._ellipse(surface, P["ogre_mid"],
                    (hx + f * 3 - 4, hy + 4, 9, 5))
        # brow ridge berat
        NS._poly(surface, P["ogre_darkest"], [
            (hx - 9, hy - 3), (hx + 8, hy - 3), (hx + 7, hy - 1),
            (hx - 8, hy - 1)])
        NS._poly(surface, P["ogre_dark"], [
            (hx - 8, hy - 3), (hx + 7, hy - 3), (hx + 6, hy - 2),
            (hx - 7, hy - 2)])
        # mata (kedip deterministik ~2.6 dtk) + glow rage
        blink = 1 if (phase % (math.pi * 5.0)) < 0.14 else 0
        eye_c = P["eye_rage"] if rage else P["eye_hot"]
        for ex in (hx - 5, hx + 4):
            if blink:
                NS._aaline(surface, P["ogre_darkest"],
                           (ex - 1, hy - 1), (ex + 2, hy - 1), 1)
            else:
                NS._aacircle(surface, P["eye_dark"], (ex, hy), 2)
                NS._aacircle(surface, eye_c, (ex, hy), 1)
        # taring atas-bawah (underbite: taring bawah naik)
        for tx, up in ((hx - 5, 1), (hx + 5, 1), (hx - 2, -1)):
            ty = hy + 8 if up > 0 else hy + 6
            d = -3 if up > 0 else 3
            NS._poly(surface, P["bone_dark"], [
                (tx - 1, ty), (tx + 2, ty), (tx + 1, ty + d),
                (tx, ty + d)])
            NS._poly(surface, P["bone_mid"], [
                (tx - 1, ty), (tx + 1, ty), (tx + 1, ty + d),
                (tx, ty + d)])
            NS._aacircle(surface, P["bone_light"],
                         (tx + f, ty + d), 1)
        # hidung
        NS._aacircle(surface, P["ogre_darkest"],
                     (hx + f * 1, hy + 1), 2)
        # telinga runcing
        for sgn in (-1, 1):
            ex = hx + sgn * 11
            NS._poly(surface, P["ogre_darkest"],
                     [(ex, hy - 2), (ex + sgn * 6, hy - 7),
                      (ex + sgn * 5, hy + 2)])
            NS._poly(surface, P["ogre_dark"],
                     [(ex, hy - 1), (ex + sgn * 4, hy - 5),
                      (ex + sgn * 4, hy + 1)])
        # ikat kain + war paint
        NS._rect(surface, P["leather_darkest"],
                 (hx - 11, hy - 12 + 2, 22, 5))
        NS._rect(surface, P["leather_dark"],
                 (hx - 10, hy - 11 + 2, 20, 3))
        NS._aaline(surface, P["acid_mid"],
                   (hx - 6, hy - 4), (hx - 2, hy + 6), 2)
        NS._aaline(surface, P["acid_mid"],
                   (hx + 6, hy - 4), (hx + 2, hy + 6), 2)
        # topknot kecil
        NS._aacircle(surface, P["leather_mid"],
                     (hx - f * 2, hy - 11), 3)
        NS._aacircle(surface, P["leather_light"],
                     (hx - f * 3, hy - 12), 2)

    def _draw_acid_gun(surface, hx, hy, ang, f, firing, phase):
        """Acid gun goblin: laras kuningan + tangki kaca + moncong."""
        NS = _NS_alchemist
        P = NS.PALETTE
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca

        def pt(dist, side):
            return (int(hx + ca * dist + px * side),
                    int(hy + sa * dist + py * side))

        # laras
        NS._poly(surface, P["shadow_deep"],
                 [pt(-2, -3), pt(13, -3), pt(13, 3), pt(-2, 3)])
        NS._poly(surface, P["brass_dark"],
                 [pt(-1, -3), pt(12, -3), pt(12, 3), pt(-1, 3)])
        NS._poly(surface, P["brass_mid"],
                 [pt(-1, -2), pt(11, -2), pt(11, 2), pt(-1, 2)])
        NS._aaline(surface, P["brass_light"], pt(0, -1), pt(10, -1), 1)
        # cincin laras
        for d in (3, 8):
            NS._aaline(surface, P["brass_dark"], pt(d, -3), pt(d, 3), 1)
        # tangki kaca asam di atas laras
        tk = pt(4, -5)
        slosh = int(math.sin(phase * 2.2) * 1)
        NS._ellipse(surface, P["glass_dark"],
                    (tk[0] - 3, tk[1] - 3 + slosh, 6, 7))
        NS._ellipse(surface, P["glass_mid"],
                    (tk[0] - 2, tk[1] - 2 + slosh, 4, 5))
        NS._aacircle(surface, P["glass_shine"], (tk[0] - 1, tk[1] - 2),
                     1)
        NS._aacircle(surface, P["acid_hot"], (tk[0], tk[1] + 1), 1)
        # pegangan + pelatuk
        gp = pt(0, 4)
        NS._poly(surface, P["leather_darkest"],
                 [pt(-1, 3), pt(2, 3), pt(1, 7), pt(-2, 7)])
        NS._aacircle(surface, P["leather_mid"], (gp[0], gp[1]), 2)
        # moncong: uap tetes saat idle, semburan saat firing
        mz = pt(13, 0)
        if firing:
            NS._aacircle(surface, (*P["acid_white"], 230),
                         (mz[0], mz[1]), 4)
            NS._aacircle(surface, P["acid_hot"], (mz[0], mz[1]), 2)
        else:
            drip = (phase * 0.5) % 1.0
            NS._aacircle(surface, (*P["acid_bright"],
                                   int(190 * (1 - drip))),
                         (mz[0], mz[1] + int(drip * 5)), 1)
        return mz

    def _draw_goblin_rider(surface, gx, gy, f, phase, action, ap,
                           rage, aim_angle=None):
        """Goblin alkemis menunggangi bahu ogre.

        action mengendalikan lengan: q = bidik senapan, w = botol
        diangkat (gemetar saat charge), e/r = pengangkatan, lainnya
        genggam tali. Return posisi tangan senapan & tangan botol.
        """
        NS = _NS_alchemist
        P = NS.PALETTE
        bob = int(math.sin(phase * 1.1) * 1)
        gx += 0
        gy += bob
        # badan goblin
        NS._poly(surface, P["shadow_deep"],
                 [(gx - 6, gy - 8), (gx + 6, gy - 8), (gx + 6, gy + 8),
                  (gx - 6, gy + 8)])
        NS._poly(surface, P["gob_darkest"],
                 [(gx - 5, gy - 7), (gx + 5, gy - 7), (gx + 5, gy + 7),
                  (gx - 5, gy + 7)])
        NS._poly(surface, P["gob_dark"],
                 [(gx - 4, gy - 6), (gx + 4, gy - 6), (gx + 4, gy + 5),
                  (gx - 4, gy + 5)])
        NS._poly(surface, P["gob_mid"],
                 [(gx - 3, gy - 5), (gx + 3, gy - 5), (gx + 3, gy + 3),
                  (gx - 3, gy + 3)])
        # rompi kulit + gesper
        NS._rect(surface, P["leather_darkest"],
                 (gx - 4, gy - 2, 8, 7))
        NS._rect(surface, P["leather_dark"], (gx - 3, gy - 1, 6, 5))
        NS._aacircle(surface, P["brass_light"], (gx, gy + 1), 1)
        # kaki mencengkeram bahu ogre
        NS._aaline(surface, P["gob_darkest"],
                   (gx - 3, gy + 6), (gx - 6 + f * 3, gy + 10), 2)
        NS._aaline(surface, P["gob_darkest"],
                   (gx + 3, gy + 6), (gx + 6 + f * 3, gy + 10), 2)
        # kepala goblin
        NS._ellipse(surface, P["shadow_deep"],
                    (gx - 6, gy - 15, 12, 11))
        NS._ellipse(surface, P["gob_darkest"],
                    (gx - 5, gy - 14, 10, 9))
        NS._ellipse(surface, P["gob_dark"],
                    (gx - 4, gy - 13, 8, 7))
        NS._ellipse(surface, P["gob_mid"],
                    (gx - 2, gy - 12, 4, 5))
        # mata glow (kuning-panas; rage = hijau)
        eye = P["eye_rage"] if rage else P["eye_hot"]
        NS._aacircle(surface, eye, (gx + f * 1 - 1, gy - 11), 1)
        NS._aacircle(surface, eye, (gx + f * 1 + 2, gy - 11), 1)
        # hidung bawang + senyum snaggle
        NS._aacircle(surface, P["gob_mid"],
                     (gx + f * 4, gy - 9), 2)
        NS._aacircle(surface, P["gob_high"],
                     (gx + f * 4, gy - 10), 1)
        NS._aaline(surface, P["gob_darkest"],
                   (gx + f * 1, gy - 7), (gx + f * 4, gy - 7), 1)
        NS._aacircle(surface, P["bone_light"],
                     (gx + f * 3, gy - 7), 1)
        # telinga
        for sgn in (-1, 1):
            ex = gx + sgn * 5
            NS._poly(surface, P["gob_darkest"],
                     [(ex, gy - 12), (ex + sgn * 6, gy - 15),
                      (ex + sgn * 5, gy - 9)])
            NS._poly(surface, P["gob_dark"],
                     [(ex, gy - 12), (ex + sgn * 4, gy - 14),
                      (ex + sgn * 4, gy - 10)])
        # topi alkemis (topi kulit ber-band kuningan + kaca)
        NS._poly(surface, P["shadow_deep"],
                 [(gx - 6, gy - 17), (gx + 6, gy - 17), (gx + 5, gy - 25),
                  (gx - 5, gy - 25)])
        NS._poly(surface, P["leather_darkest"],
                 [(gx - 5, gy - 17), (gx + 5, gy - 17), (gx + 4, gy - 24),
                  (gx - 4, gy - 24)])
        NS._poly(surface, P["leather_mid"],
                 [(gx - 4, gy - 18), (gx + 4, gy - 18), (gx + 3, gy - 23),
                  (gx - 3, gy - 23)])
        NS._aaline(surface, P["brass_mid"],
                   (gx - 4, gy - 19), (gx + 4, gy - 19), 2)
        NS._aacircle(surface, P["glass_shine"], (gx, gy - 21), 1)
        NS._aacircle(surface, P["acid_hot"], (gx, gy - 21), 1)

        # ── lengan & pose ──────────────────────────────────────────
        gun_hand = (gx + f * 9, gy - 4)
        bottle_hand = (gx + f * 3, gy - 10)
        aim_ang = (float(aim_angle) if aim_angle is not None
                   else -0.1 + math.sin(phase) * 0.06)
        if action == "q_cast":
            gun_hand = (gx + f * 8, gy - 6)
            NS._aaline(surface, P["gob_dark"],
                       (gx + 3, gy - 4), gun_hand, 3)
            NS._aaline(surface, P["gob_mid"],
                       (gx + 3, gy - 5), gun_hand, 1)
            recoil = int(math.sin(phase * 8.0) * 1)
            mz = NS._draw_acid_gun(surface, gun_hand[0] + f * 2,
                                   gun_hand[1] + recoil, aim_ang, f,
                                   firing=True, phase=phase)
            gun_hand = mz
        elif action == "w_cast":
            trem = 1 if int(phase * 26) % 2 else 0
            bottle_hand = (gx + f * (2 + trem), gy - 30)
            NS._aaline(surface, P["gob_dark"],
                       (gx + 2, gy - 5), bottle_hand, 3)
            NS._aaline(surface, P["gob_mid"],
                       (gx + 2, gy - 6), bottle_hand, 1)
            glow = 0.5 + 0.5 * math.sin(phase * 6.0)
            NS._aacircle(surface, P["glass_dark"],
                         bottle_hand, 4)
            NS._aacircle(surface, P["glass_mid"], bottle_hand, 3)
            NS._aacircle(surface, P["acid_bright"], bottle_hand, 2)
            NS._aacircle(surface, P["acid_hot"],
                         (bottle_hand[0] - 1, bottle_hand[1] - 1), 1)
            NS._aacircle(surface, (*P["acid_glow"],
                                   int(140 * glow)), bottle_hand, 7)
            # tangan satunya pegang tali
            NS._aaline(surface, P["gob_dark"],
                       (gx - 3, gy - 3), (gx - 7, gy + 2), 2)
        else:
            # genggam senapan ke atas-depan
            gun_hand = (gx + f * 8, gy - 8)
            NS._aaline(surface, P["gob_dark"],
                       (gx + 3, gy - 5), gun_hand, 3)
            NS._aaline(surface, P["gob_mid"],
                       (gx + 3, gy - 6), gun_hand, 1)
            mz = NS._draw_acid_gun(surface, gun_hand[0], gun_hand[1],
                                   -0.55 + math.sin(phase * 0.9) * 0.08,
                                   f, firing=False, phase=phase)
            gun_hand = mz
            if action in ("e_cast", "r_cast"):
                pump = int(math.sin(phase * 3.0) * 3)
                bottle_hand = (gx - f * 6, gy - 12 - pump)
                NS._aaline(surface, P["gob_dark"],
                           (gx - 3, gy - 4), bottle_hand, 3)
                NS._aacircle(surface, P["gob_mid"], bottle_hand, 2)
                if action == "r_cast":
                    NS._aacircle(surface, P["gold_light"],
                                 bottle_hand, 2)
                    NS._aacircle(surface, P["gold_shine"],
                                 (bottle_hand[0], bottle_hand[1] - 1),
                                 1)
            else:
                NS._aaline(surface, P["gob_dark"],
                           (gx - 3, gy - 3), (gx - 7, gy + 2), 2)
        return gun_hand, bottle_hand

    # ==================================================================
    # FULL COMPOSITE — buffer -> outline siluet -> lighting -> blit
    # (+ pose cache LRU supaya frame stabil 60 fps di mobile)
    # ==================================================================
    def _draw_alch_full_raw(surface, cx, cy, facing, phase, action,
                            attack_progress=0, rage=False,
                            detail=False, boss=None):
        """Rig masterwork v2 — ogre chemist + goblin rider, prosedural.

        Semua koordinat lokal: (0,0) = jangkar pinggul, +x maju
        (facing), y ke bawah. Topi goblin -68, botol W -88, kaki +56.
        Urutan lapisan: backpack -> goblin -> back arm -> legs ->
        skirt -> torso -> armor -> head -> goblin arms/weapon ->
        front arm + cleaver.
        """
        NS = _NS_alchemist
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        attack = action == "attack"
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0

        # ═══ 1. GERAK BADAN: root / lean / sway (satu sumber dgn
        # _local supaya anchor FX hidup cocok piksel-per-piksel) ═══
        lean, root_y = NS._rig_shift(action, phase, ap)
        L = lambda lx, ly: NS._local_to_screen(cx, cy, f, lean,
                                               root_y, lx, ly)

        pose = NS._attack_pose(ap) if attack else None
        flare = pose["flare"] if pose else 1.0

        # ═══ 2. BACKPACK (paling belakang) ═══
        NS._draw_backpack(surface, *L(-17, -12), phase, f, rage)

        # ═══ 3. GOBLIN RIDER (di belakang torso, di atas backpack) ═══
        aim_angle = None
        if action == "q_cast":
            if boss is not None:
                tx, ty = NS._target_position(boss, cx, cy)
                hx, hy = L(-13 + 8, -36 - 6)
                aim_angle = math.atan2(ty - hy, tx - hx)
            else:
                aim_angle = -0.1
        goblin_x, goblin_y = L(-13, -44)
        NS._draw_goblin_rider(surface, goblin_x, goblin_y, f, phase,
                              action, ap, rage, aim_angle=aim_angle)

        # ═══ 4. LENGAN BELAKANG + CLEAVER BELAKANG ═══
        grip_b = NS._cleaver_grip_local(action, phase, ap, back=True)
        ang_b = NS._cleaver_angle_local(action, phase, ap, back=True)
        gb = L(*grip_b)
        shb = L(-17, -30)
        flex = 1.0 if action == "e_cast" else 0.0
        NS._draw_ogre_arm(surface, shb[0], shb[1], gb[0], gb[1], f,
                          back=True, flex=flex)
        NS._draw_cleaver(surface, gb[0], gb[1], ang_b, f, phase)

        # ═══ 5. KAKI (alternating walk + foot plant) ═══
        if action == "walk":
            la = math.sin(phase) * 0.5
            lift_a = max(0.0, math.sin(phase + 0.4)) * 5
            lift_b = max(0.0, math.sin(phase + math.pi + 0.4)) * 5
        else:
            la = 0.08
            lift_a = lift_b = 0.0
            if attack:
                la = 0.10 + pose["lunge"] * 0.012
        hA = L(-8, 20)
        hB = L(8, 20)
        NS._draw_ogre_leg(surface, hB[0], hB[1], la, lift_a, True, f)
        NS._draw_ogre_leg(surface, hA[0], hA[1], -la, lift_b, False, f)

        # ═══ 6. ROK ROMPUL ROBEK (3 helai, inersia tertinggal) ═══
        lag = 0.0
        if action == "walk":
            lag = math.sin(phase + 2.1) * 3.2
        elif attack:
            lag = -pose["lean"] * 0.9
        else:
            lag = math.sin(phase * 0.55) * 1.6
        for i, off in enumerate((-14, -4, 7)):
            wave = int(lag + math.sin(phase * 1.0 + i) * 2)
            length = 22 + (i % 2) * 5
            p0 = L(off - 4, 22)
            p1 = L(off + 4, 22)
            p2 = L(off + 3 + wave, 22 + length)
            p3 = L(off - 3 + wave, 22 + length)
            NS._poly(surface, P["shadow_deep"],
                     [(p2[0] + 1, p2[1] + 1), (p3[0] + 1, p3[1] + 1),
                      (p1[0] + 1, p1[1] + 1)])
            NS._poly(surface, P["leather_darkest"],
                     [p0, p1, p2, p3])
            NS._poly(surface, P["leather_dark"], [
                L(off - 3, 23), L(off + 3, 23),
                L(off + 2 + wave, 22 + length - 2),
                L(off - 2 + wave, 22 + length - 2)])
            NS._poly(surface, P["leather_mid"], [
                L(off - 2, 24), L(off + 2, 24),
                L(off + 1 + wave, 22 + length - 5),
                L(off - 1 + wave, 22 + length - 5)])

        # ═══ 7. TORSO + ARMOR + KEPALA ═══
        NS._draw_ogre_torso(surface, *L(0, 2), phase, flare, rage, f)
        NS._draw_ogre_armor(surface, *L(0, 0), phase, f, rage)
        # leher tebal
        nck0, nck1 = L(-8, -30), L(8, -18)
        NS._poly(surface, NS.PALETTE["ogre_dark"],
                 [nck0, (nck1[0], nck0[1]), (nck1[0], nck1[1]),
                  (nck0[0], nck1[1])])
        hd = L(4, -50)
        if action == "attack":
            hd = (hd[0], hd[1] + int(pose["dip"] * 0.4))
        NS._draw_ogre_head(surface, hd[0], hd[1], f, phase, action,
                           rage)

        # ═══ 8. LENGAN DEPAN + CLEAVER UTAMA (paling depan) ═══
        grip_f = NS._cleaver_grip_local(action, phase, ap, back=False)
        ang_f = NS._cleaver_angle_local(action, phase, ap, back=False)
        gf = L(*grip_f)
        shf = L(17, -30)
        NS._draw_ogre_arm(surface, shf[0], shf[1], gf[0], gf[1], f,
                          back=False, flex=flex)
        NS._draw_cleaver(surface, gf[0], gf[1], ang_f, f, phase)

        # ═══ 9. HIGHLIGHTS / detail portrait ═══
        if rage:
            pul = 0.5 + 0.5 * math.sin(phase * 7.0)
            NS._aacircle(surface, (*P["acid_hot"],
                                   int(150 + 100 * pul)),
                         (gf[0], gf[1]), 4)
        if detail:
            NS._draw_alch_masterwork_details(surface, L, f, phase)

    def _draw_alch_masterwork_details(surface, L, f, phase):
        """Pass detail portrait: jahitan, paku, ukiran rune asam."""
        NS = _NS_alchemist
        P = NS.PALETTE
        # rune asam di pauldron
        px, py = L(17 * f, -27)
        NS._aaline(surface, P["acid_mid"], (px - 3, py - 1),
                   (px + 3, py - 1), 1)
        NS._aaline(surface, P["acid_mid"], (px, py - 3), (px, py + 2),
                   1)
        # jahitan harness
        for t in ((-6, -14), (-2, -6), (2, 2)):
            sxp, syp = L(t[0], t[1])
            NS._aacircle(surface, P["leather_high"], (sxp, syp), 1)
        # tetes asam menggantung di moncong gun
        gx, gy = L(9, -44)
        drip = (phase * 0.4) % 1.0
        NS._aacircle(surface, (*P["acid_bright"],
                               int(200 * (1 - drip))),
                     (gx, gy + int(drip * 7)), 1)

    def _composite_body(facing, phase, action, attack_progress=0,
                        rage=False, detail=False, boss=None):
        """Komposit badan -> (crop, dx, dy). dx,dy = offset sudut
        kiri-atas crop relatif jangkar. Outline siluet hitam 1 px
        4 arah + pass cahaya dikerjakan DI SINI (sekali per pose)."""
        NS = _NS_alchemist
        if NS._body_buf is None:
            NS._body_buf = pygame.Surface((NS.RIG_W, NS.RIG_H),
                                          pygame.SRCALPHA)
        buf = NS._body_buf
        buf.fill((0, 0, 0, 0))
        NS._draw_alch_full_raw(buf, NS.RIG_OX, NS.RIG_OY, facing,
                               phase, action, attack_progress,
                               rage=rage, detail=detail, boss=boss)
        used = buf.get_bounding_rect(min_alpha=1)
        if used.width <= 2 or used.height <= 2:
            return None, 0, 0
        used.inflate_ip(2, 2)
        used.clamp_ip(buf.get_rect())
        sub = buf.subsurface(used).copy()
        dx = used.left - NS.RIG_OX
        dy = used.top - NS.RIG_OY
        # pass cahaya DULU (rim/shade) supaya outline tetap hitam pekat,
        # lalu outline siluet 1 px 4 arah di atasnya (konvensi gorath).
        if _lighting is not None:
            try:
                _lighting.apply_to_rig(sub, rim_add=(26, 40, 14),
                                       shade_mul=168)
            except Exception:
                pass
        edge = sub.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        w, h = sub.get_size()
        padded = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
        for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            padded.blit(edge, (1 + ddx, 1 + ddy))
        padded.blit(sub, (1, 1))
        return padded, dx - 1, dy - 1

    def _draw_alch_full(surface, cx, cy, facing, phase, action,
                        attack_progress=0, rage=False, detail=False,
                        boss=None):
        """Komposit langsung (tanpa cache) — kontrak API lama."""
        NS = _NS_alchemist
        surf, dx, dy = NS._composite_body(facing, phase, action,
                                          attack_progress, rage=rage,
                                          detail=detail, boss=boss)
        if surf is None:
            return
        surface.blit(surf, (int(cx) + dx, int(cy) + dy))

    # ── pose cache: kuantum pose -> satu blit per frame ────────────
    _POSE_CACHE_MAX = 44

    def _pose_bucket(action, phase, ap):
        if action == "attack":
            return int(max(0.0, min(1.0, ap)) * 29)
        cyc = (phase / (math.pi * 2.0)) % 1.0
        return int(cyc * 24.0) % 24

    def _aim_bucket(action, boss, cx, cy):
        """Kuantum arah bidik goblin (12 bucket) — dipakai pose cache."""
        if action != "q_cast" or boss is None:
            return 0
        try:
            tx, ty = _NS_alchemist._target_position(boss, cx, cy)
            return int(math.atan2(ty - cy, tx - cx) /
                       (math.pi / 6.0)) % 12
        except Exception:
            return 0

    def _draw_alch_pose(surface, cx, cy, facing, phase, action, ap=0.0,
                        rage=False, detail=False, boss=None):
        """Badan dengan pose LRU-cache (idle 24/walk 24/attack 30
        bucket) — cache-miss ~2 ms, hit ~0.1 ms; animasi tetap
        kontinu karena bucket << jumlah frame siklus."""
        NS = _NS_alchemist
        key = (action, 1 if facing >= 0 else -1,
               NS._pose_bucket(action, phase, ap), bool(rage),
               bool(detail),
               NS._aim_bucket(action, boss, cx, cy))
        entry = NS._POSE_CACHE.get(key)
        if entry is None:
            surf, dx, dy = NS._composite_body(
                facing, phase, action, ap, rage=rage, detail=detail,
                boss=boss)
            if surf is None:
                return
            entry = (surf, int(dx), int(dy))
            NS._POSE_CACHE[key] = entry
            NS._POSE_ORDER.append(key)
            while len(NS._POSE_ORDER) > NS._POSE_CACHE_MAX:
                old = NS._POSE_ORDER.pop(0)
                NS._POSE_CACHE.pop(old, None)
        surface.blit(entry[0], (int(cx) + entry[1],
                                int(cy) + entry[2]))

    # ==================================================================
    # POSE MODES (wrapper — bayangan + wisps + badan)
    # ==================================================================
    def _draw_alch_idle(surface, boss, x, y, rage=False, detail=False):
        NS = _NS_alchemist
        phase = float(getattr(boss, "pulse", 0.0))
        bob = int(math.sin(phase * 0.7) * 2)
        if not detail:
            NS._draw_shadow(surface, x, y + NS.GROUND_DY)
            NS._draw_alch_wisps(surface, x, y + 44, phase)
        NS._draw_alch_pose(surface, x, y + bob,
                           getattr(boss, "direction", 1), phase,
                           "idle", 0.0, rage=rage, detail=detail)

    def _draw_alch_walk(surface, boss, x, y, rage=False, detail=False):
        NS = _NS_alchemist
        phase = float(getattr(boss, "pulse", 0.0)) * 2.4
        bob = int(abs(math.sin(phase * 1.3)) * 3)
        sway = int(math.sin(phase) * 2)
        if not detail:
            NS._draw_shadow(surface, x + sway, y + NS.GROUND_DY)
            NS._draw_alch_wisps(surface, x + sway, y + 40, phase,
                                trail=True,
                                facing=getattr(boss, "direction", 1))
        NS._draw_alch_pose(surface, x + sway, y - bob,
                           getattr(boss, "direction", 1), phase,
                           "walk", 0.0, rage=rage, detail=detail)

    def _draw_alch_attack(surface, boss, x, y, rage=False,
                          detail=False):
        NS = _NS_alchemist
        progress = max(0.0, min(1.0,
                                getattr(boss, "_alch_attack_progress",
                                        0.0)))
        ap = NS._attack_curve(progress)
        pose = NS._attack_pose(ap)
        lunge = int(math.sin(min(1.0, progress * 1.2) * math.pi) *
                    pose["lunge"] * 0.55) * \
            (1 if getattr(boss, "direction", 1) >= 0 else -1)
        if not detail:
            NS._draw_shadow(surface, x + lunge, y + NS.GROUND_DY,
                            lift=2 if 0.10 < progress < 0.30 else 0)
            NS._draw_alch_wisps(surface, x + lunge, y + 40,
                                float(getattr(boss, "pulse", 0.0)),
                                intense=True)
        NS._draw_alch_pose(surface, x + lunge, y,
                           getattr(boss, "direction", 1),
                           float(getattr(boss, "pulse", 0.0)),
                           "attack", ap, rage=rage, detail=detail)
        if not detail and not NS._fx_owned(boss):
            NS._draw_cleaver_swing_arc(surface, x + lunge, y,
                                       getattr(boss, "direction", 1),
                                       progress)
            NS._draw_swing_impact(surface, x + lunge, y,
                                  getattr(boss, "direction", 1),
                                  progress)

    def _draw_alch_qcast(surface, boss, x, y, timer, rage=False,
                         detail=False):
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        NS = _NS_alchemist
        bob = int(math.sin(float(getattr(boss, "pulse", 0.0)) * 0.7)
                  * 2)
        recoil = int(math.sin(progress * math.pi * 2) * 2) * \
            -1 * (1 if getattr(boss, "direction", 1) >= 0 else -1)
        if not detail:
            NS._draw_shadow(surface, x + recoil, y + NS.GROUND_DY)
            NS._draw_alch_wisps(surface, x + recoil, y + 40,
                                float(getattr(boss, "pulse", 0.0)),
                                intense=True)
        NS._draw_alch_pose(surface, x + recoil, y + bob,
                           getattr(boss, "direction", 1),
                           float(getattr(boss, "pulse", 0.0)),
                           "q_cast", 0.0, rage=rage, detail=detail,
                           boss=boss)

    def _draw_alch_wcast(surface, boss, x, y, timer, rage=False,
                         detail=False):
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        NS = _NS_alchemist
        bob = int(math.sin(float(getattr(boss, "pulse", 0.0)) * 0.7)
                  * 2)
        if not detail:
            NS._draw_shadow(surface, x, y + NS.GROUND_DY)
            NS._draw_alch_wisps(surface, x, y + 40,
                                float(getattr(boss, "pulse", 0.0)),
                                intense=progress < 0.5)
        NS._draw_alch_pose(surface, x, y + bob,
                           getattr(boss, "direction", 1),
                           float(getattr(boss, "pulse", 0.0)),
                           "w_cast", progress, rage=rage,
                           detail=detail)
        # Lempar botol pada momen yang tepat (canvas fallback; jalur
        # lapisan hidup melempar sendiri lewat _watch_engine_events).
        if 0.35 < progress < 0.45 and not detail:
            if not getattr(boss, "_alch_wcast_spawned", False):
                tx, ty = NS._world_to_screen_target(boss, x, y)
                hx, hy = NS._bottle_hand_screen(boss, x, y)
                NS._spawn_acid_bottle(boss, hx, hy, tx, ty)
                boss._alch_wcast_spawned = True
        if progress > 0.7:
            boss._alch_wcast_spawned = False

    def _draw_alch_ecast(surface, boss, x, y, timer, rage=True,
                         detail=False):
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        NS = _NS_alchemist
        hop = int(math.sin(progress * math.pi) * 6)
        if not detail:
            NS._draw_shadow(surface, x, y + NS.GROUND_DY,
                            lift=hop // 2)
            NS._draw_alch_wisps(surface, x, y + 40,
                                float(getattr(boss, "pulse", 0.0)),
                                intense=True)
        NS._draw_alch_pose(surface, x, y - hop,
                           getattr(boss, "direction", 1),
                           float(getattr(boss, "pulse", 0.0)) * 1.4,
                           "e_cast", progress, rage=True,
                           detail=detail)

    def _draw_alch_rcast(surface, boss, x, y, timer, rage=True,
                         detail=False):
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        NS = _NS_alchemist
        bob = int(math.sin(float(getattr(boss, "pulse", 0.0)) * 1.6)
                  * 2)
        if not detail:
            NS._draw_shadow(surface, x, y + NS.GROUND_DY)
            NS._draw_alch_wisps(surface, x, y + 40,
                                float(getattr(boss, "pulse", 0.0)),
                                intense=True)
        NS._draw_alch_pose(surface, x, y + bob,
                           getattr(boss, "direction", 1),
                           float(getattr(boss, "pulse", 0.0)),
                           "r_cast", progress, rage=True,
                           detail=detail)

    def _world_to_screen_target(boss, x, y):
        """Posisi target skill W (w_target_x/y dunia) -> px layar."""
        NS = _NS_alchemist
        wx = getattr(boss, "w_target_x", None)
        wy = getattr(boss, "w_target_y", None)
        if wx is None or wy is None:
            return NS._target_position(boss, x, y)
        scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
        return (int(x + (float(wx) - float(getattr(boss, "x", x)))
                    / scale),
                int(y + (float(wy) - float(getattr(boss, "y", y)))
                    / scale))

    # ==================================================================
    # CANVAS SWING FX (fallback tanpa lapisan hidup)
    # ==================================================================
    def _cleaver_arc_points(progress, facing, count=16):
        """Titik-titik busur sapuan (windup -> sudut sekarang)."""
        NS = _NS_alchemist
        ap = NS._attack_curve(max(0.0, min(1.0, progress)))
        pose = NS._attack_pose(ap)
        ang_now = pose["blade_f"]
        ang_start = -2.30
        pts = []
        for i in range(count):
            t = (i / float(count - 1)) ** 1.7
            ang = ang_start + (ang_now - ang_start) * t
            grip = NS._cleaver_grip_local("attack", 0.0, ap)
            L = NS.CLEAVER_HANDLE + NS.CLEAVER_BLADE - 2
            pts.append((ang, grip, L))
        return pts, ang_now

    def _draw_cleaver_swing_arc(surface, x, y, facing, progress):
        """Trail sapuan canvas: stamp memudar menyusuri busur —
        mengikuti ARAH serangan (bukan dua posisi snap)."""
        NS = _NS_alchemist
        P = NS.PALETTE
        if progress < 0.28 or progress > 0.78:
            return
        if progress < 0.5:
            visibility = (progress - 0.28) / 0.22
        else:
            visibility = 1.0 - (progress - 0.5) / 0.28
        visibility = max(0.0, min(1.0, visibility))
        if visibility <= 0.02:
            return
        lean, root_y = NS._rig_shift("attack", 0.0,
                                     NS._attack_curve(progress))
        arc, _ang = NS._cleaver_arc_points(progress, facing)
        n = len(arc)
        for i, (ang, grip, L) in enumerate(arc):
            t = i / float(n - 1)
            fade = t ** 1.4 * visibility
            alpha = int(215 * fade)
            if alpha <= 6:
                continue
            gx, gy = NS._local_to_screen(x, y, facing, lean, root_y,
                                         grip[0], grip[1])
            tx = int(gx + math.cos(ang) * L)
            ty = int(gy + math.sin(ang) * L)
            size = 5 + int(5 * t)
            NS._aacircle(surface, (*P["acid_darkest"], alpha),
                         (tx, ty), size)
            NS._aacircle(surface, (*P["acid_mid"], alpha),
                         (tx, ty), max(1, size - 2))
            NS._aacircle(surface, (*P["acid_bright"], alpha),
                         (tx, ty), max(1, size - 4))
            NS._aacircle(surface, (*P["acid_hot"], min(255, alpha)),
                         (tx, ty), max(1, size - 6))

    def _draw_swing_impact(surface, x, y, facing, progress):
        """Bintang + cincin benturan di jendela IMPACT (canvas)."""
        NS = _NS_alchemist
        P = NS.PALETTE
        if progress < 0.46 or progress > 0.74:
            return
        t = (progress - 0.46) / 0.28
        intensity = math.sin(t * math.pi)
        ap = NS._attack_curve(0.54)
        grip = NS._cleaver_grip_local("attack", 0.0, ap)
        ang = NS._attack_pose(ap)["blade_f"]
        lean, root_y = NS._rig_shift("attack", 0.0, ap)
        gx, gy = NS._local_to_screen(x, y, facing, lean, root_y,
                                     grip[0], grip[1])
        ix = int(gx + math.cos(ang) * (NS.CLEAVER_BLADE + 6))
        iy = int(gy + math.sin(ang) * (NS.CLEAVER_BLADE + 6))
        alpha = int(235 * intensity)
        radius = int(10 + intensity * 20)
        NS._aacircle(surface, (*P["acid_dark"], alpha // 2),
                     (ix, iy), radius + 4)
        NS._aacircle(surface, (*P["acid_bright"], alpha),
                     (ix, iy), radius, 3)
        NS._aacircle(surface, (*P["acid_hot"], alpha),
                     (ix, iy), max(1, radius - 6), 2)
        NS._aacircle(surface, (*P["acid_white"], alpha),
                     (ix, iy), max(1, radius // 2))
        for k in range(6):
            ang2 = k * math.pi / 3 + 0.35
            dx = ix + int(math.cos(ang2) * radius * 1.4)
            dy = iy + int(math.sin(ang2) * radius * 1.1)
            NS._draw_acid_droplet(surface, dx, dy, 3, alpha)

    # ==================================================================
    # SKILL Q: ACID SPRAY (cone) — canvas fallback
    # ==================================================================
    def _draw_acid_spray(surface, boss, x, y, timer, phase):
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        NS = _NS_alchemist
        P = NS.PALETTE
        tx, ty = NS._target_position(boss, x, y)
        if progress > 0.85:
            return
        start_x, start_y = NS._gun_end_screen(boss, x, y)
        dx = tx - start_x
        dy = ty - start_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 1:
            dist = 1
        dir_x, dir_y = dx / dist, dy / dist
        perp_x, perp_y = -dir_y, dir_x
        cone_len = int(160 * min(1.0, progress / 0.2))
        for i in range(26):
            t = i / 26
            base_x = start_x + dir_x * cone_len * t
            base_y = start_y + dir_y * cone_len * t
            spread = t * 22
            offset = math.sin(phase * 5 + i * 1.7) * spread
            fx = int(base_x + perp_x * offset)
            fy = int(base_y + perp_y * offset)
            size = int(5 + t * 5)
            alpha = int(230 * (1 - t * 0.3))
            if t < 0.2:
                NS._aacircle(surface, (*P["acid_white"], alpha),
                             (fx, fy), size)
                NS._aacircle(surface, (*P["acid_glow"], alpha),
                             (fx, fy), max(1, size - 2))
            elif t < 0.5:
                NS._aacircle(surface, (*P["acid_hot"], alpha),
                             (fx, fy), size)
                NS._aacircle(surface, (*P["acid_bright"], alpha),
                             (fx, fy), max(1, size - 2))
            elif t < 0.8:
                NS._aacircle(surface, (*P["acid_bright"], alpha),
                             (fx, fy), size)
                NS._aacircle(surface, (*P["acid_mid"], alpha),
                             (fx, fy), max(1, size - 2))
            else:
                NS._aacircle(surface, (*P["acid_mid"], alpha),
                             (fx, fy), size)
                NS._aacircle(surface, (*P["acid_dark"], alpha),
                             (fx, fy), max(1, size - 2))
        NS._aacircle(surface, (*P["acid_white"], 255),
                     (int(start_x), int(start_y)), 6)
        NS._aacircle(surface, (*P["acid_hot"], 255),
                     (int(start_x + dir_x * 6),
                      int(start_y + dir_y * 6)), 4)
        for i in range(8):
            t = (phase * 0.5 + i * 0.12) % 1.0
            drop_t = 0.3 + t * 0.6
            base_x = start_x + dir_x * cone_len * drop_t
            base_y = start_y + dir_y * cone_len * drop_t + int(t * 10)
            NS._draw_acid_droplet(surface, int(base_x), int(base_y),
                                  2, 200)
        # telegraph genangan di target (radius gameplay, world-space)
        r = NS._ring_r(boss, NS.SKILL_RADIUS["q"] * 0.62, surface)
        it = max(0.0, min(1.0, 1.0 - abs(progress - 0.5) / 0.4))
        NS._ground_ring(surface, tx, ty + 4, r,
                        P["acid_dark"], P["acid_bright"],
                        int(200 * it))

    # ==================================================================
    # SKILL E: CHEMICAL RAGE (self buff)
    # ==================================================================
    def _draw_chem_rage_ground(surface, boss, x, y, timer, phase):
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        NS = _NS_alchemist
        P = NS.PALETTE
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for i in range(3):
            r = int(30 + i * 15 + math.sin(phase * 2 + i) * 5)
            NS._ellipse(surface,
                        (*P["acid_bright"], int(120 * pulse)),
                        (x - r, y + 52 - r // 3, r * 2, r // 1.5), 2)
        NS._zone_fill(surface, x, y + 46, 40, P["acid_darkest"],
                      int(120 * pulse))
        # denyut denyut nadi (heal)
        if progress < 0.4:
            rr = int(20 + progress / 0.4 * 52)
            NS._aacircle(surface, (*P["acid_hot"],
                                   int(200 * (1 - progress / 0.4))),
                         (x, y + 46), rr)

    def _draw_chem_rage_foreground(surface, boss, x, y, timer, phase):
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        NS = _NS_alchemist
        P = NS.PALETTE
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        fade = 1.0 if progress < 0.7 else (1.0 - (progress - 0.7) / 0.3)
        for radius in range(50, 10, -4):
            alpha = int((50 - radius) * 4 * pulse * fade)
            if alpha > 0:
                NS._aacircle(surface,
                             (*P["acid_dark"], min(255, alpha)),
                             (x, y - 10), radius)
        for i in range(12):
            t = (phase * 0.8 + i * 0.08) % 1.0
            angle = i * math.pi * 2 / 12
            px = x + int(math.cos(angle) * 25)
            py = y + 15 - int(t * 50)
            alpha = int(255 * (1 - t) * fade)
            if alpha > 0:
                NS._aacircle(surface, (*P["acid_mid"], alpha),
                             (px, py), 4)
                NS._aacircle(surface, (*P["acid_bright"], alpha),
                             (px, py), 2)
                NS._aacircle(surface, (*P["acid_hot"], alpha),
                             (px - 1, py - 1), 1)
        for i in range(6):
            angle = phase * 2 + i * math.pi / 3
            r = 30 + int(math.sin(phase * 3 + i) * 8)
            sx = x + int(math.cos(angle) * r)
            sy = y - 10 + int(math.sin(angle) * r * 0.5)
            NS._aacircle(surface, P["acid_white"], (sx, sy), 2)
            NS._aacircle(surface, P["acid_glow"], (sx, sy), 1)

    # ==================================================================
    # SKILL R: GREEVIL'S GREED (gold storm)
    # ==================================================================
    def _draw_greevil_ground(surface, boss, x, y, timer, phase):
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        NS = _NS_alchemist
        P = NS.PALETTE
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        fade = 1.0 if progress < 0.75 else \
            max(0.0, 1.0 - (progress - 0.75) / 0.25)
        r200 = NS._ring_r(boss, NS.SKILL_RADIUS["r"], surface)
        NS._ground_ring(surface, x, y + 50, r200,
                        P["gold_dark"], P["gold_light"],
                        int(170 * pulse * fade))
        NS._zone_fill(surface, x, y + 46, min(r200, 90),
                      P["gold_darkest"], int(110 * pulse * fade))
        if progress > 0.3:
            pile_grow = min(1.0, (progress - 0.3) / 0.5)
            NS._draw_gold_pile(surface, x, y + 56, pile_grow, phase)

    def _draw_gold_pile(surface, cx, cy, grow, phase):
        """Tumpukan koin emas (stamp ter-cache + shimmer)."""
        NS = _NS_alchemist
        P = NS.PALETTE
        pile_w = max(6, int(60 * grow))
        pile_h = max(2, int(12 * grow))
        key = "gold_pile_%d_%d" % (pile_w, pile_h)
        if key not in NS._STATIC_SURFACES:
            pile = pygame.Surface((pile_w + 8, pile_h + 8),
                                  pygame.SRCALPHA)
            NS._ellipse(pile, P["shadow_deep"],
                        (2, pile_h // 2 + 3, pile_w + 4, pile_h + 3))
            NS._ellipse(pile, P["gold_darkest"],
                        (3, 2, pile_w + 2, pile_h + 2))
            NS._ellipse(pile, P["gold_dark"],
                        (5, 3, pile_w - 2, pile_h))
            NS._ellipse(pile, P["gold_mid"],
                        (8, 4, max(4, pile_w - 8), max(2, pile_h - 4)))
            NS._ellipse(pile, P["gold_light"],
                        (10, 5, max(3, pile_w - 14),
                         max(1, pile_h - 8)))
            for i in range(max(3, pile_w // 8)):
                cxx = 6 + (i * 7) % max(1, pile_w - 4)
                cyy = 5 + (i * 3) % max(1, pile_h - 2)
                NS._aacircle(pile, P["gold_dark"], (cxx, cyy), 2)
                NS._aacircle(pile, P["gold_mid"], (cxx, cyy - 1), 1)
            NS._STATIC_SURFACES[key] = pile
            if len(NS._STATIC_SURFACES) > 96:
                for k in list(NS._STATIC_SURFACES):
                    if k.startswith("gold_pile"):
                        del NS._STATIC_SURFACES[k]
                        break
        spr = NS._STATIC_SURFACES[key]
        surface.blit(spr, (cx - spr.get_width() // 2,
                           cy - spr.get_height() + 4))
        # shimmer koin
        for i in range(3):
            t = (phase * 0.7 + i * 0.33) % 1.0
            sx = cx - pile_w // 2 + int(t * pile_w)
            a = int(200 * math.sin(t * math.pi))
            NS._aaline(surface, (*P["gold_shine"], a),
                       (sx, cy - 4), (sx, cy + 2), 1)

    def _draw_greevil_foreground(surface, boss, x, y, timer, phase):
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        NS = _NS_alchemist
        P = NS.PALETTE
        if not hasattr(boss, "_alch_coins"):
            boss._alch_coins = []
        # hujan koin (spawn selama 60% pertama)
        if progress < 0.6 and len(boss._alch_coins) < 26:
            for _ in range(2):
                NS._spawn_coin(boss,
                               x + (hash((id(boss), phase, len(
                                   boss._alch_coins))) % 120 - 60),
                               y - 10)
        coins = boss._alch_coins
        for c in coins:
            c["age"] += 1
            c["x"] += c["vx"]
            c["vy"] += 0.25
            c["y"] += c["vy"]
            c["spin"] += c["spin_speed"]
            if c["y"] > y + 54:
                c["y"] = y + 54
                c["vy"] = -abs(c["vy"]) * 0.4
                c["vx"] *= 0.7
        boss._alch_coins = [c for c in coins
                            if c["age"] < c["life"]]
        for c in boss._alch_coins:
            fade = 1.0 if c["age"] < c["life"] - 12 else \
                (c["life"] - c["age"]) / 12.0
            cw = max(1, int(abs(math.cos(c["spin"])) * 4) + 1)
            a = int(230 * fade)
            NS._ellipse(surface, (*P["gold_darkest"], a),
                        (int(c["x"]) - cw - 1, int(c["y"]) - 3,
                         cw * 2 + 2, 6))
            NS._ellipse(surface, (*P["gold_mid"], a),
                        (int(c["x"]) - cw, int(c["y"]) - 2,
                         cw * 2, 4))
            NS._aacircle(surface, (*P["gold_light"], a),
                         (int(c["x"]), int(c["y"])), max(1, cw - 1))
            if math.sin(c["spin"] * 3) > 0.7:
                NS._aacircle(surface, (*P["gold_shine"], a),
                             (int(c["x"]) - 1, int(c["y"]) - 1), 1)
        # kilau greed aura
        pul = 0.5 + 0.5 * math.sin(phase * 2.2)
        for radius in range(44, 18, -5):
            alpha = int((44 - radius) * 4 * pul)
            if alpha > 0:
                NS._aacircle(surface, (*P["gold_darkest"],
                                       min(200, alpha)),
                             (x, y - 8), radius)

    # ==================================================================
    # LAPISAN FX HIDUP  (heroes/alchemist_fx.py)
    # ==================================================================
    def _live_module():
        """Muat ``heroes.alchemist_fx`` sekali; None kalau gagal."""
        NS = _NS_alchemist
        if NS._LIVE_MOD is None:
            try:
                from heroes import alchemist_fx as mod
                NS._LIVE_MOD = mod if getattr(
                    mod, "ALCHEMIST_FX_ENABLED", True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    def live_fx_ready():
        """True kalau lapisan hidup Alchemist siap (dipakai tooling)."""
        return _NS_alchemist._live_module() is not None

    def _fx_owned(boss):
        """True kalau lapisan hidup sudah mengambil alih efek unit."""
        mod = _NS_alchemist._live_module()
        if mod is None:
            return False
        try:
            return bool(mod.owns(boss))
        except Exception:
            return False

    def _live_fx(boss, surface, x, y, want_draw, portrait):
        """Lapisan hidup untuk unit ini. Return (mod, owned)."""
        NS = _NS_alchemist
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
    # DEBUG OVERLAY  (DEBUG_CHARACTER = True)
    # ==================================================================
    def _draw_alch_debug(surface, boss, x, y, action, owned):
        """Hitbox, hurtbox, jangkauan, state/frame, FPS, partikel,
        skill state, timer serangan. Digambar PALING AKHIR; tidak
        pernah menyentuh gameplay."""
        NS = _NS_alchemist
        r = max(6, int(getattr(boss, "radius", 30) * 0.9))
        pygame.draw.rect(surface, (80, 170, 255, 150),
                         pygame.Rect(int(x) - r, int(y) - r - 10,
                                     r * 2, r * 2 + 18), 1)
        rng = max(10, int(getattr(boss, "range", 50) * 0.9))
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        pygame.draw.line(surface, (255, 210, 60, 150),
                         (int(x), int(y)),
                         (int(x + rng * f), int(y)), 1)
        pygame.draw.rect(surface, (255, 210, 60, 110),
                         pygame.Rect(int(x + rng * f) - 5,
                                     int(y) - 7, 10, 14), 1)
        hb = NS._swing_hitbox(boss, x, y)
        if hb is not None:
            pygame.draw.rect(surface, (255, 70, 70, 190), hb, 2)
            pygame.draw.rect(surface, (255, 70, 70, 60), hb)
        if owned:
            try:
                mod = NS._LIVE_MOD
                for p in mod.projectiles_for(boss):
                    rr = max(3, int(p.hit_radius))
                    pygame.draw.circle(surface, (255, 120, 255, 170),
                                       (int(p.x), int(p.y)), rr, 1)
            except Exception:
                pass
        fps = getattr(boss, "_alch_dbg_fps", None)
        if fps is None:
            try:
                import __main__
                game = getattr(__main__, "game_instance", None)
                fps = game.clock.get_fps() if game else 0.0
            except Exception:
                fps = 0.0
        lines = [
            "ALCHEMIST %s" % action,
            "state=%s/%s t=%.2fs" % (
                getattr(boss, "_alch_state", "?"),
                getattr(boss, "_alch_state_prev", "?"),
                float(getattr(boss, "_alch_state_time", 0.0))),
            "phase=%s ap=%.2f hit=%d" % (
                getattr(boss, "_alch_attack_phase", "NONE"),
                float(getattr(boss, "_alch_ap", 0.0)),
                1 if getattr(boss, "_alch_hit_active", False) else 0),
            "atk=%d/%d" % (int(getattr(boss, "timer", 0)),
                           int(getattr(boss, "attack_cooldown", 50))),
            "skill=%s t=%d rage=%s" % (
                getattr(boss, "active_skill", None),
                int(getattr(boss, "active_skill_timer", 0)),
                bool(getattr(boss, "rage_active", False))),
            "fps=%.0f live=%s" % (float(fps or 0.0),
                                  "y" if owned else "n"),
        ]
        if owned:
            try:
                mod = NS._LIVE_MOD
                d = getattr(boss, "_alch_fx", None)
                if d is not None:
                    lines.append("particles=%d proj=%d trail=%d" % (
                        d.particles.count(),
                        d.projectiles.count(),
                        len(d.trail.samples)))
            except Exception:
                pass
        try:
            # BUG: dulu `_debug_font()` (nama bebas). Di dalam kelas
            # namespace, nama itu TIDAK ada di scope fungsi maupun di
            # global modul -> NameError, dan panel teks debug tidak
            # pernah tampil (tertelan `except` di bawah). Harus lewat NS
            # seperti helper _NS_alchemist lainnya.
            font = NS._debug_font()
            if font is not None:
                for i, txt in enumerate(lines):
                    surface.blit(font.render(txt, True, (235, 240, 220)),
                                 (x - 60, y - 108 + i * 11))
        except Exception:
            pass

    _DEBUG_FONT = None

    def _debug_font():
        NS = _NS_alchemist
        if NS._DEBUG_FONT is None:
            try:
                NS._DEBUG_FONT = pygame.font.Font(None, 15)
            except Exception:
                NS._DEBUG_FONT = False
        return NS._DEBUG_FONT or None

    # ==================================================================
    # MAIN ENTRY
    # ==================================================================
    def draw_alchemist(surface, boss, x, y):
        """Entry point Boss.draw() sekaligus heroes.render_hero().

        Urutan lapisan (kontrak render order proyek):

            GROUND FX -> SHADOW -> BACK PARTICLES -> BODY/ARMOR/HEAD
            -> WEAPON -> ATTACK TRAIL -> PROJECTILE -> FRONT
            PARTICLES -> SKILL FX -> IMPACT FX -> DEBUG

        Trail, partikel, botol, impact, hit-stop & shake hidup di
        heroes/alchemist_fx.py (layar 1:1, luar sprite cache); kalau
        modul itu tidak ada, semua FX kembali ke canvas dari sini.
        """
        NS = _NS_alchemist
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = NS._detect_moving(boss)
        NS._update_attack_anim(boss)
        boss._alch_moving = moving
        _action, _phase, _ap = NS._resolve_pose(boss, moving)
        boss._alch_pose_action = _action
        portrait = bool(getattr(boss, "_portrait_hd", False))
        hero_lane = hasattr(boss, "_render_scale")

        attacking = (
            getattr(boss, "_alch_attack_active", False)
            or getattr(boss, "timer", 0) >
            getattr(boss, "attack_cooldown", 50) - 15
        )
        rage = bool(active_skill in ("e", "r")
                    or getattr(boss, "rage_active", False))

        # ── lapisan hidup: jalur boss digambar dari sini tiap frame;
        #    jalur lane dipicu heroes/__init__ (_LIVE_FX_HEROES) ──
        live, owned = NS._live_fx(boss, surface, x, y,
                                  not hero_lane, portrait)

        # ---------- Background layers ----------
        if not portrait:
            NS._draw_alch_aura(surface, x, y, pulse, active_skill)
            if not owned and hasattr(boss, "_alch_patches"):
                for patch in boss._alch_patches:
                    patch.draw(surface, pulse)
            NS._draw_ground_runes(surface, x, y + 52, pulse,
                                  active_skill)

            # telegraph skill (ground, world-space, ter-cache)
            if active_skill == "w":
                NS._draw_concoction_ground(surface, boss, x, y,
                                           skill_timer, pulse)
            elif active_skill == "r":
                NS._draw_greevil_ground(surface, boss, x, y,
                                        skill_timer, pulse)
            elif active_skill == "e":
                NS._draw_chem_rage_ground(surface, boss, x, y,
                                          skill_timer, pulse)

            # gelombang kejut aktivasi (12 frame pertama)
            if active_skill in ("q", "w", "e", "r") and not owned:
                dur = NS.SKILL_DUR[active_skill]
                age = dur - skill_timer
                if 0 <= age < 12:
                    c1 = (NS.PALETTE["gold_light"]
                          if active_skill == "r"
                          else NS.PALETTE["acid_hot"])
                    c2 = (NS.PALETTE["gold_mid"]
                          if active_skill == "r"
                          else NS.PALETTE["acid_bright"])
                    NS._draw_shockwave(
                        surface, x, y + 56, age, 12, c1, c2,
                        fs=NS._fx_scale(boss))

        # ---------- hurt flash: badan menyala, tanah tidak ----------
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        _tgt, _tx, _ty = surface, x, y
        if flash > 0:
            if NS._flash_buf is None:
                NS._flash_buf = pygame.Surface((NS.RIG_W, NS.RIG_H),
                                               pygame.SRCALPHA)
            NS._flash_buf.fill((0, 0, 0, 0))
            NS._record_shadow = []
            _tgt, _tx, _ty = NS._flash_buf, NS.RIG_OX, NS.RIG_OY

        # ---------- Character (pose dispatcher) ----------
        if attacking:
            NS._draw_alch_attack(_tgt, boss, _tx, _ty, rage=rage)
        elif active_skill == "q":
            NS._draw_alch_qcast(_tgt, boss, _tx, _ty, skill_timer,
                                rage=rage)
        elif active_skill == "w":
            NS._draw_alch_wcast(_tgt, boss, _tx, _ty, skill_timer,
                                rage=rage)
        elif active_skill == "e":
            NS._draw_alch_ecast(_tgt, boss, _tx, _ty, skill_timer,
                                rage=True)
        elif active_skill == "r":
            NS._draw_alch_rcast(_tgt, boss, _tx, _ty, skill_timer,
                                rage=True)
        elif moving:
            NS._draw_alch_walk(_tgt, boss, _tx, _ty, rage=rage)
        else:
            NS._draw_alch_idle(_tgt, boss, _tx, _ty, rage=rage)

        if flash > 0:
            surface.blit(NS._flash_buf, (x - _tx, y - _ty))
            w = int(235 * min(1.0, flash / 8.0))
            m = pygame.mask.from_surface(NS._flash_buf, 50)
            wht = m.to_surface(
                setcolor=(w, int(w * 0.9), int(w * 0.8), 255),
                unsetcolor=(0, 0, 0, 0))
            for rect in (NS._record_shadow or ()):
                wht.fill((0, 0, 0, 0), rect)
            surface.blit(wht, (x - _tx, y - _ty),
                         special_flags=pygame.BLEND_RGB_ADD)
            NS._record_shadow = None

        # ---------- Projectiles + foreground FX (canvas fallback) ---
        if not portrait:
            NS._manage_projectiles(boss, surface, pulse)
            if not owned:
                if active_skill == "q":
                    NS._draw_acid_spray(surface, boss, x, y,
                                        skill_timer, pulse)
                elif active_skill == "e":
                    NS._draw_chem_rage_foreground(
                        surface, boss, x, y, skill_timer, pulse)
                elif active_skill == "r":
                    NS._draw_greevil_foreground(
                        surface, boss, x, y, skill_timer, pulse)

        # ── lapisan hidup bagian ATAS (trail/projektil/impact) ──
        if live is not None:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass

        if NS.DEBUG_CHARACTER and not portrait:
            NS._draw_alch_debug(surface, boss, x, y,
                                getattr(boss, "_alch_pose_action",
                                        "?"), owned)

    def _draw_concoction_ground(surface, boss, x, y, timer, phase):
        """Telegraph W: cincin konvergen + zona AOE 100 px dunia."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        NS = _NS_alchemist
        P = NS.PALETTE
        tx, ty = NS._world_to_screen_target(boss, x, y)
        r = NS._ring_r(boss, NS.SKILL_RADIUS["w"], surface)
        fade = 1.0 if progress < 0.8 else \
            max(0.0, 1.0 - (progress - 0.8) / 0.2)
        NS._ground_ring(surface, tx, ty + 4, r,
                        P["acid_darkest"], P["acid_bright"],
                        int(190 * fade))
        NS._zone_fill(surface, tx, ty + 4, r, P["acid_darkest"],
                      int(70 * fade))
        # cincin konvergen (memberitahu "bom akan jatuh di sini")
        conv = 1.0 - min(1.0, progress / 0.45)
        if conv > 0:
            rr = int(6 + r * conv)
            NS._aacircle(surface, (*P["acid_hot"],
                                   int(210 * fade)),
                         (tx, ty + 2), rr)
        # penanda silang
        for sgn in (-1, 1):
            NS._aaline(surface, (*P["acid_bright"], int(160 * fade)),
                       (tx - 8, ty + 2 + sgn * 5),
                       (tx + 8, ty + 2 + sgn * 5), 1)

    # ===================================================================
    # Backward compatible alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_alchemist.draw_alchemist(surface, boss, x, y)


# ====================================================================
# ENTRY POINT PUBLIK (dipanggil base_boss.Boss.draw)
# ====================================================================

def draw_razak(surface, boss, x, y):
    """Entry point razak."""
    return _NS_razak.draw_razak(surface, boss, x, y)

def draw_khalros(surface, boss, x, y):
    """Entry point khalros."""
    return _NS_khalros.draw_khalros(surface, boss, x, y)

def draw_gorath(surface, boss, x, y):
    """Entry point gorath."""
    return _NS_gorath.draw_gorath(surface, boss, x, y)

def draw_alchemist(surface, boss, x, y):
    """Entry point alchemist."""
    return _NS_alchemist.draw_alchemist(surface, boss, x, y)
