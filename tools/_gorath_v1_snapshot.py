#!/usr/bin/env python3
"""SNAPSHOT renderer gorath v1 (sebelum upgrade Pixel Masterwork v2).

Dibuat otomatis sebelum rewrite `_NS_gorath` di bosses/level2.py.
Dipakai tools/_audit_gorath_v2.py untuk lembar before/after -
jangan diedit manual; kalau perlu regenerasi, ambil dari git history.
"""
import math
import pygame

try:
    import lighting as _lighting
except Exception:  # pragma: no cover
    _lighting = None


class _NS_gorath:
    """Namespace gorath - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    # ── ORIGINAL-MAX cache (piksel-identik, dibangun lazy) ──────────
    _shadow_cache = None
    _aura_cache = None
    _flash_buf = None
    _body_buf = None        # buffer badan untuk outline+lighting
    _record_shadow = None

    # ---------------------------------------------------------------------------
    # HD Blood Palette - Deep crimson / dark red / bone
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin - reddish demon flesh
        "skin_darkest":   (35,  10,  10),
        "skin_dark":      (78,  22,  20),
        "skin_mid":       (125, 45,  35),
        "skin_light":     (175, 78,  55),
        "skin_high":      (215, 130, 90),
        "skin_shine":     (245, 185, 140),

        # Blood
        "blood_darkest":  (25,   3,   5),
        "blood_dark":     (72,   6,  10),
        "blood_mid":      (135, 15,  20),
        "blood_bright":   (195, 25,  30),
        "blood_hot":      (235, 55,  50),
        "blood_glow":     (255, 100, 85),
        "blood_light":    (255, 165, 140),

        # Hair - dark spiky
        "hair_darkest":   (10,   8,  12),
        "hair_dark":      (28,  22,  30),
        "hair_mid":       (55,  45,  58),
        "hair_high":      (95,  82, 100),

        # Leather / cloth
        "leather_darkest": (18, 12,  8),
        "leather_dark":   (45,  28,  18),
        "leather_mid":    (85,  55,  30),
        "leather_light":  (135, 90,  50),
        "leather_high":   (185, 135, 80),

        # Bone / claws
        "bone_darkest":   (55,  45,  35),
        "bone_dark":      (115, 100, 78),
        "bone_mid":       (175, 160, 130),
        "bone_light":     (220, 210, 180),
        "bone_shine":     (245, 240, 220),

        # Metal (blades)
        "metal_darkest":  (18,  15,  18),
        "metal_dark":     (48,  42,  48),
        "metal_mid":      (95,  88,  95),
        "metal_light":    (155, 148, 155),
        "metal_shine":    (215, 210, 215),

        # Eyes - glowing red
        "eye_dark":       (80,   5,   8),
        "eye_mid":        (180, 20,  25),
        "eye_bright":     (240, 55,  50),
        "eye_hot":        (255, 130, 100),
        "eye_white":      (255, 220, 200),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (5,   2,   3),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        """Clamp color channels, supports both RGB and RGBA."""
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_gorath._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
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
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_gorath._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh), border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)


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
    # Blood splatter & droplet helpers
    # ---------------------------------------------------------------------------
    def _draw_blood_splatter(surface, cx, cy, size=8, seed=0, alpha=255):
        """Draw a chaotic blood splatter."""
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
        """Draw a single blood droplet (teardrop shape)."""
        _NS_gorath._poly(surface, (*_NS_gorath.PALETTE["blood_darkest"], alpha), [
            (x, y - size),
            (x - size, y + size),
            (x + size, y + size),
        ])
        _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_mid"], alpha), (x, y + size // 2), size)
        _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], alpha),
                  (x, y + size // 2), max(1, size - 1))
        _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_hot"], alpha),
                  (x - 1, y + size // 2 - 1), max(1, size - 2))


    def _draw_blood_streak(surface, sx, sy, ex, ey, width=3, alpha=255):
        """Blood streak with dripping effect."""
        _NS_gorath._aaline(surface, (*_NS_gorath.PALETTE["blood_darkest"], alpha), (sx, sy), (ex, ey), width + 2)
        _NS_gorath._aaline(surface, (*_NS_gorath.PALETTE["blood_mid"], alpha), (sx, sy), (ex, ey), width)
        _NS_gorath._aaline(surface, (*_NS_gorath.PALETTE["blood_bright"], alpha), (sx, sy), (ex, ey), max(1, width - 1))


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM (for Bloodrite / Thirst effects)
    # ---------------------------------------------------------------------------
    class BloodProjectile:
        """A blood-based projectile for ranged skills."""
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
            if len(self.trail) > 10:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(50 + i * 15)
                r = max(1, 5 - (len(self.trail) - i))
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_dark"], alpha), (tx, ty), r + 2)
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], alpha), (tx, ty), r)
            if self.alive:
                px, py = int(self.x), int(self.y)
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_dark"], 100), (px, py), 10)
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_mid"], 180), (px, py), 7)
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], 230), (px, py), 5)
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_hot"], 250), (px, py), 3)
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_light"], 255), (px, py - 1), 1)


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
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        """Track melee attack timeline."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 44)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_gor_prev_timer", 0))
        active = bool(getattr(boss, "_gor_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._gor_attack_active = True
            boss._gor_attack_frame = 0
            active = True
        elif active:
            boss._gor_attack_frame = int(getattr(boss, "_gor_attack_frame", 0)) + 1
            if boss._gor_attack_frame > cooldown:
                boss._gor_attack_active = False
                boss._gor_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._gor_attack_active = False
            boss._gor_attack_frame = 0
            active = False

        boss._gor_prev_timer = timer
        boss._gor_attack_progress = (
            min(1.0, getattr(boss, "_gor_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_gor_projectiles"):
            boss._gor_projectiles = []
        for proj in boss._gor_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._gor_projectiles = [p for p in boss._gor_projectiles if p.alive or p.age < 8]


    def _spawn_projectile(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_gor_projectiles"):
            boss._gor_projectiles = []
        boss._gor_projectiles.append(_NS_gorath.BloodProjectile(sx, sy, tx, ty, speed=6.5))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_gorath(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_gorath._detect_moving(boss)
        _NS_gorath._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_gor_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 44) - 15
        )

        # Background
        _NS_gorath._draw_blood_aura(surface, x, y, pulse, active_skill)
        _NS_gorath._draw_ground_blood_pool(surface, x, y + 38, pulse, active_skill)

        # Skill ground effects
        if active_skill == "w":
            _NS_gorath._draw_bloodrite_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_gorath._draw_rupture_ground(surface, boss, x, y, skill_timer, pulse)

        # PERTAGAS: gelombang kejut aktivasi skill (12 frame pertama)
        if active_skill in ("q", "w", "e", "r"):
            dur = {"q": 90, "w": 60, "e": 35, "r": 90}[active_skill]
            age = dur - skill_timer
            if 0 <= age < 12:
                _NS_gorath._draw_shockwave(surface, x, y + 46, age, 12,
                                           _NS_gorath.PALETTE["blood_hot"],
                                           _NS_gorath.PALETTE["blood_light"])

        # ORIGINAL-MAX hurt flash: badan dibanjiri putih-hangat, bayangan
        # tanah tidak ikut menyala.
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        _tgt, _tx, _ty = surface, x, y
        if flash > 0:
            B = _NS_gorath
            if B._flash_buf is None:
                B._flash_buf = pygame.Surface((240, 260), pygame.SRCALPHA)
            B._flash_buf.fill((0, 0, 0, 0))
            B._record_shadow = []
            _tgt, _tx, _ty = B._flash_buf, 120, 135

        # Character
        if attacking:
            _NS_gorath._draw_gorath_attack(_tgt, boss, _tx, _ty)
        elif moving:
            _NS_gorath._draw_gorath_walk(_tgt, boss, _tx, _ty)
        else:
            _NS_gorath._draw_gorath_idle(_tgt, boss, _tx, _ty)

        if flash > 0:
            B = _NS_gorath
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

        # Projectiles
        _NS_gorath._manage_projectiles(boss, surface, pulse)

        # Foreground skill effects
        if active_skill == "q":
            _NS_gorath._draw_bloodrage(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_gorath._draw_bloodrite(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_gorath._draw_thirst(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_gorath._draw_rupture(surface, boss, x, y, skill_timer, pulse)


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
        _NS_gorath._aacircle(surface, (*c1, int(a * 0.8)),
                             (x, y - (r // 6)), ri)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_gorath_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        _NS_gorath._draw_shadow(surface, x, y + 46)
        _NS_gorath._draw_blood_wisps(surface, x, y + 30, boss.pulse)
        _NS_gorath._draw_gorath_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_gorath_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(abs(math.sin(phase * 1.3)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_gorath._draw_shadow(surface, x + sway, y + 46)
        _NS_gorath._draw_blood_wisps(surface, x + sway, y + 30, phase, trail=True, facing=boss.direction)
        _NS_gorath._draw_gorath_body(surface, x + sway, y - bob, boss.direction, phase, "walk")
        _NS_gorath._draw_blood_trail(surface, x + sway, y + 30, phase, boss.direction)


    def _draw_gorath_attack(surface, boss, x, y):
        progress = getattr(boss, "_gor_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        lunge = int(math.sin(progress * math.pi) * 5) * boss.direction

        _NS_gorath._draw_shadow(surface, x + lunge, y + 46)
        _NS_gorath._draw_blood_wisps(surface, x + lunge, y + 30, boss.pulse, intense=True)
        _NS_gorath._draw_gorath_body(surface, x + lunge, y, boss.direction, boss.pulse,
                          "attack", progress)
        _NS_gorath._draw_blade_swing_arc(surface, x + lunge, y, boss.direction, progress)
        _NS_gorath._draw_swing_impact(surface, x + lunge, y, boss.direction, progress)


    # ===================================================================
    # BODY RENDERING
    # ===================================================================
    def _draw_gorath_body_raw(surface, cx, cy, facing, phase, action, attack_progress=0):
        sway = int(math.sin(phase * 0.6) * (2 if action != "idle" else 1))

        # Lower floating body (loincloth / robe)
        _NS_gorath._draw_loincloth(surface, cx, cy + 8, phase, sway)

        # Torso
        _NS_gorath._draw_torso(surface, cx, cy - 5, phase, sway)

        # Head with hair
        _NS_gorath._draw_gorath_head(surface, cx, cy - 26, facing, phase)

        # Shoulders
        _NS_gorath._draw_shoulders(surface, cx, cy - 12, phase)

        # Arms with blades
        if action == "attack":
            _NS_gorath._draw_attack_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        else:
            _NS_gorath._draw_idle_arms(surface, cx, cy - 8, facing, phase)

        # Blood dripping from body
        _NS_gorath._draw_body_blood_drips(surface, cx, cy, phase)

    def _draw_gorath_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Komposit ORIGINAL-MAX: badan -> buffer tetap -> outline siluet
        gelap 1 px + pass pencahayaan (rim/shade) -> blit posisi dunia sama."""
        NS = _NS_gorath
        B = 200
        if NS._body_buf is None:
            NS._body_buf = pygame.Surface((B, B), pygame.SRCALPHA)
        buf = NS._body_buf
        buf.fill((0, 0, 0, 0))
        NS._draw_gorath_body_raw(buf, B // 2, B // 2, facing, phase, action, attack_progress)
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
            _lighting.apply_to_rig(sub, rim_add=(46, 18, 16), shade_mul=168)
        surface.blit(sub, (ox, oy))


    def _draw_loincloth(surface, cx, cy, phase, sway):
        """Floating lower body — tattered loincloth with blood."""
        # Waist belt
        _NS_gorath._rect(surface, _NS_gorath.PALETTE["leather_darkest"], (cx - 15, cy - 4, 30, 6))
        _NS_gorath._rect(surface, _NS_gorath.PALETTE["leather_dark"], (cx - 14, cy - 3, 28, 4))
        _NS_gorath._rect(surface, _NS_gorath.PALETTE["leather_mid"], (cx - 13, cy - 2, 26, 2))

        # Belt buckle - blood symbol
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_darkest"], (cx, cy - 1), 4)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_mid"], (cx, cy - 1), 3)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_bright"], (cx, cy - 2), 2)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_hot"], (cx, cy - 2), 1)

        # Tattered loincloth strips
        for i, offset in enumerate([-11, -6, -1, 5, 10]):
            wave = math.sin(phase * 1.2 + i) * 2
            length = 20 + (i % 2) * 4
            # Shadow
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["shadow_deep"], [
                (cx + offset - 3, cy + 3),
                (cx + offset + 3, cy + 3),
                (cx + offset + 2 + int(wave), cy + length),
                (cx + offset - 2 + int(wave), cy + length),
            ])
            # Main strip
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["leather_darkest"], [
                (cx + offset - 3, cy + 2),
                (cx + offset + 3, cy + 2),
                (cx + offset + 2 + int(wave), cy + length - 1),
                (cx + offset - 2 + int(wave), cy + length - 1),
            ])
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["leather_dark"], [
                (cx + offset - 2, cy + 3),
                (cx + offset + 2, cy + 3),
                (cx + offset + 1 + int(wave), cy + length - 3),
                (cx + offset - 1 + int(wave), cy + length - 3),
            ])
            # Blood stain on some strips
            if i % 2 == 0:
                _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_darkest"],
                          (cx + offset, cy + length - 8), 3)
                _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_dark"],
                          (cx + offset, cy + length - 8), 2)
                _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_mid"],
                          (cx + offset, cy + length - 9), 1)


    def _draw_torso(surface, cx, cy, phase, sway):
        """Muscular red-skinned torso."""
        # Shadow
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["shadow_deep"], [
            (cx - 14 + 2, cy - 8 + 2), (cx + 14 + 2, cy - 8 + 2),
            (cx + 13 + 2, cy + 14 + 2), (cx + 6 + 2, cy + 18 + 2),
            (cx - 6 + 2, cy + 18 + 2), (cx - 13 + 2, cy + 14 + 2),
        ])

        # Main torso
        torso = [
            (cx - 14, cy - 8), (cx + 14, cy - 8),
            (cx + 13, cy + 14), (cx + 6, cy + 18),
            (cx - 6, cy + 18), (cx - 13, cy + 14),
        ]
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["skin_darkest"], torso)
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["skin_dark"], [
            (cx - 12, cy - 7), (cx + 12, cy - 7),
            (cx + 11, cy + 12), (cx + 5, cy + 16),
            (cx - 5, cy + 16), (cx - 11, cy + 12),
        ])
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["skin_mid"], [
            (cx - 9, cy - 5), (cx + 9, cy - 5),
            (cx + 8, cy + 10), (cx + 3, cy + 14),
            (cx - 3, cy + 14), (cx - 8, cy + 10),
        ])

        # Chest highlights (pectorals)
        for side in (-1, 1):
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_light"],
                      (cx + side * 5, cy - 2), 4)
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_high"],
                      (cx + side * 5 - 1, cy - 3), 2)

        # Abs definition
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["skin_darkest"], (cx, cy + 2), (cx, cy + 14), 1)
        for yoff in (4, 8, 12):
            _NS_gorath._aaline(surface, _NS_gorath.PALETTE["skin_darkest"],
                    (cx - 5, cy + yoff), (cx + 5, cy + yoff), 1)

        # Blood stains on chest
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_darkest"], (cx - 4, cy + 8), 3)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_dark"], (cx - 4, cy + 8), 2)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_bright"], (cx + 6, cy + 5), 2)

        # Necklace / trophy cord
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["bone_darkest"], (cx - 8, cy - 6), (cx + 8, cy - 6), 1)
        for i, xoff in enumerate([-6, -2, 2, 6]):
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["bone_dark"], (cx + xoff, cy - 4), 2)
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["bone_mid"], (cx + xoff, cy - 4), 1)


    def _draw_shoulders(surface, cx, cy, phase):
        """Muscular shoulders with leather straps."""
        for side in (-1, 1):
            sx = cx + side * 13
            # Shadow
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["shadow_deep"], (sx + 2, cy + 2), 8)
            # Shoulder
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_darkest"], (sx, cy), 8)
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_dark"], (sx - side, cy - 1), 7)
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_mid"], (sx - side * 2, cy - 2), 5)
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_light"], (sx - side * 3, cy - 3), 3)
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_high"], (sx - side * 3, cy - 4), 1)

            # Leather shoulder strap
            _NS_gorath._rect(surface, _NS_gorath.PALETTE["leather_darkest"], (sx - 5, cy - 3, 10, 6),
                  border_radius=1)
            _NS_gorath._rect(surface, _NS_gorath.PALETTE["leather_dark"], (sx - 4, cy - 2, 8, 4))
            _NS_gorath._rect(surface, _NS_gorath.PALETTE["leather_mid"], (sx - 3, cy - 1, 6, 1))

            # Blood drip on shoulder
            if side == -1:
                _NS_gorath._draw_blood_streak(surface, sx - 2, cy + 5, sx - 3, cy + 12, 2, 200)


    def _draw_gorath_head(surface, cx, cy, facing, phase):
        """Demon head with spiky hair and glowing red eyes."""
        # Neck
        _NS_gorath._rect(surface, _NS_gorath.PALETTE["skin_darkest"], (cx - 4, cy + 8, 8, 6))
        _NS_gorath._rect(surface, _NS_gorath.PALETTE["skin_dark"], (cx - 3, cy + 8, 6, 5))
        _NS_gorath._rect(surface, _NS_gorath.PALETTE["skin_mid"], (cx - 2, cy + 8, 4, 3))

        # Head shadow
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["shadow_deep"], (cx + 2, cy + 2), 12)

        # Base head
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_darkest"], (cx, cy), 11)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_dark"], (cx - 1, cy - 1), 9)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_mid"], (cx - 2, cy - 2), 7)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_light"], (cx - 3, cy - 4), 3)

        # Blood face-paint (Bloodseeker style - across the face)
        face_paint = [
            (cx - 8, cy - 2),
            (cx + 8, cy - 2),
            (cx + 7, cy + 4),
            (cx - 7, cy + 4),
        ]
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["blood_darkest"], face_paint)
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["blood_dark"], [
            (cx - 7, cy - 1), (cx + 7, cy - 1),
            (cx + 6, cy + 3), (cx - 6, cy + 3),
        ])
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["blood_mid"], [
            (cx - 5, cy), (cx + 5, cy),
            (cx + 4, cy + 2), (cx - 4, cy + 2),
        ])

        # Blood drips from face paint
        for offset in (-5, 0, 5):
            _NS_gorath._draw_blood_streak(surface, cx + offset, cy + 4,
                              cx + offset, cy + 8 + (offset % 2), 1, 200)

        # Glowing red eyes
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for side in (-1, 1):
            ex = cx + side * 4
            ey = cy + 1
            # Eye socket
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["shadow_deep"], (ex, ey), 3)
            # Glowing eye
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["eye_dark"], (ex, ey), 2)
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["eye_bright"], (ex, ey),
                      max(1, int(2 * eye_pulse)))
            _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["eye_hot"], (ex, ey), 1)
            # Glow halo
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["eye_bright"], int(120 * eye_pulse)),
                      (ex, ey), 5)

        # Mouth - fanged
        _NS_gorath._rect(surface, _NS_gorath.PALETTE["shadow_deep"], (cx - 4, cy + 6, 8, 2))
        # Fangs
        for tooth in (-3, -1, 1, 3):
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["bone_light"], [
                (cx + tooth, cy + 6),
                (cx + tooth + 1, cy + 8),
                (cx + tooth + 2, cy + 6),
            ])

        # SPIKY HAIR (Bloodseeker signature)
        _NS_gorath._draw_spiky_hair(surface, cx, cy - 6, phase)

        # Bone/tribal decorations on head
        for side in (-1, 1):
            # Side bone ornament
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["bone_dark"], [
                (cx + side * 9, cy - 4),
                (cx + side * 13, cy - 2),
                (cx + side * 12, cy + 2),
                (cx + side * 9, cy),
            ])
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["bone_mid"], [
                (cx + side * 10, cy - 3),
                (cx + side * 12, cy - 1),
                (cx + side * 11, cy + 1),
                (cx + side * 10, cy),
            ])


    def _draw_spiky_hair(surface, cx, cy, phase):
        """Spiky mohawk/hair like Bloodseeker."""
        # Main hair mass
        hair_base = [
            (cx - 10, cy + 4),
            (cx - 8, cy - 2),
            (cx - 3, cy - 6),
            (cx + 3, cy - 6),
            (cx + 8, cy - 2),
            (cx + 10, cy + 4),
        ]
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["hair_darkest"], hair_base)
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["hair_dark"], [
            (cx - 8, cy + 3),
            (cx - 6, cy - 1),
            (cx - 2, cy - 4),
            (cx + 2, cy - 4),
            (cx + 6, cy - 1),
            (cx + 8, cy + 3),
        ])

        # Individual spikes
        spikes = [
            (cx - 9, cy - 2, -13),
            (cx - 5, cy - 5, -10),
            (cx - 2, cy - 6, -14),
            (cx + 2, cy - 6, -13),
            (cx + 5, cy - 5, -11),
            (cx + 9, cy - 2, -14),
        ]
        for sx, sy, tip_y in spikes:
            sway = int(math.sin(phase * 0.5 + sx) * 1)
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["hair_darkest"], [
                (sx - 2, sy),
                (sx + 2, sy),
                (sx + sway, cy + tip_y),
            ])
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["hair_dark"], [
                (sx - 1, sy),
                (sx + 1, sy),
                (sx + sway, cy + tip_y + 2),
            ])
            # Highlight
            _NS_gorath._aaline(surface, _NS_gorath.PALETTE["hair_mid"],
                    (sx, sy), (sx + sway, cy + tip_y + 3), 1)


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Arms holding blades at rest."""
        sway = math.sin(phase * 0.7) * 2
        for side in (-1, 1):
            sh_x = cx + side * 12
            sh_y = cy + 2
            elbow_x = sh_x + side * 10
            elbow_y = cy + 12 + int(sway)
            hand_x = elbow_x + side * 6
            hand_y = elbow_y + 8

            _NS_gorath._draw_arm_segment(surface, sh_x, sh_y, elbow_x, elbow_y)
            _NS_gorath._draw_arm_segment(surface, elbow_x, elbow_y, hand_x, hand_y)
            _NS_gorath._draw_hand(surface, hand_x, hand_y)
            # Curved blade
            _NS_gorath._draw_curved_blade(surface, hand_x, hand_y, side, 0.3, phase)


    def _draw_attack_arms(surface, cx, cy, facing, phase, progress):
        """Arms swinging blades in attack."""
        sway = math.sin(phase * 0.7) * 1

        # Back arm (non-active, held ready)
        back_side = -facing
        bs_x = cx + back_side * 12
        bs_y = cy + 2
        be_x = bs_x + back_side * 8
        be_y = cy + 12
        bh_x = be_x + back_side * 6
        bh_y = be_y + 8
        _NS_gorath._draw_arm_segment(surface, bs_x, bs_y, be_x, be_y)
        _NS_gorath._draw_arm_segment(surface, be_x, be_y, bh_x, bh_y)
        _NS_gorath._draw_hand(surface, bh_x, bh_y)
        _NS_gorath._draw_curved_blade(surface, bh_x, bh_y, back_side, 0.4, phase)

        # Front arm - swinging blade
        fs_x = cx + facing * 12
        fs_y = cy + 2

        # Swing arc: wind up → swing → recovery
        if progress < 0.25:
            # Wind up (raise blade)
            t = progress / 0.25
            t = t * t * (3 - 2 * t)  # ease
            arm_angle = -1.5 + 0.3 * t
        elif progress < 0.55:
            # Swing forward (fast)
            t = (progress - 0.25) / 0.30
            t = 1 - (1 - t) ** 3  # ease out
            arm_angle = -1.2 + 2.4 * t
        else:
            # Recovery
            t = (progress - 0.55) / 0.45
            arm_angle = 1.2 - 1.0 * t

        arm_len = 16
        fe_x = fs_x + int(math.cos(arm_angle) * arm_len) * facing
        fe_y = fs_y + int(math.sin(arm_angle) * arm_len)
        fh_x = fe_x + int(math.cos(arm_angle) * 10) * facing
        fh_y = fe_y + int(math.sin(arm_angle) * 10)

        _NS_gorath._draw_arm_segment(surface, fs_x, fs_y, fe_x, fe_y)
        _NS_gorath._draw_arm_segment(surface, fe_x, fe_y, fh_x, fh_y)
        _NS_gorath._draw_hand(surface, fh_x, fh_y)

        # Big curved blade in swinging hand
        blade_angle = arm_angle + math.pi / 4 * facing
        _NS_gorath._draw_curved_blade_angled(surface, fh_x, fh_y, facing, blade_angle,
                                  phase, size=1.3)


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Muscular arm segment."""
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["shadow_deep"], (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 8)
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["skin_darkest"], (x1, y1), (x2, y2), 7)
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["skin_dark"], (x1, y1), (x2, y2), 5)
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["skin_mid"], (x1, y1), (x2, y2), 3)
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["skin_light"], (x1 - 1, y1), (x2 - 1, y2), 1)


    def _draw_hand(surface, x, y):
        """Clenched fist."""
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["shadow_deep"], (x + 1, y + 1), 5)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_darkest"], (x, y), 4)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_dark"], (x, y), 3)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["skin_mid"], (x - 1, y - 1), 2)
        # Wrist wrap
        _NS_gorath._rect(surface, _NS_gorath.PALETTE["leather_dark"], (x - 4, y - 5, 8, 3),
              border_radius=1)
        _NS_gorath._rect(surface, _NS_gorath.PALETTE["leather_mid"], (x - 3, y - 5, 6, 1))


    def _draw_curved_blade(surface, hx, hy, side, tilt, phase):
        """Curved blade (idle pose)."""
        # Blade extends downward and curves outward
        tip_x = hx + int(side * 8)
        tip_y = hy + 18
        mid_x = hx + int(side * 12)
        mid_y = hy + 10

        # Shadow
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["shadow_deep"], [
            (hx + 1, hy + 3),
            (hx + int(side * 4) + 1, hy + 4),
            (mid_x + 1, mid_y + 1),
            (tip_x + 1, tip_y + 1),
            (hx + int(side * 2) + 1, hy + 8),
        ])

        # Blade curved shape
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["metal_darkest"], [
            (hx, hy + 2),
            (hx + int(side * 5), hy + 3),
            (mid_x, mid_y),
            (tip_x, tip_y),
            (hx + int(side * 1), hy + 7),
        ])
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["metal_dark"], [
            (hx, hy + 3),
            (hx + int(side * 4), hy + 4),
            (mid_x - int(side), mid_y),
            (tip_x - int(side), tip_y - 1),
            (hx + int(side * 1), hy + 6),
        ])
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["metal_mid"], [
            (hx + int(side), hy + 4),
            (hx + int(side * 3), hy + 5),
            (mid_x - int(side * 2), mid_y),
            (tip_x - int(side * 2), tip_y - 2),
            (hx + int(side * 1), hy + 5),
        ])

        # Blade highlight (sharp edge)
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["metal_light"],
                (hx + int(side * 4), hy + 4),
                (tip_x - int(side), tip_y - 1), 1)

        # Blood on blade edge
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_darkest"], (mid_x, mid_y + 2), 3)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_mid"], (mid_x, mid_y + 2), 2)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_bright"], (mid_x - 1, mid_y + 1), 1)
        # Dripping blood
        _NS_gorath._draw_blood_droplet(surface, mid_x, mid_y + 6, 2, 220)


    def _draw_curved_blade_angled(surface, hx, hy, facing, angle, phase, size=1.0):
        """Larger curved blade for attack swing (angled)."""
        # Blade length varies with size
        blade_len = int(22 * size)
        curve = int(10 * size)

        # Compute blade points along angle
        dx = math.cos(angle) * facing
        dy = math.sin(angle)
        perp_x = -dy
        perp_y = dx * facing

        # Base near hand
        base1_x = hx + int(perp_x * 3)
        base1_y = hy + int(perp_y * 3)
        base2_x = hx - int(perp_x * 3)
        base2_y = hy - int(perp_y * 3)

        # Mid curve outward
        mid_x = hx + int(dx * blade_len * 0.55) + int(perp_x * curve)
        mid_y = hy + int(dy * blade_len * 0.55) + int(perp_y * curve)

        # Tip
        tip_x = hx + int(dx * blade_len)
        tip_y = hy + int(dy * blade_len)

        # Shadow
        shadow_pts = [
            (base1_x + 2, base1_y + 2),
            (mid_x + 2, mid_y + 2),
            (tip_x + 2, tip_y + 2),
            (base2_x + 2, base2_y + 2),
        ]
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["shadow_deep"], shadow_pts)

        # Blade
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["metal_darkest"], [
            (base1_x, base1_y), (mid_x, mid_y),
            (tip_x, tip_y), (base2_x, base2_y),
        ])
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["metal_dark"], [
            (base1_x - int(perp_x), base1_y - int(perp_y)),
            (mid_x - int(perp_x * 0.7), mid_y - int(perp_y * 0.7)),
            (tip_x, tip_y),
            (base2_x, base2_y),
        ])
        _NS_gorath._poly(surface, _NS_gorath.PALETTE["metal_mid"], [
            (base1_x - int(perp_x * 2), base1_y - int(perp_y * 2)),
            (mid_x - int(perp_x * 1.4), mid_y - int(perp_y * 1.4)),
            (tip_x, tip_y),
        ])

        # Sharp edge highlight
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["metal_shine"],
                (base1_x - int(perp_x * 2), base1_y - int(perp_y * 2)),
                (tip_x, tip_y), 1)

        # Blood covering blade
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["blood_darkest"], (base1_x, base1_y),
                (tip_x, tip_y), 3)
        _NS_gorath._aaline(surface, _NS_gorath.PALETTE["blood_bright"], (mid_x, mid_y), (tip_x, tip_y), 2)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_hot"], (mid_x, mid_y), 3)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_glow"], (mid_x, mid_y), 1)


    def _draw_body_blood_drips(surface, cx, cy, phase):
        """Blood drips on body."""
        drips = [
            (cx - 8, cy + 5, 0),
            (cx + 6, cy + 8, 0.3),
            (cx - 3, cy - 5, 0.6),
            (cx + 10, cy - 2, 0.9),
        ]
        for dx, dy, offset in drips:
            t = (phase * 0.5 + offset) % 1.0
            drip_y = dy + int(t * 15)
            alpha = int(255 * (1 - t))
            if alpha > 20:
                _NS_gorath._draw_blood_droplet(surface, dx, drip_y, 2, alpha)


    # ===================================================================
    # FLOATING EFFECTS (replaces legs)
    # ===================================================================
    def _draw_blood_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Blood mist wisps rising from below."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(32, 3, -4):
            alpha = int((32 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_gorath.PALETTE["blood_dark"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising blood wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.6 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 26)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_darkest"], alpha), (sx, sy), 5)
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_dark"], alpha), (sx, sy - 2), 3)
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], alpha), (sx, sy - 3), 1)

        # Floating blood droplets
        for i in range(6):
            angle = phase * 0.7 + i * math.pi / 3
            r = 22 + int(math.sin(phase + i * 1.3) * 6)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 8)
            _NS_gorath._draw_blood_droplet(surface, sx, sy, 2, 200)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 140 - i * 25)
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_dark"], alpha),
                          (sx, sy), max(2, 5 - i))
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], alpha // 2),
                          (sx, sy), max(1, 3 - i))


    def _draw_blood_trail(surface, cx, cy, phase, facing):
        """Blood splashes on ground while walking."""
        for i in range(4):
            sx = cx - (i + 1) * 12 * facing
            sy = cy + int(math.cos(phase + i) * 2)
            alpha = max(0, 180 - i * 30)
            _NS_gorath._draw_blood_splatter(surface, sx, sy, max(2, 5 - i),
                                 seed=i, alpha=alpha)


    def _draw_shadow(surface, x, y, lift=0):
        """Ground shadow. ORIGINAL-MAX: cache + reaktif (menyusut saat
        badan terangkat, dasar tetap menapak tanah)."""
        NS = _NS_gorath
        if NS._shadow_cache is None:
            shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
            for radius in range(10, 0, -1):
                alpha = max(0, (10 - radius) * 16)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
                )
            pygame.draw.ellipse(shadow, (*NS.PALETTE["blood_darkest"], 100),
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


    def _draw_blood_aura(surface, x, y, phase, active_skill):
        """Background aura."""
        NS = _NS_gorath
        if NS._aura_cache is None:
            aura = pygame.Surface((180, 160), pygame.SRCALPHA)
            for radius in range(72, 5, -4):
                alpha = int((72 - radius) * 1.4)
                if alpha > 0:
                    NS._aacircle(aura, (*NS.PALETTE["blood_darkest"],
                                        min(255, alpha)), (90, 80), radius)
            NS._aura_cache = aura
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.5 if active_skill == "q" else 1.0
        a = int(255 * min(1.0, pulse * strength))
        spr = NS._aura_cache.copy()
        spr.set_alpha(a)
        surface.blit(spr, (x - 90, y - 80))


    def _draw_ground_blood_pool(surface, x, y, phase, active_skill):
        """Blood pool on ground beneath Gorath."""
        pulse = math.sin(phase * 0.8) * 0.15 + 0.85
        pool = pygame.Surface((130, 40), pygame.SRCALPHA)
        # Base pool
        pygame.draw.ellipse(pool, (*_NS_gorath.PALETTE["blood_darkest"], int(200 * pulse)),
                            (10, 12, 110, 20))
        pygame.draw.ellipse(pool, (*_NS_gorath.PALETTE["blood_dark"], int(180 * pulse)),
                            (20, 15, 90, 14))
        pygame.draw.ellipse(pool, (*_NS_gorath.PALETTE["blood_mid"], int(120 * pulse)),
                            (30, 17, 70, 10))

        # Irregular splashes around
        for i in range(8):
            angle = i * math.pi / 4 + phase * 0.1
            px = 65 + int(math.cos(angle) * 50)
            py = 22 + int(math.sin(angle) * 12)
            r = 3 + (i % 3)
            pygame.draw.ellipse(pool, (*_NS_gorath.PALETTE["blood_dark"], 180),
                                (px - r, py - r // 2, r * 2, r))

        surface.blit(pool, (x - 65, y - 20))


    def _draw_blade_swing_arc(surface, x, y, facing, progress):
        """Blade swing motion trail."""
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
            px = 70 + int(math.cos(angle) * 50) * facing
            py = 55 + int(math.sin(angle) * 38)
            alpha = int((200 - i * 10) * visibility)
            if alpha <= 0:
                continue
            _NS_gorath._aacircle(arc, (*_NS_gorath.PALETTE["blood_darkest"], alpha), (px, py), 8)
            _NS_gorath._aacircle(arc, (*_NS_gorath.PALETTE["blood_mid"], alpha), (px, py), 5)
            _NS_gorath._aacircle(arc, (*_NS_gorath.PALETTE["blood_bright"], alpha), (px, py), 3)
            _NS_gorath._aacircle(arc, (*_NS_gorath.PALETTE["blood_hot"], min(255, alpha)), (px, py), 1)
        surface.blit(arc, (x - 70, y - 55))


    def _draw_swing_impact(surface, x, y, facing, progress):
        """Impact splash at end of swing."""
        if progress < 0.45 or progress > 0.85:
            return
        t = (progress - 0.45) / 0.40
        intensity = math.sin(t * math.pi)

        impact_x = x + 35 * facing
        impact_y = y + 3
        alpha = int(230 * intensity)
        radius = int(8 + intensity * 22)

        _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_dark"], alpha // 2),
                  (impact_x, impact_y), radius + 4)
        _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], alpha),
                  (impact_x, impact_y), radius, 3)

        # Splash droplets
        for i in range(8):
            angle = i * math.pi / 4 + progress * 3
            dx = impact_x + int(math.cos(angle) * radius * 1.2)
            dy = impact_y + int(math.sin(angle) * radius * 0.9)
            _NS_gorath._draw_blood_droplet(surface, dx, dy, 3, alpha)


    # ===================================================================
    # SKILL Q: BLOODRAGE
    # ===================================================================
    def _draw_bloodrage(surface, boss, x, y, timer, phase):
        """Self-buff — flame-like blood aura around Gorath."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 3) * 0.3 + 0.7

        # Flame tongues rising around body
        for i in range(10):
            angle = phase * 0.5 + i * math.pi * 2 / 10
            base_x = x + int(math.cos(angle) * 20)
            base_y = y + 20 + int(math.sin(angle) * 5)
            flame_h = int(20 + math.sin(phase * 2 + i) * 8)

            # Flame shape
            for h in range(flame_h):
                t = h / max(1, flame_h)
                w = int(4 * (1 - t * 0.7))
                fx = base_x + int(math.sin(phase * 3 + i + t * 5) * 2)
                fy = base_y - h
                alpha = int(200 * pulse * (1 - t * 0.5))
                if t < 0.3:
                    color = _NS_gorath.PALETTE["blood_darkest"]
                elif t < 0.6:
                    color = _NS_gorath.PALETTE["blood_mid"]
                else:
                    color = _NS_gorath.PALETTE["blood_hot"]
                _NS_gorath._aacircle(surface, (*color, alpha), (fx, fy), max(1, w))

        # Inner intense glow around body
        for radius in range(30, 5, -3):
            alpha = int((30 - radius) * 4 * pulse)
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_dark"], min(255, alpha)),
                      (x, y), radius)

        # Rising blood particles
        for i in range(12):
            t = (phase * 0.6 + i * 0.08) % 1.0
            px = x + int(math.cos(i * 2.5 + phase) * 25)
            py = y + 20 - int(t * 40)
            alpha = int(255 * (1 - t))
            if alpha > 0:
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], alpha), (px, py), 2)
                _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_hot"], alpha), (px, py), 1)


    # ===================================================================
    # SKILL W: BLOODRITE (ranged rain of blood spikes)
    # ===================================================================
    def _draw_bloodrite_ground(surface, boss, x, y, timer, phase):
        """Warning circle at target location."""
        tx, ty = _NS_gorath._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 60))
        pulse = math.sin(phase * 3) * 0.3 + 0.7

        radius = int(34 + progress * 18)
        # Warning ring (ORIGINAL-MAX lebih besar & terang)
        _NS_gorath._ellipse(surface, (*_NS_gorath.PALETTE["blood_darkest"], int(220 * pulse)),
                 (tx - radius, ty - radius // 2, radius * 2, radius), 3)
        _NS_gorath._ellipse(surface, (*_NS_gorath.PALETTE["blood_mid"], int(170 * pulse)),
                 (tx - radius + 4, ty - radius // 2 + 2,
                  radius * 2 - 8, radius - 4), 2)
        _NS_gorath._ellipse(surface, (*_NS_gorath.PALETTE["blood_bright"], int(140 * pulse)),
                 (tx - radius + 8, ty - radius // 2 + 4,
                  radius * 2 - 16, radius - 8), 1)


    def _draw_bloodrite(surface, boss, x, y, timer, phase):
        """Blood spikes erupting at target."""
        tx, ty = _NS_gorath._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 60))

        # Spawn projectile at start
        if progress < 0.1 and not getattr(boss, "_gor_bloodrite_spawned", False):
            for i in range(3):
                offset_x = (i - 1) * 25
                _NS_gorath._spawn_projectile(boss, x, y - 10, tx + offset_x, ty)
            boss._gor_bloodrite_spawned = True
        if progress > 0.4:
            boss._gor_bloodrite_spawned = False

        # After 0.5 progress, spikes erupt
        if progress > 0.4:
            erupt_t = min(1.0, (progress - 0.4) / 0.3)
            radius = 45
            for i in range(12):
                angle = i * math.pi * 2 / 12
                spike_x = tx + int(math.cos(angle) * radius * 0.7)
                spike_y = ty + int(math.sin(angle) * radius * 0.4)
                spike_h = int(20 * erupt_t)

                # Blood spike
                _NS_gorath._poly(surface, _NS_gorath.PALETTE["blood_darkest"], [
                    (spike_x - 3, spike_y),
                    (spike_x + 3, spike_y),
                    (spike_x, spike_y - spike_h),
                ])
                _NS_gorath._poly(surface, _NS_gorath.PALETTE["blood_dark"], [
                    (spike_x - 2, spike_y),
                    (spike_x + 2, spike_y),
                    (spike_x, spike_y - spike_h + 2),
                ])
                _NS_gorath._poly(surface, _NS_gorath.PALETTE["blood_bright"], [
                    (spike_x - 1, spike_y),
                    (spike_x + 1, spike_y),
                    (spike_x, spike_y - spike_h + 4),
                ])
                # Tip highlight
                _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_hot"],
                          (spike_x, spike_y - spike_h + 2), 1)

            # Central spike (bigger)
            big_h = int(30 * erupt_t)
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["blood_darkest"], [
                (tx - 5, ty),
                (tx + 5, ty),
                (tx, ty - big_h),
            ])
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["blood_mid"], [
                (tx - 3, ty),
                (tx + 3, ty),
                (tx, ty - big_h + 3),
            ])
            _NS_gorath._poly(surface, _NS_gorath.PALETTE["blood_bright"], [
                (tx - 1, ty),
                (tx + 1, ty),
                (tx, ty - big_h + 5),
            ])

            # Blood splash particles
            for i in range(8):
                angle = i * math.pi / 4 + phase
                px = tx + int(math.cos(angle) * 30 * erupt_t)
                py = ty + int(math.sin(angle) * 15 * erupt_t) - 5
                _NS_gorath._draw_blood_droplet(surface, px, py, 2, int(255 * erupt_t))


    # ===================================================================
    # SKILL E: THIRST (highlight enemy from distance)
    # ===================================================================
    def _draw_thirst(surface, boss, x, y, timer, phase):
        """Red highlighting beam / marker on target."""
        tx, ty = _NS_gorath._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 35))
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7

        # Line of sight beam (blood-red thin line)
        start_x = x + 5 * boss.direction
        start_y = y - 10
        for i in range(3):
            offset = (i - 1) * 2
            alpha = int(80 - i * 20)
            _NS_gorath._aaline(surface, (*_NS_gorath.PALETTE["blood_bright"], alpha),
                    (start_x, start_y + offset), (tx, ty + offset), 2)
        _NS_gorath._aaline(surface, (*_NS_gorath.PALETTE["blood_hot"], 200), (start_x, start_y), (tx, ty), 1)

        # Target marker - crosshair
        marker_r = int(15 + math.sin(phase * 3) * 3)

        # Outer ring
        _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_darkest"], 220),
                  (tx, ty), marker_r + 2, 3)
        _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], int(230 * pulse)),
                  (tx, ty), marker_r, 2)
        _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_hot"], int(255 * pulse)),
                  (tx, ty), marker_r - 3, 1)

        # Cross lines
        for angle in (0, math.pi / 2, math.pi, math.pi * 1.5):
            x1 = tx + int(math.cos(angle) * (marker_r - 3))
            y1 = ty + int(math.sin(angle) * (marker_r - 3))
            x2 = tx + int(math.cos(angle) * (marker_r + 6))
            y2 = ty + int(math.sin(angle) * (marker_r + 6))
            _NS_gorath._aaline(surface, _NS_gorath.PALETTE["blood_bright"], (x1, y1), (x2, y2), 2)
            _NS_gorath._aaline(surface, _NS_gorath.PALETTE["blood_hot"], (x1, y1), (x2, y2), 1)

        # Central dot
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_hot"], (tx, ty), 3)
        _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_light"], (tx, ty), 1)

        # Blood-tracking particles going from Gorath to target
        for i in range(5):
            t = (phase * 0.5 + i * 0.2) % 1.0
            px = int(start_x + (tx - start_x) * t)
            py = int(start_y + (ty - start_y) * t)
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], 200), (px, py), 3)
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_hot"], 240), (px, py), 1)


    # ===================================================================
    # SKILL R: RUPTURE (chained blood damage)
    # ===================================================================
    def _draw_rupture_ground(surface, boss, x, y, timer, phase):
        """Ground blood pool at target."""
        tx, ty = _NS_gorath._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 90))
        pulse = math.sin(phase * 2) * 0.2 + 0.8

        radius = int(20 + progress * 25)
        _NS_gorath._ellipse(surface, (*_NS_gorath.PALETTE["blood_darkest"], int(200 * pulse)),
                 (tx - radius, ty - radius // 3, radius * 2, radius // 1.5))
        _NS_gorath._ellipse(surface, (*_NS_gorath.PALETTE["blood_dark"], int(180 * pulse)),
                 (tx - radius + 4, ty - radius // 3 + 2,
                  radius * 2 - 8, radius // 1.5 - 4))


    def _draw_rupture(surface, boss, x, y, timer, phase):
        """Blood chain connecting to target, exploding at target."""
        tx, ty = _NS_gorath._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 90))

        start_x = x + 12 * boss.direction
        start_y = y - 10

        # Blood chain line
        segments = 12
        prev = (start_x, start_y)
        for i in range(1, segments + 1):
            t = i / segments
            mx = start_x + (tx - start_x) * t
            my = start_y + (ty - start_y) * t
            # Add wiggle
            wiggle = math.sin(phase * 3 + i) * 3
            mx += wiggle if i < segments else 0
            curr = (int(mx), int(my))

            _NS_gorath._aaline(surface, _NS_gorath.PALETTE["blood_darkest"], prev, curr, 5)
            _NS_gorath._aaline(surface, _NS_gorath.PALETTE["blood_mid"], prev, curr, 3)
            _NS_gorath._aaline(surface, _NS_gorath.PALETTE["blood_bright"], prev, curr, 1)

            # Blood droplets along chain
            if i % 3 == 0:
                _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_dark"], curr, 4)
                _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_bright"], curr, 2)
                _NS_gorath._aacircle(surface, _NS_gorath.PALETTE["blood_hot"], curr, 1)
            prev = curr

        # Explosion at target
        if progress > 0.4:
            explosion_t = min(1.0, (progress - 0.4) / 0.5)
            radius = int(15 + explosion_t * 30)
            pulse = math.sin(phase * 4) * 0.3 + 0.7

            # Outer blast
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_darkest"], int(200 * pulse)),
                      (tx, ty), radius + 5)
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_mid"], int(220 * pulse)),
                      (tx, ty), radius)
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_bright"], int(240 * pulse)),
                      (tx, ty), max(1, radius - 8))
            _NS_gorath._aacircle(surface, (*_NS_gorath.PALETTE["blood_hot"], int(255 * pulse)),
                      (tx, ty), max(1, radius - 15))

            # Spikes bursting outward
            for i in range(10):
                angle = i * math.pi / 5 + phase * 0.5
                sp_len = int(radius * 1.3)
                sx1 = tx + int(math.cos(angle) * radius * 0.5)
                sy1 = ty + int(math.sin(angle) * radius * 0.5)
                sx2 = tx + int(math.cos(angle) * sp_len)
                sy2 = ty + int(math.sin(angle) * sp_len)
                _NS_gorath._aaline(surface, _NS_gorath.PALETTE["blood_darkest"], (sx1, sy1), (sx2, sy2), 4)
                _NS_gorath._aaline(surface, _NS_gorath.PALETTE["blood_bright"], (sx1, sy1), (sx2, sy2), 2)
                # Tip droplet
                _NS_gorath._draw_blood_droplet(surface, sx2, sy2, 2, 220)


    # ===================================================================
    # Backward compatible alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_gorath.draw_gorath(surface, boss, x, y)


def draw_gorath(surface, boss, x, y):
    _NS_gorath.draw_gorath(surface, boss, x, y)
