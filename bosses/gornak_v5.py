"""
bosses/gornak_v5.py — GORNAK "SPELLBREAKER" — TOTAL REWRITE v5
===============================================================

Gornak: orc anti-mage, mini boss level 1 DAN kartu hero. Modul ini adalah
rewrite PENUH dari nol (bukan patch v4): renderer prosedural modular,
controller animasi delta-time, pose state-machine, telegraph world-space,
dan lapisan FEEL (hit flash, status overlay, spawn / death / victory
visual). 100% prosedural — tidak ada PNG / sprite sheet / image.load;
semua piksel lahir dari pygame.draw + Surface + transform.

Empat pilar (arsitektur master-prompt)
--------------------------------------
  CHARACTER   state + movement + combat + animation  -> controller
              ``_update_gnk_attack_anim`` / ``_resolve_anim_state`` /
              ``_resolve_pose`` (delta-time, fase bernama, jendela hit).
  RENDERER    body / armor / weapon / equipment / shadow / lighting ->
              ``_draw_gnk_rig`` dan fungsi modular ``render_*`` di bawah.
  FX          partikel, skill, impact, trail, proyektil ->
              heroes/gornak_fx.py (lapisan hidup 1:1 di luar sprite cache).
  FEEL        hit-stop, shake, recoil, damage numbers ->
              heroes/combat_feel.py (bus SHARED) + notify_* di gornak_fx.

Kontrak yang DIKUNCI regression tests (tools/test_gornak_masterwork.py,
tools/test_gornak_v3_combat.py, tools/test_hero_*):
  * ``draw_gornak(surface, boss, x, y)`` satu-satunya entry point.
  * ``SCALE=1.32  LIFT=4  FEET_DY=44  GROUND_DY=54`` — telapak dipatok,
    ukuran = keluarga (morgath/abaddon boss; morgath/kaizen/vex hero).
  * ``SKILL_DUR = {q:40, w:25, e:60, r:90}`` sinkron base_boss.py dan
    hero_skills/_bundle.py.
  * ``_update_gnk_attack_anim`` + seluruh state ``_gnk_*``; fase
    ANTICIPATION/WINDUP/SWING/IMPACT/FOLLOW/RECOVERY; jendela hit
    ``ATTACK_ACTIVE_WINDOW``; kurva ``_attack_curve`` dengan TAHAN di
    ujung wind-up dan HOLD di impact.
  * ``_attack_curve(0.30)==_SWING_WIND``, ``_attack_curve(0.46)==
    _SWING_HIT-0.02`` — nama fase, pose grip, dan sudut bilah jatuh di
    patahan yang SAMA, jadi tidak pernah ada satu frame yang berbeda.
  * FX E/R = 100/180 px DUNIA di CASTER (``_ring_r`` + ``_fx_scale``,
    kompensasi 1/_render_scale); Q proc lahir dari UJUNG CLEAVER.
  * ``_resolve_pose`` / ``_tip_local`` / ``_tip_screen`` /
    ``_front_grip_local`` / ``_back_grip_local`` / ``_rig_shift`` /
    ``_local_to_screen`` = jembatan lapisan hidup (heroes/gornak_fx).
  * Semua nama bagian v4 (``_draw_gnk_legs/_torso/_kilt/_pauldrons/
    _head/_arm/_cleaver/_dagger/_rimlight/_details``) tetap ada —
    GEOMETRINYA yang ditulis ulang total, bukan namanya.

v5 vs v4 — yang berubah (visual redesign, bukan tambalan)
---------------------------------------------------------
  1. Siluet lebih KEJAM: pauldron bertumpuk tiga pelat dengan paku,
     pelat dada segmented (bukan satu trapesium), kilt asimetris dengan
     sapuan kain, boots baja ber-toe-cap, scarf robek yang bergerak
     dengan inersia — semua tetap "1 bidang = maks 3 nilai" supaya di
     57-110 px tidak jadi noise.
  2. Wajah punya EKSPRESI: alis menukik, taring bawah, mata
     (255,242,255) sebagai nilai tertinggi sprite; kedip deterministik
     dari phase (cache-safe).
  3. Lapisan baru sesuai master prompt: ``render_status_overlay``
     (burn / slow / stun), ``render_death`` (collapse + rune-dissolve),
     ``render_spawn`` (bangkit dari cincin void), ``render_highlight``
     (weapon shine + gem flare) — semuanya deterministik terhadap
     (phase, action, ap) supaya sprite cache lane hero tetap benar.
  4. Gerak tempur: anticipation dengan counter-motion pinggang, chop
     overhead BUSUR (bukan lerp), impact hold 2-3 frame, follow-through
     ke garda rendah; kaki belakang menendang tanah saat tebas.
"""

import math

import pygame

try:                     # pass cahaya bersama; opsional supaya file ini
    import lighting as _lighting          # tetap bisa dimuat sendiri
except Exception:        # pragma: no cover
    _lighting = None


