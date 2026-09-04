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


# ====================================================================
# KHALROS — PIXEL MASTERWORK v2 (rewrite dari nol)
# ====================================================================
class _NS_khalros:
    """Namespace khalros - PIXEL MASTERWORK v2 + SKILL FX v2.1.

    Rewrite PENUH renderer `_NS_khalros` mengikuti standar
    **Thorne v2 Pixel Masterwork + v2.1 Skill FX** (docs/THORNE_V2_RENDERER.md),
    pola yang sama dengan `_NS_razak` / `_NS_gorath` di file ini. Tetap
    100% prosedural: tanpa PNG, sprite-sheet, maupun pemuatan citra.

    Karakter
    --------
    Khalros "The Beastlord" - panglima perang barbar penjinak binatang:
    dua kapak tempur bergerigi, helm bertanduk babi hutan, jubah kulit
    serigala, dan elang pendamping di bahu. Skill (sinkron dengan AI
    `bosses/base_boss.py::_khalros_*`):

        Q Wild Axes      50 frame, AOE 70 px dunia DI TARGET (voli kapak)
        W Call of Wild   60 frame, AOE 120 px dunia DI DIRI (pack howl+heal)
        E Boar Charge    45 frame, dash + AOE 85 px dunia DI DIRI (pendaratan)
        R Hawk Storm     70 frame, AOE 200 px dunia DI DIRI (hujan elang)

    Yang naik dibanding v1
    ----------------------
    1. RIG di-*author* 1.5x di resolusi NATIVE (puncak tanduk -100, sol
       sepatu +66) lalu ditampilkan lewat SATU `SCALE = 0.62` untuk semua
       jalur (boss langsung, lane hero, portrait). Ukuran DI LAYAR tetap
       sekelas keluarga level-2 (alchemist true boss >= khalros mini);
       yang berubah adalah KEPADATAN detail per piksel layar.
    2. DISIPLIN PIXEL-ART: 4-7 band ramp ber-hue-shift per material
       (kulit didorong dingin di bayangan / hangat di highlight, bulu
       serigala biru-kecil, baja kapak 5 band + fuller gelap), selout
       `shadow_deep` di (+facing, +1) tiap limb, outline hitam 1 px
       4 arah TERAKHIR (setelah penskalaan), siluet bergerigi lewat
       `_tuft_points` (hem jubah, bulu pauldron, janggut dikepang),
       specular cluster 2-3 px (helm, mata kapak, gesper emas, paruh
       elang), `_dither_dots` di transisi perut & membran sayap elang.
    3. ANIMASI: solver langkah dua kaki (heel-off -> contact -> toe-off,
       debu kontak), inersia sekunder jubah/rambut/ekor elang, idle hidup
       (napas, kedip elang, bara naik, binar mata), serangan 7 keyframe
       dengan frame IMPACT tersendiri di `ap = 0.54`.
    4. SKILL FX world-space (`_fx_scale`, cap 2.6) 3 tahap
       (AKTIVASI / STEADY / TELEGRAPH). FX tanah memakai DECAL ber-falloff
       (`_ground_scorch` + `_zone_fill` edge-weighted + `_ground_ring` +
       `_rune_ring`), bukan stroke vektor per-frame.
    """

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    # ── cache (nama lama dipertahankan) ─────────────────────────────
    _shadow_cache = None
    _aura_cache = None
    _rune_cache = None
    _flash_buf = None
    _record_shadow = None
    _body_buf = None        # buffer badan untuk outline+lighting
    _ghost_buf = None       # afterimage dash (dirender 1x, di-blit 4x)
    _STATIC_SURFACES = {}   # surface statis: dibangun SEKALI, di-blit
    _EMBER_CACHE = {}       # api/bara per (size, fase-bucket, alpha)
    _PILLAR_CACHE = {}      # kolom angin/debu vertikal
    _BEAST_CACHE = {}       # siluet boar / wolf / hawk yang di-cache
    _CLAMP_MEMO = {}

    # ── metrik rig v2 ───────────────────────────────────────────────
    RIG_SCALE = 1.5
    # Buffer badan dibatasi extents TERUKUR semua pose (idle/walk/attack
    # 7 keyframe/charge, dua arah hadap) + margin smear kapak.
    RIG_W, RIG_H = 210, 192
    RIG_OX, RIG_OY = 105, 112

    # Satu SCALE untuk SEMUA jalur (boss langsung, lane hero, portrait).
    # PERINGATAN: jangan pisahkan SCALE per jalur - itu merusak
    # normalisasi _measure_native_size di heroes/__init__.py.
    #
    # Kenapa 0.68, bukan 0.62 seperti razak/gorath/alchemist: mereka membeli
    # lebar siluet dari sayap api / kolom kabut / totem sehingga body-only
    # boleh lebih kecil. Khalros berdiri di tanah dengan dua kapak - tanpa
    # pembentang siluet - jadi faktor tampilnya dinaikkan supaya bbox DI
    # LAYAR setara keluarga (razak 96x107, gorath 112x98, khalros ~100x115)
    # dan tetap di bawah alchemist (130x133). Tetap SATU angka untuk SEMUA
    # jalur (boss, lane hero, portrait) - dan itu yang dijaga normalisasi.
    SCALE = 0.68
    # Garis tanah (sol sepatu native +66 -> layar) relatif jangkar badan.
    GROUND_DY = 44

    # Durasi visual skill (frame) - HARUS sama dengan active_skill_timer
    # yang diisi AI di bosses/base_boss.py (_khalros_q/w/e/r).
    SKILL_DUR = {"q": 50, "w": 60, "e": 45, "r": 70}

    # Radius gameplay tiap skill dalam PX DUNIA (bosses/base_boss.py):
    #   q -> AOE 70 di target, w -> AOE 120 di sekitar DIRI,
    #   e -> AOE 85 setelah dash, r -> AOE 200 di sekitar DIRI.
    # Telegraph digambar TEPAT di angka ini lewat `_ring_r`.
    SKILL_RADIUS = {"q": 70, "w": 120, "e": 85, "r": 200}

    # ── controller animasi (dipakai juga oleh heroes/khalros_fx.py) ──
    #: Overlay debug hitbox/hurtbox/state - sama seperti karakter v3 lain.
    DEBUG_CHARACTER = False

    ANIM_PRIORITY = {
        "IDLE": 10, "WALK": 20, "RUN": 25, "CHARGE": 40,
        "ATTACK": 45, "SWING": 50, "CAST": 55, "SKILL": 56,
        "SPECIAL": 60, "HIT": 62, "HURT": 65, "DEATH": 100,
    }

    #: Timeline serangan (fraksi progress 0..1). Fase ini dipakai
    #: renderer DAN lapisan hidup - satu sumber kebenaran.
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

    #: Geometri kapak (ruang native rig; dipakai swing trail & hitbox).
    AXE_HANDLE = 24
    AXE_BLADE = 27
    AXE_ARM_LEN = 17

    # ---------------------------------------------------------------------------
    # HD Palette v2 - rustic barbarian: kulit tan, baja, bulu, api primal.
    # Semua kunci v1 dipertahankan (nilainya di-tuning dengan hue-shift)
    # + kunci baru untuk rim, debu, asap, tulang, dan angin.
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Kulit barbar - bayangan didorong ungu-dingin, highlight kuning-hangat
        "skin_darkest":   (38,  20,  20),
        "skin_dark":      (102, 60,  40),
        "skin_mid":       (168, 106, 66),
        "skin_light":     (214, 156, 104),
        "skin_high":      (242, 200, 152),
        "skin_shine":     (255, 232, 196),
        "skin_rim":       (255, 244, 216),

        # Rambut & janggut - cokelat tua (merah di highlight)
        "hair_darkest":   (16,  11,   9),
        "hair_dark":      (44,  29,  20),
        "hair_mid":       (82,  54,  34),
        "hair_light":     (124, 84,  52),
        "hair_high":      (168, 122, 74),

        # Kulit samak / tali
        "leather_darkest": (22,  14,   9),
        "leather_dark":   (52,  32,  16),
        "leather_mid":    (92,  60,  31),
        "leather_light":  (146, 98,  54),
        "leather_high":   (196, 145, 86),

        # Baja kapak & helm (bayangan kebiruan, highlight hangat-sedikit)
        "metal_darkest":  (16,  14,  19),
        "metal_dark":     (48,  45,  54),
        "metal_mid":      (102, 98, 110),
        "metal_light":    (168, 164, 178),
        "metal_shine":    (226, 224, 232),
        "metal_edge":     (250, 248, 252),

        # Emas (gesper, rivet, cincin elang)
        "gold_dark":      (92,  62,  16),
        "gold_mid":       (172, 128, 40),
        "gold_light":     (232, 190, 82),
        "gold_shine":     (255, 232, 152),

        # Api primal / aura beastlord
        "fire_darkest":   (62,  16,   5),
        "fire_dark":      (138, 34,   8),
        "fire_mid":       (212, 78,  15),
        "fire_bright":    (252, 132, 32),
        "fire_hot":       (255, 184, 66),
        "fire_glow":      (255, 222, 136),
        "fire_white":     (255, 248, 214),

        # War paint merah-oker
        "red_dark":       (78,  14,  12),
        "red_mid":        (166, 32,  26),
        "red_bright":     (224, 58,  46),
        "red_hot":        (255, 108, 84),

        # Bulu babi hutan (pauldron / taring)
        "boar_darkest":   (26,  16,  12),
        "boar_dark":      (62,  38,  22),
        "boar_mid":       (108, 70,  41),
        "boar_light":     (158, 108, 66),
        "boar_high":      (204, 154, 102),

        # Kulit serigala (jubah) - abu kebiruan dingin
        "wolf_darkest":   (20,  20,  28),
        "wolf_dark":      (48,  48,  60),
        "wolf_mid":       (90,  90, 104),
        "wolf_light":     (146, 146, 160),
        "wolf_high":      (200, 202, 214),
        "wolf_rim":       (228, 234, 248),

        # Elang pendamping / badai elang
        "hawk_darkest":   (26,  17,  12),
        "hawk_dark":      (62,  40,  22),
        "hawk_mid":       (118, 76,  42),
        "hawk_light":     (174, 126, 78),
        "hawk_high":      (224, 180, 132),
        "hawk_beak":      (246, 210, 102),

        # Tulang (taring, kalung, gagang)
        "bone_darkest":   (44,  38,  30),
        "bone_dark":      (108, 94,  70),
        "bone_mid":       (168, 152, 118),
        "bone_light":     (222, 212, 178),
        "bone_shine":     (248, 242, 222),

        # Debu tanah / asap / angin (FX binatang)
        "dust_dark":      (72,  56,  38),
        "dust_mid":       (126, 100, 68),
        "dust_light":     (186, 160, 122),
        "smoke_dark":     (34,  28,  30),
        "smoke_mid":      (72,  62,  60),
        "wind_dark":      (34,  52,  62),
        "wind_mid":       (86, 130, 146),
        "wind_light":     (160, 210, 224),
        "wind_shine":     (220, 246, 255),

        # Mata menyala (primal)
        "eye_dark":       (74,  20,   6),
        "eye_bright":     (255, 214,  96),
        "eye_hot":        (255, 250, 208),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (5,   3,   3),
        "white":          (255, 255, 255),
    }

    # ===================================================================
    # PRIMITIF DASAR (standar keluarga masterwork)
    # ===================================================================
    def _static(key, builder):
        """Surface statis ter-cache (dibangun sekali, dipakai ulang)."""
        surf = _NS_khalros._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_khalros._STATIC_SURFACES[key] = surf
        return surf

    def _clamp(color):
        """Clamp channel warna (RGB/RGBA) - di-memo, dipanggil ribuan kali."""
        try:
            hit = _NS_khalros._CLAMP_MEMO.get(color)
        except TypeError:
            return tuple(max(0, min(255, int(c))) for c in color)
        if hit is not None:
            return hit
        out = tuple(max(0, min(255, int(c))) for c in color)
        memo = _NS_khalros._CLAMP_MEMO
        if len(memo) > 8192:
            memo.clear()
        memo[color] = out
        return out

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _mix(a, b, t):
        """Blend linear dua warna palette (t=0 -> a, t=1 -> b)."""
        t = max(0.0, min(1.0, t))
        return _NS_khalros._clamp(
            (a[0] + (b[0] - a[0]) * t,
             a[1] + (b[1] - a[1]) * t,
             a[2] + (b[2] - a[2]) * t))

    def _hash01(i):
        """Pseudo-random deterministik 0..1 (stabil antar frame & cache)."""
        x = math.sin(i * 127.1 + 311.7) * 43758.5453
        return x - math.floor(x)

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_khalros._clamp(color)
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
        if _NS_khalros.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius,
                                     width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_khalros._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        width = int(width)
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
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey),
                         max(1, width))

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_khalros._clamp(color)
        if any(isinstance(v, float) for p in points for v in p[:2]):
            points = [(int(p[0]), int(p[1])) for p in points]
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
        color = _NS_khalros._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4),
                                  pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, int(rw), int(rh)), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3],
                            (rect[0], rect[1], int(rect[2]), int(rect[3])),
                            width)

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

    def _ring(surface, center, radius, width, color, alpha):
        """Cincin: stroke gelap di belakang + cincin terang di atas."""
        alpha = _NS_khalros._alpha(alpha)
        if alpha <= 0:
            return
        cx, cy = int(center[0]), int(center[1])
        r = int(radius)
        if r <= 0:
            return
        _NS_khalros._aacircle(surface, (6, 3, 3, alpha), (cx, cy), r + 1,
                              max(1, width + 2))
        _NS_khalros._aacircle(surface, (*color, alpha), (cx, cy), r,
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
        """Pusat jangkar target dalam ruang gambar renderer.

        Hero/boss digambar ke canvas offscreen lalu di-scale saat blit,
        jadi titik canvas = (delta dunia) / scale supaya FX mendarat
        TEPAT di target setelah blit. Boss langsung: scale = 1.
        """
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return (int(x + 190 / float(getattr(boss, "_render_scale", 1.0) or 1.0)
                    * getattr(boss, "direction", 1)), int(y))

    # ===================================================================
    # SKILL FX PRIMITIVES (standar Thorne v2.1 - kosakata keluarga)
    # ===================================================================
    def _fx_scale(boss):
        """Faktor skala efek skill (world-space), cap 2.6.

        Unit lane dirender ke canvas lalu dikecilkan `_render_scale` saat
        blit -> efek ikut menyusut. Dengan 1/_render_scale ukuran EFEK DI
        LAYAR setara boss asli. Boss langsung = 1.0.
        """
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

    def _spark_star(surface, cx, cy, size, color, alpha, spikes=6, rot=0.4,
                    core=None):
        """Bintang kilat: spike panjang-pendek selang-seling + inti."""
        alpha = _NS_khalros._alpha(alpha)
        if alpha <= 0 or size <= 0:
            return
        for k in range(spikes):
            ang = rot + k * math.pi * 2 / spikes
            ln = size * (1.0 if k % 2 == 0 else 0.55)
            _NS_khalros._aaline(surface, (*color, alpha), (int(cx), int(cy)),
                                 (int(cx + math.cos(ang) * ln),
                                  int(cy + math.sin(ang) * ln * .8)),
                                 2 if k % 2 == 0 else 1)
        if core:
            _NS_khalros._aacircle(surface, (*core, alpha), (int(cx), int(cy)),
                                  max(1, int(size * .3)))

    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        """Satu panah '>' menghadap arah ``ang`` (telegraph bergerak)."""
        alpha = _NS_khalros._alpha(alpha)
        if alpha <= 0 or size <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        tipx, tipy = cx + ca * size, cy + sa * size
        for s in (-1, 1):
            _NS_khalros._aaline(
                surface, (*color, alpha),
                (int(cx + px * s * size * .55 - ca * size * .5),
                 int(cy + py * s * size * .55 - sa * size * .5)),
                (int(tipx), int(tipy)), width)

    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=10, thick=3, span=0.6, squash=.92):
        """Cincin putus-putus berputar (marker AOE / rune ring)."""
        alpha = _NS_khalros._alpha(alpha)
        if alpha <= 0 or radius <= 1:
            return
        for i in range(segments):
            a0 = phase + i * math.pi * 2 / segments
            a1 = a0 + math.pi * 2 / segments * span
            p0 = (cx + math.cos(a0) * radius,
                  cy + math.sin(a0) * radius * squash)
            p1 = (cx + math.cos(a1) * radius,
                  cy + math.sin(a1) * radius * squash)
            _NS_khalros._aaline(surface, (*color, alpha), p0, p1, thick)

    def _wind_sweep(surface, cx, cy, radius, alpha, phase, arcs=3,
                    color=None, core=None):
        """Sapuan angin melengkung (pernafasan badai elang)."""
        P = _NS_khalros.PALETTE
        color = color or P["wind_light"]
        core = core or P["wind_shine"]
        alpha = _NS_khalros._alpha(alpha)
        if alpha <= 0:
            return
        for k in range(arcs):
            rr = int(radius * (0.55 + 0.22 * k))
            base = phase * (1.4 + 0.3 * k) + k * 2.1
            pts = []
            for i in range(9):
                t = i / 8.0
                ang = base + t * math.pi * 1.15
                pts.append((cx + math.cos(ang) * rr,
                            cy + math.sin(ang) * rr * 0.5))
            for i in range(len(pts) - 1):
                taper = max(1, int(3 * (1 - abs(i - 4) / 5.0)))
                _NS_khalros._aaline(surface, (*color, int(alpha * 0.75)),
                                    pts[i], pts[i + 1], taper + 1)
                _NS_khalros._aaline(surface, (*core, alpha), pts[i],
                                    pts[i + 1], max(1, taper - 1))

    # -------------------------------------------------------------------
    # DECAL TANAH (dibangun sekali per (radius, gaya); LRU 48)
    # -------------------------------------------------------------------
    _DECAL_CACHE = {}
    _DECAL_ORDER = []

    def _decal(key, size, builder):
        """Surface decal ter-cache; LRU sederhana supaya memori terbatas."""
        hit = _NS_khalros._DECAL_CACHE.get(key)
        if hit is not None:
            return hit
        surf = builder(max(4, int(size)))
        _NS_khalros._DECAL_CACHE[key] = surf
        _NS_khalros._DECAL_ORDER.append(key)
        if len(_NS_khalros._DECAL_ORDER) > 48:
            old = _NS_khalros._DECAL_ORDER.pop(0)
            _NS_khalros._DECAL_CACHE.pop(old, None)
        return surf

    def _decal_alpha(alpha):
        """Bucket alpha 16-step untuk kunci decal (cache tetap panas).

        Dikuantisasi supaya variasi cache sedikit (LRU 48) dan tiap varian
        dibangun sekali; hasilnya dipanggang ke decal lewat `_bake` - RGB
        untuk jalur additive, kanal alpha untuk jalur normal.
        """
        a = _NS_khalros._alpha(alpha)
        if a <= 0:
            return 0
        return max(16, min(255, (a + 15) // 16 * 16))

    def _premul(color, a):
        """Warna yang RGB-nya sudah dikalikan alpha - WAJIB untuk decal additive.

        `BLEND_RGBA_ADD` di SDL menjumlahkan kanal RGB mentah dan MENGABAIKAN
        alpha sumber (verifikasi di pygame-ce 2.5.8: surface SRCALPHA dengan
        `set_alpha(40)` yang di-blit additive tetap menyumbang RGB penuh).
        Decal yang dipakai additive karenanya harus menyimpan cahayanya DI
        RGB - kalau tidak, tiap "glow" jadi piringan keras secerah warna
        aslinya dan tiga lapis tumpangan langsung putus ke putih.
        """
        k = max(0, min(255, int(a))) / 255.0
        return (int(color[0] * k), int(color[1] * k), int(color[2] * k))

    def _bake(surf, alpha, add=False):
        """Skala decal dengan alpha bucket (sekali per build, lalu di-cache).

        add=True  -> RGB yang diskala (alpha sumber toh diabaikan SDL)
        add=False -> kanal alpha yang diskala (jalur blit normal)
        """
        if alpha >= 255:
            return surf
        if add:
            surf.fill((alpha, alpha, alpha, 255),
                      special_flags=pygame.BLEND_RGBA_MULT)
        else:
            surf.fill((255, 255, 255, alpha),
                      special_flags=pygame.BLEND_RGBA_MULT)
        return surf

    def _blit_decal(surface, decal, cx, cy, alpha=255, add=False):
        """Blit decal ter-pusat di (cx, cy).

        `alpha` hanya berlaku untuk jalur NORMAL (SDL menghormati
        `set_alpha` di sana). Decal additive membawa cahayanya sendiri di
        RGB - lihat `_premul` - jadi pemanggil additive mengirim 255 dan
        mengandalkan `_bake`.
        """
        alpha = _NS_khalros._alpha(alpha)
        if alpha <= 0:
            return
        w, h = decal.get_size()
        if not add:
            decal.set_alpha(alpha)
        surface.blit(decal, (int(cx) - w // 2, int(cy) - h // 2),
                     special_flags=pygame.BLEND_RGBA_ADD if add else 0)
        if not add:
            decal.set_alpha(255)

    def _quantize(v, step=6):
        """Bulatkan radius ke kelipatan `step` supaya decal cache nyangkut."""
        return max(step, int(round(float(v) / step) * step))

    def _build_falloff_ring(size, color, core, thickness, softness,
                            inner_glow, add=False):
        """Cincin ber-gradien: inti terang -> falloff halus ke luar.

        `add=True` menuntut warna premultiplied (lihat `_premul`) - cincin
        telegraph yang di-blit additive dengan RGB mentah langsung terlihat
        seperti neon yang terbakar habis.
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
                t = t * t
            if t <= 0.003:
                continue
            a = int(200 * t)
            col = _NS_khalros._mix(color, core,
                                   min(1.0, max(0.0, t - 0.45) * 1.5))
            if add:
                col = _NS_khalros._premul(col, a)
            pygame.draw.circle(surf, (*col, a), (c, c), r, 1)
        if inner_glow > 0:
            for r in range(lo, 0, -2):
                t = (r / float(max(1, lo))) ** 2
                a = int(inner_glow * t)
                if a > 1:
                    col = _NS_khalros._premul(color, a) if add else color
                    pygame.draw.circle(surf, (*col, a), (c, c), r, 2)
        return surf

    def _ground_ring(surface, cx, cy, radius, color, core, alpha,
                     thickness=3, softness=7, inner_glow=0, add=True):
        """Cincin AOE kelas produksi: decal ber-falloff, additive."""
        radius = _NS_khalros._quantize(radius, 6)
        ab = _NS_khalros._decal_alpha(alpha)
        if radius < 6 or ab <= 0:
            return
        pad = softness + thickness + 3
        size = radius * 2 + pad * 2
        key = ("fring", radius, color, core, thickness, softness, inner_glow,
               ab, add)
        decal = _NS_khalros._decal(
            key, size,
            lambda n: _NS_khalros._bake(
                _NS_khalros._build_falloff_ring(
                    n, color, core, thickness, softness, inner_glow, add), ab,
                add=add))
        _NS_khalros._blit_decal(surface, decal, cx, cy, 255, add=add)


    def _build_arc_ring(size, color, core, segments, span, thickness,
                        softness, taper, add=False):
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
                w = thickness * (taper + (1 - taper) * math.sin(t * math.pi))
                outer.append((c + math.cos(ang) * (r_nom + w * .5),
                              c + math.sin(ang) * (r_nom + w * .5)))
                inner.append((c + math.cos(ang) * (r_nom - w * .5),
                              c + math.sin(ang) * (r_nom - w * .5)))
            pts = outer + inner[::-1]
            ca, cb = 150, 205
            if add:
                col_a = _NS_khalros._premul(color, ca)
                col_b = _NS_khalros._premul(core, cb)
            else:
                col_a, col_b = color, core
            pygame.draw.polygon(surf, (*col_a, ca), pts)
            mid = [(c + (px - c) * .997, c + (py - c) * .997)
                   for px, py in outer[1:-1]] + \
                  [(c + (px - c) * 1.003, c + (py - c) * 1.003)
                   for px, py in inner[1:-1]][::-1]
            if len(mid) >= 3:
                pygame.draw.polygon(surf, (*col_b, cb), mid)
        return surf

    def _rune_ring(surface, cx, cy, radius, color, core, alpha, spin,
                   segments=12, span=0.42, thickness=3.0, taper=0.85,
                   add=True):
        """Cincin busur berputar (telegraph 'rune binatang terbakar').

        Geometri decal TIDAK dibangun ulang per frame - hanya sudutnya:
        decal ter-cache diputar dengan `transform.rotate` dan sudutnya
        dikunci ke dalam satu pitch segmen (`% 360/segments`), karena
        cincin dengan `segments` segmen identik berulang tiap pitch, jadi
        sisa sudut di luar satu pitch tidak menambah apa-apa.

        Kenapa hasil rotasi TIDAK di-cache (pernah dicoba, jangan diulang):
        kuncinya (radius x bucket sudut) menghasilkan 227 surface 400-580 px
        = ~105 MB per kelas boss (razak/gorath: 0.03 MB), sementara `rotate`
        cuma 0.4-0.6 ms dan masih di dalam budget. Kalau rotasi mau di-cache
        lagi, batasi BYTE, bukan jumlah entri.
        """
        radius = _NS_khalros._coarse(radius)
        ab = _NS_khalros._decal_alpha(alpha)
        if radius < 8 or ab <= 0:
            return
        pad = int(thickness) + 8
        size = radius * 2 + pad * 2
        key = ("arcring", radius, color, core, segments, round(span, 2),
               round(thickness, 1), round(taper, 2), ab, add)
        decal = _NS_khalros._decal(
            key, size,
            lambda n: _NS_khalros._bake(
                _NS_khalros._build_arc_ring(
                    n, color, core, segments, span, thickness, 6, taper,
                    add), ab, add=add))
        deg = -math.degrees(spin) % (360.0 / max(1, segments))
        rot = pygame.transform.rotate(decal, deg)
        _NS_khalros._blit_decal(surface, rot, cx, cy, 255, add=True)


    def _build_scorch(size, color, edge, seed):
        """Noda tanah: gumpalan lembut ber-tepi tidak beraturan."""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        r = c - 2
        for i in range(r, 0, -2):
            t = 1.0 - i / float(r)
            a = int(120 * (t ** 1.6))
            if a > 1:
                col = _NS_khalros._mix(edge, color, t)
                pygame.draw.circle(surf, (*col, a), (c, c), i)
        for i in range(20):
            ang = _NS_khalros._hash01(seed * 31 + i) * math.tau
            rr = r * (0.80 + 0.16 * _NS_khalros._hash01(seed * 17 + i))
            br = max(3, int(r * 0.15 * (0.5 + _NS_khalros._hash01(seed * 7 + i))))
            bx = int(c + math.cos(ang) * rr)
            by = int(c + math.sin(ang) * rr)
            for k in range(br, 0, -1):
                a = int(70 * (1.0 - k / float(br)) ** 1.5)
                if a > 1:
                    pygame.draw.circle(surf, (*edge, a), (bx, by), k)
        return surf

    def _coarse(v):
        """Kuantisasi radius BESAR lebih kasar (1/14 jangkauan, min 10 px).

        Telegraph yang tumbuh mengikuti `progress` menghasilkan radius baru
        tiap frame; dengan step tetap 8-10 px satu cast menghasilkan 40+
        varian decal - LRU 48 jadi thrashing dan tiap frame membangun ulang
        piringan 400-600 px. Untuk alas selebar itu, 20 px perbedaan tidak
        terlihat, tapi 3x lebih sedikit build terasa di FPS.
        """
        return _NS_khalros._quantize(v, max(10, int(v) // 14))

    def _ground_scorch(surface, cx, cy, radius, color, edge, alpha, seed=1):
        """Alas tanah ter-cache di bawah telegraph (menempel di lantai)."""
        radius = _NS_khalros._coarse(radius)
        ab = _NS_khalros._decal_alpha(alpha)
        if radius < 8 or ab <= 0:
            return
        size = radius * 2 + 6
        key = ("scorch", radius, color, edge, seed, ab)
        decal = _NS_khalros._decal(
            key, size,
            lambda n: _NS_khalros._bake(
                _NS_khalros._build_scorch(n, color, edge, seed), ab))
        _NS_khalros._blit_decal(surface, decal, cx, cy, 255)


    def _build_zone_fill(size, color, edge_bias, add=False):
        """Isi zona AOE: paling pekat DI DEKAT TEPI, memudar ke tengah.

        Digambar sebagai annulus 1 px dari luar ke dalam supaya tiap piksel
        ditulis SATU kali: tanpa akumulasi blend, kurva falloff yang
        dirancang = yang sampai ke layar.
        """
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        r = c - 1
        for i in range(r, 0, -1):
            t = i / float(r)
            a = int(115 * (t ** edge_bias))
            if a > 1:
                col = _NS_khalros._premul(color, a) if add else color
                pygame.draw.circle(surf, (*col, a), (c, c), i, 1)
        return surf

    def _zone_fill(surface, cx, cy, radius, color, alpha, edge_bias=3.2,
                   add=True):
        """Wash zona AOE ter-cache (edge-weighted; lihat builder-nya)."""
        radius = _NS_khalros._coarse(radius)
        ab = _NS_khalros._decal_alpha(alpha)
        if radius < 6 or ab <= 0:
            return
        decal = _NS_khalros._decal(
            ("zone", radius, color, round(edge_bias, 1), ab, add),
            radius * 2,
            lambda n: _NS_khalros._bake(
                _NS_khalros._build_zone_fill(n, color, edge_bias, add), ab,
                add=add))
        _NS_khalros._blit_decal(surface, decal, cx, cy, 255, add=add)


    def _build_radial_grad(size, color, add=False):
        """Gradien radial lembut (glow / dasar kolom).

        Annulus 1 px + warna premultiplied untuk mode additive: glow harus
        memudar di RGB, bukan hanya di alpha.
        """
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        for i in range(c, 0, -1):
            t = 1.0 - i / float(c)
            a = int(190 * (t ** 2.2))
            if a > 1:
                col = _NS_khalros._premul(color, a) if add else color
                pygame.draw.circle(surf, (*col, a), (c, c), i, 1)
        return surf

    def _glow(surface, cx, cy, radius, color, alpha, add=True):
        """Glow radial ter-cache (pengganti tumpukan `_aacircle`)."""
        radius = _NS_khalros._coarse(radius)
        ab = _NS_khalros._decal_alpha(alpha)
        if radius < 4 or ab <= 0:
            return
        decal = _NS_khalros._decal(
            ("glow", radius, color, ab, add), radius * 2,
            lambda n: _NS_khalros._bake(
                _NS_khalros._build_radial_grad(n, color, add), ab, add=add))
        _NS_khalros._blit_decal(surface, decal, cx, cy, 255, add=add)


    def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                      width=3):
        """Retakan tanah berzigzag (3 segmen) dengan seam menyala."""
        alpha = _NS_khalros._alpha(alpha)
        if alpha <= 0 or length <= 0:
            return
        x, y, a = cx, cy, ang
        pts = [(x, y)]
        for i in range(3):
            a += (_NS_khalros._hash01(seed * 7 + i * 13) - .5) * .8
            seg = length / 3.0
            x += math.cos(a) * seg
            y += math.sin(a) * seg * .55      # perspektif tanah
            pts.append((x, y))
        for i in range(len(pts) - 1):
            _NS_khalros._aaline(surface, (*colors[0], alpha), pts[i],
                                pts[i + 1], width + 2)
            _NS_khalros._aaline(surface, (*colors[1], alpha), pts[i],
                                pts[i + 1], width)

    def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
        """Ubah spine halus jadi tepi bergerigi (kain robek / bulu).

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
                d = depth * (0.55 + 0.45 * _NS_khalros._hash01(
                    i * 7 + j * 13 + seed))
                if j % 2 == 0:
                    out.append((px + nx * d, py + ny * d))
                else:
                    out.append((px - nx * d * 0.45, py - ny * d * 0.45))
            out.append((bx, by))
        return out

    def _dither_dots(surface, color, points, alpha=80):
        """Dither band 50% klasik (bertahan setelah downscale)."""
        col = (*color, _NS_khalros._alpha(alpha))
        for i, (px, py) in enumerate(points):
            if i % 2 == 0:
                _NS_khalros._aacircle(surface, col, (int(px), int(py)), 1)

    def _selout_poly(surface, color, points, facing=1, dy=1, off=1):
        """Selout: salinan warna gelap digeser ke sisi bayangan (kanan-bawah)."""
        _NS_khalros._poly(surface, color,
                          [(p[0] + facing * off, p[1] + dy) for p in points])

    # ===================================================================
    # API / FLAME / DEBU (nama lama dipertahankan, versi v2 lebih hemat)
    # ===================================================================
    def _draw_flame(surface, cx, cy, size, phase, alpha=255):
        """Api tunggal ber-lapis; di-cache per (size, fase, alpha bucket)."""
        NS = _NS_khalros
        height = int(size * 2)
        pb = int(phase * 4) % 8
        ab = int(alpha / 32) * 32
        key = (int(size), pb, ab)
        spr = NS._EMBER_CACHE.get(("flame",) + key)
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
            if len(NS._EMBER_CACHE) > 192:
                NS._EMBER_CACHE.clear()
            NS._EMBER_CACHE[("flame",) + key] = spr
        surface.blit(spr, (cx - (spr.get_width() // 2), cy - (height + 1)))

    def _draw_ember(surface, cx, cy, size=2, alpha=255):
        """Bara 3-band + inti putih (murah, tanpa alokasi)."""
        NS = _NS_khalros
        P = NS.PALETTE
        size = max(1, int(size))
        NS._aacircle(surface, (*P["fire_dark"], alpha), (cx, cy), size + 1)
        NS._aacircle(surface, (*P["fire_bright"], alpha), (cx, cy), size)
        NS._aacircle(surface, (*P["fire_hot"], alpha), (cx, cy),
                     max(1, size - 1))
        NS._aacircle(surface, (*P["fire_glow"], min(255, alpha)), (cx, cy), 1)

    def _draw_dust_puff(surface, cx, cy, radius, alpha, seed=0):
        """Debu tanah kontak kaki - gumpalan 3-tone, tanpa surface baru."""
        NS = _NS_khalros
        P = NS.PALETTE
        alpha = NS._alpha(alpha)
        if alpha <= 8 or radius <= 0:
            return
        for i in range(4):
            ang = NS._hash01(seed * 13 + i * 5) * math.tau
            rr = radius * (0.35 + 0.65 * NS._hash01(seed * 7 + i))
            px = cx + math.cos(ang) * radius * 0.8
            py = cy + math.sin(ang) * radius * 0.28
            sz = max(1, int(rr))
            NS._aacircle(surface, (*P["dust_dark"], int(alpha * 0.55)),
                         (int(px), int(py)), sz)
            NS._aacircle(surface, (*P["dust_mid"], int(alpha * 0.7)),
                         (int(px) - 1, int(py) - 1), max(1, sz - 1))
            NS._aacircle(surface, (*P["dust_light"], int(alpha * 0.5)),
                         (int(px) - 1, int(py) - 2), max(1, sz // 2))

    def _draw_wind_column(surface, cx, cy, height, width, phase):
        """Kolom angin vertikal ter-cache (aktivasi R / pilar panggilan).

        Pengganti tumpukan `aacircle` ber-alpha per frame. Sway dikunci
        ke 6 bucket fase; tinggi dikuantisasi 4 px supaya cache nyangkut.
        """
        NS = _NS_khalros
        P = NS.PALETTE
        height = max(6, int(height))
        width = max(2, int(width))
        hq = (height // 4) * 4
        pb = int(phase * 3) % 6
        key = ("col", hq, width, pb)
        spr = NS._PILLAR_CACHE.get(key)
        if spr is None:
            w_s = width * 2 + 10
            spr = pygame.Surface((w_s, hq + 8), pygame.SRCALPHA)
            base_x = w_s // 2
            for h in range(0, hq, 2):
                t = h / max(1, hq)
                w = max(1, int(width * (1 - t * 0.45)))
                fxp = base_x + int(math.sin(pb * 1.05 + h * 0.32) * 3)
                fyp = hq + 2 - h
                alpha = int(210 * (1 - t * 0.55))
                if t < 0.3:
                    color = P["wind_dark"]
                elif t < 0.62:
                    color = P["wind_mid"]
                elif t < 0.86:
                    color = P["wind_light"]
                else:
                    color = P["wind_shine"]
                pygame.draw.circle(spr, (*color, alpha), (fxp, fyp), w)
            # serat angin naik di dalam kolom
            for i in range(6):
                t = (i + 0.5) / 6.0
                yy = hq + 2 - int(t * hq)
                xx = base_x + int(math.sin(pb + i * 1.4) * width * 0.6)
                NS._aaline(spr, (*P["wind_shine"], int(150 * (1 - t))),
                           (xx - width, yy), (xx + width, yy - 2), 1)
            if len(NS._PILLAR_CACHE) > 96:
                NS._PILLAR_CACHE.clear()
            NS._PILLAR_CACHE[key] = spr
        surface.blit(spr, (int(cx) - spr.get_width() // 2,
                           int(cy) + 2 - spr.get_height()))

    # -------------------------------------------------------------------
    # BINATANG (siluet ter-cache per (jenis, facing, bucket fase, ukuran))
    # -------------------------------------------------------------------
    def _beast(kind, facing, phase, size, alpha, palette):
        """Ambil sprite binatang ter-cache; dibangun sekali per kunci."""
        NS = _NS_khalros
        f = 1 if facing >= 0 else -1
        pb = int(phase * 3) % 8
        sb = max(4, int(size / 3) * 3)
        ab = int(alpha / 32) * 32
        key = (kind, f, pb, sb, ab)
        spr = NS._BEAST_CACHE.get(key)
        if spr is None:
            w = int(sb * 5.2) + 8
            h = int(sb * 3.4) + 8
            spr = pygame.Surface((w, h), pygame.SRCALPHA)
            if kind == "boar":
                NS._paint_boar(spr, w // 2, h - 6, f, pb, sb, ab, palette)
            elif kind == "wolf":
                NS._paint_wolf(spr, w // 2, h - 6, f, pb, sb, ab, palette)
            else:
                NS._paint_hawk(spr, w // 2, h // 2, f, pb, sb, ab, palette)
            if len(NS._BEAST_CACHE) > 160:
                NS._BEAST_CACHE.clear()
            NS._BEAST_CACHE[key] = spr
        surface_w = spr.get_width()
        return spr, (int(-surface_w // 2), 0)

    def _paint_boar(s, cx, base_y, f, flap, size, alpha, P):
        """Babi hutan pembajak - ramp 5 band, bulu bergerigi, taring ivory."""
        NS = _NS_khalros
        u = size / 12.0
        bob = math.sin(flap * 0.8) * 1.5 * u
        cy = base_y - 9 * u + bob
        # bayangan contact
        NS._ellipse(s, (*P["shadow_deep"], int(alpha * 0.55)),
                    (cx - 17 * u, base_y - 3 * u, 34 * u, 5 * u))
        # kaki (4, dua-dua ditumpuk) - fase mengikuti flap
        for i, sx in enumerate((-9, -2, 5, 11)):
            lift = int(max(0.0, math.sin(flap * 1.6 + i * 1.7)) * 3 * u)
            x0 = cx + sx * u * f
            NS._rect(s, (*P["boar_darkest"], alpha),
                     (x0 - 2 * u, cy + 5 * u, 4 * u, 9 * u - lift))
            NS._rect(s, (*P["boar_dark"], alpha),
                     (x0 - 1 * u, cy + 6 * u, 2 * u, 8 * u - lift))
            NS._rect(s, (*P["bone_dark"], alpha),
                     (x0 - 2 * u, cy + 13 * u - lift, 4 * u, 2 * u))
        # badan: gundukan bahu tinggi, pinggul turun
        spine = [(cx - 15 * u * f, cy + 2 * u),
                 (cx - 8 * u * f, cy - 6 * u),
                 (cx + 1 * u * f, cy - 8 * u),
                 (cx + 9 * u * f, cy - 4 * u),
                 (cx + 15 * u * f, cy + 3 * u),
                 (cx + 12 * u * f, cy + 8 * u),
                 (cx - 11 * u * f, cy + 9 * u)]
        NS._selout_poly(s, (*P["shadow_deep"], alpha), spine, f, 1, 1)
        NS._poly(s, (*P["boar_dark"], alpha), spine)
        edge = NS._tuft_points(spine[:-2], depth=2.6 * u, min_len=4.0,
                              seed=3)
        NS._poly(s, (*P["boar_mid"], alpha),
                 [(cx + (p[0] - cx) * 0.86, cy + (p[1] - cy) * 0.82)
                  for p in edge])
        lit = [(cx + 4 * u * f, cy - 7 * u), (cx + 11 * u * f, cy - 3 * u),
               (cx + 6 * u * f, cy + 1 * u), (cx - 2 * u * f, cy - 3 * u)]
        NS._poly(s, (*P["boar_light"], alpha), lit)
        NS._poly(s, (*P["boar_high"], min(255, int(alpha * 0.8))),
                 [(cx + 6 * u * f, cy - 6 * u), (cx + 10 * u * f, cy - 4 * u),
                  (cx + 7 * u * f, cy - 2 * u)])
        # bulu kuduk bergerigi di punggung
        ruff = NS._tuft_points([(cx - 8 * u * f, cy - 6 * u),
                               (cx + 1 * u * f, cy - 9 * u),
                               (cx + 9 * u * f, cy - 5 * u)],
                              depth=3.2 * u, min_len=3.0, seed=11)
        NS._poly(s, (*P["boar_darkest"], alpha), ruff)
        # kepala rendah + moncong datar + taring
        hx, hy = cx + 17 * u * f, cy + 2 * u
        NS._poly(s, (*P["boar_dark"], alpha),
                 [(hx - 6 * u * f, hy - 6 * u), (hx + 5 * u * f, hy - 3 * u),
                  (hx + 6 * u * f, hy + 4 * u), (hx - 5 * u * f, hy + 6 * u)])
        NS._poly(s, (*P["boar_mid"], alpha),
                 [(hx - 4 * u * f, hy - 4 * u), (hx + 3 * u * f, hy - 2 * u),
                  (hx + 3 * u * f, hy + 2 * u), (hx - 4 * u * f, hy + 3 * u)])
        NS._poly(s, (*P["bone_light"], alpha),
                 [(hx + 4 * u * f, hy + 2 * u), (hx + 8 * u * f, hy - 4 * u),
                  (hx + 5 * u * f, hy + 3 * u)])
        NS._aacircle(s, (*P["bone_shine"], min(255, alpha)),
                     (int(hx + 6 * u * f), int(hy - 2 * u)), max(1, u))
        # mata merah menyala + telinga
        NS._aacircle(s, (*P["red_bright"], alpha), (hx + 1 * u * f, hy - 3 * u),
                     max(1, 1.4 * u))
        NS._aacircle(s, (*P["fire_hot"], min(255, alpha)),
                     (hx + 1 * u * f, hy - 3 * u), max(1, u))
        # napas debu dari moncong
        if flap % 4 < 2:
            NS._draw_dust_puff(s, hx + 8 * u * f, hy + 4 * u, 3 * u,
                               int(alpha * 0.6), seed=5)

    def _paint_wolf(s, cx, base_y, f, flap, size, alpha, P):
        """Serigala pack - ramp 5 band, ekor & telinga bergerigi."""
        NS = _NS_khalros
        u = size / 12.0
        bob = math.sin(flap * 1.1) * 1.4 * u
        cy = base_y - 11 * u + bob
        NS._ellipse(s, (*P["shadow_deep"], int(alpha * 0.5)),
                    (cx - 16 * u, base_y - 2 * u, 32 * u, 4 * u))
        for i, sx in enumerate((-10, -3, 4, 10)):
            lift = int(max(0.0, math.sin(flap * 2.0 + i * 1.9)) * 4 * u)
            x0 = cx + sx * u * f
            NS._aaline(s, (*P["wolf_darkest"], alpha),
                       (x0, cy + 4 * u), (x0 + lift * 0.3, base_y - 2 * u - lift),
                       max(2, int(3 * u)))
            NS._aaline(s, (*P["wolf_dark"], alpha),
                       (x0, cy + 5 * u), (x0, base_y - 3 * u - lift),
                       max(1, int(2 * u)))
        spine = [(cx - 14 * u * f, cy + 1 * u),
                 (cx - 6 * u * f, cy - 6 * u),
                 (cx + 3 * u * f, cy - 7 * u),
                 (cx + 11 * u * f, cy - 3 * u),
                 (cx + 13 * u * f, cy + 3 * u),
                 (cx - 8 * u * f, cy + 6 * u)]
        NS._selout_poly(s, (*P["shadow_deep"], alpha), spine, f, 1, 1)
        NS._poly(s, (*P["wolf_dark"], alpha), spine)
        NS._poly(s, (*P["wolf_mid"], alpha),
                 [(cx + (p[0] - cx) * 0.88, cy + (p[1] - cy) * 0.8)
                  for p in spine])
        NS._poly(s, (*P["wolf_light"], alpha),
                 [(cx + 2 * u * f, cy - 6 * u), (cx + 10 * u * f, cy - 3 * u),
                  (cx + 4 * u * f, cy + 0 * u)])
        # ekor mengibas (bergerigi)
        tail = [(cx - 14 * u * f, cy + 1 * u),
                (cx - 21 * u * f, cy - 3 * u + math.sin(flap * 1.8) * 3 * u),
                (cx - 24 * u * f, cy + 2 * u)]
        NS._poly(s, (*P["wolf_dark"], alpha),
                 NS._tuft_points([(cx - 13 * u * f, cy + 3 * u)] + tail,
                                 depth=2.6 * u, min_len=3.5, seed=6))
        NS._aacircle(s, (*P["wolf_high"], alpha),
                     (int(cx - 22 * u * f), int(cy + 0 * u)), max(1, 2 * u))
        # kepala moncong panjang + telinga runcing
        hx, hy = cx + 16 * u * f, cy - 3 * u
        NS._poly(s, (*P["wolf_dark"], alpha),
                 [(hx - 5 * u * f, hy - 4 * u), (hx + 7 * u * f, hy - 1 * u),
                  (hx + 8 * u * f, hy + 2 * u), (hx - 4 * u * f, hy + 4 * u)])
        NS._poly(s, (*P["wolf_mid"], alpha),
                 [(hx - 3 * u * f, hy - 3 * u), (hx + 5 * u * f, hy - 1 * u),
                  (hx - 2 * u * f, hy + 2 * u)])
        for sgn in (-1, 1):
            NS._poly(s, (*P["wolf_darkest"], alpha),
                     [(hx + sgn * 2 * u * f, hy - 4 * u),
                      (hx + (sgn * 2 - 3) * u * f, hy - 11 * u),
                      (hx + (sgn * 2 + 3) * u * f, hy - 5 * u)])
        NS._aacircle(s, (*P["fire_hot"], alpha), (hx + 1 * u * f, hy - 1 * u),
                     max(1, 1.3 * u))
        NS._poly(s, (*P["bone_light"], alpha),
                 [(hx + 7 * u * f, hy + 1 * u), (hx + 9 * u * f, hy + 3 * u),
                  (hx + 6 * u * f, hy + 3 * u)])

    def _paint_hawk(s, cx, cy, f, flap, size, alpha, P):
        """Elang - sayap 4-band dengan jari + bulu ekor runcing."""
        NS = _NS_khalros
        u = size / 8.0
        fs = math.sin(flap * 1.25)
        # sayap belakang
        for side_i, (span, yoff, col) in enumerate(
                ((20, -6, "hawk_dark"), (16, 2, "hawk_mid"))):
            for side in (-1, 1):
                tipx = cx + side * span * u
                tipy = cy + yoff * u - fs * 7 * u * (1 if side_i == 0 else -1)
                midx = cx + side * span * 0.55 * u
                midy = cy - fs * 3 * u
                shape = [(cx + side * 2 * u, cy - 2 * u),
                         (midx, midy - 3 * u), (tipx, tipy),
                         (cx + side * span * 0.8 * u, cy + 3 * u + fs * 2 * u),
                         (cx + side * 3 * u, cy + 4 * u)]
                NS._poly(s, (*P[col], alpha),
                         NS._tuft_points(shape[1:4], depth=2.0 * u,
                                         min_len=3.5, seed=side_i * 3 + side))
        # badan + kepala
        NS._ellipse(s, (*P["shadow_deep"], alpha),
                    (cx - 6 * u, cy - 5 * u + 1, 12 * u, 13 * u))
        NS._ellipse(s, (*P["hawk_mid"], alpha),
                    (cx - 6 * u, cy - 5 * u, 12 * u, 13 * u))
        NS._ellipse(s, (*P["hawk_light"], alpha),
                    (cx - 4 * u, cy - 4 * u, 7 * u, 8 * u))
        NS._ellipse(s, (*P["hawk_high"], alpha),
                    (cx - 3 * u, cy - 4 * u, 4 * u, 4 * u))
        hx = cx + 5 * u * f
        NS._aacircle(s, (*P["hawk_darkest"], alpha), (hx, cy - 6 * u), 4 * u)
        NS._aacircle(s, (*P["hawk_light"], alpha), (hx, cy - 6.5 * u), 3 * u)
        NS._poly(s, (*P["hawk_beak"], alpha),
                 [(hx + 3 * u * f, cy - 7 * u), (hx + 7 * u * f, cy - 5 * u),
                  (hx + 3 * u * f, cy - 4 * u)])
        NS._aacircle(s, (*P["fire_hot"], alpha), (hx + 1 * u * f, cy - 7.5 * u),
                     max(1, u))
        NS._aacircle(s, (*P["white"], min(255, alpha)),
                     (hx + 1 * u * f, cy - 8 * u), max(1, u * 0.6))
        # ekor runcing
        NS._poly(s, (*P["hawk_darkest"], alpha),
                 [(cx - 2 * u, cy + 6 * u), (cx - 9 * u * f, cy + 14 * u),
                  (cx + 3 * u, cy + 7 * u)])
        NS._poly(s, (*P["hawk_dark"], alpha),
                 [(cx - 1 * u, cy + 6 * u), (cx - 6 * u * f, cy + 12 * u),
                  (cx + 2 * u, cy + 7 * u)])
        # cakar
        for sgn in (-1, 1):
            NS._aaline(s, (*P["gold_mid"], alpha),
                       (cx + sgn * 2 * u, cy + 6 * u),
                       (cx + sgn * 3 * u, cy + 9 * u), max(1, u))

    def _draw_boar(surface, cx, cy, facing, phase, alpha=255):
        """Babi hutan (kompat nama v1) - sprite ter-cache + glow."""
        NS = _NS_khalros
        spr, off = NS._beast("boar", facing, phase, 12.0, alpha, NS.PALETTE)
        surface.blit(spr, (int(cx) + off[0], int(cy) + off[1]))

    def _draw_wolf(surface, cx, cy, facing, phase, alpha=255):
        """Serigala pack (kompat nama v1) - sprite ter-cache."""
        NS = _NS_khalros
        spr, off = NS._beast("wolf", facing, phase, 12.0, alpha, NS.PALETTE)
        surface.blit(spr, (int(cx) + off[0], int(cy) + off[1]))

    def _draw_flying_hawk(surface, cx, cy, facing, wing_phase, size=1.0):
        """Elang terbang (proyektil R + kawanan) - ter-cache."""
        NS = _NS_khalros
        spr, off = NS._beast("hawk", facing, wing_phase, 8.0 * max(0.6, size),
                             255, NS.PALETTE)
        surface.blit(spr, (int(cx) + off[0], int(cy) + off[1] - 4))

    def _draw_spinning_axe(surface, cx, cy, spin, size=1.0):
        """Kapak terbang berputar - baja 5 band + fuller + edge menyala.

        Bangun geometri SATU kali per (bucket spin, ukuran) lewat cache
        sprite; rotasi memakai `transform.rotate` (murah, kualitas sama).
        """
        NS = _NS_khalros
        P = NS.PALETTE
        sb = max(4, int(size * 12) // 2 * 2)
        spr = NS._STATIC_SURFACES.get(("axe", sb))
        if spr is None:
            u = sb / 12.0
            w = int(34 * u) + 8
            h = int(34 * u) + 8
            spr = pygame.Surface((w, h), pygame.SRCALPHA)
            ox, oy = w // 2, h // 2
            # gagang kulit: 3 band + lilitan
            NS._aaline(spr, (*P["leather_darkest"], 255),
                       (ox - 12 * u, oy + 8 * u), (ox + 6 * u, oy - 5 * u),
                       max(2, int(4 * u)))
            NS._aaline(spr, (*P["leather_mid"], 255),
                       (ox - 11 * u, oy + 7 * u), (ox + 5 * u, oy - 5 * u),
                       max(1, int(2 * u)))
            for i in range(4):
                t = i / 4.0
                gx = ox - 12 * u + t * 16 * u
                gy = oy + 8 * u - t * 12 * u
                NS._aaline(spr, (*P["leather_high"], 200),
                           (gx - 1, gy + 2), (gx + 2, gy - 1), 1)
            # mata kapak: bilah bergerigi (notch) 5 band
            blade = [(ox + 4 * u, oy - 10 * u),
                     (ox + 14 * u, oy - 8 * u),
                     (ox + 17 * u, oy - 1 * u),
                     (ox + 13 * u, oy + 6 * u),
                     (ox + 5 * u, oy + 3 * u),
                     (ox + 8 * u, oy - 2 * u)]
            NS._poly(spr, (*P["metal_darkest"], 255), blade)
            NS._poly(spr, (*P["metal_dark"], 255),
                     [(p[0] - 1 * u, p[1] + 1 * u) for p in blade])
            inner = [(ox + (p[0] - ox) * 0.78, oy + (p[1] - oy) * 0.78)
                     for p in blade]
            NS._poly(spr, (*P["metal_mid"], 255), inner)
            NS._poly(spr, (*P["metal_light"], 255),
                     [(ox + 6 * u, oy - 8 * u), (ox + 13 * u, oy - 6 * u),
                      (ox + 11 * u, oy + 1 * u), (ox + 6 * u, oy - 1 * u)])
            # fuller gelap + edge highlight
            NS._aaline(spr, (*P["metal_darkest"], 235),
                       (ox + 6 * u, oy - 6 * u), (ox + 12 * u, oy + 2 * u),
                       max(1, int(2 * u)))
            NS._aaline(spr, (*P["metal_shine"], 255),
                       (ox + 14 * u, oy - 8 * u), (ox + 17 * u, oy - 1 * u),
                       max(1, int(1.6 * u)))
            NS._aacircle(spr, (*P["metal_edge"], 235),
                         (ox + 15 * u, oy - 5 * u), max(1, u))
            # paku emas + bara di tepi
            NS._aacircle(spr, (*P["gold_mid"], 255), (ox + 7 * u, oy - 4 * u),
                         max(1, 1.3 * u))
            NS._aacircle(spr, (*P["gold_shine"], 235),
                         (ox + 6.5 * u, oy - 4.6 * u), max(1, 0.6 * u))
            NS._aacircle(spr, (*P["fire_bright"], 190),
                         (ox + 16 * u, oy - 4 * u), max(1, 2 * u))
            NS._aacircle(spr, (*P["fire_hot"], 220), (ox + 16 * u, oy - 4 * u),
                         max(1, u))
            if len(NS._STATIC_SURFACES) > 260:
                NS._STATIC_SURFACES.clear()
            NS._STATIC_SURFACES[("axe", sb)] = spr
        ang = math.degrees(spin)
        rot = pygame.transform.rotate(spr, -ang)
        surface.blit(rot, (int(cx) - rot.get_width() // 2,
                           int(cy) - rot.get_height() // 2))

    # ===================================================================
    # PROYEKTIL
    # ===================================================================
    class AxeProjectile:
        """Wild Axe - kapak berputar dengan jejak bara + asap.

        v2: busur pendek (arc) bukan garis lurus, trail 3-tone, dan
        kilau panas; tetap memakai API lama (update/draw/alive).
        """

        def __init__(self, sx, sy, tx, ty, speed=7.0, facing=1, arc=16):
            self.x = float(sx)
            self.y = float(sy)
            self.sx = float(sx)
            self.sy = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = float(speed)
            self.facing = facing
            self.arc = float(arc)
            self.alive = True
            self.age = 0
            self.spin = 0.0
            self.trail = []

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.spin += 0.62
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.hypot(dx, dy)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 9:
                self.trail.pop(0)
            ux, uy = dx / (dist or 1.0), dy / (dist or 1.0)
            # busur: simpulan naik-turun yang meluruh menuju target,
            # jadi kapak tampak "diarahkan" dan mendarat TEPAT di titik
            # radius gameplay (70 px dunia).
            arc_y = -math.sin(min(1.0, self.age / 14.0) * math.pi) \
                * self.arc * 0.35
            self.x += ux * self.speed
            self.y += uy * self.speed + arc_y

        def draw(self, surface, phase):
            NS = _NS_khalros
            P = NS.PALETTE
            n = len(self.trail)
            for i, (tx, ty) in enumerate(self.trail):
                k = i / max(1, n - 1)
                alpha = int(30 + k * 165)
                r = max(1, int(1 + k * 4))
                if k < 0.4:
                    NS._aacircle(surface, (*P["smoke_dark"], int(alpha * 0.7)),
                                 (tx, ty), r + 1)
                    NS._aacircle(surface, (*P["smoke_mid"], int(alpha * 0.5)),
                                 (tx, ty - 1), r)
                else:
                    NS._aacircle(surface, (*P["fire_dark"], alpha), (tx, ty),
                                 r + 1)
                    NS._aacircle(surface, (*P["fire_bright"], alpha), (tx, ty),
                                 r)
                    NS._aacircle(surface, (*P["fire_hot"], int(alpha * 0.85)),
                                 (tx, ty - 1), max(1, r - 2))
            if not self.alive:
                return
            px, py = int(self.x), int(self.y)
            NS._glow(surface, px, py, 16, P["fire_mid"], 110)
            NS._draw_spinning_axe(surface, px, py, self.spin, size=1.15)

    class HawkProjectile:
        """Elang penyelam - jalur melengkung predator + jejak bulu."""

        def __init__(self, sx, sy, tx, ty, speed=5.0):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = float(speed)
            self.alive = True
            self.age = 0
            self.wing_phase = 0.0
            self.facing = 1 if tx >= sx else -1
            self.trail = []

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.wing_phase += 0.5
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.hypot(dx, dy)
            if dist < self.speed + 6:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 7:
                self.trail.pop(0)
            glide = math.sin(self.age * 0.22) * 1.4
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed + glide

        def draw(self, surface, phase):
            NS = _NS_khalros
            P = NS.PALETTE
            n = len(self.trail)
            for i, (tx, ty) in enumerate(self.trail):
                k = i / max(1, n - 1)
                alpha = int(28 + k * 110)
                NS._aacircle(surface, (*P["hawk_dark"], alpha), (tx, ty),
                             max(1, int(1 + k * 2)))
                if i % 3 == 0:
                    NS._aacircle(surface, (*P["hawk_light"], int(alpha * 0.7)),
                                 (tx + 1, ty - 1), 1)
            if not self.alive:
                return
            facing = getattr(self, "facing", 1) or 1
            NS._glow(surface, int(self.x), int(self.y), 14, P["wind_dark"], 70)
            NS._draw_flying_hawk(surface, int(self.x), int(self.y), facing,
                                 self.wing_phase, size=1.1)
            # bayangan penyelam di tanah (menjaga konteks 3/4 view)
            dy_ground = 26 + int(6 * math.sin(self.age * 0.2))
            NS._ellipse(surface, (*P["shadow_deep"], 90),
                        (int(self.x) - 9, int(self.y) + dy_ground, 18, 5))

    def _spawn_axe(boss, sx, sy, tx, ty, arc=16):
        if not hasattr(boss, "_khal_projectiles"):
            boss._khal_projectiles = []
        boss._khal_projectiles.append(
            _NS_khalros.AxeProjectile(sx, sy, tx, ty, speed=7.0,
                                      facing=getattr(boss, "direction", 1),
                                      arc=arc))

    def _spawn_hawk(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_khal_projectiles"):
            boss._khal_projectiles = []
        boss._khal_projectiles.append(
            _NS_khalros.HawkProjectile(sx, sy, tx, ty, speed=5.5))

    def _manage_projectiles(boss, surface, phase):
        """Update + gambar proyektil milik boss (API lama dipertahankan)."""
        if not hasattr(boss, "_khal_projectiles"):
            boss._khal_projectiles = []
        for proj in boss._khal_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._khal_projectiles = [p for p in boss._khal_projectiles
                                  if p.alive or p.age < 5]

    # ===================================================================
    # STATE / ANIMASI
    # ===================================================================
    def _detect_moving(boss):
        """True bila posisi berubah > 0.3 px sejak frame lalu (solver kaki)."""
        if not hasattr(boss, "_khal_last_x"):
            boss._khal_last_x = getattr(boss, "x", 0.0)
            boss._khal_last_y = getattr(boss, "y", 0.0)
            return False
        dx = abs(getattr(boss, "x", 0.0) - getattr(boss, "_khal_last_x", 0.0))
        dy = abs(getattr(boss, "y", 0.0) - getattr(boss, "_khal_last_y", 0.0))
        boss._khal_last_x = getattr(boss, "x", 0.0)
        boss._khal_last_y = getattr(boss, "y", 0.0)
        return dx + dy > 0.3

    def _update_attack_anim(boss):
        """Timeline serangan 16 frame -> `_khal_attack_progress` kontinu.

        Keyframe IMPACT berada di `ATTACK_IMPACT` (0.54) - frame tempat
        bintang benturan, retakan tanah, dan hit-window dibuka.
        """
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_khal_prev_timer", 0))
        active = bool(getattr(boss, "_khal_attack_active", False))
        swing_len = max(10, min(22, cooldown // 2))

        if timer >= cooldown - 1 and previous <= 1:
            boss._khal_attack_active = True
            boss._khal_attack_frame = 0
            active = True
        elif active:
            boss._khal_attack_frame = int(
                getattr(boss, "_khal_attack_frame", 0)) + 1
            if boss._khal_attack_frame > cooldown:
                boss._khal_attack_active = False
                boss._khal_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._khal_attack_active = False
            boss._khal_attack_frame = 0
            active = False

        boss._khal_prev_timer = timer
        frame = int(getattr(boss, "_khal_attack_frame", 0))
        boss._khal_attack_progress = (
            min(1.0, frame / float(swing_len)) if active else 0.0)
        # jendela benturan (dipakai audio/hit hook & lapisan hidup)
        boss._khal_hit_active = bool(active and 0.30 <= boss._khal_attack_progress
                                      <= 0.62)
        boss._khal_attack_raw = frame

    def _attack_pose(ap):
        """Interpolasi keyframe serang -> dict pose.

        Keyframe: (progress, lunge, lean, dip, arm_a, flare, tremble)
          0.14  wind-up   : kapak diangkat ke atas-belakang, badan mundur
          0.30  tension    : gemetar 1 px, jubah & janggut tertinggal
          0.48  strike     : ayunan tercepat (smear sabit baja aktif)
          0.54  IMPACT     : squash + bintang 8-spike + retakan tanah
          0.72  follow     : rebound overshoot
          1.00  recover    : kembali ke pose istirahat
        """
        keys = (
            (0.00, 0.0,  0.0,  0.0, -2.35, 1.00, 0),
            (0.14, -3.0, -5.0, 2.5, -2.95, 1.10, 0),
            (0.30, -4.5, -6.5, 3.5, -3.10, 1.18, 1),
            (0.48, 8.0,  6.5, -2.5, 0.55, 1.06, 0),
            (0.54, 10.5, 8.5, 4.0, 1.05, 1.00, 0),
            (0.72, 4.0,  3.0, 1.5, 1.55, 1.00, 0),
            (1.00, 0.0,  0.0, 0.0, -2.35, 1.00, 0),
        )
        ap = max(0.0, min(1.0, ap))
        for i in range(len(keys) - 1):
            k0, k1 = keys[i], keys[i + 1]
            if k0[0] <= ap <= k1[0]:
                span = max(1e-6, k1[0] - k0[0])
                t = (ap - k0[0]) / span
                t = t * t * (3 - 2 * t)              # smoothstep
                vals = tuple(a + (b - a) * t for a, b in zip(k0[1:6],
                                                             k1[1:6]))
                return {
                    "lunge": vals[0], "lean": vals[1], "dip": vals[2],
                    "arm_a": vals[3], "flare": vals[4],
                    "tremble": 1 if (k0[6] and t < 0.9) else 0,
                    "impact": 1.0 - min(1.0, abs(ap - _NS_khalros.ATTACK_IMPACT)
                                        / 0.10),
                }
        return {"lunge": 0.0, "lean": 0.0, "dip": 0.0, "arm_a": -2.35,
                "flare": 1.0, "tremble": 0, "impact": 0.0}

    def _stride_solver(action, phase):
        """Solver langkah dua kaki untuk unit BERDIRI (pengganti float-solver).

        Return (swing_a, swing_b, lift_a, lift_b, contact, bob) - `contact`
        0..1 memicu debu tanah saat tumit menyentuh lantai, `bob` mengunci
        badan ke ritme langkah supaya langkah terasa menopang berat.
        """
        if action != "walk":
            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        p = phase
        a = math.sin(p)
        b = math.sin(p + math.pi)
        # heel-off (naik) saat kaki ke depan, toe-off saat ke belakang
        lift_a = max(0.0, a) * 3.0
        lift_b = max(0.0, b) * 3.0
        # kontak = kaki melewati titik terendah (akselerasi turun)
        contact = max(0.0, -math.cos(p)) * max(0.0, a)
        contact = min(1.0, contact * 2.2)
        bob = -abs(math.sin(p)) * 2.2
        return a, b, lift_a, lift_b, contact, bob

    def _resolve_pose(boss, moving=False):
        """(action, phase, ap) - murni, tanpa efek samping.

        Dipakai dispatch gambar DAN semua efek eksternal (trail, proyektil,
        lapisan hidup) supaya bilah, badan, dan FX tidak pernah beda frame.
        """
        NS = _NS_khalros
        skill = getattr(boss, "active_skill", None)
        attacking = (
            getattr(boss, "_khal_attack_active", False)
            or getattr(boss, "timer", 0)
            > getattr(boss, "attack_cooldown", 45) - 15
        )
        if skill == "e":
            action = "charge"
        elif attacking:
            action = "attack"
        elif skill in ("q", "w", "r"):
            action = "attack"
        elif moving:
            action = "walk"
        else:
            action = "idle"
        phase = float(getattr(boss, "pulse", 0.0) or 0.0)
        ap = 0.0
        if action in ("attack", "cast", "charge"):
            ap = max(0.0, min(1.0, float(
                getattr(boss, "_khal_attack_progress", 0.0) or 0.0)))
        return action, phase, ap

    # -------------------------------------------------------------------
    # Pemetaan ruang lokal rig -> layar (dipakai FX eksternal)
    # -------------------------------------------------------------------
    def _body_offset(action, phase, ap, facing=1):
        """(dx, dy) layar sebelum _draw_khalros_body (sinkron dengan raw)."""
        NS = _NS_khalros
        f = 1 if facing >= 0 else -1
        if action == "attack":
            pose = NS._attack_pose(ap)
            return int(pose["lunge"] * NS.SCALE) * f, int(math.sin(phase * 0.8) * 2)
        if action == "charge":
            return int(9 * NS.SCALE) * f, 3
        if action == "cast":
            return int(-2 * NS.SCALE) * f, int(math.sin(phase * 1.6) * 2)
        if action == "walk":
            pw = phase * 2.4
            _, _, _, _, _, bob = NS._stride_solver("walk", pw)
            return int(math.sin(pw * 0.5) * 2), int(bob)
        return 0, int(math.sin(phase * 0.7) * 2) - 1

    def _raw_shift(action, phase, ap, facing=1):
        """(lean_f, root_y, tremble, sway) ruang native `_..._body_raw`."""
        NS = _NS_khalros
        f = 1 if facing >= 0 else -1
        breath = math.sin(phase * 0.72)
        sway = int(math.sin(phase * 0.6) * 1)
        if action == "attack":
            pose = NS._attack_pose(ap)
            tremble = 1 if (pose["tremble"] and int(phase * 30) % 2) else 0
            return int(pose["lean"]) * f, int(pose["dip"]), tremble, sway
        if action == "charge":
            return 7 * f, 2, 0, int(math.sin(phase * 3.0) * 2)
        if action == "cast":
            return 1 * f, int(breath * 1.4), 0, sway
        if action == "walk":
            return 2 * f, int(breath * 1.4), 0, sway
        return int(math.sin(phase * 0.5 + 1.1) * 1.5), int(breath * 1.9), 0, sway

    def _local_to_screen(cx, cy, facing, lean_f, root_y, tremble, sway,
                         lx, ly):
        """SATU pemetaan lokal badan -> layar (x maju mengikuti facing)."""
        k = _NS_khalros.SCALE
        return (int(cx + (lx * (1 if facing >= 0 else -1) + lean_f + tremble
                          + sway) * k),
                int(cy + (ly + root_y) * k))

    def _local(boss, x, y, action, phase, ap, lx, ly):
        """Ruang lokal rig -> piksel surface (dipakai heroes/khalros_fx)."""
        NS = _NS_khalros
        facing = getattr(boss, "direction", 1) or 1
        dx, dy = NS._body_offset(action, phase, ap, facing)
        lean_f, root_y, tremble, sway = NS._raw_shift(action, phase, ap, facing)
        return NS._local_to_screen(x + dx, y + dy, facing, lean_f, root_y,
                                   tremble, sway, lx, ly)

    def _axe_grip_local(action, phase, ap, facing=1):
        """Pergelangan tangan pemegang kapak (ruang lokal native).

        Kembaran matematis `_draw_attack_arms` / `_draw_idle_arms` - angka
        di sini HARUS tetap sejalan dengan yang digambar.
        """
        NS = _NS_khalros
        f = 1 if facing >= 0 else -1
        sway_arm = int(math.sin(phase * 0.7) * 1.6)
        if action == "attack":
            pose = NS._attack_pose(ap)
            arm = pose["arm_a"]
            return (f * 14 + int(math.cos(arm) * NS.AXE_ARM_LEN) * f,
                    -34 + int(math.sin(arm) * NS.AXE_ARM_LEN))
        if action == "charge":
            return f * 22, -22
        if action == "cast":
            # tangan naik ke samping kepala (mengacung ke langit) - jangan
            # terlalu tinggi supaya bilah tidak menumpuk dengan tanduk
            return f * 13, -46 + sway_arm
        if action == "walk":
            return f * 22, -29 + sway_arm
        return f * 19, -26 + sway_arm

    def _axe_tip_local(action, phase, ap, facing=1):
        """Ujung bilah kapak (ruang lokal native) - untuk trail & hitbox."""
        NS = _NS_khalros
        f = 1 if facing >= 0 else -1
        gx, gy = NS._axe_grip_local(action, phase, ap, facing)
        total = NS.AXE_HANDLE + NS.AXE_BLADE
        if action == "attack":
            pose = NS._attack_pose(ap)
            ang = pose["arm_a"] + 0.72
            return gx + int(math.cos(ang) * total) * f, gy + int(
                math.sin(ang) * total)
        if action == "charge":
            return gx + 20 * f, gy + 14
        if action == "cast":
            return gx + 8 * f, gy - 30
        # idle / walk: kapak disandang menyilang ke atas bahu - ujung bilah
        # muncul di atas kepala (siluet khas beastlord, bukan garis lurus)
        return gx + 15 * f, gy - 36

    def _axe_grip_screen(boss, x, y):
        action, phase, ap = _NS_khalros._resolve_pose(
            boss, bool(getattr(boss, "_khal_moving", False)))
        facing = getattr(boss, "direction", 1) or 1
        lx, ly = _NS_khalros._axe_grip_local(action, phase, ap, facing)
        return _NS_khalros._local(boss, x, y, action, phase, ap, lx, ly)

    def _axe_tip_screen(boss, x, y):
        action, phase, ap = _NS_khalros._resolve_pose(
            boss, bool(getattr(boss, "_khal_moving", False)))
        facing = getattr(boss, "direction", 1) or 1
        lx, ly = _NS_khalros._axe_tip_local(action, phase, ap, facing)
        return _NS_khalros._local(boss, x, y, action, phase, ap, lx, ly)

    def _swing_hitbox(boss, x, y):
        """AABB jendela benturan (SWING/IMPACT) - dipakai debug overlay."""
        NS = _NS_khalros
        action, phase, ap = NS._resolve_pose(
            boss, bool(getattr(boss, "_khal_moving", False)))
        if action != "attack" or not (0.30 <= ap <= 0.78):
            return None
        facing = getattr(boss, "direction", 1) or 1
        gx, gy = NS._axe_grip_screen(boss, x, y)
        tx, ty = NS._axe_tip_screen(boss, x, y)
        pad = 11
        rect = pygame.Rect(int(min(gx, tx)) - pad, int(min(gy, ty)) - pad,
                           int(abs(tx - gx)) + pad * 2,
                           int(abs(ty - gy)) + pad * 2)
        if facing < 0 and rect.right > x:
            rect.width = max(4, int(x - rect.left))
        return rect

    # ===================================================================
    # LAPISAN FX HIDUP (heroes/khalros_fx.py)
    # ===================================================================
    #: Modul FX layar (diisi malas). False = gagal -> jalur canvas penuh.
    _LIVE_MOD = None

    def _live_module():
        """Muat ``heroes.khalros_fx`` sekali; None kalau tidak tersedia."""
        NS = _NS_khalros
        if NS._LIVE_MOD is None:
            try:
                from heroes import khalros_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "KHALROS_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    def live_fx_ready():
        """True bila lapisan hidup Khalros bisa dipakai (dipakai tooling)."""
        return _NS_khalros._live_module() is not None

    def _live_fx(boss, surface, x, y, want_draw, portrait):
        """Lapisan hidup untuk unit ini -> ``(mod, owned)``.

        ``want_draw`` True pada jalur BOSS (digambar tiap frame, tanpa
        cache sprite). Pada jalur lane, penggambaran dilakukan
        heroes/__init__.py, jadi di sini hanya dipasang penanda.

        PENTING: lapisan hidup TIDAK lagi menggambar badan - rig
        masterwork di namespace ini satu-satunya sumber bentuk, supaya
        tidak ada dua interpretasi siluet Khalros (penyebab v1 "jelek").
        """
        NS = _NS_khalros
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
        """True bila lapisan hidup sudah mengambil alih EFEK unit ini."""
        mod = _NS_khalros._live_module()
        if mod is None:
            return False
        try:
            return bool(mod.owns(boss))
        except Exception:
            return False

    # ===================================================================
    # MAIN ENTRY
    # ===================================================================
    def draw_khalros(surface, boss, x, y):
        """Entry point `Boss.draw()` sekaligus `heroes.render_hero()`.

        Urutan lapisan proyek:

            AURA -> GROUND FX (pool/rune/telegraph) -> SHADOW -> BADAN
            (rig native 1.5x -> SCALE -> selout -> lighting -> outline)
            -> SWING TRAIL -> PROYEKTIL -> SKILL FX DEPAN -> LAPISAN HIDUP

        Semua FX skill world-space lewat `_fx_scale`; semua nama publik v1
        dipertahankan. Bila lapisan hidup tidak tersedia, seluruh efek
        digambar di-canvas ini (jalur fallback).
        """
        NS = _NS_khalros
        pulse = float(getattr(boss, "pulse", 0.0) or 0.0)
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0) or 0)
        moving = NS._detect_moving(boss)
        NS._update_attack_anim(boss)
        # ekspos state bergerak ke lapisan hidup (heroes/khalros_fx)
        try:
            boss._khal_moving = moving
        except Exception:
            pass
        portrait = bool(getattr(boss, "_portrait_hd", False))
        in_cache = bool(getattr(boss, "_skip_renderer_projectiles", False))

        action, phase, ap = NS._resolve_pose(boss, moving)
        try:
            boss._khal_pose_action = action
        except Exception:
            pass
        # badan bereaksi ke state skill
        rage = active_skill in ("w", "r")
        hunting = active_skill in ("q", "e")

        # ---------- Lapisan hidup (ground pass) ----------
        hero_lane = hasattr(boss, "_render_scale")
        live, owned = NS._live_fx(boss, surface, x, y, not hero_lane, portrait)

        # ---------- Background layers (dibuang di portrait LOD) ----------
        if not portrait:
            NS._draw_primal_aura(surface, x, y, pulse, active_skill)
            NS._draw_ground_runes(surface, x, y + NS.GROUND_DY, pulse,
                                  active_skill)
            if not owned and not in_cache:
                NS._draw_scorch_marks(boss, surface, pulse, x, y)

            # ---------- Skill ground telegraph (world-space) ----------
            if active_skill == "q":
                NS._draw_wild_axes_ground(surface, boss, x, y, skill_timer,
                                          pulse)
            elif active_skill == "w":
                NS._draw_call_of_wild_ground(surface, boss, x, y, skill_timer,
                                             pulse)
            elif active_skill == "e":
                NS._draw_boar_ground(surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "r":
                NS._draw_hawk_storm_ground(surface, boss, x, y, skill_timer,
                                           pulse)

            # AKTIVASI: gelombang kejut + bintang (12 frame pertama).
            # Saat lapisan hidup mengambil alih, gelombang digambar di
            # sana supaya tidak dobel dan tetap 60 fps.
            if active_skill in ("q", "w", "e", "r") and not owned:
                dur = NS.SKILL_DUR[active_skill]
                age = dur - skill_timer
                if 0 <= age < 12:
                    NS._draw_shockwave(
                        surface, x, y + NS.GROUND_DY, age, 12,
                        NS.PALETTE["fire_hot"], NS.PALETTE["fire_glow"],
                        fs=NS._fx_scale(boss))

        # ---------- ORIGINAL-MAX hurt flash (badan saja) ----------
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        _tgt, _tx, _ty = surface, x, y
        if flash > 0:
            if NS._flash_buf is None:
                NS._flash_buf = pygame.Surface((NS.RIG_W, NS.RIG_H),
                                               pygame.SRCALPHA)
            NS._flash_buf.fill((0, 0, 0, 0))
            NS._record_shadow = []
            _tgt, _tx, _ty = NS._flash_buf, NS.RIG_OX, NS.RIG_OY

        # ---------- Character ----------
        if action == "charge":
            NS._draw_khalros_charge(_tgt, boss, _tx, _ty, skill_timer, rage)
        elif action == "attack":
            NS._draw_khalros_attack(_tgt, boss, _tx, _ty, rage, hunting)
        elif action == "cast":
            NS._draw_khalros_cast(_tgt, boss, _tx, _ty, active_skill,
                                  skill_timer, rage)
        elif action == "walk":
            NS._draw_khalros_walk(_tgt, boss, _tx, _ty, rage, hunting)
        else:
            NS._draw_khalros_idle(_tgt, boss, _tx, _ty, rage, hunting)

        if flash > 0:
            surface.blit(NS._flash_buf, (x - _tx, y - _ty))
            w = int(235 * min(1.0, flash / 8.0))
            m = pygame.mask.from_surface(NS._flash_buf, 50)
            wht = m.to_surface(setcolor=(w, int(w * 0.9), int(w * 0.8), 255),
                               unsetcolor=(0, 0, 0, 0))
            for rect in (NS._record_shadow or ()):
                wht.fill((0, 0, 0, 0), rect)
            surface.blit(wht, (x - _tx, y - _ty),
                         special_flags=pygame.BLEND_RGB_ADD)
            NS._record_shadow = None

        # ---------- Projectiles ----------
        if not portrait:
            if not owned:
                NS._manage_projectiles(boss, surface, pulse)

            # ---------- Foreground skill effects (fallback canvas) ----------
            if not owned:
                if active_skill == "q":
                    NS._draw_wild_axes(surface, boss, x, y, skill_timer, pulse)
                elif active_skill == "w":
                    NS._draw_call_of_wild(surface, boss, x, y, skill_timer,
                                          pulse)
                elif active_skill == "e":
                    NS._draw_boar_charge(surface, boss, x, y, skill_timer,
                                         pulse)
                elif active_skill == "r":
                    NS._draw_hawk_summon(surface, boss, x, y, skill_timer,
                                         pulse)

        # ---------- Lapisan hidup bagian ATAS + debug ----------
        if live is not None:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass

    def _draw_shockwave(surface, x, y, age, total, c1, c2, fs=1.0):
        """Gelombang kejut aktivasi skill - 12 frame pertama, world-space."""
        t = age / float(total)
        if t >= 1.0:
            return
        P = _NS_khalros.PALETTE
        ease = 1 - (1 - t) ** 2
        r = int((14 + ease * 58) * fs)
        a = _NS_khalros._alpha(235 * (1 - t))
        _NS_khalros._ground_ring(surface, x, y, r, c1, c2, a,
                                  thickness=max(1.5, 5 - ease * 3.5),
                                  softness=10)
        _NS_khalros._ground_ring(surface, x, y, int(r * 0.72), c2,
                                  P["white"], int(a * 0.55),
                                  thickness=max(1.0, 3 - ease * 2),
                                  softness=7)
        _NS_khalros._glow(surface, x, y, max(6, int(r * 0.5)), c1,
                          int(a * 0.75 * (1 - ease * 0.6)))
        _NS_khalros._spark_star(surface, x, y, int(20 * fs), c2, a,
                                spikes=8, rot=t * 2.2, core=P["white"])

    # ===================================================================
    # LAPISAN TANAH / AMBIENT
    # ===================================================================
    def _draw_scorch_marks(boss, surface, phase, x=0, y=0):
        """Bekas cakar/bantingan di tanah - memudar, ter-cache per usia.

        Disimpan sebagai OFFSET relatif jangkar badan supaya tetap benar
        baik di layar 1:1 (jalur boss) maupun di canvas cache lane hero.
        Alpha dijaga < 100 agar tidak dibaca sebagai siluet badan.
        """
        marks = getattr(boss, "_khal_ground_marks", None)
        if not marks:
            return
        P = _NS_khalros.PALETTE
        alive = []
        for (wx, wy, r, life) in marks:
            k = max(0.0, min(1.0, life / 90.0))
            a = int(150 * k)
            if a > 6:
                _NS_khalros._ground_scorch(surface, wx, wy, r,
                                           P["fire_darkest"], P["shadow_deep"],
                                           a, seed=int(r) % 7 + 2)
                _NS_khalros._zone_fill(surface, wx, wy, int(r * 0.8),
                                       P["fire_dark"], int(60 * k))
            life -= 1
            if life > 0:
                alive.append((wx, wy, r, life))
        boss._khal_ground_marks = alive

    def note_ground_mark(boss, x, y, radius=26, life=90, ax=None, ay=None):
        """Tinggalkan bekas cakar/bantingan di tanah (offset relatif jangkar).

        ``ax/ay`` = jangkar badan saat ini; kalau tidak diberi, memakai
        posisi boss (jalur 1:1).
        """
        if ax is None:
            ax = getattr(boss, "x", x)
        if ay is None:
            ay = getattr(boss, "y", y)
        marks = getattr(boss, "_khal_ground_marks", None)
        if marks is None:
            marks = []
            try:
                boss._khal_ground_marks = marks
            except Exception:
                return
        try:
            marks.append((int(x - ax), int(y - ay), int(radius), int(life)))
        except Exception:
            return
        if len(marks) > 6:
            del marks[:-6]

    def _draw_shadow(surface, x, y, lift=0):
        """Bayangan tanah ter-cache; menyusut saat lift, dasar tetap menapak."""
        NS = _NS_khalros
        P = NS.PALETTE

        def build():
            shadow = pygame.Surface((112, 24), pygame.SRCALPHA)
            for radius in range(12, 0, -1):
                alpha = max(0, (12 - radius) * 15)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (12 - radius, 12 - radius, 88 + radius * 2, radius * 2))
            # sentuhan warna: bara redup di bawah unit beastlord
            pygame.draw.ellipse(shadow, (*P["fire_dark"], 52),
                                (11, 6, 90, 12))
            return shadow

        spr = NS._shadow_cache if NS._shadow_cache is not None else build()
        if NS._shadow_cache is None:
            NS._shadow_cache = spr
        w = spr.get_width()
        h = spr.get_height()
        if lift:
            k = max(0.12, 1.0 - lift * 0.05)
            w = max(6, int(w * k))
            h = max(2, int(h * k))
            spr = pygame.transform.smoothscale(NS._shadow_cache, (w, h))
        bx = x - w // 2
        by = (y + 12) - h          # dasar menapak di y+12
        surface.blit(spr, (bx, by))
        if NS._record_shadow is not None:
            NS._record_shadow.append(pygame.Rect(bx, by, w, h))

    def _draw_primal_aura(surface, x, y, phase, active_skill):
        """Aura primal ter-cache: bara redap + rim panas; menguat saat skill."""
        NS = _NS_khalros
        P = NS.PALETTE

        def build():
            aura = pygame.Surface((208, 176), pygame.SRCALPHA)
            # kolom heat di belakang badan (lebar mengecil ke atas)
            for i in range(30):
                t = i / 29.0
                w = int(52 + 26 * (1 - t))
                yy = int(150 - t * 120)
                a = int(17 * (1 - t) ** 1.4)
                col = NS._mix(P["fire_darkest"], P["fire_dark"], t)
                NS._ellipse(aura, (*col, a), (104 - w, yy - 8, w * 2, 16))
            # lingkaran bara bawah
            for radius in range(64, 6, -4):
                a = int((64 - radius) * 0.34)
                if a > 0:
                    NS._aacircle(aura, (*P["fire_darkest"], min(255, a)),
                                 (104, 120), radius)
            return aura

        aura = NS._static(("primal_aura",), build)
        # `_aura_cache` = nama publik v1; menunjuk ke surface yang sama supaya
        # pembanding/penguji lama masih bisa memeriksa "dibangun sekali".
        NS._aura_cache = aura
        pulse = math.sin(phase * 0.55) * 0.25 + 0.75
        strength = 1.7 if active_skill in ("q", "w", "r") else 1.0
        # JANGAN copy per frame (208x176 tiap boss tiap frame = 36rb px sia-sia):
        # set_alpha pada surface cache, blit, lalu lepas lagi (pola
        # `_blit_decal`). Blit NORMAL menghormati set_alpha; additive tidak.
        aura.set_alpha(NS._alpha(255 * min(1.0, pulse * strength)))
        surface.blit(aura, (int(x) - 104, int(y) - 112))
        aura.set_alpha(255)
        # bara yang naik (deterministik - tidak mengubah bbox tiap frame)
        n = 7 if active_skill else 5
        for i in range(n):
            t = (phase * 0.42 + NS._hash01(i * 9.3)) % 1.0
            ex = x + int((NS._hash01(i * 5.1) - 0.5) * 74)
            ey = y + 34 - int(t * 92)
            ea = int(160 * (1 - t))
            if ea > 10:
                NS._draw_ember(surface, ex, ey, 1 if i % 3 else 2, ea)

    def _draw_ground_runes(surface, x, y, phase, active_skill):
        """Cincin rune binatang di lantai - decal ter-cache, bukan stroke.

        ALPHA sengaja dijaga DI BAWAH 100: ambang itu dipakai
        `get_bounding_rect(min_alpha=100)` oleh regresi keluarga
        (`tools/test_level2_masterwork.py`) dan oleh
        `heroes._measure_native_size`. Dengan begitu cincin lantai terbaca
        sebagai cahaya di tanah TANPA membuat siluet khalros membengkak
        melewati alchemist (true boss) atau menggeser normalisasi skala di
        lane hero.
        """
        NS = _NS_khalros
        P = NS.PALETTE
        pulse = math.sin(phase * 1.1) * 0.3 + 0.7
        boost = 1.4 if active_skill else 1.0
        # Saat IDEL semua lapis ambient digambar NON-additive: blit additive
        # juga MENAMBAH kanal alpha, dan canvas cache lane hero / portrait
        # menilai siluet dari alpha >= 100 - piringan lantai tidak boleh
        # ikut dihitung sebagai badan.
        amb = not active_skill
        r = 26
        NS._glow(surface, x, y, int(r * 1.25), P["fire_dark"],
                 int(26 * pulse * boost), add=amb)
        NS._ground_ring(surface, x, y, r, P["fire_mid"], P["fire_hot"],
                        int(48 * pulse * boost), thickness=1.8, softness=6,
                        inner_glow=5, add=not amb)
        NS._rune_ring(surface, x, y, int(r * 0.68), P["fire_dark"],
                      P["fire_glow"], int(46 * pulse * boost), phase * 0.35,
                      segments=9, span=0.44, thickness=2.0, add=not amb)
        # 3 bekas cakar di cincin dalam
        for i in range(3):
            ang = phase * 0.35 + i * math.tau / 3
            cx2 = x + math.cos(ang) * r * 0.7
            cy2 = y + math.sin(ang) * r * 0.7
            NS._chevron(surface, cx2, cy2, ang + math.pi / 2, 5,
                        P["fire_hot"], int(64 * pulse * boost), width=2)

    def _draw_wild_wisps(surface, cx, cy, phase, trail=False, facing=1,
                         intense=False):
        """Pita kabut primal di belakang unit (nama v1 dipertahankan).

        v2: 3 helai pita ber-falloff yang mengikuti arah gerak, bukan
        tumpukan lingkaran; murah (satu surface per frame di-buffer kecil).
        """
        NS = _NS_khalros
        P = NS.PALETTE
        n = 5 if intense else 3
        for i in range(n):
            t = (phase * (0.55 if trail else 0.34) + i * 0.37) % 1.0
            wob = math.sin(phase * 1.3 + i * 2.1) * 6
            x0 = cx - facing * (8 + i * 5) + wob * 0.4
            y0 = cy + 18 - t * 58
            alpha = int((140 if intense else 95) * (1 - t))
            if alpha <= 8:
                continue
            col = NS._mix(P["fire_dark"], P["fire_glow"], t * 0.6)
            NS._aaline(surface, (*col, alpha), (x0, y0),
                       (x0 - facing * 5 + wob, y0 - 9), max(1, 3 - i // 2))
            NS._aacircle(surface, (*P["fire_hot"], int(alpha * 0.8)),
                         (x0 - facing * 5 + wob, y0 - 9), 1)

    # ===================================================================
    # POSE MODES  (jangkar tanah = +GROUND_DY; ground FX mengikuti)
    # ===================================================================
    def _draw_khalros_idle(surface, boss, x, y, rage=False, hunting=False):
        NS = _NS_khalros
        phase = float(getattr(boss, "pulse", 0.0) or 0.0)
        bob = int(math.sin(phase * 0.7) * 2) - 1
        portrait = bool(getattr(boss, "_portrait_hd", False))
        if not portrait:
            NS._draw_shadow(surface, x, y + NS.GROUND_DY)
            NS._draw_wild_wisps(surface, x, y + 26, phase)
        NS._draw_khalros_body(surface, x, y + bob,
                              getattr(boss, "direction", 1), phase, "idle",
                              0, boss=boss)

    def _draw_khalros_walk(surface, boss, x, y, rage=False, hunting=False):
        NS = _NS_khalros
        phase = float(getattr(boss, "pulse", 0.0) or 0.0) * 2.4
        facing = getattr(boss, "direction", 1)
        _, _, _, _, contact, bob = NS._stride_solver("walk", phase)
        sway = int(math.sin(phase * 0.5) * 2)
        portrait = bool(getattr(boss, "_portrait_hd", False))
        if not portrait:
            NS._draw_shadow(surface, x + sway, y + NS.GROUND_DY)
            if contact > 0.45:
                NS._draw_dust_puff(surface, x + sway - facing * 10,
                                   y + NS.GROUND_DY, 7 + contact * 4,
                                   int(150 * contact), seed=int(phase) % 5)
            NS._draw_wild_wisps(surface, x + sway, y + 26, phase, trail=True,
                                facing=facing)
        NS._draw_khalros_body(surface, x + sway, y + int(bob), facing, phase,
                              "walk", 0, boss=boss)

    def _draw_khalros_attack(surface, boss, x, y, rage=False, hunting=False):
        NS = _NS_khalros
        progress = max(0.0, min(1.0, float(
            getattr(boss, "_khal_attack_progress", 0.0) or 0.0)))
        phase = float(getattr(boss, "pulse", 0.0) or 0.0)
        facing = getattr(boss, "direction", 1) or 1
        pose = NS._attack_pose(progress)
        bob = int(math.sin(phase * 0.8) * 2)
        lunge = int(pose["lunge"] * NS.SCALE) * facing
        portrait = bool(getattr(boss, "_portrait_hd", False))
        if not portrait:
            NS._draw_shadow(surface, x + lunge, y + NS.GROUND_DY,
                            lift=max(0, int(progress * 3)))
            NS._draw_wild_wisps(surface, x + lunge, y + 26, phase,
                                intense=True, facing=facing)
        NS._draw_khalros_body(surface, x + lunge, y + bob, facing, phase,
                              "attack", progress, boss=boss)
        # smear kapak HANYA kalau lapisan hidup tidak mengambil alih
        # (trail layar memakai histori ujung bilah yang sebenarnya).
        if not portrait and not NS._fx_owned(boss):
            NS._draw_axe_swing_arc(surface, x + lunge, y + bob, facing,
                                   progress)
            NS._draw_swing_impact(surface, x + lunge, y + bob, facing,
                                  progress)

    def _draw_khalros_cast(surface, boss, x, y, skill, timer, rage=False):
        """Pose skill (Q/W/R): badan menegak, kapak terangkat, raungan.

        Hanya POSE yang berubah di sini - telegraph & FX zona digambar
        `draw_khalros` di lantai (world-space), supaya keduanya tidak
        saling menutupi.
        """
        NS = _NS_khalros
        P = NS.PALETTE
        phase = float(getattr(boss, "pulse", 0.0) or 0.0)
        facing = getattr(boss, "direction", 1) or 1
        duration = NS.SKILL_DUR.get(skill, 50)
        progress = max(0.0, min(1.0, 1 - timer / float(duration)))
        # naik-turun badan: menunduk saat menarik napas, bangkit saat memanggil
        dip = -int(3 * math.sin(min(1.0, progress * 1.6) * math.pi))
        portrait = bool(getattr(boss, "_portrait_hd", False))
        if not portrait:
            NS._draw_shadow(surface, x, y + NS.GROUND_DY, lift=abs(dip))
            NS._draw_wild_wisps(surface, x, y + 26, phase * 1.5,
                                intense=True, facing=facing)
        NS._draw_khalros_body(surface, x, y + dip, facing, phase, "cast",
                              0, boss=boss)
        if portrait:
            return
        # raungan: tiga cincin suara membesar dari kepala (paruh pertama)
        if progress < 0.5:
            t = progress / 0.5
            hx, hy = x + 6 * facing, y - 34 + dip
            for i in range(3):
                k = max(0.0, min(1.0, t * 1.9 - i * 0.28))
                if k <= 0.0 or k >= 1.0:
                    continue
                rr = int((10 + k * 40) * NS._fx_scale(boss))
                a = NS._alpha(190 * (1 - k))
                NS._aacircle(surface, (*P["fire_bright"], a), (hx, hy), rr, 2)
                NS._aacircle(surface, (*P["fire_glow"], int(a * 0.6)),
                             (hx, hy), int(rr * 0.7), 1)

    def _draw_khalros_charge(surface, boss, x, y, timer, rage=False):
        """Bantingan babi hutan (skill E) - merendah + afterimage 4x."""
        NS = _NS_khalros
        phase = float(getattr(boss, "pulse", 0.0) or 0.0)
        facing = getattr(boss, "direction", 1) or 1
        duration = NS.SKILL_DUR["e"]
        progress = max(0.0, min(1.0, 1 - timer / float(duration)))
        lean = int(6 + 8 * math.sin(progress * math.pi)) * facing
        bob = int(math.sin(phase * 2.2) * 2)
        portrait = bool(getattr(boss, "_portrait_hd", False))
        if not portrait:
            NS._draw_shadow(surface, x + lean, y + NS.GROUND_DY, lift=3)
            NS._draw_wild_wisps(surface, x + lean, y + 26, phase * 1.6,
                                trail=True, facing=facing, intense=True)
            # debu jalur bantingan
            for i in range(4):
                a = int(150 * (1 - i / 4.0) * (1 - progress * 0.6))
                NS._draw_dust_puff(surface, x - facing * (16 + i * 13),
                                   y + NS.GROUND_DY - i, 8 + i * 2, a,
                                   seed=i + 3)

        # SATU render rig, di-blit 5x (4 afterimage + badan). Dulu ghost
        # dirender ulang ke buffer sendiri: biayanya sama besar dengan badan
        # utama, jadi E dua kali lebih mahal dari skill lain.
        comp = None if portrait else NS._compose_body(facing, phase, "charge",
                                                      progress, boss)
        if comp is not None:
            sub, edge, offx, offy = comp
            for i in range(4):
                sub.set_alpha(int(96 - i * 20))
                surface.blit(sub, (int(x + lean) + offx
                                   - facing * (i + 1) * 11,
                                   int(y + bob) + offy))
            sub.set_alpha(255)
            ox, oy = int(x + lean) + offx, int(y + bob) + offy
            for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                surface.blit(edge, (ox + ddx, oy + ddy))
            surface.blit(sub, (ox, oy))
        else:
            NS._draw_khalros_body(surface, x + lean, y + bob, facing, phase,
                                  "charge", progress, boss=boss)

    # ===================================================================
    # RIG - KOMPOSIT (outline & lighting SETELAH penskalaan)
    # ===================================================================
    def _compose_body(facing, phase, action, attack_progress=0, boss=None):
        """Rig native 1.5x -> SCALE -> selout -> lighting -> outline buffer.

        Return ``(sub, edge, offx, offy)`` atau ``None`` bila kosong. Dipisah
        dari blit supaya pemanggil yang butuh hasil yang sama berkali-kali
        (afterimage bantingan) cukup merender SEKALI lalu men-blit 4x -
        rig penuh itu ~1,3 ms, jadi render-ulang = 2x budget kebuang.
        """
        NS = _NS_khalros
        if NS._body_buf is None:
            NS._body_buf = pygame.Surface((NS.RIG_W, NS.RIG_H),
                                          pygame.SRCALPHA)
        buf = NS._body_buf
        buf.fill((0, 0, 0, 0))
        NS._draw_khalros_body_raw(buf, NS.RIG_OX, NS.RIG_OY, facing, phase,
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
        edge = sub.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        if _lighting is not None:
            _lighting.apply_to_rig(sub, rim_add=(44, 26, 16), shade_mul=170)
        return sub, edge, int(round(lx * k)), int(round(ly * k))

    def _draw_khalros_body(surface, cx, cy, facing, phase, action,
                           attack_progress=0, boss=None):
        """Komposit badan: rig native 1.5x -> buffer -> turun ke SCALE ->
        outline siluet gelap 1 px -> pass cahaya (rim/shade) -> blit.

        Outline & lighting dikerjakan SETELAH penskalaan supaya tetap
        setebal 1 px di layar (konvensi `_finish_hd_sprite`). Return hasil
        `_compose_body` (atau None) supaya pemanggil bisa memakai ulang
        surface yang sama tanpa merender dua kali.
        """
        NS = _NS_khalros
        comp = NS._compose_body(facing, phase, action, attack_progress, boss)
        if comp is None:
            return None
        sub, edge, offx, offy = comp
        ox = int(cx) + offx
        oy = int(cy) + offy
        for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(edge, (ox + ddx, oy + ddy))
        surface.blit(sub, (ox, oy))
        return sub, ox, oy

    def _draw_khalros_body_raw(surface, cx, cy, facing, phase, action,
                               attack_progress=0, boss=None):
        """Rig masterwork v2 - Khalros Beastlord, 100% prosedural.

        Koordinat lokal ~1.5x v1: (0,0) = jangkar panggul, x maju
        (mengikuti ``facing``), y ke bawah. Puncak tanduk -102, sol
        sepatu +66, jangkar kepala -66.
        """
        NS = _NS_khalros
        f = 1 if facing >= 0 else -1
        attack = action == "attack"
        ap = max(0.0, min(1.0, attack_progress)) if attack else 0.0
        pose = NS._attack_pose(ap) if attack else None

        # ═══ gerak badan + inersia sekunder ═══
        breath = math.sin(phase * 0.72)
        lean = sway = root_y = tremble = 0
        cape_lag = beard_lag = 0.0
        stride = (0.0, 0.0, 0.0, 0.0, 0.0)
        if action == "walk":
            sw_a, sw_b, lf_a, lf_b, contact, bob = NS._stride_solver(
                "walk", phase)
            stride = (sw_a, sw_b, lf_a, lf_b, contact)
            lean = 2 * f
            root_y = int(bob)
            cape_lag = -3.0
            beard_lag = -2.0
        elif action == "attack":
            lean = int(pose["lean"]) * f
            root_y = int(pose["dip"])
            tremble = 1 if pose["tremble"] else 0
            cape_lag = -pose["lean"] * 0.55
            beard_lag = -pose["lean"] * 0.35
        elif action == "charge":
            lean = 7 * f
            root_y = 2
            cape_lag = -7.0
            beard_lag = -5.0
            stride = (0.42, -0.42, 1.5, 0.0, 0.0)
        elif action == "cast":
            lean = 1 * f
            root_y = int(breath * 1.4)
            cape_lag = math.sin(phase * 1.4) * 2.0
            beard_lag = math.sin(phase * 1.1) * 1.4
        else:
            lean = int(math.sin(phase * 0.5 + 1.1) * 1.5)
            root_y = int(breath * 1.9)
            cape_lag = math.sin(phase * 0.55) * 2.2
            beard_lag = math.sin(phase * 0.5) * 1.8
            stride = (math.sin(phase * 0.7) * 0.06,
                      -math.sin(phase * 0.7) * 0.06, 0.0, 0.0, 0.0)

        ox = int(cx) + lean + tremble
        oy = int(cy) + root_y
        rage = bool(boss is not None and getattr(boss, "active_skill", None)
                    in ("w", "r"))

        # ═══ lapisan belakang -> depan ═══
        #
        # CATATAN `late`: kapak digambar DUA kali. Pass pertama (late=False)
        # menggambar kedua lengan + kapak seperti biasa, lalu kepala menimpanya
        # - bagus untuk idle, tapi kapak yang diayun jadi "hilang" di balik
        # helm/tanduk tepat pada frame IMPACT, padahal itu frame yang paling
        # dibaca pemain. Karena itu setelah kepala ada pass kedua (late=True)
        # yang hanya menggambar sisi DEPAN (bilah + tangan penggenggam); pass
        # ini melukis ulang piksel yang sama, bukan menambah lapisan baru, jadi
        # siluetnya identik dan biayanya cuma sebagian dari satu pass.
        NS._draw_beast_cape(surface, ox, oy, f, phase, action, cape_lag)
        NS._draw_hawk_companion(surface, ox - 27 * f, oy - 50, f, phase,
                                action, rage)
        NS._draw_legs(surface, ox, oy, f, phase, action, stride)
        NS._draw_loincloth(surface, ox, oy + 6, phase, sway, action=action)
        NS._draw_torso(surface, ox, oy - 1, phase, sway, action=action,
                       rage=rage, ap=ap)
        NS._draw_shoulders(surface, ox, oy - 6, phase, f, action=action,
                           rage=rage)
        if action in ("attack", "charge"):
            NS._draw_attack_arms(surface, ox, oy, f, phase,
                                 ap if attack else 0.0, action=action)
        else:
            NS._draw_idle_arms(surface, ox, oy, f, phase, action=action)
        NS._draw_khalros_head(surface, ox, oy - 58, f, phase, action=action,
                              rage=rage, beard_lag=beard_lag, ap=ap)
        # ── pass depan: senjata di atas kepala (lihat catatan `late`) ──
        if action in ("attack", "charge"):
            NS._draw_attack_arms(surface, ox, oy, f, phase,
                                 ap if attack else 0.0, action=action,
                                 late=True)
        else:
            NS._draw_idle_arms(surface, ox, oy, f, phase, action=action,
                               late=True)

    # ===================================================================
    # ANATOMI (ruang native rig 1.5x)
    # ===================================================================
    def _draw_beast_cape(surface, cx, cy, facing, phase, action, lag=0.0):
        """Jubah kulit serigala di punggung - siluet bergerigi + mata jahit."""
        NS = _NS_khalros
        P = NS.PALETTE
        f = facing
        sway = lag + math.sin(phase * 0.65) * 2.0
        top_y = cy - 46
        hem = cy + 10 + abs(lag) * 0.6
        spine = [(cx - 4 * f, top_y),
                 (cx - 27 * f, top_y + 7),
                 (cx - 30 * f + sway, cy - 12),
                 (cx - 21 * f + sway * 1.4, hem - 4),
                 (cx - 11 * f + sway * 1.6, hem),
                 (cx + 2 * f + sway * 1.2, hem - 3),
                 (cx + 12 * f, cy - 6),
                 (cx + 16 * f, top_y + 6)]
        edge = NS._tuft_points(spine[1:-2], depth=3.4, min_len=8.0, seed=5)
        shape = [spine[0]] + edge + spine[-2:]
        NS._poly(surface, (*P["shadow_deep"], 235),
                 [(p[0] + f, p[1] + 1) for p in shape])
        NS._poly(surface, P["wolf_darkest"], shape)
        inner = [(cx + (p[0] - cx) * 0.9, cy + (p[1] - cy) * 0.9)
                 for p in shape]
        NS._poly(surface, P["wolf_dark"], inner)
        # lembar bulu di sisi cahaya - terang hanya selebar 3-4 px supaya
        # jubah tidak terbaca sebagai blob abu-abu di belakang badan
        NS._poly(surface, P["wolf_mid"],
                 [(cx - 17 * f, top_y + 10), (cx - 20 * f, cy - 10),
                  (cx - 13 * f, cy - 2), (cx - 8 * f, top_y + 12)])
        NS._poly(surface, P["wolf_light"],
                 [(cx - 14 * f, top_y + 12), (cx - 16 * f, cy - 12),
                  (cx - 12 * f, cy - 8), (cx - 10 * f, top_y + 13)])
        # dither di transisi bulu
        dith = [(cx - (8 + k * 3) * f, top_y + 14 + k * 5) for k in range(5)]
        NS._dither_dots(surface, P["wolf_high"], dith, alpha=52)
        # kepala serigala sebagai pengikat (di bahu) + mata jahit
        hx = cx + 6 * f
        NS._poly(surface, P["wolf_darkest"],
                 [(hx, top_y - 4), (hx + 9 * f, top_y - 1),
                  (hx + 6 * f, top_y + 7), (hx - 2 * f, top_y + 5)])
        NS._poly(surface, P["wolf_mid"],
                 [(hx + 1 * f, top_y - 2), (hx + 7 * f, top_y),
                  (hx + 5 * f, top_y + 5), (hx, top_y + 4)])
        NS._aacircle(surface, P["fire_mid"], (hx + 4 * f, top_y + 1), 1)
        for i in range(4):
            yy = top_y + 8 + i * 9
            NS._aaline(surface, P["bone_mid"],
                       (cx - (24 - i) * f, yy), (cx - (18 - i) * f, yy + 2), 1)

    def _draw_hawk_companion(surface, cx, cy, facing, phase, action, rage):
        """Elang pendamping di bahu belakang - hidup: kedip, regang, goyang."""
        NS = _NS_khalros
        P = NS.PALETTE
        f = facing
        u = 0.52
        blink = int(phase * 1.7) % 11 == 0
        ruffle = math.sin(phase * 1.9) * (1.6 if action == "idle" else 2.6)
        flap = max(0.0, math.sin(phase * (2.6 if rage else 1.2))) * (
            5 if rage else 2)
        # cakar mencengkeram bahu
        NS._aaline(surface, P["gold_mid"], (cx + 3 * f, cy + 8),
                   (cx + 6 * f, cy + 12), 2)
        NS._aaline(surface, P["gold_mid"], (cx - 1 * f, cy + 8),
                   (cx + 2 * f, cy + 12), 2)
        # sayap terlipat (bergerigi)
        wing = [(cx - 6 * f, cy - 3), (cx - 14 * f, cy - 1 - ruffle * .5),
                (cx - 16 * f, cy + 6), (cx - 5 * f, cy + 6)]
        NS._poly(surface, P["hawk_dark"],
                 [wing[0]] + NS._tuft_points(wing[1:], depth=1.8,
                                             min_len=4.0, seed=2) + [wing[3]])
        NS._poly(surface, P["hawk_mid"],
                 [(cx - 7 * f, cy - 1), (cx - 12 * f, cy),
                  (cx - 11 * f, cy + 4), (cx - 6 * f, cy + 4)])
        if flap > 0.4:      # regang sayap saat marah / skill
            NS._poly(surface, P["hawk_light"],
                     [(cx - 8 * f, cy - 2), (cx - 18 * f, cy - 6 - flap),
                      (cx - 14 * f, cy + 1)])
        # badan + dada
        NS._ellipse(surface, P["hawk_darkest"],
                    (cx - 5 * u * 2 - 1, cy - 6, 5 * u * 2 + 4, 13))
        NS._aacircle(surface, P["hawk_mid"], (cx, cy), 5)
        NS._aacircle(surface, P["hawk_light"], (cx - 1 * f, cy - 1), 3)
        # kepala + paruh + mata
        hx, hy = cx + 4 * f, cy - 6
        NS._aacircle(surface, P["hawk_dark"], (hx, hy), 4)
        NS._aacircle(surface, P["hawk_high"], (hx - f, hy - 1), 2)
        NS._poly(surface, P["hawk_beak"],
                 [(hx + 3 * f, hy), (hx + 7 * f, hy + 2), (hx + 3 * f, hy + 3)])
        NS._aacircle(surface, (*P["fire_hot"], 235), (hx + f, hy - 1), 1)
        if blink:
            NS._aaline(surface, P["hawk_darkest"], (hx - f, hy - 1),
                       (hx + 2 * f, hy - 1), 1)
        # tungging bulu di kepala (siluet bergerigi)
        NS._poly(surface, P["hawk_darkest"],
                 NS._tuft_points([(hx - 3 * f, hy - 4), (hx - 7 * f, hy - 7)],
                                 depth=1.8, min_len=3.0, seed=9))

    def _draw_legs(surface, cx, cy, facing, phase, action, stride):
        """Dua kaki berat: paha kuadrisep, pelindung lutut, betis bulu, boot.

        Proporsi adalah bagian yang paling mudah salah di sini: badan Khalros
        lebar (sabuk 36 px rig + pauldron), jadi kalau pahanya 16 px dia
        terbaca sebagai tong dengan dua tusuk gigi. Kaki diambil ~23 px lebar
        di paha dan boot-nya melebar ke bawah supaya ada tempat berpijak.

        Jangkar vertikal TIDAK diubah (paha cy+8, lutut cy+30, pergelangan
        cy+48, sol cy+60) - `GROUND_DY`, solver langkah, dan penyempitan
        bayangan saat melayang bergantung padanya.
        """
        NS = _NS_khalros
        P = NS.PALETTE
        f = facing
        sw_a, sw_b, lift_a, lift_b, _contact = stride
        for i, (swing, lift, back) in enumerate(((sw_a, lift_a, 1),
                                                 (sw_b, lift_b, 0))):
            # kaki belakang: lebih gelap & sedikit lebih ramping (depth cue)
            shade = P["skin_darkest"] if back else P["skin_dark"]
            mid = P["skin_dark"] if back else P["skin_mid"]
            k = 0.9 if back else 1.0
            hipx = cx + (14 - i * 28) * f * 0.46
            hipy = cy + 8
            kx = hipx + swing * 12 * f
            ky = cy + 30 - lift * 0.8
            ax = hipx + swing * 17 * f
            ay = cy + 48 - lift
            my = (ky + ay) / 2.0
            th, kn, ca, an = 11.5 * k, 8.5 * k, 9.5 * k, 6.5 * k
            pts = [(hipx - th, hipy - 3), (kx - kn, ky - 1),
                   (ax - ca, my + 2), (ax - an, ay),
                   (ax + an, ay), (ax + ca, my + 2),
                   (kx + kn, ky - 1), (hipx + th, hipy - 3)]
            NS._selout_poly(surface, (*P["shadow_deep"], 255), pts, f)
            NS._poly(surface, shade, pts)
            inner = [(cx + (p[0] - cx) * 0.87, cy + (p[1] - cy) * 0.92)
                     for p in pts]
            NS._poly(surface, mid, inner)
            # kuadrisep di sisi cahaya, meruncing ke lutut
            NS._poly(surface, P["skin_light"] if not back else P["skin_mid"],
                     [(hipx - 8 * f, hipy + 1), (hipx + 2 * f, hipy),
                      (kx + 1 * f, ky - 5), (kx - 5 * f, ky - 3)])
            NS._poly(surface, (*P["shadow_deep"], 72),
                     [(hipx + th - 3 * f, hipy + 1), (kx + kn - 2 * f, ky),
                      (ax + an, ay - 2), (ax + an - 4 * f, ay - 2),
                      (kx + kn - 7 * f, ky - 3)])
            # pelindung lutut kulit + paku kuningan
            NS._poly(surface, P["leather_darkest"],
                     [(kx - 6.5 * k, ky - 4), (kx + 6.5 * k, ky - 4),
                      (kx + 5.5 * k, ky + 4.5), (kx - 5.5 * k, ky + 4.5)])
            NS._poly(surface, P["leather_mid"],
                     [(kx - 4.5 * k, ky - 2.5), (kx + 3.5 * k, ky - 2.5),
                      (kx + 3 * k, ky + 2), (kx - 3.5 * k, ky + 2)])
            NS._aacircle(surface, P["skin_high"] if not back
                         else P["skin_light"], (int(kx - 1.5 * f),
                         int(ky - 2)), 2)
            NS._aacircle(surface, P["gold_shine"], (int(kx - 4 * f), int(ky - 1)), 1)
            # tali paha: kulit melintang + gesper emas
            sx = (hipx + kx) / 2.0
            sy = (hipy + ky) / 2.0 + 1.5
            NS._poly(surface, P["leather_darkest"],
                     [(sx - th + 1, sy - 2.5), (sx + th - 1, sy - 2.5),
                      (sx + th - 2, sy + 2.5), (sx - th + 2, sy + 2.5)])
            NS._poly(surface, P["leather_light"],
                     [(sx - th + 2.5, sy - 1.5), (sx + 1, sy - 1.5),
                      (sx + 1, sy + 0.5), (sx - th + 3.5, sy + 0.5)])
            NS._aacircle(surface, P["gold_mid"], (int(sx - 3 * f), int(sy)), 2)
            # betis berbulu + dither transisi
            fur = NS._tuft_points([(ax - ca + 1, my + 3), (ax + ca - 1, my + 3)],
                                  depth=2.4, min_len=3.4, seed=12 + i)
            NS._poly(surface, P["hair_darkest"], fur)
            NS._dither_dots(surface, P["skin_high"],
                            [(int(ax - ca + 2 + j * 3.4), int(my + 6.5))
                             for j in range(4)], alpha=70)
            # sepatu bulu: melebar ke bawah, bukan mengecil jadi titik
            boot = [(ax - an - 2.5 * k, ay - 3), (ax + an + 2.5 * k, ay - 3),
                    (ax + 10.5 * k * f, ay + 12), (ax - 8.5 * k * f, ay + 12)]
            NS._poly(surface, P["leather_darkest"], boot)
            NS._poly(surface, P["leather_mid"],
                     [(ax - an - 1 * k, ay - 1), (ax + an + 1 * k, ay - 1),
                      (ax + 9.5 * k * f, ay + 10), (ax - 8 * k * f, ay + 10)])
            NS._poly(surface, P["leather_high"],
                     [(ax - an, ay - 1.5), (ax - 1 * f, ay - 1),
                      (ax - 1 * f, ay + 8), (ax - 7 * k * f, ay + 9)])
            cuff = NS._tuft_points([(ax - an - 2, ay - 2), (ax + an + 2, ay - 2)],
                                   depth=2.8, min_len=4.2, seed=4 + i)
            NS._poly(surface, P["boar_dark"], cuff)
            # sol + cakar. Solnya TIDAK boleh ditulis `(ax - c * f)`: lebar
            # rect tidak ikut ter-mirror, jadi saat facing=-1 sol bergeser
            # seluruhnya ke satu sisi dan kelihatan seperti goresan lepas di
            # samping kaki. Jarak tumit/ujung kaki dihitung terpisah.
            heel = 8.5 * k
            toe = 10.5 * k
            sole_x = ax - (heel if f > 0 else toe)
            sole_w = heel + toe
            NS._rect(surface, P["metal_dark"], (sole_x, ay + 12, sole_w, 3))
            NS._rect(surface, P["metal_light"], (sole_x, ay + 12, sole_w, 1))
            for c in range(4):
                NS._aaline(surface, P["bone_light"],
                           (ax + (7 - c * 4.6) * f, ay + 13),
                           (ax + (10.5 - c * 4.6) * f, ay + 16), 2)
    def _draw_loincloth(surface, cx, cy, phase, sway, action="idle"):
        """Rok bulu babi hutan dengan hem robek bergerigi + sabuk tulang."""
        NS = _NS_khalros
        P = NS.PALETTE
        f = 1
        lag = math.sin(phase * 0.9) * (2.0 if action == "walk" else 0.8)
        # panel depan
        # hem sengaja berhenti di ATAS lutut: kalau panelnya panjang, kaki
        # hanya menyisakan betis + boot dan badan terbaca berjalan di atas dua
        # tusuk gigi.
        spine = [(cx - 16, cy + 2), (cx - 18, cy + 17),
                 (cx - 9, cy + 24 + lag), (cx, cy + 26 + lag * 1.2),
                 (cx + 10, cy + 23 + lag), (cx + 18, cy + 16),
                 (cx + 16, cy + 2)]
        hem = NS._tuft_points(spine[1:6], depth=3.6, min_len=6.0, seed=8)
        shape = [spine[0]] + hem + [spine[-1]]
        NS._poly(surface, (*P["shadow_deep"], 255),
                 [(p[0] + 1, p[1] + 1) for p in shape])
        NS._poly(surface, P["boar_darkest"], shape)
        NS._poly(surface, P["boar_dark"],
                 [(cx + (p[0] - cx) * 0.88, cy + (p[1] - cy) * 0.86)
                  for p in shape])
        NS._poly(surface, P["boar_mid"],
                 [(cx - 10, cy + 4), (cx + 10, cy + 4), (cx + 7, cy + 16),
                  (cx - 7, cy + 16)])
        NS._poly(surface, P["boar_light"],
                 [(cx - 6, cy + 4), (cx + 2, cy + 5), (cx + 1, cy + 14),
                  (cx - 5, cy + 13)])
        # dither transisi
        NS._dither_dots(surface, P["boar_high"],
                        [(cx - 9 + k * 5, cy + 19) for k in range(4)],
                        alpha=80)
        # dua untai bulu menggantung di sisi
        for sgn in (-1, 1):
            strand = [(cx + sgn * 16, cy + 4), (cx + sgn * 20, cy + 16 + lag),
                      (cx + sgn * 17, cy + 26 + lag * 1.4)]
            NS._poly(surface, P["leather_darkest"],
                     [(p[0] - sgn * 2, p[1]) for p in strand] +
                     [(p[0] + sgn * 2, p[1] + 1) for p in strand[::-1]])
        # sabuk: kulit + geligi + gesper emas kepala binatang
        NS._rect(surface, P["leather_darkest"], (cx - 18, cy - 5, 36, 9))
        NS._rect(surface, P["leather_light"], (cx - 17, cy - 4, 34, 4))
        NS._rect(surface, P["leather_high"], (cx - 16, cy - 4, 12, 2))
        for i in range(5):
            xx = cx - 14 + i * 7
            NS._poly(surface, P["bone_light"],
                     [(xx, cy + 3), (xx + 3, cy + 3), (xx + 1, cy + 8)])
        NS._aacircle(surface, P["gold_dark"], (cx, cy - 1), 6)
        NS._aacircle(surface, P["gold_mid"], (cx - 1, cy - 2), 5)
        NS._aacircle(surface, P["gold_light"], (cx - 2, cy - 3), 2)
        NS._aacircle(surface, P["gold_shine"], (cx - 2, cy - 3), 1)
        # taring boar di sabuk
        NS._poly(surface, P["bone_mid"], [(cx + 12, cy - 3), (cx + 18, cy + 2),
                                          (cx + 13, cy + 1)])

    def _draw_torso(surface, cx, cy, phase, sway, action="idle", rage=False,
                    ap=0.0):
        """Torso 6-band: dada bidah, otot, war paint merah, luka parut."""
        NS = _NS_khalros
        P = NS.PALETTE
        breath = math.sin(phase * 0.72) * (1.6 if action != "attack" else 0.8)
        # siluet dada lebar -> pinggang (trapezoid) + selout
        sh_y = cy - 40
        waist = cy - 2
        pts = [(cx - 29, sh_y - 3), (cx + 29, sh_y - 3),
               (cx + 23, sh_y + 16), (cx + 13, waist),
               (cx - 13, waist), (cx - 23, sh_y + 16)]
        NS._poly(surface, (*P["shadow_deep"], 255),
                 [(p[0] + 2, p[1] + 2) for p in pts])
        NS._poly(surface, P["skin_dark"], pts)
        # 6 band ramp (bayangan -> highlight) dengan hue-shift
        b2 = [(cx - 24, sh_y), (cx + 24, sh_y), (cx + 17, sh_y + 18),
              (cx - 17, sh_y + 18)]
        NS._poly(surface, P["skin_mid"], b2)
        b3 = [(cx - 16, sh_y + 3), (cx + 15, sh_y + 2), (cx + 10, sh_y + 16),
              (cx - 11, sh_y + 15)]
        NS._poly(surface, P["skin_light"], b3)
        b4 = [(cx - 12, sh_y + 4), (cx + 6, sh_y + 3), (cx + 4, sh_y + 13),
              (cx - 9, sh_y + 12)]
        NS._poly(surface, P["skin_high"], b4)
        NS._poly(surface, P["skin_shine"],
                 [(cx - 8, sh_y + 5), (cx - 1, sh_y + 4), (cx - 2, sh_y + 8),
                  (cx - 7, sh_y + 9)])
        # garis tengah dada + otot perut (VALUE, bukan outline)
        NS._aaline(surface, P["skin_darkest"], (cx - 1, sh_y + 2),
                   (cx - 1, cy - 6), 2)
        NS._aaline(surface, P["skin_dark"], (cx - 1, sh_y + 3),
                   (cx - 1, cy - 7), 1)
        for i in range(3):
            yy = sh_y + 21 + i * 5
            w = 11 - i * 2
            NS._aaline(surface, (*P["skin_darkest"], 190), (cx - w, yy),
                       (cx + w, yy), 1)
            NS._aaline(surface, (*P["skin_high"], 120), (cx - w, yy - 2),
                       (cx + w, yy - 2), 1)
        # perut bawah (nilai lebih gelap) + dither transisi
        NS._poly(surface, (*P["skin_dark"], 210),
                 [(cx - 11, cy - 8), (cx + 11, cy - 8), (cx + 8, cy - 1),
                  (cx - 8, cy - 1)])
        NS._dither_dots(surface, P["skin_mid"],
                        [(cx - 9 + k * 5, cy - 3) for k in range(4)], alpha=90)
        # war paint: telapak tangan merah di dada + garis pipi
        paint = 235 if not rage else 255
        NS._poly(surface, (*P["red_mid"], paint),
                 [(cx - 17, sh_y + 6), (cx - 8, sh_y + 4), (cx - 7, sh_y + 15),
                  (cx - 16, sh_y + 17)])
        for i in range(3):
            NS._aaline(surface, (*P["red_bright"], 190),
                       (cx - 16 + i * 3, sh_y + 6), (cx - 15 + i * 3,
                                                     sh_y + 15), 1)
        NS._poly(surface, (*P["red_mid"], paint),
                 [(cx + 8, sh_y + 5), (cx + 16, sh_y + 7), (cx + 15,
                                                             sh_y + 16),
                  (cx + 9, sh_y + 14)])
        # silang dada (harness kulit tipis ber-jahitan)
        NS._aaline(surface, (*P["leather_darkest"], 235), (cx - 23, sh_y - 1),
                   (cx + 13, cy - 5), 4)
        NS._aaline(surface, (*P["leather_mid"], 235), (cx - 23, sh_y - 1),
                   (cx + 13, cy - 5), 2)
        NS._aaline(surface, (*P["leather_darkest"], 225), (cx + 23, sh_y - 1),
                   (cx - 12, cy - 4), 4)
        NS._aaline(surface, (*P["leather_light"], 210), (cx + 22, sh_y - 1),
                   (cx - 12, cy - 4), 1)
        for i in range(5):
            t = i / 5.0
            NS._aacircle(surface, (*P["leather_high"], 180),
                         (int(cx - 24 + t * 38), int(sh_y - 2 + t * 36)), 1)
        # kalung taring di leher
        for i in range(5):
            tx = cx - 10 + i * 5
            NS._poly(surface, P["bone_light"],
                     [(tx, sh_y + 1), (tx + 3, sh_y + 1), (tx + 1, sh_y + 6)])
        NS._aacircle(surface, P["bone_shine"], (cx + 2, sh_y + 2), 1)
        # bara primal menempel di dada saat skill
        if rage or action == "attack":
            glow = 200 if not rage else 255
            for i in range(3):
                t = (phase * 0.6 + i * 0.33) % 1.0
                gx = cx + (NS._hash01(i * 7.7) - 0.5) * 26
                gy = sh_y + 20 - t * 26
                NS._aacircle(surface, (*P["fire_bright"], int(glow * (1 - t))),
                             (int(gx), int(gy)), 2 if i % 2 else 1)
        # bekas luka (garis pucat diagonal)
        NS._aaline(surface, (*P["skin_shine"], 150), (cx + 4, sh_y + 8),
                   (cx + 18, sh_y + 18), 2)
        NS._aaline(surface, (*P["skin_darkest"], 150), (cx + 4, sh_y + 10),
                   (cx + 17, sh_y + 20), 1)

    def _draw_shoulders(surface, cx, cy, phase, facing=1, action="idle",
                        rage=False):
        """Pauldron: bahu depan = bulu babi hutan berduri, belakang = besi."""
        NS = _NS_khalros
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        sh_y = cy - 36
        for side in (1, -1):
            front = side > 0
            bx = cx + side * 27 * f * (1 if front else 0.94)
            by = sh_y + (0 if front else 1)
            if front:
                # bulu babi + duri tulang
                spike = [(bx - 11, by - 5), (bx + 10, by - 8),
                         (bx + 14, by + 3), (bx + 6, by + 11),
                         (bx - 10, by + 8)]
                edge = NS._tuft_points(spike[1:4], depth=3.0, min_len=5.0,
                                       seed=12)
                NS._poly(surface, (*P["shadow_deep"], 255),
                         [(p[0] + 2, p[1] + 2) for p in spike])
                NS._poly(surface, P["boar_dark"], spike)
                NS._poly(surface, P["boar_mid"],
                         [(bx + (p[0] - bx) * 0.8, by + (p[1] - by) * 0.78)
                          for p in spike[:3] + edge])
                NS._poly(surface, P["boar_light"],
                         [(bx - 6, by - 3), (bx + 6, by - 5),
                          (bx + 4, by + 1), (bx - 5, by + 2)])
                NS._poly(surface, P["bone_light"],
                         [(bx + 4, by - 7), (bx + 12, by - 17),
                          (bx + 9, by - 6)])
                NS._poly(surface, P["bone_mid"],
                         [(bx - 5, by - 5), (bx + 1, by - 14),
                          (bx - 1, by - 4)])
                NS._aacircle(surface, P["bone_shine"], (bx + 10, by - 14), 1)
                NS._dither_dots(surface, P["boar_high"],
                                [(bx - 7 + k * 4, by + 6) for k in range(4)],
                                alpha=80)
                # rivet emas
                for i in range(3):
                    NS._aacircle(surface, P["gold_mid"],
                                 (int(bx - 5 + i * 6), int(by + 6)), 2)
                    NS._aacircle(surface, P["gold_shine"],
                                 (int(bx - 5.5 + i * 6), int(by + 5)), 1)
            else:
                # pelat besi bertingkat
                plate = [(bx - 12, by - 4), (bx + 9, by - 7),
                         (bx + 12, by + 4), (bx + 3, by + 11),
                         (bx - 11, by + 8)]
                NS._poly(surface, (*P["shadow_deep"], 255),
                         [(p[0] + 2, p[1] + 2) for p in plate])
                NS._poly(surface, P["metal_dark"], plate)
                NS._poly(surface, P["metal_mid"],
                         [(bx + (p[0] - bx) * 0.82, by + (p[1] - by) * 0.8)
                          for p in plate])
                NS._poly(surface, P["metal_light"],
                         [(bx - 8, by - 2), (bx + 4, by - 4),
                          (bx + 3, by + 2), (bx - 7, by + 3)])
                NS._poly(surface, P["metal_shine"],
                         [(bx - 5, by - 2), (bx - 1, by - 3),
                          (bx - 2, by + 1)])
                for i in range(3):
                    NS._aacircle(surface, P["metal_darkest"],
                                 (int(bx - 6 + i * 6), int(by + 6)), 2)
                    NS._aacircle(surface, P["metal_shine"],
                                 (int(bx - 6.5 + i * 6), int(by + 5)), 1)
            if rage:
                NS._aacircle(surface, (*P["fire_bright"], 90),
                             (int(bx), int(by)), 9)

    def _draw_khalros_head(surface, cx, cy, facing, phase, action="idle",
                           rage=False, beard_lag=0.0, ap=0.0):
        """Kepala: tengkorak, rahang bergeraut, janggut berkepang, helm.

        ``cy`` = pusat kepala (ruang native). Mata menyala di balik celah
        helm; kedip & geram mengikuti fase.
        """
        NS = _NS_khalros
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        growl = 1.0 if action == "attack" else (0.6 if rage else 0.0)
        tilt = -2 if action == "attack" else 0

        # ── leher ──
        NS._poly(surface, P["skin_darkest"],
                 [(cx - 8, cy + 8), (cx + 8, cy + 8), (cx + 10, cy + 18),
                  (cx - 10, cy + 18)])
        NS._poly(surface, P["skin_dark"],
                 [(cx - 7, cy + 9), (cx + 6, cy + 9), (cx + 8, cy + 16),
                  (cx - 8, cy + 16)])

        # ── tengkorak (6 band + selout) ──
        skull = [(cx - 12 * f + 1, cy - 10 + tilt), (cx + 12 * f, cy - 12 + tilt),
                 (cx + 14 * f, cy - 1 + tilt), (cx + 9 * f, cy + 10 + tilt),
                 (cx - 6 * f, cy + 12 + tilt), (cx - 13 * f, cy + 2 + tilt)]
        NS._poly(surface, (*P["shadow_deep"], 255),
                 [(p[0] + f, p[1] + 2) for p in skull])
        NS._poly(surface, P["skin_dark"], skull)
        NS._poly(surface, P["skin_mid"],
                 [(cx + (p[0] - cx) * 0.86, cy + (p[1] - cy) * 0.84)
                  for p in skull])
        NS._poly(surface, P["skin_light"],
                 [(cx - 9 * f, cy - 7 + tilt), (cx + 7 * f, cy - 9 + tilt),
                  (cx + 5 * f, cy + 2 + tilt), (cx - 8 * f, cy + 3 + tilt)])
        NS._poly(surface, P["skin_high"],
                 [(cx - 6 * f, cy - 6 + tilt), (cx + 1 * f, cy - 7 + tilt),
                  (cx + 1, cy - 1 + tilt), (cx - 5 * f, cy + 0 + tilt)])
        NS._aacircle(surface, P["skin_shine"], (int(cx - 3 * f),
                                                int(cy - 5 + tilt)), 2)

        # ── war paint pipi ──
        for i in range(3):
            NS._aaline(surface, (*P["red_bright"], 210),
                       (cx - 8 * f + i * 3 * f, cy + 2 + tilt),
                       (cx - 6 * f + i * 3 * f, cy + 7 + tilt), 2)

        # ── rahang & geretan gigi (makin garang saat serang) ──
        jaw_drop = int(1 + growl * 2)
        NS._poly(surface, P["skin_darkest"],
                 [(cx + 2 * f, cy + 5 + tilt), (cx + 12 * f, cy + 3 + tilt),
                  (cx + 11 * f, cy + 9 + jaw_drop + tilt),
                  (cx + 2 * f, cy + 11 + jaw_drop + tilt)])
        teeth = [(cx + 4 * f, cy + 6 + tilt), (cx + 10 * f, cy + 5 + tilt)]
        for i, (tx, ty) in enumerate(teeth):
            NS._poly(surface, P["bone_light"],
                     [(tx, ty), (tx + 2 * f, ty), (tx + f, ty + 3)])
        if growl:
            NS._poly(surface, (*P["red_hot"], 160),
                     [(cx + 3 * f, cy + 7 + tilt), (cx + 11 * f, cy + 6 + tilt),
                      (cx + 10 * f, cy + 8 + tilt), (cx + 3 * f, cy + 9 + tilt)])
        # hidung
        NS._aaline(surface, P["skin_darkest"], (cx + 11 * f, cy - 2 + tilt),
                   (cx + 13 * f, cy + 3 + tilt), 3)
        NS._aacircle(surface, P["skin_high"], (int(cx + 12 * f),
                                               int(cy - 3 + tilt)), 1)

        # ── janggut berkepang, tepi bergerigi, ikut inersia ──
        bL = beard_lag
        braid = [(cx + 1 * f, cy + 9 + tilt),
                 (cx + 11 * f, cy + 12 + tilt),
                 (cx + 8 * f + bL, cy + 22 + tilt),
                 (cx + 2 * f + bL * 1.4, cy + 30 + tilt),
                 (cx - 6 * f + bL * 1.2, cy + 24 + tilt),
                 (cx - 9 * f, cy + 12 + tilt)]
        edge = NS._tuft_points(braid[2:5], depth=2.8, min_len=4.5, seed=3)
        NS._poly(surface, P["hair_darkest"],
                 [braid[0], braid[1]] + edge + [braid[4], braid[5]])
        NS._poly(surface, P["hair_dark"],
                 [(cx + (p[0] - cx) * 0.88, cy + (p[1] - cy) * 0.9)
                  for p in braid])
        NS._poly(surface, P["hair_mid"],
                 [(cx - 2 * f, cy + 13 + tilt), (cx + 6 * f, cy + 14 + tilt),
                  (cx + 4 * f + bL, cy + 24 + tilt), (cx - 3 * f + bL, cy + 22 + tilt)])
        # jahitan kepang + cincin emas di ujung
        for i in range(3):
            yy = cy + 16 + i * 5 + tilt
            NS._aaline(surface, P["hair_high"], (cx - 4 * f + bL * i / 2, yy),
                       (cx + 6 * f + bL * i / 2, yy + 2), 1)
        NS._aacircle(surface, P["gold_mid"], (int(cx + 2 * f + bL * 1.2),
                                             int(cy + 29 + tilt)), 3)
        NS._aacircle(surface, P["gold_shine"], (int(cx + 1.5 * f + bL * 1.2),
                                               int(cy + 28 + tilt)), 1)

        # ── kumis & brew (menumpuk di atas janggut) ──
        NS._poly(surface, P["hair_darkest"],
                 [(cx + 6 * f, cy + 1 + tilt), (cx + 16 * f, cy + 2 + tilt),
                  (cx + 13 * f, cy + 7 + tilt), (cx + 5 * f, cy + 5 + tilt)])
        NS._poly(surface, P["hair_mid"],
                 [(cx + 7 * f, cy + 2 + tilt), (cx + 14 * f, cy + 3 + tilt),
                  (cx + 12 * f, cy + 5 + tilt)])

        # ── helm bertanduk ──
        NS._draw_helm(surface, cx, cy + tilt, f, phase, action=action,
                      rage=rage)

        # ── mata menyala di celah helm (digambar setelah helm) ──
        blink = int(phase * 1.55) % 13 == 0 and not growl
        eye_x, eye_y = cx + 9 * f, cy - 3 + tilt
        if blink:
            NS._aaline(surface, P["metal_darkest"], (eye_x - 3, eye_y),
                       (eye_x + 3, eye_y), 2)
        else:
            col = P["eye_hot"] if (growl or rage) else P["eye_bright"]
            NS._aacircle(surface, (*P["eye_dark"], 235), (eye_x, eye_y), 4)
            NS._aacircle(surface, (*col, 255), (eye_x, eye_y), 3)
            NS._aacircle(surface, (*P["fire_glow"], 200),
                         (eye_x - 1 * f, eye_y - 1), 2)
            NS._aacircle(surface, P["white"], (eye_x - f, eye_y - 1), 1)
            # seberkas cahaya mata
            NS._aaline(surface, (*col, 110), (eye_x, eye_y),
                       (eye_x + 6 * f, eye_y + 1), 2)

    def _draw_helm(surface, cx, cy, facing=1, phase=0.0, action="idle",
                   rage=False):
        """Helm tempur: kubah baja ber-ring, linggis hidung, buah bulu,
        dua taring babi hutan melengkung, dan bulu elang di punggungan."""
        NS = _NS_khalros
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        crown = cy - 10
        # dome baja 5 band
        dome = [(cx - 13, crown + 2), (cx - 10, crown - 6), (cx, crown - 9),
                (cx + 10, crown - 6), (cx + 13, crown + 2), (cx + 11, crown + 6),
                (cx - 11, crown + 6)]
        NS._poly(surface, (*P["shadow_deep"], 255),
                 [(p[0] + f, p[1] + 2) for p in dome])
        NS._poly(surface, P["metal_dark"], dome)
        NS._poly(surface, P["metal_mid"],
                 [(cx + (p[0] - cx) * 0.84, cy + (p[1] - cy) * 0.84)
                  for p in dome])
        NS._poly(surface, P["metal_light"],
                 [(cx - 10, crown - 3), (cx - 1, crown - 7), (cx - 2, crown + 3),
                  (cx - 9, crown + 4)])
        NS._poly(surface, P["metal_shine"],
                 [(cx - 7, crown - 3), (cx - 3, crown - 5), (cx - 4, crown + 0),
                  (cx - 7, crown + 1)])
        # palang tengah + rivet
        NS._aaline(surface, P["metal_darkest"], (cx, crown - 8), (cx, crown + 6), 3)
        NS._aaline(surface, P["metal_light"], (cx - 1, crown - 7), (cx - 1,
                                                                    crown + 5), 1)
        for i in range(5):
            rx = cx - 10 + i * 5
            NS._aacircle(surface, P["metal_darkest"], (rx, crown + 6), 2)
            NS._aacircle(surface, P["gold_mid"], (rx - 1, crown + 5), 1)
            NS._aacircle(surface, P["gold_shine"], (rx - 1, crown + 5), 1)
        # linggis hidung (nose guard)
        NS._poly(surface, P["metal_dark"],
                 [(cx + 8 * f, crown + 5), (cx + 14 * f, crown + 6),
                  (cx + 13 * f, crown + 14), (cx + 8 * f, crown + 12)])
        NS._poly(surface, P["metal_light"],
                 [(cx + 9 * f, crown + 7), (cx + 12 * f, crown + 8),
                  (cx + 11 * f, crown + 11), (cx + 9 * f, crown + 10)])
        NS._aacircle(surface, P["metal_edge"], (int(cx + 11 * f),
                                                int(crown + 8)), 1)
        # trim bulu di pinggiran helm (bergerigi)
        fur_spine = [(cx - 14, crown + 4), (cx - 6, crown + 7),
                     (cx + 6, crown + 7), (cx + 14, crown + 4)]
        NS._poly(surface, P["boar_darkest"],
                 NS._tuft_points(fur_spine, depth=3.2, min_len=5.0, seed=17))
        NS._poly(surface, P["boar_mid"],
                 [(cx - 12, crown + 4), (cx + 12, crown + 4),
                  (cx + 6, crown + 7), (cx - 6, crown + 7)])
        NS._dither_dots(surface, P["boar_high"],
                        [(cx - 10 + k * 5, crown + 5) for k in range(5)],
                        alpha=90)
        # dua taring babi sebagai tanduk (ivory 3 band + bayangan)
        for sgn in (-1, 1):
            bx = cx + sgn * 12
            by = crown - 2
            tipx, tipy = bx + sgn * 17, by - 22
            midx, midy = bx + sgn * 11, by - 10
            horn = [(bx - sgn * 2, by + 2), (midx - sgn, midy + 2),
                    (tipx, tipy), (tipx + sgn * 3, tipy + 2),
                    (midx + 3 * sgn, midy + 5), (bx + sgn * 4, by + 5)]
            NS._poly(surface, (*P["shadow_deep"], 255),
                     [(p[0] + f, p[1] + 2) for p in horn])
            NS._poly(surface, P["bone_dark"], horn)
            NS._poly(surface, P["bone_mid"],
                     [(bx + (p[0] - bx) * 0.8, by + (p[1] - by) * 0.86)
                      for p in horn])
            NS._poly(surface, P["bone_light"],
                     [(bx + sgn * 1, by), (midx + sgn, midy + 1),
                      (tipx + sgn, tipy + 1), (tipx - sgn, tipy + 3),
                      (midx - sgn * 2, midy + 4)])
            NS._aacircle(surface, P["bone_shine"], (int(tipx), int(tipy + 1)), 1)
            # guratan taring
            for i in range(2):
                NS._aaline(surface, (*P["bone_darkest"], 190),
                           (bx + sgn * (3 + i * 3), by - i * 5 - 2),
                           (bx + sgn * (5 + i * 3), by - i * 5 + 1), 1)
        # bulu elang di punggungan (bergoyang)
        sway = math.sin(phase * 1.4) * 2
        plume = [(cx - 2 * f, crown - 8), (cx - 10 * f + sway, crown - 20),
                 (cx - 16 * f + sway * 1.5, crown - 16)]
        NS._aaline(surface, P["hawk_dark"], plume[0], plume[1], 3)
        NS._aaline(surface, P["hawk_mid"], plume[0], plume[1], 2)
        NS._poly(surface, P["hawk_light"],
                 [(plume[1][0], plume[1][1]),
                  (plume[2][0], plume[2][1] + 2),
                  (plume[2][0] + 3 * f, plume[2][1])])
        NS._poly(surface, P["hawk_high"],
                 [(plume[1][0], plume[1][1]), (plume[2][0] + f, plume[2][1] + 1),
                  (plume[2][0] + 2 * f, plume[2][1] + 3)])
        if rage:
            NS._glow(surface, cx, crown - 2, 22, P["fire_mid"], 90)

    # ===================================================================
    # LENGAN + KAPAK
    # ===================================================================
    def _draw_arm_segment(surface, x1, y1, x2, y2, wrap=True, bulk=9):
        """Segmen lengan: 3 band ramp + lilitan kulit (v1 signature)."""
        NS = _NS_khalros
        P = NS.PALETTE
        dx, dy = x2 - x1, y2 - y1
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        a = (x1 + nx * bulk, y1 + ny * bulk)
        b = (x1 - nx * bulk, y1 - ny * bulk)
        c = (x2 - nx * bulk * 0.62, y2 - ny * bulk * 0.62)
        d = (x2 + nx * bulk * 0.62, y2 + ny * bulk * 0.62)
        NS._poly(surface, (*P["shadow_deep"], 255),
                 [(p[0] + 1, p[1] + 1) for p in (a, b, c, d)])
        NS._poly(surface, P["skin_dark"], [a, b, c, d])
        inner = [((a[0] + x1) / 2, (a[1] + y1) / 2),
                 ((b[0] + x1) / 2, (b[1] + y1) / 2),
                 ((c[0] + x2) / 2, (c[1] + y2) / 2),
                 ((d[0] + x2) / 2, (d[1] + y2) / 2)]
        NS._poly(surface, P["skin_mid"], inner)
        NS._poly(surface, P["skin_light"],
                 [(inner[0][0] * .5 + inner[3][0] * .5,
                   inner[0][1] * .5 + inner[3][1] * .5 - 1),
                  inner[0], inner[1],
                  (inner[1][0] + nx * 2, inner[1][1] + ny * 2)])
        if wrap:
            # lilitan kulit di lengan bawah (3 gelang + jahitan)
            for i in range(3):
                t = 0.42 + i * 0.16
                px, py = x1 + dx * t, y1 + dy * t
                NS._aaline(surface, P["leather_darkest"],
                           (px + nx * bulk * .75, py + ny * bulk * .75),
                           (px - nx * bulk * .75, py - ny * bulk * .75), 3)
                NS._aaline(surface, P["leather_light"],
                           (px + nx * bulk * .7, py + ny * bulk * .7 - 1),
                           (px - nx * bulk * .7, py - ny * bulk * .7 - 1), 1)
                NS._aacircle(surface, P["gold_mid"], (int(px + nx * 4),
                                                     int(py + ny * 4)), 1)

    def _draw_hand(surface, x, y, facing=1, grip=False):
        """Kekepalkan tangan: 3 band + buku-buku jari + cincin."""
        NS = _NS_khalros
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        NS._ellipse(surface, (*P["shadow_deep"], 255), (x - 6 + f, y - 5 + 1, 12, 11))
        NS._aacircle(surface, P["skin_dark"], (x, y), 6)
        NS._aacircle(surface, P["skin_mid"], (x - 1, y - 1), 5)
        NS._aacircle(surface, P["skin_light"], (x - 2, y - 2), 3)
        for i in range(3):
            NS._aacircle(surface, P["skin_darkest"], (x + 3 * f, y - 3 + i * 3), 1)
            NS._aacircle(surface, P["skin_high"], (x + 2 * f, y - 4 + i * 3), 1)
        if grip:
            NS._aacircle(surface, P["gold_light"], (x + 4 * f, y + 2), 2)
            NS._aacircle(surface, P["gold_shine"], (x + 4 * f, y + 1), 1)

    def _axe_blade_shape(cx, cy, ang, size=1.0):
        """Titik bilah kapak (native) untuk sudut ``ang`` di (cx,cy)."""
        ca, sa = math.cos(ang), math.sin(ang)
        nx, ny = -sa, ca
        bx = cx + ca * _NS_khalros.AXE_HANDLE * size
        by = cy + sa * _NS_khalros.AXE_HANDLE * size
        L = _NS_khalros.AXE_BLADE * size
        return bx, by, nx, ny, L

    def _draw_axe_swinging(surface, hx, hy, facing, angle, size=1.0,
                           hot=0.0):
        """Kapak tempur berputar di tangan: gagang + bilah bergerigi 5 band.

        ``hot`` 0..1 = bilah membara (state rage / frame impact).

        ATURAN CERMIN: yang berubah saat `facing` balik adalah HADAP, bukan
        atas-bawah. `ang = angle * f` membalik sumbu Y (kapak idle yang harusnya
        menengadah ke kiri malah menukik ke kanan bawah) - jadi arah bilah
        dihitung dari (cos*face, sin) dan sudutnya diambil dari vektor itu.
        Konvensi ini sama dengan `_axe_tip_local`, sehingga trail ayunan dan
        bintang impact mendarat DI BILAH, bukan di udara.
        """
        NS = _NS_khalros
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        ca0, sa0 = math.cos(angle) * f, math.sin(angle)
        ang = math.atan2(sa0, ca0)
        bx, by, nx, ny, L = NS._axe_blade_shape(hx, hy, ang, size)
        tipx, tipy = bx + math.cos(ang) * L, by + math.sin(ang) * L
        # gagang kulit: 3 band + lilitan
        NS._aaline(surface, P["leather_darkest"],
                   (hx - math.cos(ang) * 8 * size, hy - math.sin(ang) * 8 * size),
                   (bx, by), max(3, int(5 * size)))
        NS._aaline(surface, P["leather_mid"],
                   (hx - math.cos(ang) * 7 * size, hy - math.sin(ang) * 7 * size),
                   (bx, by), max(2, int(3 * size)))
        NS._aaline(surface, P["leather_high"],
                   (hx - math.cos(ang) * 7 * size, hy - math.sin(ang) * 7 * size - 1),
                   (bx - nx * 1.5, by - ny * 1.5), 1)
        for i in range(3):
            t = 0.2 + i * 0.22
            px = hx - math.cos(ang) * 8 * size + (bx - hx + math.cos(ang) * 8 * size) * t
            py = hy - math.sin(ang) * 8 * size + (by - hy + math.sin(ang) * 8 * size) * t
            NS._aaline(surface, P["leather_light"], (px + nx * 2, py + ny * 2),
                       (px - nx * 2, py - ny * 2), 1)
        # bilah: kipas bergerigi dengan notch (siluet khas)
        half = L * 0.52
        outer = [(bx + nx * half * 0.35, by + ny * half * 0.35),
                 (bx + math.cos(ang) * L * 0.5 + nx * half,
                  by + math.sin(ang) * L * 0.5 + ny * half),
                 (tipx + nx * half * 0.55, tipy + ny * half * 0.55),
                 (tipx - nx * half * 0.45, tipy - ny * half * 0.45),
                 (bx + math.cos(ang) * L * 0.45 - nx * half * 0.85,
                  by + math.sin(ang) * L * 0.45 - ny * half * 0.85),
                 (bx - nx * half * 0.3, by - ny * half * 0.3)]
        edge = NS._tuft_points(outer[1:4], depth=2.4 * size, min_len=5.0, seed=6)
        shape = [outer[0]] + edge + outer[3:]
        NS._poly(surface, (*P["shadow_deep"], 255),
                 [(p[0] + f, p[1] + 2) for p in shape])
        NS._poly(surface, P["metal_dark"], shape)
        NS._poly(surface, P["metal_mid"],
                 [(bx + (p[0] - bx) * 0.86, by + (p[1] - by) * 0.88)
                  for p in shape])
        NS._poly(surface, P["metal_light"],
                 [(bx + (p[0] - bx) * 0.66, by + (p[1] - by) * 0.68)
                  for p in shape[:3]])
        # fuller gelap + tepi tajam
        NS._aaline(surface, P["metal_darkest"],
                   (bx + math.cos(ang) * L * 0.15, by + math.sin(ang) * L * 0.15),
                   (tipx - nx * half * 0.1, tipy - ny * half * 0.1),
                   max(2, int(3 * size)))
        NS._aaline(surface, P["metal_shine"], outer[1], outer[2],
                   max(1, int(2 * size)))
        NS._aaline(surface, P["metal_edge"],
                   (outer[2][0] - nx, outer[2][1] - ny),
                   (outer[3][0] - nx, outer[3][1] - ny), 1)
        # paku emas + mata kapak (specular cluster)
        NS._aacircle(surface, P["gold_mid"],
                     (int(bx + math.cos(ang) * 4 * size),
                      int(by + math.sin(ang) * 4 * size)), max(2, int(3 * size)))
        NS._aacircle(surface, P["gold_shine"],
                     (int(bx + math.cos(ang) * 3.5 * size),
                      int(by + math.sin(ang) * 3.5 * size - 1)),
                     max(1, int(1.4 * size)))
        # membara saat rage / impact
        if hot > 0.02:
            a = NS._alpha(230 * hot)
            NS._aaline(surface, (*P["fire_bright"], a), outer[1], outer[2],
                       max(1, int(3 * size)))
            NS._aacircle(surface, (*P["fire_hot"], a),
                         (int(tipx), int(tipy)), max(2, int(4 * size)))
            NS._aacircle(surface, (*P["fire_glow"], a),
                         (int(tipx), int(tipy)), max(1, int(2 * size)))
        return tipx, tipy

    def _draw_axe_held(surface, hx, hy, side, phase, hot=0.0):
        """Kapak kedua yang tersandang di punggung (side = -1 belakang)."""
        NS = _NS_khalros
        P = NS.PALETTE
        # -1.32 rad = hampir tegak: yang kelihatan hanya kepala bilah di atas
        # bahu. Kalau sudutnya landai, gagang kapak cadangan jadi tombak yang
        # melebarkan siluet 13 px dan mencuri tempat dari elang.
        ang = -1.32 + math.sin(phase * 0.5) * 0.03
        f = 1 if side >= 0 else -1
        # cermin horizontal (lihat `_draw_axe_swinging`); seluruh jarak
        # sepanjang sumbu bilah dikalikan f supaya bentuknya ikut terbalik
        ca, sa = math.cos(ang) * f, math.sin(ang)
        ang = math.atan2(sa, ca)
        bx, by, nx, ny, L = NS._axe_blade_shape(hx, hy, ang, 0.68)
        NS._aaline(surface, P["leather_darkest"],
                   (hx - ca * 10, hy - sa * 10), (bx, by), 4)
        NS._aaline(surface, P["leather_mid"],
                   (hx - ca * 9, hy - sa * 9), (bx, by), 2)
        shape = [(bx + nx * 6, by + ny * 6), (bx + f * L * 0.5, by - 4),
                 (bx + f * L * 0.75, by + 3), (bx + nx * 2, by + ny * 8),
                 (bx - nx * 5, by - ny * 5)]
        NS._poly(surface, P["metal_darkest"], shape)
        NS._poly(surface, P["metal_mid"],
                 [(bx + (p[0] - bx) * 0.8, by + (p[1] - by) * 0.8)
                  for p in shape])
        NS._poly(surface, P["metal_light"],
                 [(bx + f, by - 3), (bx + f * L * 0.6, by - 2),
                  (bx + f * L * 0.5, by + 1)])
        NS._aacircle(surface, P["metal_shine"],
                     (int(bx + f * L * 0.55), int(by - 1)), 1)
        if hot > 0.02:
            NS._aacircle(surface, (*P["fire_bright"], NS._alpha(180 * hot)),
                         (int(bx + f * L * 0.5), int(by)), 4)

    def _draw_idle_arms(surface, cx, cy, facing, phase, action="idle",
                        late=False):
        """Dua lengan: depan memegang kapak tempur, belakang kapak cadangan.

        ``cx/cy`` = jangkar panggul rig; bahu di cy-42. ``late=True`` =
        second pass dari `_draw_khalros_body_raw` yang mengulang sisi DEPAN
        saja (kapak idle di atas kepala/tanduk) - lihat catatan `late` di
        sana; bagian belakang sengaja tidak dilukis ulang supaya janggut dan
        helm tetap menutupi bahu.
        """
        NS = _NS_khalros
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        sway = int(math.sin(phase * 0.7) * 1.6)
        sh_y = cy - 42
        if late:
            # pass depan saja - lihat `_draw_khalros_body_raw`
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
        # lengan belakang (lebih gelap, di belakang badan)
        be_sx = cx - 22 * f
        be_hx = be_sx - 8 * f
        be_hy = sh_y + 30 + sway
        NS._draw_arm_segment(surface, be_sx, sh_y + 4, be_hx - 2 * f, be_hy,
                             bulk=8)
        NS._draw_hand(surface, int(be_hx - 2 * f), int(be_hy), f)
        NS._draw_axe_held(surface, int(be_hx - 1 * f), int(be_hy - 4), -f,
                          phase)
        # lengan depan -> grip kapak (sinkron `_axe_grip_local`)
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

    def _draw_attack_arms(surface, cx, cy, facing, phase, progress,
                          action="attack", late=False):
        """Lengan saat ayunan: keyframe `arm_a` menggerakkan grip + kapak.

        ``late=True`` = pass depan untuk bilah + tangan penggenggam saja,
        supaya kepala tidak menutupi kapak pada frame IMPACT (lihat catatan
        `late` di `_draw_khalros_body_raw`).
        """
        NS = _NS_khalros
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        pose = NS._attack_pose(progress)
        sh_y = cy - 42
        gx, gy = NS._axe_grip_local(action, phase, progress, f)
        fx, fy = cx + gx * f, cy + gy
        if late:
            # pass depan: bilah tidak pernah hilang di balik helm/tanduk
            NS._draw_axe_swinging(surface, fx, fy, f, pose["arm_a"] + 0.72,
                                  1.0,
                                  hot=pose["impact"] if action == "attack"
                                  else 0.55)
            NS._draw_hand(surface, int(fx), int(fy), f, grip=True)
            return
        fe_sx = cx + 21 * f
        elbow = ((fe_sx + fx) / 2 + 4 * f, (sh_y + fy) / 2 + 4)
        # lengan belakang mengayuh ke belakang untuk keseimbangan
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
        # ketegangan otot bergetar di fase tension
        if pose["tremble"]:
            NS._aacircle(surface, (*P["skin_shine"], 90), (int(fe_sx),
                                                           int(sh_y + 2)), 3)

    def _draw_deltoid(surface, x, y, facing=1):
        """Bahu berotot: 3 band + sorot cahaya kiri-atas."""
        NS = _NS_khalros
        P = NS.PALETTE
        f = 1 if facing >= 0 else -1
        NS._aacircle(surface, (*P["shadow_deep"], 235), (x + f, y + 1), 9)
        NS._aacircle(surface, P["skin_dark"], (x, y), 9)
        NS._aacircle(surface, P["skin_mid"], (x - 1, y - 1), 7)
        NS._aacircle(surface, P["skin_light"], (x - 2 * f, y - 3), 4)
        NS._aacircle(surface, P["skin_high"], (x - 2 * f, y - 3), 2)
        NS._aaline(surface, P["skin_darkest"], (x - 6 * f, y + 3),
                   (x + 5 * f, y + 6), 2)

    # ===================================================================
    # SMEME AYUNAN + BENTURAN (canvas fallback; lapisan hidup memakainya
    # lewat geometri yang sama -> trail di layar)
    # ===================================================================
    def _draw_axe_swing_arc(surface, x, y, facing, progress):
        """Smear sabit baja 3 lapis + tepi menyala, mengikuti busur kapak."""
        NS = _NS_khalros
        P = NS.PALETTE
        if progress < 0.26 or progress > 0.80:
            return
        if progress < 0.5:
            vis = (progress - 0.26) / 0.24
        else:
            vis = 1.0 - (progress - 0.5) / 0.30
        vis = max(0.0, min(1.0, vis))
        f = 1 if facing >= 0 else -1
        R = int(56 * NS.SCALE) + 10
        arc = pygame.Surface((R * 2 + 12, R * 2 + 12), pygame.SRCALPHA)
        acx = acy = R + 6
        sweep = min(1.0, (progress - 0.22) / 0.36)
        a_end = (-2.05 + sweep * 3.1)
        n = 16
        for band, (col, rr, wid) in enumerate((
                (P["metal_dark"], R, 10),
                (P["metal_light"], R - 4, 6),
                (P["fire_bright"], R - 8, 3))):
            pts_o, pts_i = [], []
            for i in range(n + 1):
                t = i / n
                ang = a_end - t * 1.95
                w = wid * (1.0 - t * 0.72)
                ca = math.cos(ang) * f
                sa = math.sin(ang)
                pts_o.append((acx + ca * (rr + w), acy + sa * (rr + w)))
                pts_i.append((acx + ca * (rr - w), acy + sa * (rr - w)))
            NS._poly(arc, (*col, int((140 - band * 28) * vis)),
                     pts_o + pts_i[::-1])
        # leading edge putih
        ca, sa = math.cos(a_end) * f, math.sin(a_end)
        NS._aaline(arc, (*P["metal_edge"], int(225 * vis)),
                   (acx + ca * (R - 12), acy + sa * (R - 12)),
                   (acx + ca * (R + 8), acy + sa * (R + 8)), 3)
        NS._aacircle(arc, (*P["fire_glow"], int(235 * vis)),
                     (int(acx + ca * R), int(acy + sa * R)), 5)
        NS._aacircle(arc, (*P["fire_white"], int(255 * vis)),
                     (int(acx + ca * R), int(acy + sa * R)), 2)
        # bara terlempar dari busur (deterministik)
        for i in range(5):
            t = 0.15 + 0.16 * i
            ang = a_end - t * 1.9
            rr = R * (0.9 + NS._hash01(i * 13) * 0.25)
            ex = acx + math.cos(ang) * f * rr
            ey = acy + math.sin(ang) * rr
            NS._draw_ember(arc, int(ex), int(ey), 1,
                           int(190 * vis * (1 - t)))
        surface.blit(arc, (int(x) - acx, int(y) - 42 - acy))

    def _draw_swing_impact(surface, x, y, facing, progress):
        """Frame IMPACT: bintang 8-spike, retakan tanah, debu kaki."""
        NS = _NS_khalros
        P = NS.PALETTE
        imp = 1.0 - min(1.0, abs(progress - NS.ATTACK_IMPACT) / 0.12)
        if imp <= 0.02:
            return
        f = 1 if facing >= 0 else -1
        tx, ty = NS._axe_tip_screen_from(x, y, f, progress)
        a = NS._alpha(255 * imp)
        NS._glow(surface, tx, ty, int(30 * imp) + 8, P["fire_mid"],
                 int(150 * imp))
        NS._spark_star(surface, tx, ty, int(26 * imp), P["fire_glow"], a,
                       spikes=8, rot=progress * 6, core=P["fire_white"])
        NS._ground_ring(surface, tx, ty, int(12 + 26 * imp), P["fire_bright"],
                        P["fire_hot"], int(180 * imp), thickness=2, softness=6)
        # retakan tanah dari titik bentur
        for i in range(3):
            ang = (0.25 + i * 0.5) * math.pi * (1 if f > 0 else -1)
            NS._jagged_crack(surface, tx, y + NS.GROUND_DY - 2, ang,
                             26 * imp, (P["shadow_deep"], P["fire_bright"]),
                             int(200 * imp), seed=11 + i, width=2)
        NS._draw_dust_puff(surface, tx, y + NS.GROUND_DY, 9 + imp * 5,
                           int(160 * imp), seed=7)

    def _axe_tip_screen_from(x, y, facing, progress):
        """Ujung bilah di layar untuk pose serangan tertentu (dipakai FX)."""
        NS = _NS_khalros
        phase = 0.0
        lx, ly = NS._axe_tip_local("attack", phase, progress, facing)
        lean_f, root_y, tremble, sway = NS._raw_shift("attack", phase,
                                                      progress, facing)
        dx, dy = NS._body_offset("attack", phase, progress, facing)
        return NS._local_to_screen(x + dx, y + dy, facing, lean_f, root_y,
                                   tremble, sway, lx, ly)

    # ===================================================================
    # SKILL GROUND TELEGRAPHS (world-space; radius = px DUNIA gameplay)
    # ===================================================================
    def _draw_wild_axes_ground(surface, boss, x, y, timer, phase):
        """Q telegraph: ring TEPAT 70 px dunia DI TARGET + jalur lempar."""
        NS = _NS_khalros
        P = NS.PALETTE
        duration = NS.SKILL_DUR["q"]
        progress = max(0.0, min(1.0, 1 - timer / float(duration)))
        fs = NS._fx_scale(boss)
        tx, ty = NS._target_position(boss, x, y)
        r = NS._ring_r(boss, NS.SKILL_RADIUS["q"], surface)
        pulse = math.sin(phase * 2.6) * 0.3 + 0.7

        NS._ground_scorch(surface, tx, ty, int(r * 1.02), P["fire_darkest"],
                          P["shadow_deep"], int(140 * pulse), seed=4)
        NS._zone_fill(surface, tx, ty, r, P["fire_dark"], int(85 * pulse),
                      edge_bias=3.0)
        NS._ground_ring(surface, tx, ty, r, P["fire_bright"], P["fire_glow"],
                        int(215 * pulse), thickness=3, softness=8,
                        inner_glow=24)
        # rune Dalam = HIASAN:alpha-nya harus di bawah cincin gameplay
        # (215) supaya tepi AOE terbaca sebagai batas yang paling terang;
        # cincin yang lebih terang di dalam bikin radius terbaca salah.
        NS._rune_ring(surface, tx, ty, int(r * 0.7), P["fire_mid"],
                      P["fire_hot"], int(118 * pulse), phase * 1.4,
                      segments=9, span=0.46)
        # tiga bekas cakar konvergen ke pusat
        for i in range(3):
            ang = i * math.tau / 3 + phase * 0.5
            cx0 = tx + math.cos(ang) * r * 0.85
            cy0 = ty + math.sin(ang) * r * 0.85
            for k in range(3):
                off = (k - 1) * 3
                NS._aaline(surface, (*P["bone_light"], int(190 * pulse)),
                           (cx0 + off, cy0 + off // 2),
                           (tx + (cx0 - tx) * 0.35 + off,
                            ty + (cy0 - ty) * 0.35 + off // 2), 2)
        # ring konvergen ("kapak mendarat") di paruh kedua
        if progress > 0.45:
            conv = 1.0 - ((progress - 0.45) / 0.55)
            NS._ground_ring(surface, tx, ty, NS._coarse(max(6, int(r * conv))),
                            P["fire_hot"], P["fire_white"],
                            int(150 * (1 - conv)), thickness=2, softness=5)
        # chevron berbaris dari caster ke target
        dx, dy = tx - x, ty - (y + NS.GROUND_DY)
        ang = math.atan2(dy, dx)
        for i in range(3):
            t = ((phase * 0.5 + i / 3.0) % 1.0)
            NS._chevron(surface, x + dx * t, (y + NS.GROUND_DY) + dy * t, ang,
                        7 * fs, P["fire_hot"], int(200 * (1 - t) * pulse),
                        width=3)
        NS._spark_star(surface, tx, ty, int(9 * fs), P["fire_glow"],
                       int(205 * pulse), spikes=4, rot=phase * 1.7,
                       core=P["fire_white"])

    def _draw_call_of_wild_ground(surface, boss, x, y, timer, phase):
        """W telegraph: ring 120 px dunia DI DIRI + jejak kaki pack."""
        NS = _NS_khalros
        P = NS.PALETTE
        duration = NS.SKILL_DUR["w"]
        progress = max(0.0, min(1.0, 1 - timer / float(duration)))
        gy = y + NS.GROUND_DY
        r = NS._ring_r(boss, NS.SKILL_RADIUS["w"], surface)
        pulse = math.sin(phase * 2.1) * 0.3 + 0.7

        NS._ground_scorch(surface, x, gy, int(r * 0.98), P["fire_darkest"],
                          P["shadow_deep"], int(130 * pulse), seed=8)
        NS._zone_fill(surface, x, gy, r, P["fire_dark"], int(78 * pulse),
                      edge_bias=3.4)
        NS._ground_ring(surface, x, gy, r, P["fire_bright"], P["fire_glow"],
                        int(205 * pulse), thickness=3, softness=9,
                        inner_glow=20)
        NS._rune_ring(surface, x, gy, int(r * 0.82), P["fire_mid"],
                      P["fire_hot"], int(150 * pulse), phase * 0.75,
                      segments=13, span=0.38)
        # jejak cakar mengarah masuk (pack berlari ke centre)
        for i in range(6):
            ang = i * math.tau / 6 + 0.32 + progress * 0.7
            rr = r * (0.96 - 0.42 * ((progress + i / 6.0) % 1.0))
            px = x + math.cos(ang) * rr
            py = gy + math.sin(ang) * rr * 0.92
            a = int(180 * pulse * (1 - ((progress + i / 6.0) % 1.0) * 0.6))
            NS._poly(surface, (*P["bone_mid"], a),
                     [(px, py - 3), (px + 4, py + 1), (px, py + 4),
                      (px - 4, py + 1)])
            for k in (-2, 0, 2):
                NS._aacircle(surface, (*P["bone_light"], a),
                             (int(px + k), int(py - 5)), 1)
        # akar/umi penahan (efek slow) berdenyut di tepi
        for i in range(8):
            ang = i * math.tau / 8 + phase * 0.4
            rr = r * 0.88
            px = x + math.cos(ang) * rr
            py = gy + math.sin(ang) * rr * 0.9
            hh = 8 + 5 * math.sin(phase * 3 + i)
            NS._aaline(surface, (*P["boar_dark"], int(190 * pulse)),
                       (px, py), (px + math.cos(ang) * 3, py - hh), 3)
            NS._aaline(surface, (*P["boar_light"], int(150 * pulse)),
                       (px, py), (px + math.cos(ang) * 3, py - hh + 1), 1)

    def _draw_boar_ground(surface, boss, x, y, timer, phase):
        """E telegraph: ring pendaratan 85 px dunia + jalur bantingan."""
        NS = _NS_khalros
        P = NS.PALETTE
        duration = NS.SKILL_DUR["e"]
        progress = max(0.0, min(1.0, 1 - timer / float(duration)))
        fs = NS._fx_scale(boss)
        gy = y + NS.GROUND_DY
        r = NS._ring_r(boss, NS.SKILL_RADIUS["e"], surface)
        pulse = math.sin(phase * 3.1) * 0.3 + 0.7
        f = getattr(boss, "direction", 1) or 1

        NS._ground_scorch(surface, x, gy, int(r * 0.95), P["fire_darkest"],
                          P["shadow_deep"], int(150 * pulse), seed=13)
        NS._zone_fill(surface, x, gy, r, P["fire_dark"], int(90 * pulse),
                      edge_bias=2.8)
        NS._ground_ring(surface, x, gy, r, P["fire_bright"], P["fire_glow"],
                        int(220 * pulse), thickness=4, softness=8,
                        inner_glow=26)
        NS._dashed_ring(surface, x, gy, int(r * 0.78), P["fire_hot"],
                        int(150 * pulse), -phase * 2.2 + progress * 3.0,
                        segments=11, thick=2, span=0.5, squash=1.0)
        # ring konvergen mengecil = "bantingan akan mendarat"
        conv = 1.0 - (progress * 1.5 % 1.0)
        NS._ground_ring(surface, x, gy, NS._coarse(max(6, int(r * conv))),
                        P["fire_hot"], P["fire_white"], int(150 * (1 - conv)),
                        thickness=2, softness=5)
        # jalur tanah terbelah di belakang arah dash
        for i in range(4):
            px = x - (16 + i * 15) * fs * f
            a = int(170 * (1 - i / 4.0) * pulse)
            NS._jagged_crack(surface, px, gy, math.pi if f > 0 else 0.0,
                             12 * fs, (P["shadow_deep"], P["fire_dark"]), a,
                             seed=21 + i, width=2)
            NS._draw_dust_puff(surface, px, gy, int(9 * fs),
                               int(130 * (1 - i / 4.0) * pulse), seed=i)
        # chevron ganda ke arah bantingan
        for i in range(2):
            NS._chevron(surface, x + (26 + i * 12) * fs * f, gy - 6 - i * 3,
                        0.0 if f > 0 else math.pi, 9 * fs, P["fire_glow"],
                        int(200 * pulse * (1 - i * 0.4)), width=3)

    def _draw_hawk_storm_ground(surface, boss, x, y, timer, phase):
        """R telegraph: ring badai 200 px dunia DI CASTER + bendera angin."""
        NS = _NS_khalros
        P = NS.PALETTE
        duration = NS.SKILL_DUR["r"]
        progress = max(0.0, min(1.0, 1 - timer / float(duration)))
        fs = NS._fx_scale(boss)
        gy = y + NS.GROUND_DY
        r = NS._ring_r(boss, NS.SKILL_RADIUS["r"], surface)
        pulse = math.sin(phase * 1.9) * 0.3 + 0.7

        NS._ground_scorch(surface, x, gy, int(r * 1.02), P["wind_dark"],
                          P["shadow_deep"], int(120 * pulse), seed=24)
        NS._zone_fill(surface, x, gy, r, P["fire_dark"], int(70 * pulse),
                      edge_bias=3.6)
        NS._ground_ring(surface, x, gy, r, P["fire_bright"], P["fire_glow"],
                        int(225 * pulse), thickness=4, softness=10,
                        inner_glow=26)
        NS._rune_ring(surface, x, gy, int(r * 0.86), P["fire_mid"],
                      P["fire_hot"], int(165 * pulse), phase * 0.65,
                      segments=15, span=0.36)
        # Cincin dalam: `_dashed_ring`, BUKAN `_rune_ring`. Both berputar,
        # tapi `_rune_ring` memutar decal lewat `transform.rotate` dan pada
        # radius R (200 px dunia -> 420-560 px canvas) satu rotate = 0.9-1.1
        # ms. Dua-duanya bikin ultimate ini 2x lebih mahal dari keluarga.
        # Razak/Gorath menyelesaikan hal yang sama dengan SATU rune ring;
        # di sini cincin angin dalam jadi stroke berfasa (murah, tetap
        # berputar, dan tetap di bawah alpha cincin gameplay).
        NS._dashed_ring(surface, x, gy, int(r * 0.6), P["wind_shine"],
                        int(120 * pulse), -phase * 1.1, segments=10,
                        thick=2, span=0.42, squash=.96)
        # bulu berjatuhan menandai lingkaran bahaya
        for i in range(7):
            t = (phase * 0.5 + i / 7.0) % 1.0
            ang = i * math.tau / 7 + progress * 1.2
            rr = r * (0.94 - 0.10 * math.sin(t * math.pi))
            fx = x + math.cos(ang) * rr
            fy = gy + math.sin(ang) * rr * 0.9 - (1 - t) * 26
            NS._poly(surface, (*P["hawk_light"], int(200 * (1 - t * 0.7))),
                     [(fx, fy), (fx + 4, fy + 3), (fx + 1, fy + 9),
                      (fx - 3, fy + 4)])
            NS._aacircle(surface, (*P["hawk_high"], int(150 * (1 - t))),
                         (int(fx), int(fy + 2)), 1)
        # 6 chevron mengarah turun ke dalam (hujan dari langit)
        for i in range(6):
            ang = i * math.tau / 6 + phase * 0.25
            t = (progress * 1.2 + i * 0.13) % 1.0
            rr = r * (1.02 - t * 0.5)
            px = x + math.cos(ang) * rr
            py = gy + math.sin(ang) * rr * 0.92
            NS._chevron(surface, px, py, ang + math.pi, 9 * fs,
                        P["fire_hot"], int(190 * pulse * (1 - t * 0.5)),
                        width=3)
        if progress > 0.5:
            conv = 1.0 - ((progress - 0.5) / 0.5)
            NS._ground_ring(surface, x, gy, NS._coarse(max(8, int(r * conv))),
                            P["fire_hot"], P["fire_white"],
                            int(140 * (1 - conv)), thickness=2, softness=6)

    # ===================================================================
    # SKILL Q - WILD AXES (voli kapak berputar; aktivasi -> steady -> impact)
    # ===================================================================
    def _draw_wild_axes(surface, boss, x, y, timer, phase):
        duration = 50
        NS = _NS_khalros
        P = NS.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / float(duration)))
        fs = NS._fx_scale(boss)
        tx, ty = NS._target_position(boss, x, y)
        f = getattr(boss, "direction", 1) or 1

        # AKTIVASI: pusaran kapak di atas kepala + lingkaran rune kecil
        if progress < 0.34:
            k = 1 - progress / 0.34
            ax, ay = x - 6 * f, y - 56
            a = NS._alpha(255 * k)
            NS._glow(surface, ax, ay, int(24 * fs), P["fire_mid"],
                     int(150 * k))
            NS._dashed_ring(surface, ax, ay, int(17 * fs), P["fire_hot"], a,
                            phase * 4.2, segments=6, thick=2, span=0.6,
                            squash=1.0)
            NS._dashed_ring(surface, ax, ay, int(24 * fs), P["fire_bright"],
                            int(a * 0.7), -phase * 3.1, segments=8, thick=2,
                            span=0.5, squash=1.0)
            for i in range(3):
                ang = phase * 5.0 + i * math.tau / 3
                rx = ax + math.cos(ang) * 20 * fs
                ry = ay + math.sin(ang) * 12 * fs
                NS._draw_spinning_axe(surface, rx, ry, ang * 1.4, size=0.55)
            NS._spark_star(surface, ax, ay, int(13 * fs), P["fire_glow"], a,
                           spikes=6, rot=progress * 9, core=P["fire_white"])

        # LEPAS: spawn 2 kapak di puncak ayunan (guard sekali-pakai)
        if 0.30 <= progress <= 0.44 and not getattr(boss,
                                                     "_khal_axe_spawned",
                                                     False):
            gx, gy = NS._axe_tip_screen(boss, x, y)
            for i in range(2):
                spread = (i - 0.5) * 16
                NS._spawn_axe(boss, gx + i * 6 * f, gy - 4, tx + spread,
                              ty + spread * 0.4, arc=14 + i * 6)
            boss._khal_axe_spawned = True
            NS._spark_star(surface, gx, gy, int(18 * fs), P["fire_hot"], 235,
                           spikes=8, rot=phase * 2.0, core=P["fire_white"])
        if progress < 0.30 or progress > 0.8:
            boss._khal_axe_spawned = False

        # STEADY: angin berputar mengelilingi badan + sisa bara
        if 0.34 <= progress < 0.9:
            vis = 1.0 - abs(progress - 0.55) / 0.35
            vis = max(0.0, min(1.0, vis))
            NS._wind_sweep(surface, x, y - 18, int(34 * fs),
                           int(150 * vis), phase * 2.4, arcs=3)
            for i in range(4):
                t = (phase * 0.9 + i * 0.25) % 1.0
                ex = x - f * (10 + t * 34) + math.sin(t * 6 + i) * 6
                ey = y - 8 - t * 26
                NS._draw_ember(surface, ex, ey, 1, int(190 * vis * (1 - t)))

        # IMPACT di target: splat dua ring + bekas cakar di tanah
        if 0.55 < progress < 0.95:
            imp = 1 - abs(progress - 0.72) / 0.20
            imp = max(0.0, min(1.0, imp))
            ir = int((8 + imp * 24) * fs)
            ia = NS._alpha(235 * imp)
            NS._glow(surface, tx, ty, int(26 * fs), P["fire_mid"],
                     int(150 * imp))
            NS._ground_ring(surface, tx, ty, ir, P["fire_bright"],
                            P["fire_glow"], ia, thickness=3, softness=7)
            NS._ground_ring(surface, tx, ty, int(ir * 0.5), P["fire_hot"],
                            P["fire_white"], int(ia * 0.7), thickness=2,
                            softness=5)
            for i in range(3):
                ang = i * 1.05 - 0.5
                NS._jagged_crack(surface, tx, ty, ang, ir * 1.15,
                                 (P["shadow_deep"], P["fire_bright"]),
                                 int(200 * imp), seed=33 + i, width=2)
            NS._spark_star(surface, tx, ty, int(15 * fs * imp),
                           P["fire_glow"], ia, spikes=6, rot=progress * 7,
                           core=P["fire_white"])
            if imp > 0.55 and not getattr(boss, "_khal_q_marked", False):
                NS.note_ground_mark(boss, tx, ty + 12, 24, 80)
                boss._khal_q_marked = True
            if imp < 0.4:
                boss._khal_q_marked = False

    # ===================================================================
    # SKILL W - CALL OF WILD (panggilan pack: howl + slow + pulih)
    # ===================================================================
    def _draw_call_of_wild_ground_legacy(surface, boss, x, y, timer, phase):
        """Alias lama - sama dengan telegraph W."""
        _NS_khalros._draw_call_of_wild_ground(surface, boss, x, y, timer,
                                              phase)

    def _draw_call_of_wild(surface, boss, x, y, timer, phase):
        duration = 60
        NS = _NS_khalros
        P = NS.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / float(duration)))
        fs = NS._fx_scale(boss)
        f = getattr(boss, "direction", 1) or 1
        gy = y + NS.GROUND_DY
        r = NS._ring_r(boss, NS.SKILL_RADIUS["w"], surface)

        # AKTIVASI: pilar suara + shockwave ganda + bintang 8-spike
        if progress < 0.28:
            k = 1 - progress / 0.28
            a = NS._alpha(250 * k)
            NS._draw_wind_column(surface, x, y + 24, int((70 + 60 * k) * fs),
                                 int(9 * fs), phase * 2.0)
            NS._glow(surface, x, y - 20, int(34 * fs), P["fire_mid"],
                     int(150 * k))
            for i, (rr, th) in enumerate(((1.0, 4), (0.7, 2))):
                NS._ground_ring(surface, x, gy, int(r * rr * progress * 2.4),
                                P["fire_bright"] if i == 0 else P["fire_glow"],
                                P["fire_hot"], int(a * (1 - i * 0.35)),
                                thickness=th, softness=8)
            NS._spark_star(surface, x, y - 26, int(22 * fs), P["fire_glow"],
                           a, spikes=8, rot=progress * 6, core=P["fire_white"])
            # gelombang suara: 3 cincin melebar dari kepala
            for i in range(3):
                t = (progress * 2.6 + i * 0.3) % 1.0
                rr = int((16 + t * 46) * fs)
                NS._aaline(surface, (*P["fire_hot"], int(180 * (1 - t))),
                           (x - rr, y - 30), (x - rr * 0.7, y - 40), 2)
                NS._aaline(surface, (*P["fire_hot"], int(180 * (1 - t))),
                           (x + rr, y - 30), (x + rr * 0.7, y - 40), 2)

        # STEADY: pack berlari mengelilingi caster (2 serigala + 1 babi)
        if progress > 0.2:
            vis = max(0.0, min(1.0, (progress - 0.2) / 0.22)) * \
                max(0.0, min(1.0, (0.98 - progress) / 0.12))
            for i, kind in enumerate(("wolf", "boar", "wolf")):
                ang = phase * 0.85 + i * math.tau / 3
                rr = r * 0.74
                bx = x + math.cos(ang) * rr
                by = gy + math.sin(ang) * rr * 0.42 - 2
                alpha = NS._alpha(255 * vis)
                if kind == "boar":
                    NS._draw_boar(surface, bx, by, -1 if math.cos(ang) < 0 else 1,
                                  phase * 3 + i, alpha)
                else:
                    NS._draw_wolf(surface, bx, by,
                                  -1 if math.cos(ang) < 0 else 1,
                                  phase * 3.4 + i, alpha)
                NS._draw_dust_puff(surface, bx, gy + math.sin(ang) * rr * 0.42,
                                   8, int(120 * vis), seed=i * 3)
                # bara mengikuti hidung binatang
                NS._draw_ember(surface, bx + (12 if math.cos(ang) > 0 else -12),
                               by - 8, 2, int(200 * vis))
            # uap pemulihan mengalir ke badan caster (heal)
            for i in range(6):
                t = (phase * 0.6 + i * 0.17) % 1.0
                ang = i * math.tau / 6
                hx = x + math.cos(ang) * r * 0.5 * (1 - t)
                hy = gy - t * 46
                a = int(210 * (1 - t))
                NS._aacircle(surface, (*P["gold_light"], a), (int(hx), int(hy)),
                             2)
                NS._aacircle(surface, (*P["gold_shine"], a), (int(hx),
                                                             int(hy - 1)), 1)

    # ===================================================================
    # SKILL E - BOAR CHARGE (bantingan babi hutan + AOE pendaratan)
    # ===================================================================
    def _draw_boar_charge(surface, boss, x, y, timer, phase):
        duration = 45
        NS = _NS_khalros
        P = NS.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / float(duration)))
        fs = NS._fx_scale(boss)
        f = getattr(boss, "direction", 1) or 1
        gy = y + NS.GROUND_DY
        r = NS._ring_r(boss, NS.SKILL_RADIUS["e"], surface)

        # BANTING: hantaman tanah + bintang 8-spike + debu
        if progress < 0.32:
            k = 1 - progress / 0.32
            NS._glow(surface, x + 20 * f, y + 6, int(30 * fs), P["fire_mid"],
                     int(170 * k))
            NS._spark_star(surface, x + 22 * f, y + 4, int(26 * fs * k),
                           P["fire_hot"], NS._alpha(240 * k), spikes=8,
                           rot=progress * 8, core=P["fire_white"])
            for i in range(5):
                t = i / 5.0
                px = x + f * (18 + t * 30)
                NS._draw_dust_puff(surface, px, gy - t * 4, int(9 + t * 9 * fs),
                                   int(190 * k * (1 - t)), seed=i + 2)
            NS._ground_ring(surface, x, gy, int(r * 0.55 * (0.4 + progress)),
                            P["fire_bright"], P["fire_glow"],
                            int(180 * k), thickness=3, softness=7)

        # STEADY: bayangan babi hutan menubruk di depan + serpihan tanah
        if progress > 0.22:
            vis = max(0.0, min(1.0, (progress - 0.22) / 0.2)) * \
                max(0.0, min(1.0, (0.95 - progress) / 0.1))
            bx = x + f * (30 + 8 * vis)
            by = y + 26
            NS._draw_boar(surface, bx, by, f, phase * 4.0 + 1,
                          NS._alpha(235 * vis))
            NS._glow(surface, bx, by - 8, int(26 * fs), P["fire_dark"],
                     int(120 * vis))
            for i in range(4):
                t = (phase * 1.4 + i * 0.25) % 1.0
                px = x - f * (14 + t * 40)
                py = gy - math.sin(t * math.pi) * 10
                NS._poly(surface, (*P["dust_mid"], int(190 * vis * (1 - t))),
                         [(px, py), (px + 4, py - 3), (px + 7, py + 1),
                          (px + 2, py + 4)])
                NS._draw_ember(surface, px - 2, py - 2, 1,
                               int(170 * vis * (1 - t)))
            # retakan di jalur bantingan
            for i in range(2):
                NS._jagged_crack(surface, x - f * (12 + i * 26), gy,
                                 math.pi if f > 0 else 0.0, 22 * fs,
                                 (P["shadow_deep"], P["fire_dark"]),
                                 int(150 * vis), seed=45 + i, width=2)

        # AKHIR: bekas bantingan tertinggal di tanah
        if 0.6 < progress < 0.8 and not getattr(boss, "_khal_e_marked", False):
            NS.note_ground_mark(boss, x, gy, 30, 90)
            boss._khal_e_marked = True
        if progress < 0.6 or progress > 0.8:
            boss._khal_e_marked = False

    # ===================================================================
    # SKILL R - HAWK STORM (hujan elang penyelam mengelilingi caster)
    # ===================================================================
    def _draw_hawk_summon(surface, boss, x, y, timer, phase):
        duration = 70
        NS = _NS_khalros
        P = NS.PALETTE
        progress = max(0.0, min(1.0, 1 - timer / float(duration)))
        fs = NS._fx_scale(boss)
        gy = y + NS.GROUND_DY
        r = NS._ring_r(boss, NS.SKILL_RADIUS["r"], surface)
        f = getattr(boss, "direction", 1) or 1

        # AKTIVASI: kolom panggilan + shockwave ganda + bintang
        if progress < 0.22:
            k = 1 - progress / 0.22
            NS._draw_wind_column(surface, x, y + 30, int((90 + 70 * k) * fs),
                                 int(13 * fs), phase * 1.7)
            for i, rr in enumerate((0.9, 0.6)):
                NS._ground_ring(surface, x, gy, int(r * rr * (0.3 + progress * 2.2)),
                                P["fire_bright"] if i == 0 else P["wind_shine"],
                                P["fire_glow"], int(200 * k * (1 - i * 0.4)),
                                thickness=4 - i, softness=9)
            NS._spark_star(surface, x, y - 30, int(24 * fs), P["fire_glow"],
                           NS._alpha(250 * k), spikes=8, rot=progress * 5,
                           core=P["fire_white"])
            # 4 kapak-bulu terlempar ke langit
            for i in range(4):
                ang = i * math.tau / 4 + progress * 3.0
                fx2 = x + math.cos(ang) * 26 * fs
                fy2 = y - 30 - math.sin(progress * 6 + i) * 14
                NS._poly(surface, (*P["hawk_light"], NS._alpha(220 * k)),
                         [(fx2, fy2), (fx2 + 5, fy2 + 3), (fx2 + 1, fy2 + 9),
                          (fx2 - 4, fy2 + 3)])

        # STEADY: 6 elang penyelam mengorbit di 0.62 R + bayangan penyelam
        if progress > 0.18:
            vis = max(0.0, min(1.0, (progress - 0.18) / 0.18)) * \
                max(0.0, min(1.0, (0.99 - progress) / 0.12))
            n_hawks = 6
            for i in range(n_hawks):
                ang = phase * 1.15 + i * math.tau / n_hawks
                dive = math.sin(progress * 6.0 + i * 1.2)
                rr = r * (0.62 + 0.16 * dive)
                hx = x + math.cos(ang) * rr
                hy = y - 44 - dive * 26 + math.sin(ang) * rr * 0.22
                hf = -1 if math.cos(ang) < 0 else 1
                NS._draw_flying_hawk(surface, hx, hy, hf,
                                     phase * 6.0 + i * 1.7,
                                     size=1.15 + 0.15 * dive)
                NS._glow(surface, hx, hy, int(16 * fs), P["fire_dark"],
                         int(80 * vis))
                # bayangan penyelam di lantai (memberi kedalaman)
                shx = x + math.cos(ang) * rr * 0.86
                shy = gy + math.sin(ang) * rr * 0.86 * 0.42
                NS._ellipse(surface, (*P["shadow_deep"], int(120 * vis)),
                            (shx - 10, shy - 3, 20, 6))
                # bulu rontok
                t = (phase * 0.7 + i * 0.2) % 1.0
                NS._poly(surface, (*P["hawk_high"], int(170 * vis * (1 - t))),
                         [(hx + 3, hy + 4 + t * 22), (hx + 7, hy + 7 + t * 22),
                          (hx + 3, hy + 11 + t * 22)])
            # angin berputar di tanah (2 lengan spiral)
            for arm in range(2):
                for i in range(7):
                    t = i / 7.0
                    ang2 = phase * 1.7 + arm * math.pi + t * math.tau * 0.6
                    rr2 = r * (0.30 + 0.62 * t)
                    wx = x + math.cos(ang2) * rr2
                    wy = gy + math.sin(ang2) * rr2 * 0.4
                    a = int(150 * vis * (1 - t * 0.7))
                    NS._aaline(surface, (*P["wind_light"], a), (wx, wy),
                               (x + math.cos(ang2 + 0.28) * rr2,
                                gy + math.sin(ang2 + 0.28) * rr2 * 0.4),
                               3 - (i % 3))
                    NS._aacircle(surface, (*P["wind_shine"], a),
                                 (int(wx), int(wy)), 1)

        # IMPACT: target dihantam + bekas di tanah
        if 0.4 < progress < 0.9:
            imp = 1 - abs(progress - 0.62) / 0.26
            imp = max(0.0, min(1.0, imp))
            tx, ty = NS._target_position(boss, x, y)
            NS._ground_ring(surface, tx, ty, int((12 + 22 * imp) * fs),
                            P["wind_light"], P["wind_shine"],
                            int(190 * imp), thickness=3, softness=7)
            NS._spark_star(surface, tx, ty, int(18 * fs * imp), P["fire_glow"],
                           NS._alpha(220 * imp), spikes=6, rot=progress * 5,
                           core=P["white"])
            if imp > 0.6 and not getattr(boss, "_khal_r_marked", False):
                NS.note_ground_mark(boss, tx, ty + 10, 26, 85)
                boss._khal_r_marked = True
            if imp < 0.4:
                boss._khal_r_marked = False

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
        portrait = bool(getattr(boss, "_portrait_hd", False))
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = NS._detect_moving(boss)
        # Selalu dijalankan di sini.  Untuk hero lane, sprite di-cache,
        # jadi pada frame cache-HIT fungsi ini tidak dipanggil sama
        # sekali -- heroes.render_hero yang memajukan controller pada
        # frame itu (lihat heroes._tick_pose_controller).  Hasilnya
        # controller maju tepat sekali per frame di kedua jalur.
        NS._update_gorath_attack_anim(boss)
        action, phase, ap = NS._resolve_pose(boss, moving)
        boss._gor_pose_action = action

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

        # ── AKTIVASI: shockwave ganda + bintang (TANPA pilar cahaya) ──
        # Pilar darah 4-lapis setinggi 100 px di (cx, cy) DIBUANG:
        # kolom itu menutupi badan Gorath selama Bloodrage di-cast.
        if progress < 0.18:
            t = progress / 0.18
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

        # ── AKTIVASI: shockwave ganda + bintang (TANPA pilar cahaya) ──
        # Pilar cahaya darah 4-lapis setinggi 100 px di (cx, cy)
        # DIBUANG: kolom itu menutupi badan Gorath selama R di-cast.
        if progress < 0.16:
            t = progress / 0.16
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
    """Namespace ALCHEMIST — PIXEL MASTERWORK v3 + COMBAT FX v3.

    FULL REWRITE dari rig ORIGINAL-MAX lama, mengikuti standar
    **Gorath v2 Pixel Masterwork + Razak v3 Combat FX**
    (docs/GORATH_V2_RENDERER.md, docs/RAZAK_V3_COMBAT_FX.md).
    Tetap 100% prosedural: tidak ada file gambar / sprite-sheet /
    pemuatan aset eksternal. Semua bentuk lahir dari pygame.draw +
    Surface + transform + mask.

    Apa yang diperbaiki di RIG v3 (tulis ulang lapisan gambar)
    ----------------------------------------------------------
    Kontrak animasi / FX / cache v2 dipertahankan utuh; yang ditulis
    ulang dari nol adalah bagian yang menggambar piksel:

    a. ANATOMI. Rig v2 memakai ``ky = hipy + sin(ang) * 20`` untuk
       lutut, jadi pada pose diam (ang = 0.08) kaki cuma turun ~1.6 px
       dan seluruh tungkai berhenti di y = +38 — tertelan perut yang
       turun sampai +42, sehingga sosok tampak MENGAMBANG di atas
       bayangannya. Sekarang panjang tungkai bersifat vertikal (cos)
       dan ayunan yang horizontal (sin): pinggul +18 -> lutut +39 ->
       telapak +60, mendarat tepat di GROUND_DY.
    b. VOLUME. Lengan/kaki v2 adalah poligon lebar-tetap tanpa siku
       ("sosis") dengan satu garis highlight. Sekarang lewat ``_limb``
       (meruncing, ramp 4 band, siku/lutut nyata) dan ``_ball``
       (terminator + specular) — anggota badan punya massa.
    c. CAHAYA. v2 mengalikan posisi highlight dengan ``f`` (facing),
       jadi saat hadap kiri sumber cahaya ikut pindah dan volume
       terbaca rata. ``_lit_side`` sekarang mengunci key light di
       kiri-atas RUANG LAYAR, tidak peduli arah hadap.
    d. SILUET. Kepala ogre v2 tertutup penuh badan goblin (wajah tidak
       pernah terlihat) dan sudut cleaver tidak pernah dicerminkan
       saat hadap kiri. Sekarang goblin duduk di bahu belakang,
       kepala ogre digeser maju, lengan+senjata goblin digambar pada
       lapisan terpisah di atas kepala ogre, dan sudut bilah dipetakan
       lewat ``S()`` (pi - a) saat mirror.
    e. DETAIL. Cleaver jagal berpunggung tebal + lubang gantung, botol
       ransel mendidih dengan permukaan cairan bergoyang, pauldron
       berlapis + duri, sabuk berlubang + botol gantung, dan ikat
       kepala melengkung mengikuti tempurung (v2: persegi datar yang
       memotong tengkorak jadi dua).

    Warisan yang tetap berlaku dari v2
    ----------------------------------
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

    #: Ukuran buffer badan & jangkar. Extents terukur ulang untuk rig
    #: v3 (duo lebih tinggi): ujung topi goblin -93, glow botol W -113,
    #: e_cast hop -121, telapak kaki +64, boot/cakar +70, ayunan lunge
    #: +-92 -> buffer 200x210 berpusat di (100, 132).
    #: Kalau angka ini kekecilan, kepala/topi goblin akan TERPOTONG di
    #: tepi buffer (cacat yang muncul saat rig ditinggikan).
    RIG_W, RIG_H = 200, 210
    RIG_OX, RIG_OY = 100, 132

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
        """Pergelangan tangan (grip cleaver) ruang lokal.

        Bahu ada di (+-19, -32); jangkauan lengan ogre ~30 px, jadi
        semua genggaman dijaga di dalam radius itu supaya lengan tidak
        pernah tampak "putus" dari bahu (cacat rig lama saat pose e/r).
        """
        if action == "attack":
            pose = _NS_alchemist._attack_pose(ap)
            ang = pose["blade_b"] if back else pose["blade_f"]
            reach = 22 + 10 * math.sin(min(1.0, ap * 1.6) * math.pi)
            sx = -19 if back else 19
            return (int(sx + math.cos(ang) * reach),
                    int(-32 + math.sin(ang) * reach + 10))
        if action == "walk":
            swing = math.sin(phase + (math.pi if back else 0.0)) * 7
            return (int((-20 if back else 21) + swing), 4)
        if action == "q_cast":
            return (22, 8) if not back else (-25, 8)
        if action == "w_cast":
            return (19, -14) if not back else (-19, -14)
        if action == "e_cast":
            return (29, -10) if not back else (-29, -10)
        if action == "r_cast":
            return (21, -26) if not back else (-21, -26)
        bob = math.sin(phase * 0.7 + (0.9 if back else 0.4)) * 1.8
        return (-27 if back else 27, int(6 + bob))

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

    def _lit_side(dx, dy):
        """Sisi perpendicular yang menghadap key light (kiri-atas LAYAR).

        Rig di-mirror lewat ``facing``, tapi CAHAYA TIDAK ikut mirror —
        inilah bug rig lama: highlight pindah sisi saat hadap kiri, jadi
        volume-nya terbaca rata. Semua helper limb memakai ini.
        """
        px, py = -dy, dx
        return 1.0 if (px * -0.70 + py * -0.70) > 0 else -1.0

    def _aalines_soft(surface, color, points, width=1):
        """Polyline pendek (dipakai kain/ikat yang melengkung)."""
        NS = _NS_alchemist
        for a, b in zip(points, points[1:]):
            NS._aaline(surface, color, (int(a[0]), int(a[1])),
                       (int(b[0]), int(b[1])), width)

    def _limb(surface, p0, w0, p1, w1, c_dark, c_mid, c_hi,
              c_shine=None):
        """Anggota badan meruncing (kapsul poligon) + ramp 3-4 band.

        Rig lama menggambar lengan/kaki sebagai poligon lebar-tetap
        dengan satu garis highlight, jadi terbaca sebagai 'sosis'.
        Di sini lebar mengecil dari pangkal ke ujung, band gelap /
        mid / terang mengikuti sumbu, dan sisi terang selalu sisi
        yang menghadap cahaya di RUANG LAYAR.
        """
        NS = _NS_alchemist
        x0, y0 = float(p0[0]), float(p0[1])
        x1, y1 = float(p1[0]), float(p1[1])
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy)
        if ln < 0.5:
            return
        dx, dy = dx / ln, dy / ln
        px, py = -dy, dx
        s = NS._lit_side(dx, dy)

        def quad(a0, a1, off=0.0, lo=0.0, hi=1.0):
            """Poligon meruncing: a0/a1 = setengah lebar pangkal/ujung,
            off = geser sepanjang perpendicular, lo/hi = potong sumbu."""
            bx, by = x0 + dx * ln * lo, y0 + dy * ln * lo
            ex, ey = x0 + dx * ln * hi, y0 + dy * ln * hi
            b = a0 + (a1 - a0) * lo
            e = a0 + (a1 - a0) * hi
            return [(bx + px * (off * b - b), by + py * (off * b - b)),
                    (ex + px * (off * e - e), ey + py * (off * e - e)),
                    (ex + px * (off * e + e), ey + py * (off * e + e)),
                    (bx + px * (off * b + b), by + py * (off * b + b))]

        # selout kontak (offset ke sisi gelap, bukan kotak hitam penuh)
        NS._poly(surface, NS.PALETTE["shadow_deep"],
                 [(vx - s * px * 1.0 + 0.6, vy - s * py * 1.0 + 0.9)
                  for vx, vy in quad(w0 + 0.7, w1 + 0.7)])
        NS._poly(surface, c_dark, quad(w0, w1))
        # band mid: digeser ke sisi cahaya, lebih ramping
        NS._poly(surface, c_mid,
                 [(vx + s * px * 0.55, vy + s * py * 0.55)
                  for vx, vy in quad(w0 * 0.72, w1 * 0.72)])
        # band terang: pita sempit menempel tepi cahaya
        NS._poly(surface, c_hi,
                 [(vx + s * px * (w0 * 0.52), vy + s * py * (w0 * 0.52))
                  for vx, vy in quad(w0 * 0.30, w1 * 0.30, lo=0.08,
                                     hi=0.86)])
        if c_shine is not None and ln > 9:
            NS._poly(surface, c_shine,
                     [(vx + s * px * (w0 * 0.66),
                       vy + s * py * (w0 * 0.66))
                      for vx, vy in quad(w0 * 0.13, w1 * 0.13, lo=0.16,
                                         hi=0.52)])

    def _ball(surface, cx, cy, r, c_dark, c_mid, c_hi, c_shine=None):
        """Massa bulat ber-volume: terminator + specular kiri-atas."""
        NS = _NS_alchemist
        cx, cy, r = int(cx), int(cy), max(1, int(r))
        NS._aacircle(surface, c_dark, (cx, cy), r)
        NS._aacircle(surface, c_mid, (cx - max(1, r // 5),
                                      cy - max(1, r // 5)),
                     max(1, int(r * 0.74)))
        NS._aacircle(surface, c_hi, (cx - int(r * 0.34),
                                     cy - int(r * 0.38)),
                     max(1, int(r * 0.42)))
        if c_shine is not None and r >= 4:
            NS._aacircle(surface, c_shine, (cx - int(r * 0.44),
                                            cy - int(r * 0.48)),
                         max(1, r // 5))

    # ==================================================================
    # RIG PIXEL-ART v3 — ogre chemist + goblin rider (ruang lokal).
    # Konvensi: (0,0) = jangkar pinggul; +x maju (dikali facing); y ke
    # bawah; tanah = +GROUND_DY. Key light TETAP di kiri-atas layar.
    #
    # Yang diperbaiki dari rig v2 (sumber "jelek"-nya):
    #   * kaki berakhir di y=+38 sementara perut turun sampai +42 dan
    #     bayangan di +62 -> kaki tertelan perut & sosok mengambang.
    #     Sekarang pinggul +18 -> lutut +38 -> telapak +60 menyentuh
    #     garis tanah yang sama dengan bayangan.
    #   * lengan/kaki poligon lebar-tetap tanpa siku -> "sosis".
    #     Sekarang lewat _limb (meruncing, ramp 4 band, siku nyata).
    #   * highlight ikut ter-mirror bersama facing -> volume rata.
    #     Sekarang _lit_side mengunci cahaya ke ruang layar.
    #   * kepala ogre tertutup penuh badan goblin -> siluet tanpa
    #     wajah. Sekarang kepala digeser maju + goblin mundur ke bahu
    #     belakang, keduanya terbaca.
    #   * sudut cleaver tidak di-mirror saat hadap kiri.
    # ==================================================================
    def _draw_cleaver(surface, gx, gy, ang, f, phase=0.0, glow=0.0):
        """Cleaver jagal berputar mengikuti SUDUT (arc-based).

        gx,gy = layar; ang = sudut LAYAR (0 kanan, pi/2 bawah) — sudah
        di-mirror pemanggil. Bilah = poligon dari basis ke ujung memakai
        cos/sin, jadi tidak pernah ada lerp posisi awal->akhir.
        """
        NS = _NS_alchemist
        P = NS.PALETTE
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        H = NS.CLEAVER_HANDLE
        B = NS.CLEAVER_BLADE
        lit = NS._lit_side(ca, sa)

        def pt(dist, side):
            return (gx + ca * dist + px * side,
                    gy + sa * dist + py * side)

        def ipt(dist, side):
            p = pt(dist, side)
            return (int(p[0]), int(p[1]))

        # ── gagang kayu berbalut kulit + pommel kuningan ──────────
        NS._limb(surface, pt(-3, 0), 2.6, pt(H, 0), 2.2,
                 P["leather_darkest"], P["leather_mid"],
                 P["leather_high"])
        for t in (0.25, 0.55, 0.85):
            d = -3 + (H + 3) * t
            NS._aaline(surface, P["leather_darkest"],
                       ipt(d, -2), ipt(d, 2), 1)
        # ── bolster / cincin kuningan pemisah gagang-bilah ─────────
        NS._poly(surface, P["brass_dark"],
                 [ipt(H - 1, -4), ipt(H + 2, -4), ipt(H + 2, 5),
                  ipt(H - 1, 5)])
        NS._poly(surface, P["brass_mid"],
                 [ipt(H - 1, -3), ipt(H + 1, -3), ipt(H + 1, 4),
                  ipt(H - 1, 4)])
        NS._aaline(surface, P["brass_shine"], ipt(H - 1, -3),
                   ipt(H + 1, -3), 1)

        # ── BILAH: persegi berat khas cleaver jagal, punggung tebal,
        #    mata tebang melebar ke ujung (bukan bilah pipih 6 px) ──
        back0, back1 = -4.0, -5.5          # punggung (spine)
        edge0, edge1 = 6.5, 10.5           # mata tebang
        spine = [ipt(H + 1, back0), ipt(H + B, back1)]
        # selout arah bayangan
        NS._poly(surface, P["shadow_deep"], [
            (int(pt(H + 1, back0)[0] + 1), int(pt(H + 1, back0)[1] + 1)),
            (int(pt(H + B, back1)[0] + 1), int(pt(H + B, back1)[1] + 1)),
            (int(pt(H + B, edge1)[0] + 1), int(pt(H + B, edge1)[1] + 1)),
            (int(pt(H + 1, edge0)[0] + 1), int(pt(H + 1, edge0)[1] + 1))])
        NS._poly(surface, P["metal_darkest"], [
            ipt(H + 1, back0), ipt(H + B, back1), ipt(H + B, edge1),
            ipt(H + 1, edge0)])
        # bevel utama (mengikuti sisi cahaya, bukan selalu sisi yg sama)
        NS._poly(surface, P["metal_dark"], [
            ipt(H + 2, back0 + 0.8), ipt(H + B - 1, back1 + 0.8),
            ipt(H + B - 1, edge1 - 1.0), ipt(H + 2, edge0 - 1.0)])
        NS._poly(surface, P["metal_mid"], [
            ipt(H + 3, back0 + 1.6 * lit), ipt(H + B - 2, back1 + 1.6 * lit),
            ipt(H + B - 2, edge1 * 0.45), ipt(H + 3, edge0 * 0.45)])
        # pita specular sepanjang tulang bilah
        NS._poly(surface, P["metal_light"], [
            ipt(H + 4, back0 + 1.4), ipt(H + B - 4, back1 + 1.6),
            ipt(H + B - 4, back1 + 3.4), ipt(H + 4, back0 + 3.2)])
        # lubang gantung khas cleaver (di dekat punggung)
        hole = ipt(H + B - 6, back1 + 3.0)
        NS._aacircle(surface, P["metal_darkest"], hole, 2)
        NS._aacircle(surface, P["metal_dark"], (hole[0], hole[1] + 1), 1)
        # mata tebang: garis putih tipis + gerigi karat asam
        NS._aaline(surface, P["metal_shine"], ipt(H + 1, edge0),
                   ipt(H + B, edge1), 2)
        NS._aaline(surface, P["metal_edge"], ipt(H + 3, edge0 + 0.4),
                   ipt(H + B - 1, edge1 + 0.2), 1)
        # etsa asam / noda kimia di badan bilah
        NS._aaline(surface, P["acid_dark"], ipt(H + 6, edge0 - 2.6),
                   ipt(H + B - 5, edge1 - 3.4), 1)
        NS._aacircle(surface, (*P["acid_mid"], 120),
                     ipt(H + B - 9, edge1 - 5.0), 2)
        # tetes asam menggantung di mata bilah
        drip = (phase * 0.6 + gx * 0.01) % 1.0
        if drip < 0.55:
            dp = pt(H + B - 7, edge1 - 1.0)
            NS._aacircle(surface, (*P["acid_bright"],
                                   int(210 * (1 - drip / 0.55))),
                         (int(dp[0]), int(dp[1] + drip * 7)), 1)
        # pommel
        NS._ball(surface, *ipt(-3, 0), 3, P["brass_dark"],
                 P["brass_mid"], P["brass_light"], P["brass_shine"])
        # glint periodik di ujung
        if math.sin(phase * 2.6 + ang) > 0.90:
            tip = ipt(H + B - 1, edge1 - 1)
            NS._aacircle(surface, P["metal_edge"], tip, 2)
            NS._aacircle(surface, P["white"], (tip[0] - 1, tip[1] - 1), 1)
        if glow > 0.02:
            g = int(150 * min(1.0, glow))
            NS._aacircle(surface, (*P["acid_bright"],
                                   int(g * 0.55)),
                         ipt(H + B * 0.6, edge0), 7)
            NS._aacircle(surface, (*P["acid_hot"], g),
                         ipt(H + B * 0.6, edge0), 4)

    def _draw_ogre_arm(surface, sx, sy, gx, gy, f, back=False,
                       flex=0.0):
        """Lengan ogre: deltoid -> biceps -> SIKU nyata -> lengan bawah
        -> sarung tangan. Siku diletakkan di luar garis bahu-genggaman
        (offset perpendicular) supaya ada tekukan, bukan garis lurus."""
        NS = _NS_alchemist
        P = NS.PALETTE
        dx, dy = gx - sx, gy - sy
        ln = max(1.0, math.hypot(dx, dy))
        ux, uy = dx / ln, dy / ln
        pxx, pyy = -uy, ux
        # siku menonjol keluar dari torso + turun karena berat
        bulge = (5.5 + flex * 3.0) * (-1.0 if back else 1.0)
        ex = sx + ux * ln * 0.48 + pxx * bulge
        ey = sy + uy * ln * 0.48 + pyy * bulge + 3.0 - flex * 2.0
        if back:
            c_d, c_m, c_h = (P["ogre_darkest"], P["ogre_dark"],
                             P["ogre_mid"])
            c_s = None
            w_up, w_el, w_lo = 7.0, 5.4, 4.4
        else:
            c_d, c_m, c_h = (P["ogre_dark"], P["ogre_mid"],
                             P["ogre_light"])
            c_s = P["ogre_high"]
            w_up, w_el, w_lo = 8.4, 6.2, 5.0
        # lengan atas (biceps gemuk) + lengan bawah (meruncing)
        NS._limb(surface, (sx, sy), w_up, (ex, ey), w_el,
                 c_d, c_m, c_h, c_s)
        NS._limb(surface, (ex, ey), w_el, (gx, gy), w_lo,
                 c_d, c_m, c_h, c_s)
        # deltoid
        NS._ball(surface, sx, sy, 8 if not back else 7,
                 c_d, c_m, c_h, c_s)
        # ikat lengan kulit di atas siku
        bx = sx + ux * ln * 0.30 + pxx * bulge * 0.30
        by = sy + uy * ln * 0.30 + pyy * bulge * 0.30 + 1
        NS._limb(surface, (bx - pxx * w_up * 0.9, by - pyy * w_up * 0.9),
                 2.2, (bx + pxx * w_up * 0.9, by + pyy * w_up * 0.9),
                 2.2, P["leather_darkest"], P["leather_mid"],
                 P["leather_high"])
        # siku (buku jari tulang)
        NS._ball(surface, ex, ey, 5 if not back else 4,
                 c_d, c_m, c_h)
        # otot lengan bawah + urat
        if not back:
            NS._aaline(surface, P["ogre_dark"],
                       (int(ex + ux * 4), int(ey + uy * 4)),
                       (int(gx - ux * 4), int(gy - uy * 4)), 1)
        # sarung tangan kulit berpaku + kepalan
        NS._ball(surface, gx, gy, 5, P["leather_darkest"],
                 P["leather_dark"], P["leather_mid"], P["leather_high"])
        for kx, ky in ((-2, -2), (1, -3), (3, 0)):
            NS._aacircle(surface, P["brass_mid"],
                         (int(gx + kx), int(gy + ky)), 1)

    def _draw_ogre_leg(surface, hipx, hipy, ang, lift, front, f):
        """Kaki ogre: paha -> LUTUT -> betis -> telapak MENAPAK TANAH.

        Rig lama memakai ky = hipy + sin(ang)*20 sehingga pada pose
        diam (ang=0.08) lutut cuma turun ~1.6 px dan seluruh kaki
        berakhir di y=+38 — tertelan perut yang turun sampai +42.
        Di sini panjang tungkai bersifat VERTIKAL (cos) dan ayunan
        yang horizontal (sin), jadi telapak selalu mendarat di
        sekitar GROUND_DY.
        """
        NS = _NS_alchemist
        P = NS.PALETTE
        THIGH, SHIN = 21.0, 19.0
        sa, ca = math.sin(ang), math.cos(ang)
        kx = hipx + sa * THIGH
        ky = hipy + ca * THIGH
        # betis kontra-rotasi (lutut menekuk ke belakang) + angkat
        sa2 = math.sin(-ang * 0.45)
        ca2 = math.cos(-ang * 0.45)
        ax = kx + sa2 * SHIN
        ay = ky + ca2 * SHIN - lift
        if front:
            c_d, c_m, c_h = (P["ogre_dark"], P["ogre_mid"],
                             P["ogre_light"])
            c_s = P["ogre_high"]
            w_th, w_kn, w_sh = 10.0, 7.0, 5.6
        else:
            c_d, c_m, c_h = (P["ogre_darkest"], P["ogre_dark"],
                             P["ogre_mid"])
            c_s = None
            w_th, w_kn, w_sh = 9.0, 6.2, 5.0
        # paha (gemuk) + betis (berotot lalu meruncing ke mata kaki)
        NS._limb(surface, (hipx, hipy), w_th, (kx, ky), w_kn,
                 c_d, c_m, c_h, c_s)
        NS._limb(surface, (kx, ky), w_kn, (ax, ay), w_sh,
                 c_d, c_m, c_h, c_s)
        # tempurung lutut
        NS._ball(surface, kx, ky, 6 if front else 5, c_d, c_m, c_h)
        # ikat betis kulit
        wx, wy = (kx + ax) / 2.0, (ky + ay) / 2.0
        NS._limb(surface, (wx - w_sh, wy - 1), 2.0,
                 (wx + w_sh, wy - 1), 2.0,
                 P["leather_darkest"], P["leather_dark"],
                 P["leather_mid"])
        # ── telapak: boot kulit besar menapak, dengan sol & jari ──
        fy = ay + 4
        toe = f * (9 if front else 7)
        NS._poly(surface, P["shadow_deep"], [
            (int(ax - 7), int(fy + 1)), (int(ax + toe), int(fy + 1)),
            (int(ax + toe), int(fy + 4)), (int(ax - 7), int(fy + 4))])
        NS._poly(surface, P["leather_darkest"], [
            (int(ax - 7), int(fy - 5)), (int(ax + toe * 0.8), int(fy - 5)),
            (int(ax + toe), int(fy)), (int(ax + toe), int(fy + 3)),
            (int(ax - 7), int(fy + 3))])
        NS._poly(surface, P["leather_dark"], [
            (int(ax - 6), int(fy - 4)), (int(ax + toe * 0.7), int(fy - 4)),
            (int(ax + toe - 1), int(fy)), (int(ax + toe - 1), int(fy + 1)),
            (int(ax - 6), int(fy + 1))])
        NS._aaline(surface, P["leather_mid"], (int(ax - 5), int(fy - 3)),
                   (int(ax + toe * 0.6), int(fy - 3)), 1)
        # sol karet + jahitan
        NS._poly(surface, P["metal_darkest"], [
            (int(ax - 7), int(fy + 2)), (int(ax + toe), int(fy + 2)),
            (int(ax + toe), int(fy + 4)), (int(ax - 7), int(fy + 4))])
        for t in (0.25, 0.55, 0.85):
            sxp = int(ax - 6 + (toe + 5) * t)
            NS._aacircle(surface, P["leather_high"], (sxp, int(fy - 1)), 1)
        # cakar kuku tebal mencuat dari ujung boot
        for i in (-1, 1):
            NS._poly(surface, P["bone_mid"], [
                (int(ax + toe), int(fy - 1 + i)),
                (int(ax + toe + f * 3), int(fy + i)),
                (int(ax + toe), int(fy + 1 + i))])

    def _draw_ogre_torso(surface, ox, oy, phase, flare, rage, f):
        """Torso ogre: dada bidang -> pektoral -> perut barel bertekstur.

        Massa dibangun dari DUA volume yang tumpang tindih (dada lebar
        di atas, perut bulat di bawah) bukan satu ellipse raksasa, jadi
        siluetnya punya pinggang dan tidak terbaca sebagai telur.
        """
        NS = _NS_alchemist
        P = NS.PALETTE
        fl = max(0.9, min(1.3, flare))
        breath = math.sin(phase * 0.7) * 0.6
        bw = 23.0 * fl
        bh = 20.0 / fl + breath

        # ── selout massa keseluruhan ──────────────────────────────
        NS._ellipse(surface, P["shadow_deep"],
                    (ox - bw - 2, oy - 10, bw * 2 + 4, bh * 2 + 4))
        NS._ellipse(surface, P["shadow_deep"],
                    (ox - 21, oy - 38, 42, 30))

        # ── PERUT (barel) ramp 5 band, pusat massa digeser ke kanan
        #    bawah supaya terminator terbaca ────────────────────────
        NS._ellipse(surface, P["ogre_darkest"],
                    (ox - bw, oy - 8, bw * 2, bh * 2))
        NS._ellipse(surface, P["ogre_dark"],
                    (ox - bw + 2, oy - 7, bw * 2 - 5, bh * 2 - 4))
        NS._ellipse(surface, P["ogre_mid"],
                    (ox - bw + 4, oy - 6, bw * 2 - 12, bh * 2 - 9))
        NS._ellipse(surface, P["ogre_light"],
                    (ox - bw + 7, oy - 5, bw * 2 - 23, bh * 2 - 17))
        NS._ellipse(surface, P["ogre_high"],
                    (ox - bw + 10, oy - 3, bw * 2 - 34, bh * 2 - 26))

        # ── DADA: dua pektoral berat + tulang selangka ─────────────
        NS._ellipse(surface, P["ogre_darkest"], (ox - 20, oy - 37, 40, 28))
        NS._ellipse(surface, P["ogre_dark"], (ox - 18, oy - 36, 36, 25))
        for sgn in (-1, 1):
            pxp = ox + sgn * 9
            NS._ellipse(surface, P["ogre_mid"],
                        (pxp - 10, oy - 34, 20, 18))
            NS._ellipse(surface, P["ogre_light"],
                        (pxp - 8 - sgn, oy - 33, 15, 13))
            if sgn < 0:                       # pektoral sisi cahaya
                NS._ellipse(surface, P["ogre_high"],
                            (pxp - 7, oy - 32, 10, 8))
        # belahan dada + garis bawah pektoral
        NS._aaline(surface, P["ogre_darkest"], (ox, oy - 33),
                   (ox, oy - 16), 2)
        NS._aaline(surface, P["ogre_dark"], (ox - 16, oy - 19),
                   (ox - 3, oy - 15), 2)
        NS._aaline(surface, P["ogre_dark"], (ox + 3, oy - 15),
                   (ox + 16, oy - 19), 2)
        # tulang selangka
        NS._aaline(surface, P["ogre_light"], (ox - 14, oy - 36),
                   (ox - 3, oy - 34), 1)
        NS._aaline(surface, P["ogre_mid"], (ox + 3, oy - 34),
                   (ox + 14, oy - 36), 1)

        # ── perut: gulungan lemak + pusar (tekstur, bukan dither acak)
        for i, (ry, rw) in enumerate(((-1, 17), (7, 19), (15, 16))):
            NS._aaline(surface, P["ogre_dark"],
                       (ox - rw, oy + ry), (ox + rw - 4, oy + ry + 2), 2)
            NS._aaline(surface, P["ogre_light"],
                       (ox - rw + 1, oy + ry - 1),
                       (ox + rw - 6, oy + ry + 1), 1)
        NS._aacircle(surface, P["ogre_darkest"], (ox + 1, oy + 11), 2)
        NS._aacircle(surface, P["ogre_dark"], (ox + 1, oy + 10), 1)

        # ── specular utama (kiri-atas layar, tetap saat mirror) ────
        NS._ball(surface, ox - bw + 12, oy + 1, 4, P["ogre_light"],
                 P["ogre_high"], P["ogre_shine"])
        NS._aacircle(surface, P["ogre_shine"], (ox - 13, oy - 30), 2)
        NS._aacircle(surface, P["white"], (ox - 14, oy - 31), 1)

        # ── bekas luka & noda asam (cerita karakter) ───────────────
        NS._aaline(surface, P["ogre_high"], (ox + 8, oy - 28),
                   (ox + 13, oy - 18), 1)
        NS._aaline(surface, P["ogre_high"], (ox + 6, oy - 24),
                   (ox + 12, oy - 22), 1)
        for sx_, sy_, rr in ((ox - 9, oy + 6, 3), (ox + 11, oy + 3, 2),
                             (ox + 4, oy + 16, 2)):
            NS._aacircle(surface, (*P["acid_dark"], 110), (sx_, sy_), rr)
            NS._aacircle(surface, (*P["acid_mid"], 90), (sx_, sy_), rr - 1)

        # ── denyut vena saat rage ─────────────────────────────────
        if rage:
            pul = 0.5 + 0.5 * math.sin(phase * 6.0)
            a = int(110 + 120 * pul)
            for x0_, y0_, x1_, y1_ in ((-14, -22, -6, -10),
                                       (-6, -10, -9, 2),
                                       (9, -26, 13, -14),
                                       (13, -14, 9, -2)):
                NS._aaline(surface, (*P["acid_bright"], a),
                           (ox + x0_, oy + y0_), (ox + x1_, oy + y1_), 2)
            NS._aacircle(surface, (*P["acid_hot"], int(a * 0.6)),
                         (ox - 6, oy - 10), 3)

    def _draw_ogre_armor(surface, ox, oy, phase, f, rage):
        """Harness X berjahit + pauldron baja berpaku + sabuk kuningan
        + botol sabuk. Semua plat punya bevel (gelap->mid->kilau) supaya
        terbaca sebagai logam, bukan kotak datar."""
        NS = _NS_alchemist
        P = NS.PALETTE

        # ── tali harness diagonal (dua arah, dengan jahitan) ───────
        for sgn in (1, -1):
            x0, y0 = ox - sgn * 16, oy - 35
            x1, y1 = ox + sgn * 15, oy + 6
            NS._limb(surface, (x0, y0), 3.4, (x1, y1), 3.0,
                     P["leather_darkest"], P["leather_dark"],
                     P["leather_mid"], P["leather_high"])
            for t in (0.22, 0.42, 0.62, 0.82):
                sxp = int(x0 + (x1 - x0) * t)
                syp = int(y0 + (y1 - y0) * t)
                NS._aacircle(surface, P["leather_high"], (sxp, syp), 1)
                NS._aacircle(surface, P["brass_dark"], (sxp, syp + 2), 1)

        # ── gesper dada: plat kuningan + sigil asam ────────────────
        NS._poly(surface, P["brass_dark"], [
            (ox - 6, oy - 18), (ox + 6, oy - 18), (ox + 7, oy - 10),
            (ox, oy - 6), (ox - 7, oy - 10)])
        NS._poly(surface, P["brass_mid"], [
            (ox - 5, oy - 17), (ox + 5, oy - 17), (ox + 5, oy - 11),
            (ox, oy - 8), (ox - 5, oy - 11)])
        NS._aaline(surface, P["brass_shine"], (ox - 4, oy - 16),
                   (ox + 3, oy - 16), 1)
        glow = 0.5 + 0.5 * math.sin(phase * 2.2)
        NS._aacircle(surface, P["acid_dark"], (ox, oy - 13), 3)
        NS._aacircle(surface, (*P["acid_bright"], int(170 + 80 * glow)),
                     (ox, oy - 13), 2)
        NS._aacircle(surface, P["acid_glow"], (ox - 1, oy - 14), 1)

        # (pauldron depan digambar terpisah lewat _draw_pauldron, SETELAH
        #  lengan depan — kalau digambar di sini, deltoid ogre menimpanya
        #  dan bahu terlihat seperti bola telanjang; itu cacat rig lama.)

    def _draw_pauldron(surface, ox, oy, phase, f, rage):
        """Plat bahu depan berlapis + paku keling + duri baja."""
        NS = _NS_alchemist
        P = NS.PALETTE
        px, py = ox + f * 23, oy - 31
        NS._ellipse(surface, P["shadow_deep"], (px - 12, py - 7, 24, 18))
        NS._ellipse(surface, P["metal_darkest"], (px - 11, py - 7, 22, 17))
        NS._ellipse(surface, P["metal_dark"], (px - 10, py - 6, 19, 14))
        NS._ellipse(surface, P["metal_mid"], (px - 8, py - 5, 14, 10))
        NS._ellipse(surface, P["metal_light"], (px - 7, py - 4, 9, 6))
        NS._aacircle(surface, P["metal_shine"], (px - 5, py - 3), 2)
        NS._aacircle(surface, P["white"], (px - 6, py - 4), 1)
        # lapis kedua (lame bawah)
        NS._ellipse(surface, P["metal_darkest"], (px - 10, py + 5, 20, 8))
        NS._ellipse(surface, P["metal_dark"], (px - 9, py + 5, 18, 6))
        NS._aaline(surface, P["metal_mid"], (px - 7, py + 7),
                   (px + 6, py + 7), 1)
        # paku keling
        for rv in ((-7, -1), (-1, -5), (5, -1), (2, 4)):
            NS._aacircle(surface, P["metal_darkest"],
                         (px + rv[0], py + rv[1] + 1), 2)
            NS._aacircle(surface, P["metal_light"],
                         (px + rv[0], py + rv[1]), 1)
        # duri baja di puncak pauldron
        NS._poly(surface, P["metal_dark"], [
            (px - 3, py - 6), (px + 1, py - 13), (px + 4, py - 5)])
        NS._poly(surface, P["metal_light"], [
            (px - 1, py - 6), (px + 1, py - 12), (px + 2, py - 6)])
        if rage:
            pul = 0.5 + 0.5 * math.sin(phase * 5.0)
            NS._aacircle(surface, (*P["acid_hot"], int(110 + 120 * pul)),
                         (px, py - 1), 4)
            NS._aacircle(surface, (*P["acid_glow"], int(90 + 100 * pul)),
                         (px, py - 1), 2)

        return

    def _draw_belt(surface, ox, oy, phase, f, rage):
        """Sabuk pinggang tebal + gesper kuningan + botol sabuk."""
        NS = _NS_alchemist
        P = NS.PALETTE
        # ── SABUK pinggang tebal + gesper besar + botol sabuk ──────
        NS._poly(surface, P["shadow_deep"], [
            (ox - 24, oy + 13), (ox + 24, oy + 13), (ox + 23, oy + 25),
            (ox - 23, oy + 25)])
        NS._poly(surface, P["leather_darkest"], [
            (ox - 23, oy + 13), (ox + 23, oy + 13), (ox + 22, oy + 24),
            (ox - 22, oy + 24)])
        NS._poly(surface, P["leather_dark"], [
            (ox - 21, oy + 14), (ox + 21, oy + 14), (ox + 20, oy + 22),
            (ox - 20, oy + 22)])
        NS._aaline(surface, P["leather_mid"], (ox - 20, oy + 16),
                   (ox + 19, oy + 16), 2)
        NS._aaline(surface, P["leather_high"], (ox - 19, oy + 15),
                   (ox + 5, oy + 15), 1)
        # lubang sabuk
        for i in range(-3, 4):
            NS._aacircle(surface, P["leather_darkest"],
                         (ox + i * 6, oy + 20), 1)
        # gesper kuningan besar
        NS._poly(surface, P["brass_dark"], [
            (ox - 8, oy + 12), (ox + 8, oy + 12), (ox + 8, oy + 25),
            (ox - 8, oy + 25)])
        NS._poly(surface, P["brass_mid"], [
            (ox - 6, oy + 14), (ox + 6, oy + 14), (ox + 6, oy + 23),
            (ox - 6, oy + 23)])
        NS._poly(surface, P["brass_light"], [
            (ox - 5, oy + 15), (ox + 5, oy + 15), (ox + 5, oy + 17),
            (ox - 5, oy + 17)])
        NS._aacircle(surface, P["gold_shine"], (ox, oy + 19), 3)
        NS._aacircle(surface, P["gold_light"], (ox, oy + 19), 2)
        NS._aacircle(surface, P["white"], (ox - 1, oy + 18), 1)
        # botol kecil tergantung di sabuk (sisi belakang)
        for i, bxo in enumerate((-18, -13)):
            byo = oy + 25 + (i % 2)
            NS._poly(surface, P["glass_dark"],
                     [(ox + bxo - 2, byo), (ox + bxo + 2, byo),
                      (ox + bxo + 3, byo + 7), (ox + bxo - 3, byo + 7)])
            NS._poly(surface, P["acid_mid"],
                     [(ox + bxo - 2, byo + 3), (ox + bxo + 2, byo + 3),
                      (ox + bxo + 2, byo + 6), (ox + bxo - 2, byo + 6)])
            NS._aacircle(surface, P["glass_shine"],
                         (ox + bxo - 1, byo + 2), 1)
            NS._aaline(surface, P["brass_mid"], (ox + bxo - 2, byo),
                       (ox + bxo + 2, byo), 1)

    def _draw_backpack(surface, bx, by, phase, f, rage):
        """Rangka kayu + tabung distilasi + 3 botol ramuan mendidih."""
        NS = _NS_alchemist
        P = NS.PALETTE
        # ── rangka kayu berikat besi ──────────────────────────────
        NS._poly(surface, P["shadow_deep"], [
            (bx - 11, by - 15), (bx + 10, by - 16), (bx + 11, by + 14),
            (bx - 10, by + 15)])
        NS._poly(surface, P["leather_darkest"], [
            (bx - 10, by - 14), (bx + 9, by - 15), (bx + 10, by + 13),
            (bx - 9, by + 14)])
        NS._poly(surface, P["leather_dark"], [
            (bx - 8, by - 12), (bx + 7, by - 13), (bx + 8, by + 11),
            (bx - 7, by + 12)])
        NS._poly(surface, P["leather_mid"], [
            (bx - 6, by - 10), (bx + 2, by - 11), (bx + 3, by + 2),
            (bx - 5, by + 3)])
        # papan kayu vertikal
        for i in (-4, 1, 6):
            NS._aaline(surface, P["leather_darkest"],
                       (bx + i, by - 13), (bx + i + 1, by + 12), 1)
        # ikat besi horizontal
        for yy in (-9, 3):
            NS._aaline(surface, P["metal_dark"], (bx - 10, by + yy),
                       (bx + 10, by + yy), 2)
            NS._aaline(surface, P["metal_light"], (bx - 9, by + yy - 1),
                       (bx + 4, by + yy - 1), 1)
            for rv in (-7, 0, 7):
                NS._aacircle(surface, P["metal_shine"],
                             (bx + rv, by + yy), 1)

        # ── 3 botol ramuan berdiri di rak atas ────────────────────
        boil = phase * 3.0
        for i, (bxo, h, key) in enumerate((
                (-7, 11, "acid"), (0, 14, "acid"), (7, 10, "gold"))):
            tx = bx + bxo
            ty = by - 14
            liquid = (P["acid_mid"], P["acid_bright"], P["acid_glow"]) \
                if key == "acid" else (P["gold_dark"], P["gold_mid"],
                                       P["gold_light"])
            # kaca badan botol
            NS._poly(surface, P["shadow_deep"], [
                (tx - 4, ty - h), (tx + 4, ty - h), (tx + 5, ty + 1),
                (tx - 5, ty + 1)])
            NS._poly(surface, P["glass_dark"], [
                (tx - 4, ty - h + 1), (tx + 4, ty - h + 1),
                (tx + 4, ty), (tx - 4, ty)])
            # cairan (permukaan bergoyang)
            lv = ty - h * 0.55 + math.sin(boil + i * 2.1) * 0.8
            NS._poly(surface, liquid[0],
                     [(tx - 4, lv), (tx + 4, lv), (tx + 4, ty),
                      (tx - 4, ty)])
            NS._poly(surface, liquid[1],
                     [(tx - 3, lv + 1), (tx + 2, lv + 1), (tx + 2, ty - 1),
                      (tx - 3, ty - 1)])
            NS._aaline(surface, liquid[2], (tx - 4, lv), (tx + 4, lv), 1)
            # gelembung mendidih
            for b in range(2):
                bt = (boil * 0.7 + i * 0.5 + b * 0.5) % 1.0
                NS._aacircle(surface, (*liquid[2], int(200 * (1 - bt))),
                             (int(tx - 2 + b * 3),
                              int(ty - 1 - bt * (h * 0.5))), 1)
            # kilau kaca + leher + sumbat gabus
            NS._aaline(surface, P["glass_shine"], (tx - 3, ty - h + 3),
                       (tx - 3, ty - 3), 1)
            NS._poly(surface, P["glass_mid"], [
                (tx - 2, ty - h - 2), (tx + 2, ty - h - 2),
                (tx + 2, ty - h + 1), (tx - 2, ty - h + 1)])
            NS._poly(surface, P["leather_mid"], [
                (tx - 2, ty - h - 4), (tx + 2, ty - h - 4),
                (tx + 2, ty - h - 2), (tx - 2, ty - h - 2)])
            NS._aacircle(surface, P["leather_high"], (tx - 1, ty - h - 4), 1)
            # asap tipis dari botol tengah
            if i == 1:
                for s_ in range(3):
                    st = (boil * 0.35 + s_ * 0.33) % 1.0
                    NS._aacircle(
                        surface, (*P["acid_glow"], int(120 * (1 - st))),
                        (int(tx + math.sin(boil + s_) * 3),
                         int(ty - h - 5 - st * 9)),
                        1 + int(st * 2))

        # ── pipa distilasi tembaga melingkar di sisi ──────────────
        for a in range(5):
            t = a / 4.0
            NS._aacircle(surface, P["brass_dark"],
                         (int(bx + 11 - math.sin(t * 3.1) * 3),
                          int(by - 6 + t * 16)), 2)
            NS._aacircle(surface, P["brass_light"],
                         (int(bx + 10 - math.sin(t * 3.1) * 3),
                          int(by - 7 + t * 16)), 1)
        if rage:
            pul = 0.5 + 0.5 * math.sin(phase * 5.0)
            NS._aacircle(surface, (*P["acid_hot"], int(70 + 70 * pul)),
                         (bx, by - 6), 13)

    def _draw_ogre_head(surface, hx, hy, f, phase, action, rage):
        """Kepala ogre: tengkorak berat, brow menggantung, mata cekung
        menyala, hidung bulat, RAHANG UNDERBITE menonjol ke depan dengan
        gigi taring bawah, telinga lebar, ikat kain + war-paint asam."""
        NS = _NS_alchemist
        P = NS.PALETTE
        nod = int(math.sin(phase * 0.9)) if action == "idle" else 0
        hy += nod

        # ── telinga lebar (di belakang tengkorak) ─────────────────
        for sgn in (-1, 1):
            ex = hx + sgn * 12
            flick = int(math.sin(phase * 1.6 + sgn) * 1.2)
            tip = (ex + sgn * 10, hy - 8 + flick)
            NS._poly(surface, P["shadow_deep"], [
                (ex, hy - 5), tip, (ex + sgn * 8, hy + 5)])
            NS._poly(surface, P["ogre_darkest"], [
                (ex, hy - 4), (tip[0] - sgn, tip[1] + 1),
                (ex + sgn * 7, hy + 4)])
            NS._poly(surface, P["ogre_dark" if sgn < 0 else "ogre_darkest"],
                     [(ex + sgn, hy - 3), (tip[0] - sgn * 3, tip[1] + 2),
                      (ex + sgn * 5, hy + 2)])
            if sgn < 0:                     # telinga sisi cahaya
                NS._aaline(surface, P["ogre_mid"], (ex - 1, hy - 2),
                           (tip[0] + 3, tip[1] + 3), 1)
            # anting kuningan
            NS._aacircle(surface, P["brass_mid"],
                         (ex + sgn * 6, hy + 4), 2, 1)

        # ── TENGKORAK: massa utama + ramp ─────────────────────────
        NS._ellipse(surface, P["shadow_deep"], (hx - 14, hy - 15, 28, 28))
        NS._ellipse(surface, P["ogre_darkest"], (hx - 13, hy - 14, 26, 26))
        NS._ellipse(surface, P["ogre_dark"], (hx - 12, hy - 13, 23, 23))
        NS._ellipse(surface, P["ogre_mid"], (hx - 10, hy - 12, 18, 18))
        NS._ellipse(surface, P["ogre_light"], (hx - 9, hy - 11, 12, 12))
        NS._ellipse(surface, P["ogre_high"], (hx - 8, hy - 10, 7, 7))

        # ── RAHANG UNDERBITE menonjol ke arah hadap ───────────────
        jx = hx + f * 5
        NS._ellipse(surface, P["shadow_deep"], (jx - 11, hy + 1, 22, 15))
        NS._ellipse(surface, P["ogre_darkest"], (jx - 10, hy + 1, 20, 14))
        NS._ellipse(surface, P["ogre_dark"], (jx - 9, hy + 2, 18, 11))
        NS._ellipse(surface, P["ogre_mid"], (jx - 7, hy + 3, 13, 8))
        NS._ellipse(surface, P["ogre_light"], (jx - 6, hy + 4, 7, 4))
        # garis mulut
        NS._aaline(surface, P["ogre_darkest"], (jx - 8, hy + 4),
                   (jx + 8, hy + 4), 2)
        NS._aaline(surface, P["shadow_deep"], (jx - 7, hy + 5),
                   (jx + 7, hy + 5), 1)

        # ── TARING bawah besar mencuat ke atas (khas ogre) ────────
        for tx_, hgt in ((jx - 6, 8), (jx + 6, 9)):
            NS._poly(surface, P["shadow_deep"], [
                (tx_ - 3, hy + 5), (tx_ + 3, hy + 5),
                (tx_ + 1, hy + 5 - hgt)])
            NS._poly(surface, P["bone_dark"], [
                (tx_ - 3, hy + 4), (tx_ + 3, hy + 4),
                (tx_ + 1, hy + 4 - hgt)])
            NS._poly(surface, P["bone_mid"], [
                (tx_ - 2, hy + 4), (tx_ + 2, hy + 4),
                (tx_ + 1, hy + 5 - hgt)])
            NS._poly(surface, P["bone_light"], [
                (tx_ - 2, hy + 3), (tx_, hy + 3),
                (tx_ + 0, hy + 6 - hgt)])
        # gigi kecil atas
        for i in range(-2, 3):
            NS._poly(surface, P["bone_dark"], [
                (jx + i * 3 - 1, hy + 4), (jx + i * 3 + 1, hy + 4),
                (jx + i * 3, hy + 7)])

        # ── BROW RIDGE berat menggantung (bayangan mata) ──────────
        NS._poly(surface, P["ogre_darkest"], [
            (hx - 12, hy - 6), (hx + 11, hy - 6), (hx + 10, hy + 1),
            (hx - 11, hy + 1)])
        NS._poly(surface, P["ogre_dark"], [
            (hx - 11, hy - 6), (hx + 10, hy - 6), (hx + 9, hy - 3),
            (hx - 10, hy - 3)])
        NS._aaline(surface, P["ogre_mid"], (hx - 10, hy - 6),
                   (hx + 2, hy - 7), 1)
        # kerut dahi
        NS._aaline(surface, P["ogre_darkest"], (hx - 8, hy - 9),
                   (hx + 6, hy - 10), 1)
        NS._aaline(surface, P["ogre_darkest"], (hx - 6, hy - 12),
                   (hx + 4, hy - 12), 1)

        # ── MATA cekung di bawah brow, menyala ────────────────────
        blink = 1 if (phase % (math.pi * 5.0)) < 0.14 else 0
        eye_c = P["eye_rage"] if rage else P["eye_hot"]
        for ex in (hx - 6, hx + 5):
            NS._ellipse(surface, P["shadow_deep"], (ex - 4, hy - 3, 8, 6))
            if blink:
                NS._aaline(surface, P["ogre_dark"], (ex - 3, hy),
                           (ex + 3, hy), 2)
                continue
            NS._ellipse(surface, P["eye_dark"], (ex - 3, hy - 2, 6, 5))
            NS._aacircle(surface, (*eye_c, 90), (ex, hy), 4)
            NS._aacircle(surface, eye_c, (ex, hy), 2)
            NS._aacircle(surface, P["white"], (ex - 1, hy - 1), 1)

        # ── hidung bulat besar dengan lubang ──────────────────────
        nx = hx + f * 2
        NS._ellipse(surface, P["ogre_dark"], (nx - 5, hy + 1, 10, 7))
        NS._ellipse(surface, P["ogre_mid"], (nx - 4, hy + 1, 8, 5))
        NS._aacircle(surface, P["ogre_light"], (nx - 2, hy + 2), 2)
        NS._aacircle(surface, P["ogre_darkest"], (nx - 2, hy + 5), 1)
        NS._aacircle(surface, P["ogre_darkest"], (nx + 2, hy + 5), 1)

        # ── ikat kain: MELENGKUNG mengikuti tempurung kepala
        #    (rig lama memakai persegi panjang datar yang memotong
        #    tengkorak jadi dua — itu yang membuat kepala terbaca
        #    seperti kotak) ──────────────────────────────────────────
        band = []
        for i in range(11):
            t = i / 10.0
            axp = hx - 13 + t * 26
            ayp = hy - 9 - math.sin(t * math.pi) * 6.5
            band.append((axp, ayp))
        low = [(x_, y_ + 6) for x_, y_ in reversed(band)]
        NS._poly(surface, P["shadow_deep"],
                 [(x_, y_ - 1) for x_, y_ in band] +
                 [(x_, y_ + 1) for x_, y_ in low])
        NS._poly(surface, P["leather_darkest"], band + low)
        NS._poly(surface, P["leather_dark"],
                 [(x_, y_ + 1) for x_, y_ in band] +
                 [(x_, y_ - 1) for x_, y_ in low])
        # lipatan kain + kilau sisi cahaya
        mid_band = [(x_, y_ + 3) for x_, y_ in band]
        NS._aalines_soft(surface, P["leather_mid"], mid_band, 2)
        NS._aalines_soft(surface, P["leather_high"], mid_band[:5], 1)
        for i in (2, 4, 6, 8):
            NS._aaline(surface, P["leather_darkest"],
                       (int(band[i][0]), int(band[i][1] + 1)),
                       (int(band[i][0] + 1), int(band[i][1] + 5)), 1)
        # simpul kain menjuntai di belakang
        kx = hx - f * 13
        NS._poly(surface, P["leather_dark"], [
            (kx, hy - 13), (kx - f * 6, hy - 9), (kx - f * 4, hy - 4),
            (kx, hy - 8)])
        NS._aaline(surface, P["leather_mid"], (kx - f, hy - 12),
                   (kx - f * 5, hy - 8), 1)
        # war-paint asam di pipi
        NS._aaline(surface, P["acid_mid"], (hx - 8, hy - 1),
                   (hx - 5, hy + 8), 2)
        NS._aaline(surface, P["acid_bright"], (hx - 8, hy - 1),
                   (hx - 6, hy + 4), 1)
        NS._aaline(surface, P["acid_mid"], (hx + 7, hy - 1),
                   (hx + 4, hy + 8), 2)

    def _draw_acid_gun(surface, hx, hy, ang, f, firing, phase):
        """Acid gun goblin: laras kuningan, tangki kaca, moncong corong."""
        NS = _NS_alchemist
        P = NS.PALETTE
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca

        def pt(dist, side):
            return (int(hx + ca * dist + px * side),
                    int(hy + sa * dist + py * side))

        # ── laras utama (kuningan, ber-bevel) ─────────────────────
        NS._limb(surface, pt(-3, 0), 3.4, pt(12, 0), 2.8,
                 P["brass_dark"], P["brass_mid"], P["brass_light"],
                 P["brass_shine"])
        # cincin penguat laras
        for d in (2, 7):
            NS._limb(surface, pt(d, -4), 1.4, pt(d, 4), 1.4,
                     P["brass_dark"], P["brass_mid"], P["brass_light"])
        # ── moncong corong ────────────────────────────────────────
        NS._poly(surface, P["brass_dark"], [
            pt(11, -3), pt(15, -5), pt(15, 5), pt(11, 3)])
        NS._poly(surface, P["brass_mid"], [
            pt(12, -2), pt(14, -4), pt(14, 4), pt(12, 2)])
        NS._aaline(surface, P["brass_shine"], pt(12, -2), pt(14, -4), 1)
        # ── tangki kaca asam di punggung laras ────────────────────
        tk = pt(4, -6)
        slosh = math.sin(phase * 2.2) * 0.8
        NS._ellipse(surface, P["shadow_deep"], (tk[0] - 5, tk[1] - 4, 10, 9))
        NS._ellipse(surface, P["glass_dark"], (tk[0] - 4, tk[1] - 4, 8, 8))
        NS._ellipse(surface, P["acid_mid"],
                    (tk[0] - 3, tk[1] - 1 + slosh, 6, 4))
        NS._ellipse(surface, P["acid_bright"],
                    (tk[0] - 2, tk[1] + slosh, 4, 2))
        NS._aacircle(surface, P["glass_shine"], (tk[0] - 2, tk[1] - 2), 1)
        # selang tangki -> laras
        NS._aaline(surface, P["metal_dark"], (tk[0] + 3, tk[1] + 2),
                   pt(8, -2), 2)
        NS._aaline(surface, P["metal_light"], (tk[0] + 3, tk[1] + 1),
                   pt(8, -3), 1)
        # ── pegangan pistol + pelatuk ─────────────────────────────
        NS._limb(surface, pt(0, 3), 3.0, pt(-2, 9), 2.4,
                 P["leather_darkest"], P["leather_dark"], P["leather_mid"])
        NS._aaline(surface, P["metal_mid"], pt(2, 3), pt(1, 6), 1)
        NS._poly(surface, P["metal_dark"], [
            pt(3, 3), pt(4, 8), pt(0, 9), pt(0, 7)])
        # ── moncong: tetes saat idle, semburan saat menembak ──────
        mz = pt(15, 0)
        if firing:
            NS._aacircle(surface, (*P["acid_glow"], 120), mz, 8)
            NS._aacircle(surface, (*P["acid_white"], 235), mz, 5)
            NS._aacircle(surface, P["acid_hot"], mz, 3)
            NS._aacircle(surface, P["white"], mz, 1)
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
        bob = math.sin(phase * 1.1) * 1.2
        gy += bob

        # ── kaki mencangkung mencengkeram bahu ogre ───────────────
        for sgn in (-1, 1):
            kx = gx + sgn * 5
            NS._limb(surface, (gx + sgn * 3, gy + 3), 3.0,
                     (kx + f * 2, gy + 9), 2.4,
                     P["gob_darkest"], P["gob_dark"], P["gob_mid"])
            NS._limb(surface, (kx + f * 2, gy + 9), 2.4,
                     (kx + f * 6, gy + 12), 2.0,
                     P["gob_darkest"], P["gob_dark"], P["gob_mid"])
            NS._aacircle(surface, P["leather_dark"],
                         (int(kx + f * 6), int(gy + 12)), 2)

        # ── torso kecil + rompi kulit berkantong ──────────────────
        NS._ellipse(surface, P["shadow_deep"], (gx - 7, gy - 9, 14, 18))
        NS._ellipse(surface, P["gob_darkest"], (gx - 6, gy - 8, 12, 16))
        NS._ellipse(surface, P["gob_dark"], (gx - 5, gy - 7, 10, 13))
        NS._ellipse(surface, P["gob_mid"], (gx - 4, gy - 6, 6, 9))
        NS._aacircle(surface, P["gob_light"], (gx - 2, gy - 4), 2)
        # rompi + tali bandolier botol mini
        NS._poly(surface, P["leather_darkest"], [
            (gx - 5, gy - 4), (gx + 5, gy - 4), (gx + 4, gy + 5),
            (gx - 4, gy + 5)])
        NS._poly(surface, P["leather_dark"], [
            (gx - 4, gy - 3), (gx + 4, gy - 3), (gx + 3, gy + 4),
            (gx - 3, gy + 4)])
        NS._aaline(surface, P["leather_mid"], (gx - 4, gy - 2),
                   (gx + 4, gy + 2), 2)
        for i, bxo in enumerate((-3, 0, 3)):
            NS._aacircle(surface, P["acid_bright"],
                         (gx + bxo, gy - 1 + i), 1)
        NS._aacircle(surface, P["brass_light"], (gx, gy + 2), 1)

        # ── telinga panjang goblin ────────────────────────────────
        for sgn in (-1, 1):
            ex = gx + sgn * 4
            flick = math.sin(phase * 2.2 + sgn * 1.5) * 1.5
            tip = (ex + sgn * 9, gy - 17 + flick)
            NS._poly(surface, P["shadow_deep"], [
                (ex, gy - 13), tip, (ex + sgn * 5, gy - 9)])
            NS._poly(surface, P["gob_darkest"], [
                (ex, gy - 12), (tip[0] - sgn, tip[1] + 1),
                (ex + sgn * 4, gy - 9)])
            NS._poly(surface, P["gob_dark"], [
                (ex + sgn, gy - 12), (tip[0] - sgn * 3, tip[1] + 2),
                (ex + sgn * 3, gy - 10)])

        # ── kepala + moncong runcing ──────────────────────────────
        NS._ellipse(surface, P["shadow_deep"], (gx - 7, gy - 18, 14, 13))
        NS._ellipse(surface, P["gob_darkest"], (gx - 6, gy - 17, 12, 12))
        NS._ellipse(surface, P["gob_dark"], (gx - 5, gy - 16, 10, 10))
        NS._ellipse(surface, P["gob_mid"], (gx - 5, gy - 16, 7, 7))
        NS._ellipse(surface, P["gob_light"], (gx - 4, gy - 15, 4, 4))
        # hidung bengkok panjang
        NS._poly(surface, P["gob_dark"], [
            (gx + f * 2, gy - 12), (gx + f * 9, gy - 9),
            (gx + f * 2, gy - 8)])
        NS._poly(surface, P["gob_mid"], [
            (gx + f * 2, gy - 11), (gx + f * 7, gy - 9),
            (gx + f * 2, gy - 9)])
        NS._aacircle(surface, P["gob_high"], (int(gx + f * 4), gy - 10), 1)
        # senyum snaggle-tooth
        NS._aaline(surface, P["gob_darkest"], (gx - f * 1, gy - 7),
                   (gx + f * 4, gy - 8), 1)
        NS._poly(surface, P["bone_light"], [
            (gx + f * 2, gy - 8), (gx + f * 3, gy - 8),
            (gx + f * 2, gy - 5)])
        # mata + goggle sebelah
        eye = P["eye_rage"] if rage else P["eye_hot"]
        NS._aacircle(surface, (*eye, 110), (int(gx + f * 1), gy - 13), 3)
        NS._aacircle(surface, eye, (int(gx + f * 1), gy - 13), 1)
        NS._aacircle(surface, P["metal_dark"], (int(gx - f * 3), gy - 13), 3)
        NS._aacircle(surface, P["glass_mid"], (int(gx - f * 3), gy - 13), 2)
        NS._aacircle(surface, P["glass_shine"],
                     (int(gx - f * 4), gy - 14), 1)
        NS._aaline(surface, P["leather_dark"], (gx - f * 6, gy - 13),
                   (gx + f * 5, gy - 14), 1)

        # ── topi alkemis lancip berikat kuningan ──────────────────
        tilt = f * 2
        NS._poly(surface, P["shadow_deep"], [
            (gx - 9, gy - 18), (gx + 9, gy - 18), (gx + 8, gy - 21),
            (gx - 8, gy - 21)])
        NS._poly(surface, P["leather_darkest"], [
            (gx - 9, gy - 19), (gx + 9, gy - 19), (gx + 7, gy - 22),
            (gx - 7, gy - 22)])
        NS._poly(surface, P["leather_dark"], [
            (gx - 7, gy - 20), (gx + 7, gy - 20), (gx + 6, gy - 22),
            (gx - 6, gy - 22)])
        # kerucut topi
        NS._poly(surface, P["shadow_deep"], [
            (gx - 7, gy - 21), (gx + 7, gy - 21),
            (gx + tilt + 2, gy - 33)])
        NS._poly(surface, P["leather_darkest"], [
            (gx - 6, gy - 21), (gx + 6, gy - 21),
            (gx + tilt + 1, gy - 32)])
        NS._poly(surface, P["leather_dark"], [
            (gx - 5, gy - 22), (gx + 4, gy - 22),
            (gx + tilt + 1, gy - 31)])
        NS._poly(surface, P["leather_mid"], [
            (gx - 4, gy - 22), (gx - 1, gy - 22),
            (gx + tilt, gy - 30)])
        # band kuningan + botol kecil terselip
        NS._poly(surface, P["brass_dark"], [
            (gx - 7, gy - 23), (gx + 7, gy - 23), (gx + 6, gy - 26),
            (gx - 6, gy - 26)])
        NS._poly(surface, P["brass_mid"], [
            (gx - 6, gy - 24), (gx + 6, gy - 24), (gx + 5, gy - 25),
            (gx - 5, gy - 25)])
        NS._aacircle(surface, P["brass_shine"], (gx - 4, gy - 25), 1)
        glow = 0.5 + 0.5 * math.sin(phase * 3.0)
        NS._aacircle(surface, (*P["acid_glow"], int(90 + 90 * glow)),
                     (int(gx + 4), gy - 25), 3)
        NS._aacircle(surface, P["acid_hot"], (int(gx + 4), gy - 25), 1)
        # ujung topi menjuntai
        NS._aacircle(surface, P["gold_light"],
                     (int(gx + tilt + 1), gy - 32), 2)
        NS._aacircle(surface, P["gold_shine"],
                     (int(gx + tilt), gy - 33), 1)

        # Lengan + senjata goblin digambar TERPISAH (_draw_goblin_arms)
        # SETELAH kepala ogre, kalau tidak laras senapan & botol W
        # tenggelam di belakang tengkorak ogre — cacat rig lama.
        return NS._draw_goblin_arms(surface, gx, gy - bob, f, phase,
                                    action, ap, rage, aim_angle)

    def _draw_goblin_arms(surface, gx, gy, f, phase, action, ap,
                          rage, aim_angle=None):
        """Lengan + senjata goblin (lapisan DEPAN, di atas kepala ogre).

        Return (gun_hand, bottle_hand) dalam piksel layar.
        """
        NS = _NS_alchemist
        P = NS.PALETTE
        gy += math.sin(phase * 1.1) * 1.2
        gun_hand = (gx + f * 9, gy - 4)
        bottle_hand = (gx + f * 3, gy - 10)
        aim_ang = (float(aim_angle) if aim_angle is not None
                   else -0.1 + math.sin(phase) * 0.06)

        def arm(p0, p1, bulge=2.5):
            """Lengan goblin bersiku."""
            dxx, dyy = p1[0] - p0[0], p1[1] - p0[1]
            lnn = max(1.0, math.hypot(dxx, dyy))
            exx = p0[0] + dxx * 0.5 - dyy / lnn * bulge
            eyy = p0[1] + dyy * 0.5 + dxx / lnn * bulge + 1.5
            NS._limb(surface, p0, 3.0, (exx, eyy), 2.4,
                     P["gob_darkest"], P["gob_dark"], P["gob_mid"])
            NS._limb(surface, (exx, eyy), 2.4, p1, 1.9,
                     P["gob_darkest"], P["gob_dark"], P["gob_mid"])
            NS._aacircle(surface, P["leather_dark"],
                         (int(p1[0]), int(p1[1])), 2)

        if action == "q_cast":
            gun_hand = (gx + f * 8, gy - 6)
            arm((gx + f * 3, gy - 4), gun_hand)
            arm((gx - f * 3, gy - 3), (gx + f * 2, gy - 1), -2.0)
            recoil = math.sin(phase * 8.0) * 1.2
            mz = NS._draw_acid_gun(surface, gun_hand[0] + f * 2,
                                   gun_hand[1] + recoil, aim_ang, f,
                                   firing=True, phase=phase)
            gun_hand = mz
        elif action == "w_cast":
            trem = 1 if int(phase * 26) % 2 else 0
            bottle_hand = (gx + f * (2 + trem), gy - 30)
            arm((gx + f * 2, gy - 5), bottle_hand, 3.5)
            arm((gx - f * 3, gy - 4), (gx - f * 7, gy + 1), -2.0)
            # ── BOTOL UNSTABLE CONCOCTION (kaca + cairan mendidih) ─
            bxp, byp = int(bottle_hand[0]), int(bottle_hand[1])
            glow2 = 0.5 + 0.5 * math.sin(phase * 6.0)
            NS._aacircle(surface, (*P["acid_glow"], int(60 + 70 * glow2)),
                         (bxp, byp), 11)
            NS._aacircle(surface, (*P["acid_hot"], int(90 + 90 * glow2)),
                         (bxp, byp), 7)
            NS._ellipse(surface, P["shadow_deep"], (bxp - 6, byp - 5, 12, 13))
            NS._ellipse(surface, P["glass_dark"], (bxp - 5, byp - 4, 10, 11))
            NS._ellipse(surface, P["acid_dark"], (bxp - 4, byp - 1, 8, 7))
            NS._ellipse(surface, P["acid_bright"], (bxp - 3, byp, 6, 5))
            NS._ellipse(surface, P["acid_hot"], (bxp - 2, byp + 1, 3, 3))
            NS._aaline(surface, P["glass_shine"], (bxp - 4, byp - 2),
                       (bxp - 4, byp + 3), 1)
            # leher + sumbat
            NS._poly(surface, P["glass_mid"], [
                (bxp - 2, byp - 8), (bxp + 2, byp - 8),
                (bxp + 2, byp - 4), (bxp - 2, byp - 4)])
            NS._poly(surface, P["leather_mid"], [
                (bxp - 2, byp - 10), (bxp + 2, byp - 10),
                (bxp + 2, byp - 8), (bxp - 2, byp - 8)])
            # gelembung
            for b in range(3):
                bt = (phase * 0.8 + b * 0.33) % 1.0
                NS._aacircle(surface, (*P["acid_glow"], int(220 * (1 - bt))),
                             (bxp - 2 + b * 2, int(byp + 2 - bt * 6)), 1)
        else:
            gun_hand = (gx + f * 8, gy - 8)
            arm((gx + f * 3, gy - 5), gun_hand)
            mz = NS._draw_acid_gun(surface, gun_hand[0], gun_hand[1],
                                   -0.55 + math.sin(phase * 0.9) * 0.08,
                                   f, firing=False, phase=phase)
            gun_hand = mz
            if action in ("e_cast", "r_cast"):
                pump = math.sin(phase * 3.0) * 3
                bottle_hand = (gx - f * 6, gy - 14 - pump)
                arm((gx - f * 3, gy - 4), bottle_hand, -3.0)
                bxp, byp = int(bottle_hand[0]), int(bottle_hand[1])
                if action == "r_cast":
                    c0, c1, c2 = (P["gold_dark"], P["gold_light"],
                                  P["gold_shine"])
                else:
                    c0, c1, c2 = (P["acid_dark"], P["acid_bright"],
                                  P["acid_glow"])
                NS._aacircle(surface, (*c2, 110), (bxp, byp), 7)
                NS._ellipse(surface, P["glass_dark"],
                            (bxp - 4, byp - 4, 8, 9))
                NS._ellipse(surface, c0, (bxp - 3, byp - 1, 6, 5))
                NS._ellipse(surface, c1, (bxp - 2, byp, 4, 3))
                NS._aacircle(surface, c2, (bxp - 2, byp - 2), 1)
                NS._poly(surface, P["leather_mid"], [
                    (bxp - 2, byp - 7), (bxp + 2, byp - 7),
                    (bxp + 2, byp - 4), (bxp - 2, byp - 4)])
            else:
                arm((gx - f * 3, gy - 3), (gx - f * 8, gy + 2), -2.0)
        return gun_hand, bottle_hand

    # ==================================================================
    # FULL COMPOSITE — buffer -> outline siluet -> lighting -> blit
    # (+ pose cache LRU supaya frame stabil 60 fps di mobile)
    # ==================================================================
    def _draw_alch_full_raw(surface, cx, cy, facing, phase, action,
                            attack_progress=0, rage=False,
                            detail=False, boss=None):
        """Rig masterwork v3 — ogre chemist + goblin rider, prosedural.

        Koordinat lokal: (0,0) = jangkar pinggul, +x maju (dikali
        facing), y ke bawah, tanah = +GROUND_DY (62).

        Tata letak vertikal (lokal):
            -79 ujung topi goblin   -62 kepala goblin
            -66 puncak tengkorak    -52 pusat kepala ogre
            -40 dada                  0 pinggul
            +18 pangkal paha        +39 lutut       +60 telapak

        Urutan lapisan: backpack -> goblin -> lengan belakang +
        cleaver belakang -> kaki -> cawat -> torso -> armor -> leher
        -> kepala -> lengan depan + cleaver utama -> highlight.
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

        # Sudut senjata di-author di ruang LOKAL (+x maju). Saat rig
        # di-mirror, sudut layar harus ikut dicerminkan terhadap sumbu
        # vertikal — rig lama lupa ini, jadi saat hadap kiri cleaver
        # menunjuk ke arah yang salah.
        S = (lambda a: a) if f > 0 else (lambda a: math.pi - a)

        pose = NS._attack_pose(ap) if attack else None
        flare = pose["flare"] if pose else 1.0

        # ═══ 2. BACKPACK (paling belakang, di punggung) ═══
        NS._draw_backpack(surface, *L(-25, -26), phase, f, rage)

        # ═══ 3. GOBLIN RIDER — duduk di bahu BELAKANG supaya tidak
        #        menutupi kepala ogre (siluet duo tetap terbaca) ═══
        aim_angle = None
        if action == "q_cast":
            if boss is not None:
                tx, ty = NS._target_position(boss, cx, cy)
                hx, hy = L(-23 + f * 8, -60 - 6)
                aim_angle = math.atan2(ty - hy, tx - hx)
            else:
                aim_angle = S(-0.1)
        goblin_x, goblin_y = L(-23, -60)
        NS._draw_goblin_rider(surface, goblin_x, goblin_y, f, phase,
                              action, ap, rage, aim_angle=aim_angle)

        # ═══ 4. LENGAN BELAKANG + CLEAVER BELAKANG ═══
        grip_b = NS._cleaver_grip_local(action, phase, ap, back=True)
        ang_b = NS._cleaver_angle_local(action, phase, ap, back=True)
        gb = L(*grip_b)
        shb = L(-19, -32)
        flex = 1.0 if action == "e_cast" else 0.0
        NS._draw_ogre_arm(surface, shb[0], shb[1], gb[0], gb[1], f,
                          back=True, flex=flex)
        NS._draw_cleaver(surface, gb[0], gb[1], S(ang_b), f, phase)

        # ═══ 5. KAKI — pangkal paha +18, telapak mendarat di tanah.
        #        Ayunan HORIZONTAL (sudut kecil), panjang tungkai
        #        vertikal, jadi kaki tidak pernah tertelan perut. ═══
        if action == "walk":
            la = math.sin(phase) * 0.42
            lift_a = max(0.0, math.sin(phase + 0.4)) * 6
            lift_b = max(0.0, math.sin(phase + math.pi + 0.4)) * 6
        else:
            la = 0.10
            lift_a = lift_b = 0.0
            if attack:
                la = 0.12 + pose["lunge"] * 0.010
        hA = L(-10, 18)          # kaki belakang
        hB = L(10, 18)           # kaki depan
        NS._draw_ogre_leg(surface, hA[0], hA[1], -la, lift_b, False, f)
        NS._draw_ogre_leg(surface, hB[0], hB[1], la, lift_a, True, f)

        # ═══ 6. CAWAT KULIT ROBEK (3 helai, inersia tertinggal).
        #        Dipendekkan dari rig lama (yang menutup seluruh kaki
        #        sampai lutut) menjadi cawat pinggul saja. ═══
        if action == "walk":
            lag = math.sin(phase + 2.1) * 3.0
        elif attack:
            lag = -pose["lean"] * 0.8
        else:
            lag = math.sin(phase * 0.55) * 1.4
        for i, off in enumerate((-12, -1, 10)):
            wave = lag + math.sin(phase * 1.0 + i) * 1.8
            length = 15 + (i % 2) * 4
            p0 = L(off - 5, 20)
            p1 = L(off + 5, 20)
            p2 = L(off + 4 + wave, 20 + length)
            p3 = L(off - 4 + wave, 20 + length)
            NS._poly(surface, P["shadow_deep"],
                     [(p0[0] + 1, p0[1] + 1), (p1[0] + 1, p1[1] + 1),
                      (p2[0] + 1, p2[1] + 1), (p3[0] + 1, p3[1] + 1)])
            NS._poly(surface, P["leather_darkest"], [p0, p1, p2, p3])
            NS._poly(surface, P["leather_dark"], [
                L(off - 4, 21), L(off + 4, 21),
                L(off + 3 + wave, 20 + length - 2),
                L(off - 3 + wave, 20 + length - 2)])
            NS._poly(surface, P["leather_mid"], [
                L(off - 3, 22), L(off + 1, 22),
                L(off + 1 + wave, 20 + length - 5),
                L(off - 2 + wave, 20 + length - 5)])
            # ujung robek + jahitan
            NS._aacircle(surface, P["leather_high"],
                         L(off, 23), 1)

        # ═══ 7. TORSO + ARMOR + LEHER + KEPALA ═══
        NS._draw_ogre_torso(surface, *L(0, -2), phase, flare, rage, f)
        NS._draw_ogre_armor(surface, *L(0, -2), phase, f, rage)
        NS._draw_belt(surface, *L(0, -2), phase, f, rage)
        # leher tebal berotot (trapezius menyatu ke rahang)
        nk0 = L(f * 2, -50)
        nk1 = L(f * 3, -38)
        NS._limb(surface, nk1, 7.5, nk0, 6.0,
                 P["ogre_darkest"], P["ogre_dark"], P["ogre_mid"])
        # otot trapezius: melebar dari leher ke KEDUA bahu, tetap di
        # atas garis dada supaya tidak menyilang pektoral
        for sgn in (-1, 1):
            NS._limb(surface, L(f * 3, -42), 3.5,
                     L(sgn * 13, -39), 5.0,
                     P["ogre_darkest"], P["ogre_dark"],
                     P["ogre_dark"] if sgn * f > 0 else P["ogre_mid"])
        hd = L(5, -60)
        if action == "attack":
            hd = (hd[0], hd[1] + int(pose["dip"] * 0.4))
        NS._draw_ogre_head(surface, hd[0], hd[1], f, phase, action,
                           rage)

        # ═══ 8. LENGAN + SENJATA GOBLIN (di atas kepala ogre) ═══
        NS._draw_goblin_arms(surface, goblin_x, goblin_y, f, phase,
                             action, ap, rage, aim_angle=aim_angle)

        # ═══ 9. LENGAN DEPAN + CLEAVER UTAMA (paling depan) ═══
        grip_f = NS._cleaver_grip_local(action, phase, ap, back=False)
        ang_f = NS._cleaver_angle_local(action, phase, ap, back=False)
        gf = L(*grip_f)
        shf = L(19, -32)
        NS._draw_ogre_arm(surface, shf[0], shf[1], gf[0], gf[1], f,
                          back=False, flex=flex)
        NS._draw_pauldron(surface, *L(0, -2), phase, f, rage)
        NS._draw_cleaver(surface, gf[0], gf[1], S(ang_f), f, phase,
                         glow=0.7 if rage else 0.0)

        # ═══ 10. HIGHLIGHTS / detail portrait ═══
        if rage:
            pul = 0.5 + 0.5 * math.sin(phase * 7.0)
            NS._aacircle(surface, (*P["acid_hot"],
                                   int(90 + 90 * pul)),
                         (gf[0], gf[1]), 5)
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
        # Kilau greed aura — CINCIN, bukan cakram penuh.
        # Versi lama menumpuk lingkaran PADAT beradius 44..18 px tepat di
        # (x, y-8): piringan emas itu menutupi badan Alchemist selama
        # Greevil's Greed di-cast. Sekarang digambar sebagai cincin tipis
        # (thickness 2) sehingga aura tetap terbaca tapi siluetnya utuh.
        pul = 0.5 + 0.5 * math.sin(phase * 2.2)
        for radius in range(44, 18, -5):
            alpha = int((44 - radius) * 4 * pul)
            if alpha > 0:
                pygame.draw.circle(surface,
                                   (*P["gold_darkest"], min(200, alpha)),
                                   (int(x), int(y - 8)), int(radius), 2)

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
