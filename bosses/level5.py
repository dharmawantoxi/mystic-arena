"""
bosses/level5.py - Semua boss Level 5

Gabungan dari 4 file terpisah:
  - nyxara               (mini boss)
  - gravefang            (mini boss)
  - vhalzun              (mini boss)
  - krobellus            (TRUE BOSS)

Tiap boss dibungkus dalam kelas namespace `_NS_<nama>`
supaya PALETTE dan fungsi helper-nya TIDAK saling
menimpa - 91 simbol bentrok antar file boss, termasuk
PALETTE, _aacircle, _draw_shadow, _target_position.

Kode di dalam tiap namespace TIDAK diubah isinya;
hanya referensi antar-simbol yang diberi prefix.

Entry point publik ada di bagian paling bawah file.
"""

import math
import random
import pygame

# Penanda: file ini berisi BANYAK boss (1 true + 3 mini).
# Dipakai heroes/__init__.py agar tidak menebak fungsi draw_*
# secara longgar, yang bisa mengembalikan boss yang salah.
_IS_LEVEL_BUNDLE = True


# ====================================================================
# NYXARA
# ====================================================================
class _NS_nyxara:
    """Namespace nyxara - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Pugna inspired yellow-green nether
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin - malformed green/olive
        "skin_darkest":   (25,  38,  15),
        "skin_dark":      (55,  75,  30),
        "skin_mid":       (95, 120,  50),
        "skin_light":     (140, 165,  75),
        "skin_shine":     (185, 210, 110),

        # Robe - dark brown/purple armored
        "robe_darkest":   (18,  10,  18),
        "robe_dark":      (38,  22,  38),
        "robe_mid":       (68,  38,  58),
        "robe_light":     (105, 65,  90),
        "robe_high":      (145, 100, 125),

        # Leather/inner
        "leather_dark":   (28,  18,  12),
        "leather_mid":    (55,  35,  20),
        "leather_light":  (90,  62,  35),

        # Nether green - main magical color (yellow-green)
        "nether_darkest": (25,  35,   5),
        "nether_dark":    (70,  95,  15),
        "nether_mid":     (140, 180, 30),
        "nether_light":   (200, 240, 60),
        "nether_bright":  (230, 255, 120),
        "nether_hot":     (245, 255, 180),
        "nether_white":   (255, 255, 220),

        # Skull - bone
        "bone_dark":      (75,  85,  50),
        "bone_mid":       (130, 145, 90),
        "bone_light":     (185, 200, 140),
        "bone_shine":     (225, 235, 190),

        # Gold trim
        "gold_dark":      (90,  62,  15),
        "gold_mid":       (165, 125, 35),
        "gold_light":     (225, 185, 70),
        "gold_shine":     (250, 225, 140),

        # Horns / red accent
        "horn_dark":      (60,  20,  15),
        "horn_mid":       (110, 40,  25),
        "horn_light":     (170, 75,  40),
        "horn_high":      (220, 130, 70),

        # Eye glow
        "eye_dark":       (70,  95,   5),
        "eye_mid":        (170, 220, 30),
        "eye_bright":     (220, 250, 100),
        "eye_hot":        (245, 255, 200),

        # Wood staff
        "wood_dark":      (35,  22,  15),
        "wood_mid":       (65,  42,  22),
        "wood_light":     (100, 70,  40),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   6,   3),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_nyxara._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_nyxara.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_nyxara._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
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
        color = _NS_nyxara._clamp(color)
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
        color = _NS_nyxara._clamp(color)
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
        color = _NS_nyxara._clamp(color)
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
        return int(x + 200 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Nether particle helpers
    # ---------------------------------------------------------------------------
    def _draw_nether_orb(surface, x, y, size, phase, alpha=255):
        """Draw a glowing nether orb (yellow-green)."""
        flick = math.sin(phase * 3) * 0.15 + 1.0
        s = int(size * flick)
        if s < 1:
            return
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_darkest"], alpha // 3), (x, y), s + 4)
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_dark"], alpha // 2), (x, y), s + 2)
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_mid"], alpha), (x, y), s)
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_light"], alpha), (x, y - 1),
                  max(1, s - 2))
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_bright"], min(255, alpha)),
                  (x, y - 2), max(1, s - 4))
        if s > 3:
            _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_hot"], min(255, alpha)),
                      (x, y - 2), max(1, s - 6))
        if s > 5:
            _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_white"], min(255, alpha)),
                      (x, y - 2), max(1, s - 8))


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM
    # ---------------------------------------------------------------------------
    class NetherOrbProjectile:
        """Basic nether orb - slow bright yellow-green orb."""
        def __init__(self, sx, sy, tx, ty, speed=5.0):
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
            if len(self.trail) > 14:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 3:
                return
            # Long bright trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 14)
                r = max(1, 7 - (len(self.trail) - i) // 2)
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_dark"], alpha), (tx, ty), r + 3)
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_mid"], alpha), (tx, ty), r + 1)
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_light"], alpha // 2), (tx, ty), r)

            if self.alive:
                px, py = int(self.x), int(self.y)
                _NS_nyxara._draw_nether_orb(surface, px, py, 8, phase, 250)
                # Sparks
                for i in range(4):
                    angle = phase * 4 + i * math.pi / 2
                    sx = px + int(math.cos(angle) * 12)
                    sy = py + int(math.sin(angle) * 12)
                    _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_hot"], (sx, sy), 1)
                    _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_white"], (sx, sy), 1)


    class NetherBlastProjectile:
        """Q - Larger, faster orb with big impact."""
        def __init__(self, sx, sy, tx, ty, speed=7.0):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.trail = []
            self.exploded = False
            self.explosion_frame = 0

        def update(self):
            if self.exploded:
                self.explosion_frame += 1
                if self.explosion_frame > 20:
                    self.alive = False
                return
            self.age += 1
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < self.speed + 4:
                self.exploded = True
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 14:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if self.exploded:
                # Big explosion
                t = self.explosion_frame / 20
                radius = int(20 + t * 40)
                alpha = int(240 * (1 - t))
                px, py = int(self.tx), int(self.ty)

                # Multi-ring explosion
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_dark"], alpha // 2),
                          (px, py), radius + 8)
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_mid"], alpha),
                          (px, py), radius + 4)
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_light"], alpha),
                          (px, py), radius)
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_bright"], alpha),
                          (px, py), max(1, radius - 8))
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_hot"], alpha),
                          (px, py), max(1, radius - 15))
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_white"], alpha),
                          (px, py), max(1, radius - 22))

                # Ground ring
                _NS_nyxara._ellipse(surface, (*_NS_nyxara.PALETTE["nether_bright"], alpha),
                         (px - radius, py + 10 - radius // 4,
                          radius * 2, radius // 2), 2)

                # Radial sparks
                for i in range(10):
                    angle = i * math.pi * 2 / 10 + phase
                    spark_r = radius + 5
                    sx = px + int(math.cos(angle) * spark_r)
                    sy = py + int(math.sin(angle) * spark_r)
                    _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_hot"], (sx, sy), 2)
                    _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_white"], (sx, sy), 1)
                return

            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 14)
                r = max(1, 8 - (len(self.trail) - i) // 2)
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_dark"], alpha), (tx, ty), r + 3)
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_mid"], alpha), (tx, ty), r + 1)
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_light"], alpha // 2), (tx, ty), r)

            if self.alive:
                px, py = int(self.x), int(self.y)
                _NS_nyxara._draw_nether_orb(surface, px, py, 10, phase, 250)
                # Extra bright core
                _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_white"], (px, py), 3)


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_nx_last_x"):
            boss._nx_last_x = boss.x
            boss._nx_last_y = boss.y
            return False
        dx = abs(boss.x - boss._nx_last_x)
        dy = abs(boss.y - boss._nx_last_y)
        boss._nx_last_x = boss.x
        boss._nx_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_nx_prev_timer", 0))
        active = bool(getattr(boss, "_nx_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._nx_attack_active = True
            boss._nx_attack_frame = 0
            active = True
        elif active:
            boss._nx_attack_frame = int(getattr(boss, "_nx_attack_frame", 0)) + 1
            if boss._nx_attack_frame > cooldown:
                boss._nx_attack_active = False
                boss._nx_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._nx_attack_active = False
            boss._nx_attack_frame = 0
            active = False

        boss._nx_prev_timer = timer
        boss._nx_attack_progress = (
            min(1.0, getattr(boss, "_nx_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_nx_projectiles"):
            boss._nx_projectiles = []
        for proj in boss._nx_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._nx_projectiles = [p for p in boss._nx_projectiles
                                if p.alive or p.age < 8]


    def _spawn_basic_projectile(boss, x, y):
        if not hasattr(boss, "_nx_projectiles"):
            boss._nx_projectiles = []
        tx, ty = _NS_nyxara._target_position(boss, x, y)
        sx = x + 22 * getattr(boss, "direction", 1)
        sy = y - 12
        boss._nx_projectiles.append(_NS_nyxara.NetherOrbProjectile(sx, sy, tx, ty, speed=5.0))


    def _spawn_blast_projectile(boss, x, y):
        if not hasattr(boss, "_nx_projectiles"):
            boss._nx_projectiles = []
        tx, ty = _NS_nyxara._target_position(boss, x, y)
        sx = x + 22 * getattr(boss, "direction", 1)
        sy = y - 12
        boss._nx_projectiles.append(_NS_nyxara.NetherBlastProjectile(sx, sy, tx, ty, speed=6.5))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_nyxara(surface, boss, x, y):
        """Entry point."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_nyxara._detect_moving(boss)
        _NS_nyxara._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_nx_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # ---------- Background layers ----------
        _NS_nyxara._draw_nether_aura(surface, x, y, pulse)
        _NS_nyxara._draw_ground_runes(surface, x, y + 38, pulse, active_skill)

        # ---------- Skill ground effects ----------
        if active_skill == "e":
            _NS_nyxara._draw_nether_ward_ground(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if attacking:
            _NS_nyxara._draw_nyxara_attack(surface, boss, x, y)
        elif moving:
            _NS_nyxara._draw_nyxara_walk(surface, boss, x, y)
        else:
            _NS_nyxara._draw_nyxara_idle(surface, boss, x, y)

        # ---------- Projectiles ----------
        _NS_nyxara._manage_projectiles(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "q":
            _NS_nyxara._draw_nether_blast_cast(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_nyxara._draw_decrepify(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nyxara._draw_nether_ward(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyxara._draw_life_drain(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_nyxara_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_nyxara._draw_shadow(surface, x, y + 48)
        _NS_nyxara._draw_floating_mist(surface, x, y + 35, boss.pulse)
        _NS_nyxara._draw_nyxara_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_nyxara_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(abs(math.sin(phase * 1.3)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_nyxara._draw_shadow(surface, x + sway, y + 48)
        _NS_nyxara._draw_floating_mist(surface, x + sway, y + 35, phase, trail=True,
                            facing=boss.direction)
        _NS_nyxara._draw_nyxara_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_nyxara_attack(surface, boss, x, y):
        progress = getattr(boss, "_nx_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        if 0.28 < progress < 0.35 and not getattr(boss, "_nx_proj_spawned", False):
            _NS_nyxara._spawn_basic_projectile(boss, x, y)
            boss._nx_proj_spawned = True
        if progress < 0.1 or progress > 0.9:
            boss._nx_proj_spawned = False

        recoil = int(math.sin(progress * math.pi) * 3) * -boss.direction
        _NS_nyxara._draw_shadow(surface, x + recoil, y + 48)
        _NS_nyxara._draw_floating_mist(surface, x + recoil, y + 35, boss.pulse, intense=True)
        _NS_nyxara._draw_nyxara_body(surface, x + recoil, y, boss.direction, boss.pulse,
                         "attack", progress)
        _NS_nyxara._draw_cast_flash(surface, x + recoil, y, boss.direction, progress)


    # ===================================================================
    # BODY RENDERING – HD detailed Pugna
    # ===================================================================
    def _draw_nyxara_body(surface, cx, cy, facing, phase, action,
                         attack_progress=0):
        """Main body composition - small, chubby, malformed."""
        # Skull staff (behind body)
        _NS_nyxara._draw_skull_staff(surface, cx + facing * 14, cy - 5, facing, phase)

        # Small chubby robe body
        _NS_nyxara._draw_robe(surface, cx, cy + 5, phase)

        # Torso
        _NS_nyxara._draw_torso(surface, cx, cy - 8, phase)

        # Cape/collar
        _NS_nyxara._draw_cape_collar(surface, cx, cy - 12, phase)

        # Arms
        if action == "attack":
            _NS_nyxara._draw_casting_arms(surface, cx, cy - 5, facing, phase, attack_progress)
        else:
            _NS_nyxara._draw_idle_arms(surface, cx, cy - 5, facing, phase)

        # Head with horned crown (small and monstrous)
        _NS_nyxara._draw_head(surface, cx, cy - 25, facing, phase)

        # Body particles
        _NS_nyxara._draw_body_particles(surface, cx, cy, phase)


    def _draw_robe(surface, cx, cy, phase):
        """Small chubby robe."""
        sway = int(math.sin(phase * 0.7) * 2)

        # Outermost robe - short and wide
        robe_outer = [
            (cx - 16, cy),
            (cx + 16, cy),
            (cx + 20 + sway, cy + 10),
            (cx + 18, cy + 22),
            (cx + 12, cy + 30),
            (cx + 4, cy + 34),
            (cx - 4, cy + 34),
            (cx - 12, cy + 30),
            (cx - 18, cy + 22),
            (cx - 20 - sway, cy + 10),
        ]
        _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in robe_outer])
        _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["robe_darkest"], robe_outer)

        # Mid robe
        robe_mid = [
            (cx - 14, cy + 2),
            (cx + 14, cy + 2),
            (cx + 17 + sway, cy + 10),
            (cx + 15, cy + 20),
            (cx + 10, cy + 27),
            (cx - 10, cy + 27),
            (cx - 15, cy + 20),
            (cx - 17 - sway, cy + 10),
        ]
        _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["robe_dark"], robe_mid)

        # Inner
        robe_inner = [
            (cx - 11, cy + 4),
            (cx + 11, cy + 4),
            (cx + 13 + sway, cy + 10),
            (cx + 11, cy + 18),
            (cx + 7, cy + 24),
            (cx - 7, cy + 24),
            (cx - 11, cy + 18),
            (cx - 13 - sway, cy + 10),
        ]
        _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["robe_mid"], robe_inner)

        # Vertical fold lines
        for xoff in (-8, -3, 3, 8):
            _NS_nyxara._aaline(surface, _NS_nyxara.PALETTE["robe_darkest"],
                    (cx + xoff, cy + 4), (cx + xoff, cy + 24), 1)

        # Nether glow beneath
        for i in range(5):
            alpha = 60 - i * 10
            _NS_nyxara._ellipse(surface, (*_NS_nyxara.PALETTE["nether_mid"], alpha),
                     (cx - 20 + i * 2, cy + 28 - i, 40 - i * 4, 8))

        # Belt sash - purple/dark
        _NS_nyxara._rect(surface, _NS_nyxara.PALETTE["leather_dark"], (cx - 14, cy - 1, 28, 5))
        _NS_nyxara._rect(surface, _NS_nyxara.PALETTE["leather_mid"], (cx - 12, cy, 24, 3))
        _NS_nyxara._rect(surface, _NS_nyxara.PALETTE["leather_light"], (cx - 10, cy + 1, 20, 1))

        # Belt buckle - green gem
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["gold_dark"], (cx, cy + 1), 4)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["gold_mid"], (cx, cy + 1), 3)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_dark"], (cx, cy + 1), 2)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_bright"], (cx, cy + 1),
                  max(1, int(2 * pulse)))
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_hot"], (cx, cy + 1), 1)


    def _draw_torso(surface, cx, cy, phase):
        """Chest section - leather with green symbol."""
        # Chest area
        _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["shadow_deep"], [
            (cx - 12 + 2, cy - 8 + 2), (cx + 12 + 2, cy - 8 + 2),
            (cx + 13 + 2, cy + 12 + 2), (cx + 4 + 2, cy + 16 + 2),
            (cx - 4 + 2, cy + 16 + 2), (cx - 13 + 2, cy + 12 + 2),
        ])

        chest = [
            (cx - 12, cy - 8), (cx + 12, cy - 8),
            (cx + 13, cy + 12), (cx + 4, cy + 16),
            (cx - 4, cy + 16), (cx - 13, cy + 12),
        ]
        _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["leather_dark"], chest)
        _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["leather_mid"], [
            (cx - 10, cy - 6), (cx + 10, cy - 6),
            (cx + 11, cy + 10), (cx + 4, cy + 14),
            (cx - 4, cy + 14), (cx - 11, cy + 10),
        ])
        _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["leather_light"], [
            (cx - 7, cy - 3), (cx + 7, cy - 3),
            (cx + 8, cy + 7), (cx + 3, cy + 11),
            (cx - 3, cy + 11), (cx - 8, cy + 7),
        ])

        # Center green nether symbol/gem (glowing)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_darkest"], (cx, cy + 3), 5)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_dark"], (cx, cy + 3), 4)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_mid"], (cx, cy + 3),
                  max(1, int(4 * pulse)))
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_bright"], (cx, cy + 3),
                  max(1, int(3 * pulse)))
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_hot"], (cx, cy + 3),
                  max(1, int(2 * pulse)))
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_white"], (cx, cy + 3), 1)

        # Gold outline of chest gem
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["gold_mid"], (cx, cy + 3), 5, 1)

        # Gold trim on chest edges
        _NS_nyxara._aaline(surface, _NS_nyxara.PALETTE["gold_dark"], (cx - 12, cy - 8), (cx - 13, cy + 12), 1)
        _NS_nyxara._aaline(surface, _NS_nyxara.PALETTE["gold_dark"], (cx + 12, cy - 8), (cx + 13, cy + 12), 1)


    def _draw_cape_collar(surface, cx, cy, phase):
        """Shoulder pauldrons and collar - horned."""
        for side in (-1, 1):
            sx = cx + side * 13
            # Shadow
            _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["shadow_deep"], (sx + 2, cy + 2), 8)
            # Pauldron base
            _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["robe_darkest"], (sx, cy), 7)
            _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["robe_dark"], (sx - side, cy - 1), 5)
            _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["robe_mid"], (sx - side, cy - 2), 3)

            # Small spike on shoulder
            _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["horn_dark"], [
                (sx - 2, cy - 5),
                (sx + 2, cy - 5),
                (sx + side * 3, cy - 12),
            ])
            _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["horn_mid"], [
                (sx - 1, cy - 5),
                (sx + 1, cy - 5),
                (sx + side * 2, cy - 10),
            ])
            # Tip highlight
            _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["horn_light"],
                      (sx + side * 3, cy - 12), 1)

        # Neck collar (like Pugna's high collar behind head)
        collar_pts = [
            (cx - 12, cy - 2),
            (cx - 14, cy - 8),
            (cx - 10, cy - 12),
            (cx, cy - 10),
            (cx + 10, cy - 12),
            (cx + 14, cy - 8),
            (cx + 12, cy - 2),
        ]
        _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["robe_darkest"], collar_pts)
        _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["robe_dark"], [
            (cx - 10, cy - 3),
            (cx - 12, cy - 7),
            (cx - 8, cy - 10),
            (cx, cy - 8),
            (cx + 8, cy - 10),
            (cx + 12, cy - 7),
            (cx + 10, cy - 3),
        ])
        # Collar highlight (points sticking up)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["horn_mid"], (cx - 12, cy - 8), 2)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["horn_mid"], (cx + 12, cy - 8), 2)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["horn_light"], (cx - 12, cy - 8), 1)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["horn_light"], (cx + 12, cy - 8), 1)


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Small arms - one holding staff, one free."""
        sway = math.sin(phase * 0.7) * 1

        # Staff arm (facing side)
        ss_x = cx + facing * 11
        ss_y = cy + 2
        se_x = ss_x + facing * 4
        se_y = cy + 8
        sh_x = cx + facing * 14  # goes to staff
        sh_y = cy - 3
        _NS_nyxara._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_nyxara._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)
        # Hand on staff
        _NS_nyxara._draw_creature_hand(surface, sh_x, sh_y, phase, size=3)

        # Free arm (opposite side)
        fs_x = cx + (-facing) * 11
        fs_y = cy + 2
        fe_x = fs_x + (-facing) * 5
        fe_y = cy + 8 + int(sway)
        fh_x = fe_x + (-facing) * 4
        fh_y = fe_y + 4
        _NS_nyxara._draw_arm_segment(surface, fs_x, fs_y, fe_x, fe_y)
        _NS_nyxara._draw_arm_segment(surface, fe_x, fe_y, fh_x, fh_y)
        _NS_nyxara._draw_hand_glow(surface, fh_x, fh_y, phase, 4)


    def _draw_casting_arms(surface, cx, cy, facing, phase, progress):
        """Casting - free hand extends forward with big orb."""
        # Staff arm stays holding staff
        ss_x = cx + facing * 11
        ss_y = cy + 2
        se_x = ss_x + facing * 4
        se_y = cy + 8
        sh_x = cx + facing * 14
        sh_y = cy - 3
        _NS_nyxara._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_nyxara._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)
        _NS_nyxara._draw_creature_hand(surface, sh_x, sh_y, phase, size=3)

        # Front casting arm - extends forward toward target
        fs_x = cx + (-facing) * 11
        fs_y = cy + 2

        if progress < 0.3:
            t = progress / 0.3
            arm_angle = -0.5 * t
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            arm_angle = -0.5 + 1.3 * t
        else:
            t = (progress - 0.5) / 0.5
            arm_angle = 0.8 - 0.6 * t

        fe_x = fs_x + int(math.cos(arm_angle) * 10) * facing
        fe_y = fs_y + int(math.sin(arm_angle) * 10) - 2
        fh_x = fe_x + int(math.cos(arm_angle) * 8) * facing
        fh_y = fe_y + int(math.sin(arm_angle) * 8)

        _NS_nyxara._draw_arm_segment(surface, fs_x, fs_y, fe_x, fe_y)
        _NS_nyxara._draw_arm_segment(surface, fe_x, fe_y, fh_x, fh_y)

        # Big charging orb on hand
        glow_size = 5 + int(math.sin(progress * math.pi) * 6)
        _NS_nyxara._draw_hand_glow(surface, fh_x, fh_y, phase, glow_size)

        # Energy sparks
        if 0.2 < progress < 0.6:
            intensity = math.sin((progress - 0.2) / 0.4 * math.pi)
            for i in range(5):
                angle = phase * 4 + i * math.pi * 2 / 5
                ex = fh_x + int(math.cos(angle) * 14 * intensity) * facing
                ey = fh_y + int(math.sin(angle) * 12 * intensity)
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_bright"], 220), (ex, ey), 2)
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_hot"], 240), (ex, ey), 1)


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Arm segment - robe sleeve with skin at end."""
        _NS_nyxara._aaline(surface, _NS_nyxara.PALETTE["shadow_deep"],
                (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 6)
        _NS_nyxara._aaline(surface, _NS_nyxara.PALETTE["robe_darkest"], (x1, y1), (x2, y2), 5)
        _NS_nyxara._aaline(surface, _NS_nyxara.PALETTE["robe_dark"], (x1, y1), (x2, y2), 3)
        _NS_nyxara._aaline(surface, _NS_nyxara.PALETTE["robe_mid"], (x1, y1), (x2, y2), 1)


    def _draw_creature_hand(surface, x, y, phase, size=3):
        """Small green creature hand."""
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["skin_darkest"], (x, y), size + 1)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["skin_dark"], (x, y), size)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["skin_mid"], (x - 1, y - 1), max(1, size - 1))
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["skin_light"], (x - 1, y - 1), max(1, size - 2))


    def _draw_hand_glow(surface, x, y, phase, size=5):
        """Glowing hand with nether energy."""
        pulse = math.sin(phase * 2.0) * 0.3 + 0.7
        s = int(size * pulse)

        # Hand
        _NS_nyxara._draw_creature_hand(surface, x, y, phase, size=3)

        # Nether glow
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_darkest"], 100), (x, y), s + 6)
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_dark"], 150), (x, y), s + 3)
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_mid"], 200), (x, y), s)
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_bright"], 220), (x, y), max(1, s - 2))
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_hot"], 240), (x, y), max(1, s - 4))
        if s > 4:
            _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_white"], 250),
                      (x, y), max(1, s - 6))

        # Sparks orbiting
        for i in range(3):
            angle = phase * 3 + i * math.pi * 2 / 3
            sx = x + int(math.cos(angle) * (s + 4))
            sy = y + int(math.sin(angle) * (s + 4))
            _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_hot"], (sx, sy), 1)


    def _draw_head(surface, cx, cy, facing, phase):
        """Monstrous horned green head."""
        # Neck
        _NS_nyxara._rect(surface, _NS_nyxara.PALETTE["skin_darkest"], (cx - 4, cy + 8, 8, 6))
        _NS_nyxara._rect(surface, _NS_nyxara.PALETTE["skin_dark"], (cx - 3, cy + 8, 6, 5))
        _NS_nyxara._rect(surface, _NS_nyxara.PALETTE["skin_mid"], (cx - 2, cy + 9, 4, 4))

        # Head shape - slightly monstrous, wider than tall
        # Shadow
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["shadow_deep"], (cx + 2, cy + 2), 11)

        # Skin base
        head_pts = [
            (cx - 10, cy - 4),
            (cx - 9, cy - 8),
            (cx - 4, cy - 10),
            (cx + 4, cy - 10),
            (cx + 9, cy - 8),
            (cx + 10, cy - 4),
            (cx + 10, cy + 4),
            (cx + 6, cy + 9),
            (cx - 6, cy + 9),
            (cx - 10, cy + 4),
        ]
        _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["skin_darkest"], head_pts)
        _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["skin_dark"], [
            (cx - 9, cy - 3),
            (cx - 8, cy - 7),
            (cx - 4, cy - 9),
            (cx + 4, cy - 9),
            (cx + 8, cy - 7),
            (cx + 9, cy - 3),
            (cx + 9, cy + 3),
            (cx + 5, cy + 8),
            (cx - 5, cy + 8),
            (cx - 9, cy + 3),
        ])
        _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["skin_mid"], [
            (cx - 7, cy - 1),
            (cx - 6, cy - 5),
            (cx - 3, cy - 7),
            (cx + 3, cy - 7),
            (cx + 6, cy - 5),
            (cx + 7, cy - 1),
            (cx + 6, cy + 3),
            (cx + 3, cy + 6),
            (cx - 3, cy + 6),
            (cx - 6, cy + 3),
        ])

        # Highlight
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["skin_light"], (cx - 4, cy - 4), 2)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["skin_shine"], (cx - 4, cy - 5), 1)

        # ===== HORNS (large curved horns from crown) =====
        for side in (-1, 1):
            # Main horn
            horn_pts = [
                (cx + side * 6, cy - 8),
                (cx + side * 9, cy - 10),
                (cx + side * 12, cy - 18),
                (cx + side * 13, cy - 22),
                (cx + side * 10, cy - 20),
                (cx + side * 8, cy - 12),
            ]
            _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["horn_dark"], horn_pts)
            _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["horn_mid"], [
                (cx + side * 7, cy - 8),
                (cx + side * 9, cy - 10),
                (cx + side * 11, cy - 17),
                (cx + side * 12, cy - 20),
                (cx + side * 10, cy - 18),
                (cx + side * 8, cy - 11),
            ])
            # Highlight on horn
            _NS_nyxara._aaline(surface, _NS_nyxara.PALETTE["horn_light"],
                    (cx + side * 9, cy - 11),
                    (cx + side * 12, cy - 20), 1)
            # Tip
            _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["horn_high"],
                      (cx + side * 13, cy - 22), 1)

        # Center small horn / crown spike
        _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["horn_dark"], [
            (cx - 2, cy - 10),
            (cx + 2, cy - 10),
            (cx, cy - 14),
        ])
        _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["horn_mid"], [
            (cx - 1, cy - 10),
            (cx + 1, cy - 10),
            (cx, cy - 13),
        ])

        # ===== EYES - large glowing nether green =====
        eye_pulse = math.sin(phase * 2) * 0.2 + 0.8

        # Eye sockets (deep)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["shadow_deep"], (cx - 4, cy - 2), 3)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["shadow_deep"], (cx + 4, cy - 2), 3)

        # Eye glow - very bright yellow-green
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["eye_dark"], (cx - 4, cy - 2),
                  max(1, int(3 * eye_pulse)))
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["eye_mid"], (cx - 4, cy - 2),
                  max(1, int(2 * eye_pulse)))
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["eye_bright"], (cx - 4, cy - 2),
                  max(1, int(2 * eye_pulse)))
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["eye_hot"], (cx - 4, cy - 2), 1)

        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["eye_dark"], (cx + 4, cy - 2),
                  max(1, int(3 * eye_pulse)))
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["eye_mid"], (cx + 4, cy - 2),
                  max(1, int(2 * eye_pulse)))
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["eye_bright"], (cx + 4, cy - 2),
                  max(1, int(2 * eye_pulse)))
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["eye_hot"], (cx + 4, cy - 2), 1)

        # Eye emission glow (like radiating outward)
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["eye_bright"], int(60 * eye_pulse)),
                  (cx - 4, cy - 2), 5)
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["eye_bright"], int(60 * eye_pulse)),
                  (cx + 4, cy - 2), 5)

        # Mouth - jagged/toothy
        _NS_nyxara._rect(surface, _NS_nyxara.PALETTE["shadow_deep"], (cx - 4, cy + 3, 8, 3))
        _NS_nyxara._rect(surface, _NS_nyxara.PALETTE["horn_dark"], (cx - 3, cy + 3, 6, 2))

        # Teeth
        for i in range(3):
            tx = cx - 2 + i * 2
            _NS_nyxara._rect(surface, _NS_nyxara.PALETTE["bone_light"], (tx, cy + 3, 1, 2))

        # Wrinkles/details on skin
        _NS_nyxara._aaline(surface, _NS_nyxara.PALETTE["skin_darkest"],
                (cx - 6, cy + 1), (cx - 4, cy + 2), 1)
        _NS_nyxara._aaline(surface, _NS_nyxara.PALETTE["skin_darkest"],
                (cx + 6, cy + 1), (cx + 4, cy + 2), 1)


    def _draw_skull_staff(surface, hx, hy, facing, phase):
        """Skull-topped staff."""
        # Staff shaft
        staff_top_x = hx
        staff_top_y = hy - 30
        staff_bottom_x = hx + int(math.sin(phase * 0.5) * 1)
        staff_bottom_y = hy + 22

        # Wood shaft
        _NS_nyxara._aaline(surface, _NS_nyxara.PALETTE["shadow_deep"],
                (staff_top_x + 2, staff_top_y + 2),
                (staff_bottom_x + 2, staff_bottom_y + 2), 5)
        _NS_nyxara._aaline(surface, _NS_nyxara.PALETTE["wood_dark"],
                (staff_top_x, staff_top_y),
                (staff_bottom_x, staff_bottom_y), 4)
        _NS_nyxara._aaline(surface, _NS_nyxara.PALETTE["wood_mid"],
                (staff_top_x, staff_top_y),
                (staff_bottom_x, staff_bottom_y), 3)
        _NS_nyxara._aaline(surface, _NS_nyxara.PALETTE["wood_light"],
                (staff_top_x - 1, staff_top_y),
                (staff_bottom_x - 1, staff_bottom_y), 1)

        # Wood binding rings
        for i in range(2):
            yoff = staff_top_y + 8 + i * 20
            _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["leather_dark"], (staff_top_x, yoff), 3)
            _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["leather_mid"], (staff_top_x, yoff), 2)

        # ===== SKULL AT TOP =====
        skull_x = staff_top_x
        skull_y = staff_top_y - 5

        # Skull glow aura
        glow_pulse = math.sin(phase * 2) * 0.3 + 0.7
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_dark"], int(100 * glow_pulse)),
                  (skull_x, skull_y), 12)
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_mid"], int(80 * glow_pulse)),
                  (skull_x, skull_y), 10)

        # Skull dome
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["shadow_deep"], (skull_x + 1, skull_y + 1), 8)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["bone_dark"], (skull_x, skull_y), 7)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["bone_mid"], (skull_x - 1, skull_y - 1), 6)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["bone_light"], (skull_x - 2, skull_y - 2), 3)

        # Nether green glowing eye sockets
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["shadow_deep"], (skull_x - 2, skull_y - 1), 2)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["shadow_deep"], (skull_x + 2, skull_y - 1), 2)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_mid"], (skull_x - 2, skull_y - 1),
                  max(1, int(2 * glow_pulse)))
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_bright"], (skull_x - 2, skull_y - 1), 1)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_mid"], (skull_x + 2, skull_y - 1),
                  max(1, int(2 * glow_pulse)))
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_bright"], (skull_x + 2, skull_y - 1), 1)

        # Nose
        _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["shadow_deep"], [
            (skull_x, skull_y + 1), (skull_x - 1, skull_y + 3),
            (skull_x + 1, skull_y + 3)
        ])

        # Jaw
        _NS_nyxara._rect(surface, _NS_nyxara.PALETTE["bone_dark"], (skull_x - 4, skull_y + 5, 8, 3))
        _NS_nyxara._rect(surface, _NS_nyxara.PALETTE["bone_mid"], (skull_x - 3, skull_y + 5, 6, 2))
        # Teeth
        for i in range(3):
            tx = skull_x - 2 + i * 2
            _NS_nyxara._rect(surface, _NS_nyxara.PALETTE["shadow_deep"], (tx, skull_y + 6, 1, 2))

        # Skull top bright glow
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_hot"], int(200 * glow_pulse)),
                  (skull_x, skull_y - 5), int(3 * glow_pulse))
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_white"], int(220 * glow_pulse)),
                  (skull_x, skull_y - 5), max(1, int(2 * glow_pulse)))

        # ===== BOTTOM STAFF TIP =====
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["horn_dark"],
                  (staff_bottom_x, staff_bottom_y + 2), 3)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["horn_mid"],
                  (staff_bottom_x, staff_bottom_y + 2), 2)
        # Green gem tip
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_bright"],
                  (staff_bottom_x, staff_bottom_y + 4), 2)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_hot"],
                  (staff_bottom_x, staff_bottom_y + 4), 1)


    def _draw_body_particles(surface, cx, cy, phase):
        """Nether particles floating around body."""
        for i in range(8):
            angle = phase * 0.4 + i * math.pi / 4
            radius = 26 + int(math.sin(phase * 0.7 + i) * 6)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(140 + math.sin(phase + i * 0.7) * 60)
            _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_dark"], alpha), (px, py), 2)
            _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_bright"], alpha // 2), (px, py), 1)

        # Rising embers
        for i in range(4):
            t = ((phase * 0.4 + i * 0.25) % 1.0)
            px = cx + int(math.sin(phase + i) * 15) + (i - 1) * 4
            py = cy + 20 - int(t * 50)
            alpha = int(200 * (1 - t))
            if alpha > 0:
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_light"], alpha), (px, py), 1)
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_hot"], alpha), (px, py - 1), 1)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_mist(surface, cx, cy, phase, trail=False,
                           facing=1, intense=False):
        """Nether mist below floating Nyxara."""
        strength = 1.5 if intense else 1.0

        # Base mist
        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(32, 3, -4):
            alpha = int((32 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_nyxara.PALETTE["nether_darkest"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising green wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 24)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_dark"], alpha), (sx, sy), 5)
            _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_mid"], alpha), (sx, sy - 2), 3)
            _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_bright"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Orbiting orbs
        for i in range(5):
            angle = phase * 0.9 + i * math.pi * 2 / 5
            r = 22 + int(math.sin(phase + i * 1.3) * 4)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 6)
            _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_mid"], (sx, sy), 3)
            _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_light"], (sx, sy), 2)
            _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_hot"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 130 - i * 22)
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y):
        """Ground shadow."""
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_nyxara.PALETTE["nether_darkest"], 60), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_nether_aura(surface, x, y, phase):
        """Background nether aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(72, 5, -4):
            alpha = int((72 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_nyxara._aacircle(aura, (*_NS_nyxara.PALETTE["nether_darkest"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))


    def _draw_ground_runes(surface, x, y, phase, skill):
        """Green nether runes on ground."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_nyxara.PALETTE["nether_dark"], 140),
                            (5, 10, 120, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_nyxara.PALETTE["nether_mid"], 170),
                            (20, 14, 90, 16), 2)

        for i in range(10):
            angle = phase * 0.2 + i * math.pi / 5
            x1 = 65 + int(math.cos(angle) * 30)
            y1 = 22 + int(math.sin(angle) * 6)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_nyxara.PALETTE["nether_bright"], 160),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_nyxara.PALETTE["nether_hot"], int(80 * pulse)),
                                (15, 8, 100, 28), 1)

        surface.blit(ring, (x - 65, y - 22))


    def _draw_cast_flash(surface, x, y, facing, progress):
        """Flash effect during ranged attack."""
        if progress < 0.2 or progress > 0.65:
            return
        t = (progress - 0.2) / 0.45
        intensity = math.sin(t * math.pi)

        flash_x = x + (-facing) * 22  # free hand side
        flash_y = y - 5

        alpha = int(200 * intensity)
        radius = int(8 + intensity * 15)

        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_dark"], alpha // 2),
                  (flash_x, flash_y), radius + 8)
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_mid"], alpha),
                  (flash_x, flash_y), radius)
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_bright"], alpha),
                  (flash_x, flash_y), radius // 2)
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_hot"], min(255, alpha)),
                  (flash_x, flash_y), max(1, radius // 4))
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_white"], min(255, alpha)),
                  (flash_x, flash_y), max(1, radius // 6))


    # ===================================================================
    # SKILL Q: NETHER BLAST - Large orb explosion
    # ===================================================================
    def _draw_nether_blast_cast(surface, boss, x, y, timer, phase):
        """Launch nether blast projectile."""
        if not getattr(boss, "_nx_blast_spawned", False):
            _NS_nyxara._spawn_blast_projectile(boss, x, y)
            boss._nx_blast_spawned = True

        if timer <= 5:
            boss._nx_blast_spawned = False

        # Big charge glow at hand
        hand_x = x + boss.direction * 24
        hand_y = y - 5
        pulse = math.sin(phase * 4) * 0.3 + 0.7
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_dark"], 150),
                  (hand_x, hand_y), int(14 * pulse))
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_mid"], 200),
                  (hand_x, hand_y), int(10 * pulse))
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_bright"], 230),
                  (hand_x, hand_y), int(6 * pulse))
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_hot"], 250),
                  (hand_x, hand_y), max(1, int(4 * pulse)))
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_white"],
                  (hand_x, hand_y), max(1, int(2 * pulse)))


    # ===================================================================
    # SKILL W: DECREPIFY - Beam that debuffs target
    # ===================================================================
    def _draw_decrepify(surface, boss, x, y, timer, phase):
        """Green beam applying decrepify to target."""
        tx, ty = _NS_nyxara._target_position(boss, x, y)
        hand_x = x + boss.direction * 22
        hand_y = y - 8

        # Main beam - thin and precise
        _NS_nyxara._draw_beam(surface, hand_x, hand_y, tx, ty, phase, color_key="nether")

        # Impact at target - green skull-like effect
        impact_pulse = math.sin(phase * 5) * 0.3 + 0.7
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_dark"], 150),
                  (tx, ty), int(14 * impact_pulse))
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_mid"], 200),
                  (tx, ty), int(10 * impact_pulse))
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_bright"], 230),
                  (tx, ty), int(6 * impact_pulse))
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_hot"], 250),
                  (tx, ty), max(1, int(3 * impact_pulse)))

        # Small skull hovering above target (Decrepify icon)
        skull_bob = int(math.sin(phase * 3) * 2)
        _NS_nyxara._draw_small_skull_icon(surface, tx, ty - 25 + skull_bob, phase)

        # Green particles around target (debuff visual)
        for i in range(6):
            angle = phase * 2 + i * math.pi / 3
            r = 18 + int(math.sin(phase + i) * 3)
            px = tx + int(math.cos(angle) * r)
            py = ty + int(math.sin(angle) * r * 0.6)
            _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_light"], 200), (px, py), 2)
            _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_hot"], 220), (px, py), 1)


    def _draw_beam(surface, sx, sy, tx, ty, phase, color_key="nether"):
        """Draw a bright energy beam."""
        dx = tx - sx
        dy = ty - sy
        dist = math.sqrt(dx * dx + dy * dy) or 1

        # Outer glow (thick)
        _NS_nyxara._aaline(surface, (*_NS_nyxara.PALETTE[f"{color_key}_dark"], 100), (sx, sy), (tx, ty), 8)
        _NS_nyxara._aaline(surface, (*_NS_nyxara.PALETTE[f"{color_key}_mid"], 150), (sx, sy), (tx, ty), 5)
        _NS_nyxara._aaline(surface, (*_NS_nyxara.PALETTE[f"{color_key}_light"], 200), (sx, sy), (tx, ty), 3)
        _NS_nyxara._aaline(surface, (*_NS_nyxara.PALETTE[f"{color_key}_bright"], 240), (sx, sy), (tx, ty), 2)
        _NS_nyxara._aaline(surface, (*_NS_nyxara.PALETTE[f"{color_key}_hot"], 250), (sx, sy), (tx, ty), 1)

        # Bright particles along beam
        segments = int(dist / 12)
        for i in range(segments):
            t = (phase * 0.3 + i * 0.1) % 1.0
            px = int(sx + dx * t)
            py = int(sy + dy * t)
            _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE[f"{color_key}_bright"], (px, py), 2)
            _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE[f"{color_key}_hot"], (px, py), 1)


    def _draw_small_skull_icon(surface, cx, cy, phase):
        """Small floating skull icon (for Decrepify indicator)."""
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_dark"], 150), (cx, cy), 10)
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_mid"], 180), (cx, cy), 8)
        # Skull
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["bone_dark"], (cx, cy - 1), 5)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["bone_mid"], (cx - 1, cy - 2), 4)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["bone_light"], (cx - 1, cy - 3), 2)
        # Eyes
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["shadow_deep"], (cx - 2, cy - 1), 1)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["shadow_deep"], (cx + 2, cy - 1), 1)
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_bright"], (cx - 2, cy - 1), 1)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_bright"], (cx + 2, cy - 1), 1)
        # Jaw
        _NS_nyxara._rect(surface, _NS_nyxara.PALETTE["bone_dark"], (cx - 2, cy + 3, 4, 2))
        for i in range(2):
            tx = cx - 1 + i * 2
            _NS_nyxara._rect(surface, _NS_nyxara.PALETTE["shadow_deep"], (tx, cy + 4, 1, 1))


    # ===================================================================
    # SKILL E: NETHER WARD - Summon skull ward
    # ===================================================================
    def _draw_nether_ward_ground(surface, boss, x, y, timer, phase):
        """Ward's ground indicator."""
        progress = max(0.0, min(1.0, 1 - timer / 150))
        facing = boss.direction

        # Ward placed to the side of Nyxara
        ward_x = x + facing * 50
        ward_y = y + 35

        pulse = math.sin(phase * 2) * 0.2 + 0.8
        radius = int(20 + progress * 10)

        _NS_nyxara._ellipse(surface, (*_NS_nyxara.PALETTE["nether_dark"], int(150 * pulse)),
                 (ward_x - radius, ward_y - radius // 4,
                  radius * 2, radius // 2), 3)
        _NS_nyxara._ellipse(surface, (*_NS_nyxara.PALETTE["nether_mid"], int(120 * pulse)),
                 (ward_x - radius + 3, ward_y - radius // 4 + 2,
                  radius * 2 - 6, radius // 2 - 4), 2)


    def _draw_nether_ward(surface, boss, x, y, timer, phase):
        """Skull ward standing/floating."""
        progress = max(0.0, min(1.0, 1 - timer / 150))
        facing = boss.direction

        # Ward position (in front of Nyxara)
        ward_x = x + facing * 50
        ward_y = y

        # Rising animation for first 20% of skill
        if progress < 0.2:
            rise = progress / 0.2
            ward_y = int(y + (1 - rise) * 20)
            alpha = int(255 * rise)
        else:
            # Bobbing
            ward_y = y + int(math.sin(phase * 1.5) * 2)
            alpha = 255

        # Ward body - a totem with skull
        # Wooden/dark stake going into ground
        stake_top_y = ward_y - 5
        stake_bot_y = ward_y + 20
        _NS_nyxara._aaline(surface, _NS_nyxara.PALETTE["shadow_deep"],
                (ward_x + 1, stake_top_y), (ward_x + 1, stake_bot_y), 4)
        _NS_nyxara._aaline(surface, _NS_nyxara.PALETTE["wood_dark"],
                (ward_x, stake_top_y), (ward_x, stake_bot_y), 3)
        _NS_nyxara._aaline(surface, _NS_nyxara.PALETTE["wood_mid"],
                (ward_x, stake_top_y), (ward_x, stake_bot_y), 2)

        # Skull on top of stake
        skull_x = ward_x
        skull_y = ward_y - 12

        # Big glow aura around ward
        glow_pulse = math.sin(phase * 3) * 0.3 + 0.7
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_darkest"], int(120 * glow_pulse)),
                  (skull_x, skull_y), 18)
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_dark"], int(100 * glow_pulse)),
                  (skull_x, skull_y), 14)
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_mid"], int(80 * glow_pulse)),
                  (skull_x, skull_y), 10)

        # Skull
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["shadow_deep"],
                  (skull_x + 1, skull_y + 1), 8)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["bone_dark"], (skull_x, skull_y), 7)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["bone_mid"], (skull_x - 1, skull_y - 1), 6)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["bone_light"], (skull_x - 2, skull_y - 2), 3)

        # Glowing eye sockets
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["shadow_deep"], (skull_x - 2, skull_y - 1), 2)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["shadow_deep"], (skull_x + 2, skull_y - 1), 2)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_bright"], (skull_x - 2, skull_y - 1),
                  max(1, int(2 * glow_pulse)))
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_hot"], (skull_x - 2, skull_y - 1), 1)
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_bright"], (skull_x + 2, skull_y - 1),
                  max(1, int(2 * glow_pulse)))
        _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_hot"], (skull_x + 2, skull_y - 1), 1)

        # Nose
        _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["shadow_deep"], [
            (skull_x, skull_y + 1), (skull_x - 1, skull_y + 3),
            (skull_x + 1, skull_y + 3)
        ])

        # Jaw
        _NS_nyxara._rect(surface, _NS_nyxara.PALETTE["bone_dark"], (skull_x - 4, skull_y + 5, 8, 3))
        _NS_nyxara._rect(surface, _NS_nyxara.PALETTE["bone_mid"], (skull_x - 3, skull_y + 5, 6, 2))
        # Teeth
        for i in range(3):
            tx = skull_x - 2 + i * 2
            _NS_nyxara._rect(surface, _NS_nyxara.PALETTE["shadow_deep"], (tx, skull_y + 6, 1, 2))

        # Small horns/spikes on skull sides
        for side in (-1, 1):
            _NS_nyxara._poly(surface, _NS_nyxara.PALETTE["horn_dark"], [
                (skull_x + side * 5, skull_y - 3),
                (skull_x + side * 7, skull_y - 2),
                (skull_x + side * 9, skull_y - 6),
            ])

        # Base circle glow
        _NS_nyxara._ellipse(surface, (*_NS_nyxara.PALETTE["nether_bright"], int(150 * glow_pulse)),
                 (ward_x - 12, ward_y + 20 - 3, 24, 6))
        _NS_nyxara._ellipse(surface, (*_NS_nyxara.PALETTE["nether_hot"], int(200 * glow_pulse)),
                 (ward_x - 8, ward_y + 20 - 2, 16, 4))

        # Ward is attacking - draw beams to target
        tx, ty = _NS_nyxara._target_position(boss, x, y)
        # Check if beam should fire (periodic)
        beam_active = (int(phase * 3) % 3) < 2  # Fires 2/3 of the time
        if beam_active:
            # Beam from skull mouth to target
            _NS_nyxara._draw_beam(surface, skull_x, skull_y + 6, tx, ty, phase,
                      color_key="nether")
            # Impact on target
            impact_r = int(6 + math.sin(phase * 5) * 2)
            _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_mid"], 200), (tx, ty), impact_r + 3)
            _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_bright"], 230), (tx, ty), impact_r)
            _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_hot"], 250),
                      (tx, ty), max(1, impact_r - 2))

        # Rising particles from ward
        for i in range(5):
            t = ((phase * 0.6 + i * 0.2) % 1.0)
            px = ward_x + int(math.sin(phase + i) * 8)
            py = ward_y - int(t * 30)
            alpha = int(200 * (1 - t))
            if alpha > 0:
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_light"], alpha), (px, py), 1)
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_hot"], alpha), (px, py - 1), 1)


    # ===================================================================
    # SKILL R: LIFE DRAIN
    # ===================================================================
    def _draw_life_drain(surface, boss, x, y, timer, phase):
        """Sustained beam draining life from target."""
        tx, ty = _NS_nyxara._target_position(boss, x, y)
        hand_x = x + boss.direction * 22
        hand_y = y - 8

        # Big pulsing beam
        dx = tx - hand_x
        dy = ty - hand_y
        dist = math.sqrt(dx * dx + dy * dy) or 1

        # Outer glow beam (thicker than decrepify)
        _NS_nyxara._aaline(surface, (*_NS_nyxara.PALETTE["nether_dark"], 100),
                (hand_x, hand_y), (tx, ty), 12)
        _NS_nyxara._aaline(surface, (*_NS_nyxara.PALETTE["nether_mid"], 150),
                (hand_x, hand_y), (tx, ty), 8)
        _NS_nyxara._aaline(surface, (*_NS_nyxara.PALETTE["nether_light"], 200),
                (hand_x, hand_y), (tx, ty), 5)
        _NS_nyxara._aaline(surface, (*_NS_nyxara.PALETTE["nether_bright"], 240),
                (hand_x, hand_y), (tx, ty), 3)
        _NS_nyxara._aaline(surface, (*_NS_nyxara.PALETTE["nether_hot"], 250),
                (hand_x, hand_y), (tx, ty), 2)
        _NS_nyxara._aaline(surface, (*_NS_nyxara.PALETTE["nether_white"], 250),
                (hand_x, hand_y), (tx, ty), 1)

        # Life particles flowing from target BACK to Nyxara (life drain)
        particle_count = int(dist / 8)
        for i in range(particle_count):
            # Multiple flows for effect
            for flow_offset in range(3):
                flow_t = ((phase * 0.6 + i * 0.1 + flow_offset * 0.33) % 1.0)
                # Flow from target (t=0) to Nyxara (t=1)
                px = int(tx + (hand_x - tx) * flow_t)
                py = int(ty + (hand_y - ty) * flow_t)
                # Wobble
                wobble = math.sin(flow_t * math.pi * 4 + phase * 2) * 4
                perp_x = -dy / dist * wobble
                perp_y = dx / dist * wobble
                px += int(perp_x)
                py += int(perp_y)

                # Life orb (like small hearts/souls)
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_light"], 220), (px, py), 3)
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_hot"], 240), (px, py), 2)
                _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_white"], (px, py), 1)

        # Massive impact on target - draining effect
        impact_pulse = math.sin(phase * 6) * 0.4 + 0.6
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_dark"], 180),
                  (tx, ty), int(20 * impact_pulse))
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_mid"], 220),
                  (tx, ty), int(15 * impact_pulse))
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_bright"], 240),
                  (tx, ty), int(10 * impact_pulse))
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_hot"], 250),
                  (tx, ty), int(6 * impact_pulse))
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_white"], 255),
                  (tx, ty), max(1, int(3 * impact_pulse)))

        # Explosion sparks at target
        for i in range(8):
            angle = phase * 3 + i * math.pi / 4
            r = 25 + int(math.sin(phase * 2 + i) * 5)
            px = tx + int(math.cos(angle) * r)
            py = ty + int(math.sin(angle) * r * 0.7)
            _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_hot"], (px, py), 2)
            _NS_nyxara._aacircle(surface, _NS_nyxara.PALETTE["nether_white"], (px, py), 1)

        # Healing glow at Nyxara (receiving life)
        heal_pulse = math.sin(phase * 4) * 0.3 + 0.7
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_dark"], 100),
                  (x, y - 10), int(30 * heal_pulse))
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_mid"], 150),
                  (x, y - 10), int(22 * heal_pulse))
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_bright"], 180),
                  (x, y - 10), int(15 * heal_pulse))
        _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_hot"], 220),
                  (x, y - 10), int(8 * heal_pulse))

        # Rising healing wisps around Nyxara
        for i in range(6):
            t = ((phase * 0.5 + i * 0.16) % 1.0)
            angle = i * math.pi / 3
            px = x + int(math.cos(angle) * 20)
            py = y - 5 - int(t * 30)
            alpha = int(220 * (1 - t))
            if alpha > 0:
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_bright"], alpha), (px, py), 2)
                _NS_nyxara._aacircle(surface, (*_NS_nyxara.PALETTE["nether_hot"], alpha), (px, py), 1)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_nyxara.draw_nyxara(surface, boss, x, y)


