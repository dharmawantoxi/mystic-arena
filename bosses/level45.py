"""
bosses/level45.py - Semua boss Level 45

Berisi:
  - akiraze   (mini boss - MELEE golden tempest, lightning ninja)
  - brumhar   (mini boss - MELEE glacier reaver, frost axe)
  - zorashi   (mini boss - RANGED serpent sage, snake magic)
  - deidara   (TRUE BOSS - RANGED explosive artist, clay bombs)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _ak_ (akiraze), _bh_ (brumhar), _zs_ (zorashi),
    _dei_ (deidara) sudah unik.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# AKIRAZE (GOLDEN TEMPEST) - Mini Boss
# ====================================================================

class _NS_akiraze:
    """Namespace akiraze - Golden Tempest boss (ninja/teleporter)."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (tan)
        "skin_darkest": (110, 75, 55),
        "skin_dark": (180, 130, 95),
        "skin_mid": (225, 180, 140),
        "skin_light": (245, 215, 180),
        # Hair (bright yellow-gold spiky)
        "hair_darkest": (95, 65, 5),
        "hair_dark": (180, 130, 20),
        "hair_mid": (235, 195, 55),
        "hair_light": (255, 230, 110),
        "hair_shine": (255, 250, 200),
        # Robe outer (white/cream haori)
        "robe_darkest": (95, 95, 100),
        "robe_dark": (160, 160, 165),
        "robe_mid": (215, 215, 220),
        "robe_light": (245, 245, 250),
        "robe_shine": (255, 255, 255),
        # Red flame trim on robe
        "flame_darkest": (60, 15, 10),
        "flame_dark": (130, 30, 25),
        "flame_mid": (200, 60, 45),
        "flame_light": (245, 130, 90),
        "flame_hot": (255, 200, 140),
        # Inner outfit (dark blue jonin)
        "outfit_darkest": (10, 15, 30),
        "outfit_dark": (25, 40, 65),
        "outfit_mid": (55, 75, 105),
        "outfit_light": (95, 115, 145),
        # Vest (dark green flak jacket)
        "vest_darkest": (15, 30, 15),
        "vest_dark": (35, 55, 30),
        "vest_mid": (65, 90, 55),
        "vest_light": (110, 140, 90),
        # Kunai/metal (gold + steel)
        "metal_dark": (30, 30, 40),
        "metal_mid": (85, 90, 100),
        "metal_light": (170, 175, 190),
        "metal_shine": (240, 245, 255),
        "gold_dark": (100, 70, 20),
        "gold_mid": (200, 155, 50),
        "gold_light": (250, 220, 110),
        "gold_shine": (255, 250, 200),
        # Chakra blue (energy orb, projectile)
        "chakra_darkest": (5, 20, 55),
        "chakra_dark": (20, 65, 145),
        "chakra_mid": (55, 145, 235),
        "chakra_light": (140, 210, 255),
        "chakra_hot": (200, 240, 255),
        "chakra_shine": (240, 250, 255),
        # Lightning/flash yellow (skill)
        "lightning_dark": (100, 80, 5),
        "lightning_mid": (230, 200, 25),
        "lightning_light": (255, 240, 100),
        "lightning_hot": (255, 250, 180),
        "lightning_shine": (255, 255, 240),
        # Eye (blue)
        "eye_dark": (10, 30, 75),
        "eye_mid": (60, 130, 220),
        "eye_light": (140, 210, 255),
        "eye_shine": (245, 245, 250),
        # Headband
        "band_dark": (35, 40, 55),
        "band_mid": (75, 85, 100),
        "band_light": (145, 155, 170),
        # Smoke tail
        "smoke_darkest": (10, 15, 25),
        "smoke_dark": (30, 40, 60),
        "smoke_mid": (65, 80, 110),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_akiraze._clamp(color)
        if _NS_akiraze.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_akiraze._clamp(color)
        if _NS_akiraze.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_akiraze._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_akiraze(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_akiraze._detect_moving(boss)
        _NS_akiraze._update_attack_anim(boss)
        attacking = getattr(boss, "_ak_attack_active", False)
        # Ambient
        _NS_akiraze._draw_chakra_aura(surface, x, y, pulse)
        _NS_akiraze._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX
        if active_skill == "e":
            _NS_akiraze._draw_seal_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_akiraze._draw_teleport_ground(surface, boss, x, y, skill_timer, pulse)
        # Body
        if active_skill == "r":
            _NS_akiraze._draw_teleport_body(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_akiraze._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_akiraze._draw_walk(surface, boss, x, y)
        else:
            _NS_akiraze._draw_idle(surface, boss, x, y)
        # Foreground FX
        if active_skill == "q":
            _NS_akiraze._draw_galeshot_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_akiraze._draw_flashkunai_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_akiraze._draw_seal_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_akiraze._draw_teleport_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_ak_attack_active", False))
        if not active and timer <= 2:
            boss._ak_attack_active = True
            boss._ak_attack_frame = 0
            active = True
        if active:
            boss._ak_attack_frame = int(getattr(boss, "_ak_attack_frame", 0)) + 1
            if boss._ak_attack_frame >= cooldown:
                boss._ak_attack_active = False
                boss._ak_attack_frame = 0
                active = False
        boss._ak_attack_progress = (
            min(1.0, getattr(boss, "_ak_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_ak_last_x"):
            boss._ak_last_x = boss.x
            boss._ak_last_y = boss.y
            return False
        dx = abs(boss.x - boss._ak_last_x)
        dy = abs(boss.y - boss._ak_last_y)
        boss._ak_last_x = boss.x
        boss._ak_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_akiraze._draw_shadow(surface, x, y + 50)
        _NS_akiraze._draw_smoke_base(surface, x, y + 26 + bob, boss.pulse)
        _NS_akiraze._draw_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")
    def _draw_walk(surface, boss, x, y):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.7) * 5)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_akiraze._draw_shadow(surface, x + sway, y + 50)
        _NS_akiraze._draw_smoke_base(surface, x + sway, y + 26 + bob, phase,
                                     moving=True, facing=boss.direction)
        _NS_akiraze._draw_body(surface, x + sway, y + bob, boss.direction, phase, "walk")
    def _draw_attack(surface, boss, x, y):
        progress = getattr(boss, "_ak_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        bob = int(math.sin(boss.pulse * 0.5) * 3)
        # Fast throw motion
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 3) * boss.direction
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            lunge = int((-3 + t * 10)) * boss.direction
        else:
            t = (progress - 0.5) / 0.5
            lunge = int(7 * (1 - t)) * boss.direction
        _NS_akiraze._draw_shadow(surface, x + lunge, y + 50)
        _NS_akiraze._draw_smoke_base(surface, x + lunge, y + 26 + bob, boss.pulse,
                                     intense=True)
        _NS_akiraze._draw_body(surface, x + lunge, y + bob, boss.direction, boss.pulse,
                               "attack", progress)
        _NS_akiraze._draw_chakra_projectile(surface, boss, x + lunge, y + bob, progress)
    def _draw_teleport_body(surface, boss, x, y, timer, phase):
        """Body flickers/teleports during R."""
        duration = 100
        progress = 1 - timer / duration
        # Body fade in/out with afterimages
        for i in range(3):
            offset = -boss.direction * i * 10
            alpha_mult = 1.0 - i * 0.3
            temp = pygame.Surface((150, 150), pygame.SRCALPHA)
            _NS_akiraze._draw_body(temp, 75, 75, boss.direction, phase, "idle")
            temp.set_alpha(int(200 * alpha_mult))
            surface.blit(temp, (x + offset - 75, y - 75))
        # Flash effect around body
        for i in range(6):
            angle = phase * 3 + i * math.pi / 3
            r = 20 + int(math.sin(phase * 5) * 5)
            sx = x + int(math.cos(angle) * r)
            sy = y + int(math.sin(angle) * r)
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["lightning_hot"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["lightning_shine"], (sx, sy, 1, 1))
    # ============================================================
    # BODY - Ninja with cloak
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0.0):
        # Cloak/haori BEHIND with red flame trim
        _NS_akiraze._draw_cloak(surface, cx, cy, facing, phase)
        # Legs
        _NS_akiraze._draw_legs(surface, cx, cy, facing, phase, action)
        # Torso outfit + vest
        _NS_akiraze._draw_torso(surface, cx, cy, facing, phase)
        # Back arm
        _NS_akiraze._draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress)
        # Head + hair
        _NS_akiraze._draw_head(surface, cx, cy - 22, facing, phase)
        # Spiky hair top/sides
        _NS_akiraze._draw_spiky_hair(surface, cx, cy - 22, facing, phase)
        # Headband
        _NS_akiraze._draw_headband(surface, cx, cy - 22, facing, phase)
        # Front arm (casting)
        _NS_akiraze._draw_front_arm(surface, cx, cy, facing, phase, action, attack_progress)
    def _draw_cloak(surface, cx, cy, facing, phase):
        """White haori with red flame trim at bottom."""
        sway = math.sin(phase * 0.6) * 2
        back = -facing
        # Main cloak shape (extends behind and to sides)
        cloak_shape = [
            (cx - 12, cy - 8),
            (cx - 16 + int(sway * 0.5), cy - 2),
            (cx - 18 + int(sway), cy + 10),
            (cx - 17 + int(sway), cy + 22),
            (cx - 12 + int(sway * 0.7), cy + 30),
            (cx - 4 + int(sway * 0.5), cy + 36),
            (cx + 4 + int(sway * 0.3), cy + 36),
            (cx + 12 + int(sway * 0.3), cy + 30),
            (cx + 17 + int(sway * 0.3), cy + 22),
            (cx + 18, cy + 10),
            (cx + 16, cy - 2),
            (cx + 12, cy - 8),
        ]
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["shadow_deep"],
              [(px + 2, py + 3) for px, py in cloak_shape])
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["robe_darkest"], cloak_shape)
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["robe_dark"], [
            (cx - 11, cy - 7), (cx - 15 + int(sway * 0.5), cy - 1),
            (cx - 17 + int(sway * 0.8), cy + 10),
            (cx - 16 + int(sway * 0.8), cy + 21),
            (cx - 11 + int(sway * 0.5), cy + 29),
            (cx - 3 + int(sway * 0.3), cy + 35),
            (cx + 3 + int(sway * 0.3), cy + 35),
            (cx + 11 + int(sway * 0.3), cy + 29),
            (cx + 16 + int(sway * 0.3), cy + 21),
            (cx + 17, cy + 10), (cx + 15, cy - 1), (cx + 11, cy - 7),
        ])
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["robe_mid"], [
            (cx - 9, cy - 5), (cx - 13, cy),
            (cx - 15 + int(sway * 0.5), cy + 10),
            (cx - 14 + int(sway * 0.5), cy + 20),
            (cx - 9 + int(sway * 0.3), cy + 28),
            (cx + 9 + int(sway * 0.2), cy + 28),
            (cx + 14, cy + 20),
            (cx + 15, cy + 10), (cx + 13, cy), (cx + 9, cy - 5),
        ])
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["robe_light"], [
            (cx - 6, cy - 3), (cx - 10, cy + 2),
            (cx - 11, cy + 15),
            (cx - 7, cy + 24), (cx + 7, cy + 24),
            (cx + 11, cy + 15), (cx + 10, cy + 2), (cx + 6, cy - 3),
        ])
        # RED FLAME TRIM at bottom (jagged flame pattern)
        flame_y = cy + 22
        # Left side flame trim
        for side_i, side in enumerate([-1, 1]):
            # Series of flame triangles on cloak edge
            for i in range(4):
                base_dist = 6 + i * 3
                base_x = cx + side * (base_dist + int(sway * 0.3))
                flame_base_y = flame_y + i * 3
                flame_tip_y = flame_base_y + 8 + i * 2
                flame_w = 4
                # Flame shape (jagged triangle down)
                _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["flame_darkest"], [
                    (base_x - flame_w, flame_base_y),
                    (base_x, flame_tip_y),
                    (base_x + flame_w, flame_base_y),
                ])
                _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["flame_dark"], [
                    (base_x - flame_w + 1, flame_base_y + 1),
                    (base_x, flame_tip_y - 1),
                    (base_x + flame_w - 1, flame_base_y + 1),
                ])
                _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["flame_mid"], [
                    (base_x - flame_w + 2, flame_base_y + 2),
                    (base_x, flame_tip_y - 3),
                    (base_x + flame_w - 2, flame_base_y + 2),
                ])
                # Bright tip
                pygame.draw.rect(surface, _NS_akiraze.PALETTE["flame_light"],
                                 (base_x, flame_tip_y - 2, 1, 2))
                pygame.draw.rect(surface, _NS_akiraze.PALETTE["flame_hot"],
                                 (base_x, flame_tip_y - 1, 1, 1))
        # Center bottom flame trim
        for i in range(3):
            fx = cx - 4 + i * 4 + int(sway * 0.3)
            fbase_y = cy + 32
            ftip_y = fbase_y + 6
            _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["flame_darkest"], [
                (fx - 3, fbase_y), (fx, ftip_y), (fx + 3, fbase_y),
            ])
            _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["flame_dark"], [
                (fx - 2, fbase_y + 1), (fx, ftip_y - 1), (fx + 2, fbase_y + 1),
            ])
            _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["flame_mid"], [
                (fx - 1, fbase_y + 2), (fx, ftip_y - 2), (fx + 1, fbase_y + 2),
            ])
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["flame_light"], (fx, ftip_y - 1, 1, 1))
    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Dark blue ninja pants + sandals."""
        step_offset = 0
        if action == "walk":
            step_offset = math.sin(phase * 1.5) * 2
        for i, (leg_x, leg_offset) in enumerate([(-5, step_offset), (5, -step_offset)]):
            leg_top_y = cy + 12
            leg_bot_y = cy + 22 + int(leg_offset)
            # Pants
            _NS_akiraze._aaline(surface, _NS_akiraze.PALETTE["shadow_deep"],
                    (cx + leg_x + 1, leg_top_y + 1),
                    (cx + leg_x + 1, leg_bot_y + 1), 5)
            _NS_akiraze._aaline(surface, _NS_akiraze.PALETTE["outfit_darkest"],
                    (cx + leg_x, leg_top_y), (cx + leg_x, leg_bot_y), 4)
            _NS_akiraze._aaline(surface, _NS_akiraze.PALETTE["outfit_dark"],
                    (cx + leg_x, leg_top_y), (cx + leg_x, leg_bot_y), 3)
            _NS_akiraze._aaline(surface, _NS_akiraze.PALETTE["outfit_mid"],
                    (cx + leg_x - 1, leg_top_y), (cx + leg_x - 1, leg_bot_y), 1)
            # Bandage wrap at ankle (white)
            for w in range(2):
                pygame.draw.line(surface, _NS_akiraze.PALETTE["robe_light"],
                                 (cx + leg_x - 2, leg_bot_y - 3 + w * 2),
                                 (cx + leg_x + 2, leg_bot_y - 3 + w * 2), 1)
            # Sandal (dark)
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["shadow_deep"],
                             (cx + leg_x - 4, leg_bot_y + 1, 9, 3))
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["outfit_darkest"],
                             (cx + leg_x - 4, leg_bot_y, 9, 3))
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["outfit_dark"],
                             (cx + leg_x - 3, leg_bot_y, 7, 2))
            # Strap
            pygame.draw.line(surface, _NS_akiraze.PALETTE["outfit_darkest"],
                             (cx + leg_x, leg_bot_y - 2),
                             (cx + leg_x + 2, leg_bot_y + 1), 1)
    def _draw_torso(surface, cx, cy, facing, phase):
        """Dark blue outfit + green vest."""
        # Inner outfit (dark blue turtleneck-ish)
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["outfit_darkest"], [
            (cx - 9, cy - 10),
            (cx - 10, cy - 4),
            (cx - 9, cy + 4),
            (cx + 9, cy + 4),
            (cx + 10, cy - 4),
            (cx + 9, cy - 10),
            (cx + 4, cy - 12),
            (cx - 4, cy - 12),
        ])
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["outfit_dark"], [
            (cx - 8, cy - 9), (cx - 9, cy - 4),
            (cx - 8, cy + 3), (cx + 8, cy + 3),
            (cx + 9, cy - 4), (cx + 8, cy - 9),
            (cx + 3, cy - 11), (cx - 3, cy - 11),
        ])
        # VEST (dark green flak jacket)
        vest_shape = [
            (cx - 11, cy - 8),
            (cx - 13, cy - 3),
            (cx - 12, cy + 4),
            (cx - 10, cy + 12),
            (cx + 10, cy + 12),
            (cx + 12, cy + 4),
            (cx + 13, cy - 3),
            (cx + 11, cy - 8),
            (cx + 5, cy - 11),
            (cx - 5, cy - 11),
        ]
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["shadow_deep"],
              [(px + 1, py + 2) for px, py in vest_shape])
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["vest_darkest"], vest_shape)
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["vest_dark"], [
            (cx - 10, cy - 7), (cx - 12, cy - 2),
            (cx - 11, cy + 4), (cx - 9, cy + 11),
            (cx + 9, cy + 11), (cx + 11, cy + 4),
            (cx + 12, cy - 2), (cx + 10, cy - 7),
            (cx + 4, cy - 10), (cx - 4, cy - 10),
        ])
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["vest_mid"], [
            (cx - 8, cy - 5), (cx - 10, cy),
            (cx - 9, cy + 3), (cx - 7, cy + 9),
            (cx + 7, cy + 9), (cx + 9, cy + 3),
            (cx + 10, cy), (cx + 8, cy - 5),
            (cx + 3, cy - 8), (cx - 3, cy - 8),
        ])
        # Vest pockets
        for side in (-1, 1):
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["vest_darkest"],
                             (cx + side * 6 - 2, cy - 2, 4, 4))
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["vest_dark"],
                             (cx + side * 6 - 2, cy - 2, 4, 1))
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["vest_light"],
                             (cx + side * 6 - 2, cy - 2, 4, 1))
        # Zipper down center
        pygame.draw.line(surface, _NS_akiraze.PALETTE["vest_darkest"],
                         (cx, cy - 10), (cx, cy + 11), 1)
        for i in range(5):
            y_off = -8 + i * 4
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["metal_mid"],
                             (cx, cy + y_off, 1, 1))
        # V-neck line
        pygame.draw.line(surface, _NS_akiraze.PALETTE["outfit_darkest"],
                         (cx - 4, cy - 10), (cx, cy - 4), 1)
        pygame.draw.line(surface, _NS_akiraze.PALETTE["outfit_darkest"],
                         (cx + 4, cy - 10), (cx, cy - 4), 1)
        # BELT with kunai pouch
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["outfit_darkest"],
                         (cx - 12, cy + 11, 24, 3))
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["outfit_dark"],
                         (cx - 12, cy + 11, 24, 1))
        # Belt buckle
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["metal_dark"],
                         (cx - 2, cy + 10, 4, 4))
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["metal_light"],
                         (cx - 2, cy + 10, 4, 1))
    def _draw_head(surface, cx, cy, facing, phase):
        """Ninja face."""
        # Face shape
        face_shape = [
            (cx - 6, cy + 6),
            (cx - 7, cy + 2),
            (cx - 7, cy - 3),
            (cx - 4, cy - 7),
            (cx + 4, cy - 7),
            (cx + 7, cy - 3),
            (cx + 7, cy + 2),
            (cx + 6, cy + 6),
            (cx + 2, cy + 8),
            (cx - 2, cy + 8),
        ]
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in face_shape])
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["skin_darkest"], face_shape)
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["skin_dark"], [
            (cx - 5, cy + 5), (cx - 6, cy + 2),
            (cx - 6, cy - 2), (cx - 3, cy - 6),
            (cx + 3, cy - 6), (cx + 6, cy - 2),
            (cx + 6, cy + 2), (cx + 5, cy + 5),
            (cx + 1, cy + 7), (cx - 1, cy + 7),
        ])
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["skin_mid"], [
            (cx - 4, cy + 3), (cx - 5, cy),
            (cx - 4, cy - 4), (cx - 2, cy - 5),
            (cx + 2, cy - 5), (cx + 4, cy - 4),
            (cx + 5, cy), (cx + 4, cy + 3),
        ])
        # Cheek highlight
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["skin_light"], [
            (cx - 3, cy - 1), (cx - 1, cy - 3),
            (cx - 1, cy), (cx - 3, cy + 1),
        ])
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["skin_light"], [
            (cx + 1, cy - 3), (cx + 3, cy - 1),
            (cx + 3, cy + 1), (cx + 1, cy),
        ])
        # EYES (blue determined)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_x in (cx - 3, cx + 3):
            # Eye white
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["skin_light"],
                             (eye_x - 1, cy - 2, 2, 2))
            # Iris blue
            for r in range(3, 0, -1):
                alpha = _NS_akiraze._alpha(100 * (3 - r) / 3 * pulse)
                _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["chakra_mid"], alpha),
                                      (eye_x, cy - 1), r)
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["eye_dark"],
                             (eye_x - 1, cy - 2, 2, 2))
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["eye_mid"],
                             (eye_x - 1, cy - 1, 2, 1))
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["eye_light"],
                             (eye_x, cy - 1, 1, 1))
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["eye_shine"],
                             (eye_x, cy - 1, 1, 1))
        # Sharp determined eyebrows
        pygame.draw.line(surface, _NS_akiraze.PALETTE["hair_darkest"],
                         (cx - 4, cy - 4), (cx - 1, cy - 3), 1)
        pygame.draw.line(surface, _NS_akiraze.PALETTE["hair_darkest"],
                         (cx + 1, cy - 3), (cx + 4, cy - 4), 1)
        # Nose
        pygame.draw.line(surface, _NS_akiraze.PALETTE["skin_darkest"],
                         (cx, cy), (cx, cy + 3), 1)
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["skin_dark"], (cx - 1, cy + 3, 3, 1))
        # Mouth
        pygame.draw.line(surface, _NS_akiraze.PALETTE["hair_darkest"],
                         (cx - 2, cy + 5), (cx + 2, cy + 5), 1)
    def _draw_spiky_hair(surface, cx, cy, facing, phase):
        """Spiky yellow hair with multiple spikes."""
        sway = math.sin(phase * 0.4) * 1
        # Main hair mass (base cover on top of head)
        hair_shape = [
            (cx - 8, cy + 2),
            (cx - 9, cy - 2),
            (cx - 7, cy - 6),
            (cx - 3, cy - 8),
            (cx + 3, cy - 8),
            (cx + 7, cy - 6),
            (cx + 9, cy - 2),
            (cx + 8, cy + 2),
        ]
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["shadow_deep"],
              [(p[0] + 1, p[1] + 1) for p in hair_shape])
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["hair_darkest"], hair_shape)
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["hair_dark"], [
            (cx - 7, cy + 1), (cx - 8, cy - 1),
            (cx - 6, cy - 5), (cx - 2, cy - 7),
            (cx + 2, cy - 7), (cx + 6, cy - 5),
            (cx + 8, cy - 1), (cx + 7, cy + 1),
        ])
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["hair_mid"], [
            (cx - 5, cy), (cx - 6, cy - 3),
            (cx - 3, cy - 6), (cx + 3, cy - 6),
            (cx + 6, cy - 3), (cx + 5, cy),
        ])
        # SPIKY POINTS (multiple pointing up/sides)
        spike_configs = [
            # (base_x, base_y, tip_x_off, tip_y_off, size)
            (-7, -4, -4, -8, 4),
            (-4, -7, -2, -12, 5),
            (-1, -8, -1, -14, 6),
            (2, -8, 3, -13, 5),
            (5, -7, 6, -10, 4),
            (7, -4, 9, -6, 3),
            (-8, -1, -12, -3, 3),
            (8, -1, 11, -3, 3),
        ]
        for bx, by, tx_off, ty_off, size in spike_configs:
            wave = math.sin(phase * 0.6 + bx) * 1
            base_x = cx + bx
            base_y = cy + by
            tip_x = cx + tx_off + int(wave * 0.3)
            tip_y = cy + ty_off + int(wave * 0.5)
            # Shadow
            _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["shadow_deep"], [
                (base_x - 2, base_y + 1),
                (tip_x + 1, tip_y + 1),
                (base_x + 2, base_y + 1),
            ])
            # Spike main
            _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["hair_darkest"], [
                (base_x - 2, base_y),
                (tip_x, tip_y),
                (base_x + 2, base_y),
            ])
            _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["hair_dark"], [
                (base_x - 1, base_y - 1),
                (tip_x, tip_y),
                (base_x + 1, base_y - 1),
            ])
            _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["hair_mid"], [
                (base_x, base_y - 2),
                (tip_x, tip_y),
                (base_x + 1, base_y - 1),
            ])
            # Bright edge
            pygame.draw.line(surface, _NS_akiraze.PALETTE["hair_light"],
                             (base_x - 1, base_y - 1), (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["hair_shine"], (tip_x, tip_y, 1, 1))
        # Bangs (fall down forehead)
        for side in (-1, 1):
            for i in range(2):
                bang_x = cx + side * (2 + i * 2)
                pygame.draw.line(surface, _NS_akiraze.PALETTE["hair_dark"],
                                 (bang_x, cy - 2), (bang_x + side, cy + 1 + i), 2)
                pygame.draw.line(surface, _NS_akiraze.PALETTE["hair_mid"],
                                 (bang_x - 1, cy - 2), (bang_x - 1 + side, cy + 1 + i), 1)
                pygame.draw.line(surface, _NS_akiraze.PALETTE["hair_light"],
                                 (bang_x - 1, cy - 1), (bang_x - 1 + side, cy + i), 1)
    def _draw_headband(surface, cx, cy, facing, phase):
        """Metal-plated headband."""
        # Band strap (dark)
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["shadow_deep"],
                         (cx - 8, cy - 4, 16, 3))
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["band_dark"],
                         (cx - 8, cy - 5, 16, 3))
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["band_mid"],
                         (cx - 8, cy - 5, 16, 1))
        # Metal plate (center)
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["metal_dark"],
                         (cx - 5, cy - 5, 10, 3))
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["metal_mid"],
                         (cx - 5, cy - 5, 10, 2))
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["metal_light"],
                         (cx - 5, cy - 5, 10, 1))
        # Symbol on plate (small spiral)
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["gold_dark"], (cx - 1, cy - 4, 2, 1))
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["gold_light"], (cx, cy - 4, 1, 1))
        alpha = _NS_akiraze._alpha(180 * pulse)
        pygame.draw.rect(surface, (*_NS_akiraze.PALETTE["gold_shine"], alpha), (cx, cy - 4, 1, 1))
        # Cloth tails hanging on sides
        for side in (-1, 1):
            wave = math.sin(phase * 0.5 + side) * 1
            pygame.draw.line(surface, _NS_akiraze.PALETTE["band_dark"],
                             (cx + side * 8, cy - 3),
                             (cx + side * 9 + int(wave), cy + 2), 2)
            pygame.draw.line(surface, _NS_akiraze.PALETTE["band_mid"],
                             (cx + side * 8, cy - 3),
                             (cx + side * 9 + int(wave), cy + 2), 1)
    def _draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm subtle pose."""
        arm_sway = math.sin(phase * 0.5) * 1
        back = -facing
        shoulder_x = cx + back * 10
        shoulder_y = cy - 6
        if action == "attack":
            # Pull back preparing throw
            t = attack_progress
            elbow_x = shoulder_x + back * (4 + int(t * 3))
            elbow_y = shoulder_y + 3 - int(t * 3)
            hand_x = elbow_x + back * 2
            hand_y = elbow_y + 4
        else:
            elbow_x = shoulder_x + back * 3
            elbow_y = shoulder_y + 6 + int(arm_sway)
            hand_x = elbow_x + back * 1
            hand_y = elbow_y + 8
        _NS_akiraze._draw_arm_segment(surface, (shoulder_x, shoulder_y),
                                       (elbow_x, elbow_y), 5, 0.8)
        _NS_akiraze._draw_arm_segment(surface, (elbow_x, elbow_y),
                                       (hand_x, hand_y), 4, 0.8)
        # Hand with wrapping
        _NS_akiraze._draw_wrapped_hand(surface, hand_x, hand_y, back, phase, 0.8)
    def _draw_front_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm - throws kunai/casts."""
        arm_sway = math.sin(phase * 0.5) * 1
        shoulder_x = cx + facing * 10
        shoulder_y = cy - 6
        if action == "attack":
            if attack_progress < 0.3:
                t = attack_progress / 0.3
                arm_forward = int(t * 2)
                arm_raise = int(t * 2)
            elif attack_progress < 0.5:
                t = (attack_progress - 0.3) / 0.2
                arm_forward = int(2 + t * 12)
                arm_raise = int(2 - t * 2)
            else:
                t = (attack_progress - 0.5) / 0.5
                arm_forward = int(14 * (1 - t))
                arm_raise = 0
        else:
            # Idle: hand extended slightly forward
            arm_forward = 3
            arm_raise = int(arm_sway)
        elbow_x = shoulder_x + facing * (4 + arm_forward // 2)
        elbow_y = shoulder_y + 3 - arm_raise
        hand_x = shoulder_x + facing * (9 + arm_forward)
        hand_y = shoulder_y + 2 - arm_raise
        _NS_akiraze._draw_arm_segment(surface, (shoulder_x, shoulder_y),
                                       (elbow_x, elbow_y), 5, 1.0)
        _NS_akiraze._draw_arm_segment(surface, (elbow_x, elbow_y),
                                       (hand_x, hand_y), 4, 1.0)
        _NS_akiraze._draw_wrapped_hand(surface, hand_x, hand_y, facing, phase, 1.0,
                                        casting=(action == "attack"))
    def _draw_arm_segment(surface, p1, p2, thickness, depth_shade=1.0):
        """Ninja sleeve arm (white/vest)."""
        def shade(color):
            return tuple(int(c * depth_shade) for c in color)
        _NS_akiraze._aaline(surface, _NS_akiraze.PALETTE["shadow_deep"],
                (p1[0] + 2, p1[1] + 2), (p2[0] + 2, p2[1] + 2), thickness + 1)
        _NS_akiraze._aaline(surface, shade(_NS_akiraze.PALETTE["outfit_darkest"]),
                p1, p2, thickness)
        _NS_akiraze._aaline(surface, shade(_NS_akiraze.PALETTE["outfit_dark"]),
                p1, p2, max(1, thickness - 2))
        _NS_akiraze._aaline(surface, shade(_NS_akiraze.PALETTE["outfit_mid"]),
                (p1[0] - 1, p1[1] - 1), (p2[0] - 1, p2[1] - 1),
                max(1, thickness - 4))
    def _draw_wrapped_hand(surface, cx, cy, facing, phase, depth_shade=1.0, casting=False):
        """Hand with bandage wrapping."""
        def shade(color):
            return tuple(int(c * depth_shade) for c in color)
        # White bandage wrap
        pygame.draw.rect(surface, shade(_NS_akiraze.PALETTE["robe_mid"]),
                         (cx - 3, cy - 2, 6, 4))
        pygame.draw.rect(surface, shade(_NS_akiraze.PALETTE["robe_light"]),
                         (cx - 3, cy - 2, 6, 1))
        # Wrap lines
        for i in range(2):
            pygame.draw.line(surface, shade(_NS_akiraze.PALETTE["robe_darkest"]),
                             (cx - 3, cy - 1 + i * 2), (cx + 3, cy - 1 + i * 2), 1)
        # Skin fingers extending
        pygame.draw.rect(surface, shade(_NS_akiraze.PALETTE["skin_dark"]),
                         (cx + facing * 2, cy, 3, 2))
        pygame.draw.rect(surface, shade(_NS_akiraze.PALETTE["skin_mid"]),
                         (cx + facing * 2, cy, 3, 1))
        # Casting glow
        if casting:
            pulse = math.sin(phase * 3) * 0.3 + 0.7
            palm_x = cx + facing * 3
            palm_y = cy + 1
            for r in range(6, 0, -1):
                alpha = _NS_akiraze._alpha(200 * (6 - r) / 6 * pulse)
                _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["chakra_mid"], alpha),
                                      (palm_x, palm_y), r)
            _NS_akiraze._aacircle(surface, _NS_akiraze.PALETTE["chakra_light"], (palm_x, palm_y), 2)
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["chakra_shine"], (palm_x, palm_y, 1, 1))
    # ============================================================
    # AUTO-ATTACK - CHAKRA BOLT
    # ============================================================
    def _draw_chakra_projectile(surface, boss, x, y, progress):
        """Small blue chakra bolt."""
        facing = boss.direction
        hand_x = x + facing * 22
        hand_y = y - 4
        if progress < 0.3:
            # Charge
            t = progress / 0.3
            cr = int(3 + t * 6)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_akiraze._alpha(200 * (cr + 3 - r) / (cr + 3) * t)
                _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["chakra_dark"], alpha),
                                      (hand_x, hand_y), r)
            _NS_akiraze._aacircle(surface, _NS_akiraze.PALETTE["chakra_mid"], (hand_x, hand_y),
                                  max(1, cr - 2))
            _NS_akiraze._aacircle(surface, _NS_akiraze.PALETTE["chakra_light"], (hand_x, hand_y),
                                  max(1, cr - 4))
            for i in range(4):
                angle = progress * 20 + i * math.pi / 2
                sx = hand_x + int(math.cos(angle) * (cr + 2))
                sy = hand_y + int(math.sin(angle) * (cr + 2))
                pygame.draw.rect(surface, _NS_akiraze.PALETTE["chakra_hot"], (sx, sy, 1, 1))
            return
        if progress < 0.5:
            return
        tx, ty = _NS_akiraze._target_position(boss, x, y)
        start_x = hand_x + facing * 4
        start_y = hand_y
        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Fast trail
        for i in range(8):
            trail_t = max(0.0, t - i * 0.045)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_akiraze._alpha(230 - i * 25)
            size = max(1, 6 - i)
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["chakra_darkest"], alpha),
                                  (px, py), size)
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["chakra_dark"], alpha),
                                  (px, py), max(1, size - 1))
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["chakra_mid"], alpha),
                                  (px, py), max(1, size - 2))
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["chakra_light"], alpha),
                                  (px, py), max(1, size - 3))
        # Bright head
        for r in range(9, 3, -1):
            alpha = _NS_akiraze._alpha(90 * (9 - r) / 9)
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["chakra_light"], alpha), (bx, by), r)
        _NS_akiraze._aacircle(surface, _NS_akiraze.PALETTE["chakra_darkest"], (bx, by), 6)
        _NS_akiraze._aacircle(surface, _NS_akiraze.PALETTE["chakra_dark"], (bx, by), 4)
        _NS_akiraze._aacircle(surface, _NS_akiraze.PALETTE["chakra_mid"], (bx, by), 3)
        _NS_akiraze._aacircle(surface, _NS_akiraze.PALETTE["chakra_light"], (bx, by), 2)
        _NS_akiraze._aacircle(surface, _NS_akiraze.PALETTE["chakra_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["white"], (bx, by, 1, 1))
        # Impact
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(8 + st * 18)
            alpha = _NS_akiraze._alpha(240 * (1 - st))
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["chakra_dark"], alpha),
                                  (tx, ty), radius, 3)
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["chakra_mid"], alpha),
                                  (tx, ty), max(1, radius - 4), 2)
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["chakra_light"], alpha),
                                  (tx, ty), max(1, radius - 8), 1)
            for i in range(10):
                a_s = i * math.pi / 5
                ex = tx + int(math.cos(a_s) * radius)
                ey = ty + int(math.sin(a_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_akiraze.PALETTE["chakra_hot"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # SMOKE BASE
    # ============================================================
    def _draw_smoke_base(surface, cx, cy, phase, intense=False, moving=False, facing=1):
        strength = 1.3 if intense else 1.0
        smoke = pygame.Surface((100, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(20, 3, -2):
            alpha = _NS_akiraze._alpha((20 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(smoke, (*_NS_akiraze.PALETTE["smoke_darkest"], alpha),
                    (50 - radius, 25 - radius // 2, radius * 2, max(3, radius)))
        for radius in range(14, 3, -2):
            alpha = _NS_akiraze._alpha((14 - radius) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(smoke, (*_NS_akiraze.PALETTE["smoke_dark"], alpha),
                    (50 - radius, 25 - radius // 2, radius * 2, max(2, radius)))
        surface.blit(smoke, (cx - 50, cy - 12))
        # Rising golden/blue particles
        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            px = cx - 18 + i * 5 + int(math.sin(phase + i) * 3)
            py = cy + 12 - int(t * 22)
            alpha = _NS_akiraze._alpha(210 * (1 - t) * strength)
            if alpha > 0:
                col = _NS_akiraze.PALETTE["lightning_mid"] if i % 2 == 0 else _NS_akiraze.PALETTE["chakra_mid"]
                hot = _NS_akiraze.PALETTE["lightning_hot"] if i % 2 == 0 else _NS_akiraze.PALETTE["chakra_hot"]
                pygame.draw.rect(surface, (*col, alpha), (px, py, 1, 1))
                pygame.draw.rect(surface, (*hot, alpha), (px, py, 1, 1))
        if moving:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + 8 + int(math.sin(phase + i) * 2)
                alpha = _NS_akiraze._alpha(160 - i * 30)
                if alpha <= 0:
                    continue
                _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["smoke_dark"], alpha),
                                      (sx, sy), max(2, 6 - i))
                pygame.draw.rect(surface, (*_NS_akiraze.PALETTE["lightning_light"], alpha),
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
        pygame.draw.ellipse(shadow, (10, 15, 30, 150), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (30, 60, 120, 90), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_chakra_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_akiraze._alpha((90 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_akiraze._aacircle(aura, (*_NS_akiraze.PALETTE["chakra_darkest"], alpha),
                                      (110, 100), radius)
        for radius in range(55, 5, -3):
            alpha = _NS_akiraze._alpha((55 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_akiraze._aacircle(aura, (*_NS_akiraze.PALETTE["chakra_dark"], alpha),
                                      (110, 100), radius)
        # Yellow inner tint
        for radius in range(28, 5, -2):
            alpha = _NS_akiraze._alpha((28 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_akiraze._aacircle(aura, (*_NS_akiraze.PALETTE["lightning_dark"], alpha),
                                      (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))
        # Golden sparkles
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 45 + int(math.sin(phase + i) * 14)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            col = _NS_akiraze.PALETTE["lightning_mid"] if i % 2 == 0 else _NS_akiraze.PALETTE["chakra_mid"]
            hot = _NS_akiraze.PALETTE["lightning_hot"] if i % 2 == 0 else _NS_akiraze.PALETTE["chakra_hot"]
            pygame.draw.rect(surface, col, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot, (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_akiraze.PALETTE["chakra_darkest"], 200),
                            (5, 20, 170, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_akiraze.PALETTE["chakra_dark"], 220),
                            (14, 22, 152, 24), 2)
        pygame.draw.ellipse(ring, (*_NS_akiraze.PALETTE["lightning_dark"], 180),
                            (25, 24, 130, 20), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 34 + int(math.sin(angle) * 9)
            x2 = 90 + int(math.cos(angle) * 76)
            y2 = 34 + int(math.sin(angle) * 13)
            pygame.draw.line(ring, (*_NS_akiraze.PALETTE["lightning_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_akiraze.PALETTE["chakra_hot"],
                                       _NS_akiraze._alpha(150 * pulse)),
                                (15, 12, 150, 42), 1)
        surface.blit(ring, (x - 90, y - 30))
    # ============================================================
    # SKILL Q - GALESHOT (spiraling blue orb)
    # ============================================================
    def _draw_galeshot_skill(surface, boss, x, y, timer, phase):
        """Spinning blue chakra orb thrown."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_akiraze._target_position(boss, x, y)
        hand_x = x + facing * 24
        hand_y = y - 4
        if progress < 0.3:
            # Form orb in hand (spinning)
            t = progress / 0.3
            orb_r = int(4 + t * 10)
            _NS_akiraze._draw_chakra_orb(surface, hand_x, hand_y, orb_r, phase)
            return
        # Fly to target
        t = (progress - 0.3) / 0.7
        t = min(1.0, t)
        start_x = hand_x + facing * 6
        start_y = hand_y
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Trail behind (fading orbs)
        for i in range(6):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_akiraze._alpha(200 - i * 30)
            trail_r = max(3, 10 - i)
            for r in range(trail_r + 2, 0, -1):
                a = _NS_akiraze._alpha(alpha * (trail_r + 2 - r) / (trail_r + 2))
                _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["chakra_mid"], a),
                                      (px, py), r)
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["chakra_light"], alpha),
                                  (px, py), max(1, trail_r - 3))
        # Main spinning orb
        _NS_akiraze._draw_chakra_orb(surface, bx, by, 14, phase)
        # Impact
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(18 + st * 22)
            alpha = _NS_akiraze._alpha(240 * (1 - st))
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["chakra_dark"], alpha),
                                  (tx, ty), radius, 3)
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["chakra_mid"], alpha),
                                  (tx, ty), max(1, radius - 5), 2)
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["chakra_light"], alpha),
                                  (tx, ty), max(1, radius - 12), 1)
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["chakra_shine"], alpha),
                                  (tx, ty), 3)
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["white"], (tx, ty, 2, 2))
            # Radial burst
            for i in range(12):
                a_s = i * math.pi / 6
                ex = tx + int(math.cos(a_s) * radius)
                ey = ty + int(math.sin(a_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_akiraze.PALETTE["chakra_hot"], alpha),
                                 (ex, ey, 3, 3))
                pygame.draw.rect(surface, (*_NS_akiraze.PALETTE["white"], alpha),
                                 (ex, ey, 1, 1))
    def _draw_chakra_orb(surface, cx, cy, r, phase):
        """Spinning blue chakra orb."""
        # Outer glow
        for gr in range(r + 6, r, -1):
            alpha = _NS_akiraze._alpha(120 * (r + 6 - gr) / 6)
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["chakra_light"], alpha),
                                  (cx, cy), gr)
        # Body
        _NS_akiraze._aacircle(surface, _NS_akiraze.PALETTE["chakra_darkest"], (cx, cy), r)
        _NS_akiraze._aacircle(surface, _NS_akiraze.PALETTE["chakra_dark"], (cx, cy), r - 1)
        _NS_akiraze._aacircle(surface, _NS_akiraze.PALETTE["chakra_mid"], (cx, cy), r - 3)
        _NS_akiraze._aacircle(surface, _NS_akiraze.PALETTE["chakra_light"], (cx, cy), r - 5)
        # SPIRAL PATTERN (spinning)
        num_arms = 3
        for arm in range(num_arms):
            arm_offset = arm * math.pi * 2 / num_arms + phase * 4
            for i in range(r):
                t = i / r
                spiral_r = r * t
                angle = arm_offset + t * math.pi * 2
                px = cx + int(math.cos(angle) * spiral_r)
                py = cy + int(math.sin(angle) * spiral_r)
                alpha = _NS_akiraze._alpha(220 * (1 - t * 0.5))
                pygame.draw.rect(surface, (*_NS_akiraze.PALETTE["chakra_hot"], alpha), (px, py, 1, 1))
        # Bright center
        _NS_akiraze._aacircle(surface, _NS_akiraze.PALETTE["chakra_shine"], (cx, cy), max(1, r // 4))
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["white"], (cx, cy, 1, 1))
        # Ring around orb
        _NS_akiraze._aacircle(surface, _NS_akiraze.PALETTE["chakra_light"], (cx, cy), r, 1)
    # ============================================================
    # SKILL W - FLASH KUNAI
    # ============================================================
    def _draw_flashkunai_skill(surface, boss, x, y, timer, phase):
        """Kunai flying with lightning trail."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_akiraze._target_position(boss, x, y)
        hand_x = x + facing * 24
        hand_y = y - 4
        if progress < 0.15:
            # Prep kunai in hand
            _NS_akiraze._draw_kunai(surface, hand_x, hand_y, math.pi if facing < 0 else 0)
            return
        # Fly
        t = (progress - 0.15) / 0.85
        t = min(1.0, t)
        start_x = hand_x + facing * 6
        start_y = hand_y
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        angle = math.atan2(ty - start_y, tx - start_x)
        # Lightning trail (zigzag)
        _NS_akiraze._draw_lightning_trail(surface, (start_x, start_y), (bx, by), phase)
        # Golden trail sparkles
        for i in range(8):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_akiraze._alpha(220 - i * 25)
            size = max(1, 5 - i)
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["lightning_dark"], alpha),
                                  (px, py), size)
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["lightning_mid"], alpha),
                                  (px, py), max(1, size - 1))
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["lightning_light"], alpha),
                                  (px, py), max(1, size - 2))
            pygame.draw.rect(surface, (*_NS_akiraze.PALETTE["lightning_shine"], alpha),
                             (px, py, 1, 1))
        # Kunai at head
        _NS_akiraze._draw_kunai(surface, bx, by, angle)
        # Impact
        if t > 0.9:
            st = (t - 0.9) / 0.1
            radius = int(10 + st * 20)
            alpha = _NS_akiraze._alpha(240 * (1 - st))
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["lightning_mid"], alpha),
                                  (tx, ty), radius, 2)
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["lightning_light"], alpha),
                                  (tx, ty), max(1, radius - 5), 2)
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["lightning_shine"], alpha),
                                  (tx, ty), max(1, radius - 10), 1)
            # Radial lightning bolts
            for i in range(8):
                a_s = i * math.pi / 4
                ex = tx + int(math.cos(a_s) * radius)
                ey = ty + int(math.sin(a_s) * radius)
                pygame.draw.line(surface, (*_NS_akiraze.PALETTE["lightning_hot"], alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_akiraze.PALETTE["lightning_shine"], alpha),
                                 (ex, ey, 2, 2))
    def _draw_kunai(surface, cx, cy, angle):
        """Small kunai knife shape."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        # Blade
        tip_x = cx + int(cos_a * 8)
        tip_y = cy + int(sin_a * 8)
        tail_x = cx - int(cos_a * 4)
        tail_y = cy - int(sin_a * 4)
        perp = angle + math.pi / 2
        # Diamond blade shape
        p1 = (tip_x, tip_y)
        p2 = (cx + int(math.cos(perp) * 3), cy + int(math.sin(perp) * 3))
        p3 = (cx - int(cos_a * 2), cy - int(sin_a * 2))
        p4 = (cx - int(math.cos(perp) * 3), cy - int(math.sin(perp) * 3))
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in [p1, p2, p3, p4]])
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["metal_dark"], [p1, p2, p3, p4])
        _NS_akiraze._poly(surface, _NS_akiraze.PALETTE["metal_mid"], [
            p1,
            (int(p1[0] * 0.7 + p2[0] * 0.3), int(p1[1] * 0.7 + p2[1] * 0.3)),
            p3,
            (int(p1[0] * 0.7 + p4[0] * 0.3), int(p1[1] * 0.7 + p4[1] * 0.3)),
        ])
        pygame.draw.line(surface, _NS_akiraze.PALETTE["metal_light"], p3, p1, 1)
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["metal_shine"], (p1[0], p1[1], 1, 1))
        # Handle wrap (gold)
        pygame.draw.line(surface, _NS_akiraze.PALETTE["gold_dark"],
                         p3, (tail_x, tail_y), 3)
        pygame.draw.line(surface, _NS_akiraze.PALETTE["gold_mid"],
                         p3, (tail_x, tail_y), 2)
        pygame.draw.line(surface, _NS_akiraze.PALETTE["gold_light"],
                         p3, (tail_x, tail_y), 1)
        # Ring at end
        _NS_akiraze._aacircle(surface, _NS_akiraze.PALETTE["gold_dark"], (tail_x, tail_y), 2)
        _NS_akiraze._aacircle(surface, _NS_akiraze.PALETTE["gold_light"], (tail_x, tail_y), 1)
        # Tag hanging from ring (paper seal)
        tag_x = tail_x - int(cos_a * 2)
        tag_y = tail_y - int(sin_a * 2) + 2
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["robe_mid"], (tag_x - 1, tag_y, 2, 4))
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["robe_light"], (tag_x - 1, tag_y, 2, 1))
        pygame.draw.line(surface, _NS_akiraze.PALETTE["shadow_deep"],
                         (tag_x, tag_y + 1), (tag_x, tag_y + 3), 1)
    def _draw_lightning_trail(surface, p1, p2, phase):
        """Zigzag lightning between two points."""
        segments = 6
        prev = p1
        for i in range(1, segments + 1):
            t = i / segments
            base_x = int(p1[0] + (p2[0] - p1[0]) * t)
            base_y = int(p1[1] + (p2[1] - p1[1]) * t)
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            length = math.hypot(dx, dy) or 1
            perp_x = -dy / length
            perp_y = dx / length
            jitter = math.sin(phase * 30 + i * 3) * 4 if 0 < i < segments else 0
            next_pt = (base_x + int(perp_x * jitter), base_y + int(perp_y * jitter))
            pygame.draw.line(surface, _NS_akiraze.PALETTE["lightning_hot"], prev, next_pt, 3)
            pygame.draw.line(surface, _NS_akiraze.PALETTE["lightning_light"], prev, next_pt, 2)
            pygame.draw.line(surface, _NS_akiraze.PALETTE["lightning_shine"], prev, next_pt, 1)
            prev = next_pt
    # ============================================================
    # SKILL E - SEAL MARKER
    # ============================================================
    def _draw_seal_ground(surface, boss, x, y, timer, phase):
        """Ground seal circle at target."""
        tx, ty = _NS_akiraze._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(30 * min(1.0, progress * 2))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_akiraze.PALETTE["lightning_dark"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_akiraze.PALETTE["lightning_mid"], 220),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_akiraze.PALETTE["lightning_light"], 180),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8), 1)
            # Rune markings
            for i in range(8):
                a = phase * 0.5 + i * math.pi / 4
                x1 = tx + int(math.cos(a) * r * 0.7)
                y1 = ty + int(math.sin(a) * r * 0.7 * 0.4)
                x2 = tx + int(math.cos(a) * r)
                y2 = ty + int(math.sin(a) * r * 0.4)
                pygame.draw.line(surface, (*_NS_akiraze.PALETTE["lightning_hot"], 220),
                                 (x1, y1), (x2, y2), 1)
    def _draw_seal_foreground(surface, boss, x, y, timer, phase):
        """Paper seal tag hovering at target."""
        tx, ty = _NS_akiraze._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        scale = min(1.0, progress * 2)
        # Floating paper seal (rectangular)
        seal_w = int(10 * scale)
        seal_h = int(14 * scale)
        seal_y = ty - 20 + int(math.sin(phase * 2) * 3)
        if seal_w < 2:
            return
        # Paper background
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["shadow_deep"],
                         (tx - seal_w // 2 + 1, seal_y + 1, seal_w, seal_h))
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["robe_mid"],
                         (tx - seal_w // 2, seal_y, seal_w, seal_h))
        pygame.draw.rect(surface, _NS_akiraze.PALETTE["robe_light"],
                         (tx - seal_w // 2, seal_y, seal_w, 1))
        # Rune/kanji markings on paper
        for i in range(3):
            mark_y = seal_y + 3 + i * 4
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["hair_darkest"],
                             (tx - 2, mark_y, 4, 1))
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["hair_darkest"],
                             (tx - 1, mark_y + 1, 2, 1))
        # Golden glow around seal
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(int(15 * scale), 0, -2):
            alpha = _NS_akiraze._alpha(150 * (15 - r) / 15 * pulse)
            _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["lightning_mid"], alpha),
                                  (tx, seal_y + seal_h // 2), r)
        # Sparkles
        for i in range(6):
            a = phase * 2 + i * math.pi / 3
            sr = int(12 * scale) + int(math.sin(phase * 3 + i) * 3)
            sx = tx + int(math.cos(a) * sr)
            sy = seal_y + seal_h // 2 + int(math.sin(a) * sr * 0.7)
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["lightning_hot"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["lightning_shine"], (sx, sy, 1, 1))
    # ============================================================
    # SKILL R - PHANTOM STEP (teleport)
    # ============================================================
    def _draw_teleport_ground(surface, boss, x, y, timer, phase):
        """Multiple ground marks where boss teleported."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # 3 marks in front of boss showing teleport path
        for i in range(3):
            mx = x + facing * (30 + i * 40)
            my = y + 46
            fade = math.sin(phase * 3 + i) * 0.3 + 0.7
            r = int(15 * fade * min(1.0, progress * 2))
            if r > 2:
                pygame.draw.ellipse(surface, (*_NS_akiraze.PALETTE["lightning_dark"], 200),
                                    (mx - r, my - r // 3, r * 2, r * 2 // 3), 2)
                pygame.draw.ellipse(surface, (*_NS_akiraze.PALETTE["lightning_mid"], 180),
                                    (mx - r + 2, my - r // 3 + 1,
                                     r * 2 - 4, r * 2 // 3 - 2), 1)
    def _draw_teleport_foreground(surface, boss, x, y, timer, phase):
        """Yellow flash lines connecting positions + burst."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Path from boss through 3 marks
        positions = [(x, y)]
        for i in range(3):
            positions.append((x + facing * (30 + i * 40), y - 5))
        # Draw lightning lines connecting positions
        for i in range(len(positions) - 1):
            _NS_akiraze._draw_lightning_trail(surface, positions[i], positions[i + 1], phase)
        # Burst at each position
        for i, (px, py) in enumerate(positions[1:]):
            burst_phase = (phase + i * 0.5) % 2
            r = int(8 + math.sin(burst_phase * 4) * 4)
            for br in range(r + 3, 0, -1):
                alpha = _NS_akiraze._alpha(180 * (r + 3 - br) / (r + 3))
                _NS_akiraze._aacircle(surface, (*_NS_akiraze.PALETTE["lightning_mid"], alpha),
                                      (px, py), br)
            _NS_akiraze._aacircle(surface, _NS_akiraze.PALETTE["lightning_hot"], (px, py), 4)
            _NS_akiraze._aacircle(surface, _NS_akiraze.PALETTE["lightning_shine"], (px, py), 2)
            pygame.draw.rect(surface, _NS_akiraze.PALETTE["white"], (px, py, 1, 1))
            # Radial burst
            for j in range(8):
                a = j * math.pi / 4
                ex = px + int(math.cos(a) * r)
                ey = py + int(math.sin(a) * r)
                pygame.draw.line(surface, _NS_akiraze.PALETTE["lightning_light"],
                                 (px, py), (ex, ey), 1)
                pygame.draw.rect(surface, _NS_akiraze.PALETTE["lightning_shine"], (ex, ey, 1, 1))



# ====================================================================
# BRUMHAR (GLACIER REAVER) - Mini Boss
# ====================================================================

class _NS_brumhar:
    """Namespace brumhar - Glacier Reaver boss (Frost warrior)."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # White fur (main body/beard)
        "fur_darkest": (95, 100, 115),
        "fur_dark": (145, 155, 175),
        "fur_mid": (200, 210, 225),
        "fur_light": (235, 240, 250),
        "fur_shine": (255, 255, 255),
        # Skin (pale bear-ish snout)
        "skin_dark": (110, 90, 80),
        "skin_mid": (180, 155, 140),
        "skin_light": (230, 210, 195),
        # Jacket (brown leather)
        "jacket_darkest": (25, 15, 8),
        "jacket_dark": (55, 30, 15),
        "jacket_mid": (110, 65, 35),
        "jacket_light": (170, 115, 70),
        # Hat (red winter/santa)
        "hat_darkest": (55, 10, 15),
        "hat_dark": (110, 25, 30),
        "hat_mid": (175, 50, 55),
        "hat_light": (225, 100, 100),
        # Ice blue (skills + orb)
        "ice_darkest": (10, 30, 55),
        "ice_dark": (40, 85, 140),
        "ice_mid": (95, 165, 225),
        "ice_light": (170, 220, 255),
        "ice_hot": (220, 245, 255),
        "ice_shine": (250, 253, 255),
        # Metal (hook, buckle)
        "metal_darkest": (25, 30, 40),
        "metal_dark": (65, 75, 90),
        "metal_mid": (130, 140, 155),
        "metal_light": (200, 210, 225),
        "metal_shine": (245, 250, 255),
        # Gold accents (buckle, rings)
        "gold_dark": (95, 65, 15),
        "gold_mid": (185, 145, 45),
        "gold_light": (245, 215, 115),
        # Eye (deep black bear eye + shine)
        "eye_dark": (8, 5, 5),
        "eye_mid": (30, 20, 15),
        "eye_shine": (245, 235, 220),
        # Nose (black)
        "nose_dark": (10, 8, 12),
        "nose_light": (60, 50, 55),
        # Snow ground
        "snow_dark": (140, 155, 180),
        "snow_mid": (200, 215, 235),
        "snow_light": (245, 250, 255),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_brumhar._clamp(color)
        if _NS_brumhar.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_brumhar._clamp(color)
        if _NS_brumhar.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_brumhar._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 150 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_brumhar(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_brumhar._detect_moving(boss)
        _NS_brumhar._update_attack_anim(boss)
        attacking = getattr(boss, "_bh_attack_active", False)
        # Ambient
        _NS_brumhar._draw_frost_aura(surface, x, y, pulse)
        _NS_brumhar._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX
        if active_skill == "e":
            _NS_brumhar._draw_rimepillars_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_brumhar._draw_titancharge_ground(surface, boss, x, y, skill_timer, pulse)
        # Body
        if attacking:
            _NS_brumhar._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_brumhar._draw_walk(surface, boss, x, y)
        else:
            _NS_brumhar._draw_idle(surface, boss, x, y)
        # Foreground FX
        if active_skill == "q":
            _NS_brumhar._draw_frostshards_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_brumhar._draw_glacierball_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_brumhar._draw_rimepillars_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_brumhar._draw_titancharge_foreground(surface, boss, x, y, skill_timer, pulse)
        # Snowfall ambient
        _NS_brumhar._draw_snowfall(surface, x, y, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_bh_attack_active", False))
        if not active and timer <= 2:
            boss._bh_attack_active = True
            boss._bh_attack_frame = 0
            active = True
        if active:
            boss._bh_attack_frame = int(getattr(boss, "_bh_attack_frame", 0)) + 1
            if boss._bh_attack_frame >= cooldown:
                boss._bh_attack_active = False
                boss._bh_attack_frame = 0
                active = False
        boss._bh_attack_progress = (
            min(1.0, getattr(boss, "_bh_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_bh_last_x"):
            boss._bh_last_x = boss.x
            boss._bh_last_y = boss.y
            return False
        dx = abs(boss.x - boss._bh_last_x)
        dy = abs(boss.y - boss._bh_last_y)
        boss._bh_last_x = boss.x
        boss._bh_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 3)  # subtle stationary bob
        _NS_brumhar._draw_shadow(surface, x, y + 48)
        _NS_brumhar._draw_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")
    def _draw_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        # Heavy footstep bob (up-down alternation)
        hop = int(abs(math.sin(phase * 1.2)) * 4)
        sway = int(math.sin(phase * 0.6) * 2)
        _NS_brumhar._draw_shadow(surface, x + sway, y + 48)
        _NS_brumhar._draw_body(surface, x + sway, y - hop, boss.direction, phase, "walk")
    def _draw_attack(surface, boss, x, y):
        progress = getattr(boss, "_bh_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        # Wind up → swing hook → recovery
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 4) * boss.direction
            lift = 0
        elif progress < 0.6:
            t = (progress - 0.3) / 0.3
            lunge = int((-4 + t * 12)) * boss.direction
            lift = int(t * 2)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(8 * (1 - t)) * boss.direction
            lift = int(2 * (1 - t))
        _NS_brumhar._draw_shadow(surface, x + lunge, y + 48)
        _NS_brumhar._draw_body(surface, x + lunge, y - lift, boss.direction, boss.pulse,
                               "attack", progress)
        _NS_brumhar._draw_hook_swing(surface, boss, x + lunge, y - lift, progress)
    # ============================================================
    # BODY - Frost warrior with jacket + hat + hook + orb
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0.0):
        # Legs
        _NS_brumhar._draw_legs(surface, cx, cy, facing, phase, action)
        # Torso jacket
        _NS_brumhar._draw_torso_jacket(surface, cx, cy, facing, phase)
        # Back arm (holds orb)
        _NS_brumhar._draw_orb_arm(surface, cx, cy, facing, phase, action, attack_progress)
        # Head + hat + beard
        _NS_brumhar._draw_head(surface, cx, cy - 20, facing, phase)
        # Beard hangs down
        _NS_brumhar._draw_beard(surface, cx, cy - 10, facing, phase)
        # Front arm (holds hook)
        _NS_brumhar._draw_hook_arm(surface, cx, cy, facing, phase, action, attack_progress)
    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Short chubby legs with boots."""
        step_offset = 0
        if action == "walk":
            step_offset = math.sin(phase * 1.5) * 2
        for i, (leg_x, leg_offset) in enumerate([(-5, step_offset), (5, -step_offset)]):
            leg_top_y = cy + 12
            leg_bot_y = cy + 22 + int(leg_offset)
            # Leg (jacket brown)
            _NS_brumhar._aaline(surface, _NS_brumhar.PALETTE["shadow_deep"],
                    (cx + leg_x + 1, leg_top_y + 1),
                    (cx + leg_x + 1, leg_bot_y + 1), 6)
            _NS_brumhar._aaline(surface, _NS_brumhar.PALETTE["jacket_darkest"],
                    (cx + leg_x, leg_top_y), (cx + leg_x, leg_bot_y), 5)
            _NS_brumhar._aaline(surface, _NS_brumhar.PALETTE["jacket_dark"],
                    (cx + leg_x, leg_top_y), (cx + leg_x, leg_bot_y), 3)
            _NS_brumhar._aaline(surface, _NS_brumhar.PALETTE["jacket_mid"],
                    (cx + leg_x - 1, leg_top_y), (cx + leg_x - 1, leg_bot_y), 1)
            # Boot (dark metal-toed)
            boot_y = leg_bot_y
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["shadow_deep"],
                             (cx + leg_x - 4, boot_y + 1, 10, 5))
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["jacket_darkest"],
                             (cx + leg_x - 4, boot_y, 10, 4))
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["jacket_dark"],
                             (cx + leg_x - 3, boot_y, 8, 3))
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["jacket_mid"],
                             (cx + leg_x - 3, boot_y, 8, 1))
            # Metal toe cap
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["metal_dark"],
                             (cx + leg_x + 3, boot_y + 1, 3, 3))
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["metal_light"],
                             (cx + leg_x + 3, boot_y + 1, 3, 1))
    def _draw_torso_jacket(surface, cx, cy, facing, phase):
        """Brown leather jacket with fur trim."""
        # Body shape (broad barrel chest)
        torso_shape = [
            (cx - 14, cy - 8),
            (cx - 16, cy - 3),
            (cx - 15, cy + 4),
            (cx - 12, cy + 12),
            (cx - 8, cy + 15),
            (cx + 8, cy + 15),
            (cx + 12, cy + 12),
            (cx + 15, cy + 4),
            (cx + 16, cy - 3),
            (cx + 14, cy - 8),
            (cx + 7, cy - 12),
            (cx - 7, cy - 12),
        ]
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["shadow_deep"],
              [(px + 2, py + 3) for px, py in torso_shape])
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["jacket_darkest"], torso_shape)
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["jacket_dark"], [
            (cx - 13, cy - 7), (cx - 15, cy - 2),
            (cx - 14, cy + 4), (cx - 11, cy + 11),
            (cx - 7, cy + 14), (cx + 7, cy + 14),
            (cx + 11, cy + 11), (cx + 14, cy + 4),
            (cx + 15, cy - 2), (cx + 13, cy - 7),
            (cx + 6, cy - 11), (cx - 6, cy - 11),
        ])
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["jacket_mid"], [
            (cx - 11, cy - 5), (cx - 13, cy),
            (cx - 12, cy + 3), (cx - 9, cy + 10),
            (cx + 9, cy + 10), (cx + 12, cy + 3),
            (cx + 13, cy), (cx + 11, cy - 5),
            (cx + 4, cy - 9), (cx - 4, cy - 9),
        ])
        # Highlights on chest
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["jacket_light"], [
            (cx - 8, cy - 6), (cx - 4, cy - 8),
            (cx - 3, cy - 4), (cx - 7, cy - 2),
        ])
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["jacket_light"], [
            (cx + 4, cy - 8), (cx + 8, cy - 6),
            (cx + 7, cy - 2), (cx + 3, cy - 4),
        ])
        # Fur trim at top (shoulders/collar - white fluffy)
        for side in (-1, 1):
            for i in range(4):
                fx = cx + side * (10 - i * 3)
                fy = cy - 10 - int(math.sin(phase + i) * 1)
                _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["shadow_deep"],
                                      (fx + 1, fy + 1), 3)
                _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["fur_darkest"], (fx, fy), 3)
                _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["fur_dark"], (fx, fy), 2)
                _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["fur_mid"], (fx - 1, fy - 1), 2)
                _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["fur_light"], (fx - 1, fy - 1), 1)
                pygame.draw.rect(surface, _NS_brumhar.PALETTE["fur_shine"], (fx - 1, fy - 1, 1, 1))
        # Center front fur trim (thick)
        for i in range(5):
            fx = cx - 6 + i * 3
            fy = cy - 10
            _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["fur_dark"], (fx, fy), 3)
            _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["fur_mid"], (fx, fy), 2)
            _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["fur_light"], (fx - 1, fy - 1), 1)
        # Center jacket opening (V-line down chest)
        pygame.draw.line(surface, _NS_brumhar.PALETTE["jacket_darkest"],
                         (cx, cy - 8), (cx, cy + 12), 2)
        # Belt at waist
        pygame.draw.rect(surface, _NS_brumhar.PALETTE["jacket_darkest"],
                         (cx - 14, cy + 10, 28, 4))
        pygame.draw.rect(surface, _NS_brumhar.PALETTE["shadow_deep"],
                         (cx - 14, cy + 13, 28, 1))
        # Belt highlight
        pygame.draw.line(surface, _NS_brumhar.PALETTE["jacket_mid"],
                         (cx - 14, cy + 10), (cx + 14, cy + 10), 1)
        # Gold buckle
        pygame.draw.rect(surface, _NS_brumhar.PALETTE["gold_dark"],
                         (cx - 3, cy + 9, 6, 6))
        pygame.draw.rect(surface, _NS_brumhar.PALETTE["gold_mid"],
                         (cx - 2, cy + 10, 4, 4))
        pygame.draw.rect(surface, _NS_brumhar.PALETTE["gold_light"],
                         (cx - 2, cy + 10, 4, 1))
    def _draw_head(surface, cx, cy, facing, phase):
        """Bear/walrus face with white fur + winter hat."""
        # Head shape (round, big)
        head_shape = [
            (cx - 10, cy + 8),
            (cx - 12, cy + 2),
            (cx - 11, cy - 4),
            (cx - 7, cy - 8),
            (cx + 7, cy - 8),
            (cx + 11, cy - 4),
            (cx + 12, cy + 2),
            (cx + 10, cy + 8),
            (cx + 5, cy + 11),
            (cx - 5, cy + 11),
        ]
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in head_shape])
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["fur_darkest"], head_shape)
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["fur_dark"], [
            (cx - 9, cy + 7), (cx - 11, cy + 2),
            (cx - 10, cy - 3), (cx - 6, cy - 7),
            (cx + 6, cy - 7), (cx + 10, cy - 3),
            (cx + 11, cy + 2), (cx + 9, cy + 7),
            (cx + 4, cy + 10), (cx - 4, cy + 10),
        ])
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["fur_mid"], [
            (cx - 7, cy + 5), (cx - 9, cy),
            (cx - 8, cy - 4), (cx - 4, cy - 6),
            (cx + 4, cy - 6), (cx + 8, cy - 4),
            (cx + 9, cy), (cx + 7, cy + 5),
        ])
        # Fluffy fur tufts around head
        for i, (fx, fy) in enumerate([
            (-11, -2), (-10, 4), (-8, 8),
            (11, -2), (10, 4), (8, 8),
            (-6, -7), (6, -7),
        ]):
            wave = math.sin(phase + i * 0.3) * 1
            _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["fur_dark"],
                                  (cx + fx, cy + fy + int(wave)), 2)
            _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["fur_mid"],
                                  (cx + fx, cy + fy + int(wave)), 1)
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["fur_light"],
                             (cx + fx - 1, cy + fy + int(wave) - 1, 1, 1))
        # SNOUT (protruding nose area, tan)
        snout_shape = [
            (cx - 4, cy + 2),
            (cx - 5, cy + 5),
            (cx - 3, cy + 9),
            (cx + 3, cy + 9),
            (cx + 5, cy + 5),
            (cx + 4, cy + 2),
        ]
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["fur_darkest"],
                          [(p[0], p[1] + 1) for p in snout_shape])
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["fur_dark"], snout_shape)
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["fur_mid"], [
            (cx - 3, cy + 3), (cx - 4, cy + 5),
            (cx - 2, cy + 8), (cx + 2, cy + 8),
            (cx + 4, cy + 5), (cx + 3, cy + 3),
        ])
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["fur_light"], [
            (cx - 2, cy + 4), (cx - 3, cy + 5),
            (cx - 1, cy + 7), (cx + 1, cy + 7),
            (cx + 3, cy + 5), (cx + 2, cy + 4),
        ])
        # NOSE (black button)
        pygame.draw.rect(surface, _NS_brumhar.PALETTE["shadow_deep"],
                         (cx - 2, cy + 3, 4, 3))
        pygame.draw.rect(surface, _NS_brumhar.PALETTE["nose_dark"],
                         (cx - 1, cy + 3, 3, 2))
        pygame.draw.rect(surface, _NS_brumhar.PALETTE["nose_light"],
                         (cx, cy + 3, 1, 1))
        # EYES (small black beady with shine)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_x in (cx - 4, cx + 4):
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["fur_darkest"],
                             (eye_x - 2, cy - 3, 4, 3))
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["eye_dark"],
                             (eye_x - 1, cy - 3, 3, 3))
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["eye_mid"],
                             (eye_x - 1, cy - 1, 3, 1))
            # Bright eye shine
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["eye_shine"],
                             (eye_x, cy - 3, 1, 1))
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["white"],
                             (eye_x, cy - 3, 1, 1))
        # HAT (red winter/santa hat)
        _NS_brumhar._draw_winter_hat(surface, cx, cy - 8, facing, phase)
    def _draw_winter_hat(surface, cx, cy, facing, phase):
        """Red winter hat with white fluff trim."""
        sway = math.sin(phase * 0.4) * 1
        # White fluffy brim at bottom
        for i in range(5):
            fx = cx - 8 + i * 4
            fy = cy + 2
            _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["shadow_deep"],
                                  (fx + 1, fy + 1), 3)
            _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["fur_dark"], (fx, fy), 3)
            _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["fur_mid"], (fx, fy), 2)
            _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["fur_light"], (fx - 1, fy - 1), 1)
        # Hat cone (red)
        hat_shape = [
            (cx - 8, cy),
            (cx - 6, cy - 6),
            (cx - 2 + int(sway), cy - 12),
            (cx + 3 + int(sway), cy - 14),
            (cx + 6, cy - 6),
            (cx + 8, cy),
        ]
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["shadow_deep"],
              [(p[0] + 1, p[1] + 1) for p in hat_shape])
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["hat_darkest"], hat_shape)
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["hat_dark"], [
            (cx - 7, cy - 1), (cx - 5, cy - 5),
            (cx - 1 + int(sway * 0.7), cy - 11),
            (cx + 2 + int(sway * 0.7), cy - 13),
            (cx + 5, cy - 5), (cx + 7, cy - 1),
        ])
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["hat_mid"], [
            (cx - 5, cy - 2), (cx - 4, cy - 5),
            (cx + int(sway * 0.5), cy - 10),
            (cx + 2 + int(sway * 0.5), cy - 12),
            (cx + 4, cy - 5), (cx + 5, cy - 2),
        ])
        # Highlight streak
        pygame.draw.line(surface, _NS_brumhar.PALETTE["hat_light"],
                         (cx - 3, cy - 3),
                         (cx + int(sway * 0.5), cy - 10), 1)
        # White fluffy ball at tip
        tip_x = cx + 3 + int(sway)
        tip_y = cy - 14
        _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["shadow_deep"], (tip_x + 1, tip_y + 1), 3)
        _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["fur_darkest"], (tip_x, tip_y), 3)
        _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["fur_dark"], (tip_x, tip_y), 2)
        _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["fur_mid"], (tip_x - 1, tip_y - 1), 2)
        _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["fur_light"], (tip_x - 1, tip_y - 1), 1)
        pygame.draw.rect(surface, _NS_brumhar.PALETTE["fur_shine"], (tip_x - 1, tip_y - 1, 1, 1))
    def _draw_beard(surface, cx, cy, facing, phase):
        """Massive white fluffy beard covering chest."""
        sway = math.sin(phase * 0.4) * 1
        # Big beard shape (wide at bottom)
        beard_shape = [
            (cx - 10, cy),
            (cx - 12, cy + 4),
            (cx - 11 + int(sway), cy + 10),
            (cx - 8 + int(sway), cy + 16),
            (cx - 3 + int(sway), cy + 20),
            (cx + 3 + int(sway * 0.5), cy + 20),
            (cx + 8 + int(sway * 0.5), cy + 16),
            (cx + 11, cy + 10),
            (cx + 12, cy + 4),
            (cx + 10, cy),
        ]
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["shadow_deep"],
              [(p[0] + 1, p[1] + 2) for p in beard_shape])
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["fur_darkest"], beard_shape)
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["fur_dark"], [
            (cx - 9, cy + 1), (cx - 11, cy + 4),
            (cx - 10 + int(sway * 0.7), cy + 9),
            (cx - 7 + int(sway * 0.7), cy + 15),
            (cx - 2 + int(sway * 0.5), cy + 19),
            (cx + 2 + int(sway * 0.3), cy + 19),
            (cx + 7 + int(sway * 0.3), cy + 15),
            (cx + 10, cy + 9), (cx + 11, cy + 4), (cx + 9, cy + 1),
        ])
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["fur_mid"], [
            (cx - 7, cy + 3), (cx - 9, cy + 6),
            (cx - 7 + int(sway * 0.5), cy + 12),
            (cx - 3 + int(sway * 0.5), cy + 17),
            (cx + 3 + int(sway * 0.3), cy + 17),
            (cx + 7 + int(sway * 0.3), cy + 12),
            (cx + 9, cy + 6), (cx + 7, cy + 3),
        ])
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["fur_light"], [
            (cx - 4, cy + 5), (cx - 6, cy + 10),
            (cx - 2 + int(sway * 0.3), cy + 15),
            (cx + 2 + int(sway * 0.2), cy + 15),
            (cx + 6, cy + 10), (cx + 4, cy + 5),
        ])
        # Bright hair strokes vertical
        for i in range(5):
            hx = cx - 4 + i * 2 + int(sway * 0.3)
            hy1 = cy + 3
            hy2 = cy + 17 + i
            pygame.draw.line(surface, _NS_brumhar.PALETTE["fur_shine"],
                             (hx, hy1), (hx, hy2), 1)
        # Fluffy tufts on beard edges
        for i, (fx, fy) in enumerate([
            (-10, 5), (-11, 10), (-8, 15),
            (10, 5), (11, 10), (8, 15),
            (-4, 19), (4, 19),
        ]):
            wave = math.sin(phase * 0.6 + i) * 1
            _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["fur_dark"],
                                  (cx + fx, cy + fy + int(wave)), 2)
            _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["fur_light"],
                                  (cx + fx, cy + fy + int(wave)), 1)
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["fur_shine"],
                             (cx + fx, cy + fy + int(wave), 1, 1))
    def _draw_hook_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Arm holding the hook."""
        arm_sway = math.sin(phase * 0.5) * 1
        shoulder_x = cx + facing * 10
        shoulder_y = cy - 4
        if action == "attack":
            # Wind up back → swing forward
            if attack_progress < 0.3:
                t = attack_progress / 0.3
                arm_angle = math.pi * 0.3 + t * 0.4  # up back
                arm_len = 10
            elif attack_progress < 0.6:
                t = (attack_progress - 0.3) / 0.3
                # Swing down and forward
                arm_angle = math.pi * 0.7 - t * math.pi * 0.9
                arm_len = 10 + int(t * 6)
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_angle = -math.pi * 0.2 + t * math.pi * 0.2
                arm_len = 16 - int(t * 6)
        else:
            arm_angle = -math.pi * 0.15 + arm_sway * 0.05
            arm_len = 12
        hand_x = shoulder_x + int(math.cos(arm_angle) * arm_len) * facing
        hand_y = shoulder_y - int(math.sin(arm_angle) * arm_len)
        # Elbow midpoint
        elbow_x = (shoulder_x + hand_x) // 2
        elbow_y = (shoulder_y + hand_y) // 2 + 1
        # Draw arm (brown jacket)
        _NS_brumhar._draw_arm_segment(surface, (shoulder_x, shoulder_y),
                                       (elbow_x, elbow_y), 6, 1.0)
        _NS_brumhar._draw_arm_segment(surface, (elbow_x, elbow_y),
                                       (hand_x, hand_y), 5, 1.0)
        # Hand/glove
        _NS_brumhar._draw_glove(surface, hand_x, hand_y, 1.0)
        # HOOK
        _NS_brumhar._draw_hook(surface, hand_x, hand_y, facing, phase, arm_angle,
                                action, attack_progress)
    def _draw_orb_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm holding the ice orb."""
        arm_sway = math.sin(phase * 0.5) * 1
        back = -facing
        shoulder_x = cx + back * 10
        shoulder_y = cy - 4
        # Orb hangs at side
        elbow_x = shoulder_x + back * 3
        elbow_y = shoulder_y + 6 + int(arm_sway)
        hand_x = elbow_x + back * 2
        hand_y = elbow_y + 8
        # Arm
        _NS_brumhar._draw_arm_segment(surface, (shoulder_x, shoulder_y),
                                       (elbow_x, elbow_y), 6, 0.8)
        _NS_brumhar._draw_arm_segment(surface, (elbow_x, elbow_y),
                                       (hand_x, hand_y), 5, 0.8)
        # Glove
        _NS_brumhar._draw_glove(surface, hand_x, hand_y, 0.8)
        # ICE ORB
        _NS_brumhar._draw_ice_orb(surface, hand_x + back * 2, hand_y + 4,
                                   facing, phase, 0.8)
    def _draw_arm_segment(surface, p1, p2, thickness, depth_shade=1.0):
        """Brown jacket arm."""
        def shade(color):
            return tuple(int(c * depth_shade) for c in color)
        _NS_brumhar._aaline(surface, _NS_brumhar.PALETTE["shadow_deep"],
                (p1[0] + 2, p1[1] + 2), (p2[0] + 2, p2[1] + 2), thickness + 1)
        _NS_brumhar._aaline(surface, shade(_NS_brumhar.PALETTE["jacket_darkest"]),
                p1, p2, thickness)
        _NS_brumhar._aaline(surface, shade(_NS_brumhar.PALETTE["jacket_dark"]),
                p1, p2, max(1, thickness - 2))
        _NS_brumhar._aaline(surface, shade(_NS_brumhar.PALETTE["jacket_mid"]),
                (p1[0] - 1, p1[1] - 1), (p2[0] - 1, p2[1] - 1),
                max(1, thickness - 4))
    def _draw_glove(surface, cx, cy, depth_shade=1.0):
        """Fur-trimmed glove."""
        def shade(color):
            return tuple(int(c * depth_shade) for c in color)
        # Fur cuff (white)
        _NS_brumhar._aacircle(surface, shade(_NS_brumhar.PALETTE["fur_dark"]),
                              (cx, cy - 2), 3)
        _NS_brumhar._aacircle(surface, shade(_NS_brumhar.PALETTE["fur_mid"]),
                              (cx, cy - 2), 2)
        _NS_brumhar._aacircle(surface, shade(_NS_brumhar.PALETTE["fur_light"]),
                              (cx - 1, cy - 3), 1)
        # Glove (dark)
        pygame.draw.rect(surface, shade(_NS_brumhar.PALETTE["jacket_darkest"]),
                         (cx - 3, cy - 1, 6, 5))
        pygame.draw.rect(surface, shade(_NS_brumhar.PALETTE["jacket_dark"]),
                         (cx - 2, cy - 1, 4, 4))
        pygame.draw.rect(surface, shade(_NS_brumhar.PALETTE["jacket_mid"]),
                         (cx - 2, cy - 1, 4, 1))
    def _draw_hook(surface, hand_x, hand_y, facing, phase, arm_angle,
                    action, attack_progress):
        """Curved metal hook weapon."""
        # Hook extends from hand
        # Handle
        handle_len = 8
        handle_angle = arm_angle
        handle_tip_x = hand_x + int(math.cos(handle_angle) * handle_len) * facing
        handle_tip_y = hand_y - int(math.sin(handle_angle) * handle_len)
        # Handle (dark metal)
        pygame.draw.line(surface, _NS_brumhar.PALETTE["shadow_deep"],
                         (hand_x + 1, hand_y + 1),
                         (handle_tip_x + 1, handle_tip_y + 1), 4)
        pygame.draw.line(surface, _NS_brumhar.PALETTE["metal_darkest"],
                         (hand_x, hand_y), (handle_tip_x, handle_tip_y), 3)
        pygame.draw.line(surface, _NS_brumhar.PALETTE["metal_dark"],
                         (hand_x, hand_y), (handle_tip_x, handle_tip_y), 2)
        pygame.draw.line(surface, _NS_brumhar.PALETTE["metal_light"],
                         (hand_x, hand_y - 1), (handle_tip_x, handle_tip_y - 1), 1)
        # HOOK curves outward (perpendicular to handle)
        hook_perp = handle_angle + math.pi / 2
        # Curved hook path (semicircle)
        num_segs = 8
        hook_r = 10
        prev = (handle_tip_x, handle_tip_y)
        for i in range(1, num_segs + 1):
            t = i / num_segs
            # Curve from handle tip outward and back
            arc_angle = hook_perp - t * math.pi * 1.2
            cx_off = int(math.cos(arc_angle) * hook_r) * facing
            cy_off = -int(math.sin(arc_angle) * hook_r)
            nx = handle_tip_x + cx_off
            ny = handle_tip_y + cy_off
            # Draw hook segment
            pygame.draw.line(surface, _NS_brumhar.PALETTE["shadow_deep"],
                             (prev[0] + 1, prev[1] + 1),
                             (nx + 1, ny + 1), 4)
            pygame.draw.line(surface, _NS_brumhar.PALETTE["metal_darkest"],
                             prev, (nx, ny), 3)
            pygame.draw.line(surface, _NS_brumhar.PALETTE["metal_dark"],
                             prev, (nx, ny), 2)
            pygame.draw.line(surface, _NS_brumhar.PALETTE["metal_mid"],
                             (prev[0] - 1, prev[1] - 1), (nx - 1, ny - 1), 1)
            prev = (nx, ny)
        # Sharp bright tip highlight
        pygame.draw.rect(surface, _NS_brumhar.PALETTE["metal_shine"], (prev[0], prev[1], 2, 2))
        pygame.draw.rect(surface, _NS_brumhar.PALETTE["white"], (prev[0], prev[1], 1, 1))
    def _draw_ice_orb(surface, cx, cy, facing, phase, depth_shade=1.0):
        """Glowing ice orb with rune."""
        def shade(color):
            return tuple(int(c * depth_shade) for c in color)
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        # Glow halo
        for r in range(9, 0, -1):
            alpha = _NS_brumhar._alpha(100 * (9 - r) / 9 * pulse * depth_shade)
            _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["ice_mid"], alpha),
                                  (cx, cy), r)
        # Orb body
        _NS_brumhar._aacircle(surface, shade(_NS_brumhar.PALETTE["shadow_deep"]),
                              (cx + 1, cy + 1), 6)
        _NS_brumhar._aacircle(surface, shade(_NS_brumhar.PALETTE["ice_darkest"]),
                              (cx, cy), 6)
        _NS_brumhar._aacircle(surface, shade(_NS_brumhar.PALETTE["ice_dark"]),
                              (cx, cy), 5)
        _NS_brumhar._aacircle(surface, shade(_NS_brumhar.PALETTE["ice_mid"]),
                              (cx, cy), 4)
        _NS_brumhar._aacircle(surface, shade(_NS_brumhar.PALETTE["ice_light"]),
                              (cx - 1, cy - 1), 2)
        pygame.draw.rect(surface, shade(_NS_brumhar.PALETTE["ice_shine"]),
                         (cx - 1, cy - 2, 1, 1))
        # Rune symbol on orb (snowflake)
        pygame.draw.line(surface, shade(_NS_brumhar.PALETTE["ice_light"]),
                         (cx - 2, cy), (cx + 2, cy), 1)
        pygame.draw.line(surface, shade(_NS_brumhar.PALETTE["ice_light"]),
                         (cx, cy - 2), (cx, cy + 2), 1)
        pygame.draw.line(surface, shade(_NS_brumhar.PALETTE["ice_hot"]),
                         (cx - 1, cy - 1), (cx + 1, cy + 1), 1)
        pygame.draw.line(surface, shade(_NS_brumhar.PALETTE["ice_hot"]),
                         (cx - 1, cy + 1), (cx + 1, cy - 1), 1)
    def _draw_hook_swing(surface, boss, x, y, progress):
        """Frost arc trail during hook swing."""
        if progress < 0.3 or progress > 0.7:
            return
        facing = boss.direction
        t = (progress - 0.3) / 0.4
        cx = x + facing * 10
        cy = y - 4
        start_angle = math.pi * 0.6
        end_angle = -math.pi * 0.4
        current_angle = start_angle + (end_angle - start_angle) * t
        radius = 28
        # Trail arc
        num_segs = 10
        for seg in range(num_segs):
            seg_t = seg / num_segs
            seg_angle = start_angle + (current_angle - start_angle) * seg_t
            seg_alpha = _NS_brumhar._alpha(220 * (1 - seg_t) * (1 - abs(t - 0.5) * 0.3))
            r = int(radius - seg * 0.5)
            sx = cx + int(math.cos(seg_angle) * r) * facing
            sy = cy - int(math.sin(seg_angle) * r)
            size = int(6 - seg * 0.3)
            _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["ice_dark"], seg_alpha),
                                  (sx, sy), size)
            _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["ice_mid"], seg_alpha),
                                  (sx, sy), max(1, size - 2))
            _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["ice_light"], seg_alpha),
                                  (sx, sy), max(1, size - 4))
        # Bright leading edge
        lead_x = cx + int(math.cos(current_angle) * radius) * facing
        lead_y = cy - int(math.sin(current_angle) * radius)
        for r in range(9, 0, -1):
            alpha = _NS_brumhar._alpha(140 * (9 - r) / 9)
            _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["ice_light"], alpha),
                                  (lead_x, lead_y), r)
        _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["ice_hot"], (lead_x, lead_y), 3)
        _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["ice_shine"], (lead_x, lead_y), 2)
        pygame.draw.rect(surface, _NS_brumhar.PALETTE["white"], (lead_x, lead_y, 1, 1))
        # Frost sparkles
        for i in range(8):
            spark_angle = start_angle + (current_angle - start_angle) * (i / 8)
            spark_r = radius + int(math.sin(progress * 10 + i) * 4)
            spx = cx + int(math.cos(spark_angle) * spark_r) * facing
            spy = cy - int(math.sin(spark_angle) * spark_r)
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["ice_shine"], (spx, spy, 1, 1))
            # Small snowflake
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["ice_hot"], (spx - 1, spy, 1, 1))
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["ice_hot"], (spx + 1, spy, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius, 120 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (10, 20, 40, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (40, 80, 130, 100), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_frost_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.4) * 0.2 + 0.8
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_brumhar._alpha((90 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_brumhar._aacircle(aura, (*_NS_brumhar.PALETTE["ice_darkest"], alpha),
                                      (110, 100), radius)
        for radius in range(55, 5, -3):
            alpha = _NS_brumhar._alpha((55 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_brumhar._aacircle(aura, (*_NS_brumhar.PALETTE["ice_dark"], alpha),
                                      (110, 100), radius)
        for radius in range(30, 5, -2):
            alpha = _NS_brumhar._alpha((30 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_brumhar._aacircle(aura, (*_NS_brumhar.PALETTE["ice_mid"], alpha),
                                      (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))
        # Frost sparkles
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 42 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["ice_light"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["ice_shine"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_brumhar.PALETTE["ice_darkest"], 200),
                            (5, 20, 170, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_brumhar.PALETTE["ice_dark"], 220),
                            (14, 22, 152, 24), 2)
        pygame.draw.ellipse(ring, (*_NS_brumhar.PALETTE["ice_mid"], 180),
                            (25, 24, 130, 20), 1)
        # Snowflake runes
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 34 + int(math.sin(angle) * 9)
            x2 = 90 + int(math.cos(angle) * 76)
            y2 = 34 + int(math.sin(angle) * 13)
            pygame.draw.line(ring, (*_NS_brumhar.PALETTE["ice_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_brumhar.PALETTE["ice_hot"],
                                       _NS_brumhar._alpha(150 * pulse)),
                                (15, 12, 150, 42), 1)
        surface.blit(ring, (x - 90, y - 30))
    def _draw_snowfall(surface, x, y, phase):
        """Ambient snowflakes falling."""
        for i in range(20):
            fall_t = ((phase * 0.5 + i * 0.05) % 1.0)
            sx = x - 100 + (i * 137) % 200
            sy = y - 80 + int(fall_t * 160)
            drift = int(math.sin(phase + i) * 4)
            twinkle = math.sin(phase * 3 + i) * 0.5 + 0.5
            if twinkle > 0.3:
                pygame.draw.rect(surface, _NS_brumhar.PALETTE["snow_light"],
                                 (sx + drift, sy, 1, 1))
                if twinkle > 0.7:
                    pygame.draw.rect(surface, _NS_brumhar.PALETTE["white"],
                                     (sx + drift, sy, 1, 1))
    # ============================================================
    # SKILL Q - FROSTSHARDS (multi ice projectile)
    # ============================================================
    def _draw_frostshards_skill(surface, boss, x, y, timer, phase):
        """5 ice shards flying to target."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_brumhar._target_position(boss, x, y)
        # Origin from hook tip
        origin_x = x + facing * 25
        origin_y = y - 5
        if progress < 0.2:
            # Charge
            t = progress / 0.2
            cr = int(3 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_brumhar._alpha(200 * (cr + 4 - r) / (cr + 4) * t)
                _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["ice_dark"], alpha),
                                      (origin_x, origin_y), r)
            _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["ice_mid"], (origin_x, origin_y), cr - 2)
            _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["ice_light"], (origin_x, origin_y), max(1, cr - 4))
            _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["ice_shine"], (origin_x, origin_y), max(1, cr - 6))
            return
        # Multiple shards flying
        t = (progress - 0.2) / 0.8
        num_shards = 5
        for i in range(num_shards):
            # Stagger each shard
            shard_delay = i * 0.08
            shard_t = max(0.0, min(1.0, t - shard_delay))
            if shard_t <= 0:
                continue
            # Slight spread
            spread_y = (i - 2) * 8  # -16, -8, 0, 8, 16
            target_x = tx + (i - 2) * 4
            target_y = ty + spread_y
            bx = int(origin_x + (target_x - origin_x) * shard_t)
            by = int(origin_y + (target_y - origin_y) * shard_t)
            angle = math.atan2(target_y - origin_y, target_x - origin_x)
            # Shard trail (small)
            for j in range(4):
                trail_t = max(0.0, shard_t - j * 0.03)
                px = int(origin_x + (target_x - origin_x) * trail_t)
                py = int(origin_y + (target_y - origin_y) * trail_t)
                alpha = _NS_brumhar._alpha(200 - j * 40)
                size = max(1, 4 - j)
                _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["ice_dark"], alpha),
                                      (px, py), size)
                _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["ice_mid"], alpha),
                                      (px, py), max(1, size - 1))
                _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["ice_light"], alpha),
                                      (px, py), max(1, size - 2))
            # Shard shape (diamond ice crystal)
            _NS_brumhar._draw_ice_shard(surface, bx, by, angle)
            # Impact per shard
            if shard_t > 0.9:
                st = (shard_t - 0.9) / 0.1
                r = int(4 + st * 8)
                alpha = _NS_brumhar._alpha(200 * (1 - st))
                _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["ice_mid"], alpha),
                                      (target_x, target_y), r, 2)
                _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["ice_light"], alpha),
                                      (target_x, target_y), max(1, r - 3), 1)
    def _draw_ice_shard(surface, cx, cy, angle):
        """Small ice crystal diamond shape pointing in direction."""
        # Compute rotated diamond points
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        # Diamond: 4 points, elongated in angle direction
        pts = [
            (cx + int(cos_a * 6), cy + int(sin_a * 6)),   # tip
            (cx + int(-sin_a * 2), cy + int(cos_a * 2)),
            (cx - int(cos_a * 3), cy - int(sin_a * 3)),   # tail
            (cx - int(-sin_a * 2), cy - int(cos_a * 2)),
        ]
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in pts])
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["ice_darkest"], pts)
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["ice_dark"], [
            pts[0],
            (int(pts[0][0] * 0.7 + pts[1][0] * 0.3),
             int(pts[0][1] * 0.7 + pts[1][1] * 0.3)),
            pts[2],
            (int(pts[0][0] * 0.7 + pts[3][0] * 0.3),
             int(pts[0][1] * 0.7 + pts[3][1] * 0.3)),
        ])
        # Highlight edge
        pygame.draw.line(surface, _NS_brumhar.PALETTE["ice_light"], pts[0], pts[2], 1)
        pygame.draw.line(surface, _NS_brumhar.PALETTE["ice_shine"],
                         pts[0],
                         (int(pts[0][0] * 0.6 + pts[2][0] * 0.4),
                          int(pts[0][1] * 0.6 + pts[2][1] * 0.4)), 1)
        # Bright tip
        pygame.draw.rect(surface, _NS_brumhar.PALETTE["ice_shine"], (pts[0][0], pts[0][1], 1, 1))
        pygame.draw.rect(surface, _NS_brumhar.PALETTE["white"], (pts[0][0], pts[0][1], 1, 1))
    # ============================================================
    # SKILL W - GLACIER BALL (growing snowball)
    # ============================================================
    def _draw_glacierball_skill(surface, boss, x, y, timer, phase):
        """Snowball growing as it rolls forward."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_brumhar._target_position(boss, x, y)
        origin_x = x + facing * 24
        origin_y = y + 8
        if progress < 0.15:
            # Roll wind-up (small ball at hand)
            t = progress / 0.15
            r = int(3 + t * 5)
            _NS_brumhar._draw_snowball(surface, origin_x, origin_y, r, phase, alpha_mult=1.0)
            return
        # Rolling forward - grows over time
        t = (progress - 0.15) / 0.85
        t = min(1.0, t)
        # Ball position
        bx = int(origin_x + (tx - origin_x) * t)
        by = int(origin_y + (ty - origin_y) * t * 0.3)  # mostly horizontal
        # Ball size grows from 8 to 22
        ball_r = int(8 + t * 14)
        # Trail behind (motion blur snowballs decreasing)
        for i in range(6):
            trail_t = max(0.0, t - i * 0.05)
            if trail_t <= 0:
                continue
            px = int(origin_x + (tx - origin_x) * trail_t)
            py = int(origin_y + (ty - origin_y) * trail_t * 0.3)
            alpha = _NS_brumhar._alpha(160 - i * 25)
            trail_r = max(2, ball_r - i * 2)
            _NS_brumhar._draw_snowball(surface, px, py, trail_r, phase, alpha_mult=alpha / 255)
        # Main big snowball
        _NS_brumhar._draw_snowball(surface, bx, by, ball_r, phase, alpha_mult=1.0)
        # Snow flying off sides
        for i in range(8):
            angle = phase * 3 + i * math.pi / 4
            sr = ball_r + int(math.sin(phase * 5 + i) * 3)
            sx = bx + int(math.cos(angle) * sr)
            sy = by + int(math.sin(angle) * sr)
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["snow_light"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["ice_shine"], (sx, sy, 1, 1))
        # Ground snow trail behind
        for i in range(6):
            gt = i / 6
            gx = int(origin_x + (bx - origin_x) * (1 - gt))
            gy = by + ball_r - 2
            alpha = _NS_brumhar._alpha(180 * (1 - gt))
            pygame.draw.ellipse(surface, (*_NS_brumhar.PALETTE["snow_mid"], alpha),
                                (gx - 6, gy, 12, 3))
        # Impact
        if t > 0.9:
            st = (t - 0.9) / 0.1
            radius = int(ball_r + st * 20)
            alpha = _NS_brumhar._alpha(220 * (1 - st))
            _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["ice_dark"], alpha),
                                  (tx, ty), radius, 3)
            _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["ice_mid"], alpha),
                                  (tx, ty), max(1, radius - 5), 2)
            _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["ice_light"], alpha),
                                  (tx, ty), max(1, radius - 12), 1)
            for i in range(12):
                a_s = i * math.pi / 6
                ex = tx + int(math.cos(a_s) * radius)
                ey = ty + int(math.sin(a_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_brumhar.PALETTE["ice_shine"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_brumhar.PALETTE["white"], alpha),
                                 (ex, ey, 1, 1))
    def _draw_snowball(surface, cx, cy, r, phase, alpha_mult=1.0):
        """A snowball at position."""
        base_alpha = int(255 * alpha_mult)
        if base_alpha <= 0:
            return
        # Shadow
        _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["shadow_deep"], base_alpha),
                              (cx + 2, cy + 2), r)
        # Body layers
        _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["snow_dark"], base_alpha), (cx, cy), r)
        _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["fur_dark"], base_alpha), (cx, cy), r - 1)
        _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["snow_mid"], base_alpha), (cx, cy), r - 2)
        _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["snow_light"], base_alpha),
                              (cx - r // 3, cy - r // 3), max(1, r - 4))
        # Bright shine
        _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["fur_shine"], base_alpha),
                              (cx - r // 2, cy - r // 2), max(1, r // 3))
        pygame.draw.rect(surface, (*_NS_brumhar.PALETTE["white"], base_alpha),
                         (cx - r // 2, cy - r // 2, 1, 1))
        # Texture spots (chunks of ice)
        for i in range(3):
            ta = phase + i * math.pi * 2 / 3
            tx = cx + int(math.cos(ta) * r * 0.6)
            ty = cy + int(math.sin(ta) * r * 0.6)
            pygame.draw.rect(surface, (*_NS_brumhar.PALETTE["fur_dark"], base_alpha),
                             (tx, ty, 2, 1))
            pygame.draw.rect(surface, (*_NS_brumhar.PALETTE["fur_shine"], base_alpha),
                             (tx, ty, 1, 1))
    # ============================================================
    # SKILL E - RIME PILLARS (ice wall)
    # ============================================================
    def _draw_rimepillars_ground(surface, boss, x, y, timer, phase):
        """Ground crack line where pillars will rise."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Wall origin
        wall_x = x + facing * 55
        wall_y = y + 46
        # Ground rectangle showing where wall spawns
        wall_w = int(60 * min(1.0, progress * 2))
        pygame.draw.ellipse(surface, (*_NS_brumhar.PALETTE["ice_darkest"], 200),
                            (wall_x - wall_w // 2, wall_y - 6, wall_w, 12))
        pygame.draw.ellipse(surface, (*_NS_brumhar.PALETTE["ice_dark"], 220),
                            (wall_x - wall_w // 2 + 2, wall_y - 5, wall_w - 4, 10))
        pygame.draw.ellipse(surface, (*_NS_brumhar.PALETTE["ice_mid"], 180),
                            (wall_x - wall_w // 2 + 4, wall_y - 4, wall_w - 8, 8))
    def _draw_rimepillars_foreground(surface, boss, x, y, timer, phase):
        """Ice crystal pillars erupt from ground."""
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        wall_x = x + facing * 55
        wall_y = y + 46
        # 7 pillars along a line
        num_pillars = 7
        for i in range(num_pillars):
            offset_x = -30 + i * 10
            # Stagger heights and grow timing
            pillar_delay = (i % 3) * 0.1
            pillar_progress = max(0.0, (progress - pillar_delay) / max(0.01, 1 - pillar_delay))
            if pillar_progress <= 0:
                continue
            # Height (grows then holds)
            max_h = 30 - abs(offset_x) // 4
            if pillar_progress < 0.4:
                height = int(pillar_progress * 2.5 * max_h)
            else:
                height = max_h
            if height < 3:
                continue
            px = wall_x + offset_x
            py = wall_y
            _NS_brumhar._draw_ice_pillar(surface, px, py, height, phase + i)
    def _draw_ice_pillar(surface, cx, base_y, height, phase):
        """A single ice crystal pillar."""
        tip_y = base_y - height
        # Width tapered
        base_w = 6
        tip_w = 2
        # Pillar polygon (elongated diamond)
        pts = [
            (cx - base_w // 2, base_y),
            (cx - base_w // 2 - 1, base_y - height // 3),
            (cx - tip_w // 2, tip_y + 2),
            (cx, tip_y),
            (cx + tip_w // 2, tip_y + 2),
            (cx + base_w // 2 + 1, base_y - height // 3),
            (cx + base_w // 2, base_y),
        ]
        # Shadow
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in pts])
        # Base ice
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["ice_darkest"], pts)
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["ice_dark"], [
            (cx - base_w // 2 + 1, base_y - 1),
            (cx - base_w // 2, base_y - height // 3),
            (cx, tip_y + 1),
            (cx + base_w // 2, base_y - height // 3),
            (cx + base_w // 2 - 1, base_y - 1),
        ])
        _NS_brumhar._poly(surface, _NS_brumhar.PALETTE["ice_mid"], [
            (cx - 1, base_y - 1),
            (cx - 1, base_y - height // 2),
            (cx, tip_y + 2),
            (cx + 1, base_y - height // 2),
            (cx + 1, base_y - 1),
        ])
        # Bright edge highlight
        pygame.draw.line(surface, _NS_brumhar.PALETTE["ice_light"],
                         (cx - 1, base_y - 2), (cx, tip_y + 1), 1)
        pygame.draw.line(surface, _NS_brumhar.PALETTE["ice_shine"],
                         (cx, tip_y + 1), (cx, tip_y), 1)
        # Sparkle at tip
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for r in range(3, 0, -1):
            alpha = _NS_brumhar._alpha(200 * (3 - r) / 3 * pulse)
            _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["ice_hot"], alpha),
                                  (cx, tip_y), r)
        pygame.draw.rect(surface, _NS_brumhar.PALETTE["white"], (cx, tip_y, 1, 1))
    # ============================================================
    # SKILL R - TITAN CHARGE (dash punch)
    # ============================================================
    def _draw_titancharge_ground(surface, boss, x, y, timer, phase):
        """Impact ground where boss punches."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Impact point ahead
        impact_x = x + facing * 60
        impact_y = y + 46
        if progress > 0.5:
            t = (progress - 0.5) / 0.5
            r = int(35 * t)
            alpha = _NS_brumhar._alpha(220 * (1 - t * 0.5))
            pygame.draw.ellipse(surface, (*_NS_brumhar.PALETTE["ice_darkest"], alpha),
                                (impact_x - r, impact_y - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_brumhar.PALETTE["ice_dark"], alpha),
                                (impact_x - r + 3, impact_y - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            # Ice crack lines
            for i in range(8):
                a = i * math.pi / 4
                x2 = impact_x + int(math.cos(a) * r)
                y2 = impact_y + int(math.sin(a) * r * 0.4)
                pygame.draw.line(surface, (*_NS_brumhar.PALETTE["ice_light"], alpha),
                                 (impact_x, impact_y), (x2, y2), 1)
    def _draw_titancharge_foreground(surface, boss, x, y, timer, phase):
        """Dash trail + impact burst."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Dash speed lines behind boss
        if progress < 0.7:
            for i in range(10):
                streak_x = x - facing * (10 + i * 8)
                streak_y = y - 5 + int(math.sin(phase * 4 + i) * 5)
                alpha = _NS_brumhar._alpha(220 * (1 - i / 10))
                length = 12 - i
                pygame.draw.line(surface, (*_NS_brumhar.PALETTE["ice_light"], alpha),
                                 (streak_x, streak_y),
                                 (streak_x + facing * length, streak_y), 2)
                pygame.draw.line(surface, (*_NS_brumhar.PALETTE["ice_shine"], alpha),
                                 (streak_x, streak_y),
                                 (streak_x + facing * length, streak_y), 1)
        # Impact burst at fist
        impact_x = x + facing * 60
        impact_y = y - 5
        if progress > 0.4:
            t = (progress - 0.4) / 0.6
            burst_r = int(15 + t * 30)
            alpha = _NS_brumhar._alpha(240 * (1 - t))
            for r in range(burst_r, 3, -3):
                a = _NS_brumhar._alpha(180 * (burst_r - r) / burst_r * (1 - t))
                _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["ice_dark"], a),
                                      (impact_x, impact_y), r)
            _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["ice_darkest"], (impact_x, impact_y), 12)
            _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["ice_mid"], (impact_x, impact_y), 8)
            _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["ice_light"], (impact_x, impact_y), 4)
            _NS_brumhar._aacircle(surface, _NS_brumhar.PALETTE["ice_shine"], (impact_x, impact_y), 2)
            pygame.draw.rect(surface, _NS_brumhar.PALETTE["white"], (impact_x, impact_y, 2, 2))
            # Radial ice shards outward
            for i in range(12):
                angle_s = i * math.pi / 6
                shard_r = burst_r
                sx = impact_x + int(math.cos(angle_s) * shard_r)
                sy = impact_y + int(math.sin(angle_s) * shard_r)
                _NS_brumhar._draw_ice_shard(surface, sx, sy, angle_s)
            # Snow puffs
            for i in range(10):
                puff_angle = i * math.pi / 5
                pr = burst_r + int(math.sin(phase * 4 + i) * 5)
                px = impact_x + int(math.cos(puff_angle) * pr)
                py = impact_y + int(math.sin(puff_angle) * pr * 0.6)
                _NS_brumhar._aacircle(surface, (*_NS_brumhar.PALETTE["snow_mid"], alpha), (px, py), 2)
                pygame.draw.rect(surface, (*_NS_brumhar.PALETTE["snow_light"], alpha), (px, py, 1, 1))



# ====================================================================
# ZORASHI (SERPENT SAGE) - Mini Boss
# ====================================================================

class _NS_zorashi:
    """Namespace zorashi - Serpent Sage boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Pale skin (sickly white-tan)
        "skin_darkest": (110, 95, 90),
        "skin_dark": (175, 160, 155),
        "skin_mid": (220, 210, 205),
        "skin_light": (245, 240, 235),
        # Hair (jet black long)
        "hair_darkest": (5, 5, 12),
        "hair_dark": (18, 15, 28),
        "hair_mid": (45, 40, 60),
        "hair_light": (85, 80, 100),
        # Robe cream/tan (haori outer)
        "robe_darkest": (55, 45, 30),
        "robe_dark": (110, 90, 60),
        "robe_mid": (170, 145, 105),
        "robe_light": (215, 195, 160),
        "robe_shine": (245, 230, 200),
        # Inner robe dark (kosode)
        "inner_darkest": (12, 8, 15),
        "inner_dark": (30, 22, 35),
        "inner_mid": (60, 50, 70),
        "inner_light": (100, 90, 115),
        # Purple obi (sash)
        "obi_darkest": (30, 10, 45),
        "obi_dark": (65, 25, 100),
        "obi_mid": (125, 60, 175),
        "obi_light": (185, 120, 225),
        # Serpent purple (snake body, projectile)
        "serpent_darkest": (25, 10, 40),
        "serpent_dark": (70, 30, 105),
        "serpent_mid": (130, 65, 175),
        "serpent_light": (185, 125, 220),
        "serpent_hot": (225, 180, 245),
        "serpent_shine": (245, 220, 255),
        # Venom green
        "venom_darkest": (25, 40, 5),
        "venom_dark": (75, 115, 15),
        "venom_mid": (150, 205, 35),
        "venom_light": (215, 250, 90),
        "venom_hot": (245, 255, 160),
        "venom_shine": (255, 255, 220),
        # Eye (yellow snake eye)
        "eye_socket": (8, 5, 12),
        "eye_dark": (85, 65, 15),
        "eye_mid": (200, 175, 55),
        "eye_light": (245, 225, 130),
        "eye_glow": (255, 250, 200),
        # Serpent scales (light grey-purple)
        "scale_dark": (85, 75, 100),
        "scale_mid": (155, 140, 175),
        "scale_light": (210, 195, 225),
        # Serpent belly (cream)
        "belly_dark": (100, 90, 70),
        "belly_mid": (180, 165, 130),
        "belly_light": (235, 220, 180),
        # Fangs
        "fang_dark": (185, 175, 150),
        "fang_light": (245, 240, 220),
        # Smoke tail (floating)
        "smoke_darkest": (10, 5, 20),
        "smoke_dark": (30, 15, 50),
        "smoke_mid": (65, 35, 100),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_zorashi._clamp(color)
        if _NS_zorashi.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_zorashi._clamp(color)
        if _NS_zorashi.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_zorashi._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_zorashi(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_zorashi._detect_moving(boss)
        _NS_zorashi._update_attack_anim(boss)
        attacking = getattr(boss, "_zs_attack_active", False)
        # Ambient
        _NS_zorashi._draw_serpent_aura(surface, x, y, pulse)
        _NS_zorashi._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX
        if active_skill == "w":
            _NS_zorashi._draw_summon_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zorashi._draw_hydra_ground(surface, boss, x, y, skill_timer, pulse)
        # Body
        if attacking:
            _NS_zorashi._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_zorashi._draw_walk(surface, boss, x, y)
        else:
            _NS_zorashi._draw_idle(surface, boss, x, y)
        # Coiled serpent around body (idle decoration - after body)
        _NS_zorashi._draw_coiled_serpent(surface, x, y, boss.direction, pulse,
                                          attacking, active_skill)
        # Foreground FX
        if active_skill == "q":
            _NS_zorashi._draw_viperfang_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_zorashi._draw_summon_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_zorashi._draw_venom_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zorashi._draw_hydra_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_zs_attack_active", False))
        if not active and timer <= 2:
            boss._zs_attack_active = True
            boss._zs_attack_frame = 0
            active = True
        if active:
            boss._zs_attack_frame = int(getattr(boss, "_zs_attack_frame", 0)) + 1
            if boss._zs_attack_frame >= cooldown:
                boss._zs_attack_active = False
                boss._zs_attack_frame = 0
                active = False
        boss._zs_attack_progress = (
            min(1.0, getattr(boss, "_zs_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_zs_last_x"):
            boss._zs_last_x = boss.x
            boss._zs_last_y = boss.y
            return False
        dx = abs(boss.x - boss._zs_last_x)
        dy = abs(boss.y - boss._zs_last_y)
        boss._zs_last_x = boss.x
        boss._zs_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_zorashi._draw_shadow(surface, x, y + 50)
        _NS_zorashi._draw_smoke_base(surface, x, y + 26 + bob, boss.pulse)
        _NS_zorashi._draw_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")
    def _draw_walk(surface, boss, x, y):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.7) * 5)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_zorashi._draw_shadow(surface, x + sway, y + 50)
        _NS_zorashi._draw_smoke_base(surface, x + sway, y + 26 + bob, phase,
                                     moving=True, facing=boss.direction)
        _NS_zorashi._draw_body(surface, x + sway, y + bob, boss.direction, phase, "walk")
    def _draw_attack(surface, boss, x, y):
        progress = getattr(boss, "_zs_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        bob = int(math.sin(boss.pulse * 0.5) * 3)
        # Sage rear back → cast forward → recover
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 3) * boss.direction
        elif progress < 0.55:
            t = (progress - 0.35) / 0.2
            lunge = int((-3 + t * 10)) * boss.direction
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(7 * (1 - t)) * boss.direction
        _NS_zorashi._draw_shadow(surface, x + lunge, y + 50)
        _NS_zorashi._draw_smoke_base(surface, x + lunge, y + 26 + bob, boss.pulse,
                                     intense=True)
        _NS_zorashi._draw_body(surface, x + lunge, y + bob, boss.direction, boss.pulse,
                               "attack", progress)
        _NS_zorashi._draw_venom_projectile(surface, boss, x + lunge, y + bob, progress)
    # ============================================================
    # BODY - Sage with long black hair + robe
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0.0):
        # Long hair BEHIND body
        _NS_zorashi._draw_hair_back(surface, cx, cy - 12, facing, phase)
        # Robe skirt bottom
        _NS_zorashi._draw_robe_skirt(surface, cx, cy, facing, phase)
        # Torso (cream haori)
        _NS_zorashi._draw_torso_robe(surface, cx, cy, facing, phase)
        # Back arm
        _NS_zorashi._draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress)
        # Head
        _NS_zorashi._draw_head(surface, cx, cy - 22, facing, phase)
        # Front hair strands
        _NS_zorashi._draw_hair_front(surface, cx, cy - 22, facing, phase)
        # Front arm (casting)
        _NS_zorashi._draw_front_arm(surface, cx, cy, facing, phase, action, attack_progress)
    def _draw_robe_skirt(surface, cx, cy, facing, phase):
        """Long dark inner robe (hakama-like)."""
        sway = math.sin(phase * 0.5) * 1
        # Skirt shape (flowing)
        skirt_shape = [
            (cx - 10, cy + 8),
            (cx - 12, cy + 14),
            (cx - 13 + int(sway), cy + 22),
            (cx - 12 + int(sway), cy + 30),
            (cx - 9 + int(sway), cy + 34),
            (cx + 9 + int(sway * 0.5), cy + 34),
            (cx + 12 + int(sway * 0.5), cy + 30),
            (cx + 13, cy + 22),
            (cx + 12, cy + 14),
            (cx + 10, cy + 8),
        ]
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["shadow_deep"],
              [(px + 2, py + 3) for px, py in skirt_shape])
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["inner_darkest"], skirt_shape)
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["inner_dark"], [
            (cx - 9, cy + 9), (cx - 11, cy + 14),
            (cx - 12 + int(sway * 0.7), cy + 21),
            (cx - 11 + int(sway * 0.7), cy + 29),
            (cx - 8 + int(sway * 0.5), cy + 33),
            (cx + 8 + int(sway * 0.3), cy + 33),
            (cx + 11 + int(sway * 0.3), cy + 29),
            (cx + 12, cy + 21), (cx + 11, cy + 14), (cx + 9, cy + 9),
        ])
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["inner_mid"], [
            (cx - 6, cy + 10), (cx - 8, cy + 16),
            (cx - 9, cy + 24), (cx - 6, cy + 30),
            (cx + 6, cy + 30), (cx + 9, cy + 24),
            (cx + 8, cy + 16), (cx + 6, cy + 10),
        ])
        # Vertical folds (dark hakama pleats)
        for x_off in (-8, -4, 0, 4, 8):
            pygame.draw.line(surface, _NS_zorashi.PALETTE["inner_darkest"],
                             (cx + x_off, cy + 10),
                             (cx + x_off + int(sway * 0.3), cy + 33), 1)
            pygame.draw.line(surface, _NS_zorashi.PALETTE["inner_light"],
                             (cx + x_off - 1, cy + 12),
                             (cx + x_off - 1 + int(sway * 0.3), cy + 32), 1)
    def _draw_torso_robe(surface, cx, cy, facing, phase):
        """Cream haori robe over dark inner robe."""
        # Under robe first (peek at neck)
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["inner_dark"], [
            (cx - 6, cy - 10),
            (cx + 6, cy - 10),
            (cx + 4, cy - 5),
            (cx - 4, cy - 5),
        ])
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["inner_mid"], [
            (cx - 5, cy - 9),
            (cx + 5, cy - 9),
            (cx + 3, cy - 6),
            (cx - 3, cy - 6),
        ])
        # Outer robe/haori (cream) - wraps around torso
        robe_shape = [
            (cx - 12, cy - 8),
            (cx - 14, cy - 3),
            (cx - 13, cy + 3),
            (cx - 11, cy + 9),
            (cx + 11, cy + 9),
            (cx + 13, cy + 3),
            (cx + 14, cy - 3),
            (cx + 12, cy - 8),
            (cx + 6, cy - 12),
            (cx - 6, cy - 12),
        ]
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in robe_shape])
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["robe_darkest"], robe_shape)
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["robe_dark"], [
            (cx - 11, cy - 7), (cx - 13, cy - 2),
            (cx - 12, cy + 2), (cx - 10, cy + 8),
            (cx + 10, cy + 8), (cx + 12, cy + 2),
            (cx + 13, cy - 2), (cx + 11, cy - 7),
            (cx + 5, cy - 11), (cx - 5, cy - 11),
        ])
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["robe_mid"], [
            (cx - 9, cy - 5), (cx - 11, cy - 1),
            (cx - 10, cy + 3), (cx - 8, cy + 7),
            (cx + 8, cy + 7), (cx + 10, cy + 3),
            (cx + 11, cy - 1), (cx + 9, cy - 5),
            (cx + 4, cy - 9), (cx - 4, cy - 9),
        ])
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["robe_light"], [
            (cx - 7, cy - 4), (cx - 9, cy - 1),
            (cx - 7, cy + 4), (cx + 7, cy + 4),
            (cx + 9, cy - 1), (cx + 7, cy - 4),
            (cx + 3, cy - 7), (cx - 3, cy - 7),
        ])
        # V-neck opening (inner robe visible)
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["inner_darkest"], [
            (cx - 3, cy - 8), (cx, cy - 3),
            (cx + 3, cy - 8), (cx + 2, cy - 4),
            (cx, cy - 1), (cx - 2, cy - 4),
        ])
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["inner_dark"], [
            (cx - 2, cy - 7), (cx, cy - 3),
            (cx + 2, cy - 7), (cx + 1, cy - 4),
            (cx, cy - 2), (cx - 1, cy - 4),
        ])
        # V-fold line down center
        pygame.draw.line(surface, _NS_zorashi.PALETTE["robe_darkest"],
                         (cx, cy - 3), (cx, cy + 8), 1)
        # PURPLE OBI (sash at waist)
        obi_shape = [
            (cx - 13, cy + 5),
            (cx + 13, cy + 5),
            (cx + 14, cy + 12),
            (cx - 14, cy + 12),
        ]
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["shadow_deep"],
              [(p[0] + 1, p[1] + 1) for p in obi_shape])
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["obi_darkest"], obi_shape)
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["obi_dark"], [
            (cx - 12, cy + 6), (cx + 12, cy + 6),
            (cx + 13, cy + 11), (cx - 13, cy + 11),
        ])
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["obi_mid"], [
            (cx - 11, cy + 7), (cx + 11, cy + 7),
            (cx + 12, cy + 10), (cx - 12, cy + 10),
        ])
        # Obi highlight
        pygame.draw.line(surface, _NS_zorashi.PALETTE["obi_light"],
                         (cx - 11, cy + 7), (cx + 11, cy + 7), 1)
        # Small purple gem/knot in center of obi
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for r in range(3, 0, -1):
            alpha = _NS_zorashi._alpha(200 * (3 - r) / 3 * pulse)
            _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["serpent_mid"], alpha),
                                  (cx, cy + 8), r)
        pygame.draw.rect(surface, _NS_zorashi.PALETTE["serpent_light"], (cx, cy + 8, 1, 1))
        pygame.draw.rect(surface, _NS_zorashi.PALETTE["serpent_shine"], (cx, cy + 8, 1, 1))
    def _draw_head(surface, cx, cy, facing, phase):
        """Pale sage face."""
        # Face shape (elongated oval, gaunt)
        face_shape = [
            (cx - 6, cy + 6),
            (cx - 7, cy + 2),
            (cx - 7, cy - 3),
            (cx - 4, cy - 8),
            (cx + 4, cy - 8),
            (cx + 7, cy - 3),
            (cx + 7, cy + 2),
            (cx + 6, cy + 6),
            (cx + 2, cy + 9),
            (cx - 2, cy + 9),
        ]
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in face_shape])
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["skin_darkest"], face_shape)
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["skin_dark"], [
            (cx - 5, cy + 5), (cx - 6, cy + 2),
            (cx - 6, cy - 2), (cx - 3, cy - 7),
            (cx + 3, cy - 7), (cx + 6, cy - 2),
            (cx + 6, cy + 2), (cx + 5, cy + 5),
            (cx + 1, cy + 8), (cx - 1, cy + 8),
        ])
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["skin_mid"], [
            (cx - 4, cy + 3), (cx - 5, cy),
            (cx - 4, cy - 4), (cx - 2, cy - 6),
            (cx + 2, cy - 6), (cx + 4, cy - 4),
            (cx + 5, cy), (cx + 4, cy + 3),
        ])
        # Pale white cheek highlight
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["skin_light"], [
            (cx - 3, cy - 1), (cx - 1, cy - 3),
            (cx - 1, cy), (cx - 3, cy + 1),
        ])
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["skin_light"], [
            (cx + 1, cy - 3), (cx + 3, cy - 1),
            (cx + 3, cy + 1), (cx + 1, cy),
        ])
        # SERPENT EYES (yellow slitted)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_x in (cx - 3, cx + 3):
            # Eye socket dark
            pygame.draw.rect(surface, _NS_zorashi.PALETTE["shadow_deep"],
                             (eye_x - 2, cy - 2, 4, 3))
            pygame.draw.rect(surface, _NS_zorashi.PALETTE["eye_socket"],
                             (eye_x - 2, cy - 2, 4, 3))
            # Yellow iris
            for r in range(3, 0, -1):
                alpha = _NS_zorashi._alpha(120 * (3 - r) / 3 * pulse)
                _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["eye_mid"], alpha),
                                      (eye_x, cy - 1), r)
            pygame.draw.rect(surface, _NS_zorashi.PALETTE["eye_dark"],
                             (eye_x - 1, cy - 1, 3, 2))
            pygame.draw.rect(surface, _NS_zorashi.PALETTE["eye_mid"],
                             (eye_x - 1, cy - 1, 3, 1))
            pygame.draw.rect(surface, _NS_zorashi.PALETTE["eye_light"],
                             (eye_x, cy - 1, 1, 1))
            # Vertical slit pupil (snake)
            pygame.draw.line(surface, _NS_zorashi.PALETTE["shadow_deep"],
                             (eye_x, cy - 1), (eye_x, cy + 1), 1)
        # Purple markings around eyes (like snake pattern)
        for side in (-1, 1):
            # Small purple lines beside eyes
            pygame.draw.line(surface, _NS_zorashi.PALETTE["serpent_dark"],
                             (cx + side * 3, cy + 1),
                             (cx + side * 5, cy + 3), 1)
            pygame.draw.line(surface, _NS_zorashi.PALETTE["serpent_mid"],
                             (cx + side * 3, cy + 1),
                             (cx + side * 4, cy + 2), 1)
        # Nose (subtle)
        pygame.draw.line(surface, _NS_zorashi.PALETTE["skin_darkest"],
                         (cx, cy + 1), (cx, cy + 4), 1)
        pygame.draw.rect(surface, _NS_zorashi.PALETTE["skin_dark"], (cx - 1, cy + 4, 3, 1))
        # Mouth (thin sinister smile)
        pygame.draw.line(surface, _NS_zorashi.PALETTE["shadow_deep"],
                         (cx - 2, cy + 6), (cx + 2, cy + 6), 1)
        # Small fang tips visible
        pygame.draw.rect(surface, _NS_zorashi.PALETTE["fang_light"], (cx - 1, cy + 6, 1, 1))
        pygame.draw.rect(surface, _NS_zorashi.PALETTE["fang_light"], (cx + 1, cy + 6, 1, 1))
    def _draw_hair_back(surface, cx, cy, facing, phase):
        """Long straight black hair down back."""
        sway = math.sin(phase * 0.4) * 2
        # Big hair mass (flowing down and slightly wider than head)
        hair_shape = [
            (cx - 10, cy - 6),
            (cx - 12 + int(sway * 0.5), cy),
            (cx - 13 + int(sway), cy + 10),
            (cx - 12 + int(sway), cy + 22),
            (cx - 10 + int(sway), cy + 34),
            (cx - 6 + int(sway * 0.7), cy + 42),
            (cx + 6 + int(sway * 0.3), cy + 42),
            (cx + 10 + int(sway * 0.3), cy + 34),
            (cx + 12 + int(sway * 0.3), cy + 22),
            (cx + 13 + int(sway * 0.3), cy + 10),
            (cx + 12, cy),
            (cx + 10, cy - 6),
        ]
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["shadow_deep"],
              [(px + 2, py + 2) for px, py in hair_shape])
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["hair_darkest"], hair_shape)
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["hair_dark"], [
            (cx - 9, cy - 5), (cx - 11 + int(sway * 0.4), cy),
            (cx - 12 + int(sway * 0.8), cy + 10),
            (cx - 11 + int(sway * 0.8), cy + 21),
            (cx - 9 + int(sway * 0.8), cy + 33),
            (cx - 5 + int(sway * 0.5), cy + 41),
            (cx + 5 + int(sway * 0.3), cy + 41),
            (cx + 9 + int(sway * 0.3), cy + 33),
            (cx + 11 + int(sway * 0.3), cy + 21),
            (cx + 12 + int(sway * 0.3), cy + 10),
            (cx + 11, cy), (cx + 9, cy - 5),
        ])
        # Straight hair strand highlights (vertical streaks)
        for i, x_off in enumerate((-9, -5, 0, 5, 9)):
            hy1 = cy - 2
            hy2 = cy + 38 + i
            wave_x = int(sway * 0.5)
            pygame.draw.line(surface, _NS_zorashi.PALETTE["hair_mid"],
                             (cx + x_off + wave_x, hy1),
                             (cx + x_off + wave_x + int(sway * 0.3), hy2), 1)
            pygame.draw.line(surface, _NS_zorashi.PALETTE["hair_light"],
                             (cx + x_off + wave_x - 1, hy1 + 5),
                             (cx + x_off + wave_x - 1 + int(sway * 0.3), hy2 - 5), 1)
    def _draw_hair_front(surface, cx, cy, facing, phase):
        """Front hair strands framing face."""
        sway = math.sin(phase * 0.4) * 1
        # Center bang
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["hair_darkest"], [
            (cx - 6, cy - 8),
            (cx - 5, cy - 4),
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 5, cy - 4),
            (cx + 6, cy - 8),
        ])
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["hair_dark"], [
            (cx - 5, cy - 7),
            (cx - 4, cy - 5),
            (cx - 1, cy - 4),
            (cx + 1, cy - 4),
            (cx + 4, cy - 5),
            (cx + 5, cy - 7),
        ])
        # Side hair strands falling past face
        for side in (-1, 1):
            base_x = cx + side * 5
            base_y = cy - 6
            # Long strand
            tip_x = base_x + side * 1 + int(sway * side * 0.3)
            tip_y = base_y + 20
            pygame.draw.line(surface, _NS_zorashi.PALETTE["hair_darkest"],
                             (base_x, base_y), (tip_x, tip_y), 3)
            pygame.draw.line(surface, _NS_zorashi.PALETTE["hair_dark"],
                             (base_x, base_y), (tip_x, tip_y), 2)
            pygame.draw.line(surface, _NS_zorashi.PALETTE["hair_mid"],
                             (base_x - 1, base_y + 3),
                             (tip_x - 1, tip_y - 3), 1)
    def _draw_back_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm - subtle gesture."""
        arm_sway = math.sin(phase * 0.5) * 1
        back = -facing
        shoulder_x = cx + back * 10
        shoulder_y = cy - 6
        if action == "attack":
            # Slightly raised
            t = attack_progress
            elbow_x = shoulder_x + back * 3 - int(t * 2)
            elbow_y = shoulder_y + 4 - int(t * 2)
            hand_x = elbow_x + back * 1
            hand_y = elbow_y + 6
        else:
            elbow_x = shoulder_x + back * 3
            elbow_y = shoulder_y + 6 + int(arm_sway)
            hand_x = elbow_x + back * 1
            hand_y = elbow_y + 8
        _NS_zorashi._draw_arm_segment(surface, (shoulder_x, shoulder_y),
                                       (elbow_x, elbow_y), 5, 0.8)
        _NS_zorashi._draw_arm_segment(surface, (elbow_x, elbow_y),
                                       (hand_x, hand_y), 4, 0.8)
        _NS_zorashi._draw_hand(surface, hand_x, hand_y, back, phase, 0.8)
    def _draw_front_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm - casting hand."""
        arm_sway = math.sin(phase * 0.5) * 1
        shoulder_x = cx + facing * 10
        shoulder_y = cy - 6
        if action == "attack":
            # Extended forward casting
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                arm_forward = int(t * 4)
                arm_raise = int(t * 3)
            elif attack_progress < 0.55:
                t = (attack_progress - 0.35) / 0.2
                arm_forward = int(4 + t * 10)
                arm_raise = int(3 - t * 3)
            else:
                t = (attack_progress - 0.55) / 0.45
                arm_forward = int(14 * (1 - t))
                arm_raise = 0
        else:
            arm_forward = 4  # Slightly extended (casting stance)
            arm_raise = int(arm_sway)
        elbow_x = shoulder_x + facing * (5 + arm_forward // 2)
        elbow_y = shoulder_y + 3 - arm_raise
        hand_x = shoulder_x + facing * (10 + arm_forward)
        hand_y = shoulder_y + 2 - arm_raise
        _NS_zorashi._draw_arm_segment(surface, (shoulder_x, shoulder_y),
                                       (elbow_x, elbow_y), 5, 1.0)
        _NS_zorashi._draw_arm_segment(surface, (elbow_x, elbow_y),
                                       (hand_x, hand_y), 4, 1.0)
        _NS_zorashi._draw_hand(surface, hand_x, hand_y, facing, phase, 1.0,
                                casting=(action == "attack" or attack_progress > 0))
    def _draw_arm_segment(surface, p1, p2, thickness, depth_shade=1.0):
        """Robe-covered arm."""
        def shade(color):
            return tuple(int(c * depth_shade) for c in color)
        _NS_zorashi._aaline(surface, _NS_zorashi.PALETTE["shadow_deep"],
                (p1[0] + 2, p1[1] + 2), (p2[0] + 2, p2[1] + 2), thickness + 1)
        _NS_zorashi._aaline(surface, shade(_NS_zorashi.PALETTE["robe_darkest"]),
                p1, p2, thickness)
        _NS_zorashi._aaline(surface, shade(_NS_zorashi.PALETTE["robe_dark"]),
                p1, p2, max(1, thickness - 2))
        _NS_zorashi._aaline(surface, shade(_NS_zorashi.PALETTE["robe_mid"]),
                (p1[0] - 1, p1[1] - 1), (p2[0] - 1, p2[1] - 1),
                max(1, thickness - 4))
        # Highlight
        _NS_zorashi._aaline(surface, shade(_NS_zorashi.PALETTE["robe_light"]),
                (p1[0] - 1, p1[1] - 1), (p2[0] - 1, p2[1] - 1),
                max(1, thickness - 5))
    def _draw_hand(surface, cx, cy, facing, phase, depth_shade=1.0, casting=False):
        """Pale hand with clawed fingers."""
        def shade(color):
            return tuple(int(c * depth_shade) for c in color)
        # Palm
        pygame.draw.rect(surface, shade(_NS_zorashi.PALETTE["skin_darkest"]),
                         (cx - 2, cy - 1, 5, 4))
        pygame.draw.rect(surface, shade(_NS_zorashi.PALETTE["skin_dark"]),
                         (cx - 1, cy - 1, 4, 3))
        pygame.draw.rect(surface, shade(_NS_zorashi.PALETTE["skin_mid"]),
                         (cx - 1, cy - 1, 4, 1))
        # Extended clawed fingers
        for i, (fx, fy) in enumerate([(2, 0), (3, 1), (2, 2)]):
            claw_x = cx + facing * (fx + 1)
            claw_y = cy + fy - 1
            pygame.draw.rect(surface, shade(_NS_zorashi.PALETTE["skin_dark"]),
                             (claw_x, claw_y, 2, 1))
            pygame.draw.rect(surface, shade(_NS_zorashi.PALETTE["skin_mid"]),
                             (claw_x, claw_y, 1, 1))
            # Purple claw tip
            pygame.draw.rect(surface, shade(_NS_zorashi.PALETTE["serpent_mid"]),
                             (claw_x + facing, claw_y, 1, 1))
        # Casting glow at palm
        if casting:
            pulse = math.sin(phase * 3) * 0.3 + 0.7
            palm_x = cx + facing * 2
            palm_y = cy + 1
            for r in range(6, 0, -1):
                alpha = _NS_zorashi._alpha(200 * (6 - r) / 6 * pulse)
                _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["serpent_mid"], alpha),
                                      (palm_x, palm_y), r)
            _NS_zorashi._aacircle(surface, _NS_zorashi.PALETTE["serpent_light"], (palm_x, palm_y), 2)
            pygame.draw.rect(surface, _NS_zorashi.PALETTE["serpent_shine"], (palm_x, palm_y, 1, 1))
    # ============================================================
    # COILED SERPENT (around body decoration)
    # ============================================================
    def _draw_coiled_serpent(surface, cx, cy, facing, phase, attacking, active_skill):
        """Purple serpent coiled around body."""
        # Skip if certain skills active
        if active_skill in ("w", "r"):
            return
        back = -facing
        sway = math.sin(phase * 0.7) * 2
        # Serpent starts from behind body, coils around, head peeks over shoulder
        # Body coil segments (arc from behind to shoulder area)
        segments = 12
        base_x = cx - back * 15
        base_y = cy + 20  # start near ground behind
        points = []
        for i in range(segments + 1):
            t = i / segments
            # Path: from behind low → coil around body → up to shoulder area
            # Use spiral-like path
            angle = -math.pi * 0.5 + t * math.pi * 1.8
            radius_x = 16 + math.sin(t * math.pi * 2) * 4
            radius_y = 12 + math.sin(t * math.pi) * 3
            px = int(base_x + math.cos(angle) * radius_x * back + int(sway * (1 - t)))
            py = int(base_y - t * 30 + math.sin(angle) * radius_y * 0.5)
            points.append((px, py))
        # Draw serpent body segments
        for i in range(len(points) - 1):
            thickness = max(3, 7 - i // 3)
            # Shadow
            _NS_zorashi._aaline(surface, _NS_zorashi.PALETTE["shadow_deep"],
                    (points[i][0] + 1, points[i][1] + 1),
                    (points[i + 1][0] + 1, points[i + 1][1] + 1),
                    thickness + 1)
            # Dark base
            _NS_zorashi._aaline(surface, _NS_zorashi.PALETTE["serpent_darkest"],
                    points[i], points[i + 1], thickness)
            _NS_zorashi._aaline(surface, _NS_zorashi.PALETTE["serpent_dark"],
                    points[i], points[i + 1], max(1, thickness - 1))
            _NS_zorashi._aaline(surface, _NS_zorashi.PALETTE["scale_mid"],
                    (points[i][0], points[i][1] - 1),
                    (points[i + 1][0], points[i + 1][1] - 1),
                    max(1, thickness - 3))
            # Scale highlights (bright)
            _NS_zorashi._aaline(surface, _NS_zorashi.PALETTE["scale_light"],
                    (points[i][0], points[i][1] - 2),
                    (points[i + 1][0], points[i + 1][1] - 2),
                    max(1, thickness - 5))
        # Scale pattern dots on visible segments
        for i in range(3, len(points) - 2, 2):
            p = points[i]
            pygame.draw.rect(surface, _NS_zorashi.PALETTE["serpent_darkest"], (p[0], p[1] - 1, 1, 1))
            pygame.draw.rect(surface, _NS_zorashi.PALETTE["serpent_mid"], (p[0] + 1, p[1], 1, 1))
        # SERPENT HEAD at end (peek over shoulder)
        if len(points) > 1:
            head = points[-1]
            prev = points[-2]
            head_angle = math.atan2(head[1] - prev[1], head[0] - prev[0])
            _NS_zorashi._draw_serpent_head(surface, head[0], head[1], head_angle, phase, size=1.0)
    def _draw_serpent_head(surface, cx, cy, angle, phase, size=1.0):
        """Purple snake head with fangs and glowing eyes."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        # Head shape (elongated)
        s = size
        head_pts = [
            (cx + int(cos_a * 8 * s), cy + int(sin_a * 8 * s)),  # snout
            (cx + int(cos_a * 5 * s) + int(-sin_a * 4 * s),
             cy + int(sin_a * 5 * s) + int(cos_a * 4 * s)),
            (cx + int(-sin_a * 5 * s),
             cy + int(cos_a * 5 * s)),
            (cx + int(-cos_a * 3 * s) + int(-sin_a * 3 * s),
             cy + int(-sin_a * 3 * s) + int(cos_a * 3 * s)),
            (cx + int(-cos_a * 3 * s) - int(-sin_a * 3 * s),
             cy + int(-sin_a * 3 * s) - int(cos_a * 3 * s)),
            (cx - int(-sin_a * 5 * s),
             cy - int(cos_a * 5 * s)),
            (cx + int(cos_a * 5 * s) - int(-sin_a * 4 * s),
             cy + int(sin_a * 5 * s) - int(cos_a * 4 * s)),
        ]
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["serpent_darkest"], head_pts)
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["serpent_dark"], [
            (int(cx + cos_a * 7 * s), int(cy + sin_a * 7 * s)),
            (int(cx + cos_a * 4 * s + -sin_a * 3 * s),
             int(cy + sin_a * 4 * s + cos_a * 3 * s)),
            (int(cx + -sin_a * 4 * s), int(cy + cos_a * 4 * s)),
            (int(cx + -cos_a * 2 * s), int(cy + -sin_a * 2 * s)),
            (int(cx - -sin_a * 4 * s), int(cy - cos_a * 4 * s)),
            (int(cx + cos_a * 4 * s - -sin_a * 3 * s),
             int(cy + sin_a * 4 * s - cos_a * 3 * s)),
        ])
        _NS_zorashi._poly(surface, _NS_zorashi.PALETTE["scale_mid"], [
            (int(cx + cos_a * 6 * s), int(cy + sin_a * 6 * s)),
            (int(cx + cos_a * 3 * s + -sin_a * 2 * s),
             int(cy + sin_a * 3 * s + cos_a * 2 * s)),
            (int(cx + -sin_a * 3 * s), int(cy + cos_a * 3 * s)),
            (int(cx - -sin_a * 3 * s), int(cy - cos_a * 3 * s)),
            (int(cx + cos_a * 3 * s - -sin_a * 2 * s),
             int(cy + sin_a * 3 * s - cos_a * 2 * s)),
        ])
        # Belly cream color (bottom of head)
        pygame.draw.line(surface, _NS_zorashi.PALETTE["belly_mid"],
                         (int(cx + cos_a * 5 * s), int(cy + sin_a * 5 * s + 1)),
                         (int(cx - cos_a * 1 * s), int(cy - sin_a * 1 * s + 1)), 1)
        # EYE (yellow snake eye)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        eye_off_x = int(cos_a * 3 * s + -sin_a * 1 * s)
        eye_off_y = int(sin_a * 3 * s + cos_a * 1 * s)
        ex = cx + eye_off_x
        ey = cy + eye_off_y - 1
        pygame.draw.rect(surface, _NS_zorashi.PALETTE["shadow_deep"], (ex - 1, ey, 2, 2))
        for r in range(int(3 * s), 0, -1):
            alpha = _NS_zorashi._alpha(150 * (3 - r) / 3 * pulse)
            _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["eye_mid"], alpha), (ex, ey), r)
        pygame.draw.rect(surface, _NS_zorashi.PALETTE["eye_light"], (ex, ey, 1, 1))
        pygame.draw.rect(surface, _NS_zorashi.PALETTE["eye_glow"], (ex, ey, 1, 1))
        # FANGS at snout
        fang_x = int(cx + cos_a * 7 * s)
        fang_y = int(cy + sin_a * 7 * s) + 1
        # Perpendicular for two fangs
        pygame.draw.line(surface, _NS_zorashi.PALETTE["fang_dark"],
                         (fang_x - 1, fang_y), (fang_x - 1, fang_y + int(3 * s)), 1)
        pygame.draw.line(surface, _NS_zorashi.PALETTE["fang_light"],
                         (fang_x - 1, fang_y), (fang_x - 1, fang_y + int(3 * s)), 1)
        pygame.draw.line(surface, _NS_zorashi.PALETTE["fang_dark"],
                         (fang_x + 1, fang_y), (fang_x + 1, fang_y + int(3 * s)), 1)
        pygame.draw.line(surface, _NS_zorashi.PALETTE["fang_light"],
                         (fang_x + 1, fang_y), (fang_x + 1, fang_y + int(3 * s)), 1)
        # Forked tongue (occasional)
        if math.sin(phase * 3) > 0.3:
            tongue_len = int(6 * s)
            tongue_x = int(cx + cos_a * (8 + tongue_len) * s)
            tongue_y = int(cy + sin_a * (8 + tongue_len) * s)
            pygame.draw.line(surface, _NS_zorashi.PALETTE["serpent_light"],
                             (fang_x, fang_y - 1), (tongue_x, tongue_y - 1), 1)
            # Fork
            pygame.draw.line(surface, _NS_zorashi.PALETTE["serpent_light"],
                             (tongue_x, tongue_y - 1),
                             (tongue_x + 2, tongue_y - 3), 1)
            pygame.draw.line(surface, _NS_zorashi.PALETTE["serpent_light"],
                             (tongue_x, tongue_y - 1),
                             (tongue_x + 2, tongue_y + 1), 1)
    # ============================================================
    # AUTO-ATTACK PROJECTILE (purple snake bolt)
    # ============================================================
    def _draw_venom_projectile(surface, boss, x, y, progress):
        """Purple snake-shaped projectile."""
        facing = boss.direction
        hand_x = x + facing * 24
        hand_y = y - 4
        if progress < 0.35:
            # Charge
            t = progress / 0.35
            cr = int(3 + t * 7)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_zorashi._alpha(200 * (cr + 3 - r) / (cr + 3) * t)
                _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["serpent_dark"], alpha),
                                      (hand_x, hand_y), r)
            _NS_zorashi._aacircle(surface, _NS_zorashi.PALETTE["serpent_mid"], (hand_x, hand_y),
                                  max(1, cr - 2))
            _NS_zorashi._aacircle(surface, _NS_zorashi.PALETTE["serpent_light"], (hand_x, hand_y),
                                  max(1, cr - 4))
            for i in range(4):
                angle = progress * 20 + i * math.pi / 2
                sx = hand_x + int(math.cos(angle) * (cr + 2))
                sy = hand_y + int(math.sin(angle) * (cr + 2))
                pygame.draw.rect(surface, _NS_zorashi.PALETTE["serpent_hot"], (sx, sy, 1, 1))
            return
        if progress < 0.55:
            return
        tx, ty = _NS_zorashi._target_position(boss, x, y)
        start_x = hand_x + facing * 4
        start_y = hand_y
        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        angle = math.atan2(ty - start_y, tx - start_x)
        # Purple energy trail (snake-like)
        for i in range(10):
            trail_t = max(0.0, t - i * 0.045)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            # Wavy offset (snake)
            perp = angle + math.pi / 2
            wave = math.sin(trail_t * 20 + i) * 4 * (1 - i / 10)
            px += int(math.cos(perp) * wave)
            py += int(math.sin(perp) * wave)
            alpha = _NS_zorashi._alpha(230 - i * 22)
            size = max(1, 7 - i)
            _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["serpent_darkest"], alpha),
                                  (px, py), size)
            _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["serpent_dark"], alpha),
                                  (px, py), max(1, size - 1))
            _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["serpent_mid"], alpha),
                                  (px, py), max(1, size - 2))
            _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["serpent_light"], alpha),
                                  (px, py), max(1, size - 3))
        # Head - small snake head
        _NS_zorashi._draw_serpent_head(surface, bx, by, angle, boss.pulse, size=0.7)
        # Impact
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(8 + st * 20)
            alpha = _NS_zorashi._alpha(240 * (1 - st))
            _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["serpent_dark"], alpha),
                                  (tx, ty), radius, 3)
            _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["serpent_mid"], alpha),
                                  (tx, ty), max(1, radius - 4), 2)
            _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["serpent_light"], alpha),
                                  (tx, ty), max(1, radius - 8), 1)
            for i in range(10):
                a_s = i * math.pi / 5
                ex = tx + int(math.cos(a_s) * radius)
                ey = ty + int(math.sin(a_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_zorashi.PALETTE["serpent_hot"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # FLOATING SMOKE BASE
    # ============================================================
    def _draw_smoke_base(surface, cx, cy, phase, intense=False, moving=False, facing=1):
        strength = 1.3 if intense else 1.0
        smoke = pygame.Surface((100, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(20, 3, -2):
            alpha = _NS_zorashi._alpha((20 - radius) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(smoke, (*_NS_zorashi.PALETTE["smoke_darkest"], alpha),
                    (50 - radius, 25 - radius // 2, radius * 2, max(3, radius)))
        for radius in range(14, 3, -2):
            alpha = _NS_zorashi._alpha((14 - radius) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(smoke, (*_NS_zorashi.PALETTE["smoke_dark"], alpha),
                    (50 - radius, 25 - radius // 2, radius * 2, max(2, radius)))
        surface.blit(smoke, (cx - 50, cy - 12))
        # Rising purple particles
        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            px = cx - 18 + i * 5 + int(math.sin(phase + i) * 3)
            py = cy + 12 - int(t * 22)
            alpha = _NS_zorashi._alpha(210 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_zorashi.PALETTE["serpent_mid"], alpha), (px, py, 1, 1))
                pygame.draw.rect(surface, (*_NS_zorashi.PALETTE["serpent_light"], alpha), (px, py, 1, 1))
        if moving:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + 8 + int(math.sin(phase + i) * 2)
                alpha = _NS_zorashi._alpha(160 - i * 30)
                if alpha <= 0:
                    continue
                _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["smoke_dark"], alpha),
                                      (sx, sy), max(2, 6 - i))
                pygame.draw.rect(surface, (*_NS_zorashi.PALETTE["serpent_light"], alpha),
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
        pygame.draw.ellipse(shadow, (10, 5, 20, 150), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (40, 20, 60, 90), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_serpent_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_zorashi._alpha((95 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_zorashi._aacircle(aura, (*_NS_zorashi.PALETTE["smoke_darkest"], alpha),
                                      (110, 100), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_zorashi._alpha((60 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_zorashi._aacircle(aura, (*_NS_zorashi.PALETTE["serpent_darkest"], alpha),
                                      (110, 100), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_zorashi._alpha((30 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_zorashi._aacircle(aura, (*_NS_zorashi.PALETTE["serpent_dark"], alpha),
                                      (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))
        # Floating purple embers
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 45 + int(math.sin(phase + i) * 14)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_zorashi.PALETTE["serpent_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_zorashi.PALETTE["serpent_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_zorashi.PALETTE["serpent_darkest"], 200),
                            (5, 20, 170, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_zorashi.PALETTE["serpent_dark"], 220),
                            (14, 22, 152, 24), 2)
        pygame.draw.ellipse(ring, (*_NS_zorashi.PALETTE["serpent_mid"], 180),
                            (25, 24, 130, 20), 1)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 34 + int(math.sin(angle) * 9)
            x2 = 90 + int(math.cos(angle) * 76)
            y2 = 34 + int(math.sin(angle) * 13)
            pygame.draw.line(ring, (*_NS_zorashi.PALETTE["serpent_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_zorashi.PALETTE["serpent_hot"],
                                       _NS_zorashi._alpha(150 * pulse)),
                                (15, 12, 150, 42), 1)
        surface.blit(ring, (x - 90, y - 30))
    # ============================================================
    # SKILL Q - VIPER FANG (enhanced snake projectile)
    # ============================================================
    def _draw_viperfang_skill(surface, boss, x, y, timer, phase):
        """Big snake head projectile with venom trail."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_zorashi._target_position(boss, x, y)
        hand_x = x + facing * 24
        hand_y = y - 4
        if progress < 0.2:
            # Charge
            t = progress / 0.2
            cr = int(4 + t * 12)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_zorashi._alpha(220 * (cr + 6 - r) / (cr + 6))
                _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["serpent_darkest"], alpha),
                                      (hand_x, hand_y), r)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_zorashi._alpha(220 * (cr + 3 - r) / (cr + 3))
                _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["serpent_dark"], alpha),
                                      (hand_x, hand_y), r)
            _NS_zorashi._aacircle(surface, _NS_zorashi.PALETTE["serpent_mid"], (hand_x, hand_y), cr - 2)
            _NS_zorashi._aacircle(surface, _NS_zorashi.PALETTE["serpent_light"], (hand_x, hand_y),
                                  max(1, cr - 5))
            _NS_zorashi._aacircle(surface, _NS_zorashi.PALETTE["serpent_shine"], (hand_x, hand_y),
                                  max(1, cr - 7))
            return
        # Flight
        t = (progress - 0.2) / 0.8
        t = min(1.0, t)
        start_x = hand_x + facing * 6
        start_y = hand_y
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        angle = math.atan2(ty - start_y, tx - start_x)
        # Serpent-shaped trail (wavy body)
        for i in range(12):
            trail_t = max(0.0, t - i * 0.035)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            perp = angle + math.pi / 2
            wave = math.sin(trail_t * 25 + i) * 5 * (1 - i / 12)
            px += int(math.cos(perp) * wave)
            py += int(math.sin(perp) * wave)
            alpha = _NS_zorashi._alpha(240 - i * 18)
            size = max(2, 9 - i)
            _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["serpent_darkest"], alpha),
                                  (px, py), size)
            _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["serpent_dark"], alpha),
                                  (px, py), max(1, size - 1))
            _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["scale_mid"], alpha),
                                  (px, py - 1), max(1, size - 3))
            # Scale detail
            if i % 2 == 0 and size > 2:
                pygame.draw.rect(surface, (*_NS_zorashi.PALETTE["scale_light"], alpha),
                                 (px, py - 1, 1, 1))
        # Big snake head at front
        _NS_zorashi._draw_serpent_head(surface, bx, by, angle, phase, size=1.2)
        # Impact
        if t > 0.9:
            st = (t - 0.9) / 0.1
            radius = int(12 + st * 22)
            alpha = _NS_zorashi._alpha(240 * (1 - st))
            _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["serpent_dark"], alpha),
                                  (tx, ty), radius, 3)
            _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["serpent_mid"], alpha),
                                  (tx, ty), max(1, radius - 5), 2)
            _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["serpent_light"], alpha),
                                  (tx, ty), max(1, radius - 10), 1)
            for i in range(12):
                a_s = i * math.pi / 6
                ex = tx + int(math.cos(a_s) * radius)
                ey = ty + int(math.sin(a_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_zorashi.PALETTE["serpent_hot"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # SKILL W - SUMMON SERPENT (massive snake)
    # ============================================================
    def _draw_summon_ground(surface, boss, x, y, timer, phase):
        """Ground erupts where serpent will rise."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Line in front of boss
        for i in range(5):
            gx = x + facing * (30 + i * 30)
            gy = y + 46
            r = int(15 * min(1.0, progress * 2))
            if r > 2:
                pygame.draw.ellipse(surface, (*_NS_zorashi.PALETTE["serpent_darkest"], 200),
                                    (gx - r, gy - r // 3, r * 2, r * 2 // 3))
                pygame.draw.ellipse(surface, (*_NS_zorashi.PALETTE["serpent_dark"], 220),
                                    (gx - r + 2, gy - r // 3 + 1,
                                     r * 2 - 4, r * 2 // 3 - 2))
                pygame.draw.ellipse(surface, (*_NS_zorashi.PALETTE["serpent_mid"], 180),
                                    (gx - r + 4, gy - r // 3 + 2,
                                     r * 2 - 8, r * 2 // 3 - 4))
    def _draw_summon_foreground(surface, boss, x, y, timer, phase):
        """Massive purple serpent rising and striking forward."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.2:
            return
        # Serpent rises from ground, curves upward and forward
        rise_t = min(1.0, (progress - 0.2) / 0.8)
        # Serpent body: undulating curve from ground to head striking forward
        num_segs = 14
        base_x = x + facing * 30
        base_y = y + 46
        points = []
        for i in range(num_segs + 1):
            t = i / num_segs
            # Path: rises from ground, then arcs forward
            # Vertical rise up initially, then forward
            forward_dist = t * 140 * rise_t
            height_curve = math.sin(t * math.pi) * 40 * rise_t
            wave = math.sin(t * math.pi * 3 + phase * 2) * 6 * rise_t
            px = int(base_x + facing * forward_dist)
            py = int(base_y - height_curve + wave)
            points.append((px, py))
        # Draw serpent body (thick)
        for i in range(len(points) - 1):
            thickness = max(6, 18 - i)
            _NS_zorashi._aaline(surface, _NS_zorashi.PALETTE["shadow_deep"],
                    (points[i][0] + 2, points[i][1] + 2),
                    (points[i + 1][0] + 2, points[i + 1][1] + 2),
                    thickness + 2)
            _NS_zorashi._aaline(surface, _NS_zorashi.PALETTE["serpent_darkest"],
                    points[i], points[i + 1], thickness)
            _NS_zorashi._aaline(surface, _NS_zorashi.PALETTE["serpent_dark"],
                    points[i], points[i + 1], max(1, thickness - 2))
            _NS_zorashi._aaline(surface, _NS_zorashi.PALETTE["scale_dark"],
                    (points[i][0], points[i][1] - 1),
                    (points[i + 1][0], points[i + 1][1] - 1),
                    max(1, thickness - 4))
            _NS_zorashi._aaline(surface, _NS_zorashi.PALETTE["scale_mid"],
                    (points[i][0], points[i][1] - 2),
                    (points[i + 1][0], points[i + 1][1] - 2),
                    max(1, thickness - 6))
            _NS_zorashi._aaline(surface, _NS_zorashi.PALETTE["scale_light"],
                    (points[i][0], points[i][1] - 3),
                    (points[i + 1][0], points[i + 1][1] - 3),
                    max(1, thickness - 9))
            # Belly bottom
            _NS_zorashi._aaline(surface, _NS_zorashi.PALETTE["belly_dark"],
                    (points[i][0], points[i][1] + 2),
                    (points[i + 1][0], points[i + 1][1] + 2),
                    max(1, thickness - 6))
            _NS_zorashi._aaline(surface, _NS_zorashi.PALETTE["belly_mid"],
                    (points[i][0], points[i][1] + 3),
                    (points[i + 1][0], points[i + 1][1] + 3),
                    max(1, thickness - 8))
        # Scale patterns
        for i in range(2, len(points) - 2, 2):
            p = points[i]
            for dx in (-3, 0, 3):
                pygame.draw.rect(surface, _NS_zorashi.PALETTE["serpent_darkest"],
                                 (p[0] + dx, p[1], 2, 1))
                pygame.draw.rect(surface, _NS_zorashi.PALETTE["serpent_mid"],
                                 (p[0] + dx, p[1] + 1, 1, 1))
        # HEAD at end (facing forward, mouth open)
        if len(points) > 1:
            head = points[-1]
            prev = points[-2]
            head_angle = math.atan2(head[1] - prev[1], head[0] - prev[0])
            # Bigger head with open mouth
            _NS_zorashi._draw_big_serpent_head(surface, head[0], head[1] - 5,
                                                head_angle, phase, size=2.0,
                                                mouth_open=True)
    def _draw_big_serpent_head(surface, cx, cy, angle, phase, size=1.0, mouth_open=False):
        """Bigger snake head, optionally with open mouth."""
        # Draw main head shape (bigger)
        _NS_zorashi._draw_serpent_head(surface, cx, cy, angle, phase, size=size)
        # If mouth open, draw big fangs and mouth cavity
        if mouth_open:
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            # Mouth opening (dark cavity below snout)
            mouth_x = int(cx + cos_a * 5 * size)
            mouth_y = int(cy + sin_a * 5 * size + 3 * size)
            for r in range(int(6 * size), 0, -1):
                alpha = _NS_zorashi._alpha(220 * (6 - r) / 6)
                _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["shadow"], alpha),
                                      (mouth_x, mouth_y), r)
            # Big fangs
            for side in (-1, 1):
                fx = int(cx + cos_a * 6 * size + side * -sin_a * 2 * size)
                fy = int(cy + sin_a * 6 * size + side * cos_a * 2 * size + 1)
                fang_tip_x = fx
                fang_tip_y = fy + int(6 * size)
                pygame.draw.line(surface, _NS_zorashi.PALETTE["fang_dark"],
                                 (fx, fy), (fang_tip_x, fang_tip_y), 3)
                pygame.draw.line(surface, _NS_zorashi.PALETTE["fang_light"],
                                 (fx, fy), (fang_tip_x, fang_tip_y), 2)
                pygame.draw.rect(surface, _NS_zorashi.PALETTE["fang_light"],
                                 (fang_tip_x - 1, fang_tip_y, 1, 1))
    # ============================================================
    # SKILL E - POISON SPRAY (cone venom)
    # ============================================================
    def _draw_venom_skill(surface, boss, x, y, timer, phase):
        """Green venom cone spray from mouth/hand."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        origin_x = x + facing * 24
        origin_y = y - 4
        # Cone parameters
        max_range = 150
        cone_angle = 0.5  # radians (half-cone width)
        # Cone expands during animation
        cur_range = int(max_range * min(1.0, progress * 1.5))
        # Draw layered cone
        for layer_i, (radius_offset, alpha_val) in enumerate([
            (10, 60), (5, 100), (0, 150), (-5, 200), (-8, 240)
        ]):
            colors = [
                _NS_zorashi.PALETTE["venom_darkest"],
                _NS_zorashi.PALETTE["venom_dark"],
                _NS_zorashi.PALETTE["venom_mid"],
                _NS_zorashi.PALETTE["venom_light"],
                _NS_zorashi.PALETTE["venom_hot"],
            ]
            color = colors[min(layer_i, 4)]
            # Cone points
            end_x = origin_x + facing * (cur_range - radius_offset)
            cone_r = int((cur_range - radius_offset) * math.tan(cone_angle))
            if cone_r <= 0:
                continue
            perp_angle = math.pi / 2
            # Cone shape: tip at origin, spreading to end
            pts = [
                (origin_x, origin_y),
                (end_x, origin_y - cone_r),
                (end_x, origin_y + cone_r),
            ]
            _NS_zorashi._poly(surface, (*color, alpha_val), pts)
        # Toxic bubbles floating in cone
        for i in range(15):
            bubble_t = ((phase * 1.5 + i * 0.06) % 1.0)
            bubble_dist = int(bubble_t * cur_range)
            spread = int(math.sin(phase * 2 + i) * bubble_dist * math.tan(cone_angle) * 0.7)
            bx = origin_x + facing * bubble_dist
            by = origin_y + spread
            alpha = _NS_zorashi._alpha(240 * (1 - bubble_t * 0.5))
            size = 2 + int(bubble_t * 3)
            _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["venom_dark"], alpha),
                                  (bx, by), size)
            _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["venom_mid"], alpha),
                                  (bx, by), max(1, size - 1))
            _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["venom_light"], alpha),
                                  (bx, by), max(1, size - 2))
            pygame.draw.rect(surface, (*_NS_zorashi.PALETTE["venom_hot"], alpha), (bx, by, 1, 1))
        # Green glow at origin
        pulse = math.sin(phase * 4) * 0.3 + 0.7
        for r in range(10, 0, -1):
            alpha = _NS_zorashi._alpha(180 * (10 - r) / 10 * pulse)
            _NS_zorashi._aacircle(surface, (*_NS_zorashi.PALETTE["venom_mid"], alpha),
                                  (origin_x, origin_y), r)
        _NS_zorashi._aacircle(surface, _NS_zorashi.PALETTE["venom_hot"], (origin_x, origin_y), 3)
        pygame.draw.rect(surface, _NS_zorashi.PALETTE["venom_shine"], (origin_x, origin_y, 1, 1))
    # ============================================================
    # SKILL R - HYDRA REBIRTH (multiple serpents)
    # ============================================================
    def _draw_hydra_ground(surface, boss, x, y, timer, phase):
        """Ground portals for hydra summoning."""
        facing = boss.direction
        duration = 130
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # 4 spawn points spreading out
        for i in range(4):
            offset = 30 + i * 30
            gx = x + facing * offset
            gy = y + 46
            r = int(18 * min(1.0, progress * 2))
            if r > 2:
                pygame.draw.ellipse(surface, _NS_zorashi.PALETTE["shadow"],
                                    (gx - r - 1, gy - r // 3 - 1,
                                     r * 2 + 2, r * 2 // 3 + 2))
                pygame.draw.ellipse(surface, _NS_zorashi.PALETTE["serpent_darkest"],
                                    (gx - r, gy - r // 3, r * 2, r * 2 // 3))
                pygame.draw.ellipse(surface, _NS_zorashi.PALETTE["serpent_dark"],
                                    (gx - r + 2, gy - r // 3 + 1,
                                     r * 2 - 4, r * 2 // 3 - 2))
                # Rotating rune
                for j in range(6):
                    angle = phase * 2 + j * math.pi / 3
                    px = gx + int(math.cos(angle) * r)
                    py = gy + int(math.sin(angle) * r * 0.4)
                    pygame.draw.rect(surface, _NS_zorashi.PALETTE["serpent_light"], (px, py, 2, 2))
    def _draw_hydra_foreground(surface, boss, x, y, timer, phase):
        """Multiple serpents rising from ground."""
        facing = boss.direction
        duration = 130
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            return
        rise_t = min(1.0, (progress - 0.3) / 0.7)
        # 4 serpents each with different height
        for i in range(4):
            offset = 30 + i * 30
            base_x = x + facing * offset
            base_y = y + 46
            heights = [40, 55, 45, 60]  # varied heights
            max_h = heights[i]
            # Simple curved serpent rising
            num_segs = 10
            points = []
            for j in range(num_segs + 1):
                t = j / num_segs
                # Vertical rise with slight S-curve
                wave = math.sin(t * math.pi * 2 + phase * 2 + i) * 6 * rise_t
                px = int(base_x + wave)
                py = int(base_y - t * max_h * rise_t)
                points.append((px, py))
            # Draw serpent body
            for j in range(len(points) - 1):
                thickness = max(3, 8 - j // 2)
                _NS_zorashi._aaline(surface, _NS_zorashi.PALETTE["shadow_deep"],
                        (points[j][0] + 1, points[j][1] + 1),
                        (points[j + 1][0] + 1, points[j + 1][1] + 1),
                        thickness + 1)
                _NS_zorashi._aaline(surface, _NS_zorashi.PALETTE["serpent_darkest"],
                        points[j], points[j + 1], thickness)
                _NS_zorashi._aaline(surface, _NS_zorashi.PALETTE["serpent_dark"],
                        points[j], points[j + 1], max(1, thickness - 1))
                _NS_zorashi._aaline(surface, _NS_zorashi.PALETTE["scale_mid"],
                        (points[j][0], points[j][1] - 1),
                        (points[j + 1][0], points[j + 1][1] - 1),
                        max(1, thickness - 3))
                _NS_zorashi._aaline(surface, _NS_zorashi.PALETTE["scale_light"],
                        (points[j][0], points[j][1] - 2),
                        (points[j + 1][0], points[j + 1][1] - 2),
                        max(1, thickness - 5))
            # Head at top
            if len(points) > 1:
                head = points[-1]
                prev = points[-2]
                head_angle = math.atan2(head[1] - prev[1], head[0] - prev[0]) + math.pi / 2
                if facing < 0:
                    head_angle = math.pi - head_angle
                _NS_zorashi._draw_serpent_head(surface, head[0], head[1],
                                                math.atan2(0, facing), phase + i, size=0.9)



# ====================================================================
# DEIDARA (EXPLOSIVE ARTIST) - TRUE BOSS
# ====================================================================

class _NS_deidara:
    """Namespace deidara - Explosive clay art boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin tones
        "skin_shadow": (140, 105, 80),
        "skin_dark": (200, 160, 125),
        "skin_mid": (235, 195, 155),
        "skin_light": (250, 220, 185),
        "skin_shine": (255, 240, 215),
        # Blonde hair
        "hair_darkest": (90, 60, 15),
        "hair_dark": (160, 115, 30),
        "hair_mid": (220, 175, 55),
        "hair_light": (250, 215, 100),
        "hair_shine": (255, 245, 170),
        # Akatsuki cloak (black with red clouds)
        "cloak_darkest": (5, 5, 8),
        "cloak_dark": (18, 18, 24),
        "cloak_mid": (40, 40, 50),
        "cloak_light": (70, 70, 85),
        "cloak_edge": (100, 100, 120),
        # Red cloud emblem
        "cloud_darkest": (60, 5, 8),
        "cloud_dark": (130, 15, 20),
        "cloud_mid": (200, 30, 35),
        "cloud_light": (250, 70, 60),
        "cloud_shine": (255, 150, 130),
        # Headband metal
        "metal_dark": (60, 60, 70),
        "metal_mid": (140, 140, 155),
        "metal_light": (210, 210, 220),
        "metal_shine": (255, 255, 255),
        # Clay (white/grey)
        "clay_darkest": (80, 78, 72),
        "clay_dark": (140, 135, 125),
        "clay_mid": (200, 195, 180),
        "clay_light": (235, 230, 215),
        "clay_shine": (255, 252, 240),
        # Explosion (orange/yellow/red)
        "expl_darkest": (60, 15, 5),
        "expl_dark": (150, 40, 10),
        "expl_mid": (240, 110, 20),
        "expl_hot": (255, 180, 40),
        "expl_bright": (255, 230, 120),
        "expl_shine": (255, 255, 220),
        # Smoke
        "smoke_dark": (40, 35, 30),
        "smoke_mid": (100, 95, 90),
        "smoke_light": (170, 165, 160),
        # Eye (blue)
        "eye_dark": (10, 30, 80),
        "eye_mid": (40, 100, 200),
        "eye_light": (120, 180, 255),
        "eye_shine": (220, 240, 255),
        # Scope (Deidara's eye scope - mechanical)
        "scope_dark": (30, 25, 20),
        "scope_mid": (90, 80, 65),
        "scope_light": (180, 160, 130),
        "scope_glow": (255, 100, 40),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_deidara._clamp(color)
        if _NS_deidara.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_deidara._clamp(color)
        if _NS_deidara.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_deidara._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_deidara(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_deidara._detect_moving(boss)
        _NS_deidara._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_dei_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind
        _NS_deidara._draw_explosive_aura(surface, x, y, pulse)
        _NS_deidara._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "w":
            _NS_deidara._draw_clone_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_deidara._draw_katsu_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating bob
        float_bob = int(math.sin(pulse * 0.6) * 3)
        # Body (always floating)
        if attacking:
            _NS_deidara._draw_body_attack(surface, boss, x, y + float_bob)
        elif moving:
            _NS_deidara._draw_body_walk(surface, boss, x, y + float_bob)
        else:
            _NS_deidara._draw_body_idle(surface, boss, x, y + float_bob)
        # Foreground FX
        if active_skill == "q":
            _NS_deidara._draw_micro_bomb_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_deidara._draw_clay_clone_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_deidara._draw_clay_bird_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_deidara._draw_katsu_skill(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_dei_previous_timer", 0))
        active = bool(getattr(boss, "_dei_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._dei_attack_active = True
            boss._dei_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._dei_attack_frame = int(getattr(boss, "_dei_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._dei_attack_active = False
            boss._dei_attack_frame = 0
            active = False
        boss._dei_previous_timer = timer
        boss._dei_attack_progress = (
            min(1.0, getattr(boss, "_dei_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_dei_last_x"):
            boss._dei_last_x = boss.x
            boss._dei_last_y = boss.y
            return False
        dx = abs(boss.x - boss._dei_last_x)
        dy = abs(boss.y - boss._dei_last_y)
        boss._dei_last_x = boss.x
        boss._dei_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        _NS_deidara._draw_shadow(surface, x, y + 50)
        _NS_deidara._draw_float_mist(surface, x, y + 44, boss.pulse)
        _NS_deidara._draw_body(surface, x, y, boss.direction, boss.pulse, "idle")
    def _draw_body_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_deidara._draw_shadow(surface, x + sway, y + 50)
        _NS_deidara._draw_float_mist(surface, x + sway, y + 44, phase, trail=True,
                                     facing=boss.direction)
        _NS_deidara._draw_body(surface, x + sway, y, boss.direction, phase, "walk")
    def _draw_body_attack(surface, boss, x, y):
        progress = getattr(boss, "_dei_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Throw motion: wind up → throw forward → recovery
        if progress < 0.4:
            t = progress / 0.4
            lunge = -int(t * 3) * boss.direction
        elif progress < 0.65:
            t = (progress - 0.4) / 0.25
            lunge = int((-3 + t * 10)) * boss.direction
        else:
            t = (progress - 0.65) / 0.35
            lunge = int(7 * (1 - t)) * boss.direction
        _NS_deidara._draw_shadow(surface, x + lunge, y + 50)
        _NS_deidara._draw_float_mist(surface, x + lunge, y + 44, boss.pulse, intense=True)
        _NS_deidara._draw_body(surface, x + lunge, y, boss.direction, boss.pulse,
                               "attack", progress)
        _NS_deidara._draw_basic_projectile(surface, boss, x + lunge, y, progress)
    # ============================================================
    # BODY DRAWING
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw humanoid ninja body: cloak, head, hair, arm posing."""
        # Layer order: back arm → cloak/body → front arm → head → hair
        arm_swing = 0
        if action == "attack":
            if attack_progress < 0.4:
                arm_swing = -int(attack_progress / 0.4 * 8) * facing
            elif attack_progress < 0.65:
                t = (attack_progress - 0.4) / 0.25
                arm_swing = int((-8 + t * 22)) * facing
            else:
                t = (attack_progress - 0.65) / 0.35
                arm_swing = int(14 * (1 - t)) * facing
        # Back arm (behind cloak)
        _NS_deidara._draw_arm(surface, cx - facing * 6, cy - 4, facing, phase,
                              -arm_swing // 2, back=True)
        # Cloak (main body)
        _NS_deidara._draw_cloak(surface, cx, cy, facing, phase, action)
        # Front arm (holding/throwing clay)
        _NS_deidara._draw_arm(surface, cx + facing * 4, cy - 4, facing, phase,
                              arm_swing, back=False, action=action,
                              attack_progress=attack_progress)
        # Head
        _NS_deidara._draw_head(surface, cx + facing * 2, cy - 22, facing, phase, action)
        # Hair (drawn after head)
        _NS_deidara._draw_hair(surface, cx + facing * 2, cy - 22, facing, phase)
    def _draw_cloak(surface, cx, cy, facing, phase, action):
        """Black Akatsuki cloak with red clouds."""
        sway = math.sin(phase * 0.7) * 1
        # Main cloak body (trapezoidal)
        cloak_shape = [
            (cx - 12, cy - 8),      # left shoulder
            (cx - 14, cy - 2),      # upper left
            (cx - 16, cy + 8),      # mid left
            (cx - 18, cy + 20),     # bottom left flare
            (cx - 14 + int(sway), cy + 28),  # bottom left tip
            (cx - 4, cy + 30),      # bottom mid-left
            (cx + 4, cy + 30),      # bottom mid-right
            (cx + 14 + int(sway), cy + 28),  # bottom right tip
            (cx + 18, cy + 20),     # bottom right flare
            (cx + 16, cy + 8),      # mid right
            (cx + 14, cy - 2),      # upper right
            (cx + 12, cy - 8),      # right shoulder
        ]
        # Shadow
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["shadow_deep"],
                          [(px + 2, py + 3) for px, py in cloak_shape])
        # Base darkest
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["cloak_darkest"], cloak_shape)
        # Mid tone (main visible cloak)
        cloak_inner = [
            (cx - 11, cy - 6),
            (cx - 13, cy - 1),
            (cx - 15, cy + 8),
            (cx - 16, cy + 18),
            (cx - 12, cy + 26),
            (cx + 12, cy + 26),
            (cx + 16, cy + 18),
            (cx + 15, cy + 8),
            (cx + 13, cy - 1),
            (cx + 11, cy - 6),
        ]
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["cloak_dark"], cloak_inner)
        # Highlight on chest
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["cloak_mid"], [
            (cx - 8, cy - 4),
            (cx - 10, cy + 4),
            (cx - 8, cy + 14),
            (cx + 8, cy + 14),
            (cx + 10, cy + 4),
            (cx + 8, cy - 4),
        ])
        # Center vertical opening (zipper line)
        pygame.draw.line(surface, _NS_deidara.PALETTE["cloak_darkest"],
                         (cx, cy - 6), (cx, cy + 26), 1)
        pygame.draw.line(surface, _NS_deidara.PALETTE["cloak_edge"],
                         (cx + 1, cy - 6), (cx + 1, cy + 26), 1)
        # Red cloud emblems (3 clouds on cloak)
        cloud_positions = [
            (cx - 8, cy + 2),
            (cx + 8, cy + 6),
            (cx - 4, cy + 16),
        ]
        for cpos in cloud_positions:
            _NS_deidara._draw_red_cloud(surface, cpos[0], cpos[1])
        # Collar (high stand-up collar)
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["cloak_darkest"], [
            (cx - 10, cy - 10),
            (cx - 12, cy - 6),
            (cx - 10, cy - 4),
            (cx + 10, cy - 4),
            (cx + 12, cy - 6),
            (cx + 10, cy - 10),
        ])
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["cloak_dark"], [
            (cx - 9, cy - 9),
            (cx - 11, cy - 6),
            (cx - 9, cy - 5),
            (cx + 9, cy - 5),
            (cx + 11, cy - 6),
            (cx + 9, cy - 9),
        ])
        # Collar highlight
        pygame.draw.line(surface, _NS_deidara.PALETTE["cloak_edge"],
                         (cx - 8, cy - 8), (cx + 8, cy - 8), 1)
        # Bottom edge highlight
        pygame.draw.line(surface, _NS_deidara.PALETTE["cloak_mid"],
                         (cx - 14, cy + 24), (cx + 14, cy + 24), 1)
    def _draw_red_cloud(surface, cx, cy):
        """Small red Akatsuki cloud emblem."""
        # Cloud shape - series of bumps
        # Shadow outline
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["cloud_darkest"], [
            (cx - 4, cy),
            (cx - 3, cy - 2),
            (cx - 1, cy - 3),
            (cx + 1, cy - 2),
            (cx + 3, cy - 3),
            (cx + 4, cy - 1),
            (cx + 4, cy + 1),
            (cx + 2, cy + 2),
            (cx - 2, cy + 2),
            (cx - 4, cy + 1),
        ])
        # Main red
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["cloud_mid"], [
            (cx - 3, cy),
            (cx - 2, cy - 1),
            (cx, cy - 2),
            (cx + 2, cy - 1),
            (cx + 3, cy),
            (cx + 2, cy + 1),
            (cx - 2, cy + 1),
        ])
        # Highlight
        pygame.draw.rect(surface, _NS_deidara.PALETTE["cloud_light"],
                         (cx - 1, cy - 1, 2, 1))
        pygame.draw.rect(surface, _NS_deidara.PALETTE["cloud_shine"],
                         (cx, cy - 1, 1, 1))
    def _draw_arm(surface, cx, cy, facing, phase, swing, back=False,
                  action="idle", attack_progress=0):
        """Draw arm with cloak sleeve."""
        depth = 0.7 if back else 1.0
        # Arm angle
        base_angle = math.pi * 0.5 + math.radians(swing)
        if back:
            base_angle = math.pi * 0.6
        # Shoulder to elbow
        shoulder_x = cx
        shoulder_y = cy
        elbow_len = 10
        elbow_x = shoulder_x + int(math.cos(base_angle) * elbow_len * facing * 0.3)
        elbow_y = shoulder_y + int(math.sin(base_angle) * elbow_len)
        # Elbow to hand
        hand_len = 12
        hand_angle = base_angle - math.radians(swing * 0.6)
        hand_x = elbow_x + int(math.cos(hand_angle) * hand_len * facing * 0.5)
        hand_y = elbow_y + int(math.sin(hand_angle) * hand_len)
        # If throwing, extend hand forward
        if action == "attack" and not back and attack_progress > 0.4:
            hand_x = cx + facing * (8 + int(attack_progress * 8))
            hand_y = cy + 2 - int(math.sin(attack_progress * math.pi) * 8)
        # Sleeve (dark cloak)
        thickness = 6 if not back else 5
        color_main = _NS_deidara.PALETTE["cloak_darkest"] if back \
            else _NS_deidara.PALETTE["cloak_dark"]
        color_mid = _NS_deidara.PALETTE["cloak_dark"] if back \
            else _NS_deidara.PALETTE["cloak_mid"]
        # Shadow
        _NS_deidara._aaline(surface, _NS_deidara.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 2),
                            (elbow_x + 1, elbow_y + 2), thickness + 1)
        # Upper arm
        _NS_deidara._aaline(surface, color_main,
                            (shoulder_x, shoulder_y),
                            (elbow_x, elbow_y), thickness)
        _NS_deidara._aaline(surface, color_mid,
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), max(1, thickness - 3))
        # Lower arm (forearm)
        _NS_deidara._aaline(surface, _NS_deidara.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 2),
                            (hand_x + 1, hand_y + 2), thickness)
        _NS_deidara._aaline(surface, color_main,
                            (elbow_x, elbow_y),
                            (hand_x, hand_y), thickness - 1)
        _NS_deidara._aaline(surface, color_mid,
                            (elbow_x, elbow_y - 1),
                            (hand_x, hand_y - 1), max(1, thickness - 3))
        # Cloak sleeve cuff (wider at hand)
        cuff_perp_x = -math.sin(hand_angle) * 3
        cuff_perp_y = math.cos(hand_angle) * 3
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["cloak_darkest"], [
            (hand_x - int(cuff_perp_x), hand_y - int(cuff_perp_y)),
            (hand_x + int(cuff_perp_x), hand_y + int(cuff_perp_y)),
            (hand_x + int(cuff_perp_x) - facing * 2,
             hand_y + int(cuff_perp_y) + 2),
            (hand_x - int(cuff_perp_x) - facing * 2,
             hand_y - int(cuff_perp_y) + 2),
        ])
        # Hand (skin visible from cuff)
        if not back:
            _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["shadow_deep"],
                                  (hand_x + 1, hand_y + 1), 3)
            _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["skin_shadow"],
                                  (hand_x, hand_y), 3)
            _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["skin_dark"],
                                  (hand_x, hand_y), 2)
            _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["skin_mid"],
                                  (hand_x - 1, hand_y - 1), 1)
            # Mouth on hand (Deidara's signature!)
            pygame.draw.rect(surface, _NS_deidara.PALETTE["shadow_deep"],
                             (hand_x - 1, hand_y, 3, 1))
            pygame.draw.rect(surface, _NS_deidara.PALETTE["cloud_darkest"],
                             (hand_x, hand_y, 2, 1))
            # Tongue peek if attacking
            if action == "attack" and attack_progress > 0.3:
                pygame.draw.rect(surface, _NS_deidara.PALETTE["cloud_mid"],
                                 (hand_x, hand_y, 1, 1))
    def _draw_head(surface, cx, cy, facing, phase, action):
        """Draw ninja head with headband."""
        # Face shape (rounded)
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
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["shadow_deep"],
                          [(px + 1, py + 2) for px, py in face_shape])
        # Base skin
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["skin_shadow"], face_shape)
        # Main face
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["skin_dark"], [
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
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["skin_mid"], [
            (cx - 4, cy - 4),
            (cx - 5, cy - 7),
            (cx - 3, cy - 9),
            (cx + 3, cy - 9),
            (cx + 5, cy - 7),
            (cx + 4, cy - 4),
            (cx + 2, cy),
            (cx - 2, cy),
        ])
        # Highlight (cheek)
        pygame.draw.rect(surface, _NS_deidara.PALETTE["skin_light"],
                         (cx - 3 * facing, cy - 4, 2, 2))
        pygame.draw.rect(surface, _NS_deidara.PALETTE["skin_shine"],
                         (cx - 3 * facing, cy - 4, 1, 1))
        # HEADBAND (Iwagakure - metal plate)
        _NS_deidara._draw_headband(surface, cx, cy - 8, facing)
        # Eyes
        _NS_deidara._draw_eye(surface, cx - 3 * facing, cy - 5, facing, phase, scope=True)
        _NS_deidara._draw_eye(surface, cx + 3 * facing, cy - 5, facing, phase, scope=False)
        # Mouth
        if action == "attack":
            # Open mouth (yelling "Katsu!")
            pygame.draw.rect(surface, _NS_deidara.PALETTE["shadow_deep"],
                             (cx - 2, cy + 1, 4, 2))
            pygame.draw.rect(surface, _NS_deidara.PALETTE["cloud_darkest"],
                             (cx - 1, cy + 1, 3, 2))
            pygame.draw.rect(surface, _NS_deidara.PALETTE["cloud_dark"],
                             (cx - 1, cy + 2, 3, 1))
        else:
            # Smug smirk
            pygame.draw.line(surface, _NS_deidara.PALETTE["shadow_deep"],
                             (cx - 2, cy + 2), (cx + 2, cy + 2), 1)
    def _draw_headband(surface, cx, cy, facing):
        """Iwagakure headband with slash mark."""
        # Cloth part (dark)
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["shadow_deep"], [
            (cx - 9, cy - 1),
            (cx - 10, cy + 2),
            (cx + 10, cy + 2),
            (cx + 9, cy - 1),
        ])
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["cloak_darkest"], [
            (cx - 8, cy),
            (cx - 9, cy + 2),
            (cx + 9, cy + 2),
            (cx + 8, cy),
        ])
        # Metal plate (Iwa symbol)
        pygame.draw.rect(surface, _NS_deidara.PALETTE["metal_dark"],
                         (cx - 6, cy, 13, 3))
        pygame.draw.rect(surface, _NS_deidara.PALETTE["metal_mid"],
                         (cx - 5, cy, 12, 3))
        pygame.draw.rect(surface, _NS_deidara.PALETTE["metal_light"],
                         (cx - 5, cy, 12, 1))
        pygame.draw.rect(surface, _NS_deidara.PALETTE["metal_shine"],
                         (cx - 4, cy, 8, 1))
        # Iwa symbol (a slash - rock village symbol)
        pygame.draw.line(surface, _NS_deidara.PALETTE["shadow_deep"],
                         (cx - 3, cy + 2), (cx + 4, cy), 1)
        pygame.draw.line(surface, _NS_deidara.PALETTE["metal_dark"],
                         (cx - 3, cy + 1), (cx + 4, cy - 1), 1)
        # Cloth tails hanging back
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["cloak_darkest"], [
            (cx - 8 * facing, cy + 1),
            (cx - 10 * facing, cy + 4),
            (cx - 11 * facing, cy + 8),
            (cx - 9 * facing, cy + 8),
            (cx - 8 * facing, cy + 4),
        ])
    def _draw_eye(surface, cx, cy, facing, phase, scope=False):
        """Draw eye - one has scope (mechanical)."""
        if scope:
            # Scope eye (Deidara's left eye scope)
            # Base dark socket
            pygame.draw.rect(surface, _NS_deidara.PALETTE["shadow_deep"],
                             (cx - 2, cy - 1, 4, 3))
            pygame.draw.rect(surface, _NS_deidara.PALETTE["scope_dark"],
                             (cx - 2, cy - 1, 4, 3))
            # Scope lens
            _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["scope_mid"],
                                  (cx, cy), 2)
            _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["scope_dark"],
                                  (cx, cy), 1)
            # Scope glow (mechanical eye)
            glow = math.sin(phase * 2) * 0.5 + 0.5
            alpha = _NS_deidara._alpha(200 + glow * 55)
            pygame.draw.rect(surface, _NS_deidara.PALETTE["scope_glow"],
                             (cx, cy, 1, 1))
            # Scope frame highlight
            pygame.draw.rect(surface, _NS_deidara.PALETTE["metal_light"],
                             (cx - 2, cy - 1, 1, 1))
        else:
            # Normal blue eye
            pygame.draw.rect(surface, _NS_deidara.PALETTE["shadow_deep"],
                             (cx - 1, cy - 1, 3, 2))
            pygame.draw.rect(surface, _NS_deidara.PALETTE["white"],
                             (cx - 1, cy, 3, 1))
            # Pupil/iris
            pygame.draw.rect(surface, _NS_deidara.PALETTE["eye_dark"],
                             (cx, cy, 2, 1))
            pygame.draw.rect(surface, _NS_deidara.PALETTE["eye_mid"],
                             (cx + facing, cy, 1, 1))
            # Highlight
            pygame.draw.rect(surface, _NS_deidara.PALETTE["eye_shine"],
                             (cx, cy - 1, 1, 1))
    def _draw_hair(surface, cx, cy, facing, phase):
        """Blonde hair - long tied ponytail with front bangs covering one eye."""
        # Back top hair (crown)
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["shadow_deep"], [
            (cx - 8, cy - 8),
            (cx - 6, cy - 13),
            (cx - 2, cy - 15),
            (cx + 3, cy - 15),
            (cx + 7, cy - 13),
            (cx + 9, cy - 8),
            (cx + 8, cy - 6),
            (cx - 8, cy - 6),
        ])
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["hair_darkest"], [
            (cx - 8, cy - 8),
            (cx - 6, cy - 13),
            (cx - 2, cy - 14),
            (cx + 3, cy - 14),
            (cx + 7, cy - 12),
            (cx + 8, cy - 7),
        ])
        # Main hair color (blonde dark)
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["hair_dark"], [
            (cx - 7, cy - 9),
            (cx - 5, cy - 12),
            (cx - 1, cy - 13),
            (cx + 3, cy - 13),
            (cx + 6, cy - 11),
            (cx + 7, cy - 8),
        ])
        # Highlight (blonde mid)
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["hair_mid"], [
            (cx - 5, cy - 10),
            (cx - 3, cy - 12),
            (cx + 2, cy - 12),
            (cx + 5, cy - 10),
            (cx + 4, cy - 8),
            (cx - 3, cy - 8),
        ])
        # Bright shine spot
        pygame.draw.line(surface, _NS_deidara.PALETTE["hair_light"],
                         (cx - 2, cy - 11), (cx + 2, cy - 11), 1)
        pygame.draw.rect(surface, _NS_deidara.PALETTE["hair_shine"],
                         (cx, cy - 11, 1, 1))
        # Front bangs (covering scope eye)
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["hair_darkest"], [
            (cx - 5 * facing, cy - 10),
            (cx - 7 * facing, cy - 6),
            (cx - 6 * facing, cy - 3),
            (cx - 3 * facing, cy - 4),
            (cx - 2 * facing, cy - 8),
        ])
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["hair_dark"], [
            (cx - 4 * facing, cy - 9),
            (cx - 6 * facing, cy - 5),
            (cx - 4 * facing, cy - 4),
            (cx - 2 * facing, cy - 7),
        ])
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["hair_mid"], [
            (cx - 3 * facing, cy - 8),
            (cx - 5 * facing, cy - 5),
            (cx - 3 * facing, cy - 5),
        ])
        # PONYTAIL (long, tied at back, flowing up)
        pony_sway = math.sin(phase * 0.8) * 3
        pony_base_x = cx - facing * 3
        pony_base_y = cy - 10
        # Draw ponytail as long strands going up-back
        for i, (dx, dy_off) in enumerate([
            (-3, -4), (-4, -8), (-5, -12), (-6, -16), (-7, -20),
        ]):
            actual_dx = dx * facing + int(pony_sway * (i + 1) / 5)
            end_x = pony_base_x + actual_dx
            end_y = pony_base_y + dy_off
            start_x = pony_base_x + int(actual_dx * 0.6)
            start_y = pony_base_y + int(dy_off * 0.6)
            thickness = max(2, 6 - i)
            _NS_deidara._aaline(surface, _NS_deidara.PALETTE["hair_darkest"],
                                (start_x + 1, start_y + 1),
                                (end_x + 1, end_y + 1), thickness + 1)
            _NS_deidara._aaline(surface, _NS_deidara.PALETTE["hair_dark"],
                                (start_x, start_y), (end_x, end_y), thickness)
            _NS_deidara._aaline(surface, _NS_deidara.PALETTE["hair_mid"],
                                (start_x, start_y - 1), (end_x, end_y - 1),
                                max(1, thickness - 2))
            _NS_deidara._aaline(surface, _NS_deidara.PALETTE["hair_light"],
                                (start_x, start_y - 2), (end_x, end_y - 2),
                                max(1, thickness - 4))
        # Hair tie
        pygame.draw.rect(surface, _NS_deidara.PALETTE["cloak_darkest"],
                         (pony_base_x - facing * 4, pony_base_y - 3, 3, 2))
        pygame.draw.rect(surface, _NS_deidara.PALETTE["cloak_dark"],
                         (pony_base_x - facing * 4, pony_base_y - 3, 3, 1))
    # ============================================================
    # BASIC PROJECTILE (Small clay bird - auto attack)
    # ============================================================
    def _draw_basic_projectile(surface, boss, x, y, progress):
        """Small clay bird projectile for basic attack."""
        if progress < 0.5:
            return
        facing = boss.direction
        tx, ty = _NS_deidara._target_position(boss, x, y)
        start_x = x + facing * 14
        start_y = y - 4
        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Trail
        for i in range(6):
            trail_t = max(0.0, t - i * 0.08)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_deidara._alpha(180 - i * 30)
            _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["clay_dark"], alpha),
                                  (px, py), max(1, 3 - i // 2))
        # Small clay bird
        _NS_deidara._draw_mini_clay_bird(surface, bx, by, facing, t * 8)
        # Impact
        if t > 0.9:
            st = (t - 0.9) / 0.1
            radius = int(6 + st * 15)
            alpha = _NS_deidara._alpha(240 * (1 - st))
            _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_hot"], alpha),
                                  (tx, ty), radius)
            _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_bright"], alpha),
                                  (tx, ty), max(1, radius - 4))
            _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_shine"], alpha),
                                  (tx, ty), max(1, radius - 8))
    def _draw_mini_clay_bird(surface, cx, cy, facing, wing_phase):
        """Small clay bird sprite for projectile."""
        wing_beat = math.sin(wing_phase) * 2
        # Body
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["shadow_deep"],
                              (cx + 1, cy + 1), 4)
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_darkest"], (cx, cy), 4)
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_dark"], (cx, cy), 3)
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_mid"], (cx, cy - 1), 2)
        pygame.draw.rect(surface, _NS_deidara.PALETTE["clay_light"], (cx, cy - 1, 1, 1))
        # Beak
        pygame.draw.line(surface, _NS_deidara.PALETTE["clay_darkest"],
                         (cx + facing * 3, cy),
                         (cx + facing * 5, cy), 1)
        pygame.draw.rect(surface, _NS_deidara.PALETTE["expl_dark"],
                         (cx + facing * 4, cy, 1, 1))
        # Wings
        wing_y = cy - 2 + int(wing_beat)
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_darkest"], [
            (cx, cy - 1),
            (cx - facing * 3, wing_y - 2),
            (cx - facing * 1, cy),
        ])
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_darkest"], [
            (cx, cy - 1),
            (cx + facing * 3, wing_y - 2),
            (cx + facing * 1, cy),
        ])
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_dark"], [
            (cx, cy - 1),
            (cx - facing * 2, wing_y - 1),
            (cx, cy),
        ])
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_dark"], [
            (cx, cy - 1),
            (cx + facing * 2, wing_y - 1),
            (cx, cy),
        ])
        # Tail
        pygame.draw.line(surface, _NS_deidara.PALETTE["clay_dark"],
                         (cx - facing * 3, cy),
                         (cx - facing * 5, cy + 1), 2)
    # ============================================================
    # FLOATING MIST (below body)
    # ============================================================
    def _draw_float_mist(surface, cx, cy, phase, trail=False, facing=1,
                         intense=False):
        """Chakra float mist below Deidara."""
        strength = 1.4 if intense else 1.0
        mist = pygame.Surface((100, 30), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        # Base cloudy chakra
        for radius in range(20, 3, -2):
            alpha = _NS_deidara._alpha((20 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_deidara.PALETTE["smoke_dark"], alpha),
                    (50 - radius, 15 - radius // 3,
                     radius * 2, max(2, radius // 2))
                )
        for radius in range(14, 2, -2):
            alpha = _NS_deidara._alpha((14 - radius) * 6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_deidara.PALETTE["smoke_light"], alpha),
                    (50 - radius, 15 - radius // 4,
                     radius * 2, max(2, radius // 3))
                )
        surface.blit(mist, (cx - 50, cy - 8))
        # Small floating particles rising
        for i in range(6):
            t = (phase * 0.5 + i * 0.16) % 1.0
            px = cx - 20 + i * 8 + int(math.sin(phase + i) * 3)
            py = cy + 4 - int(t * 20)
            alpha = _NS_deidara._alpha(200 * (1 - t) * strength)
            if alpha > 0:
                _NS_deidara._aacircle(surface,
                                      (*_NS_deidara.PALETTE["smoke_light"], alpha),
                                      (px, py), 2)
                pygame.draw.rect(surface, _NS_deidara.PALETTE["expl_bright"],
                                 (px, py, 1, 1))
        # Trail
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_deidara._alpha(140 - i * 25)
                if alpha > 0:
                    _NS_deidara._aacircle(surface,
                                          (*_NS_deidara.PALETTE["smoke_dark"], alpha),
                                          (sx, sy), max(1, 4 - i))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((120, 24), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 12 - radius, 100 + radius * 2, radius * 2)
            )
        pygame.draw.ellipse(shadow, (5, 3, 2, 160), (5, 6, 110, 12))
        pygame.draw.ellipse(shadow, (60, 20, 5, 100), (15, 8, 90, 8))
        surface.blit(shadow, (x - 60, y - 12))
    def _draw_explosive_aura(surface, x, y, phase):
        """Orange/red explosive aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(75, 5, -5):
            alpha = _NS_deidara._alpha((75 - radius) * 0.9 * pulse)
            if alpha > 0:
                _NS_deidara._aacircle(aura, (*_NS_deidara.PALETTE["expl_darkest"], alpha),
                                      (90, 80), radius)
        for radius in range(45, 5, -4):
            alpha = _NS_deidara._alpha((45 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_deidara._aacircle(aura, (*_NS_deidara.PALETTE["expl_dark"], alpha),
                                      (90, 80), radius)
        for radius in range(25, 5, -3):
            alpha = _NS_deidara._alpha((25 - radius) * 1.8 * pulse)
            if alpha > 0:
                _NS_deidara._aacircle(aura, (*_NS_deidara.PALETTE["expl_mid"], alpha),
                                      (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))
        # Floating embers
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            radius = 32 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.4)
            pygame.draw.rect(surface, _NS_deidara.PALETTE["expl_hot"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_deidara.PALETTE["expl_bright"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring beneath boss."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((150, 44), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_deidara.PALETTE["expl_darkest"], 200),
                            (5, 12, 140, 22), 3)
        pygame.draw.ellipse(ring, (*_NS_deidara.PALETTE["expl_dark"], 220),
                            (14, 14, 122, 18), 2)
        pygame.draw.ellipse(ring, (*_NS_deidara.PALETTE["expl_mid"], 200),
                            (25, 16, 100, 14), 1)
        # Runes
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 75 + int(math.cos(angle) * 38)
            y1 = 22 + int(math.sin(angle) * 6)
            x2 = 75 + int(math.cos(angle) * 62)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_deidara.PALETTE["expl_hot"], 200),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_deidara.PALETTE["expl_bright"],
                                       _NS_deidara._alpha(150 * pulse)),
                                (10, 8, 130, 30), 1)
        surface.blit(ring, (x - 75, y - 22))
    # ============================================================
    # SKILL Q - MICRO BOMB (small clay bird projectile)
    # ============================================================
    def _draw_micro_bomb_skill(surface, boss, x, y, timer, phase):
        """Small clay bird flies with explosion on impact."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_deidara._target_position(boss, x, y)
        if progress < 0.2:
            # Sculpt/charge in hand
            t = progress / 0.2
            hand_x = x + facing * 18
            hand_y = y - 6
            cr = int(3 + t * 5)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_deidara._alpha(180 * (cr + 3 - r) / (cr + 3))
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["clay_dark"], alpha),
                                      (hand_x, hand_y), r)
            _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_mid"],
                                  (hand_x, hand_y), max(1, cr - 2))
            _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_light"],
                                  (hand_x, hand_y), max(1, cr - 4))
            # Chakra sparks
            for i in range(4):
                angle = phase * 3 + i * math.pi / 2
                sx = hand_x + int(math.cos(angle) * (cr + 2))
                sy = hand_y + int(math.sin(angle) * (cr + 2))
                pygame.draw.rect(surface, _NS_deidara.PALETTE["expl_hot"], (sx, sy, 1, 1))
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 20
            start_y = y - 6
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Small smoke trail
            for i in range(7):
                trail_t = max(0.0, t - i * 0.06)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_deidara._alpha(180 - i * 25)
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["smoke_light"], alpha),
                                      (px, py), max(1, 4 - i // 2))
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["smoke_mid"], alpha),
                                      (px, py), max(1, 3 - i // 2))
            # Draw actual clay bird
            angle_travel = math.atan2(ty - start_y, tx - start_x)
            face_dir = 1 if math.cos(angle_travel) > 0 else -1
            _NS_deidara._draw_mini_clay_bird(surface, bx, by, face_dir, t * 12)
            # Impact
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(10 + st * 25)
                alpha = _NS_deidara._alpha(255 * (1 - st))
                # Big explosion
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_darkest"], alpha),
                                      (tx, ty), radius + 4)
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_dark"], alpha),
                                      (tx, ty), radius)
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_mid"], alpha),
                                      (tx, ty), max(1, radius - 5))
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_hot"], alpha),
                                      (tx, ty), max(1, radius - 10))
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_bright"], alpha),
                                      (tx, ty), max(1, radius - 15))
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_shine"], alpha),
                                      (tx, ty), max(1, radius // 4))
                # Radial burst
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius)
                    pygame.draw.line(surface,
                                     (*_NS_deidara.PALETTE["expl_bright"], alpha),
                                     (tx, ty), (ex, ey), 2)
    # ============================================================
    # SKILL W - CLAY CLONE
    # ============================================================
    def _draw_clone_ground(surface, boss, x, y, timer, phase):
        """Ground marker at clone position."""
        tx, ty = _NS_deidara._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(30 * min(1.0, progress * 2))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_deidara.PALETTE["expl_darkest"], 180),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_deidara.PALETTE["expl_dark"], 150),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 1)
    def _draw_clay_clone_skill(surface, boss, x, y, timer, pulse):
        """Draw clay clone at target position."""
        tx, ty = _NS_deidara._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.2:
            # Rising from ground
            t = progress / 0.2
            offset_y = int((1 - t) * 20)
            # Smoke around
            for i in range(8):
                angle = i * math.pi / 4
                sx = tx + int(math.cos(angle) * 12)
                sy = ty + int(math.sin(angle) * 6) - offset_y // 2
                alpha = _NS_deidara._alpha(200 * (1 - t))
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["smoke_light"], alpha),
                                      (sx, sy), 5)
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["smoke_mid"], alpha),
                                      (sx, sy), 3)
            _NS_deidara._draw_clay_clone_body(surface, tx, ty - offset_y,
                                              boss.direction, pulse, t)
        elif progress < 0.85:
            # Stable clone
            _NS_deidara._draw_clay_clone_body(surface, tx, ty, boss.direction, pulse, 1.0)
        else:
            # EXPLODES
            t = (progress - 0.85) / 0.15
            radius = int(15 + t * 40)
            alpha = _NS_deidara._alpha(255 * (1 - t))
            _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_darkest"], alpha),
                                  (tx, ty), radius + 5)
            _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_dark"], alpha),
                                  (tx, ty), radius)
            _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_mid"], alpha),
                                  (tx, ty), max(1, radius - 8))
            _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_hot"], alpha),
                                  (tx, ty), max(1, radius - 15))
            _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_bright"], alpha),
                                  (tx, ty), max(1, radius - 22))
            # Debris/rays
            for i in range(16):
                angle = i * math.pi / 8
                ex = tx + int(math.cos(angle) * radius * 1.2)
                ey = ty + int(math.sin(angle) * radius * 1.2)
                pygame.draw.line(surface,
                                 (*_NS_deidara.PALETTE["expl_bright"], alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface, _NS_deidara.PALETTE["expl_shine"],
                                 (ex, ey, 2, 2))
    def _draw_clay_clone_body(surface, cx, cy, facing, phase, scale):
        """Draw a clay clone (humanoid grey figure)."""
        # Simplified humanoid figure - clay grey
        # Body
        body_shape = [
            (cx - 10, cy - 5),
            (cx - 12, cy + 5),
            (cx - 10, cy + 22),
            (cx + 10, cy + 22),
            (cx + 12, cy + 5),
            (cx + 10, cy - 5),
        ]
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["shadow_deep"],
                          [(px + 1, py + 2) for px, py in body_shape])
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_darkest"], body_shape)
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_dark"], [
            (cx - 9, cy - 4),
            (cx - 10, cy + 5),
            (cx - 9, cy + 20),
            (cx + 9, cy + 20),
            (cx + 10, cy + 5),
            (cx + 9, cy - 4),
        ])
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_mid"], [
            (cx - 6, cy - 2),
            (cx - 8, cy + 8),
            (cx - 6, cy + 16),
            (cx + 6, cy + 16),
            (cx + 8, cy + 8),
            (cx + 6, cy - 2),
        ])
        # Highlight
        pygame.draw.line(surface, _NS_deidara.PALETTE["clay_light"],
                         (cx - 3, cy), (cx - 3, cy + 12), 1)
        pygame.draw.line(surface, _NS_deidara.PALETTE["clay_shine"],
                         (cx - 3, cy + 4), (cx - 3, cy + 8), 1)
        # Arms
        _NS_deidara._aaline(surface, _NS_deidara.PALETTE["clay_darkest"],
                            (cx - 10, cy - 2), (cx - 14, cy + 12), 4)
        _NS_deidara._aaline(surface, _NS_deidara.PALETTE["clay_dark"],
                            (cx - 10, cy - 2), (cx - 14, cy + 12), 3)
        _NS_deidara._aaline(surface, _NS_deidara.PALETTE["clay_mid"],
                            (cx - 10, cy - 2), (cx - 14, cy + 12), 1)
        _NS_deidara._aaline(surface, _NS_deidara.PALETTE["clay_darkest"],
                            (cx + 10, cy - 2), (cx + 14, cy + 12), 4)
        _NS_deidara._aaline(surface, _NS_deidara.PALETTE["clay_dark"],
                            (cx + 10, cy - 2), (cx + 14, cy + 12), 3)
        _NS_deidara._aaline(surface, _NS_deidara.PALETTE["clay_mid"],
                            (cx + 10, cy - 2), (cx + 14, cy + 12), 1)
        # Hand fists
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_darkest"],
                              (cx - 14, cy + 12), 3)
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_dark"],
                              (cx - 14, cy + 12), 2)
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_darkest"],
                              (cx + 14, cy + 12), 3)
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_dark"],
                              (cx + 14, cy + 12), 2)
        # Head
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["shadow_deep"],
                              (cx + 1, cy - 11), 8)
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_darkest"],
                              (cx, cy - 12), 8)
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_dark"],
                              (cx, cy - 12), 7)
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_mid"],
                              (cx - 1, cy - 13), 5)
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_light"],
                              (cx - 2, cy - 14), 2)
        pygame.draw.rect(surface, _NS_deidara.PALETTE["clay_shine"],
                         (cx - 2, cy - 15, 1, 1))
        # Dark eye sockets
        pygame.draw.rect(surface, _NS_deidara.PALETTE["shadow_deep"],
                         (cx - 3, cy - 12, 2, 2))
        pygame.draw.rect(surface, _NS_deidara.PALETTE["shadow_deep"],
                         (cx + 2, cy - 12, 2, 2))
        pygame.draw.rect(surface, _NS_deidara.PALETTE["expl_dark"],
                         (cx - 3, cy - 12, 1, 1))
        pygame.draw.rect(surface, _NS_deidara.PALETTE["expl_hot"],
                         (cx + 2, cy - 12, 1, 1))
        # Mouth (frown)
        pygame.draw.line(surface, _NS_deidara.PALETTE["shadow_deep"],
                         (cx - 2, cy - 8), (cx + 2, cy - 8), 1)
    # ============================================================
    # SKILL E - CLAY BIRD (large flying bird)
    # ============================================================
    def _draw_clay_bird_skill(surface, boss, x, y, timer, phase):
        """Large clay bird flies in straight line."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_deidara._target_position(boss, x, y)
        if progress < 0.15:
            # Summoning: smoke poof at start
            t = progress / 0.15
            for i in range(10):
                angle = i * math.pi / 5
                sx = x + facing * 30 + int(math.cos(angle) * 15 * t)
                sy = y - 8 + int(math.sin(angle) * 10 * t)
                alpha = _NS_deidara._alpha(230 * (1 - t))
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["smoke_light"], alpha),
                                      (sx, sy), 6)
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["smoke_mid"], alpha),
                                      (sx, sy), 4)
        else:
            t = (progress - 0.15) / 0.85
            start_x = x + facing * 30
            start_y = y - 8
            # Bird flies past target and continues
            end_x = tx + facing * 100
            bx = int(start_x + (end_x - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Trail
            for i in range(8):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (end_x - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_deidara._alpha(160 - i * 20)
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["smoke_light"], alpha),
                                      (px, py), max(1, 6 - i))
            # Draw large clay bird
            _NS_deidara._draw_large_clay_bird(surface, bx, by, facing, phase)
            # Detonation flash if past target
            if t > 0.65 and t < 0.85:
                dt = (t - 0.65) / 0.2
                radius = int(20 + dt * 45)
                alpha = _NS_deidara._alpha(230 * (1 - dt))
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_darkest"], alpha),
                                      (tx, ty), radius + 4)
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_dark"], alpha),
                                      (tx, ty), radius)
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_mid"], alpha),
                                      (tx, ty), max(1, radius - 8))
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_hot"], alpha),
                                      (tx, ty), max(1, radius - 16))
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_bright"], alpha),
                                      (tx, ty), max(1, radius - 24))
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_shine"], alpha),
                                      (tx, ty), max(1, radius // 5))
    def _draw_large_clay_bird(surface, cx, cy, facing, phase):
        """Big clay bird sprite (eagle-like)."""
        wing_beat = math.sin(phase * 2) * 4
        # Body (large oval)
        body_pts = [
            (cx - 12 * facing, cy),
            (cx - 10 * facing, cy - 4),
            (cx - 4 * facing, cy - 6),
            (cx + 6 * facing, cy - 5),
            (cx + 14 * facing, cy - 2),
            (cx + 16 * facing, cy),
            (cx + 14 * facing, cy + 3),
            (cx + 4 * facing, cy + 5),
            (cx - 6 * facing, cy + 4),
            (cx - 12 * facing, cy + 2),
        ]
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["shadow_deep"],
                          [(px + 2, py + 2) for px, py in body_pts])
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_darkest"], body_pts)
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_dark"], [
            (cx - 10 * facing, cy),
            (cx - 8 * facing, cy - 3),
            (cx + 4 * facing, cy - 5),
            (cx + 12 * facing, cy - 2),
            (cx + 14 * facing, cy),
            (cx + 12 * facing, cy + 2),
            (cx + 2 * facing, cy + 4),
            (cx - 8 * facing, cy + 3),
        ])
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_mid"], [
            (cx - 6 * facing, cy - 1),
            (cx - 4 * facing, cy - 3),
            (cx + 4 * facing, cy - 4),
            (cx + 8 * facing, cy - 2),
            (cx + 6 * facing, cy),
            (cx - 4 * facing, cy + 1),
        ])
        pygame.draw.line(surface, _NS_deidara.PALETTE["clay_light"],
                         (cx - 3 * facing, cy - 2), (cx + 4 * facing, cy - 2), 1)
        # Head
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_darkest"],
                              (cx + 14 * facing, cy - 4), 5)
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_dark"],
                              (cx + 14 * facing, cy - 4), 4)
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_mid"],
                              (cx + 14 * facing, cy - 5), 2)
        # Beak
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_darkest"], [
            (cx + 16 * facing, cy - 4),
            (cx + 22 * facing, cy - 3),
            (cx + 20 * facing, cy - 1),
            (cx + 16 * facing, cy - 2),
        ])
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_dark"], [
            (cx + 16 * facing, cy - 3),
            (cx + 21 * facing, cy - 2),
            (cx + 16 * facing, cy - 1),
        ])
        pygame.draw.rect(surface, _NS_deidara.PALETTE["expl_dark"],
                         (cx + 20 * facing, cy - 2, 1, 1))
        # Bird eye
        pygame.draw.rect(surface, _NS_deidara.PALETTE["shadow_deep"],
                         (cx + 13 * facing, cy - 5, 2, 2))
        pygame.draw.rect(surface, _NS_deidara.PALETTE["expl_hot"],
                         (cx + 14 * facing, cy - 5, 1, 1))
        # WINGS (large, spread)
        # Top wing (upper)
        top_wing_y = cy - 12 + int(wing_beat)
        wing_top = [
            (cx - 2 * facing, cy - 4),
            (cx - 12 * facing, top_wing_y),
            (cx - 22 * facing, top_wing_y + 2),
            (cx - 28 * facing, top_wing_y + 6),
            (cx - 24 * facing, cy - 4),
            (cx - 14 * facing, cy - 6),
        ]
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["shadow_deep"],
                          [(px + 2, py + 2) for px, py in wing_top])
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_darkest"], wing_top)
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_dark"], [
            (cx - 2 * facing, cy - 4),
            (cx - 11 * facing, top_wing_y + 1),
            (cx - 20 * facing, top_wing_y + 3),
            (cx - 22 * facing, cy - 4),
            (cx - 13 * facing, cy - 5),
        ])
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_mid"], [
            (cx - 3 * facing, cy - 4),
            (cx - 8 * facing, top_wing_y + 3),
            (cx - 15 * facing, top_wing_y + 5),
            (cx - 12 * facing, cy - 4),
        ])
        # Feathers detail on wing
        for i in range(4):
            fx = cx - (10 + i * 4) * facing
            fy = top_wing_y + 4 + i
            pygame.draw.line(surface, _NS_deidara.PALETTE["clay_darkest"],
                             (fx, fy), (fx - facing * 3, fy + 2), 1)
            pygame.draw.line(surface, _NS_deidara.PALETTE["clay_mid"],
                             (fx, fy - 1), (fx - facing * 3, fy + 1), 1)
        # Bottom wing (partial, showing depth)
        bot_wing_y = cy + 4 - int(wing_beat)
        wing_bot = [
            (cx - 4 * facing, cy),
            (cx - 12 * facing, bot_wing_y + 2),
            (cx - 18 * facing, bot_wing_y + 5),
            (cx - 14 * facing, cy + 3),
            (cx - 8 * facing, cy + 2),
        ]
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_darkest"], wing_bot)
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_dark"], [
            (cx - 4 * facing, cy),
            (cx - 10 * facing, bot_wing_y + 3),
            (cx - 15 * facing, bot_wing_y + 4),
            (cx - 12 * facing, cy + 2),
        ])
        # Tail
        tail_pts = [
            (cx - 12 * facing, cy),
            (cx - 20 * facing, cy - 1),
            (cx - 24 * facing, cy + 1),
            (cx - 20 * facing, cy + 3),
            (cx - 12 * facing, cy + 2),
        ]
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_darkest"], tail_pts)
        _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_dark"], [
            (cx - 12 * facing, cy),
            (cx - 18 * facing, cy),
            (cx - 20 * facing, cy + 2),
            (cx - 14 * facing, cy + 2),
        ])
    # ============================================================
    # SKILL R - KATSU! (Ultimate - Giant Clay Bomb)
    # ============================================================
    def _draw_katsu_ground(surface, boss, x, y, timer, phase):
        """Ground indicator for giant bomb."""
        tx, ty = _NS_deidara._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.6:
            # Warning circle grows
            t = progress / 0.6
            r = int(20 + t * 40)
            alpha = _NS_deidara._alpha(200 * t)
            pygame.draw.ellipse(surface, (*_NS_deidara.PALETTE["expl_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_deidara.PALETTE["expl_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            for i in range(12):
                angle = i * math.pi / 6 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_deidara.PALETTE["expl_hot"], (sx, sy, 2, 2))
        else:
            # Post explosion - burnt ground
            t = (progress - 0.6) / 0.4
            r = int(60 + t * 30)
            alpha = _NS_deidara._alpha(255 * (1 - t * 0.5))
            pygame.draw.ellipse(surface, (*_NS_deidara.PALETTE["expl_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_deidara.PALETTE["expl_dark"], alpha),
                                (tx - r + 5, ty - r // 3 + 3,
                                 r * 2 - 10, r * 2 // 3 - 6))
    def _draw_katsu_skill(surface, boss, x, y, timer, phase):
        """Giant clay bomb with mouth - detonates spectacularly."""
        tx, ty = _NS_deidara._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.2:
            # Growing bomb (small to large)
            t = progress / 0.2
            size = int(8 + t * 20)
            _NS_deidara._draw_giant_clay_bomb(surface, tx, ty - 8, size, phase, mouth_open=False)
        elif progress < 0.6:
            # Full size bomb with pulsating menace
            pulse_size = 28 + int(math.sin(phase * 3) * 3)
            mouth_open = progress > 0.4
            _NS_deidara._draw_giant_clay_bomb(surface, tx, ty - 8, pulse_size, phase,
                                              mouth_open=mouth_open)
            # Charge sparks
            if mouth_open:
                for i in range(8):
                    angle = phase * 2 + i * math.pi / 4
                    sx = tx + int(math.cos(angle) * (pulse_size + 5))
                    sy = ty - 8 + int(math.sin(angle) * (pulse_size + 5))
                    pygame.draw.rect(surface, _NS_deidara.PALETTE["expl_hot"],
                                     (sx, sy, 2, 2))
                    pygame.draw.rect(surface, _NS_deidara.PALETTE["expl_bright"],
                                     (sx, sy, 1, 1))
        elif progress < 0.85:
            # KATSU! MASSIVE EXPLOSION
            t = (progress - 0.6) / 0.25
            radius = int(30 + t * 90)
            alpha = _NS_deidara._alpha(255 * (1 - t * 0.7))
            # Multi-layer massive explosion
            _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_darkest"], alpha),
                                  (tx, ty), radius + 8)
            _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_dark"], alpha),
                                  (tx, ty), radius)
            _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_mid"], alpha),
                                  (tx, ty), max(1, radius - 12))
            _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_hot"], alpha),
                                  (tx, ty), max(1, radius - 25))
            _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_bright"], alpha),
                                  (tx, ty), max(1, radius - 40))
            _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_shine"], alpha),
                                  (tx, ty), max(1, radius // 6))
            # Multiple shockwaves
            for wave in range(3):
                wave_r = int(radius + wave * 15)
                wave_alpha = _NS_deidara._alpha(200 * (1 - t) * (1 - wave * 0.3))
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_bright"], wave_alpha),
                                      (tx, ty), wave_r, 2)
            # Massive radial burst
            for i in range(24):
                angle_s = i * math.pi / 12
                inner_r = radius * 0.3
                outer_r = radius * 1.3
                sx = tx + int(math.cos(angle_s) * inner_r)
                sy = ty + int(math.sin(angle_s) * inner_r)
                ex = tx + int(math.cos(angle_s) * outer_r)
                ey = ty + int(math.sin(angle_s) * outer_r)
                pygame.draw.line(surface, (*_NS_deidara.PALETTE["expl_bright"], alpha),
                                 (sx, sy), (ex, ey), 3)
                pygame.draw.rect(surface, _NS_deidara.PALETTE["expl_shine"],
                                 (ex, ey, 3, 3))
            # Debris
            for i in range(20):
                angle_d = phase * 2 + i * math.pi / 10
                d_r = radius + 10
                dx = tx + int(math.cos(angle_d) * d_r * (0.8 + (i % 4) * 0.1))
                dy = ty + int(math.sin(angle_d) * d_r * (0.8 + (i % 4) * 0.1))
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["clay_dark"], alpha),
                                      (dx, dy), 3)
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["clay_mid"], alpha),
                                      (dx, dy), 2)
        else:
            # Smoke aftermath
            t = (progress - 0.85) / 0.15
            for i in range(15):
                rise_t = (phase * 0.5 + i * 0.08) % 1.0
                rx = tx + int(math.sin(phase + i) * 40)
                ry = ty - int(rise_t * 60)
                alpha = _NS_deidara._alpha(220 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["smoke_dark"], alpha),
                                          (rx, ry), 8)
                    _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["smoke_mid"], alpha),
                                          (rx, ry), 6)
                    _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["smoke_light"], alpha),
                                          (rx, ry), 3)
    def _draw_giant_clay_bomb(surface, cx, cy, size, phase, mouth_open=False):
        """Giant clay bomb sphere with big mouth."""
        # Shadow
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["shadow_deep"],
                              (cx + 3, cy + 3), size + 1)
        # Main sphere layers
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_darkest"], (cx, cy), size)
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_dark"], (cx, cy), size - 2)
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_mid"],
                              (cx - 2, cy - 2), size - 6)
        # Highlight
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_light"],
                              (cx - size // 3, cy - size // 3), size // 4)
        _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["clay_shine"],
                              (cx - size // 3 - 1, cy - size // 3 - 1), size // 8)
        # Cracks/texture
        for i in range(4):
            angle = i * math.pi / 2 + phase * 0.2
            x1 = cx + int(math.cos(angle) * (size - 4))
            y1 = cy + int(math.sin(angle) * (size - 4))
            x2 = cx + int(math.cos(angle) * (size - 1))
            y2 = cy + int(math.sin(angle) * (size - 1))
            pygame.draw.line(surface, _NS_deidara.PALETTE["clay_darkest"],
                             (x1, y1), (x2, y2), 1)
        # BIG SCARY MOUTH
        mouth_w = size // 2 + 4
        mouth_h = mouth_w if mouth_open else 2
        if mouth_open:
            # Open mouth - dark cavity
            pygame.draw.ellipse(surface, _NS_deidara.PALETTE["shadow_deep"],
                                (cx - mouth_w, cy - mouth_h // 2,
                                 mouth_w * 2, mouth_h))
            pygame.draw.ellipse(surface, _NS_deidara.PALETTE["cloud_darkest"],
                                (cx - mouth_w + 2, cy - mouth_h // 2 + 1,
                                 mouth_w * 2 - 4, mouth_h - 2))
            # Inner glow (about to explode)
            for r in range(mouth_w - 2, 0, -2):
                alpha = _NS_deidara._alpha(200 * (mouth_w - 2 - r) / (mouth_w - 2))
                _NS_deidara._aacircle(surface, (*_NS_deidara.PALETTE["expl_hot"], alpha),
                                      (cx, cy), r)
            _NS_deidara._aacircle(surface, _NS_deidara.PALETTE["expl_bright"],
                                  (cx, cy), 3)
            # TEETH (big pointy teeth)
            num_teeth = 8
            for i in range(num_teeth):
                tx = cx - mouth_w + int(i * (mouth_w * 2) / (num_teeth - 1))
                # Upper teeth
                _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_shine"], [
                    (tx, cy - mouth_h // 2),
                    (tx + 3, cy - mouth_h // 2),
                    (tx + 1, cy - 1),
                ])
                _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_light"], [
                    (tx + 1, cy - mouth_h // 2),
                    (tx + 2, cy - mouth_h // 2),
                    (tx + 1, cy - 2),
                ])
                # Lower teeth
                _NS_deidara._poly(surface, _NS_deidara.PALETTE["clay_shine"], [
                    (tx, cy + mouth_h // 2),
                    (tx + 3, cy + mouth_h // 2),
                    (tx + 1, cy + 1),
                ])
        else:
            # Closed - stitched line
            pygame.draw.line(surface, _NS_deidara.PALETTE["shadow_deep"],
                             (cx - mouth_w, cy), (cx + mouth_w, cy), 2)
            # Stitches
            for i in range(-mouth_w + 2, mouth_w, 3):
                pygame.draw.line(surface, _NS_deidara.PALETTE["clay_darkest"],
                                 (cx + i, cy - 1), (cx + i, cy + 1), 1)
        # Eyes (evil dots)
        eye_y = cy - size // 2
        pygame.draw.rect(surface, _NS_deidara.PALETTE["shadow_deep"],
                         (cx - size // 3, eye_y, 3, 3))
        pygame.draw.rect(surface, _NS_deidara.PALETTE["shadow_deep"],
                         (cx + size // 3 - 2, eye_y, 3, 3))
        pygame.draw.rect(surface, _NS_deidara.PALETTE["expl_hot"],
                         (cx - size // 3 + 1, eye_y + 1, 1, 1))
        pygame.draw.rect(surface, _NS_deidara.PALETTE["expl_hot"],
                         (cx + size // 3 - 1, eye_y + 1, 1, 1))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_akiraze(surface, boss, x, y):
    """Entry point akiraze."""
    return _NS_akiraze.draw_akiraze(surface, boss, x, y)


def draw_brumhar(surface, boss, x, y):
    """Entry point brumhar."""
    return _NS_brumhar.draw_brumhar(surface, boss, x, y)


def draw_zorashi(surface, boss, x, y):
    """Entry point zorashi."""
    return _NS_zorashi.draw_zorashi(surface, boss, x, y)


def draw_deidara(surface, boss, x, y):
    """Entry point deidara."""
    return _NS_deidara.draw_deidara(surface, boss, x, y)
