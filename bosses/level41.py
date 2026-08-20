"""
bosses/level41.py - Semua boss Level 41

Berisi:
  - emberwick    (mini boss - RANGED blazing matron, fire + gnashfang)
  - grondarthul  (mini boss - MELEE troll king, frost troll)
  - xareth       (mini boss - RANGED timereder, voidwalker)
  - grimkor      (TRUE BOSS - MELEE sawmill warlord, sawblade)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _em_ (emberwick), _gro_ (grondarthul), _xr_ (xareth),
    _gk_ (grimkor) sudah unik.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# EMBERWICK (BLAZING MATRON) - Mini Boss
# ====================================================================

class _NS_emberwick:
    """Namespace emberwick - old lady on fire-lizard mount."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Lizard body (orange/red scales)
        "lizard_darkest": (35, 12, 5),
        "lizard_dark": (90, 35, 15),
        "lizard_mid": (180, 75, 30),
        "lizard_light": (230, 130, 60),
        "lizard_edge": (255, 190, 110),
        "lizard_shine": (255, 230, 170),
        # Lizard belly (tan/cream)
        "belly_dark": (95, 60, 30),
        "belly_mid": (170, 130, 75),
        "belly_light": (230, 195, 135),
        "belly_shine": (255, 235, 185),
        # Grandma skin (peachy)
        "skin_dark": (140, 90, 65),
        "skin_mid": (210, 155, 120),
        "skin_light": (245, 210, 175),
        "skin_shine": (255, 235, 210),
        # White grandma hair
        "hair_dark": (140, 130, 130),
        "hair_mid": (210, 200, 200),
        "hair_light": (245, 240, 240),
        "hair_shine": (255, 255, 255),
        # Green vest/goggles
        "vest_dark": (25, 55, 30),
        "vest_mid": (55, 110, 65),
        "vest_light": (110, 175, 120),
        "vest_glass": (150, 220, 180),
        # Iron/steel blunderbuss
        "iron_darkest": (18, 15, 12),
        "iron_dark": (55, 50, 45),
        "iron_mid": (110, 100, 90),
        "iron_light": (180, 170, 155),
        "iron_shine": (240, 235, 220),
        # Copper/brass accents (gun barrel)
        "brass_dark": (95, 55, 20),
        "brass_mid": (180, 115, 45),
        "brass_light": (240, 175, 80),
        "brass_shine": (255, 220, 140),
        # Fire (orange/yellow explosive)
        "fire_darkest": (40, 10, 2),
        "fire_dark": (140, 40, 10),
        "fire_mid": (240, 100, 25),
        "fire_light": (255, 175, 55),
        "fire_hot": (255, 225, 120),
        "fire_shine": (255, 250, 200),
        # Cookie (brown + green acid)
        "cookie_dark": (75, 40, 15),
        "cookie_mid": (140, 85, 40),
        "cookie_light": (200, 145, 85),
        "acid_dark": (30, 70, 15),
        "acid_mid": (105, 175, 35),
        "acid_light": (195, 245, 90),
        "acid_hot": (240, 255, 180),
        # Smoke
        "smoke_dark": (35, 32, 30),
        "smoke_mid": (100, 95, 90),
        "smoke_light": (180, 175, 170),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
        "black": (0, 0, 0),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_emberwick._clamp(color)
        if _NS_emberwick.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_emberwick._clamp(color)
        if _NS_emberwick.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_emberwick._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 260 * getattr(boss, "direction", 1)), int(y)
    # ================= ENTRY POINT =================
    def draw_emberwick(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_emberwick._detect_moving(boss)
        _NS_emberwick._update_em_attack_anim(boss)
        attacking = (
            getattr(boss, "_em_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        _NS_emberwick._draw_fire_aura(surface, x, y, pulse)
        _NS_emberwick._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX.
        if active_skill == "w":
            _NS_emberwick._draw_cookie_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_emberwick._draw_ember_kiss_ground(surface, boss, x, y, skill_timer, pulse)
        # Body.
        if attacking:
            _NS_emberwick._draw_em_attack(surface, boss, x, y)
        elif moving:
            _NS_emberwick._draw_em_walk(surface, boss, x, y)
        else:
            _NS_emberwick._draw_em_idle(surface, boss, x, y)
        # Foreground FX (projectiles/effects).
        if active_skill == "q":
            _NS_emberwick._draw_scatterblast(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_emberwick._draw_cookie_projectile(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_emberwick._draw_gnash_spit(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_emberwick._draw_ember_kiss_stream(surface, boss, x, y, skill_timer, pulse)
    # ================= ANIMATION STATE =================
    def _update_em_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_em_previous_timer", 0))
        active = bool(getattr(boss, "_em_attack_active", False))
        if not active and previous > timer and previous >= cooldown - 2:
            boss._em_attack_active = True
            boss._em_attack_frame = 0
            active = True
        elif active:
            boss._em_attack_frame = int(getattr(boss, "_em_attack_frame", 0)) + 1
            if boss._em_attack_frame >= cooldown:
                boss._em_attack_active = False
                boss._em_attack_frame = 0
                active = False
        boss._em_previous_timer = timer
        boss._em_attack_progress = (
            min(1.0, getattr(boss, "_em_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_em_last_x"):
            boss._em_last_x = boss.x
            boss._em_last_y = boss.y
            return False
        dx = abs(boss.x - boss._em_last_x)
        dy = abs(boss.y - boss._em_last_y)
        boss._em_last_x = boss.x
        boss._em_last_y = boss.y
        return dx + dy > 0.3
    # ================= POSE ROUTERS =================
    def _draw_em_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_emberwick._draw_shadow(surface, x, y + 50)
        _NS_emberwick._draw_hover_particles(surface, x, y + 44, boss.pulse)
        _NS_emberwick._draw_em_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")
    def _draw_em_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 5)
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_emberwick._draw_shadow(surface, x + sway, y + 50)
        _NS_emberwick._draw_hover_particles(surface, x + sway, y + 44, phase, trail=True, facing=boss.direction)
        _NS_emberwick._draw_em_body(surface, x + sway, y + bob, boss.direction, phase, "walk")
    def _draw_em_attack(surface, boss, x, y):
        progress = getattr(boss, "_em_attack_progress", None)
        if progress is None or progress <= 0:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Recoil kick when shooting.
        if progress < 0.3:
            t = progress / 0.3
            recoil = -int(t * 4) * boss.direction
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            recoil = int(-4 + t * 2) * boss.direction
        else:
            t = (progress - 0.5) / 0.5
            recoil = int(-2 * (1 - t)) * boss.direction
        _NS_emberwick._draw_shadow(surface, x + recoil, y + 50)
        _NS_emberwick._draw_hover_particles(surface, x + recoil, y + 44, boss.pulse, intense=True)
        _NS_emberwick._draw_em_body(surface, x + recoil, y, boss.direction, boss.pulse, "attack", progress)
        _NS_emberwick._draw_muzzle_blast(surface, boss, x + recoil, y, progress)
        _NS_emberwick._draw_basic_bullet(surface, boss, x + recoil, y, progress)
    # ================= BODY =================
    def _draw_em_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Layer: tail → back legs → lizard body → grandma → arms/gun → front legs → head."""
        # Tail (back).
        _NS_emberwick._draw_lizard_tail(surface, cx, cy + 8, facing, phase, action)
        # Back legs (behind body).
        _NS_emberwick._draw_lizard_legs(surface, cx, cy + 12, facing, phase, action, back=True)
        # Main lizard body (horizontal blob).
        _NS_emberwick._draw_lizard_body(surface, cx, cy + 6, facing, phase, action)
        # Saddle + grandma sits on top.
        _NS_emberwick._draw_saddle(surface, cx - facing * 4, cy - 6, facing, phase)
        _NS_emberwick._draw_grandma(surface, cx - facing * 4, cy - 12, facing, phase, action, attack_progress)
        # Blunderbuss extending forward.
        _NS_emberwick._draw_blunderbuss(surface, cx, cy - 8, facing, phase, action, attack_progress)
        # Lizard head (front).
        _NS_emberwick._draw_lizard_head(surface, cx + facing * 18, cy + 4, facing, phase, action)
        # Front legs.
        _NS_emberwick._draw_lizard_legs(surface, cx, cy + 12, facing, phase, action, back=False)
    def _draw_lizard_tail(surface, cx, cy, facing, phase, action):
        """Long thick tail behind."""
        back_dir = -facing
        base_x = cx + back_dir * 14
        base_y = cy
        segments = 7
        points = [(base_x, base_y)]
        for i in range(1, segments + 1):
            t = i / segments
            x_off = int(back_dir * (10 + t * 20))
            y_off = int(-2 + t * 6 - t * t * 4)
            wave = math.sin(phase * 1.0 + t * math.pi) * (2 + t * 2)
            y_off += int(wave)
            points.append((base_x + x_off, base_y + y_off))
        for i in range(len(points) - 1):
            thickness = max(3, 12 - i)
            _NS_emberwick._aaline(surface, _NS_emberwick.PALETTE["shadow_deep"],
                                  (points[i][0] + 2, points[i][1] + 2),
                                  (points[i + 1][0] + 2, points[i + 1][1] + 2),
                                  thickness + 1)
            _NS_emberwick._aaline(surface, _NS_emberwick.PALETTE["lizard_darkest"],
                                  points[i], points[i + 1], thickness)
            _NS_emberwick._aaline(surface, _NS_emberwick.PALETTE["lizard_dark"],
                                  points[i], points[i + 1], max(1, thickness - 2))
            _NS_emberwick._aaline(surface, _NS_emberwick.PALETTE["lizard_mid"],
                                  (points[i][0], points[i][1] - 1),
                                  (points[i + 1][0], points[i + 1][1] - 1),
                                  max(1, thickness - 4))
            _NS_emberwick._aaline(surface, _NS_emberwick.PALETTE["lizard_light"],
                                  (points[i][0], points[i][1] - 2),
                                  (points[i + 1][0], points[i + 1][1] - 2),
                                  max(1, thickness - 6))
            # Belly.
            _NS_emberwick._aaline(surface, _NS_emberwick.PALETTE["belly_mid"],
                                  (points[i][0], points[i][1] + 2),
                                  (points[i + 1][0], points[i + 1][1] + 2),
                                  max(1, thickness - 6))
        # Spikes along tail.
        for i in range(1, len(points), 2):
            spike_size = max(1, 4 - i // 2)
            spike_x = points[i][0]
            spike_y = points[i][1] - max(1, 6 - i)
            _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["lizard_darkest"], [
                (points[i][0] - 2, points[i][1] - 1),
                (spike_x, spike_y),
                (points[i][0] + 2, points[i][1] - 1),
            ])
            _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["lizard_light"], [
                (points[i][0] - 1, points[i][1] - 1),
                (spike_x, spike_y),
                (points[i][0] + 1, points[i][1] - 1),
            ])
    def _draw_lizard_body(surface, cx, cy, facing, phase, action):
        """Rounded chubby lizard body."""
        breath = math.sin(phase * 0.8) * 1
        body_shape = [
            (cx - 18, cy),
            (cx - 20, cy - 4),
            (cx - 18, cy - 10),
            (cx - 10, cy - 14),
            (cx + 2, cy - 15),
            (cx + 14, cy - 13),
            (cx + 20, cy - 8),
            (cx + 22, cy - 2),
            (cx + 20, cy + 5),
            (cx + 14, cy + 10),
            (cx + 4, cy + 12),
            (cx - 8, cy + 12),
            (cx - 16, cy + 10),
            (cx - 20, cy + 4),
        ]
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in body_shape])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["lizard_darkest"], body_shape)
        # Top scales (orange).
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["lizard_dark"], [
            (cx - 17, cy - 1),
            (cx - 18, cy - 8),
            (cx - 9, cy - 13),
            (cx + 3, cy - 14),
            (cx + 13, cy - 12),
            (cx + 19, cy - 6),
            (cx + 20, cy + 1),
            (cx - 17, cy + 1),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["lizard_mid"], [
            (cx - 14, cy - 3),
            (cx - 14, cy - 8),
            (cx - 5, cy - 12),
            (cx + 4, cy - 12),
            (cx + 12, cy - 10),
            (cx + 16, cy - 4),
            (cx + 14, cy),
            (cx - 12, cy),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["lizard_light"], [
            (cx - 8, cy - 8),
            (cx + 4, cy - 10),
            (cx + 10, cy - 7),
            (cx + 8, cy - 3),
            (cx - 4, cy - 3),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["lizard_edge"], [
            (cx - 2, cy - 8),
            (cx + 4, cy - 9),
            (cx + 6, cy - 6),
            (cx, cy - 5),
        ])
        # Belly (bottom, cream).
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["belly_dark"], [
            (cx - 17, cy + 2),
            (cx + 19, cy + 2),
            (cx + 18, cy + 6),
            (cx + 12, cy + 10),
            (cx + 2, cy + 12),
            (cx - 8, cy + 12),
            (cx - 15, cy + 9),
            (cx - 18, cy + 5),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["belly_mid"], [
            (cx - 15, cy + 4),
            (cx + 16, cy + 4),
            (cx + 14, cy + 8),
            (cx + 2, cy + 10),
            (cx - 8, cy + 10),
            (cx - 13, cy + 8),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["belly_light"], [
            (cx - 10, cy + 6),
            (cx + 10, cy + 6),
            (cx + 8, cy + 9),
            (cx - 6, cy + 9),
        ])
        # Belly segments.
        for i, y_off in enumerate((5, 8)):
            pygame.draw.line(surface, _NS_emberwick.PALETTE["belly_dark"],
                             (cx - 10 + i * 2, cy + y_off),
                             (cx + 10 - i * 2, cy + y_off), 1)
        # Scale texture.
        for row in range(2):
            y_row = cy - 6 + row * 3
            for i, dx in enumerate((-10, -5, 0, 5, 10)):
                offset_x = (row % 2) * 2 - 1
                pygame.draw.rect(surface, _NS_emberwick.PALETTE["lizard_edge"],
                                 (cx + dx + offset_x, y_row - 1, 1, 1))
    def _draw_lizard_head(surface, cx, cy, facing, phase, action):
        """Wide lizard head with big grin."""
        # Head shape.
        head_shape = [
            (cx - 8 * facing, cy + 4),
            (cx - 10 * facing, cy - 2),
            (cx - 6 * facing, cy - 8),
            (cx, cy - 10),
            (cx + 8 * facing, cy - 8),
            (cx + 14 * facing, cy - 4),
            (cx + 16 * facing, cy),
            (cx + 15 * facing, cy + 5),
            (cx + 10 * facing, cy + 8),
            (cx + 2 * facing, cy + 9),
            (cx - 6 * facing, cy + 8),
        ]
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in head_shape])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["lizard_darkest"], head_shape)
        # Top color.
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["lizard_dark"], [
            (cx - 8 * facing, cy + 3),
            (cx - 9 * facing, cy - 1),
            (cx - 5 * facing, cy - 7),
            (cx, cy - 9),
            (cx + 7 * facing, cy - 7),
            (cx + 13 * facing, cy - 3),
            (cx + 15 * facing, cy),
            (cx - 5 * facing, cy),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["lizard_mid"], [
            (cx - 6 * facing, cy - 1),
            (cx - 3 * facing, cy - 5),
            (cx + 4 * facing, cy - 6),
            (cx + 10 * facing, cy - 3),
            (cx + 13 * facing, cy - 1),
            (cx + 5 * facing, cy - 2),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["lizard_light"], [
            (cx - 2 * facing, cy - 4),
            (cx + 3 * facing, cy - 5),
            (cx + 7 * facing, cy - 3),
            (cx + 3 * facing, cy - 2),
        ])
        # Snout tan.
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["belly_dark"], [
            (cx + 8 * facing, cy),
            (cx + 15 * facing, cy),
            (cx + 14 * facing, cy + 4),
            (cx + 8 * facing, cy + 6),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["belly_mid"], [
            (cx + 10 * facing, cy + 1),
            (cx + 14 * facing, cy + 2),
            (cx + 12 * facing, cy + 4),
        ])
        # Small horns on top.
        for horn_off in (-3, 3):
            hx = cx + int(horn_off * facing)
            hy = cy - 7
            _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["lizard_darkest"], [
                (hx - 1, hy),
                (hx, hy - 4),
                (hx + 1, hy),
            ])
            _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["lizard_edge"], [
                (hx, hy - 3),
                (hx + 1, hy - 1),
                (hx - 1, hy - 1),
            ])
        # NOSTRIL.
        pygame.draw.rect(surface, _NS_emberwick.PALETTE["shadow_deep"],
                         (cx + 12 * facing, cy + 2, 2, 1))
        # EYES (yellow-green, big & round).
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        ex = cx + int(2 * facing)
        ey = cy - 3
        pygame.draw.rect(surface, _NS_emberwick.PALETTE["shadow_deep"], (ex - 2, ey - 2, 5, 4))
        pygame.draw.rect(surface, _NS_emberwick.PALETTE["fire_hot"], (ex - 1, ey - 1, 3, 3))
        pygame.draw.rect(surface, _NS_emberwick.PALETTE["fire_light"], (ex, ey - 1, 2, 2))
        pygame.draw.rect(surface, _NS_emberwick.PALETTE["shadow_deep"], (ex, ey, 1, 1))  # pupil
        pygame.draw.rect(surface, _NS_emberwick.PALETTE["white"], (ex + 1, ey - 1, 1, 1))
        # MOUTH GRIN (with fangs visible).
        mouth_open = 0
        if action == "attack":
            mouth_open = int(math.sin(getattr(pygame.time, "get_ticks", lambda: 0)() * 0.01) * 2 + 2)
        mouth_y = cy + 4
        if mouth_open > 0:
            _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["shadow_deep"], [
                (cx + 2 * facing, mouth_y),
                (cx + 14 * facing, mouth_y),
                (cx + 12 * facing, mouth_y + mouth_open),
                (cx + 4 * facing, mouth_y + mouth_open),
            ])
            # Small green glow inside.
            _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["acid_mid"],
                                    (cx + 8 * facing, mouth_y + 1), 2)
        else:
            pygame.draw.line(surface, _NS_emberwick.PALETTE["shadow_deep"],
                             (cx + 2 * facing, mouth_y),
                             (cx + 14 * facing, mouth_y), 1)
        # Fangs.
        for i, fx_off in enumerate((5, 9)):
            fx = cx + int(fx_off * facing)
            pygame.draw.rect(surface, _NS_emberwick.PALETTE["belly_light"], (fx, mouth_y, 1, 2))
            pygame.draw.rect(surface, _NS_emberwick.PALETTE["white"], (fx, mouth_y, 1, 1))
    def _draw_lizard_legs(surface, cx, cy, facing, phase, action, back=True):
        """Two legs (front or back)."""
        offset_x = -12 if back else 12
        leg_bob = math.sin(phase * 1.5 + (0 if back else math.pi)) * 3 if action == "walk" \
            else math.sin(phase * 0.8) * 1
        for side in (-1, 1):
            hip_x = cx + offset_x + side * 3
            hip_y = cy - 6
            knee_x = cx + offset_x + side * 5
            knee_y = cy + int(leg_bob * side * 0.5)
            foot_x = cx + offset_x + side * 4
            foot_y = cy + 8 + int(leg_bob * side * 0.3)
            _NS_emberwick._aaline(surface, _NS_emberwick.PALETTE["shadow_deep"],
                                  (hip_x + 1, hip_y + 1), (knee_x + 1, knee_y + 1), 4)
            _NS_emberwick._aaline(surface, _NS_emberwick.PALETTE["lizard_darkest"],
                                  (hip_x, hip_y), (knee_x, knee_y), 4)
            _NS_emberwick._aaline(surface, _NS_emberwick.PALETTE["lizard_dark"],
                                  (hip_x, hip_y), (knee_x, knee_y), 3)
            _NS_emberwick._aaline(surface, _NS_emberwick.PALETTE["lizard_mid"],
                                  (hip_x, hip_y), (knee_x, knee_y), 1)
            _NS_emberwick._aaline(surface, _NS_emberwick.PALETTE["lizard_darkest"],
                                  (knee_x, knee_y), (foot_x, foot_y), 3)
            _NS_emberwick._aaline(surface, _NS_emberwick.PALETTE["lizard_dark"],
                                  (knee_x, knee_y), (foot_x, foot_y), 2)
            # Claw foot (3 toes).
            _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["lizard_darkest"], [
                (foot_x - 3, foot_y - 1),
                (foot_x + 3, foot_y - 1),
                (foot_x + 2, foot_y + 2),
                (foot_x - 2, foot_y + 2),
            ])
            _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["lizard_mid"], [
                (foot_x - 2, foot_y),
                (foot_x + 2, foot_y),
                (foot_x + 1, foot_y + 1),
                (foot_x - 1, foot_y + 1),
            ])
            # Claw tips.
            for cx_toe in (-3, 0, 3):
                pygame.draw.rect(surface, _NS_emberwick.PALETTE["belly_light"],
                                 (foot_x + cx_toe, foot_y + 2, 1, 1))
    def _draw_saddle(surface, cx, cy, facing, phase):
        """Leather saddle on lizard back."""
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["shadow_deep"], [
            (cx - 9 + 1, cy + 1),
            (cx + 9 + 1, cy + 1),
            (cx + 7 + 1, cy + 4 + 1),
            (cx - 7 + 1, cy + 4 + 1),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["cookie_dark"], [
            (cx - 9, cy),
            (cx + 9, cy),
            (cx + 7, cy + 4),
            (cx - 7, cy + 4),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["cookie_mid"], [
            (cx - 8, cy + 1),
            (cx + 8, cy + 1),
            (cx + 6, cy + 3),
            (cx - 6, cy + 3),
        ])
        # Saddle rim.
        pygame.draw.line(surface, _NS_emberwick.PALETTE["brass_dark"],
                         (cx - 8, cy), (cx + 8, cy), 1)
        pygame.draw.line(surface, _NS_emberwick.PALETTE["brass_light"],
                         (cx - 8, cy - 1), (cx + 8, cy - 1), 1)
        # Rivets.
        for rx in (-7, -3, 3, 7):
            pygame.draw.rect(surface, _NS_emberwick.PALETTE["brass_mid"], (cx + rx, cy + 1, 1, 1))
            pygame.draw.rect(surface, _NS_emberwick.PALETTE["brass_shine"], (cx + rx, cy + 1, 1, 1))
    def _draw_grandma(surface, cx, cy, facing, phase, action, attack_progress):
        """Grandma sitting on saddle."""
        bob = math.sin(phase * 0.5) * 1
        # Torso (green vest).
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["shadow_deep"], [
            (cx - 6 + 1, cy + 1),
            (cx + 6 + 1, cy + 1),
            (cx + 7 + 1, cy + 8 + 1),
            (cx - 7 + 1, cy + 8 + 1),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["vest_dark"], [
            (cx - 6, cy),
            (cx + 6, cy),
            (cx + 7, cy + 8),
            (cx - 7, cy + 8),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["vest_mid"], [
            (cx - 5, cy + 1),
            (cx + 5, cy + 1),
            (cx + 6, cy + 7),
            (cx - 6, cy + 7),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["vest_light"], [
            (cx - 3, cy + 2),
            (cx + 3, cy + 2),
            (cx + 4, cy + 6),
            (cx - 4, cy + 6),
        ])
        # Belt line.
        pygame.draw.line(surface, _NS_emberwick.PALETTE["cookie_dark"],
                         (cx - 7, cy + 6), (cx + 7, cy + 6), 1)
        pygame.draw.rect(surface, _NS_emberwick.PALETTE["brass_mid"], (cx - 1, cy + 6, 3, 1))
        # HEAD.
        hy = cy - 8 + int(bob)
        _NS_emberwick._draw_grandma_head(surface, cx, hy, facing, phase, action)
        # Arms (holding gun forward).
        _NS_emberwick._draw_grandma_arms(surface, cx, cy + 2, facing, phase, action, attack_progress)
    def _draw_grandma_head(surface, cx, cy, facing, phase, action):
        """Wrinkly grandma head with big hair bun & goggles."""
        # Hair bun on top (curly big).
        for offset in [(-4, -4, 3), (4, -4, 3), (-2, -6, 3), (2, -6, 3), (0, -7, 4)]:
            hx = cx + offset[0]
            hy = cy + offset[1]
            hr = offset[2]
            _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["shadow_deep"], (hx + 1, hy + 1), hr)
            _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["hair_dark"], (hx, hy), hr)
            _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["hair_mid"], (hx, hy), hr - 1)
            _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["hair_light"], (hx - 1, hy - 1), max(1, hr - 2))
            pygame.draw.rect(surface, _NS_emberwick.PALETTE["hair_shine"], (hx - 1, hy - 1, 1, 1))
        # Face (round).
        _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["shadow_deep"], (cx + 1, cy + 1), 5)
        _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["skin_dark"], (cx, cy), 5)
        _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["skin_mid"], (cx, cy), 4)
        _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["skin_light"], (cx - 1, cy - 1), 3)
        pygame.draw.rect(surface, _NS_emberwick.PALETTE["skin_shine"], (cx - 1, cy - 1, 1, 1))
        # Red bandana line.
        pygame.draw.line(surface, _NS_emberwick.PALETTE["fire_dark"],
                         (cx - 4, cy - 3), (cx + 4, cy - 3), 1)
        pygame.draw.line(surface, _NS_emberwick.PALETTE["fire_mid"],
                         (cx - 4, cy - 4), (cx + 4, cy - 4), 1)
        # GOGGLES (round green lenses).
        for eye_off in (-2, 2):
            ex = cx + eye_off
            ey = cy - 1
            _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["iron_darkest"], (ex, ey), 2)
            _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["vest_dark"], (ex, ey), 2)
            _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["vest_glass"], (ex, ey), 1)
            pygame.draw.rect(surface, _NS_emberwick.PALETTE["white"], (ex, ey - 1, 1, 1))
        # Goggle strap.
        pygame.draw.line(surface, _NS_emberwick.PALETTE["iron_dark"], (cx - 4, cy - 1), (cx + 4, cy - 1), 1)
        # BIG GRIN mouth.
        if action == "attack":
            # Open mouth (yelling).
            pygame.draw.rect(surface, _NS_emberwick.PALETTE["shadow_deep"], (cx - 1, cy + 2, 3, 2))
            pygame.draw.rect(surface, _NS_emberwick.PALETTE["fire_dark"], (cx, cy + 2, 2, 1))
            # Tooth.
            pygame.draw.rect(surface, _NS_emberwick.PALETTE["white"], (cx, cy + 2, 1, 1))
        else:
            # Smile.
            pygame.draw.line(surface, _NS_emberwick.PALETTE["shadow_deep"],
                             (cx - 2, cy + 2), (cx + 2, cy + 2), 1)
            pygame.draw.rect(surface, _NS_emberwick.PALETTE["white"], (cx, cy + 2, 1, 1))
    def _draw_grandma_arms(surface, cx, cy, facing, phase, action, attack_progress):
        """Both arms holding the blunderbuss forward."""
        # Both arms extend forward toward gun.
        shoulder_x = cx + facing * 3
        shoulder_y = cy
        forearm_x = cx + facing * 10
        forearm_y = cy - 2
        # Back arm.
        _NS_emberwick._aaline(surface, _NS_emberwick.PALETTE["shadow_deep"],
                              (shoulder_x + 1, shoulder_y + 1), (forearm_x + 1, forearm_y + 1), 4)
        _NS_emberwick._aaline(surface, _NS_emberwick.PALETTE["vest_dark"],
                              (shoulder_x, shoulder_y), (forearm_x, forearm_y), 4)
        _NS_emberwick._aaline(surface, _NS_emberwick.PALETTE["vest_mid"],
                              (shoulder_x, shoulder_y), (forearm_x, forearm_y), 2)
        # Front arm (visible).
        _NS_emberwick._aaline(surface, _NS_emberwick.PALETTE["vest_dark"],
                              (shoulder_x, shoulder_y + 1), (forearm_x, forearm_y + 1), 3)
        _NS_emberwick._aaline(surface, _NS_emberwick.PALETTE["vest_mid"],
                              (shoulder_x, shoulder_y + 1), (forearm_x, forearm_y + 1), 1)
        # Hand grip (skin).
        _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["skin_dark"], (forearm_x, forearm_y), 2)
        _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["skin_mid"], (forearm_x, forearm_y), 1)
    def _draw_blunderbuss(surface, cx, cy, facing, phase, action, attack_progress):
        """Big blunderbuss/cannon."""
        # Recoil kick.
        kick = 0
        if action == "attack":
            if attack_progress < 0.3:
                kick = -int(attack_progress / 0.3 * 5) * facing
            elif attack_progress < 0.5:
                kick = -int(5) * facing
            else:
                t = (attack_progress - 0.5) / 0.5
                kick = int(-5 * (1 - t)) * facing
        # Blunderbuss main barrel.
        base_x = cx + facing * 8 + kick
        base_y = cy
        barrel_length = 20
        tip_x = base_x + facing * barrel_length
        tip_y = base_y
        # Stock (behind).
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["shadow_deep"], [
            (base_x - facing * 4 + 1, base_y - 2 + 1),
            (base_x + 1, base_y - 3 + 1),
            (base_x + 1, base_y + 3 + 1),
            (base_x - facing * 4 + 1, base_y + 2 + 1),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["cookie_dark"], [
            (base_x - facing * 4, base_y - 2),
            (base_x, base_y - 3),
            (base_x, base_y + 3),
            (base_x - facing * 4, base_y + 2),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["cookie_mid"], [
            (base_x - facing * 3, base_y - 1),
            (base_x, base_y - 2),
            (base_x, base_y + 2),
            (base_x - facing * 3, base_y + 1),
        ])
        # Barrel main (iron).
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["shadow_deep"], [
            (base_x + 1, base_y - 3 + 1),
            (tip_x + 1, tip_y - 4 + 1),
            (tip_x + 1, tip_y + 4 + 1),
            (base_x + 1, base_y + 3 + 1),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["iron_darkest"], [
            (base_x, base_y - 3),
            (tip_x, tip_y - 4),
            (tip_x, tip_y + 4),
            (base_x, base_y + 3),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["iron_dark"], [
            (base_x, base_y - 2),
            (tip_x, tip_y - 3),
            (tip_x, tip_y + 3),
            (base_x, base_y + 2),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["iron_mid"], [
            (base_x, base_y - 1),
            (tip_x, tip_y - 2),
            (tip_x, tip_y + 2),
            (base_x, base_y + 1),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["iron_light"], [
            (base_x, base_y - 1),
            (tip_x, tip_y - 1),
            (tip_x, tip_y),
            (base_x, base_y),
        ])
        # BIG BELL MUZZLE at end (flared).
        muzzle_tip_x = tip_x + facing * 4
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["shadow_deep"], [
            (tip_x + 1, tip_y - 5 + 1),
            (muzzle_tip_x + 1, tip_y - 7 + 1),
            (muzzle_tip_x + 1, tip_y + 7 + 1),
            (tip_x + 1, tip_y + 5 + 1),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["iron_darkest"], [
            (tip_x, tip_y - 5),
            (muzzle_tip_x, tip_y - 7),
            (muzzle_tip_x, tip_y + 7),
            (tip_x, tip_y + 5),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["iron_dark"], [
            (tip_x, tip_y - 4),
            (muzzle_tip_x - facing, tip_y - 6),
            (muzzle_tip_x - facing, tip_y + 6),
            (tip_x, tip_y + 4),
        ])
        _NS_emberwick._poly(surface, _NS_emberwick.PALETTE["iron_mid"], [
            (tip_x, tip_y - 3),
            (muzzle_tip_x - facing * 2, tip_y - 5),
            (muzzle_tip_x - facing * 2, tip_y + 5),
            (tip_x, tip_y + 3),
        ])
        # Muzzle rim (brass).
        pygame.draw.line(surface, _NS_emberwick.PALETTE["brass_dark"],
                         (muzzle_tip_x, tip_y - 7), (muzzle_tip_x, tip_y + 7), 2)
        pygame.draw.line(surface, _NS_emberwick.PALETTE["brass_light"],
                         (muzzle_tip_x - facing, tip_y - 6), (muzzle_tip_x - facing, tip_y + 6), 1)
        # Dark hole inside.
        pygame.draw.rect(surface, _NS_emberwick.PALETTE["shadow_deep"],
                         (muzzle_tip_x - facing * 2, tip_y - 4, 2, 8))
        # Brass ring around barrel middle.
        mid_barrel_x = (base_x + tip_x) // 2
        pygame.draw.line(surface, _NS_emberwick.PALETTE["brass_dark"],
                         (mid_barrel_x, base_y - 3), (mid_barrel_x, base_y + 3), 2)
        pygame.draw.line(surface, _NS_emberwick.PALETTE["brass_light"],
                         (mid_barrel_x, base_y - 2), (mid_barrel_x, base_y + 2), 1)
        pygame.draw.rect(surface, _NS_emberwick.PALETTE["brass_shine"],
                         (mid_barrel_x, base_y - 1, 1, 1))
        # Store muzzle position for FX.
        boss_info = (muzzle_tip_x, tip_y, facing, kick)
        return boss_info
    # ================= BASIC ATTACK FX =================
    def _draw_muzzle_blast(surface, boss, x, y, progress):
        """Muzzle flash + smoke when firing."""
        if progress > 0.4:
            return
        facing = boss.direction
        # Muzzle position (adjusted for recoil).
        kick = -int(progress / 0.3 * 5) * facing if progress < 0.3 else -int(5) * facing
        muzzle_x = x + facing * (8 + 20 + 4) + kick
        muzzle_y = y - 8
        t = progress / 0.4
        flash_intensity = math.sin(t * math.pi)
        alpha_base = _NS_emberwick._alpha(255 * flash_intensity)
        FX_W, FX_H = 200, 150
        fx_surf = pygame.Surface((FX_W, FX_H), pygame.SRCALPHA)
        ox, oy = 40, FX_H // 2
        # Massive fire cone.
        cone_length = int(35 + t * 20)
        cone_width = int(20 + t * 10)
        # Layered flame cone.
        for layer_i, (color, r_mult, alpha_mult) in enumerate([
            (_NS_emberwick.PALETTE["fire_darkest"], 1.15, 0.5),
            (_NS_emberwick.PALETTE["fire_dark"], 1.0, 0.7),
            (_NS_emberwick.PALETTE["fire_mid"], 0.85, 0.85),
            (_NS_emberwick.PALETTE["fire_light"], 0.7, 1.0),
            (_NS_emberwick.PALETTE["fire_hot"], 0.5, 1.0),
            (_NS_emberwick.PALETTE["fire_shine"], 0.3, 1.0),
        ]):
            cl = int(cone_length * r_mult)
            cw = int(cone_width * r_mult * 0.5)
            layer_alpha = _NS_emberwick._alpha(alpha_base * alpha_mult)
            cone_shape = [
                (ox, oy),
                (ox + facing * (cl // 3), oy - cw),
                (ox + facing * cl, oy - cw // 2),
                (ox + facing * (cl + 4), oy),
                (ox + facing * cl, oy + cw // 2),
                (ox + facing * (cl // 3), oy + cw),
            ]
            pygame.draw.polygon(fx_surf, (*color, layer_alpha), cone_shape)
        # White-hot core burst.
        for r in range(12, 0, -1):
            a = _NS_emberwick._alpha(alpha_base * (12 - r) / 12 * 1.3)
            if a > 0:
                pygame.draw.circle(fx_surf, (*_NS_emberwick.PALETTE["fire_hot"], a),
                                   (ox + facing * 2, oy), r)
        pygame.draw.circle(fx_surf, (*_NS_emberwick.PALETTE["white"], alpha_base),
                           (ox + facing * 2, oy), 3)
        # Sparks flying out.
        for i in range(18):
            spark_angle = math.sin(i * 0.7 + t * 5) * 0.6
            spark_r = cone_length + (i % 5) * 4
            spx = ox + int(math.cos(spark_angle) * spark_r) * facing
            spy = oy + int(math.sin(spark_angle) * spark_r)
            spark_alpha = _NS_emberwick._alpha(alpha_base * 0.9)
            # Trail.
            tx_ = ox + int(math.cos(spark_angle) * (spark_r - 4)) * facing
            ty_ = oy + int(math.sin(spark_angle) * (spark_r - 4))
            pygame.draw.line(fx_surf, (*_NS_emberwick.PALETTE["fire_mid"], spark_alpha),
                             (tx_, ty_), (spx, spy), 2)
            pygame.draw.rect(fx_surf, (*_NS_emberwick.PALETTE["fire_hot"], spark_alpha), (spx, spy, 2, 2))
            pygame.draw.rect(fx_surf, (*_NS_emberwick.PALETTE["fire_shine"], spark_alpha), (spx, spy, 1, 1))
        # Smoke puffs at muzzle.
        for i in range(4):
            smoke_r = int(4 + t * 6 + i)
            sx = ox - facing * i * 2
            sy = oy - int(t * 8)
            sa = _NS_emberwick._alpha(180 * (1 - t) * (1 - i * 0.2))
            pygame.draw.circle(fx_surf, (*_NS_emberwick.PALETTE["smoke_dark"], sa), (sx, sy), smoke_r)
            pygame.draw.circle(fx_surf, (*_NS_emberwick.PALETTE["smoke_mid"], sa), (sx - 1, sy - 1), max(1, smoke_r - 2))
        surface.blit(fx_surf, (muzzle_x - ox, muzzle_y - oy))
    def _draw_basic_bullet(surface, boss, x, y, progress):
        """Fireball projectile from basic attack."""
        if progress < 0.3:
            return
        facing = boss.direction
        tx, ty = _NS_emberwick._target_position(boss, x, y)
        start_x = x + facing * 36
        start_y = y - 8
        t = (progress - 0.3) / 0.7
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Fireball trail.
        for i in range(8):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_emberwick._alpha(230 - i * 25)
            size = max(1, 7 - i)
            _NS_emberwick._aacircle(surface, (*_NS_emberwick.PALETTE["fire_darkest"], alpha), (px, py), size)
            _NS_emberwick._aacircle(surface, (*_NS_emberwick.PALETTE["fire_dark"], alpha), (px, py), max(1, size - 1))
            _NS_emberwick._aacircle(surface, (*_NS_emberwick.PALETTE["fire_mid"], alpha), (px, py), max(1, size - 2))
            _NS_emberwick._aacircle(surface, (*_NS_emberwick.PALETTE["fire_light"], alpha), (px, py), max(1, size - 3))
        # Bright bolt head.
        _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["fire_darkest"], (bx, by), 7)
        _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["fire_dark"], (bx, by), 5)
        _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["fire_mid"], (bx, by), 4)
        _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["fire_light"], (bx, by), 3)
        _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["fire_hot"], (bx, by), 2)
        _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["white"], (bx, by), 1)
        # Impact splash.
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(8 + st * 20)
            alpha = _NS_emberwick._alpha(240 * (1 - st))
            _NS_emberwick._aacircle(surface, (*_NS_emberwick.PALETTE["fire_dark"], alpha), (tx, ty), radius, 3)
            _NS_emberwick._aacircle(surface, (*_NS_emberwick.PALETTE["fire_mid"], alpha), (tx, ty), max(1, radius - 4), 2)
            _NS_emberwick._aacircle(surface, (*_NS_emberwick.PALETTE["fire_hot"], alpha), (tx, ty), max(1, radius - 8), 1)
            for i in range(8):
                angle_s = i * math.pi / 4
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_emberwick.PALETTE["fire_hot"], alpha), (ex, ey, 2, 2))
    # ================= AMBIENT / GROUND =================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((160, 34), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 17 - radius, 140 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (10, 5, 3, 170), (5, 10, 150, 14))
        pygame.draw.ellipse(shadow, (60, 25, 10, 100), (12, 12, 136, 10))
        surface.blit(shadow, (x - 80, y - 17))
    def _draw_fire_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_emberwick._alpha((90 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_emberwick._aacircle(aura, (*_NS_emberwick.PALETTE["fire_dark"], alpha), (120, 100), radius)
        for radius in range(55, 5, -3):
            alpha = _NS_emberwick._alpha((55 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_emberwick._aacircle(aura, (*_NS_emberwick.PALETTE["fire_mid"], alpha), (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))
        # Floating fire embers.
        for i in range(14):
            angle = phase * 0.4 + i * math.pi / 7
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            sy -= int((phase * 8 + i * 5) % 22)
            color = _NS_emberwick.PALETTE["fire_mid"] if i % 2 == 0 else _NS_emberwick.PALETTE["fire_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_emberwick.PALETTE["fire_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((190, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_emberwick.PALETTE["fire_darkest"], 200), (5, 20, 180, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_emberwick.PALETTE["fire_dark"], 220), (14, 22, 162, 26), 2)
        pygame.draw.ellipse(ring, (*_NS_emberwick.PALETTE["fire_mid"], 180), (25, 24, 140, 22), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 95 + int(math.cos(angle) * 74)
            y1 = 35 + int(math.sin(angle) * 12)
            pygame.draw.rect(ring, _NS_emberwick.PALETTE["fire_hot"], (x1, y1, 2, 2))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_emberwick.PALETTE["fire_hot"], _NS_emberwick._alpha(150 * pulse)),
                                (15, 14, 160, 44), 1)
        surface.blit(ring, (x - 95, y - 30))
    def _draw_hover_particles(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Small fire embers rising below (floating effect)."""
        strength = 1.5 if intense else 1.0
        for i, offset in enumerate((-24, -14, -4, 6, 16, 26)):
            t = (phase * 0.5 + i * 0.15) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 22)
            alpha = _NS_emberwick._alpha(200 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_emberwick._aacircle(surface, (*_NS_emberwick.PALETTE["fire_dark"], alpha), (sx, sy), 3)
            _NS_emberwick._aacircle(surface, (*_NS_emberwick.PALETTE["fire_mid"], alpha), (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_emberwick.PALETTE["fire_hot"], alpha), (sx, sy - 1, 1, 1))
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_emberwick._alpha(160 - i * 30)
                if alpha <= 0:
                    continue
                _NS_emberwick._aacircle(surface, (*_NS_emberwick.PALETTE["fire_dark"], alpha),
                                        (sx, sy), max(2, 6 - i))
                _NS_emberwick._aacircle(surface, (*_NS_emberwick.PALETTE["fire_mid"], alpha),
                                        (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_emberwick.PALETTE["fire_hot"], alpha),
                                 (sx, sy - 1, 2, 1))
    # ================= SKILL Q — SCATTERBLAST =================
    def _draw_scatterblast(surface, boss, x, y, timer, phase):
        """Cone of shrapnel + heavy muzzle blast."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_emberwick._target_position(boss, x, y)
        muzzle_x = x + facing * 32
        muzzle_y = y - 8
        if progress < 0.25:
            # Charge up.
            t = progress / 0.25
            cr = int(3 + t * 12)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_emberwick._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_emberwick._aacircle(surface, (*_NS_emberwick.PALETTE["fire_dark"], alpha),
                                        (muzzle_x, muzzle_y), r)
            _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["fire_mid"], (muzzle_x, muzzle_y), cr - 2)
            _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["fire_hot"], (muzzle_x, muzzle_y), max(1, cr - 4))
            _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["fire_shine"], (muzzle_x, muzzle_y), max(1, cr - 6))
        else:
            # BLAST!
            t = (progress - 0.25) / 0.75
            # Massive cone.
            cone_len = int(40 + t * 180)
            cone_width = int(20 + t * 50)
            alpha_base = _NS_emberwick._alpha(240 * (1 - t))
            FX_W, FX_H = 300, 200
            fx_surf = pygame.Surface((FX_W, FX_H), pygame.SRCALPHA)
            ox, oy = 40, FX_H // 2
            for color, r_mult, alpha_mult in [
                (_NS_emberwick.PALETTE["fire_darkest"], 1.15, 0.4),
                (_NS_emberwick.PALETTE["fire_dark"], 1.0, 0.6),
                (_NS_emberwick.PALETTE["fire_mid"], 0.85, 0.8),
                (_NS_emberwick.PALETTE["fire_light"], 0.7, 0.95),
                (_NS_emberwick.PALETTE["fire_hot"], 0.5, 1.0),
                (_NS_emberwick.PALETTE["fire_shine"], 0.3, 1.0),
            ]:
                cl = int(cone_len * r_mult)
                cw = int(cone_width * r_mult * 0.5)
                la = _NS_emberwick._alpha(alpha_base * alpha_mult)
                if la <= 0:
                    continue
                cone_shape = [
                    (ox, oy),
                    (ox + facing * (cl // 3), oy - cw),
                    (ox + facing * cl, oy - cw // 2),
                    (ox + facing * (cl + 6), oy),
                    (ox + facing * cl, oy + cw // 2),
                    (ox + facing * (cl // 3), oy + cw),
                ]
                pygame.draw.polygon(fx_surf, (*color, la), cone_shape)
            # Shrapnel pellets.
            for i in range(25):
                pellet_seed = i * 0.3
                pellet_angle = math.sin(pellet_seed) * 0.7
                pellet_r = int((cone_len * 0.3) + (i % 8) * (cone_len * 0.1))
                px = ox + int(math.cos(pellet_angle) * pellet_r) * facing
                py = oy + int(math.sin(pellet_angle) * pellet_r)
                pygame.draw.rect(fx_surf, (*_NS_emberwick.PALETTE["iron_darkest"], alpha_base), (px - 1, py - 1, 3, 3))
                pygame.draw.rect(fx_surf, (*_NS_emberwick.PALETTE["fire_hot"], alpha_base), (px, py, 2, 2))
                pygame.draw.rect(fx_surf, (*_NS_emberwick.PALETTE["fire_shine"], alpha_base), (px, py, 1, 1))
            surface.blit(fx_surf, (muzzle_x - ox, muzzle_y - oy))
    # ================= SKILL W — FIRESNAP COOKIE =================
    def _draw_cookie_ground(surface, boss, x, y, timer, phase):
        """Acid pool where cookie lands."""
        tx, ty = _NS_emberwick._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Cookie flies first half, pool remains second half.
        if progress > 0.4:
            pool_t = (progress - 0.4) / 0.6
            r = int(45 * min(1.0, pool_t * 3))
            if r > 3:
                pygame.draw.ellipse(surface, (*_NS_emberwick.PALETTE["acid_dark"], 200),
                                    (tx - r, ty - r // 3, r * 2, r * 2 // 3))
                pygame.draw.ellipse(surface, (*_NS_emberwick.PALETTE["acid_mid"], 180),
                                    (tx - r + 3, ty - r // 3 + 2, r * 2 - 6, r * 2 // 3 - 4))
                pygame.draw.ellipse(surface, (*_NS_emberwick.PALETTE["acid_light"], 130),
                                    (tx - r + 8, ty - r // 3 + 4, r * 2 - 16, r * 2 // 3 - 8))
    def _draw_cookie_projectile(surface, boss, x, y, timer, phase):
        """Cookie arcing through air + acid bubbles."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_emberwick._target_position(boss, x, y)
        if progress < 0.4:
            # Cookie in flight (arc).
            t = progress / 0.4
            start_x = x + facing * 32
            start_y = y - 12
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t) - int(math.sin(t * math.pi) * 30)  # arc
            # Cookie body (round brown with chocolate chips).
            _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["shadow_deep"], (bx + 1, by + 1), 7)
            _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["cookie_dark"], (bx, by), 7)
            _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["cookie_mid"], (bx, by), 6)
            _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["cookie_light"], (bx - 1, by - 1), 4)
            # Chocolate chips.
            for chip in [(-3, -2), (2, -1), (0, 2), (3, 2), (-2, 3)]:
                pygame.draw.rect(surface, _NS_emberwick.PALETTE["cookie_dark"],
                                 (bx + chip[0], by + chip[1], 2, 2))
                pygame.draw.rect(surface, _NS_emberwick.PALETTE["black"],
                                 (bx + chip[0], by + chip[1], 1, 1))
            # Acid glow trail.
            for i in range(1, 5):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t) - int(math.sin(trail_t * math.pi) * 30)
                alpha = _NS_emberwick._alpha(180 - i * 30)
                _NS_emberwick._aacircle(surface, (*_NS_emberwick.PALETTE["acid_mid"], alpha),
                                        (px, py), max(1, 5 - i))
                pygame.draw.rect(surface, (*_NS_emberwick.PALETTE["acid_light"], alpha),
                                 (px, py, 1, 1))
            # Rotating sparks.
            for i in range(4):
                sa = phase * 3 + i * math.pi / 2
                sx = bx + int(math.cos(sa) * 9)
                sy = by + int(math.sin(sa) * 9)
                pygame.draw.rect(surface, _NS_emberwick.PALETTE["acid_hot"], (sx, sy, 1, 1))
        else:
            # Acid pool bubbles at target.
            pool_t = (progress - 0.4) / 0.6
            r = int(45 * min(1.0, pool_t * 3))
            if r > 5:
                for i in range(10):
                    bubble_t = (phase * 0.6 + i * 0.13) % 1.0
                    ba = i * math.pi / 5
                    br = int(r * 0.4)
                    bx = tx + int(math.cos(ba) * br)
                    by = ty + int(math.sin(ba) * br * 0.5) - int(bubble_t * 20)
                    alpha = _NS_emberwick._alpha(200 * (1 - bubble_t))
                    _NS_emberwick._aacircle(surface, (*_NS_emberwick.PALETTE["acid_dark"], alpha), (bx, by), 3)
                    _NS_emberwick._aacircle(surface, (*_NS_emberwick.PALETTE["acid_mid"], alpha), (bx, by - 1), 2)
                    pygame.draw.rect(surface, (*_NS_emberwick.PALETTE["acid_hot"], alpha), (bx, by - 2, 1, 1))
    # ================= SKILL E — GNASH & SPIT =================
    def _draw_gnash_spit(surface, boss, x, y, timer, phase):
        """Tongue lash to target then spit back."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_emberwick._target_position(boss, x, y)
        mouth_x = x + facing * 30
        mouth_y = y + 4
        if progress < 0.4:
            # Tongue extends toward target.
            t = progress / 0.4
            end_x = int(mouth_x + (tx - mouth_x) * t)
            end_y = int(mouth_y + (ty - mouth_y) * t)
            # Green sticky tongue.
            segments = 10
            for i in range(segments):
                t1 = i / segments
                t2 = (i + 1) / segments
                wave = math.sin(phase * 4 + i * 0.6) * 3
                px1 = int(mouth_x + (end_x - mouth_x) * t1)
                py1 = int(mouth_y + (end_y - mouth_y) * t1 + wave)
                px2 = int(mouth_x + (end_x - mouth_x) * t2)
                py2 = int(mouth_y + (end_y - mouth_y) * t2 + math.sin(phase * 4 + (i + 1) * 0.6) * 3)
                pygame.draw.line(surface, _NS_emberwick.PALETTE["acid_dark"], (px1, py1), (px2, py2), 5)
                pygame.draw.line(surface, _NS_emberwick.PALETTE["fire_dark"], (px1, py1), (px2, py2), 3)
                pygame.draw.line(surface, _NS_emberwick.PALETTE["fire_mid"], (px1, py1 - 1), (px2, py2 - 1), 1)
            # Tongue tip = green blob.
            _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["acid_dark"], (end_x, end_y), 6)
            _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["acid_mid"], (end_x, end_y), 4)
            _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["acid_light"], (end_x - 1, end_y - 1), 2)
            pygame.draw.rect(surface, _NS_emberwick.PALETTE["acid_hot"], (end_x, end_y, 1, 1))
        elif progress < 0.7:
            # Holding target.
            t = (progress - 0.4) / 0.3
            # Small pulsing chomp effect at mouth.
            pulse_r = int(8 + math.sin(phase * 6) * 3)
            for r in range(pulse_r, 0, -2):
                alpha = _NS_emberwick._alpha(180 * (pulse_r - r) / pulse_r)
                _NS_emberwick._aacircle(surface, (*_NS_emberwick.PALETTE["fire_dark"], alpha),
                                        (mouth_x, mouth_y), r)
            _NS_emberwick._aacircle(surface, _NS_emberwick.PALETTE["fire_mid"], (mouth_x, mouth_y), 3)
        else:
            # SPIT out (projectile shot forward).
            t = (progress - 0.7) / 0.3
            spit_x = int(mouth_x + facing * t * 200)
            spit_y = mouth_y
            # Spit trail.
            for i in range(8):
                trail_t = max(0.0, t - i * 0.05)
                if trail_t <= 0:
                    continue
                px = int(mouth_x + facing * trail_t * 200)
                alpha = _NS_emberwick._alpha(230 - i * 25)
                size = max(1, 8 - i)
                _NS_emberwick._aacircle(surface, (*_NS_emberwick.PALETTE["acid_dark"], alpha), (px, spit_y), size)
                _NS_emberwick._aacircle(surface, (*_NS_emberwick.PALETTE["acid_mid"], alpha), (px, spit_y),
                                        max(1, size - 2))
                pygame.draw.rect(surface, (*_NS_emberwick.PALETTE["acid_hot"], alpha), (px, spit_y, 2, 2))
    # ================= SKILL R — EMBER KISS BARRAGE =================
    def _draw_ember_kiss_ground(surface, boss, x, y, timer, phase):
        """Burning ground path from lizard mouth."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        stream_len = int(220 * min(1.0, progress * 2))
        start_x = x + facing * 32
        start_y = y + 8
        # Charred ground path.
        for i in range(0, stream_len, 8):
            wave = math.sin(phase * 3 + i * 0.1) * 4
            px = start_x + facing * i
            py = start_y + int(wave)
            r = int(6 + math.sin(phase * 2 + i * 0.05) * 2)
            pygame.draw.ellipse(surface, (*_NS_emberwick.PALETTE["fire_darkest"], 200),
                                (px - r, py - r // 2, r * 2, r))
    def _draw_ember_kiss_stream(surface, boss, x, y, timer, phase):
        """Continuous flame stream from lizard mouth."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        mouth_x = x + facing * 32
        mouth_y = y + 4
        # Stream length grows then holds.
        max_len = 240
        stream_len = int(max_len * min(1.0, progress * 2))
        # Draw flame stream as sequence of rising flame puffs.
        FX_W, FX_H = 300, 180
        fx_surf = pygame.Surface((FX_W, FX_H), pygame.SRCALPHA)
        ox, oy = 40, FX_H // 2
        # Base flame trail (undulating).
        num_puffs = 30
        for i in range(num_puffs):
            t = i / num_puffs
            if t * max_len > stream_len:
                break
            dist = t * max_len
            wave = math.sin(phase * 4 + i * 0.4) * (6 + t * 8)
            puff_x = ox + facing * int(dist)
            puff_y = oy + int(wave)
            puff_r = int(8 + t * 6 + math.sin(phase * 3 + i) * 2)
            alpha_puff = _NS_emberwick._alpha(230)
            # Layered puff.
            for color, radius_mult in [
                (_NS_emberwick.PALETTE["fire_darkest"], 1.1),
                (_NS_emberwick.PALETTE["fire_dark"], 0.95),
                (_NS_emberwick.PALETTE["fire_mid"], 0.8),
                (_NS_emberwick.PALETTE["fire_light"], 0.6),
                (_NS_emberwick.PALETTE["fire_hot"], 0.4),
            ]:
                r_ = int(puff_r * radius_mult)
                pygame.draw.circle(fx_surf, (*color, alpha_puff), (puff_x, puff_y), r_)
            # Bright core sparkles.
            if i % 3 == 0:
                pygame.draw.rect(fx_surf, (*_NS_emberwick.PALETTE["fire_shine"], alpha_puff),
                                 (puff_x, puff_y, 2, 2))
        # Rising embers.
        for i in range(20):
            t = i / 20
            if t * max_len > stream_len:
                break
            dist = t * max_len
            ember_rise = ((phase * 20 + i * 3) % 30)
            ex = ox + facing * int(dist) + int(math.sin(phase * 2 + i) * 5)
            ey = oy - int(ember_rise)
            alpha = _NS_emberwick._alpha(230 * (1 - ember_rise / 30))
            pygame.draw.rect(fx_surf, (*_NS_emberwick.PALETTE["fire_mid"], alpha), (ex, ey, 2, 2))
            pygame.draw.rect(fx_surf, (*_NS_emberwick.PALETTE["fire_hot"], alpha), (ex, ey, 1, 1))
        surface.blit(fx_surf, (mouth_x - ox, mouth_y - oy))



# ====================================================================
# GRONDARTHUL (TROLL KING) - Mini Boss
# ====================================================================

class _NS_grondarthul:
    """Namespace grondarthul - Troll King boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Troll skin (blue-grey)
        "skin_darkest": (15, 25, 40),
        "skin_dark": (50, 75, 95),
        "skin_mid": (100, 130, 150),
        "skin_light": (155, 180, 195),
        "skin_edge": (200, 220, 230),
        "skin_shine": (235, 245, 250),
        # Belly (lighter grey)
        "belly_dark": (75, 90, 105),
        "belly_mid": (145, 160, 170),
        "belly_light": (200, 210, 215),
        # Hair (magenta/pink mohawk)
        "hair_darkest": (60, 15, 35),
        "hair_dark": (140, 30, 65),
        "hair_mid": (210, 55, 100),
        "hair_light": (255, 110, 155),
        "hair_shine": (255, 180, 200),
        # Fur/collar (dark brown/grey)
        "fur_dark": (35, 30, 25),
        "fur_mid": (75, 65, 55),
        "fur_light": (130, 115, 95),
        # Leather straps/loincloth (brown)
        "leather_dark": (35, 22, 12),
        "leather_mid": (85, 60, 30),
        "leather_light": (145, 105, 60),
        "leather_shine": (200, 160, 100),
        # Metal accents
        "metal_dark": (25, 25, 30),
        "metal_mid": (75, 75, 85),
        "metal_light": (150, 150, 160),
        "metal_shine": (220, 220, 235),
        # Ice cyan (main effect - weapon, skills)
        "ice_darkest": (5, 25, 55),
        "ice_dark": (20, 80, 145),
        "ice_mid": (60, 165, 235),
        "ice_light": (150, 220, 255),
        "ice_hot": (210, 245, 255),
        "ice_shine": (240, 255, 255),
        # Fangs/claws (yellowed bone)
        "fang_dark": (60, 50, 30),
        "fang_mid": (155, 135, 85),
        "fang_light": (230, 215, 165),
        "fang_shine": (255, 250, 220),
        # Eye (glowing cyan-white)
        "eye_socket": (2, 8, 15),
        "eye_dark": (15, 60, 110),
        "eye_light": (140, 220, 255),
        "eye_glow": (240, 250, 255),
        # Snow/frost particles
        "frost_light": (220, 240, 255),
        "shadow": (0, 0, 0),
        "shadow_deep": (1, 3, 6),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_grondarthul._clamp(color)
        if _NS_grondarthul.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_grondarthul._clamp(color)
        if _NS_grondarthul.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_grondarthul._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 180 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_grondarthul(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_grondarthul._update_gro_attack_anim(boss)
        attacking = bool(getattr(boss, "_gro_attack_active", False))
        moving = _NS_grondarthul._detect_moving(boss)
        # ===== LAYER 1: BACKGROUND =====
        _NS_grondarthul._draw_frost_aura(surface, x, y, pulse)
        _NS_grondarthul._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # ===== LAYER 2: SKILL GROUND FX (behind body) =====
        if active_skill == "w":
            _NS_grondarthul._draw_frozendomain_ground(surface, boss, x, y,
                                                      skill_timer, pulse)
        elif active_skill == "r":
            _NS_grondarthul._draw_subjugate_ground(surface, boss, x, y,
                                                   skill_timer, pulse)
        # ===== LAYER 3: SNOW PARTICLES =====
        _NS_grondarthul._draw_snow_particles(surface, x, y, pulse)
        # ===== LAYER 4: SHADOW + BODY =====
        if attacking:
            _NS_grondarthul._draw_gro_attack(surface, boss, x, y, active_skill)
        elif moving:
            _NS_grondarthul._draw_gro_walk(surface, boss, x, y, active_skill)
        else:
            _NS_grondarthul._draw_gro_idle(surface, boss, x, y, active_skill)
        # ===== LAYER 5: FOREGROUND FX =====
        if attacking and not active_skill:
            _NS_grondarthul._draw_basic_attack_fx(surface, boss, x, y)
        if active_skill == "q":
            _NS_grondarthul._draw_chomp_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_grondarthul._draw_frozendomain_fx(surface, boss, x, y,
                                                   skill_timer, pulse)
        elif active_skill == "e":
            _NS_grondarthul._draw_pillarofice_fx(surface, boss, x, y,
                                                  skill_timer, pulse)
        elif active_skill == "r":
            _NS_grondarthul._draw_subjugate_fx(surface, boss, x, y,
                                                skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_gro_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_gro_previous_timer", timer))
        active = bool(getattr(boss, "_gro_attack_active", False))
        just_reset = (previous > cooldown - 5 and timer < 3)
        near_max = (timer >= cooldown - 1)
        if (just_reset or near_max) and not active:
            boss._gro_attack_active = True
            boss._gro_attack_frame = 0
            active = True
        if active:
            boss._gro_attack_frame = int(getattr(boss, "_gro_attack_frame", 0)) + 1
            attack_duration = 32
            if boss._gro_attack_frame >= attack_duration:
                boss._gro_attack_active = False
                boss._gro_attack_frame = 0
                active = False
        boss._gro_previous_timer = timer
        if active:
            attack_duration = 32
            boss._gro_attack_progress = min(1.0,
                boss._gro_attack_frame / attack_duration)
        else:
            boss._gro_attack_progress = 0.0
    def _detect_moving(boss):
        if not hasattr(boss, "_gro_last_x"):
            boss._gro_last_x = boss.x
            boss._gro_last_y = boss.y
            return False
        dx = abs(boss.x - boss._gro_last_x)
        dy = abs(boss.y - boss._gro_last_y)
        boss._gro_last_x = boss.x
        boss._gro_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_gro_idle(surface, boss, x, y, active_skill):
        breath = int(math.sin(boss.pulse * 0.5) * 2)
        _NS_grondarthul._draw_shadow(surface, x, y + 52)
        _NS_grondarthul._draw_gro_body(surface, x, y + breath, boss.direction,
                                       boss.pulse, "idle",
                                       active_skill=active_skill)
    def _draw_gro_walk(surface, boss, x, y, active_skill):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 1.2) * 3)
        _NS_grondarthul._draw_shadow(surface, x, y + 52)
        _NS_grondarthul._draw_gro_body(surface, x, y + bob, boss.direction,
                                       phase, "walk",
                                       active_skill=active_skill)
    def _draw_gro_attack(surface, boss, x, y, active_skill):
        """Big club overhead smash."""
        progress = getattr(boss, "_gro_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        facing = boss.direction
        # Rear back → smash down → recover
        if progress < 0.4:
            t = progress / 0.4
            lunge = -int(t * 4) * facing
            lift = int(t * 5)  # rise up
        elif progress < 0.65:
            t = (progress - 0.4) / 0.25
            lunge = int((-4 + t * 18)) * facing
            lift = int(5 - t * 8)  # SLAM down
        else:
            t = (progress - 0.65) / 0.35
            lunge = int(14 * (1 - t)) * facing
            lift = int(-3 + t * 3)
        _NS_grondarthul._draw_shadow(surface, x + lunge, y + 52)
        _NS_grondarthul._draw_gro_body(surface, x + lunge, y - lift, facing,
                                       boss.pulse, "attack", progress,
                                       active_skill=active_skill)
    # ============================================================
    # BODY (Humanoid troll brute)
    # ============================================================
    def _draw_gro_body(surface, cx, cy, facing, phase, action,
                        attack_progress=0, active_skill=None):
        """Full body: legs, torso, arms with ice club, head with mohawk."""
        # Legs (bottom)
        _NS_grondarthul._draw_troll_legs(surface, cx, cy + 12, facing, phase, action)
        # Loincloth
        _NS_grondarthul._draw_loincloth(surface, cx, cy + 10, facing, phase, action)
        # Torso
        _NS_grondarthul._draw_torso(surface, cx, cy - 2, facing, phase)
        # Fur collar/shoulders
        _NS_grondarthul._draw_fur_collar(surface, cx, cy - 8, facing, phase)
        # Left arm (empty hand, back)
        _NS_grondarthul._draw_left_arm(surface, cx, cy - 4, facing, phase, action,
                                        attack_progress)
        # Head
        _NS_grondarthul._draw_head(surface, cx, cy - 18, facing, phase)
        # Mohawk (magenta)
        _NS_grondarthul._draw_mohawk(surface, cx, cy - 24, facing, phase)
        # RIGHT ARM with GIANT ICE CLUB (main visual)
        _NS_grondarthul._draw_right_arm_with_club(surface, cx, cy - 4, facing,
                                                    phase, action, attack_progress)
    def _draw_troll_legs(surface, cx, cy, facing, phase, action):
        """Thick troll legs."""
        step_offset = 0
        if action == "walk":
            step_offset = int(math.sin(phase * 1.5) * 3)
        for leg_i, (side, offset_x) in enumerate([(-1, -5), (1, 5)]):
            leg_offset = step_offset if leg_i == 0 else -step_offset
            leg_top_x = cx + offset_x
            leg_top_y = cy - 4
            leg_bot_x = leg_top_x + leg_offset // 2
            leg_bot_y = cy + 12
            # Thick leg (skin)
            _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["shadow_deep"],
                                     (leg_top_x + 2, leg_top_y + 2),
                                     (leg_bot_x + 2, leg_bot_y + 2), 9)
            _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["skin_darkest"],
                                     (leg_top_x, leg_top_y),
                                     (leg_bot_x, leg_bot_y), 8)
            _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["skin_dark"],
                                     (leg_top_x, leg_top_y),
                                     (leg_bot_x, leg_bot_y), 6)
            _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["skin_mid"],
                                     (leg_top_x - 1, leg_top_y),
                                     (leg_bot_x - 1, leg_bot_y), 3)
            _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["skin_light"],
                                     (leg_top_x - 2, leg_top_y),
                                     (leg_bot_x - 2, leg_bot_y), 1)
            # Leather wrap on shin
            wrap_y = leg_top_y + 6
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["leather_dark"],
                             (leg_top_x - 3, wrap_y, 6, 3))
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["leather_mid"],
                             (leg_top_x - 3, wrap_y, 6, 2))
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["leather_light"],
                             (leg_top_x - 2, wrap_y, 4, 1))
            # Foot with claws
            foot_x = leg_bot_x
            foot_y = leg_bot_y
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["shadow_deep"], [
                (foot_x - 5, foot_y + 1),
                (foot_x + 6, foot_y + 1),
                (foot_x + 5, foot_y + 5),
                (foot_x - 5, foot_y + 5),
            ])
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["skin_darkest"], [
                (foot_x - 5, foot_y),
                (foot_x + 6, foot_y),
                (foot_x + 5, foot_y + 4),
                (foot_x - 5, foot_y + 4),
            ])
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["skin_dark"], [
                (foot_x - 4, foot_y + 1),
                (foot_x + 5, foot_y + 1),
                (foot_x + 4, foot_y + 3),
                (foot_x - 4, foot_y + 3),
            ])
            # Toe claws
            for cx_off in (-3, 0, 3):
                claw_x = foot_x + cx_off + facing
                claw_y = foot_y + 3
                _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["fang_dark"], [
                    (claw_x, claw_y),
                    (claw_x + facing, claw_y + 3),
                    (claw_x + facing * 2, claw_y),
                ])
                pygame.draw.rect(surface, _NS_grondarthul.PALETTE["fang_light"],
                                 (claw_x + facing, claw_y + 2, 1, 1))
    def _draw_loincloth(surface, cx, cy, facing, phase, action):
        """Brown leather loincloth."""
        sway = 0
        if action == "walk":
            sway = int(math.sin(phase * 1.5) * 1)
        loin_pts = [
            (cx - 8, cy - 2),
            (cx + 8, cy - 2),
            (cx + 10 + sway, cy + 6),
            (cx + 5, cy + 10),
            (cx - 5, cy + 10),
            (cx - 10 - sway, cy + 6),
        ]
        _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["shadow_deep"],
                              [(px + 2, py + 2) for px, py in loin_pts])
        _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["leather_dark"],
                              loin_pts)
        _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["leather_mid"], [
            (cx - 7, cy - 1),
            (cx + 7, cy - 1),
            (cx + 9 + sway, cy + 5),
            (cx + 4, cy + 9),
            (cx - 4, cy + 9),
            (cx - 9 - sway, cy + 5),
        ])
        _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["leather_light"], [
            (cx - 5, cy),
            (cx + 5, cy),
            (cx + 6, cy + 4),
            (cx + 2, cy + 7),
            (cx - 2, cy + 7),
            (cx - 6, cy + 4),
        ])
        # Belt (with metal buckle)
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["leather_dark"],
                         (cx - 10, cy - 3, 20, 3))
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["leather_mid"],
                         (cx - 10, cy - 3, 20, 2))
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["leather_light"],
                         (cx - 9, cy - 3, 18, 1))
        # Metal buckle center
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["metal_dark"],
                         (cx - 2, cy - 3, 5, 3))
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["metal_mid"],
                         (cx - 1, cy - 3, 3, 2))
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["metal_shine"],
                         (cx, cy - 3, 1, 1))
        # Straps hanging
        for x_off in (-6, 6):
            strap_x = cx + x_off
            pygame.draw.line(surface, _NS_grondarthul.PALETTE["leather_dark"],
                             (strap_x, cy - 1), (strap_x + sway, cy + 12), 2)
            pygame.draw.line(surface, _NS_grondarthul.PALETTE["leather_mid"],
                             (strap_x, cy - 1), (strap_x + sway, cy + 12), 1)
    def _draw_torso(surface, cx, cy, facing, phase):
        """Muscular troll torso."""
        torso_pts = [
            (cx - 12, cy - 6),
            (cx - 14, cy),
            (cx - 12, cy + 8),
            (cx - 6, cy + 14),
            (cx + 6, cy + 14),
            (cx + 12, cy + 8),
            (cx + 14, cy),
            (cx + 12, cy - 6),
        ]
        _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["shadow_deep"],
                              [(px + 2, py + 2) for px, py in torso_pts])
        _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["skin_darkest"],
                              torso_pts)
        _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["skin_dark"], [
            (cx - 11, cy - 5),
            (cx - 13, cy),
            (cx - 11, cy + 7),
            (cx - 5, cy + 13),
            (cx + 5, cy + 13),
            (cx + 11, cy + 7),
            (cx + 13, cy),
            (cx + 11, cy - 5),
        ])
        _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["skin_mid"], [
            (cx - 8, cy - 3),
            (cx - 10, cy + 1),
            (cx - 8, cy + 6),
            (cx - 3, cy + 11),
            (cx + 3, cy + 11),
            (cx + 8, cy + 6),
            (cx + 10, cy + 1),
            (cx + 8, cy - 3),
        ])
        # Muscle highlight (center chest)
        _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["skin_light"], [
            (cx - 4, cy - 1),
            (cx - 5, cy + 3),
            (cx - 3, cy + 8),
            (cx + 3, cy + 8),
            (cx + 5, cy + 3),
            (cx + 4, cy - 1),
        ])
        # Abs definition
        pygame.draw.line(surface, _NS_grondarthul.PALETTE["skin_darkest"],
                         (cx, cy + 2), (cx, cy + 12), 1)
        for y_off in (4, 7, 10):
            pygame.draw.line(surface, _NS_grondarthul.PALETTE["skin_darkest"],
                             (cx - 5, cy + y_off), (cx - 1, cy + y_off), 1)
            pygame.draw.line(surface, _NS_grondarthul.PALETTE["skin_darkest"],
                             (cx + 1, cy + y_off), (cx + 5, cy + y_off), 1)
        # Chest highlights
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["skin_edge"],
                         (cx - 2, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["skin_edge"],
                         (cx + 1, cy - 1, 1, 1))
        # Battle scars (a few white lines)
        pygame.draw.line(surface, _NS_grondarthul.PALETTE["skin_edge"],
                         (cx - 8, cy + 3), (cx - 5, cy + 6), 1)
        pygame.draw.line(surface, _NS_grondarthul.PALETTE["skin_light"],
                         (cx + 6, cy - 2), (cx + 10, cy + 1), 1)
    def _draw_fur_collar(surface, cx, cy, facing, phase):
        """Shaggy fur collar around shoulders/neck."""
        # Wide shaggy fur
        for angle_deg in range(-100, 101, 15):
            angle = math.radians(angle_deg)
            fur_len = 6 + int(math.sin(phase + angle_deg * 0.05) * 1)
            fx1 = cx + int(math.cos(angle) * 12)
            fy1 = cy - int(math.sin(angle) * 6)
            fx2 = cx + int(math.cos(angle) * (12 + fur_len))
            fy2 = cy - int(math.sin(angle) * (6 + fur_len // 2))
            pygame.draw.line(surface, _NS_grondarthul.PALETTE["fur_dark"],
                             (fx1, fy1), (fx2, fy2), 3)
            pygame.draw.line(surface, _NS_grondarthul.PALETTE["fur_mid"],
                             (fx1, fy1), (fx2, fy2), 2)
            pygame.draw.line(surface, _NS_grondarthul.PALETTE["fur_light"],
                             (fx1, fy1), (fx2, fy2), 1)
        # Main fur ellipse (base)
        pygame.draw.ellipse(surface, _NS_grondarthul.PALETTE["shadow_deep"],
                            (cx - 13, cy - 4, 26, 12))
        pygame.draw.ellipse(surface, _NS_grondarthul.PALETTE["fur_dark"],
                            (cx - 12, cy - 4, 24, 11))
        pygame.draw.ellipse(surface, _NS_grondarthul.PALETTE["fur_mid"],
                            (cx - 10, cy - 3, 20, 9))
        pygame.draw.ellipse(surface, _NS_grondarthul.PALETTE["fur_light"],
                            (cx - 6, cy - 2, 12, 4))
    def _draw_left_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Left arm - free hand, mostly behind body."""
        shoulder_x = cx - facing * 11
        shoulder_y = cy - 2
        # Hand position
        if action == "attack":
            # Balancing arm during swing
            hand_x = shoulder_x - facing * (4 + int(attack_progress * 3))
            hand_y = shoulder_y + 12 - int(attack_progress * 4)
        else:
            hand_x = shoulder_x - facing * 3 + int(math.sin(phase * 0.5) * 1)
            hand_y = shoulder_y + 16
        elbow_x = int((shoulder_x + hand_x) / 2) - facing * 2
        elbow_y = int((shoulder_y + hand_y) / 2) + 2
        # Upper arm (thick muscular)
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["shadow_deep"],
                                 (shoulder_x + 1, shoulder_y + 1),
                                 (elbow_x + 1, elbow_y + 1), 7)
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["skin_darkest"],
                                 (shoulder_x, shoulder_y),
                                 (elbow_x, elbow_y), 6)
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["skin_dark"],
                                 (shoulder_x, shoulder_y),
                                 (elbow_x, elbow_y), 4)
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["skin_mid"],
                                 (shoulder_x - 1, shoulder_y),
                                 (elbow_x - 1, elbow_y), 2)
        # Forearm
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["shadow_deep"],
                                 (elbow_x + 1, elbow_y + 1),
                                 (hand_x + 1, hand_y + 1), 6)
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["skin_darkest"],
                                 (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["skin_dark"],
                                 (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["skin_mid"],
                                 (elbow_x - 1, elbow_y),
                                 (hand_x - 1, hand_y), 1)
        # Leather wristband
        wrist_x = int((elbow_x + hand_x) / 2)
        wrist_y = int((elbow_y + hand_y) / 2)
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["leather_dark"],
                         (wrist_x - 3, wrist_y - 1, 6, 3))
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["leather_mid"],
                         (wrist_x - 3, wrist_y - 1, 6, 2))
        # Fist
        _NS_grondarthul._aacircle(surface, _NS_grondarthul.PALETTE["shadow_deep"],
                                   (hand_x + 1, hand_y + 1), 4)
        _NS_grondarthul._aacircle(surface, _NS_grondarthul.PALETTE["skin_darkest"],
                                   (hand_x, hand_y), 4)
        _NS_grondarthul._aacircle(surface, _NS_grondarthul.PALETTE["skin_dark"],
                                   (hand_x, hand_y), 3)
        _NS_grondarthul._aacircle(surface, _NS_grondarthul.PALETTE["skin_mid"],
                                   (hand_x - 1, hand_y - 1), 2)
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["skin_light"],
                         (hand_x - 1, hand_y - 1, 1, 1))
        # Small claws on fist
        for i in range(3):
            claw_x = hand_x - 2 + i * 2
            claw_y = hand_y + 3
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["fang_dark"],
                             (claw_x, claw_y, 1, 2))
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["fang_light"],
                             (claw_x, claw_y + 1, 1, 1))
    def _draw_right_arm_with_club(surface, cx, cy, facing, phase, action,
                                    attack_progress):
        """Right arm holding GIANT ICE CLUB."""
        shoulder_x = cx + facing * 11
        shoulder_y = cy - 2
        # Club angle changes during attack
        if action == "attack":
            if attack_progress < 0.4:
                # REAR BACK (raise club overhead)
                t = attack_progress / 0.4
                club_angle = math.radians(-90) - t * math.radians(60) * facing
            elif attack_progress < 0.65:
                # SMASH DOWN
                t = (attack_progress - 0.4) / 0.25
                start_a = math.radians(-150) if facing == 1 else math.radians(-30)
                end_a = math.radians(30) if facing == 1 else math.radians(-210)
                club_angle = start_a + (end_a - start_a) * t
            else:
                # Recovery (return to rest)
                t = (attack_progress - 0.65) / 0.35
                club_angle = math.radians(30) if facing == 1 else math.radians(-210)
                club_angle -= t * math.radians(60) * facing
        else:
            # Idle: club rests on shoulder (angled up)
            club_angle = math.radians(-60) if facing == 1 else math.radians(-120)
            club_angle += math.sin(phase * 0.5) * math.radians(3)
        # Hand position based on club angle
        hand_dist = 10
        hand_x = shoulder_x + int(math.cos(club_angle) * hand_dist)
        hand_y = shoulder_y + int(math.sin(club_angle) * hand_dist)
        # Elbow
        elbow_x = int((shoulder_x + hand_x) / 2) + facing * 3
        elbow_y = int((shoulder_y + hand_y) / 2) + 1
        # Upper arm (very thick and muscular)
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["shadow_deep"],
                                 (shoulder_x + 1, shoulder_y + 1),
                                 (elbow_x + 1, elbow_y + 1), 8)
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["skin_darkest"],
                                 (shoulder_x, shoulder_y),
                                 (elbow_x, elbow_y), 7)
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["skin_dark"],
                                 (shoulder_x, shoulder_y),
                                 (elbow_x, elbow_y), 5)
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["skin_mid"],
                                 (shoulder_x - 1, shoulder_y),
                                 (elbow_x - 1, elbow_y), 3)
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["skin_light"],
                                 (shoulder_x - 2, shoulder_y),
                                 (elbow_x - 2, elbow_y), 1)
        # Forearm
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["shadow_deep"],
                                 (elbow_x + 1, elbow_y + 1),
                                 (hand_x + 1, hand_y + 1), 7)
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["skin_darkest"],
                                 (elbow_x, elbow_y), (hand_x, hand_y), 6)
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["skin_dark"],
                                 (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["skin_mid"],
                                 (elbow_x - 1, elbow_y),
                                 (hand_x - 1, hand_y), 2)
        # Leather wristband
        wrist_x = int((elbow_x + hand_x) / 2)
        wrist_y = int((elbow_y + hand_y) / 2)
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["leather_dark"],
                         (wrist_x - 3, wrist_y - 2, 6, 4))
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["leather_mid"],
                         (wrist_x - 3, wrist_y - 2, 6, 3))
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["leather_shine"],
                         (wrist_x, wrist_y - 2, 1, 1))
        # Fist gripping club
        _NS_grondarthul._aacircle(surface, _NS_grondarthul.PALETTE["shadow_deep"],
                                   (hand_x + 1, hand_y + 1), 4)
        _NS_grondarthul._aacircle(surface, _NS_grondarthul.PALETTE["skin_darkest"],
                                   (hand_x, hand_y), 4)
        _NS_grondarthul._aacircle(surface, _NS_grondarthul.PALETTE["skin_dark"],
                                   (hand_x, hand_y), 3)
        # THE GIANT ICE CLUB
        _NS_grondarthul._draw_ice_club(surface, hand_x, hand_y, club_angle,
                                        facing, phase, action)
    def _draw_ice_club(surface, hand_x, hand_y, angle, facing, phase, action):
        """Massive ice club/hammer weapon."""
        # Club extends from hand outward at given angle
        perp = angle + math.pi / 2
        # HANDLE (leather-wrapped wood, short)
        handle_len = 8
        handle_end_x = hand_x + int(math.cos(angle) * handle_len)
        handle_end_y = hand_y + int(math.sin(angle) * handle_len)
        # Handle body
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["shadow_deep"],
                                 (hand_x + 1, hand_y + 1),
                                 (handle_end_x + 1, handle_end_y + 1), 5)
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["leather_dark"],
                                 (hand_x, hand_y),
                                 (handle_end_x, handle_end_y), 4)
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["leather_mid"],
                                 (hand_x, hand_y),
                                 (handle_end_x, handle_end_y), 3)
        _NS_grondarthul._aaline(surface, _NS_grondarthul.PALETTE["leather_light"],
                                 (hand_x - 1, hand_y),
                                 (handle_end_x - 1, handle_end_y), 1)
        # Handle wraps (visible bands)
        for i in range(1, 4):
            wrap_t = i / 4
            wx = hand_x + int(math.cos(angle) * handle_len * wrap_t)
            wy = hand_y + int(math.sin(angle) * handle_len * wrap_t)
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["leather_shine"],
                             (wx, wy, 1, 1))
        # Metal band at connection point
        _NS_grondarthul._aacircle(surface, _NS_grondarthul.PALETTE["metal_dark"],
                                   (handle_end_x, handle_end_y), 4)
        _NS_grondarthul._aacircle(surface, _NS_grondarthul.PALETTE["metal_mid"],
                                   (handle_end_x, handle_end_y), 3)
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["metal_shine"],
                         (handle_end_x, handle_end_y - 1, 1, 1))
        # BIG ICE CLUB HEAD (crystalline structure)
        # Extends further from handle end
        club_head_center_x = handle_end_x + int(math.cos(angle) * 12)
        club_head_center_y = handle_end_y + int(math.sin(angle) * 12)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Outer glow halo
        for r in range(18, 8, -2):
            alpha = _NS_grondarthul._alpha(80 * (18 - r) / 10 * pulse)
            _NS_grondarthul._aacircle(surface,
                                       (*_NS_grondarthul.PALETTE["ice_light"],
                                        alpha),
                                       (club_head_center_x, club_head_center_y), r)
        # Ice club head - angular crystal shape
        # 3 main spikes radiating from center
        num_spikes = 6
        for i in range(num_spikes):
            spike_a = angle + i * math.pi / 3
            spike_len = 12 if i % 2 == 0 else 8
            tip_x = club_head_center_x + int(math.cos(spike_a) * spike_len)
            tip_y = club_head_center_y + int(math.sin(spike_a) * spike_len)
            perp_spike = spike_a + math.pi / 2
            base_a_x = club_head_center_x + int(math.cos(perp_spike) * 3)
            base_a_y = club_head_center_y + int(math.sin(perp_spike) * 3)
            base_b_x = club_head_center_x - int(math.cos(perp_spike) * 3)
            base_b_y = club_head_center_y - int(math.sin(perp_spike) * 3)
            # Shadow
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (base_a_x + 1, base_a_y + 1),
                (base_b_x + 1, base_b_y + 1),
            ])
            # Ice crystal spike
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["ice_darkest"], [
                (tip_x, tip_y), (base_a_x, base_a_y), (base_b_x, base_b_y),
            ])
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["ice_dark"], [
                (tip_x, tip_y),
                (int((tip_x + base_a_x) / 2), int((tip_y + base_a_y) / 2)),
                (int((tip_x + base_b_x) / 2), int((tip_y + base_b_y) / 2)),
            ])
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["ice_mid"], [
                (tip_x, tip_y),
                (int(tip_x * 0.7 + base_a_x * 0.3),
                 int(tip_y * 0.7 + base_a_y * 0.3)),
                (int(tip_x * 0.7 + base_b_x * 0.3),
                 int(tip_y * 0.7 + base_b_y * 0.3)),
            ])
            # Bright edge
            pygame.draw.line(surface, _NS_grondarthul.PALETTE["ice_light"],
                             (tip_x, tip_y),
                             (club_head_center_x, club_head_center_y), 1)
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["ice_hot"],
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["ice_shine"],
                             (tip_x, tip_y, 1, 1))
        # Central ice core (bright)
        _NS_grondarthul._aacircle(surface, _NS_grondarthul.PALETTE["ice_dark"],
                                   (club_head_center_x, club_head_center_y), 5)
        _NS_grondarthul._aacircle(surface, _NS_grondarthul.PALETTE["ice_mid"],
                                   (club_head_center_x, club_head_center_y), 4)
        _NS_grondarthul._aacircle(surface, _NS_grondarthul.PALETTE["ice_light"],
                                   (club_head_center_x, club_head_center_y), 3)
        _NS_grondarthul._aacircle(surface, _NS_grondarthul.PALETTE["ice_hot"],
                                   (club_head_center_x, club_head_center_y), 2)
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["ice_shine"],
                         (club_head_center_x, club_head_center_y, 1, 1))
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["white"],
                         (club_head_center_x, club_head_center_y, 1, 1))
        # Ice particles/mist around club head
        for i in range(3):
            p_a = phase * 3 + i * math.pi * 2 / 3
            p_r = 14 + int(math.sin(phase * 4 + i) * 2)
            px = club_head_center_x + int(math.cos(p_a) * p_r)
            py = club_head_center_y + int(math.sin(p_a) * p_r)
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["ice_shine"],
                             (px, py, 1, 1))
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["white"],
                             (px, py, 1, 1))
    def _draw_head(surface, cx, cy, facing, phase):
        """Troll head with big lower fangs."""
        # Head shape (angular)
        head_pts = [
            (cx - 7, cy + 4),
            (cx - 9, cy),
            (cx - 8, cy - 6),
            (cx - 4, cy - 10),
            (cx + 4, cy - 10),
            (cx + 8, cy - 6),
            (cx + 9, cy),
            (cx + 7, cy + 4),
            (cx + 4, cy + 7),
            (cx - 4, cy + 7),
        ]
        _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["shadow_deep"],
                              [(px + 2, py + 2) for px, py in head_pts])
        _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["skin_darkest"],
                              head_pts)
        _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["skin_dark"], [
            (cx - 7, cy + 3),
            (cx - 8, cy),
            (cx - 7, cy - 5),
            (cx - 3, cy - 9),
            (cx + 3, cy - 9),
            (cx + 7, cy - 5),
            (cx + 8, cy),
            (cx + 7, cy + 3),
            (cx + 3, cy + 6),
            (cx - 3, cy + 6),
        ])
        _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["skin_mid"], [
            (cx - 5, cy),
            (cx - 5, cy - 4),
            (cx - 2, cy - 7),
            (cx + 2, cy - 7),
            (cx + 5, cy - 4),
            (cx + 5, cy),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
        ])
        # Highlight
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["skin_light"],
                         (cx - 2, cy - 3, 4, 2))
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["skin_edge"],
                         (cx - 1, cy - 3, 1, 1))
        # Big pointy ears (troll ears)
        for side in (-1, 1):
            ear_x = cx + side * 8
            ear_y = cy - 2
            # Ear shadow
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["shadow_deep"], [
                (ear_x + 1, ear_y + 1),
                (ear_x + side * 5 + 1, ear_y - 3 + 1),
                (ear_x + side * 3 + 1, ear_y + 4 + 1),
            ])
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["skin_darkest"], [
                (ear_x, ear_y),
                (ear_x + side * 5, ear_y - 3),
                (ear_x + side * 3, ear_y + 4),
            ])
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["skin_dark"], [
                (ear_x + side, ear_y),
                (ear_x + side * 4, ear_y - 2),
                (ear_x + side * 2, ear_y + 3),
            ])
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["skin_mid"], [
                (ear_x + side * 2, ear_y - 1),
                (ear_x + side * 3, ear_y),
                (ear_x + side * 2, ear_y + 1),
            ])
        # Glowing cyan eyes (fierce)
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        for eye_x in (cx - 2, cx + 2):
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["shadow_deep"],
                             (eye_x - 1, cy - 3, 2, 2))
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["eye_socket"],
                             (eye_x - 1, cy - 3, 2, 2))
            # Glow
            for r in range(3, 0, -1):
                alpha = _NS_grondarthul._alpha(200 * (3 - r) / 3 * pulse)
                _NS_grondarthul._aacircle(surface,
                                           (*_NS_grondarthul.PALETTE["eye_light"],
                                            alpha),
                                           (eye_x, cy - 2), r)
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["eye_glow"],
                             (eye_x, cy - 2, 1, 1))
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["white"],
                             (eye_x, cy - 2, 1, 1))
        # Brow/scowl
        pygame.draw.line(surface, _NS_grondarthul.PALETTE["skin_darkest"],
                         (cx - 4, cy - 4), (cx - 1, cy - 3), 1)
        pygame.draw.line(surface, _NS_grondarthul.PALETTE["skin_darkest"],
                         (cx + 4, cy - 4), (cx + 1, cy - 3), 1)
        # Nose (troll flat nose)
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["skin_darkest"],
                         (cx - 1, cy, 3, 2))
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["shadow_deep"],
                         (cx, cy + 1, 1, 1))
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["shadow_deep"],
                         (cx + 2, cy + 1, 1, 1))
        # Mouth line
        pygame.draw.line(surface, _NS_grondarthul.PALETTE["shadow_deep"],
                         (cx - 3, cy + 4), (cx + 3, cy + 4), 1)
        # BIG LOWER FANGS (protruding upward from mouth)
        for i, fang_x_off in enumerate((-3, 3)):
            fang_x = cx + fang_x_off
            fang_base_y = cy + 4
            fang_tip_y = cy + 1
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["shadow_deep"], [
                (fang_x - 1 + 1, fang_base_y + 1),
                (fang_x + 1 + 1, fang_base_y + 1),
                (fang_x + 1, fang_tip_y + 1),
            ])
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["fang_dark"], [
                (fang_x - 1, fang_base_y),
                (fang_x + 1, fang_base_y),
                (fang_x, fang_tip_y),
            ])
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["fang_mid"], [
                (fang_x, fang_base_y),
                (fang_x + 1, fang_base_y - 1),
                (fang_x, fang_tip_y),
            ])
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["fang_light"],
                             (fang_x, fang_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["fang_shine"],
                             (fang_x, fang_tip_y, 1, 1))
    def _draw_mohawk(surface, cx, cy, facing, phase):
        """Big magenta/pink spiky mohawk on top."""
        # Multiple tall spikes in a row
        for i, (x_off, height) in enumerate([
            (-5, 5), (-3, 8), (-1, 12), (1, 12), (3, 8), (5, 5),
        ]):
            sway = math.sin(phase * 0.4 + i * 0.5) * 1
            spike_x = cx + x_off
            spike_base_y = cy + 4
            spike_tip_y = cy - height + int(sway)
            # Shadow
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_tip_y + 1),
                (spike_x - 2 + 1, spike_base_y + 1),
                (spike_x + 2 + 1, spike_base_y + 1),
            ])
            # Main spike
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["hair_darkest"], [
                (spike_x, spike_tip_y),
                (spike_x - 2, spike_base_y),
                (spike_x + 2, spike_base_y),
            ])
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["hair_dark"], [
                (spike_x, spike_tip_y),
                (spike_x - 1, spike_base_y),
                (spike_x + 2, spike_base_y),
            ])
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["hair_mid"], [
                (spike_x, spike_tip_y),
                (spike_x, spike_base_y),
                (spike_x + 1, spike_base_y),
            ])
            # Bright tip
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["hair_light"],
                             (spike_x, spike_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["hair_shine"],
                             (spike_x, spike_tip_y + 1, 1, 1))
            # Highlight strand down
            pygame.draw.line(surface, _NS_grondarthul.PALETTE["hair_light"],
                             (spike_x, spike_tip_y + 1),
                             (spike_x, spike_tip_y + height // 2), 1)
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 15 - radius,
                                 120 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (2, 5, 10, 180), (5, 8, 130, 14))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_frost_aura(surface, x, y, phase):
        """Cold cyan aura behind boss."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_grondarthul._alpha((90 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_grondarthul._aacircle(aura,
                                           (*_NS_grondarthul.PALETTE["ice_darkest"],
                                            alpha),
                                           (110, 100), radius)
        for radius in range(50, 5, -3):
            alpha = _NS_grondarthul._alpha((50 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_grondarthul._aacircle(aura,
                                           (*_NS_grondarthul.PALETTE["ice_dark"],
                                            alpha),
                                           (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))
        # Ice particles floating
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 42 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["ice_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["ice_shine"],
                             (sx, sy, 1, 1))
    def _draw_snow_particles(surface, x, y, phase):
        """Falling snow around boss."""
        for i in range(10):
            t = (phase * 0.4 + i * 0.1) % 1.0
            drift = math.sin(phase * 0.8 + i * 0.5) * 20
            base_x = x + int(drift) + (i - 5) * 10
            base_y = y - 50 + int(t * 100)
            alpha = _NS_grondarthul._alpha(200 * (1 - abs(t - 0.5) * 0.8))
            pygame.draw.rect(surface,
                             (*_NS_grondarthul.PALETTE["frost_light"], alpha),
                             (base_x, base_y, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_grondarthul.PALETTE["white"], alpha),
                             (base_x, base_y, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground rune ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_grondarthul.PALETTE["ice_darkest"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_grondarthul.PALETTE["skin_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_grondarthul.PALETTE["ice_dark"], 220),
                            (25, 22, 120, 18), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_grondarthul.PALETTE["ice_mid"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_grondarthul.PALETTE["ice_hot"],
                                        _NS_grondarthul._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # BASIC ATTACK - Ice Club Smash (MELEE)
    # ============================================================
    def _draw_basic_attack_fx(surface, boss, x, y):
        """Basic melee: overhead club smash with ice shockwave."""
        progress = getattr(boss, "_gro_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        facing = boss.direction
        target = getattr(boss, "target", None)
        if target and getattr(target, "alive", True):
            tx = int(target.x)
            ty = int(target.y)
        else:
            tx = x + facing * 60
            ty = y + 20
        # Limit to melee range
        dx = tx - x
        dy = ty - y
        dist = math.hypot(dx, dy)
        if dist > 80:
            tx = x + int(dx / dist * 60)
            ty = y + int(dy / dist * 60)
        # PHASE 1: Wind-up (0-40%) - club raising up
        if progress < 0.4:
            t = progress / 0.4
            # Small ice charge at club head (above boss)
            club_top_x = x + facing * 5
            club_top_y = y - 30 - int(t * 5)
            for r in range(int(3 + t * 4), 0, -1):
                alpha = _NS_grondarthul._alpha(180 * t * r / 7)
                _NS_grondarthul._aacircle(surface,
                                           (*_NS_grondarthul.PALETTE["ice_light"],
                                            alpha),
                                           (club_top_x, club_top_y), r)
        # PHASE 2: SLAM DOWN (40-70%) - motion blur trail
        elif progress < 0.7:
            t = (progress - 0.4) / 0.3
            # Motion trail from top to slam point
            start_x = x + facing * 8
            start_y = y - 25
            end_x = x + facing * 30
            end_y = y + 10
            # Ice slash arc trail
            for line_i, offset in enumerate((-4, 0, 4)):
                num_pts = 8
                prev_pt = None
                for step in range(num_pts + 1):
                    step_t = step / num_pts
                    # Curved arc from up to down
                    curve_a = math.pi / 2 * step_t  # 0 to 90 degrees
                    px = int(start_x + (end_x - start_x) * step_t)
                    py = int(start_y + (end_y - start_y) * step_t
                             + offset * (1 - step_t))
                    if prev_pt is not None:
                        alpha = _NS_grondarthul._alpha(230 * step_t
                                                       * (1 - t * 0.3))
                        pygame.draw.line(surface,
                                         (*_NS_grondarthul.PALETTE["ice_darkest"],
                                          alpha),
                                         prev_pt, (px, py), 4)
                        pygame.draw.line(surface,
                                         (*_NS_grondarthul.PALETTE["ice_dark"],
                                          alpha),
                                         prev_pt, (px, py), 3)
                        pygame.draw.line(surface,
                                         (*_NS_grondarthul.PALETTE["ice_mid"],
                                          alpha),
                                         prev_pt, (px, py), 2)
                        pygame.draw.line(surface,
                                         (*_NS_grondarthul.PALETTE["ice_hot"],
                                          alpha),
                                         prev_pt, (px, py), 1)
                    prev_pt = (px, py)
            # Ice crystal shards flying
            for i in range(6):
                shard_angle = math.pi * 0.5 + i * 0.3 - 0.9
                shard_r = int(t * 25)
                sx = x + facing * 20 + int(math.cos(shard_angle) * shard_r) * facing
                sy = y - int(math.sin(shard_angle) * shard_r)
                alpha = _NS_grondarthul._alpha(230)
                # Ice shard
                pygame.draw.polygon(surface,
                                    (*_NS_grondarthul.PALETTE["ice_dark"], alpha), [
                    (sx, sy - 2), (sx + 1, sy), (sx, sy + 2), (sx - 1, sy),
                ])
                pygame.draw.rect(surface, _NS_grondarthul.PALETTE["ice_shine"],
                                 (sx, sy, 1, 1))
        # PHASE 3: IMPACT + ICE EXPLOSION (70-100%)
        else:
            t = (progress - 0.7) / 0.3
            impact_x = x + facing * 30
            impact_y = y + 25
            impact_r = int(10 + t * 25)
            alpha = _NS_grondarthul._alpha(240 * (1 - t))
            # Impact ground crack (flat ellipse)
            pygame.draw.ellipse(surface,
                                (*_NS_grondarthul.PALETTE["ice_darkest"], alpha),
                                (impact_x - impact_r,
                                 impact_y - impact_r // 3,
                                 impact_r * 2, impact_r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_grondarthul.PALETTE["ice_dark"], alpha),
                                (impact_x - impact_r + 3,
                                 impact_y - impact_r // 3 + 2,
                                 impact_r * 2 - 6, impact_r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface,
                                (*_NS_grondarthul.PALETTE["ice_mid"], alpha),
                                (impact_x - impact_r + 6,
                                 impact_y - impact_r // 3 + 4,
                                 impact_r * 2 - 12, impact_r * 2 // 3 - 8), 1)
            # Bright core burst
            core_r = max(1, int(6 * (1 - t)))
            _NS_grondarthul._aacircle(surface,
                                       (*_NS_grondarthul.PALETTE["ice_hot"], alpha),
                                       (impact_x, impact_y), core_r + 2)
            _NS_grondarthul._aacircle(surface,
                                       (*_NS_grondarthul.PALETTE["ice_shine"], alpha),
                                       (impact_x, impact_y), max(1, core_r))
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["white"],
                             (impact_x, impact_y, 1, 1))
            # ICE CRYSTALS BURSTING UP from impact
            for i in range(8):
                crystal_a = i * math.pi / 4
                crystal_r = int(impact_r * 0.7)
                cx_i = impact_x + int(math.cos(crystal_a) * crystal_r)
                cy_i = impact_y + int(math.sin(crystal_a) * crystal_r * 0.5)
                # Small ice spike
                spike_h = int(12 * (1 - t * 0.5))
                if spike_h < 2:
                    continue
                tip_x = cx_i
                tip_y = cy_i - spike_h
                _NS_grondarthul._poly(surface,
                                       (*_NS_grondarthul.PALETTE["ice_darkest"], alpha),
                                       [(tip_x, tip_y),
                                        (cx_i - 2, cy_i),
                                        (cx_i + 2, cy_i)])
                _NS_grondarthul._poly(surface,
                                       (*_NS_grondarthul.PALETTE["ice_dark"], alpha),
                                       [(tip_x, tip_y),
                                        (cx_i - 1, cy_i),
                                        (cx_i + 1, cy_i)])
                _NS_grondarthul._poly(surface,
                                       (*_NS_grondarthul.PALETTE["ice_mid"], alpha),
                                       [(tip_x, tip_y),
                                        (cx_i, cy_i - spike_h // 2),
                                        (cx_i + 1, cy_i - 1)])
                pygame.draw.rect(surface,
                                 (*_NS_grondarthul.PALETTE["ice_shine"], alpha),
                                 (tip_x, tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_grondarthul.PALETTE["white"],
                                 (tip_x, tip_y, 1, 1))
            # Snow burst particles
            for i in range(12):
                p_a = i * math.pi / 6
                p_r = int(impact_r * (0.8 + (i % 3) * 0.15))
                px = impact_x + int(math.cos(p_a) * p_r)
                py = impact_y + int(math.sin(p_a) * p_r * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_grondarthul.PALETTE["ice_shine"], alpha),
                                 (px, py, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_grondarthul.PALETTE["white"], alpha),
                                 (px, py, 1, 1))
    # ============================================================
    # SKILL: Q - CHOMP (bite heal)
    # ============================================================
    def _draw_chomp_fx(surface, boss, x, y, timer, phase):
        """Bite forward + green heal particles rising."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        target = getattr(boss, "target", None)
        if target and getattr(target, "alive", True):
            tx = int(target.x)
            ty = int(target.y)
        else:
            tx = x + facing * 60
            ty = y
        # Phase 1: Big bite forward
        if progress < 0.5:
            t = progress / 0.5
            bite_end_x = x + facing * int(t * 60)
            # Bite marks (like teeth)
            for y_off in (-8, -3, 3, 8):
                pygame.draw.line(surface,
                                 (*_NS_grondarthul.PALETTE["ice_darkest"], 220),
                                 (x + facing * 20, y - 2 + y_off),
                                 (bite_end_x, ty + y_off), 3)
                pygame.draw.line(surface,
                                 (*_NS_grondarthul.PALETTE["ice_mid"], 220),
                                 (x + facing * 20, y - 2 + y_off),
                                 (bite_end_x, ty + y_off), 2)
                pygame.draw.line(surface,
                                 (*_NS_grondarthul.PALETTE["ice_light"], 220),
                                 (x + facing * 20, y - 2 + y_off),
                                 (bite_end_x, ty + y_off), 1)
            # Bite impact
            if t > 0.5:
                for r in range(10, 0, -1):
                    alpha = _NS_grondarthul._alpha(220 * (10 - r) / 10)
                    _NS_grondarthul._aacircle(surface,
                                               (*_NS_grondarthul.PALETTE["ice_mid"],
                                                alpha),
                                               (bite_end_x, ty), r)
                _NS_grondarthul._aacircle(surface,
                                           _NS_grondarthul.PALETTE["ice_shine"],
                                           (bite_end_x, ty), 3)
        # Green heal particles rising to boss
        if progress > 0.4:
            t = (progress - 0.4) / 0.6
            for i in range(10):
                particle_t = (t + i * 0.1) % 1.0
                px = int(tx + (x - tx) * particle_t)
                py = int(ty + (y - ty) * particle_t
                         - math.sin(particle_t * math.pi) * 20)
                alpha = _NS_grondarthul._alpha(240 * (1 - particle_t * 0.5))
                # Green heal
                _NS_grondarthul._aacircle(surface, (30, 130, 40, alpha),
                                           (px, py), 3)
                _NS_grondarthul._aacircle(surface, (60, 200, 60, alpha),
                                           (px, py), 2)
                pygame.draw.rect(surface, (140, 255, 140, alpha),
                                 (px, py, 1, 1))
                pygame.draw.rect(surface, (220, 255, 220, alpha),
                                 (px, py, 1, 1))
    # ============================================================
    # SKILL: W - FROZEN DOMAIN (ice ground AoE)
    # ============================================================
    def _draw_frozendomain_ground(surface, boss, x, y, timer, phase):
        """Ice ground circle."""
        tx, ty = _NS_grondarthul._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 2))
        if r > 5:
            alpha = _NS_grondarthul._alpha(220)
            pygame.draw.ellipse(surface,
                                (*_NS_grondarthul.PALETTE["ice_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_grondarthul.PALETTE["ice_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                (*_NS_grondarthul.PALETTE["ice_mid"], 180),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
    def _draw_frozendomain_fx(surface, boss, x, y, timer, phase):
        """Ice spikes bursting up around target."""
        tx, ty = _NS_grondarthul._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Multiple ice spikes in circle pattern
        spike_positions = [
            (0, 0), (-20, -5), (20, -5), (-35, 5), (35, 5),
            (-15, 12), (15, 12), (0, -18), (-45, 0), (45, 0),
            (-10, -15), (10, -15), (0, 15), (-25, -12), (25, -12),
        ]
        for i, (dx, dy) in enumerate(spike_positions):
            delay = i * 0.03
            local_t = max(0.0, min(1.0, (progress - delay) / (1 - delay)))
            if local_t <= 0:
                continue
            # Rise then persist
            if local_t < 0.3:
                height = int((local_t / 0.3) * 20)
            else:
                height = int(20 * (1 - (local_t - 0.3) / 0.7 * 0.2))
            cx_i = tx + dx
            cy_i = ty + dy
            tip_x = cx_i
            tip_y = cy_i - height
            # Ice spike (angular crystal)
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (cx_i - 4 + 1, cy_i + 1),
                (cx_i + 4 + 1, cy_i + 1),
            ])
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["ice_darkest"], [
                (tip_x, tip_y),
                (cx_i - 4, cy_i),
                (cx_i + 4, cy_i),
            ])
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["ice_dark"], [
                (tip_x, tip_y),
                (cx_i - 3, cy_i),
                (cx_i + 3, cy_i),
            ])
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["ice_mid"], [
                (tip_x, tip_y),
                (cx_i - 2, cy_i - height // 3),
                (cx_i, cy_i - 2),
                (cx_i + 2, cy_i - height // 3),
            ])
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["ice_light"], [
                (tip_x, tip_y),
                (cx_i - 1, cy_i - height // 2),
                (cx_i + 1, cy_i - height // 2),
            ])
            # Bright tip
            for r in range(3, 0, -1):
                alpha = _NS_grondarthul._alpha(220 * (3 - r) / 3)
                _NS_grondarthul._aacircle(surface,
                                           (*_NS_grondarthul.PALETTE["ice_hot"],
                                            alpha),
                                           (tip_x, tip_y), r)
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["ice_shine"],
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["white"],
                             (tip_x, tip_y, 1, 1))
    # ============================================================
    # SKILL: E - PILLAR OF ICE (big ice pillar summon)
    # ============================================================
    def _draw_pillarofice_fx(surface, boss, x, y, timer, phase):
        """Giant ice pillar rises from ground at target."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        target = getattr(boss, "target", None)
        if target and getattr(target, "alive", True):
            tx = int(target.x)
            ty = int(target.y) + 20
        else:
            tx = x + facing * 100
            ty = y + 20
        # Rise animation
        if progress < 0.3:
            t = progress / 0.3
            height = int(45 * t)
        else:
            height = 45
        if height < 3:
            return
        # Ground shadow
        pygame.draw.ellipse(surface, _NS_grondarthul.PALETTE["shadow_deep"],
                            (tx - 10, ty - 3, 20, 8))
        pygame.draw.ellipse(surface, _NS_grondarthul.PALETTE["ice_darkest"],
                            (tx - 10, ty - 4, 20, 6))
        # Pillar shape (tall hexagonal ice crystal)
        pillar_top_y = ty - height
        pillar_base_pts = [
            (tx - 10, ty),
            (tx - 8, ty - 2),
            (tx - 8, pillar_top_y + 8),
            (tx - 5, pillar_top_y),
            (tx + 5, pillar_top_y),
            (tx + 8, pillar_top_y + 8),
            (tx + 8, ty - 2),
            (tx + 10, ty),
        ]
        _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["shadow_deep"],
                              [(px + 2, py + 2) for px, py in pillar_base_pts])
        _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["ice_darkest"],
                              pillar_base_pts)
        # Middle layer
        _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["ice_dark"], [
            (tx - 8, ty),
            (tx - 6, ty - 2),
            (tx - 6, pillar_top_y + 6),
            (tx - 3, pillar_top_y + 2),
            (tx + 3, pillar_top_y + 2),
            (tx + 6, pillar_top_y + 6),
            (tx + 6, ty - 2),
            (tx + 8, ty),
        ])
        # Inner bright
        _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["ice_mid"], [
            (tx - 5, ty),
            (tx - 4, ty - 2),
            (tx - 4, pillar_top_y + 8),
            (tx - 1, pillar_top_y + 4),
            (tx + 1, pillar_top_y + 4),
            (tx + 4, pillar_top_y + 8),
            (tx + 4, ty - 2),
            (tx + 5, ty),
        ])
        # Bright center line (crystal reflection)
        pygame.draw.line(surface, _NS_grondarthul.PALETTE["ice_light"],
                         (tx - 2, ty), (tx - 1, pillar_top_y + 5), 2)
        pygame.draw.line(surface, _NS_grondarthul.PALETTE["ice_hot"],
                         (tx - 1, ty), (tx, pillar_top_y + 5), 1)
        pygame.draw.line(surface, _NS_grondarthul.PALETTE["ice_shine"],
                         (tx, ty - 5), (tx, pillar_top_y + 5), 1)
        pygame.draw.line(surface, _NS_grondarthul.PALETTE["white"],
                         (tx, pillar_top_y + 6), (tx, pillar_top_y + 15), 1)
        # Bright tip
        for r in range(5, 0, -1):
            alpha = _NS_grondarthul._alpha(240 * (5 - r) / 5)
            _NS_grondarthul._aacircle(surface,
                                       (*_NS_grondarthul.PALETTE["ice_hot"], alpha),
                                       (tx, pillar_top_y + 2), r)
        _NS_grondarthul._aacircle(surface, _NS_grondarthul.PALETTE["ice_shine"],
                                   (tx, pillar_top_y + 2), 2)
        pygame.draw.rect(surface, _NS_grondarthul.PALETTE["white"],
                         (tx, pillar_top_y + 2, 1, 1))
        # Ice particles rising around pillar
        for i in range(6):
            p_t = (phase * 0.5 + i * 0.16) % 1.0
            p_a = i * math.pi / 3
            p_r = 12
            px = tx + int(math.cos(p_a) * p_r)
            py = ty - int(p_t * height)
            alpha = _NS_grondarthul._alpha(200 * (1 - p_t))
            pygame.draw.rect(surface,
                             (*_NS_grondarthul.PALETTE["ice_shine"], alpha),
                             (px, py, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_grondarthul.PALETTE["white"], alpha),
                             (px, py, 1, 1))
        # Small side crystals at base
        for side in (-1, 1):
            side_x = tx + side * 7
            side_top_y = ty - height // 3
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["ice_dark"], [
                (side_x, side_top_y),
                (side_x - 2, ty),
                (side_x + 2, ty),
            ])
            _NS_grondarthul._poly(surface, _NS_grondarthul.PALETTE["ice_mid"], [
                (side_x, side_top_y),
                (side_x - 1, ty),
                (side_x + 1, ty),
            ])
            pygame.draw.rect(surface, _NS_grondarthul.PALETTE["ice_shine"],
                             (side_x, side_top_y, 1, 1))
    # ============================================================
    # SKILL: R - SUBJUGATE (health drain beam)
    # ============================================================
    def _draw_subjugate_ground(surface, boss, x, y, timer, phase):
        """Ground circle indicating drain."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        r = int(45 + math.sin(phase * 2) * 3)
        alpha = _NS_grondarthul._alpha(200 * pulse)
        pygame.draw.ellipse(surface,
                            (*_NS_grondarthul.PALETTE["ice_dark"], alpha),
                            (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 3)
        pygame.draw.ellipse(surface,
                            (*_NS_grondarthul.PALETTE["ice_mid"], alpha),
                            (x - r + 3, y + 40 - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 2)
        pygame.draw.ellipse(surface,
                            (*_NS_grondarthul.PALETTE["ice_light"], alpha),
                            (x - r + 6, y + 40 - r // 3 + 4,
                             r * 2 - 12, r * 2 // 3 - 8), 1)
    def _draw_subjugate_fx(surface, boss, x, y, timer, phase):
        """Beam connecting boss to target + drain particles."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        target = getattr(boss, "target", None)
        if target and getattr(target, "alive", True):
            tx = int(target.x)
            ty = int(target.y)
        else:
            tx = x + facing * 100
            ty = y
        # Beam from boss to target
        start_x = x + facing * 15
        start_y = y - 4
        # Ice tether beam
        # Multi-layer beam
        for width, color_key, alpha_m in [
            (6, "ice_darkest", 120),
            (4, "ice_dark", 180),
            (3, "ice_mid", 220),
            (2, "ice_hot", 240),
            (1, "ice_shine", 255),
        ]:
            pygame.draw.line(surface,
                             (*_NS_grondarthul.PALETTE[color_key], alpha_m),
                             (start_x, start_y), (tx, ty), width)
        # Wavy overlay
        num_pts = 12
        for offset in (-4, 4):
            wavy_pts = []
            for i in range(num_pts + 1):
                t = i / num_pts
                mx = start_x + (tx - start_x) * t
                my = start_y + (ty - start_y) * t
                # Perpendicular wave
                perp_angle = math.atan2(ty - start_y, tx - start_x) + math.pi / 2
                wave = math.sin(t * math.pi * 3 + phase * 5) * offset
                mx += math.cos(perp_angle) * wave
                my += math.sin(perp_angle) * wave
                wavy_pts.append((int(mx), int(my)))
            for i in range(len(wavy_pts) - 1):
                pygame.draw.line(surface,
                                 (*_NS_grondarthul.PALETTE["ice_hot"], 200),
                                 wavy_pts[i], wavy_pts[i + 1], 1)
                pygame.draw.rect(surface, _NS_grondarthul.PALETTE["ice_shine"],
                                 (wavy_pts[i][0], wavy_pts[i][1], 1, 1))
        # Bright pulse at both ends
        pulse = math.sin(phase * 4) * 0.3 + 0.7
        # At boss (drain source)
        for r in range(8, 0, -1):
            alpha = _NS_grondarthul._alpha(180 * (8 - r) / 8 * pulse)
            _NS_grondarthul._aacircle(surface,
                                       (*_NS_grondarthul.PALETTE["ice_hot"], alpha),
                                       (start_x, start_y), r)
        _NS_grondarthul._aacircle(surface, _NS_grondarthul.PALETTE["ice_shine"],
                                   (start_x, start_y), 3)
        # At target (being drained)
        for r in range(10, 0, -1):
            alpha = _NS_grondarthul._alpha(200 * (10 - r) / 10 * pulse)
            _NS_grondarthul._aacircle(surface,
                                       (*_NS_grondarthul.PALETTE["ice_light"], alpha),
                                       (tx, ty), r)
        _NS_grondarthul._aacircle(surface, _NS_grondarthul.PALETTE["ice_shine"],
                                   (tx, ty), 4)
        _NS_grondarthul._aacircle(surface, _NS_grondarthul.PALETTE["white"],
                                   (tx, ty), 2)
        # HEALTH particles flowing FROM target TO boss (red particles)
        for i in range(10):
            particle_t = (phase * 0.7 + i * 0.1) % 1.0
            px = int(tx + (start_x - tx) * particle_t)
            py = int(ty + (start_y - ty) * particle_t)
            # Add wave motion
            perp_angle = math.atan2(ty - start_y, tx - start_x) + math.pi / 2
            wave = math.sin(particle_t * math.pi * 3 + phase * 5) * 3
            px += int(math.cos(perp_angle) * wave)
            py += int(math.sin(perp_angle) * wave)
            alpha = _NS_grondarthul._alpha(240 * (1 - abs(particle_t - 0.5) * 0.5))
            # Red health particle
            _NS_grondarthul._aacircle(surface, (140, 20, 30, alpha),
                                       (px, py), 3)
            _NS_grondarthul._aacircle(surface, (220, 40, 50, alpha),
                                       (px, py), 2)
            pygame.draw.rect(surface, (255, 100, 100, alpha), (px, py, 1, 1))
            pygame.draw.rect(surface, (255, 200, 200, alpha), (px, py, 1, 1))



# ====================================================================
# XARETH (TIMERENDER) - Mini Boss
# ====================================================================

class _NS_xareth:
    """Namespace xareth - void time manipulator boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Purple skin/void body (main)
        "skin_darkest": (18, 8, 30),
        "skin_dark": (55, 25, 85),
        "skin_mid": (105, 60, 155),
        "skin_light": (165, 115, 210),
        "skin_edge": (210, 175, 240),
        "skin_shine": (240, 220, 255),
        # Dark armor plates (helm, chest)
        "armor_darkest": (10, 5, 20),
        "armor_dark": (35, 20, 55),
        "armor_mid": (75, 50, 110),
        "armor_light": (130, 100, 175),
        "armor_edge": (185, 160, 220),
        # Green crystal energy (weapon, chest gem, eye)
        "crystal_darkest": (5, 30, 10),
        "crystal_dark": (25, 90, 40),
        "crystal_mid": (75, 200, 100),
        "crystal_light": (150, 255, 170),
        "crystal_hot": (220, 255, 230),
        "crystal_shine": (255, 255, 255),
        # Void purple energy (magic, aura, portals)
        "void_darkest": (12, 5, 25),
        "void_dark": (45, 20, 80),
        "void_mid": (110, 55, 180),
        "void_light": (175, 110, 240),
        "void_hot": (220, 175, 255),
        "void_shine": (245, 225, 255),
        # Glowing green eye (through helm)
        "eye_socket": (5, 2, 10),
        "eye_dark": (25, 90, 30),
        "eye_mid": (100, 220, 120),
        "eye_light": (200, 255, 210),
        "eye_glow": (255, 255, 255),
        # Time distortion (blue-white)
        "time_dark": (30, 40, 90),
        "time_mid": (100, 130, 220),
        "time_light": (200, 220, 255),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_xareth._clamp(color)
        if _NS_xareth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_xareth._clamp(color)
        if _NS_xareth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_xareth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ================= ENTRY POINT =================
    def draw_xareth(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_xareth._detect_moving(boss)
        _NS_xareth._update_xr_attack_anim(boss)
        attacking = (
            getattr(boss, "_xr_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        _NS_xareth._draw_void_aura(surface, x, y, pulse)
        _NS_xareth._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX behind body.
        if active_skill == "e":
            _NS_xareth._draw_temporal_field_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xareth._draw_chrono_prison_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_xareth._draw_aeon_rift_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (may be invisible during teleport).
        w_progress = 0
        if active_skill == "w":
            w_duration = 60
            w_progress = max(0.0, min(1.0, 1 - skill_timer / w_duration))
        body_visible = not (active_skill == "w" and 0.3 < w_progress < 0.7)
        if body_visible:
            if attacking:
                _NS_xareth._draw_xr_attack(surface, boss, x, y)
            elif moving:
                _NS_xareth._draw_xr_walk(surface, boss, x, y)
            else:
                _NS_xareth._draw_xr_idle(surface, boss, x, y)
        # Foreground FX.
        if active_skill == "q":
            _NS_xareth._draw_void_lock_projectile(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_xareth._draw_aeon_rift_foreground(surface, boss, x, y, skill_timer, pulse, w_progress)
        elif active_skill == "e":
            _NS_xareth._draw_temporal_field_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xareth._draw_chrono_prison_dome(surface, boss, x, y, skill_timer, pulse)
    # ================= ANIMATION STATE =================
    def _update_xr_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_xr_previous_timer", 0))
        active = bool(getattr(boss, "_xr_attack_active", False))
        if not active and previous > timer and previous >= cooldown - 2:
            boss._xr_attack_active = True
            boss._xr_attack_frame = 0
            active = True
        elif active:
            boss._xr_attack_frame = int(getattr(boss, "_xr_attack_frame", 0)) + 1
            if boss._xr_attack_frame >= cooldown:
                boss._xr_attack_active = False
                boss._xr_attack_frame = 0
                active = False
        boss._xr_previous_timer = timer
        boss._xr_attack_progress = (
            min(1.0, getattr(boss, "_xr_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
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
    # ================= POSE ROUTERS =================
    def _draw_xr_idle(surface, boss, x, y):
        # Floating - stronger bob for that hovering effect.
        bob = int(math.sin(boss.pulse * 0.6) * 5)
        _NS_xareth._draw_shadow(surface, x, y + 50)
        _NS_xareth._draw_hover_particles(surface, x, y + 46, boss.pulse)
        _NS_xareth._draw_xr_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")
    def _draw_xr_walk(surface, boss, x, y):
        # Walking = floating with sway.
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 6)
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_xareth._draw_shadow(surface, x + sway, y + 50)
        _NS_xareth._draw_hover_particles(surface, x + sway, y + 46, phase, trail=True, facing=boss.direction)
        _NS_xareth._draw_xr_body(surface, x + sway, y + bob, boss.direction, phase, "walk")
    def _draw_xr_attack(surface, boss, x, y):
        progress = getattr(boss, "_xr_attack_progress", None)
        if progress is None or progress <= 0:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            t_eased = 1 - (1 - t) ** 2
            lunge = int((-3 + t_eased * 12)) * boss.direction
            lift = int(3 - t_eased * 4)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(9 * (1 - t)) * boss.direction
            lift = int(-1 + t * 1)
        _NS_xareth._draw_shadow(surface, x + lunge, y + 50)
        _NS_xareth._draw_hover_particles(surface, x + lunge, y + 46, boss.pulse, intense=True)
        _NS_xareth._draw_xr_body(surface, x + lunge, y - lift, boss.direction, boss.pulse, "attack", progress)
        _NS_xareth._draw_gauntlet_swing(surface, boss, x + lunge, y - lift, progress)
    # ================= BODY =================
    def _draw_xr_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Cloak / trail behind body (billowing energy).
        _NS_xareth._draw_energy_cloak(surface, cx, cy, facing, phase)
        # Legs (floating, dangling).
        _NS_xareth._draw_void_legs(surface, cx, cy + 12, facing, phase, action)
        # Torso (main body with muscles).
        _NS_xareth._draw_void_torso(surface, cx, cy, facing, phase)
        # Non-weapon arm (back).
        _NS_xareth._draw_back_arm(surface, cx, cy, facing, phase, action)
        # Head with helm.
        _NS_xareth._draw_void_head(surface, cx, cy - 18, facing, phase, action)
        # Weapon arm (front) with gauntlet.
        _NS_xareth._draw_weapon_arm(surface, cx, cy, facing, phase, action, attack_progress)
    def _draw_energy_cloak(surface, cx, cy, facing, phase):
        """Billowing energy trail behind body."""
        wave = math.sin(phase * 1.0) * 3
        back_dir = -facing
        cloak_shape = [
            (cx + back_dir * 8, cy - 15),
            (cx + back_dir * 12, cy - 10),
            (cx + back_dir * 16 + int(wave), cy - 4),
            (cx + back_dir * 18 + int(wave * 0.7), cy + 4),
            (cx + back_dir * 14 + int(wave * 0.5), cy + 12),
            (cx + back_dir * 8, cy + 18),
            (cx + back_dir * 4, cy + 16),
            (cx + back_dir * 2, cy - 12),
        ]
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["shadow_deep"],
                         [(p[0] + 2, p[1] + 2) for p in cloak_shape])
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["void_darkest"], cloak_shape)
        # Inner cloak.
        inner_shape = [
            (cx + back_dir * 6, cy - 12),
            (cx + back_dir * 10, cy - 8),
            (cx + back_dir * 12 + int(wave * 0.5), cy - 2),
            (cx + back_dir * 14 + int(wave * 0.3), cy + 3),
            (cx + back_dir * 10, cy + 10),
            (cx + back_dir * 5, cy + 14),
            (cx + back_dir * 2, cy + 12),
            (cx + back_dir * 1, cy - 10),
        ]
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["void_dark"], inner_shape)
        # Purple glow highlight.
        for i, pt in enumerate(cloak_shape):
            if i % 2 == 0:
                pygame.draw.rect(surface, _NS_xareth.PALETTE["void_mid"],
                                 (pt[0], pt[1], 1, 1))
    def _draw_void_legs(surface, cx, cy, facing, phase, action):
        """Muscular legs with armored plates (floating below)."""
        leg_bob = math.sin(phase * 0.8) * 2 if action != "walk" \
            else math.sin(phase * 1.5) * 4
        for side in (-1, 1):
            hip_x = cx + side * 6
            hip_y = cy - 4
            knee_x = cx + side * 8
            knee_y = cy + 6 + int(leg_bob * side)
            foot_x = cx + side * 6
            foot_y = cy + 16 + int(leg_bob * 0.5 * side)
            # Upper leg (thigh with muscle).
            _NS_xareth._aaline(surface, _NS_xareth.PALETTE["shadow_deep"],
                               (hip_x + 1, hip_y + 1), (knee_x + 1, knee_y + 1), 7)
            _NS_xareth._aaline(surface, _NS_xareth.PALETTE["skin_darkest"],
                               (hip_x, hip_y), (knee_x, knee_y), 7)
            _NS_xareth._aaline(surface, _NS_xareth.PALETTE["skin_dark"],
                               (hip_x, hip_y), (knee_x, knee_y), 5)
            _NS_xareth._aaline(surface, _NS_xareth.PALETTE["skin_mid"],
                               (hip_x, hip_y), (knee_x, knee_y), 3)
            _NS_xareth._aaline(surface, _NS_xareth.PALETTE["skin_light"],
                               (hip_x - 1, hip_y), (knee_x - 1, knee_y), 1)
            # Knee armor.
            _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["armor_darkest"], (knee_x, knee_y), 4)
            _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["armor_dark"], (knee_x, knee_y), 3)
            _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["armor_mid"], (knee_x - 1, knee_y - 1), 2)
            pygame.draw.rect(surface, _NS_xareth.PALETTE["crystal_mid"], (knee_x, knee_y, 1, 1))
            # Lower leg (shin).
            _NS_xareth._aaline(surface, _NS_xareth.PALETTE["skin_darkest"],
                               (knee_x, knee_y), (foot_x, foot_y), 5)
            _NS_xareth._aaline(surface, _NS_xareth.PALETTE["skin_dark"],
                               (knee_x, knee_y), (foot_x, foot_y), 3)
            _NS_xareth._aaline(surface, _NS_xareth.PALETTE["skin_mid"],
                               (knee_x - 1, knee_y), (foot_x - 1, foot_y), 1)
            # Foot / claw.
            _NS_xareth._poly(surface, _NS_xareth.PALETTE["armor_darkest"], [
                (foot_x - 3, foot_y - 1),
                (foot_x + 3, foot_y - 1),
                (foot_x + 2, foot_y + 2),
                (foot_x - 2, foot_y + 2),
            ])
            _NS_xareth._poly(surface, _NS_xareth.PALETTE["armor_mid"], [
                (foot_x - 2, foot_y),
                (foot_x + 2, foot_y),
                (foot_x + 1, foot_y + 1),
                (foot_x - 1, foot_y + 1),
            ])
    def _draw_void_torso(surface, cx, cy, facing, phase):
        """Muscular torso with armor."""
        breath = math.sin(phase * 0.7) * 1
        # Main torso (broad shoulders, V-shape).
        torso_shape = [
            (cx - 12, cy - 12),
            (cx - 14, cy - 4),
            (cx - 12, cy + 4),
            (cx - 10, cy + 12),
            (cx - 4, cy + 15),
            (cx + 4, cy + 15),
            (cx + 10, cy + 12),
            (cx + 12, cy + 4),
            (cx + 14, cy - 4),
            (cx + 12, cy - 12),
            (cx + 6, cy - 14),
            (cx - 6, cy - 14),
        ]
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["shadow_deep"],
                         [(p[0] + 2, p[1] + 2) for p in torso_shape])
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["skin_darkest"], torso_shape)
        # Body skin dark.
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["skin_dark"], [
            (cx - 11, cy - 11),
            (cx - 13, cy - 3),
            (cx - 10, cy + 4),
            (cx - 8, cy + 13),
            (cx + 8, cy + 13),
            (cx + 10, cy + 4),
            (cx + 13, cy - 3),
            (cx + 11, cy - 11),
            (cx + 5, cy - 13),
            (cx - 5, cy - 13),
        ])
        # Mid skin.
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["skin_mid"], [
            (cx - 9, cy - 8),
            (cx - 10, cy - 2),
            (cx - 7, cy + 4),
            (cx - 4, cy + 10),
            (cx + 4, cy + 10),
            (cx + 7, cy + 4),
            (cx + 10, cy - 2),
            (cx + 9, cy - 8),
            (cx + 4, cy - 11),
            (cx - 4, cy - 11),
        ])
        # Chest muscle definition (pectorals).
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["skin_light"], [
            (cx - 7, cy - 6),
            (cx - 1, cy - 8),
            (cx - 1, cy - 3),
            (cx - 5, cy - 2),
        ])
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["skin_light"], [
            (cx + 1, cy - 8),
            (cx + 7, cy - 6),
            (cx + 5, cy - 2),
            (cx + 1, cy - 3),
        ])
        # Highlight on chest.
        pygame.draw.rect(surface, _NS_xareth.PALETTE["skin_edge"], (cx - 5, cy - 7, 2, 1))
        pygame.draw.rect(surface, _NS_xareth.PALETTE["skin_edge"], (cx + 3, cy - 7, 2, 1))
        # Ab muscles (subtle).
        for i in range(3):
            ab_y = cy - 1 + i * 3
            pygame.draw.line(surface, _NS_xareth.PALETTE["skin_darkest"],
                             (cx - 4, ab_y), (cx + 4, ab_y), 1)
            pygame.draw.line(surface, _NS_xareth.PALETTE["skin_light"],
                             (cx - 3, ab_y - 1), (cx + 3, ab_y - 1), 1)
        # Central chest GREEN CRYSTAL.
        crystal_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        crystal_x = cx
        crystal_y = cy + 2
        for r in range(8, 0, -1):
            alpha = _NS_xareth._alpha(180 * (8 - r) / 8 * crystal_pulse)
            _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["crystal_dark"], alpha),
                                 (crystal_x, crystal_y), r)
        # Crystal diamond shape.
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["crystal_darkest"], [
            (crystal_x, crystal_y - 4),
            (crystal_x + 3, crystal_y),
            (crystal_x, crystal_y + 4),
            (crystal_x - 3, crystal_y),
        ])
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["crystal_dark"], [
            (crystal_x, crystal_y - 3),
            (crystal_x + 2, crystal_y),
            (crystal_x, crystal_y + 3),
            (crystal_x - 2, crystal_y),
        ])
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["crystal_mid"], [
            (crystal_x, crystal_y - 2),
            (crystal_x + 1, crystal_y),
            (crystal_x, crystal_y + 2),
            (crystal_x - 1, crystal_y),
        ])
        pygame.draw.rect(surface, _NS_xareth.PALETTE["crystal_light"],
                         (crystal_x, crystal_y - 1, 1, 1))
        pygame.draw.rect(surface, _NS_xareth.PALETTE["crystal_hot"],
                         (crystal_x, crystal_y - 1, 1, 1))
        # Shoulder armor plates.
        for side in (-1, 1):
            sh_x = cx + side * 11
            sh_y = cy - 10
            _NS_xareth._poly(surface, _NS_xareth.PALETTE["armor_darkest"], [
                (sh_x - 3, sh_y - 3),
                (sh_x + 3, sh_y - 3),
                (sh_x + 4, sh_y + 2),
                (sh_x - 4, sh_y + 2),
            ])
            _NS_xareth._poly(surface, _NS_xareth.PALETTE["armor_dark"], [
                (sh_x - 2, sh_y - 2),
                (sh_x + 2, sh_y - 2),
                (sh_x + 3, sh_y + 1),
                (sh_x - 3, sh_y + 1),
            ])
            _NS_xareth._poly(surface, _NS_xareth.PALETTE["armor_mid"], [
                (sh_x - 2, sh_y - 1),
                (sh_x + 2, sh_y - 1),
                (sh_x + 1, sh_y),
                (sh_x - 1, sh_y),
            ])
            pygame.draw.rect(surface, _NS_xareth.PALETTE["armor_edge"], (sh_x - 1, sh_y - 1, 2, 1))
    def _draw_void_head(surface, cx, cy, facing, phase, action):
        """Alien head with tall crested helm."""
        # Helm shape (tall crown, curves back).
        helm_shape = [
            (cx - 6, cy + 4),          # bottom left
            (cx - 7, cy - 2),
            (cx - 5, cy - 8),
            (cx - 2, cy - 12),         # crown left
            (cx + 1, cy - 14),         # crown peak
            (cx + 4, cy - 12),
            (cx + 6, cy - 8),
            (cx + 7, cy - 2),
            (cx + 6, cy + 4),
            (cx + 4, cy + 6),
            (cx - 4, cy + 6),
        ]
        # Facing adjustment: crown tilts forward.
        helm_shape = [(cx + (p[0] - cx) * facing if False else p[0], p[1]) for p in helm_shape]
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["shadow_deep"],
                         [(p[0] + 2, p[1] + 2) for p in helm_shape])
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["armor_darkest"], helm_shape)
        # Main helm color.
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["armor_dark"], [
            (cx - 5, cy + 3),
            (cx - 6, cy - 1),
            (cx - 4, cy - 7),
            (cx - 1, cy - 11),
            (cx + 3, cy - 11),
            (cx + 5, cy - 7),
            (cx + 6, cy - 1),
            (cx + 5, cy + 3),
            (cx + 3, cy + 5),
            (cx - 3, cy + 5),
        ])
        # Helm highlight (top).
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["armor_mid"], [
            (cx - 3, cy - 6),
            (cx - 1, cy - 10),
            (cx + 2, cy - 10),
            (cx + 4, cy - 6),
            (cx + 3, cy - 3),
            (cx - 2, cy - 3),
        ])
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["armor_light"], [
            (cx - 1, cy - 8),
            (cx + 1, cy - 9),
            (cx + 2, cy - 6),
            (cx, cy - 5),
        ])
        pygame.draw.rect(surface, _NS_xareth.PALETTE["armor_edge"], (cx, cy - 7, 1, 1))
        # Crown crest fins (2 fins on sides).
        for side in (-1, 1):
            fin_base_x = cx + side * 3
            fin_base_y = cy - 8
            fin_tip_x = cx + side * 5
            fin_tip_y = cy - 13
            _NS_xareth._poly(surface, _NS_xareth.PALETTE["armor_darkest"], [
                (fin_base_x, fin_base_y),
                (fin_tip_x, fin_tip_y),
                (fin_base_x + side, fin_base_y - 1),
            ])
            _NS_xareth._poly(surface, _NS_xareth.PALETTE["armor_dark"], [
                (fin_base_x, fin_base_y),
                (int((fin_base_x + fin_tip_x) / 2), int((fin_base_y + fin_tip_y) / 2)),
                (fin_base_x + side, fin_base_y - 1),
            ])
            pygame.draw.rect(surface, _NS_xareth.PALETTE["armor_mid"],
                             (fin_tip_x, fin_tip_y, 1, 1))
        # Face inside helm (dark shadow).
        pygame.draw.rect(surface, _NS_xareth.PALETTE["shadow_deep"], (cx - 3, cy - 3, 6, 4))
        pygame.draw.rect(surface, _NS_xareth.PALETTE["eye_socket"], (cx - 3, cy - 2, 6, 3))
        # GLOWING GREEN EYES (2 slits).
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_off in (-2, 1):
            ex = cx + eye_off
            ey = cy - 1
            for r in range(4, 0, -1):
                alpha = _NS_xareth._alpha(150 * (4 - r) / 4 * eye_pulse)
                _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["eye_mid"], alpha), (ex, ey), r)
            pygame.draw.rect(surface, _NS_xareth.PALETTE["eye_dark"], (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_xareth.PALETTE["eye_mid"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_xareth.PALETTE["eye_light"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_xareth.PALETTE["eye_glow"], (ex, ey, 1, 1))
        # Jaw / chin.
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["skin_darkest"], [
            (cx - 3, cy + 2),
            (cx + 3, cy + 2),
            (cx + 2, cy + 5),
            (cx - 2, cy + 5),
        ])
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["skin_dark"], [
            (cx - 2, cy + 3),
            (cx + 2, cy + 3),
            (cx + 1, cy + 4),
            (cx - 1, cy + 4),
        ])
    def _draw_back_arm(surface, cx, cy, facing, phase, action):
        """The non-weapon arm (background)."""
        back_dir = -facing
        sway = math.sin(phase * 0.6) * 1
        shoulder_x = cx + back_dir * 11
        shoulder_y = cy - 8
        elbow_x = cx + back_dir * 15
        elbow_y = cy - 2 + int(sway)
        hand_x = cx + back_dir * 13
        hand_y = cy + 6 + int(sway * 0.5)
        _NS_xareth._aaline(surface, _NS_xareth.PALETTE["shadow_deep"],
                           (shoulder_x + 1, shoulder_y + 1), (elbow_x + 1, elbow_y + 1), 5)
        _NS_xareth._aaline(surface, _NS_xareth.PALETTE["skin_darkest"],
                           (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_xareth._aaline(surface, _NS_xareth.PALETTE["skin_dark"],
                           (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_xareth._aaline(surface, _NS_xareth.PALETTE["skin_mid"],
                           (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 1)
        _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["armor_darkest"], (elbow_x, elbow_y), 3)
        _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["armor_mid"], (elbow_x, elbow_y), 2)
        _NS_xareth._aaline(surface, _NS_xareth.PALETTE["skin_darkest"],
                           (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_xareth._aaline(surface, _NS_xareth.PALETTE["skin_dark"],
                           (elbow_x, elbow_y), (hand_x, hand_y), 2)
        # Fist.
        _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["skin_darkest"], (hand_x, hand_y), 3)
        _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["skin_dark"], (hand_x, hand_y), 2)
        _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["skin_mid"], (hand_x - 1, hand_y - 1), 1)
    def _draw_weapon_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding glowing gauntlet."""
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                swing_angle = -math.pi * 0.15 - t * math.pi * 0.5
                arm_length = 20
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                t_eased = 1 - (1 - t) ** 2
                swing_angle = -math.pi * 0.65 + t_eased * math.pi * 0.95
                arm_length = 20 + int(t_eased * 6)
            else:
                t = (attack_progress - 0.6) / 0.4
                swing_angle = math.pi * 0.3 - t * math.pi * 0.45
                arm_length = 26 - int(t * 6)
        else:
            swing_angle = math.pi * 0.15 + math.sin(phase * 0.6) * 0.1
            arm_length = 20
        shoulder_x = cx + facing * 11
        shoulder_y = cy - 8
        hand_x = shoulder_x + int(math.cos(swing_angle) * arm_length) * facing
        hand_y = shoulder_y + int(math.sin(swing_angle) * arm_length)
        # Elbow midpoint.
        elbow_x = (shoulder_x + hand_x) // 2
        elbow_y = (shoulder_y + hand_y) // 2
        # Upper arm.
        _NS_xareth._aaline(surface, _NS_xareth.PALETTE["shadow_deep"],
                           (shoulder_x + 1, shoulder_y + 1), (elbow_x + 1, elbow_y + 1), 6)
        _NS_xareth._aaline(surface, _NS_xareth.PALETTE["skin_darkest"],
                           (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_xareth._aaline(surface, _NS_xareth.PALETTE["skin_dark"],
                           (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_xareth._aaline(surface, _NS_xareth.PALETTE["skin_mid"],
                           (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 2)
        # Elbow joint.
        _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["armor_darkest"], (elbow_x, elbow_y), 4)
        _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["armor_dark"], (elbow_x, elbow_y), 3)
        _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["armor_mid"], (elbow_x - 1, elbow_y - 1), 2)
        pygame.draw.rect(surface, _NS_xareth.PALETTE["crystal_mid"], (elbow_x, elbow_y, 1, 1))
        # Forearm.
        _NS_xareth._aaline(surface, _NS_xareth.PALETTE["skin_darkest"],
                           (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_xareth._aaline(surface, _NS_xareth.PALETTE["skin_dark"],
                           (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_xareth._aaline(surface, _NS_xareth.PALETTE["skin_mid"],
                           (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
        # GAUNTLET (armored fist with crystal).
        _NS_xareth._draw_gauntlet(surface, hand_x, hand_y, facing, phase, swing_angle)
    def _draw_gauntlet(surface, hx, hy, facing, phase, angle):
        """Armored gauntlet with green crystal at knuckle."""
        # Base gauntlet.
        _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["shadow_deep"], (hx + 1, hy + 1), 5)
        _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["armor_darkest"], (hx, hy), 5)
        _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["armor_dark"], (hx, hy), 4)
        _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["armor_mid"], (hx - 1, hy - 1), 3)
        _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["armor_light"], (hx - 2, hy - 2), 1)
        # Extended crystal spikes forward.
        tip_x = hx + int(math.cos(angle) * 6) * facing
        tip_y = hy + int(math.sin(angle) * 6)
        # Crystal glow around gauntlet.
        crystal_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(7, 0, -1):
            alpha = _NS_xareth._alpha(150 * (7 - r) / 7 * crystal_pulse)
            _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["crystal_dark"], alpha), (tip_x, tip_y), r)
        # Crystal spike at knuckle.
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["crystal_darkest"], [
            (tip_x - 2, tip_y - 2),
            (tip_x + 2, tip_y - 2),
            (tip_x + 3, tip_y + 1),
            (tip_x, tip_y + 4),
            (tip_x - 3, tip_y + 1),
        ])
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["crystal_dark"], [
            (tip_x - 1, tip_y - 2),
            (tip_x + 1, tip_y - 2),
            (tip_x + 2, tip_y + 1),
            (tip_x, tip_y + 3),
            (tip_x - 2, tip_y + 1),
        ])
        _NS_xareth._poly(surface, _NS_xareth.PALETTE["crystal_mid"], [
            (tip_x, tip_y - 1),
            (tip_x + 1, tip_y + 1),
            (tip_x, tip_y + 2),
            (tip_x - 1, tip_y + 1),
        ])
        pygame.draw.rect(surface, _NS_xareth.PALETTE["crystal_light"], (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_xareth.PALETTE["crystal_hot"], (tip_x, tip_y, 1, 1))
    # ================= MELEE SWING FX =================
    def _draw_gauntlet_swing(surface, boss, x, y, progress):
        """Green crystal energy trail from gauntlet swing."""
        if progress < 0.30 or progress > 0.80:
            return
        facing = boss.direction
        if progress < 0.6:
            swing_t = (progress - 0.30) / 0.30
        else:
            swing_t = 1.0 - (progress - 0.6) / 0.20
        swing_t = max(0.0, min(1.0, swing_t))
        alpha_base = _NS_xareth._alpha(255 * swing_t)
        if alpha_base <= 5:
            return
        cx_sh = x + facing * 11
        cy_sh = y - 8
        if progress < 0.35:
            current_angle = -math.pi * 0.65
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            t_eased = 1 - (1 - t) ** 2
            current_angle = -math.pi * 0.65 + t_eased * math.pi * 0.95
        else:
            current_angle = math.pi * 0.3
        start_angle = -math.pi * 0.65
        arc_length = 30
        FX_W, FX_H = 220, 220
        fx_surf = pygame.Surface((FX_W, FX_H), pygame.SRCALPHA)
        ox, oy = FX_W // 2, FX_H // 2
        def to_fx(wx, wy):
            return (wx - cx_sh + ox, wy - cy_sh + oy)
        # ARC TRAIL layered (green + purple).
        for thickness, alpha_mult, color, radius_off in [
            (9, 0.35, _NS_xareth.PALETTE["void_dark"], 3),
            (7, 0.55, _NS_xareth.PALETTE["void_mid"], 1),
            (5, 0.80, _NS_xareth.PALETTE["crystal_dark"], 0),
            (3, 1.00, _NS_xareth.PALETTE["crystal_mid"], 0),
            (2, 1.00, _NS_xareth.PALETTE["crystal_light"], 0),
            (1, 1.00, _NS_xareth.PALETTE["crystal_hot"], 0),
        ]:
            steps = 24
            prev = None
            for s in range(steps + 1):
                seg_t = s / steps
                seg_alpha = _NS_xareth._alpha(alpha_base * alpha_mult * (0.25 + 0.75 * seg_t))
                if seg_alpha <= 0:
                    prev = None
                    continue
                a = start_angle + (current_angle - start_angle) * seg_t
                r = arc_length + radius_off
                wx = cx_sh + int(math.cos(a) * r) * facing
                wy = cy_sh + int(math.sin(a) * r)
                p = to_fx(wx, wy)
                if prev is not None:
                    pygame.draw.line(fx_surf, (*color, seg_alpha), prev, p, thickness)
                prev = p
        # LEADING EDGE FLASH.
        lead_wx = cx_sh + int(math.cos(current_angle) * (arc_length + 4)) * facing
        lead_wy = cy_sh + int(math.sin(current_angle) * (arc_length + 4))
        lfx, lfy = to_fx(lead_wx, lead_wy)
        for r in range(12, 0, -1):
            a = _NS_xareth._alpha(alpha_base * (12 - r) / 12 * 1.3)
            if a > 0:
                pygame.draw.circle(fx_surf, (*_NS_xareth.PALETTE["crystal_mid"], a), (lfx, lfy), r)
        pygame.draw.circle(fx_surf, (*_NS_xareth.PALETTE["crystal_hot"], alpha_base), (lfx, lfy), 3)
        pygame.draw.circle(fx_surf, (*_NS_xareth.PALETTE["white"], alpha_base), (lfx, lfy), 1)
        # SLASH LINES.
        for slash_i in range(3):
            slash_offset = (slash_i - 1) * 0.10
            slash_a = current_angle + slash_offset
            slash_alpha = _NS_xareth._alpha(alpha_base * (1 - abs(slash_offset) * 4))
            if slash_alpha <= 0:
                continue
            inner_r = arc_length - 10
            outer_r = arc_length + 12
            wx1 = cx_sh + int(math.cos(slash_a) * inner_r) * facing
            wy1 = cy_sh + int(math.sin(slash_a) * inner_r)
            wx2 = cx_sh + int(math.cos(slash_a) * outer_r) * facing
            wy2 = cy_sh + int(math.sin(slash_a) * outer_r)
            p1 = to_fx(wx1, wy1)
            p2 = to_fx(wx2, wy2)
            pygame.draw.line(fx_surf, (*_NS_xareth.PALETTE["crystal_light"], slash_alpha), p1, p2, 4 - slash_i)
            pygame.draw.line(fx_surf, (*_NS_xareth.PALETTE["white"], slash_alpha), p1, p2, 1)
        # TEMPORAL SPARKS (with void purple mixed in).
        for i in range(16):
            spark_seed = i * 0.7 + progress * 4
            spark_a = current_angle + math.sin(spark_seed) * 0.5
            spark_r = arc_length + 6 + (i % 4) * 5 + int(swing_t * 10)
            wspx = cx_sh + int(math.cos(spark_a) * spark_r) * facing
            wspy = cy_sh + int(math.sin(spark_a) * spark_r)
            spx, spy = to_fx(wspx, wspy)
            spark_alpha = _NS_xareth._alpha(alpha_base * (0.7 + (i % 3) * 0.1))
            tail_wx = wspx - int(math.cos(spark_a) * 4) * facing
            tail_wy = wspy - int(math.sin(spark_a) * 4)
            tfx, tfy = to_fx(tail_wx, tail_wy)
            spark_color = _NS_xareth.PALETTE["crystal_mid"] if i % 2 == 0 \
                else _NS_xareth.PALETTE["void_light"]
            pygame.draw.line(fx_surf, (*spark_color, spark_alpha), (tfx, tfy), (spx, spy), 2)
            pygame.draw.rect(fx_surf, (*_NS_xareth.PALETTE["crystal_hot"], spark_alpha), (spx, spy, 2, 2))
            pygame.draw.rect(fx_surf, (*_NS_xareth.PALETTE["white"], spark_alpha), (spx, spy, 1, 1))
        # IMPACT BURST.
        if 0.55 < progress < 0.72:
            impact_t = (progress - 0.55) / 0.17
            impact_alpha = _NS_xareth._alpha(240 * (1 - impact_t))
            if impact_alpha > 0:
                impact_wx = cx_sh + int(math.cos(math.pi * 0.2) * (arc_length + 8)) * facing
                impact_wy = cy_sh + int(math.sin(math.pi * 0.2) * (arc_length + 8))
                ifx, ify = to_fx(impact_wx, impact_wy)
                for burst_r in range(int(6 + impact_t * 18), 0, -2):
                    a = _NS_xareth._alpha(impact_alpha * (20 - burst_r) / 20)
                    if a > 0:
                        pygame.draw.circle(fx_surf, (*_NS_xareth.PALETTE["crystal_light"], a), (ifx, ify), burst_r)
                for i in range(10):
                    a_burst = i * math.pi / 5
                    bx = ifx + int(math.cos(a_burst) * (8 + impact_t * 14))
                    by = ify + int(math.sin(a_burst) * (8 + impact_t * 14))
                    pygame.draw.line(fx_surf, (*_NS_xareth.PALETTE["crystal_mid"], impact_alpha), (ifx, ify), (bx, by), 2)
                    pygame.draw.rect(fx_surf, (*_NS_xareth.PALETTE["crystal_hot"], impact_alpha), (bx, by, 1, 1))
        surface.blit(fx_surf, (cx_sh - ox, cy_sh - oy))
    # ================= AMBIENT / GROUND =================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 15 - radius, 120 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (30, 10, 60, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (80, 30, 140, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_void_aura(surface, x, y, phase):
        """Purple void aura + crystal green highlights."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_xareth._alpha((90 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_xareth._aacircle(aura, (*_NS_xareth.PALETTE["void_dark"], alpha), (110, 100), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_xareth._alpha((55 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_xareth._aacircle(aura, (*_NS_xareth.PALETTE["void_mid"], alpha), (110, 100), radius)
        # Green crystal inner glow.
        for radius in range(30, 5, -3):
            alpha = _NS_xareth._alpha((30 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_xareth._aacircle(aura, (*_NS_xareth.PALETTE["crystal_dark"], alpha), (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))
        # Floating particles (purple + green).
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 38 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            color = _NS_xareth.PALETTE["void_mid"] if i % 3 != 0 else _NS_xareth.PALETTE["crystal_mid"]
            hot_color = _NS_xareth.PALETTE["void_hot"] if i % 3 != 0 else _NS_xareth.PALETTE["crystal_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot_color, (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring with runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_xareth.PALETTE["void_dark"], 200), (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_xareth.PALETTE["void_darkest"], 220), (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_xareth.PALETTE["void_mid"], 180), (25, 22, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_xareth.PALETTE["crystal_dark"], 160), (40, 24, 90, 14), 1)
        # Clock/rune markers.
        for i in range(12):
            angle = i * math.pi / 6
            x1 = 85 + int(math.cos(angle) * 60)
            y1 = 30 + int(math.sin(angle) * 10)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_xareth.PALETTE["void_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_xareth.PALETTE["crystal_light"], _NS_xareth._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    def _draw_hover_particles(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Void particles rising below floating body."""
        strength = 1.5 if intense else 1.0
        # Purple mist.
        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(35, 3, -3):
            alpha = _NS_xareth._alpha((35 - radius) * 2.8 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist, (*_NS_xareth.PALETTE["void_dark"], alpha),
                                    (75 - radius * 2, 25 - radius // 3, radius * 4, max(3, radius // 2)))
        for radius in range(22, 3, -2):
            alpha = _NS_xareth._alpha((22 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist, (*_NS_xareth.PALETTE["void_mid"], alpha),
                                    (75 - radius, 25 - radius // 4, radius * 2, max(2, radius // 3)))
        surface.blit(mist, (cx - 75, cy - 10))
        # Rising purple/green bubbles.
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 28)
            alpha = _NS_xareth._alpha(200 * (1 - t) * strength)
            if alpha <= 0:
                continue
            color = _NS_xareth.PALETTE["void_dark"] if i % 3 != 0 else _NS_xareth.PALETTE["crystal_dark"]
            mid_color = _NS_xareth.PALETTE["void_mid"] if i % 3 != 0 else _NS_xareth.PALETTE["crystal_mid"]
            hot_color = _NS_xareth.PALETTE["void_hot"] if i % 3 != 0 else _NS_xareth.PALETTE["crystal_light"]
            _NS_xareth._aacircle(surface, (*color, alpha), (sx, sy), 3)
            _NS_xareth._aacircle(surface, (*mid_color, alpha), (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*hot_color, alpha), (sx, sy - 1, 1, 1))
        # Trail.
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_xareth._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["void_dark"], alpha),
                                     (sx, sy), max(2, 7 - i))
                _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["void_mid"], alpha),
                                     (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface, (*_NS_xareth.PALETTE["crystal_light"], alpha),
                                 (sx, sy - 1, 2, 2))
    # ================= SKILL Q — VOID LOCK PROJECTILE =================
    def _draw_void_lock_projectile(surface, boss, x, y, timer, phase):
        """Purple time orb projectile with comet trail."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_xareth._target_position(boss, x, y)
        if progress < 0.15:
            # Charge at gauntlet.
            t = progress / 0.15
            gauntlet_x = x + facing * 30
            gauntlet_y = y - 4
            cr = int(3 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_xareth._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["void_dark"], alpha),
                                     (gauntlet_x, gauntlet_y), r)
            _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["void_mid"], (gauntlet_x, gauntlet_y), cr - 2)
            _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["void_light"], (gauntlet_x, gauntlet_y), max(1, cr - 4))
            _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["crystal_light"], (gauntlet_x, gauntlet_y), max(1, cr - 6))
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                sx = gauntlet_x + int(math.cos(angle) * (cr + 3))
                sy = gauntlet_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_xareth.PALETTE["void_hot"], (sx, sy, 1, 1))
        else:
            t = (progress - 0.15) / 0.85
            start_x = x + facing * 34
            start_y = y - 4
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Comet trail.
            for i in range(11):
                trail_t = max(0.0, t - i * 0.045)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_xareth._alpha(240 - i * 22)
                size = max(1, 9 - i)
                _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["void_darkest"], alpha), (px, py), size)
                _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["void_dark"], alpha), (px, py), max(1, size - 1))
                _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["void_mid"], alpha), (px, py), max(1, size - 2))
                _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["void_light"], alpha), (px, py), max(1, size - 3))
                if i < 5:
                    for s in range(3):
                        spark_x = px + int(math.sin(t * 8 + i + s) * (size + 2))
                        spark_y = py + int(math.cos(t * 8 + i + s) * (size + 2))
                        pygame.draw.rect(surface, (*_NS_xareth.PALETTE["void_hot"], alpha), (spark_x, spark_y, 1, 1))
            # Head.
            for r in range(14, 3, -2):
                alpha = _NS_xareth._alpha(100 * (14 - r) / 14)
                _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["void_light"], alpha), (bx, by), r)
            _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["void_darkest"], (bx, by), 10)
            _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["void_dark"], (bx, by), 8)
            _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["void_mid"], (bx, by), 5)
            _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["void_light"], (bx, by), 3)
            _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["crystal_light"], (bx, by), 1)
            pygame.draw.rect(surface, _NS_xareth.PALETTE["white"], (bx, by, 1, 1))
            # Impact splash.
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(12 + st * 28)
                alpha = _NS_xareth._alpha(240 * (1 - st))
                _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["void_darkest"], alpha), (tx, ty), radius + 4, 3)
                _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["void_dark"], alpha), (tx, ty), radius, 3)
                _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["void_mid"], alpha), (tx, ty), max(1, radius - 5), 2)
                _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["void_light"], alpha), (tx, ty), max(1, radius - 12), 1)
                # Sparks.
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface, (*_NS_xareth.PALETTE["void_hot"], alpha), (ex, ey, 2, 2))
                    pygame.draw.rect(surface, (*_NS_xareth.PALETTE["crystal_light"], alpha), (ex, ey, 1, 1))
                # Clock face pop.
                _NS_xareth._draw_clock_mark(surface, tx, ty - radius - 8, alpha)
    def _draw_clock_mark(surface, cx, cy, alpha):
        """Small clock icon indicating time stun."""
        _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["void_darkest"], alpha), (cx, cy), 5)
        _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["void_light"], alpha), (cx, cy), 4)
        _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["void_hot"], alpha), (cx, cy), 3, 1)
        # Clock hands.
        pygame.draw.line(surface, (*_NS_xareth.PALETTE["void_darkest"], alpha), (cx, cy), (cx, cy - 3), 1)
        pygame.draw.line(surface, (*_NS_xareth.PALETTE["void_darkest"], alpha), (cx, cy), (cx + 2, cy), 1)
    # ================= SKILL W — AEON RIFT (teleport) =================
    def _draw_aeon_rift_ground(surface, boss, x, y, timer, pulse):
        """Rift portal effect at original position (fade)."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if 0.15 < progress < 0.85:
            phase_t = 0
            if progress < 0.4:
                phase_t = (progress - 0.15) / 0.25
            elif progress > 0.6:
                phase_t = 1 - (progress - 0.6) / 0.25
            r = int(30 * phase_t)
            if r > 3:
                alpha = _NS_xareth._alpha(200 * phase_t)
                # Portal rings.
                for i in range(3):
                    _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["void_darkest"], alpha),
                                         (x, y + 20), r - i * 3, 2)
                    _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["void_mid"], alpha),
                                         (x, y + 20), r - i * 3 - 1, 1)
    def _draw_aeon_rift_foreground(surface, boss, x, y, timer, pulse, progress):
        """Purple portal + afterimage during teleport."""
        # Rift open/close visuals.
        if progress < 0.3 or progress > 0.7:
            fade_t = progress / 0.3 if progress < 0.3 else (1 - progress) / 0.3
            fade_t = max(0.0, min(1.0, fade_t))
            # Ghost body outline glow.
            for r in range(30, 0, -3):
                alpha = _NS_xareth._alpha(100 * (30 - r) / 30 * fade_t)
                if alpha > 0:
                    _NS_xareth._aacircle(surface, (*_NS_xareth.PALETTE["void_light"], alpha), (x, y), r)
            # Vertical light beams (teleport streaks).
            for i in range(8):
                offset = (i - 4) * 4
                alpha = _NS_xareth._alpha(200 * fade_t)
                pygame.draw.line(surface, (*_NS_xareth.PALETTE["void_light"], alpha),
                                 (x + offset, y - 30), (x + offset, y + 30), 1)
                pygame.draw.line(surface, (*_NS_xareth.PALETTE["crystal_light"], alpha),
                                 (x + offset, y - 20), (x + offset, y + 20), 1)
        # Between 0.3-0.7: rift portal fully open (body invisible).
        if 0.25 < progress < 0.75:
            portal_t = math.sin((progress - 0.25) / 0.5 * math.pi)
            r_out = int(40 * portal_t)
            portal = pygame.Surface((r_out * 2 + 20, r_out * 2 + 20), pygame.SRCALPHA)
            pc = (r_out + 10, r_out + 10)
            # Dark center.
            for r in range(r_out, 0, -2):
                alpha = _NS_xareth._alpha(220 * (r_out - r) / r_out * portal_t)
                _NS_xareth._aacircle(portal, (*_NS_xareth.PALETTE["void_darkest"], alpha), pc, r)
            for r in range(r_out - 4, 0, -2):
                alpha = _NS_xareth._alpha(180 * portal_t)
                _NS_xareth._aacircle(portal, (*_NS_xareth.PALETTE["void_dark"], alpha), pc, r, 1)
            # Swirling energy.
            for i in range(16):
                angle = pulse * 3 + i * math.pi / 8
                spiral_r = r_out * (0.4 + (i % 4) * 0.15)
                sx = pc[0] + int(math.cos(angle) * spiral_r)
                sy = pc[1] + int(math.sin(angle) * spiral_r)
                alpha = _NS_xareth._alpha(220 * portal_t)
                pygame.draw.rect(portal, (*_NS_xareth.PALETTE["void_hot"], alpha), (sx, sy, 2, 2))
                pygame.draw.rect(portal, (*_NS_xareth.PALETTE["crystal_light"], alpha), (sx, sy, 1, 1))
            # Edge ring.
            _NS_xareth._aacircle(portal, (*_NS_xareth.PALETTE["void_light"], _NS_xareth._alpha(240 * portal_t)),
                                 pc, r_out, 2)
            surface.blit(portal, (x - r_out - 10, y - r_out - 10))
    # ================= SKILL E — TEMPORAL FIELD =================
    def _draw_temporal_field_ground(surface, boss, x, y, timer, pulse):
        """Purple slowing field on ground."""
        tx, ty = _NS_xareth._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_xareth.PALETTE["void_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_xareth.PALETTE["void_dark"], 180),
                                (tx - r + 3, ty - r // 3 + 2, r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_xareth.PALETTE["void_mid"], 130),
                                (tx - r + 8, ty - r // 3 + 4, r * 2 - 16, r * 2 // 3 - 8))
    def _draw_temporal_field_foreground(surface, boss, x, y, timer, pulse):
        """Clock hands + slowing distortion."""
        tx, ty = _NS_xareth._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 3))
        if r < 5:
            return
        # Multiple slow clock icons around edge.
        num_clocks = 5
        for i in range(num_clocks):
            angle = i * math.pi * 2 / num_clocks + pulse * 0.2
            cx_c = tx + int(math.cos(angle) * r * 0.7)
            cy_c = ty + int(math.sin(angle) * r * 0.4)
            _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["void_darkest"], (cx_c, cy_c - 12), 6)
            _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["void_light"], (cx_c, cy_c - 12), 5)
            _NS_xareth._aacircle(surface, _NS_xareth.PALETTE["void_hot"], (cx_c, cy_c - 12), 4, 1)
            # Clock hands rotating slowly.
            hand_angle = pulse * 0.3 + i
            hx1 = cx_c + int(math.cos(hand_angle) * 3)
            hy1 = cy_c - 12 + int(math.sin(hand_angle) * 3)
            pygame.draw.line(surface, _NS_xareth.PALETTE["void_darkest"],
                             (cx_c, cy_c - 12), (hx1, hy1), 1)
        # Rising particles slowed.
        for i in range(16):
            angle = i * math.pi * 2 / 16 + pulse * 0.1
            col_dist = int(r * (0.5 + (i % 3) * 0.2))
            col_x = tx + int(math.cos(angle) * col_dist)
            col_y_base = ty + int(math.sin(angle) * col_dist * 0.4)
            for layer in range(4):
                layer_t = (pulse * 0.4 + i * 0.2 + layer * 0.2) % 1.0
                layer_y = col_y_base - int(layer_t * 18)
                layer_alpha = _NS_xareth._alpha(180 * (1 - layer_t))
                pygame.draw.rect(surface, (*_NS_xareth.PALETTE["void_light"], layer_alpha),
                                 (col_x, layer_y, 1, 1))
                pygame.draw.rect(surface, (*_NS_xareth.PALETTE["crystal_light"], layer_alpha),
                                 (col_x, layer_y - 1, 1, 1))
    # ================= SKILL R — CHRONO PRISON =================
    def _draw_chrono_prison_ground(surface, boss, x, y, timer, pulse):
        """Ground base for dome."""
        tx, ty = _NS_xareth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(75 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_xareth.PALETTE["void_darkest"], 220),
                                (tx - r, ty - r // 4, r * 2, r * 2 // 4))
            pygame.draw.ellipse(surface, (*_NS_xareth.PALETTE["void_dark"], 200),
                                (tx - r + 4, ty - r // 4 + 2, r * 2 - 8, r * 2 // 4 - 4), 2)
    def _draw_chrono_prison_dome(surface, boss, x, y, timer, pulse):
        """Large purple dome trapping enemies."""
        tx, ty = _NS_xareth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(70 * min(1.0, progress * 3))
        if r < 5:
            return
        # Dome as arc — semi-circle top.
        dome = pygame.Surface((r * 2 + 20, r + 20), pygame.SRCALPHA)
        dc = (r + 10, r + 10)
        # Dark fill.
        pygame.draw.ellipse(dome, (*_NS_xareth.PALETTE["void_darkest"], 130),
                            (10, 10, r * 2, r * 2))
        # Clip bottom by drawing only the top half via clipping rect trick:
        # Draw ellipse then blit only top half.
        top_half = pygame.Surface((r * 2 + 20, r + 12), pygame.SRCALPHA)
        top_half.blit(dome, (0, 0), (0, 0, r * 2 + 20, r + 12))
        # Draw layered dome rings on top_half.
        for i, (thickness, alpha_val) in enumerate([(3, 140), (2, 180), (1, 220)]):
            pygame.draw.ellipse(top_half, (*_NS_xareth.PALETTE["void_mid"], alpha_val),
                                (10 + i, 10 + i, r * 2 - i * 2, r * 2 - i * 2), thickness)
            pygame.draw.ellipse(top_half, (*_NS_xareth.PALETTE["void_light"], alpha_val),
                                (10 + i + 1, 10 + i + 1, r * 2 - i * 2 - 2, r * 2 - i * 2 - 2), 1)
        # Vertical bars inside dome (energy cage).
        for i in range(10):
            bar_x = 10 + i * (r * 2 // 10) + r // 10
            alpha = _NS_xareth._alpha(120)
            pygame.draw.line(top_half, (*_NS_xareth.PALETTE["void_hot"], alpha),
                             (bar_x, r + 10), (bar_x, 15), 1)
        # Rotating clock symbol on top.
        clock_x = dc[0]
        clock_y = 20
        _NS_xareth._aacircle(top_half, (*_NS_xareth.PALETTE["void_darkest"], 240), (clock_x, clock_y), 8)
        _NS_xareth._aacircle(top_half, (*_NS_xareth.PALETTE["void_light"], 240), (clock_x, clock_y), 6)
        _NS_xareth._aacircle(top_half, (*_NS_xareth.PALETTE["void_hot"], 240), (clock_x, clock_y), 5, 1)
        hand_a = pulse * 2
        pygame.draw.line(top_half, _NS_xareth.PALETTE["void_darkest"],
                         (clock_x, clock_y),
                         (clock_x + int(math.cos(hand_a) * 4), clock_y + int(math.sin(hand_a) * 4)), 1)
        # Swirling particles inside.
        for i in range(20):
            angle = pulse * 1.2 + i * math.pi / 10
            spiral_r = r * (0.3 + (i % 5) * 0.14)
            sx = dc[0] + int(math.cos(angle) * spiral_r)
            sy = dc[1] + int(math.sin(angle) * spiral_r * 0.5)
            if sy > r + 10:
                continue
            pygame.draw.rect(top_half, _NS_xareth.PALETTE["crystal_light"], (sx, sy, 2, 2))
            pygame.draw.rect(top_half, _NS_xareth.PALETTE["white"], (sx, sy, 1, 1))
        surface.blit(top_half, (tx - r - 10, ty - r - 10))



# ====================================================================
# GRIMKOR (SAWMILL WARLORD) - TRUE BOSS
# ====================================================================

class _NS_grimkor:
    """Namespace grimkor - mechanical sawmill boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        "iron_darkest": (18, 15, 12),
        "iron_dark": (45, 40, 35),
        "iron_mid": (95, 88, 78),
        "iron_light": (155, 148, 135),
        "iron_edge": (200, 195, 180),
        "iron_shine": (240, 235, 220),
        "copper_darkest": (35, 18, 8),
        "copper_dark": (95, 50, 20),
        "copper_mid": (175, 105, 40),
        "copper_light": (230, 165, 75),
        "copper_shine": (255, 220, 140),
        "fire_darkest": (30, 8, 2),
        "fire_dark": (110, 30, 8),
        "fire_mid": (220, 90, 20),
        "fire_light": (255, 165, 50),
        "fire_hot": (255, 220, 120),
        "fire_shine": (255, 250, 200),
        "blade_darkest": (20, 22, 30),
        "blade_dark": (60, 68, 85),
        "blade_mid": (130, 140, 160),
        "blade_light": (200, 210, 225),
        "blade_shine": (245, 250, 255),
        "skin_darkest": (25, 40, 20),
        "skin_dark": (55, 90, 45),
        "skin_mid": (110, 155, 80),
        "skin_light": (170, 210, 130),
        "eye_socket": (5, 8, 3),
        "eye_dark": (60, 80, 15),
        "eye_mid": (180, 220, 40),
        "eye_light": (240, 255, 120),
        "eye_glow": (255, 255, 200),
        "smoke_dark": (35, 32, 30),
        "smoke_mid": (100, 95, 90),
        "smoke_light": (180, 175, 170),
        "chain_dark": (25, 22, 20),
        "chain_mid": (85, 78, 70),
        "chain_light": (170, 160, 145),
        "wood_dark": (55, 30, 10),
        "wood_mid": (130, 80, 35),
        "wood_light": (200, 155, 90),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_grimkor._clamp(color)
        if _NS_grimkor.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_grimkor._clamp(color)
        if _NS_grimkor.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_grimkor._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ================= ENTRY POINT =================
    def draw_grimkor(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_grimkor._detect_moving(boss)
        _NS_grimkor._update_gk_attack_anim(boss)
        attacking = (
            getattr(boss, "_gk_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        _NS_grimkor._draw_fire_aura(surface, x, y, pulse)
        _NS_grimkor._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        if active_skill == "w":
            _NS_grimkor._draw_chainsaw_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_grimkor._draw_reactive_ground(surface, boss, x, y, skill_timer, pulse)
        if attacking:
            _NS_grimkor._draw_gk_attack(surface, boss, x, y)
        elif moving:
            _NS_grimkor._draw_gk_walk(surface, boss, x, y)
        else:
            _NS_grimkor._draw_gk_idle(surface, boss, x, y)
        if active_skill == "r":
            _NS_grimkor._draw_reactive_bubble(surface, boss, x, y, skill_timer, pulse)
        if active_skill == "q":
            _NS_grimkor._draw_whirling_death(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_grimkor._draw_chainsaw_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_grimkor._draw_timber_chain(surface, boss, x, y, skill_timer, pulse)
    # ================= ANIMATION STATE =================
    def _update_gk_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_gk_previous_timer", 0))
        active = bool(getattr(boss, "_gk_attack_active", False))
        # Trigger: timer just reset to 0 (previous was high).
        if not active and previous > timer and previous >= cooldown - 2:
            boss._gk_attack_active = True
            boss._gk_attack_frame = 0
            active = True
        elif active:
            boss._gk_attack_frame = int(getattr(boss, "_gk_attack_frame", 0)) + 1
            # End animation after cooldown frames.
            if boss._gk_attack_frame >= cooldown:
                boss._gk_attack_active = False
                boss._gk_attack_frame = 0
                active = False
        boss._gk_previous_timer = timer
        boss._gk_attack_progress = (
            min(1.0, getattr(boss, "_gk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_gk_last_x"):
            boss._gk_last_x = boss.x
            boss._gk_last_y = boss.y
            return False
        dx = abs(boss.x - boss._gk_last_x)
        dy = abs(boss.y - boss._gk_last_y)
        boss._gk_last_x = boss.x
        boss._gk_last_y = boss.y
        return dx + dy > 0.3
    # ================= POSE ROUTERS =================
    def _draw_gk_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_grimkor._draw_shadow(surface, x, y + 50)
        _NS_grimkor._draw_steam_exhaust(surface, x, y - 20, boss.pulse, boss.direction)
        _NS_grimkor._draw_gk_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")
    def _draw_gk_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 6)
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_grimkor._draw_shadow(surface, x + sway, y + 50)
        _NS_grimkor._draw_steam_exhaust(surface, x + sway, y - 20, phase, boss.direction, intense=True)
        _NS_grimkor._draw_gk_body(surface, x + sway, y + bob, boss.direction, phase, "walk")
    def _draw_gk_attack(surface, boss, x, y):
        progress = getattr(boss, "_gk_attack_progress", None)
        if progress is None or progress <= 0:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 2)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            t_eased = 1 - (1 - t) ** 2
            lunge = int((-3 + t_eased * 10)) * boss.direction
            lift = int(2 - t_eased * 3)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(7 * (1 - t)) * boss.direction
            lift = int(-1 + t * 1)
        _NS_grimkor._draw_shadow(surface, x + lunge, y + 50)
        _NS_grimkor._draw_steam_exhaust(surface, x + lunge, y - 20, boss.pulse, boss.direction, intense=True)
        _NS_grimkor._draw_gk_body(surface, x + lunge, y - lift, boss.direction, boss.pulse, "attack", progress)
        _NS_grimkor._draw_saw_swing(surface, boss, x + lunge, y - lift, progress)
    # ================= BODY =================
    def _draw_gk_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        _NS_grimkor._draw_side_gears(surface, cx, cy, facing, phase)
        _NS_grimkor._draw_mech_legs(surface, cx, cy + 8, facing, phase, action)
        _NS_grimkor._draw_mech_body(surface, cx, cy, facing, phase)
        _NS_grimkor._draw_goblin_pilot(surface, cx, cy - 4, facing, phase, action)
        _NS_grimkor._draw_shoulder_stacks(surface, cx, cy - 8, facing, phase)
        _NS_grimkor._draw_saw_arm(surface, cx, cy, facing, phase, action, attack_progress)
    def _draw_side_gears(surface, cx, cy, facing, phase):
        gear_x = cx - facing * 18
        gear_y = cy + 4
        gear_r = 12
        rotation = phase * 0.5
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["shadow_deep"], (gear_x + 2, gear_y + 2), gear_r)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["iron_darkest"], (gear_x, gear_y), gear_r)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["iron_dark"], (gear_x, gear_y), gear_r - 1)
        for i in range(10):
            angle = rotation + i * math.pi / 5
            tx = gear_x + int(math.cos(angle) * (gear_r + 2))
            ty = gear_y + int(math.sin(angle) * (gear_r + 2))
            tx2 = gear_x + int(math.cos(angle) * gear_r)
            ty2 = gear_y + int(math.sin(angle) * gear_r)
            pygame.draw.line(surface, _NS_grimkor.PALETTE["iron_darkest"], (tx, ty), (tx2, ty2), 3)
            pygame.draw.line(surface, _NS_grimkor.PALETTE["iron_mid"], (tx, ty), (tx2, ty2), 1)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["iron_mid"], (gear_x, gear_y), gear_r - 3)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["iron_light"], (gear_x - 1, gear_y - 1), gear_r - 5)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["iron_darkest"], (gear_x, gear_y), 2)
    def _draw_mech_legs(surface, cx, cy, facing, phase, action):
        for side in (-1, 1):
            leg_bob = math.sin(phase * 0.8 + side) * 2 if action != "walk" \
                else math.sin(phase * 1.5 + side * math.pi) * 4
            hip_x = cx + side * 8
            hip_y = cy
            knee_x = cx + side * 12
            knee_y = cy + 8 + int(leg_bob)
            foot_x = cx + side * 10
            foot_y = cy + 16 + int(leg_bob * 0.5)
            _NS_grimkor._aaline(surface, _NS_grimkor.PALETTE["shadow_deep"], (hip_x + 1, hip_y + 1), (knee_x + 1, knee_y + 1), 5)
            _NS_grimkor._aaline(surface, _NS_grimkor.PALETTE["iron_darkest"], (hip_x, hip_y), (knee_x, knee_y), 5)
            _NS_grimkor._aaline(surface, _NS_grimkor.PALETTE["iron_dark"], (hip_x, hip_y), (knee_x, knee_y), 3)
            _NS_grimkor._aaline(surface, _NS_grimkor.PALETTE["iron_mid"], (hip_x - 1, hip_y), (knee_x - 1, knee_y), 1)
            _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["iron_darkest"], (knee_x, knee_y), 3)
            _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["copper_dark"], (knee_x, knee_y), 2)
            _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["copper_light"], (knee_x, knee_y), 1)
            _NS_grimkor._aaline(surface, _NS_grimkor.PALETTE["iron_darkest"], (knee_x, knee_y), (foot_x, foot_y), 4)
            _NS_grimkor._aaline(surface, _NS_grimkor.PALETTE["iron_dark"], (knee_x, knee_y), (foot_x, foot_y), 2)
            _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["iron_darkest"], [
                (foot_x - 3, foot_y - 1), (foot_x + 3, foot_y - 1),
                (foot_x + 2, foot_y + 2), (foot_x - 2, foot_y + 2),
            ])
            _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["iron_mid"], [
                (foot_x - 2, foot_y), (foot_x + 2, foot_y),
                (foot_x + 1, foot_y + 1), (foot_x - 1, foot_y + 1),
            ])
    def _draw_mech_body(surface, cx, cy, facing, phase):
        body_shape = [
            (cx - 18, cy), (cx - 20, cy - 4), (cx - 18, cy - 10),
            (cx - 12, cy - 15), (cx - 4, cy - 17), (cx + 4, cy - 17),
            (cx + 12, cy - 15), (cx + 18, cy - 10), (cx + 20, cy - 4),
            (cx + 22, cy + 2), (cx + 20, cy + 8), (cx + 12, cy + 12),
            (cx + 4, cy + 14), (cx - 4, cy + 14), (cx - 12, cy + 12),
            (cx - 20, cy + 8), (cx - 22, cy + 2),
        ]
        _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["shadow_deep"], [(px + 2, py + 3) for px, py in body_shape])
        _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["iron_darkest"], body_shape)
        _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["iron_dark"], [
            (cx - 17, cy - 1), (cx - 18, cy - 8), (cx - 10, cy - 14),
            (cx - 2, cy - 15), (cx + 6, cy - 15), (cx + 12, cy - 12),
            (cx + 18, cy - 6), (cx + 19, cy + 2), (cx + 15, cy + 8),
            (cx + 4, cy + 12), (cx - 6, cy + 12), (cx - 15, cy + 8),
            (cx - 18, cy + 2),
        ])
        _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["iron_mid"], [
            (cx - 14, cy - 3), (cx - 14, cy - 8), (cx - 6, cy - 12),
            (cx + 4, cy - 12), (cx + 12, cy - 9), (cx + 15, cy - 4),
            (cx + 14, cy + 2), (cx - 12, cy + 2),
        ])
        _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["iron_light"], [
            (cx - 8, cy - 8), (cx + 4, cy - 10), (cx + 10, cy - 6),
            (cx + 6, cy - 4), (cx - 4, cy - 4),
        ])
        _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["iron_edge"], [
            (cx - 4, cy - 8), (cx + 2, cy - 9), (cx + 4, cy - 6),
            (cx - 2, cy - 6),
        ])
        pygame.draw.line(surface, _NS_grimkor.PALETTE["iron_darkest"], (cx, cy - 15), (cx, cy + 12), 1)
        rivet_positions = [
            (-14, -8), (-8, -12), (0, -14), (8, -12), (14, -8),
            (-16, 0), (16, 0),
            (-14, 8), (-6, 11), (6, 11), (14, 8),
        ]
        for rx, ry in rivet_positions:
            _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["iron_darkest"], (cx + rx, cy + ry), 2)
            _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["copper_dark"], (cx + rx, cy + ry), 1)
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["copper_light"], (cx + rx, cy + ry, 1, 1))
        furnace_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        fx, fy = cx, cy + 4
        for r in range(6, 0, -1):
            alpha = _NS_grimkor._alpha(180 * (6 - r) / 6 * furnace_pulse)
            _NS_grimkor._aacircle(surface, (*_NS_grimkor.PALETTE["fire_dark"], alpha), (fx, fy), r)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["fire_darkest"], (fx, fy), 4)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["fire_dark"], (fx, fy), 3)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["fire_mid"], (fx, fy), 2)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["fire_hot"], (fx, fy), 1)
        for i in range(3):
            gy = fy - 2 + i * 2
            pygame.draw.line(surface, _NS_grimkor.PALETTE["iron_darkest"], (fx - 3, gy), (fx + 3, gy), 1)
    def _draw_goblin_pilot(surface, cx, cy, facing, phase, action):
        cockpit_y = cy - 10
        _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["shadow_deep"], [
            (cx - 7, cockpit_y - 4), (cx + 7, cockpit_y - 4),
            (cx + 8, cockpit_y), (cx + 6, cockpit_y + 3),
            (cx - 6, cockpit_y + 3), (cx - 8, cockpit_y),
        ])
        head_bob = math.sin(phase * 0.6) * 1
        hx = cx
        hy = cockpit_y + int(head_bob)
        _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["skin_darkest"], [
            (hx - 5, hy - 2), (hx - 5, hy + 2), (hx + 5, hy + 2),
            (hx + 5, hy - 2), (hx + 3, hy - 4), (hx - 3, hy - 4),
        ])
        _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["skin_dark"], [
            (hx - 4, hy - 1), (hx - 4, hy + 2), (hx + 4, hy + 2),
            (hx + 4, hy - 1), (hx + 3, hy - 3), (hx - 3, hy - 3),
        ])
        _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["skin_mid"], [
            (hx - 3, hy), (hx + 3, hy), (hx + 3, hy + 1), (hx - 3, hy + 1),
        ])
        pygame.draw.rect(surface, _NS_grimkor.PALETTE["skin_light"], (hx - 1, hy, 2, 1))
        pygame.draw.rect(surface, _NS_grimkor.PALETTE["skin_darkest"], (hx - 2, hy - 6, 4, 2))
        pygame.draw.rect(surface, _NS_grimkor.PALETTE["eye_dark"], (hx - 1, hy - 6, 2, 1))
        pygame.draw.rect(surface, _NS_grimkor.PALETTE["eye_mid"], (hx, hy - 6, 1, 1))
        _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["skin_dark"], [
            (hx - 5, hy - 1), (hx - 7, hy - 2), (hx - 5, hy + 1),
        ])
        _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["skin_dark"], [
            (hx + 5, hy - 1), (hx + 7, hy - 2), (hx + 5, hy + 1),
        ])
        pygame.draw.rect(surface, _NS_grimkor.PALETTE["skin_mid"], (hx - 6, hy, 1, 1))
        pygame.draw.rect(surface, _NS_grimkor.PALETTE["skin_mid"], (hx + 5, hy, 1, 1))
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_off in (-2, 2):
            ex = hx + eye_off
            ey = hy - 1
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["eye_socket"], (ex - 1, ey - 1, 2, 2))
            for r in range(3, 0, -1):
                alpha = _NS_grimkor._alpha(120 * (3 - r) / 3 * eye_pulse)
                _NS_grimkor._aacircle(surface, (*_NS_grimkor.PALETTE["eye_mid"], alpha), (ex, ey), r)
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["eye_dark"], (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["eye_mid"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["eye_light"], (ex, ey, 1, 1))
        if action == "attack":
            mouth_y = hy + 2
            pygame.draw.line(surface, _NS_grimkor.PALETTE["shadow_deep"], (hx - 2, mouth_y), (hx + 2, mouth_y), 1)
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["iron_edge"], (hx - 1, mouth_y, 1, 2))
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["iron_edge"], (hx + 1, mouth_y, 1, 2))
        else:
            pygame.draw.line(surface, _NS_grimkor.PALETTE["shadow_deep"], (hx - 1, hy + 2), (hx + 1, hy + 2), 1)
    def _draw_shoulder_stacks(surface, cx, cy, facing, phase):
        for i, offset in enumerate((-11, -6, 6, 11)):
            stack_x = cx + offset
            stack_top_y = cy - 6
            stack_bot_y = cy + 2
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["shadow_deep"], (stack_x - 1, stack_top_y + 1, 4, stack_bot_y - stack_top_y))
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["iron_darkest"], (stack_x - 2, stack_top_y, 4, stack_bot_y - stack_top_y))
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["iron_dark"], (stack_x - 1, stack_top_y, 3, stack_bot_y - stack_top_y))
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["iron_mid"], (stack_x - 1, stack_top_y, 1, stack_bot_y - stack_top_y))
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["copper_dark"], (stack_x - 2, stack_top_y - 1, 4, 1))
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["copper_mid"], (stack_x - 1, stack_top_y - 1, 2, 1))
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["shadow_deep"], (stack_x - 1, stack_top_y, 2, 1))
    def _draw_saw_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Arm with proper swing rotation from over-head to forward-down."""
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                swing_angle = -math.pi * 0.15 - t * math.pi * 0.55
                arm_length = 22
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                t_eased = 1 - (1 - t) ** 2
                swing_angle = -math.pi * 0.7 + t_eased * math.pi * 1.0
                arm_length = 22 + int(t_eased * 6)
            else:
                t = (attack_progress - 0.6) / 0.4
                swing_angle = math.pi * 0.3 - t * math.pi * 0.45
                arm_length = 28 - int(t * 6)
        else:
            swing_angle = math.sin(phase * 0.7) * 0.15
            arm_length = 22
        shoulder_x = cx + facing * 12
        shoulder_y = cy - 2
        hand_x = shoulder_x + int(math.cos(swing_angle) * arm_length) * facing
        hand_y = shoulder_y + int(math.sin(swing_angle) * arm_length)
        _NS_grimkor._aaline(surface, _NS_grimkor.PALETTE["shadow_deep"], (shoulder_x + 1, shoulder_y + 1), (hand_x + 1, hand_y + 1), 6)
        _NS_grimkor._aaline(surface, _NS_grimkor.PALETTE["iron_darkest"], (shoulder_x, shoulder_y), (hand_x, hand_y), 6)
        _NS_grimkor._aaline(surface, _NS_grimkor.PALETTE["iron_dark"], (shoulder_x, shoulder_y), (hand_x, hand_y), 4)
        _NS_grimkor._aaline(surface, _NS_grimkor.PALETTE["iron_mid"], (shoulder_x, shoulder_y - 1), (hand_x, hand_y - 1), 2)
        mid_x = (shoulder_x + hand_x) // 2
        mid_y = (shoulder_y + hand_y) // 2
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["copper_dark"], (mid_x, mid_y), 2)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["copper_light"], (mid_x, mid_y), 1)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["iron_darkest"], (shoulder_x, shoulder_y), 4)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["iron_dark"], (shoulder_x, shoulder_y), 3)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["copper_dark"], (shoulder_x, shoulder_y), 2)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["copper_light"], (shoulder_x - 1, shoulder_y - 1), 1)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["iron_darkest"], (hand_x, hand_y), 3)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["iron_mid"], (hand_x, hand_y), 2)
        saw_x = hand_x + int(math.cos(swing_angle) * 8) * facing
        saw_y = hand_y + int(math.sin(swing_angle) * 8)
        _NS_grimkor._draw_saw_blade(surface, saw_x, saw_y, phase * 2, size=9, spinning=True)
    def _draw_saw_blade(surface, cx, cy, phase, size=8, spinning=True):
        rotation = phase * 3 if spinning else 0
        if spinning:
            for r in range(size + 4, size, -1):
                alpha = _NS_grimkor._alpha(50 * (size + 4 - r) / 4)
                _NS_grimkor._aacircle(surface, (*_NS_grimkor.PALETTE["blade_light"], alpha), (cx, cy), r)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["shadow_deep"], (cx + 1, cy + 1), size)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["blade_darkest"], (cx, cy), size)
        num_teeth = 12
        for i in range(num_teeth):
            angle = rotation + i * math.pi * 2 / num_teeth
            tip_x = cx + int(math.cos(angle) * (size + 2))
            tip_y = cy + int(math.sin(angle) * (size + 2))
            base1_angle = angle - math.pi / num_teeth
            base2_angle = angle + math.pi / num_teeth
            b1x = cx + int(math.cos(base1_angle) * size)
            b1y = cy + int(math.sin(base1_angle) * size)
            b2x = cx + int(math.cos(base2_angle) * size)
            b2y = cy + int(math.sin(base2_angle) * size)
            _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["blade_dark"], [(tip_x, tip_y), (b1x, b1y), (b2x, b2y)])
            pygame.draw.line(surface, _NS_grimkor.PALETTE["blade_light"], (tip_x, tip_y), (int((b1x + b2x) / 2), int((b1y + b2y) / 2)), 1)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["blade_dark"], (cx, cy), size - 1)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["blade_mid"], (cx, cy), size - 3)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["blade_light"], (cx - 1, cy - 1), size - 5)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["copper_dark"], (cx, cy), 2)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["copper_light"], (cx, cy), 1)
        pygame.draw.rect(surface, _NS_grimkor.PALETTE["copper_shine"], (cx, cy, 1, 1))
        if spinning:
            spark_angle = phase * 5
            spx = cx + int(math.cos(spark_angle) * (size - 2))
            spy = cy + int(math.sin(spark_angle) * (size - 2))
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["blade_shine"], (spx, spy, 1, 1))
    # ================= SWING FX (FIRE TRAIL) =================
    def _draw_saw_swing(surface, boss, x, y, progress):
        """Dramatic fire trail — uses SRCALPHA surface so alpha works!"""
        if progress < 0.30 or progress > 0.80:
            return
        facing = boss.direction
        if progress < 0.6:
            swing_t = (progress - 0.30) / 0.30
        else:
            swing_t = 1.0 - (progress - 0.6) / 0.20
        swing_t = max(0.0, min(1.0, swing_t))
        alpha_base = _NS_grimkor._alpha(255 * swing_t)
        if alpha_base <= 5:
            return
        cx_sh = x + facing * 12
        cy_sh = y - 2
        if progress < 0.35:
            current_angle = -math.pi * 0.7
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            t_eased = 1 - (1 - t) ** 2
            current_angle = -math.pi * 0.7 + t_eased * math.pi * 1.0
        else:
            current_angle = math.pi * 0.3
        start_angle = -math.pi * 0.7
        arc_length = 32
        # === SRCALPHA surface for real alpha ===
        FX_W, FX_H = 220, 220
        fx_surf = pygame.Surface((FX_W, FX_H), pygame.SRCALPHA)
        ox, oy = FX_W // 2, FX_H // 2
        def to_fx(wx, wy):
            return (wx - cx_sh + ox, wy - cy_sh + oy)
        # === ARC TRAIL layered ===
        for thickness, alpha_mult, color, radius_off in [
            (9, 0.35, _NS_grimkor.PALETTE["fire_dark"],   3),
            (7, 0.55, _NS_grimkor.PALETTE["fire_mid"],    1),
            (5, 0.80, _NS_grimkor.PALETTE["fire_light"],  0),
            (3, 1.00, _NS_grimkor.PALETTE["fire_hot"],    0),
            (1, 1.00, _NS_grimkor.PALETTE["fire_shine"],  0),
        ]:
            steps = 24
            prev = None
            for s in range(steps + 1):
                seg_t = s / steps
                seg_alpha = _NS_grimkor._alpha(alpha_base * alpha_mult * (0.25 + 0.75 * seg_t))
                if seg_alpha <= 0:
                    prev = None
                    continue
                a = start_angle + (current_angle - start_angle) * seg_t
                r = arc_length + radius_off
                wx = cx_sh + int(math.cos(a) * r) * facing
                wy = cy_sh + int(math.sin(a) * r)
                p = to_fx(wx, wy)
                if prev is not None:
                    pygame.draw.line(fx_surf, (*color, seg_alpha), prev, p, thickness)
                prev = p
        # === LEADING EDGE FLASH ===
        lead_wx = cx_sh + int(math.cos(current_angle) * (arc_length + 4)) * facing
        lead_wy = cy_sh + int(math.sin(current_angle) * (arc_length + 4))
        lfx, lfy = to_fx(lead_wx, lead_wy)
        for r in range(12, 0, -1):
            a = _NS_grimkor._alpha(alpha_base * (12 - r) / 12 * 1.3)
            if a > 0:
                pygame.draw.circle(fx_surf, (*_NS_grimkor.PALETTE["fire_hot"], a), (lfx, lfy), r)
        pygame.draw.circle(fx_surf, (*_NS_grimkor.PALETTE["fire_shine"], alpha_base), (lfx, lfy), 3)
        pygame.draw.circle(fx_surf, (*_NS_grimkor.PALETTE["white"], alpha_base), (lfx, lfy), 1)
        # === SLASH LINES ===
        for slash_i in range(3):
            slash_offset = (slash_i - 1) * 0.10
            slash_a = current_angle + slash_offset
            slash_alpha = _NS_grimkor._alpha(alpha_base * (1 - abs(slash_offset) * 4))
            if slash_alpha <= 0:
                continue
            inner_r = arc_length - 10
            outer_r = arc_length + 12
            wx1 = cx_sh + int(math.cos(slash_a) * inner_r) * facing
            wy1 = cy_sh + int(math.sin(slash_a) * inner_r)
            wx2 = cx_sh + int(math.cos(slash_a) * outer_r) * facing
            wy2 = cy_sh + int(math.sin(slash_a) * outer_r)
            p1 = to_fx(wx1, wy1)
            p2 = to_fx(wx2, wy2)
            pygame.draw.line(fx_surf, (*_NS_grimkor.PALETTE["fire_shine"], slash_alpha), p1, p2, 4 - slash_i)
            pygame.draw.line(fx_surf, (*_NS_grimkor.PALETTE["white"], slash_alpha), p1, p2, 1)
        # === SPARKS ===
        for i in range(14):
            spark_seed = i * 0.7 + progress * 4
            spark_a = current_angle + math.sin(spark_seed) * 0.5
            spark_r = arc_length + 6 + (i % 4) * 5 + int(swing_t * 10)
            wspx = cx_sh + int(math.cos(spark_a) * spark_r) * facing
            wspy = cy_sh + int(math.sin(spark_a) * spark_r)
            spx, spy = to_fx(wspx, wspy)
            spark_alpha = _NS_grimkor._alpha(alpha_base * (0.7 + (i % 3) * 0.1))
            tail_wx = wspx - int(math.cos(spark_a) * 4) * facing
            tail_wy = wspy - int(math.sin(spark_a) * 4)
            tfx, tfy = to_fx(tail_wx, tail_wy)
            pygame.draw.line(fx_surf, (*_NS_grimkor.PALETTE["fire_mid"], spark_alpha), (tfx, tfy), (spx, spy), 2)
            pygame.draw.rect(fx_surf, (*_NS_grimkor.PALETTE["fire_hot"], spark_alpha), (spx, spy, 2, 2))
            pygame.draw.rect(fx_surf, (*_NS_grimkor.PALETTE["fire_shine"], spark_alpha), (spx, spy, 1, 1))
        # === IMPACT BURST ===
        if 0.55 < progress < 0.72:
            impact_t = (progress - 0.55) / 0.17
            impact_alpha = _NS_grimkor._alpha(240 * (1 - impact_t))
            if impact_alpha > 0:
                impact_wx = cx_sh + int(math.cos(math.pi * 0.2) * (arc_length + 8)) * facing
                impact_wy = cy_sh + int(math.sin(math.pi * 0.2) * (arc_length + 8))
                ifx, ify = to_fx(impact_wx, impact_wy)
                for burst_r in range(int(6 + impact_t * 16), 0, -2):
                    a = _NS_grimkor._alpha(impact_alpha * (18 - burst_r) / 18)
                    if a > 0:
                        pygame.draw.circle(fx_surf, (*_NS_grimkor.PALETTE["fire_light"], a), (ifx, ify), burst_r)
                for i in range(8):
                    a_burst = i * math.pi / 4
                    bx = ifx + int(math.cos(a_burst) * (8 + impact_t * 12))
                    by = ify + int(math.sin(a_burst) * (8 + impact_t * 12))
                    pygame.draw.line(fx_surf, (*_NS_grimkor.PALETTE["fire_hot"], impact_alpha), (ifx, ify), (bx, by), 2)
                    pygame.draw.rect(fx_surf, (*_NS_grimkor.PALETTE["fire_shine"], impact_alpha), (bx, by, 1, 1))
        surface.blit(fx_surf, (cx_sh - ox, cy_sh - oy))
    # ================= AMBIENT / GROUND =================
    def _draw_shadow(surface, x, y, moving=False):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 15 - radius, 120 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 5, 2, 170), (5, 8, 130, 14))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_fire_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(80, 5, -5):
            alpha = _NS_grimkor._alpha((80 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_grimkor._aacircle(aura, (*_NS_grimkor.PALETTE["fire_dark"], alpha), (110, 90), radius)
        for radius in range(45, 5, -3):
            alpha = _NS_grimkor._alpha((45 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_grimkor._aacircle(aura, (*_NS_grimkor.PALETTE["fire_mid"], alpha), (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            radius = 35 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            sy -= int((phase * 8 + i * 5) % 20)
            color = _NS_grimkor.PALETTE["fire_mid"] if i % 2 == 0 else _NS_grimkor.PALETTE["fire_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["fire_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_grimkor.PALETTE["iron_dark"], 200), (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_grimkor.PALETTE["fire_dark"], 220), (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_grimkor.PALETTE["fire_mid"], 180), (25, 22, 120, 18), 1)
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 85 + int(math.cos(angle) * 66)
            y1 = 30 + int(math.sin(angle) * 10)
            pygame.draw.rect(ring, _NS_grimkor.PALETTE["copper_light"], (x1, y1, 2, 2))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_grimkor.PALETTE["fire_hot"], _NS_grimkor._alpha(150 * pulse)), (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    def _draw_steam_exhaust(surface, cx, cy, phase, facing, intense=False):
        strength = 1.5 if intense else 1.0
        for stack_off in (-11, -6, 6, 11):
            sx = cx + stack_off
            sy = cy
            for i in range(5):
                t = (phase * 0.5 + i * 0.2 + stack_off * 0.05) % 1.0
                puff_x = sx + int(math.sin(phase + i + stack_off) * 3)
                puff_y = sy - int(t * 25)
                puff_r = int(2 + t * 4)
                alpha = _NS_grimkor._alpha(200 * (1 - t) * strength)
                if alpha > 0:
                    _NS_grimkor._aacircle(surface, (*_NS_grimkor.PALETTE["smoke_dark"], alpha), (puff_x, puff_y), puff_r)
                    _NS_grimkor._aacircle(surface, (*_NS_grimkor.PALETTE["smoke_mid"], alpha), (puff_x - 1, puff_y - 1), max(1, puff_r - 1))
                    _NS_grimkor._aacircle(surface, (*_NS_grimkor.PALETTE["smoke_light"], alpha), (puff_x - 1, puff_y - 2), max(1, puff_r - 2))
            if intense:
                for i in range(3):
                    ember_t = (phase * 0.8 + i * 0.3) % 1.0
                    ex = sx + int(math.sin(phase * 2 + i) * 2)
                    ey = sy - int(ember_t * 15)
                    alpha = _NS_grimkor._alpha(230 * (1 - ember_t))
                    pygame.draw.rect(surface, (*_NS_grimkor.PALETTE["fire_mid"], alpha), (ex, ey, 2, 2))
                    pygame.draw.rect(surface, (*_NS_grimkor.PALETTE["fire_hot"], alpha), (ex, ey, 1, 1))
    # ================= SKILL Q — WHIRLING DEATH =================
    def _draw_whirling_death(surface, boss, x, y, timer, phase):
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        intensity = math.sin(progress * math.pi)
        num_saws = 4
        spin_rate = phase * 4
        for ring_i in range(3):
            ring_r = 40 + ring_i * 6
            alpha = _NS_grimkor._alpha(120 * intensity * (1 - ring_i * 0.25))
            _NS_grimkor._aacircle(surface, (*_NS_grimkor.PALETTE["blade_mid"], alpha), (x, y), ring_r, 1)
        for i in range(num_saws):
            angle = spin_rate + i * math.pi * 2 / num_saws
            orbit_r = 42
            sx = x + int(math.cos(angle) * orbit_r)
            sy = y + int(math.sin(angle) * orbit_r * 0.6)
            for trail_i in range(5):
                trail_a = angle - trail_i * 0.15
                tx = x + int(math.cos(trail_a) * orbit_r)
                ty = y + int(math.sin(trail_a) * orbit_r * 0.6)
                trail_alpha = _NS_grimkor._alpha(180 * intensity * (1 - trail_i * 0.2))
                _NS_grimkor._aacircle(surface, (*_NS_grimkor.PALETTE["blade_light"], trail_alpha), (tx, ty), max(1, 4 - trail_i))
            _NS_grimkor._draw_saw_blade(surface, sx, sy, phase * 2, size=7, spinning=True)
            for s in range(3):
                spark_a = angle + s * 0.3
                spark_r = orbit_r + 6 + s * 2
                spx = x + int(math.cos(spark_a) * spark_r)
                spy = y + int(math.sin(spark_a) * spark_r * 0.6)
                pygame.draw.rect(surface, (*_NS_grimkor.PALETTE["fire_hot"], _NS_grimkor._alpha(200 * intensity)), (spx, spy, 2, 2))
                pygame.draw.rect(surface, _NS_grimkor.PALETTE["fire_shine"], (spx, spy, 1, 1))
    # ================= SKILL W — CHAINSAW DASH =================
    def _draw_chainsaw_ground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            length = int(progress / 0.3 * 100)
            alpha = _NS_grimkor._alpha(200)
            for i in range(3):
                pygame.draw.line(surface, (*_NS_grimkor.PALETTE["fire_dark"], alpha - i * 50), (x, y + 40), (x + facing * length, y + 40), 3 - i)
        else:
            t = (progress - 0.3) / 0.7
            trail_len = int(120 * (1 - t))
            for i in range(6):
                offset = i * 20
                alpha = _NS_grimkor._alpha(200 * (1 - i / 6) * (1 - t))
                if offset < trail_len:
                    tx = x - facing * offset
                    pygame.draw.line(surface, (*_NS_grimkor.PALETTE["fire_mid"], alpha), (tx, y + 38), (tx, y + 44), 3)
                    pygame.draw.line(surface, (*_NS_grimkor.PALETTE["fire_hot"], alpha), (tx, y + 40), (tx, y + 42), 1)
    def _draw_chainsaw_foreground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        base_x = x + facing * 18
        base_y = y - 2
        saw_len = int(35 + math.sin(phase * 8) * 3)
        tip_x = base_x + facing * saw_len
        tip_y = base_y
        _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["shadow_deep"], [
            (base_x + 1, base_y - 4 + 1), (tip_x + 1, tip_y - 3 + 1),
            (tip_x + facing * 3, tip_y + 1), (tip_x + 1, tip_y + 3 + 1),
            (base_x + 1, base_y + 4 + 1),
        ])
        _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["iron_darkest"], [
            (base_x, base_y - 4), (tip_x, tip_y - 3),
            (tip_x + facing * 3, tip_y), (tip_x, tip_y + 3),
            (base_x, base_y + 4),
        ])
        _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["iron_dark"], [
            (base_x, base_y - 3), (tip_x, tip_y - 2),
            (tip_x + facing * 2, tip_y), (tip_x, tip_y + 2),
            (base_x, base_y + 3),
        ])
        _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["iron_mid"], [
            (base_x, base_y - 2), (tip_x, tip_y - 1), (base_x, base_y + 2),
        ])
        chain_offset = int(phase * 20) % 6
        for i in range(-1, int(saw_len / 4) + 1):
            teeth_x = base_x + facing * (i * 4 + chain_offset)
            if abs(teeth_x - base_x) > saw_len:
                continue
            _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["blade_dark"], [
                (teeth_x - 1, base_y - 5), (teeth_x + 1, base_y - 5), (teeth_x, base_y - 6),
            ])
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["blade_light"], (teeth_x, base_y - 6, 1, 1))
            _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["blade_dark"], [
                (teeth_x - 1, base_y + 5), (teeth_x + 1, base_y + 5), (teeth_x, base_y + 6),
            ])
        for i in range(8):
            angle = i * math.pi / 4 + phase * 2
            sp_r = 8 + (i % 3) * 3
            spx = tip_x + int(math.cos(angle) * sp_r) * facing
            spy = tip_y + int(math.sin(angle) * sp_r)
            alpha = _NS_grimkor._alpha(230)
            color = _NS_grimkor.PALETTE["wood_mid"] if i % 2 == 0 else _NS_grimkor.PALETTE["fire_hot"]
            pygame.draw.rect(surface, (*color, alpha), (spx, spy, 2, 2))
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["fire_shine"], (spx, spy, 1, 1))
        for r in range(6, 0, -1):
            alpha = _NS_grimkor._alpha(180 * (6 - r) / 6)
            _NS_grimkor._aacircle(surface, (*_NS_grimkor.PALETTE["fire_dark"], alpha), (base_x - facing * 6, base_y), r)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["fire_mid"], (base_x - facing * 6, base_y), 3)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["fire_hot"], (base_x - facing * 6, base_y), 2)
    # ================= SKILL E — TIMBER CHAIN =================
    def _draw_timber_chain(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_grimkor._target_position(boss, x, y)
        start_x = x + facing * 22
        start_y = y
        if progress < 0.4:
            t = progress / 0.4
            end_x = int(start_x + (tx - start_x) * t)
            end_y = int(start_y + (ty - start_y) * t)
        elif progress < 0.7:
            end_x = tx
            end_y = ty
        else:
            t = (progress - 0.7) / 0.3
            end_x = int(tx + (start_x - tx) * t)
            end_y = int(ty + (start_y - ty) * t)
        segments = 12
        for i in range(segments):
            t1 = i / segments
            t2 = (i + 1) / segments
            wave = math.sin(phase * 3 + i * 0.5) * 2
            px1 = int(start_x + (end_x - start_x) * t1)
            py1 = int(start_y + (end_y - start_y) * t1 + wave)
            px2 = int(start_x + (end_x - start_x) * t2)
            py2 = int(start_y + (end_y - start_y) * t2 + math.sin(phase * 3 + (i + 1) * 0.5) * 2)
            mx = (px1 + px2) // 2
            my = (py1 + py2) // 2
            if i % 2 == 0:
                _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["chain_dark"], (mx, my), 3)
                _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["chain_mid"], (mx, my), 2)
                pygame.draw.rect(surface, _NS_grimkor.PALETTE["chain_light"], (mx, my, 1, 1))
            else:
                _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["chain_dark"], (mx, my), 2)
                _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["chain_mid"], (mx, my), 1)
        claw_dx = end_x - start_x
        claw_dy = end_y - start_y
        claw_angle = math.atan2(claw_dy, claw_dx)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["shadow_deep"], (end_x + 1, end_y + 1), 5)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["iron_darkest"], (end_x, end_y), 5)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["iron_dark"], (end_x, end_y), 4)
        _NS_grimkor._aacircle(surface, _NS_grimkor.PALETTE["iron_mid"], (end_x - 1, end_y - 1), 2)
        for i in range(-1, 2):
            prong_angle = claw_angle + i * math.pi / 4
            px = end_x + int(math.cos(prong_angle) * 8)
            py = end_y + int(math.sin(prong_angle) * 8)
            base_a = end_x + int(math.cos(prong_angle + math.pi / 2) * 2)
            base_b = end_y + int(math.sin(prong_angle + math.pi / 2) * 2)
            base_c = end_x - int(math.cos(prong_angle + math.pi / 2) * 2)
            base_d = end_y - int(math.sin(prong_angle + math.pi / 2) * 2)
            _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["iron_darkest"], [(px, py), (base_a, base_b), (base_c, base_d)])
            _NS_grimkor._poly(surface, _NS_grimkor.PALETTE["iron_mid"], [(px, py), (int((px + base_a) / 2), int((py + base_b) / 2)), (end_x, end_y)])
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["iron_shine"], (px, py, 1, 1))
        if 0.4 < progress < 0.7:
            splash_t = (progress - 0.4) / 0.3
            for r in range(int(10 * (1 - splash_t)), 0, -2):
                alpha = _NS_grimkor._alpha(200 * (1 - splash_t))
                _NS_grimkor._aacircle(surface, (*_NS_grimkor.PALETTE["wood_mid"], alpha), (end_x, end_y), r, 1)
            for i in range(6):
                chip_a = i * math.pi / 3
                chip_r = int(8 + splash_t * 12)
                cx_chip = end_x + int(math.cos(chip_a) * chip_r)
                cy_chip = end_y + int(math.sin(chip_a) * chip_r)
                alpha = _NS_grimkor._alpha(230 * (1 - splash_t))
                pygame.draw.rect(surface, (*_NS_grimkor.PALETTE["wood_mid"], alpha), (cx_chip, cy_chip, 2, 2))
                pygame.draw.rect(surface, (*_NS_grimkor.PALETTE["wood_light"], alpha), (cx_chip, cy_chip, 1, 1))
    # ================= SKILL R — REACTIVE ARMOR =================
    def _draw_reactive_ground(surface, boss, x, y, timer, phase):
        for i in range(2):
            r = int(35 + i * 8 + math.sin(phase * 2) * 3)
            alpha = _NS_grimkor._alpha(200 - i * 60)
            _NS_grimkor._aacircle(surface, (*_NS_grimkor.PALETTE["fire_mid"], alpha), (x, y + 40), r, 2)
            _NS_grimkor._aacircle(surface, (*_NS_grimkor.PALETTE["fire_hot"], alpha), (x, y + 40), r, 1)
    def _draw_reactive_bubble(surface, boss, x, y, timer, phase):
        breath = math.sin(phase * 2) * 3
        r = 55 + int(breath)
        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)
        for i, (thickness, alpha_val) in enumerate([(3, 120), (2, 160), (1, 200)]):
            _NS_grimkor._aacircle(bubble, (*_NS_grimkor.PALETTE["fire_dark"], alpha_val), center, r - i, thickness)
            _NS_grimkor._aacircle(bubble, (*_NS_grimkor.PALETTE["fire_mid"], alpha_val), center, r - i - 1, 1)
        num_plates = 8
        for i in range(num_plates):
            angle = phase * 1.5 + i * math.pi * 2 / num_plates
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            _NS_grimkor._aacircle(bubble, _NS_grimkor.PALETTE["iron_darkest"], (sx, sy), 4)
            _NS_grimkor._aacircle(bubble, _NS_grimkor.PALETTE["iron_dark"], (sx, sy), 3)
            _NS_grimkor._aacircle(bubble, _NS_grimkor.PALETTE["iron_mid"], (sx - 1, sy - 1), 2)
            _NS_grimkor._aacircle(bubble, _NS_grimkor.PALETTE["copper_dark"], (sx, sy), 1)
            pygame.draw.rect(bubble, _NS_grimkor.PALETTE["copper_light"], (sx, sy, 1, 1))
        for i in range(12):
            angle = phase * 0.5 + i * math.pi / 6
            inner_r = r - 8
            bx = center[0] + int(math.cos(angle) * inner_r)
            by = center[1] + int(math.sin(angle) * inner_r)
            alpha = _NS_grimkor._alpha(180 + math.sin(phase * 3 + i) * 40)
            pygame.draw.rect(bubble, (*_NS_grimkor.PALETTE["fire_hot"], alpha), (bx, by, 2, 2))
            pygame.draw.rect(bubble, _NS_grimkor.PALETTE["fire_shine"], (bx, by, 1, 1))
        surface.blit(bubble, (x - r - 10, y - r - 10))
        for i in range(6):
            angle = phase * 0.8 + i * math.pi / 3
            end_x = x + int(math.cos(angle) * (r + 10))
            end_y = y + int(math.sin(angle) * (r + 10))
            alpha = _NS_grimkor._alpha(180 + math.sin(phase * 3 + i) * 40)
            pygame.draw.line(surface, (*_NS_grimkor.PALETTE["fire_light"], alpha),
                             (x + int(math.cos(angle) * r), y + int(math.sin(angle) * r)),
                             (end_x, end_y), 2)
            pygame.draw.rect(surface, _NS_grimkor.PALETTE["fire_shine"], (end_x, end_y, 1, 1))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_emberwick(surface, boss, x, y):
    """Entry point emberwick."""
    return _NS_emberwick.draw_emberwick(surface, boss, x, y)


def draw_grondarthul(surface, boss, x, y):
    """Entry point grondarthul."""
    return _NS_grondarthul.draw_grondarthul(surface, boss, x, y)


def draw_xareth(surface, boss, x, y):
    """Entry point xareth."""
    return _NS_xareth.draw_xareth(surface, boss, x, y)


def draw_grimkor(surface, boss, x, y):
    """Entry point grimkor."""
    return _NS_grimkor.draw_grimkor(surface, boss, x, y)
