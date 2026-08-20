"""
bosses/level3.py - Semua boss Level 3

Gabungan dari 4 file terpisah:
  - varkul               (mini boss)
  - xerathis             (mini boss)
  - nyzrak               (mini boss)
  - ancient_apparition   (TRUE BOSS)

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
# VARKUL
# ====================================================================
class _NS_varkul:
    """Namespace varkul - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Lich inspired frost blue / undead purple
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin / bone (undead pale blue)
        "skin_darkest":   (30,  45,  70),
        "skin_dark":      (60,  85, 115),
        "skin_mid":       (110, 145, 175),
        "skin_light":     (165, 200, 225),
        "skin_high":      (210, 235, 250),

        # Bone / skull
        "bone_dark":      (85, 100, 120),
        "bone_mid":       (155, 175, 195),
        "bone_light":     (215, 230, 240),
        "bone_shine":     (245, 250, 255),

        # Robe – dark purple
        "robe_darkest":   (18,  12,  35),
        "robe_dark":      (38,  25,  68),
        "robe_mid":       (68,  45, 115),
        "robe_light":     (105, 78, 160),
        "robe_high":      (145, 115, 200),

        # Armor trim / shoulders (dark blue metal)
        "armor_darkest":  (15,  25,  55),
        "armor_dark":     (30,  55,  95),
        "armor_mid":      (55,  90, 140),
        "armor_light":    (110, 150, 195),
        "armor_shine":    (180, 210, 240),

        # Gold trim
        "gold_dark":      (95,  70,  20),
        "gold_mid":       (170, 130, 40),
        "gold_light":     (230, 195, 90),
        "gold_shine":     (255, 235, 165),

        # Frost / ice energy
        "ice_darkest":    (10,  30,  75),
        "ice_dark":       (25,  70, 145),
        "ice_mid":        (70, 140, 225),
        "ice_light":      (140, 200, 250),
        "ice_bright":     (195, 230, 255),
        "ice_hot":        (225, 245, 255),
        "ice_white":      (245, 252, 255),

        # Eye glow (bright blue)
        "eye_dark":       (20,  60, 140),
        "eye_mid":        (70, 140, 240),
        "eye_light":      (150, 210, 255),
        "eye_hot":        (220, 245, 255),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   6,   15),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_varkul._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_varkul.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_varkul._clamp(color)
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
        color = _NS_varkul._clamp(color)
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
        color = _NS_varkul._clamp(color)
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
        color = _NS_varkul._clamp(color)
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
    # Ice / frost visual helpers
    # ---------------------------------------------------------------------------
    def _draw_ice_shard(surface, cx, cy, size, angle, color_dark, color_mid,
                        color_light, color_hot):
        """Draw a single sharp ice crystal shard."""
        ca, sa = math.cos(angle), math.sin(angle)
        tip_x = cx + ca * size
        tip_y = cy + sa * size
        base_l_x = cx + math.cos(angle + 2.4) * size * 0.35
        base_l_y = cy + math.sin(angle + 2.4) * size * 0.35
        base_r_x = cx + math.cos(angle - 2.4) * size * 0.35
        base_r_y = cy + math.sin(angle - 2.4) * size * 0.35

        _NS_varkul._poly(surface, color_dark, [
            (tip_x, tip_y), (base_l_x, base_l_y), (base_r_x, base_r_y)
        ])
        # Inner highlight
        mid_x = (tip_x + cx) / 2
        mid_y = (tip_y + cy) / 2
        _NS_varkul._poly(surface, color_mid, [
            (tip_x, tip_y),
            ((base_l_x + cx) / 2, (base_l_y + cy) / 2),
            ((base_r_x + cx) / 2, (base_r_y + cy) / 2),
        ])
        _NS_varkul._aaline(surface, color_light, (cx, cy), (tip_x, tip_y), 1)
        _NS_varkul._aacircle(surface, color_hot, (int(tip_x), int(tip_y)), 1)


    def _draw_snowflake(surface, cx, cy, size, phase, color=None):
        """Small rotating snowflake."""
        if color is None:
            color = _NS_varkul.PALETTE["ice_bright"]
        for i in range(6):
            angle = phase * 0.5 + i * math.pi / 3
            x1 = cx + int(math.cos(angle) * size)
            y1 = cy + int(math.sin(angle) * size)
            _NS_varkul._aaline(surface, color, (cx, cy), (x1, y1), 1)
            # Small branches
            bx = cx + int(math.cos(angle) * size * 0.6)
            by = cy + int(math.sin(angle) * size * 0.6)
            for b in (-1, 1):
                ba = angle + b * 0.5
                ex = bx + int(math.cos(ba) * size * 0.3)
                ey = by + int(math.sin(ba) * size * 0.3)
                _NS_varkul._aaline(surface, color, (bx, by), (ex, ey), 1)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_hot"], (cx, cy), 1)


    def _draw_frost_particles(surface, cx, cy, phase, radius=25, count=8):
        """Frosty motes swirling around a point."""
        for i in range(count):
            angle = phase * 0.6 + i * math.pi * 2 / count
            r = radius + int(math.sin(phase + i * 0.9) * 6)
            px = cx + int(math.cos(angle) * r)
            py = cy + int(math.sin(angle) * r * 0.6)
            alpha = int(140 + math.sin(phase * 1.4 + i) * 80)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], alpha), (px, py), 2)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_hot"], alpha), (px, py), 1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM – Frost Orb
    # ---------------------------------------------------------------------------
    class FrostProjectile:
        """Frost orb projectile that travels toward a target."""
        def __init__(self, sx, sy, tx, ty, speed=5.5):
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
            if not self.alive and self.age < 2:
                return
            # Trail - frost mist
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 12)
                r = max(1, 6 - (len(self.trail) - i))
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], alpha), (tx, ty), r + 2)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], alpha // 2), (tx, ty), r)

            if self.alive:
                px, py = int(self.x), int(self.y)
                # Outer frost aura
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 90), (px, py), 15)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], 140), (px, py), 11)
                # Core orb
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_mid"], (px, py), 7)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_light"], (px, py), 5)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (px - 1, py - 1), 3)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (px - 1, py - 1), 1)
                # Ice shards protruding
                for i in range(4):
                    angle = phase * 3 + i * math.pi / 2
                    _NS_varkul._draw_ice_shard(surface, px, py, 8, angle,
                                    _NS_varkul.PALETTE["ice_dark"], _NS_varkul.PALETTE["ice_mid"],
                                    _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])


    # ---------------------------------------------------------------------------
    # Chain Frost bouncing orb
    # ---------------------------------------------------------------------------
    class ChainFrostOrb:
        """Chain frost that bounces around."""
        def __init__(self, sx, sy, tx, ty, bounces=3):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = 4.5
            self.alive = True
            self.age = 0
            self.bounces_left = bounces
            self.trail = []

        def update(self, boss):
            if not self.alive:
                return
            self.age += 1
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < self.speed + 3:
                if self.bounces_left > 0:
                    self.bounces_left -= 1
                    # Random new target direction
                    angle = self.age * 0.7
                    self.tx = self.x + math.cos(angle) * 120
                    self.ty = self.y + math.sin(angle) * 60
                else:
                    self.alive = False
                    return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 20:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(30 + i * 10)
                r = max(1, 5 - (len(self.trail) - i) // 2)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], alpha), (tx, ty), r + 1)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_bright"], alpha // 2), (tx, ty), r)
            if self.alive:
                px, py = int(self.x), int(self.y)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 120), (px, py), 13)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], 180), (px, py), 9)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_light"], (px, py), 6)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (px, py), 4)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (px - 1, py - 1), 2)
                # Rotating shards
                for i in range(5):
                    angle = phase * 4 + i * math.pi * 2 / 5
                    _NS_varkul._draw_ice_shard(surface, px, py, 7, angle,
                                    _NS_varkul.PALETTE["ice_dark"], _NS_varkul.PALETTE["ice_mid"],
                                    _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])


    # ---------------------------------------------------------------------------
    # State management helpers
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_vk_last_x"):
            boss._vk_last_x = boss.x
            boss._vk_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vk_last_x)
        dy = abs(boss.y - boss._vk_last_y)
        boss._vk_last_x = boss.x
        boss._vk_last_y = boss.y
        return dx + dy > 0.3

    def _update_attack_anim(boss):
        """Track ranged attack animation timeline."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vk_prev_timer", -1))
        active = bool(getattr(boss, "_vk_attack_active", False))

        # Trigger conditions:
        # 1. timer melonjak ke nilai tinggi (>= cooldown-1) dari nilai rendah
        # 2. timer baru saja di-reset dari tinggi ke rendah (wrap-around)
        trigger = False
        if previous < 0:
            # First frame - jangan trigger
            pass
        elif timer >= cooldown - 1 and previous < cooldown - 1:
            trigger = True
        elif previous >= cooldown - 2 and timer <= 1:
            # timer wrapped from high to low - attack fires now
            trigger = True

        if trigger and not active:
            boss._vk_attack_active = True
            boss._vk_attack_frame = 0
            active = True

        if active:
            boss._vk_attack_frame = int(getattr(boss, "_vk_attack_frame", 0)) + 1
            if boss._vk_attack_frame > cooldown:
                boss._vk_attack_active = False
                boss._vk_attack_frame = 0
                active = False

        boss._vk_prev_timer = timer
        boss._vk_attack_progress = (
            min(1.0, getattr(boss, "_vk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_vk_projectiles"):
            boss._vk_projectiles = []
        for proj in boss._vk_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._vk_projectiles = [p for p in boss._vk_projectiles if p.alive or p.age < 8]


    def _manage_chain_orbs(boss, surface, phase):
        if not hasattr(boss, "_vk_chain_orbs"):
            boss._vk_chain_orbs = []
        for orb in boss._vk_chain_orbs:
            orb.update(boss)
            orb.draw(surface, phase)
        boss._vk_chain_orbs = [o for o in boss._vk_chain_orbs if o.alive or o.age < 8]


    def _spawn_projectile(boss, x, y):
        if not hasattr(boss, "_vk_projectiles"):
            boss._vk_projectiles = []
        tx, ty = _NS_varkul._target_position(boss, x, y)
        # Staff tip position - Lich holds staff on off-hand side
        facing = getattr(boss, "direction", 1)
        sx = x - 20 * facing  # staff hand
        sy = y - 20
        boss._vk_projectiles.append(_NS_varkul.FrostProjectile(sx, sy, tx, ty, speed=5.5))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_varkul(surface, boss, x, y):
        """Entry point for Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_varkul._detect_moving(boss)
        _NS_varkul._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_vk_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # ---------- Background layers ----------
        _NS_varkul._draw_frost_aura(surface, x, y, pulse)
        _NS_varkul._draw_ice_platform(surface, x, y + 40, pulse, active_skill)

        # ---------- Skill ground effects ----------
        if active_skill == "q":
            _NS_varkul._draw_frost_blast_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_varkul._draw_sacrifice_circle(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_varkul._draw_chain_frost_ground(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if attacking:
            _NS_varkul._draw_varkul_attack(surface, boss, x, y)
        elif moving:
            _NS_varkul._draw_varkul_walk(surface, boss, x, y)
        else:
            _NS_varkul._draw_varkul_idle(surface, boss, x, y)

        # ---------- Projectiles ----------
        _NS_varkul._manage_projectiles(boss, surface, pulse)
        _NS_varkul._manage_chain_orbs(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "q":
            _NS_varkul._draw_frost_blast(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_varkul._draw_frostbite(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_varkul._draw_sacrifice_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_varkul._draw_chain_frost(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_varkul_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        _NS_varkul._draw_shadow(surface, x, y + 48)
        _NS_varkul._draw_floating_mist(surface, x, y + 35, boss.pulse)
        _NS_varkul._draw_varkul_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_varkul_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_varkul._draw_shadow(surface, x + sway, y + 48)
        _NS_varkul._draw_floating_mist(surface, x + sway, y + 35, phase, trail=True,
                            facing=boss.direction)
        _NS_varkul._draw_varkul_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_varkul_attack(surface, boss, x, y):
        progress = getattr(boss, "_vk_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Spawn projectile at the right moment
        if 0.30 < progress < 0.40 and not getattr(boss, "_vk_proj_spawned", False):
            _NS_varkul._spawn_projectile(boss, x, y)
            boss._vk_proj_spawned = True
        if progress < 0.15 or progress > 0.9:
            boss._vk_proj_spawned = False

        recoil = int(math.sin(progress * math.pi) * 2) * -boss.direction
        _NS_varkul._draw_shadow(surface, x + recoil, y + 48)
        _NS_varkul._draw_floating_mist(surface, x + recoil, y + 35, boss.pulse, intense=True)
        _NS_varkul._draw_varkul_body(surface, x + recoil, y, boss.direction, boss.pulse,
                          "attack", progress)
        _NS_varkul._draw_cast_flash(surface, x + recoil, y, boss.direction, progress)


    # ===================================================================
    # BODY RENDERING – HD detailed Lich
    # ===================================================================
    def _draw_varkul_body(surface, cx, cy, facing, phase, action,
                          attack_progress=0):
        # Cape / robe back
        _NS_varkul._draw_robe_back(surface, cx, cy, facing, phase, action)

        # Lower robes (floating)
        _NS_varkul._draw_lower_robes(surface, cx, cy + 5, phase)

        # Torso robes with skull
        _NS_varkul._draw_torso(surface, cx, cy - 8, phase)

        # Pauldrons
        _NS_varkul._draw_pauldrons(surface, cx, cy - 18, phase)

        # Arms – staff arm and casting arm
        if action == "attack":
            _NS_varkul._draw_attack_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        else:
            _NS_varkul._draw_idle_arms(surface, cx, cy - 8, facing, phase, action)

        # Skull head with crown
        _NS_varkul._draw_skull_head(surface, cx, cy - 30, phase)

        # Floating frost particles
        _NS_varkul._draw_body_particles(surface, cx, cy, phase)


    def _draw_robe_back(surface, cx, cy, facing, phase, action):
        """Back of robe / cape."""
        wave = math.sin(phase * 0.8) * 3
        wave2 = math.sin(phase * 1.1 + 0.5) * 2

        # Outer cape
        cape_outer = [
            (cx - 15, cy - 12),
            (cx - 20, cy + 5),
            (cx - 26 - int(wave), cy + 28),
            (cx - 18 - int(wave2), cy + 42),
            (cx - 5, cy + 46),
            (cx + 5, cy + 46),
            (cx + 18 + int(wave2), cy + 42),
            (cx + 26 + int(wave), cy + 28),
            (cx + 20, cy + 5),
            (cx + 15, cy - 12),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_darkest"], cape_outer)

        cape_mid = [
            (cx - 13, cy - 10),
            (cx - 17, cy + 5),
            (cx - 22 - int(wave * 0.7), cy + 26),
            (cx - 14, cy + 38),
            (cx, cy + 40),
            (cx + 14, cy + 38),
            (cx + 22 + int(wave * 0.7), cy + 26),
            (cx + 17, cy + 5),
            (cx + 13, cy - 10),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_dark"], cape_mid)

        # Inner lining (lighter purple)
        cape_inner = [
            (cx - 10, cy - 6),
            (cx - 13, cy + 5),
            (cx - 16, cy + 22),
            (cx - 8, cy + 32),
            (cx + 8, cy + 32),
            (cx + 16, cy + 22),
            (cx + 13, cy + 5),
            (cx + 10, cy - 6),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_mid"], cape_inner)

        # Ice crystals on cape edges
        for i, (px, py) in enumerate([(cx - 24, cy + 24), (cx + 24, cy + 24),
                                        (cx - 18, cy + 38), (cx + 18, cy + 38)]):
            size = 4 + int(math.sin(phase + i) * 1)
            _NS_varkul._draw_ice_shard(surface, px, py, size, -math.pi / 2 + math.sin(phase) * 0.1,
                            _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                            _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])


    def _draw_lower_robes(surface, cx, cy, phase):
        """Floating lower body with tattered robes (no legs)."""
        sway = int(math.sin(phase * 0.6) * 2)
        # Outer robe
        robe_outer = [
            (cx - 17, cy),
            (cx + 17, cy),
            (cx + 21 + sway, cy + 14),
            (cx + 15, cy + 24),
            (cx + 8, cy + 30),
            (cx + 3, cy + 32),
            (cx - 3, cy + 32),
            (cx - 8, cy + 30),
            (cx - 15, cy + 24),
            (cx - 21 - sway, cy + 14),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in robe_outer])
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_darkest"], robe_outer)

        robe_mid = [
            (cx - 14, cy + 2),
            (cx + 14, cy + 2),
            (cx + 17 + sway, cy + 14),
            (cx + 11, cy + 22),
            (cx + 5, cy + 27),
            (cx - 5, cy + 27),
            (cx - 11, cy + 22),
            (cx - 17 - sway, cy + 14),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_dark"], robe_mid)

        robe_inner = [
            (cx - 10, cy + 4),
            (cx + 10, cy + 4),
            (cx + 13 + sway, cy + 14),
            (cx + 7, cy + 20),
            (cx - 7, cy + 20),
            (cx - 13 - sway, cy + 14),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_mid"], robe_inner)

        # Tattered bottom
        for i in range(7):
            tx = cx - 15 + i * 5
            ty = cy + 28 + int(math.sin(phase * 1.3 + i) * 3)
            _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_dark"], [
                (tx - 2, cy + 24), (tx + 2, cy + 24),
                (tx + 1, ty + 4), (tx - 1, ty + 4),
            ])

        # Gold belt
        _NS_varkul._rect(surface, _NS_varkul.PALETTE["gold_dark"], (cx - 18, cy - 1, 36, 5))
        _NS_varkul._rect(surface, _NS_varkul.PALETTE["gold_mid"], (cx - 16, cy, 32, 3))
        _NS_varkul._rect(surface, _NS_varkul.PALETTE["gold_light"], (cx - 13, cy + 1, 26, 1))

        # Belt center gem – ice
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_darkest"], (cx, cy + 1), 4)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_dark"], (cx, cy + 1), 3)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_mid"], (cx - 1, cy), 2)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (cx - 1, cy), 1)


    def _draw_torso(surface, cx, cy, phase):
        """Torso with robes and a skull emblem."""
        # Shadow
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["shadow_deep"], [
            (cx - 13 + 2, cy - 10 + 2), (cx + 13 + 2, cy - 10 + 2),
            (cx + 11 + 2, cy + 14 + 2), (cx + 5 + 2, cy + 19 + 2),
            (cx - 5 + 2, cy + 19 + 2), (cx - 11 + 2, cy + 14 + 2),
        ])
        # Main torso
        torso = [
            (cx - 13, cy - 10), (cx + 13, cy - 10),
            (cx + 11, cy + 14), (cx + 5, cy + 19),
            (cx - 5, cy + 19), (cx - 11, cy + 14),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_darkest"], torso)
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_dark"], [
            (cx - 11, cy - 8), (cx + 11, cy - 8),
            (cx + 9, cy + 12), (cx + 4, cy + 16),
            (cx - 4, cy + 16), (cx - 9, cy + 12),
        ])
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_mid"], [
            (cx - 8, cy - 5), (cx + 8, cy - 5),
            (cx + 6, cy + 8), (cx + 3, cy + 12),
            (cx - 3, cy + 12), (cx - 6, cy + 8),
        ])

        # Center skull emblem (bone)
        sk_cx, sk_cy = cx, cy + 2
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_dark"], (sk_cx, sk_cy - 2), 5)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_mid"], (sk_cx, sk_cy - 2), 4)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_light"], (sk_cx - 1, sk_cy - 3), 2)
        # Eye sockets on emblem
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["shadow"], (sk_cx - 2, sk_cy - 3), 1)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["shadow"], (sk_cx + 2, sk_cy - 3), 1)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["eye_hot"], (sk_cx - 2, sk_cy - 3), 1)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["eye_hot"], (sk_cx + 2, sk_cy - 3), 1)
        # Jaw
        _NS_varkul._rect(surface, _NS_varkul.PALETTE["bone_dark"], (sk_cx - 2, sk_cy + 1, 4, 3))
        _NS_varkul._rect(surface, _NS_varkul.PALETTE["bone_mid"], (sk_cx - 2, sk_cy + 1, 4, 2))

        # Gold V-neck trim
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["gold_dark"], (cx - 11, cy - 8), (cx, cy - 2), 2)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["gold_dark"], (cx + 11, cy - 8), (cx, cy - 2), 2)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["gold_mid"], (cx - 10, cy - 7), (cx, cy - 3), 1)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["gold_mid"], (cx + 10, cy - 7), (cx, cy - 3), 1)


    def _draw_pauldrons(surface, cx, cy, phase):
        """Ice-crowned shoulder pauldrons."""
        for side in (-1, 1):
            sx = cx + side * 15
            # Shadow
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["shadow_deep"], (sx + 2, cy + 2), 10)
            # Metal pauldron base
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["armor_darkest"], (sx, cy), 9)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["armor_dark"], (sx - side, cy - 1), 7)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["armor_mid"], (sx - side * 2, cy - 2), 5)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["armor_light"], (sx - side * 2, cy - 3), 2)

            # Gold trim
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_dark"], (sx, cy), 9, 2)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_mid"], (sx, cy), 8, 1)

            # Ice crystal spikes on top of pauldron
            for i, off_a in enumerate([-0.4, 0.0, 0.4]):
                spike_angle = -math.pi / 2 + off_a
                size = 6 if i == 1 else 4
                _NS_varkul._draw_ice_shard(surface, sx, cy - 4, size,
                                spike_angle,
                                _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                                _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])


    def _draw_idle_arms(surface, cx, cy, facing, phase, action):
        """Arms - one holds staff, one has orb of frost."""
        sway = int(math.sin(phase * 0.7) * 1)

        # LEFT (staff arm - opposite of facing)
        staff_side = -facing
        ss_x = cx + staff_side * 13
        ss_y = cy + 2
        se_x = ss_x + staff_side * 6
        se_y = cy + 12 + sway
        sh_x = se_x + staff_side * 4
        sh_y = se_y + 10
        _NS_varkul._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_varkul._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        # Draw staff
        _NS_varkul._draw_staff(surface, sh_x, sh_y, phase, staff_side)

        # RIGHT (orb hand - facing direction)
        orb_side = facing
        os_x = cx + orb_side * 13
        os_y = cy + 2
        oe_x = os_x + orb_side * 8
        oe_y = cy + 10 + sway
        oh_x = oe_x + orb_side * 5
        oh_y = oe_y + 8
        _NS_varkul._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        _NS_varkul._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        # Skeletal hand
        _NS_varkul._draw_skeletal_hand(surface, oh_x, oh_y)
        # Frost orb in hand
        _NS_varkul._draw_hand_orb(surface, oh_x + orb_side * 4, oh_y + 2, phase, 5)


    def _draw_attack_arms(surface, cx, cy, facing, phase, progress):
        """Attack pose - staff raised for casting."""
        sway = int(math.sin(phase * 0.7) * 1)

        # STAFF arm rises up during cast
        staff_side = -facing
        ss_x = cx + staff_side * 13
        ss_y = cy + 2

        # Wind up then thrust
        if progress < 0.3:
            t = progress / 0.3
            arm_angle = math.pi / 2 + 0.8 * t  # raising up
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            arm_angle = math.pi / 2 + 0.8 - 0.6 * t
        else:
            t = (progress - 0.5) / 0.5
            arm_angle = math.pi / 2 + 0.2 + 0.5 * t

        se_x = ss_x + int(math.cos(arm_angle) * 10) * staff_side
        se_y = ss_y - int(math.sin(arm_angle) * 10)
        sh_x = se_x + int(math.cos(arm_angle) * 10) * staff_side
        sh_y = se_y - int(math.sin(arm_angle) * 10)

        _NS_varkul._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_varkul._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)
        _NS_varkul._draw_staff(surface, sh_x, sh_y, phase, staff_side, casting=True,
                    progress=progress)

        # ORB hand extends forward
        orb_side = facing
        os_x = cx + orb_side * 13
        os_y = cy + 2

        if progress < 0.35:
            t = progress / 0.35
            ext = t
        elif progress < 0.55:
            ext = 1.0
        else:
            t = (progress - 0.55) / 0.45
            ext = 1.0 - t * 0.7

        oe_x = os_x + orb_side * int(6 + ext * 6)
        oe_y = cy + int(10 - ext * 6)
        oh_x = oe_x + orb_side * int(5 + ext * 5)
        oh_y = oe_y + int(8 - ext * 6)

        _NS_varkul._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        _NS_varkul._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        _NS_varkul._draw_skeletal_hand(surface, oh_x, oh_y)

        # Larger, glowing orb during cast
        orb_size = 6 + int(math.sin(progress * math.pi) * 5)
        _NS_varkul._draw_hand_orb(surface, oh_x + orb_side * 4, oh_y + 2, phase, orb_size)

        # Frost trail from hand during launch
        if 0.25 < progress < 0.55:
            intensity = math.sin((progress - 0.25) / 0.3 * math.pi)
            for i in range(4):
                angle = phase * 3 + i * math.pi / 2
                ex = oh_x + int(math.cos(angle) * 12 * intensity) * facing
                ey = oh_y + int(math.sin(angle) * 10 * intensity)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], 180),
                          (ex, ey), max(1, int(3 * intensity)))
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_white"], 200),
                          (ex, ey), max(1, int(2 * intensity)))


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Draw a robed arm segment."""
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["shadow_deep"], (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 8)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["robe_darkest"], (x1, y1), (x2, y2), 7)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["robe_dark"], (x1, y1), (x2, y2), 5)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["robe_mid"], (x1, y1), (x2, y2), 3)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["robe_light"], (x1, y1 - 1), (x2, y2 - 1), 1)
        # Gold cuff at joint
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_dark"], (mx, my), 4)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_mid"], (mx, my), 3)


    def _draw_skeletal_hand(surface, x, y):
        """Small bony hand."""
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_dark"], (x, y), 4)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_mid"], (x, y), 3)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_light"], (x - 1, y - 1), 1)


    def _draw_hand_orb(surface, x, y, phase, size=5):
        """Frost orb hovering in hand."""
        pulse = math.sin(phase * 1.8) * 0.3 + 0.7
        s = int(size * pulse)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 90), (x, y), s + 6)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], 150), (x, y), s + 3)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_light"], (x, y), s)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (x - 1, y - 1), max(1, s - 2))
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (x - 1, y - 1), max(1, s - 4))

        # Tiny snowflakes floating around
        for i in range(3):
            angle = phase * 2 + i * math.pi * 2 / 3
            sx = x + int(math.cos(angle) * (s + 4))
            sy = y + int(math.sin(angle) * (s + 4))
            _NS_varkul._rect(surface, _NS_varkul.PALETTE["ice_bright"], (sx, sy, 2, 2))


    def _draw_staff(surface, x, y, phase, side, casting=False, progress=0):
        """The frost staff with ice crystal head."""
        # Staff pole - long
        top_x = x + side * -2
        top_y = y - 40
        bot_x = x + side * 4
        bot_y = y + 20

        # Shadow
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["shadow_deep"],
                (top_x + 2, top_y + 2), (bot_x + 2, bot_y + 2), 5)
        # Wood/metal staff
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["armor_darkest"], (top_x, top_y), (bot_x, bot_y), 4)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["armor_dark"], (top_x, top_y), (bot_x, bot_y), 3)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["armor_mid"], (top_x, top_y), (bot_x, bot_y), 1)

        # Gold rings on staff
        for t in (0.3, 0.6, 0.85):
            rx = int(top_x + (bot_x - top_x) * t)
            ry = int(top_y + (bot_y - top_y) * t)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_dark"], (rx, ry), 3)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_mid"], (rx, ry), 2)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_light"], (rx - 1, ry - 1), 1)

        # Staff head - crystal cluster
        head_x, head_y = top_x, top_y - 4

        # Cast glow
        glow_size = 8
        if casting:
            glow_size = 8 + int(math.sin(progress * math.pi) * 10)

        # Backing glow
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 100), (head_x, head_y), glow_size + 4)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], 160), (head_x, head_y), glow_size)

        # Metal claws holding the crystal
        for offset_a in (-1.2, -0.4, 0.4, 1.2):
            cx1 = head_x + int(math.cos(math.pi / 2 + offset_a) * 3)
            cy1 = head_y + int(math.sin(math.pi / 2 + offset_a) * 3)
            cx2 = head_x + int(math.cos(math.pi / 2 + offset_a) * 8)
            cy2 = head_y + int(math.sin(math.pi / 2 + offset_a) * 8) - 4
            _NS_varkul._aaline(surface, _NS_varkul.PALETTE["armor_darkest"], (cx1, cy1), (cx2, cy2), 3)
            _NS_varkul._aaline(surface, _NS_varkul.PALETTE["armor_mid"], (cx1, cy1), (cx2, cy2), 1)

        # Main ice crystal
        _NS_varkul._draw_ice_shard(surface, head_x, head_y, 8, -math.pi / 2,
                        _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                        _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])
        # Center gem
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_dark"], (head_x, head_y - 2), 4)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_mid"], (head_x, head_y - 2), int(3 * pulse) + 1)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (head_x, head_y - 3), 2)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (head_x, head_y - 3), 1)


    def _draw_skull_head(surface, cx, cy, phase):
        """Lich skull head with horned crown."""
        # Shadow
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["shadow_deep"], (cx + 2, cy + 2), 12)

        # Skull main
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_dark"], (cx, cy), 11)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_mid"], (cx - 1, cy - 1), 9)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_light"], (cx - 2, cy - 3), 5)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_shine"], (cx - 3, cy - 4), 2)

        # Skull cheekbones angular
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["bone_dark"], [
            (cx - 10, cy + 2), (cx - 7, cy + 8), (cx - 4, cy + 6)
        ])
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["bone_dark"], [
            (cx + 10, cy + 2), (cx + 7, cy + 8), (cx + 4, cy + 6)
        ])

        # Eye sockets
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["shadow"], (cx - 4, cy - 1), 3)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["shadow"], (cx + 4, cy - 1), 3)

        # Glowing blue eyes
        eye_pulse = math.sin(phase * 1.8) * 0.3 + 0.7
        er = max(1, int(2 * eye_pulse))
        for eox in (-4, 4):
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["eye_dark"], 200), (cx + eox, cy - 1), 3)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["eye_mid"], (cx + eox, cy - 1), er + 1)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["eye_light"], (cx + eox, cy - 1), er)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["eye_hot"], (cx + eox, cy - 1), max(1, er - 1))

        # Eye light streaks/aura
        for eox in (-4, 4):
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["eye_light"], int(80 * eye_pulse)),
                      (cx + eox, cy - 1), 5)

        # Nasal cavity
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["shadow"], [
            (cx - 1, cy + 2), (cx + 1, cy + 2),
            (cx + 2, cy + 5), (cx - 2, cy + 5),
        ])

        # Teeth / jaw
        _NS_varkul._rect(surface, _NS_varkul.PALETTE["bone_dark"], (cx - 5, cy + 6, 10, 4))
        for i in range(5):
            tx = cx - 4 + i * 2
            _NS_varkul._rect(surface, _NS_varkul.PALETTE["bone_light"], (tx, cy + 6, 1, 3))
        # Jaw shadow line
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["shadow"], (cx - 5, cy + 6), (cx + 5, cy + 6), 1)

        # Horned crown - big antler-like horns
        for side in (-1, 1):
            # Main horn curving outward
            base_x = cx + side * 6
            base_y = cy - 8

            # Base of horn
            _NS_varkul._poly(surface, _NS_varkul.PALETTE["bone_dark"], [
                (base_x - 2, base_y),
                (base_x + 2, base_y),
                (base_x + side * 4, base_y - 4),
                (base_x + side * 2, base_y - 5),
            ])

            # Curving horn segments
            for i, (dx, dy, w) in enumerate([
                (side * 4, -6, 3),
                (side * 7, -10, 2),
                (side * 10, -14, 2),
            ]):
                hx = base_x + dx
                hy = base_y + dy
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_dark"], (hx, hy), w)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_mid"], (hx - 1, hy - 1), w - 1)

            # Horn tip
            tip_x = base_x + side * 12
            tip_y = base_y - 16
            _NS_varkul._poly(surface, _NS_varkul.PALETTE["bone_light"], [
                (base_x + side * 10, base_y - 13),
                (base_x + side * 12, base_y - 13),
                (tip_x, tip_y),
            ])

            # Ice crystal at horn base
            _NS_varkul._draw_ice_shard(surface, base_x + side * 3, base_y + 1, 4,
                            -math.pi / 2 + side * 0.3,
                            _NS_varkul.PALETTE["ice_dark"], _NS_varkul.PALETTE["ice_mid"],
                            _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])

        # Central crown ice crystal
        _NS_varkul._draw_ice_shard(surface, cx, cy - 12, 6, -math.pi / 2,
                        _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                        _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])

        # Small side crystals on top
        _NS_varkul._draw_ice_shard(surface, cx - 3, cy - 10, 4, -math.pi / 2 - 0.3,
                        _NS_varkul.PALETTE["ice_dark"], _NS_varkul.PALETTE["ice_mid"],
                        _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])
        _NS_varkul._draw_ice_shard(surface, cx + 3, cy - 10, 4, -math.pi / 2 + 0.3,
                        _NS_varkul.PALETTE["ice_dark"], _NS_varkul.PALETTE["ice_mid"],
                        _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])


    def _draw_body_particles(surface, cx, cy, phase):
        """Floating frost particles around body."""
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            radius = 28 + int(math.sin(phase * 0.7 + i) * 8)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(120 + math.sin(phase + i * 0.7) * 60)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], alpha), (px, py), 2)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_white"], alpha), (px, py), 1)

        # Falling snowflakes
        for i in range(4):
            t = (phase * 0.3 + i * 0.25) % 1.0
            fx = cx - 30 + i * 20 + int(math.sin(phase + i) * 5)
            fy = cy - 40 + int(t * 90)
            alpha = int(200 * (1 - t))
            _NS_varkul._draw_snowflake(surface, fx, fy, 3,
                            phase + i, (*_NS_varkul.PALETTE["ice_bright"], alpha))


    # ===================================================================
    # FLOATING EFFECTS (replaces legs)
    # ===================================================================
    def _draw_floating_mist(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False):
        """Frost mist beneath floating Lich."""
        strength = 1.5 if intense else 1.0

        # Base mist
        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(30, 3, -4):
            alpha = int((30 - radius) * 2.8 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_varkul.PALETTE["ice_dark"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising frost wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 24)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], alpha), (sx, sy), 5)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], alpha), (sx, sy - 2), 3)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_bright"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Orbiting frost crystals
        for i in range(4):
            angle = phase * 0.9 + i * math.pi * 2 / 4
            r = 22 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 6)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_mid"], (sx, sy), 3)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (sx, sy), 2)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 120 - i * 22)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], alpha),
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
        pygame.draw.ellipse(shadow, (*_NS_varkul.PALETTE["ice_dark"], 40), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_frost_aura(surface, x, y, phase):
        """Large background frost aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(70, 5, -4):
            alpha = int((70 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_varkul._aacircle(aura, (*_NS_varkul.PALETTE["ice_darkest"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))


    def _draw_ice_platform(surface, x, y, phase, skill):
        """Ice circle / snowflake pattern on the ground."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        # Outer ice ring
        pygame.draw.ellipse(ring, (*_NS_varkul.PALETTE["ice_dark"], 150),
                            (5, 10, 120, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_varkul.PALETTE["ice_mid"], 180),
                            (20, 14, 90, 16), 2)

        # Snowflake pattern
        for i in range(8):
            angle = phase * 0.15 + i * math.pi / 4
            x1 = 65 + int(math.cos(angle) * 20)
            y1 = 22 + int(math.sin(angle) * 4)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_varkul.PALETTE["ice_light"], 170),
                             (x1, y1), (x2, y2), 1)

        # Ice shard decorations
        for angle_deg in (0, 90, 180, 270):
            angle = math.radians(angle_deg) + phase * 0.1
            sx = 65 + int(math.cos(angle) * 50)
            sy = 22 + int(math.sin(angle) * 9)
            pygame.draw.circle(ring, (*_NS_varkul.PALETTE["ice_bright"], 200), (sx, sy), 2)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_varkul.PALETTE["ice_bright"], int(80 * pulse)),
                                (15, 8, 100, 28), 1)

        surface.blit(ring, (x - 65, y - 22))


    def _draw_cast_flash(surface, x, y, facing, progress):
        """Flash effect during ranged attack."""
        if progress < 0.25 or progress > 0.6:
            return
        t = (progress - 0.25) / 0.35
        intensity = math.sin(t * math.pi)

        # Flash from staff (opposite side)
        flash_x = x - 20 * facing
        flash_y = y - 20

        alpha = int(180 * intensity)
        radius = int(6 + intensity * 15)

        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], alpha // 2),
                  (flash_x, flash_y), radius + 6)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], alpha),
                  (flash_x, flash_y), radius)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_bright"], alpha),
                  (flash_x, flash_y), radius // 2)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_white"], min(255, alpha)),
                  (flash_x, flash_y), max(1, radius // 4))

        # Snowflake burst
        for i in range(5):
            angle = progress * 6 + i * math.pi * 2 / 5
            ex = flash_x + int(math.cos(angle) * radius * 1.4)
            ey = flash_y + int(math.sin(angle) * radius * 1.4)
            _NS_varkul._draw_snowflake(surface, ex, ey, 3, progress,
                            (*_NS_varkul.PALETTE["ice_bright"], alpha))


    # ===================================================================
    # SKILL Q: FROST BLAST
    # ===================================================================
    def _draw_frost_blast_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_varkul._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 80))
        # Ground warning circle at impact
        radius = int(20 + progress * 40)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 100), (tx, ty), radius, 2)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], 80), (tx, ty), radius + 5, 1)


    def _draw_frost_blast(surface, boss, x, y, timer, phase):
        tx, ty = _NS_varkul._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 80))

        start_x = x - 20 * boss.direction
        start_y = y - 20

        if progress < 0.4:
            # Traveling beam of frost
            travel_t = progress / 0.4
            cur_x = start_x + (tx - start_x) * travel_t
            cur_y = start_y + (ty - start_y) * travel_t

            # Comet trail
            for i in range(8):
                t = travel_t - i * 0.05
                if t <= 0:
                    continue
                px = int(start_x + (tx - start_x) * t)
                py = int(start_y + (ty - start_y) * t)
                size = max(2, 10 - i)
                alpha = max(0, 200 - i * 25)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], alpha), (px, py), size + 4)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], alpha), (px, py), size + 2)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_bright"], alpha), (px, py), size)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_white"], alpha), (px, py), max(1, size - 3))

            # Head of comet
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_dark"], (int(cur_x), int(cur_y)), 14)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_mid"], (int(cur_x), int(cur_y)), 10)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_light"], (int(cur_x), int(cur_y)), 7)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (int(cur_x), int(cur_y)), 4)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (int(cur_x), int(cur_y)), 2)

            # Ice shards around comet
            for i in range(5):
                angle = phase * 4 + i * math.pi * 2 / 5
                _NS_varkul._draw_ice_shard(surface, int(cur_x), int(cur_y), 8, angle,
                                _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                                _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])
        else:
            # Impact explosion
            exp_t = (progress - 0.4) / 0.6
            exp_r = int(40 * exp_t)
            alpha = int(255 * (1 - exp_t))

            # Explosion rings
            for i in range(3):
                r = exp_r - i * 5
                if r > 0:
                    _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], alpha),
                              (tx, ty), r, 2)
                    _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], alpha),
                              (tx, ty), max(1, r - 3), 1)

            # Radiating ice shards
            for i in range(12):
                angle = i * math.pi / 6
                dist = 15 + int(exp_r * 0.8)
                sx = tx + int(math.cos(angle) * dist)
                sy = ty + int(math.sin(angle) * dist * 0.7)
                _NS_varkul._draw_ice_shard(surface, sx, sy, 8 + int(math.sin(phase) * 2),
                                angle,
                                _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                                _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])

            # Central flash
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_white"], alpha), (tx, ty), 10)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_bright"], alpha), (tx, ty), 15)


    # ===================================================================
    # SKILL W: FROSTBITE (encase target in ice)
    # ===================================================================
    def _draw_frostbite(surface, boss, x, y, timer, phase):
        tx, ty = _NS_varkul._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 70))

        if progress < 0.3:
            # Frost projectile flying to target
            t = progress / 0.3
            cur_x = x - 20 * boss.direction + (tx - (x - 20 * boss.direction)) * t
            cur_y = y - 20 + (ty - (y - 20)) * t

            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 150),
                      (int(cur_x), int(cur_y)), 10)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_mid"], (int(cur_x), int(cur_y)), 7)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_light"], (int(cur_x), int(cur_y)), 5)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (int(cur_x), int(cur_y)), 2)
        else:
            # Ice prison forming
            t = (progress - 0.3) / 0.7
            size = int(20 + t * 15)

            # Ice block base
            _NS_varkul._poly(surface, (*_NS_varkul.PALETTE["ice_dark"], 200), [
                (tx - size, ty + size),
                (tx - size + 5, ty - size),
                (tx + size - 5, ty - size),
                (tx + size, ty + size),
            ])
            _NS_varkul._poly(surface, (*_NS_varkul.PALETTE["ice_mid"], 220), [
                (tx - size + 3, ty + size - 3),
                (tx - size + 7, ty - size + 3),
                (tx + size - 7, ty - size + 3),
                (tx + size - 3, ty + size - 3),
            ])
            _NS_varkul._poly(surface, (*_NS_varkul.PALETTE["ice_light"], 180), [
                (tx - size + 6, ty + size - 6),
                (tx - size + 10, ty - size + 6),
                (tx + size - 10, ty - size + 6),
                (tx + size - 6, ty + size - 6),
            ])

            # Ice shards around
            for i in range(8):
                angle = phase * 0.5 + i * math.pi / 4
                sx = tx + int(math.cos(angle) * size)
                sy = ty + int(math.sin(angle) * size * 0.7) - 5
                _NS_varkul._draw_ice_shard(surface, sx, sy,
                                6 + int(math.sin(phase + i) * 2),
                                angle - math.pi / 2,
                                _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                                _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])

            # Shine on top
            _NS_varkul._aaline(surface, _NS_varkul.PALETTE["ice_hot"],
                    (tx - size + 8, ty - size + 4),
                    (tx - 2, ty - size + 4), 2)


    # ===================================================================
    # SKILL E: SACRIFICE (drain circle)
    # ===================================================================
    def _draw_sacrifice_circle(surface, boss, x, y, timer, phase):
        """Pentagram circle on ground."""
        progress = max(0.0, min(1.0, 1 - timer / 90))
        radius = int(35 + progress * 25)
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8

        circle = pygame.Surface((radius * 2 + 20, radius + 20), pygame.SRCALPHA)
        cx, cy = radius + 10, (radius + 20) // 2

        # Pentagram base circle
        pygame.draw.ellipse(circle, (*_NS_varkul.PALETTE["ice_dark"], int(180 * pulse)),
                            (5, 5, radius * 2 + 10, radius + 10), 3)
        pygame.draw.ellipse(circle, (*_NS_varkul.PALETTE["ice_mid"], int(150 * pulse)),
                            (15, 8, radius * 2 - 10, radius + 4), 2)

        # Pentagram star
        star_points = []
        for i in range(5):
            a = -math.pi / 2 + i * math.pi * 2 / 5 + phase * 0.1
            px = cx + int(math.cos(a) * (radius - 8))
            py = cy + int(math.sin(a) * (radius // 2 - 4))
            star_points.append((px, py))
        for i in range(5):
            p1 = star_points[i]
            p2 = star_points[(i + 2) % 5]
            pygame.draw.line(circle, (*_NS_varkul.PALETTE["ice_light"], int(200 * pulse)),
                             p1, p2, 2)

        surface.blit(circle, (x - cx, y + 30 - cy))


    def _draw_sacrifice_foreground(surface, boss, x, y, timer, phase):
        """Rising soul energy from ground to Lich."""
        progress = max(0.0, min(1.0, 1 - timer / 90))

        # Rising skull energy
        for i in range(6):
            t = (phase * 0.4 + i * 0.15) % 1.0
            offset_x = math.sin(phase + i * 0.7) * 15
            rx = x + int(offset_x)
            ry = y + 35 - int(t * 55)
            alpha = int(200 * (1 - t))
            size = 4 + int(t * 3)

            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], alpha), (rx, ry), size + 2)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], alpha), (rx, ry), size)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_white"], alpha), (rx, ry), max(1, size - 2))


    # ===================================================================
    # SKILL R: CHAIN FROST
    # ===================================================================
    def _draw_chain_frost_ground(surface, boss, x, y, timer, phase):
        """Warning glow before launch."""
        progress = max(0.0, min(1.0, 1 - timer / 100))
        if progress < 0.3:
            # Charge up
            radius = int(15 + progress * 30)
            pulse = math.sin(phase * 3) * 0.3 + 0.7
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], int(150 * pulse)),
                      (x, y - 20), radius, 2)


    def _draw_chain_frost(surface, boss, x, y, timer, phase):
        """Draw chain frost orb + charging."""
        progress = max(0.0, min(1.0, 1 - timer / 100))

        if progress < 0.35:
            # Charging in hand
            charge = progress / 0.35
            cx, cy = x + boss.direction * 18, y - 15
            r = int(6 + charge * 10)

            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 150), (cx, cy), r + 6)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], 200), (cx, cy), r + 2)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_light"], (cx, cy), r)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (cx, cy), max(1, r - 3))
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (cx, cy), max(1, r - 5))

            # Ice shards forming
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                _NS_varkul._draw_ice_shard(surface, cx, cy, int(6 + charge * 4), angle,
                                _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                                _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])
        elif progress < 0.45 and not getattr(boss, "_vk_chain_launched", False):
            # Launch
            tx, ty = _NS_varkul._target_position(boss, x, y)
            if not hasattr(boss, "_vk_chain_orbs"):
                boss._vk_chain_orbs = []
            boss._vk_chain_orbs.append(
                _NS_varkul.ChainFrostOrb(x + boss.direction * 18, y - 15, tx, ty, bounces=4)
            )
            boss._vk_chain_launched = True

        if progress > 0.9:
            boss._vk_chain_launched = False


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_varkul.draw_varkul(surface, boss, x, y)


# ====================================================================
# XERATHIS
# ====================================================================
class _NS_xerathis:
    """Namespace xerathis - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Crystal Maiden inspired
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin
        "skin_darkest":   (150, 105,  85),
        "skin_dark":      (200, 150, 120),
        "skin_mid":       (235, 195, 165),
        "skin_light":     (250, 220, 195),
        "skin_high":      (255, 240, 220),

        # Hair (blonde)
        "hair_darkest":   (105,  75,  30),
        "hair_dark":      (165, 125,  55),
        "hair_mid":       (215, 175,  95),
        "hair_light":     (245, 215, 145),
        "hair_shine":     (255, 240, 195),

        # Robe – blue/purple
        "robe_darkest":   (18,  22,  58),
        "robe_dark":      (35,  50, 110),
        "robe_mid":       (65,  90, 175),
        "robe_light":     (110, 140, 220),
        "robe_high":      (160, 190, 245),

        # Cloak – deep purple
        "cloak_darkest":  (22,  15,  50),
        "cloak_dark":     (48,  32,  95),
        "cloak_mid":      (80,  55, 145),
        "cloak_light":    (125, 95, 195),

        # Fur trim (white)
        "fur_dark":       (155, 175, 200),
        "fur_mid":        (210, 225, 240),
        "fur_light":      (240, 248, 255),

        # Gold
        "gold_dark":      (95,  70,  20),
        "gold_mid":       (170, 130, 40),
        "gold_light":     (230, 195, 90),
        "gold_shine":     (255, 235, 165),

        # Ice / crystal
        "ice_darkest":    (10,  30,  75),
        "ice_dark":       (25,  70, 145),
        "ice_mid":        (70, 140, 225),
        "ice_light":      (140, 200, 250),
        "ice_bright":     (195, 230, 255),
        "ice_hot":        (225, 245, 255),
        "ice_white":      (245, 252, 255),

        # Eye
        "eye_white":      (240, 248, 255),
        "eye_iris":       (85, 145, 220),
        "eye_iris_light": (150, 200, 255),
        "eye_pupil":      (15,  30,  60),

        # Lips
        "lips_dark":      (170,  75,  85),
        "lips_mid":       (215, 115, 125),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   6,   15),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_xerathis._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_xerathis.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_xerathis._clamp(color)
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
        color = _NS_xerathis._clamp(color)
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
        color = _NS_xerathis._clamp(color)
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
        color = _NS_xerathis._clamp(color)
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
    # Ice / crystal visual helpers
    # ---------------------------------------------------------------------------
    def _draw_ice_shard(surface, cx, cy, size, angle, color_dark, color_mid,
                        color_light, color_hot):
        """Draw a single sharp ice crystal shard."""
        ca, sa = math.cos(angle), math.sin(angle)
        tip_x = cx + ca * size
        tip_y = cy + sa * size
        base_l_x = cx + math.cos(angle + 2.4) * size * 0.35
        base_l_y = cy + math.sin(angle + 2.4) * size * 0.35
        base_r_x = cx + math.cos(angle - 2.4) * size * 0.35
        base_r_y = cy + math.sin(angle - 2.4) * size * 0.35

        _NS_xerathis._poly(surface, color_dark, [
            (tip_x, tip_y), (base_l_x, base_l_y), (base_r_x, base_r_y)
        ])
        _NS_xerathis._poly(surface, color_mid, [
            (tip_x, tip_y),
            ((base_l_x + cx) / 2, (base_l_y + cy) / 2),
            ((base_r_x + cx) / 2, (base_r_y + cy) / 2),
        ])
        _NS_xerathis._aaline(surface, color_light, (cx, cy), (tip_x, tip_y), 1)
        _NS_xerathis._aacircle(surface, color_hot, (int(tip_x), int(tip_y)), 1)


    def _draw_snowflake(surface, cx, cy, size, phase, color=None):
        """Small rotating snowflake."""
        if color is None:
            color = _NS_xerathis.PALETTE["ice_bright"]
        for i in range(6):
            angle = phase * 0.5 + i * math.pi / 3
            x1 = cx + int(math.cos(angle) * size)
            y1 = cy + int(math.sin(angle) * size)
            _NS_xerathis._aaline(surface, color, (cx, cy), (x1, y1), 1)
            bx = cx + int(math.cos(angle) * size * 0.6)
            by = cy + int(math.sin(angle) * size * 0.6)
            for b in (-1, 1):
                ba = angle + b * 0.5
                ex = bx + int(math.cos(ba) * size * 0.3)
                ey = by + int(math.sin(ba) * size * 0.3)
                _NS_xerathis._aaline(surface, color, (bx, by), (ex, ey), 1)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_hot"], (cx, cy), 1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM - Ice Shard Arrow
    # ---------------------------------------------------------------------------
    class IceShardProjectile:
        """Ice shard arrow projectile."""
        def __init__(self, sx, sy, tx, ty, speed=6.5):
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
            if len(self.trail) > 10:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            # Trail - frost mist
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 15)
                r = max(1, 5 - (len(self.trail) - i))
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_dark"], alpha), (tx, ty), r + 2)
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_light"], alpha // 2), (tx, ty), r)

            if self.alive:
                px, py = int(self.x), int(self.y)
                # Glow
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_dark"], 100), (px, py), 12)
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], 150), (px, py), 8)

                # Ice arrow body - shard shape
                ca, sa = math.cos(self.angle), math.sin(self.angle)
                length = 14
                width = 4
                tip_x = px + ca * length
                tip_y = py + sa * length
                tail_x = px - ca * length * 0.7
                tail_y = py - sa * length * 0.7
                # Perpendicular offsets
                perp_x = -sa * width
                perp_y = ca * width

                # Dark outline
                _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_darkest"], [
                    (tip_x, tip_y),
                    (px + perp_x, py + perp_y),
                    (tail_x, tail_y),
                    (px - perp_x, py - perp_y),
                ])
                # Mid layer
                _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_mid"], [
                    (tip_x - ca * 1, tip_y - sa * 1),
                    (px + perp_x * 0.7, py + perp_y * 0.7),
                    (tail_x + ca * 1, tail_y + sa * 1),
                    (px - perp_x * 0.7, py - perp_y * 0.7),
                ])
                # Light layer
                _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_light"], [
                    (tip_x - ca * 2, tip_y - sa * 2),
                    (px + perp_x * 0.4, py + perp_y * 0.4),
                    (tail_x + ca * 2, tail_y + sa * 2),
                    (px - perp_x * 0.4, py - perp_y * 0.4),
                ])
                # Bright core
                _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["ice_bright"],
                        (px - ca * length * 0.5, py - sa * length * 0.5),
                        (tip_x, tip_y), 2)
                _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["ice_white"],
                        (px, py), (tip_x - ca * 2, tip_y - sa * 2), 1)
                # Tip sparkle
                _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_white"], (int(tip_x), int(tip_y)), 2)


    # ---------------------------------------------------------------------------
    # State management helpers
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_xr_last_x"):
            boss._xr_last_x = boss.x
            boss._xr_last_y = boss.y
            return False
        dx = abs(boss.x - boss._xr_last_x)
        dy = abs(boss.y - boss._xr_last_y)
        boss._xr_last_x = boss.x
        boss._xr_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        """Track ranged attack animation timeline."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_xr_prev_timer", -1))
        active = bool(getattr(boss, "_xr_attack_active", False))

        trigger = False
        if previous < 0:
            pass
        elif timer >= cooldown - 1 and previous < cooldown - 1:
            trigger = True
        elif previous >= cooldown - 2 and timer <= 1:
            trigger = True

        if trigger and not active:
            boss._xr_attack_active = True
            boss._xr_attack_frame = 0
            active = True

        if active:
            boss._xr_attack_frame = int(getattr(boss, "_xr_attack_frame", 0)) + 1
            if boss._xr_attack_frame > cooldown:
                boss._xr_attack_active = False
                boss._xr_attack_frame = 0
                active = False

        boss._xr_prev_timer = timer
        boss._xr_attack_progress = (
            min(1.0, getattr(boss, "_xr_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_xr_projectiles"):
            boss._xr_projectiles = []
        for proj in boss._xr_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._xr_projectiles = [p for p in boss._xr_projectiles if p.alive or p.age < 8]


    def _spawn_projectile(boss, x, y):
        if not hasattr(boss, "_xr_projectiles"):
            boss._xr_projectiles = []
        tx, ty = _NS_xerathis._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        # Staff tip position (front-facing side, raised up)
        sx = x + 26 * facing
        sy = y - 18
        boss._xr_projectiles.append(_NS_xerathis.IceShardProjectile(sx, sy, tx, ty, speed=6.5))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_xerathis(surface, boss, x, y):
        """Entry point for Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_xerathis._detect_moving(boss)
        _NS_xerathis._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_xr_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # ---------- Background layers ----------
        _NS_xerathis._draw_frost_aura(surface, x, y, pulse)
        _NS_xerathis._draw_ice_platform(surface, x, y + 40, pulse, active_skill)

        # ---------- Skill ground effects ----------
        if active_skill == "q":
            _NS_xerathis._draw_crystal_nova_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_xerathis._draw_arcane_aura_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xerathis._draw_freezing_field_ground(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if attacking:
            _NS_xerathis._draw_xerathis_attack(surface, boss, x, y)
        elif moving:
            _NS_xerathis._draw_xerathis_walk(surface, boss, x, y)
        else:
            _NS_xerathis._draw_xerathis_idle(surface, boss, x, y)

        # ---------- Projectiles ----------
        _NS_xerathis._manage_projectiles(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "q":
            _NS_xerathis._draw_crystal_nova(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_xerathis._draw_frostbite(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_xerathis._draw_arcane_aura_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xerathis._draw_freezing_field(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_xerathis_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        _NS_xerathis._draw_shadow(surface, x, y + 48)
        _NS_xerathis._draw_floating_mist(surface, x, y + 35, boss.pulse)
        _NS_xerathis._draw_xerathis_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_xerathis_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_xerathis._draw_shadow(surface, x + sway, y + 48)
        _NS_xerathis._draw_floating_mist(surface, x + sway, y + 35, phase, trail=True,
                            facing=boss.direction)
        _NS_xerathis._draw_xerathis_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_xerathis_attack(surface, boss, x, y):
        progress = getattr(boss, "_xr_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        if 0.32 < progress < 0.42 and not getattr(boss, "_xr_proj_spawned", False):
            _NS_xerathis._spawn_projectile(boss, x, y)
            boss._xr_proj_spawned = True
        if progress < 0.15 or progress > 0.9:
            boss._xr_proj_spawned = False

        recoil = int(math.sin(progress * math.pi) * 2) * -boss.direction
        _NS_xerathis._draw_shadow(surface, x + recoil, y + 48)
        _NS_xerathis._draw_floating_mist(surface, x + recoil, y + 35, boss.pulse, intense=True)
        _NS_xerathis._draw_xerathis_body(surface, x + recoil, y, boss.direction, boss.pulse,
                            "attack", progress)
        _NS_xerathis._draw_cast_flash(surface, x + recoil, y, boss.direction, progress)


    # ===================================================================
    # BODY RENDERING – HD detailed Crystal Maiden
    # ===================================================================
    def _draw_xerathis_body(surface, cx, cy, facing, phase, action,
                            attack_progress=0):
        # Cape/cloak behind
        _NS_xerathis._draw_cloak(surface, cx, cy, facing, phase, action)

        # Floating lower body (dress/skirt)
        _NS_xerathis._draw_dress(surface, cx, cy + 5, phase)

        # Torso
        _NS_xerathis._draw_torso(surface, cx, cy - 8, phase)

        # Arms
        if action == "attack":
            _NS_xerathis._draw_attack_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        else:
            _NS_xerathis._draw_idle_arms(surface, cx, cy - 8, facing, phase)

        # Head with hood
        _NS_xerathis._draw_head_hood(surface, cx, cy - 28, facing, phase)

        # Body frost particles
        _NS_xerathis._draw_body_particles(surface, cx, cy, phase)


    def _draw_cloak(surface, cx, cy, facing, phase, action):
        """Flowing purple cloak behind."""
        wave = math.sin(phase * 0.8) * 3
        wave2 = math.sin(phase * 1.1 + 0.5) * 2

        # Outer cloak
        cloak_outer = [
            (cx - 16, cy - 14),
            (cx - 22, cy + 5),
            (cx - 28 - int(wave), cy + 30),
            (cx - 20 - int(wave2), cy + 44),
            (cx - 5, cy + 48),
            (cx + 5, cy + 48),
            (cx + 20 + int(wave2), cy + 44),
            (cx + 28 + int(wave), cy + 30),
            (cx + 22, cy + 5),
            (cx + 16, cy - 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_darkest"], cloak_outer)

        cloak_mid = [
            (cx - 14, cy - 12),
            (cx - 19, cy + 5),
            (cx - 24 - int(wave * 0.7), cy + 28),
            (cx - 15, cy + 40),
            (cx, cy + 42),
            (cx + 15, cy + 40),
            (cx + 24 + int(wave * 0.7), cy + 28),
            (cx + 19, cy + 5),
            (cx + 14, cy - 12),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_dark"], cloak_mid)

        # Inner (lighter)
        cloak_inner = [
            (cx - 11, cy - 8),
            (cx - 14, cy + 5),
            (cx - 18, cy + 24),
            (cx - 8, cy + 34),
            (cx + 8, cy + 34),
            (cx + 18, cy + 24),
            (cx + 14, cy + 5),
            (cx + 11, cy - 8),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_mid"], cloak_inner)

        # Fur trim on edges
        for i, (px, py) in enumerate([
            (cx - 22, cy - 8), (cx - 26, cy + 15), (cx - 22, cy + 38),
            (cx + 22, cy - 8), (cx + 26, cy + 15), (cx + 22, cy + 38),
        ]):
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["fur_dark"], (px, py), 4)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["fur_mid"], (px - 1, py - 1), 3)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["fur_light"], (px - 1, py - 1), 2)


    def _draw_dress(surface, cx, cy, phase):
        """Floating lower dress (no legs)."""
        sway = int(math.sin(phase * 0.6) * 2)
        # Outer skirt
        skirt = [
            (cx - 16, cy),
            (cx + 16, cy),
            (cx + 20 + sway, cy + 14),
            (cx + 15, cy + 24),
            (cx + 7, cy + 30),
            (cx + 2, cy + 32),
            (cx - 2, cy + 32),
            (cx - 7, cy + 30),
            (cx - 15, cy + 24),
            (cx - 20 - sway, cy + 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in skirt])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_darkest"], skirt)

        skirt_mid = [
            (cx - 13, cy + 2),
            (cx + 13, cy + 2),
            (cx + 16 + sway, cy + 14),
            (cx + 10, cy + 22),
            (cx + 5, cy + 27),
            (cx - 5, cy + 27),
            (cx - 10, cy + 22),
            (cx - 16 - sway, cy + 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_dark"], skirt_mid)

        skirt_inner = [
            (cx - 9, cy + 4),
            (cx + 9, cy + 4),
            (cx + 12 + sway, cy + 14),
            (cx + 6, cy + 20),
            (cx - 6, cy + 20),
            (cx - 12 - sway, cy + 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_mid"], skirt_inner)

        # Skirt highlight lines
        for i in range(3):
            lx = cx - 8 + i * 8
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["robe_light"],
                    (lx, cy + 5), (lx + int(sway * 0.3), cy + 25), 1)

        # Tattered bottom (dress fringe)
        for i in range(7):
            tx = cx - 14 + i * 5
            ty = cy + 28 + int(math.sin(phase * 1.3 + i) * 2)
            _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_darkest"], [
                (tx - 2, cy + 24), (tx + 2, cy + 24),
                (tx + 1, ty + 3), (tx - 1, ty + 3),
            ])

        # Gold belt with buckle
        _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["gold_dark"], (cx - 17, cy - 1, 34, 5))
        _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["gold_mid"], (cx - 15, cy, 30, 3))
        _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["gold_light"], (cx - 13, cy + 1, 26, 1))

        # Belt center gem
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_darkest"], (cx, cy + 1), 4)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_dark"], (cx, cy + 1), 3)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_light"], (cx - 1, cy), 2)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_bright"], (cx - 1, cy), 1)


    def _draw_torso(surface, cx, cy, phase):
        """Blue corset/bodice."""
        # Shadow
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["shadow_deep"], [
            (cx - 11 + 2, cy - 8 + 2), (cx + 11 + 2, cy - 8 + 2),
            (cx + 10 + 2, cy + 14 + 2), (cx + 4 + 2, cy + 18 + 2),
            (cx - 4 + 2, cy + 18 + 2), (cx - 10 + 2, cy + 14 + 2),
        ])
        # Corset base
        torso = [
            (cx - 11, cy - 8), (cx + 11, cy - 8),
            (cx + 10, cy + 14), (cx + 4, cy + 18),
            (cx - 4, cy + 18), (cx - 10, cy + 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_darkest"], torso)
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_dark"], [
            (cx - 10, cy - 7), (cx + 10, cy - 7),
            (cx + 8, cy + 12), (cx + 3, cy + 15),
            (cx - 3, cy + 15), (cx - 8, cy + 12),
        ])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_mid"], [
            (cx - 7, cy - 5), (cx + 7, cy - 5),
            (cx + 6, cy + 10), (cx + 2, cy + 12),
            (cx - 2, cy + 12), (cx - 6, cy + 10),
        ])

        # Chest/skin area (top of bodice)
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["skin_dark"], [
            (cx - 7, cy - 9), (cx + 7, cy - 9),
            (cx + 5, cy - 5), (cx - 5, cy - 5),
        ])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["skin_mid"], [
            (cx - 6, cy - 9), (cx + 6, cy - 9),
            (cx + 4, cy - 6), (cx - 4, cy - 6),
        ])
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["skin_light"],
                (cx - 4, cy - 8), (cx + 4, cy - 8), 1)

        # Corset lacing (X pattern)
        for i in range(3):
            y_off = cy - 3 + i * 5
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_mid"],
                    (cx - 3, y_off), (cx + 3, y_off + 3), 1)
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_mid"],
                    (cx + 3, y_off), (cx - 3, y_off + 3), 1)

        # Center gem on chest
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["gold_dark"], (cx, cy - 1), 3)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_mid"], (cx, cy - 1), 2)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_bright"], (cx, cy - 2), 1)

        # Side highlights on corset
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["robe_light"],
                (cx - 9, cy - 5), (cx - 8, cy + 12), 1)


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Idle arms - one holds staff, other rests."""
        sway = int(math.sin(phase * 0.7) * 1)

        # STAFF arm (facing side - holding staff up)
        staff_side = facing
        ss_x = cx + staff_side * 11
        ss_y = cy + 2
        se_x = ss_x + staff_side * 6
        se_y = cy - 4 + sway
        sh_x = se_x + staff_side * 4
        sh_y = se_y - 4
        _NS_xerathis._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_xerathis._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)
        _NS_xerathis._draw_hand(surface, sh_x, sh_y)
        # Staff
        _NS_xerathis._draw_staff(surface, sh_x, sh_y, phase, staff_side)

        # OTHER arm (opposite side - resting)
        other_side = -facing
        os_x = cx + other_side * 11
        os_y = cy + 2
        oe_x = os_x + other_side * 5
        oe_y = cy + 10 + sway
        oh_x = oe_x + other_side * 3
        oh_y = oe_y + 8
        _NS_xerathis._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        _NS_xerathis._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        _NS_xerathis._draw_hand(surface, oh_x, oh_y)


    def _draw_attack_arms(surface, cx, cy, facing, phase, progress):
        """Attack pose - staff aimed forward for casting."""
        sway = int(math.sin(phase * 0.7) * 1)

        # STAFF arm extends forward for aim/cast
        staff_side = facing
        ss_x = cx + staff_side * 11
        ss_y = cy + 2

        # Aim/thrust motion
        if progress < 0.3:
            t = progress / 0.3
            ext = t * 0.4  # slight windup
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            ext = 0.4 + t * 0.6  # thrust forward
        else:
            t = (progress - 0.5) / 0.5
            ext = 1.0 - t * 0.6

        # Aim angle - slight upward
        aim_angle = -0.15
        se_x = ss_x + int((6 + ext * 4) * math.cos(aim_angle)) * staff_side
        se_y = ss_y + int((6 + ext * 4) * math.sin(aim_angle)) - 2
        sh_x = se_x + int((6 + ext * 6) * math.cos(aim_angle)) * staff_side
        sh_y = se_y + int((6 + ext * 6) * math.sin(aim_angle)) - 4

        _NS_xerathis._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_xerathis._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)
        _NS_xerathis._draw_hand(surface, sh_x, sh_y)
        _NS_xerathis._draw_staff(surface, sh_x, sh_y, phase, staff_side, casting=True,
                    progress=progress)

        # OTHER arm (steadying - held out slightly)
        other_side = -facing
        os_x = cx + other_side * 11
        os_y = cy + 2
        oe_x = os_x + other_side * 6
        oe_y = cy + 6 + sway
        oh_x = oe_x + other_side * 4
        oh_y = oe_y + 6
        _NS_xerathis._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        _NS_xerathis._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        _NS_xerathis._draw_hand(surface, oh_x, oh_y)


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Draw a robed arm segment."""
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["shadow_deep"], (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 7)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["robe_darkest"], (x1, y1), (x2, y2), 6)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["robe_dark"], (x1, y1), (x2, y2), 4)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["robe_mid"], (x1, y1), (x2, y2), 2)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["robe_light"], (x1, y1 - 1), (x2, y2 - 1), 1)


    def _draw_hand(surface, x, y):
        """Small skin-colored hand."""
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_darkest"], (x, y), 3)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_mid"], (x, y), 2)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_light"], (x - 1, y - 1), 1)


    def _draw_staff(surface, x, y, phase, side, casting=False, progress=0):
        """The crystal staff."""
        # Staff pole - long, from hand upward and behind
        top_x = x + side * 4
        top_y = y - 38
        bot_x = x - side * 2
        bot_y = y + 16

        # Shadow
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["shadow_deep"],
                (top_x + 2, top_y + 2), (bot_x + 2, bot_y + 2), 5)
        # Wooden staff (gold-colored)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_dark"], (top_x, top_y), (bot_x, bot_y), 4)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_mid"], (top_x, top_y), (bot_x, bot_y), 3)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_light"], (top_x, top_y), (bot_x, bot_y), 1)

        # Wraps/rings on staff
        for t in (0.35, 0.65, 0.85):
            rx = int(top_x + (bot_x - top_x) * t)
            ry = int(top_y + (bot_y - top_y) * t)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["cloak_dark"], (rx, ry), 3)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["cloak_mid"], (rx, ry), 2)

        # Staff head - crystal cluster
        head_x, head_y = top_x, top_y - 4

        glow_size = 8
        if casting:
            glow_size = 8 + int(math.sin(progress * math.pi) * 12)

        # Backing glow
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_dark"], 100), (head_x, head_y), glow_size + 4)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], 160), (head_x, head_y), glow_size)

        # Gold claws holding the crystal
        for offset_a in (-1.0, -0.3, 0.3, 1.0):
            cx1 = head_x + int(math.cos(math.pi / 2 + offset_a) * 3)
            cy1 = head_y + int(math.sin(math.pi / 2 + offset_a) * 3)
            cx2 = head_x + int(math.cos(math.pi / 2 + offset_a) * 8)
            cy2 = head_y + int(math.sin(math.pi / 2 + offset_a) * 8) - 3
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_dark"], (cx1, cy1), (cx2, cy2), 3)
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_mid"], (cx1, cy1), (cx2, cy2), 1)

        # Large main ice crystal - vertical
        crystal_h = 10
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_darkest"], [
            (head_x - 4, head_y),
            (head_x + 4, head_y),
            (head_x + 3, head_y - crystal_h + 2),
            (head_x, head_y - crystal_h),
            (head_x - 3, head_y - crystal_h + 2),
        ])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_dark"], [
            (head_x - 3, head_y - 1),
            (head_x + 3, head_y - 1),
            (head_x + 2, head_y - crystal_h + 3),
            (head_x, head_y - crystal_h + 1),
            (head_x - 2, head_y - crystal_h + 3),
        ])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_mid"], [
            (head_x - 2, head_y - 2),
            (head_x + 2, head_y - 2),
            (head_x + 1, head_y - crystal_h + 4),
            (head_x, head_y - crystal_h + 2),
            (head_x - 1, head_y - crystal_h + 4),
        ])
        # Bright highlight
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["ice_bright"],
                (head_x - 1, head_y - crystal_h + 3),
                (head_x - 1, head_y - 2), 1)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_white"], (head_x - 1, head_y - crystal_h + 4), 1)

        # Small side crystals
        _NS_xerathis._draw_ice_shard(surface, head_x - 3, head_y - 3, 4, -math.pi / 2 - 0.4,
                        _NS_xerathis.PALETTE["ice_dark"], _NS_xerathis.PALETTE["ice_mid"],
                        _NS_xerathis.PALETTE["ice_light"], _NS_xerathis.PALETTE["ice_white"])
        _NS_xerathis._draw_ice_shard(surface, head_x + 3, head_y - 3, 4, -math.pi / 2 + 0.4,
                        _NS_xerathis.PALETTE["ice_dark"], _NS_xerathis.PALETTE["ice_mid"],
                        _NS_xerathis.PALETTE["ice_light"], _NS_xerathis.PALETTE["ice_white"])

        # Pulsing glow
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], int(80 * pulse)),
                  (head_x, head_y - 4), int(6 * pulse))


    def _draw_head_hood(surface, cx, cy, facing, phase):
        """Crystal Maiden's face with hood and hair."""
        # Hood back (behind head)
        hood_back = [
            (cx - 12, cy - 6),
            (cx - 14, cy + 4),
            (cx - 12, cy + 12),
            (cx + 12, cy + 12),
            (cx + 14, cy + 4),
            (cx + 12, cy - 6),
            (cx + 8, cy - 14),
            (cx - 8, cy - 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in hood_back])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_darkest"], hood_back)
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_dark"], [
            (cx - 11, cy - 5),
            (cx - 13, cy + 4),
            (cx - 11, cy + 11),
            (cx + 11, cy + 11),
            (cx + 13, cy + 4),
            (cx + 11, cy - 5),
            (cx + 7, cy - 13),
            (cx - 7, cy - 13),
        ])

        # Hair fringe (blonde, visible under hood)
        hair_points = [
            (cx - 8, cy - 6),
            (cx - 9, cy - 2),
            (cx - 7, cy + 1),
            (cx - 3, cy - 1),
            (cx, cy),
            (cx + 3, cy - 1),
            (cx + 7, cy + 1),
            (cx + 9, cy - 2),
            (cx + 8, cy - 6),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["hair_darkest"], hair_points)
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["hair_dark"], [
            (cx - 7, cy - 5),
            (cx - 8, cy - 2),
            (cx - 6, cy),
            (cx - 2, cy - 1),
            (cx + 2, cy - 1),
            (cx + 6, cy),
            (cx + 8, cy - 2),
            (cx + 7, cy - 5),
        ])
        # Hair highlight
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["hair_mid"],
                (cx - 5, cy - 4), (cx - 3, cy - 2), 1)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["hair_light"],
                (cx + 3, cy - 4), (cx + 5, cy - 3), 1)

        # Face (skin)
        face_points = [
            (cx - 6, cy),
            (cx - 7, cy + 4),
            (cx - 5, cy + 8),
            (cx - 2, cy + 10),
            (cx + 2, cy + 10),
            (cx + 5, cy + 8),
            (cx + 7, cy + 4),
            (cx + 6, cy),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["skin_darkest"],
              [(p[0] + 1, p[1] + 1) for p in face_points])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["skin_dark"], face_points)
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["skin_mid"], [
            (cx - 5, cy + 1),
            (cx - 6, cy + 4),
            (cx - 4, cy + 7),
            (cx - 2, cy + 9),
            (cx + 2, cy + 9),
            (cx + 4, cy + 7),
            (cx + 6, cy + 4),
            (cx + 5, cy + 1),
        ])
        # Cheek highlights
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_light"], (cx - 3, cy + 5), 2)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_light"], (cx + 3, cy + 5), 2)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_high"], (cx - 3, cy + 5), 1)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_high"], (cx + 3, cy + 5), 1)

        # Eyes
        for eye_x in (-3, 3):
            # Eye white
            _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["eye_white"], (cx + eye_x - 1, cy + 3, 2, 2))
            # Iris
            _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["eye_iris"], (cx + eye_x - 1, cy + 3, 2, 2))
            # Bright center
            _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["eye_iris_light"], (cx + eye_x, cy + 3, 1, 1))

        # Eyelashes/brows
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["hair_darkest"],
                (cx - 5, cy + 2), (cx - 1, cy + 2), 1)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["hair_darkest"],
                (cx + 1, cy + 2), (cx + 5, cy + 2), 1)

        # Nose (subtle)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_darkest"], (cx, cy + 6), 1)

        # Lips
        _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["lips_dark"], (cx - 2, cy + 8, 4, 1))
        _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["lips_mid"], (cx - 1, cy + 8, 2, 1))

        # Hood top (in front, framing the face)
        hood_top = [
            (cx - 11, cy - 5),
            (cx - 13, cy - 2),
            (cx - 10, cy + 2),
            (cx - 8, cy - 2),
            (cx - 6, cy - 8),
            (cx, cy - 12),
            (cx + 6, cy - 8),
            (cx + 8, cy - 2),
            (cx + 10, cy + 2),
            (cx + 13, cy - 2),
            (cx + 11, cy - 5),
            (cx + 8, cy - 14),
            (cx - 8, cy - 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_darkest"], hood_top)
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_dark"], [
            (cx - 10, cy - 4),
            (cx - 11, cy - 2),
            (cx - 9, cy + 1),
            (cx - 8, cy - 3),
            (cx - 6, cy - 7),
            (cx, cy - 11),
            (cx + 6, cy - 7),
            (cx + 8, cy - 3),
            (cx + 9, cy + 1),
            (cx + 11, cy - 2),
            (cx + 10, cy - 4),
            (cx + 7, cy - 13),
            (cx - 7, cy - 13),
        ])
        # Hood mid highlight
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_mid"], [
            (cx - 8, cy - 6),
            (cx - 9, cy - 3),
            (cx - 7, cy - 1),
            (cx - 5, cy - 6),
            (cx, cy - 9),
            (cx + 5, cy - 6),
            (cx + 7, cy - 1),
            (cx + 9, cy - 3),
            (cx + 8, cy - 6),
            (cx + 6, cy - 11),
            (cx - 6, cy - 11),
        ])

        # White fur trim on hood
        for i in range(9):
            angle = -math.pi + i * math.pi / 8
            fx = cx + int(math.cos(angle) * 12)
            fy = cy - 4 + int(math.sin(angle) * 9)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["fur_dark"], (fx, fy), 3)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["fur_mid"], (fx - 1, fy - 1), 2)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["fur_light"], (fx - 1, fy - 1), 1)

        # Ice crystal on top of hood
        _NS_xerathis._draw_ice_shard(surface, cx, cy - 15, 5, -math.pi / 2,
                        _NS_xerathis.PALETTE["ice_darkest"], _NS_xerathis.PALETTE["ice_dark"],
                        _NS_xerathis.PALETTE["ice_light"], _NS_xerathis.PALETTE["ice_white"])

        # Small ear/hair strands on sides
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["hair_dark"], [
            (cx - 8, cy + 2), (cx - 10, cy + 6), (cx - 7, cy + 8)
        ])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["hair_dark"], [
            (cx + 8, cy + 2), (cx + 10, cy + 6), (cx + 7, cy + 8)
        ])
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["hair_mid"],
                (cx - 8, cy + 3), (cx - 9, cy + 6), 1)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["hair_mid"],
                (cx + 8, cy + 3), (cx + 9, cy + 6), 1)


    def _draw_body_particles(surface, cx, cy, phase):
        """Floating frost particles around body."""
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            radius = 28 + int(math.sin(phase * 0.7 + i) * 8)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(120 + math.sin(phase + i * 0.7) * 60)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_light"], alpha), (px, py), 2)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_white"], alpha), (px, py), 1)

        # Falling snowflakes
        for i in range(4):
            t = (phase * 0.3 + i * 0.25) % 1.0
            fx = cx - 30 + i * 20 + int(math.sin(phase + i) * 5)
            fy = cy - 40 + int(t * 90)
            alpha = int(200 * (1 - t))
            _NS_xerathis._draw_snowflake(surface, fx, fy, 3,
                            phase + i, (*_NS_xerathis.PALETTE["ice_bright"], alpha))


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_mist(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False):
        """Frost mist beneath floating Xerathis."""
        strength = 1.5 if intense else 1.0

        # Base mist
        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(30, 3, -4):
            alpha = int((30 - radius) * 2.8 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_xerathis.PALETTE["ice_dark"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising frost wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 24)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_dark"], alpha), (sx, sy), 5)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], alpha), (sx, sy - 2), 3)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Orbiting frost crystals
        for i in range(4):
            angle = phase * 0.9 + i * math.pi * 2 / 4
            r = 22 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 6)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_mid"], (sx, sy), 3)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_bright"], (sx, sy), 2)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_white"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 120 - i * 22)
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], alpha),
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
        pygame.draw.ellipse(shadow, (*_NS_xerathis.PALETTE["ice_dark"], 40), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_frost_aura(surface, x, y, phase):
        """Large background aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(70, 5, -4):
            alpha = int((70 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_xerathis._aacircle(aura, (*_NS_xerathis.PALETTE["ice_darkest"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))


    def _draw_ice_platform(surface, x, y, phase, skill):
        """Ice snowflake pattern on the ground."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_xerathis.PALETTE["ice_dark"], 150),
                            (5, 10, 120, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_xerathis.PALETTE["ice_mid"], 180),
                            (20, 14, 90, 16), 2)

        for i in range(8):
            angle = phase * 0.15 + i * math.pi / 4
            x1 = 65 + int(math.cos(angle) * 20)
            y1 = 22 + int(math.sin(angle) * 4)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_xerathis.PALETTE["ice_light"], 170),
                             (x1, y1), (x2, y2), 1)

        for angle_deg in (0, 90, 180, 270):
            angle = math.radians(angle_deg) + phase * 0.1
            sx = 65 + int(math.cos(angle) * 50)
            sy = 22 + int(math.sin(angle) * 9)
            pygame.draw.circle(ring, (*_NS_xerathis.PALETTE["ice_bright"], 200), (sx, sy), 2)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_xerathis.PALETTE["ice_bright"], int(80 * pulse)),
                                (15, 8, 100, 28), 1)

        surface.blit(ring, (x - 65, y - 22))


    def _draw_cast_flash(surface, x, y, facing, progress):
        """Flash effect during ranged attack (at staff tip)."""
        if progress < 0.25 or progress > 0.6:
            return
        t = (progress - 0.25) / 0.35
        intensity = math.sin(t * math.pi)

        flash_x = x + 26 * facing
        flash_y = y - 18

        alpha = int(180 * intensity)
        radius = int(6 + intensity * 15)

        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], alpha // 2),
                  (flash_x, flash_y), radius + 6)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_light"], alpha),
                  (flash_x, flash_y), radius)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], alpha),
                  (flash_x, flash_y), radius // 2)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_white"], min(255, alpha)),
                  (flash_x, flash_y), max(1, radius // 4))

        for i in range(5):
            angle = progress * 6 + i * math.pi * 2 / 5
            ex = flash_x + int(math.cos(angle) * radius * 1.4)
            ey = flash_y + int(math.sin(angle) * radius * 1.4)
            _NS_xerathis._draw_snowflake(surface, ex, ey, 3, progress,
                            (*_NS_xerathis.PALETTE["ice_bright"], alpha))


    # ===================================================================
    # SKILL Q: CRYSTAL NOVA (AoE ice explosion at target)
    # ===================================================================
    def _draw_crystal_nova_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_xerathis._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 80))
        # Warning circle
        radius = int(25 + progress * 45)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_dark"], 100), (tx, ty), radius, 2)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], 80), (tx, ty), radius + 6, 1)


    def _draw_crystal_nova(surface, boss, x, y, timer, phase):
        tx, ty = _NS_xerathis._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 80))

        if progress < 0.35:
            # Casting phase - energy gathering above target
            t = progress / 0.35
            # Rising energy above target
            for i in range(5):
                offset = i * 0.15
                it = min(1.0, t + offset)
                gy = ty - int(it * 30)
                alpha = int(180 * (1 - offset))
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_light"], alpha),
                          (tx, gy), max(1, 4 - i))
        else:
            # Nova explosion phase
            t = (progress - 0.35) / 0.65

            # Central burst
            burst_r = int(20 + t * 25)
            alpha = int(220 * (1 - t))

            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], alpha), (tx, ty), burst_r + 4)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_light"], alpha), (tx, ty), burst_r)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], alpha), (tx, ty), burst_r // 2)

            # Radial ice crystals rising from ground
            for i in range(10):
                angle = i * math.pi / 5 + phase * 0.05
                dist = int(15 + t * 30)
                sx = tx + int(math.cos(angle) * dist)
                sy = ty + int(math.sin(angle) * dist * 0.6)

                # Rising crystal
                grow = min(1.0, t * 2.0)
                size = int(12 * grow)

                _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_darkest"], [
                    (sx - 4, sy + size // 2),
                    (sx + 4, sy + size // 2),
                    (sx + 2, sy - size),
                    (sx, sy - size - 2),
                    (sx - 2, sy - size),
                ])
                _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_dark"], [
                    (sx - 3, sy + size // 2 - 1),
                    (sx + 3, sy + size // 2 - 1),
                    (sx + 1, sy - size + 1),
                    (sx, sy - size - 1),
                    (sx - 1, sy - size + 1),
                ])
                _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_mid"], [
                    (sx - 2, sy + size // 2 - 2),
                    (sx + 2, sy + size // 2 - 2),
                    (sx + 1, sy - size + 2),
                    (sx - 1, sy - size + 2),
                ])
                _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["ice_bright"],
                        (sx, sy + size // 2 - 2), (sx, sy - size + 2), 1)
                _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_white"], (sx, sy - size), 1)

            # Ring shockwave
            ring_r = int(40 + t * 30)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_light"], int(150 * (1 - t))),
                      (tx, ty), ring_r, 2)


    # ===================================================================
    # SKILL W: FROSTBITE
    # ===================================================================
    def _draw_frostbite(surface, boss, x, y, timer, phase):
        tx, ty = _NS_xerathis._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 70))

        start_x = x + 26 * boss.direction
        start_y = y - 18

        if progress < 0.35:
            # Frost bolt flying to target
            t = progress / 0.35
            cur_x = start_x + (tx - start_x) * t
            cur_y = start_y + (ty - start_y) * t

            # Trail
            for i in range(6):
                tt = t - i * 0.05
                if tt <= 0:
                    continue
                px = int(start_x + (tx - start_x) * tt)
                py = int(start_y + (ty - start_y) * tt)
                alpha = max(0, 200 - i * 30)
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], alpha), (px, py), 6 - i // 2)
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], alpha), (px, py), 3)

            # Bolt head
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_dark"], 200),
                      (int(cur_x), int(cur_y)), 12)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_light"], (int(cur_x), int(cur_y)), 7)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_bright"], (int(cur_x), int(cur_y)), 4)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_white"], (int(cur_x), int(cur_y)), 2)
        else:
            # Target is frozen - ice encasing
            t = (progress - 0.35) / 0.65
            size = int(18 + t * 8)

            # Ice block encasing target
            _NS_xerathis._poly(surface, (*_NS_xerathis.PALETTE["ice_dark"], 220), [
                (tx - size, ty + size),
                (tx - size + 4, ty - size),
                (tx + size - 4, ty - size),
                (tx + size, ty + size),
            ])
            _NS_xerathis._poly(surface, (*_NS_xerathis.PALETTE["ice_mid"], 200), [
                (tx - size + 3, ty + size - 3),
                (tx - size + 6, ty - size + 3),
                (tx + size - 6, ty - size + 3),
                (tx + size - 3, ty + size - 3),
            ])
            _NS_xerathis._poly(surface, (*_NS_xerathis.PALETTE["ice_light"], 160), [
                (tx - size + 6, ty + size - 6),
                (tx - size + 9, ty - size + 6),
                (tx + size - 9, ty - size + 6),
                (tx + size - 6, ty + size - 6),
            ])

            # Ice crystals sticking out
            for i in range(6):
                angle = phase * 0.5 + i * math.pi / 3
                sx = tx + int(math.cos(angle) * size)
                sy = ty + int(math.sin(angle) * size * 0.7) - 3
                _NS_xerathis._draw_ice_shard(surface, sx, sy,
                                5 + int(math.sin(phase + i) * 1),
                                angle - math.pi / 2,
                                _NS_xerathis.PALETTE["ice_darkest"], _NS_xerathis.PALETTE["ice_dark"],
                                _NS_xerathis.PALETTE["ice_light"], _NS_xerathis.PALETTE["ice_white"])

            # Shine highlight
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["ice_hot"],
                    (tx - size + 8, ty - size + 4),
                    (tx - 2, ty - size + 4), 2)


    # ===================================================================
    # SKILL E: ARCANE AURA (buffs self)
    # ===================================================================
    def _draw_arcane_aura_ground(surface, boss, x, y, timer, phase):
        """Aura circle around Xerathis on ground."""
        progress = max(0.0, min(1.0, 1 - timer / 90))
        radius = int(45 + progress * 20)
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8

        aura = pygame.Surface((radius * 2 + 20, radius + 20), pygame.SRCALPHA)
        cx, cy = radius + 10, (radius + 20) // 2

        # Ring
        pygame.draw.ellipse(aura, (*_NS_xerathis.PALETTE["ice_mid"], int(180 * pulse)),
                            (5, 5, radius * 2 + 10, radius + 10), 3)
        pygame.draw.ellipse(aura, (*_NS_xerathis.PALETTE["ice_bright"], int(150 * pulse)),
                            (15, 8, radius * 2 - 10, radius + 4), 2)

        # Runic marks around aura
        for i in range(8):
            a = phase * 0.3 + i * math.pi / 4
            px = cx + int(math.cos(a) * (radius - 5))
            py = cy + int(math.sin(a) * (radius // 2 - 4))
            pygame.draw.circle(aura, (*_NS_xerathis.PALETTE["ice_hot"], int(220 * pulse)),
                               (px, py), 3)
            pygame.draw.circle(aura, (*_NS_xerathis.PALETTE["ice_white"], int(220 * pulse)),
                               (px, py), 1)

        surface.blit(aura, (x - cx, y + 30 - cy))


    def _draw_arcane_aura_foreground(surface, boss, x, y, timer, phase):
        """Rising magical energy around Xerathis."""
        progress = max(0.0, min(1.0, 1 - timer / 90))

        # Rising energy particles all around body
        for i in range(10):
            t = (phase * 0.5 + i * 0.1) % 1.0
            angle = i * math.pi / 5 + phase * 0.3
            dist = 20 + int(math.sin(phase + i) * 5)
            sx = x + int(math.cos(angle) * dist)
            sy = y + 30 - int(t * 70)
            alpha = int(200 * (1 - t))
            size = 3 + int(t * 3)

            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], alpha), (sx, sy), size + 2)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], alpha), (sx, sy), size)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_white"], alpha), (sx, sy), max(1, size - 2))

        # Pulsing halo around body
        pulse = math.sin(phase * 2) * 0.2 + 0.8
        halo_r = int(40 * pulse)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], int(60 * pulse)),
                  (x, y - 10), halo_r, 2)


    # ===================================================================
    # SKILL R: FREEZING FIELD
    # ===================================================================
    def _draw_freezing_field_ground(surface, boss, x, y, timer, phase):
        """Large ice field around Xerathis."""
        progress = max(0.0, min(1.0, 1 - timer / 100))
        radius = int(60 + progress * 30)
        pulse = math.sin(phase * 1.2) * 0.2 + 0.8

        field = pygame.Surface((radius * 2 + 30, radius + 30), pygame.SRCALPHA)
        cx, cy = radius + 15, (radius + 30) // 2

        # Base ice ring
        pygame.draw.ellipse(field, (*_NS_xerathis.PALETTE["ice_dark"], int(180 * pulse)),
                            (5, 5, radius * 2 + 20, radius + 20), 4)
        pygame.draw.ellipse(field, (*_NS_xerathis.PALETTE["ice_mid"], int(140 * pulse)),
                            (20, 12, radius * 2 - 10, radius + 6), 2)

        # Frost pattern
        for i in range(12):
            a = phase * 0.2 + i * math.pi / 6
            x1 = cx + int(math.cos(a) * 15)
            y1 = cy + int(math.sin(a) * 5)
            x2 = cx + int(math.cos(a) * (radius - 5))
            y2 = cy + int(math.sin(a) * (radius // 2 - 2))
            pygame.draw.line(field, (*_NS_xerathis.PALETTE["ice_light"], int(150 * pulse)),
                             (x1, y1), (x2, y2), 1)

        surface.blit(field, (x - cx, y + 30 - cy))


    def _draw_freezing_field(surface, boss, x, y, timer, phase):
        """Randomly exploding ice crystals in the field."""
        progress = max(0.0, min(1.0, 1 - timer / 100))

        # Deterministic random positions using phase
        for i in range(8):
            # Each crystal has its own life cycle
            crystal_phase = (phase * 0.4 + i * 0.35) % 1.0
            angle = i * math.pi / 4 + i * 0.7
            dist_r = 40 + (i * 13) % 30
            px = x + int(math.cos(angle) * dist_r)
            py = y + 25 + int(math.sin(angle) * dist_r * 0.3)

            # Grow then shrink cycle
            if crystal_phase < 0.5:
                grow = crystal_phase / 0.5
            else:
                grow = 1.0 - (crystal_phase - 0.5) / 0.5

            size = int(14 * grow)
            if size < 2:
                continue

            # Ice crystal spike shooting up
            _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_darkest"], [
                (px - 5, py + size // 2),
                (px + 5, py + size // 2),
                (px + 3, py - size),
                (px, py - size - 3),
                (px - 3, py - size),
            ])
            _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_dark"], [
                (px - 4, py + size // 2 - 1),
                (px + 4, py + size // 2 - 1),
                (px + 2, py - size + 1),
                (px, py - size - 2),
                (px - 2, py - size + 1),
            ])
            _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_mid"], [
                (px - 3, py + size // 2 - 2),
                (px + 3, py + size // 2 - 2),
                (px + 1, py - size + 2),
                (px, py - size - 1),
                (px - 1, py - size + 2),
            ])
            _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_light"], [
                (px - 2, py + size // 2 - 3),
                (px + 2, py + size // 2 - 3),
                (px + 1, py - size + 3),
                (px - 1, py - size + 3),
            ])
            # Highlight
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["ice_bright"],
                    (px, py + size // 2 - 3), (px, py - size + 3), 1)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_white"], (px, py - size), 1)

            # Impact glow at base
            if grow > 0.3:
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], int(150 * grow)),
                          (px, py + size // 2), int(size * 0.8))

        # Continuous swirling frost energy
        for i in range(8):
            angle = phase * 0.8 + i * math.pi / 4
            r = 55
            sx = x + int(math.cos(angle) * r)
            sy = y + 25 + int(math.sin(angle) * r * 0.35)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], 180), (sx, sy), 2)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_white"], 220), (sx, sy), 1)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_xerathis.draw_xerathis(surface, boss, x, y)


