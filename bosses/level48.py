"""
bosses/level48.py - Semua boss Level 48

Berisi:
  - broggmar   (mini boss - MELEE caskbreaker, explosive barrel)
  - ursath     (mini boss - RANGED wildcaller, nature beast)
  - zhaeris    (mini boss - MELEE shadowblade, shadow ninja)
  - cogsworth  (TRUE BOSS - RANGED skyfury, steampunk sky machine)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _brg_ (broggmar), _ur_ (ursath), _zhr_ (zhaeris),
    _cog_ (cogsworth) sudah unik.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# BROGGMAR (CASKBREAKER) - Mini Boss
# ====================================================================

class _NS_broggmar:
    """Namespace broggmar - dwarven brewmaster boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin tones (weathered dwarven)
        "skin_darkest": (55, 30, 20),
        "skin_dark": (110, 70, 50),
        "skin_mid": (175, 125, 95),
        "skin_light": (220, 170, 135),
        "skin_shine": (250, 210, 175),
        # Beard/hair (fiery orange-red)
        "hair_darkest": (55, 20, 5),
        "hair_dark": (130, 55, 15),
        "hair_mid": (200, 100, 30),
        "hair_light": (240, 155, 60),
        "hair_shine": (255, 210, 130),
        # Leather armor (dark brown)
        "leather_darkest": (25, 15, 8),
        "leather_dark": (60, 35, 20),
        "leather_mid": (105, 65, 35),
        "leather_light": (155, 105, 65),
        "leather_edge": (200, 150, 100),
        # Wood/cask (medium brown)
        "wood_darkest": (30, 18, 10),
        "wood_dark": (75, 45, 25),
        "wood_mid": (135, 85, 45),
        "wood_light": (185, 130, 80),
        "wood_shine": (225, 175, 120),
        # Metal (dark iron w/ gold trim)
        "iron_dark": (30, 25, 22),
        "iron_mid": (75, 65, 60),
        "iron_light": (140, 130, 120),
        "iron_shine": (200, 195, 185),
        "gold_dark": (95, 65, 15),
        "gold_mid": (180, 130, 40),
        "gold_light": (240, 195, 90),
        "gold_shine": (255, 235, 160),
        # Purple magic (brew energy) - from reference
        "magic_darkest": (25, 10, 40),
        "magic_dark": (70, 30, 110),
        "magic_mid": (140, 65, 190),
        "magic_light": (200, 130, 240),
        "magic_hot": (230, 180, 255),
        "magic_shine": (250, 220, 255),
        # Fire brew (orange-hot)
        "fire_darkest": (50, 15, 5),
        "fire_dark": (140, 45, 15),
        "fire_mid": (220, 100, 30),
        "fire_light": (255, 170, 70),
        "fire_hot": (255, 220, 130),
        "fire_shine": (255, 250, 210),
        # Eye (glowing amber)
        "eye_socket": (15, 8, 4),
        "eye_dark": (80, 40, 10),
        "eye_mid": (200, 130, 35),
        "eye_light": (255, 200, 90),
        "eye_glow": (255, 240, 180),
        # Foam/beer (light cream)
        "foam_dark": (200, 180, 130),
        "foam_mid": (235, 220, 175),
        "foam_light": (255, 245, 215),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_broggmar._clamp(color)
        if _NS_broggmar.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_broggmar._clamp(color)
        if _NS_broggmar.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_broggmar._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_broggmar(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_broggmar._detect_moving(boss)
        _NS_broggmar._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_brg_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind
        _NS_broggmar._draw_magic_aura(surface, x, y, pulse)
        _NS_broggmar._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX
        if active_skill == "q":
            _NS_broggmar._draw_barrelroll_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_broggmar._draw_bodyslam_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_broggmar._draw_explosivecask_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (floating animation)
        if active_skill == "e":
            _NS_broggmar._draw_bodyslam_pose(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_broggmar._draw_attack_pose(surface, boss, x, y)
        elif moving:
            _NS_broggmar._draw_walk_pose(surface, boss, x, y)
        else:
            _NS_broggmar._draw_idle_pose(surface, boss, x, y)
        # W - Drunken Rage aura on body
        if active_skill == "w":
            _NS_broggmar._draw_drunkenrage_aura(surface, boss, x, y, skill_timer, pulse)
        # Foreground FX
        if active_skill == "q":
            _NS_broggmar._draw_barrelroll_projectile(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_broggmar._draw_explosivecask_projectile(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_brg_previous_timer", 0))
        active = bool(getattr(boss, "_brg_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._brg_attack_active = True
            boss._brg_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._brg_attack_frame = int(
                getattr(boss, "_brg_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._brg_attack_active = False
            boss._brg_attack_frame = 0
            active = False
        boss._brg_previous_timer = timer
        boss._brg_attack_progress = (
            min(1.0, getattr(boss, "_brg_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_brg_last_x"):
            boss._brg_last_x = boss.x
            boss._brg_last_y = boss.y
            return False
        dx = abs(boss.x - boss._brg_last_x)
        dy = abs(boss.y - boss._brg_last_y)
        boss._brg_last_x = boss.x
        boss._brg_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS (floating animation)
    # ============================================================
    def _draw_idle_pose(surface, boss, x, y):
        # Slow floating bob
        bob = int(math.sin(boss.pulse * 0.7) * 5)
        _NS_broggmar._draw_shadow(surface, x, y + 50)
        _NS_broggmar._draw_float_wisps(surface, x, y + 44, boss.pulse)
        _NS_broggmar._draw_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")
    def _draw_walk_pose(surface, boss, x, y):
        # Faster floating with slight sway (floating movement)
        phase = boss.pulse * 1.4
        bob = int(math.sin(phase * 1.2) * 6)
        sway = int(math.sin(phase * 0.8) * 3)
        _NS_broggmar._draw_shadow(surface, x + sway, y + 50)
        _NS_broggmar._draw_float_wisps(surface, x + sway, y + 44, phase, trail=True,
                                       facing=boss.direction)
        _NS_broggmar._draw_body(surface, x + sway, y + bob, boss.direction, phase, "walk")
    def _draw_attack_pose(surface, boss, x, y):
        # Melee swing animation (basic attack = barrel swing)
        progress = getattr(boss, "_brg_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Wind-up (raise barrel) → swing forward → recovery
        if progress < 0.4:
            t = progress / 0.4
            lunge = -int(t * 5) * boss.direction
            lift = int(t * 6)
        elif progress < 0.65:
            t = (progress - 0.4) / 0.25
            lunge = int((-5 + t * 16)) * boss.direction
            lift = int(6 - t * 8)
        else:
            t = (progress - 0.65) / 0.35
            lunge = int(11 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        bob = int(math.sin(boss.pulse * 0.7) * 3)
        _NS_broggmar._draw_shadow(surface, x + lunge, y + 50)
        _NS_broggmar._draw_float_wisps(surface, x + lunge, y + 44, boss.pulse, intense=True)
        # Draw swing trail BEFORE body (behind)
        _NS_broggmar._draw_swing_trail(surface, boss, x + lunge, y - lift + bob,
                                        boss.direction, progress)
        _NS_broggmar._draw_body(surface, x + lunge, y - lift + bob, boss.direction,
                                boss.pulse, "attack", progress)
        # Draw impact spark at peak (over body)
        _NS_broggmar._draw_swing_impact(surface, boss, x + lunge, y - lift + bob,
                                         boss.direction, progress)
    def _draw_bodyslam_pose(surface, boss, x, y, timer, pulse):
        """E skill pose - crouching then slam."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            # Charging - lean forward
            t = progress / 0.5
            lunge = int(t * 18) * boss.direction
            lift = int(t * 3)
        else:
            # Slam - impact
            t = (progress - 0.5) / 0.5
            lunge = int(18 * (1 - t * 0.5)) * boss.direction
            lift = int(-3 + t * 3)
        _NS_broggmar._draw_shadow(surface, x + lunge, y + 50)
        _NS_broggmar._draw_float_wisps(surface, x + lunge, y + 44, pulse, intense=True)
        _NS_broggmar._draw_body(surface, x + lunge, y - lift, boss.direction, pulse,
                                "slam", progress)
    # ============================================================
    # BODY - Dwarven brewmaster with belly, beard, barrel
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, progress=0):
        """Draw dwarf body: legs, torso, arms with barrel, head with beard."""
        # Order: legs -> body/belly -> back arm -> head/beard -> front arm+barrel
        _NS_broggmar._draw_legs(surface, cx, cy, facing, phase, action)
        _NS_broggmar._draw_torso(surface, cx, cy, facing, phase)
        _NS_broggmar._draw_back_arm(surface, cx, cy, facing, phase, action, progress)
        _NS_broggmar._draw_head(surface, cx, cy, facing, phase, action)
        _NS_broggmar._draw_beard(surface, cx, cy, facing, phase)
        _NS_broggmar._draw_front_arm_barrel(surface, cx, cy, facing, phase, action,
                                            progress)
    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Short thick dwarven legs (dangling since floating)."""
        # Legs dangle since character floats
        leg_sway = math.sin(phase * 1.2) * 2 if action == "walk" else \
                   math.sin(phase * 0.5) * 1
        for side_i, side in enumerate([-1, 1]):
            lx = cx + side * 6
            ly = cy + 20
            sway = int(leg_sway * (1 if side > 0 else -1))
            # Boot/leg shape
            leg_pts = [
                (lx - 5, ly - 2),
                (lx + 5, ly - 2),
                (lx + 6 + sway, ly + 4),
                (lx + 8 + sway, ly + 10),
                (lx + 4 + sway, ly + 12),
                (lx - 4 + sway, ly + 12),
                (lx - 6 + sway, ly + 10),
                (lx - 4 + sway, ly + 4),
            ]
            _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["shadow_deep"],
                               [(px + 1, py + 2) for px, py in leg_pts])
            _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["leather_darkest"], leg_pts)
            # Pant (upper)
            _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["leather_dark"], [
                (lx - 4, ly - 1),
                (lx + 4, ly - 1),
                (lx + 5 + sway, ly + 4),
                (lx - 5 + sway, ly + 4),
            ])
            _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["leather_mid"], [
                (lx - 3, ly),
                (lx + 3, ly),
                (lx + 3 + sway, ly + 3),
                (lx - 3 + sway, ly + 3),
            ])
            # Boot (lower)
            _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["leather_darkest"], [
                (lx - 5 + sway, ly + 5),
                (lx + 5 + sway, ly + 5),
                (lx + 7 + sway, ly + 10),
                (lx + 4 + sway, ly + 12),
                (lx - 4 + sway, ly + 12),
                (lx - 7 + sway, ly + 10),
            ])
            _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["leather_dark"], [
                (lx - 4 + sway, ly + 6),
                (lx + 4 + sway, ly + 6),
                (lx + 6 + sway, ly + 10),
                (lx - 6 + sway, ly + 10),
            ])
            # Highlight on boot
            pygame.draw.rect(surface, _NS_broggmar.PALETTE["leather_edge"],
                             (lx - 2 + sway, ly + 7, 2, 1))
            # Gold buckle
            pygame.draw.rect(surface, _NS_broggmar.PALETTE["gold_dark"],
                             (lx - 2 + sway, ly + 8, 4, 2))
            pygame.draw.rect(surface, _NS_broggmar.PALETTE["gold_mid"],
                             (lx - 1 + sway, ly + 8, 2, 1))
            pygame.draw.rect(surface, _NS_broggmar.PALETTE["gold_shine"],
                             (lx - 1 + sway, ly + 8, 1, 1))
    def _draw_torso(surface, cx, cy, facing, phase):
        """Large round dwarven belly + shoulders."""
        breath = math.sin(phase * 0.6) * 1
        # Big belly (large round shape)
        belly_pts = [
            (cx - 18, cy),
            (cx - 20, cy + 6),
            (cx - 18, cy + 14),
            (cx - 12, cy + 20),
            (cx - 4, cy + 22),
            (cx + 6, cy + 22),
            (cx + 14, cy + 20),
            (cx + 20, cy + 14),
            (cx + 22, cy + 6),
            (cx + 20, cy),
            (cx + 15, cy - 5),
            (cx + 6, cy - 8),
            (cx - 6, cy - 8),
            (cx - 15, cy - 5),
        ]
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["shadow_deep"],
                           [(px + 2, py + 3) for px, py in belly_pts])
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["skin_darkest"], belly_pts)
        # Skin main
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["skin_dark"], [
            (cx - 17, cy + 1),
            (cx - 19, cy + 7),
            (cx - 16, cy + 14),
            (cx - 10, cy + 19),
            (cx - 2, cy + 20),
            (cx + 8, cy + 20),
            (cx + 15, cy + 18),
            (cx + 19, cy + 12),
            (cx + 20, cy + 6),
            (cx + 18, cy),
            (cx + 12, cy - 4),
            (cx - 12, cy - 4),
        ])
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["skin_mid"], [
            (cx - 14, cy + 3),
            (cx - 15, cy + 9),
            (cx - 10, cy + 15),
            (cx + 2, cy + 17),
            (cx + 12, cy + 15),
            (cx + 16, cy + 9),
            (cx + 15, cy + 3),
            (cx + 8, cy - 2),
            (cx - 8, cy - 2),
        ])
        # Belly highlight
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["skin_light"], [
            (cx - 6, cy + 6),
            (cx + 2, cy + 5),
            (cx + 8, cy + 8),
            (cx + 4, cy + 13),
            (cx - 4, cy + 12),
        ])
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["skin_shine"],
                         (cx - 2, cy + 7, 3, 2))
        # Navel
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["skin_darkest"], (cx, cy + 10, 2, 2))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["shadow_deep"], (cx, cy + 11, 1, 1))
        # Leather strap across chest (diagonal)
        strap_pts = [
            (cx - 16, cy - 3),
            (cx + 14, cy + 4),
            (cx + 14, cy + 7),
            (cx - 16, cy),
        ]
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["leather_darkest"], strap_pts)
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["leather_dark"], [
            (cx - 15, cy - 2),
            (cx + 13, cy + 5),
            (cx + 13, cy + 6),
            (cx - 15, cy - 1),
        ])
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["leather_mid"], [
            (cx - 14, cy - 2),
            (cx + 12, cy + 5),
            (cx + 12, cy + 5),
            (cx - 14, cy - 2),
        ])
        # Belt (bottom)
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["leather_darkest"],
                         (cx - 18, cy + 15, 40, 5))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["leather_dark"],
                         (cx - 17, cy + 16, 38, 3))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["leather_mid"],
                         (cx - 17, cy + 16, 38, 1))
        # Belt buckle (gold)
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["gold_dark"],
                         (cx - 5, cy + 14, 10, 7))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["gold_mid"],
                         (cx - 4, cy + 15, 8, 5))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["gold_light"],
                         (cx - 3, cy + 15, 6, 3))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["gold_shine"],
                         (cx - 2, cy + 16, 3, 1))
        # Gemstone in buckle
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["magic_dark"],
                         (cx - 1, cy + 17, 2, 2))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["magic_light"],
                         (cx - 1, cy + 17, 1, 1))
        # Metal studs on belt
        for i in range(-4, 5):
            if i == 0:
                continue
            stud_x = cx + i * 4
            pygame.draw.rect(surface, _NS_broggmar.PALETTE["iron_dark"],
                             (stud_x, cy + 17, 2, 2))
            pygame.draw.rect(surface, _NS_broggmar.PALETTE["iron_light"],
                             (stud_x, cy + 17, 1, 1))
    def _draw_back_arm(surface, cx, cy, facing, phase, action, progress):
        """Back arm (opposite of facing)."""
        back = -facing
        shoulder_x = cx + back * 14
        shoulder_y = cy - 4
        sway = math.sin(phase * 0.8) * 2
        # Bicep
        elbow_x = shoulder_x + back * 8
        elbow_y = shoulder_y + 8 + int(sway)
        hand_x = elbow_x + back * 2
        hand_y = elbow_y + 10
        _NS_broggmar._aaline(surface, _NS_broggmar.PALETTE["shadow_deep"],
                             (shoulder_x + 1, shoulder_y + 2),
                             (elbow_x + 1, elbow_y + 2), 10)
        _NS_broggmar._aaline(surface, _NS_broggmar.PALETTE["skin_darkest"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 9)
        _NS_broggmar._aaline(surface, _NS_broggmar.PALETTE["skin_dark"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 7)
        _NS_broggmar._aaline(surface, _NS_broggmar.PALETTE["skin_mid"],
                             (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 4)
        # Forearm
        _NS_broggmar._aaline(surface, _NS_broggmar.PALETTE["shadow_deep"],
                             (elbow_x + 1, elbow_y + 2),
                             (hand_x + 1, hand_y + 2), 8)
        _NS_broggmar._aaline(surface, _NS_broggmar.PALETTE["skin_darkest"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 7)
        _NS_broggmar._aaline(surface, _NS_broggmar.PALETTE["skin_dark"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_broggmar._aaline(surface, _NS_broggmar.PALETTE["skin_mid"],
                             (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 3)
        # Fist
        _NS_broggmar._aacircle(surface, _NS_broggmar.PALETTE["shadow_deep"],
                               (hand_x + 1, hand_y + 1), 5)
        _NS_broggmar._aacircle(surface, _NS_broggmar.PALETTE["skin_darkest"],
                               (hand_x, hand_y), 5)
        _NS_broggmar._aacircle(surface, _NS_broggmar.PALETTE["skin_dark"],
                               (hand_x, hand_y), 4)
        _NS_broggmar._aacircle(surface, _NS_broggmar.PALETTE["skin_mid"],
                               (hand_x - 1, hand_y - 1), 3)
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["skin_light"],
                         (hand_x - 1, hand_y - 1, 2, 1))
        # Wristband
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["leather_darkest"],
                         (elbow_x - 3, elbow_y + 6, 6, 4))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["leather_dark"],
                         (elbow_x - 3, elbow_y + 7, 6, 2))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["gold_dark"],
                         (elbow_x - 1, elbow_y + 7, 2, 2))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["gold_light"],
                         (elbow_x - 1, elbow_y + 7, 1, 1))
    def _draw_front_arm_barrel(surface, cx, cy, facing, phase, action, progress):
        """Front arm holding a barrel (swings during attack)."""
        # Arm angle changes during attack
        base_angle = -math.pi / 4  # holds barrel high
        if action == "attack":
            if progress < 0.4:
                # Wind-up: raise up
                t = progress / 0.4
                base_angle = -math.pi / 4 - t * math.pi / 3
            elif progress < 0.65:
                # Swing forward
                t = (progress - 0.4) / 0.25
                base_angle = -math.pi / 2 - math.pi / 12 + t * (math.pi * 0.9)
            else:
                # Recovery
                t = (progress - 0.65) / 0.35
                base_angle = math.pi / 3 - t * (math.pi / 3 + math.pi / 4)
        elif action == "slam":
            # E skill - both hands raised then slam
            if progress < 0.5:
                t = progress / 0.5
                base_angle = -math.pi / 4 - t * math.pi / 2
            else:
                t = (progress - 0.5) / 0.5
                base_angle = -math.pi * 0.75 + t * math.pi
        else:
            # Idle sway
            base_angle += math.sin(phase * 0.6) * 0.1
        shoulder_x = cx + facing * 14
        shoulder_y = cy - 4
        # Arm length
        arm_len = 22
        hand_x = shoulder_x + int(math.cos(base_angle) * arm_len) * facing
        hand_y = shoulder_y + int(math.sin(base_angle) * arm_len)
        elbow_x = shoulder_x + int(math.cos(base_angle) * arm_len * 0.5) * facing
        elbow_y = shoulder_y + int(math.sin(base_angle) * arm_len * 0.5) + 2
        # Upper arm
        _NS_broggmar._aaline(surface, _NS_broggmar.PALETTE["shadow_deep"],
                             (shoulder_x + 1, shoulder_y + 2),
                             (elbow_x + 1, elbow_y + 2), 11)
        _NS_broggmar._aaline(surface, _NS_broggmar.PALETTE["skin_darkest"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 10)
        _NS_broggmar._aaline(surface, _NS_broggmar.PALETTE["skin_dark"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 8)
        _NS_broggmar._aaline(surface, _NS_broggmar.PALETTE["skin_mid"],
                             (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 5)
        _NS_broggmar._aaline(surface, _NS_broggmar.PALETTE["skin_light"],
                             (shoulder_x, shoulder_y - 2), (elbow_x, elbow_y - 2), 2)
        # Forearm
        _NS_broggmar._aaline(surface, _NS_broggmar.PALETTE["shadow_deep"],
                             (elbow_x + 1, elbow_y + 2),
                             (hand_x + 1, hand_y + 2), 9)
        _NS_broggmar._aaline(surface, _NS_broggmar.PALETTE["skin_darkest"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 8)
        _NS_broggmar._aaline(surface, _NS_broggmar.PALETTE["skin_dark"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 6)
        _NS_broggmar._aaline(surface, _NS_broggmar.PALETTE["skin_mid"],
                             (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 3)
        # Wristband
        wrist_off_x = int(math.cos(base_angle) * -3) * facing
        wrist_off_y = int(math.sin(base_angle) * -3)
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["leather_darkest"],
                         (hand_x + wrist_off_x - 3, hand_y + wrist_off_y - 2, 6, 4))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["leather_dark"],
                         (hand_x + wrist_off_x - 3, hand_y + wrist_off_y - 1, 6, 2))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["gold_dark"],
                         (hand_x + wrist_off_x - 1, hand_y + wrist_off_y - 1, 2, 2))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["gold_mid"],
                         (hand_x + wrist_off_x - 1, hand_y + wrist_off_y - 1, 1, 1))
        # BARREL held in hand
        _NS_broggmar._draw_barrel(surface, hand_x, hand_y, facing, phase, base_angle,
                                   action)
    # ============================================================
    # SWING TRAIL FX
    # ============================================================
    def _get_barrel_position(cx, cy, facing, progress):
        """Calculate barrel position at given attack progress."""
        # Same logic as _draw_front_arm_barrel to match arm angle
        if progress < 0.4:
            t = progress / 0.4
            base_angle = -math.pi / 4 - t * math.pi / 3
        elif progress < 0.65:
            t = (progress - 0.4) / 0.25
            base_angle = -math.pi / 2 - math.pi / 12 + t * (math.pi * 0.9)
        else:
            t = (progress - 0.65) / 0.35
            base_angle = math.pi / 3 - t * (math.pi / 3 + math.pi / 4)
        shoulder_x = cx + facing * 14
        shoulder_y = cy - 4
        arm_len = 22
        hand_x = shoulder_x + int(math.cos(base_angle) * arm_len) * facing
        hand_y = shoulder_y + int(math.sin(base_angle) * arm_len)
        # Barrel offset from hand
        offset_x = int(math.cos(base_angle) * 8) * facing
        offset_y = int(math.sin(base_angle) * 8) - 3
        bx = hand_x + offset_x
        by = hand_y + offset_y
        return bx, by, base_angle
    def _draw_swing_trail(surface, boss, cx, cy, facing, progress):
        """Draw arc swing trail following barrel motion."""
        # Only show trail during swing motion (0.35 to 0.75)
        if progress < 0.35 or progress > 0.8:
            return
        # Compute trail intensity based on swing phase
        if progress < 0.4:
            # Pre-swing: minimal trail
            intensity = (progress - 0.35) / 0.05
        elif progress < 0.65:
            # Full swing: maximum trail
            intensity = 1.0
        else:
            # Recovery: fading
            intensity = max(0, 1 - (progress - 0.65) / 0.15)
        intensity = max(0.0, min(1.0, intensity))
        if intensity <= 0:
            return
        # Sample 12 positions along the swing arc (past → current)
        num_samples = 12
        trail_points = []
        for i in range(num_samples):
            # Sample from earlier progress to now
            sample_progress = progress - (i / num_samples) * 0.25
            if sample_progress < 0.35:
                continue
            bx, by, angle = _NS_broggmar._get_barrel_position(
                cx, cy, facing, sample_progress
            )
            trail_points.append((bx, by, angle, i))
        if len(trail_points) < 2:
            return
        # Draw arc as layered wide strokes (from oldest to newest)
        # Reverse so newer draws over older
        trail_points.reverse()
        # Create alpha surface for the trail
        trail_surf = pygame.Surface((260, 260), pygame.SRCALPHA)
        offset_x = cx - 130
        offset_y = cy - 130
        # Layer 1: Wide outer glow (dark purple, biggest)
        for i in range(len(trail_points) - 1):
            p1 = trail_points[i]
            p2 = trail_points[i + 1]
            fade = 1.0 - (p1[3] / num_samples)
            alpha = _NS_broggmar._alpha(120 * fade * intensity)
            if alpha <= 0:
                continue
            thickness = max(2, int(14 * fade))
            pygame.draw.line(
                trail_surf,
                (*_NS_broggmar.PALETTE["magic_darkest"], alpha),
                (p1[0] - offset_x, p1[1] - offset_y),
                (p2[0] - offset_x, p2[1] - offset_y),
                thickness,
            )
        # Layer 2: Mid layer (purple)
        for i in range(len(trail_points) - 1):
            p1 = trail_points[i]
            p2 = trail_points[i + 1]
            fade = 1.0 - (p1[3] / num_samples)
            alpha = _NS_broggmar._alpha(170 * fade * intensity)
            if alpha <= 0:
                continue
            thickness = max(2, int(10 * fade))
            pygame.draw.line(
                trail_surf,
                (*_NS_broggmar.PALETTE["magic_dark"], alpha),
                (p1[0] - offset_x, p1[1] - offset_y),
                (p2[0] - offset_x, p2[1] - offset_y),
                thickness,
            )
        # Layer 3: Bright mid (bright purple)
        for i in range(len(trail_points) - 1):
            p1 = trail_points[i]
            p2 = trail_points[i + 1]
            fade = 1.0 - (p1[3] / num_samples)
            alpha = _NS_broggmar._alpha(210 * fade * intensity)
            if alpha <= 0:
                continue
            thickness = max(1, int(6 * fade))
            pygame.draw.line(
                trail_surf,
                (*_NS_broggmar.PALETTE["magic_mid"], alpha),
                (p1[0] - offset_x, p1[1] - offset_y),
                (p2[0] - offset_x, p2[1] - offset_y),
                thickness,
            )
        # Layer 4: Hot core (light purple → white)
        for i in range(len(trail_points) - 1):
            p1 = trail_points[i]
            p2 = trail_points[i + 1]
            fade = 1.0 - (p1[3] / num_samples)
            alpha = _NS_broggmar._alpha(240 * fade * intensity)
            if alpha <= 0:
                continue
            thickness = max(1, int(3 * fade))
            pygame.draw.line(
                trail_surf,
                (*_NS_broggmar.PALETTE["magic_light"], alpha),
                (p1[0] - offset_x, p1[1] - offset_y),
                (p2[0] - offset_x, p2[1] - offset_y),
                thickness,
            )
        # Layer 5: Bright core line (hot white-ish)
        for i in range(len(trail_points) - 1):
            p1 = trail_points[i]
            p2 = trail_points[i + 1]
            fade = 1.0 - (p1[3] / num_samples)
            alpha = _NS_broggmar._alpha(255 * fade * intensity)
            if alpha <= 0:
                continue
            pygame.draw.line(
                trail_surf,
                (*_NS_broggmar.PALETTE["magic_hot"], alpha),
                (p1[0] - offset_x, p1[1] - offset_y),
                (p2[0] - offset_x, p2[1] - offset_y),
                1,
            )
        # Sparkles along trail
        for i, (bx, by, angle, idx) in enumerate(trail_points):
            fade = 1.0 - (idx / num_samples)
            alpha = _NS_broggmar._alpha(240 * fade * intensity)
            if alpha <= 0 or i % 2 == 0:
                continue
            # Sparks perpendicular to swing direction
            perp = angle + math.pi / 2
            for spark_i in range(2):
                dist = 4 + spark_i * 3
                sign = 1 if spark_i == 0 else -1
                sx = bx - offset_x + int(math.cos(perp) * dist * sign)
                sy = by - offset_y + int(math.sin(perp) * dist * sign)
                pygame.draw.rect(
                    trail_surf,
                    (*_NS_broggmar.PALETTE["magic_hot"], alpha),
                    (sx, sy, 2, 2),
                )
                pygame.draw.rect(
                    trail_surf,
                    (*_NS_broggmar.PALETTE["magic_shine"], alpha),
                    (sx, sy, 1, 1),
                )
            # Small trailing sparks (scattered)
            for spark_i in range(3):
                spark_angle = angle + math.pi / 2 + (spark_i - 1) * 0.5
                dist = 6 + spark_i * 2
                sx = bx - offset_x + int(math.cos(spark_angle) * dist)
                sy = by - offset_y + int(math.sin(spark_angle) * dist)
                pygame.draw.rect(
                    trail_surf,
                    (*_NS_broggmar.PALETTE["magic_light"], alpha),
                    (sx, sy, 1, 1),
                )
        surface.blit(trail_surf, (offset_x, offset_y))
        # Extra: leading edge glow (at current barrel position)
        if trail_points:
            lead = trail_points[0]
            for r in range(10, 2, -2):
                a = _NS_broggmar._alpha(150 * (10 - r) / 10 * intensity)
                _NS_broggmar._aacircle(
                    surface,
                    (*_NS_broggmar.PALETTE["magic_mid"], a),
                    (lead[0], lead[1]),
                    r,
                )
            _NS_broggmar._aacircle(
                surface, _NS_broggmar.PALETTE["magic_hot"],
                (lead[0], lead[1]), 3
            )
            _NS_broggmar._aacircle(
                surface, _NS_broggmar.PALETTE["magic_shine"],
                (lead[0], lead[1]), 1
            )
    def _draw_swing_impact(surface, boss, cx, cy, facing, progress):
        """Impact burst at swing peak (front of arc)."""
        # Show impact burst near end of swing (0.6 to 0.72)
        if progress < 0.6 or progress > 0.72:
            return
        t = (progress - 0.6) / 0.12
        intensity = math.sin(t * math.pi)
        # Impact position (in front of body, where barrel would hit)
        bx, by, _ = _NS_broggmar._get_barrel_position(cx, cy, facing, progress)
        impact_x = bx + int(facing * 6)
        impact_y = by
        # Radial burst
        r = int(4 + t * 14)
        alpha = _NS_broggmar._alpha(240 * intensity)
        for ring_r in range(r + 4, 0, -2):
            a = _NS_broggmar._alpha(alpha * (r + 4 - ring_r) / (r + 4))
            _NS_broggmar._aacircle(
                surface,
                (*_NS_broggmar.PALETTE["magic_dark"], a),
                (impact_x, impact_y),
                ring_r,
            )
        _NS_broggmar._aacircle(
            surface, (*_NS_broggmar.PALETTE["magic_mid"], alpha),
            (impact_x, impact_y), max(2, r - 3)
        )
        _NS_broggmar._aacircle(
            surface, (*_NS_broggmar.PALETTE["magic_light"], alpha),
            (impact_x, impact_y), max(1, r - 6)
        )
        _NS_broggmar._aacircle(
            surface, (*_NS_broggmar.PALETTE["magic_hot"], alpha),
            (impact_x, impact_y), max(1, r - 9)
        )
        pygame.draw.rect(
            surface, (*_NS_broggmar.PALETTE["white"], alpha),
            (impact_x, impact_y, 1, 1)
        )
        # Radial spark lines
        for i in range(8):
            angle_s = i * math.pi / 4 + progress * 4
            ex = impact_x + int(math.cos(angle_s) * r)
            ey = impact_y + int(math.sin(angle_s) * r)
            pygame.draw.line(
                surface,
                (*_NS_broggmar.PALETTE["magic_hot"], alpha),
                (impact_x, impact_y),
                (ex, ey),
                2,
            )
            pygame.draw.rect(
                surface,
                (*_NS_broggmar.PALETTE["magic_shine"], alpha),
                (ex, ey, 2, 2),
            )
        # Extra particles flying outward
        for i in range(6):
            angle_p = i * math.pi / 3 + t * 3
            dist = int(r * 1.3)
            px = impact_x + int(math.cos(angle_p) * dist)
            py = impact_y + int(math.sin(angle_p) * dist)
            pygame.draw.rect(
                surface,
                (*_NS_broggmar.PALETTE["magic_light"], alpha),
                (px, py, 2, 2),
            )
            pygame.draw.rect(
                surface,
                (*_NS_broggmar.PALETTE["magic_hot"], alpha),
                (px, py, 1, 1),
            )
    def _draw_barrel(surface, hx, hy, facing, phase, arm_angle, action):
        """Wooden barrel (mug/cask) held by dwarf."""
        # Barrel position offset from hand
        offset_x = int(math.cos(arm_angle) * 8) * facing
        offset_y = int(math.sin(arm_angle) * 8) - 3
        bx = hx + offset_x
        by = hy + offset_y
        # Barrel size (bigger since it's the signature weapon)
        bw = 16
        bh = 20
        # Rotate barrel with arm swing during attack
        rotation = arm_angle + math.pi / 2 if action in ("attack", "slam") else 0
        # Barrel body (main shape - oval sides)
        # We draw as vertical oval for simplicity
        barrel_pts = [
            (bx - bw // 2, by - bh // 2 + 2),
            (bx - bw // 2 + 1, by - bh // 2),
            (bx + bw // 2 - 1, by - bh // 2),
            (bx + bw // 2, by - bh // 2 + 2),
            (bx + bw // 2 + 1, by),
            (bx + bw // 2, by + bh // 2 - 2),
            (bx + bw // 2 - 1, by + bh // 2),
            (bx - bw // 2 + 1, by + bh // 2),
            (bx - bw // 2, by + bh // 2 - 2),
            (bx - bw // 2 - 1, by),
        ]
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in barrel_pts])
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["wood_darkest"], barrel_pts)
        # Wood main
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["wood_dark"], [
            (bx - bw // 2 + 1, by - bh // 2 + 2),
            (bx + bw // 2 - 1, by - bh // 2 + 2),
            (bx + bw // 2, by),
            (bx + bw // 2 - 1, by + bh // 2 - 2),
            (bx - bw // 2 + 1, by + bh // 2 - 2),
            (bx - bw // 2, by),
        ])
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["wood_mid"], [
            (bx - bw // 2 + 2, by - bh // 2 + 3),
            (bx + bw // 2 - 2, by - bh // 2 + 3),
            (bx + bw // 2 - 1, by),
            (bx + bw // 2 - 2, by + bh // 2 - 3),
            (bx - bw // 2 + 2, by + bh // 2 - 3),
            (bx - bw // 2 + 1, by),
        ])
        # Wood planks (vertical lines)
        for i, off in enumerate((-4, -1, 3)):
            plank_x = bx + off
            pygame.draw.line(surface, _NS_broggmar.PALETTE["wood_darkest"],
                             (plank_x, by - bh // 2 + 3),
                             (plank_x, by + bh // 2 - 3), 1)
        # Wood highlight
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["wood_light"], [
            (bx - 4, by - bh // 2 + 4),
            (bx - 2, by - bh // 2 + 4),
            (bx - 2, by + bh // 2 - 4),
            (bx - 4, by + bh // 2 - 4),
        ])
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["wood_shine"],
                         (bx - 3, by - bh // 2 + 5, 1, 3))
        # Metal bands (iron rings around barrel)
        for band_y_off in (-bh // 2 + 3, -2, bh // 2 - 4):
            band_y = by + band_y_off
            pygame.draw.rect(surface, _NS_broggmar.PALETTE["iron_dark"],
                             (bx - bw // 2 - 1, band_y, bw + 2, 2))
            pygame.draw.rect(surface, _NS_broggmar.PALETTE["iron_mid"],
                             (bx - bw // 2, band_y, bw, 2))
            pygame.draw.rect(surface, _NS_broggmar.PALETTE["iron_light"],
                             (bx - bw // 2, band_y, bw, 1))
            # Rivet
            pygame.draw.rect(surface, _NS_broggmar.PALETTE["iron_shine"],
                             (bx - 3, band_y, 1, 1))
        # Magic glow from top (brewing liquid)
        glow_y = by - bh // 2 + 1
        for r in range(5, 0, -1):
            alpha = _NS_broggmar._alpha(150 * (5 - r) / 5)
            _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_light"], alpha),
                                   (bx, glow_y), r)
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["magic_hot"],
                         (bx, glow_y, 1, 1))
        # Small magic bubbles floating from top
        for i in range(3):
            bub_t = (phase * 0.8 + i * 0.33) % 1.0
            bub_x = bx + int(math.sin(phase + i) * 3)
            bub_y = glow_y - int(bub_t * 8)
            alpha = _NS_broggmar._alpha(220 * (1 - bub_t))
            pygame.draw.rect(surface, (*_NS_broggmar.PALETTE["magic_mid"], alpha),
                             (bub_x, bub_y, 2, 2))
            pygame.draw.rect(surface, (*_NS_broggmar.PALETTE["magic_light"], alpha),
                             (bub_x, bub_y, 1, 1))
    def _draw_head(surface, cx, cy, facing, phase, action, base_angle=0):
        """Bald dwarven head with big nose."""
        hx = cx + facing * 3
        hy = cy - 16
        # Head shape (round-ish, bit forward)
        head_pts = [
            (hx - 8, hy + 4),
            (hx - 9, hy - 2),
            (hx - 7, hy - 7),
            (hx - 2, hy - 9),
            (hx + 4, hy - 8),
            (hx + 8, hy - 4),
            (hx + 9, hy + 1),
            (hx + 8, hy + 5),
            (hx + 4, hy + 7),
            (hx - 2, hy + 7),
            (hx - 6, hy + 6),
        ]
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in head_pts])
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["skin_darkest"], head_pts)
        # Face main
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["skin_dark"], [
            (hx - 7, hy + 3),
            (hx - 8, hy - 1),
            (hx - 6, hy - 6),
            (hx - 1, hy - 8),
            (hx + 3, hy - 7),
            (hx + 7, hy - 3),
            (hx + 8, hy + 1),
            (hx + 7, hy + 4),
            (hx + 3, hy + 6),
            (hx - 1, hy + 6),
            (hx - 5, hy + 5),
        ])
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["skin_mid"], [
            (hx - 5, hy - 3),
            (hx - 3, hy - 6),
            (hx + 2, hy - 6),
            (hx + 5, hy - 3),
            (hx + 6, hy + 1),
            (hx + 4, hy + 4),
            (hx - 2, hy + 4),
            (hx - 5, hy + 1),
        ])
        # Forehead highlight
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["skin_light"], [
            (hx - 2, hy - 5),
            (hx + 2, hy - 5),
            (hx + 3, hy - 3),
            (hx - 3, hy - 3),
        ])
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["skin_shine"],
                         (hx, hy - 5, 2, 1))
        # BIG DWARVEN NOSE (bulbous)
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["skin_darkest"], [
            (hx + facing * 2, hy - 1),
            (hx + facing * 6, hy - 1),
            (hx + facing * 7, hy + 2),
            (hx + facing * 6, hy + 4),
            (hx + facing * 3, hy + 4),
            (hx + facing * 2, hy + 2),
        ])
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["skin_dark"], [
            (hx + facing * 3, hy),
            (hx + facing * 6, hy),
            (hx + facing * 6, hy + 3),
            (hx + facing * 4, hy + 3),
        ])
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["skin_mid"], [
            (hx + facing * 4, hy + 1),
            (hx + facing * 5, hy + 1),
            (hx + facing * 5, hy + 3),
        ])
        # Nose highlight
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["skin_light"],
                         (hx + facing * 4, hy + 1, 1, 1))
        # Red drunken tint
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["fire_dark"],
                         (hx + facing * 5, hy + 3, 1, 1))
        # EYE (glowing amber)
        _NS_broggmar._draw_dwarf_eye(surface, hx - facing * 2, hy - 2, facing, phase)
        # Cheek red (drunken)
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["fire_dark"],
                         (hx - facing * 5, hy + 2, 2, 1))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["fire_mid"],
                         (hx - facing * 5, hy + 2, 1, 1))
        # Bald head shine (top)
        for i, off_x in enumerate((-2, 0, 2)):
            pygame.draw.rect(surface, _NS_broggmar.PALETTE["skin_light"],
                             (hx + off_x, hy - 7, 1, 1))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["skin_shine"],
                         (hx, hy - 8, 2, 1))
        # Small ear
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["skin_darkest"],
                         (hx - facing * 8, hy - 1, 2, 3))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["skin_dark"],
                         (hx - facing * 8, hy, 1, 2))
    def _draw_dwarf_eye(surface, ex, ey, facing, phase):
        """Glowing amber eye."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Deep socket
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["shadow_deep"],
                         (ex - 2, ey - 1, 4, 3))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["eye_socket"],
                         (ex - 1, ey - 1, 3, 3))
        # Glow halo
        for radius in range(5, 0, -1):
            alpha = _NS_broggmar._alpha(80 * (5 - radius) / 5 * pulse)
            _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["eye_mid"], alpha),
                                   (ex, ey), radius)
        # Iris
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["eye_dark"], (ex - 1, ey, 3, 2))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["eye_mid"], (ex, ey, 2, 2))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["eye_light"], (ex, ey, 1, 1))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["eye_glow"], (ex + 1, ey, 1, 1))
        # Bushy eyebrow (orange)
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["hair_darkest"],
                         (ex - 2, ey - 3, 5, 1))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["hair_dark"],
                         (ex - 2, ey - 3, 4, 1))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["hair_mid"],
                         (ex - 1, ey - 3, 2, 1))
    def _draw_beard(surface, cx, cy, facing, phase):
        """Massive fiery orange beard."""
        hx = cx + facing * 3
        hy = cy - 16
        sway = math.sin(phase * 0.5) * 1
        # Big bushy beard shape
        beard_pts = [
            (hx - 9, hy + 3),
            (hx - 12, hy + 8),
            (hx - 13, hy + 14),
            (hx - 11, hy + 20),
            (hx - 6, hy + 24),
            (hx - 2, hy + 26 + int(sway)),
            (hx + 4, hy + 25),
            (hx + 9, hy + 22),
            (hx + 12, hy + 17),
            (hx + 13, hy + 11),
            (hx + 11, hy + 5),
            (hx + 8, hy + 6),
            (hx + 4, hy + 7),
            (hx - 2, hy + 7),
            (hx - 6, hy + 6),
        ]
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in beard_pts])
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["hair_darkest"], beard_pts)
        # Main beard color
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["hair_dark"], [
            (hx - 8, hy + 4),
            (hx - 11, hy + 8),
            (hx - 12, hy + 14),
            (hx - 10, hy + 19),
            (hx - 5, hy + 22),
            (hx - 2, hy + 24),
            (hx + 4, hy + 23),
            (hx + 8, hy + 20),
            (hx + 11, hy + 15),
            (hx + 12, hy + 10),
            (hx + 10, hy + 6),
            (hx + 4, hy + 8),
            (hx - 5, hy + 8),
        ])
        # Mid tone
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["hair_mid"], [
            (hx - 6, hy + 6),
            (hx - 9, hy + 10),
            (hx - 10, hy + 14),
            (hx - 7, hy + 18),
            (hx - 2, hy + 20),
            (hx + 4, hy + 19),
            (hx + 8, hy + 16),
            (hx + 10, hy + 12),
            (hx + 9, hy + 8),
        ])
        # Light strands
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["hair_light"], [
            (hx - 4, hy + 10),
            (hx - 5, hy + 14),
            (hx - 2, hy + 16),
            (hx + 2, hy + 15),
            (hx + 5, hy + 13),
            (hx + 4, hy + 10),
        ])
        # Shine highlights
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["hair_shine"],
                         (hx - 2, hy + 12, 2, 2))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["hair_shine"],
                         (hx + 3, hy + 11, 1, 2))
        # Beard texture strands (curly)
        for i in range(6):
            angle_off = i * math.pi / 3 + phase * 0.2
            sx = hx + int(math.cos(angle_off) * 6)
            sy = hy + 15 + int(math.sin(angle_off) * 6)
            pygame.draw.line(surface, _NS_broggmar.PALETTE["hair_darkest"],
                             (sx - 1, sy), (sx + 1, sy), 1)
            pygame.draw.line(surface, _NS_broggmar.PALETTE["hair_dark"],
                             (sx, sy - 1), (sx, sy + 1), 1)
        # Mustache (bushy handlebars)
        _NS_broggmar._draw_mustache(surface, hx, hy + 5, facing, phase)
        # Gold beard ring/braid
        ring_y = hy + 20 + int(sway)
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["gold_dark"],
                         (hx - 2, ring_y, 5, 3))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["gold_mid"],
                         (hx - 2, ring_y, 5, 2))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["gold_light"],
                         (hx - 1, ring_y, 3, 1))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["gold_shine"],
                         (hx, ring_y, 1, 1))
    def _draw_mustache(surface, mx, my, facing, phase):
        """Handlebar mustache."""
        sway = math.sin(phase * 0.5) * 1
        # Left side
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["hair_darkest"], [
            (mx - 8, my - 1),
            (mx - 2, my - 1),
            (mx - 1, my + 2),
            (mx - 7, my + 3 + int(sway)),
            (mx - 10, my + 1),
        ])
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["hair_dark"], [
            (mx - 7, my),
            (mx - 2, my),
            (mx - 2, my + 2),
            (mx - 6, my + 2),
            (mx - 8, my + 1),
        ])
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["hair_mid"], [
            (mx - 5, my),
            (mx - 3, my),
            (mx - 3, my + 1),
            (mx - 5, my + 1),
        ])
        # Right side
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["hair_darkest"], [
            (mx + 2, my - 1),
            (mx + 8, my - 1),
            (mx + 10, my + 1),
            (mx + 7, my + 3 - int(sway)),
            (mx + 1, my + 2),
        ])
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["hair_dark"], [
            (mx + 2, my),
            (mx + 7, my),
            (mx + 8, my + 1),
            (mx + 6, my + 2),
            (mx + 2, my + 2),
        ])
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["hair_mid"], [
            (mx + 3, my),
            (mx + 5, my),
            (mx + 5, my + 1),
            (mx + 3, my + 1),
        ])
    # ============================================================
    # AMBIENT FX
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius, 120 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (5, 3, 8, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (30, 15, 40, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_magic_aura(surface, x, y, phase):
        """Purple magic aura around boss."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_broggmar._alpha((90 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_broggmar._aacircle(aura, (*_NS_broggmar.PALETTE["magic_darkest"], alpha),
                                       (110, 90), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_broggmar._alpha((55 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_broggmar._aacircle(aura, (*_NS_broggmar.PALETTE["magic_dark"], alpha),
                                       (110, 90), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_broggmar._alpha((30 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_broggmar._aacircle(aura, (*_NS_broggmar.PALETTE["magic_mid"], alpha),
                                       (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        # Floating sparkles
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_broggmar.PALETTE["magic_light"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_broggmar.PALETTE["magic_hot"], (sx, sy, 1, 1))
    def _draw_float_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Wisps below character (floating effect)."""
        strength = 1.5 if intense else 1.0
        # Mist below body
        mist = pygame.Surface((150, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(30, 3, -2):
            alpha = _NS_broggmar._alpha((30 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_broggmar.PALETTE["magic_dark"], alpha),
                    (75 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(18, 3, -2):
            alpha = _NS_broggmar._alpha((18 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_broggmar.PALETTE["magic_mid"], alpha),
                    (75 - radius, 20 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (x_off := cx - 75, cy - 5))
        # Rising bubbles
        for i in range(7):
            t = (phase * 0.5 + i * 0.14) % 1.0
            sx = cx - 22 + i * 8 + int(math.sin(phase + i) * 3)
            sy = cy - int(t * 20)
            alpha = _NS_broggmar._alpha(220 * (1 - t) * strength)
            if alpha > 0:
                _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_dark"], alpha),
                                       (sx, sy), 3)
                _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_mid"], alpha),
                                       (sx, sy - 1), 2)
                pygame.draw.rect(surface, (*_NS_broggmar.PALETTE["magic_light"], alpha),
                                 (sx, sy - 1, 1, 1))
        # Trail behind
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_broggmar._alpha(150 - i * 25)
                if alpha <= 0:
                    continue
                _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_dark"], alpha),
                                       (sx, sy), max(2, 6 - i))
                _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_mid"], alpha),
                                       (sx, sy), max(1, 4 - i))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring at feet."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_broggmar.PALETTE["magic_dark"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_broggmar.PALETTE["magic_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_broggmar.PALETTE["magic_mid"], 200),
                            (25, 22, 120, 18), 1)
        # Runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_broggmar.PALETTE["magic_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_broggmar.PALETTE["magic_hot"],
                                       _NS_broggmar._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # SKILL Q - BARREL ROLL (rolling barrel projectile)
    # ============================================================
    def _draw_barrelroll_ground(surface, boss, x, y, timer, phase):
        """Trail on ground behind rolling barrel."""
        pass  # visual is in projectile
    def _draw_barrelroll_projectile(surface, boss, x, y, timer, phase):
        """Rolling barrel projectile with purple magic trail."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_broggmar._target_position(boss, x, y)
        if progress < 0.15:
            # Wind-up on hand
            return
        t = (progress - 0.15) / 0.85
        t = min(1.0, t)
        start_x = x + facing * 30
        start_y = y - 5
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Trail
        for i in range(8):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_broggmar._alpha(200 - i * 22)
            size = max(2, 8 - i)
            _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_darkest"], alpha),
                                   (px, py), size)
            _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_dark"], alpha),
                                   (px, py), max(1, size - 2))
            _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_mid"], alpha),
                                   (px, py), max(1, size - 4))
            # Sparks
            if i < 3:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface,
                                     (*_NS_broggmar.PALETTE["magic_hot"], alpha),
                                     (spark_x, spark_y, 1, 1))
        # Rotating barrel
        rot = phase * 3 + t * math.pi * 6
        _NS_broggmar._draw_flying_barrel(surface, bx, by, rot, facing)
        # Purple aura around barrel
        for r in range(14, 5, -2):
            alpha = _NS_broggmar._alpha(120 * (14 - r) / 14)
            _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_light"], alpha),
                                   (bx, by), r)
        # Impact
        if t > 0.9:
            st = (t - 0.9) / 0.1
            radius = int(10 + st * 30)
            alpha = _NS_broggmar._alpha(240 * (1 - st))
            _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_darkest"], alpha),
                                   (tx, ty), radius + 3, 3)
            _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_dark"], alpha),
                                   (tx, ty), radius, 3)
            _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_mid"], alpha),
                                   (tx, ty), max(1, radius - 5), 2)
            _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_light"], alpha),
                                   (tx, ty), max(1, radius - 10), 1)
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_broggmar.PALETTE["magic_hot"], alpha),
                                 (ex, ey, 2, 2))
    def _draw_flying_barrel(surface, bx, by, rotation, facing):
        """Small flying/rolling barrel."""
        bw = 12
        bh = 14
        # Basic barrel
        rect_pts = [
            (bx - bw // 2, by - bh // 2 + 1),
            (bx + bw // 2, by - bh // 2 + 1),
            (bx + bw // 2 + 1, by),
            (bx + bw // 2, by + bh // 2 - 1),
            (bx - bw // 2, by + bh // 2 - 1),
            (bx - bw // 2 - 1, by),
        ]
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in rect_pts])
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["wood_darkest"], rect_pts)
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["wood_dark"], [
            (bx - bw // 2 + 1, by - bh // 2 + 2),
            (bx + bw // 2 - 1, by - bh // 2 + 2),
            (bx + bw // 2, by),
            (bx + bw // 2 - 1, by + bh // 2 - 2),
            (bx - bw // 2 + 1, by + bh // 2 - 2),
            (bx - bw // 2, by),
        ])
        _NS_broggmar._poly(surface, _NS_broggmar.PALETTE["wood_mid"], [
            (bx - bw // 2 + 2, by - bh // 2 + 3),
            (bx + bw // 2 - 2, by - bh // 2 + 3),
            (bx + bw // 2 - 1, by),
            (bx + bw // 2 - 2, by + bh // 2 - 3),
            (bx - bw // 2 + 2, by + bh // 2 - 3),
        ])
        # Rotating plank lines (indicates spin)
        for i in range(2):
            angle = rotation + i * math.pi / 2
            x1 = bx + int(math.cos(angle) * 3)
            y1 = by + int(math.sin(angle) * 4)
            x2 = bx - int(math.cos(angle) * 3)
            y2 = by - int(math.sin(angle) * 4)
            pygame.draw.line(surface, _NS_broggmar.PALETTE["wood_darkest"],
                             (x1, y1), (x2, y2), 1)
        # Iron bands
        for band_y_off in (-4, 3):
            band_y = by + band_y_off
            pygame.draw.rect(surface, _NS_broggmar.PALETTE["iron_dark"],
                             (bx - bw // 2 - 1, band_y, bw + 2, 2))
            pygame.draw.rect(surface, _NS_broggmar.PALETTE["iron_light"],
                             (bx - bw // 2, band_y, bw, 1))
        # Glow (magic charged)
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["magic_light"],
                         (bx - 1, by, 2, 1))
        pygame.draw.rect(surface, _NS_broggmar.PALETTE["magic_hot"],
                         (bx, by, 1, 1))
    # ============================================================
    # SKILL W - DRUNKEN RAGE (aura on body)
    # ============================================================
    def _draw_drunkenrage_aura(surface, boss, x, y, timer, phase):
        """Purple aura shroud on body."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Aura circles pulsing on body
        breath = math.sin(phase * 2) * 3
        r = 50 + int(breath)
        aura = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)
        for i, (thickness, alpha_val) in enumerate([(3, 100), (2, 140), (1, 180)]):
            _NS_broggmar._aacircle(aura, (*_NS_broggmar.PALETTE["magic_dark"], alpha_val),
                                   center, r - i, thickness)
            _NS_broggmar._aacircle(aura, (*_NS_broggmar.PALETTE["magic_mid"], alpha_val),
                                   center, r - i - 1, 1)
        # Sparkles rotating
        for i in range(16):
            angle = phase * 1.5 + i * math.pi / 8
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            pygame.draw.rect(aura, _NS_broggmar.PALETTE["magic_light"], (sx, sy, 2, 2))
            pygame.draw.rect(aura, _NS_broggmar.PALETTE["magic_hot"], (sx, sy, 1, 1))
        surface.blit(aura, (x - r - 10, y - r - 10))
        # Rising drunken fumes on body
        for i in range(8):
            fume_t = (phase * 0.6 + i * 0.12) % 1.0
            fx = x + int(math.sin(phase + i) * 15)
            fy = y + 10 - int(fume_t * 40)
            alpha = _NS_broggmar._alpha(200 * (1 - fume_t))
            if alpha > 0:
                _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_dark"], alpha),
                                       (fx, fy), 3)
                _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_mid"], alpha),
                                       (fx, fy), 2)
                pygame.draw.rect(surface, (*_NS_broggmar.PALETTE["magic_light"], alpha),
                                 (fx, fy, 1, 1))
                pygame.draw.rect(surface, (*_NS_broggmar.PALETTE["magic_hot"], alpha),
                                 (fx, fy - 1, 1, 1))
        # Foam bubbles rising (drunken)
        for i in range(4):
            b_t = (phase * 0.4 + i * 0.25) % 1.0
            bx = x - 20 + i * 12
            by = y - int(b_t * 30)
            alpha = _NS_broggmar._alpha(230 * (1 - b_t))
            _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["foam_dark"], alpha),
                                   (bx, by), 3)
            _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["foam_mid"], alpha),
                                   (bx, by), 2)
            pygame.draw.rect(surface, (*_NS_broggmar.PALETTE["foam_light"], alpha),
                             (bx, by, 1, 1))
    # ============================================================
    # SKILL E - BODY SLAM (charge + slam)
    # ============================================================
    def _draw_bodyslam_ground(surface, boss, x, y, timer, pulse):
        """Ground impact rings."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            # Charging trail
            for i in range(5):
                t_off = i / 5
                sx = x - int(boss.direction * i * 8)
                alpha = _NS_broggmar._alpha(180 * (1 - t_off))
                _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_dark"], alpha),
                                       (sx, y + 44), max(2, 6 - i))
                pygame.draw.rect(surface, (*_NS_broggmar.PALETTE["magic_light"], alpha),
                                 (sx, y + 44, 1, 1))
        else:
            # Slam impact
            t = (progress - 0.5) / 0.5
            r = int(20 + t * 45)
            alpha = _NS_broggmar._alpha(220 * (1 - t))
            for ring_i in range(3):
                ring_r = r - ring_i * 8
                if ring_r < 5:
                    continue
                pygame.draw.ellipse(surface, (*_NS_broggmar.PALETTE["magic_dark"], alpha),
                                    (x - ring_r, y + 44 - ring_r // 3,
                                     ring_r * 2, ring_r * 2 // 3), 3)
                pygame.draw.ellipse(surface, (*_NS_broggmar.PALETTE["magic_mid"], alpha),
                                    (x - ring_r + 2, y + 44 - ring_r // 3 + 2,
                                     ring_r * 2 - 4, ring_r * 2 // 3 - 4), 2)
            # Cracks radiating
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = x + int(math.cos(angle_s) * r)
                ey = y + 44 + int(math.sin(angle_s) * r * 0.4)
                pygame.draw.line(surface, (*_NS_broggmar.PALETTE["magic_light"], alpha),
                                 (x, y + 44), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_broggmar.PALETTE["magic_hot"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # SKILL R - EXPLOSIVE CASK (huge exploding barrel)
    # ============================================================
    def _draw_explosivecask_ground(surface, boss, x, y, timer, phase):
        """AoE ground at target."""
        tx, ty = _NS_broggmar._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.5:
            t = (progress - 0.5) / 0.5
            r = int(30 + t * 40)
            alpha = _NS_broggmar._alpha(240 * (1 - t * 0.4))
            pygame.draw.ellipse(surface, (*_NS_broggmar.PALETTE["magic_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_broggmar.PALETTE["magic_dark"], alpha),
                                (tx - r + 4, ty - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_broggmar.PALETTE["magic_mid"], alpha),
                                (tx - r + 10, ty - r // 3 + 4,
                                 r * 2 - 20, r * 2 // 3 - 8))
    def _draw_explosivecask_projectile(surface, boss, x, y, timer, phase):
        """Big cask lobbed with arc, then explodes."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_broggmar._target_position(boss, x, y)
        if progress < 0.15:
            # Wind-up
            return
        if progress < 0.55:
            # Cask flying with arc
            t = (progress - 0.15) / 0.4
            start_x = x + facing * 25
            start_y = y - 25
            bx = int(start_x + (tx - start_x) * t)
            arc = math.sin(t * math.pi) * 50
            by = int(start_y + (ty - start_y) * t - arc)
            # Trail
            for i in range(6):
                trail_t = max(0.0, t - i * 0.06)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t
                         - math.sin(trail_t * math.pi) * 50)
                alpha = _NS_broggmar._alpha(180 - i * 25)
                _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_dark"], alpha),
                                       (px, py), max(2, 6 - i))
                _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_mid"], alpha),
                                       (px, py), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_broggmar.PALETTE["magic_hot"], alpha),
                                 (px, py, 1, 1))
            # Rotating cask
            rot = phase * 2 + t * math.pi * 4
            _NS_broggmar._draw_flying_barrel(surface, bx, by, rot, facing)
            # Aura
            for r in range(12, 4, -2):
                alpha = _NS_broggmar._alpha(150 * (12 - r) / 12)
                _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_light"], alpha),
                                       (bx, by), r)
        else:
            # EXPLOSION
            t = (progress - 0.55) / 0.45
            explode_r = int(15 + t * 60)
            intensity = math.sin(min(t * math.pi, math.pi))
            alpha = _NS_broggmar._alpha(255 * intensity)
            # Central blast
            for r in range(explode_r + 5, 0, -4):
                a = _NS_broggmar._alpha(alpha * (explode_r + 5 - r) / (explode_r + 5))
                _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_darkest"], a),
                                       (tx, ty), r)
            for r in range(int(explode_r * 0.8), 0, -3):
                a = _NS_broggmar._alpha(alpha * (explode_r * 0.8 - r) / (explode_r * 0.8))
                _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_dark"], a),
                                       (tx, ty), r)
            for r in range(int(explode_r * 0.5), 0, -2):
                a = _NS_broggmar._alpha(alpha * (explode_r * 0.5 - r) / (explode_r * 0.5))
                _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_mid"], a),
                                       (tx, ty), r)
            _NS_broggmar._aacircle(surface, _NS_broggmar.PALETTE["magic_light"],
                                   (tx, ty), max(2, explode_r // 4))
            _NS_broggmar._aacircle(surface, _NS_broggmar.PALETTE["magic_hot"],
                                   (tx, ty), max(1, explode_r // 8))
            _NS_broggmar._aacircle(surface, _NS_broggmar.PALETTE["white"],
                                   (tx, ty), max(1, explode_r // 16))
            # Shockwave ring
            ring_r = int(explode_r * 1.1)
            pygame.draw.ellipse(surface, (*_NS_broggmar.PALETTE["magic_light"], alpha),
                                (tx - ring_r, ty - ring_r // 2,
                                 ring_r * 2, ring_r), 3)
            pygame.draw.ellipse(surface, (*_NS_broggmar.PALETTE["magic_hot"], alpha),
                                (tx - ring_r + 2, ty - ring_r // 2 + 1,
                                 ring_r * 2 - 4, ring_r - 2), 2)
            # Debris/sparks flying outward
            for i in range(16):
                angle_s = i * math.pi / 8 + phase * 0.5
                dist = int(explode_r * (0.7 + (i % 3) * 0.15))
                ex = tx + int(math.cos(angle_s) * dist)
                ey = ty + int(math.sin(angle_s) * dist * 0.75)
                pygame.draw.rect(surface, (*_NS_broggmar.PALETTE["magic_hot"], alpha),
                                 (ex, ey, 3, 3))
                pygame.draw.rect(surface, (*_NS_broggmar.PALETTE["magic_shine"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_broggmar.PALETTE["white"], alpha),
                                 (ex, ey, 1, 1))
            # Rising fumes
            for i in range(8):
                fume_t = (phase * 0.7 + i * 0.12) % 1.0
                fx = tx + int(math.cos(i * math.pi / 4) * 20)
                fy = ty - int(fume_t * 40)
                fa = _NS_broggmar._alpha(180 * (1 - fume_t) * intensity)
                if fa > 0:
                    _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_dark"], fa),
                                           (fx, fy), 3)
                    _NS_broggmar._aacircle(surface, (*_NS_broggmar.PALETTE["magic_mid"], fa),
                                           (fx, fy), 2)



# ====================================================================
# URSATH (WILDCALLER) - Mini Boss
# ====================================================================

class _NS_ursath:
    """Namespace ursath - Druid + Spirit Bear boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Druid skin (aged, weathered)
        "skin_darkest": (55, 35, 25),
        "skin_dark": (120, 85, 60),
        "skin_mid": (180, 140, 105),
        "skin_light": (225, 190, 155),
        "skin_shine": (250, 225, 195),
        # White hair/beard
        "hair_darkest": (60, 55, 50),
        "hair_dark": (130, 125, 115),
        "hair_mid": (195, 190, 180),
        "hair_light": (235, 230, 220),
        "hair_shine": (255, 255, 250),
        # Druid robe (brown-green)
        "robe_darkest": (25, 20, 12),
        "robe_dark": (60, 50, 30),
        "robe_mid": (100, 85, 50),
        "robe_light": (150, 130, 80),
        # Green cloth accents
        "cloth_green_dark": (30, 55, 25),
        "cloth_green_mid": (60, 95, 45),
        "cloth_green_light": (110, 155, 80),
        # Wood staff
        "wood_darkest": (25, 15, 8),
        "wood_dark": (60, 40, 20),
        "wood_mid": (110, 75, 40),
        "wood_light": (170, 125, 75),
        "wood_shine": (215, 180, 130),
        # Bear fur (brown)
        "fur_darkest": (25, 15, 10),
        "fur_dark": (60, 40, 25),
        "fur_mid": (105, 75, 45),
        "fur_light": (165, 125, 80),
        "fur_shine": (215, 175, 125),
        # Bear rune (bright cyan-blue)
        "rune_darkest": (5, 25, 45),
        "rune_dark": (15, 70, 130),
        "rune_mid": (50, 150, 220),
        "rune_light": (130, 210, 255),
        "rune_shine": (220, 245, 255),
        # Nature green magic (staff orb, spirit link)
        "nature_darkest": (10, 35, 10),
        "nature_dark": (30, 90, 25),
        "nature_mid": (80, 180, 50),
        "nature_light": (170, 240, 110),
        "nature_hot": (220, 255, 170),
        "nature_shine": (250, 255, 220),
        # Orange roar (savage roar)
        "roar_darkest": (45, 15, 5),
        "roar_dark": (130, 60, 15),
        "roar_mid": (230, 130, 30),
        "roar_light": (255, 200, 90),
        "roar_hot": (255, 235, 160),
        "roar_shine": (255, 250, 220),
        # Yellow eye (bear)
        "eye_dark": (100, 60, 15),
        "eye_mid": (220, 170, 40),
        "eye_light": (255, 230, 130),
        "eye_glow": (255, 250, 200),
        # Bone/fang/claw
        "bone_dark": (60, 45, 25),
        "bone_mid": (155, 130, 85),
        "bone_light": (230, 210, 165),
        "bone_shine": (255, 245, 215),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_ursath._clamp(color)
        if _NS_ursath.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_ursath._clamp(color)
        if _NS_ursath.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_ursath._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_ursath(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_ursath._detect_moving(boss)
        _NS_ursath._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_ur_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 60) - 15
        )
        # Ambient
        _NS_ursath._draw_nature_aura(surface, x, y, pulse)
        _NS_ursath._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX
        if active_skill == "q":
            _NS_ursath._draw_spirit_link_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_ursath._draw_savage_roar_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_ursath._draw_true_form_ground(surface, boss, x, y, skill_timer, pulse)
        # BEAR (in front, primary attacker) + DRUID (behind)
        # Bear position: slightly forward
        # Druid position: slightly behind
        facing = boss.direction
        bear_x = x + facing * 8
        druid_x = x - facing * 22
        # Bear scale modifier (True Form makes it bigger)
        bear_scale = 1.0
        if active_skill == "r":
            duration = 120
            progress = max(0.0, min(1.0, 1 - skill_timer / duration))
            bear_scale = 1.0 + 0.35 * math.sin(progress * math.pi)  # peaks in middle
        # Draw order: druid behind, then bear in front
        if attacking:
            _NS_ursath._draw_druid(surface, druid_x, y, boss.direction, boss.pulse,
                                    "idle_float")
            _NS_ursath._draw_bear_attack(surface, boss, bear_x, y, bear_scale)
        elif moving:
            _NS_ursath._draw_druid_walk(surface, druid_x, y, boss.direction, boss.pulse)
            _NS_ursath._draw_bear_walk(surface, boss, bear_x, y, bear_scale)
        else:
            _NS_ursath._draw_druid(surface, druid_x, y, boss.direction, boss.pulse,
                                    "idle_float")
            _NS_ursath._draw_bear_idle(surface, boss, bear_x, y, bear_scale)
        # Spirit link visual (always if Q active, connects druid ↔ bear)
        if active_skill == "q":
            _NS_ursath._draw_spirit_link(surface, druid_x, y - 8, bear_x, y - 4,
                                          pulse, skill_timer)
        # Foreground FX
        if active_skill == "e":
            _NS_ursath._draw_savage_roar_foreground(surface, boss, bear_x, y,
                                                     skill_timer, pulse)
        elif active_skill == "r":
            _NS_ursath._draw_true_form_foreground(surface, boss, bear_x, y,
                                                    skill_timer, pulse, bear_scale)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 60)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_ur_previous_timer", 0))
        active = bool(getattr(boss, "_ur_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._ur_attack_active = True
            boss._ur_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._ur_attack_frame = int(getattr(boss, "_ur_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._ur_attack_active = False
            boss._ur_attack_frame = 0
            active = False
        boss._ur_previous_timer = timer
        boss._ur_attack_progress = (
            min(1.0, getattr(boss, "_ur_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_ur_last_x"):
            boss._ur_last_x = boss.x
            boss._ur_last_y = boss.y
            return False
        dx = abs(boss.x - boss._ur_last_x)
        dy = abs(boss.y - boss._ur_last_y)
        boss._ur_last_x = boss.x
        boss._ur_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # SHADOW
    # ============================================================
    def _draw_shadow(surface, x, y, width=140):
        shadow = pygame.Surface((width + 20, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius, width + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 5, 2, 170), (5, 8, width + 10, 14))
        surface.blit(shadow, (x - width // 2 - 10, y - 15))
    # ============================================================
    # DRUID (humanoid old druid, floating)
    # ============================================================
    def _draw_druid_walk(surface, cx, cy, facing, phase):
        # Slightly different bob for walking
        float_bob = int(math.sin(phase * 1.5) * 4) - 6
        _NS_ursath._draw_druid(surface, cx, cy + float_bob, facing, phase, "walk")
    def _draw_druid(surface, cx, cy, facing, phase, action):
        """Old druid floating with staff."""
        float_bob = int(math.sin(phase * 0.6) * 4) - 6
        if action == "walk":
            float_bob = 0  # already applied by caller
        dy = cy + float_bob if action != "walk" else cy
        # Shadow (smaller, druid is behind/floating)
        _NS_ursath._draw_shadow(surface, cx, cy + 50, width=70)
        # Ambient green wisps around druid
        _NS_ursath._draw_druid_wisps(surface, cx, dy, phase)
        # Draw order: staff (behind body), robe/legs, body, arms, head, hair
        # Robe body (draped, wide at bottom, floating)
        _NS_ursath._draw_druid_robe(surface, cx, dy, facing, phase)
        # Staff (in back hand, extending up)
        _NS_ursath._draw_druid_staff(surface, cx - facing * 6, dy - 4, facing, phase)
        # Torso/arms
        _NS_ursath._draw_druid_body(surface, cx, dy, facing, phase)
        # Head with beard
        _NS_ursath._draw_druid_head(surface, cx + facing * 1, dy - 22, facing, phase)
    def _draw_druid_robe(surface, cx, cy, facing, phase):
        """Long flowing robe, wider at bottom."""
        sway = math.sin(phase * 0.5) * 2
        # Robe outline (elongated triangle, wide bottom)
        robe_shape = [
            (cx - 7, cy - 4),
            (cx - 8, cy),
            (cx - 10, cy + 8),
            (cx - 14 + int(sway), cy + 18),
            (cx - 12 + int(sway), cy + 22),
            (cx + 12 - int(sway), cy + 22),
            (cx + 14 - int(sway), cy + 18),
            (cx + 10, cy + 8),
            (cx + 8, cy),
            (cx + 7, cy - 4),
        ]
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in robe_shape])
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["robe_darkest"], robe_shape)
        # Inner robe
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["robe_dark"], [
            (cx - 6, cy - 3),
            (cx - 8, cy + 8),
            (cx - 12 + int(sway), cy + 20),
            (cx + 12 - int(sway), cy + 20),
            (cx + 8, cy + 8),
            (cx + 6, cy - 3),
        ])
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["robe_mid"], [
            (cx - 4, cy - 2),
            (cx - 6, cy + 8),
            (cx - 9 + int(sway), cy + 18),
            (cx + 9 - int(sway), cy + 18),
            (cx + 6, cy + 8),
            (cx + 4, cy - 2),
        ])
        # Green cloth trim
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["cloth_green_dark"], [
            (cx - 10 + int(sway), cy + 18),
            (cx + 10 - int(sway), cy + 18),
            (cx + 12 - int(sway), cy + 22),
            (cx - 12 + int(sway), cy + 22),
        ])
        pygame.draw.line(surface, _NS_ursath.PALETTE["cloth_green_mid"],
                         (cx - 10 + int(sway), cy + 20),
                         (cx + 10 - int(sway), cy + 20), 1)
        pygame.draw.line(surface, _NS_ursath.PALETTE["cloth_green_light"],
                         (cx - 8, cy + 21), (cx + 8, cy + 21), 1)
        # Center robe belt (with rune)
        pygame.draw.rect(surface, _NS_ursath.PALETTE["cloth_green_dark"],
                         (cx - 6, cy + 5, 12, 3))
        pygame.draw.rect(surface, _NS_ursath.PALETTE["cloth_green_mid"],
                         (cx - 6, cy + 5, 12, 1))
        # Belt buckle - rune
        pulse_rune = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(3, 0, -1):
            alpha = _NS_ursath._alpha(100 * (3 - r) / 3 * pulse_rune)
            _NS_ursath._aacircle(surface, (*_NS_ursath.PALETTE["nature_mid"], alpha),
                                  (cx, cy + 6), r)
        pygame.draw.rect(surface, _NS_ursath.PALETTE["nature_light"], (cx - 1, cy + 6, 2, 2))
        pygame.draw.rect(surface, _NS_ursath.PALETTE["nature_shine"], (cx, cy + 6, 1, 1))
    def _draw_druid_body(surface, cx, cy, facing, phase):
        """Upper torso and arms (partially hidden by robe)."""
        # Shoulders visible above robe
        shoulders = [
            (cx - 8, cy - 6),
            (cx - 9, cy - 3),
            (cx - 7, cy - 2),
            (cx + 7, cy - 2),
            (cx + 9, cy - 3),
            (cx + 8, cy - 6),
        ]
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in shoulders])
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["robe_darkest"], shoulders)
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["robe_dark"], [
            (cx - 7, cy - 5),
            (cx - 8, cy - 3),
            (cx + 8, cy - 3),
            (cx + 7, cy - 5),
        ])
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["cloth_green_mid"], [
            (cx - 5, cy - 5),
            (cx - 6, cy - 3),
            (cx + 6, cy - 3),
            (cx + 5, cy - 5),
        ])
        # Back arm (holding staff)
        back_arm_x = cx - facing * 7
        back_arm_y = cy - 3
        back_hand_x = cx - facing * 9
        back_hand_y = cy - 6
        _NS_ursath._aaline(surface, _NS_ursath.PALETTE["shadow_deep"],
                            (back_arm_x + 1, back_arm_y + 1),
                            (back_hand_x + 1, back_hand_y + 1), 4)
        _NS_ursath._aaline(surface, _NS_ursath.PALETTE["robe_dark"],
                            (back_arm_x, back_arm_y), (back_hand_x, back_hand_y), 3)
        _NS_ursath._aaline(surface, _NS_ursath.PALETTE["robe_mid"],
                            (back_arm_x, back_arm_y - 1),
                            (back_hand_x, back_hand_y - 1), 2)
        # Hand (skin)
        _NS_ursath._aacircle(surface, _NS_ursath.PALETTE["skin_darkest"],
                              (back_hand_x, back_hand_y), 2)
        _NS_ursath._aacircle(surface, _NS_ursath.PALETTE["skin_dark"],
                              (back_hand_x, back_hand_y), 1)
        # Front arm (relaxed forward)
        sway = math.sin(phase * 0.6) * 1
        front_arm_x = cx + facing * 7
        front_arm_y = cy - 2
        front_hand_x = cx + facing * 9 + int(sway)
        front_hand_y = cy + 2
        _NS_ursath._aaline(surface, _NS_ursath.PALETTE["shadow_deep"],
                            (front_arm_x + 1, front_arm_y + 1),
                            (front_hand_x + 1, front_hand_y + 1), 4)
        _NS_ursath._aaline(surface, _NS_ursath.PALETTE["robe_dark"],
                            (front_arm_x, front_arm_y), (front_hand_x, front_hand_y), 3)
        _NS_ursath._aaline(surface, _NS_ursath.PALETTE["robe_mid"],
                            (front_arm_x, front_arm_y - 1),
                            (front_hand_x, front_hand_y - 1), 2)
        # Hand
        _NS_ursath._aacircle(surface, _NS_ursath.PALETTE["skin_darkest"],
                              (front_hand_x, front_hand_y), 2)
        _NS_ursath._aacircle(surface, _NS_ursath.PALETTE["skin_mid"],
                              (front_hand_x, front_hand_y), 1)
    def _draw_druid_staff(surface, cx, cy, facing, phase):
        """Curved wooden staff with green orb at top."""
        # Staff base at hand
        base_x = cx
        base_y = cy + 2
        # Staff extends up and slightly back
        top_x = cx - facing * 3
        top_y = cy - 24
        mid_x = cx - facing * 1
        mid_y = cy - 12
        # Draw staff as curved (bezier-like) line
        prev = (base_x, base_y)
        for step in range(1, 8):
            t = step / 7
            # Quadratic curve
            bx = int((1 - t) ** 2 * base_x + 2 * (1 - t) * t * mid_x + t ** 2 * top_x)
            by = int((1 - t) ** 2 * base_y + 2 * (1 - t) * t * mid_y + t ** 2 * top_y)
            _NS_ursath._aaline(surface, _NS_ursath.PALETTE["shadow_deep"],
                                (prev[0] + 1, prev[1] + 1), (bx + 1, by + 1), 4)
            _NS_ursath._aaline(surface, _NS_ursath.PALETTE["wood_darkest"], prev, (bx, by), 3)
            _NS_ursath._aaline(surface, _NS_ursath.PALETTE["wood_dark"], prev, (bx, by), 2)
            _NS_ursath._aaline(surface, _NS_ursath.PALETTE["wood_mid"],
                                (prev[0], prev[1] - 1), (bx, by - 1), 1)
            prev = (bx, by)
        # Wood grain highlight
        pygame.draw.line(surface, _NS_ursath.PALETTE["wood_light"],
                         (base_x - facing, base_y - 5),
                         (base_x - facing, base_y - 10), 1)
        # Staff top curls (hook shape)
        curl_x, curl_y = top_x, top_y
        pygame.draw.rect(surface, _NS_ursath.PALETTE["wood_dark"],
                         (curl_x - 2, curl_y - 2, 4, 4))
        pygame.draw.rect(surface, _NS_ursath.PALETTE["wood_mid"],
                         (curl_x - 1, curl_y - 2, 3, 2))
        # GREEN ORB (glowing)
        orb_x = curl_x
        orb_y = curl_y - 5
        pulse_orb = math.sin(phase * 1.5) * 0.3 + 0.7
        # Outer glow
        for r in range(8, 0, -1):
            alpha = _NS_ursath._alpha(120 * (8 - r) / 8 * pulse_orb)
            _NS_ursath._aacircle(surface, (*_NS_ursath.PALETTE["nature_mid"], alpha),
                                  (orb_x, orb_y), r)
        # Orb core
        _NS_ursath._aacircle(surface, _NS_ursath.PALETTE["nature_darkest"], (orb_x, orb_y), 4)
        _NS_ursath._aacircle(surface, _NS_ursath.PALETTE["nature_dark"], (orb_x, orb_y), 3)
        _NS_ursath._aacircle(surface, _NS_ursath.PALETTE["nature_mid"], (orb_x, orb_y), 2)
        _NS_ursath._aacircle(surface, _NS_ursath.PALETTE["nature_light"], (orb_x, orb_y - 1), 1)
        pygame.draw.rect(surface, _NS_ursath.PALETTE["nature_shine"], (orb_x, orb_y - 1, 1, 1))
        # Sparkles around orb
        for i in range(4):
            angle = phase * 2 + i * math.pi / 2
            sx = orb_x + int(math.cos(angle) * 6)
            sy = orb_y + int(math.sin(angle) * 6)
            pygame.draw.rect(surface, _NS_ursath.PALETTE["nature_hot"], (sx, sy, 1, 1))
    def _draw_druid_head(surface, cx, cy, facing, phase):
        """Old druid head with horns/antlers, white beard/hair."""
        # Head base
        head_shape = [
            (cx - 5, cy),
            (cx - 6, cy + 3),
            (cx - 4, cy + 7),
            (cx + 4, cy + 7),
            (cx + 6, cy + 3),
            (cx + 5, cy),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ]
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in head_shape])
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["skin_darkest"], head_shape)
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["skin_dark"], [
            (cx - 4, cy + 1),
            (cx - 5, cy + 3),
            (cx - 3, cy + 6),
            (cx + 3, cy + 6),
            (cx + 5, cy + 3),
            (cx + 4, cy + 1),
            (cx + 2, cy - 2),
            (cx - 2, cy - 2),
        ])
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["skin_mid"], [
            (cx - 3, cy + 2),
            (cx - 4, cy + 4),
            (cx + 4, cy + 4),
            (cx + 3, cy + 2),
        ])
        # Skin highlight
        pygame.draw.rect(surface, _NS_ursath.PALETTE["skin_light"],
                         (cx - 1 + facing, cy + 1, 2, 1))
        # ANTLER HORNS (curling up-back)
        for side in (-1, 1):
            base_x = cx + side * 3
            base_y = cy - 2
            # Antler main branch
            tip_x = base_x + side * 6
            tip_y = cy - 10
            mid_x = base_x + side * 3
            mid_y = cy - 6
            _NS_ursath._aaline(surface, _NS_ursath.PALETTE["shadow_deep"],
                                (base_x + 1, base_y + 1), (mid_x + 1, mid_y + 1), 3)
            _NS_ursath._aaline(surface, _NS_ursath.PALETTE["wood_darkest"],
                                (base_x, base_y), (mid_x, mid_y), 2)
            _NS_ursath._aaline(surface, _NS_ursath.PALETTE["wood_dark"],
                                (base_x, base_y), (mid_x, mid_y), 1)
            _NS_ursath._aaline(surface, _NS_ursath.PALETTE["wood_darkest"],
                                (mid_x, mid_y), (tip_x, tip_y), 2)
            _NS_ursath._aaline(surface, _NS_ursath.PALETTE["wood_mid"],
                                (mid_x, mid_y), (tip_x, tip_y), 1)
            # Small branch on antler
            branch_x = mid_x + side * 2
            branch_y = mid_y - 3
            pygame.draw.line(surface, _NS_ursath.PALETTE["wood_dark"],
                             (mid_x, mid_y - 1), (branch_x, branch_y), 1)
            pygame.draw.rect(surface, _NS_ursath.PALETTE["wood_light"],
                             (branch_x, branch_y, 1, 1))
            # Tip highlight
            pygame.draw.rect(surface, _NS_ursath.PALETTE["bone_light"],
                             (tip_x, tip_y, 1, 1))
        # WHITE HAIR (flowing back)
        back_dir = -facing
        # Top hair
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["hair_darkest"], [
            (cx - 5, cy - 1),
            (cx - 6, cy + 2),
            (cx - 5 + back_dir * 2, cy + 6),
            (cx - 7 + back_dir * 3, cy + 8),
            (cx - 4, cy + 3),
            (cx - 3, cy - 2),
        ])
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["hair_dark"], [
            (cx - 4, cy),
            (cx - 5, cy + 3),
            (cx - 5 + back_dir * 2, cy + 5),
            (cx - 3, cy + 2),
        ])
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["hair_mid"], [
            (cx - 3, cy - 1),
            (cx - 4, cy + 2),
            (cx - 4 + back_dir * 1, cy + 4),
            (cx - 2, cy + 1),
        ])
        # Long hair strands
        for i in range(3):
            hx = cx + back_dir * (5 + i * 3)
            hy = cy + 2 + int(math.sin(phase * 0.3 + i) * 1) + i
            pygame.draw.rect(surface, _NS_ursath.PALETTE["hair_darkest"], (hx - 1, hy, 3, 2))
            pygame.draw.rect(surface, _NS_ursath.PALETTE["hair_mid"], (hx, hy, 1, 1))
        # BEARD (long, flowing white)
        beard_shape = [
            (cx - 4, cy + 5),
            (cx - 5, cy + 8),
            (cx - 4, cy + 14),
            (cx - 2, cy + 18),
            (cx, cy + 20),
            (cx + 2, cy + 18),
            (cx + 4, cy + 14),
            (cx + 5, cy + 8),
            (cx + 4, cy + 5),
            (cx + 2, cy + 6),
            (cx - 2, cy + 6),
        ]
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in beard_shape])
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["hair_darkest"], beard_shape)
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["hair_dark"], [
            (cx - 3, cy + 6),
            (cx - 4, cy + 9),
            (cx - 3, cy + 14),
            (cx, cy + 18),
            (cx + 3, cy + 14),
            (cx + 4, cy + 9),
            (cx + 3, cy + 6),
        ])
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["hair_mid"], [
            (cx - 2, cy + 7),
            (cx - 3, cy + 10),
            (cx - 2, cy + 13),
            (cx, cy + 16),
            (cx + 2, cy + 13),
            (cx + 3, cy + 10),
            (cx + 2, cy + 7),
        ])
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["hair_light"], [
            (cx - 1, cy + 9),
            (cx - 2, cy + 12),
            (cx, cy + 14),
            (cx + 2, cy + 12),
            (cx + 1, cy + 9),
        ])
        # Small eyes (barely visible - wise squint)
        pygame.draw.rect(surface, _NS_ursath.PALETTE["shadow_deep"],
                         (cx + facing * 1, cy + 2, 2, 1))
        pygame.draw.rect(surface, _NS_ursath.PALETTE["nature_mid"],
                         (cx + facing * 1, cy + 2, 1, 1))
    def _draw_druid_wisps(surface, cx, cy, phase):
        """Green magical wisps floating around druid."""
        for i in range(5):
            t = (phase * 0.4 + i * 0.2) % 1.0
            angle = i * math.pi * 2 / 5 + phase * 0.3
            wx = cx + int(math.cos(angle) * 12)
            wy = cy - 5 + int(math.sin(angle) * 10) - int(t * 15)
            alpha = _NS_ursath._alpha(200 * (1 - t))
            if alpha > 0:
                _NS_ursath._aacircle(surface, (*_NS_ursath.PALETTE["nature_dark"], alpha),
                                      (wx, wy), 2)
                pygame.draw.rect(surface, (*_NS_ursath.PALETTE["nature_light"], alpha),
                                 (wx, wy, 1, 1))
    # ============================================================
    # BEAR (main attacker - big brown bear with blue rune)
    # ============================================================
    def _draw_bear_idle(surface, boss, cx, cy, scale=1.0):
        phase = boss.pulse
        bob = int(math.sin(phase * 0.7) * 3) - 2
        _NS_ursath._draw_shadow(surface, cx, cy + 50, width=int(90 * scale))
        _NS_ursath._draw_bear_wisps(surface, cx, cy, phase)
        _NS_ursath._draw_bear_body(surface, cx, cy + bob, boss.direction, phase,
                                    "idle", scale=scale)
    def _draw_bear_walk(surface, boss, cx, cy, scale=1.0):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.9) * 4) - 2
        sway = int(math.sin(phase * 0.6) * 2)
        _NS_ursath._draw_shadow(surface, cx + sway, cy + 50, width=int(90 * scale))
        _NS_ursath._draw_bear_wisps(surface, cx + sway, cy, phase, trail=True,
                                     facing=boss.direction)
        _NS_ursath._draw_bear_body(surface, cx + sway, cy + bob, boss.direction, phase,
                                    "walk", scale=scale)
    def _draw_bear_attack(surface, boss, cx, cy, scale=1.0):
        progress = getattr(boss, "_ur_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Bear lunges forward during attack
        facing = boss.direction
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 4) * facing  # crouch back
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-4 + t * 16)) * facing  # LUNGE forward
            lift = int(3 - t * 5)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(12 * (1 - t)) * facing
            lift = int(-2 + t * 2)
        _NS_ursath._draw_shadow(surface, cx + lunge, cy + 50, width=int(90 * scale))
        _NS_ursath._draw_bear_wisps(surface, cx + lunge, cy, boss.pulse, intense=True)
        _NS_ursath._draw_bear_body(surface, cx + lunge, cy + lift, facing, boss.pulse,
                                    "attack", progress, scale=scale)
        _NS_ursath._draw_bear_claw_slash(surface, boss, cx + lunge, cy + lift,
                                          progress, scale)
    def _draw_bear_body(surface, cx, cy, facing, phase, action, attack_progress=0,
                        scale=1.0):
        """Big bear body - quadruped."""
        s = scale
        def sx(v):
            return int(v * s)
        # Body ellipse (main torso)
        body_shape = [
            (cx - sx(24), cy),
            (cx - sx(26), cy - sx(3)),
            (cx - sx(23), cy - sx(9)),
            (cx - sx(16), cy - sx(13)),
            (cx - sx(6), cy - sx(15)),
            (cx + sx(4), cy - sx(15)),
            (cx + sx(14), cy - sx(13)),
            (cx + sx(22), cy - sx(10)),
            (cx + sx(26), cy - sx(5)),
            (cx + sx(27), cy),
            (cx + sx(25), cy + sx(6)),
            (cx + sx(18), cy + sx(11)),
            (cx + sx(6), cy + sx(13)),
            (cx - sx(6), cy + sx(13)),
            (cx - sx(18), cy + sx(11)),
            (cx - sx(25), cy + sx(6)),
        ]
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 3) for p in body_shape])
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["fur_darkest"], body_shape)
        # Fur mid-tone (upper body)
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["fur_dark"], [
            (cx - sx(22), cy - sx(1)),
            (cx - sx(20), cy - sx(8)),
            (cx - sx(14), cy - sx(11)),
            (cx - sx(4), cy - sx(13)),
            (cx + sx(6), cy - sx(13)),
            (cx + sx(14), cy - sx(11)),
            (cx + sx(20), cy - sx(8)),
            (cx + sx(23), cy - sx(3)),
            (cx + sx(22), cy + sx(2)),
            (cx - sx(20), cy + sx(2)),
        ])
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["fur_mid"], [
            (cx - sx(18), cy - sx(3)),
            (cx - sx(15), cy - sx(9)),
            (cx - sx(4), cy - sx(11)),
            (cx + sx(6), cy - sx(11)),
            (cx + sx(15), cy - sx(9)),
            (cx + sx(18), cy - sx(3)),
            (cx + sx(16), cy),
            (cx - sx(16), cy),
        ])
        # Fur shine on back
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["fur_light"], [
            (cx - sx(10), cy - sx(9)),
            (cx - sx(2), cy - sx(11)),
            (cx + sx(6), cy - sx(11)),
            (cx + sx(10), cy - sx(9)),
            (cx + sx(6), cy - sx(7)),
            (cx - sx(6), cy - sx(7)),
        ])
        # Belly (lighter fur)
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["fur_dark"], [
            (cx - sx(18), cy + sx(3)),
            (cx + sx(18), cy + sx(3)),
            (cx + sx(22), cy + sx(6)),
            (cx + sx(14), cy + sx(11)),
            (cx - sx(14), cy + sx(11)),
            (cx - sx(22), cy + sx(6)),
        ])
        # BLUE RUNE on side (main marker)
        rune_x = cx + int(sx(2))
        rune_y = cy - int(sx(2))
        _NS_ursath._draw_bear_rune(surface, rune_x, rune_y, phase, s)
        # Legs (4 legs - simple)
        _NS_ursath._draw_bear_legs(surface, cx, cy, facing, phase, action, s)
        # Head at front
        head_x = cx + int(sx(20) * facing)
        head_y = cy - int(sx(6))
        _NS_ursath._draw_bear_head(surface, head_x, head_y, facing, phase, action,
                                    attack_progress, s)
        # Fur texture tufts on body
        for i in range(6):
            tx = cx - sx(18) + i * sx(6)
            ty = cy - sx(8) + int(math.sin(i) * sx(2))
            pygame.draw.line(surface, _NS_ursath.PALETTE["fur_darkest"],
                             (tx, ty), (tx + 1, ty - 2), 1)
            pygame.draw.rect(surface, _NS_ursath.PALETTE["fur_light"],
                             (tx + 1, ty - 2, 1, 1))
    def _draw_bear_rune(surface, cx, cy, phase, s=1.0):
        """Glowing blue rune marking on bear's side."""
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        def sx(v):
            return int(v * s)
        # Outer glow
        for r in range(sx(10), 0, -1):
            alpha = _NS_ursath._alpha(80 * (sx(10) - r) / sx(10) * pulse)
            _NS_ursath._aacircle(surface, (*_NS_ursath.PALETTE["rune_mid"], alpha),
                                  (cx, cy), r)
        # Rune circle base
        _NS_ursath._aacircle(surface, _NS_ursath.PALETTE["rune_darkest"], (cx, cy), sx(6))
        _NS_ursath._aacircle(surface, _NS_ursath.PALETTE["rune_dark"], (cx, cy), sx(5))
        _NS_ursath._aacircle(surface, _NS_ursath.PALETTE["rune_mid"], (cx, cy), sx(4), 1)
        # Rune symbol (paw or targeting reticle style)
        # Cross lines
        pygame.draw.line(surface, _NS_ursath.PALETTE["rune_light"],
                         (cx - sx(3), cy), (cx + sx(3), cy), 1)
        pygame.draw.line(surface, _NS_ursath.PALETTE["rune_light"],
                         (cx, cy - sx(3)), (cx, cy + sx(3)), 1)
        # Center dot
        pygame.draw.rect(surface, _NS_ursath.PALETTE["rune_shine"], (cx, cy, 1, 1))
        # 4 small ticks around
        for i in range(4):
            angle = i * math.pi / 2 + math.pi / 4
            tx = cx + int(math.cos(angle) * sx(4))
            ty = cy + int(math.sin(angle) * sx(4))
            pygame.draw.rect(surface, _NS_ursath.PALETTE["rune_light"], (tx, ty, 1, 1))
    def _draw_bear_legs(surface, cx, cy, facing, phase, action, s=1.0):
        """Four bear legs."""
        def sx(v):
            return int(v * s)
        # Walking phase offsets
        walk_offset_back_l = 0
        walk_offset_back_r = 0
        walk_offset_front_l = 0
        walk_offset_front_r = 0
        if action == "walk":
            walk_offset_back_l = int(math.sin(phase * 1.2) * 3)
            walk_offset_back_r = int(math.sin(phase * 1.2 + math.pi) * 3)
            walk_offset_front_l = int(math.sin(phase * 1.2 + math.pi) * 3)
            walk_offset_front_r = int(math.sin(phase * 1.2) * 3)
        # Back legs (further from viewer, drawn first)
        for leg_x, offset in [(-sx(18), walk_offset_back_l), (sx(14), walk_offset_back_r)]:
            leg_top = (cx + leg_x, cy + sx(6))
            leg_foot = (cx + leg_x + offset, cy + sx(15))
            _NS_ursath._aaline(surface, _NS_ursath.PALETTE["shadow_deep"],
                                (leg_top[0] + 1, leg_top[1] + 1),
                                (leg_foot[0] + 1, leg_foot[1] + 1), sx(7))
            _NS_ursath._aaline(surface, _NS_ursath.PALETTE["fur_darkest"],
                                leg_top, leg_foot, sx(6))
            _NS_ursath._aaline(surface, _NS_ursath.PALETTE["fur_dark"],
                                leg_top, leg_foot, sx(5))
            _NS_ursath._aaline(surface, _NS_ursath.PALETTE["fur_mid"],
                                (leg_top[0], leg_top[1] - 1),
                                (leg_foot[0], leg_foot[1] - 1), sx(3))
            # Paw
            _NS_ursath._aacircle(surface, _NS_ursath.PALETTE["fur_darkest"],
                                  leg_foot, sx(4))
            _NS_ursath._aacircle(surface, _NS_ursath.PALETTE["fur_dark"], leg_foot, sx(3))
            # Claws
            for c in range(3):
                cx_claw = leg_foot[0] + (c - 1) * 2
                cy_claw = leg_foot[1] + sx(2)
                pygame.draw.rect(surface, _NS_ursath.PALETTE["bone_dark"],
                                 (cx_claw, cy_claw, 1, 2))
                pygame.draw.rect(surface, _NS_ursath.PALETTE["bone_light"],
                                 (cx_claw, cy_claw + 1, 1, 1))
        # Front legs
        for leg_x, offset in [(-sx(6), walk_offset_front_l), (sx(6), walk_offset_front_r)]:
            leg_top = (cx + leg_x, cy + sx(8))
            leg_foot = (cx + leg_x + offset, cy + sx(15))
            _NS_ursath._aaline(surface, _NS_ursath.PALETTE["shadow_deep"],
                                (leg_top[0] + 1, leg_top[1] + 1),
                                (leg_foot[0] + 1, leg_foot[1] + 1), sx(7))
            _NS_ursath._aaline(surface, _NS_ursath.PALETTE["fur_darkest"],
                                leg_top, leg_foot, sx(6))
            _NS_ursath._aaline(surface, _NS_ursath.PALETTE["fur_dark"],
                                leg_top, leg_foot, sx(5))
            _NS_ursath._aaline(surface, _NS_ursath.PALETTE["fur_mid"],
                                (leg_top[0], leg_top[1] - 1),
                                (leg_foot[0], leg_foot[1] - 1), sx(3))
            _NS_ursath._aacircle(surface, _NS_ursath.PALETTE["fur_darkest"],
                                  leg_foot, sx(4))
            _NS_ursath._aacircle(surface, _NS_ursath.PALETTE["fur_dark"], leg_foot, sx(3))
            for c in range(3):
                cx_claw = leg_foot[0] + (c - 1) * 2
                cy_claw = leg_foot[1] + sx(2)
                pygame.draw.rect(surface, _NS_ursath.PALETTE["bone_dark"],
                                 (cx_claw, cy_claw, 1, 2))
                pygame.draw.rect(surface, _NS_ursath.PALETTE["bone_light"],
                                 (cx_claw, cy_claw + 1, 1, 1))
    def _draw_bear_head(surface, cx, cy, facing, phase, action, attack_progress, s=1.0):
        """Big bear head with snout, yellow eyes, fangs."""
        def sx(v):
            return int(v * s)
        # Head shape (rounded)
        head_shape = [
            (cx - sx(7) * facing, cy - sx(1)),
            (cx - sx(8) * facing, cy + sx(3)),
            (cx - sx(5) * facing, cy + sx(8)),
            (cx + sx(2) * facing, cy + sx(9)),
            (cx + sx(10) * facing, cy + sx(7)),
            (cx + sx(13) * facing, cy + sx(3)),
            (cx + sx(12) * facing, cy - sx(2)),
            (cx + sx(6) * facing, cy - sx(6)),
            (cx - sx(2) * facing, cy - sx(7)),
            (cx - sx(6) * facing, cy - sx(5)),
        ]
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in head_shape])
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["fur_darkest"], head_shape)
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["fur_dark"], [
            (cx - sx(6) * facing, cy),
            (cx - sx(7) * facing, cy + sx(3)),
            (cx - sx(4) * facing, cy + sx(7)),
            (cx + sx(2) * facing, cy + sx(8)),
            (cx + sx(9) * facing, cy + sx(6)),
            (cx + sx(12) * facing, cy + sx(3)),
            (cx + sx(11) * facing, cy - sx(1)),
            (cx + sx(5) * facing, cy - sx(5)),
            (cx - sx(2) * facing, cy - sx(6)),
            (cx - sx(5) * facing, cy - sx(4)),
        ])
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["fur_mid"], [
            (cx - sx(4) * facing, cy - sx(2)),
            (cx - sx(5) * facing, cy + sx(2)),
            (cx - sx(3) * facing, cy + sx(5)),
            (cx + sx(6) * facing, cy + sx(4)),
            (cx + sx(9) * facing, cy + sx(1)),
            (cx + sx(8) * facing, cy - sx(3)),
            (cx + sx(2) * facing, cy - sx(5)),
            (cx - sx(3) * facing, cy - sx(4)),
        ])
        # SNOUT (lighter fur)
        snout_shape = [
            (cx + sx(6) * facing, cy + sx(2)),
            (cx + sx(13) * facing, cy + sx(3)),
            (cx + sx(14) * facing, cy + sx(5)),
            (cx + sx(12) * facing, cy + sx(7)),
            (cx + sx(6) * facing, cy + sx(6)),
        ]
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["fur_dark"], snout_shape)
        _NS_ursath._poly(surface, _NS_ursath.PALETTE["fur_light"], [
            (cx + sx(7) * facing, cy + sx(3)),
            (cx + sx(12) * facing, cy + sx(4)),
            (cx + sx(11) * facing, cy + sx(6)),
            (cx + sx(7) * facing, cy + sx(5)),
        ])
        # NOSE (black)
        pygame.draw.rect(surface, _NS_ursath.PALETTE["shadow_deep"],
                         (cx + sx(13) * facing - 1, cy + sx(3), 3, 2))
        pygame.draw.rect(surface, _NS_ursath.PALETTE["fur_darkest"],
                         (cx + sx(12) * facing, cy + sx(4), 2, 1))
        # EYES (yellow, menacing)
        eye_x = cx + sx(3) * facing
        eye_y = cy + sx(1)
        # Glow
        for r in range(3, 0, -1):
            alpha = _NS_ursath._alpha(100 * (3 - r) / 3)
            _NS_ursath._aacircle(surface, (*_NS_ursath.PALETTE["eye_mid"], alpha),
                                  (eye_x, eye_y), r)
        pygame.draw.rect(surface, _NS_ursath.PALETTE["shadow_deep"],
                         (eye_x - 1, eye_y - 1, 3, 2))
        pygame.draw.rect(surface, _NS_ursath.PALETTE["eye_dark"],
                         (eye_x - 1, eye_y, 3, 1))
        pygame.draw.rect(surface, _NS_ursath.PALETTE["eye_mid"], (eye_x, eye_y, 2, 1))
        pygame.draw.rect(surface, _NS_ursath.PALETTE["eye_light"], (eye_x + 1, eye_y, 1, 1))
        pygame.draw.rect(surface, _NS_ursath.PALETTE["eye_glow"], (eye_x, eye_y, 1, 1))
        # EARS (small triangular)
        for side_x in [-sx(4), sx(4)]:
            ear_bx = cx + side_x * facing
            ear_by = cy - sx(6)
            _NS_ursath._poly(surface, _NS_ursath.PALETTE["fur_darkest"], [
                (ear_bx - 2, ear_by + 2),
                (ear_bx, ear_by - 2),
                (ear_bx + 2, ear_by + 2),
            ])
            _NS_ursath._poly(surface, _NS_ursath.PALETTE["fur_dark"], [
                (ear_bx - 1, ear_by + 1),
                (ear_bx, ear_by - 1),
                (ear_bx + 1, ear_by + 1),
            ])
            pygame.draw.rect(surface, _NS_ursath.PALETTE["fur_mid"],
                             (ear_bx, ear_by, 1, 1))
        # MOUTH / FANGS (opens during attack)
        mouth_open = 0
        if action == "attack" and 0.3 < attack_progress < 0.75:
            mouth_open = int(math.sin((attack_progress - 0.3) / 0.45 * math.pi) * sx(5))
        mouth_x_start = cx + sx(6) * facing
        mouth_x_end = cx + sx(13) * facing
        mouth_y = cy + sx(6)
        if mouth_open > 0:
            # Open mouth (dark red)
            _NS_ursath._poly(surface, _NS_ursath.PALETTE["shadow_deep"], [
                (mouth_x_start, mouth_y),
                (mouth_x_end, mouth_y),
                (mouth_x_end, mouth_y + mouth_open),
                (mouth_x_start, mouth_y + int(mouth_open * 0.7)),
            ])
            _NS_ursath._poly(surface, (60, 15, 15), [
                (mouth_x_start + facing, mouth_y + 1),
                (mouth_x_end - facing, mouth_y + 1),
                (mouth_x_end - facing, mouth_y + mouth_open - 1),
                (mouth_x_start + facing, mouth_y + int(mouth_open * 0.7) - 1),
            ])
            # Upper fangs
            for i, x_off in enumerate((7, 10, 12)):
                fang_x = cx + int(x_off * facing * s)
                fang_top = mouth_y + 1
                fang_bot = mouth_y + int(mouth_open * 0.7)
                pygame.draw.line(surface, _NS_ursath.PALETTE["bone_dark"],
                                 (fang_x, fang_top), (fang_x, fang_bot), 1)
                pygame.draw.rect(surface, _NS_ursath.PALETTE["bone_light"],
                                 (fang_x, fang_bot, 1, 1))
            # Lower fangs
            for i, x_off in enumerate((8, 11)):
                fang_x = cx + int(x_off * facing * s)
                fang_bot = mouth_y + mouth_open
                fang_top = fang_bot - 2
                pygame.draw.line(surface, _NS_ursath.PALETTE["bone_dark"],
                                 (fang_x, fang_bot), (fang_x, fang_top), 1)
                pygame.draw.rect(surface, _NS_ursath.PALETTE["bone_mid"],
                                 (fang_x, fang_top, 1, 1))
        else:
            # Closed mouth line
            pygame.draw.line(surface, _NS_ursath.PALETTE["shadow_deep"],
                             (mouth_x_start, mouth_y + 1),
                             (mouth_x_end, mouth_y + 1), 1)
            # Small fang tips visible
            for x_off in (8, 11):
                fang_x = cx + int(x_off * facing * s)
                pygame.draw.rect(surface, _NS_ursath.PALETTE["bone_mid"],
                                 (fang_x, mouth_y + 1, 1, 2))
    def _draw_bear_claw_slash(surface, boss, cx, cy, progress, scale=1.0):
        """Claw swipe FX during bear attack."""
        if progress < 0.35 or progress > 0.85:
            return
        facing = boss.direction
        t = (progress - 0.35) / 0.5
        t = min(1.0, t)
        # Claw slash arc - horizontal swipe forward
        slash_cx = cx + facing * int(20 * scale)
        slash_cy = cy
        # 3 parallel claw lines
        for claw_i in range(3):
            offset_y = (claw_i - 1) * 5
            # Slash extends across
            start_x = slash_cx - facing * int(15 * scale)
            end_x = slash_cx + facing * int(20 * scale)
            slash_y = slash_cy + offset_y
            # Trail based on t
            current_end_x = int(start_x + (end_x - start_x) * t)
            for layer_i, (thickness, alpha_val, color) in enumerate([
                (5, 80, _NS_ursath.PALETTE["shadow_deep"]),
                (3, 160, _NS_ursath.PALETTE["fur_darkest"]),
                (2, 220, _NS_ursath.PALETTE["bone_light"]),
                (1, 255, _NS_ursath.PALETTE["bone_shine"]),
            ]):
                actual_alpha = _NS_ursath._alpha(alpha_val * (1 - t * 0.4))
                pygame.draw.line(surface, (*color, actual_alpha),
                                 (start_x, slash_y), (current_end_x, slash_y),
                                 thickness)
            # Sparks along claw
            for sp in range(4):
                sp_t = sp / 3
                if sp_t > t:
                    continue
                sp_x = int(start_x + (end_x - start_x) * sp_t)
                sp_y = slash_y + int(math.sin(t * 5 + sp) * 2)
                alpha = _NS_ursath._alpha(220 * (1 - t) * (sp_t + 0.3))
                pygame.draw.rect(surface, (*_NS_ursath.PALETTE["nature_hot"], alpha),
                                 (sp_x, sp_y, 2, 2))
                pygame.draw.rect(surface, (*_NS_ursath.PALETTE["nature_shine"], alpha),
                                 (sp_x, sp_y, 1, 1))
        # Bright impact at leading edge
        tip_x = current_end_x
        for r in range(8, 0, -1):
            alpha = _NS_ursath._alpha(180 * (8 - r) / 8 * (1 - t * 0.5))
            _NS_ursath._aacircle(surface, (*_NS_ursath.PALETTE["rune_light"], alpha),
                                  (tip_x, slash_cy), r)
        _NS_ursath._aacircle(surface, _NS_ursath.PALETTE["rune_shine"],
                              (tip_x, slash_cy), 2)
        pygame.draw.rect(surface, _NS_ursath.PALETTE["white"], (tip_x, slash_cy, 1, 1))
    def _draw_bear_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Blue rune wisps around bear."""
        strength = 1.5 if intense else 1.0
        for i in range(8):
            t = (phase * 0.4 + i * 0.13) % 1.0
            angle = i * math.pi * 2 / 8 + phase * 0.2
            wx = cx + int(math.cos(angle) * 25)
            wy = cy + int(math.sin(angle) * 15) - int(t * 12)
            alpha = _NS_ursath._alpha(200 * (1 - t) * strength)
            if alpha > 0:
                _NS_ursath._aacircle(surface, (*_NS_ursath.PALETTE["rune_dark"], alpha),
                                      (wx, wy), 2)
                pygame.draw.rect(surface, (*_NS_ursath.PALETTE["rune_light"], alpha),
                                 (wx, wy, 1, 1))
        if trail:
            for i in range(4):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_ursath._alpha(150 - i * 30)
                if alpha > 0:
                    _NS_ursath._aacircle(surface, (*_NS_ursath.PALETTE["rune_dark"], alpha),
                                          (sx, sy), max(2, 4 - i))
                    pygame.draw.rect(surface, (*_NS_ursath.PALETTE["rune_light"], alpha),
                                     (sx, sy - 1, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_nature_aura(surface, x, y, phase):
        """Green nature aura around boss."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 180), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_ursath._alpha((100 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_ursath._aacircle(aura, (*_NS_ursath.PALETTE["nature_darkest"], alpha),
                                      (120, 90), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_ursath._alpha((65 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_ursath._aacircle(aura, (*_NS_ursath.PALETTE["nature_dark"], alpha),
                                      (120, 90), radius)
        surface.blit(aura, (x - 120, y - 90))
        # Nature sparkles
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 45 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            color = _NS_ursath.PALETTE["nature_mid"] if i % 2 == 0 \
                else _NS_ursath.PALETTE["rune_mid"]
            hot = _NS_ursath.PALETTE["nature_hot"] if i % 2 == 0 \
                else _NS_ursath.PALETTE["rune_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot, (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground rune ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_ursath.PALETTE["nature_dark"], 200),
                            (5, 22, 170, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_ursath.PALETTE["nature_mid"], 220),
                            (14, 24, 152, 26), 2)
        pygame.draw.ellipse(ring, (*_NS_ursath.PALETTE["rune_mid"], 230),
                            (25, 26, 130, 22), 1)
        # Runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 37 + int(math.sin(angle) * 10)
            x2 = 90 + int(math.cos(angle) * 78)
            y2 = 37 + int(math.sin(angle) * 14)
            pygame.draw.line(ring, (*_NS_ursath.PALETTE["nature_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_ursath.PALETTE["nature_hot"],
                                        _NS_ursath._alpha(150 * pulse)),
                                (15, 15, 150, 40), 1)
        surface.blit(ring, (x - 90, y - 30))
    # ============================================================
    # SKILL Q: SPIRIT LINK - visible cord between druid and bear
    # ============================================================
    def _draw_spirit_link_ground(surface, boss, x, y, timer, pulse):
        """Ground pulses around both entities."""
        # Small pulses at druid and bear feet
        facing = boss.direction
        for cx_off in [-30, 20]:
            r_pulse = int(20 + math.sin(pulse * 2 + cx_off) * 5)
            alpha = _NS_ursath._alpha(180)
            pygame.draw.ellipse(surface, (*_NS_ursath.PALETTE["nature_mid"], alpha),
                                (x + cx_off - r_pulse, y + 40 - r_pulse // 3,
                                 r_pulse * 2, r_pulse * 2 // 3), 2)
    def _draw_spirit_link(surface, dx, dy, bx, by, phase, timer):
        """Green energy tether between druid and bear."""
        # Draw undulating cord
        num_segments = 12
        prev = (dx, dy)
        for i in range(1, num_segments + 1):
            t = i / num_segments
            base_x = int(dx + (bx - dx) * t)
            base_y = int(dy + (by - dy) * t)
            # Wave perturbation
            wave = math.sin(phase * 3 + t * math.pi * 4) * 5
            perp_x = -(by - dy) / max(1, math.hypot(bx - dx, by - dy))
            perp_y = (bx - dx) / max(1, math.hypot(bx - dx, by - dy))
            base_x += int(perp_x * wave)
            base_y += int(perp_y * wave)
            # Multi-layer glow line
            for thickness, color in [
                (5, _NS_ursath.PALETTE["nature_darkest"]),
                (3, _NS_ursath.PALETTE["nature_dark"]),
                (2, _NS_ursath.PALETTE["nature_mid"]),
                (1, _NS_ursath.PALETTE["nature_hot"]),
            ]:
                pygame.draw.line(surface, color, prev, (base_x, base_y), thickness)
            prev = (base_x, base_y)
        # Sparks along the link
        for i in range(6):
            t = ((phase * 0.5 + i / 6) % 1.0)
            spark_x = int(dx + (bx - dx) * t)
            spark_y = int(dy + (by - dy) * t)
            wave = math.sin(phase * 3 + t * math.pi * 4) * 5
            perp_x = -(by - dy) / max(1, math.hypot(bx - dx, by - dy))
            perp_y = (bx - dx) / max(1, math.hypot(bx - dx, by - dy))
            spark_x += int(perp_x * wave)
            spark_y += int(perp_y * wave)
            pygame.draw.rect(surface, _NS_ursath.PALETTE["nature_shine"],
                             (spark_x, spark_y, 2, 2))
            pygame.draw.rect(surface, _NS_ursath.PALETTE["white"],
                             (spark_x, spark_y, 1, 1))
    # ============================================================
    # SKILL E: SAVAGE ROAR (orange sound waves forward)
    # ============================================================
    def _draw_savage_roar_ground(surface, boss, x, y, timer, phase):
        """Orange pulse ring."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(3):
            pulse_offset = (phase * 1.5 + i * 0.5) % 1.0
            r = int(25 + pulse_offset * 45)
            alpha = _NS_ursath._alpha(180 * (1 - pulse_offset))
            pygame.draw.ellipse(surface, (*_NS_ursath.PALETTE["roar_dark"], alpha),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_ursath.PALETTE["roar_mid"], alpha),
                                (x - r + 3, y + 40 - r // 3, r * 2 - 6, r * 2 // 3), 1)
    def _draw_savage_roar_foreground(surface, boss, bear_x, y, timer, phase):
        """Cone of orange sound waves emanating from bear's mouth."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Origin at bear mouth
        origin_x = bear_x + facing * 25
        origin_y = y - 4
        # Multiple concentric wave arcs
        for wave_i in range(5):
            wave_t = (phase * 1.2 + wave_i * 0.2) % 1.0
            wave_r = int(wave_t * 90)
            if wave_r < 10:
                continue
            alpha = _NS_ursath._alpha(220 * (1 - wave_t) * (1 - progress * 0.3))
            # Draw arc segment (facing forward)
            num_pts = 12
            arc_pts = []
            arc_start = -math.pi * 0.35
            arc_end = math.pi * 0.35
            for i in range(num_pts):
                seg_t = i / (num_pts - 1)
                a = arc_start + (arc_end - arc_start) * seg_t
                # Facing multiplier
                px = origin_x + int(math.cos(a) * wave_r * facing)
                py = origin_y + int(math.sin(a) * wave_r)
                arc_pts.append((px, py))
            # Draw as line segments
            for i in range(len(arc_pts) - 1):
                pygame.draw.line(surface,
                                 (*_NS_ursath.PALETTE["roar_darkest"], alpha),
                                 arc_pts[i], arc_pts[i + 1], 4)
                pygame.draw.line(surface,
                                 (*_NS_ursath.PALETTE["roar_dark"], alpha),
                                 arc_pts[i], arc_pts[i + 1], 3)
                pygame.draw.line(surface,
                                 (*_NS_ursath.PALETTE["roar_mid"], alpha),
                                 arc_pts[i], arc_pts[i + 1], 2)
                pygame.draw.line(surface,
                                 (*_NS_ursath.PALETTE["roar_light"], alpha),
                                 arc_pts[i], arc_pts[i + 1], 1)
        # Sparks in front of bear
        for i in range(12):
            spark_t = (phase * 2 + i * 0.1) % 1.0
            angle = (-math.pi * 0.35 + (math.pi * 0.7) * (i / 11))
            spark_dist = int(30 + spark_t * 60)
            sx = origin_x + int(math.cos(angle) * spark_dist * facing)
            sy = origin_y + int(math.sin(angle) * spark_dist)
            alpha = _NS_ursath._alpha(240 * (1 - spark_t))
            pygame.draw.rect(surface, (*_NS_ursath.PALETTE["roar_hot"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_ursath.PALETTE["roar_shine"], alpha),
                             (sx, sy, 1, 1))
    # ============================================================
    # SKILL R: TRUE FORM (bear grows bigger + green glow)
    # ============================================================
    def _draw_true_form_ground(surface, boss, x, y, timer, phase):
        """Ground green rings under enlarged bear."""
        for i in range(4):
            pulse_offset = (phase * 1.2 + i * 0.4) % 1.0
            r = int(30 + pulse_offset * 55)
            alpha = _NS_ursath._alpha(180 * (1 - pulse_offset * 0.7))
            pygame.draw.ellipse(surface, (*_NS_ursath.PALETTE["nature_dark"], alpha),
                                (x - r + 25, y + 40 - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_ursath.PALETTE["nature_mid"], alpha),
                                (x - r + 25 + 2, y + 40 - r // 3,
                                 r * 2 - 4, r * 2 // 3), 1)
    def _draw_true_form_foreground(surface, boss, bear_x, y, timer, phase, bear_scale):
        """Green transformation aura around enlarged bear."""
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Aura circle around bear
        aura_r = int(50 * bear_scale + math.sin(phase * 2) * 4)
        aura = pygame.Surface((aura_r * 2 + 30, aura_r * 2 + 30), pygame.SRCALPHA)
        center = (aura_r + 15, aura_r + 15)
        # Rings
        for i, (thickness, alpha_val) in enumerate([
            (3, 100), (2, 150), (1, 200),
        ]):
            _NS_ursath._aacircle(aura, (*_NS_ursath.PALETTE["nature_dark"], alpha_val),
                                  center, aura_r - i * 2, thickness)
            _NS_ursath._aacircle(aura, (*_NS_ursath.PALETTE["nature_mid"], alpha_val),
                                  center, aura_r - i * 2 - 1, 1)
        # Rising leaves/sparkles
        for i in range(14):
            angle = phase * 0.8 + i * math.pi / 7
            spark_r = aura_r + int(math.sin(phase * 3 + i) * 6) - 3
            sx = center[0] + int(math.cos(angle) * spark_r)
            sy = center[1] + int(math.sin(angle) * spark_r)
            _NS_ursath._aacircle(aura, _NS_ursath.PALETTE["nature_hot"], (sx, sy), 2)
            pygame.draw.rect(aura, _NS_ursath.PALETTE["nature_shine"], (sx, sy, 1, 1))
        surface.blit(aura, (bear_x - aura_r - 15, y - aura_r - 15))
        # Energy tendrils rising
        for i in range(8):
            angle = phase * 0.5 + i * math.pi / 4
            end_x = bear_x + int(math.cos(angle) * (aura_r + 5))
            end_y = y + int(math.sin(angle) * (aura_r + 5))
            alpha = _NS_ursath._alpha(180 + math.sin(phase * 3 + i) * 60)
            pygame.draw.line(surface, (*_NS_ursath.PALETTE["nature_light"], alpha),
                             (bear_x + int(math.cos(angle) * aura_r),
                              y + int(math.sin(angle) * aura_r)),
                             (end_x, end_y), 1)
            pygame.draw.rect(surface, _NS_ursath.PALETTE["nature_hot"], (end_x, end_y, 1, 1))
# ============================================================
# CONVENIENCE WRAPPER
# ============================================================
def draw_ursath(surface, boss, x, y):
    _NS_ursath.draw_ursath(surface, boss, x, y)



# ====================================================================
# ZHAERIS (SHADOWBLADE) - Mini Boss
# ====================================================================

class _NS_zhaeris:
    """Namespace zhaeris - shadow assassin boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (pale, cool-toned assassin)
        "skin_darkest": (38, 32, 42),
        "skin_dark": (82, 72, 90),
        "skin_mid": (145, 130, 155),
        "skin_light": (195, 180, 205),
        "skin_shine": (230, 220, 240),
        # Hair (dark blue-black, long flowing)
        "hair_darkest": (4, 4, 12),
        "hair_dark": (12, 12, 30),
        "hair_mid": (25, 25, 50),
        "hair_light": (45, 45, 75),
        "hair_shine": (75, 75, 115),
        "hair_edge": (105, 105, 145),
        # Outfit (dark ninja cloth)
        "cloth_darkest": (6, 6, 12),
        "cloth_dark": (18, 18, 32),
        "cloth_mid": (35, 35, 55),
        "cloth_light": (60, 60, 85),
        "cloth_edge": (90, 90, 120),
        "cloth_shine": (120, 120, 155),
        # Green energy (neon green — signature)
        "energy_darkest": (5, 30, 10),
        "energy_dark": (15, 75, 30),
        "energy_mid": (45, 165, 65),
        "energy_light": (105, 225, 115),
        "energy_hot": (165, 255, 175),
        "energy_shine": (220, 255, 230),
        # Blade/weapon (green-tinted steel)
        "blade_darkest": (20, 30, 25),
        "blade_dark": (45, 70, 55),
        "blade_mid": (90, 140, 105),
        "blade_light": (155, 215, 170),
        "blade_shine": (220, 250, 230),
        # Smoke/shadow (W skill)
        "smoke_darkest": (8, 6, 16),
        "smoke_dark": (25, 20, 42),
        "smoke_mid": (55, 45, 75),
        "smoke_light": (90, 80, 120),
        "smoke_edge": (130, 120, 165),
        # Eye (green glowing, sharp)
        "eye_socket": (4, 4, 8),
        "eye_dark": (10, 55, 22),
        "eye_mid": (45, 155, 65),
        "eye_light": (105, 225, 125),
        "eye_glow": (185, 255, 195),
        # Wrappings
        "wrap_darkest": (28, 24, 35),
        "wrap_dark": (50, 45, 60),
        "wrap_mid": (75, 70, 90),
        "wrap_light": (105, 100, 120),
        # Metal (kunai/shuriken)
        "metal_darkest": (25, 25, 30),
        "metal_dark": (60, 60, 68),
        "metal_mid": (110, 110, 120),
        "metal_light": (175, 175, 185),
        "metal_shine": (225, 225, 235),
        # Sash accent (dark green)
        "sash_dark": (15, 40, 20),
        "sash_mid": (35, 80, 45),
        "sash_light": (65, 130, 75),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    # ── helpers ──────────────────────────────────────────────
    def _clamp(c):
        return tuple(max(0, min(255, int(v))) for v in c)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_zhaeris._clamp(color)
        if _NS_zhaeris.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_zhaeris._clamp(color)
        if _NS_zhaeris.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        if len(points) < 3:
            return
        pygame.draw.polygon(surface, _NS_zhaeris._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_zhaeris(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_zhaeris._detect_moving(boss)
        _NS_zhaeris._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_zhr_attack_active", False)
            or getattr(boss, "timer", 0)
            > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind
        _NS_zhaeris._draw_energy_aura(surface, x, y, pulse)
        _NS_zhaeris._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX behind body
        if active_skill == "w":
            _NS_zhaeris._draw_twilightshroud_ground(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "e":
            pass  # shuriken has no ground FX
        elif active_skill == "r":
            _NS_zhaeris._draw_perfectexec_ground(
                surface, boss, x, y, skill_timer, pulse
            )
        # Body
        if active_skill == "r":
            _NS_zhaeris._draw_perfectexec_pose(
                surface, boss, x, y, skill_timer, pulse
            )
        elif attacking:
            _NS_zhaeris._draw_attack_pose(surface, boss, x, y)
        elif moving:
            _NS_zhaeris._draw_walk_pose(surface, boss, x, y)
        else:
            _NS_zhaeris._draw_idle_pose(surface, boss, x, y)
        # Twilight shroud overlay on body
        if active_skill == "w":
            _NS_zhaeris._draw_twilightshroud_overlay(
                surface, boss, x, y, skill_timer, pulse
            )
        # Foreground skill FX
        if active_skill == "q":
            _NS_zhaeris._draw_fivepointstrike(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "e":
            _NS_zhaeris._draw_shurikenflip(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "r":
            _NS_zhaeris._draw_perfectexec_slash(
                surface, boss, x, y, skill_timer, pulse
            )
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        prev = int(getattr(boss, "_zhr_prev_timer", 0))
        active = bool(getattr(boss, "_zhr_attack_active", False))
        if timer >= cd - 1 and prev <= 1:
            boss._zhr_attack_active = True
            boss._zhr_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._zhr_attack_frame = int(getattr(boss, "_zhr_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._zhr_attack_active = False
            boss._zhr_attack_frame = 0
            active = False
        boss._zhr_prev_timer = timer
        boss._zhr_attack_progress = (
            min(1.0, getattr(boss, "_zhr_attack_frame", 0) / max(1, cd - 1))
            if active
            else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_zhr_last_x"):
            boss._zhr_last_x = boss.x
            boss._zhr_last_y = boss.y
            return False
        dx = abs(boss.x - boss._zhr_last_x)
        dy = abs(boss.y - boss._zhr_last_y)
        boss._zhr_last_x = boss.x
        boss._zhr_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS  (floating movement)
    # ============================================================
    def _draw_idle_pose(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 5)
        _NS_zhaeris._draw_shadow(surface, x, y + 50)
        _NS_zhaeris._draw_float_wisps(surface, x, y + 42, boss.pulse)
        _NS_zhaeris._draw_body(
            surface, x, y + bob, boss.direction, boss.pulse, "idle"
        )
    def _draw_walk_pose(surface, boss, x, y):
        ph = boss.pulse * 1.6
        bob = int(math.sin(ph * 1.1) * 6)
        sway = int(math.sin(ph * 0.7) * 3)
        _NS_zhaeris._draw_shadow(surface, x + sway, y + 50)
        _NS_zhaeris._draw_float_wisps(
            surface, x + sway, y + 42, ph, trail=True, facing=boss.direction
        )
        _NS_zhaeris._draw_body(
            surface, x + sway, y + bob, boss.direction, ph, "walk"
        )
    def _draw_attack_pose(surface, boss, x, y):
        progress = getattr(boss, "_zhr_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 4) * boss.direction
            lift = int(t * 5)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-4 + t * 18)) * boss.direction
            lift = int(5 - t * 7)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(14 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        _NS_zhaeris._draw_shadow(surface, x + lunge, y + 50)
        _NS_zhaeris._draw_float_wisps(
            surface, x + lunge, y + 42, boss.pulse, intense=True
        )
        _NS_zhaeris._draw_swing_trail(
            surface, boss, x + lunge, y - lift + bob, boss.direction, progress
        )
        _NS_zhaeris._draw_body(
            surface, x + lunge, y - lift + bob, boss.direction,
            boss.pulse, "attack", progress,
        )
        _NS_zhaeris._draw_swing_impact(
            surface, boss, x + lunge, y - lift + bob, boss.direction, progress
        )
    def _draw_perfectexec_pose(surface, boss, x, y, timer, pulse):
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_zhaeris._target_position(boss, x, y)
        if progress < 0.3:
            t = progress / 0.3
            lunge = 0
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.3) / 0.3
            lunge = int(t * (tx - x))
            lift = 3
        else:
            t = (progress - 0.6) / 0.4
            lunge = int((tx - x) * (1 - t * 0.1))
            lift = int(3 * (1 - t))
        bx = x + lunge
        bob = int(math.sin(pulse * 0.7) * 2)
        _NS_zhaeris._draw_shadow(surface, bx, y + 50)
        _NS_zhaeris._draw_float_wisps(surface, bx, y + 42, pulse, intense=True)
        # Afterimages
        if 0.3 < progress < 0.65:
            for i in range(4):
                ax = int(x + lunge * (1 - (i + 1) * 0.2))
                a = _NS_zhaeris._alpha(120 - i * 30)
                gh = pygame.Surface((60, 80), pygame.SRCALPHA)
                _NS_zhaeris._aacircle(
                    gh, (*_NS_zhaeris.PALETTE["energy_dark"], a), (30, 35), 22
                )
                _NS_zhaeris._aacircle(
                    gh, (*_NS_zhaeris.PALETTE["energy_darkest"], a), (30, 35), 16
                )
                surface.blit(gh, (ax - 30, y - lift + bob - 35))
        _NS_zhaeris._draw_body(
            surface, bx, y - lift + bob, boss.direction, pulse, "attack", 0.5
        )
    # ============================================================
    # BODY COMPOSITION
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, progress=0):
        _NS_zhaeris._draw_scarf(surface, cx, cy, facing, phase, action)
        _NS_zhaeris._draw_hair_back(surface, cx, cy, facing, phase)
        _NS_zhaeris._draw_back_arm(surface, cx, cy, facing, phase, action, progress)
        _NS_zhaeris._draw_legs(surface, cx, cy, facing, phase, action)
        _NS_zhaeris._draw_torso(surface, cx, cy, facing, phase)
        _NS_zhaeris._draw_head(surface, cx, cy, facing, phase)
        _NS_zhaeris._draw_hair_front(surface, cx, cy, facing, phase)
        _NS_zhaeris._draw_front_arm_kama(
            surface, cx, cy, facing, phase, action, progress
        )
    # ── LEGS (dangling, floating) ────────────────────────────
    def _draw_legs(surface, cx, cy, facing, phase, action):
        sway = (
            math.sin(phase * 1.3) * 3
            if action == "walk"
            else math.sin(phase * 0.5) * 1.5
        )
        for side in (-1, 1):
            lx = cx + side * 5
            ly = cy + 14
            sw = int(sway * (1 if side > 0 else -1))
            # Thigh
            thigh = [
                (lx - 3, ly - 1), (lx + 3, ly - 1),
                (lx + 4 + sw, ly + 6), (lx - 4 + sw, ly + 6),
            ]
            _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 2) for p in thigh])
            _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["cloth_darkest"], thigh)
            _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["cloth_dark"], [
                (lx - 2, ly), (lx + 2, ly),
                (lx + 3 + sw, ly + 5), (lx - 3 + sw, ly + 5),
            ])
            # Shin + wrapping
            shin = [
                (lx - 3 + sw, ly + 6), (lx + 3 + sw, ly + 6),
                (lx + 3 + sw, ly + 14), (lx - 3 + sw, ly + 14),
            ]
            _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["cloth_darkest"], shin)
            _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["cloth_dark"], [
                (lx - 2 + sw, ly + 7), (lx + 2 + sw, ly + 7),
                (lx + 2 + sw, ly + 13), (lx - 2 + sw, ly + 13),
            ])
            # Wrap bands
            for wy in (ly + 8, ly + 10, ly + 12):
                pygame.draw.line(
                    surface, _NS_zhaeris.PALETTE["wrap_dark"],
                    (lx - 3 + sw, wy + sw // 3),
                    (lx + 3 + sw, wy + sw // 3), 1,
                )
            # Boot tip
            _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["cloth_darkest"], [
                (lx - 3 + sw, ly + 13), (lx + 3 + sw, ly + 13),
                (lx + 4 + sw + facing, ly + 16), (lx - 2 + sw + facing, ly + 16),
            ])
            _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["cloth_dark"], [
                (lx - 2 + sw, ly + 14), (lx + 2 + sw, ly + 14),
                (lx + 3 + sw + facing, ly + 15),
            ])
            pygame.draw.rect(surface, _NS_zhaeris.PALETTE["cloth_light"],
                             (lx + sw, ly + 14, 1, 1))
    # ── TORSO (slim ninja outfit) ────────────────────────────
    def _draw_torso(surface, cx, cy, facing, phase):
        breath = math.sin(phase * 0.6) * 0.8
        body = [
            (cx - 10, cy - 8), (cx - 6, cy - 12),
            (cx + 6, cy - 12), (cx + 10, cy - 8),
            (cx + 11, cy), (cx + 10, cy + 8),
            (cx + 6, cy + 14), (cx - 6, cy + 14),
            (cx - 10, cy + 8), (cx - 11, cy),
        ]
        _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 2) for p in body])
        _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["cloth_darkest"], body)
        # Outfit panels
        _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["cloth_dark"], [
            (cx - 9, cy - 7), (cx - 5, cy - 11), (cx + 5, cy - 11),
            (cx + 9, cy - 7), (cx + 10, cy), (cx + 9, cy + 7),
            (cx + 5, cy + 12), (cx - 5, cy + 12),
            (cx - 9, cy + 7), (cx - 10, cy),
        ])
        _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["cloth_mid"], [
            (cx - 7, cy - 5), (cx - 3, cy - 9), (cx + 3, cy - 9),
            (cx + 7, cy - 5), (cx + 8, cy), (cx + 7, cy + 5),
            (cx + 3, cy + 9), (cx - 3, cy + 9),
            (cx - 7, cy + 5), (cx - 8, cy),
        ])
        # Center seam
        pygame.draw.line(surface, _NS_zhaeris.PALETTE["cloth_darkest"],
                         (cx, cy - 10), (cx, cy + 12), 1)
        # Chest detail (V collar)
        _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["skin_darkest"], [
            (cx - 3, cy - 11), (cx, cy - 7), (cx + 3, cy - 11),
        ])
        _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["skin_dark"], [
            (cx - 2, cy - 10), (cx, cy - 8), (cx + 2, cy - 10),
        ])
        # Green energy trim on collar
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["energy_dark"],
                            (cx - 4, cy - 11), (cx, cy - 6), 1)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["energy_dark"],
                            (cx + 4, cy - 11), (cx, cy - 6), 1)
        # Belt / sash
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["sash_dark"],
                         (cx - 10, cy + 8, 20, 4))
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["sash_mid"],
                         (cx - 9, cy + 9, 18, 2))
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["sash_light"],
                         (cx - 9, cy + 9, 18, 1))
        # Buckle
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["metal_dark"],
                         (cx - 2, cy + 8, 4, 4))
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["metal_mid"],
                         (cx - 1, cy + 9, 2, 2))
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["energy_mid"],
                         (cx - 1, cy + 9, 1, 1))
        # Arm tattoo marks (on torso side, visible)
        for i in range(3):
            ty = cy - 4 + i * 3
            pygame.draw.line(surface, _NS_zhaeris.PALETTE["energy_darkest"],
                             (cx + facing * 8, ty),
                             (cx + facing * 10, ty + 1), 1)
            pygame.draw.rect(surface, _NS_zhaeris.PALETTE["energy_dark"],
                             (cx + facing * 9, ty, 1, 1))
        # Highlight
        _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["cloth_light"], [
            (cx - 3, cy - 6), (cx - 1, cy - 8),
            (cx + 1, cy - 8), (cx + 3, cy - 6),
            (cx + 2, cy - 3), (cx - 2, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["cloth_shine"],
                         (cx - 1, cy - 7, 2, 1))
    # ── BACK ARM ─────────────────────────────────────────────
    def _draw_back_arm(surface, cx, cy, facing, phase, action, progress):
        back = -facing
        sx = cx + back * 10
        sy = cy - 8
        sway = math.sin(phase * 0.7) * 2
        ex = sx + back * 6
        ey = sy + 10 + int(sway)
        hx = ex + back * 3
        hy = ey + 8
        # Upper arm
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["shadow_deep"],
                            (sx + 1, sy + 2), (ex + 1, ey + 2), 7)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["cloth_darkest"],
                            (sx, sy), (ex, ey), 6)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["cloth_dark"],
                            (sx, sy), (ex, ey), 4)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["cloth_mid"],
                            (sx, sy - 1), (ex, ey - 1), 2)
        # Forearm (wrapping)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["shadow_deep"],
                            (ex + 1, ey + 2), (hx + 1, hy + 2), 6)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["wrap_darkest"],
                            (ex, ey), (hx, hy), 5)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["wrap_dark"],
                            (ex, ey), (hx, hy), 4)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["wrap_mid"],
                            (ex, ey - 1), (hx, hy - 1), 2)
        # Wrap bands
        for i in range(3):
            t = i / 3
            bx = int(ex + (hx - ex) * t)
            by = int(ey + (hy - ey) * t)
            pygame.draw.line(surface, _NS_zhaeris.PALETTE["wrap_light"],
                             (bx - 2, by), (bx + 2, by), 1)
        # Fist
        _NS_zhaeris._aacircle(surface, _NS_zhaeris.PALETTE["shadow_deep"],
                              (hx + 1, hy + 1), 4)
        _NS_zhaeris._aacircle(surface, _NS_zhaeris.PALETTE["skin_darkest"],
                              (hx, hy), 4)
        _NS_zhaeris._aacircle(surface, _NS_zhaeris.PALETTE["skin_dark"],
                              (hx, hy), 3)
        _NS_zhaeris._aacircle(surface, _NS_zhaeris.PALETTE["skin_mid"],
                              (hx - 1, hy - 1), 2)
        # Small kama in back hand
        _NS_zhaeris._draw_kama_small(surface, hx, hy, back, phase)
    # ── FRONT ARM + KAMA (swings during attack) ──────────────
    def _draw_front_arm_kama(surface, cx, cy, facing, phase, action, progress):
        base_angle = -math.pi / 6
        if action == "attack":
            if progress < 0.35:
                t = progress / 0.35
                base_angle = -math.pi / 6 - t * math.pi / 2.5
            elif progress < 0.6:
                t = (progress - 0.35) / 0.25
                base_angle = -math.pi / 6 - math.pi / 2.5 + t * (math.pi * 1.1)
            else:
                t = (progress - 0.6) / 0.4
                base_angle = (
                    -math.pi / 6 + math.pi * 0.7 - t * (math.pi * 0.7 + math.pi / 6)
                )
                base_angle = -math.pi / 6 + (math.pi * 0.7 * (1 - t))
        else:
            base_angle += math.sin(phase * 0.6) * 0.08
        sx = cx + facing * 10
        sy = cy - 8
        arm_len = 18
        hx = sx + int(math.cos(base_angle) * arm_len) * facing
        hy = sy + int(math.sin(base_angle) * arm_len)
        ex = sx + int(math.cos(base_angle) * arm_len * 0.5) * facing
        ey = sy + int(math.sin(base_angle) * arm_len * 0.5) + 2
        # Upper arm
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["shadow_deep"],
                            (sx + 1, sy + 2), (ex + 1, ey + 2), 8)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["cloth_darkest"],
                            (sx, sy), (ex, ey), 7)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["cloth_dark"],
                            (sx, sy), (ex, ey), 5)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["cloth_mid"],
                            (sx, sy - 1), (ex, ey - 1), 3)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["cloth_light"],
                            (sx, sy - 1), (ex, ey - 1), 1)
        # Forearm (wrapping + tattoo)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["shadow_deep"],
                            (ex + 1, ey + 2), (hx + 1, hy + 2), 7)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["wrap_darkest"],
                            (ex, ey), (hx, hy), 6)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["wrap_dark"],
                            (ex, ey), (hx, hy), 4)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["wrap_mid"],
                            (ex, ey - 1), (hx, hy - 1), 2)
        # Tattoo marks on forearm
        for i in range(3):
            t = 0.2 + i * 0.25
            tx = int(ex + (hx - ex) * t)
            ty = int(ey + (hy - ey) * t)
            pygame.draw.rect(surface, _NS_zhaeris.PALETTE["energy_dark"],
                             (tx, ty, 2, 1))
            pygame.draw.rect(surface, _NS_zhaeris.PALETTE["energy_mid"],
                             (tx, ty, 1, 1))
        # Wrap bands
        for i in range(3):
            t = i / 3
            bx = int(ex + (hx - ex) * t)
            by = int(ey + (hy - ey) * t)
            pygame.draw.line(surface, _NS_zhaeris.PALETTE["wrap_light"],
                             (bx - 2, by), (bx + 2, by), 1)
        # Hand
        _NS_zhaeris._aacircle(surface, _NS_zhaeris.PALETTE["shadow_deep"],
                              (hx + 1, hy + 1), 4)
        _NS_zhaeris._aacircle(surface, _NS_zhaeris.PALETTE["skin_darkest"],
                              (hx, hy), 4)
        _NS_zhaeris._aacircle(surface, _NS_zhaeris.PALETTE["skin_dark"],
                              (hx, hy), 3)
        _NS_zhaeris._aacircle(surface, _NS_zhaeris.PALETTE["skin_mid"],
                              (hx - 1, hy - 1), 2)
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["skin_light"],
                         (hx - 1, hy - 1, 1, 1))
        # KAMA WEAPON
        _NS_zhaeris._draw_kama(surface, hx, hy, facing, phase, base_angle)
    # ── KAMA WEAPONS ─────────────────────────────────────────
    def _draw_kama(surface, hx, hy, facing, phase, arm_angle):
        """Large kama (sickle blade) in main hand."""
        # Handle along arm direction
        h_len = 8
        h_ex = hx + int(math.cos(arm_angle) * h_len) * facing
        h_ey = hy + int(math.sin(arm_angle) * h_len)
        # Handle
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["shadow_deep"],
                            (hx + 1, hy + 1), (h_ex + 1, h_ey + 1), 4)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["wrap_darkest"],
                            (hx, hy), (h_ex, h_ey), 3)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["wrap_dark"],
                            (hx, hy), (h_ex, h_ey), 2)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["wrap_mid"],
                            (hx, hy), (h_ex, h_ey), 1)
        # Blade: curves perpendicular to handle
        blade_angle = arm_angle - math.pi / 2 * facing
        b_len = 12
        b_tip_x = h_ex + int(math.cos(blade_angle) * b_len) * facing
        b_tip_y = h_ey + int(math.sin(blade_angle) * b_len)
        b_mid_x = h_ex + int(math.cos(blade_angle) * b_len * 0.6) * facing
        b_mid_y = h_ey + int(math.sin(blade_angle) * b_len * 0.6)
        # Perpendicular for blade width
        perp = blade_angle + math.pi / 2
        w = 3
        # Blade shape (crescent)
        pts = [
            (h_ex, h_ey),
            (b_mid_x + int(math.cos(perp) * w), b_mid_y + int(math.sin(perp) * w)),
            (b_tip_x, b_tip_y),
            (b_mid_x - int(math.cos(perp) * 1), b_mid_y - int(math.sin(perp) * 1)),
        ]
        _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in pts])
        _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["blade_darkest"], pts)
        # Inner blade
        inner = [
            (h_ex, h_ey),
            (b_mid_x + int(math.cos(perp) * (w - 1)),
             b_mid_y + int(math.sin(perp) * (w - 1))),
            (b_tip_x, b_tip_y),
        ]
        _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["blade_dark"], inner)
        # Bright edge
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["blade_mid"],
                            (h_ex, h_ey), (b_tip_x, b_tip_y), 1)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["blade_light"],
                            (b_mid_x, b_mid_y), (b_tip_x, b_tip_y), 1)
        # Green energy glow on edge
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["energy_dark"],
                            (b_mid_x, b_mid_y), (b_tip_x, b_tip_y), 1)
        for r in range(4, 0, -1):
            a = _NS_zhaeris._alpha(100 * (4 - r) / 4)
            _NS_zhaeris._aacircle(surface, (*_NS_zhaeris.PALETTE["energy_mid"], a),
                                  (b_tip_x, b_tip_y), r)
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["energy_hot"],
                         (b_tip_x, b_tip_y, 1, 1))
    def _draw_kama_small(surface, hx, hy, facing, phase):
        """Small kama in off-hand."""
        angle = math.pi / 4
        h_len = 6
        h_ex = hx + int(math.cos(angle) * h_len) * facing
        h_ey = hy + int(math.sin(angle) * h_len)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["wrap_darkest"],
                            (hx, hy), (h_ex, h_ey), 2)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["wrap_mid"],
                            (hx, hy), (h_ex, h_ey), 1)
        blade_angle = angle - math.pi / 2 * facing
        b_len = 9
        b_tip_x = h_ex + int(math.cos(blade_angle) * b_len) * facing
        b_tip_y = h_ey + int(math.sin(blade_angle) * b_len)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["blade_darkest"],
                            (h_ex, h_ey), (b_tip_x, b_tip_y), 2)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["blade_mid"],
                            (h_ex, h_ey), (b_tip_x, b_tip_y), 1)
        _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["energy_dark"],
                            (h_ex, h_ey), (b_tip_x, b_tip_y), 1)
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["energy_light"],
                         (b_tip_x, b_tip_y, 1, 1))
    # ── HEAD + MASK ──────────────────────────────────────────
    def _draw_head(surface, cx, cy, facing, phase):
        hx = cx + facing * 2
        hy = cy - 20
        # Head shape
        head = [
            (hx - 7, hy + 3), (hx - 8, hy - 1), (hx - 6, hy - 6),
            (hx - 2, hy - 8), (hx + 3, hy - 8), (hx + 7, hy - 5),
            (hx + 8, hy), (hx + 7, hy + 4), (hx + 4, hy + 6),
            (hx - 2, hy + 6), (hx - 5, hy + 5),
        ]
        _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in head])
        _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["skin_darkest"], head)
        # Upper face (visible)
        _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["skin_dark"], [
            (hx - 6, hy - 2), (hx - 5, hy - 5), (hx - 1, hy - 7),
            (hx + 3, hy - 7), (hx + 6, hy - 4), (hx + 7, hy),
            (hx + 5, hy + 1), (hx - 4, hy + 1),
        ])
        _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["skin_mid"], [
            (hx - 4, hy - 3), (hx - 2, hy - 5), (hx + 2, hy - 5),
            (hx + 5, hy - 2), (hx + 4, hy), (hx - 3, hy),
        ])
        _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["skin_light"], [
            (hx - 1, hy - 4), (hx + 2, hy - 4),
            (hx + 3, hy - 2), (hx - 2, hy - 2),
        ])
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["skin_shine"],
                         (hx, hy - 4, 2, 1))
        # MASK (lower face)
        mask_pts = [
            (hx - 7, hy + 1), (hx + 7, hy + 1), (hx + 7, hy + 4),
            (hx + 4, hy + 6), (hx - 2, hy + 6), (hx - 5, hy + 5),
            (hx - 7, hy + 3),
        ]
        _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["cloth_darkest"], mask_pts)
        _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["cloth_dark"], [
            (hx - 6, hy + 2), (hx + 6, hy + 2), (hx + 6, hy + 3),
            (hx + 3, hy + 5), (hx - 2, hy + 5), (hx - 6, hy + 3),
        ])
        # Mask detail line
        pygame.draw.line(surface, _NS_zhaeris.PALETTE["cloth_mid"],
                         (hx - 5, hy + 3), (hx + 5, hy + 3), 1)
        # Green energy accent on mask edge
        pygame.draw.line(surface, _NS_zhaeris.PALETTE["energy_darkest"],
                         (hx - 6, hy + 1), (hx + 6, hy + 1), 1)
        # EYES (narrow, sharp, green glow)
        _NS_zhaeris._draw_ninja_eye(surface, hx + facing * 2, hy - 2, facing, phase)
    def _draw_ninja_eye(surface, ex, ey, facing, phase):
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        # Socket
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["eye_socket"],
                         (ex - 2, ey - 1, 5, 3))
        # Glow halo
        for r in range(6, 0, -1):
            a = _NS_zhaeris._alpha(70 * (6 - r) / 6 * pulse)
            _NS_zhaeris._aacircle(surface, (*_NS_zhaeris.PALETTE["energy_mid"], a),
                                  (ex + 1, ey), r)
        # Narrow eye shape (horizontal)
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["eye_dark"],
                         (ex - 1, ey - 1, 4, 2))
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["eye_mid"],
                         (ex, ey - 1, 3, 2))
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["eye_light"],
                         (ex + 1, ey, 1, 1))
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["eye_glow"],
                         (ex + 1, ey - 1, 1, 1))
        # Sharp corners
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["eye_dark"],
                         (ex - 2, ey, 1, 1))
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["eye_mid"],
                         (ex + 3, ey, 1, 1))
    # ── HAIR ─────────────────────────────────────────────────
    def _draw_hair_back(surface, cx, cy, facing, phase):
        """Flowing dark hair behind body — multiple animated strands."""
        hx = cx + facing * 2
        hy = cy - 20
        strands = [
            (-4, -7, 0.0, 28, 5),
            (-2, -8, 0.3, 30, 6),
            (0, -8, 0.6, 32, 6),
            (2, -7, 0.9, 28, 5),
            (4, -6, 1.2, 24, 4),
            (-5, -5, 0.5, 22, 4),
            (5, -5, 1.5, 20, 3),
        ]
        for (ox, oy, ph_off, length, base_w) in strands:
            pts = []
            seg = 7
            for j in range(seg + 1):
                t = j / seg
                sx = hx + ox - int(facing * t * length * 0.6)
                sy = hy + oy + int(t * length * 0.75)
                wave = math.sin(phase * 1.3 + ph_off + t * math.pi * 1.8)
                sx += int(wave * (2 + t * 5)) * (-facing)
                sy += int(math.sin(phase * 0.8 + ph_off + t * 1.5) * 2)
                pts.append((sx, sy))
            for j in range(len(pts) - 1):
                thick = max(1, base_w - j)
                _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["shadow_deep"],
                                    (pts[j][0] + 1, pts[j][1] + 1),
                                    (pts[j + 1][0] + 1, pts[j + 1][1] + 1),
                                    thick + 1)
                _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["hair_darkest"],
                                    pts[j], pts[j + 1], thick)
                _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["hair_dark"],
                                    pts[j], pts[j + 1], max(1, thick - 1))
                if thick > 2:
                    _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["hair_mid"],
                                        (pts[j][0], pts[j][1] - 1),
                                        (pts[j + 1][0], pts[j + 1][1] - 1),
                                        max(1, thick - 3))
            # Green energy wisp along some strands
            if base_w >= 5 and len(pts) > 3:
                for j in range(2, len(pts) - 1, 2):
                    a = _NS_zhaeris._alpha(
                        140 * (1 - j / len(pts))
                        * (0.5 + 0.5 * math.sin(phase * 2 + ph_off))
                    )
                    pygame.draw.rect(
                        surface,
                        (*_NS_zhaeris.PALETTE["energy_dark"], a),
                        (pts[j][0], pts[j][1], 2, 1),
                    )
                    pygame.draw.rect(
                        surface,
                        (*_NS_zhaeris.PALETTE["energy_mid"], a),
                        (pts[j][0], pts[j][1], 1, 1),
                    )
    def _draw_hair_front(surface, cx, cy, facing, phase):
        """Front bangs/fringe over forehead."""
        hx = cx + facing * 2
        hy = cy - 20
        # Short bangs
        bangs = [
            (facing * 3, -7, 0.2, 6),
            (facing * 5, -6, 0.5, 8),
            (facing * 1, -8, 0.8, 5),
            (-facing * 1, -7, 0.0, 6),
        ]
        for (ox, oy, ph_off, length) in bangs:
            bx = hx + ox
            by = hy + oy
            wave = math.sin(phase * 1.0 + ph_off) * 1
            tip_x = bx + int(facing * 2 + wave)
            tip_y = by + length
            _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["hair_darkest"],
                                (bx, by), (tip_x, tip_y), 3)
            _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["hair_dark"],
                                (bx, by), (tip_x, tip_y), 2)
            _NS_zhaeris._aaline(surface, _NS_zhaeris.PALETTE["hair_mid"],
                                (bx, by - 1), (tip_x, tip_y - 1), 1)
            pygame.draw.rect(surface, _NS_zhaeris.PALETTE["hair_light"],
                             (tip_x, tip_y, 1, 1))
    # ── SCARF (flowing behind) ───────────────────────────────
    def _draw_scarf(surface, cx, cy, facing, phase, action):
        base_x = cx - facing * 2
        base_y = cy - 14
        seg = 7
        pts_t = []
        pts_b = []
        for i in range(seg + 1):
            t = i / seg
            sx = base_x - int(facing * t * 26)
            sy = base_y + int(t * 10)
            wave = math.sin(phase * 1.6 + t * math.pi * 1.5) * (2 + t * 5)
            sy += int(wave)
            w = int(4 * (1 - t * 0.5))
            pts_t.append((sx, sy - w))
            pts_b.append((sx, sy + w))
        full = pts_t + list(reversed(pts_b))
        if len(full) >= 3:
            _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 2) for p in full])
            _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["cloth_darkest"], full)
            inner = pts_t[:-1] + list(reversed(pts_b[:-1]))
            if len(inner) >= 3:
                _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["cloth_dark"], inner)
        # Green edge
        for i in range(len(pts_t) - 1):
            a = _NS_zhaeris._alpha(200 * (1 - i / len(pts_t)))
            pygame.draw.line(surface,
                             (*_NS_zhaeris.PALETTE["energy_dark"], a),
                             pts_t[i], pts_t[i + 1], 1)
        # Tip glow
        if pts_t:
            tip = pts_t[-1]
            pygame.draw.rect(surface, _NS_zhaeris.PALETTE["energy_mid"],
                             (tip[0], tip[1], 2, 2))
            pygame.draw.rect(surface, _NS_zhaeris.PALETTE["energy_light"],
                             (tip[0], tip[1], 1, 1))
    # ============================================================
    # SWING TRAIL + IMPACT (melee kama attack)
    # ============================================================
    def _get_kama_tip(cx, cy, facing, progress):
        if progress < 0.35:
            t = progress / 0.35
            angle = -math.pi / 6 - t * math.pi / 2.5
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            angle = -math.pi / 6 - math.pi / 2.5 + t * (math.pi * 1.1)
        else:
            t = (progress - 0.6) / 0.4
            angle = -math.pi / 6 + (math.pi * 0.7 * (1 - t))
        sx = cx + facing * 10
        sy = cy - 8
        arm_len = 18
        hx = sx + int(math.cos(angle) * arm_len) * facing
        hy = sy + int(math.sin(angle) * arm_len)
        kama_off = 18
        blade_angle = angle - math.pi / 2 * facing
        kx = hx + int(math.cos(blade_angle) * kama_off) * facing
        ky = hy + int(math.sin(blade_angle) * kama_off)
        return kx, ky, angle
    def _draw_swing_trail(surface, boss, cx, cy, facing, progress):
        if progress < 0.3 or progress > 0.75:
            return
        if progress < 0.35:
            intensity = (progress - 0.3) / 0.05
        elif progress < 0.6:
            intensity = 1.0
        else:
            intensity = max(0, 1 - (progress - 0.6) / 0.15)
        intensity = max(0.0, min(1.0, intensity))
        if intensity <= 0:
            return
        num = 14
        trail = []
        for i in range(num):
            sp = progress - (i / num) * 0.22
            if sp < 0.3:
                continue
            kx, ky, ang = _NS_zhaeris._get_kama_tip(cx, cy, facing, sp)
            trail.append((kx, ky, ang, i))
        if len(trail) < 2:
            return
        trail.reverse()
        ts = pygame.Surface((280, 280), pygame.SRCALPHA)
        ox = cx - 140
        oy = cy - 140
        layers = [
            (_NS_zhaeris.PALETTE["energy_darkest"], 14, 100),
            (_NS_zhaeris.PALETTE["energy_dark"], 10, 140),
            (_NS_zhaeris.PALETTE["energy_mid"], 6, 190),
            (_NS_zhaeris.PALETTE["energy_light"], 3, 230),
            (_NS_zhaeris.PALETTE["energy_hot"], 1, 255),
        ]
        for color, max_w, max_a in layers:
            for i in range(len(trail) - 1):
                p1, p2 = trail[i], trail[i + 1]
                fade = 1.0 - (p1[3] / num)
                a = _NS_zhaeris._alpha(max_a * fade * intensity)
                w = max(1, int(max_w * fade))
                if a > 0:
                    pygame.draw.line(
                        ts, (*color, a),
                        (p1[0] - ox, p1[1] - oy),
                        (p2[0] - ox, p2[1] - oy), w,
                    )
        # Sparkles
        for i, (kx, ky, ang, idx) in enumerate(trail):
            fade = 1.0 - (idx / num)
            a = _NS_zhaeris._alpha(240 * fade * intensity)
            if a <= 0 or i % 2 == 0:
                continue
            perp = ang + math.pi / 2
            for s in range(2):
                d = 4 + s * 3
                sign = 1 if s == 0 else -1
                spx = kx - ox + int(math.cos(perp) * d * sign)
                spy = ky - oy + int(math.sin(perp) * d * sign)
                pygame.draw.rect(ts, (*_NS_zhaeris.PALETTE["energy_hot"], a),
                                 (spx, spy, 2, 2))
                pygame.draw.rect(ts, (*_NS_zhaeris.PALETTE["energy_shine"], a),
                                 (spx, spy, 1, 1))
        surface.blit(ts, (ox, oy))
        # Leading glow
        if trail:
            lead = trail[0]
            for r in range(8, 1, -2):
                a = _NS_zhaeris._alpha(140 * (8 - r) / 8 * intensity)
                _NS_zhaeris._aacircle(
                    surface, (*_NS_zhaeris.PALETTE["energy_mid"], a),
                    (lead[0], lead[1]), r,
                )
            _NS_zhaeris._aacircle(surface, _NS_zhaeris.PALETTE["energy_hot"],
                                  (lead[0], lead[1]), 2)
    def _draw_swing_impact(surface, boss, cx, cy, facing, progress):
        if progress < 0.55 or progress > 0.7:
            return
        t = (progress - 0.55) / 0.15
        inten = math.sin(t * math.pi)
        kx, ky, _ = _NS_zhaeris._get_kama_tip(cx, cy, facing, progress)
        ix = kx + facing * 4
        iy = ky
        r = int(4 + t * 12)
        a = _NS_zhaeris._alpha(240 * inten)
        for rr in range(r + 3, 0, -2):
            ra = _NS_zhaeris._alpha(a * (r + 3 - rr) / (r + 3))
            _NS_zhaeris._aacircle(surface, (*_NS_zhaeris.PALETTE["energy_dark"], ra),
                                  (ix, iy), rr)
        _NS_zhaeris._aacircle(surface, (*_NS_zhaeris.PALETTE["energy_mid"], a),
                              (ix, iy), max(2, r - 4))
        _NS_zhaeris._aacircle(surface, (*_NS_zhaeris.PALETTE["energy_light"], a),
                              (ix, iy), max(1, r - 7))
        _NS_zhaeris._aacircle(surface, (*_NS_zhaeris.PALETTE["energy_hot"], a),
                              (ix, iy), max(1, r - 10))
        for i in range(6):
            ang = i * math.pi / 3 + progress * 4
            ex = ix + int(math.cos(ang) * r)
            ey = iy + int(math.sin(ang) * r)
            pygame.draw.line(surface, (*_NS_zhaeris.PALETTE["energy_light"], a),
                             (ix, iy), (ex, ey), 1)
            pygame.draw.rect(surface, (*_NS_zhaeris.PALETTE["energy_hot"], a),
                             (ex, ey, 2, 2))
    # ============================================================
    # AMBIENT / FLOATING EFFECTS
    # ============================================================
    def _draw_shadow(surface, x, y):
        sh = pygame.Surface((120, 24), pygame.SRCALPHA)
        for r in range(12, 0, -1):
            a = max(0, (12 - r) * 18)
            pygame.draw.ellipse(sh, (0, 0, 0, a),
                                (10 - r, 12 - r, 100 + r * 2, r * 2))
        pygame.draw.ellipse(sh, (3, 5, 2, 150), (8, 6, 104, 12))
        surface.blit(sh, (x - 60, y - 12))
    def _draw_energy_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((200, 160), pygame.SRCALPHA)
        for r in range(80, 5, -5):
            a = _NS_zhaeris._alpha((80 - r) * 1.0 * pulse)
            if a > 0:
                _NS_zhaeris._aacircle(aura, (*_NS_zhaeris.PALETTE["energy_darkest"], a),
                                      (100, 80), r)
        for r in range(45, 5, -3):
            a = _NS_zhaeris._alpha((45 - r) * 1.3 * pulse)
            if a > 0:
                _NS_zhaeris._aacircle(aura, (*_NS_zhaeris.PALETTE["energy_dark"], a),
                                      (100, 80), r)
        surface.blit(aura, (x - 100, y - 80))
        for i in range(10):
            ang = phase * 0.4 + i * math.pi / 5
            rd = 35 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(ang) * rd)
            sy = y - 5 + int(math.sin(ang) * rd * 0.4)
            pygame.draw.rect(surface, _NS_zhaeris.PALETTE["energy_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_zhaeris.PALETTE["energy_hot"],
                             (sx, sy, 1, 1))
    def _draw_float_wisps(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        strength = 1.4 if intense else 1.0
        mist = pygame.Surface((130, 34), pygame.SRCALPHA)
        p = math.sin(phase * 1.2) * 0.25 + 0.75
        for r in range(24, 3, -2):
            a = _NS_zhaeris._alpha((24 - r) * 3.2 * p * strength)
            if a > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_zhaeris.PALETTE["energy_darkest"], a),
                    (65 - r * 2, 17 - r // 3, r * 4, max(3, r // 2)),
                )
        for r in range(14, 3, -2):
            a = _NS_zhaeris._alpha((14 - r) * 4 * p * strength)
            if a > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_zhaeris.PALETTE["energy_dark"], a),
                    (65 - r, 17 - r // 4, r * 2, max(2, r // 3)),
                )
        surface.blit(mist, (cx - 65, cy - 10))
        for i in range(6):
            t = (phase * 0.5 + i * 0.16) % 1.0
            sx = cx - 18 + i * 7 + int(math.sin(phase + i) * 3)
            sy = cy - int(t * 18)
            a = _NS_zhaeris._alpha(200 * (1 - t) * strength)
            if a > 0:
                _NS_zhaeris._aacircle(surface,
                                      (*_NS_zhaeris.PALETTE["energy_dark"], a),
                                      (sx, sy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_zhaeris.PALETTE["energy_mid"], a),
                                 (sx, sy, 1, 1))
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 10 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                a = _NS_zhaeris._alpha(130 - i * 25)
                if a > 0:
                    _NS_zhaeris._aacircle(
                        surface, (*_NS_zhaeris.PALETTE["energy_dark"], a),
                        (sx, sy), max(2, 5 - i),
                    )
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((150, 44), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_zhaeris.PALETTE["energy_darkest"], 180),
                            (5, 14, 140, 22), 3)
        pygame.draw.ellipse(ring, (*_NS_zhaeris.PALETTE["energy_dark"], 200),
                            (15, 16, 120, 18), 2)
        pygame.draw.ellipse(ring, (*_NS_zhaeris.PALETTE["energy_mid"], 180),
                            (25, 18, 100, 14), 1)
        for i in range(8):
            ang = phase * 0.4 + i * math.pi / 4
            x1 = 75 + int(math.cos(ang) * 40)
            y1 = 24 + int(math.sin(ang) * 7)
            x2 = 75 + int(math.cos(ang) * 62)
            y2 = 24 + int(math.sin(ang) * 10)
            pygame.draw.line(ring, (*_NS_zhaeris.PALETTE["energy_light"], 200),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(
                ring, (*_NS_zhaeris.PALETTE["energy_hot"],
                       _NS_zhaeris._alpha(130 * pulse)),
                (10, 8, 130, 32), 1,
            )
        surface.blit(ring, (x - 75, y - 22))
    # ============================================================
    # SKILL Q — FIVE POINT STRIKE (5 kunai fan)
    # ============================================================
    def _draw_fivepointstrike(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_zhaeris._target_position(boss, x, y)
        base_angle = math.atan2(ty - y, (tx - x) * facing)
        if progress < 0.2:
            # Charge
            t = progress / 0.2
            cr = int(3 + t * 6)
            mx = x + facing * 20
            my = y - 12
            for r in range(cr + 4, 0, -1):
                a = _NS_zhaeris._alpha(180 * (cr + 4 - r) / (cr + 4))
                _NS_zhaeris._aacircle(surface,
                                      (*_NS_zhaeris.PALETTE["energy_dark"], a),
                                      (mx, my), r)
            _NS_zhaeris._aacircle(surface, _NS_zhaeris.PALETTE["energy_light"],
                                  (mx, my), max(1, cr - 2))
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 22
            start_y = y - 12
            spread = math.pi / 7
            for k_i in range(5):
                angle_off = (k_i - 2) * spread
                kang = base_angle + angle_off
                dist = math.sqrt((tx - start_x) ** 2 + (ty - start_y) ** 2) * 1.2
                kx = int(start_x + math.cos(kang) * dist * t * facing)
                ky = int(start_y + math.sin(kang) * dist * t)
                is_center = k_i == 2
                size = 4 if is_center else 3
                # Trail
                for ti in range(5):
                    tt = max(0.0, t - ti * 0.05)
                    px = int(start_x + math.cos(kang) * dist * tt * facing)
                    py = int(start_y + math.sin(kang) * dist * tt)
                    a = _NS_zhaeris._alpha(200 - ti * 35)
                    s = max(1, size - ti)
                    _NS_zhaeris._aacircle(
                        surface, (*_NS_zhaeris.PALETTE["energy_dark"], a),
                        (px, py), s,
                    )
                # Kunai head (diamond)
                _NS_zhaeris._draw_kunai(surface, kx, ky, kang * facing, is_center)
                # Glow
                for r in range(size + 3, 0, -1):
                    a = _NS_zhaeris._alpha(80 * (size + 3 - r) / (size + 3))
                    _NS_zhaeris._aacircle(
                        surface, (*_NS_zhaeris.PALETTE["energy_mid"], a),
                        (kx, ky), r,
                    )
            # Impact
            if t > 0.88:
                st = (t - 0.88) / 0.12
                r = int(8 + st * 22)
                a = _NS_zhaeris._alpha(240 * (1 - st))
                _NS_zhaeris._aacircle(
                    surface, (*_NS_zhaeris.PALETTE["energy_dark"], a),
                    (tx, ty), r, 3,
                )
                _NS_zhaeris._aacircle(
                    surface, (*_NS_zhaeris.PALETTE["energy_mid"], a),
                    (tx, ty), max(1, r - 5), 2,
                )
                for i in range(8):
                    ea = i * math.pi / 4
                    ex = tx + int(math.cos(ea) * r)
                    ey = ty + int(math.sin(ea) * r * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_zhaeris.PALETTE["energy_hot"], a),
                                     (ex, ey, 2, 2))
    def _draw_kunai(surface, kx, ky, angle, center=False):
        """Small kunai (diamond blade + handle)."""
        bl = 6 if center else 5
        bw = 2 if center else 1
        tip_x = kx + int(math.cos(angle) * bl)
        tip_y = ky + int(math.sin(angle) * bl)
        back_x = kx - int(math.cos(angle) * 3)
        back_y = ky - int(math.sin(angle) * 3)
        perp = angle + math.pi / 2
        sx1 = kx + int(math.cos(perp) * bw)
        sy1 = ky + int(math.sin(perp) * bw)
        sx2 = kx - int(math.cos(perp) * bw)
        sy2 = ky - int(math.sin(perp) * bw)
        _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["metal_dark"],
                          [(tip_x, tip_y), (sx1, sy1), (back_x, back_y),
                           (sx2, sy2)])
        _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["metal_mid"],
                          [(tip_x, tip_y), (kx, ky), (back_x, back_y)])
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["metal_shine"],
                         (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["energy_light"],
                         (tip_x, tip_y, 1, 1))
    # ============================================================
    # SKILL W — TWILIGHT SHROUD (expanding smoke cloud)
    # ============================================================
    def _draw_twilightshroud_ground(surface, boss, x, y, timer, phase):
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 2.5))
        if r < 5:
            return
        # Dark smoke pool
        for layer_r in range(r, 5, -5):
            a = _NS_zhaeris._alpha((r - layer_r + 5) * 3)
            pygame.draw.ellipse(
                surface, (*_NS_zhaeris.PALETTE["smoke_darkest"], a),
                (x - layer_r, y + 35 - layer_r // 3,
                 layer_r * 2, layer_r * 2 // 3),
            )
        pygame.draw.ellipse(
            surface, (*_NS_zhaeris.PALETTE["smoke_dark"], 140),
            (x - r + 5, y + 35 - r // 3 + 2, r * 2 - 10, r * 2 // 3 - 4),
        )
    def _draw_twilightshroud_overlay(surface, boss, x, y, timer, phase):
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 2.5))
        if r < 8:
            return
        smoke = pygame.Surface((r * 2 + 30, r * 2 + 30), pygame.SRCALPHA)
        c = (r + 15, r + 15)
        # Billowing smoke
        for i in range(10):
            ang = phase * 0.4 + i * math.pi / 5
            dist = int(r * (0.4 + (i % 3) * 0.2))
            sx = c[0] + int(math.cos(ang) * dist)
            sy = c[1] + int(math.sin(ang) * dist * 0.6)
            sr = int(r * 0.35 + math.sin(phase + i) * 5)
            a = _NS_zhaeris._alpha(120 + math.sin(phase * 2 + i) * 30)
            _NS_zhaeris._aacircle(smoke, (*_NS_zhaeris.PALETTE["smoke_dark"], a),
                                  (sx, sy), sr)
            _NS_zhaeris._aacircle(smoke, (*_NS_zhaeris.PALETTE["smoke_mid"], a // 2),
                                  (sx, sy), max(1, sr - 4))
        # Edge wisps
        for i in range(14):
            ang = phase * 0.6 + i * math.pi / 7
            ex = c[0] + int(math.cos(ang) * r)
            ey = c[1] + int(math.sin(ang) * r * 0.6)
            pygame.draw.rect(smoke, _NS_zhaeris.PALETTE["smoke_light"],
                             (ex, ey, 2, 2))
        # Green energy wisps in smoke
        for i in range(6):
            ang = phase * 0.8 + i * math.pi / 3
            gx = c[0] + int(math.cos(ang) * r * 0.5)
            gy = c[1] + int(math.sin(ang) * r * 0.3)
            a = _NS_zhaeris._alpha(
                160 * (0.5 + 0.5 * math.sin(phase * 3 + i))
            )
            _NS_zhaeris._aacircle(smoke,
                                  (*_NS_zhaeris.PALETTE["energy_dark"], a),
                                  (gx, gy), 3)
            pygame.draw.rect(smoke, (*_NS_zhaeris.PALETTE["energy_mid"], a),
                             (gx, gy, 1, 1))
        surface.blit(smoke, (x - r - 15, y - r - 15))
    # ============================================================
    # SKILL E — SHURIKEN FLIP (spinning shuriken projectile)
    # ============================================================
    def _draw_shurikenflip(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_zhaeris._target_position(boss, x, y)
        if progress < 0.15:
            return
        t = (progress - 0.15) / 0.85
        t = min(1.0, t)
        sx_start = x + facing * 20
        sy_start = y - 10
        bx = int(sx_start + (tx - sx_start) * t)
        by = int(sy_start + (ty - sy_start) * t)
        # Trail
        for i in range(7):
            tt = max(0.0, t - i * 0.05)
            px = int(sx_start + (tx - sx_start) * tt)
            py = int(sy_start + (ty - sy_start) * tt)
            a = _NS_zhaeris._alpha(210 - i * 28)
            s = max(1, 6 - i)
            _NS_zhaeris._aacircle(surface,
                                  (*_NS_zhaeris.PALETTE["energy_dark"], a),
                                  (px, py), s)
            _NS_zhaeris._aacircle(surface,
                                  (*_NS_zhaeris.PALETTE["energy_mid"], a),
                                  (px, py), max(1, s - 2))
        # Spinning shuriken
        _NS_zhaeris._draw_shuriken(surface, bx, by, phase * 5 + t * 12)
        # Aura
        for r in range(10, 3, -2):
            a = _NS_zhaeris._alpha(120 * (10 - r) / 10)
            _NS_zhaeris._aacircle(surface,
                                  (*_NS_zhaeris.PALETTE["energy_mid"], a),
                                  (bx, by), r)
        # Impact
        if t > 0.9:
            st = (t - 0.9) / 0.1
            ir = int(8 + st * 20)
            ia = _NS_zhaeris._alpha(240 * (1 - st))
            _NS_zhaeris._aacircle(surface,
                                  (*_NS_zhaeris.PALETTE["energy_dark"], ia),
                                  (tx, ty), ir, 3)
            _NS_zhaeris._aacircle(surface,
                                  (*_NS_zhaeris.PALETTE["energy_mid"], ia),
                                  (tx, ty), max(1, ir - 4), 2)
            for i in range(6):
                ea = i * math.pi / 3
                ex = tx + int(math.cos(ea) * ir)
                ey = ty + int(math.sin(ea) * ir * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_zhaeris.PALETTE["energy_hot"], ia),
                                 (ex, ey, 2, 2))
    def _draw_shuriken(surface, sx, sy, rotation):
        """4-pointed star shuriken."""
        for i in range(4):
            ang = rotation + i * math.pi / 2
            tx = sx + int(math.cos(ang) * 8)
            ty = sy + int(math.sin(ang) * 8)
            perp = ang + math.pi / 2
            w = 2
            p1 = (sx + int(math.cos(perp) * w), sy + int(math.sin(perp) * w))
            p2 = (sx - int(math.cos(perp) * w), sy - int(math.sin(perp) * w))
            _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["metal_dark"],
                              [(tx, ty), p1, p2])
            _NS_zhaeris._poly(surface, _NS_zhaeris.PALETTE["metal_mid"],
                              [(tx, ty), (sx, sy), p1])
            pygame.draw.rect(surface, _NS_zhaeris.PALETTE["metal_shine"],
                             (tx, ty, 1, 1))
            pygame.draw.rect(surface, _NS_zhaeris.PALETTE["energy_light"],
                             (tx, ty, 1, 1))
        _NS_zhaeris._aacircle(surface, _NS_zhaeris.PALETTE["metal_dark"],
                              (sx, sy), 2)
        _NS_zhaeris._aacircle(surface, _NS_zhaeris.PALETTE["metal_light"],
                              (sx, sy), 1)
    # ============================================================
    # SKILL R — PERFECT EXECUTION (dash + X slash)
    # ============================================================
    def _draw_perfectexec_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_zhaeris._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.5:
            t = (progress - 0.5) / 0.5
            r = int(25 + t * 30)
            a = _NS_zhaeris._alpha(220 * (1 - t * 0.3))
            pygame.draw.ellipse(surface,
                                (*_NS_zhaeris.PALETTE["energy_darkest"], a),
                                (tx - r, ty + 35 - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_zhaeris.PALETTE["energy_dark"], a),
                                (tx - r + 4, ty + 35 - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4))
    def _draw_perfectexec_slash(surface, boss, x, y, timer, phase):
        tx, ty = _NS_zhaeris._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5 or progress > 0.85:
            return
        t = (progress - 0.5) / 0.35
        inten = math.sin(t * math.pi)
        a = _NS_zhaeris._alpha(255 * inten)
        sl = int(25 + t * 20)
        # X slash: two crossing lines
        for pair in [(-1, -1, 1, 1), (1, -1, -1, 1)]:
            x1 = tx + pair[0] * sl
            y1 = ty + pair[1] * sl
            x2 = tx + pair[2] * sl
            y2 = ty + pair[3] * sl
            for w, color, wa in [
                (8, _NS_zhaeris.PALETTE["energy_darkest"], 80),
                (5, _NS_zhaeris.PALETTE["energy_dark"], 120),
                (3, _NS_zhaeris.PALETTE["energy_mid"], 180),
                (2, _NS_zhaeris.PALETTE["energy_light"], 220),
                (1, _NS_zhaeris.PALETTE["energy_hot"], 255),
            ]:
                la = _NS_zhaeris._alpha(wa * inten)
                pygame.draw.line(surface, (*color, la), (x1, y1), (x2, y2), w)
        # Center burst
        br = int(8 + t * 12)
        for r in range(br + 4, 0, -2):
            ra = _NS_zhaeris._alpha(a * (br + 4 - r) / (br + 4))
            _NS_zhaeris._aacircle(surface,
                                  (*_NS_zhaeris.PALETTE["energy_mid"], ra),
                                  (tx, ty), r)
        _NS_zhaeris._aacircle(surface, (*_NS_zhaeris.PALETTE["energy_hot"], a),
                              (tx, ty), max(1, br // 3))
        _NS_zhaeris._aacircle(surface, _NS_zhaeris.PALETTE["energy_shine"],
                              (tx, ty), max(1, br // 6))
        pygame.draw.rect(surface, _NS_zhaeris.PALETTE["white"],
                         (tx, ty, 1, 1))
        # Flying sparks
        for i in range(10):
            sa = i * math.pi / 5 + phase * 0.8
            dist = int(sl * 0.8)
            ex = tx + int(math.cos(sa) * dist)
            ey = ty + int(math.sin(sa) * dist)
            pygame.draw.rect(surface, (*_NS_zhaeris.PALETTE["energy_hot"], a),
                             (ex, ey, 2, 2))
            pygame.draw.rect(surface, (*_NS_zhaeris.PALETTE["energy_shine"], a),
                             (ex, ey, 1, 1))



# ====================================================================
# COGSWORTH (SKYFURY) - TRUE BOSS
# ====================================================================

class _NS_cogsworth:
    """Namespace cogsworth - dwarven gyrocopter pilot boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Copper/brass body (main hull)
        "copper_darkest": (35, 18, 8),
        "copper_dark": (90, 50, 20),
        "copper_mid": (170, 100, 40),
        "copper_light": (230, 155, 75),
        "copper_shine": (255, 210, 140),
        # Iron plating (dark metal parts)
        "iron_darkest": (12, 12, 15),
        "iron_dark": (35, 35, 42),
        "iron_mid": (75, 75, 85),
        "iron_light": (135, 135, 148),
        "iron_shine": (200, 200, 215),
        # Teal/cyan accents (from ref - pilot outfit, panels)
        "teal_darkest": (5, 25, 30),
        "teal_dark": (15, 60, 75),
        "teal_mid": (35, 120, 145),
        "teal_light": (80, 180, 200),
        "teal_shine": (150, 230, 245),
        # Fire/exhaust (rocket flames)
        "fire_darkest": (45, 15, 5),
        "fire_dark": (140, 45, 15),
        "fire_mid": (230, 105, 30),
        "fire_light": (255, 175, 65),
        "fire_hot": (255, 225, 130),
        "fire_shine": (255, 250, 210),
        # Skin (dwarven pilot face)
        "skin_darkest": (75, 45, 30),
        "skin_dark": (140, 90, 65),
        "skin_mid": (195, 145, 110),
        "skin_light": (235, 190, 155),
        "skin_shine": (255, 220, 185),
        # White beard/mustache (aged pilot)
        "beard_darkest": (90, 85, 80),
        "beard_dark": (150, 145, 140),
        "beard_mid": (200, 195, 190),
        "beard_light": (235, 230, 225),
        "beard_shine": (255, 250, 245),
        # Goggles (glass with cyan tint)
        "glass_darkest": (5, 20, 30),
        "glass_dark": (20, 60, 90),
        "glass_mid": (60, 140, 180),
        "glass_light": (140, 220, 250),
        "glass_shine": (220, 250, 255),
        # Red missiles/warheads
        "red_darkest": (50, 10, 10),
        "red_dark": (130, 25, 25),
        "red_mid": (210, 55, 45),
        "red_light": (255, 110, 90),
        "red_shine": (255, 180, 160),
        # Smoke/exhaust trail
        "smoke_darkest": (25, 22, 20),
        "smoke_dark": (65, 60, 55),
        "smoke_mid": (125, 118, 110),
        "smoke_light": (190, 185, 178),
        "smoke_edge": (230, 225, 218),
        # Gold accents (trim)
        "gold_dark": (110, 80, 20),
        "gold_mid": (200, 155, 55),
        "gold_light": (245, 210, 100),
        "gold_shine": (255, 240, 170),
        # Wood (small handle grips)
        "wood_dark": (55, 32, 15),
        "wood_mid": (120, 75, 40),
        "wood_light": (175, 125, 75),
        # Eye
        "eye_socket": (10, 5, 4),
        "eye_dark": (30, 60, 80),
        "eye_mid": (80, 160, 200),
        "eye_light": (180, 230, 250),
        # Rotor blur
        "rotor_blur": (100, 100, 110),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    # ── helpers ──────────────────────────────────────────────
    def _clamp(c):
        return tuple(max(0, min(255, int(v))) for v in c)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_cogsworth._clamp(color)
        if _NS_cogsworth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_cogsworth._clamp(color)
        if _NS_cogsworth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        if len(points) < 3:
            return
        pygame.draw.polygon(surface, _NS_cogsworth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_cogsworth(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_cogsworth._detect_moving(boss)
        _NS_cogsworth._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_cog_attack_active", False)
            or getattr(boss, "timer", 0)
            > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind
        _NS_cogsworth._draw_sky_aura(surface, x, y, pulse)
        _NS_cogsworth._draw_ground_ring(surface, x, y + 55, pulse, active_skill)
        # Skill ground FX
        if active_skill == "r":
            _NS_cogsworth._draw_calldown_ground(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "e":
            _NS_cogsworth._draw_flak_ground(
                surface, boss, x, y, skill_timer, pulse
            )
        # Body
        _NS_cogsworth._draw_body(
            surface, boss, x, y, boss.direction, pulse, moving, attacking
        )
        # Basic attack projectile (bullet dari chin gun)
        if attacking and not active_skill:
            _NS_cogsworth._draw_basic_bullet(surface, boss, x, y, pulse)
        # Foreground skill FX
        if active_skill == "q":
            _NS_cogsworth._draw_homing_missile(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "w":
            _NS_cogsworth._draw_rocket_barrage(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "e":
            _NS_cogsworth._draw_flak_cannon(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "r":
            _NS_cogsworth._draw_calldown_bombs(
                surface, boss, x, y, skill_timer, pulse
            )
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        prev = int(getattr(boss, "_cog_prev_timer", 0))
        active = bool(getattr(boss, "_cog_attack_active", False))
        if timer >= cd - 1 and prev <= 1:
            boss._cog_attack_active = True
            boss._cog_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._cog_attack_frame = int(getattr(boss, "_cog_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._cog_attack_active = False
            boss._cog_attack_frame = 0
            active = False
        boss._cog_prev_timer = timer
        boss._cog_attack_progress = (
            min(1.0, getattr(boss, "_cog_attack_frame", 0) / max(1, cd - 1))
            if active
            else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_cog_last_x"):
            boss._cog_last_x = boss.x
            boss._cog_last_y = boss.y
            return False
        dx = abs(boss.x - boss._cog_last_x)
        dy = abs(boss.y - boss._cog_last_y)
        boss._cog_last_x = boss.x
        boss._cog_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # BODY (Gyrocopter — always floating with rotor spin)
    # ============================================================
    def _draw_body(surface, boss, x, y, facing, phase, moving, attacking):
        # Floating hover bob
        bob = int(math.sin(phase * 0.9) * 4)
        tilt = 0
        if moving:
            tilt = int(math.sin(phase * 0.5) * 2)
            bob = int(math.sin(phase * 1.3) * 5)
        if attacking:
            # Recoil kickback
            progress = getattr(boss, "_cog_attack_progress", 0.5)
            if 0.3 < progress < 0.55:
                bob += int(math.sin((progress - 0.3) / 0.25 * math.pi) * 3)
            tilt += -int(facing * 1)
        cx = x
        cy = y + bob
        _NS_cogsworth._draw_shadow(surface, x, y + 55)
        _NS_cogsworth._draw_hover_wash(surface, x, y + 48, phase, facing, moving)
        # Order: rear rotor blur -> tail -> main body -> pilot -> weapons -> main rotor blur
        _NS_cogsworth._draw_tail_rotor(surface, cx, cy, facing, phase)
        _NS_cogsworth._draw_tail_boom(surface, cx, cy, facing, phase, tilt)
        _NS_cogsworth._draw_landing_skids(surface, cx, cy, facing, phase, moving)
        _NS_cogsworth._draw_hull(surface, cx, cy, facing, phase, tilt)
        _NS_cogsworth._draw_wing_weapons(surface, cx, cy, facing, phase, attacking)
        _NS_cogsworth._draw_pilot(surface, cx, cy, facing, phase)
        _NS_cogsworth._draw_cockpit_glass(surface, cx, cy, facing, phase)
        _NS_cogsworth._draw_main_rotor(surface, cx, cy - 22, facing, phase)
    # ── HULL (main body) ─────────────────────────────────────
    def _draw_hull(surface, cx, cy, facing, phase, tilt):
        # Main copper hull - elongated horizontal shape
        hull = [
            (cx - 26, cy - 4),      # rear top
            (cx - 28, cy + 2),      # rear mid
            (cx - 24, cy + 10),     # rear bottom
            (cx - 12, cy + 14),     # belly back
            (cx + 8, cy + 14),      # belly front
            (cx + 22, cy + 10),     # front bottom
            (cx + 30, cy + 4),      # nose
            (cx + 28, cy - 2),      # front top
            (cx + 18, cy - 8),      # top front
            (cx - 8, cy - 10),      # top mid
            (cx - 20, cy - 8),      # top rear
        ]
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in hull])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["copper_darkest"], hull)
        # Copper mid layer
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["copper_dark"], [
            (cx - 25, cy - 3), (cx - 26, cy + 2), (cx - 22, cy + 9),
            (cx - 10, cy + 13), (cx + 7, cy + 13), (cx + 21, cy + 9),
            (cx + 28, cy + 3), (cx + 26, cy - 1), (cx + 17, cy - 7),
            (cx - 8, cy - 9), (cx - 19, cy - 7),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["copper_mid"], [
            (cx - 22, cy - 2), (cx - 23, cy + 3), (cx - 19, cy + 8),
            (cx - 8, cy + 11), (cx + 6, cy + 11), (cx + 19, cy + 8),
            (cx + 25, cy + 3), (cx + 23, cy), (cx + 15, cy - 6),
            (cx - 6, cy - 7), (cx - 17, cy - 6),
        ])
        # Copper highlight (top)
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["copper_light"], [
            (cx - 16, cy - 5), (cx - 4, cy - 6), (cx + 8, cy - 5),
            (cx + 14, cy - 3), (cx + 10, cy - 2), (cx - 4, cy - 3),
            (cx - 14, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["copper_shine"],
                         (cx - 6, cy - 5, 8, 1))
        # Rivets along hull
        for rv_x in (-22, -14, -4, 6, 14, 20):
            pygame.draw.rect(surface, _NS_cogsworth.PALETTE["copper_darkest"],
                             (cx + rv_x, cy + 6, 2, 2))
            pygame.draw.rect(surface, _NS_cogsworth.PALETTE["copper_shine"],
                             (cx + rv_x, cy + 6, 1, 1))
        # Iron belly plating
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["iron_darkest"], [
            (cx - 18, cy + 10), (cx + 18, cy + 10),
            (cx + 14, cy + 14), (cx - 14, cy + 14),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["iron_dark"], [
            (cx - 16, cy + 11), (cx + 16, cy + 11),
            (cx + 12, cy + 13), (cx - 12, cy + 13),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["iron_mid"], [
            (cx - 12, cy + 11), (cx + 12, cy + 11),
            (cx + 10, cy + 12), (cx - 10, cy + 12),
        ])
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_light"],
                         (cx - 6, cy + 11, 12, 1))
        # Belly rivets
        for i in range(-3, 4):
            pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_shine"],
                             (cx + i * 4, cy + 12, 1, 1))
        # Teal panel accents
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["teal_darkest"], [
            (cx - 12, cy - 2), (cx - 4, cy - 4), (cx - 4, cy + 4),
            (cx - 12, cy + 4),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["teal_dark"], [
            (cx - 11, cy - 1), (cx - 5, cy - 3), (cx - 5, cy + 3),
            (cx - 11, cy + 3),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["teal_mid"], [
            (cx - 10, cy), (cx - 6, cy - 2), (cx - 6, cy + 2),
            (cx - 10, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["teal_light"],
                         (cx - 9, cy - 1, 1, 2))
        # Gold trim strip along top
        pygame.draw.line(surface, _NS_cogsworth.PALETTE["gold_dark"],
                         (cx - 18, cy - 5), (cx + 16, cy - 4), 1)
        pygame.draw.line(surface, _NS_cogsworth.PALETTE["gold_mid"],
                         (cx - 16, cy - 5), (cx + 14, cy - 4), 1)
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["gold_shine"],
                         (cx - 4, cy - 5, 4, 1))
        # NOSE cone (pointed front)
        nose_pts = [
            (cx + 22, cy - 2),
            (cx + 30, cy + 4),
            (cx + 22, cy + 8),
        ]
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["copper_darkest"],
                            [(p[0] + 1, p[1] + 1) for p in nose_pts])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["copper_dark"], nose_pts)
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["copper_mid"], [
            (cx + 22, cy - 1), (cx + 28, cy + 4), (cx + 22, cy + 7),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["copper_light"], [
            (cx + 23, cy), (cx + 27, cy + 3), (cx + 23, cy + 4),
        ])
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["copper_shine"],
                         (cx + 25, cy + 2, 1, 1))
        # Nose gun/light tip (small barrel jutting forward)
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_dark"],
                         (cx + 29, cy + 3, 3, 2))
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_light"],
                         (cx + 29, cy + 3, 3, 1))
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["shadow_deep"],
                         (cx + 31, cy + 4, 1, 1))
    # ── TAIL BOOM ────────────────────────────────────────────
    def _draw_tail_boom(surface, cx, cy, facing, phase, tilt):
        # Tail extends back-left when facing right
        back = -facing
        tail_start_x = cx + back * 22
        tail_start_y = cy - 2
        tail_end_x = cx + back * 44
        tail_end_y = cy - 5
        # Tapered boom
        pts = [
            (tail_start_x, tail_start_y - 3),
            (tail_end_x, tail_end_y - 1),
            (tail_end_x, tail_end_y + 3),
            (tail_start_x, tail_start_y + 5),
        ]
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in pts])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["copper_darkest"], pts)
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["copper_dark"], [
            (tail_start_x, tail_start_y - 2),
            (tail_end_x, tail_end_y),
            (tail_end_x, tail_end_y + 2),
            (tail_start_x, tail_start_y + 4),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["copper_mid"], [
            (tail_start_x + back * 2, tail_start_y - 1),
            (tail_end_x, tail_end_y),
            (tail_end_x, tail_end_y + 1),
            (tail_start_x + back * 2, tail_start_y + 3),
        ])
        # Highlight
        pygame.draw.line(surface, _NS_cogsworth.PALETTE["copper_light"],
                         (tail_start_x, tail_start_y - 1),
                         (tail_end_x, tail_end_y), 1)
        # Rivets on tail
        for i in range(4):
            rvx = tail_start_x + int(back * (5 + i * 6))
            pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_darkest"],
                             (rvx, tail_start_y + 1, 1, 1))
            pygame.draw.rect(surface, _NS_cogsworth.PALETTE["copper_shine"],
                             (rvx, tail_start_y, 1, 1))
        # Vertical stabilizer (fin at end)
        fin_pts = [
            (tail_end_x, tail_end_y - 1),
            (tail_end_x + back * 4, tail_end_y - 8),
            (tail_end_x + back * 6, tail_end_y - 4),
            (tail_end_x + back * 3, tail_end_y + 2),
        ]
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in fin_pts])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["copper_darkest"], fin_pts)
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["copper_dark"], [
            (tail_end_x + back * 1, tail_end_y - 1),
            (tail_end_x + back * 4, tail_end_y - 7),
            (tail_end_x + back * 5, tail_end_y - 4),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["copper_mid"], [
            (tail_end_x + back * 2, tail_end_y - 2),
            (tail_end_x + back * 4, tail_end_y - 6),
            (tail_end_x + back * 4, tail_end_y - 4),
        ])
    def _draw_tail_rotor(surface, cx, cy, facing, phase):
        """Small spinning rotor at tail end."""
        back = -facing
        rx = cx + back * 46
        ry = cy - 5
        # Hub
        _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["iron_darkest"],
                                (rx, ry), 3)
        _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["iron_dark"],
                                (rx, ry), 2)
        _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["iron_light"],
                                (rx, ry), 1)
        # Spinning blur (fast rotation blur)
        rot = phase * 8
        for i in range(3):
            ang = rot + i * math.pi * 2 / 3
            for r_step in range(1, 8):
                bx = rx + int(math.cos(ang) * r_step)
                by = ry + int(math.sin(ang) * r_step)
                a = _NS_cogsworth._alpha(100 - r_step * 10)
                pygame.draw.rect(surface,
                                 (*_NS_cogsworth.PALETTE["rotor_blur"], a),
                                 (bx, by, 1, 1))
        # Motion blur ring
        for r_ring in range(7, 4, -1):
            a = _NS_cogsworth._alpha(60 + (7 - r_ring) * 25)
            _NS_cogsworth._aacircle(surface,
                                    (*_NS_cogsworth.PALETTE["rotor_blur"], a),
                                    (rx, ry), r_ring, 1)
    # ── MAIN ROTOR (top) ─────────────────────────────────────
    def _draw_main_rotor(surface, cx, cy, facing, phase):
        """Large spinning rotor above the body."""
        # Mast
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_darkest"],
                         (cx - 2, cy, 4, 8))
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_dark"],
                         (cx - 1, cy, 3, 8))
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_light"],
                         (cx - 1, cy, 1, 6))
        # Hub
        _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["shadow_deep"],
                                (cx + 1, cy + 1), 5)
        _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["iron_darkest"],
                                (cx, cy), 5)
        _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["iron_dark"],
                                (cx, cy), 4)
        _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["iron_mid"],
                                (cx, cy), 3)
        _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["iron_light"],
                                (cx - 1, cy - 1), 2)
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["gold_mid"],
                         (cx - 1, cy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["gold_shine"],
                         (cx - 1, cy - 1, 1, 1))
        # SPINNING BLADES (motion blur ellipse)
        rot_speed = phase * 12
        # Draw as elliptical motion blur (rotating fast so appears as blur disc)
        blur_surf = pygame.Surface((90, 20), pygame.SRCALPHA)
        for r_ring in range(42, 0, -3):
            a = _NS_cogsworth._alpha(30 + (42 - r_ring) * 2)
            pygame.draw.ellipse(blur_surf,
                                (*_NS_cogsworth.PALETTE["iron_darkest"], a),
                                (45 - r_ring, 10 - 2, r_ring * 2, 4))
        # Individual blade streaks
        for i in range(4):
            ang = rot_speed + i * math.pi / 2
            blade_end = 40
            # Only show blades that are visible from side (perspective)
            visibility = abs(math.cos(ang))
            if visibility < 0.15:
                continue
            direction = 1 if math.cos(ang) > 0 else -1
            length = int(blade_end * visibility)
            end_x = 45 + direction * length
            a = _NS_cogsworth._alpha(120 * visibility)
            pygame.draw.line(blur_surf,
                             (*_NS_cogsworth.PALETTE["iron_dark"], a),
                             (45, 10), (end_x, 10 + int(math.sin(ang) * 2)), 2)
            pygame.draw.line(blur_surf,
                             (*_NS_cogsworth.PALETTE["iron_mid"], a),
                             (45, 10), (end_x, 10 + int(math.sin(ang) * 2)), 1)
        # Outer disc ring (blur silhouette)
        pygame.draw.ellipse(blur_surf,
                            (*_NS_cogsworth.PALETTE["iron_light"], 60),
                            (2, 8, 86, 4), 1)
        surface.blit(blur_surf, (cx - 45, cy - 10))
        # Small highlights (blade tips catching light)
        for i in range(2):
            tip_ang = rot_speed + i * math.pi
            tip_x = cx + int(math.cos(tip_ang) * 40)
            tip_y = cy + int(math.sin(tip_ang) * 3)
            pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_shine"],
                             (tip_x, tip_y, 2, 1))
    # ── LANDING SKIDS ────────────────────────────────────────
    def _draw_landing_skids(surface, cx, cy, facing, phase, moving):
        # Skids below the body
        skid_y = cy + 20
        # Front skid strut
        pygame.draw.line(surface, _NS_cogsworth.PALETTE["iron_darkest"],
                         (cx + 8, cy + 14), (cx + 10, skid_y), 3)
        pygame.draw.line(surface, _NS_cogsworth.PALETTE["iron_dark"],
                         (cx + 8, cy + 14), (cx + 10, skid_y), 2)
        pygame.draw.line(surface, _NS_cogsworth.PALETTE["iron_darkest"],
                         (cx - 8, cy + 14), (cx - 10, skid_y), 3)
        pygame.draw.line(surface, _NS_cogsworth.PALETTE["iron_dark"],
                         (cx - 8, cy + 14), (cx - 10, skid_y), 2)
        # Horizontal skid bar
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_darkest"],
                         (cx - 16, skid_y, 32, 3))
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_dark"],
                         (cx - 15, skid_y, 30, 2))
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_mid"],
                         (cx - 15, skid_y, 30, 1))
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_light"],
                         (cx - 8, skid_y, 12, 1))
        # Skid tips curling up
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_dark"],
                         (cx - 18, skid_y - 1, 3, 3))
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_dark"],
                         (cx + 15, skid_y - 1, 3, 3))
    # ── WING WEAPONS (rockets, guns) ─────────────────────────
    def _draw_wing_weapons(surface, cx, cy, facing, phase, attacking):
        # Rocket pod attached to side of hull
        pod_y = cy + 6
        pod_x_offset = facing * 12
        # Under-pod (dark iron mount)
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_darkest"],
                         (cx - 14, pod_y, 28, 5))
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_dark"],
                         (cx - 13, pod_y, 26, 4))
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_mid"],
                         (cx - 13, pod_y, 26, 1))
        # Rocket tubes (3 per side) - main rocket cluster at front
        rocket_x = cx + facing * 14
        rocket_y = pod_y + 1
        # Cluster of 3 rockets in a triangle
        for rk_i, (dx, dy) in enumerate([(0, -2), (2, 0), (0, 2)]):
            rx = rocket_x + int(dx * facing)
            ry = rocket_y + dy
            # Tube
            pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_darkest"],
                             (rx - 4 if facing > 0 else rx, ry, 8, 2))
            pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_dark"],
                             (rx - 4 if facing > 0 else rx, ry, 8, 1))
            # Red missile tip visible
            tip_x = rx + facing * 4
            pygame.draw.rect(surface, _NS_cogsworth.PALETTE["red_darkest"],
                             (tip_x - (0 if facing > 0 else 1), ry, 2, 2))
            pygame.draw.rect(surface, _NS_cogsworth.PALETTE["red_mid"],
                             (tip_x - (0 if facing > 0 else 1), ry, 2, 1))
            pygame.draw.rect(surface, _NS_cogsworth.PALETTE["red_light"],
                             (tip_x + (1 if facing > 0 else 0), ry, 1, 1))
        # Chin gun barrel (Gatling-style) - under nose
        gun_x = cx + facing * 20
        gun_y = cy + 10
        # Gun body
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_darkest"],
                         (gun_x - 5, gun_y, 10, 5))
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_dark"],
                         (gun_x - 4, gun_y, 10, 4))
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_mid"],
                         (gun_x - 4, gun_y, 10, 1))
        # Barrels (multiple visible)
        for barrel_off in (0, 2, 4):
            bx = gun_x + facing * (5 + barrel_off)
            pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_darkest"],
                             (bx if facing > 0 else bx - 2, gun_y + 1, 3, 1))
            pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_light"],
                             (bx if facing > 0 else bx - 2, gun_y + 1, 2, 1))
        # Barrel tip
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["shadow_deep"],
                         (gun_x + facing * 9, gun_y + 2, 1, 1))
        # Attack muzzle flash
        if attacking:
            progress = getattr(pygame, "_", None)  # placeholder unused
            flash_x = gun_x + facing * 11
            flash_y = gun_y + 2
            for r in range(5, 0, -1):
                a = _NS_cogsworth._alpha(150 * (5 - r) / 5)
                _NS_cogsworth._aacircle(surface,
                                        (*_NS_cogsworth.PALETTE["fire_mid"], a),
                                        (flash_x, flash_y), r)
            _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["fire_hot"],
                                    (flash_x, flash_y), 2)
            pygame.draw.rect(surface, _NS_cogsworth.PALETTE["fire_shine"],
                             (flash_x, flash_y, 1, 1))
    # ── PILOT (dwarf in cockpit) ─────────────────────────────
    def _draw_pilot(surface, cx, cy, facing, phase):
        # Pilot upper body visible in open cockpit
        px = cx + facing * 2
        py = cy - 10
        # Torso (teal jacket)
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["shadow_deep"], [
            (px - 4, py + 2), (px + 4, py + 2),
            (px + 5, py + 6), (px - 5, py + 6),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["teal_darkest"], [
            (px - 4, py + 1), (px + 4, py + 1),
            (px + 5, py + 5), (px - 5, py + 5),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["teal_dark"], [
            (px - 3, py + 2), (px + 3, py + 2),
            (px + 4, py + 5), (px - 4, py + 5),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["teal_mid"], [
            (px - 2, py + 2), (px + 2, py + 2),
            (px + 3, py + 4), (px - 3, py + 4),
        ])
        # Gold jacket trim
        pygame.draw.line(surface, _NS_cogsworth.PALETTE["gold_dark"],
                         (px - 4, py + 2), (px + 4, py + 2), 1)
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["gold_light"],
                         (px, py + 2, 1, 1))
        # Button
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["gold_mid"],
                         (px, py + 4, 1, 1))
        # HEAD (round bald with helmet-goggles)
        hy = py - 4
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["shadow_deep"], [
            (px - 4, hy + 3), (px - 5, hy - 1), (px - 3, hy - 4),
            (px + 3, hy - 4), (px + 5, hy - 1), (px + 4, hy + 3),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["skin_darkest"], [
            (px - 4, hy + 2), (px - 5, hy - 1), (px - 3, hy - 4),
            (px + 3, hy - 4), (px + 5, hy - 1), (px + 4, hy + 2),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["skin_dark"], [
            (px - 4, hy + 1), (px - 4, hy - 1), (px - 2, hy - 3),
            (px + 2, hy - 3), (px + 4, hy - 1), (px + 4, hy + 1),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["skin_mid"], [
            (px - 3, hy - 1), (px - 1, hy - 2),
            (px + 1, hy - 2), (px + 3, hy - 1),
            (px + 3, hy), (px - 3, hy),
        ])
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["skin_light"],
                         (px - 1, hy - 2, 2, 1))
        # BIG NOSE (drunkard-like red)
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["skin_dark"],
                         (px + facing * 1, hy, 2, 2))
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["skin_mid"],
                         (px + facing * 1, hy, 1, 1))
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["red_dark"],
                         (px + facing * 1, hy + 1, 2, 1))
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["red_mid"],
                         (px + facing * 2, hy + 1, 1, 1))
        # GOGGLES (large aviator goggles with cyan lenses)
        _NS_cogsworth._draw_goggles(surface, px, hy - 1, facing, phase)
        # WHITE MUSTACHE (big handlebar)
        _NS_cogsworth._draw_mustache(surface, px, hy + 2, facing, phase)
        # WHITE BEARD (short round)
        _NS_cogsworth._draw_beard(surface, px, hy + 3, facing, phase)
        # HELMET/CAP top
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["iron_darkest"], [
            (px - 5, hy - 4), (px - 3, hy - 5), (px + 3, hy - 5),
            (px + 5, hy - 4), (px + 4, hy - 3), (px - 4, hy - 3),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["iron_dark"], [
            (px - 4, hy - 4), (px - 2, hy - 5), (px + 2, hy - 5),
            (px + 4, hy - 4), (px + 3, hy - 3), (px - 3, hy - 3),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["iron_mid"], [
            (px - 2, hy - 4), (px + 2, hy - 4),
            (px + 2, hy - 3), (px - 2, hy - 3),
        ])
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_light"],
                         (px - 1, hy - 4, 2, 1))
        # Helmet gold rivet
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["gold_light"],
                         (px, hy - 4, 1, 1))
    def _draw_goggles(surface, gx, gy, facing, phase):
        """Aviator goggles with glowing cyan lenses."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Strap across head
        pygame.draw.line(surface, _NS_cogsworth.PALETTE["wood_dark"],
                         (gx - 5, gy), (gx + 5, gy), 1)
        # Two round lenses
        for lx_off in (-3, 3):
            lx = gx + lx_off
            # Rim
            _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["wood_dark"],
                                    (lx, gy), 3)
            _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["copper_mid"],
                                    (lx, gy), 2)
            # Glass
            _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["glass_darkest"],
                                    (lx, gy), 2)
            _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["glass_dark"],
                                    (lx, gy), 1)
            # Glow
            for r in range(4, 0, -1):
                a = _NS_cogsworth._alpha(60 * (4 - r) / 4 * pulse)
                _NS_cogsworth._aacircle(surface,
                                        (*_NS_cogsworth.PALETTE["glass_mid"], a),
                                        (lx, gy), r)
            pygame.draw.rect(surface, _NS_cogsworth.PALETTE["glass_light"],
                             (lx, gy - 1, 1, 1))
            pygame.draw.rect(surface, _NS_cogsworth.PALETTE["glass_shine"],
                             (lx, gy - 1, 1, 1))
    def _draw_mustache(surface, mx, my, facing, phase):
        """White handlebar mustache."""
        sway = math.sin(phase * 0.5) * 0.5
        # Left side
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["beard_darkest"], [
            (mx - 5, my - 1), (mx - 1, my - 1),
            (mx, my + 2), (mx - 4, my + 2 + int(sway)),
            (mx - 6, my),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["beard_dark"], [
            (mx - 4, my), (mx - 1, my),
            (mx - 1, my + 1), (mx - 3, my + 1),
            (mx - 5, my),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["beard_mid"], [
            (mx - 3, my), (mx - 2, my),
            (mx - 2, my + 1), (mx - 3, my + 1),
        ])
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["beard_light"],
                         (mx - 3, my, 1, 1))
        # Right side
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["beard_darkest"], [
            (mx + 1, my - 1), (mx + 5, my - 1),
            (mx + 6, my), (mx + 4, my + 2 - int(sway)),
            (mx, my + 2),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["beard_dark"], [
            (mx + 1, my), (mx + 4, my),
            (mx + 5, my), (mx + 3, my + 1),
            (mx + 1, my + 1),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["beard_mid"], [
            (mx + 2, my), (mx + 3, my),
            (mx + 3, my + 1), (mx + 2, my + 1),
        ])
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["beard_light"],
                         (mx + 2, my, 1, 1))
    def _draw_beard(surface, bx, by, facing, phase):
        """Short round white beard."""
        beard_pts = [
            (bx - 4, by), (bx - 5, by + 2), (bx - 4, by + 4),
            (bx - 1, by + 5), (bx + 1, by + 5), (bx + 4, by + 4),
            (bx + 5, by + 2), (bx + 4, by),
        ]
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in beard_pts])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["beard_darkest"], beard_pts)
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["beard_dark"], [
            (bx - 4, by + 1), (bx - 4, by + 3),
            (bx - 1, by + 4), (bx + 1, by + 4),
            (bx + 4, by + 3), (bx + 4, by + 1),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["beard_mid"], [
            (bx - 3, by + 2), (bx - 2, by + 3),
            (bx + 2, by + 3), (bx + 3, by + 2),
        ])
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["beard_light"],
                         (bx - 1, by + 3, 2, 1))
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["beard_shine"],
                         (bx, by + 3, 1, 1))
    # ── COCKPIT GLASS (front canopy) ─────────────────────────
    def _draw_cockpit_glass(surface, cx, cy, facing, phase):
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8
        # Cockpit windshield (curved glass in front of pilot)
        cp_x = cx + facing * 8
        cp_y = cy - 6
        canopy_pts = [
            (cp_x - facing * 2, cp_y + 4),
            (cp_x - facing * 3, cp_y - 2),
            (cp_x + facing * 4, cp_y - 4),
            (cp_x + facing * 8, cp_y),
            (cp_x + facing * 6, cp_y + 4),
        ]
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["copper_darkest"],
                            [(p[0] + 1, p[1] + 1) for p in canopy_pts])
        # Glass fill (semi-transparent)
        glass_surf = pygame.Surface((30, 20), pygame.SRCALPHA)
        local = [(p[0] - cp_x + 15, p[1] - cp_y + 10) for p in canopy_pts]
        _NS_cogsworth._poly(glass_surf, (*_NS_cogsworth.PALETTE["glass_dark"], 180),
                            local)
        _NS_cogsworth._poly(glass_surf, (*_NS_cogsworth.PALETTE["glass_mid"], 130),
                            [(p[0] + 1, p[1] + 1) for p in local[:-1]])
        # Highlight strip
        pygame.draw.line(glass_surf,
                         (*_NS_cogsworth.PALETTE["glass_light"],
                          _NS_cogsworth._alpha(200 * pulse)),
                         (local[1][0] + 1, local[1][1] + 1),
                         (local[2][0], local[2][1] + 1), 1)
        pygame.draw.rect(glass_surf,
                         (*_NS_cogsworth.PALETTE["glass_shine"], 220),
                         (local[2][0] - 1, local[2][1] + 1, 2, 1))
        surface.blit(glass_surf, (cp_x - 15, cp_y - 10))
        # Frame edge
        for i in range(len(canopy_pts) - 1):
            pygame.draw.line(surface, _NS_cogsworth.PALETTE["copper_dark"],
                             canopy_pts[i], canopy_pts[i + 1], 1)
        pygame.draw.line(surface, _NS_cogsworth.PALETTE["gold_mid"],
                         canopy_pts[1], canopy_pts[2], 1)
    # ============================================================
    # AMBIENT / HOVER WASH
    # ============================================================
    def _draw_shadow(surface, x, y):
        sh = pygame.Surface((160, 30), pygame.SRCALPHA)
        for r in range(14, 0, -1):
            a = max(0, (14 - r) * 15)
            pygame.draw.ellipse(sh, (0, 0, 0, a),
                                (10 - r, 15 - r, 140 + r * 2, r * 2))
        pygame.draw.ellipse(sh, (5, 3, 2, 150), (8, 8, 144, 14))
        surface.blit(sh, (x - 80, y - 15))
    def _draw_hover_wash(surface, cx, cy, phase, facing, moving):
        """Dust/wind blowing outward from rotor downwash."""
        strength = 1.3 if moving else 1.0
        # Ground dust cloud
        mist = pygame.Surface((180, 40), pygame.SRCALPHA)
        for r in range(28, 3, -3):
            a = _NS_cogsworth._alpha((28 - r) * 2.5 * strength)
            if a > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_cogsworth.PALETTE["smoke_dark"], a),
                    (90 - r * 2, 20 - r // 3,
                     r * 4, max(3, r // 2)),
                )
        for r in range(18, 3, -2):
            a = _NS_cogsworth._alpha((18 - r) * 3 * strength)
            if a > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_cogsworth.PALETTE["smoke_mid"], a),
                    (90 - r, 20 - r // 4,
                     r * 2, max(2, r // 3)),
                )
        surface.blit(mist, (cx - 90, cy - 10))
        # Wind rings (radial dust puffs)
        for i in range(6):
            t = (phase * 0.6 + i * 0.16) % 1.0
            side = 1 if i % 2 == 0 else -1
            dx = int(t * 40 * side)
            dy = int(math.sin(t * math.pi) * 5)
            a = _NS_cogsworth._alpha(180 * (1 - t) * strength)
            if a > 0:
                _NS_cogsworth._aacircle(
                    surface, (*_NS_cogsworth.PALETTE["smoke_dark"], a),
                    (cx + dx, cy + dy), max(2, 5 - int(t * 3)),
                )
                _NS_cogsworth._aacircle(
                    surface, (*_NS_cogsworth.PALETTE["smoke_light"], a),
                    (cx + dx, cy + dy - 1), max(1, 3 - int(t * 2)),
                )
    def _draw_sky_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.2 + 0.8
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for r in range(85, 5, -6):
            a = _NS_cogsworth._alpha((85 - r) * 0.9 * pulse)
            if a > 0:
                _NS_cogsworth._aacircle(
                    aura, (*_NS_cogsworth.PALETTE["smoke_darkest"], a),
                    (110, 90), r,
                )
        for r in range(50, 5, -4):
            a = _NS_cogsworth._alpha((50 - r) * 1.0 * pulse)
            if a > 0:
                _NS_cogsworth._aacircle(
                    aura, (*_NS_cogsworth.PALETTE["teal_dark"], a),
                    (110, 90), r,
                )
        surface.blit(aura, (x - 110, y - 90))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 46), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_cogsworth.PALETTE["fire_darkest"], 140),
                            (5, 14, 170, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_cogsworth.PALETTE["fire_dark"], 180),
                            (14, 16, 152, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_cogsworth.PALETTE["fire_mid"], 160),
                            (25, 18, 130, 16), 1)
        for i in range(10):
            ang = phase * 0.4 + i * math.pi / 5
            x1 = 90 + int(math.cos(ang) * 50)
            y1 = 25 + int(math.sin(ang) * 8)
            x2 = 90 + int(math.cos(ang) * 78)
            y2 = 25 + int(math.sin(ang) * 12)
            pygame.draw.line(ring, (*_NS_cogsworth.PALETTE["fire_light"], 200),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(
                ring, (*_NS_cogsworth.PALETTE["fire_hot"],
                       _NS_cogsworth._alpha(150 * pulse)),
                (10, 8, 160, 32), 1,
            )
        surface.blit(ring, (x - 90, y - 23))
    # ============================================================
    # BASIC ATTACK — BULLET PROJECTILE (chin gun)
    # ============================================================
    def _draw_basic_bullet(surface, boss, x, y, phase):
        """Draw bullet projectile from chin gun during basic attack."""
        facing = boss.direction
        progress = getattr(boss, "_cog_attack_progress", 0.0)
        if progress <= 0:
            return
        tx, ty = _NS_cogsworth._target_position(boss, x, y)
        # Muzzle position (chin gun tip)
        gun_x = x + facing * 32
        gun_y = y + 12
        # ── PHASE 1: Wind-up + Muzzle flash (0 - 0.25) ──────
        if progress < 0.25:
            fl_t = progress / 0.25
            fl_r = int(3 + fl_t * 7)
            fl_intensity = math.sin(fl_t * math.pi)
            # Muzzle flash
            for r in range(fl_r + 3, 0, -1):
                a = _NS_cogsworth._alpha(240 * (fl_r + 3 - r) / (fl_r + 3)
                                          * fl_intensity)
                _NS_cogsworth._aacircle(
                    surface, (*_NS_cogsworth.PALETTE["fire_dark"], a),
                    (gun_x, gun_y), r,
                )
            _NS_cogsworth._aacircle(
                surface,
                (*_NS_cogsworth.PALETTE["fire_mid"],
                 _NS_cogsworth._alpha(255 * fl_intensity)),
                (gun_x, gun_y), max(1, fl_r - 2),
            )
            _NS_cogsworth._aacircle(
                surface,
                (*_NS_cogsworth.PALETTE["fire_hot"],
                 _NS_cogsworth._alpha(255 * fl_intensity)),
                (gun_x, gun_y), max(1, fl_r - 4),
            )
            _NS_cogsworth._aacircle(
                surface,
                (*_NS_cogsworth.PALETTE["fire_shine"],
                 _NS_cogsworth._alpha(255 * fl_intensity)),
                (gun_x, gun_y), max(1, fl_r - 6),
            )
            # Radial flash spikes
            for i in range(6):
                ang = i * math.pi / 3 + phase
                sp_len = int(fl_r * 1.5)
                ex = gun_x + int(math.cos(ang) * sp_len)
                ey = gun_y + int(math.sin(ang) * sp_len)
                pygame.draw.line(
                    surface,
                    (*_NS_cogsworth.PALETTE["fire_hot"],
                     _NS_cogsworth._alpha(200 * fl_intensity)),
                    (gun_x, gun_y), (ex, ey), 1,
                )
            # Shell casing ejection
            if fl_t > 0.3:
                cs_t = (fl_t - 0.3) / 0.7
                cs_x = gun_x - int(cs_t * 8)
                cs_y = gun_y + int(cs_t * cs_t * 12) - 4
                pygame.draw.rect(
                    surface, _NS_cogsworth.PALETTE["gold_dark"],
                    (cs_x, cs_y, 2, 3),
                )
                pygame.draw.rect(
                    surface, _NS_cogsworth.PALETTE["gold_light"],
                    (cs_x, cs_y, 1, 2),
                )
                pygame.draw.rect(
                    surface, _NS_cogsworth.PALETTE["gold_shine"],
                    (cs_x, cs_y, 1, 1),
                )
            return
        # ── PHASE 2: Bullet flying (0.25 - 1.0) ─────────────
        t = (progress - 0.25) / 0.75
        t = max(0.0, min(1.0, t))
        # Bullet position (linear interpolation)
        bx = int(gun_x + (tx - gun_x) * t)
        by = int(gun_y + (ty - gun_y) * t)
        # Angle to target
        angle = math.atan2(ty - gun_y, tx - gun_x)
        # ── TRAIL (streak behind bullet) ─────────────────────
        for i in range(8):
            trail_t = max(0.0, t - i * 0.04)
            px = int(gun_x + (tx - gun_x) * trail_t)
            py = int(gun_y + (ty - gun_y) * trail_t)
            a = _NS_cogsworth._alpha(220 - i * 25)
            if a <= 0:
                continue
            size = max(1, 4 - i // 2)
            _NS_cogsworth._aacircle(
                surface,
                (*_NS_cogsworth.PALETTE["fire_darkest"], a),
                (px, py), size + 1,
            )
            _NS_cogsworth._aacircle(
                surface,
                (*_NS_cogsworth.PALETTE["fire_dark"], a),
                (px, py), size,
            )
            _NS_cogsworth._aacircle(
                surface,
                (*_NS_cogsworth.PALETTE["fire_mid"], a),
                (px, py), max(1, size - 1),
            )
            if i < 3:
                pygame.draw.rect(
                    surface,
                    (*_NS_cogsworth.PALETTE["fire_hot"], a),
                    (px, py, 1, 1),
                )
        # ── BULLET (elongated tracer) ────────────────────────
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        bl = 8  # bullet length
        bw = 2  # bullet width
        # Bullet shape (elongated)
        tip_x = bx + int(cos_a * bl * 0.5)
        tip_y = by + int(sin_a * bl * 0.5)
        back_x = bx - int(cos_a * bl * 0.5)
        back_y = by - int(sin_a * bl * 0.5)
        perp_x = -sin_a
        perp_y = cos_a
        bullet_pts = [
            (tip_x, tip_y),
            (bx + int(perp_x * bw), by + int(perp_y * bw)),
            (back_x + int(perp_x * bw), back_y + int(perp_y * bw)),
            (back_x - int(perp_x * bw), back_y - int(perp_y * bw)),
            (bx - int(perp_x * bw), by - int(perp_y * bw)),
        ]
        # Outer glow (fire aura)
        for glow_r in range(6, 2, -1):
            a = _NS_cogsworth._alpha(120 * (6 - glow_r) / 6)
            _NS_cogsworth._aacircle(
                surface,
                (*_NS_cogsworth.PALETTE["fire_mid"], a),
                (bx, by), glow_r,
            )
        # Bullet body
        _NS_cogsworth._poly(
            surface, _NS_cogsworth.PALETTE["shadow_deep"],
            [(p[0] + 1, p[1] + 1) for p in bullet_pts],
        )
        _NS_cogsworth._poly(
            surface, _NS_cogsworth.PALETTE["fire_darkest"], bullet_pts,
        )
        # Metal jacket
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["gold_dark"], [
            (tip_x, tip_y),
            (bx + int(perp_x * (bw - 1)), by + int(perp_y * (bw - 1))),
            (back_x + int(perp_x * (bw - 1)),
             back_y + int(perp_y * (bw - 1))),
            (back_x - int(perp_x * (bw - 1)),
             back_y - int(perp_y * (bw - 1))),
            (bx - int(perp_x * (bw - 1)), by - int(perp_y * (bw - 1))),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["gold_mid"], [
            (tip_x, tip_y),
            (bx, by + int(perp_y * (bw - 1))),
            (back_x, back_y),
            (bx, by - int(perp_y * (bw - 1))),
        ])
        # Bright tracer core
        pygame.draw.line(
            surface, _NS_cogsworth.PALETTE["fire_hot"],
            (tip_x, tip_y), (back_x, back_y), 1,
        )
        pygame.draw.rect(
            surface, _NS_cogsworth.PALETTE["fire_shine"],
            (tip_x, tip_y, 1, 1),
        )
        pygame.draw.rect(
            surface, _NS_cogsworth.PALETTE["white"],
            (tip_x, tip_y, 1, 1),
        )
        # ── IMPACT (last 15%) ────────────────────────────────
        if t > 0.85:
            impact_t = (t - 0.85) / 0.15
            r = int(6 + impact_t * 14)
            a = _NS_cogsworth._alpha(240 * (1 - impact_t))
            # Impact flash
            for rr in range(r + 3, 0, -2):
                ra = _NS_cogsworth._alpha(a * (r + 3 - rr) / (r + 3))
                _NS_cogsworth._aacircle(
                    surface,
                    (*_NS_cogsworth.PALETTE["fire_dark"], ra),
                    (tx, ty), rr,
                )
            _NS_cogsworth._aacircle(
                surface, (*_NS_cogsworth.PALETTE["fire_mid"], a),
                (tx, ty), max(2, r - 3),
            )
            _NS_cogsworth._aacircle(
                surface, (*_NS_cogsworth.PALETTE["fire_light"], a),
                (tx, ty), max(1, r - 6),
            )
            _NS_cogsworth._aacircle(
                surface, (*_NS_cogsworth.PALETTE["fire_hot"], a),
                (tx, ty), max(1, r - 9),
            )
            _NS_cogsworth._aacircle(
                surface, (*_NS_cogsworth.PALETTE["fire_shine"], a),
                (tx, ty), max(1, r - 12),
            )
            pygame.draw.rect(
                surface, (*_NS_cogsworth.PALETTE["white"], a),
                (tx, ty, 1, 1),
            )
            # Sparks flying outward
            for i in range(6):
                ang = i * math.pi / 3 + impact_t * 4
                ex = tx + int(math.cos(ang) * r)
                ey = ty + int(math.sin(ang) * r)
                pygame.draw.line(
                    surface,
                    (*_NS_cogsworth.PALETTE["fire_hot"], a),
                    (tx, ty), (ex, ey), 1,
                )
                pygame.draw.rect(
                    surface,
                    (*_NS_cogsworth.PALETTE["fire_shine"], a),
                    (ex, ey, 2, 2),
                )
    # ============================================================
    # SKILL Q — HOMING MISSILE
    # ============================================================
    def _draw_homing_missile(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_cogsworth._target_position(boss, x, y)
        if progress < 0.1:
            return
        t = (progress - 0.1) / 0.9
        t = min(1.0, t)
        # Wavy homing path
        start_x = x + facing * 30
        start_y = y + 2
        # Slight sinusoidal path
        wave = math.sin(t * math.pi * 2) * 12
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t + wave)
        # Long smoke trail
        for i in range(14):
            trail_t = max(0.0, t - i * 0.05)
            trail_wave = math.sin(trail_t * math.pi * 2) * 12
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t + trail_wave)
            a = _NS_cogsworth._alpha(220 - i * 15)
            size = max(1, 5 - i // 2)
            _NS_cogsworth._aacircle(surface,
                                    (*_NS_cogsworth.PALETTE["smoke_darkest"], a),
                                    (px, py), size + 1)
            _NS_cogsworth._aacircle(surface,
                                    (*_NS_cogsworth.PALETTE["smoke_mid"], a),
                                    (px, py), size)
            _NS_cogsworth._aacircle(surface,
                                    (*_NS_cogsworth.PALETTE["smoke_light"], a),
                                    (px, py), max(1, size - 1))
            # Occasional ember
            if i % 3 == 0:
                pygame.draw.rect(surface,
                                 (*_NS_cogsworth.PALETTE["fire_mid"], a),
                                 (px, py, 1, 1))
        # Missile body (calc direction from wave)
        prev_wave = math.sin((t - 0.02) * math.pi * 2) * 12
        prev_x = int(start_x + (tx - start_x) * (t - 0.02))
        prev_y = int(start_y + (ty - start_y) * (t - 0.02) + prev_wave)
        mangle = math.atan2(by - prev_y, (bx - prev_x) * facing)
        _NS_cogsworth._draw_missile(surface, bx, by, mangle, facing, big=True)
        # Flame at back of missile
        flame_x = bx - int(math.cos(mangle) * 6) * facing
        flame_y = by - int(math.sin(mangle) * 6)
        for r in range(6, 0, -1):
            a = _NS_cogsworth._alpha(200 * (6 - r) / 6)
            _NS_cogsworth._aacircle(surface,
                                    (*_NS_cogsworth.PALETTE["fire_dark"], a),
                                    (flame_x, flame_y), r)
        _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["fire_mid"],
                                (flame_x, flame_y), 3)
        _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["fire_hot"],
                                (flame_x, flame_y), 2)
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["fire_shine"],
                         (flame_x, flame_y, 1, 1))
        # Impact
        if t > 0.9:
            _NS_cogsworth._draw_explosion(surface, tx, ty, (t - 0.9) / 0.1)
    def _draw_missile(surface, mx, my, angle, facing, big=False):
        """Rocket/missile shape."""
        length = 12 if big else 8
        width = 3 if big else 2
        # Body direction vector
        cos_a = math.cos(angle) * facing
        sin_a = math.sin(angle)
        # Tip and back
        tip_x = mx + int(cos_a * length * 0.6)
        tip_y = my + int(sin_a * length * 0.6)
        back_x = mx - int(cos_a * length * 0.4)
        back_y = my - int(sin_a * length * 0.4)
        # Perpendicular
        perp_x = -sin_a
        perp_y = cos_a
        # Body poly (rocket shape)
        body = [
            (tip_x, tip_y),
            (mx + int(perp_x * width), my + int(perp_y * width)),
            (back_x + int(perp_x * width), back_y + int(perp_y * width)),
            (back_x - int(perp_x * width), back_y - int(perp_y * width)),
            (mx - int(perp_x * width), my - int(perp_y * width)),
        ]
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in body])
        # Red warhead (front)
        head = [
            (tip_x, tip_y),
            (mx + int(perp_x * width), my + int(perp_y * width)),
            (mx - int(perp_x * width), my - int(perp_y * width)),
        ]
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["red_darkest"], head)
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["red_dark"], [
            (tip_x, tip_y),
            (int((tip_x + mx) / 2 + perp_x * (width - 1)),
             int((tip_y + my) / 2 + perp_y * (width - 1))),
            (int((tip_x + mx) / 2 - perp_x * (width - 1)),
             int((tip_y + my) / 2 - perp_y * (width - 1))),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["red_mid"], [
            (tip_x, tip_y),
            (int((tip_x + mx) / 2), int((tip_y + my) / 2 + perp_y)),
            (int((tip_x + mx) / 2), int((tip_y + my) / 2 - perp_y)),
        ])
        # White body
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["beard_dark"], [
            (mx + int(perp_x * width), my + int(perp_y * width)),
            (back_x + int(perp_x * width), back_y + int(perp_y * width)),
            (back_x - int(perp_x * width), back_y - int(perp_y * width)),
            (mx - int(perp_x * width), my - int(perp_y * width)),
        ])
        _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["beard_light"], [
            (mx + int(perp_x * (width - 1)), my + int(perp_y * (width - 1))),
            (back_x + int(perp_x * (width - 1)),
             back_y + int(perp_y * (width - 1))),
            (back_x, back_y),
            (mx, my),
        ])
        # Highlight tip
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["red_light"],
                         (tip_x, tip_y, 1, 1))
        # Fins at back
        fin_len = 3 if big else 2
        for sign in (1, -1):
            fin_tip_x = back_x + int(perp_x * (width + fin_len) * sign)
            fin_tip_y = back_y + int(perp_y * (width + fin_len) * sign)
            _NS_cogsworth._poly(surface, _NS_cogsworth.PALETTE["red_dark"], [
                (back_x + int(perp_x * width * sign),
                 back_y + int(perp_y * width * sign)),
                (fin_tip_x, fin_tip_y),
                (back_x - int(cos_a * 2), back_y - int(sin_a * 2)),
            ])
    def _draw_explosion(surface, ex, ey, t):
        r = int(12 + t * 25)
        a = _NS_cogsworth._alpha(255 * (1 - t))
        for rr in range(r + 4, 0, -3):
            ra = _NS_cogsworth._alpha(a * (r + 4 - rr) / (r + 4))
            _NS_cogsworth._aacircle(surface,
                                    (*_NS_cogsworth.PALETTE["fire_darkest"], ra),
                                    (ex, ey), rr)
        for rr in range(int(r * 0.75), 0, -2):
            ra = _NS_cogsworth._alpha(a * (r * 0.75 - rr) / (r * 0.75))
            _NS_cogsworth._aacircle(surface,
                                    (*_NS_cogsworth.PALETTE["fire_dark"], ra),
                                    (ex, ey), rr)
        _NS_cogsworth._aacircle(surface, (*_NS_cogsworth.PALETTE["fire_mid"], a),
                                (ex, ey), max(2, r // 2))
        _NS_cogsworth._aacircle(surface, (*_NS_cogsworth.PALETTE["fire_light"], a),
                                (ex, ey), max(1, r // 3))
        _NS_cogsworth._aacircle(surface, (*_NS_cogsworth.PALETTE["fire_hot"], a),
                                (ex, ey), max(1, r // 5))
        _NS_cogsworth._aacircle(surface, (*_NS_cogsworth.PALETTE["fire_shine"], a),
                                (ex, ey), max(1, r // 8))
        pygame.draw.rect(surface, (*_NS_cogsworth.PALETTE["white"], a),
                         (ex, ey, 1, 1))
        # Sparks
        for i in range(10):
            ang = i * math.pi / 5 + t * 3
            sx = ex + int(math.cos(ang) * r)
            sy = ey + int(math.sin(ang) * r * 0.8)
            pygame.draw.rect(surface,
                             (*_NS_cogsworth.PALETTE["fire_hot"], a),
                             (sx, sy, 2, 2))
    # ============================================================
    # SKILL W — ROCKET BARRAGE (fan of rockets)
    # ============================================================
    def _draw_rocket_barrage(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_cogsworth._target_position(boss, x, y)
        if progress < 0.1:
            return
        t = (progress - 0.1) / 0.9
        t = min(1.0, t)
        # 6 rockets in a fan
        num_rockets = 6
        start_x = x + facing * 22
        start_y = y + 4
        base_dist = math.sqrt((tx - start_x) ** 2 + (ty - start_y) ** 2)
        base_ang = math.atan2(ty - start_y, (tx - start_x) * facing)
        spread = math.pi / 4
        for r_i in range(num_rockets):
            ang_off = (r_i - (num_rockets - 1) / 2) * (spread / num_rockets)
            r_ang = base_ang + ang_off
            r_start_delay = r_i * 0.06
            r_t = max(0.0, min(1.0, (t - r_start_delay) / (1 - r_start_delay)))
            if r_t <= 0:
                continue
            rx = int(start_x + math.cos(r_ang) * base_dist * r_t * facing)
            ry = int(start_y + math.sin(r_ang) * base_dist * r_t)
            # Smoke trail
            for ti in range(6):
                tt = max(0.0, r_t - ti * 0.06)
                px = int(start_x + math.cos(r_ang) * base_dist * tt * facing)
                py = int(start_y + math.sin(r_ang) * base_dist * tt)
                a = _NS_cogsworth._alpha(180 - ti * 25)
                s = max(1, 4 - ti // 2)
                _NS_cogsworth._aacircle(surface,
                                        (*_NS_cogsworth.PALETTE["smoke_dark"], a),
                                        (px, py), s)
                _NS_cogsworth._aacircle(surface,
                                        (*_NS_cogsworth.PALETTE["smoke_mid"], a),
                                        (px, py), max(1, s - 1))
            # Missile
            _NS_cogsworth._draw_missile(surface, rx, ry, r_ang, facing, big=False)
            # Flame at back
            fx = rx - int(math.cos(r_ang) * 4) * facing
            fy = ry - int(math.sin(r_ang) * 4)
            for rr in range(4, 0, -1):
                a = _NS_cogsworth._alpha(180 * (4 - rr) / 4)
                _NS_cogsworth._aacircle(surface,
                                        (*_NS_cogsworth.PALETTE["fire_mid"], a),
                                        (fx, fy), rr)
            pygame.draw.rect(surface, _NS_cogsworth.PALETTE["fire_hot"],
                             (fx, fy, 1, 1))
            # Impact per rocket (spread hits)
            if r_t > 0.9:
                impact_x = tx + int((r_i - 2.5) * 12)
                impact_y = ty + int((r_i % 3 - 1) * 6)
                _NS_cogsworth._draw_explosion(surface, impact_x, impact_y,
                                              (r_t - 0.9) / 0.1)
    # ============================================================
    # SKILL E — FLAK CANNON (shrapnel spray)
    # ============================================================
    def _draw_flak_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_cogsworth._target_position(boss, x, y)
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.3:
            t = (progress - 0.3) / 0.7
            r = int(20 + t * 30)
            a = _NS_cogsworth._alpha(200 * (1 - t * 0.3))
            pygame.draw.ellipse(surface,
                                (*_NS_cogsworth.PALETTE["fire_darkest"], a),
                                (tx - r, ty + 35 - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_cogsworth.PALETTE["fire_dark"], a),
                                (tx - r + 4, ty + 35 - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4))
    def _draw_flak_cannon(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_cogsworth._target_position(boss, x, y)
        if progress < 0.1:
            return
        t = (progress - 0.1) / 0.9
        # Muzzle flash at chin gun
        gun_x = x + facing * 30
        gun_y = y + 12
        if t < 0.3:
            flash_t = t / 0.3
            fr = int(4 + flash_t * 8)
            for r in range(fr + 3, 0, -1):
                a = _NS_cogsworth._alpha(240 * (fr + 3 - r) / (fr + 3))
                _NS_cogsworth._aacircle(surface,
                                        (*_NS_cogsworth.PALETTE["fire_mid"], a),
                                        (gun_x, gun_y), r)
            _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["fire_hot"],
                                    (gun_x, gun_y), max(1, fr - 3))
            _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["fire_shine"],
                                    (gun_x, gun_y), max(1, fr - 5))
        # Shrapnel spray (many small orange dots)
        num_shots = 24
        for i in range(num_shots):
            shot_seed = i * 0.377
            shot_start_t = (shot_seed % 0.4)
            if t < shot_start_t:
                continue
            shot_t = min(1.0, (t - shot_start_t) / 0.6)
            # Random spread within cone
            spread_ang = (shot_seed - 0.2) * 0.6
            base_ang = math.atan2(ty - gun_y, (tx - gun_x) * facing)
            shot_ang = base_ang + spread_ang
            shot_dist = math.sqrt((tx - gun_x) ** 2 + (ty - gun_y) ** 2)
            # Small random variance in distance
            dist_var = 0.9 + (shot_seed % 0.3)
            sx = int(gun_x + math.cos(shot_ang) * shot_dist * shot_t
                     * dist_var * facing)
            sy = int(gun_y + math.sin(shot_ang) * shot_dist * shot_t
                     * dist_var)
            # Shrapnel dot
            a = _NS_cogsworth._alpha(240 * (1 - shot_t * 0.3))
            _NS_cogsworth._aacircle(surface,
                                    (*_NS_cogsworth.PALETTE["fire_dark"], a),
                                    (sx, sy), 3)
            _NS_cogsworth._aacircle(surface,
                                    (*_NS_cogsworth.PALETTE["fire_mid"], a),
                                    (sx, sy), 2)
            pygame.draw.rect(surface,
                             (*_NS_cogsworth.PALETTE["fire_hot"], a),
                             (sx, sy, 1, 1))
            # Short trail behind each shrapnel
            for ti in range(3):
                tt = max(0.0, shot_t - ti * 0.05)
                px = int(gun_x + math.cos(shot_ang) * shot_dist * tt
                         * dist_var * facing)
                py = int(gun_y + math.sin(shot_ang) * shot_dist * tt
                         * dist_var)
                ta = _NS_cogsworth._alpha(150 - ti * 40)
                pygame.draw.rect(surface,
                                 (*_NS_cogsworth.PALETTE["fire_light"], ta),
                                 (px, py, 1, 1))
        # Target area impact sparks
        if t > 0.4:
            for i in range(8):
                spark_seed = (phase * 2 + i) % 1.0
                sx = tx + int((spark_seed - 0.5) * 40)
                sy = ty + int(((i * 0.33) % 1 - 0.5) * 30)
                a = _NS_cogsworth._alpha(220)
                pygame.draw.rect(surface,
                                 (*_NS_cogsworth.PALETTE["fire_hot"], a),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_cogsworth.PALETTE["fire_shine"], a),
                                 (sx, sy, 1, 1))
    # ============================================================
    # SKILL R — CALL DOWN (bombing run from sky)
    # ============================================================
    def _draw_calldown_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_cogsworth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Target indicator ring
        if progress < 0.3:
            t = progress / 0.3
            r = int(30 + math.sin(phase * 4) * 3)
            a = _NS_cogsworth._alpha(200 * t)
            pygame.draw.ellipse(surface,
                                (*_NS_cogsworth.PALETTE["fire_dark"], a),
                                (tx - r, ty + 30 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_cogsworth.PALETTE["fire_mid"], a),
                                (tx - r + 4, ty + 30 - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4), 2)
            # Crosshair
            pygame.draw.line(surface, (*_NS_cogsworth.PALETTE["fire_hot"], a),
                             (tx - r, ty + 30),
                             (tx + r, ty + 30), 1)
            pygame.draw.line(surface, (*_NS_cogsworth.PALETTE["fire_hot"], a),
                             (tx, ty + 30 - r // 3),
                             (tx, ty + 30 + r // 3), 1)
        else:
            t = (progress - 0.3) / 0.7
            r = int(35 + t * 20)
            a = _NS_cogsworth._alpha(220 * (1 - t * 0.4))
            # Scorched ground
            pygame.draw.ellipse(surface,
                                (*_NS_cogsworth.PALETTE["fire_darkest"], a),
                                (tx - r, ty + 30 - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_cogsworth.PALETTE["fire_dark"], a),
                                (tx - r + 5, ty + 30 - r // 3 + 2,
                                 r * 2 - 10, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                (*_NS_cogsworth.PALETTE["fire_mid"], a),
                                (tx - r + 12, ty + 30 - r // 3 + 5,
                                 r * 2 - 24, r * 2 // 3 - 10))
    def _draw_calldown_bombs(surface, boss, x, y, timer, phase):
        tx, ty = _NS_cogsworth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            return
        # Multiple bombs falling from top
        num_bombs = 6
        for b_i in range(num_bombs):
            # Each bomb has staggered timing and horizontal offset
            b_start = 0.3 + b_i * 0.08
            b_end = b_start + 0.15
            b_x_off = int((b_i - 2.5) * 18)
            b_target_x = tx + b_x_off
            b_target_y = ty + 20
            if progress < b_start:
                continue
            if progress > b_end + 0.15:
                continue
            if progress < b_end:
                # Bomb falling
                fall_t = (progress - b_start) / (b_end - b_start)
                start_y = b_target_y - 200
                by = int(start_y + (b_target_y - start_y) * fall_t)
                bx = b_target_x
                # Bomb sprite
                _NS_cogsworth._draw_bomb(surface, bx, by)
                # Falling trail
                for ti in range(8):
                    tt = max(0.0, fall_t - ti * 0.04)
                    py = int(start_y + (b_target_y - start_y) * tt)
                    a = _NS_cogsworth._alpha(180 - ti * 22)
                    _NS_cogsworth._aacircle(
                        surface,
                        (*_NS_cogsworth.PALETTE["smoke_dark"], a),
                        (bx, py), max(2, 5 - ti // 2),
                    )
                    _NS_cogsworth._aacircle(
                        surface,
                        (*_NS_cogsworth.PALETTE["smoke_mid"], a),
                        (bx, py), max(1, 3 - ti // 2),
                    )
                    if ti < 2:
                        pygame.draw.rect(
                            surface,
                            (*_NS_cogsworth.PALETTE["fire_mid"], a),
                            (bx, py, 1, 2),
                        )
            else:
                # Explosion
                ex_t = (progress - b_end) / 0.15
                _NS_cogsworth._draw_explosion(surface, b_target_x, b_target_y, ex_t)
    def _draw_bomb(surface, bx, by):
        """Small falling bomb shape."""
        # Round body
        _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["shadow_deep"],
                                (bx + 1, by + 1), 4)
        _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["iron_darkest"],
                                (bx, by), 4)
        _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["iron_dark"],
                                (bx, by), 3)
        _NS_cogsworth._aacircle(surface, _NS_cogsworth.PALETTE["iron_mid"],
                                (bx - 1, by - 1), 2)
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["iron_light"],
                         (bx - 1, by - 1, 1, 1))
        # Red stripe
        pygame.draw.line(surface, _NS_cogsworth.PALETTE["red_dark"],
                         (bx - 3, by), (bx + 3, by), 1)
        pygame.draw.rect(surface, _NS_cogsworth.PALETTE["red_mid"],
                         (bx, by, 1, 1))
        # Fins on top
        pygame.draw.line(surface, _NS_cogsworth.PALETTE["iron_darkest"],
                         (bx - 2, by - 5), (bx + 2, by - 5), 2)
        pygame.draw.line(surface, _NS_cogsworth.PALETTE["iron_dark"],
                         (bx, by - 6), (bx, by - 3), 1)

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_broggmar(surface, boss, x, y):
    """Entry point broggmar."""
    return _NS_broggmar.draw_broggmar(surface, boss, x, y)


def draw_ursath(surface, boss, x, y):
    """Entry point ursath."""
    return _NS_ursath.draw_ursath(surface, boss, x, y)


def draw_zhaeris(surface, boss, x, y):
    """Entry point zhaeris."""
    return _NS_zhaeris.draw_zhaeris(surface, boss, x, y)


def draw_cogsworth(surface, boss, x, y):
    """Entry point cogsworth."""
    return _NS_cogsworth.draw_cogsworth(surface, boss, x, y)
