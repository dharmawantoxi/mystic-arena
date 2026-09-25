"""GRIMJAW V1.0 pixel-art renderer — pola arsitektur ``heroes/kaizen_v1.py``.

Modul ini mengganti jalur gambar Grimjaw dengan sprite chibi pixel-art
48x48 @2.6x, persis seperti yang dilakukan ``heroes/kaizen_v1.py`` untuk
Kaizen: grid sumber kecil, blok pixel integer, satu rig berlapis yang
dihitung ulang setiap pose, dan kontrak geometri senjata yang menjadi
SATU sumber kebenaran bagi lapisan FX hidup (``heroes/grimjaw_fx.py``).

Struktur berkas sengaja MIRROR kaizen_v1.py supaya kedua renderer bisa
dibandingkan baris per baris:

    KONFIGURASI & PALETTE          identitas Grimjaw (api + darah + baja)
    HELPER PROSEDURAL              _clamp/_rgba/_mix/_static/_scratch/...
    KONTRAK KOORDINAT & ANIMASI    _pixel_local/_make_pixel_ops/...
    POSE & ANIMATION CONTROLLER    _detect_moving/_update_attack_anim/
                                   _attack_pose/_blade_angle/...
    LAYER SPRITE V1                mane/mask/torso/pauldron/blade/...
    AMBIENT & SKILL FX (canvas)    aura, platform, Q/W/E/R telegraph
    PROYEKTIL (fallback canvas)    FlameWave / CritWave
    POSE MODES + ENTRY POINT       idle/walk/attack/spin/hurt/death
    HOOK LAPISAN HIDUP             _live_module/_fx_live_owned

Yang TIDAK berubah (identitas & gameplay Grimjaw):
  * skill Q Blade Fury, W Healing Ward, E Critical Strike, R Omnislash,
    beserta timer visual ``SKILL_VISUAL_DURATION``;
  * timeline serangan ``ATTACK_WINDUP_END/ATTACK_SWING_END`` dan busur
    bilah ``ATTACK_ARC_START/SWEEP/END`` (kontrak heroes/grimjaw_fx.py
    dan tools/test_grimjaw_swing_arah.py);
  * nama atribut state ``_gj_*``, ``_moving_cached``, proyektil
    ``_gj_projectiles``, dan hook ``owns()/attach()`` lapisan hidup;
  * PALETTE lama tetap menang lewat pewarisan namespace legacy.

Gameplay, kontrol sentuh, generasi dunia, dan damage tetap milik Mystic
Arena; modul ini hanya memiliki pose visual Grimjaw dan efek canvas
fallback-nya. 100% PROSEDURAL - tidak ada PNG/JPG/GIF/sprite-sheet.

Catatan pass kebersihan (review pemain):
  * KAKI digambar sebagai rect grid (pola Kaizen): paha + greave baja +
    boot dengan sol gelap - bukan lagi garis tebal/poligon bot raksasa.
  * PEDANG digambar sebagai bilah segmen garis (pola katana Kaizen)
    dengan garda emas tegak-lurus sumbu bilah (ikut rotasi), hilt wrap
    merah + pommel emas, dan kepalan yang MENUTUP pangkal bilah sehingga
    bilah selalu terlihat menyatu dengan tangan.
  * Detail sub-piksel (garis 0.6px, titik api melayang) dibuang supaya
    hasil downscale HD bersih dan mulus.
"""

import math
import random

import pygame


