"""
bosses/level33.py - Semua boss Level 33

Berisi:
  - rakzhan    (mini boss - MELEE emberfist prodigy, fire fists)
  - sirakzan   (mini boss - MELEE blade rolling duelist)
  - valekris   (mini boss - RANGED vengeful wraith, cyan spectre)
  - zharakzuul (TRUE BOSS - RANGED voidbound sovereign, void mage)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _rz_ (rakzhan), _sk_ (sirakzan), _zk_ (zharakzuul) sudah unik.
  - _vk_ (valekris) di-rename -> _vlk_ (bentrok dengan vulkareth
    level 25), termasuk atribut _last_x/_last_y.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# RAKZHAN (EMBERFIST PRODIGY) - Mini Boss
# ====================================================================

class _NS_rakzhan:
    """Namespace rakzhan - fire martial artist mini boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Tan skin
        "skin_darkest": (60, 30, 20),
        "skin_dark": (130, 75, 50),
        "skin_mid": (195, 135, 95),
        "skin_light": (235, 185, 145),
        "skin_shine": (255, 220, 185),
        # Red-orange hair
        "hair_darkest": (55, 15, 5),
        "hair_dark": (130, 40, 15),
        "hair_mid": (215, 80, 25),
        "hair_light": (255, 145, 55),
        "hair_shine": (255, 210, 130),
        # Black clothes (pants, top)
        "cloth_darkest": (5, 5, 8),
        "cloth_dark": (20, 15, 20),
        "cloth_mid": (45, 35, 40),
        "cloth_light": (85, 70, 75),
        # Gold armor (crown, belt, bracers)
        "gold_darkest": (55, 30, 8),
        "gold_dark": (105, 70, 20),
        "gold_mid": (195, 145, 45),
        "gold_light": (245, 205, 95),
        "gold_shine": (255, 240, 175),
        # Red cloth accents (sash, ribbons)
        "sash_dark": (85, 20, 15),
        "sash_mid": (185, 45, 35),
        "sash_light": (235, 90, 70),
        # Fire (fists, aura, projectiles)
        "fire_darkest": (35, 8, 3),
        "fire_dark": (125, 30, 8),
        "fire_mid": (225, 85, 20),
        "fire_light": (255, 160, 50),
        "fire_hot": (255, 220, 130),
        "fire_shine": (255, 250, 210),
        # Deep red eyes
        "eye_socket": (10, 3, 3),
        "eye_dark": (90, 15, 15),
        "eye_mid": (215, 40, 40),
        "eye_light": (255, 130, 100),
        "eye_glow": (255, 220, 180),
        # Tribal tattoo (glowing orange)
        "tattoo_dark": (155, 55, 15),
        "tattoo_mid": (240, 130, 30),
        "tattoo_shine": (255, 210, 100),
        # Gem red
        "gem_dark": (85, 10, 15),
        "gem_mid": (215, 35, 40),
        "gem_light": (255, 120, 100),
        "gem_shine": (255, 230, 200),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_rakzhan._clamp(color)
        if _NS_rakzhan.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_rakzhan._clamp(color)
        if _NS_rakzhan.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_rakzhan._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 200 * getattr(boss, "direction", 1)), int(y)
    def _arm_elbow(shoulder, hand, bend=4, bend_up=False):
        """Calculate elbow position with natural bend."""
        sx, sy = shoulder
        hx, hy = hand
        mid_x = (sx + hx) / 2
        mid_y = (sy + hy) / 2
        dx = hx - sx
        dy = hy - sy
        length = max(1.0, math.sqrt(dx * dx + dy * dy))
        perp_x = -dy / length
        perp_y = dx / length
        if bend_up:
            if perp_y > 0:
                perp_x = -perp_x
                perp_y = -perp_y
        else:
            if perp_y < 0:
                perp_x = -perp_x
                perp_y = -perp_y
        return (int(mid_x + perp_x * bend), int(mid_y + perp_y * bend))
    def _fist_position(boss, x, y):
        """Position of front fist (source of projectiles/shockwaves)."""
        facing = boss.direction
        # Front hand position roughly.
        active = getattr(boss, "_rz_attack_active", False)
        progress = getattr(boss, "_rz_attack_progress", 0.0)
        if active:
            # During punch: fist extends forward.
            if progress < 0.35:
                # Wind back.
                t = progress / 0.35
                fx = x + facing * int(6 - t * 4)
                fy = y - 4
            elif progress < 0.55:
                # Punch forward.
                t = (progress - 0.35) / 0.2
                fx = x + facing * int(2 + t * 26)
                fy = y - 4
            elif progress < 0.75:
                # Hold extended.
                fx = x + facing * 28
                fy = y - 4
            else:
                # Return.
                t = (progress - 0.75) / 0.25
                fx = x + facing * int(28 - t * 22)
                fy = y - 4
        else:
            fx = x + facing * 14
            fy = y - 6
        return fx, fy
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_rakzhan(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_rakzhan._update_attack_anim(boss)
        attack_progress = getattr(boss, "_rz_attack_progress", 0.0)
        attacking = (
            getattr(boss, "_rz_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )
        # Ambient FX behind body.
        _NS_rakzhan._draw_fire_aura(surface, x, y, pulse)
        _NS_rakzhan._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX.
        if active_skill == "q":
            _NS_rakzhan._draw_transcendent_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_rakzhan._draw_myturn_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_rakzhan._draw_letmeshow_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating body (martial artist floating stance).
        float_bob = math.sin(pulse * 0.7) * 4
        body_y = y + int(float_bob)
        # Body pose.
        if attacking:
            _NS_rakzhan._draw_body_attack(surface, boss, x, body_y)
        elif active_skill == "q":
            # Q = dash pose.
            _NS_rakzhan._draw_body_dash(surface, boss, x, body_y,
                                         skill_timer, pulse)
        elif active_skill == "w":
            # W = combo pose.
            _NS_rakzhan._draw_body_combo(surface, boss, x, body_y,
                                          skill_timer, pulse)
        elif active_skill == "r":
            # R = burst punch pose.
            _NS_rakzhan._draw_body_burst(surface, boss, x, body_y,
                                          skill_timer, pulse)
        else:
            _NS_rakzhan._draw_body_idle(surface, boss, x, body_y)
        # Foreground FX.
        if active_skill == "q":
            _NS_rakzhan._draw_transcendent_dash_fx(surface, boss, x, body_y,
                                                    skill_timer, pulse)
        elif active_skill == "w":
            _NS_rakzhan._draw_soulcombo_fx(surface, boss, x, body_y,
                                            skill_timer, pulse)
        elif active_skill == "e":
            _NS_rakzhan._draw_myturn_dome(surface, boss, x, body_y,
                                           skill_timer, pulse)
        elif active_skill == "r":
            _NS_rakzhan._draw_letmeshow_shockwave(surface, boss, x, body_y,
                                                    skill_timer, pulse)
        else:
            if attacking and attack_progress > 0:
                _NS_rakzhan._draw_basic_punch_fx(surface, boss, x, body_y)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_rz_attack_active", False))
        if not active and timer >= cooldown - 2:
            boss._rz_attack_active = True
            boss._rz_attack_frame = 0
            active = True
        elif active:
            boss._rz_attack_frame = int(getattr(boss, "_rz_attack_frame", 0)) + 1
            if boss._rz_attack_frame >= cooldown:
                boss._rz_attack_active = False
                boss._rz_attack_frame = 0
                active = False
        boss._rz_previous_timer = timer
        boss._rz_attack_progress = (
            min(1.0, getattr(boss, "_rz_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # BODY POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, cx, cy):
        _NS_rakzhan._draw_float_shadow(surface, cx, cy + 50, boss.pulse)
        _NS_rakzhan._draw_floor_flames(surface, cx, cy + 40, boss.pulse)
        _NS_rakzhan._draw_body(surface, boss, cx, cy, "idle", 0)
    def _draw_body_attack(surface, boss, cx, cy):
        progress = getattr(boss, "_rz_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        _NS_rakzhan._draw_float_shadow(surface, cx, cy + 50, boss.pulse)
        _NS_rakzhan._draw_floor_flames(surface, cx, cy + 40, boss.pulse, intense=True)
        _NS_rakzhan._draw_body(surface, boss, cx, cy, "punch", progress)
    def _draw_body_dash(surface, boss, cx, cy, timer, phase):
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_rakzhan._draw_float_shadow(surface, cx, cy + 50, phase)
        _NS_rakzhan._draw_floor_flames(surface, cx, cy + 40, phase, intense=True)
        _NS_rakzhan._draw_body(surface, boss, cx, cy, "dash", progress)
    def _draw_body_combo(surface, boss, cx, cy, timer, phase):
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_rakzhan._draw_float_shadow(surface, cx, cy + 50, phase)
        _NS_rakzhan._draw_floor_flames(surface, cx, cy + 40, phase, intense=True)
        _NS_rakzhan._draw_body(surface, boss, cx, cy, "combo", progress)
    def _draw_body_burst(surface, boss, cx, cy, timer, phase):
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_rakzhan._draw_float_shadow(surface, cx, cy + 50, phase)
        _NS_rakzhan._draw_floor_flames(surface, cx, cy + 40, phase, intense=True)
        _NS_rakzhan._draw_body(surface, boss, cx, cy, "burst", progress)
    # ============================================================
    # MAIN BODY
    # ============================================================
    def _draw_body(surface, boss, cx, cy, action, progress):
        facing = boss.direction
        phase = boss.pulse
        # Red sash flowing behind.
        _NS_rakzhan._draw_sash(surface, cx, cy, facing, phase)
        # Legs (in stance).
        _NS_rakzhan._draw_legs(surface, cx, cy, facing, phase, action, progress)
        # Torso.
        _NS_rakzhan._draw_torso(surface, cx, cy, facing, phase)
        # Arms with flaming fists.
        _NS_rakzhan._draw_arms(surface, cx, cy, facing, phase, action, progress)
        # Head.
        _NS_rakzhan._draw_head(surface, cx, cy - 20, facing, phase, action)
    def _draw_sash(surface, cx, cy, facing, phase):
        """Red flowing sash behind body."""
        sway = math.sin(phase * 0.6) * 3
        # Left flowing ribbon.
        pts = [
            (cx - facing * 6, cy + 4),
            (cx - facing * 12 + int(sway), cy + 12),
            (cx - facing * 14 + int(sway * 1.2), cy + 22),
            (cx - facing * 11 + int(sway), cy + 30),
            (cx - facing * 8, cy + 32),
            (cx - facing * 4, cy + 20),
            (cx - facing * 2, cy + 8),
        ]
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in pts])
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["sash_dark"], pts)
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["sash_mid"], [
            (cx - facing * 5, cy + 5),
            (cx - facing * 10 + int(sway), cy + 12),
            (cx - facing * 12 + int(sway * 1.2), cy + 20),
            (cx - facing * 9 + int(sway), cy + 28),
            (cx - facing * 6, cy + 28),
            (cx - facing * 3, cy + 18),
        ])
        # Highlight edge.
        pygame.draw.line(surface, _NS_rakzhan.PALETTE["sash_light"],
                         (cx - facing * 5, cy + 6),
                         (cx - facing * 10 + int(sway), cy + 12), 1)
        pygame.draw.line(surface, _NS_rakzhan.PALETTE["sash_light"],
                         (cx - facing * 12 + int(sway * 1.2), cy + 20),
                         (cx - facing * 9 + int(sway), cy + 28), 1)
    def _draw_legs(surface, cx, cy, facing, phase, action, progress):
        """Legs in martial arts stance (slightly wide)."""
        # Fighting stance: legs apart, one forward.
        for i, side in enumerate((-1, 1)):
            # Front leg slightly forward for facing side.
            forward = (side == facing)
            leg_x = cx + side * 6
            if forward:
                leg_x = cx + facing * 8
            else:
                leg_x = cx - facing * 6
            # Thigh (fitted black pants).
            thigh_pts = [
                (leg_x - 4, cy + 8),
                (leg_x + 4, cy + 8),
                (leg_x + 5, cy + 18),
                (leg_x + 3, cy + 26),
                (leg_x - 3, cy + 26),
                (leg_x - 5, cy + 18),
            ]
            _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 2) for p in thigh_pts])
            _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["cloth_darkest"], thigh_pts)
            _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["cloth_dark"], [
                (leg_x - 3, cy + 9),
                (leg_x + 3, cy + 9),
                (leg_x + 4, cy + 18),
                (leg_x + 2, cy + 25),
                (leg_x - 2, cy + 25),
                (leg_x - 4, cy + 18),
            ])
            _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["cloth_mid"], [
                (leg_x - 2, cy + 10),
                (leg_x + 2, cy + 10),
                (leg_x + 3, cy + 18),
                (leg_x + 1, cy + 22),
                (leg_x - 1, cy + 22),
                (leg_x - 3, cy + 18),
            ])
            # Highlight stripe.
            pygame.draw.line(surface, _NS_rakzhan.PALETTE["cloth_light"],
                             (leg_x - 2, cy + 12), (leg_x - 2, cy + 22), 1)
            # Gold ankle band.
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["gold_dark"],
                             (leg_x - 4, cy + 26, 8, 2))
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["gold_mid"],
                             (leg_x - 3, cy + 26, 6, 1))
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["gold_light"],
                             (leg_x - 2, cy + 26, 4, 1))
            # Foot (bare/wrapped).
            _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["shadow_deep"], [
                (leg_x - 4 + 1, cy + 28 + 1),
                (leg_x + 5 + 1, cy + 28 + 1),
                (leg_x + 6 + 1, cy + 32 + 1),
                (leg_x - 4 + 1, cy + 32 + 1),
            ])
            _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["skin_darkest"], [
                (leg_x - 4, cy + 28),
                (leg_x + 5, cy + 28),
                (leg_x + 6, cy + 32),
                (leg_x - 4, cy + 32),
            ])
            _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["skin_dark"], [
                (leg_x - 3, cy + 28),
                (leg_x + 4, cy + 28),
                (leg_x + 5, cy + 31),
                (leg_x - 3, cy + 31),
            ])
            pygame.draw.line(surface, _NS_rakzhan.PALETTE["skin_mid"],
                             (leg_x - 2, cy + 29), (leg_x + 3, cy + 29), 1)
            # Ankle wraps (white/red cloth).
            for wrap_y in (cy + 28, cy + 30):
                pygame.draw.line(surface, _NS_rakzhan.PALETTE["sash_dark"],
                                 (leg_x - 4, wrap_y),
                                 (leg_x + 5, wrap_y), 1)
    def _draw_torso(surface, cx, cy, facing, phase):
        """Muscular topless torso."""
        breath = math.sin(phase * 0.7) * 1
        # Torso shape.
        torso_pts = [
            (cx - 12, cy - 14),
            (cx - 14, cy - 6),
            (cx - 12, cy + 2),
            (cx - 8, cy + 8),
            (cx + 8, cy + 8),
            (cx + 12, cy + 2),
            (cx + 14, cy - 6),
            (cx + 12, cy - 14),
            (cx + 6, cy - 18),
            (cx - 6, cy - 18),
        ]
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in torso_pts])
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["skin_darkest"], torso_pts)
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["skin_dark"], [
            (cx - 11, cy - 13),
            (cx - 13, cy - 6),
            (cx - 11, cy + 1),
            (cx - 7, cy + 7),
            (cx + 7, cy + 7),
            (cx + 11, cy + 1),
            (cx + 13, cy - 6),
            (cx + 11, cy - 13),
            (cx + 5, cy - 17),
            (cx - 5, cy - 17),
        ])
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["skin_mid"], [
            (cx - 8, cy - 10),
            (cx - 10, cy - 4),
            (cx - 8, cy + 3),
            (cx + 8, cy + 3),
            (cx + 10, cy - 4),
            (cx + 8, cy - 10),
            (cx + 4, cy - 14),
            (cx - 4, cy - 14),
        ])
        # Pec division.
        pygame.draw.line(surface, _NS_rakzhan.PALETTE["skin_darkest"],
                         (cx, cy - 10), (cx, cy + 4), 1)
        # Pec highlight.
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["skin_light"], [
            (cx - 8, cy - 8),
            (cx - 2, cy - 8),
            (cx - 3, cy - 3),
            (cx - 8, cy - 3),
        ])
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["skin_light"], [
            (cx + 2, cy - 8),
            (cx + 8, cy - 8),
            (cx + 8, cy - 3),
            (cx + 3, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["skin_shine"], (cx - 6, cy - 6, 2, 1))
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["skin_shine"], (cx + 4, cy - 6, 2, 1))
        # Abs.
        for row in range(2):
            for side_ab in (-1, 1):
                ab_y = cy - 1 + row * 3
                pygame.draw.line(surface, _NS_rakzhan.PALETTE["skin_darkest"],
                                 (cx + side_ab * 2, ab_y),
                                 (cx + side_ab * 5, ab_y), 1)
        # Center black tunic strip (down chest).
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["cloth_darkest"], [
            (cx - 4, cy - 14),
            (cx + 4, cy - 14),
            (cx + 3, cy + 4),
            (cx - 3, cy + 4),
        ])
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["cloth_dark"], [
            (cx - 3, cy - 13),
            (cx + 3, cy - 13),
            (cx + 2, cy + 3),
            (cx - 2, cy + 3),
        ])
        # Gold accent line down center.
        pygame.draw.line(surface, _NS_rakzhan.PALETTE["gold_mid"],
                         (cx, cy - 12), (cx, cy + 2), 1)
        # Gold belt.
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["gold_darkest"],
                         (cx - 12, cy + 6, 24, 5))
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["gold_dark"],
                         (cx - 11, cy + 6, 22, 4))
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["gold_mid"],
                         (cx - 10, cy + 7, 20, 3))
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["gold_light"],
                         (cx - 9, cy + 8, 18, 1))
        # Belt central gem (red).
        _NS_rakzhan._aacircle(surface, _NS_rakzhan.PALETTE["gold_darkest"], (cx, cy + 8), 3)
        _NS_rakzhan._aacircle(surface, _NS_rakzhan.PALETTE["gem_dark"], (cx, cy + 8), 2)
        _NS_rakzhan._aacircle(surface, _NS_rakzhan.PALETTE["gem_mid"], (cx, cy + 8), 1)
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["gem_shine"], (cx, cy + 8, 1, 1))
    def _draw_arms(surface, cx, cy, facing, phase, action, progress):
        """Two arms with flaming fists. Different poses per action."""
        # Determine hand positions.
        front_sh = (cx + facing * 12, cy - 12)
        back_sh = (cx - facing * 12, cy - 12)
        # Idle: both fists ready (front slightly forward, back tucked in).
        # Punch: front punches forward, back retracted.
        # Combo (W): alternating punches.
        # Dash (Q): both fists forward.
        # Burst (R): both fists cocked back charging fire.
        front_hand_x = cx + facing * 12
        front_hand_y = cy - 4
        back_hand_x = cx - facing * 6
        back_hand_y = cy - 6
        if action == "punch":
            # Basic punch: front fist extends.
            if progress < 0.35:
                # Wind back.
                t = progress / 0.35
                front_hand_x = cx + facing * int(12 - t * 6)
                front_hand_y = cy - 4 + int(t * 2)
            elif progress < 0.55:
                # Punch forward.
                t = (progress - 0.35) / 0.2
                front_hand_x = cx + facing * int(6 + t * 22)
                front_hand_y = cy - 4
            elif progress < 0.75:
                # Hold extended.
                front_hand_x = cx + facing * 28
                front_hand_y = cy - 4
            else:
                # Return.
                t = (progress - 0.75) / 0.25
                front_hand_x = cx + facing * int(28 - t * 16)
                front_hand_y = cy - 4
            # Back hand pulled to chest.
            back_hand_x = cx - facing * 4
            back_hand_y = cy - 4
        elif action == "combo":
            # 3-hit combo: hands alternate.
            phase_p = (progress * 3) % 1.0
            hit_num = int(progress * 3)
            if hit_num == 0 or hit_num == 2:
                # Front hand punches (hit 1, 3).
                if phase_p < 0.5:
                    t = phase_p / 0.5
                    front_hand_x = cx + facing * int(6 + t * 22)
                else:
                    t = (phase_p - 0.5) / 0.5
                    front_hand_x = cx + facing * int(28 - t * 16)
                back_hand_x = cx - facing * 4
            else:
                # Back hand punches (hit 2 - uppercut effect).
                if phase_p < 0.5:
                    t = phase_p / 0.5
                    back_hand_x = cx - facing * int(6 - t * 12)
                    back_hand_y = cy - 4 - int(t * 6)
                else:
                    t = (phase_p - 0.5) / 0.5
                    back_hand_x = cx - facing * int(6 - (1 - t) * 12)
                    back_hand_y = cy - 4 - int((1 - t) * 6)
                front_hand_x = cx + facing * 8
                front_hand_y = cy - 4
        elif action == "dash":
            # Both hands forward in fist position.
            front_hand_x = cx + facing * 22
            front_hand_y = cy - 6
            back_hand_x = cx + facing * 16
            back_hand_y = cy - 2
        elif action == "burst":
            # Cocked back charging.
            if progress < 0.5:
                # Charging: both hands drawn back.
                t = progress / 0.5
                front_hand_x = cx + facing * int(12 - t * 8)
                front_hand_y = cy - 4 - int(t * 3)
                back_hand_x = cx - facing * int(6 + t * 4)
                back_hand_y = cy - 4
            elif progress < 0.7:
                # PUNCH forward (both together).
                t = (progress - 0.5) / 0.2
                front_hand_x = cx + facing * int(4 + t * 30)
                front_hand_y = cy - 7 + int(t * 3)
                back_hand_x = cx + facing * int(-10 + t * 20)
                back_hand_y = cy - 4
            else:
                # Return.
                t = (progress - 0.7) / 0.3
                front_hand_x = cx + facing * int(34 - t * 22)
                front_hand_y = cy - 4
                back_hand_x = cx + facing * int(10 - t * 16)
                back_hand_y = cy - 4
        # Compute elbows.
        front_elbow = _NS_rakzhan._arm_elbow(front_sh, (front_hand_x, front_hand_y), bend=4)
        back_elbow = _NS_rakzhan._arm_elbow(back_sh, (back_hand_x, back_hand_y), bend=4)
        # Draw back arm first (behind).
        _NS_rakzhan._draw_arm_segment(surface, back_sh, back_elbow,
                                       (back_hand_x, back_hand_y), phase,
                                       is_charging=(action == "burst" and progress < 0.5))
        # Front arm.
        _NS_rakzhan._draw_arm_segment(surface, front_sh, front_elbow,
                                       (front_hand_x, front_hand_y), phase,
                                       is_charging=(action == "burst" and progress < 0.5))
    def _draw_arm_segment(surface, shoulder, elbow, hand, phase, is_charging=False):
        """Draw arm with tribal tattoo + flaming fist."""
        sx, sy = shoulder
        ex, ey = elbow
        hx, hy = hand
        # Upper arm (with tribal glow).
        pygame.draw.line(surface, _NS_rakzhan.PALETTE["shadow_deep"],
                         (sx + 1, sy + 1), (ex + 1, ey + 1), 6)
        pygame.draw.line(surface, _NS_rakzhan.PALETTE["skin_darkest"],
                         (sx, sy), (ex, ey), 5)
        pygame.draw.line(surface, _NS_rakzhan.PALETTE["skin_dark"],
                         (sx, sy), (ex, ey), 4)
        pygame.draw.line(surface, _NS_rakzhan.PALETTE["skin_mid"],
                         (sx, sy - 1), (ex, ey - 1), 2)
        pygame.draw.line(surface, _NS_rakzhan.PALETTE["skin_light"],
                         (sx, sy - 2), (ex, ey - 2), 1)
        # Tribal tattoo on upper arm (glowing orange).
        mid_up_x = (sx + ex) // 2
        mid_up_y = (sy + ey) // 2
        for i in range(3):
            offset_y = i - 1
            pygame.draw.line(surface, _NS_rakzhan.PALETTE["tattoo_dark"],
                             (mid_up_x - 2, mid_up_y + offset_y),
                             (mid_up_x + 2, mid_up_y + offset_y), 1)
        pygame.draw.line(surface, _NS_rakzhan.PALETTE["tattoo_mid"],
                         (mid_up_x - 2, mid_up_y),
                         (mid_up_x + 2, mid_up_y), 1)
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["tattoo_shine"],
                         (mid_up_x, mid_up_y, 1, 1))
        # Forearm.
        pygame.draw.line(surface, _NS_rakzhan.PALETTE["shadow_deep"],
                         (ex + 1, ey + 1), (hx + 1, hy + 1), 6)
        pygame.draw.line(surface, _NS_rakzhan.PALETTE["skin_darkest"],
                         (ex, ey), (hx, hy), 5)
        pygame.draw.line(surface, _NS_rakzhan.PALETTE["skin_dark"],
                         (ex, ey), (hx, hy), 3)
        pygame.draw.line(surface, _NS_rakzhan.PALETTE["skin_mid"],
                         (ex, ey - 1), (hx, hy - 1), 1)
        # Gold bracer on forearm.
        mid_fore_x = (ex + hx) // 2
        mid_fore_y = (ey + hy) // 2
        # Perpendicular direction.
        dx = hx - ex
        dy = hy - ey
        length = max(1, math.sqrt(dx * dx + dy * dy))
        perp_x = -dy / length
        perp_y = dx / length
        # Bracer band.
        bracer_pts = [
            (int(mid_fore_x - dx / length * 3 + perp_x * 3),
             int(mid_fore_y - dy / length * 3 + perp_y * 3)),
            (int(mid_fore_x + dx / length * 3 + perp_x * 3),
             int(mid_fore_y + dy / length * 3 + perp_y * 3)),
            (int(mid_fore_x + dx / length * 3 - perp_x * 3),
             int(mid_fore_y + dy / length * 3 - perp_y * 3)),
            (int(mid_fore_x - dx / length * 3 - perp_x * 3),
             int(mid_fore_y - dy / length * 3 - perp_y * 3)),
        ]
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["gold_dark"], bracer_pts)
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["gold_mid"], [
            (int(mid_fore_x - dx / length * 2 + perp_x * 2),
             int(mid_fore_y - dy / length * 2 + perp_y * 2)),
            (int(mid_fore_x + dx / length * 2 + perp_x * 2),
             int(mid_fore_y + dy / length * 2 + perp_y * 2)),
            (int(mid_fore_x + dx / length * 2 - perp_x * 2),
             int(mid_fore_y + dy / length * 2 - perp_y * 2)),
            (int(mid_fore_x - dx / length * 2 - perp_x * 2),
             int(mid_fore_y - dy / length * 2 - perp_y * 2)),
        ])
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["gold_light"],
                         (mid_fore_x - 1, mid_fore_y, 2, 1))
        # FLAMING FIST.
        _NS_rakzhan._draw_flaming_fist(surface, hx, hy, phase, is_charging)
    def _draw_flaming_fist(surface, fx, fy, phase, is_charging=False):
        """Fist wrapped in fire."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        intensity = 1.6 if is_charging else 1.0
        # Fire aura around fist.
        aura_r = int((5 + math.sin(phase * 3) * 1) * intensity)
        for r in range(aura_r + 6, 0, -1):
            alpha = _NS_rakzhan._alpha(70 * (aura_r + 6 - r) / (aura_r + 6) * pulse * intensity)
            _NS_rakzhan._aacircle(surface,
                                  (*_NS_rakzhan.PALETTE["fire_dark"], alpha),
                                  (fx, fy), r)
        for r in range(aura_r + 3, 0, -1):
            alpha = _NS_rakzhan._alpha(110 * (aura_r + 3 - r) / (aura_r + 3) * pulse * intensity)
            _NS_rakzhan._aacircle(surface,
                                  (*_NS_rakzhan.PALETTE["fire_mid"], alpha),
                                  (fx, fy), r)
        # Fist (skin).
        _NS_rakzhan._aacircle(surface, _NS_rakzhan.PALETTE["shadow_deep"], (fx + 1, fy + 1), 4)
        _NS_rakzhan._aacircle(surface, _NS_rakzhan.PALETTE["skin_darkest"], (fx, fy), 4)
        _NS_rakzhan._aacircle(surface, _NS_rakzhan.PALETTE["skin_dark"], (fx, fy), 3)
        _NS_rakzhan._aacircle(surface, _NS_rakzhan.PALETTE["skin_mid"], (fx, fy - 1), 2)
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["skin_light"], (fx, fy - 2, 1, 1))
        # Knuckles (small bumps).
        for kx_off in (-2, 0, 2):
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["skin_darkest"],
                             (fx + kx_off, fy + 1, 1, 1))
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["skin_light"],
                             (fx + kx_off, fy, 1, 1))
        # Fire tongues rising from fist.
        for i in range(5):
            angle = i * math.pi / 4 - math.pi / 2
            flame_len = int((5 + math.sin(phase * 4 + i) * 2) * intensity)
            fx_end = fx + int(math.cos(angle) * flame_len)
            fy_end = fy + int(math.sin(angle) * flame_len)
            pygame.draw.line(surface, _NS_rakzhan.PALETTE["fire_mid"],
                             (fx, fy), (fx_end, fy_end), 2)
            pygame.draw.line(surface, _NS_rakzhan.PALETTE["fire_light"],
                             (fx, fy), (fx_end, fy_end), 1)
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["fire_hot"], (fx_end, fy_end, 1, 1))
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["fire_shine"], (fx_end, fy_end, 1, 1))
        # Extra sparks.
        for i in range(4):
            spark_t = (phase * 3 + i * 0.25) % 1.0
            spark_r = int(aura_r + 4 + spark_t * 4)
            angle = phase * 4 + i * math.pi / 2
            spx = fx + int(math.cos(angle) * spark_r)
            spy = fy + int(math.sin(angle) * spark_r)
            alpha = _NS_rakzhan._alpha(240 * (1 - spark_t) * intensity)
            pygame.draw.rect(surface, (*_NS_rakzhan.PALETTE["fire_shine"], alpha),
                             (spx, spy, 1, 1))
    def _draw_head(surface, cx, cy, facing, phase, action):
        """Young male martial artist head with red hair."""
        # Hair back layer (behind head).
        _NS_rakzhan._draw_hair_back(surface, cx, cy, facing, phase)
        # Face.
        face_pts = [
            (cx - 6, cy - 4),
            (cx - 7, cy),
            (cx - 6, cy + 4),
            (cx - 3, cy + 8),
            (cx + 3, cy + 8),
            (cx + 6, cy + 4),
            (cx + 7, cy),
            (cx + 6, cy - 4),
            (cx + 3, cy - 7),
            (cx - 3, cy - 7),
        ]
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in face_pts])
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["skin_darkest"], face_pts)
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["skin_dark"], [
            (cx - 5, cy - 3),
            (cx - 6, cy),
            (cx - 5, cy + 3),
            (cx - 2, cy + 7),
            (cx + 2, cy + 7),
            (cx + 5, cy + 3),
            (cx + 6, cy),
            (cx + 5, cy - 3),
            (cx + 2, cy - 6),
            (cx - 2, cy - 6),
        ])
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["skin_mid"], [
            (cx - 3, cy - 2),
            (cx - 4, cy + 1),
            (cx - 2, cy + 5),
            (cx + 2, cy + 5),
            (cx + 4, cy + 1),
            (cx + 3, cy - 2),
        ])
        # Cheek highlight.
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["skin_light"], (cx - 3, cy, 1, 1))
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["skin_light"], (cx + 2, cy, 1, 1))
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["skin_shine"], (cx - 3, cy, 1, 1))
        # Front hair (spiky bangs).
        _NS_rakzhan._draw_hair_front(surface, cx, cy, facing, phase)
        # Red demon eyes.
        _NS_rakzhan._draw_eyes(surface, cx, cy, phase, action)
        # Nose.
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["skin_darkest"], (cx, cy + 2, 1, 2))
        # Mouth (fierce grin or roar during attack).
        if action in ("punch", "combo", "dash", "burst") and phase % 1 < 0.6:
            # Roar/shout.
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["shadow_deep"],
                             (cx - 2, cy + 5, 5, 2))
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["eye_dark"],
                             (cx - 1, cy + 5, 3, 1))
        else:
            # Determined line.
            pygame.draw.line(surface, _NS_rakzhan.PALETTE["shadow_deep"],
                             (cx - 2, cy + 6), (cx + 2, cy + 6), 1)
        # GOLD CROWN with GEM.
        _NS_rakzhan._draw_crown(surface, cx, cy - 8, facing, phase)
    def _draw_hair_back(surface, cx, cy, facing, phase):
        """Wild spiky hair backdrop."""
        sway = math.sin(phase * 0.5) * 1
        # Big spiky hair mass.
        hair_pts = [
            (cx - 8, cy - 6),
            (cx - 10 + int(sway), cy - 10),
            (cx - 8, cy - 14),
            (cx - 4, cy - 17),
            (cx, cy - 18),
            (cx + 4, cy - 17),
            (cx + 8, cy - 14),
            (cx + 10 - int(sway), cy - 10),
            (cx + 8, cy - 6),
            (cx + 6, cy - 4),
            (cx - 6, cy - 4),
        ]
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in hair_pts])
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["hair_darkest"], hair_pts)
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["hair_dark"], [
            (cx - 7, cy - 6),
            (cx - 9 + int(sway), cy - 10),
            (cx - 7, cy - 13),
            (cx - 3, cy - 16),
            (cx, cy - 17),
            (cx + 3, cy - 16),
            (cx + 7, cy - 13),
            (cx + 9 - int(sway), cy - 10),
            (cx + 7, cy - 6),
        ])
        # Spiky ends going up (flame-like).
        for spike_i, (spike_x, spike_h) in enumerate([
            (-6, -20), (-3, -22), (0, -23), (3, -22), (6, -20),
        ]):
            base_x = cx + spike_x + int(sway * 0.5)
            tip_y = cy + spike_h + int(math.sin(phase + spike_i) * 1)
            _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["hair_dark"], [
                (base_x - 2, cy - 15),
                (base_x, tip_y),
                (base_x + 2, cy - 15),
            ])
            _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["hair_mid"], [
                (base_x - 1, cy - 15),
                (base_x, tip_y + 1),
                (base_x + 1, cy - 15),
            ])
            # Fiery highlights on hair tips.
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["hair_light"], (base_x, tip_y + 1, 1, 1))
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["hair_shine"], (base_x, tip_y, 1, 1))
        # Hair strands on sides (flowing).
        for i, (sx_off, sy_off) in enumerate([(-8, -4), (8, -4), (-9, 0), (9, 0)]):
            strand_x = cx + sx_off + int(sway * 0.3)
            strand_y = cy + sy_off
            pygame.draw.line(surface, _NS_rakzhan.PALETTE["hair_dark"],
                             (strand_x, strand_y),
                             (strand_x - int(sway), strand_y + 5), 2)
            pygame.draw.line(surface, _NS_rakzhan.PALETTE["hair_mid"],
                             (strand_x, strand_y),
                             (strand_x - int(sway), strand_y + 5), 1)
    def _draw_hair_front(surface, cx, cy, facing, phase):
        """Front bangs falling over forehead."""
        # Spiky bangs.
        for i, x_off in enumerate((-5, -2, 0, 2, 5)):
            bang_x = cx + x_off
            bang_top_y = cy - 8
            bang_bot_y = cy - 4 + int(math.sin(phase + i) * 1)
            _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["hair_darkest"], [
                (bang_x - 1, bang_top_y),
                (bang_x + 2, bang_top_y),
                (bang_x + 1, bang_bot_y),
                (bang_x, bang_bot_y),
            ])
            _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["hair_dark"], [
                (bang_x, bang_top_y + 1),
                (bang_x + 1, bang_top_y + 1),
                (bang_x + 1, bang_bot_y - 1),
                (bang_x, bang_bot_y - 1),
            ])
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["hair_mid"],
                             (bang_x, bang_top_y + 2, 1, 2))
            # Fire glow at bang tips.
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["hair_light"], (bang_x, bang_bot_y - 1, 1, 1))
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["fire_hot"], (bang_x, bang_bot_y, 1, 1))
    def _draw_eyes(surface, cx, cy, phase, action):
        """Sharp red glowing eyes."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        intensity = 1.4 if action in ("punch", "combo", "dash", "burst") else 1.0
        for side in (-1, 1):
            ex = cx + side * 3
            ey = cy + 1
            # Deep socket.
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["eye_socket"],
                             (ex - 1, ey - 1, 3, 2))
            # Glow halo.
            for r in range(4, 0, -1):
                alpha = _NS_rakzhan._alpha(120 * (4 - r) / 4 * pulse * intensity)
                _NS_rakzhan._aacircle(surface,
                                      (*_NS_rakzhan.PALETTE["eye_mid"], alpha),
                                      (ex, ey), r)
            # Eye core.
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["eye_dark"], (ex - 1, ey, 3, 1))
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["eye_mid"], (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["eye_light"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["eye_glow"], (ex, ey, 1, 1))
    def _draw_crown(surface, cx, cy, facing, phase):
        """Gold crown with central red gem."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Crown band.
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["gold_darkest"], (cx - 6, cy, 13, 3))
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["gold_dark"], (cx - 6, cy, 13, 2))
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["gold_mid"], (cx - 5, cy, 11, 1))
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["gold_light"], (cx - 4, cy, 9, 1))
        # Side peaks.
        for side in (-1, 1):
            peak_x = cx + side * 5
            _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["gold_dark"], [
                (peak_x - 1, cy),
                (peak_x, cy - 3),
                (peak_x + 1, cy),
            ])
            _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["gold_mid"], [
                (peak_x, cy),
                (peak_x, cy - 2),
                (peak_x + 1, cy),
            ])
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["gold_light"], (peak_x, cy - 2, 1, 1))
        # Central peak with GEM.
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["gold_dark"], [
            (cx - 2, cy),
            (cx, cy - 5),
            (cx + 2, cy),
        ])
        _NS_rakzhan._poly(surface, _NS_rakzhan.PALETTE["gold_mid"], [
            (cx - 1, cy - 1),
            (cx, cy - 4),
            (cx + 1, cy - 1),
        ])
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["gold_light"], (cx, cy - 3, 1, 1))
        # Red gem in center of crown.
        for r in range(4, 0, -1):
            alpha = _NS_rakzhan._alpha(120 * (4 - r) / 4 * pulse)
            _NS_rakzhan._aacircle(surface,
                                  (*_NS_rakzhan.PALETTE["gem_mid"], alpha),
                                  (cx, cy + 1), r)
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["gem_dark"], (cx - 1, cy + 1, 3, 1))
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["gem_mid"], (cx, cy + 1, 2, 1))
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["gem_light"], (cx, cy + 1, 1, 1))
        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["gem_shine"], (cx, cy + 1, 1, 1))
    # ============================================================
    # BASIC ATTACK: Simple punch shockwave
    # ============================================================
    def _draw_basic_punch_fx(surface, boss, x, y):
        """Fire shockwave when fist connects."""
        progress = getattr(boss, "_rz_attack_progress", 0.0)
        if progress < 0.55 or progress > 0.85:
            return
        facing = boss.direction
        # Origin at fist extended position.
        origin_x = x + facing * 30
        origin_y = y - 4
        t = (progress - 0.55) / 0.30
        radius = int(4 + t * 22)
        alpha = _NS_rakzhan._alpha(240 * (1 - t))
        # Ring shockwave.
        _NS_rakzhan._aacircle(surface, (*_NS_rakzhan.PALETTE["fire_dark"], alpha),
                              (origin_x, origin_y), radius + 2, 3)
        _NS_rakzhan._aacircle(surface, (*_NS_rakzhan.PALETTE["fire_mid"], alpha),
                              (origin_x, origin_y), radius, 2)
        _NS_rakzhan._aacircle(surface, (*_NS_rakzhan.PALETTE["fire_light"], alpha),
                              (origin_x, origin_y), max(1, radius - 4), 1)
        # Radial fire rays.
        for i in range(8):
            angle = i * math.pi / 4
            ex = origin_x + int(math.cos(angle) * radius)
            ey = origin_y + int(math.sin(angle) * radius)
            pygame.draw.line(surface, (*_NS_rakzhan.PALETTE["fire_hot"], alpha),
                             (origin_x, origin_y), (ex, ey), 2)
            pygame.draw.rect(surface, (*_NS_rakzhan.PALETTE["fire_shine"], alpha),
                             (ex, ey, 2, 2))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        """Shadow beneath floating fighter."""
        breath = math.sin(phase * 0.7) * 0.15 + 0.85
        shadow = pygame.Surface((120, 24), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, int((10 - radius) * 18 * breath))
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 12 - radius,
                                 100 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (10, 3, 3, int(160 * breath)),
                            (10, 8, 100, 8))
        surface.blit(shadow, (x - 60, y - 12))
    def _draw_floor_flames(surface, cx, cy, phase, intense=False):
        """Flames licking up from ground beneath fighter."""
        strength = 1.6 if intense else 1.0
        # Flame tongues rising.
        for i in range(9):
            offset = -20 + i * 5
            t = (phase * 0.5 + i * 0.13) % 1.0
            fx = cx + offset + int(math.sin(phase + i * 0.6) * 3)
            fy = cy + 4 - int(t * 22)
            flame_size = int((4 + t * 2) * strength)
            alpha = _NS_rakzhan._alpha(230 * (1 - t) * strength)
            if alpha > 0:
                # Flame shape (teardrop).
                _NS_rakzhan._aacircle(surface, (*_NS_rakzhan.PALETTE["fire_dark"], alpha),
                                      (fx, fy), flame_size)
                _NS_rakzhan._aacircle(surface, (*_NS_rakzhan.PALETTE["fire_mid"], alpha),
                                      (fx, fy - 1), max(1, flame_size - 1))
                _NS_rakzhan._aacircle(surface, (*_NS_rakzhan.PALETTE["fire_light"], alpha),
                                      (fx, fy - 2), max(1, flame_size - 2))
                pygame.draw.rect(surface, (*_NS_rakzhan.PALETTE["fire_hot"], alpha),
                                 (fx, fy - 3, 1, 1))
                pygame.draw.rect(surface, (*_NS_rakzhan.PALETTE["fire_shine"], alpha),
                                 (fx, fy - 3, 1, 1))
        # Small embers floating up.
        for i in range(6):
            t = (phase * 0.7 + i * 0.17) % 1.0
            ex = cx - 22 + i * 8 + int(math.sin(phase * 1.5 + i) * 5)
            ey = cy - int(t * 26)
            alpha = _NS_rakzhan._alpha(240 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_rakzhan.PALETTE["fire_light"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_rakzhan.PALETTE["fire_shine"], alpha),
                                 (ex, ey, 1, 1))
    def _draw_fire_aura(surface, x, y, phase):
        """Fiery orange-red aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_rakzhan._alpha((85 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_rakzhan._aacircle(aura,
                                      (*_NS_rakzhan.PALETTE["fire_darkest"], alpha),
                                      (100, 90), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_rakzhan._alpha((55 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_rakzhan._aacircle(aura,
                                      (*_NS_rakzhan.PALETTE["fire_dark"], alpha),
                                      (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))
        # Floating fire particles.
        for i in range(14):
            angle = phase * 0.4 + i * math.pi / 7
            radius = 42 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = _NS_rakzhan.PALETTE["fire_mid"] if i % 2 == 0 else _NS_rakzhan.PALETTE["fire_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["fire_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Fiery runic ground ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_rakzhan.PALETTE["fire_darkest"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_rakzhan.PALETTE["fire_dark"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_rakzhan.PALETTE["fire_mid"], 180),
                            (25, 22, 120, 18), 1)
        # Runes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_rakzhan.PALETTE["fire_light"], 220),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.rect(ring, _NS_rakzhan.PALETTE["fire_hot"], (x2, y2, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_rakzhan.PALETTE["fire_hot"],
                                       _NS_rakzhan._alpha(160 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # SKILL Q: TRANSCENDENT FIST (dash punch)
    # ============================================================
    def _draw_transcendent_ground(surface, boss, x, y, timer, phase):
        """Dash trail on ground."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_rakzhan._target_position(boss, x, y)
        if 0.3 < progress < 0.7:
            t = (progress - 0.3) / 0.4
            start_x = x + facing * 20
            start_y = y + 40
            end_x = int(start_x + (tx - start_x) * t)
            end_y = int(start_y + (ty - start_y) * t * 0.3)
            # Fiery dash trail on ground.
            for i in range(6):
                trail_t = t - i * 0.08
                if trail_t < 0:
                    continue
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t * 0.3)
                alpha = _NS_rakzhan._alpha(240 - i * 35)
                pygame.draw.ellipse(surface, (*_NS_rakzhan.PALETTE["fire_dark"], alpha),
                                    (px - 15, py - 3, 30, 8))
                pygame.draw.ellipse(surface, (*_NS_rakzhan.PALETTE["fire_mid"], alpha),
                                    (px - 12, py - 2, 24, 5))
                pygame.draw.ellipse(surface, (*_NS_rakzhan.PALETTE["fire_hot"], alpha),
                                    (px - 8, py - 1, 16, 3))
    def _draw_transcendent_dash_fx(surface, boss, x, y, timer, phase):
        """Fiery streak from boss to target during dash."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_rakzhan._target_position(boss, x, y)
        if progress < 0.3:
            # Charge up: fists gathering fire.
            t = progress / 0.3
            for hand_off in (facing * 22, facing * 16):
                hx = x + hand_off
                hy = y - 4
                cr = int(4 + t * 4)
                for r in range(cr + 5, 0, -1):
                    alpha = _NS_rakzhan._alpha(200 * (cr + 5 - r) / (cr + 5))
                    _NS_rakzhan._aacircle(surface,
                                          (*_NS_rakzhan.PALETTE["fire_mid"], alpha),
                                          (hx, hy), r)
                _NS_rakzhan._aacircle(surface, _NS_rakzhan.PALETTE["fire_shine"], (hx, hy), 2)
        elif progress < 0.7:
            # DASHING: horizontal streak of fire from boss to target.
            t = (progress - 0.3) / 0.4
            intensity = math.sin(t * math.pi)
            start_x = x + facing * 20
            start_y = y - 4
            cur_end_x = int(start_x + (tx - start_x) * t)
            cur_end_y = int(start_y + (ty - start_y) * t)
            # Streak layers.
            for width, color in [
                (8, _NS_rakzhan.PALETTE["fire_dark"]),
                (5, _NS_rakzhan.PALETTE["fire_mid"]),
                (3, _NS_rakzhan.PALETTE["fire_light"]),
                (1, _NS_rakzhan.PALETTE["fire_shine"]),
            ]:
                alpha = _NS_rakzhan._alpha(240 * intensity)
                pygame.draw.line(surface, (*color, alpha),
                                 (start_x, start_y), (cur_end_x, cur_end_y), width)
            # Sparks along streak.
            for i in range(12):
                sp_t = ((phase * 3 + i * 0.08) % 1.0)
                dx = tx - start_x
                dy = ty - start_y
                length = max(1, math.sqrt(dx * dx + dy * dy))
                perp_x = -dy / length
                perp_y = dx / length
                sx = int(start_x + dx * sp_t)
                sy = int(start_y + dy * sp_t)
                offset = math.sin(phase * 5 + i) * 5
                sx += int(perp_x * offset)
                sy += int(perp_y * offset)
                alpha = _NS_rakzhan._alpha(240 * intensity)
                pygame.draw.rect(surface, (*_NS_rakzhan.PALETTE["fire_hot"], alpha), (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_rakzhan.PALETTE["fire_shine"], alpha), (sx, sy, 1, 1))
            # Impact burst at moving end.
            impact_r = int(6 + t * 12)
            alpha = _NS_rakzhan._alpha(240 * intensity)
            _NS_rakzhan._aacircle(surface, (*_NS_rakzhan.PALETTE["fire_dark"], alpha),
                                  (cur_end_x, cur_end_y), impact_r + 2, 2)
            _NS_rakzhan._aacircle(surface, (*_NS_rakzhan.PALETTE["fire_mid"], alpha),
                                  (cur_end_x, cur_end_y), impact_r, 2)
            _NS_rakzhan._aacircle(surface, (*_NS_rakzhan.PALETTE["fire_hot"], alpha),
                                  (cur_end_x, cur_end_y), max(1, impact_r // 2))
            _NS_rakzhan._aacircle(surface, (*_NS_rakzhan.PALETTE["fire_shine"], alpha),
                                  (cur_end_x, cur_end_y), max(1, impact_r // 4))
        else:
            # Aftermath sparks at target.
            t = (progress - 0.7) / 0.3
            for i in range(10):
                angle = i * math.pi / 5
                sp_r = int(15 + t * 15)
                sx = tx + int(math.cos(angle) * sp_r)
                sy = ty + int(math.sin(angle) * sp_r * 0.7)
                alpha = _NS_rakzhan._alpha(220 * (1 - t))
                pygame.draw.rect(surface, (*_NS_rakzhan.PALETTE["fire_hot"], alpha), (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_rakzhan.PALETTE["fire_shine"], alpha), (sx, sy, 1, 1))
    # ============================================================
    # SKILL W: SOUL COMBO (3 hit sweeps with knock airborne)
    # ============================================================
    def _draw_soulcombo_fx(surface, boss, x, y, timer, phase):
        """3 crescent sweep slashes with fire trail."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_rakzhan._target_position(boss, x, y)
        # 3 phases: each ~0.33.
        for hit_i in range(3):
            hit_start = hit_i * 0.33
            hit_end = hit_start + 0.33
            if progress < hit_start or progress > hit_end:
                continue
            local_t = (progress - hit_start) / 0.33
            intensity = math.sin(local_t * math.pi)
            # Fist origin (front fist).
            origin_x = x + facing * 20
            origin_y = y - 4
            # Slash arc: crescent sweep from top-back to bottom-front.
            slash_angle_start = -math.pi / 3 - hit_i * 0.3
            slash_angle_end = math.pi / 3 + hit_i * 0.3
            slash_r = 24
            # Direction flip per hit.
            if hit_i == 1:
                slash_angle_start, slash_angle_end = slash_angle_end, slash_angle_start
            # Current angle within slash arc.
            cur_angle = slash_angle_start + (slash_angle_end - slash_angle_start) * local_t
            # Arc trail (crescent slash line).
            trail_pts = []
            for i in range(10):
                trail_t = max(0, local_t - i * 0.05)
                ang = slash_angle_start + (slash_angle_end - slash_angle_start) * trail_t
                px = origin_x + int(math.cos(ang) * slash_r) * facing
                py = origin_y + int(math.sin(ang) * slash_r)
                trail_pts.append((px, py))
            # Draw arc trail thick.
            for i in range(len(trail_pts) - 1):
                alpha = _NS_rakzhan._alpha(240 * intensity * (1 - i * 0.1))
                if alpha <= 0:
                    continue
                pygame.draw.line(surface, (*_NS_rakzhan.PALETTE["fire_dark"], alpha),
                                 trail_pts[i], trail_pts[i + 1], 6)
                pygame.draw.line(surface, (*_NS_rakzhan.PALETTE["fire_mid"], alpha),
                                 trail_pts[i], trail_pts[i + 1], 4)
                pygame.draw.line(surface, (*_NS_rakzhan.PALETTE["fire_light"], alpha),
                                 trail_pts[i], trail_pts[i + 1], 2)
                pygame.draw.line(surface, (*_NS_rakzhan.PALETTE["fire_shine"], alpha),
                                 trail_pts[i], trail_pts[i + 1], 1)
            # Bright leading edge.
            if trail_pts:
                lead = trail_pts[0]
                _NS_rakzhan._aacircle(surface,
                                      (*_NS_rakzhan.PALETTE["fire_shine"],
                                       _NS_rakzhan._alpha(255 * intensity)),
                                      lead, 3)
                pygame.draw.rect(surface, _NS_rakzhan.PALETTE["white"],
                                 (lead[0] - 1, lead[1] - 1, 2, 2))
            # Impact glow at target.
            if local_t > 0.5:
                imp_alpha = _NS_rakzhan._alpha(200 * intensity)
                impact_offset_y = -int(hit_i * 8) if hit_i == 2 else 0  # 3rd hit = airborne
                imp_r = int(12 + local_t * 6)
                _NS_rakzhan._aacircle(surface, (*_NS_rakzhan.PALETTE["fire_dark"], imp_alpha),
                                      (tx, ty + impact_offset_y), imp_r + 2, 2)
                _NS_rakzhan._aacircle(surface, (*_NS_rakzhan.PALETTE["fire_mid"], imp_alpha),
                                      (tx, ty + impact_offset_y), imp_r, 2)
                _NS_rakzhan._aacircle(surface, (*_NS_rakzhan.PALETTE["fire_hot"], imp_alpha),
                                      (tx, ty + impact_offset_y), max(1, imp_r // 2))
                # Special: 3rd hit = knock airborne (upward burst).
                if hit_i == 2:
                    for i in range(10):
                        angle = i * math.pi / 5
                        burst_r = int(imp_r * 1.5)
                        ex = tx + int(math.cos(angle) * burst_r)
                        ey = ty + impact_offset_y + int(math.sin(angle) * burst_r * 0.7)
                        pygame.draw.line(surface,
                                         (*_NS_rakzhan.PALETTE["fire_hot"], imp_alpha),
                                         (tx, ty + impact_offset_y), (ex, ey), 2)
                        pygame.draw.rect(surface, _NS_rakzhan.PALETTE["fire_shine"], (ex, ey, 2, 2))
    # ============================================================
    # SKILL E: MY TURN (arena dome)
    # ============================================================
    def _draw_myturn_ground(surface, boss, x, y, timer, phase):
        """Arena floor ring on ground."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        origin_x = x
        origin_y = y + 42
        r = int(min(70, 30 + progress * 90))
        alpha = _NS_rakzhan._alpha(220)
        # Multiple concentric rings.
        pygame.draw.ellipse(surface, (*_NS_rakzhan.PALETTE["fire_darkest"], alpha),
                            (origin_x - r, origin_y - r // 3, r * 2, r * 2 // 3), 4)
        pygame.draw.ellipse(surface, (*_NS_rakzhan.PALETTE["fire_dark"], alpha),
                            (origin_x - r + 3, origin_y - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 3)
        pygame.draw.ellipse(surface, (*_NS_rakzhan.PALETTE["fire_mid"], 180),
                            (origin_x - r + 8, origin_y - r // 3 + 4,
                             r * 2 - 16, r * 2 // 3 - 8), 2)
        pygame.draw.ellipse(surface, (*_NS_rakzhan.PALETTE["fire_hot"], 140),
                            (origin_x - r + 14, origin_y - r // 3 + 7,
                             r * 2 - 28, r * 2 // 3 - 14), 1)
        # Runes around perimeter.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            rx = origin_x + int(math.cos(angle) * r)
            ry = origin_y + int(math.sin(angle) * r * 0.4)
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["fire_shine"], (rx - 1, ry, 3, 2))
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["white"], (rx, ry, 1, 1))
    def _draw_myturn_dome(surface, boss, x, y, timer, phase):
        """Dome of fire pillars around boss."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        origin_x = x
        origin_y = y + 42
        r = int(min(70, 30 + progress * 90))
        # Fire pillars around perimeter.
        num_pillars = 12
        for i in range(num_pillars):
            angle = i * math.pi * 2 / num_pillars
            px = origin_x + int(math.cos(angle) * r)
            py = origin_y + int(math.sin(angle) * r * 0.4)
            # Pillar height varies.
            pillar_h = int(30 + math.sin(phase * 2 + i * 0.5) * 8)
            pillar_w = 4
            # Fire pillar (rising).
            for layer_i, (color, alpha_v) in enumerate([
                (_NS_rakzhan.PALETTE["fire_dark"], 220),
                (_NS_rakzhan.PALETTE["fire_mid"], 200),
                (_NS_rakzhan.PALETTE["fire_light"], 180),
                (_NS_rakzhan.PALETTE["fire_hot"], 150),
            ]):
                w = pillar_w - layer_i
                if w < 1:
                    continue
                pygame.draw.rect(surface, (*color, alpha_v),
                                 (px - w, py - pillar_h + layer_i * 2, w * 2, pillar_h))
            # Top of pillar (flame tip).
            pygame.draw.rect(surface, _NS_rakzhan.PALETTE["fire_shine"],
                             (px, py - pillar_h, 1, 2))
            _NS_rakzhan._aacircle(surface, _NS_rakzhan.PALETTE["fire_hot"],
                                  (px, py - pillar_h), 2)
            # Connecting fire arc to next pillar.
            next_angle = ((i + 1) % num_pillars) * math.pi * 2 / num_pillars
            npx = origin_x + int(math.cos(next_angle) * r)
            npy = origin_y + int(math.sin(next_angle) * r * 0.4)
            top_y = py - pillar_h + int(math.sin(phase * 2 + i) * 2)
            n_top_y = npy - int(30 + math.sin(phase * 2 + i + 1) * 8)
            # Arc line between pillar tops.
            pygame.draw.line(surface, _NS_rakzhan.PALETTE["fire_mid"],
                             (px, top_y), (npx, n_top_y), 2)
            pygame.draw.line(surface, _NS_rakzhan.PALETTE["fire_hot"],
                             (px, top_y), (npx, n_top_y), 1)
        # Rising embers inside dome.
        for i in range(15):
            t = (phase * 0.6 + i * 0.09) % 1.0
            em_angle = i * math.pi * 2 / 15 + phase * 0.3
            em_dist = int(r * 0.6)
            ex = origin_x + int(math.cos(em_angle) * em_dist)
            ey = origin_y + int(math.sin(em_angle) * em_dist * 0.4) - int(t * 30)
            alpha = _NS_rakzhan._alpha(230 * (1 - t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_rakzhan.PALETTE["fire_light"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_rakzhan.PALETTE["fire_shine"], alpha),
                                 (ex, ey, 1, 1))
    # ============================================================
    # SKILL R: LET ME SHOW YOU (burst punch shockwave)
    # ============================================================
    def _draw_letmeshow_ground(surface, boss, x, y, timer, phase):
        """Ground crack from boss forward."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_rakzhan._target_position(boss, x, y)
        if progress < 0.5:
            # Charge phase: rune circle forming below feet.
            t = progress / 0.5
            r = int(28 * t)
            alpha = _NS_rakzhan._alpha(200 * t)
            pygame.draw.ellipse(surface, (*_NS_rakzhan.PALETTE["fire_dark"], alpha),
                                (x - r, y + 42 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_rakzhan.PALETTE["fire_mid"], alpha),
                                (x - r + 3, y + 42 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.5
                sx = x + int(math.cos(angle) * r)
                sy = y + 42 + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_rakzhan.PALETTE["fire_hot"], (sx, sy, 2, 2))
        elif progress < 0.85:
            # After punch: burnt crack toward target.
            t = (progress - 0.5) / 0.35
            start_x = x + facing * 30
            start_y = y + 40
            for i in range(20):
                crack_t = i / 19
                cx_p = int(start_x + (tx - start_x) * crack_t)
                cy_p = int(start_y + (ty - start_y) * crack_t * 0.3)
                alpha = _NS_rakzhan._alpha(220 * (1 - t * 0.5))
                offset_x = int(math.sin(crack_t * 8) * 2)
                pygame.draw.rect(surface, (*_NS_rakzhan.PALETTE["fire_dark"], alpha),
                                 (cx_p + offset_x - 1, cy_p, 3, 2))
                pygame.draw.rect(surface, (*_NS_rakzhan.PALETTE["fire_hot"], alpha),
                                 (cx_p + offset_x, cy_p, 1, 1))
    def _draw_letmeshow_shockwave(surface, boss, x, y, timer, phase):
        """Massive burst punch shockwave to target."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_rakzhan._target_position(boss, x, y)
        if progress < 0.5:
            # Charging: massive fire aura at both fists (drawn by body arm code).
            # Extra ambient charge sparks converging.
            t = progress / 0.5
            for i in range(14):
                angle = phase * 3 + i * math.pi / 7
                dist = int(35 * (1 - t))
                center_x = x + facing * 4
                center_y = y - 4
                sx = center_x + int(math.cos(angle) * dist)
                sy = center_y + int(math.sin(angle) * dist)
                alpha = _NS_rakzhan._alpha(230 * t)
                pygame.draw.line(surface, (*_NS_rakzhan.PALETTE["fire_hot"], alpha),
                                 (sx, sy), (center_x, center_y), 1)
                pygame.draw.rect(surface, (*_NS_rakzhan.PALETTE["fire_shine"], alpha), (sx, sy, 2, 2))
            # Growing charge orb at chest.
            cr = int(4 + t * 12)
            for r in range(cr + 6, 0, -2):
                alpha = _NS_rakzhan._alpha(120 * (cr + 6 - r) / (cr + 6) * t)
                _NS_rakzhan._aacircle(surface,
                                      (*_NS_rakzhan.PALETTE["fire_mid"], alpha),
                                      (x + facing * 4, y - 4), r)
        elif progress < 0.75:
            # BURST: massive shockwave from fist forward.
            t = (progress - 0.5) / 0.25
            intensity = math.sin(t * math.pi)
            start_x = x + facing * 34
            start_y = y - 4
            # Expanding cone-shaped shockwave.
            dx = tx - start_x
            dy = ty - start_y
            length = max(1, math.sqrt(dx * dx + dy * dy))
            dir_x = dx / length
            dir_y = dy / length
            perp_x = -dir_y
            perp_y = dir_x
            # Multiple expanding rings.
            for ring_i in range(4):
                ring_dist = int(length * t) - ring_i * 15
                if ring_dist < 0:
                    continue
                cx_r = start_x + int(dir_x * ring_dist)
                cy_r = start_y + int(dir_y * ring_dist)
                ring_r = int(15 + ring_i * 5 + t * 10)
                alpha = _NS_rakzhan._alpha(220 * intensity * (4 - ring_i) / 4)
                _NS_rakzhan._aacircle(surface,
                                      (*_NS_rakzhan.PALETTE["fire_dark"], alpha),
                                      (cx_r, cy_r), ring_r + 2, 3)
                _NS_rakzhan._aacircle(surface,
                                      (*_NS_rakzhan.PALETTE["fire_mid"], alpha),
                                      (cx_r, cy_r), ring_r, 2)
                _NS_rakzhan._aacircle(surface,
                                      (*_NS_rakzhan.PALETTE["fire_hot"], alpha),
                                      (cx_r, cy_r), max(1, ring_r - 4), 1)
            # Main streak from fist to target.
            cur_end_x = int(start_x + dx * t)
            cur_end_y = int(start_y + dy * t)
            for width, color in [
                (14, _NS_rakzhan.PALETTE["fire_darkest"]),
                (10, _NS_rakzhan.PALETTE["fire_dark"]),
                (7, _NS_rakzhan.PALETTE["fire_mid"]),
                (4, _NS_rakzhan.PALETTE["fire_hot"]),
                (2, _NS_rakzhan.PALETTE["fire_shine"]),
            ]:
                alpha = _NS_rakzhan._alpha(255 * intensity)
                pygame.draw.line(surface, (*color, alpha),
                                 (start_x, start_y), (cur_end_x, cur_end_y), width)
            pygame.draw.line(surface, _NS_rakzhan.PALETTE["white"],
                             (start_x, start_y), (cur_end_x, cur_end_y), 1)
            # Impact explosion at target.
            if t > 0.6:
                impact_t = (t - 0.6) / 0.4
                impact_r = int(20 + impact_t * 30)
                impact_alpha = _NS_rakzhan._alpha(255 * intensity)
                _NS_rakzhan._aacircle(surface, (*_NS_rakzhan.PALETTE["fire_darkest"], impact_alpha),
                                      (tx, ty), impact_r + 4, 3)
                _NS_rakzhan._aacircle(surface, (*_NS_rakzhan.PALETTE["fire_dark"], impact_alpha),
                                      (tx, ty), impact_r, 3)
                _NS_rakzhan._aacircle(surface, (*_NS_rakzhan.PALETTE["fire_mid"], impact_alpha),
                                      (tx, ty), max(1, impact_r - 8), 2)
                _NS_rakzhan._aacircle(surface, (*_NS_rakzhan.PALETTE["fire_hot"], impact_alpha),
                                      (tx, ty), max(1, impact_r - 16), 1)
                _NS_rakzhan._aacircle(surface, (*_NS_rakzhan.PALETTE["fire_shine"], impact_alpha),
                                      (tx, ty), max(1, impact_r // 3))
                pygame.draw.rect(surface, _NS_rakzhan.PALETTE["white"], (tx - 1, ty - 1, 2, 2))
                # Radial burst rays.
                for i in range(14):
                    angle_s = i * math.pi / 7
                    ex = tx + int(math.cos(angle_s) * impact_r)
                    ey = ty + int(math.sin(angle_s) * impact_r * 0.7)
                    pygame.draw.line(surface, (*_NS_rakzhan.PALETTE["fire_hot"], impact_alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface, (*_NS_rakzhan.PALETTE["fire_shine"], impact_alpha),
                                     (ex, ey, 2, 2))
                # Damage number float up (visual only).
                # Skip for simplicity.
        else:
            # Aftermath: embers rising at target.
            t = (progress - 0.75) / 0.25
            for i in range(12):
                rise_t = (phase * 0.7 + i * 0.08) % 1.0
                rx = tx + int(math.sin(phase + i) * 20)
                ry = ty - int(rise_t * 30)
                alpha = _NS_rakzhan._alpha(220 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    pygame.draw.rect(surface, (*_NS_rakzhan.PALETTE["fire_mid"], alpha),
                                     (rx, ry, 2, 2))
                    pygame.draw.rect(surface, (*_NS_rakzhan.PALETTE["fire_hot"], alpha),
                                     (rx, ry, 1, 1))
                    pygame.draw.rect(surface, (*_NS_rakzhan.PALETTE["fire_shine"], alpha),
                                     (rx, ry - 1, 1, 1))



# ====================================================================
# SIRAKZAN (BLADE ROLLING DUELIST) - Mini Boss
# ====================================================================

class _NS_sirakzan:
    """Namespace sirakzan - pangolin swashbuckler mini boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Scale armor (purple-magenta pangolin scales)
        "scale_darkest": (25, 10, 30),
        "scale_dark": (60, 25, 65),
        "scale_mid": (115, 55, 115),
        "scale_light": (180, 105, 175),
        "scale_shine": (230, 175, 220),
        # Cape (crimson red)
        "cape_darkest": (35, 8, 12),
        "cape_dark": (95, 20, 25),
        "cape_mid": (175, 40, 45),
        "cape_light": (225, 85, 75),
        "cape_shine": (255, 145, 120),
        # Gold trim
        "gold_darkest": (55, 30, 8),
        "gold_dark": (110, 75, 20),
        "gold_mid": (200, 150, 45),
        "gold_light": (245, 210, 95),
        "gold_shine": (255, 245, 180),
        # Fur (brown belly)
        "fur_dark": (55, 35, 20),
        "fur_mid": (110, 75, 45),
        "fur_light": (170, 130, 90),
        # Snout (soft peach)
        "snout_dark": (95, 55, 40),
        "snout_mid": (170, 115, 90),
        "snout_light": (220, 175, 145),
        # Steel rapier
        "steel_darkest": (25, 30, 45),
        "steel_dark": (65, 75, 100),
        "steel_mid": (150, 165, 195),
        "steel_light": (215, 225, 245),
        "steel_shine": (250, 252, 255),
        # Blue eyes
        "eye_socket": (5, 8, 15),
        "eye_dark": (25, 55, 110),
        "eye_mid": (70, 145, 230),
        "eye_light": (170, 220, 255),
        "eye_glow": (230, 245, 255),
        # Feather (bright red)
        "feather_dark": (95, 15, 20),
        "feather_mid": (200, 40, 45),
        "feather_light": (255, 100, 90),
        # Sparkle FX (golden magic)
        "spark_dark": (110, 75, 15),
        "spark_mid": (240, 175, 40),
        "spark_light": (255, 220, 130),
        "spark_shine": (255, 250, 210),
        # Lucky charm green (clover)
        "clover_dark": (25, 75, 30),
        "clover_mid": (75, 175, 65),
        "clover_light": (155, 235, 130),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_sirakzan._clamp(color)
        if _NS_sirakzan.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_sirakzan._clamp(color)
        if _NS_sirakzan.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_sirakzan._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    def _arm_elbow(shoulder, hand, bend=4, bend_up=False):
        sx, sy = shoulder
        hx, hy = hand
        mid_x = (sx + hx) / 2
        mid_y = (sy + hy) / 2
        dx = hx - sx
        dy = hy - sy
        length = max(1.0, math.sqrt(dx * dx + dy * dy))
        perp_x = -dy / length
        perp_y = dx / length
        if bend_up:
            if perp_y > 0:
                perp_x = -perp_x
                perp_y = -perp_y
        else:
            if perp_y < 0:
                perp_x = -perp_x
                perp_y = -perp_y
        return (int(mid_x + perp_x * bend), int(mid_y + perp_y * bend))
    def _rapier_tip_position(boss, x, y):
        """Position of rapier tip (for basic attack FX)."""
        facing = boss.direction
        active = getattr(boss, "_sk_attack_active", False)
        progress = getattr(boss, "_sk_attack_progress", 0.0)
        if active:
            if progress < 0.35:
                t = progress / 0.35
                tx = x + facing * int(20 - t * 12)
                ty = y - 8
            elif progress < 0.55:
                t = (progress - 0.35) / 0.2
                tx = x + facing * int(8 + t * 38)
                ty = y - 8
            elif progress < 0.75:
                tx = x + facing * 46
                ty = y - 8
            else:
                t = (progress - 0.75) / 0.25
                tx = x + facing * int(46 - t * 26)
                ty = y - 8
        else:
            tx = x + facing * 20
            ty = y - 8
        return tx, ty
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_sirakzan(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_sirakzan._update_attack_anim(boss)
        attack_progress = getattr(boss, "_sk_attack_progress", 0.0)
        attacking = (
            getattr(boss, "_sk_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )
        # Ambient FX.
        _NS_sirakzan._draw_purple_aura(surface, x, y, pulse)
        _NS_sirakzan._draw_ground_ring(surface, x, y + 50, pulse, active_skill)
        # Skill ground FX.
        if active_skill == "e":
            _NS_sirakzan._draw_luckyshot_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_sirakzan._draw_shieldcrash_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_sirakzan._draw_rollingthunder_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating body.
        float_bob = math.sin(pulse * 0.7) * 4
        body_y = y + int(float_bob)
        # Body pose - determine which pose to draw.
        if active_skill == "w":
            # Ball form rolling to target.
            _NS_sirakzan._draw_ball_form(surface, boss, x, body_y,
                                          skill_timer, pulse, "shieldcrash")
        elif active_skill == "r":
            # Ball form rolling chain.
            _NS_sirakzan._draw_ball_form(surface, boss, x, body_y,
                                          skill_timer, pulse, "rollingthunder")
        elif active_skill == "q":
            # Lunge with rapier.
            _NS_sirakzan._draw_body_lunge(surface, boss, x, body_y,
                                           skill_timer, pulse)
        elif active_skill == "e":
            # Aim + fire lucky charm.
            _NS_sirakzan._draw_body_aim(surface, boss, x, body_y,
                                         skill_timer, pulse)
        elif attacking:
            _NS_sirakzan._draw_body_attack(surface, boss, x, body_y)
        else:
            _NS_sirakzan._draw_body_idle(surface, boss, x, body_y)
        # Foreground FX (projectiles).
        if active_skill == "q":
            _NS_sirakzan._draw_swashbuckle_fx(surface, boss, x, body_y,
                                                skill_timer, pulse)
        elif active_skill == "e":
            _NS_sirakzan._draw_luckyshot_projectile(surface, boss, x, body_y,
                                                     skill_timer, pulse)
        else:
            if attacking and attack_progress > 0 and active_skill is None:
                _NS_sirakzan._draw_basic_slash_fx(surface, boss, x, body_y)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_sk_attack_active", False))
        if not active and timer >= cooldown - 2:
            boss._sk_attack_active = True
            boss._sk_attack_frame = 0
            active = True
        elif active:
            boss._sk_attack_frame = int(getattr(boss, "_sk_attack_frame", 0)) + 1
            if boss._sk_attack_frame >= cooldown:
                boss._sk_attack_active = False
                boss._sk_attack_frame = 0
                active = False
        boss._sk_previous_timer = timer
        boss._sk_attack_progress = (
            min(1.0, getattr(boss, "_sk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # BODY POSES
    # ============================================================
    def _draw_body_idle(surface, boss, cx, cy):
        _NS_sirakzan._draw_float_shadow(surface, cx, cy + 52, boss.pulse)
        _NS_sirakzan._draw_floating_sparkles(surface, cx, cy + 40, boss.pulse)
        _NS_sirakzan._draw_body(surface, boss, cx, cy, "idle", 0)
    def _draw_body_attack(surface, boss, cx, cy):
        progress = getattr(boss, "_sk_attack_progress", 0.0)
        _NS_sirakzan._draw_float_shadow(surface, cx, cy + 52, boss.pulse)
        _NS_sirakzan._draw_floating_sparkles(surface, cx, cy + 40, boss.pulse,
                                              intense=True)
        _NS_sirakzan._draw_body(surface, boss, cx, cy, "attack", progress)
    def _draw_body_lunge(surface, boss, cx, cy, timer, phase):
        """Q Swashbuckle: lunging pose with rapier extended."""
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_sirakzan._draw_float_shadow(surface, cx, cy + 52, phase)
        _NS_sirakzan._draw_floating_sparkles(surface, cx, cy + 40, phase, intense=True)
        _NS_sirakzan._draw_body(surface, boss, cx, cy, "lunge", progress)
    def _draw_body_aim(surface, boss, cx, cy, timer, phase):
        """E Lucky Shot: pointing rapier as gun."""
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_sirakzan._draw_float_shadow(surface, cx, cy + 52, phase)
        _NS_sirakzan._draw_floating_sparkles(surface, cx, cy + 40, phase, intense=True)
        _NS_sirakzan._draw_body(surface, boss, cx, cy, "aim", progress)
    # ============================================================
    # MAIN BODY (humanoid form)
    # ============================================================
    def _draw_body(surface, boss, cx, cy, action, progress):
        facing = boss.direction
        phase = boss.pulse
        # Cape backdrop.
        _NS_sirakzan._draw_cape(surface, cx, cy, facing, phase)
        # Legs.
        _NS_sirakzan._draw_legs(surface, cx, cy, facing, phase, action, progress)
        # Torso (with scale armor).
        _NS_sirakzan._draw_torso(surface, cx, cy, facing, phase)
        # Tail behind.
        _NS_sirakzan._draw_tail(surface, cx, cy, facing, phase)
        # Arms with rapier.
        _NS_sirakzan._draw_arms(surface, cx, cy, facing, phase, action, progress)
        # Head with helm.
        _NS_sirakzan._draw_head(surface, cx, cy - 20, facing, phase, action)
    def _draw_cape(surface, cx, cy, facing, phase):
        """Red crimson cape flowing behind."""
        sway = math.sin(phase * 0.6) * 3
        cape_pts = [
            (cx - facing * 6, cy - 14),
            (cx - facing * 14 + int(sway), cy - 4),
            (cx - facing * 18 + int(sway), cy + 8),
            (cx - facing * 20 + int(sway * 1.2), cy + 20),
            (cx - facing * 16 + int(sway), cy + 30),
            (cx - facing * 8, cy + 34),
            (cx + facing * 2, cy + 28),
            (cx + facing * 4, cy + 8),
            (cx + facing * 2, cy - 10),
        ]
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 3) for p in cape_pts])
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["cape_darkest"], cape_pts)
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["cape_dark"], [
            (cx - facing * 5, cy - 13),
            (cx - facing * 12 + int(sway), cy - 4),
            (cx - facing * 16 + int(sway), cy + 8),
            (cx - facing * 18 + int(sway * 1.2), cy + 18),
            (cx - facing * 14 + int(sway), cy + 28),
            (cx - facing * 6, cy + 30),
            (cx + facing * 1, cy + 24),
            (cx + facing * 3, cy + 8),
            (cx + facing * 1, cy - 8),
        ])
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["cape_mid"], [
            (cx - facing * 4, cy - 10),
            (cx - facing * 10 + int(sway * 0.8), cy - 2),
            (cx - facing * 12 + int(sway), cy + 10),
            (cx - facing * 10 + int(sway), cy + 22),
            (cx - facing * 4, cy + 24),
            (cx + facing * 1, cy + 12),
        ])
        # Gold trim edge.
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["gold_mid"],
                         (cx - facing * 6, cy - 14),
                         (cx - facing * 14 + int(sway), cy - 4), 1)
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["gold_light"],
                         (cx - facing * 14 + int(sway), cy - 4),
                         (cx - facing * 18 + int(sway), cy + 8), 1)
    def _draw_tail(surface, cx, cy, facing, phase):
        """Pangolin tail with scales."""
        base_x = cx - facing * 4
        base_y = cy + 12
        segments = 5
        prev = (base_x, base_y)
        for i in range(1, segments + 1):
            t = i / segments
            wave = math.sin(phase * 1.2 + t * math.pi) * 3
            x_off = int(-facing * (6 + t * 10))
            y_off = int(4 + t * 12 + wave)
            end = (base_x + x_off, base_y + y_off)
            thickness = max(2, 6 - i)
            _NS_sirakzan._aaline(surface, _NS_sirakzan.PALETTE["shadow_deep"],
                                 (prev[0] + 1, prev[1] + 1),
                                 (end[0] + 1, end[1] + 1), thickness + 1)
            _NS_sirakzan._aaline(surface, _NS_sirakzan.PALETTE["scale_darkest"],
                                 prev, end, thickness)
            _NS_sirakzan._aaline(surface, _NS_sirakzan.PALETTE["scale_dark"],
                                 prev, end, max(1, thickness - 1))
            _NS_sirakzan._aaline(surface, _NS_sirakzan.PALETTE["scale_mid"],
                                 (prev[0], prev[1] - 1),
                                 (end[0], end[1] - 1),
                                 max(1, thickness - 3))
            # Scale ridge.
            _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["scale_light"], [
                (prev[0], prev[1] - thickness // 2),
                (int((prev[0] + end[0]) / 2), int((prev[1] + end[1]) / 2 - thickness // 2)),
                (end[0], end[1] - thickness // 2),
            ])
            prev = end
        # Tail tip highlight.
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["scale_shine"],
                         (prev[0], prev[1] - 1, 1, 1))
    def _draw_legs(surface, cx, cy, facing, phase, action, progress):
        """Two legs with fur pants."""
        # Lunge = front leg forward, back leg extended.
        lunge_offset = 0
        if action == "lunge":
            if progress < 0.4:
                lunge_offset = int(progress / 0.4 * 6)
            elif progress < 0.7:
                lunge_offset = 6
            else:
                lunge_offset = int(6 * (1 - (progress - 0.7) / 0.3))
        for i, side in enumerate((-1, 1)):
            forward = (side == facing)
            leg_x_base = cx + side * 6
            if forward:
                leg_x = cx + facing * (6 + lunge_offset)
            else:
                leg_x = cx - facing * 6
            # Thigh (fur).
            thigh_pts = [
                (leg_x - 4, cy + 8),
                (leg_x + 4, cy + 8),
                (leg_x + 5, cy + 18),
                (leg_x + 3, cy + 24),
                (leg_x - 3, cy + 24),
                (leg_x - 5, cy + 18),
            ]
            _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["shadow_deep"],
                               [(p[0] + 1, p[1] + 2) for p in thigh_pts])
            _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["fur_dark"], thigh_pts)
            _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["fur_mid"], [
                (leg_x - 3, cy + 9),
                (leg_x + 3, cy + 9),
                (leg_x + 4, cy + 18),
                (leg_x + 2, cy + 23),
                (leg_x - 2, cy + 23),
                (leg_x - 4, cy + 18),
            ])
            pygame.draw.line(surface, _NS_sirakzan.PALETTE["fur_light"],
                             (leg_x - 2, cy + 11),
                             (leg_x - 2, cy + 22), 1)
            # Boot (dark leather with gold trim).
            boot_pts = [
                (leg_x - 5, cy + 24),
                (leg_x + 5, cy + 24),
                (leg_x + 6, cy + 30),
                (leg_x + 4, cy + 34),
                (leg_x - 4, cy + 34),
                (leg_x - 6, cy + 30),
            ]
            _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["shadow_deep"],
                               [(p[0] + 1, p[1] + 2) for p in boot_pts])
            _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["scale_darkest"], boot_pts)
            _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["scale_dark"], [
                (leg_x - 4, cy + 25),
                (leg_x + 4, cy + 25),
                (leg_x + 5, cy + 30),
                (leg_x + 3, cy + 33),
                (leg_x - 3, cy + 33),
                (leg_x - 5, cy + 30),
            ])
            _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["scale_mid"], [
                (leg_x - 2, cy + 27),
                (leg_x + 2, cy + 27),
                (leg_x + 3, cy + 30),
                (leg_x + 1, cy + 32),
                (leg_x - 1, cy + 32),
                (leg_x - 3, cy + 30),
            ])
            # Gold trim on boot top.
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["gold_dark"],
                             (leg_x - 5, cy + 24, 10, 2))
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["gold_mid"],
                             (leg_x - 4, cy + 24, 8, 1))
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["gold_light"],
                             (leg_x - 3, cy + 24, 6, 1))
    def _draw_torso(surface, cx, cy, facing, phase):
        """Torso covered in purple scale armor."""
        breath = math.sin(phase * 0.6) * 1
        torso_pts = [
            (cx - 10, cy - 14),
            (cx - 12, cy - 6),
            (cx - 10, cy + 4),
            (cx - 6, cy + 10),
            (cx + 6, cy + 10),
            (cx + 10, cy + 4),
            (cx + 12, cy - 6),
            (cx + 10, cy - 14),
            (cx + 4, cy - 18),
            (cx - 4, cy - 18),
        ]
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in torso_pts])
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["scale_darkest"], torso_pts)
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["scale_dark"], [
            (cx - 9, cy - 13),
            (cx - 11, cy - 6),
            (cx - 9, cy + 3),
            (cx - 5, cy + 9),
            (cx + 5, cy + 9),
            (cx + 9, cy + 3),
            (cx + 11, cy - 6),
            (cx + 9, cy - 13),
            (cx + 3, cy - 17),
            (cx - 3, cy - 17),
        ])
        # SCALE PATTERN (overlapping scales).
        for row in range(4):
            y_row = cy - 12 + row * 5
            for col_offset in range(-8, 9, 4):
                offset_x = (row % 2) * 2
                scale_x = cx + col_offset + offset_x
                if abs(col_offset + offset_x) > 8:
                    continue
                # Scale shape (overlapping arc).
                _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["scale_mid"], [
                    (scale_x - 2, y_row),
                    (scale_x, y_row - 2),
                    (scale_x + 2, y_row),
                    (scale_x + 2, y_row + 2),
                    (scale_x - 2, y_row + 2),
                ])
                _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["scale_light"], [
                    (scale_x - 1, y_row),
                    (scale_x, y_row - 1),
                    (scale_x + 1, y_row),
                    (scale_x + 1, y_row + 1),
                    (scale_x - 1, y_row + 1),
                ])
                pygame.draw.rect(surface, _NS_sirakzan.PALETTE["scale_shine"],
                                 (scale_x, y_row, 1, 1))
        # Gold belt.
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["gold_darkest"],
                         (cx - 10, cy + 6, 20, 5))
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["gold_dark"],
                         (cx - 9, cy + 6, 18, 4))
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["gold_mid"],
                         (cx - 8, cy + 7, 16, 3))
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["gold_light"],
                         (cx - 7, cy + 8, 14, 1))
        # Belt buckle.
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["gold_darkest"],
                         (cx - 3, cy + 6, 6, 5))
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["gold_light"],
                         (cx - 2, cy + 7, 4, 2))
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["gold_shine"],
                         (cx - 1, cy + 8, 2, 1))
        # Gold shoulder pauldrons.
        for side in (-1, 1):
            base_x = cx + side * 10
            paul_pts = [
                (base_x - side, cy - 16),
                (base_x + side * 4, cy - 15),
                (base_x + side * 5, cy - 9),
                (base_x + side * 2, cy - 8),
                (base_x - side, cy - 10),
            ]
            _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["gold_darkest"], paul_pts)
            _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["gold_dark"], [
                (base_x, cy - 15),
                (base_x + side * 3, cy - 14),
                (base_x + side * 4, cy - 10),
                (base_x + side, cy - 9),
            ])
            _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["gold_mid"], [
                (base_x + side, cy - 14),
                (base_x + side * 3, cy - 13),
                (base_x + side * 3, cy - 11),
                (base_x + side * 1, cy - 10),
            ])
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["gold_light"],
                             (base_x + side * 2, cy - 13, 1, 1))
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["gold_shine"],
                             (base_x + side * 2, cy - 13, 1, 1))
    def _draw_arms(surface, cx, cy, facing, phase, action, progress):
        """Two arms. Front arm holds rapier."""
        # Shoulder positions.
        front_sh = (cx + facing * 10, cy - 10)
        back_sh = (cx - facing * 10, cy - 10)
        # Determine front hand position based on action.
        if action == "attack":
            # Basic slash: quick horizontal slash.
            if progress < 0.35:
                # Wind back.
                t = progress / 0.35
                front_hand_x = cx + facing * int(14 - t * 8)
                front_hand_y = cy - 4 - int(t * 4)
            elif progress < 0.55:
                # Slash forward.
                t = (progress - 0.35) / 0.2
                front_hand_x = cx + facing * int(6 + t * 24)
                front_hand_y = cy - 8 + int(t * 6)
            elif progress < 0.75:
                # Hold.
                front_hand_x = cx + facing * 30
                front_hand_y = cy - 2
            else:
                # Return.
                t = (progress - 0.75) / 0.25
                front_hand_x = cx + facing * int(30 - t * 16)
                front_hand_y = cy - 2 - int(t * 2)
        elif action == "lunge":
            # Q Swashbuckle: dramatic lunge extending rapier fully.
            if progress < 0.3:
                t = progress / 0.3
                front_hand_x = cx + facing * int(14 - t * 8)
                front_hand_y = cy - 4 - int(t * 6)
            elif progress < 0.6:
                t = (progress - 0.3) / 0.3
                front_hand_x = cx + facing * int(6 + t * 32)
                front_hand_y = cy - 10 + int(t * 4)
            elif progress < 0.8:
                front_hand_x = cx + facing * 38
                front_hand_y = cy - 6
            else:
                t = (progress - 0.8) / 0.2
                front_hand_x = cx + facing * int(38 - t * 24)
                front_hand_y = cy - 6 + int(t * 2)
        elif action == "aim":
            # E Lucky Shot: pointing rapier steady forward.
            if progress < 0.3:
                t = progress / 0.3
                front_hand_x = cx + facing * int(14 + t * 12)
                front_hand_y = cy - 6 - int(t * 4)
            elif progress < 0.7:
                front_hand_x = cx + facing * 26
                front_hand_y = cy - 10
            else:
                t = (progress - 0.7) / 0.3
                front_hand_x = cx + facing * int(26 - t * 12)
                front_hand_y = cy - 10 + int(t * 4)
        else:
            # Idle: rapier at ready pose.
            idle_sway = math.sin(phase * 0.8) * 1
            front_hand_x = cx + facing * 14
            front_hand_y = cy - 4 + int(idle_sway)
        # Back hand: holds hilt of another item / relaxed.
        back_hand_x = cx - facing * 8
        back_hand_y = cy + 2
        # Compute elbows.
        front_elbow = _NS_sirakzan._arm_elbow(front_sh, (front_hand_x, front_hand_y), bend=4)
        back_elbow = _NS_sirakzan._arm_elbow(back_sh, (back_hand_x, back_hand_y), bend=3)
        # Draw back arm first.
        _NS_sirakzan._draw_arm_segment(surface, back_sh, back_elbow,
                                        (back_hand_x, back_hand_y),
                                        show_glove=True)
        # Draw front arm.
        _NS_sirakzan._draw_arm_segment(surface, front_sh, front_elbow,
                                        (front_hand_x, front_hand_y),
                                        show_glove=True)
        # DRAW RAPIER in front hand.
        _NS_sirakzan._draw_rapier(surface, front_hand_x, front_hand_y,
                                   front_elbow, facing, phase, action, progress)
    def _draw_arm_segment(surface, shoulder, elbow, hand, show_glove=True):
        """Draw arm with scale sleeve + glove."""
        sx, sy = shoulder
        ex, ey = elbow
        hx, hy = hand
        # Upper arm (scale sleeve).
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["shadow_deep"],
                         (sx + 1, sy + 1), (ex + 1, ey + 1), 5)
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["scale_darkest"],
                         (sx, sy), (ex, ey), 4)
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["scale_dark"],
                         (sx, sy), (ex, ey), 3)
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["scale_mid"],
                         (sx, sy - 1), (ex, ey - 1), 1)
        # Forearm.
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["shadow_deep"],
                         (ex + 1, ey + 1), (hx + 1, hy + 1), 5)
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["scale_darkest"],
                         (ex, ey), (hx, hy), 4)
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["scale_dark"],
                         (ex, ey), (hx, hy), 2)
        # Glove (gold bracer at wrist).
        if show_glove:
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["gold_dark"],
                             (hx - 2, hy - 2, 4, 4))
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["gold_mid"],
                             (hx - 1, hy - 2, 3, 3))
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["gold_light"],
                             (hx - 1, hy - 1, 2, 1))
    def _draw_rapier(surface, hx, hy, elbow, facing, phase, action, progress):
        """Thin fencing rapier extending from hand."""
        # Compute rapier direction (from elbow → hand → extended forward).
        # For simplicity: rapier points in facing direction with slight tilt.
        # Base of rapier at hand.
        base_x, base_y = hx, hy
        # Rapier angle: horizontal forward, slight upward tilt in idle.
        angle = 0
        if action == "aim":
            angle = -0.1  # slight up
        elif action == "lunge":
            angle = -0.05
        else:
            angle = math.sin(phase * 0.8) * 0.05  # small idle wobble
        blade_len = 24
        tip_x = base_x + int(math.cos(angle) * blade_len) * facing
        tip_y = base_y + int(math.sin(angle) * blade_len)
        # Cross-guard (small hilt).
        cg_size = 4
        perp_x = -math.sin(angle)
        perp_y = math.cos(angle)
        cg_a = (base_x + int(perp_x * cg_size),
                base_y + int(perp_y * cg_size))
        cg_b = (base_x - int(perp_x * cg_size),
                base_y - int(perp_y * cg_size))
        # Cross-guard shadow.
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["shadow_deep"],
                         (cg_a[0] + 1, cg_a[1] + 1),
                         (cg_b[0] + 1, cg_b[1] + 1), 3)
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["gold_dark"],
                         cg_a, cg_b, 3)
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["gold_mid"],
                         cg_a, cg_b, 2)
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["gold_light"],
                         cg_a, cg_b, 1)
        # Center guard sphere.
        _NS_sirakzan._aacircle(surface, _NS_sirakzan.PALETTE["gold_dark"],
                               (base_x, base_y), 3)
        _NS_sirakzan._aacircle(surface, _NS_sirakzan.PALETTE["gold_mid"],
                               (base_x, base_y), 2)
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["gold_shine"],
                         (base_x, base_y, 1, 1))
        # BLADE (thin steel line).
        # Shadow.
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["shadow_deep"],
                         (base_x + 1, base_y + 1), (tip_x + 1, tip_y + 1), 3)
        # Steel body (dark outer).
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["steel_darkest"],
                         (base_x, base_y), (tip_x, tip_y), 3)
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["steel_dark"],
                         (base_x, base_y), (tip_x, tip_y), 2)
        # Shiny edge.
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["steel_mid"],
                         (base_x, base_y - 1), (tip_x, tip_y - 1), 1)
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["steel_light"],
                         (base_x + facing * 2, base_y - 1),
                         (tip_x - facing * 2, tip_y - 1), 1)
        # Sharp tip.
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["steel_shine"],
                         (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["white"],
                         (tip_x, tip_y, 1, 1))
        # Blade shine sparkle (during idle).
        if action == "idle":
            sparkle_t = (phase * 0.5) % 1.0
            spark_pos_t = sparkle_t
            spx = int(base_x + (tip_x - base_x) * spark_pos_t)
            spy = int(base_y + (tip_y - base_y) * spark_pos_t)
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["steel_shine"], (spx, spy - 1, 1, 1))
    def _draw_head(surface, cx, cy, facing, phase, action):
        """Pangolin head with helm."""
        # Head shape (rodent-like, elongated snout).
        head_pts = [
            (cx - 6, cy),
            (cx - 8, cy - 4),
            (cx - 7, cy - 10),
            (cx - 3, cy - 13),
            (cx + 3, cy - 13),
            (cx + 7, cy - 10),
            (cx + 9, cy - 4),
            (cx + 10, cy),
            (cx + 12, cy + 3),
            (cx + 14, cy + 6),
            (cx + 12, cy + 8),
            (cx + 6, cy + 8),
            (cx + 2, cy + 10),
            (cx - 4, cy + 8),
            (cx - 6, cy + 4),
        ]
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in head_pts])
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["scale_darkest"], head_pts)
        # Facial fur (bottom of face).
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["fur_dark"], [
            (cx - 4, cy + 4),
            (cx + 12, cy + 5),
            (cx + 14, cy + 7),
            (cx + 12, cy + 8),
            (cx + 6, cy + 8),
            (cx + 2, cy + 10),
            (cx - 4, cy + 8),
            (cx - 6, cy + 4),
        ])
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["fur_mid"], [
            (cx - 3, cy + 5),
            (cx + 10, cy + 5),
            (cx + 12, cy + 7),
            (cx + 5, cy + 7),
            (cx + 1, cy + 9),
            (cx - 3, cy + 7),
        ])
        # SNOUT (elongated).
        snout_pts = [
            (cx + 6, cy + 2),
            (cx + 14, cy + 3),
            (cx + 16, cy + 5),
            (cx + 15, cy + 7),
            (cx + 10, cy + 8),
            (cx + 6, cy + 7),
        ]
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["snout_dark"], snout_pts)
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["snout_mid"], [
            (cx + 7, cy + 3),
            (cx + 13, cy + 4),
            (cx + 15, cy + 5),
            (cx + 13, cy + 7),
            (cx + 8, cy + 7),
        ])
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["snout_light"],
                         (cx + 10, cy + 4, 2, 1))
        # Nose (small black tip).
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["shadow_deep"],
                         (cx + 14, cy + 4, 2, 2))
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["scale_darkest"],
                         (cx + 15, cy + 5, 1, 1))
        # MUSTACHE (swashbuckler style).
        for side in (-1, 1):
            m_start = (cx + 10 * facing, cy + 6)
            m_end = (cx + 15 * facing + side * 2, cy + 5 + side * -1)
            pygame.draw.line(surface, _NS_sirakzan.PALETTE["fur_dark"],
                             m_start, m_end, 2)
            pygame.draw.line(surface, _NS_sirakzan.PALETTE["fur_mid"],
                             m_start, m_end, 1)
        # BLUE EYES.
        _NS_sirakzan._draw_eyes(surface, cx, cy, facing, phase, action)
        # HELM.
        _NS_sirakzan._draw_helm(surface, cx, cy - 8, facing, phase)
    def _draw_eyes(surface, cx, cy, facing, phase, action):
        """Blue glowing pangolin eyes."""
        pulse = math.sin(phase * 2.5) * 0.2 + 0.8
        for side in (-1, 1):
            # Position eyes on facing side more (since snout points forward).
            ex_offset = 2 * side * facing if side != facing else 4 * facing
            ex = cx + ex_offset
            ey = cy - 3
            # Eye socket.
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["eye_socket"],
                             (ex - 1, ey - 1, 3, 3))
            # Glow.
            for r in range(4, 0, -1):
                alpha = _NS_sirakzan._alpha(100 * (4 - r) / 4 * pulse)
                _NS_sirakzan._aacircle(surface,
                                       (*_NS_sirakzan.PALETTE["eye_mid"], alpha),
                                       (ex, ey), r)
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["eye_dark"], (ex - 1, ey, 3, 1))
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["eye_mid"], (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["eye_light"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["eye_glow"], (ex, ey, 1, 1))
    def _draw_helm(surface, cx, cy, facing, phase):
        """Purple-blue helm with gold trim and red feather."""
        sway = math.sin(phase * 0.6) * 1
        # Base helm cap.
        helm_pts = [
            (cx - 8, cy),
            (cx - 9, cy - 4),
            (cx - 6, cy - 8),
            (cx, cy - 10),
            (cx + 6, cy - 8),
            (cx + 9, cy - 4),
            (cx + 8, cy),
        ]
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in helm_pts])
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["scale_darkest"], helm_pts)
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["scale_dark"], [
            (cx - 7, cy),
            (cx - 8, cy - 4),
            (cx - 5, cy - 7),
            (cx, cy - 9),
            (cx + 5, cy - 7),
            (cx + 8, cy - 4),
            (cx + 7, cy),
        ])
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["scale_mid"], [
            (cx - 4, cy - 2),
            (cx - 5, cy - 5),
            (cx - 2, cy - 7),
            (cx + 2, cy - 7),
            (cx + 5, cy - 5),
            (cx + 4, cy - 2),
        ])
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["scale_light"], (cx - 1, cy - 6, 3, 1))
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["scale_shine"], (cx, cy - 6, 1, 1))
        # Gold trim around helm base.
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["gold_dark"],
                         (cx - 8, cy), (cx + 8, cy), 1)
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["gold_mid"],
                         (cx - 7, cy), (cx + 7, cy), 1)
        # Front trim (nose guard down).
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["gold_dark"],
                         (cx, cy - 8), (cx, cy + 4), 2)
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["gold_mid"],
                         (cx, cy - 8), (cx, cy + 4), 1)
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["gold_light"], (cx, cy - 7, 1, 1))
        # Center gold gem/emblem.
        _NS_sirakzan._aacircle(surface, _NS_sirakzan.PALETTE["gold_dark"], (cx, cy - 3), 2)
        _NS_sirakzan._aacircle(surface, _NS_sirakzan.PALETTE["gold_mid"], (cx, cy - 3), 1)
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["gold_shine"], (cx, cy - 3, 1, 1))
        # RED FEATHER PLUME on top.
        feather_pts = [
            (cx - 2, cy - 10),
            (cx - 5 + int(sway), cy - 15),
            (cx - 6 + int(sway * 1.2), cy - 22),
            (cx - 3 + int(sway), cy - 26),
            (cx + int(sway * 0.5), cy - 24),
            (cx + 2, cy - 20),
            (cx + 3, cy - 12),
            (cx + 1, cy - 10),
        ]
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 1) for p in feather_pts])
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["feather_dark"], feather_pts)
        _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["feather_mid"], [
            (cx - 1, cy - 11),
            (cx - 4 + int(sway), cy - 15),
            (cx - 5 + int(sway * 1.2), cy - 21),
            (cx - 2 + int(sway), cy - 25),
            (cx + int(sway * 0.5), cy - 23),
            (cx + 1, cy - 18),
            (cx + 2, cy - 12),
        ])
        # Highlight strand.
        pygame.draw.line(surface, _NS_sirakzan.PALETTE["feather_light"],
                         (cx - 1 + int(sway), cy - 13),
                         (cx - 3 + int(sway), cy - 23), 1)
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["cape_shine"],
                         (cx - 3 + int(sway), cy - 25, 1, 1))
        # Ear/wing side flairs on helm.
        for side in (-1, 1):
            _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["gold_dark"], [
                (cx + side * 8, cy - 4),
                (cx + side * 11, cy - 6),
                (cx + side * 10, cy - 2),
                (cx + side * 8, cy - 2),
            ])
            _NS_sirakzan._poly(surface, _NS_sirakzan.PALETTE["gold_mid"], [
                (cx + side * 8, cy - 3),
                (cx + side * 10, cy - 5),
                (cx + side * 9, cy - 2),
            ])
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["gold_shine"],
                             (cx + side * 10, cy - 5, 1, 1))
    # ============================================================
    # BALL FORM (for skill W & R)
    # ============================================================
    def _draw_ball_form(surface, boss, cx, cy, timer, phase, skill_type):
        """Pangolin rolled into armored ball, rolling to target."""
        facing = boss.direction
        tx, ty = _NS_sirakzan._target_position(boss, cx, cy)
        if skill_type == "shieldcrash":
            duration = 60
            progress = max(0.0, min(1.0, 1 - timer / duration))
            # Roll from boss position to target.
            if progress < 0.15:
                # Curl up in place.
                t = progress / 0.15
                ball_x = cx
                ball_y = cy + int(t * 8)
                scale = 0.3 + t * 0.7
            elif progress < 0.75:
                # Rolling to target.
                t = (progress - 0.15) / 0.6
                # Arc trajectory.
                arc = math.sin(t * math.pi) * 20
                ball_x = int(cx + (tx - cx) * t)
                ball_y = int(cy + 8 + (ty - cy - 8) * t - arc)
                scale = 1.0
            elif progress < 0.9:
                # Impact + stay at target.
                ball_x = tx
                ball_y = ty
                scale = 1.0
            else:
                # Uncurl.
                t = (progress - 0.9) / 0.1
                ball_x = tx
                ball_y = ty
                scale = 1.0 - t * 0.7
            # Shadow.
            _NS_sirakzan._draw_float_shadow(surface, ball_x, ball_y + 20, phase)
            # Draw ball.
            _NS_sirakzan._draw_pangolin_ball(surface, ball_x, ball_y, phase, facing,
                                              scale=scale, spinning=True)
            # Trail (dust cloud behind rolling ball).
            if 0.15 < progress < 0.85:
                for i in range(6):
                    trail_t = max(0.0, progress - i * 0.05 - 0.15) / 0.6
                    if trail_t < 0 or trail_t > 1:
                        continue
                    arc_t = math.sin(trail_t * math.pi) * 20
                    tx_p = int(cx + (tx - cx) * trail_t)
                    ty_p = int(cy + 8 + (ty - cy - 8) * trail_t - arc_t)
                    alpha = _NS_sirakzan._alpha(200 - i * 30)
                    _NS_sirakzan._aacircle(surface,
                                           (*_NS_sirakzan.PALETTE["spark_dark"], alpha),
                                           (tx_p, ty_p + 8), max(1, 6 - i))
                    _NS_sirakzan._aacircle(surface,
                                           (*_NS_sirakzan.PALETTE["spark_mid"], alpha),
                                           (tx_p, ty_p + 8), max(1, 4 - i))
                    pygame.draw.rect(surface,
                                     (*_NS_sirakzan.PALETTE["spark_light"], alpha),
                                     (tx_p, ty_p + 8, 1, 1))
            # Impact burst.
            if 0.75 < progress < 0.9:
                imp_t = (progress - 0.75) / 0.15
                imp_r = int(15 + imp_t * 30)
                alpha = _NS_sirakzan._alpha(240 * (1 - imp_t))
                _NS_sirakzan._aacircle(surface, (*_NS_sirakzan.PALETTE["spark_dark"], alpha),
                                       (tx, ty), imp_r + 2, 3)
                _NS_sirakzan._aacircle(surface, (*_NS_sirakzan.PALETTE["spark_mid"], alpha),
                                       (tx, ty), imp_r, 2)
                _NS_sirakzan._aacircle(surface, (*_NS_sirakzan.PALETTE["spark_light"], alpha),
                                       (tx, ty), max(1, imp_r - 5), 2)
                _NS_sirakzan._aacircle(surface, (*_NS_sirakzan.PALETTE["spark_shine"], alpha),
                                       (tx, ty), max(1, imp_r - 10), 1)
                # Radial burst rays.
                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * imp_r)
                    ey = ty + int(math.sin(angle_s) * imp_r * 0.7)
                    pygame.draw.line(surface,
                                     (*_NS_sirakzan.PALETTE["spark_light"], alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_sirakzan.PALETTE["spark_shine"], alpha),
                                     (ex, ey, 2, 2))
        elif skill_type == "rollingthunder":
            duration = 110
            progress = max(0.0, min(1.0, 1 - timer / duration))
            # Rolling with multiple bounces to target.
            if progress < 0.1:
                # Curl.
                t = progress / 0.1
                ball_x = cx
                ball_y = cy + 8
                scale = 0.3 + t * 0.7
            elif progress < 0.9:
                # Bouncing chain to target.
                t = (progress - 0.1) / 0.8
                # Multiple bounces (3 bounces).
                bounce_count = 3
                bounce_t = (t * bounce_count) % 1.0
                arc = math.sin(bounce_t * math.pi) * 30
                ball_x = int(cx + (tx - cx) * t)
                ball_y = int(cy + 8 + (ty - cy - 8) * t - arc)
                scale = 1.1  # bigger for R skill
            else:
                t = (progress - 0.9) / 0.1
                ball_x = tx
                ball_y = ty
                scale = 1.1 - t * 0.7
            _NS_sirakzan._draw_float_shadow(surface, ball_x, ball_y + 22, phase)
            # Draw ball (bigger, more intense glow).
            _NS_sirakzan._draw_pangolin_ball(surface, ball_x, ball_y, phase, facing,
                                              scale=scale, spinning=True, glow_intense=True)
            # Bigger fire trail.
            if 0.1 < progress < 0.95:
                for i in range(10):
                    trail_t = max(0.0, ((progress - 0.1) / 0.8) - i * 0.04)
                    if trail_t < 0 or trail_t > 1:
                        continue
                    bounce_count = 3
                    bt = (trail_t * bounce_count) % 1.0
                    arc_t = math.sin(bt * math.pi) * 30
                    tx_p = int(cx + (tx - cx) * trail_t)
                    ty_p = int(cy + 8 + (ty - cy - 8) * trail_t - arc_t)
                    alpha = _NS_sirakzan._alpha(230 - i * 22)
                    # Bigger, hotter trail.
                    _NS_sirakzan._aacircle(surface,
                                           (*_NS_sirakzan.PALETTE["spark_dark"], alpha),
                                           (tx_p, ty_p), max(1, 8 - i))
                    _NS_sirakzan._aacircle(surface,
                                           (*_NS_sirakzan.PALETTE["spark_mid"], alpha),
                                           (tx_p, ty_p), max(1, 6 - i))
                    _NS_sirakzan._aacircle(surface,
                                           (*_NS_sirakzan.PALETTE["spark_light"], alpha),
                                           (tx_p, ty_p), max(1, 4 - i))
                    pygame.draw.rect(surface,
                                     (*_NS_sirakzan.PALETTE["spark_shine"], alpha),
                                     (tx_p, ty_p, 2, 2))
                    # Sparks scatter.
                    for s in range(2):
                        angle_s = trail_t * 5 + i + s
                        spark_r = 5 + i
                        spx = tx_p + int(math.cos(angle_s) * spark_r)
                        spy = ty_p + int(math.sin(angle_s) * spark_r)
                        pygame.draw.rect(surface,
                                         (*_NS_sirakzan.PALETTE["spark_shine"], alpha),
                                         (spx, spy, 1, 1))
            # Impact bursts at each bounce landing.
            bounce_count = 3
            for b in range(bounce_count):
                bounce_progress = (b + 1) / bounce_count
                if abs(progress - 0.1 - bounce_progress * 0.8) < 0.05:
                    bp = 1 - abs(progress - 0.1 - bounce_progress * 0.8) / 0.05
                    bimp_x = int(cx + (tx - cx) * bounce_progress)
                    bimp_y = int(cy + 8 + (ty - cy - 8) * bounce_progress)
                    bimp_r = int(15 * bp)
                    balpha = _NS_sirakzan._alpha(240 * bp)
                    _NS_sirakzan._aacircle(surface, (*_NS_sirakzan.PALETTE["spark_mid"], balpha),
                                           (bimp_x, bimp_y), bimp_r + 2, 2)
                    _NS_sirakzan._aacircle(surface, (*_NS_sirakzan.PALETTE["spark_light"], balpha),
                                           (bimp_x, bimp_y), bimp_r, 1)
    def _draw_pangolin_ball(surface, cx, cy, phase, facing, scale=1.0,
                             spinning=False, glow_intense=False):
        """Armored ball form of pangolin."""
        size = int(18 * scale)
        if size < 2:
            return
        # Rotation for spinning effect.
        rot = phase * 6 if spinning else 0
        # Glow aura.
        intensity = 1.6 if glow_intense else 1.0
        for r in range(size + 8, size - 2, -2):
            alpha = _NS_sirakzan._alpha(60 * (size + 8 - r) / 10 * intensity)
            _NS_sirakzan._aacircle(surface, (*_NS_sirakzan.PALETTE["spark_mid"], alpha),
                                   (cx, cy), r)
        # Ball body (shadow).
        _NS_sirakzan._aacircle(surface, _NS_sirakzan.PALETTE["shadow_deep"], (cx + 2, cy + 2), size)
        # Main dark body.
        _NS_sirakzan._aacircle(surface, _NS_sirakzan.PALETTE["scale_darkest"], (cx, cy), size)
        _NS_sirakzan._aacircle(surface, _NS_sirakzan.PALETTE["scale_dark"], (cx, cy), size - 1)
        _NS_sirakzan._aacircle(surface, _NS_sirakzan.PALETTE["scale_mid"], (cx - 1, cy - 1), size - 3)
        # Scale plates around ball (rotating).
        num_scales = 8
        for i in range(num_scales):
            angle = rot + i * math.pi * 2 / num_scales
            plate_r = size - 2
            px = cx + int(math.cos(angle) * plate_r * 0.8)
            py = cy + int(math.sin(angle) * plate_r * 0.8)
            # Scale plate (small arc segment).
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["scale_darkest"],
                             (px - 2, py - 2, 4, 4))
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["scale_dark"],
                             (px - 2, py - 2, 3, 3))
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["scale_light"],
                             (px - 1, py - 1, 2, 2))
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["scale_shine"],
                             (px - 1, py - 1, 1, 1))
        # Outer scale ridges (bigger spikes rotating).
        num_spikes = 6
        for i in range(num_spikes):
            angle = rot + i * math.pi * 2 / num_spikes
            spike_inner = size - 1
            spike_outer = size + 2
            ix = cx + int(math.cos(angle) * spike_inner)
            iy = cy + int(math.sin(angle) * spike_inner)
            ox = cx + int(math.cos(angle) * spike_outer)
            oy = cy + int(math.sin(angle) * spike_outer)
            pygame.draw.line(surface, _NS_sirakzan.PALETTE["scale_darkest"],
                             (ix, iy), (ox, oy), 3)
            pygame.draw.line(surface, _NS_sirakzan.PALETTE["scale_dark"],
                             (ix, iy), (ox, oy), 2)
            pygame.draw.line(surface, _NS_sirakzan.PALETTE["scale_light"],
                             (ix, iy), (ox, oy), 1)
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["scale_shine"],
                             (ox, oy, 1, 1))
        # Gold trim ring around ball.
        _NS_sirakzan._aacircle(surface, _NS_sirakzan.PALETTE["gold_dark"], (cx, cy), size - 4, 1)
        _NS_sirakzan._aacircle(surface, _NS_sirakzan.PALETTE["gold_mid"], (cx, cy), size - 5, 1)
        # Central highlight.
        _NS_sirakzan._aacircle(surface, _NS_sirakzan.PALETTE["scale_shine"],
                               (cx - size // 3, cy - size // 3), max(1, size // 4))
        pygame.draw.rect(surface, _NS_sirakzan.PALETTE["white"],
                         (cx - size // 3, cy - size // 3, 1, 1))
        # Fire/spark sparkles orbiting.
        for i in range(4):
            angle = phase * 4 + i * math.pi / 2
            spark_r = size + 4
            sx = cx + int(math.cos(angle) * spark_r)
            sy = cy + int(math.sin(angle) * spark_r)
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["spark_shine"], (sx, sy, 2, 2))
    # ============================================================
    # BASIC ATTACK: Rapier slash
    # ============================================================
    def _draw_basic_slash_fx(surface, boss, x, y):
        """Golden slash arc from rapier."""
        progress = getattr(boss, "_sk_attack_progress", 0.0)
        if progress < 0.4 or progress > 0.7:
            return
        facing = boss.direction
        # Origin at rapier tip.
        tip_x, tip_y = _NS_sirakzan._rapier_tip_position(boss, x, y)
        t = (progress - 0.4) / 0.3
        intensity = math.sin(t * math.pi)
        # Slash arc trail.
        base_x = x + facing * 12
        base_y = y - 4
        # Trail curve from bottom to top through slash.
        for i in range(8):
            trail_t = max(0.0, t - i * 0.08)
            if trail_t <= 0:
                continue
            angle_start = math.pi / 3
            angle_end = -math.pi / 3
            ang = angle_start + (angle_end - angle_start) * trail_t
            tx_p = base_x + int(math.cos(ang) * 30) * facing
            ty_p = base_y + int(math.sin(ang) * 20)
            alpha = _NS_sirakzan._alpha(230 * intensity * (1 - i * 0.1))
            if alpha <= 0:
                continue
            _NS_sirakzan._aacircle(surface,
                                   (*_NS_sirakzan.PALETTE["spark_dark"], alpha),
                                   (tx_p, ty_p), max(1, 4 - i // 2))
            _NS_sirakzan._aacircle(surface,
                                   (*_NS_sirakzan.PALETTE["spark_mid"], alpha),
                                   (tx_p, ty_p), max(1, 3 - i // 2))
            _NS_sirakzan._aacircle(surface,
                                   (*_NS_sirakzan.PALETTE["spark_light"], alpha),
                                   (tx_p, ty_p), max(1, 2 - i // 2))
            pygame.draw.rect(surface,
                             (*_NS_sirakzan.PALETTE["spark_shine"], alpha),
                             (tx_p, ty_p, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        breath = math.sin(phase * 0.7) * 0.15 + 0.85
        shadow = pygame.Surface((120, 24), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, int((10 - radius) * 18 * breath))
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 12 - radius,
                                 100 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (15, 5, 20, int(160 * breath)),
                            (10, 8, 100, 8))
        surface.blit(shadow, (x - 60, y - 12))
    def _draw_floating_sparkles(surface, cx, cy, phase, intense=False):
        strength = 1.6 if intense else 1.0
        for i in range(8):
            t = (phase * 0.4 + i * 0.13) % 1.0
            dx = cx + int(math.sin(phase + i * 0.7) * 25) - 12 + i * 3
            dy = cy - int(t * 20)
            alpha = _NS_sirakzan._alpha(200 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_sirakzan.PALETTE["spark_mid"], alpha),
                                 (dx, dy, 1, 1))
                pygame.draw.rect(surface, (*_NS_sirakzan.PALETTE["spark_shine"], alpha),
                                 (dx, dy - 1, 1, 1))
    def _draw_purple_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_sirakzan._alpha((85 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_sirakzan._aacircle(aura,
                                       (*_NS_sirakzan.PALETTE["scale_darkest"], alpha),
                                       (100, 90), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_sirakzan._alpha((55 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_sirakzan._aacircle(aura,
                                       (*_NS_sirakzan.PALETTE["scale_dark"], alpha),
                                       (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))
        # Golden sparkles orbiting.
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            radius = 42 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["spark_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["spark_shine"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_sirakzan.PALETTE["scale_darkest"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_sirakzan.PALETTE["scale_dark"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_sirakzan.PALETTE["scale_mid"], 180),
                            (25, 22, 120, 18), 1)
        # Runes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_sirakzan.PALETTE["spark_light"], 220),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.rect(ring, _NS_sirakzan.PALETTE["spark_shine"], (x2, y2, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_sirakzan.PALETTE["spark_shine"],
                                        _NS_sirakzan._alpha(160 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # SKILL Q: SWASHBUCKLE (multi-hit lunge with rapier)
    # ============================================================
    def _draw_swashbuckle_fx(surface, boss, x, y, timer, phase):
        """Multiple golden slash arcs along line to target."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_sirakzan._target_position(boss, x, y)
        # Rapier tip position during lunge.
        start_x = x + facing * 12
        start_y = y - 4
        if progress < 0.3:
            # Charge: sparkles around rapier tip.
            t = progress / 0.3
            tip_x = x + facing * int(24 - t * 6)
            tip_y = y - 8
            for i in range(6):
                angle = phase * 5 + i * math.pi / 3
                orbit_r = int(6 + (1 - t) * 6)
                sx = tip_x + int(math.cos(angle) * orbit_r)
                sy = tip_y + int(math.sin(angle) * orbit_r)
                pygame.draw.rect(surface, _NS_sirakzan.PALETTE["spark_shine"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_sirakzan.PALETTE["white"], (sx, sy, 1, 1))
        elif progress < 0.8:
            # LUNGE: multi-slash trail extending to target.
            t = (progress - 0.3) / 0.5
            intensity = math.sin(t * math.pi)
            # 3 slash arcs along the lunge path.
            for slash_i in range(3):
                slash_t = max(0.0, t - slash_i * 0.15)
                if slash_t <= 0:
                    continue
                slash_local_t = min(1.0, slash_t * 3)
                # Position along lunge path.
                pos_t = (slash_i + 0.5) / 3.0 * t
                cx_slash = int(start_x + (tx - start_x) * pos_t)
                cy_slash = int(start_y + (ty - start_y) * pos_t)
                # Draw slash arc (crescent).
                slash_alpha = _NS_sirakzan._alpha(240 * intensity)
                slash_r = 20
                for i in range(8):
                    trail_t = max(0.0, slash_local_t - i * 0.08)
                    ang = math.pi / 2.5 - trail_t * math.pi * 0.8
                    tx_p = cx_slash + int(math.cos(ang) * slash_r) * facing
                    ty_p = cy_slash + int(math.sin(ang) * slash_r * 0.7)
                    trail_alpha = _NS_sirakzan._alpha(slash_alpha * (1 - i * 0.1))
                    if trail_alpha > 0:
                        _NS_sirakzan._aacircle(surface,
                                               (*_NS_sirakzan.PALETTE["spark_dark"], trail_alpha),
                                               (tx_p, ty_p), max(1, 5 - i // 2))
                        _NS_sirakzan._aacircle(surface,
                                               (*_NS_sirakzan.PALETTE["spark_mid"], trail_alpha),
                                               (tx_p, ty_p), max(1, 4 - i // 2))
                        _NS_sirakzan._aacircle(surface,
                                               (*_NS_sirakzan.PALETTE["spark_light"], trail_alpha),
                                               (tx_p, ty_p), max(1, 2 - i // 2))
                        pygame.draw.rect(surface,
                                         (*_NS_sirakzan.PALETTE["spark_shine"], trail_alpha),
                                         (tx_p, ty_p, 1, 1))
            # Streak line from boss to current position.
            cur_end_x = int(start_x + (tx - start_x) * t)
            cur_end_y = int(start_y + (ty - start_y) * t)
            for width, color in [
                (4, _NS_sirakzan.PALETTE["spark_dark"]),
                (2, _NS_sirakzan.PALETTE["spark_mid"]),
                (1, _NS_sirakzan.PALETTE["spark_shine"]),
            ]:
                alpha = _NS_sirakzan._alpha(180 * intensity)
                pygame.draw.line(surface, (*color, alpha),
                                 (start_x, start_y), (cur_end_x, cur_end_y), width)
            # Final impact burst.
            if t > 0.7:
                imp_t = (t - 0.7) / 0.3
                imp_r = int(12 + imp_t * 18)
                imp_alpha = _NS_sirakzan._alpha(240 * intensity)
                _NS_sirakzan._aacircle(surface, (*_NS_sirakzan.PALETTE["spark_dark"], imp_alpha),
                                       (tx, ty), imp_r + 2, 2)
                _NS_sirakzan._aacircle(surface, (*_NS_sirakzan.PALETTE["spark_mid"], imp_alpha),
                                       (tx, ty), imp_r, 2)
                _NS_sirakzan._aacircle(surface, (*_NS_sirakzan.PALETTE["spark_light"], imp_alpha),
                                       (tx, ty), max(1, imp_r - 5), 1)
                _NS_sirakzan._aacircle(surface, (*_NS_sirakzan.PALETTE["spark_shine"], imp_alpha),
                                       (tx, ty), max(1, imp_r // 3))
                pygame.draw.rect(surface, _NS_sirakzan.PALETTE["white"], (tx - 1, ty - 1, 2, 2))
                # Radial sparks.
                for i in range(8):
                    angle_s = i * math.pi / 4
                    ex = tx + int(math.cos(angle_s) * imp_r)
                    ey = ty + int(math.sin(angle_s) * imp_r * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_sirakzan.PALETTE["spark_shine"], imp_alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL W: SHIELD CRASH (ball roll to target)
    # ============================================================
    def _draw_shieldcrash_ground(surface, boss, x, y, timer, phase):
        """Ground marker at target."""
        tx, ty = _NS_sirakzan._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.75:
            # Warning marker.
            t = min(1.0, progress / 0.5)
            r = int(20 * t)
            alpha = _NS_sirakzan._alpha(150 * t)
            pygame.draw.ellipse(surface, (*_NS_sirakzan.PALETTE["spark_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)
        else:
            # Post-impact crater.
            t = (progress - 0.75) / 0.25
            r = int(28 - t * 6)
            alpha = _NS_sirakzan._alpha(220 * (1 - t))
            if r > 2:
                pygame.draw.ellipse(surface,
                                    (*_NS_sirakzan.PALETTE["spark_dark"], alpha),
                                    (tx - r, ty - r // 3, r * 2, r * 2 // 3))
                pygame.draw.ellipse(surface,
                                    (*_NS_sirakzan.PALETTE["spark_mid"], alpha),
                                    (tx - r + 3, ty - r // 3 + 2,
                                     r * 2 - 6, r * 2 // 3 - 4))
                pygame.draw.ellipse(surface,
                                    (*_NS_sirakzan.PALETTE["spark_light"], alpha),
                                    (tx - r + 6, ty - r // 3 + 4,
                                     r * 2 - 12, r * 2 // 3 - 8))
    # ============================================================
    # SKILL E: LUCKY SHOT (projectile with lucky charm)
    # ============================================================
    def _draw_luckyshot_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_sirakzan._target_position(boss, x, y)
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.7:
            t = (progress - 0.7) / 0.3
            r = int(20 * (1 - t))
            alpha = _NS_sirakzan._alpha(180 * (1 - t))
            if r > 2:
                pygame.draw.ellipse(surface, (*_NS_sirakzan.PALETTE["clover_dark"], alpha),
                                    (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)
                pygame.draw.ellipse(surface, (*_NS_sirakzan.PALETTE["clover_mid"], alpha),
                                    (tx - r + 2, ty - r // 3 + 1,
                                     r * 2 - 4, r * 2 // 3 - 2), 1)
    def _draw_luckyshot_projectile(surface, boss, x, y, timer, phase):
        """Golden bullet with clover trail."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_sirakzan._target_position(boss, x, y)
        # Source at rapier tip.
        tip_x, tip_y = _NS_sirakzan._rapier_tip_position(boss, x, y)
        if progress < 0.3:
            # Aim + charge.
            t = progress / 0.3
            cr = int(3 + t * 5)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_sirakzan._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_sirakzan._aacircle(surface,
                                       (*_NS_sirakzan.PALETTE["spark_mid"], alpha),
                                       (tip_x, tip_y), r)
            _NS_sirakzan._aacircle(surface, _NS_sirakzan.PALETTE["spark_light"], (tip_x, tip_y), cr - 1)
            _NS_sirakzan._aacircle(surface, _NS_sirakzan.PALETTE["spark_shine"], (tip_x, tip_y), max(1, cr - 3))
            # Clover charge preview.
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["clover_mid"],
                             (tip_x, tip_y, 1, 1))
        else:
            # Projectile flying to target.
            t = (progress - 0.3) / 0.7
            t = min(1.0, t)
            bx = int(tip_x + (tx - tip_x) * t)
            by = int(tip_y + (ty - tip_y) * t)
            # Trail (golden sparkle stars).
            for i in range(9):
                trail_t = max(0.0, t - i * 0.05)
                px = int(tip_x + (tx - tip_x) * trail_t)
                py = int(tip_y + (ty - tip_y) * trail_t)
                alpha = _NS_sirakzan._alpha(230 - i * 24)
                size = max(1, 6 - i)
                # Star-shaped sparkle.
                _NS_sirakzan._aacircle(surface,
                                       (*_NS_sirakzan.PALETTE["spark_dark"], alpha),
                                       (px, py), size)
                _NS_sirakzan._aacircle(surface,
                                       (*_NS_sirakzan.PALETTE["spark_mid"], alpha),
                                       (px, py), max(1, size - 1))
                _NS_sirakzan._aacircle(surface,
                                       (*_NS_sirakzan.PALETTE["spark_light"], alpha),
                                       (px, py), max(1, size - 2))
                pygame.draw.rect(surface, (*_NS_sirakzan.PALETTE["spark_shine"], alpha),
                                 (px, py, 1, 1))
                # 4-point star rays.
                if i < 4:
                    for ray_dir in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        ray_x = px + ray_dir[0] * (size + 1)
                        ray_y = py + ray_dir[1] * (size + 1)
                        pygame.draw.rect(surface,
                                         (*_NS_sirakzan.PALETTE["spark_shine"], alpha),
                                         (ray_x, ray_y, 1, 1))
            # Big charm head (clover in center of golden orb).
            for r in range(9, 3, -2):
                alpha = _NS_sirakzan._alpha(90 * (9 - r) / 9)
                _NS_sirakzan._aacircle(surface,
                                       (*_NS_sirakzan.PALETTE["spark_mid"], alpha),
                                       (bx, by), r)
            _NS_sirakzan._aacircle(surface, _NS_sirakzan.PALETTE["spark_dark"], (bx, by), 6)
            _NS_sirakzan._aacircle(surface, _NS_sirakzan.PALETTE["spark_mid"], (bx, by), 4)
            _NS_sirakzan._aacircle(surface, _NS_sirakzan.PALETTE["spark_light"], (bx, by), 3)
            # 4-leaf clover center.
            for cx_off, cy_off in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                _NS_sirakzan._aacircle(surface, _NS_sirakzan.PALETTE["clover_dark"],
                                       (bx + cx_off, by + cy_off), 1)
                pygame.draw.rect(surface, _NS_sirakzan.PALETTE["clover_mid"],
                                 (bx + cx_off, by + cy_off, 1, 1))
            pygame.draw.rect(surface, _NS_sirakzan.PALETTE["clover_light"], (bx, by, 1, 1))
            # 8-point star rays.
            for i in range(8):
                ray_angle = phase * 2 + i * math.pi / 4
                ray_len = 8
                rx = bx + int(math.cos(ray_angle) * ray_len)
                ry = by + int(math.sin(ray_angle) * ray_len)
                pygame.draw.line(surface, _NS_sirakzan.PALETTE["spark_shine"],
                                 (bx, by), (rx, ry), 1)
                pygame.draw.rect(surface, _NS_sirakzan.PALETTE["white"], (rx, ry, 1, 1))
            # Impact burst.
            if t > 0.9:
                st = (t - 0.9) / 0.1
                imp_r = int(15 + st * 20)
                alpha = _NS_sirakzan._alpha(240 * (1 - st))
                _NS_sirakzan._aacircle(surface, (*_NS_sirakzan.PALETTE["spark_dark"], alpha),
                                       (tx, ty), imp_r + 2, 3)
                _NS_sirakzan._aacircle(surface, (*_NS_sirakzan.PALETTE["spark_mid"], alpha),
                                       (tx, ty), imp_r, 2)
                _NS_sirakzan._aacircle(surface, (*_NS_sirakzan.PALETTE["clover_mid"], alpha),
                                       (tx, ty), max(1, imp_r - 6), 1)
                _NS_sirakzan._aacircle(surface, (*_NS_sirakzan.PALETTE["spark_shine"], alpha),
                                       (tx, ty), max(1, imp_r // 3))
                # 4 clover shapes exploding.
                for i in range(4):
                    angle = i * math.pi / 2
                    ex = tx + int(math.cos(angle) * imp_r)
                    ey = ty + int(math.sin(angle) * imp_r * 0.7)
                    _NS_sirakzan._aacircle(surface,
                                           (*_NS_sirakzan.PALETTE["clover_mid"], alpha),
                                           (ex, ey), 3)
                    _NS_sirakzan._aacircle(surface,
                                           (*_NS_sirakzan.PALETTE["clover_light"], alpha),
                                           (ex, ey), 1)
                    pygame.draw.rect(surface, _NS_sirakzan.PALETTE["white"], (ex, ey, 1, 1))
    # ============================================================
    # SKILL R: ROLLING THUNDER (chain rolling)
    # ============================================================
    def _draw_rollingthunder_ground(surface, boss, x, y, timer, phase):
        """Rolling path with fire trail on ground."""
        facing = boss.direction
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_sirakzan._target_position(boss, x, y)
        if 0.1 < progress < 0.95:
            t = (progress - 0.1) / 0.85
            # Fiery trail on ground.
            for i in range(15):
                trail_t = max(0.0, t - i * 0.03)
                if trail_t < 0 or trail_t > 1:
                    continue
                px = int(x + (tx - x) * trail_t)
                py = int(y + 40 + (ty - y - 40) * trail_t * 0.3)  # keep low
                alpha = _NS_sirakzan._alpha(220 - i * 14)
                # Fire glow trail.
                pygame.draw.ellipse(surface, (*_NS_sirakzan.PALETTE["spark_dark"], alpha),
                                    (px - 12, py - 3, 24, 6))
                pygame.draw.ellipse(surface, (*_NS_sirakzan.PALETTE["spark_mid"], alpha),
                                    (px - 10, py - 2, 20, 4))
                pygame.draw.ellipse(surface, (*_NS_sirakzan.PALETTE["spark_light"], alpha),
                                    (px - 6, py - 1, 12, 2))
                pygame.draw.rect(surface, (*_NS_sirakzan.PALETTE["spark_shine"], alpha),
                                 (px, py, 1, 1))



# ====================================================================
# VALEKRIS (VENGEFUL WRAITH) - Mini Boss
# ====================================================================

class _NS_valekris:
    """Namespace valekris - spectral wraith mini boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Ghostly cyan skin
        "skin_darkest": (10, 25, 35),
        "skin_dark": (30, 65, 80),
        "skin_mid": (75, 130, 145),
        "skin_light": (140, 195, 210),
        "skin_shine": (200, 240, 250),
        # Dark hair (black-blue)
        "hair_darkest": (3, 5, 12),
        "hair_dark": (12, 18, 30),
        "hair_mid": (25, 35, 55),
        "hair_light": (55, 70, 100),
        # Dark armor (black spectral)
        "armor_darkest": (5, 8, 15),
        "armor_dark": (18, 25, 40),
        "armor_mid": (40, 55, 80),
        "armor_light": (85, 105, 140),
        "armor_shine": (140, 165, 195),
        # Bone helm (dark)
        "bone_dark": (25, 25, 40),
        "bone_mid": (60, 65, 85),
        "bone_light": (120, 130, 155),
        # Cyan glow (main color - eyes, spears, aura)
        "cyan_darkest": (5, 30, 45),
        "cyan_dark": (15, 80, 115),
        "cyan_mid": (40, 180, 220),
        "cyan_light": (130, 235, 255),
        "cyan_hot": (200, 250, 255),
        "cyan_shine": (240, 255, 255),
        # Spear tip glow (brighter cyan)
        "spear_dark": (20, 100, 140),
        "spear_mid": (60, 200, 240),
        "spear_light": (170, 245, 255),
        # Spectral tendrils (dark cyan smoke)
        "wraith_darkest": (5, 15, 25),
        "wraith_dark": (15, 40, 55),
        "wraith_mid": (30, 90, 115),
        "wraith_light": (80, 160, 190),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 6),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_valekris._clamp(color)
        if _NS_valekris.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_valekris._clamp(color)
        if _NS_valekris.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_valekris._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 240 * getattr(boss, "direction", 1)), int(y)
    def _arm_elbow(shoulder, hand, bend=4, bend_up=False):
        sx, sy = shoulder
        hx, hy = hand
        mid_x = (sx + hx) / 2
        mid_y = (sy + hy) / 2
        dx = hx - sx
        dy = hy - sy
        length = max(1.0, math.sqrt(dx * dx + dy * dy))
        perp_x = -dy / length
        perp_y = dx / length
        if bend_up:
            if perp_y > 0:
                perp_x = -perp_x
                perp_y = -perp_y
        else:
            if perp_y < 0:
                perp_x = -perp_x
                perp_y = -perp_y
        return (int(mid_x + perp_x * bend), int(mid_y + perp_y * bend))
    def _spear_hand_position(boss, x, y):
        """Position of spear-holding hand (source of projectiles)."""
        facing = boss.direction
        active = getattr(boss, "_vlk_attack_active", False)
        progress = getattr(boss, "_vlk_attack_progress", 0.0)
        if active:
            if progress < 0.35:
                # Wind back (behind head).
                t = progress / 0.35
                hx = x + facing * int(-6 + t * -8)
                hy = y - int(18 + t * 4)
            elif progress < 0.55:
                # Throw forward.
                t = (progress - 0.35) / 0.2
                hx = x + facing * int(-14 + t * 42)
                hy = y - 22 + int(t * 12)
            elif progress < 0.75:
                # Hold extended.
                hx = x + facing * 28
                hy = y - 10
            else:
                # Return to ready.
                t = (progress - 0.75) / 0.25
                hx = x + facing * int(28 - t * 24)
                hy = y - 10 - int(t * 6)
        else:
            hx = x + facing * 4
            hy = y - 16
        return hx, hy
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_valekris(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_valekris._update_attack_anim(boss)
        attack_progress = getattr(boss, "_vlk_attack_progress", 0.0)
        attacking = (
            getattr(boss, "_vlk_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )
        # Ambient FX behind body.
        _NS_valekris._draw_cyan_aura(surface, x, y, pulse)
        _NS_valekris._draw_ground_ring(surface, x, y + 52, pulse, active_skill)
        # Skill ground FX.
        if active_skill == "w":
            _NS_valekris._draw_sentinel_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_valekris._draw_fatescall_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating body (ghostly float).
        float_bob = math.sin(pulse * 0.8) * 6  # more pronounced float
        body_y = y + int(float_bob)
        # Ghost tendrils rising below (only when idle/light action).
        _NS_valekris._draw_ghost_tendrils(surface, x, body_y, pulse)
        # Body pose.
        if active_skill == "q":
            _NS_valekris._draw_body_qthrow(surface, boss, x, body_y,
                                            skill_timer, pulse)
        elif active_skill == "w":
            _NS_valekris._draw_body_summon(surface, boss, x, body_y,
                                            skill_timer, pulse)
        elif active_skill == "e":
            _NS_valekris._draw_body_rend(surface, boss, x, body_y,
                                          skill_timer, pulse)
        elif active_skill == "r":
            _NS_valekris._draw_body_binding(surface, boss, x, body_y,
                                             skill_timer, pulse)
        elif attacking:
            _NS_valekris._draw_body_attack(surface, boss, x, body_y)
        else:
            _NS_valekris._draw_body_idle(surface, boss, x, body_y)
        # Foreground FX.
        if active_skill == "q":
            _NS_valekris._draw_pierce_projectile(surface, boss, x, body_y,
                                                  skill_timer, pulse)
        elif active_skill == "w":
            _NS_valekris._draw_sentinel_projectile(surface, boss, x, body_y,
                                                     skill_timer, pulse)
        elif active_skill == "e":
            _NS_valekris._draw_rend_burst(surface, boss, x, body_y,
                                           skill_timer, pulse)
        elif active_skill == "r":
            _NS_valekris._draw_fatescall_tether(surface, boss, x, body_y,
                                                  skill_timer, pulse)
        else:
            if attacking and attack_progress > 0:
                _NS_valekris._draw_basic_spear_throw(surface, boss, x, body_y)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_vlk_attack_active", False))
        if not active and timer >= cooldown - 2:
            boss._vlk_attack_active = True
            boss._vlk_attack_frame = 0
            active = True
        elif active:
            boss._vlk_attack_frame = int(getattr(boss, "_vlk_attack_frame", 0)) + 1
            if boss._vlk_attack_frame >= cooldown:
                boss._vlk_attack_active = False
                boss._vlk_attack_frame = 0
                active = False
        boss._vlk_previous_timer = timer
        boss._vlk_attack_progress = (
            min(1.0, getattr(boss, "_vlk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, cx, cy):
        _NS_valekris._draw_float_shadow(surface, cx, cy + 54, boss.pulse)
        _NS_valekris._draw_body(surface, boss, cx, cy, "idle", 0)
    def _draw_body_attack(surface, boss, cx, cy):
        progress = getattr(boss, "_vlk_attack_progress", 0.0)
        _NS_valekris._draw_float_shadow(surface, cx, cy + 54, boss.pulse)
        _NS_valekris._draw_body(surface, boss, cx, cy, "throw", progress)
    def _draw_body_qthrow(surface, boss, cx, cy, timer, phase):
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_valekris._draw_float_shadow(surface, cx, cy + 54, phase)
        _NS_valekris._draw_body(surface, boss, cx, cy, "throw", progress)
    def _draw_body_summon(surface, boss, cx, cy, timer, phase):
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_valekris._draw_float_shadow(surface, cx, cy + 54, phase)
        _NS_valekris._draw_body(surface, boss, cx, cy, "summon", progress)
    def _draw_body_rend(surface, boss, cx, cy, timer, phase):
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_valekris._draw_float_shadow(surface, cx, cy + 54, phase)
        _NS_valekris._draw_body(surface, boss, cx, cy, "rend", progress)
    def _draw_body_binding(surface, boss, cx, cy, timer, phase):
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_valekris._draw_float_shadow(surface, cx, cy + 54, phase)
        _NS_valekris._draw_body(surface, boss, cx, cy, "binding", progress)
    # ============================================================
    # MAIN BODY
    # ============================================================
    def _draw_body(surface, boss, cx, cy, action, progress):
        facing = boss.direction
        phase = boss.pulse
        # Draw ghost tail/lower body (wraith form, no legs).
        _NS_valekris._draw_wraith_lower(surface, cx, cy, facing, phase)
        # Draw spears on back FIRST (behind torso).
        _NS_valekris._draw_back_spears(surface, cx, cy - 10, facing, phase)
        # Torso.
        _NS_valekris._draw_torso(surface, cx, cy, facing, phase)
        # Long hair back layer.
        _NS_valekris._draw_hair_back(surface, cx, cy - 22, facing, phase)
        # Head with horned helm.
        _NS_valekris._draw_head(surface, cx, cy - 22, facing, phase, action)
        # Arms with spear.
        _NS_valekris._draw_arms(surface, cx, cy, facing, phase, action, progress)
    def _draw_wraith_lower(surface, cx, cy, facing, phase):
        """Ghostly lower body - flowing tendrils instead of legs."""
        sway = math.sin(phase * 0.7) * 2
        # Main flowing body strands.
        for i, x_off in enumerate((-10, -4, 0, 4, 10)):
            wave = math.sin(phase * 0.8 + i * 0.5) * 3
            strand_pts = [
                (cx + x_off + int(sway * 0.5) - 3, cy + 8),
                (cx + x_off + int(sway * 0.5) + 3, cy + 8),
                (cx + x_off + int(wave) + 4, cy + 22),
                (cx + x_off + int(wave * 1.2) + 2, cy + 36),
                (cx + x_off + int(wave * 1.5), cy + 46),
                (cx + x_off + int(wave * 1.2) - 2, cy + 36),
                (cx + x_off + int(wave) - 4, cy + 22),
            ]
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["shadow_deep"],
                               [(p[0] + 1, p[1] + 2) for p in strand_pts])
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["wraith_darkest"], strand_pts)
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["wraith_dark"], [
                (cx + x_off + int(sway * 0.5) - 2, cy + 9),
                (cx + x_off + int(sway * 0.5) + 2, cy + 9),
                (cx + x_off + int(wave) + 3, cy + 22),
                (cx + x_off + int(wave * 1.2) + 1, cy + 34),
                (cx + x_off + int(wave * 1.5), cy + 44),
                (cx + x_off + int(wave * 1.2) - 1, cy + 34),
                (cx + x_off + int(wave) - 3, cy + 22),
            ])
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["wraith_mid"], [
                (cx + x_off + int(sway * 0.5) - 1, cy + 10),
                (cx + x_off + int(sway * 0.5) + 1, cy + 10),
                (cx + x_off + int(wave) + 2, cy + 22),
                (cx + x_off + int(wave * 1.2), cy + 30),
                (cx + x_off + int(wave) - 2, cy + 22),
            ])
            # Cyan glow tip at end of strand.
            tip_x = cx + x_off + int(wave * 1.5)
            tip_y = cy + 46
            pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_dark"], (tip_x, tip_y, 1, 1))
        # Wisps rising from the tendrils.
        for i in range(6):
            wisp_t = (phase * 0.5 + i * 0.17) % 1.0
            wx = cx - 12 + i * 5 + int(math.sin(phase + i) * 3)
            wy = cy + 40 - int(wisp_t * 30)
            alpha = _NS_valekris._alpha(180 * (1 - wisp_t))
            if alpha > 0:
                _NS_valekris._aacircle(surface,
                                       (*_NS_valekris.PALETTE["cyan_dark"], alpha),
                                       (wx, wy), 2)
                _NS_valekris._aacircle(surface,
                                       (*_NS_valekris.PALETTE["cyan_mid"], alpha),
                                       (wx, wy - 1), 1)
                pygame.draw.rect(surface, (*_NS_valekris.PALETTE["cyan_light"], alpha),
                                 (wx, wy - 1, 1, 1))
    def _draw_back_spears(surface, cx, cy, facing, phase):
        """Multiple cyan spears mounted on back."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # 5 spears fanning behind body.
        for i, (angle_deg, offset_x, offset_y) in enumerate([
            (-70, -4, 2),
            (-55, -6, -2),
            (-40, -8, -6),
            (-25, -10, -10),
            (-10, -12, -14),
        ]):
            angle = math.radians(angle_deg)
            base_x = cx + facing * offset_x
            base_y = cy + offset_y
            spear_len = 28
            tip_x = base_x + int(math.cos(angle) * spear_len) * (-facing)
            tip_y = base_y + int(math.sin(angle) * spear_len)
            # Shadow.
            pygame.draw.line(surface, _NS_valekris.PALETTE["shadow_deep"],
                             (base_x + 1, base_y + 1), (tip_x + 1, tip_y + 1), 3)
            # Shaft (dark blue-black).
            pygame.draw.line(surface, _NS_valekris.PALETTE["armor_darkest"],
                             (base_x, base_y), (tip_x, tip_y), 3)
            pygame.draw.line(surface, _NS_valekris.PALETTE["armor_dark"],
                             (base_x, base_y), (tip_x, tip_y), 2)
            # Cyan glow along shaft.
            for r in range(4, 0, -1):
                alpha = _NS_valekris._alpha(60 * (4 - r) / 4 * pulse)
                _NS_valekris._aaline(surface,
                                     (*_NS_valekris.PALETTE["cyan_mid"], alpha),
                                     (base_x, base_y), (tip_x, tip_y), r)
            _NS_valekris._aaline(surface,
                                 _NS_valekris.PALETTE["cyan_light"],
                                 (base_x, base_y), (tip_x, tip_y), 1)
            # Spear tip (jagged crystal-like blade).
            perp_x = -math.sin(angle) * (-facing)
            perp_y = math.cos(angle)
            tip_head_len = 6
            head_tip_x = tip_x + int(math.cos(angle) * tip_head_len) * (-facing)
            head_tip_y = tip_y + int(math.sin(angle) * tip_head_len)
            side_a_x = tip_x + int(perp_x * 3)
            side_a_y = tip_y + int(perp_y * 3)
            side_b_x = tip_x - int(perp_x * 3)
            side_b_y = tip_y - int(perp_y * 3)
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["shadow_deep"], [
                (head_tip_x + 1, head_tip_y + 1),
                (side_a_x + 1, side_a_y + 1),
                (side_b_x + 1, side_b_y + 1),
            ])
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["cyan_darkest"], [
                (head_tip_x, head_tip_y),
                (side_a_x, side_a_y),
                (side_b_x, side_b_y),
            ])
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["cyan_dark"], [
                (head_tip_x, head_tip_y),
                (int((head_tip_x + side_a_x) / 2), int((head_tip_y + side_a_y) / 2)),
                (tip_x, tip_y),
                (int((head_tip_x + side_b_x) / 2), int((head_tip_y + side_b_y) / 2)),
            ])
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["cyan_mid"], [
                (head_tip_x, head_tip_y),
                (int(tip_x + (head_tip_x - tip_x) * 0.6),
                 int(tip_y + (head_tip_y - tip_y) * 0.6)),
                (tip_x, tip_y),
            ])
            # Bright glow at tip.
            for r in range(4, 0, -1):
                alpha = _NS_valekris._alpha(100 * (4 - r) / 4 * pulse)
                _NS_valekris._aacircle(surface,
                                       (*_NS_valekris.PALETTE["cyan_hot"], alpha),
                                       (head_tip_x, head_tip_y), r)
            pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_shine"],
                             (head_tip_x, head_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_valekris.PALETTE["white"],
                             (head_tip_x, head_tip_y, 1, 1))
    def _draw_torso(surface, cx, cy, facing, phase):
        """Dark spectral armor torso."""
        breath = math.sin(phase * 0.6) * 1
        torso_pts = [
            (cx - 10, cy - 14),
            (cx - 12, cy - 6),
            (cx - 10, cy + 4),
            (cx - 6, cy + 10),
            (cx + 6, cy + 10),
            (cx + 10, cy + 4),
            (cx + 12, cy - 6),
            (cx + 10, cy - 14),
            (cx + 4, cy - 18),
            (cx - 4, cy - 18),
        ]
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in torso_pts])
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["armor_darkest"], torso_pts)
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["armor_dark"], [
            (cx - 9, cy - 13),
            (cx - 11, cy - 6),
            (cx - 9, cy + 3),
            (cx - 5, cy + 9),
            (cx + 5, cy + 9),
            (cx + 9, cy + 3),
            (cx + 11, cy - 6),
            (cx + 9, cy - 13),
            (cx + 3, cy - 17),
            (cx - 3, cy - 17),
        ])
        # Chest highlights.
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["armor_mid"], [
            (cx - 7, cy - 10),
            (cx - 9, cy - 5),
            (cx - 7, cy + 2),
            (cx + 7, cy + 2),
            (cx + 9, cy - 5),
            (cx + 7, cy - 10),
            (cx + 3, cy - 14),
            (cx - 3, cy - 14),
        ])
        # Chest gem (cyan glowing).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        gem_x = cx
        gem_y = cy - 6
        for r in range(6, 0, -1):
            alpha = _NS_valekris._alpha(120 * (6 - r) / 6 * pulse)
            _NS_valekris._aacircle(surface,
                                   (*_NS_valekris.PALETTE["cyan_mid"], alpha),
                                   (gem_x, gem_y), r)
        # Diamond gem shape.
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["cyan_darkest"], [
            (gem_x, gem_y - 3),
            (gem_x - 2, gem_y),
            (gem_x, gem_y + 3),
            (gem_x + 2, gem_y),
        ])
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["cyan_dark"], [
            (gem_x, gem_y - 2),
            (gem_x - 1, gem_y),
            (gem_x, gem_y + 2),
            (gem_x + 1, gem_y),
        ])
        pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_light"], (gem_x, gem_y, 1, 1))
        pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_shine"], (gem_x, gem_y - 1, 1, 1))
        # Ribcage/armor lines.
        for i in range(2):
            y_line = cy - 2 + i * 4
            for side_l in (-1, 1):
                pygame.draw.line(surface, _NS_valekris.PALETTE["armor_darkest"],
                                 (cx + side_l * 3, y_line),
                                 (cx + side_l * 8, y_line + 1), 1)
                pygame.draw.line(surface, _NS_valekris.PALETTE["armor_mid"],
                                 (cx + side_l * 3, y_line - 1),
                                 (cx + side_l * 8, y_line), 1)
        # Shoulder pauldrons with spikes.
        for side in (-1, 1):
            base_x = cx + side * 10
            paul_pts = [
                (base_x - side, cy - 16),
                (base_x + side * 3, cy - 16),
                (base_x + side * 5, cy - 10),
                (base_x + side * 3, cy - 8),
                (base_x - side, cy - 10),
            ]
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["armor_darkest"], paul_pts)
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["armor_dark"], [
                (base_x, cy - 15),
                (base_x + side * 3, cy - 15),
                (base_x + side * 4, cy - 10),
                (base_x + side, cy - 9),
            ])
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["armor_mid"], [
                (base_x + side, cy - 14),
                (base_x + side * 3, cy - 13),
                (base_x + side * 3, cy - 11),
                (base_x + side * 1, cy - 10),
            ])
            # Spike on shoulder.
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["bone_dark"], [
                (base_x + side * 2, cy - 16),
                (base_x + side * 4, cy - 22),
                (base_x + side * 5, cy - 15),
            ])
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["bone_mid"], [
                (base_x + side * 3, cy - 16),
                (base_x + side * 4, cy - 21),
                (base_x + side * 4, cy - 15),
            ])
            pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_light"],
                             (base_x + side * 4, cy - 21, 1, 1))
    def _draw_hair_back(surface, cx, cy, facing, phase):
        """Long dark flowing hair behind head."""
        sway = math.sin(phase * 0.5) * 2
        # Hair mass flowing back and down.
        hair_pts = [
            (cx - 8, cy),
            (cx - 12 + int(sway), cy + 6),
            (cx - 14 + int(sway), cy + 16),
            (cx - 12 + int(sway * 1.2), cy + 26),
            (cx - 8 + int(sway), cy + 34),
            (cx - 3, cy + 36),
            (cx + 3, cy + 36),
            (cx + 8 - int(sway), cy + 34),
            (cx + 12 - int(sway * 1.2), cy + 26),
            (cx + 14 - int(sway), cy + 16),
            (cx + 12 - int(sway), cy + 6),
            (cx + 8, cy),
        ]
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in hair_pts])
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["hair_darkest"], hair_pts)
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["hair_dark"], [
            (cx - 7, cy),
            (cx - 11 + int(sway), cy + 6),
            (cx - 12 + int(sway), cy + 16),
            (cx - 10 + int(sway * 1.2), cy + 24),
            (cx - 6 + int(sway), cy + 32),
            (cx + 6 - int(sway), cy + 32),
            (cx + 10 - int(sway * 1.2), cy + 24),
            (cx + 12 - int(sway), cy + 16),
            (cx + 11 - int(sway), cy + 6),
            (cx + 7, cy),
        ])
        # Hair mid-tones as strands.
        for i, x_off in enumerate((-8, -4, 0, 4, 8)):
            strand_x = cx + x_off + int(sway * 0.5)
            strand_top_y = cy + 4
            strand_bot_y = cy + 30 - i * 2 + i
            pygame.draw.line(surface, _NS_valekris.PALETTE["hair_mid"],
                             (strand_x, strand_top_y),
                             (strand_x + int(sway), strand_bot_y), 1)
    def _draw_head(surface, cx, cy, facing, phase, action):
        """Skull-like head with bone crown."""
        # Face (gaunt).
        face_pts = [
            (cx - 6, cy - 2),
            (cx - 7, cy + 1),
            (cx - 6, cy + 4),
            (cx - 3, cy + 7),
            (cx + 3, cy + 7),
            (cx + 6, cy + 4),
            (cx + 7, cy + 1),
            (cx + 6, cy - 2),
            (cx + 3, cy - 6),
            (cx - 3, cy - 6),
        ]
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in face_pts])
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["skin_darkest"], face_pts)
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["skin_dark"], [
            (cx - 5, cy - 1),
            (cx - 6, cy + 1),
            (cx - 5, cy + 3),
            (cx - 2, cy + 6),
            (cx + 2, cy + 6),
            (cx + 5, cy + 3),
            (cx + 6, cy + 1),
            (cx + 5, cy - 1),
            (cx + 2, cy - 5),
            (cx - 2, cy - 5),
        ])
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["skin_mid"], [
            (cx - 3, cy),
            (cx - 4, cy + 2),
            (cx - 2, cy + 4),
            (cx + 2, cy + 4),
            (cx + 4, cy + 2),
            (cx + 3, cy),
        ])
        # Cheek shading.
        pygame.draw.rect(surface, _NS_valekris.PALETTE["skin_light"], (cx - 3, cy, 1, 1))
        pygame.draw.rect(surface, _NS_valekris.PALETTE["skin_light"], (cx + 2, cy, 1, 1))
        # Sunken cheek shadows.
        pygame.draw.line(surface, _NS_valekris.PALETTE["shadow_deep"],
                         (cx - 4, cy + 2), (cx - 3, cy + 5), 1)
        pygame.draw.line(surface, _NS_valekris.PALETTE["shadow_deep"],
                         (cx + 4, cy + 2), (cx + 3, cy + 5), 1)
        # Glowing cyan eyes (spectral empty).
        _NS_valekris._draw_wraith_eyes(surface, cx, cy, phase, action)
        # Nose (barely visible).
        pygame.draw.rect(surface, _NS_valekris.PALETTE["skin_darkest"], (cx, cy + 3, 1, 1))
        # Mouth (grim/roar during attack).
        if action in ("throw", "rend", "binding") and phase % 1 < 0.6:
            pygame.draw.rect(surface, _NS_valekris.PALETTE["shadow_deep"],
                             (cx - 2, cy + 5, 5, 2))
            pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_dark"],
                             (cx - 1, cy + 5, 3, 1))
        else:
            pygame.draw.line(surface, _NS_valekris.PALETTE["shadow_deep"],
                             (cx - 2, cy + 6), (cx + 2, cy + 6), 1)
        # BONE CROWN with horns.
        _NS_valekris._draw_bone_crown(surface, cx, cy - 6, facing, phase)
    def _draw_wraith_eyes(surface, cx, cy, phase, action):
        """Empty glowing cyan eyes."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        intensity = 1.5 if action != "idle" else 1.0
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy - 1
            # Deep socket.
            pygame.draw.rect(surface, _NS_valekris.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 3, 3))
            pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_darkest"],
                             (ex - 1, ey - 1, 3, 3))
            # Glow halo.
            for r in range(5, 0, -1):
                alpha = _NS_valekris._alpha(140 * (5 - r) / 5 * pulse * intensity)
                _NS_valekris._aacircle(surface,
                                       (*_NS_valekris.PALETTE["cyan_mid"], alpha),
                                       (ex, ey), r)
            # Glowing eye core (no pupil - spectral empty).
            pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_dark"], (ex - 1, ey, 3, 1))
            pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_mid"], (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_light"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_shine"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_valekris.PALETTE["white"], (ex, ey, 1, 1))
            # Wispy trail rising from eye (spectral).
            for tr in range(2):
                wisp_alpha = _NS_valekris._alpha(150 * pulse * intensity - tr * 40)
                if wisp_alpha > 0:
                    pygame.draw.rect(surface,
                                     (*_NS_valekris.PALETTE["cyan_mid"], wisp_alpha),
                                     (ex + int(math.sin(phase + tr) * 1), ey - 2 - tr * 2, 1, 1))
    def _draw_bone_crown(surface, cx, cy, facing, phase):
        """Bone crown with multiple horns going up and back."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Base band.
        pygame.draw.rect(surface, _NS_valekris.PALETTE["shadow_deep"],
                         (cx - 8, cy + 1, 17, 3))
        pygame.draw.rect(surface, _NS_valekris.PALETTE["bone_dark"], (cx - 8, cy, 17, 3))
        pygame.draw.rect(surface, _NS_valekris.PALETTE["bone_mid"], (cx - 7, cy, 15, 2))
        pygame.draw.rect(surface, _NS_valekris.PALETTE["bone_light"], (cx - 6, cy, 13, 1))
        # Multiple horns going up and back (like antler crown).
        horns = [
            (-6, -8, -8, 1),   # left far
            (-3, -12, -5, 1),  # left mid
            (0, -14, 0, 0),    # center tallest
            (3, -12, 5, 1),    # right mid
            (6, -8, 8, 1),     # right far
        ]
        for i, (base_x_off, tip_y_off, tip_x_off, ridges) in enumerate(horns):
            base_x = cx + base_x_off
            base_y = cy
            tip_x = cx + tip_x_off
            tip_y = cy + tip_y_off
            # Horn shape.
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["shadow_deep"], [
                (base_x - 1 + 1, base_y + 1),
                (tip_x + 1, tip_y + 1),
                (base_x + 1 + 1, base_y + 1),
            ])
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["bone_dark"], [
                (base_x - 1, base_y),
                (tip_x, tip_y),
                (base_x + 1, base_y),
            ])
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["bone_mid"], [
                (base_x, base_y),
                (tip_x, tip_y),
                (base_x + 1, base_y),
            ])
            pygame.draw.rect(surface, _NS_valekris.PALETTE["bone_light"], (tip_x, tip_y, 1, 1))
            # Cyan glow at horn tip.
            for r in range(3, 0, -1):
                alpha = _NS_valekris._alpha(100 * (3 - r) / 3 * pulse)
                _NS_valekris._aacircle(surface,
                                       (*_NS_valekris.PALETTE["cyan_mid"], alpha),
                                       (tip_x, tip_y), r)
            pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_shine"], (tip_x, tip_y, 1, 1))
    def _draw_arms(surface, cx, cy, facing, phase, action, progress):
        """Two arms. Front arm holds throwing spear."""
        front_sh = (cx + facing * 10, cy - 12)
        back_sh = (cx - facing * 10, cy - 12)
        # Determine positions.
        if action == "throw":
            # Basic/Q throw.
            if progress < 0.35:
                # Wind back.
                t = progress / 0.35
                front_hand_x = cx + facing * int(-8 * t)
                front_hand_y = cy - 14 - int(t * 6)
            elif progress < 0.55:
                # Forward throw.
                t = (progress - 0.35) / 0.2
                front_hand_x = cx + facing * int(-8 + t * 36)
                front_hand_y = cy - 20 + int(t * 16)
            elif progress < 0.75:
                # Hold extended.
                front_hand_x = cx + facing * 28
                front_hand_y = cy - 4
            else:
                # Return.
                t = (progress - 0.75) / 0.25
                front_hand_x = cx + facing * int(28 - t * 24)
                front_hand_y = cy - 4 - int(t * 10)
        elif action == "rend":
            # Both hands out - pulling spears with force.
            if progress < 0.5:
                t = progress / 0.5
                front_hand_x = cx + facing * int(6 + t * 12)
                front_hand_y = cy - 8 - int(t * 6)
            else:
                t = (progress - 0.5) / 0.5
                # Pull back sharply.
                front_hand_x = cx + facing * int(18 - t * 30)
                front_hand_y = cy - 14 + int(t * 4)
        elif action == "summon":
            # Reach out casting.
            if progress < 0.5:
                t = progress / 0.5
                front_hand_x = cx + facing * int(6 + t * 18)
                front_hand_y = cy - 6 - int(t * 6)
            else:
                t = (progress - 0.5) / 0.5
                front_hand_x = cx + facing * int(24 - t * 12)
                front_hand_y = cy - 12 + int(t * 6)
        elif action == "binding":
            # Both hands raised.
            front_hand_x = cx + facing * 12
            front_hand_y = cy - 16
        else:
            # Idle: holding spear ready.
            idle_sway = math.sin(phase * 0.8) * 1
            front_hand_x = cx + facing * 8
            front_hand_y = cy - 12 + int(idle_sway)
        # Back hand.
        back_hand_x = cx - facing * 8
        back_hand_y = cy - 4
        # Compute elbows.
        front_elbow = _NS_valekris._arm_elbow(front_sh, (front_hand_x, front_hand_y), bend=4)
        back_elbow = _NS_valekris._arm_elbow(back_sh, (back_hand_x, back_hand_y), bend=3)
        # Draw back arm.
        _NS_valekris._draw_arm_segment(surface, back_sh, back_elbow,
                                        (back_hand_x, back_hand_y))
        # Draw front arm.
        _NS_valekris._draw_arm_segment(surface, front_sh, front_elbow,
                                        (front_hand_x, front_hand_y))
        # DRAW HAND-HELD SPEAR (only when in appropriate action).
        # During throw's later phase, spear is airborne so hide.
        if action == "throw" and 0.5 < progress < 0.85:
            pass  # spear in flight (drawn as projectile)
        elif action == "summon" and progress > 0.5:
            pass  # sentinel released
        else:
            # Hand-held spear at front hand.
            _NS_valekris._draw_handheld_spear(surface, front_hand_x, front_hand_y,
                                                facing, phase, action, progress)
    def _draw_arm_segment(surface, shoulder, elbow, hand):
        """Draw a single arm."""
        sx, sy = shoulder
        ex, ey = elbow
        hx, hy = hand
        # Upper arm.
        pygame.draw.line(surface, _NS_valekris.PALETTE["shadow_deep"],
                         (sx + 1, sy + 1), (ex + 1, ey + 1), 5)
        pygame.draw.line(surface, _NS_valekris.PALETTE["armor_darkest"],
                         (sx, sy), (ex, ey), 4)
        pygame.draw.line(surface, _NS_valekris.PALETTE["armor_dark"],
                         (sx, sy), (ex, ey), 3)
        pygame.draw.line(surface, _NS_valekris.PALETTE["armor_mid"],
                         (sx, sy - 1), (ex, ey - 1), 1)
        # Forearm (skin visible).
        pygame.draw.line(surface, _NS_valekris.PALETTE["shadow_deep"],
                         (ex + 1, ey + 1), (hx + 1, hy + 1), 4)
        pygame.draw.line(surface, _NS_valekris.PALETTE["skin_darkest"],
                         (ex, ey), (hx, hy), 3)
        pygame.draw.line(surface, _NS_valekris.PALETTE["skin_dark"],
                         (ex, ey), (hx, hy), 2)
        pygame.draw.line(surface, _NS_valekris.PALETTE["skin_mid"],
                         (ex, ey - 1), (hx, hy - 1), 1)
        # Hand (small).
        _NS_valekris._aacircle(surface, _NS_valekris.PALETTE["skin_dark"], (hx, hy), 2)
        _NS_valekris._aacircle(surface, _NS_valekris.PALETTE["skin_mid"], (hx, hy - 1), 1)
    def _draw_handheld_spear(surface, hx, hy, facing, phase, action, progress):
        """Cyan spear held in hand."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Spear angle depends on action.
        if action == "throw" and progress < 0.35:
            angle = -math.pi / 3  # tilted up behind
        elif action == "throw" and progress < 0.55:
            angle = 0  # horizontal forward
        elif action == "rend":
            angle = -math.pi / 6
        else:
            angle = -math.pi / 8  # slight up tilt idle
        spear_len = 24
        base_x = hx - int(math.cos(angle) * 4) * facing
        base_y = hy - int(math.sin(angle) * 4)
        tip_x = hx + int(math.cos(angle) * spear_len) * facing
        tip_y = hy + int(math.sin(angle) * spear_len)
        # Shadow.
        pygame.draw.line(surface, _NS_valekris.PALETTE["shadow_deep"],
                         (base_x + 1, base_y + 1), (tip_x + 1, tip_y + 1), 3)
        # Shaft (dark).
        pygame.draw.line(surface, _NS_valekris.PALETTE["armor_darkest"],
                         (base_x, base_y), (tip_x, tip_y), 3)
        pygame.draw.line(surface, _NS_valekris.PALETTE["armor_dark"],
                         (base_x, base_y), (tip_x, tip_y), 2)
        # Cyan glow along shaft.
        for r in range(4, 0, -1):
            alpha = _NS_valekris._alpha(70 * (4 - r) / 4 * pulse)
            _NS_valekris._aaline(surface,
                                 (*_NS_valekris.PALETTE["cyan_mid"], alpha),
                                 (base_x, base_y), (tip_x, tip_y), r)
        _NS_valekris._aaline(surface, _NS_valekris.PALETTE["cyan_light"],
                             (base_x, base_y), (tip_x, tip_y), 1)
        # Spear head (crystalline).
        perp_x = -math.sin(angle) * facing
        perp_y = math.cos(angle)
        head_tip_x = tip_x + int(math.cos(angle) * 7) * facing
        head_tip_y = tip_y + int(math.sin(angle) * 7)
        side_a = (tip_x + int(perp_x * 3), tip_y + int(perp_y * 3))
        side_b = (tip_x - int(perp_x * 3), tip_y - int(perp_y * 3))
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["shadow_deep"], [
            (head_tip_x + 1, head_tip_y + 1),
            (side_a[0] + 1, side_a[1] + 1),
            (side_b[0] + 1, side_b[1] + 1),
        ])
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["cyan_darkest"], [
            (head_tip_x, head_tip_y), side_a, side_b,
        ])
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["cyan_dark"], [
            (head_tip_x, head_tip_y),
            (int((head_tip_x + side_a[0]) / 2), int((head_tip_y + side_a[1]) / 2)),
            (tip_x, tip_y),
            (int((head_tip_x + side_b[0]) / 2), int((head_tip_y + side_b[1]) / 2)),
        ])
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["cyan_mid"], [
            (head_tip_x, head_tip_y),
            (int(tip_x + (head_tip_x - tip_x) * 0.5),
             int(tip_y + (head_tip_y - tip_y) * 0.5)),
            (tip_x, tip_y),
        ])
        # Glow at tip.
        for r in range(5, 0, -1):
            alpha = _NS_valekris._alpha(120 * (5 - r) / 5 * pulse)
            _NS_valekris._aacircle(surface,
                                   (*_NS_valekris.PALETTE["cyan_hot"], alpha),
                                   (head_tip_x, head_tip_y), r)
        pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_shine"],
                         (head_tip_x, head_tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_valekris.PALETTE["white"],
                         (head_tip_x, head_tip_y, 1, 1))
    # ============================================================
    # BASIC ATTACK: Spear throw projectile
    # ============================================================
    def _draw_basic_spear_throw(surface, boss, x, y):
        """Cyan spear thrown at target with piercing trail."""
        progress = getattr(boss, "_vlk_attack_progress", 0.0)
        if progress < 0.55:
            return
        facing = boss.direction
        tx, ty = _NS_valekris._target_position(boss, x, y)
        sx, sy = _NS_valekris._spear_hand_position(boss, x, y)
        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        # Position of spear.
        bx = int(sx + (tx - sx) * t)
        by = int(sy + (ty - sy) * t)
        # Spear direction angle.
        dx = tx - sx
        dy = ty - sy
        length = max(1, math.sqrt(dx * dx + dy * dy))
        dir_x = dx / length
        dir_y = dy / length
        perp_x = -dir_y
        perp_y = dir_x
        # Spear shape (elongated, points forward).
        spear_len = 22
        spear_back_x = bx - int(dir_x * spear_len)
        spear_back_y = by - int(dir_y * spear_len)
        # Trail (cyan glow behind).
        for i in range(8):
            trail_t = max(0.0, t - i * 0.05)
            px = int(sx + (tx - sx) * trail_t)
            py = int(sy + (ty - sy) * trail_t)
            alpha = _NS_valekris._alpha(230 - i * 28)
            size = max(1, 5 - i)
            _NS_valekris._aacircle(surface,
                                   (*_NS_valekris.PALETTE["cyan_darkest"], alpha),
                                   (px, py), size + 1)
            _NS_valekris._aacircle(surface,
                                   (*_NS_valekris.PALETTE["cyan_dark"], alpha),
                                   (px, py), size)
            _NS_valekris._aacircle(surface,
                                   (*_NS_valekris.PALETTE["cyan_mid"], alpha),
                                   (px, py), max(1, size - 1))
            _NS_valekris._aacircle(surface,
                                   (*_NS_valekris.PALETTE["cyan_light"], alpha),
                                   (px, py), max(1, size - 3))
        # Spear shaft.
        pygame.draw.line(surface, _NS_valekris.PALETTE["shadow_deep"],
                         (spear_back_x + 1, spear_back_y + 1), (bx + 1, by + 1), 4)
        pygame.draw.line(surface, _NS_valekris.PALETTE["armor_dark"],
                         (spear_back_x, spear_back_y), (bx, by), 3)
        pygame.draw.line(surface, _NS_valekris.PALETTE["cyan_dark"],
                         (spear_back_x, spear_back_y), (bx, by), 2)
        pygame.draw.line(surface, _NS_valekris.PALETTE["cyan_light"],
                         (spear_back_x, spear_back_y), (bx, by), 1)
        # Spear head (bright glowing tip).
        head_ext_x = bx + int(dir_x * 6)
        head_ext_y = by + int(dir_y * 6)
        side_a = (bx + int(perp_x * 3), by + int(perp_y * 3))
        side_b = (bx - int(perp_x * 3), by - int(perp_y * 3))
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["cyan_darkest"], [
            (head_ext_x, head_ext_y), side_a, side_b,
        ])
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["cyan_dark"], [
            (head_ext_x, head_ext_y),
            (int((head_ext_x + side_a[0]) / 2), int((head_ext_y + side_a[1]) / 2)),
            (bx, by),
            (int((head_ext_x + side_b[0]) / 2), int((head_ext_y + side_b[1]) / 2)),
        ])
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["cyan_mid"], [
            (head_ext_x, head_ext_y),
            (int(bx + (head_ext_x - bx) * 0.5),
             int(by + (head_ext_y - by) * 0.5)),
            (bx, by),
        ])
        # Bright glow at tip.
        for r in range(7, 0, -1):
            alpha = _NS_valekris._alpha(120 * (7 - r) / 7)
            _NS_valekris._aacircle(surface,
                                   (*_NS_valekris.PALETTE["cyan_hot"], alpha),
                                   (head_ext_x, head_ext_y), r)
        _NS_valekris._aacircle(surface, _NS_valekris.PALETTE["cyan_shine"],
                               (head_ext_x, head_ext_y), 2)
        pygame.draw.rect(surface, _NS_valekris.PALETTE["white"],
                         (head_ext_x, head_ext_y, 1, 1))
        # Impact burst.
        if t > 0.88:
            st = (t - 0.88) / 0.12
            imp_r = int(10 + st * 15)
            alpha = _NS_valekris._alpha(240 * (1 - st))
            _NS_valekris._aacircle(surface, (*_NS_valekris.PALETTE["cyan_dark"], alpha),
                                   (tx, ty), imp_r + 2, 3)
            _NS_valekris._aacircle(surface, (*_NS_valekris.PALETTE["cyan_mid"], alpha),
                                   (tx, ty), imp_r, 2)
            _NS_valekris._aacircle(surface, (*_NS_valekris.PALETTE["cyan_light"], alpha),
                                   (tx, ty), max(1, imp_r - 6), 1)
            _NS_valekris._aacircle(surface, (*_NS_valekris.PALETTE["cyan_shine"], alpha),
                                   (tx, ty), max(1, imp_r // 3))
            # Radial burst.
            for i in range(8):
                angle_s = i * math.pi / 4
                ex = tx + int(math.cos(angle_s) * imp_r)
                ey = ty + int(math.sin(angle_s) * imp_r * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_valekris.PALETTE["cyan_shine"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        breath = math.sin(phase * 0.8) * 0.15 + 0.85
        shadow = pygame.Surface((130, 24), pygame.SRCALPHA)
        for radius in range(11, 0, -1):
            alpha = max(0, int((11 - radius) * 16 * breath))
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (11 - radius, 12 - radius,
                                 108 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 15, 20, int(160 * breath)),
                            (10, 8, 110, 8))
        surface.blit(shadow, (x - 65, y - 12))
    def _draw_ghost_tendrils(surface, cx, cy, phase):
        """Ghostly wisps rising from below the character."""
        for i in range(8):
            t = (phase * 0.4 + i * 0.13) % 1.0
            dx = cx + int(math.sin(phase + i * 0.7) * 22) - 12 + i * 3
            dy = cy + 30 - int(t * 45)
            alpha = _NS_valekris._alpha(180 * (1 - t))
            if alpha > 0:
                _NS_valekris._aacircle(surface,
                                       (*_NS_valekris.PALETTE["wraith_dark"], alpha),
                                       (dx, dy), 2)
                _NS_valekris._aacircle(surface,
                                       (*_NS_valekris.PALETTE["wraith_mid"], alpha),
                                       (dx, dy - 1), 1)
                pygame.draw.rect(surface, (*_NS_valekris.PALETTE["cyan_light"], alpha),
                                 (dx, dy - 2, 1, 1))
                pygame.draw.rect(surface, (*_NS_valekris.PALETTE["cyan_shine"], alpha),
                                 (dx, dy - 2, 1, 1))
    def _draw_cyan_aura(surface, x, y, phase):
        """Spectral cyan aura around body."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_valekris._alpha((95 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_valekris._aacircle(aura,
                                       (*_NS_valekris.PALETTE["wraith_darkest"], alpha),
                                       (110, 100), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_valekris._alpha((65 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_valekris._aacircle(aura,
                                       (*_NS_valekris.PALETTE["cyan_darkest"], alpha),
                                       (110, 100), radius)
        for radius in range(40, 5, -3):
            alpha = _NS_valekris._alpha((40 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_valekris._aacircle(aura,
                                       (*_NS_valekris.PALETTE["cyan_dark"], alpha),
                                       (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))
        # Floating cyan sparkles orbiting.
        for i in range(14):
            angle = phase * 0.4 + i * math.pi / 7
            radius = 42 + int(math.sin(phase + i) * 14)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_shine"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 56), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_valekris.PALETTE["cyan_darkest"], 200),
                            (5, 18, 170, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_valekris.PALETTE["cyan_dark"], 220),
                            (14, 20, 152, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_valekris.PALETTE["cyan_mid"], 180),
                            (25, 22, 130, 18), 1)
        # Rune spikes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 31 + int(math.sin(angle) * 8)
            x2 = 90 + int(math.cos(angle) * 76)
            y2 = 31 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_valekris.PALETTE["cyan_light"], 220),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.rect(ring, _NS_valekris.PALETTE["cyan_shine"], (x2, y2, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_valekris.PALETTE["cyan_shine"],
                                       _NS_valekris._alpha(160 * pulse)),
                                (15, 12, 150, 42), 1)
        surface.blit(ring, (x - 90, y - 28))
    # ============================================================
    # SKILL Q: PIERCE (big spear that passes through)
    # ============================================================
    def _draw_pierce_projectile(surface, boss, x, y, timer, phase):
        """Massive piercing spear that extends past target."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_valekris._target_position(boss, x, y)
        sx, sy = _NS_valekris._spear_hand_position(boss, x, y)
        if progress < 0.35:
            # Wind-up: charging cyan energy in hand.
            t = progress / 0.35
            cr = int(4 + t * 8)
            for r in range(cr + 6, 0, -2):
                alpha = _NS_valekris._alpha(150 * (cr + 6 - r) / (cr + 6) * t)
                _NS_valekris._aacircle(surface,
                                       (*_NS_valekris.PALETTE["cyan_dark"], alpha),
                                       (sx, sy), r)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_valekris._alpha(200 * (cr + 3 - r) / (cr + 3))
                _NS_valekris._aacircle(surface,
                                       (*_NS_valekris.PALETTE["cyan_mid"], alpha),
                                       (sx, sy), r)
            _NS_valekris._aacircle(surface, _NS_valekris.PALETTE["cyan_light"], (sx, sy), max(1, cr - 2))
            _NS_valekris._aacircle(surface, _NS_valekris.PALETTE["cyan_shine"], (sx, sy), max(1, cr - 5))
            # Sparks converging.
            for i in range(8):
                angle = phase * 4 + i * math.pi / 4
                orbit_r = int(15 * (1 - t))
                sxp = sx + int(math.cos(angle) * orbit_r)
                syp = sy + int(math.sin(angle) * orbit_r)
                pygame.draw.line(surface, _NS_valekris.PALETTE["cyan_light"],
                                 (sxp, syp), (sx, sy), 1)
                pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_shine"], (sxp, syp, 1, 1))
        else:
            # Massive spear traveling and piercing through target.
            t = (progress - 0.35) / 0.65
            t = min(1.0, t)
            # Spear travels PAST target (continues beyond).
            dx = tx - sx
            dy = ty - sy
            length = math.sqrt(dx * dx + dy * dy)
            # Extend 60% beyond target.
            end_x = int(sx + dx * 1.6)
            end_y = int(sy + dy * 1.6)
            # Current tip position.
            bx = int(sx + (end_x - sx) * t)
            by = int(sy + (end_y - sy) * t)
            # Direction.
            if length > 0:
                dir_x = dx / length
                dir_y = dy / length
                perp_x = -dir_y
                perp_y = dir_x
            else:
                dir_x, dir_y = 1, 0
                perp_x, perp_y = 0, 1
            # Spear back position (long spear).
            spear_len = 40
            spear_back_x = bx - int(dir_x * spear_len)
            spear_back_y = by - int(dir_y * spear_len)
            # HUGE cyan trail behind.
            for i in range(12):
                trail_t = max(0.0, t - i * 0.03)
                px = int(sx + (end_x - sx) * trail_t)
                py = int(sy + (end_y - sy) * trail_t)
                alpha = _NS_valekris._alpha(230 - i * 18)
                size = max(1, 8 - i // 2)
                _NS_valekris._aacircle(surface,
                                       (*_NS_valekris.PALETTE["cyan_darkest"], alpha),
                                       (px, py), size + 1)
                _NS_valekris._aacircle(surface,
                                       (*_NS_valekris.PALETTE["cyan_dark"], alpha),
                                       (px, py), size)
                _NS_valekris._aacircle(surface,
                                       (*_NS_valekris.PALETTE["cyan_mid"], alpha),
                                       (px, py), max(1, size - 1))
                _NS_valekris._aacircle(surface,
                                       (*_NS_valekris.PALETTE["cyan_light"], alpha),
                                       (px, py), max(1, size - 3))
                # Sparks.
                if i < 6:
                    for s in range(2):
                        spark_angle = phase * 5 + i + s * math.pi
                        sp_r = size + 2
                        spx = px + int(math.cos(spark_angle) * sp_r)
                        spy = py + int(math.sin(spark_angle) * sp_r)
                        pygame.draw.rect(surface,
                                         (*_NS_valekris.PALETTE["cyan_shine"], alpha),
                                         (spx, spy, 1, 1))
            # BIG spear shaft.
            for width, color in [
                (8, _NS_valekris.PALETTE["cyan_darkest"]),
                (6, _NS_valekris.PALETTE["cyan_dark"]),
                (4, _NS_valekris.PALETTE["cyan_mid"]),
                (2, _NS_valekris.PALETTE["cyan_light"]),
                (1, _NS_valekris.PALETTE["cyan_shine"]),
            ]:
                pygame.draw.line(surface, color,
                                 (spear_back_x, spear_back_y), (bx, by), width)
            # HUGE spear head (crystalline).
            head_ext_x = bx + int(dir_x * 12)
            head_ext_y = by + int(dir_y * 12)
            side_a = (bx + int(perp_x * 6), by + int(perp_y * 6))
            side_b = (bx - int(perp_x * 6), by - int(perp_y * 6))
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["cyan_darkest"], [
                (head_ext_x, head_ext_y), side_a, side_b,
            ])
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["cyan_dark"], [
                (head_ext_x, head_ext_y),
                (int((head_ext_x + side_a[0]) / 2), int((head_ext_y + side_a[1]) / 2)),
                (bx, by),
                (int((head_ext_x + side_b[0]) / 2), int((head_ext_y + side_b[1]) / 2)),
            ])
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["cyan_mid"], [
                (head_ext_x, head_ext_y),
                (int(bx + (head_ext_x - bx) * 0.5),
                 int(by + (head_ext_y - by) * 0.5)),
                (bx, by),
            ])
            pygame.draw.line(surface, _NS_valekris.PALETTE["cyan_shine"],
                             (bx, by), (head_ext_x, head_ext_y), 2)
            # Blinding tip.
            for r in range(10, 0, -2):
                alpha = _NS_valekris._alpha(120 * (10 - r) / 10)
                _NS_valekris._aacircle(surface,
                                       (*_NS_valekris.PALETTE["cyan_hot"], alpha),
                                       (head_ext_x, head_ext_y), r)
            _NS_valekris._aacircle(surface, _NS_valekris.PALETTE["cyan_shine"],
                                   (head_ext_x, head_ext_y), 3)
            _NS_valekris._aacircle(surface, _NS_valekris.PALETTE["white"],
                                   (head_ext_x, head_ext_y), 1)
            # Extra piercing burst when passing target.
            # Check if spear tip past target.
            travel_t = t * 1.6  # since end is 1.6x
            if 0.5 < travel_t < 0.8:
                pierce_t = (travel_t - 0.5) / 0.3
                pierce_r = int(15 * (1 - pierce_t))
                pa = _NS_valekris._alpha(240 * (1 - pierce_t))
                _NS_valekris._aacircle(surface, (*_NS_valekris.PALETTE["cyan_hot"], pa),
                                       (tx, ty), pierce_r + 2, 2)
                _NS_valekris._aacircle(surface, (*_NS_valekris.PALETTE["cyan_shine"], pa),
                                       (tx, ty), max(1, pierce_r), 1)
                for i in range(10):
                    ang = i * math.pi / 5
                    ex = tx + int(math.cos(ang) * pierce_r)
                    ey = ty + int(math.sin(ang) * pierce_r)
                    pygame.draw.rect(surface, (*_NS_valekris.PALETTE["cyan_shine"], pa),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL W: SENTINEL (spectral scout)
    # ============================================================
    def _draw_sentinel_ground(surface, boss, x, y, timer, phase):
        """Ground rune where sentinel will scout."""
        tx, ty = _NS_valekris._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.6:
            # Sentinel arrived - reveal area.
            t = (progress - 0.6) / 0.4
            r = int(35 * t)
            alpha = _NS_valekris._alpha(200 * (1 - t * 0.3))
            pygame.draw.ellipse(surface, (*_NS_valekris.PALETTE["cyan_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_valekris.PALETTE["cyan_mid"], 100),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 1)
            # Runes.
            for i in range(10):
                angle = i * math.pi / 5 + phase * 0.5
                rx = tx + int(math.cos(angle) * r)
                ry = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_light"], (rx, ry, 2, 2))
                pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_shine"], (rx, ry, 1, 1))
    def _draw_sentinel_projectile(surface, boss, x, y, timer, phase):
        """Ghost/skull face flying to target."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_valekris._target_position(boss, x, y)
        sx, sy = _NS_valekris._spear_hand_position(boss, x, y)
        if progress < 0.3:
            # Charge/summon at hand.
            t = progress / 0.3
            cr = int(4 + t * 6)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_valekris._alpha(180 * (cr + 4 - r) / (cr + 4))
                _NS_valekris._aacircle(surface,
                                       (*_NS_valekris.PALETTE["cyan_mid"], alpha),
                                       (sx, sy), r)
            _NS_valekris._aacircle(surface, _NS_valekris.PALETTE["cyan_light"], (sx, sy), max(1, cr - 1))
            _NS_valekris._aacircle(surface, _NS_valekris.PALETTE["cyan_shine"], (sx, sy), max(1, cr - 3))
        elif progress < 0.6:
            # Sentinel flying to target.
            t = (progress - 0.3) / 0.3
            bx = int(sx + (tx - sx) * t)
            by = int(sy + (ty - sy) * t) - int(math.sin(t * math.pi) * 10)  # slight arc
            # Trail.
            for i in range(6):
                trail_t = max(0.0, t - i * 0.06)
                px = int(sx + (tx - sx) * trail_t)
                py = int(sy + (ty - sy) * trail_t) - int(math.sin(trail_t * math.pi) * 10)
                alpha = _NS_valekris._alpha(180 - i * 25)
                _NS_valekris._aacircle(surface,
                                       (*_NS_valekris.PALETTE["cyan_dark"], alpha),
                                       (px, py), max(1, 5 - i))
                _NS_valekris._aacircle(surface,
                                       (*_NS_valekris.PALETTE["cyan_mid"], alpha),
                                       (px, py), max(1, 3 - i))
            # Draw ghost skull face.
            _NS_valekris._draw_ghost_face(surface, bx, by, phase)
        else:
            # At target: eye/rune revealing area.
            t = (progress - 0.6) / 0.4
            # Draw the eye at target.
            eye_pulse = math.sin(phase * 3) * 0.3 + 0.7
            for r in range(10, 0, -1):
                alpha = _NS_valekris._alpha(140 * (10 - r) / 10 * eye_pulse)
                _NS_valekris._aacircle(surface,
                                       (*_NS_valekris.PALETTE["cyan_mid"], alpha),
                                       (tx, ty - 4), r)
            # Eye shape.
            _NS_valekris._poly(surface, _NS_valekris.PALETTE["cyan_dark"], [
                (tx - 6, ty - 4),
                (tx - 3, ty - 7),
                (tx + 3, ty - 7),
                (tx + 6, ty - 4),
                (tx + 3, ty - 1),
                (tx - 3, ty - 1),
            ])
            _NS_valekris._aacircle(surface, _NS_valekris.PALETTE["cyan_darkest"], (tx, ty - 4), 3)
            _NS_valekris._aacircle(surface, _NS_valekris.PALETTE["cyan_light"], (tx, ty - 4), 2)
            _NS_valekris._aacircle(surface, _NS_valekris.PALETTE["cyan_shine"], (tx, ty - 4), 1)
            pygame.draw.rect(surface, _NS_valekris.PALETTE["white"], (tx, ty - 4, 1, 1))
    def _draw_ghost_face(surface, cx, cy, phase):
        """Small ghost skull face."""
        # Ghostly aura.
        for r in range(8, 0, -1):
            alpha = _NS_valekris._alpha(80 * (8 - r) / 8)
            _NS_valekris._aacircle(surface,
                                   (*_NS_valekris.PALETTE["cyan_mid"], alpha),
                                   (cx, cy), r)
        # Skull face outline.
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["cyan_dark"], [
            (cx - 4, cy - 2),
            (cx - 3, cy - 5),
            (cx + 3, cy - 5),
            (cx + 4, cy - 2),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
        ])
        _NS_valekris._poly(surface, _NS_valekris.PALETTE["cyan_darkest"], [
            (cx - 3, cy - 1),
            (cx - 2, cy - 4),
            (cx + 2, cy - 4),
            (cx + 3, cy - 1),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2),
        ])
        # Eyes.
        pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_shine"], (cx - 2, cy - 2, 1, 1))
        pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_shine"], (cx + 1, cy - 2, 1, 1))
        pygame.draw.rect(surface, _NS_valekris.PALETTE["white"], (cx - 2, cy - 2, 1, 1))
        pygame.draw.rect(surface, _NS_valekris.PALETTE["white"], (cx + 1, cy - 2, 1, 1))
        # Wispy tail behind.
        for i in range(4):
            t = (phase * 0.5 + i * 0.2) % 1.0
            wx = cx + int(math.sin(phase + i) * 2)
            wy = cy + 3 + int(t * 6)
            alpha = _NS_valekris._alpha(180 * (1 - t))
            pygame.draw.rect(surface, (*_NS_valekris.PALETTE["cyan_mid"], alpha), (wx, wy, 1, 1))
    # ============================================================
    # SKILL E: REND (multi-spear extraction burst)
    # ============================================================
    def _draw_rend_burst(surface, boss, x, y, timer, phase):
        """Multiple spears exploding out of target."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_valekris._target_position(boss, x, y)
        sx, sy = _NS_valekris._spear_hand_position(boss, x, y)
        if progress < 0.4:
            # Gesture: cyan energy flowing from boss hand to target.
            t = progress / 0.4
            for i in range(8):
                trail_t = ((phase * 2 + i * 0.12) % 1.0)
                px = int(sx + (tx - sx) * trail_t)
                py = int(sy + (ty - sy) * trail_t)
                alpha = _NS_valekris._alpha(200 * t)
                pygame.draw.rect(surface, (*_NS_valekris.PALETTE["cyan_shine"], alpha),
                                 (px, py, 2, 2))
                pygame.draw.rect(surface, (*_NS_valekris.PALETTE["white"], alpha), (px, py, 1, 1))
        else:
            # BURST: many spears exploding outward from target.
            t = (progress - 0.4) / 0.6
            intensity = math.sin(t * math.pi)
            # 8 spears radiating out from target.
            num_spears = 8
            for i in range(num_spears):
                angle = i * math.pi * 2 / num_spears + phase * 0.5
                spear_travel = 30 * min(1.0, t * 2)
                # Spear starts at target and travels outward.
                sp_end_x = tx + int(math.cos(angle) * spear_travel)
                sp_end_y = ty + int(math.sin(angle) * spear_travel)
                sp_back_x = tx + int(math.cos(angle) * (spear_travel - 15))
                sp_back_y = ty + int(math.sin(angle) * (spear_travel - 15))
                alpha = _NS_valekris._alpha(230 * intensity)
                # Spear shaft.
                pygame.draw.line(surface, (*_NS_valekris.PALETTE["cyan_darkest"], alpha),
                                 (sp_back_x, sp_back_y), (sp_end_x, sp_end_y), 4)
                pygame.draw.line(surface, (*_NS_valekris.PALETTE["cyan_dark"], alpha),
                                 (sp_back_x, sp_back_y), (sp_end_x, sp_end_y), 3)
                pygame.draw.line(surface, (*_NS_valekris.PALETTE["cyan_mid"], alpha),
                                 (sp_back_x, sp_back_y), (sp_end_x, sp_end_y), 2)
                pygame.draw.line(surface, (*_NS_valekris.PALETTE["cyan_light"], alpha),
                                 (sp_back_x, sp_back_y), (sp_end_x, sp_end_y), 1)
                # Spear tip glow.
                _NS_valekris._aacircle(surface, (*_NS_valekris.PALETTE["cyan_hot"], alpha),
                                       (sp_end_x, sp_end_y), 3)
                _NS_valekris._aacircle(surface, (*_NS_valekris.PALETTE["cyan_shine"], alpha),
                                       (sp_end_x, sp_end_y), 2)
                pygame.draw.rect(surface, (*_NS_valekris.PALETTE["white"], alpha),
                                 (sp_end_x, sp_end_y, 1, 1))
            # Central burst at target.
            burst_r = int(12 + t * 15)
            alpha_b = _NS_valekris._alpha(240 * intensity)
            _NS_valekris._aacircle(surface, (*_NS_valekris.PALETTE["cyan_dark"], alpha_b),
                                   (tx, ty), burst_r + 2, 3)
            _NS_valekris._aacircle(surface, (*_NS_valekris.PALETTE["cyan_mid"], alpha_b),
                                   (tx, ty), burst_r, 2)
            _NS_valekris._aacircle(surface, (*_NS_valekris.PALETTE["cyan_light"], alpha_b),
                                   (tx, ty), max(1, burst_r - 5), 1)
            _NS_valekris._aacircle(surface, (*_NS_valekris.PALETTE["cyan_shine"], alpha_b),
                                   (tx, ty), max(1, burst_r // 3))
            pygame.draw.rect(surface, _NS_valekris.PALETTE["white"], (tx - 1, ty - 1, 2, 2))
    # ============================================================
    # SKILL R: FATE'S CALL (spectral binding tether)
    # ============================================================
    def _draw_fatescall_ground(surface, boss, x, y, timer, phase):
        """Ground marker at target being bound."""
        tx, ty = _NS_valekris._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Ground rune at target throughout duration.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        r = 22
        alpha = _NS_valekris._alpha(200 * pulse)
        pygame.draw.ellipse(surface, (*_NS_valekris.PALETTE["cyan_dark"], alpha),
                            (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
        pygame.draw.ellipse(surface, (*_NS_valekris.PALETTE["cyan_mid"], alpha),
                            (tx - r + 3, ty - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 2)
        # Runes rotating.
        for i in range(6):
            angle = i * math.pi / 3 + phase * 0.8
            rx = tx + int(math.cos(angle) * r)
            ry = ty + int(math.sin(angle) * r * 0.4)
            pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_light"], (rx, ry, 2, 2))
            pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_shine"], (rx, ry, 1, 1))
        # Ground rune at boss too.
        r_b = 20
        pygame.draw.ellipse(surface, (*_NS_valekris.PALETTE["cyan_dark"], alpha),
                            (x - r_b, y + 45 - r_b // 3, r_b * 2, r_b * 2 // 3), 2)
        for i in range(5):
            angle = i * math.pi / 2.5 + phase * 0.8
            rx = x + int(math.cos(angle) * r_b)
            ry = y + 45 + int(math.sin(angle) * r_b * 0.4)
            pygame.draw.rect(surface, _NS_valekris.PALETTE["cyan_shine"], (rx, ry, 1, 1))
    def _draw_fatescall_tether(surface, boss, x, y, timer, phase):
        """Cyan binding tether from boss to target."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_valekris._target_position(boss, x, y)
        sx, sy = _NS_valekris._spear_hand_position(boss, x, y)
        # Chain of cyan energy connecting hand to target.
        segments = 20
        prev = (sx, sy)
        for i in range(1, segments + 1):
            t = i / segments
            base_x = int(sx + (tx - sx) * t)
            base_y = int(sy + (ty - sy) * t)
            # Wavy energy.
            dx = tx - sx
            dy = ty - sy
            length = max(1, math.sqrt(dx * dx + dy * dy))
            perp_x = -dy / length
            perp_y = dx / length
            wave = math.sin(phase * 5 + t * 10) * 6
            px = base_x + int(perp_x * wave)
            py = base_y + int(perp_y * wave)
            # Multi-layer tether.
            for width, color in [
                (5, _NS_valekris.PALETTE["cyan_darkest"]),
                (3, _NS_valekris.PALETTE["cyan_dark"]),
                (2, _NS_valekris.PALETTE["cyan_mid"]),
                (1, _NS_valekris.PALETTE["cyan_light"]),
            ]:
                pygame.draw.line(surface, color, prev, (px, py), width)
            prev = (px, py)
        # Ghost skulls flowing along tether (toward caster).
        for i in range(5):
            flow_t = ((phase * 0.6 + i * 0.2) % 1.0)
            t = 1.0 - flow_t
            base_x = int(sx + (tx - sx) * t)
            base_y = int(sy + (ty - sy) * t)
            dx = tx - sx
            dy = ty - sy
            length = max(1, math.sqrt(dx * dx + dy * dy))
            perp_x = -dy / length
            perp_y = dx / length
            wave = math.sin(phase * 5 + t * 10) * 6
            px = base_x + int(perp_x * wave)
            py = base_y + int(perp_y * wave)
            _NS_valekris._draw_ghost_face(surface, px, py, phase)
        # Anchor glow at both ends.
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for anchor in [(sx, sy), (tx, ty)]:
            for r in range(10, 0, -1):
                alpha = _NS_valekris._alpha(120 * (10 - r) / 10 * pulse)
                _NS_valekris._aacircle(surface,
                                       (*_NS_valekris.PALETTE["cyan_mid"], alpha),
                                       anchor, r)
            _NS_valekris._aacircle(surface, _NS_valekris.PALETTE["cyan_light"], anchor, 3)
            _NS_valekris._aacircle(surface, _NS_valekris.PALETTE["cyan_shine"], anchor, 1)
            pygame.draw.rect(surface, _NS_valekris.PALETTE["white"], (anchor[0], anchor[1], 1, 1))



