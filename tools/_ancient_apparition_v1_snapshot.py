#!/usr/bin/env python3
"""SNAPSHOT renderer ancient_apparition v1 (sebelum upgrade Pixel Masterwork v2).

Dibuat otomatis sebelum rewrite `_NS_ancient_apparition` di bosses/level3.py.
Dipakai tools/_audit_ancient_apparition_v2.py untuk lembar before/after -
jangan diedit manual; kalau perlu regenerasi, ambil dari git history.
"""
import math
import pygame

try:
    import lighting as _lighting
except Exception:  # pragma: no cover
    _lighting = None

def _composite_boss_body(surface, ns, raw, cx, cy, facing, phase, action,
                         attack_progress=0, rim_add=(150, 225, 255), bsize=200):
    if getattr(ns, "_body_buf", None) is None:
        ns._body_buf = pygame.Surface((bsize, bsize), pygame.SRCALPHA)
    buf = ns._body_buf
    buf.fill((0, 0, 0, 0))
    raw(buf, bsize // 2, bsize // 2, facing, phase, action, attack_progress)
    used = buf.get_bounding_rect(min_alpha=1)
    if used.width <= 2 or used.height <= 2:
        return
    cropped = buf.subsurface(used).copy()
    m = pygame.mask.from_surface(cropped, 40)
    ol = m.to_surface(setcolor=(0, 0, 0, 240), unsetcolor=(0, 0, 0, 0))
    bw, bh = cropped.get_size()
    framed = pygame.Surface((bw + 4, bh + 4), pygame.SRCALPHA)
    for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        framed.blit(ol, (2 + ox, 2 + oy))
    framed.blit(cropped, (2, 2))
    if _lighting is not None and hasattr(_lighting, "apply_to_rig"):
        try:
            _lighting.apply_to_rig(framed, rim_add=rim_add, shade_mul=190)
        except Exception:
            pass
    bx = cx - bsize // 2 + used.left - 2
    by = cy - bsize // 2 + used.top - 2
    surface.blit(framed, (bx, by))

class _NS_ancient_apparition:
    """Namespace ancient_apparition - isi asli tidak diubah."""

    # ── ORIGINAL-MAX cache (piksel-identik, dibangun lazy) ──────────
    _body_buf = None
    _flash_buf = None
    _record_shadow = None
    _shadow_cache = None
    _aura_cache = None
    _ground_cache = None
    _mist_cache = None

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Ice Palette
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Ice body - deep blue to bright white
        "ice_darkest":    (8,   20,  55),
        "ice_dark":       (22,  55, 115),
        "ice_mid":        (55, 110, 180),
        "ice_light":      (115, 175, 230),
        "ice_bright":     (170, 215, 250),
        "ice_hot":        (220, 240, 255),
        "ice_white":      (245, 252, 255),
        "ice_pure":       (255, 255, 255),

        # Cyan tints
        "cyan_dark":      (15,  75, 110),
        "cyan_mid":       (55, 155, 195),
        "cyan_light":     (130, 215, 240),
        "cyan_bright":    (200, 245, 255),

        # Deep shadow (inside ice)
        "shadow_ice":     (12,  25,  55),

        # Face glow
        "face_dark":      (30,  70, 130),
        "face_mid":       (95, 175, 230),
        "face_bright":    (180, 230, 255),
        "face_hot":       (230, 248, 255),

        # Frost mist
        "frost_dark":     (30,  75, 130),
        "frost_mid":      (95, 165, 220),
        "frost_light":    (170, 220, 250),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (2,   5,  12),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_ancient_apparition._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_ancient_apparition.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_ancient_apparition._clamp(color)
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
        color = _NS_ancient_apparition._clamp(color)
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
        color = _NS_ancient_apparition._clamp(color)
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
        color = _NS_ancient_apparition._clamp(color)
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
    # Ice / Snowflake helpers
    # ---------------------------------------------------------------------------
    def _draw_snowflake(surface, cx, cy, size=3, alpha=255, rotate=0):
        """Draw a snowflake - cross with small arms."""
        for i in range(6):
            angle = rotate + i * math.pi / 3
            ex = cx + int(math.cos(angle) * size)
            ey = cy + int(math.sin(angle) * size)
            _NS_ancient_apparition._aaline(surface, (*_NS_ancient_apparition.PALETTE["ice_hot"], alpha), (cx, cy), (ex, ey), 1)
            # Little tick marks
            tick_angle_1 = angle + math.pi / 2
            tick_angle_2 = angle - math.pi / 2
            mx = cx + int(math.cos(angle) * (size - 1))
            my = cy + int(math.sin(angle) * (size - 1))
            tx1 = mx + int(math.cos(tick_angle_1) * 1)
            ty1 = my + int(math.sin(tick_angle_1) * 1)
            tx2 = mx + int(math.cos(tick_angle_2) * 1)
            ty2 = my + int(math.sin(tick_angle_2) * 1)
            _NS_ancient_apparition._aaline(surface, (*_NS_ancient_apparition.PALETTE["ice_bright"], alpha), (mx, my), (tx1, ty1), 1)
            _NS_ancient_apparition._aaline(surface, (*_NS_ancient_apparition.PALETTE["ice_bright"], alpha), (mx, my), (tx2, ty2), 1)
        _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_pure"], alpha), (cx, cy), 1)


    def _draw_ice_shard(surface, points, colors_layers=None):
        """Draw a layered ice shard from a set of polygon points."""
        if colors_layers is None:
            colors_layers = [
                _NS_ancient_apparition.PALETTE["ice_darkest"],
                _NS_ancient_apparition.PALETTE["ice_dark"],
                _NS_ancient_apparition.PALETTE["ice_mid"],
                _NS_ancient_apparition.PALETTE["ice_light"],
                _NS_ancient_apparition.PALETTE["ice_bright"],
            ]
        for i, color in enumerate(colors_layers):
            # Shrink polygon slightly per layer
            cx = sum(p[0] for p in points) / len(points)
            cy = sum(p[1] for p in points) / len(points)
            shrink = i * 0.15
            inner = [(p[0] + (cx - p[0]) * shrink,
                      p[1] + (cy - p[1]) * shrink) for p in points]
            _NS_ancient_apparition._poly(surface, color, inner)


    def _draw_frost_crystal_spike(surface, cx, base_y, tip_y, width=4, alpha=255,
                                    phase=0):
        """Draw a single ice spike growing upward."""
        height = base_y - tip_y
        if height <= 0:
            return

        # Shadow
        _NS_ancient_apparition._poly(surface, (*_NS_ancient_apparition.PALETTE["shadow_deep"], alpha), [
            (cx - width + 1, base_y + 1),
            (cx + width + 1, base_y + 1),
            (cx + 1, tip_y + 1),
        ])

        # Outer dark
        _NS_ancient_apparition._poly(surface, (*_NS_ancient_apparition.PALETTE["ice_darkest"], alpha), [
            (cx - width, base_y),
            (cx + width, base_y),
            (cx, tip_y),
        ])
        # Layers getting brighter
        for i, color_key in enumerate(["ice_dark", "ice_mid", "ice_light", "ice_bright"]):
            shrink = (i + 1) * 0.15
            w = int(width * (1 - shrink))
            _NS_ancient_apparition._poly(surface, (*_NS_ancient_apparition.PALETTE[color_key], alpha), [
                (cx - w, base_y - 1),
                (cx + w, base_y - 1),
                (cx, tip_y + int(height * shrink * 0.2)),
            ])
        # White edge line
        _NS_ancient_apparition._aaline(surface, (*_NS_ancient_apparition.PALETTE["ice_hot"], alpha),
                (cx, base_y - 2), (cx, tip_y + 2), 1)
        _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_pure"], alpha), (cx, tip_y + 1), 1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM
    # ---------------------------------------------------------------------------
    class IceShardProjectile:
        """Cold Touch - small fast ice shard."""
        def __init__(self, sx, sy, tx, ty, speed=7.5):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.trail = []
            # angle for shard rotation
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
            if len(self.trail) > 10:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(50 + i * 15)
                r = max(1, 4 - (len(self.trail) - i))
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_dark"], alpha), (tx, ty), r + 2)
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_light"], alpha), (tx, ty), r)
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_hot"], alpha // 2), (tx, ty), max(1, r - 1))

            if self.alive:
                px, py = int(self.x), int(self.y)
                # Shard shape (diamond)
                dx = math.cos(self.angle)
                dy = math.sin(self.angle)
                perp_x = -dy
                perp_y = dx

                shard = [
                    (px + int(dx * 8), py + int(dy * 8)),
                    (px + int(perp_x * 4), py + int(perp_y * 4)),
                    (px - int(dx * 5), py - int(dy * 5)),
                    (px - int(perp_x * 4), py - int(perp_y * 4)),
                ]
                _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["shadow_deep"],
                      [(p[0] + 1, p[1] + 1) for p in shard])
                _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_darkest"], shard)
                _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_dark"], [
                    (px + int(dx * 7), py + int(dy * 7)),
                    (px + int(perp_x * 3), py + int(perp_y * 3)),
                    (px - int(dx * 4), py - int(dy * 4)),
                    (px - int(perp_x * 3), py - int(perp_y * 3)),
                ])
                _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_mid"], [
                    (px + int(dx * 6), py + int(dy * 6)),
                    (px + int(perp_x * 2), py + int(perp_y * 2)),
                    (px - int(dx * 3), py - int(dy * 3)),
                    (px - int(perp_x * 2), py - int(perp_y * 2)),
                ])
                _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_bright"], [
                    (px + int(dx * 5), py + int(dy * 5)),
                    (px + int(perp_x), py + int(perp_y)),
                    (px - int(dx * 2), py - int(dy * 2)),
                    (px - int(perp_x), py - int(perp_y)),
                ])
                _NS_ancient_apparition._aaline(surface, _NS_ancient_apparition.PALETTE["ice_pure"],
                        (px + int(dx * 6), py + int(dy * 6)),
                        (px - int(dx * 3), py - int(dy * 3)), 1)

                # Glow
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_light"], 120), (px, py), 10)
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_bright"], 80), (px, py), 6)


    class IceBoltProjectile:
        """Ice Blast (E) - larger, slower shard bolt."""
        def __init__(self, sx, sy, tx, ty, speed=5.5):
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
            if dist < self.speed + 5:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 14:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            # Long streaking trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 15)
                r = max(1, 6 - (len(self.trail) - i))
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_dark"], alpha), (tx, ty), r + 2)
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_mid"], alpha), (tx, ty), r)
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_bright"], alpha // 2), (tx, ty), max(1, r - 1))

            if self.alive:
                px, py = int(self.x), int(self.y)
                dx = math.cos(self.angle)
                dy = math.sin(self.angle)
                perp_x = -dy
                perp_y = dx

                # Large shard bolt
                shard = [
                    (px + int(dx * 14), py + int(dy * 14)),
                    (px + int(perp_x * 6), py + int(perp_y * 6)),
                    (px - int(dx * 8), py - int(dy * 8)),
                    (px - int(perp_x * 6), py - int(perp_y * 6)),
                ]
                _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["shadow_deep"],
                      [(p[0] + 2, p[1] + 2) for p in shard])
                _NS_ancient_apparition._draw_ice_shard(surface, shard)
                _NS_ancient_apparition._aaline(surface, _NS_ancient_apparition.PALETTE["ice_pure"],
                        (px + int(dx * 12), py + int(dy * 12)),
                        (px - int(dx * 6), py - int(dy * 6)), 1)

                # Bright glow
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_light"], 140), (px, py), 16)
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_bright"], 100), (px, py), 10)

                # Snowflake particles around
                for i in range(3):
                    angle = phase * 3 + i * math.pi * 2 / 3
                    sx = px + int(math.cos(angle) * 12)
                    sy = py + int(math.sin(angle) * 12)
                    _NS_ancient_apparition._draw_snowflake(surface, sx, sy, 2, 200, rotate=phase)


    class FrostBeam:
        """Chilling Touch (W) - continuous beam."""
        def __init__(self, sx, sy, tx, ty, life=40):
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
            elif t < 0.7:
                alpha_scale = 1.0
            else:
                alpha_scale = 1 - (t - 0.7) / 0.3

            dx = self.tx - self.sx
            dy = self.ty - self.sy
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 1:
                return
            dir_x = dx / dist
            dir_y = dy / dist
            perp_x = -dir_y
            perp_y = dir_x

            # Draw beam as many layered particles
            for i in range(int(dist / 4)):
                t_pos = i / max(1, int(dist / 4))
                base_x = self.sx + dir_x * dist * t_pos
                base_y = self.sy + dir_y * dist * t_pos

                # Sinusoidal offset (chilling wave)
                wave = math.sin(phase * 6 + t_pos * 15) * 4
                fx = int(base_x + perp_x * wave)
                fy = int(base_y + perp_y * wave)

                alpha = int(200 * alpha_scale)
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_dark"], alpha), (fx, fy), 6)
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_mid"], alpha), (fx, fy), 4)
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_bright"], alpha), (fx, fy), 3)
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_hot"], alpha), (fx, fy), 2)
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_pure"], alpha), (fx, fy), 1)

            # Snowflake sparkles along beam
            for i in range(8):
                t_pos = (phase * 0.3 + i * 0.13) % 1.0
                sx = int(self.sx + dir_x * dist * t_pos)
                sy = int(self.sy + dir_y * dist * t_pos)
                _NS_ancient_apparition._draw_snowflake(surface, sx + int(perp_x * 6), sy + int(perp_y * 6),
                                 2, int(230 * alpha_scale), rotate=phase * 2 + i)


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_aa_last_x"):
            boss._aa_last_x = boss.x
            boss._aa_last_y = boss.y
            return False
        dx = abs(boss.x - boss._aa_last_x)
        dy = abs(boss.y - boss._aa_last_y)
        boss._aa_last_x = boss.x
        boss._aa_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_aa_prev_timer", 0))
        active = bool(getattr(boss, "_aa_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._aa_attack_active = True
            boss._aa_attack_frame = 0
            active = True
        elif active:
            boss._aa_attack_frame = int(getattr(boss, "_aa_attack_frame", 0)) + 1
            if boss._aa_attack_frame > cooldown:
                boss._aa_attack_active = False
                boss._aa_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._aa_attack_active = False
            boss._aa_attack_frame = 0
            active = False

        boss._aa_prev_timer = timer
        boss._aa_attack_progress = (
            min(1.0, getattr(boss, "_aa_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_aa_projectiles"):
            boss._aa_projectiles = []
        if not hasattr(boss, "_aa_beams"):
            boss._aa_beams = []

        for proj in boss._aa_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._aa_projectiles = [p for p in boss._aa_projectiles
                                 if p.alive or p.age < 5]

        for beam in boss._aa_beams:
            beam.update()
            beam.draw(surface, phase)
        boss._aa_beams = [b for b in boss._aa_beams if b.alive]


    def _spawn_ice_shard(boss, sx, sy, tx, ty):
        # Saat Ancient Apparition DIMAINKAN sebagai hero (class Hero),
        # basic attack-nya sudah menembakkan homing ice shard dari
        # sistem projectile Hero (Hero._do_attack -> _spawn_projectile,
        # digambar _draw_ice_shard_projectile di koordinat layar).
        # Shard internal renderer ini hidup di ruang canvas offscreen
        # yang ikut di-scale & sering ter-clip: dulu basic attack AA
        # yang dimainkan jadi tidak terlihat sama sekali, dan kalau
        # dibiarkan kini malah ada DUA shard. Flag
        # ``_aa_hero_basic_shard`` mematikannya untuk hero; versi TRUE
        # BOSS musuh (class Boss) tetap memakai shard internal ini.
        if getattr(boss, "_aa_hero_basic_shard", False):
            return
        if not hasattr(boss, "_aa_projectiles"):
            boss._aa_projectiles = []
        boss._aa_projectiles.append(_NS_ancient_apparition.IceShardProjectile(sx, sy, tx, ty))


    def _spawn_ice_bolt(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_aa_projectiles"):
            boss._aa_projectiles = []
        boss._aa_projectiles.append(_NS_ancient_apparition.IceBoltProjectile(sx, sy, tx, ty))


    def _spawn_frost_beam(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_aa_beams"):
            boss._aa_beams = []
        boss._aa_beams.append(_NS_ancient_apparition.FrostBeam(sx, sy, tx, ty, life=50))


    # ===================================================================
    # MAIN ENTRY
    # ===================================================================
    def draw_apparition(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_ancient_apparition._detect_moving(boss)
        _NS_ancient_apparition._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_aa_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # Background
        _NS_ancient_apparition._draw_frost_aura(surface, x, y, pulse, active_skill)
        _NS_ancient_apparition._draw_ground_frost(surface, x, y + 42, pulse, active_skill)

        # Skill ground effects
        if active_skill == "q":
            _NS_ancient_apparition._draw_ice_vortex_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_ancient_apparition._draw_cold_feet_ground(surface, boss, x, y, skill_timer, pulse)

        # Character
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        _tgt, _tx, _ty = surface, x, y
        if flash > 0:
            NS = _NS_ancient_apparition
            if NS._flash_buf is None:
                NS._flash_buf = pygame.Surface((220, 240), pygame.SRCALPHA)
            NS._flash_buf.fill((0, 0, 0, 0))
            NS._record_shadow = []
            _tgt, _tx, _ty = NS._flash_buf, 110, 120

        if attacking:
            _NS_ancient_apparition._draw_aa_attack(_tgt, boss, _tx, _ty)
        elif active_skill == "w":
            _NS_ancient_apparition._draw_aa_casting(_tgt, boss, _tx, _ty, "w")
        elif active_skill == "e":
            _NS_ancient_apparition._draw_aa_casting(_tgt, boss, _tx, _ty, "e")
        elif moving:
            _NS_ancient_apparition._draw_aa_walk(_tgt, boss, _tx, _ty)
        else:
            _NS_ancient_apparition._draw_aa_idle(_tgt, boss, _tx, _ty)

        if flash > 0:
            NS = _NS_ancient_apparition
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

        # Trigger projectiles for skills
        _NS_ancient_apparition._handle_skill_projectiles(boss, x, y, active_skill, skill_timer)

        # Projectiles
        _NS_ancient_apparition._manage_projectiles(boss, surface, pulse)

        # Foreground skill effects
        if active_skill == "q":
            _NS_ancient_apparition._draw_ice_vortex(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_ancient_apparition._draw_cold_feet_spikes(surface, boss, x, y, skill_timer, pulse)


    def _handle_skill_projectiles(boss, x, y, active_skill, timer):
        """Spawn projectiles at appropriate times."""
        tx, ty = _NS_ancient_apparition._target_position(boss, x, y)

        if active_skill == "e":
            duration = 50
            progress = max(0.0, min(1.0, 1 - timer / duration))
            if 0.35 < progress < 0.45 and not getattr(boss, "_aa_e_spawned", False):
                _NS_ancient_apparition._spawn_ice_bolt(boss, x + 25 * boss.direction, y - 5, tx, ty)
                boss._aa_e_spawned = True
            if progress > 0.7:
                boss._aa_e_spawned = False

        elif active_skill == "w":
            duration = 45
            progress = max(0.0, min(1.0, 1 - timer / duration))
            if 0.3 < progress < 0.4 and not getattr(boss, "_aa_w_spawned", False):
                _NS_ancient_apparition._spawn_frost_beam(boss, x + 25 * boss.direction, y - 5, tx, ty)
                boss._aa_w_spawned = True
            if progress > 0.7:
                boss._aa_w_spawned = False


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_aa_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_ancient_apparition._draw_shadow(surface, x, y + 52)
        _NS_ancient_apparition._draw_ice_wisps(surface, x, y + 38, boss.pulse)
        _NS_ancient_apparition._draw_aa_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_aa_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(abs(math.sin(phase * 1.3)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_ancient_apparition._draw_shadow(surface, x + sway, y + 52)
        _NS_ancient_apparition._draw_ice_wisps(surface, x + sway, y + 38, phase, trail=True,
                         facing=boss.direction)
        _NS_ancient_apparition._draw_aa_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_aa_attack(surface, boss, x, y):
        progress = getattr(boss, "_aa_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        recoil = int(math.sin(progress * math.pi) * 3) * -boss.direction

        # Spawn ice shard mid-attack
        if 0.35 < progress < 0.45 and not getattr(boss, "_aa_atk_spawned", False):
            tx, ty = _NS_ancient_apparition._target_position(boss, x, y)
            _NS_ancient_apparition._spawn_ice_shard(boss, x + 22 * boss.direction, y - 5, tx, ty)
            boss._aa_atk_spawned = True
        if progress < 0.1 or progress > 0.9:
            boss._aa_atk_spawned = False

        _NS_ancient_apparition._draw_shadow(surface, x + recoil, y + 52)
        _NS_ancient_apparition._draw_ice_wisps(surface, x + recoil, y + 38, boss.pulse, intense=True)
        _NS_ancient_apparition._draw_aa_body(surface, x + recoil, y, boss.direction, boss.pulse,
                      "attack", progress)
        _NS_ancient_apparition._draw_cast_flash(surface, x + recoil, y, boss.direction, progress)


    def _draw_aa_casting(surface, boss, x, y, skill_key):
        """Casting pose - arms raised, glowing intensity."""
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_ancient_apparition._draw_shadow(surface, x, y + 52)
        _NS_ancient_apparition._draw_ice_wisps(surface, x, y + 38, boss.pulse, intense=True)
        _NS_ancient_apparition._draw_aa_body(surface, x, y + bob, boss.direction, boss.pulse,
                      "cast_" + skill_key)


    # ===================================================================
    # BODY RENDERING - Ice crystalline entity
    # ===================================================================
    def _draw_aa_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Komposit ORIGINAL-MAX: buffer tetap + outline + lighting."""
        _composite_boss_body(
            surface, _NS_ancient_apparition, _NS_ancient_apparition._draw_aa_body_raw,
            cx, cy, facing, phase, action, attack_progress,
            rim_add=(150, 225, 255), bsize=200)

    def _masterwork_finish(surface, cx, cy, facing, phase, action,
                           attack_progress=0):
        """ORIGINAL-MAX detail pass: wajah true boss + emblem + rim kiri-atas."""
        P = _NS_ancient_apparition.PALETTE
        fy = cy - 26
        for side in (-1, 1):
            ex = cx + side * 3
            pygame.draw.circle(surface, P["shadow_deep"], (ex, fy - 1), 3)
            pygame.draw.circle(surface, P["face_hot"], (ex, fy - 1), 2)
            pygame.draw.circle(surface, P["ice_white"], (ex, fy - 2), 1)
            pygame.draw.circle(surface, P["face_bright"], (ex, fy - 1), 4)
        pygame.draw.rect(surface, P["shadow_deep"], (cx - 3, fy + 2, 6, 2))
        pygame.draw.rect(surface, P["face_mid"], (cx - 2, fy + 2, 4, 1))
        pygame.draw.circle(surface, P["cyan_dark"], (cx, cy - 7), 6)
        pygame.draw.circle(surface, P["cyan_bright"], (cx, cy - 7), 4)
        pygame.draw.circle(surface, P["ice_pure"], (cx, cy - 7), 3)
        pygame.draw.line(surface, P["shadow_deep"], (cx - 10, cy - 18), (cx + 10, cy - 18), 1)
        pygame.draw.line(surface, P["ice_darkest"], (cx - 15, cy - 2), (cx - 11, cy + 2), 1)
        pygame.draw.line(surface, P["ice_darkest"], (cx + 15, cy - 2), (cx + 11, cy + 2), 1)
        for xo, yo in ((-4, -44), (0, -48), (4, -44)):
            pygame.draw.circle(surface, P["ice_hot"], (cx + xo, cy + yo), 2)
        for side in (-1, 1):
            pygame.draw.circle(surface, P["ice_bright"], (cx + side * 14, cy - 24), 2)


    def _draw_aa_body_raw(surface, cx, cy, facing, phase, action,
                          attack_progress=0):
        """Ancient Apparition body - ice crystal humanoid."""
        is_casting = action.startswith("cast_")
        intensity = 1.3 if is_casting else 1.0

        # Lower ice shards (floating base) - drawn as icy skirt/tail
        _NS_ancient_apparition._draw_ice_skirt(surface, cx, cy + 8, phase, intensity)

        # Torso (crystalline shard cluster)
        _NS_ancient_apparition._draw_ice_torso(surface, cx, cy - 5, phase, intensity)

        # Arms (ice claw arms)
        if action == "attack":
            _NS_ancient_apparition._draw_attack_arms(surface, cx, cy - 5, facing, phase, attack_progress)
        elif is_casting:
            _NS_ancient_apparition._draw_casting_arms(surface, cx, cy - 5, facing, phase)
        else:
            _NS_ancient_apparition._draw_idle_arms(surface, cx, cy - 5, facing, phase)

        # Head with ghostly face
        _NS_ancient_apparition._draw_aa_head(surface, cx, cy - 26, facing, phase, intensity)

        # Ice crown / top shards
        _NS_ancient_apparition._draw_ice_crown(surface, cx, cy - 40, phase, intensity)

        # Sparkle particles around body
        _NS_ancient_apparition._draw_body_sparkles(surface, cx, cy - 10, phase, intensity)

        # ORIGINAL-MAX detail pass (wajah true boss + emblem + rim)
        _NS_ancient_apparition._masterwork_finish(surface, cx, cy, facing,
                                                  phase, action, attack_progress)


    def _draw_ice_skirt(surface, cx, cy, phase, intensity=1.0):
        """Lower body - jagged ice shards flowing down."""
        sway = math.sin(phase * 0.6) * 2

        # Central mass
        _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["shadow_ice"], [
            (cx - 16, cy),
            (cx + 16, cy),
            (cx + 14, cy + 25),
            (cx + 6, cy + 32),
            (cx - 6, cy + 32),
            (cx - 14, cy + 25),
        ])
        _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_darkest"], [
            (cx - 14, cy + 2),
            (cx + 14, cy + 2),
            (cx + 12, cy + 23),
            (cx + 5, cy + 30),
            (cx - 5, cy + 30),
            (cx - 12, cy + 23),
        ])
        _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_dark"], [
            (cx - 12, cy + 4),
            (cx + 12, cy + 4),
            (cx + 10, cy + 21),
            (cx + 4, cy + 26),
            (cx - 4, cy + 26),
            (cx - 10, cy + 21),
        ])
        _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_mid"], [
            (cx - 8, cy + 6),
            (cx + 8, cy + 6),
            (cx + 6, cy + 18),
            (cx + 2, cy + 22),
            (cx - 2, cy + 22),
            (cx - 6, cy + 18),
        ])

        # Vertical light lines (ice reflection)
        for line_x in (-4, 0, 4):
            _NS_ancient_apparition._aaline(surface, _NS_ancient_apparition.PALETTE["ice_bright"],
                    (cx + line_x, cy + 4), (cx + line_x, cy + 20), 1)

        # Jagged ice shards hanging down at sides
        for i, offset in enumerate([-14, -8, -2, 4, 10, 14]):
            shard_h = 18 + (i % 3) * 4
            shard_x = cx + offset + int(sway * (offset / 15))
            tip_x = shard_x + int(sway * 0.5)
            tip_y = cy + shard_h

            _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["shadow_deep"], [
                (shard_x - 3 + 1, cy + 4 + 1),
                (shard_x + 3 + 1, cy + 4 + 1),
                (tip_x + 1, tip_y + 1),
            ])
            _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_darkest"], [
                (shard_x - 3, cy + 4),
                (shard_x + 3, cy + 4),
                (tip_x, tip_y),
            ])
            _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_dark"], [
                (shard_x - 2, cy + 5),
                (shard_x + 2, cy + 5),
                (tip_x, tip_y - 1),
            ])
            _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_mid"], [
                (shard_x - 1, cy + 6),
                (shard_x + 1, cy + 6),
                (tip_x, tip_y - 3),
            ])
            _NS_ancient_apparition._aaline(surface, _NS_ancient_apparition.PALETTE["ice_bright"],
                    (shard_x, cy + 6), (tip_x, tip_y - 2), 1)
            _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["ice_hot"], (tip_x, tip_y - 1), 1)


    def _draw_ice_torso(surface, cx, cy, phase, intensity=1.0):
        """Crystalline torso - cluster of shards."""
        # Shadow
        _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["shadow_deep"], [
            (cx - 12 + 2, cy - 8 + 2),
            (cx + 12 + 2, cy - 8 + 2),
            (cx + 14 + 2, cy + 10 + 2),
            (cx - 14 + 2, cy + 10 + 2),
        ])

        # Main torso mass
        torso = [
            (cx - 12, cy - 8),
            (cx + 12, cy - 8),
            (cx + 14, cy + 10),
            (cx - 14, cy + 10),
        ]
        _NS_ancient_apparition._draw_ice_shard(surface, torso)

        # Central bright core
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        core_r = int(6 * pulse * intensity)
        _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_dark"], 200), (cx, cy), core_r + 4)
        _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["ice_mid"], (cx, cy), core_r + 2)
        _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["ice_bright"], (cx, cy), core_r)
        _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["ice_hot"], (cx, cy), max(1, core_r - 2))
        _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["ice_pure"], (cx, cy), max(1, core_r - 4))

        # Diagonal ice facet lines
        _NS_ancient_apparition._aaline(surface, _NS_ancient_apparition.PALETTE["ice_bright"], (cx - 10, cy - 5), (cx - 4, cy + 5), 1)
        _NS_ancient_apparition._aaline(surface, _NS_ancient_apparition.PALETTE["ice_bright"], (cx + 10, cy - 5), (cx + 4, cy + 5), 1)
        _NS_ancient_apparition._aaline(surface, _NS_ancient_apparition.PALETTE["ice_hot"], (cx - 5, cy - 6), (cx - 2, cy - 2), 1)
        _NS_ancient_apparition._aaline(surface, _NS_ancient_apparition.PALETTE["ice_hot"], (cx + 5, cy - 6), (cx + 2, cy - 2), 1)

        # Shoulder shards jutting outward
        for side in (-1, 1):
            _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_darkest"], [
                (cx + side * 10, cy - 6),
                (cx + side * 16, cy - 10),
                (cx + side * 14, cy - 4),
            ])
            _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_dark"], [
                (cx + side * 11, cy - 5),
                (cx + side * 15, cy - 9),
                (cx + side * 13, cy - 4),
            ])
            _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_mid"], [
                (cx + side * 12, cy - 5),
                (cx + side * 14, cy - 8),
                (cx + side * 13, cy - 5),
            ])
            _NS_ancient_apparition._aaline(surface, _NS_ancient_apparition.PALETTE["ice_bright"],
                    (cx + side * 12, cy - 5),
                    (cx + side * 15, cy - 9), 1)

        # Small ice spikes on chest (upward)
        for i, off in enumerate([-6, -2, 3, 7]):
            _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_darkest"], [
                (cx + off - 1, cy - 6),
                (cx + off + 1, cy - 6),
                (cx + off, cy - 10 - (i % 2) * 2),
            ])
            _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_bright"], [
                (cx + off, cy - 6),
                (cx + off + 1, cy - 6),
                (cx + off, cy - 9),
            ])


    def _draw_aa_head(surface, cx, cy, facing, phase, intensity=1.0):
        """Ghostly ice head with glowing face."""
        # Head shape - elongated hood-like
        head = [
            (cx - 9, cy + 8),
            (cx - 10, cy - 2),
            (cx - 6, cy - 10),
            (cx, cy - 12),
            (cx + 6, cy - 10),
            (cx + 10, cy - 2),
            (cx + 9, cy + 8),
        ]
        _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["shadow_deep"], [(p[0] + 2, p[1] + 2) for p in head])
        _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_darkest"], head)
        _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_dark"], [
            (cx - 8, cy + 7),
            (cx - 9, cy - 2),
            (cx - 5, cy - 9),
            (cx, cy - 11),
            (cx + 5, cy - 9),
            (cx + 9, cy - 2),
            (cx + 8, cy + 7),
        ])
        _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_mid"], [
            (cx - 6, cy + 6),
            (cx - 7, cy - 2),
            (cx - 4, cy - 7),
            (cx, cy - 9),
            (cx + 4, cy - 7),
            (cx + 7, cy - 2),
            (cx + 6, cy + 6),
        ])

        # Face area - darker recessed
        _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["shadow_deep"], [
            (cx - 6, cy - 4),
            (cx + 6, cy - 4),
            (cx + 5, cy + 5),
            (cx - 5, cy + 5),
        ])

        # GHOSTLY GLOWING FACE (Ancient Apparition signature!)
        face_pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        face_intensity = face_pulse * intensity

        # Two glowing eyes (elongated ovals) - layered ring + hot core
        for side in (-1, 1):
            ex = cx + side * 3
            ey = cy - 1
            # Outer glow
            _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["face_dark"], int(180 * face_intensity)),
                      (ex, ey), 4)
            # Bright core
            _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["face_hot"], int(255 * face_intensity)),
                      (ex, ey), 2)
            # Bright halo
            _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["face_bright"], int(80 * face_intensity)),
                      (ex, ey), 6)

        # Ghostly mouth (glowing hollow)
        _NS_ancient_apparition._ellipse(surface, _NS_ancient_apparition.PALETTE["shadow_deep"], (cx - 3, cy + 2, 6, 3))
        _NS_ancient_apparition._ellipse(surface, (*_NS_ancient_apparition.PALETTE["face_mid"], int(200 * face_intensity)),
                 (cx - 2, cy + 2, 4, 2))
        _NS_ancient_apparition._ellipse(surface, (*_NS_ancient_apparition.PALETTE["face_bright"], int(230 * face_intensity)),
                 (cx - 1, cy + 2, 2, 1))

        # Ice spikes on sides of head (jagged)
        for side in (-1, 1):
            _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_darkest"], [
                (cx + side * 9, cy - 4),
                (cx + side * 14, cy - 8),
                (cx + side * 11, cy - 2),
            ])
            _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_mid"], [
                (cx + side * 10, cy - 4),
                (cx + side * 13, cy - 7),
                (cx + side * 11, cy - 3),
            ])
            _NS_ancient_apparition._aaline(surface, _NS_ancient_apparition.PALETTE["ice_bright"],
                    (cx + side * 10, cy - 4),
                    (cx + side * 13, cy - 7), 1)

        # Small chin spikes
        for off in (-3, 0, 3):
            _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_darkest"], [
                (cx + off - 1, cy + 6),
                (cx + off + 1, cy + 6),
                (cx + off, cy + 10),
            ])
            _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_mid"], [
                (cx + off, cy + 6),
                (cx + off + 1, cy + 6),
                (cx + off, cy + 9),
            ])

        # Face outer glow (larger halo)
        _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["face_bright"], int(40 * face_intensity)),
                  (cx, cy), 12)


    def _draw_ice_crown(surface, cx, cy, phase, intensity=1.0):
        """Tall ice shards on top of head - crown."""
        # Main central tall spike
        _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["shadow_deep"], [
            (cx - 3 + 1, cy + 8 + 1),
            (cx + 3 + 1, cy + 8 + 1),
            (cx + 1, cy - 10 + 1),
        ])
        _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_darkest"], [
            (cx - 3, cy + 8),
            (cx + 3, cy + 8),
            (cx, cy - 10),
        ])
        _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_dark"], [
            (cx - 2, cy + 7),
            (cx + 2, cy + 7),
            (cx, cy - 9),
        ])
        _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_mid"], [
            (cx - 1, cy + 6),
            (cx + 1, cy + 6),
            (cx, cy - 8),
        ])
        _NS_ancient_apparition._aaline(surface, _NS_ancient_apparition.PALETTE["ice_bright"], (cx, cy + 5), (cx, cy - 8), 1)
        _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["ice_hot"], (cx, cy - 8), 1)

        # Side spikes (slightly shorter, angled outward)
        for side in (-1, 1):
            for offset in (side * 4, side * 8):
                spike_h = 14 - abs(offset) // 2
                tip_x = cx + offset + side * 2
                tip_y = cy + 8 - spike_h

                _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["shadow_deep"], [
                    (cx + offset - 2 + 1, cy + 8 + 1),
                    (cx + offset + 2 + 1, cy + 8 + 1),
                    (tip_x + 1, tip_y + 1),
                ])
                _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_darkest"], [
                    (cx + offset - 2, cy + 8),
                    (cx + offset + 2, cy + 8),
                    (tip_x, tip_y),
                ])
                _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_dark"], [
                    (cx + offset - 1, cy + 7),
                    (cx + offset + 1, cy + 7),
                    (tip_x - side, tip_y + 1),
                ])
                _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_bright"], [
                    (cx + offset, cy + 7),
                    (cx + offset + 1, cy + 7),
                    (tip_x - side, tip_y + 2),
                ])
                _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["ice_hot"], (tip_x, tip_y + 1), 1)

        # Sparkles at spike tips
        for i in range(4):
            angle = phase * 0.5 + i * math.pi / 2
            sx = cx + int(math.cos(angle) * 10)
            sy = cy - 4 + int(math.sin(angle) * 6)
            _NS_ancient_apparition._draw_snowflake(surface, sx, sy, 2, int(180 * intensity),
                            rotate=phase * 2)


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Arms at rest with claw-hands."""
        sway = math.sin(phase * 0.7) * 2
        for side in (-1, 1):
            sh_x = cx + side * 14
            sh_y = cy - 2
            elbow_x = sh_x + side * 8
            elbow_y = cy + 8 + int(sway)
            hand_x = elbow_x + side * 5
            hand_y = elbow_y + 10

            _NS_ancient_apparition._draw_ice_arm_segment(surface, sh_x, sh_y, elbow_x, elbow_y)
            _NS_ancient_apparition._draw_ice_arm_segment(surface, elbow_x, elbow_y, hand_x, hand_y)
            _NS_ancient_apparition._draw_ice_claw(surface, hand_x, hand_y, side, phase)


    def _draw_casting_arms(surface, cx, cy, facing, phase):
        """Both arms raised for casting."""
        for side in (-1, 1):
            sh_x = cx + side * 14
            sh_y = cy - 2
            # Raised elbow
            elbow_x = sh_x + side * 10
            elbow_y = cy - 4
            hand_x = elbow_x + side * 6
            hand_y = cy - 10

            _NS_ancient_apparition._draw_ice_arm_segment(surface, sh_x, sh_y, elbow_x, elbow_y)
            _NS_ancient_apparition._draw_ice_arm_segment(surface, elbow_x, elbow_y, hand_x, hand_y)
            _NS_ancient_apparition._draw_ice_claw(surface, hand_x, hand_y, side, phase)

            # Casting energy in hand
            pulse = math.sin(phase * 4 + side) * 0.3 + 0.7
            r = int(5 * pulse)
            _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_dark"], 150), (hand_x, hand_y), r + 4)
            _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["ice_mid"], (hand_x, hand_y), r + 2)
            _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["ice_bright"], (hand_x, hand_y), r)
            _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["ice_hot"], (hand_x, hand_y), max(1, r - 2))
            _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["ice_pure"], (hand_x, hand_y), max(1, r - 3))


    def _draw_attack_arms(surface, cx, cy, facing, phase, progress):
        """One arm extended forward casting."""
        # Back arm - resting
        back_side = -facing
        bs_x = cx + back_side * 14
        bs_y = cy - 2
        be_x = bs_x + back_side * 8
        be_y = cy + 6
        bh_x = be_x + back_side * 4
        bh_y = be_y + 8
        _NS_ancient_apparition._draw_ice_arm_segment(surface, bs_x, bs_y, be_x, be_y)
        _NS_ancient_apparition._draw_ice_arm_segment(surface, be_x, be_y, bh_x, bh_y)
        _NS_ancient_apparition._draw_ice_claw(surface, bh_x, bh_y, back_side, phase)

        # Front arm - extends forward
        fs_x = cx + facing * 14
        fs_y = cy - 2

        if progress < 0.3:
            t = progress / 0.3
            arm_angle = -0.9 * t
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            arm_angle = -0.9 + 1.8 * t
        else:
            t = (progress - 0.5) / 0.5
            arm_angle = 0.9 - 0.5 * t

        arm_len = 14
        fe_x = fs_x + int(math.cos(arm_angle) * arm_len * 0.6) * facing
        fe_y = fs_y + int(math.sin(arm_angle) * arm_len * 0.6) - 2
        fh_x = fe_x + int(math.cos(arm_angle) * arm_len * 0.7) * facing
        fh_y = fe_y + int(math.sin(arm_angle) * arm_len * 0.7)

        _NS_ancient_apparition._draw_ice_arm_segment(surface, fs_x, fs_y, fe_x, fe_y)
        _NS_ancient_apparition._draw_ice_arm_segment(surface, fe_x, fe_y, fh_x, fh_y)
        _NS_ancient_apparition._draw_ice_claw(surface, fh_x, fh_y, facing, phase)

        # Casting energy
        if 0.2 < progress < 0.55:
            intensity = math.sin((progress - 0.2) / 0.35 * math.pi)
            r = int(4 + intensity * 6)
            _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_dark"], 150), (fh_x, fh_y), r + 4)
            _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["ice_mid"], (fh_x, fh_y), r + 2)
            _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["ice_bright"], (fh_x, fh_y), r)
            _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["ice_hot"], (fh_x, fh_y), max(1, r - 2))
            _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["ice_pure"], (fh_x, fh_y), max(1, r - 4))


    def _draw_ice_arm_segment(surface, x1, y1, x2, y2):
        """Arm segment - jagged ice."""
        _NS_ancient_apparition._aaline(surface, _NS_ancient_apparition.PALETTE["shadow_deep"], (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 8)
        _NS_ancient_apparition._aaline(surface, _NS_ancient_apparition.PALETTE["ice_darkest"], (x1, y1), (x2, y2), 7)
        _NS_ancient_apparition._aaline(surface, _NS_ancient_apparition.PALETTE["ice_dark"], (x1, y1), (x2, y2), 5)
        _NS_ancient_apparition._aaline(surface, _NS_ancient_apparition.PALETTE["ice_mid"], (x1, y1), (x2, y2), 3)
        _NS_ancient_apparition._aaline(surface, _NS_ancient_apparition.PALETTE["ice_bright"], (x1 - 1, y1), (x2 - 1, y2), 1)


    def _draw_ice_claw(surface, cx, cy, facing, phase):
        """Ice claw hand — 3 sharp fingers."""
        # Palm
        _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["shadow_deep"], (cx + 1, cy + 1), 4)
        _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["ice_darkest"], (cx, cy), 4)
        _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["ice_dark"], (cx, cy), 3)
        _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["ice_mid"], (cx - 1, cy - 1), 2)

        # 3 curved claws
        for i, angle_off in enumerate((-0.4, 0, 0.4)):
            base_angle = 0.3 * facing + angle_off
            tip_x = cx + int(math.cos(base_angle) * 8) * facing
            tip_y = cy + int(math.sin(base_angle) * 8) + 3
            base_x = cx + int(math.cos(base_angle) * 3) * facing
            base_y = cy + int(math.sin(base_angle) * 3)

            # Shadow
            _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["shadow_deep"], [
                (base_x - 1 + 1, base_y + 1),
                (base_x + 1 + 1, base_y + 1),
                (tip_x + 1, tip_y + 1),
            ])
            _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_darkest"], [
                (base_x - 1, base_y),
                (base_x + 1, base_y),
                (tip_x, tip_y),
            ])
            _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_dark"], [
                (base_x - 1, base_y),
                (base_x + 1, base_y),
                (tip_x - 1, tip_y - 1),
            ])
            _NS_ancient_apparition._poly(surface, _NS_ancient_apparition.PALETTE["ice_bright"], [
                (base_x, base_y),
                (base_x + 1, base_y),
                (tip_x - 1, tip_y - 2),
            ])
            _NS_ancient_apparition._aacircle(surface, _NS_ancient_apparition.PALETTE["ice_hot"], (tip_x, tip_y), 1)


    def _draw_body_sparkles(surface, cx, cy, phase, intensity=1.0):
        """Sparkling ice particles around body."""
        for i in range(6):
            angle = phase * 0.4 + i * math.pi / 5
            r = 22 + int(math.sin(phase * 0.7 + i) * 8)
            px = cx + int(math.cos(angle) * r)
            py = cy + int(math.sin(angle) * r * 0.6)
            alpha = int((150 + math.sin(phase + i * 0.5) * 100) * intensity)
            alpha = max(0, min(255, alpha))
            _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_bright"], alpha), (px, py), 2)
            _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_hot"], alpha), (px, py), 1)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_ice_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Frost wisps rising from below."""
        NS = _NS_ancient_apparition
        if NS._mist_cache is None:
            mist = pygame.Surface((140, 42), pygame.SRCALPHA)
            for radius in range(34, 3, -4):
                alpha = int((34 - radius) * 2.5)
                if alpha > 0:
                    pygame.draw.ellipse(
                        mist, (*NS.PALETTE["frost_dark"], min(255, alpha)),
                        (70 - radius * 2, 21 - radius // 3,
                         radius * 4, max(3, radius // 2)),
                    )
            NS._mist_cache = mist
        strength = 1.5 if intense else 1.0
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        spr = NS._mist_cache
        spr.set_alpha(int(255 * min(1.0, pulse * strength)))
        surface.blit(spr, (cx - 70, cy - 10))

        # Rising frost wisps
        for i, offset in enumerate((-18, 0, 18)):
            t = (phase * 0.55 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 28)
            alpha = max(0, min(255, int(220 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["frost_dark"], alpha), (sx, sy), 5)
            _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_hot"], alpha), (sx, sy - 3), 2)

        # Snowflakes drifting
        for i in range(3):
            t = (phase * 0.4 + i * 0.2) % 1.0
            angle = phase * 0.5 + i * math.pi * 2 / 5
            r = 22 + int(math.sin(phase + i * 1.3) * 6)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 9) - int(t * 8)
            alpha = int(230 * (1 - t * 0.5) * strength)
            _NS_ancient_apparition._draw_snowflake(surface, sx, sy, 2, max(0, min(255, alpha)),
                             rotate=phase + i)

        # Small ice crystals on ground
        for i in range(2):
            angle = i * math.pi / 2
            sx = cx + int(math.cos(angle) * 30)
            sy = cy + int(math.sin(angle) * 6)
            _NS_ancient_apparition._draw_frost_crystal_spike(surface, sx, sy + 4, sy - 3, 2, 200)

        if trail:
            for i in range(3):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = max(0, 140 - i * 25)
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["frost_mid"], alpha),
                          (sx, sy), max(2, 5 - i))
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["frost_light"], alpha),
                          (sx, sy), max(1, 3 - i))


    def _draw_shadow(surface, x, y, lift=0):
        NS = _NS_ancient_apparition
        if NS._shadow_cache is None:
            shadow = pygame.Surface((110, 22), pygame.SRCALPHA)
            for radius in range(11, 0, -1):
                alpha = max(0, (11 - radius) * 15)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (11 - radius, 11 - radius, 88 + radius * 2, radius * 2),
                )
            pygame.draw.ellipse(shadow, (*NS.PALETTE["ice_dark"], 80), (10, 5, 90, 12))
            NS._shadow_cache = shadow
        spr = NS._shadow_cache
        w, h = spr.get_size()
        if lift:
            k = max(0.12, 1.0 - lift * 0.05)
            w = max(6, int(w * k))
            h = max(2, int(h * k))
            spr = pygame.transform.smoothscale(spr, (w, h))
        bx = x - w // 2
        by = (y + 11) - h          # dasar tetap menapak di y+11
        surface.blit(spr, (bx, by))
        if NS._record_shadow is not None:
            NS._record_shadow.append(pygame.Rect(bx, by, w, h))


    def _draw_frost_aura(surface, x, y, phase, active_skill):
        NS = _NS_ancient_apparition
        if NS._aura_cache is None:
            aura = pygame.Surface((200, 180), pygame.SRCALPHA)
            for radius in range(80, 5, -4):
                alpha = int((80 - radius) * 1.4)
                if alpha > 0:
                    NS._aacircle(aura, (*NS.PALETTE["ice_darkest"], min(255, alpha)),
                                 (100, 90), radius)
            NS._aura_cache = aura
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.5 if active_skill in ("q", "w", "e", "r") else 1.0
        spr = NS._aura_cache
        spr.set_alpha(int(255 * max(0.15, min(1.0, pulse * strength))))
        surface.blit(spr, (x - 100, y - 90))


    def _draw_ground_frost(surface, x, y, phase, active_skill):
        """Frost ring on ground (basis di-cache)."""
        NS = _NS_ancient_apparition
        if NS._ground_cache is None:
            ring = pygame.Surface((140, 46), pygame.SRCALPHA)
            pygame.draw.ellipse(ring, (*NS.PALETTE["ice_dark"], 160),
                                (5, 10, 130, 26), 3)
            pygame.draw.ellipse(ring, (*NS.PALETTE["ice_mid"], 190),
                                (20, 14, 100, 18), 2)
            for i in range(10):
                angle = i * math.pi / 5
                x1 = 70 + int(math.cos(angle) * 32)
                y1 = 23 + int(math.sin(angle) * 7)
                x2 = 70 + int(math.cos(angle) * 60)
                y2 = 23 + int(math.sin(angle) * 11)
                pygame.draw.line(ring, (*NS.PALETTE["ice_bright"], 180),
                                 (x1, y1), (x2, y2), 1)
            NS._ground_cache = ring
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        surface.blit(NS._ground_cache, (x - 70, y - 23))
        if active_skill:
            pygame.draw.ellipse(surface, (*NS.PALETTE["ice_hot"], int(80 * pulse)),
                                (x - 55, y - 15, 110, 30), 1)


    def _draw_cast_flash(surface, x, y, facing, progress):
        """Flash at hand during ranged attack."""
        if progress < 0.25 or progress > 0.6:
            return
        t = (progress - 0.25) / 0.35
        intensity = math.sin(t * math.pi)

        fx = x + 22 * facing
        fy = y - 5
        alpha = int(220 * intensity)
        radius = int(6 + intensity * 14)

        _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_dark"], alpha // 2), (fx, fy), radius + 6)
        _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_mid"], alpha), (fx, fy), radius + 2)
        _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_bright"], alpha), (fx, fy), radius)
        _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_hot"], alpha), (fx, fy), max(1, radius - 3))
        _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_pure"], min(255, alpha)),
                  (fx, fy), max(1, radius - 5))

        # Snowflake burst
        for i in range(5):
            angle = i * math.pi * 2 / 5 + progress * 3
            ex = fx + int(math.cos(angle) * radius * 1.4)
            ey = fy + int(math.sin(angle) * radius * 1.4)
            _NS_ancient_apparition._draw_snowflake(surface, ex, ey, 2, alpha, rotate=progress * 5)


    # ===================================================================
    # SKILL Q: ICE VORTEX
    # ===================================================================
    def _draw_ice_vortex_ground(surface, boss, x, y, timer, phase):
        """Ground ripple beneath vortex."""
        tx, ty = _NS_ancient_apparition._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 3) * 0.3 + 0.7

        # Concentric rings
        for i in range(4):
            r = int(15 + i * 12 + progress * 20 + math.sin(phase * 2 + i) * 3)
            _NS_ancient_apparition._ellipse(surface, (*_NS_ancient_apparition.PALETTE["ice_dark"], int(150 * pulse)),
                     (tx - r, ty - r // 3, r * 2, r // 1.5), 2)
            _NS_ancient_apparition._ellipse(surface, (*_NS_ancient_apparition.PALETTE["ice_mid"], int(100 * pulse)),
                     (tx - r + 3, ty - r // 3 + 2,
                      r * 2 - 6, r // 1.5 - 4), 1)


    def _draw_ice_vortex(surface, boss, x, y, timer, phase):
        """Spinning ice tornado at target."""
        tx, ty = _NS_ancient_apparition._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.15:
            return

        # Vortex height and width
        if progress < 0.5:
            height = int(60 * (progress - 0.15) / 0.35)
        else:
            height = int(60 * (1 - (progress - 0.85) / 0.15)) if progress > 0.85 else 60

        if height <= 0:
            return

        max_width = 28

        # Draw spinning vortex - rings at different heights
        ring_count = height // 3
        for i in range(ring_count):
            h_ratio = i / max(1, ring_count)
            y_offset = -int(h_ratio * height)
            # Wider at bottom, narrower at top
            width = int(max_width * (1 - h_ratio * 0.4))

            rotation = phase * 4 + h_ratio * 8
            # Ring is a spinning ellipse - draw as several arcs
            for j in range(8):
                angle1 = rotation + j * math.pi / 4
                angle2 = angle1 + 0.5
                x1 = tx + int(math.cos(angle1) * width)
                y1 = ty + y_offset + int(math.sin(angle1) * width * 0.3)
                x2 = tx + int(math.cos(angle2) * width)
                y2 = ty + y_offset + int(math.sin(angle2) * width * 0.3)

                alpha = int(200 * (1 - h_ratio * 0.3))
                _NS_ancient_apparition._aaline(surface, (*_NS_ancient_apparition.PALETTE["ice_dark"], alpha), (x1, y1), (x2, y2), 3)
                _NS_ancient_apparition._aaline(surface, (*_NS_ancient_apparition.PALETTE["ice_bright"], alpha), (x1, y1), (x2, y2), 1)

            # Bright spots (spinning fast)
            for j in range(3):
                spin_angle = rotation + j * math.pi * 2 / 3
                sx = tx + int(math.cos(spin_angle) * width)
                sy = ty + y_offset + int(math.sin(spin_angle) * width * 0.3)
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_hot"], 220), (sx, sy), 3)
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_pure"], 250), (sx, sy), 1)

        # Ice shards flying around vortex
        for i in range(6):
            angle = phase * 2 + i * math.pi / 3
            r = max_width - 3
            sx = tx + int(math.cos(angle) * r)
            sy = ty - height // 2 + int(math.sin(angle) * 15)
            _NS_ancient_apparition._draw_snowflake(surface, sx, sy, 3, 230, rotate=phase * 3)

        # Base pool
        _NS_ancient_apparition._ellipse(surface, (*_NS_ancient_apparition.PALETTE["ice_bright"], 180),
                 (tx - max_width, ty - max_width // 3,
                  max_width * 2, max_width // 1.5), 2)


    # ===================================================================
    # SKILL R: COLD FEET (ice spike ring)
    # ===================================================================
    def _draw_cold_feet_ground(surface, boss, x, y, timer, phase):
        """Warning circle for cold feet."""
        tx, ty = _NS_ancient_apparition._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 3) * 0.3 + 0.7

        if progress < 0.4:
            radius = int(40 + progress * 20)
            _NS_ancient_apparition._ellipse(surface, (*_NS_ancient_apparition.PALETTE["ice_dark"], int(200 * pulse)),
                     (tx - radius, ty - radius // 3, radius * 2, radius // 1.5), 3)
            _NS_ancient_apparition._ellipse(surface, (*_NS_ancient_apparition.PALETTE["ice_mid"], int(150 * pulse)),
                     (tx - radius + 4, ty - radius // 3 + 2,
                      radius * 2 - 8, radius // 1.5 - 4), 2)


    def _draw_cold_feet_spikes(surface, boss, x, y, timer, phase):
        """Ring of ice spikes erupting from ground."""
        tx, ty = _NS_ancient_apparition._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # Charging phase - snowflakes gathering
            for i in range(8):
                angle = phase * 2 + i * math.pi / 4
                r = 60 * (1 - progress / 0.3)
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.5)
                _NS_ancient_apparition._draw_snowflake(surface, sx, sy, 3, 200, rotate=phase * 4)
            return

        # Erupt phase
        erupt_t = min(1.0, (progress - 0.3) / 0.3)

        # Ring of spikes
        num_spikes = 12
        ring_r = 50
        for i in range(num_spikes):
            angle = i * math.pi * 2 / num_spikes
            spike_x = tx + int(math.cos(angle) * ring_r)
            spike_y = ty + int(math.sin(angle) * ring_r * 0.5)
            spike_h = int(25 * erupt_t)
            width = 3

            _NS_ancient_apparition._draw_frost_crystal_spike(surface, spike_x, spike_y,
                                        spike_y - spike_h, width, 240, phase)

        # Central big spike (bigger)
        center_h = int(35 * erupt_t)
        _NS_ancient_apparition._draw_frost_crystal_spike(surface, tx, ty, ty - center_h, 5, 250, phase)

        # Second ring - smaller spikes between
        for i in range(num_spikes):
            angle = (i + 0.5) * math.pi * 2 / num_spikes
            spike_x = tx + int(math.cos(angle) * (ring_r * 0.6))
            spike_y = ty + int(math.sin(angle) * (ring_r * 0.6) * 0.5)
            spike_h = int(18 * erupt_t)
            _NS_ancient_apparition._draw_frost_crystal_spike(surface, spike_x, spike_y,
                                        spike_y - spike_h, 2, 230, phase)

        # Snowflakes bursting outward
        for i in range(10):
            angle = i * math.pi / 5 + phase * 2
            r = ring_r + int(math.sin(phase * 3 + i) * 10)
            sx = tx + int(math.cos(angle) * r)
            sy = ty + int(math.sin(angle) * r * 0.5) - int(erupt_t * 15)
            _NS_ancient_apparition._draw_snowflake(surface, sx, sy, 2, int(230 * erupt_t),
                             rotate=phase * 3 + i)

        # Frost mist around
        for i in range(5):
            angle = phase * 0.5 + i * math.pi * 2 / 5
            r = ring_r + 5
            sx = tx + int(math.cos(angle) * r)
            sy = ty + int(math.sin(angle) * r * 0.5)
            _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["frost_light"], int(120 * erupt_t)),
                      (sx, sy), 8)


    # ===================================================================
    # Backward compatible alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_ancient_apparition.draw_apparition(surface, boss, x, y)

    # ===================================================================
    # ALIAS - nama fungsi yang dipakai registry heroes/__init__.py
    # ===================================================================
    def draw_ancient_apparition(surface, boss, x, y):
        """Entry point resmi untuk Ancient Apparition."""
        _NS_ancient_apparition.draw_apparition(surface, boss, x, y)



# ====================================================================

def draw_ancient_apparition_v1(surface, boss, x, y):
    return _NS_ancient_apparition.draw_ancient_apparition(surface, boss, x, y)