# ====================================================================
# GRAVEFANG
# ====================================================================
class _NS_gravefang:
    """Namespace gravefang - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Arc Warden inspired deep purple / electric blue
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Armor – dark indigo / gold trim
        "armor_darkest":  (12,  10,  28),
        "armor_dark":     (28,  22,  58),
        "armor_mid":      (52,  42,  95),
        "armor_light":    (85,  72, 140),
        "armor_high":     (130, 115, 185),
        "armor_shine":    (195, 185, 230),

        # Gold trim
        "gold_dark":      (100, 72,  18),
        "gold_mid":       (175, 135, 42),
        "gold_light":     (230, 195, 85),
        "gold_shine":     (255, 235, 160),

        # Cape / cloth
        "cape_darkest":   (8,   5,   22),
        "cape_dark":      (22,  14,  52),
        "cape_mid":       (42,  28,  88),
        "cape_light":     (68,  48, 125),
        "cape_high":      (95,  72, 165),

        # Arcane energy – electric blue / purple
        "arc_darkest":    (15,  20,  80),
        "arc_dark":       (35,  55, 160),
        "arc_mid":        (75, 105, 220),
        "arc_light":      (130, 165, 255),
        "arc_bright":     (180, 210, 255),
        "arc_hot":        (220, 235, 255),
        "arc_white":      (245, 248, 255),

        # Purple magic
        "magic_darkest":  (25,   8,  55),
        "magic_dark":     (65,  20, 120),
        "magic_mid":      (115, 45, 185),
        "magic_light":    (165, 85, 225),
        "magic_bright":   (200, 140, 255),
        "magic_hot":      (235, 200, 255),

        # Face gem
        "gem_dark":       (20,  25, 100),
        "gem_mid":        (55,  75, 190),
        "gem_light":      (100, 135, 240),
        "gem_bright":     (160, 195, 255),
        "gem_hot":        (210, 230, 255),
        "gem_white":      (240, 248, 255),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   3,   10),
        "white":          (255, 255, 255),

        # Spark / lightning
        "spark_dark":     (40,  60, 180),
        "spark_mid":      (90, 130, 240),
        "spark_light":    (160, 200, 255),
        "spark_hot":      (220, 240, 255),
    }


    def _clamp(color):
        """Clamp color channels, supports both RGB and RGBA."""
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_gravefang._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_gravefang.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_gravefang._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
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
        color = _NS_gravefang._clamp(color)
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
        color = _NS_gravefang._clamp(color)
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
        color = _NS_gravefang._clamp(color)
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
        return int(x + 200 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Lightning / electrical arc drawing helpers
    # ---------------------------------------------------------------------------
    def _draw_lightning_bolt(surface, start, end, color_inner, color_outer,
                             segments=8, jitter=8, width_outer=3, width_inner=1):
        """Draw a jagged lightning bolt between two points."""
        sx, sy = start
        ex, ey = end
        points = [(sx, sy)]
        for i in range(1, segments):
            t = i / segments
            mx = sx + (ex - sx) * t + (hash((sx, sy, i, ex)) % (jitter * 2) - jitter)
            my = sy + (ey - sy) * t + (hash((sy, sx, i, ey)) % (jitter * 2) - jitter)
            points.append((int(mx), int(my)))
        points.append((ex, ey))

        for i in range(len(points) - 1):
            _NS_gravefang._aaline(surface, color_outer, points[i], points[i + 1], width_outer)
        for i in range(len(points) - 1):
            _NS_gravefang._aaline(surface, color_inner, points[i], points[i + 1], width_inner)


    def _draw_lightning_arc(surface, cx, cy, radius, phase, count=6,
                            color=None):
        """Draw arcing lightning around a circle."""
        if color is None:
            color = _NS_gravefang.PALETTE["arc_light"]
        for i in range(count):
            angle1 = phase + i * math.pi * 2 / count
            angle2 = angle1 + 0.4 + math.sin(phase * 3 + i) * 0.3
            x1 = cx + int(math.cos(angle1) * radius)
            y1 = cy + int(math.sin(angle1) * radius * 0.5)
            x2 = cx + int(math.cos(angle2) * (radius + 8))
            y2 = cy + int(math.sin(angle2) * (radius + 8) * 0.5)
            _NS_gravefang._draw_lightning_bolt(surface, (x1, y1), (x2, y2),
                                 _NS_gravefang.PALETTE["arc_bright"], color,
                                 segments=4, jitter=5, width_outer=2, width_inner=1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM
    # ---------------------------------------------------------------------------
    class ArcProjectile:
        """A lightning projectile that travels toward a target."""
        def __init__(self, sx, sy, tx, ty, speed=6.0):
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
            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(60 + i * 12)
                r = max(1, 6 - (len(self.trail) - i))
                _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_dark"], alpha), (tx, ty), r)
                _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_light"], alpha // 2), (tx, ty), r + 2)

            if self.alive:
                px, py = int(self.x), int(self.y)
                # Outer glow
                _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_dark"], 80), (px, py), 14)
                _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_mid"], 120), (px, py), 10)
                # Core
                _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_light"], (px, py), 6)
                _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_bright"], (px, py), 4)
                _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_hot"], (px, py), 2)
                # Mini lightning
                for i in range(4):
                    angle = phase * 4 + i * math.pi / 2
                    ex = px + int(math.cos(angle) * 11)
                    ey = py + int(math.sin(angle) * 11)
                    _NS_gravefang._draw_lightning_bolt(surface, (px, py), (ex, ey),
                                         _NS_gravefang.PALETTE["arc_bright"], _NS_gravefang.PALETTE["arc_mid"],
                                         segments=3, jitter=4, width_outer=2, width_inner=1)


    # ---------------------------------------------------------------------------
    # State management helpers
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_morg_last_x"):
            boss._morg_last_x = boss.x
            boss._morg_last_y = boss.y
            return False
        dx = abs(boss.x - boss._morg_last_x)
        dy = abs(boss.y - boss._morg_last_y)
        boss._morg_last_x = boss.x
        boss._morg_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        """Track ranged attack animation timeline."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_morg_prev_timer", 0))
        active = bool(getattr(boss, "_morg_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._morg_attack_active = True
            boss._morg_attack_frame = 0
            active = True
        elif active:
            boss._morg_attack_frame = int(
                getattr(boss, "_morg_attack_frame", 0)) + 1
            if boss._morg_attack_frame > cooldown:
                boss._morg_attack_active = False
                boss._morg_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._morg_attack_active = False
            boss._morg_attack_frame = 0
            active = False

        boss._morg_prev_timer = timer
        boss._morg_attack_progress = (
            min(1.0, getattr(boss, "_morg_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        """Update and draw all active projectiles."""
        if not hasattr(boss, "_morg_projectiles"):
            boss._morg_projectiles = []
        for proj in boss._morg_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._morg_projectiles = [p for p in boss._morg_projectiles if p.alive or p.age < 8]


    def _spawn_projectile(boss, x, y):
        """Spawn a new arc projectile toward target."""
        if not hasattr(boss, "_morg_projectiles"):
            boss._morg_projectiles = []
        tx, ty = _NS_gravefang._target_position(boss, x, y)
        sx = x + 22 * getattr(boss, "direction", 1)
        sy = y - 12
        boss._morg_projectiles.append(_NS_gravefang.ArcProjectile(sx, sy, tx, ty, speed=5.5))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_morgath(surface, boss, x, y):
        """Entry point for Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_gravefang._detect_moving(boss)
        _NS_gravefang._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_morg_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # ---------- Background layers ----------
        _NS_gravefang._draw_arcane_aura(surface, x, y, pulse)
        _NS_gravefang._draw_ground_runes(surface, x, y + 38, pulse, active_skill)

        # ---------- Skill ground effects ----------
        if active_skill == "q":
            _NS_gravefang._draw_spark_wraith_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_gravefang._draw_magnetic_field(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_gravefang._draw_tempest_double_ground(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if attacking:
            _NS_gravefang._draw_morgath_attack(surface, boss, x, y)
        elif moving:
            _NS_gravefang._draw_morgath_walk(surface, boss, x, y)
        else:
            _NS_gravefang._draw_morgath_idle(surface, boss, x, y)

        # ---------- Projectiles ----------
        _NS_gravefang._manage_projectiles(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "q":
            _NS_gravefang._draw_spark_wraith(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_gravefang._draw_flux(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_gravefang._draw_magnetic_field_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_gravefang._draw_tempest_double(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_morgath_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_gravefang._draw_shadow(surface, x, y + 48)
        _NS_gravefang._draw_floating_wisps(surface, x, y + 35, boss.pulse)
        _NS_gravefang._draw_morgath_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_morgath_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(abs(math.sin(phase * 1.3)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_gravefang._draw_shadow(surface, x + sway, y + 48)
        _NS_gravefang._draw_floating_wisps(surface, x + sway, y + 35, phase, trail=True,
                             facing=boss.direction)
        _NS_gravefang._draw_morgath_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_morgath_attack(surface, boss, x, y):
        progress = getattr(boss, "_morg_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Spawn projectile at the right moment
        if 0.28 < progress < 0.35 and not getattr(boss, "_morg_proj_spawned", False):
            _NS_gravefang._spawn_projectile(boss, x, y)
            boss._morg_proj_spawned = True
        if progress < 0.1 or progress > 0.9:
            boss._morg_proj_spawned = False

        recoil = int(math.sin(progress * math.pi) * 3) * -boss.direction
        _NS_gravefang._draw_shadow(surface, x + recoil, y + 48)
        _NS_gravefang._draw_floating_wisps(surface, x + recoil, y + 35, boss.pulse, intense=True)
        _NS_gravefang._draw_morgath_body(surface, x + recoil, y, boss.direction, boss.pulse,
                           "attack", progress)
        _NS_gravefang._draw_cast_flash(surface, x + recoil, y, boss.direction, progress)


    # ===================================================================
    # BODY RENDERING – HD detailed
    # ===================================================================
    def _draw_morgath_body(surface, cx, cy, facing, phase, action,
                           attack_progress=0):
        sway = int(math.sin(phase * 0.6) * (2 if action != "idle" else 1))

        # Cape (drawn behind body)
        _NS_gravefang._draw_cape(surface, cx, cy, facing, phase, action)

        # Lower robes / floating lower body
        _NS_gravefang._draw_lower_robes(surface, cx, cy + 5, phase, sway)

        # Torso armor
        _NS_gravefang._draw_torso(surface, cx, cy - 8, phase)

        # Shoulder pauldrons
        _NS_gravefang._draw_pauldrons(surface, cx, cy - 16, phase)

        # Arms
        if action == "attack":
            _NS_gravefang._draw_casting_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        else:
            _NS_gravefang._draw_idle_arms(surface, cx, cy - 8, facing, phase)

        # Head
        _NS_gravefang._draw_head(surface, cx, cy - 30, phase)

        # Floating arcane particles around body
        _NS_gravefang._draw_body_particles(surface, cx, cy, phase)


    def _draw_cape(surface, cx, cy, facing, phase, action):
        """Flowing cape behind the character."""
        wave = math.sin(phase * 0.8) * 3
        wave2 = math.sin(phase * 1.2 + 0.5) * 2

        # Cape shape - multiple layers for depth
        cape_points_outer = [
            (cx - 14, cy - 14),
            (cx - 18, cy + 5),
            (cx - 24 - int(wave), cy + 30),
            (cx - 18 - int(wave2), cy + 42),
            (cx - 5, cy + 45 + int(abs(wave))),
            (cx + 5, cy + 45 + int(abs(wave))),
            (cx + 18 + int(wave2), cy + 42),
            (cx + 24 + int(wave), cy + 30),
            (cx + 18, cy + 5),
            (cx + 14, cy - 14),
        ]
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["cape_darkest"], cape_points_outer)

        cape_mid = [
            (cx - 12, cy - 12),
            (cx - 16, cy + 5),
            (cx - 20 - int(wave * 0.7), cy + 28),
            (cx - 14 - int(wave2 * 0.7), cy + 38),
            (cx - 3, cy + 40),
            (cx + 3, cy + 40),
            (cx + 14 + int(wave2 * 0.7), cy + 38),
            (cx + 20 + int(wave * 0.7), cy + 28),
            (cx + 16, cy + 5),
            (cx + 12, cy - 12),
        ]
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["cape_dark"], cape_mid)

        cape_inner = [
            (cx - 9, cy - 8),
            (cx - 12, cy + 5),
            (cx - 15 - int(wave * 0.4), cy + 22),
            (cx - 8, cy + 32),
            (cx, cy + 34),
            (cx + 8, cy + 32),
            (cx + 15 + int(wave * 0.4), cy + 22),
            (cx + 12, cy + 5),
            (cx + 9, cy - 8),
        ]
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["cape_mid"], cape_inner)

        # Cape edge lightning streaks
        for i in range(4):
            t = (phase * 0.3 + i * 0.25) % 1.0
            idx = int(t * (len(cape_points_outer) - 1))
            px, py = cape_points_outer[idx]
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_mid"], 100), (px, py), 3)


    def _draw_lower_robes(surface, cx, cy, phase, sway):
        """Floating lower body with tattered robes."""
        # Outer robe shape
        robe_outer = [
            (cx - 18, cy),
            (cx + 18, cy),
            (cx + 22 + sway, cy + 12),
            (cx + 16, cy + 22),
            (cx + 8, cy + 28),
            (cx + 3, cy + 30),
            (cx - 3, cy + 30),
            (cx - 8, cy + 28),
            (cx - 16, cy + 22),
            (cx - 22 - sway, cy + 12),
        ]
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["shadow_deep"], [(p[0] + 2, p[1] + 2) for p in robe_outer])
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_darkest"], robe_outer)

        robe_mid = [
            (cx - 15, cy + 2),
            (cx + 15, cy + 2),
            (cx + 18 + sway, cy + 12),
            (cx + 12, cy + 20),
            (cx + 5, cy + 25),
            (cx - 5, cy + 25),
            (cx - 12, cy + 20),
            (cx - 18 - sway, cy + 12),
        ]
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_dark"], robe_mid)

        robe_inner = [
            (cx - 11, cy + 4),
            (cx + 11, cy + 4),
            (cx + 14 + sway, cy + 12),
            (cx + 8, cy + 18),
            (cx - 8, cy + 18),
            (cx - 14 - sway, cy + 12),
        ]
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_mid"], robe_inner)

        # Tattered bottom edges
        for i in range(7):
            tx = cx - 15 + i * 5
            ty = cy + 26 + int(math.sin(phase * 1.5 + i) * 3)
            _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["cape_dark"], [
                (tx - 3, cy + 24), (tx + 3, cy + 24),
                (tx + 1, ty + 4), (tx - 1, ty + 4),
            ])

        # Gold belt line
        _NS_gravefang._rect(surface, _NS_gravefang.PALETTE["gold_dark"], (cx - 19, cy - 1, 38, 5))
        _NS_gravefang._rect(surface, _NS_gravefang.PALETTE["gold_mid"], (cx - 17, cy, 34, 3))
        _NS_gravefang._rect(surface, _NS_gravefang.PALETTE["gold_light"], (cx - 14, cy + 1, 28, 1))

        # Belt buckle gem
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_dark"], (cx, cy + 1), 4)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_mid"], (cx, cy + 1), 3)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_light"], (cx - 1, cy), 2)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_bright"], (cx - 1, cy), 1)


    def _draw_torso(surface, cx, cy, phase):
        """Main chest armor with gold trim."""
        # Shadow
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["shadow_deep"], [
            (cx - 14 + 2, cy - 10 + 2), (cx + 14 + 2, cy - 10 + 2),
            (cx + 12 + 2, cy + 14 + 2), (cx + 5 + 2, cy + 19 + 2),
            (cx - 5 + 2, cy + 19 + 2), (cx - 12 + 2, cy + 14 + 2),
        ])

        # Main chest plate
        chest = [
            (cx - 14, cy - 10), (cx + 14, cy - 10),
            (cx + 12, cy + 14), (cx + 5, cy + 19),
            (cx - 5, cy + 19), (cx - 12, cy + 14),
        ]
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_darkest"], chest)
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_dark"], [
            (cx - 12, cy - 8), (cx + 12, cy - 8),
            (cx + 10, cy + 12), (cx + 4, cy + 16),
            (cx - 4, cy + 16), (cx - 10, cy + 12),
        ])
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_mid"], [
            (cx - 9, cy - 5), (cx + 9, cy - 5),
            (cx + 7, cy + 9), (cx + 3, cy + 13),
            (cx - 3, cy + 13), (cx - 7, cy + 9),
        ])

        # Gold chest accent lines
        _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["gold_dark"], (cx - 12, cy - 8), (cx, cy + 14), 2)
        _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["gold_dark"], (cx + 12, cy - 8), (cx, cy + 14), 2)
        _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["gold_mid"], (cx - 11, cy - 7), (cx, cy + 13), 1)
        _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["gold_mid"], (cx + 11, cy - 7), (cx, cy + 13), 1)

        # Center gem
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_darkest"], (cx, cy + 2), 5)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_dark"], (cx, cy + 2), 4)
        pulse_r = 3 + int(math.sin(phase * 1.5) * 1)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_mid"], (cx, cy + 1), pulse_r)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_light"], (cx, cy + 1), 2)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_hot"], (cx, cy + 1), 1)

        # Seam details
        for xoff, yoff in [(-8, 0), (6, 1), (-6, 8), (5, 9)]:
            pygame.draw.line(surface, _NS_gravefang.PALETTE["armor_darkest"],
                             (cx + xoff, cy + yoff),
                             (cx + xoff + 3, cy + yoff + 3), 1)

        # Gold trim around edges
        for i in range(len(chest)):
            p1 = chest[i]
            p2 = chest[(i + 1) % len(chest)]
            _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["gold_dark"], p1, p2, 2)


    def _draw_pauldrons(surface, cx, cy, phase):
        """Shoulder pauldrons with gold trim."""
        for side in (-1, 1):
            sx = cx + side * 16
            # Shadow
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["shadow_deep"], (sx + 2, cy + 2), 11)
            # Main pauldron
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["armor_darkest"], (sx, cy), 10)
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["armor_dark"], (sx - side, cy - 1), 8)
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["armor_mid"], (sx - side * 2, cy - 2), 6)
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["armor_light"], (sx - side * 3, cy - 4), 3)

            # Gold trim ring
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gold_dark"], (sx, cy), 10, 2)
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gold_mid"], (sx, cy), 9, 1)

            # Pauldron gem
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_dark"], (sx, cy - 2), 3)
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_mid"], (sx, cy - 2), 2)
            p = math.sin(phase * 1.2 + side) * 0.5 + 0.5
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_light"], (sx, cy - 2), max(1, int(2 * p)))

            # Spike on top
            _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_darkest"], [
                (sx - 2, cy - 8),
                (sx + 2, cy - 8),
                (sx + side * 2, cy - 16),
            ])
            _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["gold_mid"],
                    (sx, cy - 8), (sx + side * 2, cy - 16), 1)


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Arms in resting position with arcane energy in hands."""
        sway = math.sin(phase * 0.7) * 2
        for side in (-1, 1):
            shoulder_x = cx + side * 14
            shoulder_y = cy + 2
            elbow_x = shoulder_x + side * 8
            elbow_y = cy + 12 + int(sway)
            hand_x = elbow_x + side * 4
            hand_y = elbow_y + 10

            _NS_gravefang._draw_arm_segment(surface, shoulder_x, shoulder_y,
                              elbow_x, elbow_y, phase)
            _NS_gravefang._draw_arm_segment(surface, elbow_x, elbow_y,
                              hand_x, hand_y, phase)
            _NS_gravefang._draw_hand_glow(surface, hand_x, hand_y, phase + side, 5)


    def _draw_casting_arms(surface, cx, cy, facing, phase, progress):
        """Arms in casting pose – one arm raised forward shooting."""
        sway = math.sin(phase * 0.7) * 1

        # Back arm (away from facing)
        back_side = -facing
        bs_x = cx + back_side * 14
        bs_y = cy + 2
        be_x = bs_x + back_side * 8
        be_y = cy + 10
        bh_x = be_x + back_side * 5
        bh_y = be_y + 8
        _NS_gravefang._draw_arm_segment(surface, bs_x, bs_y, be_x, be_y, phase)
        _NS_gravefang._draw_arm_segment(surface, be_x, be_y, bh_x, bh_y, phase)
        _NS_gravefang._draw_hand_glow(surface, bh_x, bh_y, phase, 4)

        # Front arm (casting arm) – extends forward
        fs_x = cx + facing * 14
        fs_y = cy + 2

        # Wind up then thrust forward
        if progress < 0.3:
            t = progress / 0.3
            arm_angle = -0.8 * t
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            arm_angle = -0.8 + 1.6 * t
        else:
            t = (progress - 0.5) / 0.5
            arm_angle = 0.8 - 0.5 * t

        fe_x = fs_x + int(math.cos(arm_angle) * 14) * facing
        fe_y = fs_y + int(math.sin(arm_angle) * 14) - 4
        fh_x = fe_x + int(math.cos(arm_angle) * 12) * facing
        fh_y = fe_y + int(math.sin(arm_angle) * 12)

        _NS_gravefang._draw_arm_segment(surface, fs_x, fs_y, fe_x, fe_y, phase)
        _NS_gravefang._draw_arm_segment(surface, fe_x, fe_y, fh_x, fh_y, phase)

        # Larger glow on casting hand
        glow_size = 6 + int(math.sin(progress * math.pi) * 5)
        _NS_gravefang._draw_hand_glow(surface, fh_x, fh_y, phase, glow_size)

        # Arc energy from hand during cast
        if 0.2 < progress < 0.6:
            intensity = math.sin((progress - 0.2) / 0.4 * math.pi)
            for i in range(3):
                angle = phase * 5 + i * math.pi * 2 / 3
                ex = fh_x + int(math.cos(angle) * 15 * intensity) * facing
                ey = fh_y + int(math.sin(angle) * 12 * intensity)
                _NS_gravefang._draw_lightning_bolt(surface, (fh_x, fh_y), (ex, ey),
                                     _NS_gravefang.PALETTE["arc_bright"], _NS_gravefang.PALETTE["arc_mid"],
                                     segments=3, jitter=4, width_outer=2, width_inner=1)


    def _draw_arm_segment(surface, x1, y1, x2, y2, phase):
        """Draw a single arm segment with armor detail."""
        _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["shadow_deep"], (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 8)
        _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["armor_darkest"], (x1, y1), (x2, y2), 7)
        _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["armor_dark"], (x1, y1), (x2, y2), 5)
        _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["armor_mid"], (x1, y1), (x2, y2), 3)
        _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["armor_light"], (x1, y1 - 1), (x2, y2 - 1), 1)
        # Gold joint ring
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gold_dark"], (mx, my), 4)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gold_mid"], (mx, my), 3)


    def _draw_hand_glow(surface, x, y, phase, size=5):
        """Draw glowing arcane energy in hand."""
        pulse = math.sin(phase * 2.0) * 0.3 + 0.7
        s = int(size * pulse)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_dark"], 80), (x, y), s + 6)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_mid"], 130), (x, y), s + 3)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_light"], (x, y), s)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_bright"], (x, y), max(1, s - 2))
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_hot"], (x, y), max(1, s - 4))

        # Tiny sparks
        for i in range(3):
            angle = phase * 3 + i * math.pi * 2 / 3
            sx = x + int(math.cos(angle) * (s + 4))
            sy = y + int(math.sin(angle) * (s + 4))
            _NS_gravefang._rect(surface, _NS_gravefang.PALETTE["arc_bright"], (sx, sy, 2, 2))


    def _draw_head(surface, cx, cy, phase):
        """Ornate helm with large central gem - Arc Warden style."""
        # Shadow
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["shadow_deep"], (cx + 2, cy + 2), 13)

        # Helm base
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["armor_darkest"], (cx, cy), 12)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["armor_dark"], (cx - 1, cy - 1), 10)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["armor_mid"], (cx - 2, cy - 2), 7)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["armor_light"], (cx - 3, cy - 4), 4)

        # Gold helm trim
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gold_dark"], (cx, cy), 12, 2)

        # Face plate – darker recessed area
        _NS_gravefang._rect(surface, _NS_gravefang.PALETTE["armor_darkest"], (cx - 8, cy - 4, 16, 10),
              border_radius=3)
        _NS_gravefang._rect(surface, _NS_gravefang.PALETTE["shadow_deep"], (cx - 6, cy - 2, 12, 7),
              border_radius=2)

        # Central gem (large, Arc Warden style)
        gem_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        gem_r = int(6 * gem_pulse)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_dark"], (cx, cy), gem_r + 2)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_mid"], (cx, cy), gem_r)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_light"], (cx - 1, cy - 1), max(1, gem_r - 2))
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_bright"], (cx - 1, cy - 2), max(1, gem_r - 4))
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gem_hot"], (cx - 1, cy - 2), max(1, gem_r - 5))

        # Gem glow effect
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["gem_light"], int(60 * gem_pulse)),
                  (cx, cy), gem_r + 6)

        # Gold frame around gem
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gold_mid"], (cx, cy), gem_r + 2, 2)
        _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gold_light"], (cx, cy), gem_r + 1, 1)

        # Helm horns / crown
        for side in (-1, 1):
            # Main horn
            _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_darkest"], [
                (cx + side * 8, cy - 6),
                (cx + side * 14, cy - 20),
                (cx + side * 10, cy - 5),
            ])
            _NS_gravefang._aaline(surface, _NS_gravefang.PALETTE["gold_mid"],
                    (cx + side * 9, cy - 6),
                    (cx + side * 14, cy - 20), 1)
            # Gold tip
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["gold_light"],
                      (cx + side * 14, cy - 20), 2)

            # Secondary smaller horn
            _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_dark"], [
                (cx + side * 5, cy - 9),
                (cx + side * 8, cy - 16),
                (cx + side * 6, cy - 8),
            ])

        # Chin guard
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_darkest"], [
            (cx - 6, cy + 6),
            (cx + 6, cy + 6),
            (cx + 3, cy + 12),
            (cx, cy + 14),
            (cx - 3, cy + 12),
        ])
        _NS_gravefang._poly(surface, _NS_gravefang.PALETTE["armor_dark"], [
            (cx - 4, cy + 7),
            (cx + 4, cy + 7),
            (cx + 2, cy + 11),
            (cx, cy + 12),
            (cx - 2, cy + 11),
        ])


    def _draw_body_particles(surface, cx, cy, phase):
        """Floating arcane particles around body."""
        for i in range(8):
            angle = phase * 0.4 + i * math.pi / 4
            radius = 25 + int(math.sin(phase * 0.7 + i) * 8)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(120 + math.sin(phase + i * 0.7) * 60)
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_mid"], alpha), (px, py), 2)
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_bright"], alpha // 2), (px, py), 1)


    # ===================================================================
    # FLOATING EFFECTS (replaces legs)
    # ===================================================================
    def _draw_floating_wisps(surface, cx, cy, phase, trail=False,
                             facing=1, intense=False):
        """Arcane mist and energy wisps beneath floating Morgath."""
        strength = 1.5 if intense else 1.0

        # Misty base
        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(32, 3, -4):
            alpha = int((32 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_gravefang.PALETTE["arc_dark"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising energy wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 24)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_dark"], alpha), (sx, sy), 5)
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_mid"], alpha), (sx, sy - 2), 3)
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_light"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Small orbiting energy balls
        for i in range(5):
            angle = phase * 0.9 + i * math.pi * 2 / 5
            r = 20 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 7)
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_mid"], (sx, sy), 3)
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_light"], (sx, sy), 2)
            _NS_gravefang._aacircle(surface, _NS_gravefang.PALETTE["arc_hot"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 120 - i * 22)
                _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y):
        """Ground shadow beneath floating entity."""
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_gravefang.PALETTE["arc_dark"], 40), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_arcane_aura(surface, x, y, phase):
        """Large background aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(72, 5, -4):
            alpha = int((72 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_gravefang._aacircle(aura, (*_NS_gravefang.PALETTE["magic_darkest"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))


    def _draw_ground_runes(surface, x, y, phase, skill):
        """Arcane circle on the ground."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        # Outer ring
        pygame.draw.ellipse(ring, (*_NS_gravefang.PALETTE["arc_dark"], 140),
                            (5, 10, 120, 24), 3)
        # Inner ring
        pygame.draw.ellipse(ring, (*_NS_gravefang.PALETTE["arc_mid"], 170),
                            (20, 14, 90, 16), 2)

        # Rune marks
        for i in range(10):
            angle = phase * 0.2 + i * math.pi / 5
            x1 = 65 + int(math.cos(angle) * 30)
            y1 = 22 + int(math.sin(angle) * 6)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_gravefang.PALETTE["arc_light"], 160),
                             (x1, y1), (x2, y2), 1)

        # Pulsing inner glow when skill active
        if skill:
            pygame.draw.ellipse(ring, (*_NS_gravefang.PALETTE["arc_bright"], int(70 * pulse)),
                                (15, 8, 100, 28), 1)

        surface.blit(ring, (x - 65, y - 22))


    def _draw_cast_flash(surface, x, y, facing, progress):
        """Flash effect during ranged attack."""
        if progress < 0.2 or progress > 0.65:
            return
        t = (progress - 0.2) / 0.45
        intensity = math.sin(t * math.pi)

        flash_x = x + 22 * facing
        flash_y = y - 12

        alpha = int(180 * intensity)
        radius = int(8 + intensity * 18)

        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_mid"], alpha // 2), (flash_x, flash_y), radius + 8)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_light"], alpha), (flash_x, flash_y), radius)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_bright"], alpha), (flash_x, flash_y), radius // 2)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_hot"], min(255, alpha)),
                  (flash_x, flash_y), max(1, radius // 4))

        # Lightning sparks from flash
        for i in range(5):
            angle = progress * 8 + i * math.pi * 2 / 5
            ex = flash_x + int(math.cos(angle) * radius * 1.3)
            ey = flash_y + int(math.sin(angle) * radius * 1.3)
            _NS_gravefang._draw_lightning_bolt(surface, (flash_x, flash_y), (ex, ey),
                                 (*_NS_gravefang.PALETTE["arc_bright"], alpha),
                                 (*_NS_gravefang.PALETTE["arc_mid"], alpha // 2),
                                 segments=3, jitter=5, width_outer=2, width_inner=1)


    # ===================================================================
    # SKILL Q: SPARK WRAITH
    # ===================================================================
    def _draw_spark_wraith_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_gravefang._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 80))
        # Ground warning circle
        radius = int(20 + progress * 35)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["magic_dark"], 100), (tx, ty), radius, 2)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["magic_mid"], 80), (tx, ty), radius + 5, 1)


    def _draw_spark_wraith(surface, boss, x, y, timer, phase):
        tx, ty = _NS_gravefang._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 80))

        # Wraith forming at target location
        if progress < 0.4:
            # Forming phase
            form = progress / 0.4
            alpha = int(200 * form)
            radius = int(18 * form)
        else:
            alpha = 200
            radius = 18 + int(math.sin(phase * 3) * 4)

        # Wraith body - ghostly sphere
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["magic_dark"], alpha // 2), (tx, ty), radius + 8)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["magic_mid"], alpha), (tx, ty), radius)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["magic_light"], alpha), (tx, ty), max(1, radius - 5))
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["magic_bright"], min(255, alpha)),
                  (tx, ty), max(1, radius - 10))

        # Lightning arcs around wraith
        _NS_gravefang._draw_lightning_arc(surface, tx, ty, radius + 5, phase, count=5,
                            color=_NS_gravefang.PALETTE["arc_light"])

        # Sparks flying outward
        for i in range(6):
            angle = phase * 2 + i * math.pi / 3
            dist = radius + 10 + int(math.sin(phase * 3 + i) * 8)
            sx = tx + int(math.cos(angle) * dist)
            sy = ty + int(math.sin(angle) * dist * 0.6)
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["spark_light"], 180), (sx, sy), 2)
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["spark_hot"], 220), (sx, sy), 1)


    # ===================================================================
    # SKILL W: FLUX
    # ===================================================================
    def _draw_flux(surface, boss, x, y, timer, phase):
        tx, ty = _NS_gravefang._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 70))

        # Flux beam connecting Morgath to target
        start_x = x + 20 * boss.direction
        start_y = y - 10

        # Multiple lightning beams
        for i in range(3):
            offset = (i - 1) * 3
            _NS_gravefang._draw_lightning_bolt(
                surface,
                (start_x, start_y + offset),
                (tx, ty + offset),
                _NS_gravefang.PALETTE["arc_bright"],
                _NS_gravefang.PALETTE["arc_mid"],
                segments=12,
                jitter=12,
                width_outer=3,
                width_inner=1
            )

        # Energy nodes along the beam
        for i in range(8):
            t = (progress + i * 0.12) % 1.0
            px = int(start_x + (tx - start_x) * t)
            py = int(start_y + (ty - start_y) * t)
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_light"], 200), (px, py), 4)
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_hot"], 220), (px, py), 2)

        # Impact at target
        impact_pulse = math.sin(phase * 4) * 0.3 + 0.7
        impact_r = int(15 * impact_pulse)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_mid"], 150), (tx, ty), impact_r + 5)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_light"], 200), (tx, ty), impact_r)
        _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_hot"], 230), (tx, ty), max(1, impact_r - 5))

        # Slow effect visual - pulsing rings at target
        for i in range(3):
            ring_r = int(20 + i * 12 + math.sin(phase * 2 + i) * 5)
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["magic_mid"], 80), (tx, ty), ring_r, 2)


    # ===================================================================
    # SKILL E: MAGNETIC FIELD
    # ===================================================================
    def _draw_magnetic_field(surface, boss, x, y, timer, phase):
        """Ground layer of magnetic field dome."""
        progress = max(0.0, min(1.0, 1 - timer / 90))
        radius = int(45 + progress * 30)
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8

        # Ground ellipse
        _NS_gravefang._ellipse(surface, (*_NS_gravefang.PALETTE["arc_dark"], int(80 * pulse)),
                 (x - radius, y + 30 - radius // 4, radius * 2, radius // 2), 2)
        _NS_gravefang._ellipse(surface, (*_NS_gravefang.PALETTE["arc_mid"], int(60 * pulse)),
                 (x - radius + 5, y + 32 - radius // 4,
                  radius * 2 - 10, radius // 2 - 4), 1)


    def _draw_magnetic_field_foreground(surface, boss, x, y, timer, phase):
        """Dome and lightning of magnetic field."""
        progress = max(0.0, min(1.0, 1 - timer / 90))
        radius = int(45 + progress * 30)
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8

        # Dome surface (semi-transparent)
        dome = pygame.Surface((radius * 2 + 20, radius + 40), pygame.SRCALPHA)
        dome_cx = radius + 10
        dome_cy = radius + 20

        # Draw dome arcs
        for i in range(8):
            angle1 = math.pi + i * math.pi / 8
            angle2 = angle1 + math.pi / 8
            x1 = dome_cx + int(math.cos(angle1) * radius)
            y1 = dome_cy + int(math.sin(angle1) * radius * 0.7)
            x2 = dome_cx + int(math.cos(angle2) * radius)
            y2 = dome_cy + int(math.sin(angle2) * radius * 0.7)
            alpha = int(120 * pulse)
            pygame.draw.line(dome, (*_NS_gravefang.PALETTE["arc_mid"], alpha),
                             (x1, y1), (x2, y2), 2)

        # Lightning crawling on dome surface
        for i in range(6):
            angle = phase * 1.2 + i * math.pi / 3
            lx1 = dome_cx + int(math.cos(angle) * radius * 0.8)
            ly1 = dome_cy + int(math.sin(angle) * radius * 0.5)
            lx2 = dome_cx + int(math.cos(angle + 0.5) * radius)
            ly2 = dome_cy + int(math.sin(angle + 0.5) * radius * 0.6)
            _NS_gravefang._draw_lightning_bolt(dome, (lx1, ly1), (lx2, ly2),
                                 (*_NS_gravefang.PALETTE["arc_bright"], 180),
                                 (*_NS_gravefang.PALETTE["arc_mid"], 120),
                                 segments=4, jitter=6, width_outer=2, width_inner=1)

        # Bright orbs on dome
        for i in range(4):
            angle = phase * 0.8 + i * math.pi / 2
            ox = dome_cx + int(math.cos(angle) * radius * 0.9)
            oy = dome_cy + int(math.sin(angle) * radius * 0.55)
            pygame.draw.circle(dome, (*_NS_gravefang.PALETTE["arc_light"], 200), (ox, oy), 5)
            pygame.draw.circle(dome, (*_NS_gravefang.PALETTE["arc_hot"], 230), (ox, oy), 3)
            pygame.draw.circle(dome, (*_NS_gravefang.PALETTE["arc_white"], 250), (ox, oy), 1)

        surface.blit(dome, (x - dome_cx, y - 20 - dome_cy + radius))


    # ===================================================================
    # SKILL R: TEMPEST DOUBLE
    # ===================================================================
    def _draw_tempest_double_ground(surface, boss, x, y, timer, phase):
        """Ground effects for summoning."""
        progress = max(0.0, min(1.0, 1 - timer / 100))
        # Summoning circle
        radius = int(30 + progress * 20)
        sx = x + 50 * boss.direction
        sy = y + 35

        pulse = math.sin(phase * 2) * 0.3 + 0.7
        _NS_gravefang._ellipse(surface, (*_NS_gravefang.PALETTE["magic_mid"], int(120 * pulse)),
                 (sx - radius, sy - radius // 4, radius * 2, radius // 2), 2)
        _NS_gravefang._ellipse(surface, (*_NS_gravefang.PALETTE["arc_mid"], int(100 * pulse)),
                 (sx - radius + 5, sy - radius // 4 + 2,
                  radius * 2 - 10, radius // 2 - 4), 1)

        # Rune marks in circle
        for i in range(6):
            angle = phase * 0.3 + i * math.pi / 3
            rx = sx + int(math.cos(angle) * (radius - 5))
            ry = sy + int(math.sin(angle) * (radius // 4 - 2))
            _NS_gravefang._aacircle(surface, (*_NS_gravefang.PALETTE["arc_light"], int(150 * pulse)),
                      (rx, ry), 3)


    def _draw_tempest_double(surface, boss, x, y, timer, phase):
        """Draw the tempest double forming/formed."""
        progress = max(0.0, min(1.0, 1 - timer / 100))
        sx = x + 50 * boss.direction
        sy = y

        if progress < 0.5:
            # Forming phase - ghostly silhouette rising
            form = progress / 0.5
            alpha = int(180 * form)

            # Rising energy pillar
            pillar_h = int(60 * form)
            for i in range(pillar_h):
                t = i / max(1, pillar_h)
                pw = int(15 * (1 - t * 0.3))
                pa = int(alpha * (1 - t * 0.5))
                _NS_gravefang._rect(surface, (*_NS_gravefang.PALETTE["magic_mid"], pa),
                      (sx - pw, sy + 20 - i, pw * 2, 2))

            # Lightning around pillar
            for i in range(4):
                angle = phase * 3 + i * math.pi / 2
                lx = sx + int(math.cos(angle) * 20)
                ly = sy + 20 - int(pillar_h * 0.5) + int(math.sin(angle) * pillar_h * 0.3)
                _NS_gravefang._draw_lightning_bolt(surface, (sx, sy + 20 - pillar_h // 2),
                                     (lx, ly),
                                     (*_NS_gravefang.PALETTE["arc_bright"], alpha),
                                     (*_NS_gravefang.PALETTE["arc_mid"], alpha // 2),
                                     segments=4, jitter=6)
        else:
            # Formed - draw ghostly copy of Morgath
            form = (progress - 0.5) / 0.5
            alpha = int(150 + form * 50)
            ghost = pygame.Surface((100, 120), pygame.SRCALPHA)
            # Draw a simplified ghostly version
            gcx, gcy = 50, 60
            # Body shape
            pygame.draw.circle(ghost, (*_NS_gravefang.PALETTE["magic_mid"], alpha), (gcx, gcy - 15), 10)
            pygame.draw.circle(ghost, (*_NS_gravefang.PALETTE["magic_light"], alpha // 2),
                               (gcx, gcy - 15), 7)
            # Torso
            _NS_gravefang._poly(ghost, (*_NS_gravefang.PALETTE["magic_dark"], alpha), [
                (gcx - 12, gcy - 8), (gcx + 12, gcy - 8),
                (gcx + 10, gcy + 12), (gcx - 10, gcy + 12),
            ])
            # Gem eye
            pygame.draw.circle(ghost, (*_NS_gravefang.PALETTE["gem_light"], min(255, alpha)),
                               (gcx, gcy - 15), 4)
            pygame.draw.circle(ghost, (*_NS_gravefang.PALETTE["gem_hot"], min(255, alpha)),
                               (gcx, gcy - 16), 2)
            # Cape wisps
            for i in range(3):
                wave = math.sin(phase + i) * 4
                _NS_gravefang._poly(ghost, (*_NS_gravefang.PALETTE["magic_dark"], alpha // 2), [
                    (gcx - 8 + i * 8, gcy + 10),
                    (gcx - 10 + i * 8 + int(wave), gcy + 30),
                    (gcx - 4 + i * 8 + int(wave * 0.5), gcy + 28),
                ])
            # Aura
            pygame.draw.circle(ghost, (*_NS_gravefang.PALETTE["arc_mid"], alpha // 3),
                               (gcx, gcy), 35, 2)

            surface.blit(ghost, (sx - 50, sy - 60))

            # Lightning connection between original and double
            _NS_gravefang._draw_lightning_bolt(surface, (x, y - 10), (sx, sy - 10),
                                 _NS_gravefang.PALETTE["arc_light"], _NS_gravefang.PALETTE["arc_mid"],
                                 segments=8, jitter=10, width_outer=2, width_inner=1)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_gravefang.draw_morgath(surface, boss, x, y)

    # ===================================================================
    # ALIAS - nama fungsi yang dipakai registry heroes/__init__.py
    # File ini punya implementasi visual sendiri, tapi nama fungsinya
    # masih ikut template Morgath. Alias supaya import tidak gagal
    # diam-diam (yang bikin boss render jadi bulat generic).
    # ===================================================================
    def draw_gravefang(surface, boss, x, y):
        """Entry point resmi untuk Gravefang."""
        _NS_gravefang.draw_morgath(surface, boss, x, y)


# ====================================================================
# VHALZUN
# ====================================================================
class _NS_vhalzun:
    """Namespace vhalzun - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Necrophos inspired dark green / necrotic
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Robe - dark teal/green
        "robe_darkest":   (8,   20,  18),
        "robe_dark":      (18,  42,  36),
        "robe_mid":       (35,  72,  58),
        "robe_light":     (58, 110,  88),
        "robe_high":      (95, 155, 125),
        "robe_shine":     (150, 200, 175),

        # Inner robe - darker
        "inner_darkest":  (5,   12,  10),
        "inner_dark":     (12,  25,  20),
        "inner_mid":      (22,  45,  35),

        # Skull - pale bone
        "bone_dark":      (60,  75,  55),
        "bone_mid":       (110, 130, 100),
        "bone_light":     (170, 185, 155),
        "bone_shine":     (215, 225, 200),

        # Necrotic green - main magical color
        "necro_darkest":  (5,   30,  10),
        "necro_dark":     (18,  75,  25),
        "necro_mid":      (40, 155,  55),
        "necro_light":    (90, 220,  95),
        "necro_bright":   (150, 250, 140),
        "necro_hot":      (200, 255, 180),
        "necro_white":    (235, 255, 220),

        # Scythe blade
        "blade_dark":     (35,  60,  40),
        "blade_mid":      (75, 130,  80),
        "blade_light":    (130, 200, 130),
        "blade_shine":    (200, 245, 200),

        # Gold trim
        "gold_dark":      (85,  60,  15),
        "gold_mid":       (155, 115, 35),
        "gold_light":     (215, 180, 70),
        "gold_shine":     (250, 225, 145),

        # Wood staff
        "wood_dark":      (40,  25,  15),
        "wood_mid":       (70,  45,  25),
        "wood_light":     (110, 78,  45),

        # Eye glow
        "eye_dark":       (25,  75,  20),
        "eye_mid":        (80, 200,  60),
        "eye_bright":     (170, 255, 130),
        "eye_hot":        (230, 255, 200),

        # Purple accent (small)
        "purple_dark":    (35,  15,  55),
        "purple_mid":     (75,  40, 115),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (3,   6,   4),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vhalzun._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_vhalzun.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_vhalzun._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
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
        color = _NS_vhalzun._clamp(color)
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
        color = _NS_vhalzun._clamp(color)
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
        color = _NS_vhalzun._clamp(color)
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
        return int(x + 200 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Necro particle helpers
    # ---------------------------------------------------------------------------
    def _draw_necro_orb(surface, x, y, size, phase, alpha=255):
        """Draw a glowing necrotic orb."""
        flick = math.sin(phase * 3) * 0.15 + 1.0
        s = int(size * flick)
        if s < 1:
            return
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_darkest"], alpha // 3), (x, y), s + 3)
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_dark"], alpha // 2), (x, y), s + 1)
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_mid"], alpha), (x, y), s)
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_light"], alpha), (x, y - 1),
                  max(1, s - 2))
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_bright"], min(255, alpha)),
                  (x, y - 2), max(1, s - 4))
        if s > 3:
            _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_hot"], min(255, alpha)),
                      (x, y - 2), max(1, s - 6))


    def _draw_mini_skull(surface, cx, cy, size=6, phase=0, alpha=220):
        """Draw a small skull (for aura, ghost shroud, etc)."""
        # Skull dome
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["bone_dark"], alpha), (cx, cy - 1), size)
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["bone_mid"], alpha), (cx - 1, cy - 2), size - 1)
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["bone_light"], alpha), (cx - 1, cy - 3),
                  max(1, size - 3))

        # Jaw
        _NS_vhalzun._rect(surface, (*_NS_vhalzun.PALETTE["bone_dark"], alpha),
              (cx - size + 2, cy + size - 3, (size - 2) * 2, 3))
        _NS_vhalzun._rect(surface, (*_NS_vhalzun.PALETTE["bone_mid"], alpha),
              (cx - size + 3, cy + size - 3, (size - 3) * 2, 2))

        # Teeth
        for i in range(3):
            tx = cx - 2 + i * 2
            _NS_vhalzun._rect(surface, _NS_vhalzun.PALETTE["shadow_deep"], (tx, cy + size - 2, 1, 2))

        # Eye sockets
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        eye_size = max(1, int(size // 3 * eye_pulse))
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["shadow_deep"],
                  (cx - size // 2, cy - 1), eye_size + 1)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["shadow_deep"],
                  (cx + size // 2, cy - 1), eye_size + 1)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["eye_bright"],
                  (cx - size // 2, cy - 1), eye_size)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["eye_hot"],
                  (cx - size // 2, cy - 1), max(1, eye_size - 1))
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["eye_bright"],
                  (cx + size // 2, cy - 1), eye_size)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["eye_hot"],
                  (cx + size // 2, cy - 1), max(1, eye_size - 1))


    def _draw_wraith(surface, cx, cy, phase, size=10, alpha=200):
        """Draw a wraith / ghost shroud creature."""
        wave = math.sin(phase * 2) * 2

        # Outer glow
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_darkest"], alpha // 3),
                  (cx, cy), size + 4)
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_dark"], alpha // 2),
                  (cx, cy), size + 2)

        # Wraith body (elongated tear shape)
        body_pts = [
            (cx - size + 1, cy - 2),
            (cx, cy - size),
            (cx + size - 1, cy - 2),
            (cx + size - 2, cy + size - 2),
            (cx + int(wave), cy + size + 2),
            (cx - size + 2, cy + size - 2),
        ]
        _NS_vhalzun._poly(surface, (*_NS_vhalzun.PALETTE["necro_dark"], alpha), body_pts)

        # Inner brighter
        inner_pts = [
            (cx - size + 3, cy - 1),
            (cx, cy - size + 2),
            (cx + size - 3, cy - 1),
            (cx + size - 4, cy + size - 3),
            (cx + int(wave * 0.5), cy + size),
            (cx - size + 4, cy + size - 3),
        ]
        _NS_vhalzun._poly(surface, (*_NS_vhalzun.PALETTE["necro_mid"], alpha), inner_pts)
        _NS_vhalzun._poly(surface, (*_NS_vhalzun.PALETTE["necro_light"], alpha // 2), [
            (cx - size // 2, cy),
            (cx, cy - size // 2),
            (cx + size // 2, cy),
            (cx + size // 2 - 1, cy + size - 4),
            (cx - size // 2 + 1, cy + size - 4),
        ])

        # Eye sockets
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["shadow_deep"],
                  (cx - size // 3, cy - 1), max(1, size // 4))
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["shadow_deep"],
                  (cx + size // 3, cy - 1), max(1, size // 4))
        # Eye glow
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["eye_bright"],
                  (cx - size // 3, cy - 1), max(1, size // 5))
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["eye_bright"],
                  (cx + size // 3, cy - 1), max(1, size // 5))

        # Tail wisps
        for i in range(3):
            tx = cx + (i - 1) * 2 + int(wave)
            ty = cy + size + 2 + i
            _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_mid"], alpha // 2),
                      (tx, ty), max(1, 2 - i // 2))


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM
    # ---------------------------------------------------------------------------
    class DeathPulseProjectile:
        """Green orb projectile from Death Pulse."""
        def __init__(self, sx, sy, tx, ty, speed=6.0):
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
            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(50 + i * 15)
                r = max(1, 6 - (len(self.trail) - i))
                _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_dark"], alpha), (tx, ty), r + 2)
                _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_mid"], alpha), (tx, ty), r)

            if self.alive:
                px, py = int(self.x), int(self.y)
                _NS_vhalzun._draw_necro_orb(surface, px, py, 7, phase, 240)
                # Orbiting sparks
                for i in range(4):
                    angle = phase * 5 + i * math.pi / 2
                    sx = px + int(math.cos(angle) * 10)
                    sy = py + int(math.sin(angle) * 10)
                    _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_hot"], (sx, sy), 1)


    class ReaperScytheProjectile:
        """Scythe wave projectile that flies at target."""
        def __init__(self, sx, sy, tx, ty, speed=9.0):
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
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 16:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 3:
                return
            # Long crescent trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(30 + i * 14)
                r = max(1, 5 - (len(self.trail) - i) // 2)
                _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_dark"], alpha), (tx, ty), r + 3)
                _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_mid"], alpha), (tx, ty), r + 1)
                _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_light"], alpha), (tx, ty), r)

            if self.alive:
                px, py = int(self.x), int(self.y)
                # Crescent/scythe wave shape
                perp = self.angle + math.pi / 2
                for i in range(-6, 7):
                    offset = i
                    # Curved wave shape
                    curve = math.cos(i * 0.25) * 8
                    wx = px + int(math.cos(perp) * offset - math.cos(self.angle) * curve)
                    wy = py + int(math.sin(perp) * offset - math.sin(self.angle) * curve)
                    _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_dark"], 180), (wx, wy), 3)
                    _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_mid"], 220), (wx, wy), 2)
                    _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_bright"], 240), (wx, wy), 1)

                # Bright core
                _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_hot"], (px, py), 3)
                _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_white"], (px, py), 1)


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_vh_last_x"):
            boss._vh_last_x = boss.x
            boss._vh_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vh_last_x)
        dy = abs(boss.y - boss._vh_last_y)
        boss._vh_last_x = boss.x
        boss._vh_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vh_prev_timer", 0))
        active = bool(getattr(boss, "_vh_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._vh_attack_active = True
            boss._vh_attack_frame = 0
            active = True
        elif active:
            boss._vh_attack_frame = int(getattr(boss, "_vh_attack_frame", 0)) + 1
            if boss._vh_attack_frame > cooldown:
                boss._vh_attack_active = False
                boss._vh_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._vh_attack_active = False
            boss._vh_attack_frame = 0
            active = False

        boss._vh_prev_timer = timer
        boss._vh_attack_progress = (
            min(1.0, getattr(boss, "_vh_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_vh_projectiles"):
            boss._vh_projectiles = []
        for proj in boss._vh_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._vh_projectiles = [p for p in boss._vh_projectiles
                                if p.alive or p.age < 8]


    def _spawn_basic_projectile(boss, x, y):
        if not hasattr(boss, "_vh_projectiles"):
            boss._vh_projectiles = []
        tx, ty = _NS_vhalzun._target_position(boss, x, y)
        sx = x + 22 * getattr(boss, "direction", 1)
        sy = y - 12
        boss._vh_projectiles.append(_NS_vhalzun.DeathPulseProjectile(sx, sy, tx, ty, speed=5.5))


    def _spawn_scythe_projectile(boss, x, y):
        if not hasattr(boss, "_vh_projectiles"):
            boss._vh_projectiles = []
        tx, ty = _NS_vhalzun._target_position(boss, x, y)
        sx = x + 22 * getattr(boss, "direction", 1)
        sy = y - 10
        boss._vh_projectiles.append(_NS_vhalzun.ReaperScytheProjectile(sx, sy, tx, ty, speed=9.0))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_vhalzun(surface, boss, x, y):
        """Entry point."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_vhalzun._detect_moving(boss)
        _NS_vhalzun._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_vh_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # ---------- Background layers ----------
        _NS_vhalzun._draw_necro_aura(surface, x, y, pulse)
        _NS_vhalzun._draw_ground_runes(surface, x, y + 38, pulse, active_skill)

        # ---------- Skill ground effects ----------
        if active_skill == "q":
            _NS_vhalzun._draw_death_pulse_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vhalzun._draw_heartstopper_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vhalzun._draw_ghost_shroud_ground(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if attacking:
            _NS_vhalzun._draw_vhalzun_attack(surface, boss, x, y)
        elif moving:
            _NS_vhalzun._draw_vhalzun_walk(surface, boss, x, y)
        else:
            _NS_vhalzun._draw_vhalzun_idle(surface, boss, x, y)

        # ---------- Projectiles ----------
        _NS_vhalzun._manage_projectiles(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "q":
            _NS_vhalzun._draw_death_pulse(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vhalzun._draw_heartstopper_aura(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vhalzun._draw_reapers_scythe(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vhalzun._draw_ghost_shroud(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_vhalzun_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_vhalzun._draw_shadow(surface, x, y + 48)
        _NS_vhalzun._draw_floating_mist(surface, x, y + 35, boss.pulse)
        _NS_vhalzun._draw_vhalzun_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_vhalzun_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(abs(math.sin(phase * 1.3)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_vhalzun._draw_shadow(surface, x + sway, y + 48)
        _NS_vhalzun._draw_floating_mist(surface, x + sway, y + 35, phase, trail=True,
                            facing=boss.direction)
        _NS_vhalzun._draw_vhalzun_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_vhalzun_attack(surface, boss, x, y):
        progress = getattr(boss, "_vh_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        if 0.28 < progress < 0.35 and not getattr(boss, "_vh_proj_spawned", False):
            _NS_vhalzun._spawn_basic_projectile(boss, x, y)
            boss._vh_proj_spawned = True
        if progress < 0.1 or progress > 0.9:
            boss._vh_proj_spawned = False

        recoil = int(math.sin(progress * math.pi) * 3) * -boss.direction
        _NS_vhalzun._draw_shadow(surface, x + recoil, y + 48)
        _NS_vhalzun._draw_floating_mist(surface, x + recoil, y + 35, boss.pulse, intense=True)
        _NS_vhalzun._draw_vhalzun_body(surface, x + recoil, y, boss.direction, boss.pulse,
                           "attack", progress)
        _NS_vhalzun._draw_cast_flash(surface, x + recoil, y, boss.direction, progress)


    # ===================================================================
    # BODY RENDERING – HD detailed Reaper
    # ===================================================================
    def _draw_vhalzun_body(surface, cx, cy, facing, phase, action,
                           attack_progress=0):
        """Main body composition."""
        # Scythe staff (behind body - drawn first)
        if action != "attack" or attack_progress < 0.3:
            _NS_vhalzun._draw_scythe_staff(surface, cx + facing * 16, cy - 5, facing, phase,
                              held=True)

        # Robe (large outer shape)
        _NS_vhalzun._draw_robe(surface, cx, cy + 5, phase)

        # Torso robe inner
        _NS_vhalzun._draw_robe_torso(surface, cx, cy - 8, phase)

        # Hood shoulders
        _NS_vhalzun._draw_hood_shoulders(surface, cx, cy - 14, phase)

        # Arms - one holding staff, one free
        if action == "attack":
            _NS_vhalzun._draw_casting_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        else:
            _NS_vhalzun._draw_idle_arms(surface, cx, cy - 8, facing, phase)

        # Head (skull inside hood)
        _NS_vhalzun._draw_hood_and_skull(surface, cx, cy - 30, facing, phase)

        # Scythe staff in front if attacking mid-swing
        if action == "attack" and attack_progress >= 0.3:
            # Staff drawn during arm sequence
            pass

        # Floating soul particles
        _NS_vhalzun._draw_body_soul_particles(surface, cx, cy, phase)


    def _draw_robe(surface, cx, cy, phase):
        """Long tattered robe."""
        sway = int(math.sin(phase * 0.7) * 3)
        sway2 = int(math.sin(phase * 0.5 + 1) * 2)

        # Outermost robe silhouette
        robe_outer = [
            (cx - 22, cy),
            (cx + 22, cy),
            (cx + 28 + sway, cy + 15),
            (cx + 26 + sway2, cy + 30),
            (cx + 22, cy + 42),
            (cx + 14, cy + 52 + sway2),
            (cx + 4, cy + 56),
            (cx - 4, cy + 56),
            (cx - 14, cy + 52 - sway2),
            (cx - 22, cy + 42),
            (cx - 26 - sway2, cy + 30),
            (cx - 28 - sway, cy + 15),
        ]
        _NS_vhalzun._poly(surface, _NS_vhalzun.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in robe_outer])
        _NS_vhalzun._poly(surface, _NS_vhalzun.PALETTE["robe_darkest"], robe_outer)

        # Mid robe
        robe_mid = [
            (cx - 19, cy + 2),
            (cx + 19, cy + 2),
            (cx + 24 + sway, cy + 15),
            (cx + 22 + sway2, cy + 28),
            (cx + 18, cy + 40),
            (cx + 10, cy + 48),
            (cx - 10, cy + 48),
            (cx - 18, cy + 40),
            (cx - 22 - sway2, cy + 28),
            (cx - 24 - sway, cy + 15),
        ]
        _NS_vhalzun._poly(surface, _NS_vhalzun.PALETTE["robe_dark"], robe_mid)

        # Inner robe (with darker interior)
        robe_inner = [
            (cx - 15, cy + 4),
            (cx + 15, cy + 4),
            (cx + 19 + sway, cy + 15),
            (cx + 16, cy + 26),
            (cx + 12, cy + 36),
            (cx - 12, cy + 36),
            (cx - 16, cy + 26),
            (cx - 19 - sway, cy + 15),
        ]
        _NS_vhalzun._poly(surface, _NS_vhalzun.PALETTE["inner_mid"], robe_inner)

        # Robe fold lines (lighter highlights)
        for xoff in (-10, -5, 0, 5, 10):
            _NS_vhalzun._aaline(surface, _NS_vhalzun.PALETTE["robe_mid"],
                    (cx + xoff, cy + 6), (cx + xoff, cy + 32), 1)

        # Highlights
        _NS_vhalzun._aaline(surface, _NS_vhalzun.PALETTE["robe_light"],
                (cx - 12, cy + 4), (cx - 15, cy + 30), 1)
        _NS_vhalzun._aaline(surface, _NS_vhalzun.PALETTE["robe_light"],
                (cx + 12, cy + 4), (cx + 15, cy + 30), 1)

        # Tattered bottom edges
        for i in range(10):
            tx = cx - 22 + i * 5
            ty = cy + 44 + int(math.sin(phase * 1.5 + i) * 5)
            _NS_vhalzun._poly(surface, _NS_vhalzun.PALETTE["robe_darkest"], [
                (tx - 3, cy + 40), (tx + 3, cy + 40),
                (tx + 1, ty + 7), (tx - 1, ty + 7),
            ])

        # Green necrotic glow beneath robe
        for i in range(6):
            alpha = 70 - i * 10
            _NS_vhalzun._ellipse(surface, (*_NS_vhalzun.PALETTE["necro_mid"], alpha),
                     (cx - 28 + i * 2, cy + 50 - i, 56 - i * 4, 10))

        # Rope/sash at waist
        _NS_vhalzun._rect(surface, _NS_vhalzun.PALETTE["robe_darkest"], (cx - 16, cy - 1, 32, 5))
        _NS_vhalzun._rect(surface, _NS_vhalzun.PALETTE["robe_dark"], (cx - 15, cy, 30, 3))
        _NS_vhalzun._rect(surface, _NS_vhalzun.PALETTE["robe_mid"], (cx - 13, cy + 1, 26, 1))

        # Green gem on sash
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_darkest"], (cx, cy + 2), 4)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_dark"], (cx, cy + 2), 3)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_mid"], (cx, cy + 1),
                  max(1, int(3 * pulse)))
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_bright"], (cx, cy + 1),
                  max(1, int(2 * pulse)))
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_hot"], (cx, cy + 1), 1)


    def _draw_robe_torso(surface, cx, cy, phase):
        """Inner torso section under hood."""
        # Inner shadow of hood
        _NS_vhalzun._poly(surface, _NS_vhalzun.PALETTE["inner_darkest"], [
            (cx - 11, cy - 8), (cx + 11, cy - 8),
            (cx + 13, cy + 12), (cx + 4, cy + 17),
            (cx - 4, cy + 17), (cx - 13, cy + 12),
        ])
        _NS_vhalzun._poly(surface, _NS_vhalzun.PALETTE["inner_dark"], [
            (cx - 9, cy - 6), (cx + 9, cy - 6),
            (cx + 11, cy + 10), (cx + 3, cy + 14),
            (cx - 3, cy + 14), (cx - 11, cy + 10),
        ])

        # Gold chest decoration (like small chain necklace/emblem)
        _NS_vhalzun._rect(surface, _NS_vhalzun.PALETTE["gold_dark"], (cx - 5, cy + 2, 10, 2))
        _NS_vhalzun._rect(surface, _NS_vhalzun.PALETTE["gold_mid"], (cx - 4, cy + 2, 8, 1))

        # Small green gem in center of chest
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_dark"], (cx, cy + 5), 3)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_mid"], (cx, cy + 5), 2)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_bright"], (cx, cy + 4), 1)


    def _draw_hood_shoulders(surface, cx, cy, phase):
        """Shoulders of the hood/robe."""
        for side in (-1, 1):
            sx = cx + side * 14
            # Shadow
            _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["shadow_deep"], (sx + 2, cy + 2), 9)
            # Shoulder pad
            _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["robe_darkest"], (sx, cy), 8)
            _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["robe_dark"], (sx - side, cy - 1), 6)
            _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["robe_mid"], (sx - side, cy - 2), 4)
            _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["robe_light"], (sx - side * 2, cy - 3), 2)


    def _draw_hood_and_skull(surface, cx, cy, facing, phase):
        """Hood covering skull - reaper look."""
        # Hood - large outer piece
        hood_pts = [
            (cx - 14, cy - 4),
            (cx - 12, cy - 13),
            (cx - 6, cy - 17),
            (cx, cy - 19),
            (cx + 6, cy - 17),
            (cx + 12, cy - 13),
            (cx + 14, cy - 4),
            (cx + 15, cy + 8),
            (cx + 8, cy + 12),
            (cx - 8, cy + 12),
            (cx - 15, cy + 8),
        ]
        _NS_vhalzun._poly(surface, _NS_vhalzun.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in hood_pts])
        _NS_vhalzun._poly(surface, _NS_vhalzun.PALETTE["robe_darkest"], hood_pts)

        # Hood inner
        hood_inner = [
            (cx - 12, cy - 3),
            (cx - 10, cy - 12),
            (cx - 5, cy - 15),
            (cx, cy - 17),
            (cx + 5, cy - 15),
            (cx + 10, cy - 12),
            (cx + 12, cy - 3),
            (cx + 13, cy + 6),
            (cx + 7, cy + 10),
            (cx - 7, cy + 10),
            (cx - 13, cy + 6),
        ]
        _NS_vhalzun._poly(surface, _NS_vhalzun.PALETTE["robe_dark"], hood_inner)

        # Hood edge highlight
        _NS_vhalzun._aaline(surface, _NS_vhalzun.PALETTE["robe_mid"],
                (cx - 11, cy - 12), (cx, cy - 17), 1)
        _NS_vhalzun._aaline(surface, _NS_vhalzun.PALETTE["robe_mid"],
                (cx + 11, cy - 12), (cx, cy - 17), 1)
        _NS_vhalzun._aaline(surface, _NS_vhalzun.PALETTE["robe_light"],
                (cx - 6, cy - 15), (cx, cy - 17), 1)

        # Dark interior of hood (where skull sits)
        _NS_vhalzun._poly(surface, _NS_vhalzun.PALETTE["inner_darkest"], [
            (cx - 9, cy - 8),
            (cx - 8, cy - 12),
            (cx, cy - 14),
            (cx + 8, cy - 12),
            (cx + 9, cy - 8),
            (cx + 8, cy + 5),
            (cx, cy + 8),
            (cx - 8, cy + 5),
        ])
        _NS_vhalzun._poly(surface, _NS_vhalzun.PALETTE["shadow_deep"], [
            (cx - 7, cy - 7),
            (cx - 7, cy - 10),
            (cx, cy - 12),
            (cx + 7, cy - 10),
            (cx + 7, cy - 7),
            (cx + 6, cy + 4),
            (cx, cy + 6),
            (cx - 6, cy + 4),
        ])

        # SKULL inside hood
        _NS_vhalzun._draw_skull_face(surface, cx, cy - 2, phase, facing)

        # Green glow from hood interior
        glow_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_mid"], int(80 * glow_pulse)),
                  (cx, cy), 12)
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_bright"], int(60 * glow_pulse)),
                  (cx, cy), 8)


    def _draw_skull_face(surface, cx, cy, phase, facing):
        """Skull face inside hood."""
        # Skull dome
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["bone_dark"], (cx, cy - 1), 7)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["bone_mid"], (cx - 1, cy - 2), 6)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["bone_light"], (cx - 2, cy - 3), 3)

        # Cheek bones shading
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["bone_dark"], (cx - 4, cy + 1), 2)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["bone_dark"], (cx + 4, cy + 1), 2)

        # Eye sockets - deep dark with green glow
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["shadow_deep"], (cx - 3, cy - 1), 3)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["shadow_deep"], (cx + 3, cy - 1), 3)

        # Glowing green eyes
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        eye_size = max(1, int(2 * eye_pulse))
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["eye_dark"], (cx - 3, cy - 1), eye_size + 1)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["eye_mid"], (cx - 3, cy - 1), eye_size)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["eye_bright"], (cx - 3, cy - 1),
                  max(1, eye_size - 1))
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["eye_hot"], (cx - 3, cy - 1), 1)

        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["eye_dark"], (cx + 3, cy - 1), eye_size + 1)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["eye_mid"], (cx + 3, cy - 1), eye_size)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["eye_bright"], (cx + 3, cy - 1),
                  max(1, eye_size - 1))
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["eye_hot"], (cx + 3, cy - 1), 1)

        # Nose cavity (triangular)
        _NS_vhalzun._poly(surface, _NS_vhalzun.PALETTE["shadow_deep"], [
            (cx, cy + 1), (cx - 1, cy + 4), (cx + 1, cy + 4)
        ])

        # Jaw with teeth
        _NS_vhalzun._rect(surface, _NS_vhalzun.PALETTE["bone_dark"], (cx - 5, cy + 5, 10, 3))
        _NS_vhalzun._rect(surface, _NS_vhalzun.PALETTE["bone_mid"], (cx - 4, cy + 5, 8, 2))

        # Teeth
        for i in range(4):
            tx = cx - 3 + i * 2
            _NS_vhalzun._rect(surface, _NS_vhalzun.PALETTE["shadow_deep"], (tx, cy + 6, 1, 2))


    def _draw_scythe_staff(surface, hx, hy, facing, phase, held=True):
        """The scythe/reaper staff."""
        # Staff top and bottom
        staff_top_x = hx
        staff_top_y = hy - 32
        staff_bottom_x = hx + int(math.sin(phase * 0.5) * 1)
        staff_bottom_y = hy + 24

        # Staff shaft (wood)
        _NS_vhalzun._aaline(surface, _NS_vhalzun.PALETTE["shadow_deep"],
                (staff_top_x + 2, staff_top_y + 2),
                (staff_bottom_x + 2, staff_bottom_y + 2), 5)
        _NS_vhalzun._aaline(surface, _NS_vhalzun.PALETTE["wood_dark"],
                (staff_top_x, staff_top_y),
                (staff_bottom_x, staff_bottom_y), 4)
        _NS_vhalzun._aaline(surface, _NS_vhalzun.PALETTE["wood_mid"],
                (staff_top_x, staff_top_y),
                (staff_bottom_x, staff_bottom_y), 3)
        _NS_vhalzun._aaline(surface, _NS_vhalzun.PALETTE["wood_light"],
                (staff_top_x - 1, staff_top_y),
                (staff_bottom_x - 1, staff_bottom_y), 1)

        # Wood grain (small dark lines)
        for i in range(3):
            yoff = staff_top_y + (i + 1) * 15
            _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["wood_dark"], (staff_top_x, yoff), 2)

        # ===== SCYTHE BLADE (top) =====
        blade_base_x = staff_top_x
        blade_base_y = staff_top_y

        # Blade extends to one side (curved crescent)
        blade_dir = facing
        blade_tip_x = blade_base_x + blade_dir * 22
        blade_tip_y = blade_base_y - 8

        # Blade curve points
        blade_pts_outer = [
            (blade_base_x, blade_base_y - 2),
            (blade_base_x + blade_dir * 8, blade_base_y - 12),
            (blade_base_x + blade_dir * 18, blade_base_y - 12),
            (blade_tip_x, blade_tip_y),
            (blade_base_x + blade_dir * 15, blade_base_y - 3),
            (blade_base_x + blade_dir * 5, blade_base_y + 1),
        ]
        _NS_vhalzun._poly(surface, _NS_vhalzun.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in blade_pts_outer])
        _NS_vhalzun._poly(surface, _NS_vhalzun.PALETTE["blade_dark"], blade_pts_outer)

        # Blade inner
        blade_inner = [
            (blade_base_x + blade_dir * 2, blade_base_y - 3),
            (blade_base_x + blade_dir * 8, blade_base_y - 10),
            (blade_base_x + blade_dir * 16, blade_base_y - 10),
            (blade_base_x + blade_dir * 20, blade_tip_y + 1),
            (blade_base_x + blade_dir * 13, blade_base_y - 4),
            (blade_base_x + blade_dir * 6, blade_base_y),
        ]
        _NS_vhalzun._poly(surface, _NS_vhalzun.PALETTE["blade_mid"], blade_inner)

        # Blade shine (inner edge)
        _NS_vhalzun._aaline(surface, _NS_vhalzun.PALETTE["blade_light"],
                (blade_base_x + blade_dir * 3, blade_base_y - 5),
                (blade_base_x + blade_dir * 18, blade_base_y - 8), 1)
        _NS_vhalzun._aaline(surface, _NS_vhalzun.PALETTE["blade_shine"],
                (blade_base_x + blade_dir * 4, blade_base_y - 6),
                (blade_base_x + blade_dir * 17, blade_base_y - 9), 1)

        # Green necrotic glow on blade edge
        for i in range(6):
            t = i / 6
            gx = blade_base_x + int(blade_dir * (5 + t * 15))
            gy = blade_base_y - int(3 + t * 5)
            pulse = math.sin(phase * 3 + i) * 0.3 + 0.7
            _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_mid"], int(150 * pulse)),
                      (gx, gy), 2)
            _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_bright"], int(180 * pulse)),
                      (gx, gy), 1)

        # Gold connector between blade and shaft
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["gold_dark"], (blade_base_x, blade_base_y), 4)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["gold_mid"], (blade_base_x, blade_base_y), 3)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["gold_light"],
                  (blade_base_x - 1, blade_base_y - 1), 1)

        # ===== LANTERN/ORB at bottom =====
        lantern_x = staff_bottom_x
        lantern_y = staff_bottom_y

        # Lantern hanging chain
        _NS_vhalzun._aaline(surface, _NS_vhalzun.PALETTE["gold_dark"],
                (lantern_x, lantern_y - 3), (lantern_x, lantern_y + 2), 1)

        # Lantern frame
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["gold_dark"], (lantern_x, lantern_y + 4), 5)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["gold_mid"], (lantern_x, lantern_y + 4), 4)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["gold_light"], (lantern_x - 1, lantern_y + 3), 2)

        # Green flame inside
        flame_pulse = math.sin(phase * 4) * 0.3 + 0.7
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_darkest"], (lantern_x, lantern_y + 4), 3)
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_mid"], 220),
                  (lantern_x, lantern_y + 4), int(3 * flame_pulse))
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_bright"], 240),
                  (lantern_x, lantern_y + 3), int(2 * flame_pulse))
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_hot"],
                  (lantern_x, lantern_y + 3), max(1, int(1 * flame_pulse)))

        # Lantern glow radius
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_mid"], int(60 * flame_pulse)),
                  (lantern_x, lantern_y + 4), 12)


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Arms - one holding scythe, one extended."""
        sway = math.sin(phase * 0.7) * 2

        # Staff hand (facing side) - up near staff
        ss_x = cx + facing * 12
        ss_y = cy + 2
        se_x = ss_x + facing * 6
        se_y = cy + 10
        sh_x = cx + facing * 16  # goes to staff
        sh_y = cy - 3

        _NS_vhalzun._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_vhalzun._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        # Extended free hand (opposite side) - reaching out with glow
        fs_x = cx + (-facing) * 12
        fs_y = cy + 2
        fe_x = fs_x + (-facing) * 8
        fe_y = cy + 10 + int(sway)
        fh_x = fe_x + (-facing) * 6
        fh_y = fe_y + 4

        _NS_vhalzun._draw_arm_segment(surface, fs_x, fs_y, fe_x, fe_y)
        _NS_vhalzun._draw_arm_segment(surface, fe_x, fe_y, fh_x, fh_y)
        _NS_vhalzun._draw_hand_glow(surface, fh_x, fh_y, phase, 5)


    def _draw_casting_arms(surface, cx, cy, facing, phase, progress):
        """Casting arms - one hand pointing forward."""
        # Staff arm stays holding staff
        ss_x = cx + facing * 12
        ss_y = cy + 2
        se_x = ss_x + facing * 6
        se_y = cy + 10
        sh_x = cx + facing * 16
        sh_y = cy - 3
        _NS_vhalzun._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_vhalzun._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        # But shift staff position based on progress for casting animation
        staff_offset_y = int(math.sin(progress * math.pi) * -3)
        _NS_vhalzun._draw_scythe_staff(surface, cx + facing * 16, cy - 5 + staff_offset_y,
                           facing, phase, held=True)

        # Casting arm - extends forward
        fs_x = cx + (-facing) * 12
        fs_y = cy + 2

        if progress < 0.3:
            t = progress / 0.3
            arm_angle = -0.5 * t
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            arm_angle = -0.5 + 1.3 * t
        else:
            t = (progress - 0.5) / 0.5
            arm_angle = 0.8 - 0.6 * t

        # Note: casting arm goes toward facing direction (crosses body if needed)
        # Actually for necrophos, the free hand extends toward target
        # Since staff is on facing side, free hand also extends toward facing target
        fe_x = fs_x + int(math.cos(arm_angle) * 12) * facing
        fe_y = fs_y + int(math.sin(arm_angle) * 12) - 2
        fh_x = fe_x + int(math.cos(arm_angle) * 10) * facing
        fh_y = fe_y + int(math.sin(arm_angle) * 10)

        _NS_vhalzun._draw_arm_segment(surface, fs_x, fs_y, fe_x, fe_y)
        _NS_vhalzun._draw_arm_segment(surface, fe_x, fe_y, fh_x, fh_y)

        # Charging glow on hand
        glow_size = 5 + int(math.sin(progress * math.pi) * 6)
        _NS_vhalzun._draw_hand_glow(surface, fh_x, fh_y, phase, glow_size)

        # Necrotic energy sparks
        if 0.2 < progress < 0.6:
            intensity = math.sin((progress - 0.2) / 0.4 * math.pi)
            for i in range(4):
                angle = phase * 4 + i * math.pi / 2
                ex = fh_x + int(math.cos(angle) * 14 * intensity) * facing
                ey = fh_y + int(math.sin(angle) * 12 * intensity)
                _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_bright"], 220), (ex, ey), 2)
                _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_hot"], 240), (ex, ey), 1)


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Robe sleeve arm segment."""
        _NS_vhalzun._aaline(surface, _NS_vhalzun.PALETTE["shadow_deep"],
                (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 7)
        _NS_vhalzun._aaline(surface, _NS_vhalzun.PALETTE["robe_darkest"], (x1, y1), (x2, y2), 6)
        _NS_vhalzun._aaline(surface, _NS_vhalzun.PALETTE["robe_dark"], (x1, y1), (x2, y2), 4)
        _NS_vhalzun._aaline(surface, _NS_vhalzun.PALETTE["robe_mid"], (x1, y1), (x2, y2), 2)
        _NS_vhalzun._aaline(surface, _NS_vhalzun.PALETTE["robe_light"], (x1 - 1, y1), (x2 - 1, y2), 1)


    def _draw_hand_glow(surface, x, y, phase, size=5):
        """Glowing skeletal hand."""
        pulse = math.sin(phase * 2.0) * 0.3 + 0.7
        s = int(size * pulse)

        # Skeletal hand hint
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["bone_dark"], (x, y), 3)
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["bone_mid"], (x, y - 1), 2)

        # Necrotic glow
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_darkest"], 100), (x, y), s + 6)
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_dark"], 150), (x, y), s + 3)
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_mid"], 200), (x, y), s)
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_bright"], 220), (x, y), max(1, s - 2))
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_hot"], 240), (x, y), max(1, s - 4))

        # Sparks
        for i in range(3):
            angle = phase * 3 + i * math.pi * 2 / 3
            sx = x + int(math.cos(angle) * (s + 4))
            sy = y + int(math.sin(angle) * (s + 4))
            _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_hot"], (sx, sy), 1)


    def _draw_body_soul_particles(surface, cx, cy, phase):
        """Necrotic particles around body."""
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            radius = 30 + int(math.sin(phase * 0.7 + i) * 8)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(140 + math.sin(phase + i * 0.7) * 60)
            _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_dark"], alpha), (px, py), 2)
            _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_bright"], alpha // 2), (px, py), 1)

        # Rising soul embers
        for i in range(5):
            t = ((phase * 0.4 + i * 0.2) % 1.0)
            px = cx + int(math.sin(phase + i) * 20) + (i - 2) * 4
            py = cy + 20 - int(t * 55)
            alpha = int(200 * (1 - t))
            if alpha > 0:
                _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_light"], alpha), (px, py), 1)
                _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_hot"], alpha), (px, py - 1), 1)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_mist(surface, cx, cy, phase, trail=False,
                           facing=1, intense=False):
        """Necrotic mist below floating Vhalzun."""
        strength = 1.5 if intense else 1.0

        # Base mist
        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(32, 3, -4):
            alpha = int((32 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_vhalzun.PALETTE["necro_darkest"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising green wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 24)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_dark"], alpha), (sx, sy), 5)
            _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_mid"], alpha), (sx, sy - 2), 3)
            _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_bright"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Small orbiting orbs
        for i in range(5):
            angle = phase * 0.9 + i * math.pi * 2 / 5
            r = 22 + int(math.sin(phase + i * 1.3) * 4)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 6)
            _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_mid"], (sx, sy), 3)
            _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_light"], (sx, sy), 2)
            _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_hot"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 130 - i * 22)
                _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y):
        """Ground shadow."""
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_vhalzun.PALETTE["necro_darkest"], 60), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_necro_aura(surface, x, y, phase):
        """Background necrotic aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(72, 5, -4):
            alpha = int((72 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_vhalzun._aacircle(aura, (*_NS_vhalzun.PALETTE["necro_darkest"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))


    def _draw_ground_runes(surface, x, y, phase, skill):
        """Necrotic runes on ground."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_vhalzun.PALETTE["necro_dark"], 140),
                            (5, 10, 120, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_vhalzun.PALETTE["necro_mid"], 170),
                            (20, 14, 90, 16), 2)

        # Runes
        for i in range(10):
            angle = phase * 0.2 + i * math.pi / 5
            x1 = 65 + int(math.cos(angle) * 30)
            y1 = 22 + int(math.sin(angle) * 6)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_vhalzun.PALETTE["necro_bright"], 160),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_vhalzun.PALETTE["necro_hot"], int(80 * pulse)),
                                (15, 8, 100, 28), 1)

        surface.blit(ring, (x - 65, y - 22))


    def _draw_cast_flash(surface, x, y, facing, progress):
        """Flash effect during ranged attack."""
        if progress < 0.2 or progress > 0.65:
            return
        t = (progress - 0.2) / 0.45
        intensity = math.sin(t * math.pi)

        # Flash near free hand
        flash_x = x + facing * 24
        flash_y = y - 8

        alpha = int(180 * intensity)
        radius = int(8 + intensity * 15)

        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_dark"], alpha // 2),
                  (flash_x, flash_y), radius + 8)
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_mid"], alpha),
                  (flash_x, flash_y), radius)
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_bright"], alpha),
                  (flash_x, flash_y), radius // 2)
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_hot"], min(255, alpha)),
                  (flash_x, flash_y), max(1, radius // 4))


    # ===================================================================
    # SKILL Q: DEATH PULSE
    # ===================================================================
    def _draw_death_pulse_ground(surface, boss, x, y, timer, phase):
        """Expanding shockwave on ground."""
        progress = max(0.0, min(1.0, 1 - timer / 60))
        pulse = math.sin(phase * 2) * 0.2 + 0.8
        radius = int(20 + progress * 90)

        alpha = int(180 * (1 - progress) * pulse)
        _NS_vhalzun._ellipse(surface, (*_NS_vhalzun.PALETTE["necro_mid"], alpha),
                 (x - radius, y + 32 - radius // 4, radius * 2, radius // 2), 3)
        _NS_vhalzun._ellipse(surface, (*_NS_vhalzun.PALETTE["necro_bright"], alpha),
                 (x - radius + 5, y + 34 - radius // 4,
                  radius * 2 - 10, radius // 2 - 4), 2)


    def _draw_death_pulse(surface, boss, x, y, timer, phase):
        """Expanding ring of green death energy from Vhalzun."""
        progress = max(0.0, min(1.0, 1 - timer / 60))

        # Expanding pulse rings
        for ring_i in range(2):
            ring_progress = progress - ring_i * 0.15
            if ring_progress <= 0 or ring_progress > 1:
                continue
            radius = int(15 + ring_progress * 100)
            alpha = int(220 * (1 - ring_progress))

            # Multi-layered ring
            _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_dark"], alpha // 2),
                      (x, y - 10), radius + 4, 4)
            _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_mid"], alpha),
                      (x, y - 10), radius + 2, 3)
            _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_bright"], alpha),
                      (x, y - 10), radius, 2)
            _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_hot"], alpha),
                      (x, y - 10), max(1, radius - 2), 1)

            # Particles along the ring
            particle_count = int(12 + ring_progress * 8)
            for i in range(particle_count):
                angle = i * math.pi * 2 / particle_count + phase * 0.5
                px = x + int(math.cos(angle) * radius)
                py = y - 10 + int(math.sin(angle) * radius * 0.7)
                _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_hot"], (px, py), 2)
                _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_white"], (px, py), 1)

        # Central burst
        if progress < 0.3:
            burst_r = int(30 * (1 - progress / 0.3))
            burst_alpha = int(240 * (1 - progress / 0.3))
            _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_bright"], burst_alpha),
                      (x, y - 10), burst_r)
            _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_hot"], burst_alpha),
                      (x, y - 10), max(1, burst_r - 5))
            _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_white"], min(255, burst_alpha)),
                      (x, y - 10), max(1, burst_r - 10))


    # ===================================================================
    # SKILL W: HEARTSTOPPER AURA
    # ===================================================================
    def _draw_heartstopper_ground(surface, boss, x, y, timer, phase):
        """Aura ground circle."""
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8
        radius = 65

        # Large aura circle on ground
        for i in range(3):
            r = radius - i * 8
            alpha = int(80 * pulse) - i * 15
            if alpha > 0:
                _NS_vhalzun._ellipse(surface, (*_NS_vhalzun.PALETTE["necro_mid"], alpha),
                         (x - r, y + 32 - r // 4, r * 2, r // 2), 3)


    def _draw_heartstopper_aura(surface, boss, x, y, timer, phase):
        """Passive skull aura around Vhalzun."""
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8

        # Orbiting skulls
        skull_count = 6
        for i in range(skull_count):
            angle = phase * 0.6 + i * math.pi * 2 / skull_count
            r_x = 55 + int(math.sin(phase + i) * 5)
            r_y = 22 + int(math.sin(phase * 0.7 + i * 1.2) * 3)
            sx = x + int(math.cos(angle) * r_x)
            sy = y + 10 + int(math.sin(angle) * r_y)

            bob = int(math.sin(phase * 2 + i * 0.5) * 3)
            _NS_vhalzun._draw_mini_skull(surface, sx, sy + bob, size=5, phase=phase + i,
                             alpha=int(230 * pulse))

        # Heart-like pulse (small heart icons rising)
        for i in range(3):
            t = ((phase * 0.4 + i * 0.33) % 1.0)
            hx = x + (i - 1) * 20 + int(math.sin(phase + i) * 5)
            hy = y - 30 - int(t * 30)
            alpha = int(200 * (1 - t) * pulse)
            if alpha > 0:
                # Simple heart shape (two circles + triangle)
                _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_light"], alpha),
                          (hx - 2, hy), 2)
                _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_light"], alpha),
                          (hx + 2, hy), 2)
                _NS_vhalzun._poly(surface, (*_NS_vhalzun.PALETTE["necro_light"], alpha), [
                    (hx - 3, hy + 1), (hx + 3, hy + 1), (hx, hy + 5)
                ])
                _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_bright"], alpha), (hx, hy + 1), 1)

        # Faint green damaging aura tint
        aura_surf = pygame.Surface((160, 100), pygame.SRCALPHA)
        for r in range(50, 5, -4):
            alpha = int((50 - r) * 0.6 * pulse)
            if alpha > 0:
                _NS_vhalzun._aacircle(aura_surf, (*_NS_vhalzun.PALETTE["necro_mid"], min(80, alpha)),
                          (80, 50), r)
        surface.blit(aura_surf, (x - 80, y - 20))


    # ===================================================================
    # SKILL E: REAPER'S SCYTHE
    # ===================================================================
    def _draw_reapers_scythe(surface, boss, x, y, timer, phase):
        """Launch scythe projectile at target."""
        # Spawn scythe once
        if not getattr(boss, "_vh_scythe_spawned", False):
            _NS_vhalzun._spawn_scythe_projectile(boss, x, y)
            boss._vh_scythe_spawned = True

        if timer <= 5:
            boss._vh_scythe_spawned = False

        # Casting glow at hand
        hand_x = x + boss.direction * 24
        hand_y = y - 8
        pulse = math.sin(phase * 4) * 0.3 + 0.7
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_dark"], 150),
                  (hand_x, hand_y), int(12 * pulse))
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_mid"], 200),
                  (hand_x, hand_y), int(8 * pulse))
        _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_bright"], 230),
                  (hand_x, hand_y), int(5 * pulse))
        _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_hot"],
                  (hand_x, hand_y), max(1, int(3 * pulse)))

        # Scythe trail lines
        for i in range(4):
            angle = phase * 3 + i * math.pi / 2
            ex = hand_x + int(math.cos(angle) * 15) * boss.direction
            ey = hand_y + int(math.sin(angle) * 12)
            _NS_vhalzun._aaline(surface, (*_NS_vhalzun.PALETTE["necro_bright"], 180),
                    (hand_x, hand_y), (ex, ey), 2)


    # ===================================================================
    # SKILL R: GHOST SHROUD
    # ===================================================================
    def _draw_ghost_shroud_ground(surface, boss, x, y, timer, phase):
        """Ground ring for ghost shroud."""
        progress = max(0.0, min(1.0, 1 - timer / 120))
        pulse = math.sin(phase * 2) * 0.2 + 0.8
        radius = int(55 + progress * 25)

        _NS_vhalzun._ellipse(surface, (*_NS_vhalzun.PALETTE["necro_darkest"], int(180 * pulse)),
                 (x - radius, y + 30 - radius // 3, radius * 2, radius * 2 // 3), 4)
        _NS_vhalzun._ellipse(surface, (*_NS_vhalzun.PALETTE["necro_dark"], int(150 * pulse)),
                 (x - radius + 5, y + 32 - radius // 3,
                  radius * 2 - 10, radius * 2 // 3 - 6), 3)
        _NS_vhalzun._ellipse(surface, (*_NS_vhalzun.PALETTE["necro_mid"], int(120 * pulse)),
                 (x - radius + 10, y + 34 - radius // 3,
                  radius * 2 - 20, radius * 2 // 3 - 12), 2)

        # Rune spots in circle
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            rx = x + int(math.cos(angle) * (radius - 8))
            ry = y + 38 + int(math.sin(angle) * (radius // 3 - 4))
            _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_bright"], (rx, ry), 3)
            _NS_vhalzun._aacircle(surface, _NS_vhalzun.PALETTE["necro_hot"], (rx, ry), 1)


    def _draw_ghost_shroud(surface, boss, x, y, timer, phase):
        """Wraiths rising up around Vhalzun."""
        progress = max(0.0, min(1.0, 1 - timer / 120))

        # Multiple wraiths at different positions
        wraith_positions = [
            # (angle_offset, radius_x, radius_y, size, delay)
            (0.0, 55, 15, 10, 0.0),
            (0.5, 70, 22, 9, 0.1),
            (1.0, 45, 12, 8, 0.05),
            (1.5, 78, 26, 11, 0.15),
            (2.0, 60, 18, 9, 0.08),
            (2.5, 72, 22, 10, 0.12),
            (3.0, 48, 14, 8, 0.03),
            (3.5, 65, 20, 9, 0.1),
            (4.0, 76, 24, 10, 0.14),
            (4.5, 50, 13, 8, 0.06),
        ]

        for angle_off, rx, ry, size, delay in wraith_positions:
            if progress < delay:
                continue

            wraith_progress = min(1.0, (progress - delay) / max(0.1, 1 - delay))

            angle = angle_off + phase * 0.3
            base_x = x + int(math.cos(angle) * rx)

            # Wraiths rise from ground
            rise = wraith_progress * 40
            base_y = y + 40 - int(rise) + int(math.sin(phase + angle_off) * 3)

            alpha = int(230 * min(1.0, wraith_progress * 2))
            bob = int(math.sin(phase * 2 + angle_off) * 3)

            _NS_vhalzun._draw_wraith(surface, base_x, base_y + bob, phase + angle_off,
                        size=size, alpha=alpha)

            # Rising trail wisps below
            for j in range(3):
                wisp_y = base_y + 12 + j * 5
                wisp_alpha = max(0, alpha - (j + 1) * 60)
                _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_mid"], wisp_alpha),
                          (base_x + int(math.sin(phase + j) * 2), wisp_y),
                          max(1, 3 - j))

        # Extra rising green particles
        for i in range(15):
            t = ((phase * 0.5 + i * 0.12) % 1.0)
            angle = i * math.pi * 2 / 15
            r = 40 + int(math.sin(phase + i) * 15)
            px = x + int(math.cos(angle) * r)
            py = y + 40 - int(t * 60) + int(math.sin(phase + i) * 3)
            alpha = int(200 * (1 - t))
            if alpha > 0:
                _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_light"], alpha), (px, py), 2)
                _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_hot"], alpha), (px, py - 1), 1)

        # Ghostly aura around Vhalzun (protection effect)
        aura_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(35, 5, -3):
            alpha = int((35 - r) * 3 * aura_pulse)
            _NS_vhalzun._aacircle(surface, (*_NS_vhalzun.PALETTE["necro_dark"], min(80, alpha)),
                      (x, y - 10), r)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_vhalzun.draw_vhalzun(surface, boss, x, y)


# ====================================================================
# KROBELLUS
# ====================================================================
class _NS_krobellus:
    """Namespace krobellus - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Death Prophet inspired teal/purple/spectral
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Dress - dark purple
        "dress_darkest":  (18,  10,  30),
        "dress_dark":     (38,  20,  58),
        "dress_mid":      (68,  38,  95),
        "dress_light":    (105, 65, 140),
        "dress_high":     (145, 100, 185),
        "dress_shine":    (195, 160, 225),

        # Corset/inner
        "corset_darkest": (12,   6,   22),
        "corset_dark":    (28,  15,  42),
        "corset_mid":     (52,  30,  72),
        "corset_light":   (85,  55, 110),

        # Skin - pale ghostly
        "skin_dark":      (135, 145, 148),
        "skin_mid":       (180, 195, 195),
        "skin_light":     (215, 228, 225),
        "skin_shine":     (240, 250, 248),

        # Ghost / spirit teal
        "ghost_darkest":  (10,  40,  38),
        "ghost_dark":     (30,  90,  85),
        "ghost_mid":      (55, 160, 145),
        "ghost_light":    (110, 220, 195),
        "ghost_bright":   (170, 250, 225),
        "ghost_hot":      (215, 255, 245),
        "ghost_white":    (240, 255, 250),

        # Hair - teal
        "hair_darkest":   (15,  50,  45),
        "hair_dark":      (35,  95,  85),
        "hair_mid":       (60, 155, 140),
        "hair_light":     (110, 210, 190),
        "hair_shine":     (170, 245, 225),

        # Purple magic (silence)
        "magic_darkest":  (30,  10,  55),
        "magic_dark":     (75,  25, 130),
        "magic_mid":      (130, 55, 200),
        "magic_light":    (185, 110, 240),
        "magic_bright":   (220, 170, 255),
        "magic_hot":      (240, 210, 255),

        # Gold trim
        "gold_dark":      (95,  62,  15),
        "gold_mid":       (170, 125, 35),
        "gold_light":     (230, 190, 75),
        "gold_shine":     (255, 235, 150),

        # Red eyes / gem
        "red_dark":       (100, 15,  25),
        "red_mid":        (180, 40,  50),
        "red_bright":     (230, 80,  80),
        "red_hot":        (255, 150, 140),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (5,   3,   10),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_krobellus._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_krobellus.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_krobellus._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
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
        color = _NS_krobellus._clamp(color)
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
        color = _NS_krobellus._clamp(color)
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
        color = _NS_krobellus._clamp(color)
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
        return int(x + 200 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Spirit / ghost drawing helpers
    # ---------------------------------------------------------------------------


    def _draw_ghost_head(surface, cx, cy, phase, size=8, facing=1, alpha=220):
        """Draw a small floating ghost head (skull-like spirit)."""
        # Body/head shape (elongated tear-drop / ghost shape)
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_darkest"], alpha // 3),
                  (cx, cy), size + 4)
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_dark"], alpha // 2),
                  (cx, cy), size + 2)

        # Main body
        head_pts = [
            (cx - size, cy - 2),
            (cx - size + 1, cy - size + 2),
            (cx, cy - size),
            (cx + size - 1, cy - size + 2),
            (cx + size, cy - 2),
            (cx + size - 2, cy + size - 3),
            (cx + 2, cy + size),
            (cx - 2, cy + size),
            (cx - size + 2, cy + size - 3),
        ]
        _NS_krobellus._poly(surface, (*_NS_krobellus.PALETTE["ghost_mid"], alpha), head_pts)

        # Inner brighter shape
        inner_pts = [
            (cx - size + 2, cy - 1),
            (cx - 1, cy - size + 2),
            (cx + 1, cy - size + 2),
            (cx + size - 2, cy - 1),
            (cx + size - 3, cy + size - 4),
            (cx, cy + size - 2),
            (cx - size + 3, cy + size - 4),
        ]
        _NS_krobellus._poly(surface, (*_NS_krobellus.PALETTE["ghost_light"], alpha), inner_pts)

        # Eye sockets (dark)
        eye_off = max(1, size // 3)
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["ghost_darkest"],
                  (cx - eye_off, cy - 1), max(1, size // 4))
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["ghost_darkest"],
                  (cx + eye_off, cy - 1), max(1, size // 4))
        # Eye glow
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["ghost_hot"],
                  (cx - eye_off, cy - 1), max(1, size // 5))
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["ghost_hot"],
                  (cx + eye_off, cy - 1), max(1, size // 5))

        # Tail wisps at bottom
        wave = math.sin(phase * 3) * 2
        for i in range(3):
            off = (i - 1) * 3
            tail_x = cx + off + int(wave)
            tail_y = cy + size + 2 + i
            _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_mid"], alpha // 2),
                      (tail_x, tail_y), 2)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM - Spirit projectile
    # ---------------------------------------------------------------------------
    class SpiritProjectile:
        """A spirit that flies at target."""
        def __init__(self, sx, sy, tx, ty, speed=5.5, spirit_size=7):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.trail = []
            self.spirit_size = spirit_size
            self.wobble = 0.0

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.wobble += 0.35
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 10:
                self.trail.pop(0)
            # Wobble perpendicular for ghostly motion
            nx = dx / dist
            ny = dy / dist
            wob = math.sin(self.wobble) * 1.5
            self.x += nx * self.speed - ny * wob
            self.y += ny * self.speed + nx * wob

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 15)
                r = max(1, self.spirit_size - (len(self.trail) - i))
                _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_dark"], alpha), (tx, ty), r + 1)
                _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_light"], alpha // 2), (tx, ty), r - 1)

            if self.alive:
                px, py = int(self.x), int(self.y)
                _NS_krobellus._draw_ghost_head(surface, px, py, phase, self.spirit_size)


    class SilenceProjectile:
        """Purple silence bolt."""
        def __init__(self, sx, sy, tx, ty, speed=8.0):
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
            d = math.sqrt(dx * dx + dy * dy) or 1
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
            if len(self.trail) > 14:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 3:
                return
            # Long trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(30 + i * 15)
                r = max(1, 5 - (len(self.trail) - i) // 2)
                _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["magic_dark"], alpha), (tx, ty), r + 2)
                _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["magic_mid"], alpha), (tx, ty), r)
                _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["magic_bright"], alpha // 2), (tx, ty), max(1, r - 1))

            if self.alive:
                px, py = int(self.x), int(self.y)
                # Elongated bolt shape
                perp = self.angle + math.pi / 2
                tip_x = px + int(math.cos(self.angle) * 12)
                tip_y = py + int(math.sin(self.angle) * 12)
                back_x = px - int(math.cos(self.angle) * 6)
                back_y = py - int(math.sin(self.angle) * 6)
                side1_x = px + int(math.cos(perp) * 5)
                side1_y = py + int(math.sin(perp) * 5)
                side2_x = px - int(math.cos(perp) * 5)
                side2_y = py - int(math.sin(perp) * 5)

                _NS_krobellus._poly(surface, (*_NS_krobellus.PALETTE["magic_dark"], 200),
                      [(tip_x, tip_y), (side1_x, side1_y),
                       (back_x, back_y), (side2_x, side2_y)])
                _NS_krobellus._poly(surface, (*_NS_krobellus.PALETTE["magic_mid"], 220),
                      [(tip_x, tip_y),
                       (px + int(math.cos(perp) * 3), py + int(math.sin(perp) * 3)),
                       (back_x, back_y),
                       (px - int(math.cos(perp) * 3), py - int(math.sin(perp) * 3))])
                _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["magic_bright"], (px, py), 4)
                _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["magic_hot"], (px, py), 2)


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_krb_last_x"):
            boss._krb_last_x = boss.x
            boss._krb_last_y = boss.y
            return False
        dx = abs(boss.x - boss._krb_last_x)
        dy = abs(boss.y - boss._krb_last_y)
        boss._krb_last_x = boss.x
        boss._krb_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_krb_prev_timer", 0))
        active = bool(getattr(boss, "_krb_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._krb_attack_active = True
            boss._krb_attack_frame = 0
            active = True
        elif active:
            boss._krb_attack_frame = int(getattr(boss, "_krb_attack_frame", 0)) + 1
            if boss._krb_attack_frame > cooldown:
                boss._krb_attack_active = False
                boss._krb_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._krb_attack_active = False
            boss._krb_attack_frame = 0
            active = False

        boss._krb_prev_timer = timer
        boss._krb_attack_progress = (
            min(1.0, getattr(boss, "_krb_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_krb_projectiles"):
            boss._krb_projectiles = []
        for proj in boss._krb_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._krb_projectiles = [p for p in boss._krb_projectiles
                                 if p.alive or p.age < 8]


    def _spawn_basic_projectile(boss, x, y):
        if not hasattr(boss, "_krb_projectiles"):
            boss._krb_projectiles = []
        tx, ty = _NS_krobellus._target_position(boss, x, y)
        sx = x + 22 * getattr(boss, "direction", 1)
        sy = y - 10
        boss._krb_projectiles.append(_NS_krobellus.SpiritProjectile(sx, sy, tx, ty, speed=5.5))


    def _spawn_silence_projectile(boss, x, y):
        if not hasattr(boss, "_krb_projectiles"):
            boss._krb_projectiles = []
        tx, ty = _NS_krobellus._target_position(boss, x, y)
        sx = x + 22 * getattr(boss, "direction", 1)
        sy = y - 15
        boss._krb_projectiles.append(_NS_krobellus.SilenceProjectile(sx, sy, tx, ty, speed=8.0))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_krobellus(surface, boss, x, y):
        """Entry point."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_krobellus._detect_moving(boss)
        _NS_krobellus._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_krb_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # ---------- Background layers ----------
        _NS_krobellus._draw_spectral_aura(surface, x, y, pulse)
        _NS_krobellus._draw_ground_runes(surface, x, y + 38, pulse, active_skill)

        # ---------- Skill ground effects ----------
        if active_skill == "q":
            _NS_krobellus._draw_exorcism_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_krobellus._draw_spirit_siphon_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_krobellus._draw_crypt_swarm_ground(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if attacking:
            _NS_krobellus._draw_krobellus_attack(surface, boss, x, y)
        elif moving:
            _NS_krobellus._draw_krobellus_walk(surface, boss, x, y)
        else:
            _NS_krobellus._draw_krobellus_idle(surface, boss, x, y)

        # ---------- Projectiles ----------
        _NS_krobellus._manage_projectiles(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "q":
            _NS_krobellus._draw_exorcism(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_krobellus._draw_silence_cast(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_krobellus._draw_spirit_siphon(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_krobellus._draw_crypt_swarm(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_krobellus_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_krobellus._draw_shadow(surface, x, y + 48)
        _NS_krobellus._draw_floating_wisps(surface, x, y + 35, boss.pulse)
        _NS_krobellus._draw_krobellus_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")
        # Companion ghost heads (like reference image)
        _NS_krobellus._draw_companion_ghosts(surface, x, y + bob, boss.pulse)


    def _draw_krobellus_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(abs(math.sin(phase * 1.3)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_krobellus._draw_shadow(surface, x + sway, y + 48)
        _NS_krobellus._draw_floating_wisps(surface, x + sway, y + 35, phase, trail=True,
                             facing=boss.direction)
        _NS_krobellus._draw_krobellus_body(surface, x + sway, y - bob, boss.direction, phase, "walk")
        _NS_krobellus._draw_companion_ghosts(surface, x + sway, y - bob, phase, trailing=True,
                               facing=boss.direction)


    def _draw_krobellus_attack(surface, boss, x, y):
        progress = getattr(boss, "_krb_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        if 0.28 < progress < 0.35 and not getattr(boss, "_krb_proj_spawned", False):
            _NS_krobellus._spawn_basic_projectile(boss, x, y)
            boss._krb_proj_spawned = True
        if progress < 0.1 or progress > 0.9:
            boss._krb_proj_spawned = False

        recoil = int(math.sin(progress * math.pi) * 3) * -boss.direction
        _NS_krobellus._draw_shadow(surface, x + recoil, y + 48)
        _NS_krobellus._draw_floating_wisps(surface, x + recoil, y + 35, boss.pulse, intense=True)
        _NS_krobellus._draw_krobellus_body(surface, x + recoil, y, boss.direction, boss.pulse,
                            "attack", progress)
        _NS_krobellus._draw_companion_ghosts(surface, x + recoil, y, boss.pulse, intense=True)
        _NS_krobellus._draw_cast_flash(surface, x + recoil, y, boss.direction, progress)


    # ===================================================================
    # BODY RENDERING – HD detailed Death Prophet
    # ===================================================================
    def _draw_krobellus_body(surface, cx, cy, facing, phase, action,
                            attack_progress=0):
        """Main body composition."""
        # Long flowing dress (background)
        _NS_krobellus._draw_flowing_dress(surface, cx, cy + 5, phase)

        # Torso/corset
        _NS_krobellus._draw_corset(surface, cx, cy - 8, phase)

        # Shoulders / pauldrons (dark spiky)
        _NS_krobellus._draw_shoulders(surface, cx, cy - 16, phase)

        # Arms
        if action == "attack":
            _NS_krobellus._draw_casting_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        else:
            _NS_krobellus._draw_idle_arms(surface, cx, cy - 8, facing, phase)

        # Head + hair
        _NS_krobellus._draw_head(surface, cx, cy - 30, facing, phase)
        _NS_krobellus._draw_flowing_hair(surface, cx, cy - 30, facing, phase)

        # Body wisps / floating soul particles
        _NS_krobellus._draw_body_soul_particles(surface, cx, cy, phase)


    def _draw_flowing_dress(surface, cx, cy, phase):
        """Long tattered purple dress that floats."""
        sway = int(math.sin(phase * 0.7) * 3)
        sway2 = int(math.sin(phase * 0.5 + 1) * 2)

        # Outermost tattered dress silhouette
        dress_outer = [
            (cx - 20, cy),
            (cx + 20, cy),
            (cx + 26 + sway, cy + 15),
            (cx + 24 + sway2, cy + 30),
            (cx + 20, cy + 42),
            (cx + 12, cy + 50 + sway2),
            (cx + 3, cy + 54),
            (cx - 3, cy + 54),
            (cx - 12, cy + 50 - sway2),
            (cx - 20, cy + 42),
            (cx - 24 - sway2, cy + 30),
            (cx - 26 - sway, cy + 15),
        ]
        _NS_krobellus._poly(surface, _NS_krobellus.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in dress_outer])
        _NS_krobellus._poly(surface, _NS_krobellus.PALETTE["dress_darkest"], dress_outer)

        # Mid dress
        dress_mid = [
            (cx - 17, cy + 2),
            (cx + 17, cy + 2),
            (cx + 22 + sway, cy + 15),
            (cx + 20 + sway2, cy + 28),
            (cx + 16, cy + 40),
            (cx + 8, cy + 46),
            (cx - 8, cy + 46),
            (cx - 16, cy + 40),
            (cx - 20 - sway2, cy + 28),
            (cx - 22 - sway, cy + 15),
        ]
        _NS_krobellus._poly(surface, _NS_krobellus.PALETTE["dress_dark"], dress_mid)

        # Inner dress with lighter shade
        dress_inner = [
            (cx - 13, cy + 4),
            (cx + 13, cy + 4),
            (cx + 17 + sway, cy + 15),
            (cx + 14, cy + 26),
            (cx + 10, cy + 36),
            (cx - 10, cy + 36),
            (cx - 14, cy + 26),
            (cx - 17 - sway, cy + 15),
        ]
        _NS_krobellus._poly(surface, _NS_krobellus.PALETTE["dress_mid"], dress_inner)

        # Vertical light streaks (dress folds)
        for xoff in (-8, -3, 3, 8):
            _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["dress_light"],
                    (cx + xoff, cy + 6), (cx + xoff, cy + 30), 1)

        # Tattered edges at bottom
        for i in range(9):
            tx = cx - 20 + i * 5
            ty = cy + 44 + int(math.sin(phase * 1.5 + i) * 4)
            _NS_krobellus._poly(surface, _NS_krobellus.PALETTE["dress_darkest"], [
                (tx - 3, cy + 40), (tx + 3, cy + 40),
                (tx + 1, ty + 6), (tx - 1, ty + 6),
            ])

        # Purple glow beneath (spectral)
        for i in range(5):
            alpha = 60 - i * 10
            _NS_krobellus._ellipse(surface, (*_NS_krobellus.PALETTE["magic_mid"], alpha),
                     (cx - 25 + i * 2, cy + 48 - i, 50 - i * 4, 8))

        # Gold belt / trim at waist
        _NS_krobellus._rect(surface, _NS_krobellus.PALETTE["gold_dark"], (cx - 15, cy - 1, 30, 4))
        _NS_krobellus._rect(surface, _NS_krobellus.PALETTE["gold_mid"], (cx - 13, cy, 26, 2))
        _NS_krobellus._rect(surface, _NS_krobellus.PALETTE["gold_light"], (cx - 10, cy + 1, 20, 1))

        # Belt gem (red)
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["gold_dark"], (cx, cy + 1), 4)
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["red_dark"], (cx, cy + 1), 3)
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["red_bright"], (cx - 1, cy), 2)
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["red_hot"], (cx - 1, cy), 1)


    def _draw_corset(surface, cx, cy, phase):
        """Dark corset/bodice."""
        # Shadow
        _NS_krobellus._poly(surface, _NS_krobellus.PALETTE["shadow_deep"], [
            (cx - 12 + 2, cy - 10 + 2), (cx + 12 + 2, cy - 10 + 2),
            (cx + 14 + 2, cy + 12 + 2), (cx + 4 + 2, cy + 17 + 2),
            (cx - 4 + 2, cy + 17 + 2), (cx - 14 + 2, cy + 12 + 2),
        ])

        corset = [
            (cx - 12, cy - 10), (cx + 12, cy - 10),
            (cx + 14, cy + 12), (cx + 4, cy + 17),
            (cx - 4, cy + 17), (cx - 14, cy + 12),
        ]
        _NS_krobellus._poly(surface, _NS_krobellus.PALETTE["corset_darkest"], corset)
        _NS_krobellus._poly(surface, _NS_krobellus.PALETTE["corset_dark"], [
            (cx - 10, cy - 8), (cx + 10, cy - 8),
            (cx + 12, cy + 10), (cx + 4, cy + 14),
            (cx - 4, cy + 14), (cx - 12, cy + 10),
        ])
        _NS_krobellus._poly(surface, _NS_krobellus.PALETTE["corset_mid"], [
            (cx - 7, cy - 5), (cx + 7, cy - 5),
            (cx + 9, cy + 8), (cx + 3, cy + 11),
            (cx - 3, cy + 11), (cx - 9, cy + 8),
        ])

        # Center chest gold decoration (V shape)
        _NS_krobellus._poly(surface, _NS_krobellus.PALETTE["gold_dark"], [
            (cx - 6, cy - 6), (cx + 6, cy - 6),
            (cx, cy + 10),
        ])
        _NS_krobellus._poly(surface, _NS_krobellus.PALETTE["gold_mid"], [
            (cx - 4, cy - 4), (cx + 4, cy - 4),
            (cx, cy + 8),
        ])

        # Central red gem
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["red_dark"], (cx, cy - 2), 3)
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["red_mid"], (cx, cy - 2), 2)
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["red_bright"], (cx, cy - 2),
                  max(1, int(2 * pulse)))
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["red_hot"], (cx, cy - 2), 1)

        # Corset lacing
        for i in range(4):
            y_off = cy - 4 + i * 4
            _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["gold_light"],
                    (cx - 3, y_off), (cx + 3, y_off + 2), 1)
            _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["gold_light"],
                    (cx - 3, y_off + 2), (cx + 3, y_off), 1)

        # Corset outline (dark)
        for i in range(len(corset)):
            p1 = corset[i]
            p2 = corset[(i + 1) % len(corset)]
            _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["shadow_deep"], p1, p2, 1)


    def _draw_shoulders(surface, cx, cy, phase):
        """Dark spiky shoulder pieces."""
        for side in (-1, 1):
            sx = cx + side * 14
            # Shadow
            _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["shadow_deep"], (sx + 2, cy + 2), 8)
            # Shoulder pad
            _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["dress_darkest"], (sx, cy), 7)
            _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["dress_dark"], (sx - side, cy - 1), 5)
            _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["dress_mid"], (sx - side, cy - 2), 3)

            # Spike protruding
            _NS_krobellus._poly(surface, _NS_krobellus.PALETTE["dress_darkest"], [
                (sx - 2, cy - 4),
                (sx + 2, cy - 4),
                (sx + side * 3, cy - 12),
            ])
            _NS_krobellus._poly(surface, _NS_krobellus.PALETTE["dress_dark"], [
                (sx - 1, cy - 4),
                (sx + 1, cy - 4),
                (sx + side * 2, cy - 10),
            ])

            # Small gold ornament
            _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["gold_mid"], (sx, cy - 1), 2)
            _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["gold_light"], (sx - 1, cy - 2), 1)


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Arms with pale skin, glowing hands."""
        sway = math.sin(phase * 0.7) * 2
        for side in (-1, 1):
            shoulder_x = cx + side * 12
            shoulder_y = cy + 2
            elbow_x = shoulder_x + side * 6
            elbow_y = cy + 12 + int(sway)
            hand_x = elbow_x + side * 4
            hand_y = elbow_y + 10

            _NS_krobellus._draw_arm_segment(surface, shoulder_x, shoulder_y,
                              elbow_x, elbow_y, sleeve=True)
            _NS_krobellus._draw_arm_segment(surface, elbow_x, elbow_y,
                              hand_x, hand_y, sleeve=False)
            _NS_krobellus._draw_hand_wisp(surface, hand_x, hand_y, phase + side, 4)


    def _draw_casting_arms(surface, cx, cy, facing, phase, progress):
        """Casting pose."""
        # Back arm
        back_side = -facing
        bs_x = cx + back_side * 12
        bs_y = cy + 2
        be_x = bs_x + back_side * 6
        be_y = cy + 10
        bh_x = be_x + back_side * 4
        bh_y = be_y + 8
        _NS_krobellus._draw_arm_segment(surface, bs_x, bs_y, be_x, be_y, sleeve=True)
        _NS_krobellus._draw_arm_segment(surface, be_x, be_y, bh_x, bh_y, sleeve=False)
        _NS_krobellus._draw_hand_wisp(surface, bh_x, bh_y, phase, 3)

        # Front arm - casting forward
        fs_x = cx + facing * 12
        fs_y = cy + 2

        if progress < 0.3:
            t = progress / 0.3
            arm_angle = -0.6 * t
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            arm_angle = -0.6 + 1.4 * t
        else:
            t = (progress - 0.5) / 0.5
            arm_angle = 0.8 - 0.5 * t

        fe_x = fs_x + int(math.cos(arm_angle) * 12) * facing
        fe_y = fs_y + int(math.sin(arm_angle) * 12) - 2
        fh_x = fe_x + int(math.cos(arm_angle) * 10) * facing
        fh_y = fe_y + int(math.sin(arm_angle) * 10)

        _NS_krobellus._draw_arm_segment(surface, fs_x, fs_y, fe_x, fe_y, sleeve=True)
        _NS_krobellus._draw_arm_segment(surface, fe_x, fe_y, fh_x, fh_y, sleeve=False)

        # Big glow on casting hand
        glow_size = 5 + int(math.sin(progress * math.pi) * 5)
        _NS_krobellus._draw_hand_wisp(surface, fh_x, fh_y, phase, glow_size)

        # Spirit energy from hand during cast
        if 0.2 < progress < 0.6:
            intensity = math.sin((progress - 0.2) / 0.4 * math.pi)
            for i in range(4):
                angle = phase * 4 + i * math.pi / 2
                ex = fh_x + int(math.cos(angle) * 12 * intensity) * facing
                ey = fh_y + int(math.sin(angle) * 10 * intensity)
                _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_bright"], 200), (ex, ey), 2)
                _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_hot"], 240), (ex, ey), 1)


    def _draw_arm_segment(surface, x1, y1, x2, y2, sleeve=True):
        """Arm segment with dress sleeve or bare skin."""
        if sleeve:
            # Purple sleeve
            _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["shadow_deep"],
                    (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 7)
            _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["dress_darkest"], (x1, y1), (x2, y2), 6)
            _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["dress_dark"], (x1, y1), (x2, y2), 4)
            _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["dress_mid"], (x1, y1), (x2, y2), 2)
        else:
            # Bare arm (pale skin)
            _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["shadow_deep"],
                    (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 5)
            _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["skin_dark"], (x1, y1), (x2, y2), 4)
            _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["skin_mid"], (x1, y1), (x2, y2), 3)
            _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["skin_light"], (x1 - 1, y1), (x2 - 1, y2), 1)


    def _draw_hand_wisp(surface, x, y, phase, size=4):
        """Glowing ghostly hand."""
        pulse = math.sin(phase * 2.0) * 0.3 + 0.7
        s = int(size * pulse)
        # Hand base
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["skin_dark"], (x, y), 3)
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["skin_mid"], (x, y - 1), 2)
        # Ghost energy
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_dark"], 100), (x, y), s + 5)
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_mid"], 160), (x, y), s + 2)
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_light"], 200), (x, y), s)
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_bright"], 220), (x, y), max(1, s - 2))

        # Tiny wisps
        for i in range(3):
            angle = phase * 2 + i * math.pi * 2 / 3
            sx = x + int(math.cos(angle) * (s + 4))
            sy = y + int(math.sin(angle) * (s + 4))
            _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["ghost_hot"], (sx, sy), 1)


    def _draw_head(surface, cx, cy, facing, phase):
        """Death Prophet head - pale skin, glowing eyes."""
        # Neck
        _NS_krobellus._rect(surface, _NS_krobellus.PALETTE["skin_dark"], (cx - 3, cy + 8, 6, 5))
        _NS_krobellus._rect(surface, _NS_krobellus.PALETTE["skin_mid"], (cx - 2, cy + 8, 4, 4))

        # Head shape (oval)
        # Shadow
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["shadow_deep"], (cx + 2, cy + 2), 10)
        # Skin base
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["skin_dark"], (cx, cy), 9)
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["skin_mid"], (cx - 1, cy - 1), 8)
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["skin_light"], (cx - 2, cy - 3), 5)

        # Cheek shading
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["dress_dark"], 60), (cx + 4, cy + 3), 3)
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["dress_dark"], 60), (cx - 4, cy + 3), 3)

        # Eyes - glowing red
        eye_pulse = math.sin(phase * 2) * 0.2 + 0.8
        # Eye socket
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["shadow_deep"], (cx - 3, cy - 1), 2)
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["shadow_deep"], (cx + 3, cy - 1), 2)
        # Eye glow
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["red_dark"], (cx - 3, cy - 1),
                  max(1, int(2 * eye_pulse)))
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["red_bright"], (cx - 3, cy - 1), 1)
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["red_dark"], (cx + 3, cy - 1),
                  max(1, int(2 * eye_pulse)))
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["red_bright"], (cx + 3, cy - 1), 1)

        # Nose
        _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["skin_dark"], (cx, cy), (cx, cy + 3), 1)

        # Mouth - slight open, dark
        _NS_krobellus._rect(surface, _NS_krobellus.PALETTE["shadow_deep"], (cx - 2, cy + 4, 4, 2))
        _NS_krobellus._rect(surface, _NS_krobellus.PALETTE["red_dark"], (cx - 1, cy + 4, 2, 1))

        # Small forehead gem
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["gold_dark"], (cx, cy - 6), 2)
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["red_bright"], (cx, cy - 6), 1)


    def _draw_flowing_hair(surface, cx, cy, facing, phase):
        """Long flowing teal hair."""
        wave1 = math.sin(phase * 0.8) * 4
        wave2 = math.sin(phase * 1.1 + 0.5) * 3
        wave3 = math.sin(phase * 1.3 + 1) * 3

        # Back hair (behind head, flowing up and back)
        for side in (-1, 1):
            # Hair streams flowing upward and outward
            for i in range(4):
                base_x = cx + side * (3 + i * 2)
                base_y = cy - 8
                # Stream goes up and back
                stream_pts = [
                    (base_x, base_y),
                    (base_x + side * (4 + i) + int(wave1 * 0.5), base_y - 8),
                    (base_x + side * (8 + i * 2) + int(wave2), base_y - 16),
                    (base_x + side * (10 + i * 2) + int(wave3), base_y - 22),
                ]
                for j in range(len(stream_pts) - 1):
                    p1 = stream_pts[j]
                    p2 = stream_pts[j + 1]
                    _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["hair_darkest"], p1, p2, 4)
                    _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["hair_dark"], p1, p2, 3)
                    _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["hair_mid"], p1, p2, 2)
                    _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["hair_light"], p1, p2, 1)

        # Top of head hair
        for i in range(-3, 4):
            base_x = cx + i * 2
            base_y = cy - 8
            top_x = base_x + int(math.sin(phase + i * 0.5) * 2)
            top_y = base_y - 6 - abs(i)
            _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["hair_darkest"], (base_x, base_y), (top_x, top_y), 3)
            _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["hair_mid"], (base_x, base_y), (top_x, top_y), 2)
            _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["hair_light"], (base_x, base_y - 1),
                    (top_x, top_y), 1)

        # Side hair falling down past shoulders
        for side in (-1, 1):
            hair_side_pts = [
                (cx + side * 7, cy - 4),
                (cx + side * 9, cy + 3),
                (cx + side * 10 + int(wave1 * 0.5), cy + 12),
                (cx + side * 8 + int(wave2 * 0.5), cy + 20),
            ]
            for j in range(len(hair_side_pts) - 1):
                p1 = hair_side_pts[j]
                p2 = hair_side_pts[j + 1]
                _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["hair_darkest"], p1, p2, 5)
                _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["hair_dark"], p1, p2, 4)
                _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["hair_mid"], p1, p2, 2)
                _NS_krobellus._aaline(surface, _NS_krobellus.PALETTE["hair_light"], p1, p2, 1)

        # Hair wisps (small teal particles rising from hair)
        for i in range(5):
            angle = phase * 0.8 + i * math.pi / 3
            r = 12 + int(math.sin(phase + i) * 3)
            px = cx + int(math.cos(angle) * r)
            py = cy - 14 + int(math.sin(angle) * 3)
            alpha = 180
            _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["hair_mid"], alpha), (px, py), 2)
            _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["hair_shine"], alpha), (px, py), 1)


    def _draw_body_soul_particles(surface, cx, cy, phase):
        """Floating soul particles around body."""
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            radius = 30 + int(math.sin(phase * 0.7 + i) * 8)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(140 + math.sin(phase + i * 0.7) * 60)
            _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_dark"], alpha), (px, py), 2)
            _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_bright"], alpha // 2), (px, py), 1)


    # ===================================================================
    # COMPANION GHOSTS (from reference image)
    # ===================================================================
    def _draw_companion_ghosts(surface, cx, cy, phase, trailing=False,
                              facing=1, intense=False):
        """Small ghosts floating around Krobellus."""
        count = 3 if not intense else 4
        for i in range(count):
            angle = phase * 0.5 + i * math.pi * 2 / count
            r_x = 45 + int(math.sin(phase * 0.9 + i) * 8)
            r_y = 20 + int(math.sin(phase * 0.7 + i * 1.4) * 6)
            px = cx + int(math.cos(angle) * r_x)
            py = cy - 25 + int(math.sin(angle) * r_y)

            # Size varies
            size = 6 + int(math.sin(phase + i) * 1)
            alpha = 200 if not intense else 240
            _NS_krobellus._draw_ghost_head(surface, px, py, phase + i, size, facing, alpha)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_wisps(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False):
        """Spectral mist beneath floating Krobellus."""
        strength = 1.5 if intense else 1.0

        # Base mist
        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(32, 3, -4):
            alpha = int((32 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_krobellus.PALETTE["ghost_darkest"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising ghost wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 24)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_dark"], alpha), (sx, sy), 5)
            _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_mid"], alpha), (sx, sy - 2), 3)
            _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_bright"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Small orbiting soul balls
        for i in range(5):
            angle = phase * 0.9 + i * math.pi * 2 / 5
            r = 22 + int(math.sin(phase + i * 1.3) * 4)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 6)
            _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["ghost_mid"], (sx, sy), 3)
            _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["ghost_light"], (sx, sy), 2)
            _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["ghost_hot"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 130 - i * 22)
                _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y):
        """Ground shadow."""
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_krobellus.PALETTE["ghost_darkest"], 60), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_spectral_aura(surface, x, y, phase):
        """Green/purple background aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(72, 5, -4):
            alpha = int((72 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_krobellus._aacircle(aura, (*_NS_krobellus.PALETTE["dress_darkest"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))

        # Additional teal glow
        aura2 = pygame.Surface((120, 100), pygame.SRCALPHA)
        for radius in range(48, 5, -3):
            alpha = int((48 - radius) * 0.8 * pulse)
            if alpha > 0:
                _NS_krobellus._aacircle(aura2, (*_NS_krobellus.PALETTE["ghost_darkest"], min(255, alpha)),
                          (60, 50), radius)
        surface.blit(aura2, (x - 60, y - 40))


    def _draw_ground_runes(surface, x, y, phase, skill):
        """Necromantic circle on ground."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_krobellus.PALETTE["ghost_dark"], 140),
                            (5, 10, 120, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_krobellus.PALETTE["ghost_mid"], 170),
                            (20, 14, 90, 16), 2)

        # Rune marks
        for i in range(10):
            angle = phase * 0.2 + i * math.pi / 5
            x1 = 65 + int(math.cos(angle) * 30)
            y1 = 22 + int(math.sin(angle) * 6)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_krobellus.PALETTE["ghost_bright"], 160),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_krobellus.PALETTE["ghost_hot"], int(80 * pulse)),
                                (15, 8, 100, 28), 1)

        surface.blit(ring, (x - 65, y - 22))


    def _draw_cast_flash(surface, x, y, facing, progress):
        """Flash effect during ranged attack."""
        if progress < 0.2 or progress > 0.65:
            return
        t = (progress - 0.2) / 0.45
        intensity = math.sin(t * math.pi)

        flash_x = x + 22 * facing
        flash_y = y - 10

        alpha = int(180 * intensity)
        radius = int(8 + intensity * 15)

        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_dark"], alpha // 2),
                  (flash_x, flash_y), radius + 8)
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_mid"], alpha),
                  (flash_x, flash_y), radius)
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_bright"], alpha),
                  (flash_x, flash_y), radius // 2)
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_hot"], min(255, alpha)),
                  (flash_x, flash_y), max(1, radius // 4))


    # ===================================================================
    # SKILL Q: EXORCISM - Summon swarm of spirits
    # ===================================================================
    def _draw_exorcism_ground(surface, boss, x, y, timer, phase):
        """Ground effect for exorcism."""
        progress = max(0.0, min(1.0, 1 - timer / 100))
        pulse = math.sin(phase * 2) * 0.2 + 0.8
        radius = int(50 + progress * 30)

        _NS_krobellus._ellipse(surface, (*_NS_krobellus.PALETTE["ghost_dark"], int(150 * pulse)),
                 (x - radius, y + 30 - radius // 4, radius * 2, radius // 2), 3)
        _NS_krobellus._ellipse(surface, (*_NS_krobellus.PALETTE["ghost_mid"], int(120 * pulse)),
                 (x - radius + 5, y + 32 - radius // 4,
                  radius * 2 - 10, radius // 2 - 4), 2)


    def _draw_exorcism(surface, boss, x, y, timer, phase):
        """Swarm of small ghost heads flying around."""
        progress = max(0.0, min(1.0, 1 - timer / 100))

        # Spawn ghosts orbiting Krobellus, then flying out at target
        ghost_count = int(6 + progress * 6)

        for i in range(ghost_count):
            angle = phase * 1.5 + i * math.pi * 2 / ghost_count

            if progress < 0.5:
                # Orbit around Krobellus
                r_x = 40 + int(math.sin(phase + i) * 8)
                r_y = 20 + int(math.sin(phase * 0.7 + i) * 5)
                gx = x + int(math.cos(angle) * r_x)
                gy = y - 10 + int(math.sin(angle) * r_y)
            else:
                # Fly outward
                fly_t = (progress - 0.5) / 0.5
                r_x = 40 + int(fly_t * 100)
                r_y = 20 + int(fly_t * 40)
                gx = x + int(math.cos(angle) * r_x)
                gy = y - 10 + int(math.sin(angle) * r_y)

            size = 6 + int(math.sin(phase * 2 + i) * 1)
            alpha = 220
            _NS_krobellus._draw_ghost_head(surface, gx, gy, phase + i, size,
                             boss.direction, alpha)

            # Trailing wisp
            for j in range(3):
                tx = gx - int(math.cos(angle) * (j + 1) * 3)
                ty = gy - int(math.sin(angle) * (j + 1) * 3)
                a = max(0, alpha - (j + 1) * 60)
                _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_mid"], a), (tx, ty), 2)


    # ===================================================================
    # SKILL W: SILENCE - Purple bolt
    # ===================================================================
    def _draw_silence_cast(surface, boss, x, y, timer, phase):
        """Cast silence projectile."""
        # Spawn projectile once
        if not getattr(boss, "_krb_silence_spawned", False):
            _NS_krobellus._spawn_silence_projectile(boss, x, y)
            boss._krb_silence_spawned = True

        # Reset when skill ends
        if timer <= 5:
            boss._krb_silence_spawned = False

        # Casting flash at hand
        hand_x = x + 20 * boss.direction
        hand_y = y - 8
        pulse = math.sin(phase * 4) * 0.3 + 0.7
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["magic_dark"], 150),
                  (hand_x, hand_y), int(10 * pulse))
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["magic_mid"], 200),
                  (hand_x, hand_y), int(7 * pulse))
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["magic_bright"], 230),
                  (hand_x, hand_y), int(4 * pulse))
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["magic_hot"],
                  (hand_x, hand_y), max(1, int(2 * pulse)))


    # ===================================================================
    # SKILL E: SPIRIT SIPHON - Green beam
    # ===================================================================
    def _draw_spirit_siphon_ground(surface, boss, x, y, timer, phase):
        """Ground energy trail."""
        tx, ty = _NS_krobellus._target_position(boss, x, y)
        # Trail marks between boss and target
        for i in range(5):
            t = i / 5
            px = int(x + (tx - x) * t)
            py = int(y + 40 + (ty - y) * t * 0.3)
            alpha = int(80 * math.sin(phase * 2 + i))
            _NS_krobellus._ellipse(surface, (*_NS_krobellus.PALETTE["ghost_mid"], max(0, alpha)),
                     (px - 10, py - 2, 20, 4))


    def _draw_spirit_siphon(surface, boss, x, y, timer, phase):
        """Green streaming beam pulling from target."""
        tx, ty = _NS_krobellus._target_position(boss, x, y)
        hand_x = x + 22 * boss.direction
        hand_y = y - 8

        # Small particles flowing FROM target TO Krobellus (siphon)
        dx = hand_x - tx
        dy = hand_y - ty
        dist = math.sqrt(dx * dx + dy * dy) or 1

        # Main energy stream (thin curved line with particles)
        segments = int(dist / 8)
        for i in range(segments):
            t = i / max(1, segments)
            # Curved path
            wave = math.sin(t * math.pi * 3 + phase * 3) * 6
            perp_x = -dy / dist
            perp_y = dx / dist

            # Multiple particles flowing along path (toward boss)
            for particle_off in range(3):
                flow_t = ((phase * 0.5 + particle_off * 0.33 + t) % 1.0)
                px = int(tx + (hand_x - tx) * flow_t + perp_x * wave)
                py = int(ty + (hand_y - ty) * flow_t + perp_y * wave)

                # Particle
                _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_dark"], 200), (px, py), 4)
                _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_mid"], 220), (px, py), 3)
                _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_light"], 230), (px, py), 2)
                _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["ghost_hot"], (px, py), 1)

        # Impact at target - green drain effect
        drain_pulse = math.sin(phase * 5) * 0.3 + 0.7
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_dark"], 150),
                  (tx, ty), int(14 * drain_pulse))
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_mid"], 200),
                  (tx, ty), int(10 * drain_pulse))
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_bright"], 230),
                  (tx, ty), int(6 * drain_pulse))

        # Rising soul particles at target
        for i in range(4):
            t = (phase + i * 0.3) % 1.0
            px = tx + int(math.sin(phase * 2 + i) * 6)
            py = ty - int(t * 25)
            alpha = int(200 * (1 - t))
            if alpha > 0:
                _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_light"], alpha), (px, py), 2)
                _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_hot"], alpha), (px, py - 1), 1)

        # Healing glow at Krobellus (receiving)
        heal_pulse = math.sin(phase * 4) * 0.3 + 0.7
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_dark"], 100),
                  (hand_x, hand_y), int(12 * heal_pulse))
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_mid"], 150),
                  (hand_x, hand_y), int(8 * heal_pulse))
        _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_bright"], 200),
                  (hand_x, hand_y), int(5 * heal_pulse))
        _NS_krobellus._aacircle(surface, _NS_krobellus.PALETTE["ghost_hot"],
                  (hand_x, hand_y), max(1, int(3 * heal_pulse)))


    # ===================================================================
    # SKILL R: CRYPT SWARM - Army of ghosts
    # ===================================================================
    def _draw_crypt_swarm_ground(surface, boss, x, y, timer, phase):
        """Ground shockwave and darkness."""
        progress = max(0.0, min(1.0, 1 - timer / 120))
        pulse = math.sin(phase * 2) * 0.2 + 0.8
        radius = int(60 + progress * 40)

        # Dark ground effect
        _NS_krobellus._ellipse(surface, (*_NS_krobellus.PALETTE["dress_darkest"], int(200 * pulse)),
                 (x - radius, y + 30 - radius // 3, radius * 2, radius * 2 // 3), 4)
        _NS_krobellus._ellipse(surface, (*_NS_krobellus.PALETTE["magic_dark"], int(150 * pulse)),
                 (x - radius + 5, y + 32 - radius // 3,
                  radius * 2 - 10, radius * 2 // 3 - 6), 3)

        # Cracks / rune lines
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = x + int(math.cos(angle) * (radius - 20))
            y1 = y + 40 + int(math.sin(angle) * (radius // 3 - 8))
            x2 = x + int(math.cos(angle) * radius)
            y2 = y + 40 + int(math.sin(angle) * (radius // 3))
            _NS_krobellus._aaline(surface, (*_NS_krobellus.PALETTE["ghost_bright"], int(150 * pulse)),
                    (x1, y1), (x2, y2), 2)


    def _draw_crypt_swarm(surface, boss, x, y, timer, pulse):
        """Army of ghosts rising up around Krobellus."""
        progress = max(0.0, min(1.0, 1 - timer / 120))

        # Multiple layers of ghosts at different distances and positions
        ghost_positions = [
            # (angle_offset, radius_x, radius_y, size, delay)
            (0.0, 55, 15, 8, 0.0),
            (0.3, 70, 20, 7, 0.1),
            (0.6, 45, 12, 6, 0.05),
            (0.9, 80, 25, 9, 0.15),
            (1.2, 60, 18, 7, 0.08),
            (1.5, 75, 22, 8, 0.12),
            (1.8, 50, 14, 6, 0.03),
            (2.1, 65, 19, 7, 0.1),
            (2.4, 78, 24, 8, 0.14),
            (2.7, 48, 13, 6, 0.06),
            (3.0, 72, 21, 7, 0.11),
            (3.3, 58, 16, 7, 0.07),
        ]

        for angle_off, rx, ry, size, delay in ghost_positions:
            # Ghost appears based on delay
            if progress < delay:
                continue

            ghost_progress = min(1.0, (progress - delay) / max(0.1, 1 - delay))

            # Position
            angle = angle_off + pulse * 0.3
            base_x = x + int(math.cos(angle) * rx)

            # Ghosts rise from ground
            rise = ghost_progress * 40
            base_y = y + 40 - int(rise) + int(math.sin(pulse + angle_off) * 3)

            # Fade in
            alpha = int(230 * min(1.0, ghost_progress * 2))

            # Bobbing motion
            bob = int(math.sin(pulse * 2 + angle_off) * 3)

            _NS_krobellus._draw_ghost_head(surface, base_x, base_y + bob, pulse + angle_off,
                             size, boss.direction, alpha)

            # Trail of wisps below (rising from ground)
            for j in range(3):
                wisp_y = base_y + 10 + j * 5
                wisp_alpha = max(0, alpha - (j + 1) * 60)
                _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_mid"], wisp_alpha),
                          (base_x + int(math.sin(pulse + j) * 2), wisp_y),
                          max(1, 3 - j))

        # Extra particles rising
        for i in range(15):
            t = ((pulse * 0.5 + i * 0.12) % 1.0)
            angle = i * math.pi * 2 / 15
            r = 40 + int(math.sin(pulse + i) * 15)
            px = x + int(math.cos(angle) * r)
            py = y + 40 - int(t * 60) + int(math.sin(pulse + i) * 3)
            alpha = int(200 * (1 - t))
            if alpha > 0:
                _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_light"], alpha), (px, py), 2)
                _NS_krobellus._aacircle(surface, (*_NS_krobellus.PALETTE["ghost_hot"], alpha), (px, py - 1), 1)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_krobellus.draw_krobellus(surface, boss, x, y)


# ====================================================================
# ENTRY POINT PUBLIK (dipanggil base_boss.Boss.draw)
# ====================================================================

def draw_nyxara(surface, boss, x, y):
    """Entry point nyxara."""
    return _NS_nyxara.draw_nyxara(surface, boss, x, y)

def draw_gravefang(surface, boss, x, y):
    """Entry point gravefang."""
    return _NS_gravefang.draw_gravefang(surface, boss, x, y)

def draw_vhalzun(surface, boss, x, y):
    """Entry point vhalzun."""
    return _NS_vhalzun.draw_vhalzun(surface, boss, x, y)

def draw_krobellus(surface, boss, x, y):
    """Entry point krobellus."""
    return _NS_krobellus.draw_krobellus(surface, boss, x, y)
