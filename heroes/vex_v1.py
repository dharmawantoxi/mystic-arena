"""Vex V1 pixel-art renderer adapted from the Kaizen V1 renderer pattern.

The game is pygame based, so this module keeps the existing renderer contract
(``draw_vex(surface, hero, x, y)``) and translates Vex's look into the chunky
chibi pixel-art style established by ``heroes/kaizen_v1.py``: a native 48x48
source grid drawn at 2.6x and normalized by the hero cache pipeline before it
reaches the arena.  Gameplay, touch controls, world generation and damage
remain owned by Mystic Arena; this module only owns Vex's visual pose and its
canvas fallback effects.

Vex stays Vex: a hooded void-mage (Outworld-Destroyer-inspired) with a
shadow face, glowing teal eyes, obsidian crown horns, a torn floating robe,
and his signature staff with the big faceted arcane orb.  Only the drawing
language changes - from the old masterwork bone-rig to small integer pixel
rectangles like Kaizen V1.

The implementation deliberately has no image assets.  Every shape is built
with pygame.draw + pygame.Surface + pygame.transform.
"""

import math

import pygame



def install(legacy_cls):
    """Return a V1 renderer subclass while retaining legacy API compatibility.

    ``heroes._bundle`` historically contains all hero namespaces in one file.
    Subclassing the old namespace lets older tools and the live FX layer keep
    importing their helper names while the actual Vex render path is fully
    replaced by the V1 pixel-art implementation below.
    """

    class VexV1Renderer(legacy_cls):
        """VEX V1.0 — Harbinger of the Void (pixel-art adaptation)."""

        # ------------------------------------------------------------------
        # Palette: direct translation of the masterwork void-mage ramp into
        # flat pixel-art swatches (same language as Kaizen V1).
        # ------------------------------------------------------------------
        C_OUTLINE = (8, 11, 20)
        C_ROBE_DARK = (16, 11, 34)
        C_ROBE_MID = (34, 25, 64)
        C_ROBE_LIGHT = (58, 44, 100)
        C_ROBE_HI = (92, 72, 148)
        C_ARMOR_DARK = (13, 15, 28)
        C_ARMOR_MID = (34, 40, 62)
        C_ARMOR_HI = (78, 90, 128)
        C_ARMOR_SHINE = (130, 146, 186)
        C_FACE = (12, 10, 24)
        C_HOOD_DARK = (12, 9, 28)
        C_HOOD_MID = (26, 19, 52)
        C_HOOD_HI = (48, 36, 88)
        C_CROWN = (10, 12, 24)
        C_CROWN_HI = (30, 34, 56)
        C_STAFF_DARK = (15, 20, 30)
        C_STAFF_MID = (42, 48, 64)
        C_STAFF_HI = (100, 114, 140)
        C_VOID_DARK = (14, 74, 78)
        C_VOID_MID = (36, 152, 158)
        C_VOID_LIGHT = (95, 222, 214)
        C_VOID_HI = (160, 246, 236)
        C_VOID_CORE = (234, 255, 250)
        C_AST_DARK = (48, 18, 92)
        C_AST_MID = (112, 50, 186)
        C_AST_LIGHT = (176, 108, 236)
        C_AST_HI = (226, 188, 252)
        C_GREEN = (60, 235, 150)
        C_EYE = C_VOID_LIGHT
        C_EYE_HI = C_VOID_CORE

        # The renderer namespace is also consumed by heroes/vex_fx.py.
        # Keep its historic keys as aliases so the live layer remains binary
        # compatible while following the flat void-mage pixel palette.
        PALETTE = dict(getattr(legacy_cls, "PALETTE", {}) or {}, **{
            "outline": C_OUTLINE,
            "skin_darkest": (25, 30, 45),
            "skin_dark": C_FACE,
            "skin_mid": (34, 30, 52),
            "skin_light": (70, 62, 96),
            "robe_darkest": C_ROBE_DARK,
            "robe_dark": C_ROBE_DARK,
            "robe_mid": C_ROBE_MID,
            "robe_light": C_ROBE_LIGHT,
            "robe_high": C_ROBE_HI,
            "armor_darkest": C_OUTLINE,
            "armor_dark": C_ARMOR_DARK,
            "armor_mid": C_ARMOR_MID,
            "armor_light": C_ARMOR_HI,
            "armor_shine": C_ARMOR_SHINE,
            "armor_rim": C_ARMOR_SHINE,
            "void_darkest": (8, 40, 50),
            "void_dark": C_VOID_DARK,
            "void_mid": C_VOID_MID,
            "void_light": C_VOID_LIGHT,
            "void_bright": C_VOID_HI,
            "void_hot": C_VOID_CORE,
            "void_white": C_VOID_CORE,
            "void_edge": (120, 255, 236),
            "void_green": C_GREEN,
            "void_gold": (232, 210, 118),
            "void_gold_hot": (255, 240, 196),
            "void_magma": (236, 72, 80),
            "face_dark": C_FACE,
            "crown_tip": C_VOID_CORE,
            "crown_rim": C_VOID_LIGHT,
            "orb_satellite": C_VOID_HI,
            "rune_trace": (140, 235, 230),
            "robe_weave": (50, 38, 84),
            "robe_dither": (30, 22, 52),
            "astral_darkest": (25, 8, 50),
            "astral_dark": C_AST_DARK,
            "astral_mid": C_AST_MID,
            "astral_light": C_AST_LIGHT,
            "astral_bright": C_AST_HI,
            "astral_hot": (240, 220, 255),
            "eye_glow": C_EYE,
            "eye_bright": C_EYE_HI,
            "staff_dark": C_STAFF_DARK,
            "staff_mid": C_STAFF_MID,
            "staff_light": C_STAFF_HI,
            "staff_shine": (140, 156, 184),
            "rune_dark": (30, 75, 85),
            "rune_mid": C_VOID_DARK,
            "rune_light": C_VOID_LIGHT,
            "shadow": (0, 0, 0),
            "shadow_deep": C_OUTLINE,
            "white": (255, 255, 255),
        })

        # Native coordinates on the V1 48x48 pixel grid.  The existing
        # pipeline later normalizes this larger rig to arena size.
        PIXEL_SCALE = 2.6
        PIXEL_ORIGIN = 24.0
        # Staff geometry is shared by the cached body, the live swing trail
        # (vex_fx.staff_points) and the fallback projectile spawn.  Local
        # helpers below already return canvas pixels, so the historic
        # RIG_SCALE multiplier must become neutral (1.0) instead of the old
        # masterwork 1.52 - otherwise the live trail would detach from the
        # drawn orb.
        RIG_SCALE = 1.0
        HAND_SRC = (31.0, 24.0)       # staff hand on the source grid
        ORB_REST_SRC = (33.0, 9.0)    # idle orb position
        STAFF_BUTT_LEN = 9.0          # source px of shaft below the hand

        # Durations stay synced with the legacy rig and vex_fx.py.
        SKILL_VISUAL_DURATION = {"q": 30, "w": 66, "e": 39, "r": 52}
        ATTACK_WINDUP_END = 0.28
        ATTACK_IMPACT = 0.56
        ATTACK_IMPACT_POINT = ATTACK_IMPACT
        ATTACK_SWING_END = 0.66

        ANIM_STATES = {
            "IDLE": 0, "WALK": 10, "ORBCAST": 20, "ECLIPSE": 30,
            "ASTRAL": 35, "FLUX": 40, "ATTACK": 50,
            "HURT": 70, "DEATH": 100,
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
        # Low-level procedural helpers and compatibility API.
        # ------------------------------------------------------------------
        @staticmethod
        def _clamp(color):
            vals = tuple(int(max(0, min(255, c))) for c in color)
            return vals if len(vals) in (3, 4) else vals[:3]

        @staticmethod
        def _rgba(color, alpha=255):
            c = VexV1Renderer._clamp(color)
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
            surf = VexV1Renderer._STATIC_SURFACES.get(key)
            if surf is None:
                if len(VexV1Renderer._STATIC_SURFACES) > 96:
                    VexV1Renderer._STATIC_SURFACES.clear()
                surf = builder()
                VexV1Renderer._STATIC_SURFACES[key] = surf
            return surf

        @staticmethod
        def _scratch(w, h):
            key = (max(1, int(w)), max(1, int(h)))
            pool = VexV1Renderer._SCRATCH_POOL
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
                pygame.draw.rect(surface, color, rect, border_radius=border_radius)
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
                VexV1Renderer._aaline(
                    surface, (*color, int(alpha)),
                    (int(cx - dx), int(cy - dy)),
                    (int(cx + dx), int(cy + dy)), 1)
            c = int(max(1, size * 0.28))
            VexV1Renderer._rect(surface, (*color, int(alpha)),
                                (int(cx) - c, int(cy) - c, c * 2, c * 2))

        @staticmethod
        def _chevron(surface, cx, cy, ang, size, color, alpha, width=2):
            back = ang + 2.55
            x1 = cx + math.cos(back) * size
            y1 = cy + math.sin(back) * size * 0.6
            x2 = cx + math.cos(ang - 2.55) * size
            y2 = cy + math.sin(ang - 2.55) * size * 0.6
            VexV1Renderer._aaline(surface, (*color, int(alpha)),
                                  (x1, y1), (cx, cy), width)
            VexV1Renderer._aaline(surface, (*color, int(alpha)),
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
                VexV1Renderer._aaline(surface, (*color, int(alpha)),
                                      p0, p1, width)

        @staticmethod
        def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                          width=2, segments=5):
            px, py = cx, cy
            for i in range(int(segments)):
                t = (i + 1) / float(segments)
                wiggle = (VexV1Renderer._hash01(seed + i * 7) - 0.5) * 10.0
                nx = cx + math.cos(ang) * length * t - math.sin(ang) * wiggle
                ny = cy + math.sin(ang) * length * t * 0.5 + math.cos(ang) * wiggle * 0.5
                col = colors[min(len(colors) - 1, i * len(colors) // segments)]
                VexV1Renderer._aaline(surface, (*col, int(alpha)),
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
                ln = min_len + VexV1Renderer._hash01(seed + i) * depth
                pts.append((bx, by + ln))
                pts.append((bx + (x1 - x0) / float(count + 1) * 0.5, by))
            pts.append((x1, y1))
            return pts

        @staticmethod
        def _aoe_marks(surface, cx, cy, radius, color, alpha, phase=0.0,
                       squash=1.0, ticks=16, tick_len=8):
            radius = max(8, int(radius))
            VexV1Renderer._dashed_ring(
                surface, cx, cy, radius, color, alpha, phase * 0.5,
                dashes=max(8, ticks // 2), width=2, squash=squash)
            for i in range(ticks):
                a = phase * 0.35 + i * math.tau / ticks
                x0 = cx + math.cos(a) * (radius - tick_len)
                y0 = cy + math.sin(a) * (radius - tick_len) * squash
                x1 = cx + math.cos(a) * radius
                y1 = cy + math.sin(a) * radius * squash
                VexV1Renderer._aaline(surface, (*color, int(alpha)),
                                      (x0, y0), (x1, y1), 2)

        @staticmethod
        def _crystal(surface, cx, cy, ang, length, width, ramp, alpha,
                     outline=True):
            """Small faceted crystal shard (poligon tetap pixel-friendly)."""
            ca, sa = math.cos(ang), math.sin(ang)

            def P(dx, dy):
                return (cx + dx * ca - dy * sa, cy + dx * sa + dy * ca)

            dark, mid, light = ramp
            tip = P(0, -length)
            left = P(-width, 0)
            right = P(width, 0)
            base_l = P(-width * 0.6, 3)
            base_r = P(width * 0.6, 3)
            if outline:
                VexV1Renderer._poly(
                    surface, (*VexV1Renderer.C_OUTLINE, int(alpha)),
                    [P(0, -length - 1), P(-width - 1, 0), P(-width * 0.6 - 1, 3),
                     P(width * 0.6 + 1, 3), P(width + 1, 0)])
            VexV1Renderer._poly(surface, (*mid, int(alpha)),
                                [tip, left, base_l, base_r, right])
            VexV1Renderer._poly(surface, (*dark, int(alpha)),
                                [tip, left, base_l])
            VexV1Renderer._poly(surface, (*light, int(alpha)),
                                [P(0, -length + 2), P(-width * 0.4, 1),
                                 P(width * 0.18, 1)])

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
        def _skill_progress(boss, skill, timer):
            duration = float(VexV1Renderer.SKILL_VISUAL_DURATION.get(
                skill, max(1, timer or 1)))
            return max(0.0, min(1.0, 1.0 - float(timer) / max(1.0, duration)))

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
                return VexV1Renderer._world_to_local(
                    boss, x, y, target.x, target.y)
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            return int(x + 150 * scale * getattr(boss, "direction", 1)), int(y)

        @staticmethod
        def _pixel_local(x, y):
            s = VexV1Renderer.PIXEL_SCALE
            return ((float(x) - VexV1Renderer.PIXEL_ORIGIN) * s,
                    (float(y) - VexV1Renderer.PIXEL_ORIGIN) * s)

        @staticmethod
        def _tint(color, tint):
            c = VexV1Renderer._clamp(color)
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
            s = VexV1Renderer.PIXEL_SCALE
            sx = -1.0 if facing < 0 else 1.0

            def rect_for(x, y, w, h, ox=0, oy=0, extra_crouch=0):
                rx = cx + ((x + body_x + ox - VexV1Renderer.PIXEL_ORIGIN) * s * sx)
                if facing < 0:
                    rx -= w * s
                ry = cy + ((y + body_y + crouch + extra_crouch -
                            VexV1Renderer.PIXEL_ORIGIN) * s)
                return pygame.Rect(int(round(rx)), int(round(ry)),
                                   max(1, int(round(w * s))),
                                   max(1, int(round(h * s))))

            def R(x, y, w, h, col, alpha=None):
                color = VexV1Renderer._tint(col, tint)
                if alpha is not None:
                    color = color[:3] + (int(color[3] * alpha / 255.0),)
                pygame.draw.rect(surface, color, rect_for(x, y, w, h))

            def RO(x, y, w, h, col, alpha=None):
                # One source-pixel selout keeps the sprite readable after
                # smoothscale, mirroring Kaizen V1 exactly.
                R(x - 1, y - 1, w + 2, h + 2, (6, 8, 18), alpha)
                R(x, y, w, h, col, alpha)

            def point(x, y, ox=0, oy=0):
                return (cx + ((x + body_x + ox - VexV1Renderer.PIXEL_ORIGIN) * s * sx),
                        cy + ((y + body_y + crouch + oy - VexV1Renderer.PIXEL_ORIGIN) * s))

            def line(a, b, color, width=1, alpha=None):
                c = VexV1Renderer._tint(color, tint)
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
            if not hasattr(boss, "_vx_last_x"):
                boss._vx_last_x = float(getattr(boss, "x", 0.0))
                boss._vx_last_y = float(getattr(boss, "y", 0.0))
                boss._moving_cached = False
                return False
            dx = abs(float(getattr(boss, "x", 0.0)) - boss._vx_last_x)
            dy = abs(float(getattr(boss, "y", 0.0)) - boss._vx_last_y)
            boss._vx_last_x = float(getattr(boss, "x", 0.0))
            boss._vx_last_y = float(getattr(boss, "y", 0.0))
            moving = dx + dy > .3
            boss._moving_cached = moving
            return moving

        @staticmethod
        def _update_attack_anim(boss):
            """Track the attack timeline (identik dengan rig legacy)."""
            cooldown = max(2, int(getattr(boss, "attack_cooldown", 50) or 50))
            timer = int(getattr(boss, "timer", getattr(boss, "attack_timer", 0)) or 0)
            previous = int(getattr(boss, "_vx_prev_timer", -1))
            active = bool(getattr(boss, "_vx_attack_active", False))
            # A new attack is the only upward edge of the countdown timer.
            if timer > 0 and (previous <= 0 or timer > previous):
                active = True
                boss._vx_proj_spawned = False
            if active and timer <= 0:
                active = False
            boss._vx_prev_timer = timer
            boss._vx_attack_active = active
            frame = max(0, cooldown - timer) if active else 0
            boss._vx_attack_frame = frame
            boss._vx_attack_progress = min(1.0, frame / max(1, cooldown - 1)) if active else 0.0

        @staticmethod
        def _orb_src(action, phase, ap):
            """Posisi orb staff pada grid sumber 48x48.

            Keyframe serangan mengikuti timeline legacy: wind-up menarik
            orb ke belakang/atas, release mendorong ke depan, IMPACT di
            0.56, lalu recovery.  Idle/walk mengambang halus.
            """
            wave = math.sin(float(phase) * 1.3) * 0.8
            if action == "attack":
                keys = (
                    (0.00, (33.0,  9.0)),
                    (0.18, (26.0,  2.5)),
                    (0.32, (23.0,  1.5)),
                    (0.48, (34.0, 13.0)),
                    (0.56, (38.5, 21.0)),
                    (0.76, (35.0, 12.0)),
                    (1.00, (33.0,  9.0)),
                )
                ap = max(0.0, min(1.0, float(ap)))
                for i in range(len(keys) - 1):
                    a, b = keys[i], keys[i + 1]
                    if a[0] <= ap <= b[0]:
                        t = (ap - a[0]) / max(1e-6, b[0] - a[0])
                        t = t * t * (3.0 - 2.0 * t)
                        return (a[1][0] + (b[1][0] - a[1][0]) * t,
                                a[1][1] + (b[1][1] - a[1][1]) * t)
                return keys[-1][1]
            if action == "walk":
                return (33.0 + math.sin(float(phase) * 1.72) * 1.2,
                        9.0 + wave)
            return (VexV1Renderer.ORB_REST_SRC[0],
                    VexV1Renderer.ORB_REST_SRC[1] + wave)

        # ------------------------------------------------------------------
        # Geometry bridge consumed by heroes/vex_fx.py (live trail orb).
        # Local helpers return CANVAS pixels directly; RIG_SCALE = 1.0 keeps
        # the historic multiplication in staff_points() neutral.
        # ------------------------------------------------------------------
        @staticmethod
        def _orb_tip_local(phase, action="idle", attack_progress=0.0):
            ox, oy = VexV1Renderer._orb_src(action, phase, attack_progress)
            return VexV1Renderer._pixel_local(ox, oy)

        @staticmethod
        def _staff_grip_local(phase, action="idle", attack_progress=0.0):
            return VexV1Renderer._pixel_local(*VexV1Renderer.HAND_SRC)

        @staticmethod
        def _staff_butt_local(phase, action="idle", attack_progress=0.0):
            P = VexV1Renderer
            ox, oy = P._orb_src(action, phase, attack_progress)
            hx, hy = P.HAND_SRC
            dx, dy = ox - hx, oy - hy
            ln = max(1e-6, math.hypot(dx, dy))
            bx = hx - dx / ln * P.STAFF_BUTT_LEN
            by = hy - dy / ln * P.STAFF_BUTT_LEN
            return P._pixel_local(bx, by)

        @staticmethod
        def _staff_orb_position(cx, cy, facing, phase=0.0, action="idle",
                                attack_progress=0.0):
            """Posisi orb (canvas) untuk efek skill / spawn proyektil."""
            tx, ty = VexV1Renderer._orb_tip_local(phase, action,
                                                  attack_progress)
            f = 1 if facing >= 0 else -1
            return int(cx + tx * f), int(cy + ty)

        @staticmethod
        def _attack_pose(ap):
            """Keyframe serangan V1: lean badan + flare orb + tremble."""
            keys = (
                (0.00,   0, 0, 1.00, 0),
                (0.18,  -2, -4, 1.10, 0),
                (0.32,  -4, -6, 1.22, 1),
                (0.48,   0,  6, 1.14, 0),
                (0.56,   3, 10, 1.38, 0),
                (0.76,   1,  4, 1.08, 0),
                (1.00,   0,  0, 1.00, 0),
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

        # ------------------------------------------------------------------
        # The actual V1 sprite layers (bahasa Kaizen V1, identitas Vex).
        # ------------------------------------------------------------------
        @staticmethod
        def _draw_pixel_cape(R, RO, wave_amt, anim_name, cape_wave):
            """Torn back-cape strips floating behind the hood."""
            P = VexV1Renderer
            w1 = math.sin(cape_wave) * wave_amt
            w2 = math.sin(cape_wave + 1.2) * wave_amt
            w3 = math.sin(cape_wave + 2.4) * wave_amt
            if anim_name == "orbcast":
                for x, y in ((11, 20), (7, 22), (3, 24), (-1, 26 + int(w1))):
                    RO(x, y, 4, 3, P.C_ROBE_DARK)
                R(0, 26 + int(w1), 3, 1, P.C_VOID_MID)
            else:
                RO(13, 18, 4, 7, P.C_ROBE_DARK)
                RO(11 + int(w1), 24, 4, 7, P.C_ROBE_DARK)
                RO(9 + int(w2), 30, 3, 6, P.C_ROBE_DARK)
                RO(11 + int(w3), 35, 3, 4, P.C_ROBE_MID)
                R(12 + int(w1), 27, 1, 5, P.C_ROBE_HI)
                R(10 + int(w2), 33, 1, 3, P.C_VOID_MID)

        @staticmethod
        def _draw_pixel_hem(R, RO, hem_pose, anim_name):
            """Tattered floating robe hem - Vex has no legs, he hovers."""
            P = VexV1Renderer
            if anim_name in ("idle", "attack", "orbcast", "eclipse",
                             "astral", "flux", "hurt"):
                RO(16, 36, 5, 6, P.C_ROBE_MID)
                RO(22, 36, 5, 8, P.C_ROBE_MID)
                RO(28, 36, 4, 5, P.C_ROBE_MID)
                R(17, 40, 3, 3, P.C_ROBE_DARK)
                R(23, 41, 3, 4, P.C_ROBE_DARK)
                R(29, 39, 2, 3, P.C_ROBE_DARK)
                # Hem rim light keeps the float readable over dark terrain.
                R(16, 41, 2, 1, P.C_VOID_MID)
                R(23, 44, 2, 1, P.C_VOID_MID)
            else:
                poses = (
                    ((16, 36, 5, 6), (22, 36, 5, 8), (28, 36, 4, 5)),
                    ((14, 36, 5, 5), (21, 36, 5, 8), (29, 36, 4, 6)),
                    ((18, 36, 5, 6), (23, 36, 4, 7), (27, 36, 4, 5)),
                    ((15, 36, 5, 7), (22, 36, 5, 6), (28, 36, 5, 7)),
                )
                pose = poses[int(hem_pose) % len(poses)]
                for box in pose:
                    RO(*box, P.C_ROBE_MID)
                    R(box[0] + 1, box[1] + box[3] - 2, max(1, box[2] - 2), 2,
                      P.C_ROBE_DARK)

        @staticmethod
        def _draw_pixel_hood(R, RO, head_y, anim_name):
            """Hood + shadow face + glowing eyes + obsidian crown horns."""
            P = VexV1Renderer
            # Crown flames behind the hood (three obsidian spikes, cyan tips).
            RO(16, 2 + head_y, 3, 5, P.C_CROWN)
            R(17, 1 + head_y, 2, 2, P.C_VOID_MID)
            RO(22, -1 + head_y, 4, 6, P.C_CROWN)
            R(23, -2 + head_y, 2, 3, P.C_CROWN_HI)
            R(23, -3 + head_y, 1, 2, P.C_VOID_LIGHT)
            RO(28, 2 + head_y, 3, 5, P.C_CROWN)
            R(29, 1 + head_y, 2, 2, P.C_VOID_MID)
            # Hood dome.
            RO(15, 4 + head_y, 18, 7, P.C_HOOD_MID)
            RO(14, 8 + head_y, 20, 9, P.C_HOOD_MID)
            R(16, 5 + head_y, 14, 5, P.C_HOOD_HI)
            R(17, 5 + head_y, 9, 3, P.C_ROBE_LIGHT)
            R(15, 8 + head_y, 2, 8, P.C_HOOD_DARK)
            R(31, 8 + head_y, 2, 8, P.C_HOOD_DARK)
            # Shadow face inside the hood.
            R(18, 10 + head_y, 12, 7, P.C_FACE)
            R(19, 15 + head_y, 10, 2, P.C_HOOD_DARK)
            if anim_name in ("hurt", "death"):
                # Eyes squeezed shut.
                R(20, 13 + head_y, 3, 1, P.C_VOID_DARK)
                R(25, 13 + head_y, 3, 1, P.C_VOID_DARK)
            else:
                # Two glowing teal eyes with a hot core pixel.
                R(20, 12 + head_y, 3, 3, P.C_EYE)
                R(25, 12 + head_y, 3, 3, P.C_EYE)
                R(21, 12 + head_y, 1, 1, P.C_EYE_HI)
                R(26, 12 + head_y, 1, 1, P.C_EYE_HI)

        @staticmethod
        def _draw_pixel_staff(surface, R, RO, point, line, orb_x, orb_y,
                              phase, flare=1.0, glow_color=None,
                              show_orbit=True):
            """Right-sleeve arm + staff shaft + the big faceted arcane orb."""
            P = VexV1Renderer
            hx, hy = P.HAND_SRC
            # Sleeve arm from shoulder to hand.
            RO(28, 21, 5, 5, P.C_ROBE_LIGHT)
            R(29, 22, 3, 3, P.C_ROBE_HI)
            RO(hx, hy, 4, 4, P.C_ARMOR_MID)
            R(hx + 1, hy + 1, 2, 2, P.C_ARMOR_HI)
            # Shaft: segmented pixel line (selout 3, mid 2, shine 1) like the
            # Kaizen blade - from butt below the hand to the orb seat.
            dx, dy = orb_x - hx, orb_y - hy
            ln = max(1e-6, math.hypot(dx, dy))
            ux, uy = dx / ln, dy / ln
            bx = hx - ux * P.STAFF_BUTT_LEN
            by = hy - uy * P.STAFF_BUTT_LEN
            seat_x = orb_x - ux * 3.0
            seat_y = orb_y - uy * 3.0
            segs = 10
            for i in range(segs):
                t0 = i / float(segs)
                t1 = (i + 1) / float(segs)
                a = (bx + (seat_x - bx) * t0, by + (seat_y - by) * t0)
                b = (bx + (seat_x - bx) * t1, by + (seat_y - by) * t1)
                line(a, b, P.C_OUTLINE, 3)
                line(a, b, P.C_STAFF_MID, 2)
                line(a, b, P.C_STAFF_HI, 1)
            # Butt cap + teal seat knob where the shaft meets the orb.
            RO(bx - 1, by - 1, 3, 3, P.C_STAFF_DARK)
            # Orb: the signature Vex arcane orb - soft canvas halo, faceted
            # diamond in nested rects, hot core, and an orbiting shard.
            glow = glow_color or P.C_VOID_MID
            flare = max(0.6, float(flare))
            cx0, cy0 = point(orb_x, orb_y)
            halo_r = max(6.0, (6.0 + 4.0 * flare) * P.PIXEL_SCALE * 0.55)
            pygame.draw.circle(surface, (*glow, 44),
                               (int(cx0), int(cy0)), int(halo_r))
            pygame.draw.circle(surface, (*P.C_VOID_LIGHT, 90),
                               (int(cx0), int(cy0)), int(halo_r * 0.62))
            r_out = max(3, int(round(4 * flare)))
            R(orb_x - 1, orb_y - r_out - 1, 2, 2, glow)
            R(orb_x - 1, orb_y + r_out - 1, 2, 2, glow)
            R(orb_x - r_out - 1, orb_y - 1, 2, 2, glow)
            R(orb_x + r_out - 1, orb_y - 1, 2, 2, glow)
            RO(orb_x - 3, orb_y - 3, 6, 6, P.C_VOID_DARK)
            R(orb_x - 2, orb_y - 2, 4, 4, P.C_VOID_LIGHT)
            R(orb_x - 1, orb_y - 1, 2, 2, P.C_VOID_CORE)
            R(orb_x - 2, orb_y - 2, 1, 1, P.C_VOID_CORE)
            # Tiny satellite shard orbiting the orb (signature Vex).
            if show_orbit:
                a = float(phase) * 1.9
                sx = orb_x + math.cos(a) * (r_out + 3)
                sy = orb_y + math.sin(a) * (r_out + 3) * 0.6
                R(sx, sy, 1, 1, P.C_VOID_HI)

        @staticmethod
        def _draw_vex_sprite(surface, origin, flip_left, anim_name,
                             frame_idx, tint=(255, 255, 255, 255),
                             attack_progress=0.0, cape_wave=0.0):
            P = VexV1Renderer
            body_y = body_x = head_y = 0
            hem_pose = 0
            crouch = 0
            dead = False
            flash = False
            cape_amt = 1.0
            flare = 1.0
            glow = None
            frame_idx = int(frame_idx)

            orb_action = "idle"
            if anim_name == "idle":
                body_y = 1 if frame_idx % 2 else 0
                head_y = body_y
                cape_amt = 1.6
            elif anim_name == "walk":
                body_y = -1 if frame_idx % 2 else 0
                head_y = body_y
                hem_pose = frame_idx % 4
                orb_action = "walk"
                cape_amt = 2.2
            elif anim_name == "attack":
                pose = P._attack_pose(attack_progress)
                body_y = pose["bob"]
                body_x = pose["lean"] * 0.6
                head_y = max(-1, min(2, pose["bob"] // 2))
                flare = pose["flare"]
                orb_action = "attack"
                cape_amt = 4.0
                if pose["tremble"]:
                    body_x += (1 if int(cape_wave * 31) % 2 else -1) * 0.5
            elif anim_name == "orbcast":
                body_x, body_y, cape_amt = 2, 1, 5.0
                flare = 1.45
                orb_action = "attack"  # reuse thrust keyframe at the end
            elif anim_name == "eclipse":
                crouch = 2
                head_y = 1
                cape_amt = 2.6
            elif anim_name == "astral":
                body_y = -2
                head_y = -1
                cape_amt = 3.2
                glow = P.C_AST_MID
                flare = 1.25
            elif anim_name == "flux":
                body_x, body_y, cape_amt = -2, -1, 4.5
                flare = 1.55
            elif anim_name == "hurt":
                flash = True
                body_x = -3 if not flip_left else 3
                head_y, body_y = -1, (1 if frame_idx == 1 else 0)
            elif anim_name == "death":
                if frame_idx == 0:
                    flash, head_y = True, -1
                elif frame_idx == 1:
                    crouch, head_y = 4, 2
                elif frame_idx == 2:
                    crouch, head_y = 8, 5
                else:
                    dead = True

            use_tint = (255, 96, 96, 255) if flash else tint
            R, RO, point, line = P._make_pixel_ops(
                surface, origin[0], origin[1], -1 if flip_left else 1,
                body_x, body_y, crouch, use_tint)

            if dead:
                # Collapsed robe, fallen staff, dimmed orb.
                RO(12, 41, 19, 5, P.C_ROBE_DARK)
                R(14, 42, 15, 3, P.C_ROBE_MID)
                RO(13, 38, 8, 5, P.C_HOOD_MID)
                R(15, 40, 4, 2, P.C_FACE)
                line((20, 44), (38, 40), P.C_OUTLINE, 3)
                line((20, 44), (38, 40), P.C_STAFF_MID, 2)
                R(38, 39, 3, 3, P.C_VOID_DARK)
                R(39, 40, 1, 1, P.C_VOID_MID)
                return

            # Back-to-front: cape -> robe -> hem -> chest -> hood -> staff.
            P._draw_pixel_cape(R, RO, cape_amt, anim_name, cape_wave)
            RO(16, 18, 16, 15, P.C_ROBE_MID)
            R(17, 19, 14, 12, P.C_ROBE_LIGHT)
            R(18, 20, 5, 9, P.C_ROBE_MID)
            R(25, 20, 5, 9, P.C_ROBE_MID)
            R(17, 19, 2, 3, P.C_ROBE_HI)
            R(29, 19, 2, 3, P.C_ROBE_HI)
            # Belt / sash with a void clasp.
            RO(16, 29, 16, 3, P.C_ARMOR_DARK)
            R(17, 30, 14, 1, P.C_ARMOR_HI)
            R(22, 29, 4, 3, P.C_VOID_MID)
            R(23, 30, 2, 1, P.C_VOID_CORE)
            # Small pauldron spikes.
            RO(13, 17, 4, 4, P.C_ARMOR_DARK)
            R(14, 16, 3, 3, P.C_ARMOR_MID)
            R(15, 15, 1, 1, P.C_ARMOR_SHINE)
            RO(30, 17, 4, 4, P.C_ARMOR_DARK)
            R(31, 16, 3, 3, P.C_ARMOR_MID)
            R(32, 15, 1, 1, P.C_ARMOR_SHINE)
            P._draw_pixel_hem(R, RO, hem_pose, anim_name)

            P._draw_pixel_hood(R, RO, head_y, anim_name)

            # Staff pose lookup (attack = continuous keyframe path).
            if orb_action == "attack" and anim_name == "attack":
                ox, oy = P._orb_src("attack", 0.0, attack_progress)
            elif anim_name == "orbcast":
                ox, oy = 38.0, 18.0
            elif anim_name == "eclipse":
                ox, oy = 35.0, 32.0
                glow = P.C_VOID_LIGHT
            elif anim_name == "astral":
                ox, oy = 31.0, 3.0
            elif anim_name == "flux":
                ox, oy = 30.0, 1.0
            elif orb_action == "walk":
                ox, oy = P._orb_src("walk", cape_wave, 0.0)
            else:
                ox, oy = P._orb_src("idle", cape_wave, 0.0)
            P._draw_pixel_staff(surface, R, RO, point, line, ox, oy,
                                cape_wave, flare=flare, glow_color=glow)

            if anim_name == "flux":
                cx0, cy0 = point(24, 30)
                for i in range(6):
                    a = cape_wave * 2.2 + i * math.tau / 6.0
                    rr = 19.0 + math.sin(cape_wave * 5.0) * 3.0
                    P._rect(surface, (*P.C_VOID_CORE, 190),
                            (cx0 + math.cos(a) * rr - 2,
                             cy0 + math.sin(a) * rr * .45 - 2, 4, 4))

        # ------------------------------------------------------------------
        # Elite body wrapper (kontrak lama) + highlight clusters.
        # ------------------------------------------------------------------
        @staticmethod
        def _draw_vex_elite(surface, cx, cy, facing, phase, action,
                            attack_progress=0.0, detail=False,
                            skill_state=None):
            """Render one V1 pixel-art frame.

            ``skill_state`` lets the legacy callers force a skill pose, but
            the normal action string already carries q/w/e/r poses.
            """
            P = VexV1Renderer
            anim = action
            if skill_state in ("q", "w", "e", "r") and action in (
                    "idle", "walk"):
                anim = {"q": "orbcast", "w": "eclipse",
                        "e": "astral", "r": "flux"}[skill_state]
            frame = 0
            if anim == "idle":
                frame = int(abs(math.sin(float(phase) * 4.0)) > .45)
            elif anim == "walk":
                frame = int(float(phase) * 6.0) % 6
            elif anim == "attack":
                frame = min(4, max(0, int(float(attack_progress) * 5.0)))
            else:
                counts = {"orbcast": 4, "eclipse": 3, "astral": 3,
                          "flux": 4, "hurt": 3, "death": 5}
                frame = int(float(phase) * 8.0) % counts.get(anim, 4)
            P._draw_vex_sprite(
                surface, (cx, cy), facing < 0, anim, frame,
                attack_progress=attack_progress, cape_wave=float(phase) * 1.7)
            f = -1 if facing < 0 else 1
            # Void rim clusters keep the purple ramp alive after downscale.
            P._rect(surface, (*P.C_ROBE_HI, 225),
                    (cx + f * 15, cy - 12, 2, 1))
            if anim == "attack":
                micro = int(max(0.0, min(0.999999,
                                         float(attack_progress))) * 9.0)
                P._rect(surface, (*P.C_VOID_CORE, 220),
                        (cx + f * (38 + micro), cy - 20 - (micro % 2), 2, 2))
            if detail and anim != "death":
                y = cy - 34
                P._rect(surface, (*P.C_VOID_LIGHT, 240),
                        (cx + f * 4 - 1, y, 2, 1))
                P._rect(surface, (*P.C_AST_LIGHT, 230),
                        (cx + f * 8, y + 4, 1, 1))
                P._rect(surface, (*P.C_ROBE_HI, 230),
                        (cx - f * 20, cy - 42, 2, 2))

        @staticmethod
        def _draw_vex_body(surface, cx, cy, facing, phase, action,
                           attack_progress=0.0, detail=False,
                           skill_state=None):
            VexV1Renderer._draw_vex_elite(
                surface, cx, cy, facing, phase, action, attack_progress,
                detail, skill_state)

        # ------------------------------------------------------------------
        # Ambient and skill effects (fallback canvas effects; the live
        # layer heroes/vex_fx.py owns the 60fps versions in the arena).
        # ------------------------------------------------------------------
        @staticmethod
        def _draw_shadow(surface, x, y):
            P = VexV1Renderer
            pygame.draw.ellipse(surface, (*P.C_OUTLINE, 110),
                                pygame.Rect(int(x - 44), int(y - 8), 88, 14))
            pygame.draw.ellipse(surface, (*P.C_VOID_MID, 40),
                                pygame.Rect(int(x - 30), int(y - 5), 60, 8))

        @staticmethod
        def _draw_mage_rim_light(surface, x, y, phase):
            P = VexV1Renderer
            alpha = int(30 + 22 * (.5 + .5 * math.sin(phase)))
            pygame.draw.ellipse(surface, (*P.C_VOID_MID, alpha),
                                pygame.Rect(int(x - 26), int(y - 46), 52, 88), 2)

        @staticmethod
        def _draw_void_silhouette_glow(surface, x, y, pulse):
            VexV1Renderer._draw_mage_rim_light(surface, x, y + 8, pulse)

        @staticmethod
        def _draw_void_aura(surface, x, y, phase):
            P = VexV1Renderer
            for i in range(3):
                r = 40 + i * 8 + int(math.sin(phase * 1.5 + i) * 3)
                P._dashed_ring(surface, x, y + 8, r, P.C_VOID_MID,
                               34 - i * 7, phase * .4 + i, dashes=10,
                               width=1, squash=.35)

        @staticmethod
        def _draw_flux_aura(surface, x, y, phase):
            P = VexV1Renderer
            P._draw_void_aura(surface, x, y, phase * 1.7)
            for i in range(6):
                a = phase * 1.8 + i * math.tau / 6
                P._spark_star(surface, x + math.cos(a) * 36,
                              y + 5 + math.sin(a) * 12, 5, P.C_VOID_CORE,
                              125, 4, rot=a)

        @staticmethod
        def _draw_void_platform(surface, x, y, phase, skill):
            P = VexV1Renderer
            P._dashed_ring(surface, x, y, 38, P.C_VOID_MID, 105, phase * .3,
                           dashes=14, width=2, squash=.27)
            P._dashed_ring(surface, x, y, 58, P.C_ROBE_HI, 58, -phase * .2,
                           dashes=10, width=1, squash=.2)
            for i in range(4):
                a = phase * .15 + i * math.pi / 2
                P._spark_star(surface, x + math.cos(a) * 48,
                              y + math.sin(a) * 13, 3, P.C_VOID_CORE, 170,
                              4, rot=a)

        @staticmethod
        def _draw_floating_void(surface, cx, cy, phase, trail=False,
                                facing=1, intense=False):
            P = VexV1Renderer
            count = 5 if intense else 3
            for i in range(count):
                t = (phase * (.45 if not intense else .75) + i * .23) % 1.0
                sx = cx - facing * (18 + i * 10) + math.sin(phase + i) * 4
                sy = cy + 9 - t * 28
                alpha = int(165 * (1.0 - t))
                P._aaline(surface, (*P.C_VOID_MID, alpha), (sx, sy),
                          (sx + facing * 6, sy - 4), 2)
                if i % 2 == 0:
                    P._spark_star(surface, sx, sy, 3, P.C_VOID_CORE,
                                  alpha, 4, rot=phase + i)
            if trail:
                for i in range(4):
                    P._aaline(surface, (*P.C_VOID_DARK, 100 - i * 20),
                              (cx - facing * (14 + i * 10), cy + i),
                              (cx - facing * (24 + i * 12), cy + i), 1)

        # ---------- Skill FX: Q Arcane Orb ----------
        @staticmethod
        def _draw_arcane_orb_telegraph(surface, boss, x, y, timer, phase):
            P = VexV1Renderer
            tx, ty = P._target_position(boss, x, y)
            P._dashed_ring(surface, tx, ty + 4, 22, P.C_VOID_MID, 150,
                           phase, dashes=10, width=2, squash=.35)

        @staticmethod
        def _draw_arcane_orb_charge(surface, boss, x, y, timer, phase):
            P = VexV1Renderer
            progress = P._skill_progress(boss, "q", timer)
            f = getattr(boss, "direction", 1)
            ox, oy = P._staff_orb_position(
                x, y, f, phase, "attack",
                getattr(boss, "_vx_attack_progress", 0.5) or 0.5)
            charge = min(1.0, progress * 2.2)
            P._aacircle(surface, (*P.C_VOID_LIGHT, int(120 * charge)),
                        (ox, oy), 8 + int(10 * charge))
            P._aacircle(surface, (*P.C_VOID_CORE, int(190 * charge)),
                        (ox, oy), 4 + int(5 * charge))
            for i in range(4):
                a = phase * 2.4 + i * math.pi / 2
                gx = ox + math.cos(a) * (16 - 8 * charge)
                gy = oy + math.sin(a) * (16 - 8 * charge) * .6
                P._spark_star(surface, gx, gy, 3, P.C_VOID_HI,
                              int(170 * charge), 4, rot=a)

        # ---------- Skill FX: W Sanity's Eclipse ----------
        @staticmethod
        def _draw_sanity_eclipse_ground(surface, boss, x, y, timer, phase):
            P = VexV1Renderer
            radius = P._ring_r(boss, 55, surface)
            P._aoe_marks(surface, x, y + 44, radius, P.C_VOID_LIGHT, 185,
                         phase, squash=.5, ticks=14, tick_len=7)

        @staticmethod
        def _draw_sanity_eclipse(surface, boss, x, y, timer, phase):
            P = VexV1Renderer
            progress = P._skill_progress(boss, "w", timer)
            radius = P._ring_r(boss, 55, surface)
            grow = min(1.0, progress * 2.4)
            n = 7
            for i in range(n):
                a = phase * .22 + i * math.tau / n
                cx = x + math.cos(a) * radius
                cy = y + 44 + math.sin(a) * radius * .5
                h = (14 + 16 * P._hash01(i + 3)) * grow
                P._crystal(surface, cx, cy, -math.pi / 2 + math.sin(a) * .18,
                           h, 5, (P.C_VOID_DARK, P.C_VOID_MID, P.C_VOID_HI),
                           int(225 * grow))
            ox, oy = P._staff_orb_position(
                x, y, getattr(boss, "direction", 1), phase, "attack", 0.56)
            P._spark_star(surface, ox, oy, 7, P.C_VOID_CORE,
                          int(200 * grow), 4, rot=phase)

        # ---------- Skill FX: E Astral Imprisonment ----------
        @staticmethod
        def _draw_astral_indicator(surface, boss, x, y, timer, phase):
            P = VexV1Renderer
            tx, ty = P._target_position(boss, x, y)
            P._dashed_ring(surface, tx, ty + 4, 20, P.C_AST_LIGHT, 150,
                           phase * 1.3, dashes=8, width=2, squash=.35)

        @staticmethod
        def _handle_astral_skill(surface, boss, x, y, timer, phase):
            P = VexV1Renderer
            progress = P._skill_progress(boss, "e", timer)
            tgt = getattr(boss, "_astral_prison_target", None)
            if tgt is not None and getattr(tgt, "alive", False):
                tx, ty = P._world_to_local(boss, x, y, tgt.x, tgt.y)
            else:
                tx, ty = P._target_position(boss, x, y)
            grow = min(1.0, progress * 3.0)
            r = int(26 * grow)
            if r > 2:
                P._aacircle(surface, (*P.C_AST_DARK, int(120 * grow)),
                            (tx, ty - 20), r + 6)
                P._dashed_ring(surface, tx, ty - 20, r + 6, P.C_AST_LIGHT,
                               int(220 * grow), phase * 1.6, dashes=10,
                               width=2, squash=.92)
                P._dashed_ring(surface, tx, ty - 20, max(4, r - 5),
                               P.C_AST_HI, int(190 * grow), -phase * 1.1,
                               dashes=8, width=1, squash=.92)
                for i in range(3):
                    a = phase * 2.0 + i * math.tau / 3
                    P._crystal(surface, tx + math.cos(a) * (r + 10),
                               ty - 20 + math.sin(a) * (r + 10) * .5,
                               -math.pi / 2, 8, 3,
                               (P.C_AST_DARK, P.C_AST_MID, P.C_AST_LIGHT),
                               int(210 * grow))

        # ---------- Skill FX: R Essence Flux ----------
        @staticmethod
        def _draw_essence_flux_ground(surface, boss, x, y, timer, phase):
            P = VexV1Renderer
            radius = P._ring_r(boss, 120, surface)
            P._aoe_marks(surface, x, y + 44, radius, P.C_GREEN, 175,
                         phase * 1.3, squash=.5, ticks=18, tick_len=9)

        @staticmethod
        def _draw_essence_flux(surface, boss, x, y, timer, phase):
            P = VexV1Renderer
            progress = P._skill_progress(boss, "r", timer)
            radius = P._ring_r(boss, 120, surface)
            boom = min(1.0, progress * 1.6)
            P._aacircle(surface, (*P.C_VOID_DARK, int(70 * (1 - boom * .5))),
                        (x, y), 24 + int(radius * .35 * boom))
            P._dashed_ring(surface, x, y + 4, 20 + radius * .8 * boom,
                           P.C_VOID_CORE, int(210 * (1 - boom * .4)),
                           phase * 2.0, dashes=20, width=3, squash=.4)
            P._dashed_ring(surface, x, y + 4, 12 + radius * .45 * boom,
                           P.C_GREEN, int(170 * (1 - boom * .4)),
                           -phase * 1.4, dashes=14, width=2, squash=.4)
            for i in range(8):
                a = phase * 1.1 + i * math.tau / 8
                rr = 18 + radius * .6 * boom
                P._spark_star(surface, x + math.cos(a) * rr,
                              y + 4 + math.sin(a) * rr * .45, 4,
                              P.C_GREEN, int(190 * (1 - progress * .3)),
                              4, rot=a)
            ox, oy = P._staff_orb_position(
                x, y, getattr(boss, "direction", 1), phase, "attack", 0.56)
            P._aacircle(surface, (*P.C_VOID_CORE, int(220 * boom)),
                        (ox, oy), 6 + int(12 * boom))

        # ---------- Attack swing trail (fallback in-canvas) ----------
        @staticmethod
        def _draw_staff_swing_trail(surface, cx, cy, f, phase, ap):
            P = VexV1Renderer
            if ap <= 0.15 or ap >= .92:
                return
            for i in range(6):
                p = max(0.0, ap - i * .05)
                tip = P._orb_tip_local(phase, "attack", p)
                P._aacircle(surface, (*P.C_VOID_MID, 130 - i * 18),
                            (cx + tip[0] * f, cy + tip[1]),
                            max(1, 5 - i // 2))
            tip = P._orb_tip_local(phase, "attack", ap)
            P._spark_star(surface, cx + tip[0] * f, cy + tip[1], 8,
                          P.C_VOID_CORE, 180, 4, rot=phase)

        # ------------------------------------------------------------------
        # Fallback projectile and the draw orchestrator.
        # ------------------------------------------------------------------
        class ArcaneOrbProjectile:
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
                self.damage = damage
                self.team = team
                self.angle = math.atan2(ty - sy, tx - sx)

            def update(self):
                if not self.alive:
                    self.dead_frames += 1
                    return
                self.age += 1
                if self.target is not None and getattr(self.target, "alive", False):
                    self.tx, self.ty = float(self.target.x), float(self.target.y)
                dx, dy = self.tx - self.x, self.ty - self.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    self.angle = math.atan2(dy, dx)
                if dist <= self.speed + 4:
                    self.alive = False
                    return
                self.trail.append((self.x, self.y))
                if len(self.trail) > 14:
                    self.trail.pop(0)
                self.x += dx / dist * self.speed
                self.y += dy / dist * self.speed

            def draw(self, surface, phase):
                P = VexV1Renderer
                if not self.alive:
                    t = max(0.0, 1.0 - self.dead_frames / 8.0)
                    if t > 0:
                        P._spark_star(surface, self.x, self.y, 16 * t,
                                      P.C_VOID_CORE, int(220 * t), 6,
                                      rot=phase)
                    return
                for i, (tx, ty) in enumerate(self.trail):
                    a = int(30 + 130 * i / max(1, len(self.trail) - 1))
                    P._aacircle(surface, (*P.C_VOID_MID, a), (tx, ty),
                                max(1, 5 - (len(self.trail) - i) // 3))
                P._aacircle(surface, (*P.C_VOID_LIGHT, 210), (self.x, self.y), 7)
                P._aacircle(surface, (*P.C_VOID_CORE, 235), (self.x, self.y), 4)
                P._spark_star(surface, self.x, self.y, 10, P.C_VOID_HI,
                              170, 4, rot=phase)

        class AstralOrbProjectile(ArcaneOrbProjectile):
            def draw(self, surface, phase):
                P = VexV1Renderer
                if not self.alive:
                    t = max(0.0, 1.0 - self.dead_frames / 8.0)
                    if t > 0:
                        P._dashed_ring(surface, self.x, self.y, 18 * t,
                                       P.C_AST_LIGHT, int(220 * t),
                                       phase, dashes=8, width=2, squash=.9)
                    return
                for i, (tx, ty) in enumerate(self.trail):
                    a = int(30 + 130 * i / max(1, len(self.trail) - 1))
                    P._aacircle(surface, (*P.C_AST_MID, a), (tx, ty),
                                max(1, 5 - (len(self.trail) - i) // 3))
                P._aacircle(surface, (*P.C_AST_LIGHT, 220), (self.x, self.y), 7)
                P._aacircle(surface, (*P.C_AST_HI, 235), (self.x, self.y), 4)

        @staticmethod
        def _manage_projectiles(boss, surface, phase):
            if getattr(boss, "_skip_renderer_projectiles", False):
                return
            items = getattr(boss, "_vx_projectiles", None)
            if items is None:
                boss._vx_projectiles = []
                items = boss._vx_projectiles
            for proj in items:
                proj.update()
                proj.draw(surface, phase)
            boss._vx_projectiles[:] = [p for p in items
                                       if p.alive or p.dead_frames < 8]

        @staticmethod
        def _spawn_arcane_orb(boss, x, y):
            if getattr(boss, "_skip_renderer_projectiles", False):
                return
            items = getattr(boss, "_vx_projectiles", None)
            if items is None:
                items = []
                boss._vx_projectiles = items
            P = VexV1Renderer
            tx, ty = P._target_position(boss, x, y)
            f = getattr(boss, "direction", 1)
            sx, sy = P._staff_orb_position(
                x, y, f, float(getattr(boss, "pulse", 0.0)), "attack",
                float(getattr(boss, "_vx_attack_progress", 0.0)))
            proj = P.ArcaneOrbProjectile(
                sx, sy, tx, ty, speed=6.5,
                target=getattr(boss, "target", None),
                team=getattr(boss, "team", None))
            proj.source, proj.cx, proj.cy = boss, x, y
            items.append(proj)

        @staticmethod
        def _spawn_astral_orb(boss, x, y):
            if getattr(boss, "_skip_renderer_projectiles", False):
                return
            items = getattr(boss, "_vx_projectiles", None)
            if items is None:
                items = []
                boss._vx_projectiles = items
            P = VexV1Renderer
            tx, ty = P._target_position(boss, x, y)
            f = getattr(boss, "direction", 1)
            sx, sy = P._staff_orb_position(
                x, y, f, float(getattr(boss, "pulse", 0.0)), "attack",
                float(getattr(boss, "_vx_attack_progress", 0.0)))
            proj = P.AstralOrbProjectile(
                sx, sy, tx, ty, speed=7.0,
                target=getattr(boss, "target", None),
                team=getattr(boss, "team", None))
            proj.source, proj.cx, proj.cy = boss, x, y
            items.append(proj)

        # ------------------------------------------------------------------
        # Pose modes.
        # ------------------------------------------------------------------
        @staticmethod
        def _draw_vex_idle(surface, boss, x, y):
            P = VexV1Renderer
            phase = float(getattr(boss, "pulse", 0.0))
            if not getattr(boss, "_portrait_hd", False):
                P._draw_shadow(surface, x, y + 62)
                P._draw_floating_void(surface, x, y + 46, phase)
            P._draw_vex_body(
                surface, x, y, getattr(boss, "direction", 1), phase, "idle",
                detail=bool(getattr(boss, "_portrait_hd", False)),
                skill_state=getattr(boss, "active_skill", None))

        @staticmethod
        def _draw_vex_walk(surface, boss, x, y):
            P = VexV1Renderer
            phase = float(getattr(boss, "pulse", 0.0))
            f = getattr(boss, "direction", 1)
            if not getattr(boss, "_portrait_hd", False):
                P._draw_shadow(surface, x, y + 62)
                P._draw_floating_void(surface, x, y + 46, phase,
                                      trail=True, facing=f)
            P._draw_vex_body(
                surface, x, y, f, phase, "walk",
                detail=bool(getattr(boss, "_portrait_hd", False)),
                skill_state=getattr(boss, "active_skill", None))

        @staticmethod
        def _draw_vex_attack(surface, boss, x, y):
            P = VexV1Renderer
            phase = float(getattr(boss, "pulse", 0.0))
            progress = max(0.0, min(1.0, float(
                getattr(boss, "_vx_attack_progress", 0.0))))
            f = getattr(boss, "direction", 1)
            portrait = bool(getattr(boss, "_portrait_hd", False))

            # Basic attack tidak spawn renderer projectile (pakai generic
            # _entity.py); orb renderer hanya saat skill aktif (pola legacy).
            if (getattr(boss, "active_skill", None) is not None
                    and 0.5 < progress < 0.6
                    and not getattr(boss, "_vx_proj_spawned", False)
                    and not portrait):
                if getattr(boss, "active_skill", None) == "e":
                    P._spawn_astral_orb(boss, x, y)
                else:
                    P._spawn_arcane_orb(boss, x, y)
                boss._vx_proj_spawned = True
            if progress < 0.15 or progress > 0.9:
                boss._vx_proj_spawned = False

            recoil = int(math.sin(progress * math.pi) * 2) * -f
            P._draw_vex_body(
                surface, x + recoil, y, f, phase, "attack", progress,
                detail=portrait,
                skill_state=getattr(boss, "active_skill", None))
            if not portrait and not P._FX_LIVE.v:
                P._draw_staff_swing_trail(surface, x, y, f, phase, progress)

        @staticmethod
        def _draw_vex_hurt(surface, boss, x, y):
            P = VexV1Renderer
            phase = float(getattr(boss, "pulse", 0.0))
            P._draw_vex_body(
                surface, x, y, getattr(boss, "direction", 1), phase, "hurt",
                detail=bool(getattr(boss, "_portrait_hd", False)))

        @staticmethod
        def draw_vex(surface, boss, x, y):
            """Entry point used by both the hero and boss render paths."""
            P = VexV1Renderer
            phase = float(getattr(boss, "pulse", 0.0))
            active_skill = getattr(boss, "active_skill", None)
            timer = int(getattr(boss, "active_skill_timer", 0) or 0)
            moving = P._detect_moving(boss)
            P._update_attack_anim(boss)
            portrait = bool(getattr(boss, "_portrait_hd", False))

            # Live FX wiring (sama seperti rig legacy): jalur hero lane
            # cukup attach (heroes/__init__ menggambar lapisannya), jalur
            # BOSS menggambar draw_ground_layer/draw_live_layer sendiri.
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

            attacking = bool(getattr(boss, "_vx_attack_active", False))
            alive = bool(getattr(boss, "alive", True))

            if not portrait:
                P._draw_mage_rim_light(surface, x, y - 12, phase)
                if active_skill == "r":
                    P._draw_flux_aura(surface, x, y, phase)
                else:
                    P._draw_void_aura(surface, x, y, phase)
                P._draw_void_platform(surface, x, y + 58, phase, active_skill)
                if active_skill == "q":
                    P._draw_arcane_orb_telegraph(surface, boss, x, y, timer, phase)
                elif active_skill == "w":
                    P._draw_sanity_eclipse_ground(surface, boss, x, y, timer, phase)
                elif active_skill == "r":
                    P._draw_essence_flux_ground(surface, boss, x, y, timer, phase)
                elif active_skill == "e":
                    P._draw_astral_indicator(surface, boss, x, y, timer, phase)

            skill_pose = {"q": "orbcast", "w": "eclipse",
                          "e": "astral", "r": "flux"}.get(active_skill)
            if not alive:
                P._draw_vex_body(surface, x, y, getattr(boss, "direction", 1),
                                 phase, "death", detail=portrait)
            elif attacking:
                P._draw_vex_attack(surface, boss, x, y)
            elif skill_pose is not None:
                P._draw_vex_body(surface, x, y, getattr(boss, "direction", 1),
                                 phase, skill_pose, detail=portrait)
            elif getattr(boss, "_vx_hurt_timer", 0) > 0:
                P._draw_vex_hurt(surface, boss, x, y)
            elif moving:
                P._draw_vex_walk(surface, boss, x, y)
            else:
                P._draw_vex_idle(surface, boss, x, y)

            if not portrait:
                P._manage_projectiles(boss, surface, phase)
                if active_skill == "q":
                    P._draw_arcane_orb_charge(surface, boss, x, y, timer, phase)
                elif active_skill == "w":
                    P._draw_sanity_eclipse(surface, boss, x, y, timer, phase)
                elif active_skill == "e":
                    P._handle_astral_skill(surface, boss, x, y, timer, phase)
                elif active_skill == "r":
                    P._draw_essence_flux(surface, boss, x, y, timer, phase)

                if not hero_lane:
                    try:
                        mod = P._live_module()
                        if mod is not None:
                            mod.draw_live_layer(surface, boss, x, y)
                    except Exception:
                        pass

            if P.DEBUG_CHARACTER:
                P._draw_debug(surface, boss, x, y)

        @staticmethod
        def draw_boss(surface, boss, x, y):
            VexV1Renderer.draw_vex(surface, boss, x, y)

        @staticmethod
        def _draw_debug(surface, boss, x, y):
            P = VexV1Renderer
            pygame.draw.rect(surface, (155, 245, 235),
                             pygame.Rect(int(x - 50), int(y - 90), 100, 150), 1)
            prog = float(getattr(boss, "_vx_attack_progress", 0.0))
            pygame.draw.rect(surface, P.C_OUTLINE,
                             pygame.Rect(int(x - 40), int(y - 105), 80, 5))
            pygame.draw.rect(surface, P.C_VOID_LIGHT,
                             pygame.Rect(int(x - 40), int(y - 105),
                                         int(80 * prog), 5))

        # The live FX module asks for these hooks when the renderer is
        # available, so use the current namespace's lazy import contract.
        @staticmethod
        def _live_module():
            if VexV1Renderer._LIVE_MOD is None:
                try:
                    from heroes import vex_fx as mod
                    VexV1Renderer._LIVE_MOD = (
                        mod if getattr(mod, "VEX_FX_ENABLED", True) else False)
                except Exception:
                    VexV1Renderer._LIVE_MOD = False
            return VexV1Renderer._LIVE_MOD or None

        @staticmethod
        def _fx_live_owned(hero):
            try:
                mod = VexV1Renderer._live_module()
                return bool(mod is not None and mod.owns(hero))
            except Exception:
                return False

        @staticmethod
        def live_fx_ready():
            return VexV1Renderer._live_module() is not None

    return VexV1Renderer
