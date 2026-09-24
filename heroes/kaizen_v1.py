"""Kaizen V1 pixel-art renderer adapted from the supplied Godot prototype.

The game is pygame based, so this module keeps the existing renderer contract
(``draw_kaizen(surface, hero, x, y)``) and translates the Godot CharacterBody2D
sprite/VFX layer into a procedural pygame renderer.  Gameplay, touch controls,
world generation and damage remain owned by Mystic Arena; this module only
owns Kaizen's visual pose and its canvas fallback effects.

The implementation deliberately has no image assets.  The small, integer-ish
rectangles are drawn at a native 2.6x pixel-art scale and are normalized by the
existing hero cache pipeline before reaching the arena.
"""

import math
import random

import pygame



def install(legacy_cls):
    """Return a V1 renderer subclass while retaining legacy API compatibility.

    ``heroes._bundle`` historically contains all hero namespaces in one file.
    Subclassing the old namespace lets older tools and the live FX layer keep
    importing their helper names while the actual Kaizen render path is fully
    replaced by the V1 pixel-art implementation below.
    """

    class KaizenV1Renderer(legacy_cls):
        """KAIZEN V1.0 — Wandering Swordsman (pixel-art adaptation)."""

        # ------------------------------------------------------------------
        # Palette: direct translation of the supplied Godot constants.
        # ------------------------------------------------------------------
        C_OUTLINE = (10, 14, 24)
        C_CLOTH_DARK = (26, 38, 71)
        C_CLOTH_MID = (45, 67, 115)
        C_CLOTH_LIGHT = (74, 107, 181)
        C_CLOTH_HI = (127, 168, 255)
        C_HAIR_DARK = (61, 36, 22)
        C_HAIR_MID = (107, 64, 40)
        C_HAIR_LIGHT = (156, 100, 64)
        C_SKIN = (240, 192, 144)
        C_SKIN_SH = (201, 141, 100)
        C_BELT = (107, 62, 31)
        C_BELT_HI = (168, 103, 48)
        C_PANTS = (30, 45, 92)
        C_PANTS_HI = (58, 77, 138)
        C_BOOT = (42, 26, 16)
        C_BLADE = (216, 228, 245)
        C_BLADE_HI = (255, 255, 255)
        C_HILT = (42, 24, 16)
        C_WIND = (175, 255, 255)
        C_WIND_CORE = (255, 255, 255)
        C_SCARF = (58, 90, 168)
        C_TABI = (204, 211, 216)

        # The renderer namespace is also consumed by heroes/kaizen_fx.py.
        # Keep its historic keys as aliases so the live layer remains binary
        # compatible while following the new blue-samurai palette.
        PALETTE = {
            "outline": C_OUTLINE,
            "ink": C_OUTLINE,
            "ink_soft": (38, 52, 82),
            "paper": (250, 250, 255),
            "cloth_dark": C_CLOTH_DARK,
            "cloth_mid": C_CLOTH_MID,
            "cloth_light": C_CLOTH_LIGHT,
            "cloth_high": C_CLOTH_HI,
            "skin_darkest": (130, 86, 58),
            "skin_dark": C_SKIN_SH,
            "skin_mid": C_SKIN,
            "skin_light": (250, 214, 174),
            "skin_high": (255, 235, 204),
            "hair_darkest": (35, 20, 13),
            "hair_dark": C_HAIR_DARK,
            "hair_mid": C_HAIR_MID,
            "hair_light": C_HAIR_LIGHT,
            "hair_shine": (196, 135, 88),
            "hair_high": (230, 176, 116),
            "pants_dark": C_PANTS,
            "pants_mid": C_PANTS_HI,
            "pants_light": (84, 105, 178),
            "leather_dark": C_BELT,
            "leather_mid": C_BELT_HI,
            "leather_light": (215, 145, 74),
            "steel_darkest": (72, 85, 108),
            "steel_dark": (126, 145, 174),
            "steel_mid": C_BLADE,
            "steel_light": (235, 243, 255),
            "steel_shine": C_BLADE_HI,
            "wrap_dark": (35, 27, 24),
            "wrap_mid": (78, 46, 38),
            "wrap_light": (140, 91, 66),
            "gold_dark": (110, 69, 30),
            "gold_mid": C_BELT_HI,
            "gold_light": C_BELT_HI,
            "gold_shine": (244, 190, 92),
            # Compatibility aliases.  V1 has no lacquered saya, so these
            # point to the warm belt material actually drawn by the rig.
            "saya_dark": (53, 32, 25),
            "saya_mid": C_BELT_HI,
            "saya_light": (206, 133, 64),
            "saya_shine": (241, 190, 112),
            "scarf_deep": (30, 50, 108),
            "scarf_dark": (42, 69, 137),
            "scarf_mid": C_SCARF,
            "scarf_light": C_CLOTH_LIGHT,
            "scarf_high": C_CLOTH_HI,
            "wind_deep": (28, 74, 118),
            "wind_darkest": (46, 112, 164),
            "wind_dark": (76, 166, 220),
            "wind_mid": (127, 200, 255),
            "wind_light": (170, 229, 255),
            "wind_bright": (213, 244, 255),
            "wind_white": C_WIND_CORE,
            "wind_pale": (232, 248, 255),
            "eye_white": C_BLADE_HI,
            "eye_iris": (102, 177, 255),
            "eye_iris_light": C_BLADE_HI,
            "eye_pupil": C_OUTLINE,
            "eye_glow": C_WIND,
            "cord_dark": (40, 55, 115),
            "cord_mid": C_SCARF,
            "shadow": (0, 0, 0),
            "shadow_deep": C_OUTLINE,
            "white": C_BLADE_HI,
        }

        # Native coordinates from the Godot prototype.  The existing
        # pipeline later normalizes this larger rig to arena size.
        PIXEL_SCALE = 2.6
        PIXEL_ORIGIN = 24.0
        # Sword geometry is shared by the cached body and the live swing
        # trail.  The old body used 26 source pixels while the FX tip used
        # a shorter, hand-offset estimate, which made the kissaki look
        # chopped off in the arena.  Keep the small pixel-art grip offset
        # explicit so both paths terminate at the same visible point.
        BLADE_GRIP_SOURCE = 2.0
        BLADE_BASE_SOURCE = 28.0
        BLADE_LEN = (BLADE_GRIP_SOURCE + BLADE_BASE_SOURCE) * PIXEL_SCALE
        SKILL_VISUAL_DURATION = {"q": 39, "w": 59, "e": 39, "r": 66}

        ATTACK_WINDUP_END = 0.28
        ATTACK_SWING_END = 0.72
        ATTACK_IMPACT = 0.54
        ATTACK_IMPACT_POINT = ATTACK_IMPACT
        ATTACK_ACTIVE_WINDOW = (0.43, 0.64)

        ANIM_STATES = {
            "IDLE": 0, "WALK": 10, "DASH": 20, "WINDWALL": 30,
            "SWEEP": 35, "TORNADO": 40, "ATTACK": 50,
            "HURT": 70, "DEATH": 100,
        }
        DEBUG_CHARACTER = False

        _LIVE_MOD = None
        _STATIC_SURFACES = {}
        _SCRATCH_POOL = {}
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
            c = KaizenV1Renderer._clamp(color)
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
            surf = KaizenV1Renderer._STATIC_SURFACES.get(key)
            if surf is None:
                if len(KaizenV1Renderer._STATIC_SURFACES) > 96:
                    KaizenV1Renderer._STATIC_SURFACES.clear()
                surf = builder()
                KaizenV1Renderer._STATIC_SURFACES[key] = surf
            return surf

        @staticmethod
        def _scratch(w, h):
            key = (max(1, int(w)), max(1, int(h)))
            surf = KaizenV1Renderer._SCRATCH_POOL.get(key)
            if surf is None:
                if len(KaizenV1Renderer._SCRATCH_POOL) > 24:
                    KaizenV1Renderer._SCRATCH_POOL.clear()
                surf = pygame.Surface(key, pygame.SRCALPHA)
                KaizenV1Renderer._SCRATCH_POOL[key] = surf
            surf.fill((0, 0, 0, 0))
            return surf

        @staticmethod
        def _rect(surface, color, rect, border_radius=0):
            pygame.draw.rect(surface, KaizenV1Renderer._rgba(color),
                             pygame.Rect(*(int(round(v)) for v in rect)),
                             border_radius=max(0, int(border_radius)))

        @staticmethod
        def _poly(surface, color, points):
            if len(points) >= 3:
                pygame.draw.polygon(surface, KaizenV1Renderer._rgba(color),
                                    [(int(round(x)), int(round(y))) for x, y in points])

        @staticmethod
        def _ellipse(surface, color, rect, width=0):
            pygame.draw.ellipse(surface, KaizenV1Renderer._rgba(color),
                                pygame.Rect(*(int(round(v)) for v in rect)),
                                max(0, int(width)))

        @staticmethod
        def _aaline(surface, color, start, end, width=1):
            pygame.draw.line(surface, KaizenV1Renderer._rgba(color),
                             (int(round(start[0])), int(round(start[1]))),
                             (int(round(end[0])), int(round(end[1]))),
                             max(1, int(round(width))))

        @staticmethod
        def _aacircle(surface, color, center, radius, width=0):
            pygame.draw.circle(surface, KaizenV1Renderer._rgba(color),
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
                KaizenV1Renderer._rect(surface, (*color[:3], alpha),
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
                KaizenV1Renderer._aaline(surface, (*color[:3], alpha), p0, p1, 1)
            if core is not None:
                KaizenV1Renderer._aacircle(surface, (*core[:3], alpha),
                                            (cx, cy), max(1, size * 0.22))

        @staticmethod
        def _chevron(surface, cx, cy, ang, size, color, alpha, width=2):
            ux, uy = math.cos(ang), math.sin(ang)
            px, py = -uy, ux
            tip = (cx + ux * size, cy + uy * size)
            a = (cx - ux * size * .35 + px * size * .55,
                 cy - uy * size * .35 + py * size * .55)
            b = (cx - ux * size * .35 - px * size * .55,
                 cy - uy * size * .35 - py * size * .55)
            KaizenV1Renderer._aaline(surface, (*color[:3], alpha), a, tip, width)
            KaizenV1Renderer._aaline(surface, (*color[:3], alpha), tip, b, width)

        @staticmethod
        def _dashed_ring(surface, cx, cy, radius, color, alpha, phase,
                         dashes=12, width=2, squash=1.0):
            for i in range(max(4, int(dashes))):
                a0 = phase + i * math.tau / dashes + .08
                a1 = phase + (i + .72) * math.tau / dashes
                pts = [(cx + math.cos(a0 + (a1 - a0) * j / 5.0) * radius,
                        cy + math.sin(a0 + (a1 - a0) * j / 5.0) * radius * squash)
                       for j in range(6)]
                pygame.draw.lines(surface, KaizenV1Renderer._rgba((*color[:3], alpha)),
                                  False, [(int(x), int(y)) for x, y in pts], width)

        @staticmethod
        def _jagged_crack(surface, cx, cy, ang, length, colors, alpha, seed,
                          width=2):
            pts = [(cx, cy)]
            ux, uy = math.cos(ang), math.sin(ang)
            px, py = -uy, ux
            for i in range(1, 7):
                t = i / 6.0
                jitter = (KaizenV1Renderer._hash01(seed + i * 9) - .5) * length * .22
                pts.append((cx + ux * length * t + px * jitter,
                            cy + uy * length * t + py * jitter))
            for i in range(len(pts) - 1):
                col = colors[i % len(colors)] if colors else KaizenV1Renderer.C_WIND
                KaizenV1Renderer._aaline(surface, (*col[:3], alpha),
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
                    side = -1.0 if KaizenV1Renderer._hash01(seed + i) < .5 else 1.0
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
                KaizenV1Renderer._aaline(surface, (*KaizenV1Renderer.C_OUTLINE, alpha),
                                         p0, p1, 3)
                KaizenV1Renderer._aaline(surface, (*color[:3], alpha), p0, p1, 1)
            if corner:
                for a in (math.pi / 4, 3 * math.pi / 4,
                          5 * math.pi / 4, 7 * math.pi / 4):
                    p = (cx + math.cos(a) * radius,
                         cy + math.sin(a) * radius * squash)
                    KaizenV1Renderer._chevron(surface, p[0], p[1], a + math.pi / 2,
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
            KaizenV1Renderer._poly(surface, color, pts)

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
            duration = float(KaizenV1Renderer.SKILL_VISUAL_DURATION.get(skill,
                                                                        max(1, timer or 1)))
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
                return KaizenV1Renderer._world_to_local(
                    boss, x, y, target.x, target.y)
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            return int(x + 150 * scale * getattr(boss, "direction", 1)), int(y)

        @staticmethod
        def _pixel_local(x, y):
            s = KaizenV1Renderer.PIXEL_SCALE
            return ((float(x) - KaizenV1Renderer.PIXEL_ORIGIN) * s,
                    (float(y) - KaizenV1Renderer.PIXEL_ORIGIN) * s)

        @staticmethod
        def _tint(color, tint):
            c = KaizenV1Renderer._clamp(color)
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
            """Create R/RO closures equivalent to Godot's pixel helpers."""
            s = KaizenV1Renderer.PIXEL_SCALE
            sx = -1.0 if facing < 0 else 1.0

            def rect_for(x, y, w, h, ox=0, oy=0, extra_crouch=0):
                rx = cx + ((x + body_x + ox - KaizenV1Renderer.PIXEL_ORIGIN) * s * sx)
                if facing < 0:
                    rx -= w * s
                ry = cy + ((y + body_y + crouch + extra_crouch -
                            KaizenV1Renderer.PIXEL_ORIGIN) * s)
                return pygame.Rect(int(round(rx)), int(round(ry)),
                                  max(1, int(round(w * s))),
                                  max(1, int(round(h * s))))

            def R(x, y, w, h, col, alpha=None):
                color = KaizenV1Renderer._tint(col, tint)
                if alpha is not None:
                    color = color[:3] + (int(color[3] * alpha / 255.0),)
                pygame.draw.rect(surface, color, rect_for(x, y, w, h))

            def RO(x, y, w, h, col, alpha=None):
                # A one source-pixel selout keeps the sprite readable after
                # smoothscale, while preserving the chunky V1 silhouette.
                # Slightly darker selout than the named palette swatch keeps
                # a true dark contour after the later HD lighting pass.
                R(x - 1, y - 1, w + 2, h + 2,
                  (8, 11, 20), alpha)
                R(x, y, w, h, col, alpha)

            def point(x, y, ox=0, oy=0):
                return (cx + ((x + body_x + ox - KaizenV1Renderer.PIXEL_ORIGIN) * s * sx),
                        cy + ((y + body_y + crouch + oy - KaizenV1Renderer.PIXEL_ORIGIN) * s))

            def line(a, b, color, width=1, alpha=None):
                c = KaizenV1Renderer._tint(color, tint)
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
            if not hasattr(boss, "_kz_last_x"):
                boss._kz_last_x = float(getattr(boss, "x", 0.0))
                boss._kz_last_y = float(getattr(boss, "y", 0.0))
                boss._moving_cached = False
                return False
            dx = abs(float(getattr(boss, "x", 0.0)) - boss._kz_last_x)
            dy = abs(float(getattr(boss, "y", 0.0)) - boss._kz_last_y)
            boss._kz_last_x = float(getattr(boss, "x", 0.0))
            boss._kz_last_y = float(getattr(boss, "y", 0.0))
            moving = dx + dy > .3
            boss._moving_cached = moving
            return moving

        @staticmethod
        def _update_attack_anim(boss):
            cooldown = max(2, int(getattr(boss, "attack_cooldown", 45) or 45))
            timer = int(getattr(boss, "timer", getattr(boss, "attack_timer", 0)) or 0)
            previous = int(getattr(boss, "_kz_prev_timer", -1))
            active = bool(getattr(boss, "_kz_attack_active", False))
            # A new attack is the only upward edge of the countdown timer.
            if timer > 0 and (previous <= 0 or timer > previous):
                active = True
                last_start = float(getattr(boss, "_kz_last_attack_pulse", -99.0))
                now = float(getattr(boss, "pulse", 0.0))
                if now - last_start <= 1.0:
                    boss._kz_combo = (int(getattr(boss, "_kz_combo", 0)) + 1) % 3
                else:
                    boss._kz_combo = 0
                boss._kz_last_attack_pulse = now
                boss._kz_proj_spawned = False
            if active and timer <= 0:
                active = False
            boss._kz_prev_timer = timer
            boss._kz_attack_active = active
            frame = max(0, cooldown - timer) if active else 0
            boss._kz_attack_frame = frame
            boss._kz_attack_progress = min(1.0, frame / max(1, cooldown - 1)) if active else 0.0

        @staticmethod
        def _attack_pose(ap):
            """Return the V1 sword pose in renderer-local pixels.

            The supplied script has five discrete frames.  Interpolating
            those keyframes keeps the same silhouette while making the
            existing 60 Hz/cache pipeline look less stepped.
            """
            keys = (
                (0.00, -1.80, 0, -2, 0),
                (0.25, -0.80, -2, 0, 1),
                (0.50, 0.30, 0, 6, 3),
                (0.75, 1.20, 0, 8, 4),
                (1.00, 1.40, 0, 4, 2),
            )
            ap = max(0.0, min(1.0, float(ap)))
            for a, b in zip(keys, keys[1:]):
                if a[0] <= ap <= b[0]:
                    t = (ap - a[0]) / max(1e-6, b[0] - a[0])
                    t = t * t * (3.0 - 2.0 * t)
                    angle = a[1] + (b[1] - a[1]) * t
                    body_x = a[2] + (b[2] - a[2]) * t
                    arm = a[3] + (b[3] - a[3]) * t
                    lean = a[4] + (b[4] - a[4]) * t
                    # Match the actual hand used by
                    # _draw_pixel_sword_arm: shoulder -> hand is an
                    # eight-source-pixel reach plus the pose's forward
                    # arm offset.  The previous helper omitted the reach,
                    # so live trail/projectile geometry stopped short of
                    # the blade rendered by the cached body.
                    hx = 30.0 + math.cos(angle) * 8.0 + arm
                    hy = 22.0 + math.sin(angle) * 8.0
                    hpx, hpy = KaizenV1Renderer._pixel_local(hx, hy)
                    return {"angle": angle, "bob": int(round(lean * 1.5)),
                            "lean": int(round(body_x)),
                            "hand": (hpx, hpy),
                            "flare": 1.0 + .25 * (1.0 - abs(ap - .5) * 2),
                            "tremble": 1 if .20 < ap < .36 else 0}
            angle = 1.4
            hx = 30.0 + math.cos(angle) * 8.0 + 4.0
            hy = 22.0 + math.sin(angle) * 8.0
            return {"angle": angle, "bob": 0, "lean": 2,
                    "hand": KaizenV1Renderer._pixel_local(hx, hy),
                    "flare": 1.0, "tremble": 0}

        @staticmethod
        def _katana_angle(phase, action, progress=0.0):
            if action == "attack":
                return KaizenV1Renderer._attack_pose(progress)["angle"]
            if action == "walk":
                return .10 + math.sin(float(phase) * 1.7) * .05
            return .20 + math.sin(float(phase) * .72) * .03

        @staticmethod
        def _attack_extension(progress, attack_combo=0):
            """Return the extra source-pixel blade length for a combo.

            The cached body has three combo pose tables.  Keeping this tiny
            geometry helper beside the pose code prevents the 60 Hz live
            trail from ending before the cached sword tip.
            """
            tables = (
                (0.0, 0.0, 6.0, 8.0, 4.0),
                (0.0, 2.0, 14.0, 10.0, 4.0),
                (0.0, 0.0, 0.0, 0.0, 0.0),
            )
            keys = tables[int(attack_combo) % len(tables)]
            ap = max(0.0, min(1.0, float(progress)))
            spans = (0.0, 0.25, 0.50, 0.75, 1.0)
            for i in range(len(spans) - 1):
                if spans[i] <= ap <= spans[i + 1]:
                    t = (ap - spans[i]) / max(1e-6, spans[i + 1] - spans[i])
                    t = t * t * (3.0 - 2.0 * t)
                    return keys[i] + (keys[i + 1] - keys[i]) * t
            return keys[-1]

        @staticmethod
        def _katana_tip_local(phase, action, progress=0.0,
                              attack_combo=None):
            P = KaizenV1Renderer
            if action == "attack":
                pose = P._attack_pose(progress)
                hx, hy = pose["hand"]
                angle = pose["angle"]
                if attack_combo is None:
                    hero = getattr(P, "_DRAW_HERO", None)
                    attack_combo = int(getattr(hero, "_kz_combo", 0) or 0)
                length = P.BLADE_LEN + (
                    P._attack_extension(progress, attack_combo)
                    * P.PIXEL_SCALE)
            elif action == "walk":
                angle = P._katana_angle(phase, action)
                hand_x = 30.0 + math.cos(angle) * 8.0
                hand_y = 22.0 + math.sin(angle) * 8.0
                hx, hy = P._pixel_local(hand_x, hand_y)
                length = P.BLADE_LEN
            else:
                angle = P._katana_angle(phase, action)
                hand_x = 30.0 + math.cos(angle) * 8.0
                hand_y = 22.0 + math.sin(angle) * 8.0
                hx, hy = P._pixel_local(hand_x, hand_y)
                length = P.BLADE_LEN
            return (hx + math.cos(angle) * length,
                    hy + math.sin(angle) * length)

        @staticmethod
        def _katana_hand_local(phase, action, progress=0.0):
            P = KaizenV1Renderer
            if action == "attack":
                return P._attack_pose(progress)["hand"]
            angle = P._katana_angle(phase, action)
            return P._pixel_local(30.0 + math.cos(angle) * 8.0,
                                  22.0 + math.sin(angle) * 8.0)

        # ------------------------------------------------------------------
        # The actual V1 sprite layers, translated from the supplied script.
        # ------------------------------------------------------------------
        @staticmethod
        def _draw_pixel_legs(R, RO, leg_pose, anim_name):
            P = KaizenV1Renderer
            if anim_name == "dash":
                RO(22, 36, 5, 8, P.C_PANTS)
                RO(16, 40, 6, 5, P.C_BOOT)
                RO(28, 38, 6, 6, P.C_BOOT)
            elif anim_name in ("idle", "attack", "windwall", "sweep", "tornado", "hurt"):
                RO(16, 38, 6, 8, P.C_PANTS)
                RO(26, 38, 6, 8, P.C_PANTS)
                RO(15, 44, 8, 4, P.C_BOOT)
                RO(25, 44, 8, 4, P.C_BOOT)
                # bright tabi strips from the source palette
                R(16, 42, 5, 3, P.C_TABI)
                R(26, 42, 5, 3, P.C_TABI)
            else:
                poses = (
                    ((16, 38, 6, 9), (26, 38, 6, 9), (15, 45, 8, 3), (25, 45, 8, 3)),
                    ((14, 38, 6, 9), (28, 38, 6, 9), (13, 45, 8, 3), (27, 45, 8, 3)),
                    ((20, 38, 6, 9), (24, 38, 6, 9), (19, 45, 8, 3), (23, 45, 8, 3)),
                    ((18, 38, 6, 9), (26, 38, 9, 9), (17, 45, 8, 3), (25, 45, 8, 3)),
                )
                pose = poses[int(leg_pose) % len(poses)]
                for box in pose[:2]:
                    RO(*box, P.C_PANTS)
                for box in pose[2:]:
                    RO(*box, P.C_BOOT)
                R(pose[0][0], pose[0][1] + 4, pose[0][2] - 1, 3, P.C_TABI)
                R(pose[1][0], pose[1][1] + 4, pose[1][2] - 1, 3, P.C_TABI)

        @staticmethod
        def _draw_pixel_hair(R, RO, head_y, flip_left, anim_name, hair_wave):
            P = KaizenV1Renderer
            RO(17, 5 + head_y, 14, 6, P.C_HAIR_DARK)
            R(18, 4 + head_y, 12, 5, P.C_HAIR_MID)
            R(19, 4 + head_y, 8, 3, P.C_HAIR_LIGHT)
            R(16, 8 + head_y, 3, 5, P.C_HAIR_DARK)
            R(29, 8 + head_y, 3, 5, P.C_HAIR_DARK)
            R(16, 8 + head_y, 2, 3, P.C_HAIR_MID)
            R(30, 8 + head_y, 2, 3, P.C_HAIR_MID)
            wave = math.sin(hair_wave) * 2.0
            pt = int(round(wave))
            RO(11, 2 + head_y, 6, 5, P.C_HAIR_DARK)
            RO(8 + pt, -1 + head_y, 5, 6, P.C_HAIR_DARK)
            R(9 + pt, 0 + head_y, 3, 4, P.C_HAIR_MID)
            RO(9 + pt, -4 + head_y, 3, 4, P.C_HAIR_DARK)
            R(10 + pt, -4 + head_y, 1, 3, P.C_HAIR_MID)
            RO(11 + pt, -6 + head_y, 3, 3, P.C_HAIR_DARK)
            R(12 + pt, -6 + head_y, 1, 2, P.C_HAIR_LIGHT)
            RO(13 + pt, -8 + head_y, 3, 3, P.C_HAIR_DARK)
            R(14 + pt, -8 + head_y, 1, 2, P.C_HAIR_MID)
            # Small forward spike: keeps the silhouette readable when the
            # sprite is mirrored and scaled down to a lane hero.
            RO(27, -4 + head_y, 2, 3, P.C_HAIR_DARK)
            R(18, 8 + head_y, 3, 2, P.C_HAIR_DARK)
            R(27, 8 + head_y, 3, 2, P.C_HAIR_DARK)

        @staticmethod
        def _draw_pixel_scarf(R, RO, flip_left, wave_amt, anim_name, hair_wave):
            P = KaizenV1Renderer
            RO(17, 17, 14, 4, P.C_SCARF)
            R(18, 18, 12, 2, P.C_CLOTH_LIGHT)
            w1 = math.sin(hair_wave) * wave_amt
            w2 = math.sin(hair_wave + 1.0) * wave_amt
            w3 = math.sin(hair_wave + 2.0) * wave_amt
            base_x = 12
            if anim_name == "dash":
                for x, y in ((10, 20), (6, 21), (2, 22), (-2, 22 + int(w1))):
                    RO(x, y, 5, 3, P.C_SCARF)
                R(-1, 22 + int(w1), 3, 1, P.C_CLOTH_LIGHT)
            else:
                RO(base_x, 20, 4, 4, P.C_SCARF)
                RO(base_x - 1 + int(w1), 23, 4, 4, P.C_SCARF)
                RO(base_x - 2 + int(w2), 26, 4, 4, P.C_SCARF)
                RO(base_x - 1 + int(w3), 29, 3, 4, P.C_SCARF)
                R(base_x + int(w1), 22, 2, 1, P.C_CLOTH_LIGHT)

        @staticmethod
        def _draw_pixel_sword_arm(R, RO, point, line, angle, extend,
                                  arm_forward, anim_name, show_charge):
            P = KaizenV1Renderer
            shoulder_x, shoulder_y = 30.0, 22.0
            hand_dist = 8.0
            hand_x = shoulder_x + math.cos(angle) * hand_dist + arm_forward
            hand_y = shoulder_y + math.sin(angle) * hand_dist
            RO(shoulder_x, shoulder_y, 4, 4, P.C_CLOTH_DARK)
            R(shoulder_x, shoulder_y, 3, 2, P.C_CLOTH_LIGHT)
            mid_x = (shoulder_x + hand_x) * .5
            mid_y = (shoulder_y + hand_y) * .5
            RO(mid_x, mid_y, 4, 4, P.C_SKIN)
            R(mid_x, mid_y + 1, 3, 2, P.C_SKIN_SH)
            RO(hand_x, hand_y, 4, 4, P.C_SKIN)

            sword_length = P.BLADE_BASE_SOURCE + extend
            blade_start_x = hand_x + P.BLADE_GRIP_SOURCE
            blade_start_y = hand_y + P.BLADE_GRIP_SOURCE
            blade_end_x = blade_start_x + math.cos(angle) * sword_length
            blade_end_y = blade_start_y + math.sin(angle) * sword_length
            # Segmented pixel line: dark selout, pale blade, white tip.
            # The extra source-pixel cap makes the kissaki read as a
            # complete pointed blade after the HD downscale instead of a
            # white line that appears abruptly chopped at its end.
            for i in range(12):
                t = i / 12.0
                t2 = (i + 1) / 12.0
                a = point(blade_start_x + math.cos(angle) * sword_length * t,
                          blade_start_y + math.sin(angle) * sword_length * t)
                b = point(blade_start_x + math.cos(angle) * sword_length * t2,
                          blade_start_y + math.sin(angle) * sword_length * t2)
                line((blade_start_x + math.cos(angle) * sword_length * t,
                      blade_start_y + math.sin(angle) * sword_length * t),
                     (blade_start_x + math.cos(angle) * sword_length * t2,
                      blade_start_y + math.sin(angle) * sword_length * t2),
                     P.C_OUTLINE, 3)
                line((blade_start_x + math.cos(angle) * sword_length * t,
                      blade_start_y + math.sin(angle) * sword_length * t),
                     (blade_start_x + math.cos(angle) * sword_length * t2,
                      blade_start_y + math.sin(angle) * sword_length * t2),
                     P.C_BLADE, 2)
            tip_cap_a = (blade_end_x - math.cos(angle) * 1.4,
                         blade_end_y - math.sin(angle) * 1.4)
            tip_cap_b = (blade_end_x + math.cos(angle) * 1.4,
                         blade_end_y + math.sin(angle) * 1.4)
            line(tip_cap_a, tip_cap_b, P.C_OUTLINE, 3)
            line(tip_cap_a, tip_cap_b, P.C_BLADE_HI, 1)
            R(blade_end_x, blade_end_y, 2, 2, P.C_BLADE_HI)
            R(blade_end_x - 1, blade_end_y - 1, 2, 2, P.C_BLADE)
            RO(hand_x + 1, hand_y + 1, 3, 3, P.C_HILT)
            R(hand_x + 1, hand_y + 1, 3, 1, P.C_BELT_HI)
            hilt_x = hand_x - math.cos(angle) * 3.0
            hilt_y = hand_y - math.sin(angle) * 3.0
            R(hilt_x, hilt_y + 1, 2, 3, P.C_HILT)
            if show_charge or anim_name == "dash":
                for i in range(4):
                    t = i / 4.0
                    gx = hand_x + 2 + math.cos(angle) * sword_length * (.3 + t * .7)
                    gy = hand_y + 2 + math.sin(angle) * sword_length * (.3 + t * .7)
                    size = 5.0 - t * 2.0
                    R(gx - size * .5, gy - size * .5, size, size,
                      (*P.C_WIND_CORE, 150))

        @staticmethod
        def _draw_kaizen_sprite(surface, origin, flip_left, anim_name,
                                frame_idx, tint=(255, 255, 255, 255),
                                attack_combo=0, hair_wave=0.0):
            P = KaizenV1Renderer
            # Match the source's pose table.
            body_y = body_x = head_y = 0
            sword_angle = 0.0
            sword_extend = 0
            leg_pose = 0
            arm_forward = 0
            scarf_wave_amt = 1.0
            dead = False
            flash = False
            lean = 0
            crouch = 0
            show_charge = False
            frame_idx = int(frame_idx)

            if anim_name == "idle":
                body_y = 1 if frame_idx % 2 else 0
                head_y = body_y
                scarf_wave_amt = 1.5
            elif anim_name == "walk":
                body_y = -1 if frame_idx % 2 else 0
                head_y = body_y
                leg_pose = frame_idx % 4
                scarf_wave_amt = 2.0
            elif anim_name == "attack":
                combo = int(attack_combo) % 3
                if combo == 0:
                    poses = ((-1.8, -2, 0, 0, 0), (-.8, 0, 0, 0, 1),
                             (.3, 0, 0, 6, 3), (1.2, 0, 0, 8, 4), (1.4, 0, 0, 4, 2))
                elif combo == 1:
                    poses = ((0.0, -4, -3, 0, 0), (0.0, 2, 0, 0, 0),
                             (0.0, 14, 5, 0, 4), (0.0, 10, 3, 0, 2), (0.0, 4, 0, 0, 0))
                else:
                    poses = ((1.5, 0, 0, 0, 0), (.5, 0, 0, 0, 0),
                             (-.6, 0, 0, 6, -2), (-1.6, 0, 0, 8, -3), (-1.2, 0, 0, 0, 0))
                sword_angle, sword_extend, body_x, arm_forward, crouch = poses[min(4, max(0, frame_idx))]
                scarf_wave_amt = 4.0
            elif anim_name == "dash":
                body_x, lean, crouch, leg_pose = 3, 4, 3, (1 if frame_idx % 2 == 0 else 3)
                sword_angle, arm_forward, scarf_wave_amt = .6, 4, 5.0
            elif anim_name == "windwall":
                crouch = (1, 2, 1, 0, 0)[min(4, max(0, frame_idx))]
                arm_forward = (0, 3, 5, 4, 2)[min(4, max(0, frame_idx))]
                sword_angle, scarf_wave_amt = -.5, 3.5
            elif anim_name == "sweep":
                crouch = (2, 3, -2, 0, 0)[min(4, max(0, frame_idx))]
                sword_angle = (-.3, -.3, .8, .6, .3)[min(4, max(0, frame_idx))]
                if frame_idx == 2:
                    body_y, arm_forward = -3, 3
                scarf_wave_amt = 4.0
            elif anim_name == "tornado":
                if frame_idx <= 2:
                    crouch, show_charge, sword_angle = 1 + frame_idx, True, -.4
                elif frame_idx == 3:
                    crouch, show_charge, sword_angle = 3, True, -.6
                elif frame_idx == 4:
                    crouch, body_y, sword_angle, arm_forward = -2, -2, .7, 4
                elif frame_idx == 5:
                    sword_angle = .4
                else:
                    sword_angle = .2
                scarf_wave_amt = 4.5
            elif anim_name == "hurt":
                flash = True
                body_x = 3 if not flip_left else -3
                head_y, body_y, sword_angle = -1, (1 if frame_idx == 1 else 0), -.8
            elif anim_name == "death":
                if frame_idx == 0:
                    flash, head_y = True, -1
                elif frame_idx == 1:
                    crouch, head_y = 4, 2
                elif frame_idx == 2:
                    crouch, head_y = 8, 5
                else:
                    dead = True

            use_tint = (255, 89, 89, 255) if flash else tint
            R, RO, point, line = P._make_pixel_ops(
                surface, origin[0], origin[1], -1 if flip_left else 1,
                body_x, body_y, crouch, use_tint)

            if dead:
                RO(10, 42, 28, 5, P.C_CLOTH_DARK)
                R(12, 43, 24, 3, P.C_CLOTH_MID)
                RO(10, 40, 10, 5, P.C_SKIN)
                RO(20, 44, 22, 2, P.C_BLADE)
                R(20, 44, 4, 2, P.C_HILT)
                R(9, 39, 4, 3, P.C_HAIR_MID)
                R(8, 40, 3, 2, P.C_HAIR_DARK)
                return

            # Back-to-front order is intentionally identical to the source.
            P._draw_pixel_scarf(R, RO, flip_left, scarf_wave_amt, anim_name, hair_wave)
            RO(14, 20, 3, 14, P.C_BELT)
            P._draw_pixel_legs(R, RO, leg_pose, anim_name)
            RO(15, 32, 18, 8, P.C_PANTS)
            R(17, 33, 14, 5, P.C_PANTS_HI)
            RO(14, 30, 20, 4, P.C_BELT)
            R(15, 31, 18, 2, P.C_BELT_HI)
            R(30 if not flip_left else 15, 30, 3, 5, P.C_SCARF)
            RO(16, 20, 16, 12, P.C_SKIN)
            R(18, 22, 5, 8, P.C_SKIN_SH)
            R(25, 22, 5, 8, P.C_SKIN_SH)
            R(23, 24, 2, 6, P.C_SKIN_SH)
            RO(14, 18, 5, 16, P.C_CLOTH_DARK)
            R(15, 19, 3, 14, P.C_CLOTH_MID)
            RO(29, 18, 5, 16, P.C_CLOTH_DARK)
            R(30, 19, 3, 14, P.C_CLOTH_MID)
            R(15, 19, 2, 3, P.C_CLOTH_LIGHT)
            R(30, 19, 2, 3, P.C_CLOTH_LIGHT)
            RO(13, 18, 5, 5, P.C_CLOTH_DARK)
            R(14, 19, 3, 3, P.C_CLOTH_LIGHT)
            RO(30, 18, 5, 5, P.C_CLOTH_DARK)
            R(31, 19, 3, 3, P.C_CLOTH_LIGHT)
            R(22, 17, 4, 3, P.C_SKIN_SH)
            RO(18, 8 + head_y, 12, 10, P.C_SKIN)
            R(18, 15 + head_y, 12, 3, P.C_SKIN_SH)
            R(20, 17 + head_y, 8, 1, P.C_SKIN_SH)
            if anim_name in ("hurt", "death"):
                R(20, 12 + head_y, 3, 1, P.C_OUTLINE)
                R(25, 12 + head_y, 3, 1, P.C_OUTLINE)
            else:
                R(20, 11 + head_y, 3, 1, P.C_HAIR_DARK)
                R(25, 11 + head_y, 3, 1, P.C_HAIR_DARK)
                R(20, 12 + head_y, 3, 2, P.C_OUTLINE)
                R(25, 12 + head_y, 3, 2, P.C_OUTLINE)
                R(21, 12 + head_y, 1, 1, P.C_BLADE_HI)
                R(26, 12 + head_y, 1, 1, P.C_BLADE_HI)
            R(23, 15 + head_y, 2, 1, P.C_SKIN_SH)
            P._draw_pixel_hair(R, RO, head_y, flip_left, anim_name, hair_wave)
            P._draw_pixel_sword_arm(R, RO, point, line, sword_angle,
                                    sword_extend, arm_forward, anim_name,
                                    show_charge)

            if show_charge:
                cx0, cy0 = point(24, 35)
                for i in range(6):
                    a = hair_wave * 3.0 + i * math.tau / 6.0
                    rr = 20.0 + math.sin(hair_wave * 5.0) * 4.0
                    P._rect(surface, (*P.C_WIND_CORE, 210),
                             (cx0 + math.cos(a) * rr - 2,
                              cy0 + math.sin(a) * rr * .4 - 2, 4, 4))

        @staticmethod
        def draw_kaizen_sprite(surface, origin, flip_left, anim_name,
                               frame_idx, tint=(255, 255, 255, 255),
                               attack_combo=0, hair_wave=0.0):
            """Public V1 sprite entry point matching the Godot function."""
            return KaizenV1Renderer._draw_kaizen_sprite(
                surface, origin, flip_left, anim_name, frame_idx, tint,
                attack_combo=attack_combo, hair_wave=hair_wave)

        @staticmethod
        def _draw_kaizen_elite(surface, cx, cy, facing, phase, action,
                               attack_progress=0.0, detail=False, gale=False,
                               storm=False, tint=(255, 255, 255, 255),
                               attack_combo=0):
            """Render one V1 pixel-art frame.

            ``detail`` is the portrait LOD flag.  It adds a few crisp
            clusters without changing the arena silhouette.
            """
            frame = 0
            if action == "idle":
                frame = int(abs(math.sin(float(phase) * 4.0)) > .45)
            elif action == "walk":
                frame = int(float(phase) * 6.0) % 6
            elif action == "attack":
                frame = min(4, max(0, int(float(attack_progress) * 5.0)))
            else:
                frame_counts = {"dash": 4, "windwall": 5, "sweep": 5,
                                "tornado": 7, "hurt": 3, "death": 5}
                frame = int(float(phase) * 8.0) % frame_counts.get(action, 4)
            P = KaizenV1Renderer
            P._draw_kaizen_sprite(
                surface, (cx, cy), facing < 0, action, frame, tint,
                attack_combo=attack_combo,
                hair_wave=float(phase) * 1.7)
            # A few V1 highlight clusters are always present so the
            # blue-samurai material ramps survive the arena downscale.
            f = -1 if facing < 0 else 1
            P._rect(surface, (*P.C_CLOTH_HI, 225),
                    (cx + f * 16, cy - 14, 2, 1))
            if action == "attack":
                # Preserve the five source frames while adding a tiny
                # deterministic sub-frame glint.  This keeps the cached
                # attack readable at 30 Hz and closes at progress 1.0.
                micro = int(max(0.0, min(0.999999, float(attack_progress))) * 9.0)
                P._rect(surface, (*P.C_WIND_CORE, 220),
                        (cx + f * (44 + micro), cy - 18 - (micro % 2), 2, 2))
            if gale or storm:
                P._aaline(surface, (*P.C_WIND, 145 if gale else 205),
                          (cx - f * 18, cy - 28), (cx + f * 24, cy - 37), 1)
                P._spark_star(surface, cx + f * 22, cy - 38, 4,
                              P.C_WIND_CORE, 180 if gale else 235, 4,
                              rot=float(phase))
            # Portrait LOD: source-inspired crisp pixel clusters.
            if detail and action != "death":
                y = cy - 31
                P._rect(surface, (*P.C_CLOTH_HI, 245),
                        (cx + f * 5 - 1, y, 2, 1))
                P._rect(surface, (*P.C_BLADE_HI, 235),
                        (cx + f * 9, y + 4, 1, 1))
                P._rect(surface, (*P.C_HAIR_LIGHT, 230),
                        (cx - f * 22, cy - 43, 2, 2))

        @staticmethod
        def _draw_kaizen_body(surface, cx, cy, facing, phase, action,
                              attack_progress=0.0, detail=False, gale=False,
                              storm=False):
            combo = int(getattr(getattr(KaizenV1Renderer, "_DRAW_HERO", None),
                                "_kz_combo", 0) or 0)
            KaizenV1Renderer._draw_kaizen_elite(
                surface, cx, cy, facing, phase, action, attack_progress,
                detail, gale, storm, attack_combo=combo)

        # ------------------------------------------------------------------
        # Ambient and skill effects translated from the supplied script.
        # These are fallback canvas effects; the existing live layer takes
        # over trail/projectile motion when the hero is in the arena cache.
        # ------------------------------------------------------------------
        @staticmethod
        def _draw_shadow(surface, x, y):
            P = KaizenV1Renderer
            pygame.draw.ellipse(surface, (*P.C_OUTLINE, 110),
                                pygame.Rect(int(x - 48), int(y - 8), 96, 15))
            pygame.draw.ellipse(surface, (*P.C_WIND, 42),
                                pygame.Rect(int(x - 34), int(y - 5), 68, 8))

        @staticmethod
        def _draw_swordsman_rim_light(surface, x, y, phase):
            P = KaizenV1Renderer
            alpha = int(30 + 22 * (.5 + .5 * math.sin(phase)))
            pygame.draw.ellipse(surface, (*P.C_WIND, alpha),
                                pygame.Rect(int(x - 30), int(y - 44), 60, 92), 2)

        @staticmethod
        def _draw_wind_aura(surface, x, y, phase):
            P = KaizenV1Renderer
            for i in range(3):
                r = 43 + i * 8 + int(math.sin(phase * 1.5 + i) * 3)
                P._dashed_ring(surface, x, y + 8, r, P.C_WIND, 34 - i * 7,
                               phase * .4 + i, dashes=10, width=1, squash=.35)

        @staticmethod
        def _draw_storm_aura(surface, x, y, phase):
            P = KaizenV1Renderer
            P._draw_wind_aura(surface, x, y, phase * 1.7)
            for i in range(6):
                a = phase * 1.8 + i * math.tau / 6
                P._spark_star(surface, x + math.cos(a) * 38,
                              y + 5 + math.sin(a) * 12, 5, P.C_WIND_CORE,
                              125, 4, rot=a)

        @staticmethod
        def _draw_wind_platform(surface, x, y, phase, skill):
            P = KaizenV1Renderer
            P._dashed_ring(surface, x, y, 40, P.C_WIND, 105, phase * .3,
                           dashes=14, width=2, squash=.27)
            P._dashed_ring(surface, x, y, 63, P.C_WIND, 58, -phase * .2,
                           dashes=10, width=1, squash=.2)
            for i in range(4):
                a = phase * .15 + i * math.pi / 2
                P._spark_star(surface, x + math.cos(a) * 52,
                              y + math.sin(a) * 14, 3, P.C_WIND_CORE, 170,
                              4, rot=a)

        @staticmethod
        def _draw_floating_wind(surface, cx, cy, phase, trail=False,
                                facing=1, intense=False, gale=False):
            P = KaizenV1Renderer
            count = 5 if intense else 3
            for i in range(count):
                t = (phase * (.45 if not intense else .75) + i * .23) % 1.0
                sx = cx - facing * (20 + i * 12) + math.sin(phase + i) * 4
                sy = cy + 9 - t * 30
                alpha = int(165 * (1.0 - t))
                P._aaline(surface, (*P.C_WIND, alpha), (sx, sy),
                          (sx + facing * 8, sy - 4), 2)
                if i % 2 == 0:
                    P._spark_star(surface, sx, sy, 3, P.C_WIND_CORE,
                                  alpha, 4, rot=phase + i)
            if trail:
                for i in range(4):
                    P._aaline(surface, (*P.C_WIND, 100 - i * 20),
                              (cx - facing * (16 + i * 10), cy + i),
                              (cx - facing * (26 + i * 12), cy + i), 1)
            if gale:
                P._draw_wind_aura(surface, cx, cy, phase)

        @staticmethod
        def _draw_dash_ground(surface, boss, x, y, timer, phase):
            P = KaizenV1Renderer
            progress = P._skill_progress(boss, "q", timer)
            P._dashed_ring(surface, x, y + 7, 24 + int(progress * 34), P.C_WIND,
                           150, phase, dashes=12, width=2, squash=.3)

        @staticmethod
        def _draw_dash_effect(surface, boss, x, y, timer, phase):
            P = KaizenV1Renderer
            f = getattr(boss, "direction", 1)
            for i in range(5):
                P._aaline(surface, (*P.C_WIND, 125 - i * 18),
                          (x - f * (12 + i * 11), y + 5 + i * 2),
                          (x - f * (34 + i * 14), y + i * 3), 2)
            P._spark_star(surface, x + f * 34, y - 4, 9, P.C_WIND_CORE,
                          190, 4, rot=phase)

        @staticmethod
        def _draw_wind_wall(surface, boss, x, y, timer, phase):
            P = KaizenV1Renderer
            progress = P._skill_progress(boss, "w", timer)
            f = getattr(boss, "direction", 1)
            px = x + f * 80
            alpha = int(220 * min(1.0, progress * 3.0))
            for h in range(-3, 4):
                yy = y + h * 12
                radius = 38 * (1.0 - abs(h) * .11)
                P._dashed_ring(surface, px, yy, radius, P.C_WIND, alpha,
                               phase + h * .4, dashes=8, width=2, squash=.32)
            P._aaline(surface, (*P.C_WIND_CORE, alpha),
                      (px, y - 42), (px, y + 42), 3)

        @staticmethod
        def _draw_sweep_ground(surface, boss, x, y, timer, phase):
            P = KaizenV1Renderer
            radius = P._ring_r(boss, 100, surface)
            # The source Godot pulse is a true circular world-space pulse;
            # do not squash the radius when the hero sprite is normalized.
            P._aoe_marks(surface, x, y + 30, radius, P.C_WIND, 185,
                         phase, squash=1.0, ticks=16, tick_len=8)

        @staticmethod
        def _draw_sweep_effect(surface, boss, x, y, timer, phase):
            P = KaizenV1Renderer
            progress = P._skill_progress(boss, "e", timer)
            f = getattr(boss, "direction", 1)
            angle = 0.0 if f > 0 else math.pi
            P._filled_crescent(surface, x + f * 22, y, angle,
                               48 + progress * 28, 30 + progress * 20,
                               1.0, (*P.C_WIND, 150), segments=16)
            P._aaline(surface, (*P.C_WIND_CORE, 220),
                      (x + f * 5, y + 4), (x + f * 75, y - 12), 2)

        @staticmethod
        def _draw_tornado_ground(surface, boss, x, y, timer, phase):
            P = KaizenV1Renderer
            radius = P._ring_r(boss, 150, surface)
            P._aoe_marks(surface, x, y + 30, radius, P.C_WIND, 175,
                         phase * 1.4, squash=1.0, ticks=20, tick_len=10)

        @staticmethod
        def _draw_tornado(surface, boss, x, y, timer, phase):
            P = KaizenV1Renderer
            progress = P._skill_progress(boss, "r", timer)
            f = getattr(boss, "direction", 1)
            pos = (x + f * 120, y)
            height = 70.0 * min(1.0, progress * 1.8)
            radius = 8.0 + 38.0 * min(1.0, progress * 1.5)
            P._aacircle(surface, (*P.C_WIND, 72), (pos[0], pos[1] + 5),
                        radius * 1.2)
            P._dashed_ring(surface, pos[0], pos[1] + 5, radius * 1.2,
                           P.C_WIND_CORE, 190, phase, dashes=24, width=2, squash=.35)
            for i in range(8):
                ratio = i / 8.0
                yy = pos[1] - height * ratio
                rr = radius * (.4 + ratio * .7)
                P._dashed_ring(surface, pos[0], yy, rr, P.C_WIND,
                               int(190 * (1 - ratio * .3)),
                               phase * 2 + ratio * 3, dashes=12, width=2,
                               squash=.35)
            P._spark_star(surface, pos[0], pos[1] - height, 5,
                          P.C_WIND_CORE, 230, 4, rot=phase)

        @staticmethod
        def _draw_katana_swing_trail(surface, cx, cy, f, phase, ap):
            P = KaizenV1Renderer
            if ap <= 0.15 or ap >= .92:
                return
            for i in range(6):
                p = max(0.0, ap - i * .055)
                tip = P._katana_tip_local(phase, "attack", p)
                P._aacircle(surface, (*P.C_WIND, 130 - i * 18),
                             (cx + tip[0] * f, cy + tip[1]), max(1, 5 - i // 2))
            tip = P._katana_tip_local(phase, "attack", ap)
            P._spark_star(surface, cx + tip[0] * f, cy + tip[1], 8,
                          P.C_WIND_CORE, 180, 4, rot=phase)

        # ------------------------------------------------------------------
        # Fallback projectile and the draw orchestrator.
        # ------------------------------------------------------------------
        class WindSlashProjectile:
            def __init__(self, sx, sy, tx, ty, speed=8.0,
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
                self.trail.append((self.x, self.y, self.angle))
                if len(self.trail) > 14:
                    self.trail.pop(0)
                self.x += dx / dist * self.speed
                self.y += dy / dist * self.speed

            def draw(self, surface, phase):
                P = KaizenV1Renderer
                if not self.alive:
                    t = max(0.0, 1.0 - self.dead_frames / 8.0)
                    if t > 0:
                        P._spark_star(surface, self.x, self.y, 18 * t,
                                      P.C_WIND_CORE, int(220 * t), 8,
                                      rot=phase)
                    return
                for i, (tx, ty, ang) in enumerate(self.trail):
                    a = int(30 + 130 * i / max(1, len(self.trail) - 1))
                    P._filled_crescent(surface, tx, ty, ang, 10, 4,
                                       .9, (*P.C_WIND, a), 8)
                P._filled_crescent(surface, self.x, self.y, self.angle,
                                   22, 9, 1.1, (*P.C_WIND, 210), 12)
                P._filled_crescent(surface, self.x, self.y, self.angle,
                                   16, 6, 1.0, (*P.C_WIND_CORE, 235), 12)

        @staticmethod
        def _manage_projectiles(boss, surface, phase):
            if getattr(boss, "_skip_renderer_projectiles", False):
                return
            items = getattr(boss, "_kz_projectiles", None)
            if items is None:
                boss._kz_projectiles = []
                items = boss._kz_projectiles
            for proj in items:
                proj.update()
                proj.draw(surface, phase)
            boss._kz_projectiles[:] = [p for p in items
                                       if p.alive or p.dead_frames < 8]

        @staticmethod
        def _spawn_wind_slash(boss, x, y):
            if getattr(boss, "_skip_renderer_projectiles", False):
                return
            items = getattr(boss, "_kz_projectiles", None)
            if items is None:
                items = []
                boss._kz_projectiles = items
            tx, ty = KaizenV1Renderer._target_position(boss, x, y)
            f = getattr(boss, "direction", 1)
            proj = KaizenV1Renderer.WindSlashProjectile(
                x + 24 * f, y - 8, tx, ty, speed=8.0,
                target=getattr(boss, "target", None), team=getattr(boss, "team", None))
            proj.source, proj.cx, proj.cy = boss, x, y
            items.append(proj)

        @staticmethod
        def _draw_kaizen_idle(surface, boss, x, y):
            KaizenV1Renderer._DRAW_HERO = boss
            phase = float(getattr(boss, "pulse", 0.0))
            if not getattr(boss, "_portrait_hd", False):
                KaizenV1Renderer._draw_shadow(surface, x, y + 62)
                KaizenV1Renderer._draw_floating_wind(surface, x, y + 46, phase,
                                                     gale=getattr(boss, "active_skill", None) == "w")
            KaizenV1Renderer._draw_kaizen_body(
                surface, x, y, getattr(boss, "direction", 1), phase, "idle",
                detail=bool(getattr(boss, "_portrait_hd", False)))

        @staticmethod
        def _draw_kaizen_walk(surface, boss, x, y):
            KaizenV1Renderer._DRAW_HERO = boss
            phase = float(getattr(boss, "pulse", 0.0))
            f = getattr(boss, "direction", 1)
            if not getattr(boss, "_portrait_hd", False):
                KaizenV1Renderer._draw_shadow(surface, x, y + 62)
                KaizenV1Renderer._draw_floating_wind(surface, x, y + 46, phase,
                                                     trail=True, facing=f)
            KaizenV1Renderer._draw_kaizen_body(
                surface, x, y, f, phase, "walk",
                detail=bool(getattr(boss, "_portrait_hd", False)))

        @staticmethod
        def _draw_kaizen_attack(surface, boss, x, y):
            KaizenV1Renderer._DRAW_HERO = boss
            phase = float(getattr(boss, "pulse", 0.0))
            progress = max(0.0, min(1.0, float(getattr(boss, "_kz_attack_progress", 0.0))))
            f = getattr(boss, "direction", 1)
            KaizenV1Renderer._draw_kaizen_body(
                surface, x + int(math.sin(progress * math.pi) * 3) * f, y,
                f, phase, "attack", progress,
                detail=bool(getattr(boss, "_portrait_hd", False)))
            if not getattr(boss, "_portrait_hd", False) and not KaizenV1Renderer._FX_LIVE.v:
                KaizenV1Renderer._draw_katana_swing_trail(surface, x, y, f, phase, progress)

        @staticmethod
        def _draw_kaizen_hurt(surface, boss, x, y):
            KaizenV1Renderer._DRAW_HERO = boss
            phase = float(getattr(boss, "pulse", 0.0))
            KaizenV1Renderer._draw_kaizen_body(
                surface, x, y, getattr(boss, "direction", 1), phase, "hurt",
                detail=bool(getattr(boss, "_portrait_hd", False)))

        @staticmethod
        def draw_kaizen(surface, boss, x, y):
            """Entry point used by both the hero and boss render paths."""
            P = KaizenV1Renderer
            P._DRAW_HERO = boss
            phase = float(getattr(boss, "pulse", 0.0))
            P._detect_moving(boss)
            P._update_attack_anim(boss)
            portrait = bool(getattr(boss, "_portrait_hd", False))

            if not portrait:
                try:
                    mod = P._live_module()
                    if mod is not None:
                        mod.attach(boss)
                except Exception:
                    pass
            try:
                P._FX_LIVE.v = (not portrait) and P._fx_live_owned(boss)
            except Exception:
                P._FX_LIVE.v = False

            active_skill = getattr(boss, "active_skill", None)
            timer = int(getattr(boss, "active_skill_timer", 0) or 0)
            attacking = bool(getattr(boss, "_kz_attack_active", False))
            alive = bool(getattr(boss, "alive", True))

            # Skill ground telegraphs remain canvas-owned, like the old
            # renderer; their radius is converted from world pixels.
            if not portrait:
                P._draw_swordsman_rim_light(surface, x, y - 12, phase)
                if active_skill == "r":
                    P._draw_storm_aura(surface, x, y, phase)
                else:
                    P._draw_wind_aura(surface, x, y, phase)
                P._draw_wind_platform(surface, x, y + 58, phase, active_skill)
                if active_skill == "q":
                    P._draw_dash_ground(surface, boss, x, y, timer, phase)
                elif active_skill == "e":
                    P._draw_sweep_ground(surface, boss, x, y, timer, phase)
                elif active_skill == "r":
                    P._draw_tornado_ground(surface, boss, x, y, timer, phase)

            if not alive:
                P._draw_kaizen_body(surface, x, y, getattr(boss, "direction", 1),
                                    phase, "death", detail=portrait)
            elif attacking:
                P._draw_kaizen_attack(surface, boss, x, y)
            elif active_skill == "q":
                P._draw_kaizen_body(surface, x, y, getattr(boss, "direction", 1),
                                    phase, "dash", detail=portrait)
            elif active_skill == "w":
                P._draw_kaizen_body(surface, x, y, getattr(boss, "direction", 1),
                                    phase, "windwall", detail=portrait)
            elif active_skill == "e":
                P._draw_kaizen_body(surface, x, y, getattr(boss, "direction", 1),
                                    phase, "sweep", detail=portrait)
            elif active_skill == "r":
                P._draw_kaizen_body(surface, x, y, getattr(boss, "direction", 1),
                                    phase, "tornado", detail=portrait)
            elif getattr(boss, "_kz_hurt_timer", 0) > 0:
                P._draw_kaizen_hurt(surface, boss, x, y)
            elif getattr(boss, "_moving_cached", False):
                P._draw_kaizen_walk(surface, boss, x, y)
            else:
                P._draw_kaizen_idle(surface, boss, x, y)

            if not portrait:
                P._manage_projectiles(boss, surface, phase)
                if active_skill == "q":
                    P._draw_dash_effect(surface, boss, x, y, timer, phase)
                elif active_skill == "w":
                    P._draw_wind_wall(surface, boss, x, y, timer, phase)
                elif active_skill == "e":
                    P._draw_sweep_effect(surface, boss, x, y, timer, phase)
                elif active_skill == "r":
                    P._draw_tornado(surface, boss, x, y, timer, phase)

            if P.DEBUG_CHARACTER:
                P._draw_debug(surface, boss, x, y)

        @staticmethod
        def draw_boss(surface, boss, x, y):
            KaizenV1Renderer.draw_kaizen(surface, boss, x, y)

        @staticmethod
        def _draw_debug(surface, boss, x, y):
            P = KaizenV1Renderer
            pygame.draw.rect(surface, (90, 220, 255),
                             pygame.Rect(int(x - 50), int(y - 90), 100, 150), 1)
            prog = float(getattr(boss, "_kz_attack_progress", 0.0))
            pygame.draw.rect(surface, P.C_OUTLINE,
                             pygame.Rect(int(x - 40), int(y - 105), 80, 5))
            pygame.draw.rect(surface, P.C_CLOTH_HI,
                             pygame.Rect(int(x - 40), int(y - 105), int(80 * prog), 5))

        # The live FX module asks for these hooks when the renderer is
        # available, so use the current namespace's lazy import contract.
        @staticmethod
        def _live_module():
            if KaizenV1Renderer._LIVE_MOD is None:
                try:
                    from heroes import kaizen_fx as mod
                    KaizenV1Renderer._LIVE_MOD = (
                        mod if getattr(mod, "KAIZEN_FX_ENABLED", True) else False)
                except Exception:
                    KaizenV1Renderer._LIVE_MOD = False
            return KaizenV1Renderer._LIVE_MOD or None

        @staticmethod
        def _fx_live_owned(hero):
            try:
                mod = KaizenV1Renderer._live_module()
                return bool(mod is not None and mod.owns(hero))
            except Exception:
                return False

    return KaizenV1Renderer