# ====================================================================
# ZHARAKZUUL (VOIDBOUND SOVEREIGN) - TRUE BOSS
# ====================================================================

class _NS_zharakzuul:
    """Namespace zharakzuul - true boss void sage."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Pale purple-lilac skin
        "skin_darkest": (35, 20, 55),
        "skin_dark": (85, 65, 110),
        "skin_mid": (155, 130, 180),
        "skin_light": (210, 190, 225),
        "skin_shine": (245, 230, 250),
        # White hair/beard (bright silver-white)
        "hair_darkest": (60, 55, 75),
        "hair_dark": (130, 125, 150),
        "hair_mid": (200, 200, 220),
        "hair_light": (240, 240, 250),
        "hair_shine": (255, 255, 255),
        # Dark purple robe (main outfit)
        "robe_darkest": (15, 8, 30),
        "robe_dark": (35, 20, 60),
        "robe_mid": (70, 40, 110),
        "robe_light": (125, 85, 175),
        "robe_shine": (185, 145, 225),
        # Void purple (magic, sword, aura - vibrant magenta)
        "void_darkest": (25, 5, 45),
        "void_dark": (85, 20, 145),
        "void_mid": (175, 55, 235),
        "void_light": (225, 130, 255),
        "void_hot": (245, 200, 255),
        "void_shine": (255, 240, 255),
        # Gold trim
        "gold_darkest": (60, 40, 10),
        "gold_dark": (120, 85, 20),
        "gold_mid": (210, 165, 55),
        "gold_light": (250, 220, 110),
        "gold_shine": (255, 245, 190),
        # Cyan-white eyes (empty spectral)
        "eye_socket": (5, 5, 15),
        "eye_dark": (30, 60, 100),
        "eye_mid": (100, 200, 240),
        "eye_light": (200, 245, 255),
        "eye_glow": (250, 255, 255),
        # Void crystals (background gems, sword crystal)
        "crystal_dark": (55, 15, 105),
        "crystal_mid": (155, 60, 220),
        "crystal_light": (215, 145, 250),
        # Red belt gem accent
        "gem_dark": (85, 15, 30),
        "gem_mid": (190, 40, 60),
        "gem_light": (255, 130, 130),
        "shadow": (0, 0, 0),
        "shadow_deep": (3, 2, 8),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_zharakzuul._clamp(color)
        if _NS_zharakzuul.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_zharakzuul._clamp(color)
        if _NS_zharakzuul.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_zharakzuul._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 240 * getattr(boss, "direction", 1)), int(y)
    def _arm_elbow(shoulder, hand, bend=4, bend_up=False):
        sx, sy = shoulder
        hx, hy = hand
        mid_x = (sx + hx) / 2
        mid_y = (sy + hy) / 2
        dx = hx - sx
        dy = hy - sy
        length = max(1.0, math.sqrt(dx * dx + dy * dy))
        perp_x = -dy / length
        perp_y = dx / length
        if bend_up:
            if perp_y > 0:
                perp_x = -perp_x
                perp_y = -perp_y
        else:
            if perp_y < 0:
                perp_x = -perp_x
                perp_y = -perp_y
        return (int(mid_x + perp_x * bend), int(mid_y + perp_y * bend))
    def _blade_hand_position(boss, x, y):
        """Position of front hand holding void blade."""
        facing = boss.direction
        active = getattr(boss, "_zk_attack_active", False)
        progress = getattr(boss, "_zk_attack_progress", 0.0)
        skill = getattr(boss, "active_skill", None)
        if skill == "q":
            # Meditation pose - hands together in front.
            return x, y - 6
        elif active or skill == "w":
            # Sword swing/throw animation.
            if progress < 0.3:
                # Wind up (raised behind).
                t = progress / 0.3
                hx = x + facing * int(4 - t * 8)
                hy = y - int(14 + t * 6)
            elif progress < 0.5:
                # Swing forward.
                t = (progress - 0.3) / 0.2
                hx = x + facing * int(-4 + t * 28)
                hy = y - 20 + int(t * 14)
            elif progress < 0.75:
                # Hold extended.
                hx = x + facing * 24
                hy = y - 6
            else:
                # Return.
                t = (progress - 0.75) / 0.25
                hx = x + facing * int(24 - t * 16)
                hy = y - 6 - int(t * 6)
        else:
            hx = x + facing * 12
            hy = y - 8
        return hx, hy
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_zharakzuul(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_zharakzuul._update_attack_anim(boss)
        attack_progress = getattr(boss, "_zk_attack_progress", 0.0)
        attacking = (
            getattr(boss, "_zk_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 55) - 15
        )
        # Ambient FX (BIG for TRUE BOSS).
        _NS_zharakzuul._draw_void_aura(surface, x, y, pulse)
        _NS_zharakzuul._draw_ground_ring(surface, x, y + 54, pulse, active_skill)
        # Skill ground FX.
        if active_skill == "e":
            _NS_zharakzuul._draw_pulse_rings_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zharakzuul._draw_resonant_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_zharakzuul._draw_meditation_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating body (dramatic float since he's a void mystic).
        float_bob = math.sin(pulse * 0.7) * 6
        body_y = y + int(float_bob)
        # Void particles rising from below.
        _NS_zharakzuul._draw_void_particles(surface, x, body_y + 40, pulse)
        # Body pose.
        if active_skill == "q":
            _NS_zharakzuul._draw_body_meditate(surface, boss, x, body_y,
                                                skill_timer, pulse)
        elif active_skill == "w":
            _NS_zharakzuul._draw_body_wthrow(surface, boss, x, body_y,
                                              skill_timer, pulse)
        elif active_skill == "e":
            _NS_zharakzuul._draw_body_pulse(surface, boss, x, body_y,
                                             skill_timer, pulse)
        elif active_skill == "r":
            _NS_zharakzuul._draw_body_resonant(surface, boss, x, body_y,
                                                skill_timer, pulse)
        elif attacking:
            _NS_zharakzuul._draw_body_attack(surface, boss, x, body_y)
        else:
            _NS_zharakzuul._draw_body_idle(surface, boss, x, body_y)
        # Foreground FX.
        if active_skill == "q":
            _NS_zharakzuul._draw_aether_remedy_fx(surface, boss, x, body_y,
                                                   skill_timer, pulse)
        elif active_skill == "w":
            _NS_zharakzuul._draw_voidsling_projectile(surface, boss, x, body_y,
                                                       skill_timer, pulse)
        elif active_skill == "e":
            _NS_zharakzuul._draw_pulse_rings(surface, boss, x, body_y,
                                              skill_timer, pulse)
        elif active_skill == "r":
            _NS_zharakzuul._draw_resonant_pulse_fx(surface, boss, x, body_y,
                                                     skill_timer, pulse)
        else:
            if attacking and attack_progress > 0:
                _NS_zharakzuul._draw_basic_slash_fx(surface, boss, x, body_y)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 55)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_zk_attack_active", False))
        if not active and timer >= cooldown - 2:
            boss._zk_attack_active = True
            boss._zk_attack_frame = 0
            active = True
        elif active:
            boss._zk_attack_frame = int(getattr(boss, "_zk_attack_frame", 0)) + 1
            if boss._zk_attack_frame >= cooldown:
                boss._zk_attack_active = False
                boss._zk_attack_frame = 0
                active = False
        boss._zk_previous_timer = timer
        boss._zk_attack_progress = (
            min(1.0, getattr(boss, "_zk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, cx, cy):
        _NS_zharakzuul._draw_float_shadow(surface, cx, cy + 56, boss.pulse)
        _NS_zharakzuul._draw_body(surface, boss, cx, cy, "idle", 0)
    def _draw_body_attack(surface, boss, cx, cy):
        progress = getattr(boss, "_zk_attack_progress", 0.0)
        _NS_zharakzuul._draw_float_shadow(surface, cx, cy + 56, boss.pulse)
        _NS_zharakzuul._draw_body(surface, boss, cx, cy, "slash", progress)
    def _draw_body_meditate(surface, boss, cx, cy, timer, phase):
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_zharakzuul._draw_float_shadow(surface, cx, cy + 56, phase)
        _NS_zharakzuul._draw_body(surface, boss, cx, cy - 6, "meditate", progress)
    def _draw_body_wthrow(surface, boss, cx, cy, timer, phase):
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_zharakzuul._draw_float_shadow(surface, cx, cy + 56, phase)
        _NS_zharakzuul._draw_body(surface, boss, cx, cy, "throw", progress)
    def _draw_body_pulse(surface, boss, cx, cy, timer, phase):
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_zharakzuul._draw_float_shadow(surface, cx, cy + 56, phase)
        _NS_zharakzuul._draw_body(surface, boss, cx, cy, "pulse", progress)
    def _draw_body_resonant(surface, boss, cx, cy, timer, phase):
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_zharakzuul._draw_float_shadow(surface, cx, cy + 56, phase)
        _NS_zharakzuul._draw_body(surface, boss, cx, cy, "resonant", progress)
    # ============================================================
    # MAIN BODY
    # ============================================================
    def _draw_body(surface, boss, cx, cy, action, progress):
        facing = boss.direction
        phase = boss.pulse
        # Robe backdrop (flowing behind).
        _NS_zharakzuul._draw_robe_back(surface, cx, cy, facing, phase, action)
        # Robe lower body (long flowing).
        _NS_zharakzuul._draw_robe_bottom(surface, cx, cy, facing, phase, action)
        # Torso.
        _NS_zharakzuul._draw_torso(surface, cx, cy, facing, phase)
        # Hair back layer.
        _NS_zharakzuul._draw_hair_back(surface, cx, cy - 24, facing, phase)
        # Head with elder face.
        _NS_zharakzuul._draw_head(surface, cx, cy - 26, facing, phase, action, progress)
        # Arms with void blade (meditation shows hands differently).
        _NS_zharakzuul._draw_arms(surface, cx, cy, facing, phase, action, progress)
    def _draw_robe_back(surface, cx, cy, facing, phase, action):
        """Dark purple robe backdrop flowing behind."""
        sway = math.sin(phase * 0.5) * 3
        robe_pts = [
            (cx - facing * 4, cy - 18),
            (cx - facing * 14 + int(sway), cy - 8),
            (cx - facing * 20 + int(sway), cy + 4),
            (cx - facing * 22 + int(sway * 1.2), cy + 18),
            (cx - facing * 18 + int(sway), cy + 32),
            (cx - facing * 10, cy + 40),
            (cx + facing * 2, cy + 34),
            (cx + facing * 4, cy + 8),
            (cx + facing * 2, cy - 14),
        ]
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["shadow_deep"],
                             [(p[0] + 2, p[1] + 3) for p in robe_pts])
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["robe_darkest"], robe_pts)
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["robe_dark"], [
            (cx - facing * 3, cy - 17),
            (cx - facing * 12 + int(sway), cy - 6),
            (cx - facing * 18 + int(sway), cy + 4),
            (cx - facing * 20 + int(sway * 1.2), cy + 16),
            (cx - facing * 16 + int(sway), cy + 30),
            (cx - facing * 8, cy + 36),
            (cx + facing * 1, cy + 30),
            (cx + facing * 3, cy + 8),
            (cx + facing * 1, cy - 12),
        ])
        # Gold trim edges.
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["gold_dark"],
                         (cx - facing * 4, cy - 18),
                         (cx - facing * 14 + int(sway), cy - 8), 1)
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["gold_mid"],
                         (cx - facing * 14 + int(sway), cy - 8),
                         (cx - facing * 20 + int(sway), cy + 4), 1)
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["gold_dark"],
                         (cx - facing * 20 + int(sway), cy + 4),
                         (cx - facing * 18 + int(sway), cy + 32), 1)
    def _draw_robe_bottom(surface, cx, cy, facing, phase, action):
        """Long flowing robe from waist down (no legs visible - floating)."""
        sway = math.sin(phase * 0.6) * 3
        # Multiple flowing strands.
        for i, x_off in enumerate((-10, -4, 0, 4, 10)):
            wave = math.sin(phase * 0.6 + i * 0.4) * 3
            strand_pts = [
                (cx + x_off + int(sway * 0.4) - 3, cy + 6),
                (cx + x_off + int(sway * 0.4) + 3, cy + 6),
                (cx + x_off + int(wave) + 5, cy + 22),
                (cx + x_off + int(wave * 1.3) + 3, cy + 38),
                (cx + x_off + int(wave * 1.5), cy + 50),
                (cx + x_off + int(wave * 1.3) - 3, cy + 38),
                (cx + x_off + int(wave) - 5, cy + 22),
            ]
            _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["shadow_deep"],
                                 [(p[0] + 1, p[1] + 2) for p in strand_pts])
            _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["robe_darkest"], strand_pts)
            _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["robe_dark"], [
                (cx + x_off + int(sway * 0.4) - 2, cy + 7),
                (cx + x_off + int(sway * 0.4) + 2, cy + 7),
                (cx + x_off + int(wave) + 4, cy + 22),
                (cx + x_off + int(wave * 1.3) + 2, cy + 36),
                (cx + x_off + int(wave * 1.5), cy + 48),
                (cx + x_off + int(wave * 1.3) - 2, cy + 36),
                (cx + x_off + int(wave) - 4, cy + 22),
            ])
            _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["robe_mid"], [
                (cx + x_off + int(sway * 0.4) - 1, cy + 8),
                (cx + x_off + int(sway * 0.4) + 1, cy + 8),
                (cx + x_off + int(wave) + 2, cy + 22),
                (cx + x_off + int(wave * 1.3), cy + 32),
                (cx + x_off + int(wave) - 2, cy + 22),
            ])
            # Gold trim at bottom of strand.
            tip_x = cx + x_off + int(wave * 1.5)
            tip_y = cy + 50
            pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_dark"], (tip_x - 1, tip_y, 3, 1))
            pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_mid"], (tip_x, tip_y, 1, 1))
    def _draw_torso(surface, cx, cy, facing, phase):
        """Robed torso with gold ornaments."""
        breath = math.sin(phase * 0.5) * 1
        torso_pts = [
            (cx - 12, cy - 15),
            (cx - 14, cy - 6),
            (cx - 12, cy + 4),
            (cx - 8, cy + 10),
            (cx + 8, cy + 10),
            (cx + 12, cy + 4),
            (cx + 14, cy - 6),
            (cx + 12, cy - 15),
            (cx + 6, cy - 20),
            (cx - 6, cy - 20),
        ]
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["shadow_deep"],
                             [(p[0] + 1, p[1] + 2) for p in torso_pts])
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["robe_darkest"], torso_pts)
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["robe_dark"], [
            (cx - 11, cy - 14),
            (cx - 13, cy - 6),
            (cx - 11, cy + 3),
            (cx - 7, cy + 9),
            (cx + 7, cy + 9),
            (cx + 11, cy + 3),
            (cx + 13, cy - 6),
            (cx + 11, cy - 14),
            (cx + 5, cy - 19),
            (cx - 5, cy - 19),
        ])
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["robe_mid"], [
            (cx - 9, cy - 10),
            (cx - 11, cy - 4),
            (cx - 7, cy + 4),
            (cx + 7, cy + 4),
            (cx + 11, cy - 4),
            (cx + 9, cy - 10),
            (cx + 4, cy - 15),
            (cx - 4, cy - 15),
        ])
        # Center chest V-line.
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["robe_darkest"], [
            (cx, cy - 18),
            (cx - 4, cy - 12),
            (cx, cy - 6),
            (cx + 4, cy - 12),
        ])
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["robe_dark"], [
            (cx, cy - 17),
            (cx - 3, cy - 12),
            (cx, cy - 7),
            (cx + 3, cy - 12),
        ])
        # Gold necklace/chain.
        for i, y_off in enumerate((-16, -13)):
            pygame.draw.line(surface, _NS_zharakzuul.PALETTE["gold_dark"],
                             (cx - 6, cy + y_off), (cx + 6, cy + y_off), 1)
            pygame.draw.line(surface, _NS_zharakzuul.PALETTE["gold_mid"],
                             (cx - 5, cy + y_off), (cx + 5, cy + y_off), 1)
        # Big red gem pendant on chest.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        gem_x = cx
        gem_y = cy - 10
        for r in range(6, 0, -1):
            alpha = _NS_zharakzuul._alpha(120 * (6 - r) / 6 * pulse)
            _NS_zharakzuul._aacircle(surface,
                                     (*_NS_zharakzuul.PALETTE["gem_mid"], alpha),
                                     (gem_x, gem_y), r)
        # Gold setting.
        _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["gold_dark"], (gem_x, gem_y), 4)
        _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["gold_mid"], (gem_x, gem_y), 3)
        # Gem.
        _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["gem_dark"], (gem_x, gem_y), 2)
        _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["gem_mid"], (gem_x, gem_y), 1)
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gem_light"], (gem_x, gem_y, 1, 1))
        # Gold belt.
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_darkest"],
                         (cx - 12, cy + 5, 24, 6))
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_dark"],
                         (cx - 11, cy + 5, 22, 5))
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_mid"],
                         (cx - 10, cy + 6, 20, 3))
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_light"],
                         (cx - 9, cy + 7, 18, 1))
        # Belt central buckle with void gem.
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_darkest"],
                         (cx - 4, cy + 5, 8, 6))
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_mid"],
                         (cx - 3, cy + 6, 6, 4))
        # Void gem in buckle.
        _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["void_darkest"],
                                 (cx, cy + 8), 2)
        _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["void_mid"],
                                 (cx, cy + 8), 1)
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["void_shine"], (cx, cy + 8, 1, 1))
        # Shoulder pauldrons.
        for side in (-1, 1):
            base_x = cx + side * 12
            paul_pts = [
                (base_x - side, cy - 18),
                (base_x + side * 3, cy - 19),
                (base_x + side * 5, cy - 12),
                (base_x + side * 2, cy - 10),
                (base_x - side, cy - 12),
            ]
            _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["gold_darkest"], paul_pts)
            _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["gold_dark"], [
                (base_x, cy - 18),
                (base_x + side * 3, cy - 18),
                (base_x + side * 4, cy - 12),
                (base_x + side, cy - 11),
            ])
            _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["gold_mid"], [
                (base_x + side, cy - 17),
                (base_x + side * 3, cy - 16),
                (base_x + side * 3, cy - 13),
                (base_x + side, cy - 12),
            ])
            pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_light"],
                             (base_x + side * 2, cy - 16, 1, 1))
            pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_shine"],
                             (base_x + side * 2, cy - 16, 1, 1))
    def _draw_hair_back(surface, cx, cy, facing, phase):
        """Long white hair flowing behind."""
        sway = math.sin(phase * 0.5) * 2
        hair_pts = [
            (cx - 7, cy),
            (cx - 11 + int(sway), cy + 6),
            (cx - 13 + int(sway), cy + 16),
            (cx - 12 + int(sway * 1.2), cy + 26),
            (cx - 8 + int(sway), cy + 34),
            (cx - 3, cy + 36),
            (cx + 3, cy + 36),
            (cx + 8 - int(sway), cy + 34),
            (cx + 12 - int(sway * 1.2), cy + 26),
            (cx + 13 - int(sway), cy + 16),
            (cx + 11 - int(sway), cy + 6),
            (cx + 7, cy),
        ]
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["shadow_deep"],
                             [(p[0] + 1, p[1] + 2) for p in hair_pts])
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["hair_darkest"], hair_pts)
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["hair_dark"], [
            (cx - 6, cy),
            (cx - 10 + int(sway), cy + 6),
            (cx - 11 + int(sway), cy + 16),
            (cx - 10 + int(sway * 1.2), cy + 24),
            (cx - 6 + int(sway), cy + 32),
            (cx + 6 - int(sway), cy + 32),
            (cx + 10 - int(sway * 1.2), cy + 24),
            (cx + 11 - int(sway), cy + 16),
            (cx + 10 - int(sway), cy + 6),
            (cx + 6, cy),
        ])
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["hair_mid"], [
            (cx - 5, cy),
            (cx - 8 + int(sway), cy + 8),
            (cx - 8 + int(sway), cy + 20),
            (cx - 4 + int(sway), cy + 28),
            (cx + 4 - int(sway), cy + 28),
            (cx + 8 - int(sway), cy + 20),
            (cx + 8 - int(sway), cy + 8),
            (cx + 5, cy),
        ])
        # Light hair strands.
        for i, x_off in enumerate((-7, -3, 0, 3, 7)):
            strand_x = cx + x_off + int(sway * 0.5)
            strand_top_y = cy + 4
            strand_bot_y = cy + 30 - i
            pygame.draw.line(surface, _NS_zharakzuul.PALETTE["hair_light"],
                             (strand_x, strand_top_y),
                             (strand_x + int(sway), strand_bot_y), 1)
        # Sheen.
        for x_off in (-4, 0, 4):
            pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["hair_shine"],
                             (cx + x_off + int(sway * 0.3), cy + 8, 1, 1))
    def _draw_head(surface, cx, cy, facing, phase, action, progress):
        """Elder head with white hair, beard, glowing eyes."""
        # Face.
        face_pts = [
            (cx - 7, cy - 2),
            (cx - 8, cy + 2),
            (cx - 7, cy + 6),
            (cx - 4, cy + 10),
            (cx + 4, cy + 10),
            (cx + 7, cy + 6),
            (cx + 8, cy + 2),
            (cx + 7, cy - 2),
            (cx + 4, cy - 6),
            (cx - 4, cy - 6),
        ]
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["shadow_deep"],
                             [(p[0] + 1, p[1] + 2) for p in face_pts])
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["skin_darkest"], face_pts)
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["skin_dark"], [
            (cx - 6, cy - 1),
            (cx - 7, cy + 2),
            (cx - 6, cy + 5),
            (cx - 3, cy + 9),
            (cx + 3, cy + 9),
            (cx + 6, cy + 5),
            (cx + 7, cy + 2),
            (cx + 6, cy - 1),
            (cx + 3, cy - 5),
            (cx - 3, cy - 5),
        ])
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["skin_mid"], [
            (cx - 4, cy),
            (cx - 5, cy + 3),
            (cx - 3, cy + 6),
            (cx + 3, cy + 6),
            (cx + 5, cy + 3),
            (cx + 4, cy),
        ])
        # Cheek highlights.
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["skin_light"], (cx - 4, cy + 1, 1, 1))
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["skin_light"], (cx + 3, cy + 1, 1, 1))
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["skin_shine"], (cx - 4, cy + 1, 1, 1))
        # Sunken elder eyes (wrinkle lines).
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["skin_darkest"],
                         (cx - 5, cy - 1), (cx - 3, cy - 1), 1)
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["skin_darkest"],
                         (cx + 3, cy - 1), (cx + 5, cy - 1), 1)
        # WHITE BEARD (long).
        _NS_zharakzuul._draw_beard(surface, cx, cy + 8, facing, phase)
        # Glowing white-cyan eyes.
        _NS_zharakzuul._draw_elder_eyes(surface, cx, cy, phase, action)
        # Nose.
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["skin_darkest"], (cx, cy + 3, 1, 2))
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["skin_dark"], (cx, cy + 3, 1, 1))
        # HEADBAND / crown-like accessory.
        _NS_zharakzuul._draw_headband(surface, cx, cy - 4, facing, phase)
    def _draw_beard(surface, cx, cy, facing, phase):
        """Long white flowing beard."""
        sway = math.sin(phase * 0.5) * 1
        beard_pts = [
            (cx - 5, cy - 2),
            (cx - 6 + int(sway), cy + 2),
            (cx - 5 + int(sway), cy + 8),
            (cx - 3 + int(sway * 1.2), cy + 14),
            (cx, cy + 16),
            (cx + 3 - int(sway * 1.2), cy + 14),
            (cx + 5 - int(sway), cy + 8),
            (cx + 6 - int(sway), cy + 2),
            (cx + 5, cy - 2),
        ]
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["shadow_deep"],
                             [(p[0] + 1, p[1] + 1) for p in beard_pts])
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["hair_dark"], beard_pts)
        _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["hair_mid"], [
            (cx - 4, cy - 1),
            (cx - 5 + int(sway), cy + 2),
            (cx - 4 + int(sway), cy + 8),
            (cx - 2 + int(sway * 1.2), cy + 13),
            (cx, cy + 15),
            (cx + 2 - int(sway * 1.2), cy + 13),
            (cx + 4 - int(sway), cy + 8),
            (cx + 5 - int(sway), cy + 2),
            (cx + 4, cy - 1),
        ])
        # Light strands.
        for x_off in (-3, 0, 3):
            pygame.draw.line(surface, _NS_zharakzuul.PALETTE["hair_light"],
                             (cx + x_off, cy),
                             (cx + x_off + int(sway * 0.5), cy + 12), 1)
        # Bright tip.
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["hair_shine"], (cx, cy + 14, 1, 1))
        # Mustache (curved).
        for side in (-1, 1):
            m_start = (cx + side * 2, cy - 3)
            m_end = (cx + side * 5, cy - 4)
            pygame.draw.line(surface, _NS_zharakzuul.PALETTE["hair_dark"],
                             m_start, m_end, 2)
            pygame.draw.line(surface, _NS_zharakzuul.PALETTE["hair_mid"],
                             m_start, m_end, 1)
    def _draw_elder_eyes(surface, cx, cy, phase, action):
        """Glowing cyan-white spectral eyes."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        intensity = 1.5 if action != "idle" and action != "meditate" else 1.0
        for side in (-1, 1):
            ex = cx + side * 3
            ey = cy + 1
            # Deep socket.
            pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["eye_socket"],
                             (ex - 1, ey - 1, 3, 3))
            # Glow halo.
            for r in range(5, 0, -1):
                alpha = _NS_zharakzuul._alpha(140 * (5 - r) / 5 * pulse * intensity)
                _NS_zharakzuul._aacircle(surface,
                                         (*_NS_zharakzuul.PALETTE["eye_mid"], alpha),
                                         (ex, ey), r)
            # Empty spectral eye (no pupil).
            pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["eye_dark"], (ex - 1, ey, 3, 1))
            pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["eye_mid"], (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["eye_light"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["eye_glow"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["white"], (ex, ey, 1, 1))
    def _draw_headband(surface, cx, cy, facing, phase):
        """Gold headband with center gem."""
        # Base band.
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_darkest"],
                         (cx - 6, cy - 1, 13, 3))
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_dark"],
                         (cx - 6, cy - 1, 13, 2))
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_mid"],
                         (cx - 5, cy - 1, 11, 1))
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_light"],
                         (cx - 4, cy - 1, 9, 1))
        # Central gem (void purple).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_zharakzuul._alpha(140 * (4 - r) / 4 * pulse)
            _NS_zharakzuul._aacircle(surface,
                                     (*_NS_zharakzuul.PALETTE["void_mid"], alpha),
                                     (cx, cy), r)
        _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["void_darkest"], (cx, cy), 2)
        _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["void_dark"], (cx, cy), 1)
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["void_light"], (cx, cy, 1, 1))
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["void_shine"], (cx, cy, 1, 1))
        # Side pointed tips.
        for side in (-1, 1):
            _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["gold_dark"], [
                (cx + side * 6, cy - 1),
                (cx + side * 8, cy - 3),
                (cx + side * 7, cy + 1),
            ])
            _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["gold_mid"], [
                (cx + side * 6, cy - 1),
                (cx + side * 7, cy - 2),
                (cx + side * 6, cy),
            ])
            pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_light"],
                             (cx + side * 7, cy - 2, 1, 1))
    def _draw_arms(surface, cx, cy, facing, phase, action, progress):
        """Two arms. Front holds void blade."""
        front_sh = (cx + facing * 12, cy - 12)
        back_sh = (cx - facing * 12, cy - 12)
        # Meditation pose: both hands together in front (prayer).
        if action == "meditate":
            hands_x = cx
            hands_y = cy - 4
            front_hand_x = hands_x + facing * 3
            front_hand_y = hands_y
            back_hand_x = hands_x - facing * 3
            back_hand_y = hands_y
        elif action == "slash" or action == "throw":
            if progress < 0.3:
                # Wind up.
                t = progress / 0.3
                front_hand_x = cx + facing * int(6 - t * 12)
                front_hand_y = cy - 12 - int(t * 6)
            elif progress < 0.5:
                # Swing forward.
                t = (progress - 0.3) / 0.2
                front_hand_x = cx + facing * int(-6 + t * 32)
                front_hand_y = cy - 18 + int(t * 14)
            elif progress < 0.75:
                # Hold.
                front_hand_x = cx + facing * 26
                front_hand_y = cy - 4
            else:
                # Return.
                t = (progress - 0.75) / 0.25
                front_hand_x = cx + facing * int(26 - t * 16)
                front_hand_y = cy - 4 - int(t * 6)
            back_hand_x = cx - facing * 8
            back_hand_y = cy - 4
        elif action == "pulse":
            # Cast pose: hand out, palm forward.
            if progress < 0.5:
                t = progress / 0.5
                front_hand_x = cx + facing * int(8 + t * 12)
                front_hand_y = cy - 8 - int(t * 4)
            else:
                t = (progress - 0.5) / 0.5
                front_hand_x = cx + facing * int(20 - t * 8)
                front_hand_y = cy - 12 + int(t * 4)
            back_hand_x = cx - facing * 8
            back_hand_y = cy - 2
        elif action == "resonant":
            # Both hands raised then thrust forward.
            if progress < 0.4:
                t = progress / 0.4
                front_hand_x = cx + facing * int(6 + t * 4)
                front_hand_y = cy - 12 - int(t * 12)
                back_hand_x = cx - facing * int(6 + t * 4)
                back_hand_y = cy - 12 - int(t * 12)
            elif progress < 0.7:
                t = (progress - 0.4) / 0.3
                front_hand_x = cx + facing * int(10 + t * 20)
                front_hand_y = cy - 24 + int(t * 20)
                back_hand_x = cx - facing * int(10 - t * 4)
                back_hand_y = cy - 24 + int(t * 20)
            else:
                t = (progress - 0.7) / 0.3
                front_hand_x = cx + facing * int(30 - t * 20)
                front_hand_y = cy - 4 - int(t * 8)
                back_hand_x = cx - facing * int(6 + t * 2)
                back_hand_y = cy - 4 - int(t * 8)
        else:
            # Idle: sword at side, ready pose.
            idle_sway = math.sin(phase * 0.8) * 1
            front_hand_x = cx + facing * 12
            front_hand_y = cy - 6 + int(idle_sway)
            back_hand_x = cx - facing * 8
            back_hand_y = cy - 2
        # Compute elbows.
        front_elbow = _NS_zharakzuul._arm_elbow(front_sh, (front_hand_x, front_hand_y), bend=5)
        back_elbow = _NS_zharakzuul._arm_elbow(back_sh, (back_hand_x, back_hand_y), bend=4)
        # Draw back arm first.
        _NS_zharakzuul._draw_arm_segment(surface, back_sh, back_elbow,
                                          (back_hand_x, back_hand_y))
        # Front arm.
        _NS_zharakzuul._draw_arm_segment(surface, front_sh, front_elbow,
                                          (front_hand_x, front_hand_y))
        # Void blade in front hand (hidden during meditation & when thrown).
        blade_hidden = (
            action == "meditate" or
            (action == "throw" and 0.4 < progress < 0.85) or
            action == "pulse"
        )
        if not blade_hidden:
            _NS_zharakzuul._draw_void_blade(surface, front_hand_x, front_hand_y,
                                             facing, phase, action, progress)
        # Meditation: draw glowing hands.
        if action == "meditate":
            _NS_zharakzuul._draw_meditation_hands(surface, cx, cy - 4, phase)
        # Resonant: draw energy sphere between raised hands.
        if action == "resonant" and progress < 0.7:
            t = min(1.0, progress / 0.4)
            orb_x = cx
            orb_y = cy - 24
            orb_r = int(4 + t * 10)
            for r in range(orb_r + 6, 0, -1):
                alpha = _NS_zharakzuul._alpha(180 * (orb_r + 6 - r) / (orb_r + 6) * t)
                _NS_zharakzuul._aacircle(surface,
                                         (*_NS_zharakzuul.PALETTE["void_mid"], alpha),
                                         (orb_x, orb_y), r)
            _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["void_light"],
                                     (orb_x, orb_y), max(1, orb_r - 2))
            _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["void_shine"],
                                     (orb_x, orb_y), max(1, orb_r - 5))
            pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["white"],
                             (orb_x, orb_y, 1, 1))
    def _draw_arm_segment(surface, shoulder, elbow, hand):
        """Draw arm with robe sleeve + skin forearm."""
        sx, sy = shoulder
        ex, ey = elbow
        hx, hy = hand
        # Upper arm (robed).
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["shadow_deep"],
                         (sx + 1, sy + 1), (ex + 1, ey + 1), 6)
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["robe_darkest"],
                         (sx, sy), (ex, ey), 5)
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["robe_dark"],
                         (sx, sy), (ex, ey), 4)
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["robe_mid"],
                         (sx, sy - 1), (ex, ey - 1), 2)
        # Forearm (skin visible).
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["shadow_deep"],
                         (ex + 1, ey + 1), (hx + 1, hy + 1), 5)
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["skin_darkest"],
                         (ex, ey), (hx, hy), 4)
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["skin_dark"],
                         (ex, ey), (hx, hy), 3)
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["skin_mid"],
                         (ex, ey - 1), (hx, hy - 1), 1)
        # Gold bracer at wrist.
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_darkest"],
                         (hx - 3, hy - 2, 6, 4))
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_dark"],
                         (hx - 2, hy - 2, 5, 3))
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_mid"],
                         (hx - 1, hy - 1, 3, 2))
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_light"],
                         (hx - 1, hy - 1, 3, 1))
        # Hand.
        _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["skin_dark"], (hx, hy), 2)
        _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["skin_mid"], (hx, hy - 1), 1)
    def _draw_meditation_hands(surface, cx, cy, phase):
        """Glowing hands in prayer position + energy between."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Glowing energy between hands.
        for r in range(8, 0, -1):
            alpha = _NS_zharakzuul._alpha(150 * (8 - r) / 8 * pulse)
            _NS_zharakzuul._aacircle(surface,
                                     (*_NS_zharakzuul.PALETTE["void_mid"], alpha),
                                     (cx, cy), r)
        _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["void_light"], (cx, cy), 3)
        _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["void_shine"], (cx, cy), 2)
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["white"], (cx, cy, 1, 1))
    def _draw_void_blade(surface, hx, hy, facing, phase, action, progress):
        """Long crystalline void blade with intense purple glow."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Blade angle depends on action.
        if action in ("slash", "throw") and progress < 0.3:
            angle = -math.pi / 2.5  # up behind
        elif action in ("slash", "throw") and progress < 0.5:
            angle = math.pi / 8   # diagonal down
        elif action in ("slash", "throw") and progress < 0.75:
            angle = 0             # horizontal
        else:
            angle = -math.pi / 8  # slight up idle
        blade_len = 32
        # Handle/pommel first.
        pommel_x = hx - int(math.cos(angle) * 3) * facing
        pommel_y = hy - int(math.sin(angle) * 3)
        _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["gold_darkest"],
                                 (pommel_x, pommel_y), 3)
        _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["gold_dark"],
                                 (pommel_x, pommel_y), 2)
        _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["gold_mid"],
                                 (pommel_x, pommel_y), 1)
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["gold_shine"],
                         (pommel_x, pommel_y, 1, 1))
        # Cross guard.
        perp_x = -math.sin(angle) * facing
        perp_y = math.cos(angle)
        cg_a = (hx + int(perp_x * 4), hy + int(perp_y * 4))
        cg_b = (hx - int(perp_x * 4), hy - int(perp_y * 4))
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["shadow_deep"],
                         (cg_a[0] + 1, cg_a[1] + 1), (cg_b[0] + 1, cg_b[1] + 1), 4)
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["gold_dark"],
                         cg_a, cg_b, 3)
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["gold_mid"],
                         cg_a, cg_b, 2)
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["gold_light"],
                         cg_a, cg_b, 1)
        # BLADE tip position.
        tip_x = hx + int(math.cos(angle) * blade_len) * facing
        tip_y = hy + int(math.sin(angle) * blade_len)
        # BLADE glow aura (thick).
        for r in range(8, 0, -1):
            alpha = _NS_zharakzuul._alpha(100 * (8 - r) / 8 * pulse)
            _NS_zharakzuul._aaline(surface,
                                   (*_NS_zharakzuul.PALETTE["void_mid"], alpha),
                                   (hx, hy), (tip_x, tip_y), r)
        # Shadow.
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["shadow_deep"],
                         (hx + 1, hy + 1), (tip_x + 1, tip_y + 1), 5)
        # BLADE body (crystalline layers).
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["void_darkest"],
                         (hx, hy), (tip_x, tip_y), 5)
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["void_dark"],
                         (hx, hy), (tip_x, tip_y), 4)
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["void_mid"],
                         (hx, hy), (tip_x, tip_y), 3)
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["void_light"],
                         (hx, hy), (tip_x, tip_y), 2)
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["void_shine"],
                         (hx, hy), (tip_x, tip_y), 1)
        # White core.
        pygame.draw.line(surface, _NS_zharakzuul.PALETTE["white"],
                         (hx + int(math.cos(angle) * 5) * facing,
                          hy + int(math.sin(angle) * 5)),
                         (tip_x - int(math.cos(angle) * 3) * facing,
                          tip_y - int(math.sin(angle) * 3)), 1)
        # SHARP TIP glow.
        for r in range(6, 0, -1):
            alpha = _NS_zharakzuul._alpha(140 * (6 - r) / 6 * pulse)
            _NS_zharakzuul._aacircle(surface,
                                     (*_NS_zharakzuul.PALETTE["void_hot"], alpha),
                                     (tip_x, tip_y), r)
        _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["void_shine"],
                                 (tip_x, tip_y), 2)
        pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["white"], (tip_x, tip_y, 1, 1))
        # Sparkles orbiting blade.
        for i in range(4):
            angle_orb = phase * 3 + i * math.pi / 2
            orb_t = (i + 0.5) / 4
            spark_base_x = int(hx + (tip_x - hx) * orb_t)
            spark_base_y = int(hy + (tip_y - hy) * orb_t)
            spark_x = spark_base_x + int(math.cos(angle_orb) * 4)
            spark_y = spark_base_y + int(math.sin(angle_orb) * 4)
            pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["void_shine"], (spark_x, spark_y, 1, 1))
    # ============================================================
    # BASIC ATTACK: Void blade slash
    # ============================================================
    def _draw_basic_slash_fx(surface, boss, x, y):
        """Void purple slash arc."""
        progress = getattr(boss, "_zk_attack_progress", 0.0)
        if progress < 0.4 or progress > 0.75:
            return
        facing = boss.direction
        t = (progress - 0.4) / 0.35
        intensity = math.sin(t * math.pi)
        base_x = x + facing * 14
        base_y = y - 6
        # Slash arc.
        for i in range(10):
            trail_t = max(0.0, t - i * 0.07)
            if trail_t <= 0:
                continue
            angle_start = math.pi / 3
            angle_end = -math.pi / 3
            ang = angle_start + (angle_end - angle_start) * trail_t
            tx_p = base_x + int(math.cos(ang) * 28) * facing
            ty_p = base_y + int(math.sin(ang) * 20)
            alpha = _NS_zharakzuul._alpha(230 * intensity * (1 - i * 0.09))
            if alpha <= 0:
                continue
            _NS_zharakzuul._aacircle(surface,
                                     (*_NS_zharakzuul.PALETTE["void_darkest"], alpha),
                                     (tx_p, ty_p), max(1, 6 - i // 2))
            _NS_zharakzuul._aacircle(surface,
                                     (*_NS_zharakzuul.PALETTE["void_dark"], alpha),
                                     (tx_p, ty_p), max(1, 5 - i // 2))
            _NS_zharakzuul._aacircle(surface,
                                     (*_NS_zharakzuul.PALETTE["void_mid"], alpha),
                                     (tx_p, ty_p), max(1, 3 - i // 2))
            _NS_zharakzuul._aacircle(surface,
                                     (*_NS_zharakzuul.PALETTE["void_light"], alpha),
                                     (tx_p, ty_p), max(1, 2 - i // 3))
            pygame.draw.rect(surface,
                             (*_NS_zharakzuul.PALETTE["void_shine"], alpha),
                             (tx_p, ty_p, 1, 1))
    # ============================================================
    # AMBIENT / GROUND (TRUE BOSS scale)
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        """Big shadow beneath colossus."""
        breath = math.sin(phase * 0.6) * 0.15 + 0.85
        shadow = pygame.Surface((160, 32), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, int((14 - radius) * 14 * breath))
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (14 - radius, 16 - radius,
                                 132 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (10, 3, 20, int(180 * breath)),
                            (12, 10, 136, 12))
        surface.blit(shadow, (x - 80, y - 16))
    def _draw_void_particles(surface, cx, cy, phase):
        """Void purple particles rising from ground."""
        for i in range(10):
            t = (phase * 0.5 + i * 0.11) % 1.0
            dx = cx + int(math.sin(phase + i * 0.6) * 30) - 15 + i * 3
            dy = cy - int(t * 32)
            alpha = _NS_zharakzuul._alpha(220 * (1 - t))
            if alpha > 0:
                _NS_zharakzuul._aacircle(surface,
                                         (*_NS_zharakzuul.PALETTE["void_dark"], alpha),
                                         (dx, dy), 2)
                _NS_zharakzuul._aacircle(surface,
                                         (*_NS_zharakzuul.PALETTE["void_mid"], alpha),
                                         (dx, dy - 1), 1)
                pygame.draw.rect(surface, (*_NS_zharakzuul.PALETTE["void_light"], alpha),
                                 (dx, dy - 1, 1, 1))
                pygame.draw.rect(surface, (*_NS_zharakzuul.PALETTE["void_shine"], alpha),
                                 (dx, dy - 2, 1, 1))
    def _draw_void_aura(surface, x, y, phase):
        """Massive void purple aura (TRUE BOSS scale)."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((260, 220), pygame.SRCALPHA)
        for radius in range(110, 5, -5):
            alpha = _NS_zharakzuul._alpha((110 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_zharakzuul._aacircle(aura,
                                         (*_NS_zharakzuul.PALETTE["void_darkest"], alpha),
                                         (130, 110), radius)
        for radius in range(75, 5, -4):
            alpha = _NS_zharakzuul._alpha((75 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_zharakzuul._aacircle(aura,
                                         (*_NS_zharakzuul.PALETTE["void_dark"], alpha),
                                         (130, 110), radius)
        for radius in range(45, 5, -3):
            alpha = _NS_zharakzuul._alpha((45 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_zharakzuul._aacircle(aura,
                                         (*_NS_zharakzuul.PALETTE["void_mid"], alpha),
                                         (130, 110), radius)
        surface.blit(aura, (x - 130, y - 110))
        # Orbiting void embers.
        for i in range(18):
            angle = phase * 0.3 + i * math.pi / 9
            radius = 48 + int(math.sin(phase + i) * 16)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = _NS_zharakzuul.PALETTE["void_mid"] if i % 2 == 0 else _NS_zharakzuul.PALETTE["void_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["void_shine"], (sx, sy, 1, 1))
        # Void crystals floating (accent).
        for i in range(6):
            angle = phase * 0.2 + i * math.pi / 3
            radius = 65
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.6)
            _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["crystal_dark"], [
                (sx, sy - 3),
                (sx - 2, sy),
                (sx, sy + 3),
                (sx + 2, sy),
            ])
            _NS_zharakzuul._poly(surface, _NS_zharakzuul.PALETTE["crystal_mid"], [
                (sx, sy - 2),
                (sx - 1, sy),
                (sx, sy + 2),
                (sx + 1, sy),
            ])
            pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["crystal_light"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """BIG runic ground ring (TRUE BOSS)."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((200, 62), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_zharakzuul.PALETTE["void_darkest"], 200),
                            (5, 20, 190, 32), 3)
        pygame.draw.ellipse(ring, (*_NS_zharakzuul.PALETTE["void_dark"], 220),
                            (14, 22, 172, 28), 2)
        pygame.draw.ellipse(ring, (*_NS_zharakzuul.PALETTE["void_mid"], 200),
                            (25, 24, 150, 24), 1)
        pygame.draw.ellipse(ring, (*_NS_zharakzuul.PALETTE["void_dark"], 180),
                            (40, 26, 120, 20), 1)
        # Runes.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 100 + int(math.cos(angle) * 52)
            y1 = 34 + int(math.sin(angle) * 10)
            x2 = 100 + int(math.cos(angle) * 82)
            y2 = 34 + int(math.sin(angle) * 15)
            pygame.draw.line(ring, (*_NS_zharakzuul.PALETTE["void_light"], 220),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.rect(ring, _NS_zharakzuul.PALETTE["void_shine"], (x2, y2, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_zharakzuul.PALETTE["void_hot"],
                                        _NS_zharakzuul._alpha(160 * pulse)),
                                (15, 14, 170, 46), 1)
        surface.blit(ring, (x - 100, y - 31))
    # ============================================================
    # SKILL Q: AETHER REMEDY (self-heal meditation)
    # ============================================================
    def _draw_meditation_ground(surface, boss, x, y, timer, phase):
        """Ground rune during meditation."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        origin_x = x
        origin_y = y + 46
        r = 50
        alpha = _NS_zharakzuul._alpha(200 * pulse)
        pygame.draw.ellipse(surface, (*_NS_zharakzuul.PALETTE["void_dark"], alpha),
                            (origin_x - r, origin_y - r // 3, r * 2, r * 2 // 3), 3)
        pygame.draw.ellipse(surface, (*_NS_zharakzuul.PALETTE["void_mid"], alpha),
                            (origin_x - r + 4, origin_y - r // 3 + 2,
                             r * 2 - 8, r * 2 // 3 - 4), 2)
        pygame.draw.ellipse(surface, (*_NS_zharakzuul.PALETTE["void_light"], alpha),
                            (origin_x - r + 10, origin_y - r // 3 + 5,
                             r * 2 - 20, r * 2 // 3 - 10), 1)
        # Rotating runes.
        for i in range(12):
            angle = phase * 0.5 + i * math.pi / 6
            rx = origin_x + int(math.cos(angle) * r)
            ry = origin_y + int(math.sin(angle) * r * 0.4)
            pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["void_shine"], (rx, ry, 2, 2))
            pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["white"], (rx, ry, 1, 1))
    def _draw_aether_remedy_fx(surface, boss, x, y, timer, phase):
        """Rising void energy + healing sparkles around body."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Healing spiral rising around body.
        for i in range(16):
            angle = phase * 3 + i * math.pi / 8
            spiral_t = ((phase * 0.5 + i * 0.08) % 1.0)
            spiral_r = 25 - int(spiral_t * 5)
            sx = x + int(math.cos(angle) * spiral_r)
            sy = y + 20 - int(spiral_t * 60)
            alpha = _NS_zharakzuul._alpha(230 * (1 - spiral_t))
            if alpha > 0:
                _NS_zharakzuul._aacircle(surface,
                                         (*_NS_zharakzuul.PALETTE["void_mid"], alpha),
                                         (sx, sy), 3)
                _NS_zharakzuul._aacircle(surface,
                                         (*_NS_zharakzuul.PALETTE["void_light"], alpha),
                                         (sx, sy), 2)
                pygame.draw.rect(surface, (*_NS_zharakzuul.PALETTE["void_shine"], alpha),
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_zharakzuul.PALETTE["white"], alpha),
                                 (sx, sy, 1, 1))
        # Big glow orb at chest.
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        orb_x = x
        orb_y = y - 10
        for r in range(15, 0, -2):
            alpha = _NS_zharakzuul._alpha(80 * (15 - r) / 15 * pulse)
            _NS_zharakzuul._aacircle(surface,
                                     (*_NS_zharakzuul.PALETTE["void_mid"], alpha),
                                     (orb_x, orb_y), r)
        # Vertical light beam from ground up (spiritual).
        for i in range(3):
            beam_alpha = _NS_zharakzuul._alpha(120 * pulse - i * 30)
            if beam_alpha > 0:
                pygame.draw.line(surface,
                                 (*_NS_zharakzuul.PALETTE["void_light"], beam_alpha),
                                 (x + i - 1, y + 40), (x + i - 1, y - 40), 1)
    # ============================================================
    # SKILL W: VOID SLING (throw blade projectile)
    # ============================================================
    def _draw_voidsling_projectile(surface, boss, x, y, timer, phase):
        """Throw void blade as projectile."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_zharakzuul._target_position(boss, x, y)
        sx, sy = _NS_zharakzuul._blade_hand_position(boss, x, y)
        if progress < 0.4:
            # Wind up: charge void energy on blade.
            t = progress / 0.4
            for r in range(int(8 + t * 6), 0, -1):
                alpha = _NS_zharakzuul._alpha(150 * (int(8 + t * 6) - r) / (int(8 + t * 6)) * t)
                _NS_zharakzuul._aacircle(surface,
                                         (*_NS_zharakzuul.PALETTE["void_mid"], alpha),
                                         (sx + facing * 8, sy), r)
        else:
            # Blade in flight.
            t = (progress - 0.4) / 0.6
            t = min(1.0, t)
            dx = tx - sx
            dy = ty - sy
            length = max(1, math.sqrt(dx * dx + dy * dy))
            dir_x = dx / length
            dir_y = dy / length
            perp_x = -dir_y
            perp_y = dir_x
            bx = int(sx + dx * t)
            by = int(sy + dy * t)
            # HUGE trail.
            for i in range(12):
                trail_t = max(0.0, t - i * 0.04)
                px = int(sx + dx * trail_t)
                py = int(sy + dy * trail_t)
                alpha = _NS_zharakzuul._alpha(230 - i * 18)
                size = max(1, 8 - i // 2)
                _NS_zharakzuul._aacircle(surface,
                                         (*_NS_zharakzuul.PALETTE["void_darkest"], alpha),
                                         (px, py), size + 1)
                _NS_zharakzuul._aacircle(surface,
                                         (*_NS_zharakzuul.PALETTE["void_dark"], alpha),
                                         (px, py), size)
                _NS_zharakzuul._aacircle(surface,
                                         (*_NS_zharakzuul.PALETTE["void_mid"], alpha),
                                         (px, py), max(1, size - 1))
                _NS_zharakzuul._aacircle(surface,
                                         (*_NS_zharakzuul.PALETTE["void_light"], alpha),
                                         (px, py), max(1, size - 3))
                # Sparks.
                if i < 5:
                    for s in range(2):
                        sp_angle = trail_t * 6 + i + s * math.pi
                        sp_r = size + 3
                        spx = px + int(math.cos(sp_angle) * sp_r)
                        spy = py + int(math.sin(sp_angle) * sp_r)
                        pygame.draw.rect(surface,
                                         (*_NS_zharakzuul.PALETTE["void_shine"], alpha),
                                         (spx, spy, 1, 1))
            # Draw actual blade shape.
            blade_len = 24
            blade_back_x = bx - int(dir_x * blade_len)
            blade_back_y = by - int(dir_y * blade_len)
            # Blade layers.
            for width, color in [
                (7, _NS_zharakzuul.PALETTE["void_darkest"]),
                (5, _NS_zharakzuul.PALETTE["void_dark"]),
                (3, _NS_zharakzuul.PALETTE["void_mid"]),
                (2, _NS_zharakzuul.PALETTE["void_light"]),
                (1, _NS_zharakzuul.PALETTE["void_shine"]),
            ]:
                pygame.draw.line(surface, color,
                                 (blade_back_x, blade_back_y), (bx, by), width)
            # White core.
            pygame.draw.line(surface, _NS_zharakzuul.PALETTE["white"],
                             (blade_back_x, blade_back_y), (bx, by), 1)
            # Blade tip glow.
            for r in range(8, 0, -1):
                alpha = _NS_zharakzuul._alpha(140 * (8 - r) / 8)
                _NS_zharakzuul._aacircle(surface,
                                         (*_NS_zharakzuul.PALETTE["void_hot"], alpha),
                                         (bx, by), r)
            _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["void_shine"],
                                     (bx, by), 3)
            _NS_zharakzuul._aacircle(surface, _NS_zharakzuul.PALETTE["white"],
                                     (bx, by), 1)
            # Impact burst.
            if t > 0.88:
                st = (t - 0.88) / 0.12
                imp_r = int(15 + st * 20)
                alpha = _NS_zharakzuul._alpha(240 * (1 - st))
                _NS_zharakzuul._aacircle(surface, (*_NS_zharakzuul.PALETTE["void_dark"], alpha),
                                         (tx, ty), imp_r + 3, 3)
                _NS_zharakzuul._aacircle(surface, (*_NS_zharakzuul.PALETTE["void_mid"], alpha),
                                         (tx, ty), imp_r, 3)
                _NS_zharakzuul._aacircle(surface, (*_NS_zharakzuul.PALETTE["void_light"], alpha),
                                         (tx, ty), max(1, imp_r - 6), 2)
                _NS_zharakzuul._aacircle(surface, (*_NS_zharakzuul.PALETTE["void_shine"], alpha),
                                         (tx, ty), max(1, imp_r // 3))
                pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["white"], (tx - 1, ty - 1, 2, 2))
                # Radial burst.
                for i in range(12):
                    ang = i * math.pi / 6
                    ex = tx + int(math.cos(ang) * imp_r)
                    ey = ty + int(math.sin(ang) * imp_r * 0.7)
                    pygame.draw.line(surface,
                                     (*_NS_zharakzuul.PALETTE["void_light"], alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_zharakzuul.PALETTE["void_shine"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL E: PULSE OF THE VOID (concentric rings AoE)
    # ============================================================
    def _draw_pulse_rings_ground(surface, boss, x, y, timer, phase):
        """Ground marker showing pulse area."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        origin_x = x
        origin_y = y + 46
        # Multiple concentric growing rings.
        for ring_i in range(4):
            ring_delay = ring_i * 0.15
            ring_t = max(0.0, progress - ring_delay)
            if ring_t <= 0 or ring_t > 0.7:
                continue
            local_t = ring_t / 0.7
            r = int(20 + local_t * 60)
            alpha = _NS_zharakzuul._alpha(200 * (1 - local_t))
            pygame.draw.ellipse(surface, (*_NS_zharakzuul.PALETTE["void_dark"], alpha),
                                (origin_x - r, origin_y - r // 3,
                                 r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_zharakzuul.PALETTE["void_mid"], alpha),
                                (origin_x - r + 3, origin_y - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_zharakzuul.PALETTE["void_light"], alpha),
                                (origin_x - r + 6, origin_y - r // 3 + 4,
                                 r * 2 - 12, r * 2 // 3 - 8), 1)
    def _draw_pulse_rings(surface, boss, x, y, timer, phase):
        """Concentric void rings expanding outward + sparkles."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        origin_x = x
        origin_y = y + 46
        # Rings at eye-level too (dome effect).
        for ring_i in range(4):
            ring_delay = ring_i * 0.15
            ring_t = max(0.0, progress - ring_delay)
            if ring_t <= 0 or ring_t > 0.7:
                continue
            local_t = ring_t / 0.7
            r = int(20 + local_t * 60)
            alpha = _NS_zharakzuul._alpha(200 * (1 - local_t))
            # Higher rings.
            for h_off in (0, -8, -16):
                pygame.draw.ellipse(surface, (*_NS_zharakzuul.PALETTE["void_dark"], alpha),
                                    (origin_x - r, origin_y - r // 3 + h_off,
                                     r * 2, r * 2 // 3), 2)
                pygame.draw.ellipse(surface, (*_NS_zharakzuul.PALETTE["void_mid"], alpha),
                                    (origin_x - r + 3, origin_y - r // 3 + 2 + h_off,
                                     r * 2 - 6, r * 2 // 3 - 4), 1)
        # Sparkles orbiting outward.
        for i in range(20):
            angle = i * math.pi * 2 / 20 + phase * 0.5
            travel_t = ((phase * 0.6 + i * 0.05) % 1.0)
            dist = int(travel_t * 65)
            sx = origin_x + int(math.cos(angle) * dist)
            sy = origin_y + int(math.sin(angle) * dist * 0.4) - int(travel_t * 8)
            alpha = _NS_zharakzuul._alpha(240 * (1 - travel_t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_zharakzuul.PALETTE["void_light"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_zharakzuul.PALETTE["void_shine"], alpha),
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_zharakzuul.PALETTE["white"], alpha),
                                 (sx, sy, 1, 1))
        # Silence symbols (mute marks) floating up.
        for i in range(5):
            si_t = ((phase * 0.4 + i * 0.2) % 1.0)
            sx = origin_x - 20 + i * 10
            sy = origin_y - int(si_t * 40)
            alpha = _NS_zharakzuul._alpha(200 * (1 - si_t))
            if alpha > 0:
                # X mark.
                pygame.draw.line(surface,
                                 (*_NS_zharakzuul.PALETTE["void_shine"], alpha),
                                 (sx - 2, sy - 2), (sx + 2, sy + 2), 1)
                pygame.draw.line(surface,
                                 (*_NS_zharakzuul.PALETTE["void_shine"], alpha),
                                 (sx - 2, sy + 2), (sx + 2, sy - 2), 1)
    # ============================================================
    # SKILL R: RESONANT PULSE (BIG cone of pulses)
    # ============================================================
    def _draw_resonant_ground(surface, boss, x, y, timer, phase):
        """Ground path from boss to target."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_zharakzuul._target_position(boss, x, y)
        if 0.4 < progress:
            t = (progress - 0.4) / 0.6
            # Multiple concentric rings from boss to target.
            num_rings = 6
            for i in range(num_rings):
                ring_progress = min(1.0, t * 2 - i * 0.15)
                if ring_progress <= 0:
                    continue
                # Ring position along path.
                path_t = (i + 0.5) / num_rings
                ring_x = int(x + (tx - x) * path_t)
                ring_y = int(y + 46 + (ty - y - 46) * path_t * 0.5)
                # Expanding ring.
                r = int(15 + ring_progress * 20)
                alpha = _NS_zharakzuul._alpha(200 * (1 - ring_progress * 0.5))
                pygame.draw.ellipse(surface, (*_NS_zharakzuul.PALETTE["void_dark"], alpha),
                                    (ring_x - r, ring_y - r // 3, r * 2, r * 2 // 3), 2)
                pygame.draw.ellipse(surface, (*_NS_zharakzuul.PALETTE["void_light"], alpha),
                                    (ring_x - r + 2, ring_y - r // 3 + 1,
                                     r * 2 - 4, r * 2 // 3 - 2), 1)
    def _draw_resonant_pulse_fx(surface, boss, x, y, timer, phase):
        """Massive pulse from boss to target with expanding energy rings."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_zharakzuul._target_position(boss, x, y)
        if progress < 0.4:
            # Charge up: energy sphere between raised hands (drawn by body).
            # Add extra intensity sparks converging to hands.
            t = progress / 0.4
            for i in range(14):
                angle = phase * 3 + i * math.pi / 7
                spark_dist = int(30 * (1 - t))
                sx = x + int(math.cos(angle) * spark_dist)
                sy = y - 24 + int(math.sin(angle) * spark_dist)
                alpha = _NS_zharakzuul._alpha(240 * t)
                pygame.draw.line(surface, (*_NS_zharakzuul.PALETTE["void_shine"], alpha),
                                 (sx, sy), (x, y - 24), 1)
                pygame.draw.rect(surface, (*_NS_zharakzuul.PALETTE["white"], alpha),
                                 (sx, sy, 1, 1))
        elif progress < 0.7:
            # UNLEASH: massive pulse forward.
            t = (progress - 0.4) / 0.3
            intensity = math.sin(t * math.pi)
            # Origin at hands (front, extended).
            origin_x = x + facing * 26
            origin_y = y - 6
            # BIG expanding rings forward.
            num_rings = 5
            for ring_i in range(num_rings):
                ring_delay = ring_i * 0.12
                ring_t = max(0.0, t - ring_delay)
                if ring_t <= 0:
                    continue
                # Ring travels forward.
                dist = ring_t * 250
                # Position of ring center.
                dx = tx - origin_x
                dy = ty - origin_y
                length = max(1, math.sqrt(dx * dx + dy * dy))
                dir_x = dx / length
                dir_y = dy / length
                ring_x = int(origin_x + dir_x * dist)
                ring_y = int(origin_y + dir_y * dist)
                # Ring size grows.
                r = int(20 + ring_t * 30)
                alpha = _NS_zharakzuul._alpha(240 * intensity * (1 - ring_t * 0.3))
                # Multi-layer ring.
                _NS_zharakzuul._aacircle(surface, (*_NS_zharakzuul.PALETTE["void_darkest"], alpha),
                                         (ring_x, ring_y), r + 2, 3)
                _NS_zharakzuul._aacircle(surface, (*_NS_zharakzuul.PALETTE["void_dark"], alpha),
                                         (ring_x, ring_y), r, 3)
                _NS_zharakzuul._aacircle(surface, (*_NS_zharakzuul.PALETTE["void_mid"], alpha),
                                         (ring_x, ring_y), max(1, r - 4), 2)
                _NS_zharakzuul._aacircle(surface, (*_NS_zharakzuul.PALETTE["void_light"], alpha),
                                         (ring_x, ring_y), max(1, r - 8), 1)
                # Sparkles orbit ring edge.
                for i in range(8):
                    sp_ang = phase * 3 + i * math.pi / 4
                    spx = ring_x + int(math.cos(sp_ang) * r)
                    spy = ring_y + int(math.sin(sp_ang) * r)
                    pygame.draw.rect(surface,
                                     (*_NS_zharakzuul.PALETTE["void_shine"], alpha),
                                     (spx, spy, 2, 2))
            # Impact at target.
            if t > 0.5:
                imp_t = (t - 0.5) / 0.5
                imp_r = int(20 + imp_t * 30)
                imp_alpha = _NS_zharakzuul._alpha(255 * intensity)
                _NS_zharakzuul._aacircle(surface, (*_NS_zharakzuul.PALETTE["void_darkest"], imp_alpha),
                                         (tx, ty), imp_r + 4, 3)
                _NS_zharakzuul._aacircle(surface, (*_NS_zharakzuul.PALETTE["void_dark"], imp_alpha),
                                         (tx, ty), imp_r, 3)
                _NS_zharakzuul._aacircle(surface, (*_NS_zharakzuul.PALETTE["void_mid"], imp_alpha),
                                         (tx, ty), max(1, imp_r - 8), 2)
                _NS_zharakzuul._aacircle(surface, (*_NS_zharakzuul.PALETTE["void_light"], imp_alpha),
                                         (tx, ty), max(1, imp_r - 16), 1)
                _NS_zharakzuul._aacircle(surface, (*_NS_zharakzuul.PALETTE["void_hot"], imp_alpha),
                                         (tx, ty), max(1, imp_r // 3))
                _NS_zharakzuul._aacircle(surface, (*_NS_zharakzuul.PALETTE["void_shine"], imp_alpha),
                                         (tx, ty), max(1, imp_r // 5))
                pygame.draw.rect(surface, _NS_zharakzuul.PALETTE["white"], (tx - 1, ty - 1, 2, 2))
                # Radial burst.
                for i in range(14):
                    ang = i * math.pi / 7
                    ex = tx + int(math.cos(ang) * imp_r)
                    ey = ty + int(math.sin(ang) * imp_r * 0.7)
                    pygame.draw.line(surface,
                                     (*_NS_zharakzuul.PALETTE["void_light"], imp_alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_zharakzuul.PALETTE["void_shine"], imp_alpha),
                                     (ex, ey, 2, 2))
        else:
            # Aftermath: fading rings + rising particles.
            t = (progress - 0.7) / 0.3
            for i in range(12):
                rise_t = (phase * 0.7 + i * 0.08) % 1.0
                rx = tx + int(math.sin(phase + i) * 22)
                ry = ty - int(rise_t * 32)
                alpha = _NS_zharakzuul._alpha(220 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_zharakzuul._aacircle(surface,
                                             (*_NS_zharakzuul.PALETTE["void_mid"], alpha),
                                             (rx, ry), 2)
                    pygame.draw.rect(surface, (*_NS_zharakzuul.PALETTE["void_shine"], alpha),
                                     (rx, ry - 1, 1, 1))
                    pygame.draw.rect(surface, (*_NS_zharakzuul.PALETTE["white"], alpha),
                                     (rx, ry - 1, 1, 1))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_rakzhan(surface, boss, x, y):
    """Entry point rakzhan."""
    return _NS_rakzhan.draw_rakzhan(surface, boss, x, y)


def draw_sirakzan(surface, boss, x, y):
    """Entry point sirakzan."""
    return _NS_sirakzan.draw_sirakzan(surface, boss, x, y)


def draw_valekris(surface, boss, x, y):
    """Entry point valekris."""
    return _NS_valekris.draw_valekris(surface, boss, x, y)


def draw_zharakzuul(surface, boss, x, y):
    """Entry point zharakzuul."""
    return _NS_zharakzuul.draw_zharakzuul(surface, boss, x, y)
