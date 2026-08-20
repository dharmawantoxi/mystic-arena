"""
bosses/level47.py - Semua boss Level 47

Berisi:
  - kaizoku_raijin  (mini boss - MELEE festival thunder, lightning pirate)
  - korokai         (mini boss - MELEE mirror blade, shinobi duelist)
  - verdanix        (mini boss - RANGED verdant fury, nature wrath)
  - pyraena         (TRUE BOSS - RANGED emberweaver, fire mage)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _kr_ (kaizoku_raijin), _kor_ (korokai), _ver_ (verdanix) sudah unik.
  - _pyr_ (pyraena) di-rename -> _pye_ (bentrok dengan pyrenth
    level 4 & pyraklos level 13), termasuk atribut _last_x/_last_y.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# KAIZOKU RAIJIN (FESTIVAL THUNDER) - Mini Boss
# ====================================================================

class _NS_kaizoku_raijin:
    """Namespace kaizoku_raijin - Sound Hashira inspired boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (tan warrior)
        "skin_darkest": (60, 30, 20),
        "skin_dark": (130, 80, 55),
        "skin_mid": (200, 145, 105),
        "skin_light": (240, 195, 155),
        "skin_shine": (255, 230, 200),
        # Silver/white hair
        "hair_darkest": (40, 40, 55),
        "hair_dark": (110, 110, 130),
        "hair_mid": (180, 180, 200),
        "hair_light": (230, 230, 245),
        "hair_shine": (255, 255, 255),
        # Dark clothing (gilet)
        "cloth_darkest": (10, 10, 15),
        "cloth_dark": (30, 28, 40),
        "cloth_mid": (55, 50, 70),
        "cloth_light": (90, 85, 110),
        # Gold accents (armbands, belt)
        "gold_darkest": (60, 40, 5),
        "gold_dark": (140, 100, 20),
        "gold_mid": (220, 170, 50),
        "gold_light": (255, 220, 110),
        "gold_shine": (255, 250, 200),
        # Red eye + jewel
        "jewel_darkest": (40, 5, 8),
        "jewel_dark": (110, 20, 25),
        "jewel_mid": (210, 45, 50),
        "jewel_light": (255, 110, 100),
        "jewel_glow": (255, 200, 180),
        # Nichirin blade (dark with gold edge)
        "blade_darkest": (15, 12, 8),
        "blade_dark": (45, 35, 20),
        "blade_mid": (100, 80, 45),
        "blade_edge": (220, 180, 90),
        "blade_shine": (255, 240, 180),
        # Sound / thunder (gold-orange)
        "sound_darkest": (40, 20, 5),
        "sound_dark": (120, 70, 15),
        "sound_mid": (230, 150, 40),
        "sound_light": (255, 210, 90),
        "sound_hot": (255, 240, 160),
        "sound_shine": (255, 255, 230),
        # Cyan/white sound waves
        "wave_darkest": (10, 30, 40),
        "wave_dark": (30, 80, 110),
        "wave_mid": (100, 180, 220),
        "wave_light": (180, 230, 250),
        "wave_shine": (240, 250, 255),
        # Purple firework accents
        "spark_dark": (50, 20, 80),
        "spark_mid": (140, 70, 200),
        "spark_light": (210, 150, 250),
        # Pink firework
        "pink_dark": (110, 30, 70),
        "pink_mid": (220, 80, 140),
        "pink_light": (255, 160, 200),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kaizoku_raijin._clamp(color)
        if _NS_kaizoku_raijin.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_kaizoku_raijin._clamp(color)
        if _NS_kaizoku_raijin.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_kaizoku_raijin._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_kaizoku_raijin(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kaizoku_raijin._detect_moving(boss)
        _NS_kaizoku_raijin._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_kr_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind
        _NS_kaizoku_raijin._draw_festival_aura(surface, x, y, pulse)
        _NS_kaizoku_raijin._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "w":
            _NS_kaizoku_raijin._draw_rising_dragon_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaizoku_raijin._draw_rhapsody_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaizoku_raijin._draw_string_ground(surface, boss, x, y, skill_timer, pulse)
        # Body - floating animation always
        if attacking:
            _NS_kaizoku_raijin._draw_kr_attack(surface, boss, x, y)
        elif moving:
            _NS_kaizoku_raijin._draw_kr_walk(surface, boss, x, y)
        else:
            _NS_kaizoku_raijin._draw_kr_idle(surface, boss, x, y)
        # Foreground FX
        if active_skill == "q":
            _NS_kaizoku_raijin._draw_thunderclap_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kaizoku_raijin._draw_rising_dragon_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaizoku_raijin._draw_rhapsody_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaizoku_raijin._draw_string_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kr_previous_timer", 0))
        active = bool(getattr(boss, "_kr_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._kr_attack_active = True
            boss._kr_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._kr_attack_frame = int(getattr(boss, "_kr_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._kr_attack_active = False
            boss._kr_attack_frame = 0
            active = False
        boss._kr_previous_timer = timer
        boss._kr_attack_progress = (
            min(1.0, getattr(boss, "_kr_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_kr_last_x"):
            boss._kr_last_x = boss.x
            boss._kr_last_y = boss.y
            return False
        dx = abs(boss.x - boss._kr_last_x)
        dy = abs(boss.y - boss._kr_last_y)
        boss._kr_last_x = boss.x
        boss._kr_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS - Floating animation always
    # ============================================================
    def _draw_kr_idle(surface, boss, x, y):
        # Floating bob - gentle up/down
        float_bob = int(math.sin(boss.pulse * 0.6) * 6) - 8
        _NS_kaizoku_raijin._draw_shadow(surface, x, y + 50)
        _NS_kaizoku_raijin._draw_floating_sparks(surface, x, y + 45, boss.pulse)
        _NS_kaizoku_raijin._draw_kr_body(surface, x, y + float_bob,
                                          boss.direction, boss.pulse, "idle")
    def _draw_kr_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        # Faster float when moving
        float_bob = int(math.sin(phase * 0.8) * 8) - 8
        sway = int(math.sin(phase * 0.5) * 3)
        _NS_kaizoku_raijin._draw_shadow(surface, x + sway, y + 50)
        _NS_kaizoku_raijin._draw_floating_sparks(surface, x + sway, y + 45, phase, trail=True,
                                                  facing=boss.direction)
        _NS_kaizoku_raijin._draw_kr_body(surface, x + sway, y + float_bob,
                                          boss.direction, phase, "walk")
    # ============================================================
    # POSE ROUTERS - Floating animation always
    # ============================================================
    def _draw_kr_attack(surface, boss, x, y):
        progress = getattr(boss, "_kr_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Swing attack: wind-up → swing forward → follow-through
        if progress < 0.35:
            # Wind up - pull back
            t = progress / 0.35
            lunge = -int(t * 6) * boss.direction
            lift = int(t * 4) - 8
        elif progress < 0.6:
            # SWING - big forward lunge
            t = (progress - 0.35) / 0.25
            lunge = int((-6 + t * 22)) * boss.direction
            lift = int(4 - t * 8) - 8
        else:
            # Follow through - return
            t = (progress - 0.6) / 0.4
            lunge = int(16 * (1 - t)) * boss.direction
            lift = int(-4 + t * 4) - 8
        _NS_kaizoku_raijin._draw_shadow(surface, x + lunge, y + 50)
        _NS_kaizoku_raijin._draw_floating_sparks(surface, x + lunge, y + 45,
                                                  boss.pulse, intense=True)
        _NS_kaizoku_raijin._draw_kr_body(surface, x + lunge, y + lift,
                                          boss.direction, boss.pulse, "attack", progress)
        _NS_kaizoku_raijin._draw_sword_slash_fx(surface, boss, x + lunge, y + lift, progress)
    # ============================================================
    # BODY - Humanoid Samurai (head, torso, arms with dual blades, legs)
    # ============================================================
    def _draw_kr_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Layer order: back arm/blade → legs → torso → front arm/blade → head → hair details
        back_arm_angle = 0
        front_arm_angle = 0
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                # Wind up: raise blades HIGH ABOVE HEAD (both arms up-back)
                # arm_angle: -pi/2 = straight up, 0 = down, +pi/2 = forward
                back_arm_angle = -math.pi * 0.9 * t  # nearly straight up
                front_arm_angle = -math.pi * 0.75 * t  # up-back
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                # SWING down and forward (from up → forward-down)
                back_arm_angle = -math.pi * 0.9 + math.pi * 1.3 * t  # ends forward-down
                front_arm_angle = -math.pi * 0.75 + math.pi * 1.15 * t
            else:
                t = (attack_progress - 0.6) / 0.4
                # Follow through: blades forward-down, gradually reset
                back_arm_angle = math.pi * 0.4 * (1 - t)
                front_arm_angle = math.pi * 0.4 * (1 - t)
        else:
            # Idle sway
            back_arm_angle = math.sin(phase * 0.6) * 0.15
            front_arm_angle = math.sin(phase * 0.6 + 0.5) * 0.12
        # Back arm + blade (behind body)
        _NS_kaizoku_raijin._draw_arm_with_blade(surface, cx - facing * 3, cy - 4, facing,
                                                 back_arm_angle, phase, is_back=True)
        # Legs (floating - crossed/relaxed pose)
        _NS_kaizoku_raijin._draw_floating_legs(surface, cx, cy + 10, facing, phase)
        # Torso
        _NS_kaizoku_raijin._draw_torso(surface, cx, cy, facing, phase)
        # Head
        _NS_kaizoku_raijin._draw_head(surface, cx + facing * 2, cy - 18, facing, phase)
        # Front arm + blade (over body)
        _NS_kaizoku_raijin._draw_arm_with_blade(surface, cx + facing * 3, cy - 4, facing,
                                                 front_arm_angle, phase, is_back=False)
    def _draw_floating_legs(surface, cx, cy, facing, phase):
        """Legs in floating pose - slightly bent, drifting."""
        sway = math.sin(phase * 0.7) * 2
        # Back leg
        bl_hip = (cx - 4, cy - 2)
        bl_knee = (cx - 6 - int(sway), cy + 6)
        bl_foot = (cx - 5 - int(sway * 0.5), cy + 14)
        # Front leg
        fl_hip = (cx + 4, cy - 2)
        fl_knee = (cx + 6 + int(sway), cy + 8)
        fl_foot = (cx + 5 + int(sway * 0.5), cy + 14)
        # Shadow
        for hip, knee, foot in [(bl_hip, bl_knee, bl_foot), (fl_hip, fl_knee, fl_foot)]:
            _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["shadow_deep"],
                                        (hip[0] + 1, hip[1] + 1), (knee[0] + 1, knee[1] + 1), 6)
            _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["shadow_deep"],
                                        (knee[0] + 1, knee[1] + 1), (foot[0] + 1, foot[1] + 1), 5)
        # Draw both legs (dark pants)
        for hip, knee, foot in [(bl_hip, bl_knee, bl_foot), (fl_hip, fl_knee, fl_foot)]:
            _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["cloth_darkest"], hip, knee, 6)
            _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["cloth_dark"], hip, knee, 5)
            _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["cloth_mid"],
                                        (hip[0], hip[1] - 1), (knee[0], knee[1] - 1), 3)
            _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["cloth_darkest"], knee, foot, 5)
            _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["cloth_dark"], knee, foot, 4)
            _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["cloth_mid"],
                                        (knee[0], knee[1] - 1), (foot[0], foot[1] - 1), 2)
            # Boot (gold ankle band)
            pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["gold_dark"],
                             (foot[0] - 3, foot[1] - 1, 6, 3))
            pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["gold_mid"],
                             (foot[0] - 3, foot[1] - 1, 6, 1))
            pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["gold_light"],
                             (foot[0] - 2, foot[1] - 1, 1, 1))
    def _draw_torso(surface, cx, cy, facing, phase):
        """Muscular torso with dark gilet."""
        breath = math.sin(phase * 0.7) * 1
        # Body shape (V-taper muscular)
        torso_shape = [
            (cx - 11, cy - 8),   # shoulder L
            (cx - 12, cy - 5),
            (cx - 10, cy + 4),   # side
            (cx - 7, cy + 10),   # hip L
            (cx - 4, cy + 12),
            (cx + 4, cy + 12),
            (cx + 7, cy + 10),   # hip R
            (cx + 10, cy + 4),
            (cx + 12, cy - 5),
            (cx + 11, cy - 8),   # shoulder R
            (cx + 4, cy - 10),
            (cx - 4, cy - 10),
        ]
        # Shadow
        _NS_kaizoku_raijin._poly(surface, _NS_kaizoku_raijin.PALETTE["shadow_deep"],
                                  [(p[0] + 2, p[1] + 2) for p in torso_shape])
        # Skin (chest/arms visible)
        _NS_kaizoku_raijin._poly(surface, _NS_kaizoku_raijin.PALETTE["skin_darkest"], torso_shape)
        _NS_kaizoku_raijin._poly(surface, _NS_kaizoku_raijin.PALETTE["skin_dark"], [
            (cx - 10, cy - 7),
            (cx - 11, cy - 4),
            (cx - 9, cy + 3),
            (cx - 6, cy + 9),
            (cx + 6, cy + 9),
            (cx + 9, cy + 3),
            (cx + 11, cy - 4),
            (cx + 10, cy - 7),
            (cx + 3, cy - 9),
            (cx - 3, cy - 9),
        ])
        # Dark gilet (sleeveless vest)
        _NS_kaizoku_raijin._poly(surface, _NS_kaizoku_raijin.PALETTE["cloth_darkest"], [
            (cx - 8, cy - 6),
            (cx - 9, cy - 3),
            (cx - 8, cy + 4),
            (cx - 6, cy + 10),
            (cx + 6, cy + 10),
            (cx + 8, cy + 4),
            (cx + 9, cy - 3),
            (cx + 8, cy - 6),
            (cx + 3, cy - 8),
            (cx - 3, cy - 8),
        ])
        _NS_kaizoku_raijin._poly(surface, _NS_kaizoku_raijin.PALETTE["cloth_dark"], [
            (cx - 7, cy - 5),
            (cx - 8, cy),
            (cx - 6, cy + 8),
            (cx + 6, cy + 8),
            (cx + 8, cy),
            (cx + 7, cy - 5),
        ])
        _NS_kaizoku_raijin._poly(surface, _NS_kaizoku_raijin.PALETTE["cloth_mid"], [
            (cx - 6, cy - 3),
            (cx - 7, cy + 2),
            (cx - 5, cy + 6),
            (cx + 5, cy + 6),
            (cx + 7, cy + 2),
            (cx + 6, cy - 3),
        ])
        # Center chest gap (V-neck showing skin)
        _NS_kaizoku_raijin._poly(surface, _NS_kaizoku_raijin.PALETTE["skin_dark"], [
            (cx - 2, cy - 8),
            (cx + 2, cy - 8),
            (cx + 1, cy - 2),
            (cx, cy),
            (cx - 1, cy - 2),
        ])
        _NS_kaizoku_raijin._poly(surface, _NS_kaizoku_raijin.PALETTE["skin_mid"], [
            (cx - 1, cy - 7),
            (cx + 1, cy - 7),
            (cx, cy - 3),
        ])
        # Muscle definition (highlights on chest)
        pygame.draw.line(surface, _NS_kaizoku_raijin.PALETTE["skin_light"],
                         (cx - 6, cy - 5), (cx - 4, cy - 6), 1)
        pygame.draw.line(surface, _NS_kaizoku_raijin.PALETTE["skin_light"],
                         (cx + 4, cy - 6), (cx + 6, cy - 5), 1)
        # Gold belt
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["gold_darkest"],
                         (cx - 8, cy + 9, 16, 4))
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["gold_dark"],
                         (cx - 8, cy + 9, 16, 3))
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["gold_mid"],
                         (cx - 8, cy + 9, 16, 1))
        # Belt buckle
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["gold_light"],
                         (cx - 2, cy + 9, 4, 3))
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["gold_shine"],
                         (cx - 1, cy + 10, 2, 1))
    def _draw_arm_with_blade(surface, cx, cy, facing, arm_angle, phase, is_back=False):
        """Arm holding a nichirin blade at given angle."""
        alpha_mult = 0.85 if is_back else 1.0
        # Shoulder position
        shoulder_x = cx
        shoulder_y = cy
        # Arm length
        upper_len = 11
        forearm_len = 11
        # Base angle: pointing DOWN by default, modified by arm_angle
        # arm_angle 0 = arm hanging down
        # arm_angle -pi/2 = arm straight up
        # arm_angle +pi/2 = arm straight forward
        base_angle = math.pi / 2 + arm_angle  # pi/2 = down
        # Elbow position (from shoulder)
        elbow_x = shoulder_x + int(math.cos(base_angle) * upper_len * facing) if False else \
                  shoulder_x + int(math.sin(arm_angle) * upper_len) * facing
        elbow_y = shoulder_y + int(math.cos(arm_angle) * upper_len)
        # Wrist position (forearm slightly bent)
        forearm_angle = arm_angle + 0.2  # slight elbow bend
        wrist_x = elbow_x + int(math.sin(forearm_angle) * forearm_len) * facing
        wrist_y = elbow_y + int(math.cos(forearm_angle) * forearm_len)
        # Draw arm - shadow
        _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["shadow_deep"],
                                    (shoulder_x + 1, shoulder_y + 1),
                                    (elbow_x + 1, elbow_y + 1), 6)
        _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["shadow_deep"],
                                    (elbow_x + 1, elbow_y + 1),
                                    (wrist_x + 1, wrist_y + 1), 5)
        # Upper arm (skin)
        _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["skin_darkest"],
                                    (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["skin_dark"],
                                    (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["skin_mid"],
                                    (shoulder_x, shoulder_y - 1),
                                    (elbow_x, elbow_y - 1), 3)
        _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["skin_light"],
                                    (shoulder_x, shoulder_y - 2),
                                    (elbow_x, elbow_y - 2), 1)
        # Gold armband on upper arm
        mid_x = (shoulder_x + elbow_x) // 2
        mid_y = (shoulder_y + elbow_y) // 2
        _NS_kaizoku_raijin._aacircle(surface, _NS_kaizoku_raijin.PALETTE["gold_darkest"],
                                      (mid_x, mid_y), 4)
        _NS_kaizoku_raijin._aacircle(surface, _NS_kaizoku_raijin.PALETTE["gold_dark"],
                                      (mid_x, mid_y), 3)
        _NS_kaizoku_raijin._aacircle(surface, _NS_kaizoku_raijin.PALETTE["gold_mid"],
                                      (mid_x, mid_y - 1), 2)
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["gold_shine"],
                         (mid_x, mid_y - 2, 1, 1))
        # Forearm (skin)
        _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["skin_darkest"],
                                    (elbow_x, elbow_y), (wrist_x, wrist_y), 5)
        _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["skin_dark"],
                                    (elbow_x, elbow_y), (wrist_x, wrist_y), 4)
        _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["skin_mid"],
                                    (elbow_x, elbow_y - 1),
                                    (wrist_x, wrist_y - 1), 2)
        # Wrist wrap (dark)
        _NS_kaizoku_raijin._aacircle(surface, _NS_kaizoku_raijin.PALETTE["cloth_darkest"],
                                      (wrist_x, wrist_y), 3)
        _NS_kaizoku_raijin._aacircle(surface, _NS_kaizoku_raijin.PALETTE["cloth_dark"],
                                      (wrist_x, wrist_y), 2)
        # Draw the NICHIRIN BLADE - blade points in continuation of forearm
        blade_angle = forearm_angle
        _NS_kaizoku_raijin._draw_nichirin_blade(surface, wrist_x, wrist_y,
                                                 blade_angle, facing, phase, alpha_mult)
    def _draw_nichirin_blade(surface, hx, hy, angle, facing, phase, alpha_mult=1.0):
        """Nichirin katana - dark blade with gold edge.
        angle: 0 = blade pointing down, -pi/2 = up, +pi/2 = forward
        """
        handle_len = 6
        blade_len = 24
        # Direction vector based on angle (angle 0 = down)
        dir_x = math.sin(angle) * facing
        dir_y = math.cos(angle)
        # Handle end (opposite of blade)
        handle_end_x = hx - int(dir_x * handle_len)
        handle_end_y = hy - int(dir_y * handle_len)
        # Blade tip
        blade_tip_x = hx + int(dir_x * blade_len)
        blade_tip_y = hy + int(dir_y * blade_len)
        # Perpendicular for blade thickness
        perp_x = -dir_y
        perp_y = dir_x
        # Handle (dark wrapped)
        _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["shadow_deep"],
                                    (handle_end_x + 1, handle_end_y + 1),
                                    (hx + 1, hy + 1), 5)
        _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["cloth_darkest"],
                                    (handle_end_x, handle_end_y), (hx, hy), 4)
        _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["cloth_dark"],
                                    (handle_end_x, handle_end_y), (hx, hy), 3)
        # Gold handle wrap details
        for i in range(3):
            t = (i + 1) / 4
            wx = int(handle_end_x + (hx - handle_end_x) * t)
            wy = int(handle_end_y + (hy - handle_end_y) * t)
            pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["gold_mid"], (wx, wy, 1, 1))
        # Guard (tsuba) - gold
        guard_a = (hx + int(perp_x * 3), hy + int(perp_y * 3))
        guard_b = (hx - int(perp_x * 3), hy - int(perp_y * 3))
        _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["gold_darkest"],
                                    guard_a, guard_b, 3)
        _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["gold_dark"],
                                    guard_a, guard_b, 2)
        _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["gold_mid"],
                                    guard_a, guard_b, 1)
        # Blade shape (curved katana)
        blade_base_a = (hx + int(perp_x * 2),
                        hy + int(perp_y * 2))
        blade_base_b = (hx - int(perp_x * 2),
                        hy - int(perp_y * 2))
        blade_mid_a = (int(hx + (blade_tip_x - hx) * 0.6 + perp_x * 1.5),
                       int(hy + (blade_tip_y - hy) * 0.6 + perp_y * 1.5))
        blade_mid_b = (int(hx + (blade_tip_x - hx) * 0.6 - perp_x * 1.5),
                       int(hy + (blade_tip_y - hy) * 0.6 - perp_y * 1.5))
        blade_poly = [blade_base_a, blade_mid_a, (blade_tip_x, blade_tip_y),
                      blade_mid_b, blade_base_b]
        # Shadow
        _NS_kaizoku_raijin._poly(surface, _NS_kaizoku_raijin.PALETTE["shadow_deep"],
                                  [(p[0] + 1, p[1] + 1) for p in blade_poly])
        # Dark blade fill
        _NS_kaizoku_raijin._poly(surface, _NS_kaizoku_raijin.PALETTE["blade_darkest"], blade_poly)
        _NS_kaizoku_raijin._poly(surface, _NS_kaizoku_raijin.PALETTE["blade_dark"], [
            (int(blade_base_a[0] * 0.8 + blade_base_b[0] * 0.2),
             int(blade_base_a[1] * 0.8 + blade_base_b[1] * 0.2)),
            blade_mid_a,
            (blade_tip_x, blade_tip_y),
            blade_mid_b,
            (int(blade_base_b[0] * 0.8 + blade_base_a[0] * 0.2),
             int(blade_base_b[1] * 0.8 + blade_base_a[1] * 0.2)),
        ])
        # Gold cutting edge (top of blade)
        _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["blade_dark"],
                                    blade_base_a, blade_mid_a, 2)
        _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["blade_edge"],
                                    blade_base_a, blade_mid_a, 1)
        _NS_kaizoku_raijin._aaline(surface, _NS_kaizoku_raijin.PALETTE["blade_edge"],
                                    blade_mid_a, (blade_tip_x, blade_tip_y), 1)
        # Blade shine
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["blade_shine"],
                         (blade_mid_a[0], blade_mid_a[1], 1, 1))
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["blade_shine"],
                         (blade_tip_x, blade_tip_y, 1, 1))
        # Small gold glow on blade tip
        _NS_kaizoku_raijin._aacircle(surface, _NS_kaizoku_raijin.PALETTE["sound_light"],
                                      (blade_tip_x, blade_tip_y), 2)
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["sound_shine"],
                         (blade_tip_x, blade_tip_y, 1, 1))
    def _draw_head(surface, cx, cy, facing, phase):
        """Head with silver hair, jeweled headband, red eye, face markings."""
        # Neck
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["shadow_deep"],
                         (cx - 3, cy + 8, 6, 5))
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["skin_darkest"],
                         (cx - 3, cy + 7, 6, 5))
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["skin_dark"],
                         (cx - 2, cy + 7, 4, 4))
        # Head shape (oval)
        head_shape = [
            (cx - 7, cy - 2),
            (cx - 8, cy + 2),
            (cx - 7, cy + 6),
            (cx - 4, cy + 9),
            (cx + 4, cy + 9),
            (cx + 7, cy + 6),
            (cx + 8, cy + 2),
            (cx + 7, cy - 2),
            (cx + 5, cy - 6),
            (cx - 5, cy - 6),
        ]
        _NS_kaizoku_raijin._poly(surface, _NS_kaizoku_raijin.PALETTE["shadow_deep"],
                                  [(p[0] + 1, p[1] + 2) for p in head_shape])
        _NS_kaizoku_raijin._poly(surface, _NS_kaizoku_raijin.PALETTE["skin_darkest"], head_shape)
        # Skin fill
        _NS_kaizoku_raijin._poly(surface, _NS_kaizoku_raijin.PALETTE["skin_dark"], [
            (cx - 6, cy - 1),
            (cx - 7, cy + 2),
            (cx - 6, cy + 5),
            (cx - 3, cy + 8),
            (cx + 3, cy + 8),
            (cx + 6, cy + 5),
            (cx + 7, cy + 2),
            (cx + 6, cy - 1),
            (cx + 4, cy - 5),
            (cx - 4, cy - 5),
        ])
        _NS_kaizoku_raijin._poly(surface, _NS_kaizoku_raijin.PALETTE["skin_mid"], [
            (cx - 5, cy),
            (cx - 6, cy + 3),
            (cx - 4, cy + 6),
            (cx + 4, cy + 6),
            (cx + 6, cy + 3),
            (cx + 5, cy),
            (cx + 3, cy - 4),
            (cx - 3, cy - 4),
        ])
        # Skin highlight
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["skin_light"],
                         (cx - 2 + facing, cy - 2, 3, 2))
        # HAIR (silver, flowing back)
        # Top hair
        _NS_kaizoku_raijin._poly(surface, _NS_kaizoku_raijin.PALETTE["hair_darkest"], [
            (cx - 8, cy - 3),
            (cx - 9, cy - 5),
            (cx - 6, cy - 8),
            (cx, cy - 9),
            (cx + 6, cy - 8),
            (cx + 9, cy - 5),
            (cx + 8, cy - 3),
            (cx + 5, cy - 5),
            (cx - 5, cy - 5),
        ])
        _NS_kaizoku_raijin._poly(surface, _NS_kaizoku_raijin.PALETTE["hair_dark"], [
            (cx - 7, cy - 4),
            (cx - 8, cy - 5),
            (cx - 5, cy - 7),
            (cx, cy - 8),
            (cx + 5, cy - 7),
            (cx + 8, cy - 5),
            (cx + 7, cy - 4),
        ])
        _NS_kaizoku_raijin._poly(surface, _NS_kaizoku_raijin.PALETTE["hair_mid"], [
            (cx - 5, cy - 5),
            (cx - 6, cy - 6),
            (cx - 3, cy - 7),
            (cx, cy - 7),
            (cx + 3, cy - 7),
            (cx + 6, cy - 6),
            (cx + 5, cy - 5),
        ])
        _NS_kaizoku_raijin._poly(surface, _NS_kaizoku_raijin.PALETTE["hair_light"], [
            (cx - 2, cy - 6),
            (cx + 2, cy - 6),
            (cx + 1, cy - 4),
            (cx - 1, cy - 4),
        ])
        # Long hair flowing back
        back_dir = -facing
        for i in range(4):
            t = i / 3
            hx = cx + back_dir * (7 + i * 3)
            hy = cy - 2 + int(math.sin(phase * 0.5 + i) * 1) + i
            pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["hair_darkest"],
                             (hx - 1, hy, 3, 3 - i // 2))
            pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["hair_dark"],
                             (hx - 1, hy, 2, 2))
            pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["hair_mid"],
                             (hx, hy, 1, 1))
        # HEADBAND (dark cloth with jewels)
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["cloth_darkest"],
                         (cx - 7, cy - 4, 14, 3))
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["cloth_dark"],
                         (cx - 7, cy - 4, 14, 2))
        # Red jewels on headband (3 gems)
        for jx in (-4, 0, 4):
            jewel_pulse = math.sin(phase * 2 + jx) * 0.3 + 0.7
            # Glow
            for r in range(3, 0, -1):
                alpha = _NS_kaizoku_raijin._alpha(120 * (3 - r) / 3 * jewel_pulse)
                _NS_kaizoku_raijin._aacircle(surface,
                                              (*_NS_kaizoku_raijin.PALETTE["jewel_mid"], alpha),
                                              (cx + jx, cy - 3), r)
            pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["jewel_darkest"],
                             (cx + jx - 1, cy - 3, 2, 2))
            pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["jewel_mid"],
                             (cx + jx - 1, cy - 3, 2, 1))
            pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["jewel_light"],
                             (cx + jx, cy - 3, 1, 1))
        # EYE (red, intense)
        eye_x = cx + facing * 2
        eye_y = cy + 1
        # Glow halo
        for r in range(4, 0, -1):
            alpha = _NS_kaizoku_raijin._alpha(80 * (4 - r) / 4)
            _NS_kaizoku_raijin._aacircle(surface,
                                          (*_NS_kaizoku_raijin.PALETTE["jewel_mid"], alpha),
                                          (eye_x, eye_y), r)
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["shadow_deep"],
                         (eye_x - 1, eye_y - 1, 3, 2))
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["jewel_darkest"],
                         (eye_x - 1, eye_y, 3, 1))
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["jewel_mid"],
                         (eye_x, eye_y, 2, 1))
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["jewel_light"],
                         (eye_x + 1, eye_y, 1, 1))
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["jewel_glow"],
                         (eye_x, eye_y, 1, 1))
        # Face markings (red dots on cheek - festival makeup)
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["jewel_dark"],
                         (cx - facing * 3, cy + 4, 2, 1))
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["jewel_mid"],
                         (cx - facing * 3, cy + 4, 1, 1))
        # Mouth (slight smirk)
        pygame.draw.line(surface, _NS_kaizoku_raijin.PALETTE["skin_darkest"],
                         (cx - 1, cy + 6), (cx + 2, cy + 6), 1)
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["skin_darkest"],
                         (cx + 2, cy + 5, 1, 1))
    # ============================================================
    # SWORD SLASH FX (melee attack)
    # ============================================================
    # ============================================================
    # SWORD SLASH FX (melee attack) - Natural diagonal slash
    # ============================================================
    def _draw_sword_slash_fx(surface, boss, x, y, progress):
        """Big golden crescent slash - diagonal top-to-forward swing."""
        if progress < 0.35 or progress > 0.9:
            return
        facing = boss.direction
        t = (progress - 0.35) / 0.55
        t = min(1.0, t)
        # Pivot point: at boss shoulder area
        arc_cx = x
        arc_cy = y - 8
        # Arc radius
        radius = int(32 + t * 8)
        # Swing angle sweep (in pygame coords: 0=right, pi/2=DOWN, -pi/2=UP)
        # Natural diagonal slash: from UP-BACK to FORWARD-DOWN
        # facing=1 (right): start from upper-left, sweep to lower-right
        # facing=-1 (left): start from upper-right, sweep to lower-left
        if facing == 1:
            sweep_start = -math.pi * 0.85  # up-slightly-left
            sweep_end = math.pi * 0.15     # slightly down-right (forward)
        else:
            sweep_start = -math.pi * 0.15  # up-slightly-right
            sweep_end = math.pi * 0.85 + math.pi * 0.7  # forward-left-down
            # simplify: just mirror
            sweep_start = math.pi + math.pi * 0.15
            sweep_end = math.pi - math.pi * 0.15 - math.pi * 0.7
        # Cleaner approach - use facing multiplier
        # Angle 0 = pointing right (forward if facing=1)
        # Negative Y = up in pygame
        base_start = -math.pi * 0.75   # up-back (75% toward up-behind)
        base_end = math.pi * 0.2       # forward-slight-down
        # For facing=1: swing from up-left over to down-right
        # For facing=-1: mirror horizontally
        if facing == 1:
            sweep_start = math.pi + math.pi * 0.25   # up-back-left (~225°)
            sweep_end = math.pi * 0.2                 # down-forward-right (~36°)
            # Swing direction: clockwise (angle increases)
            current_angle = sweep_start + (sweep_end - sweep_start + math.pi * 2) % (math.pi * 2) * t
            # Simpler: interpolate through the shortest path going clockwise
            current_angle = sweep_start - (sweep_start - sweep_end) * t
            if current_angle < sweep_end:
                current_angle = sweep_end
        else:
            sweep_start = -math.pi * 0.25   # up-back-right
            sweep_end = math.pi - math.pi * 0.2   # down-forward-left
            current_angle = sweep_start + (sweep_end - sweep_start) * t
        # Trail span (arc behind current position)
        trail_span = math.pi * 0.9
        # Multiple layered arcs for HD crescent
        for layer_i, (r_off, alpha_val, color, thickness) in enumerate([
            (7, 60, _NS_kaizoku_raijin.PALETTE["sound_darkest"], 6),
            (4, 100, _NS_kaizoku_raijin.PALETTE["sound_dark"], 5),
            (1, 180, _NS_kaizoku_raijin.PALETTE["sound_mid"], 4),
            (-1, 230, _NS_kaizoku_raijin.PALETTE["sound_light"], 3),
            (-3, 255, _NS_kaizoku_raijin.PALETTE["sound_hot"], 2),
            (-4, 255, _NS_kaizoku_raijin.PALETTE["sound_shine"], 1),
        ]):
            actual_alpha = _NS_kaizoku_raijin._alpha(alpha_val * (1 - t * 0.3))
            arc_r = radius + r_off
            if arc_r < 3:
                continue
            # Draw arc trail from current angle backwards
            num_segments = 26
            prev = None
            for seg in range(num_segments + 1):
                seg_t = seg / num_segments  # 0 = tail (oldest), 1 = leading edge
                # Trail goes BACKWARDS from current_angle
                # (opposite direction of swing)
                if facing == 1:
                    # Swing is going clockwise (angle decreasing then wrapping)
                    # Trail is at LARGER angles (behind current)
                    trail_angle = current_angle + trail_span * (1 - seg_t)
                else:
                    # Swing going counter-clockwise (angle increasing)
                    # Trail is at SMALLER angles
                    trail_angle = current_angle - trail_span * (1 - seg_t)
                # Fade tail
                seg_alpha = int(actual_alpha * (seg_t ** 0.6))
                if seg_alpha < 10:
                    prev = None
                    continue
                px = arc_cx + int(math.cos(trail_angle) * arc_r)
                py = arc_cy + int(math.sin(trail_angle) * arc_r)
                if prev is not None:
                    pygame.draw.line(surface, (*color, seg_alpha),
                                     prev, (px, py), thickness)
                prev = (px, py)
        # Bright leading edge (current tip of slash)
        tip_x = arc_cx + int(math.cos(current_angle) * radius)
        tip_y = arc_cy + int(math.sin(current_angle) * radius)
        # Big flash at leading edge
        for r in range(12, 0, -1):
            alpha = _NS_kaizoku_raijin._alpha(220 * (12 - r) / 12 * (1 - t * 0.5))
            _NS_kaizoku_raijin._aacircle(surface,
                                          (*_NS_kaizoku_raijin.PALETTE["sound_light"], alpha),
                                          (tip_x, tip_y), r)
        _NS_kaizoku_raijin._aacircle(surface, _NS_kaizoku_raijin.PALETTE["sound_hot"],
                                      (tip_x, tip_y), 4)
        _NS_kaizoku_raijin._aacircle(surface, _NS_kaizoku_raijin.PALETTE["sound_shine"],
                                      (tip_x, tip_y), 2)
        pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["white"],
                         (tip_x, tip_y, 1, 1))
        # Sparks bursting along the arc trail
        for i in range(16):
            spark_t = i / 15
            if facing == 1:
                spark_angle = current_angle + trail_span * (1 - spark_t)
            else:
                spark_angle = current_angle - trail_span * (1 - spark_t)
            spark_r = radius + int(math.sin(t * 8 + i) * 4)
            sx = arc_cx + int(math.cos(spark_angle) * spark_r)
            sy = arc_cy + int(math.sin(spark_angle) * spark_r)
            alpha = _NS_kaizoku_raijin._alpha(240 * (1 - t) * (spark_t ** 0.5))
            if alpha < 20:
                continue
            pygame.draw.rect(surface, (*_NS_kaizoku_raijin.PALETTE["sound_hot"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_kaizoku_raijin.PALETTE["sound_shine"], alpha),
                             (sx, sy, 1, 1))
        # Firework sparks emanating outward from tip
        for i in range(18):
            spark_t = i / 17
            if facing == 1:
                spark_angle = current_angle + trail_span * (1 - spark_t) * 0.7
            else:
                spark_angle = current_angle - trail_span * (1 - spark_t) * 0.7
            dist = radius + 8 + int(t * 20) + int(math.sin(i * 2) * 3)
            sx = arc_cx + int(math.cos(spark_angle) * dist)
            sy = arc_cy + int(math.sin(spark_angle) * dist)
            alpha = _NS_kaizoku_raijin._alpha(220 * (1 - t) * spark_t)
            colors = [_NS_kaizoku_raijin.PALETTE["sound_hot"],
                      _NS_kaizoku_raijin.PALETTE["spark_light"],
                      _NS_kaizoku_raijin.PALETTE["pink_light"],
                      _NS_kaizoku_raijin.PALETTE["sound_shine"]]
            color = colors[i % 4]
            size = 2 if i % 2 == 0 else 1
            pygame.draw.rect(surface, (*color, alpha), (sx, sy, size, size))
        # Motion blur streaks (radial from center out along arc trail)
        if t < 0.7:
            for i in range(6):
                blur_t = i / 5
                if facing == 1:
                    blur_angle = current_angle + trail_span * 0.4 * blur_t
                else:
                    blur_angle = current_angle - trail_span * 0.4 * blur_t
                inner_r = radius - 10
                outer_r = radius + 14
                x1 = arc_cx + int(math.cos(blur_angle) * inner_r)
                y1 = arc_cy + int(math.sin(blur_angle) * inner_r)
                x2 = arc_cx + int(math.cos(blur_angle) * outer_r)
                y2 = arc_cy + int(math.sin(blur_angle) * outer_r)
                alpha = _NS_kaizoku_raijin._alpha(180 * (1 - t) * (1 - blur_t))
                pygame.draw.line(surface, (*_NS_kaizoku_raijin.PALETTE["sound_light"], alpha),
                                 (x1, y1), (x2, y2), 1)
    # ============================================================
    # FLOATING SPARKS (below feet - festival sparkles)
    # ============================================================
    def _draw_floating_sparks(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Festival sparkles floating below character (like fireworks)."""
        strength = 1.5 if intense else 1.0
        # Base floating cloud
        cloud = pygame.Surface((100, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(20, 3, -2):
            alpha = _NS_kaizoku_raijin._alpha((20 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    cloud, (*_NS_kaizoku_raijin.PALETTE["sound_dark"], alpha),
                    (50 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2))
                )
        surface.blit(cloud, (cx - 50, cy - 10))
        # Rising sparks (gold, purple, pink)
        for i in range(10):
            t = (phase * 0.5 + i * 0.1) % 1.0
            sx = cx - 20 + i * 4 + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 20)
            alpha = _NS_kaizoku_raijin._alpha(240 * (1 - t) * strength)
            if alpha <= 0:
                continue
            # Cycle colors
            color_choice = i % 3
            if color_choice == 0:
                color = _NS_kaizoku_raijin.PALETTE["sound_mid"]
                hot = _NS_kaizoku_raijin.PALETTE["sound_hot"]
            elif color_choice == 1:
                color = _NS_kaizoku_raijin.PALETTE["spark_mid"]
                hot = _NS_kaizoku_raijin.PALETTE["spark_light"]
            else:
                color = _NS_kaizoku_raijin.PALETTE["pink_mid"]
                hot = _NS_kaizoku_raijin.PALETTE["pink_light"]
            pygame.draw.rect(surface, (*color, alpha), (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*hot, alpha), (sx, sy, 1, 1))
        # Ground sparkle ring
        for i in range(6):
            angle = phase * 0.5 + i * math.pi / 3
            sx = cx + int(math.cos(angle) * 15)
            sy = cy + int(math.sin(angle) * 4)
            alpha = _NS_kaizoku_raijin._alpha(200 * strength)
            pygame.draw.rect(surface, (*_NS_kaizoku_raijin.PALETTE["sound_shine"], alpha),
                             (sx, sy, 1, 1))
        # Trail behind (when moving)
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 10 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_kaizoku_raijin._alpha(150 - i * 25)
                if alpha <= 0:
                    continue
                _NS_kaizoku_raijin._aacircle(surface,
                                              (*_NS_kaizoku_raijin.PALETTE["sound_dark"], alpha),
                                              (sx, sy), max(2, 5 - i))
                pygame.draw.rect(surface, (*_NS_kaizoku_raijin.PALETTE["sound_light"], alpha),
                                 (sx, sy - 1, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius, 120 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 5, 2, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (60, 40, 5, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_festival_aura(surface, x, y, phase):
        """Gold + purple + pink festival aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_kaizoku_raijin._alpha((95 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_kaizoku_raijin._aacircle(aura,
                                              (*_NS_kaizoku_raijin.PALETTE["sound_darkest"], alpha),
                                              (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_kaizoku_raijin._alpha((60 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_kaizoku_raijin._aacircle(aura,
                                              (*_NS_kaizoku_raijin.PALETTE["sound_dark"], alpha),
                                              (110, 90), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_kaizoku_raijin._alpha((35 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_kaizoku_raijin._aacircle(aura,
                                              (*_NS_kaizoku_raijin.PALETTE["spark_dark"], alpha),
                                              (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        # Floating festival sparks around
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            color_i = i % 3
            if color_i == 0:
                color = _NS_kaizoku_raijin.PALETTE["sound_mid"]
                hot = _NS_kaizoku_raijin.PALETTE["sound_hot"]
            elif color_i == 1:
                color = _NS_kaizoku_raijin.PALETTE["spark_mid"]
                hot = _NS_kaizoku_raijin.PALETTE["spark_light"]
            else:
                color = _NS_kaizoku_raijin.PALETTE["pink_mid"]
                hot = _NS_kaizoku_raijin.PALETTE["pink_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot, (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Golden festival ground ring with runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_kaizoku_raijin.PALETTE["sound_dark"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_kaizoku_raijin.PALETTE["sound_mid"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_kaizoku_raijin.PALETTE["gold_mid"], 230),
                            (25, 22, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_kaizoku_raijin.PALETTE["spark_dark"], 180),
                            (40, 24, 90, 14), 1)
        # Runes (Japanese-style tick marks)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_kaizoku_raijin.PALETTE["sound_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                 (*_NS_kaizoku_raijin.PALETTE["sound_hot"],
                                  _NS_kaizoku_raijin._alpha(150 * pulse)),
                                 (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # SKILL Q: THUNDERCLAP AND FLASH - Horizontal slash shockwave
    # ============================================================
    def _draw_thunderclap_skill(surface, boss, x, y, timer, phase):
        """Fast horizontal slash with wide shockwave."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kaizoku_raijin._target_position(boss, x, y)
        if progress < 0.25:
            # Wind up flash near boss
            t = progress / 0.25
            fx = x + facing * 15
            fy = y - 10
            r = int(3 + t * 8)
            for radius in range(r + 4, 0, -1):
                alpha = _NS_kaizoku_raijin._alpha(180 * (r + 4 - radius) / (r + 4))
                _NS_kaizoku_raijin._aacircle(surface,
                                              (*_NS_kaizoku_raijin.PALETTE["sound_dark"], alpha),
                                              (fx, fy), radius)
            _NS_kaizoku_raijin._aacircle(surface, _NS_kaizoku_raijin.PALETTE["sound_mid"],
                                          (fx, fy), max(1, r - 2))
            _NS_kaizoku_raijin._aacircle(surface, _NS_kaizoku_raijin.PALETTE["sound_shine"],
                                          (fx, fy), max(1, r - 4))
        else:
            # Main slash - crescent horizontal slash beam
            t = (progress - 0.25) / 0.75
            # Slash extends from boss toward target
            start_x = x + facing * 15
            start_y = y - 10
            slash_len = int(140 + t * 40)
            end_x = start_x + facing * slash_len
            end_y = start_y
            # Crescent shape (thicker in middle)
            beam_height = int(30 - t * 10)
            # Layered crescent slash
            for layer_i, (h_off, alpha_val, color) in enumerate([
                (8, 80, _NS_kaizoku_raijin.PALETTE["sound_darkest"]),
                (5, 130, _NS_kaizoku_raijin.PALETTE["sound_dark"]),
                (2, 200, _NS_kaizoku_raijin.PALETTE["sound_mid"]),
                (0, 240, _NS_kaizoku_raijin.PALETTE["sound_light"]),
                (-2, 255, _NS_kaizoku_raijin.PALETTE["sound_shine"]),
            ]):
                actual_alpha = _NS_kaizoku_raijin._alpha(alpha_val * (1 - t * 0.6))
                h = beam_height + h_off
                if h < 2:
                    continue
                # Crescent points
                num_pts = 30
                top_pts = []
                bot_pts = []
                for i in range(num_pts + 1):
                    seg_t = i / num_pts
                    px = int(start_x + (end_x - start_x) * seg_t)
                    # Crescent curve
                    curve = math.sin(seg_t * math.pi) * h
                    top_pts.append((px, int(start_y - curve)))
                    bot_pts.append((px, int(start_y + curve * 0.3)))
                all_pts = top_pts + list(reversed(bot_pts))
                if len(all_pts) >= 3:
                    _NS_kaizoku_raijin._poly(surface, (*color, actual_alpha), all_pts)
            # Sparks along the slash
            for i in range(20):
                seg_t = i / 19
                px = int(start_x + (end_x - start_x) * seg_t)
                py = int(start_y - math.sin(seg_t * math.pi) * beam_height * 0.7)
                py += int(math.sin(phase * 5 + i) * 3)
                alpha = _NS_kaizoku_raijin._alpha(240 * (1 - t))
                pygame.draw.rect(surface, (*_NS_kaizoku_raijin.PALETTE["sound_hot"], alpha),
                                 (px, py, 2, 2))
                pygame.draw.rect(surface, (*_NS_kaizoku_raijin.PALETTE["sound_shine"], alpha),
                                 (px, py, 1, 1))
            # Endpoint burst
            if t < 0.5:
                burst_r = int(10 + t * 15)
                burst_alpha = _NS_kaizoku_raijin._alpha(240 * (1 - t * 2))
                for r in range(burst_r, 0, -2):
                    alpha = _NS_kaizoku_raijin._alpha(burst_alpha * r / burst_r)
                    _NS_kaizoku_raijin._aacircle(surface,
                                                  (*_NS_kaizoku_raijin.PALETTE["sound_light"], alpha),
                                                  (end_x, end_y), r)
    # ============================================================
    # SKILL W: RISING DRAGON - Spiral rising shockwave
    # ============================================================
    def _draw_rising_dragon_ground(surface, boss, x, y, timer, phase):
        """Ground swirl building up."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Spiral on ground
        for ring_i in range(3):
            r = int(15 + ring_i * 12 + progress * 20)
            alpha = _NS_kaizoku_raijin._alpha(180 - ring_i * 40)
            pygame.draw.ellipse(surface, (*_NS_kaizoku_raijin.PALETTE["wave_dark"], alpha),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_kaizoku_raijin.PALETTE["wave_mid"], alpha),
                                (x - r + 2, y + 40 - r // 3, r * 2 - 4, r * 2 // 3), 1)
    def _draw_rising_dragon_foreground(surface, boss, x, y, timer, phase):
        """Rising spiral of sound dragon."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Spiral rising column
        num_segments = 40
        max_height = 100
        for i in range(num_segments):
            seg_t = i / num_segments
            height = int(seg_t * max_height * min(1.0, progress * 2))
            spiral_angle = seg_t * math.pi * 6 + phase * 2
            spiral_r = int(15 + seg_t * 20)
            sx = x + int(math.cos(spiral_angle) * spiral_r)
            sy = y + 30 - height
            alpha = _NS_kaizoku_raijin._alpha(230 * (1 - seg_t * 0.6))
            # White spiral trail
            _NS_kaizoku_raijin._aacircle(surface,
                                          (*_NS_kaizoku_raijin.PALETTE["wave_dark"], alpha),
                                          (sx, sy), 5)
            _NS_kaizoku_raijin._aacircle(surface,
                                          (*_NS_kaizoku_raijin.PALETTE["wave_mid"], alpha),
                                          (sx, sy), 3)
            _NS_kaizoku_raijin._aacircle(surface,
                                          (*_NS_kaizoku_raijin.PALETTE["wave_light"], alpha),
                                          (sx, sy), 2)
            pygame.draw.rect(surface, (*_NS_kaizoku_raijin.PALETTE["wave_shine"], alpha),
                             (sx, sy, 1, 1))
        # Dragon head at top (bright orb)
        if progress > 0.3:
            head_y = y + 30 - max_height
            head_r = int(10 * min(1.0, (progress - 0.3) * 3))
            for r in range(head_r + 5, 0, -1):
                alpha = _NS_kaizoku_raijin._alpha(220 * (head_r + 5 - r) / (head_r + 5))
                _NS_kaizoku_raijin._aacircle(surface,
                                              (*_NS_kaizoku_raijin.PALETTE["wave_mid"], alpha),
                                              (x, head_y), r)
            _NS_kaizoku_raijin._aacircle(surface, _NS_kaizoku_raijin.PALETTE["wave_light"],
                                          (x, head_y), max(1, head_r - 2))
            _NS_kaizoku_raijin._aacircle(surface, _NS_kaizoku_raijin.PALETTE["wave_shine"],
                                          (x, head_y), max(1, head_r - 4))
            pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["white"],
                             (x, head_y, 1, 1))
        # Rising sparks
        for i in range(15):
            spark_t = (phase * 1.2 + i * 0.08) % 1.0
            angle = i * math.pi * 2 / 15 + phase
            sr = int(20 + spark_t * 15)
            sx = x + int(math.cos(angle) * sr)
            sy = y + 30 - int(spark_t * max_height)
            alpha = _NS_kaizoku_raijin._alpha(230 * (1 - spark_t))
            pygame.draw.rect(surface, (*_NS_kaizoku_raijin.PALETTE["wave_shine"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_kaizoku_raijin.PALETTE["sound_hot"], alpha),
                             (sx, sy, 1, 1))
    # ============================================================
    # SKILL E: STRING PERFORMANCE - Flurry of slashes
    # ============================================================
    def _draw_string_ground(surface, boss, x, y, timer, phase):
        """Rhythmic ground pulses."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Multiple concentric pulse rings
        for i in range(3):
            pulse_offset = (phase * 2 + i * 0.7) % 1.0
            r = int(20 + pulse_offset * 40)
            alpha = _NS_kaizoku_raijin._alpha(200 * (1 - pulse_offset))
            pygame.draw.ellipse(surface, (*_NS_kaizoku_raijin.PALETTE["sound_dark"], alpha),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_kaizoku_raijin.PALETTE["sound_mid"], alpha),
                                (x - r + 2, y + 40 - r // 3, r * 2 - 4, r * 2 // 3), 1)
    def _draw_string_foreground(surface, boss, x, y, timer, phase):
        """Multiple slash arcs around target - flurry."""
        tx, ty = _NS_kaizoku_raijin._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Multiple slashes at random angles around target
        num_slashes = 8
        for i in range(num_slashes):
            slash_phase = (phase * 2 + i * 0.4) % 1.0
            if slash_phase < 0.5:
                angle = i * math.pi * 2 / num_slashes + phase * 0.5
                # Slash arc
                arc_cx = tx + int(math.cos(angle) * 25)
                arc_cy = ty + int(math.sin(angle) * 25)
                slash_angle = angle + math.pi / 2
                slash_len = int(20 * (1 - slash_phase * 2))
                if slash_len < 3:
                    continue
                s1_x = arc_cx + int(math.cos(slash_angle) * slash_len)
                s1_y = arc_cy + int(math.sin(slash_angle) * slash_len)
                s2_x = arc_cx - int(math.cos(slash_angle) * slash_len)
                s2_y = arc_cy - int(math.sin(slash_angle) * slash_len)
                alpha = _NS_kaizoku_raijin._alpha(240 * (1 - slash_phase * 2))
                pygame.draw.line(surface, (*_NS_kaizoku_raijin.PALETTE["sound_darkest"], alpha),
                                 (s1_x, s1_y), (s2_x, s2_y), 4)
                pygame.draw.line(surface, (*_NS_kaizoku_raijin.PALETTE["sound_mid"], alpha),
                                 (s1_x, s1_y), (s2_x, s2_y), 3)
                pygame.draw.line(surface, (*_NS_kaizoku_raijin.PALETTE["sound_light"], alpha),
                                 (s1_x, s1_y), (s2_x, s2_y), 2)
                pygame.draw.line(surface, (*_NS_kaizoku_raijin.PALETTE["sound_shine"], alpha),
                                 (s1_x, s1_y), (s2_x, s2_y), 1)
                # Impact spark at slash center
                pygame.draw.rect(surface, (*_NS_kaizoku_raijin.PALETTE["sound_hot"], alpha),
                                 (arc_cx, arc_cy, 3, 3))
                pygame.draw.rect(surface, _NS_kaizoku_raijin.PALETTE["white"],
                                 (arc_cx, arc_cy, 1, 1))
        # Musical notes floating (musical performance)
        for i in range(6):
            note_t = (phase * 0.5 + i * 0.17) % 1.0
            note_x = tx + int(math.cos(phase + i) * 30) + int(math.sin(note_t * math.pi) * 10)
            note_y = ty - int(note_t * 40)
            alpha = _NS_kaizoku_raijin._alpha(220 * (1 - note_t))
            # Note head (circle)
            _NS_kaizoku_raijin._aacircle(surface,
                                          (*_NS_kaizoku_raijin.PALETTE["spark_dark"], alpha),
                                          (note_x, note_y), 3)
            _NS_kaizoku_raijin._aacircle(surface,
                                          (*_NS_kaizoku_raijin.PALETTE["spark_mid"], alpha),
                                          (note_x, note_y), 2)
            # Note stem
            pygame.draw.line(surface, (*_NS_kaizoku_raijin.PALETTE["spark_mid"], alpha),
                             (note_x + 2, note_y),
                             (note_x + 2, note_y - 6), 1)
            pygame.draw.rect(surface, (*_NS_kaizoku_raijin.PALETTE["spark_light"], alpha),
                             (note_x, note_y, 1, 1))
    # ============================================================
    # SKILL R: RHAPSODY - Dome of resonating sound
    # ============================================================
    def _draw_rhapsody_ground(surface, boss, x, y, timer, phase):
        """Ground purple resonating rings."""
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(4):
            pulse_offset = (phase * 1.5 + i * 0.5) % 1.0
            r = int(30 + pulse_offset * 50)
            alpha = _NS_kaizoku_raijin._alpha(180 * (1 - pulse_offset * 0.8))
            pygame.draw.ellipse(surface, (*_NS_kaizoku_raijin.PALETTE["spark_dark"], alpha),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_kaizoku_raijin.PALETTE["spark_mid"], alpha),
                                (x - r + 2, y + 40 - r // 3, r * 2 - 4, r * 2 // 3), 1)
    def _draw_rhapsody_foreground(surface, boss, x, y, timer, phase):
        """Dome of purple sound waves around boss."""
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Dome radius (breathing)
        breath = math.sin(phase * 2) * 4
        dome_r = 65 + int(breath)
        dome = pygame.Surface((dome_r * 2 + 20, dome_r * 2 + 20), pygame.SRCALPHA)
        center = (dome_r + 10, dome_r + 10)
        # Dome rings (multiple layers)
        for i, (thickness, alpha_val, color) in enumerate([
            (3, 100, _NS_kaizoku_raijin.PALETTE["spark_dark"]),
            (2, 150, _NS_kaizoku_raijin.PALETTE["spark_mid"]),
            (1, 200, _NS_kaizoku_raijin.PALETTE["spark_light"]),
        ]):
            _NS_kaizoku_raijin._aacircle(dome, (*color, alpha_val),
                                          center, dome_r - i, thickness)
        # Purple sound waves emanating outward (pulsing)
        for i in range(8):
            wave_t = (phase * 1.5 + i * 0.125) % 1.0
            wave_r = int(dome_r * wave_t)
            if wave_r < 5:
                continue
            alpha = _NS_kaizoku_raijin._alpha(200 * (1 - wave_t))
            _NS_kaizoku_raijin._aacircle(dome, (*_NS_kaizoku_raijin.PALETTE["spark_light"], alpha),
                                          center, wave_r, 2)
            _NS_kaizoku_raijin._aacircle(dome, (*_NS_kaizoku_raijin.PALETTE["pink_light"], alpha),
                                          center, wave_r - 1, 1)
        # Skull symbols floating around edge
        for i in range(6):
            angle = phase * 0.5 + i * math.pi / 3
            sx = center[0] + int(math.cos(angle) * dome_r * 0.9)
            sy = center[1] + int(math.sin(angle) * dome_r * 0.9)
            # Simple skull shape
            pygame.draw.rect(dome, _NS_kaizoku_raijin.PALETTE["spark_light"],
                             (sx - 2, sy - 2, 4, 3))
            pygame.draw.rect(dome, _NS_kaizoku_raijin.PALETTE["shadow_deep"],
                             (sx - 2, sy - 1, 1, 1))
            pygame.draw.rect(dome, _NS_kaizoku_raijin.PALETTE["shadow_deep"],
                             (sx + 1, sy - 1, 1, 1))
            pygame.draw.rect(dome, _NS_kaizoku_raijin.PALETTE["spark_light"],
                             (sx - 1, sy + 1, 3, 2))
        # Musical notes swirling around dome
        for i in range(10):
            angle = phase * 0.8 + i * math.pi / 5
            note_r = dome_r + int(math.sin(phase * 2 + i) * 5) - 8
            nx = center[0] + int(math.cos(angle) * note_r)
            ny = center[1] + int(math.sin(angle) * note_r)
            _NS_kaizoku_raijin._aacircle(dome, _NS_kaizoku_raijin.PALETTE["pink_mid"], (nx, ny), 2)
            pygame.draw.line(dome, _NS_kaizoku_raijin.PALETTE["pink_mid"],
                             (nx + 1, ny), (nx + 1, ny - 4), 1)
            pygame.draw.rect(dome, _NS_kaizoku_raijin.PALETTE["pink_light"], (nx, ny, 1, 1))
        surface.blit(dome, (x - dome_r - 10, y - dome_r - 10))
        # Extra bombardment - vibration bolts hitting ground around
        for i in range(4):
            bolt_phase = (phase * 2 + i * 0.25) % 1.0
            if bolt_phase < 0.4:
                angle = i * math.pi / 2 + phase * 0.3
                bolt_x = x + int(math.cos(angle) * (dome_r - 15))
                bolt_y_top = y - 30
                bolt_y_bot = y + int(math.sin(angle) * (dome_r - 15) * 0.4) + 20
                alpha = _NS_kaizoku_raijin._alpha(220 * (1 - bolt_phase * 2.5))
                pygame.draw.line(surface,
                                 (*_NS_kaizoku_raijin.PALETTE["spark_light"], alpha),
                                 (bolt_x, bolt_y_top), (bolt_x, bolt_y_bot), 3)
                pygame.draw.line(surface,
                                 (*_NS_kaizoku_raijin.PALETTE["pink_light"], alpha),
                                 (bolt_x, bolt_y_top), (bolt_x, bolt_y_bot), 1)
                # Impact
                _NS_kaizoku_raijin._aacircle(surface,
                                              (*_NS_kaizoku_raijin.PALETTE["spark_light"], alpha),
                                              (bolt_x, bolt_y_bot), 4)
# ============================================================
# CONVENIENCE WRAPPER (matches style of vhorethzir integration)
# ============================================================
def draw_kaizoku_raijin(surface, boss, x, y):
    _NS_kaizoku_raijin.draw_kaizoku_raijin(surface, boss, x, y)



# ====================================================================
# KOROKAI (MIRROR BLADE) - Mini Boss
# ====================================================================

class _NS_korokai:
    """Namespace korokai - Mirror Blade shinobi boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin tones
        "skin_shadow": (170, 135, 115),
        "skin_dark": (215, 180, 155),
        "skin_mid": (240, 210, 185),
        "skin_light": (255, 230, 205),
        "skin_shine": (255, 245, 225),
        # Silver/grey hair
        "hair_darkest": (60, 65, 75),
        "hair_dark": (120, 125, 135),
        "hair_mid": (180, 185, 195),
        "hair_light": (220, 225, 235),
        "hair_shine": (250, 252, 255),
        # Green flak vest
        "vest_darkest": (15, 35, 20),
        "vest_dark": (35, 65, 40),
        "vest_mid": (65, 105, 70),
        "vest_light": (100, 145, 100),
        "vest_shine": (155, 195, 150),
        # Dark blue shinobi uniform
        "uniform_darkest": (10, 15, 25),
        "uniform_dark": (25, 35, 55),
        "uniform_mid": (55, 70, 95),
        "uniform_light": (95, 115, 145),
        # Mask (dark navy - covers lower face)
        "mask_dark": (15, 20, 35),
        "mask_mid": (35, 45, 65),
        "mask_light": (65, 75, 100),
        # Headband metal
        "metal_dark": (55, 55, 65),
        "metal_mid": (140, 140, 155),
        "metal_light": (215, 215, 225),
        "metal_shine": (255, 255, 255),
        # Regular eye (dark grey)
        "eye_dark": (25, 25, 35),
        "eye_mid": (55, 55, 70),
        # CRIMSON MYSTIC EYE (W skill)
        "crimson_darkest": (55, 5, 5),
        "crimson_dark": (130, 15, 15),
        "crimson_mid": (210, 35, 35),
        "crimson_light": (255, 85, 65),
        "crimson_shine": (255, 180, 150),
        # Lightning blue (Q, E skills)
        "elec_darkest": (15, 30, 80),
        "elec_dark": (25, 75, 180),
        "elec_mid": (70, 160, 240),
        "elec_bright": (150, 220, 255),
        "elec_hot": (220, 245, 255),
        "elec_shine": (255, 255, 255),
        # Void purple (R skill)
        "void_darkest": (20, 5, 40),
        "void_dark": (55, 15, 100),
        "void_mid": (130, 45, 200),
        "void_light": (200, 130, 255),
        "void_shine": (240, 210, 255),
        # Steel (kunai)
        "steel_dark": (60, 65, 75),
        "steel_mid": (130, 140, 155),
        "steel_light": (200, 210, 220),
        "steel_shine": (250, 252, 255),
        # Gloves (dark)
        "glove_dark": (15, 15, 20),
        "glove_mid": (35, 35, 45),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_korokai._clamp(color)
        if _NS_korokai.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_korokai._clamp(color)
        if _NS_korokai.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_korokai._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    def _draw_lightning_bolt(surface, start, end, color, width=2,
                             segments=6, jitter=6, alpha=255):
        """Draw jagged lightning bolt between two points."""
        color = (*_NS_korokai._clamp(color), _NS_korokai._alpha(alpha))
        sx, sy = start
        ex, ey = end
        pts = [(sx, sy)]
        for i in range(1, segments):
            t = i / segments
            mx = sx + (ex - sx) * t
            my = sy + (ey - sy) * t
            dx = ex - sx
            dy = ey - sy
            length = max(1, math.sqrt(dx * dx + dy * dy))
            perp_x = -dy / length
            perp_y = dx / length
            j = (math.sin(i * 12.345 + t * 7.7) * jitter)
            pts.append((int(mx + perp_x * j), int(my + perp_y * j)))
        pts.append((ex, ey))
        for i in range(len(pts) - 1):
            pygame.draw.line(surface, color, pts[i], pts[i + 1], width)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_korokai(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_korokai._detect_moving(boss)
        _NS_korokai._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_kor_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind
        _NS_korokai._draw_shinobi_aura(surface, x, y, pulse)
        _NS_korokai._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "e":
            _NS_korokai._draw_lightning_pierce_ground(surface, boss, x, y,
                                                     skill_timer, pulse)
        elif active_skill == "r":
            _NS_korokai._draw_void_warp_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating bob
        float_bob = int(math.sin(pulse * 0.6) * 3)
        # Handle E lightning charge motion (body lunges forward)
        body_x_offset = 0
        if active_skill == "e":
            duration = 70
            e_prog = max(0.0, min(1.0, 1 - skill_timer / duration))
            if 0.35 < e_prog < 0.7:
                # Dashing forward with chidori
                dash_t = (e_prog - 0.35) / 0.35
                tx, ty = _NS_korokai._target_position(boss, x, y)
                body_x_offset = int((tx - x - boss.direction * 40) * dash_t)
        # Body (always floating)
        actual_x = x + body_x_offset
        actual_y = y + float_bob
        if attacking:
            _NS_korokai._draw_body_attack(surface, boss, actual_x, actual_y)
        elif moving:
            _NS_korokai._draw_body_walk(surface, boss, actual_x, actual_y)
        else:
            _NS_korokai._draw_body_idle(surface, boss, actual_x, actual_y)
        # Determine if crimson eye is active (W, or during other skills)
        crimson_active = active_skill in ("w", "r", "e")
        # Re-draw eye area with crimson if active (over body)
        if crimson_active:
            _NS_korokai._draw_crimson_eye_overlay(surface, actual_x, actual_y - 22,
                                                 boss.direction, pulse,
                                                 active_skill == "r")
        # W - Purple aura shield (over body)
        if active_skill == "w":
            _NS_korokai._draw_mirror_eye_aura(surface, boss, x, y + float_bob,
                                             skill_timer, pulse)
        # Foreground FX
        if active_skill == "q":
            _NS_korokai._draw_thunder_kunai_skill(surface, boss, x, y,
                                                 skill_timer, pulse)
        elif active_skill == "e":
            _NS_korokai._draw_lightning_pierce_skill(surface, boss, actual_x,
                                                    y + float_bob, skill_timer,
                                                    pulse, body_x_offset)
        elif active_skill == "r":
            _NS_korokai._draw_void_warp_skill(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kor_previous_timer", 0))
        active = bool(getattr(boss, "_kor_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._kor_attack_active = True
            boss._kor_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._kor_attack_frame = int(getattr(boss, "_kor_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._kor_attack_active = False
            boss._kor_attack_frame = 0
            active = False
        boss._kor_previous_timer = timer
        boss._kor_attack_progress = (
            min(1.0, getattr(boss, "_kor_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_kor_last_x"):
            boss._kor_last_x = boss.x
            boss._kor_last_y = boss.y
            return False
        dx = abs(boss.x - boss._kor_last_x)
        dy = abs(boss.y - boss._kor_last_y)
        boss._kor_last_x = boss.x
        boss._kor_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        _NS_korokai._draw_shadow(surface, x, y + 50)
        _NS_korokai._draw_shinobi_mist(surface, x, y + 44, boss.pulse)
        _NS_korokai._draw_body(surface, x, y, boss.direction, boss.pulse, "idle")
    def _draw_body_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_korokai._draw_shadow(surface, x + sway, y + 50)
        _NS_korokai._draw_shinobi_mist(surface, x + sway, y + 44, phase, trail=True,
                                       facing=boss.direction)
        _NS_korokai._draw_body(surface, x + sway, y, boss.direction, phase, "walk")
    def _draw_body_attack(surface, boss, x, y):
        progress = getattr(boss, "_kor_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Slash motion
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 4) * boss.direction
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-4 + t * 14)) * boss.direction
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(10 * (1 - t)) * boss.direction
        _NS_korokai._draw_shadow(surface, x + lunge, y + 50)
        _NS_korokai._draw_shinobi_mist(surface, x + lunge, y + 44, boss.pulse,
                                       intense=True)
        _NS_korokai._draw_body(surface, x + lunge, y, boss.direction, boss.pulse,
                               "attack", progress)
        _NS_korokai._draw_kunai_slash(surface, boss, x + lunge, y, progress)
    # ============================================================
    # BODY DRAWING
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw shinobi: green vest, dark uniform, masked face, silver hair."""
        arm_swing = 0
        if action == "attack":
            if attack_progress < 0.35:
                arm_swing = -int(attack_progress / 0.35 * 12) * facing
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                arm_swing = int((-12 + t * 32)) * facing
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_swing = int(20 * (1 - t)) * facing
        # Back arm
        _NS_korokai._draw_arm(surface, cx - facing * 8, cy - 4, facing, phase,
                              -arm_swing // 2, back=True)
        # Body (vest + uniform)
        _NS_korokai._draw_torso(surface, cx, cy, facing, phase, action)
        # Front arm holding kunai
        _NS_korokai._draw_arm_with_kunai(surface, cx + facing * 6, cy - 4, facing,
                                        phase, arm_swing, action, attack_progress)
        # Head
        _NS_korokai._draw_head(surface, cx, cy - 22, facing, phase, action)
    def _draw_torso(surface, cx, cy, facing, phase, action):
        """Green flak vest over dark uniform."""
        sway = math.sin(phase * 0.7) * 1
        # UNIFORM (base layer, dark blue)
        uniform_shape = [
            (cx - 12, cy - 8),
            (cx - 13, cy - 2),
            (cx - 13, cy + 8),
            (cx - 11, cy + 20),
            (cx - 8, cy + 30),
            (cx - 3, cy + 34),
            (cx + 3, cy + 34),
            (cx + 8, cy + 30),
            (cx + 11, cy + 20),
            (cx + 13, cy + 8),
            (cx + 13, cy - 2),
            (cx + 12, cy - 8),
        ]
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["shadow_deep"],
                          [(px + 2, py + 3) for px, py in uniform_shape])
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["uniform_darkest"], uniform_shape)
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["uniform_dark"], [
            (cx - 11, cy - 7),
            (cx - 12, cy - 1),
            (cx - 12, cy + 8),
            (cx - 10, cy + 19),
            (cx - 7, cy + 29),
            (cx + 7, cy + 29),
            (cx + 10, cy + 19),
            (cx + 12, cy + 8),
            (cx + 12, cy - 1),
            (cx + 11, cy - 7),
        ])
        # GREEN FLAK VEST (over uniform, upper torso)
        vest_shape = [
            (cx - 12, cy - 6),
            (cx - 13, cy),
            (cx - 12, cy + 8),
            (cx - 10, cy + 18),
            (cx + 10, cy + 18),
            (cx + 12, cy + 8),
            (cx + 13, cy),
            (cx + 12, cy - 6),
        ]
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["vest_darkest"], vest_shape)
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["vest_dark"], [
            (cx - 11, cy - 5),
            (cx - 12, cy),
            (cx - 11, cy + 8),
            (cx - 9, cy + 17),
            (cx + 9, cy + 17),
            (cx + 11, cy + 8),
            (cx + 12, cy),
            (cx + 11, cy - 5),
        ])
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["vest_mid"], [
            (cx - 9, cy - 3),
            (cx - 10, cy + 2),
            (cx - 9, cy + 10),
            (cx - 7, cy + 16),
            (cx + 7, cy + 16),
            (cx + 9, cy + 10),
            (cx + 10, cy + 2),
            (cx + 9, cy - 3),
        ])
        # Vest highlight
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["vest_light"], [
            (cx - 6, cy - 1),
            (cx - 7, cy + 6),
            (cx - 5, cy + 14),
            (cx + 5, cy + 14),
            (cx + 7, cy + 6),
            (cx + 6, cy - 1),
        ])
        pygame.draw.line(surface, _NS_korokai.PALETTE["vest_shine"],
                         (cx - 3, cy), (cx - 3, cy + 12), 1)
        # Central vest opening/zipper line
        pygame.draw.line(surface, _NS_korokai.PALETTE["vest_darkest"],
                         (cx, cy - 4), (cx, cy + 16), 1)
        pygame.draw.line(surface, _NS_korokai.PALETTE["vest_shine"],
                         (cx + 1, cy - 4), (cx + 1, cy + 16), 1)
        # Chest pouches (small squares on chest)
        for pouch_side in (-1, 1):
            px = cx + pouch_side * 5
            py = cy + 4
            _NS_korokai._poly(surface, _NS_korokai.PALETTE["vest_darkest"], [
                (px - 3, py - 2), (px + 3, py - 2),
                (px + 3, py + 4), (px - 3, py + 4),
            ])
            _NS_korokai._poly(surface, _NS_korokai.PALETTE["vest_dark"], [
                (px - 2, py - 1), (px + 2, py - 1),
                (px + 2, py + 3), (px - 2, py + 3),
            ])
            pygame.draw.line(surface, _NS_korokai.PALETTE["vest_mid"],
                             (px - 2, py + 1), (px + 2, py + 1), 1)
        # Red spiral symbol on left shoulder
        _NS_korokai._aacircle(surface, _NS_korokai.PALETTE["crimson_dark"],
                              (cx - 9, cy - 3), 3)
        _NS_korokai._aacircle(surface, _NS_korokai.PALETTE["crimson_mid"],
                              (cx - 9, cy - 3), 2, 1)
        _NS_korokai._aacircle(surface, _NS_korokai.PALETTE["crimson_light"],
                              (cx - 9, cy - 3), 1)
        # Belt/waist
        pygame.draw.line(surface, _NS_korokai.PALETTE["uniform_darkest"],
                         (cx - 11, cy + 17), (cx + 11, cy + 17), 2)
        pygame.draw.line(surface, _NS_korokai.PALETTE["uniform_mid"],
                         (cx - 10, cy + 18), (cx + 10, cy + 18), 1)
        # Pants (visible below vest)
        # Legs
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["uniform_darkest"], [
            (cx - 9, cy + 20),
            (cx - 10, cy + 30),
            (cx - 7, cy + 34),
            (cx - 3, cy + 34),
            (cx - 2, cy + 24),
            (cx - 2, cy + 20),
        ])
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["uniform_darkest"], [
            (cx + 2, cy + 20),
            (cx + 2, cy + 24),
            (cx + 3, cy + 34),
            (cx + 7, cy + 34),
            (cx + 10, cy + 30),
            (cx + 9, cy + 20),
        ])
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["uniform_dark"], [
            (cx - 8, cy + 21),
            (cx - 9, cy + 29),
            (cx - 6, cy + 33),
            (cx - 3, cy + 33),
            (cx - 3, cy + 21),
        ])
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["uniform_dark"], [
            (cx + 3, cy + 21),
            (cx + 3, cy + 33),
            (cx + 6, cy + 33),
            (cx + 9, cy + 29),
            (cx + 8, cy + 21),
        ])
        # Leg highlights
        pygame.draw.line(surface, _NS_korokai.PALETTE["uniform_mid"],
                         (cx - 7, cy + 23), (cx - 7, cy + 30), 1)
        pygame.draw.line(surface, _NS_korokai.PALETTE["uniform_mid"],
                         (cx + 7, cy + 23), (cx + 7, cy + 30), 1)
        # Bandage wraps on shins/ankles
        for leg_x in (-6, 6):
            wrap_x = cx + leg_x
            for wrap_y in (28, 31):
                pygame.draw.line(surface, _NS_korokai.PALETTE["hair_light"],
                                 (wrap_x - 2, cy + wrap_y),
                                 (wrap_x + 2, cy + wrap_y), 1)
    def _draw_arm(surface, cx, cy, facing, phase, swing, back=True):
        """Draw arm with dark uniform sleeve."""
        base_angle = math.pi * 0.5 + math.radians(swing)
        if back:
            base_angle = math.pi * 0.55
        shoulder_x = cx
        shoulder_y = cy
        elbow_len = 10
        elbow_x = shoulder_x + int(math.cos(base_angle) * elbow_len * facing * 0.4)
        elbow_y = shoulder_y + int(math.sin(base_angle) * elbow_len)
        hand_len = 12
        hand_angle = base_angle - math.radians(swing * 0.6)
        hand_x = elbow_x + int(math.cos(hand_angle) * hand_len * facing * 0.6)
        hand_y = elbow_y + int(math.sin(hand_angle) * hand_len)
        thickness = 6 if not back else 5
        color_main = _NS_korokai.PALETTE["uniform_darkest"] if back \
            else _NS_korokai.PALETTE["uniform_dark"]
        color_mid = _NS_korokai.PALETTE["uniform_dark"] if back \
            else _NS_korokai.PALETTE["uniform_mid"]
        # Shadow
        _NS_korokai._aaline(surface, _NS_korokai.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 2),
                            (elbow_x + 1, elbow_y + 2), thickness + 1)
        # Upper arm
        _NS_korokai._aaline(surface, color_main,
                            (shoulder_x, shoulder_y),
                            (elbow_x, elbow_y), thickness)
        _NS_korokai._aaline(surface, color_mid,
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), max(1, thickness - 3))
        # Forearm
        _NS_korokai._aaline(surface, _NS_korokai.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 2),
                            (hand_x + 1, hand_y + 2), thickness)
        _NS_korokai._aaline(surface, color_main,
                            (elbow_x, elbow_y),
                            (hand_x, hand_y), thickness - 1)
        _NS_korokai._aaline(surface, color_mid,
                            (elbow_x, elbow_y - 1),
                            (hand_x, hand_y - 1), max(1, thickness - 3))
        # Bandage wrap on forearm
        fore_dx = hand_x - elbow_x
        fore_dy = hand_y - elbow_y
        fore_len = max(1, math.sqrt(fore_dx * fore_dx + fore_dy * fore_dy))
        perp_x = -fore_dy / fore_len
        perp_y = fore_dx / fore_len
        for i in range(3):
            t = (i + 1) / 4
            tx = elbow_x + fore_dx * t
            ty = elbow_y + fore_dy * t
            band_w = 3
            pygame.draw.line(surface, _NS_korokai.PALETTE["hair_light"],
                             (int(tx + perp_x * band_w),
                              int(ty + perp_y * band_w)),
                             (int(tx - perp_x * band_w),
                              int(ty - perp_y * band_w)), 1)
        # Dark glove/hand
        _NS_korokai._aacircle(surface, _NS_korokai.PALETTE["shadow_deep"],
                              (hand_x + 1, hand_y + 1), 3)
        _NS_korokai._aacircle(surface, _NS_korokai.PALETTE["glove_dark"],
                              (hand_x, hand_y), 3)
        _NS_korokai._aacircle(surface, _NS_korokai.PALETTE["glove_mid"],
                              (hand_x, hand_y), 2)
    def _draw_arm_with_kunai(surface, cx, cy, facing, phase, swing, action,
                             attack_progress):
        """Front arm holding kunai with slash animation."""
        base_angle = math.pi * 0.5 + math.radians(swing)
        shoulder_x = cx
        shoulder_y = cy
        elbow_len = 11
        elbow_x = shoulder_x + int(math.cos(base_angle) * elbow_len * facing * 0.4)
        elbow_y = shoulder_y + int(math.sin(base_angle) * elbow_len)
        hand_len = 14
        hand_angle = base_angle - math.radians(swing * 0.6)
        hand_x = elbow_x + int(math.cos(hand_angle) * hand_len * facing * 0.6)
        hand_y = elbow_y + int(math.sin(hand_angle) * hand_len)
        # Extended for slash
        if action == "attack" and attack_progress > 0.35:
            hand_x = cx + facing * (12 + int(attack_progress * 12))
            hand_y = cy + 2 - int(math.sin(attack_progress * math.pi) * 6)
        thickness = 6
        # Sleeve
        _NS_korokai._aaline(surface, _NS_korokai.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 2),
                            (elbow_x + 1, elbow_y + 2), thickness + 1)
        _NS_korokai._aaline(surface, _NS_korokai.PALETTE["uniform_dark"],
                            (shoulder_x, shoulder_y),
                            (elbow_x, elbow_y), thickness)
        _NS_korokai._aaline(surface, _NS_korokai.PALETTE["uniform_mid"],
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), max(1, thickness - 3))
        # Forearm
        _NS_korokai._aaline(surface, _NS_korokai.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 2),
                            (hand_x + 1, hand_y + 2), thickness)
        _NS_korokai._aaline(surface, _NS_korokai.PALETTE["uniform_dark"],
                            (elbow_x, elbow_y),
                            (hand_x, hand_y), thickness - 1)
        _NS_korokai._aaline(surface, _NS_korokai.PALETTE["uniform_mid"],
                            (elbow_x, elbow_y - 1),
                            (hand_x, hand_y - 1), max(1, thickness - 3))
        # Bandage wraps
        fore_dx = hand_x - elbow_x
        fore_dy = hand_y - elbow_y
        fore_len = max(1, math.sqrt(fore_dx * fore_dx + fore_dy * fore_dy))
        perp_x = -fore_dy / fore_len
        perp_y = fore_dx / fore_len
        for i in range(3):
            t = (i + 1) / 4
            tx = elbow_x + fore_dx * t
            ty = elbow_y + fore_dy * t
            band_w = 3
            pygame.draw.line(surface, _NS_korokai.PALETTE["hair_light"],
                             (int(tx + perp_x * band_w),
                              int(ty + perp_y * band_w)),
                             (int(tx - perp_x * band_w),
                              int(ty - perp_y * band_w)), 1)
        # Hand
        _NS_korokai._aacircle(surface, _NS_korokai.PALETTE["shadow_deep"],
                              (hand_x + 1, hand_y + 1), 3)
        _NS_korokai._aacircle(surface, _NS_korokai.PALETTE["glove_dark"],
                              (hand_x, hand_y), 3)
        _NS_korokai._aacircle(surface, _NS_korokai.PALETTE["glove_mid"],
                              (hand_x, hand_y), 2)
        # KUNAI
        _NS_korokai._draw_kunai(surface, hand_x, hand_y, facing, phase, action,
                                attack_progress, hand_angle)
    def _draw_kunai(surface, hand_x, hand_y, facing, phase, action, progress,
                    hand_angle):
        """Draw kunai (throwing knife) held in hand."""
        # Kunai angle
        if action == "attack":
            if progress < 0.35:
                # Wind up - kunai pointed back-up
                kunai_angle = -math.pi * 0.7
            elif progress < 0.6:
                # Slash forward
                t = (progress - 0.35) / 0.25
                start_a = -math.pi * 0.7
                end_a = math.pi * 0.15
                kunai_angle = start_a + (end_a - start_a) * t
            else:
                # Recovery
                t = (progress - 0.6) / 0.4
                kunai_angle = math.pi * 0.15 - t * 0.1
        else:
            # Idle - held forward slightly
            kunai_angle = -math.pi * 0.1
            kunai_angle += math.sin(phase * 0.5) * 0.03
        cos_a = math.cos(kunai_angle) * facing
        sin_a = math.sin(kunai_angle)
        # Handle (wrapped grip)
        handle_len = 5
        handle_end_x = hand_x + int(cos_a * handle_len)
        handle_end_y = hand_y + int(sin_a * handle_len)
        _NS_korokai._aaline(surface, _NS_korokai.PALETTE["hair_dark"],
                            (hand_x, hand_y), (handle_end_x, handle_end_y), 3)
        _NS_korokai._aaline(surface, _NS_korokai.PALETTE["hair_light"],
                            (hand_x, hand_y), (handle_end_x, handle_end_y), 2)
        # Handle wraps
        for i in range(2):
            wrap_t = (i + 1) / 3
            wx = hand_x + int((handle_end_x - hand_x) * wrap_t)
            wy = hand_y + int((handle_end_y - hand_y) * wrap_t)
            perp_x = -sin_a
            perp_y = cos_a
            pygame.draw.line(surface, _NS_korokai.PALETTE["mask_dark"],
                             (wx - int(perp_x * 2), wy - int(perp_y * 2)),
                             (wx + int(perp_x * 2), wy + int(perp_y * 2)), 1)
        # Ring/loop at end of handle
        ring_x = hand_x - int(cos_a * 2)
        ring_y = hand_y - int(sin_a * 2)
        _NS_korokai._aacircle(surface, _NS_korokai.PALETTE["steel_dark"],
                              (ring_x, ring_y), 2, 1)
        pygame.draw.rect(surface, _NS_korokai.PALETTE["steel_mid"],
                         (ring_x, ring_y - 1, 1, 1))
        # Blade (diamond/leaf shaped)
        blade_len = 12
        blade_tip_x = handle_end_x + int(cos_a * blade_len)
        blade_tip_y = handle_end_y + int(sin_a * blade_len)
        # Perpendicular for blade width
        perp_x = -sin_a
        perp_y = cos_a
        blade_mid_x = handle_end_x + int(cos_a * blade_len * 0.4)
        blade_mid_y = handle_end_y + int(sin_a * blade_len * 0.4)
        # Wide part of blade
        wide_a_x = blade_mid_x + int(perp_x * 4)
        wide_a_y = blade_mid_y + int(perp_y * 4)
        wide_b_x = blade_mid_x - int(perp_x * 2)
        wide_b_y = blade_mid_y - int(perp_y * 2)
        # Blade shadow
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["shadow_deep"], [
            (handle_end_x + 1, handle_end_y + 1),
            (wide_a_x + 1, wide_a_y + 1),
            (blade_tip_x + 1, blade_tip_y + 1),
            (wide_b_x + 1, wide_b_y + 1),
        ])
        # Blade layers
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["steel_dark"], [
            (handle_end_x, handle_end_y),
            (wide_a_x, wide_a_y),
            (blade_tip_x, blade_tip_y),
            (wide_b_x, wide_b_y),
        ])
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["steel_mid"], [
            (handle_end_x, handle_end_y),
            (int(wide_a_x * 0.7 + blade_tip_x * 0.3),
             int(wide_a_y * 0.7 + blade_tip_y * 0.3)),
            (blade_tip_x, blade_tip_y),
            (int(wide_b_x * 0.7 + blade_tip_x * 0.3),
             int(wide_b_y * 0.7 + blade_tip_y * 0.3)),
        ])
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["steel_light"], [
            (handle_end_x, handle_end_y),
            (int(wide_a_x * 0.5 + blade_tip_x * 0.5),
             int(wide_a_y * 0.5 + blade_tip_y * 0.5)),
            (blade_tip_x, blade_tip_y),
        ])
        # Sharp tip highlight
        pygame.draw.rect(surface, _NS_korokai.PALETTE["steel_shine"],
                         (blade_tip_x, blade_tip_y, 1, 1))
        # Center ridge line
        pygame.draw.line(surface, _NS_korokai.PALETTE["steel_shine"],
                         (handle_end_x, handle_end_y),
                         (blade_tip_x, blade_tip_y), 1)
    def _draw_head(surface, cx, cy, facing, phase, action):
        """Head with silver hair, headband, mask covering lower face."""
        # Face shape
        face_shape = [
            (cx - 7, cy - 2),
            (cx - 8, cy - 6),
            (cx - 6, cy - 10),
            (cx - 2, cy - 12),
            (cx + 2, cy - 12),
            (cx + 6, cy - 10),
            (cx + 8, cy - 6),
            (cx + 7, cy - 2),
            (cx + 5, cy + 3),
            (cx + 1, cy + 5),
            (cx - 3, cy + 5),
            (cx - 6, cy + 3),
        ]
        # Shadow
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["shadow_deep"],
                          [(px + 1, py + 2) for px, py in face_shape])
        # Base skin
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["skin_shadow"], face_shape)
        # Main face (only upper half visible, lower is masked)
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["skin_dark"], [
            (cx - 6, cy - 3),
            (cx - 7, cy - 6),
            (cx - 5, cy - 9),
            (cx - 2, cy - 11),
            (cx + 2, cy - 11),
            (cx + 5, cy - 9),
            (cx + 7, cy - 6),
            (cx + 6, cy - 3),
            (cx + 4, cy - 1),
            (cx - 4, cy - 1),
        ])
        # Skin mid tone
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["skin_mid"], [
            (cx - 4, cy - 4),
            (cx - 5, cy - 7),
            (cx - 3, cy - 9),
            (cx + 3, cy - 9),
            (cx + 5, cy - 7),
            (cx + 4, cy - 4),
            (cx + 2, cy - 2),
            (cx - 2, cy - 2),
        ])
        # Cheek highlight
        pygame.draw.rect(surface, _NS_korokai.PALETTE["skin_light"],
                         (cx - 3 * facing, cy - 4, 2, 2))
        pygame.draw.rect(surface, _NS_korokai.PALETTE["skin_shine"],
                         (cx - 3 * facing, cy - 4, 1, 1))
        # MASK (covers from nose down)
        _NS_korokai._draw_mask(surface, cx, cy, facing, phase, action)
        # HEADBAND with metal plate (covers left eye when W not active)
        _NS_korokai._draw_headband(surface, cx, cy - 8, facing, phase)
        # RIGHT EYE (natural, visible)
        _NS_korokai._draw_normal_eye(surface, cx + 3, cy - 5, facing, phase, action)
        # LEFT EYE (covered by headband slant - visible only when W active,
        # will be overlaid in main draw)
        # Placeholder - dark socket under headband
        pygame.draw.rect(surface, _NS_korokai.PALETTE["shadow_deep"],
                         (cx - 4, cy - 6, 3, 2))
        # SILVER HAIR (spiky, upward + right side)
        _NS_korokai._draw_hair(surface, cx, cy, facing, phase)
    def _draw_mask(surface, cx, cy, facing, phase, action):
        """Dark mask covering lower half of face."""
        # Mask shape (covers from below eyes down to neck)
        mask_shape = [
            (cx - 8, cy - 2),
            (cx - 8, cy + 3),
            (cx - 6, cy + 6),
            (cx - 3, cy + 7),
            (cx + 3, cy + 7),
            (cx + 6, cy + 6),
            (cx + 8, cy + 3),
            (cx + 8, cy - 2),
            (cx + 6, cy - 1),
            (cx - 6, cy - 1),
        ]
        # Shadow
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["shadow_deep"],
                          [(px + 1, py + 1) for px, py in mask_shape])
        # Base
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["mask_dark"], mask_shape)
        # Mid tone
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["mask_mid"], [
            (cx - 7, cy - 1),
            (cx - 7, cy + 3),
            (cx - 5, cy + 5),
            (cx + 5, cy + 5),
            (cx + 7, cy + 3),
            (cx + 7, cy - 1),
        ])
        # Highlight (subtle)
        pygame.draw.line(surface, _NS_korokai.PALETTE["mask_light"],
                         (cx - 3, cy), (cx + 3, cy), 1)
        # Nose bump/shape
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["mask_light"], [
            (cx - 1, cy),
            (cx, cy - 1),
            (cx + 1, cy),
            (cx, cy + 1),
        ])
        # Mouth line hint (very subtle)
        if action == "attack":
            pygame.draw.line(surface, _NS_korokai.PALETTE["shadow_deep"],
                             (cx - 2, cy + 3), (cx + 2, cy + 3), 1)
    def _draw_headband(surface, cx, cy, facing, phase):
        """Headband with metal plate, slanted to cover left eye."""
        # Cloth band (dark, going across forehead)
        # It slants down over the left eye
        # Main headband band
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["shadow_deep"], [
            (cx - 9, cy - 1),
            (cx - 10, cy + 3),
            (cx + 10, cy + 3),
            (cx + 9, cy - 1),
        ])
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["uniform_darkest"], [
            (cx - 8, cy),
            (cx - 9, cy + 3),
            (cx + 9, cy + 3),
            (cx + 8, cy),
        ])
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["uniform_dark"], [
            (cx - 7, cy + 1),
            (cx - 8, cy + 2),
            (cx + 8, cy + 2),
            (cx + 7, cy + 1),
        ])
        # METAL PLATE with symbol (across forehead)
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["metal_dark"], [
            (cx - 7, cy),
            (cx - 8, cy + 3),
            (cx + 8, cy + 3),
            (cx + 7, cy),
        ])
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["metal_mid"], [
            (cx - 6, cy + 1),
            (cx - 7, cy + 3),
            (cx + 7, cy + 3),
            (cx + 6, cy + 1),
        ])
        # Metal shine
        pygame.draw.line(surface, _NS_korokai.PALETTE["metal_light"],
                         (cx - 5, cy + 1), (cx + 5, cy + 1), 1)
        pygame.draw.line(surface, _NS_korokai.PALETTE["metal_shine"],
                         (cx - 3, cy + 1), (cx + 3, cy + 1), 1)
        # Symbol (abstract shinobi mark - X-shape or spiral)
        # We'll do a simple X mark
        pygame.draw.line(surface, _NS_korokai.PALETTE["shadow_deep"],
                         (cx - 2, cy + 1), (cx + 2, cy + 3), 1)
        pygame.draw.line(surface, _NS_korokai.PALETTE["shadow_deep"],
                         (cx + 2, cy + 1), (cx - 2, cy + 3), 1)
        pygame.draw.rect(surface, _NS_korokai.PALETTE["metal_dark"],
                         (cx, cy + 2, 1, 1))
        # SLANTED CORNER DOWN OVER LEFT EYE
        # This is the extension of headband cloth going down diagonally
        slant_x_start = cx - 8
        slant_y_start = cy + 2
        slant_x_end = cx - 2 * facing
        slant_y_end = cy + 6
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["shadow_deep"], [
            (slant_x_start - 1, slant_y_start),
            (slant_x_end - 2, slant_y_end + 1),
            (slant_x_end + 1, slant_y_end + 1),
            (slant_x_start + 2, slant_y_start),
        ])
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["uniform_darkest"], [
            (slant_x_start, slant_y_start),
            (slant_x_end - 1, slant_y_end),
            (slant_x_end + 1, slant_y_end),
            (slant_x_start + 2, slant_y_start),
        ])
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["uniform_dark"], [
            (slant_x_start + 1, slant_y_start),
            (slant_x_end, slant_y_end),
            (slant_x_end + 1, slant_y_end),
            (slant_x_start + 2, slant_y_start),
        ])
        # Cloth tails hanging back
        tail_x = cx - 9 * facing
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["uniform_darkest"], [
            (tail_x, cy + 2),
            (tail_x - 2 * facing, cy + 6),
            (tail_x - 3 * facing, cy + 10),
            (tail_x - 1 * facing, cy + 10),
            (tail_x + 1 * facing, cy + 6),
        ])
        pygame.draw.line(surface, _NS_korokai.PALETTE["uniform_mid"],
                         (tail_x - 1 * facing, cy + 4),
                         (tail_x - 2 * facing, cy + 8), 1)
    def _draw_normal_eye(surface, cx, cy, facing, phase, action):
        """Regular dark eye (right eye)."""
        pygame.draw.rect(surface, _NS_korokai.PALETTE["shadow_deep"],
                         (cx - 1, cy - 1, 3, 2))
        pygame.draw.rect(surface, _NS_korokai.PALETTE["white"],
                         (cx - 1, cy, 3, 1))
        # Iris (dark)
        pygame.draw.rect(surface, _NS_korokai.PALETTE["eye_dark"],
                         (cx, cy, 2, 1))
        pygame.draw.rect(surface, _NS_korokai.PALETTE["eye_mid"],
                         (cx + facing, cy, 1, 1))
        # Highlight
        pygame.draw.rect(surface, _NS_korokai.PALETTE["hair_shine"],
                         (cx, cy - 1, 1, 1))
    def _draw_crimson_eye_overlay(surface, cx_body, cy_head, facing, phase, is_r):
        """Draw crimson mystical eye over the left eye when W (or R) active.
        This overrides the headband slant covering."""
        # Position of left eye
        eye_x = cx_body - 3
        eye_y = cy_head - 5
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Move headband slant up briefly (draw skin/eye over it)
        # Redraw skin patch
        pygame.draw.rect(surface, _NS_korokai.PALETTE["skin_mid"],
                         (eye_x - 2, eye_y - 1, 5, 3))
        pygame.draw.rect(surface, _NS_korokai.PALETTE["skin_dark"],
                         (eye_x - 2, eye_y - 1, 5, 1))
        # CRIMSON EYE
        # Outer sclera
        pygame.draw.rect(surface, _NS_korokai.PALETTE["shadow_deep"],
                         (eye_x - 1, eye_y - 1, 3, 2))
        # Glow halo around eye
        for r in range(5, 0, -1):
            alpha = _NS_korokai._alpha(120 * (5 - r) / 5 * pulse)
            _NS_korokai._aacircle(surface,
                                  (*_NS_korokai.PALETTE["crimson_mid"], alpha),
                                  (eye_x, eye_y), r)
        # Red iris
        pygame.draw.rect(surface, _NS_korokai.PALETTE["crimson_darkest"],
                         (eye_x - 1, eye_y - 1, 3, 2))
        pygame.draw.rect(surface, _NS_korokai.PALETTE["crimson_dark"],
                         (eye_x - 1, eye_y, 3, 1))
        pygame.draw.rect(surface, _NS_korokai.PALETTE["crimson_mid"],
                         (eye_x, eye_y, 2, 1))
        pygame.draw.rect(surface, _NS_korokai.PALETTE["crimson_light"],
                         (eye_x + facing, eye_y, 1, 1))
        # TOMOE PATTERN (3 rotating comma-shapes around pupil)
        # For R skill (advanced mode) - draw larger tomoe with more detail
        num_tomoe = 4 if is_r else 3
        for i in range(num_tomoe):
            tomoe_angle = phase * 2 + i * math.pi * 2 / num_tomoe
            tomoe_r = 2 if is_r else 1
            tx = eye_x + int(math.cos(tomoe_angle) * tomoe_r)
            ty = eye_y + int(math.sin(tomoe_angle) * tomoe_r)
            pygame.draw.rect(surface, _NS_korokai.PALETTE["shadow_deep"],
                             (tx, ty, 1, 1))
        # Central pupil
        pygame.draw.rect(surface, _NS_korokai.PALETTE["shadow_deep"],
                         (eye_x, eye_y, 1, 1))
        # Bright shine highlight
        pygame.draw.rect(surface, _NS_korokai.PALETTE["crimson_shine"],
                         (eye_x, eye_y - 1, 1, 1))
    def _draw_hair(surface, cx, cy, facing, phase):
        """Silver spiky hair leaning to one side (right)."""
        cy_h = cy - 22  # hair position
        # Back hair mass
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["shadow_deep"], [
            (cx - 9, cy_h - 8),
            (cx - 7, cy_h - 14),
            (cx - 2, cy_h - 16),
            (cx + 5, cy_h - 15),
            (cx + 10, cy_h - 12),
            (cx + 11, cy_h - 6),
            (cx + 10, cy_h - 4),
            (cx - 8, cy_h - 4),
        ])
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["hair_darkest"], [
            (cx - 8, cy_h - 8),
            (cx - 6, cy_h - 13),
            (cx - 1, cy_h - 15),
            (cx + 5, cy_h - 14),
            (cx + 9, cy_h - 11),
            (cx + 10, cy_h - 6),
        ])
        # Main dark grey/silver
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["hair_dark"], [
            (cx - 7, cy_h - 9),
            (cx - 5, cy_h - 12),
            (cx, cy_h - 13),
            (cx + 5, cy_h - 12),
            (cx + 8, cy_h - 10),
            (cx + 9, cy_h - 7),
        ])
        # Silver mid highlight
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["hair_mid"], [
            (cx - 5, cy_h - 10),
            (cx - 2, cy_h - 12),
            (cx + 3, cy_h - 11),
            (cx + 7, cy_h - 9),
            (cx + 6, cy_h - 7),
            (cx - 3, cy_h - 7),
        ])
        # Light silver
        pygame.draw.line(surface, _NS_korokai.PALETTE["hair_light"],
                         (cx - 2, cy_h - 11), (cx + 4, cy_h - 10), 1)
        pygame.draw.rect(surface, _NS_korokai.PALETTE["hair_shine"],
                         (cx, cy_h - 12, 2, 1))
        # SPIKY MESSY BANGS on forehead (irregular)
        for spike_x_off, spike_h in [(-5, -2), (-2, -3), (1, -3), (4, -2), (6, -1)]:
            sx = cx + spike_x_off
            sy = cy_h - 5
            _NS_korokai._poly(surface, _NS_korokai.PALETTE["hair_darkest"], [
                (sx - 2, sy),
                (sx, sy + spike_h),
                (sx + 2, sy),
            ])
            _NS_korokai._poly(surface, _NS_korokai.PALETTE["hair_dark"], [
                (sx - 1, sy),
                (sx, sy + spike_h + 1),
                (sx + 1, sy),
            ])
            _NS_korokai._poly(surface, _NS_korokai.PALETTE["hair_mid"], [
                (sx, sy),
                (sx, sy + spike_h + 1),
                (sx + 1, sy),
            ])
        # BIG SPIKES SWEPT LEANING RIGHT (side)
        top_sway = math.sin(phase * 0.6) * 1
        for spike_i, (spike_x_off, spike_h, side_off) in enumerate([
            (-5, -4, -2), (-2, -8, 0), (0, -10, 2), (3, -11, 4),
            (6, -9, 6), (8, -6, 7),
        ]):
            sx = cx + spike_x_off + int(top_sway * (spike_i - 2.5) / 3)
            sy = cy_h - 13
            end_x = sx + side_off
            end_y = sy + spike_h
            _NS_korokai._poly(surface, _NS_korokai.PALETTE["hair_darkest"], [
                (sx - 2, sy),
                (end_x, end_y),
                (sx + 2, sy),
            ])
            _NS_korokai._poly(surface, _NS_korokai.PALETTE["hair_dark"], [
                (sx - 1, sy),
                (end_x, end_y + 1),
                (sx + 1, sy),
            ])
            _NS_korokai._poly(surface, _NS_korokai.PALETTE["hair_mid"], [
                (sx, sy),
                (end_x, end_y + 1),
                (sx + 1, sy),
            ])
            pygame.draw.rect(surface, _NS_korokai.PALETTE["hair_light"],
                             (end_x, end_y + 1, 1, 1))
            if spike_i in (2, 3):
                pygame.draw.rect(surface, _NS_korokai.PALETTE["hair_shine"],
                                 (end_x, end_y + 1, 1, 1))
    # ============================================================
    # BASIC MELEE - Kunai slash
    # ============================================================
    def _draw_kunai_slash(surface, boss, x, y, progress):
        """Kunai slash arc trail."""
        if progress < 0.35 or progress > 0.75:
            return
        facing = boss.direction
        swing_t = (progress - 0.35) / 0.4
        # Slash arc from behind-up to forward-down
        start_angle = -math.pi * 0.7
        end_angle = math.pi * 0.15
        current_angle = start_angle + (end_angle - start_angle) * swing_t
        origin_x = x + facing * 10
        origin_y = y - 4
        arc_radius = 26
        # Slash trail (motion blur)
        for trace in range(6):
            trace_t = swing_t - trace * 0.06
            if trace_t < 0:
                continue
            t_angle = start_angle + (end_angle - start_angle) * trace_t
            ex = origin_x + int(math.cos(t_angle) * arc_radius) * facing
            ey = origin_y + int(math.sin(t_angle) * arc_radius)
            alpha = _NS_korokai._alpha(220 - trace * 35)
            # Slash arc lines
            _NS_korokai._aaline(surface,
                                (*_NS_korokai.PALETTE["steel_dark"], alpha),
                                (origin_x, origin_y), (ex, ey), 4)
            _NS_korokai._aaline(surface,
                                (*_NS_korokai.PALETTE["steel_mid"], alpha),
                                (origin_x, origin_y), (ex, ey), 2)
            _NS_korokai._aaline(surface,
                                (*_NS_korokai.PALETTE["steel_light"], alpha),
                                (origin_x, origin_y), (ex, ey), 1)
            _NS_korokai._aaline(surface,
                                (*_NS_korokai.PALETTE["steel_shine"], alpha),
                                (origin_x, origin_y - 1), (ex, ey - 1), 1)
            # Endpoint bright
            _NS_korokai._aacircle(surface,
                                  (*_NS_korokai.PALETTE["steel_shine"], alpha),
                                  (ex, ey), 2)
            pygame.draw.rect(surface, _NS_korokai.PALETTE["white"], (ex, ey, 1, 1))
    # ============================================================
    # FLOATING MIST
    # ============================================================
    def _draw_shinobi_mist(surface, cx, cy, phase, trail=False, facing=1,
                           intense=False):
        """Dark shinobi chakra mist below body."""
        strength = 1.4 if intense else 1.0
        mist = pygame.Surface((130, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(28, 3, -3):
            alpha = _NS_korokai._alpha((28 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_korokai.PALETTE["uniform_darkest"], alpha),
                    (65 - radius, 20 - radius // 3,
                     radius * 2, max(2, radius // 2))
                )
        for radius in range(18, 2, -2):
            alpha = _NS_korokai._alpha((18 - radius) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_korokai.PALETTE["uniform_dark"], alpha),
                    (65 - radius, 20 - radius // 4,
                     radius * 2, max(2, radius // 3))
                )
        surface.blit(mist, (cx - 65, cy - 10))
        # Blue electric sparks (chakra)
        for i in range(6):
            t = (phase * 0.5 + i * 0.15) % 1.0
            px = cx - 18 + i * 7 + int(math.sin(phase + i) * 3)
            py = cy + 4 - int(t * 22)
            alpha = _NS_korokai._alpha(200 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface,
                                 (*_NS_korokai.PALETTE["elec_mid"], alpha),
                                 (px, py, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_korokai.PALETTE["elec_bright"], alpha),
                                 (px, py, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_korokai.PALETTE["elec_hot"], alpha),
                                 (px, py - 1, 1, 1))
        # Trail
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_korokai._alpha(140 - i * 25)
                if alpha > 0:
                    _NS_korokai._aacircle(surface,
                                          (*_NS_korokai.PALETTE["uniform_dark"], alpha),
                                          (sx, sy), max(1, 4 - i))
                    pygame.draw.rect(surface, _NS_korokai.PALETTE["elec_bright"],
                                     (sx, sy - 1, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((130, 24), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 12 - radius, 110 + radius * 2, radius * 2)
            )
        pygame.draw.ellipse(shadow, (3, 3, 8, 170), (5, 6, 120, 12))
        pygame.draw.ellipse(shadow, (20, 30, 60, 100), (15, 8, 100, 8))
        surface.blit(shadow, (x - 65, y - 12))
    def _draw_shinobi_aura(surface, x, y, phase):
        """Dark blue aura with electric hints."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((200, 170), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_korokai._alpha((85 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_korokai._aacircle(aura,
                                      (*_NS_korokai.PALETTE["uniform_darkest"], alpha),
                                      (100, 85), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_korokai._alpha((55 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_korokai._aacircle(aura,
                                      (*_NS_korokai.PALETTE["uniform_dark"], alpha),
                                      (100, 85), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_korokai._alpha((30 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_korokai._aacircle(aura,
                                      (*_NS_korokai.PALETTE["elec_darkest"], alpha),
                                      (100, 85), radius)
        surface.blit(aura, (x - 100, y - 85))
        # Floating electric particles
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            radius = 38 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_korokai.PALETTE["elec_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_korokai.PALETTE["elec_bright"], (sx, sy, 1, 1))
        # Occasional lightning arcs
        for i in range(2):
            if math.sin(phase * 3 + i * 2.7) > 0.7:
                ax = x + int(math.cos(phase + i) * 40)
                ay = y - 10 + int(math.sin(phase * 2 + i) * 15)
                bx = ax + int(math.cos(phase * 1.5 + i) * 20)
                by = ay + int(math.sin(phase * 1.5 + i) * 20)
                _NS_korokai._draw_lightning_bolt(
                    surface, (ax, ay), (bx, by),
                    _NS_korokai.PALETTE["elec_bright"],
                    width=1, jitter=3, alpha=180
                )
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        # Color depends on active skill
        base_color = _NS_korokai.PALETTE["elec_dark"]
        accent_color = _NS_korokai.PALETTE["elec_bright"]
        if skill == "w" or skill == "r":
            base_color = _NS_korokai.PALETTE["crimson_dark"]
            accent_color = _NS_korokai.PALETTE["crimson_light"]
        pygame.draw.ellipse(ring, (*_NS_korokai.PALETTE["uniform_darkest"], 210),
                            (5, 15, 150, 24), 3)
        pygame.draw.ellipse(ring, (*base_color, 220),
                            (14, 17, 132, 20), 2)
        pygame.draw.ellipse(ring, (*accent_color, 180),
                            (25, 19, 110, 16), 1)
        # Runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 27 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 27 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*accent_color, 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*accent_color,
                                        _NS_korokai._alpha(160 * pulse)),
                                (12, 10, 136, 32), 1)
        surface.blit(ring, (x - 80, y - 25))
    # ============================================================
    # SKILL Q - THUNDER KUNAI (electric kunai projectile)
    # ============================================================
    def _draw_thunder_kunai_skill(surface, boss, x, y, timer, phase):
        """Kunai charged with lightning thrown at target."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_korokai._target_position(boss, x, y)
        if progress < 0.25:
            # Charge - kunai in hand crackles with lightning
            t = progress / 0.25
            hand_x = x + facing * 22
            hand_y = y - 4
            # Lightning aura around hand
            for r in range(int(10 * t), 0, -1):
                alpha = _NS_korokai._alpha(180 * t * (10 - r) / 10)
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["elec_dark"], alpha),
                                      (hand_x, hand_y), r)
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["elec_mid"], alpha),
                                      (hand_x, hand_y), max(1, r - 2))
            # Sparks around hand
            for i in range(5):
                s_angle = phase * 4 + i * math.pi * 2 / 5
                sx = hand_x + int(math.cos(s_angle) * (8 + t * 4))
                sy = hand_y + int(math.sin(s_angle) * (8 + t * 4))
                pygame.draw.rect(surface, _NS_korokai.PALETTE["elec_bright"],
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_korokai.PALETTE["elec_shine"],
                                 (sx, sy, 1, 1))
                # Lightning branches
                if t > 0.5:
                    _NS_korokai._draw_lightning_bolt(
                        surface, (hand_x, hand_y), (sx, sy),
                        _NS_korokai.PALETTE["elec_bright"],
                        width=1, jitter=2, alpha=int(200 * t)
                    )
        else:
            # KUNAI FLIES to target with lightning trail
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 24
            start_y = y - 4
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Angle for kunai orientation
            travel_angle = math.atan2(ty - start_y, tx - start_x)
            # Lightning trail behind kunai
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_korokai._alpha(240 - i * 22)
                # Electric glow
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["elec_darkest"], alpha),
                                      (px, py), max(1, 6 - i))
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["elec_dark"], alpha),
                                      (px, py), max(1, 5 - i))
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["elec_mid"], alpha),
                                      (px, py), max(1, 3 - i))
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["elec_bright"], alpha),
                                      (px, py), max(1, 2 - i // 2))
                if i < 4:
                    pygame.draw.rect(surface,
                                     (*_NS_korokai.PALETTE["elec_shine"], alpha),
                                     (px, py, 1, 1))
            # Lightning bolts along trajectory
            for i in range(3):
                if math.sin(phase * 5 + i) > 0:
                    branch_angle = travel_angle + math.pi / 2 + i * 0.5
                    end_x = bx + int(math.cos(branch_angle) * 10)
                    end_y = by + int(math.sin(branch_angle) * 10)
                    _NS_korokai._draw_lightning_bolt(
                        surface, (bx, by), (end_x, end_y),
                        _NS_korokai.PALETTE["elec_bright"],
                        width=1, jitter=3, alpha=200
                    )
            # Draw the kunai itself (rotated to travel direction)
            _NS_korokai._draw_flying_kunai(surface, bx, by, travel_angle)
            # Impact
            if t > 0.9:
                st = (t - 0.9) / 0.1
                radius = int(12 + st * 20)
                alpha = _NS_korokai._alpha(240 * (1 - st))
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["elec_darkest"], alpha),
                                      (tx, ty), radius + 3, 3)
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["elec_dark"], alpha),
                                      (tx, ty), radius, 2)
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["elec_mid"], alpha),
                                      (tx, ty), max(1, radius - 4), 2)
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["elec_bright"], alpha),
                                      (tx, ty), max(1, radius - 8), 1)
                # Radial lightning
                for i in range(8):
                    angle_s = i * math.pi / 4
                    ex = tx + int(math.cos(angle_s) * radius * 1.2)
                    ey = ty + int(math.sin(angle_s) * radius * 1.2)
                    _NS_korokai._draw_lightning_bolt(
                        surface, (tx, ty), (ex, ey),
                        _NS_korokai.PALETTE["elec_bright"],
                        width=2, segments=4, jitter=4, alpha=int(220 * (1 - st))
                    )
    def _draw_flying_kunai(surface, cx, cy, angle):
        """Kunai sprite oriented along travel angle."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        # Tip
        tip_x = cx + int(cos_a * 8)
        tip_y = cy + int(sin_a * 8)
        # Back
        back_x = cx - int(cos_a * 5)
        back_y = cy - int(sin_a * 5)
        # Wide points
        perp_x = -sin_a
        perp_y = cos_a
        mid_x = cx + int(cos_a * 2)
        mid_y = cy + int(sin_a * 2)
        wide_a_x = mid_x + int(perp_x * 3)
        wide_a_y = mid_y + int(perp_y * 3)
        wide_b_x = mid_x - int(perp_x * 3)
        wide_b_y = mid_y - int(perp_y * 3)
        # Blade shadow
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["shadow_deep"], [
            (tip_x + 1, tip_y + 1), (wide_a_x + 1, wide_a_y + 1),
            (back_x + 1, back_y + 1), (wide_b_x + 1, wide_b_y + 1),
        ])
        # Base blade
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["steel_dark"], [
            (tip_x, tip_y), (wide_a_x, wide_a_y),
            (back_x, back_y), (wide_b_x, wide_b_y),
        ])
        # Mid layer
        _NS_korokai._poly(surface, _NS_korokai.PALETTE["steel_mid"], [
            (tip_x, tip_y),
            (int(wide_a_x * 0.7 + tip_x * 0.3),
             int(wide_a_y * 0.7 + tip_y * 0.3)),
            (int(mid_x * 0.7 + back_x * 0.3),
             int(mid_y * 0.7 + back_y * 0.3)),
            (int(wide_b_x * 0.7 + tip_x * 0.3),
             int(wide_b_y * 0.7 + tip_y * 0.3)),
        ])
        # Light highlight (fixed - now 3 points minimum for triangle)
        light_p1 = (tip_x, tip_y)
        light_p2 = (int(mid_x * 0.5 + tip_x * 0.5),
                    int(mid_y * 0.5 + tip_y * 0.5))
        light_p3 = (int(wide_a_x * 0.5 + tip_x * 0.5),
                    int(wide_a_y * 0.5 + tip_y * 0.5))
        # Only draw if points are distinct (avoid degenerate polygon)
        if light_p1 != light_p2 and light_p2 != light_p3 and light_p1 != light_p3:
            _NS_korokai._poly(surface, _NS_korokai.PALETTE["steel_light"], [
                light_p1, light_p2, light_p3,
            ])
        # Center ridge line (bright)
        pygame.draw.line(surface, _NS_korokai.PALETTE["steel_shine"],
                         (back_x, back_y), (tip_x, tip_y), 1)
        # Sharp tip highlight
        pygame.draw.rect(surface, _NS_korokai.PALETTE["steel_shine"],
                         (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_korokai.PALETTE["white"],
                         (tip_x, tip_y, 1, 1))
    # ============================================================
    # SKILL W - MIRROR EYE (crimson eye buff aura)
    # ============================================================
    def _draw_mirror_eye_aura(surface, boss, x, y, timer, phase):
        """Purple aura around body when Mirror Eye active."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Bubble aura
        breath = math.sin(phase * 2.5) * 2
        r = 42 + int(breath)
        aura_surf = pygame.Surface((r * 2 + 30, r * 2 + 30), pygame.SRCALPHA)
        center = (r + 15, r + 15)
        # Ring layers (purple/void)
        for i, (thickness, alpha_val) in enumerate([
            (3, 100), (2, 140), (1, 180),
        ]):
            _NS_korokai._aacircle(aura_surf,
                                  (*_NS_korokai.PALETTE["void_dark"], alpha_val),
                                  center, r - i, thickness)
            _NS_korokai._aacircle(aura_surf,
                                  (*_NS_korokai.PALETTE["void_mid"], alpha_val),
                                  center, r - i - 1, 1)
        # Rotating sparks (crimson accent)
        for i in range(16):
            angle = phase * 2 + i * math.pi / 8
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            color = _NS_korokai.PALETTE["crimson_light"] if i % 2 == 0 \
                else _NS_korokai.PALETTE["void_light"]
            pygame.draw.rect(aura_surf, color, (sx, sy, 2, 2))
            pygame.draw.rect(aura_surf, _NS_korokai.PALETTE["crimson_shine"],
                             (sx, sy, 1, 1))
        surface.blit(aura_surf, (x - r - 15, y - r - 15))
        # Radial tendrils outward
        for i in range(6):
            angle = phase * 1.5 + i * math.pi / 3
            end_x = x + int(math.cos(angle) * (r + 10))
            end_y = y + int(math.sin(angle) * (r + 10))
            start_x = x + int(math.cos(angle) * r)
            start_y = y + int(math.sin(angle) * r)
            alpha = _NS_korokai._alpha(150 + math.sin(phase * 3 + i) * 40)
            pygame.draw.line(surface,
                             (*_NS_korokai.PALETTE["crimson_light"], alpha),
                             (start_x, start_y), (end_x, end_y), 1)
            pygame.draw.rect(surface, _NS_korokai.PALETTE["crimson_shine"],
                             (end_x, end_y, 1, 1))
    # ============================================================
    # SKILL E - LIGHTNING PIERCE (Chidori-style thrust)
    # ============================================================
    def _draw_lightning_pierce_ground(surface, boss, x, y, timer, phase):
        """Dash trail on ground."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_korokai._target_position(boss, x, y)
        if 0.35 < progress < 0.75:
            # Trail on ground
            for i in range(8):
                dt = (progress - 0.35) / 0.4 - i * 0.05
                if dt < 0:
                    continue
                dx = int(x + (tx - x) * dt)
                dy = ty + 40
                alpha = _NS_korokai._alpha(180 * (1 - i / 8))
                pygame.draw.ellipse(surface,
                                    (*_NS_korokai.PALETTE["elec_mid"], alpha),
                                    (dx - 8, dy - 3, 16, 6))
    def _draw_lightning_pierce_skill(surface, boss, x, y, timer, phase,
                                     body_offset=0):
        """Chidori-like lightning in hand + dash + pierce impact."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_korokai._target_position(boss, x, y)
        if progress < 0.35:
            # Charging Chidori in hand
            t = progress / 0.35
            hand_x = x + facing * 20
            hand_y = y - 4
            # Massive lightning ball in hand
            for r in range(int(18 * t), 0, -1):
                alpha = _NS_korokai._alpha(220 * t * (18 - r) / 18)
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["elec_darkest"], alpha),
                                      (hand_x, hand_y), r)
            for r in range(int(14 * t), 0, -1):
                alpha = _NS_korokai._alpha(240 * t * (14 - r) / 14)
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["elec_dark"], alpha),
                                      (hand_x, hand_y), r)
            _NS_korokai._aacircle(surface, _NS_korokai.PALETTE["elec_mid"],
                                  (hand_x, hand_y), max(1, int(10 * t)))
            _NS_korokai._aacircle(surface, _NS_korokai.PALETTE["elec_bright"],
                                  (hand_x, hand_y), max(1, int(6 * t)))
            _NS_korokai._aacircle(surface, _NS_korokai.PALETTE["elec_hot"],
                                  (hand_x, hand_y), max(1, int(3 * t)))
            _NS_korokai._aacircle(surface, _NS_korokai.PALETTE["elec_shine"],
                                  (hand_x, hand_y), max(1, int(1 * t)))
            pygame.draw.rect(surface, _NS_korokai.PALETTE["white"],
                             (hand_x, hand_y, 1, 1))
            # Chirping lightning bolts (chidori's signature)
            for i in range(8):
                angle = phase * 5 + i * math.pi / 4
                lightning_r = 20 + int(math.sin(phase * 8 + i) * 5)
                ex = hand_x + int(math.cos(angle) * lightning_r)
                ey = hand_y + int(math.sin(angle) * lightning_r)
                _NS_korokai._draw_lightning_bolt(
                    surface, (hand_x, hand_y), (ex, ey),
                    _NS_korokai.PALETTE["elec_bright"],
                    width=2, jitter=4, alpha=int(220 * t)
                )
                _NS_korokai._draw_lightning_bolt(
                    surface, (hand_x, hand_y), (ex, ey),
                    _NS_korokai.PALETTE["elec_shine"],
                    width=1, jitter=2, alpha=int(255 * t)
                )
                pygame.draw.rect(surface, _NS_korokai.PALETTE["elec_shine"],
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, _NS_korokai.PALETTE["white"],
                                 (ex, ey, 1, 1))
        elif progress < 0.75:
            # DASH + PIERCE - big lightning trail and chidori in hand
            t = (progress - 0.35) / 0.4
            # Lightning still in hand (during dash)
            hand_x = x + facing * 22
            hand_y = y - 4
            # Chidori ball
            for r in range(15, 0, -1):
                alpha = _NS_korokai._alpha(200 * (15 - r) / 15)
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["elec_darkest"], alpha),
                                      (hand_x, hand_y), r)
            _NS_korokai._aacircle(surface, _NS_korokai.PALETTE["elec_dark"],
                                  (hand_x, hand_y), 10)
            _NS_korokai._aacircle(surface, _NS_korokai.PALETTE["elec_mid"],
                                  (hand_x, hand_y), 6)
            _NS_korokai._aacircle(surface, _NS_korokai.PALETTE["elec_bright"],
                                  (hand_x, hand_y), 4)
            _NS_korokai._aacircle(surface, _NS_korokai.PALETTE["elec_shine"],
                                  (hand_x, hand_y), 2)
            pygame.draw.rect(surface, _NS_korokai.PALETTE["white"],
                             (hand_x, hand_y, 1, 1))
            # Chirping bolts around hand
            for i in range(6):
                angle = phase * 8 + i * math.pi / 3
                ex = hand_x + int(math.cos(angle) * 18)
                ey = hand_y + int(math.sin(angle) * 18)
                _NS_korokai._draw_lightning_bolt(
                    surface, (hand_x, hand_y), (ex, ey),
                    _NS_korokai.PALETTE["elec_bright"],
                    width=2, jitter=3, alpha=220
                )
            # DASH TRAIL (multiple streak lines behind boss)
            for line_i in range(4):
                streak_y_offset = (line_i - 1.5) * 4
                line_y = y - 4 + streak_y_offset
                for i in range(8):
                    trail_offset = i * 8
                    sx = hand_x - facing * (10 + trail_offset)
                    alpha = _NS_korokai._alpha(220 - i * 25)
                    _NS_korokai._aaline(surface,
                                        (*_NS_korokai.PALETTE["elec_dark"], alpha),
                                        (sx, line_y), (sx + facing * 6, line_y), 2)
                    _NS_korokai._aaline(surface,
                                        (*_NS_korokai.PALETTE["elec_bright"], alpha),
                                        (sx, line_y), (sx + facing * 6, line_y), 1)
            # Impact at target (only when close)
            if t > 0.6:
                impact_t = (t - 0.6) / 0.4
                radius = int(20 + impact_t * 25)
                alpha = _NS_korokai._alpha(240 * (1 - impact_t))
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["elec_darkest"], alpha),
                                      (tx, ty), radius + 5)
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["elec_dark"], alpha),
                                      (tx, ty), radius)
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["elec_mid"], alpha),
                                      (tx, ty), max(1, radius - 8))
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["elec_bright"], alpha),
                                      (tx, ty), max(1, radius - 15))
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["elec_shine"], alpha),
                                      (tx, ty), max(1, radius // 5))
                # Explosive lightning burst
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius * 1.3)
                    ey = ty + int(math.sin(angle_s) * radius * 1.3)
                    _NS_korokai._draw_lightning_bolt(
                        surface, (tx, ty), (ex, ey),
                        _NS_korokai.PALETTE["elec_shine"],
                        width=2, segments=5, jitter=5,
                        alpha=int(240 * (1 - impact_t))
                    )
                    pygame.draw.rect(surface, _NS_korokai.PALETTE["white"],
                                     (ex, ey, 2, 2))
        else:
            # Aftermath - lingering sparks
            t = (progress - 0.75) / 0.25
            for i in range(8):
                rise_t = (phase * 0.8 + i * 0.13) % 1.0
                rx = tx + int(math.sin(phase + i) * 30)
                ry = ty - int(rise_t * 30)
                alpha = _NS_korokai._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    pygame.draw.rect(surface,
                                     (*_NS_korokai.PALETTE["elec_bright"], alpha),
                                     (rx, ry, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_korokai.PALETTE["elec_shine"], alpha),
                                     (rx, ry, 1, 1))
    # ============================================================
    # SKILL R - VOID WARP (dimensional warp)
    # ============================================================
    def _draw_void_warp_ground(surface, boss, x, y, timer, phase):
        """Ground portal at target."""
        tx, ty = _NS_korokai._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.3:
            t = min(1.0, (progress - 0.3) / 0.5)
            r = int(40 * t)
            if r > 3:
                # Purple portal
                pygame.draw.ellipse(surface,
                                    (*_NS_korokai.PALETTE["void_darkest"], 220),
                                    (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
                pygame.draw.ellipse(surface,
                                    (*_NS_korokai.PALETTE["void_dark"], 220),
                                    (tx - r + 3, ty - r // 3 + 2,
                                     r * 2 - 6, r * 2 // 3 - 4), 2)
                pygame.draw.ellipse(surface,
                                    (*_NS_korokai.PALETTE["void_mid"], 200),
                                    (tx - r + 8, ty - r // 3 + 4,
                                     r * 2 - 16, r * 2 // 3 - 8), 1)
    def _draw_void_warp_skill(surface, boss, x, y, timer, phase):
        """Warp portal + spiral vortex sucking target in."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_korokai._target_position(boss, x, y)
        if progress < 0.3:
            # Charge - focus/aim at target with eye
            t = progress / 0.3
            # Beam from boss eye to target
            eye_x = x - 3
            eye_y = y - 27
            beam_end_x = int(eye_x + (tx - eye_x) * t)
            beam_end_y = int(eye_y + (ty - eye_y) * t)
            _NS_korokai._aaline(surface,
                                (*_NS_korokai.PALETTE["crimson_dark"], 180),
                                (eye_x, eye_y), (beam_end_x, beam_end_y), 3)
            _NS_korokai._aaline(surface,
                                (*_NS_korokai.PALETTE["crimson_mid"], 220),
                                (eye_x, eye_y), (beam_end_x, beam_end_y), 2)
            _NS_korokai._aaline(surface,
                                (*_NS_korokai.PALETTE["crimson_light"], 255),
                                (eye_x, eye_y), (beam_end_x, beam_end_y), 1)
            # Small purple glow at target
            if t > 0.5:
                pre_r = int(6 * (t - 0.5) * 2)
                for r in range(pre_r + 2, 0, -1):
                    alpha = _NS_korokai._alpha(180 * (pre_r + 2 - r) / (pre_r + 2))
                    _NS_korokai._aacircle(surface,
                                          (*_NS_korokai.PALETTE["void_mid"], alpha),
                                          (tx, ty), r)
        elif progress < 0.7:
            # WARP VORTEX - spiral sucking inward
            t = (progress - 0.3) / 0.4
            # Multiple spiral layers
            for spiral_layer in range(3):
                spiral_r_max = 40 - spiral_layer * 8
                num_pts = 40
                for i in range(num_pts):
                    spiral_t = i / num_pts
                    angle = phase * 3 + spiral_t * math.pi * 4 + spiral_layer * 0.5
                    # Spiral gets tighter toward center
                    spiral_r = int((1 - spiral_t) * spiral_r_max)
                    sx = tx + int(math.cos(angle) * spiral_r)
                    sy = ty + int(math.sin(angle) * spiral_r * 0.6)
                    alpha = _NS_korokai._alpha(200 - spiral_layer * 40)
                    if spiral_layer == 0:
                        _NS_korokai._aacircle(surface,
                                              (*_NS_korokai.PALETTE["void_darkest"], alpha),
                                              (sx, sy), 3)
                        _NS_korokai._aacircle(surface,
                                              (*_NS_korokai.PALETTE["void_dark"], alpha),
                                              (sx, sy), 2)
                    elif spiral_layer == 1:
                        _NS_korokai._aacircle(surface,
                                              (*_NS_korokai.PALETTE["void_mid"], alpha),
                                              (sx, sy), 2)
                        pygame.draw.rect(surface,
                                         (*_NS_korokai.PALETTE["void_light"], alpha),
                                         (sx, sy, 1, 1))
                    else:
                        pygame.draw.rect(surface,
                                         (*_NS_korokai.PALETTE["void_light"], alpha),
                                         (sx, sy, 1, 1))
                        pygame.draw.rect(surface,
                                         (*_NS_korokai.PALETTE["void_shine"], alpha),
                                         (sx, sy, 1, 1))
            # Central dark hole (target being warped)
            hole_r = int(15 * t)
            for r in range(hole_r, 0, -1):
                alpha = _NS_korokai._alpha(240 * (hole_r - r) / hole_r)
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["shadow_deep"], alpha),
                                      (tx, ty), r)
            _NS_korokai._aacircle(surface, _NS_korokai.PALETTE["void_darkest"],
                                  (tx, ty), max(1, hole_r - 3))
            # Radial streaks being sucked in
            for i in range(8):
                streak_angle = phase * 2 + i * math.pi / 4
                sx = tx + int(math.cos(streak_angle) * 45)
                sy = ty + int(math.sin(streak_angle) * 30)
                ex = tx + int(math.cos(streak_angle) * 15)
                ey = ty + int(math.sin(streak_angle) * 15)
                pygame.draw.line(surface, _NS_korokai.PALETTE["void_light"],
                                 (sx, sy), (ex, ey), 2)
                pygame.draw.line(surface, _NS_korokai.PALETTE["void_shine"],
                                 (sx, sy), (ex, ey), 1)
        else:
            # Aftermath - portal closing
            t = (progress - 0.7) / 0.3
            close_r = int((1 - t) * 30)
            if close_r > 2:
                for r in range(close_r, 0, -2):
                    alpha = _NS_korokai._alpha(200 * (close_r - r) / close_r * (1 - t))
                    _NS_korokai._aacircle(surface,
                                          (*_NS_korokai.PALETTE["void_dark"], alpha),
                                          (tx, ty), r)
                # Central bright flash fading
                _NS_korokai._aacircle(surface,
                                      (*_NS_korokai.PALETTE["void_shine"],
                                       _NS_korokai._alpha(180 * (1 - t))),
                                      (tx, ty), max(1, close_r // 3))
            # Fading purple particles
            for i in range(10):
                p_t = (phase * 0.5 + i * 0.1) % 1.0
                px = tx + int(math.sin(phase + i) * 25)
                py = ty - int(p_t * 25)
                alpha = _NS_korokai._alpha(180 * (1 - t) * (1 - p_t))
                if alpha > 0:
                    _NS_korokai._aacircle(surface,
                                          (*_NS_korokai.PALETTE["void_mid"], alpha),
                                          (px, py), 2)
                    pygame.draw.rect(surface, _NS_korokai.PALETTE["void_light"],
                                     (px, py, 1, 1))



# ====================================================================
# VERDANIX (VERDANT FURY) - Mini Boss
# ====================================================================

class _NS_verdanix:
    """Namespace verdanix - Verdant Fury taijutsu boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin tones
        "skin_shadow": (170, 130, 100),
        "skin_dark": (215, 175, 135),
        "skin_mid": (240, 200, 165),
        "skin_light": (255, 220, 190),
        "skin_shine": (255, 240, 215),
        # Black bowl-cut hair
        "hair_darkest": (5, 5, 10),
        "hair_dark": (18, 18, 25),
        "hair_mid": (40, 40, 55),
        "hair_light": (75, 75, 90),
        "hair_shine": (120, 120, 140),
        # Green jumpsuit (main outfit)
        "suit_darkest": (15, 45, 20),
        "suit_dark": (35, 80, 40),
        "suit_mid": (65, 125, 65),
        "suit_light": (100, 165, 95),
        "suit_shine": (145, 205, 130),
        # Red belt/sash
        "sash_dark": (75, 15, 15),
        "sash_mid": (155, 35, 35),
        "sash_light": (220, 70, 70),
        "sash_shine": (255, 130, 120),
        # Orange leg warmers/bandage wraps at ankles
        "wrap_dark": (100, 55, 20),
        "wrap_mid": (180, 105, 40),
        "wrap_light": (230, 155, 75),
        "wrap_shine": (255, 200, 110),
        # White hand bandages
        "bandage_shadow": (150, 145, 130),
        "bandage_dark": (195, 185, 165),
        "bandage_mid": (225, 215, 195),
        "bandage_light": (245, 240, 225),
        "bandage_shine": (255, 252, 245),
        # Sandals (dark)
        "sandal_dark": (25, 15, 10),
        "sandal_mid": (55, 40, 25),
        # Headband metal
        "metal_dark": (55, 55, 65),
        "metal_mid": (140, 140, 155),
        "metal_light": (215, 215, 225),
        "metal_shine": (255, 255, 255),
        # Green energy (Q, W, E, R - main theme!)
        "green_darkest": (5, 40, 15),
        "green_dark": (20, 110, 40),
        "green_mid": (50, 200, 80),
        "green_bright": (130, 255, 140),
        "green_hot": (200, 255, 200),
        "green_shine": (240, 255, 240),
        # Fury red aura (R skill secondary color)
        "fury_darkest": (55, 5, 8),
        "fury_dark": (140, 20, 20),
        "fury_mid": (230, 60, 45),
        "fury_bright": (255, 130, 100),
        "fury_shine": (255, 210, 180),
        # Steam/mist
        "steam_dark": (100, 130, 100),
        "steam_mid": (160, 190, 160),
        "steam_light": (220, 240, 220),
        # Black eyes
        "eye_dark": (10, 10, 15),
        "eye_mid": (35, 35, 45),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_verdanix._clamp(color)
        if _NS_verdanix.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_verdanix._clamp(color)
        if _NS_verdanix.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        # Safety check for degenerate polygons
        if len(points) < 3:
            if len(points) == 2:
                pygame.draw.line(surface, _NS_verdanix._clamp(color),
                                 points[0], points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_verdanix._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_verdanix(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_verdanix._detect_moving(boss)
        _NS_verdanix._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_ver_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind
        _NS_verdanix._draw_verdant_aura(surface, x, y, pulse, active_skill == "r")
        _NS_verdanix._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "q":
            _NS_verdanix._draw_kick_dash_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_verdanix._draw_cyclone_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_verdanix._draw_gate_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating bob
        float_bob = int(math.sin(pulse * 0.6) * 3)
        # Handle body positioning during skills
        body_x_offset = 0
        body_y_offset = 0
        show_body = True
        if active_skill == "q":
            duration = 55
            q_prog = max(0.0, min(1.0, 1 - skill_timer / duration))
            if 0.2 < q_prog < 0.7:
                # Dashing forward
                dash_t = (q_prog - 0.2) / 0.5
                tx, ty = _NS_verdanix._target_position(boss, x, y)
                body_x_offset = int((tx - x - boss.direction * 40) * dash_t)
        if active_skill == "w":
            duration = 60
            w_prog = max(0.0, min(1.0, 1 - skill_timer / duration))
            if 0.15 < w_prog < 0.65:
                # Fast dash with swirl (body slightly translucent - moving fast)
                dash_t = (w_prog - 0.15) / 0.5
                tx, ty = _NS_verdanix._target_position(boss, x, y)
                body_x_offset = int((tx - x - boss.direction * 30) * dash_t)
        if active_skill == "e":
            # E - spinning in place, no body offset but body will be drawn spinning
            pass
        # Body (always floating)
        if show_body:
            actual_x = x + body_x_offset
            actual_y = y + body_y_offset + float_bob
            if active_skill == "e" and 0.15 < (1 - skill_timer / 90) < 0.85:
                # Draw spinning body for cyclone
                _NS_verdanix._draw_spinning_body(surface, boss, actual_x, actual_y,
                                                 skill_timer, pulse)
            elif active_skill == "r" and 0.1 < (1 - skill_timer / 100) < 0.9:
                # R active - power stance with red/green aura around
                _NS_verdanix._draw_power_body(surface, boss, actual_x, actual_y,
                                              skill_timer, pulse)
            elif attacking:
                _NS_verdanix._draw_body_attack(surface, boss, actual_x, actual_y)
            elif moving:
                _NS_verdanix._draw_body_walk(surface, boss, actual_x, actual_y)
            else:
                _NS_verdanix._draw_body_idle(surface, boss, actual_x, actual_y)
        # Foreground FX
        if active_skill == "q":
            _NS_verdanix._draw_kick_skill(surface, boss, x, y, skill_timer, pulse,
                                          body_x_offset)
        elif active_skill == "w":
            _NS_verdanix._draw_dynamic_entry_skill(surface, boss, x, y, skill_timer,
                                                  pulse, body_x_offset)
        elif active_skill == "e":
            _NS_verdanix._draw_cyclone_skill(surface, boss, x, y + float_bob,
                                            skill_timer, pulse)
        elif active_skill == "r":
            _NS_verdanix._draw_gate_skill(surface, boss, x, y + float_bob,
                                         skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_ver_previous_timer", 0))
        active = bool(getattr(boss, "_ver_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._ver_attack_active = True
            boss._ver_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._ver_attack_frame = int(getattr(boss, "_ver_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._ver_attack_active = False
            boss._ver_attack_frame = 0
            active = False
        boss._ver_previous_timer = timer
        boss._ver_attack_progress = (
            min(1.0, getattr(boss, "_ver_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_ver_last_x"):
            boss._ver_last_x = boss.x
            boss._ver_last_y = boss.y
            return False
        dx = abs(boss.x - boss._ver_last_x)
        dy = abs(boss.y - boss._ver_last_y)
        boss._ver_last_x = boss.x
        boss._ver_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        _NS_verdanix._draw_shadow(surface, x, y + 50)
        _NS_verdanix._draw_verdant_mist(surface, x, y + 44, boss.pulse)
        _NS_verdanix._draw_body(surface, x, y, boss.direction, boss.pulse, "idle")
    def _draw_body_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_verdanix._draw_shadow(surface, x + sway, y + 50)
        _NS_verdanix._draw_verdant_mist(surface, x + sway, y + 44, phase, trail=True,
                                        facing=boss.direction)
        _NS_verdanix._draw_body(surface, x + sway, y, boss.direction, phase, "walk")
    def _draw_body_attack(surface, boss, x, y):
        progress = getattr(boss, "_ver_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Punch motion
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 4) * boss.direction
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-4 + t * 14)) * boss.direction
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(10 * (1 - t)) * boss.direction
        _NS_verdanix._draw_shadow(surface, x + lunge, y + 50)
        _NS_verdanix._draw_verdant_mist(surface, x + lunge, y + 44, boss.pulse,
                                        intense=True)
        _NS_verdanix._draw_body(surface, x + lunge, y, boss.direction, boss.pulse,
                                "attack", progress)
        _NS_verdanix._draw_punch_impact(surface, boss, x + lunge, y, progress)
    def _draw_spinning_body(surface, boss, x, y, timer, phase):
        """Body spinning rapidly (E skill)."""
        # Spinning fast - draw ghost images
        num_ghosts = 6
        for i in range(num_ghosts):
            spin_angle = phase * 12 + i * math.pi * 2 / num_ghosts
            ghost_x = x + int(math.cos(spin_angle) * 3)
            ghost_alpha_factor = 1.0 - (i / num_ghosts) * 0.7
            # Draw ghost body with reduced clarity
            # Just the outline / silhouette
            _NS_verdanix._draw_shadow(surface, ghost_x, y + 50)
            # Simplified body (just torso + head silhouette)
            pygame.draw.circle(surface, _NS_verdanix.PALETTE["suit_dark"],
                               (ghost_x, y), 14)
            pygame.draw.circle(surface, _NS_verdanix.PALETTE["skin_dark"],
                               (ghost_x, y - 22), 8)
        # Main body (full detail, at center)
        _NS_verdanix._draw_body(surface, x, y, boss.direction, phase, "idle")
    def _draw_power_body(surface, boss, x, y, timer, phase):
        """Body with power aura (R skill)."""
        # Body in power stance
        _NS_verdanix._draw_shadow(surface, x, y + 50)
        _NS_verdanix._draw_verdant_mist(surface, x, y + 44, phase, intense=True)
        _NS_verdanix._draw_body(surface, x, y, boss.direction, phase, "power")
    # ============================================================
    # BODY DRAWING
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw taijutsu warrior: green jumpsuit, bowl-cut hair, bandages."""
        arm_swing = 0
        if action == "attack":
            if attack_progress < 0.35:
                arm_swing = -int(attack_progress / 0.35 * 12) * facing
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                arm_swing = int((-12 + t * 30)) * facing
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_swing = int(18 * (1 - t)) * facing
        elif action == "power":
            # Power stance - arms slightly bent, fists down
            arm_swing = 25
        # Back arm
        _NS_verdanix._draw_arm(surface, cx - facing * 8, cy - 4, facing, phase,
                               -arm_swing // 2, back=True, action=action)
        # Jumpsuit body
        _NS_verdanix._draw_jumpsuit(surface, cx, cy, facing, phase, action)
        # Front arm (punching)
        _NS_verdanix._draw_arm(surface, cx + facing * 6, cy - 4, facing, phase,
                               arm_swing, back=False, action=action,
                               attack_progress=attack_progress)
        # Head
        _NS_verdanix._draw_head(surface, cx, cy - 22, facing, phase, action)
    def _draw_jumpsuit(surface, cx, cy, facing, phase, action):
        """Green jumpsuit (full body outfit)."""
        sway = math.sin(phase * 0.7) * 1
        # Main jumpsuit shape (form-fitting from shoulders to ankles)
        # Torso
        torso_shape = [
            (cx - 11, cy - 8),
            (cx - 12, cy - 2),
            (cx - 11, cy + 6),
            (cx - 9, cy + 14),
            (cx - 7, cy + 20),
            (cx + 7, cy + 20),
            (cx + 9, cy + 14),
            (cx + 11, cy + 6),
            (cx + 12, cy - 2),
            (cx + 11, cy - 8),
        ]
        # Shadow
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["shadow_deep"],
                           [(px + 2, py + 3) for px, py in torso_shape])
        # Base darkest
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["suit_darkest"], torso_shape)
        # Mid green
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["suit_dark"], [
            (cx - 10, cy - 7),
            (cx - 11, cy - 1),
            (cx - 10, cy + 6),
            (cx - 8, cy + 13),
            (cx - 6, cy + 19),
            (cx + 6, cy + 19),
            (cx + 8, cy + 13),
            (cx + 10, cy + 6),
            (cx + 11, cy - 1),
            (cx + 10, cy - 7),
        ])
        # Bright green mid
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["suit_mid"], [
            (cx - 8, cy - 5),
            (cx - 9, cy + 2),
            (cx - 8, cy + 10),
            (cx - 5, cy + 17),
            (cx + 5, cy + 17),
            (cx + 8, cy + 10),
            (cx + 9, cy + 2),
            (cx + 8, cy - 5),
        ])
        # Highlight (chest)
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["suit_light"], [
            (cx - 5, cy - 3),
            (cx - 6, cy + 4),
            (cx - 4, cy + 12),
            (cx + 4, cy + 12),
            (cx + 6, cy + 4),
            (cx + 5, cy - 3),
        ])
        # Shine spot
        pygame.draw.line(surface, _NS_verdanix.PALETTE["suit_shine"],
                         (cx - 2, cy - 1), (cx - 2, cy + 8), 1)
        # Chest definition (subtle muscle)
        pygame.draw.line(surface, _NS_verdanix.PALETTE["suit_darkest"],
                         (cx, cy - 3), (cx, cy + 12), 1)
        # Pectoral line
        pygame.draw.line(surface, _NS_verdanix.PALETTE["suit_darkest"],
                         (cx - 5, cy + 1), (cx - 1, cy + 3), 1)
        pygame.draw.line(surface, _NS_verdanix.PALETTE["suit_darkest"],
                         (cx + 5, cy + 1), (cx + 1, cy + 3), 1)
        # RED SASH/BELT at waist
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["sash_dark"], [
            (cx - 11, cy + 18),
            (cx - 12, cy + 24),
            (cx + 12, cy + 24),
            (cx + 11, cy + 18),
        ])
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["sash_mid"], [
            (cx - 10, cy + 19),
            (cx - 11, cy + 23),
            (cx + 11, cy + 23),
            (cx + 10, cy + 19),
        ])
        # Sash highlight
        pygame.draw.line(surface, _NS_verdanix.PALETTE["sash_light"],
                         (cx - 9, cy + 20), (cx + 9, cy + 20), 1)
        pygame.draw.line(surface, _NS_verdanix.PALETTE["sash_shine"],
                         (cx - 4, cy + 20), (cx + 4, cy + 20), 1)
        # Bottom edge shadow
        pygame.draw.line(surface, _NS_verdanix.PALETTE["sash_dark"],
                         (cx - 10, cy + 22), (cx + 10, cy + 22), 1)
        # Belt buckle (metal square in center)
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["metal_dark"], [
            (cx - 3, cy + 19),
            (cx - 4, cy + 23),
            (cx + 4, cy + 23),
            (cx + 3, cy + 19),
        ])
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["metal_mid"], [
            (cx - 2, cy + 20),
            (cx - 3, cy + 22),
            (cx + 3, cy + 22),
            (cx + 2, cy + 20),
        ])
        pygame.draw.line(surface, _NS_verdanix.PALETTE["metal_light"],
                         (cx - 2, cy + 20), (cx + 2, cy + 20), 1)
        pygame.draw.rect(surface, _NS_verdanix.PALETTE["metal_shine"],
                         (cx - 1, cy + 20, 2, 1))
        # PANTS (jumpsuit continues down)
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["suit_darkest"], [
            (cx - 8, cy + 23),
            (cx - 9, cy + 32),
            (cx - 4, cy + 36),
            (cx - 2, cy + 32),
            (cx - 1, cy + 24),
        ])
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["suit_darkest"], [
            (cx + 1, cy + 24),
            (cx + 2, cy + 32),
            (cx + 4, cy + 36),
            (cx + 9, cy + 32),
            (cx + 8, cy + 23),
        ])
        # Pants mid tone
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["suit_dark"], [
            (cx - 7, cy + 24),
            (cx - 8, cy + 31),
            (cx - 4, cy + 34),
            (cx - 2, cy + 31),
            (cx - 1, cy + 25),
        ])
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["suit_dark"], [
            (cx + 1, cy + 25),
            (cx + 2, cy + 31),
            (cx + 4, cy + 34),
            (cx + 8, cy + 31),
            (cx + 7, cy + 24),
        ])
        # Pants highlight
        pygame.draw.line(surface, _NS_verdanix.PALETTE["suit_mid"],
                         (cx - 6, cy + 26), (cx - 6, cy + 32), 1)
        pygame.draw.line(surface, _NS_verdanix.PALETTE["suit_mid"],
                         (cx + 6, cy + 26), (cx + 6, cy + 32), 1)
        pygame.draw.line(surface, _NS_verdanix.PALETTE["suit_light"],
                         (cx - 5, cy + 28), (cx - 5, cy + 31), 1)
        pygame.draw.line(surface, _NS_verdanix.PALETTE["suit_light"],
                         (cx + 5, cy + 28), (cx + 5, cy + 31), 1)
        # ORANGE LEG WARMERS at ankles
        for leg_side, leg_x_center in ((-1, -6), (1, 6)):
            ankle_x = cx + leg_x_center
            # Warmer wrap
            _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["shadow_deep"], [
                (ankle_x - 3, cy + 33),
                (ankle_x - 4, cy + 40),
                (ankle_x + 4, cy + 40),
                (ankle_x + 3, cy + 33),
            ])
            _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["wrap_dark"], [
                (ankle_x - 3, cy + 34),
                (ankle_x - 4, cy + 39),
                (ankle_x + 4, cy + 39),
                (ankle_x + 3, cy + 34),
            ])
            _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["wrap_mid"], [
                (ankle_x - 2, cy + 35),
                (ankle_x - 3, cy + 38),
                (ankle_x + 3, cy + 38),
                (ankle_x + 2, cy + 35),
            ])
            # Warmer highlight
            pygame.draw.line(surface, _NS_verdanix.PALETTE["wrap_light"],
                             (ankle_x - 2, cy + 36), (ankle_x + 2, cy + 36), 1)
            pygame.draw.line(surface, _NS_verdanix.PALETTE["wrap_shine"],
                             (ankle_x - 1, cy + 36), (ankle_x + 1, cy + 36), 1)
            # Wrap lines (horizontal bandage indicators)
            for wrap_y in (35, 37):
                pygame.draw.line(surface, _NS_verdanix.PALETTE["wrap_dark"],
                                 (ankle_x - 3, cy + wrap_y),
                                 (ankle_x + 3, cy + wrap_y), 1)
            # Sandals (dark)
            _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["sandal_dark"], [
                (ankle_x - 4, cy + 40),
                (ankle_x - 5, cy + 42),
                (ankle_x + 5, cy + 42),
                (ankle_x + 4, cy + 40),
            ])
            _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["sandal_mid"], [
                (ankle_x - 4, cy + 40),
                (ankle_x - 4, cy + 41),
                (ankle_x + 4, cy + 41),
                (ankle_x + 4, cy + 40),
            ])
            # Strap
            pygame.draw.line(surface, _NS_verdanix.PALETTE["sandal_dark"],
                             (ankle_x, cy + 40), (ankle_x, cy + 42), 1)
    def _draw_arm(surface, cx, cy, facing, phase, swing, back=False,
                  action="idle", attack_progress=0):
        """Arm with green sleeve + white bandage on forearm."""
        base_angle = math.pi * 0.5 + math.radians(swing)
        if back:
            base_angle = math.pi * 0.55
        shoulder_x = cx
        shoulder_y = cy
        elbow_len = 11
        elbow_x = shoulder_x + int(math.cos(base_angle) * elbow_len * facing * 0.4)
        elbow_y = shoulder_y + int(math.sin(base_angle) * elbow_len)
        hand_len = 13
        hand_angle = base_angle - math.radians(swing * 0.6)
        hand_x = elbow_x + int(math.cos(hand_angle) * hand_len * facing * 0.6)
        hand_y = elbow_y + int(math.sin(hand_angle) * hand_len)
        # If attacking, extend fist forward
        if action == "attack" and not back and attack_progress > 0.35:
            hand_x = cx + facing * (14 + int(attack_progress * 12))
            hand_y = cy - 2 + int(math.sin(attack_progress * math.pi) * -3)
        thickness = 7 if not back else 6
        # Shadow
        _NS_verdanix._aaline(surface, _NS_verdanix.PALETTE["shadow_deep"],
                             (shoulder_x + 1, shoulder_y + 2),
                             (elbow_x + 1, elbow_y + 2), thickness + 1)
        # Upper arm (green sleeve)
        color_main = _NS_verdanix.PALETTE["suit_darkest"] if back \
            else _NS_verdanix.PALETTE["suit_dark"]
        color_mid = _NS_verdanix.PALETTE["suit_dark"] if back \
            else _NS_verdanix.PALETTE["suit_mid"]
        color_light = _NS_verdanix.PALETTE["suit_light"]
        _NS_verdanix._aaline(surface, color_main,
                             (shoulder_x, shoulder_y),
                             (elbow_x, elbow_y), thickness)
        _NS_verdanix._aaline(surface, color_mid,
                             (shoulder_x, shoulder_y - 1),
                             (elbow_x, elbow_y - 1), max(1, thickness - 3))
        if not back:
            _NS_verdanix._aaline(surface, color_light,
                                 (shoulder_x, shoulder_y - 2),
                                 (elbow_x, elbow_y - 2), max(1, thickness - 5))
        # FOREARM WITH WHITE BANDAGE (Rock Lee signature!)
        _NS_verdanix._aaline(surface, _NS_verdanix.PALETTE["shadow_deep"],
                             (elbow_x + 1, elbow_y + 2),
                             (hand_x + 1, hand_y + 2), thickness)
        # Base bandage
        _NS_verdanix._aaline(surface, _NS_verdanix.PALETTE["bandage_shadow"],
                             (elbow_x, elbow_y),
                             (hand_x, hand_y), thickness)
        _NS_verdanix._aaline(surface, _NS_verdanix.PALETTE["bandage_dark"],
                             (elbow_x, elbow_y),
                             (hand_x, hand_y), thickness - 1)
        _NS_verdanix._aaline(surface, _NS_verdanix.PALETTE["bandage_mid"],
                             (elbow_x, elbow_y - 1),
                             (hand_x, hand_y - 1), max(1, thickness - 3))
        # Diagonal bandage wrap lines (signature look!)
        fore_dx = hand_x - elbow_x
        fore_dy = hand_y - elbow_y
        fore_len = max(1, math.sqrt(fore_dx * fore_dx + fore_dy * fore_dy))
        perp_x = -fore_dy / fore_len
        perp_y = fore_dx / fore_len
        for i in range(5):
            t = (i + 0.5) / 5
            tx = elbow_x + fore_dx * t
            ty = elbow_y + fore_dy * t
            band_w = thickness // 2 + 1
            pygame.draw.line(surface, _NS_verdanix.PALETTE["bandage_shadow"],
                             (int(tx + perp_x * band_w),
                              int(ty + perp_y * band_w)),
                             (int(tx - perp_x * band_w),
                              int(ty - perp_y * band_w)), 1)
        # BANDAGED FIST (large fist wrapped)
        _NS_verdanix._aacircle(surface, _NS_verdanix.PALETTE["shadow_deep"],
                               (hand_x + 1, hand_y + 1), 5)
        _NS_verdanix._aacircle(surface, _NS_verdanix.PALETTE["bandage_shadow"],
                               (hand_x, hand_y), 5)
        _NS_verdanix._aacircle(surface, _NS_verdanix.PALETTE["bandage_dark"],
                               (hand_x, hand_y), 4)
        _NS_verdanix._aacircle(surface, _NS_verdanix.PALETTE["bandage_mid"],
                               (hand_x - 1, hand_y - 1), 3)
        if not back:
            _NS_verdanix._aacircle(surface, _NS_verdanix.PALETTE["bandage_light"],
                                   (hand_x - 1, hand_y - 1), 2)
            pygame.draw.rect(surface, _NS_verdanix.PALETTE["bandage_shine"],
                             (hand_x - 2, hand_y - 2, 2, 1))
        # Knuckle line
        pygame.draw.line(surface, _NS_verdanix.PALETTE["bandage_shadow"],
                         (hand_x - 3, hand_y), (hand_x + 3, hand_y), 1)
        # Bandage wrap around knuckles
        for wrap_off in (-2, 0, 2):
            pygame.draw.line(surface, _NS_verdanix.PALETTE["bandage_shadow"],
                             (hand_x + wrap_off - 3, hand_y - 2),
                             (hand_x + wrap_off - 3, hand_y + 2), 1)
    def _draw_head(surface, cx, cy, facing, phase, action):
        """Head with bowl-cut black hair, thick eyebrows, headband."""
        # Face shape
        face_shape = [
            (cx - 7, cy - 2),
            (cx - 8, cy - 6),
            (cx - 6, cy - 10),
            (cx - 2, cy - 12),
            (cx + 2, cy - 12),
            (cx + 6, cy - 10),
            (cx + 8, cy - 6),
            (cx + 7, cy - 2),
            (cx + 5, cy + 3),
            (cx + 1, cy + 5),
            (cx - 3, cy + 5),
            (cx - 6, cy + 3),
        ]
        # Shadow
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["shadow_deep"],
                           [(px + 1, py + 2) for px, py in face_shape])
        # Base skin
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["skin_shadow"], face_shape)
        # Main face
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["skin_dark"], [
            (cx - 6, cy - 3),
            (cx - 7, cy - 6),
            (cx - 5, cy - 9),
            (cx - 2, cy - 11),
            (cx + 2, cy - 11),
            (cx + 5, cy - 9),
            (cx + 7, cy - 6),
            (cx + 6, cy - 3),
            (cx + 4, cy + 2),
            (cx, cy + 4),
            (cx - 4, cy + 2),
        ])
        # Lighter mid
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["skin_mid"], [
            (cx - 4, cy - 4),
            (cx - 5, cy - 7),
            (cx - 3, cy - 9),
            (cx + 3, cy - 9),
            (cx + 5, cy - 7),
            (cx + 4, cy - 4),
            (cx + 2, cy),
            (cx - 2, cy),
        ])
        # Cheek highlight
        pygame.draw.rect(surface, _NS_verdanix.PALETTE["skin_light"],
                         (cx - 3 * facing, cy - 4, 2, 2))
        pygame.draw.rect(surface, _NS_verdanix.PALETTE["skin_shine"],
                         (cx - 3 * facing, cy - 4, 1, 1))
        # THICK BLACK EYEBROWS (signature!)
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["hair_darkest"], [
            (cx - 5, cy - 7),
            (cx - 6, cy - 6),
            (cx - 1, cy - 6),
            (cx - 1, cy - 7),
        ])
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["hair_dark"], [
            (cx - 5, cy - 7),
            (cx - 5, cy - 6),
            (cx - 2, cy - 6),
            (cx - 2, cy - 7),
        ])
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["hair_darkest"], [
            (cx + 1, cy - 7),
            (cx + 1, cy - 6),
            (cx + 6, cy - 6),
            (cx + 5, cy - 7),
        ])
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["hair_dark"], [
            (cx + 2, cy - 7),
            (cx + 2, cy - 6),
            (cx + 5, cy - 6),
            (cx + 5, cy - 7),
        ])
        # BIG ROUND BLACK EYES
        _NS_verdanix._draw_big_eye(surface, cx - 3, cy - 4, facing, phase, action)
        _NS_verdanix._draw_big_eye(surface, cx + 3, cy - 4, facing, phase, action)
        # Mouth
        if action == "attack" or action == "power":
            # Battle shout (open mouth)
            pygame.draw.rect(surface, _NS_verdanix.PALETTE["shadow_deep"],
                             (cx - 2, cy + 1, 4, 3))
            pygame.draw.rect(surface, (50, 15, 20),
                             (cx - 1, cy + 1, 3, 2))
            # Teeth
            pygame.draw.line(surface, _NS_verdanix.PALETTE["bandage_light"],
                             (cx - 1, cy + 2), (cx + 1, cy + 2), 1)
        else:
            # Determined smile
            pygame.draw.line(surface, _NS_verdanix.PALETTE["shadow_deep"],
                             (cx - 2, cy + 2), (cx + 2, cy + 2), 1)
            pygame.draw.rect(surface, _NS_verdanix.PALETTE["shadow_deep"],
                             (cx - 3, cy + 1, 1, 1))
            pygame.draw.rect(surface, _NS_verdanix.PALETTE["shadow_deep"],
                             (cx + 2, cy + 1, 1, 1))
        # BOWL-CUT HAIR (signature!)
        _NS_verdanix._draw_hair(surface, cx, cy, facing, phase)
        # HEADBAND (white cloth around forehead, above eyebrows)
        _NS_verdanix._draw_headband(surface, cx, cy - 10, facing, phase)
    def _draw_big_eye(surface, cx, cy, facing, phase, action):
        """Big round black eyes."""
        # Eye white (larger)
        pygame.draw.rect(surface, _NS_verdanix.PALETTE["shadow_deep"],
                         (cx - 2, cy - 1, 4, 2))
        pygame.draw.rect(surface, _NS_verdanix.PALETTE["white"],
                         (cx - 1, cy - 1, 3, 2))
        # Large dark pupil
        pygame.draw.rect(surface, _NS_verdanix.PALETTE["eye_dark"],
                         (cx, cy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_verdanix.PALETTE["shadow_deep"],
                         (cx, cy, 2, 1))
        # Small white highlight
        pygame.draw.rect(surface, _NS_verdanix.PALETTE["white"],
                         (cx, cy - 1, 1, 1))
        if action == "power":
            # Intense determined look (small red glow around)
            for r in range(3, 0, -1):
                alpha = _NS_verdanix._alpha(100 * (3 - r) / 3)
                _NS_verdanix._aacircle(surface,
                                       (*_NS_verdanix.PALETTE["fury_bright"], alpha),
                                       (cx, cy), r)
    def _draw_hair(surface, cx, cy, facing, phase):
        """Bowl-cut hairstyle (black, shiny, mushroom shape)."""
        cy_h = cy - 22  # hair position
        # BOWL SHAPE (rounded on top, straight cut around)
        # Top rounded part
        bowl_shape = [
            (cx - 9, cy_h - 4),
            (cx - 9, cy_h - 10),
            (cx - 7, cy_h - 14),
            (cx - 3, cy_h - 16),
            (cx + 3, cy_h - 16),
            (cx + 7, cy_h - 14),
            (cx + 9, cy_h - 10),
            (cx + 9, cy_h - 4),
        ]
        # Shadow
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["shadow_deep"],
                           [(px + 1, py + 2) for px, py in bowl_shape])
        # Base darkest
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["hair_darkest"], bowl_shape)
        # Mid dark
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["hair_dark"], [
            (cx - 8, cy_h - 4),
            (cx - 8, cy_h - 10),
            (cx - 6, cy_h - 13),
            (cx - 2, cy_h - 15),
            (cx + 2, cy_h - 15),
            (cx + 6, cy_h - 13),
            (cx + 8, cy_h - 10),
            (cx + 8, cy_h - 4),
        ])
        # Highlight (shiny top)
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["hair_mid"], [
            (cx - 5, cy_h - 8),
            (cx - 3, cy_h - 12),
            (cx + 3, cy_h - 12),
            (cx + 5, cy_h - 8),
            (cx + 4, cy_h - 6),
            (cx - 4, cy_h - 6),
        ])
        # Bright shine spot (very shiny bowl-cut!)
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["hair_light"], [
            (cx - 3, cy_h - 10),
            (cx - 1, cy_h - 12),
            (cx + 1, cy_h - 12),
            (cx + 3, cy_h - 10),
            (cx + 2, cy_h - 8),
            (cx - 2, cy_h - 8),
        ])
        # Peak shine
        pygame.draw.line(surface, _NS_verdanix.PALETTE["hair_shine"],
                         (cx - 1, cy_h - 11), (cx + 1, cy_h - 11), 1)
        pygame.draw.rect(surface, _NS_verdanix.PALETTE["hair_shine"],
                         (cx, cy_h - 12, 1, 1))
        # Straight-cut BANGS across forehead (thick line)
        # The bangs go horizontally across, hiding eyebrows partially
        pygame.draw.line(surface, _NS_verdanix.PALETTE["hair_darkest"],
                         (cx - 8, cy_h - 4), (cx + 8, cy_h - 4), 2)
        pygame.draw.line(surface, _NS_verdanix.PALETTE["hair_dark"],
                         (cx - 7, cy_h - 3), (cx + 7, cy_h - 3), 1)
        # Hair covering ears (side flaps)
        for side_mult in (-1, 1):
            side_x = cx + 8 * side_mult
            _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["hair_darkest"], [
                (side_x, cy_h - 8),
                (side_x + side_mult * 1, cy_h - 4),
                (side_x + side_mult * 2, cy_h - 2),
                (side_x, cy_h - 2),
                (side_x - side_mult * 1, cy_h - 5),
            ])
            _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["hair_dark"], [
                (side_x, cy_h - 7),
                (side_x + side_mult * 1, cy_h - 4),
                (side_x - side_mult * 1, cy_h - 4),
            ])
    def _draw_headband(surface, cx, cy, facing, phase):
        """Headband with metal plate (worn horizontally on forehead)."""
        # Cloth band
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["shadow_deep"], [
            (cx - 9, cy),
            (cx - 10, cy + 3),
            (cx + 10, cy + 3),
            (cx + 9, cy),
        ])
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["bandage_shadow"], [
            (cx - 8, cy + 1),
            (cx - 9, cy + 3),
            (cx + 9, cy + 3),
            (cx + 8, cy + 1),
        ])
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["bandage_dark"], [
            (cx - 7, cy + 1),
            (cx - 8, cy + 2),
            (cx + 8, cy + 2),
            (cx + 7, cy + 1),
        ])
        pygame.draw.line(surface, _NS_verdanix.PALETTE["bandage_light"],
                         (cx - 6, cy + 1), (cx + 6, cy + 1), 1)
        pygame.draw.rect(surface, _NS_verdanix.PALETTE["bandage_shine"],
                         (cx - 3, cy + 1, 6, 1))
        # METAL PLATE in the middle
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["metal_dark"], [
            (cx - 6, cy + 1),
            (cx - 7, cy + 3),
            (cx + 7, cy + 3),
            (cx + 6, cy + 1),
        ])
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["metal_mid"], [
            (cx - 5, cy + 2),
            (cx - 6, cy + 3),
            (cx + 6, cy + 3),
            (cx + 5, cy + 2),
        ])
        # Metal shine
        pygame.draw.line(surface, _NS_verdanix.PALETTE["metal_light"],
                         (cx - 4, cy + 2), (cx + 4, cy + 2), 1)
        pygame.draw.line(surface, _NS_verdanix.PALETTE["metal_shine"],
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)
        # Simple leaf/swirl symbol on plate
        pygame.draw.circle(surface, _NS_verdanix.PALETTE["shadow_deep"],
                           (cx, cy + 2), 1)
        # Cloth tails hanging behind
        tail_x = cx - 9 * facing
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["bandage_shadow"], [
            (tail_x, cy + 2),
            (tail_x - 2 * facing, cy + 6),
            (tail_x - 3 * facing, cy + 12),
            (tail_x - 1 * facing, cy + 12),
            (tail_x + 1 * facing, cy + 6),
        ])
        _NS_verdanix._poly(surface, _NS_verdanix.PALETTE["bandage_dark"], [
            (tail_x + 1 * facing, cy + 3),
            (tail_x - 1 * facing, cy + 6),
            (tail_x - 2 * facing, cy + 11),
            (tail_x, cy + 11),
        ])
        pygame.draw.line(surface, _NS_verdanix.PALETTE["bandage_mid"],
                         (tail_x, cy + 5),
                         (tail_x - 1 * facing, cy + 10), 1)
    # ============================================================
    # BASIC MELEE - Punch impact
    # ============================================================
    def _draw_punch_impact(surface, boss, x, y, progress):
        """Punch impact with green energy burst."""
        if progress < 0.5 or progress > 0.85:
            return
        facing = boss.direction
        t = (progress - 0.5) / 0.35
        # Impact position
        impact_x = x + facing * 30
        impact_y = y - 4
        # Expanding green shockwave
        r = int(6 + t * 18)
        alpha = _NS_verdanix._alpha(240 * (1 - t))
        _NS_verdanix._aacircle(surface,
                               (*_NS_verdanix.PALETTE["green_darkest"], alpha),
                               (impact_x, impact_y), r + 2, 2)
        _NS_verdanix._aacircle(surface,
                               (*_NS_verdanix.PALETTE["green_dark"], alpha),
                               (impact_x, impact_y), r, 2)
        _NS_verdanix._aacircle(surface,
                               (*_NS_verdanix.PALETTE["green_mid"], alpha),
                               (impact_x, impact_y), max(1, r - 3), 1)
        _NS_verdanix._aacircle(surface,
                               (*_NS_verdanix.PALETTE["green_bright"], alpha),
                               (impact_x, impact_y), max(1, r - 6), 1)
        # Center flash
        _NS_verdanix._aacircle(surface,
                               (*_NS_verdanix.PALETTE["green_shine"], alpha),
                               (impact_x, impact_y), max(1, 3 - int(t * 3)))
        # Radial sparks
        for i in range(6):
            angle = i * math.pi / 3
            ex = impact_x + int(math.cos(angle) * (r + 3))
            ey = impact_y + int(math.sin(angle) * (r + 3))
            pygame.draw.rect(surface,
                             (*_NS_verdanix.PALETTE["green_shine"], alpha),
                             (ex, ey, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_verdanix.PALETTE["white"], alpha),
                             (ex, ey, 1, 1))
    # ============================================================
    # FLOATING MIST
    # ============================================================
    def _draw_verdant_mist(surface, cx, cy, phase, trail=False, facing=1,
                           intense=False):
        """Green chakra mist below body."""
        strength = 1.4 if intense else 1.0
        mist = pygame.Surface((130, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(28, 3, -3):
            alpha = _NS_verdanix._alpha((28 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_verdanix.PALETTE["green_darkest"], alpha),
                    (65 - radius, 20 - radius // 3,
                     radius * 2, max(2, radius // 2))
                )
        for radius in range(18, 2, -2):
            alpha = _NS_verdanix._alpha((18 - radius) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_verdanix.PALETTE["green_dark"], alpha),
                    (65 - radius, 20 - radius // 4,
                     radius * 2, max(2, radius // 3))
                )
        surface.blit(mist, (cx - 65, cy - 10))
        # Rising green sparks
        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            px = cx - 24 + i * 6 + int(math.sin(phase + i) * 3)
            py = cy + 4 - int(t * 24)
            alpha = _NS_verdanix._alpha(220 * (1 - t) * strength)
            if alpha > 0:
                _NS_verdanix._aacircle(surface,
                                       (*_NS_verdanix.PALETTE["green_dark"], alpha),
                                       (px, py), 3)
                _NS_verdanix._aacircle(surface,
                                       (*_NS_verdanix.PALETTE["green_mid"], alpha),
                                       (px, py - 1), 2)
                pygame.draw.rect(surface,
                                 (*_NS_verdanix.PALETTE["green_bright"], alpha),
                                 (px, py - 1, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_verdanix.PALETTE["green_shine"], alpha),
                                 (px, py - 2, 1, 1))
        # Trail
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_verdanix._alpha(160 - i * 25)
                if alpha > 0:
                    _NS_verdanix._aacircle(surface,
                                           (*_NS_verdanix.PALETTE["green_dark"], alpha),
                                           (sx, sy), max(1, 5 - i))
                    _NS_verdanix._aacircle(surface,
                                           (*_NS_verdanix.PALETTE["green_mid"], alpha),
                                           (sx, sy), max(1, 3 - i))
                    pygame.draw.rect(surface, _NS_verdanix.PALETTE["green_bright"],
                                     (sx, sy - 1, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((130, 24), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 12 - radius, 110 + radius * 2, radius * 2)
            )
        pygame.draw.ellipse(shadow, (3, 8, 3, 170), (5, 6, 120, 12))
        pygame.draw.ellipse(shadow, (20, 60, 25, 100), (15, 8, 100, 8))
        surface.blit(shadow, (x - 65, y - 12))
    def _draw_verdant_aura(surface, x, y, phase, gate_active=False):
        """Green aura (red-tinged when Gate active)."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        primary_key = "fury_dark" if gate_active else "green_dark"
        mid_key = "fury_mid" if gate_active else "green_mid"
        for radius in range(90, 5, -5):
            alpha = _NS_verdanix._alpha((90 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_verdanix._aacircle(aura,
                                       (*_NS_verdanix.PALETTE["green_darkest"], alpha),
                                       (110, 90), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_verdanix._alpha((55 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_verdanix._aacircle(aura,
                                       (*_NS_verdanix.PALETTE[primary_key], alpha),
                                       (110, 90), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_verdanix._alpha((30 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_verdanix._aacircle(aura,
                                       (*_NS_verdanix.PALETTE[mid_key], alpha),
                                       (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        # Floating particles
        for i in range(14):
            angle = phase * 0.4 + i * math.pi / 7
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            color = _NS_verdanix.PALETTE[mid_key]
            hot_color = _NS_verdanix.PALETTE["green_bright"] if not gate_active \
                else _NS_verdanix.PALETTE["fury_bright"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot_color, (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground green ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        base_color = _NS_verdanix.PALETTE["green_dark"]
        accent_color = _NS_verdanix.PALETTE["green_bright"]
        if skill == "r":
            base_color = _NS_verdanix.PALETTE["fury_dark"]
            accent_color = _NS_verdanix.PALETTE["fury_bright"]
        pygame.draw.ellipse(ring, (*_NS_verdanix.PALETTE["green_darkest"], 210),
                            (5, 15, 150, 24), 3)
        pygame.draw.ellipse(ring, (*base_color, 220),
                            (14, 17, 132, 20), 2)
        pygame.draw.ellipse(ring, (*accent_color, 180),
                            (25, 19, 110, 16), 1)
        # Runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 27 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 27 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*accent_color, 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*accent_color,
                                        _NS_verdanix._alpha(160 * pulse)),
                                (12, 10, 136, 32), 1)
        surface.blit(ring, (x - 80, y - 25))
    # ============================================================
    # SKILL Q - CRESCENT KICK (dash + front kick with green arc)
    # ============================================================
    def _draw_kick_dash_ground(surface, boss, x, y, timer, phase):
        """Dash trail on ground."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_verdanix._target_position(boss, x, y)
        if 0.2 < progress < 0.75:
            # Streak trail on ground
            for i in range(8):
                dt = (progress - 0.2) / 0.55 - i * 0.06
                if dt < 0:
                    continue
                dx = int(x + (tx - x) * dt)
                dy = ty + 40
                alpha = _NS_verdanix._alpha(160 * (1 - i / 8))
                pygame.draw.ellipse(surface,
                                    (*_NS_verdanix.PALETTE["green_mid"], alpha),
                                    (dx - 8, dy - 3, 16, 6))
    def _draw_kick_skill(surface, boss, x, y, timer, phase, body_offset=0):
        """Dash + front kick with big green arc."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_verdanix._target_position(boss, x, y)
        if progress < 0.2:
            # Wind up - crouch, gather energy
            t = progress / 0.2
            for r in range(int(10 * t), 0, -1):
                alpha = _NS_verdanix._alpha(180 * t)
                _NS_verdanix._aacircle(surface,
                                       (*_NS_verdanix.PALETTE["green_mid"], alpha),
                                       (x, y + 10), r)
            _NS_verdanix._aacircle(surface, _NS_verdanix.PALETTE["green_bright"],
                                   (x, y + 10), max(1, int(4 * t)))
        elif progress < 0.7:
            # DASH FORWARD - draw motion streak
            t = (progress - 0.2) / 0.5
            # Multiple parallel streak lines
            for line_i in range(5):
                streak_y_offset = (line_i - 2) * 5
                line_y = y - 6 + streak_y_offset
                for i in range(8):
                    trail_offset = i * 10
                    sx = x + body_offset - facing * (5 + trail_offset)
                    alpha = _NS_verdanix._alpha(200 - i * 25)
                    _NS_verdanix._aaline(surface,
                                         (*_NS_verdanix.PALETTE["green_dark"], alpha),
                                         (sx, line_y), (sx + facing * 8, line_y), 2)
                    _NS_verdanix._aaline(surface,
                                         (*_NS_verdanix.PALETTE["green_bright"], alpha),
                                         (sx, line_y), (sx + facing * 8, line_y), 1)
                    if i < 3:
                        pygame.draw.rect(surface,
                                         (*_NS_verdanix.PALETTE["green_shine"], alpha),
                                         (sx + facing * 4, line_y, 1, 1))
            # KICK IMPACT near end - big green arc/crescent
            if t > 0.5:
                kick_t = (t - 0.5) / 0.5
                # Kick arc position (at front of dashing body)
                kick_x = x + body_offset + facing * 25
                kick_y = y - 4
                # Big crescent/arc slash
                arc_radius = 22 + int(kick_t * 8)
                num_arc = 15
                arc_pts_inner = []
                arc_pts_outer = []
                # Vertical crescent (kicking up)
                for i in range(num_arc):
                    arc_t = i / (num_arc - 1)
                    arc_angle = -math.pi / 2.3 + arc_t * math.pi / 1.5
                    if facing == -1:
                        arc_angle = math.pi - arc_angle
                    ix = kick_x + int(math.cos(arc_angle) * (arc_radius - 4))
                    iy = kick_y + int(math.sin(arc_angle) * (arc_radius - 4))
                    ox = kick_x + int(math.cos(arc_angle) * (arc_radius + 4))
                    oy = kick_y + int(math.sin(arc_angle) * (arc_radius + 4))
                    arc_pts_inner.append((ix, iy))
                    arc_pts_outer.append((ox, oy))
                # Draw crescent (thick arc)
                for i in range(len(arc_pts_inner) - 1):
                    alpha = _NS_verdanix._alpha(240 * (1 - kick_t * 0.5))
                    pygame.draw.line(surface,
                                     (*_NS_verdanix.PALETTE["green_darkest"], alpha),
                                     arc_pts_inner[i], arc_pts_inner[i + 1], 5)
                    pygame.draw.line(surface,
                                     (*_NS_verdanix.PALETTE["green_dark"], alpha),
                                     arc_pts_inner[i], arc_pts_inner[i + 1], 3)
                    pygame.draw.line(surface,
                                     (*_NS_verdanix.PALETTE["green_mid"], alpha),
                                     arc_pts_inner[i], arc_pts_inner[i + 1], 2)
                    pygame.draw.line(surface,
                                     (*_NS_verdanix.PALETTE["green_bright"], alpha),
                                     arc_pts_inner[i], arc_pts_inner[i + 1], 1)
                    # Outer edge glow
                    pygame.draw.line(surface,
                                     (*_NS_verdanix.PALETTE["green_bright"], alpha),
                                     arc_pts_outer[i], arc_pts_outer[i + 1], 2)
                    pygame.draw.line(surface,
                                     (*_NS_verdanix.PALETTE["green_shine"], alpha),
                                     arc_pts_outer[i], arc_pts_outer[i + 1], 1)
                # Bright middle line
                for i in range(len(arc_pts_inner) - 1):
                    mx1 = (arc_pts_inner[i][0] + arc_pts_outer[i][0]) // 2
                    my1 = (arc_pts_inner[i][1] + arc_pts_outer[i][1]) // 2
                    mx2 = (arc_pts_inner[i + 1][0] + arc_pts_outer[i + 1][0]) // 2
                    my2 = (arc_pts_inner[i + 1][1] + arc_pts_outer[i + 1][1]) // 2
                    pygame.draw.line(surface,
                                     (*_NS_verdanix.PALETTE["green_shine"], alpha),
                                     (mx1, my1), (mx2, my2), 1)
                    pygame.draw.line(surface, _NS_verdanix.PALETTE["white"],
                                     (mx1, my1), (mx2, my2), 1)
                # Impact burst at target
                if kick_t > 0.6:
                    burst_t = (kick_t - 0.6) / 0.4
                    burst_r = int(12 + burst_t * 20)
                    burst_alpha = _NS_verdanix._alpha(240 * (1 - burst_t))
                    _NS_verdanix._aacircle(surface,
                                           (*_NS_verdanix.PALETTE["green_dark"], burst_alpha),
                                           (tx, ty), burst_r, 2)
                    _NS_verdanix._aacircle(surface,
                                           (*_NS_verdanix.PALETTE["green_mid"], burst_alpha),
                                           (tx, ty), max(1, burst_r - 4), 1)
                    for i in range(8):
                        angle_s = i * math.pi / 4
                        ex = tx + int(math.cos(angle_s) * burst_r)
                        ey = ty + int(math.sin(angle_s) * burst_r)
                        pygame.draw.rect(surface,
                                         (*_NS_verdanix.PALETTE["green_shine"], burst_alpha),
                                         (ex, ey, 2, 2))
    # ============================================================
    # SKILL W - GALE ENTRY (swirl dash + strike)
    # ============================================================
    def _draw_dynamic_entry_skill(surface, boss, x, y, timer, phase, body_offset=0):
        """Green swirl dash trail + stun stars."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_verdanix._target_position(boss, x, y)
        if progress < 0.15:
            # Charge - swirl gathering
            t = progress / 0.15
            for i in range(8):
                spiral_angle = phase * 5 + i * math.pi / 4
                spiral_r = int(15 * t)
                sx = x + int(math.cos(spiral_angle) * spiral_r)
                sy = y - 4 + int(math.sin(spiral_angle) * spiral_r)
                alpha = _NS_verdanix._alpha(200 * t)
                _NS_verdanix._aacircle(surface,
                                       (*_NS_verdanix.PALETTE["green_mid"], alpha),
                                       (sx, sy), 3)
                pygame.draw.rect(surface, _NS_verdanix.PALETTE["green_bright"],
                                 (sx, sy, 1, 1))
        elif progress < 0.7:
            # HIGH-SPEED SWIRL DASH
            t = (progress - 0.15) / 0.55
            # Draw big spiral behind the dashing body
            spiral_center_x = x + body_offset - facing * 20
            spiral_center_y = y - 4
            # Large spiraling swirl (motion effect)
            num_spirals = 20
            for i in range(num_spirals):
                spiral_t = i / num_spirals
                # Spiral goes outward
                spiral_angle = phase * 8 + spiral_t * math.pi * 3
                spiral_r = 5 + int(spiral_t * 20)
                sx = spiral_center_x + int(math.cos(spiral_angle) * spiral_r)
                sy = spiral_center_y + int(math.sin(spiral_angle) * spiral_r)
                alpha = _NS_verdanix._alpha(240 - i * 8)
                _NS_verdanix._aacircle(surface,
                                       (*_NS_verdanix.PALETTE["green_dark"], alpha),
                                       (sx, sy), 4)
                _NS_verdanix._aacircle(surface,
                                       (*_NS_verdanix.PALETTE["green_mid"], alpha),
                                       (sx, sy), 3)
                _NS_verdanix._aacircle(surface,
                                       (*_NS_verdanix.PALETTE["green_bright"], alpha),
                                       (sx, sy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_verdanix.PALETTE["green_shine"], alpha),
                                 (sx, sy, 1, 1))
            # Fast horizontal streaks
            for line_i in range(3):
                streak_y = y - 6 + line_i * 4
                for streak_i in range(5):
                    sx = x + body_offset - facing * (20 + streak_i * 12)
                    alpha = _NS_verdanix._alpha(200 - streak_i * 35)
                    _NS_verdanix._aaline(surface,
                                         (*_NS_verdanix.PALETTE["green_bright"], alpha),
                                         (sx, streak_y),
                                         (sx + facing * 10, streak_y), 1)
            # Impact stun effect at target (last phase of skill)
            if t > 0.7:
                # Multiple stun stars appearing above target
                for i in range(4):
                    star_t = (phase * 3 + i * 0.25) % 1.0
                    star_angle = phase * 2 + i * math.pi / 2
                    star_r = 12
                    sx = tx + int(math.cos(star_angle) * star_r)
                    sy = ty - 10 + int(math.sin(star_angle) * star_r * 0.5)
                    # Draw star (5-point)
                    for point in range(5):
                        p_angle = point * math.pi * 2 / 5 - math.pi / 2
                        px = sx + int(math.cos(p_angle) * 3)
                        py = sy + int(math.sin(p_angle) * 3)
                        pygame.draw.line(surface,
                                         _NS_verdanix.PALETTE["wrap_shine"],
                                         (sx, sy), (px, py), 1)
                    _NS_verdanix._aacircle(surface,
                                           _NS_verdanix.PALETTE["wrap_light"],
                                           (sx, sy), 2)
                    pygame.draw.rect(surface, _NS_verdanix.PALETTE["white"],
                                     (sx, sy, 1, 1))
                # Impact burst
                burst_r = int(15 + (t - 0.7) * 30)
                burst_alpha = _NS_verdanix._alpha(240 * (1 - (t - 0.7) / 0.3))
                _NS_verdanix._aacircle(surface,
                                       (*_NS_verdanix.PALETTE["green_dark"], burst_alpha),
                                       (tx, ty), burst_r, 2)
                _NS_verdanix._aacircle(surface,
                                       (*_NS_verdanix.PALETTE["green_bright"], burst_alpha),
                                       (tx, ty), max(1, burst_r - 6), 1)
    # ============================================================
    # SKILL E - VERDANT CYCLONE (spinning tornado)
    # ============================================================
    def _draw_cyclone_ground(surface, boss, x, y, timer, phase):
        """Circular AOE marker on ground."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.15:
            r = int(45 * min(1.0, (progress - 0.15) * 3))
            if r > 3:
                pygame.draw.ellipse(surface,
                                    (*_NS_verdanix.PALETTE["green_darkest"], 200),
                                    (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 3)
                pygame.draw.ellipse(surface,
                                    (*_NS_verdanix.PALETTE["green_dark"], 200),
                                    (x - r + 3, y + 40 - r // 3 + 2,
                                     r * 2 - 6, r * 2 // 3 - 4), 2)
                pygame.draw.ellipse(surface,
                                    (*_NS_verdanix.PALETTE["green_mid"], 180),
                                    (x - r + 8, y + 40 - r // 3 + 4,
                                     r * 2 - 16, r * 2 // 3 - 8), 1)
    def _draw_cyclone_skill(surface, boss, x, y, timer, phase):
        """Green swirling tornado around boss."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.15:
            # Wind up - starting spin
            t = progress / 0.15
            for i in range(6):
                spiral_angle = phase * 5 + i * math.pi / 3
                spiral_r = int(10 * t)
                sx = x + int(math.cos(spiral_angle) * spiral_r)
                sy = y + int(math.sin(spiral_angle) * spiral_r)
                _NS_verdanix._aacircle(surface,
                                       _NS_verdanix.PALETTE["green_mid"],
                                       (sx, sy), 3)
                pygame.draw.rect(surface, _NS_verdanix.PALETTE["green_bright"],
                                 (sx, sy, 1, 1))
        elif progress < 0.85:
            # FULL CYCLONE - vertical tornado around body
            tornado_h = 60
            num_layers = 12
            for layer_i in range(num_layers):
                layer_t = layer_i / num_layers
                layer_y = y - int(layer_t * tornado_h) + 20
                # Width based on layer (wider in middle)
                width_factor = math.sin(layer_t * math.pi) * 0.5 + 0.7
                layer_w = int(35 * width_factor)
                # Rotating ring of particles per layer
                for i in range(16):
                    ring_angle = phase * 8 + i * math.pi / 8 + layer_i * 0.4
                    sx = x + int(math.cos(ring_angle) * layer_w)
                    sy = layer_y + int(math.sin(ring_angle) * layer_w * 0.35)
                    # Depth-based coloring
                    d = abs(math.cos(ring_angle))
                    alpha = _NS_verdanix._alpha(220)
                    if d > 0.7:  # Front-facing (bright)
                        _NS_verdanix._aacircle(surface,
                                               (*_NS_verdanix.PALETTE["green_mid"], alpha),
                                               (sx, sy), 3)
                        _NS_verdanix._aacircle(surface,
                                               (*_NS_verdanix.PALETTE["green_bright"], alpha),
                                               (sx, sy), 2)
                        pygame.draw.rect(surface,
                                         (*_NS_verdanix.PALETTE["green_shine"], alpha),
                                         (sx, sy, 1, 1))
                    elif d > 0.4:  # Side
                        _NS_verdanix._aacircle(surface,
                                               (*_NS_verdanix.PALETTE["green_dark"], alpha),
                                               (sx, sy), 3)
                        _NS_verdanix._aacircle(surface,
                                               (*_NS_verdanix.PALETTE["green_mid"], alpha),
                                               (sx, sy), 2)
                    else:  # Back-facing (dark)
                        _NS_verdanix._aacircle(surface,
                                               (*_NS_verdanix.PALETTE["green_darkest"], alpha),
                                               (sx, sy), 2)
                        pygame.draw.rect(surface,
                                         (*_NS_verdanix.PALETTE["green_dark"], alpha),
                                         (sx, sy, 1, 1))
            # Extra fast-swirling streaks (motion lines)
            for i in range(8):
                streak_angle = phase * 10 + i * math.pi / 4
                s_r = 40
                start_x = x + int(math.cos(streak_angle) * s_r)
                start_y = y + int(math.sin(streak_angle) * s_r * 0.4)
                end_x = x + int(math.cos(streak_angle + 0.3) * s_r)
                end_y = y + int(math.sin(streak_angle + 0.3) * s_r * 0.4)
                _NS_verdanix._aaline(surface, _NS_verdanix.PALETTE["green_bright"],
                                     (start_x, start_y), (end_x, end_y), 2)
                _NS_verdanix._aaline(surface, _NS_verdanix.PALETTE["green_shine"],
                                     (start_x, start_y), (end_x, end_y), 1)
            # Multi-hit visual FX - random slash sparks
            for i in range(4):
                if math.sin(phase * 12 + i * 3) > 0.5:
                    slash_angle = i * math.pi / 2 + phase
                    sx = x + int(math.cos(slash_angle) * 30)
                    sy = y + int(math.sin(slash_angle) * 20)
                    pygame.draw.rect(surface, _NS_verdanix.PALETTE["green_shine"],
                                     (sx, sy, 3, 3))
                    pygame.draw.rect(surface, _NS_verdanix.PALETTE["white"],
                                     (sx, sy, 1, 1))
        else:
            # Cyclone dissipating
            t = (progress - 0.85) / 0.15
            for i in range(10):
                fade_angle = phase * 4 + i * math.pi / 5
                r = 35 + int(t * 20)
                sx = x + int(math.cos(fade_angle) * r)
                sy = y + int(math.sin(fade_angle) * r * 0.4) - int(t * 20)
                alpha = _NS_verdanix._alpha(220 * (1 - t))
                _NS_verdanix._aacircle(surface,
                                       (*_NS_verdanix.PALETTE["green_mid"], alpha),
                                       (sx, sy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_verdanix.PALETTE["green_bright"], alpha),
                                 (sx, sy, 1, 1))
    # ============================================================
    # SKILL R - GATE OF FURY (open inner gates)
    # ============================================================
    def _draw_gate_ground(surface, boss, x, y, timer, phase):
        """Ground crack + red/green glow."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.1:
            # Ground shattered by power release
            r = int(50 * min(1.0, (progress - 0.1) * 3))
            if r > 3:
                # Red-green outer ring
                pygame.draw.ellipse(surface,
                                    (*_NS_verdanix.PALETTE["fury_darkest"], 220),
                                    (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 3)
                pygame.draw.ellipse(surface,
                                    (*_NS_verdanix.PALETTE["fury_dark"], 220),
                                    (x - r + 3, y + 40 - r // 3 + 2,
                                     r * 2 - 6, r * 2 // 3 - 4), 2)
                pygame.draw.ellipse(surface,
                                    (*_NS_verdanix.PALETTE["fury_mid"], 200),
                                    (x - r + 8, y + 40 - r // 3 + 4,
                                     r * 2 - 16, r * 2 // 3 - 8), 1)
                # Ground cracks radiating outward
                for i in range(8):
                    crack_angle = i * math.pi / 4 + phase * 0.2
                    crack_end_x = x + int(math.cos(crack_angle) * r)
                    crack_end_y = y + 40 + int(math.sin(crack_angle) * r * 0.4)
                    pygame.draw.line(surface,
                                     _NS_verdanix.PALETTE["fury_bright"],
                                     (x, y + 40), (crack_end_x, crack_end_y), 2)
                    pygame.draw.line(surface, _NS_verdanix.PALETTE["fury_shine"],
                                     (x, y + 40), (crack_end_x, crack_end_y), 1)
    def _draw_gate_skill(surface, boss, x, y, timer, phase):
        """Massive red/green power aura - gates opened."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.15:
            # Charging - green energy gathering
            t = progress / 0.15
            for r in range(int(30 * t), 0, -3):
                alpha = _NS_verdanix._alpha(200 * t)
                _NS_verdanix._aacircle(surface,
                                       (*_NS_verdanix.PALETTE["green_mid"], alpha),
                                       (x, y), r)
        elif progress < 0.85:
            # FULL POWER MODE - green AND red aura combined
            # Green outer aura
            breath = math.sin(phase * 3) * 3
            r_outer = 50 + int(breath)
            aura_surf = pygame.Surface((r_outer * 2 + 40, r_outer * 2 + 40),
                                       pygame.SRCALPHA)
            center = (r_outer + 20, r_outer + 20)
            # Green outer layers (multiple rings)
            for i in range(4):
                ring_alpha = 100 + i * 30
                _NS_verdanix._aacircle(aura_surf,
                                       (*_NS_verdanix.PALETTE["green_darkest"], ring_alpha),
                                       center, r_outer - i * 2, 3)
                _NS_verdanix._aacircle(aura_surf,
                                       (*_NS_verdanix.PALETTE["green_dark"], ring_alpha),
                                       center, r_outer - i * 2 - 1, 2)
                _NS_verdanix._aacircle(aura_surf,
                                       (*_NS_verdanix.PALETTE["green_mid"], ring_alpha),
                                       center, r_outer - i * 2 - 2, 1)
            # Red inner aura (fury layer)
            r_inner = r_outer - 10
            for i in range(3):
                _NS_verdanix._aacircle(aura_surf,
                                       (*_NS_verdanix.PALETTE["fury_dark"], 180),
                                       center, r_inner - i * 3, 3)
                _NS_verdanix._aacircle(aura_surf,
                                       (*_NS_verdanix.PALETTE["fury_mid"], 200),
                                       center, r_inner - i * 3 - 1, 2)
                _NS_verdanix._aacircle(aura_surf,
                                       (*_NS_verdanix.PALETTE["fury_bright"], 220),
                                       center, r_inner - i * 3 - 2, 1)
            # Rising flame licks (multiple pillars around body)
            for flame_i in range(12):
                flame_angle = flame_i * math.pi * 2 / 12 + phase * 0.5
                flame_base_x = center[0] + int(math.cos(flame_angle) * (r_outer - 5))
                flame_base_y = center[1] + int(math.sin(flame_angle) * (r_outer - 5))
                # Flame body (like a flame licking upward)
                flame_wave = math.sin(phase * 4 + flame_i) * 3
                flame_h = 12 + int(flame_wave)
                flame_tip_x = flame_base_x + int(math.cos(flame_angle) * flame_h)
                flame_tip_y = flame_base_y + int(math.sin(flame_angle) * flame_h)
                # Draw flame lick
                _NS_verdanix._aaline(aura_surf,
                                     (*_NS_verdanix.PALETTE["fury_dark"], 220),
                                     (flame_base_x, flame_base_y),
                                     (flame_tip_x, flame_tip_y), 4)
                _NS_verdanix._aaline(aura_surf,
                                     (*_NS_verdanix.PALETTE["fury_mid"], 240),
                                     (flame_base_x, flame_base_y),
                                     (flame_tip_x, flame_tip_y), 3)
                _NS_verdanix._aaline(aura_surf,
                                     (*_NS_verdanix.PALETTE["fury_bright"], 250),
                                     (flame_base_x, flame_base_y),
                                     (flame_tip_x, flame_tip_y), 2)
                _NS_verdanix._aaline(aura_surf,
                                     (*_NS_verdanix.PALETTE["fury_shine"], 255),
                                     (flame_base_x, flame_base_y),
                                     (flame_tip_x, flame_tip_y), 1)
                pygame.draw.rect(aura_surf, _NS_verdanix.PALETTE["white"],
                                 (flame_tip_x, flame_tip_y, 1, 1))
            # Rotating sparks
            for i in range(24):
                angle = phase * 2 + i * math.pi / 12
                sx = center[0] + int(math.cos(angle) * r_outer)
                sy = center[1] + int(math.sin(angle) * r_outer)
                color = _NS_verdanix.PALETTE["fury_shine"] if i % 2 == 0 \
                    else _NS_verdanix.PALETTE["green_shine"]
                pygame.draw.rect(aura_surf, color, (sx, sy, 2, 2))
                pygame.draw.rect(aura_surf, _NS_verdanix.PALETTE["white"],
                                 (sx, sy, 1, 1))
            surface.blit(aura_surf, (x - r_outer - 20, y - r_outer - 20))
            # Rising steam/energy particles
            for i in range(12):
                p_t = (phase + i * 0.1) % 1.0
                px = x + int(math.sin(phase * 2 + i) * 40)
                py = y - int(p_t * 60) + 10
                alpha = _NS_verdanix._alpha(220 * (1 - p_t))
                color = _NS_verdanix.PALETTE["fury_bright"] if i % 3 == 0 \
                    else _NS_verdanix.PALETTE["green_bright"]
                _NS_verdanix._aacircle(surface, (*color, alpha), (px, py), 3)
                _NS_verdanix._aacircle(surface,
                                       (*_NS_verdanix.PALETTE["fury_shine"], alpha),
                                       (px, py), 2)
                pygame.draw.rect(surface, _NS_verdanix.PALETTE["white"],
                                 (px, py, 1, 1))
            # Ground cracks with red glow
            for i in range(8):
                crack_angle = i * math.pi / 4
                crack_length = 50 + int(math.sin(phase * 2 + i) * 5)
                cx_end = x + int(math.cos(crack_angle) * crack_length)
                cy_end = y + 40 + int(math.sin(crack_angle) * crack_length * 0.3)
                pygame.draw.line(surface,
                                 _NS_verdanix.PALETTE["fury_shine"],
                                 (x, y + 40), (cx_end, cy_end), 2)
                pygame.draw.line(surface, _NS_verdanix.PALETTE["white"],
                                 (x, y + 40), (cx_end, cy_end), 1)
            # SHOUTING TEXT VISUAL - just intense glow
            # Kanji-like small mark above head (abstract power symbol)
            kanji_y = y - 55
            for r in range(6, 0, -1):
                alpha = _NS_verdanix._alpha(180 * (6 - r) / 6)
                _NS_verdanix._aacircle(surface,
                                       (*_NS_verdanix.PALETTE["fury_mid"], alpha),
                                       (x, kanji_y), r)
            # Draw abstract "power" symbol (spiral)
            for i in range(4):
                sym_angle = phase * 3 + i * math.pi / 2
                sr = 3
                s_x = x + int(math.cos(sym_angle) * sr)
                s_y = kanji_y + int(math.sin(sym_angle) * sr)
                pygame.draw.rect(surface, _NS_verdanix.PALETTE["fury_shine"],
                                 (s_x, s_y, 1, 1))
            pygame.draw.rect(surface, _NS_verdanix.PALETTE["white"],
                             (x, kanji_y, 1, 1))
        else:
            # Aftermath - fading
            t = (progress - 0.85) / 0.15
            for r in range(int(40 * (1 - t)), 5, -3):
                alpha = _NS_verdanix._alpha(180 * (1 - t))
                _NS_verdanix._aacircle(surface,
                                       (*_NS_verdanix.PALETTE["fury_mid"], alpha),
                                       (x, y), r, 2)
            # Steam rising
            for i in range(10):
                s_t = (phase * 0.8 + i * 0.1) % 1.0
                sx = x + int(math.sin(phase + i) * 20)
                sy = y - int(s_t * 40)
                alpha = _NS_verdanix._alpha(150 * (1 - t) * (1 - s_t))
                if alpha > 0:
                    _NS_verdanix._aacircle(surface,
                                           (*_NS_verdanix.PALETTE["steam_mid"], alpha),
                                           (sx, sy), 3)
                    _NS_verdanix._aacircle(surface,
                                           (*_NS_verdanix.PALETTE["steam_light"], alpha),
                                           (sx, sy), 2)



# ====================================================================
# PYRAENA (EMBERWEAVER) - TRUE BOSS
# ====================================================================

class _NS_pyraena:
    """Namespace pyraena - Emberweaver fire mage boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin tones (fair, warm)
        "skin_shadow": (180, 140, 115),
        "skin_dark": (225, 185, 155),
        "skin_mid": (245, 210, 180),
        "skin_light": (255, 230, 205),
        "skin_shine": (255, 245, 225),
        # Fiery orange/red hair
        "hair_darkest": (85, 20, 10),
        "hair_dark": (160, 45, 20),
        "hair_mid": (230, 100, 30),
        "hair_light": (255, 165, 60),
        "hair_shine": (255, 220, 130),
        # Red dress (main outfit - deep crimson/wine)
        "dress_darkest": (35, 8, 15),
        "dress_dark": (85, 20, 30),
        "dress_mid": (145, 35, 50),
        "dress_light": (200, 60, 80),
        "dress_shine": (240, 120, 130),
        # Gold trim on dress
        "gold_dark": (95, 65, 15),
        "gold_mid": (200, 155, 45),
        "gold_light": (250, 215, 110),
        "gold_shine": (255, 245, 190),
        # Boots (dark red/brown)
        "boot_dark": (40, 15, 15),
        "boot_mid": (85, 35, 30),
        "boot_light": (140, 65, 55),
        # Fire (main theme - orange/red/yellow)
        "fire_darkest": (60, 10, 5),
        "fire_dark": (150, 30, 15),
        "fire_mid": (240, 90, 25),
        "fire_hot": (255, 165, 45),
        "fire_bright": (255, 220, 100),
        "fire_shine": (255, 250, 200),
        # Ember (glowing embers/coals)
        "ember_dark": (100, 25, 10),
        "ember_mid": (200, 60, 20),
        "ember_light": (255, 130, 45),
        # Smoke (dark grey)
        "smoke_dark": (30, 20, 15),
        "smoke_mid": (70, 55, 45),
        "smoke_light": (130, 110, 95),
        # Green eyes (fair skin with green eyes)
        "eye_dark": (15, 55, 25),
        "eye_mid": (60, 155, 75),
        "eye_light": (140, 220, 155),
        "eye_shine": (220, 250, 225),
        # Lips (red)
        "lip_dark": (100, 20, 30),
        "lip_mid": (180, 50, 60),
        "lip_light": (230, 100, 110),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_pyraena._clamp(color)
        if _NS_pyraena.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_pyraena._clamp(color)
        if _NS_pyraena.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_pyraena._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_pyraena(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_pyraena._detect_moving(boss)
        _NS_pyraena._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_pye_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind
        _NS_pyraena._draw_fire_aura(surface, x, y, pulse)
        _NS_pyraena._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "w":
            _NS_pyraena._draw_ember_spears_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_pyraena._draw_plasma_lance_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating bob
        float_bob = int(math.sin(pulse * 0.6) * 3)
        # Body (always floating)
        if attacking:
            _NS_pyraena._draw_body_attack(surface, boss, x, y + float_bob)
        elif moving:
            _NS_pyraena._draw_body_walk(surface, boss, x, y + float_bob)
        else:
            _NS_pyraena._draw_body_idle(surface, boss, x, y + float_bob)
        # R - Fiery Soul orbs (over body)
        if active_skill == "r":
            _NS_pyraena._draw_ember_soul_orbs(surface, boss, x, y + float_bob,
                                              skill_timer, pulse)
        # Foreground FX
        if active_skill == "q":
            _NS_pyraena._draw_dragon_breath_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_pyraena._draw_ember_spears_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_pyraena._draw_plasma_lance_skill(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_pye_previous_timer", 0))
        active = bool(getattr(boss, "_pye_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._pye_attack_active = True
            boss._pye_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._pye_attack_frame = int(getattr(boss, "_pye_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._pye_attack_active = False
            boss._pye_attack_frame = 0
            active = False
        boss._pye_previous_timer = timer
        boss._pye_attack_progress = (
            min(1.0, getattr(boss, "_pye_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_pye_last_x"):
            boss._pye_last_x = boss.x
            boss._pye_last_y = boss.y
            return False
        dx = abs(boss.x - boss._pye_last_x)
        dy = abs(boss.y - boss._pye_last_y)
        boss._pye_last_x = boss.x
        boss._pye_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        _NS_pyraena._draw_shadow(surface, x, y + 50)
        _NS_pyraena._draw_fire_mist(surface, x, y + 44, boss.pulse)
        _NS_pyraena._draw_body(surface, x, y, boss.direction, boss.pulse, "idle")
    def _draw_body_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_pyraena._draw_shadow(surface, x + sway, y + 50)
        _NS_pyraena._draw_fire_mist(surface, x + sway, y + 44, phase, trail=True,
                                    facing=boss.direction)
        _NS_pyraena._draw_body(surface, x + sway, y, boss.direction, phase, "walk")
    def _draw_body_attack(surface, boss, x, y):
        progress = getattr(boss, "_pye_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Cast motion (extends both hands forward - fire caster)
        if progress < 0.4:
            t = progress / 0.4
            lunge = -int(t * 3) * boss.direction
        elif progress < 0.65:
            t = (progress - 0.4) / 0.25
            lunge = int((-3 + t * 10)) * boss.direction
        else:
            t = (progress - 0.65) / 0.35
            lunge = int(7 * (1 - t)) * boss.direction
        _NS_pyraena._draw_shadow(surface, x + lunge, y + 50)
        _NS_pyraena._draw_fire_mist(surface, x + lunge, y + 44, boss.pulse, intense=True)
        _NS_pyraena._draw_body(surface, x + lunge, y, boss.direction, boss.pulse,
                               "attack", progress)
        _NS_pyraena._draw_basic_fire_projectile(surface, boss, x + lunge, y, progress)
    # ============================================================
    # BODY DRAWING
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw fire mage: red dress with gold trim, long orange hair, boots."""
        arm_swing = 0
        if action == "attack":
            if attack_progress < 0.4:
                arm_swing = -int(attack_progress / 0.4 * 8) * facing
            elif attack_progress < 0.65:
                t = (attack_progress - 0.4) / 0.25
                arm_swing = int((-8 + t * 24)) * facing
            else:
                t = (attack_progress - 0.65) / 0.35
                arm_swing = int(16 * (1 - t)) * facing
        # Both arms extended for casting (idle: arms slightly out with flames)
        # Order: back arm → dress/body → boots → front arm → head
        # Back arm
        _NS_pyraena._draw_arm(surface, cx - facing * 8, cy - 3, facing, phase,
                              -arm_swing // 2, back=True, action=action,
                              attack_progress=attack_progress)
        # Dress + body
        _NS_pyraena._draw_dress(surface, cx, cy, facing, phase, action)
        # Boots (partially visible under dress)
        _NS_pyraena._draw_boots(surface, cx, cy, facing, phase)
        # Front arm (casting fire)
        _NS_pyraena._draw_arm(surface, cx + facing * 6, cy - 3, facing, phase,
                              arm_swing, back=False, action=action,
                              attack_progress=attack_progress)
        # Head
        _NS_pyraena._draw_head(surface, cx, cy - 22, facing, phase, action)
    def _draw_dress(surface, cx, cy, facing, phase, action):
        """Red dress with gold trim, wide skirt."""
        sway = math.sin(phase * 0.7) * 2
        # Bodice (upper corset - tight)
        bodice_shape = [
            (cx - 10, cy - 8),      # left shoulder
            (cx - 11, cy - 2),      # under left arm
            (cx - 10, cy + 4),      # waist left
            (cx - 8, cy + 10),      # tapered waist
            (cx + 8, cy + 10),
            (cx + 10, cy + 4),
            (cx + 11, cy - 2),
            (cx + 10, cy - 8),
        ]
        # Shadow
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["shadow_deep"],
                          [(px + 2, py + 3) for px, py in bodice_shape])
        # Base darkest
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["dress_darkest"], bodice_shape)
        # Mid tone
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["dress_dark"], [
            (cx - 9, cy - 7),
            (cx - 10, cy - 1),
            (cx - 9, cy + 4),
            (cx - 7, cy + 9),
            (cx + 7, cy + 9),
            (cx + 9, cy + 4),
            (cx + 10, cy - 1),
            (cx + 9, cy - 7),
        ])
        # Highlight (chest area)
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["dress_mid"], [
            (cx - 7, cy - 5),
            (cx - 8, cy),
            (cx - 6, cy + 6),
            (cx + 6, cy + 6),
            (cx + 8, cy),
            (cx + 7, cy - 5),
        ])
        # Bright fabric shine
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["dress_light"], [
            (cx - 4, cy - 4),
            (cx - 5, cy + 2),
            (cx - 3, cy + 6),
            (cx + 3, cy + 6),
            (cx + 5, cy + 2),
            (cx + 4, cy - 4),
        ])
        pygame.draw.line(surface, _NS_pyraena.PALETTE["dress_shine"],
                         (cx - 2, cy - 2), (cx - 2, cy + 4), 1)
        # CLEAVAGE V-neck (skin shows through)
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["skin_shadow"], [
            (cx - 4, cy - 8),
            (cx - 3, cy - 5),
            (cx, cy - 1),
            (cx + 3, cy - 5),
            (cx + 4, cy - 8),
        ])
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["skin_dark"], [
            (cx - 3, cy - 7),
            (cx - 2, cy - 4),
            (cx, cy - 1),
            (cx + 2, cy - 4),
            (cx + 3, cy - 7),
        ])
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["skin_mid"],
                         (cx - 1, cy - 6, 2, 3))
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["skin_light"],
                         (cx - 1, cy - 5, 1, 1))
        # GOLD TRIM around V-neck and edges
        pygame.draw.line(surface, _NS_pyraena.PALETTE["gold_dark"],
                         (cx - 4, cy - 8), (cx, cy - 1), 1)
        pygame.draw.line(surface, _NS_pyraena.PALETTE["gold_mid"],
                         (cx - 3, cy - 8), (cx, cy - 2), 1)
        pygame.draw.line(surface, _NS_pyraena.PALETTE["gold_dark"],
                         (cx + 4, cy - 8), (cx, cy - 1), 1)
        pygame.draw.line(surface, _NS_pyraena.PALETTE["gold_mid"],
                         (cx + 3, cy - 8), (cx, cy - 2), 1)
        # Central gem/gold pendant on chest
        _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["gold_dark"],
                              (cx, cy + 2), 3)
        _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_dark"],
                              (cx, cy + 2), 2)
        _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_hot"],
                              (cx, cy + 2), 1)
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["fire_shine"],
                         (cx, cy + 2, 1, 1))
        # WAIST/BELT area (gold band)
        pygame.draw.line(surface, _NS_pyraena.PALETTE["gold_dark"],
                         (cx - 8, cy + 10), (cx + 8, cy + 10), 1)
        pygame.draw.line(surface, _NS_pyraena.PALETTE["gold_mid"],
                         (cx - 7, cy + 11), (cx + 7, cy + 11), 1)
        pygame.draw.line(surface, _NS_pyraena.PALETTE["gold_light"],
                         (cx - 5, cy + 11), (cx + 5, cy + 11), 1)
        # Central belt gem (diamond)
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["gold_dark"], [
            (cx, cy + 9), (cx + 2, cy + 11), (cx, cy + 13), (cx - 2, cy + 11),
        ])
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["fire_hot"], [
            (cx, cy + 10), (cx + 1, cy + 11), (cx, cy + 12), (cx - 1, cy + 11),
        ])
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["fire_shine"],
                         (cx, cy + 11, 1, 1))
        # SKIRT (wide, flowing, with gold trim)
        skirt_shape = [
            (cx - 8, cy + 10),
            (cx - 12, cy + 18),
            (cx - 16, cy + 26),
            (cx - 15 + int(sway), cy + 34),
            (cx - 5, cy + 38),
            (cx + 5, cy + 38),
            (cx + 15 + int(sway), cy + 34),
            (cx + 16, cy + 26),
            (cx + 12, cy + 18),
            (cx + 8, cy + 10),
        ]
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["shadow_deep"],
                          [(px + 2, py + 3) for px, py in skirt_shape])
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["dress_darkest"], skirt_shape)
        # Skirt mid tone
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["dress_dark"], [
            (cx - 7, cy + 11),
            (cx - 11, cy + 18),
            (cx - 15, cy + 26),
            (cx - 13, cy + 33),
            (cx - 4, cy + 37),
            (cx + 4, cy + 37),
            (cx + 13, cy + 33),
            (cx + 15, cy + 26),
            (cx + 11, cy + 18),
            (cx + 7, cy + 11),
        ])
        # Skirt highlight
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["dress_mid"], [
            (cx - 6, cy + 13),
            (cx - 9, cy + 20),
            (cx - 12, cy + 28),
            (cx - 10, cy + 33),
            (cx - 3, cy + 35),
            (cx + 3, cy + 35),
            (cx + 10, cy + 33),
            (cx + 12, cy + 28),
            (cx + 9, cy + 20),
            (cx + 6, cy + 13),
        ])
        # Skirt fold highlights (vertical streaks)
        pygame.draw.line(surface, _NS_pyraena.PALETTE["dress_light"],
                         (cx - 8, cy + 15), (cx - 12, cy + 32), 1)
        pygame.draw.line(surface, _NS_pyraena.PALETTE["dress_light"],
                         (cx + 8, cy + 15), (cx + 12, cy + 32), 1)
        pygame.draw.line(surface, _NS_pyraena.PALETTE["dress_light"],
                         (cx, cy + 16), (cx, cy + 36), 1)
        pygame.draw.line(surface, _NS_pyraena.PALETTE["dress_shine"],
                         (cx - 4, cy + 20), (cx - 4, cy + 34), 1)
        pygame.draw.line(surface, _NS_pyraena.PALETTE["dress_shine"],
                         (cx + 4, cy + 20), (cx + 4, cy + 34), 1)
        # GOLD TRIM at bottom hem
        pygame.draw.line(surface, _NS_pyraena.PALETTE["gold_dark"],
                         (cx - 15, cy + 34), (cx + 15, cy + 34), 2)
        pygame.draw.line(surface, _NS_pyraena.PALETTE["gold_mid"],
                         (cx - 14, cy + 34), (cx + 14, cy + 34), 1)
        pygame.draw.line(surface, _NS_pyraena.PALETTE["gold_light"],
                         (cx - 10, cy + 34), (cx + 10, cy + 34), 1)
        # Small gold decorations at hem
        for x_off in (-12, -6, 0, 6, 12):
            gx = cx + x_off
            _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["gold_dark"],
                                  (gx, cy + 36), 2)
            _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["gold_mid"],
                                  (gx, cy + 36), 1)
            pygame.draw.rect(surface, _NS_pyraena.PALETTE["gold_shine"],
                             (gx, cy + 36, 1, 1))
        # CENTER SKIRT SLIT (showing leg + boot underneath)
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["dress_darkest"], [
            (cx - 2, cy + 12),
            (cx - 3, cy + 26),
            (cx - 2, cy + 34),
            (cx + 2, cy + 34),
            (cx + 3, cy + 26),
            (cx + 2, cy + 12),
        ])
    def _draw_boots(surface, cx, cy, facing, phase):
        """Red boots visible below dress."""
        # Left boot
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["shadow_deep"], [
            (cx - 9, cy + 34),
            (cx - 10, cy + 40),
            (cx - 4, cy + 40),
            (cx - 3, cy + 34),
        ])
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["boot_dark"], [
            (cx - 8, cy + 34),
            (cx - 9, cy + 39),
            (cx - 4, cy + 39),
            (cx - 3, cy + 34),
        ])
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["boot_mid"], [
            (cx - 7, cy + 35),
            (cx - 8, cy + 38),
            (cx - 5, cy + 38),
            (cx - 4, cy + 35),
        ])
        pygame.draw.line(surface, _NS_pyraena.PALETTE["boot_light"],
                         (cx - 6, cy + 36), (cx - 6, cy + 37), 1)
        # Right boot
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["shadow_deep"], [
            (cx + 3, cy + 34),
            (cx + 4, cy + 40),
            (cx + 10, cy + 40),
            (cx + 9, cy + 34),
        ])
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["boot_dark"], [
            (cx + 3, cy + 34),
            (cx + 4, cy + 39),
            (cx + 9, cy + 39),
            (cx + 8, cy + 34),
        ])
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["boot_mid"], [
            (cx + 4, cy + 35),
            (cx + 5, cy + 38),
            (cx + 8, cy + 38),
            (cx + 7, cy + 35),
        ])
        pygame.draw.line(surface, _NS_pyraena.PALETTE["boot_light"],
                         (cx + 6, cy + 36), (cx + 6, cy + 37), 1)
        # Gold trim on boots
        pygame.draw.line(surface, _NS_pyraena.PALETTE["gold_mid"],
                         (cx - 8, cy + 34), (cx - 3, cy + 34), 1)
        pygame.draw.line(surface, _NS_pyraena.PALETTE["gold_mid"],
                         (cx + 3, cy + 34), (cx + 8, cy + 34), 1)
    def _draw_arm(surface, cx, cy, facing, phase, swing, back=False,
                  action="idle", attack_progress=0):
        """Feminine arm with flame in palm."""
        # Both arms slightly out at idle (mage stance)
        idle_offset = math.radians(20 if not back else -20)
        base_angle = math.pi * 0.4 + math.radians(swing) + idle_offset
        if back:
            base_angle = math.pi * 0.4 - idle_offset
        shoulder_x = cx
        shoulder_y = cy
        elbow_len = 10
        elbow_x = shoulder_x + int(math.cos(base_angle) * elbow_len * facing * 0.5)
        elbow_y = shoulder_y + int(math.sin(base_angle) * elbow_len)
        hand_len = 12
        hand_angle = base_angle - math.radians(swing * 0.6)
        hand_x = elbow_x + int(math.cos(hand_angle) * hand_len * facing * 0.7)
        hand_y = elbow_y + int(math.sin(hand_angle) * hand_len)
        # If attacking, extend both hands forward
        if action == "attack" and attack_progress > 0.4:
            if not back:
                hand_x = cx + facing * (14 + int(attack_progress * 10))
                hand_y = cy - 2 - int(math.sin(attack_progress * math.pi) * 4)
            else:
                hand_x = cx + facing * (8 + int(attack_progress * 8))
                hand_y = cy + int(math.sin(attack_progress * math.pi) * 3)
        thickness = 5
        # Shadow
        _NS_pyraena._aaline(surface, _NS_pyraena.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 2),
                            (elbow_x + 1, elbow_y + 2), thickness + 1)
        # Upper arm (dress sleeve - red with gold cuff at shoulder)
        color_main = _NS_pyraena.PALETTE["dress_darkest"] if back \
            else _NS_pyraena.PALETTE["dress_dark"]
        color_mid = _NS_pyraena.PALETTE["dress_dark"] if back \
            else _NS_pyraena.PALETTE["dress_mid"]
        # Sleeve (short, only near shoulder)
        _NS_pyraena._aaline(surface, color_main,
                            (shoulder_x, shoulder_y),
                            (shoulder_x + int(math.cos(base_angle) * 4 * facing * 0.5),
                             shoulder_y + int(math.sin(base_angle) * 4)), thickness)
        _NS_pyraena._aaline(surface, color_mid,
                            (shoulder_x, shoulder_y - 1),
                            (shoulder_x + int(math.cos(base_angle) * 4 * facing * 0.5),
                             shoulder_y + int(math.sin(base_angle) * 4) - 1),
                            max(1, thickness - 2))
        # Gold shoulder detail
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["gold_dark"],
                         (shoulder_x - 2, shoulder_y - 2, 4, 2))
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["gold_mid"],
                         (shoulder_x - 2, shoulder_y - 2, 4, 1))
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["gold_shine"],
                         (shoulder_x - 1, shoulder_y - 2, 2, 1))
        # Rest of arm is bare skin
        skin_color = _NS_pyraena.PALETTE["skin_shadow"] if back \
            else _NS_pyraena.PALETTE["skin_dark"]
        skin_mid = _NS_pyraena.PALETTE["skin_dark"] if back \
            else _NS_pyraena.PALETTE["skin_mid"]
        # Upper arm skin
        _NS_pyraena._aaline(surface, skin_color,
                            (shoulder_x + int(math.cos(base_angle) * 4 * facing * 0.5),
                             shoulder_y + int(math.sin(base_angle) * 4)),
                            (elbow_x, elbow_y), thickness - 1)
        _NS_pyraena._aaline(surface, skin_mid,
                            (shoulder_x + int(math.cos(base_angle) * 4 * facing * 0.5),
                             shoulder_y + int(math.sin(base_angle) * 4) - 1),
                            (elbow_x, elbow_y - 1), max(1, thickness - 3))
        # Forearm
        _NS_pyraena._aaline(surface, _NS_pyraena.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 2),
                            (hand_x + 1, hand_y + 2), thickness)
        _NS_pyraena._aaline(surface, skin_color,
                            (elbow_x, elbow_y),
                            (hand_x, hand_y), thickness - 1)
        _NS_pyraena._aaline(surface, skin_mid,
                            (elbow_x, elbow_y - 1),
                            (hand_x, hand_y - 1), max(1, thickness - 3))
        # Hand
        _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["shadow_deep"],
                              (hand_x + 1, hand_y + 1), 3)
        _NS_pyraena._aacircle(surface, skin_color, (hand_x, hand_y), 3)
        _NS_pyraena._aacircle(surface, skin_mid, (hand_x, hand_y), 2)
        if not back:
            _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["skin_light"],
                                  (hand_x - 1, hand_y - 1), 1)
        # FLAME IN PALM (both hands always show small flame at idle!)
        flame_intensity = 1.5 if action == "attack" else 1.0
        _NS_pyraena._draw_hand_flame(surface, hand_x, hand_y, phase, flame_intensity,
                                     back=back)
    def _draw_hand_flame(surface, hand_x, hand_y, phase, intensity, back=False):
        """Small persistent flame flickering above hand."""
        pulse = math.sin(phase * 3) * 0.3 + 0.7 * intensity
        flame_size = int(4 * intensity * pulse)
        # Flame position (just above palm)
        fx = hand_x
        fy = hand_y - 3
        # Flame body (teardrop shape)
        # Base darkest
        for r in range(flame_size + 3, 0, -1):
            alpha = _NS_pyraena._alpha(200 * (flame_size + 3 - r) / (flame_size + 3))
            _NS_pyraena._aacircle(surface, (*_NS_pyraena.PALETTE["fire_darkest"], alpha),
                                  (fx, fy), r)
        # Fire base (dark red)
        _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_dark"],
                              (fx, fy + 1), flame_size)
        _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_mid"],
                              (fx, fy), flame_size - 1)
        _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_hot"],
                              (fx, fy - 1), max(1, flame_size - 2))
        _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_bright"],
                              (fx, fy - 2), max(1, flame_size - 3))
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["fire_shine"],
                         (fx, fy - 3, 1, 1))
        # Rising sparks
        for i in range(3):
            spark_t = (phase * 2 + i * 0.33) % 1.0
            sx = fx + int(math.sin(phase * 3 + i) * 3)
            sy = fy - int(spark_t * 8) - 2
            alpha = _NS_pyraena._alpha(220 * (1 - spark_t))
            pygame.draw.rect(surface, (*_NS_pyraena.PALETTE["fire_hot"], alpha),
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface, (*_NS_pyraena.PALETTE["fire_bright"], alpha),
                             (sx, sy - 1, 1, 1))
    def _draw_head(surface, cx, cy, facing, phase, action):
        """Feminine head with fair skin, green eyes, red lips."""
        # Face shape (slightly softer/rounder for feminine)
        face_shape = [
            (cx - 6, cy - 2),
            (cx - 7, cy - 6),
            (cx - 5, cy - 10),
            (cx - 2, cy - 12),
            (cx + 2, cy - 12),
            (cx + 5, cy - 10),
            (cx + 7, cy - 6),
            (cx + 6, cy - 2),
            (cx + 4, cy + 3),
            (cx + 1, cy + 5),
            (cx - 3, cy + 5),
            (cx - 5, cy + 3),
        ]
        # Shadow
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["shadow_deep"],
                          [(px + 1, py + 2) for px, py in face_shape])
        # Base skin
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["skin_shadow"], face_shape)
        # Main face
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["skin_dark"], [
            (cx - 5, cy - 3),
            (cx - 6, cy - 6),
            (cx - 4, cy - 9),
            (cx - 2, cy - 11),
            (cx + 2, cy - 11),
            (cx + 4, cy - 9),
            (cx + 6, cy - 6),
            (cx + 5, cy - 3),
            (cx + 3, cy + 2),
            (cx, cy + 4),
            (cx - 3, cy + 2),
        ])
        # Light mid
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["skin_mid"], [
            (cx - 4, cy - 4),
            (cx - 5, cy - 7),
            (cx - 3, cy - 9),
            (cx + 3, cy - 9),
            (cx + 5, cy - 7),
            (cx + 4, cy - 4),
            (cx + 2, cy),
            (cx - 2, cy),
        ])
        # Cheek blush highlights (feminine)
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["skin_light"],
                         (cx - 3 * facing, cy - 3, 2, 2))
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["skin_shine"],
                         (cx - 3 * facing, cy - 3, 1, 1))
        # Blush on both cheeks (pink tint)
        pygame.draw.rect(surface, (245, 180, 160),
                         (cx - 4, cy - 1, 1, 1))
        pygame.draw.rect(surface, (245, 180, 160),
                         (cx + 4, cy - 1, 1, 1))
        # GREEN EYES with long lashes
        _NS_pyraena._draw_feminine_eye(surface, cx - 3, cy - 5, facing, phase, action)
        _NS_pyraena._draw_feminine_eye(surface, cx + 3, cy - 5, facing, phase, action)
        # Eyebrows (thin, arched)
        pygame.draw.line(surface, _NS_pyraena.PALETTE["hair_dark"],
                         (cx - 4, cy - 8), (cx - 2, cy - 7), 1)
        pygame.draw.line(surface, _NS_pyraena.PALETTE["hair_dark"],
                         (cx + 2, cy - 7), (cx + 4, cy - 8), 1)
        # RED LIPS (feminine touch)
        pygame.draw.line(surface, _NS_pyraena.PALETTE["lip_dark"],
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)
        pygame.draw.line(surface, _NS_pyraena.PALETTE["lip_mid"],
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["lip_light"],
                         (cx, cy + 2, 1, 1))
        if action == "attack":
            # Slight open mouth (casting)
            pygame.draw.rect(surface, _NS_pyraena.PALETTE["shadow_deep"],
                             (cx - 1, cy + 2, 2, 1))
        # FLAMING RED-ORANGE HAIR (long, flowing)
        _NS_pyraena._draw_hair(surface, cx, cy, facing, phase)
    def _draw_feminine_eye(surface, cx, cy, facing, phase, action):
        """Green eye with lashes and eye shadow."""
        # Eye shadow (dark eye lining)
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["shadow_deep"],
                         (cx - 1, cy - 1, 3, 1))
        # Sclera
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["white"],
                         (cx - 1, cy, 3, 1))
        # Green iris
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["eye_dark"],
                         (cx, cy, 2, 1))
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["eye_mid"],
                         (cx + facing, cy, 1, 1))
        # Highlight
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["eye_shine"],
                         (cx, cy, 1, 1))
        # Long lashes (single pixel above)
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["shadow_deep"],
                         (cx - 1, cy - 2, 1, 1))
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["shadow_deep"],
                         (cx + 2, cy - 2, 1, 1))
        if action == "attack":
            # Intense glow
            for r in range(4, 0, -1):
                alpha = _NS_pyraena._alpha(100 * (4 - r) / 4)
                _NS_pyraena._aacircle(surface,
                                      (*_NS_pyraena.PALETTE["eye_light"], alpha),
                                      (cx, cy), r)
    def _draw_hair(surface, cx, cy, facing, phase):
        """Long flowing fiery orange/red hair with animation."""
        cy_h = cy - 22  # hair top position
        # Hair sways with movement
        sway1 = math.sin(phase * 0.6) * 2
        sway2 = math.sin(phase * 0.6 + math.pi / 3) * 3
        sway3 = math.sin(phase * 0.6 + math.pi * 2 / 3) * 2
        # BACK HAIR (long, flowing behind body - large mass)
        # This creates the long-hair silhouette behind the shoulders
        back_hair_shape = [
            (cx - 10, cy_h - 8),
            (cx - 12, cy_h - 4),
            (cx - 14, cy_h + 4),
            (cx - 16 + int(sway1), cy_h + 14),
            (cx - 17 + int(sway1), cy_h + 22),
            (cx - 15 + int(sway1), cy_h + 30),
            (cx - 10 + int(sway1), cy_h + 34),
            (cx - 5, cy_h + 32),
            # Right side mirror
            (cx + 5, cy_h + 32),
            (cx + 10 + int(sway2), cy_h + 34),
            (cx + 15 + int(sway2), cy_h + 30),
            (cx + 17 + int(sway2), cy_h + 22),
            (cx + 16 + int(sway2), cy_h + 14),
            (cx + 14, cy_h + 4),
            (cx + 12, cy_h - 4),
            (cx + 10, cy_h - 8),
            (cx + 3, cy_h - 15),
            (cx - 3, cy_h - 15),
        ]
        # Shadow
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["shadow_deep"],
                          [(px + 2, py + 3) for px, py in back_hair_shape])
        # Darkest hair (base layer)
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["hair_darkest"], back_hair_shape)
        # Mid dark red hair
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["hair_dark"], [
            (cx - 9, cy_h - 7),
            (cx - 11, cy_h - 3),
            (cx - 13, cy_h + 4),
            (cx - 15 + int(sway1), cy_h + 14),
            (cx - 16 + int(sway1), cy_h + 20),
            (cx - 14 + int(sway1), cy_h + 28),
            (cx - 9, cy_h + 31),
            (cx + 9, cy_h + 31),
            (cx + 14 + int(sway2), cy_h + 28),
            (cx + 16 + int(sway2), cy_h + 20),
            (cx + 15 + int(sway2), cy_h + 14),
            (cx + 13, cy_h + 4),
            (cx + 11, cy_h - 3),
            (cx + 9, cy_h - 7),
            (cx + 2, cy_h - 14),
            (cx - 2, cy_h - 14),
        ])
        # Bright orange highlight (main hair color)
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["hair_mid"], [
            (cx - 7, cy_h - 5),
            (cx - 9, cy_h),
            (cx - 11, cy_h + 6),
            (cx - 13 + int(sway1), cy_h + 15),
            (cx - 11 + int(sway1), cy_h + 25),
            (cx - 6, cy_h + 28),
            (cx + 6, cy_h + 28),
            (cx + 11 + int(sway2), cy_h + 25),
            (cx + 13 + int(sway2), cy_h + 15),
            (cx + 11, cy_h + 6),
            (cx + 9, cy_h),
            (cx + 7, cy_h - 5),
        ])
        # Bright fire-orange streaks (highlights - vertical)
        for x_off in (-9, -5, 0, 5, 9):
            streak_x = cx + x_off
            _NS_pyraena._aaline(surface, _NS_pyraena.PALETTE["hair_light"],
                                (streak_x, cy_h - 3),
                                (streak_x + int(sway1 * x_off / 10), cy_h + 24), 1)
        # Bright yellow shine strands
        _NS_pyraena._aaline(surface, _NS_pyraena.PALETTE["hair_shine"],
                            (cx - 2, cy_h - 2), (cx - 2, cy_h + 14), 1)
        _NS_pyraena._aaline(surface, _NS_pyraena.PALETTE["hair_shine"],
                            (cx + 2, cy_h - 2), (cx + 2, cy_h + 14), 1)
        # BANGS on forehead (parted, flowing to sides)
        # Left bang sweep
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["hair_darkest"], [
            (cx - 6, cy_h - 5),
            (cx - 7, cy_h - 2),
            (cx - 5, cy_h),
            (cx - 3, cy_h - 3),
            (cx - 2, cy_h - 6),
        ])
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["hair_dark"], [
            (cx - 5, cy_h - 5),
            (cx - 6, cy_h - 2),
            (cx - 4, cy_h - 1),
            (cx - 3, cy_h - 3),
            (cx - 2, cy_h - 5),
        ])
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["hair_mid"], [
            (cx - 4, cy_h - 4),
            (cx - 5, cy_h - 2),
            (cx - 3, cy_h - 2),
            (cx - 2, cy_h - 4),
        ])
        # Right bang sweep
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["hair_darkest"], [
            (cx + 2, cy_h - 6),
            (cx + 3, cy_h - 3),
            (cx + 5, cy_h),
            (cx + 7, cy_h - 2),
            (cx + 6, cy_h - 5),
        ])
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["hair_dark"], [
            (cx + 2, cy_h - 5),
            (cx + 3, cy_h - 3),
            (cx + 4, cy_h - 1),
            (cx + 6, cy_h - 2),
            (cx + 5, cy_h - 5),
        ])
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["hair_mid"], [
            (cx + 2, cy_h - 4),
            (cx + 3, cy_h - 2),
            (cx + 5, cy_h - 2),
            (cx + 4, cy_h - 4),
        ])
        # Top of head highlight (bright center part line)
        pygame.draw.line(surface, _NS_pyraena.PALETTE["hair_light"],
                         (cx, cy_h - 15), (cx, cy_h - 8), 1)
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["hair_shine"],
                         (cx, cy_h - 13, 1, 2))
        # Flame-like hair tips at ends (fiery ember tips)
        for i, (dx, dy) in enumerate([(-15 + int(sway1), 30), (-8, 32),
                                        (8, 32), (15 + int(sway2), 30)]):
            tip_x = cx + dx
            tip_y = cy_h + dy
            # Small ember at hair tip
            _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_dark"],
                                  (tip_x, tip_y), 2)
            _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_hot"],
                                  (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_pyraena.PALETTE["fire_bright"],
                             (tip_x, tip_y, 1, 1))
    # ============================================================
    # BASIC RANGED - Small fireball
    # ============================================================
    def _draw_basic_fire_projectile(surface, boss, x, y, progress):
        """Small fireball projectile."""
        if progress < 0.5:
            return
        facing = boss.direction
        tx, ty = _NS_pyraena._target_position(boss, x, y)
        start_x = x + facing * 24
        start_y = y - 4
        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Fire trail
        for i in range(8):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_pyraena._alpha(220 - i * 25)
            size = max(1, 5 - i)
            _NS_pyraena._aacircle(surface, (*_NS_pyraena.PALETTE["fire_dark"], alpha),
                                  (px, py), size)
            _NS_pyraena._aacircle(surface, (*_NS_pyraena.PALETTE["fire_mid"], alpha),
                                  (px, py), max(1, size - 1))
            _NS_pyraena._aacircle(surface, (*_NS_pyraena.PALETTE["fire_hot"], alpha),
                                  (px, py), max(1, size - 2))
            # Sparks
            if i < 4:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 8 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 8 + i + s) * (size + 1))
                    pygame.draw.rect(surface, (*_NS_pyraena.PALETTE["fire_bright"], alpha),
                                     (spark_x, spark_y, 1, 1))
        # Main fireball head
        _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_darkest"], (bx, by), 6)
        _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_dark"], (bx, by), 5)
        _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_mid"], (bx, by), 4)
        _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_hot"], (bx, by), 3)
        _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_bright"], (bx, by), 2)
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["fire_shine"], (bx, by, 1, 1))
        # Impact
        if t > 0.9:
            st = (t - 0.9) / 0.1
            radius = int(10 + st * 18)
            alpha = _NS_pyraena._alpha(240 * (1 - st))
            _NS_pyraena._aacircle(surface, (*_NS_pyraena.PALETTE["fire_darkest"], alpha),
                                  (tx, ty), radius + 3, 3)
            _NS_pyraena._aacircle(surface, (*_NS_pyraena.PALETTE["fire_dark"], alpha),
                                  (tx, ty), radius, 2)
            _NS_pyraena._aacircle(surface, (*_NS_pyraena.PALETTE["fire_hot"], alpha),
                                  (tx, ty), max(1, radius - 5), 1)
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_pyraena.PALETTE["fire_bright"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # FLOATING FIRE MIST
    # ============================================================
    def _draw_fire_mist(surface, cx, cy, phase, trail=False, facing=1,
                        intense=False):
        """Fire mist below body (she's floating on flames)."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((140, 45), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        # Base dark fire glow
        for radius in range(32, 3, -3):
            alpha = _NS_pyraena._alpha((32 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_pyraena.PALETTE["fire_darkest"], alpha),
                    (70 - radius, 22 - radius // 3,
                     radius * 2, max(2, radius // 2))
                )
        for radius in range(22, 3, -2):
            alpha = _NS_pyraena._alpha((22 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_pyraena.PALETTE["fire_dark"], alpha),
                    (70 - radius, 22 - radius // 4,
                     radius * 2, max(2, radius // 3))
                )
        for radius in range(14, 2, -2):
            alpha = _NS_pyraena._alpha((14 - radius) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_pyraena.PALETTE["fire_mid"], alpha),
                    (70 - radius, 22 - radius // 5,
                     radius * 2, max(2, radius // 4))
                )
        surface.blit(mist, (cx - 70, cy - 12))
        # Rising fire embers
        for i in range(10):
            t = (phase * 0.5 + i * 0.13) % 1.0
            px = cx - 24 + i * 6 + int(math.sin(phase + i) * 4)
            py = cy + 4 - int(t * 28)
            alpha = _NS_pyraena._alpha(220 * (1 - t) * strength)
            if alpha > 0:
                _NS_pyraena._aacircle(surface,
                                      (*_NS_pyraena.PALETTE["fire_dark"], alpha),
                                      (px, py), 3)
                _NS_pyraena._aacircle(surface,
                                      (*_NS_pyraena.PALETTE["fire_hot"], alpha),
                                      (px, py - 1), 2)
                pygame.draw.rect(surface,
                                 (*_NS_pyraena.PALETTE["fire_bright"], alpha),
                                 (px, py - 1, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_pyraena.PALETTE["fire_shine"], alpha),
                                 (px, py - 2, 1, 1))
        # Glowing bright embers
        for i in range(6):
            spark_t = (phase * 0.8 + i * 0.2) % 1.0
            sx = cx - 20 + i * 8 + int(math.sin(phase + i) * 5)
            sy = cy + 4 - int(spark_t * 22)
            alpha = _NS_pyraena._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_pyraena.PALETTE["fire_bright"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_pyraena.PALETTE["fire_shine"], alpha),
                                 (sx, sy, 1, 1))
        # Trail behind
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_pyraena._alpha(160 - i * 25)
                if alpha > 0:
                    _NS_pyraena._aacircle(surface,
                                          (*_NS_pyraena.PALETTE["fire_dark"], alpha),
                                          (sx, sy), max(1, 5 - i))
                    _NS_pyraena._aacircle(surface,
                                          (*_NS_pyraena.PALETTE["fire_hot"], alpha),
                                          (sx, sy), max(1, 3 - i))
                    pygame.draw.rect(surface, _NS_pyraena.PALETTE["fire_bright"],
                                     (sx, sy - 1, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 26), pygame.SRCALPHA)
        for radius in range(13, 0, -1):
            alpha = max(0, (13 - radius) * 14)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 13 - radius, 120 + radius * 2, radius * 2)
            )
        pygame.draw.ellipse(shadow, (5, 3, 2, 170), (5, 6, 130, 14))
        pygame.draw.ellipse(shadow, (80, 20, 5, 100), (15, 8, 110, 10))
        surface.blit(shadow, (x - 70, y - 13))
    def _draw_fire_aura(surface, x, y, phase):
        """Bright orange/red fire aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_pyraena._alpha((90 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_pyraena._aacircle(aura, (*_NS_pyraena.PALETTE["fire_darkest"], alpha),
                                      (110, 90), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_pyraena._alpha((55 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_pyraena._aacircle(aura, (*_NS_pyraena.PALETTE["fire_dark"], alpha),
                                      (110, 90), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_pyraena._alpha((30 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_pyraena._aacircle(aura, (*_NS_pyraena.PALETTE["fire_mid"], alpha),
                                      (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        # Floating fire embers
        for i in range(14):
            angle = phase * 0.4 + i * math.pi / 7
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_pyraena.PALETTE["fire_hot"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_pyraena.PALETTE["fire_bright"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground fire ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_pyraena.PALETTE["fire_darkest"], 210),
                            (5, 15, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_pyraena.PALETTE["fire_dark"], 220),
                            (14, 17, 132, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_pyraena.PALETTE["fire_mid"], 200),
                            (25, 19, 110, 16), 1)
        # Fire runes around
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 27 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 27 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_pyraena.PALETTE["fire_bright"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_pyraena.PALETTE["fire_shine"],
                                        _NS_pyraena._alpha(160 * pulse)),
                                (12, 10, 136, 32), 1)
        surface.blit(ring, (x - 80, y - 25))
    # ============================================================
    # SKILL Q - DRAGON'S BREATH (fire dragon projectile)
    # ============================================================
    def _draw_dragon_breath_skill(surface, boss, x, y, timer, phase):
        """Fire dragon head breath projectile."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_pyraena._target_position(boss, x, y)
        if progress < 0.2:
            # Charge - fire gathers in both palms
            t = progress / 0.2
            hand_x = x + facing * 22
            hand_y = y - 4
            for r in range(int(12 * t), 0, -1):
                alpha = _NS_pyraena._alpha(200 * t * (12 - r) / 12)
                _NS_pyraena._aacircle(surface, (*_NS_pyraena.PALETTE["fire_dark"], alpha),
                                      (hand_x, hand_y), r)
            _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_hot"],
                                  (hand_x, hand_y), max(1, int(6 * t)))
            _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_bright"],
                                  (hand_x, hand_y), max(1, int(3 * t)))
            pygame.draw.rect(surface, _NS_pyraena.PALETTE["fire_shine"],
                             (hand_x, hand_y, 1, 1))
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 24
            start_y = y - 4
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Fire trail (LONG dragon body of fire)
            for i in range(15):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_pyraena._alpha(240 - i * 15)
                # Wavy dragon body
                wave = math.sin(trail_t * 20 + phase * 4) * 3
                perp_angle = math.atan2(ty - start_y, tx - start_x) + math.pi / 2
                py_wave = py + int(math.sin(perp_angle) * wave)
                px_wave = px + int(math.cos(perp_angle) * wave)
                size = max(2, 12 - i // 2)
                _NS_pyraena._aacircle(surface,
                                      (*_NS_pyraena.PALETTE["fire_darkest"], alpha),
                                      (px_wave, py_wave), size)
                _NS_pyraena._aacircle(surface,
                                      (*_NS_pyraena.PALETTE["fire_dark"], alpha),
                                      (px_wave, py_wave), max(1, size - 2))
                _NS_pyraena._aacircle(surface,
                                      (*_NS_pyraena.PALETTE["fire_mid"], alpha),
                                      (px_wave, py_wave), max(1, size - 4))
                _NS_pyraena._aacircle(surface,
                                      (*_NS_pyraena.PALETTE["fire_hot"], alpha),
                                      (px_wave, py_wave), max(1, size - 6))
                _NS_pyraena._aacircle(surface,
                                      (*_NS_pyraena.PALETTE["fire_bright"], alpha),
                                      (px_wave, py_wave), max(1, size - 8))
                # Sparks
                if i < 6:
                    for s in range(3):
                        spark_a = phase * 3 + i + s
                        spark_x = px_wave + int(math.cos(spark_a) * (size + 3))
                        spark_y = py_wave + int(math.sin(spark_a) * (size + 3))
                        pygame.draw.rect(surface,
                                         (*_NS_pyraena.PALETTE["fire_shine"], alpha),
                                         (spark_x, spark_y, 1, 1))
                        pygame.draw.rect(surface,
                                         (*_NS_pyraena.PALETTE["white"], alpha),
                                         (spark_x, spark_y, 1, 1))
            # DRAGON HEAD at front
            _NS_pyraena._draw_fire_dragon_head(surface, bx, by, facing, phase)
            # Impact stun effect
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(15 + st * 30)
                alpha = _NS_pyraena._alpha(240 * (1 - st))
                _NS_pyraena._aacircle(surface,
                                      (*_NS_pyraena.PALETTE["fire_darkest"], alpha),
                                      (tx, ty), radius + 4)
                _NS_pyraena._aacircle(surface,
                                      (*_NS_pyraena.PALETTE["fire_dark"], alpha),
                                      (tx, ty), radius)
                _NS_pyraena._aacircle(surface,
                                      (*_NS_pyraena.PALETTE["fire_mid"], alpha),
                                      (tx, ty), max(1, radius - 8))
                _NS_pyraena._aacircle(surface,
                                      (*_NS_pyraena.PALETTE["fire_hot"], alpha),
                                      (tx, ty), max(1, radius - 15))
                _NS_pyraena._aacircle(surface,
                                      (*_NS_pyraena.PALETTE["fire_bright"], alpha),
                                      (tx, ty), max(1, radius - 20))
                # Stun stars around target
                for i in range(5):
                    star_angle = phase * 2 + i * math.pi * 2 / 5
                    sx = tx + int(math.cos(star_angle) * (radius + 5))
                    sy = ty + int(math.sin(star_angle) * (radius + 5))
                    pygame.draw.rect(surface,
                                     (*_NS_pyraena.PALETTE["fire_bright"], alpha),
                                     (sx, sy, 3, 3))
                    pygame.draw.rect(surface,
                                     (*_NS_pyraena.PALETTE["fire_shine"], alpha),
                                     (sx, sy, 2, 2))
    def _draw_fire_dragon_head(surface, cx, cy, facing, phase):
        """Draw the dragon head at the front of the fire breath."""
        # Head shape (elongated dragon snout)
        head_shape = [
            (cx - 8 * facing, cy - 6),
            (cx - 5 * facing, cy - 10),
            (cx + 3 * facing, cy - 8),
            (cx + 12 * facing, cy - 4),
            (cx + 16 * facing, cy),
            (cx + 12 * facing, cy + 4),
            (cx + 3 * facing, cy + 6),
            (cx - 5 * facing, cy + 8),
            (cx - 8 * facing, cy + 4),
        ]
        # Shadow
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["shadow_deep"],
                          [(px + 2, py + 2) for px, py in head_shape])
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["fire_darkest"], head_shape)
        # Layered fire dragon head
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["fire_dark"], [
            (cx - 6 * facing, cy - 5),
            (cx - 3 * facing, cy - 9),
            (cx + 3 * facing, cy - 7),
            (cx + 11 * facing, cy - 3),
            (cx + 14 * facing, cy),
            (cx + 11 * facing, cy + 3),
            (cx + 3 * facing, cy + 5),
            (cx - 3 * facing, cy + 7),
            (cx - 6 * facing, cy + 3),
        ])
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["fire_mid"], [
            (cx - 4 * facing, cy - 4),
            (cx, cy - 7),
            (cx + 4 * facing, cy - 5),
            (cx + 10 * facing, cy - 2),
            (cx + 12 * facing, cy),
            (cx + 10 * facing, cy + 2),
            (cx + 4 * facing, cy + 4),
            (cx, cy + 6),
            (cx - 4 * facing, cy + 3),
        ])
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["fire_hot"], [
            (cx - 2 * facing, cy - 3),
            (cx + 2 * facing, cy - 5),
            (cx + 8 * facing, cy - 1),
            (cx + 10 * facing, cy),
            (cx + 8 * facing, cy + 1),
            (cx + 2 * facing, cy + 5),
            (cx - 2 * facing, cy + 3),
        ])
        _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["fire_bright"], [
            (cx, cy - 2),
            (cx + 3 * facing, cy - 3),
            (cx + 6 * facing, cy),
            (cx + 3 * facing, cy + 3),
            (cx, cy + 2),
        ])
        # Dragon eye (glowing white/yellow)
        eye_x = cx + 5 * facing
        eye_y = cy - 3
        _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["shadow_deep"],
                              (eye_x, eye_y), 3)
        _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_bright"],
                              (eye_x, eye_y), 2)
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["fire_shine"],
                         (eye_x, eye_y, 1, 1))
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["white"],
                         (eye_x, eye_y, 1, 1))
        # Nostril
        pygame.draw.rect(surface, _NS_pyraena.PALETTE["fire_darkest"],
                         (cx + 13 * facing, cy - 1, 1, 1))
        # Open mouth with fire teeth
        pygame.draw.line(surface, _NS_pyraena.PALETTE["fire_darkest"],
                         (cx + 8 * facing, cy + 1), (cx + 15 * facing, cy + 2), 1)
        # Fangs
        for f in (10, 13):
            pygame.draw.rect(surface, _NS_pyraena.PALETTE["fire_bright"],
                             (cx + f * facing, cy + 1, 1, 2))
            pygame.draw.rect(surface, _NS_pyraena.PALETTE["fire_shine"],
                             (cx + f * facing, cy + 2, 1, 1))
        # Horns (small fire spikes)
        for horn_off_x, horn_off_y, horn_h in [(-2, -8, -3), (2, -8, -4)]:
            hx = cx + int(horn_off_x * facing)
            hy = cy + horn_off_y
            tip_y = hy + horn_h
            _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["fire_dark"], [
                (hx - 1, hy),
                (hx, tip_y),
                (hx + 1, hy),
            ])
            _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["fire_hot"], [
                (hx, hy),
                (hx, tip_y),
                (hx + 1, hy),
            ])
            pygame.draw.rect(surface, _NS_pyraena.PALETTE["fire_bright"],
                             (hx, tip_y, 1, 1))
        # Flame mane at back of head
        for mane_i in range(5):
            mane_angle = math.pi / 2 + mane_i * 0.3 - 0.6
            mane_x = cx - int(math.cos(mane_angle) * 8) * facing
            mane_y = cy - int(math.sin(mane_angle) * 8)
            wave = math.sin(phase * 3 + mane_i) * 2
            end_x = mane_x - int(math.cos(mane_angle) * (6 + wave)) * facing
            end_y = mane_y - int(math.sin(mane_angle) * (6 + wave))
            _NS_pyraena._aaline(surface, _NS_pyraena.PALETTE["fire_dark"],
                                (mane_x, mane_y), (end_x, end_y), 3)
            _NS_pyraena._aaline(surface, _NS_pyraena.PALETTE["fire_hot"],
                                (mane_x, mane_y), (end_x, end_y), 2)
            _NS_pyraena._aaline(surface, _NS_pyraena.PALETTE["fire_bright"],
                                (mane_x, mane_y), (end_x, end_y), 1)
            pygame.draw.rect(surface, _NS_pyraena.PALETTE["fire_shine"],
                             (end_x, end_y, 1, 1))
    # ============================================================
    # SKILL W - EMBER SPEARS (fire spears rain in line)
    # ============================================================
    def _draw_ember_spears_ground(surface, boss, x, y, timer, phase):
        """Ground marks where spears will hit."""
        facing = boss.direction
        duration = 75
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_pyraena._target_position(boss, x, y)
        if progress > 0.3:
            # Line of ground marks
            num_spears = 6
            for i in range(num_spears):
                spear_t = i / (num_spears - 1)
                sp_x = int(x + (tx - x) * (0.2 + spear_t * 0.8))
                sp_y = ty
                # Ground scorch mark
                r = int(15 * min(1.0, (progress - 0.3) * 3))
                if r > 3:
                    alpha = _NS_pyraena._alpha(180)
                    pygame.draw.ellipse(surface,
                                        (*_NS_pyraena.PALETTE["fire_darkest"], alpha),
                                        (sp_x - r, sp_y - r // 3, r * 2, r * 2 // 3))
                    pygame.draw.ellipse(surface,
                                        (*_NS_pyraena.PALETTE["fire_dark"], alpha),
                                        (sp_x - r + 2, sp_y - r // 3 + 1,
                                         r * 2 - 4, r * 2 // 3 - 2))
    def _draw_ember_spears_skill(surface, boss, x, y, timer, phase):
        """Multiple fire spears rain down in a line."""
        facing = boss.direction
        duration = 75
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_pyraena._target_position(boss, x, y)
        if progress < 0.25:
            # Charge - hands raised, gathering fire
            t = progress / 0.25
            for hand_off_x in (-6, 6):
                hand_x = x + hand_off_x * facing
                hand_y = y - 4
                for r in range(int(6 * t), 0, -1):
                    alpha = _NS_pyraena._alpha(200 * t)
                    _NS_pyraena._aacircle(surface,
                                          (*_NS_pyraena.PALETTE["fire_mid"], alpha),
                                          (hand_x, hand_y), r)
                _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_bright"],
                                      (hand_x, hand_y), 2)
        else:
            # SPEARS RAIN DOWN in sequence
            t = (progress - 0.25) / 0.75
            num_spears = 6
            for i in range(num_spears):
                spear_t = i / (num_spears - 1)
                sp_x = int(x + (tx - x) * (0.2 + spear_t * 0.8))
                sp_y = ty
                # Each spear appears in sequence
                spear_start_t = i * 0.1
                if t < spear_start_t:
                    continue
                spear_progress = min(1.0, (t - spear_start_t) / 0.25)
                # Spear falls from top of screen
                fall_start_y = sp_y - 200
                current_y = int(fall_start_y + (sp_y - fall_start_y) * spear_progress)
                # Draw spear
                spear_len = 60
                spear_top = current_y - spear_len
                # Multi-layer spear shape (elongated flame)
                # Shadow
                pygame.draw.line(surface, _NS_pyraena.PALETTE["shadow_deep"],
                                 (sp_x + 1, spear_top + 1),
                                 (sp_x + 1, current_y + 1), 8)
                # Base
                pygame.draw.line(surface, _NS_pyraena.PALETTE["fire_darkest"],
                                 (sp_x, spear_top),
                                 (sp_x, current_y), 8)
                pygame.draw.line(surface, _NS_pyraena.PALETTE["fire_dark"],
                                 (sp_x, spear_top),
                                 (sp_x, current_y), 6)
                pygame.draw.line(surface, _NS_pyraena.PALETTE["fire_mid"],
                                 (sp_x, spear_top),
                                 (sp_x, current_y), 4)
                pygame.draw.line(surface, _NS_pyraena.PALETTE["fire_hot"],
                                 (sp_x, spear_top),
                                 (sp_x, current_y), 3)
                pygame.draw.line(surface, _NS_pyraena.PALETTE["fire_bright"],
                                 (sp_x, spear_top),
                                 (sp_x, current_y), 2)
                pygame.draw.line(surface, _NS_pyraena.PALETTE["fire_shine"],
                                 (sp_x, spear_top),
                                 (sp_x, current_y), 1)
                # Spear tip (bright pointed)
                _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["fire_bright"], [
                    (sp_x - 4, current_y - 4),
                    (sp_x, current_y + 2),
                    (sp_x + 4, current_y - 4),
                ])
                _NS_pyraena._poly(surface, _NS_pyraena.PALETTE["fire_shine"], [
                    (sp_x - 2, current_y - 3),
                    (sp_x, current_y + 1),
                    (sp_x + 2, current_y - 3),
                ])
                pygame.draw.rect(surface, _NS_pyraena.PALETTE["white"],
                                 (sp_x, current_y - 1, 1, 1))
                # Spear top (feathery flame)
                for feather_i in range(3):
                    f_angle = -math.pi / 2 + (feather_i - 1) * 0.4
                    f_len = 8
                    end_x = sp_x + int(math.cos(f_angle) * f_len)
                    end_y = spear_top + int(math.sin(f_angle) * f_len)
                    pygame.draw.line(surface, _NS_pyraena.PALETTE["fire_dark"],
                                     (sp_x, spear_top), (end_x, end_y), 3)
                    pygame.draw.line(surface, _NS_pyraena.PALETTE["fire_hot"],
                                     (sp_x, spear_top), (end_x, end_y), 2)
                    pygame.draw.line(surface, _NS_pyraena.PALETTE["fire_bright"],
                                     (sp_x, spear_top), (end_x, end_y), 1)
                # Sparks trailing spear
                for spark_i in range(4):
                    spark_y = current_y - 10 - spark_i * 8
                    spark_x = sp_x + int(math.sin(phase * 3 + spark_i) * 3)
                    spark_alpha = _NS_pyraena._alpha(220 - spark_i * 40)
                    pygame.draw.rect(surface,
                                     (*_NS_pyraena.PALETTE["fire_bright"], spark_alpha),
                                     (spark_x, spark_y, 1, 1))
                    pygame.draw.rect(surface,
                                     (*_NS_pyraena.PALETTE["fire_shine"], spark_alpha),
                                     (spark_x, spark_y - 1, 1, 1))
                # Impact when spear reaches ground
                if spear_progress >= 1.0:
                    impact_r = int(10 + (t - spear_start_t - 0.25) * 30)
                    impact_alpha = _NS_pyraena._alpha(220)
                    _NS_pyraena._aacircle(surface,
                                          (*_NS_pyraena.PALETTE["fire_dark"], impact_alpha),
                                          (sp_x, sp_y), impact_r, 2)
                    _NS_pyraena._aacircle(surface,
                                          (*_NS_pyraena.PALETTE["fire_hot"], impact_alpha),
                                          (sp_x, sp_y), max(1, impact_r - 4), 1)
                    # Radial burst
                    for burst_i in range(6):
                        burst_angle = burst_i * math.pi / 3
                        bx = sp_x + int(math.cos(burst_angle) * impact_r)
                        by = sp_y + int(math.sin(burst_angle) * impact_r * 0.5)
                        pygame.draw.rect(surface,
                                         (*_NS_pyraena.PALETTE["fire_bright"], impact_alpha),
                                         (bx, by, 2, 2))
    # ============================================================
    # SKILL E - PLASMA LANCE (single-target beam)
    # ============================================================
    def _draw_plasma_lance_ground(surface, boss, x, y, timer, phase):
        """Ground scorch at target."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_pyraena._target_position(boss, x, y)
        if progress > 0.3:
            r = int(30 * min(1.0, (progress - 0.3) * 3))
            if r > 3:
                pygame.draw.ellipse(surface,
                                    (*_NS_pyraena.PALETTE["fire_darkest"], 220),
                                    (tx - r, ty - r // 3, r * 2, r * 2 // 3))
                pygame.draw.ellipse(surface,
                                    (*_NS_pyraena.PALETTE["fire_dark"], 200),
                                    (tx - r + 3, ty - r // 3 + 2,
                                     r * 2 - 6, r * 2 // 3 - 4))
                pygame.draw.ellipse(surface,
                                    (*_NS_pyraena.PALETTE["fire_mid"], 150),
                                    (tx - r + 8, ty - r // 3 + 4,
                                     r * 2 - 16, r * 2 // 3 - 8))
    def _draw_plasma_lance_skill(surface, boss, x, y, timer, phase):
        """Massive fire beam lance to target."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_pyraena._target_position(boss, x, y)
        if progress < 0.3:
            # Charge - massive fire at hand
            t = progress / 0.3
            hand_x = x + facing * 22
            hand_y = y - 4
            cr = int(4 + t * 12)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_pyraena._alpha(220 * t * (cr + 5 - r) / (cr + 5))
                _NS_pyraena._aacircle(surface,
                                      (*_NS_pyraena.PALETTE["fire_darkest"], alpha),
                                      (hand_x, hand_y), r)
            for r in range(cr + 2, 0, -1):
                alpha = _NS_pyraena._alpha(240 * t * (cr + 2 - r) / (cr + 2))
                _NS_pyraena._aacircle(surface,
                                      (*_NS_pyraena.PALETTE["fire_dark"], alpha),
                                      (hand_x, hand_y), r)
            _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_mid"],
                                  (hand_x, hand_y), cr - 2)
            _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_hot"],
                                  (hand_x, hand_y), max(1, cr - 4))
            _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_bright"],
                                  (hand_x, hand_y), max(1, cr - 6))
            _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_shine"],
                                  (hand_x, hand_y), max(1, cr - 8))
            pygame.draw.rect(surface, _NS_pyraena.PALETTE["white"],
                             (hand_x, hand_y, 1, 1))
        elif progress < 0.75:
            # BEAM FIRING
            t = (progress - 0.3) / 0.45
            intensity = math.sin(t * math.pi) if t > 0.5 else 1.0
            start_x = x + facing * 26
            start_y = y - 4
            # Multi-layer beam (thick fire lance)
            beam_layers = [
                (14, "fire_darkest", 200),
                (11, "fire_dark", 220),
                (8, "fire_mid", 240),
                (5, "fire_hot", 250),
                (3, "fire_bright", 255),
                (1, "fire_shine", 255),
            ]
            for thickness, color_key, alpha_val in beam_layers:
                actual_alpha = _NS_pyraena._alpha(alpha_val * intensity)
                if actual_alpha <= 0:
                    continue
                pygame.draw.line(surface,
                                 (*_NS_pyraena.PALETTE[color_key], actual_alpha),
                                 (start_x, start_y), (tx, ty), thickness)
            # White core (hottest center)
            pygame.draw.line(surface, _NS_pyraena.PALETTE["white"],
                             (start_x, start_y), (tx, ty), 1)
            # Sparks along beam
            for i in range(10):
                spark_t = i / 10
                spark_x = int(start_x + (tx - start_x) * spark_t)
                spark_y = int(start_y + (ty - start_y) * spark_t)
                # Perpendicular offset
                beam_angle = math.atan2(ty - start_y, tx - start_x)
                perp_x = -math.sin(beam_angle)
                perp_y = math.cos(beam_angle)
                offset = int(math.sin(phase * 5 + i) * 6)
                sx = spark_x + int(perp_x * offset)
                sy = spark_y + int(perp_y * offset)
                pygame.draw.rect(surface, _NS_pyraena.PALETTE["fire_bright"],
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_pyraena.PALETTE["fire_shine"],
                                 (sx, sy, 1, 1))
            # HUGE impact at target
            impact_r = int(20 + t * 25)
            impact_alpha = _NS_pyraena._alpha(240 * intensity)
            _NS_pyraena._aacircle(surface,
                                  (*_NS_pyraena.PALETTE["fire_darkest"], impact_alpha),
                                  (tx, ty), impact_r + 5)
            _NS_pyraena._aacircle(surface,
                                  (*_NS_pyraena.PALETTE["fire_dark"], impact_alpha),
                                  (tx, ty), impact_r)
            _NS_pyraena._aacircle(surface,
                                  (*_NS_pyraena.PALETTE["fire_mid"], impact_alpha),
                                  (tx, ty), max(1, impact_r - 8))
            _NS_pyraena._aacircle(surface,
                                  (*_NS_pyraena.PALETTE["fire_hot"], impact_alpha),
                                  (tx, ty), max(1, impact_r - 15))
            _NS_pyraena._aacircle(surface,
                                  (*_NS_pyraena.PALETTE["fire_bright"], impact_alpha),
                                  (tx, ty), max(1, impact_r - 22))
            _NS_pyraena._aacircle(surface,
                                  (*_NS_pyraena.PALETTE["fire_shine"], impact_alpha),
                                  (tx, ty), max(1, impact_r // 4))
            # Radial rays
            for i in range(12):
                angle_s = i * math.pi / 6
                ex = tx + int(math.cos(angle_s) * impact_r * 1.3)
                ey = ty + int(math.sin(angle_s) * impact_r * 1.3)
                pygame.draw.line(surface,
                                 (*_NS_pyraena.PALETTE["fire_bright"], impact_alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface,
                                 (*_NS_pyraena.PALETTE["fire_shine"], impact_alpha),
                                 (ex, ey, 3, 3))
        else:
            # Aftermath - lingering fire
            t = (progress - 0.75) / 0.25
            for i in range(8):
                rise_t = (phase * 0.8 + i * 0.15) % 1.0
                rx = tx + int(math.sin(phase + i) * 30)
                ry = ty - int(rise_t * 40)
                alpha = _NS_pyraena._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_pyraena._aacircle(surface,
                                          (*_NS_pyraena.PALETTE["fire_dark"], alpha),
                                          (rx, ry), 3)
                    _NS_pyraena._aacircle(surface,
                                          (*_NS_pyraena.PALETTE["fire_hot"], alpha),
                                          (rx, ry), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_pyraena.PALETTE["fire_bright"], alpha),
                                     (rx, ry, 1, 1))
    # ============================================================
    # SKILL R - EMBER SOUL (orbiting fire orbs aura)
    # ============================================================
    def _draw_ember_soul_orbs(surface, boss, x, y, timer, phase):
        """Fiery orbs orbit around body."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Number of orbs (6 orbiting)
        num_orbs = 6
        orbit_r = 35 + int(math.sin(phase * 2) * 3)
        for i in range(num_orbs):
            orb_angle = phase * 2 + i * math.pi * 2 / num_orbs
            ox = x + int(math.cos(orb_angle) * orbit_r)
            oy = y + int(math.sin(orb_angle) * orbit_r * 0.6)
            # Orb size (varies slightly)
            orb_size = 6 + int(math.sin(phase * 3 + i) * 1)
            # Draw orb (fire ball)
            # Glow halo
            for r in range(orb_size + 4, 0, -1):
                alpha = _NS_pyraena._alpha(180 * (orb_size + 4 - r) / (orb_size + 4))
                _NS_pyraena._aacircle(surface,
                                      (*_NS_pyraena.PALETTE["fire_dark"], alpha),
                                      (ox, oy), r)
            # Core layers
            _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_darkest"],
                                  (ox, oy), orb_size)
            _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_dark"],
                                  (ox, oy), orb_size - 1)
            _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_mid"],
                                  (ox, oy), max(1, orb_size - 2))
            _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_hot"],
                                  (ox, oy), max(1, orb_size - 3))
            _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_bright"],
                                  (ox, oy), max(1, orb_size - 4))
            _NS_pyraena._aacircle(surface, _NS_pyraena.PALETTE["fire_shine"],
                                  (ox, oy), max(1, orb_size - 5))
            pygame.draw.rect(surface, _NS_pyraena.PALETTE["white"],
                             (ox - 1, oy - 1, 1, 1))
            # Sparks around each orb
            for s in range(3):
                spark_angle = phase * 4 + i * 2 + s * math.pi * 2 / 3
                sx = ox + int(math.cos(spark_angle) * (orb_size + 2))
                sy = oy + int(math.sin(spark_angle) * (orb_size + 2))
                pygame.draw.rect(surface, _NS_pyraena.PALETTE["fire_bright"],
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface, _NS_pyraena.PALETTE["fire_shine"],
                                 (sx, sy, 1, 1))
            # Small trail behind orb (following orbit)
            trail_angle = orb_angle - 0.3
            tx_orb = x + int(math.cos(trail_angle) * orbit_r)
            ty_orb = y + int(math.sin(trail_angle) * orbit_r * 0.6)
            pygame.draw.line(surface,
                             (*_NS_pyraena.PALETTE["fire_hot"], 180),
                             (tx_orb, ty_orb), (ox, oy), 2)
            pygame.draw.line(surface,
                             (*_NS_pyraena.PALETTE["fire_bright"], 220),
                             (tx_orb, ty_orb), (ox, oy), 1)
        # Central fire pulse (heart of the aura)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        core_r = int(8 * pulse)
        for r in range(core_r + 3, 0, -1):
            alpha = _NS_pyraena._alpha(150 * (core_r + 3 - r) / (core_r + 3))
            _NS_pyraena._aacircle(surface,
                                  (*_NS_pyraena.PALETTE["fire_hot"], alpha),
                                  (x, y), r)
        # Fire lines connecting orbs to center (magical energy)
        for i in range(num_orbs):
            orb_angle = phase * 2 + i * math.pi * 2 / num_orbs
            ox = x + int(math.cos(orb_angle) * orbit_r)
            oy = y + int(math.sin(orb_angle) * orbit_r * 0.6)
            alpha = _NS_pyraena._alpha(80 + math.sin(phase * 3 + i) * 40)
            pygame.draw.line(surface,
                             (*_NS_pyraena.PALETTE["fire_bright"], alpha),
                             (x, y), (ox, oy), 1)

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_kaizoku_raijin(surface, boss, x, y):
    """Entry point kaizoku_raijin."""
    return _NS_kaizoku_raijin.draw_kaizoku_raijin(surface, boss, x, y)


def draw_korokai(surface, boss, x, y):
    """Entry point korokai."""
    return _NS_korokai.draw_korokai(surface, boss, x, y)


def draw_verdanix(surface, boss, x, y):
    """Entry point verdanix."""
    return _NS_verdanix.draw_verdanix(surface, boss, x, y)


def draw_pyraena(surface, boss, x, y):
    """Entry point pyraena."""
    return _NS_pyraena.draw_pyraena(surface, boss, x, y)
