"""
bosses/level44.py - Semua boss Level 44

Berisi:
  - lyrenya     (mini boss - RANGED verdant whisper, nature magic)
  - vyraeth     (mini boss - RANGED haunting wraith, spectral)
  - zorothrax   (mini boss - RANGED rune sovereign, arcane)
  - kagetsuka   (TRUE BOSS - MELEE eternal warlord, sharingan fire)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _ly_ (lyrenya), _zx_ (zorothrax), _kg_ (kagetsuka) sudah unik.
  - _vy_ (vyraeth) di-rename -> _vyt_ (bentrok dengan vessyra
    level 32), termasuk atribut _last_x/_last_y.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# LYRENYA (VERDANT WHISPER) - Mini Boss
# ====================================================================

class _NS_lyrenya:
    """Namespace lyrenya - Verdant Whisper boss (Nature Enchantress)."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (warm feminine)
        "skin_darkest": (95, 60, 45),
        "skin_dark": (170, 120, 90),
        "skin_mid": (220, 175, 140),
        "skin_light": (245, 215, 185),
        "skin_shine": (255, 240, 220),
        # Hair (auburn/copper red)
        "hair_darkest": (55, 20, 10),
        "hair_dark": (110, 45, 20),
        "hair_mid": (170, 85, 35),
        "hair_light": (220, 140, 65),
        "hair_shine": (255, 195, 120),
        # Dress (nature green leaves)
        "dress_darkest": (15, 35, 12),
        "dress_dark": (35, 70, 25),
        "dress_mid": (65, 115, 40),
        "dress_light": (110, 170, 65),
        "dress_shine": (170, 220, 110),
        # Leaf accents (bright green)
        "leaf_dark": (25, 60, 15),
        "leaf_mid": (75, 145, 40),
        "leaf_light": (150, 220, 80),
        "leaf_shine": (210, 250, 140),
        # Gold trim (antlers, jewelry)
        "gold_darkest": (55, 35, 5),
        "gold_dark": (110, 80, 20),
        "gold_mid": (200, 155, 55),
        "gold_light": (245, 215, 115),
        "gold_shine": (255, 240, 180),
        # Wood staff
        "wood_dark": (45, 25, 12),
        "wood_mid": (95, 60, 28),
        "wood_light": (155, 105, 55),
        "wood_shine": (210, 170, 115),
        # Nature magic (bright golden-green)
        "magic_darkest": (25, 35, 5),
        "magic_dark": (85, 110, 15),
        "magic_mid": (180, 220, 40),
        "magic_light": (240, 255, 130),
        "magic_hot": (255, 255, 200),
        "magic_shine": (255, 255, 240),
        # Eyes (bright green)
        "eye_dark": (10, 40, 15),
        "eye_mid": (60, 155, 65),
        "eye_light": (140, 230, 130),
        "eye_shine": (230, 255, 210),
        # Deer companion (fawn brown)
        "deer_dark": (75, 45, 20),
        "deer_mid": (150, 100, 55),
        "deer_light": (215, 170, 115),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_lyrenya._clamp(color)
        if _NS_lyrenya.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_lyrenya._clamp(color)
        if _NS_lyrenya.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_lyrenya._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_lyrenya(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_lyrenya._detect_moving(boss)
        _NS_lyrenya._update_attack_anim(boss)
        attacking = getattr(boss, "_ly_attack_active", False)
        # Ambient
        _NS_lyrenya._draw_nature_aura(surface, x, y, pulse)
        _NS_lyrenya._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX
        if active_skill == "e":
            _NS_lyrenya._draw_attendants_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_lyrenya._draw_shield_ground(surface, boss, x, y, skill_timer, pulse)
        # Body
        if attacking:
            _NS_lyrenya._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_lyrenya._draw_walk(surface, boss, x, y)
        else:
            _NS_lyrenya._draw_idle(surface, boss, x, y)
        # Foreground FX
        if active_skill == "q":
            _NS_lyrenya._draw_naturebolt_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_lyrenya._draw_charm_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_lyrenya._draw_attendants_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_lyrenya._draw_shield_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_ly_attack_active", False))
        if not active and timer <= 2:
            boss._ly_attack_active = True
            boss._ly_attack_frame = 0
            active = True
        if active:
            boss._ly_attack_frame = int(getattr(boss, "_ly_attack_frame", 0)) + 1
            if boss._ly_attack_frame >= cooldown:
                boss._ly_attack_active = False
                boss._ly_attack_frame = 0
                active = False
        boss._ly_attack_progress = (
            min(1.0, getattr(boss, "_ly_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_ly_last_x"):
            boss._ly_last_x = boss.x
            boss._ly_last_y = boss.y
            return False
        dx = abs(boss.x - boss._ly_last_x)
        dy = abs(boss.y - boss._ly_last_y)
        boss._ly_last_x = boss.x
        boss._ly_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        # Gentle float bob
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_lyrenya._draw_shadow(surface, x, y + 50)
        _NS_lyrenya._draw_nature_base(surface, x, y + 26 + bob, boss.pulse)
        _NS_lyrenya._draw_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")
    def _draw_walk(surface, boss, x, y):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.7) * 5)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_lyrenya._draw_shadow(surface, x + sway, y + 50)
        _NS_lyrenya._draw_nature_base(surface, x + sway, y + 26 + bob, phase,
                                      moving=True, facing=boss.direction)
        _NS_lyrenya._draw_body(surface, x + sway, y + bob, boss.direction, phase, "walk")
    def _draw_attack(surface, boss, x, y):
        progress = getattr(boss, "_ly_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        bob = int(math.sin(boss.pulse * 0.5) * 3)
        # Raise staff → cast forward → recover
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 2) * boss.direction
        elif progress < 0.55:
            t = (progress - 0.35) / 0.2
            lunge = int((-2 + t * 8)) * boss.direction
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(6 * (1 - t)) * boss.direction
        _NS_lyrenya._draw_shadow(surface, x + lunge, y + 50)
        _NS_lyrenya._draw_nature_base(surface, x + lunge, y + 26 + bob, boss.pulse,
                                      intense=True)
        _NS_lyrenya._draw_body(surface, x + lunge, y + bob, boss.direction, boss.pulse,
                               "attack", progress)
        _NS_lyrenya._draw_nature_projectile(surface, boss, x + lunge, y + bob, progress)
    # ============================================================
    # BODY - Elf enchantress with staff
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0.0):
        # Dress skirt (bottom)
        _NS_lyrenya._draw_dress(surface, cx, cy, facing, phase)
        # Torso corset
        _NS_lyrenya._draw_torso(surface, cx, cy, facing, phase)
        # Free arm (back)
        _NS_lyrenya._draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress)
        # Long hair behind
        _NS_lyrenya._draw_hair_back(surface, cx, cy - 12, facing, phase)
        # Head + face
        _NS_lyrenya._draw_head(surface, cx, cy - 20, facing, phase)
        # Antlers/crown
        _NS_lyrenya._draw_antlers(surface, cx, cy - 26, facing, phase)
        # Front hair strands
        _NS_lyrenya._draw_hair_front(surface, cx, cy - 20, facing, phase)
        # Staff-holding arm + staff (front, over body)
        _NS_lyrenya._draw_staff_arm(surface, cx, cy, facing, phase, action, attack_progress)
        # Floating butterflies/leaves around
        _NS_lyrenya._draw_orbiting_leaves(surface, cx, cy, facing, phase)
    def _draw_dress(surface, cx, cy, facing, phase):
        """Long flowing dress of layered leaves."""
        sway = math.sin(phase * 0.6) * 2
        # Main dress shape (flowing skirt)
        dress_shape = [
            (cx - 10, cy + 6),
            (cx - 12, cy + 12),
            (cx - 14 + int(sway), cy + 22),
            (cx - 13 + int(sway), cy + 30),
            (cx - 10 + int(sway), cy + 36),
            (cx + 10 + int(sway * 0.5), cy + 36),
            (cx + 13 + int(sway * 0.5), cy + 30),
            (cx + 14, cy + 22),
            (cx + 12, cy + 12),
            (cx + 10, cy + 6),
        ]
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["shadow_deep"],
              [(px + 2, py + 3) for px, py in dress_shape])
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["dress_darkest"], dress_shape)
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["dress_dark"], [
            (cx - 9, cy + 7), (cx - 11, cy + 12),
            (cx - 13 + int(sway * 0.7), cy + 21),
            (cx - 12 + int(sway * 0.7), cy + 29),
            (cx - 9 + int(sway * 0.5), cy + 35),
            (cx + 9 + int(sway * 0.3), cy + 35),
            (cx + 12 + int(sway * 0.3), cy + 29),
            (cx + 13, cy + 21), (cx + 11, cy + 12), (cx + 9, cy + 7),
        ])
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["dress_mid"], [
            (cx - 7, cy + 8), (cx - 9, cy + 14),
            (cx - 10 + int(sway * 0.5), cy + 22),
            (cx - 8 + int(sway * 0.5), cy + 30),
            (cx + 8 + int(sway * 0.3), cy + 30),
            (cx + 10 + int(sway * 0.3), cy + 22),
            (cx + 9, cy + 14), (cx + 7, cy + 8),
        ])
        # Vertical folds
        for x_off in (-6, -2, 2, 6):
            pygame.draw.line(surface, _NS_lyrenya.PALETTE["dress_darkest"],
                             (cx + x_off, cy + 10),
                             (cx + x_off + int(sway * 0.3), cy + 34), 1)
        # Layered leaves on dress (decorative overlay)
        for i, (lx, ly, angle) in enumerate([
            (-8, 12, -0.3), (-3, 15, 0.2), (3, 15, -0.2), (8, 12, 0.3),
            (-6, 22, -0.4), (0, 25, 0), (6, 22, 0.4),
            (-4, 30, -0.5), (4, 30, 0.5),
        ]):
            leaf_x = cx + lx + int(sway * 0.3)
            leaf_y = cy + ly
            _NS_lyrenya._draw_small_leaf(surface, leaf_x, leaf_y, angle)
        # Gold belt at waist
        pygame.draw.rect(surface, _NS_lyrenya.PALETTE["gold_dark"],
                         (cx - 10, cy + 5, 20, 4))
        pygame.draw.rect(surface, _NS_lyrenya.PALETTE["gold_mid"],
                         (cx - 10, cy + 5, 20, 2))
        pygame.draw.rect(surface, _NS_lyrenya.PALETTE["gold_light"],
                         (cx - 10, cy + 5, 20, 1))
        # Belt gem
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for r in range(3, 0, -1):
            alpha = _NS_lyrenya._alpha(220 * (3 - r) / 3 * pulse)
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_mid"], alpha),
                                  (cx, cy + 7), r)
        pygame.draw.rect(surface, _NS_lyrenya.PALETTE["magic_shine"], (cx, cy + 7, 1, 1))
    def _draw_small_leaf(surface, cx, cy, angle):
        """Small decorative leaf."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        # Leaf shape (diamond)
        pts = [
            (cx, cy - 2),
            (cx + int(cos_a * 2), cy + int(sin_a * 2)),
            (cx + int(cos_a * 4), cy + int(sin_a * 4) + 1),
            (cx + int(cos_a * 2), cy + int(sin_a * 2) + 2),
        ]
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["leaf_dark"], pts)
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["leaf_mid"], [
            pts[0],
            (int((pts[0][0] + pts[1][0]) / 2), int((pts[0][1] + pts[1][1]) / 2)),
            pts[2], pts[3],
        ])
        pygame.draw.rect(surface, _NS_lyrenya.PALETTE["leaf_light"],
                         (cx + int(cos_a * 2), cy + int(sin_a * 2), 1, 1))
    def _draw_torso(surface, cx, cy, facing, phase):
        """Feminine torso with green leaf corset."""
        # Torso shape (hourglass female)
        torso_shape = [
            (cx - 9, cy - 8),   # shoulder line
            (cx - 10, cy - 4),
            (cx - 8, cy),
            (cx - 6, cy + 3),   # waist
            (cx - 8, cy + 6),
            (cx + 8, cy + 6),
            (cx + 6, cy + 3),
            (cx + 8, cy),
            (cx + 10, cy - 4),
            (cx + 9, cy - 8),
            (cx + 5, cy - 11),
            (cx - 5, cy - 11),
        ]
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["shadow_deep"],
              [(px + 2, py + 3) for px, py in torso_shape])
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["dress_darkest"], torso_shape)
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["dress_dark"], [
            (cx - 8, cy - 7), (cx - 9, cy - 3),
            (cx - 7, cy), (cx - 5, cy + 3),
            (cx - 7, cy + 5), (cx + 7, cy + 5),
            (cx + 5, cy + 3), (cx + 7, cy),
            (cx + 9, cy - 3), (cx + 8, cy - 7),
            (cx + 4, cy - 10), (cx - 4, cy - 10),
        ])
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["dress_mid"], [
            (cx - 6, cy - 5), (cx - 7, cy - 2),
            (cx - 5, cy + 1), (cx - 4, cy + 3),
            (cx + 4, cy + 3), (cx + 5, cy + 1),
            (cx + 7, cy - 2), (cx + 6, cy - 5),
            (cx + 3, cy - 8), (cx - 3, cy - 8),
        ])
        # Skin exposed (chest/decolletage - upper chest visible)
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["skin_dark"], [
            (cx - 5, cy - 10), (cx - 6, cy - 7),
            (cx - 3, cy - 4), (cx + 3, cy - 4),
            (cx + 6, cy - 7), (cx + 5, cy - 10),
        ])
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["skin_mid"], [
            (cx - 4, cy - 9), (cx - 5, cy - 7),
            (cx - 2, cy - 5), (cx + 2, cy - 5),
            (cx + 5, cy - 7), (cx + 4, cy - 9),
        ])
        pygame.draw.rect(surface, _NS_lyrenya.PALETTE["skin_light"],
                         (cx - 1, cy - 7, 2, 1))
        # Center leaf ornament on chest
        _NS_lyrenya._draw_center_leaf(surface, cx, cy - 6, phase)
        # Corset lines (crisscross)
        for i in range(3):
            y_off = -2 + i * 3
            pygame.draw.line(surface, _NS_lyrenya.PALETTE["gold_dark"],
                             (cx - 4, cy + y_off), (cx + 4, cy + y_off - 1), 1)
            pygame.draw.line(surface, _NS_lyrenya.PALETTE["gold_mid"],
                             (cx - 4, cy + y_off - 1), (cx + 4, cy + y_off), 1)
        # Shoulder highlights (dress edge)
        pygame.draw.line(surface, _NS_lyrenya.PALETTE["dress_light"],
                         (cx - 9, cy - 8), (cx - 5, cy - 11), 1)
        pygame.draw.line(surface, _NS_lyrenya.PALETTE["dress_light"],
                         (cx + 9, cy - 8), (cx + 5, cy - 11), 1)
    def _draw_center_leaf(surface, cx, cy, phase):
        """Glowing leaf pendant on chest."""
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        # Leaf shape
        pts = [
            (cx, cy - 3),
            (cx + 2, cy),
            (cx, cy + 3),
            (cx - 2, cy),
        ]
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["leaf_dark"], pts)
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["leaf_mid"], [
            pts[0], (cx + 1, cy - 1), pts[2], (cx - 1, cy - 1),
        ])
        pygame.draw.rect(surface, _NS_lyrenya.PALETTE["leaf_light"], (cx, cy - 1, 1, 1))
        # Glow
        for r in range(4, 0, -1):
            alpha = _NS_lyrenya._alpha(150 * (4 - r) / 4 * pulse)
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_mid"], alpha),
                                  (cx, cy), r)
        pygame.draw.rect(surface, _NS_lyrenya.PALETTE["magic_shine"], (cx, cy, 1, 1))
    def _draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm (opposite of staff hand) - gestures or rests."""
        arm_sway = math.sin(phase * 0.6) * 1
        back_side = -facing
        shoulder_x = cx + back_side * 9
        shoulder_y = cy - 7
        if action == "attack":
            # Slightly raised for emphasis
            if attack_progress < 0.55:
                t = attack_progress / 0.55
                elbow_x = shoulder_x + back_side * 4 - int(t * 2)
                elbow_y = shoulder_y + 4 - int(t * 3)
                hand_x = elbow_x + back_side * 2
                hand_y = elbow_y + 4 - int(t * 2)
            else:
                t = (attack_progress - 0.55) / 0.45
                elbow_x = shoulder_x + back_side * 4 - int((1 - t) * 2)
                elbow_y = shoulder_y + 4 - int((1 - t) * 3)
                hand_x = elbow_x + back_side * 2
                hand_y = elbow_y + 4 - int((1 - t) * 2)
        else:
            elbow_x = shoulder_x + back_side * 3
            elbow_y = shoulder_y + 6 + int(arm_sway)
            hand_x = elbow_x + back_side * 2
            hand_y = elbow_y + 8
        # Draw arm (skin colored)
        _NS_lyrenya._draw_slim_arm(surface, (shoulder_x, shoulder_y), (elbow_x, elbow_y),
                                    (hand_x, hand_y), depth_shade=0.85)
        # Hand
        _NS_lyrenya._draw_hand(surface, hand_x, hand_y, back_side, phase, depth_shade=0.85)
    def _draw_staff_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Staff-holding arm and staff itself."""
        arm_sway = math.sin(phase * 0.5) * 1
        shoulder_x = cx + facing * 9
        shoulder_y = cy - 7
        # Staff position based on action
        if action == "attack":
            # Point staff forward
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                staff_lean = -int(t * 3)  # tilt back slightly
            elif attack_progress < 0.55:
                t = (attack_progress - 0.35) / 0.2
                staff_lean = int((-3 + t * 10))  # thrust forward
            else:
                t = (attack_progress - 0.55) / 0.45
                staff_lean = int(7 * (1 - t))
        else:
            staff_lean = 0
        # Hand position (grip on staff)
        hand_x = shoulder_x + facing * 4 + int(staff_lean * 0.5)
        hand_y = shoulder_y + 6 + int(arm_sway)
        # Elbow
        elbow_x = shoulder_x + facing * 2 + int(staff_lean * 0.3)
        elbow_y = shoulder_y + 3
        # Draw arm
        _NS_lyrenya._draw_slim_arm(surface, (shoulder_x, shoulder_y),
                                    (elbow_x, elbow_y), (hand_x, hand_y),
                                    depth_shade=1.0)
        # Draw STAFF vertical
        _NS_lyrenya._draw_staff(surface, hand_x, hand_y, facing, phase, staff_lean, action, attack_progress)
        # Draw hand gripping staff
        _NS_lyrenya._draw_hand(surface, hand_x, hand_y, facing, phase, depth_shade=1.0)
    def _draw_slim_arm(surface, shoulder, elbow, hand, depth_shade=1.0):
        """Slim feminine arm with skin tone."""
        def shade(color):
            return tuple(int(c * depth_shade) for c in color)
        # Upper arm
        _NS_lyrenya._aaline(surface, _NS_lyrenya.PALETTE["shadow_deep"],
                (shoulder[0] + 1, shoulder[1] + 1),
                (elbow[0] + 1, elbow[1] + 1), 4)
        _NS_lyrenya._aaline(surface, shade(_NS_lyrenya.PALETTE["skin_darkest"]),
                shoulder, elbow, 3)
        _NS_lyrenya._aaline(surface, shade(_NS_lyrenya.PALETTE["skin_dark"]),
                shoulder, elbow, 2)
        _NS_lyrenya._aaline(surface, shade(_NS_lyrenya.PALETTE["skin_mid"]),
                (shoulder[0], shoulder[1] - 1), (elbow[0], elbow[1] - 1), 1)
        # Forearm
        _NS_lyrenya._aaline(surface, _NS_lyrenya.PALETTE["shadow_deep"],
                (elbow[0] + 1, elbow[1] + 1),
                (hand[0] + 1, hand[1] + 1), 4)
        _NS_lyrenya._aaline(surface, shade(_NS_lyrenya.PALETTE["skin_darkest"]),
                elbow, hand, 3)
        _NS_lyrenya._aaline(surface, shade(_NS_lyrenya.PALETTE["skin_dark"]),
                elbow, hand, 2)
        _NS_lyrenya._aaline(surface, shade(_NS_lyrenya.PALETTE["skin_mid"]),
                (elbow[0], elbow[1] - 1), (hand[0], hand[1] - 1), 1)
    def _draw_hand(surface, cx, cy, facing, phase, depth_shade=1.0):
        """Small feminine hand."""
        def shade(color):
            return tuple(int(c * depth_shade) for c in color)
        pygame.draw.rect(surface, shade(_NS_lyrenya.PALETTE["skin_darkest"]),
                         (cx - 2, cy - 1, 4, 4))
        pygame.draw.rect(surface, shade(_NS_lyrenya.PALETTE["skin_dark"]),
                         (cx - 2, cy - 1, 4, 3))
        pygame.draw.rect(surface, shade(_NS_lyrenya.PALETTE["skin_mid"]),
                         (cx - 2, cy - 1, 4, 1))
    def _draw_staff(surface, hand_x, hand_y, facing, phase, lean, action, attack_progress):
        """Wooden staff with crystal top."""
        # Staff extends up from hand (with lean tilt)
        top_y = hand_y - 40
        top_x = hand_x + int(lean * 0.7)
        bot_y = hand_y + 20
        bot_x = hand_x + int(lean * 0.3)
        # Staff wooden shaft
        pygame.draw.line(surface, _NS_lyrenya.PALETTE["shadow_deep"],
                         (top_x + 1, top_y + 1), (bot_x + 1, bot_y + 1), 4)
        pygame.draw.line(surface, _NS_lyrenya.PALETTE["wood_dark"],
                         (top_x, top_y), (bot_x, bot_y), 3)
        pygame.draw.line(surface, _NS_lyrenya.PALETTE["wood_mid"],
                         (top_x, top_y), (bot_x, bot_y), 2)
        pygame.draw.line(surface, _NS_lyrenya.PALETTE["wood_light"],
                         (top_x - 1, top_y), (bot_x - 1, bot_y), 1)
        # Wood knots/texture
        for i in range(3):
            knot_y = top_y + (i + 1) * 12
            pygame.draw.rect(surface, _NS_lyrenya.PALETTE["shadow_deep"],
                             (top_x + int(lean * 0.5 * (1 - i / 3)) - 1, knot_y, 2, 1))
        # Wrapping (twine near top)
        wrap_y = top_y + 6
        pygame.draw.line(surface, _NS_lyrenya.PALETTE["wood_dark"],
                         (top_x - 2, wrap_y), (top_x + 2, wrap_y), 1)
        pygame.draw.line(surface, _NS_lyrenya.PALETTE["wood_light"],
                         (top_x - 2, wrap_y + 1), (top_x + 2, wrap_y + 1), 1)
        # CRYSTAL AT TOP (glowing green)
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        crystal_x = top_x
        crystal_y = top_y - 4
        # Casting glow bigger when attacking
        glow_boost = 1.5 if action == "attack" else 1.0
        # Big halo
        for r in range(12, 0, -1):
            alpha = _NS_lyrenya._alpha(140 * (12 - r) / 12 * pulse * glow_boost)
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_mid"], alpha),
                                  (crystal_x, crystal_y), r)
        # Crystal shape (pointed diamond)
        pts = [
            (crystal_x, crystal_y - 6),
            (crystal_x + 3, crystal_y - 2),
            (crystal_x + 3, crystal_y + 2),
            (crystal_x, crystal_y + 5),
            (crystal_x - 3, crystal_y + 2),
            (crystal_x - 3, crystal_y - 2),
        ]
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in pts])
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["magic_darkest"], pts)
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["magic_dark"], [
            (crystal_x, crystal_y - 5),
            (crystal_x + 2, crystal_y - 2),
            (crystal_x + 2, crystal_y + 1),
            (crystal_x, crystal_y + 4),
            (crystal_x - 2, crystal_y + 1),
            (crystal_x - 2, crystal_y - 2),
        ])
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["magic_mid"], [
            (crystal_x, crystal_y - 4),
            (crystal_x + 1, crystal_y - 2),
            (crystal_x + 1, crystal_y),
            (crystal_x, crystal_y + 3),
            (crystal_x - 1, crystal_y),
            (crystal_x - 1, crystal_y - 2),
        ])
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["magic_light"], [
            (crystal_x, crystal_y - 3),
            (crystal_x + 1, crystal_y - 1),
            (crystal_x, crystal_y + 1),
            (crystal_x - 1, crystal_y - 1),
        ])
        pygame.draw.rect(surface, _NS_lyrenya.PALETTE["magic_shine"], (crystal_x, crystal_y - 2, 1, 1))
        pygame.draw.rect(surface, _NS_lyrenya.PALETTE["white"], (crystal_x, crystal_y - 2, 1, 1))
        # Small leaves around crystal (nature decoration)
        for i, angle in enumerate([-0.5, 0.5, math.pi - 0.5, math.pi + 0.5]):
            lx = crystal_x + int(math.cos(angle) * 4)
            ly = crystal_y + 2 + int(math.sin(angle) * 3)
            _NS_lyrenya._draw_small_leaf(surface, lx, ly, angle * 0.3)
        # Sparkles from crystal
        for i in range(4):
            sp_angle = phase * 2 + i * math.pi / 2
            sp_r = 8 + int(math.sin(phase * 3 + i) * 3)
            sx = crystal_x + int(math.cos(sp_angle) * sp_r)
            sy = crystal_y + int(math.sin(sp_angle) * sp_r)
            alpha = _NS_lyrenya._alpha(200 * pulse)
            pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["magic_hot"], alpha), (sx, sy, 1, 1))
            pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["magic_shine"], alpha), (sx, sy, 1, 1))
    def _draw_hair_back(surface, cx, cy, facing, phase):
        """Long flowing hair behind body."""
        sway = math.sin(phase * 0.5) * 2
        # Big hair mass fanning out behind head/shoulders
        hair_shape = [
            (cx - 12, cy - 4),
            (cx - 15 + int(sway * 0.5), cy + 4),
            (cx - 16 + int(sway), cy + 14),
            (cx - 14 + int(sway), cy + 22),
            (cx - 10 + int(sway), cy + 28),
            (cx - 4, cy + 30),
            (cx + 4, cy + 30),
            (cx + 10 + int(sway * 0.3), cy + 28),
            (cx + 14 + int(sway * 0.3), cy + 22),
            (cx + 16 + int(sway * 0.5), cy + 14),
            (cx + 15, cy + 4),
            (cx + 12, cy - 4),
        ]
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in hair_shape])
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["hair_darkest"], hair_shape)
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["hair_dark"], [
            (cx - 11, cy - 3), (cx - 14 + int(sway * 0.4), cy + 4),
            (cx - 15 + int(sway * 0.8), cy + 13),
            (cx - 13 + int(sway * 0.8), cy + 21),
            (cx - 9 + int(sway * 0.7), cy + 27),
            (cx - 3, cy + 29), (cx + 3, cy + 29),
            (cx + 9 + int(sway * 0.2), cy + 27),
            (cx + 13 + int(sway * 0.2), cy + 21),
            (cx + 15 + int(sway * 0.4), cy + 13),
            (cx + 14, cy + 4), (cx + 11, cy - 3),
        ])
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["hair_mid"], [
            (cx - 8, cy), (cx - 11, cy + 6),
            (cx - 12, cy + 14), (cx - 9, cy + 22),
            (cx - 5, cy + 26), (cx + 5, cy + 26),
            (cx + 9, cy + 22), (cx + 12, cy + 14),
            (cx + 11, cy + 6), (cx + 8, cy),
        ])
        # Bright hair strands
        for i, x_off in enumerate((-9, -5, 5, 9)):
            hy1 = cy + 4
            hy2 = cy + 22 + i
            pygame.draw.line(surface, _NS_lyrenya.PALETTE["hair_light"],
                             (cx + x_off + int(sway * 0.3), hy1),
                             (cx + x_off + int(sway * 0.5), hy2), 1)
            pygame.draw.line(surface, _NS_lyrenya.PALETTE["hair_shine"],
                             (cx + x_off - 1 + int(sway * 0.3), hy1),
                             (cx + x_off - 1 + int(sway * 0.5), hy2), 1)
    def _draw_hair_front(surface, cx, cy, facing, phase):
        """Front hair strands framing face."""
        sway = math.sin(phase * 0.5) * 1
        # Two side strands
        for side in (-1, 1):
            base_x = cx + side * 6
            base_y = cy - 4
            tip_x = base_x + side * 2 + int(sway * side)
            tip_y = base_y + 12
            pygame.draw.line(surface, _NS_lyrenya.PALETTE["hair_darkest"],
                             (base_x, base_y), (tip_x, tip_y), 3)
            pygame.draw.line(surface, _NS_lyrenya.PALETTE["hair_dark"],
                             (base_x, base_y), (tip_x, tip_y), 2)
            pygame.draw.line(surface, _NS_lyrenya.PALETTE["hair_mid"],
                             (base_x - 1, base_y), (tip_x - 1, tip_y), 1)
            pygame.draw.line(surface, _NS_lyrenya.PALETTE["hair_light"],
                             (base_x - 1, base_y + 2), (tip_x - 1, tip_y - 2), 1)
    def _draw_head(surface, cx, cy, facing, phase):
        """Elf face with pointed ears."""
        # Face shape (oval, feminine)
        face_shape = [
            (cx - 5, cy + 6),
            (cx - 6, cy + 2),
            (cx - 6, cy - 3),
            (cx - 3, cy - 7),
            (cx + 3, cy - 7),
            (cx + 6, cy - 3),
            (cx + 6, cy + 2),
            (cx + 5, cy + 6),
            (cx + 2, cy + 8),
            (cx - 2, cy + 8),
        ]
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in face_shape])
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["skin_darkest"], face_shape)
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["skin_dark"], [
            (cx - 4, cy + 5), (cx - 5, cy + 2),
            (cx - 5, cy - 2), (cx - 2, cy - 6),
            (cx + 2, cy - 6), (cx + 5, cy - 2),
            (cx + 5, cy + 2), (cx + 4, cy + 5),
            (cx + 1, cy + 7), (cx - 1, cy + 7),
        ])
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["skin_mid"], [
            (cx - 3, cy + 3), (cx - 4, cy),
            (cx - 3, cy - 4), (cx - 1, cy - 5),
            (cx + 1, cy - 5), (cx + 3, cy - 4),
            (cx + 4, cy), (cx + 3, cy + 3),
        ])
        # Cheek highlight
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["skin_light"], [
            (cx - 3, cy - 1), (cx - 1, cy - 3),
            (cx - 1, cy), (cx - 3, cy + 1),
        ])
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["skin_light"], [
            (cx + 1, cy - 3), (cx + 3, cy - 1),
            (cx + 3, cy + 1), (cx + 1, cy),
        ])
        # POINTED ELF EARS
        for side in (-1, 1):
            ex = cx + side * 6
            ey = cy + 1
            _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["skin_darkest"], [
                (ex, ey - 2), (ex + side * 3, ey - 5),
                (ex + side * 2, ey), (ex, ey + 2),
            ])
            _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["skin_dark"], [
                (ex, ey - 1), (ex + side * 2, ey - 4),
                (ex + side, ey), (ex, ey + 1),
            ])
            _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["skin_mid"], [
                (ex, ey), (ex + side, ey - 3),
                (ex + side, ey - 1),
            ])
            # Earring (small gold)
            pygame.draw.rect(surface, _NS_lyrenya.PALETTE["gold_mid"], (ex, ey + 2, 1, 1))
            pygame.draw.rect(surface, _NS_lyrenya.PALETTE["gold_light"], (ex, ey + 3, 1, 1))
        # EYES (green with shine)
        for eye_x in (cx - 2, cx + 2):
            # Eye white
            pygame.draw.rect(surface, _NS_lyrenya.PALETTE["skin_shine"],
                             (eye_x - 1, cy - 2, 2, 2))
            # Iris (green)
            pygame.draw.rect(surface, _NS_lyrenya.PALETTE["eye_dark"],
                             (eye_x - 1, cy - 2, 2, 2))
            pygame.draw.rect(surface, _NS_lyrenya.PALETTE["eye_mid"],
                             (eye_x - 1, cy - 1, 2, 1))
            pygame.draw.rect(surface, _NS_lyrenya.PALETTE["eye_light"],
                             (eye_x, cy - 1, 1, 1))
            # Sparkle
            pygame.draw.rect(surface, _NS_lyrenya.PALETTE["eye_shine"],
                             (eye_x, cy - 2, 1, 1))
            pygame.draw.rect(surface, _NS_lyrenya.PALETTE["white"],
                             (eye_x, cy - 2, 1, 1))
        # Eyebrows (subtle)
        pygame.draw.line(surface, _NS_lyrenya.PALETTE["hair_dark"],
                         (cx - 3, cy - 3), (cx - 1, cy - 4), 1)
        pygame.draw.line(surface, _NS_lyrenya.PALETTE["hair_dark"],
                         (cx + 1, cy - 4), (cx + 3, cy - 3), 1)
        # Nose (subtle)
        pygame.draw.rect(surface, _NS_lyrenya.PALETTE["skin_dark"], (cx, cy + 1, 1, 2))
        # Mouth (small smile)
        pygame.draw.line(surface, _NS_lyrenya.PALETTE["hair_darkest"],
                         (cx - 1, cy + 5), (cx + 1, cy + 5), 1)
        pygame.draw.rect(surface, _NS_lyrenya.PALETTE["hair_dark"], (cx - 1, cy + 4, 3, 1))
        # Lip shine
        pygame.draw.rect(surface, _NS_lyrenya.PALETTE["hair_mid"], (cx, cy + 5, 1, 1))
    def _draw_antlers(surface, cx, cy, facing, phase):
        """Golden antlers/crown branching up."""
        # Central crown gem
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        alpha = _NS_lyrenya._alpha(230 * pulse)
        # Center leaf/gem
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["gold_dark"], [
            (cx, cy - 2), (cx + 2, cy),
            (cx, cy + 2), (cx - 2, cy),
        ])
        _NS_lyrenya._poly(surface, _NS_lyrenya.PALETTE["gold_mid"], [
            (cx, cy - 1), (cx + 1, cy),
            (cx, cy + 1), (cx - 1, cy),
        ])
        for r in range(4, 0, -1):
            a = _NS_lyrenya._alpha(150 * (4 - r) / 4 * pulse)
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_mid"], a), (cx, cy), r)
        pygame.draw.rect(surface, _NS_lyrenya.PALETTE["magic_shine"], (cx, cy, 1, 1))
        # ANTLERS branching out (like deer antlers)
        for side in (-1, 1):
            # Main antler stem
            base_x = cx + side * 3
            base_y = cy + 1
            # Multiple branches
            branch_configs = [
                (0.7, 8, 0),       # main upward
                (1.0, 6, 1),       # side branch
                (0.5, 10, 0),      # inner tall
                (1.2, 5, 2),       # low side
            ]
            for angle_mult, length, branch_i in branch_configs:
                angle = math.pi * (0.5 + angle_mult * 0.3) * side
                tip_x = base_x + int(math.cos(angle) * length * side)
                tip_y = base_y - int(math.sin(angle) * length)
                # Draw antler line (gold)
                pygame.draw.line(surface, _NS_lyrenya.PALETTE["shadow_deep"],
                                 (base_x + 1, base_y + 1), (tip_x + 1, tip_y + 1), 3)
                pygame.draw.line(surface, _NS_lyrenya.PALETTE["gold_darkest"],
                                 (base_x, base_y), (tip_x, tip_y), 2)
                pygame.draw.line(surface, _NS_lyrenya.PALETTE["gold_mid"],
                                 (base_x, base_y), (tip_x, tip_y), 1)
                # Bright tip
                pygame.draw.rect(surface, _NS_lyrenya.PALETTE["gold_light"], (tip_x, tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_lyrenya.PALETTE["gold_shine"], (tip_x, tip_y, 1, 1))
                # Small sub-branch mid-way
                if branch_i == 0 and length > 6:
                    mid_x = (base_x + tip_x) // 2
                    mid_y = (base_y + tip_y) // 2
                    sub_tip_x = mid_x + side * 3
                    sub_tip_y = mid_y - 2
                    pygame.draw.line(surface, _NS_lyrenya.PALETTE["gold_darkest"],
                                     (mid_x, mid_y), (sub_tip_x, sub_tip_y), 1)
                    pygame.draw.line(surface, _NS_lyrenya.PALETTE["gold_mid"],
                                     (mid_x, mid_y), (sub_tip_x, sub_tip_y), 1)
                    pygame.draw.rect(surface, _NS_lyrenya.PALETTE["gold_light"],
                                     (sub_tip_x, sub_tip_y, 1, 1))
            # Small leaves on antler branches
            for i, (lx, ly) in enumerate([(side * 5, -3), (side * 7, 2)]):
                _NS_lyrenya._draw_small_leaf(surface, cx + lx, cy + ly, 0.2 * side)
    def _draw_orbiting_leaves(surface, cx, cy, facing, phase):
        """Floating leaves/butterflies around."""
        for i in range(4):
            angle = phase * 0.4 + i * math.pi / 2
            radius_x = 25
            radius_y = 12
            rx = cx + int(math.cos(angle) * radius_x)
            ry = cy - 5 + int(math.sin(angle) * radius_y)
            pulse = math.sin(phase * 2 + i) * 0.3 + 0.7
            # Alternating leaf and butterfly
            if i % 2 == 0:
                _NS_lyrenya._draw_small_leaf(surface, rx, ry, angle * 0.3)
            else:
                # Butterfly (small)
                alpha = _NS_lyrenya._alpha(220 * pulse)
                flap = math.sin(phase * 8 + i)
                wing_w = 2 + int(abs(flap))
                pygame.draw.ellipse(surface, (*_NS_lyrenya.PALETTE["magic_light"], alpha),
                                    (rx - wing_w, ry - 1, wing_w, 2))
                pygame.draw.ellipse(surface, (*_NS_lyrenya.PALETTE["magic_light"], alpha),
                                    (rx, ry - 1, wing_w, 2))
                pygame.draw.rect(surface, _NS_lyrenya.PALETTE["magic_mid"], (rx, ry, 1, 1))
    # ============================================================
    # AUTO-ATTACK - NATURE BOLT PROJECTILE
    # ============================================================
    def _draw_nature_projectile(surface, boss, x, y, progress):
        """Golden nature bolt from staff crystal."""
        facing = boss.direction
        # Crystal position (top of staff)
        crystal_x = x + facing * 13
        crystal_y = y - 27
        if progress < 0.35:
            # Charge glow at crystal
            t = progress / 0.35
            cr = int(3 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_lyrenya._alpha(200 * (cr + 4 - r) / (cr + 4) * t)
                _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_mid"], alpha),
                                      (crystal_x, crystal_y), r)
            _NS_lyrenya._aacircle(surface, _NS_lyrenya.PALETTE["magic_light"],
                                  (crystal_x, crystal_y), max(1, cr - 2))
            _NS_lyrenya._aacircle(surface, _NS_lyrenya.PALETTE["magic_shine"],
                                  (crystal_x, crystal_y), max(1, cr - 4))
            for i in range(4):
                angle = progress * 20 + i * math.pi / 2
                sx = crystal_x + int(math.cos(angle) * (cr + 2))
                sy = crystal_y + int(math.sin(angle) * (cr + 2))
                pygame.draw.rect(surface, _NS_lyrenya.PALETTE["magic_hot"], (sx, sy, 1, 1))
            return
        if progress < 0.55:
            return
        # Travel phase
        tx, ty = _NS_lyrenya._target_position(boss, x, y)
        start_x = crystal_x
        start_y = crystal_y
        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Comet trail
        for i in range(9):
            trail_t = max(0.0, t - i * 0.045)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_lyrenya._alpha(230 - i * 25)
            size = max(1, 7 - i)
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_darkest"], alpha),
                                  (px, py), size)
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_dark"], alpha),
                                  (px, py), max(1, size - 1))
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_mid"], alpha),
                                  (px, py), max(1, size - 2))
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_light"], alpha),
                                  (px, py), max(1, size - 3))
            # Leaf sparkles trailing
            if i < 4:
                for s in range(2):
                    sp_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    sp_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["leaf_light"], alpha),
                                     (sp_x, sp_y, 1, 1))
                    pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["magic_hot"], alpha),
                                     (sp_x, sp_y, 1, 1))
        # Bright bolt head
        for r in range(10, 3, -1):
            alpha = _NS_lyrenya._alpha(90 * (10 - r) / 10)
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_light"], alpha), (bx, by), r)
        _NS_lyrenya._aacircle(surface, _NS_lyrenya.PALETTE["magic_darkest"], (bx, by), 7)
        _NS_lyrenya._aacircle(surface, _NS_lyrenya.PALETTE["magic_dark"], (bx, by), 5)
        _NS_lyrenya._aacircle(surface, _NS_lyrenya.PALETTE["magic_mid"], (bx, by), 3)
        _NS_lyrenya._aacircle(surface, _NS_lyrenya.PALETTE["magic_light"], (bx, by), 2)
        _NS_lyrenya._aacircle(surface, _NS_lyrenya.PALETTE["magic_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_lyrenya.PALETTE["white"], (bx, by, 1, 1))
        # Impact
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(8 + st * 22)
            alpha = _NS_lyrenya._alpha(240 * (1 - st))
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_dark"], alpha),
                                  (tx, ty), radius, 3)
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_mid"], alpha),
                                  (tx, ty), max(1, radius - 4), 2)
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_light"], alpha),
                                  (tx, ty), max(1, radius - 8), 1)
            for i in range(10):
                a_s = i * math.pi / 5
                ex = tx + int(math.cos(a_s) * radius)
                ey = ty + int(math.sin(a_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["magic_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["leaf_light"], alpha),
                                 (ex, ey, 1, 1))
    # ============================================================
    # NATURE BASE (floating below - roots/vines)
    # ============================================================
    def _draw_nature_base(surface, cx, cy, phase, intense=False, moving=False, facing=1):
        """Green nature aura + swirling leaves below floating body."""
        strength = 1.3 if intense else 1.0
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        # Base green glow (like grass mist)
        smoke = pygame.Surface((100, 50), pygame.SRCALPHA)
        for radius in range(20, 3, -2):
            alpha = _NS_lyrenya._alpha((20 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    smoke, (*_NS_lyrenya.PALETTE["dress_darkest"], alpha),
                    (50 - radius, 25 - radius // 2, radius * 2, max(3, radius)))
        for radius in range(14, 3, -2):
            alpha = _NS_lyrenya._alpha((14 - radius) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    smoke, (*_NS_lyrenya.PALETTE["dress_dark"], alpha),
                    (50 - radius, 25 - radius // 2, radius * 2, max(2, radius)))
        surface.blit(smoke, (cx - 50, cy - 12))
        # Small leaves swirling upward
        for i in range(6):
            t = (phase * 0.6 + i * 0.16) % 1.0
            angle = i * math.pi / 3 + phase * 0.3
            px = cx + int(math.cos(angle) * 12) + int(math.sin(phase + i) * 3)
            py = cy + 10 - int(t * 20)
            alpha = _NS_lyrenya._alpha(200 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["leaf_dark"], alpha),
                                 (px, py, 2, 2))
                pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["leaf_mid"], alpha),
                                 (px, py, 1, 1))
                pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["leaf_light"], alpha),
                                 (px, py, 1, 1))
        # Rising magic sparkles
        for i in range(8):
            t = (phase * 0.7 + i * 0.13) % 1.0
            sx = cx - 16 + i * 5 + int(math.sin(phase * 2 + i) * 3)
            sy = cy + 10 - int(t * 22)
            alpha = _NS_lyrenya._alpha(230 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["magic_light"], alpha), (sx, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["magic_hot"], alpha), (sx, sy - 1, 1, 1))
        if moving:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + 8 + int(math.sin(phase + i) * 2)
                alpha = _NS_lyrenya._alpha(160 - i * 30)
                if alpha <= 0:
                    continue
                _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["dress_dark"], alpha),
                                      (sx, sy), max(2, 6 - i))
                pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["leaf_light"], alpha),
                                 (sx, sy - 1, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 12)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius, 120 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (5, 15, 5, 150), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (25, 50, 15, 90), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_nature_aura(surface, x, y, phase):
        """Warm green nature aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_lyrenya._alpha((95 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_lyrenya._aacircle(aura, (*_NS_lyrenya.PALETTE["dress_darkest"], alpha),
                                      (110, 100), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_lyrenya._alpha((60 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_lyrenya._aacircle(aura, (*_NS_lyrenya.PALETTE["dress_dark"], alpha),
                                      (110, 100), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_lyrenya._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_lyrenya._aacircle(aura, (*_NS_lyrenya.PALETTE["magic_darkest"], alpha),
                                      (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))
        # Floating leaves + fireflies
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 45 + int(math.sin(phase + i) * 14)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            if i % 3 == 0:
                # Leaf
                pygame.draw.rect(surface, _NS_lyrenya.PALETTE["leaf_dark"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_lyrenya.PALETTE["leaf_mid"], (sx, sy, 1, 1))
                pygame.draw.rect(surface, _NS_lyrenya.PALETTE["leaf_light"], (sx, sy, 1, 1))
            else:
                # Firefly
                twinkle = math.sin(phase * 3 + i) * 0.5 + 0.5
                if twinkle > 0.4:
                    pygame.draw.rect(surface, _NS_lyrenya.PALETTE["magic_hot"], (sx, sy, 1, 1))
                    pygame.draw.rect(surface, _NS_lyrenya.PALETTE["magic_shine"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_lyrenya.PALETTE["dress_darkest"], 200),
                            (5, 20, 170, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_lyrenya.PALETTE["dress_dark"], 220),
                            (14, 22, 152, 24), 2)
        pygame.draw.ellipse(ring, (*_NS_lyrenya.PALETTE["magic_dark"], 180),
                            (25, 24, 130, 20), 1)
        # Rune leaves
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 34 + int(math.sin(angle) * 9)
            x2 = 90 + int(math.cos(angle) * 76)
            y2 = 34 + int(math.sin(angle) * 13)
            pygame.draw.line(ring, (*_NS_lyrenya.PALETTE["magic_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_lyrenya.PALETTE["magic_hot"],
                                       _NS_lyrenya._alpha(150 * pulse)),
                                (15, 12, 150, 42), 1)
        surface.blit(ring, (x - 90, y - 30))
    # ============================================================
    # SKILL Q - IMPETUS (charged nature beam)
    # ============================================================
    def _draw_naturebolt_skill(surface, boss, x, y, timer, phase):
        """Enhanced nature bolt piercing to target."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_lyrenya._target_position(boss, x, y)
        crystal_x = x + facing * 13
        crystal_y = y - 27
        if progress < 0.25:
            # Big charge
            t = progress / 0.25
            cr = int(4 + t * 12)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_lyrenya._alpha(220 * (cr + 6 - r) / (cr + 6))
                _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_darkest"], alpha),
                                      (crystal_x, crystal_y), r)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_lyrenya._alpha(220 * (cr + 3 - r) / (cr + 3))
                _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_dark"], alpha),
                                      (crystal_x, crystal_y), r)
            _NS_lyrenya._aacircle(surface, _NS_lyrenya.PALETTE["magic_mid"], (crystal_x, crystal_y), cr - 2)
            _NS_lyrenya._aacircle(surface, _NS_lyrenya.PALETTE["magic_light"], (crystal_x, crystal_y), max(1, cr - 5))
            _NS_lyrenya._aacircle(surface, _NS_lyrenya.PALETTE["magic_shine"], (crystal_x, crystal_y), max(1, cr - 7))
            pygame.draw.rect(surface, _NS_lyrenya.PALETTE["white"], (crystal_x, crystal_y, 1, 1))
            for i in range(10):
                angle = phase * 3 + i * math.pi / 5
                sx = crystal_x + int(math.cos(angle) * (cr + 4))
                sy = crystal_y + int(math.sin(angle) * (cr + 4))
                pygame.draw.rect(surface, _NS_lyrenya.PALETTE["magic_hot"], (sx, sy, 1, 1))
            return
        # Beam/projectile phase
        t = (progress - 0.25) / 0.75
        t = min(1.0, t)
        bx = int(crystal_x + (tx - crystal_x) * t)
        by = int(crystal_y + (ty - crystal_y) * t)
        # Continuous beam
        beam_wobble = math.sin(phase * 15) * 1
        # Beam from crystal to bolt head
        for layer_i, (w, alpha_val) in enumerate([
            (5, 80), (4, 130), (3, 180), (2, 220), (1, 255),
        ]):
            colors = [
                _NS_lyrenya.PALETTE["magic_darkest"],
                _NS_lyrenya.PALETTE["magic_dark"],
                _NS_lyrenya.PALETTE["magic_mid"],
                _NS_lyrenya.PALETTE["magic_light"],
                _NS_lyrenya.PALETTE["magic_shine"],
            ]
            color = colors[min(layer_i, 4)]
            pygame.draw.line(surface, (*color, alpha_val),
                             (crystal_x, crystal_y),
                             (bx, by + int(beam_wobble)), w)
        # Bright head
        for r in range(14, 3, -1):
            alpha = _NS_lyrenya._alpha(100 * (14 - r) / 14)
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_light"], alpha), (bx, by), r)
        _NS_lyrenya._aacircle(surface, _NS_lyrenya.PALETTE["magic_dark"], (bx, by), 8)
        _NS_lyrenya._aacircle(surface, _NS_lyrenya.PALETTE["magic_mid"], (bx, by), 5)
        _NS_lyrenya._aacircle(surface, _NS_lyrenya.PALETTE["magic_light"], (bx, by), 3)
        _NS_lyrenya._aacircle(surface, _NS_lyrenya.PALETTE["magic_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_lyrenya.PALETTE["white"], (bx, by, 1, 1))
        # Falling leaves along beam
        for i in range(8):
            leaf_t = (phase * 1.2 + i * 0.12) % 1.0
            px = int(crystal_x + (tx - crystal_x) * leaf_t)
            py = int(crystal_y + (ty - crystal_y) * leaf_t + math.sin(phase + i) * 4)
            alpha = _NS_lyrenya._alpha(230 * (1 - leaf_t * 0.3))
            _NS_lyrenya._draw_small_leaf(surface, px, py, phase + i)
        # Impact
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(10 + st * 20)
            alpha = _NS_lyrenya._alpha(240 * (1 - st))
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_dark"], alpha),
                                  (tx, ty), radius, 3)
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_mid"], alpha),
                                  (tx, ty), max(1, radius - 5), 2)
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_light"], alpha),
                                  (tx, ty), max(1, radius - 10), 1)
            for i in range(12):
                a_s = i * math.pi / 6
                ex = tx + int(math.cos(a_s) * radius)
                ey = ty + int(math.sin(a_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["magic_hot"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # SKILL W - CHARM (enchant beam)
    # ============================================================
    def _draw_charm_skill(surface, boss, x, y, timer, phase):
        """Charm beam connecting boss to target with hearts."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_lyrenya._target_position(boss, x, y)
        crystal_x = x + facing * 13
        crystal_y = y - 27
        # Continuous connection beam (soft)
        if progress > 0.1:
            # Gentle wavy beam
            num_pts = 20
            prev_pt = (crystal_x, crystal_y)
            for i in range(1, num_pts + 1):
                t = i / num_pts
                base_x = int(crystal_x + (tx - crystal_x) * t)
                base_y = int(crystal_y + (ty - crystal_y) * t)
                wave = math.sin(phase * 3 + t * math.pi * 4) * 4 * (t * (1 - t) * 4)
                # Perpendicular offset
                dx = tx - crystal_x
                dy = ty - crystal_y
                length = math.hypot(dx, dy) or 1
                perp_x = -dy / length
                perp_y = dx / length
                next_pt = (base_x + int(perp_x * wave), base_y + int(perp_y * wave))
                # Draw multi-layer
                for w, col, alpha_val in [
                    (3, _NS_lyrenya.PALETTE["magic_dark"], 120),
                    (2, _NS_lyrenya.PALETTE["magic_mid"], 180),
                    (1, _NS_lyrenya.PALETTE["magic_light"], 240),
                ]:
                    pygame.draw.line(surface, (*col, alpha_val), prev_pt, next_pt, w)
                prev_pt = next_pt
        # Sparkles flowing along beam
        for i in range(6):
            flow_t = ((phase * 1.5 + i * 0.16) % 1.0)
            fx = int(crystal_x + (tx - crystal_x) * flow_t)
            fy = int(crystal_y + (ty - crystal_y) * flow_t)
            alpha = _NS_lyrenya._alpha(240)
            pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["magic_hot"], alpha), (fx, fy, 2, 2))
            pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["magic_shine"], alpha), (fx, fy, 1, 1))
        # Charm effect at target (hearts/butterflies rising)
        if progress > 0.3:
            for i in range(4):
                heart_t = (phase * 0.5 + i * 0.25) % 1.0
                hx = tx + int(math.sin(phase + i) * 10)
                hy = ty - int(heart_t * 25)
                alpha = _NS_lyrenya._alpha(230 * (1 - heart_t))
                # Small heart-ish shape (or butterfly)
                _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_mid"], alpha),
                                      (hx - 1, hy), 2)
                _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_mid"], alpha),
                                      (hx + 1, hy), 2)
                pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["magic_light"], alpha),
                                 (hx, hy + 2, 1, 1))
        # Bright core at target
        pulse = math.sin(phase * 4) * 0.3 + 0.7
        for r in range(8, 0, -1):
            alpha = _NS_lyrenya._alpha(150 * (8 - r) / 8 * pulse)
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_mid"], alpha), (tx, ty), r)
        _NS_lyrenya._aacircle(surface, _NS_lyrenya.PALETTE["magic_shine"], (tx, ty), 2)
        pygame.draw.rect(surface, _NS_lyrenya.PALETTE["white"], (tx, ty, 1, 1))
    # ============================================================
    # SKILL E - NATURE'S ATTENDANTS (deer minions)
    # ============================================================
    def _draw_attendants_ground(surface, boss, x, y, timer, phase):
        """Portal circles where deer spawn."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # 2 spawn positions
        for i, side in enumerate([-1, 1]):
            portal_x = x + side * 40
            portal_y = y + 45
            r = int(15 * min(1.0, progress * 2))
            if r > 2:
                pygame.draw.ellipse(surface, _NS_lyrenya.PALETTE["shadow"],
                                    (portal_x - r, portal_y - r // 3, r * 2, r * 2 // 3))
                pygame.draw.ellipse(surface, _NS_lyrenya.PALETTE["dress_darkest"],
                                    (portal_x - r + 1, portal_y - r // 3 + 1,
                                     r * 2 - 2, r * 2 // 3 - 2))
                pygame.draw.ellipse(surface, _NS_lyrenya.PALETTE["magic_dark"],
                                    (portal_x - r + 3, portal_y - r // 3 + 2,
                                     r * 2 - 6, r * 2 // 3 - 4))
                # Rotating leaves
                for j in range(6):
                    angle = phase * 2 + j * math.pi / 3
                    px = portal_x + int(math.cos(angle) * r)
                    py = portal_y + int(math.sin(angle) * r * 0.4)
                    pygame.draw.rect(surface, _NS_lyrenya.PALETTE["magic_light"], (px, py, 2, 2))
    def _draw_attendants_foreground(surface, boss, x, y, timer, phase):
        """Deer companions rising."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            return
        rise_t = min(1.0, (progress - 0.3) / 0.7 * 2)
        for i, side in enumerate([-1, 1]):
            dx = x + side * 40
            dy = y + 45 - int(rise_t * 25)
            _NS_lyrenya._draw_mini_deer(surface, dx, dy, side, phase + i, rise_t)
    def _draw_mini_deer(surface, cx, cy, facing, phase, alpha_t):
        """Small glowing deer companion."""
        alpha_mult = min(1.0, alpha_t)
        base_alpha = _NS_lyrenya._alpha(255 * alpha_mult)
        # Body (small oval)
        body_pts = [
            (cx - 6, cy - 2), (cx - 5, cy - 5),
            (cx - 2, cy - 6), (cx + 4, cy - 6),
            (cx + 7, cy - 4), (cx + 8, cy),
            (cx + 6, cy + 3), (cx - 4, cy + 3),
            (cx - 6, cy),
        ]
        _NS_lyrenya._poly(surface, (*_NS_lyrenya.PALETTE["shadow_deep"], base_alpha),
                          [(p[0] + 1, p[1] + 1) for p in body_pts])
        _NS_lyrenya._poly(surface, (*_NS_lyrenya.PALETTE["deer_dark"], base_alpha), body_pts)
        _NS_lyrenya._poly(surface, (*_NS_lyrenya.PALETTE["deer_mid"], base_alpha), [
            (cx - 5, cy - 1), (cx - 4, cy - 4),
            (cx - 1, cy - 5), (cx + 3, cy - 5),
            (cx + 6, cy - 3), (cx + 7, cy),
            (cx + 5, cy + 2), (cx - 3, cy + 2),
        ])
        _NS_lyrenya._poly(surface, (*_NS_lyrenya.PALETTE["deer_light"], base_alpha), [
            (cx - 2, cy - 3), (cx + 2, cy - 4),
            (cx + 4, cy - 2), (cx + 2, cy),
        ])
        # Head + neck
        head_x = cx + facing * 7
        head_y = cy - 5
        pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["deer_dark"], base_alpha),
                         (head_x - 2, head_y - 2, 4, 4))
        pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["deer_mid"], base_alpha),
                         (head_x - 1, head_y - 1, 3, 3))
        pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["deer_light"], base_alpha),
                         (head_x - 1, head_y - 1, 2, 1))
        # Ears
        pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["deer_dark"], base_alpha),
                         (head_x - 2, head_y - 4, 1, 2))
        pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["deer_dark"], base_alpha),
                         (head_x + 1, head_y - 4, 1, 2))
        # Legs (4)
        for lx in (-4, -2, 3, 5):
            pygame.draw.line(surface, (*_NS_lyrenya.PALETTE["deer_dark"], base_alpha),
                             (cx + lx, cy + 3), (cx + lx, cy + 8), 1)
        # Small tail
        pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["deer_light"], base_alpha),
                         (cx - facing * 6, cy - 2, 1, 2))
        # Glowing aura around deer
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(8, 0, -2):
            alpha = _NS_lyrenya._alpha(100 * (8 - r) / 8 * pulse * alpha_mult)
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_mid"], alpha),
                                  (cx, cy), r)
        # Sparkle at feet
        for i in range(3):
            angle = phase * 2 + i * math.pi / 1.5
            sx = cx + int(math.cos(angle) * 6)
            sy = cy + 6 + int(math.sin(angle) * 2)
            spa = _NS_lyrenya._alpha(240 * pulse * alpha_mult)
            pygame.draw.rect(surface, (*_NS_lyrenya.PALETTE["magic_hot"], spa), (sx, sy, 1, 1))
    # ============================================================
    # SKILL R - VERDANT SHIELD (bubble)
    # ============================================================
    def _draw_shield_ground(surface, boss, x, y, timer, phase):
        """Ring under boss."""
        for i in range(2):
            r = int(35 + i * 8 + math.sin(phase * 2) * 3)
            alpha = _NS_lyrenya._alpha(200 - i * 60)
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_light"], alpha),
                                  (x, y + 45), r, 2)
            _NS_lyrenya._aacircle(surface, (*_NS_lyrenya.PALETTE["magic_shine"], alpha),
                                  (x, y + 45), r, 1)
    def _draw_shield_foreground(surface, boss, x, y, timer, phase):
        """Green protective bubble around boss."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        breath = math.sin(phase * 2) * 3
        r = 55 + int(breath)
        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)
        # Ring layers
        for i, (thickness, alpha_val) in enumerate([(3, 100), (2, 150), (1, 220)]):
            _NS_lyrenya._aacircle(bubble, (*_NS_lyrenya.PALETTE["magic_dark"], alpha_val),
                                  center, r - i, thickness)
            _NS_lyrenya._aacircle(bubble, (*_NS_lyrenya.PALETTE["magic_mid"], alpha_val),
                                  center, r - i - 1, 1)
        # Leaves rotating around bubble
        for i in range(12):
            angle = phase * 1.2 + i * math.pi / 6
            lx = center[0] + int(math.cos(angle) * r)
            ly = center[1] + int(math.sin(angle) * r)
            _NS_lyrenya._draw_small_leaf(bubble, lx, ly, angle)
        # Sparkles inside
        for i in range(10):
            angle = phase * 0.8 + i * math.pi / 5
            inner_r = r - 8
            bx = center[0] + int(math.cos(angle) * inner_r)
            by = center[1] + int(math.sin(angle) * inner_r)
            alpha = _NS_lyrenya._alpha(200)
            _NS_lyrenya._aacircle(bubble, (*_NS_lyrenya.PALETTE["magic_hot"], alpha), (bx, by), 2)
            pygame.draw.rect(bubble, _NS_lyrenya.PALETTE["magic_shine"], (bx, by, 1, 1))
        surface.blit(bubble, (x - r - 10, y - r - 10))



# ====================================================================
# VYRAETH (HAUNTING WRAITH) - Mini Boss
# ====================================================================

class _NS_vyraeth:
    """Namespace vyraeth - Haunting Wraith boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Wraith body (dark violet/purple)
        "wraith_darkest": (10, 5, 20),
        "wraith_dark": (30, 15, 55),
        "wraith_mid": (65, 30, 105),
        "wraith_light": (120, 65, 175),
        "wraith_edge": (170, 105, 220),
        "wraith_shine": (215, 165, 245),
        # Spectral energy (bright magenta-violet)
        "spectral_darkest": (25, 5, 40),
        "spectral_dark": (75, 20, 120),
        "spectral_mid": (155, 55, 210),
        "spectral_light": (220, 130, 250),
        "spectral_hot": (245, 190, 255),
        "spectral_shine": (255, 230, 255),
        # Eye (bright violet glow)
        "eye_socket": (5, 2, 12),
        "eye_dark": (35, 10, 65),
        "eye_mid": (155, 60, 220),
        "eye_light": (230, 170, 255),
        "eye_glow": (255, 240, 255),
        # Blade/scythe (dark metal with spectral edge)
        "blade_darkest": (15, 5, 25),
        "blade_dark": (45, 25, 65),
        "blade_mid": (95, 55, 130),
        "blade_light": (170, 120, 210),
        "blade_shine": (240, 210, 250),
        # Blade handle (dark bone)
        "bone_dark": (30, 20, 35),
        "bone_mid": (85, 70, 95),
        "bone_light": (170, 155, 180),
        # Smoke tail
        "smoke_darkest": (8, 4, 18),
        "smoke_dark": (28, 15, 50),
        "smoke_mid": (65, 35, 110),
        "smoke_light": (130, 85, 180),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vyraeth._clamp(color)
        if _NS_vyraeth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_vyraeth._clamp(color)
        if _NS_vyraeth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_vyraeth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 120 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_vyraeth(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_vyraeth._detect_moving(boss)
        _NS_vyraeth._update_attack_anim(boss)
        attacking = getattr(boss, "_vyt_attack_active", False)
        # Ambient
        _NS_vyraeth._draw_spectral_aura(surface, x, y, pulse)
        _NS_vyraeth._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX
        if active_skill == "w":
            _NS_vyraeth._draw_soulrend_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vyraeth._draw_haunt_ground(surface, boss, x, y, skill_timer, pulse)
        # Body
        if active_skill == "e":
            _NS_vyraeth._draw_dispersion_body(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_vyraeth._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_vyraeth._draw_walk(surface, boss, x, y)
        else:
            _NS_vyraeth._draw_idle(surface, boss, x, y)
        # Foreground FX
        if active_skill == "q":
            _NS_vyraeth._draw_phantomdagger_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vyraeth._draw_soulrend_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vyraeth._draw_dispersion_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vyraeth._draw_haunt_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_vyt_attack_active", False))
        if not active and timer <= 2:
            boss._vyt_attack_active = True
            boss._vyt_attack_frame = 0
            active = True
        if active:
            boss._vyt_attack_frame = int(getattr(boss, "_vyt_attack_frame", 0)) + 1
            if boss._vyt_attack_frame >= cooldown:
                boss._vyt_attack_active = False
                boss._vyt_attack_frame = 0
                active = False
        boss._vyt_attack_progress = (
            min(1.0, getattr(boss, "_vyt_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_vyt_last_x"):
            boss._vyt_last_x = boss.x
            boss._vyt_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vyt_last_x)
        dy = abs(boss.y - boss._vyt_last_y)
        boss._vyt_last_x = boss.x
        boss._vyt_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 5)
        _NS_vyraeth._draw_shadow(surface, x, y + 50)
        _NS_vyraeth._draw_smoke_tail(surface, x, y + 22 + bob, boss.pulse)
        _NS_vyraeth._draw_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")
    def _draw_walk(surface, boss, x, y):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.8) * 6)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_vyraeth._draw_shadow(surface, x + sway, y + 50)
        _NS_vyraeth._draw_smoke_tail(surface, x + sway, y + 22 + bob, phase,
                                     moving=True, facing=boss.direction)
        _NS_vyraeth._draw_body(surface, x + sway, y + bob, boss.direction, phase, "walk")
    def _draw_attack(surface, boss, x, y):
        progress = getattr(boss, "_vyt_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        bob = int(math.sin(boss.pulse * 0.5) * 3)
        # Wind up → swing → recovery
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 5) * boss.direction
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            lunge = int((-5 + t * 12)) * boss.direction
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(7 * (1 - t)) * boss.direction
        _NS_vyraeth._draw_shadow(surface, x + lunge, y + 50)
        _NS_vyraeth._draw_smoke_tail(surface, x + lunge, y + 22 + bob, boss.pulse,
                                     intense=True)
        _NS_vyraeth._draw_body(surface, x + lunge, y + bob, boss.direction, boss.pulse,
                               "attack", progress)
        # Melee swing arc
        _NS_vyraeth._draw_scythe_swing(surface, boss, x + lunge, y + bob, progress)
    def _draw_dispersion_body(surface, boss, x, y, skill_timer, phase):
        """Body dissolves into spectral fragments during E."""
        duration = 70
        progress = 1 - skill_timer / duration
        # Multiple ghostly afterimages
        for i in range(4):
            offset = -boss.direction * i * 12
            alpha_mult = 1.0 - i * 0.25
            _NS_vyraeth._draw_body_ghost(surface, x + offset, y,
                                          boss.direction, phase, alpha_mult)
    def _draw_body_ghost(surface, cx, cy, facing, phase, alpha_mult):
        """Semi-transparent version of body."""
        # Just draw simplified body with alpha via temp surface
        temp = pygame.Surface((100, 100), pygame.SRCALPHA)
        _NS_vyraeth._draw_body(temp, 50, 50, facing, phase, "idle")
        temp.set_alpha(int(200 * alpha_mult))
        surface.blit(temp, (cx - 50, cy - 50))
    # ============================================================
    # BODY - Wraith with tentacle hair + scythe
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0.0):
        """Draw wraith: hair tentacles, cloak body, head, scythe."""
        # Tentacle hair behind (LOTS of tendrils)
        _NS_vyraeth._draw_hair_tentacles(surface, cx, cy - 8, facing, phase, back=True)
        # Cloak body
        _NS_vyraeth._draw_cloak_body(surface, cx, cy, facing, phase)
        # Head
        _NS_vyraeth._draw_head(surface, cx, cy - 14, facing, phase)
        # Front tentacles (few over face/shoulders)
        _NS_vyraeth._draw_hair_tentacles(surface, cx, cy - 8, facing, phase, back=False)
        # Arm + scythe
        _NS_vyraeth._draw_scythe_arm(surface, cx, cy, facing, phase, action, attack_progress)
    def _draw_hair_tentacles(surface, cx, cy, facing, phase, back=True):
        """Long shadow-tentacle hair strands."""
        if back:
            # 8 back tentacles fanning out and upward
            configs = [
                (-1.0, 1.4, 28, 0),
                (-0.85, 1.3, 32, 1),
                (-0.7, 1.15, 34, 2),
                (-0.5, 1.05, 30, 3),
                (-1.15, 1.5, 26, 4),
                (-1.3, 1.6, 22, 5),
                (0.5, 1.0, 26, 6),
                (-0.3, 0.95, 28, 7),
            ]
        else:
            # 3 front tentacles slightly forward
            configs = [
                (0.7, 0.9, 20, 10),
                (0.9, 0.7, 18, 11),
                (0.4, 0.8, 22, 12),
            ]
        for dir_x, dir_y, length, seed in configs:
            _NS_vyraeth._draw_single_tentacle(surface, cx, cy, facing,
                                              dir_x, dir_y, length, phase, seed, back)
    def _draw_single_tentacle(surface, cx, cy, facing, dir_x, dir_y, length, phase, seed, back):
        """One curly tentacle strand."""
        segments = 6
        prev_x = cx
        prev_y = cy
        # Base wave animation
        base_wave = math.sin(phase * 0.8 + seed * 0.7)
        for i in range(1, segments + 1):
            t = i / segments
            # Curl based on t
            curl_angle = t * 0.4 * (1 if seed % 2 == 0 else -1)
            wave = math.sin(phase * 1.2 + seed + t * 3) * 3 * t
            # Base direction
            angle = math.atan2(dir_y, dir_x) + curl_angle + base_wave * 0.15
            step_len = length / segments
            # Add wave perpendicular
            nx = int(prev_x + math.cos(angle) * step_len * (facing if abs(dir_x) > 0.1 else 1))
            ny = int(prev_y + math.sin(angle) * step_len + wave)
            # For back tentacles, direction is not flipped (fan out)
            if back:
                nx = int(prev_x + dir_x * step_len * facing + math.cos(phase + seed + i) * 2)
                ny = int(prev_y + dir_y * step_len - t * 3 + wave)
            else:
                nx = int(prev_x + dir_x * step_len * facing)
                ny = int(prev_y + dir_y * step_len + wave)
            thickness = max(1, 6 - i)
            # Shadow
            _NS_vyraeth._aaline(surface, _NS_vyraeth.PALETTE["shadow_deep"],
                    (prev_x + 1, prev_y + 1), (nx + 1, ny + 1), thickness + 1)
            # Dark base
            _NS_vyraeth._aaline(surface, _NS_vyraeth.PALETTE["wraith_darkest"],
                    (prev_x, prev_y), (nx, ny), thickness)
            _NS_vyraeth._aaline(surface, _NS_vyraeth.PALETTE["wraith_dark"],
                    (prev_x, prev_y), (nx, ny), max(1, thickness - 1))
            _NS_vyraeth._aaline(surface, _NS_vyraeth.PALETTE["wraith_mid"],
                    (prev_x, prev_y), (nx, ny), max(1, thickness - 3))
            # Glow edge on outer side
            if i < 4:
                _NS_vyraeth._aaline(surface, _NS_vyraeth.PALETTE["spectral_mid"],
                        (prev_x, prev_y - 1), (nx, ny - 1), max(1, thickness - 4))
            prev_x, prev_y = nx, ny
        # Bright glowing tip
        tip = (prev_x, prev_y)
        for r in range(4, 0, -1):
            alpha = _NS_vyraeth._alpha(120 * (4 - r) / 4)
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_mid"], alpha), tip, r)
        _NS_vyraeth._aacircle(surface, _NS_vyraeth.PALETTE["spectral_light"], tip, 2)
        pygame.draw.rect(surface, _NS_vyraeth.PALETTE["spectral_shine"], (tip[0], tip[1], 1, 1))
    def _draw_cloak_body(surface, cx, cy, facing, phase):
        """Wraith body - flowing dark cloak shape."""
        sway = math.sin(phase * 0.6) * 2
        # Body shape (upper wider, lower tapered/wispy)
        body_shape = [
            (cx - 10, cy - 8),
            (cx - 13, cy - 3),
            (cx - 14, cy + 5),
            (cx - 12 + int(sway), cy + 14),
            (cx - 8 + int(sway), cy + 22),
            (cx - 4 + int(sway), cy + 26),
            (cx + 4 + int(sway * 0.5), cy + 26),
            (cx + 8 + int(sway * 0.5), cy + 22),
            (cx + 12, cy + 14),
            (cx + 14, cy + 5),
            (cx + 13, cy - 3),
            (cx + 10, cy - 8),
            (cx + 5, cy - 10),
            (cx - 5, cy - 10),
        ]
        _NS_vyraeth._poly(surface, _NS_vyraeth.PALETTE["shadow_deep"],
              [(px + 2, py + 3) for px, py in body_shape])
        _NS_vyraeth._poly(surface, _NS_vyraeth.PALETTE["wraith_darkest"], body_shape)
        _NS_vyraeth._poly(surface, _NS_vyraeth.PALETTE["wraith_dark"], [
            (cx - 9, cy - 7), (cx - 12, cy - 2),
            (cx - 13, cy + 4),
            (cx - 11 + int(sway * 0.7), cy + 13),
            (cx - 7 + int(sway * 0.7), cy + 21),
            (cx - 3 + int(sway * 0.5), cy + 25),
            (cx + 3 + int(sway * 0.3), cy + 25),
            (cx + 7 + int(sway * 0.3), cy + 21),
            (cx + 11, cy + 13),
            (cx + 13, cy + 4), (cx + 12, cy - 2), (cx + 9, cy - 7),
            (cx + 4, cy - 9), (cx - 4, cy - 9),
        ])
        _NS_vyraeth._poly(surface, _NS_vyraeth.PALETTE["wraith_mid"], [
            (cx - 7, cy - 5), (cx - 10, cy - 1),
            (cx - 10, cy + 4), (cx - 8, cy + 12),
            (cx - 4, cy + 18), (cx + 4, cy + 18),
            (cx + 8, cy + 12), (cx + 10, cy + 4),
            (cx + 10, cy - 1), (cx + 7, cy - 5),
            (cx + 3, cy - 7), (cx - 3, cy - 7),
        ])
        # Body glow on chest (heart of shadow)
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for r in range(6, 0, -1):
            alpha = _NS_vyraeth._alpha(200 * (6 - r) / 6 * pulse)
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_dark"], alpha),
                                  (cx, cy - 2), r)
        _NS_vyraeth._aacircle(surface, _NS_vyraeth.PALETTE["spectral_mid"], (cx, cy - 2), 2)
        _NS_vyraeth._aacircle(surface, _NS_vyraeth.PALETTE["spectral_light"], (cx, cy - 2), 1)
        pygame.draw.rect(surface, _NS_vyraeth.PALETTE["spectral_shine"], (cx, cy - 2, 1, 1))
        # Body edge highlights (spectral wisps)
        for i, (ex, ey) in enumerate([(-13, 0), (13, 0), (-10, 8), (10, 8)]):
            alpha = _NS_vyraeth._alpha(180 * pulse)
            pygame.draw.rect(surface, (*_NS_vyraeth.PALETTE["spectral_dark"], alpha),
                             (cx + ex, cy + ey, 1, 2))
            pygame.draw.rect(surface, (*_NS_vyraeth.PALETTE["spectral_mid"], alpha),
                             (cx + ex, cy + ey, 1, 1))
        # Wispy bottom fade (dissolving edges)
        for i in range(5):
            wisp_t = (phase * 0.6 + i * 0.2) % 1.0
            wx = cx - 6 + i * 3 + int(sway)
            wy = cy + 24 + int(wisp_t * 6)
            alpha = _NS_vyraeth._alpha(160 * (1 - wisp_t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_vyraeth.PALETTE["wraith_mid"], alpha),
                                 (wx, wy, 2, 2))
                pygame.draw.rect(surface, (*_NS_vyraeth.PALETTE["spectral_mid"], alpha),
                                 (wx, wy, 1, 1))
    def _draw_head(surface, cx, cy, facing, phase):
        """Hooded head with glowing eyes."""
        # Head shape (skull-ish, small)
        head_shape = [
            (cx - 7, cy + 5),
            (cx - 8, cy + 1),
            (cx - 7, cy - 4),
            (cx - 3, cy - 8),
            (cx + 3, cy - 8),
            (cx + 7, cy - 4),
            (cx + 8, cy + 1),
            (cx + 7, cy + 5),
            (cx + 3, cy + 7),
            (cx - 3, cy + 7),
        ]
        _NS_vyraeth._poly(surface, _NS_vyraeth.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in head_shape])
        _NS_vyraeth._poly(surface, _NS_vyraeth.PALETTE["wraith_darkest"], head_shape)
        _NS_vyraeth._poly(surface, _NS_vyraeth.PALETTE["wraith_dark"], [
            (cx - 6, cy + 4), (cx - 7, cy),
            (cx - 6, cy - 3), (cx - 2, cy - 7),
            (cx + 2, cy - 7), (cx + 6, cy - 3),
            (cx + 7, cy), (cx + 6, cy + 4),
            (cx + 2, cy + 6), (cx - 2, cy + 6),
        ])
        _NS_vyraeth._poly(surface, _NS_vyraeth.PALETTE["wraith_mid"], [
            (cx - 4, cy + 2), (cx - 5, cy - 1),
            (cx - 4, cy - 4), (cx - 1, cy - 6),
            (cx + 1, cy - 6), (cx + 4, cy - 4),
            (cx + 5, cy - 1), (cx + 4, cy + 2),
        ])
        # Dark cavity (face shadow)
        _NS_vyraeth._poly(surface, _NS_vyraeth.PALETTE["shadow"], [
            (cx - 4, cy - 2), (cx - 5, cy + 1),
            (cx - 3, cy + 4), (cx + 3, cy + 4),
            (cx + 5, cy + 1), (cx + 4, cy - 2),
        ])
        # GLOWING EYES (bright violet)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_x in (cx - 2, cx + 2):
            # Big glow
            for r in range(5, 0, -1):
                alpha = _NS_vyraeth._alpha(120 * (5 - r) / 5 * pulse)
                _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_mid"], alpha),
                                      (eye_x, cy + 1), r)
            pygame.draw.rect(surface, _NS_vyraeth.PALETTE["eye_dark"],
                             (eye_x - 1, cy, 2, 2))
            pygame.draw.rect(surface, _NS_vyraeth.PALETTE["eye_mid"],
                             (eye_x - 1, cy + 1, 2, 1))
            pygame.draw.rect(surface, _NS_vyraeth.PALETTE["eye_light"],
                             (eye_x, cy + 1, 1, 1))
            pygame.draw.rect(surface, _NS_vyraeth.PALETTE["eye_glow"],
                             (eye_x, cy + 1, 1, 1))
        # Cheek/jaw wisps drifting down
        for side in (-1, 1):
            alpha = _NS_vyraeth._alpha(150 * pulse)
            pygame.draw.line(surface, (*_NS_vyraeth.PALETTE["spectral_dark"], alpha),
                             (cx + side * 3, cy + 5),
                             (cx + side * 4, cy + 8), 1)
    def _draw_scythe_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Arm holding curved scythe/blade."""
        # Arm rest position and swing
        if action == "attack":
            # Swing arc
            if attack_progress < 0.3:
                # Wind up (behind)
                t = attack_progress / 0.3
                arm_angle = math.pi * 0.8 - t * 0.3  # behind head
                arm_extend = 8 + t * 2
            elif attack_progress < 0.6:
                # Swing forward (fast)
                t = (attack_progress - 0.3) / 0.3
                arm_angle = math.pi * 0.5 - t * math.pi * 1.0  # arc from up to down-forward
                arm_extend = 10 + t * 6
            else:
                # Recovery
                t = (attack_progress - 0.6) / 0.4
                arm_angle = -math.pi * 0.5 + t * math.pi * 0.5
                arm_extend = 16 - t * 8
        else:
            # Idle: blade held forward-down at side
            wave = math.sin(phase * 0.6) * 0.05
            arm_angle = -math.pi * 0.15 + wave
            arm_extend = 12
        # Shoulder position
        shoulder_x = cx + facing * 6
        shoulder_y = cy - 3
        # Hand position based on angle
        hand_x = shoulder_x + int(math.cos(arm_angle) * arm_extend) * facing
        hand_y = shoulder_y - int(math.sin(arm_angle) * arm_extend)
        # Draw arm (wispy tendril-like)
        _NS_vyraeth._draw_wispy_arm(surface, shoulder_x, shoulder_y, hand_x, hand_y, phase)
        # Draw scythe at hand
        _NS_vyraeth._draw_scythe(surface, hand_x, hand_y, facing, phase, arm_angle,
                                 action, attack_progress)
    def _draw_wispy_arm(surface, x1, y1, x2, y2, phase):
        """Ghostly wispy arm."""
        # 3-segment wispy arm
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2
        _NS_vyraeth._aaline(surface, _NS_vyraeth.PALETTE["shadow_deep"],
                (x1 + 1, y1 + 1), (mid_x + 1, mid_y + 1), 5)
        _NS_vyraeth._aaline(surface, _NS_vyraeth.PALETTE["wraith_darkest"],
                (x1, y1), (mid_x, mid_y), 4)
        _NS_vyraeth._aaline(surface, _NS_vyraeth.PALETTE["wraith_dark"],
                (x1, y1), (mid_x, mid_y), 3)
        _NS_vyraeth._aaline(surface, _NS_vyraeth.PALETTE["wraith_mid"],
                (x1, y1), (mid_x, mid_y), 1)
        _NS_vyraeth._aaline(surface, _NS_vyraeth.PALETTE["shadow_deep"],
                (mid_x + 1, mid_y + 1), (x2 + 1, y2 + 1), 4)
        _NS_vyraeth._aaline(surface, _NS_vyraeth.PALETTE["wraith_darkest"],
                (mid_x, mid_y), (x2, y2), 3)
        _NS_vyraeth._aaline(surface, _NS_vyraeth.PALETTE["wraith_dark"],
                (mid_x, mid_y), (x2, y2), 2)
        _NS_vyraeth._aaline(surface, _NS_vyraeth.PALETTE["wraith_mid"],
                (mid_x, mid_y), (x2, y2), 1)
    def _draw_scythe(surface, hand_x, hand_y, facing, phase, arm_angle,
                     action, attack_progress):
        """Curved spectral scythe blade."""
        # Handle direction from hand along arm angle extended
        handle_end_angle = arm_angle
        handle_len = 18
        # Handle end (tip of pole)
        handle_tip_x = hand_x + int(math.cos(handle_end_angle) * handle_len) * facing
        handle_tip_y = hand_y - int(math.sin(handle_end_angle) * handle_len)
        # Handle (dark bone/wood)
        pygame.draw.line(surface, _NS_vyraeth.PALETTE["shadow_deep"],
                         (hand_x + 1, hand_y + 1), (handle_tip_x + 1, handle_tip_y + 1), 4)
        pygame.draw.line(surface, _NS_vyraeth.PALETTE["bone_dark"],
                         (hand_x, hand_y), (handle_tip_x, handle_tip_y), 3)
        pygame.draw.line(surface, _NS_vyraeth.PALETTE["bone_mid"],
                         (hand_x, hand_y), (handle_tip_x, handle_tip_y), 2)
        pygame.draw.line(surface, _NS_vyraeth.PALETTE["bone_light"],
                         (hand_x, hand_y), (handle_tip_x, handle_tip_y), 1)
        # BLADE - curved crescent scythe blade at handle tip
        # Blade curves perpendicular to handle
        blade_perp_angle = handle_end_angle + math.pi / 2
        # Blade base near tip
        # Blade tip point (end of curve)
        blade_len = 24
        blade_curve = 12
        # Simple crescent: 3 points defining the arc
        # Point A: back of blade
        back_x = handle_tip_x + int(math.cos(blade_perp_angle) * 4) * facing
        back_y = handle_tip_y - int(math.sin(blade_perp_angle) * 4)
        # Point B: outer arc middle
        mid_angle = blade_perp_angle + 0.6
        outer_x = handle_tip_x + int(math.cos(mid_angle) * blade_len * 0.6) * facing
        outer_y = handle_tip_y - int(math.sin(mid_angle) * blade_len * 0.6)
        # Point C: sharp tip
        tip_angle = blade_perp_angle + 1.2
        tip_x = handle_tip_x + int(math.cos(tip_angle) * blade_len) * facing
        tip_y = handle_tip_y - int(math.sin(tip_angle) * blade_len)
        # Blade polygon (crescent shape)
        blade_pts = [
            (handle_tip_x, handle_tip_y),
            (back_x, back_y),
            (outer_x, outer_y),
            (tip_x, tip_y),
        ]
        # Shadow
        _NS_vyraeth._poly(surface, _NS_vyraeth.PALETTE["shadow_deep"],
                          [(px + 2, py + 2) for px, py in blade_pts])
        _NS_vyraeth._poly(surface, _NS_vyraeth.PALETTE["blade_darkest"], blade_pts)
        _NS_vyraeth._poly(surface, _NS_vyraeth.PALETTE["blade_dark"], [
            (handle_tip_x, handle_tip_y),
            ((back_x + handle_tip_x) // 2, (back_y + handle_tip_y) // 2),
            (outer_x, outer_y),
            (tip_x, tip_y),
        ])
        _NS_vyraeth._poly(surface, _NS_vyraeth.PALETTE["blade_mid"], [
            (handle_tip_x, handle_tip_y),
            (outer_x, outer_y),
            (tip_x, tip_y),
        ])
        # Sharp edge highlight (bright line from base to tip along outer arc)
        _NS_vyraeth._aaline(surface, _NS_vyraeth.PALETTE["blade_light"],
                (outer_x, outer_y), (tip_x, tip_y), 2)
        _NS_vyraeth._aaline(surface, _NS_vyraeth.PALETTE["blade_shine"],
                (outer_x, outer_y), (tip_x, tip_y), 1)
        # Spectral glow along blade edge
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for i in range(6):
            t = i / 5
            glow_x = int(handle_tip_x + (tip_x - handle_tip_x) * t)
            glow_y = int(handle_tip_y + (tip_y - handle_tip_y) * t)
            # Offset toward outer side
            offset_x = int(math.cos(mid_angle) * 2 * (1 - t)) * facing
            offset_y = -int(math.sin(mid_angle) * 2 * (1 - t))
            gx = glow_x + offset_x
            gy = glow_y + offset_y
            for r in range(3, 0, -1):
                alpha = _NS_vyraeth._alpha(150 * pulse * (3 - r) / 3)
                _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_mid"], alpha),
                                      (gx, gy), r)
            pygame.draw.rect(surface, _NS_vyraeth.PALETTE["spectral_shine"], (gx, gy, 1, 1))
        # Sharp tip glow
        for r in range(5, 0, -1):
            alpha = _NS_vyraeth._alpha(180 * pulse * (5 - r) / 5)
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_light"], alpha),
                                  (tip_x, tip_y), r)
        pygame.draw.rect(surface, _NS_vyraeth.PALETTE["spectral_shine"], (tip_x, tip_y, 1, 1))
        # Handle grip (wrap)
        pygame.draw.rect(surface, _NS_vyraeth.PALETTE["blade_dark"],
                         (hand_x - 2, hand_y - 2, 4, 4))
    def _draw_scythe_swing(surface, boss, x, y, progress):
        """Bright spectral arc trail during swing."""
        if progress < 0.3 or progress > 0.7:
            return
        facing = boss.direction
        t = (progress - 0.3) / 0.4
        # Swing arc center at shoulder
        cx = x + facing * 6
        cy = y - 3
        start_angle = math.pi * 0.5
        end_angle = -math.pi * 0.5
        current_angle = start_angle + (end_angle - start_angle) * t
        radius = 30
        # Trail arc (many segments)
        num_segs = 12
        for seg in range(num_segs):
            seg_t = seg / num_segs
            seg_angle = start_angle + (current_angle - start_angle) * seg_t
            seg_alpha = _NS_vyraeth._alpha(230 * (1 - seg_t) * (1 - abs(t - 0.5) * 0.3))
            r = int(radius - seg * 0.5)
            sx = cx + int(math.cos(seg_angle) * r) * facing
            sy = cy - int(math.sin(seg_angle) * r)
            size = int(6 - seg * 0.3)
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_dark"], seg_alpha),
                                  (sx, sy), size)
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_mid"], seg_alpha),
                                  (sx, sy), max(1, size - 2))
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_light"], seg_alpha),
                                  (sx, sy), max(1, size - 4))
        # Bright leading edge
        lead_x = cx + int(math.cos(current_angle) * radius) * facing
        lead_y = cy - int(math.sin(current_angle) * radius)
        for r in range(9, 0, -1):
            alpha = _NS_vyraeth._alpha(150 * (9 - r) / 9)
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_light"], alpha),
                                  (lead_x, lead_y), r)
        _NS_vyraeth._aacircle(surface, _NS_vyraeth.PALETTE["spectral_hot"], (lead_x, lead_y), 3)
        _NS_vyraeth._aacircle(surface, _NS_vyraeth.PALETTE["spectral_shine"], (lead_x, lead_y), 2)
        pygame.draw.rect(surface, _NS_vyraeth.PALETTE["white"], (lead_x, lead_y, 1, 1))
        # Sparkles along arc
        for i in range(8):
            spark_angle = start_angle + (current_angle - start_angle) * (i / 8)
            spark_r = radius + int(math.sin(progress * 10 + i) * 4)
            spx = cx + int(math.cos(spark_angle) * spark_r) * facing
            spy = cy - int(math.sin(spark_angle) * spark_r)
            pygame.draw.rect(surface, _NS_vyraeth.PALETTE["spectral_hot"], (spx, spy, 1, 1))
    # ============================================================
    # SKILL Q - PHANTOM DAGGER
    # ============================================================
    def _draw_phantomdagger_skill(surface, boss, x, y, timer, phase):
        """Spectral dagger thrown."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vyraeth._target_position(boss, x, y)
        if progress < 0.2:
            # Charge in hand
            t = progress / 0.2
            hand_x = x + facing * 18
            hand_y = y - 2
            cr = int(4 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_vyraeth._alpha(220 * (cr + 4 - r) / (cr + 4))
                _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_darkest"], alpha),
                                      (hand_x, hand_y), r)
            _NS_vyraeth._aacircle(surface, _NS_vyraeth.PALETTE["spectral_mid"], (hand_x, hand_y), cr - 2)
            _NS_vyraeth._aacircle(surface, _NS_vyraeth.PALETTE["spectral_light"], (hand_x, hand_y), max(1, cr - 4))
            _NS_vyraeth._aacircle(surface, _NS_vyraeth.PALETTE["spectral_shine"], (hand_x, hand_y), max(1, cr - 6))
            return
        # Flight
        t = (progress - 0.2) / 0.8
        t = min(1.0, t)
        start_x = x + facing * 22
        start_y = y - 2
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        angle = math.atan2(ty - start_y, tx - start_x)
        # Trail (spectral fragments)
        for i in range(10):
            trail_t = max(0.0, t - i * 0.04)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_vyraeth._alpha(240 - i * 22)
            size = max(1, 8 - i)
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_darkest"], alpha),
                                  (px, py), size)
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_dark"], alpha),
                                  (px, py), max(1, size - 1))
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_mid"], alpha),
                                  (px, py), max(1, size - 2))
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_light"], alpha),
                                  (px, py), max(1, size - 3))
            # Trailing wisps (dagger fragments)
            if i < 4:
                for s in range(2):
                    wisp_x = px + int(math.sin(t * 8 + i + s) * (size + 2))
                    wisp_y = py + int(math.cos(t * 8 + i + s) * (size + 2))
                    pygame.draw.rect(surface, (*_NS_vyraeth.PALETTE["spectral_hot"], alpha),
                                     (wisp_x, wisp_y, 1, 1))
        # Draw dagger shape at head
        dag_len = 10
        tail_x = bx - int(math.cos(angle) * dag_len)
        tail_y = by - int(math.sin(angle) * dag_len)
        # Blade
        pygame.draw.line(surface, _NS_vyraeth.PALETTE["blade_dark"], (tail_x, tail_y), (bx, by), 3)
        pygame.draw.line(surface, _NS_vyraeth.PALETTE["blade_light"], (tail_x, tail_y), (bx, by), 2)
        pygame.draw.line(surface, _NS_vyraeth.PALETTE["spectral_shine"], (tail_x, tail_y), (bx, by), 1)
        # Bright tip
        for r in range(6, 0, -1):
            alpha = _NS_vyraeth._alpha(150 * (6 - r) / 6)
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_light"], alpha), (bx, by), r)
        _NS_vyraeth._aacircle(surface, _NS_vyraeth.PALETTE["spectral_shine"], (bx, by), 2)
        pygame.draw.rect(surface, _NS_vyraeth.PALETTE["white"], (bx, by, 1, 1))
        # Impact
        if t > 0.9:
            st = (t - 0.9) / 0.1
            radius = int(8 + st * 20)
            alpha = _NS_vyraeth._alpha(240 * (1 - st))
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_dark"], alpha),
                                  (tx, ty), radius, 3)
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_mid"], alpha),
                                  (tx, ty), max(1, radius - 4), 2)
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_light"], alpha),
                                  (tx, ty), max(1, radius - 8), 1)
            for i in range(10):
                a_s = i * math.pi / 5
                ex = tx + int(math.cos(a_s) * radius)
                ey = ty + int(math.sin(a_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_vyraeth.PALETTE["spectral_hot"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # SKILL W - SOULREND
    # ============================================================
    def _draw_soulrend_ground(surface, boss, x, y, timer, phase):
        """AoE ground purple."""
        duration = 80
        progress = 1 - timer / duration
        r = int(55 * min(1.0, progress * 2))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_vyraeth.PALETTE["spectral_darkest"], 200),
                                (x - r, y + 46 - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_vyraeth.PALETTE["spectral_dark"], 180),
                                (x - r + 3, y + 46 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_vyraeth.PALETTE["wraith_mid"], 150),
                                (x - r + 8, y + 46 - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
    def _draw_soulrend_foreground(surface, boss, x, y, timer, phase):
        """Wraith figures rising from ground."""
        duration = 80
        progress = 1 - timer / duration
        # 4 wraith figures around boss
        for i in range(4):
            angle = i * math.pi / 2 + math.pi / 4
            radius = 40
            fx = x + int(math.cos(angle) * radius)
            fy = y + 46 + int(math.sin(angle) * radius * 0.4)
            rise = min(1.0, progress * 2)
            _NS_vyraeth._draw_wraith_figure(surface, fx, fy, phase + i, rise)
        # Central column glow
        for r in range(30, 0, -3):
            alpha = _NS_vyraeth._alpha(80 * (30 - r) / 30 * min(1.0, progress * 2))
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_mid"], alpha),
                                  (x, y + 20), r)
    def _draw_wraith_figure(surface, cx, cy, phase, rise):
        """Small wraith figure standing."""
        height = int(20 * rise)
        if height < 3:
            return
        alpha = _NS_vyraeth._alpha(220 * rise)
        # Body triangle (tapered up)
        pts = [
            (cx - 5, cy),
            (cx - 3, cy - height + 3),
            (cx - 2, cy - height),
            (cx + 2, cy - height),
            (cx + 3, cy - height + 3),
            (cx + 5, cy),
        ]
        _NS_vyraeth._poly(surface, (*_NS_vyraeth.PALETTE["wraith_darkest"], alpha), pts)
        _NS_vyraeth._poly(surface, (*_NS_vyraeth.PALETTE["wraith_dark"], alpha), [
            (cx - 4, cy - 1), (cx - 2, cy - height + 3),
            (cx + 2, cy - height + 3), (cx + 4, cy - 1),
        ])
        _NS_vyraeth._poly(surface, (*_NS_vyraeth.PALETTE["wraith_mid"], alpha), [
            (cx - 2, cy - height // 2),
            (cx + 2, cy - height // 2),
            (cx + 1, cy - 2),
            (cx - 1, cy - 2),
        ])
        # Glowing eyes at top
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        eye_alpha = _NS_vyraeth._alpha(255 * pulse * rise)
        for ex in (cx - 1, cx + 1):
            pygame.draw.rect(surface, (*_NS_vyraeth.PALETTE["spectral_light"], eye_alpha),
                             (ex, cy - height + 2, 1, 1))
            pygame.draw.rect(surface, (*_NS_vyraeth.PALETTE["spectral_shine"], eye_alpha),
                             (ex, cy - height + 2, 1, 1))
    # ============================================================
    # SKILL E - DISPERSION / VOIDSHIFT
    # ============================================================
    def _draw_dispersion_foreground(surface, boss, x, y, timer, phase):
        """Spectral fragments streaking forward."""
        facing = boss.direction
        duration = 70
        progress = 1 - timer / duration
        # Multiple streaks in a line forward
        for i in range(20):
            t = ((phase * 1.5 + i * 0.08) % 1.0)
            forward_dist = int(t * 150)
            spread = int(math.sin(phase * 2 + i) * 15)
            fx = x + facing * forward_dist
            fy = y + spread
            alpha = _NS_vyraeth._alpha(240 * (1 - t))
            size = max(1, int(4 * (1 - t)))
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_dark"], alpha),
                                  (fx, fy), size)
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_mid"], alpha),
                                  (fx, fy), max(1, size - 1))
            pygame.draw.rect(surface, (*_NS_vyraeth.PALETTE["spectral_hot"], alpha),
                             (fx, fy, 1, 1))
        # Speed streak lines
        for i in range(5):
            line_y = y - 10 + i * 6
            for j in range(3):
                sx = x + facing * (20 + j * 30)
                pygame.draw.line(surface, _NS_vyraeth.PALETTE["spectral_light"],
                                 (sx, line_y), (sx + facing * 15, line_y), 1)
    # ============================================================
    # SKILL R - HAUNTING
    # ============================================================
    def _draw_haunt_ground(surface, boss, x, y, timer, phase):
        """Ghost portal at target."""
        tx, ty = _NS_vyraeth._target_position(boss, x, y)
        duration = 100
        progress = 1 - timer / duration
        r = int(35 * min(1.0, progress * 2))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_vyraeth.PALETTE["shadow"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_vyraeth.PALETTE["spectral_darkest"], 240),
                                (tx - r + 2, ty - r // 3 + 1,
                                 r * 2 - 4, r * 2 // 3 - 2))
    def _draw_haunt_foreground(surface, boss, x, y, timer, phase):
        """Ghostly trail from boss to target + wraith mask."""
        facing = boss.direction
        tx, ty = _NS_vyraeth._target_position(boss, x, y)
        duration = 100
        progress = 1 - timer / duration
        # 5 ghost afterimages along path
        for i in range(6):
            t = i / 5
            gx = int(x + (tx - x) * t)
            gy = int(y + (ty - y) * t)
            alpha = _NS_vyraeth._alpha(200 * (1 - t * 0.7) * min(1.0, progress * 2))
            _NS_vyraeth._draw_wraith_afterimage(surface, gx, gy, facing, phase, alpha)
        # Wraith mask hovering at target
        if progress > 0.3:
            _NS_vyraeth._draw_wraith_mask(surface, tx, ty - 30, phase, progress)
        # Impact at target
        if progress > 0.6:
            burst_r = int((progress - 0.6) * 60)
            alpha = _NS_vyraeth._alpha(200 * (1 - (progress - 0.6) / 0.4))
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_dark"], alpha),
                                  (tx, ty), burst_r, 3)
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_mid"], alpha),
                                  (tx, ty), max(1, burst_r - 6), 2)
            _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_light"], alpha),
                                  (tx, ty), max(1, burst_r - 12), 1)
            for i in range(12):
                a_s = i * math.pi / 6
                ex = tx + int(math.cos(a_s) * burst_r)
                ey = ty + int(math.sin(a_s) * burst_r)
                pygame.draw.rect(surface, (*_NS_vyraeth.PALETTE["spectral_hot"], alpha),
                                 (ex, ey, 2, 2))
    def _draw_wraith_afterimage(surface, cx, cy, facing, phase, alpha):
        """Small wraith silhouette."""
        pts = [
            (cx - 6, cy + 10),
            (cx - 8, cy),
            (cx - 5, cy - 8),
            (cx + 5, cy - 8),
            (cx + 8, cy),
            (cx + 6, cy + 10),
        ]
        _NS_vyraeth._poly(surface, (*_NS_vyraeth.PALETTE["wraith_dark"], alpha), pts)
        _NS_vyraeth._poly(surface, (*_NS_vyraeth.PALETTE["wraith_mid"], alpha), [
            (cx - 4, cy + 8), (cx - 6, cy),
            (cx - 3, cy - 6), (cx + 3, cy - 6),
            (cx + 6, cy), (cx + 4, cy + 8),
        ])
        # Glowing eyes
        for ex in (cx - 2, cx + 2):
            pygame.draw.rect(surface, (*_NS_vyraeth.PALETTE["spectral_light"], alpha),
                             (ex, cy - 4, 1, 1))
    def _draw_wraith_mask(surface, cx, cy, phase, progress):
        """Big scary wraith face hovering."""
        alpha = _NS_vyraeth._alpha(230 * min(1.0, (progress - 0.3) * 3))
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Hood shape
        pts = [
            (cx - 14, cy + 10),
            (cx - 16, cy + 2),
            (cx - 12, cy - 10),
            (cx - 5, cy - 16),
            (cx + 5, cy - 16),
            (cx + 12, cy - 10),
            (cx + 16, cy + 2),
            (cx + 14, cy + 10),
            (cx + 8, cy + 12),
            (cx - 8, cy + 12),
        ]
        _NS_vyraeth._poly(surface, (*_NS_vyraeth.PALETTE["shadow_deep"], alpha),
                          [(p[0] + 2, p[1] + 2) for p in pts])
        _NS_vyraeth._poly(surface, (*_NS_vyraeth.PALETTE["wraith_darkest"], alpha), pts)
        _NS_vyraeth._poly(surface, (*_NS_vyraeth.PALETTE["wraith_dark"], alpha), [
            (cx - 12, cy + 9), (cx - 14, cy + 1),
            (cx - 10, cy - 9), (cx - 4, cy - 14),
            (cx + 4, cy - 14), (cx + 10, cy - 9),
            (cx + 14, cy + 1), (cx + 12, cy + 9),
            (cx + 6, cy + 11), (cx - 6, cy + 11),
        ])
        # Dark inner void
        _NS_vyraeth._poly(surface, (*_NS_vyraeth.PALETTE["shadow"], alpha), [
            (cx - 8, cy - 4), (cx - 9, cy + 3),
            (cx - 6, cy + 8), (cx + 6, cy + 8),
            (cx + 9, cy + 3), (cx + 8, cy - 4),
        ])
        # Big scary eyes
        for eye_x in (cx - 4, cx + 4):
            eye_alpha = _NS_vyraeth._alpha(255 * pulse * min(1.0, (progress - 0.3) * 3))
            for r in range(6, 0, -1):
                a = _NS_vyraeth._alpha(150 * pulse * (6 - r) / 6)
                _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["spectral_mid"], a),
                                      (eye_x, cy + 1), r)
            pygame.draw.rect(surface, (*_NS_vyraeth.PALETTE["spectral_light"], eye_alpha),
                             (eye_x - 1, cy, 3, 2))
            pygame.draw.rect(surface, (*_NS_vyraeth.PALETTE["spectral_shine"], eye_alpha),
                             (eye_x, cy + 1, 1, 1))
    # ============================================================
    # SMOKE TAIL (floating body dissipating)
    # ============================================================
    def _draw_smoke_tail(surface, cx, cy, phase, intense=False, moving=False, facing=1):
        strength = 1.3 if intense else 1.0
        smoke = pygame.Surface((100, 60), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(22, 3, -2):
            alpha = _NS_vyraeth._alpha((22 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    smoke, (*_NS_vyraeth.PALETTE["smoke_darkest"], alpha),
                    (50 - radius, 30 - radius // 2, radius * 2, max(3, radius)))
        for radius in range(15, 3, -2):
            alpha = _NS_vyraeth._alpha((15 - radius) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    smoke, (*_NS_vyraeth.PALETTE["smoke_dark"], alpha),
                    (50 - radius, 30 - radius // 2, radius * 2, max(2, radius)))
        surface.blit(smoke, (cx - 50, cy - 15))
        # Rising spectral particles
        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            px = cx - 18 + i * 5 + int(math.sin(phase + i) * 3)
            py = cy + 12 - int(t * 22)
            alpha = _NS_vyraeth._alpha(210 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_vyraeth.PALETTE["spectral_mid"], alpha),
                                 (px, py, 1, 1))
                pygame.draw.rect(surface, (*_NS_vyraeth.PALETTE["spectral_light"], alpha),
                                 (px, py, 1, 1))
        if moving:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + 8 + int(math.sin(phase + i) * 2)
                alpha = _NS_vyraeth._alpha(160 - i * 30)
                if alpha <= 0:
                    continue
                _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["smoke_dark"], alpha),
                                      (sx, sy), max(2, 6 - i))
                _NS_vyraeth._aacircle(surface, (*_NS_vyraeth.PALETTE["smoke_mid"], alpha),
                                      (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_vyraeth.PALETTE["spectral_light"], alpha),
                                 (sx, sy - 1, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 12)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius, 120 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (10, 5, 20, 150), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (50, 20, 80, 90), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_spectral_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_vyraeth._alpha((100 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_vyraeth._aacircle(aura, (*_NS_vyraeth.PALETTE["smoke_darkest"], alpha),
                                      (120, 100), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_vyraeth._alpha((65 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_vyraeth._aacircle(aura, (*_NS_vyraeth.PALETTE["spectral_darkest"], alpha),
                                      (120, 100), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_vyraeth._alpha((35 - radius) * 1.8 * pulse)
            if alpha > 0:
                _NS_vyraeth._aacircle(aura, (*_NS_vyraeth.PALETTE["spectral_dark"], alpha),
                                      (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))
        # Floating violet embers
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 45 + int(math.sin(phase + i) * 14)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_vyraeth.PALETTE["spectral_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_vyraeth.PALETTE["spectral_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_vyraeth.PALETTE["wraith_darkest"], 200),
                            (5, 20, 170, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_vyraeth.PALETTE["spectral_darkest"], 220),
                            (14, 22, 152, 24), 2)
        pygame.draw.ellipse(ring, (*_NS_vyraeth.PALETTE["spectral_dark"], 180),
                            (25, 24, 130, 20), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 34 + int(math.sin(angle) * 9)
            x2 = 90 + int(math.cos(angle) * 76)
            y2 = 34 + int(math.sin(angle) * 13)
            pygame.draw.line(ring, (*_NS_vyraeth.PALETTE["spectral_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_vyraeth.PALETTE["spectral_hot"],
                                       _NS_vyraeth._alpha(150 * pulse)),
                                (15, 12, 150, 42), 1)
        surface.blit(ring, (x - 90, y - 30))



# ====================================================================
# ZOROTHRAX (RUNE SOVEREIGN) - Mini Boss
# ====================================================================

class _NS_zorothrax:
    """Namespace zorothrax - Rune Sovereign boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (pale grey-blue muscular)
        "skin_darkest": (35, 30, 45),
        "skin_dark": (75, 70, 90),
        "skin_mid": (130, 125, 150),
        "skin_light": (185, 180, 200),
        "skin_shine": (225, 220, 240),
        # Beard (long grey-white)
        "beard_dark": (50, 50, 65),
        "beard_mid": (120, 120, 140),
        "beard_light": (200, 200, 215),
        "beard_shine": (240, 240, 250),
        # Rune blue (glowing tattoos, magic)
        "rune_darkest": (10, 20, 60),
        "rune_dark": (25, 60, 140),
        "rune_mid": (60, 120, 230),
        "rune_light": (130, 180, 255),
        "rune_hot": (200, 225, 255),
        "rune_shine": (240, 250, 255),
        # Robe (dark red/maroon)
        "robe_darkest": (30, 10, 15),
        "robe_dark": (75, 25, 35),
        "robe_mid": (130, 50, 60),
        "robe_light": (180, 90, 100),
        # Cloak dark (over shoulders)
        "cloak_darkest": (15, 10, 20),
        "cloak_dark": (35, 25, 45),
        "cloak_mid": (65, 50, 80),
        "cloak_light": (110, 90, 130),
        # Bracers / metal (dark iron with gold)
        "metal_dark": (25, 20, 30),
        "metal_mid": (70, 65, 80),
        "metal_light": (135, 130, 150),
        "gold_dark": (85, 60, 15),
        "gold_mid": (175, 135, 45),
        "gold_light": (240, 210, 115),
        # Eyes (glowing blue)
        "eye_socket": (5, 5, 15),
        "eye_dark": (20, 40, 100),
        "eye_mid": (100, 160, 240),
        "eye_light": (200, 220, 255),
        "eye_glow": (240, 245, 255),
        # Portal/void (dark purple with blue rim)
        "portal_darkest": (5, 5, 15),
        "portal_dark": (25, 15, 55),
        "portal_mid": (60, 40, 120),
        "portal_light": (110, 80, 200),
        # Smoke tail (floating)
        "smoke_darkest": (10, 8, 25),
        "smoke_dark": (30, 25, 60),
        "smoke_mid": (60, 55, 110),
        "smoke_light": (110, 105, 180),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_zorothrax._clamp(color)
        if _NS_zorothrax.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_zorothrax._clamp(color)
        if _NS_zorothrax.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_zorothrax._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_zorothrax(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_zorothrax._detect_moving(boss)
        _NS_zorothrax._update_attack_anim(boss)
        attacking = getattr(boss, "_zx_attack_active", False)
        # Ambient
        _NS_zorothrax._draw_arcane_aura(surface, x, y, pulse)
        _NS_zorothrax._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX
        if active_skill == "w":
            _NS_zorothrax._draw_prison_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zorothrax._draw_portal_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (floating)
        if attacking:
            _NS_zorothrax._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_zorothrax._draw_walk(surface, boss, x, y)
        else:
            _NS_zorothrax._draw_idle(surface, boss, x, y)
        # Foreground FX
        if active_skill == "q":
            _NS_zorothrax._draw_runebolt_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_zorothrax._draw_prison_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_zorothrax._draw_arcanewave_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zorothrax._draw_portal_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_zx_attack_active", False))
        if not active and timer <= 2:
            boss._zx_attack_active = True
            boss._zx_attack_frame = 0
            active = True
        if active:
            boss._zx_attack_frame = int(getattr(boss, "_zx_attack_frame", 0)) + 1
            if boss._zx_attack_frame >= cooldown:
                boss._zx_attack_active = False
                boss._zx_attack_frame = 0
                active = False
        boss._zx_attack_progress = (
            min(1.0, getattr(boss, "_zx_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_zx_last_x"):
            boss._zx_last_x = boss.x
            boss._zx_last_y = boss.y
            return False
        dx = abs(boss.x - boss._zx_last_x)
        dy = abs(boss.y - boss._zx_last_y)
        boss._zx_last_x = boss.x
        boss._zx_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        # Floating bob
        bob = int(math.sin(boss.pulse * 0.5) * 5)
        _NS_zorothrax._draw_shadow(surface, x, y + 50)
        _NS_zorothrax._draw_smoke_base(surface, x, y + 22 + bob, boss.pulse)
        _NS_zorothrax._draw_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")
    def _draw_walk(surface, boss, x, y):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.8) * 6)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_zorothrax._draw_shadow(surface, x + sway, y + 50)
        _NS_zorothrax._draw_smoke_base(surface, x + sway, y + 22 + bob, phase,
                                       moving=True, facing=boss.direction)
        _NS_zorothrax._draw_body(surface, x + sway, y + bob, boss.direction, phase, "walk")
    def _draw_attack(surface, boss, x, y):
        progress = getattr(boss, "_zx_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        bob = int(math.sin(boss.pulse * 0.5) * 3)
        # Cast: raise arm → thrust forward → recovery
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 2) * boss.direction
        elif progress < 0.55:
            t = (progress - 0.35) / 0.2
            lunge = int((-2 + t * 8)) * boss.direction
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(6 * (1 - t)) * boss.direction
        _NS_zorothrax._draw_shadow(surface, x + lunge, y + 50)
        _NS_zorothrax._draw_smoke_base(surface, x + lunge, y + 22 + bob, boss.pulse,
                                       intense=True)
        _NS_zorothrax._draw_body(surface, x + lunge, y + bob, boss.direction, boss.pulse,
                                 "attack", progress)
        _NS_zorothrax._draw_rune_projectile(surface, boss, x + lunge, y + bob, progress)
    # ============================================================
    # BODY - Muscular mage with beard
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0.0):
        # Cloak behind
        _NS_zorothrax._draw_cloak(surface, cx, cy, facing, phase)
        # Robe skirt
        _NS_zorothrax._draw_robe(surface, cx, cy, facing, phase)
        # Torso muscular
        _NS_zorothrax._draw_torso(surface, cx, cy, facing, phase)
        # Arms
        _NS_zorothrax._draw_arms(surface, cx, cy, facing, phase, action, attack_progress)
        # Head + beard
        _NS_zorothrax._draw_head(surface, cx, cy - 22, facing, phase)
        # Beard hangs down over torso
        _NS_zorothrax._draw_beard(surface, cx, cy - 14, facing, phase)
        # Floating rune orbs around body
        _NS_zorothrax._draw_orbiting_runes(surface, cx, cy, facing, phase)
    def _draw_cloak(surface, cx, cy, facing, phase):
        """Dark cloak behind shoulders."""
        sway = math.sin(phase * 0.5) * 2
        back = -facing
        cloak_shape = [
            (cx - 12, cy - 10),
            (cx - 15, cy - 5),
            (cx - 16 + int(back + sway), cy + 5),
            (cx - 14 + int(back * 2 + sway), cy + 15),
            (cx - 10 + int(back * 2 + sway), cy + 22),
            (cx + 10 + int(back + sway * 0.5), cy + 22),
            (cx + 14, cy + 15),
            (cx + 16, cy + 5),
            (cx + 15, cy - 5),
            (cx + 12, cy - 10),
        ]
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["shadow_deep"],
              [(px + 2, py + 3) for px, py in cloak_shape])
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["cloak_darkest"], cloak_shape)
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["cloak_dark"], [
            (cx - 11, cy - 9), (cx - 14, cy - 4),
            (cx - 15 + int(back + sway * 0.5), cy + 5),
            (cx - 13 + int(back + sway * 0.5), cy + 14),
            (cx - 9, cy + 21), (cx + 9, cy + 21),
            (cx + 13, cy + 14), (cx + 15, cy + 5),
            (cx + 14, cy - 4), (cx + 11, cy - 9),
        ])
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["cloak_mid"], [
            (cx - 10, cy - 8), (cx - 12, cy - 3),
            (cx - 12, cy + 3), (cx - 8, cy + 10),
            (cx + 8, cy + 10), (cx + 12, cy + 3),
            (cx + 12, cy - 3), (cx + 10, cy - 8),
        ])
        # Rune glow on cloak edges
        glow_pulse = math.sin(phase * 1.2) * 0.3 + 0.7
        for edge_x in (cx - 14, cx + 14):
            for i in range(3):
                y_off = i * 6 - 3
                alpha = _NS_zorothrax._alpha(160 * glow_pulse)
                pygame.draw.rect(surface, (*_NS_zorothrax.PALETTE["rune_dark"], alpha),
                                 (edge_x, cy + y_off, 1, 3))
                pygame.draw.rect(surface, (*_NS_zorothrax.PALETTE["rune_light"], alpha),
                                 (edge_x, cy + y_off + 1, 1, 1))
    def _draw_robe(surface, cx, cy, facing, phase):
        """Dark red robe skirt below waist."""
        sway = math.sin(phase * 0.5) * 2
        robe_shape = [
            (cx - 10, cy + 12),
            (cx - 12, cy + 20),
            (cx - 11 + int(sway), cy + 30),
            (cx - 8, cy + 34),
            (cx + 8, cy + 34),
            (cx + 11 + int(sway * 0.5), cy + 30),
            (cx + 12, cy + 20),
            (cx + 10, cy + 12),
        ]
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in robe_shape])
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["robe_darkest"], robe_shape)
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["robe_dark"], [
            (cx - 9, cy + 13), (cx - 11, cy + 20),
            (cx - 10 + int(sway * 0.5), cy + 29),
            (cx - 7, cy + 33), (cx + 7, cy + 33),
            (cx + 10 + int(sway * 0.3), cy + 29),
            (cx + 11, cy + 20), (cx + 9, cy + 13),
        ])
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["robe_mid"], [
            (cx - 7, cy + 14), (cx - 8, cy + 22),
            (cx - 6, cy + 30), (cx + 6, cy + 30),
            (cx + 8, cy + 22), (cx + 7, cy + 14),
        ])
        # Vertical highlight fold
        pygame.draw.line(surface, _NS_zorothrax.PALETTE["robe_light"],
                         (cx, cy + 15), (cx, cy + 32), 1)
        pygame.draw.line(surface, _NS_zorothrax.PALETTE["robe_mid"],
                         (cx - 4, cy + 15), (cx - 4, cy + 32), 1)
        pygame.draw.line(surface, _NS_zorothrax.PALETTE["robe_mid"],
                         (cx + 4, cy + 15), (cx + 4, cy + 32), 1)
        # GOLD BELT with rune buckle
        pygame.draw.rect(surface, _NS_zorothrax.PALETTE["gold_dark"],
                         (cx - 11, cy + 10, 22, 4))
        pygame.draw.rect(surface, _NS_zorothrax.PALETTE["gold_mid"],
                         (cx - 11, cy + 10, 22, 2))
        pygame.draw.rect(surface, _NS_zorothrax.PALETTE["gold_light"],
                         (cx - 11, cy + 10, 22, 1))
        # Buckle
        pygame.draw.rect(surface, _NS_zorothrax.PALETTE["gold_dark"],
                         (cx - 4, cy + 9, 8, 6))
        pygame.draw.rect(surface, _NS_zorothrax.PALETTE["gold_mid"],
                         (cx - 3, cy + 10, 6, 4))
        # Rune in center of buckle (glowing)
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for r in range(3, 0, -1):
            alpha = _NS_zorothrax._alpha(200 * (3 - r) / 3 * pulse)
            _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_mid"], alpha),
                                    (cx, cy + 12), r)
        pygame.draw.rect(surface, _NS_zorothrax.PALETTE["rune_shine"], (cx, cy + 12, 1, 1))
    def _draw_torso(surface, cx, cy, facing, phase):
        """Muscular bare chest (visible above beard/belt)."""
        # Torso shape
        torso_shape = [
            (cx - 12, cy - 8),
            (cx - 14, cy - 4),
            (cx - 13, cy + 4),
            (cx - 11, cy + 10),
            (cx + 11, cy + 10),
            (cx + 13, cy + 4),
            (cx + 14, cy - 4),
            (cx + 12, cy - 8),
            (cx + 6, cy - 12),
            (cx - 6, cy - 12),
        ]
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["shadow_deep"],
              [(px + 2, py + 3) for px, py in torso_shape])
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["skin_darkest"], torso_shape)
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["skin_dark"], [
            (cx - 11, cy - 7), (cx - 13, cy - 3),
            (cx - 12, cy + 3), (cx - 10, cy + 9),
            (cx + 10, cy + 9), (cx + 12, cy + 3),
            (cx + 13, cy - 3), (cx + 11, cy - 7),
            (cx + 5, cy - 11), (cx - 5, cy - 11),
        ])
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["skin_mid"], [
            (cx - 9, cy - 5), (cx - 11, cy - 2),
            (cx - 10, cy + 3), (cx - 7, cy + 8),
            (cx + 7, cy + 8), (cx + 10, cy + 3),
            (cx + 11, cy - 2), (cx + 9, cy - 5),
            (cx + 4, cy - 9), (cx - 4, cy - 9),
        ])
        # Pec definition
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["skin_light"], [
            (cx - 8, cy - 5), (cx - 2, cy - 7),
            (cx - 1, cy - 2), (cx - 6, cy),
        ])
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["skin_light"], [
            (cx + 2, cy - 7), (cx + 8, cy - 5),
            (cx + 6, cy), (cx + 1, cy - 2),
        ])
        # Center chest line
        pygame.draw.line(surface, _NS_zorothrax.PALETTE["skin_darkest"],
                         (cx, cy - 8), (cx, cy - 2), 1)
        # Abs
        for i, y_off in enumerate((2, 5, 8)):
            pygame.draw.line(surface, _NS_zorothrax.PALETTE["skin_darkest"],
                             (cx - 4 + i, cy + y_off),
                             (cx + 4 - i, cy + y_off), 1)
        # RUNE TATTOOS glowing on chest and arms
        glow_pulse = math.sin(phase * 1.2) * 0.3 + 0.7
        # Chest rune circles
        for i, (rx, ry, sz) in enumerate([
            (-6, -4, 2), (6, -4, 2),   # pecs
            (0, 4, 3),                  # center abs
            (-7, 6, 1), (7, 6, 1),      # side abs
        ]):
            alpha = _NS_zorothrax._alpha(220 * glow_pulse)
            _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_dark"], alpha),
                                    (cx + rx, cy + ry), sz + 1)
            _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_mid"], alpha),
                                    (cx + rx, cy + ry), sz)
            _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_light"], alpha),
                                    (cx + rx, cy + ry), max(1, sz - 1))
            pygame.draw.rect(surface, _NS_zorothrax.PALETTE["rune_shine"],
                             (cx + rx, cy + ry, 1, 1))
        # Small rune lines connecting
        for (x1, y1, x2, y2) in [(-6, -4, 0, 4), (6, -4, 0, 4)]:
            alpha = _NS_zorothrax._alpha(150 * glow_pulse)
            pygame.draw.line(surface, (*_NS_zorothrax.PALETTE["rune_mid"], alpha),
                             (cx + x1, cy + y1), (cx + x2, cy + y2), 1)
    def _draw_arms(surface, cx, cy, facing, phase, action, attack_progress):
        """Two muscular arms with bracers."""
        arm_sway = math.sin(phase * 0.5) * 1
        # Determine arm poses
        if action == "attack":
            # Front arm thrust, back arm slightly raised
            if attack_progress < 0.35:
                # Raising
                t = attack_progress / 0.35
                front_forward = int(t * 4) * facing
                front_raise = int(t * 3)
            elif attack_progress < 0.55:
                # Thrust
                t = (attack_progress - 0.35) / 0.2
                front_forward = int((4 + t * 10)) * facing
                front_raise = int(3 - t * 3)
            else:
                # Recovery
                t = (attack_progress - 0.55) / 0.45
                front_forward = int(14 * (1 - t)) * facing
                front_raise = 0
        else:
            front_forward = 0
            front_raise = int(arm_sway)
        # BACK arm (draw first, behind body)
        back_shoulder = (cx - facing * 10, cy - 6)
        back_elbow = (cx - facing * 12, cy + 2 + int(arm_sway))
        back_hand = (cx - facing * 10, cy + 12)
        # Draw back arm
        _NS_zorothrax._draw_arm_segment(surface, back_shoulder, back_elbow, 6, 0.75)
        _NS_zorothrax._draw_arm_segment(surface, back_elbow, back_hand, 5, 0.75)
        _NS_zorothrax._draw_bracer(surface, back_hand[0], back_hand[1] - 4, 0.75)
        _NS_zorothrax._draw_fist(surface, back_hand[0], back_hand[1] + 2, facing, phase, 0.75)
        # FRONT arm (over body)
        front_shoulder = (cx + facing * 10, cy - 6)
        # Compute forward extended position
        front_elbow = (cx + facing * (13 + front_forward // 2),
                       cy - 2 - front_raise + int(arm_sway))
        front_hand = (cx + facing * (16 + front_forward),
                      cy + front_raise * 2 - front_raise)
        # Simple hand at end when thrusting
        if action == "attack" and attack_progress >= 0.35:
            front_hand = (cx + facing * (18 + front_forward),
                          cy - 2 + int(arm_sway))
        _NS_zorothrax._draw_arm_segment(surface, front_shoulder, front_elbow, 6, 1.0)
        _NS_zorothrax._draw_arm_segment(surface, front_elbow, front_hand, 5, 1.0)
        _NS_zorothrax._draw_bracer(surface, front_hand[0] - facing * 2,
                                   front_hand[1] - 2, 1.0)
        _NS_zorothrax._draw_fist(surface, front_hand[0], front_hand[1] + 1,
                                 facing, phase, 1.0, casting=(action == "attack"))
    def _draw_arm_segment(surface, p1, p2, thickness, depth_shade=1.0):
        """Muscular arm with rune tattoos."""
        def shade(color):
            return tuple(int(c * depth_shade) for c in color)
        # Shadow
        _NS_zorothrax._aaline(surface, _NS_zorothrax.PALETTE["shadow_deep"],
                (p1[0] + 2, p1[1] + 2), (p2[0] + 2, p2[1] + 2), thickness + 1)
        # Base
        _NS_zorothrax._aaline(surface, shade(_NS_zorothrax.PALETTE["skin_darkest"]),
                p1, p2, thickness)
        _NS_zorothrax._aaline(surface, shade(_NS_zorothrax.PALETTE["skin_dark"]),
                p1, p2, max(1, thickness - 2))
        # Highlight
        _NS_zorothrax._aaline(surface, shade(_NS_zorothrax.PALETTE["skin_mid"]),
                (p1[0] - 1, p1[1] - 1), (p2[0] - 1, p2[1] - 1),
                max(1, thickness - 4))
        # Small rune tattoo on arm midpoint
        mid_x = (p1[0] + p2[0]) // 2
        mid_y = (p1[1] + p2[1]) // 2
        pygame.draw.rect(surface, shade(_NS_zorothrax.PALETTE["rune_mid"]),
                         (mid_x, mid_y, 1, 1))
        pygame.draw.rect(surface, shade(_NS_zorothrax.PALETTE["rune_light"]),
                         (mid_x, mid_y, 1, 1))
    def _draw_bracer(surface, cx, cy, depth_shade=1.0):
        """Metal bracer with gold trim."""
        def shade(color):
            return tuple(int(c * depth_shade) for c in color)
        # Base metal
        pygame.draw.rect(surface, shade(_NS_zorothrax.PALETTE["metal_dark"]),
                         (cx - 4, cy - 3, 8, 7))
        pygame.draw.rect(surface, shade(_NS_zorothrax.PALETTE["metal_mid"]),
                         (cx - 3, cy - 2, 6, 5))
        pygame.draw.rect(surface, shade(_NS_zorothrax.PALETTE["metal_light"]),
                         (cx - 3, cy - 2, 6, 1))
        # Gold trim
        pygame.draw.line(surface, shade(_NS_zorothrax.PALETTE["gold_dark"]),
                         (cx - 4, cy + 3), (cx + 4, cy + 3), 1)
        pygame.draw.line(surface, shade(_NS_zorothrax.PALETTE["gold_mid"]),
                         (cx - 4, cy - 3), (cx + 4, cy - 3), 1)
        # Rune on bracer center
        pygame.draw.rect(surface, shade(_NS_zorothrax.PALETTE["rune_mid"]),
                         (cx, cy, 1, 1))
    def _draw_fist(surface, cx, cy, facing, phase, depth_shade=1.0, casting=False):
        """Fist/hand with optional casting glow."""
        def shade(color):
            return tuple(int(c * depth_shade) for c in color)
        # Fist shape
        pygame.draw.rect(surface, shade(_NS_zorothrax.PALETTE["skin_darkest"]),
                         (cx - 3, cy - 2, 6, 5))
        pygame.draw.rect(surface, shade(_NS_zorothrax.PALETTE["skin_dark"]),
                         (cx - 2, cy - 1, 4, 4))
        pygame.draw.rect(surface, shade(_NS_zorothrax.PALETTE["skin_mid"]),
                         (cx - 2, cy - 1, 4, 1))
        # Casting glow in palm
        if casting:
            pulse = math.sin(phase * 3) * 0.3 + 0.7
            for r in range(6, 0, -1):
                alpha = _NS_zorothrax._alpha(200 * (6 - r) / 6 * pulse)
                _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_mid"], alpha),
                                        (cx + facing * 2, cy), r)
            _NS_zorothrax._aacircle(surface, _NS_zorothrax.PALETTE["rune_light"],
                                    (cx + facing * 2, cy), 2)
            pygame.draw.rect(surface, _NS_zorothrax.PALETTE["rune_shine"],
                             (cx + facing * 2, cy, 1, 1))
    def _draw_head(surface, cx, cy, facing, phase):
        """Bald head with rune tattoos, stern face."""
        # Head shape (bald, round-square)
        head_shape = [
            (cx - 7, cy + 6),
            (cx - 8, cy + 2),
            (cx - 8, cy - 4),
            (cx - 5, cy - 9),
            (cx + 5, cy - 9),
            (cx + 8, cy - 4),
            (cx + 8, cy + 2),
            (cx + 7, cy + 6),
            (cx + 3, cy + 8),
            (cx - 3, cy + 8),
        ]
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in head_shape])
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["skin_darkest"], head_shape)
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["skin_dark"], [
            (cx - 6, cy + 5), (cx - 7, cy + 2),
            (cx - 7, cy - 3), (cx - 4, cy - 8),
            (cx + 4, cy - 8), (cx + 7, cy - 3),
            (cx + 7, cy + 2), (cx + 6, cy + 5),
            (cx + 2, cy + 7), (cx - 2, cy + 7),
        ])
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["skin_mid"], [
            (cx - 5, cy + 3), (cx - 6, cy),
            (cx - 5, cy - 5), (cx - 2, cy - 7),
            (cx + 2, cy - 7), (cx + 5, cy - 5),
            (cx + 6, cy), (cx + 5, cy + 3),
        ])
        # Top highlight (bald shine)
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["skin_light"], [
            (cx - 3, cy - 6), (cx + 2, cy - 8),
            (cx + 3, cy - 5), (cx - 2, cy - 4),
        ])
        # RUNE tattoos on forehead
        glow_pulse = math.sin(phase * 1.2) * 0.3 + 0.7
        # Central forehead rune (bigger)
        alpha = _NS_zorothrax._alpha(230 * glow_pulse)
        _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_dark"], alpha),
                                (cx, cy - 5), 3)
        _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_mid"], alpha),
                                (cx, cy - 5), 2)
        _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_light"], alpha),
                                (cx, cy - 5), 1)
        pygame.draw.rect(surface, _NS_zorothrax.PALETTE["rune_shine"], (cx, cy - 5, 1, 1))
        # Side head runes
        for side in (-1, 1):
            pygame.draw.rect(surface, (*_NS_zorothrax.PALETTE["rune_mid"], alpha),
                             (cx + side * 5, cy - 3, 1, 1))
            pygame.draw.rect(surface, (*_NS_zorothrax.PALETTE["rune_mid"], alpha),
                             (cx + side * 6, cy, 1, 1))
        # EYES (glowing blue slits)
        _NS_zorothrax._draw_rune_eyes(surface, cx, cy, phase)
        # Nose (subtle line)
        pygame.draw.line(surface, _NS_zorothrax.PALETTE["skin_darkest"],
                         (cx, cy + 1), (cx, cy + 3), 1)
        pygame.draw.rect(surface, _NS_zorothrax.PALETTE["skin_dark"],
                         (cx - 1, cy + 3, 3, 1))
        # Mouth hidden by beard mustache
        pygame.draw.rect(surface, _NS_zorothrax.PALETTE["beard_dark"],
                         (cx - 3, cy + 5, 6, 2))
        pygame.draw.rect(surface, _NS_zorothrax.PALETTE["beard_mid"],
                         (cx - 3, cy + 5, 6, 1))
        # Mustache hairs
        for i, x_off in enumerate((-3, -1, 1, 3)):
            pygame.draw.line(surface, _NS_zorothrax.PALETTE["beard_light"],
                             (cx + x_off, cy + 5), (cx + x_off + i - 2, cy + 7), 1)
    def _draw_rune_eyes(surface, cx, cy, phase):
        """Two glowing rune eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_x in (cx - 3, cx + 3):
            # Socket
            pygame.draw.rect(surface, _NS_zorothrax.PALETTE["eye_socket"],
                             (eye_x - 2, cy - 1, 4, 3))
            # Glow halo
            for r in range(4, 0, -1):
                alpha = _NS_zorothrax._alpha(120 * (4 - r) / 4 * pulse)
                _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_mid"], alpha),
                                        (eye_x, cy), r)
            # Bright eye
            pygame.draw.rect(surface, _NS_zorothrax.PALETTE["eye_dark"],
                             (eye_x - 1, cy - 1, 3, 2))
            pygame.draw.rect(surface, _NS_zorothrax.PALETTE["eye_mid"],
                             (eye_x - 1, cy, 3, 1))
            pygame.draw.rect(surface, _NS_zorothrax.PALETTE["eye_light"],
                             (eye_x, cy, 1, 1))
            pygame.draw.rect(surface, _NS_zorothrax.PALETTE["eye_glow"],
                             (eye_x, cy, 1, 1))
    def _draw_beard(surface, cx, cy, facing, phase):
        """Long grey-white beard hanging down."""
        sway = math.sin(phase * 0.6) * 1
        # Beard mass (triangular hanging)
        beard_shape = [
            (cx - 6, cy),
            (cx - 7, cy + 4),
            (cx - 6 + int(sway), cy + 10),
            (cx - 4 + int(sway), cy + 16),
            (cx - 2 + int(sway), cy + 20),
            (cx + 2 + int(sway * 0.5), cy + 20),
            (cx + 4 + int(sway * 0.5), cy + 16),
            (cx + 6, cy + 10),
            (cx + 7, cy + 4),
            (cx + 6, cy),
        ]
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in beard_shape])
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["beard_dark"], beard_shape)
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["beard_mid"], [
            (cx - 5, cy + 1), (cx - 6, cy + 4),
            (cx - 5 + int(sway * 0.7), cy + 9),
            (cx - 3 + int(sway * 0.7), cy + 15),
            (cx - 1 + int(sway * 0.5), cy + 18),
            (cx + 1 + int(sway * 0.5), cy + 18),
            (cx + 3 + int(sway * 0.3), cy + 15),
            (cx + 5, cy + 9), (cx + 6, cy + 4), (cx + 5, cy + 1),
        ])
        _NS_zorothrax._poly(surface, _NS_zorothrax.PALETTE["beard_light"], [
            (cx - 3, cy + 3), (cx - 4, cy + 8),
            (cx - 2 + int(sway * 0.5), cy + 14),
            (cx, cy + 16),
            (cx + 2 + int(sway * 0.3), cy + 14),
            (cx + 4, cy + 8), (cx + 3, cy + 3),
        ])
        # Bright hair strokes
        for i in range(4):
            hx = cx - 3 + i * 2 + int(sway * 0.3)
            hy1 = cy + 3
            hy2 = cy + 15 + i
            pygame.draw.line(surface, _NS_zorothrax.PALETTE["beard_shine"],
                             (hx, hy1), (hx, hy2), 1)
        # Braid detail at end
        pygame.draw.rect(surface, _NS_zorothrax.PALETTE["gold_dark"],
                         (cx - 1, cy + 20, 2, 2))
        pygame.draw.rect(surface, _NS_zorothrax.PALETTE["gold_mid"], (cx, cy + 20, 1, 1))
    def _draw_orbiting_runes(surface, cx, cy, facing, phase):
        """Small rune symbols orbiting the mage."""
        for i in range(4):
            angle = phase * 0.5 + i * math.pi / 2
            radius_x = 22
            radius_y = 8
            rx = cx + int(math.cos(angle) * radius_x)
            ry = cy - 5 + int(math.sin(angle) * radius_y)
            pulse = math.sin(phase * 2 + i) * 0.3 + 0.7
            alpha = _NS_zorothrax._alpha(200 * pulse)
            # Rune symbol (small diamond)
            _NS_zorothrax._poly(surface, (*_NS_zorothrax.PALETTE["rune_dark"], alpha), [
                (rx, ry - 2), (rx + 2, ry),
                (rx, ry + 2), (rx - 2, ry),
            ])
            _NS_zorothrax._poly(surface, (*_NS_zorothrax.PALETTE["rune_mid"], alpha), [
                (rx, ry - 1), (rx + 1, ry),
                (rx, ry + 1), (rx - 1, ry),
            ])
            pygame.draw.rect(surface, (*_NS_zorothrax.PALETTE["rune_shine"], alpha),
                             (rx, ry, 1, 1))
    # ============================================================
    # AUTO-ATTACK - RUNE BOLT
    # ============================================================
    def _draw_rune_projectile(surface, boss, x, y, progress):
        """Blue rune bolt projectile."""
        facing = boss.direction
        # Charge phase in hand
        hand_x = x + facing * 18
        hand_y = y - 2
        if progress < 0.35:
            t = progress / 0.35
            cr = int(2 + t * 6)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_zorothrax._alpha(200 * (cr + 3 - r) / (cr + 3) * t)
                _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_dark"], alpha),
                                        (hand_x, hand_y), r)
            _NS_zorothrax._aacircle(surface, _NS_zorothrax.PALETTE["rune_mid"],
                                    (hand_x, hand_y), max(1, cr - 2))
            _NS_zorothrax._aacircle(surface, _NS_zorothrax.PALETTE["rune_light"],
                                    (hand_x, hand_y), max(1, cr - 4))
            for i in range(4):
                angle = progress * 20 + i * math.pi / 2
                sx = hand_x + int(math.cos(angle) * (cr + 2))
                sy = hand_y + int(math.sin(angle) * (cr + 2))
                pygame.draw.rect(surface, _NS_zorothrax.PALETTE["rune_hot"], (sx, sy, 1, 1))
            return
        if progress < 0.55:
            return
        # Travel phase
        tx, ty = _NS_zorothrax._target_position(boss, x, y)
        start_x = x + facing * 22
        start_y = y - 2
        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Comet trail (bright blue)
        for i in range(8):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_zorothrax._alpha(230 - i * 25)
            size = max(1, 7 - i)
            _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_darkest"], alpha),
                                    (px, py), size)
            _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_dark"], alpha),
                                    (px, py), max(1, size - 1))
            _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_mid"], alpha),
                                    (px, py), max(1, size - 2))
            _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_light"], alpha),
                                    (px, py), max(1, size - 3))
            if i < 3:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface,
                                     (*_NS_zorothrax.PALETTE["rune_hot"], alpha),
                                     (spark_x, spark_y, 1, 1))
        # Bright bolt head
        for r in range(10, 3, -1):
            alpha = _NS_zorothrax._alpha(90 * (10 - r) / 10)
            _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_light"], alpha),
                                    (bx, by), r)
        _NS_zorothrax._aacircle(surface, _NS_zorothrax.PALETTE["rune_darkest"], (bx, by), 7)
        _NS_zorothrax._aacircle(surface, _NS_zorothrax.PALETTE["rune_dark"], (bx, by), 5)
        _NS_zorothrax._aacircle(surface, _NS_zorothrax.PALETTE["rune_mid"], (bx, by), 3)
        _NS_zorothrax._aacircle(surface, _NS_zorothrax.PALETTE["rune_light"], (bx, by), 2)
        _NS_zorothrax._aacircle(surface, _NS_zorothrax.PALETTE["rune_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_zorothrax.PALETTE["white"], (bx, by, 1, 1))
        # Impact
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(8 + st * 22)
            alpha = _NS_zorothrax._alpha(240 * (1 - st))
            _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_darkest"], alpha),
                                    (tx, ty), radius + 3, 3)
            _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_dark"], alpha),
                                    (tx, ty), radius, 3)
            _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_mid"], alpha),
                                    (tx, ty), max(1, radius - 4), 2)
            _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_light"], alpha),
                                    (tx, ty), max(1, radius - 8), 1)
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_zorothrax.PALETTE["rune_hot"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # FLOATING SMOKE BASE
    # ============================================================
    def _draw_smoke_base(surface, cx, cy, phase, intense=False, moving=False, facing=1):
        """Arcane smoke below floating mage (where feet would be)."""
        strength = 1.3 if intense else 1.0
        smoke = pygame.Surface((100, 60), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(24, 3, -2):
            alpha = _NS_zorothrax._alpha((24 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    smoke, (*_NS_zorothrax.PALETTE["smoke_darkest"], alpha),
                    (50 - radius, 30 - radius // 2, radius * 2, max(3, radius)))
        for radius in range(18, 3, -2):
            alpha = _NS_zorothrax._alpha((18 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    smoke, (*_NS_zorothrax.PALETTE["smoke_dark"], alpha),
                    (50 - radius, 30 - radius // 2, radius * 2, max(3, radius)))
        for radius in range(12, 2, -1):
            alpha = _NS_zorothrax._alpha((12 - radius) * 6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    smoke, (*_NS_zorothrax.PALETTE["smoke_mid"], alpha),
                    (50 - radius, 30 - radius // 2, radius * 2, max(2, radius)))
        surface.blit(smoke, (cx - 50, cy - 15))
        # Rising rune particles
        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            px = cx - 18 + i * 5 + int(math.sin(phase + i) * 3)
            py = cy + 12 - int(t * 22)
            alpha = _NS_zorothrax._alpha(210 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_zorothrax.PALETTE["rune_mid"], alpha),
                                 (px, py, 1, 1))
                pygame.draw.rect(surface, (*_NS_zorothrax.PALETTE["rune_light"], alpha),
                                 (px, py, 1, 1))
        # Rune symbols floating up (small diamond)
        for i in range(3):
            t = (phase * 0.3 + i * 0.33) % 1.0
            rx = cx - 10 + i * 10
            ry = cy + 10 - int(t * 25)
            alpha = _NS_zorothrax._alpha(200 * (1 - t) * strength)
            if alpha > 0:
                _NS_zorothrax._poly(surface, (*_NS_zorothrax.PALETTE["rune_mid"], alpha), [
                    (rx, ry - 2), (rx + 2, ry),
                    (rx, ry + 2), (rx - 2, ry),
                ])
        # Trail when moving
        if moving:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + 8 + int(math.sin(phase + i) * 2)
                alpha = _NS_zorothrax._alpha(160 - i * 30)
                if alpha <= 0:
                    continue
                _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["smoke_dark"], alpha),
                                        (sx, sy), max(2, 6 - i))
                _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["smoke_mid"], alpha),
                                        (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_zorothrax.PALETTE["rune_light"], alpha),
                                 (sx, sy - 1, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 12)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius, 120 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (5, 5, 20, 150), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (30, 30, 80, 90), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_arcane_aura(surface, x, y, phase):
        """Blue arcane aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 190), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_zorothrax._alpha((95 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_zorothrax._aacircle(aura, (*_NS_zorothrax.PALETTE["rune_darkest"], alpha),
                                        (110, 95), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_zorothrax._alpha((60 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_zorothrax._aacircle(aura, (*_NS_zorothrax.PALETTE["rune_dark"], alpha),
                                        (110, 95), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_zorothrax._alpha((35 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_zorothrax._aacircle(aura, (*_NS_zorothrax.PALETTE["portal_dark"], alpha),
                                        (110, 95), radius)
        surface.blit(aura, (x - 110, y - 95))
        # Floating rune particles
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 42 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_zorothrax.PALETTE["rune_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_zorothrax.PALETTE["rune_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground rune circle."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_zorothrax.PALETTE["rune_darkest"], 200),
                            (5, 20, 170, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_zorothrax.PALETTE["rune_dark"], 220),
                            (14, 22, 152, 24), 2)
        pygame.draw.ellipse(ring, (*_NS_zorothrax.PALETTE["rune_mid"], 180),
                            (25, 24, 130, 20), 1)
        # Runes at cardinal points
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 34 + int(math.sin(angle) * 9)
            x2 = 90 + int(math.cos(angle) * 76)
            y2 = 34 + int(math.sin(angle) * 13)
            pygame.draw.line(ring, (*_NS_zorothrax.PALETTE["rune_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_zorothrax.PALETTE["rune_hot"],
                                       _NS_zorothrax._alpha(150 * pulse)),
                                (15, 12, 150, 42), 1)
        surface.blit(ring, (x - 90, y - 30))
    # ============================================================
    # SKILL Q - RUNEBOLT (bouncing lightning)
    # ============================================================
    def _draw_runebolt_skill(surface, boss, x, y, timer, phase):
        """Enhanced runebolt that bounces to nearby enemies."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_zorothrax._target_position(boss, x, y)
        if progress < 0.2:
            # Charge
            t = progress / 0.2
            hand_x = x + facing * 22
            hand_y = y - 2
            cr = int(4 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_zorothrax._alpha(220 * (cr + 5 - r) / (cr + 5))
                _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_darkest"], alpha),
                                        (hand_x, hand_y), r)
            _NS_zorothrax._aacircle(surface, _NS_zorothrax.PALETTE["rune_mid"], (hand_x, hand_y), cr - 2)
            _NS_zorothrax._aacircle(surface, _NS_zorothrax.PALETTE["rune_light"], (hand_x, hand_y),
                                    max(1, cr - 4))
            _NS_zorothrax._aacircle(surface, _NS_zorothrax.PALETTE["rune_shine"], (hand_x, hand_y),
                                    max(1, cr - 6))
            for i in range(8):
                angle = phase * 5 + i * math.pi / 4
                sx = hand_x + int(math.cos(angle) * (cr + 3))
                sy = hand_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_zorothrax.PALETTE["rune_hot"], (sx, sy, 1, 1))
            return
        # Multi-bounce trajectory
        t = (progress - 0.2) / 0.8
        t = min(1.0, t)
        start_x = x + facing * 24
        start_y = y - 2
        # Bounce points
        bounce_targets = [
            (tx, ty),
            (tx + 55, ty - 15),
            (tx + 20, ty + 25),
        ]
        num_bounces = len(bounce_targets)
        bounce_t = t * num_bounces
        current = min(int(bounce_t), num_bounces - 1)
        local_t = bounce_t - current
        seg_start = (start_x, start_y) if current == 0 else bounce_targets[current - 1]
        seg_end = bounce_targets[current]
        bx = int(seg_start[0] + (seg_end[0] - seg_start[0]) * local_t)
        by = int(seg_start[1] + (seg_end[1] - seg_start[1]) * local_t)
        # Draw electric trail from start through bounces
        prev_pt = (start_x, start_y)
        for bi in range(current):
            _NS_zorothrax._draw_lightning_line(surface, prev_pt, bounce_targets[bi], phase, alpha=180)
            prev_pt = bounce_targets[bi]
        _NS_zorothrax._draw_lightning_line(surface, prev_pt, (bx, by), phase, alpha=240)
        # Comet trail
        for i in range(8):
            trail_t = max(0.0, t - i * 0.04)
            trail_bt = trail_t * num_bounces
            trail_cur = min(int(trail_bt), num_bounces - 1)
            trail_local = trail_bt - trail_cur
            ts = (start_x, start_y) if trail_cur == 0 else bounce_targets[trail_cur - 1]
            te = bounce_targets[trail_cur]
            px = int(ts[0] + (te[0] - ts[0]) * trail_local)
            py = int(ts[1] + (te[1] - ts[1]) * trail_local)
            alpha = _NS_zorothrax._alpha(220 - i * 25)
            size = max(1, 7 - i)
            _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_dark"], alpha),
                                    (px, py), size)
            _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_light"], alpha),
                                    (px, py), max(1, size - 2))
        # Bright head
        for r in range(12, 3, -1):
            alpha = _NS_zorothrax._alpha(90 * (12 - r) / 12)
            _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_light"], alpha), (bx, by), r)
        _NS_zorothrax._aacircle(surface, _NS_zorothrax.PALETTE["rune_darkest"], (bx, by), 8)
        _NS_zorothrax._aacircle(surface, _NS_zorothrax.PALETTE["rune_mid"], (bx, by), 5)
        _NS_zorothrax._aacircle(surface, _NS_zorothrax.PALETTE["rune_light"], (bx, by), 3)
        _NS_zorothrax._aacircle(surface, _NS_zorothrax.PALETTE["rune_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_zorothrax.PALETTE["white"], (bx, by, 1, 1))
    def _draw_lightning_line(surface, p1, p2, phase, alpha=200):
        """Zigzag lightning between two points."""
        segments = 6
        prev = p1
        for i in range(1, segments + 1):
            t = i / segments
            base_x = int(p1[0] + (p2[0] - p1[0]) * t)
            base_y = int(p1[1] + (p2[1] - p1[1]) * t)
            # Perpendicular jitter
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            length = math.hypot(dx, dy) or 1
            perp_x = -dy / length
            perp_y = dx / length
            jitter = math.sin(phase * 20 + i) * 3 if 0 < i < segments else 0
            next_pt = (base_x + int(perp_x * jitter), base_y + int(perp_y * jitter))
            pygame.draw.line(surface, (*_NS_zorothrax.PALETTE["rune_light"], alpha),
                             prev, next_pt, 2)
            pygame.draw.line(surface, (*_NS_zorothrax.PALETTE["rune_shine"], alpha),
                             prev, next_pt, 1)
            prev = next_pt
    # ============================================================
    # SKILL W - GLYPH PRISON (cage)
    # ============================================================
    def _draw_prison_ground(surface, boss, x, y, timer, phase):
        """Bottom rune circle."""
        tx, ty = _NS_zorothrax._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(24 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_zorothrax.PALETTE["rune_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_zorothrax.PALETTE["rune_dark"], 240),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_zorothrax.PALETTE["rune_mid"], 200),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8), 1)
    def _draw_prison_foreground(surface, boss, x, y, timer, phase):
        """Vertical rune cylinder cage around target."""
        tx, ty = _NS_zorothrax._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        scale = min(1.0, progress * 2)
        cage_r = int(24 * scale)
        cage_h = int(40 * scale)
        if cage_r < 3:
            return
        # Top rune circle
        top_y = ty - cage_h
        pygame.draw.ellipse(surface, (*_NS_zorothrax.PALETTE["rune_darkest"], 220),
                            (tx - cage_r, top_y - cage_r // 3,
                             cage_r * 2, cage_r * 2 // 3), 2)
        pygame.draw.ellipse(surface, (*_NS_zorothrax.PALETTE["rune_mid"], 220),
                            (tx - cage_r + 2, top_y - cage_r // 3 + 1,
                             cage_r * 2 - 4, cage_r * 2 // 3 - 2), 1)
        # Vertical bars (8 bars around cylinder)
        num_bars = 8
        for i in range(num_bars):
            angle = phase * 0.5 + i * math.pi * 2 / num_bars
            bx = tx + int(math.cos(angle) * cage_r)
            by_bottom = ty + int(math.sin(angle) * cage_r * 0.3)
            by_top = top_y + int(math.sin(angle) * cage_r * 0.3)
            # Fade based on side (back bars dimmer)
            depth = (math.sin(angle) + 1) * 0.5
            alpha = _NS_zorothrax._alpha(200 + depth * 55)
            pulse_alpha = _NS_zorothrax._alpha(alpha * (math.sin(phase * 3 + i) * 0.2 + 0.8))
            pygame.draw.line(surface, (*_NS_zorothrax.PALETTE["rune_dark"], pulse_alpha),
                             (bx, by_bottom), (bx, by_top), 2)
            pygame.draw.line(surface, (*_NS_zorothrax.PALETTE["rune_light"], pulse_alpha),
                             (bx, by_bottom), (bx, by_top), 1)
            # Rune symbols on bar
            mid_y = (by_top + by_bottom) // 2
            _NS_zorothrax._poly(surface, (*_NS_zorothrax.PALETTE["rune_shine"], pulse_alpha), [
                (bx, mid_y - 2), (bx + 2, mid_y),
                (bx, mid_y + 2), (bx - 2, mid_y),
            ])
        # Center top pillar of light
        for r in range(6, 0, -1):
            alpha = _NS_zorothrax._alpha(180 * (6 - r) / 6)
            _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_mid"], alpha),
                                    (tx, top_y - 4), r)
        pygame.draw.rect(surface, _NS_zorothrax.PALETTE["rune_shine"], (tx, top_y - 4, 1, 1))
        # Damage ticks (sparkles inside)
        for i in range(6):
            spk_t = (phase * 1.5 + i * 0.16) % 1.0
            angle = i * math.pi / 3 + phase
            spk_x = tx + int(math.cos(angle) * cage_r * 0.6)
            spk_y = ty - int(spk_t * cage_h)
            alpha = _NS_zorothrax._alpha(240 * (1 - spk_t))
            pygame.draw.rect(surface, (*_NS_zorothrax.PALETTE["rune_hot"], alpha),
                             (spk_x, spk_y, 2, 2))
            pygame.draw.rect(surface, (*_NS_zorothrax.PALETTE["rune_shine"], alpha),
                             (spk_x, spk_y, 1, 1))
    # ============================================================
    # SKILL E - ARCANE WAVE (crescent slash)
    # ============================================================
    def _draw_arcanewave_skill(surface, boss, x, y, timer, phase):
        """Crescent wave of energy."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.15:
            # Charge in hand
            t = progress / 0.15
            hand_x = x + facing * 20
            hand_y = y - 2
            for r in range(int(4 + t * 6), 0, -1):
                alpha = _NS_zorothrax._alpha(200 * t)
                _NS_zorothrax._aacircle(surface, (*_NS_zorothrax.PALETTE["rune_dark"], alpha),
                                        (hand_x, hand_y), r)
            _NS_zorothrax._aacircle(surface, _NS_zorothrax.PALETTE["rune_light"],
                                    (hand_x, hand_y), 2)
            return
        # Wave expanding forward
        t = (progress - 0.15) / 0.85
        start_x = x + facing * 22
        start_y = y - 2
        # Wave distance
        max_dist = 200
        wave_dist = int(t * max_dist)
        wave_center_x = start_x + wave_dist * facing
        wave_center_y = start_y
        # Crescent shape (arc facing forward)
        wave_r = int(30 + t * 25)
        # Draw crescent with layered arcs
        for layer_i, (thick, alpha_val) in enumerate([
            (5, 100), (4, 140), (3, 180), (2, 220), (1, 255),
        ]):
            actual_alpha = _NS_zorothrax._alpha(alpha_val * (1 - t * 0.3))
            colors = [
                _NS_zorothrax.PALETTE["rune_darkest"],
                _NS_zorothrax.PALETTE["rune_dark"],
                _NS_zorothrax.PALETTE["rune_mid"],
                _NS_zorothrax.PALETTE["rune_light"],
                _NS_zorothrax.PALETTE["rune_shine"],
            ]
            color = colors[min(layer_i, 4)]
            # Draw arc as series of points along crescent
            num_pts = 16
            arc_start = -math.pi / 2 - 0.5
            arc_end = math.pi / 2 + 0.5
            prev_pt = None
            for i in range(num_pts + 1):
                arc_t = i / num_pts
                arc_angle = arc_start + (arc_end - arc_start) * arc_t
                px = wave_center_x + int(math.cos(arc_angle) * wave_r * 0.6) * facing
                py = wave_center_y + int(math.sin(arc_angle) * wave_r)
                if prev_pt:
                    pygame.draw.line(surface, (*color, actual_alpha),
                                     prev_pt, (px, py), thick)
                prev_pt = (px, py)
        # Sparkles along wave
        for i in range(10):
            spark_angle = -math.pi / 2 + i * math.pi / 9
            sx = wave_center_x + int(math.cos(spark_angle) * wave_r * 0.6) * facing
            sy = wave_center_y + int(math.sin(spark_angle) * wave_r)
            alpha = _NS_zorothrax._alpha(240 * (1 - t * 0.5))
            pygame.draw.rect(surface, (*_NS_zorothrax.PALETTE["rune_hot"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_zorothrax.PALETTE["rune_shine"], alpha),
                             (sx, sy, 1, 1))
        # Trail behind (thinner crescents)
        for trail_i in range(4):
            trail_dist = wave_dist - (trail_i + 1) * 15
            if trail_dist <= 0:
                continue
            trail_cx = start_x + trail_dist * facing
            trail_alpha = _NS_zorothrax._alpha(150 - trail_i * 35)
            num_pts = 8
            for i in range(num_pts):
                arc_t = i / (num_pts - 1)
                arc_angle = -math.pi / 2 + arc_t * math.pi
                px = trail_cx + int(math.cos(arc_angle) * wave_r * 0.6) * facing
                py = wave_center_y + int(math.sin(arc_angle) * wave_r)
                pygame.draw.rect(surface, (*_NS_zorothrax.PALETTE["rune_light"], trail_alpha),
                                 (px, py, 1, 1))
    # ============================================================
    # SKILL R - RIFT PORTAL
    # ============================================================
    def _draw_portal_ground(surface, boss, x, y, timer, pulse):
        """Both portals ground rings."""
        tx, ty = _NS_zorothrax._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(28 * min(1.0, progress * 2))
        # Portal 1 (near boss)
        near_x = x + boss.direction * 30
        near_y = y + 40
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_zorothrax.PALETTE["portal_darkest"], 200),
                                (near_x - r, near_y - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_zorothrax.PALETTE["portal_dark"], 220),
                                (near_x - r + 2, near_y - r // 3 + 1,
                                 r * 2 - 4, r * 2 // 3 - 2))
        # Portal 2 (at target)
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_zorothrax.PALETTE["portal_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_zorothrax.PALETTE["portal_dark"], 220),
                                (tx - r + 2, ty - r // 3 + 1,
                                 r * 2 - 4, r * 2 // 3 - 2))
    def _draw_portal_foreground(surface, boss, x, y, timer, phase):
        """Two vertical portals (oval shape like doorway)."""
        tx, ty = _NS_zorothrax._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        scale = min(1.0, progress * 2)
        # Two portal locations
        near_x = x + boss.direction * 30
        near_y = y - 5
        for portal_x, portal_y in [(near_x, near_y), (tx, ty - 5)]:
            _NS_zorothrax._draw_single_portal(surface, portal_x, portal_y, phase, scale)
        # Connecting energy line between portals
        if scale > 0.8:
            _NS_zorothrax._draw_lightning_line(surface, (near_x, near_y),
                                               (tx, ty - 5), phase, alpha=120)
    def _draw_single_portal(surface, cx, cy, phase, scale):
        """Vertical oval portal doorway."""
        port_w = int(22 * scale)
        port_h = int(38 * scale)
        if port_w < 3:
            return
        # Portal void interior
        pygame.draw.ellipse(surface, _NS_zorothrax.PALETTE["shadow"],
                            (cx - port_w - 1, cy - port_h - 1,
                             port_w * 2 + 2, port_h * 2 + 2))
        pygame.draw.ellipse(surface, _NS_zorothrax.PALETTE["portal_darkest"],
                            (cx - port_w, cy - port_h, port_w * 2, port_h * 2))
        pygame.draw.ellipse(surface, _NS_zorothrax.PALETTE["portal_dark"],
                            (cx - port_w + 2, cy - port_h + 2,
                             port_w * 2 - 4, port_h * 2 - 4))
        # Swirling energy inside
        for i in range(6):
            angle = phase * 2 + i * math.pi / 3
            sw_r = int(port_w * 0.5)
            sx = cx + int(math.cos(angle) * sw_r)
            sy = cy + int(math.sin(angle) * port_h * 0.5)
            alpha = _NS_zorothrax._alpha(200)
            pygame.draw.rect(surface, (*_NS_zorothrax.PALETTE["portal_mid"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_zorothrax.PALETTE["rune_light"], alpha),
                             (sx, sy, 1, 1))
        # Bright rune ring border
        for thick, alpha_val in [(3, 180), (2, 220), (1, 255)]:
            pygame.draw.ellipse(surface, (*_NS_zorothrax.PALETTE["rune_mid"], alpha_val),
                                (cx - port_w, cy - port_h,
                                 port_w * 2, port_h * 2), thick)
        pygame.draw.ellipse(surface, _NS_zorothrax.PALETTE["rune_light"],
                            (cx - port_w, cy - port_h,
                             port_w * 2, port_h * 2), 1)
        # Rune symbols around portal edge
        num_runes = 8
        for i in range(num_runes):
            angle = i * math.pi * 2 / num_runes + phase * 0.5
            rx = cx + int(math.cos(angle) * port_w)
            ry = cy + int(math.sin(angle) * port_h)
            pulse_a = _NS_zorothrax._alpha(220 * (math.sin(phase * 2 + i) * 0.3 + 0.7))
            _NS_zorothrax._poly(surface, (*_NS_zorothrax.PALETTE["rune_shine"], pulse_a), [
                (rx, ry - 2), (rx + 2, ry),
                (rx, ry + 2), (rx - 2, ry),
            ])



# ====================================================================
# KAGETSUKA (ETERNAL WARLORD) - TRUE BOSS
# ====================================================================

class _NS_kagetsuka:
    """Namespace kagetsuka - Eternal Warlord boss (samurai)."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (tan/pale male)
        "skin_darkest": (70, 45, 35),
        "skin_dark": (140, 100, 80),
        "skin_mid": (200, 165, 135),
        "skin_light": (240, 215, 185),
        # Hair (black spiky)
        "hair_darkest": (5, 5, 12),
        "hair_dark": (20, 18, 30),
        "hair_mid": (50, 45, 65),
        "hair_light": (95, 90, 115),
        # Armor (dark red/crimson)
        "armor_darkest": (25, 10, 15),
        "armor_dark": (70, 20, 30),
        "armor_mid": (130, 40, 50),
        "armor_light": (185, 75, 85),
        "armor_shine": (240, 130, 130),
        # Armor plates edges (metallic dark)
        "plate_dark": (20, 12, 18),
        "plate_mid": (50, 35, 45),
        "plate_light": (105, 85, 100),
        # Sharingan red (eye + fire aura)
        "sharingan_darkest": (35, 0, 5),
        "sharingan_dark": (110, 10, 20),
        "sharingan_mid": (200, 30, 40),
        "sharingan_light": (255, 90, 90),
        "sharingan_glow": (255, 180, 160),
        # Fire orange (skill Q)
        "fire_darkest": (40, 15, 5),
        "fire_dark": (130, 45, 10),
        "fire_mid": (225, 105, 20),
        "fire_light": (255, 180, 60),
        "fire_hot": (255, 230, 140),
        "fire_shine": (255, 250, 210),
        # Spectral blue (Susanoo)
        "spec_darkest": (5, 20, 40),
        "spec_dark": (20, 65, 130),
        "spec_mid": (55, 145, 225),
        "spec_light": (130, 205, 255),
        "spec_hot": (200, 235, 255),
        "spec_shine": (240, 250, 255),
        # Gunbai (war fan) - white with red pattern
        "fan_dark": (155, 145, 135),
        "fan_mid": (215, 205, 190),
        "fan_light": (245, 240, 225),
        "fan_shine": (255, 255, 245),
        # Wood handle
        "wood_dark": (35, 20, 10),
        "wood_mid": (80, 55, 30),
        "wood_light": (140, 100, 65),
        # Smoke tail (floating)
        "smoke_darkest": (10, 5, 15),
        "smoke_dark": (35, 20, 30),
        "smoke_mid": (75, 40, 55),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kagetsuka._clamp(color)
        if _NS_kagetsuka.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_kagetsuka._clamp(color)
        if _NS_kagetsuka.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_kagetsuka._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 150 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_kagetsuka(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kagetsuka._detect_moving(boss)
        _NS_kagetsuka._update_attack_anim(boss)
        attacking = getattr(boss, "_kg_attack_active", False)
        # Ambient
        _NS_kagetsuka._draw_shadow_aura(surface, x, y, pulse, active_skill)
        _NS_kagetsuka._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX
        if active_skill == "r":
            _NS_kagetsuka._draw_avatar_ground(surface, boss, x, y, skill_timer, pulse)
        # AVATAR (draw behind body for R)
        if active_skill == "r":
            _NS_kagetsuka._draw_susanoo_avatar(surface, boss, x, y, skill_timer, pulse)
        # Body
        if attacking:
            _NS_kagetsuka._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_kagetsuka._draw_walk(surface, boss, x, y)
        else:
            _NS_kagetsuka._draw_idle(surface, boss, x, y)
        # Foreground FX
        if active_skill == "q":
            _NS_kagetsuka._draw_hellfire_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kagetsuka._draw_sharingan_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kagetsuka._draw_ribcage_skill(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_kg_attack_active", False))
        if not active and timer <= 2:
            boss._kg_attack_active = True
            boss._kg_attack_frame = 0
            active = True
        if active:
            boss._kg_attack_frame = int(getattr(boss, "_kg_attack_frame", 0)) + 1
            if boss._kg_attack_frame >= cooldown:
                boss._kg_attack_active = False
                boss._kg_attack_frame = 0
                active = False
        boss._kg_attack_progress = (
            min(1.0, getattr(boss, "_kg_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_kg_last_x"):
            boss._kg_last_x = boss.x
            boss._kg_last_y = boss.y
            return False
        dx = abs(boss.x - boss._kg_last_x)
        dy = abs(boss.y - boss._kg_last_y)
        boss._kg_last_x = boss.x
        boss._kg_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_kagetsuka._draw_shadow(surface, x, y + 50)
        _NS_kagetsuka._draw_smoke_base(surface, x, y + 26 + bob, boss.pulse)
        _NS_kagetsuka._draw_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")
    def _draw_walk(surface, boss, x, y):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.7) * 5)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_kagetsuka._draw_shadow(surface, x + sway, y + 50)
        _NS_kagetsuka._draw_smoke_base(surface, x + sway, y + 26 + bob, phase,
                                        moving=True, facing=boss.direction)
        _NS_kagetsuka._draw_body(surface, x + sway, y + bob, boss.direction, phase, "walk")
    def _draw_attack(surface, boss, x, y):
        progress = getattr(boss, "_kg_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        bob = int(math.sin(boss.pulse * 0.5) * 3)
        # Wind up → swing → recovery
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 4) * boss.direction
        elif progress < 0.6:
            t = (progress - 0.3) / 0.3
            lunge = int((-4 + t * 12)) * boss.direction
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(8 * (1 - t)) * boss.direction
        _NS_kagetsuka._draw_shadow(surface, x + lunge, y + 50)
        _NS_kagetsuka._draw_smoke_base(surface, x + lunge, y + 26 + bob, boss.pulse,
                                        intense=True)
        _NS_kagetsuka._draw_body(surface, x + lunge, y + bob, boss.direction, boss.pulse,
                                 "attack", progress)
        _NS_kagetsuka._draw_gunbai_swing(surface, boss, x + lunge, y + bob, progress)
    # ============================================================
    # BODY - Samurai warrior
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0.0):
        # Long hair BEHIND (drawn first)
        _NS_kagetsuka._draw_hair_back(surface, cx, cy - 8, facing, phase)
        # Armor skirt bottom
        _NS_kagetsuka._draw_armor_skirt(surface, cx, cy, facing, phase)
        # Torso armor
        _NS_kagetsuka._draw_torso_armor(surface, cx, cy, facing, phase)
        # Back arm (holds chain of gunbai)
        _NS_kagetsuka._draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress)
        # Head
        _NS_kagetsuka._draw_head(surface, cx, cy - 22, facing, phase)
        # Front hair strands
        _NS_kagetsuka._draw_hair_front(surface, cx, cy - 22, facing, phase)
        # Front arm + gunbai
        _NS_kagetsuka._draw_gunbai_arm(surface, cx, cy, facing, phase, action, attack_progress)
    def _draw_armor_skirt(surface, cx, cy, facing, phase):
        """Armor skirt (haidate)."""
        sway = math.sin(phase * 0.5) * 1
        skirt_shape = [
            (cx - 10, cy + 8),
            (cx - 12, cy + 14),
            (cx - 13 + int(sway), cy + 22),
            (cx - 11 + int(sway), cy + 30),
            (cx - 8, cy + 34),
            (cx + 8, cy + 34),
            (cx + 11 + int(sway * 0.5), cy + 30),
            (cx + 13, cy + 22),
            (cx + 12, cy + 14),
            (cx + 10, cy + 8),
        ]
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["shadow_deep"],
              [(px + 2, py + 3) for px, py in skirt_shape])
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["armor_darkest"], skirt_shape)
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["armor_dark"], [
            (cx - 9, cy + 9), (cx - 11, cy + 14),
            (cx - 12 + int(sway * 0.5), cy + 21),
            (cx - 10 + int(sway * 0.5), cy + 29),
            (cx - 7, cy + 33), (cx + 7, cy + 33),
            (cx + 10 + int(sway * 0.3), cy + 29),
            (cx + 12, cy + 21), (cx + 11, cy + 14), (cx + 9, cy + 9),
        ])
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["armor_mid"], [
            (cx - 7, cy + 10), (cx - 9, cy + 15),
            (cx - 10, cy + 22), (cx - 6, cy + 28),
            (cx + 6, cy + 28), (cx + 10, cy + 22),
            (cx + 9, cy + 15), (cx + 7, cy + 10),
        ])
        # Vertical plate lines (kusazuri - armor strips)
        for x_off in (-8, -3, 3, 8):
            pygame.draw.line(surface, _NS_kagetsuka.PALETTE["plate_dark"],
                             (cx + x_off, cy + 10),
                             (cx + x_off + int(sway * 0.3), cy + 32), 1)
            pygame.draw.line(surface, _NS_kagetsuka.PALETTE["armor_light"],
                             (cx + x_off + 1, cy + 12),
                             (cx + x_off + 1 + int(sway * 0.3), cy + 30), 1)
        # Horizontal armor strip
        for y_off in (16, 24):
            pygame.draw.line(surface, _NS_kagetsuka.PALETTE["plate_mid"],
                             (cx - 10, cy + y_off), (cx + 10, cy + y_off), 1)
        # OBI (belt sash)
        pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["plate_dark"],
                         (cx - 11, cy + 7, 22, 4))
        pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["armor_darkest"],
                         (cx - 11, cy + 7, 22, 2))
        pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["armor_dark"],
                         (cx - 11, cy + 8, 22, 1))
        # Belt center emblem (small crest)
        pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["plate_light"],
                         (cx - 3, cy + 6, 6, 5))
        pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["plate_mid"],
                         (cx - 2, cy + 7, 4, 3))
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        alpha = _NS_kagetsuka._alpha(200 * pulse)
        pygame.draw.rect(surface, (*_NS_kagetsuka.PALETTE["sharingan_mid"], alpha),
                         (cx - 1, cy + 8, 2, 2))
        pygame.draw.rect(surface, (*_NS_kagetsuka.PALETTE["sharingan_light"], alpha),
                         (cx, cy + 8, 1, 1))
    def _draw_torso_armor(surface, cx, cy, facing, phase):
        """Chest plate armor (crimson)."""
        # Torso shape
        torso_shape = [
            (cx - 11, cy - 8),
            (cx - 13, cy - 3),
            (cx - 12, cy + 4),
            (cx - 10, cy + 9),
            (cx + 10, cy + 9),
            (cx + 12, cy + 4),
            (cx + 13, cy - 3),
            (cx + 11, cy - 8),
            (cx + 6, cy - 12),
            (cx - 6, cy - 12),
        ]
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["shadow_deep"],
              [(px + 2, py + 3) for px, py in torso_shape])
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["armor_darkest"], torso_shape)
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["armor_dark"], [
            (cx - 10, cy - 7), (cx - 12, cy - 2),
            (cx - 11, cy + 3), (cx - 9, cy + 8),
            (cx + 9, cy + 8), (cx + 11, cy + 3),
            (cx + 12, cy - 2), (cx + 10, cy - 7),
            (cx + 5, cy - 11), (cx - 5, cy - 11),
        ])
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["armor_mid"], [
            (cx - 8, cy - 5), (cx - 10, cy),
            (cx - 9, cy + 5), (cx - 7, cy + 7),
            (cx + 7, cy + 7), (cx + 9, cy + 5),
            (cx + 10, cy), (cx + 8, cy - 5),
            (cx + 3, cy - 9), (cx - 3, cy - 9),
        ])
        # Chest plate highlight (V-shape)
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["armor_light"], [
            (cx - 6, cy - 6), (cx, cy - 1),
            (cx + 6, cy - 6), (cx + 4, cy - 4),
            (cx, cy + 1), (cx - 4, cy - 4),
        ])
        # Shoulder pauldrons (large plates)
        for side in (-1, 1):
            # Pauldron shape
            paul_x = cx + side * 12
            paul_y = cy - 8
            _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["shadow_deep"], [
                (paul_x + 1, paul_y + 1),
                (paul_x + side * 6, paul_y - 3),
                (paul_x + side * 8, paul_y + 3),
                (paul_x + side * 5, paul_y + 9),
                (paul_x - side, paul_y + 6),
            ])
            _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["armor_darkest"], [
                (paul_x, paul_y),
                (paul_x + side * 5, paul_y - 4),
                (paul_x + side * 7, paul_y + 2),
                (paul_x + side * 4, paul_y + 8),
                (paul_x - side * 2, paul_y + 5),
            ])
            _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["armor_dark"], [
                (paul_x, paul_y - 1),
                (paul_x + side * 4, paul_y - 3),
                (paul_x + side * 6, paul_y + 2),
                (paul_x + side * 3, paul_y + 7),
                (paul_x - side, paul_y + 4),
            ])
            _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["armor_mid"], [
                (paul_x + side * 2, paul_y - 2),
                (paul_x + side * 5, paul_y + 1),
                (paul_x + side * 3, paul_y + 5),
                (paul_x, paul_y + 2),
            ])
            # Highlight ridge
            pygame.draw.line(surface, _NS_kagetsuka.PALETTE["armor_light"],
                             (paul_x + side * 2, paul_y - 2),
                             (paul_x + side * 4, paul_y - 3), 1)
            # Rivets
            pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["plate_dark"],
                             (paul_x + side * 3, paul_y + 5, 1, 1))
            pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["plate_light"],
                             (paul_x + side * 3, paul_y + 5, 1, 1))
        # Center chest V-armor detail
        pygame.draw.line(surface, _NS_kagetsuka.PALETTE["plate_dark"],
                         (cx - 6, cy - 6), (cx, cy + 1), 1)
        pygame.draw.line(surface, _NS_kagetsuka.PALETTE["plate_dark"],
                         (cx + 6, cy - 6), (cx, cy + 1), 1)
        # Horizontal segment lines
        for y_off in (2, 5):
            pygame.draw.line(surface, _NS_kagetsuka.PALETTE["plate_dark"],
                             (cx - 9, cy + y_off), (cx + 9, cy + y_off), 1)
    def _draw_head(surface, cx, cy, facing, phase):
        """Male samurai face."""
        # Face shape
        face_shape = [
            (cx - 6, cy + 6),
            (cx - 7, cy + 2),
            (cx - 7, cy - 3),
            (cx - 4, cy - 8),
            (cx + 4, cy - 8),
            (cx + 7, cy - 3),
            (cx + 7, cy + 2),
            (cx + 6, cy + 6),
            (cx + 2, cy + 8),
            (cx - 2, cy + 8),
        ]
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in face_shape])
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["skin_darkest"], face_shape)
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["skin_dark"], [
            (cx - 5, cy + 5), (cx - 6, cy + 2),
            (cx - 6, cy - 2), (cx - 3, cy - 7),
            (cx + 3, cy - 7), (cx + 6, cy - 2),
            (cx + 6, cy + 2), (cx + 5, cy + 5),
            (cx + 1, cy + 7), (cx - 1, cy + 7),
        ])
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["skin_mid"], [
            (cx - 4, cy + 3), (cx - 5, cy + 1),
            (cx - 4, cy - 3), (cx - 2, cy - 6),
            (cx + 2, cy - 6), (cx + 4, cy - 3),
            (cx + 5, cy + 1), (cx + 4, cy + 3),
        ])
        # Cheekbone highlight
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["skin_light"], [
            (cx - 3, cy - 1), (cx - 1, cy - 3),
            (cx - 1, cy), (cx - 3, cy + 1),
        ])
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["skin_light"], [
            (cx + 1, cy - 3), (cx + 3, cy - 1),
            (cx + 3, cy + 1), (cx + 1, cy),
        ])
        # EYES (fierce, red sharingan)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_x in (cx - 2, cx + 2):
            # Eye socket
            pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["shadow_deep"],
                             (eye_x - 1, cy - 2, 2, 2))
            # Red sharingan glow
            for r in range(4, 0, -1):
                alpha = _NS_kagetsuka._alpha(120 * (4 - r) / 4 * pulse)
                _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["sharingan_mid"], alpha),
                                        (eye_x, cy - 1), r)
            pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["sharingan_dark"],
                             (eye_x - 1, cy - 2, 2, 2))
            pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["sharingan_mid"],
                             (eye_x - 1, cy - 1, 2, 1))
            pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["sharingan_light"],
                             (eye_x, cy - 1, 1, 1))
            pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["sharingan_glow"],
                             (eye_x, cy - 1, 1, 1))
        # Fierce eyebrow (angry)
        pygame.draw.line(surface, _NS_kagetsuka.PALETTE["hair_darkest"],
                         (cx - 4, cy - 4), (cx - 1, cy - 3), 2)
        pygame.draw.line(surface, _NS_kagetsuka.PALETTE["hair_dark"],
                         (cx - 4, cy - 4), (cx - 1, cy - 3), 1)
        pygame.draw.line(surface, _NS_kagetsuka.PALETTE["hair_darkest"],
                         (cx + 1, cy - 3), (cx + 4, cy - 4), 2)
        pygame.draw.line(surface, _NS_kagetsuka.PALETTE["hair_dark"],
                         (cx + 1, cy - 3), (cx + 4, cy - 4), 1)
        # Nose
        pygame.draw.line(surface, _NS_kagetsuka.PALETTE["skin_darkest"],
                         (cx, cy), (cx, cy + 3), 1)
        pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["skin_dark"],
                         (cx - 1, cy + 3, 3, 1))
        # Mouth (stern)
        pygame.draw.line(surface, _NS_kagetsuka.PALETTE["hair_darkest"],
                         (cx - 2, cy + 5), (cx + 2, cy + 5), 1)
    def _draw_hair_back(surface, cx, cy, facing, phase):
        """Huge messy black hair mane behind."""
        sway = math.sin(phase * 0.5) * 2
        # HUGE mane shape (wild spiky)
        hair_shape = [
            (cx - 15, cy - 8),
            (cx - 18 + int(sway), cy - 2),
            (cx - 20 + int(sway), cy + 8),
            (cx - 19 + int(sway), cy + 18),
            (cx - 15 + int(sway), cy + 28),
            (cx - 8 + int(sway * 0.5), cy + 34),
            (cx + 8 + int(sway * 0.3), cy + 34),
            (cx + 15 + int(sway * 0.3), cy + 28),
            (cx + 19, cy + 18),
            (cx + 20, cy + 8),
            (cx + 18, cy - 2),
            (cx + 15, cy - 8),
        ]
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in hair_shape])
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["hair_darkest"], hair_shape)
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["hair_dark"], [
            (cx - 14, cy - 7),
            (cx - 17 + int(sway * 0.7), cy - 1),
            (cx - 19 + int(sway * 0.7), cy + 8),
            (cx - 18 + int(sway * 0.7), cy + 17),
            (cx - 14 + int(sway * 0.7), cy + 27),
            (cx - 7 + int(sway * 0.3), cy + 33),
            (cx + 7 + int(sway * 0.3), cy + 33),
            (cx + 14, cy + 27),
            (cx + 18, cy + 17),
            (cx + 19, cy + 8),
            (cx + 17, cy - 1),
            (cx + 14, cy - 7),
        ])
        # Spiky highlights (bright strand streaks)
        for i, (sx1, sy1, sx2, sy2) in enumerate([
            (-13, -3, -16, 8), (-8, -6, -6, 8),
            (10, -6, 14, 8), (14, -3, 17, 8),
            (-11, 12, -14, 22), (11, 12, 14, 22),
            (0, 12, 2, 28),
        ]):
            wave = int(sway * 0.3) if sy1 > 0 else 0
            pygame.draw.line(surface, _NS_kagetsuka.PALETTE["hair_mid"],
                             (cx + sx1 + wave, cy + sy1),
                             (cx + sx2 + wave, cy + sy2), 2)
            pygame.draw.line(surface, _NS_kagetsuka.PALETTE["hair_light"],
                             (cx + sx1 + wave - 1, cy + sy1),
                             (cx + sx2 + wave - 1, cy + sy2), 1)
        # Spiky tips at bottom
        for tx in (-10, -4, 4, 10):
            spike_x = cx + tx + int(sway * 0.3)
            spike_y = cy + 32
            _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["hair_darkest"], [
                (spike_x - 2, spike_y),
                (spike_x, spike_y + 4),
                (spike_x + 2, spike_y),
            ])
            _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["hair_dark"], [
                (spike_x - 1, spike_y),
                (spike_x, spike_y + 3),
                (spike_x + 1, spike_y),
            ])
        # Spiky top tips
        for tx in (-12, -8, -4, 4, 8, 12):
            spike_x = cx + tx
            spike_y = cy - 8
            _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["hair_darkest"], [
                (spike_x - 1, spike_y),
                (spike_x, spike_y - 4),
                (spike_x + 1, spike_y),
            ])
            # Small line instead of polygon (was causing 2-point polygon)
            pygame.draw.line(surface, _NS_kagetsuka.PALETTE["hair_dark"],
                             (spike_x, spike_y), (spike_x, spike_y - 3), 1)
    def _draw_hair_front(surface, cx, cy, facing, phase):
        """Front hair bangs covering forehead partially."""
        sway = math.sin(phase * 0.5) * 1
        # Center bang
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["hair_darkest"], [
            (cx - 5, cy - 8), (cx - 3, cy - 4),
            (cx + 3, cy - 4), (cx + 5, cy - 8),
        ])
        _NS_kagetsuka._poly(surface, _NS_kagetsuka.PALETTE["hair_dark"], [
            (cx - 4, cy - 7), (cx - 2, cy - 5),
            (cx + 2, cy - 5), (cx + 4, cy - 7),
        ])
        # Side hair falling down
        for side in (-1, 1):
            base_x = cx + side * 5
            base_y = cy - 6
            tip_x = base_x + side * 2 + int(sway * side * 0.5)
            tip_y = base_y + 16
            pygame.draw.line(surface, _NS_kagetsuka.PALETTE["hair_darkest"],
                             (base_x, base_y), (tip_x, tip_y), 3)
            pygame.draw.line(surface, _NS_kagetsuka.PALETTE["hair_dark"],
                             (base_x, base_y), (tip_x, tip_y), 2)
            pygame.draw.line(surface, _NS_kagetsuka.PALETTE["hair_mid"],
                             (base_x - 1, base_y + 2),
                             (tip_x - 1, tip_y - 2), 1)
    def _draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm holding chain of gunbai."""
        back_side = -facing
        shoulder_x = cx + back_side * 10
        shoulder_y = cy - 6
        # Arm just hangs at side
        elbow_x = shoulder_x + back_side * 3
        elbow_y = shoulder_y + 8
        hand_x = elbow_x - back_side * 1
        hand_y = elbow_y + 8
        # Draw arm
        _NS_kagetsuka._draw_arm_segment(surface, (shoulder_x, shoulder_y),
                                         (elbow_x, elbow_y), 6, 0.8)
        _NS_kagetsuka._draw_arm_segment(surface, (elbow_x, elbow_y),
                                         (hand_x, hand_y), 5, 0.8)
        # Bracer at wrist
        _NS_kagetsuka._draw_bracer(surface, hand_x, hand_y - 2, 0.8)
    def _draw_gunbai_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding gunbai (war fan)."""
        shoulder_x = cx + facing * 10
        shoulder_y = cy - 6
        # Arm position based on action
        if action == "attack":
            # Wind up (behind) → swing forward
            if attack_progress < 0.3:
                t = attack_progress / 0.3
                # Raise arm up
                arm_angle = math.pi * 0.4 - t * 0.5
                arm_len = 12
            elif attack_progress < 0.6:
                t = (attack_progress - 0.3) / 0.3
                # Swing from up to forward-down
                arm_angle = math.pi * 0.3 - t * math.pi * 0.7
                arm_len = 12 + int(t * 4)
            else:
                t = (attack_progress - 0.6) / 0.4
                # Recovery
                arm_angle = -math.pi * 0.4 + t * math.pi * 0.4
                arm_len = 16 - int(t * 4)
        else:
            # Idle: arm at side holding gunbai
            arm_angle = -math.pi * 0.2
            arm_len = 12
        # Hand position
        hand_x = shoulder_x + int(math.cos(arm_angle) * arm_len) * facing
        hand_y = shoulder_y - int(math.sin(arm_angle) * arm_len)
        # Elbow (midpoint)
        elbow_x = (shoulder_x + hand_x) // 2
        elbow_y = (shoulder_y + hand_y) // 2 + 2
        # Draw arm
        _NS_kagetsuka._draw_arm_segment(surface, (shoulder_x, shoulder_y),
                                         (elbow_x, elbow_y), 6, 1.0)
        _NS_kagetsuka._draw_arm_segment(surface, (elbow_x, elbow_y),
                                         (hand_x, hand_y), 5, 1.0)
        # Bracer
        _NS_kagetsuka._draw_bracer(surface, hand_x, hand_y - 2, 1.0)
        # GUNBAI (war fan)
        _NS_kagetsuka._draw_gunbai(surface, hand_x, hand_y, facing, phase, arm_angle,
                                    action, attack_progress)
    def _draw_arm_segment(surface, p1, p2, thickness, depth_shade=1.0):
        """Armor-covered arm."""
        def shade(color):
            return tuple(int(c * depth_shade) for c in color)
        _NS_kagetsuka._aaline(surface, _NS_kagetsuka.PALETTE["shadow_deep"],
                (p1[0] + 2, p1[1] + 2), (p2[0] + 2, p2[1] + 2), thickness + 1)
        _NS_kagetsuka._aaline(surface, shade(_NS_kagetsuka.PALETTE["armor_darkest"]),
                p1, p2, thickness)
        _NS_kagetsuka._aaline(surface, shade(_NS_kagetsuka.PALETTE["armor_dark"]),
                p1, p2, max(1, thickness - 2))
        _NS_kagetsuka._aaline(surface, shade(_NS_kagetsuka.PALETTE["armor_mid"]),
                (p1[0] - 1, p1[1] - 1), (p2[0] - 1, p2[1] - 1),
                max(1, thickness - 4))
    def _draw_bracer(surface, cx, cy, depth_shade=1.0):
        """Metal bracer."""
        def shade(color):
            return tuple(int(c * depth_shade) for c in color)
        pygame.draw.rect(surface, shade(_NS_kagetsuka.PALETTE["plate_dark"]),
                         (cx - 4, cy - 2, 8, 6))
        pygame.draw.rect(surface, shade(_NS_kagetsuka.PALETTE["plate_mid"]),
                         (cx - 3, cy - 1, 6, 4))
        pygame.draw.rect(surface, shade(_NS_kagetsuka.PALETTE["plate_light"]),
                         (cx - 3, cy - 1, 6, 1))
    def _draw_gunbai(surface, hand_x, hand_y, facing, phase, arm_angle,
                     action, attack_progress):
        """War fan - large round white fan with red center."""
        # Handle extends from hand
        handle_len = 16
        handle_angle = arm_angle
        handle_tip_x = hand_x + int(math.cos(handle_angle) * handle_len) * facing
        handle_tip_y = hand_y - int(math.sin(handle_angle) * handle_len)
        # Handle (wood)
        pygame.draw.line(surface, _NS_kagetsuka.PALETTE["shadow_deep"],
                         (hand_x + 1, hand_y + 1), (handle_tip_x + 1, handle_tip_y + 1), 5)
        pygame.draw.line(surface, _NS_kagetsuka.PALETTE["wood_dark"],
                         (hand_x, hand_y), (handle_tip_x, handle_tip_y), 4)
        pygame.draw.line(surface, _NS_kagetsuka.PALETTE["wood_mid"],
                         (hand_x, hand_y), (handle_tip_x, handle_tip_y), 2)
        pygame.draw.line(surface, _NS_kagetsuka.PALETTE["wood_light"],
                         (hand_x, hand_y), (handle_tip_x, handle_tip_y), 1)
        # FAN HEAD at handle tip
        # Fan is oval/round shape, perpendicular to handle
        fan_cx = handle_tip_x + int(math.cos(handle_angle) * 12) * facing
        fan_cy = handle_tip_y - int(math.sin(handle_angle) * 12)
        # Fan radius
        fan_r = 14
        # Shadow
        pygame.draw.circle(surface, _NS_kagetsuka.PALETTE["shadow_deep"],
                           (fan_cx + 2, fan_cy + 2), fan_r + 1)
        # Fan body (white/cream with red details)
        pygame.draw.circle(surface, _NS_kagetsuka.PALETTE["fan_dark"], (fan_cx, fan_cy), fan_r)
        pygame.draw.circle(surface, _NS_kagetsuka.PALETTE["fan_mid"], (fan_cx, fan_cy), fan_r - 1)
        pygame.draw.circle(surface, _NS_kagetsuka.PALETTE["fan_light"], (fan_cx, fan_cy), fan_r - 3)
        pygame.draw.circle(surface, _NS_kagetsuka.PALETTE["fan_shine"], (fan_cx - 3, fan_cy - 4), fan_r - 8)
        # Center red circle (crest)
        pygame.draw.circle(surface, _NS_kagetsuka.PALETTE["sharingan_dark"], (fan_cx, fan_cy), 4)
        pygame.draw.circle(surface, _NS_kagetsuka.PALETTE["sharingan_mid"], (fan_cx, fan_cy), 3)
        pygame.draw.circle(surface, _NS_kagetsuka.PALETTE["sharingan_light"], (fan_cx, fan_cy), 1)
        # Small red circles around edge (like fan pattern)
        for i in range(3):
            angle = i * math.pi * 2 / 3 + math.pi / 6
            dot_x = fan_cx + int(math.cos(angle) * 8)
            dot_y = fan_cy + int(math.sin(angle) * 8)
            pygame.draw.circle(surface, _NS_kagetsuka.PALETTE["sharingan_dark"], (dot_x, dot_y), 2)
            pygame.draw.circle(surface, _NS_kagetsuka.PALETTE["sharingan_mid"], (dot_x, dot_y), 1)
        # Fan border dark
        pygame.draw.circle(surface, _NS_kagetsuka.PALETTE["plate_dark"], (fan_cx, fan_cy), fan_r, 2)
        pygame.draw.circle(surface, _NS_kagetsuka.PALETTE["plate_mid"], (fan_cx, fan_cy), fan_r, 1)
        # Chain hanging from handle end
        chain_start = (hand_x, hand_y + 2)
        chain_end = (hand_x + facing * 3, hand_y + 12)
        for i in range(4):
            t1 = i / 4
            t2 = (i + 1) / 4
            cx1 = int(chain_start[0] + (chain_end[0] - chain_start[0]) * t1)
            cy1 = int(chain_start[1] + (chain_end[1] - chain_start[1]) * t1 +
                      math.sin(phase * 0.5 + i) * 1)
            cx2 = int(chain_start[0] + (chain_end[0] - chain_start[0]) * t2)
            cy2 = int(chain_start[1] + (chain_end[1] - chain_start[1]) * t2 +
                      math.sin(phase * 0.5 + i + 1) * 1)
            pygame.draw.circle(surface, _NS_kagetsuka.PALETTE["plate_dark"], (cx1, cy1), 2)
            pygame.draw.circle(surface, _NS_kagetsuka.PALETTE["plate_light"], (cx1, cy1), 1)
    def _draw_gunbai_swing(surface, boss, x, y, progress):
        """Wind/dust arc from gunbai swing."""
        if progress < 0.3 or progress > 0.7:
            return
        facing = boss.direction
        t = (progress - 0.3) / 0.4
        # Swing center at shoulder
        cx = x + facing * 10
        cy = y - 6
        start_angle = math.pi * 0.3
        end_angle = -math.pi * 0.4
        current_angle = start_angle + (end_angle - start_angle) * t
        radius = 32
        # Trail arc
        num_segs = 10
        for seg in range(num_segs):
            seg_t = seg / num_segs
            seg_angle = start_angle + (current_angle - start_angle) * seg_t
            seg_alpha = _NS_kagetsuka._alpha(220 * (1 - seg_t) * (1 - abs(t - 0.5) * 0.3))
            r = int(radius - seg * 0.5)
            sx = cx + int(math.cos(seg_angle) * r) * facing
            sy = cy - int(math.sin(seg_angle) * r)
            size = int(7 - seg * 0.4)
            _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["fan_dark"], seg_alpha),
                                    (sx, sy), size)
            _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["fan_mid"], seg_alpha),
                                    (sx, sy), max(1, size - 2))
            _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["fan_light"], seg_alpha),
                                    (sx, sy), max(1, size - 4))
        # Bright leading edge
        lead_x = cx + int(math.cos(current_angle) * radius) * facing
        lead_y = cy - int(math.sin(current_angle) * radius)
        for r in range(9, 0, -1):
            alpha = _NS_kagetsuka._alpha(140 * (9 - r) / 9)
            _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["fan_light"], alpha),
                                    (lead_x, lead_y), r)
        _NS_kagetsuka._aacircle(surface, _NS_kagetsuka.PALETTE["fan_shine"], (lead_x, lead_y), 3)
        pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["white"], (lead_x, lead_y, 1, 1))
        # Dust/wind particles
        for i in range(10):
            spark_angle = start_angle + (current_angle - start_angle) * (i / 10)
            spark_r = radius + int(math.sin(progress * 10 + i) * 4)
            spx = cx + int(math.cos(spark_angle) * spark_r) * facing
            spy = cy - int(math.sin(spark_angle) * spark_r)
            pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["fan_shine"], (spx, spy, 1, 1))
    # ============================================================
    # SMOKE BASE (floating below)
    # ============================================================
    def _draw_smoke_base(surface, cx, cy, phase, intense=False, moving=False, facing=1):
        strength = 1.3 if intense else 1.0
        smoke = pygame.Surface((100, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(20, 3, -2):
            alpha = _NS_kagetsuka._alpha((20 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    smoke, (*_NS_kagetsuka.PALETTE["smoke_darkest"], alpha),
                    (50 - radius, 25 - radius // 2, radius * 2, max(3, radius)))
        for radius in range(14, 3, -2):
            alpha = _NS_kagetsuka._alpha((14 - radius) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    smoke, (*_NS_kagetsuka.PALETTE["smoke_dark"], alpha),
                    (50 - radius, 25 - radius // 2, radius * 2, max(2, radius)))
        surface.blit(smoke, (cx - 50, cy - 12))
        # Rising embers (crimson)
        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            px = cx - 18 + i * 5 + int(math.sin(phase + i) * 3)
            py = cy + 12 - int(t * 22)
            alpha = _NS_kagetsuka._alpha(210 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_kagetsuka.PALETTE["sharingan_dark"], alpha),
                                 (px, py, 1, 1))
                pygame.draw.rect(surface, (*_NS_kagetsuka.PALETTE["sharingan_mid"], alpha),
                                 (px, py, 1, 1))
        if moving:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + 8 + int(math.sin(phase + i) * 2)
                alpha = _NS_kagetsuka._alpha(160 - i * 30)
                if alpha <= 0:
                    continue
                _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["smoke_dark"], alpha),
                                        (sx, sy), max(2, 6 - i))
                pygame.draw.rect(surface, (*_NS_kagetsuka.PALETTE["sharingan_mid"], alpha),
                                 (sx, sy - 1, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 12)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius, 120 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (15, 5, 10, 150), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (60, 15, 20, 90), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_shadow_aura(surface, x, y, phase, active_skill):
        """Dark red aura - shifts to blue if R active."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        if active_skill == "r":
            aura_color = _NS_kagetsuka.PALETTE["spec_dark"]
            inner_color = _NS_kagetsuka.PALETTE["spec_mid"]
        else:
            aura_color = _NS_kagetsuka.PALETTE["armor_darkest"]
            inner_color = _NS_kagetsuka.PALETTE["sharingan_dark"]
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_kagetsuka._alpha((100 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_kagetsuka._aacircle(aura, (*_NS_kagetsuka.PALETTE["smoke_darkest"], alpha),
                                        (120, 100), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_kagetsuka._alpha((65 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_kagetsuka._aacircle(aura, (*aura_color, alpha), (120, 100), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_kagetsuka._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_kagetsuka._aacircle(aura, (*inner_color, alpha), (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))
        # Floating embers
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 45 + int(math.sin(phase + i) * 14)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            if active_skill == "r":
                col = _NS_kagetsuka.PALETTE["spec_mid"]
                hot = _NS_kagetsuka.PALETTE["spec_hot"]
            else:
                col = _NS_kagetsuka.PALETTE["sharingan_mid"]
                hot = _NS_kagetsuka.PALETTE["sharingan_light"]
            pygame.draw.rect(surface, col, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot, (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_kagetsuka.PALETTE["armor_darkest"], 200),
                            (5, 20, 170, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_kagetsuka.PALETTE["sharingan_dark"], 220),
                            (14, 22, 152, 24), 2)
        pygame.draw.ellipse(ring, (*_NS_kagetsuka.PALETTE["armor_dark"], 180),
                            (25, 24, 130, 20), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 34 + int(math.sin(angle) * 9)
            x2 = 90 + int(math.cos(angle) * 76)
            y2 = 34 + int(math.sin(angle) * 13)
            pygame.draw.line(ring, (*_NS_kagetsuka.PALETTE["sharingan_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_kagetsuka.PALETTE["sharingan_glow"],
                                       _NS_kagetsuka._alpha(150 * pulse)),
                                (15, 12, 150, 42), 1)
        surface.blit(ring, (x - 90, y - 30))
    # ============================================================
    # SKILL Q - HELLFIRE ORB (giant fireball)
    # ============================================================
    def _draw_hellfire_skill(surface, boss, x, y, timer, phase):
        """Big fireball projectile."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kagetsuka._target_position(boss, x, y)
        # Origin from mouth/face
        origin_x = x + facing * 8
        origin_y = y - 20
        if progress < 0.25:
            # Charge - fire builds up in mouth/hand
            t = progress / 0.25
            cr = int(4 + t * 14)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_kagetsuka._alpha(220 * (cr + 6 - r) / (cr + 6))
                _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["fire_darkest"], alpha),
                                        (origin_x, origin_y), r)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_kagetsuka._alpha(220 * (cr + 3 - r) / (cr + 3))
                _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["fire_dark"], alpha),
                                        (origin_x, origin_y), r)
            _NS_kagetsuka._aacircle(surface, _NS_kagetsuka.PALETTE["fire_mid"], (origin_x, origin_y), cr - 2)
            _NS_kagetsuka._aacircle(surface, _NS_kagetsuka.PALETTE["fire_light"], (origin_x, origin_y), max(1, cr - 5))
            _NS_kagetsuka._aacircle(surface, _NS_kagetsuka.PALETTE["fire_hot"], (origin_x, origin_y), max(1, cr - 7))
            _NS_kagetsuka._aacircle(surface, _NS_kagetsuka.PALETTE["fire_shine"], (origin_x, origin_y), max(1, cr - 9))
            # Flame flicker
            for i in range(10):
                angle = phase * 4 + i * math.pi / 5
                sx = origin_x + int(math.cos(angle) * (cr + 3))
                sy = origin_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["fire_hot"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["fire_shine"], (sx, sy, 1, 1))
            return
        # Flight phase (giant fireball)
        t = (progress - 0.25) / 0.75
        t = min(1.0, t)
        bx = int(origin_x + (tx - origin_x) * t)
        by = int(origin_y + (ty - origin_y) * t)
        # Fireball size grows during flight
        ball_r = int(14 + t * 4)
        # Trailing fire tail
        for i in range(12):
            trail_t = max(0.0, t - i * 0.035)
            px = int(origin_x + (tx - origin_x) * trail_t)
            py = int(origin_y + (ty - origin_y) * trail_t)
            alpha = _NS_kagetsuka._alpha(240 - i * 18)
            size = max(1, ball_r - i)
            _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["fire_darkest"], alpha),
                                    (px, py), size)
            _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["fire_dark"], alpha),
                                    (px, py), max(1, size - 2))
            _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["fire_mid"], alpha),
                                    (px, py), max(1, size - 4))
            _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["fire_light"], alpha),
                                    (px, py), max(1, size - 6))
            # Wobbling flames
            if i < 5:
                for s in range(3):
                    ang = phase * 3 + i + s * 2
                    fx = px + int(math.cos(ang) * (size + 3))
                    fy = py + int(math.sin(ang) * (size + 3))
                    pygame.draw.rect(surface, (*_NS_kagetsuka.PALETTE["fire_hot"], alpha),
                                     (fx, fy, 2, 2))
                    pygame.draw.rect(surface, (*_NS_kagetsuka.PALETTE["fire_shine"], alpha),
                                     (fx, fy, 1, 1))
        # Massive bright bolt head
        for r in range(ball_r + 6, 3, -2):
            alpha = _NS_kagetsuka._alpha(120 * (ball_r + 6 - r) / (ball_r + 6))
            _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["fire_light"], alpha), (bx, by), r)
        _NS_kagetsuka._aacircle(surface, _NS_kagetsuka.PALETTE["fire_darkest"], (bx, by), ball_r)
        _NS_kagetsuka._aacircle(surface, _NS_kagetsuka.PALETTE["fire_dark"], (bx, by), ball_r - 2)
        _NS_kagetsuka._aacircle(surface, _NS_kagetsuka.PALETTE["fire_mid"], (bx, by), ball_r - 5)
        _NS_kagetsuka._aacircle(surface, _NS_kagetsuka.PALETTE["fire_light"], (bx, by), ball_r - 8)
        _NS_kagetsuka._aacircle(surface, _NS_kagetsuka.PALETTE["fire_hot"], (bx, by), ball_r - 10)
        _NS_kagetsuka._aacircle(surface, _NS_kagetsuka.PALETTE["fire_shine"], (bx, by), max(1, ball_r - 12))
        pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["white"], (bx, by, 2, 2))
        # Flame licks around ball
        for i in range(8):
            angle = phase * 3 + i * math.pi / 4
            flame_r = ball_r + int(math.sin(phase * 4 + i) * 4)
            fx = bx + int(math.cos(angle) * flame_r)
            fy = by + int(math.sin(angle) * flame_r)
            for r in range(3, 0, -1):
                a = _NS_kagetsuka._alpha(200 * (3 - r) / 3)
                _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["fire_hot"], a), (fx, fy), r)
            pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["fire_shine"], (fx, fy, 1, 1))
        # Impact
        if t > 0.9:
            st = (t - 0.9) / 0.1
            radius = int(20 + st * 25)
            alpha = _NS_kagetsuka._alpha(240 * (1 - st))
            _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["fire_darkest"], alpha),
                                    (tx, ty), radius + 3, 3)
            _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["fire_dark"], alpha),
                                    (tx, ty), radius, 3)
            _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["fire_mid"], alpha),
                                    (tx, ty), max(1, radius - 5), 2)
            _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["fire_light"], alpha),
                                    (tx, ty), max(1, radius - 12), 1)
            for i in range(14):
                a_s = i * math.pi / 7
                ex = tx + int(math.cos(a_s) * radius)
                ey = ty + int(math.sin(a_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_kagetsuka.PALETTE["fire_hot"], alpha),
                                 (ex, ey, 3, 3))
                pygame.draw.rect(surface, (*_NS_kagetsuka.PALETTE["fire_shine"], alpha),
                                 (ex, ey, 1, 1))
    # ============================================================
    # SKILL W - SHARINGAN (red aura)
    # ============================================================
    def _draw_sharingan_skill(surface, boss, x, y, timer, phase):
        """Red aura pulses + big sharingan symbol overlay."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        # Red pulsing aura around boss
        for r in range(50, 5, -3):
            alpha = _NS_kagetsuka._alpha(80 * (50 - r) / 50 * pulse)
            _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["sharingan_dark"], alpha),
                                    (x, y - 5), r)
        for r in range(30, 5, -2):
            alpha = _NS_kagetsuka._alpha(120 * (30 - r) / 30 * pulse)
            _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["sharingan_mid"], alpha),
                                    (x, y - 5), r)
        # Big sharingan symbol above head
        sy = y - 60
        for r in range(18, 0, -1):
            alpha = _NS_kagetsuka._alpha(150 * (18 - r) / 18 * pulse)
            _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["sharingan_dark"], alpha),
                                    (x, sy), r)
        # Central eye
        _NS_kagetsuka._aacircle(surface, _NS_kagetsuka.PALETTE["sharingan_darkest"], (x, sy), 12)
        _NS_kagetsuka._aacircle(surface, _NS_kagetsuka.PALETTE["sharingan_dark"], (x, sy), 10)
        _NS_kagetsuka._aacircle(surface, _NS_kagetsuka.PALETTE["sharingan_mid"], (x, sy), 8)
        _NS_kagetsuka._aacircle(surface, _NS_kagetsuka.PALETTE["sharingan_light"], (x, sy), 4)
        # Three tomoe (comma) rotating
        rotation = phase * 2
        for i in range(3):
            angle = rotation + i * math.pi * 2 / 3
            tx1 = x + int(math.cos(angle) * 6)
            ty1 = sy + int(math.sin(angle) * 6)
            _NS_kagetsuka._aacircle(surface, _NS_kagetsuka.PALETTE["shadow_deep"], (tx1, ty1), 2)
            # Tail of tomoe
            tail_angle = angle + math.pi / 2
            tail_x = tx1 + int(math.cos(tail_angle) * 3)
            tail_y = ty1 + int(math.sin(tail_angle) * 3)
            pygame.draw.line(surface, _NS_kagetsuka.PALETTE["shadow_deep"],
                             (tx1, ty1), (tail_x, tail_y), 2)
        # Center pupil
        _NS_kagetsuka._aacircle(surface, _NS_kagetsuka.PALETTE["shadow"], (x, sy), 2)
        pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["sharingan_glow"], (x, sy, 1, 1))
        # Sparks
        for i in range(8):
            angle = phase * 2 + i * math.pi / 4
            r = 25 + int(math.sin(phase * 3 + i) * 5)
            sx = x + int(math.cos(angle) * r)
            spy = sy + int(math.sin(angle) * r)
            pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["sharingan_light"], (sx, spy, 1, 1))
            pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["sharingan_glow"], (sx, spy, 1, 1))
    # ============================================================
    # SKILL E - SPECTRAL RIBCAGE (partial susanoo)
    # ============================================================
    def _draw_ribcage_skill(surface, boss, x, y, timer, phase):
        """Blue ethereal ribcage armor around boss."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.2 + 0.8
        scale = min(1.0, progress * 3)
        # Ribcage bones
        # Spine (vertical center line)
        spine_top = (x, y - 25)
        spine_bot = (x, y + 8)
        # Draw multi-layer glow for spine
        for w, alpha_val in [(4, 100), (3, 150), (2, 200), (1, 240)]:
            pygame.draw.line(surface,
                             (*_NS_kagetsuka.PALETTE["spec_mid"],
                              _NS_kagetsuka._alpha(alpha_val * pulse * scale)),
                             spine_top, spine_bot, w)
        # RIBS (curved bones on both sides)
        for side in (-1, 1):
            for i in range(5):
                # Rib base position on spine
                rib_y = y - 22 + i * 6
                # Rib curves outward and down
                mid_x = x + side * int(14 * scale)
                mid_y = rib_y + 3
                end_x = x + side * int(8 * scale)
                end_y = rib_y + 8
                # Bezier-like 3-point curve (approximated with line segments)
                num_segs = 5
                prev_pt = (x, rib_y)
                for s in range(1, num_segs + 1):
                    t = s / num_segs
                    # Quadratic bezier
                    bx = int((1 - t) ** 2 * x + 2 * (1 - t) * t * mid_x + t ** 2 * end_x)
                    by = int((1 - t) ** 2 * rib_y + 2 * (1 - t) * t * mid_y + t ** 2 * end_y)
                    for w, alpha_val in [(4, 80), (3, 130), (2, 190), (1, 240)]:
                        a = _NS_kagetsuka._alpha(alpha_val * pulse * scale)
                        colors = [
                            _NS_kagetsuka.PALETTE["spec_dark"],
                            _NS_kagetsuka.PALETTE["spec_mid"],
                            _NS_kagetsuka.PALETTE["spec_light"],
                            _NS_kagetsuka.PALETTE["spec_hot"],
                        ]
                        col = colors[min(w - 1, 3)]
                        pygame.draw.line(surface, (*col, a), prev_pt, (bx, by), w)
                    prev_pt = (bx, by)
        # Skull-like top of ribcage
        skull_y = y - 30
        for r in range(int(8 * scale), 0, -1):
            alpha = _NS_kagetsuka._alpha(180 * (8 - r) / 8 * pulse * scale)
            _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["spec_mid"], alpha),
                                    (x, skull_y), r)
        _NS_kagetsuka._aacircle(surface, _NS_kagetsuka.PALETTE["spec_hot"], (x, skull_y), max(1, int(3 * scale)))
        # Sparkles
        for i in range(10):
            angle = phase * 1.5 + i * math.pi / 5
            r = 20 + int(math.sin(phase * 3 + i) * 5)
            sx = x + int(math.cos(angle) * r)
            sy = y - 10 + int(math.sin(angle) * r * 0.7)
            spa = _NS_kagetsuka._alpha(240 * pulse * scale)
            pygame.draw.rect(surface, (*_NS_kagetsuka.PALETTE["spec_hot"], spa), (sx, sy, 1, 1))
            pygame.draw.rect(surface, (*_NS_kagetsuka.PALETTE["spec_shine"], spa), (sx, sy, 1, 1))
    # ============================================================
    # SKILL R - AVATAR OF WRATH (giant susanoo)
    # ============================================================
    def _draw_avatar_ground(surface, boss, x, y, timer, phase):
        """Ground pulse ring for R."""
        pulse = math.sin(phase * 2) * 0.25 + 0.75
        r = int(70 * pulse)
        pygame.draw.ellipse(surface, (*_NS_kagetsuka.PALETTE["spec_dark"], 200),
                            (x - r, y + 45 - r // 3, r * 2, r * 2 // 3), 3)
        pygame.draw.ellipse(surface, (*_NS_kagetsuka.PALETTE["spec_mid"], 220),
                            (x - r + 3, y + 45 - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 2)
        pygame.draw.ellipse(surface, (*_NS_kagetsuka.PALETTE["spec_light"], 180),
                            (x - r + 8, y + 45 - r // 3 + 4,
                             r * 2 - 16, r * 2 // 3 - 8), 1)
    def _draw_susanoo_avatar(surface, boss, x, y, timer, phase):
        """Giant blue samurai spirit behind boss."""
        duration = 130
        progress = max(0.0, min(1.0, 1 - timer / duration))
        scale = min(1.0, progress * 2)
        facing = boss.direction
        if scale < 0.1:
            return
        pulse = math.sin(phase * 1.5) * 0.15 + 0.85
        # Base alpha for translucent avatar
        base_alpha = _NS_kagetsuka._alpha(200 * pulse * scale)
        # Center of avatar (bigger, above boss)
        acx = x
        acy = y - 60
        # AVATAR BODY (giant humanoid)
        body_h = int(60 * scale)
        body_w = int(30 * scale)
        # Legs area (below boss)
        # Torso (from boss upward)
        torso_top = (acx, acy - body_h // 2)
        torso_bot = (acx, acy + body_h // 2)
        # Draw giant torso as polygon (armored)
        _NS_kagetsuka._poly(surface, (*_NS_kagetsuka.PALETTE["spec_dark"], base_alpha), [
            (acx - body_w, acy - body_h // 3),
            (acx - body_w - 3, acy),
            (acx - body_w + 2, acy + body_h // 3),
            (acx + body_w - 2, acy + body_h // 3),
            (acx + body_w + 3, acy),
            (acx + body_w, acy - body_h // 3),
            (acx + body_w - 5, acy - body_h // 2),
            (acx - body_w + 5, acy - body_h // 2),
        ])
        _NS_kagetsuka._poly(surface, (*_NS_kagetsuka.PALETTE["spec_mid"], base_alpha), [
            (acx - body_w + 3, acy - body_h // 3 + 2),
            (acx - body_w, acy),
            (acx - body_w + 5, acy + body_h // 3 - 3),
            (acx + body_w - 5, acy + body_h // 3 - 3),
            (acx + body_w, acy),
            (acx + body_w - 3, acy - body_h // 3 + 2),
        ])
        # Armor plate lines
        pygame.draw.line(surface, (*_NS_kagetsuka.PALETTE["spec_light"], base_alpha),
                         (acx - body_w // 2, acy - body_h // 4),
                         (acx + body_w // 2, acy - body_h // 4), 2)
        pygame.draw.line(surface, (*_NS_kagetsuka.PALETTE["spec_light"], base_alpha),
                         (acx - body_w // 2, acy + body_h // 6),
                         (acx + body_w // 2, acy + body_h // 6), 2)
        # HEAD (with horns/samurai helm)
        head_y = acy - body_h // 2 - int(15 * scale)
        head_r = int(14 * scale)
        # Head base
        _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["spec_dark"], base_alpha),
                                (acx, head_y), head_r)
        _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["spec_mid"], base_alpha),
                                (acx, head_y), head_r - 2)
        _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["spec_light"], base_alpha),
                                (acx - 3, head_y - 4), max(1, head_r // 3))
        # Horns/wings on helm (samurai crest)
        for side in (-1, 1):
            horn_start = (acx + side * head_r // 2, head_y - head_r // 2)
            horn_tip = (acx + side * int(head_r * 1.5), head_y - int(head_r * 1.5))
            for w, alpha_val in [(3, 150), (2, 200), (1, 255)]:
                pygame.draw.line(surface,
                                 (*_NS_kagetsuka.PALETTE["spec_light"],
                                  _NS_kagetsuka._alpha(alpha_val * pulse * scale)),
                                 horn_start, horn_tip, w)
        # GLOWING EYES on avatar face
        for eye_x in (acx - 4, acx + 4):
            for r in range(4, 0, -1):
                alpha = _NS_kagetsuka._alpha(180 * (4 - r) / 4 * pulse * scale)
                _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["spec_hot"], alpha),
                                        (eye_x, head_y), r)
            pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["spec_shine"], (eye_x, head_y, 1, 1))
            pygame.draw.rect(surface, _NS_kagetsuka.PALETTE["white"], (eye_x, head_y, 1, 1))
        # GIANT SWORD (behind, facing forward)
        sword_base_x = acx + facing * int(body_w * 1.5)
        sword_base_y = acy
        sword_tip_x = sword_base_x + facing * int(80 * scale)
        sword_tip_y = sword_base_y - int(20 * scale)
        # Multi-layer sword beam
        for w, alpha_val in [(10, 60), (8, 100), (6, 150), (4, 200), (2, 240)]:
            pygame.draw.line(surface, (*_NS_kagetsuka.PALETTE["spec_dark"],
                                       _NS_kagetsuka._alpha(alpha_val * pulse * scale)),
                             (sword_base_x, sword_base_y),
                             (sword_tip_x, sword_tip_y), w)
        # Bright core
        pygame.draw.line(surface, (*_NS_kagetsuka.PALETTE["spec_light"],
                                   _NS_kagetsuka._alpha(255 * pulse * scale)),
                         (sword_base_x, sword_base_y),
                         (sword_tip_x, sword_tip_y), 2)
        pygame.draw.line(surface, (*_NS_kagetsuka.PALETTE["spec_shine"],
                                   _NS_kagetsuka._alpha(255 * pulse * scale)),
                         (sword_base_x, sword_base_y),
                         (sword_tip_x, sword_tip_y), 1)
        # Bright tip
        for r in range(int(6 * scale), 0, -1):
            a = _NS_kagetsuka._alpha(200 * (6 - r) / 6 * pulse * scale)
            _NS_kagetsuka._aacircle(surface, (*_NS_kagetsuka.PALETTE["spec_hot"], a),
                                    (sword_tip_x, sword_tip_y), r)
        # Rising energy particles
        for i in range(15):
            t = ((phase * 1.2 + i * 0.08) % 1.0)
            angle = i * math.pi * 2 / 15
            pr = int(body_w * 1.5)
            px = acx + int(math.cos(angle) * pr)
            py = acy - int(t * 40)
            alpha = _NS_kagetsuka._alpha(220 * (1 - t) * scale)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_kagetsuka.PALETTE["spec_hot"], alpha),
                                 (px, py, 2, 2))
                pygame.draw.rect(surface, (*_NS_kagetsuka.PALETTE["spec_shine"], alpha),
                                 (px, py, 1, 1))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_lyrenya(surface, boss, x, y):
    """Entry point lyrenya."""
    return _NS_lyrenya.draw_lyrenya(surface, boss, x, y)


def draw_vyraeth(surface, boss, x, y):
    """Entry point vyraeth."""
    return _NS_vyraeth.draw_vyraeth(surface, boss, x, y)


def draw_zorothrax(surface, boss, x, y):
    """Entry point zorothrax."""
    return _NS_zorothrax.draw_zorothrax(surface, boss, x, y)


def draw_kagetsuka(surface, boss, x, y):
    """Entry point kagetsuka."""
    return _NS_kagetsuka.draw_kagetsuka(surface, boss, x, y)