class _NS_gornak:
    """Namespace gornak — Anti-Mage mini boss, PROCEDURAL RIG v5.

    Renderer modular: setiap bagian bisa diedit tanpa menyentuh yang
    lain (lihat ``render_*``). Satu sumber pose (``_resolve_pose``)
    dipakai badan DAN semua efek hidup, jadi bilah, trail, bolt, dan
    telegraph tidak pernah berbeda frame.
    """

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    _STATIC_SURFACES = {}

    # ── SKALA BADAN ───────────────────────────────────────────────
    # Rujukan keluarga (render padat, alpha>=100):
    #   morgath 116x112 · abaddon 150x150 · hero final ~72-82 px.
    SCALE = 1.32
    LIFT = 4
    # Telapak dipatok di FEET_DY ruang LOKAL; garis tanah dunia turunan
    # langsung dari sini supaya shadow, rune, dan sol tidak lepas.
    FEET_DY = 44
    GROUND_DY = int(round(FEET_DY * SCALE)) - LIFT        # = 54

    # Buffer rig = extents TERUKUR semua pose (idle/walk/attack/surge/
    # ward/void/blink/victory + LIFT + lean + margin). Outline menyalin
    # buffer ini 4x per frame — jangan ada ruang kosong.
    RIG_W, RIG_H = 196, 164
    RIG_OX, RIG_OY = 94, 100

    # Kotak acuan pass cahaya — TETAP (bukan bbox per frame) supaya arah
    # cahaya tidak berubah saat ganti pose (terbaca sebagai lampu berkedip).
    GRAD_BOX = (RIG_OX - 54, RIG_OY - 52, 126, 102)

    #: Durasi pose per skill (frame simulasi) — HARUS sama dengan
    #: active_skill_timer yang diisi AI boss & skill hero.
    SKILL_DUR = {"q": 40, "w": 25, "e": 60, "r": 90}

    #: Radius TELEGRAPH dunia per skill (px). E/R = radius gameplay
    #: sebenarnya; Q/W memakai proc/telegraph kecil milik badan.
    SKILL_RADIUS = {"q": 44.0, "w": 30.0, "e": 100.0, "r": 180.0}

    # Penanda "sedang dirender ke canvas lane hero" (pipeline men-set
    # _render_scale; flag mencegah pass cahaya dobel dengan
    # heroes._finish_hd_sprite).
    class _HERO_LANE:
        v = False

    # ==================================================================
    # PALETTE — 9 kunci kontrak (via sinkronisasi gornak_fx) + ramp
    # per material. Nilai magic_*/blade_light/blade_dark/blade_mid/
    # blade_shine/armor_darkest DIKUNCI (dipakai sync heroes/gornak_fx
    # dan default "outline"-nya); jangan melenceng.
    # ==================================================================
    PALETTE = {
        # ── kulit ork hijau zaitun (identitas anti-mage) ────────────
        "skin_darkest": (16, 26, 14),
        "skin_dark":    (44, 66, 32),
        "skin_mid":     (88, 120, 58),
        "skin_light":   (134, 166, 90),
        "skin_shine":   (184, 206, 130),
        "skin_high":    (224, 238, 178),

        # ── topknot hitam-ungu ──────────────────────────────────────
        "hair_darkest": (10, 8, 16),
        "hair_dark":    (28, 22, 40),
        "hair_mid":     (58, 46, 82),
        "hair_light":   (104, 84, 138),
        "hair_shine":   (160, 132, 196),

        # ── kilt perang / kain ungu dalam ───────────────────────────
        "robe_darkest": (14, 7, 26),
        "robe_dark":    (34, 17, 60),
        "robe_mid":     (64, 33, 104),
        "robe_light":   (106, 62, 152),
        "robe_edge":    (156, 108, 200),

        # ── baja biru-gelap "spellbreaker" ──────────────────────────
        # armor_darkest DIKUNCI (7,6,12): dipakai gornak_fx sbg default
        # "outline". Jangan berubah.
        "armor_darkest": (7, 6, 12),
        "armor_dark":    (30, 33, 48),
        "armor_mid":     (78, 84, 108),
        "armor_light":   (138, 146, 176),
        "armor_shine":   (204, 210, 236),

        # ── bilah silver-biru (DIKUNCI: gornak_fx men-sync) ────────
        # Hierarki nilai: MATA > PERMATA > edge-bilah > pelat > bilah.
        "blade_darkest": (18, 18, 30),
        "blade_dark":    (36, 34, 52),
        "blade_mid":     (96, 100, 128),
        "blade_light":   (164, 170, 196),
        "blade_shine":   (212, 218, 242),
        "blade_hamon":   (168, 196, 236),
        "blade_edge":    (188, 204, 236),

        # ── kulit tan / kuningan / taring tulang ─────────────────────
        "leather_dark":  (40, 26, 16),
        "leather_mid":   (82, 54, 32),
        "leather_light": (128, 90, 54),
        "brass_dark":    (94, 66, 23),
        "brass_mid":     (172, 132, 51),
        "brass_light":   (230, 202, 116),
        "bone_dark":     (150, 138, 108),
        "bone_light":    (226, 216, 186),

        # ── permata mana (pelat dada) — membesar saat Ward/Void ─────
        "gem_dark":      (26, 8, 48),
        "gem_mid":       (150, 70, 220),
        "gem_hot":       (235, 190, 255),

        # ── aura anti-sihir (DIKUNCI: gornak_fx men-sync) ──────────
        "magic_void":    (36, 7, 70),
        "magic_darkest": (24, 5, 44),
        "magic_dark":    (58, 19, 108),
        "magic_mid":     (130, 55, 200),
        "magic_light":   (186, 111, 241),
        "magic_hot":     (221, 161, 255),
        "magic_shine":   (245, 210, 255),
        "magic_core":    (255, 236, 255),

        # ── mata menyala (nilai TERTINGGI di sprite) ────────────────
        "eye_dark":  (36, 12, 60),
        "eye_mid":   (176, 92, 236),
        "eye_light": (240, 190, 255),
        "eye_glow":  (255, 242, 255),

        "shadow":      (0, 0, 0),
        "shadow_deep": (4, 2, 8),
        "white":       (255, 255, 255),
    }

    #: Ramp 5 band per material: (darkest, dark, body, light, shine).
    #: SATU tabel supaya setiap bidang memakai tangga nilai yang sama.
    _RAMP = {
        "skin":   ("skin_darkest", "skin_dark", "skin_mid",
                   "skin_light", "skin_shine"),
        "armor":  ("armor_darkest", "armor_dark", "armor_mid",
                   "armor_light", "armor_shine"),
        "robe":   ("robe_darkest", "robe_dark", "robe_mid",
                   "robe_light", "robe_edge"),
        "leather": ("shadow_deep", "leather_dark", "leather_mid",
                    "leather_light", "brass_light"),
        "blade":  ("blade_darkest", "blade_dark", "blade_mid",
                   "blade_light", "blade_shine"),
        "hair":   ("hair_darkest", "hair_dark", "hair_mid",
                   "hair_light", "hair_shine"),
        "magic":  ("magic_darkest", "magic_dark", "magic_mid",
                   "magic_light", "magic_hot"),
        "brass":  ("shadow_deep", "brass_dark", "brass_mid",
                   "brass_light", "white"),
        "gem":    ("gem_dark", "magic_dark", "gem_mid", "gem_hot",
                   "magic_core"),
    }

    @staticmethod
    def _band(ramp, i):
        """Warna band ke-i (0=tergelap .. 4=terang) dari ramp bernama."""
        keys = _NS_gornak._RAMP[ramp]
        return _NS_gornak.PALETTE[keys[max(0, min(4, int(i)))]]

    # ==================================================================
    # PRIMITIF — menggambar bentuk ber-alpha lewat surface sementara.
    # Tanpa primitif ini, pygame.draw ellipse/circle tidak bisa transparan
    # di atas surface SRCALPHA (blit REPLACE akan menghapus latar).
    # ==================================================================
    @staticmethod
    def _clamp(color):
        # Alpha (kanal ke-4) DIPERTAHANKAN: cabang alpha-aware di
        # _aacircle/_aaline/_poly/_ellipse/_rect memeriksa len==4.
        vals = [max(0, min(255, int(c))) for c in color[:4]]
        if len(vals) == 4:
            return tuple(vals)
        return tuple(max(0, min(255, int(c))) for c in color[:3])

    @staticmethod
    def _alpha(v):
        return max(0, min(255, int(v)))

    @staticmethod
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_gornak._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius <= 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4),
                                  pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2),
                               radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_gornak.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius,
                                     width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)

    @staticmethod
    def _aaline(surface, color, start, end, width=1):
        color = _NS_gornak._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        width = max(1, int(width))
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width - 2
            min_y = min(sy, ey) - width - 2
            w = abs(ex - sx) + width * 4 + 6
            h = abs(ey - sy) + width * 4 + 6
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color, (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), width)
            surface.blit(temp, (min_x, min_y))
            return
        if _NS_gornak.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color[:3], (sx, sy), (ex, ey))
                return
            except Exception:
                pass
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), width)

    @staticmethod
    def _poly(surface, color, points):
        if not points or len(points) < 3:
            return
        color = _NS_gornak._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.polygon(temp, color,
                                [(p[0] - min_x, p[1] - min_y)
                                 for p in points])
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)

    @staticmethod
    def _ellipse(surface, color, rect, width=0):
        color = _NS_gornak._clamp(color)
        rx, ry, rw, rh = (int(rect[0]), int(rect[1]),
                          int(rect[2]), int(rect[3]))
        if rw <= 0 or rh <= 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], (rx, ry, rw, rh), width)

    @staticmethod
    def _rect(surface, color, rect):
        color = _NS_gornak._clamp(color)
        rx, ry, rw, rh = (int(rect[0]), int(rect[1]),
                          int(rect[2]), int(rect[3]))
        if rw <= 0 or rh <= 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh))
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], (rx, ry, rw, rh))

    @staticmethod
    def _mix(a, b, t):
        """Blend linear dua warna palette (t=0 -> a, t=1 -> b)."""
        t = max(0.0, min(1.0, t))
        return _NS_gornak._clamp(
            (a[0] + (b[0] - a[0]) * t,
             a[1] + (b[1] - a[1]) * t,
             a[2] + (b[2] - a[2]) * t))

    @staticmethod
    def _hash01(i):
        """Pseudo-random deterministik 0..1 — stabil antar frame & cache.

        Semua 'kekacauan' pixel-art (grain, jitter segel, serpihan)
        harus deterministik atau sprite cache lane hero akan berkedip.
        """
        x = math.sin(i * 127.1 + 311.7) * 43758.5453
        return x - math.floor(x)

    @staticmethod
    def _static(key, builder):
        """Cache surface statis (shadow, aura, pelat segel)."""
        surf = _NS_gornak._STATIC_SURFACES.get(key)
        if surf is None:
            surf = builder()
            _NS_gornak._STATIC_SURFACES[key] = surf
        return surf

    # ==================================================================
    # FX WORLD-SPACE — hero dirender ke canvas lalu dikecilkan
    # _render_scale; efek yang diukur dalam PIKSEL DUNIA (telegraph E/R)
    # harus dikompensasi 1/_render_scale supaya DI LAYAR persis seukuran
    # radius gameplay. Boss asli (tanpa _render_scale) = 1.0.
    # ==================================================================
    @staticmethod
    def _fx_scale(boss):
        scale = getattr(boss, "_render_scale", None)
        if not scale:
            return 1.0
        return max(1.0, min(2.6, 1.0 / float(scale)))

    @staticmethod
    def _ring_r(boss, world_r):
        """Radius canvas untuk ``world_r`` piksel dunia."""
        return max(1, int(round(float(world_r) * _NS_gornak._fx_scale(boss))))

    @staticmethod
    def _world_to_local(boss, x, y, wx, wy):
        """Titik dunia -> ruang gambar renderer (clamp ke canvas hero)."""
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

    @staticmethod
    def _clamp_fx_xy(boss, x, y, px, py):
        """Jaga FX tetap di dalam canvas hero (rumus = _canvas_size_for)."""
        scale = getattr(boss, "_render_scale", None)
        if scale is None:
            return int(px), int(py)
        scale = float(scale) or 1.0
        rng = int(getattr(boss, "range", 130) or 130)
        half = max(120, int(rng / scale) + 40)
        max_off = half - 12
        ox, oy = px - x, py - y
        d = math.hypot(ox, oy)
        if d > max_off:
            ox *= max_off / d
            oy *= max_off / d
        return int(x + ox), int(y + oy)

    @staticmethod
    def _target_position(boss, x, y):
        """Posisi target dalam ruang jangkar (x, y) renderer ini."""
        target = getattr(boss, "target", None)
        scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
        if target is not None and getattr(target, "alive", True):
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return (int(x + 120.0 / scale * getattr(boss, "direction", 1)),
                int(y))

    @staticmethod
    def _skill_progress(boss, skill):
        """0..1 sepanjang durasi skill (timer engine turun -> naik)."""
        dur = float(_NS_gornak.SKILL_DUR.get(skill, 40) or 40)
        timer = int(getattr(boss, "active_skill_timer", 0) or 0)
        return max(0.0, min(1.0, 1.0 - timer / dur))

    # ==================================================================
    # BRUSH KIT — bahasa bentuk Gornak. Semua deterministik terhadap
    # (phase/progress/seed) supaya cache sprite tidak pernah berkedip.
    # ==================================================================
    @staticmethod
    def _spark_star(surface, cx, cy, size, color, alpha, spikes=6, rot=0.4,
                    core=None):
        """Bintang kilat: spike panjang-pendek selang-seling + inti."""
        if alpha <= 0 or size <= 0:
            return
        for k in range(spikes):
            ang = rot + k * math.tau / spikes
            ln = size * (1.0 if k % 2 == 0 else 0.55)
            _NS_gornak._aaline(
                surface, (*color, alpha), (int(cx), int(cy)),
                (int(cx + math.cos(ang) * ln),
                 int(cy + math.sin(ang) * ln * 0.8)),
                2 if k % 2 == 0 else 1)
        if core:
            _NS_gornak._aacircle(surface, (*core, alpha), (int(cx), int(cy)),
                                 max(1, int(size * 0.3)))

    @staticmethod
    def _chevron(surface, cx, cy, ang, size, color, alpha, width=3):
        """Satu panah '>' menghadap arah ``ang`` (telegraph bergerak)."""
        if alpha <= 0 or size <= 0:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        tipx, tipy = cx + ca * size, cy + sa * size
        for s in (-1, 1):
            _NS_gornak._aaline(
                surface, (*color, alpha),
                (int(cx + px * s * size * 0.55 - ca * size * 0.5),
                 int(cy + py * s * size * 0.55 - sa * size * 0.5)),
                (int(tipx), int(tipy)), width)

    @staticmethod
    def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                     segments=10, thick=3, span=0.6, squash=0.92):
        """Cincin putus-putus berputar (marker AOE / ring rune)."""
        if alpha <= 0 or radius <= 1:
            return
        for i in range(segments):
            a0 = phase + i * math.tau / segments
            a1 = a0 + math.tau / segments * span
            _NS_gornak._aaline(
                surface, (*color, alpha),
                (cx + math.cos(a0) * radius,
                 cy + math.sin(a0) * radius * squash),
                (cx + math.cos(a1) * radius,
                 cy + math.sin(a1) * radius * squash), thick)

    #: segmen rim segel arcane + cache pelatnya (di-bake per radius/scale)
    _SEAL_N = 30
    _SEAL_CACHE = {}

    @staticmethod
    def _seal_plate(radius, fs, nodes, star, teeth, alpha):
        """Bagian STATIS segel (rim bergerigi + bintang + simpul kristal).

        Di-bake sekali per (radius, fs, nodes, star, teeth, alpha bucket):
        40 garis aaline per frame itu mahal; yang bergerak nanti cuma
        sapuan cahaya + orbit rune. Rim digambar pada radius PERSIS
        ``radius`` (jitter 1 px) karena tools/test_gornak_masterwork.py
        men-sampling lingkaran di radius dunia untuk mengunci telegraph.
        """
        key = (radius, round(fs, 2), nodes, star, teeth, alpha // 8)
        surf = _NS_gornak._SEAL_CACHE.get(key)
        if surf is not None:
            return surf
        p = _NS_gornak.PALETTE
        size = radius * 2 + 10
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        # rim ganda: garis luar presisi + dalam yang lebih redup
        _NS_gornak._ellipse(surf, (*p["magic_mid"], alpha),
                             (c - radius, c - radius, radius * 2,
                              radius * 2), max(2, int(3 * fs)))
        _NS_gornak._ellipse(surf, (*p["magic_dark"], int(alpha * 0.55)),
                            (c - radius + 2, c - radius + 2,
                             (radius - 2) * 2, (radius - 2) * 2),
                            max(1, int(2 * fs)))
        # gigi radial di sepanjang rim
        for i in range(teeth):
            a = i * math.tau / teeth
            r0 = radius - int(4 * fs)
            r1 = radius + int(5 * fs)
            _NS_gornak._aaline(
                surf, (*p["magic_light"], int(alpha * 0.9)),
                (c + math.cos(a) * r0, c + math.sin(a) * r0),
                (c + math.cos(a) * r1, c + math.sin(a) * r1),
                max(1, int(2 * fs)))
        # poligon bintang dalam (star points, lompat 2)
        if star >= 3:
            pts = []
            for i in range(star):
                a = i * math.tau / star
                pts.append((c + math.cos(a) * radius * 0.62,
                            c + math.sin(a) * radius * 0.62))
            order = [pts[(i * 2) % star] for i in range(star + 1)]
            for i in range(len(order) - 1):
                _NS_gornak._aaline(
                    surf, (*p["magic_dark"], int(alpha * 0.75)),
                    order[i], order[i + 1], max(1, int(fs + 1)))
        # simpul kristal pada rim (serpihan, bukan titik bulat)
        for i in range(nodes):
            a = i * math.tau / nodes
            rr = radius + (_NS_gornak._hash01(i * 3 + 1) - 0.5) * 1.6
            _NS_gornak._shard(surf, c + math.cos(a) * rr,
                              c + math.sin(a) * rr, a + math.pi / 2,
                              max(3, int(6 * fs)), max(1, int(3 * fs)),
                              p["magic_hot"], int(alpha * 0.95),
                              core=p["magic_shine"])
        _NS_gornak._SEAL_CACHE[key] = surf
        if len(_NS_gornak._SEAL_CACHE) > 64:            # batasi memori
            _NS_gornak._SEAL_CACHE.pop(
                next(iter(_NS_gornak._SEAL_CACHE)))
        return surf

    @staticmethod
    def _arcane_seal(surface, cx, cy, radius, phase, alpha, fs=1.0,
                     nodes=8, star=4, spin=1.0, sweep=True):
        """Segel anti-mana: pelat statis + sapuan cahaya berputar.

        Rim pada radius PERSIS ``radius`` — sampling test AOE mengunci
        angka ini; jangan dikurangi untuk estetika.
        """
        if alpha <= 0 or radius < 4:
            return
        p = _NS_gornak.PALETTE
        plate = _NS_gornak._seal_plate(int(radius), fs, nodes, star,
                                       max(8, int(radius / 12)), alpha)
        surface.blit(plate, (int(cx) - plate.get_width() // 2,
                             int(cy) - plate.get_height() // 2))
        if not sweep or alpha <= 40:
            return
        # sapuan: 3 busur pendek yang berputar + jitter rim 1 px
        for k in range(3):
            f0 = (phase * 0.7 * spin + k / 3.0) % 1.0
            a0 = f0 * math.tau
            a1 = a0 + 0.55
            col = p["magic_shine"] if k == 0 else p["magic_hot"]
            a = _NS_gornak._alpha(alpha * (0.4 + 0.6 * (1 - abs(k - 0.6))))
            n = 6
            for j in range(n):
                ang = a0 + (a1 - a0) * j / float(n)
                ang2 = a0 + (a1 - a0) * (j + 1) / float(n)
                rr = radius + (_NS_gornak._hash01((k * 7 + j) % 30) - 0.5) \
                    * 1.4
                _NS_gornak._aaline(
                    surface, (*col, a),
                    (cx + math.cos(ang) * rr, cy + math.sin(ang) * rr),
                    (cx + math.cos(ang2) * rr, cy + math.sin(ang2) * rr),
                    max(2, int(3 * fs)))

    @staticmethod
    def _rune_orbit(surface, cx, cy, radius, phase, alpha, fs=1.0,
                    count=8):
        """Serpihan rune mengorbit cincin (berkebalikan arah dari segel)."""
        if alpha <= 0 or radius <= 2:
            return
        p = _NS_gornak.PALETTE
        for i in range(count):
            ang = phase * 1.1 + i * math.tau / count
            d = radius * (1.0 + (_NS_gornak._hash01(i * 5 + 2) - 0.5) * 0.08)
            _NS_gornak._shard(
                surface, cx + math.cos(ang) * d, cy + math.sin(ang) * d,
                ang + math.pi / 2 + _NS_gornak._hash01(i) * 0.6,
                max(3, int(5 * fs)), max(1, int(2 * fs)),
                p["magic_light"], _NS_gornak._alpha(
                    alpha * (0.5 + 0.5 * _NS_gornak._hash01(i * 11))),
                core=p["magic_shine"])

    @staticmethod
    def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                      width=2, segs=3):
        """Retak zigzag dari pusat (tanah pecah / realitas sobek)."""
        if alpha <= 0 or length <= 2:
            return
        px, py = cx, cy
        a = ang
        for i in range(segs):
            a += (_NS_gornak._hash01(seed * 7 + i * 13) - 0.5) * 0.9
            nx = px + math.cos(a) * (length / segs)
            ny = py + math.sin(a) * (length / segs)
            col = colors[min(len(colors) - 1, i)]
            _NS_gornak._aaline(surface, (*col, _NS_gornak._alpha(
                alpha * (1.0 - 0.22 * i))), (int(px), int(py)),
                (int(nx), int(ny)), max(1, width - (i > 1)))
            px, py = nx, ny

    @staticmethod
    def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
        """Deret runcing sepanjang tulang punggung (bulu/gerigi/syal)."""
        pts = []
        n = max(2, len(spine) - 1)
        for i in range(n):
            x0, y0 = spine[i]
            x1, y1 = spine[min(i + 1, len(spine) - 1)]
            dx, dy = x1 - x0, y1 - y0
            ln = math.hypot(dx, dy)
            if ln < 0.01:
                continue
            nx, ny = -dy / ln, dx / ln
            f = _NS_gornak._hash01(seed * 31 + i)
            d = depth * (0.62 + 0.55 * f)
            if ln < min_len * 0.5:
                d *= 0.45
            mx, my = (x0 + x1) * 0.5, (y0 + y1) * 0.5
            pts.append((x0, y0))
            pts.append((mx + nx * d, my + ny * d))
        pts.append(spine[-1])
        return pts

    @staticmethod
    def _dither_dots(surface, color, points, alpha=70):
        """Dots 1-px longgar — tekstur; HANYA dipakai mode portrait."""
        col = (*_NS_gornak._clamp(color)[:3], _NS_gornak._alpha(alpha))
        for px, py in points:
            surface.set_at((int(px), int(py)), col)

    @staticmethod
    def _shard(surface, cx, cy, ang, length, width, color, alpha,
               core=None):
        """Serpihan kristal mana: belah ketupat runcing searah ``ang``.

        Bentuk yang sama dipakai proyektil, impact, debris, dan orbit —
        satu bahasa visual supaya Gornak terbaca konsisten.
        """
        if alpha <= 0 or length <= 1:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        nx, ny = -sa, ca
        pts = [(cx + ca * length, cy + sa * length),
               (cx + nx * width, cy + ny * width),
               (cx - ca * length * 0.45, cy - sa * length * 0.45),
               (cx - nx * width, cy - ny * width)]
        _NS_gornak._poly(surface, (*color, _NS_gornak._alpha(alpha)),
                         [(int(px), int(py)) for px, py in pts])
        if core:
            _NS_gornak._aaline(
                surface, (*core, _NS_gornak._alpha(alpha)),
                (int(cx - ca * length * 0.3), int(cy - sa * length * 0.3)),
                (int(cx + ca * length * 0.8), int(cy + sa * length * 0.8)),
                1)

    @staticmethod
    def _ribbon(surface, path, widths, color, alpha):
        """Pita tebasan: strip tebal-tipis dari daftar titik.

        Polygon [left.. + right..terbalik]; dipakai fallback canvas untuk
        sapuan bilah. Trail 60fps yang SUNGGUH hidup milik
        heroes/gornak_fx (histori posisi bilah per frame).
        """
        if len(path) < 3 or alpha <= 0:
            return
        left, right = [], []
        for i, (px, py) in enumerate(path):
            if i == 0:
                dx, dy = path[1][0] - px, path[1][1] - py
            elif i == len(path) - 1:
                dx, dy = px - path[-2][0], py - path[-2][1]
            else:
                dx = path[i + 1][0] - path[i - 1][0]
                dy = path[i + 1][1] - path[i - 1][1]
            ln = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / ln, dx / ln
            w = widths[i]
            left.append((px + nx * w, py + ny * w))
            right.append((px - nx * w, py - ny * w))
        _NS_gornak._poly(surface, (*color, _NS_gornak._alpha(alpha)),
                         [(int(a), int(b)) for a, b in left + right[::-1]])

    # ==================================================================
    # CONTROLLER ANIMASI — SATU sumber kebenaran state karakter.
    #
    # Delta-time nyata + timeline berbasis timer engine yang IDEMPOTEN
    # (dipanggil berkali-kali dalam satu frame tidak mempercepat apa
    # pun). Fase bernama, jendela hit eksplisit, prioritas state, dan
    # timer spawn/death untuk visual layer v5.
    # ==================================================================
    # Batas fase = fraksi 0..1 DURASI SERANGAN (bukan waktu pose yang
    # sudah dilengkungkan kurva). Batas jatuh PERSIS di patahan
    # _attack_curve, jadi tabel grip / sudut bilah / nama fase tidak
    # pernah berbeda satu frame.
    ATTACK_ANTICIPATION_END = 0.16
    ATTACK_WINDUP_END = 0.30            # bilah di atas kepala + TAHAN
    ATTACK_SWING_END = 0.46             # tebasan turun (paling cepat)
    ATTACK_IMPACT_END = 0.60            # HOLD impact -> freeze 2-3 frame
    ATTACK_FOLLOW_END = 0.80            # follow-through -> garda
    #: jendela bilah secara geometris menyapu depan badan
    ATTACK_ACTIVE_WINDOW = (0.36, 0.62)
    #: puncak benturan (FX memicu spark "di udara" di sini)
    ATTACK_IMPACT_FRAME = 0.53

    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, 0.16),
        ("WINDUP",       0.16, 0.30),
        ("SWING",        0.30, 0.46),
        ("IMPACT",       0.46, 0.60),
        ("FOLLOW",       0.60, 0.80),
        ("RECOVERY",     0.80, 1.00),
    )

    #: Prioritas state — angka besar menang; DEATH mengunci.
    ANIM_STATES = {
        "IDLE": 0,
        "WALK": 10,
        "RUN": 15,
        "VICTORY": 20,
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

    #: Debug visual arena: hitbox, hurtbox, jangkauan, state, frame, FPS,
    #: partikel, timer skill. (Lane hero punya overlay yang sama di
    #: heroes/gornak_fx.DEBUG_CHARACTER.)
    DEBUG_CHARACTER = False

    @staticmethod
    def attack_phases_order():
        """Urutan nama fase (dipakai test & alat audit)."""
        return tuple(name for name, _a, _b in _NS_gornak.ATTACK_PHASES)

    @staticmethod
    def attack_phase(progress):
        """Nama fase serangan untuk progress 0..1 (NONE di luar serangan)."""
        if progress is None:
            return "NONE"
        p = max(0.0, min(1.0, float(progress)))
        for name, a, b in _NS_gornak.ATTACK_PHASES:
            if a <= p < b:
                return name
        return "RECOVERY"

    @staticmethod
    def _resolve_anim_state(boss, attacking, phase):
        """State animasi yang DIINGINKAN frame ini (prioritas keras)."""
        if not getattr(boss, "alive", True):
            return "DEATH"
        if int(getattr(boss, "_gnk_hurt_frames", 0)) > 0:
            return "HURT"
        if getattr(boss, "_gnk_victory", False):
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

    @staticmethod
    def _swing_hitbox(boss, cx, cy):
        """Rect hitbox ayunan (ruang permukaan) HANYA saat jendela hit.

        Dipakai overlay debug + alat audit; None di luar jendela supaya
        tidak pernah terlihat seperti "pedang menembus tembok".
        """
        if not getattr(boss, "_gnk_hit_active", False):
            return None
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        scale = _NS_gornak._fx_scale(boss)
        reach = int(58 * scale)
        top = int(cy - 34 * scale)
        h = int(64 * scale)
        left = int(cx) if f > 0 else int(cx) - reach
        return pygame.Rect(left, top, max(8, reach), max(10, h))

    #: spawn-in (bangkit dari lingkaran void) & death-out (collapse +
    #: rune-dissolve) dalam DETIK — dibaca render_spawn / render_death.
    SPAWN_TIME = 0.85
    DEATH_TIME = 1.35

    @staticmethod
    def _update_gnk_attack_anim(boss):
        """Controller animasi Gornak — state, fase, timing, delta-time.

        * ``_gnk_dt`` / ``_gnk_frame_duration``  delta-time nyata (dijepit)
        * ``_gnk_attack_active`` / ``_gnk_attack_frame`` /
          ``_gnk_attack_progress`` / ``_gnk_attack_raw``  — kontrak lama
        * ``_gnk_attack_phase``   ANTICIPATION..RECOVERY / NONE
        * ``_gnk_hit_active``     True hanya di jendela hit
        * ``_gnk_state`` / ``_gnk_state_prev`` / ``_gnk_state_time``
        * ``_gnk_hurt_frames``    respons kena damage (dari flash boss)
        * ``_gnk_spawn_t``        timer spawn-in (hit mundur sekali)
        * ``_gnk_death_t``        timer death-out (hit maju saat mati)
        * ``_gnk_victory``        flag victory-pose (diisi game/tools)
        """
        NS = _NS_gornak

        # ── delta time NYATA (bukan frame-count) ────────────────────
        try:
            now = pygame.time.get_ticks()
        except Exception:                          # pragma: no cover
            now = 0
        prev_ms = getattr(boss, "_gnk_last_ms", None)
        if prev_ms is None:
            dt = 1.0 / 60.0
        else:
            dt = (now - prev_ms) / 1000.0
            if dt <= 0.0 or dt > 0.05:
                dt = 1.0 / 60.0
        boss._gnk_last_ms = now
        boss._gnk_dt = dt
        boss._gnk_frame_duration = dt

        # ── spawn / death (visual v5; deterministik, cache-safe) ────
        spawn = getattr(boss, "_gnk_spawn_t", None)
        if spawn is None:
            boss._gnk_spawn_t = NS.SPAWN_TIME
        elif spawn > 0.0:
            boss._gnk_spawn_t = max(0.0, spawn - dt)
        if not getattr(boss, "alive", True):
            boss._gnk_death_t = min(NS.DEATH_TIME,
                                    getattr(boss, "_gnk_death_t", 0.0) + dt)
        else:
            boss._gnk_death_t = 0.0

        # ── timeline serangan ───────────────────────────────────────
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 38)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_gnk_previous_timer", 0))
        active = bool(getattr(boss, "_gnk_attack_active", False))
        span = max(1, cooldown - 1)

        # Serangan dikenali dari EVENT eksplisit (_basic_attack_seq ditulis
        # Hero._do_attack / Boss.update). Fallback pola timer untuk alat
        # preview. Frame diturunkan DARI SISA TIMER, bukan di-increment per
        # pemanggil, supaya cache-probe / beam-pass yang memanggil renderer
        # berkali-kali dalam satu frame tidak mempercepat ayunan.
        seq_present = hasattr(boss, "_basic_attack_seq")
        seq = int(getattr(boss, "_basic_attack_seq", 0) or 0)
        last_seq = getattr(boss, "_gnk_last_attack_seq", None)
        seq_changed = seq_present and seq != last_seq
        timer_started = (timer >= cooldown - 1
                         and (previous <= 1 or timer > previous))
        triggered = bool(timer > 0
                         and (seq_changed
                              or (not seq_present and timer_started)))

        if seq_changed:
            boss._gnk_last_attack_seq = seq

        if triggered:
            boss._gnk_attack_active = True
            boss._gnk_attack_manual = False
            active = True
        elif timer > 0 and active:
            boss._gnk_attack_manual = False
        elif timer <= 0:
            manual_progress = float(getattr(boss, "_gnk_attack_progress",
                                            0.0) or 0.0)
            if (active and not seq_present and previous <= 0
                    and not getattr(boss, "_gnk_attack_manual", False)
                    and manual_progress > 0.0):
                # Ada yang mengaktifkan serangan TANPA menyentuh timer
                # (alat audit/preview/test): hormati, tandai manual, dan
                # jangan dimatikan di sini. Syarat previous<=0 mencegah
                # akhir serangan engine tersalah-baca sebagai manual.
                boss._gnk_attack_manual = True
                active = True
            elif not getattr(boss, "_gnk_attack_manual", False):
                boss._gnk_attack_active = False
                boss._gnk_attack_frame = 0
                active = False
            if not active:
                boss._gnk_attack_active = False
                boss._gnk_attack_frame = 0

        boss._gnk_previous_timer = timer
        if bool(getattr(boss, "_gnk_attack_manual", False)) and active:
            # Mode alat preview: pemanggil menggerakkan _gnk_attack_progress
            # sendiri; kita turunkan fase + jendela hit dari angka itu.
            progress = min(1.0, max(0.0, float(getattr(
                boss, "_gnk_attack_progress", 0.0))))
            boss._gnk_attack_frame = int(round(progress * span))
        else:
            frame = max(0, min(span, cooldown - timer)) if active else 0
            boss._gnk_attack_frame = frame
            progress = min(1.0, frame / float(span)) if active else 0.0
            boss._gnk_attack_progress = progress

        if not getattr(boss, "_gnk_attack_active", False):
            # pemanggil mematikan serangannya -> lupa status manual
            boss._gnk_attack_active = False
            boss._gnk_attack_manual = False
            active = False

        phase = NS.attack_phase(progress) if active else "NONE"
        boss._gnk_attack_phase = phase
        lo, hi = NS.ATTACK_ACTIVE_WINDOW
        boss._gnk_hit_active = bool(active and lo <= progress < hi)

        # ── respons kena damage: flash boss 8..0 -> HURT>=10 frame ───
        hurt = int(getattr(boss, "_gnk_hurt_frames", 0))
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        if flash >= 8 and hurt <= 0:
            hurt = 10
        boss._gnk_hurt_frames = max(0, hurt - 1) if hurt > 0 else 0

        # ── state machine berprioritas ──────────────────────────────
        want = NS._resolve_anim_state(boss, active, phase)
        cur = getattr(boss, "_gnk_state", None)
        if cur is None:
            boss._gnk_state = want
            boss._gnk_state_prev = want
            boss._gnk_state_time = 0.0
        elif want != cur:
            cur_p = NS.ANIM_STATES.get(cur, 0)
            new_p = NS.ANIM_STATES.get(want, 0)
            stime = float(getattr(boss, "_gnk_state_time", 0.0))
            # DEATH mengunci; state lain menang bila prioritas >=, atau
            # state lama sudah lewat 0.08 s (anti pose tersangkut).
            if cur != "DEATH" and (new_p >= cur_p or stime > 0.08):
                boss._gnk_state_prev = cur
                boss._gnk_state = want
                boss._gnk_state_time = 0.0
            else:
                boss._gnk_state_time = stime + dt
        else:
            boss._gnk_state_time = float(getattr(boss, "_gnk_state_time",
                                                 0.0)) + dt

    @staticmethod
    def _detect_moving(boss):
        """Apakah unit berpindah sejak frame lalu (cache + flag)."""
        cur_x = float(getattr(boss, "x", 0.0))
        cur_y = float(getattr(boss, "y", 0.0))
        if not hasattr(boss, "_gnk_last_x"):
            boss._gnk_last_x = cur_x
            boss._gnk_last_y = cur_y
            boss._moving_cached = False
            return False
        moved = abs(cur_x - boss._gnk_last_x) + abs(cur_y - boss._gnk_last_y)
        boss._gnk_last_x = cur_x
        boss._gnk_last_y = cur_y
        moving = moved > 0.3
        # Nama sama dengan hero lain (kaizen/zephyr/dll): satu konvensi
        # untuk state machine & kunci sprite cache.
        boss._moving_cached = moving
        return moving

    @staticmethod
    def set_victory(boss, on=True):
        """VICTORY / special state — dipanggil game setelah menang atau
        oleh alat preview. Murni visual; tidak menyentuh stats."""
        try:
            boss._gnk_victory = bool(on) and bool(getattr(boss, "alive",
                                                           True))
        except Exception:                          # pragma: no cover
            pass
        return boss

    # ==================================================================
    # POSE STATE — satu sumber kebenaran untuk rig DAN semua FX
    # ==================================================================
    ACTIONS = ("idle", "walk", "attack", "surge", "ward", "void",
               "blink", "victory", "death", "spawn")

    #: pose yang dipetakan per tombol skill (kontrak test_pose_router)
    SKILL_ACTION = {"q": "surge", "w": "blink", "e": "ward", "r": "void"}

    @staticmethod
    def _resolve_pose(boss, moving=False):
        """(action, phase, ap) — dipakai rig DAN anchor FX agar sinkron.

        MURNI (tanpa efek samping): boleh dipanggil ulang oleh fungsi
        efek kapan pun; hasil selalu sama untuk state yang sama sehingga
        sprite-cache lane hero tidak pernah berkedip.
        """
        NS = _NS_gornak
        skill = getattr(boss, "active_skill", None)
        if skill in NS.SKILL_ACTION:
            action = NS.SKILL_ACTION[skill]
        elif getattr(boss, "_gnk_victory", False) \
                and getattr(boss, "alive", True):
            action = "victory"
        elif (getattr(boss, "_gnk_attack_active", False)
              or getattr(boss, "timer", 0)
              > getattr(boss, "attack_cooldown", 40) - 15):
            action = "attack"
        elif moving:
            action = "walk"
        else:
            action = "idle"

        phase = float(getattr(boss, "pulse", 0.0))
        if action == "walk":
            run = float(getattr(boss, "speed", 1.0)) >= 2.2
            phase *= 2.6 if run else 2.0
        ap = 0.0
        if action == "attack":
            raw = max(0.0, min(1.0, float(getattr(boss,
                                                   "_gnk_attack_progress",
                                                   0.0))))
            ap = NS._attack_curve(raw)
            boss._gnk_attack_raw = raw
        return action, phase, ap

    # ── anatomi ruang LOKAL (y=0 garis pinggang; +y ke bawah) ───────
    # Puncak topknot -38 .. telapak +44 → 108 px setelah SCALE+LIFT —
    # sejajar keluarga mini boss; wajah tetap di bawah HP bar boss.
    HEAD_Y = -27
    SHOULDER_Y = -14
    SHOULDER_FRONT = (14, -12)
    SHOULDER_BACK = (-13, -13)
    WAIST_Y = 4
    HIP_Y = 6
    #: rongga dada — dipakai alat audit untuk mengecek bilah TIDAK
    #: pernah menembus torso sendiri.
    CHEST_BOX = (-8, -11, 8, -4)

    #: Kunci fase ayunan — dipakai grip, sudut bilah, DAN pita slash.
    _SWING_WIND = 0.26                    # puncak wind-up (bilah di atas)
    _SWING_HIT = 0.80                     # frame impact (bilah menyapu)

    @staticmethod
    def _attack_curve(ap):
        """Remap progres mentah 0..1 -> waktu pose 0..1, MONOTON naik.

        Yang membuat ayunan 2D terasa murah bukan jumlah frame, tapi
        tidak adanya: (a) anticipation yang terbaca, (b) TAHAN di puncak
        dan HOLD saat impact, (c) follow-through yang tidak langsung
        ditarik balik. Empat segmen ini memberi ketiganya dengan kontras
        laju ~17x antara tebasan dan hold.

        Batas segmen jatuh PERSIS di patahan _SWING_WIND/_SWING_HIT,
        jadi tabel grip & sudut bilah tidak pernah "patah" di tengah
        transisi — nama fase, pose, dan FX membaca angka yang sama.
        """
        if ap <= 0.0:
            return 0.0
        if ap >= 1.0:
            return 1.0
        NS = _NS_gornak
        w, h = NS._SWING_WIND, NS._SWING_HIT
        if ap < 0.30:                    # angkat ke atas lalu TAHAN
            t = ap / 0.30
            return w * (t ** 0.80)
        if ap < 0.46:                      # tebasan: dipercepat
            t = (ap - 0.30) / 0.16
            return w + (h - w - 0.03) * (t ** 1.15)
        if ap < 0.60:                      # IMPACT HOLD (nyaris beku)
            t = (ap - 0.46) / 0.14
            return (h - 0.03) + 0.03 * t
        t = (ap - 0.60) / 0.40             # follow-through -> garda siap
        return h + (1.0 - h) * (t ** 0.80)

    @staticmethod
    def _portrait_blade_angle(back=False):
        """Sudut bilah mode portrait: rapat ke badan, ujung menukik.

        HeroPortraits meng-crop bbox lalu men-scale-nya ke kartu — figur
        yang LEBAR (cleaver terentang) justru terKECIL di kartu. Dengan
        senjata ditarik masuk, bbox menyempit dan figur ter-render lebih
        besar: wajah & zirah akhirnya terbaca.
        """
        return -0.68 if back else 0.98

    @staticmethod
    def _blade_angle(phase, action, ap=0.0, back=False):
        """Sudut bilah (rad): tip = grip + (sin a * L, cos a * L).

        a=0 menunjuk LURUS KE BAWAH, a=pi/2 lurus ke depan, a=pi lurus
        ke atas. Tangan DEPAN memegang CLEAVER (overhead chop: angkat ke
        atas-belakang -> tebas turun menyapu depan); tangan BELAKANG
        memegang BELATI reverse-grip yang bergerak berlawanan sebagai
        penyeimbang — dua senjata tidak pernah sejajar.
        """
        NS = _NS_gornak
        s = math.sin(phase * 1.72)
        if action == "attack":
            w, h = NS._SWING_WIND, NS._SWING_HIT
            if ap < w:                     # wind-up: angkat tinggi
                u = ap / w
                return (2.05 + 1.75 * u, -0.90 - 0.45 * u)[back]
            if ap < h:                     # OVERHEAD CHOP turun ke depan
                u = (ap - w) / (h - w)
                return (3.80 - 2.60 * u, -1.35 + 0.75 * u)[back]
            u = (ap - h) / (1.0 - h)       # recovery -> garda siap
            return (1.20 + 0.85 * u, -0.60 - 0.30 * u)[back]
        if action == "surge":              # Q: tusukan mana mendatar
            return (1.62, -1.30)[back]
        if action == "ward":               # E: dua bilah tegak = garda X
            return (2.85, -2.85)[back]
        if action == "void":               # R: kedua bilah dibuka ke atas
            return (2.52, -2.52)[back]
        if action == "blink":              # W: profil rendah, bilah rapat
            return (0.88, -0.78)[back]
        if action == "victory":            # kemenangan: cleaver diangkat
            return (3.05, -1.85)[back]
        if action == "death":
            return (0.55, -0.35)[back]
        if action == "walk":
            return (2.05 + 0.12 * s, -0.90 - 0.10 * s)[back]
        # garda siap: cleaver diagonal depan-atas, belati menukik ke
        # belakang-bawah — asimetris supaya kepala & dada tetap subjek.
        w = math.sin(phase * 0.62) * 0.05
        return (2.05 + w, -0.90 - w)[back]

    @staticmethod
    def _front_grip_local(action, ap=0.0, phase=0.0, compact=False):
        """Pergelangan tangan DEPAN (cleaver), ruang lokal."""
        NS = _NS_gornak
        rest = NS.SHOULDER_Y + 14                        # = 0
        if compact:
            return (10, rest + 2)
        if action == "attack":
            w, h = NS._SWING_WIND, NS._SWING_HIT
            if ap < w:
                e = (ap / w) ** 0.9
                return (int(13 - 18 * e), int(rest - 23 * e))
            if ap < h:
                u = (ap - w) / (h - w)
                return (int(-5 + 25 * u), int(rest - 23 + 29 * u))
            u = (ap - h) / (1.0 - h)
            return (int(20 - 7 * u), int(rest + 6 - 6 * u))
        if action == "surge":
            return (23, rest + 1)
        if action == "ward":
            return (9, rest - 10)
        if action == "void":
            return (17, rest - 11)
        if action == "blink":
            return (12, rest - 2)
        if action == "victory":
            return (7, rest - 15)
        if action == "walk":
            s = math.sin(phase * 1.72)
            return (int(14 + 3 * s), int(rest - 2 * s))
        return (13.8, rest + int(math.sin(phase * 0.62)))

    @staticmethod
    def _back_grip_local(action, ap=0.0, phase=0.0, compact=False):
        """Pergelangan tangan BELAKANG (belati reverse-grip)."""
        NS = _NS_gornak
        rest = NS.SHOULDER_Y + 15                        # = 1
        if compact:
            return (-10, rest + 2)
        if action == "attack":
            w, h = NS._SWING_WIND, NS._SWING_HIT
            if ap < w:
                e = (ap / w) ** 0.9
                return (int(-15 + 5 * e), int(rest - 14 * e))
            if ap < h:
                u = (ap - w) / (h - w)
                return (int(-10 - 4 * u), int(rest - 13 + 21 * u))
            u = (ap - h) / (1.0 - h)
            return (int(-13 + 3 * u), int(rest + 8 - 7 * u))
        if action == "surge":
            return (-16, rest - 2)
        if action == "ward":
            return (-9, rest - 10)
        if action == "void":
            return (-16, rest - 11)
        if action == "blink":
            return (-12, rest - 1)
        if action == "victory":
            return (-14, rest - 6)
        if action == "walk":
            s = math.sin(phase * 1.72)
            return (int(-12 + 3 * s), int(rest + 2 * s))
        return (-12.4, rest + int(math.sin(phase * 0.62 + 1.1)))

    @staticmethod
    def _elbow(a, b, bend):
        """Siku dua-tulang: titik tengah + offset tegak lurus.

        Lengan selalu tersambung (tidak pernah "lepas" seperti sticker)
        dan lengkungannya bisa diarahkan per sisi.
        """
        mx = (a[0] + b[0]) * 0.5
        my = (a[1] + b[1]) * 0.5
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        return (int(mx + (-dy / ln) * bend), int(my + (dx / ln) * bend))

    @staticmethod
    def _arm_chain(shoulder, grip, phase, action, ap=0.0, back=False):
        """(elbow, blade_angle) — siku dari lengan, sudut dari tabel pose."""
        NS = _NS_gornak
        elbow = NS._elbow(shoulder, grip, 5.0 if back else -4.5)
        return elbow, NS._blade_angle(phase, action, ap, back)

    @staticmethod
    def _blade_len(action, back=False):
        """Panjang senjata.

        Cleaver depan = jangkauan utama; belati belakang sengaja pendek
        supaya siluet tetap rapat — lebar siluet datang dari TUBUH,
        bukan dari dua pedang panjang menyilang (biang "palang" v3).
        """
        if back:
            return 17 if action == "attack" else 16
        if action in ("attack", "surge"):
            return 40
        if action in ("ward", "void"):
            return 38
        if action == "victory":
            return 39
        if action == "death":
            return 30
        return 38

    @staticmethod
    def _head_bob(action, phase, ap):
        """Offset kepala (dx, dy) lokal — kepala TIDAK direkat ke torso.

        Mengangguk mengikuti langkah, menunduk menghantam saat ayunan,
        mendongak saat victory, bergoyang halus saat idle (napas).
        """
        if action == "walk":
            return (-int(round(math.sin(phase * 1.72) * 1.4)),
                    -1 - int(round(abs(math.sin(phase * 1.15)) * 1.2)))
        if action == "attack":
            k = math.sin(ap * math.pi)
            return (int(round(k * 3.0)), -int(round(k * 1.8)))
        if action == "void":
            return (-1, -3)
        if action == "ward":
            return (0, -1)
        if action == "surge":
            return (2, 0)
        if action == "victory":
            return (0, -2)
        if action == "death":
            return (2, 2)
        return (int(round(math.sin(phase * 0.31) * 0.9)),
                int(round(math.sin(phase * 0.62 + 0.8) * 0.8)))

    @staticmethod
    def _rig_shift(action, phase, ap):
        """(lean, root_y) badan; KAKI tidak ikut bergeser — telapak patok.

        squash & stretch versi pixel: napas mengangkat root, ayunan
        melempar bobot ke depan (lean) lalu menariknya kembali.
        """
        lean = 0
        root_y = int(math.sin(phase * 0.62) * 1.2)
        if action == "walk":
            lean = int(math.sin(phase * 1.72) * 2)
            root_y -= int(abs(math.sin(phase * 1.15)) * 2.5)
        elif action == "attack":
            k = math.sin(ap * math.pi)
            lean = int(k * 6)
            root_y += int(k * 2)
        elif action == "surge":
            lean, root_y = 3, -1
        elif action in ("void", "ward"):
            root_y -= 2
        elif action == "blink":
            lean, root_y = 1, -1
        elif action == "victory":
            root_y -= 2
        elif action == "death":
            lean = 2
        return lean, root_y

    @staticmethod
    def _s(v):
        """Ukuran ruang lokal (lebar garis, radius) -> piksel layar."""
        return max(1, int(round(v * _NS_gornak.SCALE)))

    @staticmethod
    def _local_to_screen(cx, cy, facing, lean, root_y, lx, ly):
        """SATU pemetaan lokal -> layar: skala, arah hadap, bob/lean.

        Semua bagian tubuh dan semua jangkar efek (ujung bilah,
        pergelangan) melewati fungsi ini — ukuran boleh diubah lewat satu
        angka tanpa membuat efek lepas dari badan.
        """
        NS = _NS_gornak
        f = 1 if facing >= 0 else -1
        k = NS.SCALE
        return (int(cx + (lx * f + lean * f) * k),
                int(cy - NS.LIFT + (ly + root_y) * k))

    @staticmethod
    def _local(boss, x, y, action, phase, ap, lx, ly):
        """Ruang lokal rig -> piksel surface (dipakai FX eksternal)."""
        NS = _NS_gornak
        facing = getattr(boss, "direction", 1) or 1
        lean, root_y = NS._rig_shift(action, phase, ap)
        return NS._local_to_screen(x, y, facing, lean, root_y, lx, ly)

    @staticmethod
    def _tip_local(action, phase, ap=0.0, back=False):
        """Ujung bilah ruang lokal — rig & FX memakai angka yang sama."""
        NS = _NS_gornak
        grip = (NS._back_grip_local(action, ap, phase) if back
                else NS._front_grip_local(action, ap, phase))
        shoulder = NS.SHOULDER_BACK if back else NS.SHOULDER_FRONT
        _, angle = NS._arm_chain(shoulder, grip, phase, action, ap, back)
        L = NS._blade_len(action, back)
        return (int(grip[0] + math.sin(angle) * L),
                int(grip[1] + math.cos(angle) * L))

    @staticmethod
    def _tip_screen(boss, x, y, back=False):
        NS = _NS_gornak
        action, phase, ap = NS._resolve_pose(boss)
        # FX selalu memakai pose yang SAMA dengan badan (lihat
        # _resolve_pose yang murni) — bolt/proc tidak pernah lepas.
        return NS._local(boss, x, y, action, phase, ap,
                         *NS._tip_local(action, phase, ap, back))

    # ==================================================================
    # LAPISAN FX HIDUP (heroes/gornak_fx)
    # ==================================================================
    #: Modul FX layar (diisi malas). False = percobaan gagal -> canvas.
    _LIVE_MOD = None

    @staticmethod
    def _live_module():
        """Muat ``heroes.gornak_fx`` sekali; None kalau tidak tersedia.

        Impor DI SINI (bukan di kepala modul) supaya modul boss besar tidak
        menarik paket hero saat build hanya-butuh-renderer, dan supaya FX
        bisa dimatikan satu flag tanpa merusak jalur render.
        """
        NS = _NS_gornak
        if NS._LIVE_MOD is None:
            try:
                from heroes import gornak_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "GORNAK_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    @staticmethod
    def live_fx_ready():
        """True kalau lapisan hidup Gornak bisa dipakai (dipakai tooling)."""
        return _NS_gornak._live_module() is not None

    @staticmethod
    def _live_fx(boss, surface, x, y, want_draw, portrait):
        """Kembalikan ``(mod, owned)`` untuk unit ini.

        ``owned`` True = efek ayunan/bolt sudah DIAMBIL ALIH lapisan
        hidup; renderer melewati salinan di-canvas (anti-gambar-dobel).
        ``want_draw`` True pada jalur BOSS (digambar tiap frame tanpa
        cache sprite); pada jalur HERO cukup pasang penanda —
        heroes/__init__ yang menggambar lapisannya tiap frame. Kalau modul
        FX gagal diimpor, keduanya False dan canvas fallback tetap
        lengkap: visual kehilangan polish, TIDAK PERNAH kehilangan efek.
        """
        NS = _NS_gornak
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
    # ENTRY POINT
    # ==================================================================
    @staticmethod
    def draw_gornak(surface, boss, x, y):
        """Entry point Boss.draw() SEKALIGUS heroes.render_hero().

        Render order (kontrak proyek, identik di kedua jalur):

            GROUND (telegraph, rune) -> SHADOW -> BODY/ARMOR/HEAD ->
            WEAPON -> ATTACK TRAIL -> PROJECTILE -> SKILL FX -> IMPACT ->
            STATUS/HIT FLASH -> DEBUG

        Yang butuh 60fps sejati (trail, partikel, bolt, impact, shake)
        hidup di heroes/gornak_fx di LUAR sprite cache; kalau modul itu
        tidak ada, semuanya digambar di-canvas (fallback) — gameplay
        telegraph (cincin E/R, proc Q) TIDAK PERNAH ikut hilang.
        """
        NS = _NS_gornak
        # jalur hero (lane): pipeline men-set _render_scale sebelum
        # memanggil renderer dan _finish_hd_sprite menambah rim/terminator
        # -> pass cahaya di sini dilewati.
        hero_lane = hasattr(boss, "_render_scale")
        # Cache sprite BOSS juga men-set _render_scale — tapi pada skala
        # NATIF 1.0 dan TANPA pass heroes; penanda _boss_native_cache
        # membuat pass cahaya renderer tetap jalan.
        NS._HERO_LANE.v = hero_lane and not getattr(boss,
                                                    "_boss_native_cache",
                                                    False)
        NS._update_gnk_attack_anim(boss)
        action, phase, ap = NS._resolve_pose(boss, NS._detect_moving(boss))
        boss._gnk_pose_action = action
        skill = getattr(boss, "active_skill", None)
        timer = int(getattr(boss, "active_skill_timer", 0))
        portrait = bool(getattr(boss, "_portrait_hd", False))
        facing = getattr(boss, "direction", 1) or 1
        flash = NS._alpha(170 * (getattr(boss, "hurt_flash_timer", 0)
                                 / 8.0))
        # Jalur boss digambar tiap frame TANPA cache -> lapisan hidup
        # dipicu dari sini. Jalur lane sudah dipicu heroes/__init__.
        live, owned = NS._live_fx(boss, surface, x, y,
                                  not hero_lane, portrait)

        # ── Latar. Dibuang TOTAL saat portrait: auto-crop Hero Shop harus
        #    terisi wajah & material, bukan lingkaran efek.
        if not portrait:
            NS.render_aura(surface, boss, x, y, phase, action, skill)
            if skill != "r":
                # saat ULT, segel void menutupi rune -> hemat di frame
                # paling berat
                NS._draw_ground_rune(surface, x, y, phase, skill)
            if skill == "q":
                NS._draw_manabreak_ground(surface, boss, x, y, timer, phase)
            elif skill == "w":
                NS._draw_blink_ground(surface, boss, x, y, timer, phase)
            elif skill == "r":
                NS._draw_manavoid_ground(surface, boss, x, y, timer, phase)
            if not owned:
                NS._draw_cast_shockwave(surface, boss, x, y, skill, timer)

        # ── Karakter (spawn / death di-handle di dalam rig_at)
        if action == "blink":
            NS._draw_gnk_blink(surface, boss, x, y, timer, portrait, flash)
        else:
            if not portrait:
                NS.render_shadow(surface, x, y + NS.GROUND_DY)
            NS._draw_gnk_rig_at(surface, x, y, facing, phase, action, ap,
                               portrait, flash)
            if not portrait:
                NS.render_status_overlay(surface, boss, x, y, phase)
                if action == "attack" and not owned:
                    # pita ayunan DI-CANVAS hanya kalau lapisan hidup tidak
                    # mengambil alih (canvas lane di-smoothscale -> pita
                    # di sana lembek; trail layar 1:1 lebih tajam)
                    NS._draw_crescent_slash(surface, x, y, facing, phase, ap)
                elif action == "walk":
                    # debu langkah: kepul kecil TEPAT saat telapak
                    # mendarat — bobot badan menekan tanah
                    NS._draw_footfall_dust(surface, x, y, facing, phase)

        # ── Foreground FX per skill (telegraph dunia — selalu canvas)
        if not portrait:
            if skill == "q":
                if not owned:
                    NS._draw_manabreak_foreground(surface, boss, x, y,
                                                 timer, phase)
            elif skill == "e":
                NS._draw_counterspell_foreground(surface, boss, x, y, timer,
                                                 phase)
            elif skill == "r":
                NS._draw_manavoid_foreground(surface, boss, x, y, timer,
                                             phase)

        # ── Lapisan hidup bagian ATAS + debug overlay
        if live is not None:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass
        if NS.DEBUG_CHARACTER and not portrait:
            NS._draw_gnk_debug(surface, boss, x, y, action, owned)

    # ==================================================================
    # DEBUG OVERLAY  (DEBUG_CHARACTER = True)
    # ==================================================================
    @staticmethod
    def _draw_gnk_debug(surface, boss, x, y, action, owned):
        """Hitbox, hurtbox, jangkauan, state/frame, FPS, jumlah partikel.

        Tidak menyentuh gameplay: angka dibaca dari state yang sudah ada,
        overlay digambar PALING AKHIR supaya tidak tertutup apa pun.
        """
        NS = _NS_gornak

        # hurtbox = lingkaran radius unit
        r = max(6, int(getattr(boss, "radius", 16) * 0.9 * NS.SCALE))
        pygame.draw.rect(surface, (80, 170, 255, 150),
                         pygame.Rect(int(x) - r, int(y) - r - 8, r * 2,
                                     r * 2), 1)

        # jangkauan serangan
        rng = max(10, int(getattr(boss, "range", 60) * NS.SCALE * 0.9))
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        pygame.draw.line(surface, (255, 210, 60, 150), (int(x), int(y)),
                         (int(x) + int(rng * f), int(y)), 1)
        pygame.draw.rect(surface, (255, 210, 60, 110),
                         pygame.Rect(int(x + rng * f) - 5, int(y) - 7,
                                     10, 14), 1)

        # hitbox ayunan — hanya saat jendela hit aktif
        hb = NS._swing_hitbox(boss, x, y)
        if hb is not None:
            pygame.draw.rect(surface, (255, 70, 70, 190), hb, 2)
            pygame.draw.rect(surface, (255, 70, 70, 60), hb)

        # proyektil lapisan hidup
        if owned:
            try:
                mod = NS._LIVE_MOD
                for p in mod.projectiles_for(boss):
                    rr = max(3, int(p["hit_radius"]))
                    pygame.draw.circle(surface, (255, 120, 255, 170),
                                       (int(p["sx"]), int(p["sy"])), rr, 1)
            except Exception:
                pass

        # panel teks
        fps = getattr(boss, "_gnk_fps", None)
        if fps is None:
            boss._gnk_fps = 60.0
            fps = 60.0
        else:
            dt = float(getattr(boss, "_gnk_dt", 1.0 / 60.0))
            inst = 1.0 / dt if dt > 0 else 60.0
            boss._gnk_fps = fps + (inst - fps) * 0.1
            fps = boss._gnk_fps
        lines = (
            "GORNAK  %.0f fps" % fps,
            "state %s (prev %s) %.2fs" % (
                getattr(boss, "_gnk_state", "IDLE"),
                getattr(boss, "_gnk_state_prev", "-"),
                float(getattr(boss, "_gnk_state_time", 0.0))),
            "action %s  phase %s" % (action,
                                     getattr(boss, "_gnk_attack_phase",
                                             "NONE")),
            "atk frame %d/%d  prog %.2f  hit %s" % (
                int(getattr(boss, "_gnk_attack_frame", 0)),
                max(1, int(getattr(boss, "attack_cooldown", 38)) - 1),
                float(getattr(boss, "_gnk_attack_progress", 0.0)),
                "ON" if getattr(boss, "_gnk_hit_active", False) else "off"),
            "timer %d  hurt %d" % (int(getattr(boss, "timer", 0)),
                                   int(getattr(boss, "_gnk_hurt_frames", 0))),
            "skill %s  %d  live %s" % (
                getattr(boss, "active_skill", None) or "-",
                int(getattr(boss, "active_skill_timer", 0)),
                "on" if owned else "canvas"),
            "particles %d  dt %.1fms" % (
                int(NS._LIVE_MOD.total_particles())
                if NS._LIVE_MOD else 0,
                float(getattr(boss, "_gnk_dt", 1.0 / 60.0)) * 1000.0),
        )
        fnt = pygame.font.SysFont("consolas,monospace", 10)
        y0 = int(y) - int(140 * NS.SCALE) - 12 * len(lines)
        box = pygame.Rect(int(x) - 99, y0 - 2, 200, 12 * len(lines) + 4)
        bg = pygame.Surface(box.size, pygame.SRCALPHA)
        bg.fill((6, 4, 12, 150))
        surface.blit(bg, box.topleft)
        for i, t in enumerate(lines):
            txt = fnt.render(t, True, (255, 226, 150))
            surface.blit(txt, (box.x + 3, box.y + 1 + i * 12))

    @staticmethod
    def _draw_cast_shockwave(surface, boss, x, y, skill, timer):
        """Gelombang kejut 12 frame PERTAMA setiap skill (world-space).

        Satu "tanda baca" yang sama untuk Q/W/E/R: pemain langsung tahu
        sebuah skill baru keluar tanpa perlu membaca efeknya.
        """
        NS = _NS_gornak
        if skill not in NS.SKILL_DUR:
            return
        age = NS.SKILL_DUR[skill] - timer
        if not (0 <= age < 12):
            return
        p = NS.PALETTE
        st = age / 12.0
        fs = NS._fx_scale(boss)
        a = NS._alpha(235 * (1 - st) ** 1.4)
        rr = int((16 + st * 52) * fs)
        gy = y + NS.GROUND_DY
        NS._ellipse(surface, (*p["magic_mid"], a),
                    (x - rr, gy - rr // 3, rr * 2, max(4, rr * 2 // 3)), 2)
        NS._ellipse(surface, (*p["magic_shine"], a),
                    (x - rr // 2, gy - rr // 6, rr, max(3, rr // 3)), 1)
        for i in range(6):
            ang = i * math.tau / 6 + st * 1.2
            NS._shard(surface, x + math.cos(ang) * rr * 0.9,
                      gy + math.sin(ang) * rr * 0.3, ang,
                      int(6 * fs * (1 - st)) + 2, max(1, int(2 * fs)),
                      p["magic_light"], a, core=p["magic_shine"])
        NS._spark_star(surface, x, gy - 4, int(10 * fs * (1 - st)),
                       p["magic_hot"], a, spikes=8, rot=st * 1.4,
                       core=p["magic_shine"])

    # ==================================================================
    # RIG — SATU buffer, satu blit
    # ==================================================================
    #: pool buffer (aturan perf: jangan alokasi Surface per frame)
    _RIG_POOL = []

    @staticmethod
    def _rig_surface():
        pool = _NS_gornak._RIG_POOL
        if pool:
            buf = pool.pop()
            buf.fill((0, 0, 0, 0))
            return buf
        return pygame.Surface((_NS_gornak.RIG_W, _NS_gornak.RIG_H),
                              pygame.SRCALPHA)

    @staticmethod
    def _rig_release(buf):
        pool = _NS_gornak._RIG_POOL
        if len(pool) < 3:
            pool.append(buf)

    @staticmethod
    def _draw_gnk_rig_at(surface, x, y, facing, phase, action, ap, detail,
                         flash=0, boss=None):
        """Rig -> buffer -> outline gelap 1 px -> satu blit murah.

        Mode portrait Hero Shop memakai kanvas kecil (160x160) dan
        meng-crop dari bbox: badan dengan anchor di pinggang membuat
        cleaver melewati tepi kanan dan TERPOTONG. Jadi di mode portrait
        konten dipusatkan pada bbox-nya sendiri; jalur boss tidak
        berubah sama sekali.

        v5: ``boss`` (kalau diberikan) mengaktifkan lapisan SPAWN
        (bangkit dari tanah, badan terpotong garis tanah) dan DEATH
        (collapse + memudar + serpihan rune). Deterministik terhadap
        timer -> sprite-cache lane hero tetap konsisten.
        """
        NS = _NS_gornak
        # ── transform spawn / death ─────────────────────────────────
        sink = 0
        fade = 255
        if boss is not None:
            # spawn HANYA setelah timer benar-benar berdetak (0 < sp <
            # SPAWN_TIME): frame pertama sebuah unit (dan semua probe
            # satu-render di tools/pipeline pengukur) tidak tersentuh,
            # jadi auto-scale & test keluarga melihat pose standar.
            sp = float(getattr(boss, "_gnk_spawn_t", 0.0) or 0.0)
            if 0.0 < sp < NS.SPAWN_TIME - 1e-9:
                k = max(0.0, min(1.0, sp / NS.SPAWN_TIME))
                sink = int(round(k * k * 8))
            if not getattr(boss, "alive", True):
                d = float(getattr(boss, "_gnk_death_t", 0.0) or 0.0)
                kd = min(1.0, d / 0.6)
                sink += int(round(kd * 14))
                fade = int(255 - 150 * min(1.0, d / NS.DEATH_TIME))

        buf = NS._rig_surface()
        NS._draw_gnk_rig(buf, NS.RIG_OX, NS.RIG_OY + sink, facing, phase,
                         action, ap, detail)
        if sink:
            # potong di garis tanah: badan "tenggelam" saat spawn/death
            ground_row = NS.RIG_OY - NS.LIFT + int(NS.FEET_DY * NS.SCALE) + 1
            buf.fill((0, 0, 0, 0),
                     (0, ground_row, NS.RIG_W, NS.RIG_H - ground_row))
        if flash > 0:
            lit = buf.copy()
            lit.fill((255, 246, 255, 0),
                     special_flags=pygame.BLEND_RGBA_MAX)
            lit.set_alpha(flash)
            buf.blit(lit, (0, 0))
            NS._rig_release(lit)
        # Pass cahaya (rim + terminator + gradien arah): HANYA kalau
        # sprite ini tidak akan lewat heroes._finish_hd_sprite:
        #   * boss 1x (tanpa _render_scale)      -> pasang di sini
        #   * lane hero (punya _render_scale)    -> jangan (dobel)
        #   * Hero Shop portrait (tanpa scale)   -> pasang di sini
        if _lighting is not None and not NS._HERO_LANE.v and fade == 255:
            _lighting.apply_to_rig(
                buf, rim_add=(32, 26, 46), shade_mul=160,
                box=NS.GRAD_BOX if not detail else None)
        if fade < 255:
            buf.set_alpha(fade)

        ox = int(x) - NS.RIG_OX
        oy = int(y) - NS.RIG_OY
        if detail:                      # portrait: pusatkan konten
            used = buf.get_bounding_rect(min_alpha=1)
            if used.width > 0:
                ox = int(x) - (used.left + used.width // 2)
                oy = int(y) - (used.top + used.height // 2)
        # Outline siluet: salinan hitam (alpha dipertahankan lewat MULT)
        # digeser 4 arah — bagian tetap terpisah saat unit bertumpuk.
        edge = buf.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surface.blit(edge, (ox + dx, oy + dy))
        surface.blit(buf, (ox, oy))
        NS._rig_release(edge)
        NS._rig_release(buf)
        return buf

    # Pose tunggal (dipakai tool debug/preview + wrapper render_*).
    def _draw_gnk_idle(surface, boss, x, y):
        _NS_gornak._draw_gnk_rig_at(surface, x, y,
                                    getattr(boss, "direction", 1) or 1,
                                    float(getattr(boss, "pulse", 0.0)),
                                    "idle", 0.0, False, boss=boss)

    def _draw_gnk_walk(surface, boss, x, y):
        _NS_gornak._draw_gnk_rig_at(surface, x, y,
                                    getattr(boss, "direction", 1) or 1,
                                    float(getattr(boss, "pulse", 0.0)) * 2.0,
                                    "walk", 0.0, False, boss=boss)

    def _draw_gnk_attack(surface, boss, x, y, ap=0.5):
        _NS_gornak._draw_gnk_rig_at(surface, x, y,
                                    getattr(boss, "direction", 1) or 1,
                                    float(getattr(boss, "pulse", 0.0)),
                                    "attack", ap, False, boss=boss)

    @staticmethod
    def _draw_gnk_blink(surface, boss, x, y, timer, portrait, flash):
        """Blink W: after-image RIG YANG SAMA + disolusi serpihan.

        Three ghosts stretch the path from the old position to the new
        one, a void shard dissolves at the exit point and a 6-spike
        arrival star closes it — the teleport reads as *motion*, not as
        the sprite simply appearing somewhere else.
        """
        NS = _NS_gornak
        p = NS.PALETTE
        duration = NS.SKILL_DUR["w"]
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = getattr(boss, "direction", 1) or 1
        phase = float(getattr(boss, "pulse", 0.0))
        # kurva snap: 62% durasi badan "hilang di void", lalu mendarat
        if progress < 0.30:
            alpha_t = 1.0 - progress / 0.30
        elif progress < 0.68:
            alpha_t = 0.14
        else:
            alpha_t = (progress - 0.68) / 0.32

        if not portrait:
            NS._draw_shadow(surface, x, y + NS.GROUND_DY)

        rig, ax, ay = NS._compose_outline(x, y, facing, phase, "blink",
                                          0.0, portrait)
        if progress < 0.80:
            for i in (3, 2, 1):
                rig.set_alpha(NS._alpha(80 * alpha_t / i))
                surface.blit(rig, (x - ax - facing * i * 8, y - ay + i))
        rig.set_alpha(NS._alpha(70 + 185 * min(1.0, alpha_t)))
        surface.blit(rig, (x - ax, y - ay))
        rig.set_alpha(255)

        if not portrait:
            # debu void di titik-titik perjalanan (deterministik phase)
            gy = y + NS.GROUND_DY
            for i in range(9):
                t = (phase * 0.5 + i * 0.111) % 1.0
                gx = x + int(math.sin(i * 1.7) * (10 + t * 18))
                a = NS._alpha(200 * (1 - t) * alpha_t)
                if a <= 0:
                    continue
                NS._shard(surface, gx, gy - int(t * 16),
                          -math.pi / 2 + math.sin(i * 2.1) * 0.5,
                          4 + int((1 - t) * 4), 2, p["magic_light"], a,
                          core=p["magic_shine"])
            # bintang kedatangan (hanya saat menapak)
            if progress > 0.68:
                k = min(1.0, (progress - 0.68) / 0.20)
                NS._spark_star(surface, x + facing * 6, y - 6,
                               int(14 * (1 - k) + 4), p["magic_hot"],
                               NS._alpha(220 * (1 - k)), spikes=6,
                               rot=phase * 0.2, core=p["magic_core"])

    @staticmethod
    def _compose_outline(x, y, facing, phase, action, ap, detail):
        """Rig + outline gelap 1 px sebagai SATU surface.

        After-image blink butuh mengatur alpha sendiri, jadi outline
        harus sudah menyatu dalam satu permukaan. Return
        ``(surface, anchor_x, anchor_y)`` — titik dalam surface yang
        jatuh tepat di dunia ``(x, y)``.
        """
        NS = _NS_gornak
        buf = NS._rig_surface()
        NS._draw_gnk_rig(buf, NS.RIG_OX, NS.RIG_OY, facing, phase, action,
                         ap, detail)
        pad = 1
        out = pygame.Surface((NS.RIG_W + pad * 2, NS.RIG_H + pad * 2),
                             pygame.SRCALPHA)
        edge = buf.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        # Selout: outline gelap hanya sisi bayangan (kanan-bawah relatif
        # hadap). Key light kiri-atas (lighting.LIGHT_DIR = (-1,-1)); sisi
        # cahaya dibiarkan bersih — rim 1 px ada di _draw_gnk_rimlight.
        sx = 1 if facing >= 0 else -1
        for dx, dy in ((sx, 0), (0, 1), (sx, 1)):
            out.blit(edge, (pad + dx, pad + dy))
        out.blit(buf, (pad, pad))
        NS._rig_release(edge)
        NS._rig_release(buf)
        return out, NS.RIG_OX + pad, NS.RIG_OY + pad

    # ==================================================================
    # BONE RIG 2D — v5. Prinsip pixel-art: SATU poligon dasar + SATU
    # bidang cahaya + maks 1 aksen 1px per bagian (kalau lebih, di 70-110
    # px badannya jadi noise). Semua bagian lewat _Ctx yang sama supaya
    # jangkar (bilah, scarf, FX) tidak pernah lepas dari badan.
    # ==================================================================
    class _Ctx:
        """ Konteks pemetaan lokal->layar + helper menggambar per-pose.

        Dibuat SEKALI per render; bagian tubuh apa pun (dan wrapper
        ``render_*`` publik) menggambar lewat objek yang sama, jadi tidak
        ada dua salinan matematika yang bisa melenceng.
        """

        __slots__ = ("surface", "f", "k", "cx", "cy", "lean", "root_y",
                     "p", "NS")

        def __init__(self, surface, cx, cy, facing, lean, root_y):
            self.surface = surface
            self.cx, self.cy = cx, cy
            self.f = 1 if facing >= 0 else -1
            self.lean = lean
            self.root_y = root_y
            self.k = _NS_gornak.SCALE
            self.NS = _NS_gornak
            self.p = _NS_gornak.PALETTE

        def pt(self, lx, ly):
            return _NS_gornak._local_to_screen(self.cx, self.cy, self.f,
                                               self.lean, self.root_y,
                                               lx, ly)

        def ptg(self, lx, ly):
            """Pemetaan TERKUNCI TANAH — kaki tidak ikut bob/lean."""
            k = self.k
            return (int(self.cx + lx * self.f * k),
                    int(self.cy - _NS_gornak.LIFT + ly * k))

        def P(self, pts, ptg=False):
            m = self.ptg if ptg else self.pt
            return [m(a, b) for a, b in pts]

        def poly(self, color, pts, selout=True, ptg=False):
            """Poligon + selout: salinan shadow_deep digeser ke sisi
            bayangan (1px, searah hadap) — ini yang menjaga siluet tetap
            terbaca saat unit bertumpuk."""
            q = self.P(pts, ptg)
            if selout:
                self.NS._poly(self.surface,
                              (*self.p["shadow_deep"],
                               color[3] if len(color) == 4 else 255),
                              [(x + self.f, y + 1) for x, y in q])
            self.NS._poly(self.surface, color, q)

        def poly_raw(self, color, qpts):
            """Poligon ruang layar (sudah dipetakan pemanggil)."""
            self.NS._poly(self.surface, color, qpts)

        def line(self, a, b, color, w=1, ptg=False):
            m = self.ptg if ptg else self.pt
            self.NS._aaline(self.surface, color, m(*a), m(*b), w)

        def dot(self, lx, ly, r, color):
            x, y = self.pt(lx, ly)
            self.NS._aacircle(self.surface, color, (x, y),
                              self.NS._s(r))

        def tick(self, lx, ly, color):
            """Highlight 1px — specular/paku; satuan piksel, bukan bulat."""
            x, y = self.pt(lx, ly)
            self.NS._rect(self.surface, color, (x, y, 1, 1))

    @staticmethod
    def _make_ctx(surface, cx, cy, facing, phase, action, ap):
        NS = _NS_gornak
        lean, root_y = NS._rig_shift(action, phase, ap)
        return NS._Ctx(surface, cx, cy, facing, lean, root_y)

    # ------------------------------------------------------------------
    # BAGIAN 1 — kaki (sol TERPATOK di FEET_DY; lutut yang naik-turun)
    # ------------------------------------------------------------------
    @staticmethod
    def _draw_gnk_legs(ctx, phase, action, ap, detail):
        NS = _NS_gornak
        p = ctx.p
        stride = math.sin(phase * 1.72) if action in ("walk", "idle",
                                                      "victory") else 0.0
        run = action == "walk" and abs(stride)
        if action == "attack":
            k_ = math.sin(ap * math.pi)
            stance = ((8.5 + k_ * 2.0, -6.5 - k_ * 0.8), (0, 0))
            front_x, back_x = stance[0]
            flift = int(k_ * 1.6)
            blift = 0
        elif action == "death":
            front_x, back_x, flift, blift = 9.0, -8.0, 0, 0
        else:
            front_x, back_x = 7.0, -7.0
            flift = int(max(0.0, -stride) * 3.2 * (1.3 if run else 1.0))
            blift = int(max(0.0, stride) * 3.2 * (1.3 if run else 1.0))

        for back in (True, False):
            side = -1 if back else 1
            hx = back_x if back else front_x
            lift = blift if back else flift
            swing = stride * 3.0 * side if action == "walk" else 0.0
            fx = hx + swing
            knee = (hx * 0.62 + fx * 0.38 + side * 1.2,
                    25.0 - lift * 0.45)
            foot = (fx, 44.0 - lift)
            hipc = (hx, NS.HIP_Y)
            shade = 0.55 if back else 1.0
            leg_col = p["leather_dark"] if back else p["leather_mid"]
            # paha -> lutut
            ctx.poly(leg_col, [(hipc[0] - 3.1, hipc[1]),
                               (hipc[0] + 3.1, hipc[1]),
                               (knee[0] + 2.5, knee[1]),
                               (knee[0] - 2.5, knee[1])],
                     ptg=True)
            # pelindung lutut (pelat baja kecil)
            ctx.poly(p["armor_mid"] if not back else p["armor_dark"],
                     [(knee[0] - 2.6, knee[1] - 2.2),
                      (knee[0] + 2.6, knee[1] - 2.2),
                      (knee[0] + 2.9, knee[1] + 1.4),
                      (knee[0] - 2.9, knee[1] + 1.4)], ptg=True)
            # shin -> buku kaki
            ctx.poly(leg_col, [(knee[0] - 2.4, knee[1] + 1.0),
                               (knee[0] + 2.4, knee[1] + 1.0),
                               (foot[0] + 2.1, foot[1] - 3.0),
                               (foot[0] - 2.1, foot[1] - 3.0)],
                     ptg=True)
            # sepatu bot + toe cap baja
            ctx.poly(p["leather_dark"] if back else p["leather_mid"],
                     [(foot[0] - 3.4, foot[1] - 3.2),
                      (foot[0] + 3.2 + (1.6 if not back else 0.6),
                       foot[1] - 2.6),
                      (foot[0] + 3.4 + (1.8 if not back else 0.6),
                       foot[1] - 0.2),
                      (foot[0] - 3.8, foot[1] - 0.2)], ptg=True)
            if not back:
                ctx.poly(p["armor_light"],
                         [(foot[0] + 2.6, foot[1] - 2.4),
                          (foot[0] + 4.9, foot[1] - 2.3),
                          (foot[0] + 5.2, foot[1] - 0.4),
                          (foot[0] + 2.4, foot[1] - 0.4)], ptg=True)
            # SOL: 1.6px lokal ≈ 2px layar, warna pekat OPAQUE (kontrak
            # test walk: minimal satu sol menapak penuh di garis tanah).
            ctx.poly_raw((26, 20, 34, 255),
                         [(ctx.ptg(foot[0] - 4.0, foot[1] - 0.2)[0],
                           ctx.ptg(0, foot[1] - 0.2)[1]),
                          (ctx.ptg(foot[0] + 5.2, foot[1] - 0.2)[0],
                           ctx.ptg(0, foot[1] - 0.2)[1]),
                          (ctx.ptg(foot[0] + 5.2, foot[1] + 1.15)[0],
                           ctx.ptg(0, foot[1] + 1.15)[1]),
                          (ctx.ptg(foot[0] - 4.0, foot[1] + 1.15)[0],
                           ctx.ptg(0, foot[1] + 1.15)[1])])
            if lift <= 0 and action != "attack":
                # tekanan tapak: garis contact 1px sedikit lebih lebar
                xg = ctx.ptg(foot[0], foot[1] + 1.9)
                NS._rect(ctx.surface, (0, 0, 0, 120),
                         (xg[0] - 5, xg[1], 11, 1))
            if detail and not back:
                ctx.tick(foot[0] + 1.2, foot[1] - 2.6,
                         (*p["brass_light"], 235))
                ctx.line((knee[0] - 1.8, knee[1] - 1.4),
                         (knee[0] + 1.8, knee[1] - 1.4),
                         (*p["armor_shine"], 200), 1)
            _ = shade

    # ------------------------------------------------------------------
    # BAGIAN 2 — torso: badan ork + pelat dada spellbreaker + permata
    # ------------------------------------------------------------------
    @staticmethod
    def _draw_gnk_torso(ctx, phase, action, ap, detail):
        NS = _NS_gornak
        p = ctx.p
        breath = math.sin(phase * 0.62)
        ward = action == "ward"
        void = action == "void"
        surge = action == "surge"
        # kulit di bawah zirah (leher ketas, pinggang menyempit)
        ctx.poly(p["skin_dark"], [(-11.6, -14.0), (11.6, -14.0),
                                  (9.6, 6.4), (-9.6, 6.4)])
        ctx.poly(p["skin_mid"], [(-11.0, -13.4), (10.6, -13.4),
                                 (8.8, 5.6), (-9.4, 5.6)], selout=False)
        # pelat dada utama (trapesium dada lebar — siluet "tank")
        plate = [(-13.6, -14.6 + breath * 0.35), (13.6, -14.6),
                 (10.4, 4.8), (-10.4, 4.8)]
        ctx.poly(p["armor_mid"], plate)
        # segmen bawah pelat lebih gelap (terminator autor)
        ctx.poly(p["armor_dark"], [(-11.9, -4.6), (11.9, -4.6),
                                   (10.4, 4.8), (-10.4, 4.8)],
                 selout=False)
        # garis sambungan tengah + garis pektoral (bidang terbelah
        # = pelat, bukan trapesium polos)
        ctx.line((0.8, -13.2), (1.6, 3.8), (*p["armor_darkest"], 235), 1)
        ctx.line((-8.6, -7.6), (-1.4, -5.8), (*p["armor_darkest"], 190), 1)
        ctx.line((3.0, -6.0), (9.6, -8.0), (*p["armor_darkest"], 190), 1)
        # highlight kiri-atas (key light) + terminator bawah
        ctx.poly(p["armor_light"], [(-13.0, -14.2), (-2.4, -14.2),
                                    (-3.0, -12.2), (-12.2, -12.4)],
                 selout=False)
        ctx.poly(p["armor_shine"], [(-12.2, -13.8), (-7.4, -13.8),
                                    (-7.8, -13.0), (-11.8, -13.0)],
                 selout=False)
        # kerah logam
        ctx.poly(p["armor_dark"], [(-7.6, -16.6), (7.6, -16.2),
                                   (6.0, -13.8), (-6.2, -14.0)],
                 selout=False)
        ctx.line((-5.6, -15.6), (5.2, -15.2), (*p["armor_light"], 220), 1)
        # ── PERMATA ANTI-MANA: berdenyut, menjerat cahaya saat Ward/Void
        gx, gy = 2.4, -9.6
        pulse = 0.5 + 0.5 * math.sin(phase * 1.24 + 0.6)
        gr = 2.3 + (0.7 if ward or void else 0.0)
        ctx.dot(gx, gy, gr + 1.5,
                (*p["magic_mid"], 90 + int(70 * (pulse if not ward and
                                                 not void else 1.0))))
        ctx.dot(gx, gy, gr, p["gem_mid"] if not (ward or void)
                else p["gem_hot"])
        ctx.dot(gx, gy, max(0.7, gr - 1.2), p["magic_shine"])
        ctx.tick(gx - 2, gy - 2, (*p["gem_dark"], 255))
        if ward or void:
            for i in range(3):
                a = phase * 1.5 + i * math.tau / 3
                rr = 5.2 + 1.6 * math.sin(phase * 2.2 + i * 2.1)
                ctx.line((gx + math.cos(a) * 2.6, gy + math.sin(a) * 2.6),
                         (gx + math.cos(a) * rr, gy + math.sin(a) * rr),
                         (*p["magic_hot"], 190), 1)
        # ── ikat pinggang kulit + gesper kuningan
        ctx.poly(p["leather_dark"], [(-10.8, 3.4), (10.8, 3.4),
                                     (10.2, 6.6), (-10.2, 6.6)])
        ctx.line((-10.0, 4.2), (9.8, 4.2), (*p["leather_light"], 200), 1)
        ctx.poly(p["brass_mid"], [(0.4, 3.6), (3.4, 3.6), (3.4, 6.4),
                                  (0.4, 6.4)], selout=False)
        ctx.poly(p["brass_light"], [(1.1, 4.2), (2.7, 4.2), (2.7, 5.7),
                                    (1.1, 5.7)], selout=False)
        if detail:
            # rivet pelat dada (bukan lingkaran — tick 1px kuningan)
            for rx, ry in ((-10.8, -12.0), (10.6, -12.4), (-9.0, 1.6),
                           (8.6, 1.4)):
                ctx.tick(rx, ry, p["brass_mid"])
            # jahitan ikat pinggang
            for sx in range(-8, 9, 3):
                ctx.tick(sx * 1.0 + 0.4, 5.6, (*p["bone_dark"], 210))
            # coreng perang pipi + parut alis sudah di head; di torso:
            # goresan pedang lama (1px terang, cerita, bukan noise)
            ctx.line((-7.4, -1.2), (-4.6, -3.4), (*p["armor_shine"], 150),
                     1)
            _ = surge
        _ = ap

    # ------------------------------------------------------------------
    # BAGIAN 3 — kilt perang: tiga panel, hem bergerak, sapuan kain
    # ------------------------------------------------------------------
    @staticmethod
    def _draw_gnk_kilt(ctx, phase, action, ap, detail):
        NS = _NS_gornak
        p = ctx.p
        if action == "attack":
            sway = math.sin(ap * math.pi) * 2.2
            flutter = 0.8
        elif action == "walk":
            sway = 0.0
            flutter = math.sin(phase * 1.72) * 1.6
        else:
            sway = 0.0
            flutter = math.sin(phase * 0.62 + 1.4) * 0.7
        # panel samping belakang (lebih gelap, di bawah paha)
        for side in (-1, 1):
            base = 9.2 * side
            hemx = base + 4.2 * side + sway * side * 1.4
            ctx.poly(p["robe_dark"],
                     [(base - 1.2, 6.6), (base + 4.6 * side, 6.8),
                      (hemx + 3.6 * side, 20.5 - (1 if side < 0 else 0)),
                      (hemx - 0.6, 21.6)], ptg=False)
        # panel depan tengah dengan hem bergerigi (robek)
        cx0 = 0.6 + sway * 0.6
        top = [(cx0 - 4.8, 6.2), (cx0 + 4.8, 6.2)]
        hem = []
        n = 4
        for i in range(n + 1):
            t = i / float(n)
            hx = cx0 - 5.6 + 11.2 * t
            hyy = 22.4 + 1.8 * math.sin(t * 5.2 + phase * 1.72) \
                + flutter * (1.4 if i % 2 else 0.2) - abs(sway) * 0.35
            hem.append((hx, hyy))
        ctx.poly(p["robe_mid"], [top[0], top[1], hem[-1], hem[0]])
        ctx.poly(p["robe_light"], [(cx0 - 4.4, 6.4), (cx0 - 1.4, 6.4),
                                   (cx0 - 2.2, 15.2), (cx0 - 5.2, 14.6)],
                 selout=False)
        # garis hem 1px (edge) + noda tanah 2px deterministik
        for i in range(n):
            ctx.line(hem[i], (hem[i][0] + 2.4, hem[i][1] - 0.6),
                     (*p["robe_edge"], 225), 1)
        if detail:
            NS._dither_dots(ctx.surface, p["robe_darkest"],
                            [ctx.pt(cx0 - 3.1, 18.2 + (i % 2) * 0.8),
                             ctx.pt(cx0 + 2.6, 19.4 - (i % 3) * 0.7),
                             ctx.pt(cx0 + 0.2, 12.2),
                             ctx.pt(cx0 - 3.8, 11.0),
                             ctx.pt(cx0 + 3.4, 15.8)]
                            , 90)
            # rantai pinggul (3 link 1px bone)
            for i in range(3):
                ctx.tick(7.4 + i * 1.5, 8.2 + i * 1.9 + flutter * 0.2,
                         p["bone_dark"])
                ctx.tick(7.5 + i * 1.5, 8.8 + i * 1.9 + flutter * 0.2,
                         p["bone_light"])
        # pelat paha (tassets)
        for side in (-1, 1):
            hx = 7.2 * side
            ctx.poly(p["armor_mid"] if side > 0 else p["armor_dark"],
                     [(hx - 2.4, 7.0), (hx + 2.6, 7.0),
                      (hx + 2.2, 12.6), (hx - 2.0, 12.2)], selout=True)
            ctx.line((hx - 2.2, 7.6), (hx + 2.3, 7.6),
                     (*p["armor_light"], 210), 1)

    # ------------------------------------------------------------------
    # BAGIAN 4 — pauldron tiga pelat + spike (kiri-atas kena cahaya)
    # ------------------------------------------------------------------
    @staticmethod
    def _draw_gnk_pauldrons(ctx, phase, action, ap, detail, back=False):
        NS = _NS_gornak
        p = ctx.p
        breath = math.sin(phase * 0.62) * 0.5
        sh = NS.SHOULDER_BACK if back else NS.SHOULDER_FRONT
        sx, sy = sh
        sy += int(breath)
        if action == "attack":
            # bahu naik mengikuti ayunan (rotasi shoulder guard)
            sy -= int(math.sin(ap * math.pi) * 1.6)
            sx += int(math.sin(ap * math.pi) * 1.4)
        n_plates = 2 if back else 3
        for i in range(n_plates):
            w = 5.6 - i * 0.7
            px = sx + (1.2 if not back else -1.2)
            py = sy - 2.2 + i * 2.55
            ctx.poly(p["armor_mid"] if not back else p["armor_dark"],
                     [(px - w, py), (px + w, py - 0.4),
                      (px + w * 0.9, py + 2.9), (px - w * 0.9, py + 3.1)])
            ctx.line((px - w * 0.92, py + 2.9), (px + w * 0.9, py + 2.6),
                     (*p["armor_darkest"], 215), 1)
            if not back:
                ctx.line((px - w * 0.8, py + 0.4), (px - w * 0.1, py + 0.2),
                         (*p["armor_shine"], 235), 1)
            if detail and i == 0:
                ctx.tick(px + w * 0.55, py + 1.1, p["brass_mid"])
                ctx.tick(px - w * 0.7, py + 1.4, p["brass_mid"])
        if not back:
            # spike spellbreaker: pelat pertama ditumbuk naik
            sp = [(sx + 3.6, sy - 3.0), (sx + 5.6, sy - 6.4),
                  (sx + 6.2, sy - 2.2)]
            ctx.poly(p["armor_light"], sp)
            ctx.poly_raw((*p["blade_shine"], 255),
                         [ctx.pt(sx + 5.6, sy - 6.4),
                          ctx.pt(sx + 4.9, sy - 4.6),
                          ctx.pt(sx + 5.5, sy - 4.4)])

    # ------------------------------------------------------------------
    # BAGIAN 5 — kepala ork: alis, taring, mata MENYALA, topknot
    # ------------------------------------------------------------------
    @staticmethod
    def _draw_gnk_head(ctx, phase, action, ap, detail):
        NS = _NS_gornak
        p = ctx.p
        hdx, hdy = NS._head_bob(action, phase, ap)
        # kedip DETERMINISTIK dari phase (bukan waktu nyata): cache sprite
        # lane hero mengkuantisasi phase -> kedip tidak pernah berkedip
        # acak yang tidak sinkron dengan pose.
        blink = ((phase * 0.62 + 2.1) % 5.4) < 0.16
        dying = action == "death"
        look = 1.0 if action in ("surge", "attack") else 0.0

        def H(lx, ly):
            return (lx + hdx, ly + hdy)

        jaw_d = 1.6 if dying else 0.0
        # leher
        ctx.poly(p["skin_dark"], [H(-2.6, -20.2), H(4.6, -19.8),
                                  H(4.2, -16.6), H(-3.0, -16.8)])
        # tengkorak + rahang bawah berat (underbite ork)
        ctx.poly(p["skin_mid"],
                 [H(-5.6, -27.6), H(-4.8, -32.6), H(2.6, -33.6),
                  H(6.6, -30.6), H(7.6, -25.4 + jaw_d),
                  H(5.6, -21.4 + jaw_d), H(-2.2, -21.6 + jaw_d),
                  H(-6.2, -24.6)])
        # terminator kanan-bawah + highlight kiri-atas
        ctx.poly(p["skin_dark"], [H(4.8, -30.6), H(7.0, -28.4),
                                  H(6.2, -22.6 + jaw_d), H(3.6, -22.4)],
                 selout=False)
        ctx.poly(p["skin_light"], [H(-5.4, -32.0), H(0.6, -33.0),
                                   H(1.0, -31.6), H(-4.8, -30.6)],
                 selout=False)
        # alis menukik (marah) — garis gelap tebal di atas mata
        ctx.poly(p["skin_darkest"], [H(-3.6, -30.4), H(2.2, -31.0),
                                     H(6.4, -29.0), H(6.0, -28.0),
                                     H(1.8, -29.4), H(-3.4, -29.0)],
                 selout=False)
        # telinga kecil di sisi jauh
        ctx.poly(p["skin_dark"], [H(-6.8, -28.6), H(-5.4, -29.6),
                                  H(-5.2, -25.8), H(-6.6, -25.2)],
                 selout=False)
        # moncong
        ctx.poly(p["skin_mid"], [H(2.6, -27.4), H(5.6, -26.6),
                                 H(5.2, -24.2), H(2.2, -24.4)],
                 selout=False)
        ctx.tick(*H(5.0, -25.6), p["skin_darkest"])
        # MULUT moncong + taring bawah
        ctx.line(H(1.8, -23.6 + jaw_d), H(5.4, -23.2 + jaw_d),
                 (*p["skin_darkest"], 240), 1)
        ctx.poly(p["bone_light"], [H(3.6, -23.4 + jaw_d), H(4.4, -23.4),
                                   H(4.1, -25.1 + jaw_d)], selout=False)
        ctx.poly(p["bone_dark"], [H(0.6, -23.2 + jaw_d), H(1.4, -23.2),
                                  H(1.0, -24.6 + jaw_d)], selout=False)
        # ── MATA: dua piksel TERANG di wajah (kontrak identitas; nilai
        # tertinggi sprite = eye_glow). Saat blink -> garis kelopak.
        e1, e2 = H(1.2, -28.6), H(4.0, -28.2)
        if blink or dying:
            ctx.line((e1[0] - 0.7, e1[1]), (e1[0] + 0.9, e1[1]),
                     (*p["eye_mid"], 235), 1)
            ctx.line((e2[0] - 0.9, e2[1]), (e2[0] + 0.9, e2[1]),
                     (*p["eye_mid"], 235), 1)
        else:
            ctx.tick(*e1, p["eye_light"])
            ctx.tick(*e2, p["eye_glow"])
            ctx.tick(e2[0] + 1.0, e2[1] - 0.4 + look * 0.2, p["eye_glow"])
            # glow 1px di sekeliling (bukan halo bulat)
            ctx.tick(e2[0] + 1.0, e2[1] + 0.8, (*p["magic_hot"], 170))
            ctx.tick(e1[0] - 0.8, e1[1] - 0.8, (*p["magic_hot"], 150))
        # ── topknot hitam-ungu (IDENTITAS keluarga; hair_light/_shine
        # WAJIB terlihat — palet ini dipakai juga oleh test tema warna).
        sway = math.sin(phase * 0.9) * 1.4 + (1.6 if action == "walk"
                                              else 0.0)
        root = H(-4.6, -33.2)
        tail = H(-7.4 - sway * 0.8, -37.2 - abs(sway) * 0.2)
        mid = H(-6.4 - sway * 0.5, -35.6)
        ctx.poly(p["hair_mid"],
                 [(root[0] - 2.6, root[1] + 0.8), (root[0] + 1.8, root[1]),
                  (mid[0] + 1.6, mid[1]), (tail[0] + 0.6, tail[1] - 0.8),
                  (tail[0] - 1.2, tail[1] + 1.4), (mid[0] - 1.8,
                                                    mid[1] + 2.2),
                  (root[0] - 3.6, root[1] + 3.0)], selout=True)
        ctx.line(root, tail, (*p["hair_shine"], 255), 1)
        ctx.tick(*tail, p["hair_shine"])
        # cukur samping: band gelap di belakang tengkorak
        ctx.line(H(-6.0, -31.6), H(-4.2, -23.8), (*p["hair_dark"], 225), 2)
        if detail:
            # coreng perang pipi (dedikasi portrait LOD; di arena jalur
            # lane sudah di-downscale, coreng ini hanya akan jadi noise)
            ctx.line(H(2.2, -26.2), H(4.6, -25.2), (*p["robe_light"],
                                                     190), 1)
            ctx.tick(*H(3.0, -25.8), (*p["robe_edge"], 200))
            # parut di dahi
            ctx.line(H(-2.6, -31.2), H(-0.6, -30.0), (*p["skin_darkest"],
                                                       200), 1)
            # ikat kepala kuningan di pangkal topknot
            ctx.line(H(-6.2, -32.4), H(-3.2, -33.0), (*p["brass_mid"],
                                                      255), 1)
            ctx.tick(*H(-5.0, -32.8), p["brass_light"])

    # ------------------------------------------------------------------
    # BAGIAN 6 — lengan dua-tulang (kulit + bracer baja)
    # ------------------------------------------------------------------
    @staticmethod
    def _draw_gnk_arm(ctx, phase, action, ap, back, detail):
        NS = _NS_gornak
        p = ctx.p
        sh = NS.SHOULDER_BACK if back else NS.SHOULDER_FRONT
        if action == "death":
            grip = ((-12.0, 6.0) if back else (12.0, 6.5))
            elbow = NS._elbow(sh, grip, 5.0 if back else -4.5)
        else:
            compact = detail
            grip = (NS._back_grip_local(action, ap, phase, compact)
                    if back else
                    NS._front_grip_local(action, ap, phase, compact))
            elbow, _ = NS._arm_chain(sh, grip, phase, action, ap, back)
        upper = p["skin_mid"] if not back else p["skin_dark"]
        fore = p["armor_dark"] if back else p["armor_mid"]
        # segmen atas (bahu -> siku)
        ctx.poly(upper, [(sh[0] - 3.0, sh[1] - 1.2), (sh[0] + 3.0, sh[1] -
                                                       1.6),
                         (elbow[0] + 2.3, elbow[1] - 0.6),
                         (elbow[0] - 2.3, elbow[1] + 0.4)], selout=True)
        # lengan bawah ber-bracer (siku -> grip)
        ctx.poly(fore, [(elbow[0] - 2.4, elbow[1] - 0.8),
                        (elbow[0] + 2.4, elbow[1] + 0.8),
                        (grip[0] + 2.0, grip[1] + 1.6),
                        (grip[0] - 2.0, grip[1] - 1.2)], selout=True)
        bracer_rim = p["armor_light"] if not back else p["armor_darkest"]
        ctx.line((elbow[0] - 2.0, elbow[1] + 0.2),
                 (grip[0] - 1.6, grip[1] - 0.6),
                 (*bracer_rim, 210), 1)
        # tangan mengepal di atas gagang
        ctx.dot(grip[0], grip[1], 2.1, p["skin_dark"] if back else
                p["skin_mid"])
        ctx.tick(grip[0] - 1.2, grip[1] - 1.2,
                 (*p["skin_light"], 235) if not back else
                 (*p["skin_darkest"], 220))
        _ = ap

    # ------------------------------------------------------------------
    # BAGIAN 7 — cleaver spellbreaker: 5 band + fuller bercahaya
    # ------------------------------------------------------------------
    @staticmethod
    def _draw_gnk_cleaver(ctx, phase, action, ap, back=False):
        NS = _NS_gornak
        p = ctx.p
        sh = NS.SHOULDER_BACK if back else NS.SHOULDER_FRONT
        if back:
            return                       # belati punya fungsi sendiri
        grip = NS._front_grip_local(action, ap, phase,
                                    compact=False)
        if action == "death":
            grip = (12.0, 6.5)
        _, angle = NS._arm_chain(sh, grip, phase, action, ap, False)
        L = NS._blade_len(action, False)
        dx, dy = math.sin(angle), math.cos(angle)
        nx, ny = -dy, dx                   # tegak lurus (sisi edge = +n)

        def bl(u, v):
            return (grip[0] + dx * u + nx * v, grip[1] + dy * u + ny * v)

        # gagang + pomel
        ctx.poly(p["leather_dark"],
                 [bl(-5.2, -1.5), bl(0.6, -1.5), bl(0.6, 1.5),
                  bl(-5.2, 1.5)], selout=False)
        ctx.dot(*bl(-5.6, 0.0), 1.15, p["brass_mid"])
        # crossguard baja
        ctx.poly(p["armor_mid"], [bl(0.4, -3.0), bl(1.6, -2.4),
                                  bl(1.6, 3.2), bl(0.4, 3.8)],
                 selout=True)
        # bilah: belly melebar di 2/3 lalu menumpuk ke ujung (khas cleaver)
        ctx.poly(p["blade_mid"],
                 [bl(1.6, -2.0), bl(L * 0.45, -2.8), bl(L * 0.8, -1.6),
                  bl(L, 0.8), bl(L * 0.78, 4.4), bl(L * 0.35, 4.0),
                  bl(1.6, 2.6)], selout=True)
        # edge bevel 1.2px (berkilau) sepanjang sisi tajam
        ctx.poly(p["blade_light"],
                 [bl(2.0, 1.9), bl(L * 0.5, 3.1), bl(L * 0.8, 3.5),
                  bl(L * 0.98, 0.9), bl(L * 0.8, 2.2), bl(L * 0.5, 1.8),
                  bl(2.0, 0.9)], selout=False)
        ctx.poly(p["blade_shine"], [bl(6.0, 2.9), bl(L * 0.66, 3.7),
                                    bl(L * 0.8, 3.15), bl(6.4, 2.35)],
                 selout=False)
        # punggung gelap + spike pemutus mantra di pangkal bilah
        ctx.line(bl(2.2, -1.9), bl(L * 0.72, -1.5),
                 (*p["blade_darkest"], 235), 1)
        ctx.poly(p["armor_light"], [bl(3.4, -2.2), bl(6.6, -5.4),
                                     bl(8.4, -2.0)], selout=True)
        ctx.poly(p["blade_darkest"], [bl(2.4, -2.1), bl(9.2, -2.6),
                                      bl(9.2, -1.7), bl(2.4, -1.2)],
                 selout=False)
        # ── fuller: alur rune yang MENYALA saat Ward/Void/Surge
        glow = {"ward": 0.85, "void": 1.0, "surge": 0.75}.get(action, 0.0)
        idle_pulse = 0.16 + 0.1 * math.sin(phase * 1.1)
        a = int(255 * min(1.0, idle_pulse + glow))
        if a > 26:
            col = p["magic_light"] if glow == 0 else p["magic_hot"]
            ctx.line(bl(4.4, 0.1), bl(L * 0.74, 0.5), (*col, a), 1)
            for i in range(4):
                t = 0.16 + 0.16 * i
                ctx.tick(*bl(L * t, 0.35), (*p["magic_shine"], a))
        # specular ujung 1px + kilat saat impact-hold (bintang, bukan blur)
        ctx.tick(*bl(L - 2.4, 1.4), p["blade_shine"])
        if action == "attack" and 0.44 <= ap <= 0.62:
            tipx, tipy = ctx.pt(*bl(L, 0.6))
            k = 1.0 - abs(ap - 0.53) / 0.09
            NS._spark_star(ctx.surface, tipx, tipy,
                           NS._s(3.4 + 3.2 * k), p["magic_hot"],
                           NS._alpha(230 * k), spikes=6, rot=phase * 0.4,
                           core=p["magic_core"])
        if back:
            return
        _ = ap

    # ------------------------------------------------------------------
    # BAGIAN 8 — belati reverse-grip (penyeimbang, bukan karakter kedua)
    # ------------------------------------------------------------------
    @staticmethod
    def _draw_gnk_dagger(ctx, phase, action, ap, detail):
        NS = _NS_gornak
        p = ctx.p
        sh = NS.SHOULDER_BACK
        if action == "death":
            grip = (-12.0, 6.0)
            angle = -0.35
        else:
            grip = NS._back_grip_local(action, ap, phase, compact=detail)
            _, angle = NS._arm_chain(sh, grip, phase, action, ap, True)
        L = NS._blade_len(action, True)
        dx, dy = math.sin(angle), math.cos(angle)
        nx, ny = -dy, dx

        def bl(u, v):
            return (grip[0] + dx * u + nx * v, grip[1] + dy * u + ny * v)

        # reverse-grip: gagang DI UJUNG dalam, bilah keluar dari genggaman
        ctx.poly(p["leather_dark"], [bl(-3.0, -1.2), bl(1.2, -1.2),
                                     bl(1.2, 1.2), bl(-3.0, 1.2)],
                 selout=False)
        ctx.dot(*bl(-3.4, 0.0), 0.95, p["brass_dark"])
        ctx.poly(p["armor_mid"], [bl(1.0, -1.9), bl(1.8, -1.5),
                                  bl(1.8, 1.9), bl(1.0, 2.2)],
                 selout=False)
        ctx.poly(p["blade_light"], [bl(2.0, -1.1), bl(L * 0.7, -1.5),
                                    bl(L, 0.4), bl(L * 0.66, 2.0),
                                    bl(2.0, 1.4)], selout=True)
        ctx.line(bl(2.6, 1.15), bl(L * 0.86, 1.0), (*p["blade_shine"], 235),
                 1)
        ctx.line(bl(2.2, -0.9), bl(L * 0.6, -1.15),
                 (*p["blade_darkest"], 215), 1)
        if detail:
            ctx.tick(*bl(L * 0.3, 0.2), (*p["magic_light"], 200))
        _ = ap

    # ------------------------------------------------------------------
    # BAGIAN 9 — rim light ungu dingin (sisi bayangan) + specular
    # ------------------------------------------------------------------
    @staticmethod
    def _draw_gnk_rimlight(ctx, phase, action, ap, detail):
        NS = _NS_gornak
        p = ctx.p
        ward = action in ("ward", "void")
        base = 120 if ward else 66
        hdx, hdy = NS._head_bob(action, phase, ap)
        pulse = int(18 * math.sin(phase * 1.24))
        a = NS._alpha(base + pulse + (26 if ward else 0))
        # garis rim sepanjang sisi kanan-bawah kepala/pundak/pelat
        ctx.line((6.9 + hdx, -30.2 + hdy), (7.8 + hdx, -24.6 + hdy),
                 (*p["magic_light"], a), 1)
        ctx.line((16.2, -15.4), (18.4, -12.2), (*p["magic_light"], a), 1)
        ctx.line((12.8, 1.2), (10.0, 4.4), (*p["magic_light"],
                                            NS._alpha(base * 0.8 + pulse)),
                 1)
        ctx.line((-12.2, -3.4), (-11.0, 2.2), (*p["magic_light"],
                                                NS._alpha(base * 0.7)), 1)
        ctx.line((8.4, 21.8), (5.2, 22.8), (*p["magic_dark"],
                                             NS._alpha(base * 0.9)), 1)
        if ward:
            # cincin rim badan saat Ward/Void: 4 tick di kontur bahu
            for i in range(4):
                t = phase * 1.5 + i * 1.57
                ctx.tick(10.6 * math.cos(t) + 2.0,
                         -8 + 3.2 * math.sin(t),
                         (*p["magic_hot"], NS._alpha(150 + pulse)))
        if detail and not ward:
            ctx.tick(-3.4, -31.6 + hdy, (*p["magic_shine"], 150))
        _ = ap

    # ------------------------------------------------------------------
    # BAGIAN 10 — micro-detail khusus portrait (LOD Hero Shop)
    # ------------------------------------------------------------------
    @staticmethod
    def _draw_gnk_details(ctx, phase, action, ap):
        NS = _NS_gornak
        p = ctx.p
        # panel tekstur pelat: tiga gores 1px, bukan dither noise
        ctx.line((-6.8, -9.6), (-4.2, -8.8), (*p["armor_light"], 150), 1)
        ctx.line((-6.6, -7.2), (-4.4, -6.6), (*p["armor_light"], 120), 1)
        ctx.line((5.6, -2.8), (8.2, -3.6), (*p["armor_shine"], 130), 1)
        # gesper: diagonal highlight
        ctx.tick(1.4, 4.6, p["brass_light"])
        # serpihan ukiran pada pelat paha
        for side in (-1, 1):
            hx = 7.2 * side
            ctx.tick(hx - 1.1, 9.6, (*p["armor_shine"], 175))
            ctx.tick(hx + 0.4, 11.2, (*p["armor_light"], 150))
        # goresan ukiran pada gagang cleaver
        ctx.line((-4.4, -0.9), (-1.6, -0.6), (*p["leather_light"], 190), 1)
        ctx.tick(-3.2, 0.6, (*p["brass_mid"], 235))
        _ = phase, action, ap

    # ------------------------------------------------------------------
    # ASSEMBLY — urutan lapisan belakang -> depan
    # ------------------------------------------------------------------
    @staticmethod
    def _draw_gnk_rig(surface, cx, cy, facing, phase, action, ap=0.0,
                      detail=False):
        """Gambar SELURUH badan satu pose ke surface apa pun.

        Ini satu-satunya tempat bagian-bagian dirakit; ``draw_gornak``,
        cache lane hero, portrait Hero Shop, dan tool audit semuanya
        memanggil fungsi yang sama -> mustahil hasilnya berbeda jalur.
        """
        NS = _NS_gornak
        ctx = NS._make_ctx(surface, cx, cy, facing, phase, action, ap)
        NS._draw_gnk_legs(ctx, phase, action, ap, detail)
        NS._draw_gnk_scarf(ctx, phase, action)
        NS._draw_gnk_arm(ctx, phase, action, ap, back=True, detail=detail)
        NS._draw_gnk_dagger(ctx, phase, action, ap, detail)
        NS._draw_gnk_pauldrons(ctx, phase, action, ap, detail, back=True)
        NS._draw_gnk_torso(ctx, phase, action, ap, detail)
        NS._draw_gnk_kilt(ctx, phase, action, ap, detail)
        NS._draw_gnk_head(ctx, phase, action, ap, detail)
        NS._draw_gnk_pauldrons(ctx, phase, action, ap, detail, back=False)
        NS._draw_gnk_arm(ctx, phase, action, ap, back=False, detail=detail)
        NS._draw_gnk_cleaver(ctx, phase, action, ap)
        NS._draw_gnk_rimlight(ctx, phase, action, ap, detail)
        if detail:
            NS._draw_gnk_details(ctx, phase, action, ap)
        return ctx

    # ------------------------------------------------------------------
    # BAGIAN 11 — syal robek (EQUIPMENT layer): inersia sederhana,
    # mengikuti phase + arah; membuktikan badan punya massa.
    # ------------------------------------------------------------------
    @staticmethod
    def _draw_gnk_scarf(ctx, phase, action):
        NS = _NS_gornak
        p = ctx.p
        if action == "walk":
            wave = math.sin(phase * 1.72) * 2.2
            lift = 0.8
        elif action == "attack":
            wave = -3.0
            lift = -1.4
        elif action in ("ward", "void"):
            wave = math.sin(phase * 2.4) * 1.4
            lift = -2.2
        else:
            wave = math.sin(phase * 0.62 + 2.0) * 1.2
            lift = 0.0
        neck = (-2.2, -19.4)
        mid1 = (neck[0] - 3.4 - lift * 0.3, neck[1] + 2.6 + wave * 0.4)
        mid2 = (neck[0] - 7.6 - lift * 0.4, neck[1] + 5.4 + wave * 0.85)
        tail = (neck[0] - 10.4, neck[1] + 9.6 + wave * 1.15)
        # dua pita tipis (ramp 2 nilai) dengan ujung sobek segitiga
        ctx.poly(p["robe_mid"],
                 [(neck[0], neck[1] - 1.0), (neck[0] + 2.2, neck[1] -
                                              0.2),
                  (mid2[0] + 1.6, mid2[1] - 0.6), (mid2[0] - 0.6,
                                                   mid2[1] + 0.9)],
                 selout=False)
        ctx.poly(p["robe_dark"],
                 [(mid1[0], mid1[1] - 0.4), (mid2[0] + 1.1, mid2[1] -
                                             0.8),
                  (tail[0] + 1.9, tail[1] - 0.8), (tail[0] + 0.4,
                                                    tail[1] + 1.6),
                  (tail[0] - 1.5, tail[1] + 0.2), (mid2[0] - 1.0,
                                                   mid2[1] + 1.4)],
                 selout=False)
        ctx.line(mid1, tail, (*p["robe_edge"], 190), 1)

    # ==================================================================
    # API MODULAR v5 — layer terpisah sesuai master prompt.
    # Masing-masing bisa dipakai sendiri oleh tool/layersheet; semua
    # delegasi ke fungsi bagian yang SAMA dengan rig utuh, jadi tidak
    # pernah ada dua sumber bentuk.
    # ==================================================================
    def render_idle(surface, cx, cy, facing, phase, detail=False):
        """Pose IDLE: napas + kedip + denyut permata (semua phase-driven)."""
        return _NS_gornak._draw_gnk_rig(surface, cx, cy, facing, phase,
                                        "idle", 0.0, detail)

    def render_attack(surface, cx, cy, facing, phase, ap, detail=False):
        """Pose ATTACK pada waktu-pose ``ap`` (keluaran _attack_curve)."""
        return _NS_gornak._draw_gnk_rig(surface, cx, cy, facing, phase,
                                        "attack", ap, detail)

    def render_walk(surface, cx, cy, facing, phase, detail=False):
        return _NS_gornak._draw_gnk_rig(surface, cx, cy, facing, phase,
                                        "walk", 0.0, detail)

    def render_body(surface, cx, cy, facing, phase, action, ap=0.0,
                    detail=False):
        """TORSO layer saja (kulit + pelat dada + kerah)."""
        ctx = _NS_gornak._make_ctx(surface, cx, cy, facing, phase, action,
                                   ap)
        _NS_gornak._draw_gnk_torso(ctx, phase, action, ap, detail)
        return ctx

    def render_head(surface, cx, cy, facing, phase, action, ap=0.0,
                    detail=False):
        """HEAD layer: wajah, alis, mata menyala, topknot."""
        ctx = _NS_gornak._make_ctx(surface, cx, cy, facing, phase, action,
                                   ap)
        _NS_gornak._draw_gnk_head(ctx, phase, action, ap, detail)
        return ctx

    render_face = render_head

    def render_weapon(surface, cx, cy, facing, phase, action, ap=0.0,
                      detail=False):
        """WEAPON layer: cleaver depan + belati belakang (satu bahasa)."""
        ctx = _NS_gornak._make_ctx(surface, cx, cy, facing, phase, action,
                                   ap)
        _NS_gornak._draw_gnk_dagger(ctx, phase, action, ap, detail)
        _NS_gornak._draw_gnk_cleaver(ctx, phase, action, ap)
        return ctx

    def render_equipment(surface, cx, cy, facing, phase, action, ap=0.0,
                         detail=False):
        """EQUIPMENT layer: ikat pinggang, kilt, tassets, syal, pauldron."""
        ctx = _NS_gornak._make_ctx(surface, cx, cy, facing, phase, action,
                                   ap)
        _NS_gornak._draw_gnk_scarf(ctx, phase, action)
        _NS_gornak._draw_gnk_kilt(ctx, phase, action, ap, detail)
        _NS_gornak._draw_gnk_pauldrons(ctx, phase, action, ap, detail,
                                       back=True)
        _NS_gornak._draw_gnk_pauldrons(ctx, phase, action, ap, detail,
                                       back=False)
        return ctx

    def render_highlight(surface, cx, cy, facing, phase, action, ap=0.0,
                        detail=False):
        """HIGHLIGHT layer: rim ungu dingin + specular pelat/bilah."""
        ctx = _NS_gornak._make_ctx(surface, cx, cy, facing, phase, action,
                                   ap)
        _NS_gornak._draw_gnk_rimlight(ctx, phase, action, ap, detail)
        if detail:
            _NS_gornak._draw_gnk_details(ctx, phase, action, ap)
        return ctx

    def render_outline(surface, cx, cy, facing, phase, action, ap=0.0,
                       detail=False):
        """OUTLINE layer: salinan gelap 1px sisi bayangan saja (selout)."""
        NS = _NS_gornak
        buf = NS._rig_surface()
        NS._draw_gnk_rig(buf, NS.RIG_OX, NS.RIG_OY, facing, phase, action,
                         ap, detail)
        edge = buf.copy()
        edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
        buf.fill((0, 0, 0, 0))
        sx = 1 if facing >= 0 else -1
        for dx, dy in ((sx, 0), (0, 1), (sx, 1)):
            buf.blit(edge, (dx, dy))
        NS._rig_release(edge)
        NS._rig_release(buf)
        surface.blit(buf, (int(cx) - NS.RIG_OX, int(cy) - NS.RIG_OY))
        return buf

    def render_hit_flash(surface, cx, cy, facing, phase, action, ap, t,
                         detail=False):
        """HIT FLASH: siluet MAX-fill putih hangat, alpha = t*185.

        Hanya SATU lapisan — tidak menutupi bentuk, tidak memutihkan
        penuh; dipadukan dengan screen-shake dan hit-stop oleh feel bus.
        """
        NS = _NS_gornak
        buf = NS._rig_surface()
        NS._draw_gnk_rig(buf, NS.RIG_OX, NS.RIG_OY, facing, phase, action,
                         ap, detail)
        lit = buf.copy()
        lit.fill((255, 246, 235, 0), special_flags=pygame.BLEND_RGBA_MAX)
        lit.set_alpha(NS._alpha(185 * max(0.0, min(1.0, t))))
        ox, oy = int(cx) - NS.RIG_OX, int(cy) - NS.RIG_OY
        surface.blit(lit, (ox, oy))
        NS._rig_release(lit)
        NS._rig_release(buf)
        return buf

    def render_shadow(surface, x, ground_y):
        """KONTAK BAYANGAN: dua ellips (pool lembut + inti kontak).

        Static surface (di-cache) — blit per frame, nol alokasi.
        """
        NS = _NS_gornak

        def build():
            w, h = 78, 14
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            NS._ellipse(s, (0, 0, 0, 78), (3, 2, w - 6, h - 4))
            NS._ellipse(s, (0, 0, 0, 118), (10, 4, w - 20, h - 7))
            NS._ellipse(s, (4, 2, 8, 168), (w // 2 - 12, h // 2 - 3, 24,
                                            6))
            return s

        spr = NS._static("shadow_v5", build)
        surface.blit(spr, (int(x) - spr.get_width() // 2,
                           int(ground_y) - spr.get_height() // 2))
        return spr

    def render_aura(surface, boss, x, y, phase, action, skill):
        """ANTI-MAGIC FIELD di bawah badan + lapisan SPAWN/DEATH ground.

        Satu fungsi untuk "aura lantai" supaya ground pass hanya punya
        satu titik masuk (mudah diaudit, mudah dimatikan saat portrait).
        """
        NS = _NS_gornak
        NS._draw_anti_magic_field(surface, x, y, phase, skill)
        sp = float(getattr(boss, "_gnk_spawn_t", 0.0) or 0.0)
        if 0.0 < sp < NS.SPAWN_TIME - 1e-9:
            NS._draw_spawn_ring(surface, x, y, sp / NS.SPAWN_TIME, phase)
        dth = float(getattr(boss, "_gnk_death_t", 0.0) or 0.0)
        if dth > 0.0:
            NS._draw_death_ground(surface, x, y, dth / NS.DEATH_TIME, phase)

    @staticmethod
    def _draw_spawn_ring(surface, x, y, k, phase):
        """Void ring yang MENUTUP saat Gornak bangkit dari tanah.

        Semua geometri DIJAGA tetap di dalam bbox badan (radius ≤ 30,
        serpihan tidak pernah menyentuh bawah garis tanah) — ukuran
        karakter yang diukur pipeline (tools/test_gornak_masterwork.py
        keluarga hero, _measure_native_size) tidak boleh terinflasi oleh
        efek spawn.
        """
        NS = _NS_gornak
        p = NS.PALETTE
        gy = y + NS.GROUND_DY
        a = NS._alpha(190 * (0.25 + 0.75 * k))
        r = int(10 + 19 * k)
        NS._ellipse(surface, (*p["magic_mid"], a),
                    (x - r, gy - r // 3, r * 2, max(4, r // 2)), 2)
        for i in range(6):
            ang = i * math.tau / 6 + phase * 0.4
            rr = r * (0.62 + 0.30 * k)
            NS._shard(surface, x + math.cos(ang) * rr,
                      gy - 3 - abs(math.sin(ang)) * rr * 0.45 - 8.0 * (1 - k),
                      -math.pi / 2 + math.sin(i * 2.4) * 0.4,
                      int(3 + 3 * k), 1, p["magic_light"],
                      NS._alpha(210 * k), core=p["magic_shine"])
        NS._spark_star(surface, x, gy - 3, 5 + int(4 * k), p["magic_hot"],
                       a, spikes=6, rot=phase * 0.3, core=p["magic_core"])

    @staticmethod
    def _draw_death_ground(surface, x, y, k, phase):
        """Lingkaran rune PECAH yang menyebar saat badan rubuh."""
        NS = _NS_gornak
        p = NS.PALETTE
        gy = y + NS.GROUND_DY
        a = NS._alpha(190 * (1 - k))
        if a <= 0:
            return
        r = int(16 + 46 * k)
        NS._dashed_ring(surface, x, gy, r, p["magic_mid"], a, phase * 0.3,
                        segments=8, thick=2, span=0.5, squash=0.34)
        for i in range(5):
            hh = NS._hash01(i * 9.7)
            ang = i * math.tau / 5 + phase * 0.2
            NS._jagged_crack(surface, x + math.cos(ang) * 12,
                             gy + math.sin(ang) * 4, ang, 10 + 26 * k,
                             (p["magic_mid"], p["magic_hot"]), a, i,
                             width=1, segs=2)
            _ = hh

    #: Alias nama kontrak lama untuk bayangan kontak (dipakai jalur blink,
    #: tools audit, dan konsumen eksternal yang mengimpor _NS_gornak).
    def _draw_shadow(surface, x, ground_y):
        _NS_gornak.render_shadow(surface, x, ground_y)

    @staticmethod
    def render_status_overlay(surface, boss, x, y, phase):
        """STATUS layer: burn (bara), slow (bunga es), stun (bintang).

        Murni VISUAL — membaca flag status yang ada kalau engine
        mengirimnya; karakter tanpa status tidak menggambar apa pun.
        """
        NS = _NS_gornak
        p = NS.PALETTE
        burn = max(0.0, float(getattr(boss, "burn_timer", 0) or
                              getattr(boss, "status_burn", 0) or 0.0))
        slow = max(0.0, float(getattr(boss, "slow_timer", 0) or
                              getattr(boss, "status_slow", 0) or 0.0))
        stun = max(0.0, float(getattr(boss, "stun_timer", 0) or
                              getattr(boss, "status_stun", 0) or 0.0))
        if burn > 0:
            for i in range(5):
                t = (phase * 1.35 + i * 0.2) % 1.0
                fx = x + int((NS._hash01(i * 3.1) - 0.5) * 34)
                fy = y - int(6 + t * 44)
                a = NS._alpha(215 * (1 - t) * min(1.0, 0.4 + burn))
                NS._aaline(surface, (255, 158, 54, a), (fx, fy),
                           (fx + 1, fy - 3), 1)
                NS._rect(surface, (255, 214, 120, a), (fx, fy - 1, 1, 1))
        if slow > 0:
            for i in range(6):
                ang = phase * 0.5 + i * math.tau / 6
                r = 16 + 4.5 * math.sin(phase + i * 1.7)
                fx = x + int(math.cos(ang) * r * 1.3)
                fy = y - 10 + int(math.sin(ang) * r * 0.55)
                a = NS._alpha(120 + 60 * math.sin(phase * 2 + i))
                NS._rect(surface, (158, 212, 246, a), (fx, fy, 2, 1))
                NS._rect(surface, (158, 212, 246, a), (fx, fy, 1, 2))
        if stun > 0:
            for i in range(3):
                ang = phase * 2.1 + i * math.tau / 3
                sx2 = x + math.cos(ang) * 15
                sy2 = y - int(52) + math.sin(ang) * 4.0
                NS._spark_star(surface, sx2, sy2, 4, (255, 224, 120),
                               NS._alpha(210 * min(1.0, 0.3 + stun)),
                               spikes=4, rot=phase * 1.4,
                               core=(255, 250, 220))

    @staticmethod
    def render_death(surface, boss, x, y, facing, phase, action, ap,
                     detail=False):
        """DEATH layer: tubuh rubuh TERSUSUN (sink+fade di rig_at) +
        serpihan rune yang MENGUAP ke atas (deterministik phase).

        Tidak menghidupkan/mematikan apa pun — hanya menggambar apa yang
        sudah diputuskan gameplay.
        """
        NS = _NS_gornak
        d = float(getattr(boss, "_gnk_death_t", 0.0) or 0.0)
        if d <= 0.0:
            return
        p = NS.PALETTE
        k = min(1.0, d / NS.DEATH_TIME)
        a = NS._alpha(230 * (1 - k) ** 1.3)
        if a <= 0:
            return
        for i in range(9):
            hh = NS._hash01(i * 5.3 + 1.7)
            rise = d * (26.0 + 40.0 * hh)
            px = x + int((hh - 0.5) * 44) + int(math.sin(i * 2.2) * 6)
            py = y - int(rise) + 6
            NS._shard(surface, px, py,
                      -math.pi / 2 + (NS._hash01(i * 1.3) - 0.5) * 1.2,
                      max(2, int((5 - 3 * k) + 2 * hh)), 2,
                      p["magic_light"], a, core=p["magic_shine"])
        # cincin terakhir saat tubuh menyentuh tanah
        if 0.42 <= k <= 0.78:
            kk = (k - 0.42) / 0.36
            NS._ellipse(surface, (*p["magic_hot"], NS._alpha(190 *
                                                              (1 - kk))),
                        (x - int(20 + 40 * kk),
                         y + NS.GROUND_DY - int(7 + 12 * kk),
                         int(40 + 80 * kk), int(14 + 24 * kk)), 2)

    # ==================================================================
    # FX LAUTAN — shadow / field / rune (semua soft-alpha; portrait
    # mematikan semuanya lewat draw_gornak)
    # ==================================================================
    @staticmethod
    def _draw_anti_magic_field(surface, x, y, phase, skill):
        """Pendar anti-mana: kubah lembut + genangan di bawah kaki.

        Warna MURNI magic_* (bukan campuran kulit) supaya area soft-alpha
        yang besar tidak menodai ramp badan di mata. Saat Ward/Void
        field naik — visual "perisai menyala" tanpa perlu efek baru.
        """
        NS = _NS_gornak
        p = NS.PALETTE

        def build():
            w = h = 124
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            c = w // 2
            for r in range(48, 8, -4):
                t = (48 - r) / 40.0
                a = int(34 + 66 * t)
                col = p["magic_mid"] if t > 0.72 else p["magic_dark"]
                NS._aacircle(s, (*col, a), (c, c), r, width=4)
            NS._ellipse(s, (*p["magic_mid"], 96), (c - 12, c + 20, 24, 8))
            return s

        glow = NS._static("field_v5", build)
        ward = skill in ("e", "r")
        glow.set_alpha(NS._alpha(118 if ward else 76
                                 + int(16 * math.sin(phase * 0.62))))
        surface.blit(glow, (int(x) - 62, int(y) - 58))
        glow.set_alpha(255)
        # cincin kontak: dua busur tipis berputar berlawanan (RUNE hidup)
        NS._dashed_ring(surface, x, y + 4, 40, p["magic_mid"],
                        NS._alpha(92 + (26 if ward else 0)),
                        phase * 0.35, segments=7, thick=1, span=0.55,
                        squash=0.26)
        NS._dashed_ring(surface, x, y + 12, 26, p["magic_dark"],
                        NS._alpha(84), -phase * 0.5, segments=5, thick=1,
                        span=0.6, squash=0.30)

    @staticmethod
    def _draw_ground_rune(surface, x, y, phase, skill):
        """Cincin rune tanah — penanda "di sini mana mengalir"."""
        NS = _NS_gornak
        p = NS.PALETTE
        gy = y + NS.GROUND_DY
        pulse = 0.5 + 0.5 * math.sin(phase * 0.8 + (0.8 if skill else 0.0))
        NS._dashed_ring(surface, x, gy, 30, p["magic_dark"],
                        NS._alpha(48 + 26 * pulse), phase * 0.24,
                        segments=10, thick=2, span=0.52, squash=0.34)
        for i in range(3):
            ang = phase * 0.24 + (i + 0.5) * math.tau / 3
            NS._chevron(surface, x + math.cos(ang) * 25,
                        gy + math.sin(ang) * 8, ang, 3.5,
                        p["magic_mid"], NS._alpha(60 + 40 * pulse), 1)

    @staticmethod
    def _draw_footfall_dust(surface, x, y, facing, phase):
        """Debu langkah HANYA saat telapak menekan tanah.

        phase pi/2 (kaki melayang penuh) TIDAK menggambar apa pun — test
        lock ini membuktikan debu terikat SOL, bukan timer global.
        """
        NS = _NS_gornak
        p = NS.PALETTE
        contact = abs(math.sin(phase * 1.15))
        if contact > 0.72:
            return
        k = 1.0 - contact / 0.72
        f = 1 if facing >= 0 else -1
        gy = y + NS.GROUND_DY
        for i in range(2):
            side = 1 if i == 0 else -1
            dx = (10.5 + 2.5 * k) * f * (0.7 + 0.3 * side)
            a = NS._alpha(128 * k)
            if a <= 0:
                continue
            NS._ellipse(surface, (*p["leather_light"], a),
                        (x + dx - 5 - 4 * k, gy - 4 - int(2.5 * k * side),
                         9 + int(8 * k), 4 + int(3 * k)))
            NS._ellipse(surface, (*p["robe_edge"], a // 2),
                        (x + dx - 2, gy - 3 - int(4 * k), 5, 2))

    @staticmethod
    def _draw_crescent_slash(surface, x, y, facing, phase, ap):
        """Pita tebasan CANVAS (fallback saat lapisan hidup tidak aktif).

        Geometri = busur UJUNG BILAH sungguhan: di-sample dari
        _tip_local pada beberapa waktu pose, jadi sabit selalu mendarat
        tepat di bilah (bukan lingkaran dekorasi).
        """
        NS = _NS_gornak
        p = NS.PALETTE
        w, h = NS._SWING_WIND, NS._SWING_HIT
        if not (w - 0.06 <= ap <= 0.66):
            return
        f = 1 if facing >= 0 else -1
        fade = math.sin(math.pi * max(0.0, min(1.0,
                             (ap - (w - 0.06)) / (0.66 - w + 0.06)))) ** 0.7
        pts = []
        n = 9
        lo = max(0.0, min(ap - 0.16, w))
        lean, root_y = NS._rig_shift("attack", phase, ap)
        for j in range(n):
            aj = lo + (ap - lo) * j / float(n - 1)
            tip = NS._tip_local("attack", phase, aj)
            pts.append(NS._local_to_screen(x, y, f, lean, root_y,
                                           tip[0], tip[1]))
        widths = [max(1, int(NS.SCALE * (0.8 + 5.4 * (j / float(n - 1)))))
                  for j in range(n)]
        # tiga lapis: halo ungu -> bilah -> inti cahaya
        NS._ribbon(surface, [(px + f, py + 1) for px, py in pts],
                   [int(wd * 1.45) for wd in widths], p["magic_mid"],
                   NS._alpha(150 * fade))
        NS._ribbon(surface, pts, widths, p["blade_light"],
                   NS._alpha(205 * fade))
        NS._ribbon(surface, [(px, py - 1) for px, py in pts],
                   [max(1, wd // 3) for wd in widths], p["magic_shine"],
                   NS._alpha(235 * fade))
        tipx, tipy = pts[-1]
        if 0.42 <= ap <= 0.60:
            k = max(0.0, 1.0 - abs(ap - 0.51) / 0.09)
            NS._spark_star(surface, tipx, tipy,
                           NS._s(3.0 + 3.4 * k), p["magic_hot"],
                           NS._alpha(235 * k), spikes=6,
                           rot=phase * 0.4, core=p["magic_core"])
            NS._ellipse(surface, (*p["magic_mid"], NS._alpha(120 * k)),
                        (x - int(24 * (0.5 + k)), y + NS.GROUND_DY - 6,
                         int(48 * (0.5 + k)), 8), 1)

    # ==================================================================
    # SKILL FALLBACK (canvas) — dipakai HANYA kalau heroes/gornak_fx
    # tidak tersedia. Cincin E/R TETAP digambar renderer (kontrak
    # telegraph dunia), sisanya diambil alih lapisan hidup.
    # ==================================================================
    @staticmethod
    def _draw_manabreak_ground(surface, boss, x, y, timer, phase):
        """Q telegraph: mana TERKONDENSASI di ujung cleaver.

        Ujung bilah = titik spawn proyektil — jadi pemain membaca
        "proc lahir DI SANA" bahkan sebelum bolt-nya keluar.
        """
        NS = _NS_gornak
        p = NS.PALETTE
        if timer <= 0:
            return
        progress = NS._skill_progress(boss, "q")
        tx, ty = NS._tip_screen(boss, x, y)
        pulse = 0.5 + 0.5 * math.sin(phase * 2.2)
        a_core = NS._alpha(150 + 105 * progress)
        NS._aacircle(surface, (*p["magic_mid"],
                               NS._alpha(120 + 60 * pulse)),
                     (tx, ty), NS._s(6.5 - 3.0 * progress))
        NS._aacircle(surface, (*p["magic_hot"], a_core), (tx, ty),
                     NS._s(3.6 - 1.2 * progress))
        NS._aacircle(surface, (*p["magic_shine"], 235), (tx, ty),
                     NS._s(1.7))
        NS._aacircle(surface, (*p["magic_core"], 255), (tx, ty), 1)
        for i in range(3):
            ang = phase * 2.4 + i * math.tau / 3
            rr = (11.5 - 8.0 * progress) * NS.SCALE
            NS._shard(surface, tx + math.cos(ang) * rr,
                      ty + math.sin(ang) * rr * 0.9, ang + 1.6,
                      4, 1.5, p["magic_light"], NS._alpha(190),
                      core=p["magic_shine"])
        NS._spark_star(surface, tx, ty, NS._s(2.6 + 4.0 * progress),
                       p["magic_hot"], NS._alpha(120 + 110 * progress),
                       spikes=4, rot=phase * 0.5, core=p["magic_shine"])
        NS._dashed_ring(surface, x, y + NS.GROUND_DY, 21,
                        p["magic_dark"], NS._alpha(60 + 120 * progress),
                        phase * 0.4, segments=6, thick=2, span=0.5,
                        squash=0.32)

    @staticmethod
    def _draw_manabreak_foreground(surface, boss, x, y, timer, phase):
        """Q fallback: streak bolt tip -> target + burst arrival."""
        NS = _NS_gornak
        p = NS.PALETTE
        progress = NS._skill_progress(boss, "q")
        tx, ty = NS._tip_screen(boss, x, y)
        if progress < 0.62:
            for i in range(4):
                t = (phase * 0.8 + i * 0.25) % 1.0
                NS._shard(surface, tx + (NS._hash01(i * 7.1) - 0.5) * 10,
                          ty - t * 14, -1.57 + math.sin(i * 2.2) * 0.5,
                          int(2 + 3 * t), 1, p["magic_light"],
                          NS._alpha(200 * (1 - t)), core=p["magic_shine"])
            return
        bx, by = NS._target_position(boss, x, y)
        k = min(1.0, (progress - 0.62) / 0.30)
        hx = tx + (bx - tx) * k
        hy = ty + (by - ty) * k
        ang = math.atan2(by - ty, bx - tx)
        trail = []
        for j in range(7):
            tj = max(0.0, k - j * 0.085)
            trail.append((int(tx + (bx - tx) * tj),
                          int(ty + (by - ty) * tj)))
        NS._ribbon(surface, list(reversed(trail)), [1, 1, 2, 2, 3, 4, 5],
                   p["magic_mid"], NS._alpha(150))
        NS._poly(surface, (*p["magic_hot"], 235),
                 [(int(hx + math.cos(ang) * 7),
                   int(hy + math.sin(ang) * 7)),
                  (int(hx + math.cos(ang + 2.2) * 3),
                   int(hy + math.sin(ang + 2.2) * 3)),
                  (int(hx - math.cos(ang) * 4), int(hy - math.sin(ang) *
                                                     4)),
                  (int(hx + math.cos(ang - 2.2) * 3),
                   int(hy + math.sin(ang - 2.2) * 3))])
        NS._aacircle(surface, (*p["magic_core"], 255), (int(hx), int(hy)),
                     2)
        if k >= 0.99:
            fk = max(0.0, 1.0 - min(1.0, (progress - 0.92) * 8.0))
            NS._spark_star(surface, bx, by, 11, p["magic_hot"],
                           NS._alpha(235 * fk),
                           spikes=8, rot=phase * 0.5, core=p["magic_core"])

    @staticmethod
    def _draw_blink_ground(surface, boss, x, y, timer, phase):
        """W: cincin asal menutup + cincin kedatangan terbuka."""
        NS = _NS_gornak
        p = NS.PALETTE
        progress = NS._skill_progress(boss, "w")
        fx = getattr(boss, "blink_from_x", 0)
        fy = getattr(boss, "blink_from_y", 0)
        if fx or fy:
            ox, oy = NS._world_to_local(boss, x, y, fx, fy)
            a = NS._alpha(200 * (1 - progress) ** 1.2)
            r = int(24 * (1 - progress * 0.7))
            NS._dashed_ring(surface, ox, oy + 4, r, p["magic_mid"], a,
                            phase * 0.9, segments=6, thick=2, span=0.55,
                            squash=0.30)
            NS._aaline(surface, (*p["magic_light"], a), (ox, oy + 4),
                       (ox, oy - 26), 2)
            for i in range(4):
                hh = NS._hash01(i * 3.7)
                NS._shard(surface, ox + (hh - 0.5) * 22,
                          oy + 4 - hh * 16, -1.57 + (hh - 0.5),
                          4, 1.5, p["magic_light"], a,
                          core=p["magic_shine"])
        ka = max(0.0, (progress - 0.62) / 0.38)
        if ka > 0:
            aa = NS._alpha(215 * (1 - ka))
            rr = int(10 + 40 * ka)
            NS._ellipse(surface, (*p["magic_hot"], aa),
                        (x - rr, y + NS.GROUND_DY - rr // 3, rr * 2,
                         max(5, rr // 2)), 2)
            NS._spark_star(surface, x, y + NS.GROUND_DY - 4, rr // 2,
                           p["magic_shine"], aa, spikes=6, rot=phase * 0.4,
                           core=p["magic_core"])

    @staticmethod
    def _draw_counterspell_foreground(surface, boss, x, y, timer, phase):
        """E Counterspell — TELEGRAPH DUNIA (100 px) + kubah badan.

        Kontrak masterwork: ring E HARUS lingkaran pada radius
        100/``_fx_scale`` di sekitar (x, y), bahkan saat lapisan hidup
        mengambil alih — cincin E bukan dekorasi, dia menjawab "apa yang
        akan kebal". Karena itu digambar di canvas dan TIDAK pernah
        disupres oleh ``owned``.
        """
        NS = _NS_gornak
        p = NS.PALETTE
        progress = NS._skill_progress(boss, "e")
        fs = NS._fx_scale(boss)
        wr = NS._ring_r(boss, 100)
        fade = 1.0 - max(0.0, progress - 0.9) * 8.0
        a = NS._alpha(235 * fade * (0.25 + 0.75 * min(1.0,
                                                       progress * 4)))
        # segel presisi di radius dunia
        NS._arcane_seal(surface, x, y, wr, phase * 0.6, a, fs, nodes=8,
                       star=4, spin=1.1)
        NS._dashed_ring(surface, x, y, int(wr * 0.90), p["magic_dark"],
                        NS._alpha(120 * fade), -phase * 0.8, segments=12,
                        thick=1, span=0.42, squash=1.0)
        NS._rune_orbit(surface, x, y, wr * 0.70, -phase * 0.9,
                       NS._alpha(190 * fade), fs, count=8)
        for i in range(6):
            ang = i * math.tau / 6 + phase * 0.15
            NS._chevron(surface, x + math.cos(ang) * wr * 0.84,
                        y + math.sin(ang) * wr * 0.84, ang,
                        int(6 * fs), p["magic_light"],
                        NS._alpha(170 * fade), max(2, int(fs + 1)))
        # retakan tanah + serpihan pantul HANYA di 28% pertama (gating
        # presisi: sampling test menguji frame STEADY, bukan frame tangkap)
        if progress < 0.28:
            k = progress / 0.28
            for i in range(6):
                ang = i * math.tau / 6 + 0.4
                NS._jagged_crack(surface, x, y + NS.GROUND_DY, ang,
                                 int(wr * 0.42 * k),
                                 (p["magic_mid"], p["magic_light"]),
                                 NS._alpha(150 * (1 - k * 0.4)), i + 2,
                                 width=max(1, int(2 * fs)), segs=3)
            for i in range(7):
                d = wr * (1.04 - 0.86 * k)
                ang = i * math.tau / 7 + 0.9
                NS._shard(surface, x + math.cos(ang) * d,
                          y + math.sin(ang) * d, ang,
                          int(5 * fs) + 2, max(2, int(2.4 * fs)),
                          p["magic_hot"], NS._alpha(220 * (1 - k * 0.6)),
                          core=p["magic_shine"])
        # kubah hexagonal di badan (jauh lebih kecil dari ring dunia)
        cx0, cy0 = x, y - 3
        r0 = 24.0
        hexpts = []
        for i in range(7):
            ang = i * math.tau / 6 + phase * 0.2
            hexpts.append((cx0 + math.cos(ang) * r0,
                           cy0 + math.sin(ang) * r0 * 0.92))
        NS._poly(surface, (*p["armor_dark"], NS._alpha(96 * fade)),
                 [(int(px), int(py)) for px, py in hexpts])
        NS._poly(surface, (*p["magic_dark"], NS._alpha(70 * fade)),
                 [(int(px), int(py)) for px, py in hexpts])
        for i in range(6):
            NS._aaline(surface, (*p["magic_hot"], NS._alpha(205 * fade)),
                       (int(hexpts[i][0]), int(hexpts[i][1])),
                       (int(hexpts[i + 1][0]), int(hexpts[i + 1][1])), 1)

    @staticmethod
    def _draw_manavoid_ground(surface, boss, x, y, timer, phase):
        """R Mana Void — genangan + segel dunia 180 px DI CASTER."""
        NS = _NS_gornak
        p = NS.PALETTE
        progress = NS._skill_progress(boss, "r")
        fs = NS._fx_scale(boss)
        wr = NS._ring_r(boss, 180)
        gy = y + NS.GROUND_DY
        open_ = min(1.0, progress * 3.0)
        a_fill = NS._alpha(150 * open_)
        # genangan: fill KECIL di tengah + rim lebar — keduanya sengaja
        # TIDAK menyentuh band sampling di radius sprite (lihat catatan
        # _draw_counterspell_foreground: ring dunia = satu-satunya yang
        # boleh lewat presisi)
        NS._ellipse(surface, (*p["magic_darkest"], a_fill),
                    (x - int(wr * 0.45), gy - int(wr * 0.15),
                     int(wr * 0.9), int(wr * 0.3)), 0)
        NS._ellipse(surface, (*p["magic_void"], NS._alpha(200 * open_)),
                    (x - int(wr * 0.30), gy - int(wr * 0.10),
                     int(wr * 0.6), int(wr * 0.2)), 0)
        NS._ellipse(surface,
                    (*p["magic_mid"],
                     NS._alpha(96 + 60 * math.sin(phase * 1.2))),
                    (x - wr, gy - int(wr * 0.30), wr * 2,
                     int(wr * 0.60)), 2)
        # segel presisi radius dunia di sekitar CASTER (bukan target)
        NS._arcane_seal(surface, x, y, wr, phase * 0.45,
                        NS._alpha(220 * open_), fs, nodes=7, star=4,
                        spin=-0.8)
        if progress < 0.5:
            for i in range(8):
                t = progress / 0.5
                d = wr * (0.92 - 0.76 * t)
                ang = i * math.tau / 8 + phase * 0.55
                NS._shard(surface, x + math.cos(ang) * d,
                          gy + math.sin(ang) * d * 0.30 - d * 0.18,
                          -1.4 + math.sin(i) * 0.6,
                          int(5 * fs) + 2, max(2, int(2.2 * fs)),
                          p["magic_light"],
                          NS._alpha(120 + 110 * t), core=p["magic_shine"])
        for i in range(8):
            hh = NS._hash01(i * 1.9 + 0.3)
            ang = i * math.tau / 8 + hh
            NS._jagged_crack(surface, x, gy, ang, int(wr * 0.40 * open_),
                             (p["magic_mid"], p["magic_dark"]),
                             NS._alpha(150 * open_), 10 + i,
                             width=max(1, int(2 * fs)), segs=3)

    @staticmethod
    def _draw_manavoid_foreground(surface, boss, x, y, timer, phase):
        """R foreground: core void di dada + retak petir + pilar hisap."""
        NS = _NS_gornak
        p = NS.PALETTE
        progress = NS._skill_progress(boss, "r")
        fs = NS._fx_scale(boss)
        cx0, cy0 = x, y - 4
        pulse = 0.5 + 0.5 * math.sin(phase * 2.6)
        r0 = NS._s(9 + 6 * progress + 2 * pulse)
        NS._aacircle(surface, (*p["magic_void"], NS._alpha(235)),
                     (cx0, cy0), r0)
        NS._aacircle(surface, (*p["magic_mid"], 255), (cx0, cy0),
                     max(1, int(r0 * 0.62)))
        NS._aacircle(surface, (*p["magic_shine"], 255), (cx0, cy0),
                     max(1, int(r0 * 0.30)))
        for i in range(12):
            hh = NS._hash01(i * 2.7)
            ang = phase * (0.9 + 0.25 * hh) + i * math.tau / 12
            rr = r0 + int(8 + 20 * hh)
            NS._shard(surface, cx0 + math.cos(ang) * rr,
                      cy0 + math.sin(ang) * rr * 0.85, ang + 1.57,
                      max(2, int((3 + 5 * progress) * fs * 0.9)), 2,
                      p["magic_hot"], NS._alpha(120 + 100 * progress),
                      core=p["magic_core"])
        if progress > 0.55:
            for i in range(5):
                hh = NS._hash01(i * 11.3 + 2.1)
                ang = 0.6 + i * 1.22 + hh * 0.7
                NS._jagged_crack(surface, cx0, cy0, ang,
                                 int(46 * fs + 40 * hh * progress),
                                 (p["magic_hot"], p["magic_shine"],
                                  p["white"]),
                                 NS._alpha(150 + 90 * progress), 21 + i,
                                 width=1, segs=3)
        if progress > 0.80:
            k = (progress - 0.80) / 0.20
            ha = NS._alpha(210 * (1 - k))
            hgt = int(120 * (0.4 + 0.6 * k))
            for off, col in ((0, p["magic_mid"]), (3, p["magic_light"]),
                             (-3, p["magic_dark"])):
                NS._aaline(surface, (*col, ha), (x + off, y - 30),
                           (x + off, y - 30 - hgt),
                           3 if off == 0 else 1)
            NS._spark_star(surface, x, y - 34 - hgt // 2,
                           int(12 + 16 * k), p["magic_hot"], ha, spikes=8,
                           rot=phase, core=p["magic_core"])
        if progress > 0.62:
            k = (progress - 0.62) / 0.38
            NS._ellipse(surface, (*p["magic_shine"], NS._alpha(160 * k)),
                        (x - int(30 * k), y - 4 - int(30 * k),
                         int(60 * k), int(60 * k)), 2)


# ====================================================================
# Alias modul — akses cepat ala-namespace lama + re-export yang aman
# untuk `from bosses.gornak_v5 import draw_gornak`.
# ====================================================================
_NS = _NS_gornak
SCALE = _NS.SCALE
LIFT = _NS.LIFT
GROUND_DY = _NS.GROUND_DY
SKILL_DUR = _NS.SKILL_DUR
PALETTE = _NS.PALETTE
ACTIONS = _NS.ACTIONS
DEBUG_CHARACTER = _NS.DEBUG_CHARACTER
ATTACK_PHASES = _NS.ATTACK_PHASES
ATTACK_ACTIVE_WINDOW = _NS.ATTACK_ACTIVE_WINDOW
draw_gornak = _NS.draw_gornak


if __name__ == "__main__":                      # smoke render manual
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((1, 1))

    class _Probe:
        def __init__(self):
            self.direction = 1
            self.pulse = 1.35
            self.timer = 0
            self.attack_cooldown = 38
            self.active_skill = None
            self.active_skill_timer = 0
            self.alive = True
            self.hurt_flash_timer = 0
            self.speed = 1.5
            self.radius = 16
            self.range = 60
            self.target = None
            self.x = 0.0
            self.y = 0.0

    surf = pygame.Surface((320, 240), pygame.SRCALPHA)
    pr = _Probe()
    for name in ("idle", "walk", "attack", "surge", "ward", "void",
                 "blink", "victory", "death"):
        pr._gnk_attack_progress = 0.55
        pr._gnk_attack_active = name == "attack"
        _NS._draw_gnk_rig(surf, 160, 130, 1, 1.2, name, 0.4, False)
    pygame.image.save(surf, "/tmp/gornak_v5_smoke.png")
    print("smoke render ok -> /tmp/gornak_v5_smoke.png")
