"""
bosses/level1.py - Semua boss Level 1

Gabungan dari 4 file terpisah:
  - gornak               (mini boss)
  - morgath              (mini boss)
  - drakar               (mini boss)
  - abaddon              (TRUE BOSS)

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
# GORNAK (ANTI-MAGE) - Mini Boss
# ====================================================================
import math
import pygame


class _NS_gornak:
    """Namespace gornak - Anti-Mage mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin (tanned brown)
        "skin_darkest": (45, 25, 15),
        "skin_dark": (95, 55, 30),
        "skin_mid": (155, 95, 55),
        "skin_light": (200, 140, 90),
        "skin_shine": (235, 180, 130),

        # Mohawk / hair (purple magic)
        "hair_dark": (40, 15, 60),
        "hair_mid": (95, 40, 140),
        "hair_light": (170, 100, 220),
        "hair_shine": (220, 170, 255),

        # Robe / cloth (dark purple)
        "robe_darkest": (15, 8, 25),
        "robe_dark": (35, 20, 55),
        "robe_mid": (65, 40, 95),
        "robe_light": (110, 75, 150),
        "robe_edge": (160, 120, 200),

        # Armor / metal (dark iron with purple tint)
        "armor_darkest": (10, 8, 15),
        "armor_dark": (30, 25, 40),
        "armor_mid": (65, 55, 80),
        "armor_light": (115, 100, 135),
        "armor_shine": (180, 165, 200),

        # Blade / metal (silver-purple)
        "blade_dark": (40, 35, 55),
        "blade_mid": (110, 100, 135),
        "blade_light": (190, 180, 210),
        "blade_shine": (240, 230, 255),

        # Magic aura (bright violet - main FX color)
        "magic_darkest": (25, 5, 45),
        "magic_dark": (60, 20, 110),
        "magic_mid": (130, 55, 200),
        "magic_light": (185, 110, 240),
        "magic_hot": (220, 160, 255),
        "magic_shine": (245, 210, 255),

        # Eye glow (bright magenta-white)
        "eye_dark": (60, 20, 80),
        "eye_mid": (180, 90, 220),
        "eye_light": (240, 180, 255),
        "eye_glow": (255, 230, 255),

        # Ground / rune
        "rune_dark": (20, 10, 40),
        "rune_mid": (90, 40, 160),
        "rune_light": (180, 120, 240),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 5),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_gornak._clamp(color)
        if _NS_gornak.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_gornak._clamp(color)
        if _NS_gornak.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_gornak._clamp(color), points)

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

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_gornak(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_gornak._detect_moving(boss)
        _NS_gornak._update_gnk_attack_anim(boss)
        attacking = (
            getattr(boss, "_gnk_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind
        _NS_gornak._draw_magic_aura(surface, x, y, pulse)
        _NS_gornak._draw_ground_rune(surface, x, y + 42, pulse, active_skill)

        # Skill ground FX (behind body)
        if active_skill == "q":
            _NS_gornak._draw_manabreak_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_gornak._draw_blink_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_gornak._draw_counterspell_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_gornak._draw_manavoid_ground(surface, boss, x, y, skill_timer, pulse)

        # Body
        if active_skill == "w":
            _NS_gornak._draw_gnk_blink(surface, boss, x, y, skill_timer)
        elif attacking:
            _NS_gornak._draw_gnk_attack(surface, boss, x, y)
        elif moving:
            _NS_gornak._draw_gnk_walk(surface, boss, x, y)
        else:
            _NS_gornak._draw_gnk_idle(surface, boss, x, y)

        # Foreground FX
        if active_skill == "q":
            _NS_gornak._draw_manabreak_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_gornak._draw_counterspell_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_gornak._draw_manavoid_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_gnk_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_gnk_previous_timer", 0))
        active = bool(getattr(boss, "_gnk_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._gnk_attack_active = True
            boss._gnk_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._gnk_attack_frame = int(getattr(boss, "_gnk_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._gnk_attack_active = False
            boss._gnk_attack_frame = 0
            active = False

        boss._gnk_previous_timer = timer
        boss._gnk_attack_progress = (
            min(1.0, getattr(boss, "_gnk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_gnk_last_x"):
            boss._gnk_last_x = boss.x
            boss._gnk_last_y = boss.y
            return False
        dx = abs(boss.x - boss._gnk_last_x)
        dy = abs(boss.y - boss._gnk_last_y)
        boss._gnk_last_x = boss.x
        boss._gnk_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_gnk_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 2)
        _NS_gornak._draw_shadow(surface, x, y + 46)
        _NS_gornak._draw_gnk_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")

    def _draw_gnk_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase * 0.8) * 2)
        _NS_gornak._draw_shadow(surface, x + sway, y + 46)
        _NS_gornak._draw_gnk_body(surface, x + sway, y - bob + 2, boss.direction, phase, "walk")

    def _draw_gnk_attack(surface, boss, x, y):
        progress = getattr(boss, "_gnk_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))

        # Wind-up (raise blade) → swing forward → recovery
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 2)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-3 + t * 12)) * boss.direction
            lift = int(2 - t * 3)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(9 * (1 - t)) * boss.direction
            lift = int(-1 + t)

        _NS_gornak._draw_shadow(surface, x + lunge, y + 46)
        _NS_gornak._draw_gnk_body(surface, x + lunge, y - lift, boss.direction,
                                   boss.pulse, "attack", progress)
        # Crescent slash arc
        _NS_gornak._draw_crescent_slash(surface, boss, x + lunge, y - lift, progress)

    def _draw_gnk_blink(surface, boss, x, y, timer):
        """Blink animation - fading in/out with afterimage."""
        duration = 30
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_gornak._draw_shadow(surface, x, y + 46)

        # Fade phase: alpha modulates
        if progress < 0.3:
            # Fading out
            alpha_t = 1.0 - progress / 0.3
        elif progress < 0.7:
            # Invisible / traveling
            alpha_t = 0.15
        else:
            # Fading back in
            alpha_t = (progress - 0.7) / 0.3

        # Draw body with alpha
        body_surf = pygame.Surface((100, 100), pygame.SRCALPHA)
        _NS_gornak._draw_gnk_body(body_surf, 50, 50, boss.direction, boss.pulse, "idle")
        body_surf.set_alpha(int(255 * alpha_t))
        surface.blit(body_surf, (x - 50, y - 50))

    # ============================================================
    # BODY (Humanoid: legs, torso, arms with blades, head with mohawk)
    # ============================================================
    def _draw_gnk_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw humanoid warrior with twin blades."""
        # Legs first (back)
        _NS_gornak._draw_gnk_legs(surface, cx, cy + 12, facing, phase, action)

        # Robe / lower body
        _NS_gornak._draw_gnk_robe(surface, cx, cy + 4, facing, phase)

        # Torso / armor
        _NS_gornak._draw_gnk_torso(surface, cx, cy - 6, facing, phase)

        # Back arm (holding blade behind)
        _NS_gornak._draw_gnk_arm_back(surface, cx, cy - 4, facing, phase, action, attack_progress)

        # Head
        _NS_gornak._draw_gnk_head(surface, cx, cy - 18, facing, phase, action)

        # Front arm (main blade)
        _NS_gornak._draw_gnk_arm_front(surface, cx, cy - 4, facing, phase, action, attack_progress)

    def _draw_gnk_legs(surface, cx, cy, facing, phase, action):
        """Two legs with armored boots."""
        # Leg positions
        if action == "walk":
            stride = math.sin(phase * 2) * 3
            back_lift = max(0, -math.sin(phase * 2)) * 2
            front_lift = max(0, math.sin(phase * 2)) * 2
        else:
            stride = 0
            back_lift = 0
            front_lift = 0

        # Back leg
        bx = cx - 4
        by = cy - int(back_lift)
        _NS_gornak._draw_leg(surface, bx + int(stride), by, facing, back=True)

        # Front leg
        fx = cx + 4
        fy = cy - int(front_lift)
        _NS_gornak._draw_leg(surface, fx - int(stride), fy, facing, back=False)

    def _draw_leg(surface, cx, cy, facing, back=False):
        """Single armored leg with boot."""
        shade_offset = 1 if back else 0
        # Thigh (dark robe/pants)
        pygame.draw.rect(surface, _NS_gornak.PALETTE["shadow_deep"],
                         (cx - 3, cy - 6, 7, 9))
        pygame.draw.rect(surface, _NS_gornak.PALETTE["robe_darkest"],
                         (cx - 3, cy - 6, 6, 8))
        pygame.draw.rect(surface, _NS_gornak.PALETTE["robe_dark"],
                         (cx - 2, cy - 6, 4, 7))
        if not back:
            pygame.draw.rect(surface, _NS_gornak.PALETTE["robe_mid"],
                             (cx - 1, cy - 5, 2, 5))

        # Boot (armored)
        pygame.draw.rect(surface, _NS_gornak.PALETTE["shadow_deep"],
                         (cx - 4, cy + 2, 9, 5))
        pygame.draw.rect(surface, _NS_gornak.PALETTE["armor_darkest"],
                         (cx - 4, cy + 2, 8, 4))
        pygame.draw.rect(surface, _NS_gornak.PALETTE["armor_dark"],
                         (cx - 3, cy + 2, 6, 3))
        if not back:
            pygame.draw.rect(surface, _NS_gornak.PALETTE["armor_mid"],
                             (cx - 3, cy + 2, 5, 1))
            pygame.draw.rect(surface, _NS_gornak.PALETTE["armor_light"],
                             (cx - 2, cy + 2, 3, 1))

        # Knee guard
        pygame.draw.rect(surface, _NS_gornak.PALETTE["armor_dark"],
                         (cx - 2, cy - 1, 4, 2))
        pygame.draw.rect(surface, _NS_gornak.PALETTE["armor_mid"],
                         (cx - 2, cy - 1, 3, 1))

    def _draw_gnk_robe(surface, cx, cy, facing, phase):
        """Robe skirt with runic emblem."""
        sway = math.sin(phase * 0.6) * 1

        # Robe shape (trapezoid)
        robe_pts = [
            (cx - 8, cy - 4),
            (cx + 8, cy - 4),
            (cx + 11, cy + 8),
            (cx + 4 + int(sway), cy + 12),
            (cx - 4 + int(sway), cy + 12),
            (cx - 11, cy + 8),
        ]
        _NS_gornak._poly(surface, _NS_gornak.PALETTE["shadow_deep"],
                         [(px + 1, py + 1) for px, py in robe_pts])
        _NS_gornak._poly(surface, _NS_gornak.PALETTE["robe_darkest"], robe_pts)

        # Mid tone
        _NS_gornak._poly(surface, _NS_gornak.PALETTE["robe_dark"], [
            (cx - 7, cy - 3),
            (cx + 7, cy - 3),
            (cx + 10, cy + 7),
            (cx + 3 + int(sway), cy + 11),
            (cx - 3 + int(sway), cy + 11),
            (cx - 10, cy + 7),
        ])

        # Highlight (left side, catching light)
        _NS_gornak._poly(surface, _NS_gornak.PALETTE["robe_mid"], [
            (cx - 5, cy - 2),
            (cx + 2, cy - 2),
            (cx + 4, cy + 6),
            (cx - 3, cy + 8),
            (cx - 7, cy + 5),
        ])

        # Fold lines
        pygame.draw.line(surface, _NS_gornak.PALETTE["robe_darkest"],
                         (cx - 4, cy - 2), (cx - 6, cy + 10), 1)
        pygame.draw.line(surface, _NS_gornak.PALETTE["robe_darkest"],
                         (cx + 2, cy - 2), (cx + 5, cy + 10), 1)

        # Belt
        pygame.draw.rect(surface, _NS_gornak.PALETTE["armor_darkest"],
                         (cx - 9, cy - 4, 18, 3))
        pygame.draw.rect(surface, _NS_gornak.PALETTE["armor_dark"],
                         (cx - 9, cy - 4, 18, 2))
        pygame.draw.rect(surface, _NS_gornak.PALETTE["armor_mid"],
                         (cx - 8, cy - 3, 16, 1))
        # Belt buckle (magic gem)
        pygame.draw.rect(surface, _NS_gornak.PALETTE["magic_dark"],
                         (cx - 2, cy - 4, 4, 3))
        pygame.draw.rect(surface, _NS_gornak.PALETTE["magic_mid"],
                         (cx - 1, cy - 3, 2, 1))
        pygame.draw.rect(surface, _NS_gornak.PALETTE["magic_hot"],
                         (cx, cy - 3, 1, 1))

        # Emblem on robe (crescent moon rune)
        emblem_pulse = math.sin(phase * 2) * 0.4 + 0.6
        alpha_em = _NS_gornak._alpha(220 * emblem_pulse)
        pygame.draw.rect(surface, _NS_gornak.PALETTE["magic_darkest"],
                         (cx - 2, cy + 2, 4, 5))
        pygame.draw.rect(surface, _NS_gornak.PALETTE["magic_dark"],
                         (cx - 1, cy + 3, 3, 3))
        pygame.draw.rect(surface, _NS_gornak.PALETTE["magic_mid"],
                         (cx - 1, cy + 4, 2, 1))
        pygame.draw.rect(surface, _NS_gornak.PALETTE["magic_light"],
                         (cx, cy + 4, 1, 1))

    def _draw_gnk_torso(surface, cx, cy, facing, phase):
        """Chest with armor plate."""
        breath = math.sin(phase * 0.7) * 1

        # Torso shape
        torso_pts = [
            (cx - 7, cy - 4),
            (cx - 8, cy + 2),
            (cx - 6, cy + 8),
            (cx + 6, cy + 8),
            (cx + 8, cy + 2),
            (cx + 7, cy - 4),
            (cx + 4, cy - 6),
            (cx - 4, cy - 6),
        ]
        _NS_gornak._poly(surface, _NS_gornak.PALETTE["shadow_deep"],
                         [(px + 1, py + 1) for px, py in torso_pts])
        _NS_gornak._poly(surface, _NS_gornak.PALETTE["robe_darkest"], torso_pts)

        # Armor plate (chest)
        armor_pts = [
            (cx - 6, cy - 3 + int(breath)),
            (cx - 7, cy + 2),
            (cx - 5, cy + 7),
            (cx + 5, cy + 7),
            (cx + 7, cy + 2),
            (cx + 6, cy - 3 + int(breath)),
            (cx + 3, cy - 5 + int(breath)),
            (cx - 3, cy - 5 + int(breath)),
        ]
        _NS_gornak._poly(surface, _NS_gornak.PALETTE["armor_darkest"], armor_pts)
        _NS_gornak._poly(surface, _NS_gornak.PALETTE["armor_dark"], [
            (cx - 5, cy - 2 + int(breath)),
            (cx - 6, cy + 2),
            (cx - 4, cy + 6),
            (cx + 4, cy + 6),
            (cx + 6, cy + 2),
            (cx + 5, cy - 2 + int(breath)),
            (cx + 2, cy - 4 + int(breath)),
            (cx - 2, cy - 4 + int(breath)),
        ])
        _NS_gornak._poly(surface, _NS_gornak.PALETTE["armor_mid"], [
            (cx - 3, cy - 1 + int(breath)),
            (cx - 4, cy + 2),
            (cx - 2, cy + 5),
            (cx + 2, cy + 5),
            (cx + 4, cy + 2),
            (cx + 3, cy - 1 + int(breath)),
        ])

        # Chest highlight
        _NS_gornak._poly(surface, _NS_gornak.PALETTE["armor_light"], [
            (cx - 2, cy + int(breath)),
            (cx + 1, cy + int(breath)),
            (cx + 2, cy + 3),
            (cx, cy + 4),
            (cx - 2, cy + 3),
        ])

        # V-collar (robe over armor)
        pygame.draw.line(surface, _NS_gornak.PALETTE["robe_dark"],
                         (cx - 4, cy - 5), (cx, cy - 1), 2)
        pygame.draw.line(surface, _NS_gornak.PALETTE["robe_dark"],
                         (cx + 4, cy - 5), (cx, cy - 1), 2)
        pygame.draw.line(surface, _NS_gornak.PALETTE["robe_mid"],
                         (cx - 3, cy - 5), (cx, cy - 2), 1)

        # Shoulder pads
        for side in (-1, 1):
            sx = cx + side * 7
            pygame.draw.rect(surface, _NS_gornak.PALETTE["shadow_deep"],
                             (sx - 3, cy - 5, 6, 5))
            pygame.draw.rect(surface, _NS_gornak.PALETTE["armor_darkest"],
                             (sx - 3, cy - 5, 5, 4))
            pygame.draw.rect(surface, _NS_gornak.PALETTE["armor_dark"],
                             (sx - 2, cy - 5, 4, 3))
            pygame.draw.rect(surface, _NS_gornak.PALETTE["armor_mid"],
                             (sx - 2, cy - 5, 3, 1))
            # Shoulder gem
            pygame.draw.rect(surface, _NS_gornak.PALETTE["magic_dark"],
                             (sx - 1, cy - 4, 2, 2))
            pygame.draw.rect(surface, _NS_gornak.PALETTE["magic_mid"],
                             (sx, cy - 4, 1, 1))

    def _draw_gnk_arm_back(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm holding blade."""
        # Back arm is on far side
        base_x = cx - facing * 6
        base_y = cy

        # Arm swing based on action
        if action == "attack":
            if attack_progress < 0.35:
                # Wind up back
                arm_angle = -0.8
            elif attack_progress < 0.6:
                # Follow through
                t = (attack_progress - 0.35) / 0.25
                arm_angle = -0.8 + t * 1.0
            else:
                arm_angle = 0.2
        elif action == "walk":
            arm_angle = math.sin(phase * 2 + math.pi) * 0.3
        else:
            arm_angle = math.sin(phase * 0.6) * 0.1

        # Elbow position
        elbow_x = base_x - facing * int(4 + math.sin(arm_angle) * 2)
        elbow_y = base_y + int(4 - math.cos(arm_angle) * 2)

        # Hand position
        hand_x = elbow_x - facing * int(3 + math.sin(arm_angle + 0.5) * 2)
        hand_y = elbow_y + int(5 - math.cos(arm_angle + 0.5) * 3)

        # Upper arm
        _NS_gornak._aaline(surface, _NS_gornak.PALETTE["shadow_deep"],
                           (base_x + 1, base_y + 1), (elbow_x + 1, elbow_y + 1), 5)
        _NS_gornak._aaline(surface, _NS_gornak.PALETTE["robe_darkest"],
                           (base_x, base_y), (elbow_x, elbow_y), 4)
        _NS_gornak._aaline(surface, _NS_gornak.PALETTE["robe_dark"],
                           (base_x, base_y), (elbow_x, elbow_y), 3)

        # Forearm (skin visible - rolled sleeves)
        _NS_gornak._aaline(surface, _NS_gornak.PALETTE["shadow_deep"],
                           (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 4)
        _NS_gornak._aaline(surface, _NS_gornak.PALETTE["skin_darkest"],
                           (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_gornak._aaline(surface, _NS_gornak.PALETTE["skin_dark"],
                           (elbow_x, elbow_y), (hand_x, hand_y), 2)

        # Draw blade (behind, smaller/dimmer)
        _NS_gornak._draw_blade(surface, hand_x, hand_y, facing, phase, back=True,
                               action=action, attack_progress=attack_progress)

    def _draw_gnk_arm_front(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm - main blade."""
        base_x = cx + facing * 6
        base_y = cy

        # Arm swing based on action
        if action == "attack":
            if attack_progress < 0.35:
                # Wind up
                t = attack_progress / 0.35
                arm_angle = -0.4 - t * 0.8
            elif attack_progress < 0.6:
                # Swing forward
                t = (attack_progress - 0.35) / 0.25
                arm_angle = -1.2 + t * 2.4
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_angle = 1.2 - t * 1.0
        elif action == "walk":
            arm_angle = math.sin(phase * 2) * 0.3
        else:
            arm_angle = math.sin(phase * 0.6 + 0.5) * 0.15 - 0.1

        # Elbow
        elbow_x = base_x + facing * int(3 + math.cos(arm_angle) * 3)
        elbow_y = base_y + int(3 + math.sin(arm_angle) * 3)

        # Hand
        hand_x = elbow_x + facing * int(4 + math.cos(arm_angle + 0.3) * 3)
        hand_y = elbow_y + int(4 + math.sin(arm_angle + 0.3) * 4)

        # Upper arm
        _NS_gornak._aaline(surface, _NS_gornak.PALETTE["shadow_deep"],
                           (base_x + 1, base_y + 1), (elbow_x + 1, elbow_y + 1), 5)
        _NS_gornak._aaline(surface, _NS_gornak.PALETTE["robe_darkest"],
                           (base_x, base_y), (elbow_x, elbow_y), 4)
        _NS_gornak._aaline(surface, _NS_gornak.PALETTE["robe_dark"],
                           (base_x, base_y), (elbow_x, elbow_y), 3)
        _NS_gornak._aaline(surface, _NS_gornak.PALETTE["robe_mid"],
                           (base_x, base_y - 1), (elbow_x, elbow_y - 1), 1)

        # Forearm (bare skin)
        _NS_gornak._aaline(surface, _NS_gornak.PALETTE["shadow_deep"],
                           (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 4)
        _NS_gornak._aaline(surface, _NS_gornak.PALETTE["skin_darkest"],
                           (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_gornak._aaline(surface, _NS_gornak.PALETTE["skin_mid"],
                           (elbow_x, elbow_y), (hand_x, hand_y), 2)
        _NS_gornak._aaline(surface, _NS_gornak.PALETTE["skin_light"],
                           (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)

        # Wrist wrap (magic band)
        _NS_gornak._aacircle(surface, _NS_gornak.PALETTE["magic_dark"],
                             (hand_x, hand_y), 2)
        _NS_gornak._aacircle(surface, _NS_gornak.PALETTE["magic_mid"],
                             (hand_x - facing, hand_y), 1)

        # Main blade
        _NS_gornak._draw_blade(surface, hand_x, hand_y, facing, phase, back=False,
                               action=action, attack_progress=attack_progress)

    def _draw_blade(surface, cx, cy, facing, phase, back=False, action="idle",
                    attack_progress=0):
        """Curved crescent blade with magic aura."""
        # Blade orientation
        if action == "attack":
            if attack_progress < 0.35:
                blade_angle = -math.pi * 0.7
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                blade_angle = -math.pi * 0.7 + t * math.pi * 1.4
            else:
                blade_angle = math.pi * 0.7
        else:
            # Idle: blade pointing down-forward
            blade_angle = math.pi * 0.35 + math.sin(phase * 0.8) * 0.1

        # Blade sweeps from base to tip along curve
        blade_len = 14 if not back else 12
        alpha_mult = 1.0 if not back else 0.7

        # Compute crescent curve points
        curve_points = []
        for i in range(9):
            t = i / 8
            # Angle along curve
            a = blade_angle - t * 0.9 * facing
            # Distance grows and curves
            r = blade_len * t
            px = cx + int(math.cos(a) * r) * facing
            py = cy + int(math.sin(a) * r)
            curve_points.append((px, py))

        # Draw blade curved shape (crescent)
        if len(curve_points) >= 3:
            # Outer edge
            outer_pts = []
            inner_pts = []
            for i, (px, py) in enumerate(curve_points):
                thick = int(3 * math.sin((i / 8) * math.pi)) + 1
                # Perpendicular
                if i > 0:
                    prev = curve_points[i - 1]
                    dx = px - prev[0]
                    dy = py - prev[1]
                    perp_len = math.hypot(dx, dy)
                    if perp_len > 0:
                        perp_x = -dy / perp_len * thick
                        perp_y = dx / perp_len * thick
                    else:
                        perp_x = perp_y = 0
                else:
                    perp_x = perp_y = 0
                outer_pts.append((px + int(perp_x), py + int(perp_y)))
                inner_pts.append((px - int(perp_x), py - int(perp_y)))

            blade_shape = outer_pts + list(reversed(inner_pts))

            # Shadow
            shadow_shape = [(p[0] + 1, p[1] + 1) for p in blade_shape]
            _NS_gornak._poly(surface, _NS_gornak.PALETTE["shadow_deep"], shadow_shape)

            # Main blade
            _NS_gornak._poly(surface, _NS_gornak.PALETTE["blade_dark"], blade_shape)

            # Highlight strip along the edge
            mid_pts = []
            for i in range(len(curve_points)):
                mx = int((outer_pts[i][0] * 0.4 + inner_pts[i][0] * 0.6))
                my = int((outer_pts[i][1] * 0.4 + inner_pts[i][1] * 0.6))
                mid_pts.append((mx, my))

            if len(mid_pts) >= 2:
                for i in range(len(mid_pts) - 1):
                    _NS_gornak._aaline(surface, _NS_gornak.PALETTE["blade_mid"],
                                       mid_pts[i], mid_pts[i + 1], 2)
                    _NS_gornak._aaline(surface, _NS_gornak.PALETTE["blade_light"],
                                       mid_pts[i], mid_pts[i + 1], 1)

            # Glow along outer edge (magic infusion)
            aura_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
            offset_x = cx - 40
            offset_y = cy - 40
            for i in range(len(outer_pts) - 1):
                p1 = (outer_pts[i][0] - offset_x, outer_pts[i][1] - offset_y)
                p2 = (outer_pts[i + 1][0] - offset_x, outer_pts[i + 1][1] - offset_y)
                pygame.draw.line(aura_surf,
                                 (*_NS_gornak.PALETTE["magic_mid"], int(200 * alpha_mult)),
                                 p1, p2, 3)
                pygame.draw.line(aura_surf,
                                 (*_NS_gornak.PALETTE["magic_light"], int(240 * alpha_mult)),
                                 p1, p2, 2)
                pygame.draw.line(aura_surf,
                                 (*_NS_gornak.PALETTE["magic_hot"], int(255 * alpha_mult)),
                                 p1, p2, 1)
            surface.blit(aura_surf, (offset_x, offset_y))

            # Bright tip
            tip = curve_points[-1]
            _NS_gornak._aacircle(surface, _NS_gornak.PALETTE["magic_light"], tip, 2)
            _NS_gornak._aacircle(surface, _NS_gornak.PALETTE["magic_shine"], tip, 1)
            pygame.draw.rect(surface, _NS_gornak.PALETTE["white"], (tip[0], tip[1], 1, 1))

            # Handle at base
            base = curve_points[0]
            pygame.draw.rect(surface, _NS_gornak.PALETTE["armor_darkest"],
                             (base[0] - 1, base[1] - 1, 3, 3))
            pygame.draw.rect(surface, _NS_gornak.PALETTE["armor_mid"],
                             (base[0], base[1] - 1, 1, 2))

    def _draw_gnk_head(surface, cx, cy, facing, phase, action):
        """Head with mohawk, face, and glowing eyes."""
        # Neck
        pygame.draw.rect(surface, _NS_gornak.PALETTE["shadow_deep"],
                         (cx - 2, cy + 6, 5, 3))
        pygame.draw.rect(surface, _NS_gornak.PALETTE["skin_darkest"],
                         (cx - 2, cy + 6, 4, 3))
        pygame.draw.rect(surface, _NS_gornak.PALETTE["skin_dark"],
                         (cx - 1, cy + 6, 3, 2))

        # Head shape (rounded square)
        head_pts = [
            (cx - 6, cy - 2),
            (cx - 7, cy + 2),
            (cx - 5, cy + 6),
            (cx + 5, cy + 6),
            (cx + 7, cy + 2),
            (cx + 6, cy - 2),
            (cx + 4, cy - 5),
            (cx - 4, cy - 5),
        ]
        _NS_gornak._poly(surface, _NS_gornak.PALETTE["shadow_deep"],
                         [(px + 1, py + 1) for px, py in head_pts])
        _NS_gornak._poly(surface, _NS_gornak.PALETTE["skin_darkest"], head_pts)

        # Face main tone
        _NS_gornak._poly(surface, _NS_gornak.PALETTE["skin_dark"], [
            (cx - 5, cy - 1),
            (cx - 6, cy + 2),
            (cx - 4, cy + 5),
            (cx + 4, cy + 5),
            (cx + 6, cy + 2),
            (cx + 5, cy - 1),
            (cx + 3, cy - 4),
            (cx - 3, cy - 4),
        ])

        # Face highlight (lit from front-top)
        _NS_gornak._poly(surface, _NS_gornak.PALETTE["skin_mid"], [
            (cx - 3, cy),
            (cx - 4, cy + 2),
            (cx - 2, cy + 4),
            (cx + 4, cy + 4),
            (cx + 5, cy + 2),
            (cx + 4, cy - 1),
            (cx + 2, cy - 3),
            (cx - 2, cy - 3),
        ])

        # Cheek/chin light
        _NS_gornak._poly(surface, _NS_gornak.PALETTE["skin_light"], [
            (cx + facing * 1, cy - 1),
            (cx + facing * 4, cy),
            (cx + facing * 3, cy + 3),
            (cx + facing * 1, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_gornak.PALETTE["skin_shine"],
                         (cx + facing * 3, cy, 1, 1))

        # Eyebrow (thick, angry)
        pygame.draw.rect(surface, _NS_gornak.PALETTE["shadow_deep"],
                         (cx - 4, cy - 1, 8, 1))
        pygame.draw.rect(surface, _NS_gornak.PALETTE["hair_dark"],
                         (cx - 3, cy - 1, 6, 1))

        # Eyes (glowing violet)
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_off in (-2, 2):
            ex = cx + eye_off
            ey = cy + 1
            # Glow halo
            for r in range(3, 0, -1):
                alpha = _NS_gornak._alpha(120 * (3 - r) / 3 * eye_pulse)
                _NS_gornak._aacircle(surface, (*_NS_gornak.PALETTE["magic_mid"], alpha),
                                     (ex, ey), r)
            pygame.draw.rect(surface, _NS_gornak.PALETTE["shadow_deep"],
                             (ex - 1, ey, 3, 2))
            pygame.draw.rect(surface, _NS_gornak.PALETTE["eye_dark"],
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_gornak.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_gornak.PALETTE["eye_glow"],
                             (ex, ey, 1, 1))

        # Nose
        pygame.draw.rect(surface, _NS_gornak.PALETTE["skin_darkest"],
                         (cx, cy + 2, 1, 2))
        pygame.draw.rect(surface, _NS_gornak.PALETTE["skin_dark"],
                         (cx + facing, cy + 2, 1, 1))

        # Mouth (stern)
        pygame.draw.rect(surface, _NS_gornak.PALETTE["shadow_deep"],
                         (cx - 2, cy + 4, 4, 1))
        pygame.draw.rect(surface, _NS_gornak.PALETTE["skin_darkest"],
                         (cx - 1, cy + 4, 2, 1))

        # Ear (side)
        pygame.draw.rect(surface, _NS_gornak.PALETTE["skin_darkest"],
                         (cx - facing * 6, cy + 1, 1, 3))
        pygame.draw.rect(surface, _NS_gornak.PALETTE["skin_dark"],
                         (cx - facing * 6, cy + 2, 1, 1))

        # MOHAWK (tall spiky purple hair)
        _NS_gornak._draw_mohawk(surface, cx, cy - 5, facing, phase)

    def _draw_mohawk(surface, cx, cy, facing, phase):
        """Tall spiky purple mohawk."""
        wave = math.sin(phase * 1.2) * 0.5

        # Multiple spikes forming mohawk
        spikes = [
            # (x_offset, height, width)
            (-3, 3, 2),
            (-1, 5, 2),
            (1, 6, 2),
            (3, 4, 2),
        ]

        for i, (x_off, h, w) in enumerate(spikes):
            spike_x = cx + x_off
            spike_h = h + int(math.sin(phase * 1.5 + i) * 1)
            spike_top = cy - spike_h

            # Shadow
            _NS_gornak._poly(surface, _NS_gornak.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_top + 1),
                (spike_x - w // 2 + 1, cy + 1),
                (spike_x + w // 2 + 1, cy + 1),
            ])
            # Base dark
            _NS_gornak._poly(surface, _NS_gornak.PALETTE["hair_dark"], [
                (spike_x, spike_top),
                (spike_x - w // 2, cy),
                (spike_x + w // 2, cy),
            ])
            # Mid
            _NS_gornak._poly(surface, _NS_gornak.PALETTE["hair_mid"], [
                (spike_x, spike_top),
                (spike_x - w // 2 + 1, cy),
                (spike_x + w // 2, cy),
            ])
            # Light tip
            pygame.draw.rect(surface, _NS_gornak.PALETTE["hair_light"],
                             (spike_x, spike_top, 1, 2))
            pygame.draw.rect(surface, _NS_gornak.PALETTE["hair_shine"],
                             (spike_x, spike_top, 1, 1))

        # Base hair line connecting spikes
        pygame.draw.rect(surface, _NS_gornak.PALETTE["hair_dark"],
                         (cx - 4, cy, 8, 1))
        pygame.draw.rect(surface, _NS_gornak.PALETTE["hair_mid"],
                         (cx - 3, cy, 6, 1))

    # ============================================================
    # CRESCENT SLASH (attack FX)
    # ============================================================
    def _draw_crescent_slash(surface, boss, cx, cy, progress):
        """Purple crescent slash arc during melee attack."""
        if progress < 0.35 or progress > 0.85:
            return

        facing = boss.direction
        t = (progress - 0.35) / 0.5  # 0 to 1
        t = min(1.0, t)

        # Slash center (in front of boss)
        slash_cx = cx + facing * 22
        slash_cy = cy - 4

        # Slash grows and fades
        radius = int(14 + t * 8)
        alpha = _NS_gornak._alpha(255 * (1 - t * 0.6))

        # Draw crescent as thick arc
        slash_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
        center = (40, 40)

        # Arc angle
        start_angle = -math.pi * 0.6
        end_angle = math.pi * 0.6

        # Multiple layered arcs
        for layer_i, (r_off, thick, color, a_mult) in enumerate([
            (2, 5, _NS_gornak.PALETTE["magic_darkest"], 0.7),
            (1, 4, _NS_gornak.PALETTE["magic_dark"], 0.85),
            (0, 3, _NS_gornak.PALETTE["magic_mid"], 1.0),
            (-1, 2, _NS_gornak.PALETTE["magic_light"], 1.0),
            (-2, 1, _NS_gornak.PALETTE["magic_hot"], 1.0),
        ]):
            actual_alpha = int(alpha * a_mult)
            if actual_alpha <= 0:
                continue
            arc_r = radius + r_off
            arc_pts = []
            steps = 20
            for i in range(steps + 1):
                a = start_angle + (end_angle - start_angle) * i / steps
                px = center[0] + int(math.cos(a) * arc_r) * facing
                py = center[1] + int(math.sin(a) * arc_r)
                arc_pts.append((px, py))
            for i in range(len(arc_pts) - 1):
                pygame.draw.line(slash_surf, (*color, actual_alpha),
                                 arc_pts[i], arc_pts[i + 1], thick)

        # Bright inner core line
        inner_pts = []
        steps = 20
        for i in range(steps + 1):
            a = start_angle + (end_angle - start_angle) * i / steps
            px = center[0] + int(math.cos(a) * (radius - 3)) * facing
            py = center[1] + int(math.sin(a) * (radius - 3))
            inner_pts.append((px, py))
        for i in range(len(inner_pts) - 1):
            pygame.draw.line(slash_surf,
                             (*_NS_gornak.PALETTE["magic_shine"], alpha),
                             inner_pts[i], inner_pts[i + 1], 1)

        # Sparkles along arc
        for i in range(8):
            spark_t = (i / 8) * (end_angle - start_angle) + start_angle
            sx = center[0] + int(math.cos(spark_t) * radius) * facing
            sy = center[1] + int(math.sin(spark_t) * radius)
            pygame.draw.rect(slash_surf, (*_NS_gornak.PALETTE["magic_shine"], alpha),
                             (sx, sy, 1, 1))
            pygame.draw.rect(slash_surf, (*_NS_gornak.PALETTE["white"], alpha),
                             (sx, sy, 1, 1))

        surface.blit(slash_surf, (slash_cx - 40, slash_cy - 40))

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((80, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 18)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 10 - radius, 60 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (5, 2, 10, 180), (5, 5, 70, 10))
        surface.blit(shadow, (x - 40, y - 10))

    def _draw_magic_aura(surface, x, y, phase):
        """Violet magic aura behind boss."""
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75

        aura = pygame.Surface((160, 140), pygame.SRCALPHA)
        for radius in range(70, 5, -4):
            alpha = _NS_gornak._alpha((70 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_gornak._aacircle(aura, (*_NS_gornak.PALETTE["magic_darkest"], alpha),
                                     (80, 70), radius)
        for radius in range(45, 5, -3):
            alpha = _NS_gornak._alpha((45 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_gornak._aacircle(aura, (*_NS_gornak.PALETTE["magic_dark"], alpha),
                                     (80, 70), radius)
        surface.blit(aura, (x - 80, y - 70))

        # Floating magic sparkles
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            r = 30 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * r)
            sy = y - 5 + int(math.sin(angle) * r * 0.5)
            alpha = _NS_gornak._alpha(200 + math.sin(phase * 3 + i) * 55)
            pygame.draw.rect(surface, _NS_gornak.PALETTE["magic_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_gornak.PALETTE["magic_hot"], (sx, sy, 1, 1))

    def _draw_ground_rune(surface, x, y, phase, skill):
        """Magic rune circle on ground."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((120, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_gornak.PALETTE["magic_darkest"], 200),
                            (5, 12, 110, 18), 2)
        pygame.draw.ellipse(ring, (*_NS_gornak.PALETTE["magic_dark"], 220),
                            (12, 14, 96, 14), 1)
        pygame.draw.ellipse(ring, (*_NS_gornak.PALETTE["magic_mid"], 180),
                            (22, 16, 76, 10), 1)

        # Rune symbols around ring
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 60 + int(math.cos(angle) * 35)
            y1 = 21 + int(math.sin(angle) * 7)
            x2 = 60 + int(math.cos(angle) * 52)
            y2 = 21 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_gornak.PALETTE["magic_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_gornak.PALETTE["magic_hot"],
                                       _NS_gornak._alpha(160 * pulse)),
                                (10, 8, 100, 26), 1)
        surface.blit(ring, (x - 60, y - 20))

    # ============================================================
    # SKILL Q: MANA BREAK (magic projectile)
    # ============================================================
    def _draw_manabreak_ground(surface, boss, x, y, timer, phase):
        """Small charge circle before launch."""
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            t = progress / 0.3
            r = int(20 * t)
            alpha = _NS_gornak._alpha(180 * t)
            _NS_gornak._aacircle(surface, (*_NS_gornak.PALETTE["magic_mid"], alpha),
                                 (x, y + 40), r, 2)
            _NS_gornak._aacircle(surface, (*_NS_gornak.PALETTE["magic_light"], alpha),
                                 (x, y + 40), max(1, r - 3), 1)

    def _draw_manabreak_foreground(surface, boss, x, y, timer, phase):
        """Magic bolt projectile."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_gornak._target_position(boss, x, y)

        if progress < 0.25:
            # Charge in hand
            t = progress / 0.25
            charge_x = x + facing * 18
            charge_y = y - 4
            cr = int(3 + t * 6)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_gornak._alpha(220 * (cr + 4 - r) / (cr + 4))
                _NS_gornak._aacircle(surface, (*_NS_gornak.PALETTE["magic_darkest"], alpha),
                                     (charge_x, charge_y), r)
            for r in range(cr, 0, -1):
                alpha = _NS_gornak._alpha(240 * (cr - r + 1) / cr)
                _NS_gornak._aacircle(surface, (*_NS_gornak.PALETTE["magic_mid"], alpha),
                                     (charge_x, charge_y), r)
            _NS_gornak._aacircle(surface, _NS_gornak.PALETTE["magic_light"],
                                 (charge_x, charge_y), max(1, cr - 2))
            _NS_gornak._aacircle(surface, _NS_gornak.PALETTE["magic_shine"],
                                 (charge_x, charge_y), max(1, cr - 4))
            pygame.draw.rect(surface, _NS_gornak.PALETTE["white"], (charge_x, charge_y, 1, 1))

            # Sparks
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                sx = charge_x + int(math.cos(angle) * (cr + 3))
                sy = charge_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_gornak.PALETTE["magic_hot"], (sx, sy, 1, 1))
        else:
            # Projectile flying
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 22
            start_y = y - 4
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Long trail
            for i in range(10):
                trail_t = max(0.0, t - i * 0.045)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_gornak._alpha(240 - i * 24)

                size = max(1, 7 - i)
                _NS_gornak._aacircle(surface, (*_NS_gornak.PALETTE["magic_darkest"], alpha),
                                     (px, py), size)
                _NS_gornak._aacircle(surface, (*_NS_gornak.PALETTE["magic_dark"], alpha),
                                     (px, py), max(1, size - 1))
                _NS_gornak._aacircle(surface, (*_NS_gornak.PALETTE["magic_mid"], alpha),
                                     (px, py), max(1, size - 2))
                _NS_gornak._aacircle(surface, (*_NS_gornak.PALETTE["magic_light"], alpha),
                                     (px, py), max(1, size - 3))

                if i < 4:
                    for s in range(2):
                        spark_x = px + int(math.sin(t * 6 + i + s) * (size + 2))
                        spark_y = py + int(math.cos(t * 6 + i + s) * (size + 2))
                        pygame.draw.rect(surface, (*_NS_gornak.PALETTE["magic_hot"], alpha),
                                         (spark_x, spark_y, 1, 1))

            # Bright bolt head
            for r in range(12, 3, -2):
                alpha = _NS_gornak._alpha(80 * (12 - r) / 12)
                _NS_gornak._aacircle(surface, (*_NS_gornak.PALETTE["magic_light"], alpha),
                                     (bx, by), r)
            _NS_gornak._aacircle(surface, _NS_gornak.PALETTE["magic_darkest"], (bx, by), 8)
            _NS_gornak._aacircle(surface, _NS_gornak.PALETTE["magic_dark"], (bx, by), 6)
            _NS_gornak._aacircle(surface, _NS_gornak.PALETTE["magic_mid"], (bx, by), 4)
            _NS_gornak._aacircle(surface, _NS_gornak.PALETTE["magic_light"], (bx, by), 3)
            _NS_gornak._aacircle(surface, _NS_gornak.PALETTE["magic_shine"], (bx, by), 2)
            pygame.draw.rect(surface, _NS_gornak.PALETTE["white"], (bx, by, 1, 1))

            # Impact
            if t > 0.88:
                st = (t - 0.88) / 0.12
                radius = int(10 + st * 24)
                alpha = _NS_gornak._alpha(240 * (1 - st))
                _NS_gornak._aacircle(surface, (*_NS_gornak.PALETTE["magic_darkest"], alpha),
                                     (tx, ty), radius + 3, 3)
                _NS_gornak._aacircle(surface, (*_NS_gornak.PALETTE["magic_dark"], alpha),
                                     (tx, ty), radius, 3)
                _NS_gornak._aacircle(surface, (*_NS_gornak.PALETTE["magic_mid"], alpha),
                                     (tx, ty), max(1, radius - 5), 2)
                _NS_gornak._aacircle(surface, (*_NS_gornak.PALETTE["magic_light"], alpha),
                                     (tx, ty), max(1, radius - 10), 1)

                # Radial burst
                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface, (*_NS_gornak.PALETTE["magic_hot"], alpha),
                                     (ex, ey, 2, 2))
                    pygame.draw.rect(surface, (*_NS_gornak.PALETTE["magic_shine"], alpha),
                                     (ex, ey, 1, 1))

    # ============================================================
    # SKILL W: BLINK (teleport)
    # ============================================================
    def _draw_blink_ground(surface, boss, x, y, timer, phase):
        """Teleport ring at position."""
        duration = 30
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ring at old position (start) fading, ring at new (end) growing
        if progress < 0.5:
            # Depart ring
            t = progress / 0.5
            r = int(12 + t * 20)
            alpha = _NS_gornak._alpha(240 * (1 - t))
            for i in range(3):
                _NS_gornak._aacircle(surface,
                                     (*_NS_gornak.PALETTE["magic_light"], alpha),
                                     (x, y + 40), r + i * 2, 1)
        else:
            # Arrival ring
            t = (progress - 0.5) / 0.5
            r = int(30 - t * 15)
            alpha = _NS_gornak._alpha(240 * t)
            for i in range(3):
                _NS_gornak._aacircle(surface,
                                     (*_NS_gornak.PALETTE["magic_hot"], alpha),
                                     (x, y + 40), r - i * 2, 1)

        # Sparkles
        for i in range(12):
            angle = phase * 2 + i * math.pi / 6
            r_sp = 20 + int(math.sin(phase * 3 + i) * 8)
            sx = x + int(math.cos(angle) * r_sp)
            sy = y + 40 + int(math.sin(angle) * r_sp * 0.4)
            pygame.draw.rect(surface, _NS_gornak.PALETTE["magic_shine"], (sx, sy, 1, 1))

    # ============================================================
    # SKILL E: COUNTERSPELL (magic shield burst)
    # ============================================================
    def _draw_counterspell_ground(surface, boss, x, y, timer, phase):
        """Ground circle for counterspell."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for i in range(2):
            r = int(35 + i * 5 + math.sin(phase * 2) * 2)
            alpha = _NS_gornak._alpha(200 * pulse - i * 40)
            _NS_gornak._aacircle(surface, (*_NS_gornak.PALETTE["magic_mid"], alpha),
                                 (x, y + 40), r, 2)
            _NS_gornak._aacircle(surface, (*_NS_gornak.PALETTE["magic_light"], alpha),
                                 (x, y + 40), r, 1)

    def _draw_counterspell_foreground(surface, boss, x, y, timer, phase):
        """Bubble shield around boss with rune sigils."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Bubble
        breath = math.sin(phase * 2.5) * 2
        r = 42 + int(breath)

        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)

        # Multi-ring
        for i, (thickness, alpha_val) in enumerate([
            (3, 130), (2, 170), (1, 220),
        ]):
            _NS_gornak._aacircle(bubble, (*_NS_gornak.PALETTE["magic_dark"], alpha_val),
                                 center, r - i, thickness)
            _NS_gornak._aacircle(bubble, (*_NS_gornak.PALETTE["magic_mid"], alpha_val),
                                 center, r - i - 1, 1)

        # Rotating rune symbols on shield
        for i in range(6):
            angle = phase * 1.2 + i * math.pi / 3
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            # Cross/rune
            pygame.draw.rect(bubble, (*_NS_gornak.PALETTE["magic_hot"], 240),
                             (sx - 2, sy, 5, 1))
            pygame.draw.rect(bubble, (*_NS_gornak.PALETTE["magic_hot"], 240),
                             (sx, sy - 2, 1, 5))
            pygame.draw.rect(bubble, (*_NS_gornak.PALETTE["magic_shine"], 255),
                             (sx, sy, 1, 1))

        # Hex pattern inside
        for i in range(12):
            angle = phase * 0.5 + i * math.pi / 6
            inner_r = r - 6
            bx = center[0] + int(math.cos(angle) * inner_r)
            by = center[1] + int(math.sin(angle) * inner_r)
            alpha = _NS_gornak._alpha(160)
            pygame.draw.rect(bubble, (*_NS_gornak.PALETTE["magic_light"], alpha),
                             (bx, by, 1, 1))

        surface.blit(bubble, (x - r - 10, y - r - 10 + 5))

        # Energy tendrils
        for i in range(8):
            angle = phase * 0.8 + i * math.pi / 4
            end_x = x + int(math.cos(angle) * (r + 6))
            end_y = y + 5 + int(math.sin(angle) * (r + 6))
            alpha = _NS_gornak._alpha(180 + math.sin(phase * 4 + i) * 60)
            pygame.draw.line(surface, (*_NS_gornak.PALETTE["magic_light"], alpha),
                             (x + int(math.cos(angle) * r),
                              y + 5 + int(math.sin(angle) * r)),
                             (end_x, end_y), 1)
            pygame.draw.rect(surface, _NS_gornak.PALETTE["magic_hot"], (end_x, end_y, 1, 1))

    # ============================================================
    # SKILL R: MANA VOID (vortex + explosion)
    # ============================================================
    def _draw_manavoid_ground(surface, boss, x, y, timer, phase):
        """Void vortex on ground at target."""
        tx, ty = _NS_gornak._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.5:
            # Vortex growing
            t = progress / 0.5
            r = int(45 * t)
            alpha = _NS_gornak._alpha(220 * t)
            pygame.draw.ellipse(surface, (*_NS_gornak.PALETTE["magic_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_gornak.PALETTE["magic_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
        else:
            # Explosion aftermath ring
            t = (progress - 0.5) / 0.5
            r = int(45 + t * 30)
            alpha = _NS_gornak._alpha(240 * (1 - t))
            pygame.draw.ellipse(surface, (*_NS_gornak.PALETTE["magic_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_gornak.PALETTE["magic_mid"], alpha),
                                (tx - r + 4, ty - r // 3 + 3,
                                 r * 2 - 8, r * 2 // 3 - 6), 2)

    def _draw_manavoid_foreground(surface, boss, x, y, timer, phase):
        """Swirling vortex + explosion."""
        tx, ty = _NS_gornak._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.5:
            # Swirling vortex spiral
            t = progress / 0.5
            max_r = int(30 * t)

            # Spiral arms
            for arm in range(3):
                for step in range(20):
                    s_t = step / 20
                    spiral_angle = phase * 3 + arm * math.pi * 2 / 3 + s_t * math.pi * 4
                    s_r = max_r * (1 - s_t)
                    sx = tx + int(math.cos(spiral_angle) * s_r)
                    sy = ty + int(math.sin(spiral_angle) * s_r * 0.6)
                    alpha = _NS_gornak._alpha(240 * (1 - s_t) * t)
                    if alpha > 0:
                        pygame.draw.rect(surface,
                                         (*_NS_gornak.PALETTE["magic_light"], alpha),
                                         (sx, sy, 2, 2))
                        pygame.draw.rect(surface,
                                         (*_NS_gornak.PALETTE["magic_hot"], alpha),
                                         (sx, sy, 1, 1))

            # Central dark eye
            core_r = int(6 + t * 4)
            for r in range(core_r, 0, -1):
                alpha = _NS_gornak._alpha(240 * (core_r - r + 1) / core_r)
                _NS_gornak._aacircle(surface,
                                     (*_NS_gornak.PALETTE["magic_darkest"], alpha),
                                     (tx, ty), r)

        elif progress < 0.65:
            # EXPLOSION burst
            t = (progress - 0.5) / 0.15
            intensity = math.sin(t * math.pi)
            burst_r = int(40 + t * 20)

            # Central bright core
            for r in range(burst_r, 0, -3):
                alpha = _NS_gornak._alpha(240 * intensity * (burst_r - r + 3) / burst_r)
                _NS_gornak._aacircle(surface,
                                     (*_NS_gornak.PALETTE["magic_light"], alpha),
                                     (tx, ty), r)
            _NS_gornak._aacircle(surface, _NS_gornak.PALETTE["magic_shine"],
                                 (tx, ty), 8)
            _NS_gornak._aacircle(surface, _NS_gornak.PALETTE["white"],
                                 (tx, ty), 4)

            # Radiating spikes
            for i in range(16):
                angle = i * math.pi / 8
                end_x = tx + int(math.cos(angle) * burst_r)
                end_y = ty + int(math.sin(angle) * burst_r * 0.7)
                alpha = _NS_gornak._alpha(255 * intensity)
                pygame.draw.line(surface, (*_NS_gornak.PALETTE["magic_hot"], alpha),
                                 (tx, ty), (end_x, end_y), 2)
                pygame.draw.rect(surface, (*_NS_gornak.PALETTE["magic_shine"], alpha),
                                 (end_x, end_y, 2, 2))
        else:
            # Rising void debris
            t = (progress - 0.65) / 0.35
            for i in range(14):
                rise_t = (phase * 0.6 + i * 0.08) % 1.0
                rx = tx + int(math.sin(phase + i) * 25)
                ry = ty - int(rise_t * 40)
                alpha = _NS_gornak._alpha(220 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_gornak._aacircle(surface,
                                         (*_NS_gornak.PALETTE["magic_dark"], alpha),
                                         (rx, ry), 3)
                    _NS_gornak._aacircle(surface,
                                         (*_NS_gornak.PALETTE["magic_mid"], alpha),
                                         (rx, ry), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_gornak.PALETTE["magic_hot"], alpha),
                                     (rx, ry, 1, 1))

# ====================================================================
# MORGATH (ARC WARDEN) - Mini Boss
# ====================================================================
import math
import pygame


class _NS_morgath:
    """Namespace morgath - Arc Warden mini boss (ranged lightning caster)."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Robe / cloak (dark purple)
        "robe_darkest": (12, 8, 25),
        "robe_dark": (30, 20, 55),
        "robe_mid": (60, 40, 100),
        "robe_light": (105, 75, 160),
        "robe_edge": (155, 120, 210),

        # Armor plating (dark blue-steel)
        "armor_darkest": (8, 12, 25),
        "armor_dark": (25, 40, 65),
        "armor_mid": (55, 85, 120),
        "armor_light": (110, 150, 190),
        "armor_shine": (180, 210, 240),

        # Gold trim (armor accents)
        "gold_dark": (75, 55, 20),
        "gold_mid": (160, 125, 55),
        "gold_light": (230, 195, 110),
        "gold_shine": (255, 235, 170),

        # Crystal orb (bright cyan-blue, main magic color)
        "orb_darkest": (5, 15, 40),
        "orb_dark": (20, 55, 130),
        "orb_mid": (60, 130, 220),
        "orb_light": (130, 200, 255),
        "orb_hot": (200, 235, 255),
        "orb_shine": (240, 250, 255),

        # Lightning/arc (bright electric blue-white)
        "arc_darkest": (15, 30, 80),
        "arc_dark": (40, 90, 190),
        "arc_mid": (90, 160, 240),
        "arc_light": (180, 220, 255),
        "arc_hot": (230, 245, 255),
        "arc_shine": (255, 255, 255),

        # Flux purple (ability accent)
        "flux_darkest": (25, 8, 45),
        "flux_dark": (65, 25, 110),
        "flux_mid": (130, 60, 200),
        "flux_light": (190, 130, 240),
        "flux_hot": (225, 180, 255),

        # Skin (visible on hands/face if any) - shadowed
        "skin_darkest": (35, 30, 55),
        "skin_dark": (75, 65, 100),
        "skin_mid": (130, 115, 160),
        "skin_light": (180, 165, 210),

        # Ground rune
        "rune_dark": (15, 25, 60),
        "rune_mid": (60, 110, 200),
        "rune_light": (150, 200, 255),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 8),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_morgath._clamp(color)
        if _NS_morgath.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_morgath._clamp(color)
        if _NS_morgath.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_morgath._clamp(color), points)

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
        return int(x + 240 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)

    def _jagged_line(surface, color, start, end, jitter=4, segments=6, width=2):
        """Draw jagged lightning line between two points."""
        color = _NS_morgath._clamp(color)
        prev = start
        for i in range(1, segments + 1):
            t = i / segments
            bx = int(start[0] + (end[0] - start[0]) * t)
            by = int(start[1] + (end[1] - start[1]) * t)
            if i < segments:
                # Perpendicular jitter
                dx = end[0] - start[0]
                dy = end[1] - start[1]
                length = max(1, math.hypot(dx, dy))
                perp_x = -dy / length
                perp_y = dx / length
                jit = (math.sin(t * 12 + start[0]) - 0.5) * jitter * 2
                bx += int(perp_x * jit)
                by += int(perp_y * jit)
            pygame.draw.line(surface, color, prev, (bx, by), width)
            prev = (bx, by)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_morgath(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        # Beam-only pass (hero): body sudah di-blit ter-scale oleh
        # heroes/__init__.py; di sini hanya beam yang digambar, pada
        # koordinat & skala dunia = identik dengan versi mini boss.
        if getattr(boss, "_beam_pass_only", False):
            _NS_morgath._draw_mor_beam_pass(surface, boss, x, y)
            return
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_morgath._detect_moving(boss)
        _NS_morgath._update_mor_attack_anim(boss)
        attacking = (
            getattr(boss, "_mor_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient
        _NS_morgath._draw_arc_aura(surface, x, y, pulse)
        _NS_morgath._draw_ground_rune(surface, x, y + 42, pulse, active_skill)

        # Ground FX per skill
        if active_skill == "q":
            _NS_morgath._draw_sparkwraith_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_morgath._draw_flux_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_morgath._draw_magneticfield_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morgath._draw_tempest_ground(surface, boss, x, y, skill_timer, pulse)

        # Body
        if attacking:
            _NS_morgath._draw_mor_attack(surface, boss, x, y)
        elif moving:
            _NS_morgath._draw_mor_walk(surface, boss, x, y)
        else:
            _NS_morgath._draw_mor_idle(surface, boss, x, y)

        # Tempest Double clone
        if active_skill == "r":
            _NS_morgath._draw_tempest_clone(surface, boss, x, y, skill_timer, pulse)

        # Foreground FX
        if active_skill == "q":
            _NS_morgath._draw_sparkwraith_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_morgath._draw_flux_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_morgath._draw_magneticfield_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morgath._draw_tempest_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_mor_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_mor_previous_timer", 0))
        active = bool(getattr(boss, "_mor_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._mor_attack_active = True
            boss._mor_attack_frame = 0
            # Kunci arah + posisi target saat serangan dimulai.
            # Beam petir jadi terbang lurus ke titik target yang
            # SAMA selama animasi, tidak ikut "lompat" kalau hero
            # (versi summon) berbalik / ganti target di tengah cast.
            boss._mor_attack_dir = int(getattr(boss, "direction", 1))
            # Simpan sebagai OFFSET DUNIA relatif terhadap posisi boss
            # (bukan ruang canvas). Saat render ter-scale,
            # _draw_lightning_projectile membaginya dengan
            # _render_scale; saat render di layar (skala 1.0, termasuk
            # beam pass hero) offset dipakai apa adanya. Dengan cara
            # ini tidak ada galat pembulatan dari konversi int canvas.
            _t = getattr(boss, "target", None)
            if _t is not None and getattr(_t, "alive", True):
                boss._mor_attack_target = (
                    int(_t.x) - int(getattr(boss, "x", 0)),
                    int(_t.y) - int(getattr(boss, "y", 0)))
            else:
                tx, ty = _NS_morgath._target_position(
                    boss, getattr(boss, "x", 0), getattr(boss, "y", 0))
                boss._mor_attack_target = (
                    int(tx) - int(getattr(boss, "x", 0)),
                    int(ty) - int(getattr(boss, "y", 0)))
            active = True
        elif active and timer > 0:
            boss._mor_attack_frame = int(getattr(boss, "_mor_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._mor_attack_active = False
            boss._mor_attack_frame = 0
            active = False

        boss._mor_previous_timer = timer
        boss._mor_attack_progress = (
            min(1.0, getattr(boss, "_mor_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_mor_last_x"):
            boss._mor_last_x = boss.x
            boss._mor_last_y = boss.y
            return False
        dx = abs(boss.x - boss._mor_last_x)
        dy = abs(boss.y - boss._mor_last_y)
        boss._mor_last_x = boss.x
        boss._mor_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_mor_idle(surface, boss, x, y):
        # Slow float bob (mystical hover feel)
        bob = int(math.sin(boss.pulse * 0.7) * 3)
        _NS_morgath._draw_shadow(surface, x, y + 46)
        _NS_morgath._draw_mor_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")

    def _draw_mor_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.1)) * 3)
        sway = int(math.sin(phase * 0.7) * 2)
        _NS_morgath._draw_shadow(surface, x + sway, y + 46)
        _NS_morgath._draw_mor_body(surface, x + sway, y - bob + 2,
                                    boss.direction, phase, "walk")

    def _mor_attack_pose(boss, progress):
        """Arah + lean/lift pose serangan (dipakai body & beam pass)."""
        # Arah terkunci saat serangan dimulai (lihat
        # _update_mor_attack_anim). Fallback ke arah live kalau
        # state kunci tidak ada (entity fake/portrait).
        facing = getattr(boss, "_mor_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Charge → cast → release (little forward lean, arm outstretched)
        if progress < 0.4:
            t = progress / 0.4
            lean = int(t * 2) * facing * -1  # slight back charge
            lift = int(t * 2)
        elif progress < 0.7:
            t = (progress - 0.4) / 0.3
            lean = int((-2 + t * 6)) * facing
            lift = int(2 - t * 3)
        else:
            t = (progress - 0.7) / 0.3
            lean = int(4 * (1 - t)) * facing
            lift = int(-1 + t)
        return facing, lean, lift

    def _mor_progress(boss):
        # LIVE dari attack_timer (bukan counter frame yang cuma naik
        # saat renderer dipanggil). Dengan body hero di-cache
        # (renderer dipanggil tiap N frame), progress tetap maju tiap
        # frame -> beam live tetap mulus 60fps.
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_mor_attack_active", False):
            return max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        return 0.0

    def _draw_mor_attack(surface, boss, x, y):
        progress = _NS_morgath._mor_progress(boss)
        facing, lean, lift = _NS_morgath._mor_attack_pose(boss, progress)

        _NS_morgath._draw_shadow(surface, x + lean, y + 46)
        _NS_morgath._draw_mor_body(surface, x + lean, y - lift, facing,
                                    boss.pulse, "attack", progress)
        # Lightning bolt projectile. Skip saat beam digambar terpisah
        # langsung di layar pada skala 1.0 (heroes/__init__.py) supaya
        # beam hero = persis beam mini boss (tidak kena smoothscale).
        if not getattr(boss, "_skip_beam", False):
            _NS_morgath._draw_lightning_projectile(surface, boss, x + lean, y - lift, progress)

    def _draw_mor_beam_pass(surface, boss, x, y):
        """Gambar HANYA beam pada koordinat dunia (skala 1.0).

        Dipanggil heroes/__init__.py setelah body hero di-blit
        ter-scale. Hasilnya beam berukuran & berkecerahan persis
        sama seperti saat entity ini jadi mini boss.

        Catatan: _update_mor_attack_anim dipanggil di sini (tiap
        frame, idempoten) supaya state kunci arah/target tetap
        terinisialisasi walau frame pertama serangan kena cache
        hit (body hero di-cache, renderer tidak selalu dipanggil).
        """
        _NS_morgath._update_mor_attack_anim(boss)
        progress = _NS_morgath._mor_progress(boss)
        facing, lean, lift = _NS_morgath._mor_attack_pose(boss, progress)
        _NS_morgath._draw_lightning_projectile(surface, boss, x + lean, y - lift, progress)

    # ============================================================
    # BODY
    # ============================================================
    def _draw_mor_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw mystical hooded caster body."""
        # Cape/robe back (visible behind)
        _NS_morgath._draw_mor_cape(surface, cx, cy, facing, phase, action)

        # Legs / lower robe
        _NS_morgath._draw_mor_legs(surface, cx, cy + 12, facing, phase, action)

        # Robe skirt
        _NS_morgath._draw_mor_robe(surface, cx, cy + 4, facing, phase)

        # Torso armor
        _NS_morgath._draw_mor_torso(surface, cx, cy - 6, facing, phase)

        # Back arm
        _NS_morgath._draw_mor_arm_back(surface, cx, cy - 4, facing, phase, action, attack_progress)

        # Head (hood + orb helm)
        _NS_morgath._draw_mor_head(surface, cx, cy - 18, facing, phase, action)

        # Front arm (casts spells)
        _NS_morgath._draw_mor_arm_front(surface, cx, cy - 4, facing, phase, action, attack_progress)

    def _draw_mor_cape(surface, cx, cy, facing, phase, action):
        """Flowing cape behind body."""
        sway = math.sin(phase * 0.8) * 3
        if action == "walk":
            sway += math.sin(phase * 1.5) * 2

        # Cape shape (wide behind)
        back_dir = -facing
        cape_pts = [
            (cx + back_dir * 3, cy - 8),
            (cx + back_dir * 8, cy - 4 + int(sway)),
            (cx + back_dir * 12, cy + 6 + int(sway * 1.3)),
            (cx + back_dir * 14, cy + 16 + int(sway * 1.5)),
            (cx + back_dir * 10, cy + 20 + int(sway * 1.5)),
            (cx + back_dir * 4, cy + 22),
            (cx + back_dir * 2, cy + 10),
            (cx + back_dir * 1, cy - 5),
        ]
        _NS_morgath._poly(surface, _NS_morgath.PALETTE["shadow_deep"],
                          [(px + 1, py + 1) for px, py in cape_pts])
        _NS_morgath._poly(surface, _NS_morgath.PALETTE["robe_darkest"], cape_pts)

        # Mid tone
        _NS_morgath._poly(surface, _NS_morgath.PALETTE["robe_dark"], [
            (cx + back_dir * 3, cy - 7),
            (cx + back_dir * 7, cy - 3 + int(sway)),
            (cx + back_dir * 10, cy + 6 + int(sway)),
            (cx + back_dir * 11, cy + 15 + int(sway)),
            (cx + back_dir * 8, cy + 19),
            (cx + back_dir * 3, cy + 20),
            (cx + back_dir * 2, cy + 10),
            (cx + back_dir * 1, cy - 5),
        ])

        # Fold lines
        for i in range(3):
            fold_x = cx + back_dir * (5 + i * 3)
            fold_y_top = cy - 4 + i * 2 + int(sway)
            fold_y_bot = cy + 15 + i * 2 + int(sway)
            pygame.draw.line(surface, _NS_morgath.PALETTE["robe_darkest"],
                             (fold_x, fold_y_top), (fold_x + back_dir * 1, fold_y_bot), 1)

        # Highlight edge
        pygame.draw.line(surface, _NS_morgath.PALETTE["robe_mid"],
                         (cx + back_dir * 1, cy - 5),
                         (cx + back_dir * 3, cy + 20), 1)

    def _draw_mor_legs(surface, cx, cy, facing, phase, action):
        """Legs with armored greaves."""
        if action == "walk":
            back_lift = max(0, -math.sin(phase * 2)) * 2
            front_lift = max(0, math.sin(phase * 2)) * 2
            stride = math.sin(phase * 2) * 2
        else:
            back_lift = front_lift = 0
            stride = 0

        # Back leg
        bx = cx - 4 + int(stride)
        by = cy - int(back_lift)
        _NS_morgath._draw_leg(surface, bx, by, facing, back=True)

        # Front leg
        fx = cx + 4 - int(stride)
        fy = cy - int(front_lift)
        _NS_morgath._draw_leg(surface, fx, fy, facing, back=False)

    def _draw_leg(surface, cx, cy, facing, back=False):
        """Armored leg with greave and boot."""
        # Thigh (dark robe)
        pygame.draw.rect(surface, _NS_morgath.PALETTE["shadow_deep"],
                         (cx - 3, cy - 6, 7, 8))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["robe_darkest"],
                         (cx - 3, cy - 6, 6, 8))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["robe_dark"],
                         (cx - 2, cy - 6, 4, 7))
        if not back:
            pygame.draw.rect(surface, _NS_morgath.PALETTE["robe_mid"],
                             (cx - 1, cy - 5, 2, 5))

        # Greave (metal shin)
        pygame.draw.rect(surface, _NS_morgath.PALETTE["shadow_deep"],
                         (cx - 3, cy, 7, 4))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["armor_darkest"],
                         (cx - 3, cy, 6, 4))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["armor_dark"],
                         (cx - 2, cy, 5, 3))
        if not back:
            pygame.draw.rect(surface, _NS_morgath.PALETTE["armor_mid"],
                             (cx - 2, cy, 4, 2))
            pygame.draw.rect(surface, _NS_morgath.PALETTE["armor_light"],
                             (cx - 1, cy, 2, 1))

        # Gold trim on greave
        pygame.draw.rect(surface, _NS_morgath.PALETTE["gold_dark"],
                         (cx - 2, cy + 2, 4, 1))
        if not back:
            pygame.draw.rect(surface, _NS_morgath.PALETTE["gold_mid"],
                             (cx - 1, cy + 2, 2, 1))

        # Boot
        pygame.draw.rect(surface, _NS_morgath.PALETTE["shadow_deep"],
                         (cx - 4, cy + 4, 9, 4))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["armor_darkest"],
                         (cx - 4, cy + 4, 8, 3))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["armor_dark"],
                         (cx - 3, cy + 4, 6, 2))
        if not back:
            pygame.draw.rect(surface, _NS_morgath.PALETTE["armor_mid"],
                             (cx - 3, cy + 4, 5, 1))

    def _draw_mor_robe(surface, cx, cy, facing, phase):
        """Ornate robe skirt with tabard."""
        sway = math.sin(phase * 0.7) * 1

        # Robe shape (trapezoid, longer than gornak)
        robe_pts = [
            (cx - 8, cy - 4),
            (cx + 8, cy - 4),
            (cx + 12, cy + 8),
            (cx + 6 + int(sway), cy + 14),
            (cx - 6 + int(sway), cy + 14),
            (cx - 12, cy + 8),
        ]
        _NS_morgath._poly(surface, _NS_morgath.PALETTE["shadow_deep"],
                          [(px + 1, py + 1) for px, py in robe_pts])
        _NS_morgath._poly(surface, _NS_morgath.PALETTE["robe_darkest"], robe_pts)

        # Mid tone
        _NS_morgath._poly(surface, _NS_morgath.PALETTE["robe_dark"], [
            (cx - 7, cy - 3),
            (cx + 7, cy - 3),
            (cx + 11, cy + 7),
            (cx + 5 + int(sway), cy + 13),
            (cx - 5 + int(sway), cy + 13),
            (cx - 11, cy + 7),
        ])

        # Central tabard (lighter, blue-purple)
        _NS_morgath._poly(surface, _NS_morgath.PALETTE["robe_mid"], [
            (cx - 3, cy - 3),
            (cx + 3, cy - 3),
            (cx + 4, cy + 8),
            (cx + int(sway), cy + 12),
            (cx - 4, cy + 8),
        ])

        # Highlight
        pygame.draw.rect(surface, _NS_morgath.PALETTE["robe_light"],
                         (cx - 1, cy - 1, 2, 6))

        # Fold lines
        for x_off in (-6, -3, 3, 6):
            pygame.draw.line(surface, _NS_morgath.PALETTE["robe_darkest"],
                             (cx + x_off, cy - 2),
                             (cx + x_off + int(sway * 0.5), cy + 12), 1)

        # Gold trim (belt)
        pygame.draw.rect(surface, _NS_morgath.PALETTE["gold_dark"],
                         (cx - 9, cy - 4, 18, 3))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["gold_mid"],
                         (cx - 9, cy - 4, 18, 2))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["gold_light"],
                         (cx - 8, cy - 3, 16, 1))

        # Belt buckle (crystal gem)
        pygame.draw.rect(surface, _NS_morgath.PALETTE["orb_darkest"],
                         (cx - 2, cy - 4, 4, 3))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["orb_dark"],
                         (cx - 2, cy - 4, 3, 3))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["orb_mid"],
                         (cx - 1, cy - 3, 2, 1))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["orb_light"],
                         (cx, cy - 3, 1, 1))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["orb_shine"],
                         (cx, cy - 3, 1, 1))

        # Gold trim on bottom of robe
        pygame.draw.line(surface, _NS_morgath.PALETTE["gold_dark"],
                         (cx - 6, cy + 13), (cx + 6, cy + 13), 1)
        pygame.draw.line(surface, _NS_morgath.PALETTE["gold_mid"],
                         (cx - 4, cy + 13), (cx + 4, cy + 13), 1)

    def _draw_mor_torso(surface, cx, cy, facing, phase):
        """Ornate armored torso with crystal chest gem."""
        breath = math.sin(phase * 0.7) * 1

        # Torso shape
        torso_pts = [
            (cx - 7, cy - 4),
            (cx - 8, cy + 2),
            (cx - 6, cy + 8),
            (cx + 6, cy + 8),
            (cx + 8, cy + 2),
            (cx + 7, cy - 4),
            (cx + 4, cy - 6),
            (cx - 4, cy - 6),
        ]
        _NS_morgath._poly(surface, _NS_morgath.PALETTE["shadow_deep"],
                          [(px + 1, py + 1) for px, py in torso_pts])
        _NS_morgath._poly(surface, _NS_morgath.PALETTE["armor_darkest"], torso_pts)

        # Main armor tone
        _NS_morgath._poly(surface, _NS_morgath.PALETTE["armor_dark"], [
            (cx - 6, cy - 3 + int(breath)),
            (cx - 7, cy + 2),
            (cx - 5, cy + 7),
            (cx + 5, cy + 7),
            (cx + 7, cy + 2),
            (cx + 6, cy - 3 + int(breath)),
            (cx + 3, cy - 5),
            (cx - 3, cy - 5),
        ])

        # Chest highlight
        _NS_morgath._poly(surface, _NS_morgath.PALETTE["armor_mid"], [
            (cx - 4, cy - 2 + int(breath)),
            (cx - 5, cy + 2),
            (cx - 3, cy + 5),
            (cx + 3, cy + 5),
            (cx + 5, cy + 2),
            (cx + 4, cy - 2 + int(breath)),
            (cx + 2, cy - 4),
            (cx - 2, cy - 4),
        ])

        # Bright spot (light hits chest)
        _NS_morgath._poly(surface, _NS_morgath.PALETTE["armor_light"], [
            (cx - 2, cy + int(breath)),
            (cx + 2, cy + int(breath)),
            (cx + 2, cy + 3),
            (cx - 2, cy + 3),
        ])

        # Chest crystal gem (glowing blue)
        gem_pulse = math.sin(phase * 2) * 0.3 + 0.7
        gx = cx
        gy = cy + 3
        # Glow halo
        for r in range(5, 0, -1):
            alpha = _NS_morgath._alpha(120 * (5 - r) / 5 * gem_pulse)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["orb_mid"], alpha),
                                  (gx, gy), r)
        pygame.draw.rect(surface, _NS_morgath.PALETTE["orb_darkest"],
                         (gx - 2, gy - 2, 5, 5))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["orb_dark"],
                         (gx - 1, gy - 2, 3, 4))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["orb_mid"],
                         (gx - 1, gy - 1, 3, 2))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["orb_light"],
                         (gx, gy - 1, 2, 1))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["orb_shine"],
                         (gx, gy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["white"], (gx, gy - 1, 1, 1))

        # Gold trim on torso edges
        pygame.draw.line(surface, _NS_morgath.PALETTE["gold_dark"],
                         (cx - 6, cy - 5), (cx + 6, cy - 5), 1)
        pygame.draw.line(surface, _NS_morgath.PALETTE["gold_mid"],
                         (cx - 5, cy - 5), (cx + 5, cy - 5), 1)

        # Shoulder pauldrons (ornate)
        for side in (-1, 1):
            sx = cx + side * 7
            # Big shoulder plate
            pygame.draw.rect(surface, _NS_morgath.PALETTE["shadow_deep"],
                             (sx - 3, cy - 6, 7, 6))
            pygame.draw.rect(surface, _NS_morgath.PALETTE["armor_darkest"],
                             (sx - 3, cy - 6, 6, 5))
            pygame.draw.rect(surface, _NS_morgath.PALETTE["armor_dark"],
                             (sx - 2, cy - 6, 4, 4))
            pygame.draw.rect(surface, _NS_morgath.PALETTE["armor_mid"],
                             (sx - 2, cy - 6, 3, 2))
            pygame.draw.rect(surface, _NS_morgath.PALETTE["armor_light"],
                             (sx - 1, cy - 6, 1, 1))
            # Gold trim
            pygame.draw.line(surface, _NS_morgath.PALETTE["gold_mid"],
                             (sx - 3, cy - 6), (sx + 3, cy - 6), 1)
            pygame.draw.rect(surface, _NS_morgath.PALETTE["gold_light"],
                             (sx - 2, cy - 6, 1, 1))
            # Small gem
            pygame.draw.rect(surface, _NS_morgath.PALETTE["orb_dark"],
                             (sx - 1, cy - 4, 2, 2))
            pygame.draw.rect(surface, _NS_morgath.PALETTE["orb_light"],
                             (sx, cy - 4, 1, 1))

    def _draw_mor_arm_back(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm."""
        base_x = cx - facing * 6
        base_y = cy

        if action == "attack":
            if attack_progress < 0.4:
                arm_angle = -0.3
            elif attack_progress < 0.7:
                t = (attack_progress - 0.4) / 0.3
                arm_angle = -0.3 + t * 0.5
            else:
                arm_angle = 0.2
        elif action == "walk":
            arm_angle = math.sin(phase * 2 + math.pi) * 0.25
        else:
            arm_angle = math.sin(phase * 0.7) * 0.1

        elbow_x = base_x - facing * int(3 + math.sin(arm_angle) * 2)
        elbow_y = base_y + int(4 - math.cos(arm_angle) * 1)
        hand_x = elbow_x - facing * int(2 + math.sin(arm_angle + 0.5) * 2)
        hand_y = elbow_y + int(5 - math.cos(arm_angle + 0.5) * 2)

        # Upper arm (robe sleeve)
        _NS_morgath._aaline(surface, _NS_morgath.PALETTE["shadow_deep"],
                            (base_x + 1, base_y + 1), (elbow_x + 1, elbow_y + 1), 5)
        _NS_morgath._aaline(surface, _NS_morgath.PALETTE["robe_darkest"],
                            (base_x, base_y), (elbow_x, elbow_y), 4)
        _NS_morgath._aaline(surface, _NS_morgath.PALETTE["robe_dark"],
                            (base_x, base_y), (elbow_x, elbow_y), 3)

        # Forearm (armored gauntlet)
        _NS_morgath._aaline(surface, _NS_morgath.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 4)
        _NS_morgath._aaline(surface, _NS_morgath.PALETTE["armor_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_morgath._aaline(surface, _NS_morgath.PALETTE["armor_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 2)

        # Small idle arc energy in hand
        if action == "idle":
            energy_pulse = math.sin(phase * 3) * 0.4 + 0.6
            _NS_morgath._aacircle(surface,
                                  (*_NS_morgath.PALETTE["arc_mid"],
                                   _NS_morgath._alpha(150 * energy_pulse)),
                                  (hand_x, hand_y), 3)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_light"],
                                  (hand_x, hand_y), 1)

    def _draw_mor_arm_front(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm - main casting hand."""
        base_x = cx + facing * 6
        base_y = cy

        if action == "attack":
            if attack_progress < 0.4:
                # Draw arm up/back for charge
                t = attack_progress / 0.4
                arm_angle = -0.5 - t * 0.5
            elif attack_progress < 0.7:
                # Thrust forward
                t = (attack_progress - 0.4) / 0.3
                arm_angle = -1.0 + t * 1.5
            else:
                # Recovery
                t = (attack_progress - 0.7) / 0.3
                arm_angle = 0.5 - t * 0.3
        elif action == "walk":
            arm_angle = math.sin(phase * 2) * 0.25
        else:
            arm_angle = math.sin(phase * 0.7 + 0.5) * 0.15 - 0.05

        elbow_x = base_x + facing * int(3 + math.cos(arm_angle) * 3)
        elbow_y = base_y + int(3 + math.sin(arm_angle) * 2)
        hand_x = elbow_x + facing * int(4 + math.cos(arm_angle + 0.3) * 3)
        hand_y = elbow_y + int(3 + math.sin(arm_angle + 0.3) * 3)

        # Upper arm (robe sleeve)
        _NS_morgath._aaline(surface, _NS_morgath.PALETTE["shadow_deep"],
                            (base_x + 1, base_y + 1), (elbow_x + 1, elbow_y + 1), 5)
        _NS_morgath._aaline(surface, _NS_morgath.PALETTE["robe_darkest"],
                            (base_x, base_y), (elbow_x, elbow_y), 4)
        _NS_morgath._aaline(surface, _NS_morgath.PALETTE["robe_dark"],
                            (base_x, base_y), (elbow_x, elbow_y), 3)
        _NS_morgath._aaline(surface, _NS_morgath.PALETTE["robe_mid"],
                            (base_x, base_y - 1), (elbow_x, elbow_y - 1), 1)

        # Forearm (armored gauntlet with gold trim)
        _NS_morgath._aaline(surface, _NS_morgath.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 4)
        _NS_morgath._aaline(surface, _NS_morgath.PALETTE["armor_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_morgath._aaline(surface, _NS_morgath.PALETTE["armor_mid"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 2)
        _NS_morgath._aaline(surface, _NS_morgath.PALETTE["armor_light"],
                            (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)

        # Gauntlet detail
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["gold_mid"],
                              (hand_x, hand_y), 2)
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["gold_light"],
                              (hand_x - facing, hand_y), 1)

        # Casting energy in hand (idle: small orb, attack: bigger charge)
        if action == "attack" and attack_progress < 0.55:
            # Charging orb
            t = attack_progress / 0.55
            cr = int(3 + t * 6)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_morgath._alpha(220 * (cr + 4 - r) / (cr + 4))
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_darkest"], alpha),
                                      (hand_x, hand_y), r)
            for r in range(cr, 0, -1):
                alpha = _NS_morgath._alpha(240 * (cr - r + 1) / cr)
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_mid"], alpha),
                                      (hand_x, hand_y), r)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_light"],
                                  (hand_x, hand_y), max(1, cr - 2))
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_shine"],
                                  (hand_x, hand_y), max(1, cr - 4))
            pygame.draw.rect(surface, _NS_morgath.PALETTE["white"],
                             (hand_x, hand_y, 1, 1))

            # Sparks
            for i in range(4):
                angle = phase * 5 + i * math.pi / 2
                sx = hand_x + int(math.cos(angle) * (cr + 3))
                sy = hand_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_morgath.PALETTE["arc_hot"],
                                 (sx, sy, 1, 1))

            # Small lightning arcs to arm
            if attack_progress > 0.15:
                for i in range(2):
                    end_x = hand_x + int(math.sin(phase * 8 + i) * 4)
                    end_y = hand_y + int(math.cos(phase * 8 + i) * 4)
                    _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_hot"],
                                             (hand_x, hand_y),
                                             (elbow_x, elbow_y),
                                             jitter=2, segments=4, width=1)
        elif action == "idle" or action == "walk":
            # Ambient small orb
            orb_pulse = math.sin(phase * 3) * 0.4 + 0.6
            for r in range(4, 0, -1):
                alpha = _NS_morgath._alpha(180 * (4 - r) / 4 * orb_pulse)
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_mid"], alpha),
                                      (hand_x, hand_y), r)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_light"],
                                  (hand_x, hand_y), 2)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_shine"],
                                  (hand_x, hand_y), 1)

            # Occasional arc
            arc_frame = int(phase * 4) % 8
            if arc_frame < 2:
                arc_end_x = hand_x + int(math.sin(phase * 6) * 5)
                arc_end_y = hand_y - 3 - int(math.cos(phase * 6) * 2)
                _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_light"],
                                         (hand_x, hand_y),
                                         (arc_end_x, arc_end_y),
                                         jitter=2, segments=4, width=1)

    def _draw_mor_head(surface, cx, cy, facing, phase, action):
        """Hood + big glowing crystal orb helm."""
        # Hood (dark cowl behind orb)
        hood_pts = [
            (cx - 7, cy + 4),
            (cx - 8, cy - 2),
            (cx - 6, cy - 8),
            (cx - 2, cy - 10),
            (cx + 2, cy - 10),
            (cx + 6, cy - 8),
            (cx + 8, cy - 2),
            (cx + 7, cy + 4),
        ]
        _NS_morgath._poly(surface, _NS_morgath.PALETTE["shadow_deep"],
                          [(px + 1, py + 1) for px, py in hood_pts])
        _NS_morgath._poly(surface, _NS_morgath.PALETTE["robe_darkest"], hood_pts)
        _NS_morgath._poly(surface, _NS_morgath.PALETTE["robe_dark"], [
            (cx - 6, cy + 3),
            (cx - 7, cy - 2),
            (cx - 5, cy - 7),
            (cx - 1, cy - 9),
            (cx + 1, cy - 9),
            (cx + 5, cy - 7),
            (cx + 7, cy - 2),
            (cx + 6, cy + 3),
        ])

        # Hood inner shadow (dark inside)
        _NS_morgath._poly(surface, _NS_morgath.PALETTE["shadow_deep"], [
            (cx - 5, cy + 2),
            (cx - 6, cy - 2),
            (cx - 4, cy - 6),
            (cx + 4, cy - 6),
            (cx + 6, cy - 2),
            (cx + 5, cy + 2),
        ])

        # Hood highlight edge
        pygame.draw.line(surface, _NS_morgath.PALETTE["robe_edge"],
                         (cx - 6 * facing, cy - 7),
                         (cx - 7 * facing, cy - 1), 1)

        # Gold trim on hood edge
        pygame.draw.line(surface, _NS_morgath.PALETTE["gold_dark"],
                         (cx - 5, cy - 7), (cx + 5, cy - 7), 1)
        pygame.draw.line(surface, _NS_morgath.PALETTE["gold_mid"],
                         (cx - 3, cy - 7), (cx + 3, cy - 7), 1)

        # CRYSTAL ORB HELM (huge glowing sphere as head)
        _NS_morgath._draw_crystal_orb(surface, cx, cy - 4, phase, action)

        # Chin guard piece
        pygame.draw.rect(surface, _NS_morgath.PALETTE["armor_darkest"],
                         (cx - 3, cy + 4, 7, 3))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["armor_dark"],
                         (cx - 3, cy + 4, 6, 2))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["armor_mid"],
                         (cx - 2, cy + 4, 4, 1))
        # Gold trim
        pygame.draw.line(surface, _NS_morgath.PALETTE["gold_mid"],
                         (cx - 3, cy + 6), (cx + 3, cy + 6), 1)

    def _draw_crystal_orb(surface, cx, cy, phase, action):
        """Big glowing crystal orb (the 'face' of Morgath)."""
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7

        # Outer glow halo
        for r in range(10, 4, -1):
            alpha = _NS_morgath._alpha(120 * (10 - r) / 6 * pulse)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["orb_mid"], alpha),
                                  (cx, cy), r)

        # Main orb sphere
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["shadow_deep"], (cx + 1, cy + 1), 6)
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["orb_darkest"], (cx, cy), 6)
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["orb_dark"], (cx, cy), 5)
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["orb_mid"], (cx, cy), 4)
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["orb_light"], (cx - 1, cy - 1), 3)
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["orb_hot"], (cx - 1, cy - 1), 2)
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["orb_shine"], (cx - 1, cy - 2), 1)
        pygame.draw.rect(surface, _NS_morgath.PALETTE["white"], (cx - 1, cy - 2, 1, 1))

        # Rim dark (bottom-right shadow)
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["orb_darkest"],
                              (cx + 2, cy + 2), 3, 1)

        # Metal collar under orb (holds it)
        pygame.draw.rect(surface, _NS_morgath.PALETTE["armor_darkest"],
                         (cx - 4, cy + 5, 9, 2))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["armor_dark"],
                         (cx - 4, cy + 5, 8, 1))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["gold_mid"],
                         (cx - 3, cy + 5, 6, 1))

        # Small electric arcs around orb
        arc_frame = int(phase * 6) % 6
        if arc_frame < 3:
            for i in range(3):
                angle = phase * 4 + i * math.pi * 2 / 3
                r_arc = 8
                arc_end_x = cx + int(math.cos(angle) * r_arc)
                arc_end_y = cy + int(math.sin(angle) * r_arc)
                pygame.draw.rect(surface, _NS_morgath.PALETTE["arc_hot"],
                                 (arc_end_x, arc_end_y, 1, 1))
                pygame.draw.rect(surface, _NS_morgath.PALETTE["arc_shine"],
                                 (arc_end_x, arc_end_y, 1, 1))

    # ============================================================
    # LIGHTNING PROJECTILE (basic attack)
    # ============================================================
    def _draw_lightning_projectile(surface, boss, x, y, progress):
        """Lightning bolt projectile from hand."""
        if progress < 0.55:
            return

        # ═══ KOMPENSASI SCALE HERO ═══
        # Hero dirender ke canvas lalu di-scale (heroes/__init__.py).
        # Supaya beam terlihat SAMA PERSIS seperti saat jadi mini boss
        # (tebal penuh, kepala besar, jitter & impact sama), semua
        # ukuran beam digambar 1/_render_scale kali lebih besar di
        # canvas, sehingga setelah di-scale hasilnya = ukuran asli
        # boss. Boss asli digambar langsung di layar: _render_scale=1,
        # jadi fungsi ini berperilaku persis seperti sebelumnya.
        inv = 1.0 / max(0.3, float(getattr(boss, "_render_scale", 1.0) or 1.0))

        def W(w):
            # ceil: garis 1px tetap terang setelah smoothscale
            # (round membuatnya 1px lalu blur jadi redup).
            return max(1, int(math.ceil(w * inv)))

        def _A(a):
            # Alpha dinaikkan sebesar inv: smoothscale menurunkan
            # cakupan alpha ~scale kali, jadi ini mengembalikan
            # kecerahan beam ke level asli boss setelah di-blit.
            return _NS_morgath._alpha(a * min(1.4, inv))

        def R(r):
            return max(1, int(round(r * inv)))

        # Arah & target terkunci saat serangan dimulai (lihat
        # _update_mor_attack_anim) supaya beam tidak patah arah /
        # pindah tujuan di tengah cast. Fallback ke live kalau
        # state kunci tidak ada.
        facing = getattr(boss, "_mor_attack_dir", None)
        if facing is None:
            facing = boss.direction
        if hasattr(boss, "_mor_attack_target"):
            # Offset tersimpan dalam ruang DUNIA; konversi ke ruang
            # render saat ini (canvas ter-scale atau layar skala 1.0).
            scl = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            ox, oy = boss._mor_attack_target
            tx, ty = int(x + ox / scl), int(y + oy / scl)
        else:
            tx, ty = _NS_morgath._target_position(boss, x, y)

        # Launch from front hand position (18px = ukuran asli boss)
        start_x = x + facing * int(round(18 * inv))
        start_y = y - 2

        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Jagged lightning beam from start to bolt head
        segments = 8
        prev = (start_x, start_y)
        for i in range(1, segments + 1):
            seg_t = i / segments
            px = int(start_x + (bx - start_x) * seg_t)
            py = int(start_y + (by - start_y) * seg_t)
            if i < segments:
                # Add jitter perpendicular to path
                dx = bx - start_x
                dy = by - start_y
                length = max(1, math.hypot(dx, dy))
                perp_x = -dy / length
                perp_y = dx / length
                jitter = math.sin(seg_t * 15 + progress * 20) * (4 * inv)
                px += int(perp_x * jitter)
                py += int(perp_y * jitter)

            # Beam colors (layered)
            alpha = _A(220 * (1 - seg_t * 0.3))
            pygame.draw.line(surface, (*_NS_morgath.PALETTE["arc_darkest"], alpha),
                             prev, (px, py), W(5))
            pygame.draw.line(surface, (*_NS_morgath.PALETTE["arc_dark"], alpha),
                             prev, (px, py), W(4))
            pygame.draw.line(surface, (*_NS_morgath.PALETTE["arc_mid"], alpha),
                             prev, (px, py), W(3))
            pygame.draw.line(surface, (*_NS_morgath.PALETTE["arc_light"], alpha),
                             prev, (px, py), W(2))
            pygame.draw.line(surface, (*_NS_morgath.PALETTE["arc_hot"], alpha),
                             prev, (px, py), W(1))
            prev = (px, py)

        # Bolt head (bright ball)
        for r in range(10, 3, -1):
            alpha = _A(100 * (10 - r) / 10)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_light"], alpha),
                                  (bx, by), R(r))
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_darkest"], (bx, by), R(6))
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_dark"], (bx, by), R(4))
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_light"], (bx, by), R(3))
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_hot"], (bx, by), R(2))
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_shine"], (bx, by), R(1))
        pygame.draw.rect(surface, _NS_morgath.PALETTE["white"], (bx, by, W(1), W(1)))

        # Radiating jagged forks near head
        for i in range(4):
            angle = i * math.pi / 2 + progress * 3
            fork_end_x = bx + int(math.cos(angle) * 8 * inv)
            fork_end_y = by + int(math.sin(angle) * 8 * inv)
            _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_hot"],
                                     (bx, by), (fork_end_x, fork_end_y),
                                     jitter=2 * inv, segments=3, width=W(1))

        # Impact
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(10 + st * 24)
            alpha = _A(240 * (1 - st))
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_darkest"], alpha),
                                  (tx, ty), R(radius + 3), W(3))
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_dark"], alpha),
                                  (tx, ty), R(radius), W(3))
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_mid"], alpha),
                                  (tx, ty), R(max(1, radius - 5)), W(2))
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_light"], alpha),
                                  (tx, ty), R(max(1, radius - 10)), W(1))

            # Lightning tendrils outward
            for i in range(8):
                angle = i * math.pi / 4
                end_x = tx + int(math.cos(angle) * radius * inv)
                end_y = ty + int(math.sin(angle) * radius * 0.7 * inv)
                _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_shine"],
                                         (tx, ty), (end_x, end_y),
                                         jitter=3 * inv, segments=4, width=W(1))
                pygame.draw.rect(surface, (*_NS_morgath.PALETTE["white"], alpha),
                                 (end_x, end_y, W(2), W(2)))

    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((80, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 18)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 10 - radius, 60 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (2, 5, 12, 180), (5, 5, 70, 10))
        surface.blit(shadow, (x - 40, y - 10))

    def _draw_arc_aura(surface, x, y, phase):
        """Blue electric aura behind boss."""
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75

        aura = pygame.Surface((160, 140), pygame.SRCALPHA)
        for radius in range(70, 5, -4):
            alpha = _NS_morgath._alpha((70 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_morgath._aacircle(aura, (*_NS_morgath.PALETTE["arc_darkest"], alpha),
                                      (80, 70), radius)
        for radius in range(45, 5, -3):
            alpha = _NS_morgath._alpha((45 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_morgath._aacircle(aura, (*_NS_morgath.PALETTE["arc_dark"], alpha),
                                      (80, 70), radius)
        surface.blit(aura, (x - 80, y - 70))

        # Floating electric sparkles
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            r = 32 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * r)
            sy = y - 5 + int(math.sin(angle) * r * 0.5)
            alpha = _NS_morgath._alpha(220 + math.sin(phase * 4 + i) * 35)
            pygame.draw.rect(surface, _NS_morgath.PALETTE["arc_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_morgath.PALETTE["arc_hot"], (sx, sy, 1, 1))

        # Occasional lightning arc between random sparkles
        arc_frame = int(phase * 3) % 8
        if arc_frame < 2:
            for k in range(2):
                a1 = phase * 0.4 + k * math.pi / 6
                a2 = phase * 0.4 + (k + 3) * math.pi / 6
                r = 32
                p1 = (x + int(math.cos(a1) * r),
                      y - 5 + int(math.sin(a1) * r * 0.5))
                p2 = (x + int(math.cos(a2) * r),
                      y - 5 + int(math.sin(a2) * r * 0.5))
                _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_light"],
                                         p1, p2, jitter=3, segments=5, width=1)

    def _draw_ground_rune(surface, x, y, phase, skill):
        """Blue magic rune circle."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_morgath.PALETTE["arc_darkest"], 200),
                            (5, 14, 120, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_morgath.PALETTE["arc_dark"], 220),
                            (12, 16, 106, 16), 1)
        pygame.draw.ellipse(ring, (*_NS_morgath.PALETTE["arc_mid"], 180),
                            (25, 18, 80, 12), 1)

        # Rune spokes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 65 + int(math.cos(angle) * 40)
            y1 = 23 + int(math.sin(angle) * 8)
            x2 = 65 + int(math.cos(angle) * 58)
            y2 = 23 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_morgath.PALETTE["arc_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_morgath.PALETTE["arc_hot"],
                                       _NS_morgath._alpha(160 * pulse)),
                                (10, 10, 110, 28), 1)
        surface.blit(ring, (x - 65, y - 22))

    # ============================================================
    # SKILL Q: SPARK WRAITH (homing electric orb)
    # ============================================================
    def _draw_sparkwraith_ground(surface, boss, x, y, timer, phase):
        """Launch rune."""
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.25:
            t = progress / 0.25
            r = int(22 * t)
            alpha = _NS_morgath._alpha(200 * t)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_mid"], alpha),
                                  (x, y + 40), r, 2)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_light"], alpha),
                                  (x, y + 40), max(1, r - 3), 1)

    def _draw_sparkwraith_foreground(surface, boss, x, y, timer, phase):
        """Sparking electric orb that flies to target."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morgath._target_position(boss, x, y)

        if progress < 0.3:
            # Charge in hand
            t = progress / 0.3
            charge_x = x + facing * 18
            charge_y = y - 2
            cr = int(4 + t * 6)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_morgath._alpha(220 * (cr + 5 - r) / (cr + 5))
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_darkest"], alpha),
                                      (charge_x, charge_y), r)
            for r in range(cr + 2, 0, -1):
                alpha = _NS_morgath._alpha(240 * (cr + 2 - r) / (cr + 2))
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_dark"], alpha),
                                      (charge_x, charge_y), r)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_mid"],
                                  (charge_x, charge_y), cr - 2)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_light"],
                                  (charge_x, charge_y), max(1, cr - 4))
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_shine"],
                                  (charge_x, charge_y), max(1, cr - 6))

            # Sparks
            for i in range(6):
                angle = phase * 5 + i * math.pi / 3
                sx = charge_x + int(math.cos(angle) * (cr + 3))
                sy = charge_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_morgath.PALETTE["arc_hot"], (sx, sy, 1, 1))

            # Jagged arcs from orb
            for i in range(3):
                ea_x = charge_x + int(math.cos(phase * 6 + i) * (cr + 5))
                ea_y = charge_y + int(math.sin(phase * 6 + i) * (cr + 5))
                _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_light"],
                                         (charge_x, charge_y), (ea_x, ea_y),
                                         jitter=2, segments=3, width=1)
        else:
            # Orb travels toward target (curved wraith)
            t = (progress - 0.3) / 0.7
            start_x = x + facing * 22
            start_y = y - 2

            # Slight arc trajectory
            mid_x = (start_x + tx) / 2
            mid_y = min(start_y, ty) - 30
            bx = int((1 - t) ** 2 * start_x + 2 * (1 - t) * t * mid_x + t ** 2 * tx)
            by = int((1 - t) ** 2 * start_y + 2 * (1 - t) * t * mid_y + t ** 2 * ty)

            # Trail behind
            for i in range(8):
                trail_t = max(0.0, t - i * 0.06)
                px = int((1 - trail_t) ** 2 * start_x + 2 * (1 - trail_t) * trail_t * mid_x
                         + trail_t ** 2 * tx)
                py = int((1 - trail_t) ** 2 * start_y + 2 * (1 - trail_t) * trail_t * mid_y
                         + trail_t ** 2 * ty)
                alpha = _NS_morgath._alpha(240 - i * 28)
                size = max(1, 8 - i)
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_darkest"], alpha),
                                      (px, py), size)
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_dark"], alpha),
                                      (px, py), max(1, size - 1))
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_mid"], alpha),
                                      (px, py), max(1, size - 2))
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_light"], alpha),
                                      (px, py), max(1, size - 3))

            # Bright orb head with electric aura
            for r in range(14, 4, -2):
                alpha = _NS_morgath._alpha(90 * (14 - r) / 14)
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_light"], alpha),
                                      (bx, by), r)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_darkest"], (bx, by), 9)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_dark"], (bx, by), 7)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_mid"], (bx, by), 5)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_light"], (bx, by), 3)
            _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["arc_shine"], (bx, by), 2)
            pygame.draw.rect(surface, _NS_morgath.PALETTE["white"], (bx, by, 1, 1))

            # Electric tendrils around orb
            for i in range(5):
                angle = phase * 6 + i * math.pi * 2 / 5
                tend_end_x = bx + int(math.cos(angle) * 10)
                tend_end_y = by + int(math.sin(angle) * 10)
                _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_hot"],
                                         (bx, by), (tend_end_x, tend_end_y),
                                         jitter=3, segments=3, width=1)

            # Impact
            if t > 0.88:
                st = (t - 0.88) / 0.12
                radius = int(12 + st * 26)
                alpha = _NS_morgath._alpha(240 * (1 - st))
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_darkest"], alpha),
                                      (tx, ty), radius + 4, 3)
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_dark"], alpha),
                                      (tx, ty), radius, 3)
                _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_light"], alpha),
                                      (tx, ty), max(1, radius - 8), 2)

                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_shine"],
                                             (tx, ty), (ex, ey),
                                             jitter=3, segments=4, width=1)

    # ============================================================
    # SKILL W: FLUX (purple debuff aura on target)
    # ============================================================
    def _draw_flux_ground(surface, boss, x, y, timer, phase):
        """Purple pool at target."""
        tx, ty = _NS_morgath._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(38 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_morgath.PALETTE["flux_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_morgath.PALETTE["flux_dark"], 180),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_morgath.PALETTE["flux_mid"], 140),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))

    def _draw_flux_foreground(surface, boss, x, y, timer, phase):
        """Rising purple energy tendrils around target."""
        tx, ty = _NS_morgath._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(38 * min(1.0, progress * 3))

        if r < 5:
            return

        # Rising purple tendrils/wisps
        for i in range(8):
            wisp_t = (phase * 0.7 + i * 0.15) % 1.0
            angle = i * math.pi / 4 + phase * 0.3
            wx = tx + int(math.cos(angle) * r * 0.6)
            wy_base = ty + int(math.sin(angle) * r * 0.3)
            wy = wy_base - int(wisp_t * 30)
            alpha = _NS_morgath._alpha(230 * (1 - wisp_t))

            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["flux_dark"], alpha),
                                  (wx, wy), 4)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["flux_mid"], alpha),
                                  (wx, wy - 1), 3)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["flux_light"], alpha),
                                  (wx, wy - 1), 2)
            pygame.draw.rect(surface, (*_NS_morgath.PALETTE["flux_hot"], alpha),
                             (wx, wy - 1, 1, 1))

        # Central bubbling core
        core_pulse = math.sin(phase * 3) * 0.4 + 0.6
        for cr in range(6, 0, -1):
            alpha = _NS_morgath._alpha(200 * (6 - cr) / 6 * core_pulse)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["flux_mid"], alpha),
                                  (tx, ty), cr)
        _NS_morgath._aacircle(surface, _NS_morgath.PALETTE["flux_light"], (tx, ty), 2)

        # Sparkles on ground
        for i in range(14):
            angle = i * math.pi * 2 / 14 + phase * 0.4
            sp_r = int(r * (0.5 + (i % 3) * 0.2))
            sx = tx + int(math.cos(angle) * sp_r)
            sy = ty + int(math.sin(angle) * sp_r * 0.4)
            pygame.draw.rect(surface, _NS_morgath.PALETTE["flux_light"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_morgath.PALETTE["flux_hot"], (sx, sy, 1, 1))

    # ============================================================
    # SKILL E: MAGNETIC FIELD (dome shield)
    # ============================================================
    def _draw_magneticfield_ground(surface, boss, x, y, timer, phase):
        """Ground ring under dome."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for i in range(3):
            r = int(48 + i * 4 + math.sin(phase * 2) * 2)
            alpha = _NS_morgath._alpha(220 * pulse - i * 50)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_mid"], alpha),
                                  (x, y + 42), r, 2)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["arc_light"], alpha),
                                  (x, y + 42), r, 1)

    def _draw_magneticfield_foreground(surface, boss, x, y, timer, phase):
        """Big blue dome shield over boss."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Dome dimensions
        breath = math.sin(phase * 2) * 2
        r = 52 + int(breath)

        # Draw dome (semi-circle top-half)
        dome_surf = pygame.Surface((r * 2 + 30, r + 30), pygame.SRCALPHA)
        center = (r + 15, r + 15)

        # Multi-ring dome
        for layer_i, (thickness, alpha_val) in enumerate([
            (4, 100), (3, 140), (2, 190), (1, 240),
        ]):
            # Draw arc (top half)
            arc_rect = pygame.Rect(center[0] - r + layer_i, center[1] - r + layer_i,
                                   (r - layer_i) * 2, (r - layer_i) * 2)
            pygame.draw.arc(dome_surf, (*_NS_morgath.PALETTE["arc_dark"], alpha_val),
                            arc_rect, 0, math.pi, thickness)
            pygame.draw.arc(dome_surf, (*_NS_morgath.PALETTE["arc_mid"], alpha_val),
                            arc_rect, 0, math.pi, max(1, thickness - 1))
            pygame.draw.arc(dome_surf, (*_NS_morgath.PALETTE["arc_light"], alpha_val),
                            arc_rect, 0, math.pi, max(1, thickness - 2))

        # Hex/grid pattern inside dome
        for h_row in range(4):
            for h_col in range(-3, 4):
                grid_x = center[0] + h_col * 12 + (h_row % 2) * 6
                grid_y = center[1] - h_row * 10
                dist_from_center = math.hypot(grid_x - center[0], grid_y - center[1])
                if dist_from_center < r - 5:
                    alpha = _NS_morgath._alpha(180 * (1 - dist_from_center / r))
                    pygame.draw.rect(dome_surf,
                                     (*_NS_morgath.PALETTE["arc_mid"], alpha),
                                     (grid_x - 1, grid_y - 1, 3, 3), 1)

        # Rotating electric arcs on dome surface
        for i in range(6):
            angle = phase * 1.5 + i * math.pi / 3
            arc_angle = math.pi + angle  # constrain to top half
            arc_angle = math.pi * (0.1 + (i / 6) * 0.8)
            ax = center[0] + int(math.cos(math.pi + arc_angle) * r)
            ay = center[1] + int(math.sin(math.pi + arc_angle) * r)
            pygame.draw.rect(dome_surf, (*_NS_morgath.PALETTE["arc_hot"], 240),
                             (ax, ay, 2, 2))
            pygame.draw.rect(dome_surf, (*_NS_morgath.PALETTE["arc_shine"], 255),
                             (ax, ay, 1, 1))

        surface.blit(dome_surf, (x - r - 15, y - r - 15 + 10))

        # Random lightning arcs across dome interior
        arc_frame = int(phase * 4) % 5
        if arc_frame < 2:
            for k in range(2):
                a1 = phase * 2 + k * 1.7
                a2 = phase * 2 + k * 1.7 + 1.5
                arc_angle1 = math.pi * (0.15 + ((math.sin(a1) + 1) / 2) * 0.7)
                arc_angle2 = math.pi * (0.15 + ((math.sin(a2) + 1) / 2) * 0.7)
                p1 = (x + int(math.cos(math.pi + arc_angle1) * r),
                      y + 10 + int(math.sin(math.pi + arc_angle1) * r))
                p2 = (x + int(math.cos(math.pi + arc_angle2) * r),
                      y + 10 + int(math.sin(math.pi + arc_angle2) * r))
                _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_hot"],
                                         p1, p2, jitter=4, segments=6, width=1)

    # ============================================================
    # SKILL R: TEMPEST DOUBLE (spawn clone + lightning)
    # ============================================================
    def _draw_tempest_ground(surface, boss, x, y, timer, phase):
        """Twin rune circles."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        # Original boss ring
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        r = int(25 + math.sin(phase * 2) * 2)
        for i in range(2):
            alpha = _NS_morgath._alpha(200 * pulse - i * 60)
            _NS_morgath._aacircle(surface, (*_NS_morgath.PALETTE["flux_mid"], alpha),
                                  (x, y + 42), r + i * 2, 2)

        # Clone spawn ring (offset)
        if progress > 0.2:
            clone_offset = -facing * 40
            clone_alpha_mult = min(1.0, (progress - 0.2) / 0.2)
            for i in range(2):
                alpha = _NS_morgath._alpha(200 * pulse * clone_alpha_mult - i * 60)
                _NS_morgath._aacircle(surface,
                                      (*_NS_morgath.PALETTE["flux_mid"], alpha),
                                      (x + clone_offset, y + 42), r + i * 2, 2)

    def _draw_tempest_clone(surface, boss, x, y, timer, phase):
        """Ghostly duplicate of boss."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        if progress < 0.2:
            return

        # Clone spawn animation
        spawn_t = min(1.0, (progress - 0.2) / 0.3)
        alpha_val = int(180 * spawn_t)

        clone_offset = -facing * 40
        clone_x = x + clone_offset

        # Draw clone body to surface with alpha
        clone_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
        # Use idle pose for clone
        _NS_morgath._draw_mor_body(clone_surf, 60, 60, facing, phase, "idle")
        clone_surf.set_alpha(alpha_val)

        # Tint clone slightly blue
        tint = pygame.Surface((120, 120), pygame.SRCALPHA)
        tint.fill((80, 130, 220, 60))
        clone_surf.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        surface.blit(clone_surf, (clone_x - 60, y - 60))

        # Electric arcs between clone and original
        arc_frame = int(phase * 6) % 4
        if arc_frame < 2:
            _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_hot"],
                                     (x, y - 10), (clone_x, y - 10),
                                     jitter=6, segments=8, width=2)
            _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_shine"],
                                     (x, y - 10), (clone_x, y - 10),
                                     jitter=5, segments=8, width=1)

    def _draw_tempest_foreground(surface, boss, x, y, timer, phase):
        """Lightning storm burst FX."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        if progress < 0.2:
            # Charge phase - purple ground swirl
            t = progress / 0.2
            for arm in range(3):
                for step in range(15):
                    s_t = step / 15
                    spiral_angle = phase * 3 + arm * math.pi * 2 / 3 + s_t * math.pi * 3
                    s_r = int(30 * (1 - s_t) * t)
                    sx = x + int(math.cos(spiral_angle) * s_r)
                    sy = y + 30 + int(math.sin(spiral_angle) * s_r * 0.4)
                    alpha = _NS_morgath._alpha(200 * (1 - s_t) * t)
                    pygame.draw.rect(surface,
                                     (*_NS_morgath.PALETTE["flux_light"], alpha),
                                     (sx, sy, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_morgath.PALETTE["flux_hot"], alpha),
                                     (sx, sy, 1, 1))

        elif progress < 0.5:
            # Burst
            t = (progress - 0.2) / 0.3
            intensity = math.sin(t * math.pi)
            burst_r = int(30 + t * 40)

            # Radial lightning bolts from boss
            for i in range(12):
                angle = i * math.pi / 6 + phase * 0.5
                end_x = x + int(math.cos(angle) * burst_r)
                end_y = y - 10 + int(math.sin(angle) * burst_r * 0.8)
                alpha = _NS_morgath._alpha(240 * intensity)
                _NS_morgath._jagged_line(surface,
                                         _NS_morgath.PALETTE["arc_darkest"],
                                         (x, y - 10), (end_x, end_y),
                                         jitter=4, segments=6, width=4)
                _NS_morgath._jagged_line(surface,
                                         _NS_morgath.PALETTE["arc_mid"],
                                         (x, y - 10), (end_x, end_y),
                                         jitter=4, segments=6, width=2)
                _NS_morgath._jagged_line(surface,
                                         _NS_morgath.PALETTE["arc_shine"],
                                         (x, y - 10), (end_x, end_y),
                                         jitter=3, segments=6, width=1)
                pygame.draw.rect(surface, (*_NS_morgath.PALETTE["white"], alpha),
                                 (end_x, end_y, 2, 2))

            # Bright core flash
            for r in range(15, 0, -1):
                alpha = _NS_morgath._alpha(220 * intensity * (15 - r) / 15)
                _NS_morgath._aacircle(surface,
                                      (*_NS_morgath.PALETTE["arc_light"], alpha),
                                      (x, y - 10), r)
        else:
            # Aftermath - lingering sparks
            t = (progress - 0.5) / 0.5
            for i in range(16):
                rise_t = (phase * 0.7 + i * 0.06) % 1.0
                angle = i * math.pi * 2 / 16 + phase * 0.3
                r_sp = 35 + int(math.sin(phase + i) * 8)
                rx = x + int(math.cos(angle) * r_sp)
                ry = y + 10 + int(math.sin(angle) * r_sp * 0.4) - int(rise_t * 20)
                alpha = _NS_morgath._alpha(220 * (1 - t) * (1 - rise_t * 0.5))
                if alpha > 0:
                    pygame.draw.rect(surface,
                                     (*_NS_morgath.PALETTE["arc_light"], alpha),
                                     (rx, ry, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_morgath.PALETTE["arc_shine"], alpha),
                                     (rx, ry, 1, 1))

            # Occasional lingering arcs
            arc_frame = int(phase * 4) % 6
            if arc_frame < 2:
                clone_offset = -facing * 40
                _NS_morgath._jagged_line(surface, _NS_morgath.PALETTE["arc_hot"],
                                         (x, y - 10),
                                         (x + clone_offset, y - 10),
                                         jitter=5, segments=6, width=1)

# ====================================================================
# DRAKAR (AXE) - Mini Boss HD (Redesigned)
# ====================================================================
import math
import pygame


class _NS_drakar:
    """Namespace drakar - Axe berserker mini boss (HD scale)."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin (red - main body color)
        "skin_darkest": (55, 15, 15),
        "skin_dark": (110, 30, 25),
        "skin_mid": (170, 55, 40),
        "skin_light": (215, 95, 70),
        "skin_shine": (240, 145, 110),

        # Hair / beard (black-dark)
        "hair_darkest": (8, 6, 10),
        "hair_dark": (28, 22, 28),
        "hair_mid": (55, 45, 50),
        "hair_light": (95, 80, 85),

        # Leather (dark brown)
        "leather_darkest": (22, 12, 6),
        "leather_dark": (55, 32, 18),
        "leather_mid": (95, 62, 38),
        "leather_light": (140, 100, 65),

        # Metal armor (dark iron)
        "armor_darkest": (15, 12, 15),
        "armor_dark": (42, 38, 45),
        "armor_mid": (85, 78, 88),
        "armor_light": (140, 132, 142),
        "armor_shine": (200, 195, 205),

        # Axe blade (steel)
        "blade_darkest": (18, 15, 22),
        "blade_dark": (55, 50, 62),
        "blade_mid": (115, 108, 125),
        "blade_light": (185, 178, 195),
        "blade_shine": (240, 235, 250),

        # Blood (bright red)
        "blood_darkest": (45, 5, 10),
        "blood_dark": (110, 15, 20),
        "blood_mid": (185, 25, 35),
        "blood_light": (235, 55, 60),
        "blood_hot": (255, 100, 90),
        "blood_shine": (255, 180, 160),

        # Rage aura (crimson glow)
        "rage_darkest": (60, 10, 5),
        "rage_dark": (140, 30, 15),
        "rage_mid": (220, 55, 30),
        "rage_light": (255, 110, 60),
        "rage_hot": (255, 180, 120),

        # Eye glow (yellow-red berserker)
        "eye_dark": (80, 30, 10),
        "eye_mid": (200, 90, 20),
        "eye_light": (255, 180, 60),
        "eye_glow": (255, 240, 180),

        # Ground rune
        "rune_dark": (30, 8, 10),
        "rune_mid": (140, 30, 30),
        "rune_light": (230, 70, 60),

        "shadow": (0, 0, 0),
        "shadow_deep": (3, 1, 2),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _rgba(color, alpha):
        """Safely build rgba tuple."""
        r, g, b = color[0], color[1], color[2]
        return (max(0, min(255, int(r))),
                max(0, min(255, int(g))),
                max(0, min(255, int(b))),
                max(0, min(255, int(alpha))))

    def _aacircle(surface, color, center, radius, width=0):
        if len(color) == 4:
            color = (max(0, min(255, int(color[0]))),
                     max(0, min(255, int(color[1]))),
                     max(0, min(255, int(color[2]))),
                     max(0, min(255, int(color[3]))))
        else:
            color = _NS_drakar._clamp(color)
        if _NS_drakar.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        if len(color) == 4:
            color = (max(0, min(255, int(color[0]))),
                     max(0, min(255, int(color[1]))),
                     max(0, min(255, int(color[2]))),
                     max(0, min(255, int(color[3]))))
        else:
            color = _NS_drakar._clamp(color)
        if _NS_drakar.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_drakar._clamp(color), points)

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

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_drakar(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_drakar._detect_moving(boss)
        _NS_drakar._update_drk_attack_anim(boss)
        attacking = (
            getattr(boss, "_drk_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Bigger ambient behind (Vhorethzir-scale)
        _NS_drakar._draw_rage_aura(surface, x, y, pulse)
        _NS_drakar._draw_ground_ring(surface, x, y + 76, pulse, active_skill)

        # Skill ground FX
        if active_skill == "q":
            _NS_drakar._draw_battlehunger_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_drakar._draw_counterhelix_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_drakar._draw_berserkerscall_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_drakar._draw_cullingblade_ground(surface, boss, x, y, skill_timer, pulse)

        # Body
        if active_skill == "w":
            _NS_drakar._draw_drk_helix(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_drakar._draw_drk_attack(surface, boss, x, y)
        elif moving:
            _NS_drakar._draw_drk_walk(surface, boss, x, y)
        else:
            _NS_drakar._draw_drk_idle(surface, boss, x, y)

        # Foreground FX
        if active_skill == "q":
            _NS_drakar._draw_battlehunger_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_drakar._draw_berserkerscall_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_drakar._draw_cullingblade_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_drk_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_drk_previous_timer", 0))
        active = bool(getattr(boss, "_drk_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._drk_attack_active = True
            boss._drk_attack_frame = 0
            # Kunci arah swing saat serangan dimulai. Sebelumnya
            # swing pakai direction LIVE: hero (versi summon) yang
            # kena hit lalu retreat/chase berbalik tiap frame,
            # sehingga lunge, axe trail & impact burst ikut
            # terbalik-balik -> swing kacau.
            boss._drk_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._drk_attack_frame = int(getattr(boss, "_drk_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._drk_attack_active = False
            boss._drk_attack_frame = 0
            active = False

        boss._drk_previous_timer = timer
        boss._drk_attack_progress = (
            min(1.0, getattr(boss, "_drk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_drk_last_x"):
            boss._drk_last_x = boss.x
            boss._drk_last_y = boss.y
            return False
        dx = abs(boss.x - boss._drk_last_x)
        dy = abs(boss.y - boss._drk_last_y)
        boss._drk_last_x = boss.x
        boss._drk_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_drk_idle(surface, boss, x, y):
        # Heavy breathing bob
        bob = int(math.sin(boss.pulse * 0.5) * 6)
        _NS_drakar._draw_shadow(surface, x, y + 80)
        _NS_drakar._draw_rage_mist(surface, x, y + 60, boss.pulse)
        _NS_drakar._draw_drk_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")

    def _draw_drk_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.1)) * 5)
        sway = int(math.sin(phase * 0.8) * 3)
        _NS_drakar._draw_shadow(surface, x + sway, y + 80)
        _NS_drakar._draw_rage_mist(surface, x + sway, y + 60, phase, trail=True,
                                    facing=boss.direction)
        _NS_drakar._draw_drk_body(surface, x + sway, y - bob + 2, boss.direction,
                                   phase, "walk")

    def _draw_drk_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (bukan counter frame yang
        # hanya naik saat renderer dipanggil). Dengan body hero di-
        # cache, renderer dipanggil tiap N frame; progress tetap maju
        # tiap frame supaya fase swing tidak membeku.
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 46)))
        if getattr(boss, "_drk_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        # Arah swing terkunci saat serangan dimulai (lihat
        # _update_drk_attack_anim). Fallback ke arah live kalau
        # state kunci tidak ada.
        facing = getattr(boss, "_drk_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Two-handed swing has bigger body movement
        if progress < 0.15:
            # Anticipation - crouch
            t = progress / 0.15
            lunge = -int(t * 4) * facing
            lift = -int(t * 4)
        elif progress < 0.40:
            # Wind-up - lean back, rise up
            t = (progress - 0.15) / 0.25
            lunge = -int(4 + t * 4) * facing
            lift = int(-4 + t * 10)
        elif progress < 0.55:
            # EXPLOSIVE SWING - lunge forward hard
            t = (progress - 0.40) / 0.15
            t_ease = 1 - (1 - t) ** 2
            lunge = int((-8 + t_ease * 28)) * facing
            lift = int(6 - t_ease * 10)
        elif progress < 0.70:
            # Impact hold - screen shake feel
            t = (progress - 0.55) / 0.15
            shake_x = int(math.sin(t * 30) * 3 * (1 - t))
            lunge = int(20 + shake_x) * facing
            lift = int(-4 - t * 2)
        else:
            # Recovery
            t = (progress - 0.70) / 0.30
            t_ease = 1 - (1 - t) ** 2
            lunge = int(20 * (1 - t_ease)) * facing
            lift = int(-6 + t_ease * 6)

        _NS_drakar._draw_shadow(surface, x + lunge, y + 80)
        _NS_drakar._draw_rage_mist(surface, x + lunge, y + 60, boss.pulse, intense=True)
        _NS_drakar._draw_drk_body(surface, x + lunge, y - lift, facing,
                                   boss.pulse, "attack", progress)
        _NS_drakar._draw_axe_slash_trail(surface, boss, x + lunge, y - lift, progress)
        if 0.53 <= progress <= 0.70:
            _NS_drakar._draw_impact_burst(surface, boss, x + lunge, y - lift, progress)

    def _draw_drk_helix(surface, boss, x, y, timer, phase):
        """Counter Helix - spinning."""
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        spin = progress * math.pi * 8

        bob = int(math.sin(progress * math.pi) * -5)
        _NS_drakar._draw_shadow(surface, x, y + 80)
        _NS_drakar._draw_rage_mist(surface, x, y + 60, phase, intense=True)

        # Big spinning red crescent slash around boss
        slash_surf = pygame.Surface((280, 280), pygame.SRCALPHA)
        center = (140, 140)
        radius = 72

        for arm_i in range(2):
            arm_start = spin + arm_i * math.pi
            arc_pts = []
            steps = 24
            arc_span = math.pi * 0.9
            for i in range(steps + 1):
                a = arm_start + arc_span * i / steps
                px = center[0] + int(math.cos(a) * radius)
                py = center[1] + int(math.sin(a) * radius * 0.7)
                arc_pts.append((px, py))

            for layer_i, (r_off, thick, color, a_mult) in enumerate([
                (4, 10, _NS_drakar.PALETTE["blood_darkest"], 0.7),
                (2, 8, _NS_drakar.PALETTE["blood_dark"], 0.85),
                (0, 6, _NS_drakar.PALETTE["blood_mid"], 1.0),
                (-1, 4, _NS_drakar.PALETTE["blood_light"], 1.0),
                (-2, 2, _NS_drakar.PALETTE["blood_hot"], 1.0),
            ]):
                for k in range(len(arc_pts) - 1):
                    fade = 1 - (k / len(arc_pts))
                    alpha_val = _NS_drakar._alpha(240 * a_mult * fade)
                    if alpha_val <= 0:
                        continue
                    pygame.draw.line(slash_surf,
                                     _NS_drakar._rgba(color, alpha_val),
                                     arc_pts[k], arc_pts[k + 1], thick)

            if arc_pts:
                tip = arc_pts[-1]
                pygame.draw.rect(slash_surf,
                                 _NS_drakar._rgba(_NS_drakar.PALETTE["blade_shine"], 255),
                                 (tip[0], tip[1], 3, 3))
                pygame.draw.rect(slash_surf,
                                 _NS_drakar._rgba(_NS_drakar.PALETTE["white"], 255),
                                 (tip[0], tip[1], 2, 2))

        # Blood particles flying out
        for i in range(28):
            angle = spin * 0.5 + i * math.pi / 14
            r_p = radius + int(math.sin(phase + i) * 12) - 8
            px = center[0] + int(math.cos(angle) * r_p)
            py = center[1] + int(math.sin(angle) * r_p * 0.7)
            alpha = _NS_drakar._alpha(220)
            pygame.draw.rect(slash_surf,
                             _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], alpha),
                             (px, py, 3, 3))
            pygame.draw.rect(slash_surf,
                             _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"], alpha),
                             (px, py, 2, 2))

        surface.blit(slash_surf, (x - 140, y - 140 + bob))

        _NS_drakar._draw_drk_body(surface, x, y + bob, boss.direction, phase, "helix",
                                   spin_angle=spin)

    # ============================================================
    # BODY (LARGER SCALE)
    # ============================================================
    def _draw_drk_body(surface, cx, cy, facing, phase, action, attack_progress=0,
                       spin_angle=0):
        """Draw bulky barbarian body (HD scale, two-handed axe)."""
        # Legs (behind)
        _NS_drakar._draw_drk_legs(surface, cx, cy + 28, facing, phase, action)

        # Waist / belt
        _NS_drakar._draw_drk_waist(surface, cx, cy + 14, facing, phase)

        # Torso (bulky bare chest)
        _NS_drakar._draw_drk_torso(surface, cx, cy - 6, facing, phase, action)

        # Head
        _NS_drakar._draw_drk_head(surface, cx, cy - 30, facing, phase, action)

        # Compute axe grip positions FIRST (front hand + back hand on same handle)
        grip_data = _NS_drakar._compute_two_handed_grip(cx, cy, facing, phase,
                                                        action, attack_progress,
                                                        spin_angle)

        # Draw BACK arm reaching to grip (behind axe)
        _NS_drakar._draw_drk_arm_two_handed_back(surface, cx, cy - 4, facing, phase,
                                                  grip_data["back_hand"], action)

        # Draw AXE (in front of back arm)
        _NS_drakar._draw_axe(surface, grip_data["axe_head"][0],
                             grip_data["axe_head"][1],
                             facing, grip_data["axe_angle"], action,
                             attack_progress,
                             pommel_pos=grip_data["pommel"])

        # Draw FRONT arm gripping (in front of axe)
        _NS_drakar._draw_drk_arm_two_handed_front(surface, cx, cy - 4, facing, phase,
                                                   grip_data["front_hand"], action,
                                                   attack_progress)

    def _draw_drk_legs(surface, cx, cy, facing, phase, action):
        """Bulky legs, HD scale."""
        if action == "walk":
            stride = math.sin(phase * 2) * 5
            back_lift = max(0, -math.sin(phase * 2)) * 4
            front_lift = max(0, math.sin(phase * 2)) * 4
        else:
            stride = 0
            back_lift = front_lift = 0

        bx = cx - 9 + int(stride)
        by = cy - int(back_lift)
        _NS_drakar._draw_leg(surface, bx, by, facing, back=True)

        fx = cx + 9 - int(stride)
        fy = cy - int(front_lift)
        _NS_drakar._draw_leg(surface, fx, fy, facing, back=False)

    def _draw_leg(surface, cx, cy, facing, back=False):
        """Big beefy leg (HD)."""
        # Thigh (leather pants) - taller and wider
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"],
                         (cx - 7, cy - 14, 15, 18))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_darkest"],
                         (cx - 7, cy - 14, 14, 17))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_dark"],
                         (cx - 6, cy - 14, 11, 16))
        if not back:
            pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_mid"],
                             (cx - 4, cy - 13, 7, 14))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_light"],
                             (cx - 2, cy - 12, 2, 10))

        # Straps around thigh
        for strap_y in (cy - 10, cy - 4):
            pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_darkest"],
                             (cx - 7, strap_y, 14, 2))
            if not back:
                pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_mid"],
                                 (cx - 6, strap_y, 12, 1))
            # Studs
            for stud_x in (cx - 4, cx + 3):
                pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"],
                                 (stud_x, strap_y, 2, 2))
                if not back:
                    pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"],
                                     (stud_x, strap_y, 1, 1))

        # Knee guard (metal)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"],
                         (cx - 6, cy + 4, 13, 6))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_darkest"],
                         (cx - 6, cy + 4, 12, 6))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"],
                         (cx - 5, cy + 4, 10, 5))
        if not back:
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_mid"],
                             (cx - 5, cy + 4, 8, 3))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"],
                             (cx - 4, cy + 4, 5, 1))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_shine"],
                             (cx - 3, cy + 4, 2, 1))

        # Boot (heavy iron-plated)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"],
                         (cx - 8, cy + 10, 18, 10))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_darkest"],
                         (cx - 8, cy + 10, 17, 9))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_dark"],
                         (cx - 7, cy + 10, 14, 8))
        if not back:
            pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_mid"],
                             (cx - 6, cy + 10, 10, 5))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_light"],
                             (cx - 5, cy + 11, 6, 3))

        # Metal boot cap / plates
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_darkest"],
                         (cx - 8, cy + 15, 18, 4))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"],
                         (cx - 8, cy + 15, 17, 3))
        if not back:
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_mid"],
                             (cx - 7, cy + 15, 15, 2))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"],
                             (cx - 6, cy + 15, 12, 1))

        # Boot toe stud
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"],
                         (cx + facing * 6, cy + 17, 2, 2))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_shine"],
                         (cx + facing * 6, cy + 17, 1, 1))

    def _draw_drk_waist(surface, cx, cy, facing, phase):
        """Big belt with buckle + loincloth (HD)."""
        # Thick belt
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"],
                         (cx - 22, cy - 6, 45, 10))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_darkest"],
                         (cx - 21, cy - 6, 43, 10))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_dark"],
                         (cx - 21, cy - 6, 42, 8))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_mid"],
                         (cx - 20, cy - 5, 40, 5))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_light"],
                         (cx - 18, cy - 5, 6, 2))

        # Belt studs
        for sx_off in (-16, -10, -4, 8, 14):
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_darkest"],
                             (cx + sx_off - 1, cy - 2, 4, 4))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"],
                             (cx + sx_off, cy - 2, 3, 3))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_mid"],
                             (cx + sx_off, cy - 2, 2, 2))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"],
                             (cx + sx_off, cy - 2, 1, 1))

        # Big central buckle (skull/axe rune)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"],
                         (cx - 6, cy - 6, 14, 11))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_darkest"],
                         (cx - 6, cy - 6, 13, 11))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"],
                         (cx - 5, cy - 6, 11, 10))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_mid"],
                         (cx - 4, cy - 5, 9, 8))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"],
                         (cx - 4, cy - 5, 3, 2))

        # Rune on buckle (red glow)
        rune_pulse = math.sin(phase * 2) * 0.3 + 0.7
        rune_alpha = _NS_drakar._alpha(240 * rune_pulse)
        for r in range(5, 0, -1):
            _NS_drakar._aacircle(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"],
                                 _NS_drakar._alpha(120 * (5 - r) / 5 * rune_pulse)),
                (cx + 1, cy), r)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_darkest"],
                         (cx - 2, cy - 2, 6, 5))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_mid"],
                         (cx - 1, cy - 1, 4, 3))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_hot"],
                         (cx, cy, 2, 1))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_shine"],
                         (cx, cy, 1, 1))

        # Loincloth (bigger flap)
        loin_pts = [
            (cx - 9, cy + 3),
            (cx + 9, cy + 3),
            (cx + 7, cy + 12),
            (cx + 3, cy + 16),
            (cx - 3, cy + 16),
            (cx - 7, cy + 12),
        ]
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"],
                         [(px + 1, py + 1) for px, py in loin_pts])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["leather_darkest"], loin_pts)
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["leather_dark"], [
            (cx - 7, cy + 3),
            (cx + 7, cy + 3),
            (cx + 5, cy + 12),
            (cx, cy + 15),
            (cx - 5, cy + 12),
        ])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["leather_mid"], [
            (cx - 3, cy + 4),
            (cx + 3, cy + 4),
            (cx + 2, cy + 12),
            (cx, cy + 14),
            (cx - 2, cy + 12),
        ])
        # Fold line
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_darkest"],
                         (cx, cy + 4), (cx, cy + 15), 1)
        # Metal tip / spike on loincloth
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"],
                         (cx - 1, cy + 15, 3, 2))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"],
                         (cx, cy + 15, 1, 1))

    def _draw_drk_torso(surface, cx, cy, facing, phase, action):
        """MUSCULAR red torso (HD, big)."""
        breath = math.sin(phase * 0.6) * 2
        if action == "attack":
            breath += math.sin(phase * 3) * 1

        # Main torso shape (much bigger, wider chest)
        torso_pts = [
            (cx - 18, cy - 4),
            (cx - 20, cy + 6),
            (cx - 17, cy + 16),
            (cx + 17, cy + 16),
            (cx + 20, cy + 6),
            (cx + 18, cy - 4),
            (cx + 12, cy - 10),
            (cx - 12, cy - 10),
        ]
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"],
                         [(px + 2, py + 2) for px, py in torso_pts])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_darkest"], torso_pts)

        # Mid skin
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_dark"], [
            (cx - 17, cy - 2 + int(breath)),
            (cx - 19, cy + 6),
            (cx - 15, cy + 15),
            (cx + 15, cy + 15),
            (cx + 19, cy + 6),
            (cx + 17, cy - 2 + int(breath)),
            (cx + 10, cy - 9),
            (cx - 10, cy - 9),
        ])

        # Highlight
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_mid"], [
            (cx - 14, cy + int(breath)),
            (cx - 16, cy + 6),
            (cx - 12, cy + 12),
            (cx + 12, cy + 12),
            (cx + 16, cy + 6),
            (cx + 14, cy + int(breath)),
            (cx + 8, cy - 7),
            (cx - 8, cy - 7),
        ])

        # Pectoral definition
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_light"], [
            (cx - 10, cy + 1 + int(breath)),
            (cx - 3, cy + 1 + int(breath)),
            (cx - 5, cy + 8),
            (cx - 10, cy + 6),
        ])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_light"], [
            (cx + 3, cy + 1 + int(breath)),
            (cx + 10, cy + 1 + int(breath)),
            (cx + 10, cy + 6),
            (cx + 5, cy + 8),
        ])
        # Pec highlights
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_shine"],
                         (cx - 8, cy + 2 + int(breath), 3, 1))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_shine"],
                         (cx + 5, cy + 2 + int(breath), 3, 1))

        # Central chest divide
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_darkest"],
                         (cx, cy - 5 + int(breath)), (cx, cy + 12), 2)
        pygame.draw.line(surface, _NS_drakar.PALETTE["shadow_deep"],
                         (cx, cy - 4 + int(breath)), (cx, cy + 11), 1)

        # Ab muscles (6-pack style)
        for i, y_off in enumerate((6, 10, 13)):
            for x_side in (-1, 1):
                pygame.draw.line(surface, _NS_drakar.PALETTE["skin_darkest"],
                                 (cx + x_side * 2, cy + y_off),
                                 (cx + x_side * 7, cy + y_off), 1)
            # Highlights on abs
            pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_light"],
                             (cx - 5, cy + y_off - 1, 2, 1))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_light"],
                             (cx + 3, cy + y_off - 1, 2, 1))

        # Scar on chest (diagonal)
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_darkest"],
                         (cx + 4, cy - 3 + int(breath)), (cx + 10, cy + 3), 1)
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_shine"],
                         (cx + 5, cy - 2 + int(breath)), (cx + 9, cy + 2), 1)

        # Leather bandolier strap
        strap_start = (cx - 18, cy - 3)
        strap_end = (cx + 18, cy + 15)
        pygame.draw.line(surface, _NS_drakar.PALETTE["shadow_deep"],
                         (strap_start[0] + 1, strap_start[1] + 1),
                         (strap_end[0] + 1, strap_end[1] + 1), 6)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_darkest"],
                         strap_start, strap_end, 5)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_dark"],
                         strap_start, strap_end, 4)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_mid"],
                         (strap_start[0], strap_start[1] - 1),
                         (strap_end[0], strap_end[1] - 1), 2)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_light"],
                         (strap_start[0], strap_start[1] - 2),
                         (strap_end[0], strap_end[1] - 2), 1)

        # SPIKED SHOULDER PAULDRON (iconic - big and dramatic)
        _NS_drakar._draw_shoulder_pauldron(surface, cx - facing * 16, cy - 8, facing)

        # Other shoulder (bare bulky muscle)
        _NS_drakar._draw_bare_shoulder(surface, cx + facing * 14, cy - 8, facing)

    def _draw_shoulder_pauldron(surface, cx, cy, facing):
        """Big spiked iron shoulder guard."""
        # Base dome (bigger)
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"], [
            (cx - 9, cy + 8),
            (cx - 10, cy + 3),
            (cx - 7, cy - 5),
            (cx - 3, cy - 8),
            (cx + 4, cy - 8),
            (cx + 8, cy - 5),
            (cx + 10, cy + 3),
            (cx + 9, cy + 8),
        ])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_darkest"], [
            (cx - 8, cy + 7),
            (cx - 9, cy + 3),
            (cx - 6, cy - 4),
            (cx - 3, cy - 7),
            (cx + 4, cy - 7),
            (cx + 7, cy - 4),
            (cx + 9, cy + 3),
            (cx + 8, cy + 7),
        ])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_dark"], [
            (cx - 7, cy + 6),
            (cx - 8, cy + 3),
            (cx - 5, cy - 3),
            (cx - 2, cy - 6),
            (cx + 3, cy - 6),
            (cx + 6, cy - 3),
            (cx + 8, cy + 3),
            (cx + 7, cy + 6),
        ])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_mid"], [
            (cx - 5, cy + 5),
            (cx - 7, cy + 2),
            (cx - 4, cy - 2),
            (cx - 1, cy - 5),
            (cx + 2, cy - 5),
            (cx + 5, cy - 2),
            (cx + 7, cy + 2),
            (cx + 5, cy + 5),
        ])
        # Highlight
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_light"], [
            (cx - 3, cy),
            (cx - 1, cy - 3),
            (cx + 1, cy - 3),
            (cx + 2, cy),
            (cx, cy + 2),
            (cx - 2, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_shine"],
                         (cx - 1, cy - 1, 2, 2))

        # BIG SPIKES on top (3 tall spikes)
        for i, (x_off, height) in enumerate([(-5, 6), (-1, 8), (4, 6)]):
            spike_x = cx + x_off
            spike_top_y = cy - 7 - height

            # Shadow
            _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_top_y + 1),
                (spike_x - 3 + 1, cy - 5 + 1),
                (spike_x + 3 + 1, cy - 5 + 1),
            ])
            # Base
            _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_darkest"], [
                (spike_x, spike_top_y),
                (spike_x - 3, cy - 5),
                (spike_x + 3, cy - 5),
            ])
            _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_dark"], [
                (spike_x, spike_top_y),
                (spike_x - 2, cy - 5),
                (spike_x + 2, cy - 5),
            ])
            _NS_drakar._poly(surface, _NS_drakar.PALETTE["armor_mid"], [
                (spike_x, spike_top_y),
                (spike_x - 1, cy - 5),
                (spike_x + 2, cy - 5),
            ])
            # Tip highlight
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"],
                             (spike_x, spike_top_y, 1, 2))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_shine"],
                             (spike_x, spike_top_y, 1, 1))

        # Rivets on pauldron
        for rx_off in (-6, 0, 6):
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_darkest"],
                             (cx + rx_off - 1, cy + 4, 2, 2))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"],
                             (cx + rx_off, cy + 4, 1, 1))

    def _draw_bare_shoulder(surface, cx, cy, facing):
        """Big muscular bare shoulder (bicep)."""
        # Deltoid muscle
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"],
                         (cx - 5, cy - 4, 11, 12))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"],
                         (cx - 5, cy - 4, 10, 11))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_dark"],
                         (cx - 4, cy - 3, 9, 10))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_mid"],
                         (cx - 3, cy - 2, 7, 8))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_light"],
                         (cx - 1, cy - 1, 3, 5))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_shine"],
                         (cx, cy, 1, 2))

        # Muscle line curves
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_darkest"],
                         (cx - 2, cy + 2), (cx + 3, cy + 5), 1)

    def _draw_drk_arm_two_handed_front(surface, cx, cy, facing, phase,
                                        hand_pos, action, attack_progress=0):
        """Front arm reaching up to grip axe (near blade end)."""
        # Shoulder base
        base_x = cx + facing * 15
        base_y = cy + 2

        hand_x, hand_y = hand_pos

        # Compute elbow via IK (bent arm bending outward)
        arm_length = 22  # total arm length
        # Vector from shoulder to hand
        vx = hand_x - base_x
        vy = hand_y - base_y
        dist = max(1, math.hypot(vx, vy))
        dist = min(dist, arm_length * 0.98)

        # Midpoint
        mid_x = (base_x + hand_x) / 2
        mid_y = (base_y + hand_y) / 2

        # Perpendicular for elbow displacement (bend outward/downward)
        perp_x = -vy / dist
        perp_y = vx / dist
        # Elbow bends forward-out
        elbow_offset = math.sqrt(max(0, (arm_length / 2) ** 2 - (dist / 2) ** 2)) * 0.7
        # Bend direction based on facing and action
        bend_sign = facing
        elbow_x = int(mid_x + perp_x * elbow_offset * bend_sign)
        elbow_y = int(mid_y + perp_y * elbow_offset * bend_sign)

        # Upper arm (muscular skin)
        _NS_drakar._aaline(surface, _NS_drakar.PALETTE["shadow_deep"],
                           (base_x + 2, base_y + 2), (elbow_x + 2, elbow_y + 2), 10)
        _NS_drakar._aaline(surface, _NS_drakar.PALETTE["skin_darkest"],
                           (base_x, base_y), (elbow_x, elbow_y), 9)
        _NS_drakar._aaline(surface, _NS_drakar.PALETTE["skin_dark"],
                           (base_x, base_y), (elbow_x, elbow_y), 7)
        _NS_drakar._aaline(surface, _NS_drakar.PALETTE["skin_mid"],
                           (base_x, base_y - 1), (elbow_x, elbow_y - 1), 4)
        _NS_drakar._aaline(surface, _NS_drakar.PALETTE["skin_light"],
                           (base_x, base_y - 2), (elbow_x, elbow_y - 2), 2)

        # Bicep flex (bigger during swing)
        mid_arm_x = int((base_x + elbow_x) / 2)
        mid_arm_y = int((base_y + elbow_y) / 2)
        bicep_flex = 1
        if action == "attack" and 0.15 <= attack_progress <= 0.55:
            bicep_flex = 2
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["skin_dark"],
                             (mid_arm_x + facing, mid_arm_y - 2), 5 + bicep_flex)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["skin_mid"],
                             (mid_arm_x + facing, mid_arm_y - 3), 3 + bicep_flex)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["skin_light"],
                             (mid_arm_x + facing, mid_arm_y - 3), 1 + bicep_flex)

        # Forearm bracer (leather)
        _NS_drakar._aaline(surface, _NS_drakar.PALETTE["shadow_deep"],
                           (elbow_x + 2, elbow_y + 2), (hand_x + 2, hand_y + 2), 8)
        _NS_drakar._aaline(surface, _NS_drakar.PALETTE["leather_darkest"],
                           (elbow_x, elbow_y), (hand_x, hand_y), 7)
        _NS_drakar._aaline(surface, _NS_drakar.PALETTE["leather_dark"],
                           (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_drakar._aaline(surface, _NS_drakar.PALETTE["leather_mid"],
                           (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 3)
        _NS_drakar._aaline(surface, _NS_drakar.PALETTE["leather_light"],
                           (elbow_x, elbow_y - 2), (hand_x, hand_y - 2), 1)

        # Bracer studs
        for stud_t in (0.35, 0.65):
            stud_x = int(elbow_x + (hand_x - elbow_x) * stud_t)
            stud_y = int(elbow_y + (hand_y - elbow_y) * stud_t)
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"],
                             (stud_x - 1, stud_y - 1, 3, 3))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_mid"],
                             (stud_x, stud_y - 1, 2, 2))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_shine"],
                             (stud_x, stud_y - 1, 1, 1))

        # FIST gripping handle
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["shadow_deep"],
                             (hand_x + 1, hand_y + 1), 5)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["skin_darkest"],
                             (hand_x, hand_y), 5)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["skin_dark"],
                             (hand_x, hand_y), 4)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["skin_mid"],
                             (hand_x - facing, hand_y - 1), 3)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["skin_light"],
                             (hand_x - facing, hand_y - 1), 1)
        # Knuckles
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"],
                         (hand_x - 2, hand_y - 2, 1, 1))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"],
                         (hand_x, hand_y - 2, 1, 1))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"],
                         (hand_x + 2, hand_y - 2, 1, 1))

    def _draw_drk_arm_two_handed_back(surface, cx, cy, facing, phase,
                                       hand_pos, action):
        """Back arm reaching across to grip axe handle (near pommel)."""
        base_x = cx - facing * 12
        base_y = cy + 2

        hand_x, hand_y = hand_pos

        # IK for elbow
        arm_length = 22
        vx = hand_x - base_x
        vy = hand_y - base_y
        dist = max(1, math.hypot(vx, vy))
        dist = min(dist, arm_length * 0.98)

        mid_x = (base_x + hand_x) / 2
        mid_y = (base_y + hand_y) / 2

        perp_x = -vy / dist
        perp_y = vx / dist
        elbow_offset = math.sqrt(max(0, (arm_length / 2) ** 2 - (dist / 2) ** 2)) * 0.7
        # Back arm bends the opposite way (backward)
        bend_sign = -facing
        elbow_x = int(mid_x + perp_x * elbow_offset * bend_sign)
        elbow_y = int(mid_y + perp_y * elbow_offset * bend_sign)

        # Upper arm (skin - slightly darker for back-shading)
        _NS_drakar._aaline(surface, _NS_drakar.PALETTE["shadow_deep"],
                           (base_x + 2, base_y + 2), (elbow_x + 2, elbow_y + 2), 10)
        _NS_drakar._aaline(surface, _NS_drakar.PALETTE["skin_darkest"],
                           (base_x, base_y), (elbow_x, elbow_y), 9)
        _NS_drakar._aaline(surface, _NS_drakar.PALETTE["skin_dark"],
                           (base_x, base_y), (elbow_x, elbow_y), 7)
        _NS_drakar._aaline(surface, _NS_drakar.PALETTE["skin_mid"],
                           (base_x, base_y - 1), (elbow_x, elbow_y - 1), 3)

        # Bicep (smaller/dimmer since back)
        mid_arm_x = int((base_x + elbow_x) / 2)
        mid_arm_y = int((base_y + elbow_y) / 2)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["skin_darkest"],
                             (mid_arm_x, mid_arm_y - 1), 5)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["skin_dark"],
                             (mid_arm_x, mid_arm_y - 2), 3)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["skin_mid"],
                             (mid_arm_x, mid_arm_y - 2), 1)

        # Forearm bracer
        _NS_drakar._aaline(surface, _NS_drakar.PALETTE["shadow_deep"],
                           (elbow_x + 2, elbow_y + 2), (hand_x + 2, hand_y + 2), 8)
        _NS_drakar._aaline(surface, _NS_drakar.PALETTE["leather_darkest"],
                           (elbow_x, elbow_y), (hand_x, hand_y), 7)
        _NS_drakar._aaline(surface, _NS_drakar.PALETTE["leather_dark"],
                           (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_drakar._aaline(surface, _NS_drakar.PALETTE["leather_mid"],
                           (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 2)

        # Bracer studs
        for stud_t in (0.35, 0.65):
            stud_x = int(elbow_x + (hand_x - elbow_x) * stud_t)
            stud_y = int(elbow_y + (hand_y - elbow_y) * stud_t)
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_darkest"],
                             (stud_x - 1, stud_y - 1, 3, 3))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"],
                             (stud_x, stud_y - 1, 2, 2))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_mid"],
                             (stud_x, stud_y - 1, 1, 1))

        # Fist gripping handle
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["shadow_deep"],
                             (hand_x + 1, hand_y + 1), 5)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["skin_darkest"],
                             (hand_x, hand_y), 5)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["skin_dark"],
                             (hand_x, hand_y), 4)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["skin_mid"],
                             (hand_x - facing, hand_y - 1), 2)
        # Knuckles
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"],
                         (hand_x - 2, hand_y - 2, 1, 1))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"],
                         (hand_x, hand_y - 2, 1, 1))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"],
                         (hand_x + 2, hand_y - 2, 1, 1))

    def _compute_two_handed_grip(cx, cy, facing, phase, action,
                                  attack_progress=0, spin_angle=0):
        """Compute positions for two-handed axe grip.
        Returns: front_hand, back_hand, axe_head, pommel, axe_angle
        """
        # Base position (chest-front of body)
        base_x = cx + facing * 8
        base_y = cy - 2

        # Determine axe angle based on action
        if action == "attack":
            if attack_progress < 0.15:
                # Anticipation
                t = attack_progress / 0.15
                axe_angle = (-math.pi * 0.15 - t * 0.4) * facing
                grip_lean = -t * 4  # pull weapon back
            elif attack_progress < 0.40:
                # Wind up HIGH BACK (over shoulder, both hands raised)
                t = (attack_progress - 0.15) / 0.25
                t_ease = t * t
                axe_angle = (-math.pi * 0.55 - t_ease * math.pi * 0.75) * facing
                grip_lean = -4 - t * 3
            elif attack_progress < 0.55:
                # EXPLOSIVE SWING
                t = (attack_progress - 0.40) / 0.15
                t_ease = 1 - (1 - t) ** 2
                start_a = -math.pi * 1.3 * facing
                end_a = math.pi * 0.55 * facing
                axe_angle = start_a + (end_a - start_a) * t_ease
                grip_lean = -7 + t_ease * 14
            elif attack_progress < 0.70:
                # Impact hold
                axe_angle = math.pi * 0.55 * facing
                grip_lean = 7
            else:
                # Recovery
                t = (attack_progress - 0.70) / 0.30
                start_a = math.pi * 0.55 * facing
                end_a = math.pi * 0.05 * facing
                axe_angle = start_a + (end_a - start_a) * t
                grip_lean = 7 * (1 - t)
        elif action == "helix":
            axe_angle = spin_angle * facing
            grip_lean = 0
        elif action == "walk":
            axe_angle = math.pi * 0.05 * facing + math.sin(phase * 2) * 0.15
            grip_lean = int(math.sin(phase * 2) * 2)
        else:
            # Idle - axe held horizontal across body (both hands ready)
            axe_angle = math.pi * 0.05 * facing + math.sin(phase * 0.5) * 0.06
            grip_lean = 0

        # Axe direction unit vector
        dx = math.cos(axe_angle)
        dy = math.sin(axe_angle)

        # Handle length and grip positions along the handle
        handle_len = 42
        # Front hand grips near the axe head (upper grip)
        # Back hand grips near the pommel (lower grip)

        # Grip base center (in front of chest area, moves with attack)
        grip_cx = base_x + grip_lean * facing
        grip_cy = base_y + 2

        # For attack phase, grip position shifts up during wind-up
        if action == "attack":
            if attack_progress < 0.40:
                # Move grip up during wind-up
                t = min(1.0, (attack_progress) / 0.40)
                grip_cy = base_y + 2 - int(t * 8)
            elif attack_progress < 0.55:
                # Grip swings down during swing
                t = (attack_progress - 0.40) / 0.15
                t_ease = 1 - (1 - t) ** 2
                grip_cy = base_y + 2 - int((1 - t_ease) * 8) + int(t_ease * 6)
            elif attack_progress < 0.70:
                # Impact - grip extended forward-down
                grip_cy = base_y + 8
            else:
                # Recovery
                t = (attack_progress - 0.70) / 0.30
                grip_cy = base_y + 8 - int(t * 6)

        # Front hand position (near axe head, ~70% along handle from pommel)
        front_grip_t = 0.70
        # Back hand position (near pommel, ~25% along handle from pommel)
        back_grip_t = 0.25

        # Compute along handle axis
        pommel_x = int(grip_cx - dx * handle_len * 0.5) * (1 if facing > 0 else 1)
        pommel_x = grip_cx + int(-dx * handle_len * 0.5) * facing
        pommel_y = grip_cy + int(-dy * handle_len * 0.5)

        axe_head_x = grip_cx + int(dx * handle_len * 0.5) * facing
        axe_head_y = grip_cy + int(dy * handle_len * 0.5)

        front_hand_x = pommel_x + int((axe_head_x - pommel_x) * front_grip_t)
        front_hand_y = pommel_y + int((axe_head_y - pommel_y) * front_grip_t)

        back_hand_x = pommel_x + int((axe_head_x - pommel_x) * back_grip_t)
        back_hand_y = pommel_y + int((axe_head_y - pommel_y) * back_grip_t)

        return {
            "front_hand": (front_hand_x, front_hand_y),
            "back_hand": (back_hand_x, back_hand_y),
            "axe_head": (axe_head_x, axe_head_y),
            "pommel": (pommel_x, pommel_y),
            "axe_angle": axe_angle,
        }

    def _draw_axe(surface, cx, cy, facing, angle, action, attack_progress,
                  pommel_pos=None):
        """MASSIVE double-bladed axe (HD, two-handed).
        cx, cy = axe HEAD position
        pommel_pos = (x, y) of pommel end
        """
        dx = math.cos(angle)
        dy = math.sin(angle)

        # Head position
        head_cx = cx
        head_cy = cy

        # Pommel position (opposite end)
        if pommel_pos is not None:
            handle_back_x, handle_back_y = pommel_pos
        else:
            handle_len = 42
            handle_back_x = cx - int(dx * handle_len) * facing
            handle_back_y = cy - int(dy * handle_len)

        # Wooden handle (thick)
        pygame.draw.line(surface, _NS_drakar.PALETTE["shadow_deep"],
                         (handle_back_x + 2, handle_back_y + 2),
                         (head_cx + 2, head_cy + 2), 7)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_darkest"],
                         (handle_back_x, handle_back_y),
                         (head_cx, head_cy), 6)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_dark"],
                         (handle_back_x, handle_back_y),
                         (head_cx, head_cy), 4)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_mid"],
                         (handle_back_x, handle_back_y - 1),
                         (head_cx, head_cy - 1), 2)
        pygame.draw.line(surface, _NS_drakar.PALETTE["leather_light"],
                         (handle_back_x, handle_back_y - 2),
                         (head_cx, head_cy - 2), 1)

        # Leather wraps on grip (evenly spaced along the handle)
        for i in range(5):
            wrap_t = 0.1 + i * 0.16
            wrap_x = int(handle_back_x + (head_cx - handle_back_x) * wrap_t)
            wrap_y = int(handle_back_y + (head_cy - handle_back_y) * wrap_t)
            pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_darkest"],
                             (wrap_x - 1, wrap_y - 1, 4, 4))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_dark"],
                             (wrap_x, wrap_y, 3, 3))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["leather_mid"],
                             (wrap_x, wrap_y, 2, 2))

        # Pommel (bottom of handle - spiked knob)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["shadow_deep"],
                             (handle_back_x + 1, handle_back_y + 1), 5)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["armor_darkest"],
                             (handle_back_x, handle_back_y), 5)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["armor_dark"],
                             (handle_back_x, handle_back_y), 4)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["armor_mid"],
                             (handle_back_x, handle_back_y), 3)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["armor_light"],
                             (handle_back_x, handle_back_y), 1)
        # Small spike on pommel
        pommel_spike_x = handle_back_x - int(dx * 4) * facing
        pommel_spike_y = handle_back_y - int(dy * 4)
        pygame.draw.line(surface, _NS_drakar.PALETTE["armor_darkest"],
                         (handle_back_x, handle_back_y),
                         (pommel_spike_x, pommel_spike_y), 3)
        pygame.draw.line(surface, _NS_drakar.PALETTE["armor_mid"],
                         (handle_back_x, handle_back_y),
                         (pommel_spike_x, pommel_spike_y), 1)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_shine"],
                         (pommel_spike_x, pommel_spike_y, 1, 1))

        # AXE HEAD (perpendicular direction)
        perp_x = -dy
        perp_y = dx

        blade_size = 22  # Even bigger for two-handed!

        # Top blade (crescent)
        top_tip_x = head_cx + int(perp_x * blade_size) * facing
        top_tip_y = head_cy + int(perp_y * blade_size)
        top_edge1_x = head_cx + int((perp_x * blade_size * 0.65 + dx * blade_size * 0.75)) * facing
        top_edge1_y = head_cy + int((perp_y * blade_size * 0.65 + dy * blade_size * 0.75))
        top_edge2_x = head_cx + int((perp_x * blade_size * 0.65 - dx * blade_size * 0.75)) * facing
        top_edge2_y = head_cy + int((perp_y * blade_size * 0.65 - dy * blade_size * 0.75))
        top_mid1_x = head_cx + int((perp_x * blade_size * 0.9 + dx * blade_size * 0.4)) * facing
        top_mid1_y = head_cy + int((perp_y * blade_size * 0.9 + dy * blade_size * 0.4))
        top_mid2_x = head_cx + int((perp_x * blade_size * 0.9 - dx * blade_size * 0.4)) * facing
        top_mid2_y = head_cy + int((perp_y * blade_size * 0.9 - dy * blade_size * 0.4))

        # Bottom blade
        bot_tip_x = head_cx - int(perp_x * blade_size) * facing
        bot_tip_y = head_cy - int(perp_y * blade_size)
        bot_edge1_x = head_cx - int((perp_x * blade_size * 0.65 - dx * blade_size * 0.75)) * facing
        bot_edge1_y = head_cy - int((perp_y * blade_size * 0.65 - dy * blade_size * 0.75))
        bot_edge2_x = head_cx - int((perp_x * blade_size * 0.65 + dx * blade_size * 0.75)) * facing
        bot_edge2_y = head_cy - int((perp_y * blade_size * 0.65 + dy * blade_size * 0.75))
        bot_mid1_x = head_cx - int((perp_x * blade_size * 0.9 - dx * blade_size * 0.4)) * facing
        bot_mid1_y = head_cy - int((perp_y * blade_size * 0.9 - dy * blade_size * 0.4))
        bot_mid2_x = head_cx - int((perp_x * blade_size * 0.9 + dx * blade_size * 0.4)) * facing
        bot_mid2_y = head_cy - int((perp_y * blade_size * 0.9 + dy * blade_size * 0.4))

        # Draw top blade (layered)
        top_shape = [
            (head_cx, head_cy),
            (top_edge1_x, top_edge1_y),
            (top_mid1_x, top_mid1_y),
            (top_tip_x, top_tip_y),
            (top_mid2_x, top_mid2_y),
            (top_edge2_x, top_edge2_y),
        ]
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"],
                         [(p[0] + 2, p[1] + 2) for p in top_shape])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["blade_darkest"], top_shape)
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["blade_dark"], [
            (head_cx, head_cy),
            (int((head_cx + top_edge1_x) / 2), int((head_cy + top_edge1_y) / 2)),
            (top_mid1_x, top_mid1_y),
            (top_tip_x, top_tip_y),
            (top_mid2_x, top_mid2_y),
            (int((head_cx + top_edge2_x) / 2), int((head_cy + top_edge2_y) / 2)),
        ])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["blade_mid"], [
            (int(head_cx + perp_x * 4 * facing), int(head_cy + perp_y * 4)),
            (top_mid1_x, top_mid1_y),
            (top_tip_x, top_tip_y),
            (top_mid2_x, top_mid2_y),
        ])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["blade_light"], [
            (int(head_cx + perp_x * 8 * facing), int(head_cy + perp_y * 8)),
            (int((top_mid1_x + top_tip_x) / 2), int((top_mid1_y + top_tip_y) / 2)),
            (int((top_mid2_x + top_tip_x) / 2), int((top_mid2_y + top_tip_y) / 2)),
        ])
        # Bright edges
        pygame.draw.line(surface, _NS_drakar.PALETTE["blade_shine"],
                         (top_tip_x, top_tip_y), (top_mid1_x, top_mid1_y), 2)
        pygame.draw.line(surface, _NS_drakar.PALETTE["blade_shine"],
                         (top_tip_x, top_tip_y), (top_mid2_x, top_mid2_y), 2)
        pygame.draw.line(surface, _NS_drakar.PALETTE["white"],
                         (top_tip_x, top_tip_y), (top_mid1_x, top_mid1_y), 1)

        # Draw bottom blade
        bot_shape = [
            (head_cx, head_cy),
            (bot_edge1_x, bot_edge1_y),
            (bot_mid1_x, bot_mid1_y),
            (bot_tip_x, bot_tip_y),
            (bot_mid2_x, bot_mid2_y),
            (bot_edge2_x, bot_edge2_y),
        ]
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"],
                         [(p[0] + 2, p[1] + 2) for p in bot_shape])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["blade_darkest"], bot_shape)
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["blade_dark"], [
            (head_cx, head_cy),
            (int((head_cx + bot_edge1_x) / 2), int((head_cy + bot_edge1_y) / 2)),
            (bot_mid1_x, bot_mid1_y),
            (bot_tip_x, bot_tip_y),
            (bot_mid2_x, bot_mid2_y),
            (int((head_cx + bot_edge2_x) / 2), int((head_cy + bot_edge2_y) / 2)),
        ])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["blade_mid"], [
            (int(head_cx - perp_x * 4 * facing), int(head_cy - perp_y * 4)),
            (bot_mid1_x, bot_mid1_y),
            (bot_tip_x, bot_tip_y),
            (bot_mid2_x, bot_mid2_y),
        ])
        pygame.draw.line(surface, _NS_drakar.PALETTE["blade_shine"],
                         (bot_tip_x, bot_tip_y), (bot_mid1_x, bot_mid1_y), 2)
        pygame.draw.line(surface, _NS_drakar.PALETTE["blade_shine"],
                         (bot_tip_x, bot_tip_y), (bot_mid2_x, bot_mid2_y), 2)

        # Center hub (bigger for two-handed axe)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["shadow_deep"],
                             (head_cx + 1, head_cy + 1), 7)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["armor_darkest"],
                             (head_cx, head_cy), 7)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["armor_dark"],
                             (head_cx, head_cy), 6)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["armor_mid"],
                             (head_cx, head_cy), 4)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["armor_light"],
                             (head_cx, head_cy), 2)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["armor_shine"],
                             (head_cx - 1, head_cy - 1), 1)

        # Spike at TOP of axe head (between the two blades, pointing up along handle dir)
        spike_top_x = head_cx + int(dx * 8) * facing
        spike_top_y = head_cy + int(dy * 8)
        pygame.draw.line(surface, _NS_drakar.PALETTE["shadow_deep"],
                         (head_cx + 1, head_cy + 1),
                         (spike_top_x + 1, spike_top_y + 1), 4)
        pygame.draw.line(surface, _NS_drakar.PALETTE["blade_darkest"],
                         (head_cx, head_cy),
                         (spike_top_x, spike_top_y), 3)
        pygame.draw.line(surface, _NS_drakar.PALETTE["blade_mid"],
                         (head_cx, head_cy),
                         (spike_top_x, spike_top_y), 1)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["blade_shine"],
                         (spike_top_x, spike_top_y, 1, 1))

        # BLOOD DRIP on both tips (larger, more dramatic)
        for tip_x, tip_y in [(top_tip_x, top_tip_y), (bot_tip_x, bot_tip_y)]:
            pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_darkest"],
                             (tip_x - 1, tip_y, 4, 2))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_dark"],
                             (tip_x, tip_y, 3, 5))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_mid"],
                             (tip_x, tip_y + 2, 2, 4))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_light"],
                             (tip_x, tip_y + 5, 1, 2))
            # Falling drop
            pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_mid"],
                             (tip_x, tip_y + 8, 1, 2))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_dark"],
                             (tip_x, tip_y + 10, 1, 1))

    def _draw_drk_head(surface, cx, cy, facing, phase, action):
        """Head with wild hair, beard, glowing eyes (HD)."""
        # Neck (thick)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"],
                         (cx - 5, cy + 10, 11, 8))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"],
                         (cx - 5, cy + 10, 10, 8))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_dark"],
                         (cx - 4, cy + 10, 8, 7))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_mid"],
                         (cx - 2, cy + 10, 4, 5))

        # HAIR / mane (behind head first)
        _NS_drakar._draw_wild_hair(surface, cx, cy - 4, facing, phase)

        # Head shape (bigger, broader jaw)
        head_pts = [
            (cx - 10, cy - 4),
            (cx - 12, cy + 4),
            (cx - 9, cy + 12),
            (cx + 9, cy + 12),
            (cx + 12, cy + 4),
            (cx + 10, cy - 4),
            (cx + 7, cy - 8),
            (cx - 7, cy - 8),
        ]
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"],
                         [(px + 2, py + 2) for px, py in head_pts])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_darkest"], head_pts)

        # Mid tone
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_dark"], [
            (cx - 9, cy - 3),
            (cx - 11, cy + 4),
            (cx - 8, cy + 11),
            (cx + 8, cy + 11),
            (cx + 11, cy + 4),
            (cx + 9, cy - 3),
            (cx + 6, cy - 7),
            (cx - 6, cy - 7),
        ])

        # Face highlight (top)
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_mid"], [
            (cx - 6, cy - 1),
            (cx - 8, cy + 4),
            (cx - 5, cy + 9),
            (cx + 6, cy + 9),
            (cx + 9, cy + 4),
            (cx + 7, cy - 1),
            (cx + 4, cy - 5),
            (cx - 4, cy - 5),
        ])

        # Bright cheek (facing side)
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["skin_light"], [
            (cx + facing * 2, cy - 2),
            (cx + facing * 7, cy),
            (cx + facing * 5, cy + 5),
            (cx + facing * 2, cy + 3),
        ])
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_shine"],
                         (cx + facing * 5, cy + 1, 2, 2))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_shine"],
                         (cx + facing * 5, cy + 1, 1, 1))

        # Forehead scar
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_darkest"],
                         (cx - 4, cy - 6), (cx + 3, cy - 3), 1)
        pygame.draw.line(surface, _NS_drakar.PALETTE["skin_shine"],
                         (cx - 3, cy - 5), (cx + 2, cy - 3), 1)

        # Angry eyebrows (thick, V-angled)
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_darkest"], [
            (cx - 7, cy),
            (cx - 1, cy - 2),
            (cx - 1, cy + 1),
            (cx - 7, cy + 2),
        ])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_darkest"], [
            (cx + 7, cy),
            (cx + 1, cy - 2),
            (cx + 1, cy + 1),
            (cx + 7, cy + 2),
        ])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_dark"], [
            (cx - 6, cy),
            (cx - 2, cy - 1),
            (cx - 2, cy + 1),
            (cx - 6, cy + 1),
        ])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_dark"], [
            (cx + 6, cy),
            (cx + 2, cy - 1),
            (cx + 2, cy + 1),
            (cx + 6, cy + 1),
        ])

        # EYES (glowing yellow-orange)
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_off in (-4, 4):
            ex = cx + eye_off
            ey = cy + 2
            # Glow halo
            for r in range(5, 0, -1):
                alpha = _NS_drakar._alpha(140 * (5 - r) / 5 * eye_pulse)
                _NS_drakar._aacircle(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["eye_mid"], alpha),
                    (ex, ey), r)
            # Socket
            pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"],
                             (ex - 2, ey - 1, 5, 3))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["eye_dark"],
                             (ex - 1, ey - 1, 4, 2))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["eye_mid"],
                             (ex, ey - 1, 3, 2))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["eye_light"],
                             (ex + 1, ey - 1, 2, 1))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["eye_glow"],
                             (ex + 1, ey - 1, 1, 1))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["white"],
                             (ex + 1, ey - 1, 1, 1))

        # Nose (broad flat)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"],
                         (cx - 2, cy + 3, 5, 4))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"],
                         (cx - 2, cy + 3, 4, 4))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_dark"],
                         (cx - 1, cy + 3, 3, 3))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_mid"],
                         (cx + facing, cy + 3, 1, 2))
        # Nostrils
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"],
                         (cx - 1, cy + 6, 1, 1))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"],
                         (cx + 1, cy + 6, 1, 1))

        # BEARD (thick, big)
        _NS_drakar._draw_beard(surface, cx, cy + 7, facing, phase)

        # Ear (small on far side)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_darkest"],
                         (cx - facing * 10, cy + 2, 2, 5))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["skin_dark"],
                         (cx - facing * 10, cy + 3, 1, 3))
        # Ear piercing (metal ring)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"],
                         (cx - facing * 11, cy + 5, 1, 2))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_shine"],
                         (cx - facing * 11, cy + 5, 1, 1))

    def _draw_wild_hair(surface, cx, cy, facing, phase):
        """Wild flowing black mane (bigger)."""
        sway = math.sin(phase * 0.7) * 2

        # Mane back (larger)
        hair_pts = [
            (cx - 10, cy - 4),
            (cx - 12, cy),
            (cx - 14, cy + 6),
            (cx - 16 + int(sway), cy + 14),
            (cx - 14 + int(sway), cy + 22),
            (cx - 10 + int(sway), cy + 26),
            (cx - 6, cy + 24),
            (cx - 5, cy + 10),
            (cx - 4, cy - 5),
        ]
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"],
                         [(px + 2, py + 2) for px, py in hair_pts])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_darkest"], hair_pts)
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_dark"], [
            (cx - 9, cy - 3),
            (cx - 11, cy),
            (cx - 13, cy + 6),
            (cx - 14 + int(sway), cy + 13),
            (cx - 12 + int(sway), cy + 20),
            (cx - 8 + int(sway), cy + 24),
            (cx - 6, cy + 22),
            (cx - 5, cy + 10),
            (cx - 3, cy - 4),
        ])

        # Hair strand highlights
        for strand_x in (cx - 8, cx - 11, cx - 6):
            pygame.draw.line(surface, _NS_drakar.PALETTE["hair_mid"],
                             (strand_x, cy + 2),
                             (strand_x + int(sway * 0.5), cy + 20), 1)

        # Top spike hairs (mohawk style)
        for i, (x_off, height) in enumerate([(-4, 6), (-1, 8), (2, 7), (5, 5)]):
            spike_h = height + int(math.sin(phase + i) * 2)
            spike_x = cx + x_off
            _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"], [
                (spike_x + 1, cy - spike_h + 1),
                (spike_x - 3 + 1, cy + 1),
                (spike_x + 3 + 1, cy + 1),
            ])
            _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_darkest"], [
                (spike_x, cy - spike_h),
                (spike_x - 3, cy),
                (spike_x + 3, cy),
            ])
            _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_dark"], [
                (spike_x, cy - spike_h),
                (spike_x - 2, cy),
                (spike_x + 2, cy),
            ])
            _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_mid"], [
                (spike_x, cy - spike_h),
                (spike_x - 1, cy),
                (spike_x + 1, cy),
            ])
            pygame.draw.rect(surface, _NS_drakar.PALETTE["hair_light"],
                             (spike_x, cy - spike_h, 1, 2))

    def _draw_beard(surface, cx, cy, facing, phase):
        """Thick black beard."""
        beard_pts = [
            (cx - 9, cy - 1),
            (cx - 11, cy + 3),
            (cx - 8, cy + 10),
            (cx - 4, cy + 13),
            (cx + 4, cy + 13),
            (cx + 8, cy + 10),
            (cx + 11, cy + 3),
            (cx + 9, cy - 1),
            (cx + 5, cy),
            (cx - 5, cy),
        ]
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["shadow_deep"],
                         [(px + 2, py + 2) for px, py in beard_pts])
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_darkest"], beard_pts)
        _NS_drakar._poly(surface, _NS_drakar.PALETTE["hair_dark"], [
            (cx - 8, cy),
            (cx - 10, cy + 3),
            (cx - 7, cy + 10),
            (cx - 3, cy + 12),
            (cx + 3, cy + 12),
            (cx + 7, cy + 10),
            (cx + 10, cy + 3),
            (cx + 8, cy),
        ])

        # Beard highlights
        pygame.draw.line(surface, _NS_drakar.PALETTE["hair_mid"],
                         (cx + facing * 4, cy + 3), (cx + facing * 6, cy + 8), 2)
        pygame.draw.line(surface, _NS_drakar.PALETTE["hair_mid"],
                         (cx - 5, cy + 4), (cx - 7, cy + 9), 1)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["hair_light"],
                         (cx + facing * 5, cy + 5, 1, 1))

        # Beard braids / details
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_dark"],
                         (cx - 2, cy + 11, 4, 2))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["armor_light"],
                         (cx - 1, cy + 11, 2, 1))

        # Mouth (visible above beard - grimacing)
        pygame.draw.rect(surface, _NS_drakar.PALETTE["shadow_deep"],
                         (cx - 3, cy - 2, 7, 2))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["hair_darkest"],
                         (cx - 2, cy - 2, 5, 1))
        # Tusks visible
        pygame.draw.rect(surface, _NS_drakar.PALETTE["blade_light"],
                         (cx - 2, cy - 1, 1, 2))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["blade_light"],
                         (cx + 2, cy - 1, 1, 2))
        pygame.draw.rect(surface, _NS_drakar.PALETTE["blade_shine"],
                         (cx - 2, cy - 1, 1, 1))

    # ============================================================
    # AXE SLASH TRAIL
    # ============================================================
    def _draw_axe_slash_trail(surface, boss, cx, cy, progress):
        """Motion blur trail following axe arc (dramatic)."""
        # Only show during actual swing phase
        if progress < 0.42 or progress > 0.72:
            return

        facing = getattr(boss, "_drk_attack_dir", None)
        if facing is None:
            facing = boss.direction
        # Swing phase: 0.40-0.55 (fast slash), 0.55-0.70 (impact fade)
        if progress < 0.55:
            swing_t = (progress - 0.42) / 0.13
        else:
            swing_t = 1.0
        swing_t = max(0.0, min(1.0, swing_t))

        # Fade out after impact
        if progress > 0.55:
            fade = 1 - (progress - 0.55) / 0.17
            fade = max(0.0, fade)
        else:
            fade = 1.0

        # Slash arc center (in front of body)
        slash_cx = cx + facing * 30
        slash_cy = cy - 4

        slash_surf = pygame.Surface((220, 220), pygame.SRCALPHA)
        center = (110, 110)

        # Axe arc parameters - matches swing (from back-up to front-down)
        start_angle = -math.pi * 1.1  # axe way behind/above
        end_angle = math.pi * 0.4    # axe front-down

        # Number of trail steps (more = longer motion blur)
        trail_steps = 12
        # Current progress along arc
        current_a = start_angle + (end_angle - start_angle) * swing_t

        # Draw motion-blur trail from earlier positions
        radius = 55
        for step in range(trail_steps):
            step_t = step / trail_steps
            # Each step is a bit behind current position along the arc
            trail_progress = max(0.0, swing_t - step_t * 0.35)
            trail_a = start_angle + (end_angle - start_angle) * trail_progress

            # Position along arc
            tip_x = center[0] + int(math.cos(trail_a) * radius) * facing
            tip_y = center[1] + int(math.sin(trail_a) * radius)

            # Ghost axe blade curve
            fade_step = (1 - step_t) * fade
            alpha_step = _NS_drakar._alpha(240 * fade_step)
            if alpha_step <= 0:
                continue

            # Draw curved trail segment (crescent shape)
            arc_pts = []
            arc_span = 0.15  # width of each trail slice
            steps_inner = 6
            for i in range(steps_inner + 1):
                a = trail_a - arc_span + (arc_span * 2) * i / steps_inner
                # Slight radius variance for organic feel
                r_var = radius + math.sin(step + i) * 2
                px = center[0] + int(math.cos(a) * r_var) * facing
                py = center[1] + int(math.sin(a) * r_var)
                arc_pts.append((px, py))

            # Draw layered arc (fatter for closer ghosts)
            layer_thickness = max(2, int(10 * fade_step))
            for layer_i, (r_off, thick_mult, color, a_mult) in enumerate([
                (3, 1.2, _NS_drakar.PALETTE["blood_darkest"], 0.5),
                (2, 1.0, _NS_drakar.PALETTE["blood_dark"], 0.7),
                (0, 0.8, _NS_drakar.PALETTE["blood_mid"], 0.9),
                (-1, 0.6, _NS_drakar.PALETTE["blood_light"], 1.0),
                (-2, 0.4, _NS_drakar.PALETTE["blood_hot"], 1.0),
            ]):
                thick = max(1, int(layer_thickness * thick_mult))
                actual_alpha = _NS_drakar._alpha(alpha_step * a_mult)
                if actual_alpha <= 0:
                    continue
                for i in range(len(arc_pts) - 1):
                    pygame.draw.line(slash_surf,
                                     _NS_drakar._rgba(color, actual_alpha),
                                     arc_pts[i], arc_pts[i + 1], thick)

        # Leading edge (brightest, current position)
        if swing_t > 0.05:
            leading_pts = []
            steps_lead = 10
            arc_span_lead = 0.5
            for i in range(steps_lead + 1):
                a = current_a - arc_span_lead + (arc_span_lead * 2) * i / steps_lead
                px = center[0] + int(math.cos(a) * radius) * facing
                py = center[1] + int(math.sin(a) * radius)
                leading_pts.append((px, py))

            for layer_i, (thick, color) in enumerate([
                (10, _NS_drakar.PALETTE["blood_darkest"]),
                (8, _NS_drakar.PALETTE["blood_dark"]),
                (6, _NS_drakar.PALETTE["blood_mid"]),
                (4, _NS_drakar.PALETTE["blood_light"]),
                (3, _NS_drakar.PALETTE["blood_hot"]),
                (2, _NS_drakar.PALETTE["blood_shine"]),
                (1, _NS_drakar.PALETTE["white"]),
            ]):
                alpha = _NS_drakar._alpha(255 * fade)
                if alpha <= 0:
                    continue
                for i in range(len(leading_pts) - 1):
                    pygame.draw.line(slash_surf,
                                     _NS_drakar._rgba(color, alpha),
                                     leading_pts[i], leading_pts[i + 1], thick)

        # Blood droplets flying outward from arc
        for i in range(20):
            drop_angle = start_angle + (end_angle - start_angle) * (i / 20) * swing_t
            drop_r = radius + int(math.sin(swing_t * 8 + i) * 15) + 10
            dx = center[0] + int(math.cos(drop_angle) * drop_r) * facing
            dy = center[1] + int(math.sin(drop_angle) * drop_r)
            drop_alpha = _NS_drakar._alpha(240 * fade * (i / 20))
            if drop_alpha > 0:
                pygame.draw.rect(slash_surf,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], drop_alpha),
                    (dx, dy, 3, 3))
                pygame.draw.rect(slash_surf,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"], drop_alpha),
                    (dx, dy, 2, 2))
                pygame.draw.rect(slash_surf,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_shine"], drop_alpha),
                    (dx, dy, 1, 1))
                # Trail behind droplet
                pygame.draw.rect(slash_surf,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"], drop_alpha),
                    (dx, dy + 3, 1, 3))

        surface.blit(slash_surf, (slash_cx - 110, slash_cy - 110))

    def _draw_impact_burst(surface, boss, cx, cy, progress):
        """Explosive burst FX when axe hits the ground (impact phase)."""
        facing = getattr(boss, "_drk_attack_dir", None)
        if facing is None:
            facing = boss.direction
        # Impact phase: 0.53-0.70
        if progress < 0.53 or progress > 0.72:
            return

        t = (progress - 0.53) / 0.19
        t = max(0.0, min(1.0, t))
        intensity = math.sin(t * math.pi)  # peak at middle

        # Impact point (where axe hits, front-down)
        impact_x = cx + facing * 45
        impact_y = cy + 20

        # Ground shockwave rings
        for ring_i in range(3):
            ring_r = int(15 + t * 40 + ring_i * 8)
            ring_alpha = _NS_drakar._alpha(220 * intensity * (1 - ring_i * 0.3))
            if ring_alpha > 0:
                pygame.draw.ellipse(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_darkest"], ring_alpha),
                    (impact_x - ring_r, impact_y - ring_r // 3,
                     ring_r * 2, ring_r * 2 // 3), 3)
                pygame.draw.ellipse(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], ring_alpha),
                    (impact_x - ring_r + 3, impact_y - ring_r // 3 + 2,
                     ring_r * 2 - 6, ring_r * 2 // 3 - 4), 2)
                pygame.draw.ellipse(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"], ring_alpha),
                    (impact_x - ring_r + 6, impact_y - ring_r // 3 + 4,
                     ring_r * 2 - 12, ring_r * 2 // 3 - 8), 1)

        # Central bright flash
        flash_r = int(15 + intensity * 12)
        for r in range(flash_r, 0, -2):
            alpha = _NS_drakar._alpha(220 * intensity * (flash_r - r) / flash_r)
            _NS_drakar._aacircle(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"], alpha),
                (impact_x, impact_y), r)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["blood_shine"],
                             (impact_x, impact_y), 5)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["white"],
                             (impact_x, impact_y), 2)

        # Radial blood spatter shooting outward
        for i in range(14):
            angle = i * math.pi / 7
            spatter_len = int(20 + t * 40)
            for step in range(4):
                step_r = spatter_len * (0.3 + step * 0.25)
                sx = impact_x + int(math.cos(angle) * step_r)
                sy = impact_y + int(math.sin(angle) * step_r * 0.6)
                alpha = _NS_drakar._alpha(240 * intensity * (1 - step * 0.2))
                if alpha > 0:
                    size = max(1, 4 - step)
                    pygame.draw.rect(surface,
                        _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"], alpha),
                        (sx, sy, size, size))
                    pygame.draw.rect(surface,
                        _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], alpha),
                        (sx, sy, max(1, size - 1), max(1, size - 1)))
                    if step < 2:
                        pygame.draw.rect(surface,
                            _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"], alpha),
                            (sx, sy, 1, 1))

        # Vertical debris chunks rising up
        for i in range(6):
            chunk_angle = -math.pi / 2 + (i - 3) * 0.3
            chunk_t = min(1.0, t * 1.5)
            chunk_r = int(chunk_t * 35)
            cx_debris = impact_x + int(math.cos(chunk_angle) * chunk_r)
            cy_debris = impact_y + int(math.sin(chunk_angle) * chunk_r * 0.8)
            alpha = _NS_drakar._alpha(220 * (1 - chunk_t * 0.5))
            if alpha > 0:
                pygame.draw.rect(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["leather_darkest"], alpha),
                    (cx_debris - 1, cy_debris - 1, 3, 3))
                pygame.draw.rect(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["leather_dark"], alpha),
                    (cx_debris, cy_debris, 2, 2))

        # Ground crack lines radiating from impact
        if intensity > 0.5:
            for i in range(6):
                crack_angle = i * math.pi / 3 + facing * 0.2
                crack_len = int(20 + intensity * 20)
                end_x = impact_x + int(math.cos(crack_angle) * crack_len)
                end_y = impact_y + int(math.sin(crack_angle) * crack_len * 0.5)
                # Jagged crack
                prev = (impact_x, impact_y)
                segments = 4
                for seg in range(1, segments + 1):
                    t_seg = seg / segments
                    seg_x = int(impact_x + (end_x - impact_x) * t_seg
                                + math.sin(seg + i) * 3)
                    seg_y = int(impact_y + (end_y - impact_y) * t_seg
                                + math.cos(seg + i) * 2)
                    alpha = _NS_drakar._alpha(200 * intensity * (1 - t_seg * 0.5))
                    pygame.draw.line(surface,
                        _NS_drakar._rgba(_NS_drakar.PALETTE["blood_darkest"], alpha),
                        prev, (seg_x, seg_y), 3)
                    pygame.draw.line(surface,
                        _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"], alpha),
                        prev, (seg_x, seg_y), 2)
                    pygame.draw.line(surface,
                        _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], alpha),
                        prev, (seg_x, seg_y), 1)
                    prev = (seg_x, seg_y)
    # ============================================================
    # RAGE MIST (like poison mist for Vhorethzir)
    # ============================================================
    def _draw_rage_mist(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Red rage mist floating around boss."""
        strength = 1.5 if intense else 1.0

        # Mist cloud
        mist = pygame.Surface((240, 80), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(50, 3, -3):
            alpha = _NS_drakar._alpha((50 - radius) * 2.2 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_darkest"], alpha),
                    (120 - radius * 2, 40 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(35, 3, -2):
            alpha = _NS_drakar._alpha((35 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"], alpha),
                    (120 - radius, 40 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 120, cy - 20))

        # Rising red embers
        for i, offset in enumerate((-36, -24, -12, 0, 12, 24, 36, -44, 44)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 4)
            sy = cy + 8 - int(t * 36)
            alpha = _NS_drakar._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_drakar._aacircle(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"], alpha), (sx, sy), 4)
            _NS_drakar._aacircle(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], alpha), (sx, sy - 1), 3)
            _NS_drakar._aacircle(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["rage_light"], alpha), (sx, sy - 1), 1)
            pygame.draw.rect(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["rage_hot"], alpha),
                (sx, sy - 2, 1, 1))

        # Bright orange sparks
        for i in range(10):
            spark_t = (phase * 0.6 + i * 0.12) % 1.0
            ex = cx - 30 + i * 8 + int(math.sin(phase + i) * 5)
            ey = cy + 6 - int(spark_t * 30)
            alpha = _NS_drakar._alpha(230 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["rage_mid"], alpha),
                    (ex, ey, 2, 2))
                pygame.draw.rect(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["rage_hot"], alpha),
                    (ex, ey, 1, 1))

        # Trail behind
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 18 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = _NS_drakar._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_drakar._aacircle(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"], alpha),
                    (sx, sy), max(2, 8 - i))
                _NS_drakar._aacircle(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], alpha),
                    (sx, sy), max(1, 6 - i))
                pygame.draw.rect(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["rage_light"], alpha),
                    (sx, sy - 1, 2, 2))

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        """Big shadow (Vhorethzir scale)."""
        shadow = pygame.Surface((180, 40), pygame.SRCALPHA)
        for radius in range(18, 0, -1):
            alpha = max(0, (18 - radius) * 14)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (12 - radius, 20 - radius,
                                 156 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (10, 3, 5, 190), (6, 12, 168, 16))
        pygame.draw.ellipse(shadow, (40, 10, 15, 130), (14, 14, 152, 12))
        surface.blit(shadow, (x - 90, y - 20))

    def _draw_rage_aura(surface, x, y, phase):
        """Big red rage aura (Vhorethzir scale)."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((260, 220), pygame.SRCALPHA)
        for radius in range(110, 5, -5):
            alpha = _NS_drakar._alpha((110 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_drakar._aacircle(aura,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_darkest"], alpha),
                    (130, 110), radius)
        for radius in range(75, 5, -4):
            alpha = _NS_drakar._alpha((75 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_drakar._aacircle(aura,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["rage_dark"], alpha),
                    (130, 110), radius)
        for radius in range(45, 5, -3):
            alpha = _NS_drakar._alpha((45 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_drakar._aacircle(aura,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["rage_mid"], alpha),
                    (130, 110), radius)
        surface.blit(aura, (x - 130, y - 110))

        # Rising floating embers around
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 50 + int(math.sin(phase + i) * 14)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 10 + int(math.sin(angle) * radius * 0.5)
            color = _NS_drakar.PALETTE["blood_mid"] if i % 2 else _NS_drakar.PALETTE["rage_mid"]
            hot_color = _NS_drakar.PALETTE["blood_hot"] if i % 2 else _NS_drakar.PALETTE["rage_hot"]
            pygame.draw.rect(surface, color, (sx, sy, 3, 3))
            pygame.draw.rect(surface, hot_color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["white"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Big red runic ground ring (Vhorethzir scale)."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((200, 68), pygame.SRCALPHA)
        pygame.draw.ellipse(ring,
            _NS_drakar._rgba(_NS_drakar.PALETTE["blood_darkest"], 200),
            (5, 22, 190, 34), 4)
        pygame.draw.ellipse(ring,
            _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"], 220),
            (14, 26, 172, 28), 3)
        pygame.draw.ellipse(ring,
            _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], 230),
            (30, 30, 140, 20), 2)
        pygame.draw.ellipse(ring,
            _NS_drakar._rgba(_NS_drakar.PALETTE["rage_dark"], 180),
            (46, 32, 108, 16), 1)

        # Runes around
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 100 + int(math.cos(angle) * 55)
            y1 = 39 + int(math.sin(angle) * 10)
            x2 = 100 + int(math.cos(angle) * 88)
            y2 = 39 + int(math.sin(angle) * 15)
            pygame.draw.line(ring,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_light"], 220),
                (x1, y1), (x2, y2), 2)
            pygame.draw.rect(ring,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"], 240),
                (x2, y2, 2, 2))

        if skill:
            pygame.draw.ellipse(ring,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"],
                                 _NS_drakar._alpha(160 * pulse)),
                (14, 16, 172, 44), 2)
        surface.blit(ring, (x - 100, y - 34))

    # ============================================================
    # SKILL Q: BATTLE HUNGER
    # ============================================================
    def _draw_battlehunger_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_drakar._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_darkest"], 200),
                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"], 180),
                (tx - r + 4, ty - r // 3 + 3,
                 r * 2 - 8, r * 2 // 3 - 6))
            pygame.draw.ellipse(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["rage_mid"], 130),
                (tx - r + 10, ty - r // 3 + 6,
                 r * 2 - 20, r * 2 // 3 - 12))

    def _draw_battlehunger_foreground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_drakar._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 3))

        if r < 5:
            return

        # Flame columns
        for i in range(8):
            col_angle = i * math.pi * 2 / 8 + phase * 0.15
            col_dist = int(r * 0.55)
            col_x = tx + int(math.cos(col_angle) * col_dist)
            col_y_base = ty + int(math.sin(col_angle) * col_dist * 0.4)

            for layer in range(6):
                layer_t = (phase * 0.7 + i * 0.3 + layer * 0.15) % 1.0
                layer_y = col_y_base - int(layer_t * 36)
                layer_alpha = _NS_drakar._alpha(220 * (1 - layer_t))
                layer_w = int(6 + layer_t * 3)
                layer_h = int(4 + layer_t * 3)

                pygame.draw.ellipse(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_darkest"], layer_alpha),
                    (col_x - layer_w, layer_y - layer_h,
                     layer_w * 2, layer_h * 2))
                pygame.draw.ellipse(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"], layer_alpha),
                    (col_x - layer_w + 1, layer_y - layer_h + 1,
                     max(1, layer_w * 2 - 2), max(1, layer_h * 2 - 2)))
                pygame.draw.ellipse(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["rage_mid"], layer_alpha),
                    (col_x - layer_w + 2, layer_y - layer_h + 2,
                     max(1, layer_w * 2 - 4), max(1, layer_h * 2 - 4)))
                pygame.draw.rect(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["rage_light"], layer_alpha),
                    (col_x, layer_y - 1, 1, 1))
                pygame.draw.rect(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["rage_hot"], layer_alpha),
                    (col_x, layer_y - 2, 1, 1))

        # Central core
        core_pulse = math.sin(phase * 3) * 0.4 + 0.6
        for cr in range(10, 0, -1):
            alpha = _NS_drakar._alpha(200 * (10 - cr) / 10 * core_pulse)
            _NS_drakar._aacircle(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], alpha),
                (tx, ty), cr)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["rage_light"], (tx, ty), 3)
        _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["rage_hot"], (tx, ty), 1)

        # Blood spatters
        for i in range(24):
            angle = i * math.pi * 2 / 24 + phase * 0.4
            sp_r = int(r * (0.4 + (i % 3) * 0.2))
            sx = tx + int(math.cos(angle) * sp_r)
            sy = ty + int(math.sin(angle) * sp_r * 0.4)
            pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_light"], (sx, sy, 1, 1))

    # ============================================================
    # SKILL W: COUNTER HELIX
    # ============================================================
    def _draw_counterhelix_ground(surface, boss, x, y, timer, phase):
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 + progress * 30)
        alpha = _NS_drakar._alpha(240 * (1 - progress * 0.5))
        pygame.draw.ellipse(surface,
            _NS_drakar._rgba(_NS_drakar.PALETTE["blood_darkest"], alpha),
            (x - r, y + 76 - r // 3, r * 2, r * 2 // 3), 4)
        pygame.draw.ellipse(surface,
            _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], alpha),
            (x - r + 5, y + 76 - r // 3 + 4,
             r * 2 - 10, r * 2 // 3 - 8), 3)
        pygame.draw.ellipse(surface,
            _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"], alpha),
            (x - r + 10, y + 76 - r // 3 + 7,
             r * 2 - 20, r * 2 // 3 - 14), 2)

        # Spinning arc trails
        spin = progress * math.pi * 6
        for i in range(4):
            a = spin + i * math.pi / 2
            arc_pts = []
            for step in range(12):
                st = step / 11
                arc_a = a + st * math.pi / 3
                ax = x + int(math.cos(arc_a) * (r - 6))
                ay = y + 76 + int(math.sin(arc_a) * (r - 6) * 0.4)
                arc_pts.append((ax, ay))
            for k in range(len(arc_pts) - 1):
                pygame.draw.line(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_light"], alpha),
                    arc_pts[k], arc_pts[k + 1], 3)
                pygame.draw.line(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"], alpha),
                    arc_pts[k], arc_pts[k + 1], 1)

    # ============================================================
    # SKILL E: BERSERKER'S CALL
    # ============================================================
    def _draw_berserkerscall_ground(surface, boss, x, y, timer, phase):
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress > 0.2:
            t = (progress - 0.2) / 0.8
            r = int(45 + t * 80)
            base_alpha = _NS_drakar._alpha(240 * (1 - t))
            for i in range(3):
                a = _NS_drakar._alpha(base_alpha - i * 60)
                if a > 0:
                    pygame.draw.ellipse(surface,
                        _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], a),
                        (x - r - i * 4, y + 76 - r // 3 - i,
                         (r + i * 4) * 2, (r + i * 4) * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"], base_alpha),
                (x - r + 5, y + 76 - r // 3 + 4,
                 r * 2 - 10, r * 2 // 3 - 8), 2)

    def _draw_berserkerscall_foreground(surface, boss, x, y, timer, phase):
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            t = progress / 0.3
            glow_r = int(12 + t * 12)
            for r in range(glow_r + 6, 0, -1):
                alpha = _NS_drakar._alpha(180 * (glow_r + 6 - r) / (glow_r + 6) * t)
                _NS_drakar._aacircle(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"], alpha),
                    (x, y - 4), r)
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["blood_mid"], (x, y - 4), 10)
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["rage_light"], (x, y - 4), 6)
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["rage_hot"], (x, y - 4), 3)
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["white"], (x, y - 4), 1)

            for i in range(12):
                angle = i * math.pi / 6
                mist_x = x + int(math.cos(angle) * 30 * t)
                mist_y = y - 8 + int(math.sin(angle) * 25 * t)
                alpha = _NS_drakar._alpha(200 * t)
                _NS_drakar._aacircle(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], alpha),
                    (mist_x, mist_y), 4)
                _NS_drakar._aacircle(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["rage_light"], alpha),
                    (mist_x, mist_y), 2)
        else:
            t = (progress - 0.3) / 0.7
            wave_r = int(t * 130)

            for i in range(28):
                angle = i * math.pi * 2 / 28
                px = x + int(math.cos(angle) * wave_r)
                py = y - 8 + int(math.sin(angle) * wave_r * 0.7)
                alpha = _NS_drakar._alpha(240 * (1 - t))
                _NS_drakar._aacircle(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"], alpha),
                    (px, py), 5)
                _NS_drakar._aacircle(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], alpha),
                    (px, py), 4)
                _NS_drakar._aacircle(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["rage_light"], alpha),
                    (px, py), 2)
                pygame.draw.rect(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["rage_hot"], alpha),
                    (px, py, 2, 2))
                pygame.draw.rect(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["white"], alpha),
                    (px, py, 1, 1))

            for i in range(14):
                angle = i * math.pi / 7
                inner_r = int(wave_r * 0.65)
                outer_r = wave_r
                p1 = (x + int(math.cos(angle) * inner_r),
                      y - 8 + int(math.sin(angle) * inner_r * 0.7))
                p2 = (x + int(math.cos(angle) * outer_r),
                      y - 8 + int(math.sin(angle) * outer_r * 0.7))
                alpha = _NS_drakar._alpha(220 * (1 - t))
                pygame.draw.line(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_light"], alpha),
                    p1, p2, 3)
                pygame.draw.line(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["rage_hot"], alpha),
                    p1, p2, 1)

    # ============================================================
    # SKILL R: CULLING BLADE
    # ============================================================
    def _draw_cullingblade_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_drakar._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.4:
            t = progress / 0.4
            r = int(50 * t)
            alpha = _NS_drakar._alpha(200 * t)
            pygame.draw.ellipse(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_darkest"], alpha),
                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 4)
            pygame.draw.ellipse(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], alpha),
                (tx - r + 4, ty - r // 3 + 3,
                 r * 2 - 8, r * 2 // 3 - 6), 3)
            for i in range(10):
                angle = i * math.pi / 5 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_light"], (sx, sy, 3, 3))
                pygame.draw.rect(surface, _NS_drakar.PALETTE["blood_hot"], (sx, sy, 2, 2))
        else:
            t = (progress - 0.4) / 0.6
            r = int(50 + t * 30)
            alpha = _NS_drakar._alpha(240 * (1 - t * 0.5))
            pygame.draw.ellipse(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_darkest"], alpha),
                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"], alpha),
                (tx - r + 5, ty - r // 3 + 4,
                 r * 2 - 10, r * 2 // 3 - 8))

    def _draw_cullingblade_foreground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_drakar._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.4:
            t = progress / 0.4
            facing = boss.direction
            charge_x = x + facing * 40
            charge_y = y - 6
            cr = int(8 + t * 10)
            for r in range(cr + 7, 0, -1):
                alpha = _NS_drakar._alpha(220 * (cr + 7 - r) / (cr + 7))
                _NS_drakar._aacircle(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_darkest"], alpha),
                    (charge_x, charge_y), r)
            for r in range(cr, 0, -1):
                alpha = _NS_drakar._alpha(240 * (cr - r + 1) / cr)
                _NS_drakar._aacircle(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], alpha),
                    (charge_x, charge_y), r)
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["blood_light"],
                                 (charge_x, charge_y), max(1, cr - 3))
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["rage_light"],
                                 (charge_x, charge_y), max(1, cr - 5))
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["rage_hot"],
                                 (charge_x, charge_y), max(1, cr - 7))
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["white"],
                                 (charge_x, charge_y), max(1, cr - 9))

            alpha_warn = _NS_drakar._alpha(180 * t)
            _NS_drakar._aacircle(surface,
                _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"], alpha_warn),
                (tx, ty), 10, 2)

        elif progress < 0.65:
            t = (progress - 0.4) / 0.25
            intensity = math.sin(t * math.pi)
            slash_len = int(65 + t * 25)

            for slash_dir in [(1, 1), (1, -1)]:
                dx, dy = slash_dir
                p1 = (tx - dx * slash_len, ty - dy * slash_len)
                p2 = (tx + dx * slash_len, ty + dy * slash_len)

                for layer_i, (thick, color, a_mult) in enumerate([
                    (12, _NS_drakar.PALETTE["blood_darkest"], 0.6),
                    (9, _NS_drakar.PALETTE["blood_dark"], 0.8),
                    (6, _NS_drakar.PALETTE["blood_mid"], 1.0),
                    (4, _NS_drakar.PALETTE["blood_light"], 1.0),
                    (2, _NS_drakar.PALETTE["blood_hot"], 1.0),
                    (1, _NS_drakar.PALETTE["blood_shine"], 1.0),
                ]):
                    alpha = _NS_drakar._alpha(255 * intensity * a_mult)
                    if alpha <= 0:
                        continue
                    pygame.draw.line(surface,
                        _NS_drakar._rgba(color, alpha), p1, p2, thick)

            for r in range(25, 0, -1):
                alpha = _NS_drakar._alpha(240 * intensity * (25 - r) / 25)
                _NS_drakar._aacircle(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"], alpha),
                    (tx, ty), r)
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["blood_shine"],
                                 (tx, ty), 10)
            _NS_drakar._aacircle(surface, _NS_drakar.PALETTE["white"], (tx, ty), 5)

            for i in range(20):
                angle = i * math.pi / 10
                spatter_len = int(slash_len * 0.8)
                sx = tx + int(math.cos(angle) * spatter_len)
                sy = ty + int(math.sin(angle) * spatter_len)
                alpha = _NS_drakar._alpha(240 * intensity)
                pygame.draw.rect(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], alpha),
                    (sx, sy, 4, 4))
                pygame.draw.rect(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_hot"], alpha),
                    (sx, sy, 3, 3))
                pygame.draw.rect(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_shine"], alpha),
                    (sx, sy, 1, 1))
        else:
            t = (progress - 0.65) / 0.35
            for i in range(18):
                fall_t = (phase * 0.5 + i * 0.1) % 1.0
                rx = tx + int(math.sin(phase + i) * 40)
                ry = ty - 24 + int(fall_t * 40)
                alpha = _NS_drakar._alpha(220 * (1 - t) * (1 - fall_t * 0.5))
                if alpha > 0:
                    pygame.draw.rect(surface,
                        _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"], alpha),
                        (rx, ry, 3, 4))
                    pygame.draw.rect(surface,
                        _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], alpha),
                        (rx, ry, 2, 3))

            for slash_dir in [(1, 1), (1, -1)]:
                dx, dy = slash_dir
                slash_len = 40
                p1 = (tx - dx * slash_len, ty - dy * slash_len)
                p2 = (tx + dx * slash_len, ty + dy * slash_len)
                alpha = _NS_drakar._alpha(150 * (1 - t))
                pygame.draw.line(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_dark"], alpha),
                    p1, p2, 3)
                pygame.draw.line(surface,
                    _NS_drakar._rgba(_NS_drakar.PALETTE["blood_mid"], alpha),
                    p1, p2, 2)

# ====================================================================
# ABADDON
# ====================================================================
class _NS_abaddon:
    """Namespace abaddon - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Abaddon inspired dark purple / cyan flame
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Cape / cloth - deep purple
        "cape_darkest":   (18,   8,  32),
        "cape_dark":      (35,  20,  62),
        "cape_mid":       (60,  38, 105),
        "cape_light":     (95,  70, 155),
        "cape_high":      (140, 115, 195),
        "cape_shine":     (185, 165, 225),

        # Armor - dark purple/black with gold trim
        "armor_darkest":  (12,   8,  22),
        "armor_dark":     (28,  20,  48),
        "armor_mid":      (55,  42,  85),
        "armor_light":    (95,  78, 130),
        "armor_high":     (150, 130, 180),

        # Gold trim
        "gold_darkest":   (65,  42,  10),
        "gold_dark":      (115, 85,  25),
        "gold_mid":       (175, 140, 45),
        "gold_light":     (225, 190, 85),
        "gold_shine":     (250, 225, 145),

        # Horse body - dark blue-purple
        "horse_darkest":  (10,  15,  30),
        "horse_dark":     (25,  35,  60),
        "horse_mid":      (50,  70, 105),
        "horse_light":    (85, 115, 155),
        "horse_high":     (135, 170, 200),

        # Cyan flame / mist - the signature color
        "flame_darkest":  (5,   45,  55),
        "flame_dark":     (15,  95, 115),
        "flame_mid":      (40, 170, 185),
        "flame_light":    (95, 230, 235),
        "flame_bright":   (160, 250, 250),
        "flame_hot":      (215, 255, 255),
        "flame_white":    (240, 255, 255),

        # Sword blade - cyan energy blade
        "blade_darkest":  (30,  55,  70),
        "blade_dark":     (60, 120, 145),
        "blade_mid":      (110, 190, 210),
        "blade_light":    (170, 235, 240),
        "blade_shine":    (220, 250, 250),

        # Purple magic (for skills)
        "magic_darkest":  (20,   5,  50),
        "magic_dark":     (55,  25, 115),
        "magic_mid":      (105, 60, 180),
        "magic_light":    (165, 120, 225),
        "magic_bright":   (210, 175, 250),
        "magic_hot":      (240, 220, 255),

        # Eye glow
        "eye_dark":       (30,  90, 100),
        "eye_mid":        (90, 200, 205),
        "eye_bright":     (170, 245, 245),
        "eye_hot":        (230, 255, 255),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (3,   4,   8),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_abaddon._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_abaddon.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_abaddon._clamp(color)
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
        color = _NS_abaddon._clamp(color)
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
        color = _NS_abaddon._clamp(color)
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
        color = _NS_abaddon._clamp(color)
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
    # Cyan flame helper
    # ---------------------------------------------------------------------------
    def _draw_cyan_flame(surface, x, y, size, phase, alpha=255):
        """Draw a cyan mist flame particle."""
        flick = math.sin(phase * 3) * 0.15 + 1.0
        s = int(size * flick)
        if s < 1:
            return
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_darkest"], alpha // 3), (x, y), s + 3)
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_dark"], alpha // 2), (x, y), s + 1)
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], alpha), (x, y), s)
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_light"], alpha), (x, y - 1),
                  max(1, s - 2))
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], min(255, alpha)),
                  (x, y - 2), max(1, s - 4))
        if s > 3:
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_hot"], min(255, alpha)),
                      (x, y - 3), max(1, s - 6))


    def _draw_flame_streamer(surface, x, y, height, phase, alpha=220):
        """Draw a rising cyan flame streamer."""
        for i in range(height):
            t = i / max(1, height)
            wave = math.sin(phase * 3 + t * 5) * 2
            size = int(3 * (1 - t * 0.7))
            if size < 1:
                break
            fx = x + int(wave)
            fy = y - i
            f_alpha = int(alpha * (1 - t * 0.6))
            _NS_abaddon._draw_cyan_flame(surface, fx, fy, size, phase, f_alpha)


    # ---------------------------------------------------------------------------
    # PROJECTILE / EFFECT SYSTEM
    # ---------------------------------------------------------------------------
    class MistCoilProjectile:
        """Q - Purple/cyan orb projectile."""
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
            if len(self.trail) > 14:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 3:
                return

            # Long misty trail (purple/cyan)
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 15)
                r = max(1, 6 - (len(self.trail) - i) // 2)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_dark"], alpha), (tx, ty), r + 2)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_mid"], alpha), (tx, ty), r)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], alpha // 2),
                          (tx, ty), max(1, r - 1))

            if self.alive:
                px, py = int(self.x), int(self.y)
                # Multi-layer orb
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_darkest"], 180), (px, py), 10)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_dark"], 220), (px, py), 8)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_mid"], 240), (px, py), 6)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], 240), (px, py), 4)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], 250), (px, py), 3)
                _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"], (px, py), 2)
                _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_white"], (px, py), 1)

                # Mist trails
                for i in range(4):
                    angle = phase * 4 + i * math.pi / 2
                    sx = px + int(math.cos(angle) * 10)
                    sy = py + int(math.sin(angle) * 10)
                    _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_light"], 200), (sx, sy), 2)
                    _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"], (sx, sy), 1)


    class DarknessGaleProjectile:
        """E - Dark wave/gale that travels forward."""
        def __init__(self, sx, sy, direction, max_dist=250):
            self.x = float(sx)
            self.y = float(sy)
            self.direction = direction
            self.max_dist = max_dist
            self.speed = 11.0
            self.alive = True
            self.age = 0
            self.max_age = 25

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.x += self.speed * self.direction
            if self.age >= self.max_age:
                self.alive = False

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            t = self.age / self.max_age
            alpha = int(255 * (1 - t * 0.5))
            px, py = int(self.x), int(self.y)

            # Elongated gale/wind streak
            for i in range(-6, 7):
                # Multiple parallel streaks
                for streak_off in (-4, 0, 4):
                    streak_y = py + i * 2 + streak_off
                    # Length varies
                    for length_i in range(20):
                        lt = length_i / 20
                        lx = px - int(lt * 40) * self.direction
                        ly = streak_y + int(math.sin(lt * 5 + phase + i) * 2)

                        w_alpha = int(alpha * (1 - abs(i) / 7) * (1 - lt * 0.4))
                        if w_alpha <= 0:
                            continue

                        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_dark"], w_alpha),
                                  (lx, ly), 2)
                        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_dark"], w_alpha),
                                  (lx, ly), 1)

            # Bright forward core
            for i in range(-4, 5):
                core_y = py + i * 2
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], alpha),
                          (px, core_y), 3)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], alpha),
                          (px, core_y), 2)
                _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"], (px, core_y), 1)

            # Bright tip
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], alpha),
                      (px + 8 * self.direction, py), 4)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"],
                      (px + 8 * self.direction, py), 3)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_white"],
                      (px + 8 * self.direction, py), 1)


    class DeathSeverWave:
        """R - Purple crescent wave."""
        def __init__(self, sx, sy, direction, max_dist=200):
            self.x = float(sx)
            self.y = float(sy)
            self.direction = direction
            self.max_dist = max_dist
            self.speed = 9.0
            self.alive = True
            self.age = 0
            self.max_age = 22

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.x += self.speed * self.direction
            if self.age >= self.max_age:
                self.alive = False

        def draw(self, surface, phase):
            if not self.alive:
                return
            t = self.age / self.max_age
            alpha = int(255 * (1 - t * 0.4))
            px, py = int(self.x), int(self.y)

            # Purple crescent wave
            for i in range(-14, 15):
                curve = math.cos(i * 0.2) * 8
                vy = py + i * 2
                vx = px + int(curve) * self.direction

                w_alpha = int(alpha * (1 - abs(i) / 15))
                if w_alpha <= 0:
                    continue

                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_darkest"], w_alpha),
                          (vx, vy), 5)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_dark"], w_alpha),
                          (vx, vy), 4)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_mid"], w_alpha),
                          (vx, vy), 3)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_light"], w_alpha),
                          (vx, vy), 2)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_bright"], w_alpha),
                          (vx, vy), 1)

            # Bright core arc
            for i in range(-12, 13):
                curve = math.cos(i * 0.2) * 8
                vy = py + i * 2
                vx = px + int(curve) * self.direction
                core_alpha = int(alpha * (1 - abs(i) / 13))
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_hot"], core_alpha),
                          (vx, vy), 2)
                _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["white"], (vx, vy), 1)

            # Trailing purple sparks
            for i in range(6):
                angle = phase * 3 + i * math.pi / 3
                r = 15 + int(math.sin(phase + i) * 4)
                sx = px + int(math.cos(angle) * r) * self.direction
                sy = py + int(math.sin(angle) * r)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_bright"], alpha), (sx, sy), 2)
                _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["magic_hot"], (sx, sy), 1)


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_ab_last_x"):
            boss._ab_last_x = boss.x
            boss._ab_last_y = boss.y
            return False
        dx = abs(boss.x - boss._ab_last_x)
        dy = abs(boss.y - boss._ab_last_y)
        boss._ab_last_x = boss.x
        boss._ab_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_ab_prev_timer", 0))
        active = bool(getattr(boss, "_ab_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._ab_attack_active = True
            boss._ab_attack_frame = 0
            active = True
        elif active:
            boss._ab_attack_frame = int(getattr(boss, "_ab_attack_frame", 0)) + 1
            if boss._ab_attack_frame > cooldown:
                boss._ab_attack_active = False
                boss._ab_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._ab_attack_active = False
            boss._ab_attack_frame = 0
            active = False

        boss._ab_prev_timer = timer
        boss._ab_attack_progress = (
            min(1.0, getattr(boss, "_ab_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_ab_projectiles"):
            boss._ab_projectiles = []
        for p in boss._ab_projectiles:
            p.update()
            p.draw(surface, phase)
        boss._ab_projectiles = [p for p in boss._ab_projectiles
                               if p.alive or p.age < 8]


    def _spawn_mist_coil(boss, x, y):
        if not hasattr(boss, "_ab_projectiles"):
            boss._ab_projectiles = []
        tx, ty = _NS_abaddon._target_position(boss, x, y)
        sx = x + 26 * boss.direction
        sy = y - 10
        boss._ab_projectiles.append(_NS_abaddon.MistCoilProjectile(sx, sy, tx, ty, speed=6.5))


    def _spawn_darkness_gale(boss, x, y):
        if not hasattr(boss, "_ab_projectiles"):
            boss._ab_projectiles = []
        sx = x + 30 * boss.direction
        sy = y - 8
        boss._ab_projectiles.append(_NS_abaddon.DarknessGaleProjectile(sx, sy, boss.direction))


    def _spawn_death_sever(boss, x, y):
        if not hasattr(boss, "_ab_projectiles"):
            boss._ab_projectiles = []
        sx = x + 30 * boss.direction
        sy = y - 8
        boss._ab_projectiles.append(_NS_abaddon.DeathSeverWave(sx, sy, boss.direction))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_abaddon(surface, boss, x, y):
        """Entry point."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_abaddon._detect_moving(boss)
        _NS_abaddon._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_ab_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # ---------- Background layers ----------
        _NS_abaddon._draw_dark_aura(surface, x, y, pulse)
        _NS_abaddon._draw_ground_runes(surface, x, y + 48, pulse, active_skill)

        # ---------- Character body ----------
        if active_skill == "q":
            _NS_abaddon._draw_abaddon_mist_coil(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_abaddon._draw_abaddon_darkness_gale(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_abaddon._draw_abaddon_death_sever(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_abaddon._draw_abaddon_melee_attack(surface, boss, x, y)
        elif moving:
            _NS_abaddon._draw_abaddon_walk(surface, boss, x, y)
        else:
            _NS_abaddon._draw_abaddon_idle(surface, boss, x, y)

        # Aphotic Shield goes over body
        if active_skill == "w":
            _NS_abaddon._draw_aphotic_shield(surface, boss, x, y, skill_timer, pulse)

        # ---------- Projectiles ----------
        _NS_abaddon._manage_projectiles(boss, surface, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_abaddon_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_abaddon._draw_shadow(surface, x, y + 58)
        _NS_abaddon._draw_horse_flame_base(surface, x, y + 45, boss.pulse)
        _NS_abaddon._draw_abaddon_full(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_abaddon_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(abs(math.sin(phase * 1.3)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_abaddon._draw_shadow(surface, x + sway, y + 58)
        _NS_abaddon._draw_horse_flame_base(surface, x + sway, y + 45, phase, trail=True,
                              facing=boss.direction)
        _NS_abaddon._draw_abaddon_full(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_abaddon_melee_attack(surface, boss, x, y):
        """Sword swing on horseback."""
        progress = getattr(boss, "_ab_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        lunge = int(math.sin(progress * math.pi) * 4) * boss.direction
        _NS_abaddon._draw_shadow(surface, x + lunge, y + 58)
        _NS_abaddon._draw_horse_flame_base(surface, x + lunge, y + 45, boss.pulse, intense=True)
        _NS_abaddon._draw_abaddon_full(surface, x + lunge, y, boss.direction, boss.pulse,
                          "melee", progress)
        _NS_abaddon._draw_sword_swing_trail(surface, x + lunge, y - 8, boss.direction, progress)


    def _draw_abaddon_mist_coil(surface, boss, x, y, timer, phase):
        """Q - Mist Coil cast."""
        cast_duration = 45
        elapsed = cast_duration - timer
        progress = max(0.0, min(1.0, elapsed / cast_duration))

        if 0.3 < progress < 0.4 and not getattr(boss, "_ab_coil_spawned", False):
            _NS_abaddon._spawn_mist_coil(boss, x, y)
            boss._ab_coil_spawned = True
        if progress < 0.2 or progress > 0.9:
            boss._ab_coil_spawned = False

        _NS_abaddon._draw_shadow(surface, x, y + 58)
        _NS_abaddon._draw_horse_flame_base(surface, x, y + 45, phase, intense=True)
        _NS_abaddon._draw_abaddon_full(surface, x, y, boss.direction, phase, "cast", progress)

        # Casting glow on sword tip
        if 0.15 < progress < 0.5:
            sword_x = x + 32 * boss.direction
            sword_y = y - 20
            glow_pulse = math.sin(phase * 4) * 0.3 + 0.7
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_dark"], 180),
                      (sword_x, sword_y), int(12 * glow_pulse))
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_mid"], 220),
                      (sword_x, sword_y), int(8 * glow_pulse))
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], 240),
                      (sword_x, sword_y), int(5 * glow_pulse))
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"],
                      (sword_x, sword_y), max(1, int(3 * glow_pulse)))


    def _draw_abaddon_darkness_gale(surface, boss, x, y, timer, phase):
        """E - Darkness Gale cast."""
        cast_duration = 40
        elapsed = cast_duration - timer
        progress = max(0.0, min(1.0, elapsed / cast_duration))

        if 0.3 < progress < 0.4 and not getattr(boss, "_ab_gale_spawned", False):
            _NS_abaddon._spawn_darkness_gale(boss, x, y)
            boss._ab_gale_spawned = True
        if progress < 0.2 or progress > 0.9:
            boss._ab_gale_spawned = False

        _NS_abaddon._draw_shadow(surface, x, y + 58)
        _NS_abaddon._draw_horse_flame_base(surface, x, y + 45, phase, intense=True)
        _NS_abaddon._draw_abaddon_full(surface, x, y, boss.direction, phase, "cast", progress)


    def _draw_abaddon_death_sever(surface, boss, x, y, timer, phase):
        """R - Death Sever cast."""
        cast_duration = 50
        elapsed = cast_duration - timer
        progress = max(0.0, min(1.0, elapsed / cast_duration))

        if 0.35 < progress < 0.45 and not getattr(boss, "_ab_sever_spawned", False):
            _NS_abaddon._spawn_death_sever(boss, x, y)
            boss._ab_sever_spawned = True
        if progress < 0.2 or progress > 0.9:
            boss._ab_sever_spawned = False

        lunge = int(math.sin(progress * math.pi) * 6) * boss.direction
        _NS_abaddon._draw_shadow(surface, x + lunge, y + 58)
        _NS_abaddon._draw_horse_flame_base(surface, x + lunge, y + 45, phase, intense=True)
        _NS_abaddon._draw_abaddon_full(surface, x + lunge, y, boss.direction, phase,
                          "melee", progress)
        _NS_abaddon._draw_sword_purple_trail(surface, x + lunge, y - 8, boss.direction,
                                 progress, phase)


    # ===================================================================
    # FULL COMPOSITE - Abaddon + Horse
    # ===================================================================
    def _draw_abaddon_full(surface, cx, cy, facing, phase, action,
                          attack_progress=0):
        """Draw horse + Abaddon rider composition."""
        # Horse (drawn first as background)
        _NS_abaddon._draw_horse(surface, cx, cy + 15, facing, phase)

        # Abaddon rider on top
        _NS_abaddon._draw_abaddon_rider(surface, cx, cy - 8, facing, phase, action,
                           attack_progress)


    # ===================================================================
    # HORSE (ghostly mount)
    # ===================================================================
    def _draw_horse(surface, cx, cy, facing, phase):
        """Ghostly horse mount with cyan flames."""
        step = math.sin(phase * 1.5) * 1

        # Horse body (elongated oval)
        body_pts = [
            (cx - 25 * facing, cy - 2),
            (cx - 22 * facing, cy - 10),
            (cx - 10 * facing, cy - 12),
            (cx + 10 * facing, cy - 12),
            (cx + 20 * facing, cy - 10),
            (cx + 25 * facing, cy - 5),
            (cx + 23 * facing, cy + 8),
            (cx + 12 * facing, cy + 12),
            (cx - 12 * facing, cy + 12),
            (cx - 22 * facing, cy + 8),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in body_pts])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_darkest"], body_pts)
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_dark"], [
            (cx - 23 * facing, cy - 1),
            (cx - 20 * facing, cy - 8),
            (cx - 10 * facing, cy - 10),
            (cx + 10 * facing, cy - 10),
            (cx + 18 * facing, cy - 8),
            (cx + 23 * facing, cy - 4),
            (cx + 21 * facing, cy + 7),
            (cx + 10 * facing, cy + 10),
            (cx - 10 * facing, cy + 10),
            (cx - 20 * facing, cy + 7),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_mid"], [
            (cx - 18 * facing, cy - 3),
            (cx - 15 * facing, cy - 7),
            (cx - 5 * facing, cy - 8),
            (cx + 5 * facing, cy - 8),
            (cx + 15 * facing, cy - 7),
            (cx + 20 * facing, cy - 3),
            (cx + 15 * facing, cy + 6),
            (cx - 15 * facing, cy + 6),
        ])

        # Body highlight (top of back)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["horse_light"], (cx - 5 * facing, cy - 7), 3)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["horse_high"], (cx - 6 * facing, cy - 8), 1)

        # ===== FRONT LEGS =====
        for leg_off in (-8, 0):
            lx = cx + (12 + leg_off) * facing
            # Upper leg
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["shadow_deep"],
                    (lx + 1, cy + 11), (lx + int(step) + 1, cy + 20), 4)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["horse_darkest"],
                    (lx, cy + 11), (lx + int(step), cy + 20), 3)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["horse_dark"],
                    (lx, cy + 11), (lx + int(step), cy + 20), 2)
            # Lower leg (dissolves into flame)
            for h in range(8):
                t = h / 8
                fy = cy + 20 + h
                fx = lx + int(step)
                f_alpha = int(200 * (1 - t * 0.5))
                _NS_abaddon._draw_cyan_flame(surface, fx, fy, max(1, 3 - h // 2),
                                phase + h, f_alpha)

        # ===== BACK LEGS =====
        for leg_off in (-8, 0):
            lx = cx + (-12 - leg_off) * facing
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["shadow_deep"],
                    (lx + 1, cy + 11), (lx - int(step) + 1, cy + 20), 4)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["horse_darkest"],
                    (lx, cy + 11), (lx - int(step), cy + 20), 3)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["horse_dark"],
                    (lx, cy + 11), (lx - int(step), cy + 20), 2)
            # Flame at hoof
            for h in range(8):
                t = h / 8
                fy = cy + 20 + h
                fx = lx - int(step)
                f_alpha = int(200 * (1 - t * 0.5))
                _NS_abaddon._draw_cyan_flame(surface, fx, fy, max(1, 3 - h // 2),
                                phase + h + 2, f_alpha)

        # ===== HORSE NECK =====
        neck_x = cx + 20 * facing
        neck_y = cy - 8
        neck_top_x = cx + 26 * facing
        neck_top_y = cy - 20

        # Neck shape
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_darkest"], [
            (neck_x - 3 * facing, neck_y),
            (neck_x + 3 * facing, neck_y - 2),
            (neck_top_x + 4 * facing, neck_top_y),
            (neck_top_x - 3 * facing, neck_top_y + 3),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_dark"], [
            (neck_x - 2 * facing, neck_y - 1),
            (neck_x + 3 * facing, neck_y - 2),
            (neck_top_x + 3 * facing, neck_top_y + 1),
            (neck_top_x - 2 * facing, neck_top_y + 3),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_mid"], [
            (neck_x, neck_y - 1),
            (neck_x + 2 * facing, neck_y - 2),
            (neck_top_x + 2 * facing, neck_top_y + 1),
            (neck_top_x - 1 * facing, neck_top_y + 3),
        ])

        # ===== HORSE HEAD =====
        head_x = neck_top_x + 2 * facing
        head_y = neck_top_y

        # Head shape (elongated)
        head_pts = [
            (head_x - 5 * facing, head_y - 3),
            (head_x + 3 * facing, head_y - 5),
            (head_x + 12 * facing, head_y - 2),
            (head_x + 13 * facing, head_y + 3),
            (head_x + 8 * facing, head_y + 6),
            (head_x - 3 * facing, head_y + 5),
            (head_x - 6 * facing, head_y + 2),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"], [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_darkest"], head_pts)
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_dark"], [
            (head_x - 4 * facing, head_y - 2),
            (head_x + 3 * facing, head_y - 4),
            (head_x + 11 * facing, head_y - 1),
            (head_x + 12 * facing, head_y + 3),
            (head_x + 7 * facing, head_y + 5),
            (head_x - 3 * facing, head_y + 4),
            (head_x - 5 * facing, head_y + 1),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_mid"], [
            (head_x - 2 * facing, head_y - 1),
            (head_x + 2 * facing, head_y - 3),
            (head_x + 9 * facing, head_y - 1),
            (head_x + 10 * facing, head_y + 2),
            (head_x + 5 * facing, head_y + 4),
            (head_x - 2 * facing, head_y + 3),
        ])

        # Horse ears
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_darkest"], [
            (head_x + 1 * facing, head_y - 5),
            (head_x + 3 * facing, head_y - 5),
            (head_x + 2 * facing, head_y - 9),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["horse_darkest"], [
            (head_x + 5 * facing, head_y - 5),
            (head_x + 7 * facing, head_y - 5),
            (head_x + 6 * facing, head_y - 9),
        ])

        # Horse glowing eye
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["shadow_deep"],
                  (head_x + 5 * facing, head_y), 2)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_dark"],
                  (head_x + 5 * facing, head_y), max(1, int(2 * eye_pulse)))
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_bright"],
                  (head_x + 5 * facing, head_y), 1)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_hot"],
                  (head_x + 5 * facing, head_y - 1), 1)

        # Nostril
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["shadow_deep"],
                  (head_x + 11 * facing, head_y + 2), 1)

        # ===== HORSE MANE (cyan flames along neck) =====
        for i in range(6):
            t = i / 6
            mane_x = neck_x + int((neck_top_x - neck_x) * t) - 3 * facing
            mane_y = neck_y + int((neck_top_y - neck_y) * t) - 2
            _NS_abaddon._draw_flame_streamer(surface, mane_x, mane_y + 3, 6 + i, phase + i,
                                200)

        # ===== HORSE TAIL (flame) =====
        tail_x = cx - 25 * facing
        tail_y = cy - 3
        for i in range(6):
            t = i / 6
            # Tail curves down
            tx = tail_x - int(t * 15) * facing
            ty = tail_y + int(t * 15) + int(math.sin(phase + i) * 2)
            _NS_abaddon._draw_flame_streamer(surface, tx, ty, 8 - i, phase + i, 200)

        # Also curling tail flame
        for i in range(4):
            angle = math.pi * (0.6 + i * 0.15)
            fx = tail_x + int(math.cos(angle) * 10) * facing
            fy = tail_y + int(math.sin(angle) * 12)
            _NS_abaddon._draw_cyan_flame(surface, fx, fy, 4 - i, phase + i, 220)

        # ===== HORSE SADDLE/HARNESS =====
        # Saddle blanket (purple)
        saddle_pts = [
            (cx - 10 * facing, cy - 12),
            (cx + 12 * facing, cy - 12),
            (cx + 10 * facing, cy - 5),
            (cx - 12 * facing, cy - 5),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_darkest"], saddle_pts)
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_dark"], [
            (cx - 8 * facing, cy - 11),
            (cx + 10 * facing, cy - 11),
            (cx + 8 * facing, cy - 6),
            (cx - 10 * facing, cy - 6),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_mid"], [
            (cx - 6 * facing, cy - 10),
            (cx + 6 * facing, cy - 10),
            (cx + 5 * facing, cy - 7),
            (cx - 7 * facing, cy - 7),
        ])

        # Gold saddle trim
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_dark"],
                (cx - 10 * facing, cy - 5), (cx + 10 * facing, cy - 5), 2)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_mid"],
                (cx - 10 * facing, cy - 5), (cx + 10 * facing, cy - 5), 1)

        # Reins (from Abaddon's hand to horse head)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["leather_mid"] if "leather_mid" in _NS_abaddon.PALETTE
                else _NS_abaddon.PALETTE["cape_darkest"],
                (cx + 5 * facing, cy - 10), (head_x + 2 * facing, head_y + 3), 1)


    # ===================================================================
    # ABADDON RIDER
    # ===================================================================
    def _draw_abaddon_rider(surface, cx, cy, facing, phase, action,
                           attack_progress=0):
        """Draw Abaddon on horseback."""
        # Cape (flowing behind)
        _NS_abaddon._draw_cape(surface, cx, cy + 5, facing, phase, action)

        # Rider legs (visible sitting on horse)
        _NS_abaddon._draw_rider_legs(surface, cx, cy + 12, facing, phase)

        # Torso armor
        _NS_abaddon._draw_torso(surface, cx, cy - 3, phase)

        # Pauldrons
        _NS_abaddon._draw_pauldrons(surface, cx, cy - 10, phase)

        # Arms (one holding sword, one holding reins)
        if action in ("melee",):
            _NS_abaddon._draw_melee_arms(surface, cx, cy - 3, facing, phase, attack_progress)
        elif action == "cast":
            _NS_abaddon._draw_casting_arms(surface, cx, cy - 3, facing, phase, attack_progress)
        else:
            _NS_abaddon._draw_idle_arms(surface, cx, cy - 3, facing, phase)

        # Head with hood
        _NS_abaddon._draw_hooded_head(surface, cx, cy - 22, facing, phase)

        # Floating cyan flames around body
        _NS_abaddon._draw_body_flames(surface, cx, cy, phase)


    def _draw_cape(surface, cx, cy, facing, phase, action):
        """Purple flowing cape."""
        wave = math.sin(phase * 0.8) * 3
        wave2 = math.sin(phase * 1.2 + 0.5) * 2

        cape_outer = [
            (cx - 14, cy - 20),
            (cx - 20, cy - 5),
            (cx - 24 - int(wave), cy + 12),
            (cx - 22 - int(wave2), cy + 25),
            (cx - 10, cy + 30 + int(abs(wave))),
            (cx + 10, cy + 30 + int(abs(wave))),
            (cx + 22 + int(wave2), cy + 25),
            (cx + 24 + int(wave), cy + 12),
            (cx + 20, cy - 5),
            (cx + 14, cy - 20),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in cape_outer])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_darkest"], cape_outer)

        cape_mid = [
            (cx - 12, cy - 18),
            (cx - 18, cy - 5),
            (cx - 22 - int(wave * 0.7), cy + 10),
            (cx - 18 - int(wave2 * 0.7), cy + 22),
            (cx - 6, cy + 26),
            (cx + 6, cy + 26),
            (cx + 18 + int(wave2 * 0.7), cy + 22),
            (cx + 22 + int(wave * 0.7), cy + 10),
            (cx + 18, cy - 5),
            (cx + 12, cy - 18),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_dark"], cape_mid)

        cape_inner = [
            (cx - 10, cy - 15),
            (cx - 15, cy - 5),
            (cx - 18, cy + 8),
            (cx - 10, cy + 20),
            (cx, cy + 22),
            (cx + 10, cy + 20),
            (cx + 18, cy + 8),
            (cx + 15, cy - 5),
            (cx + 10, cy - 15),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_mid"], cape_inner)

        # Cape highlights
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["cape_light"],
                (cx - 8, cy - 12), (cx - 12, cy + 15), 1)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["cape_light"],
                (cx + 8, cy - 12), (cx + 12, cy + 15), 1)


    def _draw_rider_legs(surface, cx, cy, facing, phase):
        """Rider legs on horse."""
        for side in (-1, 1):
            # Thigh (goes to knee)
            thigh_x = cx + side * 5
            thigh_top = cy
            thigh_bot = cy + 8

            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["shadow_deep"],
                    (thigh_x + 1, thigh_top + 1), (thigh_x + 1, thigh_bot + 1), 6)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_darkest"],
                    (thigh_x, thigh_top), (thigh_x, thigh_bot), 5)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_dark"],
                    (thigh_x, thigh_top), (thigh_x, thigh_bot), 3)
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_mid"],
                    (thigh_x - 1, thigh_top), (thigh_x - 1, thigh_bot), 1)

            # Boot area (sticking out below horse)
            boot_x = thigh_x
            boot_y = thigh_bot + 4
            _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["shadow_deep"],
                  (boot_x - 4, boot_y - 2, 8, 8))
            _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["armor_darkest"],
                  (boot_x - 3, boot_y - 2, 7, 7))
            _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["armor_dark"],
                  (boot_x - 3, boot_y - 2, 7, 5))
            # Gold boot detail
            _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["gold_dark"], (boot_x - 3, boot_y, 7, 1))
            _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["gold_mid"], (boot_x - 3, boot_y, 6, 1))


    def _draw_torso(surface, cx, cy, phase):
        """Torso armor."""
        # Shadow
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"], [
            (cx - 12 + 2, cy - 8 + 2), (cx + 12 + 2, cy - 8 + 2),
            (cx + 11 + 2, cy + 12 + 2), (cx - 11 + 2, cy + 12 + 2),
        ])

        torso_pts = [
            (cx - 12, cy - 8),
            (cx + 12, cy - 8),
            (cx + 13, cy + 5),
            (cx + 10, cy + 12),
            (cx - 10, cy + 12),
            (cx - 13, cy + 5),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_darkest"], torso_pts)
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_dark"], [
            (cx - 10, cy - 6),
            (cx + 10, cy - 6),
            (cx + 11, cy + 5),
            (cx + 8, cy + 10),
            (cx - 8, cy + 10),
            (cx - 11, cy + 5),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_mid"], [
            (cx - 7, cy - 3),
            (cx + 7, cy - 3),
            (cx + 8, cy + 4),
            (cx + 5, cy + 8),
            (cx - 5, cy + 8),
            (cx - 8, cy + 4),
        ])

        # Gold trim (V-shape on chest)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_dark"],
                (cx - 10, cy - 6), (cx, cy + 8), 2)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_dark"],
                (cx + 10, cy - 6), (cx, cy + 8), 2)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_mid"],
                (cx - 9, cy - 5), (cx, cy + 7), 1)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_mid"],
                (cx + 9, cy - 5), (cx, cy + 7), 1)

        # Central gem (cyan)
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_darkest"], (cx, cy + 1), 4)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_dark"], (cx, cy + 1), 3)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_mid"], (cx, cy + 1),
                  max(1, int(3 * pulse)))
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_bright"], (cx, cy + 1),
                  max(1, int(2 * pulse)))
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"], (cx, cy + 1), 1)

        # Gold outline
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_mid"], (cx, cy + 1), 4, 1)

        # Belt
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["cape_darkest"], (cx - 13, cy + 10, 26, 4))
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["cape_dark"], (cx - 12, cy + 10, 24, 3))
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["gold_dark"], (cx - 3, cy + 10, 6, 4))
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["gold_mid"], (cx - 2, cy + 10, 4, 3))


    def _draw_pauldrons(surface, cx, cy, phase):
        """Shoulder pauldrons with spikes."""
        for side in (-1, 1):
            sx = cx + side * 14
            # Shadow
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["shadow_deep"], (sx + 2, cy + 2), 8)
            # Pauldron
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["armor_darkest"], (sx, cy), 7)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["armor_dark"], (sx - side, cy - 1), 5)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["armor_mid"], (sx - side, cy - 2), 3)

            # Gold trim
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_dark"], (sx, cy), 7, 2)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_mid"], (sx, cy), 6, 1)

            # Small spike on top
            _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_darkest"], [
                (sx - 2, cy - 6),
                (sx + 2, cy - 6),
                (sx + side * 2, cy - 12),
            ])
            _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_dark"], [
                (sx - 1, cy - 6),
                (sx + 1, cy - 6),
                (sx + side * 1, cy - 11),
            ])
            # Gold tip
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_mid"],
                      (sx + side * 2, cy - 12), 1)


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Idle - one arm with sword down, one holding reins."""
        sway = math.sin(phase * 0.7) * 1

        # Sword arm (facing side)
        ss_x = cx + facing * 13
        ss_y = cy + 2
        se_x = ss_x + facing * 6
        se_y = cy + 10 + int(sway)
        sh_x = se_x + facing * 4
        sh_y = se_y + 12
        _NS_abaddon._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_abaddon._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        # Sword pointing down
        _NS_abaddon._draw_energy_sword(surface, sh_x, sh_y, facing, phase, angle=math.pi/2 - 0.2)

        # Reins arm (opposite side, holding reins forward)
        ra_x = cx + (-facing) * 13
        ra_y = cy + 2
        re_x = ra_x + (-facing) * 5
        re_y = cy + 8
        rh_x = re_x + (-facing) * 3
        rh_y = re_y + 4
        _NS_abaddon._draw_arm_segment(surface, ra_x, ra_y, re_x, re_y)
        _NS_abaddon._draw_arm_segment(surface, re_x, re_y, rh_x, rh_y)
        _NS_abaddon._draw_gloved_hand(surface, rh_x, rh_y)


    def _draw_melee_arms(surface, cx, cy, facing, phase, progress):
        """Melee sword swing."""
        # Reins arm stable
        ra_x = cx + (-facing) * 13
        ra_y = cy + 2
        re_x = ra_x + (-facing) * 5
        re_y = cy + 8
        rh_x = re_x + (-facing) * 3
        rh_y = re_y + 4
        _NS_abaddon._draw_arm_segment(surface, ra_x, ra_y, re_x, re_y)
        _NS_abaddon._draw_arm_segment(surface, re_x, re_y, rh_x, rh_y)
        _NS_abaddon._draw_gloved_hand(surface, rh_x, rh_y)

        # Sword arm - swing motion
        ss_x = cx + facing * 13
        ss_y = cy + 2

        if progress < 0.3:
            t = progress / 0.3
            arm_angle = -0.8 + (-1.0) * t
        elif progress < 0.6:
            t = (progress - 0.3) / 0.3
            arm_angle = -1.8 + 2.8 * t
        else:
            t = (progress - 0.6) / 0.4
            arm_angle = 1.0 - 1.5 * t

        se_x = ss_x + int(math.cos(arm_angle) * 12) * facing
        se_y = ss_y + int(math.sin(arm_angle) * 12)
        sh_x = se_x + int(math.cos(arm_angle) * 10) * facing
        sh_y = se_y + int(math.sin(arm_angle) * 10)

        _NS_abaddon._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_abaddon._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        # Sword with rotation
        sword_angle = arm_angle + (0.3 if facing > 0 else -0.3)
        _NS_abaddon._draw_energy_sword(surface, sh_x, sh_y, facing, phase, angle=sword_angle,
                          intense=(0.3 < progress < 0.7))


    def _draw_casting_arms(surface, cx, cy, facing, phase, progress):
        """Casting - sword extended forward."""
        # Reins arm
        ra_x = cx + (-facing) * 13
        ra_y = cy + 2
        re_x = ra_x + (-facing) * 5
        re_y = cy + 8
        rh_x = re_x + (-facing) * 3
        rh_y = re_y + 4
        _NS_abaddon._draw_arm_segment(surface, ra_x, ra_y, re_x, re_y)
        _NS_abaddon._draw_arm_segment(surface, re_x, re_y, rh_x, rh_y)
        _NS_abaddon._draw_gloved_hand(surface, rh_x, rh_y)

        # Sword arm - point forward
        ss_x = cx + facing * 13
        ss_y = cy + 2

        if progress < 0.3:
            t = progress / 0.3
            arm_angle = -0.5 - 0.5 * t
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            arm_angle = -1.0 + 1.3 * t
        else:
            t = (progress - 0.5) / 0.5
            arm_angle = 0.3 - 0.5 * t

        se_x = ss_x + int(math.cos(arm_angle) * 12) * facing
        se_y = ss_y + int(math.sin(arm_angle) * 12)
        sh_x = se_x + int(math.cos(arm_angle) * 10) * facing
        sh_y = se_y + int(math.sin(arm_angle) * 10)

        _NS_abaddon._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_abaddon._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        _NS_abaddon._draw_energy_sword(surface, sh_x, sh_y, facing, phase, angle=arm_angle,
                          intense=(0.2 < progress < 0.5))


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Armored arm segment."""
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["shadow_deep"],
                (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 6)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_darkest"], (x1, y1), (x2, y2), 5)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_dark"], (x1, y1), (x2, y2), 4)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_mid"], (x1, y1), (x2, y2), 2)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_light"], (x1 - 1, y1), (x2 - 1, y2), 1)
        # Gold joint
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_dark"], (mx, my), 3)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_mid"], (mx, my), 2)


    def _draw_gloved_hand(surface, x, y):
        """Armored gauntlet hand."""
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["shadow_deep"], (x + 1, y + 1), 4)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["armor_darkest"], (x, y), 3)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["armor_dark"], (x, y - 1), 2)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["armor_mid"], (x - 1, y - 1), 1)


    def _draw_energy_sword(surface, hx, hy, facing, phase, angle=0, intense=False):
        """Abaddon's cyan energy sword."""
        length = 32
        tip_x = hx + int(math.cos(angle) * length) * facing
        tip_y = hy + int(math.sin(angle) * length)

        perp_angle = angle + math.pi / 2
        px = math.cos(perp_angle) * facing
        py = math.sin(perp_angle)

        # Blade base - crystalline shape
        blade_pts = [
            (hx + int(px * 3), hy + int(py * 3)),
            (hx - int(px * 2), hy - int(py * 2)),
            (tip_x - int(math.cos(angle) * 4) * facing - int(px * 1),
             tip_y - int(math.sin(angle) * 4) - int(py * 1)),
            (tip_x, tip_y),
            (tip_x - int(math.cos(angle) * 4) * facing + int(px * 3),
             tip_y - int(math.sin(angle) * 4) + int(py * 3)),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in blade_pts])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["blade_darkest"], blade_pts)

        # Layers
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["blade_dark"], [
            (hx + int(px * 2), hy + int(py * 2)),
            (hx - int(px * 1), hy - int(py * 1)),
            (tip_x, tip_y),
            (hx + int(px * 2) + int(math.cos(angle) * length * 0.5) * facing,
             hy + int(py * 2) + int(math.sin(angle) * length * 0.5)),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["blade_mid"], [
            (hx + int(px * 1), hy + int(py * 1)),
            (hx, hy),
            (tip_x, tip_y),
        ])

        # Energy glow along blade
        for i in range(6):
            t = i / 6
            bx = int(hx + (tip_x - hx) * t)
            by = int(hy + (tip_y - hy) * t)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], 200), (bx, by), 3)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], 220), (bx, by), 2)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"], (bx, by), 1)

        # Bright edge
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["blade_shine"], (hx, hy), (tip_x, tip_y), 2)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["flame_white"], (hx, hy), (tip_x, tip_y), 1)

        # Extra intense glow when swinging
        if intense:
            # Aura around blade
            for i in range(4):
                t = i / 4
                bx = int(hx + (tip_x - hx) * t)
                by = int(hy + (tip_y - hy) * t)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], 100), (bx, by), 6)
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], 150), (bx, by), 4)

        # Guard (crossguard - gold)
        guard_perp_x = int(px * 6)
        guard_perp_y = int(py * 6)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_darkest"],
                (hx + guard_perp_x, hy + guard_perp_y),
                (hx - guard_perp_x, hy - guard_perp_y), 4)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_dark"],
                (hx + guard_perp_x, hy + guard_perp_y),
                (hx - guard_perp_x, hy - guard_perp_y), 3)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_mid"],
                (hx + guard_perp_x, hy + guard_perp_y),
                (hx - guard_perp_x, hy - guard_perp_y), 1)

        # Pommel with cyan gem
        pommel_x = hx - int(math.cos(angle) * 5) * facing
        pommel_y = hy - int(math.sin(angle) * 5)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_darkest"], (pommel_x, pommel_y), 3)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["gold_dark"], (pommel_x, pommel_y), 2)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_bright"], (pommel_x, pommel_y), 1)


    def _draw_hooded_head(surface, cx, cy, facing, phase):
        """Hood with glowing eyes inside."""
        # Neck
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["armor_darkest"], (cx - 3, cy + 8, 6, 5))
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["armor_dark"], (cx - 2, cy + 8, 4, 4))

        # Hood shape (large purple hood covering head)
        hood_pts = [
            (cx - 12, cy - 2),
            (cx - 11, cy - 10),
            (cx - 6, cy - 14),
            (cx, cy - 16),
            (cx + 6, cy - 14),
            (cx + 11, cy - 10),
            (cx + 12, cy - 2),
            (cx + 13, cy + 8),
            (cx + 7, cy + 12),
            (cx - 7, cy + 12),
            (cx - 13, cy + 8),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"], [(p[0] + 2, p[1] + 2) for p in hood_pts])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_darkest"], hood_pts)

        hood_mid = [
            (cx - 10, cy - 1),
            (cx - 9, cy - 9),
            (cx - 5, cy - 13),
            (cx, cy - 15),
            (cx + 5, cy - 13),
            (cx + 9, cy - 9),
            (cx + 10, cy - 1),
            (cx + 11, cy + 6),
            (cx + 6, cy + 10),
            (cx - 6, cy + 10),
            (cx - 11, cy + 6),
        ]
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["cape_dark"], hood_mid)

        # Hood highlight edge
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["cape_mid"],
                (cx - 9, cy - 9), (cx, cy - 15), 1)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["cape_mid"],
                (cx + 9, cy - 9), (cx, cy - 15), 1)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["cape_light"],
                (cx - 5, cy - 13), (cx, cy - 15), 1)

        # Dark interior of hood
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["shadow_deep"], [
            (cx - 8, cy - 6),
            (cx - 7, cy - 10),
            (cx, cy - 12),
            (cx + 7, cy - 10),
            (cx + 8, cy - 6),
            (cx + 7, cy + 5),
            (cx, cy + 8),
            (cx - 7, cy + 5),
        ])

        # ===== HELM inside hood =====
        # Simple helm shape (visible under hood)
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_darkest"], [
            (cx - 6, cy - 3),
            (cx - 5, cy - 8),
            (cx, cy - 10),
            (cx + 5, cy - 8),
            (cx + 6, cy - 3),
            (cx + 5, cy + 4),
            (cx, cy + 6),
            (cx - 5, cy + 4),
        ])
        _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_dark"], [
            (cx - 5, cy - 2),
            (cx - 4, cy - 7),
            (cx, cy - 9),
            (cx + 4, cy - 7),
            (cx + 5, cy - 2),
            (cx + 4, cy + 3),
            (cx, cy + 5),
            (cx - 4, cy + 3),
        ])

        # Gold helm brow
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_dark"],
                (cx - 5, cy - 5), (cx + 5, cy - 5), 2)
        _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["gold_mid"],
                (cx - 5, cy - 5), (cx + 5, cy - 5), 1)

        # ===== GLOWING EYES =====
        eye_pulse = math.sin(phase * 2) * 0.2 + 0.8
        eye_size = max(1, int(2 * eye_pulse))
        # Eye sockets (dark slits)
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["shadow_deep"], (cx - 5, cy - 2, 4, 2))
        _NS_abaddon._rect(surface, _NS_abaddon.PALETTE["shadow_deep"], (cx + 1, cy - 2, 4, 2))
        # Bright cyan eye glow
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_dark"], (cx - 3, cy - 1), eye_size + 1)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_mid"], (cx - 3, cy - 1), eye_size)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_bright"], (cx - 3, cy - 1),
                  max(1, eye_size - 1))
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_hot"], (cx - 3, cy - 1), 1)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_dark"], (cx + 3, cy - 1), eye_size + 1)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_mid"], (cx + 3, cy - 1), eye_size)
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_bright"], (cx + 3, cy - 1),
                  max(1, eye_size - 1))
        _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["eye_hot"], (cx + 3, cy - 1), 1)

        # Eye emission glow
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["eye_bright"], int(80 * eye_pulse)),
                  (cx - 3, cy - 1), 5)
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["eye_bright"], int(80 * eye_pulse)),
                  (cx + 3, cy - 1), 5)

        # ===== HELM HORNS =====
        for side in (-1, 1):
            # Curved horn
            _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_darkest"], [
                (cx + side * 5, cy - 8),
                (cx + side * 8, cy - 12),
                (cx + side * 12, cy - 20),
                (cx + side * 14, cy - 22),
                (cx + side * 11, cy - 19),
                (cx + side * 7, cy - 11),
            ])
            _NS_abaddon._poly(surface, _NS_abaddon.PALETTE["armor_dark"], [
                (cx + side * 6, cy - 9),
                (cx + side * 8, cy - 12),
                (cx + side * 11, cy - 18),
                (cx + side * 13, cy - 21),
                (cx + side * 10, cy - 18),
                (cx + side * 7, cy - 11),
            ])
            _NS_abaddon._aaline(surface, _NS_abaddon.PALETTE["armor_mid"],
                    (cx + side * 8, cy - 12),
                    (cx + side * 13, cy - 21), 1)
            # Small cyan glow on horn tip
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], 180),
                      (cx + side * 14, cy - 22), 2)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_bright"],
                      (cx + side * 14, cy - 22), 1)

        # Cyan flame streamers coming up from head
        for i in (-4, 0, 4):
            _NS_abaddon._draw_flame_streamer(surface, cx + i, cy - 10, 6, phase + i * 0.3, 180)


    def _draw_body_flames(surface, cx, cy, phase):
        """Cyan flames rising from body."""
        for i in range(6):
            angle = phase * 0.4 + i * math.pi / 3
            radius = 22 + int(math.sin(phase * 0.7 + i) * 4)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(140 + math.sin(phase + i * 0.7) * 60)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_dark"], alpha), (px, py), 2)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], alpha // 2), (px, py), 1)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_horse_flame_base(surface, cx, cy, phase, trail=False,
                              facing=1, intense=False):
        """Cyan flame base beneath the ghostly horse."""
        strength = 1.5 if intense else 1.0

        # Base flame mist
        mist = pygame.Surface((150, 45), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(42, 3, -4):
            alpha = int((42 - radius) * 2.0 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_abaddon.PALETTE["flame_darkest"], min(255, alpha)),
                    (75 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 75, cy - 12))

        # Rising cyan flames
        for i, offset in enumerate((-30, -18, -6, 6, 18, 30)):
            t = (phase * 0.5 + i * 0.17) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 25)
            alpha = max(0, min(255, int(220 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_abaddon._draw_cyan_flame(surface, sx, sy, max(1, 4 - int(t * 3)),
                            phase + i, alpha)

        # Orbiting flame orbs
        for i in range(5):
            angle = phase * 0.9 + i * math.pi * 2 / 5
            r = 28 + int(math.sin(phase + i * 1.3) * 4)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 7)
            _NS_abaddon._draw_cyan_flame(surface, sx, sy, 3, phase + i, 220)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 140 - i * 25)
                _NS_abaddon._draw_cyan_flame(surface, sx, sy, max(2, 4 - i), phase + i, alpha)


    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((130, 24), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (12 - radius, 12 - radius, 106 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_abaddon.PALETTE["flame_darkest"], 60),
                           (10, 5, 108, 12))
        surface.blit(shadow, (x - 65, y - 12))


    def _draw_dark_aura(surface, x, y, phase):
        """Dark purple/cyan background aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(88, 5, -4):
            alpha = int((88 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_abaddon._aacircle(aura, (*_NS_abaddon.PALETTE["cape_darkest"], min(255, alpha)),
                          (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))

        # Cyan glow overlay
        aura2 = pygame.Surface((160, 140), pygame.SRCALPHA)
        for radius in range(64, 5, -3):
            alpha = int((64 - radius) * 0.7 * pulse)
            if alpha > 0:
                _NS_abaddon._aacircle(aura2, (*_NS_abaddon.PALETTE["flame_darkest"], min(255, alpha)),
                          (80, 70), radius)
        surface.blit(aura2, (x - 80, y - 70))


    def _draw_ground_runes(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((160, 52), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_abaddon.PALETTE["cape_dark"], 140),
                            (5, 12, 150, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_abaddon.PALETTE["flame_dark"], 170),
                            (25, 16, 110, 22), 2)

        for i in range(10):
            angle = phase * 0.2 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 38)
            y1 = 27 + int(math.sin(angle) * 8)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 27 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_abaddon.PALETTE["flame_bright"], 160),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_abaddon.PALETTE["flame_hot"], int(80 * pulse)),
                                (15, 10, 130, 34), 1)

        surface.blit(ring, (x - 80, y - 26))


    def _draw_sword_swing_trail(surface, x, y, facing, progress):
        """Cyan trail during basic sword swing."""
        if progress < 0.3 or progress > 0.7:
            return
        t = (progress - 0.3) / 0.4
        center_x = x + facing * 5
        center_y = y
        radius = 45

        start_angle = -math.pi / 2 - 0.5
        end_angle = math.pi / 4
        current_angle = start_angle + (end_angle - start_angle) * t

        trail_length = 1.5
        segments = 14
        for i in range(segments):
            seg_t = i / segments
            angle = current_angle - trail_length * seg_t
            if angle < start_angle:
                continue

            ax = center_x + int(math.cos(angle) * radius) * facing
            ay = center_y + int(math.sin(angle) * radius)

            alpha_seg = int(220 * (1 - seg_t))
            size = int(4 * (1 - seg_t * 0.4))
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_dark"], alpha_seg),
                      (ax, ay), size + 2)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_mid"], alpha_seg),
                      (ax, ay), size + 1)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], alpha_seg),
                      (ax, ay), size)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"],
                      (ax, ay), max(1, size - 1))


    def _draw_sword_purple_trail(surface, x, y, facing, progress, phase):
        """Purple trail during Death Sever."""
        if progress < 0.15 or progress > 0.75:
            return

        t = (progress - 0.15) / 0.6
        center_x = x + facing * 5
        center_y = y
        radius = 50

        start_angle = -math.pi / 2 - 0.5
        end_angle = math.pi / 4
        current_angle = start_angle + (end_angle - start_angle) * t

        trail_length = 2.0
        segments = 16
        for i in range(segments):
            seg_t = i / segments
            angle = current_angle - trail_length * seg_t
            if angle < start_angle:
                continue

            ax = center_x + int(math.cos(angle) * radius) * facing
            ay = center_y + int(math.sin(angle) * radius)

            alpha_seg = int(240 * (1 - seg_t))
            size = int(5 * (1 - seg_t * 0.3))
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_darkest"], alpha_seg),
                      (ax, ay), size + 3)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_dark"], alpha_seg),
                      (ax, ay), size + 2)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_mid"], alpha_seg),
                      (ax, ay), size + 1)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_bright"], alpha_seg),
                      (ax, ay), size)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["magic_hot"], alpha_seg),
                      (ax, ay), max(1, size - 1))


    # ===================================================================
    # SKILL W: APHOTIC SHIELD
    # ===================================================================
    def _draw_aphotic_shield(surface, boss, x, y, timer, phase):
        """Bubble shield around Abaddon."""
        progress = max(0.0, min(1.0, 1 - timer / 100))
        pulse = math.sin(phase * 2) * 0.2 + 0.8

        # Shield radius
        radius = int(45 + progress * 5)

        # Multi-layer shield sphere
        shield_layers = [
            (radius + 3, _NS_abaddon.PALETTE["flame_dark"], 100),
            (radius, _NS_abaddon.PALETTE["flame_mid"], 180),
            (radius - 3, _NS_abaddon.PALETTE["flame_light"], 150),
            (radius - 6, _NS_abaddon.PALETTE["flame_bright"], 100),
        ]

        for r, color, alpha in shield_layers:
            a = int(alpha * pulse)
            _NS_abaddon._aacircle(surface, (*color, a), (x, y - 8), r, 3)

        # Bright edge highlights
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], int(220 * pulse)),
                  (x, y - 8), radius, 2)
        _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_hot"], int(200 * pulse)),
                  (x, y - 8), radius, 1)

        # Rotating energy bands
        for band_i in range(3):
            band_phase = phase * 1.5 + band_i * math.pi / 3
            # Draw as arc segments (approximated with lines)
            for j in range(-6, 7):
                angle = band_phase + j * 0.15
                bx = x + int(math.cos(angle) * radius * math.cos(band_i * 0.4))
                by = y - 8 + int(math.sin(angle) * radius * math.cos(band_i * 0.4))
                _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_hot"], 200), (bx, by), 2)
                _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_white"], (bx, by), 1)

        # Small orbs orbiting the shield
        for i in range(6):
            angle = phase * 1.2 + i * math.pi / 3
            ox = x + int(math.cos(angle) * radius)
            oy = y - 8 + int(math.sin(angle) * radius * 0.6)
            _NS_abaddon._aacircle(surface, (*_NS_abaddon.PALETTE["flame_bright"], 220), (ox, oy), 3)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_hot"], (ox, oy), 2)
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_white"], (ox, oy), 1)

        # Bright sparks
        for i in range(8):
            angle = phase * 0.8 + i * math.pi / 4
            sx = x + int(math.cos(angle) * (radius + 5))
            sy = y - 8 + int(math.sin(angle) * (radius + 5))
            _NS_abaddon._aacircle(surface, _NS_abaddon.PALETTE["flame_shine"] if "flame_shine" in _NS_abaddon.PALETTE
                      else _NS_abaddon.PALETTE["flame_hot"], (sx, sy), 1)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_abaddon.draw_abaddon(surface, boss, x, y)


# ====================================================================
# ENTRY POINT PUBLIK (dipanggil base_boss.Boss.draw)
# ====================================================================

def draw_gornak(surface, boss, x, y):
    """Entry point gornak."""
    return _NS_gornak.draw_gornak(surface, boss, x, y)

def draw_morgath(surface, boss, x, y):
    """Entry point morgath."""
    return _NS_morgath.draw_morgath(surface, boss, x, y)

def draw_drakar(surface, boss, x, y):
    """Entry point drakar."""
    return _NS_drakar.draw_drakar(surface, boss, x, y)

def draw_abaddon(surface, boss, x, y):
    """Entry point abaddon."""
    return _NS_abaddon.draw_abaddon(surface, boss, x, y)