def install(legacy_cls):
    """Kembalikan subclass V1 dari namespace legacy yang diberikan.

    ``heroes._bundle`` historically contains all hero namespaces in one
    file.  Subclassing the old namespace lets older tools and the live FX
    layer keep importing their helper names while the actual Grimjaw
    render path is fully replaced by the V1 pixel-art implementation
    below - the same layering used by ``heroes/kaizen_v1.py``.
    """

    class GrimjawV1Renderer(legacy_cls):
        """GRIMJAW V1.0 — Juggernaut Flame-Blade (pixel-art, Kaizen pattern)."""

        # ------------------------------------------------------------------
        # Palette: swatch doodle/masterwork dipertahankan supaya identitas
        # material Grimjaw (api + darah + baja + emas) sama persis.
        # ------------------------------------------------------------------
        C_OUTLINE = (20, 17, 23)
        C_SKIN_DARKEST = (118, 82, 64)
        C_SKIN_DARK = (154, 110, 82)
        C_SKIN_MID = (192, 146, 106)
        C_SKIN_LIGHT = (222, 182, 140)
        C_SKIN_HIGH = (243, 214, 176)
        C_HAIR_DARKEST = (120, 42, 28)
        C_HAIR_DARK = (170, 62, 26)
        C_HAIR_MID = (220, 108, 34)
        C_HAIR_LIGHT = (243, 156, 54)
        C_HAIR_HIGH = (252, 198, 92)
        C_HAIR_SHINE = (255, 228, 136)
        C_MASK_SHADOW = (170, 162, 152)
        C_MASK_DARK = (200, 194, 184)
        C_MASK_MID = (230, 226, 216)
        C_MASK_LIGHT = (246, 244, 236)
        C_MASK_SHINE = (255, 255, 252)
        C_MASK_LINE = (88, 80, 90)
        C_BLOOD_DARKEST = (118, 26, 30)
        C_BLOOD_DARK = (156, 36, 40)
        C_BLOOD_MID = (196, 48, 52)
        C_BLOOD_LIGHT = (224, 76, 76)
        C_BLOOD_BRIGHT = (242, 114, 110)
        C_ARMOR_DARKEST = (56, 40, 28)
        C_ARMOR_DARK = (90, 62, 40)
        C_ARMOR_MID = (126, 88, 52)
        C_ARMOR_LIGHT = (166, 120, 72)
        C_ARMOR_HIGH = (202, 152, 96)
        C_RED_DARKEST = (108, 30, 34)
        C_RED_DARK = (144, 38, 42)
        C_RED_MID = (188, 52, 56)
        C_RED_LIGHT = (218, 76, 78)
        C_RED_BRIGHT = (240, 110, 108)
        C_GOLD_DARKEST = (118, 78, 24)
        C_GOLD_DARK = (160, 112, 32)
        C_GOLD_MID = (204, 150, 48)
        C_GOLD_LIGHT = (234, 190, 78)
        C_GOLD_SHINE = (252, 226, 132)
        C_METAL_DARKEST = (46, 46, 54)
        C_METAL_DARK = (76, 76, 86)
        C_METAL_MID = (114, 114, 124)
        C_METAL_LIGHT = (158, 158, 168)
        C_METAL_SHINE = (218, 218, 226)
        C_FIRE_DARKEST = (112, 28, 10)
        C_FIRE_DARK = (166, 48, 14)
        C_FIRE_MID = (230, 104, 22)
        C_FIRE_LIGHT = (248, 168, 48)
        C_FIRE_HOT = (255, 214, 100)
        C_FIRE_CORE = (255, 246, 220)
        C_EMBER = (255, 178, 84)
        C_HEAL_DARKEST = (28, 74, 36)
        C_HEAL_DARK = (52, 124, 62)
        C_HEAL_MID = (96, 190, 106)
        C_HEAL_LIGHT = (150, 232, 158)
        C_HEAL_CORE = (228, 252, 230)
        C_RAGE_DARK = (118, 28, 22)
        C_RAGE_MID = (186, 48, 34)
        C_RAGE_LIGHT = (238, 96, 56)
        C_RAGE_BRIGHT = (255, 148, 96)
        C_BOOT_DARKEST = (38, 32, 36)
        C_BOOT_DARK = (60, 48, 46)
        C_BOOT_MID = (96, 70, 56)
        C_BOOT_LIGHT = (136, 98, 72)
        C_EYE = (255, 64, 48)
        C_PAPER = (250, 246, 236)

        # The renderer namespace is also consumed by heroes/grimjaw_fx.py.
        # Legacy values win when present (jaga swatch); defaults fill the
        # critical live-FX keys when the base is minimal (tools).
        _V1_PALETTE_DEFAULTS = {
            "ink": (20, 17, 23),
            "ink_soft": (44, 38, 50),
            "paper": (250, 246, 236),
            "skin_darkest": (118, 82, 64),
            "skin_dark": (154, 110, 82),
            "skin_mid": (192, 146, 106),
            "skin_light": (222, 182, 140),
            "skin_high": (243, 214, 176),
            "hair_darkest": (120, 42, 28),
            "hair_dark": (170, 62, 26),
            "hair_mid": (220, 108, 34),
            "hair_light": (243, 156, 54),
            "hair_high": (252, 198, 92),
            "hair_shine": (255, 228, 136),
            "mask_shadow": (170, 162, 152),
            "mask_dark": (200, 194, 184),
            "mask_mid": (230, 226, 216),
            "mask_light": (246, 244, 236),
            "mask_shine": (255, 255, 252),
            "mask_line": (88, 80, 90),
            "blood_darkest": (118, 26, 30),
            "blood_dark": (156, 36, 40),
            "blood_mid": (196, 48, 52),
            "blood_light": (224, 76, 76),
            "blood_bright": (242, 114, 110),
            "armor_darkest": (56, 40, 28),
            "armor_dark": (90, 62, 40),
            "armor_mid": (126, 88, 52),
            "armor_light": (166, 120, 72),
            "armor_high": (202, 152, 96),
            "red_darkest": (108, 30, 34),
            "red_dark": (144, 38, 42),
            "red_mid": (188, 52, 56),
            "red_light": (218, 76, 78),
            "red_bright": (240, 110, 108),
            "gold_darkest": (118, 78, 24),
            "gold_dark": (160, 112, 32),
            "gold_mid": (204, 150, 48),
            "gold_light": (234, 190, 78),
            "gold_shine": (252, 226, 132),
            "gold_engrave": (255, 210, 110),
            "metal_darkest": (46, 46, 54),
            "metal_dark": (76, 76, 86),
            "metal_mid": (114, 114, 124),
            "metal_light": (158, 158, 168),
            "metal_shine": (218, 218, 226),
            "fire_darkest": (112, 28, 10),
            "fire_dark": (166, 48, 14),
            "fire_mid": (230, 104, 22),
            "fire_light": (248, 168, 48),
            "fire_hot": (255, 214, 100),
            "fire_core": (255, 246, 220),
            "ember": (255, 178, 84),
            "heal_darkest": (28, 74, 36),
            "heal_dark": (52, 124, 62),
            "heal_mid": (96, 190, 106),
            "heal_light": (150, 232, 158),
            "heal_core": (228, 252, 230),
            "rage_dark": (118, 28, 22),
            "rage_mid": (186, 48, 34),
            "rage_light": (238, 96, 56),
            "rage_bright": (255, 148, 96),
            "shadow": (0, 0, 0),
            "shadow_deep": (20, 17, 23),
            "white": (255, 255, 255),
            "eye_glow": (255, 64, 48),
            "dark_eye": (30, 22, 34),
            "boot_darkest": (38, 32, 36),
            "boot_dark": (60, 48, 46),
            "boot_mid": (96, 70, 56),
            "boot_light": (136, 98, 72),
            "cloth_stitch": (98, 32, 36),
        }
        PALETTE = dict(_V1_PALETTE_DEFAULTS,
                       **(getattr(legacy_cls, "PALETTE", {}) or {}))
        INK = (20, 17, 23)

        # ------------------------------------------------------------------
        # Grid & geometri bilah.
        #
        # Native coordinates live on the V1 48x48 pixel grid (origin 24).
        # The existing pipeline later normalizes this rig to arena size,
        # so the SOURCE grid is laid out with the same chunky proportions
        # as Kaizen V1 (kepala sempit, kaki mekar, senjata kebawa keluar)
        # instead of the narrow doodle column it replaced.
        # ------------------------------------------------------------------
        PIXEL_SCALE = 2.6
        PIXEL_ORIGIN = 24.0
        # Grimjaw legacy locals are already canvas pixels (no RIG_SCALE
        # multiplier in grimjaw_fx.blade_points), so V1 keeps the neutral
        # 1.0 for pattern parity with Kaizen/Vex V1.
        RIG_SCALE = 1.0

        # Blade geometry is shared by the cached body and the live swing
        # trail.  ``_blade_grip_local``/``_blade_tip_local`` return canvas
        # pixels relative to the hip anchor (+x = arah hadap), so the live
        # layer terminates exactly on the blade the rig draws.
        BLADE_LEN_SRC = 35.0
        BLADE_LEN = BLADE_LEN_SRC * PIXEL_SCALE

        # Tangan idle/gagang bilah + bahu lengan pedang pada grid sumber.
        # Nilainya ikut rig V1 (badan lebih lebar & senjata dibawa ke
        # depan), bukan kolom doodle sempit versi lama.
        HAND_SRC = (40.2, 26.3)
        SHOULDER_SRC = (32.0, 21.0)

        # Durasi tetap sinkron dengan rig legacy dan grimjaw_fx.py.
        SKILL_VISUAL_DURATION = {"q": 118, "w": 59, "e": 39, "r": 59}
        ATTACK_WINDUP_END = 0.25
        ATTACK_SWING_END = 0.62
        ATTACK_ARC_START = -2.30
        ATTACK_ARC_SWEEP = -3.05
        ATTACK_ARC_END = ATTACK_ARC_START + ATTACK_ARC_SWEEP
        ATTACK_IMPACT = 0.56
        ATTACK_IMPACT_POINT = ATTACK_IMPACT
        ATTACK_ACTIVE_WINDOW = (0.43, 0.64)

        ANIM_STATES = {
            "IDLE": 0, "WALK": 10, "SPIN": 20, "WARD": 30,
            "CRIT": 35, "OMNI": 40, "ATTACK": 50,
            "HURT": 70, "DEATH": 100,
        }
        DEBUG_CHARACTER = False

        _LIVE_MOD = None
        _STATIC_SURFACES = {}
        _SCRATCH_POOL = {}
        _GHOST_BUF = {}
        _OMNI_BUF = {}
        try:
            _FX_LIVE = legacy_cls._LiveFlag()
        except Exception:  # pragma: no cover - stripped tools
            _FX_LIVE = type("_LiveFlag", (), {"v": False})()

        # ------------------------------------------------------------------
        # Low-level procedural helpers and compatibility API.
        # ------------------------------------------------------------------
        @staticmethod
        def _clamp(color):
            vals = tuple(int(max(0, min(255, c))) for c in color)
            return vals if len(vals) in (3, 4) else vals[:3]

        @staticmethod
        def _rgba(color, alpha=255):
            c = GrimjawV1Renderer._clamp(color)
            if len(c) >= 4:
                return c[:3] + (int(max(0, min(255, c[3] * alpha / 255.0))),)
            return c[:3] + (int(max(0, min(255, alpha))),)

        @staticmethod
        def _mix(a, b, t):
            t = max(0.0, min(1.0, float(t)))
            return tuple(int(x + (y - x) * t) for x, y in zip(a[:3], b[:3]))

        @staticmethod
        def _hash01(seed):
            n = math.sin(float(seed) * 12.9898 + 78.233) * 43758.5453
            return n - math.floor(n)

        @staticmethod
        def _static(key, builder):
            surf = GrimjawV1Renderer._STATIC_SURFACES.get(key)
            if surf is None:
                if len(GrimjawV1Renderer._STATIC_SURFACES) > 96:
                    GrimjawV1Renderer._STATIC_SURFACES.clear()
                surf = builder()
                GrimjawV1Renderer._STATIC_SURFACES[key] = surf
            return surf

        @staticmethod
        def _scratch(w, h):
            key = (max(1, int(w)), max(1, int(h)))
            surf = GrimjawV1Renderer._SCRATCH_POOL.get(key)
            if surf is None:
                if len(GrimjawV1Renderer._SCRATCH_POOL) > 24:
                    GrimjawV1Renderer._SCRATCH_POOL.clear()
                surf = pygame.Surface(key, pygame.SRCALPHA)
                GrimjawV1Renderer._SCRATCH_POOL[key] = surf
            surf.fill((0, 0, 0, 0))
            return surf

        @staticmethod
        def _rect(surface, color, rect, border_radius=0):
            pygame.draw.rect(surface, GrimjawV1Renderer._rgba(color),
                             pygame.Rect(*(int(round(v)) for v in rect)),
                             border_radius=max(0, int(border_radius)))

        @staticmethod
        def _poly(surface, color, points):
            if len(points) >= 3:
                pygame.draw.polygon(
                    surface, GrimjawV1Renderer._rgba(color),
                    [(int(round(x)), int(round(y))) for x, y in points])

        @staticmethod
        def _ellipse(surface, color, rect, width=0):
            pygame.draw.ellipse(surface, GrimjawV1Renderer._rgba(color),
                                pygame.Rect(*(int(round(v)) for v in rect)),
                                max(0, int(width)))

        @staticmethod
        def _aaline(surface, color, start, end, width=1):
            pygame.draw.line(surface, GrimjawV1Renderer._rgba(color),
                             (int(round(start[0])), int(round(start[1]))),
                             (int(round(end[0])), int(round(end[1]))),
                             max(1, int(round(width))))

        @staticmethod
        def _aacircle(surface, color, center, radius, width=0):
            pygame.draw.circle(surface, GrimjawV1Renderer._rgba(color),
                               (int(round(center[0])), int(round(center[1]))),
                               max(1, int(round(radius))), max(0, int(width)))

        @staticmethod
        def _dither_dots(surface, color, a, b, step=3, alpha=210):
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy)
            if length <= 0:
                return
            count = max(2, int(length / max(1, step)))
            for i in range(0, count, 2):
                t = i / float(count)
                x, y = a[0] + dx * t, a[1] + dy * t
                GrimjawV1Renderer._rect(surface, (*color[:3], alpha),
                                        (x, y, 1, 1))

        @staticmethod
        def _spark_star(surface, cx, cy, size, color, alpha,
                        spikes=4, rot=0.0, core=None):
            if alpha <= 0:
                return
            for i in range(max(2, int(spikes))):
                a = rot + i * math.pi / max(2, int(spikes))
                inner = size * 0.22
                p0 = (cx + math.cos(a) * inner, cy + math.sin(a) * inner)
                p1 = (cx + math.cos(a) * size, cy + math.sin(a) * size)
                GrimjawV1Renderer._aaline(surface, (*color[:3], alpha),
                                          p0, p1, 1)
            if core is not None:
                GrimjawV1Renderer._aacircle(
                    surface, (*core[:3], alpha), (cx, cy), max(1, size * 0.22))

        @staticmethod
        def _chevron(surface, cx, cy, ang, size, color, alpha, width=2):
            ux, uy = math.cos(ang), math.sin(ang)
            px, py = -uy, ux
            tip = (cx + ux * size, cy + uy * size)
            a = (cx - ux * size * .35 + px * size * .55,
                 cy - uy * size * .35 + py * size * .55)
            b = (cx - ux * size * .35 - px * size * .55,
                 cy - uy * size * .35 - py * size * .55)
            GrimjawV1Renderer._aaline(surface, (*color[:3], alpha),
                                      a, tip, width)
            GrimjawV1Renderer._aaline(surface, (*color[:3], alpha),
                                      tip, b, width)

        @staticmethod
        def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                         dashes=12, width=2, squash=1.0):
            for i in range(max(4, int(dashes))):
                a0 = phase + i * math.tau / dashes + .08
                a1 = phase + (i + .72) * math.tau / dashes
                pts = [(cx + math.cos(a0 + (a1 - a0) * j / 5.0) * radius,
                        cy + math.sin(a0 + (a1 - a0) * j / 5.0) * radius * squash)
                       for j in range(6)]
                pygame.draw.lines(
                    surface, GrimjawV1Renderer._rgba((*color[:3], alpha)),
                    False, [(int(x), int(y)) for x, y in pts], width)

        @staticmethod
        def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                          width=2, segments=3):
            pts = [(cx, cy)]
            ux, uy = math.cos(ang), math.sin(ang)
            px, py = -uy, ux
            steps = 5 + max(0, int(segments)) * 2
            for i in range(1, steps):
                t = i / float(steps)
                jitter = (GrimjawV1Renderer._hash01(seed + i * 9) - .5) * length * .22
                pts.append((cx + ux * length * t + px * jitter,
                            cy + uy * length * t + py * jitter))
            for i in range(len(pts) - 1):
                col = colors[i % len(colors)] if colors else \
                    GrimjawV1Renderer.C_FIRE_MID
                GrimjawV1Renderer._aaline(surface, (*col[:3], alpha),
                                          pts[i], pts[i + 1], width)

        @staticmethod
        def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
            pts = list(spine)
            if len(pts) < 2:
                return pts
            out = []
            for i, p in enumerate(pts):
                out.append(p)
                if i < len(pts) - 1:
                    a = pts[i + 1]
                    dx, dy = a[0] - p[0], a[1] - p[1]
                    ln = math.hypot(dx, dy) or 1.0
                    nx, ny = -dy / ln, dx / ln
                    side = -1.0 if GrimjawV1Renderer._hash01(seed + i) < .5 else 1.0
                    out.append((p[0] + dx * .55 + nx * (min_len + depth) * side,
                                p[1] + dy * .55 + ny * (min_len + depth) * side))
            return out

        @staticmethod
        def _aoe_marks(surface, cx, cy, radius, color, alpha, phase=0.0,
                       squash=1.0, ticks=12, tick_len=None, corner=True,
                       inner=False):
            if radius < 4 or alpha <= 0:
                return
            tick_len = tick_len or max(6, int(radius * .1))
            lo, hi = ((radius - tick_len, radius) if not inner
                      else (radius, radius + tick_len))
            for i in range(max(4, int(ticks))):
                a = phase + i * math.tau / ticks
                p0 = (cx + math.cos(a) * lo, cy + math.sin(a) * lo * squash)
                p1 = (cx + math.cos(a) * hi, cy + math.sin(a) * hi * squash)
                GrimjawV1Renderer._aaline(
                    surface, (*GrimjawV1Renderer.C_OUTLINE, alpha), p0, p1, 3)
                GrimjawV1Renderer._aaline(surface, (*color[:3], alpha),
                                          p0, p1, 1)
            if corner:
                for a in (math.pi / 4, 3 * math.pi / 4,
                          5 * math.pi / 4, 7 * math.pi / 4):
                    p = (cx + math.cos(a) * radius,
                         cy + math.sin(a) * radius * squash)
                    GrimjawV1Renderer._chevron(
                        surface, p[0], p[1], a + math.pi / 2,
                        max(5, radius * .11), color, alpha, 1)

        @staticmethod
        def _filled_crescent(surface, cx, cy, ang, r_outer, r_inner, span,
                             color, segments=12):
            pts = []
            n = max(4, int(segments))
            perp = ang + math.pi / 2.0
            for i in range(n + 1):
                a = perp - span + 2.0 * span * i / n
                pts.append((cx + math.cos(a) * r_outer,
                            cy + math.sin(a) * r_outer))
            for i in range(n, -1, -1):
                a = perp - span + 2.0 * span * i / n
                pts.append((cx + math.cos(a) * r_inner,
                            cy + math.sin(a) * r_inner))
            GrimjawV1Renderer._poly(surface, color, pts)

        @staticmethod
        def _fx_scale(boss):
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            return max(1.0, min(2.6, 1.0 / scale))

        @staticmethod
        def _ring_r(boss, world_px, surface=None):
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            radius = float(world_px) / scale
            if surface is not None:
                radius = min(radius, min(surface.get_size()) * .5 - 10)
            return max(4, int(radius))

        @staticmethod
        def _skill_progress(skill, timer):
            """Progress 0..1 skill FX dari countdown active_skill_timer."""
            dur = float(GrimjawV1Renderer.SKILL_VISUAL_DURATION.get(
                skill, max(1, timer or 1)))
            return max(0.0, min(1.0, 1.0 - float(timer) / dur))

        @staticmethod
        def _skill_steady(progress, tail=5.0, floor=.25):
            """Amplop fade akhir skill: plateau 1.0 lalu melandai ke floor."""
            return max(floor, min(1.0, (1.0 - progress) * tail + .3))

        # ------------------------------------------------------------------
        # Coordinate and animation contracts consumed by live FX.
        # ------------------------------------------------------------------
        @staticmethod
        def _world_to_local(hero, x, y, wx, wy):
            scale = float(getattr(hero, "_render_scale", 1.0) or 1.0)
            ox = (float(wx) - float(getattr(hero, "x", x))) / scale
            oy = (float(wy) - float(getattr(hero, "y", y))) / scale
            rng = int(getattr(hero, "range", 130) or 130)
            half = max(120, int(rng / scale) + 40)
            max_off = half - 20
            dist = math.hypot(ox, oy)
            if dist > max_off and dist > 0:
                ox *= max_off / dist
                oy *= max_off / dist
            return int(x + ox), int(y + oy)

        @staticmethod
        def _target_position(hero, x, y):
            target = getattr(hero, "target", None)
            if target is not None and getattr(target, "alive", True):
                return GrimjawV1Renderer._world_to_local(
                    hero, x, y, target.x, target.y)
            scale = getattr(hero, "_render_scale", None)
            dist = 60 * (float(scale) if scale else 1.0)
            return int(x + dist * getattr(hero, "direction", 1)), int(y)

        @staticmethod
        def _pixel_local(x, y):
            s = GrimjawV1Renderer.PIXEL_SCALE
            return ((float(x) - GrimjawV1Renderer.PIXEL_ORIGIN) * s,
                    (float(y) - GrimjawV1Renderer.PIXEL_ORIGIN) * s)

        @staticmethod
        def _local_to_src(lx, ly):
            """Konversi lokal canvas -> grid sumber 48x48 (gambar bilah)."""
            P = GrimjawV1Renderer
            return (P.PIXEL_ORIGIN + float(lx) / P.PIXEL_SCALE,
                    P.PIXEL_ORIGIN + float(ly) / P.PIXEL_SCALE)

        @staticmethod
        def _tint(color, tint):
            c = GrimjawV1Renderer._clamp(color)
            if tint is None:
                return c
            if isinstance(tint, pygame.Color):
                t = tuple(tint)
            else:
                t = tuple(tint)
            vals = tuple(int(c[i] * t[i] / 255.0) for i in range(3))
            alpha = int((c[3] if len(c) > 3 else 255) *
                        (t[3] if len(t) > 3 else 255) / 255.0)
            return vals + (alpha,)

        @staticmethod
        def _make_pixel_ops(surface, cx, cy, facing, body_x=0, body_y=0,
                            crouch=0, tint=None):
            """Create R/RO closures equivalent to Kaizen V1's pixel helpers."""
            s = GrimjawV1Renderer.PIXEL_SCALE
            sx = -1.0 if facing < 0 else 1.0

            def rect_for(x, y, w, h, ox=0, oy=0, extra_crouch=0):
                rx = cx + ((x + body_x + ox - GrimjawV1Renderer.PIXEL_ORIGIN) * s * sx)
                if facing < 0:
                    rx -= w * s
                ry = cy + ((y + body_y + crouch + extra_crouch -
                            GrimjawV1Renderer.PIXEL_ORIGIN) * s)
                return pygame.Rect(int(round(rx)), int(round(ry)),
                                   max(1, int(round(w * s))),
                                   max(1, int(round(h * s))))

            def R(x, y, w, h, col, alpha=None):
                color = GrimjawV1Renderer._tint(col, tint)
                if alpha is not None:
                    color = color[:3] + (int(color[3] * alpha / 255.0),)
                pygame.draw.rect(surface, color, rect_for(x, y, w, h))

            def RO(x, y, w, h, col, alpha=None):
                # One source-pixel selout keeps the sprite readable after
                # smoothscale, mirroring Kaizen V1 exactly.
                R(x - 1, y - 1, w + 2, h + 2,
                  GrimjawV1Renderer.C_OUTLINE, alpha)
                R(x, y, w, h, col, alpha)

            def point(x, y, ox=0, oy=0):
                return (cx + ((x + body_x + ox - GrimjawV1Renderer.PIXEL_ORIGIN) * s * sx),
                        cy + ((y + body_y + crouch + oy - GrimjawV1Renderer.PIXEL_ORIGIN) * s))

            def line(a, b, color, width=1, alpha=None):
                c = GrimjawV1Renderer._tint(color, tint)
                if alpha is not None:
                    c = c[:3] + (int(c[3] * alpha / 255.0),)
                pygame.draw.line(surface, c, point(*a), point(*b),
                                 max(1, int(round(width * s))))

            return R, RO, point, line

        # ------------------------------------------------------------------
        # V1 pose calculation and animation controller.
        #
        # Geometri bilah (_blade_angle/_blade_grip_local/_blade_len/
        # _blade_tip_local) dimiliki V1 seperti pada Kaizen, namun tanda
        # tangan fungsinya DIPERTAHANKAN sama dengan namespace legacy
        # karena heroes/grimjaw_fx.py memakainya sebagai jembatan pose.
        # ------------------------------------------------------------------
        @staticmethod
        def _detect_moving(hero):
            if not hasattr(hero, "_gj_last_x"):
                hero._gj_last_x = float(getattr(hero, "x", 0.0))
                hero._gj_last_y = float(getattr(hero, "y", 0.0))
                hero._moving_cached = False
                return False
            dx = abs(float(getattr(hero, "x", 0.0)) - hero._gj_last_x)
            dy = abs(float(getattr(hero, "y", 0.0)) - hero._gj_last_y)
            hero._gj_last_x = float(getattr(hero, "x", 0.0))
            hero._gj_last_y = float(getattr(hero, "y", 0.0))
            moving = dx + dy > 0.3
            hero._moving_cached = moving
            return moving

        @staticmethod
        def _update_attack_anim(hero):
            """Track melee attack animation timeline (kontrak v3).

            Serangan baru dideteksi dari timer NAIK sehingga bekerja pada
            berapa pun langkah simulasi antar frame gambar.
            """
            cooldown = max(2, int(getattr(hero, "attack_cooldown", 40)))
            timer = int(getattr(hero, "timer", 0))
            previous = int(getattr(hero, "_gj_prev_timer", -1))
            active = bool(getattr(hero, "_gj_attack_active", False))

            trigger = previous >= 0 and timer > previous

            if trigger:
                hero._gj_attack_active = True
                hero._gj_crit_active = random.random() < 0.25
                active = True

            if active and timer <= 0:
                hero._gj_attack_active = False
                hero._gj_crit_active = False
                active = False

            hero._gj_prev_timer = timer
            hero._gj_attack_frame = max(0, cooldown - timer) if active else 0
            hero._gj_attack_progress = (
                min(1.0, hero._gj_attack_frame / max(1, cooldown - 1))
                if active else 0.0)

        @staticmethod
        def _attack_pose(ap):
            """Pose badan basic attack -> dict (bob, lean, flare, tremble).

            Sudut & gagang TIDAK ditabulasi ulang di sini: keduanya dibaca
            dari ``_blade_angle`` / ``_blade_grip_local`` supaya rig,
            crescent api, dan lapisan hidup mustahil menyimpang.  Kunci
            legacy ``bob``/``lean`` tetap disediakan karena jalur doodle
            lama (heroes/_bundle.py) masih membacanya.
            """
            P = GrimjawV1Renderer
            ap = max(0.0, min(1.0, float(ap)))
            if ap < P.ATTACK_SWING_END:
                span = max(1e-6, P.ATTACK_SWING_END - P.ATTACK_WINDUP_END)
                t = max(0.0, min(1.0, (ap - P.ATTACK_WINDUP_END) / span))
                bump = math.sin(math.pi * t)
                return {
                    "angle": P._blade_angle(0.0, "attack", ap, 0.0),
                    "grip": P._blade_grip_local("attack", ap, 0.0),
                    "bob": int(round(4.0 * bump)),
                    "lean": int(round(-3.0 + 12.0 * t)),
                    "flare": 1.0 + 0.16 * bump,
                    "tremble": 1 if 0.20 < ap < 0.36 else 0,
                }
            u = max(0.0, min(1.0, (ap - P.ATTACK_SWING_END) /
                             max(1e-6, 1.0 - P.ATTACK_SWING_END)))
            u = u * u * (3.0 - 2.0 * u)
            return {
                "angle": P._blade_angle(0.0, "attack", ap, 0.0),
                "grip": P._blade_grip_local("attack", ap, 0.0),
                "bob": 0,
                "lean": int(round(9.0 - 8.0 * u)),
                "flare": 1.0 + 0.04 * (1.0 - u),
                "tremble": 0,
            }

        @staticmethod
        def _blade_angle(phase, action, attack_progress=0.0, spin_phase=0.0):
            """Radian dari garis lurus-bawah: 0 = blade menunjuk ke bawah.

            Basic attack SELALU berputar ke arah negatif: bilah diangkat
            ke atas-belakang kepala lalu menebas TURUN ke depan.
            """
            P = GrimjawV1Renderer
            if action == "attack":
                ap = max(0.0, min(1.0, attack_progress))
                if ap < P.ATTACK_WINDUP_END:
                    t = ap / P.ATTACK_WINDUP_END
                    # Wind-up LINEAR (bukan eased): bilah menempuh busur
                    # ~3 rad, easing akan membuat langkah ujung > 26 px per
                    # 1/59 progres (kontrak test_ujung_bilah_kontinu).
                    return 0.92 + (P.ATTACK_ARC_START - 0.92) * t
                if ap < P.ATTACK_SWING_END:
                    t = ((ap - P.ATTACK_WINDUP_END) /
                         (P.ATTACK_SWING_END - P.ATTACK_WINDUP_END))
                    t = t ** 1.35
                    return (P.ATTACK_ARC_START + P.ATTACK_ARC_SWEEP * t)
                if ap >= 1.0:
                    return 0.92
                t = ((ap - P.ATTACK_SWING_END) /
                     (1.0 - P.ATTACK_SWING_END))
                t = t * t * (3.0 - 2.0 * t)
                return (P.ATTACK_ARC_END + 2.0 * math.pi) + \
                    (0.92 - (P.ATTACK_ARC_END + 2.0 * math.pi)) * t
            if action == "spin":
                return spin_phase * 0.5 + math.sin(phase * 1.2) * 0.06
            if action == "walk":
                return 0.88 + math.sin(phase * 1.72) * 0.06
            return 0.92 + math.sin(phase * 0.5) * 0.04

        @staticmethod
        def _blade_grip_local(action, attack_progress=0.0, phase=0.0):
            """Posisi gagang blade (ruang lokal, forward = +x)."""
            P = GrimjawV1Renderer
            if action == "attack":
                ap = max(0.0, min(1.0, attack_progress))
                if ap < P.ATTACK_WINDUP_END:
                    # Sinkron dengan _blade_angle: linear saat wind-up.
                    t = ap / P.ATTACK_WINDUP_END
                    # Gagang naik LEBIH DULU (t^0.4): tanpa ini ujung bilah
                    # menukik ~20 px di bawah tanah saat bilah melewati
                    # posisi lurus-bawah di pertengahan wind-up.
                    return (42.0 - 22.0 * t, 6.0 - 40.0 * (t ** 0.4))
                if ap < P.ATTACK_SWING_END:
                    t = ((ap - P.ATTACK_WINDUP_END) /
                         (P.ATTACK_SWING_END - P.ATTACK_WINDUP_END))
                    if t < 0.45:
                        u = t / 0.45
                        return (20.0 + 24.0 * u, -27.0 + 3.0 * u)
                    u = (t - 0.45) / 0.55
                    u = u * u
                    return (44.0 + 12.0 * u, -24.0 + 29.0 * u)
                t = ((ap - P.ATTACK_SWING_END) /
                     (1.0 - P.ATTACK_SWING_END))
                t = t * t * (3.0 - 2.0 * t)
                return (56.0 - 14.0 * t, 5.0 + 1.0 * t)
            if action == "spin":
                return (34.0, -4.0)
            if action == "walk":
                return (42.0 + math.sin(phase * 1.72) * 3.0, 8.0)
            return (42.0 + math.sin(phase * 0.5) * 1.5,
                    6.0 + math.sin(phase * 0.7) * 1.0)

        @staticmethod
        def _blade_len(action):
            return int(round(GrimjawV1Renderer.BLADE_LEN))

        @staticmethod
        def _blade_len_ap(action, attack_progress=0.0):
            """Panjang bilah per progres serang (loop closure tanpa pop)."""
            return int(round(GrimjawV1Renderer.BLADE_LEN))

        @staticmethod
        def _front_arm_elbow(attack_progress=0.0):
            """Siku lengan pedang selama basic attack (ruang lokal)."""
            P = GrimjawV1Renderer
            ap = max(0.0, min(1.0, attack_progress))
            if ap < P.ATTACK_WINDUP_END:
                t = ap / P.ATTACK_WINDUP_END
                t = 1.0 - (1.0 - t) ** 2
                gx, gy = P._blade_grip_local("attack", ap)
                return (34.0 - 14.0 * t, 12.0 - 39.0 * t)
            if ap < P.ATTACK_SWING_END:
                gx, gy = P._blade_grip_local("attack", ap)
                return (gx - 8.0, gy + 6.0)
            gx, gy = P._blade_grip_local("attack", ap)
            return (gx - 8.0, gy + 6.0)

        @staticmethod
        def _blade_tip_local(phase, action, attack_progress=0.0,
                             spin_phase=0.0):
            """Posisi ujung blade (ruang lokal) - anchor FX lapisan hidup."""
            P = GrimjawV1Renderer
            a = P._blade_angle(phase, action, attack_progress, spin_phase)
            gx, gy = P._blade_grip_local(action, attack_progress, phase)
            L = P._blade_len_ap(action, attack_progress)
            return (gx + math.sin(a) * L, gy + math.cos(a) * L)

        @staticmethod
        def _blade_hand_local(phase, action, attack_progress=0.0):
            """Posisi tangan/gagang dalam ruang lokal (mirror Kaizen)."""
            return GrimjawV1Renderer._blade_grip_local(
                action, attack_progress, phase)

        @staticmethod
        def _blade_tip_position(cx, cy, facing, phase=0.0, action="idle",
                                attack_progress=0.0, spin_phase=0.0):
            """Posisi ujung bilah (canvas) untuk spawn proyektil / FX."""
            P = GrimjawV1Renderer
            tx, ty = P._blade_tip_local(phase, action, attack_progress,
                                        spin_phase)
            f = 1 if facing >= 0 else -1
            return int(cx + tx * f), int(cy + ty)

        @staticmethod
        def _blade_grip_position(cx, cy, facing, action="idle",
                                 attack_progress=0.0, phase=0.0):
            """Posisi gagang bilah (canvas) untuk FX tebasan."""
            P = GrimjawV1Renderer
            gx, gy = P._blade_grip_local(action, attack_progress, phase)
            f = 1 if facing >= 0 else -1
            return int(cx + gx * f), int(cy + gy)

        @staticmethod
        def _grip_src(action, ap=0.0, phase=0.0):
            """Posisi gagang bilah pada grid sumber 48x48."""
            P = GrimjawV1Renderer
            gx, gy = P._blade_grip_local(action, ap, phase)
            return P._local_to_src(gx, gy)

        @staticmethod
        def _tip_src(phase, action, ap=0.0, spin_phase=0.0):
            """Posisi ujung bilah pada grid sumber 48x48."""
            P = GrimjawV1Renderer
            tx, ty = P._blade_tip_local(phase, action, ap, spin_phase)
            return P._local_to_src(tx, ty)

        # ------------------------------------------------------------------
        # The actual V1 sprite layers (bahasa Kaizen V1, identitas Grimjaw:
        # mane api, mask juggernaut, flame blade).  Semua koordinat di
        # bawah adalah grid sumber 48x48 (origin 24, skala 2.6).
        # ------------------------------------------------------------------
        # Lidah mane (base_x, base_y, tilt_derajat, panjang, lebar).
        _MANE_TONGUES_SRC = (
            (11.5, 2.8, -54, 9.0, 4.2),
            (14.5, 0.8, -38, 10.6, 4.6),
            (17.8, -0.6, -22, 11.6, 5.0),
            (21.2, -1.6, -6, 12.0, 5.0),
            (24.8, -1.2, 10, 11.2, 4.6),
            (28.2, 0.4, 26, 9.6, 4.2),
            (31.2, 2.0, 44, 7.4, 3.6),
        )
        _MANE_DETAIL_SRC = (
            (10.8, 4.6, -66, 6.2, 3.0),
            (32.0, 3.4, 58, 5.8, 3.0),
        )
        _MANE_FRINGE_SRC = (
            (18.6, 2.4, -30, 4.4, 2.6),
            (22.4, 1.8, -8, 5.2, 3.0),
            (26.2, 2.4, 14, 4.2, 2.4),
        )

        @staticmethod
        def _flame_tongue_pixel(R, bx, by, dx, dy, length, width, phase,
                                seed=0, hot=False, rage=False):
            """Satu lidah api pixel: 3 pass (tinta, badan, inti)."""
            P = GrimjawV1Renderer
            ln = math.hypot(dx, dy) or 1.0
            ux, uy = dx / ln, dy / ln
            length *= 1.0 + math.sin(phase * 3.1 + seed * 1.7) * 0.08
            steps = max(3, int(length / 1.5))
            if rage:
                outer = (P.C_RAGE_DARK, P.C_RAGE_MID, P.C_RAGE_LIGHT)
                inner = (P.C_RAGE_LIGHT, P.C_RAGE_BRIGHT, P.C_FIRE_CORE)
            elif hot:
                outer = (P.C_FIRE_DARK, P.C_FIRE_MID, P.C_FIRE_LIGHT)
                inner = (P.C_FIRE_LIGHT, P.C_FIRE_HOT, P.C_FIRE_CORE)
            else:
                outer = (P.C_HAIR_DARKEST, P.C_HAIR_DARK, P.C_HAIR_MID)
                inner = (P.C_HAIR_MID, P.C_HAIR_LIGHT, P.C_HAIR_HIGH)
            for pas, ramp, wmul, lmul in (
                    (0, None, 1.0, 1.0),
                    (1, outer, 0.72, 0.94),
                    (2, inner, 0.42, 0.62)):
                for i in range(steps):
                    t = (i + 0.5) / steps * lmul
                    if t <= 0.0 or t > 1.0:
                        continue
                    wob = math.sin(phase * 4.0 + seed + i * 1.3) * 0.6 * t
                    px = bx + ux * length * t - uy * wob
                    py = by + uy * length * t + ux * wob
                    half = max(0.5, width * 0.5 * wmul * (1.0 - t * 0.8))
                    if pas == 0:
                        col = P.C_OUTLINE
                    else:
                        col = ramp[min(len(ramp) - 1, int(t * len(ramp)))]
                    R(px - half, py - half * 0.75,
                      half * 2, half * 1.5 + 0.6, col)

        @staticmethod
        def _draw_pixel_mane_back(R, RO, phase, tilt=0.0, flare=1.0,
                                  fury=False, omni=False, detail=False):
            """Mane api belakang: 7 lidah mengelilingi puncak kepala."""
            P = GrimjawV1Renderer
            tongues = P._MANE_TONGUES_SRC + (
                P._MANE_DETAIL_SRC if detail else ())
            for i, (bx, by, tilt_deg, ln, wd) in enumerate(tongues):
                a = math.radians(tilt_deg) + tilt
                P._flame_tongue_pixel(
                    R, bx, by, math.sin(a), -math.cos(a), ln * flare, wd,
                    phase, seed=i * 3 + 1, hot=bool(fury or omni),
                    rage=bool(omni and i % 3 == 0))

        @staticmethod
        def _draw_pixel_mane_front(R, phase, tilt=0.0):
            """Poni api kecil menjuntai di dahi mask."""
            P = GrimjawV1Renderer
            for i, (bx, by, tilt_deg, ln, wd) in enumerate(
                    P._MANE_FRINGE_SRC):
                a = math.radians(tilt_deg) + tilt * 0.6
                P._flame_tongue_pixel(
                    R, bx, by, math.sin(a), math.cos(a), ln, wd,
                    phase + 0.7, seed=40 + i * 5)

        @staticmethod
        def _draw_pixel_rear_arm(R, RO, line, elbow, hand, detail=False):
            """Lengan belakang (tinju): 2 pass bersih + kepalan."""
            P = GrimjawV1Renderer
            sh = (19.5, 21.0)
            line(sh, elbow, P.C_OUTLINE, 4.8)
            line(sh, elbow, P.C_SKIN_DARK, 3.4)
            line(elbow, hand, P.C_OUTLINE, 4.4)
            line(elbow, hand, P.C_SKIN_DARK, 3.0)
            RO(hand[0] - 1.6, hand[1] - 1.6, 3.2, 3.2, P.C_SKIN_DARK)
            R(hand[0] - 1.0, hand[1] - 1.2, 2.0, 0.8, P.C_SKIN_MID)
            if detail:
                for kn in (-0.9, 0.1):
                    R(hand[0] + kn, hand[1] + 0.7, 0.7, 0.9, P.C_OUTLINE)

        @staticmethod
        def _draw_pixel_cloth_teeth(surface, point, spine_src, top_src,
                                    fill, shade, inner):
            """Hem bergerigi: poligon gigi + isi + tepi tinta."""
            P = GrimjawV1Renderer
            teeth = P._tuft_points(list(spine_src), depth=1.4, min_len=2.4,
                                   seed=9)
            x0, y0 = top_src[0]
            x1, y1 = top_src[1]
            pts = [point(x0, y0), point(x1, y1)]
            pts += [point(*t) for t in teeth]
            P._poly(surface, fill, pts)
            edge = [point(x0, y0)] + [point(*t) for t in teeth] + [
                point(x1, y1)]
            pygame.draw.lines(
                surface, P.C_OUTLINE, False,
                [(int(x), int(y)) for x, y in edge], 2)
            cx = (x0 + x1) / 2.0
            short = [point(x0 + 2, y0 + 2), point(x1 - 2, y1 + 2)]
            short += [point(cx + (t[0] - cx) * 0.55,
                            y0 + (t[1] - y0) * 0.55) for t in teeth]
            P._poly(surface, inner, short)
            P._poly(surface, shade, [point(x0, y0), point(x0 + 2, y0),
                                     point(x0 + 1, y0 + 4)])

        @staticmethod
        def _draw_pixel_skirt_back(surface, R, RO, point, sway_src):
            """War-skirt belakang: panel + hem bergerigi."""
            P = GrimjawV1Renderer
            RO(16.0, 30.0, 16.0, 5.0, P.C_RED_DARK)
            R(17.0, 31.0, 14.0, 3.0, P.C_RED_MID)
            P._draw_pixel_cloth_teeth(
                surface, point,
                [(29.4 + sway_src, 37.3), (26.3, 40.8), (24.0, 39.6),
                 (21.7, 41.2), (18.6 + sway_src, 36.9)],
                [(16.5, 33.5), (31.5, 33.5)],
                P.C_RED_DARK, P.C_RED_DARKEST, P.C_RED_MID)

        @staticmethod
        def _draw_pixel_loincloth(surface, R, RO, point, sway_src):
            """Loincloth depan: panel + hem bergerigi."""
            P = GrimjawV1Renderer
            RO(19.0, 31.0, 10.0, 4.0, P.C_RED_DARK)
            R(20.0, 32.0, 8.0, 2.0, P.C_RED_MID)
            P._draw_pixel_cloth_teeth(
                surface, point,
                [(19.5, 35.5), (22.1, 38.5 + sway_src), (24.0, 40.1 + sway_src),
                 (25.9, 38.2 + sway_src), (28.5, 35.5)],
                [(19.5, 34.0), (28.5, 34.0)],
                P.C_RED_DARK, P.C_RED_DARKEST, P.C_RED_MID)

        @staticmethod
        def _draw_pixel_legs(surface, R, RO, point, line, front_step,
                             rear_step, front_lift, rear_lift, walking):
            """Kaki: rect grid bersih (pola Kaizen) - paha, greave baja,
            boot kokoh dengan sol gelap.  Tanpa garis spageti/poligon
            raksasa supaya tetap tajam setelah downscale HD."""
            P = GrimjawV1Renderer
            for side, step, lift, dark in (
                    (-1, rear_step, rear_lift, True),
                    (1, front_step, front_lift, False)):
                bx = 22.0 if side < 0 else 27.5
                off = int(round(step))
                up = int(round(lift))
                skin = P.C_SKIN_DARK if dark else P.C_SKIN_MID
                # Paha: menempel di hip (tidak ikut melangkah).
                RO(bx - 2.6, 32.5, 5.2, 5.5, skin)
                R(bx - 1.8, 33.4, 1.5, 3.4,
                  P.C_SKIN_MID if dark else P.C_SKIN_LIGHT)
                # Lutut: band emas.
                kx = bx - 2.0 + off * 0.5
                R(kx, 37.3, 4.0, 1.3, P.C_GOLD_DARK)
                R(kx + 0.6, 37.4, 2.8, 0.8, P.C_GOLD_MID)
                # Greave baja (menyusut saat kaki terangkat = lutut menekuk).
                gx0 = bx - 2.2 + off
                gy0 = 38.4 - up * 0.9
                RO(gx0, gy0, 4.4, 6.2 - up * 0.7,
                   P.C_METAL_DARK if dark else P.C_METAL_MID)
                R(gx0 + 0.8, gy0 + 1.0, 1.2, 3.8 - up * 0.5,
                  P.C_METAL_MID if dark else P.C_METAL_LIGHT)
                # Boot: badan + toe depan + sol gelap tebal.
                fx0 = bx - 3.0 + off
                fy0 = 44.4 - up
                boot = P.C_BOOT_DARK if dark else P.C_BOOT_MID
                RO(fx0, fy0, 7.4, 5.0, boot)
                if not dark:
                    RO(fx0 + 6.2, fy0 + 1.5, 3.4, 3.5, boot)
                    R(fx0 + 6.4, fy0 + 1.8, 1.3, 2.6, P.C_BOOT_LIGHT)
                R(fx0 + 0.6, fy0 + 0.6, 4.4, 1.0,
                  P.C_BOOT_LIGHT if not dark else boot)
                R(fx0 - 0.4, fy0 + 4.4, 10.4, 1.5, P.C_OUTLINE)

        @staticmethod
        def _draw_pixel_torso(R, RO, line, detail=False):
            """Torso V-taper + sash + harness + medallion."""
            P = GrimjawV1Renderer
            RO(16.5, 18.0, 15.0, 5.0, P.C_SKIN_MID)
            RO(16.5, 22.0, 15.0, 5.0, P.C_SKIN_MID)
            RO(18.0, 26.0, 12.0, 3.5, P.C_SKIN_MID)
            R(28.5, 19.0, 3.0, 9.0, P.C_SKIN_DARK)
            R(17.5, 19.0, 5.0, 2.0, P.C_SKIN_LIGHT)
            line((23.5, 19.0), (23.5, 28.0), P.C_MASK_LINE, 0.6)
            line((20.0, 25.0), (27.0, 25.0), P.C_SKIN_DARK, 0.6)
            # Sash diagonal (tali merah).
            line((17.2, 19.8), (31.4, 28.5), P.C_OUTLINE, 3.6)
            line((17.2, 19.8), (31.4, 28.5), P.C_RED_MID, 2.4)
            line((17.2, 19.2), (31.4, 27.9), P.C_RED_LIGHT, 0.8)
            for i in range(4):
                t = 0.2 + i * 0.2
                R(17.2 + 14.2 * t - 0.5, 19.8 + 8.7 * t - 0.5, 1, 1,
                  P.C_RED_DARKEST)
            # Harness baja.
            line((31.0, 19.4), (18.8, 28.5), P.C_ARMOR_DARK, 2.4)
            line((31.0, 19.4), (18.8, 28.5), P.C_ARMOR_MID, 1.4)
            for i in range(3):
                t = 0.25 + i * 0.25
                R(31.0 - 12.2 * t - 0.5, 19.4 + 9.1 * t - 0.5, 1, 1,
                  P.C_GOLD_MID)
            RO(23.5, 22.0, 2.0, 2.0, P.C_GOLD_MID)
            R(23.1, 21.6, 0.8, 0.8, P.C_PAPER)
            if detail:
                line((19.0, 24.0), (21.5, 28.0), P.C_SKIN_DARK, 0.5)
                line((29.0, 24.0), (26.5, 28.0), P.C_SKIN_DARK, 0.5)

        @staticmethod
        def _draw_pixel_belt(R, RO):
            """Sabuk + gesper emas."""
            P = GrimjawV1Renderer
            RO(18.0, 28.0, 12.0, 3.0, P.C_ARMOR_DARK)
            for bx in (19.5, 21.5, 26.5, 28.5):
                R(bx, 29.0, 1, 1, P.C_GOLD_DARK)
            RO(22.5, 28.3, 3, 2.4, P.C_GOLD_MID)
            R(23.0, 28.8, 1, 1, P.C_GOLD_SHINE)

        @staticmethod
        def _draw_pixel_tassets(R, RO):
            """Hip tassets: 2 pelat per sisi."""
            P = GrimjawV1Renderer
            for hx in (18.5, 29.5):
                RO(hx - 2, 29.5, 4, 5, P.C_ARMOR_DARK)
                R(hx - 1.2, 30.2, 2.4, 3.4, P.C_ARMOR_MID)
                R(hx - 0.5, 33.2, 1, 1, P.C_GOLD_LIGHT)

        @staticmethod
        def _draw_pixel_pauldrons(surface, R, RO, point):
            """Pauldron baja + duri + trim emas."""
            P = GrimjawV1Renderer
            for sx in (14.5, 33.5):
                RO(sx - 3.0, 15.0, 6.0, 5.0, P.C_METAL_LIGHT)
                R(sx + 0.5, 17.2, 2, 1.6, P.C_METAL_MID)
                R(sx - 3.0, 18.8, 6.0, 0.8, P.C_GOLD_MID)
                for dx in (-1.4, 0.8):
                    sp = [point(sx + dx - 0.4, 15.1),
                          point(sx + dx + 0.4, 15.1),
                          point(sx + dx + (0.35 if dx > 0 else -0.35), 11.6)]
                    P._poly(surface, P.C_METAL_MID, sp)
                    pygame.draw.lines(surface, P.C_OUTLINE, True,
                                      [(int(x), int(y)) for x, y in sp], 1)
                R(sx - 2.2, 15.8, 1, 1, P.C_METAL_SHINE)

        @staticmethod
        def _draw_pixel_front_arm(R, RO, line, elbow_src, grip_src):
            """Lengan blade: 2 pass bersih + bracer baja kotak."""
            P = GrimjawV1Renderer
            sh = (32.0, 21.0)
            line(sh, elbow_src, P.C_OUTLINE, 4.6)
            line(sh, elbow_src, P.C_SKIN_MID, 3.2)
            line(elbow_src, grip_src, P.C_OUTLINE, 4.2)
            line(elbow_src, grip_src, P.C_SKIN_LIGHT, 2.8)
            # Bracer: kotak baja di lengan bawah (bukan garis tipis).
            mx = elbow_src[0] * 0.72 + grip_src[0] * 0.28
            my = elbow_src[1] * 0.72 + grip_src[1] * 0.28
            RO(mx - 1.8, my - 1.6, 3.6, 3.2, P.C_METAL_MID)
            R(mx - 1.1, my - 1.1, 1.1, 2.4, P.C_METAL_LIGHT)
            R(mx - 1.8, my + 0.6, 3.6, 0.8, P.C_GOLD_DARK)

        @staticmethod
        def _draw_pixel_blade(surface, R, RO, point, line, grip_src, tip_src,
                              phase, hot=False, detail=False):
            """Flame blade: bilah baja bersegmen + garda emas terputar.

            Pola bilah mengikuti Kaizen V1 (segmen garis outline + isi)
            supaya terbaca sebagai PEDANG, bukan tangga kotak.  Garda,
            hilt, dan pommel dihitung pada sumbu bilah sehingga selalu
            menempel di genggaman pada sudut apa pun.  Gagang & ujung
            tetap berasal dari geometri lokal renderer sehingga trail
            lapisan hidup menempel PERSIS di bilah yang digambar.
            """
            P = GrimjawV1Renderer
            gx, gy = grip_src
            tx, ty = tip_src
            dx, dy = tx - gx, ty - gy
            L = max(1e-6, math.hypot(dx, dy))
            ux, uy = dx / L, dy / L
            nx, ny = -uy, ux

            # 1) Hilt: wrap merah + pommel emas di BELAKANG genggaman.
            h0 = (gx - ux * 1.0, gy - uy * 1.0)
            h1 = (gx - ux * 4.6, gy - uy * 4.6)
            line(h0, h1, P.C_OUTLINE, 2.6)
            line(h0, h1, P.C_RED_DARKEST, 1.6)
            p0 = (gx - ux * 5.2, gy - uy * 5.2)
            p1 = (gx - ux * 6.2, gy - uy * 6.2)
            line(p0, p1, P.C_OUTLINE, 2.4)
            line(p0, p1, P.C_GOLD_DARK, 1.4)
            line(p0, p1, P.C_GOLD_LIGHT, 0.6)

            # 2) Bilah: segmen outline + baja, gradasi gelap->terang ke
            #    ujung, menirus pada 25% terakhir (kissaki).
            N = 14
            for i in range(N):
                t0, t1 = i / N, (i + 1) / N
                a = (gx + dx * t0, gy + dy * t0)
                b = (gx + dx * t1, gy + dy * t1)
                w_out = 3.0 if t1 < 0.75 else 2.4
                line(a, b, P.C_OUTLINE, w_out)
                steel = (P.C_METAL_DARK if t0 < 0.2 else
                         P.C_METAL_MID if t0 < 0.55 else P.C_METAL_LIGHT)
                line(a, b, steel, w_out - 1.2)
            # Kilau sisi dalam bilah (edge shine) - satu garis tipis.
            e0 = (gx + ux * L * 0.12 - nx * 1.0, gy + uy * L * 0.12 - ny * 1.0)
            e1 = (gx + ux * L * 0.80 - nx * 1.0, gy + uy * L * 0.80 - ny * 1.0)
            line(e0, e1, P.C_METAL_SHINE, 0.7)

            # 3) Ujung: cap kissaki terang.
            a = (tx - ux * 1.8, ty - uy * 1.8)
            line(a, (tx, ty), P.C_OUTLINE, 2.4)
            line(a, (tx, ty), P.C_METAL_SHINE, 1.0)
            R(tx - 0.8, ty - 0.8, 1.6, 1.6,
              P.C_FIRE_HOT if hot else P.C_METAL_SHINE)

            # 4) Garda emas: palang tegak-lurus sumbu bilah (ikut rotasi).
            g0 = (gx + nx * 2.6, gy + ny * 2.6)
            g1 = (gx - nx * 2.6, gy - ny * 2.6)
            line(g0, g1, P.C_OUTLINE, 3.2)
            line(g0, g1, P.C_GOLD_DARK, 2.0)
            line((gx + nx * 0.2, gy + ny * 0.2),
                 (gx + nx * 1.4, gy + ny * 1.4), P.C_GOLD_LIGHT, 0.8)

            # 5) Gigi api rapi di tepi luar (identitas flame blade).
            for i in range(3):
                t = 0.28 + i * 0.22
                fl = 1.0 + math.sin(phase * 4.2 + i * 2.0) * 0.35
                b0 = (gx + ux * L * t + nx * 1.1, gy + uy * L * t + ny * 1.1)
                b1 = (gx + ux * L * t + nx * (1.3 + 1.7 * fl),
                      gy + uy * L * t + ny * (1.3 + 1.7 * fl))
                line(b0, b1, P.C_FIRE_DARK, 1.4)
                line(b0, b1,
                     P.C_FIRE_LIGHT if i == 1 else P.C_FIRE_MID, 0.8)
            if hot:
                line((gx + ux * L * 0.2 + nx * 1.0, gy + uy * L * 0.2 + ny * 1.0),
                     (tx + nx * 0.8, ty + ny * 0.8), P.C_FIRE_LIGHT, 0.8)
                hx, hy = point(tx, ty)
                P._spark_star(surface, hx, hy, 9, P.C_FIRE_HOT, 200,
                              4, rot=phase)
            if detail:
                R(gx + ux * L * 0.45 + nx * 1.5, gy + uy * L * 0.45 + ny * 1.5,
                  0.8, 0.8, P.C_GOLD_MID)

            # 6) Kepalan MENUTUP pangkal bilah (digambar terakhir ->
            #    bilah selalu nyambung ke tangan, tidak melayang).
            RO(gx - 1.9, gy - 1.8, 3.8, 3.6, P.C_SKIN_MID)
            R(gx - 1.3, gy - 1.5, 2.6, 0.9, P.C_SKIN_HIGH)
            R(gx - 1.9, gy + 0.7, 3.8, 0.7, P.C_SKIN_DARK)
            line((gx - 1.3 - ux * 0.6, gy - 1.0 - uy * 0.6),
                 (gx + 1.3 - ux * 0.6, gy + 0.3 - uy * 0.6),
                 P.C_SKIN_DARK, 0.9)

        @staticmethod
        def _draw_pixel_mask(R, RO, line, phase, anim_name, ward=False,
                             crit=False, omni=False, dead=False):
            """Mask juggernaut: kertas putih + strip darah + mata bara."""
            P = GrimjawV1Renderer
            eyes_glow = anim_name in ("attack", "spin") or crit or omni
            eye_col = P.C_HEAL_MID if ward else P.C_EYE
            RO(19.5, 1.0, 9.0, 4.0, P.C_MASK_LIGHT)
            RO(18.5, 4.0, 12.0, 6.0, P.C_MASK_LIGHT)
            RO(19.0, 9.0, 10.0, 5.0, P.C_MASK_LIGHT)
            RO(20.0, 13.0, 8.0, 3.5, P.C_MASK_LIGHT)
            R(21.0, 16.0, 6.0, 1.2, P.C_MASK_MID)
            R(27.0, 3.0, 2.0, 9.0, P.C_MASK_MID)
            R(28.0, 5.0, 1.0, 7.0, P.C_MASK_SHADOW)
            line((20.5, 1.5), (23.5, 0.8), P.C_MASK_SHINE, 0.8)
            # Tanduk kecil menunjuk ke luar-atas.
            R(18.8, 0.6, 1.4, 2.2, P.C_MASK_MID)
            R(18.4, -0.6, 1.2, 1.4, P.C_MASK_MID)
            R(28.2, 0.6, 1.4, 2.2, P.C_MASK_MID)
            R(28.8, -0.6, 1.2, 1.4, P.C_MASK_MID)
            # Emblem emas diamond di dahi.
            R(23.6, 0.2, 1.2, 2.4, P.C_GOLD_MID)
            R(23.1, 0.8, 2.2, 1.2, P.C_GOLD_MID)
            R(23.8, 1.0, 0.8, 0.8, P.C_GOLD_SHINE)
            # Alis marah + batang hidung.
            line((20.6, 4.2), (22.9, 3.0), P.C_OUTLINE, 0.9)
            line((27.6, 4.2), (25.3, 3.0), P.C_OUTLINE, 0.9)
            line((24.0, 2.6), (24.0, 7.6), P.C_MASK_LINE, 0.6)
            # Strip darah tengah + samping + tetes.
            R(23.7, 0.0, 1.0, 13.5, P.C_BLOOD_MID)
            R(24.0, 1.0, 0.4, 11.5, P.C_BLOOD_LIGHT)
            line((20.6, 1.8), (22.6, 7.6), P.C_BLOOD_DARK, 1.1)
            line((27.6, 1.8), (25.6, 7.6), P.C_BLOOD_DARK, 1.1)
            R(24.6, 15.4, 0.9, 1.2, P.C_BLOOD_MID)
            # Mata: bara merah (hijau saat ward), kedip saat idle.
            blink = (anim_name == "idle" and not eyes_glow
                     and P._hash01(int(phase * 0.9) + 3) > 0.92)
            for ex in (21.8, 26.4):
                if dead:
                    line((ex - 1, 5.0), (ex + 1, 7.0), P.C_OUTLINE, 0.8)
                    line((ex - 1, 7.0), (ex + 1, 5.0), P.C_OUTLINE, 0.8)
                elif blink:
                    R(ex - 1, 6.0, 2, 0.8, P.C_OUTLINE)
                else:
                    R(ex - 1.2, 5.6, 2.4, 2.4, eye_col)
                    R(ex - 0.5, 6.1, 1, 1, P.C_FIRE_CORE)
                    if eyes_glow:
                        R(ex - 1.6, 5.2, 3.2, 0.6, eye_col)

        @staticmethod
        def _draw_grimjaw_sprite(surface, origin, flip_left, anim_name,
                                 frame_idx, tint=(255, 255, 255, 255),
                                 attack_progress=0.0, phase=0.0,
                                 spin_phase=0.0, fury=False, ward=False,
                                 crit=False, omni=False, detail=False,
                                 death_frame=3):
            """Satu frame rig pixel Grimjaw (belakang -> depan)."""
            P = GrimjawV1Renderer
            frame_idx = int(frame_idx)
            ap = max(0.0, min(1.0, float(attack_progress)))
            body_x = body_y = head_y = 0.0
            crouch = 0.0
            flash = False
            dead_eyes = False
            stride = 0.0
            front_step = rear_step = 0.0
            front_lift = rear_lift = 0
            walking = False
            blade_action = anim_name if anim_name in (
                "idle", "walk", "attack", "spin") else "idle"
            blade_ap = ap if anim_name == "attack" else 0.0
            mane_tilt = 0.0
            mane_flare = 1.0
            breath = math.sin(phase * 0.78)
            t_rec = 0.0
            if anim_name == "attack" and ap > P.ATTACK_SWING_END:
                t_rec = (ap - P.ATTACK_SWING_END) / (
                    1.0 - P.ATTACK_SWING_END)
            skirt_sway = math.sin(phase * 0.9 + 1.2) * 3.0 / P.PIXEL_SCALE
            cloth_sway = math.sin(phase * 1.1) * 3.0 / P.PIXEL_SCALE

            if anim_name == "idle":
                body_y = breath * 2.2 / P.PIXEL_SCALE
                body_x = (math.sin(phase * 0.5) * 2.0
                          + math.sin(phase * 0.5 + 1.2) * 1.5
                          ) / P.PIXEL_SCALE
            elif anim_name == "walk":
                walking = True
                stride = math.sin(phase * 1.72)
                body_y = -abs(math.sin(phase * 1.2)) * 4.0 / P.PIXEL_SCALE
                body_x = (math.sin(phase) * 3.0
                          + (4 + abs(stride) * 2)) / P.PIXEL_SCALE
                front_step = stride * 6
                rear_step = -front_step
                vel = math.cos(phase * 1.72)
                front_lift = int(max(0.0, vel) * 3)
                rear_lift = int(max(0.0, -vel) * 3)
                mane_tilt = math.sin(phase + 2.6) * 0.07
            elif anim_name == "attack":
                pose = P._attack_pose(ap)
                body_y = 0.0
                body_x = (pose["grip"][0] - 42.0) * 0.12 / P.PIXEL_SCALE
                mane_flare = pose["flare"]
                mane_tilt = -body_x * 0.05 * (1.0 - t_rec)
                if pose["tremble"]:
                    body_x += 0.4 if int(phase * 30) % 2 else -0.4
                front_step = ap * 5 * (1.0 - t_rec)
                rear_step = -ap * 3 * (1.0 - t_rec)
            elif anim_name == "spin":
                body_y = -2.0 / P.PIXEL_SCALE
                mane_flare = 1.12
                mane_tilt = math.sin(phase * 3.0) * 0.05
                front_step, rear_step = 8.0, -8.0
            elif anim_name == "hurt":
                flash = True
                body_x = -3.0 if not flip_left else 3.0
                body_y = 1.0 if frame_idx == 1 else 0.0
                head_y = -1.0
            elif anim_name == "death":
                dead_eyes = True
                dfr = death_frame if death_frame is not None else 3
                if dfr <= 0:
                    flash = True
                    body_x = -3.0 if not flip_left else 3.0
                    head_y = -1.0
                else:
                    crouch = min(14.0, 5.0 + dfr * 3.0)
                    head_y = min(8.0, dfr * 2.0)
                    body_x = -1.5 if not flip_left else 1.5
                    mane_flare = 0.6
                    mane_tilt = 0.9 if not flip_left else -0.9
            if fury:
                mane_flare *= 1.10 + 0.05 * math.sin(phase * 3)
            if crit or omni:
                mane_flare *= 1.06

            use_tint = (255, 96, 96, 255) if flash else tint
            facing = -1 if flip_left else 1
            R, RO, point, line = P._make_pixel_ops(
                surface, origin[0], origin[1], facing,
                body_x, body_y, crouch, use_tint)
            if head_y:
                R2, RO2, point2, line2 = P._make_pixel_ops(
                    surface, origin[0], origin[1], facing,
                    body_x, body_y + head_y, crouch, use_tint)
            else:
                R2, RO2, point2, line2 = R, RO, point, line

            # Solver lengan belakang (tinju) pada grid sumber.
            if anim_name == "attack":
                r_elbow = (13.0 + 2.0 * (1.0 - t_rec), 26.0 - 2.0 * t_rec)
                r_hand = (9.5 + 2.0 * (1.0 - t_rec), 34.0 + 2.0 * t_rec)
            elif anim_name == "walk":
                r_elbow = (13.0, 26.0 + stride * 2.0)
                r_hand = (9.5, 34.0 + stride * 3.0)
            elif anim_name == "spin":
                r_elbow = (12.0, 25.0)
                r_hand = (8.5, 30.0)
            else:
                r_elbow = (13.0, 26.0 + breath * 0.6)
                r_hand = (9.5, 34.0 + breath * 0.8)

            # Gagang / ujung / siku lengan blade.
            grip_l = P._blade_grip_local(blade_action, blade_ap, phase)
            if anim_name == "attack":
                elbow_l = P._front_arm_elbow(blade_ap)
            elif anim_name == "walk":
                elbow_l = (grip_l[0] - 8.0, grip_l[1] + 6.0 + stride * 2.0)
            else:
                elbow_l = (grip_l[0] - 8.0, grip_l[1] + 6.0)
            grip_s = P._local_to_src(*grip_l)
            elbow_s = P._local_to_src(*elbow_l)
            tip_s = P._tip_src(phase, blade_action, blade_ap, spin_phase)
            if anim_name == "death" and (
                    death_frame is None or death_frame >= 2):
                tip_s = (grip_s[0] + 2.0, grip_s[1] + 18.0)

            # Belakang -> depan: mane -> lengan blk -> skirt -> kaki ->
            # torso -> belt -> loincloth -> tassets -> pauldron -> leher ->
            # lengan dpn -> blade -> mask -> poni.
            P._draw_pixel_mane_back(R, RO, phase, mane_tilt, mane_flare,
                                    fury, omni, detail)
            P._draw_pixel_rear_arm(R, RO, line, r_elbow, r_hand, detail)
            P._draw_pixel_skirt_back(surface, R, RO, point, skirt_sway)
            P._draw_pixel_legs(surface, R, RO, point, line, front_step,
                               rear_step, front_lift, rear_lift, walking)
            P._draw_pixel_torso(R, RO, line, detail)
            P._draw_pixel_belt(R, RO)
            P._draw_pixel_loincloth(surface, R, RO, point, cloth_sway)
            P._draw_pixel_tassets(R, RO)
            P._draw_pixel_pauldrons(surface, R, RO, point)
            R(22.0, 17.5, 4.0, 3.0, P.C_SKIN_DARK)
            P._draw_pixel_front_arm(R, RO, line, elbow_s, grip_s)
            if anim_name == "spin":
                P._draw_spin_flame_sweep(surface, origin[0], origin[1],
                                         facing, spin_phase, phase)
            P._draw_pixel_blade(surface, R, RO, point, line, grip_s, tip_s,
                                phase, hot=bool(crit or omni),
                                detail=detail)
            P._draw_pixel_mask(R2, RO2, line2, phase, anim_name, ward,
                               crit, omni, dead_eyes)
            P._draw_pixel_mane_front(R2, phase, mane_tilt)

            # Aksen gerak: garis kecepatan + bara mane.
            if anim_name == "walk" and abs(stride) > 0.55:
                bx, by = point(-22, -16)
                for k in range(3):
                    P._aaline(surface, (*P.C_OUTLINE, 80),
                              (bx - k * 6 * facing, by + k * 3),
                              (bx - k * 6 * facing - 9 * facing,
                               by + k * 3), 1)
            if fury or omni:
                for i in range(3):
                    ex = origin[0] + facing * 6 + (i - 1) * 14
                    ey = origin[1] - 55 - (i % 2) * 8
                    P._spark_star(surface, ex, ey, 4, P.C_HAIR_LIGHT,
                                  150, 4, rot=phase + i)

        @staticmethod
        def draw_grimjaw_sprite(surface, origin, flip_left, anim_name,
                                frame_idx, tint=(255, 255, 255, 255),
                                attack_progress=0.0, phase=0.0,
                                spin_phase=0.0, **kwargs):
            """Public V1 sprite entry point (mirror Kaizen V1)."""
            return GrimjawV1Renderer._draw_grimjaw_sprite(
                surface, origin, flip_left, anim_name, frame_idx, tint,
                attack_progress=attack_progress, phase=phase,
                spin_phase=spin_phase, **kwargs)

        # ------------------------------------------------------------------
        # Elite body wrapper (kontrak lama: dipanggil pose legacy,
        # ghost/omni buffer, dan tooling dengan urutan argumen warisan).
        # ------------------------------------------------------------------
        @staticmethod
        def _draw_grimjaw_elite(surface, cx, cy, facing, phase, action,
                                attack_progress=0.0, spin_phase=0.0,
                                detail=False, fury=False, ward=False,
                                crit=False, omni=False, death_frame=3):
            """Render satu frame pixel-art V1 (tanda tangan legacy)."""
            P = GrimjawV1Renderer
            anim = action if action in (
                "idle", "walk", "attack", "spin", "hurt", "death") else "idle"
            if anim == "idle":
                frame = int(abs(math.sin(float(phase) * 4.0)) > 0.45)
            elif anim == "walk":
                frame = int(float(phase) * 6.0) % 6
            elif anim == "attack":
                frame = min(4, max(0, int(float(attack_progress) * 5.0)))
            elif anim == "spin":
                frame = int(float(spin_phase) * 2.0) % 6
            elif anim == "hurt":
                frame = int(float(phase) * 8.0) % 2
            else:
                frame = 0
            P._draw_grimjaw_sprite(
                surface, (cx, cy), facing < 0, anim, frame,
                attack_progress=attack_progress, phase=float(phase),
                spin_phase=float(spin_phase), fury=fury, ward=ward,
                crit=crit, omni=omni, detail=detail,
                death_frame=death_frame)
            f = -1 if facing < 0 else 1
            if anim == "attack":
                tip = P._blade_tip_local(float(phase), "attack",
                                         float(attack_progress))
                P._rect(surface, (*P.C_FIRE_CORE, 220),
                        (cx + tip[0] * f - 1, cy + tip[1] - 1, 2, 2))
            if detail and anim != "death":
                y = cy - 34
                P._rect(surface, (*P.C_GOLD_LIGHT, 240),
                        (cx + f * 4 - 1, y, 2, 1))
                P._rect(surface, (*P.C_MASK_LIGHT, 230),
                        (cx + f * 8, y + 4, 1, 1))
                P._rect(surface, (*P.C_HAIR_HIGH, 230),
                        (cx - f * 20, cy - 42, 2, 2))

        @staticmethod
        def _draw_grimjaw_body(surface, cx, cy, facing, phase, action,
                               attack_progress=0, spin_phase=0, detail=False,
                               fury=False, ward=False, crit=False, omni=False,
                               skill_state=None, death_frame=3):
            """Wrapper historis - semua pose lewat satu rig pixel V1."""
            P = GrimjawV1Renderer
            act = action
            if skill_state in ("q", "w", "e", "r") and action in (
                    "idle", "walk"):
                if skill_state == "q":
                    act = "spin"
                    spin_phase = spin_phase or float(phase) * 6.0
                elif skill_state == "w":
                    ward = True
                elif skill_state == "e":
                    crit = True
                elif skill_state == "r":
                    act = "attack"
                    attack_progress = 0.6
                    omni = True
            P._draw_grimjaw_elite(
                surface, cx, cy, facing, phase, act, attack_progress,
                spin_phase, detail, fury, ward, crit, omni,
                death_frame=death_frame)

        # ------------------------------------------------------------------
        # Ambient dan skill FX (fallback canvas; lapisan hidup
        # heroes/grimjaw_fx.py memiliki versi 60fps di arena).
        # ------------------------------------------------------------------
        @staticmethod
        def _draw_shadow(surface, x, y):
            P = GrimjawV1Renderer
            pygame.draw.ellipse(surface, (*P.C_OUTLINE, 110),
                                pygame.Rect(int(x - 40), int(y - 7), 80, 13))
            pygame.draw.ellipse(surface, (*P.C_FIRE_DARK, 45),
                                pygame.Rect(int(x - 26), int(y - 4), 52, 7))

        @staticmethod
        def _draw_fire_mist(surface, cx, cy, phase, trail=False, facing=1,
                            intense=False):
            """Kabut bara di kaki: kotak asap + bara naik (pixel)."""
            P = GrimjawV1Renderer
            q = int(phase * 2) % 8
            seed = q * 37 + (1 if intense else 0)
            col = P.C_FIRE_DARK if intense else P._mix(
                P.C_FIRE_DARK, P.C_OUTLINE, 0.5)
            alpha = 95 if intense else 70
            n = 3 if (trail or intense) else 2
            for i in range(n):
                ox = ((P._hash01(seed + i * 7) - 0.5) * 18 - i * 6 * facing
                      - (4 * facing if trail else 0))
                oy = (-i * 5
                      + (P._hash01(seed * 3 + i) - 0.5) * 6)
                w = max(4, 16 - i * 4)
                P._rect(surface, (*col, max(20, alpha - i * 18)),
                        (int(cx + ox - w / 2), int(cy - 5 + oy - 2), w, 5))
            embers = 3 if intense else 2
            ecol = P.C_FIRE_MID if intense else P.C_EMBER
            ealpha = 80 if intense else 55
            for i in range(embers):
                ex = cx + (P._hash01(seed + 5 + i * 3) - 0.5) * 44
                ey = cy + 2 - ((phase * 9 + i * 7) % 12)
                P._rect(surface, (*ecol, ealpha), (int(ex), int(ey), 2, 2))

        @staticmethod
        def _draw_fire_aura(surface, x, y, phase):
            """Halo api samar di belakang badan (pixel)."""
            P = GrimjawV1Renderer
            P._dashed_ring(surface, x, y - 10, 52, P.C_FIRE_MID, 34,
                           phase * 0.4, dashes=14, width=2, squash=0.85)
            P._dashed_ring(surface, x, y - 10, 38, P.C_FIRE_DARK, 30,
                           -phase * 0.3, dashes=10, width=2, squash=0.85)
            for i in range(6):
                a = phase * 0.5 + i * math.tau / 6
                ex = x + math.cos(a) * 52
                ey = y - 10 + math.sin(a) * 52 * 0.85
                P._rect(surface, (*P.C_EMBER, 60),
                        (int(ex), int(ey), 2, 2))

        @staticmethod
        def _draw_rage_aura(surface, x, y, phase):
            """Halo rage (omnislash): cincin merah lebih liar."""
            P = GrimjawV1Renderer
            P._dashed_ring(surface, x, y - 10, 56, P.C_RAGE_MID, 40,
                           phase * 0.7, dashes=16, width=2, squash=0.85)
            P._dashed_ring(surface, x, y - 10, 42, P.C_RAGE_DARK, 34,
                           -phase * 0.5, dashes=12, width=2, squash=0.85)
            P._dashed_ring(surface, x, y - 10, 28, P.C_RAGE_LIGHT, 30,
                           phase * 1.1, dashes=8, width=1, squash=0.85)
            for i in range(8):
                a = phase * 0.9 + i * math.tau / 8
                rr = 56 if i % 2 == 0 else 42
                ex = x + math.cos(a) * rr
                ey = y - 10 + math.sin(a) * rr * 0.85
                P._rect(surface, (*P.C_RAGE_BRIGHT, 70),
                        (int(ex), int(ey), 2, 2))

        @staticmethod
        def _draw_fire_platform(surface, x, y, phase, skill):
            """Sigil tanah pixel: cincin putus + bracket + rune (cache)."""
            P = GrimjawV1Renderer
            edge = {"q": P.C_FIRE_MID, "w": P.C_HEAL_MID,
                    "e": P.C_GOLD_MID, "r": P.C_RAGE_MID}.get(
                        skill, P.C_EMBER)
            q = int(phase * 2) % 8

            def build():
                s = pygame.Surface((96, 48), pygame.SRCALPHA)
                cx, cy = 48, 26
                P._dashed_ring(s, cx, cy + 6, 34, edge, 150, q * 0.8,
                               dashes=9, width=2, squash=11 / 34)
                for k in range(4):
                    a = k * (math.pi / 2) + math.pi / 4
                    x0 = cx + math.cos(a) * 30
                    y0 = cy + 6 + math.sin(a) * 10
                    x1 = cx + math.cos(a) * 38
                    y1 = cy + 6 + math.sin(a) * 12
                    P._aaline(s, (*edge, 170), (x0, y0), (x1, y1), 2)
                P._rect(s, (*P.C_OUTLINE, 120), (cx - 2, cy - 2, 4, 16))
                P._rect(s, (*edge, 190), (cx - 1, cy - 1, 2, 14))
                return s

            surf = P._static(("gj_platform", q), build)
            a = 235
            surf.set_alpha(a)
            surface.blit(surf, (int(x - 48), int(y - 26)))
            surf.set_alpha(255)

        @staticmethod
        def _draw_blade_fury_ground(surface, hero, x, y, timer, phase):
            """Q Blade Fury (tanah): marker angular + retakan + spiral."""
            P = GrimjawV1Renderer
            prog = P._skill_progress("q", timer)
            env = P._skill_steady(prog)
            if env <= 0.0:
                return
            rng_world = int(getattr(hero, "skill_range", 70) or 70)
            r = P._ring_r(hero, rng_world, surface)
            # PENTING: marker angular dipusatkan TEPAT di (x, y) sebagai
            # LINGKARAN penuh - tooling memverifikasi radius dunia dari
            # titik jangkar ke segala arah.
            cy = y
            seed = int(phase * 7)
            P._aoe_marks(surface, x, cy, r, P.C_FIRE_MID, int(215 * env),
                         phase, squash=1.0, ticks=26,
                         tick_len=max(6, int(r * 0.10)))
            P._dashed_ring(surface, x, cy, int(r * 0.8), P.C_FIRE_DARK,
                           int(120 * env), phase, dashes=9, width=2,
                           squash=0.5)
            for i in range(3):
                a = i * (math.tau / 3) + 0.4
                P._jagged_crack(surface, x, cy, a, r * 0.5,
                                (P.C_FIRE_DARKEST, P.C_FIRE_DARK),
                                int(150 * env), seed + 2 + i,
                                width=2, segments=3)
            P._rect(surface, (*P.C_FIRE_DARKEST, int(55 * env)),
                    (int(x - r * 0.35), int(cy - 6),
                     int(r * 0.7), 12))
            for i in range(4):
                ex = x + (P._hash01(seed + 6 + i * 3) - 0.5) * r * 0.44
                P._rect(surface, (*P.C_FIRE_MID, int(90 * env)),
                        (int(ex), int(cy - 2 + (i % 2) * 4), 3, 2))
            for k in range(4):
                a = k * (math.pi / 2) + math.pi / 4
                bx = x + math.cos(a) * r * 0.97
                by = cy + math.sin(a) * r * 0.5
                P._chevron(surface, bx, by,
                           a + math.pi if math.cos(a) < 0 else a,
                           9, P.C_FIRE_LIGHT, int(190 * env), 2)
            if prog < 0.22:
                t = prog / 0.22
                P._aoe_marks(surface, x, cy, int(r * (1.0 - 0.55 * t)),
                             P.C_FIRE_LIGHT, int(210 * (1.0 - t * 0.4)),
                             phase * 2.0, squash=1.0, ticks=12,
                             tick_len=max(5, int(r * 0.08)))
                P._spark_star(surface, x, cy, 16 + int(10 * t),
                              P.C_FIRE_LIGHT, int(200 * (1 - t * 0.5)),
                              6, rot=phase)

        @staticmethod
        def _draw_blade_fury_rings(surface, x, y, phase):
            """Q Blade Fury (depan): busur titik tipis + percik tepi.

            Disiplin V1: massa spiral hidup di lapisan TANAH; depan
            hanya busur putus-putus dan spark sehingga badan tetap
            terbaca penuh saat Q aktif.
            """
            P = GrimjawV1Renderer
            for k in range(2):
                rx = 40 - k * 8
                ry = 13 - k * 3
                a0 = phase * (2.2 + k * 0.8) * (1 if k % 2 == 0 else -1)
                col = P.C_FIRE_MID if k % 2 == 0 else P.C_FIRE_LIGHT
                for i in range(8):
                    a = a0 + 2.0 * i / 8
                    px = x + math.cos(a) * rx
                    py = y + math.sin(a) * ry
                    P._rect(surface, (*col, 170 - k * 40),
                            (int(px) - 1, int(py) - 1, 3, 3))
            for i in range(3):
                a = phase * 2.0 + i * (math.tau / 3)
                P._spark_star(surface, x + math.cos(a) * 36,
                              y + math.sin(a) * 12, 4, P.C_FIRE_HOT,
                              200, 4, rot=phase + i)

        @staticmethod
        def _draw_fire_particles_orbit(surface, x, y, phase):
            """Bara mengorbit badan (Blade Fury)."""
            P = GrimjawV1Renderer
            for i in range(5):
                a = phase * 2.4 + i * (math.tau / 5)
                ox = math.cos(a) * 24
                oy = -30 + math.sin(a) * 9
                col = P.C_FIRE_LIGHT if i % 2 else P.C_FIRE_HOT
                px, py = int(x + ox), int(y + oy)
                P._spark_star(surface, px, py, 4, col, 210, 4,
                              rot=phase + i)
                pygame.draw.line(
                    surface, (*col, 120), (px, py),
                    (px - int(math.cos(a) * 5),
                     py - int(math.sin(a) * 2)), 1)

        @staticmethod
        def _draw_spin_flame_sweep(surface, cx, cy, f, spin_phase, phase):
            """Sapuan api berputar (Blade Fury): busur titik + percik."""
            P = GrimjawV1Renderer
            for k in range(3):
                rx = 37 - k * 6
                ry = 13 - k * 2
                a0 = spin_phase * (1.0 if k % 2 == 0 else -1.3) + k * 2.2
                col = P.C_FIRE_MID if k % 2 == 0 else P.C_FIRE_LIGHT
                for i in range(10):
                    a = a0 + 2.2 * i / 10
                    wob = 1.0 + (P._hash01(
                        int(spin_phase * 4) * 7 + k * 13 + i) - 0.5) * 0.1
                    px = cx + math.cos(a) * rx * wob
                    py = cy - 8 + math.sin(a) * ry * wob
                    sz = 3 - k
                    P._rect(surface, (*col, 215 - k * 35),
                            (int(px) - sz // 2, int(py) - sz // 2,
                             max(2, sz), max(2, sz)))
            for i in range(4):
                a = spin_phase * 1.5 + i * (math.tau / 4)
                P._spark_star(surface, cx + math.cos(a) * 34,
                              cy - 8 + math.sin(a) * 11, 4,
                              P.C_FIRE_HOT, 220, 4, rot=phase + i)

        # ==================================================================
        # W HEALING WARD - cincin hijau + totem + halo
        # ==================================================================
        @staticmethod
        def _draw_healing_ward_ground(surface, hero, x, y, timer, phase):
            """W Healing Ward (tanah): cincin hijau + salib + mote naik."""
            P = GrimjawV1Renderer
            prog = P._skill_progress("w", timer)
            env = P._skill_steady(prog)
            if env <= 0.0:
                return
            wp = getattr(hero, "_heal_ward_pos", None)
            if wp:
                tx, ty = P._world_to_local(hero, x, y, wp[0], wp[1])
            else:
                tx, ty = x, y
            r = P._ring_r(hero, 90, surface)
            seed = int(phase * 7)
            P._dashed_ring(surface, tx, ty + 6, r, P.C_HEAL_MID,
                           int(200 * env), phase, dashes=12, width=3,
                           squash=0.62)
            for k in range(4):
                a = k * (math.pi / 2)
                px = tx + math.cos(a) * r * 0.78
                py = ty + 6 + math.sin(a) * r * 0.42
                P._rect(surface, (*P.C_HEAL_LIGHT, int(190 * env)),
                        (int(px) - 4, int(py) - 1, 8, 2))
                P._rect(surface, (*P.C_HEAL_LIGHT, int(190 * env)),
                        (int(px) - 1, int(py) - 4, 2, 8))
            for i in range(4):
                ex = tx + (P._hash01(seed + 9 + i * 3) - 0.5) * r * 2.2
                ey = ty + 2 - ((phase * 8 + i * 6) % 16)
                P._rect(surface, (*P.C_HEAL_LIGHT, int(160 * env)),
                        (int(ex), int(ey), 2, 2))
            P._rect(surface, (*P.C_HEAL_DARK, int(70 * env)),
                    (int(tx - r * 0.32), int(ty + 6 - r * 0.06),
                     int(r * 0.64), max(2, int(r * 0.12))))
            if prog < 0.25:
                P._spark_star(surface, tx, ty + 4, 14, P.C_HEAL_CORE,
                              220, 6, rot=phase)

        @staticmethod
        def _draw_healing_ward_totem(surface, hero, x, y, timer, phase):
            """Totem ward pixel: tiang + kepala + daun + glow (cache)."""
            P = GrimjawV1Renderer
            prog = P._skill_progress("w", timer)
            env = P._skill_steady(prog)
            if env <= 0.05:
                return
            wp = getattr(hero, "_heal_ward_pos", None)
            if wp:
                tx, ty = P._world_to_local(hero, x, y, wp[0], wp[1])
            else:
                # Tanpa posisi ward: totem berdiri di sisi belakang badan
                # (tetap di dalam cincin) supaya tidak tertutup sprite.
                f = getattr(hero, "direction", 1)
                f = -1 if f < 0 else 1
                tx, ty = x - f * 40, y
            q = int(phase * 2) % 6

            def build():
                s = pygame.Surface((48, 88), pygame.SRCALPHA)
                # Tiang kayu + sabuk.
                P._rect(s, (*P.C_OUTLINE, 255), (15, 24, 18, 60))
                P._rect(s, (*P.C_ARMOR_MID, 255), (17, 26, 14, 56))
                P._rect(s, (*P.C_ARMOR_DARK, 255), (25, 26, 6, 56))
                for by in (34, 52, 70):
                    P._rect(s, (*P.C_GOLD_DARK, 255), (17, by, 14, 2))
                # Kepala totem + mata hijau.
                P._rect(s, (*P.C_OUTLINE, 255), (13, 6, 22, 20))
                P._rect(s, (*P.C_MASK_LIGHT, 255), (15, 8, 18, 16))
                P._rect(s, (*P.C_MASK_MID, 255), (27, 8, 6, 16))
                P._rect(s, (*P.C_HEAL_MID, 255), (19, 13, 3, 4))
                P._rect(s, (*P.C_HEAL_MID, 255), (26, 13, 3, 4))
                P._rect(s, (*P.C_HEAL_CORE, 255), (20, 14, 1, 1))
                P._rect(s, (*P.C_HEAL_CORE, 255), (27, 14, 1, 1))
                P._rect(s, (*P.C_OUTLINE, 220), (21, 21, 6, 1))
                # Daun tuft di puncak.
                for i, dx in enumerate((-5, 0, 5)):
                    leaf = P.C_HEAL_MID if i != 1 else P.C_HEAL_LIGHT
                    P._rect(s, (*leaf, 240), (24 + dx - 2, 0, 4, 7))
                    P._rect(s, (*P.C_HEAL_CORE, 240),
                            (24 + dx - 1, 1, 2, 3))
                # Salib kecil di tiang.
                P._rect(s, (*P.C_HEAL_LIGHT, 190), (23, 42, 2, 10))
                P._rect(s, (*P.C_HEAL_LIGHT, 190), (19, 45, 10, 2))
                return s

            surf = P._static(("gj_totem", q), build)
            a = int(255 * min(1.0, env + 0.15))
            surf.set_alpha(a)
            surface.blit(surf, (int(tx - 24), int(ty - 12)))
            surf.set_alpha(255)

        @staticmethod
        def _draw_heal_aura(surface, x, y, phase):
            """Halo penyembuh: cincin + titik hijau lembut."""
            P = GrimjawV1Renderer
            P._dashed_ring(surface, x, y - 8, 46, P.C_HEAL_MID, 38,
                           phase * 0.4, dashes=12, width=2, squash=0.85)
            P._dashed_ring(surface, x, y - 8, 32, P.C_HEAL_LIGHT, 30,
                           -phase * 0.3, dashes=9, width=2, squash=0.85)
            for i in range(5):
                a = phase * 0.5 + i * math.tau / 5
                ex = x + math.cos(a) * 46
                ey = y - 8 + math.sin(a) * 46 * 0.85
                P._rect(surface, (*P.C_HEAL_LIGHT, 55),
                        (int(ex), int(ey), 2, 2))

        # ==================================================================
        # E CRITICAL STRIKE - chevron konvergen + cincin gold
        # ==================================================================
        @staticmethod
        def _draw_crit_telegraph(surface, hero, x, y, timer, phase):
            """E Critical Strike (fase cast): chevron + ring mengecil."""
            P = GrimjawV1Renderer
            prog = P._skill_progress("e", timer)
            if prog > 0.30:
                return
            t = prog / 0.30
            tx, ty = P._target_position(hero, x, y)
            ang = math.atan2(ty - (y - 10), tx - x)
            for i in range(3):
                d = 46 - i * 12 - t * 18
                cxp = x + math.cos(ang) * d
                cyp = y - 10 + math.sin(ang) * d
                P._chevron(surface, cxp, cyp, ang, 10 + i * 3,
                           P.C_GOLD_LIGHT, int(200 - 30 * i), 3)
            P._spark_star(surface, x, y - 10, int(14 + 6 * t),
                          P.C_GOLD_LIGHT, 160, 5, rot=phase)
            P._dashed_ring(surface, x, y - 6, int(30 - 14 * t),
                           P.C_GOLD_MID, 180, phase, dashes=8, width=2,
                           squash=0.35)
            for i in range(3):
                d0 = 12 + i * 6
                x0 = x + math.cos(ang) * d0
                y0 = y - 10 + math.sin(ang) * d0
                x1 = x + math.cos(ang) * (d0 + 9)
                y1 = y - 10 + math.sin(ang) * (d0 + 9)
                P._aaline(surface, (*P.C_GOLD_MID, int(120 * (1 - t))),
                          (x0, y0), (x1, y1), 1)

        @staticmethod
        def _draw_crit_steady(surface, hero, x, y, timer, phase):
            """E Critical Strike (steady): cincin gold + kilau orbit."""
            P = GrimjawV1Renderer
            prog = P._skill_progress("e", timer)
            env = P._skill_steady(prog)
            if env <= 0.0:
                return
            pulse = 0.6 + 0.4 * math.sin(phase * 3)
            r = P._ring_r(hero, 26, surface)
            P._dashed_ring(surface, x, y - 8, r, P.C_GOLD_LIGHT,
                           int(190 * env * pulse), phase * 2.0,
                           dashes=8, width=2, squash=1.0)
            P._dashed_ring(surface, x, y - 8, int(r * 0.7),
                           P.C_GOLD_MID, int(150 * env), -phase * 1.5,
                           dashes=6, width=2, squash=0.5)
            for i in range(3):
                a = phase * 2.0 + i * (math.tau / 3)
                P._spark_star(surface, x + math.cos(a) * r * 1.1,
                              y - 8 + math.sin(a) * r * 0.4, 6,
                              P.C_GOLD_SHINE, int(200 * env), 4,
                              rot=phase + i)

        # ==================================================================
        # R OMNISLASH - ring tanah + tebasan perimeter + crosshair target
        # ==================================================================
        @staticmethod
        def _draw_omnislash_ground(surface, hero, x, y, timer, phase):
            """R Omnislash (tanah): ring besar + tanda X + retakan."""
            P = GrimjawV1Renderer
            prog = P._skill_progress("r", timer)
            env = P._skill_steady(prog, 4.0)
            if env <= 0.0:
                return
            r = P._ring_r(hero, 80, surface)
            cy = y + 4
            seed = int(phase * 7)
            P._dashed_ring(surface, x, cy, r, P.C_RAGE_MID,
                           int(200 * env), phase, dashes=12, width=3,
                           squash=0.5)
            P._dashed_ring(surface, x, cy, int(r * 0.55),
                           P.C_RAGE_DARK, int(140 * env), -phase,
                           dashes=8, width=2, squash=0.3)
            for i in range(4):
                a = i * (math.tau / 4) + phase * 0.6
                px = x + math.cos(a) * r * 0.75
                py = cy + math.sin(a) * r * 0.35
                P._aaline(surface, (*P.C_RAGE_LIGHT, int(190 * env)),
                          (px - 5, py - 5), (px + 5, py + 5), 2)
                P._aaline(surface, (*P.C_RAGE_LIGHT, int(190 * env)),
                          (px - 5, py + 5), (px + 5, py - 5), 2)
            for i in range(5):
                a = i * (math.tau / 5) + 0.3
                P._jagged_crack(surface, x, cy, a, r * 0.6,
                                (P.C_RAGE_DARK, P.C_RAGE_MID),
                                int(140 * env), seed + 10 + i,
                                width=2, segments=3)

        @staticmethod
        def _draw_omnislash_slashes(surface, hero, x, y, timer, phase):
            """R Omnislash (depan): tebasan pendek di perimeter badan.

            Disiplin V1: tebasan legacy menyilang TENGAH badan; versi
            pixel menyerang di sekeliling siluet (cincin rx 55 / ry 30
            di sekitar dada) sehingga Grimjaw tetap terbaca penuh.
            """
            P = GrimjawV1Renderer
            prog = P._skill_progress("r", timer)
            env = P._skill_steady(prog, 4.0)
            if env <= 0.3:
                return
            seed = int(phase * 4)
            for i in range(4):
                a = phase * 7.0 + i * (math.tau / 4)
                L = 30 + 10 * P._hash01(seed + i)
                cxp = x + math.cos(a) * 55
                cyp = y - 18 + math.sin(a) * 30
                d = a + 1.2
                dx, dy = math.cos(d), math.sin(d)
                p0 = (cxp - dx * L / 2, cyp - dy * L / 2)
                p1 = (cxp + dx * L / 2, cyp + dy * L / 2)
                alpha = int(210 * env)
                P._aaline(surface, (*P.C_OUTLINE, int(alpha * 0.5)),
                          p0, p1, 5)
                P._aaline(surface, (*P.C_RAGE_LIGHT, alpha), p0, p1, 3)
                P._aaline(surface, (*P.C_RAGE_BRIGHT, min(255, alpha + 40)),
                          p0, p1, 1)
                P._spark_star(surface, p1[0], p1[1], 6, P.C_FIRE_HOT,
                              int(180 * env), 4, rot=phase + i)

        @staticmethod
        def _draw_omnislash_target(surface, hero, x, y, timer, phase):
            """R Omnislash: crosshair di target."""
            P = GrimjawV1Renderer
            prog = P._skill_progress("r", timer)
            env = P._skill_steady(prog, 4.0)
            if env <= 0.0:
                return
            tx, ty = P._target_position(hero, x, y)
            pulse = 0.55 + 0.45 * math.sin(phase * 4)
            alpha = int(210 * env)
            P._aaline(surface, (*P.C_RAGE_LIGHT, alpha),
                      (tx - 11, ty - 11), (tx + 11, ty + 11), 3)
            P._aaline(surface, (*P.C_RAGE_LIGHT, alpha),
                      (tx - 11, ty + 11), (tx + 11, ty - 11), 3)
            P._dashed_ring(surface, tx, ty, 16, P.C_RAGE_BRIGHT,
                           int(200 * env * pulse), phase * 2.0,
                           dashes=8, width=2, squash=1.0)
            for k in range(4):
                a = k * (math.pi / 2)
                x0 = tx + math.cos(a) * 19
                y0 = ty + math.sin(a) * 19
                x1 = tx + math.cos(a) * 25
                y1 = ty + math.sin(a) * 25
                pygame.draw.line(surface, (*P.C_RAGE_BRIGHT, alpha),
                                 (round(x0), round(y0)),
                                 (round(x1), round(y1)), 2)
            P._spark_star(surface, tx, ty, 6, P.C_RAGE_BRIGHT,
                          int(220 * env), 4, rot=phase)

        # ---------- Attack swing trail + slash + impact (fallback) ----------
        @staticmethod
        def _draw_blade_swing_trail(surface, cx, cy, f, phase, ap):
            """Ekor api mengikuti jalur ujung pedang (pixel)."""
            P = GrimjawV1Renderer
            p0 = max(P.ATTACK_WINDUP_END, ap - 0.20)
            steps = 7
            prev = None
            for i in range(steps + 1):
                t = i / steps
                pr = p0 + (ap - p0) * t
                tip = P._blade_tip_local(phase, "attack", pr)
                cur = (cx + tip[0] * f, cy + tip[1])
                if prev is not None:
                    wgt = 0.30 + 0.70 * t
                    alpha = int(205 * wgt)
                    wdt = max(2, int(8 * wgt))
                    j = (P._hash01(int(pr * 90) + i) - 0.5) * 2.4
                    mx = (prev[0] + cur[0]) / 2
                    my = (prev[1] + cur[1]) / 2 + j * 0.4
                    P._rect(surface, (*P.C_FIRE_DARK, int(alpha * 0.6)),
                            (int(mx - wdt / 2), int(my - wdt / 2),
                             wdt, wdt))
                    inner = max(1, wdt // 2)
                    P._rect(surface, (*P.C_FIRE_LIGHT, alpha),
                            (int(mx - inner / 2), int(my - inner / 2),
                             inner, inner))
                prev = cur

        @staticmethod
        def _draw_fire_slash_arc(surface, x, y, facing, progress,
                                 crit=False, phase=0.0):
            """Sabit tebasan pixel - ATAS -> BAWAH, kepala di ujung pedang.

            Titik-titik sabit diambil dari posisi ujung pedang SEBENARNYA
            (fungsi pose yang sama dengan rig) sehingga arah tebasan tidak
            mungkin berlawanan dengan pedang (kontrak test arah tebasan).
            """
            P = GrimjawV1Renderer
            p0 = P.ATTACK_WINDUP_END - 0.02
            p1 = P.ATTACK_SWING_END
            if progress < p0 or progress > 0.92:
                return
            fsign = 1 if facing >= 0 else -1
            travel = max(0.0, min(1.0, (progress - p0) / (p1 - p0)))
            travel = travel ** 1.35
            fade = 1.0
            if progress > p1:
                fade = 1.0 - (progress - p1) / (0.92 - p1)
            fade = max(0.0, min(1.0, fade))
            if fade <= 0.0:
                return
            steps = 14
            pts = []
            for i in range(steps + 1):
                s = (i + 1) / steps
                pr = p0 + (progress - p0) * s
                tipx, tipy = P._blade_tip_local(phase, "attack", pr)
                pts.append((x + tipx * fsign, y + tipy))
            base = 9 if crit else 8
            for i in range(steps):
                s = (i + 1) / steps
                taper = 0.3 + 0.7 * (s ** 1.6)
                alpha = int((40 + 205 * (s ** 1.5)) * fade)
                if alpha <= 0:
                    continue
                a, b = pts[i], pts[i + 1]
                seg_len = math.hypot(b[0] - a[0], b[1] - a[1])
                dots = max(1, int(seg_len / 3))
                for d in range(dots + 1):
                    u = d / max(1, dots)
                    mx = a[0] + (b[0] - a[0]) * u
                    my = a[1] + (b[1] - a[1]) * u
                    wdt = max(2, int(base * taper))
                    P._rect(surface, (*P.C_FIRE_DARK, int(alpha * 0.55)),
                            (int(mx - wdt / 2), int(my - wdt / 2),
                             wdt, wdt))
                    mid = max(2, int(base * taper * 0.62))
                    P._rect(surface, (*P.C_FIRE_MID, alpha),
                            (int(mx - mid / 2), int(my - mid / 2),
                             mid, mid))
                    core = max(1, int(base * taper * 0.3))
                    P._rect(surface, (*P.C_FIRE_LIGHT, alpha),
                            (int(mx - core / 2), int(my - core / 2),
                             core, core))
            tipx, tipy = P._blade_tip_local(phase, "attack", progress)
            hx = x + tipx * fsign
            hy = y + tipy
            head_a = fade * (0.5 + 0.5 * travel)
            arc_scale = 1.25 if crit else 1.0
            P._spark_star(surface, hx, hy, 15 * arc_scale,
                          P.C_FIRE_LIGHT, int(215 * head_a), 6,
                          rot=phase + progress * 9)
            P._spark_star(surface, hx, hy, 8 * arc_scale, P.C_FIRE_HOT,
                          int(250 * head_a), 5, rot=phase)
            P._rect(surface, (*P.C_FIRE_CORE, int(230 * head_a)),
                    (int(hx) - 2, int(hy) - 2, 4, 4))

        @staticmethod
        def _draw_impact_flash(surface, x, y, facing, progress, crit=False):
            """Pop benturan pixel: bintang + cincin + garis kecepatan."""
            P = GrimjawV1Renderer
            if not (0.52 < progress < 0.86):
                return
            t = (progress - 0.52) / 0.34
            env = math.sin(math.pi * t)
            if env <= 0.05:
                return
            fsign = 1 if facing >= 0 else -1
            tipx, tipy = P._blade_tip_local(
                0.0, "attack", min(progress, P.ATTACK_SWING_END))
            ix = x + tipx * fsign
            iy = y + tipy
            r = (13 if crit else 10) * (0.6 + 0.5 * env)
            alpha = int(235 * env)
            P._spark_star(surface, ix, iy, r * 1.25, P.C_FIRE_LIGHT,
                          int(alpha * 0.45), 4, rot=progress * 9)
            P._spark_star(surface, ix, iy, r, P.C_FIRE_HOT, alpha,
                          7 if crit else 6, rot=progress * 7)
            P._spark_star(surface, ix, iy, r * 0.5, P.C_FIRE_CORE,
                          min(255, alpha + 30), 4, rot=progress * 5)
            P._dashed_ring(surface, ix, iy, int(r * 1.5), P.C_FIRE_MID,
                           int(alpha * 0.5), progress * 6.0,
                           dashes=8, width=2, squash=1.0)
            back = math.pi if fsign > 0 else 0.0
            for i in range(3):
                d0 = 6 + i * 5
                x0 = ix + math.cos(back) * d0
                y0 = iy + math.sin(back) * d0 * 0.5
                x1 = ix + math.cos(back) * (d0 + 8)
                y1 = iy + math.sin(back) * (d0 + 8) * 0.5
                P._aaline(surface, (*P.C_OUTLINE, int(alpha * 0.5)),
                          (x0, y0), (x1, y1), 1)

        @staticmethod
        def _draw_critical_strike_burst(surface, x, y, facing, progress):
            """Ledakan crit pixel: bintang besar + cincin + percik."""
            P = GrimjawV1Renderer
            if not (0.56 < progress < 0.82):
                return
            t = (progress - 0.56) / 0.26
            env = math.sin(math.pi * t)
            if env <= 0.05:
                return
            fsign = 1 if facing >= 0 else -1
            tipx, tipy = P._blade_tip_local(0.0, "attack",
                                            P.ATTACK_SWING_END)
            ix = x + tipx * fsign
            iy = y + tipy
            r = 16 + 14 * env
            P._spark_star(surface, ix, iy, r, P.C_GOLD_LIGHT,
                          int(240 * env), 8, rot=progress * 8)
            P._spark_star(surface, ix, iy, r * 0.55, P.C_FIRE_HOT,
                          min(255, int(255 * env)), 5, rot=progress * 6)
            P._dashed_ring(surface, ix, iy, int(r * 1.15),
                           P.C_GOLD_MID, int(190 * env), progress * 6.0,
                           dashes=9, width=2, squash=1.0)
            for i in range(5):
                a = i * (math.tau / 5) + progress * 3.0
                px = ix + math.cos(a) * r * 1.35
                py = iy + math.sin(a) * r * 1.1
                P._spark_star(surface, px, py, 5, P.C_GOLD_SHINE,
                              int(200 * env), 4, rot=progress * 4 + i)

        # ------------------------------------------------------------------
        # Fallback projectile and the draw orchestrator.
        # ------------------------------------------------------------------
        class FlameWaveProjectile:
            """Gelombang api basic attack: MURNI VISUAL (damage=0).

            Dilepas dari ujung bilah di titik rilis ayunan; touchdown
            hanya percikan lembut - TANPA ImpactFX / hit-stop / shake
            (kontrak tools/test_basic_attack_no_impact_fx.py).
            """

            def __init__(self, sx, sy, tx, ty, speed=6.5,
                         target=None, damage=0, team=None):
                self.x, self.y = float(sx), float(sy)
                self.tx, self.ty = float(tx), float(ty)
                self.speed = float(speed)
                self.alive = True
                self.age = 0
                self.dead_frames = 0
                self.trail = []
                self.target = target
                self.damage = 0
                self.team = team
                self.angle = math.atan2(ty - sy, tx - sx)
                self.source = None
                self.cx = self.cy = 0

            def update(self):
                if not self.alive:
                    self.dead_frames += 1
                    return
                self.age += 1
                if self.age > 40:
                    self.alive = False
                    return
                if self.target is not None and getattr(
                        self.target, "alive", False):
                    self.tx, self.ty = float(self.target.x), float(
                        self.target.y)
                dx, dy = self.tx - self.x, self.ty - self.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    self.angle = math.atan2(dy, dx)
                if dist <= self.speed + 4:
                    self.alive = False
                    return
                self.trail.append((self.x, self.y))
                if len(self.trail) > 10:
                    self.trail.pop(0)
                self.x += dx / dist * self.speed
                self.y += dy / dist * self.speed

            def draw(self, surface, phase):
                P = GrimjawV1Renderer
                if not self.alive:
                    # Touchdown lembut: percikan memudar, tanpa impact FX.
                    t = max(0.0, 1.0 - self.dead_frames / 10.0)
                    if t > 0:
                        P._spark_star(surface, self.x, self.y, 10 * t,
                                      P.C_FIRE_LIGHT, int(160 * t), 4,
                                      rot=phase)
                    return
                for i, (tx, ty) in enumerate(self.trail):
                    a = int(30 + 110 * i / max(1, len(self.trail) - 1))
                    sz = max(2, 5 - (len(self.trail) - i) // 3)
                    P._rect(surface, (*P.C_FIRE_DARK, a),
                            (int(tx) - sz // 2, int(ty) - sz // 2,
                             sz, sz))
                # Kepala busur: 3 lapis kotak api + inti panas.
                dx, dy = math.cos(self.angle), math.sin(self.angle)
                nx, ny = -dy, dx
                wid = 10 + math.sin(phase * 6 + self.age) * 2
                P._rect(surface, (*P.C_FIRE_DARK, 200),
                        (int(self.x - wid / 2), int(self.y - 3),
                         int(wid), 6))
                P._rect(surface, (*P.C_FIRE_MID, 220),
                        (int(self.x + dx * 3 - wid / 2 + 2),
                         int(self.y + dy * 3 - 2), int(wid) - 4, 4))
                hx = self.x + dx * 6 + nx * math.sin(phase * 9) * 2
                hy = self.y + dy * 6 + ny * math.sin(phase * 9) * 2
                P._rect(surface, (*P.C_FIRE_HOT, 235),
                        (int(hx) - 2, int(hy) - 2, 4, 4))
                P._rect(surface, (*P.C_FIRE_CORE, 235),
                        (int(hx) - 1, int(hy) - 1, 2, 2))

        class CritWaveProjectile(FlameWaveProjectile):
            """Varian emas saat buff crit / serangan crit aktif."""

            def draw(self, surface, phase):
                P = GrimjawV1Renderer
                if not self.alive:
                    t = max(0.0, 1.0 - self.dead_frames / 10.0)
                    if t > 0:
                        P._spark_star(surface, self.x, self.y, 12 * t,
                                      P.C_GOLD_LIGHT, int(180 * t), 5,
                                      rot=phase)
                        P._dashed_ring(surface, self.x, self.y,
                                       14 * t + 4, P.C_GOLD_MID,
                                       int(150 * t), phase,
                                       dashes=8, width=2, squash=1.0)
                    return
                for i, (tx, ty) in enumerate(self.trail):
                    a = int(30 + 120 * i / max(1, len(self.trail) - 1))
                    sz = max(2, 5 - (len(self.trail) - i) // 3)
                    P._rect(surface, (*P.C_GOLD_DARK, a),
                            (int(tx) - sz // 2, int(ty) - sz // 2,
                             sz, sz))
                dx, dy = math.cos(self.angle), math.sin(self.angle)
                wid = 11 + math.sin(phase * 6 + self.age) * 2
                P._rect(surface, (*P.C_GOLD_DARK, 210),
                        (int(self.x - wid / 2), int(self.y - 3),
                         int(wid), 6))
                P._rect(surface, (*P.C_GOLD_MID, 230),
                        (int(self.x + dx * 3 - wid / 2 + 2),
                         int(self.y + dy * 3 - 2), int(wid) - 4, 4))
                hx, hy = self.x + dx * 6, self.y + dy * 6
                P._rect(surface, (*P.C_GOLD_SHINE, 240),
                        (int(hx) - 2, int(hy) - 2, 4, 4))
                P._spark_star(surface, self.x, self.y, 8,
                              P.C_GOLD_LIGHT, 170, 4, rot=phase)

        @staticmethod
        def _manage_projectiles(hero, surface, phase):
            if getattr(hero, "_skip_renderer_projectiles", False):
                return
            items = getattr(hero, "_gj_projectiles", None)
            if items is None:
                hero._gj_projectiles = []
                items = hero._gj_projectiles
            for proj in items:
                proj.update()
                proj.draw(surface, phase)
            hero._gj_projectiles[:] = [p for p in items
                                       if p.alive or p.dead_frames < 10]

        @staticmethod
        def _spawn_flame_wave(hero, x, y):
            if getattr(hero, "_skip_renderer_projectiles", False):
                return
            items = getattr(hero, "_gj_projectiles", None)
            if items is None:
                items = []
                hero._gj_projectiles = items
            P = GrimjawV1Renderer
            tx, ty = P._target_position(hero, x, y)
            f = getattr(hero, "direction", 1)
            sx, sy = P._blade_tip_position(
                x, y, f, float(getattr(hero, "pulse", 0.0)), "attack",
                float(getattr(hero, "_gj_attack_progress", 0.0)))
            proj = P.FlameWaveProjectile(
                sx, sy, tx, ty, speed=6.5,
                target=getattr(hero, "target", None),
                team=getattr(hero, "team", None))
            proj.source, proj.cx, proj.cy = hero, x, y
            items.append(proj)

        @staticmethod
        def _spawn_crit_wave(hero, x, y):
            if getattr(hero, "_skip_renderer_projectiles", False):
                return
            items = getattr(hero, "_gj_projectiles", None)
            if items is None:
                items = []
                hero._gj_projectiles = items
            P = GrimjawV1Renderer
            tx, ty = P._target_position(hero, x, y)
            f = getattr(hero, "direction", 1)
            sx, sy = P._blade_tip_position(
                x, y, f, float(getattr(hero, "pulse", 0.0)), "attack",
                float(getattr(hero, "_gj_attack_progress", 0.0)))
            proj = P.CritWaveProjectile(
                sx, sy, tx, ty, speed=7.0,
                target=getattr(hero, "target", None),
                team=getattr(hero, "team", None))
            proj.source, proj.cx, proj.cy = hero, x, y
            items.append(proj)

        # ------------------------------------------------------------------
        # Pose modes (cermin dispatch legacy + proyektil canvas V1).
        # ------------------------------------------------------------------
        @staticmethod
        def _draw_grimjaw_idle(surface, hero, x, y, fury=False, ward=False,
                               crit=False, omni=False):
            P = GrimjawV1Renderer
            bob = int(math.sin(hero.pulse * 0.7) * 3)
            portrait = bool(getattr(hero, "_portrait_hd", False))
            if not portrait:
                P._draw_shadow(surface, x, y + 72)
                P._draw_fire_mist(surface, x, y + 56, hero.pulse)
            P._draw_grimjaw_body(surface, x, y + bob, hero.direction,
                                 hero.pulse, "idle", detail=portrait,
                                 fury=fury, ward=ward, crit=crit, omni=omni)

        @staticmethod
        def _draw_grimjaw_walk(surface, hero, x, y, fury=False, ward=False,
                               crit=False, omni=False):
            P = GrimjawV1Renderer
            phase = hero.pulse * 2.0
            bob = int(abs(math.sin(phase * 1.2)) * 4)
            sway = int(math.sin(phase) * 3)
            portrait = bool(getattr(hero, "_portrait_hd", False))
            if not portrait:
                P._draw_shadow(surface, x + sway, y + 72)
                P._draw_fire_mist(surface, x + sway, y + 56, phase,
                                  trail=True, facing=hero.direction)
            P._draw_grimjaw_body(surface, x + sway, y - bob, hero.direction,
                                 phase, "walk", detail=portrait,
                                 fury=fury, ward=ward, crit=crit, omni=omni)

        @staticmethod
        def _draw_grimjaw_attack(surface, hero, x, y, crit=False,
                                 omni=False):
            P = GrimjawV1Renderer
            progress = max(0.0, min(1.0, float(
                getattr(hero, "_gj_attack_progress", 0.0))))
            crit = crit or getattr(hero, "_gj_crit_active", False)
            portrait = bool(getattr(hero, "_portrait_hd", False))

            # Body lunge: puncak TEPAT saat pedang mendarat (SWING_END).
            if progress < P.ATTACK_WINDUP_END:
                lunge = int(-3.0 * (progress / P.ATTACK_WINDUP_END))
            elif progress < P.ATTACK_SWING_END:
                t = ((progress - P.ATTACK_WINDUP_END) /
                     (P.ATTACK_SWING_END - P.ATTACK_WINDUP_END))
                lunge = int(-3.0 + 10.0 * (t ** 1.6))
            else:
                t = ((progress - P.ATTACK_SWING_END) /
                     (1.0 - P.ATTACK_SWING_END))
                lunge = int(7.0 * (1.0 - t))
            lunge *= hero.direction

            if not portrait:
                P._draw_shadow(surface, x + lunge, y + 72)
                P._draw_fire_mist(surface, x + lunge, y + 56,
                                  hero.pulse, intense=True)
            P._draw_grimjaw_body(surface, x + lunge, y, hero.direction,
                                 hero.pulse, "attack", progress,
                                 detail=portrait, crit=crit, omni=omni)

            # RELEASE WINDOW - ayunan melepas gelombang api dari ujung
            # bilah tepat di titik rilis (ap 0.5-0.6): varian emas saat
            # crit.  Murni visual (damage=0, tanpa impact FX); Grimjaw
            # melee tidak punya proyektil basic-attack di lapisan hidup,
            # jadi canvas selalu spawn (tidak mungkin dobel).
            if (0.5 < progress < 0.6
                    and not getattr(hero, "_gj_proj_spawned", False)
                    and not portrait):
                if crit:
                    P._spawn_crit_wave(hero, x + lunge, y)
                else:
                    P._spawn_flame_wave(hero, x + lunge, y)
                hero._gj_proj_spawned = True
            if progress < 0.15 or progress > 0.9:
                hero._gj_proj_spawned = False

            # FX tebasan in-canvas (FALLBACK) - dilompati saat lapisan
            # hidup (heroes/grimjaw_fx.py) mengambil alih unit ini.
            if not portrait and not P._FX_LIVE.v:
                P._draw_blade_swing_trail(surface, x + lunge, y,
                                          hero.direction, hero.pulse,
                                          progress)
                P._draw_fire_slash_arc(surface, x + lunge, y,
                                       hero.direction, progress, crit,
                                       hero.pulse)
                P._draw_impact_flash(surface, x + lunge, y,
                                     hero.direction, progress, crit)
                if crit and 0.56 < progress < 0.82:
                    P._draw_critical_strike_burst(surface, x + lunge, y,
                                                  hero.direction, progress)

        @staticmethod
        def _draw_grimjaw_blade_fury(surface, hero, x, y, timer, phase):
            """Blade Fury - berputar dengan cincin api pixel."""
            P = GrimjawV1Renderer
            spin_phase = phase * 6
            bob = int(math.sin(spin_phase) * -1)
            # Arah hadap berganti cepat = ilusi berputar (rig sisi 2D).
            facing = 1 if int(spin_phase * 2) % 2 == 0 else -1
            P._draw_shadow(surface, x, y + 72)
            P._draw_fire_mist(surface, x, y + 56, phase * 2, intense=True)
            P._draw_grimjaw_body(surface, x, y + bob, facing, phase,
                                 "spin", spin_phase=spin_phase, fury=True)

        @staticmethod
        def _draw_grimjaw_omnislash(surface, hero, x, y, timer, phase):
            """Omnislash - teleport cepat dengan pose dramatis."""
            P = GrimjawV1Renderer
            flicker_phase = phase * 8
            offset_x = int(math.sin(flicker_phase) * 4)
            offset_y = int(math.cos(flicker_phase * 1.3) * 3)

            P._draw_shadow(surface, x, y + 72)
            P._draw_fire_mist(surface, x, y + 56, phase, intense=True)

            # Afterimage: badai tebasan Grimjaw yang bertumpuk.
            for i in range(4):
                ghost_alpha = 45 + i * 28
                gx = x - int(math.sin(flicker_phase - i * 0.5) * 24)
                gy = y + int(math.cos(flicker_phase - i * 0.5) * 8)
                ghost_ap = max(0.05, 0.85 - i * 0.22)
                P._draw_grimjaw_ghost(surface, gx, gy,
                                      hero.direction, phase,
                                      ghost_alpha, ghost_ap)

            # Badan utama (pose serang) di-cache per bucket fase.
            bucket = int(phase * 12) % 12
            key = ("v1_omni_body", hero.direction, bucket)
            entry = P._OMNI_BUF.get(key)
            if entry is None:
                if len(P._OMNI_BUF) > 16:
                    P._OMNI_BUF.clear()
                buf = pygame.Surface((240, 240), pygame.SRCALPHA)
                P._draw_grimjaw_body(buf, 120, 124, hero.direction,
                                     phase, "attack", 0.6,
                                     detail=False, omni=True)
                box = buf.get_bounding_rect(min_alpha=1)
                if box.width <= 0:
                    box = pygame.Rect(0, 0, 240, 240)
                crop = buf.subsurface(box).copy()
                entry = (crop, box)
                P._OMNI_BUF[key] = entry
            crop, box = entry
            surface.blit(crop, (int(x + offset_x) - 120 + box.x,
                                int(y + offset_y) - 124 + box.y))

        @staticmethod
        def _draw_grimjaw_ghost(surface, cx, cy, facing, phase, alpha,
                                attack_progress=0.6):
            """Afterimage rig penuh untuk jejak omnislash (buffer V1)."""
            P = GrimjawV1Renderer
            f = 1 if facing >= 0 else -1
            q = max(0.0, min(1.0, round(attack_progress / 0.05) * 0.05))
            key = ("v1", f, q)
            entry = P._GHOST_BUF.get(key)
            if entry is None:
                if len(P._GHOST_BUF) > 24:
                    P._GHOST_BUF.clear()
                buf = pygame.Surface((220, 220), pygame.SRCALPHA)
                P._draw_grimjaw_elite(
                    buf, 110, 118, f, 1.0, "attack", q, 0.0, False)
                box = buf.get_bounding_rect(min_alpha=1)
                if box.width <= 0:
                    box = pygame.Rect(0, 0, 220, 220)
                crop = buf.subsurface(box).copy()
                entry = (crop, box)
                P._GHOST_BUF[key] = entry
            crop, box = entry
            crop.set_alpha(alpha)
            surface.blit(crop, (int(cx) - 110 + box.x,
                                int(cy) - 118 + box.y))
            crop.set_alpha(255)

        @staticmethod
        def _draw_grimjaw_hurt(surface, hero, x, y):
            P = GrimjawV1Renderer
            phase = float(getattr(hero, "pulse", 0.0))
            P._draw_grimjaw_body(
                surface, x, y, getattr(hero, "direction", 1), phase,
                "hurt", detail=bool(getattr(hero, "_portrait_hd", False)))

        @staticmethod
        def draw_grimjaw(surface, hero, x, y):
            """Entry point untuk jalur hero dan boss."""
            P = GrimjawV1Renderer
            pulse = float(getattr(hero, "pulse", 0.0))
            active_skill = getattr(hero, "active_skill", None)
            skill_timer = int(getattr(hero, "active_skill_timer", 0) or 0)
            moving = P._detect_moving(hero)
            P._update_attack_anim(hero)
            portrait = bool(getattr(hero, "_portrait_hd", False))

            # Wiring FX hidup: jalur hero lane cukup attach (pipeline
            # heroes/__init__ menggambar lapisannya), jalur BOSS
            # menggambar draw_ground_layer/draw_live_layer sendiri.
            hero_lane = hasattr(hero, "_render_scale")
            if not portrait:
                try:
                    mod = P._live_module()
                    if mod is not None:
                        if hero_lane:
                            mod.attach(hero)
                        else:
                            mod.draw_ground_layer(surface, hero, x, y)
                except Exception:
                    pass
            try:
                P._FX_LIVE.v = (not portrait) and P._fx_live_owned(hero)
            except Exception:
                P._FX_LIVE.v = False

            attacking = (
                getattr(hero, "_gj_attack_active", False)
                or getattr(hero, "timer", 0)
                > getattr(hero, "attack_cooldown", 40) - 15
            )
            alive = bool(getattr(hero, "alive", True))
            hurt = int(getattr(hero, "_gj_hurt_timer", 0) or 0) > 0

            # Q = Blade Fury, W = Healing Ward, E = Critical Strike,
            # R = Omnislash.
            is_blade_fury = active_skill == "q"
            is_healing_ward = active_skill == "w"
            is_crit_buff = active_skill == "e"
            is_omnislash = active_skill == "r"

            fury = is_blade_fury
            ward = is_healing_ward
            crit = is_crit_buff
            omni = is_omnislash

            if not portrait:
                # ---------- Background layers ----------
                if omni:
                    P._draw_rage_aura(surface, x, y, pulse)
                else:
                    P._draw_fire_aura(surface, x, y, pulse)
                P._draw_fire_platform(surface, x, y + 64, pulse,
                                      active_skill)

                # ---------- Skill ground effects (world-space) ----------
                # Massa besar selalu SEBELUM badan (badan berdiri DI ATAS
                # FX, bukan di baliknya).  Totem ward adalah objek dunia
                # sehingga ikut lapisan tanah.
                if is_healing_ward:
                    P._draw_healing_ward_ground(surface, hero, x, y,
                                                skill_timer, pulse)
                    P._draw_healing_ward_totem(surface, hero, x, y,
                                               skill_timer, pulse)
                elif is_crit_buff:
                    P._draw_crit_telegraph(surface, hero, x, y,
                                           skill_timer, pulse)
                elif is_omnislash:
                    P._draw_omnislash_ground(surface, hero, x, y,
                                             skill_timer, pulse)
                elif is_blade_fury:
                    P._draw_blade_fury_ground(surface, hero, x, y,
                                              skill_timer, pulse)

            # ---------- Character body ----------
            if not alive:
                df = min(3, int(getattr(hero, "_gj_death_frame", 0) or 0))
                P._draw_grimjaw_body(
                    surface, x, y, getattr(hero, "direction", 1),
                    pulse, "death", detail=portrait, death_frame=df)
                hero._gj_death_frame = min(3, df + 1)
            elif is_blade_fury:
                P._draw_grimjaw_blade_fury(surface, hero, x, y,
                                           skill_timer, pulse)
            elif is_omnislash:
                P._draw_grimjaw_omnislash(surface, hero, x, y,
                                          skill_timer, pulse)
            elif attacking:
                P._draw_grimjaw_attack(surface, hero, x, y,
                                       crit=crit, omni=omni)
            elif hurt:
                P._draw_grimjaw_hurt(surface, hero, x, y)
            elif moving:
                P._draw_grimjaw_walk(surface, hero, x, y,
                                     fury=fury, ward=ward, crit=crit,
                                     omni=omni)
            else:
                P._draw_grimjaw_idle(surface, hero, x, y,
                                     fury=fury, ward=ward, crit=crit,
                                     omni=omni)

            if not portrait:
                # ---------- Skill foreground: HANYA aksen ringan -----
                P._manage_projectiles(hero, surface, pulse)
                if is_blade_fury:
                    P._draw_blade_fury_rings(surface, x, y + 20, pulse)
                    P._draw_fire_particles_orbit(surface, x, y, pulse)
                if is_healing_ward:
                    P._draw_heal_aura(surface, x, y, pulse)
                if is_crit_buff:
                    P._draw_crit_steady(surface, hero, x, y,
                                        skill_timer, pulse)
                if is_omnislash:
                    P._draw_omnislash_slashes(surface, hero, x, y,
                                              skill_timer, pulse)
                    P._draw_omnislash_target(surface, hero, x, y,
                                             skill_timer, pulse)

                if not hero_lane:
                    try:
                        mod = P._live_module()
                        if mod is not None:
                            mod.draw_live_layer(surface, hero, x, y)
                    except Exception:
                        pass

            if P.DEBUG_CHARACTER:
                P._draw_debug(surface, hero, x, y)

        @staticmethod
        def draw_boss(surface, boss, x, y):
            GrimjawV1Renderer.draw_grimjaw(surface, boss, x, y)

        @staticmethod
        def _draw_debug(surface, hero, x, y):
            P = GrimjawV1Renderer
            pygame.draw.rect(surface, (255, 214, 100),
                             pygame.Rect(int(x - 50), int(y - 90),
                                         100, 150), 1)
            prog = float(getattr(hero, "_gj_attack_progress", 0.0))
            pygame.draw.rect(surface, P.C_OUTLINE,
                             pygame.Rect(int(x - 40), int(y - 105), 80, 5))
            pygame.draw.rect(surface, P.C_FIRE_MID,
                             pygame.Rect(int(x - 40), int(y - 105),
                                         int(80 * prog), 5))
            tip = P._blade_tip_local(float(getattr(hero, "pulse", 0.0)),
                                     "attack", prog)
            f = getattr(hero, "direction", 1)
            pygame.draw.circle(surface, (255, 64, 48),
                               (int(x + tip[0] * f), int(y + tip[1])), 3)

        # Lapisan FX hidup menanyakan hook ini saat renderer tersedia.
        @staticmethod
        def _live_module():
            if GrimjawV1Renderer._LIVE_MOD is None:
                try:
                    from heroes import grimjaw_fx as mod
                    GrimjawV1Renderer._LIVE_MOD = (
                        mod if getattr(mod, "GRIMJAW_FX_ENABLED", True)
                        else False)
                except Exception:
                    GrimjawV1Renderer._LIVE_MOD = False
            return GrimjawV1Renderer._LIVE_MOD or None

        @staticmethod
        def _fx_live_owned(hero):
            try:
                mod = GrimjawV1Renderer._live_module()
                return bool(mod is not None and mod.owns(hero))
            except Exception:
                return False

        @staticmethod
        def live_fx_ready():
            return GrimjawV1Renderer._live_module() is not None

    return GrimjawV1Renderer
