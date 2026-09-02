"""
bosses/level42.py - Semua boss Level 42

Berisi:
  - kaedrin    (mini boss - MELEE moonfang, half-demon bladebearer)
  - morvaeth   (mini boss - MELEE mirrorborn, demon marauder)
  - vardrok    (mini boss - MELEE axe-king, executioner)
  - kaineroth  (TRUE BOSS - RANGED crow-eyed, sharingan crimson)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _kd_ (kaedrin), _vd_ (vardrok) sudah unik.
  - _mv_ (morvaeth) di-rename -> _mrv_ (bentrok dengan morvaeth
    level 25), termasuk atribut _last_x/_last_y.
  - _kn_ (kaineroth) di-rename -> _knt_ (bentrok dengan kyrenzai
    level 38), termasuk atribut _last_x/_last_y.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# KAEDRIN (MOONFANG) - Mini Boss
# ====================================================================

class _NS_kaedrin:
    """Namespace kaedrin - half-demon warrior boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Red robe (main body)
        "robe_darkest": (55, 8, 10),
        "robe_dark": (120, 20, 25),
        "robe_mid": (185, 40, 45),
        "robe_light": (230, 80, 75),
        "robe_edge": (255, 140, 130),
        "robe_shine": (255, 200, 190),
        # Skin (tan warrior)
        "skin_dark": (130, 90, 70),
        "skin_mid": (200, 155, 120),
        "skin_light": (240, 205, 170),
        "skin_shine": (255, 230, 200),
        # White hair (long silver-white)
        "hair_darkest": (110, 105, 115),
        "hair_dark": (170, 165, 175),
        "hair_mid": (215, 213, 220),
        "hair_light": (245, 245, 250),
        "hair_shine": (255, 255, 255),
        # Yellow amber eyes (demon eyes)
        "eye_socket": (10, 5, 3),
        "eye_dark": (95, 55, 8),
        "eye_mid": (215, 155, 30),
        "eye_light": (255, 220, 90),
        "eye_hot": (255, 250, 180),
        # Sword blade (steel white)
        "steel_darkest": (35, 40, 55),
        "steel_dark": (80, 90, 110),
        "steel_mid": (150, 160, 180),
        "steel_light": (215, 225, 240),
        "steel_shine": (250, 250, 255),
        # Sword hilt (brown wrap)
        "hilt_dark": (45, 25, 10),
        "hilt_mid": (95, 55, 25),
        "hilt_light": (155, 100, 55),
        # Blade fur handle guard (white fluffy)
        "fur_dark": (155, 150, 155),
        "fur_mid": (210, 205, 215),
        "fur_light": (245, 240, 245),
        # Beads necklace (dark purple)
        "bead_dark": (30, 15, 45),
        "bead_mid": (75, 40, 100),
        "bead_light": (150, 100, 180),
        # Fire (orange demonic aura)
        "fire_darkest": (40, 8, 2),
        "fire_dark": (140, 35, 10),
        "fire_mid": (235, 90, 25),
        "fire_light": (255, 155, 55),
        "fire_hot": (255, 215, 115),
        "fire_shine": (255, 245, 200),
        # Purple demonic (Life Break beam)
        "demon_darkest": (25, 5, 40),
        "demon_dark": (75, 15, 115),
        "demon_mid": (150, 40, 200),
        "demon_light": (215, 110, 250),
        "demon_hot": (245, 190, 255),
        "demon_shine": (255, 240, 255),
        # Blood red (Berserker)
        "blood_dark": (75, 8, 15),
        "blood_mid": (170, 25, 35),
        "blood_light": (240, 60, 65),
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
        color = _NS_kaedrin._clamp(color)
        if _NS_kaedrin.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_kaedrin._clamp(color)
        if _NS_kaedrin.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_kaedrin._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ================= ENTRY POINT =================
    def draw_kaedrin(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kaedrin._detect_moving(boss)
        _NS_kaedrin._update_kd_attack_anim(boss)
        attacking = (
            getattr(boss, "_kd_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        _NS_kaedrin._draw_fire_aura(surface, x, y, pulse)
        _NS_kaedrin._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX behind body.
        if active_skill == "q":
            _NS_kaedrin._draw_ember_spear_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaedrin._draw_lifecleave_ground(surface, boss, x, y, skill_timer, pulse)
        # Body.
        if attacking:
            _NS_kaedrin._draw_kd_attack(surface, boss, x, y)
        elif moving:
            _NS_kaedrin._draw_kd_walk(surface, boss, x, y)
        else:
            _NS_kaedrin._draw_kd_idle(surface, boss, x, y)
        # Inner Fire buff bubble (over body).
        if active_skill == "w":
            _NS_kaedrin._draw_inner_fire_flames(surface, boss, x, y, skill_timer, pulse)
        # Foreground FX.
        if active_skill == "q":
            _NS_kaedrin._draw_ember_spear_projectile(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaedrin._draw_bloodrage_strike(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaedrin._draw_lifecleave_beam(surface, boss, x, y, skill_timer, pulse)
    # ================= ANIMATION STATE =================
    def _update_kd_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kd_previous_timer", 0))
        active = bool(getattr(boss, "_kd_attack_active", False))
        if not active and previous > timer and previous >= cooldown - 2:
            boss._kd_attack_active = True
            boss._kd_attack_frame = 0
            active = True
        elif active:
            boss._kd_attack_frame = int(getattr(boss, "_kd_attack_frame", 0)) + 1
            if boss._kd_attack_frame >= cooldown:
                boss._kd_attack_active = False
                boss._kd_attack_frame = 0
                active = False
        boss._kd_previous_timer = timer
        boss._kd_attack_progress = (
            min(1.0, getattr(boss, "_kd_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_kd_last_x"):
            boss._kd_last_x = boss.x
            boss._kd_last_y = boss.y
            return False
        dx = abs(boss.x - boss._kd_last_x)
        dy = abs(boss.y - boss._kd_last_y)
        boss._kd_last_x = boss.x
        boss._kd_last_y = boss.y
        return dx + dy > 0.3
    # ================= POSE ROUTERS =================
    def _draw_kd_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_kaedrin._draw_shadow(surface, x, y + 50)
        _NS_kaedrin._draw_hover_particles(surface, x, y + 44, boss.pulse)
        _NS_kaedrin._draw_kd_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")
    def _draw_kd_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 6)
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_kaedrin._draw_shadow(surface, x + sway, y + 50)
        _NS_kaedrin._draw_hover_particles(surface, x + sway, y + 44, phase, trail=True, facing=boss.direction)
        _NS_kaedrin._draw_kd_body(surface, x + sway, y + bob, boss.direction, phase, "walk")
    def _draw_kd_attack(surface, boss, x, y):
        progress = getattr(boss, "_kd_attack_progress", None)
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
        _NS_kaedrin._draw_shadow(surface, x + lunge, y + 50)
        _NS_kaedrin._draw_hover_particles(surface, x + lunge, y + 44, boss.pulse, intense=True)
        _NS_kaedrin._draw_kd_body(surface, x + lunge, y - lift, boss.direction, boss.pulse, "attack", progress)
        _NS_kaedrin._draw_sword_swing(surface, boss, x + lunge, y - lift, progress)
    # ================= BODY =================
    def _draw_kd_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Long hair trailing back (background).
        _NS_kaedrin._draw_back_hair(surface, cx, cy - 14, facing, phase)
        # Legs (with hakama pants flare).
        _NS_kaedrin._draw_hakama_legs(surface, cx, cy + 8, facing, phase, action)
        # Robe torso.
        _NS_kaedrin._draw_robe_torso(surface, cx, cy, facing, phase)
        # Back arm.
        _NS_kaedrin._draw_back_arm(surface, cx, cy, facing, phase, action)
        # Head with dog ears + white hair front.
        _NS_kaedrin._draw_dog_head(surface, cx, cy - 18, facing, phase, action)
        # Prayer bead necklace.
        _NS_kaedrin._draw_beads(surface, cx, cy - 8, facing, phase)
        # Sword arm (front, with big blade).
        _NS_kaedrin._draw_sword_arm(surface, cx, cy, facing, phase, action, attack_progress)
    def _draw_back_hair(surface, cx, cy, facing, phase):
        """Long white hair flowing behind."""
        wave = math.sin(phase * 0.6) * 2
        back_dir = -facing
        # Main hair mass.
        hair_shape = [
            (cx + back_dir * 2, cy - 4),
            (cx + back_dir * 8, cy - 2),
            (cx + back_dir * 12 + int(wave), cy + 4),
            (cx + back_dir * 14 + int(wave * 0.7), cy + 12),
            (cx + back_dir * 12 + int(wave * 0.5), cy + 22),
            (cx + back_dir * 8, cy + 28),
            (cx + back_dir * 3, cy + 26),
            (cx + back_dir * 1, cy + 12),
            (cx + back_dir * 2, cy),
        ]
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in hair_shape])
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["hair_darkest"], hair_shape)
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["hair_dark"], [
            (cx + back_dir * 2, cy - 2),
            (cx + back_dir * 7, cy),
            (cx + back_dir * 11 + int(wave * 0.7), cy + 6),
            (cx + back_dir * 12 + int(wave * 0.4), cy + 18),
            (cx + back_dir * 8, cy + 26),
            (cx + back_dir * 3, cy + 22),
            (cx + back_dir * 2, cy),
        ])
        # Silver highlights (streaks).
        for i, offset in enumerate((-2, 4, 10, 18)):
            hy = cy + offset
            hx = cx + back_dir * (4 + i * 2) + int(wave * 0.5)
            pygame.draw.line(surface, _NS_kaedrin.PALETTE["hair_mid"],
                             (hx, hy), (hx + back_dir, hy + 4), 1)
            pygame.draw.line(surface, _NS_kaedrin.PALETTE["hair_light"],
                             (hx, hy), (hx + back_dir, hy + 2), 1)
    def _draw_hakama_legs(surface, cx, cy, facing, phase, action):
        """Red hakama pants (wide flared)."""
        leg_bob = math.sin(phase * 1.5) * 3 if action == "walk" else math.sin(phase * 0.8) * 1
        # Wide hakama shape (like a skirt flare).
        hakama_shape = [
            (cx - 14, cy - 4),
            (cx + 14, cy - 4),
            (cx + 18, cy + 6),
            (cx + 16, cy + 14),
            (cx + 8, cy + 18),
            (cx - 8, cy + 18),
            (cx - 16, cy + 14),
            (cx - 18, cy + 6),
        ]
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in hakama_shape])
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["robe_darkest"], hakama_shape)
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["robe_dark"], [
            (cx - 13, cy - 3),
            (cx + 13, cy - 3),
            (cx + 17, cy + 6),
            (cx + 14, cy + 13),
            (cx + 6, cy + 16),
            (cx - 6, cy + 16),
            (cx - 14, cy + 13),
            (cx - 17, cy + 6),
        ])
        # Mid highlight fold.
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["robe_mid"], [
            (cx - 10, cy - 2),
            (cx + 10, cy - 2),
            (cx + 12, cy + 4),
            (cx - 12, cy + 4),
        ])
        # Vertical fold lines.
        for fold_x in (-8, -3, 3, 8):
            pygame.draw.line(surface, _NS_kaedrin.PALETTE["robe_darkest"],
                             (cx + fold_x, cy - 2), (cx + fold_x + int(fold_x * 0.3), cy + 16), 1)
            pygame.draw.line(surface, _NS_kaedrin.PALETTE["robe_mid"],
                             (cx + fold_x - 1, cy - 2), (cx + fold_x + int(fold_x * 0.3) - 1, cy + 14), 1)
        # Feet visible below.
        for side in (-1, 1):
            foot_x = cx + side * 6
            foot_y = cy + 18 + int(leg_bob * side * 0.3)
            _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["shadow_deep"], [
                (foot_x - 3 + 1, foot_y - 1 + 1),
                (foot_x + 3 + 1, foot_y - 1 + 1),
                (foot_x + 2 + 1, foot_y + 2 + 1),
                (foot_x - 2 + 1, foot_y + 2 + 1),
            ])
            _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["skin_dark"], [
                (foot_x - 3, foot_y - 1),
                (foot_x + 3, foot_y - 1),
                (foot_x + 2, foot_y + 2),
                (foot_x - 2, foot_y + 2),
            ])
            _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["skin_mid"], [
                (foot_x - 2, foot_y),
                (foot_x + 2, foot_y),
                (foot_x + 1, foot_y + 1),
                (foot_x - 1, foot_y + 1),
            ])
    def _draw_robe_torso(surface, cx, cy, facing, phase):
        """Red robe wrapping torso with V-neck."""
        breath = math.sin(phase * 0.7) * 1
        torso_shape = [
            (cx - 13, cy - 10),
            (cx - 15, cy - 4),
            (cx - 13, cy + 4),
            (cx - 12, cy + 12),
            (cx + 12, cy + 12),
            (cx + 13, cy + 4),
            (cx + 15, cy - 4),
            (cx + 13, cy - 10),
            (cx + 6, cy - 12),
            (cx - 6, cy - 12),
        ]
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 3) for p in torso_shape])
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["robe_darkest"], torso_shape)
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["robe_dark"], [
            (cx - 12, cy - 9),
            (cx - 14, cy - 3),
            (cx - 12, cy + 3),
            (cx - 11, cy + 11),
            (cx + 11, cy + 11),
            (cx + 12, cy + 3),
            (cx + 14, cy - 3),
            (cx + 12, cy - 9),
            (cx + 5, cy - 11),
            (cx - 5, cy - 11),
        ])
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["robe_mid"], [
            (cx - 10, cy - 6),
            (cx - 12, cy - 2),
            (cx - 10, cy + 6),
            (cx + 10, cy + 6),
            (cx + 12, cy - 2),
            (cx + 10, cy - 6),
        ])
        # V-neck (skin visible).
        v_neck = [
            (cx - 5, cy - 11),
            (cx + 5, cy - 11),
            (cx + 2, cy - 6),
            (cx, cy - 3),
            (cx - 2, cy - 6),
        ]
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["skin_dark"], v_neck)
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["skin_mid"], [
            (cx - 4, cy - 10),
            (cx + 4, cy - 10),
            (cx + 1, cy - 6),
            (cx - 1, cy - 6),
        ])
        pygame.draw.rect(surface, _NS_kaedrin.PALETTE["skin_light"], (cx, cy - 8, 1, 1))
        # V-neck lapels (fold lines).
        pygame.draw.line(surface, _NS_kaedrin.PALETTE["robe_edge"],
                         (cx - 5, cy - 11), (cx - 2, cy - 6), 1)
        pygame.draw.line(surface, _NS_kaedrin.PALETTE["robe_edge"],
                         (cx + 5, cy - 11), (cx + 2, cy - 6), 1)
        pygame.draw.line(surface, _NS_kaedrin.PALETTE["robe_shine"],
                         (cx - 4, cy - 11), (cx - 1, cy - 7), 1)
        # Sash/obi belt.
        pygame.draw.rect(surface, _NS_kaedrin.PALETTE["shadow_deep"], (cx - 13, cy + 8, 26, 4))
        pygame.draw.rect(surface, _NS_kaedrin.PALETTE["hilt_dark"], (cx - 13, cy + 8, 26, 4))
        pygame.draw.rect(surface, _NS_kaedrin.PALETTE["hilt_mid"], (cx - 12, cy + 9, 24, 2))
        pygame.draw.rect(surface, _NS_kaedrin.PALETTE["hilt_light"], (cx - 12, cy + 9, 24, 1))
        # Knot at side.
        _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["hilt_dark"], (cx + facing * 12, cy + 10), 3)
        _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["hilt_mid"], (cx + facing * 12, cy + 10), 2)
        # Shoulder detail.
        for side in (-1, 1):
            sh_x = cx + side * 12
            sh_y = cy - 8
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["robe_darkest"], (sh_x, sh_y), 4)
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["robe_dark"], (sh_x, sh_y), 3)
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["robe_mid"], (sh_x - 1, sh_y - 1), 2)
            pygame.draw.rect(surface, _NS_kaedrin.PALETTE["robe_edge"], (sh_x - 1, sh_y - 1, 1, 1))
    def _draw_beads(surface, cx, cy, facing, phase):
        """Purple prayer bead necklace."""
        num_beads = 9
        for i in range(num_beads):
            angle = math.pi * 0.15 + (i / (num_beads - 1)) * math.pi * 0.7
            bx = cx + int(math.cos(angle) * 7)
            by = cy + int(math.sin(angle) * 4) + 2
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["shadow_deep"], (bx + 1, by + 1), 2)
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["bead_dark"], (bx, by), 2)
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["bead_mid"], (bx, by), 1)
            pygame.draw.rect(surface, _NS_kaedrin.PALETTE["bead_light"], (bx, by, 1, 1))
    def _draw_dog_head(surface, cx, cy, facing, phase, action):
        """Head with dog ears + long white hair + amber eyes."""
        # DOG EARS on top (triangular pointy).
        for side_i, side_off in enumerate((-5, 5)):
            ear_base_x = cx + side_off
            ear_base_y = cy - 6
            ear_tip_x = cx + side_off + (side_off // 2)
            ear_tip_y = cy - 12
            # Outer.
            _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["shadow_deep"], [
                (ear_base_x - 2 + 1, ear_base_y + 1),
                (ear_base_x + 3 + 1, ear_base_y + 1),
                (ear_tip_x + 1, ear_tip_y + 1),
            ])
            _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["hair_darkest"], [
                (ear_base_x - 2, ear_base_y),
                (ear_base_x + 3, ear_base_y),
                (ear_tip_x, ear_tip_y),
            ])
            # Mid.
            _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["hair_dark"], [
                (ear_base_x - 1, ear_base_y - 1),
                (ear_base_x + 2, ear_base_y - 1),
                (ear_tip_x, ear_tip_y + 1),
            ])
            _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["hair_mid"], [
                (ear_base_x, ear_base_y - 1),
                (ear_base_x + 1, ear_base_y - 1),
                (ear_tip_x, ear_tip_y + 2),
            ])
            # Inner pink.
            _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["robe_mid"], [
                (ear_base_x, ear_base_y),
                (ear_base_x + 1, ear_base_y),
                (ear_tip_x, ear_tip_y + 3),
            ])
            pygame.draw.rect(surface, _NS_kaedrin.PALETTE["hair_light"], (ear_tip_x, ear_tip_y + 1, 1, 1))
        # HAIR (top of head - front).
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["shadow_deep"], [
            (cx - 7 + 1, cy - 5 + 1),
            (cx - 8 + 1, cy + 3 + 1),
            (cx - 4 + 1, cy + 6 + 1),
            (cx + 4 + 1, cy + 6 + 1),
            (cx + 8 + 1, cy + 3 + 1),
            (cx + 7 + 1, cy - 5 + 1),
            (cx + 4 + 1, cy - 8 + 1),
            (cx - 4 + 1, cy - 8 + 1),
        ])
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["hair_darkest"], [
            (cx - 7, cy - 5),
            (cx - 8, cy + 3),
            (cx - 4, cy + 6),
            (cx + 4, cy + 6),
            (cx + 8, cy + 3),
            (cx + 7, cy - 5),
            (cx + 4, cy - 8),
            (cx - 4, cy - 8),
        ])
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["hair_dark"], [
            (cx - 6, cy - 4),
            (cx - 7, cy + 2),
            (cx - 3, cy + 5),
            (cx + 3, cy + 5),
            (cx + 7, cy + 2),
            (cx + 6, cy - 4),
            (cx + 3, cy - 7),
            (cx - 3, cy - 7),
        ])
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["hair_mid"], [
            (cx - 4, cy - 3),
            (cx - 5, cy),
            (cx - 2, cy + 3),
            (cx + 2, cy + 3),
            (cx + 5, cy),
            (cx + 4, cy - 3),
            (cx + 2, cy - 6),
            (cx - 2, cy - 6),
        ])
        pygame.draw.rect(surface, _NS_kaedrin.PALETTE["hair_light"], (cx - 2, cy - 5, 4, 1))
        pygame.draw.rect(surface, _NS_kaedrin.PALETTE["hair_shine"], (cx - 1, cy - 5, 2, 1))
        # Face (skin peek at bottom).
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["skin_dark"], [
            (cx - 4, cy + 2),
            (cx - 4, cy + 6),
            (cx + 4, cy + 6),
            (cx + 4, cy + 2),
        ])
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["skin_mid"], [
            (cx - 3, cy + 3),
            (cx - 3, cy + 5),
            (cx + 3, cy + 5),
            (cx + 3, cy + 3),
        ])
        pygame.draw.rect(surface, _NS_kaedrin.PALETTE["skin_light"], (cx - 1, cy + 3, 2, 1))
        # HAIR STRANDS on face (side bangs).
        for strand_x in (-4, 4):
            pygame.draw.line(surface, _NS_kaedrin.PALETTE["hair_darkest"],
                             (cx + strand_x, cy - 3), (cx + strand_x - 1, cy + 5), 2)
            pygame.draw.line(surface, _NS_kaedrin.PALETTE["hair_dark"],
                             (cx + strand_x, cy - 3), (cx + strand_x - 1, cy + 5), 1)
            pygame.draw.line(surface, _NS_kaedrin.PALETTE["hair_light"],
                             (cx + strand_x, cy - 2), (cx + strand_x - 1, cy + 3), 1)
        # AMBER EYES (glowing).
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_off in (-2, 2):
            ex = cx + eye_off
            ey = cy + 2
            for r in range(3, 0, -1):
                alpha = _NS_kaedrin._alpha(140 * (3 - r) / 3 * eye_pulse)
                _NS_kaedrin._aacircle(surface, (*_NS_kaedrin.PALETTE["eye_mid"], alpha), (ex, ey), r)
            pygame.draw.rect(surface, _NS_kaedrin.PALETTE["eye_socket"], (ex - 1, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_kaedrin.PALETTE["eye_dark"], (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_kaedrin.PALETTE["eye_mid"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_kaedrin.PALETTE["eye_light"], (ex, ey, 1, 1))
        # Mouth (with fangs).
        mouth_y = cy + 5
        if action == "attack":
            pygame.draw.rect(surface, _NS_kaedrin.PALETTE["shadow_deep"], (cx - 2, mouth_y, 5, 2))
            pygame.draw.rect(surface, _NS_kaedrin.PALETTE["blood_dark"], (cx - 1, mouth_y, 3, 1))
            # Fangs.
            pygame.draw.rect(surface, _NS_kaedrin.PALETTE["white"], (cx - 1, mouth_y, 1, 2))
            pygame.draw.rect(surface, _NS_kaedrin.PALETTE["white"], (cx + 1, mouth_y, 1, 2))
        else:
            pygame.draw.line(surface, _NS_kaedrin.PALETTE["shadow_deep"],
                             (cx - 2, mouth_y), (cx + 2, mouth_y), 1)
            # Small fang tip.
            pygame.draw.rect(surface, _NS_kaedrin.PALETTE["white"], (cx + 1, mouth_y, 1, 1))
    def _draw_back_arm(surface, cx, cy, facing, phase, action):
        """Back arm (mostly hidden by robe)."""
        back_dir = -facing
        sway = math.sin(phase * 0.6) * 1
        shoulder_x = cx + back_dir * 10
        shoulder_y = cy - 6
        hand_x = cx + back_dir * 6
        hand_y = cy + 4 + int(sway)
        _NS_kaedrin._aaline(surface, _NS_kaedrin.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 1), (hand_x + 1, hand_y + 1), 6)
        _NS_kaedrin._aaline(surface, _NS_kaedrin.PALETTE["robe_darkest"],
                            (shoulder_x, shoulder_y), (hand_x, hand_y), 6)
        _NS_kaedrin._aaline(surface, _NS_kaedrin.PALETTE["robe_dark"],
                            (shoulder_x, shoulder_y), (hand_x, hand_y), 4)
        _NS_kaedrin._aaline(surface, _NS_kaedrin.PALETTE["robe_mid"],
                            (shoulder_x, shoulder_y - 1), (hand_x, hand_y - 1), 1)
        # Fist.
        _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["skin_dark"], (hand_x, hand_y), 2)
        _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["skin_mid"], (hand_x, hand_y), 1)
    def _draw_sword_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm with big Fangblade — swing animation."""
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
            swing_angle = math.pi * 0.15 + math.sin(phase * 0.6) * 0.1
            arm_length = 22
        shoulder_x = cx + facing * 12
        shoulder_y = cy - 6
        hand_x = shoulder_x + int(math.cos(swing_angle) * arm_length) * facing
        hand_y = shoulder_y + int(math.sin(swing_angle) * arm_length)
        elbow_x = (shoulder_x + hand_x) // 2 + facing * 2
        elbow_y = (shoulder_y + hand_y) // 2
        # Upper arm (robe sleeve).
        _NS_kaedrin._aaline(surface, _NS_kaedrin.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 1), (elbow_x + 1, elbow_y + 1), 7)
        _NS_kaedrin._aaline(surface, _NS_kaedrin.PALETTE["robe_darkest"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 7)
        _NS_kaedrin._aaline(surface, _NS_kaedrin.PALETTE["robe_dark"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_kaedrin._aaline(surface, _NS_kaedrin.PALETTE["robe_mid"],
                            (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 2)
        # Forearm (robe).
        _NS_kaedrin._aaline(surface, _NS_kaedrin.PALETTE["robe_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 6)
        _NS_kaedrin._aaline(surface, _NS_kaedrin.PALETTE["robe_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_kaedrin._aaline(surface, _NS_kaedrin.PALETTE["robe_mid"],
                            (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
        # Hand (skin, gripping hilt).
        _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["skin_dark"], (hand_x, hand_y), 3)
        _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["skin_mid"], (hand_x, hand_y), 2)
        _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["skin_light"], (hand_x - 1, hand_y - 1), 1)
        # THE BIG BLADE (Fangblade).
        _NS_kaedrin._draw_fangblade(surface, hand_x, hand_y, facing, phase, swing_angle)
    def _draw_fangblade(surface, hx, hy, facing, phase, angle):
        """Massive white sword with fur guard."""
        # Handle direction.
        # Guard/pommel is behind hand.
        pommel_len = 5
        pommel_x = hx - int(math.cos(angle) * pommel_len) * facing
        pommel_y = hy - int(math.sin(angle) * pommel_len)
        # Blade extends far in angle direction.
        blade_len = 34
        tip_x = hx + int(math.cos(angle) * blade_len) * facing
        tip_y = hy + int(math.sin(angle) * blade_len)
        # Perpendicular for blade width.
        perp = angle + math.pi / 2
        base_width = 5
        # Blade shape (wide near guard, tapers at tip).
        b1 = (hx + int(math.cos(perp) * base_width),
              hy + int(math.sin(perp) * base_width))
        b2 = (hx - int(math.cos(perp) * base_width),
              hy - int(math.sin(perp) * base_width))
        # Mid width.
        mid_x = hx + int(math.cos(angle) * (blade_len * 0.5)) * facing
        mid_y = hy + int(math.sin(angle) * (blade_len * 0.5))
        m1 = (mid_x + int(math.cos(perp) * (base_width - 1)),
              mid_y + int(math.sin(perp) * (base_width - 1)))
        m2 = (mid_x - int(math.cos(perp) * (base_width - 1)),
              mid_y - int(math.sin(perp) * (base_width - 1)))
        # Shadow.
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["shadow_deep"], [
            (b1[0] + 2, b1[1] + 2),
            (m1[0] + 2, m1[1] + 2),
            (tip_x + 2, tip_y + 2),
            (m2[0] + 2, m2[1] + 2),
            (b2[0] + 2, b2[1] + 2),
        ])
        # Base blade dark outline.
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["steel_darkest"], [
            b1, m1, (tip_x, tip_y), m2, b2,
        ])
        # Mid gray.
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["steel_dark"], [
            (b1[0] - int(math.cos(perp)), b1[1] - int(math.sin(perp))),
            (m1[0] - int(math.cos(perp)), m1[1] - int(math.sin(perp))),
            (tip_x, tip_y),
            (m2[0] + int(math.cos(perp)), m2[1] + int(math.sin(perp))),
            (b2[0] + int(math.cos(perp)), b2[1] + int(math.sin(perp))),
        ])
        # Steel mid (main fill).
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["steel_mid"], [
            (b1[0] - int(math.cos(perp) * 1), b1[1] - int(math.sin(perp) * 1)),
            (m1[0] - int(math.cos(perp) * 2), m1[1] - int(math.sin(perp) * 2)),
            (tip_x, tip_y),
            (hx, hy),
        ])
        # Bright center highlight.
        _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["steel_light"], [
            (b1[0] - int(math.cos(perp) * 2), b1[1] - int(math.sin(perp) * 2)),
            (m1[0] - int(math.cos(perp) * 3), m1[1] - int(math.sin(perp) * 3)),
            (int((mid_x + tip_x) / 2), int((mid_y + tip_y) / 2)),
            (hx, hy),
        ])
        # Blade edge shine (a fine line down the middle).
        pygame.draw.line(surface, _NS_kaedrin.PALETTE["steel_shine"],
                         (hx, hy), (tip_x, tip_y), 1)
        pygame.draw.rect(surface, _NS_kaedrin.PALETTE["white"], (tip_x, tip_y, 1, 1))
        # FUR GUARD at handle (fluffy white).
        fur_offsets = [(0, 0, 4), (-2, -1, 3), (2, -1, 3), (-2, 1, 3),
                       (2, 1, 3), (0, -3, 3), (0, 3, 3)]
        for off in fur_offsets:
            fx = hx - int(math.cos(angle) * 2) * facing + off[0]
            fy = hy - int(math.sin(angle) * 2) + off[1]
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["shadow_deep"], (fx + 1, fy + 1), off[2])
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["fur_dark"], (fx, fy), off[2])
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["fur_mid"], (fx, fy), off[2] - 1)
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["fur_light"], (fx - 1, fy - 1), max(1, off[2] - 2))
        # HILT (dark brown wrap).
        pygame.draw.line(surface, _NS_kaedrin.PALETTE["hilt_dark"],
                         (pommel_x, pommel_y), (hx, hy), 4)
        pygame.draw.line(surface, _NS_kaedrin.PALETTE["hilt_mid"],
                         (pommel_x, pommel_y), (hx, hy), 2)
        # Wrap texture (X pattern lines).
        for i in range(3):
            t = i / 3
            wx = int(pommel_x + (hx - pommel_x) * t)
            wy = int(pommel_y + (hy - pommel_y) * t)
            pygame.draw.rect(surface, _NS_kaedrin.PALETTE["hilt_dark"], (wx, wy, 1, 1))
        # Pommel end.
        _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["hilt_dark"], (pommel_x, pommel_y), 2)
        _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["hilt_mid"], (pommel_x, pommel_y), 1)
    # ================= MELEE SWING FX =================
    def _draw_sword_swing(surface, boss, x, y, progress):
        """Big white slash arc with red/orange energy."""
        if progress < 0.30 or progress > 0.80:
            return
        facing = boss.direction
        if progress < 0.6:
            swing_t = (progress - 0.30) / 0.30
        else:
            swing_t = 1.0 - (progress - 0.6) / 0.20
        swing_t = max(0.0, min(1.0, swing_t))
        alpha_base = _NS_kaedrin._alpha(255 * swing_t)
        if alpha_base <= 5:
            return
        cx_sh = x + facing * 12
        cy_sh = y - 6
        if progress < 0.35:
            current_angle = -math.pi * 0.7
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            t_eased = 1 - (1 - t) ** 2
            current_angle = -math.pi * 0.7 + t_eased * math.pi * 1.0
        else:
            current_angle = math.pi * 0.3
        start_angle = -math.pi * 0.7
        arc_length = 36
        FX_W, FX_H = 240, 240
        fx_surf = pygame.Surface((FX_W, FX_H), pygame.SRCALPHA)
        ox, oy = FX_W // 2, FX_H // 2
        def to_fx(wx, wy):
            return (wx - cx_sh + ox, wy - cy_sh + oy)
        # ARC TRAIL — steel white with fire outer glow.
        for thickness, alpha_mult, color, radius_off in [
            (11, 0.30, _NS_kaedrin.PALETTE["fire_dark"], 4),
            (9, 0.45, _NS_kaedrin.PALETTE["fire_mid"], 2),
            (7, 0.60, _NS_kaedrin.PALETTE["fire_light"], 1),
            (5, 0.85, _NS_kaedrin.PALETTE["steel_mid"], 0),
            (3, 1.00, _NS_kaedrin.PALETTE["steel_light"], 0),
            (2, 1.00, _NS_kaedrin.PALETTE["steel_shine"], 0),
            (1, 1.00, _NS_kaedrin.PALETTE["white"], 0),
        ]:
            steps = 26
            prev = None
            for s in range(steps + 1):
                seg_t = s / steps
                seg_alpha = _NS_kaedrin._alpha(alpha_base * alpha_mult * (0.2 + 0.8 * seg_t))
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
        for r in range(14, 0, -1):
            a = _NS_kaedrin._alpha(alpha_base * (14 - r) / 14 * 1.3)
            if a > 0:
                pygame.draw.circle(fx_surf, (*_NS_kaedrin.PALETTE["fire_hot"], a), (lfx, lfy), r)
        pygame.draw.circle(fx_surf, (*_NS_kaedrin.PALETTE["steel_shine"], alpha_base), (lfx, lfy), 4)
        pygame.draw.circle(fx_surf, (*_NS_kaedrin.PALETTE["white"], alpha_base), (lfx, lfy), 2)
        # SLASH LINES (bright cut).
        for slash_i in range(3):
            slash_offset = (slash_i - 1) * 0.10
            slash_a = current_angle + slash_offset
            slash_alpha = _NS_kaedrin._alpha(alpha_base * (1 - abs(slash_offset) * 4))
            if slash_alpha <= 0:
                continue
            inner_r = arc_length - 12
            outer_r = arc_length + 14
            wx1 = cx_sh + int(math.cos(slash_a) * inner_r) * facing
            wy1 = cy_sh + int(math.sin(slash_a) * inner_r)
            wx2 = cx_sh + int(math.cos(slash_a) * outer_r) * facing
            wy2 = cy_sh + int(math.sin(slash_a) * outer_r)
            p1 = to_fx(wx1, wy1)
            p2 = to_fx(wx2, wy2)
            pygame.draw.line(fx_surf, (*_NS_kaedrin.PALETTE["white"], slash_alpha), p1, p2, 5 - slash_i)
            pygame.draw.line(fx_surf, (*_NS_kaedrin.PALETTE["steel_shine"], slash_alpha), p1, p2, 1)
        # SPARKS + FIRE EMBERS.
        for i in range(18):
            spark_seed = i * 0.7 + progress * 4
            spark_a = current_angle + math.sin(spark_seed) * 0.6
            spark_r = arc_length + 6 + (i % 4) * 6 + int(swing_t * 12)
            wspx = cx_sh + int(math.cos(spark_a) * spark_r) * facing
            wspy = cy_sh + int(math.sin(spark_a) * spark_r)
            spx, spy = to_fx(wspx, wspy)
            spark_alpha = _NS_kaedrin._alpha(alpha_base * (0.7 + (i % 3) * 0.1))
            tail_wx = wspx - int(math.cos(spark_a) * 5) * facing
            tail_wy = wspy - int(math.sin(spark_a) * 5)
            tfx, tfy = to_fx(tail_wx, tail_wy)
            pygame.draw.line(fx_surf, (*_NS_kaedrin.PALETTE["fire_mid"], spark_alpha), (tfx, tfy), (spx, spy), 2)
            pygame.draw.rect(fx_surf, (*_NS_kaedrin.PALETTE["fire_hot"], spark_alpha), (spx, spy, 2, 2))
            pygame.draw.rect(fx_surf, (*_NS_kaedrin.PALETTE["fire_shine"], spark_alpha), (spx, spy, 1, 1))
        # IMPACT BURST.
        if 0.55 < progress < 0.72:
            impact_t = (progress - 0.55) / 0.17
            impact_alpha = _NS_kaedrin._alpha(240 * (1 - impact_t))
            if impact_alpha > 0:
                impact_wx = cx_sh + int(math.cos(math.pi * 0.2) * (arc_length + 10)) * facing
                impact_wy = cy_sh + int(math.sin(math.pi * 0.2) * (arc_length + 10))
                ifx, ify = to_fx(impact_wx, impact_wy)
                for burst_r in range(int(8 + impact_t * 20), 0, -2):
                    a = _NS_kaedrin._alpha(impact_alpha * (22 - burst_r) / 22)
                    if a > 0:
                        pygame.draw.circle(fx_surf, (*_NS_kaedrin.PALETTE["fire_light"], a), (ifx, ify), burst_r)
                for i in range(12):
                    a_burst = i * math.pi / 6
                    bx = ifx + int(math.cos(a_burst) * (10 + impact_t * 14))
                    by = ify + int(math.sin(a_burst) * (10 + impact_t * 14))
                    pygame.draw.line(fx_surf, (*_NS_kaedrin.PALETTE["fire_hot"], impact_alpha), (ifx, ify), (bx, by), 2)
                    pygame.draw.rect(fx_surf, (*_NS_kaedrin.PALETTE["fire_shine"], impact_alpha), (bx, by, 2, 2))
                    pygame.draw.rect(fx_surf, (*_NS_kaedrin.PALETTE["white"], impact_alpha), (bx, by, 1, 1))
        surface.blit(fx_surf, (cx_sh - ox, cy_sh - oy))
    # ================= AMBIENT / GROUND =================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((150, 32), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 16 - radius, 130 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (10, 3, 5, 180), (5, 9, 140, 14))
        pygame.draw.ellipse(shadow, (100, 25, 20, 130), (12, 11, 126, 10))
        surface.blit(shadow, (x - 75, y - 16))
    def _draw_fire_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_kaedrin._alpha((90 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_kaedrin._aacircle(aura, (*_NS_kaedrin.PALETTE["fire_dark"], alpha), (120, 100), radius)
        for radius in range(55, 5, -3):
            alpha = _NS_kaedrin._alpha((55 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_kaedrin._aacircle(aura, (*_NS_kaedrin.PALETTE["fire_mid"], alpha), (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))
        # Floating fire embers.
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            sy -= int((phase * 8 + i * 5) % 22)
            color = _NS_kaedrin.PALETTE["fire_mid"] if i % 2 == 0 else _NS_kaedrin.PALETTE["fire_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kaedrin.PALETTE["fire_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 56), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_kaedrin.PALETTE["fire_darkest"], 200), (5, 18, 170, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_kaedrin.PALETTE["fire_dark"], 220), (14, 20, 152, 24), 2)
        pygame.draw.ellipse(ring, (*_NS_kaedrin.PALETTE["fire_mid"], 180), (25, 22, 130, 20), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 90 + int(math.cos(angle) * 74)
            y1 = 32 + int(math.sin(angle) * 12)
            pygame.draw.rect(ring, _NS_kaedrin.PALETTE["fire_hot"], (x1, y1, 2, 2))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_kaedrin.PALETTE["fire_hot"], _NS_kaedrin._alpha(150 * pulse)),
                                (15, 12, 150, 40), 1)
        surface.blit(ring, (x - 90, y - 28))
    def _draw_hover_particles(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Fire embers rising below."""
        strength = 1.5 if intense else 1.0
        for i, offset in enumerate((-24, -14, -4, 6, 16, 26)):
            t = (phase * 0.5 + i * 0.15) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 22)
            alpha = _NS_kaedrin._alpha(200 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_kaedrin._aacircle(surface, (*_NS_kaedrin.PALETTE["fire_dark"], alpha), (sx, sy), 3)
            _NS_kaedrin._aacircle(surface, (*_NS_kaedrin.PALETTE["fire_mid"], alpha), (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_kaedrin.PALETTE["fire_hot"], alpha), (sx, sy - 1, 1, 1))
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_kaedrin._alpha(160 - i * 30)
                if alpha <= 0:
                    continue
                _NS_kaedrin._aacircle(surface, (*_NS_kaedrin.PALETTE["fire_dark"], alpha),
                                      (sx, sy), max(2, 6 - i))
                _NS_kaedrin._aacircle(surface, (*_NS_kaedrin.PALETTE["fire_mid"], alpha),
                                      (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_kaedrin.PALETTE["fire_hot"], alpha),
                                 (sx, sy - 1, 2, 1))
    # ================= SKILL Q — EMBER SPEAR (projectile) =================
    def _draw_ember_spear_ground(surface, boss, x, y, timer, phase):
        """Small burn mark at target."""
        tx, ty = _NS_kaedrin._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.4:
            burn_t = (progress - 0.4) / 0.6
            r = int(30 * min(1.0, burn_t * 3))
            if r > 3:
                pygame.draw.ellipse(surface, (*_NS_kaedrin.PALETTE["fire_darkest"], 200),
                                    (tx - r, ty - r // 3, r * 2, r * 2 // 3))
                pygame.draw.ellipse(surface, (*_NS_kaedrin.PALETTE["fire_dark"], 170),
                                    (tx - r + 3, ty - r // 3 + 2, r * 2 - 6, r * 2 // 3 - 4))
    def _draw_ember_spear_projectile(surface, boss, x, y, timer, phase):
        """Spiritual spear of fire flying to target."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kaedrin._target_position(boss, x, y)
        if progress < 0.2:
            # Charging spear on hand.
            t = progress / 0.2
            hand_x = x + facing * 28
            hand_y = y - 6
            spear_len = int(t * 20)
            for i in range(spear_len):
                ratio = i / max(1, spear_len)
                px = hand_x + int(math.cos(0) * i) * facing
                py = hand_y
                _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["fire_dark"], (px, py), 3)
                _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["fire_mid"], (px, py), 2)
                pygame.draw.rect(surface, _NS_kaedrin.PALETTE["fire_hot"], (px, py, 1, 1))
        else:
            # Spear projectile.
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 32
            start_y = y - 6
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Direction vector.
            dx = tx - start_x
            dy = ty - start_y
            length = math.hypot(dx, dy) or 1
            ux = dx / length
            uy = dy / length
            # Spear body (elongated).
            spear_len = 24
            head_x = bx
            head_y = by
            tail_x = int(bx - ux * spear_len)
            tail_y = int(by - uy * spear_len)
            # Trail comet (behind tail).
            for i in range(8):
                trail_t = max(0.0, t - i * 0.05)
                if trail_t <= 0:
                    continue
                tpx = int(start_x + (tx - start_x) * trail_t - ux * spear_len)
                tpy = int(start_y + (ty - start_y) * trail_t - uy * spear_len)
                alpha = _NS_kaedrin._alpha(200 - i * 25)
                size = max(1, 6 - i)
                _NS_kaedrin._aacircle(surface, (*_NS_kaedrin.PALETTE["fire_dark"], alpha), (tpx, tpy), size)
                _NS_kaedrin._aacircle(surface, (*_NS_kaedrin.PALETTE["fire_mid"], alpha), (tpx, tpy), max(1, size - 1))
                pygame.draw.rect(surface, (*_NS_kaedrin.PALETTE["fire_hot"], alpha), (tpx, tpy, 1, 1))
            # Spear shaft (line with glow).
            for thickness, color in [
                (6, _NS_kaedrin.PALETTE["fire_darkest"]),
                (4, _NS_kaedrin.PALETTE["fire_dark"]),
                (3, _NS_kaedrin.PALETTE["fire_mid"]),
                (2, _NS_kaedrin.PALETTE["fire_light"]),
                (1, _NS_kaedrin.PALETTE["fire_hot"]),
            ]:
                pygame.draw.line(surface, color, (tail_x, tail_y), (head_x, head_y), thickness)
            # Spearhead (triangle at tip).
            perp_x = -uy
            perp_y = ux
            tip_x = int(head_x + ux * 6)
            tip_y = int(head_y + uy * 6)
            side1 = (int(head_x + perp_x * 4), int(head_y + perp_y * 4))
            side2 = (int(head_x - perp_x * 4), int(head_y - perp_y * 4))
            _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["fire_darkest"],
                              [(tip_x + 1, tip_y + 1), (side1[0] + 1, side1[1] + 1), (side2[0] + 1, side2[1] + 1)])
            _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["fire_dark"], [(tip_x, tip_y), side1, side2])
            _NS_kaedrin._poly(surface, _NS_kaedrin.PALETTE["fire_mid"], [
                (tip_x, tip_y),
                (int((tip_x + side1[0]) / 2), int((tip_y + side1[1]) / 2)),
                (int((tip_x + side2[0]) / 2), int((tip_y + side2[1]) / 2)),
            ])
            pygame.draw.rect(surface, _NS_kaedrin.PALETTE["fire_shine"], (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_kaedrin.PALETTE["white"], (tip_x, tip_y, 1, 1))
            # Impact splash.
            if t > 0.9:
                st = (t - 0.9) / 0.1
                radius = int(10 + st * 20)
                alpha = _NS_kaedrin._alpha(240 * (1 - st))
                _NS_kaedrin._aacircle(surface, (*_NS_kaedrin.PALETTE["fire_dark"], alpha), (tx, ty), radius, 3)
                _NS_kaedrin._aacircle(surface, (*_NS_kaedrin.PALETTE["fire_mid"], alpha), (tx, ty), max(1, radius - 4), 2)
                _NS_kaedrin._aacircle(surface, (*_NS_kaedrin.PALETTE["fire_hot"], alpha), (tx, ty), max(1, radius - 8), 1)
                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface, (*_NS_kaedrin.PALETTE["fire_hot"], alpha), (ex, ey, 2, 2))
                    pygame.draw.rect(surface, (*_NS_kaedrin.PALETTE["fire_shine"], alpha), (ex, ey, 1, 1))
    # ================= SKILL W — INNER FIRE (self buff, flames around body) =================
    def _draw_inner_fire_flames(surface, boss, x, y, timer, phase):
        """Fire pillar around body."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        intensity = math.sin(progress * math.pi)
        # Rising flames all around boss body.
        FX_W, FX_H = 160, 180
        fx_surf = pygame.Surface((FX_W, FX_H), pygame.SRCALPHA)
        ox, oy = FX_W // 2, FX_H // 2
        # Ring of flame columns.
        num_flames = 12
        for i in range(num_flames):
            angle = i * math.pi * 2 / num_flames
            base_x = ox + int(math.cos(angle) * 24)
            base_y = oy + int(math.sin(angle) * 12) + 10
            # Rising flame layers.
            for layer in range(8):
                layer_t = (phase * 0.6 + i * 0.15 + layer * 0.1) % 1.0
                flame_y = base_y - int(layer_t * 55)
                flame_r = int(4 + layer_t * 4)
                flame_alpha = _NS_kaedrin._alpha(220 * (1 - layer_t) * intensity)
                if flame_alpha <= 0:
                    continue
                # Multi-layer color.
                pygame.draw.circle(fx_surf, (*_NS_kaedrin.PALETTE["fire_darkest"], flame_alpha),
                                   (base_x, flame_y), flame_r + 1)
                pygame.draw.circle(fx_surf, (*_NS_kaedrin.PALETTE["fire_dark"], flame_alpha),
                                   (base_x, flame_y), flame_r)
                pygame.draw.circle(fx_surf, (*_NS_kaedrin.PALETTE["fire_mid"], flame_alpha),
                                   (base_x, flame_y - 1), max(1, flame_r - 1))
                pygame.draw.circle(fx_surf, (*_NS_kaedrin.PALETTE["fire_hot"], flame_alpha),
                                   (base_x, flame_y - 2), max(1, flame_r - 3))
                if layer < 3:
                    pygame.draw.rect(fx_surf, (*_NS_kaedrin.PALETTE["fire_shine"], flame_alpha),
                                     (base_x, flame_y - 2, 1, 1))
        # Sparks rising all around.
        for i in range(20):
            spark_t = (phase * 0.8 + i * 0.1) % 1.0
            spark_a = i * math.pi / 10
            spark_r = int(20 + math.sin(phase + i) * 8)
            sx = ox + int(math.cos(spark_a) * spark_r)
            sy = oy - int(spark_t * 50) + int(math.sin(spark_a) * spark_r * 0.5)
            alpha = _NS_kaedrin._alpha(240 * (1 - spark_t) * intensity)
            pygame.draw.rect(fx_surf, (*_NS_kaedrin.PALETTE["fire_mid"], alpha), (sx, sy, 2, 2))
            pygame.draw.rect(fx_surf, (*_NS_kaedrin.PALETTE["fire_hot"], alpha), (sx, sy, 1, 1))
        surface.blit(fx_surf, (x - ox, y - oy))
    # ================= SKILL E — BLOODRAGE STRIKE (melee empowered) =================
    def _draw_bloodrage_strike(surface, boss, x, y, timer, phase):
        """Extended red slash beam from sword forward."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kaedrin._target_position(boss, x, y)
        if progress < 0.3:
            # Charge red aura around sword hand.
            t = progress / 0.3
            hand_x = x + facing * 30
            hand_y = y - 6
            cr = int(4 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_kaedrin._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_kaedrin._aacircle(surface, (*_NS_kaedrin.PALETTE["blood_dark"], alpha), (hand_x, hand_y), r)
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["blood_mid"], (hand_x, hand_y), cr - 2)
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["blood_light"], (hand_x, hand_y), max(1, cr - 4))
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["white"], (hand_x, hand_y), max(1, cr - 6))
        else:
            # LONG SLASH BEAM.
            t = (progress - 0.3) / 0.7
            intensity = math.sin(t * math.pi)
            start_x = x + facing * 34
            start_y = y - 6
            # Slash line to target.
            beam_len = int(math.hypot(tx - start_x, ty - start_y) * min(1.0, t * 2))
            dx = tx - start_x
            dy = ty - start_y
            length = math.hypot(dx, dy) or 1
            ux = dx / length
            uy = dy / length
            end_x = int(start_x + ux * beam_len)
            end_y = int(start_y + uy * beam_len)
            alpha_base = _NS_kaedrin._alpha(255 * intensity)
            # Beam shaft (multi-layer red).
            perp_x = -uy
            perp_y = ux
            for width, color in [
                (10, _NS_kaedrin.PALETTE["blood_dark"]),
                (7, _NS_kaedrin.PALETTE["blood_mid"]),
                (5, _NS_kaedrin.PALETTE["blood_light"]),
                (3, _NS_kaedrin.PALETTE["fire_hot"]),
                (1, _NS_kaedrin.PALETTE["white"]),
            ]:
                FX_W, FX_H = 400, 200
                fx_surf = pygame.Surface((FX_W, FX_H), pygame.SRCALPHA)
                ox_l, oy_l = 20, FX_H // 2
                # Beam quad shape.
                a1 = (ox_l + int(perp_x * width), oy_l + int(perp_y * width))
                a2 = (ox_l - int(perp_x * width), oy_l - int(perp_y * width))
                b1 = (ox_l + int(ux * beam_len) + int(perp_x * width),
                      oy_l + int(uy * beam_len) + int(perp_y * width))
                b2 = (ox_l + int(ux * beam_len) - int(perp_x * width),
                      oy_l + int(uy * beam_len) - int(perp_y * width))
                pygame.draw.polygon(fx_surf, (*color, alpha_base), [a1, b1, b2, a2])
                surface.blit(fx_surf, (start_x - ox_l, start_y - oy_l))
            # Sparks along beam.
            for i in range(int(beam_len / 8)):
                sp_t = i * 8 / max(1, beam_len)
                spx = int(start_x + ux * sp_t * beam_len) + int(math.sin(phase * 5 + i) * 4)
                spy = int(start_y + uy * sp_t * beam_len) + int(math.cos(phase * 5 + i) * 4)
                sp_alpha = _NS_kaedrin._alpha(alpha_base * 0.9)
                pygame.draw.rect(surface, (*_NS_kaedrin.PALETTE["blood_light"], sp_alpha), (spx, spy, 2, 2))
                pygame.draw.rect(surface, (*_NS_kaedrin.PALETTE["white"], sp_alpha), (spx, spy, 1, 1))
            # Impact at target.
            if t > 0.4:
                imp_alpha = _NS_kaedrin._alpha(240 * intensity)
                for r in range(20, 0, -2):
                    a = _NS_kaedrin._alpha(imp_alpha * (20 - r) / 20)
                    _NS_kaedrin._aacircle(surface, (*_NS_kaedrin.PALETTE["blood_mid"], a), (end_x, end_y), r)
                _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["blood_light"], (end_x, end_y), 6)
                _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["white"], (end_x, end_y), 2)
                for i in range(10):
                    ang = i * math.pi / 5
                    ex = end_x + int(math.cos(ang) * 16)
                    ey = end_y + int(math.sin(ang) * 16)
                    pygame.draw.line(surface, (*_NS_kaedrin.PALETTE["blood_light"], imp_alpha),
                                     (end_x, end_y), (ex, ey), 2)
                    pygame.draw.rect(surface, (*_NS_kaedrin.PALETTE["white"], imp_alpha), (ex, ey, 1, 1))
    # ================= SKILL R — LIFE CLEAVE (giant purple beam) =================
    def _draw_lifecleave_ground(surface, boss, x, y, timer, phase):
        """Purple burning trail on ground."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.3:
            trail_len = int(240 * min(1.0, (progress - 0.3) / 0.7))
            start_x = x + facing * 32
            start_y = y + 20
            for i in range(0, trail_len, 6):
                px = start_x + facing * i
                py = start_y + int(math.sin(phase * 3 + i * 0.1) * 3)
                r = int(6 + math.sin(phase * 2 + i * 0.05) * 2)
                pygame.draw.ellipse(surface, (*_NS_kaedrin.PALETTE["demon_darkest"], 200),
                                    (px - r, py - r // 2, r * 2, r))
                pygame.draw.ellipse(surface, (*_NS_kaedrin.PALETTE["demon_dark"], 180),
                                    (px - r + 1, py - r // 2 + 1, r * 2 - 2, r - 2))
    def _draw_lifecleave_beam(surface, boss, x, y, timer, phase):
        """Massive purple energy beam from sword."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kaedrin._target_position(boss, x, y)
        if progress < 0.25:
            # Charge on sword.
            t = progress / 0.25
            hand_x = x + facing * 34
            hand_y = y - 6
            cr = int(6 + t * 14)
            for r in range(cr + 8, 0, -1):
                alpha = _NS_kaedrin._alpha(200 * (cr + 8 - r) / (cr + 8))
                _NS_kaedrin._aacircle(surface, (*_NS_kaedrin.PALETTE["demon_dark"], alpha), (hand_x, hand_y), r)
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["demon_darkest"], (hand_x, hand_y), cr)
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["demon_mid"], (hand_x, hand_y), cr - 3)
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["demon_light"], (hand_x, hand_y), max(1, cr - 6))
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["demon_hot"], (hand_x, hand_y), max(1, cr - 9))
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["white"], (hand_x, hand_y), max(1, cr - 11))
        else:
            # BEAM!
            t = (progress - 0.25) / 0.75
            intensity = math.sin(t * math.pi) if t < 0.85 else 1.0
            if t > 0.85:
                intensity = (1 - t) / 0.15
            start_x = x + facing * 36
            start_y = y - 6
            dx = tx - start_x
            dy = ty - start_y
            length = math.hypot(dx, dy) or 1
            ux = dx / length
            uy = dy / length
            perp_x = -uy
            perp_y = ux
            beam_len = int(length * min(1.0, t * 3))
            end_x = int(start_x + ux * beam_len)
            end_y = int(start_y + uy * beam_len)
            alpha_base = _NS_kaedrin._alpha(255 * intensity)
            # HUGE beam quad — multiple layers.
            FX_W, FX_H = 500, 200
            fx_surf = pygame.Surface((FX_W, FX_H), pygame.SRCALPHA)
            ox_l, oy_l = 30, FX_H // 2
            # Wave undulation.
            for width_layer, color in [
                (16, _NS_kaedrin.PALETTE["demon_darkest"]),
                (12, _NS_kaedrin.PALETTE["demon_dark"]),
                (9, _NS_kaedrin.PALETTE["demon_mid"]),
                (6, _NS_kaedrin.PALETTE["demon_light"]),
                (4, _NS_kaedrin.PALETTE["demon_hot"]),
                (2, _NS_kaedrin.PALETTE["demon_shine"]),
                (1, _NS_kaedrin.PALETTE["white"]),
            ]:
                # Undulating beam via multiple polygon segments.
                seg_count = 12
                for seg_i in range(seg_count):
                    s1 = seg_i / seg_count
                    s2 = (seg_i + 1) / seg_count
                    wave1 = math.sin(phase * 4 + seg_i * 0.5) * 3
                    wave2 = math.sin(phase * 4 + (seg_i + 1) * 0.5) * 3
                    x1 = ox_l + int(ux * s1 * beam_len)
                    y1 = oy_l + int(uy * s1 * beam_len)
                    x2 = ox_l + int(ux * s2 * beam_len)
                    y2 = oy_l + int(uy * s2 * beam_len)
                    a1 = (x1 + int(perp_x * (width_layer + wave1)), y1 + int(perp_y * (width_layer + wave1)))
                    a2 = (x1 - int(perp_x * (width_layer - wave1)), y1 - int(perp_y * (width_layer - wave1)))
                    b1 = (x2 + int(perp_x * (width_layer + wave2)), y2 + int(perp_y * (width_layer + wave2)))
                    b2 = (x2 - int(perp_x * (width_layer - wave2)), y2 - int(perp_y * (width_layer - wave2)))
                    pygame.draw.polygon(fx_surf, (*color, alpha_base), [a1, b1, b2, a2])
            surface.blit(fx_surf, (start_x - ox_l, start_y - oy_l))
            # Sparks along beam.
            for i in range(int(beam_len / 6)):
                sp_t = i * 6 / max(1, beam_len)
                spx = int(start_x + ux * sp_t * beam_len) + int(math.sin(phase * 6 + i) * 8)
                spy = int(start_y + uy * sp_t * beam_len) + int(math.cos(phase * 6 + i) * 8)
                sp_alpha = _NS_kaedrin._alpha(alpha_base * 0.9)
                pygame.draw.rect(surface, (*_NS_kaedrin.PALETTE["demon_hot"], sp_alpha), (spx, spy, 2, 2))
                pygame.draw.rect(surface, (*_NS_kaedrin.PALETTE["white"], sp_alpha), (spx, spy, 1, 1))
            # Impact explosion.
            imp_alpha = _NS_kaedrin._alpha(240 * intensity)
            imp_r = int(20 + t * 20)
            for r in range(imp_r + 4, 0, -2):
                a = _NS_kaedrin._alpha(imp_alpha * (imp_r + 4 - r) / (imp_r + 4))
                _NS_kaedrin._aacircle(surface, (*_NS_kaedrin.PALETTE["demon_mid"], a), (end_x, end_y), r)
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["demon_light"], (end_x, end_y), 10)
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["demon_hot"], (end_x, end_y), 6)
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["demon_shine"], (end_x, end_y), 3)
            _NS_kaedrin._aacircle(surface, _NS_kaedrin.PALETTE["white"], (end_x, end_y), 1)
            for i in range(12):
                ang = i * math.pi / 6
                ex = end_x + int(math.cos(ang) * 24)
                ey = end_y + int(math.sin(ang) * 24)
                pygame.draw.line(surface, (*_NS_kaedrin.PALETTE["demon_light"], imp_alpha),
                                 (end_x, end_y), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_kaedrin.PALETTE["demon_shine"], imp_alpha), (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_kaedrin.PALETTE["white"], imp_alpha), (ex, ey, 1, 1))



# ====================================================================
# MORVAETH (MIRRORBORN) - Mini Boss
# ====================================================================

class _NS_morvaeth:
    """Namespace morvaeth - demon marauder with reflection powers."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Dark demon armor (body)
        "armor_darkest": (8, 8, 15),
        "armor_dark": (25, 22, 40),
        "armor_mid": (55, 50, 80),
        "armor_light": (105, 95, 145),
        "armor_edge": (160, 150, 200),
        "armor_shine": (215, 210, 245),
        # Demon skin (dark grey-purple)
        "skin_darkest": (15, 12, 22),
        "skin_dark": (40, 30, 55),
        "skin_mid": (85, 65, 105),
        "skin_light": (150, 120, 180),
        # Purple magic (main FX color)
        "purple_darkest": (25, 5, 45),
        "purple_dark": (75, 20, 120),
        "purple_mid": (155, 50, 210),
        "purple_light": (215, 120, 250),
        "purple_hot": (245, 195, 255),
        "purple_shine": (255, 240, 255),
        # Cyan energy (swords, wings, blue accents)
        "cyan_darkest": (5, 30, 45),
        "cyan_dark": (15, 90, 130),
        "cyan_mid": (40, 180, 220),
        "cyan_light": (130, 235, 255),
        "cyan_hot": (200, 250, 255),
        "cyan_shine": (255, 255, 255),
        # Wing crystal (dark blue-purple gradient)
        "wing_darkest": (12, 8, 25),
        "wing_dark": (35, 25, 65),
        "wing_mid": (75, 55, 130),
        "wing_light": (140, 110, 200),
        "wing_edge": (200, 170, 240),
        # Red demon glow (eyes, chest gem)
        "demon_eye_dark": (85, 8, 20),
        "demon_eye_mid": (215, 30, 45),
        "demon_eye_light": (255, 100, 105),
        "demon_eye_glow": (255, 200, 200),
        "eye_socket": (5, 3, 10),
        # Horns (dark curved)
        "horn_darkest": (10, 5, 15),
        "horn_dark": (35, 20, 45),
        "horn_mid": (75, 55, 90),
        "horn_light": (140, 120, 160),
        # Mist / shadow
        "mist_dark": (20, 15, 35),
        "mist_mid": (50, 35, 80),
        "mist_light": (120, 90, 170),
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
        color = _NS_morvaeth._clamp(color)
        if _NS_morvaeth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_morvaeth._clamp(color)
        if _NS_morvaeth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_morvaeth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ================= ENTRY POINT =================
    def draw_morvaeth(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_morvaeth._detect_moving(boss)
        _NS_morvaeth._update_mrv_attack_anim(boss)
        attacking = (
            getattr(boss, "_mrv_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        _NS_morvaeth._draw_demon_aura(surface, x, y, pulse)
        _NS_morvaeth._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX behind body.
        if active_skill == "e":
            _NS_morvaeth._draw_demonform_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morvaeth._draw_sunder_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_morvaeth._draw_conjure_portal_ground(surface, boss, x, y, skill_timer, pulse)
        # Illusion clone (behind main body if active).
        if active_skill == "w":
            _NS_morvaeth._draw_conjured_clone(surface, boss, x, y, skill_timer, pulse)
        # Body — demonform enlarges it.
        is_demonform = (active_skill == "e")
        e_scale = 1.0
        if is_demonform:
            e_dur = 90
            e_prog = max(0.0, min(1.0, 1 - skill_timer / e_dur))
            e_scale = 1.0 + 0.15 * math.sin(e_prog * math.pi)
        if attacking:
            _NS_morvaeth._draw_mrv_attack(surface, boss, x, y, is_demonform, e_scale)
        elif moving:
            _NS_morvaeth._draw_mrv_walk(surface, boss, x, y, is_demonform, e_scale)
        else:
            _NS_morvaeth._draw_mrv_idle(surface, boss, x, y, is_demonform, e_scale)
        # Demonform aura overlay (over body).
        if active_skill == "e":
            _NS_morvaeth._draw_demonform_aura(surface, boss, x, y, skill_timer, pulse)
        # Foreground FX.
        if active_skill == "q":
            _NS_morvaeth._draw_mirror_lance(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morvaeth._draw_soul_sunder_beam(surface, boss, x, y, skill_timer, pulse)
    # ================= ANIMATION STATE =================
    def _update_mrv_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_mrv_previous_timer", 0))
        active = bool(getattr(boss, "_mrv_attack_active", False))
        if not active and previous > timer and previous >= cooldown - 2:
            boss._mrv_attack_active = True
            boss._mrv_attack_frame = 0
            active = True
        elif active:
            boss._mrv_attack_frame = int(getattr(boss, "_mrv_attack_frame", 0)) + 1
            if boss._mrv_attack_frame >= cooldown:
                boss._mrv_attack_active = False
                boss._mrv_attack_frame = 0
                active = False
        boss._mrv_previous_timer = timer
        boss._mrv_attack_progress = (
            min(1.0, getattr(boss, "_mrv_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_mrv_last_x"):
            boss._mrv_last_x = boss.x
            boss._mrv_last_y = boss.y
            return False
        dx = abs(boss.x - boss._mrv_last_x)
        dy = abs(boss.y - boss._mrv_last_y)
        boss._mrv_last_x = boss.x
        boss._mrv_last_y = boss.y
        return dx + dy > 0.3
    # ================= POSE ROUTERS =================
    def _draw_mrv_idle(surface, boss, x, y, demonform=False, scale=1.0):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_morvaeth._draw_shadow(surface, x, y + 50)
        _NS_morvaeth._draw_hover_particles(surface, x, y + 44, boss.pulse)
        _NS_morvaeth._draw_mrv_body(surface, x, y + bob, boss.direction, boss.pulse, "idle",
                                   demonform=demonform, scale=scale)
    def _draw_mrv_walk(surface, boss, x, y, demonform=False, scale=1.0):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 6)
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_morvaeth._draw_shadow(surface, x + sway, y + 50)
        _NS_morvaeth._draw_hover_particles(surface, x + sway, y + 44, phase, trail=True, facing=boss.direction)
        _NS_morvaeth._draw_mrv_body(surface, x + sway, y + bob, boss.direction, phase, "walk",
                                   demonform=demonform, scale=scale)
    def _draw_mrv_attack(surface, boss, x, y, demonform=False, scale=1.0):
        progress = getattr(boss, "_mrv_attack_progress", None)
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
        _NS_morvaeth._draw_shadow(surface, x + lunge, y + 50)
        _NS_morvaeth._draw_hover_particles(surface, x + lunge, y + 44, boss.pulse, intense=True)
        _NS_morvaeth._draw_mrv_body(surface, x + lunge, y - lift, boss.direction, boss.pulse, "attack",
                                   attack_progress=progress, demonform=demonform, scale=scale)
        _NS_morvaeth._draw_dual_sword_swing(surface, boss, x + lunge, y - lift, progress)
    # ================= BODY =================
    def _draw_mrv_body(surface, cx, cy, facing, phase, action, attack_progress=0,
                      demonform=False, scale=1.0, is_clone=False):
        """Master body draw. is_clone=True renders in cyan-only tint."""
        # Wings FIRST (behind body).
        _NS_morvaeth._draw_crystal_wings(surface, cx, cy - 4, facing, phase, action, demonform,
                                         is_clone=is_clone)
        # Legs.
        _NS_morvaeth._draw_demon_legs(surface, cx, cy + 10, facing, phase, action, is_clone=is_clone)
        # Torso armor.
        _NS_morvaeth._draw_demon_torso(surface, cx, cy, facing, phase, demonform, is_clone=is_clone)
        # Head with big horns.
        _NS_morvaeth._draw_horned_head(surface, cx, cy - 20, facing, phase, action, demonform,
                                       is_clone=is_clone)
        # Back sword arm.
        _NS_morvaeth._draw_sword_arm(surface, cx, cy - 2, facing, phase, action, attack_progress,
                                     back=True, is_clone=is_clone)
        # Front sword arm.
        _NS_morvaeth._draw_sword_arm(surface, cx, cy - 2, facing, phase, action, attack_progress,
                                     back=False, is_clone=is_clone)
    def _draw_crystal_wings(surface, cx, cy, facing, phase, action, demonform, is_clone=False):
        """Big crystal wings behind — like sharp shards spreading."""
        beat = math.sin(phase * 1.5) * 2 if action != "attack" \
            else math.sin(phase * 2.5) * 3
        wing_scale = 1.2 if demonform else 1.0
        blade_color_light = "cyan_light" if not is_clone else "cyan_light"
        blade_color_edge = "cyan_hot" if not is_clone else "cyan_hot"
        for side_i, (side, size_mult, alpha_mult) in enumerate([
            (-1, 1.0 * wing_scale, 1.0),
            (1, 0.85 * wing_scale, 0.85),
        ]):
            base_x = cx - facing * 4
            base_y = cy - 4
            # Multiple wing shards (like frozen wings, sharp).
            num_shards = 5
            for shard_i in range(num_shards):
                shard_angle = math.pi * 0.5 + (shard_i / (num_shards - 1)) * math.pi * 0.7 - math.pi * 0.35
                shard_angle *= side
                shard_angle -= math.radians(beat)
                shard_len = int((30 + shard_i * 4) * size_mult)
                if shard_i == 2:  # middle longer
                    shard_len = int(38 * size_mult)
                tip_x = base_x + int(math.cos(shard_angle) * shard_len) * (-facing)
                tip_y = base_y - int(math.sin(shard_angle) * shard_len)
                # Shard perpendicular width.
                perp_a = shard_angle + math.pi / 2
                shard_w = int(6 * size_mult)
                mid_x = base_x + int(math.cos(shard_angle) * shard_len * 0.5) * (-facing)
                mid_y = base_y - int(math.sin(shard_angle) * shard_len * 0.5)
                w1 = (mid_x + int(math.cos(perp_a) * shard_w) * (-facing),
                      mid_y - int(math.sin(perp_a) * shard_w))
                w2 = (mid_x - int(math.cos(perp_a) * shard_w) * (-facing),
                      mid_y + int(math.sin(perp_a) * shard_w))
                # Shard body.
                _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["shadow_deep"], [
                    (base_x + 2, base_y + 2),
                    (w1[0] + 2, w1[1] + 2),
                    (tip_x + 2, tip_y + 2),
                    (w2[0] + 2, w2[1] + 2),
                ])
                _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["wing_darkest"], [
                    (base_x, base_y), w1, (tip_x, tip_y), w2,
                ])
                _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["wing_dark"], [
                    (base_x, base_y),
                    (int(w1[0] * 0.8 + base_x * 0.2), int(w1[1] * 0.8 + base_y * 0.2)),
                    (tip_x, tip_y),
                    (int(w2[0] * 0.8 + base_x * 0.2), int(w2[1] * 0.8 + base_y * 0.2)),
                ])
                # Mid highlight.
                _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["wing_mid"], [
                    (base_x, base_y),
                    (int(w1[0] * 0.7 + mid_x * 0.3), int(w1[1] * 0.7 + mid_y * 0.3)),
                    (tip_x, tip_y),
                ])
                _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["wing_light"], [
                    (base_x, base_y),
                    (int((base_x + tip_x) / 2), int((base_y + tip_y) / 2)),
                    (tip_x, tip_y),
                ])
                # Cyan glowing edge (from base to tip).
                pygame.draw.line(surface, _NS_morvaeth.PALETTE["cyan_dark"],
                                 (base_x, base_y), (tip_x, tip_y), 2)
                pygame.draw.line(surface, _NS_morvaeth.PALETTE[blade_color_light],
                                 (base_x, base_y), (tip_x, tip_y), 1)
                # Tip sparkle.
                pygame.draw.rect(surface, _NS_morvaeth.PALETTE[blade_color_edge], (tip_x, tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_morvaeth.PALETTE["white"], (tip_x, tip_y, 1, 1))
                # Small purple glow at base.
                _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["purple_mid"], (base_x, base_y), 2)
    def _draw_demon_legs(surface, cx, cy, facing, phase, action, is_clone=False):
        """Muscular legs with armored knee/foot."""
        leg_bob = math.sin(phase * 0.8) * 2 if action != "walk" \
            else math.sin(phase * 1.5) * 4
        for side in (-1, 1):
            hip_x = cx + side * 6
            hip_y = cy - 2
            knee_x = cx + side * 8
            knee_y = cy + 8 + int(leg_bob * side * 0.5)
            foot_x = cx + side * 6
            foot_y = cy + 18 + int(leg_bob * side * 0.3)
            # Thigh (armored).
            _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["shadow_deep"],
                                 (hip_x + 1, hip_y + 1), (knee_x + 1, knee_y + 1), 7)
            _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_darkest"],
                                 (hip_x, hip_y), (knee_x, knee_y), 7)
            _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_dark"],
                                 (hip_x, hip_y), (knee_x, knee_y), 5)
            _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_mid"],
                                 (hip_x, hip_y), (knee_x, knee_y), 3)
            _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_light"],
                                 (hip_x - 1, hip_y), (knee_x - 1, knee_y), 1)
            # Knee spike.
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["armor_darkest"], (knee_x, knee_y), 4)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["armor_dark"], (knee_x, knee_y), 3)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["armor_mid"], (knee_x - 1, knee_y - 1), 2)
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["cyan_light"], (knee_x, knee_y, 1, 1))
            # Small knee spike going out.
            _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["horn_dark"], [
                (knee_x + side * 3, knee_y),
                (knee_x + side * 6, knee_y - 2),
                (knee_x + side * 3, knee_y + 2),
            ])
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["cyan_hot"], (knee_x + side * 5, knee_y - 1, 1, 1))
            # Shin.
            _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_darkest"],
                                 (knee_x, knee_y), (foot_x, foot_y), 6)
            _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_dark"],
                                 (knee_x, knee_y), (foot_x, foot_y), 4)
            _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_mid"],
                                 (knee_x - 1, knee_y), (foot_x - 1, foot_y), 1)
            # Foot claw.
            _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["shadow_deep"], [
                (foot_x - 4 + 1, foot_y - 1 + 1),
                (foot_x + 4 + 1, foot_y - 1 + 1),
                (foot_x + 3 + 1, foot_y + 2 + 1),
                (foot_x - 3 + 1, foot_y + 2 + 1),
            ])
            _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_darkest"], [
                (foot_x - 4, foot_y - 1),
                (foot_x + 4, foot_y - 1),
                (foot_x + 3, foot_y + 2),
                (foot_x - 3, foot_y + 2),
            ])
            _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_mid"], [
                (foot_x - 3, foot_y),
                (foot_x + 3, foot_y),
                (foot_x + 2, foot_y + 1),
                (foot_x - 2, foot_y + 1),
            ])
            # Claw toes.
            for cx_toe in (-3, 0, 3):
                pygame.draw.rect(surface, _NS_morvaeth.PALETTE["horn_dark"],
                                 (foot_x + cx_toe, foot_y + 2, 1, 2))
                pygame.draw.rect(surface, _NS_morvaeth.PALETTE["cyan_light"],
                                 (foot_x + cx_toe, foot_y + 3, 1, 1))
    def _draw_demon_torso(surface, cx, cy, facing, phase, demonform, is_clone=False):
        """Chest armor with red gem."""
        breath = math.sin(phase * 0.7) * 1
        # Main torso shape.
        torso_shape = [
            (cx - 14, cy - 12),
            (cx - 17, cy - 6),
            (cx - 14, cy + 2),
            (cx - 12, cy + 12),
            (cx + 12, cy + 12),
            (cx + 14, cy + 2),
            (cx + 17, cy - 6),
            (cx + 14, cy - 12),
            (cx + 6, cy - 14),
            (cx - 6, cy - 14),
        ]
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 3) for p in torso_shape])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_darkest"], torso_shape)
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_dark"], [
            (cx - 13, cy - 11),
            (cx - 15, cy - 5),
            (cx - 12, cy + 2),
            (cx - 10, cy + 11),
            (cx + 10, cy + 11),
            (cx + 12, cy + 2),
            (cx + 15, cy - 5),
            (cx + 13, cy - 11),
            (cx + 5, cy - 13),
            (cx - 5, cy - 13),
        ])
        # Muscular chest plates.
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_mid"], [
            (cx - 10, cy - 8),
            (cx - 12, cy - 3),
            (cx - 8, cy + 4),
            (cx + 8, cy + 4),
            (cx + 12, cy - 3),
            (cx + 10, cy - 8),
        ])
        # Pectoral highlights.
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_light"], [
            (cx - 8, cy - 6),
            (cx - 2, cy - 8),
            (cx - 2, cy - 3),
            (cx - 6, cy - 2),
        ])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_light"], [
            (cx + 2, cy - 8),
            (cx + 8, cy - 6),
            (cx + 6, cy - 2),
            (cx + 2, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["armor_edge"], (cx - 5, cy - 7, 2, 1))
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["armor_edge"], (cx + 3, cy - 7, 2, 1))
        # Ab plate lines.
        for i in range(3):
            ab_y = cy + i * 3
            pygame.draw.line(surface, _NS_morvaeth.PALETTE["armor_darkest"],
                             (cx - 4, ab_y), (cx + 4, ab_y), 1)
            pygame.draw.line(surface, _NS_morvaeth.PALETTE["armor_light"],
                             (cx - 3, ab_y - 1), (cx + 3, ab_y - 1), 1)
        # RED GEM in chest.
        gem_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        gem_x = cx
        gem_y = cy - 4
        gem_col_mid = "demon_eye_mid" if not is_clone else "cyan_mid"
        gem_col_light = "demon_eye_light" if not is_clone else "cyan_light"
        gem_col_glow = "demon_eye_glow" if not is_clone else "cyan_hot"
        for r in range(6, 0, -1):
            alpha = _NS_morvaeth._alpha(180 * (6 - r) / 6 * gem_pulse)
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE[gem_col_mid], alpha), (gem_x, gem_y), r)
        # Diamond gem shape.
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["shadow_deep"], [
            (gem_x, gem_y - 4),
            (gem_x + 3, gem_y),
            (gem_x, gem_y + 4),
            (gem_x - 3, gem_y),
        ])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["demon_eye_dark"] if not is_clone else _NS_morvaeth.PALETTE["cyan_dark"], [
            (gem_x, gem_y - 3),
            (gem_x + 2, gem_y),
            (gem_x, gem_y + 3),
            (gem_x - 2, gem_y),
        ])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE[gem_col_mid], [
            (gem_x, gem_y - 2),
            (gem_x + 1, gem_y),
            (gem_x, gem_y + 2),
            (gem_x - 1, gem_y),
        ])
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE[gem_col_light], (gem_x, gem_y - 1, 1, 1))
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE[gem_col_glow], (gem_x, gem_y - 1, 1, 1))
        # Shoulder pauldrons with spikes.
        for side in (-1, 1):
            sh_x = cx + side * 12
            sh_y = cy - 10
            # Base pauldron.
            _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["shadow_deep"], [
                (sh_x - 4 + 1, sh_y - 3 + 1),
                (sh_x + 4 + 1, sh_y - 3 + 1),
                (sh_x + 5 + 1, sh_y + 3 + 1),
                (sh_x - 5 + 1, sh_y + 3 + 1),
            ])
            _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_darkest"], [
                (sh_x - 4, sh_y - 3),
                (sh_x + 4, sh_y - 3),
                (sh_x + 5, sh_y + 3),
                (sh_x - 5, sh_y + 3),
            ])
            _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_dark"], [
                (sh_x - 3, sh_y - 2),
                (sh_x + 3, sh_y - 2),
                (sh_x + 4, sh_y + 2),
                (sh_x - 4, sh_y + 2),
            ])
            _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_mid"], [
                (sh_x - 2, sh_y - 1),
                (sh_x + 2, sh_y - 1),
                (sh_x + 2, sh_y + 1),
                (sh_x - 2, sh_y + 1),
            ])
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["armor_edge"], (sh_x - 1, sh_y - 1, 2, 1))
            # Pauldron spikes (2 spikes going up-out).
            for spike_off in ((-2, -5), (2, -5)):
                sp_x = sh_x + spike_off[0]
                sp_y = sh_y + spike_off[1]
                _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["horn_dark"], [
                    (sp_x - 1, sh_y - 3),
                    (sp_x + 1, sh_y - 3),
                    (sp_x, sp_y),
                ])
                pygame.draw.rect(surface, _NS_morvaeth.PALETTE["cyan_light"], (sp_x, sp_y, 1, 1))
    def _draw_horned_head(surface, cx, cy, facing, phase, action, demonform, is_clone=False):
        """Head with big curved horns and glowing red eyes."""
        # Head shape.
        head_shape = [
            (cx - 5, cy + 5),
            (cx - 6, cy),
            (cx - 5, cy - 5),
            (cx - 2, cy - 8),
            (cx + 2, cy - 8),
            (cx + 5, cy - 5),
            (cx + 6, cy),
            (cx + 5, cy + 5),
            (cx + 2, cy + 8),
            (cx - 2, cy + 8),
        ]
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 2) for p in head_shape])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["skin_darkest"], head_shape)
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["skin_dark"], [
            (cx - 4, cy + 4),
            (cx - 5, cy),
            (cx - 4, cy - 4),
            (cx - 1, cy - 7),
            (cx + 1, cy - 7),
            (cx + 4, cy - 4),
            (cx + 5, cy),
            (cx + 4, cy + 4),
            (cx + 1, cy + 7),
            (cx - 1, cy + 7),
        ])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["skin_mid"], [
            (cx - 3, cy),
            (cx - 3, cy - 3),
            (cx + 3, cy - 3),
            (cx + 3, cy),
            (cx + 2, cy + 3),
            (cx - 2, cy + 3),
        ])
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["skin_light"], (cx - 1, cy - 2, 1, 1))
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["skin_light"], (cx + 1, cy - 2, 1, 1))
        # HELM crown on top.
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["shadow_deep"], [
            (cx - 6 + 1, cy - 5 + 1),
            (cx + 6 + 1, cy - 5 + 1),
            (cx + 4 + 1, cy - 8 + 1),
            (cx - 4 + 1, cy - 8 + 1),
        ])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_darkest"], [
            (cx - 6, cy - 5),
            (cx + 6, cy - 5),
            (cx + 4, cy - 8),
            (cx - 4, cy - 8),
        ])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_dark"], [
            (cx - 5, cy - 5),
            (cx + 5, cy - 5),
            (cx + 3, cy - 7),
            (cx - 3, cy - 7),
        ])
        _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["armor_mid"], [
            (cx - 3, cy - 5),
            (cx + 3, cy - 5),
            (cx + 2, cy - 6),
            (cx - 2, cy - 6),
        ])
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["armor_edge"], (cx - 1, cy - 6, 2, 1))
        # BIG CURVED HORNS (like ram/demon horns).
        horn_scale = 1.3 if demonform else 1.0
        for side_i, side in enumerate((-1, 1)):
            # Horn base at side of head.
            base_x = cx + side * 4
            base_y = cy - 6
            # Big curved horn going up + out + back.
            segments = 5
            prev = (base_x, base_y)
            for seg in range(1, segments + 1):
                t = seg / segments
                # Curve outward and upward.
                curve_x = base_x + int(side * (4 + t * 8) * horn_scale)
                curve_y = base_y - int((6 + t * 10) * horn_scale)
                # Add slight back curl.
                curl_x = int(side * (t * t * 4))
                bx = curve_x - curl_x
                by = curve_y + int(t * t * 2)
                thickness = max(1, 5 - seg)
                _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["shadow_deep"],
                                     (prev[0] + 1, prev[1] + 1), (bx + 1, by + 1), thickness + 1)
                _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["horn_darkest"],
                                     prev, (bx, by), thickness)
                _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["horn_dark"],
                                     prev, (bx, by), max(1, thickness - 1))
                _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["horn_mid"],
                                     (prev[0] - 1, prev[1]), (bx - 1, by), max(1, thickness - 2))
                prev = (bx, by)
            # Cyan glow at horn tip.
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["cyan_light"], (prev[0], prev[1], 1, 1))
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["cyan_hot"], (prev[0], prev[1], 1, 1))
        # RED GLOWING EYES.
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        eye_col_dark = "demon_eye_dark" if not is_clone else "cyan_dark"
        eye_col_mid = "demon_eye_mid" if not is_clone else "cyan_mid"
        eye_col_light = "demon_eye_light" if not is_clone else "cyan_light"
        for eye_off in (-2, 2):
            ex = cx + eye_off
            ey = cy - 1
            for r in range(4, 0, -1):
                alpha = _NS_morvaeth._alpha(140 * (4 - r) / 4 * eye_pulse)
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE[eye_col_mid], alpha), (ex, ey), r)
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["eye_socket" if not is_clone else "cyan_darkest"], (ex - 1, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE[eye_col_dark], (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE[eye_col_mid], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE[eye_col_light], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["white"], (ex, ey, 1, 1))
        # Fanged mouth.
        if action == "attack":
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["shadow_deep"], (cx - 2, cy + 4, 5, 3))
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["demon_eye_dark"] if not is_clone else _NS_morvaeth.PALETTE["cyan_dark"], (cx - 1, cy + 4, 3, 2))
            # Fangs top.
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["horn_light"], (cx - 1, cy + 4, 1, 2))
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["horn_light"], (cx + 1, cy + 4, 1, 2))
        else:
            pygame.draw.line(surface, _NS_morvaeth.PALETTE["shadow_deep"],
                             (cx - 2, cy + 5), (cx + 2, cy + 5), 1)
            # Fang tip.
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["horn_light"], (cx - 1, cy + 5, 1, 1))
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["horn_light"], (cx + 1, cy + 5, 1, 1))
    def _draw_sword_arm(surface, cx, cy, facing, phase, action, attack_progress, back=False, is_clone=False):
        """Arm holding cyan sword."""
        arm_facing = -facing if back else facing
        # Back arm has offset angle & is behind body.
        if back:
            if action == "attack":
                if attack_progress < 0.35:
                    t = attack_progress / 0.35
                    swing_angle = -math.pi * 0.4 - t * math.pi * 0.3
                    arm_length = 22
                elif attack_progress < 0.6:
                    t = (attack_progress - 0.35) / 0.25
                    t_eased = 1 - (1 - t) ** 2
                    swing_angle = -math.pi * 0.7 + t_eased * math.pi * 0.8
                    arm_length = 22 + int(t_eased * 5)
                else:
                    t = (attack_progress - 0.6) / 0.4
                    swing_angle = math.pi * 0.1 - t * math.pi * 0.5
                    arm_length = 27 - int(t * 5)
            else:
                swing_angle = math.pi * 0.2 + math.sin(phase * 0.7) * 0.1
                arm_length = 22
        else:
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
                swing_angle = math.pi * 0.15 + math.sin(phase * 0.6) * 0.1
                arm_length = 22
        shoulder_x = cx + arm_facing * 11
        shoulder_y = cy - 4
        hand_x = shoulder_x + int(math.cos(swing_angle) * arm_length) * arm_facing
        hand_y = shoulder_y + int(math.sin(swing_angle) * arm_length)
        elbow_x = (shoulder_x + hand_x) // 2 + arm_facing * 1
        elbow_y = (shoulder_y + hand_y) // 2
        # Upper arm (armored).
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["shadow_deep"],
                             (shoulder_x + 1, shoulder_y + 1), (elbow_x + 1, elbow_y + 1), 7)
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_darkest"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 7)
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_dark"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_mid"],
                             (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 2)
        # Elbow spike.
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["armor_darkest"], (elbow_x, elbow_y), 4)
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["armor_dark"], (elbow_x, elbow_y), 3)
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["armor_mid"], (elbow_x - 1, elbow_y - 1), 2)
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["cyan_light"], (elbow_x, elbow_y, 1, 1))
        # Forearm.
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_darkest"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_dark"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_morvaeth._aaline(surface, _NS_morvaeth.PALETTE["armor_mid"],
                             (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
        # Gauntlet hand.
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["armor_darkest"], (hand_x, hand_y), 3)
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["armor_mid"], (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["cyan_light"], (hand_x, hand_y, 1, 1))
        # DUAL CYAN SWORD.
        _NS_morvaeth._draw_cyan_sword(surface, hand_x, hand_y, arm_facing, phase, swing_angle,
                                      back=back, is_clone=is_clone)
    def _draw_cyan_sword(surface, hx, hy, facing, phase, angle, back=False, is_clone=False):
        """Long cyan energy sword."""
        blade_len = 30
        tip_x = hx + int(math.cos(angle) * blade_len) * facing
        tip_y = hy + int(math.sin(angle) * blade_len)
        # Handle behind hand.
        handle_x = hx - int(math.cos(angle) * 6) * facing
        handle_y = hy - int(math.sin(angle) * 6)
        # Perpendicular for blade width.
        perp = angle + math.pi / 2
        base_w = 3
        b1 = (hx + int(math.cos(perp) * base_w),
              hy + int(math.sin(perp) * base_w))
        b2 = (hx - int(math.cos(perp) * base_w),
              hy - int(math.sin(perp) * base_w))
        # Handle guard (cross).
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["armor_darkest"],
                         (hx + int(math.cos(perp) * 5), hy + int(math.sin(perp) * 5)),
                         (hx - int(math.cos(perp) * 5), hy - int(math.sin(perp) * 5)), 3)
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["armor_dark"],
                         (hx + int(math.cos(perp) * 4), hy + int(math.sin(perp) * 4)),
                         (hx - int(math.cos(perp) * 4), hy - int(math.sin(perp) * 4)), 2)
        # Handle grip.
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["armor_darkest"],
                         (handle_x, handle_y), (hx, hy), 4)
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["armor_dark"],
                         (handle_x, handle_y), (hx, hy), 2)
        # Pommel.
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["armor_darkest"], (handle_x, handle_y), 2)
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["cyan_dark"], (handle_x, handle_y), 1)
        # BLADE (energy).
        # Outer glow layer.
        for width_g, alpha_g, color in [
            (7, 100, "cyan_dark"),
            (5, 150, "cyan_mid"),
            (3, 220, "cyan_light"),
            (2, 255, "cyan_hot"),
            (1, 255, "white"),
        ]:
            FX_W, FX_H = 100, 100
            fx_surf = pygame.Surface((FX_W, FX_H), pygame.SRCALPHA)
            ox, oy = FX_W // 2, FX_H // 2
            b1_l = (ox + int(math.cos(perp) * base_w),
                    oy + int(math.sin(perp) * base_w))
            b2_l = (ox - int(math.cos(perp) * base_w),
                    oy - int(math.sin(perp) * base_w))
            tip_l = (ox + int(math.cos(angle) * blade_len) * facing,
                     oy + int(math.sin(angle) * blade_len))
            pygame.draw.polygon(fx_surf, (*_NS_morvaeth.PALETTE[color], alpha_g),
                                [b1_l, tip_l, b2_l])
            surface.blit(fx_surf, (hx - ox, hy - oy))
        # Bright core line.
        pygame.draw.line(surface, _NS_morvaeth.PALETTE["white"], (hx, hy), (tip_x, tip_y), 1)
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["white"], (tip_x, tip_y, 1, 1))
        # Tip sparkle.
        _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["cyan_hot"], (tip_x, tip_y), 2)
        pygame.draw.rect(surface, _NS_morvaeth.PALETTE["white"], (tip_x, tip_y, 1, 1))
    # ================= MELEE SWING FX =================
    def _draw_dual_sword_swing(surface, boss, x, y, progress):
        """Dual cyan slash arc."""
        if progress < 0.30 or progress > 0.80:
            return
        facing = boss.direction
        if progress < 0.6:
            swing_t = (progress - 0.30) / 0.30
        else:
            swing_t = 1.0 - (progress - 0.6) / 0.20
        swing_t = max(0.0, min(1.0, swing_t))
        alpha_base = _NS_morvaeth._alpha(255 * swing_t)
        if alpha_base <= 5:
            return
        cx_sh = x + facing * 11
        cy_sh = y - 6
        if progress < 0.35:
            current_angle = -math.pi * 0.7
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            t_eased = 1 - (1 - t) ** 2
            current_angle = -math.pi * 0.7 + t_eased * math.pi * 1.0
        else:
            current_angle = math.pi * 0.3
        start_angle = -math.pi * 0.7
        arc_length = 34
        FX_W, FX_H = 240, 240
        fx_surf = pygame.Surface((FX_W, FX_H), pygame.SRCALPHA)
        ox, oy = FX_W // 2, FX_H // 2
        def to_fx(wx, wy):
            return (wx - cx_sh + ox, wy - cy_sh + oy)
        # ARC TRAIL (cyan with purple outer glow).
        for thickness, alpha_mult, color, radius_off in [
            (11, 0.30, _NS_morvaeth.PALETTE["purple_dark"], 4),
            (9, 0.45, _NS_morvaeth.PALETTE["purple_mid"], 2),
            (7, 0.65, _NS_morvaeth.PALETTE["cyan_dark"], 1),
            (5, 0.85, _NS_morvaeth.PALETTE["cyan_mid"], 0),
            (3, 1.00, _NS_morvaeth.PALETTE["cyan_light"], 0),
            (2, 1.00, _NS_morvaeth.PALETTE["cyan_hot"], 0),
            (1, 1.00, _NS_morvaeth.PALETTE["white"], 0),
        ]:
            steps = 26
            prev = None
            for s in range(steps + 1):
                seg_t = s / steps
                seg_alpha = _NS_morvaeth._alpha(alpha_base * alpha_mult * (0.2 + 0.8 * seg_t))
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
        # SECOND ARC (offset — dual sword feel).
        offset_arc = 8
        for thickness, alpha_mult, color, radius_off in [
            (5, 0.60, _NS_morvaeth.PALETTE["cyan_mid"], -offset_arc),
            (3, 0.85, _NS_morvaeth.PALETTE["cyan_light"], -offset_arc),
            (1, 1.00, _NS_morvaeth.PALETTE["white"], -offset_arc),
        ]:
            steps = 20
            prev = None
            for s in range(steps + 1):
                seg_t = s / steps
                seg_alpha = _NS_morvaeth._alpha(alpha_base * alpha_mult * (0.2 + 0.8 * seg_t))
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
        for r in range(14, 0, -1):
            a = _NS_morvaeth._alpha(alpha_base * (14 - r) / 14 * 1.3)
            if a > 0:
                pygame.draw.circle(fx_surf, (*_NS_morvaeth.PALETTE["cyan_hot"], a), (lfx, lfy), r)
        pygame.draw.circle(fx_surf, (*_NS_morvaeth.PALETTE["white"], alpha_base), (lfx, lfy), 3)
        # SLASH LINES.
        for slash_i in range(3):
            slash_offset = (slash_i - 1) * 0.10
            slash_a = current_angle + slash_offset
            slash_alpha = _NS_morvaeth._alpha(alpha_base * (1 - abs(slash_offset) * 4))
            if slash_alpha <= 0:
                continue
            inner_r = arc_length - 12
            outer_r = arc_length + 14
            wx1 = cx_sh + int(math.cos(slash_a) * inner_r) * facing
            wy1 = cy_sh + int(math.sin(slash_a) * inner_r)
            wx2 = cx_sh + int(math.cos(slash_a) * outer_r) * facing
            wy2 = cy_sh + int(math.sin(slash_a) * outer_r)
            p1 = to_fx(wx1, wy1)
            p2 = to_fx(wx2, wy2)
            pygame.draw.line(fx_surf, (*_NS_morvaeth.PALETTE["white"], slash_alpha), p1, p2, 4 - slash_i)
            pygame.draw.line(fx_surf, (*_NS_morvaeth.PALETTE["cyan_shine"], slash_alpha), p1, p2, 1)
        # SPARKS (cyan + purple mix).
        for i in range(16):
            spark_seed = i * 0.7 + progress * 4
            spark_a = current_angle + math.sin(spark_seed) * 0.5
            spark_r = arc_length + 6 + (i % 4) * 5 + int(swing_t * 10)
            wspx = cx_sh + int(math.cos(spark_a) * spark_r) * facing
            wspy = cy_sh + int(math.sin(spark_a) * spark_r)
            spx, spy = to_fx(wspx, wspy)
            spark_alpha = _NS_morvaeth._alpha(alpha_base * (0.7 + (i % 3) * 0.1))
            tail_wx = wspx - int(math.cos(spark_a) * 4) * facing
            tail_wy = wspy - int(math.sin(spark_a) * 4)
            tfx, tfy = to_fx(tail_wx, tail_wy)
            spark_color = _NS_morvaeth.PALETTE["cyan_mid"] if i % 2 == 0 else _NS_morvaeth.PALETTE["purple_mid"]
            pygame.draw.line(fx_surf, (*spark_color, spark_alpha), (tfx, tfy), (spx, spy), 2)
            pygame.draw.rect(fx_surf, (*_NS_morvaeth.PALETTE["cyan_hot"], spark_alpha), (spx, spy, 2, 2))
            pygame.draw.rect(fx_surf, (*_NS_morvaeth.PALETTE["white"], spark_alpha), (spx, spy, 1, 1))
        # IMPACT BURST.
        if 0.55 < progress < 0.72:
            impact_t = (progress - 0.55) / 0.17
            impact_alpha = _NS_morvaeth._alpha(240 * (1 - impact_t))
            if impact_alpha > 0:
                impact_wx = cx_sh + int(math.cos(math.pi * 0.2) * (arc_length + 10)) * facing
                impact_wy = cy_sh + int(math.sin(math.pi * 0.2) * (arc_length + 10))
                ifx, ify = to_fx(impact_wx, impact_wy)
                for burst_r in range(int(8 + impact_t * 20), 0, -2):
                    a = _NS_morvaeth._alpha(impact_alpha * (22 - burst_r) / 22)
                    if a > 0:
                        pygame.draw.circle(fx_surf, (*_NS_morvaeth.PALETTE["cyan_light"], a), (ifx, ify), burst_r)
                for i in range(12):
                    a_burst = i * math.pi / 6
                    bx = ifx + int(math.cos(a_burst) * (10 + impact_t * 14))
                    by = ify + int(math.sin(a_burst) * (10 + impact_t * 14))
                    pygame.draw.line(fx_surf, (*_NS_morvaeth.PALETTE["cyan_hot"], impact_alpha), (ifx, ify), (bx, by), 2)
                    pygame.draw.rect(fx_surf, (*_NS_morvaeth.PALETTE["white"], impact_alpha), (bx, by, 2, 2))
        surface.blit(fx_surf, (cx_sh - ox, cy_sh - oy))
    # ================= AMBIENT / GROUND =================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((160, 32), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 16 - radius, 140 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (10, 5, 20, 180), (5, 9, 150, 14))
        pygame.draw.ellipse(shadow, (30, 15, 60, 120), (12, 11, 136, 10))
        surface.blit(shadow, (x - 80, y - 16))
    def _draw_demon_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((260, 220), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_morvaeth._alpha((100 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_morvaeth._aacircle(aura, (*_NS_morvaeth.PALETTE["purple_darkest"], alpha), (130, 110), radius)
        for radius in range(65, 5, -3):
            alpha = _NS_morvaeth._alpha((65 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_morvaeth._aacircle(aura, (*_NS_morvaeth.PALETTE["purple_dark"], alpha), (130, 110), radius)
        for radius in range(35, 5, -2):
            alpha = _NS_morvaeth._alpha((35 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_morvaeth._aacircle(aura, (*_NS_morvaeth.PALETTE["cyan_dark"], alpha), (130, 110), radius)
        surface.blit(aura, (x - 130, y - 110))
        # Floating particles (cyan + purple).
        for i in range(14):
            angle = phase * 0.4 + i * math.pi / 7
            radius = 42 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            sy -= int((phase * 6 + i * 5) % 24)
            color = _NS_morvaeth.PALETTE["cyan_mid"] if i % 2 == 0 else _NS_morvaeth.PALETTE["purple_mid"]
            hot_color = _NS_morvaeth.PALETTE["cyan_light"] if i % 2 == 0 else _NS_morvaeth.PALETTE["purple_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot_color, (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((190, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_morvaeth.PALETTE["purple_darkest"], 200), (5, 20, 180, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_morvaeth.PALETTE["purple_dark"], 220), (14, 22, 162, 26), 2)
        pygame.draw.ellipse(ring, (*_NS_morvaeth.PALETTE["cyan_dark"], 200), (25, 24, 140, 22), 1)
        pygame.draw.ellipse(ring, (*_NS_morvaeth.PALETTE["purple_mid"], 180), (40, 26, 110, 18), 1)
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 95 + int(math.cos(angle) * 74)
            y1 = 35 + int(math.sin(angle) * 12)
            color = _NS_morvaeth.PALETTE["cyan_light"] if i % 2 == 0 else _NS_morvaeth.PALETTE["purple_light"]
            pygame.draw.rect(ring, color, (x1, y1, 2, 2))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_morvaeth.PALETTE["cyan_hot"], _NS_morvaeth._alpha(150 * pulse)),
                                (15, 14, 160, 44), 1)
        surface.blit(ring, (x - 95, y - 30))
    def _draw_hover_particles(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Cyan+purple particles rising below."""
        strength = 1.5 if intense else 1.0
        for i, offset in enumerate((-24, -14, -4, 6, 16, 26, -32, 32)):
            t = (phase * 0.5 + i * 0.15) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 22)
            alpha = _NS_morvaeth._alpha(200 * (1 - t) * strength)
            if alpha <= 0:
                continue
            color = _NS_morvaeth.PALETTE["cyan_dark"] if i % 2 == 0 else _NS_morvaeth.PALETTE["purple_dark"]
            mid_color = _NS_morvaeth.PALETTE["cyan_mid"] if i % 2 == 0 else _NS_morvaeth.PALETTE["purple_mid"]
            hot_color = _NS_morvaeth.PALETTE["cyan_light"] if i % 2 == 0 else _NS_morvaeth.PALETTE["purple_light"]
            _NS_morvaeth._aacircle(surface, (*color, alpha), (sx, sy), 3)
            _NS_morvaeth._aacircle(surface, (*mid_color, alpha), (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*hot_color, alpha), (sx, sy - 1, 1, 1))
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_morvaeth._alpha(160 - i * 30)
                if alpha <= 0:
                    continue
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["purple_dark"], alpha),
                                       (sx, sy), max(2, 6 - i))
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["cyan_mid"], alpha),
                                       (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_morvaeth.PALETTE["cyan_light"], alpha),
                                 (sx, sy - 1, 2, 1))
    # ================= SKILL Q — MIRROR LANCE =================
    def _draw_mirror_lance(surface, boss, x, y, timer, phase):
        """Long purple lance projectile that goes and comes back."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morvaeth._target_position(boss, x, y)
        start_x = x + facing * 34
        start_y = y - 6
        # Phase 1 (0-0.5): fly outward. Phase 2 (0.5-1.0): return.
        if progress < 0.15:
            # Charge on hand.
            t = progress / 0.15
            hand_x = start_x
            hand_y = start_y
            cr = int(3 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_morvaeth._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["purple_dark"], alpha), (hand_x, hand_y), r)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["purple_mid"], (hand_x, hand_y), cr - 2)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["purple_hot"], (hand_x, hand_y), max(1, cr - 4))
        else:
            t_full = (progress - 0.15) / 0.85
            if t_full <= 0.5:
                # Outward.
                fly_t = t_full / 0.5
                bx = int(start_x + (tx - start_x) * fly_t)
                by = int(start_y + (ty - start_y) * fly_t)
            else:
                # Return.
                fly_t = (t_full - 0.5) / 0.5
                bx = int(tx + (start_x - tx) * fly_t)
                by = int(ty + (start_y - ty) * fly_t)
            # Direction unit.
            dx = tx - start_x
            dy = ty - start_y
            length = math.hypot(dx, dy) or 1
            ux = dx / length
            uy = dy / length
            # Flip on return.
            if t_full > 0.5:
                ux = -ux
                uy = -uy
            # Lance body (elongated purple energy).
            lance_len = 30
            head_x = bx
            head_y = by
            tail_x = int(bx - ux * lance_len)
            tail_y = int(by - uy * lance_len)
            # Trail (behind tail).
            for i in range(10):
                trail_t = i * 0.06
                tail_prev_x = int(tail_x - ux * (i * 4))
                tail_prev_y = int(tail_y - uy * (i * 4))
                alpha = _NS_morvaeth._alpha(200 - i * 22)
                size = max(1, 6 - i)
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["purple_dark"], alpha),
                                       (tail_prev_x, tail_prev_y), size)
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["purple_mid"], alpha),
                                       (tail_prev_x, tail_prev_y), max(1, size - 1))
                pygame.draw.rect(surface, (*_NS_morvaeth.PALETTE["purple_light"], alpha),
                                 (tail_prev_x, tail_prev_y, 1, 1))
            # Lance shaft.
            for thickness, color in [
                (6, _NS_morvaeth.PALETTE["purple_darkest"]),
                (4, _NS_morvaeth.PALETTE["purple_dark"]),
                (3, _NS_morvaeth.PALETTE["purple_mid"]),
                (2, _NS_morvaeth.PALETTE["purple_light"]),
                (1, _NS_morvaeth.PALETTE["purple_hot"]),
            ]:
                pygame.draw.line(surface, color, (tail_x, tail_y), (head_x, head_y), thickness)
            # Spearhead at tip.
            perp_x = -uy
            perp_y = ux
            tip_x = int(head_x + ux * 8)
            tip_y = int(head_y + uy * 8)
            side1 = (int(head_x + perp_x * 5), int(head_y + perp_y * 5))
            side2 = (int(head_x - perp_x * 5), int(head_y - perp_y * 5))
            _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["purple_darkest"],
                               [(tip_x + 1, tip_y + 1), (side1[0] + 1, side1[1] + 1), (side2[0] + 1, side2[1] + 1)])
            _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["purple_dark"], [(tip_x, tip_y), side1, side2])
            _NS_morvaeth._poly(surface, _NS_morvaeth.PALETTE["purple_mid"], [
                (tip_x, tip_y),
                (int((tip_x + side1[0]) / 2), int((tip_y + side1[1]) / 2)),
                (int((tip_x + side2[0]) / 2), int((tip_y + side2[1]) / 2)),
            ])
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["purple_hot"], (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_morvaeth.PALETTE["white"], (tip_x, tip_y, 1, 1))
            # Impact splash at turnaround.
            if 0.45 < t_full < 0.55:
                st = abs(0.5 - t_full) / 0.05
                radius = int(15 * (1 - st))
                alpha = _NS_morvaeth._alpha(240 * (1 - st))
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["purple_dark"], alpha), (tx, ty), radius, 3)
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["purple_mid"], alpha), (tx, ty), max(1, radius - 4), 2)
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["purple_hot"], alpha), (tx, ty), max(1, radius - 8), 1)
                for i in range(10):
                    ang = i * math.pi / 5
                    ex = tx + int(math.cos(ang) * radius)
                    ey = ty + int(math.sin(ang) * radius * 0.7)
                    pygame.draw.rect(surface, (*_NS_morvaeth.PALETTE["purple_hot"], alpha), (ex, ey, 2, 2))
                    pygame.draw.rect(surface, (*_NS_morvaeth.PALETTE["white"], alpha), (ex, ey, 1, 1))
    # ================= SKILL W — CONJURE TWIN =================
    def _draw_conjure_portal_ground(surface, boss, x, y, timer, pulse):
        """Cyan portal at side of boss."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Portal opens at side.
        portal_x = x - facing * 40
        portal_y = y
        # Portal only visible during summon (first 30%).
        if progress < 0.4:
            fade_t = min(1.0, progress / 0.2) if progress < 0.2 else (1.0 - (progress - 0.2) / 0.2)
            fade_t = max(0.0, fade_t)
            portal_r = int(20 * fade_t)
            if portal_r > 3:
                for r in range(portal_r, 0, -2):
                    alpha = _NS_morvaeth._alpha(200 * (portal_r - r) / portal_r * fade_t)
                    _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["cyan_darkest"], alpha),
                                           (portal_x, portal_y + 20), r)
                # Rings.
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["cyan_light"], _NS_morvaeth._alpha(240 * fade_t)),
                                       (portal_x, portal_y + 20), portal_r, 2)
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["cyan_hot"], _NS_morvaeth._alpha(240 * fade_t)),
                                       (portal_x, portal_y + 20), portal_r - 3, 1)
    def _draw_conjured_clone(surface, boss, x, y, timer, pulse):
        """Illusion clone next to boss."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.2:
            return  # not spawned yet
        # Clone at side of boss.
        clone_x = x - facing * 40
        clone_y = y
        # Fade in.
        clone_alpha_mult = min(1.0, (progress - 0.2) / 0.15)
        if progress > 0.85:
            clone_alpha_mult = (1.0 - (progress - 0.85) / 0.15)
        if clone_alpha_mult <= 0:
            return
        # Draw clone body (semi-transparent via layer surface).
        clone_surf = pygame.Surface((180, 200), pygame.SRCALPHA)
        clone_ox, clone_oy = 90, 100
        # Draw body onto clone_surf at center.
        # But since _draw_mrv_body draws directly on surface, we need to redirect.
        # Simple approach: draw on temp surface then blit with alpha.
        _NS_morvaeth._draw_mrv_body(clone_surf, clone_ox, clone_oy, facing, pulse, "idle",
                                   is_clone=True)
        # Apply alpha.
        clone_surf.set_alpha(int(160 * clone_alpha_mult))
        surface.blit(clone_surf, (clone_x - clone_ox, clone_y - clone_oy))
        # Cyan outline shimmer around clone.
        for r in range(24, 12, -3):
            alpha = _NS_morvaeth._alpha(80 * clone_alpha_mult)
            _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["cyan_light"], alpha),
                                   (clone_x, clone_y), r, 1)
    # ================= SKILL E — DEMONFORM =================
    def _draw_demonform_ground(surface, boss, x, y, timer, pulse):
        """Cyan+purple ring under boss."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        intensity = math.sin(progress * math.pi)
        for i in range(3):
            r = int(40 + i * 8 + math.sin(pulse * 2) * 3)
            alpha = _NS_morvaeth._alpha(200 - i * 50) * intensity
            alpha_i = _NS_morvaeth._alpha(alpha)
            color = _NS_morvaeth.PALETTE["cyan_light"] if i % 2 == 0 else _NS_morvaeth.PALETTE["purple_light"]
            _NS_morvaeth._aacircle(surface, (*color, alpha_i), (x, y + 44), r, 2)
    def _draw_demonform_aura(surface, boss, x, y, timer, pulse):
        """Purple + cyan rising flames around body."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        intensity = math.sin(progress * math.pi)
        FX_W, FX_H = 180, 200
        fx_surf = pygame.Surface((FX_W, FX_H), pygame.SRCALPHA)
        ox, oy = FX_W // 2, FX_H // 2
        # Rising flame columns.
        num_flames = 14
        for i in range(num_flames):
            angle = i * math.pi * 2 / num_flames
            base_x = ox + int(math.cos(angle) * 28)
            base_y = oy + int(math.sin(angle) * 14) + 10
            for layer in range(8):
                layer_t = (pulse * 0.6 + i * 0.15 + layer * 0.1) % 1.0
                flame_y = base_y - int(layer_t * 60)
                flame_r = int(4 + layer_t * 4)
                flame_alpha = _NS_morvaeth._alpha(220 * (1 - layer_t) * intensity)
                if flame_alpha <= 0:
                    continue
                color_dark = _NS_morvaeth.PALETTE["purple_dark"] if i % 2 == 0 else _NS_morvaeth.PALETTE["cyan_dark"]
                color_mid = _NS_morvaeth.PALETTE["purple_mid"] if i % 2 == 0 else _NS_morvaeth.PALETTE["cyan_mid"]
                color_hot = _NS_morvaeth.PALETTE["purple_hot"] if i % 2 == 0 else _NS_morvaeth.PALETTE["cyan_hot"]
                pygame.draw.circle(fx_surf, (*color_dark, flame_alpha), (base_x, flame_y), flame_r + 1)
                pygame.draw.circle(fx_surf, (*color_mid, flame_alpha), (base_x, flame_y - 1), flame_r)
                pygame.draw.circle(fx_surf, (*color_hot, flame_alpha), (base_x, flame_y - 2), max(1, flame_r - 2))
                if layer < 3:
                    pygame.draw.rect(fx_surf, (*_NS_morvaeth.PALETTE["white"], flame_alpha),
                                     (base_x, flame_y - 2, 1, 1))
        # Spikes rising up (like transformation energy).
        for i in range(6):
            spike_a = i * math.pi / 3 + pulse * 0.5
            spike_r = 40
            sp_bx = ox + int(math.cos(spike_a) * spike_r)
            sp_by = oy + int(math.sin(spike_a) * spike_r * 0.5)
            sp_tx = sp_bx + int(math.cos(spike_a - math.pi / 2) * 20)
            sp_ty = sp_by + int(math.sin(spike_a - math.pi / 2) * 20)
            alpha = _NS_morvaeth._alpha(200 * intensity)
            pygame.draw.line(fx_surf, (*_NS_morvaeth.PALETTE["purple_light"], alpha),
                             (sp_bx, sp_by), (sp_tx, sp_ty), 2)
            pygame.draw.rect(fx_surf, (*_NS_morvaeth.PALETTE["white"], alpha), (sp_tx, sp_ty, 1, 1))
        surface.blit(fx_surf, (x - ox, y - oy))
    # ================= SKILL R — SOUL SUNDER (beam) =================
    def _draw_sunder_ground(surface, boss, x, y, timer, pulse):
        """Purple burning trail."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.25:
            trail_len = int(240 * min(1.0, (progress - 0.25) / 0.75))
            start_x = x + facing * 32
            start_y = y + 24
            for i in range(0, trail_len, 6):
                px = start_x + facing * i
                py = start_y + int(math.sin(pulse * 3 + i * 0.1) * 3)
                r = int(7 + math.sin(pulse * 2 + i * 0.05) * 2)
                pygame.draw.ellipse(surface, (*_NS_morvaeth.PALETTE["purple_darkest"], 200),
                                    (px - r, py - r // 2, r * 2, r))
                pygame.draw.ellipse(surface, (*_NS_morvaeth.PALETTE["purple_dark"], 180),
                                    (px - r + 1, py - r // 2 + 1, r * 2 - 2, r - 2))
                pygame.draw.ellipse(surface, (*_NS_morvaeth.PALETTE["cyan_dark"], 160),
                                    (px - r + 3, py - r // 2 + 2, r * 2 - 6, r - 4))
    def _draw_soul_sunder_beam(surface, boss, x, y, timer, pulse):
        """Massive cyan-purple beam to target."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morvaeth._target_position(boss, x, y)
        if progress < 0.25:
            # Charge.
            t = progress / 0.25
            hand_x = x + facing * 34
            hand_y = y - 4
            cr = int(6 + t * 14)
            for r in range(cr + 8, 0, -1):
                alpha = _NS_morvaeth._alpha(200 * (cr + 8 - r) / (cr + 8))
                color = _NS_morvaeth.PALETTE["purple_dark"] if r > 6 else _NS_morvaeth.PALETTE["cyan_dark"]
                _NS_morvaeth._aacircle(surface, (*color, alpha), (hand_x, hand_y), r)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["cyan_mid"], (hand_x, hand_y), cr - 3)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["cyan_light"], (hand_x, hand_y), max(1, cr - 6))
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["cyan_hot"], (hand_x, hand_y), max(1, cr - 8))
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["white"], (hand_x, hand_y), max(1, cr - 10))
        else:
            t = (progress - 0.25) / 0.75
            intensity = math.sin(t * math.pi) if t < 0.85 else (1 - t) / 0.15
            intensity = max(0, min(1, intensity))
            start_x = x + facing * 36
            start_y = y - 4
            dx = tx - start_x
            dy = ty - start_y
            length = math.hypot(dx, dy) or 1
            ux = dx / length
            uy = dy / length
            perp_x = -uy
            perp_y = ux
            beam_len = int(length * min(1.0, t * 3))
            end_x = int(start_x + ux * beam_len)
            end_y = int(start_y + uy * beam_len)
            alpha_base = _NS_morvaeth._alpha(255 * intensity)
            # Beam layers.
            FX_W, FX_H = 500, 200
            fx_surf = pygame.Surface((FX_W, FX_H), pygame.SRCALPHA)
            ox_l, oy_l = 30, FX_H // 2
            for width_layer, color in [
                (16, _NS_morvaeth.PALETTE["purple_darkest"]),
                (13, _NS_morvaeth.PALETTE["purple_dark"]),
                (10, _NS_morvaeth.PALETTE["purple_mid"]),
                (8, _NS_morvaeth.PALETTE["cyan_dark"]),
                (6, _NS_morvaeth.PALETTE["cyan_mid"]),
                (4, _NS_morvaeth.PALETTE["cyan_light"]),
                (2, _NS_morvaeth.PALETTE["cyan_hot"]),
                (1, _NS_morvaeth.PALETTE["white"]),
            ]:
                seg_count = 12
                for seg_i in range(seg_count):
                    s1 = seg_i / seg_count
                    s2 = (seg_i + 1) / seg_count
                    wave1 = math.sin(pulse * 4 + seg_i * 0.5) * 3
                    wave2 = math.sin(pulse * 4 + (seg_i + 1) * 0.5) * 3
                    x1 = ox_l + int(ux * s1 * beam_len)
                    y1 = oy_l + int(uy * s1 * beam_len)
                    x2 = ox_l + int(ux * s2 * beam_len)
                    y2 = oy_l + int(uy * s2 * beam_len)
                    a1 = (x1 + int(perp_x * (width_layer + wave1)), y1 + int(perp_y * (width_layer + wave1)))
                    a2 = (x1 - int(perp_x * (width_layer - wave1)), y1 - int(perp_y * (width_layer - wave1)))
                    b1 = (x2 + int(perp_x * (width_layer + wave2)), y2 + int(perp_y * (width_layer + wave2)))
                    b2 = (x2 - int(perp_x * (width_layer - wave2)), y2 - int(perp_y * (width_layer - wave2)))
                    pygame.draw.polygon(fx_surf, (*color, alpha_base), [a1, b1, b2, a2])
            surface.blit(fx_surf, (start_x - ox_l, start_y - oy_l))
            # Sparks along beam.
            for i in range(int(beam_len / 6)):
                sp_t = i * 6 / max(1, beam_len)
                spx = int(start_x + ux * sp_t * beam_len) + int(math.sin(pulse * 6 + i) * 8)
                spy = int(start_y + uy * sp_t * beam_len) + int(math.cos(pulse * 6 + i) * 8)
                sp_alpha = _NS_morvaeth._alpha(alpha_base * 0.9)
                color = _NS_morvaeth.PALETTE["cyan_hot"] if i % 2 == 0 else _NS_morvaeth.PALETTE["purple_hot"]
                pygame.draw.rect(surface, (*color, sp_alpha), (spx, spy, 2, 2))
                pygame.draw.rect(surface, (*_NS_morvaeth.PALETTE["white"], sp_alpha), (spx, spy, 1, 1))
            # Impact.
            imp_alpha = _NS_morvaeth._alpha(240 * intensity)
            imp_r = int(20 + t * 22)
            for r in range(imp_r + 4, 0, -2):
                a = _NS_morvaeth._alpha(imp_alpha * (imp_r + 4 - r) / (imp_r + 4))
                _NS_morvaeth._aacircle(surface, (*_NS_morvaeth.PALETTE["purple_mid"], a), (end_x, end_y), r)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["purple_light"], (end_x, end_y), 12)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["cyan_light"], (end_x, end_y), 7)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["cyan_hot"], (end_x, end_y), 4)
            _NS_morvaeth._aacircle(surface, _NS_morvaeth.PALETTE["white"], (end_x, end_y), 2)
            for i in range(14):
                ang = i * math.pi / 7
                ex = end_x + int(math.cos(ang) * 26)
                ey = end_y + int(math.sin(ang) * 26)
                color = _NS_morvaeth.PALETTE["cyan_light"] if i % 2 == 0 else _NS_morvaeth.PALETTE["purple_light"]
                pygame.draw.line(surface, (*color, imp_alpha), (end_x, end_y), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_morvaeth.PALETTE["white"], imp_alpha), (ex, ey, 2, 2))



