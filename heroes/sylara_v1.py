"""SYLARA V1.0 pixel-art renderer — pola arsitektur ``heroes/vex_v1.py``.

Modul ini mengganti jalur gambar Sylara (Wind Ranger) dengan sprite chibi
pixel-art 48x48 @2.6x, persis seperti ``heroes/kaizen_v1.py`` untuk Kaizen,
``heroes/vex_v1.py`` untuk Vex, dan ``heroes/grimjaw_v1.py`` untuk Grimjaw:
grid sumber kecil, blok pixel integer, satu rig berlapis yang dihitung ulang
tiap pose, dan kontrak geometri senjata yang menjadi SATU sumber kebenaran
bagi lapisan FX hidup (``heroes/sylara_fx.py``).

Struktur berkas sengaja MIRROR vex_v1.py/grimjaw_v1.py supaya ketiga
renderer bisa dibandingkan baris per baris:

    KONFIGURASI & PALETTE          identitas Sylara (hijau hutan + angin)
    HELPER PROSEDURAL              _clamp/_rgba/_mix/_static/_scratch/...
    KONTRAK KOORDINAT & ANIMASI    _pixel_local/_make_pixel_ops/...
    POSE & ANIMATION CONTROLLER    _detect_moving/_update_attack_anim/
                                   _attack_pose/_swing_arc_pose/...
    GEOMETRI BUSUR (JEMBATAN FX)   _bow_pose_local/_bow_geometry/...
    LAYER SPRITE V1                cape/quiver/legs/torso/hood/bow/arm
    AMBIENT & SKILL FX (canvas)    aura, platform, telegraph Q/W/E/R
    PROYEKTIL (fallback canvas)    WindBolt (basic) / Shackle (E)
    POSE MODES + ENTRY POINT       idle/walk/attack/windrun/hurt/death
    HOOK LAPISAN HIDUP             _live_module/_fx_live_owned

Yang TIDAK berubah (identitas & gameplay Sylara):
  * skill Q Focus Fire, W Windrun, E Shackle Shot, R Powershot beserta
    timer visual ``SKILL_VISUAL_DURATION`` (180/180/150/60);
  * timeline serangan + ayunan busur berbasis ARC
    (``ATTACK_ANTICIPATION_END`` .. ``ATTACK_FOLLOW_END``, ``SWING_WINDOW``,
    ``SWING_RANGE``, ``_swing_arc_pose``) — kontrak ``heroes/sylara_fx.py``
    dan ``tools/test_sylara_v3_combat_fx.py``;
  * nama atribut state ``_sy_*``, ``_moving_cached``, proyektil
    ``_sy_projectiles``, ``_pose_variant`` (kunci cache sprite), dan hook
    ``owns()/attach()`` lapisan hidup;
  * PALETTE lama tetap menang lewat pewarisan namespace legacy.

Gameplay, kontrol sentuh, generasi dunia, dan damage tetap milik Mystic
Arena; modul ini hanya memiliki pose visual Sylara dan efek canvas
fallback-nya.  100% PROSEDURAL - tidak ada PNG/JPG/GIF/sprite-sheet.

Catatan pass kebersihan (pola vex_v1/grimjaw_v1):
  * KAKI digambar sebagai rect grid: paha kulit-hijau + boot kulit 3 band
    (sol gelap, badan, kilau) - bukan garis tebal.
  * BUSUR digambar sebagai busur recurve dari segmen garis (selout 3 px,
    kayu 2 px, kilau 1 px) yang posenya datang dari ``_bow_geometry``;
    tali + anak panah ternock ikut tarikan ``draw_amt``.
  * MUKA & HOOD: hood runcing hijau + rambut merah berkibar (identitas
    Wind Ranger), mata hijau 2 px dengan kilau putih 1 px.
  * Serangan dasar melepas panah angin visual (damage=0) dari nock di
    titik rilis ayunan; touchdown hanya percikan lembut TANPA ImpactFX /
    hit-stop / shake (kontrak tools/test_basic_attack_no_impact_fx.py).
  * FX skill: massa besar (cakram isi, cincin mengembang) SELALU di
    lapisan TANAH sebelum badan; lapisan depan hanya aksen ringan.
"""

import math

import pygame


