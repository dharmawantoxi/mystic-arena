#!/usr/bin/env python3
"""SNAPSHOT renderer KHALROS v1 (sebelum upgrade Pixel Masterwork v2).

Diekstrak VERBATIM dari `bosses/level2.py` pada commit 4d32b02 (blok
`class _NS_khalros`, 1768 baris) tepat sebelum rewrite dimulai. Jangan
diedit manual - fungsinya hanya satu: memberi pembanding "sebelum" yang
jujur di `tools/_audit_khalros_v2.py` / `_shot_khalros_v2.py`.

Nama kelas di dalam file ini tetap `_NS_khalros` supaya seluruh referensi
diri-sendiri (`_NS_khalros.PALETTE`, ...) jalan tanpa perubahan.
"""
import math
import pygame

try:
    import lighting as _lighting
except Exception:  # pragma: no cover
    _lighting = None


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