# ====================================================================
# NYZRAK
# ====================================================================
class _NS_nyzrak:
    """Namespace nyzrak - isi asli tidak diubah."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Winter Palette
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Wyvern body - teal/cyan
        "wy_darkest":     (5,   30,  40),
        "wy_dark":        (18,  70,  90),
        "wy_mid":         (45, 135, 155),
        "wy_light":       (95, 190, 210),
        "wy_high":        (155, 225, 235),
        "wy_shine":       (215, 245, 250),

        # Wyvern belly (lighter)
        "belly_dark":     (85, 140, 155),
        "belly_mid":      (140, 195, 210),
        "belly_light":    (200, 235, 245),

        # Wing membrane (blue-purple)
        "wing_darkest":   (18,  20,  55),
        "wing_dark":      (45,  55, 115),
        "wing_mid":       (85, 100, 175),
        "wing_light":     (140, 165, 220),

        # Rider - purple/blue robe
        "robe_darkest":   (25,  20,  55),
        "robe_dark":      (55,  50, 105),
        "robe_mid":       (95,  90, 155),
        "robe_light":     (150, 145, 200),
        "robe_high":      (200, 195, 235),

        # Fur trim (white)
        "fur_dark":       (155, 165, 185),
        "fur_mid":        (210, 220, 235),
        "fur_light":      (245, 250, 255),

        # Rider skin (fair)
        "skin_dark":      (185, 145, 130),
        "skin_mid":       (230, 195, 175),
        "skin_light":     (250, 225, 210),

        # Hair (blonde/white)
        "hair_dark":      (185, 155, 100),
        "hair_mid":       (225, 200, 145),
        "hair_light":     (250, 235, 190),

        # Ice / crystal
        "ice_darkest":    (8,   35,  75),
        "ice_dark":       (30,  85, 155),
        "ice_mid":        (75, 155, 220),
        "ice_light":      (150, 210, 245),
        "ice_bright":     (200, 235, 250),
        "ice_hot":        (230, 245, 255),
        "ice_pure":       (250, 253, 255),

        # Purple frost (Q skill)
        "frost_darkest":  (25,  10,  60),
        "frost_dark":     (65,  30, 130),
        "frost_mid":      (125, 75, 200),
        "frost_light":    (175, 130, 240),
        "frost_bright":   (215, 180, 255),
        "frost_hot":      (240, 220, 255),

        # Metal (spear/armor)
        "metal_darkest":  (18,  18,  25),
        "metal_dark":     (48,  55,  70),
        "metal_mid":      (105, 115, 135),
        "metal_light":    (170, 180, 200),
        "metal_shine":    (225, 230, 245),

        # Gold accents (small)
        "gold_mid":       (200, 165, 60),
        "gold_light":     (240, 210, 110),

        # Eyes
        "eye_dark":       (10,  30,  60),
        "eye_bright":     (140, 210, 255),
        "eye_hot":        (220, 240, 255),

        # Wyvern eye (orange/red - fierce)
        "wy_eye_dark":    (85,  25,  10),
        "wy_eye_bright":  (255, 130, 40),
        "wy_eye_hot":     (255, 210, 120),

        # Teeth
        "bone_dark":      (155, 145, 115),
        "bone_light":     (240, 230, 200),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (3,   5,  10),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_nyzrak._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_nyzrak.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_nyzrak._clamp(color)
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
        color = _NS_nyzrak._clamp(color)
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
        color = _NS_nyzrak._clamp(color)
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
        color = _NS_nyzrak._clamp(color)
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
        return int(x + 220 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Snowflake / ice crystal helpers
    # ---------------------------------------------------------------------------
    def _draw_snowflake(surface, cx, cy, size=3, alpha=255, rotate=0):
        """Snowflake - 6-arm star."""
        for i in range(6):
            angle = rotate + i * math.pi / 3
            ex = cx + int(math.cos(angle) * size)
            ey = cy + int(math.sin(angle) * size)
            _NS_nyzrak._aaline(surface, (*_NS_nyzrak.PALETTE["ice_hot"], alpha), (cx, cy), (ex, ey), 1)
            # Tick marks
            tick1 = angle + math.pi / 2
            tick2 = angle - math.pi / 2
            mx = cx + int(math.cos(angle) * (size - 1))
            my = cy + int(math.sin(angle) * (size - 1))
            _NS_nyzrak._aaline(surface, (*_NS_nyzrak.PALETTE["ice_bright"], alpha),
                    (mx, my),
                    (mx + int(math.cos(tick1) * 1), my + int(math.sin(tick1) * 1)), 1)
            _NS_nyzrak._aaline(surface, (*_NS_nyzrak.PALETTE["ice_bright"], alpha),
                    (mx, my),
                    (mx + int(math.cos(tick2) * 1), my + int(math.sin(tick2) * 1)), 1)
        _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_pure"], alpha), (cx, cy), 1)


    def _draw_crystal_spike(surface, cx, base_y, tip_y, width=4, alpha=255,
                             color_set="ice"):
        """Ice crystal spike growing upward."""
        if color_set == "ice":
            colors = ["ice_darkest", "ice_dark", "ice_mid", "ice_light", "ice_bright"]
        else:
            colors = ["frost_darkest", "frost_dark", "frost_mid", "frost_light", "frost_bright"]

        _NS_nyzrak._poly(surface, (*_NS_nyzrak.PALETTE["shadow_deep"], alpha), [
            (cx - width + 1, base_y + 1),
            (cx + width + 1, base_y + 1),
            (cx + 1, tip_y + 1),
        ])
        _NS_nyzrak._poly(surface, (*_NS_nyzrak.PALETTE[colors[0]], alpha), [
            (cx - width, base_y),
            (cx + width, base_y),
            (cx, tip_y),
        ])
        for i in range(1, 5):
            shrink = i * 0.18
            w = max(1, int(width * (1 - shrink)))
            _NS_nyzrak._poly(surface, (*_NS_nyzrak.PALETTE[colors[i]], alpha), [
                (cx - w, base_y - 1),
                (cx + w, base_y - 1),
                (cx, tip_y + int((base_y - tip_y) * shrink * 0.15)),
            ])
        _NS_nyzrak._aaline(surface, (*_NS_nyzrak.PALETTE["ice_hot"], alpha),
                (cx, base_y - 2), (cx, tip_y + 2), 1)
        _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_pure"], alpha), (cx, tip_y + 1), 1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM
    # ---------------------------------------------------------------------------
    class IceProjectile:
        """Ice shard/snowflake projectile for Nyzrak's ranged attack."""
        def __init__(self, sx, sy, tx, ty, speed=7.0):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.trail = []
            self.spin = 0.0
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.spin += 0.4
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
            # Trail with snowflakes
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(50 + i * 15)
                r = max(1, 4 - (len(self.trail) - i))
                _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_dark"], alpha), (tx, ty), r + 2)
                _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_light"], alpha), (tx, ty), r)
                _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_hot"], alpha // 2),
                          (tx, ty), max(1, r - 1))

            if self.alive:
                px, py = int(self.x), int(self.y)
                # Outer glow
                _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_dark"], 130), (px, py), 12)
                _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_mid"], 180), (px, py), 8)

                # Snowflake sprite spinning
                _NS_nyzrak._draw_snowflake(surface, px, py, 6, 255, rotate=self.spin)

                # Inner shard (diamond)
                dx = math.cos(self.angle)
                dy = math.sin(self.angle)
                perp_x = -dy
                perp_y = dx

                shard = [
                    (px + int(dx * 5), py + int(dy * 5)),
                    (px + int(perp_x * 2), py + int(perp_y * 2)),
                    (px - int(dx * 3), py - int(dy * 3)),
                    (px - int(perp_x * 2), py - int(perp_y * 2)),
                ]
                _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["ice_bright"], shard)
                _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["ice_pure"], (px, py), 2)


    class SplinterShard:
        """Splinter Blast (W) — small shard flying outward."""
        def __init__(self, x, y, dir_x, dir_y, speed=6.0, life=25):
            self.x = float(x)
            self.y = float(y)
            self.dir_x = dir_x
            self.dir_y = dir_y
            self.speed = speed
            self.life = life
            self.age = 0
            self.alive = True
            self.angle = math.atan2(dir_y, dir_x)
            self.trail = []

        def update(self):
            self.age += 1
            if self.age >= self.life:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 6:
                self.trail.pop(0)
            self.x += self.dir_x * self.speed
            self.y += self.dir_y * self.speed

        def draw(self, surface, phase):
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 20)
                _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_light"], alpha), (tx, ty), 2)
                _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_hot"], alpha), (tx, ty), 1)

            if self.alive:
                px, py = int(self.x), int(self.y)
                dx = self.dir_x
                dy = self.dir_y
                perp_x = -dy
                perp_y = dx

                # Long thin shard
                shard = [
                    (px + int(dx * 8), py + int(dy * 8)),
                    (px + int(perp_x * 2), py + int(perp_y * 2)),
                    (px - int(dx * 4), py - int(dy * 4)),
                    (px - int(perp_x * 2), py - int(perp_y * 2)),
                ]
                _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["shadow_deep"],
                      [(p[0] + 1, p[1] + 1) for p in shard])
                _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["ice_darkest"], shard)
                _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["ice_dark"], [
                    (px + int(dx * 7), py + int(dy * 7)),
                    (px + int(perp_x), py + int(perp_y)),
                    (px - int(dx * 3), py - int(dy * 3)),
                    (px - int(perp_x), py - int(perp_y)),
                ])
                _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["ice_bright"], [
                    (px + int(dx * 6), py + int(dy * 6)),
                    (px, py),
                    (px - int(dx * 2), py - int(dy * 2)),
                ])
                _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["ice_pure"],
                        (px + int(dx * 6), py + int(dy * 6)),
                        (px - int(dx * 2), py - int(dy * 2)), 1)


    class ArcticBurnBeam:
        """Q - Arctic Burn continuous purple frost beam."""
        def __init__(self, sx, sy, tx, ty, life=45):
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
            if t < 0.15:
                alpha_scale = t / 0.15
            elif t < 0.75:
                alpha_scale = 1.0
            else:
                alpha_scale = 1 - (t - 0.75) / 0.25

            dx = self.tx - self.sx
            dy = self.ty - self.sy
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 1:
                return
            dir_x = dx / dist
            dir_y = dy / dist
            perp_x = -dir_y
            perp_y = dir_x

            # Beam extends progressively at start
            beam_len = dist * min(1.0, t / 0.3)

            # Multi-layer purple frost beam
            for i in range(int(beam_len / 3)):
                t_pos = i / max(1, int(beam_len / 3))
                base_x = self.sx + dir_x * beam_len * t_pos
                base_y = self.sy + dir_y * beam_len * t_pos

                # Sinusoidal wave
                wave = math.sin(phase * 6 + t_pos * 12) * 5
                fx = int(base_x + perp_x * wave)
                fy = int(base_y + perp_y * wave)

                alpha = int(220 * alpha_scale)
                size = int(8 + math.sin(phase * 3 + t_pos * 10) * 3)

                _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["frost_darkest"], alpha), (fx, fy), size + 2)
                _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["frost_dark"], alpha), (fx, fy), size)
                _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["frost_mid"], alpha), (fx, fy), max(1, size - 2))
                _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["frost_light"], alpha), (fx, fy), max(1, size - 4))
                _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["frost_bright"], alpha), (fx, fy), max(1, size - 6))
                _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["frost_hot"], alpha), (fx, fy), max(1, size - 7))

            # Snowflakes along beam
            for i in range(6):
                t_pos = (phase * 0.4 + i * 0.17) % 1.0
                if t_pos > beam_len / dist:
                    continue
                sx = int(self.sx + dir_x * dist * t_pos)
                sy = int(self.sy + dir_y * dist * t_pos)
                _NS_nyzrak._draw_snowflake(surface, sx + int(perp_x * 8), sy + int(perp_y * 8),
                                2, int(230 * alpha_scale), rotate=phase * 2 + i)

            # Impact end burst
            if t > 0.3 and t < 0.85:
                impact_intensity = math.sin((t - 0.3) / 0.55 * math.pi)
                ex = int(self.sx + dir_x * beam_len)
                ey = int(self.sy + dir_y * beam_len)
                _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["frost_dark"], int(150 * impact_intensity)),
                          (ex, ey), int(20 * impact_intensity))
                _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["frost_bright"], int(200 * impact_intensity)),
                          (ex, ey), int(12 * impact_intensity))
                _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_pure"], int(255 * impact_intensity)),
                          (ex, ey), int(6 * impact_intensity))

                # Ice crystals bursting
                for i in range(6):
                    angle = i * math.pi / 3 + phase
                    spike_h = int(15 * impact_intensity)
                    cx = ex + int(math.cos(angle) * 15)
                    cy = ey + int(math.sin(angle) * 8)
                    _NS_nyzrak._draw_crystal_spike(surface, cx, cy, cy - spike_h, 2,
                                         int(230 * impact_intensity))


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_nyz_last_x"):
            boss._nyz_last_x = boss.x
            boss._nyz_last_y = boss.y
            return False
        dx = abs(boss.x - boss._nyz_last_x)
        dy = abs(boss.y - boss._nyz_last_y)
        boss._nyz_last_x = boss.x
        boss._nyz_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_nyz_prev_timer", 0))
        active = bool(getattr(boss, "_nyz_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._nyz_attack_active = True
            boss._nyz_attack_frame = 0
            active = True
        elif active:
            boss._nyz_attack_frame = int(getattr(boss, "_nyz_attack_frame", 0)) + 1
            if boss._nyz_attack_frame > cooldown:
                boss._nyz_attack_active = False
                boss._nyz_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._nyz_attack_active = False
            boss._nyz_attack_frame = 0
            active = False

        boss._nyz_prev_timer = timer
        boss._nyz_attack_progress = (
            min(1.0, getattr(boss, "_nyz_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_nyz_projectiles"):
            boss._nyz_projectiles = []
        if not hasattr(boss, "_nyz_shards"):
            boss._nyz_shards = []
        if not hasattr(boss, "_nyz_beams"):
            boss._nyz_beams = []

        for p in boss._nyz_projectiles:
            p.update()
            p.draw(surface, phase)
        boss._nyz_projectiles = [p for p in boss._nyz_projectiles
                                  if p.alive or p.age < 3]

        for s in boss._nyz_shards:
            s.update()
            s.draw(surface, phase)
        boss._nyz_shards = [s for s in boss._nyz_shards if s.alive]

        for b in boss._nyz_beams:
            b.update()
            b.draw(surface, phase)
        boss._nyz_beams = [b for b in boss._nyz_beams if b.alive]


    def _spawn_ice_projectile(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_nyz_projectiles"):
            boss._nyz_projectiles = []
        boss._nyz_projectiles.append(_NS_nyzrak.IceProjectile(sx, sy, tx, ty))


    def _spawn_splinter_burst(boss, x, y, count=8):
        if not hasattr(boss, "_nyz_shards"):
            boss._nyz_shards = []
        for i in range(count):
            angle = i * math.pi * 2 / count
            boss._nyz_shards.append(_NS_nyzrak.SplinterShard(
                x, y, math.cos(angle), math.sin(angle) * 0.7, speed=5.5, life=28
            ))


    def _spawn_arctic_burn(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_nyz_beams"):
            boss._nyz_beams = []
        boss._nyz_beams.append(_NS_nyzrak.ArcticBurnBeam(sx, sy, tx, ty))


    # ===================================================================
    # MAIN ENTRY
    # ===================================================================
    def draw_nyzrak(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_nyzrak._detect_moving(boss)
        _NS_nyzrak._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_nyz_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 45) - 15
        )

        # Background aura
        _NS_nyzrak._draw_frost_aura(surface, x, y, pulse, active_skill)
        _NS_nyzrak._draw_ground_frost(surface, x, y + 46, pulse, active_skill)

        # Ground skill effects
        if active_skill == "e":
            _NS_nyzrak._draw_winters_curse_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyzrak._draw_cold_embrace_ground(surface, boss, x, y, skill_timer, pulse)

        # Character
        if attacking:
            _NS_nyzrak._draw_nyz_attack(surface, boss, x, y)
        elif active_skill in ("q", "w"):
            _NS_nyzrak._draw_nyz_casting(surface, boss, x, y, active_skill, skill_timer)
        elif moving:
            _NS_nyzrak._draw_nyz_walk(surface, boss, x, y)
        else:
            _NS_nyzrak._draw_nyz_idle(surface, boss, x, y)

        # Skill spawn triggers
        _NS_nyzrak._handle_skill_projectiles(boss, x, y, active_skill, skill_timer)

        # Projectiles
        _NS_nyzrak._manage_projectiles(boss, surface, pulse)

        # Foreground skill effects
        if active_skill == "e":
            _NS_nyzrak._draw_winters_curse_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_nyzrak._draw_cold_embrace_foreground(surface, boss, x, y, skill_timer, pulse)


    def _handle_skill_projectiles(boss, x, y, active_skill, timer):
        tx, ty = _NS_nyzrak._target_position(boss, x, y)

        if active_skill == "q":
            duration = 60
            progress = max(0.0, min(1.0, 1 - timer / duration))
            if 0.35 < progress < 0.45 and not getattr(boss, "_nyz_q_spawned", False):
                _NS_nyzrak._spawn_arctic_burn(boss, x + 25 * boss.direction, y - 15, tx, ty)
                boss._nyz_q_spawned = True
            if progress > 0.7:
                boss._nyz_q_spawned = False

        elif active_skill == "w":
            duration = 55
            progress = max(0.0, min(1.0, 1 - timer / duration))
            if 0.35 < progress < 0.45 and not getattr(boss, "_nyz_w_spawned", False):
                # Burst of shards in cone direction
                sx = x + 25 * boss.direction
                sy = y - 10
                # Spawn 5 shards in a forward cone
                base_angle = math.atan2(ty - sy, (tx - sx) or 1)
                for i in range(5):
                    spread = (i - 2) * 0.25
                    a = base_angle + spread
                    if not hasattr(boss, "_nyz_shards"):
                        boss._nyz_shards = []
                    boss._nyz_shards.append(_NS_nyzrak.SplinterShard(
                        sx, sy, math.cos(a), math.sin(a), speed=6.0, life=35
                    ))
                boss._nyz_w_spawned = True
            if progress > 0.7:
                boss._nyz_w_spawned = False


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_nyz_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 3)
        _NS_nyzrak._draw_shadow(surface, x, y + 55)
        _NS_nyzrak._draw_frost_wisps(surface, x, y + 40, boss.pulse)
        _NS_nyzrak._draw_nyz_full(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_nyz_walk(surface, boss, x, y):
        phase = boss.pulse * 2.3
        bob = int(math.sin(phase * 1.2) * 4)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_nyzrak._draw_shadow(surface, x + sway, y + 55)
        _NS_nyzrak._draw_frost_wisps(surface, x + sway, y + 40, phase, trail=True,
                          facing=boss.direction)
        _NS_nyzrak._draw_nyz_full(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_nyz_attack(surface, boss, x, y):
        progress = getattr(boss, "_nyz_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        recoil = int(math.sin(progress * math.pi) * 3) * -boss.direction

        # Spawn ice projectile mid-attack
        if 0.35 < progress < 0.45 and not getattr(boss, "_nyz_atk_spawned", False):
            tx, ty = _NS_nyzrak._target_position(boss, x, y)
            # Fires from spear tip (above rider)
            sx = x + 20 * boss.direction
            sy = y - 30
            _NS_nyzrak._spawn_ice_projectile(boss, sx, sy, tx, ty)
            boss._nyz_atk_spawned = True
        if progress < 0.1 or progress > 0.9:
            boss._nyz_atk_spawned = False

        _NS_nyzrak._draw_shadow(surface, x + recoil, y + 55)
        _NS_nyzrak._draw_frost_wisps(surface, x + recoil, y + 40, boss.pulse, intense=True)
        _NS_nyzrak._draw_nyz_full(surface, x + recoil, y + bob, boss.direction, boss.pulse,
                       "attack", progress)
        _NS_nyzrak._draw_cast_flash(surface, x + recoil, y - 25, boss.direction, progress)


    def _draw_nyz_casting(surface, boss, x, y, skill, timer):
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_nyzrak._draw_shadow(surface, x, y + 55)
        _NS_nyzrak._draw_frost_wisps(surface, x, y + 40, boss.pulse, intense=True)
        _NS_nyzrak._draw_nyz_full(surface, x, y + bob, boss.direction, boss.pulse,
                       "cast_" + skill)


    # ===================================================================
    # FULL COMPOSITE - Wyvern + Rider
    # ===================================================================
    def _draw_nyz_full(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Back wings first
        _NS_nyzrak._draw_wyvern_wings_back(surface, cx, cy, facing, phase, action)

        # Wyvern tail (behind body)
        _NS_nyzrak._draw_wyvern_tail(surface, cx, cy + 8, facing, phase, action)

        # Wyvern body
        _NS_nyzrak._draw_wyvern_body(surface, cx, cy + 5, facing, phase)

        # Wyvern head
        _NS_nyzrak._draw_wyvern_head(surface, cx + 20 * facing, cy + 5, facing, phase, action)

        # Wyvern legs (small, front)
        _NS_nyzrak._draw_wyvern_legs(surface, cx, cy + 15, facing, phase, action)

        # RIDER on top
        _NS_nyzrak._draw_rider(surface, cx - 3 * facing, cy - 18, facing, phase, action,
                    attack_progress)

        # Front wings (overlap when needed)
        if action == "attack" or action.startswith("cast"):
            _NS_nyzrak._draw_wyvern_wing_front(surface, cx, cy, facing, phase)


    def _draw_wyvern_wings_back(surface, cx, cy, facing, phase, action):
        """Wyvern wings spread out behind (both sides)."""
        flap_speed = 2.5 if action == "walk" else 1.2
        flap = math.sin(phase * flap_speed) * 0.35

        for side in (-1, 1):
            wing_base_x = cx + side * 10
            wing_base_y = cy - 5

            # Wing extends outward and slightly up/back
            tip_x = cx + side * (36 + int(math.cos(flap) * 5))
            tip_y = cy - 18 + int(math.sin(flap) * 6)
            mid_x = cx + side * 28
            mid_y = cy - 8 + int(math.sin(flap) * 5)
            low_x = cx + side * 24
            low_y = cy + 10 + int(math.sin(flap) * 3)

            # Membrane
            wing_shape = [
                (wing_base_x, wing_base_y),
                (tip_x, tip_y),
                (cx + side * 32, cy - 6 + int(math.sin(flap) * 4)),
                (mid_x, mid_y),
                (cx + side * 30, cy + 3 + int(math.sin(flap) * 4)),
                (low_x, low_y),
                (cx + side * 6, cy + 6),
            ]

            _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["shadow_deep"],
                  [(p[0] + 2, p[1] + 2) for p in wing_shape])
            _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["wing_darkest"], wing_shape)
            # Inner brighter
            _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["wing_dark"], [
                (wing_base_x + side, wing_base_y + 1),
                (tip_x - side * 2, tip_y + 1),
                (mid_x - side, mid_y),
                (low_x - side, low_y - 1),
                (cx + side * 6, cy + 5),
            ])
            _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["wing_mid"], [
                (wing_base_x + side * 2, wing_base_y + 2),
                (cx + side * 24, mid_y + 1),
                (low_x - side * 2, low_y - 2),
                (cx + side * 7, cy + 4),
            ])

            # Wing bones
            _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["wing_darkest"],
                    (wing_base_x, wing_base_y), (tip_x, tip_y), 2)
            _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["wing_darkest"],
                    (wing_base_x, wing_base_y), (mid_x, mid_y), 2)
            _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["wing_darkest"],
                    (wing_base_x, wing_base_y), (low_x, low_y), 2)

            # Highlight on bones
            _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["wing_light"],
                    (wing_base_x + side, wing_base_y - 1),
                    (tip_x - side * 2, tip_y - 1), 1)

            # Claw at wing tip
            _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["bone_dark"], [
                (tip_x, tip_y),
                (tip_x + side * 3, tip_y - 2),
                (tip_x + side, tip_y + 1),
            ])
            _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["bone_light"],
                      (tip_x + side * 2, tip_y - 1), 1)


    def _draw_wyvern_wing_front(surface, cx, cy, facing, phase):
        """Highlight overlay on wings."""
        for side in (-1, 1):
            _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["wing_light"],
                    (cx + side * 12, cy - 2),
                    (cx + side * 28, cy - 10), 1)


    def _draw_wyvern_tail(surface, cx, cy, facing, phase, action):
        """Long curling wyvern tail."""
        tail_wave = math.sin(phase * 0.8) * 3
        # Tail curves back and slightly up
        segments = [
            (cx - facing * 14, cy + 2),
            (cx - facing * 22, cy + int(tail_wave)),
            (cx - facing * 30, cy - 3 + int(tail_wave * 1.5)),
            (cx - facing * 35, cy - 10 + int(tail_wave * 1.5)),
            (cx - facing * 36, cy - 18 + int(tail_wave)),
        ]

        # Draw tail as connected thick segments
        for i in range(len(segments) - 1):
            thickness = 5 - i
            x1, y1 = segments[i]
            x2, y2 = segments[i + 1]
            _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["shadow_deep"],
                    (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), thickness + 2)
            _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["wy_darkest"], (x1, y1), (x2, y2), thickness + 1)
            _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["wy_dark"], (x1, y1), (x2, y2), thickness)
            _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["wy_mid"], (x1, y1), (x2, y2), max(1, thickness - 2))
            _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["wy_light"], (x1 - 1, y1), (x2 - 1, y2), 1)

        # Tail fin at end
        tip_x, tip_y = segments[-1]
        fin_pts = [
            (tip_x, tip_y),
            (tip_x - facing * 4, tip_y - 8),
            (tip_x + facing * 2, tip_y - 4),
            (tip_x + facing * 5, tip_y - 6),
            (tip_x + facing * 2, tip_y + 2),
        ]
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["wy_darkest"], fin_pts)
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["wy_dark"], [
            (tip_x, tip_y - 1),
            (tip_x - facing * 3, tip_y - 7),
            (tip_x + facing * 1, tip_y - 4),
            (tip_x + facing * 4, tip_y - 5),
            (tip_x + facing * 1, tip_y + 1),
        ])
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["wy_mid"], [
            (tip_x, tip_y - 1),
            (tip_x - facing * 2, tip_y - 5),
            (tip_x + facing * 3, tip_y - 4),
        ])

        # Tail spikes along back
        for i, (sx, sy) in enumerate(segments[:-1]):
            _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["wy_darkest"], [
                (sx - 1, sy - 2),
                (sx + 1, sy - 2),
                (sx, sy - 5 - (i % 2)),
            ])
            _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["wy_mid"], [
                (sx, sy - 2),
                (sx + 1, sy - 2),
                (sx, sy - 4 - (i % 2)),
            ])


    def _draw_wyvern_body(surface, cx, cy, facing, phase):
        """Ice wyvern body — teal/cyan dragon."""
        # Body shadow
        _NS_nyzrak._ellipse(surface, _NS_nyzrak.PALETTE["shadow_deep"], (cx - 18, cy - 5, 36, 22))

        # Main body (elongated oval)
        _NS_nyzrak._ellipse(surface, _NS_nyzrak.PALETTE["wy_darkest"], (cx - 17, cy - 7, 34, 20))
        _NS_nyzrak._ellipse(surface, _NS_nyzrak.PALETTE["wy_dark"], (cx - 15, cy - 6, 30, 17))
        _NS_nyzrak._ellipse(surface, _NS_nyzrak.PALETTE["wy_mid"], (cx - 13, cy - 5, 26, 14))
        _NS_nyzrak._ellipse(surface, _NS_nyzrak.PALETTE["wy_light"], (cx - 10, cy - 6, 20, 8))

        # Belly (lighter underside)
        _NS_nyzrak._ellipse(surface, _NS_nyzrak.PALETTE["belly_dark"], (cx - 10, cy + 5, 20, 8))
        _NS_nyzrak._ellipse(surface, _NS_nyzrak.PALETTE["belly_mid"], (cx - 8, cy + 6, 16, 5))
        _NS_nyzrak._ellipse(surface, _NS_nyzrak.PALETTE["belly_light"], (cx - 5, cy + 6, 10, 3))

        # Belly scales lines
        for xoff in (-5, 0, 5):
            _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["belly_dark"],
                    (cx + xoff - 2, cy + 6), (cx + xoff + 2, cy + 6), 1)
            _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["belly_dark"],
                    (cx + xoff - 2, cy + 9), (cx + xoff + 2, cy + 9), 1)

        # Dorsal spikes
        for i, sx_off in enumerate((-10, -5, 0, 5, 10)):
            h = 5 + (i % 3)
            _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["wy_darkest"], [
                (cx + sx_off - 2, cy - 6),
                (cx + sx_off + 2, cy - 6),
                (cx + sx_off, cy - 6 - h),
            ])
            _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["wy_mid"], [
                (cx + sx_off, cy - 6),
                (cx + sx_off + 1, cy - 6),
                (cx + sx_off, cy - 4 - h),
            ])
            _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["wy_high"],
                      (cx + sx_off, cy - 5 - h), 1)

        # Ice frost patches on body
        for i in range(3):
            px = cx - 8 + i * 8
            py = cy - 2 + (i % 2) * 3
            _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["ice_bright"], (px, py), 2)
            _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["ice_hot"], (px, py), 1)


    def _draw_wyvern_head(surface, cx, cy, facing, phase, action):
        """Ice wyvern head - dragon-like with horns."""
        # Head shadow
        _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["shadow_deep"], (cx + 1, cy + 1), 9)

        # Head base
        _NS_nyzrak._ellipse(surface, _NS_nyzrak.PALETTE["wy_darkest"], (cx - 8, cy - 6, 16, 13))
        _NS_nyzrak._ellipse(surface, _NS_nyzrak.PALETTE["wy_dark"], (cx - 7, cy - 5, 14, 11))
        _NS_nyzrak._ellipse(surface, _NS_nyzrak.PALETTE["wy_mid"], (cx - 6, cy - 4, 12, 8))
        _NS_nyzrak._ellipse(surface, _NS_nyzrak.PALETTE["wy_light"], (cx - 5, cy - 4, 8, 4))

        # Snout (extending forward)
        snout = [
            (cx + facing * 1, cy - 2),
            (cx + facing * 10, cy - 3),
            (cx + facing * 13, cy + 1),
            (cx + facing * 10, cy + 4),
            (cx + facing * 1, cy + 4),
        ]
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["shadow_deep"], [(p[0] + 1, p[1] + 1) for p in snout])
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["wy_darkest"], snout)
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["wy_dark"], [
            (cx + facing * 2, cy - 1),
            (cx + facing * 9, cy - 2),
            (cx + facing * 12, cy + 1),
            (cx + facing * 9, cy + 3),
            (cx + facing * 2, cy + 3),
        ])
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["wy_mid"], [
            (cx + facing * 3, cy),
            (cx + facing * 8, cy - 1),
            (cx + facing * 10, cy + 1),
            (cx + facing * 8, cy + 2),
        ])

        # Open mouth (fierce)
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["shadow_deep"], [
            (cx + facing * 6, cy + 1),
            (cx + facing * 13, cy + 1),
            (cx + facing * 12, cy + 4),
            (cx + facing * 6, cy + 3),
        ])

        # Fangs
        for tooth_off in (7, 10):
            _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["bone_light"], [
                (cx + facing * tooth_off, cy + 1),
                (cx + facing * tooth_off + facing, cy + 4),
                (cx + facing * (tooth_off + 1), cy + 1),
            ])
        # Lower fang
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["bone_light"], [
            (cx + facing * 8, cy + 4),
            (cx + facing * 8 + facing, cy + 1),
            (cx + facing * 9, cy + 4),
        ])

        # Cold breath particles from mouth
        for i in range(3):
            px = cx + facing * (14 + i * 3)
            py = cy + 1 + int(math.sin(phase * 2 + i) * 2)
            alpha = 200 - i * 50
            _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_light"], alpha), (px, py), 3 - i)
            _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_hot"], alpha), (px, py), max(1, 2 - i))

        # Nostril
        _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["shadow_deep"], (cx + facing * 10, cy - 1), 1)

        # Fierce orange eye
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["shadow_deep"], (cx + facing * 3, cy - 3), 2)
        _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["wy_eye_dark"], (cx + facing * 3, cy - 3), 2)
        _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["wy_eye_bright"], (cx + facing * 3, cy - 3),
                  max(1, int(2 * eye_pulse)))
        _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["wy_eye_hot"], (cx + facing * 3, cy - 3), 1)

        # Horns on top (2 curved horns)
        for side_off in (-2, 2):
            hb_x = cx + side_off
            hb_y = cy - 5
            # Curved horn
            _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["shadow_deep"], [
                (hb_x - 1 + 1, hb_y + 1),
                (hb_x + 2 + 1, hb_y - 8 + 1),
                (hb_x - side_off + 1, hb_y - 10 + 1),
                (hb_x - side_off - 1 + 1, hb_y - 6 + 1),
            ])
            _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["bone_dark"], [
                (hb_x - 1, hb_y),
                (hb_x + 2, hb_y - 8),
                (hb_x - side_off, hb_y - 10),
                (hb_x - side_off - 1, hb_y - 6),
            ])
            _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["bone_light"], [
                (hb_x, hb_y),
                (hb_x + 1, hb_y - 7),
                (hb_x - side_off, hb_y - 9),
            ])
            # Tip
            _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["ice_hot"], (hb_x - side_off, hb_y - 10), 1)

        # Ear-like fin
        for side_off in (-6, 6):
            _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["wy_darkest"], [
                (cx + side_off, cy - 4),
                (cx + side_off + (1 if side_off > 0 else -1) * 2, cy - 8),
                (cx + side_off + (1 if side_off > 0 else -1) * 3, cy - 3),
            ])
            _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["wy_dark"], [
                (cx + side_off, cy - 4),
                (cx + side_off + (1 if side_off > 0 else -1), cy - 7),
                (cx + side_off + (1 if side_off > 0 else -1) * 2, cy - 3),
            ])


    def _draw_wyvern_legs(surface, cx, cy, facing, phase, action):
        """Wyvern's small hind legs, drawn but wyvern is mostly floating."""
        walk_phase = phase * 3 if action == "walk" else 0
        for side_off in (-9, 9):
            leg_lift = int(math.sin(walk_phase + (0 if side_off > 0 else math.pi)) * 2)
            lx = cx + side_off
            ly = cy - leg_lift

            # Upper leg
            _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["shadow_deep"], (lx + 1, ly + 1), (lx + 1, ly + 6), 5)
            _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["wy_darkest"], (lx, ly), (lx, ly + 5), 4)
            _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["wy_dark"], (lx, ly), (lx, ly + 5), 3)
            _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["wy_mid"], (lx, ly), (lx, ly + 4), 1)

            # Claws
            for c in (-1, 0, 1):
                _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["bone_dark"], [
                    (lx + c - 1, ly + 6),
                    (lx + c + 1, ly + 6),
                    (lx + c, ly + 9),
                ])
                _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["bone_light"], [
                    (lx + c, ly + 6),
                    (lx + c + 1, ly + 6),
                    (lx + c, ly + 8),
                ])


    def _draw_rider(surface, cx, cy, facing, phase, action, attack_progress):
        """Female rider in blue hooded cloak with fur trim, holding ice spear."""
        sway = int(math.sin(phase * 0.7) * 1)
        if action == "walk":
            sway += int(math.sin(phase * 2) * 1)

        # Cloak/robe lower (sits on wyvern back)
        _NS_nyzrak._draw_cloak_lower(surface, cx + sway, cy + 4, facing, phase)

        # Body (torso)
        _NS_nyzrak._draw_rider_torso(surface, cx + sway, cy, facing, phase)

        # Arms + spear
        if action == "attack":
            _NS_nyzrak._draw_rider_attack_arms(surface, cx + sway, cy, facing, phase, attack_progress)
        elif action.startswith("cast"):
            _NS_nyzrak._draw_rider_cast_arms(surface, cx + sway, cy, facing, phase, action)
        else:
            _NS_nyzrak._draw_rider_idle_arms(surface, cx + sway, cy, facing, phase)

        # Head with hood
        _NS_nyzrak._draw_rider_head(surface, cx + sway, cy - 8, facing, phase)


    def _draw_cloak_lower(surface, cx, cy, facing, phase):
        """Lower cloak spread over wyvern's back."""
        sway = int(math.sin(phase * 0.6) * 1)

        # Base cloak spreading down and out
        cloak_pts = [
            (cx - 10, cy - 2),
            (cx + 10, cy - 2),
            (cx + 14, cy + 8 + sway),
            (cx + 10, cy + 14),
            (cx + 3, cy + 16),
            (cx - 3, cy + 16),
            (cx - 10, cy + 14),
            (cx - 14, cy + 8 + sway),
        ]
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["shadow_deep"], [(p[0] + 1, p[1] + 1) for p in cloak_pts])
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["robe_darkest"], cloak_pts)
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["robe_dark"], [
            (cx - 9, cy - 1),
            (cx + 9, cy - 1),
            (cx + 12, cy + 7 + sway),
            (cx + 8, cy + 12),
            (cx - 8, cy + 12),
            (cx - 12, cy + 7 + sway),
        ])
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["robe_mid"], [
            (cx - 7, cy),
            (cx + 7, cy),
            (cx + 9, cy + 6 + sway),
            (cx + 5, cy + 10),
            (cx - 5, cy + 10),
            (cx - 9, cy + 6 + sway),
        ])

        # Fur trim at bottom
        for xoff in range(-11, 12, 3):
            _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["fur_dark"], (cx + xoff, cy + 14), 2)
            _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["fur_mid"], (cx + xoff, cy + 13), 2)
            _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["fur_light"], (cx + xoff - 1, cy + 12), 1)


    def _draw_rider_torso(surface, cx, cy, facing, phase):
        """Rider's torso in robe."""
        # Shadow
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["shadow_deep"], [
            (cx - 7 + 1, cy - 5 + 1), (cx + 7 + 1, cy - 5 + 1),
            (cx + 6 + 1, cy + 6 + 1), (cx - 6 + 1, cy + 6 + 1),
        ])

        # Torso base
        torso = [
            (cx - 7, cy - 5), (cx + 7, cy - 5),
            (cx + 6, cy + 6), (cx - 6, cy + 6),
        ]
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["robe_darkest"], torso)
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["robe_dark"], [
            (cx - 6, cy - 4), (cx + 6, cy - 4),
            (cx + 5, cy + 5), (cx - 5, cy + 5),
        ])
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["robe_mid"], [
            (cx - 4, cy - 3), (cx + 4, cy - 3),
            (cx + 3, cy + 4), (cx - 3, cy + 4),
        ])

        # Fur trim collar (V-neck)
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["fur_dark"], [
            (cx - 6, cy - 5), (cx + 6, cy - 5),
            (cx + 4, cy - 3), (cx - 4, cy - 3),
        ])
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["fur_mid"], [
            (cx - 5, cy - 5), (cx + 5, cy - 5),
            (cx + 3, cy - 4), (cx - 3, cy - 4),
        ])

        # Belt with ice gem
        _NS_nyzrak._rect(surface, _NS_nyzrak.PALETTE["metal_darkest"], (cx - 6, cy + 2, 12, 3))
        _NS_nyzrak._rect(surface, _NS_nyzrak.PALETTE["metal_dark"], (cx - 5, cy + 2, 10, 2))
        _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["ice_dark"], (cx, cy + 3), 2)
        _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["ice_bright"], (cx, cy + 3), 1)

        # V-decoration on chest
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["ice_bright"], (cx - 3, cy - 2), (cx, cy + 1), 1)
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["ice_bright"], (cx + 3, cy - 2), (cx, cy + 1), 1)


    def _draw_rider_idle_arms(surface, cx, cy, facing, phase):
        """One arm holds spear, other rests on wyvern."""
        sway = math.sin(phase * 0.7) * 1

        # Right arm - holds spear high (back arm)
        spear_side = facing  # spear held on facing side
        sh_x = cx + spear_side * 6
        sh_y = cy - 3
        # Elbow raised
        elbow_x = sh_x + spear_side * 3
        elbow_y = cy - 8
        hand_x = elbow_x + spear_side * 2
        hand_y = cy - 12

        _NS_nyzrak._draw_rider_arm(surface, sh_x, sh_y, elbow_x, elbow_y)
        _NS_nyzrak._draw_rider_arm(surface, elbow_x, elbow_y, hand_x, hand_y)
        _NS_nyzrak._draw_rider_hand(surface, hand_x, hand_y)

        # Ice spear held vertically
        _NS_nyzrak._draw_ice_spear_vertical(surface, hand_x, hand_y, spear_side, phase)

        # Front arm - rests down / on wyvern
        other_side = -facing
        sh_x2 = cx + other_side * 6
        sh_y2 = cy - 3
        hand_x2 = sh_x2 + other_side * 4
        hand_y2 = cy + 4 + int(sway)
        _NS_nyzrak._draw_rider_arm(surface, sh_x2, sh_y2, hand_x2, hand_y2)
        _NS_nyzrak._draw_rider_hand(surface, hand_x2, hand_y2)


    def _draw_rider_cast_arms(surface, cx, cy, facing, phase, action):
        """Cast pose - spear extended forward."""
        # Back arm - holds spear
        spear_side = facing
        sh_x = cx + spear_side * 6
        sh_y = cy - 3
        elbow_x = sh_x + spear_side * 5
        elbow_y = cy - 5
        hand_x = elbow_x + spear_side * 5
        hand_y = cy - 7

        _NS_nyzrak._draw_rider_arm(surface, sh_x, sh_y, elbow_x, elbow_y)
        _NS_nyzrak._draw_rider_arm(surface, elbow_x, elbow_y, hand_x, hand_y)
        _NS_nyzrak._draw_rider_hand(surface, hand_x, hand_y)

        # Ice spear extended forward
        _NS_nyzrak._draw_ice_spear_forward(surface, hand_x, hand_y, facing, phase)

        # Front arm - forward too, gathering energy
        other_side = -facing
        sh_x2 = cx + other_side * 6
        sh_y2 = cy - 3
        elbow_x2 = sh_x2 + facing * 3
        elbow_y2 = cy - 3
        hand_x2 = elbow_x2 + facing * 6
        hand_y2 = cy - 5

        _NS_nyzrak._draw_rider_arm(surface, sh_x2, sh_y2, elbow_x2, elbow_y2)
        _NS_nyzrak._draw_rider_arm(surface, elbow_x2, elbow_y2, hand_x2, hand_y2)
        _NS_nyzrak._draw_rider_hand(surface, hand_x2, hand_y2)

        # Casting energy
        pulse = math.sin(phase * 4) * 0.3 + 0.7
        r = int(5 * pulse)
        if action == "cast_q":
            color_dark = _NS_nyzrak.PALETTE["frost_dark"]
            color_bright = _NS_nyzrak.PALETTE["frost_bright"]
            color_hot = _NS_nyzrak.PALETTE["frost_hot"]
        else:
            color_dark = _NS_nyzrak.PALETTE["ice_dark"]
            color_bright = _NS_nyzrak.PALETTE["ice_bright"]
            color_hot = _NS_nyzrak.PALETTE["ice_hot"]
        _NS_nyzrak._aacircle(surface, (*color_dark, 150), (hand_x2, hand_y2), r + 4)
        _NS_nyzrak._aacircle(surface, color_bright, (hand_x2, hand_y2), r)
        _NS_nyzrak._aacircle(surface, color_hot, (hand_x2, hand_y2), max(1, r - 2))
        _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["ice_pure"], (hand_x2, hand_y2), max(1, r - 3))


    def _draw_rider_attack_arms(surface, cx, cy, facing, phase, progress):
        """Attack pose - spear thrust forward to fire projectile."""
        spear_side = facing

        # Wind-up then thrust
        if progress < 0.3:
            t = progress / 0.3
            angle = -1.2 - 0.3 * t
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            angle = -1.5 + 2.0 * t
        else:
            t = (progress - 0.5) / 0.5
            angle = 0.5 - 0.3 * t

        sh_x = cx + spear_side * 6
        sh_y = cy - 3

        arm_len = 10
        hand_x = sh_x + int(math.cos(angle) * arm_len) * facing
        hand_y = sh_y + int(math.sin(angle) * arm_len)
        elbow_x = sh_x + int(math.cos(angle) * arm_len * 0.55) * facing
        elbow_y = sh_y + int(math.sin(angle) * arm_len * 0.55)

        _NS_nyzrak._draw_rider_arm(surface, sh_x, sh_y, elbow_x, elbow_y)
        _NS_nyzrak._draw_rider_arm(surface, elbow_x, elbow_y, hand_x, hand_y)
        _NS_nyzrak._draw_rider_hand(surface, hand_x, hand_y)

        # Spear angled
        spear_angle = angle
        _NS_nyzrak._draw_ice_spear_angled(surface, hand_x, hand_y, facing, spear_angle)

        # Other arm rests
        other_side = -facing
        sh_x2 = cx + other_side * 6
        sh_y2 = cy - 3
        hand_x2 = sh_x2 + other_side * 3
        hand_y2 = cy + 4
        _NS_nyzrak._draw_rider_arm(surface, sh_x2, sh_y2, hand_x2, hand_y2)
        _NS_nyzrak._draw_rider_hand(surface, hand_x2, hand_y2)


    def _draw_rider_arm(surface, x1, y1, x2, y2):
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["shadow_deep"], (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 5)
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["robe_darkest"], (x1, y1), (x2, y2), 4)
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["robe_dark"], (x1, y1), (x2, y2), 3)
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["robe_mid"], (x1, y1), (x2, y2), 1)


    def _draw_rider_hand(surface, x, y):
        _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["shadow_deep"], (x + 1, y + 1), 3)
        _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["skin_dark"], (x, y), 2)
        _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["skin_mid"], (x - 1, y - 1), 2)
        _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["skin_light"], (x - 1, y - 1), 1)


    def _draw_rider_head(surface, cx, cy, facing, phase):
        """Female rider head with hood + fur trim."""
        # Hood back (drawn wider, behind head)
        hood_back = [
            (cx - 9, cy + 2),
            (cx - 10, cy - 5),
            (cx - 6, cy - 11),
            (cx, cy - 12),
            (cx + 6, cy - 11),
            (cx + 10, cy - 5),
            (cx + 9, cy + 2),
        ]
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["shadow_deep"], [(p[0] + 2, p[1] + 2) for p in hood_back])
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["robe_darkest"], hood_back)
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["robe_dark"], [
            (cx - 8, cy + 1),
            (cx - 9, cy - 5),
            (cx - 5, cy - 10),
            (cx, cy - 11),
            (cx + 5, cy - 10),
            (cx + 9, cy - 5),
            (cx + 8, cy + 1),
        ])

        # Fur trim around hood opening
        for i, xoff in enumerate([-7, -5, -3, 0, 3, 5, 7]):
            yoff = -8 if i in (2, 3, 4) else -6
            yoff += (i % 2)
            _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["fur_dark"], (cx + xoff, cy + yoff), 2)
            _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["fur_mid"], (cx + xoff, cy + yoff), 2)
            _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["fur_light"], (cx + xoff - 1, cy + yoff - 1), 1)

        # Face (inside hood shadow)
        face_pts = [
            (cx - 5, cy - 4),
            (cx + 5, cy - 4),
            (cx + 4, cy + 4),
            (cx, cy + 5),
            (cx - 4, cy + 4),
        ]
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["skin_dark"], face_pts)
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["skin_mid"], [
            (cx - 4, cy - 3),
            (cx + 4, cy - 3),
            (cx + 3, cy + 3),
            (cx, cy + 4),
            (cx - 3, cy + 3),
        ])
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["skin_light"], [
            (cx - 3, cy - 2),
            (cx + 3, cy - 2),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2),
        ])

        # Hair strands visible on sides / front
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["hair_dark"], [
            (cx - 5, cy - 4),
            (cx - 3, cy - 2),
            (cx - 3, cy + 1),
            (cx - 5, cy - 1),
        ])
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["hair_mid"], [
            (cx - 4, cy - 3),
            (cx - 3, cy - 2),
            (cx - 3, cy + 1),
            (cx - 4, cy - 1),
        ])
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["hair_dark"], [
            (cx + 3, cy - 2),
            (cx + 5, cy - 4),
            (cx + 5, cy - 1),
            (cx + 3, cy + 1),
        ])
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["hair_mid"], [
            (cx + 3, cy - 2),
            (cx + 4, cy - 3),
            (cx + 4, cy - 1),
            (cx + 3, cy + 1),
        ])
        # Hair light
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["hair_light"], (cx - 4, cy - 3), (cx - 4, cy), 1)
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["hair_light"], (cx + 4, cy - 3), (cx + 4, cy), 1)

        # Icy blue eyes
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy - 1
            _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["shadow_deep"], (ex, ey), 1)
            _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["eye_dark"], (ex, ey), 1)
            _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["eye_bright"], (ex, ey), 1)

        # Small mouth
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["skin_dark"], (cx - 1, cy + 2), (cx + 1, cy + 2), 1)

        # Snowflake earring or decoration on hood
        _NS_nyzrak._draw_snowflake(surface, cx - 8, cy - 3, 2, 220, rotate=phase)
        _NS_nyzrak._draw_snowflake(surface, cx + 8, cy - 3, 2, 220, rotate=phase + 1)


    def _draw_ice_spear_vertical(surface, hx, hy, side, phase):
        """Spear held vertical, tip pointing up."""
        # Handle extends up from hand
        top_x = hx
        top_y = hy - 20
        bottom_x = hx
        bottom_y = hy + 8

        # Handle shaft
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["shadow_deep"],
                (top_x + 1, top_y + 1), (bottom_x + 1, bottom_y + 1), 3)
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["metal_darkest"],
                (top_x, top_y), (bottom_x, bottom_y), 3)
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["metal_dark"],
                (top_x, top_y), (bottom_x, bottom_y), 2)
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["metal_light"],
                (top_x - 1, top_y), (bottom_x - 1, bottom_y), 1)

        # Gold rings on handle
        for ry in (hy - 12, hy - 4):
            _NS_nyzrak._rect(surface, _NS_nyzrak.PALETTE["gold_mid"], (hx - 2, ry, 4, 2))
            _NS_nyzrak._rect(surface, _NS_nyzrak.PALETTE["gold_light"], (hx - 2, ry, 4, 1))

        # ICE CRYSTAL BLADE at top
        tip_y = top_y - 12
        spear_head = [
            (top_x, top_y - 1),
            (top_x - 4, top_y - 5),
            (top_x - 3, top_y - 10),
            (top_x, tip_y),
            (top_x + 3, top_y - 10),
            (top_x + 4, top_y - 5),
        ]
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["shadow_deep"], [(p[0] + 1, p[1] + 1) for p in spear_head])
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["ice_darkest"], spear_head)
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["ice_dark"], [
            (top_x, top_y - 1),
            (top_x - 3, top_y - 5),
            (top_x - 2, top_y - 9),
            (top_x, tip_y + 1),
            (top_x + 2, top_y - 9),
            (top_x + 3, top_y - 5),
        ])
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["ice_mid"], [
            (top_x, top_y - 1),
            (top_x - 2, top_y - 5),
            (top_x - 1, top_y - 8),
            (top_x, tip_y + 2),
            (top_x + 1, top_y - 8),
            (top_x + 2, top_y - 5),
        ])
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["ice_bright"], (top_x, top_y - 1), (top_x, tip_y + 2), 1)
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["ice_hot"], (top_x, top_y - 4), (top_x, tip_y + 3), 1)
        _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["ice_pure"], (top_x, tip_y + 1), 1)

        # Small blade glow
        _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_bright"], 150), (top_x, top_y - 5), 5)
        _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_hot"], 200), (top_x, top_y - 5), 2)


    def _draw_ice_spear_forward(surface, hx, hy, facing, phase):
        """Spear extended forward."""
        tip_x = hx + facing * 22
        tip_y = hy

        # Handle
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["shadow_deep"], (hx + 1, hy + 1),
                (tip_x + 1, tip_y + 1), 3)
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["metal_darkest"], (hx, hy), (tip_x, tip_y), 3)
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["metal_dark"], (hx, hy), (tip_x, tip_y), 2)
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["metal_light"], (hx, hy - 1), (tip_x, tip_y - 1), 1)

        # Gold rings
        for t in (0.3, 0.7):
            rx = hx + int((tip_x - hx) * t)
            _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["gold_mid"], (rx, hy), 2)

        # Ice crystal blade at tip (perpendicular to handle)
        _NS_nyzrak._draw_ice_spear_head(surface, tip_x, tip_y, facing, phase)


    def _draw_ice_spear_angled(surface, hx, hy, facing, angle):
        """Spear at specific angle."""
        spear_len = 22
        dx = math.cos(angle) * facing
        dy = math.sin(angle)
        tip_x = hx + int(dx * spear_len)
        tip_y = hy + int(dy * spear_len)

        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["shadow_deep"], (hx + 1, hy + 1),
                (tip_x + 1, tip_y + 1), 3)
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["metal_darkest"], (hx, hy), (tip_x, tip_y), 3)
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["metal_dark"], (hx, hy), (tip_x, tip_y), 2)

        # Gold rings
        for t in (0.3, 0.7):
            rx = hx + int(dx * spear_len * t)
            ry = hy + int(dy * spear_len * t)
            _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["gold_mid"], (rx, ry), 2)

        # Ice blade at tip
        _NS_nyzrak._draw_ice_spear_head(surface, tip_x, tip_y, facing, 0)


    def _draw_ice_spear_head(surface, tip_x, tip_y, facing, phase):
        """Ice crystal spear head - diamond shape at tip."""
        # Diamond
        blade_pts = [
            (tip_x + facing * 8, tip_y),
            (tip_x + facing * 3, tip_y - 4),
            (tip_x - facing * 2, tip_y),
            (tip_x + facing * 3, tip_y + 4),
        ]
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["shadow_deep"], [(p[0] + 1, p[1] + 1) for p in blade_pts])
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["ice_darkest"], blade_pts)
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["ice_dark"], [
            (tip_x + facing * 7, tip_y),
            (tip_x + facing * 3, tip_y - 3),
            (tip_x - facing * 1, tip_y),
            (tip_x + facing * 3, tip_y + 3),
        ])
        _NS_nyzrak._poly(surface, _NS_nyzrak.PALETTE["ice_mid"], [
            (tip_x + facing * 6, tip_y),
            (tip_x + facing * 3, tip_y - 2),
            (tip_x, tip_y),
            (tip_x + facing * 3, tip_y + 2),
        ])
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["ice_bright"],
                (tip_x + facing * 6, tip_y), (tip_x, tip_y), 1)
        _NS_nyzrak._aaline(surface, _NS_nyzrak.PALETTE["ice_hot"],
                (tip_x + facing * 5, tip_y), (tip_x + facing * 1, tip_y), 1)
        _NS_nyzrak._aacircle(surface, _NS_nyzrak.PALETTE["ice_pure"], (tip_x + facing * 3, tip_y), 1)

        # Glow
        _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_bright"], 130), (tip_x + facing * 3, tip_y), 6)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_frost_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Frost wisps beneath wyvern."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((150, 45), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(36, 3, -4):
            alpha = int((36 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_nyzrak.PALETTE["ice_darkest"], min(255, alpha)),
                    (75 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 75, cy - 11))

        # Rising frost wisps
        for i, offset in enumerate((-24, -8, 8, 24)):
            t = (phase * 0.55 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 28)
            alpha = max(0, min(255, int(220 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_dark"], alpha), (sx, sy), 5)
            _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_mid"], alpha), (sx, sy - 2), 3)
            _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_bright"], alpha), (sx, sy - 3), 2)
            _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_hot"], alpha), (sx, sy - 3), 1)

        # Snowflakes drifting
        for i in range(5):
            t = (phase * 0.4 + i * 0.2) % 1.0
            angle = phase * 0.5 + i * math.pi * 2 / 5
            r = 24 + int(math.sin(phase + i * 1.3) * 6)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 9) - int(t * 8)
            alpha = int(230 * (1 - t * 0.5) * strength)
            _NS_nyzrak._draw_snowflake(surface, sx, sy, 2, max(0, min(255, alpha)),
                             rotate=phase + i)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = max(0, 140 - i * 25)
                _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_mid"], alpha),
                          (sx, sy), max(2, 5 - i))
                _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_light"], alpha),
                          (sx, sy), max(1, 3 - i))


    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((120, 22), pygame.SRCALPHA)
        for radius in range(11, 0, -1):
            alpha = max(0, (11 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (11 - radius, 11 - radius, 98 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_nyzrak.PALETTE["ice_dark"], 80), (10, 5, 100, 12))
        surface.blit(shadow, (x - 60, y - 11))


    def _draw_frost_aura(surface, x, y, phase, active_skill):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.6 if active_skill in ("q", "w", "e", "r") else 1.0
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        color = _NS_nyzrak.PALETTE["frost_darkest"] if active_skill == "q" else _NS_nyzrak.PALETTE["ice_darkest"]
        for radius in range(90, 5, -4):
            alpha = int((90 - radius) * 1.2 * pulse * strength)
            if alpha > 0:
                _NS_nyzrak._aacircle(aura, (*color, min(255, alpha)),
                          (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))


    def _draw_ground_frost(surface, x, y, phase, active_skill):
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((140, 46), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_nyzrak.PALETTE["ice_dark"], 160),
                            (5, 10, 130, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_nyzrak.PALETTE["ice_mid"], 190),
                            (20, 14, 100, 18), 2)

        for i in range(10):
            angle = phase * 0.15 + i * math.pi / 5
            x1 = 70 + int(math.cos(angle) * 32)
            y1 = 23 + int(math.sin(angle) * 7)
            x2 = 70 + int(math.cos(angle) * 60)
            y2 = 23 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_nyzrak.PALETTE["ice_bright"], 180),
                             (x1, y1), (x2, y2), 1)

        if active_skill:
            pygame.draw.ellipse(ring, (*_NS_nyzrak.PALETTE["ice_hot"], int(80 * pulse)),
                                (15, 8, 110, 30), 1)

        for i in range(6):
            angle = phase * 0.3 + i * math.pi / 3
            sx = 70 + int(math.cos(angle) * 50)
            sy = 23 + int(math.sin(angle) * 8)
            _NS_nyzrak._draw_snowflake(ring, sx, sy, 2, 200, rotate=phase * 2 + i)

        surface.blit(ring, (x - 70, y - 23))


    def _draw_cast_flash(surface, x, y, facing, progress):
        if progress < 0.25 or progress > 0.6:
            return
        t = (progress - 0.25) / 0.35
        intensity = math.sin(t * math.pi)
        fx = x + 24 * facing
        fy = y - 5
        alpha = int(220 * intensity)
        radius = int(6 + intensity * 14)

        _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_dark"], alpha // 2), (fx, fy), radius + 6)
        _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_mid"], alpha), (fx, fy), radius + 2)
        _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_bright"], alpha), (fx, fy), radius)
        _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_hot"], alpha), (fx, fy), max(1, radius - 3))
        _NS_nyzrak._aacircle(surface, (*_NS_nyzrak.PALETTE["ice_pure"], min(255, alpha)),
                  (fx, fy), max(1, radius - 5))

        for i in range(5):
            angle = i * math.pi * 2 / 5 + progress * 3
            ex = fx + int(math.cos(angle) * radius * 1.4)
            ey = fy + int(math.sin(angle) * radius * 1.4)
            _NS_nyzrak._draw_snowflake(surface, ex, ey, 2, alpha, rotate=progress * 5)


    # ===================================================================
    # SKILL E: WINTER'S CURSE (freeze target in ice tomb)
    # ===================================================================
    def _draw_winters_curse_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_nyzrak._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        radius = int(25 + progress * 12)
        _NS_nyzrak._ellipse(surface, (*_NS_nyzrak.PALETTE["ice_dark"], int(180 * pulse)),
                 (tx - radius, ty - radius // 3, radius * 2, radius // 1.5), 3)
        _NS_nyzrak._ellipse(surface, (*_NS_nyzrak.PALETTE["ice_mid"], int(150 * pulse)),
                 (tx - radius + 4, ty - radius // 3 + 2,
                  radius * 2 - 8, radius // 1.5 - 4), 2)


    def _draw_winters_curse_foreground(surface, boss, x, y, timer, phase):
        """Ice tomb / prison around target."""
        tx, ty = _NS_nyzrak._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.15:
            # Charging - snowflakes converging
            for i in range(12):
                angle = phase * 2 + i * math.pi / 6
                r = 50 * (1 - progress / 0.15)
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.5)
                _NS_nyzrak._draw_snowflake(surface, sx, sy, 3, 200, rotate=phase * 4)
            return

        # Build ice tomb around target
        form_t = min(1.0, (progress - 0.15) / 0.3)

        # Ice tomb base (rounded rectangle - taller than wide)
        tomb_w = int(30 * form_t)
        tomb_h = int(45 * form_t)

        if tomb_h <= 0:
            return

        # Outer tomb shape
        tomb_pts = [
            (tx - tomb_w, ty + 5),
            (tx - tomb_w, ty - tomb_h + 8),
            (tx - tomb_w // 2, ty - tomb_h),
            (tx + tomb_w // 2, ty - tomb_h),
            (tx + tomb_w, ty - tomb_h + 8),
            (tx + tomb_w, ty + 5),
        ]
        _NS_nyzrak._poly(surface, (*_NS_nyzrak.PALETTE["ice_darkest"], 200), tomb_pts)
        _NS_nyzrak._poly(surface, (*_NS_nyzrak.PALETTE["ice_dark"], 180), [
            (tx - tomb_w + 2, ty + 4),
            (tx - tomb_w + 2, ty - tomb_h + 10),
            (tx - tomb_w // 2, ty - tomb_h + 2),
            (tx + tomb_w // 2, ty - tomb_h + 2),
            (tx + tomb_w - 2, ty - tomb_h + 10),
            (tx + tomb_w - 2, ty + 4),
        ])
        _NS_nyzrak._poly(surface, (*_NS_nyzrak.PALETTE["ice_mid"], 160), [
            (tx - tomb_w + 4, ty + 3),
            (tx - tomb_w + 4, ty - tomb_h + 12),
            (tx - tomb_w // 2 + 2, ty - tomb_h + 4),
            (tx + tomb_w // 2 - 2, ty - tomb_h + 4),
            (tx + tomb_w - 4, ty - tomb_h + 12),
            (tx + tomb_w - 4, ty + 3),
        ])

        # Bright internal highlights (glowing crystal look)
        _NS_nyzrak._aaline(surface, (*_NS_nyzrak.PALETTE["ice_bright"], 200),
                (tx - tomb_w + 4, ty - tomb_h + 15), (tx - tomb_w + 4, ty), 1)
        _NS_nyzrak._aaline(surface, (*_NS_nyzrak.PALETTE["ice_bright"], 200),
                (tx + tomb_w - 4, ty - tomb_h + 15), (tx + tomb_w - 4, ty), 1)
        _NS_nyzrak._aaline(surface, (*_NS_nyzrak.PALETTE["ice_hot"], 220),
                (tx, ty - tomb_h + 3), (tx, ty - 5), 1)

        # Diagonal ice facet lines
        for i in range(3):
            _NS_nyzrak._aaline(surface, (*_NS_nyzrak.PALETTE["ice_light"], 180),
                    (tx - tomb_w + 4, ty - i * 12),
                    (tx - tomb_w // 2, ty - tomb_h + i * 5 + 5), 1)
            _NS_nyzrak._aaline(surface, (*_NS_nyzrak.PALETTE["ice_light"], 180),
                    (tx + tomb_w - 4, ty - i * 12),
                    (tx + tomb_w // 2, ty - tomb_h + i * 5 + 5), 1)

        # Ice spikes protruding from tomb
        for i, off in enumerate((-tomb_w + 2, 0, tomb_w - 2)):
            _NS_nyzrak._draw_crystal_spike(surface, tx + off, ty - tomb_h + 3,
                                 ty - tomb_h - 8, 3, 240)

        # Snowflake sparkles
        for i in range(5):
            angle = phase + i * math.pi * 2 / 5
            r = tomb_w + 5
            sx = tx + int(math.cos(angle) * r)
            sy = ty - tomb_h // 2 + int(math.sin(angle) * tomb_h // 2)
            _NS_nyzrak._draw_snowflake(surface, sx, sy, 2, 220, rotate=phase * 2 + i)


    # ===================================================================
    # SKILL R: COLD EMBRACE (ice dome shield)
    # ===================================================================
    def _draw_cold_embrace_ground(surface, boss, x, y, timer, phase):
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Ground circle
        for i in range(3):
            r = int(50 + i * 12 + math.sin(phase + i) * 4)
            _NS_nyzrak._ellipse(surface, (*_NS_nyzrak.PALETTE["ice_bright"], int(120 * pulse)),
                     (x - r, y + 45 - r // 3, r * 2, r // 1.5), 2)


    def _draw_cold_embrace_foreground(surface, boss, x, y, timer, phase):
        """Ice crystal dome around boss."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ice crystal spikes rising in ring around boss
        if progress < 0.3:
            rise_t = progress / 0.3
        else:
            rise_t = 1.0

        ring_radius = 55
        for i in range(14):
            angle = i * math.pi * 2 / 14
            spike_x = x + int(math.cos(angle) * ring_radius)
            spike_y = y + 40 + int(math.sin(angle) * ring_radius * 0.5)
            spike_h = int(30 * rise_t) + (i % 3) * 3

            _NS_nyzrak._draw_crystal_spike(surface, spike_x, spike_y,
                                 spike_y - spike_h, 4, 240)

        # Inner smaller spikes
        for i in range(10):
            angle = i * math.pi * 2 / 10 + phase * 0.1
            r_inner = 35
            spike_x = x + int(math.cos(angle) * r_inner)
            spike_y = y + 42 + int(math.sin(angle) * r_inner * 0.5)
            spike_h = int(22 * rise_t)
            _NS_nyzrak._draw_crystal_spike(surface, spike_x, spike_y,
                                 spike_y - spike_h, 3, 220)

        # Dome overlay (semi-transparent)
        if progress > 0.3:
            dome_alpha = int(100 * min(1.0, (progress - 0.3) / 0.2))
            dome = pygame.Surface((ring_radius * 2 + 20, ring_radius + 40), pygame.SRCALPHA)
            # Draw dome arcs
            dcx, dcy = ring_radius + 10, ring_radius + 20
            for i in range(10):
                a1 = math.pi + i * math.pi / 10
                a2 = a1 + math.pi / 10
                x1 = dcx + int(math.cos(a1) * ring_radius)
                y1 = dcy + int(math.sin(a1) * ring_radius * 0.7)
                x2 = dcx + int(math.cos(a2) * ring_radius)
                y2 = dcy + int(math.sin(a2) * ring_radius * 0.7)
                pygame.draw.line(dome, (*_NS_nyzrak.PALETTE["ice_bright"], dome_alpha),
                                 (x1, y1), (x2, y2), 2)

            # Bright orbs on dome
            for i in range(4):
                angle = phase * 0.5 + i * math.pi / 2
                ox = dcx + int(math.cos(angle) * ring_radius * 0.85)
                oy = dcy + int(math.sin(angle) * ring_radius * 0.55)
                pygame.draw.circle(dome, (*_NS_nyzrak.PALETTE["ice_hot"], dome_alpha + 100),
                                   (ox, oy), 4)
                pygame.draw.circle(dome, (*_NS_nyzrak.PALETTE["ice_pure"], min(255, dome_alpha + 155)),
                                   (ox, oy), 2)

            surface.blit(dome, (x - dcx, y + 40 - dcy + ring_radius // 2))

        # Sparkling snowflakes around dome
        for i in range(8):
            angle = phase * 1.5 + i * math.pi / 4
            r = ring_radius + 8
            sx = x + int(math.cos(angle) * r)
            sy = y + 20 + int(math.sin(angle) * r * 0.5) - 10
            _NS_nyzrak._draw_snowflake(surface, sx, sy, 3, 230, rotate=phase * 3 + i)


    # ===================================================================
    # Backward compatible alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_nyzrak.draw_nyzrak(surface, boss, x, y)


# ====================================================================
# ANCIENT_APPARITION
# ====================================================================
class _NS_ancient_apparition:
    """Namespace ancient_apparition - isi asli tidak diubah."""

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
        if attacking:
            _NS_ancient_apparition._draw_aa_attack(surface, boss, x, y)
        elif active_skill == "w":
            _NS_ancient_apparition._draw_aa_casting(surface, boss, x, y, "w")
        elif active_skill == "e":
            _NS_ancient_apparition._draw_aa_casting(surface, boss, x, y, "e")
        elif moving:
            _NS_ancient_apparition._draw_aa_walk(surface, boss, x, y)
        else:
            _NS_ancient_apparition._draw_aa_idle(surface, boss, x, y)

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
            duration = 60
            progress = max(0.0, min(1.0, 1 - timer / duration))
            if 0.35 < progress < 0.45 and not getattr(boss, "_aa_e_spawned", False):
                _NS_ancient_apparition._spawn_ice_bolt(boss, x + 25 * boss.direction, y - 5, tx, ty)
                boss._aa_e_spawned = True
            if progress > 0.7:
                boss._aa_e_spawned = False

        elif active_skill == "w":
            duration = 60
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

        # Two glowing eyes (elongated ovals)
        for side in (-1, 1):
            ex = cx + side * 3
            ey = cy - 1
            # Outer glow
            _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["face_dark"], int(180 * face_intensity)),
                      (ex, ey), 4)
            _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["face_mid"], int(220 * face_intensity)),
                      (ex, ey), 3)
            _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["face_bright"], int(255 * face_intensity)),
                      (ex, ey), 2)
            _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["face_hot"], int(255 * face_intensity)),
                      (ex, ey), 1)
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
        for i in range(10):
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
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((140, 42), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(34, 3, -4):
            alpha = int((34 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_ancient_apparition.PALETTE["frost_dark"], min(255, alpha)),
                    (70 - radius * 2, 21 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 70, cy - 10))

        # Rising frost wisps
        for i, offset in enumerate((-22, -8, 8, 22)):
            t = (phase * 0.55 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 28)
            alpha = max(0, min(255, int(220 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["frost_dark"], alpha), (sx, sy), 5)
            _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["frost_mid"], alpha), (sx, sy - 2), 3)
            _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["frost_light"], alpha), (sx, sy - 3), 2)
            _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["ice_hot"], alpha), (sx, sy - 3), 1)

        # Snowflakes drifting
        for i in range(5):
            t = (phase * 0.4 + i * 0.2) % 1.0
            angle = phase * 0.5 + i * math.pi * 2 / 5
            r = 22 + int(math.sin(phase + i * 1.3) * 6)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 9) - int(t * 8)
            alpha = int(230 * (1 - t * 0.5) * strength)
            _NS_ancient_apparition._draw_snowflake(surface, sx, sy, 2, max(0, min(255, alpha)),
                             rotate=phase + i)

        # Small ice crystals on ground
        for i in range(4):
            angle = i * math.pi / 2
            sx = cx + int(math.cos(angle) * 30)
            sy = cy + int(math.sin(angle) * 6)
            _NS_ancient_apparition._draw_frost_crystal_spike(surface, sx, sy + 4, sy - 3, 2, 200)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = max(0, 140 - i * 25)
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["frost_mid"], alpha),
                          (sx, sy), max(2, 5 - i))
                _NS_ancient_apparition._aacircle(surface, (*_NS_ancient_apparition.PALETTE["frost_light"], alpha),
                          (sx, sy), max(1, 3 - i))


    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((110, 22), pygame.SRCALPHA)
        for radius in range(11, 0, -1):
            alpha = max(0, (11 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (11 - radius, 11 - radius, 88 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_ancient_apparition.PALETTE["ice_dark"], 80), (10, 5, 90, 12))
        surface.blit(shadow, (x - 55, y - 11))


    def _draw_frost_aura(surface, x, y, phase, active_skill):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.5 if active_skill in ("q", "w", "e", "r") else 1.0
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(80, 5, -4):
            alpha = int((80 - radius) * 1.4 * pulse * strength)
            if alpha > 0:
                _NS_ancient_apparition._aacircle(aura, (*_NS_ancient_apparition.PALETTE["ice_darkest"], min(255, alpha)),
                          (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))


    def _draw_ground_frost(surface, x, y, phase, active_skill):
        """Frost ring on ground."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((140, 46), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_ancient_apparition.PALETTE["ice_dark"], 160),
                            (5, 10, 130, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_ancient_apparition.PALETTE["ice_mid"], 190),
                            (20, 14, 100, 18), 2)

        for i in range(10):
            angle = phase * 0.15 + i * math.pi / 5
            x1 = 70 + int(math.cos(angle) * 32)
            y1 = 23 + int(math.sin(angle) * 7)
            x2 = 70 + int(math.cos(angle) * 60)
            y2 = 23 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_ancient_apparition.PALETTE["ice_bright"], 180),
                             (x1, y1), (x2, y2), 1)

        if active_skill:
            pygame.draw.ellipse(ring, (*_NS_ancient_apparition.PALETTE["ice_hot"], int(80 * pulse)),
                                (15, 8, 110, 30), 1)

        # Snowflakes on ring
        for i in range(6):
            angle = phase * 0.3 + i * math.pi / 3
            sx = 70 + int(math.cos(angle) * 50)
            sy = 23 + int(math.sin(angle) * 8)
            _NS_ancient_apparition._draw_snowflake(ring, sx, sy, 2, 200, rotate=phase * 2 + i)

        surface.blit(ring, (x - 70, y - 23))


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
        duration = 70
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
        duration = 70
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
        duration = 100
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
        duration = 100
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
# ENTRY POINT PUBLIK (dipanggil base_boss.Boss.draw)
# ====================================================================

def draw_varkul(surface, boss, x, y):
    """Entry point varkul."""
    return _NS_varkul.draw_varkul(surface, boss, x, y)

def draw_xerathis(surface, boss, x, y):
    """Entry point xerathis."""
    return _NS_xerathis.draw_xerathis(surface, boss, x, y)

def draw_nyzrak(surface, boss, x, y):
    """Entry point nyzrak."""
    return _NS_nyzrak.draw_nyzrak(surface, boss, x, y)

def draw_ancient_apparition(surface, boss, x, y):
    """Entry point ancient_apparition."""
    return _NS_ancient_apparition.draw_ancient_apparition(surface, boss, x, y)