def install(legacy_cls):
    """Kembalikan subclass V1 dari namespace legacy yang diberikan.

    ``heroes._bundle`` menyimpan seluruh namespace hero dalam satu berkas.
    Subclassing namespace lama membuat tool lama dan lapisan FX hidup tetap
    menemukan helper-nya, sementara jalur gambar Sylara diganti penuh oleh
    implementasi pixel-art V1 di bawah - layering yang sama dengan
    ``heroes/vex_v1.py`` dan ``heroes/grimjaw_v1.py``.
    """

    class SylaraV1Renderer(legacy_cls):
        """SYLARA V1.0 — Wind Ranger (pixel-art, pola Kaizen/Vex V1)."""

        # ------------------------------------------------------------------
        # Palette: swatch skin/hair/cloth/leather/gold/wood/wind dipertahankan
        # supaya identitas material Sylara sama persis (dan sinkronisasi
        # heroes/sylara_fx.py::_sync_palette tetap dapat kunci yang sama).
        # ------------------------------------------------------------------
        C_OUTLINE = (9, 20, 12)
        C_SKIN_DARKEST = (155, 105, 85)
        C_SKIN_DARK = (210, 160, 130)
        C_SKIN_MID = (240, 200, 170)
        C_SKIN_LIGHT = (250, 220, 195)
        C_SKIN_HIGH = (255, 240, 220)
        C_HAIR_DARKEST = (85, 25, 15)
        C_HAIR_DARK = (145, 50, 25)
        C_HAIR_MID = (200, 85, 35)
        C_HAIR_LIGHT = (240, 130, 55)
        C_HAIR_SHINE = (255, 180, 95)
        C_HAIR_HIGH = (255, 214, 140)
        C_CLOTH_DARKEST = (15, 35, 20)
        C_CLOTH_DARK = (35, 65, 35)
        C_CLOTH_MID = (60, 105, 55)
        C_CLOTH_LIGHT = (95, 150, 80)
        C_CLOTH_HIGH = (140, 195, 115)
        C_CLOAK_DARKEST = (20, 40, 25)
        C_CLOAK_DARK = (40, 75, 40)
        C_CLOAK_MID = (65, 110, 55)
        C_CLOAK_LIGHT = (100, 155, 80)
        C_CLOAK_HIGH = (148, 198, 118)
        C_HOOD_DARKEST = (18, 36, 20)
        C_HOOD_DARK = (30, 55, 30)
        C_HOOD_MID = (55, 95, 50)
        C_HOOD_LIGHT = (85, 135, 70)
        C_LEATHER_DARKEST = (35, 20, 10)
        C_LEATHER_DARK = (70, 45, 25)
        C_LEATHER_MID = (110, 75, 45)
        C_LEATHER_LIGHT = (155, 110, 70)
        C_LEATHER_HIGH = (198, 150, 96)
        C_GOLD_DARK = (95, 70, 20)
        C_GOLD_MID = (170, 130, 40)
        C_GOLD_LIGHT = (230, 195, 90)
        C_GOLD_SHINE = (255, 236, 150)
        C_WOOD_DARKEST = (45, 25, 15)
        C_WOOD_DARK = (85, 55, 30)
        C_WOOD_MID = (130, 90, 50)
        C_WOOD_LIGHT = (170, 125, 75)
        C_WOOD_SHINE = (205, 165, 105)
        C_STRING = (220, 210, 180)
        C_STRING_SHINE = (250, 245, 220)
        C_WIND_DARKEST = (20, 60, 25)
        C_WIND_DARK = (50, 120, 50)
        C_WIND_MID = (110, 195, 90)
        C_WIND_LIGHT = (170, 235, 135)
        C_WIND_BRIGHT = (210, 255, 175)
        C_WIND_WHITE = (240, 255, 220)
        C_LEAF_GOLD = (196, 214, 72)
        C_LEAF_EMBER = (236, 168, 58)
        C_ARROW_SHAFT = (200, 175, 130)
        C_ARROW_SHAFT_D = (140, 110, 70)
        C_ARROW_HEAD = (180, 195, 210)
        C_ARROW_HEAD_D = (100, 115, 135)
        C_ARROW_FEATHER = (140, 200, 95)
        C_ARROW_FEATHER_D = (70, 120, 55)
        C_EYE_WHITE = (240, 248, 255)
        C_EYE_IRIS = (90, 145, 80)
        C_EYE_IRIS_LIGHT = (150, 210, 130)
        C_EYE_PUPIL = (15, 25, 15)
        C_LIPS_DARK = (155, 70, 75)
        C_LIPS_MID = (205, 110, 115)
        C_SHADOW = (0, 0, 0)
        C_WHITE = (255, 255, 255)

        # Swatch V1 (identik nilai dengan palette legacy — diverifikasi
        # byte-per-byte).  Ditulis eksplisit supaya namespace tetap lengkap
        # walau di-install di atas base minimal, lalu di-merge dengan
        # PALETTE legacy (warisan menang) + alias kunci tambahan.
        _PALETTE_V1 = {
            "outline": C_OUTLINE, "shadow_deep": C_OUTLINE,
            "outline_dark": (6, 14, 8),
            "hood_darkest": C_HOOD_DARKEST, "hood_dark": C_HOOD_DARK,
            "hood_mid": C_HOOD_MID, "hood_light": C_HOOD_LIGHT,
            "cloth_darkest": C_CLOTH_DARKEST, "cloth_dark": C_CLOTH_DARK,
            "cloth_mid": C_CLOTH_MID, "cloth_light": C_CLOTH_LIGHT,
            "cloth_high": C_CLOTH_HIGH,
            "cloak_darkest": C_CLOAK_DARKEST, "cloak_dark": C_CLOAK_DARK,
            "cloak_mid": C_CLOAK_MID, "cloak_light": C_CLOAK_LIGHT,
            "cloak_high": C_CLOAK_HIGH,
            "leather_darkest": C_LEATHER_DARKEST,
            "leather_dark": C_LEATHER_DARK, "leather_mid": C_LEATHER_MID,
            "leather_light": C_LEATHER_LIGHT, "leather_high": C_LEATHER_HIGH,
            "gold_dark": C_GOLD_DARK, "gold_mid": C_GOLD_MID,
            "gold_light": C_GOLD_LIGHT, "gold_shine": C_GOLD_SHINE,
            "wood_darkest": C_WOOD_DARKEST, "wood_dark": C_WOOD_DARK,
            "wood_mid": C_WOOD_MID, "wood_light": C_WOOD_LIGHT,
            "wood_shine": C_WOOD_SHINE,
            "hair_darkest": C_HAIR_DARKEST, "hair_dark": C_HAIR_DARK,
            "hair_mid": C_HAIR_MID, "hair_light": C_HAIR_LIGHT,
            "hair_shine": C_HAIR_SHINE, "hair_high": C_HAIR_HIGH,
            "skin_darkest": C_SKIN_DARKEST, "skin_dark": C_SKIN_DARK,
            "skin_mid": C_SKIN_MID, "skin_light": C_SKIN_LIGHT,
            "skin_high": C_SKIN_HIGH,
            "wind_darkest": C_WIND_DARKEST, "wind_dark": C_WIND_DARK,
            "wind_mid": C_WIND_MID, "wind_light": C_WIND_LIGHT,
            "wind_bright": C_WIND_BRIGHT, "wind_white": C_WIND_WHITE,
            "wind_pale": C_WIND_WHITE, "wind_core": C_WIND_BRIGHT,
            "leaf_gold": C_LEAF_GOLD, "leaf_ember": C_LEAF_EMBER,
            "leaf_light": (222, 232, 120), "leaf_deep": (120, 130, 40),
            "vine_darkest": (16, 44, 22),
            "arrow_shaft": C_ARROW_SHAFT, "arrow_shaft_d": C_ARROW_SHAFT_D,
            "arrow_head": C_ARROW_HEAD, "arrow_head_d": C_ARROW_HEAD_D,
            "arrow_feather": C_ARROW_FEATHER,
            "arrow_feather_d": C_ARROW_FEATHER_D,
            "arrow_metal": C_ARROW_HEAD,
            "arrow_metal_dark": C_ARROW_HEAD_D,
            "arrow_fletch": C_ARROW_FEATHER,
            "string": C_STRING, "string_shine": C_STRING_SHINE,
            "eye_white": C_EYE_WHITE, "eye_iris": C_EYE_IRIS,
            "eye_iris_light": C_EYE_IRIS_LIGHT, "eye_pupil": C_EYE_PUPIL,
            "lips_dark": C_LIPS_DARK, "lips_mid": C_LIPS_MID,
            "gold_hot": C_GOLD_SHINE, "wood_pale": C_WOOD_SHINE,
            "hair_light_2": C_HAIR_HIGH, "cloth_shine": C_CLOTH_HIGH,
            "cloak_darkest_2": C_CLOAK_DARKEST,
            "white": C_WHITE, "shadow": C_SHADOW,
        }

        # Namespace ini juga dikonsumsi heroes/sylara_fx.py (mode minimal) dan
        # tool lama: PALETTE legacy di-merge DI ATAS swatch V1 supaya kunci
        # historis (dan nilai lamanya) menang, sementara kunci V1 baru tetap
        # tersedia.  Nilai keduanya sudah identik untuk seluruh material.
        PALETTE = dict(_PALETTE_V1,
                       **(dict(getattr(legacy_cls, "PALETTE", {}) or {})))

        # Native coordinates on the V1 48x48 pixel grid.  The hero cache
        # pipeline measures this rig and normalizes it to arena size, so a
        # denser native rig only raises sharpness, never on-screen height.
        PIXEL_SCALE = 2.6
        PIXEL_ORIGIN = 24.0
        # Local helpers already return canvas pixels (bow geometry bridge),
        # so the historic RIG_SCALE multiplier in sylara_fx.bow_points() must
        # become neutral 1.0 - otherwise the live trail would detach from the
        # drawn bow (bug class yang sama seperti staff Vex).
        RIG_SCALE = 1.0

        # Busur V1 (satuan grid sumber 48x48).
        BOW_LIMB_SRC = 11.0
        BOW_GRIP_SRC = (33.0, 23.5)
        BOW_HAND_SRC = (31.0, 23.5)
        DRAW_HAND_SRC = (21.5, 24.0)
        SHOULDER_SRC = (27.5, 20.5)
        SWING_PIVOT_SRC = (28.0, 21.0)
        FOOT_SRC_Y = 45.0
        #: Garis tanah tempat FX massa besar di-squash (canvas px lokal).
        GROUND_LOCAL = 40.0
        #: Rasio squash efek yang diproyeksikan ke bidang tanah.
        GROUND_SQUASH = 0.45

        # Durasi pose per skill (langkah simulasi) — identik dgn legacy dan
        # heroes/sylara_fx.py::SKILL_DUR.
        SKILL_VISUAL_DURATION = {"q": 180, "w": 180, "e": 150, "r": 60}

        # Timeline serangan v3 — SATU sumber kebenaran untuk fase FX
        # (sylara_fx._resolve_timeline membaca nilai ini) dan pose body.
        ATTACK_ANTICIPATION_END = 0.12
        ATTACK_WINDUP_END = 0.26
        ATTACK_SWING_END = 0.58
        ATTACK_IMPACT_END = 0.62
        ATTACK_FOLLOW_END = 0.80
        ATTACK_IMPACT_FRAME = 0.52
        ATTACK_ACTIVE_WINDOW = (0.42, 0.62)
        SWING_WINDOW = (0.16, 0.88)
        SWING_RANGE = 64.0
        # Alias lama (dipakai tooling/dokumen pra-v3).
        ATTACK_RELEASE_END = ATTACK_SWING_END
        ATTACK_IMPACT = ATTACK_IMPACT_FRAME

        ANIM_STATES = {
            "IDLE": 0, "WALK": 10, "RUN": 15, "CHARGE": 30, "CAST": 35,
            "ATTACK": 40, "SWING": 45, "SKILL": 50, "SPECIAL": 55,
            "HIT": 60, "HURT": 65, "DEATH": 100,
        }
        DEBUG_CHARACTER = False

        _LIVE_MOD = None
        _STATIC_SURFACES = {}
        _SCRATCH_POOL = {}
        try:
            _FX_LIVE = legacy_cls._LiveFlag()
        except Exception:  # pragma: no cover - stripped tools
            _FX_LIVE = type("_LiveFlag", (), {"v": False})()

        # ------------------------------------------------------------------
        # Low-level procedural helpers (kosakata keluarga V1).
        # ------------------------------------------------------------------
        @staticmethod
        def _clamp(color):
            vals = tuple(int(max(0, min(255, c))) for c in color)
            return vals if len(vals) in (3, 4) else vals[:3]

        @staticmethod
        def _rgba(color, alpha=255):
            c = SylaraV1Renderer._clamp(color)
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
            surf = SylaraV1Renderer._STATIC_SURFACES.get(key)
            if surf is None:
                if len(SylaraV1Renderer._STATIC_SURFACES) > 96:
                    SylaraV1Renderer._STATIC_SURFACES.clear()
                surf = builder()
                SylaraV1Renderer._STATIC_SURFACES[key] = surf
            return surf

        @staticmethod
        def _scratch(w, h):
            key = (max(1, int(w)), max(1, int(h)))
            pool = SylaraV1Renderer._SCRATCH_POOL
            surf = pool.get(key)
            if surf is None:
                if len(pool) > 32:
                    pool.clear()
                surf = pygame.Surface(key, pygame.SRCALPHA)
                pool[key] = surf
            else:
                surf.fill((0, 0, 0, 0))
            return surf

        @staticmethod
        def _rect(surface, color, rect, border_radius=0):
            if border_radius:
                pygame.draw.rect(surface, color, rect,
                                 border_radius=border_radius)
            else:
                pygame.draw.rect(surface, color, rect)

        @staticmethod
        def _poly(surface, color, points):
            pygame.draw.polygon(surface, color, points)

        @staticmethod
        def _ellipse(surface, color, rect, width=0):
            pygame.draw.ellipse(surface, color, rect, width)

        @staticmethod
        def _aaline(surface, color, start, end, width=1):
            if width > 1:
                pygame.draw.line(surface, color, start, end, width)
                return
            pygame.draw.aaline(surface, color, start, end)

        @staticmethod
        def _aacircle(surface, color, center, radius, width=0):
            radius = max(1, int(radius))
            if width:
                pygame.draw.circle(surface, color, center, radius, width)
            else:
                pygame.draw.circle(surface, color, center, radius)

        @staticmethod
        def _spark_star(surface, cx, cy, size, color, alpha,
                        spikes=4, rot=0.4):
            size = max(1.0, float(size))
            for i in range(max(2, int(spikes))):
                a = float(rot) + i * math.pi / max(2, int(spikes))
                dx = math.cos(a) * size
                dy = math.sin(a) * size * 0.5
                SylaraV1Renderer._aaline(
                    surface, (*color, int(alpha)),
                    (int(cx - dx), int(cy - dy)),
                    (int(cx + dx), int(cy + dy)), 1)
            c = int(max(1, size * 0.28))
            SylaraV1Renderer._rect(surface, (*color, int(alpha)),
                                   (int(cx) - c, int(cy) - c, c * 2, c * 2))

        @staticmethod
        def _chevron(surface, cx, cy, ang, size, color, alpha, width=2):
            back = ang + 2.55
            x1 = cx + math.cos(back) * size
            y1 = cy + math.sin(back) * size * 0.6
            x2 = cx + math.cos(ang - 2.55) * size
            y2 = cy + math.sin(ang - 2.55) * size * 0.6
            SylaraV1Renderer._aaline(surface, (*color, int(alpha)),
                                     (x1, y1), (cx, cy), width)
            SylaraV1Renderer._aaline(surface, (*color, int(alpha)),
                                     (cx, cy), (x2, y2), width)

        @staticmethod
        def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                         dashes=12, width=2, squash=0.35):
            radius = max(2.0, float(radius))
            step = math.tau / dashes
            for i in range(dashes):
                a0 = phase + i * step
                a1 = a0 + step * 0.55
                p0 = (cx + math.cos(a0) * radius,
                      cy + math.sin(a0) * radius * squash)
                p1 = (cx + math.cos(a1) * radius,
                      cy + math.sin(a1) * radius * squash)
                SylaraV1Renderer._aaline(surface, (*color, int(alpha)),
                                         p0, p1, width)

        @staticmethod
        def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                          width=2, segments=5):
            px, py = cx, cy
            for i in range(int(segments)):
                t = (i + 1) / float(segments)
                wiggle = (SylaraV1Renderer._hash01(seed + i * 7) - 0.5) * 10.0
                nx = cx + math.cos(ang) * length * t - math.sin(ang) * wiggle
                ny = (cy + math.sin(ang) * length * t * 0.5
                      + math.cos(ang) * wiggle * 0.5)
                col = colors[min(len(colors) - 1,
                                 i * len(colors) // int(segments))]
                SylaraV1Renderer._aaline(surface, (*col, int(alpha)),
                                         (px, py), (nx, ny), width)
                px, py = nx, ny

        @staticmethod
        def _tuft_points(spine, depth=4.0, min_len=7.0, seed=0):
            (x0, y0), (x1, y1) = spine
            pts = [(x0, y0)]
            count = 3
            for i in range(1, count + 1):
                t = i / float(count + 1)
                bx = x0 + (x1 - x0) * t
                by = y0 + (y1 - y0) * t
                ln = min_len + SylaraV1Renderer._hash01(seed + i) * depth
                pts.append((bx, by + ln))
                pts.append((bx + (x1 - x0) / float(count + 1) * 0.5, by))
            pts.append((x1, y1))
            return pts

        @staticmethod
        def _aoe_marks(surface, cx, cy, radius, color, alpha, phase=0.0,
                       squash=1.0, ticks=16, tick_len=8):
            radius = max(8, int(radius))
            SylaraV1Renderer._dashed_ring(
                surface, cx, cy, radius, color, alpha, phase * 0.5,
                dashes=max(8, int(ticks) // 2), width=2, squash=squash)
            for i in range(int(ticks)):
                a = phase * 0.35 + i * math.tau / int(ticks)
                x0 = cx + math.cos(a) * (radius - tick_len)
                y0 = cy + math.sin(a) * (radius - tick_len) * squash
                x1 = cx + math.cos(a) * radius
                y1 = cy + math.sin(a) * radius * squash
                SylaraV1Renderer._aaline(surface, (*color, int(alpha)),
                                         (x0, y0), (x1, y1), 2)

        @staticmethod
        def _fx_scale(boss):
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            return max(1.0, min(2.6, 1.0 / scale))

        @staticmethod
        def _ring_r(boss, world_px, surface=None):
            """Radius DUNIA (px) -> px canvas, di-clamp ke dalam canvas.

            Efek yang digambar di luar cache canvas akan terpotong dan
            meninggalkan garis aneh di tepi sprite hero.
            """
            scale = float(getattr(boss, "_render_scale", None) or 0.0)
            radius = (float(world_px) / scale if scale
                      else float(world_px))
            if surface is not None:
                margin = min(surface.get_width(),
                             surface.get_height()) // 2 - 10
                radius = min(radius, margin)
            return int(max(4, radius))

        @staticmethod
        def _skill_progress(skill, timer):
            duration = float(SylaraV1Renderer.SKILL_VISUAL_DURATION.get(
                skill, max(1, timer or 1)))
            return max(0.0, min(1.0, 1.0 - float(timer) / max(1.0, duration)))

        # Alias legacy (dipakai tooling lama).
        @staticmethod
        def _sy_progress(skill, timer):
            return SylaraV1Renderer._skill_progress(skill, timer)

        # ------------------------------------------------------------------
        # Coordinate and animation contracts consumed by live FX.
        # ------------------------------------------------------------------
        @staticmethod
        def _world_to_local(boss, x, y, wx, wy):
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            ox = (float(wx) - float(getattr(boss, "x", x))) / scale
            oy = (float(wy) - float(getattr(boss, "y", y))) / scale
            rng = int(getattr(boss, "range", 130) or 130)
            half = max(120, int(rng / scale) + 40)
            max_off = half - 20
            dist = math.hypot(ox, oy)
            if dist > max_off and dist > 0:
                ox *= max_off / dist
                oy *= max_off / dist
            return int(x + ox), int(y + oy)

        @staticmethod
        def _target_position(boss, x, y):
            target = getattr(boss, "target", None)
            if target is not None and getattr(target, "alive", True):
                return SylaraV1Renderer._world_to_local(
                    boss, x, y, target.x, target.y)
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            return (int(x + 150 * scale * getattr(boss, "direction", 1)),
                    int(y))

        @staticmethod
        def _pixel_local(x, y):
            """Grid sumber -> canvas px relatif anchor (PIXEL_SCALE)."""
            s = SylaraV1Renderer.PIXEL_SCALE
            return ((float(x) - SylaraV1Renderer.PIXEL_ORIGIN) * s,
                    (float(y) - SylaraV1Renderer.PIXEL_ORIGIN) * s)

        @staticmethod
        def _local_to_src(lx, ly):
            s = SylaraV1Renderer.PIXEL_SCALE
            return (float(lx) / s + SylaraV1Renderer.PIXEL_ORIGIN,
                    float(ly) / s + SylaraV1Renderer.PIXEL_ORIGIN)

        @staticmethod
        def _tint(color, tint):
            c = SylaraV1Renderer._clamp(color)
            if tint is None:
                return c
            t = tuple(tint)
            vals = tuple(int(c[i] * t[i] / 255.0) for i in range(3))
            alpha = int((c[3] if len(c) > 3 else 255) *
                        (t[3] if len(t) > 3 else 255) / 255.0)
            return vals + (alpha,)

        @staticmethod
        def _make_pixel_ops(surface, cx, cy, facing, body_x=0, body_y=0,
                            crouch=0, tint=None):
            """R/RO/point/line setara Kaizen/Vex V1 (selout 1 grid pixel)."""
            s = SylaraV1Renderer.PIXEL_SCALE
            sx = -1.0 if facing < 0 else 1.0

            def rect_for(x, y, w, h, ox=0, oy=0, extra_crouch=0):
                rx = cx + ((x + body_x + ox - SylaraV1Renderer.PIXEL_ORIGIN)
                           * s * sx)
                if facing < 0:
                    rx -= w * s
                ry = cy + ((y + body_y + crouch + extra_crouch -
                            SylaraV1Renderer.PIXEL_ORIGIN) * s)
                return pygame.Rect(int(round(rx)), int(round(ry)),
                                   max(1, int(round(w * s))),
                                   max(1, int(round(h * s))))

            def R(x, y, w, h, col, alpha=None):
                color = SylaraV1Renderer._tint(col, tint)
                if alpha is not None:
                    color = color[:3] + (int(color[3] * alpha / 255.0),)
                pygame.draw.rect(surface, color, rect_for(x, y, w, h))

            def RO(x, y, w, h, col, alpha=None):
                # Selout satu pixel grid menjaga sprite tetap terbaca
                # setelah smoothscale + pass HD.
                R(x - 1, y - 1, w + 2, h + 2, SylaraV1Renderer.C_OUTLINE,
                  alpha)
                R(x, y, w, h, col, alpha)

            def point(x, y, ox=0, oy=0):
                return (cx + ((x + body_x + ox
                               - SylaraV1Renderer.PIXEL_ORIGIN) * s * sx),
                        cy + ((y + body_y + crouch + oy
                               - SylaraV1Renderer.PIXEL_ORIGIN) * s))

            def line(a, b, color, width=1, alpha=None):
                c = SylaraV1Renderer._tint(color, tint)
                if alpha is not None:
                    c = c[:3] + (int(c[3] * alpha / 255.0),)
                pygame.draw.line(surface, c, point(*a), point(*b),
                                 max(1, int(round(width * s))))

            return R, RO, point, line

        # ------------------------------------------------------------------
        # V1 pose calculation and animation controller.
        # ------------------------------------------------------------------
        @staticmethod
        def _detect_moving(boss):
            if not hasattr(boss, "_sy_last_x"):
                boss._sy_last_x = boss.x
                boss._sy_last_y = boss.y
                boss._moving_cached = False
                return False
            dx = abs(boss.x - boss._sy_last_x)
            dy = abs(boss.y - boss._sy_last_y)
            boss._sy_last_x = boss.x
            boss._sy_last_y = boss.y
            moving = dx + dy > 0.3
            boss._moving_cached = moving
            return moving

        @staticmethod
        def _attack_pose(ap):
            """Keyframe serangan V1: draw -> hold -> IMPACT -> recover."""
            keys = (
                (0.00,  0,  0, 1.00, 0),
                (0.12,  2, -4, 1.08, 0),
                (0.26,  3, -6, 1.18, 1),
                (0.42,  1, -5, 1.22, 0),
                (0.52, -2,  8, 1.32, 0),
                (0.72,  1,  3, 1.08, 0),
                (1.00,  0,  0, 1.00, 0),
            )
            ap = max(0.0, min(1.0, float(ap)))
            for i in range(len(keys) - 1):
                k0, k1 = keys[i], keys[i + 1]
                if k0[0] <= ap <= k1[0]:
                    span = max(1e-6, k1[0] - k0[0])
                    t = (ap - k0[0]) / span
                    t = t * t * (3 - 2 * t)
                    return {
                        "bob": int(round(k0[1] + (k1[1] - k0[1]) * t)),
                        "lean": int(round(k0[2] + (k1[2] - k0[2]) * t)),
                        "flare": k0[3] + (k1[3] - k0[3]) * t,
                        "tremble": 1 if (k0[4] and t < .9) else 0,
                    }
            return {"bob": 0, "lean": 0, "flare": 1.0, "tremble": 0}

        @staticmethod
        def _update_attack_anim(boss):
            """Controller pose per-frame (identik semantik rig legacy).

            Serangan baru dikenali dari timer yang NAIK (attack_timer
            menghitung mundur), jadi animasi tetap benar pada fixed
            timestep berapa pun.  ``_pose_variant`` membedakan pose sapuan
            melee dari pose tembakan supaya kunci cache sprite tidak
            menyajikan sprite basi.
            """
            cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
            timer = int(getattr(boss, "timer", 0))
            previous = int(getattr(boss, "_sy_prev_timer", -1))
            active = bool(getattr(boss, "_sy_attack_active", False))

            trigger = previous >= 0 and timer > previous
            if trigger:
                boss._sy_attack_active = True
                active = True
            if active and timer <= 0:
                boss._sy_attack_active = False
                active = False
            boss._sy_prev_timer = timer

            boss._sy_attack_frame = max(0, cooldown - timer) if active else 0
            progress = (min(1.0, boss._sy_attack_frame / max(1, cooldown - 1))
                        if active else 0.0)
            boss._sy_attack_progress = progress

            A = SylaraV1Renderer
            if not active:
                phase = "NONE"
            elif progress < A.ATTACK_ANTICIPATION_END:
                phase = "ANTICIPATION"
            elif progress < A.ATTACK_WINDUP_END:
                phase = "WINDUP"
            elif progress < A.ATTACK_SWING_END:
                phase = "SWING"
            elif progress < A.ATTACK_IMPACT_END:
                phase = "IMPACT"
            elif progress < A.ATTACK_FOLLOW_END:
                phase = "FOLLOW"
            else:
                phase = "RECOVERY"
            boss._sy_attack_phase = phase

            lo, hi = A.ATTACK_ACTIVE_WINDOW
            boss._sy_hit_active = bool(active and lo <= progress < hi)

            # Mode ayunan dikunci SAAT serangan mulai (bukan tiap frame).
            if trigger or (active and not hasattr(boss, "_sy_swing_mode")):
                tgt = getattr(boss, "target", None)
                close = False
                if tgt is not None and getattr(tgt, "alive", True):
                    try:
                        close = math.hypot(float(tgt.x) - float(boss.x),
                                           float(tgt.y) - float(boss.y)) \
                            <= A.SWING_RANGE
                    except Exception:
                        close = False
                boss._sy_swing_mode = bool(close)
            if not active:
                boss._sy_swing_mode = False
            boss._pose_variant = (1 if getattr(boss, "_sy_swing_mode", False)
                                  else 0)

            hurt = int(getattr(boss, "_sy_hurt_frames", 0) or 0)
            if hurt > 0:
                boss._sy_hurt_frames = hurt - 1

            want = A._resolve_anim_state(boss, active, phase)
            cur = getattr(boss, "_sy_state", None)
            if cur is None:
                boss._sy_state = want
                boss._sy_state_prev = want
                boss._sy_state_time = 0.0
            else:
                dt = 1.0 / 60.0
                state_time = float(getattr(boss, "_sy_state_time", 0.0))
                if want != cur:
                    cur_p = A.ANIM_STATES.get(cur, 0)
                    new_p = A.ANIM_STATES.get(want, 0)
                    if cur != "DEATH" and (new_p >= cur_p
                                           or state_time > 0.08):
                        boss._sy_state_prev = cur
                        boss._sy_state = want
                        boss._sy_state_time = 0.0
                    else:
                        boss._sy_state_time = state_time + dt
                else:
                    boss._sy_state_time = state_time + dt

        @staticmethod
        def _swing_hitbox(boss, cx, cy):
            """Rect hitbox sapuan (ruang canvas) saat jendela hit aktif.

            Return ``None`` kalau jendela hit sedang tidak aktif.  Dipakai
            overlay debug dan (opsional) sistem tumbukan; lebarnya mengikuti
            ``SWING_RANGE`` dunia yang sudah dibagi ``_render_scale`` supaya
            kotak di canvas setara jangkauan gameplay.
            """
            if not getattr(boss, "_sy_hit_active", False):
                return None
            f = 1 if getattr(boss, "direction", 1) >= 0 else -1
            scale = float(getattr(boss, "_render_scale", None) or 0.0)
            reach = int(SylaraV1Renderer.SWING_RANGE /
                        max(0.05, scale if scale else 1.0))
            reach = max(16, min(reach, 200))
            left = cx if f > 0 else cx - reach
            return pygame.Rect(int(left), int(cy - 52), reach, 74)

        # ------------------------------------------------------------------
        # GEOMETRI BUSUR — jembatan ke heroes/sylara_fx.py.
        #
        # Semua helper di bawah mengembalikan canvas px relatif anchor
        # (RIG_SCALE = 1.0 sudah menyerap PIXEL_SCALE), sehingga
        # sylara_fx.bow_points() menempel PERSIS di kayu busur yang
        # digambar - satu sumber kebenaran untuk pose DAN FX.
        # ------------------------------------------------------------------
        @staticmethod
        def _bow_limb_offset(s, draw_amt):
            """Profil recurve: perut maju, ujung menekuk balik."""
            flex = max(0.0, float(draw_amt)) * 0.55
            return 6.0 * s * s - 10.5 * (s ** 4) - flex * 5.0 * s * s

        @staticmethod
        def _bow_point_src(grip, tilt, u, v):
            (ux, uy), (fx, fy) = SylaraV1Renderer._bow_frame(tilt)
            return (grip[0] + ux * u + fx * v, grip[1] + uy * u + fy * v)

        @staticmethod
        def _bow_nock_src(grip, tilt, draw_amt):
            """Titik nock (tangan penarik) — ditarik ke arah badan."""
            draw = max(0.0, min(1.0, float(draw_amt)))
            # tarikan berhenti di depan dada, bukan di depan wajah
            return SylaraV1Renderer._bow_point_src(
                grip, tilt, 0.0, -1.2 - draw * 4.4)

        @staticmethod
        def _bow_pose_local(action="idle", ap=0.0, wave=0.0):
            """(grip, tilt, draw_amt) busur pada GRID SUMBER 48x48.

            Satu sumber kebenaran untuk pose busur: dipakai rig saat
            menggambar DAN oleh ``_bow_geometry`` (jembatan FX hidup).
            """
            A = SylaraV1Renderer
            ap = max(0.0, min(1.0, float(ap)))
            if action == "swing":
                pose = A._swing_arc_pose(ap)
                ang, rad = pose["angle"], pose["radius"]
                px, py = A.SWING_PIVOT_SRC
                # SWING_R_* legacy berada di ruang rig 1.52x; skala ke grid
                # sumber V1 supaya panjang ayunan tetap proporsional.
                rad = rad * (A.BOW_LIMB_SRC / 26.0)
                grip = (px + math.cos(ang) * rad, py + math.sin(ang) * rad)
                return grip, ang + 1.40, 0.0
            if action == "attack":
                if ap < 0.12:
                    t = A._ease_in_out(ap / 0.12)
                    return ((32.5 - t * 0.5, 23.5 - t * 1.2),
                            0.24 - t * 0.06, 0.10 * t)
                if ap < 0.26:
                    t = A._ease_in_out((ap - 0.12) / 0.14)
                    return ((32 - t * 1.4, 22.3 - t * 1.0),
                            0.18 - t * 0.06, 0.10 + 0.50 * t)
                if ap < 0.42:
                    t = A._ease_in_out((ap - 0.26) / 0.16)
                    return ((30.6 - t * 0.8, 21.3), 0.12 - t * 0.04,
                            0.60 + 0.40 * t)
                if ap < 0.52:
                    return (29.8, 21.3), 0.08, 1.0
                if ap < 0.58:
                    t = (ap - 0.52) / 0.06
                    return ((29.8 + t * 3.4, 21.3 + t * 1.6), 0.08,
                            max(0.0, 1.0 - t * 1.7))
                if ap < 0.72:
                    t = A._ease_in_out((ap - 0.58) / 0.14)
                    return ((33.2 - t * 0.6, 22.9 + t * 0.8),
                            0.08 + t * 0.10, 0.0)
                t = A._ease_in_out((ap - 0.72) / 0.28)
                return ((32.6 - t * 0.4, 23.7 - t * 0.6),
                        0.18 + t * 0.10, 0.0)
            if action == "windrun":
                return (29.0, 25.0), 0.85, 0.0
            if action == "focus":
                return (30.6, 22.4), 0.10, 0.55
            if action == "shackle":
                return (33.4, 23.0), 0.16, 0.85
            if action == "powershot":
                return (29.4, 21.0), 0.06, 1.0
            # idle / walk
            return (33.0 + math.sin(wave) * 0.5, 23.5 + math.sin(wave) * 0.6), \
                0.30 + math.sin(wave) * 0.05, 0.0

        @staticmethod
        def _bow_geometry(phase=0.0, action="idle", attack_progress=0.0):
            """Semua titik penting busur dalam CANVAS px relatif anchor.

            Return dict dengan kunci ``grip`` / ``tilt`` / ``draw`` /
            ``tip_up`` / ``tip_low`` / ``nock`` / ``arrow_tip`` -
            kontrak yang dibaca ``heroes/sylara_fx.py`` (bow_points,
            trail sapuan, titik lepas anak panah).
            """
            A = SylaraV1Renderer
            wave = math.sin(float(phase) * 1.15)
            grip, tilt, draw_amt = A._bow_pose_local(action, attack_progress,
                                                     wave)
            flex = draw_amt * 0.55
            v_tip = 6.0 - 10.5 - flex * 5.0
            tip_up = A._bow_point_src(grip, tilt, A.BOW_LIMB_SRC, v_tip)
            tip_low = A._bow_point_src(grip, tilt, -A.BOW_LIMB_SRC, v_tip)
            nock = A._bow_nock_src(grip, tilt, draw_amt)
            (_ux, _uy), (fx, fy) = A._bow_frame(tilt)
            arrow_tip = (nock[0] + fx * 18.0, nock[1] + fy * 18.0)
            return {
                "grip": A._pixel_local(*grip),
                "tilt": tilt,
                "draw": draw_amt,
                "tip_up": A._pixel_local(*tip_up),
                "tip_low": A._pixel_local(*tip_low),
                "nock": A._pixel_local(*nock),
                "arrow_tip": A._pixel_local(*arrow_tip),
            }

        @staticmethod
        def _bow_grip_local(phase=0.0, action="idle", attack_progress=0.0):
            return SylaraV1Renderer._bow_geometry(
                phase, action, attack_progress)["grip"]

        @staticmethod
        def _bow_tip_local(phase=0.0, action="idle", attack_progress=0.0):
            return SylaraV1Renderer._bow_geometry(
                phase, action, attack_progress)["tip_up"]

        @staticmethod
        def _bow_nock_local(phase=0.0, action="idle", attack_progress=0.0):
            return SylaraV1Renderer._bow_geometry(
                phase, action, attack_progress)["nock"]

        @staticmethod
        def _bow_release_local(phase=0.0, attack_progress=0.0):
            return SylaraV1Renderer._bow_geometry(
                phase, "attack", attack_progress)["arrow_tip"]

        @staticmethod
        def _bow_grip_position(cx, cy, facing, phase=0.0, action="idle",
                               attack_progress=0.0):
            """Posisi grip di CANVAS (siap dipakai FX & spawn)."""
            gx, gy = SylaraV1Renderer._bow_geometry(
                phase, action, attack_progress)["grip"]
            f = 1 if facing >= 0 else -1
            return int(cx + gx * f), int(cy + gy)

        @staticmethod
        def _bow_tip_position(cx, cy, facing, phase=0.0, action="attack",
                              attack_progress=0.0):
            tx, ty = SylaraV1Renderer._bow_geometry(
                phase, action, attack_progress)["tip_up"]
            f = 1 if facing >= 0 else -1
            return int(cx + tx * f), int(cy + ty)

        @staticmethod
        def _bow_nock_position(cx, cy, facing, phase=0.0, action="attack",
                               attack_progress=0.0):
            nx, ny = SylaraV1Renderer._bow_geometry(
                phase, action, attack_progress)["nock"]
            f = 1 if facing >= 0 else -1
            return int(cx + nx * f), int(cy + ny)

        @staticmethod
        def _bow_release_position(cx, cy, facing, phase=0.0,
                                  attack_progress=0.0):
            """Ujung mata panah di canvas — titik lahir proyektil visual."""
            rx, ry = SylaraV1Renderer._bow_geometry(
                phase, "attack", attack_progress)["arrow_tip"]
            f = 1 if facing >= 0 else -1
            return int(cx + rx * f), int(cy + ry)

        @staticmethod
        def _bow_frame(tilt):
            """Basis lokal busur (helper legacy dipertahankan)."""
            return ((math.sin(tilt), -math.cos(tilt)),
                    (math.cos(tilt), math.sin(tilt)))

        @staticmethod
        def _bow_point(grip, tilt, u, v):
            """Titik pada bidang busur (helper legacy, ruang apapun)."""
            return SylaraV1Renderer._bow_point_src(grip, tilt, u, v)

        @staticmethod
        def _bow_nock(grip, tilt, draw_amt):
            """Nock legacy: ditarik MUNDUR dari grip saat tali ditarik."""
            return SylaraV1Renderer._bow_nock_src(grip, tilt, draw_amt)

        @staticmethod
        def _bow_trail_samples(phase, attack_progress, count=10,
                               action="swing", span=0.16):
            """Histori posisi busur [(grip, tip)] di CANVAS px relatif anchor."""
            A = SylaraV1Renderer
            out = []
            n = max(2, int(count))
            for i in range(n):
                t = attack_progress - span * (1.0 - i / float(n - 1))
                if t < 0.0:
                    t = 0.0
                g = A._bow_geometry(phase, action, t)
                out.append((g["grip"], g["tip_up"]))
            return out

        @staticmethod
        def _draw_bow_swing_trail(surface, pt, phase, attack_progress,
                                  alpha_scale=1.0):
            """Pita sapuan busur di CANVAS (fallback tanpa lapisan hidup).

            ``pt`` = pemeta titik lokal (canvas px relatif anchor) ke
            koordinat surface.  Kalau heroes/sylara_fx.py aktif (60 fps),
            pemanggil melewati fungsi ini supaya tidak dobel.
            """
            P = SylaraV1Renderer
            samples = P._bow_trail_samples(phase, attack_progress, count=9)
            if len(samples) < 2:
                return
            n = len(samples)
            for i in range(n - 1):
                f = (i + 1) / float(n)
                a = int(170 * f * f * alpha_scale)
                if a <= 6:
                    continue
                (g0, t0), (g1, t1) = samples[i], samples[i + 1]
                m0 = (g0[0] + (t0[0] - g0[0]) * 0.34,
                      g0[1] + (t0[1] - g0[1]) * 0.34)
                m1 = (g1[0] + (t1[0] - g1[0]) * 0.34,
                      g1[1] + (t1[1] - g1[1]) * 0.34)
                P._poly(surface, (*P.C_WIND_DARK, a),
                        [pt(*m0), pt(*t0), pt(*t1), pt(*m1)])
                m0 = (g0[0] + (t0[0] - g0[0]) * 0.72,
                      g0[1] + (t0[1] - g0[1]) * 0.72)
                m1 = (g1[0] + (t1[0] - g1[0]) * 0.72,
                      g1[1] + (t1[1] - g1[1]) * 0.72)
                P._poly(surface, (*P.C_WIND_LIGHT, min(255, int(a * 1.4))),
                        [pt(*m0), pt(*t0), pt(*t1), pt(*m1)])
                P._aaline(surface, (*P.C_WIND_WHITE, min(255, int(a * 1.7))),
                          pt(*t0), pt(*t1), 2)

        @staticmethod
        def _draw_bow_release_flash(surface, x, y, facing, progress):
            """Kilat kecil di nock saat anak panah lepas (aksen ringan)."""
            if progress < 0.44 or progress > 0.82:
                return
            P = SylaraV1Renderer
            t = max(0.0, min(1.0, (progress - 0.44) / 0.30))
            intensity = math.sin(t * math.pi) if t < 0.9 else 0.0
            if intensity <= 0.02:
                return
            nx, ny = P._bow_nock_position(
                x, y, facing, 0.0, "attack", progress)
            alpha = int(190 * intensity)
            for k, col in enumerate((P.C_WIND_MID, P.C_WIND_BRIGHT,
                                     P.C_WIND_WHITE)):
                rx = int(6 + intensity * 9 - k * 2)
                ry = max(2, int(rx * 0.42))
                P._ellipse(surface, (*col, max(18, alpha - k * 46)),
                           (nx - rx, ny - ry, rx * 2, ry * 2), 2)
            P._spark_star(surface, nx, ny, 5 + intensity * 7,
                          P.C_WIND_WHITE, alpha, 4, rot=progress * 7)

        # ------------------------------------------------------------------
        # LAYER SPRITE V1 — identitas Wind Ranger di grid 48x48.
        # ------------------------------------------------------------------
        @staticmethod
        def _draw_pixel_cape(R, RO, wave_amt, anim_name, wave):
            """Cape hijau robek di belakang badan (3 panel beranimasi)."""
            P = SylaraV1Renderer
            w1 = math.sin(wave) * wave_amt
            w2 = math.sin(wave + 1.1) * wave_amt
            w3 = math.sin(wave + 2.2) * wave_amt
            if anim_name == "windrun":
                for x, y in ((12, 20), (7, 22), (2, 24), (-2, 26)):
                    RO(x, y, 5, 4, P.C_CLOAK_DARK)
                R(-1, 25, 4, 2, P.C_CLOAK_LIGHT)
                return
            RO(13, 19, 4, 9, P.C_CLOAK_DARK)
            RO(10 + int(w1), 24, 4, 9, P.C_CLOAK_DARK)
            RO(8 + int(w2), 31, 4, 8, P.C_CLOAK_DARKEST)
            RO(10 + int(w3), 36, 3, 5, P.C_CLOAK_DARKEST)
            R(14, 21, 1, 6, P.C_CLOAK_MID)
            R(11 + int(w1), 26, 1, 6, P.C_CLOAK_MID)
            R(9 + int(w2), 33, 1, 4, P.C_CLOAK_LIGHT)
            R(10 + int(w3), 38, 1, 3, P.C_CLOAK_MID)
            # ujung sobek
            R(8 + int(w2), 38, 2, 2, P.C_CLOAK_DARKEST)
            R(10 + int(w3), 40, 2, 2, P.C_CLOAK_DARKEST)

        @staticmethod
        def _draw_pixel_quiver(R, RO, anim_name, wave):
            """Quiver kulit + 3 anak panah (fletching hijau-emas)."""
            P = SylaraV1Renderer
            if anim_name == "death":
                return
            sway = int(round(math.sin(wave + 0.6) * 0.6))
            RO(13 + sway, 18, 4, 11, P.C_LEATHER_DARK)
            R(14 + sway, 19, 2, 9, P.C_LEATHER_MID)
            R(14 + sway, 24, 2, 1, P.C_LEATHER_HIGH)
            # tali quiver
            R(14 + sway, 22, 2, 1, P.C_GOLD_DARK)
            # batang panah menyembul di atas bahu
            for i, (dx, dy) in enumerate(((0, 0), (2, -1), (4, 0))):
                R(14 + sway + dx, 12 + dy, 1, 7, P.C_ARROW_SHAFT_D)
                R(14 + sway + dx, 12 + dy, 1, 6, P.C_ARROW_SHAFT)
                col = P.C_ARROW_FEATHER_D if i % 2 else P.C_LEAF_EMBER
                R(13 + sway + dx, 10 + dy, 2, 2, col)
                R(14 + sway + dx, 9 + dy, 1, 1, P.C_LEATHER_DARKEST)

        @staticmethod
        def _draw_pixel_legs(R, RO, leg_pose, anim_name):
            """Paha hijau + boot kulit 3 band (pola Kaizen: rect grid).

            ``leg_pose`` 0..3 = fase langkah; ``windrun`` memakai pose
            meluncur rendah (kaki ditekuk ke depan) alih-alih lari biasa.
            """
            P = SylaraV1Renderer
            if anim_name == "death":
                return
            if anim_name == "windrun":
                RO(21, 32, 6, 7, P.C_CLOTH_DARK)
                RO(26, 34, 7, 5, P.C_CLOTH_MID)
                RO(19, 39, 9, 5, P.C_LEATHER_DARK)
                RO(28, 39, 8, 5, P.C_LEATHER_MID)
                R(19, 39, 8, 2, P.C_LEATHER_MID)
                R(29, 39, 7, 2, P.C_LEATHER_LIGHT)
                return
            poses = (
                ((16, 31, 6, 8), (26, 31, 6, 8),
                 (15, 38, 8, 7), (25, 38, 8, 7)),
                ((18, 31, 6, 7), (25, 31, 6, 7),
                 (17, 38, 8, 7), (24, 38, 8, 7)),
                ((16, 31, 6, 8), (27, 31, 6, 7),
                 (15, 38, 8, 7), (26, 38, 8, 7)),
                ((19, 31, 6, 7), (24, 31, 6, 8),
                 (18, 38, 8, 7), (23, 39, 8, 6)),
            )
            if anim_name == "idle":
                pose = poses[0]
            elif anim_name in ("attack", "swing", "focus", "shackle",
                               "powershot"):
                # kuda-kuda bertarung: kaki depan sedikit lebih lebar
                pose = poses[3]
            else:
                pose = poses[int(leg_pose) % len(poses)]
            for box in pose[:2]:
                RO(*box, P.C_CLOTH_DARK)
                R(box[0], box[1], box[2] - 1, 3, P.C_CLOTH_MID)
            for box in pose[2:]:
                RO(*box, P.C_LEATHER_DARK)
                R(box[0], box[1], box[2] - 1, 2, P.C_LEATHER_MID)
                R(box[0], box[1] + 2, box[2] - 2, 2, P.C_LEATHER_LIGHT)
                R(box[0], box[1] + box[3] - 2, box[2], 2,
                  P.C_LEATHER_DARKEST)

        @staticmethod
        def _draw_pixel_torso(R, RO, detail, skill_glow=None):
            """Korset hijau ber-strap kulit + gesper emas + pauldron."""
            P = SylaraV1Renderer
            RO(17, 19, 14, 12, P.C_CLOTH_DARK)
            R(18, 20, 12, 10, P.C_CLOTH_MID)
            R(18, 20, 5, 5, P.C_CLOTH_LIGHT)
            R(18, 20, 3, 2, P.C_CLOTH_HIGH)
            # strap kulit menyilang dada
            R(19, 23, 10, 2, P.C_LEATHER_DARK)
            R(20, 22, 8, 1, P.C_LEATHER_MID)
            R(19, 27, 10, 2, P.C_LEATHER_DARK)
            R(20, 27, 8, 1, P.C_LEATHER_MID)
            # gesper emas
            R(23, 25, 3, 3, P.C_GOLD_DARK)
            R(23, 25, 3, 2, P.C_GOLD_MID)
            R(23, 25, 1, 1, P.C_GOLD_SHINE)
            # plastron kulit di perut (bidang gelap pemecah massa hijau)
            RO(19, 25, 10, 4, P.C_LEATHER_DARK)
            R(20, 25, 8, 2, P.C_LEATHER_MID)
            R(20, 26, 3, 1, P.C_LEATHER_LIGHT)
            # lipatan kain tunic di bawah dada
            R(19, 22, 9, 1, P.C_CLOTH_HIGH)
            R(19, 23, 2, 1, P.C_CLOTH_LIGHT)
            R(26, 23, 2, 1, P.C_CLOTH_LIGHT)
            # hem bawah: bayangan tipis sebagai penutup
            R(17, 30, 14, 1, P.C_CLOTH_DARK)
            # sabuk tunic: garis emas memecah massa hijau
            R(18, 29, 12, 1, P.C_GOLD_DARK)
            R(19, 29, 6, 1, P.C_GOLD_MID)
            R(28, 29, 2, 1, P.C_GOLD_SHINE)
            # pauldron / bahu cape
            RO(14, 18, 5, 4, P.C_CLOAK_DARK)
            R(15, 18, 3, 2, P.C_CLOAK_MID)
            RO(28, 18, 5, 4, P.C_CLOAK_DARK)
            R(29, 18, 3, 2, P.C_CLOAK_MID)
            if detail:
                R(26, 21, 3, 1, P.C_CLOTH_HIGH)
                R(19, 26, 1, 1, P.C_LEATHER_HIGH)
            if skill_glow is not None:
                R(18, 29, 12, 1, skill_glow)

        @staticmethod
        def _draw_pixel_hair(R, RO, head_y, wave, anim_name, wave_amt):
            """Rambut merah Wind Ranger: poni depan + ponytail berkibar."""
            P = SylaraV1Renderer
            w1 = int(round(math.sin(wave) * wave_amt))
            w2 = int(round(math.sin(wave + 1.2) * wave_amt))
            w3 = int(round(math.sin(wave + 2.4) * wave_amt))
            long_hair = anim_name not in ("death",)
            if long_hair:
                RO(12 + w1, 8 + head_y, 4, 5, P.C_HAIR_DARKEST)
                RO(10 + w2, 11 + head_y, 3, 6, P.C_HAIR_DARK)
                RO(12 + w2, 16 + head_y, 3, 5, P.C_HAIR_DARK)
                RO(10 + w3, 20 + head_y, 3, 6, P.C_HAIR_DARKEST)
                R(11 + w2, 12 + head_y, 1, 7, P.C_HAIR_DARK)
                R(12 + w1, 9 + head_y, 1, 2, P.C_HAIR_MID)
                R(11 + w3, 21 + head_y, 1, 4, P.C_HAIR_MID)
                R(12 + w3, 24 + head_y, 1, 2, P.C_HAIR_LIGHT)
            # poni depan di bawah tepi hood
            R(19, 8 + head_y, 9, 2, P.C_HAIR_DARK)
            R(20, 8 + head_y, 6, 1, P.C_HAIR_MID)
            R(24, 8 + head_y, 1, 3, P.C_HAIR_LIGHT)
            R(17, 9 + head_y, 2, 5, P.C_HAIR_DARK)
            R(17, 9 + head_y, 1, 3, P.C_HAIR_MID)

        @staticmethod
        def _draw_pixel_hood(R, RO, head_y, anim_name):
            """Hood hijau runcing + wajah + mata hijau (identitas Sylara)."""
            P = SylaraV1Renderer
            # kubah hood: bahu lebar
            RO(15, 3 + head_y, 16, 9, P.C_HOOD_MID)
            RO(14, 8 + head_y, 18, 8, P.C_HOOD_MID)
            R(16, 4 + head_y, 12, 4, P.C_HOOD_LIGHT)
            R(17, 4 + head_y, 7, 2, P.C_CLOTH_HIGH)
            R(15, 8 + head_y, 2, 6, P.C_HOOD_DARK)
            R(29, 8 + head_y, 2, 6, P.C_HOOD_DARK)
            # sudut atas dibulatkan (kalau tidak, hood terbaca kotak)
            R(17, 2 + head_y, 12, 1, P.C_HOOD_MID)
            R(15, 3 + head_y, 2, 1, P.C_HOOD_DARK)
            R(29, 3 + head_y, 2, 1, P.C_HOOD_DARK)
            # crest tersapu ke BELAKANG: 2 bar bertingkat, bukan antena
            R(16, 1 + head_y, 9, 2, P.C_HOOD_DARK)
            R(12, -1 + head_y, 7, 2, P.C_HOOD_MID)
            R(13, -1 + head_y, 4, 1, P.C_HOOD_LIGHT)
            R(9, -1 + head_y, 3, 2, P.C_HOOD_DARK)
            R(9, -1 + head_y, 1, 1, P.C_CLOTH_HIGH)
            # brim: wajah masuk ke bayangan hood (2 baris tergelap)
            R(19, 9 + head_y, 10, 1, P.C_HOOD_DARK)
            R(28, 10 + head_y, 2, 5, P.C_HOOD_DARK)
            R(19, 10 + head_y, 1, 5, P.C_HOOD_DARK)
            R(19, 15 + head_y, 1, 1, P.C_GOLD_LIGHT)
            # wajah: kulit GELAP karena di dalam hood; highlight hanya 1 kolom
            R(20, 11 + head_y, 8, 6, P.C_SKIN_DARK)
            R(20, 11 + head_y, 8, 1, P.C_HOOD_DARKEST)
            R(20, 16 + head_y, 8, 1, P.C_SKIN_DARKEST)
            R(21, 12 + head_y, 1, 4, P.C_SKIN_MID)
            # poni merah: dua helai pendek dari bawah brim (bukan Ikat kepala)
            R(21, 11 + head_y, 2, 1, P.C_HAIR_DARK)
            R(25, 11 + head_y, 1, 1, P.C_HAIR_DARK)
            R(21, 12 + head_y, 1, 2, P.C_HAIR_MID)
            R(25, 12 + head_y, 1, 1, P.C_HAIR_LIGHT)
            if anim_name in ("hurt", "death"):
                R(22, 13 + head_y, 1, 1, P.C_OUTLINE)
                R(25, 13 + head_y, 1, 1, P.C_OUTLINE)
            else:
                # mata ramping 1x2 px: iris + 1 px highlight, bukan blok
                R(22, 12 + head_y, 1, 2, P.C_EYE_IRIS)
                R(25, 12 + head_y, 1, 2, P.C_EYE_IRIS)
                R(22, 12 + head_y, 1, 1, P.C_EYE_WHITE)
                R(25, 12 + head_y, 1, 1, P.C_EYE_WHITE)
                R(22, 13 + head_y, 1, 1, P.C_EYE_IRIS_LIGHT)
                R(25, 13 + head_y, 1, 1, P.C_EYE_IRIS_LIGHT)
            R(23, 15 + head_y, 2, 1, P.C_LIPS_DARK)
            R(23, 15 + head_y, 1, 1, P.C_LIPS_MID)

        @staticmethod
        def _draw_pixel_arms(R, RO, point, line, grip_src, nock_src, draw_amt,
                             anim_name):
            """Lengan depan (tarik tali) + sarung tangan kulit."""
            P = SylaraV1Renderer
            sx, sy = P.SHOULDER_SRC
            if anim_name == "death":
                return
            dx, dy = nock_src
            ex = (sx + dx) * 0.5 - 1.0
            ey = (sy + dy) * 0.5 + 2.0
            RO(ex, ey, 4, 4, P.C_CLOTH_MID)
            RO(dx, dy, 4, 4, P.C_SKIN_MID)
            if draw_amt > 0.05:
                R(dx, dy, 3, 3, P.C_LEATHER_MID)
                R(dx, dy + 2, 3, 1, P.C_LEATHER_DARK)
                R(dx, dy, 1, 1, P.C_LEATHER_HIGH)
            # lengan busur (depan, lebih terang = dekat kamera).  Digambar
            # sebagai LIMB bahu->grip supaya busur tidak pernah lepas dari
            # badan saat sapuan melebar.
            bx, by = grip_src
            line((sx, sy), (bx, by), P.C_OUTLINE, 4.6)
            line((sx, sy), (bx, by), P.C_CLOTH_LIGHT, 3.0)
            mx = sx + (bx - sx) * 0.55
            my = sy + (by - sy) * 0.55
            R(mx - 1, my - 1, 3, 3, P.C_CLOTH_MID)
            RO(bx - 1, by - 1, 4, 4, P.C_SKIN_LIGHT)
            R(bx, by + 1, 3, 3, P.C_LEATHER_LIGHT)
            R(bx, by + 1, 1, 1, P.C_LEATHER_HIGH)

        @staticmethod
        def _draw_pixel_bow(surface, R, RO, point, line, grip, tilt, draw_amt,
                            phase, glow=False):
            """Busur recurve pose-driven: limb, tali, anak panah ternock."""
            P = SylaraV1Renderer
            limb = P.BOW_LIMB_SRC
            nock = P._bow_nock_src(grip, tilt, draw_amt)
            tips = {}
            for sign in (1, -1):
                pts = []
                for i in range(6):
                    s = i / 5.0
                    u = sign * limb * s
                    v = P._bow_limb_offset(s, draw_amt)
                    pts.append(P._bow_point_src(grip, tilt, u, v))
                key = "up" if sign > 0 else "low"
                tips[key] = pts[-1]
                for i in range(len(pts) - 1):
                    line(pts[i], pts[i + 1], P.C_OUTLINE, 3)
                for i in range(len(pts) - 1):
                    line(pts[i], pts[i + 1], P.C_WOOD_MID, 2)
                for i in range(1, len(pts) - 1):
                    line(pts[i], pts[i + 1],
                         P.C_WOOD_SHINE if sign > 0 else P.C_WOOD_LIGHT, 1)
            # grip wrap (kulit) di tengah busur
            gx, gy = grip
            R(gx - 1, gy - 2, 3, 5, P.C_LEATHER_DARK)
            R(gx, gy - 1, 2, 3, P.C_LEATHER_MID)
            R(gx, gy, 1, 1, P.C_LEATHER_HIGH)
            # tali: tip -> nock -> tip (2 px outline, 1 px tali)
            for a, b in ((tips["up"], nock), (nock, tips["low"])):
                line(a, b, P.C_OUTLINE, 2)
            for a, b in ((tips["up"], nock), (nock, tips["low"])):
                line(a, b, P.C_STRING, 1)
                line(a, b, P.C_STRING_SHINE, 0.4)
            # panah ternock saat tali ditarik
            if draw_amt > 0.22:
                (_ux, _uy), (fx, fy) = P._bow_frame(tilt)
                ln = 10.0 + 8.0 * draw_amt
                hx = nock[0] + fx * ln
                hy = nock[1] + fy * ln
                line(nock, (hx, hy), P.C_OUTLINE, 3)
                line(nock, (hx, hy), P.C_ARROW_SHAFT, 2)
                line(nock, (hx, hy), P.C_WOOD_SHINE, 0.5)
                # mata panah
                P._poly(surface, (*P.C_ARROW_HEAD_D,
                                  int(210 + 45 * draw_amt)),
                        [point(hx + fx * 2.4, hy + fy * 2.4),
                         point(hx - (fy * 1.6), hy + (fx * 1.6)),
                         point(hx + (fy * 1.6), hy - (fx * 1.6))])
                # bulu panah
                R(nock[0] + fx * 1.5 - 1, nock[1] + fy * 1.5 - 1, 2, 2,
                  P.C_ARROW_FEATHER)
                R(nock[0] + fx * 3.5 - 1, nock[1] + fy * 3.5 - 1, 2, 2,
                  P.C_ARROW_FEATHER_D)
            if glow:
                P._spark_star(surface, *point(grip[0] + 1, grip[1] - 1),
                              4, P.C_WIND_WHITE, 150, 4,
                              rot=float(phase) * 3.0)

        # ------------------------------------------------------------------
        # SPRITE ASSEMBLER (satu frame rig penuh).
        # ------------------------------------------------------------------
        @staticmethod
        def _draw_sylara_sprite(surface, origin, flip_left, anim_name,
                                frame_idx, tint=(255, 255, 255, 255),
                                attack_progress=0.0, wave_amt=1.0,
                                wave=0.0, detail=False):
            P = SylaraV1Renderer
            body_y = body_x = head_y = 0
            leg_pose = 0
            crouch = 0
            dead = False
            flash = False
            draw_amt = 0.0
            grip = P.BOW_GRIP_SRC
            tilt = 0.30
            glow = False
            cape_amt = 0.6
            frame_idx = int(frame_idx)

            if anim_name == "idle":
                body_y = 1 if frame_idx % 2 else 0
                head_y = body_y
            elif anim_name == "walk":
                body_y = -1 if frame_idx % 2 else 0
                head_y = body_y
                leg_pose = frame_idx % 4
                body_x = (1, 0, -1, 0)[leg_pose]
                cape_amt = 1.8
            elif anim_name == "attack":
                pose = P._attack_pose(attack_progress)
                body_y = pose["bob"]
                body_x = pose["lean"] * 0.35
                head_y = max(-1, min(2, int(round(pose["bob"] / 2.0))))
                cape_amt = 3.4
                grip, tilt, draw_amt = P._bow_pose_local(
                    "attack", attack_progress, wave)
                if pose["tremble"]:
                    body_x += (1 if int(wave * 31) % 2 else -1) * 0.5
            elif anim_name == "swing":
                pose = P._swing_arc_pose(attack_progress)
                body_x = pose["lean"] * 0.30
                body_y = int(round(pose["bob"]))
                head_y = 1 if pose["bob"] > 1 else 0
                cape_amt = 4.2
                grip, tilt, draw_amt = P._bow_pose_local(
                    "swing", attack_progress, wave)
            elif anim_name == "windrun":
                body_x, body_y, crouch = 2, 1, 1
                cape_amt = 5.0
                leg_pose = frame_idx
                grip, tilt, draw_amt = P._bow_pose_local("windrun", 0.0, wave)
            elif anim_name == "focus":
                body_y = -1
                cape_amt = 2.6
                grip, tilt, draw_amt = P._bow_pose_local("focus", 0.0, wave)
                glow = True
            elif anim_name == "shackle":
                body_x = 1
                cape_amt = 2.8
                grip, tilt, draw_amt = P._bow_pose_local("shackle", 0.0, wave)
                glow = True
            elif anim_name == "powershot":
                pose = P._attack_pose(0.45)
                body_y = pose["bob"]
                body_x = pose["lean"] * 0.30
                head_y = 1
                cape_amt = 4.6
                grip, tilt, draw_amt = P._bow_pose_local("powershot", 0.0,
                                                         wave)
                glow = True
            elif anim_name == "hurt":
                flash = True
                body_x = 3 if not flip_left else -3
                head_y, body_y = -1, (1 if frame_idx == 1 else 0)
                grip, tilt, draw_amt = P._bow_pose_local("focus", 0.0, wave)
            elif anim_name == "death":
                if frame_idx == 0:
                    flash, head_y = True, -1
                elif frame_idx == 1:
                    crouch, head_y = 3, 2
                    body_y = 3
                    body_x = -1
                    grip, tilt, draw_amt = (25.5, 27.5), 1.15, 0.0
                elif frame_idx == 2:
                    crouch, head_y = 6, 5
                    body_y = 5
                    body_x = -2
                    grip, tilt, draw_amt = (24.0, 32.0), 1.45, 0.0
                else:
                    dead = True

            use_tint = (255, 89, 89, 255) if flash else tint
            R, RO, point, line = P._make_pixel_ops(
                surface, origin[0], origin[1], -1 if flip_left else 1,
                body_x, body_y, crouch, use_tint)

            if anim_name == "death" and frame_idx in (1, 2):
                fold = 2 * frame_idx
                RO(16, 33 + fold, 7, 6, P.C_CLOTH_DARK)
                RO(25, 33 + fold, 7, 5, P.C_CLOTH_DARK)
                R(17, 34 + fold, 5, 2, P.C_CLOTH_MID)
                RO(15, 39 + fold, 9, 5, P.C_LEATHER_DARK)
                RO(24, 39 + fold, 9, 5, P.C_LEATHER_DARK)
                R(16, 40 + fold, 7, 2, P.C_LEATHER_MID)
                R(25, 40 + fold, 7, 2, P.C_LEATHER_MID)

            if dead:
                RO(12, 41, 19, 5, P.C_CLOTH_DARK)
                R(14, 42, 15, 3, P.C_CLOTH_MID)
                RO(13, 38, 8, 5, P.C_HOOD_MID)
                R(15, 40, 4, 2, P.C_SKIN_DARK)
                R(14, 39, 3, 1, P.C_HAIR_DARK)
                line((20, 44), (38, 39), P.C_WOOD_DARKEST, 3)
                line((20, 44), (38, 39), P.C_WOOD_MID, 1)
                R(37, 38, 3, 2, P.C_STRING)
                return

            # Back-to-front: cape -> quiver -> lengan-tarik -> rambut ->
            # kaki -> torso -> tangan-busur -> hood -> busur.
            P._draw_pixel_cape(R, RO, cape_amt, anim_name, wave)
            P._draw_pixel_quiver(R, RO, anim_name, wave)
            P._draw_pixel_hair(R, RO, head_y, wave, anim_name, cape_amt * 0.6)
            P._draw_pixel_legs(R, RO, leg_pose, anim_name)
            P._draw_pixel_torso(R, RO, detail,
                                skill_glow=(P.C_WIND_MID if glow else None))
            nock_src = P._bow_nock_src(grip, tilt, draw_amt)
            P._draw_pixel_arms(R, RO, point, line, grip, nock_src, draw_amt,
                               anim_name)
            P._draw_pixel_hood(R, RO, head_y, anim_name)
            P._draw_pixel_bow(surface, R, RO, point, line, grip, tilt,
                              draw_amt, wave, glow=glow)

        # ------------------------------------------------------------------
        # Entry points: elite (kompatibel legacy) + body wrapper.
        # ------------------------------------------------------------------
        @staticmethod
        def _draw_sylara_elite(surface, cx, cy, facing, phase, action,
                               attack_progress=0.0, powered=False,
                               detail=False, focus=False, wind=False,
                               shackle=False, powershot=False, crit=False,
                               death_frame=0):
            """Komposisi akhir V1: satu frame rig pixel-art.

            ``action`` legacy (idle/walk/attack/swing/windrun) tetap
            didukung; kwarg skill (focus/wind/shackle/powershot) membuat
            badan IKUT berubah pose — bukan sekadar sticker FX.
            """
            P = SylaraV1Renderer
            anim = action
            if shackle:
                anim = "shackle"
            elif powershot or crit:
                anim = "powershot"
            elif focus:
                anim = "focus"
            elif wind:
                anim = "windrun"
            if anim in ("attack", "swing"):
                frame = min(4, max(0, int(float(attack_progress) * 5.0)))
            elif anim == "death":
                frame = min(3, max(0, int(death_frame)))
            else:
                counts = {"windrun": 4, "focus": 4, "shackle": 3,
                          "powershot": 4, "hurt": 3}
                frame = int(float(phase) * 8.0) % counts.get(anim, 4)
            P._draw_sylara_sprite(
                surface, (cx, cy), facing < 0, anim, frame,
                attack_progress=float(attack_progress),
                wave=float(phase) * 1.7, detail=bool(detail))
            f = -1 if facing < 0 else 1
            # Cluster rim hijau di ujung hood + kilau gesper ikut turun-scale.
            P._rect(surface, (*P.C_CLOTH_HIGH, 225),
                    (cx + f * 14, cy - 13, 2, 1))
            P._rect(surface, (*P.C_GOLD_SHINE, 220),
                    (cx + f * 1, cy + 2, 1, 1))
            if detail and anim != "death":
                if focus or wind or shackle or powershot or crit:
                    P._draw_sylara_skill_overlay(
                        surface, cx, cy, facing, phase, anim,
                        float(attack_progress), focus=focus, wind=wind,
                        shackle=shackle, powershot=powershot, crit=crit)
                y = cy - 34
                P._rect(surface, (*P.C_WIND_LIGHT, 240),
                        (cx + f * 4 - 1, y, 2, 1))
                P._rect(surface, (*P.C_ARROW_FEATHER, 230),
                        (cx + f * 9, y + 4, 1, 1))
                P._rect(surface, (*P.C_HAIR_SHINE, 230),
                        (cx - f * 12, cy - 30, 1, 2))

        @staticmethod
        def _draw_sylara_body(surface, cx, cy, facing, phase, action,
                              attack_progress=0, powered=False, detail=False,
                              focus=False, wind=False, shackle=False,
                              powershot=False, crit=False, death_frame=0):
            SylaraV1Renderer._draw_sylara_elite(
                surface, cx, cy, facing, phase, action, attack_progress,
                powered=powered, detail=detail, focus=focus, wind=wind,
                shackle=shackle, powershot=powershot, crit=crit,
                death_frame=death_frame)

        @staticmethod
        def _draw_sylara_skill_overlay(surface, cx, cy, facing, phase, action,
                                       attack_progress=0.0, focus=False,
                                       wind=False, shackle=False,
                                       powershot=False, crit=False):
            """Glow reaktif ringan di badan saat skill aktif (aksen depan)."""
            P = SylaraV1Renderer
            f = 1 if facing >= 0 else -1
            pulse = math.sin(phase * 3.2) * 0.5 + 0.5
            if focus or powershot or crit:
                bx, by = P._bow_grip_position(cx, cy, facing, phase, "focus")
                P._aacircle(surface, (*P.C_WIND_BRIGHT, int(60 + 50 * pulse)),
                            (bx, by), int(5 + 2 * pulse))
                P._aacircle(surface, P.C_WIND_WHITE, (bx + f * 2, by), 1)
                P._aaline(surface, (*P.C_CLOTH_HIGH, 110),
                          (cx - 6 * f, cy - 30), (cx - 10 * f, cy + 4), 1)
            if focus:
                P._dashed_ring(surface, cx + f * 12, cy - 6,
                               int(9 + 2 * pulse), P.C_WIND_BRIGHT,
                               int(140 + 50 * pulse), phase * 2.2,
                               dashes=6, width=2, squash=0.55)
            if powershot:
                P._aacircle(surface, (*P.C_WIND_WHITE, 200),
                            (cx + f * 16, cy - 6), int(3 + 2 * pulse))
            if shackle:
                P._dashed_ring(surface, cx + f * 12, cy - 4,
                               int(10 + 2 * pulse), P.C_WIND_LIGHT,
                               int(150 + 50 * pulse), -phase * 2.6,
                               dashes=8, width=2, squash=0.55)
            if wind:
                for i in range(4):
                    al = 42 - i * 9
                    if al > 0:
                        P._aacircle(surface, (*P.C_WIND_MID, al),
                                    (cx, cy - 2), int(18 + i * 5), 1)

        # ------------------------------------------------------------------
        # Ambient (canvas fallback).
        # ------------------------------------------------------------------
        @staticmethod
        def _draw_shadow(surface, x, y):
            P = SylaraV1Renderer
            P._ellipse(surface, (*P.C_OUTLINE, 110),
                       (int(x - 26), int(y - 5), 52, 9))
            P._ellipse(surface, (*P.C_WIND_DARKEST, 60),
                       (int(x - 18), int(y - 3), 36, 6))

        @staticmethod
        def _draw_ranger_silhouette_glow(surface, x, y, phase):
            P = SylaraV1Renderer
            alpha = int(30 + 22 * (.5 + .5 * math.sin(phase)))
            P._ellipse(surface, (*P.C_WIND_MID, alpha),
                       (int(x - 20), int(y - 30), 40, 60), 2)

        @staticmethod
        def _draw_wind_aura(surface, x, y, phase):
            P = SylaraV1Renderer
            for i in range(3):
                r = 26 + i * 6 + int(math.sin(phase * 1.5 + i) * 2)
                P._dashed_ring(surface, x, y + 6, r, P.C_WIND_MID,
                               30 - i * 6, phase * .4 + i, dashes=10,
                               width=1, squash=.35)

        @staticmethod
        def _draw_wind_platform(surface, x, y, phase, skill):
            P = SylaraV1Renderer
            P._dashed_ring(surface, x, y, 26, P.C_WIND_MID, 105, phase * .3,
                           dashes=12, width=2, squash=.27)
            P._dashed_ring(surface, x, y, 40, P.C_CLOAK_LIGHT, 58,
                           -phase * .2, dashes=9, width=1, squash=.2)
            for i in range(3):
                a = phase * .15 + i * math.tau / 3
                P._spark_star(surface, x + math.cos(a) * 32,
                              y + math.sin(a) * 9, 3, P.C_WIND_WHITE, 160,
                              4, rot=a)

        @staticmethod
        def _draw_floating_wind(surface, cx, cy, phase, trail=False,
                                facing=1, intense=False):
            P = SylaraV1Renderer
            strength = 1.6 if intense else 1.0
            for i, offset in enumerate((-14, -5, 5, 14)):
                t = (phase * 0.5 + i * 0.25) % 1.0
                sx = cx + offset + int(math.sin(phase + i) * 3)
                sy = cy + 4 - int(t * 18)
                alpha = int(150 * (1 - t) * strength)
                if alpha <= 8:
                    continue
                P._aaline(surface, (*P.C_WIND_MID, alpha), (sx, sy),
                          (sx - facing * 6, sy - 3), 2)
                P._spark_star(surface, sx, sy, 3, P.C_WIND_BRIGHT, alpha,
                              4, rot=phase + i)
            # daun angin mengorbit
            for i in range(3):
                a = phase * 1.0 + i * math.tau / 3
                r = 16 + math.sin(phase + i * 1.3) * 4
                lx = cx + math.cos(a) * r
                ly = cy + math.sin(a) * r * 0.35
                P._draw_sylara_leaf(surface, lx, ly, 3.4, a, phase)
            if trail:
                for i in range(4):
                    sy = cy + int(math.sin(phase + i) * 2)
                    P._aaline(surface, (*P.C_WIND_DARK, 90 - i * 20),
                              (cx - facing * (10 + i * 9), sy),
                              (cx - facing * (22 + i * 11), sy), 1)

        @staticmethod
        def _draw_sylara_leaf(surface, cx, cy, size, angle, phase=0.0):
            """Daun kecil tema hutan (aksen identitas, bukan partikel generik)."""
            P = SylaraV1Renderer
            ca, sa = math.cos(angle), math.sin(angle)
            px, py = -sa, ca
            tip = (cx + ca * size, cy + sa * size * 0.7)
            base = (cx - ca * size * 0.5, cy - sa * size * 0.5)
            side = (cx + px * size * 0.55, cy + py * size * 0.55)
            P._poly(surface, (*P.C_LEAF_GOLD, 210), [tip, side, base])
            P._poly(surface, (*P.C_WIND_LIGHT, 190),
                    [(cx - ca * size * 0.2, cy - sa * size * 0.2), tip, base])
            P._aaline(surface, (*P.C_LEAF_EMBER, 170), base, tip, 1)

        @staticmethod
        def _draw_floating_wind_legacy(surface, cx, cy, phase, trail=False,
                                       facing=1, intense=False):
            return SylaraV1Renderer._draw_floating_wind(
                surface, cx, cy, phase, trail, facing, intense)

        # ------------------------------------------------------------------
        # SKILL FX — Q Focus Fire.
        # ------------------------------------------------------------------
        @staticmethod
        def _draw_focus_fire_ground(surface, boss, x, y, timer, phase):
            """Q — koridor bidik + halo rumput (massa di lapisan TANAH)."""
            P = SylaraV1Renderer
            progress = P._skill_progress("q", timer)
            facing = getattr(boss, "direction", 1)
            pulse = math.sin(phase * 2.2) * 0.25 + 0.75
            fs = P._fx_scale(boss)
            world_r = int(getattr(boss, "skill_range", 200) or 200)
            rng = P._ring_r(boss, world_r, surface)
            gy = y + P.GROUND_LOCAL       # proyeksi tanah dekat kaki
            ang = 0.0 if facing > 0 else math.pi
            bow_x, bow_y = P._bow_grip_position(x, y, facing, phase, "focus")

            alpha = int(150 * (1.0 - abs(progress - 0.45) * 1.1))
            if alpha > 6:
                # koridor tembak, di-SQUASH ke bidang tanah
                for side in (-1, 1):
                    P._aaline(surface, (*P.C_WIND_DARK, alpha),
                              (bow_x, gy + side * 5),
                              (bow_x + facing * rng, gy + side * 3), 2)
                n_chev = 5
                for i in range(n_chev):
                    t = ((progress * 1.6 + i / float(n_chev)) % 1.0)
                    cx = bow_x + facing * rng * t
                    P._chevron(surface, cx, gy, ang, 5, P.C_WIND_LIGHT,
                               int(alpha * (1.0 - t * 0.5)), 2)
                P._ellipse(surface, (*P.C_WIND_DARK, int(alpha * 0.8)),
                           (bow_x - 16, gy - 7, 32, 14))
                P._sy_grass_halo(surface, x, gy, max(14, rng // 3),
                                 phase, int(120 + 50 * pulse),
                                 squash=P.GROUND_SQUASH)
                # cincin fletching baca-jangkauan
                mark_r = max(20, int(rng * 0.55))
                P._dashed_ring(surface, x, gy, mark_r, P.C_WIND_MID,
                               int(105 + 45 * pulse), phase * 0.4,
                               dashes=8, width=2, squash=0.5)
                for i in range(5):
                    a = phase * 0.4 + i * math.tau / 5
                    P._fletch_pixel(surface, x + math.cos(a) * mark_r,
                                    gy + math.sin(a) * mark_r * 0.5,
                                    a + math.pi * 0.5, 3.0,
                                    int(150 + 50 * pulse))
            if progress < 0.14:
                P._skill_leaf_burst(surface, bow_x, bow_y, progress / 0.14,
                                    fs)
            if progress > 0.80:
                t = (progress - 0.80) / 0.20
                # penutup volley — massa tetap di tanah
                P._aoe_marks(surface, x, gy, max(18, rng // 2), P.C_WIND_LIGHT,
                             int(140 * (1 - t)), phase, squash=0.5,
                             ticks=10, tick_len=5)

        @staticmethod
        def _draw_focus_fire_effect(surface, boss, x, y, timer, phase):
            """Q — aksen depan: spiral fletching kecil di busur + volley.

            Volley panah visual dilepas berkala dari busur (damage=0) —
            di sini, bukan di pose serangan, supaya Q yang tidak memakai
            pose ATTACK tetap melepas anak panahnya.
            """
            P = SylaraV1Renderer
            progress = P._skill_progress("q", timer)
            if not getattr(boss, "_portrait_hd", False):
                if not hasattr(boss, "_sy_focus_last_shot"):
                    boss._sy_focus_last_shot = -100
                if 0.2 < progress < 0.9 and timer % 10 == 0 \
                        and boss._sy_focus_last_shot != timer:
                    P._spawn_focus_fire_volley(boss, x, y)
                    boss._sy_focus_last_shot = timer
                if progress < 0.2:
                    boss._sy_focus_last_shot = -100
            if progress < 0.2 or progress > 0.92:
                return
            facing = getattr(boss, "direction", 1)
            fx = P._fx_scale(boss)
            bx, by = P._bow_grip_position(x, y, facing, phase, "focus")
            for i in range(4):
                a = phase * 2.8 + i * math.tau / 4
                r = 7 + 3 * math.sin(phase * 2 + i)
                P._spark_star(surface, bx + math.cos(a) * r,
                              by + math.sin(a) * r * 0.7, 3,
                              P.C_WIND_BRIGHT, 170, 4, rot=a)
            P._spark_star(surface, bx, by, 6 * fx, P.C_WIND_WHITE,
                          130 + 60 * math.sin(phase * 4), 4, rot=phase)

        # ------------------------------------------------------------------
        # SKILL FX — W Windrun.
        # ------------------------------------------------------------------
        @staticmethod
        def _draw_windrun_ground(surface, boss, x, y, timer, phase):
            """W — halo rumput di radius DUNIA 70 + siklon daun (TANAH)."""
            P = SylaraV1Renderer
            progress = P._skill_progress("w", timer)
            facing = getattr(boss, "direction", 1)
            pulse = math.sin(phase * 4.0) * 0.5 + 0.5
            fs = P._fx_scale(boss)
            rng = P._ring_r(boss, 70, surface)
            gy = y + P.GROUND_LOCAL
            if progress < 0.16:
                P._skill_leaf_burst(surface, x, gy, progress / 0.16, fs)
            P._sy_grass_halo(surface, x, gy, rng, phase,
                             int(140 + 60 * pulse), squash=P.GROUND_SQUASH)
            P._dashed_ring(surface, x, gy, max(8, int(rng * 0.58)),
                           P.C_WIND_LIGHT, int(105 + 45 * pulse),
                           -phase * 0.9, dashes=10, width=2, squash=0.45)
            for i in range(6):
                a = phase * 1.2 + i * math.tau / 6
                rr = rng * (0.6 + 0.35 * P._hash01(i * 13))
                P._draw_sylara_leaf(surface, x + math.cos(a) * rr,
                                    gy + math.sin(a) * rr * 0.45,
                                    max(2.5, 3.6 * fs), a + phase, phase)
            if progress > 0.78:
                t = (progress - 0.78) / 0.22
                P._dashed_ring(surface, x, gy,
                               max(6, int(rng * (1.0 - t * 0.7))),
                               P.C_WIND_WHITE, int(180 * t), phase * 2.0,
                               dashes=8, width=3, squash=0.45)
            # arah lari: fletching di tanah, bukan chevron generik
            for i in range(4):
                t = (i / 4.0 + phase * 0.35) % 1.0
                P._fletch_pixel(surface, x + facing * rng * (0.25 + 0.7 * t),
                                gy + math.sin(phase + i) * 3,
                                0.0 if facing > 0 else math.pi,
                                max(3.0, rng * 0.05),
                                int(170 * (1.0 - t * 0.4)))

        @staticmethod
        def _side_gust(surface, x, y, facing, phase, alpha,
                       base_y=-14, seed=0):
            """Hembusan pendek di SISI tubuh (aksen depan, bukan massa).

            Depan (arah hadap) = gust vertikal mulai 20 px dari pusat;
            belakang (sisi cape/rambut yang berkibar) = gust horizontal di
            BAWAH pinggang, di luar jangkauan cape.  Dengan begitu tidak
            ada aksen depan yang melintasi siluet badan.
            """
            P = SylaraV1Renderer
            if alpha <= 0:
                return
            for i in range(3):
                t = (phase * 0.5 + i / 3.0 + seed) % 1.0
                al = int(alpha * (1.0 - t) * (0.6 + 0.4 * (i % 2)))
                if al <= 0:
                    continue
                if facing >= 0:
                    sx = x + 20 + t * 16
                    sy = y + base_y + i * 10 + math.sin(phase * 2 + i) * 3
                    P._aaline(surface, (*P.C_WIND_DARK, al // 2), (sx, sy),
                              (sx + 12, sy - 2), 2)
                    P._aaline(surface, (*P.C_WIND_BRIGHT, al), (sx, sy),
                              (sx + 12, sy - 2), 1)
                else:
                    sx = x - (30 + t * 12)
                    sy = y + 28 + i * 6 + math.sin(phase * 2 + i) * 2
                    P._aaline(surface, (*P.C_WIND_DARK, al // 2), (sx, sy),
                              (sx - 14, sy - 1), 2)
                    P._aaline(surface, (*P.C_WIND_BRIGHT, al), (sx, sy),
                              (sx - 14, sy - 1), 1)

        @staticmethod
        def _draw_windrun_effect(surface, boss, x, y, timer, phase):
            """W — aksen depan: gust di SISI tubuh (tidak melintasi sprite).

            Massa (halo rumput, siklon daun) sudah digambar di lapisan
            tanah; di sini hanya hembusan pendek di depan & samping badan
            plus daun yang tersedot — semuanya dimulai >= 20 px dari pusat
            supaya siluet dan cape yang berkibar tetap utuh.
            """
            P = SylaraV1Renderer
            if getattr(boss, "_portrait_hd", False):
                return
            facing = getattr(boss, "direction", 1)
            progress = P._skill_progress("w", timer)
            pulse = math.sin(phase * 3.4) * 0.5 + 0.5
            P._side_gust(surface, x, y, facing, phase,
                         int(150 * (0.6 + 0.4 * pulse)))
            for i in range(2):
                t = (phase * 0.35 + i / 2.0) % 1.0
                if facing >= 0:
                    lx = x + 22 + t * 16
                    ly = y - 6 + math.sin(phase * 2 + i) * 8
                else:
                    lx = x - 34 - t * 14
                    ly = y + 26 + math.sin(phase * 2 + i) * 4
                P._draw_sylara_leaf(surface, lx, ly, 3.0,
                                    phase + i + (0.0 if facing >= 0
                                                 else math.pi), phase)
            if progress > 0.8:
                k = (progress - 0.8) / 0.2
                P._spark_star(surface, x + facing * 24, y + 4,
                              4 + 4 * k, P.C_WIND_WHITE, int(190 * (1 - k)),
                              4, rot=phase * 2)

        @staticmethod
        def _draw_windrun_trail(surface, x, y, facing, phase):
            """W — lembar angin di BELAKANG badan (dipakai jalur badan)."""
            P = SylaraV1Renderer
            # Semua streak/daun dimulai DI LUAR siluet badan (>= 20 px):
            # lapisan depan hanya aksen, tidak melintasi sprite.
            for i in range(5):
                t = (phase * 0.55 + i / 5.0) % 1.0
                sy = y - 12 + i * 6 + math.sin(phase * 2.1 + i) * 2
                sx = x - facing * (20 + t * 30)
                ex = sx - facing * (16 + t * 12)
                al = int(175 * (1.0 - t) * (0.55 + 0.45 * (i % 2)))
                if al <= 0:
                    continue
                P._aaline(surface, (*P.C_WIND_DARK, al // 2), (sx, sy),
                          (ex, sy - 1), 2)
                P._aaline(surface, (*P.C_WIND_BRIGHT, al), (sx, sy),
                          (ex, sy - 1), 1)
            for i in range(3):
                t = (phase * 0.4 + i / 3.0) % 1.0
                P._draw_sylara_leaf(surface, x - facing * (22 + t * 26),
                                    y - 8 + math.sin(phase * 2 + i) * 6,
                                    3.0, phase + i, phase)

        # ------------------------------------------------------------------
        # SKILL FX — E Shackle Shot.
        # ------------------------------------------------------------------
        @staticmethod
        def _draw_shackle_ground(surface, boss, x, y, timer, phase):
            """E — karangan daun di target + akar tanah (massa TANAH)."""
            P = SylaraV1Renderer
            progress = P._skill_progress("e", timer)
            facing = getattr(boss, "direction", 1)
            fs = P._fx_scale(boss)
            tx, ty = P._target_position(boss, x, y)
            gx, gy = P._bow_grip_position(x, y, facing, phase, "shackle")
            if progress < 0.16:
                P._skill_leaf_burst(surface, gx, gy, progress / 0.16, fs)
            al = int(165 + 45 * math.sin(phase * 3))
            wreath = max(8, int(14 * fs))
            gty = ty + P.GROUND_LOCAL
            P._sy_grass_halo(surface, tx, gty, wreath + 6, phase, al,
                             squash=P.GROUND_SQUASH)
            P._dashed_ring(surface, tx, gty, wreath, P.C_CLOTH_LIGHT,
                           int(130 + 50 * math.sin(phase)), phase * 1.4,
                           dashes=8, width=2, squash=0.42)
            if progress > 0.78:
                t = (progress - 0.78) / 0.22
                P._dashed_ring(surface, tx, gty,
                               max(5, int((wreath + 14 * fs) * (1.0 - t))),
                               P.C_LEAF_GOLD, int(200 * (0.4 + 0.6 * t)),
                               -phase * 2.0, dashes=8, width=3, squash=0.42)
                P._skill_leaf_burst(surface, tx, gty, t, fs)
            if not getattr(boss, "_sy_shackle_spawned", False):
                P._spawn_shackle(boss, x, y)
                boss._sy_shackle_spawned = True
            if timer < 5:
                boss._sy_shackle_spawned = False

        @staticmethod
        def _draw_shackle_effect(surface, boss, x, y, timer, phase):
            """E — aksen depan: sulur tipis dari busur ke target."""
            P = SylaraV1Renderer
            progress = P._skill_progress("e", timer)
            if progress < 0.1:
                return
            facing = getattr(boss, "direction", 1)
            fs = P._fx_scale(boss)
            tx, ty = P._target_position(boss, x, y)
            gx, gy = P._bow_grip_position(x, y, facing, phase, "shackle")
            al = int(200 * (1.0 - progress) ** 0.5)
            if al <= 6:
                return
            dx, dy = tx - gx, ty - 8 - gy
            dist = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / dist, dx / dist
            prev = None
            for i in range(11):
                t = i / 10.0
                wob = math.sin(t * 5.0 + phase * 2.4) * 4.0 * fs
                px = gx + dx * t + nx * wob
                py = gy + dy * t + ny * wob
                if prev is not None:
                    P._aaline(surface, (*P.C_CLOTH_DARKEST, al), prev,
                              (px, py), 3)
                    P._aaline(surface, (*P.C_WIND_LIGHT, al), prev,
                              (px, py), 1)
                if i % 3 == 0:
                    P._draw_sylara_leaf(surface, px + nx * 4, py + ny * 4,
                                        3.0 * fs, math.atan2(ny, nx), phase)
                prev = (px, py)

        # ------------------------------------------------------------------
        # SKILL FX — R Powershot.
        # ------------------------------------------------------------------
        @staticmethod
        def _draw_powershot_ground(surface, boss, x, y, timer, phase):
            """R — SEMUA massa besar di lapisan TANAH (cakram + cincin).

            Keluhan owner pada rig lama: cakram isi + cincin tebal
            mengembang digambar di depan badan sehingga menutupi sprite.
            Di V1 massa itu di-SQUASH ke bidang tanah (squash 0.45) dan
            digambar SEBELUM badan; lapisan depan hanya aksen ringan
            (lihat ``_draw_powershot_charge``).
            """
            P = SylaraV1Renderer
            progress = P._skill_progress("r", timer)
            facing = getattr(boss, "direction", 1)
            fs = P._fx_scale(boss)
            gy = y + P.GROUND_LOCAL
            radius = max(24, int(70 * fs))
            gx, gyy = P._bow_grip_position(x, y, facing, phase, "powershot")

            # fase: 0.0-0.45 charge, 0.45-0.62 release, 0.62-1.0 after
            if progress < 0.45:
                k = progress / 0.45
                P._aoe_marks(surface, x, gy, max(16, int(radius * 0.7)),
                             P.C_WIND_MID, int(120 + 60 * k), phase * 1.3,
                             squash=0.45, ticks=12, tick_len=6)
                P._ellipse(surface, (*P.C_WIND_DARK, int(70 + 60 * k)),
                           (x - int(radius * 0.45), gy - int(radius * 0.16),
                            int(radius * 0.9), int(radius * 0.32)))
                P._dashed_ring(surface, x, gy,
                               max(10, int(radius * (0.55 - k * 0.3))),
                               P.C_WIND_LIGHT, int(130 + 70 * k),
                               phase * 2.2, dashes=12, width=2, squash=0.45)
            else:
                k = min(1.0, (progress - 0.45) / 0.35)
                # cakram isi + dua cincin mengembang, semuanya di TANAH
                P._aacircle(surface,
                            (*P.C_WIND_DARK, int(70 * (1 - k * 0.5))),
                            (x, gy), int(radius * (0.35 + 0.55 * k)))
                P._dashed_ring(surface, x, gy,
                               int(radius * (0.5 + 0.85 * k)), P.C_WIND_WHITE,
                               int(200 * (1 - k * 0.4)), phase * 2.0,
                               dashes=16, width=3, squash=0.45)
                P._dashed_ring(surface, x, gy,
                               int(radius * (0.3 + 0.55 * k)), P.C_LEAF_GOLD,
                               int(170 * (1 - k * 0.4)), -phase * 1.4,
                               dashes=12, width=2, squash=0.45)
                # koridor gale di tanah menuju target
                tx, ty = P._target_position(boss, x, y)
                ang = math.atan2(ty - gy, tx - gx)
                for i in range(5):
                    t = (i / 5.0 + phase * 0.5) % 1.0
                    reach = radius * (1.3 + 1.9 * k)
                    cxp = gx + math.cos(ang) * reach * t
                    cyp = gy + math.sin(ang) * reach * t * 0.35
                    P._chevron(surface, cxp, cyp, ang, 4 + 2 * (1 - t),
                               P.C_WIND_BRIGHT, int(180 * (1 - t) * (1 - k * 0.4)),
                               2)
                if progress > 0.55:
                    P._skill_leaf_burst(
                        surface, tx, ty + 10, min(1.0, (progress - 0.55) / 0.3),
                        fs)
            if progress < 0.22:
                P._skill_leaf_burst(surface, gx, gyy, progress / 0.22, fs)

        @staticmethod
        def _draw_powershot_charge(surface, boss, x, y, timer, phase):
            """R — aksen depan: flash KECIL di busur + streak sisi tubuh."""
            P = SylaraV1Renderer
            progress = P._skill_progress("r", timer)
            facing = getattr(boss, "direction", 1)
            gx, gy = P._bow_grip_position(x, y, facing, phase, "powershot")
            if progress < 0.5:
                k = progress / 0.5
                # flash di senjata: radius DI-CAP supaya tidak menelan hood
                P._aacircle(surface, (*P.C_WIND_BRIGHT, int(120 * (1 - k))),
                            (gx, gy), 4 + int(3 * k))
                P._aacircle(surface, (*P.C_WIND_WHITE, int(180 * (1 - k))),
                            (gx, gy), 2 + int(2 * k))
                P._spark_star(surface, gx, gy, 5, P.C_WIND_WHITE,
                              int(170 * (1 - k)), 4, rot=phase)
            # Streak angin di sisi tubuh — aksen RINGAN, offset di luar
            # siluet (depan >= 20 px; sisi belakang turun ke bawah pinggang
            # supaya rambut/cape yang berkibar tidak tertutup).
            t = min(1.0, progress / 0.6)
            P._side_gust(surface, x, y, facing, phase,
                         int(140 * (1 - t * 0.35)), base_y=12 - int(26 * t),
                         seed=0.37)
            if progress < 0.5:
                k = progress / 0.5
                P._aacircle(surface, (*P.C_WIND_WHITE, int(90 * (1 - k))),
                            (x + facing * 26, y - 4), 1)
            if progress > 0.5:
                k = min(1.0, (progress - 0.5) / 0.5)
                P._spark_star(surface, gx + facing * 6, gy,
                              6 * (1 - k) + 2, P.C_WIND_WHITE,
                              int(200 * (1 - k)), 6, rot=phase * 2)

        # ------------------------------------------------------------------
        # HELPER FX KECIL (kosakata ranger: daun, fletching, rumput).
        # ------------------------------------------------------------------
        @staticmethod
        def _fletch_pixel(surface, x, y, ang, size, alpha):
            """Jejak bulu anak panah (bukan chevron generik)."""
            P = SylaraV1Renderer
            if alpha <= 0:
                return
            ca, sa = math.cos(ang), math.sin(ang)
            px, py = -sa, ca
            tip = (x + ca * size, y + sa * size)
            for s in (-1, 1):
                a = (x - ca * size * 0.4 + px * s * size * 0.55,
                     y - sa * size * 0.4 + py * s * size * 0.55)
                P._poly(surface, (*P.C_ARROW_FEATHER_D, int(alpha)),
                        [tip, a, (x - ca * size * 0.15, y - sa * size * 0.15)])
                P._poly(surface,
                        (*P.C_ARROW_FEATHER, int(alpha)),
                        [tip, (x + px * s * size * 0.28,
                               y + py * s * size * 0.28),
                         (x + ca * size * 0.35, y + sa * size * 0.35)])

        @staticmethod
        def _skill_leaf_burst(surface, cx, cy, t, fs=1.0):
            """Ledakan daun saat skill keluar (bahasa hutan, bukan bintang)."""
            P = SylaraV1Renderer
            t = max(0.0, min(1.0, float(t)))
            if t <= 0.01:
                return
            n = 8
            for i in range(n):
                a = i * math.tau / n + t * 0.4
                r = (7 + t * 22) * fs * (0.7 + 0.3 * P._hash01(i * 9))
                P._draw_sylara_leaf(surface, cx + math.cos(a) * r,
                                    cy + math.sin(a) * r * 0.5,
                                    max(2.2, (5.0 - t * 3.0) * fs),
                                    a + t * 2, t)

        @staticmethod
        def _sy_grass_halo(surface, cx, cy, radius, phase, alpha,
                           squash=1.0):
            """Cincin rumput pada radius dunia — telegraph khas hutan."""
            P = SylaraV1Renderer
            if alpha <= 0 or radius <= 2:
                return
            P._dashed_ring(surface, cx, cy, radius, P.C_WIND_MID,
                           int(alpha * 0.85), phase * 0.15, dashes=14,
                           width=3, squash=squash)
            P._dashed_ring(surface, cx, cy, max(4, int(radius * 0.92)),
                           P.C_WIND_BRIGHT, int(alpha * 0.7), -phase * 0.1,
                           dashes=10, width=1, squash=squash)
            blades = max(10, int(radius / 6))
            for i in range(blades):
                a = phase * 0.15 + i * math.tau / blades
                bx = cx + math.cos(a) * radius
                by = cy + math.sin(a) * radius * squash
                sway = math.sin(phase * 2.4 + i) * 3
                tipx = bx + math.cos(a) * 6 + sway
                tipy = by + math.sin(a) * 3 - 4
                col = P.C_LEAF_GOLD if i % 3 == 0 else P.C_WIND_LIGHT
                P._aaline(surface, (*col, int(alpha)), (bx, by),
                          (tipx, tipy), 2 if i % 2 == 0 else 1)

        @staticmethod
        def _sy_leaf_orbit(surface, cx, cy, radius, phase, count, fs,
                           squash=0.46):
            P = SylaraV1Renderer
            for i in range(count):
                t = (phase * 0.28 + i / float(count)) % 1.0
                a = phase * 0.9 + i * math.tau / count
                r = radius * (0.55 + 0.45 * P._hash01(i * 17))
                P._draw_sylara_leaf(
                    surface, cx + math.cos(a) * r,
                    cy + math.sin(a) * r * squash - t * 7 * fs,
                    max(2.2, (3.6 + (i % 3)) * fs * (1.0 - t * 0.35)),
                    a + t * 3.0, phase)

        # ------------------------------------------------------------------
        # PROYEKTIL (fallback canvas) — panah angin tema Sylara.
        # ------------------------------------------------------------------
        class WindBolt:
            """Panah angin visual basic attack (MURNI VISUAL, damage=0).

            Dilepas dari nock di titik rilis ayunan; touchdown hanya
            percikan lembut TANPA ImpactFX / hit-stop / shake — kontrak
            tools/test_basic_attack_no_impact_fx.py.
            """

            def __init__(self, sx, sy, tx, ty, speed=8.5, powered=False,
                         target=None, damage=0, team=None):
                self.x, self.y = float(sx), float(sy)
                self.tx, self.ty = float(tx), float(ty)
                self.speed = float(speed)
                self.powered = bool(powered)
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
                    src = getattr(self, "source", None)
                    if src is not None:
                        self.tx, self.ty = SylaraV1Renderer._world_to_local(
                            src, self.cx, self.cy, self.target.x,
                            self.target.y)
                    else:
                        self.tx = float(self.target.x)
                        self.ty = float(self.target.y)
                dx, dy = self.tx - self.x, self.ty - self.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    self.angle = math.atan2(dy, dx)
                if dist <= self.speed + 4:
                    self.alive = False
                    return
                self.trail.append((self.x, self.y))
                if len(self.trail) > (12 if self.powered else 8):
                    self.trail.pop(0)
                self.x += dx / dist * self.speed
                self.y += dy / dist * self.speed

            def draw(self, surface, phase):
                P = SylaraV1Renderer
                if not self.alive:
                    # Touchdown lembut: percikan memudar, tanpa impact FX.
                    t = max(0.0, 1.0 - self.dead_frames / 9.0)
                    if t > 0:
                        P._spark_star(surface, self.x, self.y, 8 * t,
                                      P.C_WIND_LIGHT, int(150 * t), 4,
                                      rot=phase)
                    return
                for i, (tx, ty) in enumerate(self.trail):
                    a = int(26 + 110 * i / max(1, len(self.trail) - 1))
                    sz = max(1, 4 - (len(self.trail) - i) // 3)
                    P._rect(surface, (*P.C_WIND_DARK, a),
                            (int(tx) - sz // 2, int(ty) - sz // 2, sz, sz))
                ca, sa = math.cos(self.angle), math.sin(self.angle)
                ln = 20 if self.powered else 14
                for i in range(ln):
                    t = i / float(ln)
                    P._rect(surface, (*P.C_WIND_LIGHT, int(30 + 150 * t)),
                            (int(self.x - ca * ln * 0.5 + ca * i),
                             int(self.y - sa * ln * 0.5 + sa * i), 1, 1))
                # mata panah + bulu
                hx, hy = self.x + ca * 3, self.y + sa * 3
                P._poly(surface, (*P.C_ARROW_HEAD, 235),
                        [(hx + ca * 4, hy + sa * 4),
                         (hx - sa * 2, hy + ca * 2),
                         (hx + sa * 2, hy - ca * 2)])
                bx, by = self.x - ca * 5, self.y - sa * 5
                P._poly(surface, (*P.C_ARROW_FEATHER, 220),
                        [(bx, by), (bx - ca * 3 - sa * 2, by - sa * 3 + ca * 2),
                         (bx - ca * 2, by - sa * 2)])
                P._poly(surface, (*P.C_LEAF_GOLD, 200),
                        [(bx, by), (bx - ca * 3 + sa * 2, by - sa * 3 - ca * 2),
                         (bx - ca * 2, by - sa * 2)])
                P._spark_star(surface, hx, hy, 4, P.C_WIND_WHITE, 170, 4,
                              rot=phase)

        class ShackleBolt(WindBolt):
            """Panah E: sulur membelit di sepanjang lintasan."""

            def __init__(self, sx, sy, tx, ty, speed=7.5, target=None,
                         damage=0, team=None, **kw):
                kw["powered"] = False
                super().__init__(sx, sy, tx, ty, speed=speed,
                                 target=target, damage=0, team=team, **kw)

            def draw(self, surface, phase):
                P = SylaraV1Renderer
                if not self.alive:
                    t = max(0.0, 1.0 - self.dead_frames / 9.0)
                    if t > 0:
                        P._dashed_ring(surface, self.x, self.y, 10 * t + 3,
                                       P.C_CLOTH_LIGHT, int(150 * t), phase,
                                       dashes=8, width=2, squash=0.9)
                    return
                SylaraV1Renderer.WindBolt.draw(self, surface, phase)
                ca, sa = math.cos(self.angle), math.sin(self.angle)
                for i in range(4):
                    a = phase * 6 + i * math.tau / 4
                    px = self.x - ca * 4 + math.cos(a) * 3
                    py = self.y - sa * 4 + math.sin(a) * 3
                    P._draw_sylara_leaf(surface, px, py, 2.4, a, phase)

        @staticmethod
        def _manage_projectiles(boss, surface, phase):
            if getattr(boss, "_skip_renderer_projectiles", False):
                return
            items = getattr(boss, "_sy_projectiles", None)
            if items is None:
                boss._sy_projectiles = []
                items = boss._sy_projectiles
            for proj in items:
                proj.update()
                proj.draw(surface, phase)
            boss._sy_projectiles[:] = [p for p in items
                                       if p.alive or p.dead_frames < 9]

        @staticmethod
        def _spawn_basic_shot(boss, x, y, powered=False, kind="bolt"):
            """Panah angin VISUAL dari nock (damage=0, tanpa impact FX)."""
            if getattr(boss, "_skip_renderer_projectiles", False):
                return None
            items = getattr(boss, "_sy_projectiles", None)
            if items is None:
                items = []
                boss._sy_projectiles = items
            P = SylaraV1Renderer
            facing = getattr(boss, "direction", 1)
            progress = float(getattr(boss, "_sy_attack_progress", 0.0))
            sx, sy = P._bow_release_position(
                x, y, facing, float(getattr(boss, "pulse", 0.0)), progress)
            tx, ty = P._target_position(boss, x, y)
            cls = P.ShackleBolt if kind == "shackle" else P.WindBolt
            proj = cls(sx, sy, tx, ty,
                       speed=(11.0 if powered else 8.5),
                       powered=powered,
                       target=getattr(boss, "target", None),
                       team=getattr(boss, "team", None))
            proj.source, proj.cx, proj.cy = boss, x, y
            items.append(proj)
            return proj

        @staticmethod
        def _spawn_arrow(boss, x, y, powered=False):
            """Alias legacy: panah visual (bukan damage) dari busur."""
            return SylaraV1Renderer._spawn_basic_shot(
                boss, x, y, powered=powered, kind="bolt")

        @staticmethod
        def _spawn_shackle(boss, x, y):
            return SylaraV1Renderer._spawn_basic_shot(
                boss, x, y, powered=False, kind="shackle")

        @staticmethod
        def _spawn_focus_fire_volley(boss, x, y, count=5, spread=0.06):
            """Q — volley panah angin visual yang mengarah ke target."""
            if getattr(boss, "_skip_renderer_projectiles", False):
                return
            P = SylaraV1Renderer
            items = getattr(boss, "_sy_projectiles", None)
            if items is None:
                items = []
                boss._sy_projectiles = items
            facing = getattr(boss, "direction", 1)
            sx, sy = P._bow_grip_position(
                x, y, facing, float(getattr(boss, "pulse", 0.0)), "focus")
            tx, ty = P._target_position(boss, x, y)
            base = math.atan2(ty - sy, tx - sx)
            for i in range(int(count)):
                ang = base + (i - (count - 1) * 0.5) * spread
                ex = sx + math.cos(ang) * 360
                ey = sy + math.sin(ang) * 360
                proj = P.WindBolt(sx, sy, ex, ey, speed=11.0, powered=False,
                                  target=getattr(boss, "target", None),
                                  team=getattr(boss, "team", None))
                proj.source, proj.cx, proj.cy = boss, x, y
                items.append(proj)

        # ------------------------------------------------------------------
        # POSE MODES (kontrak legacy + proyektil canvas V1).
        # ------------------------------------------------------------------
        @staticmethod
        def _skill_flags(boss):
            active_skill = getattr(boss, "active_skill", None)
            return {
                "focus": active_skill == "q",
                "wind": active_skill == "w",
                "shackle": active_skill == "e",
                "powershot": active_skill == "r",
            }

        @staticmethod
        def _draw_sylara_idle(surface, boss, x, y):
            P = SylaraV1Renderer
            bob = int(math.sin(boss.pulse * 0.7) * 2)
            sf = P._skill_flags(boss)
            if not getattr(boss, "_portrait_hd", False):
                P._draw_shadow(surface, x, y + 56)
                P._draw_floating_wind(surface, x, y + 34, boss.pulse)
            P._draw_sylara_body(
                surface, x, y + bob, boss.direction, boss.pulse, "idle",
                detail=getattr(boss, "_portrait_hd", False), **sf)

        @staticmethod
        def _draw_sylara_walk(surface, boss, x, y):
            P = SylaraV1Renderer
            phase = boss.pulse * 2.0
            bob = int(abs(math.sin(phase * 1.2)) * 3)
            sway = int(math.sin(phase) * 2)
            sf = P._skill_flags(boss)
            if not getattr(boss, "_portrait_hd", False):
                P._draw_shadow(surface, x + sway, y + 56)
                P._draw_floating_wind(surface, x + sway, y + 34, phase,
                                      trail=True, facing=boss.direction)
            P._draw_sylara_body(
                surface, x + sway, y - bob, boss.direction, phase, "walk",
                detail=getattr(boss, "_portrait_hd", False), **sf)

        @staticmethod
        def _draw_sylara_attack(surface, boss, x, y):
            """Pose serangan: tembakan (attack) atau sapuan busur (swing)."""
            P = SylaraV1Renderer
            progress = max(0.0, min(1.0, float(
                getattr(boss, "_sy_attack_progress", 0.0))))
            portrait = bool(getattr(boss, "_portrait_hd", False))
            facing = getattr(boss, "direction", 1)
            active_skill = getattr(boss, "active_skill", None)
            powered = active_skill in ("q", "r")
            swing_mode = bool(getattr(boss, "_sy_swing_mode", False))
            action = "swing" if swing_mode else "attack"

            # RELEASE WINDOW — panah angin visual lahir dari nock di titik
            # rilis (ap 0.5-0.6).  Murni visual (damage=0, tanpa impact FX).
            # Saat lapisan hidup memegang unit ini, director menembakkan
            # panah 60 fps-nya sendiri untuk serangan dasar -> canvas tidak
            # boleh dobel; skill tetap melepas panahnya sendiri.
            if (0.5 < progress < 0.6 and not swing_mode
                    and not getattr(boss, "_sy_shot_spawned", False)
                    and not portrait
                    and (active_skill is not None or not P._FX_LIVE.v)):
                P._spawn_basic_shot(boss, x, y, powered=powered, kind="bolt")
                boss._sy_shot_spawned = True
            if progress < 0.15 or progress > 0.9:
                boss._sy_shot_spawned = False

            if not portrait:
                P._draw_shadow(surface, x, y + 56)
                P._draw_floating_wind(surface, x, y + 34, boss.pulse,
                                      intense=True, facing=facing)
            sf = P._skill_flags(boss)
            P._draw_sylara_body(
                surface, x, y, facing, boss.pulse, action, progress,
                powered=powered, detail=portrait, **sf)

            if portrait:
                return
            lo, hi = P.SWING_WINDOW
            if swing_mode and lo < progress < hi:
                # Trail sapuan versi CANVAS hanya kalau lapisan hidup tidak
                # mengambil alih (kalau aktif, pita 60 fps-nya yang jalan).
                if not P._FX_LIVE.v:
                    def _pt(dx, dy):
                        return (int(x + dx * facing), int(y + dy))
                    P._draw_bow_swing_trail(surface, _pt, boss.pulse,
                                            progress)
            elif not swing_mode:
                P._draw_bow_release_flash(surface, x, y, facing, progress)

        @staticmethod
        def _draw_sylara_windrun(surface, boss, x, y, timer):
            P = SylaraV1Renderer
            phase = boss.pulse * 3.0
            bob = int(abs(math.sin(phase * 2)) * 2)
            sf = P._skill_flags(boss)
            if not getattr(boss, "_portrait_hd", False):
                P._draw_shadow(surface, x, y + 56)
                P._draw_windrun_trail(surface, x, y, boss.direction, phase)
            P._draw_sylara_body(
                surface, x, y - bob, boss.direction, phase, "windrun",
                detail=getattr(boss, "_portrait_hd", False), **sf)

        @staticmethod
        def _draw_sylara_hurt(surface, boss, x, y):
            P = SylaraV1Renderer
            P._draw_sylara_body(
                surface, x, y, getattr(boss, "direction", 1),
                float(getattr(boss, "pulse", 0.0)), "hurt",
                detail=bool(getattr(boss, "_portrait_hd", False)))

        # ------------------------------------------------------------------
        # DRAW ORCHESTRATOR.
        # ------------------------------------------------------------------
        @staticmethod
        def draw_sylara(surface, boss, x, y):
            """Entry point jalur hero DAN boss (urutan lapisan legacy).

            GROUND FX -> SHADOW -> BODY -> WEAPON -> PROJECTILE ->
            FRONT ACCENTS -> LIVE LAYER -> DEBUG.

            Kontrak "FX skill tidak menutupi badan": SEMUA massa besar
            (cakram isi, cincin mengembang, halo rumput) digambar di
            lapisan TANAH **sebelum** badan; lapisan depan hanya aksen
            ringan (spark di tepi, streak di sisi tubuh, flash kecil di
            senjata).
            """
            P = SylaraV1Renderer
            pulse = float(getattr(boss, "pulse", 0.0))
            active_skill = getattr(boss, "active_skill", None)
            skill_timer = int(getattr(boss, "active_skill_timer", 0) or 0)
            moving = P._detect_moving(boss)
            P._update_attack_anim(boss)
            portrait = bool(getattr(boss, "_portrait_hd", False))
            hero_lane = hasattr(boss, "_render_scale")

            if not portrait:
                try:
                    mod = P._live_module()
                    if mod is not None:
                        if hero_lane:
                            mod.attach(boss)
                        else:
                            mod.draw_ground_layer(surface, boss, x, y)
                except Exception:
                    pass
            try:
                P._FX_LIVE.v = (not portrait) and P._fx_live_owned(boss)
            except Exception:
                P._FX_LIVE.v = False

            attacking = (
                bool(getattr(boss, "_sy_attack_active", False))
                or getattr(boss, "timer", 0)
                > getattr(boss, "attack_cooldown", 45) - 15
            )
            alive = bool(getattr(boss, "alive", True))
            hurt = int(getattr(boss, "_sy_hurt_frames", 0) or 0) > 0
            if alive and int(getattr(boss, "_sy_death_frame", 0) or 0):
                # pose roboh di-reset begitu unit hidup lagi (respawn)
                boss._sy_death_frame = 0
            windrun = active_skill == "w" or bool(
                getattr(boss, "_windrun_active", False))

            # ---------- LAPISAN TANAH (massa besar, sebelum badan) ----------
            if not portrait:
                P._draw_ranger_silhouette_glow(surface, x, y - 8, pulse)
                P._draw_wind_aura(surface, x, y, pulse)
                P._draw_wind_platform(surface, x, y + 54, pulse,
                                      active_skill)
                if active_skill == "q":
                    P._draw_focus_fire_ground(surface, boss, x, y,
                                              skill_timer, pulse)
                elif active_skill == "w":
                    P._draw_windrun_ground(surface, boss, x, y,
                                           skill_timer, pulse)
                elif active_skill == "e":
                    P._draw_shackle_ground(surface, boss, x, y,
                                           skill_timer, pulse)
                elif active_skill == "r":
                    P._draw_powershot_ground(surface, boss, x, y,
                                             skill_timer, pulse)
                if active_skill in ("q", "w", "e", "r"):
                    age = (P.SKILL_VISUAL_DURATION.get(active_skill, 60)
                           - skill_timer)
                    if 0 <= age < 10:
                        P._skill_leaf_burst(surface, x, y + 30,
                                            age / 10.0, P._fx_scale(boss))

            # ---------- BADAN ----------
            if not alive:
                df = min(3, int(getattr(boss, "_sy_death_frame", 0) or 0))
                P._draw_sylara_body(surface, x, y,
                                    getattr(boss, "direction", 1), pulse,
                                    "death", detail=portrait,
                                    death_frame=df)
                boss._sy_death_frame = min(3, df + 1)
            elif windrun:
                P._draw_sylara_windrun(surface, boss, x, y, skill_timer)
            elif active_skill == "q":
                P._draw_sylara_body(surface, x, y,
                                    getattr(boss, "direction", 1), pulse,
                                    "focus", detail=portrait, focus=True)
            elif active_skill == "e":
                P._draw_sylara_body(surface, x, y,
                                    getattr(boss, "direction", 1), pulse,
                                    "shackle", detail=portrait, shackle=True)
            elif active_skill == "r":
                P._draw_sylara_body(surface, x, y,
                                    getattr(boss, "direction", 1), pulse,
                                    "powershot", detail=portrait,
                                    powershot=True)
            elif attacking:
                P._draw_sylara_attack(surface, boss, x, y)
            elif hurt:
                P._draw_sylara_hurt(surface, boss, x, y)
            elif moving:
                P._draw_sylara_walk(surface, boss, x, y)
            else:
                P._draw_sylara_idle(surface, boss, x, y)

            # ---------- LAPISAN DEPAN (aksen ringan saja) ----------
            if not portrait:
                P._manage_projectiles(boss, surface, pulse)
                if active_skill == "q":
                    P._draw_focus_fire_effect(surface, boss, x, y,
                                              skill_timer, pulse)
                elif active_skill == "w":
                    P._draw_windrun_effect(surface, boss, x, y,
                                           skill_timer, pulse)
                elif active_skill == "e":
                    P._draw_shackle_effect(surface, boss, x, y,
                                           skill_timer, pulse)
                elif active_skill == "r":
                    P._draw_powershot_charge(surface, boss, x, y,
                                             skill_timer, pulse)
                if not hero_lane:
                    try:
                        mod = P._live_module()
                        if mod is not None:
                            mod.draw_live_layer(surface, boss, x, y)
                    except Exception:
                        pass

            if P.DEBUG_CHARACTER:
                P._draw_debug(surface, boss, x, y, None)

        @staticmethod
        def draw_boss(surface, boss, x, y):
            SylaraV1Renderer.draw_sylara(surface, boss, x, y)

        @staticmethod
        def _draw_debug(surface, boss, x, y, state=None):
            P = SylaraV1Renderer
            pygame.draw.rect(surface, (170, 235, 135),
                             pygame.Rect(int(x - 40), int(y - 80),
                                         80, 140), 1)
            prog = float(getattr(boss, "_sy_attack_progress", 0.0))
            pygame.draw.rect(surface, P.C_OUTLINE,
                             pygame.Rect(int(x - 34), int(y - 92), 68, 5))
            pygame.draw.rect(surface, P.C_WIND_MID,
                             pygame.Rect(int(x - 34), int(y - 92),
                                         int(68 * prog), 5))
            facing = getattr(boss, "direction", 1)
            gx, gy = P._bow_grip_position(
                int(x), int(y), facing, float(getattr(boss, "pulse", 0.0)),
                "idle")
            pygame.draw.circle(surface, (120, 255, 150), (gx, gy), 3)
            # busur nyata (hasil _bow_geometry) sebagai penanda geometri FX
            geo = P._bow_geometry(float(getattr(boss, "pulse", 0.0)), "idle")
            f = 1 if facing >= 0 else -1
            for key, col in (("tip_up", (255, 214, 140)),
                             ("nock", (255, 120, 120))):
                px, py = geo[key]
                pygame.draw.circle(surface, col,
                                   (int(x + px * f), int(y + py)), 2)

        # ------------------------------------------------------------------
        # LIVE FX HOOKS (dipakai heroes/__init__.py & heroes/sylara_fx.py).
        # ------------------------------------------------------------------
        @staticmethod
        def _live_module():
            if SylaraV1Renderer._LIVE_MOD is None:
                try:
                    from heroes import sylara_fx as mod
                    SylaraV1Renderer._LIVE_MOD = (
                        mod if getattr(mod, "SYLARA_FX_ENABLED", True)
                        else False)
                except Exception:
                    SylaraV1Renderer._LIVE_MOD = False
            return SylaraV1Renderer._LIVE_MOD or None

        @staticmethod
        def _fx_live_owned(hero):
            try:
                mod = SylaraV1Renderer._live_module()
                return bool(mod is not None and mod.owns(hero))
            except Exception:
                return False

        @staticmethod
        def live_fx_ready():
            return SylaraV1Renderer._live_module() is not None

    return SylaraV1Renderer