# ====================================================================
# VARDROK (AXE-KING) - Mini Boss
# ====================================================================

class _NS_vardrok:
    """Namespace vardrok - muscular axe gladiator boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (tan muscular)
        "skin_darkest": (60, 30, 20),
        "skin_dark": (140, 85, 55),
        "skin_mid": (200, 145, 100),
        "skin_light": (235, 190, 145),
        "skin_shine": (255, 220, 180),
        # Hair (dark purple mohawk)
        "hair_darkest": (25, 15, 40),
        "hair_dark": (55, 30, 80),
        "hair_mid": (95, 55, 130),
        "hair_light": (155, 105, 190),
        # Facial hair (dark brown)
        "beard_dark": (30, 20, 15),
        "beard_mid": (70, 45, 30),
        "beard_light": (120, 85, 60),
        # Leather pants (dark brown)
        "leather_darkest": (18, 12, 8),
        "leather_dark": (45, 30, 20),
        "leather_mid": (85, 55, 35),
        "leather_light": (140, 100, 65),
        "leather_edge": (195, 155, 105),
        # Steel (axe blades)
        "steel_darkest": (25, 28, 40),
        "steel_dark": (75, 82, 100),
        "steel_mid": (145, 155, 175),
        "steel_light": (210, 220, 235),
        "steel_shine": (250, 250, 255),
        # Brass (buckle, accents)
        "brass_dark": (85, 55, 20),
        "brass_mid": (170, 115, 45),
        "brass_light": (235, 180, 85),
        "brass_shine": (255, 225, 145),
        # Blood red (main FX color)
        "blood_darkest": (35, 5, 8),
        "blood_dark": (110, 15, 20),
        "blood_mid": (200, 30, 40),
        "blood_light": (250, 75, 80),
        "blood_hot": (255, 145, 140),
        "blood_shine": (255, 220, 210),
        # Red bandana / cloth accents
        "cloth_dark": (90, 15, 20),
        "cloth_mid": (170, 30, 40),
        "cloth_light": (230, 75, 80),
        # Shadow / darkness
        "shadow_deep": (2, 2, 4),
        "shadow": (0, 0, 0),
        "white": (255, 255, 255),
        "black": (0, 0, 0),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vardrok._clamp(color)
        if _NS_vardrok.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_vardrok._clamp(color)
        if _NS_vardrok.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_vardrok._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 260 * getattr(boss, "direction", 1)), int(y)
    # ================= ENTRY POINT =================
    def draw_vardrok(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_vardrok._detect_moving(boss)
        _NS_vardrok._update_vd_attack_anim(boss)
        attacking = (
            getattr(boss, "_vd_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        _NS_vardrok._draw_blood_aura(surface, x, y, pulse)
        _NS_vardrok._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX behind body.
        if active_skill == "w":
            _NS_vardrok._draw_frenzy_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vardrok._draw_whirlwind_ground(surface, boss, x, y, skill_timer, pulse)
        # Body.
        if attacking:
            _NS_vardrok._draw_vd_attack(surface, boss, x, y)
        elif moving:
            _NS_vardrok._draw_vd_walk(surface, boss, x, y)
        else:
            _NS_vardrok._draw_vd_idle(surface, boss, x, y)
        # Frenzy aura overlay (over body).
        if active_skill == "w":
            _NS_vardrok._draw_frenzy_aura(surface, boss, x, y, skill_timer, pulse)
        # Idle spinning axes (always shown as ambient).
        _NS_vardrok._draw_idle_orbit_axes(surface, x, y, pulse)
        # Foreground FX.
        if active_skill == "q":
            _NS_vardrok._draw_bloodspin_axe(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vardrok._draw_twin_cleaver(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vardrok._draw_whirlwind_massacre(surface, boss, x, y, skill_timer, pulse)
    # ================= ANIMATION STATE =================
    def _update_vd_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vd_previous_timer", 0))
        active = bool(getattr(boss, "_vd_attack_active", False))
        if not active and previous > timer and previous >= cooldown - 2:
            boss._vd_attack_active = True
            boss._vd_attack_frame = 0
            active = True
        elif active:
            boss._vd_attack_frame = int(getattr(boss, "_vd_attack_frame", 0)) + 1
            if boss._vd_attack_frame >= cooldown:
                boss._vd_attack_active = False
                boss._vd_attack_frame = 0
                active = False
        boss._vd_previous_timer = timer
        boss._vd_attack_progress = (
            min(1.0, getattr(boss, "_vd_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_vd_last_x"):
            boss._vd_last_x = boss.x
            boss._vd_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vd_last_x)
        dy = abs(boss.y - boss._vd_last_y)
        boss._vd_last_x = boss.x
        boss._vd_last_y = boss.y
        return dx + dy > 0.3
    # ================= POSE ROUTERS =================
    def _draw_vd_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_vardrok._draw_shadow(surface, x, y + 50)
        _NS_vardrok._draw_hover_particles(surface, x, y + 44, boss.pulse)
        _NS_vardrok._draw_vd_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")
    def _draw_vd_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 6)
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_vardrok._draw_shadow(surface, x + sway, y + 50)
        _NS_vardrok._draw_hover_particles(surface, x + sway, y + 44, phase, trail=True, facing=boss.direction)
        _NS_vardrok._draw_vd_body(surface, x + sway, y + bob, boss.direction, phase, "walk")
    def _draw_vd_attack(surface, boss, x, y):
        progress = getattr(boss, "_vd_attack_progress", None)
        if progress is None or progress <= 0:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Ranged throw: pull arm back, throw forward, recovery.
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 4) * boss.direction
            lift = int(t * 3)
        elif progress < 0.55:
            t = (progress - 0.35) / 0.20
            t_eased = 1 - (1 - t) ** 2
            lunge = int((-4 + t_eased * 12)) * boss.direction
            lift = int(3 - t_eased * 4)
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(8 * (1 - t)) * boss.direction
            lift = int(-1 + t * 1)
        _NS_vardrok._draw_shadow(surface, x + lunge, y + 50)
        _NS_vardrok._draw_hover_particles(surface, x + lunge, y + 44, boss.pulse, intense=True)
        _NS_vardrok._draw_vd_body(surface, x + lunge, y - lift, boss.direction, boss.pulse, "attack", progress)
        _NS_vardrok._draw_thrown_axe(surface, boss, x + lunge, y - lift, progress)
    # ================= BODY =================
    def _draw_vd_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Back arm holding axe (behind).
        _NS_vardrok._draw_back_arm(surface, cx, cy - 4, facing, phase, action, attack_progress)
        # Legs (leather pants).
        _NS_vardrok._draw_leather_legs(surface, cx, cy + 10, facing, phase, action)
        # Muscular torso (bare chest).
        _NS_vardrok._draw_bare_torso(surface, cx, cy, facing, phase)
        # Belt with buckle.
        _NS_vardrok._draw_big_belt(surface, cx, cy + 8, facing, phase)
        # Head with mohawk + beard.
        _NS_vardrok._draw_gladiator_head(surface, cx, cy - 18, facing, phase, action)
        # Front arm with throw pose.
        _NS_vardrok._draw_throw_arm(surface, cx, cy - 4, facing, phase, action, attack_progress)
    def _draw_leather_legs(surface, cx, cy, facing, phase, action):
        """Dark leather pants with belt strap."""
        leg_bob = math.sin(phase * 1.5) * 3 if action == "walk" \
            else math.sin(phase * 0.8) * 1
        # Wide pants shape.
        pants_shape = [
            (cx - 12, cy - 4),
            (cx + 12, cy - 4),
            (cx + 14, cy + 6),
            (cx + 12, cy + 14),
            (cx + 6, cy + 18),
            (cx - 6, cy + 18),
            (cx - 12, cy + 14),
            (cx - 14, cy + 6),
        ]
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in pants_shape])
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["leather_darkest"], pants_shape)
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["leather_dark"], [
            (cx - 11, cy - 3),
            (cx + 11, cy - 3),
            (cx + 13, cy + 6),
            (cx + 10, cy + 13),
            (cx + 5, cy + 16),
            (cx - 5, cy + 16),
            (cx - 10, cy + 13),
            (cx - 13, cy + 6),
        ])
        # Mid highlight.
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["leather_mid"], [
            (cx - 8, cy - 2),
            (cx + 8, cy - 2),
            (cx + 10, cy + 6),
            (cx - 10, cy + 6),
        ])
        # Central seam / strap.
        pygame.draw.line(surface, _NS_vardrok.PALETTE["leather_darkest"],
                         (cx, cy - 4), (cx, cy + 16), 1)
        pygame.draw.line(surface, _NS_vardrok.PALETTE["leather_light"],
                         (cx - 1, cy - 4), (cx - 1, cy + 14), 1)
        # Red loincloth in front (little sash).
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["cloth_dark"], [
            (cx - 4, cy - 2),
            (cx + 4, cy - 2),
            (cx + 3, cy + 8),
            (cx, cy + 10),
            (cx - 3, cy + 8),
        ])
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["cloth_mid"], [
            (cx - 3, cy),
            (cx + 3, cy),
            (cx + 2, cy + 6),
            (cx, cy + 8),
            (cx - 2, cy + 6),
        ])
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["cloth_light"], (cx, cy + 2, 1, 3))
        # Belts/straps around thighs.
        for side in (-1, 1):
            thigh_x = cx + side * 7
            for band_y in (2, 8):
                pygame.draw.line(surface, _NS_vardrok.PALETTE["leather_darkest"],
                                 (thigh_x - 3, cy + band_y),
                                 (thigh_x + 3, cy + band_y), 2)
                pygame.draw.line(surface, _NS_vardrok.PALETTE["leather_edge"],
                                 (thigh_x - 3, cy + band_y - 1),
                                 (thigh_x + 3, cy + band_y - 1), 1)
                # Small buckle.
                pygame.draw.rect(surface, _NS_vardrok.PALETTE["brass_mid"],
                                 (thigh_x + side * 3, cy + band_y - 1, 2, 2))
                pygame.draw.rect(surface, _NS_vardrok.PALETTE["brass_light"],
                                 (thigh_x + side * 3, cy + band_y - 1, 1, 1))
        # Boots visible below.
        for side in (-1, 1):
            foot_x = cx + side * 6
            foot_y = cy + 18 + int(leg_bob * side * 0.3)
            # Boot.
            _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["shadow_deep"], [
                (foot_x - 4 + 1, foot_y - 2 + 1),
                (foot_x + 4 + 1, foot_y - 2 + 1),
                (foot_x + 3 + 1, foot_y + 2 + 1),
                (foot_x - 3 + 1, foot_y + 2 + 1),
            ])
            _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["leather_darkest"], [
                (foot_x - 4, foot_y - 2),
                (foot_x + 4, foot_y - 2),
                (foot_x + 3, foot_y + 2),
                (foot_x - 3, foot_y + 2),
            ])
            _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["leather_dark"], [
                (foot_x - 3, foot_y - 1),
                (foot_x + 3, foot_y - 1),
                (foot_x + 2, foot_y + 1),
                (foot_x - 2, foot_y + 1),
            ])
            _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["leather_mid"], [
                (foot_x - 2, foot_y - 1),
                (foot_x + 2, foot_y - 1),
                (foot_x + 1, foot_y),
                (foot_x - 1, foot_y),
            ])
            pygame.draw.rect(surface, _NS_vardrok.PALETTE["leather_edge"], (foot_x - 1, foot_y - 1, 2, 1))
    def _draw_bare_torso(surface, cx, cy, facing, phase):
        """Muscular tan chest — bare."""
        breath = math.sin(phase * 0.7) * 1
        # Torso shape (broad shoulders, V-shape).
        torso_shape = [
            (cx - 14, cy - 12),
            (cx - 16, cy - 4),
            (cx - 13, cy + 4),
            (cx - 10, cy + 10),
            (cx + 10, cy + 10),
            (cx + 13, cy + 4),
            (cx + 16, cy - 4),
            (cx + 14, cy - 12),
            (cx + 6, cy - 14),
            (cx - 6, cy - 14),
        ]
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 3) for p in torso_shape])
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["skin_darkest"], torso_shape)
        # Base skin.
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["skin_dark"], [
            (cx - 13, cy - 11),
            (cx - 15, cy - 3),
            (cx - 12, cy + 3),
            (cx - 9, cy + 9),
            (cx + 9, cy + 9),
            (cx + 12, cy + 3),
            (cx + 15, cy - 3),
            (cx + 13, cy - 11),
            (cx + 5, cy - 13),
            (cx - 5, cy - 13),
        ])
        # Mid skin.
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["skin_mid"], [
            (cx - 11, cy - 9),
            (cx - 13, cy - 2),
            (cx - 10, cy + 4),
            (cx - 8, cy + 8),
            (cx + 8, cy + 8),
            (cx + 10, cy + 4),
            (cx + 13, cy - 2),
            (cx + 11, cy - 9),
            (cx + 4, cy - 12),
            (cx - 4, cy - 12),
        ])
        # PECTORALS (2 distinct chest muscles).
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["skin_light"], [
            (cx - 9, cy - 7),
            (cx - 1, cy - 9),
            (cx - 1, cy - 3),
            (cx - 7, cy - 2),
        ])
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["skin_light"], [
            (cx + 1, cy - 9),
            (cx + 9, cy - 7),
            (cx + 7, cy - 2),
            (cx + 1, cy - 3),
        ])
        # Highlight on chest.
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["skin_shine"], (cx - 6, cy - 8, 3, 1))
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["skin_shine"], (cx + 4, cy - 8, 3, 1))
        # ABS (6-pack).
        for row in range(3):
            ab_y = cy - 1 + row * 2
            # Center line.
            pygame.draw.line(surface, _NS_vardrok.PALETTE["skin_darkest"],
                             (cx, ab_y - 1), (cx, ab_y + 1), 1)
            # Horizontal ab lines.
            pygame.draw.line(surface, _NS_vardrok.PALETTE["skin_darkest"],
                             (cx - 4, ab_y), (cx + 4, ab_y), 1)
            pygame.draw.line(surface, _NS_vardrok.PALETTE["skin_light"],
                             (cx - 3, ab_y - 1), (cx + 3, ab_y - 1), 1)
        # BICEPS bulge outline.
        for side in (-1, 1):
            bicep_x = cx + side * 13
            bicep_y = cy - 4
            _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["skin_dark"], (bicep_x, bicep_y), 4)
            _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["skin_mid"], (bicep_x, bicep_y), 3)
            _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["skin_light"], (bicep_x - 1, bicep_y - 1), 1)
        # Fur/leather shoulder straps.
        for side in (-1, 1):
            strap_x = cx + side * 10
            strap_y_top = cy - 12
            strap_y_bot = cy - 4
            pygame.draw.line(surface, _NS_vardrok.PALETTE["leather_darkest"],
                             (strap_x, strap_y_top), (strap_x, strap_y_bot), 4)
            pygame.draw.line(surface, _NS_vardrok.PALETTE["leather_dark"],
                             (strap_x, strap_y_top), (strap_x, strap_y_bot), 2)
            pygame.draw.line(surface, _NS_vardrok.PALETTE["leather_light"],
                             (strap_x - 1, strap_y_top), (strap_x - 1, strap_y_bot), 1)
            # Rivets.
            for ry in (strap_y_top + 2, strap_y_bot - 2):
                pygame.draw.rect(surface, _NS_vardrok.PALETTE["brass_mid"], (strap_x, ry, 1, 1))
                pygame.draw.rect(surface, _NS_vardrok.PALETTE["brass_shine"], (strap_x, ry, 1, 1))
    def _draw_big_belt(surface, cx, cy, facing, phase):
        """Wide leather belt with big brass buckle."""
        # Belt strap.
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["shadow_deep"], [
            (cx - 14 + 1, cy - 3 + 1),
            (cx + 14 + 1, cy - 3 + 1),
            (cx + 14 + 1, cy + 3 + 1),
            (cx - 14 + 1, cy + 3 + 1),
        ])
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["leather_darkest"], [
            (cx - 14, cy - 3),
            (cx + 14, cy - 3),
            (cx + 14, cy + 3),
            (cx - 14, cy + 3),
        ])
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["leather_dark"], [
            (cx - 13, cy - 2),
            (cx + 13, cy - 2),
            (cx + 13, cy + 2),
            (cx - 13, cy + 2),
        ])
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["leather_mid"], [
            (cx - 13, cy - 1),
            (cx + 13, cy - 1),
            (cx + 13, cy),
            (cx - 13, cy),
        ])
        # Stitching top.
        for i in range(-13, 14, 3):
            pygame.draw.rect(surface, _NS_vardrok.PALETTE["leather_edge"], (cx + i, cy - 2, 1, 1))
        # BIG BUCKLE (round with X or star pattern).
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["shadow_deep"], (cx + 1, cy + 1), 5)
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["brass_dark"], (cx, cy), 5)
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["brass_mid"], (cx, cy), 4)
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["brass_light"], (cx - 1, cy - 1), 3)
        # Star pattern on buckle.
        pygame.draw.line(surface, _NS_vardrok.PALETTE["brass_dark"], (cx - 3, cy), (cx + 3, cy), 1)
        pygame.draw.line(surface, _NS_vardrok.PALETTE["brass_dark"], (cx, cy - 3), (cx, cy + 3), 1)
        pygame.draw.line(surface, _NS_vardrok.PALETTE["brass_dark"], (cx - 2, cy - 2), (cx + 2, cy + 2), 1)
        pygame.draw.line(surface, _NS_vardrok.PALETTE["brass_dark"], (cx - 2, cy + 2), (cx + 2, cy - 2), 1)
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["brass_shine"], (cx, cy, 1, 1))
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["white"], (cx, cy, 1, 1))
    def _draw_gladiator_head(surface, cx, cy, facing, phase, action):
        """Head with purple mohawk, dark beard, and evil grin."""
        # Face shape (angular).
        head_shape = [
            (cx - 5, cy + 5),
            (cx - 6, cy),
            (cx - 5, cy - 5),
            (cx - 2, cy - 8),
            (cx + 2, cy - 8),
            (cx + 5, cy - 5),
            (cx + 6, cy),
            (cx + 5, cy + 5),
            (cx + 2, cy + 8),
            (cx - 2, cy + 8),
        ]
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in head_shape])
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["skin_darkest"], head_shape)
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["skin_dark"], [
            (cx - 4, cy + 4),
            (cx - 5, cy),
            (cx - 4, cy - 4),
            (cx - 1, cy - 7),
            (cx + 1, cy - 7),
            (cx + 4, cy - 4),
            (cx + 5, cy),
            (cx + 4, cy + 4),
            (cx + 1, cy + 7),
            (cx - 1, cy + 7),
        ])
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["skin_mid"], [
            (cx - 4, cy - 2),
            (cx - 3, cy - 6),
            (cx + 3, cy - 6),
            (cx + 4, cy - 2),
            (cx + 3, cy + 2),
            (cx - 3, cy + 2),
        ])
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["skin_light"], [
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 2, cy),
            (cx - 2, cy),
        ])
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["skin_shine"], (cx - 1, cy - 3, 1, 1))
        # MOHAWK on top (purple, tall).
        mohawk_wave = math.sin(phase * 0.4) * 1
        # Base of mohawk.
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["shadow_deep"], [
            (cx - 3 + 1, cy - 7 + 1),
            (cx + 3 + 1, cy - 7 + 1),
            (cx + 2 + 1, cy - 12 + 1 + int(mohawk_wave)),
            (cx - 2 + 1, cy - 12 + 1 + int(mohawk_wave)),
        ])
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["hair_darkest"], [
            (cx - 3, cy - 7),
            (cx + 3, cy - 7),
            (cx + 2, cy - 12 + int(mohawk_wave)),
            (cx - 2, cy - 12 + int(mohawk_wave)),
        ])
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["hair_dark"], [
            (cx - 2, cy - 7),
            (cx + 2, cy - 7),
            (cx + 1, cy - 11 + int(mohawk_wave)),
            (cx - 1, cy - 11 + int(mohawk_wave)),
        ])
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["hair_mid"], [
            (cx - 1, cy - 8),
            (cx + 1, cy - 8),
            (cx, cy - 11 + int(mohawk_wave)),
        ])
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["hair_light"], (cx, cy - 10, 1, 1))
        # Sides of head (shaved — skin visible).
        # (Already covered by head shape).
        # EYEBROWS (heavy).
        for eye_off in (-2, 2):
            pygame.draw.rect(surface, _NS_vardrok.PALETTE["beard_dark"], (cx + eye_off - 1, cy - 3, 2, 1))
            pygame.draw.rect(surface, _NS_vardrok.PALETTE["beard_mid"], (cx + eye_off - 1, cy - 4, 2, 1))
        # EYES (small, fierce).
        for eye_off in (-2, 2):
            ex = cx + eye_off
            ey = cy - 1
            pygame.draw.rect(surface, _NS_vardrok.PALETTE["shadow_deep"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_vardrok.PALETTE["white"], (ex, ey, 1, 1))
            # Angry angle.
            pygame.draw.rect(surface, _NS_vardrok.PALETTE["shadow_deep"], (ex, ey, 1, 1))
        # NOSE.
        pygame.draw.line(surface, _NS_vardrok.PALETTE["skin_darkest"],
                         (cx, cy - 1), (cx, cy + 2), 1)
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["skin_light"], (cx - 1, cy + 1, 1, 1))
        # BEARD + MUSTACHE (dark).
        # Mustache.
        pygame.draw.line(surface, _NS_vardrok.PALETTE["beard_dark"],
                         (cx - 3, cy + 3), (cx + 3, cy + 3), 2)
        pygame.draw.line(surface, _NS_vardrok.PALETTE["beard_mid"],
                         (cx - 3, cy + 3), (cx + 3, cy + 3), 1)
        # Curled mustache tips.
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["beard_dark"], (cx - 4, cy + 3, 1, 2))
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["beard_dark"], (cx + 4, cy + 3, 1, 2))
        # Chin beard.
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["beard_dark"], [
            (cx - 2, cy + 5),
            (cx + 2, cy + 5),
            (cx + 1, cy + 8),
            (cx - 1, cy + 8),
        ])
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["beard_mid"], (cx - 1, cy + 6, 2, 1))
        # EVIL GRIN mouth.
        if action == "attack":
            # Wide open grin (yelling).
            pygame.draw.rect(surface, _NS_vardrok.PALETTE["shadow_deep"], (cx - 2, cy + 4, 5, 2))
            pygame.draw.rect(surface, _NS_vardrok.PALETTE["cloth_dark"], (cx - 1, cy + 4, 3, 1))
            pygame.draw.rect(surface, _NS_vardrok.PALETTE["white"], (cx - 1, cy + 4, 1, 1))
            pygame.draw.rect(surface, _NS_vardrok.PALETTE["white"], (cx + 1, cy + 4, 1, 1))
        else:
            # Confident smirk.
            pygame.draw.line(surface, _NS_vardrok.PALETTE["shadow_deep"],
                             (cx - 2, cy + 4), (cx + 2, cy + 4), 1)
            pygame.draw.rect(surface, _NS_vardrok.PALETTE["white"], (cx - 1, cy + 4, 1, 1))
        # Red bandana forehead band.
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["cloth_dark"], (cx - 5, cy - 6, 10, 2))
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["cloth_mid"], (cx - 5, cy - 6, 10, 1))
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["cloth_light"], (cx - 4, cy - 6, 4, 1))
    def _draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm — for throw pose."""
        back_dir = -facing
        if action == "attack":
            if attack_progress < 0.35:
                # Wind up: back arm cocks with axe.
                t = attack_progress / 0.35
                swing_angle = -math.pi * 0.2 - t * math.pi * 0.4
                arm_length = 22
            elif attack_progress < 0.55:
                t = (attack_progress - 0.35) / 0.20
                t_eased = 1 - (1 - t) ** 2
                swing_angle = -math.pi * 0.6 + t_eased * math.pi * 0.7
                arm_length = 22
            else:
                t = (attack_progress - 0.55) / 0.45
                swing_angle = math.pi * 0.1 - t * math.pi * 0.3
                arm_length = 22 - int(t * 2)
        else:
            swing_angle = math.pi * 0.15 + math.sin(phase * 0.6) * 0.15
            arm_length = 20
        shoulder_x = cx + back_dir * 10
        shoulder_y = cy - 4
        hand_x = shoulder_x + int(math.cos(swing_angle) * arm_length) * back_dir
        hand_y = shoulder_y + int(math.sin(swing_angle) * arm_length)
        elbow_x = (shoulder_x + hand_x) // 2 + back_dir * 1
        elbow_y = (shoulder_y + hand_y) // 2
        # Upper arm (bare skin).
        _NS_vardrok._aaline(surface, _NS_vardrok.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 1), (elbow_x + 1, elbow_y + 1), 6)
        _NS_vardrok._aaline(surface, _NS_vardrok.PALETTE["skin_darkest"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_vardrok._aaline(surface, _NS_vardrok.PALETTE["skin_dark"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_vardrok._aaline(surface, _NS_vardrok.PALETTE["skin_mid"],
                            (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 2)
        _NS_vardrok._aaline(surface, _NS_vardrok.PALETTE["skin_light"],
                            (shoulder_x, shoulder_y - 2), (elbow_x, elbow_y - 2), 1)
        # Elbow.
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["skin_darkest"], (elbow_x, elbow_y), 3)
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["skin_dark"], (elbow_x, elbow_y), 2)
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["skin_mid"], (elbow_x - 1, elbow_y - 1), 1)
        # Forearm.
        _NS_vardrok._aaline(surface, _NS_vardrok.PALETTE["skin_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_vardrok._aaline(surface, _NS_vardrok.PALETTE["skin_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_vardrok._aaline(surface, _NS_vardrok.PALETTE["skin_mid"],
                            (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
        # Hand (fist).
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["skin_darkest"], (hand_x, hand_y), 3)
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["skin_dark"], (hand_x, hand_y), 2)
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["skin_mid"], (hand_x - 1, hand_y - 1), 1)
        # Holding axe (held in idle/wind-up, thrown in follow-through).
        if action != "attack" or attack_progress < 0.5:
            _NS_vardrok._draw_held_axe(surface, hand_x, hand_y, back_dir, phase, swing_angle)
    def _draw_throw_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm — extended forward during throw."""
        if action == "attack":
            if attack_progress < 0.35:
                # Front arm pulled back too.
                t = attack_progress / 0.35
                swing_angle = math.pi * 0.05 - t * math.pi * 0.15
                arm_length = 22 - int(t * 3)
            elif attack_progress < 0.55:
                # THROW forward.
                t = (attack_progress - 0.35) / 0.20
                t_eased = 1 - (1 - t) ** 2
                swing_angle = -math.pi * 0.1 + t_eased * math.pi * 0.25
                arm_length = 19 + int(t_eased * 8)
            else:
                # Recovery.
                t = (attack_progress - 0.55) / 0.45
                swing_angle = math.pi * 0.15 - t * math.pi * 0.1
                arm_length = 27 - int(t * 5)
        else:
            swing_angle = math.pi * 0.15 + math.sin(phase * 0.6) * 0.1
            arm_length = 22
        shoulder_x = cx + facing * 12
        shoulder_y = cy - 4
        hand_x = shoulder_x + int(math.cos(swing_angle) * arm_length) * facing
        hand_y = shoulder_y + int(math.sin(swing_angle) * arm_length)
        elbow_x = (shoulder_x + hand_x) // 2 + facing * 1
        elbow_y = (shoulder_y + hand_y) // 2
        # Upper arm.
        _NS_vardrok._aaline(surface, _NS_vardrok.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 1), (elbow_x + 1, elbow_y + 1), 7)
        _NS_vardrok._aaline(surface, _NS_vardrok.PALETTE["skin_darkest"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 7)
        _NS_vardrok._aaline(surface, _NS_vardrok.PALETTE["skin_dark"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_vardrok._aaline(surface, _NS_vardrok.PALETTE["skin_mid"],
                            (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 3)
        _NS_vardrok._aaline(surface, _NS_vardrok.PALETTE["skin_light"],
                            (shoulder_x, shoulder_y - 2), (elbow_x, elbow_y - 2), 1)
        # Elbow.
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["skin_darkest"], (elbow_x, elbow_y), 4)
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["skin_dark"], (elbow_x, elbow_y), 3)
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["skin_mid"], (elbow_x - 1, elbow_y - 1), 2)
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["skin_light"], (elbow_x - 1, elbow_y - 1), 1)
        # Forearm (bulging bicep effect on side).
        _NS_vardrok._aaline(surface, _NS_vardrok.PALETTE["skin_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 6)
        _NS_vardrok._aaline(surface, _NS_vardrok.PALETTE["skin_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_vardrok._aaline(surface, _NS_vardrok.PALETTE["skin_mid"],
                            (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 2)
        _NS_vardrok._aaline(surface, _NS_vardrok.PALETTE["skin_light"],
                            (elbow_x, elbow_y - 2), (hand_x, hand_y - 2), 1)
        # Fist.
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["skin_darkest"], (hand_x, hand_y), 3)
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["skin_dark"], (hand_x, hand_y), 2)
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["skin_mid"], (hand_x - 1, hand_y - 1), 1)
        # Bracer/gauntlet on forearm.
        mid_x = (elbow_x + hand_x) // 2
        mid_y = (elbow_y + hand_y) // 2
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["leather_darkest"], (mid_x, mid_y), 4)
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["leather_dark"], (mid_x, mid_y), 3)
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["leather_mid"], (mid_x - 1, mid_y - 1), 2)
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["brass_light"], (mid_x, mid_y, 1, 1))
    def _draw_held_axe(surface, hx, hy, facing, phase, angle):
        """Static held axe (before throw)."""
        # Handle.
        handle_len = 8
        handle_end_x = hx - int(math.cos(angle) * handle_len) * facing
        handle_end_y = hy - int(math.sin(angle) * handle_len)
        pygame.draw.line(surface, _NS_vardrok.PALETTE["shadow_deep"],
                         (hx + 1, hy + 1), (handle_end_x + 1, handle_end_y + 1), 3)
        pygame.draw.line(surface, _NS_vardrok.PALETTE["leather_darkest"],
                         (hx, hy), (handle_end_x, handle_end_y), 3)
        pygame.draw.line(surface, _NS_vardrok.PALETTE["leather_mid"],
                         (hx, hy), (handle_end_x, handle_end_y), 1)
        # Axe head (round with 2 blades).
        head_x = hx + int(math.cos(angle) * 5) * facing
        head_y = hy + int(math.sin(angle) * 5)
        _NS_vardrok._draw_axe_head_static(surface, head_x, head_y, facing)
    def _draw_axe_head_static(surface, cx, cy, facing):
        """Draw static axe head (2 blades top/bottom)."""
        # Central circle.
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["shadow_deep"], (cx + 1, cy + 1), 3)
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["steel_dark"], (cx, cy), 3)
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["steel_mid"], (cx, cy), 2)
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["steel_light"], (cx, cy, 1, 1))
        # Top blade.
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["shadow_deep"], [
            (cx - 4 + 1, cy - 3 + 1),
            (cx + 4 + 1, cy - 3 + 1),
            (cx + 6 + 1, cy - 7 + 1),
            (cx - 6 + 1, cy - 7 + 1),
        ])
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["steel_darkest"], [
            (cx - 4, cy - 3),
            (cx + 4, cy - 3),
            (cx + 6, cy - 7),
            (cx - 6, cy - 7),
        ])
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["steel_dark"], [
            (cx - 3, cy - 3),
            (cx + 3, cy - 3),
            (cx + 5, cy - 6),
            (cx - 5, cy - 6),
        ])
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["steel_mid"], [
            (cx - 3, cy - 4),
            (cx + 3, cy - 4),
            (cx + 4, cy - 6),
            (cx - 4, cy - 6),
        ])
        # Blade edge.
        pygame.draw.line(surface, _NS_vardrok.PALETTE["steel_shine"],
                         (cx - 6, cy - 7), (cx + 6, cy - 7), 1)
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["white"], (cx - 5, cy - 7, 2, 1))
        # Bottom blade.
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["shadow_deep"], [
            (cx - 4 + 1, cy + 3 + 1),
            (cx + 4 + 1, cy + 3 + 1),
            (cx + 6 + 1, cy + 7 + 1),
            (cx - 6 + 1, cy + 7 + 1),
        ])
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["steel_darkest"], [
            (cx - 4, cy + 3),
            (cx + 4, cy + 3),
            (cx + 6, cy + 7),
            (cx - 6, cy + 7),
        ])
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["steel_dark"], [
            (cx - 3, cy + 3),
            (cx + 3, cy + 3),
            (cx + 5, cy + 6),
            (cx - 5, cy + 6),
        ])
        _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["steel_mid"], [
            (cx - 3, cy + 4),
            (cx + 3, cy + 4),
            (cx + 4, cy + 6),
            (cx - 4, cy + 6),
        ])
        pygame.draw.line(surface, _NS_vardrok.PALETTE["steel_shine"],
                         (cx - 6, cy + 7), (cx + 6, cy + 7), 1)
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["white"], (cx - 5, cy + 7, 2, 1))
        # Blood drips on blade.
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["blood_dark"], (cx, cy - 6, 1, 1))
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["blood_mid"], (cx + 2, cy + 5, 1, 1))
    # ================= SPINNING AXE (for projectiles) =================
    def _draw_spinning_axe(surface, cx, cy, phase, size=1.0, blood_trail=True):
        """Spinning axe with blood trail — used for all projectiles."""
        rotation = phase * 8  # fast spin
        blade_len = int(8 * size)
        blade_w = int(6 * size)
        # Blood mist behind (motion blur).
        if blood_trail:
            for r in range(int(blade_len + 4), int(blade_len), -1):
                alpha = _NS_vardrok._alpha(80 * (blade_len + 4 - r) / 4)
                _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_dark"], alpha), (cx, cy), r)
        # Central pivot.
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["shadow_deep"], (cx + 1, cy + 1), int(3 * size))
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["steel_darkest"], (cx, cy), int(3 * size))
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["steel_dark"], (cx, cy), int(2 * size))
        # 2 blades at opposite angles.
        for blade_i in range(2):
            angle = rotation + blade_i * math.pi
            # Blade tip.
            tip_x = cx + int(math.cos(angle) * blade_len)
            tip_y = cy + int(math.sin(angle) * blade_len)
            # Perpendicular for width.
            perp = angle + math.pi / 2
            side1 = (cx + int(math.cos(perp) * blade_w * 0.5) + int(math.cos(angle) * blade_len * 0.5),
                     cy + int(math.sin(perp) * blade_w * 0.5) + int(math.sin(angle) * blade_len * 0.5))
            side2 = (cx - int(math.cos(perp) * blade_w * 0.5) + int(math.cos(angle) * blade_len * 0.5),
                     cy - int(math.sin(perp) * blade_w * 0.5) + int(math.sin(angle) * blade_len * 0.5))
            # Blade shape.
            _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["shadow_deep"], [
                (cx + 1, cy + 1), (side1[0] + 1, side1[1] + 1),
                (tip_x + 1, tip_y + 1), (side2[0] + 1, side2[1] + 1),
            ])
            _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["steel_darkest"], [
                (cx, cy), side1, (tip_x, tip_y), side2,
            ])
            _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["steel_dark"], [
                (cx, cy),
                (int(side1[0] * 0.7 + cx * 0.3), int(side1[1] * 0.7 + cy * 0.3)),
                (tip_x, tip_y),
                (int(side2[0] * 0.7 + cx * 0.3), int(side2[1] * 0.7 + cy * 0.3)),
            ])
            _NS_vardrok._poly(surface, _NS_vardrok.PALETTE["steel_mid"], [
                (cx, cy),
                (int((cx + tip_x) / 2), int((cy + tip_y) / 2)),
                (tip_x, tip_y),
            ])
            # Blade edge.
            pygame.draw.line(surface, _NS_vardrok.PALETTE["steel_light"],
                             (cx, cy), (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_vardrok.PALETTE["steel_shine"], (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_vardrok.PALETTE["white"], (tip_x, tip_y, 1, 1))
            # Blood on blade tips.
            pygame.draw.rect(surface, _NS_vardrok.PALETTE["blood_mid"], (tip_x, tip_y, 1, 1))
        # Central hub bright.
        _NS_vardrok._aacircle(surface, _NS_vardrok.PALETTE["brass_mid"], (cx, cy), 1)
        pygame.draw.rect(surface, _NS_vardrok.PALETTE["brass_shine"], (cx, cy, 1, 1))
    # ================= BASIC ATTACK — THROWN AXE =================
    def _draw_thrown_axe(surface, boss, x, y, progress):
        """Spinning axe flies to target."""
        if progress < 0.4:
            return
        facing = boss.direction
        tx, ty = _NS_vardrok._target_position(boss, x, y)
        start_x = x + facing * 24
        start_y = y - 4
        t = (progress - 0.4) / 0.6
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Blood trail behind axe.
        for i in range(8):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_vardrok._alpha(200 - i * 25)
            trail_size = max(1, 6 - i)
            _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_darkest"], alpha), (px, py), trail_size)
            _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_dark"], alpha), (px, py), max(1, trail_size - 1))
            _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_mid"], alpha), (px, py), max(1, trail_size - 3))
            # Small blood droplets.
            if i < 4:
                for s in range(2):
                    dp_x = px + int(math.sin(t * 4 + i + s) * (trail_size + 1))
                    dp_y = py + int(math.cos(t * 4 + i + s) * (trail_size + 1))
                    pygame.draw.rect(surface, (*_NS_vardrok.PALETTE["blood_mid"], alpha), (dp_x, dp_y, 1, 1))
        # Draw spinning axe at current position.
        _NS_vardrok._draw_spinning_axe(surface, bx, by, boss.pulse * 2, size=1.0, blood_trail=False)
        # Impact splash.
        if t > 0.9:
            st = (t - 0.9) / 0.1
            radius = int(10 + st * 18)
            alpha = _NS_vardrok._alpha(240 * (1 - st))
            _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_dark"], alpha), (tx, ty), radius, 3)
            _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_mid"], alpha), (tx, ty), max(1, radius - 4), 2)
            _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_light"], alpha), (tx, ty), max(1, radius - 8), 1)
            # Blood splatter.
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_vardrok.PALETTE["blood_light"], alpha), (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_vardrok.PALETTE["blood_hot"], alpha), (ex, ey, 1, 1))
    # ================= IDLE ORBIT AXES (ambient) =================
    def _draw_idle_orbit_axes(surface, x, y, phase):
        """2 axes orbiting slowly around boss for style."""
        for i in range(2):
            orbit_angle = phase * 0.6 + i * math.pi
            orbit_r = 30
            ax = x + int(math.cos(orbit_angle) * orbit_r)
            ay = y + int(math.sin(orbit_angle) * orbit_r * 0.4) - 4
            _NS_vardrok._draw_spinning_axe(surface, ax, ay, phase * 2 + i * 2, size=0.75, blood_trail=False)
    # ================= AMBIENT / GROUND =================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((160, 34), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 17 - radius, 140 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (15, 3, 6, 180), (5, 10, 150, 14))
        pygame.draw.ellipse(shadow, (80, 15, 20, 130), (12, 12, 136, 10))
        surface.blit(shadow, (x - 80, y - 17))
    def _draw_blood_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_vardrok._alpha((90 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_vardrok._aacircle(aura, (*_NS_vardrok.PALETTE["blood_darkest"], alpha), (120, 100), radius)
        for radius in range(55, 5, -3):
            alpha = _NS_vardrok._alpha((55 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_vardrok._aacircle(aura, (*_NS_vardrok.PALETTE["blood_dark"], alpha), (120, 100), radius)
        for radius in range(30, 5, -2):
            alpha = _NS_vardrok._alpha((30 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_vardrok._aacircle(aura, (*_NS_vardrok.PALETTE["blood_mid"], alpha), (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))
        # Floating blood droplets.
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            radius = 42 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            sy -= int((phase * 6 + i * 5) % 22)
            color = _NS_vardrok.PALETTE["blood_dark"] if i % 2 == 0 else _NS_vardrok.PALETTE["blood_mid"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_vardrok.PALETTE["blood_light"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((190, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_vardrok.PALETTE["blood_darkest"], 200), (5, 20, 180, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_vardrok.PALETTE["blood_dark"], 220), (14, 22, 162, 26), 2)
        pygame.draw.ellipse(ring, (*_NS_vardrok.PALETTE["blood_mid"], 180), (25, 24, 140, 22), 1)
        # Splatter marks around ring.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 95 + int(math.cos(angle) * 74)
            y1 = 35 + int(math.sin(angle) * 12)
            pygame.draw.rect(ring, _NS_vardrok.PALETTE["blood_light"], (x1, y1, 2, 2))
            pygame.draw.rect(ring, _NS_vardrok.PALETTE["blood_hot"], (x1, y1, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_vardrok.PALETTE["blood_hot"], _NS_vardrok._alpha(150 * pulse)),
                                (15, 14, 160, 44), 1)
        surface.blit(ring, (x - 95, y - 30))
    def _draw_hover_particles(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Blood mist rising."""
        strength = 1.5 if intense else 1.0
        # Mist.
        mist = pygame.Surface((160, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(32, 3, -3):
            alpha = _NS_vardrok._alpha((32 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist, (*_NS_vardrok.PALETTE["blood_darkest"], alpha),
                                    (80 - radius * 2, 25 - radius // 3, radius * 4, max(3, radius // 2)))
        for radius in range(22, 3, -2):
            alpha = _NS_vardrok._alpha((22 - radius) * 3.2 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist, (*_NS_vardrok.PALETTE["blood_dark"], alpha),
                                    (80 - radius, 25 - radius // 4, radius * 2, max(2, radius // 3)))
        surface.blit(mist, (cx - 80, cy - 10))
        # Rising blood droplets.
        for i, offset in enumerate((-24, -14, -4, 6, 16, 26, -32, 32)):
            t = (phase * 0.5 + i * 0.15) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 22)
            alpha = _NS_vardrok._alpha(200 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_darkest"], alpha), (sx, sy), 3)
            _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_dark"], alpha), (sx, sy - 1), 2)
            _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_mid"], alpha), (sx, sy - 2), 1)
            pygame.draw.rect(surface, (*_NS_vardrok.PALETTE["blood_light"], alpha), (sx, sy - 2, 1, 1))
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_vardrok._alpha(160 - i * 30)
                if alpha <= 0:
                    continue
                _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_dark"], alpha),
                                      (sx, sy), max(2, 6 - i))
                _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_mid"], alpha),
                                      (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_vardrok.PALETTE["blood_light"], alpha),
                                 (sx, sy - 1, 2, 1))
    # ================= SKILL Q — BLOODSPIN AXE =================
    def _draw_bloodspin_axe(surface, boss, x, y, timer, phase):
        """Enhanced spinning axe with heavy blood trail."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vardrok._target_position(boss, x, y)
        start_x = x + facing * 24
        start_y = y - 4
        if progress < 0.15:
            # Charge.
            t = progress / 0.15
            hand_x = start_x
            hand_y = start_y
            _NS_vardrok._draw_spinning_axe(surface, hand_x, hand_y, phase * 4 * (1 + t),
                                           size=1.0 + t * 0.3, blood_trail=True)
            for r in range(int(10 * t), 0, -2):
                alpha = _NS_vardrok._alpha(150 * (10 * t - r) / max(1, 10 * t))
                _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_mid"], alpha),
                                      (hand_x, hand_y), r)
        else:
            t = (progress - 0.15) / 0.85
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Big blood trail.
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_vardrok._alpha(240 - i * 22)
                trail_size = max(1, 8 - i)
                _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_darkest"], alpha), (px, py), trail_size)
                _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_dark"], alpha), (px, py), max(1, trail_size - 1))
                _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_mid"], alpha), (px, py), max(1, trail_size - 3))
                _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_light"], alpha), (px, py), max(1, trail_size - 5))
                if i < 5:
                    for s in range(3):
                        dp_x = px + int(math.sin(t * 4 + i + s) * (trail_size + 2))
                        dp_y = py + int(math.cos(t * 4 + i + s) * (trail_size + 2))
                        pygame.draw.rect(surface, (*_NS_vardrok.PALETTE["blood_hot"], alpha), (dp_x, dp_y, 1, 1))
            # Bigger spinning axe.
            _NS_vardrok._draw_spinning_axe(surface, bx, by, phase * 3, size=1.3, blood_trail=True)
            # Impact.
            if t > 0.88:
                st = (t - 0.88) / 0.12
                radius = int(15 + st * 25)
                alpha = _NS_vardrok._alpha(240 * (1 - st))
                _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_darkest"], alpha), (tx, ty), radius + 4, 3)
                _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_dark"], alpha), (tx, ty), radius, 3)
                _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_mid"], alpha), (tx, ty), max(1, radius - 6), 2)
                _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_light"], alpha), (tx, ty), max(1, radius - 12), 1)
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface, (*_NS_vardrok.PALETTE["blood_hot"], alpha), (ex, ey, 2, 2))
                    pygame.draw.rect(surface, (*_NS_vardrok.PALETTE["blood_shine"], alpha), (ex, ey, 1, 1))
    # ================= SKILL W — BLOOD FRENZY (buff) =================
    def _draw_frenzy_ground(surface, boss, x, y, timer, pulse):
        """Blood ring pulsing at feet."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        intensity = math.sin(progress * math.pi)
        for i in range(3):
            r = int(38 + i * 8 + math.sin(pulse * 2) * 3)
            alpha_v = int((200 - i * 50) * intensity)
            alpha_i = _NS_vardrok._alpha(alpha_v)
            _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_dark"], alpha_i), (x, y + 44), r, 2)
            _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_light"], alpha_i), (x, y + 44), r, 1)
    def _draw_frenzy_aura(surface, boss, x, y, timer, pulse):
        """Blood mist + rising blood flames around body."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        intensity = math.sin(progress * math.pi)
        FX_W, FX_H = 180, 200
        fx_surf = pygame.Surface((FX_W, FX_H), pygame.SRCALPHA)
        ox, oy = FX_W // 2, FX_H // 2
        # Blood mist all around.
        for r in range(60, 5, -3):
            alpha = _NS_vardrok._alpha(80 * (60 - r) / 60 * intensity)
            _NS_vardrok._aacircle(fx_surf, (*_NS_vardrok.PALETTE["blood_dark"], alpha), (ox, oy), r)
        for r in range(40, 5, -2):
            alpha = _NS_vardrok._alpha(120 * (40 - r) / 40 * intensity)
            _NS_vardrok._aacircle(fx_surf, (*_NS_vardrok.PALETTE["blood_mid"], alpha), (ox, oy), r)
        # Blood streaks rising.
        num_streaks = 12
        for i in range(num_streaks):
            angle = i * math.pi * 2 / num_streaks + pulse * 0.2
            base_x = ox + int(math.cos(angle) * 30)
            base_y = oy + int(math.sin(angle) * 15) + 8
            for layer in range(6):
                layer_t = (pulse * 0.7 + i * 0.15 + layer * 0.15) % 1.0
                streak_y = base_y - int(layer_t * 45)
                streak_r = int(3 + layer_t * 3)
                streak_alpha = _NS_vardrok._alpha(220 * (1 - layer_t) * intensity)
                if streak_alpha <= 0:
                    continue
                pygame.draw.circle(fx_surf, (*_NS_vardrok.PALETTE["blood_darkest"], streak_alpha),
                                   (base_x, streak_y), streak_r + 1)
                pygame.draw.circle(fx_surf, (*_NS_vardrok.PALETTE["blood_dark"], streak_alpha),
                                   (base_x, streak_y), streak_r)
                pygame.draw.circle(fx_surf, (*_NS_vardrok.PALETTE["blood_mid"], streak_alpha),
                                   (base_x, streak_y - 1), max(1, streak_r - 1))
                pygame.draw.rect(fx_surf, (*_NS_vardrok.PALETTE["blood_light"], streak_alpha),
                                 (base_x, streak_y - 2, 1, 1))
        surface.blit(fx_surf, (x - ox, y - oy))
    # ================= SKILL E — TWIN CLEAVER (2 axes sideways) =================
    def _draw_twin_cleaver(surface, boss, x, y, timer, pulse):
        """Two axes fly perpendicular directions (up-forward + down-forward)."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vardrok._target_position(boss, x, y)
        start_x = x + facing * 24
        start_y = y - 4
        # Two axes: one goes up-fwd, one goes down-fwd.
        max_dist = 240
        for axe_i, y_offset in enumerate((-60, 60)):
            end_x = tx + facing * 40
            end_y = ty + y_offset
            if progress < 0.15:
                # Charge.
                t = progress / 0.15
                bx = start_x
                by = start_y
                _NS_vardrok._draw_spinning_axe(surface, bx, by, pulse * 4, size=1.0, blood_trail=True)
            else:
                t = (progress - 0.15) / 0.85
                bx = int(start_x + (end_x - start_x) * t)
                by = int(start_y + (end_y - start_y) * t)
                # Blood trail.
                for i in range(8):
                    trail_t = max(0.0, t - i * 0.06)
                    px = int(start_x + (end_x - start_x) * trail_t)
                    py = int(start_y + (end_y - start_y) * trail_t)
                    alpha = _NS_vardrok._alpha(230 - i * 25)
                    size = max(1, 7 - i)
                    _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_darkest"], alpha), (px, py), size)
                    _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_dark"], alpha), (px, py), max(1, size - 1))
                    _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_mid"], alpha), (px, py), max(1, size - 3))
                _NS_vardrok._draw_spinning_axe(surface, bx, by, pulse * 3 + axe_i * 2, size=1.1, blood_trail=True)
    # ================= SKILL R — WHIRLWIND MASSACRE =================
    def _draw_whirlwind_ground(surface, boss, x, y, timer, pulse):
        """Circular blood ring."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(80 * min(1.0, progress * 3))
        if r > 5:
            pygame.draw.ellipse(surface, (*_NS_vardrok.PALETTE["blood_darkest"], 220),
                                (x - r, y + 24 - r // 4, r * 2, r * 2 // 4))
            pygame.draw.ellipse(surface, (*_NS_vardrok.PALETTE["blood_dark"], 200),
                                (x - r + 4, y + 24 - r // 4 + 2, r * 2 - 8, r * 2 // 4 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_vardrok.PALETTE["blood_mid"], 170),
                                (x - r + 10, y + 24 - r // 4 + 4, r * 2 - 20, r * 2 // 4 - 8), 1)
    def _draw_whirlwind_massacre(surface, boss, x, y, timer, pulse):
        """Multiple axes orbiting boss + blood tornado."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        intensity = math.sin(progress * math.pi) if progress < 0.85 else (1 - progress) / 0.15
        intensity = max(0, min(1, intensity))
        num_axes = 6
        for i in range(num_axes):
            orbit_angle = pulse * 3 + i * math.pi * 2 / num_axes
            orbit_r = 50 + int(math.sin(pulse * 2 + i) * 8)
            ax = x + int(math.cos(orbit_angle) * orbit_r)
            ay = y + int(math.sin(orbit_angle) * orbit_r * 0.6)
            # Motion arc trail.
            for trail_i in range(6):
                trail_a = orbit_angle - trail_i * 0.2
                tx_ = x + int(math.cos(trail_a) * orbit_r)
                ty_ = y + int(math.sin(trail_a) * orbit_r * 0.6)
                trail_alpha = _NS_vardrok._alpha(200 * intensity * (1 - trail_i * 0.15))
                _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_dark"], trail_alpha),
                                      (tx_, ty_), max(1, 5 - trail_i))
                _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_mid"], trail_alpha),
                                      (tx_, ty_), max(1, 3 - trail_i))
            _NS_vardrok._draw_spinning_axe(surface, ax, ay, pulse * 4 + i, size=1.1, blood_trail=True)
            # Sparks around each axe.
            for s in range(3):
                spark_a = orbit_angle + s * 0.5
                spark_r = orbit_r + 8 + s * 2
                spx = x + int(math.cos(spark_a) * spark_r)
                spy = y + int(math.sin(spark_a) * spark_r * 0.6)
                sp_alpha = _NS_vardrok._alpha(220 * intensity)
                pygame.draw.rect(surface, (*_NS_vardrok.PALETTE["blood_hot"], sp_alpha), (spx, spy, 2, 2))
                pygame.draw.rect(surface, (*_NS_vardrok.PALETTE["blood_shine"], sp_alpha), (spx, spy, 1, 1))
        # Central blood tornado.
        for ring_i in range(4):
            ring_r = 30 + ring_i * 10 + int(math.sin(pulse * 3) * 3)
            alpha = _NS_vardrok._alpha(150 * intensity * (1 - ring_i * 0.2))
            _NS_vardrok._aacircle(surface, (*_NS_vardrok.PALETTE["blood_mid"], alpha), (x, y), ring_r, 1)



# ====================================================================
# KAINEROTH (CROW-EYED) - TRUE BOSS
# ====================================================================

class _NS_kaineroth:
    """Namespace kaineroth - dark ninja illusionist boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Cloak black
        "cloak_darkest": (5, 3, 8),
        "cloak_dark": (18, 12, 22),
        "cloak_mid": (35, 25, 42),
        "cloak_light": (60, 45, 70),
        "cloak_edge": (95, 75, 110),
        # Red cloud accents (on cloak)
        "cloud_dark": (85, 15, 20),
        "cloud_mid": (170, 35, 45),
        "cloud_light": (230, 70, 80),
        "cloud_edge": (255, 130, 130),
        # Skin (pale ninja)
        "skin_dark": (145, 115, 100),
        "skin_mid": (210, 175, 155),
        "skin_light": (245, 220, 200),
        "skin_shine": (255, 240, 225),
        # Black hair
        "hair_darkest": (5, 3, 8),
        "hair_dark": (20, 15, 25),
        "hair_mid": (45, 35, 55),
        "hair_light": (75, 60, 90),
        # Headband (silver plate + blue cloth)
        "band_dark": (25, 30, 45),
        "band_mid": (55, 65, 90),
        "band_light": (110, 125, 155),
        "metal_dark": (60, 60, 65),
        "metal_mid": (130, 130, 140),
        "metal_light": (210, 210, 220),
        "metal_shine": (250, 250, 255),
        # Sharingan RED eye
        "eye_socket": (15, 3, 5),
        "eye_darkest": (30, 3, 5),
        "eye_dark": (110, 15, 20),
        "eye_mid": (215, 30, 40),
        "eye_light": (255, 80, 85),
        "eye_hot": (255, 180, 180),
        "eye_glow": (255, 255, 255),
        # Red flame (normal fire)
        "flame_darkest": (35, 5, 5),
        "flame_dark": (130, 20, 15),
        "flame_mid": (235, 65, 30),
        "flame_light": (255, 145, 55),
        "flame_hot": (255, 210, 120),
        "flame_shine": (255, 250, 200),
        # Black flame (Amaterasu-like)
        "black_flame_dark": (8, 3, 12),
        "black_flame_mid": (25, 8, 30),
        "black_flame_hot": (60, 15, 60),
        "black_flame_edge": (135, 30, 130),
        # Kunai steel
        "steel_dark": (30, 32, 40),
        "steel_mid": (95, 100, 115),
        "steel_light": (175, 180, 195),
        "steel_shine": (240, 245, 255),
        # Crow feathers (for FX)
        "crow_dark": (10, 8, 15),
        "crow_mid": (30, 25, 40),
        "crow_edge": (75, 65, 95),
        # Void/nightmare purple
        "void_dark": (25, 8, 35),
        "void_mid": (75, 25, 100),
        "void_light": (150, 90, 190),
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
        color = _NS_kaineroth._clamp(color)
        if _NS_kaineroth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_kaineroth._clamp(color)
        if _NS_kaineroth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_kaineroth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ================= ENTRY POINT =================
    def draw_kaineroth(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kaineroth._detect_moving(boss)
        _NS_kaineroth._update_knt_attack_anim(boss)
        attacking = (
            getattr(boss, "_knt_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        _NS_kaineroth._draw_shadow_aura(surface, x, y, pulse)
        _NS_kaineroth._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX (behind body).
        if active_skill == "q":
            _NS_kaineroth._draw_blackflame_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaineroth._draw_fireball_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaineroth._draw_prison_ground(surface, boss, x, y, skill_timer, pulse)
        # Crow FX around body (constant ambient).
        _NS_kaineroth._draw_ambient_crows(surface, x, y, pulse)
        # Body.
        if attacking:
            _NS_kaineroth._draw_knt_attack(surface, boss, x, y)
        elif moving:
            _NS_kaineroth._draw_knt_walk(surface, boss, x, y)
        else:
            _NS_kaineroth._draw_knt_idle(surface, boss, x, y)
        # Foreground FX.
        if active_skill == "q":
            _NS_kaineroth._draw_blackflame_projectile(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kaineroth._draw_sharingan_activation(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaineroth._draw_grand_fireball(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaineroth._draw_mind_prison_dome(surface, boss, x, y, skill_timer, pulse)
    # ================= ANIMATION STATE =================
    def _update_knt_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_knt_previous_timer", 0))
        active = bool(getattr(boss, "_knt_attack_active", False))
        if not active and previous > timer and previous >= cooldown - 2:
            boss._knt_attack_active = True
            boss._knt_attack_frame = 0
            active = True
        elif active:
            boss._knt_attack_frame = int(getattr(boss, "_knt_attack_frame", 0)) + 1
            if boss._knt_attack_frame >= cooldown:
                boss._knt_attack_active = False
                boss._knt_attack_frame = 0
                active = False
        boss._knt_previous_timer = timer
        boss._knt_attack_progress = (
            min(1.0, getattr(boss, "_knt_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_knt_last_x"):
            boss._knt_last_x = boss.x
            boss._knt_last_y = boss.y
            return False
        dx = abs(boss.x - boss._knt_last_x)
        dy = abs(boss.y - boss._knt_last_y)
        boss._knt_last_x = boss.x
        boss._knt_last_y = boss.y
        return dx + dy > 0.3
    # ================= POSE ROUTERS =================
    def _draw_knt_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_kaineroth._draw_shadow(surface, x, y + 50)
        _NS_kaineroth._draw_shadow_wisps(surface, x, y + 44, boss.pulse)
        _NS_kaineroth._draw_knt_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")
    def _draw_knt_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 6)
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_kaineroth._draw_shadow(surface, x + sway, y + 50)
        _NS_kaineroth._draw_shadow_wisps(surface, x + sway, y + 44, phase, trail=True, facing=boss.direction)
        _NS_kaineroth._draw_knt_body(surface, x + sway, y + bob, boss.direction, phase, "walk")
    def _draw_knt_attack(surface, boss, x, y):
        progress = getattr(boss, "_knt_attack_progress", None)
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
        _NS_kaineroth._draw_shadow(surface, x + lunge, y + 50)
        _NS_kaineroth._draw_shadow_wisps(surface, x + lunge, y + 44, boss.pulse, intense=True)
        _NS_kaineroth._draw_knt_body(surface, x + lunge, y - lift, boss.direction, boss.pulse, "attack", progress)
        _NS_kaineroth._draw_kunai_swing(surface, boss, x + lunge, y - lift, progress)
    # ================= BODY =================
    def _draw_knt_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Back cloak billowing.
        _NS_kaineroth._draw_back_cloak(surface, cx, cy, facing, phase)
        # Legs (floating).
        _NS_kaineroth._draw_ninja_legs(surface, cx, cy + 14, facing, phase, action)
        # Main torso (cloak with red clouds).
        _NS_kaineroth._draw_cloak_torso(surface, cx, cy, facing, phase)
        # Back arm (non-weapon).
        _NS_kaineroth._draw_back_arm(surface, cx, cy, facing, phase, action)
        # Head (hair + headband).
        _NS_kaineroth._draw_ninja_head(surface, cx, cy - 20, facing, phase, action)
        # High collar (cloak neck).
        _NS_kaineroth._draw_high_collar(surface, cx, cy - 12, facing, phase)
        # Front arm with kunai.
        _NS_kaineroth._draw_kunai_arm(surface, cx, cy, facing, phase, action, attack_progress)
    def _draw_back_cloak(surface, cx, cy, facing, phase):
        """Cloak billowing behind body."""
        wave = math.sin(phase * 0.9) * 3
        back_dir = -facing
        cloak_shape = [
            (cx + back_dir * 6, cy - 14),
            (cx + back_dir * 12, cy - 8),
            (cx + back_dir * 18 + int(wave), cy - 2),
            (cx + back_dir * 22 + int(wave * 0.8), cy + 6),
            (cx + back_dir * 20 + int(wave * 0.6), cy + 14),
            (cx + back_dir * 14, cy + 20),
            (cx + back_dir * 6, cy + 22),
            (cx + back_dir * 2, cy + 18),
            (cx + back_dir * 1, cy - 10),
        ]
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in cloak_shape])
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["cloak_darkest"], cloak_shape)
        # Inner darker layer.
        inner_shape = [
            (cx + back_dir * 4, cy - 12),
            (cx + back_dir * 10, cy - 6),
            (cx + back_dir * 14 + int(wave * 0.5), cy),
            (cx + back_dir * 16 + int(wave * 0.3), cy + 8),
            (cx + back_dir * 12, cy + 16),
            (cx + back_dir * 5, cy + 18),
            (cx + back_dir * 2, cy + 14),
            (cx + back_dir * 1, cy - 8),
        ]
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["cloak_dark"], inner_shape)
        # Red cloud on back.
        cloud_x = cx + back_dir * 10
        cloud_y = cy + 4
        for offset in [(0, 0, 3), (3, 1, 2), (-3, 2, 2), (2, -2, 2), (-2, -1, 2)]:
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["cloud_dark"],
                                    (cloud_x + offset[0], cloud_y + offset[1]), offset[2])
        for offset in [(0, 0, 2), (2, 1, 1), (-2, 1, 1)]:
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["cloud_mid"],
                                    (cloud_x + offset[0], cloud_y + offset[1]), offset[2])
        pygame.draw.rect(surface, _NS_kaineroth.PALETTE["cloud_light"], (cloud_x, cloud_y, 1, 1))
    def _draw_ninja_legs(surface, cx, cy, facing, phase, action):
        """Legs covered by cloak bottom (mostly hidden)."""
        leg_bob = math.sin(phase * 0.8) * 2 if action != "walk" else math.sin(phase * 1.5) * 4
        # Cloak bottom hem.
        hem_shape = [
            (cx - 14, cy - 4),
            (cx + 14, cy - 4),
            (cx + 16, cy + 4),
            (cx + 12, cy + 10),
            (cx + 6, cy + 12),
            (cx - 6, cy + 12),
            (cx - 12, cy + 10),
            (cx - 16, cy + 4),
        ]
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in hem_shape])
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["cloak_darkest"], hem_shape)
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["cloak_dark"], [
            (cx - 13, cy - 3),
            (cx + 13, cy - 3),
            (cx + 14, cy + 3),
            (cx + 10, cy + 9),
            (cx - 10, cy + 9),
            (cx - 14, cy + 3),
        ])
        # Red cloud on hem.
        cloud_x = cx - 7
        cloud_y = cy + 4
        for offset in [(0, 0, 2), (2, 1, 1), (-2, 0, 2), (1, -1, 1)]:
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["cloud_dark"],
                                    (cloud_x + offset[0], cloud_y + offset[1]), offset[2])
        pygame.draw.rect(surface, _NS_kaineroth.PALETTE["cloud_mid"], (cloud_x, cloud_y, 1, 1))
        pygame.draw.rect(surface, _NS_kaineroth.PALETTE["cloud_light"], (cloud_x, cloud_y, 1, 1))
        # Legs peek at bottom (feet).
        for side in (-1, 1):
            foot_x = cx + side * 5
            foot_y = cy + 12 + int(leg_bob * side * 0.3)
            _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["shadow_deep"], [
                (foot_x - 3 + 1, foot_y - 1 + 1),
                (foot_x + 3 + 1, foot_y - 1 + 1),
                (foot_x + 2 + 1, foot_y + 2 + 1),
                (foot_x - 2 + 1, foot_y + 2 + 1),
            ])
            _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["cloak_darkest"], [
                (foot_x - 3, foot_y - 1),
                (foot_x + 3, foot_y - 1),
                (foot_x + 2, foot_y + 2),
                (foot_x - 2, foot_y + 2),
            ])
            _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["cloak_mid"], [
                (foot_x - 2, foot_y),
                (foot_x + 2, foot_y),
                (foot_x + 1, foot_y + 1),
                (foot_x - 1, foot_y + 1),
            ])
    def _draw_cloak_torso(surface, cx, cy, facing, phase):
        """Main torso covered in black cloak with red clouds."""
        breath = math.sin(phase * 0.7) * 1
        # V-shape torso.
        torso_shape = [
            (cx - 13, cy - 10),
            (cx - 15, cy - 4),
            (cx - 14, cy + 4),
            (cx - 12, cy + 12),
            (cx - 6, cy + 14),
            (cx + 6, cy + 14),
            (cx + 12, cy + 12),
            (cx + 14, cy + 4),
            (cx + 15, cy - 4),
            (cx + 13, cy - 10),
            (cx + 6, cy - 12),
            (cx - 6, cy - 12),
        ]
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in torso_shape])
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["cloak_darkest"], torso_shape)
        # Cloak dark fill.
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["cloak_dark"], [
            (cx - 12, cy - 9),
            (cx - 14, cy - 3),
            (cx - 13, cy + 3),
            (cx - 10, cy + 11),
            (cx + 10, cy + 11),
            (cx + 13, cy + 3),
            (cx + 14, cy - 3),
            (cx + 12, cy - 9),
            (cx + 5, cy - 11),
            (cx - 5, cy - 11),
        ])
        # Cloak mid highlight (vertical fold lines).
        for fold_x in (-6, 0, 6):
            pygame.draw.line(surface, _NS_kaineroth.PALETTE["cloak_mid"],
                             (cx + fold_x, cy - 10), (cx + fold_x, cy + 12), 1)
        # Central Y-shape cloak opening (front fold).
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["cloak_darkest"], [
            (cx - 2, cy - 12),
            (cx + 2, cy - 12),
            (cx + 4, cy + 14),
            (cx - 4, cy + 14),
        ])
        pygame.draw.line(surface, _NS_kaineroth.PALETTE["cloak_edge"],
                         (cx - 2, cy - 12), (cx - 3, cy + 14), 1)
        pygame.draw.line(surface, _NS_kaineroth.PALETTE["cloak_edge"],
                         (cx + 2, cy - 12), (cx + 3, cy + 14), 1)
        # RED CLOUD on chest (Akatsuki style).
        cloud_x = cx + facing * 6
        cloud_y = cy + 2
        for offset in [(0, 0, 3), (3, 1, 2), (-3, 2, 2), (2, -2, 2), (-2, -1, 2), (1, 3, 1)]:
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["cloud_dark"],
                                    (cloud_x + offset[0], cloud_y + offset[1]), offset[2])
        for offset in [(0, 0, 2), (2, 1, 1), (-2, 1, 1)]:
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["cloud_mid"],
                                    (cloud_x + offset[0], cloud_y + offset[1]), offset[2])
        pygame.draw.rect(surface, _NS_kaineroth.PALETTE["cloud_light"], (cloud_x, cloud_y, 1, 1))
        pygame.draw.rect(surface, _NS_kaineroth.PALETTE["cloud_edge"], (cloud_x, cloud_y, 1, 1))
        # Shoulder highlights.
        for side in (-1, 1):
            sh_x = cx + side * 12
            sh_y = cy - 8
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["cloak_mid"], (sh_x, sh_y), 3)
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["cloak_light"], (sh_x - 1, sh_y - 1), 1)
    def _draw_high_collar(surface, cx, cy, facing, phase):
        """Tall cloak collar around neck."""
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["shadow_deep"], [
            (cx - 7 + 1, cy + 2 + 1),
            (cx - 8 + 1, cy - 4 + 1),
            (cx - 5 + 1, cy - 8 + 1),
            (cx + 5 + 1, cy - 8 + 1),
            (cx + 8 + 1, cy - 4 + 1),
            (cx + 7 + 1, cy + 2 + 1),
        ])
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["cloak_darkest"], [
            (cx - 7, cy + 2),
            (cx - 8, cy - 4),
            (cx - 5, cy - 8),
            (cx + 5, cy - 8),
            (cx + 8, cy - 4),
            (cx + 7, cy + 2),
        ])
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["cloak_dark"], [
            (cx - 6, cy + 1),
            (cx - 7, cy - 3),
            (cx - 4, cy - 7),
            (cx + 4, cy - 7),
            (cx + 7, cy - 3),
            (cx + 6, cy + 1),
        ])
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["cloak_mid"], [
            (cx - 5, cy),
            (cx - 5, cy - 4),
            (cx + 5, cy - 4),
            (cx + 5, cy),
        ])
        # Rim highlight.
        pygame.draw.line(surface, _NS_kaineroth.PALETTE["cloak_edge"],
                         (cx - 5, cy - 7), (cx + 5, cy - 7), 1)
    def _draw_ninja_head(surface, cx, cy, facing, phase, action):
        """Head with black hair, pale skin, headband."""
        # Hair back (mass covering back of head).
        hair_shape_back = [
            (cx - 7, cy + 6),
            (cx - 9, cy - 2),
            (cx - 8, cy - 8),
            (cx - 5, cy - 10),
            (cx + 5, cy - 10),
            (cx + 8, cy - 8),
            (cx + 9, cy - 2),
            (cx + 7, cy + 6),
            (cx + 4, cy + 8),
            (cx - 4, cy + 8),
        ]
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in hair_shape_back])
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["hair_darkest"], hair_shape_back)
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["hair_dark"], [
            (cx - 6, cy + 5),
            (cx - 8, cy - 2),
            (cx - 7, cy - 7),
            (cx - 4, cy - 9),
            (cx + 4, cy - 9),
            (cx + 7, cy - 7),
            (cx + 8, cy - 2),
            (cx + 6, cy + 5),
        ])
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["hair_mid"], [
            (cx - 5, cy - 3),
            (cx - 6, cy - 6),
            (cx + 6, cy - 6),
            (cx + 5, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_kaineroth.PALETTE["hair_light"], (cx - 2, cy - 6, 1, 1))
        pygame.draw.rect(surface, _NS_kaineroth.PALETTE["hair_light"], (cx + 2, cy - 6, 1, 1))
        # Face (pale skin).
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["skin_dark"], [
            (cx - 4, cy),
            (cx - 5, cy + 3),
            (cx - 3, cy + 6),
            (cx + 3, cy + 6),
            (cx + 5, cy + 3),
            (cx + 4, cy),
        ])
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["skin_mid"], [
            (cx - 3, cy + 1),
            (cx - 4, cy + 3),
            (cx - 2, cy + 5),
            (cx + 2, cy + 5),
            (cx + 4, cy + 3),
            (cx + 3, cy + 1),
        ])
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["skin_light"], [
            (cx - 2, cy + 2),
            (cx + 2, cy + 2),
            (cx + 2, cy + 4),
            (cx - 2, cy + 4),
        ])
        pygame.draw.rect(surface, _NS_kaineroth.PALETTE["skin_shine"], (cx - 1, cy + 2, 1, 1))
        # Front hair strands hanging.
        for strand_x in (-3, 3):
            pygame.draw.line(surface, _NS_kaineroth.PALETTE["hair_darkest"],
                             (cx + strand_x, cy - 4), (cx + strand_x, cy + 4), 1)
            pygame.draw.line(surface, _NS_kaineroth.PALETTE["hair_dark"],
                             (cx + strand_x, cy - 4), (cx + strand_x, cy + 4), 1)
        # HEADBAND (silver plate on blue cloth).
        band_y = cy - 3
        # Cloth (blue).
        pygame.draw.rect(surface, _NS_kaineroth.PALETTE["band_dark"], (cx - 7, band_y - 1, 14, 3))
        pygame.draw.rect(surface, _NS_kaineroth.PALETTE["band_mid"], (cx - 7, band_y, 14, 2))
        pygame.draw.rect(surface, _NS_kaineroth.PALETTE["band_light"], (cx - 7, band_y, 14, 1))
        # Metal plate (center).
        pygame.draw.rect(surface, _NS_kaineroth.PALETTE["metal_dark"], (cx - 4, band_y - 1, 8, 3))
        pygame.draw.rect(surface, _NS_kaineroth.PALETTE["metal_mid"], (cx - 3, band_y - 1, 6, 3))
        pygame.draw.rect(surface, _NS_kaineroth.PALETTE["metal_light"], (cx - 3, band_y, 6, 1))
        pygame.draw.rect(surface, _NS_kaineroth.PALETTE["metal_shine"], (cx - 2, band_y, 1, 1))
        # Small engraving mark on plate.
        pygame.draw.rect(surface, _NS_kaineroth.PALETTE["metal_dark"], (cx - 1, band_y, 2, 1))
        pygame.draw.rect(surface, _NS_kaineroth.PALETTE["shadow_deep"], (cx, band_y, 1, 1))
        # SHARINGAN EYES (red glowing).
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_off in (-2, 2):
            ex = cx + eye_off
            ey = cy + 3
            # Socket.
            pygame.draw.rect(surface, _NS_kaineroth.PALETTE["eye_socket"], (ex - 1, ey - 1, 2, 2))
            # Red glow.
            for r in range(4, 0, -1):
                alpha = _NS_kaineroth._alpha(140 * (4 - r) / 4 * eye_pulse)
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["eye_mid"], alpha), (ex, ey), r)
            # Iris.
            pygame.draw.rect(surface, _NS_kaineroth.PALETTE["eye_dark"], (ex - 1, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_kaineroth.PALETTE["eye_mid"], (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_kaineroth.PALETTE["eye_light"], (ex, ey, 1, 1))
            # Pupil (black dot).
            pygame.draw.rect(surface, _NS_kaineroth.PALETTE["shadow_deep"], (ex, ey, 1, 1))
            # Shine.
            pygame.draw.rect(surface, _NS_kaineroth.PALETTE["eye_hot"], (ex + 1, ey - 1, 1, 1))
        # Mouth.
        if action == "attack":
            pygame.draw.line(surface, _NS_kaineroth.PALETTE["skin_dark"],
                             (cx - 2, cy + 5), (cx + 2, cy + 5), 1)
        else:
            pygame.draw.line(surface, _NS_kaineroth.PALETTE["skin_dark"],
                             (cx - 1, cy + 5), (cx + 1, cy + 5), 1)
    def _draw_back_arm(surface, cx, cy, facing, phase, action):
        """Back arm (mostly hidden by cloak, just sleeve peek)."""
        back_dir = -facing
        sway = math.sin(phase * 0.6) * 1
        shoulder_x = cx + back_dir * 8
        shoulder_y = cy - 6
        hand_x = cx + back_dir * 6
        hand_y = cy + 6 + int(sway)
        # Sleeve (cloak arm).
        _NS_kaineroth._aaline(surface, _NS_kaineroth.PALETTE["shadow_deep"],
                              (shoulder_x + 1, shoulder_y + 1), (hand_x + 1, hand_y + 1), 6)
        _NS_kaineroth._aaline(surface, _NS_kaineroth.PALETTE["cloak_darkest"],
                              (shoulder_x, shoulder_y), (hand_x, hand_y), 6)
        _NS_kaineroth._aaline(surface, _NS_kaineroth.PALETTE["cloak_dark"],
                              (shoulder_x, shoulder_y), (hand_x, hand_y), 4)
        _NS_kaineroth._aaline(surface, _NS_kaineroth.PALETTE["cloak_mid"],
                              (shoulder_x, shoulder_y - 1), (hand_x, hand_y - 1), 1)
        # Fist (skin).
        _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["skin_dark"], (hand_x, hand_y), 2)
        _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["skin_mid"], (hand_x, hand_y), 1)
    def _draw_kunai_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding kunai — with swing animation."""
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
            swing_angle = math.pi * 0.1 + math.sin(phase * 0.6) * 0.1
            arm_length = 20
        shoulder_x = cx + facing * 12
        shoulder_y = cy - 6
        hand_x = shoulder_x + int(math.cos(swing_angle) * arm_length) * facing
        hand_y = shoulder_y + int(math.sin(swing_angle) * arm_length)
        elbow_x = (shoulder_x + hand_x) // 2 + facing * 1
        elbow_y = (shoulder_y + hand_y) // 2
        # Sleeve upper arm.
        _NS_kaineroth._aaline(surface, _NS_kaineroth.PALETTE["shadow_deep"],
                              (shoulder_x + 1, shoulder_y + 1), (elbow_x + 1, elbow_y + 1), 7)
        _NS_kaineroth._aaline(surface, _NS_kaineroth.PALETTE["cloak_darkest"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 7)
        _NS_kaineroth._aaline(surface, _NS_kaineroth.PALETTE["cloak_dark"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_kaineroth._aaline(surface, _NS_kaineroth.PALETTE["cloak_mid"],
                              (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 2)
        # Sleeve forearm.
        _NS_kaineroth._aaline(surface, _NS_kaineroth.PALETTE["cloak_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_kaineroth._aaline(surface, _NS_kaineroth.PALETTE["cloak_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 3)
        # Hand (skin).
        _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["skin_dark"], (hand_x, hand_y), 3)
        _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["skin_mid"], (hand_x, hand_y), 2)
        _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["skin_light"], (hand_x - 1, hand_y - 1), 1)
        # KUNAI.
        _NS_kaineroth._draw_kunai(surface, hand_x, hand_y, facing, phase, swing_angle)
    def _draw_kunai(surface, hx, hy, facing, phase, angle):
        """Kunai knife extending from hand."""
        # Direction of blade.
        blade_len = 12
        blade_end_x = hx + int(math.cos(angle) * blade_len) * facing
        blade_end_y = hy + int(math.sin(angle) * blade_len)
        # Handle behind hand.
        handle_x = hx - int(math.cos(angle) * 5) * facing
        handle_y = hy - int(math.sin(angle) * 5)
        # Handle (wrap).
        pygame.draw.line(surface, _NS_kaineroth.PALETTE["cloak_darkest"],
                         (handle_x, handle_y), (hx, hy), 4)
        pygame.draw.line(surface, _NS_kaineroth.PALETTE["cloak_dark"],
                         (handle_x, handle_y), (hx, hy), 2)
        # Blade (dagger shape).
        perp_angle = angle + math.pi / 2
        wide_side = 2
        p1 = (hx + int(math.cos(perp_angle) * wide_side),
              hy + int(math.sin(perp_angle) * wide_side))
        p2 = (hx - int(math.cos(perp_angle) * wide_side),
              hy - int(math.sin(perp_angle) * wide_side))
        p3 = (blade_end_x, blade_end_y)
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["shadow_deep"],
                            [(p1[0] + 1, p1[1] + 1), (p2[0] + 1, p2[1] + 1), (p3[0] + 1, p3[1] + 1)])
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["steel_dark"], [p1, p2, p3])
        # Highlight.
        _NS_kaineroth._poly(surface, _NS_kaineroth.PALETTE["steel_mid"], [
            p1,
            (int((p1[0] + p3[0]) / 2), int((p1[1] + p3[1]) / 2)),
            (hx, hy),
        ])
        pygame.draw.line(surface, _NS_kaineroth.PALETTE["steel_light"],
                         (hx, hy), blade_end_x if False else (blade_end_x, blade_end_y), 1)
        # Blade tip shine.
        pygame.draw.rect(surface, _NS_kaineroth.PALETTE["steel_shine"],
                         (blade_end_x, blade_end_y, 1, 1))
        # Ring at handle end.
        _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["steel_dark"], (handle_x, handle_y), 2)
        _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["steel_mid"], (handle_x, handle_y), 1)
    # ================= MELEE SWING FX =================
    def _draw_kunai_swing(surface, boss, x, y, progress):
        """Red flame trail from kunai swing."""
        if progress < 0.30 or progress > 0.80:
            return
        facing = boss.direction
        if progress < 0.6:
            swing_t = (progress - 0.30) / 0.30
        else:
            swing_t = 1.0 - (progress - 0.6) / 0.20
        swing_t = max(0.0, min(1.0, swing_t))
        alpha_base = _NS_kaineroth._alpha(255 * swing_t)
        if alpha_base <= 5:
            return
        cx_sh = x + facing * 12
        cy_sh = y - 6
        if progress < 0.35:
            current_angle = -math.pi * 0.65
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            t_eased = 1 - (1 - t) ** 2
            current_angle = -math.pi * 0.65 + t_eased * math.pi * 0.95
        else:
            current_angle = math.pi * 0.3
        start_angle = -math.pi * 0.65
        arc_length = 32
        FX_W, FX_H = 220, 220
        fx_surf = pygame.Surface((FX_W, FX_H), pygame.SRCALPHA)
        ox, oy = FX_W // 2, FX_H // 2
        def to_fx(wx, wy):
            return (wx - cx_sh + ox, wy - cy_sh + oy)
        # ARC TRAIL layered (red flame).
        for thickness, alpha_mult, color, radius_off in [
            (9, 0.35, _NS_kaineroth.PALETTE["flame_darkest"], 3),
            (7, 0.55, _NS_kaineroth.PALETTE["flame_dark"], 1),
            (5, 0.80, _NS_kaineroth.PALETTE["flame_mid"], 0),
            (3, 1.00, _NS_kaineroth.PALETTE["flame_light"], 0),
            (2, 1.00, _NS_kaineroth.PALETTE["flame_hot"], 0),
            (1, 1.00, _NS_kaineroth.PALETTE["flame_shine"], 0),
        ]:
            steps = 24
            prev = None
            for s in range(steps + 1):
                seg_t = s / steps
                seg_alpha = _NS_kaineroth._alpha(alpha_base * alpha_mult * (0.25 + 0.75 * seg_t))
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
            a = _NS_kaineroth._alpha(alpha_base * (12 - r) / 12 * 1.3)
            if a > 0:
                pygame.draw.circle(fx_surf, (*_NS_kaineroth.PALETTE["flame_hot"], a), (lfx, lfy), r)
        pygame.draw.circle(fx_surf, (*_NS_kaineroth.PALETTE["flame_shine"], alpha_base), (lfx, lfy), 3)
        pygame.draw.circle(fx_surf, (*_NS_kaineroth.PALETTE["white"], alpha_base), (lfx, lfy), 1)
        # SLASH LINES (blood-red streak).
        for slash_i in range(3):
            slash_offset = (slash_i - 1) * 0.10
            slash_a = current_angle + slash_offset
            slash_alpha = _NS_kaineroth._alpha(alpha_base * (1 - abs(slash_offset) * 4))
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
            pygame.draw.line(fx_surf, (*_NS_kaineroth.PALETTE["flame_shine"], slash_alpha), p1, p2, 4 - slash_i)
            pygame.draw.line(fx_surf, (*_NS_kaineroth.PALETTE["white"], slash_alpha), p1, p2, 1)
        # SPARKS + CROW FEATHERS.
        for i in range(14):
            spark_seed = i * 0.7 + progress * 4
            spark_a = current_angle + math.sin(spark_seed) * 0.5
            spark_r = arc_length + 6 + (i % 4) * 5 + int(swing_t * 10)
            wspx = cx_sh + int(math.cos(spark_a) * spark_r) * facing
            wspy = cy_sh + int(math.sin(spark_a) * spark_r)
            spx, spy = to_fx(wspx, wspy)
            spark_alpha = _NS_kaineroth._alpha(alpha_base * (0.7 + (i % 3) * 0.1))
            # Every 4th is a crow feather instead of spark.
            if i % 4 == 0:
                pygame.draw.rect(fx_surf, (*_NS_kaineroth.PALETTE["crow_dark"], spark_alpha), (spx - 1, spy, 3, 1))
                pygame.draw.rect(fx_surf, (*_NS_kaineroth.PALETTE["crow_mid"], spark_alpha), (spx, spy, 2, 1))
            else:
                tail_wx = wspx - int(math.cos(spark_a) * 4) * facing
                tail_wy = wspy - int(math.sin(spark_a) * 4)
                tfx, tfy = to_fx(tail_wx, tail_wy)
                pygame.draw.line(fx_surf, (*_NS_kaineroth.PALETTE["flame_mid"], spark_alpha), (tfx, tfy), (spx, spy), 2)
                pygame.draw.rect(fx_surf, (*_NS_kaineroth.PALETTE["flame_hot"], spark_alpha), (spx, spy, 2, 2))
                pygame.draw.rect(fx_surf, (*_NS_kaineroth.PALETTE["flame_shine"], spark_alpha), (spx, spy, 1, 1))
        # IMPACT BURST.
        if 0.55 < progress < 0.72:
            impact_t = (progress - 0.55) / 0.17
            impact_alpha = _NS_kaineroth._alpha(240 * (1 - impact_t))
            if impact_alpha > 0:
                impact_wx = cx_sh + int(math.cos(math.pi * 0.2) * (arc_length + 8)) * facing
                impact_wy = cy_sh + int(math.sin(math.pi * 0.2) * (arc_length + 8))
                ifx, ify = to_fx(impact_wx, impact_wy)
                for burst_r in range(int(6 + impact_t * 18), 0, -2):
                    a = _NS_kaineroth._alpha(impact_alpha * (20 - burst_r) / 20)
                    if a > 0:
                        pygame.draw.circle(fx_surf, (*_NS_kaineroth.PALETTE["flame_light"], a), (ifx, ify), burst_r)
                for i in range(10):
                    a_burst = i * math.pi / 5
                    bx = ifx + int(math.cos(a_burst) * (8 + impact_t * 14))
                    by = ify + int(math.sin(a_burst) * (8 + impact_t * 14))
                    pygame.draw.line(fx_surf, (*_NS_kaineroth.PALETTE["flame_mid"], impact_alpha), (ifx, ify), (bx, by), 2)
                    pygame.draw.rect(fx_surf, (*_NS_kaineroth.PALETTE["flame_hot"], impact_alpha), (bx, by, 1, 1))
        surface.blit(fx_surf, (cx_sh - ox, cy_sh - oy))
    # ================= AMBIENT / GROUND =================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((150, 32), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 16 - radius, 130 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (10, 3, 8, 180), (5, 9, 140, 14))
        pygame.draw.ellipse(shadow, (60, 15, 25, 130), (12, 11, 126, 10))
        surface.blit(shadow, (x - 75, y - 16))
    def _draw_shadow_aura(surface, x, y, phase):
        """Dark red aura + purple void."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_kaineroth._alpha((95 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_kaineroth._aacircle(aura, (*_NS_kaineroth.PALETTE["cloak_darkest"], alpha), (120, 100), radius)
        for radius in range(60, 5, -3):
            alpha = _NS_kaineroth._alpha((60 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_kaineroth._aacircle(aura, (*_NS_kaineroth.PALETTE["cloud_dark"], alpha), (120, 100), radius)
        for radius in range(30, 5, -2):
            alpha = _NS_kaineroth._alpha((30 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_kaineroth._aacircle(aura, (*_NS_kaineroth.PALETTE["eye_dark"], alpha), (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))
        # Red floating embers.
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            sy -= int((phase * 6 + i * 5) % 22)
            color = _NS_kaineroth.PALETTE["flame_dark"] if i % 2 == 0 else _NS_kaineroth.PALETTE["cloud_mid"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kaineroth.PALETTE["flame_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 56), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_kaineroth.PALETTE["cloak_darkest"], 200), (5, 18, 170, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_kaineroth.PALETTE["cloud_dark"], 220), (14, 20, 152, 24), 2)
        pygame.draw.ellipse(ring, (*_NS_kaineroth.PALETTE["cloud_mid"], 180), (25, 22, 130, 20), 1)
        # Sharingan-like tomoe markers (3).
        for i in range(3):
            angle = phase * 0.5 + i * math.pi * 2 / 3
            x1 = 90 + int(math.cos(angle) * 68)
            y1 = 32 + int(math.sin(angle) * 12)
            _NS_kaineroth._aacircle(ring, _NS_kaineroth.PALETTE["eye_mid"], (x1, y1), 2)
            pygame.draw.rect(ring, _NS_kaineroth.PALETTE["eye_light"], (x1, y1, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_kaineroth.PALETTE["eye_light"], _NS_kaineroth._alpha(150 * pulse)),
                                (15, 12, 150, 40), 1)
        surface.blit(ring, (x - 90, y - 28))
    def _draw_shadow_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Dark red wisps rising below body."""
        strength = 1.5 if intense else 1.0
        # Wisp mist.
        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(32, 3, -3):
            alpha = _NS_kaineroth._alpha((32 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist, (*_NS_kaineroth.PALETTE["cloak_darkest"], alpha),
                                    (75 - radius * 2, 25 - radius // 3, radius * 4, max(3, radius // 2)))
        for radius in range(20, 3, -2):
            alpha = _NS_kaineroth._alpha((20 - radius) * 3.0 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(mist, (*_NS_kaineroth.PALETTE["cloud_dark"], alpha),
                                    (75 - radius, 25 - radius // 4, radius * 2, max(2, radius // 3)))
        surface.blit(mist, (cx - 75, cy - 10))
        # Rising red embers.
        for i, offset in enumerate((-24, -14, -4, 6, 16, 26)):
            t = (phase * 0.5 + i * 0.15) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 22)
            alpha = _NS_kaineroth._alpha(200 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["cloud_dark"], alpha), (sx, sy), 3)
            _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["cloud_mid"], alpha), (sx, sy - 1), 2)
            pygame.draw.rect(surface, (*_NS_kaineroth.PALETTE["flame_hot"], alpha), (sx, sy - 1, 1, 1))
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_kaineroth._alpha(160 - i * 30)
                if alpha <= 0:
                    continue
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["cloak_dark"], alpha),
                                        (sx, sy), max(2, 6 - i))
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["cloud_dark"], alpha),
                                        (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_kaineroth.PALETTE["flame_hot"], alpha),
                                 (sx, sy - 1, 2, 1))
    def _draw_ambient_crows(surface, x, y, phase):
        """Flying crow silhouettes in background."""
        for i in range(3):
            t = (phase * 0.4 + i * 0.35) % 1.0
            cx = x - 90 + int(t * 180)
            cy = y - 80 + int(math.sin(phase + i * 2) * 20)
            _NS_kaineroth._draw_crow(surface, cx, cy, phase + i, small=True)
    def _draw_crow(surface, cx, cy, phase, small=False):
        """Small crow silhouette with flapping wings."""
        flap = math.sin(phase * 4) * 3
        size = 3 if small else 5
        # Body.
        _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["crow_dark"], (cx, cy), size)
        _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["crow_mid"], (cx - 1, cy - 1), max(1, size - 1))
        # Wings (angled).
        wing_len = size + 3
        # Left wing.
        wl_end_x = cx - wing_len
        wl_end_y = cy - int(flap)
        pygame.draw.line(surface, _NS_kaineroth.PALETTE["crow_dark"],
                         (cx, cy), (wl_end_x, wl_end_y), 2)
        pygame.draw.line(surface, _NS_kaineroth.PALETTE["crow_mid"],
                         (cx, cy), (wl_end_x, wl_end_y), 1)
        # Right wing.
        wr_end_x = cx + wing_len
        wr_end_y = cy - int(flap)
        pygame.draw.line(surface, _NS_kaineroth.PALETTE["crow_dark"],
                         (cx, cy), (wr_end_x, wr_end_y), 2)
        pygame.draw.line(surface, _NS_kaineroth.PALETTE["crow_mid"],
                         (cx, cy), (wr_end_x, wr_end_y), 1)
        # Small red eye.
        pygame.draw.rect(surface, _NS_kaineroth.PALETTE["eye_light"], (cx, cy - 1, 1, 1))
    # ================= SKILL Q — BLACKFLAME CURSE =================
    def _draw_blackflame_ground(surface, boss, x, y, timer, phase):
        """Burning black flame patch at target."""
        tx, ty = _NS_kaineroth._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # After projectile lands, black flame burns on ground.
        if progress > 0.35:
            burn_t = (progress - 0.35) / 0.65
            r = int(35 * min(1.0, burn_t * 3))
            if r > 3:
                pygame.draw.ellipse(surface, (*_NS_kaineroth.PALETTE["shadow_deep"], 220),
                                    (tx - r, ty - r // 3, r * 2, r * 2 // 3))
                pygame.draw.ellipse(surface, (*_NS_kaineroth.PALETTE["black_flame_dark"], 200),
                                    (tx - r + 2, ty - r // 3 + 1, r * 2 - 4, r * 2 // 3 - 2))
                pygame.draw.ellipse(surface, (*_NS_kaineroth.PALETTE["black_flame_mid"], 180),
                                    (tx - r + 5, ty - r // 3 + 3, r * 2 - 10, r * 2 // 3 - 6))
    def _draw_blackflame_projectile(surface, boss, x, y, timer, phase):
        """Black flame projectile shooting to target with rising black flames."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kaineroth._target_position(boss, x, y)
        if progress < 0.2:
            # Charge in hand.
            t = progress / 0.2
            hand_x = x + facing * 28
            hand_y = y - 8
            cr = int(3 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_kaineroth._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["black_flame_dark"], alpha),
                                        (hand_x, hand_y), r)
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["black_flame_mid"], (hand_x, hand_y), cr - 2)
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["black_flame_edge"], (hand_x, hand_y), max(1, cr - 4))
        elif progress < 0.4:
            # Projectile flight.
            t = (progress - 0.2) / 0.2
            start_x = x + facing * 32
            start_y = y - 8
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Comet trail (black flame).
            for i in range(9):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_kaineroth._alpha(240 - i * 25)
                size = max(1, 8 - i)
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["shadow_deep"], alpha), (px, py), size)
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["black_flame_dark"], alpha), (px, py), max(1, size - 1))
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["black_flame_mid"], alpha), (px, py), max(1, size - 2))
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["black_flame_edge"], alpha), (px, py), max(1, size - 4))
            # Head.
            for r in range(12, 0, -1):
                alpha = _NS_kaineroth._alpha(100 * (12 - r) / 12)
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["black_flame_edge"], alpha), (bx, by), r)
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["shadow_deep"], (bx, by), 8)
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["black_flame_dark"], (bx, by), 6)
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["black_flame_hot"], (bx, by), 3)
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["black_flame_edge"], (bx, by), 1)
        else:
            # Black flames rising from target.
            burn_t = (progress - 0.4) / 0.6
            r = int(35 * min(1.0, burn_t * 3))
            # Rising black flame columns.
            for i in range(8):
                col_angle = i * math.pi * 2 / 8 + phase * 0.2
                col_dist = int(r * 0.5)
                col_x = tx + int(math.cos(col_angle) * col_dist)
                col_y_base = ty + int(math.sin(col_angle) * col_dist * 0.4)
                for layer in range(6):
                    layer_t = (phase * 0.5 + i * 0.2 + layer * 0.15) % 1.0
                    layer_y = col_y_base - int(layer_t * 26)
                    layer_alpha = _NS_kaineroth._alpha(200 * (1 - layer_t))
                    layer_w = int(4 + layer_t * 3)
                    _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["shadow_deep"], layer_alpha),
                                            (col_x, layer_y), layer_w + 1)
                    _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["black_flame_dark"], layer_alpha),
                                            (col_x, layer_y), layer_w)
                    _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["black_flame_mid"], layer_alpha),
                                            (col_x, layer_y - 1), max(1, layer_w - 1))
                    pygame.draw.rect(surface, (*_NS_kaineroth.PALETTE["black_flame_edge"], layer_alpha),
                                     (col_x, layer_y - 1, 1, 1))
    # ================= SKILL W — CRIMSON EYE (buff self) =================
    def _draw_sharingan_activation(surface, boss, x, y, timer, phase):
        """Big red Sharingan eye above the boss."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        intensity = math.sin(progress * math.pi)
        # Aura around body.
        for r in range(45, 0, -3):
            alpha = _NS_kaineroth._alpha(120 * (45 - r) / 45 * intensity)
            _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["eye_mid"], alpha), (x, y), r, 1)
        # Big Sharingan eye above head.
        eye_x = x
        eye_y = y - 60
        eye_r = int(18 + intensity * 4)
        FX_W = 80
        eye_surf = pygame.Surface((FX_W, FX_W), pygame.SRCALPHA)
        ec = (FX_W // 2, FX_W // 2)
        # Outer socket.
        for r in range(eye_r + 8, 0, -1):
            alpha = _NS_kaineroth._alpha(100 * (eye_r + 8 - r) / (eye_r + 8) * intensity)
            _NS_kaineroth._aacircle(eye_surf, (*_NS_kaineroth.PALETTE["eye_dark"], alpha), ec, r)
        # White scleral base.
        _NS_kaineroth._aacircle(eye_surf, (*_NS_kaineroth.PALETTE["white"], _NS_kaineroth._alpha(240 * intensity)),
                                ec, eye_r)
        # Red iris.
        _NS_kaineroth._aacircle(eye_surf, (*_NS_kaineroth.PALETTE["eye_mid"], _NS_kaineroth._alpha(255 * intensity)),
                                ec, eye_r - 2)
        _NS_kaineroth._aacircle(eye_surf, (*_NS_kaineroth.PALETTE["eye_dark"], _NS_kaineroth._alpha(255 * intensity)),
                                ec, eye_r - 4)
        _NS_kaineroth._aacircle(eye_surf, (*_NS_kaineroth.PALETTE["eye_mid"], _NS_kaineroth._alpha(255 * intensity)),
                                ec, eye_r - 6)
        # Pupil (black center).
        _NS_kaineroth._aacircle(eye_surf, (*_NS_kaineroth.PALETTE["black"], _NS_kaineroth._alpha(255 * intensity)),
                                ec, 3)
        # 3 tomoe rotating around pupil.
        tomoe_r = eye_r - 5
        rotation = phase * 2
        for i in range(3):
            angle = rotation + i * math.pi * 2 / 3
            tx_p = ec[0] + int(math.cos(angle) * tomoe_r)
            ty_p = ec[1] + int(math.sin(angle) * tomoe_r)
            # Tomoe = teardrop/comma shape.
            _NS_kaineroth._aacircle(eye_surf, (*_NS_kaineroth.PALETTE["black"], _NS_kaineroth._alpha(255 * intensity)),
                                    (tx_p, ty_p), 3)
            # Tail of comma.
            tail_angle = angle + math.pi / 2
            tt_x = tx_p + int(math.cos(tail_angle) * 3)
            tt_y = ty_p + int(math.sin(tail_angle) * 3)
            pygame.draw.line(eye_surf, (*_NS_kaineroth.PALETTE["black"], _NS_kaineroth._alpha(255 * intensity)),
                             (tx_p, ty_p), (tt_x, tt_y), 2)
        surface.blit(eye_surf, (eye_x - FX_W // 2, eye_y - FX_W // 2))
    # ================= SKILL E — GRAND FIREBALL =================
    def _draw_fireball_ground(surface, boss, x, y, timer, phase):
        """Burning ground on impact."""
        tx, ty = _NS_kaineroth._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.5:
            burn_t = (progress - 0.5) / 0.5
            r = int(50 * min(1.0, burn_t * 3))
            if r > 3:
                pygame.draw.ellipse(surface, (*_NS_kaineroth.PALETTE["flame_darkest"], 220),
                                    (tx - r, ty - r // 3, r * 2, r * 2 // 3))
                pygame.draw.ellipse(surface, (*_NS_kaineroth.PALETTE["flame_dark"], 200),
                                    (tx - r + 3, ty - r // 3 + 2, r * 2 - 6, r * 2 // 3 - 4))
    def _draw_grand_fireball(surface, boss, x, y, timer, phase):
        """Massive fireball projectile."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kaineroth._target_position(boss, x, y)
        if progress < 0.3:
            # Massive charge.
            t = progress / 0.3
            hand_x = x + facing * 28
            hand_y = y - 6
            cr = int(6 + t * 16)
            for r in range(cr + 8, 0, -1):
                alpha = _NS_kaineroth._alpha(200 * (cr + 8 - r) / (cr + 8))
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["flame_dark"], alpha),
                                        (hand_x, hand_y), r)
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["flame_darkest"], (hand_x, hand_y), cr)
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["flame_mid"], (hand_x, hand_y), cr - 3)
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["flame_hot"], (hand_x, hand_y), max(1, cr - 6))
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["flame_shine"], (hand_x, hand_y), max(1, cr - 9))
            # Sparks.
            for i in range(10):
                angle = phase * 4 + i * math.pi / 5
                sx = hand_x + int(math.cos(angle) * (cr + 4))
                sy = hand_y + int(math.sin(angle) * (cr + 4))
                pygame.draw.rect(surface, _NS_kaineroth.PALETTE["flame_hot"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_kaineroth.PALETTE["flame_shine"], (sx, sy, 1, 1))
        else:
            # HUGE fireball flying.
            t = (progress - 0.3) / 0.7
            start_x = x + facing * 36
            start_y = y - 6
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Massive comet trail.
            for i in range(14):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_kaineroth._alpha(240 - i * 18)
                size = max(1, 14 - i)
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["flame_darkest"], alpha), (px, py), size)
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["flame_dark"], alpha), (px, py), max(1, size - 1))
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["flame_mid"], alpha), (px, py), max(1, size - 3))
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["flame_light"], alpha), (px, py), max(1, size - 5))
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["flame_hot"], alpha), (px, py), max(1, size - 7))
                if i < 6:
                    for s in range(3):
                        spark_x = px + int(math.sin(t * 8 + i + s) * (size + 2))
                        spark_y = py + int(math.cos(t * 8 + i + s) * (size + 2))
                        pygame.draw.rect(surface, (*_NS_kaineroth.PALETTE["flame_shine"], alpha), (spark_x, spark_y, 1, 1))
            # Head — very bright.
            for r in range(20, 0, -2):
                alpha = _NS_kaineroth._alpha(120 * (20 - r) / 20)
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["flame_light"], alpha), (bx, by), r)
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["flame_darkest"], (bx, by), 14)
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["flame_dark"], (bx, by), 11)
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["flame_mid"], (bx, by), 8)
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["flame_light"], (bx, by), 5)
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["flame_hot"], (bx, by), 3)
            _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["flame_shine"], (bx, by), 1)
            # Explosion at impact.
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(20 + st * 40)
                alpha = _NS_kaineroth._alpha(240 * (1 - st))
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["flame_darkest"], alpha), (tx, ty), radius + 4, 3)
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["flame_dark"], alpha), (tx, ty), radius, 3)
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["flame_mid"], alpha), (tx, ty), max(1, radius - 6), 2)
                _NS_kaineroth._aacircle(surface, (*_NS_kaineroth.PALETTE["flame_light"], alpha), (tx, ty), max(1, radius - 14), 1)
                # Radial rays.
                for i in range(14):
                    angle_s = i * math.pi / 7
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.line(surface, (*_NS_kaineroth.PALETTE["flame_hot"], alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface, (*_NS_kaineroth.PALETTE["flame_shine"], alpha), (ex, ey, 2, 2))
    # ================= SKILL R — MIND PRISON =================
    def _draw_prison_ground(surface, boss, x, y, timer, phase):
        """Dome base at target."""
        tx, ty = _NS_kaineroth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(75 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_kaineroth.PALETTE["cloak_darkest"], 220),
                                (tx - r, ty - r // 4, r * 2, r * 2 // 4))
            pygame.draw.ellipse(surface, (*_NS_kaineroth.PALETTE["cloud_dark"], 200),
                                (tx - r + 4, ty - r // 4 + 2, r * 2 - 8, r * 2 // 4 - 4), 2)
            # Rotating tomoe symbols.
            for i in range(3):
                ang = phase * 0.4 + i * math.pi * 2 / 3
                px = tx + int(math.cos(ang) * (r - 8))
                py = ty + int(math.sin(ang) * (r - 8) * 0.4)
                _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["eye_dark"], (px, py), 3)
                _NS_kaineroth._aacircle(surface, _NS_kaineroth.PALETTE["eye_light"], (px, py), 2)
    def _draw_mind_prison_dome(surface, boss, x, y, timer, phase):
        """Red illusion dome trapping target."""
        tx, ty = _NS_kaineroth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(70 * min(1.0, progress * 3))
        if r < 5:
            return
        # Semi-transparent red dome.
        dome = pygame.Surface((r * 2 + 20, r + 20), pygame.SRCALPHA)
        # Red gradient inner fill.
        for r_i in range(r, 0, -3):
            alpha = _NS_kaineroth._alpha(120 * (r - r_i) / r)
            pygame.draw.ellipse(dome, (*_NS_kaineroth.PALETTE["eye_dark"], alpha),
                                (10 + r - r_i, 10 + r - r_i, r_i * 2, r_i * 2))
        # Layered dome rings.
        for i, (thickness, alpha_val) in enumerate([(3, 140), (2, 180), (1, 240)]):
            pygame.draw.ellipse(dome, (*_NS_kaineroth.PALETTE["eye_mid"], alpha_val),
                                (10 + i, 10 + i, r * 2 - i * 2, r * 2 - i * 2), thickness)
            pygame.draw.ellipse(dome, (*_NS_kaineroth.PALETTE["eye_light"], alpha_val),
                                (10 + i + 1, 10 + i + 1, r * 2 - i * 2 - 2, r * 2 - i * 2 - 2), 1)
        # Vertical bars (illusion cage).
        for i in range(12):
            bar_x = 10 + i * (r * 2 // 12) + r // 12
            alpha = _NS_kaineroth._alpha(140)
            pygame.draw.line(dome, (*_NS_kaineroth.PALETTE["eye_hot"], alpha),
                             (bar_x, r + 10), (bar_x, 15), 1)
        # Big Sharingan symbol on top of dome.
        symbol_x = r + 10
        symbol_y = 25
        _NS_kaineroth._aacircle(dome, (*_NS_kaineroth.PALETTE["black"], 240), (symbol_x, symbol_y), 12)
        _NS_kaineroth._aacircle(dome, (*_NS_kaineroth.PALETTE["eye_mid"], 240), (symbol_x, symbol_y), 10)
        _NS_kaineroth._aacircle(dome, (*_NS_kaineroth.PALETTE["eye_dark"], 240), (symbol_x, symbol_y), 8)
        _NS_kaineroth._aacircle(dome, (*_NS_kaineroth.PALETTE["black"], 240), (symbol_x, symbol_y), 3)
        # 3 tomoe.
        for i in range(3):
            ang = phase * 2 + i * math.pi * 2 / 3
            tx_t = symbol_x + int(math.cos(ang) * 7)
            ty_t = symbol_y + int(math.sin(ang) * 7)
            _NS_kaineroth._aacircle(dome, (*_NS_kaineroth.PALETTE["black"], 240), (tx_t, ty_t), 2)
        # Crows flying inside dome.
        for i in range(4):
            crow_ang = phase * 1.5 + i * math.pi / 2
            crow_r_orbit = r * 0.5
            cx_c = symbol_x + int(math.cos(crow_ang) * crow_r_orbit)
            cy_c = 10 + r - int(abs(math.sin(crow_ang)) * r * 0.7)
            if cy_c > r + 10:
                continue
            _NS_kaineroth._draw_crow(dome, cx_c, cy_c, phase * 2 + i, small=True)
        surface.blit(dome, (tx - r - 10, ty - r - 10))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_kaedrin(surface, boss, x, y):
    """Entry point kaedrin."""
    return _NS_kaedrin.draw_kaedrin(surface, boss, x, y)


def draw_morvaeth(surface, boss, x, y):
    """Entry point morvaeth."""
    return _NS_morvaeth.draw_morvaeth(surface, boss, x, y)


def draw_morvaeth2(surface, boss, x, y):
    """Entry point morvaeth2 (The Mirrorborn, mini boss level 42).

    FIX: dipakai sebagai renderer morvaeth2 yang sebelumnya tidak
    terindeks di _boss_index.py (215/216) sehingga boss muncul
    sebagai body generic.
    """
    return _NS_morvaeth.draw_morvaeth(surface, boss, x, y)


def draw_vardrok(surface, boss, x, y):
    """Entry point vardrok."""
    return _NS_vardrok.draw_vardrok(surface, boss, x, y)


def draw_kaineroth(surface, boss, x, y):
    """Entry point kaineroth."""
    return _NS_kaineroth.draw_kaineroth(surface, boss, x, y)
