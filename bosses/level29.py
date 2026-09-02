"""
bosses/level29.py - Semua boss Level 29

Berisi:
  - ignakhor    (mini boss - MELEE furnace-wrought berserker, fire)
  - kazureth    (mini boss - MELEE thunder wielder, lightning katana)
  - sethrakhar  (mini boss - MELEE sunforged butcher, rage)
  - nyrellieth  (TRUE BOSS - RANGED frost-veiled huntress, ice archer)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _kaz_ (kazureth), _seth_ (sethrakhar), _nyr_ (nyrellieth) sudah unik.
  - _ign_ (ignakhor) di-rename -> _igk_ (bentrok dengan ignis_drachorn
    level 4), termasuk atribut _last_x/_last_y.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True


# ====================================================================
# IGNAKHOR (FURNACE-WROUGHT BERSERKER) - Mini Boss
# ====================================================================

class _NS_ignakhor:
    """Namespace ignakhor - fire cyborg mini-boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Metal / iron machinery (main body armor)
        "metal_darkest": (10, 10, 12),
        "metal_dark": (30, 30, 35),
        "metal_mid": (65, 65, 72),
        "metal_light": (110, 110, 120),
        "metal_edge": (170, 170, 180),
        "metal_shine": (220, 220, 225),
        # Rust brown (aged metal)
        "rust_darkest": (30, 15, 8),
        "rust_dark": (65, 35, 15),
        "rust_mid": (115, 65, 30),
        "rust_light": (170, 105, 55),
        # Fire orange (main magic theme)
        "fire_darkest": (50, 15, 3),
        "fire_dark": (125, 45, 8),
        "fire_mid": (215, 90, 20),
        "fire_light": (255, 155, 50),
        "fire_hot": (255, 210, 95),
        "fire_shine": (255, 245, 175),
        "fire_glare": (255, 255, 220),
        # Red hair (spiky wild)
        "hair_darkest": (55, 10, 8),
        "hair_dark": (110, 20, 15),
        "hair_mid": (180, 40, 30),
        "hair_light": (230, 75, 55),
        "hair_shine": (255, 130, 100),
        # Skin (tanned face)
        "skin_darkest": (75, 45, 30),
        "skin_dark": (135, 90, 60),
        "skin_mid": (190, 140, 100),
        "skin_light": (230, 180, 140),
        "skin_shine": (250, 210, 175),
        # Cyan/yellow tech glow (screens, eyes)
        "tech_dark": (60, 90, 30),
        "tech_mid": (180, 220, 40),
        "tech_light": (240, 255, 100),
        "tech_shine": (255, 255, 200),
        # Gold accents (goggle rim, decals)
        "gold_dark": (100, 75, 20),
        "gold_mid": (185, 145, 45),
        "gold_light": (240, 205, 85),
        "gold_shine": (255, 240, 160),
        # Dark red cloth (belt, straps)
        "cloth_darkest": (25, 8, 8),
        "cloth_dark": (75, 20, 15),
        "cloth_mid": (135, 45, 30),
        # Eyes (glowing yellow-orange)
        "eye_socket": (5, 3, 2),
        "eye_dark": (100, 60, 5),
        "eye_mid": (230, 170, 40),
        "eye_light": (255, 220, 100),
        "eye_glow": (255, 250, 200),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_ignakhor._clamp(color)
        if _NS_ignakhor.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_ignakhor._clamp(color)
        if _NS_ignakhor.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_ignakhor._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_ignakhor(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_ignakhor._detect_moving(boss)
        _NS_ignakhor._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_igk_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_ignakhor._draw_furnace_aura(surface, x, y, pulse)
        _NS_ignakhor._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "w":
            _NS_ignakhor._draw_firestake_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_ignakhor._draw_firespin_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_ignakhor._draw_lastinsanity_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (always floating - jet propulsion)
        if attacking:
            _NS_ignakhor._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_ignakhor._draw_float_move(surface, boss, x, y)
        else:
            _NS_ignakhor._draw_float_idle(surface, boss, x, y)
        # Last Insanity aura (over body)
        if active_skill == "r":
            _NS_ignakhor._draw_lastinsanity_aura(surface, boss, x, y, skill_timer, pulse)
        # Foreground FX
        if active_skill == "q":
            _NS_ignakhor._draw_firemissile_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_ignakhor._draw_firestake_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_ignakhor._draw_firespin_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_igk_previous_timer", 0))
        active = bool(getattr(boss, "_igk_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._igk_attack_active = True
            boss._igk_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._igk_attack_frame = int(getattr(boss, "_igk_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._igk_attack_active = False
            boss._igk_attack_frame = 0
            active = False
        boss._igk_previous_timer = timer
        boss._igk_attack_progress = (
            min(1.0, getattr(boss, "_igk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_igk_last_x"):
            boss._igk_last_x = boss.x
            boss._igk_last_y = boss.y
            return False
        dx = abs(boss.x - boss._igk_last_x)
        dy = abs(boss.y - boss._igk_last_y)
        boss._igk_last_x = boss.x
        boss._igk_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS (Floating with jet exhaust)
    # ============================================================
    def _draw_float_idle(surface, boss, x, y):
        hover = int(math.sin(boss.pulse * 0.9) * 4) - 6
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_ignakhor._draw_float_shadow(surface, x + sway, y + 50, boss.pulse)
        _NS_ignakhor._draw_jet_exhaust(surface, x + sway, y + 40, boss.pulse)
        _NS_ignakhor._draw_body(surface, x + sway, y + hover,
                                boss.direction, boss.pulse, "idle")
    def _draw_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.6
        hover = int(math.sin(phase * 1.0) * 5) - 7
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_ignakhor._draw_float_shadow(surface, x + sway, y + 50, phase)
        _NS_ignakhor._draw_jet_exhaust(surface, x + sway, y + 40, phase,
                                       trail=True, facing=boss.direction)
        _NS_ignakhor._draw_body(surface, x + sway, y + hover,
                                boss.direction, phase, "float")
    def _draw_attack(surface, boss, x, y):
        """Ranged: fire missile launcher."""
        progress = getattr(boss, "_igk_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Recoil pose
        if progress < 0.4:
            t = progress / 0.4
            lean = -int(t * 4) * boss.direction
            lift = int(t * 2)
        elif progress < 0.6:
            t = (progress - 0.4) / 0.2
            lean = int((-4 + t * 12)) * boss.direction
            lift = int(2 - t * 4)
        else:
            t = (progress - 0.6) / 0.4
            lean = int(8 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        hover = int(math.sin(boss.pulse * 0.9) * 3) - 5
        _NS_ignakhor._draw_float_shadow(surface, x + lean, y + 50, boss.pulse)
        _NS_ignakhor._draw_jet_exhaust(surface, x + lean, y + 40,
                                       boss.pulse, intense=True)
        _NS_ignakhor._draw_body(surface, x + lean, y + hover - lift,
                                boss.direction, boss.pulse,
                                "attack", progress)
        _NS_ignakhor._draw_missile_projectile(surface, boss, x + lean,
                                              y + hover - lift, progress)
    # ============================================================
    # BODY - Cyborg
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Back mechanical arm (with pistons)
        _NS_ignakhor._draw_back_mech_arm(surface, cx, cy - 2, facing, phase)
        # Torso (mech armor)
        _NS_ignakhor._draw_mech_torso(surface, cx, cy, facing, phase)
        # Legs (mechanical, dangling)
        _NS_ignakhor._draw_mech_legs(surface, cx, cy + 8, facing, phase, action)
        # Head (skin face + goggles + spiky red hair)
        _NS_ignakhor._draw_cyborg_head(surface, cx, cy - 18, facing, phase, action,
                                       attack_progress)
        # Front arm with fire cannon (LAST)
        _NS_ignakhor._draw_cannon_arm(surface, cx, cy - 2, facing, phase, action,
                                      attack_progress)
    def _draw_mech_torso(surface, cx, cy, facing, phase):
        """Metal chest armor with red glowing core."""
        breath = math.sin(phase * 0.7) * 1
        # Torso base
        torso_pts = [
            (cx - 10, cy - 6),
            (cx - 11, cy),
            (cx - 10, cy + 7),
            (cx - 7, cy + 10),
            (cx + 7, cy + 10),
            (cx + 10, cy + 7),
            (cx + 11, cy),
            (cx + 10, cy - 6),
        ]
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in torso_pts])
        # Dark metal base
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["metal_darkest"], torso_pts)
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["metal_dark"], [
            (cx - 9, cy - 5),
            (cx - 10, cy),
            (cx - 9, cy + 6),
            (cx - 6, cy + 9),
            (cx + 6, cy + 9),
            (cx + 9, cy + 6),
            (cx + 10, cy),
            (cx + 9, cy - 5),
        ])
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["metal_mid"], [
            (cx - 7, cy - 4),
            (cx - 8, cy),
            (cx - 7, cy + 4),
            (cx - 5, cy + 8),
            (cx + 5, cy + 8),
            (cx + 7, cy + 4),
            (cx + 8, cy),
            (cx + 7, cy - 4),
        ])
        # Chest highlight (metal shine)
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["metal_light"], [
            (cx - 5, cy - 2),
            (cx + 5, cy - 2),
            (cx + 4, cy),
            (cx - 4, cy),
        ])
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_edge"],
                         (cx - 3, cy - 2, 6, 1))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_shine"],
                         (cx - 2, cy - 2, 4, 1))
        # RED FURNACE CORE in center chest (like X.Borg!)
        core_pulse = math.sin(phase * 3) * 0.4 + 0.6
        core_cx = cx
        core_cy = cy + 3
        # Core socket
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["shadow_deep"],
                         (core_cx - 3, core_cy - 3, 6, 6))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                         (core_cx - 3, core_cy - 3, 6, 5))
        # Circular core
        _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["fire_darkest"],
                               (core_cx, core_cy), 3)
        _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["fire_dark"],
                               (core_cx, core_cy), 3)
        # Pulsing bright core
        for r in range(4, 0, -1):
            alpha = _NS_ignakhor._alpha(220 * (4 - r) / 4 * core_pulse)
            _NS_ignakhor._aacircle(surface,
                                   (*_NS_ignakhor.PALETTE["fire_mid"], alpha),
                                   (core_cx, core_cy), r)
        _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["fire_hot"],
                               (core_cx, core_cy), 1)
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_shine"],
                         (core_cx, core_cy, 1, 1))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["white"],
                         (core_cx, core_cy, 1, 1))
        # Bolts/rivets around core
        for i in range(4):
            a = i * math.pi / 2
            bx = core_cx + int(math.cos(a) * 4)
            by = core_cy + int(math.sin(a) * 4)
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_edge"],
                             (bx, by, 1, 1))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_shine"],
                             (bx, by, 1, 1))
        # Vertical panel lines on torso
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                         (cx - 5, cy + 6), (cx - 5, cy + 9), 1)
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                         (cx + 5, cy + 6), (cx + 5, cy + 9), 1)
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_edge"],
                         (cx - 4, cy + 6), (cx - 4, cy + 8), 1)
        # SHOULDER PADS (chunky metal pauldrons)
        for side in (-1, 1):
            paul_x = cx + side * 10
            paul_y = cy - 6
            _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["shadow_deep"], [
                (paul_x - 3, paul_y),
                (paul_x + 3, paul_y),
                (paul_x + 5, paul_y + 3),
                (paul_x + 3, paul_y + 6),
                (paul_x - 3, paul_y + 6),
                (paul_x - 5, paul_y + 3),
            ])
            _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["metal_darkest"], [
                (paul_x - 3, paul_y - 1),
                (paul_x + 3, paul_y - 1),
                (paul_x + 4, paul_y + 3),
                (paul_x + 2, paul_y + 5),
                (paul_x - 2, paul_y + 5),
                (paul_x - 4, paul_y + 3),
            ])
            _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["metal_dark"], [
                (paul_x - 3, paul_y),
                (paul_x + 3, paul_y),
                (paul_x + 3, paul_y + 3),
                (paul_x + 2, paul_y + 4),
                (paul_x - 2, paul_y + 4),
                (paul_x - 3, paul_y + 3),
            ])
            _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["metal_mid"], [
                (paul_x - 2, paul_y),
                (paul_x + 2, paul_y),
                (paul_x + 2, paul_y + 2),
                (paul_x - 2, paul_y + 2),
            ])
            # Highlight
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_edge"],
                             (paul_x - 2, paul_y - 1, 4, 1))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_shine"],
                             (paul_x - 1, paul_y - 1, 2, 1))
            # Red hot vent on pauldron
            vent_pulse = math.sin(phase * 4 + side) * 0.3 + 0.7
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["shadow_deep"],
                             (paul_x - 1, paul_y + 3, 3, 2))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_darkest"],
                             (paul_x - 1, paul_y + 3, 3, 2))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_dark"],
                             (paul_x - 1, paul_y + 3, 3, 1))
            fire_alpha = _NS_ignakhor._alpha(220 * vent_pulse)
            pygame.draw.rect(surface,
                             (*_NS_ignakhor.PALETTE["fire_mid"], fire_alpha),
                             (paul_x - 1, paul_y + 3, 3, 1))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_hot"],
                             (paul_x, paul_y + 3, 1, 1))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_shine"],
                             (paul_x, paul_y + 3, 1, 1))
        # WAIST BELT (dark leather with metal buckle)
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["cloth_darkest"],
                         (cx - 8, cy + 8, 16, 3))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["cloth_dark"],
                         (cx - 8, cy + 8, 16, 2))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["cloth_mid"],
                         (cx - 8, cy + 8, 16, 1))
        # Buckle (metal)
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                         (cx - 2, cy + 8, 5, 3))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_mid"],
                         (cx - 2, cy + 8, 5, 2))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_edge"],
                         (cx - 1, cy + 8, 3, 1))
        # Fire hot core in buckle
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_mid"],
                         (cx, cy + 9, 1, 1))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_hot"],
                         (cx, cy + 9, 1, 1))
        # Small pistons/tubes on side of torso
        for side in (-1, 1):
            for pi in range(2):
                pipe_x = cx + side * (9 - pi)
                pipe_y = cy + 2 + pi * 2
                pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                                 (pipe_x, pipe_y, 1, 2))
                pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_edge"],
                                 (pipe_x, pipe_y, 1, 1))
    def _draw_mech_legs(surface, cx, cy, facing, phase, action):
        """Mechanical legs with pistons - dangling because floating."""
        sway = math.sin(phase * 0.9) * 1.5
        for side in (-1, 1):
            leg_x_top = cx + side * 4
            leg_x_bot = cx + side * 5 + int(sway * side * 0.5)
            leg_y_top = cy
            leg_y_bot = cy + 15
            # Thigh (thick metal)
            pygame.draw.line(surface, _NS_ignakhor.PALETTE["shadow_deep"],
                             (leg_x_top + 1, leg_y_top + 1),
                             (leg_x_bot + 1, leg_y_bot + 1), 6)
            pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                             (leg_x_top, leg_y_top),
                             (leg_x_bot, leg_y_bot), 5)
            pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_dark"],
                             (leg_x_top, leg_y_top),
                             (leg_x_bot, leg_y_bot), 4)
            pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_mid"],
                             (leg_x_top - side, leg_y_top),
                             (leg_x_bot - side, leg_y_bot), 3)
            pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_edge"],
                             (leg_x_top - side, leg_y_top + 1),
                             (leg_x_bot - side, leg_y_bot - 1), 1)
            # Knee joint (piston circle)
            knee_y = leg_y_top + 7
            knee_x = leg_x_top + int((leg_x_bot - leg_x_top) * 0.5)
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["shadow_deep"],
                                   (knee_x, knee_y), 3)
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                                   (knee_x, knee_y), 3)
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["metal_dark"],
                                   (knee_x, knee_y), 2)
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["metal_edge"],
                                   (knee_x, knee_y), 1)
            # Red gleam
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_hot"],
                             (knee_x, knee_y, 1, 1))
            # Foot (chunky metal boot)
            boot_x = leg_x_bot
            boot_y = leg_y_bot
            _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["shadow_deep"], [
                (boot_x - 4, boot_y - 1),
                (boot_x + 4, boot_y - 1),
                (boot_x + 5, boot_y + 3),
                (boot_x - 5, boot_y + 3),
            ])
            _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["metal_darkest"], [
                (boot_x - 4, boot_y - 2),
                (boot_x + 4, boot_y - 2),
                (boot_x + 4, boot_y + 2),
                (boot_x - 4, boot_y + 2),
            ])
            _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["metal_dark"], [
                (boot_x - 3, boot_y - 2),
                (boot_x + 3, boot_y - 2),
                (boot_x + 3, boot_y + 1),
                (boot_x - 3, boot_y + 1),
            ])
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_mid"],
                             (boot_x - 3, boot_y - 2, 6, 1))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_edge"],
                             (boot_x - 2, boot_y - 2, 4, 1))
            # Red flame at bottom (jet exhaust from feet)
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_dark"],
                             (boot_x - 2, boot_y + 2, 4, 1))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_hot"],
                             (boot_x - 1, boot_y + 2, 2, 1))
    def _draw_back_mech_arm(surface, cx, cy, facing, phase):
        """Back arm - mechanical with pistons."""
        back_shoulder_x = cx - facing * 5
        back_shoulder_y = cy - 2
        arm_angle = math.pi * 0.35 + math.sin(phase * 0.5) * 0.1
        arm_length = 12
        back_hand_x = back_shoulder_x - int(math.cos(arm_angle) * arm_length) * facing
        back_hand_y = back_shoulder_y + int(math.sin(arm_angle) * arm_length) + 2
        elbow_x = back_shoulder_x - int(math.cos(arm_angle) * (arm_length * 0.5)) * facing
        elbow_y = back_shoulder_y + int(math.sin(arm_angle) * (arm_length * 0.5))
        # Upper arm (mech)
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["shadow_deep"],
                         (back_shoulder_x + 1, back_shoulder_y + 1),
                         (elbow_x + 1, elbow_y + 1), 5)
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                         (back_shoulder_x, back_shoulder_y),
                         (elbow_x, elbow_y), 4)
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_dark"],
                         (back_shoulder_x, back_shoulder_y),
                         (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_mid"],
                         (back_shoulder_x - 1, back_shoulder_y),
                         (elbow_x - 1, elbow_y), 2)
        # Piston on upper arm
        piston_mid_x = int((back_shoulder_x + elbow_x) / 2)
        piston_mid_y = int((back_shoulder_y + elbow_y) / 2)
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                         (piston_mid_x - 1, piston_mid_y - 2, 2, 4))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_edge"],
                         (piston_mid_x - 1, piston_mid_y - 2, 1, 4))
        # Elbow joint
        _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                               (elbow_x, elbow_y), 2)
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_hot"],
                         (elbow_x, elbow_y, 1, 1))
        # Forearm (skin - some parts organic!)
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["shadow_deep"],
                         (elbow_x + 1, elbow_y + 1),
                         (back_hand_x + 1, back_hand_y + 1), 4)
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["skin_darkest"],
                         (elbow_x, elbow_y), (back_hand_x, back_hand_y), 3)
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["skin_dark"],
                         (elbow_x, elbow_y), (back_hand_x, back_hand_y), 2)
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["skin_mid"],
                         (elbow_x - 1, elbow_y), (back_hand_x - 1, back_hand_y), 1)
        # Wristband (metal cuff)
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                         (back_hand_x - 2, back_hand_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_dark"],
                         (back_hand_x - 2, back_hand_y - 1, 4, 2))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_edge"],
                         (back_hand_x - 2, back_hand_y - 1, 4, 1))
        # Fist
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["skin_dark"],
                         (back_hand_x - 1, back_hand_y + 1, 3, 2))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["skin_mid"],
                         (back_hand_x - 1, back_hand_y + 1, 2, 1))
    def _draw_cannon_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm with big fire missile cannon."""
        shoulder_x = cx + facing * 5
        shoulder_y = cy - 2
        if action == "attack":
            if attack_progress < 0.4:
                t = attack_progress / 0.4
                arm_angle = -math.pi * 0.05 * (1 - t) - math.pi * 0.15 * t
            elif attack_progress < 0.6:
                t = (attack_progress - 0.4) / 0.2
                # Aim forward + recoil
                arm_angle = -math.pi * 0.15 + math.pi * 0.15 * t
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * 0.0 * (1 - t)
        else:
            # Weapon aimed forward
            arm_angle = -math.pi * 0.05 + math.sin(phase * 0.5) * 0.03
        arm_length = 12
        hand_x = shoulder_x + int(math.cos(arm_angle) * arm_length) * facing
        hand_y = shoulder_y + int(math.sin(arm_angle) * arm_length) + 4
        elbow_x = shoulder_x + int(math.cos(arm_angle) * (arm_length * 0.55)) * facing
        elbow_y = shoulder_y + int(math.sin(arm_angle) * (arm_length * 0.55)) + 2
        # Upper arm (mech)
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["shadow_deep"],
                         (shoulder_x + 1, shoulder_y + 1),
                         (elbow_x + 1, elbow_y + 1), 6)
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_dark"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_mid"],
                         (shoulder_x - 1, shoulder_y), (elbow_x - 1, elbow_y), 2)
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_edge"],
                         (shoulder_x - 1, shoulder_y + 1),
                         (elbow_x - 1, elbow_y - 1), 1)
        # Piston tube on arm
        piston_x = int((shoulder_x + elbow_x) / 2)
        piston_y = int((shoulder_y + elbow_y) / 2)
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                         (piston_x - 2, piston_y - 3, 4, 6))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_dark"],
                         (piston_x - 2, piston_y - 3, 4, 5))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_edge"],
                         (piston_x - 1, piston_y - 3, 2, 6))
        # Red hot line on piston (heat)
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["fire_mid"],
                         (piston_x, piston_y - 3), (piston_x, piston_y + 3), 1)
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["fire_hot"],
                         (piston_x, piston_y - 2), (piston_x, piston_y + 2), 1)
        # Elbow joint circle
        _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["shadow_deep"],
                               (elbow_x, elbow_y), 3)
        _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                               (elbow_x, elbow_y), 3)
        _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["metal_dark"],
                               (elbow_x, elbow_y), 2)
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_hot"],
                         (elbow_x, elbow_y, 1, 1))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_shine"],
                         (elbow_x, elbow_y, 1, 1))
        # FIRE CANNON (mechanical launcher on forearm)
        _NS_ignakhor._draw_fire_cannon(surface, elbow_x, elbow_y, hand_x, hand_y,
                                       facing, phase, action, attack_progress,
                                       arm_angle)
    def _draw_fire_cannon(surface, elbow_x, elbow_y, hand_x, hand_y,
                          facing, phase, action, attack_progress, arm_angle):
        """Big mechanical fire missile launcher."""
        # Barrel extends forward from hand
        barrel_len = 22
        # Direction of barrel
        barrel_end_x = hand_x + int(math.cos(arm_angle) * barrel_len) * facing
        barrel_end_y = hand_y + int(math.sin(arm_angle) * barrel_len) + 2
        # Cannon body (chunky rectangle from elbow to hand+barrel)
        perp_x = -math.sin(arm_angle)
        perp_y = math.cos(arm_angle)
        # Cannon body - main chamber
        body_a = (hand_x + int(perp_x * 5), hand_y + int(perp_y * 5))
        body_b = (hand_x - int(perp_x * 5), hand_y - int(perp_y * 5))
        body_c = (barrel_end_x - facing * 6 - int(perp_x * 4),
                  barrel_end_y - int(perp_y * 4) + 1)
        body_d = (barrel_end_x - facing * 6 + int(perp_x * 4),
                  barrel_end_y + int(perp_y * 4) + 1)
        # Shadow
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["shadow_deep"], [
            (body_a[0] + 2, body_a[1] + 2),
            (body_c[0] + 2, body_c[1] + 2),
            (body_d[0] + 2, body_d[1] + 2),
            (body_b[0] + 2, body_b[1] + 2),
        ])
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                           [body_a, body_c, body_d, body_b])
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["metal_dark"], [
            (body_a[0] - int(perp_x), body_a[1] - int(perp_y)),
            (body_c[0] - int(perp_x), body_c[1] - int(perp_y)),
            (body_d[0] + int(perp_x), body_d[1] + int(perp_y)),
            (body_b[0] + int(perp_x), body_b[1] + int(perp_y)),
        ])
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["metal_mid"], [
            (body_a[0] - int(perp_x * 2), body_a[1] - int(perp_y * 2)),
            (body_c[0] - int(perp_x * 2), body_c[1] - int(perp_y * 2)),
            (body_d[0] + int(perp_x * 2), body_d[1] + int(perp_y * 2)),
            (body_b[0] + int(perp_x * 2), body_b[1] + int(perp_y * 2)),
        ])
        # Top highlight
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_edge"],
                         (body_a[0] - int(perp_x * 3), body_a[1] - int(perp_y * 3)),
                         (body_c[0] - int(perp_x * 3), body_c[1] - int(perp_y * 3)), 1)
        pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_shine"],
                         (body_a[0] - int(perp_x * 3.5), body_a[1] - int(perp_y * 3.5)),
                         (body_c[0] - int(perp_x * 3.5),
                          body_c[1] - int(perp_y * 3.5)), 1)
        # BARREL (dark cylindrical extension forward)
        barrel_a = (barrel_end_x - facing * 6 - int(perp_x * 3),
                    barrel_end_y - int(perp_y * 3) + 1)
        barrel_b = (barrel_end_x - facing * 6 + int(perp_x * 3),
                    barrel_end_y + int(perp_y * 3) + 1)
        barrel_c = (barrel_end_x - int(perp_x * 3),
                    barrel_end_y - int(perp_y * 3) + 1)
        barrel_d = (barrel_end_x + int(perp_x * 3),
                    barrel_end_y + int(perp_y * 3) + 1)
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["shadow_deep"], [
            (barrel_a[0] + 2, barrel_a[1] + 2),
            (barrel_c[0] + 2, barrel_c[1] + 2),
            (barrel_d[0] + 2, barrel_d[1] + 2),
            (barrel_b[0] + 2, barrel_b[1] + 2),
        ])
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                           [barrel_a, barrel_c, barrel_d, barrel_b])
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["metal_dark"], [
            (barrel_a[0] - int(perp_x), barrel_a[1] - int(perp_y)),
            (barrel_c[0] - int(perp_x), barrel_c[1] - int(perp_y)),
            (barrel_d[0] + int(perp_x), barrel_d[1] + int(perp_y)),
            (barrel_b[0] + int(perp_x), barrel_b[1] + int(perp_y)),
        ])
        # Rust bands on barrel
        for band_t in (0.3, 0.6, 0.9):
            band_x = int(barrel_a[0] + (barrel_c[0] - barrel_a[0]) * band_t)
            band_y = int(barrel_a[1] + (barrel_c[1] - barrel_a[1]) * band_t)
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["rust_dark"],
                             (band_x - 1, band_y - 3, 2, 6))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["rust_mid"],
                             (band_x - 1, band_y - 3, 2, 5))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["rust_light"],
                             (band_x - 1, band_y - 3, 1, 5))
        # BARREL MUZZLE (dark hole at tip)
        _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["shadow_deep"],
                               (barrel_end_x, barrel_end_y), 4)
        _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                               (barrel_end_x, barrel_end_y), 3)
        # Fire glow inside barrel (constant)
        muzzle_pulse = math.sin(phase * 4) * 0.4 + 0.6
        muzzle_r = int(2 + muzzle_pulse * 1.5)
        for r in range(muzzle_r + 2, 0, -1):
            alpha = _NS_ignakhor._alpha(220 * (muzzle_r + 2 - r) / (muzzle_r + 2))
            _NS_ignakhor._aacircle(surface,
                                   (*_NS_ignakhor.PALETTE["fire_dark"], alpha),
                                   (barrel_end_x, barrel_end_y), r)
        _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["fire_mid"],
                               (barrel_end_x, barrel_end_y), muzzle_r)
        _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["fire_hot"],
                               (barrel_end_x, barrel_end_y), max(1, muzzle_r - 1))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_shine"],
                         (barrel_end_x, barrel_end_y, 1, 1))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["white"],
                         (barrel_end_x, barrel_end_y, 1, 1))
        # Muzzle flash (when attacking)
        if action == "attack" and 0.4 < attack_progress < 0.6:
            flash_t = (attack_progress - 0.4) / 0.2
            flash_size = int(10 * (1 - flash_t))
            for r in range(flash_size + 5, 0, -1):
                alpha = _NS_ignakhor._alpha(240 * (flash_size + 5 - r) / (flash_size + 5))
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_light"], alpha),
                                       (barrel_end_x + facing * 4, barrel_end_y), r)
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["fire_hot"],
                                   (barrel_end_x + facing * 4, barrel_end_y),
                                   max(1, flash_size - 2))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["white"],
                             (barrel_end_x + facing * 4, barrel_end_y, 1, 1))
        # Ammo chamber (mag) on top of cannon (like reference)
        chamber_x = hand_x + int(math.cos(arm_angle) * 4) * facing
        chamber_y = hand_y + int(math.sin(arm_angle) * 4) - 4
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["shadow_deep"],
                         (chamber_x - 3, chamber_y - 4, 6, 5))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                         (chamber_x - 3, chamber_y - 4, 6, 4))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_dark"],
                         (chamber_x - 3, chamber_y - 4, 6, 3))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_mid"],
                         (chamber_x - 2, chamber_y - 4, 4, 2))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_edge"],
                         (chamber_x - 2, chamber_y - 4, 4, 1))
        # Chamber indicator (fire)
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_mid"],
                         (chamber_x, chamber_y - 2, 1, 1))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_hot"],
                         (chamber_x, chamber_y - 2, 1, 1))
    def _draw_cyborg_head(surface, cx, cy, facing, phase, action, attack_progress):
        """Head with tanned skin, glowing eye, goggles, spiky red hair."""
        # Head shape (face)
        head_pts = [
            (cx - 6, cy + 3),
            (cx - 7, cy - 1),
            (cx - 6, cy - 5),
            (cx - 3, cy - 8),
            (cx + 3, cy - 8),
            (cx + 6, cy - 5),
            (cx + 7, cy - 1),
            (cx + 6, cy + 3),
            (cx + 3, cy + 6),
            (cx - 3, cy + 6),
            (cx - 5, cy + 4),
        ]
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in head_pts])
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["skin_darkest"], head_pts)
        # Face base (tanned skin)
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["skin_dark"], [
            (cx - 5, cy + 2),
            (cx - 6, cy - 1),
            (cx - 5, cy - 4),
            (cx - 2, cy - 7),
            (cx + 3, cy - 7),
            (cx + 5, cy - 4),
            (cx + 6, cy - 1),
            (cx + 5, cy + 2),
            (cx + 2, cy + 5),
            (cx - 2, cy + 5),
        ])
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["skin_mid"], [
            (cx - 3, cy - 2),
            (cx - 3, cy - 4),
            (cx, cy - 6),
            (cx + 3, cy - 6),
            (cx + 5, cy - 3),
            (cx + 5, cy),
            (cx + 3, cy + 4),
            (cx, cy + 4),
            (cx - 2, cy + 2),
        ])
        # Highlights
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["skin_light"], [
            (cx + 1, cy - 4),
            (cx + 3, cy - 4),
            (cx + 4, cy - 2),
            (cx + 2, cy),
        ])
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["skin_shine"],
                         (cx + facing * 2, cy - 4, 1, 1))
        # SPIKY RED HAIR (wild flame-like)
        _NS_ignakhor._draw_flame_hair(surface, cx, cy, facing, phase)
        # GOGGLES/HEADBAND on forehead (metal + tech screen)
        _NS_ignakhor._draw_goggles(surface, cx, cy - 5, facing, phase)
        # GLOWING EYES (yellow-orange - Half hidden by goggle sometimes)
        _NS_ignakhor._draw_cyborg_eyes(surface, cx, cy - 2, facing, phase, action)
        # Nose
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["skin_darkest"],
                         (cx + facing, cy, 1, 1))
        # Smirking mouth (Zenitsu-style grinning)
        if action == "attack":
            # Yelling
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["shadow_deep"],
                             (cx - 2, cy + 3, 4, 2))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["cloth_darkest"],
                             (cx - 2, cy + 3, 4, 1))
            # Show teeth
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_shine"],
                             (cx - 1, cy + 3, 3, 1))
        else:
            # Smirk
            pygame.draw.line(surface, _NS_ignakhor.PALETTE["skin_darkest"],
                             (cx - 1, cy + 3), (cx + 2, cy + 3), 1)
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["skin_darkest"],
                             (cx + 2 * facing, cy + 2, 1, 1))
        # NECK MECHANICAL COLLAR/COMPONENT
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                         (cx - 4, cy + 6, 8, 3))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_dark"],
                         (cx - 4, cy + 6, 8, 2))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_mid"],
                         (cx - 4, cy + 6, 8, 1))
        # Red hot pipe on neck
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_mid"],
                         (cx - 3, cy + 7, 6, 1))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_hot"],
                         (cx - 2, cy + 7, 4, 1))
    def _draw_flame_hair(surface, cx, cy, facing, phase):
        """Wild spiky red hair like flames."""
        wind = math.sin(phase * 0.6) * 1
        # Hair mass (behind + on top)
        hair_bulk = [
            (cx - 6, cy - 4),
            (cx - 7, cy - 6),
            (cx - 5, cy - 9),
            (cx - 2, cy - 11),
            (cx + 2, cy - 11),
            (cx + 5, cy - 10),
            (cx + 7, cy - 7),
            (cx + 7, cy - 3),
            (cx + 5, cy),
            (cx - 5, cy),
        ]
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["shadow_deep"],
                           [(px + 1, py + 1) for px, py in hair_bulk])
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["hair_darkest"], hair_bulk)
        # Mid layer (red)
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["hair_dark"], [
            (cx - 5, cy - 5),
            (cx - 6, cy - 8),
            (cx - 2, cy - 10),
            (cx + 2, cy - 10),
            (cx + 5, cy - 8),
            (cx + 6, cy - 5),
            (cx + 5, cy - 1),
            (cx - 4, cy - 1),
        ])
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["hair_mid"], [
            (cx - 4, cy - 6),
            (cx - 5, cy - 8),
            (cx - 1, cy - 9),
            (cx + 2, cy - 9),
            (cx + 5, cy - 7),
            (cx + 4, cy - 3),
            (cx - 3, cy - 3),
        ])
        # Bright highlights
        _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["hair_light"], [
            (cx - 2, cy - 7),
            (cx - 3, cy - 8),
            (cx, cy - 9),
            (cx + 3, cy - 8),
            (cx + 3, cy - 5),
            (cx - 1, cy - 5),
        ])
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["hair_shine"],
                         (cx, cy - 8, 1, 1))
        # WILD SPIKES (like flame tips)
        spike_positions = [
            (-6, -6, 4), (-3, -10, 6), (-1, -11, 7),
            (2, -11, 6), (5, -10, 5), (7, -6, 4),
        ]
        for i, (spike_x_off, spike_base_y, spike_height) in enumerate(spike_positions):
            spike_sway = int(math.sin(phase * 0.6 + i * 0.4) * 1)
            spike_x = cx + spike_x_off
            spike_tip_x = spike_x + spike_sway
            spike_tip_y = cy + spike_base_y - spike_height
            _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["shadow_deep"], [
                (spike_x - 1, cy + spike_base_y),
                (spike_x + 2, cy + spike_base_y),
                (spike_tip_x + 1, spike_tip_y + 1),
            ])
            _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["hair_darkest"], [
                (spike_x - 1, cy + spike_base_y),
                (spike_x + 1, cy + spike_base_y),
                (spike_tip_x, spike_tip_y),
            ])
            _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["hair_dark"], [
                (spike_x, cy + spike_base_y),
                (spike_x + 1, cy + spike_base_y),
                (spike_tip_x, spike_tip_y),
            ])
            # FIX: Added 3rd point (spike_x + 1) so it forms a valid triangle
            _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["hair_mid"], [
                (spike_x, cy + spike_base_y - 1),
                (spike_x + 1, cy + spike_base_y - 1),
                (spike_tip_x, spike_tip_y),
            ])
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["hair_light"],
                             (spike_tip_x, spike_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["hair_shine"],
                             (spike_tip_x, spike_tip_y, 1, 1))
        # Fire ember at tip of tallest spike
        for spike_x_off, spike_base_y, spike_height in [(-1, -11, 7)]:
            spike_x = cx + spike_x_off
            spike_tip_y = cy + spike_base_y - spike_height
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_mid"],
                             (spike_x, spike_tip_y - 1, 1, 1))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_hot"],
                             (spike_x, spike_tip_y - 1, 1, 1))
    def _draw_goggles(surface, cx, cy, facing, phase):
        """Metal goggles on forehead."""
        # Goggle band
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["shadow_deep"],
                         (cx - 6, cy - 1, 12, 3))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                         (cx - 6, cy - 1, 12, 2))
        pygame.draw.rect(surface, _NS_ignakhor.PALETTE["metal_dark"],
                         (cx - 6, cy - 1, 12, 1))
        # Two goggle lenses
        for side in (-1, 1):
            lens_x = cx + side * 3
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["shadow_deep"],
                                   (lens_x, cy), 3)
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["gold_dark"],
                                   (lens_x, cy), 3)
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["gold_mid"],
                                   (lens_x, cy), 2)
            # Dark lens center
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                                   (lens_x, cy), 1)
            # Tech reflection
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["tech_light"],
                             (lens_x, cy, 1, 1))
            # Gold rim highlight
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["gold_shine"],
                             (lens_x - 1, cy - 2, 1, 1))
    def _draw_cyborg_eyes(surface, cx, cy, facing, phase, action):
        """Bright glowing yellow-orange eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        intensity = 1.5 if action == "attack" else 1.0
        for side in (-1, 1):
            ex = cx + side * 2 + (1 if facing == 1 else -1)
            ey = cy
            # Small socket
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["skin_darkest"],
                             (ex - 1, ey - 1, 3, 2))
            # Glow halo
            for radius in range(4, 0, -1):
                alpha = _NS_ignakhor._alpha(90 * (4 - radius) / 4 * pulse * intensity)
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["eye_mid"], alpha),
                                       (ex, ey), radius)
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["eye_dark"],
                             (ex - 1, ey, 3, 1))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["eye_mid"],
                             (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["eye_glow"],
                             (ex + 1, ey, 1, 1))
    # ============================================================
    # RANGED ATTACK - FIRE MISSILE PROJECTILE
    # ============================================================
    def _draw_missile_projectile(surface, boss, x, y, progress):
        """Fire missile with smoke trail."""
        if progress < 0.55:
            return
        facing = boss.direction
        tx, ty = _NS_ignakhor._target_position(boss, x, y)
        # Launch from cannon muzzle
        start_x = x + facing * 34
        start_y = y - 2
        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Missile trail (fire + smoke)
        for i in range(10):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_ignakhor._alpha(240 - i * 22)
            size = max(1, 8 - i)
            _NS_ignakhor._aacircle(surface,
                                   (*_NS_ignakhor.PALETTE["fire_darkest"], alpha),
                                   (px, py), size)
            _NS_ignakhor._aacircle(surface,
                                   (*_NS_ignakhor.PALETTE["fire_dark"], alpha),
                                   (px, py), max(1, size - 1))
            _NS_ignakhor._aacircle(surface,
                                   (*_NS_ignakhor.PALETTE["fire_mid"], alpha),
                                   (px, py), max(1, size - 2))
            _NS_ignakhor._aacircle(surface,
                                   (*_NS_ignakhor.PALETTE["fire_light"], alpha),
                                   (px, py), max(1, size - 3))
            # Smoke particles
            if i > 3:
                pygame.draw.rect(surface,
                                 (*_NS_ignakhor.PALETTE["metal_dark"], alpha),
                                 (px - 2, py - 2, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_ignakhor.PALETTE["metal_mid"], alpha),
                                 (px + 1, py + 1, 2, 2))
            # Sparks
            if i < 5:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface,
                                     (*_NS_ignakhor.PALETTE["fire_hot"], alpha),
                                     (spark_x, spark_y, 1, 1))
        # Missile HEAD - actual rocket shape
        # Direction of travel
        dx = tx - start_x
        dy = ty - start_y
        length = math.hypot(dx, dy)
        if length > 1:
            nx = dx / length
            ny = dy / length
            perp_x = -ny
            perp_y = nx
            # Missile body (cylindrical)
            body_len = 8
            body_a = (bx - int(nx * body_len) + int(perp_x * 2),
                      by - int(ny * body_len) + int(perp_y * 2))
            body_b = (bx - int(nx * body_len) - int(perp_x * 2),
                      by - int(ny * body_len) - int(perp_y * 2))
            body_c = (bx + int(perp_x * 2), by + int(perp_y * 2))
            body_d = (bx - int(perp_x * 2), by - int(perp_y * 2))
            _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["shadow_deep"], [
                (body_a[0] + 1, body_a[1] + 1),
                (body_c[0] + 1, body_c[1] + 1),
                (body_d[0] + 1, body_d[1] + 1),
                (body_b[0] + 1, body_b[1] + 1),
            ])
            _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                               [body_a, body_c, body_d, body_b])
            _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["metal_dark"],
                               [body_a, body_c, body_d, body_b])
            pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_mid"],
                             body_a, body_c, 1)
            pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_edge"],
                             (body_a[0] - int(perp_x), body_a[1] - int(perp_y)),
                             (body_c[0] - int(perp_x), body_c[1] - int(perp_y)), 1)
            # Nose cone (pointed tip)
            tip = (bx + int(nx * 5), by + int(ny * 5))
            _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                               [tip, body_c, body_d])
            _NS_ignakhor._poly(surface, _NS_ignakhor.PALETTE["fire_dark"],
                               [tip, (int((tip[0] + body_c[0]) / 2), int((tip[1] + body_c[1]) / 2)), body_c])
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_hot"],
                             (tip[0], tip[1], 1, 1))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_shine"],
                             (tip[0], tip[1], 1, 1))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["white"],
                             (tip[0], tip[1], 1, 1))
            # Rear fire jet
            rear_jet_end = (bx - int(nx * (body_len + 6)),
                            by - int(ny * (body_len + 6)))
            for r in range(5, 0, -1):
                alpha = _NS_ignakhor._alpha(200 * (5 - r) / 5)
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_mid"], alpha),
                                       ((body_a[0] + body_b[0]) // 2,
                                        (body_a[1] + body_b[1]) // 2), r)
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["fire_hot"],
                                   ((body_a[0] + body_b[0]) // 2,
                                    (body_a[1] + body_b[1]) // 2), 2)
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_shine"],
                             ((body_a[0] + body_b[0]) // 2,
                              (body_a[1] + body_b[1]) // 2, 1, 1))
        # Radial glow around missile head
        for r in range(10, 3, -2):
            alpha = _NS_ignakhor._alpha(80 * (10 - r) / 10)
            _NS_ignakhor._aacircle(surface,
                                   (*_NS_ignakhor.PALETTE["fire_light"], alpha),
                                   (bx, by), r)
        # IMPACT
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(12 + st * 26)
            alpha = _NS_ignakhor._alpha(240 * (1 - st))
            _NS_ignakhor._aacircle(surface,
                                   (*_NS_ignakhor.PALETTE["fire_darkest"], alpha),
                                   (tx, ty), radius + 3, 3)
            _NS_ignakhor._aacircle(surface,
                                   (*_NS_ignakhor.PALETTE["fire_dark"], alpha),
                                   (tx, ty), radius, 3)
            _NS_ignakhor._aacircle(surface,
                                   (*_NS_ignakhor.PALETTE["fire_mid"], alpha),
                                   (tx, ty), max(1, radius - 5), 2)
            _NS_ignakhor._aacircle(surface,
                                   (*_NS_ignakhor.PALETTE["fire_light"], alpha),
                                   (tx, ty), max(1, radius - 12), 1)
            # Explosion sparks
            for i in range(12):
                angle_s = i * math.pi / 6
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_ignakhor.PALETTE["fire_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_ignakhor.PALETTE["fire_shine"], alpha),
                                 (ex, ey, 1, 1))
            # Smoke rings
            for smoke_r in range(radius, 0, -6):
                s_alpha = _NS_ignakhor._alpha(150 * (1 - st))
                pygame.draw.ellipse(surface,
                                    (*_NS_ignakhor.PALETTE["metal_dark"], s_alpha),
                                    (tx - smoke_r, ty - smoke_r // 3,
                                     smoke_r * 2, smoke_r * 2 // 3), 2)
    # ============================================================
    # JET EXHAUST (ambient)
    # ============================================================
    def _draw_jet_exhaust(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        """Fire jet exhaust below floating cyborg."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((160, 55), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(38, 3, -3):
            alpha = _NS_ignakhor._alpha((38 - radius) * 2.2 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_ignakhor.PALETTE["fire_darkest"], alpha),
                    (80 - radius * 2, 27 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(24, 3, -2):
            alpha = _NS_ignakhor._alpha((24 - radius) * 3.4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_ignakhor.PALETTE["fire_dark"], alpha),
                    (80 - radius, 27 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 80, cy - 12))
        # Rising jet flames from feet
        for i in range(2):
            jet_x = cx + (i * 8) - 4
            for j in range(5):
                jet_t = (phase * 2 + j * 0.2) % 1.0
                jet_y = cy + 6 - int(jet_t * 25)
                jet_width = int(3 + (1 - jet_t) * 3)
                alpha = _NS_ignakhor._alpha(240 * (1 - jet_t) * strength)
                pygame.draw.ellipse(
                    surface,
                    (*_NS_ignakhor.PALETTE["fire_dark"], alpha),
                    (jet_x - jet_width, jet_y - 1,
                     jet_width * 2, 3),
                )
                pygame.draw.ellipse(
                    surface,
                    (*_NS_ignakhor.PALETTE["fire_mid"], alpha),
                    (jet_x - jet_width + 1, jet_y - 1,
                     jet_width * 2 - 2, 2),
                )
                pygame.draw.rect(surface,
                                 (*_NS_ignakhor.PALETTE["fire_hot"], alpha),
                                 (jet_x, jet_y - 1, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_ignakhor.PALETTE["fire_shine"], alpha),
                                 (jet_x, jet_y - 1, 1, 1))
        # Sparks / embers rising
        for i in range(10):
            ember_t = (phase * 0.7 + i * 0.15) % 1.0
            ex = cx - 28 + i * 6 + int(math.sin(phase + i) * 4)
            ey = cy + 4 - int(ember_t * 26)
            alpha = _NS_ignakhor._alpha(230 * (1 - ember_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface,
                                 (*_NS_ignakhor.PALETTE["fire_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_ignakhor.PALETTE["fire_shine"], alpha),
                                 (ex, ey, 1, 1))
        # Trail
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_ignakhor._alpha(160 - i * 22)
                if alpha <= 0:
                    continue
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_dark"], alpha),
                                       (sx, sy), max(2, 6 - i))
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_mid"], alpha),
                                       (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface,
                                 (*_NS_ignakhor.PALETTE["fire_hot"], alpha),
                                 (sx, sy - 1, 2, 2))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        hover_offset = int(math.sin(phase * 0.9) * 1)
        shadow = pygame.Surface((140, 28), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 14 - radius, 120 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (12, 6, 3, 170), (10, 8, 120, 12))
        pygame.draw.ellipse(shadow, (55, 25, 10, 110), (18, 10, 104, 8))
        surface.blit(shadow, (x - 70, y - 14 + hover_offset))
    def _draw_furnace_aura(surface, x, y, phase):
        """Orange furnace aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((230, 195), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_ignakhor._alpha((100 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_ignakhor._aacircle(aura,
                                       (*_NS_ignakhor.PALETTE["fire_darkest"], alpha),
                                       (115, 97), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_ignakhor._alpha((65 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_ignakhor._aacircle(aura,
                                       (*_NS_ignakhor.PALETTE["fire_dark"], alpha),
                                       (115, 97), radius)
        for radius in range(38, 5, -3):
            alpha = _NS_ignakhor._alpha((38 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_ignakhor._aacircle(aura,
                                       (*_NS_ignakhor.PALETTE["fire_mid"], alpha),
                                       (115, 97), radius)
        surface.blit(aura, (x - 115, y - 97))
        # Floating fire embers
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 42 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Fiery mechanical rune ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_ignakhor.PALETTE["fire_darkest"], 210),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_ignakhor.PALETTE["fire_dark"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_ignakhor.PALETTE["fire_mid"], 200),
                            (25, 22, 120, 18), 1)
        # Mechanical bolts/runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_ignakhor.PALETTE["fire_hot"], 230),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_ignakhor.PALETTE["fire_shine"],
                                 _NS_ignakhor._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # SKILL Q: FIRE MISSILE (enhanced ranged missile)
    # ============================================================
    def _draw_firemissile_foreground(surface, boss, x, y, timer, phase):
        """Bigger, faster fire missile."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_ignakhor._target_position(boss, x, y)
        if progress < 0.2:
            # Charge in cannon
            t = progress / 0.2
            muzzle_x = x + facing * 34
            muzzle_y = y - 2
            cr = int(4 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_ignakhor._alpha(220 * (cr + 5 - r) / (cr + 5))
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_darkest"], alpha),
                                       (muzzle_x, muzzle_y), r)
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["fire_dark"],
                                   (muzzle_x, muzzle_y), cr - 1)
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["fire_mid"],
                                   (muzzle_x, muzzle_y), max(1, cr - 3))
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["fire_hot"],
                                   (muzzle_x, muzzle_y), max(1, cr - 4))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_shine"],
                             (muzzle_x, muzzle_y, 1, 1))
        else:
            # Missile flies
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 36
            start_y = y - 2
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Extra bright trail
            for i in range(12):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_ignakhor._alpha(240 - i * 20)
                size = max(1, 9 - i)
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_darkest"], alpha),
                                       (px, py), size)
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_dark"], alpha),
                                       (px, py), max(1, size - 1))
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_mid"], alpha),
                                       (px, py), max(1, size - 2))
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_light"], alpha),
                                       (px, py), max(1, size - 3))
                # Sparks
                if i < 5:
                    for s in range(3):
                        spark_x = px + int(math.sin(t * 8 + i + s) * (size + 2))
                        spark_y = py + int(math.cos(t * 8 + i + s) * (size + 2))
                        pygame.draw.rect(surface,
                                         (*_NS_ignakhor.PALETTE["fire_hot"], alpha),
                                         (spark_x, spark_y, 1, 1))
            # Huge bright missile head
            for r in range(15, 3, -2):
                alpha = _NS_ignakhor._alpha(100 * (15 - r) / 15)
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_light"], alpha),
                                       (bx, by), r)
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["fire_darkest"],
                                   (bx, by), 10)
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["fire_dark"],
                                   (bx, by), 8)
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["fire_mid"],
                                   (bx, by), 5)
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["fire_light"],
                                   (bx, by), 3)
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["fire_shine"],
                                   (bx, by), 1)
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["white"], (bx, by, 1, 1))
            # Big impact
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(15 + st * 30)
                alpha = _NS_ignakhor._alpha(240 * (1 - st))
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_darkest"], alpha),
                                       (tx, ty), radius + 4, 3)
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_dark"], alpha),
                                       (tx, ty), radius, 3)
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_mid"], alpha),
                                       (tx, ty), max(1, radius - 5), 2)
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_light"], alpha),
                                       (tx, ty), max(1, radius - 12), 1)
                for i in range(14):
                    angle_s = i * math.pi / 7
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_ignakhor.PALETTE["fire_hot"], alpha),
                                     (ex, ey, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_ignakhor.PALETTE["fire_shine"], alpha),
                                     (ex, ey, 1, 1))
                # Smoke rings expanding
                for smoke_r in range(radius, 0, -8):
                    s_alpha = _NS_ignakhor._alpha(120 * (1 - st))
                    pygame.draw.ellipse(surface,
                                        (*_NS_ignakhor.PALETTE["metal_dark"], s_alpha),
                                        (tx - smoke_r, ty - smoke_r // 3,
                                         smoke_r * 2, smoke_r * 2 // 3), 2)
    # ============================================================
    # SKILL W: FIRE STAKE (thrown stake trap)
    # ============================================================
    def _draw_firestake_ground(surface, boss, x, y, timer, phase):
        """Ground pool at target where stake lands."""
        tx, ty = _NS_ignakhor._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Only show after stake lands
        if progress > 0.4:
            r = int(45 * min(1.0, (progress - 0.4) / 0.6 * 3))
            if r > 3:
                pygame.draw.ellipse(surface,
                                    (*_NS_ignakhor.PALETTE["fire_darkest"], 220),
                                    (tx - r, ty - r // 3, r * 2, r * 2 // 3))
                pygame.draw.ellipse(surface,
                                    (*_NS_ignakhor.PALETTE["fire_dark"], 200),
                                    (tx - r + 3, ty - r // 3 + 2,
                                     r * 2 - 6, r * 2 // 3 - 4))
                pygame.draw.ellipse(surface,
                                    (*_NS_ignakhor.PALETTE["fire_mid"], 150),
                                    (tx - r + 8, ty - r // 3 + 4,
                                     r * 2 - 16, r * 2 // 3 - 8))
    def _draw_firestake_foreground(surface, boss, x, y, timer, phase):
        """Flying stake + explosion."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_ignakhor._target_position(boss, x, y)
        if progress < 0.4:
            # Stake flying to target
            t = progress / 0.4
            start_x = x + facing * 20
            start_y = y - 8
            # Arc trajectory
            mid_x = int((start_x + tx) / 2)
            mid_y = int(min(start_y, ty) - 40)
            bx = int((1 - t) ** 2 * start_x + 2 * (1 - t) * t * mid_x + t ** 2 * tx)
            by = int((1 - t) ** 2 * start_y + 2 * (1 - t) * t * mid_y + t ** 2 * ty)
            # Direction of stake (rotate)
            spin_angle = t * math.pi * 4
            perp_x = math.cos(spin_angle)
            perp_y = math.sin(spin_angle)
            # Stake shape (small cylinder)
            stake_a = (bx + int(perp_x * 4), by + int(perp_y * 4))
            stake_b = (bx - int(perp_x * 4), by - int(perp_y * 4))
            pygame.draw.line(surface, _NS_ignakhor.PALETTE["shadow_deep"],
                             (stake_a[0] + 1, stake_a[1] + 1),
                             (stake_b[0] + 1, stake_b[1] + 1), 5)
            pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                             stake_a, stake_b, 4)
            pygame.draw.line(surface, _NS_ignakhor.PALETTE["rust_dark"],
                             stake_a, stake_b, 3)
            pygame.draw.line(surface, _NS_ignakhor.PALETTE["rust_mid"],
                             stake_a, stake_b, 2)
            pygame.draw.line(surface, _NS_ignakhor.PALETTE["rust_light"],
                             stake_a, stake_b, 1)
            # Fire on stake tip
            for r in range(4, 0, -1):
                alpha = _NS_ignakhor._alpha(200 * (4 - r) / 4)
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_mid"], alpha),
                                       stake_a, r)
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_hot"],
                             (stake_a[0], stake_a[1], 1, 1))
            # Trail (small)
            for i in range(3):
                trail_t = t - i * 0.08
                if trail_t < 0:
                    continue
                px = int((1 - trail_t) ** 2 * start_x + 2 * (1 - trail_t) * trail_t * mid_x + trail_t ** 2 * tx)
                py = int((1 - trail_t) ** 2 * start_y + 2 * (1 - trail_t) * trail_t * mid_y + trail_t ** 2 * ty)
                alpha = _NS_ignakhor._alpha(180 - i * 50)
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_dark"], alpha),
                                       (px, py), 3)
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_mid"], alpha),
                                       (px, py), 2)
                pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_hot"],
                                 (px, py, 1, 1))
        else:
            # STAKE PLANTED at target - explosion + burning
            t = (progress - 0.4) / 0.6
            # Planted stake (vertical)
            stake_top_y = ty - 8
            pygame.draw.line(surface, _NS_ignakhor.PALETTE["shadow_deep"],
                             (tx + 1, stake_top_y + 1), (tx + 1, ty + 1), 5)
            pygame.draw.line(surface, _NS_ignakhor.PALETTE["metal_darkest"],
                             (tx, stake_top_y), (tx, ty), 4)
            pygame.draw.line(surface, _NS_ignakhor.PALETTE["rust_dark"],
                             (tx, stake_top_y), (tx, ty), 3)
            pygame.draw.line(surface, _NS_ignakhor.PALETTE["rust_mid"],
                             (tx, stake_top_y), (tx, ty), 2)
            pygame.draw.line(surface, _NS_ignakhor.PALETTE["rust_light"],
                             (tx, stake_top_y), (tx, ty), 1)
            # Fire on top of stake (constant)
            fire_pulse = math.sin(phase * 4) * 0.3 + 0.7
            for r in range(8, 0, -1):
                alpha = _NS_ignakhor._alpha(200 * (8 - r) / 8 * fire_pulse)
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_dark"], alpha),
                                       (tx, stake_top_y - 3), r)
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["fire_mid"],
                                   (tx, stake_top_y - 3), 4)
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["fire_hot"],
                                   (tx, stake_top_y - 3), 2)
            _NS_ignakhor._aacircle(surface, _NS_ignakhor.PALETTE["fire_shine"],
                                   (tx, stake_top_y - 3), 1)
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["white"],
                             (tx, stake_top_y - 3, 1, 1))
            # Rising flames from stake
            for i in range(6):
                flame_t = (phase * 1.5 + i * 0.16) % 1.0
                flame_y = stake_top_y - int(flame_t * 18)
                flame_x = tx + int(math.sin(phase + i) * 2)
                alpha = _NS_ignakhor._alpha(220 * (1 - flame_t))
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_dark"], alpha),
                                       (flame_x, flame_y), 2)
                pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_hot"],
                                 (flame_x, flame_y, 1, 1))
            # Impact explosion (first frame)
            if t < 0.2:
                exp_t = t / 0.2
                radius = int(15 + exp_t * 20)
                alpha = _NS_ignakhor._alpha(240 * (1 - exp_t))
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_dark"], alpha),
                                       (tx, ty), radius, 2)
                _NS_ignakhor._aacircle(surface,
                                       (*_NS_ignakhor.PALETTE["fire_mid"], alpha),
                                       (tx, ty), max(1, radius - 5), 1)
                for i in range(8):
                    a = i * math.pi / 4
                    ex = tx + int(math.cos(a) * radius)
                    ey = ty + int(math.sin(a) * radius * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_ignakhor.PALETTE["fire_hot"], alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL E: FIRE SPIN (spinning AoE)
    # ============================================================
    def _draw_firespin_ground(surface, boss, x, y, timer, phase):
        """Fire ring on ground while spinning."""
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(50 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_ignakhor.PALETTE["fire_darkest"], 220),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 4)
            pygame.draw.ellipse(surface,
                                (*_NS_ignakhor.PALETTE["fire_dark"], 200),
                                (x - r + 4, y + 40 - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_ignakhor.PALETTE["fire_mid"], 220),
                                (x - r + 10, y + 40 - r // 3 + 5,
                                 r * 2 - 20, r * 2 // 3 - 10), 2)
    def _draw_firespin_foreground(surface, boss, x, y, timer, phase):
        """Spinning fire spiral around boss."""
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))
        radius = int(45 * min(1.0, progress * 3))
        # Fast spinning fire slashes
        spin_speed = 10
        num_slashes = 8
        for i in range(num_slashes):
            base_angle = phase * spin_speed + i * (math.pi * 2 / num_slashes)
            for sub in range(4):
                angle = base_angle + sub * 0.2
                inner_x = x + int(math.cos(angle) * (radius - 12))
                inner_y = y - 4 + int(math.sin(angle) * (radius - 12) * 0.6)
                outer_x = x + int(math.cos(angle) * (radius + 6))
                outer_y = y - 4 + int(math.sin(angle) * (radius + 6) * 0.6)
                alpha = _NS_ignakhor._alpha(240 - sub * 60)
                # Fire arc
                pygame.draw.line(surface,
                                 (*_NS_ignakhor.PALETTE["fire_darkest"], alpha),
                                 (inner_x, inner_y), (outer_x, outer_y), 4)
                pygame.draw.line(surface,
                                 (*_NS_ignakhor.PALETTE["fire_dark"], alpha),
                                 (inner_x, inner_y), (outer_x, outer_y), 3)
                pygame.draw.line(surface,
                                 (*_NS_ignakhor.PALETTE["fire_mid"], alpha),
                                 (inner_x, inner_y), (outer_x, outer_y), 2)
                pygame.draw.line(surface,
                                 (*_NS_ignakhor.PALETTE["fire_light"], alpha),
                                 (inner_x, inner_y), (outer_x, outer_y), 1)
                # Sparks at tip
                pygame.draw.rect(surface,
                                 (*_NS_ignakhor.PALETTE["fire_hot"], alpha),
                                 (outer_x, outer_y, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_ignakhor.PALETTE["fire_shine"], alpha),
                                 (outer_x, outer_y, 1, 1))
        # Ring of fire particles orbiting
        for i in range(20):
            angle = -phase * 5 + i * math.pi / 10
            dx = x + int(math.cos(angle) * radius)
            dy = y - 4 + int(math.sin(angle) * radius * 0.6)
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_dark"], (dx, dy, 2, 2))
            pygame.draw.rect(surface, _NS_ignakhor.PALETTE["fire_hot"], (dx, dy, 1, 1))
    # ============================================================
    # SKILL R: LAST INSANITY (berserker mode)
    # ============================================================
    def _draw_lastinsanity_ground(surface, boss, x, y, timer, phase):
        """Massive burning ring on ground."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(80 * min(1.0, progress * 2))
        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_ignakhor.PALETTE["fire_darkest"], 230),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 5)
            pygame.draw.ellipse(surface,
                                (*_NS_ignakhor.PALETTE["fire_dark"], 220),
                                (x - r + 5, y + 40 - r // 3 + 2,
                                 r * 2 - 10, r * 2 // 3 - 4), 4)
            pygame.draw.ellipse(surface,
                                (*_NS_ignakhor.PALETTE["fire_mid"], 230),
                                (x - r + 10, y + 40 - r // 3 + 5,
                                 r * 2 - 20, r * 2 // 3 - 10), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_ignakhor.PALETTE["fire_hot"], 200),
                                (x - r + 18, y + 40 - r // 3 + 9,
                                 r * 2 - 36, r * 2 // 3 - 18), 2)
            # Cracks glowing
            for i in range(12):
                angle = phase * 0.4 + i * math.pi / 6
                x1 = x + int(math.cos(angle) * r)
                y1 = y + 40 + int(math.sin(angle) * r * 0.4)
                x2 = x + int(math.cos(angle) * (r - 15))
                y2 = y + 40 + int(math.sin(angle) * (r - 15) * 0.4)
                pygame.draw.line(surface, _NS_ignakhor.PALETTE["fire_shine"],
                                 (x1, y1), (x2, y2), 2)
    def _draw_lastinsanity_aura(surface, boss, x, y, timer, phase):
        """Berserker fire aura around body."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Body flame aura (surrounds boss)
        aura_r = 55 + int(math.sin(phase * 4) * 6)
        aura_surf = pygame.Surface((aura_r * 2 + 20, aura_r * 2 + 20), pygame.SRCALPHA)
        center = (aura_r + 10, aura_r + 10)
        for r in range(aura_r, 3, -3):
            alpha = _NS_ignakhor._alpha(140 * (aura_r - r) / aura_r)
            _NS_ignakhor._aacircle(aura_surf,
                                   (*_NS_ignakhor.PALETTE["fire_dark"], alpha),
                                   center, r)
        surface.blit(aura_surf, (x - aura_r - 10, y - aura_r - 10 - 5))


# ====================================================================
# KAZURETH (THUNDER WIELDER) - Mini Boss
# ====================================================================

class _NS_kazureth:
    """Namespace kazureth - Thunder Wielder boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin tones
        "skin_shadow": (140, 100, 75),
        "skin_dark": (210, 160, 120),
        "skin_mid": (240, 195, 150),
        "skin_light": (255, 220, 180),
        "skin_shine": (255, 240, 215),
        # Yellow blonde hair
        "hair_darkest": (100, 60, 10),
        "hair_dark": (180, 120, 20),
        "hair_mid": (240, 190, 40),
        "hair_light": (255, 225, 90),
        "hair_shine": (255, 250, 180),
        # Orange/yellow haori (kimono jacket)
        "haori_darkest": (110, 60, 5),
        "haori_dark": (180, 110, 15),
        "haori_mid": (235, 155, 30),
        "haori_light": (255, 200, 70),
        "haori_shine": (255, 235, 140),
        "haori_pattern": (100, 50, 5),  # dark pattern lines
        # Black kimono under haori
        "kimono_darkest": (5, 5, 8),
        "kimono_dark": (20, 20, 28),
        "kimono_mid": (45, 45, 55),
        "kimono_light": (75, 75, 88),
        # Katana (silver/steel)
        "steel_darkest": (30, 35, 45),
        "steel_dark": (80, 90, 105),
        "steel_mid": (150, 160, 175),
        "steel_light": (210, 218, 230),
        "steel_shine": (250, 252, 255),
        # Hilt (dark wrap)
        "hilt_dark": (25, 15, 10),
        "hilt_mid": (60, 40, 25),
        "hilt_wrap": (140, 100, 50),
        # Lightning yellow (core theme!)
        "light_darkest": (100, 70, 5),
        "light_dark": (180, 130, 15),
        "light_mid": (250, 200, 30),
        "light_bright": (255, 235, 100),
        "light_hot": (255, 250, 180),
        "light_shine": (255, 255, 240),
        # Electric blue-white accent
        "elec_dark": (60, 100, 180),
        "elec_mid": (150, 200, 255),
        "elec_light": (220, 240, 255),
        # Storm cloud (grey)
        "cloud_darkest": (30, 30, 40),
        "cloud_dark": (60, 60, 75),
        "cloud_mid": (100, 100, 115),
        "cloud_light": (150, 150, 165),
        # Eyes (golden)
        "eye_dark": (80, 40, 5),
        "eye_mid": (200, 140, 20),
        "eye_light": (255, 220, 80),
        "eye_shine": (255, 250, 200),
        # Dragon (for R skill)
        "drag_darkest": (100, 60, 0),
        "drag_dark": (200, 130, 10),
        "drag_mid": (255, 200, 30),
        "drag_light": (255, 235, 100),
        "drag_shine": (255, 255, 200),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kazureth._clamp(color)
        if _NS_kazureth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_kazureth._clamp(color)
        if _NS_kazureth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_kazureth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    def _draw_lightning_bolt(surface, start, end, color, width=2,
                             segments=6, jitter=6, alpha=255):
        """Draw jagged lightning bolt between two points."""
        color = (*_NS_kazureth._clamp(color), _NS_kazureth._alpha(alpha))
        sx, sy = start
        ex, ey = end
        pts = [(sx, sy)]
        for i in range(1, segments):
            t = i / segments
            mx = sx + (ex - sx) * t
            my = sy + (ey - sy) * t
            # Perpendicular jitter
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
    def draw_kazureth(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kazureth._detect_moving(boss)
        _NS_kazureth._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_kaz_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient behind
        _NS_kazureth._draw_thunder_aura(surface, x, y, pulse)
        _NS_kazureth._draw_ground_ring(surface, x, y + 46, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "e":
            _NS_kazureth._draw_distant_thunder_ground(surface, boss, x, y,
                                                     skill_timer, pulse)
        elif active_skill == "q":
            _NS_kazureth._draw_thunderclap_ground(surface, boss, x, y,
                                                 skill_timer, pulse)
        # Floating bob
        float_bob = int(math.sin(pulse * 0.6) * 3)
        # Handle Q dash (body appears at destination during dash)
        show_body = True
        body_x_offset = 0
        if active_skill == "q":
            duration = 55
            q_prog = max(0.0, min(1.0, 1 - skill_timer / duration))
            if 0.25 < q_prog < 0.55:
                # Dashing - body moves toward target
                dash_t = (q_prog - 0.25) / 0.3
                tx, ty = _NS_kazureth._target_position(boss, x, y)
                body_x_offset = int((tx - x - boss.direction * 40) * dash_t)
        # Body (always floating)
        if show_body:
            actual_x = x + body_x_offset
            if attacking:
                _NS_kazureth._draw_body_attack(surface, boss, actual_x, y + float_bob)
            elif moving:
                _NS_kazureth._draw_body_walk(surface, boss, actual_x, y + float_bob)
            else:
                _NS_kazureth._draw_body_idle(surface, boss, actual_x, y + float_bob)
        # W - Lightning cloak (over body)
        if active_skill == "w":
            _NS_kazureth._draw_lightning_cloak(surface, boss, x + body_x_offset,
                                              y + float_bob, skill_timer, pulse)
        # Foreground FX
        if active_skill == "q":
            _NS_kazureth._draw_thunderclap_skill(surface, boss, x, y,
                                                skill_timer, pulse)
        elif active_skill == "e":
            _NS_kazureth._draw_distant_thunder_skill(surface, boss, x, y,
                                                    skill_timer, pulse)
        elif active_skill == "r":
            _NS_kazureth._draw_honoikazuchi_skill(surface, boss, x, y,
                                                 skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kaz_previous_timer", 0))
        active = bool(getattr(boss, "_kaz_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._kaz_attack_active = True
            boss._kaz_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._kaz_attack_frame = int(getattr(boss, "_kaz_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._kaz_attack_active = False
            boss._kaz_attack_frame = 0
            active = False
        boss._kaz_previous_timer = timer
        boss._kaz_attack_progress = (
            min(1.0, getattr(boss, "_kaz_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_kaz_last_x"):
            boss._kaz_last_x = boss.x
            boss._kaz_last_y = boss.y
            return False
        dx = abs(boss.x - boss._kaz_last_x)
        dy = abs(boss.y - boss._kaz_last_y)
        boss._kaz_last_x = boss.x
        boss._kaz_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        _NS_kazureth._draw_shadow(surface, x, y + 50)
        _NS_kazureth._draw_thunder_mist(surface, x, y + 44, boss.pulse)
        _NS_kazureth._draw_body(surface, x, y, boss.direction, boss.pulse, "idle")
    def _draw_body_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_kazureth._draw_shadow(surface, x + sway, y + 50)
        _NS_kazureth._draw_thunder_mist(surface, x + sway, y + 44, phase,
                                       trail=True, facing=boss.direction)
        _NS_kazureth._draw_body(surface, x + sway, y, boss.direction, phase, "walk")
    def _draw_body_attack(surface, boss, x, y):
        progress = getattr(boss, "_kaz_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Melee slash motion
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 5) * boss.direction
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-5 + t * 15)) * boss.direction
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(10 * (1 - t)) * boss.direction
        _NS_kazureth._draw_shadow(surface, x + lunge, y + 50)
        _NS_kazureth._draw_thunder_mist(surface, x + lunge, y + 44, boss.pulse,
                                       intense=True)
        _NS_kazureth._draw_body(surface, x + lunge, y, boss.direction, boss.pulse,
                               "attack", progress)
        _NS_kazureth._draw_katana_slash(surface, boss, x + lunge, y, progress)
    # ============================================================
    # BODY DRAWING
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw ninja body with haori, katana, blonde hair."""
        # Order: back arm → body/haori → katana + front arm → head → hair
        arm_swing = 0
        if action == "attack":
            if attack_progress < 0.35:
                arm_swing = -int(attack_progress / 0.35 * 12) * facing
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                arm_swing = int((-12 + t * 34)) * facing
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_swing = int(22 * (1 - t)) * facing
        # Back arm
        _NS_kazureth._draw_arm(surface, cx - facing * 6, cy - 4, facing, phase,
                              -arm_swing // 2, back=True)
        # Body (kimono + haori)
        _NS_kazureth._draw_haori(surface, cx, cy, facing, phase, action)
        # Front arm holding katana
        _NS_kazureth._draw_arm_with_katana(surface, cx + facing * 4, cy - 4, facing,
                                          phase, arm_swing, action, attack_progress)
        # Head
        _NS_kazureth._draw_head(surface, cx, cy - 22, facing, phase, action)
        # Hair (blonde spiky)
        _NS_kazureth._draw_hair(surface, cx, cy - 22, facing, phase)
    def _draw_haori(surface, cx, cy, facing, phase, action):
        """Orange/yellow haori (kimono jacket) with black pattern."""
        sway = math.sin(phase * 0.7) * 1
        # Main haori shape
        haori_shape = [
            (cx - 13, cy - 8),
            (cx - 15, cy - 2),
            (cx - 17, cy + 8),
            (cx - 18, cy + 20),
            (cx - 15 + int(sway), cy + 28),
            (cx - 6, cy + 32),
            (cx + 6, cy + 32),
            (cx + 15 + int(sway), cy + 28),
            (cx + 18, cy + 20),
            (cx + 17, cy + 8),
            (cx + 15, cy - 2),
            (cx + 13, cy - 8),
        ]
        # Shadow
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["shadow_deep"],
                          [(px + 2, py + 3) for px, py in haori_shape])
        # Base dark
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["haori_darkest"], haori_shape)
        # Mid orange
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["haori_dark"], [
            (cx - 12, cy - 7),
            (cx - 14, cy - 1),
            (cx - 16, cy + 8),
            (cx - 17, cy + 18),
            (cx - 13, cy + 26),
            (cx - 4, cy + 30),
            (cx + 4, cy + 30),
            (cx + 13, cy + 26),
            (cx + 17, cy + 18),
            (cx + 16, cy + 8),
            (cx + 14, cy - 1),
            (cx + 12, cy - 7),
        ])
        # Bright orange main
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["haori_mid"], [
            (cx - 10, cy - 5),
            (cx - 12, cy + 2),
            (cx - 14, cy + 12),
            (cx - 12, cy + 22),
            (cx - 4, cy + 26),
            (cx + 4, cy + 26),
            (cx + 12, cy + 22),
            (cx + 14, cy + 12),
            (cx + 12, cy + 2),
            (cx + 10, cy - 5),
        ])
        # Highlights (folds)
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["haori_light"], [
            (cx - 6, cy - 2),
            (cx - 8, cy + 6),
            (cx - 8, cy + 18),
            (cx - 4, cy + 22),
            (cx + 4, cy + 22),
            (cx + 8, cy + 18),
            (cx + 8, cy + 6),
            (cx + 6, cy - 2),
        ])
        pygame.draw.line(surface, _NS_kazureth.PALETTE["haori_shine"],
                        (cx - 4, cy + 2), (cx - 4, cy + 16), 1)
        pygame.draw.line(surface, _NS_kazureth.PALETTE["haori_shine"],
                        (cx + 4, cy + 2), (cx + 4, cy + 16), 1)
        # Black inner kimono (visible in center opening)
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["kimono_darkest"], [
            (cx - 3, cy - 4),
            (cx - 4, cy + 4),
            (cx - 3, cy + 20),
            (cx + 3, cy + 20),
            (cx + 4, cy + 4),
            (cx + 3, cy - 4),
        ])
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["kimono_dark"], [
            (cx - 2, cy - 3),
            (cx - 3, cy + 4),
            (cx - 2, cy + 18),
            (cx + 2, cy + 18),
            (cx + 3, cy + 4),
            (cx + 2, cy - 3),
        ])
        # Kimono highlight
        pygame.draw.line(surface, _NS_kazureth.PALETTE["kimono_light"],
                        (cx, cy - 2), (cx, cy + 16), 1)
        # Obi/belt (black band at waist)
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["kimono_darkest"], [
            (cx - 14, cy + 18),
            (cx - 15, cy + 22),
            (cx + 15, cy + 22),
            (cx + 14, cy + 18),
        ])
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["kimono_dark"], [
            (cx - 13, cy + 19),
            (cx - 14, cy + 21),
            (cx + 14, cy + 21),
            (cx + 13, cy + 19),
        ])
        pygame.draw.line(surface, _NS_kazureth.PALETTE["kimono_mid"],
                        (cx - 12, cy + 20), (cx + 12, cy + 20), 1)
        # Haori bottom hem (darker)
        pygame.draw.line(surface, _NS_kazureth.PALETTE["haori_darkest"],
                        (cx - 16, cy + 26), (cx + 16, cy + 26), 1)
        # BLACK PATTERN (triangle/mountain motif on haori)
        # Triangles on lower haori
        for x_off in (-13, -8, 8, 13):
            tri_x = cx + x_off
            tri_y = cy + 25
            _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["haori_pattern"], [
                (tri_x - 3, tri_y + 3),
                (tri_x, tri_y - 2),
                (tri_x + 3, tri_y + 3),
            ])
            _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["kimono_darkest"], [
                (tri_x - 2, tri_y + 2),
                (tri_x, tri_y - 1),
                (tri_x + 2, tri_y + 2),
            ])
        # Lightning bolt patterns on shoulders
        for side_mult in (-1, 1):
            bolt_x = cx + 10 * side_mult
            # Small lightning zigzag
            pygame.draw.line(surface, _NS_kazureth.PALETTE["haori_pattern"],
                            (bolt_x, cy - 6), (bolt_x + side_mult, cy - 3), 1)
            pygame.draw.line(surface, _NS_kazureth.PALETTE["haori_pattern"],
                            (bolt_x + side_mult, cy - 3), (bolt_x - side_mult, cy), 1)
            pygame.draw.line(surface, _NS_kazureth.PALETTE["haori_pattern"],
                            (bolt_x - side_mult, cy), (bolt_x + side_mult * 2, cy + 3), 1)
        # Legs (visible below obi, black hakama pants)
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["kimono_darkest"], [
            (cx - 10, cy + 22),
            (cx - 11, cy + 32),
            (cx - 7, cy + 33),
            (cx - 5, cy + 22),
        ])
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["kimono_darkest"], [
            (cx + 5, cy + 22),
            (cx + 7, cy + 33),
            (cx + 11, cy + 32),
            (cx + 10, cy + 22),
        ])
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["kimono_dark"], [
            (cx - 9, cy + 23),
            (cx - 10, cy + 31),
            (cx - 7, cy + 31),
            (cx - 6, cy + 23),
        ])
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["kimono_dark"], [
            (cx + 6, cy + 23),
            (cx + 7, cy + 31),
            (cx + 10, cy + 31),
            (cx + 9, cy + 23),
        ])
        # Leg highlight
        pygame.draw.line(surface, _NS_kazureth.PALETTE["kimono_mid"],
                        (cx - 8, cy + 25), (cx - 8, cy + 30), 1)
        pygame.draw.line(surface, _NS_kazureth.PALETTE["kimono_mid"],
                        (cx + 8, cy + 25), (cx + 8, cy + 30), 1)
    def _draw_arm(surface, cx, cy, facing, phase, swing, back=False):
        """Draw arm with haori sleeve."""
        base_angle = math.pi * 0.5 + math.radians(swing)
        if back:
            base_angle = math.pi * 0.55
        shoulder_x = cx
        shoulder_y = cy
        elbow_len = 10
        elbow_x = shoulder_x + int(math.cos(base_angle) * elbow_len * facing * 0.3)
        elbow_y = shoulder_y + int(math.sin(base_angle) * elbow_len)
        hand_len = 12
        hand_angle = base_angle - math.radians(swing * 0.6)
        hand_x = elbow_x + int(math.cos(hand_angle) * hand_len * facing * 0.5)
        hand_y = elbow_y + int(math.sin(hand_angle) * hand_len)
        thickness = 6 if not back else 5
        color_main = _NS_kazureth.PALETTE["haori_darkest"] if back \
            else _NS_kazureth.PALETTE["haori_dark"]
        color_mid = _NS_kazureth.PALETTE["haori_dark"] if back \
            else _NS_kazureth.PALETTE["haori_mid"]
        color_light = _NS_kazureth.PALETTE["haori_light"]
        # Shadow
        _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 2),
                            (elbow_x + 1, elbow_y + 2), thickness + 1)
        # Upper arm
        _NS_kazureth._aaline(surface, color_main,
                            (shoulder_x, shoulder_y),
                            (elbow_x, elbow_y), thickness)
        _NS_kazureth._aaline(surface, color_mid,
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), max(1, thickness - 3))
        if not back:
            _NS_kazureth._aaline(surface, color_light,
                                (shoulder_x, shoulder_y - 2),
                                (elbow_x, elbow_y - 2), max(1, thickness - 5))
        # Forearm
        _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 2),
                            (hand_x + 1, hand_y + 2), thickness)
        _NS_kazureth._aaline(surface, color_main,
                            (elbow_x, elbow_y),
                            (hand_x, hand_y), thickness - 1)
        _NS_kazureth._aaline(surface, color_mid,
                            (elbow_x, elbow_y - 1),
                            (hand_x, hand_y - 1), max(1, thickness - 3))
        # Sleeve cuff (wide)
        cuff_perp_x = -math.sin(hand_angle) * 3
        cuff_perp_y = math.cos(hand_angle) * 3
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["haori_darkest"], [
            (hand_x - int(cuff_perp_x), hand_y - int(cuff_perp_y)),
            (hand_x + int(cuff_perp_x), hand_y + int(cuff_perp_y)),
            (hand_x + int(cuff_perp_x) - facing * 2,
             hand_y + int(cuff_perp_y) + 2),
            (hand_x - int(cuff_perp_x) - facing * 2,
             hand_y - int(cuff_perp_y) + 2),
        ])
        # Hand (skin)
        if not back:
            _NS_kazureth._aacircle(surface, _NS_kazureth.PALETTE["shadow_deep"],
                                  (hand_x + 1, hand_y + 1), 3)
            _NS_kazureth._aacircle(surface, _NS_kazureth.PALETTE["skin_shadow"],
                                  (hand_x, hand_y), 3)
            _NS_kazureth._aacircle(surface, _NS_kazureth.PALETTE["skin_dark"],
                                  (hand_x, hand_y), 2)
            _NS_kazureth._aacircle(surface, _NS_kazureth.PALETTE["skin_mid"],
                                  (hand_x - 1, hand_y - 1), 1)
    def _draw_arm_with_katana(surface, cx, cy, facing, phase, swing, action,
                              attack_progress):
        """Draw front arm holding katana with slash animation."""
        base_angle = math.pi * 0.5 + math.radians(swing)
        shoulder_x = cx
        shoulder_y = cy
        elbow_len = 11
        elbow_x = shoulder_x + int(math.cos(base_angle) * elbow_len * facing * 0.3)
        elbow_y = shoulder_y + int(math.sin(base_angle) * elbow_len)
        hand_len = 14
        hand_angle = base_angle - math.radians(swing * 0.6)
        hand_x = elbow_x + int(math.cos(hand_angle) * hand_len * facing * 0.5)
        hand_y = elbow_y + int(math.sin(hand_angle) * hand_len)
        # Extended hand for slash
        if action == "attack" and attack_progress > 0.35:
            hand_x = cx + facing * (10 + int(attack_progress * 12))
            hand_y = cy + 2 - int(math.sin(attack_progress * math.pi) * 6)
        # Sleeve (haori arm)
        thickness = 6
        _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["shadow_deep"],
                            (shoulder_x + 1, shoulder_y + 2),
                            (elbow_x + 1, elbow_y + 2), thickness + 1)
        _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["haori_dark"],
                            (shoulder_x, shoulder_y),
                            (elbow_x, elbow_y), thickness)
        _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["haori_mid"],
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), max(1, thickness - 3))
        _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["haori_light"],
                            (shoulder_x, shoulder_y - 2),
                            (elbow_x, elbow_y - 2), max(1, thickness - 5))
        # Forearm
        _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 2),
                            (hand_x + 1, hand_y + 2), thickness)
        _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["haori_dark"],
                            (elbow_x, elbow_y),
                            (hand_x, hand_y), thickness - 1)
        _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["haori_mid"],
                            (elbow_x, elbow_y - 1),
                            (hand_x, hand_y - 1), max(1, thickness - 3))
        # Hand
        _NS_kazureth._aacircle(surface, _NS_kazureth.PALETTE["shadow_deep"],
                              (hand_x + 1, hand_y + 1), 3)
        _NS_kazureth._aacircle(surface, _NS_kazureth.PALETTE["skin_shadow"],
                              (hand_x, hand_y), 3)
        _NS_kazureth._aacircle(surface, _NS_kazureth.PALETTE["skin_dark"],
                              (hand_x, hand_y), 2)
        # KATANA
        _NS_kazureth._draw_katana(surface, hand_x, hand_y, facing, phase, action,
                                 attack_progress, hand_angle)
    def _draw_katana(surface, hand_x, hand_y, facing, phase, action, progress,
                     hand_angle):
        """Draw katana sword from hand - FIXED: proper top-down swing angle."""
        # Katana angle based on action
        if action == "attack":
            if progress < 0.35:
                # Wind up - katana RAISED HIGH above head (pointing up-back)
                # angle points from hand upward-backward
                sword_angle = -math.pi * 0.85  # nearly straight up, slightly back
            elif progress < 0.6:
                # Swing DOWN from top to forward-down
                t = (progress - 0.35) / 0.25
                start_a = -math.pi * 0.85     # top
                end_a = math.pi * 0.25         # forward-down
                sword_angle = start_a + (end_a - start_a) * t
            else:
                # Recovery - katana held forward-down after slash
                t = (progress - 0.6) / 0.4
                sword_angle = math.pi * 0.25 - t * 0.2
        else:
            # Idle - katana held forward at ready
            sword_angle = -math.pi * 0.15  # slightly angled up-forward
            sword_angle += math.sin(phase * 0.5) * 0.05
        # For facing left, mirror the horizontal component
        cos_a = math.cos(sword_angle) * facing
        sin_a = math.sin(sword_angle)
        # Hilt
        hilt_len = 6
        hilt_end_x = hand_x + int(cos_a * hilt_len)
        hilt_end_y = hand_y + int(sin_a * hilt_len)
        _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["hilt_dark"],
                            (hand_x, hand_y), (hilt_end_x, hilt_end_y), 4)
        _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["hilt_mid"],
                            (hand_x, hand_y), (hilt_end_x, hilt_end_y), 3)
        # Wrap pattern
        for i in range(3):
            wrap_t = (i + 1) / 4
            wx = hand_x + int((hilt_end_x - hand_x) * wrap_t)
            wy = hand_y + int((hilt_end_y - hand_y) * wrap_t)
            perp_x = -sin_a
            perp_y = cos_a
            pygame.draw.line(surface, _NS_kazureth.PALETTE["hilt_wrap"],
                            (wx - int(perp_x * 2), wy - int(perp_y * 2)),
                            (wx + int(perp_x * 2), wy + int(perp_y * 2)), 1)
        # Tsuba (guard)
        perp_x = -sin_a
        perp_y = cos_a
        guard_a = (hilt_end_x + int(perp_x * 4), hilt_end_y + int(perp_y * 4))
        guard_b = (hilt_end_x - int(perp_x * 4), hilt_end_y - int(perp_y * 4))
        _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["steel_darkest"],
                            guard_a, guard_b, 3)
        _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["steel_dark"],
                            guard_a, guard_b, 2)
        _NS_kazureth._aacircle(surface, _NS_kazureth.PALETTE["light_mid"],
                              (hilt_end_x, hilt_end_y), 2)
        pygame.draw.rect(surface, _NS_kazureth.PALETTE["light_shine"],
                        (hilt_end_x, hilt_end_y, 1, 1))
        # Blade
        blade_len = 32
        blade_end_x = hilt_end_x + int(cos_a * blade_len)
        blade_end_y = hilt_end_y + int(sin_a * blade_len)
        # Shadow
        _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["shadow_deep"],
                            (hilt_end_x + 1, hilt_end_y + 2),
                            (blade_end_x + 1, blade_end_y + 2), 5)
        # Dark base
        _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["steel_darkest"],
                            (hilt_end_x, hilt_end_y),
                            (blade_end_x, blade_end_y), 5)
        _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["steel_dark"],
                            (hilt_end_x, hilt_end_y),
                            (blade_end_x, blade_end_y), 3)
        _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["steel_mid"],
                            (hilt_end_x, hilt_end_y),
                            (blade_end_x, blade_end_y), 2)
        _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["steel_light"],
                            (hilt_end_x, hilt_end_y),
                            (blade_end_x, blade_end_y), 1)
        # Shine
        shine_offset_x = perp_x * 1
        shine_offset_y = perp_y * 1
        _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["steel_shine"],
                            (hilt_end_x + int(shine_offset_x),
                             hilt_end_y + int(shine_offset_y)),
                            (blade_end_x + int(shine_offset_x),
                             blade_end_y + int(shine_offset_y)), 1)
        # Blade tip
        pygame.draw.rect(surface, _NS_kazureth.PALETTE["steel_shine"],
                        (blade_end_x, blade_end_y, 2, 2))
        pygame.draw.rect(surface, _NS_kazureth.PALETTE["white"],
                        (blade_end_x, blade_end_y, 1, 1))
        # Lightning crackling along blade
        for i in range(3):
            spark_t = (phase * 3 + i * 0.35) % 1.0
            sx = hilt_end_x + int((blade_end_x - hilt_end_x) * spark_t)
            sy = hilt_end_y + int((blade_end_y - hilt_end_y) * spark_t)
            alpha = _NS_kazureth._alpha(180 * math.sin(spark_t * math.pi))
            pygame.draw.rect(surface, (*_NS_kazureth.PALETTE["light_bright"], alpha),
                            (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_kazureth.PALETTE["light_hot"], alpha),
                            (sx, sy, 1, 1))
    def _draw_head(surface, cx, cy, facing, phase, action):
        """Draw head with face."""
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
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["shadow_deep"],
                          [(px + 1, py + 2) for px, py in face_shape])
        # Base skin
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["skin_shadow"], face_shape)
        # Main face
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["skin_dark"], [
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
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["skin_mid"], [
            (cx - 4, cy - 4),
            (cx - 5, cy - 7),
            (cx - 3, cy - 9),
            (cx + 3, cy - 9),
            (cx + 5, cy - 7),
            (cx + 4, cy - 4),
            (cx + 2, cy),
            (cx - 2, cy),
        ])
        # Cheek highlights
        pygame.draw.rect(surface, _NS_kazureth.PALETTE["skin_light"],
                        (cx - 4 * facing, cy - 4, 2, 2))
        pygame.draw.rect(surface, _NS_kazureth.PALETTE["skin_shine"],
                        (cx - 4 * facing, cy - 4, 1, 1))
        # Eyes (golden yellow - glowing when attacking)
        _NS_kazureth._draw_eye(surface, cx - 3 * facing, cy - 5, facing, phase,
                              intense=(action == "attack"))
        _NS_kazureth._draw_eye(surface, cx + 3 * facing, cy - 5, facing, phase,
                              intense=(action == "attack"))
        # Mouth
        if action == "attack":
            # Open mouth (battle cry)
            pygame.draw.rect(surface, _NS_kazureth.PALETTE["shadow_deep"],
                            (cx - 2, cy + 1, 4, 2))
            pygame.draw.rect(surface, (60, 20, 10),
                            (cx - 1, cy + 1, 3, 2))
        else:
            # Determined line
            pygame.draw.line(surface, _NS_kazureth.PALETTE["shadow_deep"],
                            (cx - 2, cy + 2), (cx + 2, cy + 2), 1)
    def _draw_eye(surface, cx, cy, facing, phase, intense=False):
        """Golden yellow eye with lightning glow."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        intensity = 1.3 if intense else 1.0
        pygame.draw.rect(surface, _NS_kazureth.PALETTE["shadow_deep"],
                        (cx - 1, cy - 1, 3, 2))
        pygame.draw.rect(surface, _NS_kazureth.PALETTE["white"],
                        (cx - 1, cy, 3, 1))
        # Iris (golden)
        pygame.draw.rect(surface, _NS_kazureth.PALETTE["eye_dark"],
                        (cx, cy, 2, 1))
        pygame.draw.rect(surface, _NS_kazureth.PALETTE["eye_mid"],
                        (cx + facing, cy, 1, 1))
        if intense:
            # Glowing eye
            for r in range(4, 0, -1):
                alpha = _NS_kazureth._alpha(80 * (4 - r) / 4 * pulse)
                _NS_kazureth._aacircle(surface,
                                      (*_NS_kazureth.PALETTE["eye_light"], alpha),
                                      (cx, cy), r)
            pygame.draw.rect(surface, _NS_kazureth.PALETTE["eye_shine"],
                            (cx, cy, 1, 1))
        # Highlight dot
        pygame.draw.rect(surface, _NS_kazureth.PALETTE["eye_shine"],
                        (cx, cy - 1, 1, 1))
    def _draw_hair(surface, cx, cy, facing, phase):
        """Spiky blonde hair with darker roots at top."""
        # Back hair base
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["shadow_deep"], [
            (cx - 9, cy - 8),
            (cx - 8, cy - 13),
            (cx - 4, cy - 16),
            (cx + 4, cy - 16),
            (cx + 8, cy - 13),
            (cx + 9, cy - 8),
            (cx + 8, cy - 6),
            (cx - 8, cy - 6),
        ])
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["hair_darkest"], [
            (cx - 8, cy - 8),
            (cx - 7, cy - 13),
            (cx - 3, cy - 15),
            (cx + 3, cy - 15),
            (cx + 7, cy - 13),
            (cx + 8, cy - 8),
        ])
        # Main hair (dark blonde)
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["hair_dark"], [
            (cx - 7, cy - 9),
            (cx - 6, cy - 12),
            (cx - 2, cy - 14),
            (cx + 2, cy - 14),
            (cx + 6, cy - 12),
            (cx + 7, cy - 9),
            (cx + 6, cy - 7),
            (cx - 6, cy - 7),
        ])
        # Bright blonde mid
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["hair_mid"], [
            (cx - 6, cy - 10),
            (cx - 4, cy - 12),
            (cx + 4, cy - 12),
            (cx + 6, cy - 10),
            (cx + 5, cy - 8),
            (cx - 5, cy - 8),
        ])
        # Bright yellow highlight
        pygame.draw.line(surface, _NS_kazureth.PALETTE["hair_light"],
                        (cx - 3, cy - 11), (cx + 3, cy - 11), 1)
        pygame.draw.rect(surface, _NS_kazureth.PALETTE["hair_shine"],
                        (cx - 1, cy - 12, 2, 1))
        # SPIKY BANGS on forehead (multiple spikes)
        for spike_x_off, spike_h in [(-4, -3), (-1, -4), (2, -3), (5, -2)]:
            sx = cx + spike_x_off
            sy = cy - 6
            # Dark spike outline
            _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["hair_darkest"], [
                (sx - 2, sy),
                (sx, sy + spike_h),
                (sx + 2, sy),
            ])
            _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["hair_dark"], [
                (sx - 1, sy),
                (sx, sy + spike_h + 1),
                (sx + 1, sy),
            ])
            _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["hair_mid"], [
                (sx, sy),
                (sx, sy + spike_h + 1),
                (sx + 1, sy),
            ])
        # Side hair spikes (2 on each side)
        for side_mult in (-1, 1):
            for spike_i, (dy, spike_len) in enumerate([(-6, 3), (-2, 4)]):
                sx = cx + 7 * side_mult + spike_i
                sy = cy + dy
                end_x = sx + side_mult * spike_len
                end_y = sy - 1
                # Shadow
                _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["hair_darkest"], [
                    (sx, sy - 2),
                    (end_x, end_y - 1),
                    (end_x, end_y + 1),
                    (sx, sy + 2),
                ])
                _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["hair_dark"], [
                    (sx, sy - 1),
                    (end_x, end_y),
                    (sx, sy + 1),
                ])
                _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["hair_mid"], [
                    (sx, sy),
                    (int((sx + end_x) / 2), end_y),
                    (sx, sy + 1),
                ])
        # Top spiky hair swept up
        top_sway = math.sin(phase * 0.7) * 1
        for spike_i, (spike_x_off, spike_h) in enumerate([
            (-4, -6), (-1, -8), (2, -8), (5, -6),
        ]):
            sx = cx + spike_x_off + int(top_sway)
            sy = cy - 13
            end_y = sy + spike_h
            _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["hair_darkest"], [
                (sx - 2, sy),
                (sx, end_y),
                (sx + 2, sy),
            ])
            _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["hair_dark"], [
                (sx - 1, sy),
                (sx, end_y + 1),
                (sx + 1, sy),
            ])
            _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["hair_mid"], [
                (sx, sy),
                (sx, end_y + 1),
                (sx + 1, sy),
            ])
            pygame.draw.rect(surface, _NS_kazureth.PALETTE["hair_light"],
                            (sx, end_y + 1, 1, 1))
            pygame.draw.rect(surface, _NS_kazureth.PALETTE["hair_shine"],
                            (sx, end_y + 1, 1, 1))
    # ============================================================
    # BASIC MELEE - Katana Slash (FIXED: TOP-DOWN SWING)
    # ============================================================
    def _draw_katana_slash(surface, boss, x, y, progress):
        """Yellow lightning slash arc - DOWNWARD swing (top to bottom)."""
        if progress < 0.35 or progress > 0.8:
            return
        facing = boss.direction
        swing_t = (progress - 0.35) / 0.45
        # FIXED: Slash arc dari ATAS (over the shoulder) ke BAWAH-DEPAN
        # start: high behind head, end: low forward
        start_angle = -math.pi * 0.85   # top-back (above head)
        end_angle = math.pi * 0.25       # forward-down
        current_angle = start_angle + (end_angle - start_angle) * swing_t
        origin_x = x + facing * 8
        origin_y = y - 4       # shoulder level
        arc_radius = 34
        # Slash trail (multiple traces for motion blur)
        for trace in range(7):
            trace_t = swing_t - trace * 0.05
            if trace_t < 0:
                continue
            t_angle = start_angle + (end_angle - start_angle) * trace_t
            ex = origin_x + int(math.cos(t_angle) * arc_radius) * facing
            ey = origin_y + int(math.sin(t_angle) * arc_radius)
            alpha = _NS_kazureth._alpha(240 - trace * 32)
            # Main slash arc line
            _NS_kazureth._aaline(surface,
                                (*_NS_kazureth.PALETTE["light_darkest"], alpha),
                                (origin_x, origin_y), (ex, ey), 6)
            _NS_kazureth._aaline(surface,
                                (*_NS_kazureth.PALETTE["light_dark"], alpha),
                                (origin_x, origin_y), (ex, ey), 4)
            _NS_kazureth._aaline(surface,
                                (*_NS_kazureth.PALETTE["light_mid"], alpha),
                                (origin_x, origin_y), (ex, ey), 3)
            _NS_kazureth._aaline(surface,
                                (*_NS_kazureth.PALETTE["light_bright"], alpha),
                                (origin_x, origin_y), (ex, ey), 2)
            _NS_kazureth._aaline(surface,
                                (*_NS_kazureth.PALETTE["light_hot"], alpha),
                                (origin_x, origin_y), (ex, ey), 1)
            # Bright endpoint (blade tip trail)
            _NS_kazureth._aacircle(surface,
                                  (*_NS_kazureth.PALETTE["light_hot"], alpha),
                                  (ex, ey), 3)
            _NS_kazureth._aacircle(surface,
                                  (*_NS_kazureth.PALETTE["light_shine"], alpha),
                                  (ex, ey), 1)
        # CRESCENT ARC - draw the sweep as curved arc points
        arc_pts = []
        arc_pts_outer = []
        num_arc = 12
        for i in range(num_arc + 1):
            a_t = i / num_arc
            # Only show already-swept portion
            if a_t > swing_t:
                break
            a_angle = start_angle + (end_angle - start_angle) * a_t
            ax = origin_x + int(math.cos(a_angle) * arc_radius) * facing
            ay = origin_y + int(math.sin(a_angle) * arc_radius)
            arc_pts.append((ax, ay))
            ax_o = origin_x + int(math.cos(a_angle) * (arc_radius + 5)) * facing
            ay_o = origin_y + int(math.sin(a_angle) * (arc_radius + 5))
            arc_pts_outer.append((ax_o, ay_o))
        # Draw crescent (thin lightning slash effect)
        if len(arc_pts) > 2:
            for i in range(len(arc_pts) - 1):
                alpha = _NS_kazureth._alpha(200 - i * 8)
                _NS_kazureth._aaline(surface,
                                    (*_NS_kazureth.PALETTE["light_bright"], alpha),
                                    arc_pts[i], arc_pts[i + 1], 2)
                _NS_kazureth._aaline(surface,
                                    (*_NS_kazureth.PALETTE["light_hot"], alpha),
                                    arc_pts_outer[i], arc_pts_outer[i + 1], 1)
                _NS_kazureth._aaline(surface,
                                    (*_NS_kazureth.PALETTE["light_shine"], alpha),
                                    (arc_pts[i][0], arc_pts[i][1] - 1),
                                    (arc_pts[i + 1][0], arc_pts[i + 1][1] - 1), 1)
        # Lightning sparks flying off blade tip
        blade_tip_x = origin_x + int(math.cos(current_angle) * arc_radius) * facing
        blade_tip_y = origin_y + int(math.sin(current_angle) * arc_radius)
        for i in range(5):
            spark_ang = current_angle + (i - 2) * 0.3
            sp_r = arc_radius + 3 + i * 2
            sx = origin_x + int(math.cos(spark_ang) * sp_r) * facing
            sy = origin_y + int(math.sin(spark_ang) * sp_r)
            pygame.draw.rect(surface, _NS_kazureth.PALETTE["light_shine"],
                            (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kazureth.PALETTE["white"], (sx, sy, 1, 1))
        # Lightning bolts branching from blade tip
        if swing_t > 0.2 and swing_t < 0.85:
            for i in range(2):
                branch_ang = current_angle + (i - 0.5) * 0.6
                end_pt = (blade_tip_x + int(math.cos(branch_ang) * 22) * facing,
                         blade_tip_y + int(math.sin(branch_ang) * 22))
                _NS_kazureth._draw_lightning_bolt(
                    surface, (blade_tip_x, blade_tip_y), end_pt,
                    _NS_kazureth.PALETTE["light_bright"],
                    width=2, jitter=4, alpha=220
                )
    # ============================================================
    # FLOATING MIST (thunder sparks below)
    # ============================================================
    def _draw_thunder_mist(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        """Electric mist below body."""
        strength = 1.4 if intense else 1.0
        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        # Base yellow glow
        for radius in range(24, 3, -2):
            alpha = _NS_kazureth._alpha((24 - radius) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kazureth.PALETTE["light_dark"], alpha),
                    (60 - radius, 20 - radius // 3,
                     radius * 2, max(2, radius // 2))
                )
        for radius in range(16, 2, -2):
            alpha = _NS_kazureth._alpha((16 - radius) * 6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kazureth.PALETTE["light_mid"], alpha),
                    (60 - radius, 20 - radius // 4,
                     radius * 2, max(2, radius // 3))
                )
        surface.blit(mist, (cx - 60, cy - 10))
        # Rising electric sparks
        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            px = cx - 24 + i * 7 + int(math.sin(phase + i) * 4)
            py = cy + 4 - int(t * 25)
            alpha = _NS_kazureth._alpha(220 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_kazureth.PALETTE["light_mid"], alpha),
                                (px, py, 2, 2))
                pygame.draw.rect(surface, (*_NS_kazureth.PALETTE["light_bright"], alpha),
                                (px, py, 1, 1))
                pygame.draw.rect(surface, (*_NS_kazureth.PALETTE["light_shine"], alpha),
                                (px, py - 1, 1, 1))
        # Random lightning arcs on ground
        for i in range(3):
            if math.sin(phase * 4 + i * 2) > 0.5:
                sx = cx + int(math.sin(phase * 2 + i) * 20)
                sy = cy + 6
                ex = sx + int(math.cos(phase + i) * 12) - 6
                ey = sy - 4
                _NS_kazureth._draw_lightning_bolt(
                    surface, (sx, sy), (ex, ey),
                    _NS_kazureth.PALETTE["light_bright"],
                    width=1, jitter=2, alpha=180
                )
        # Trail
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_kazureth._alpha(160 - i * 25)
                if alpha > 0:
                    _NS_kazureth._aacircle(surface,
                                          (*_NS_kazureth.PALETTE["light_dark"], alpha),
                                          (sx, sy), max(1, 5 - i))
                    _NS_kazureth._aacircle(surface,
                                          (*_NS_kazureth.PALETTE["light_mid"], alpha),
                                          (sx, sy), max(1, 3 - i))
                    pygame.draw.rect(surface, _NS_kazureth.PALETTE["light_bright"],
                                    (sx, sy - 1, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((130, 26), pygame.SRCALPHA)
        for radius in range(13, 0, -1):
            alpha = max(0, (13 - radius) * 14)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 13 - radius, 110 + radius * 2, radius * 2)
            )
        pygame.draw.ellipse(shadow, (5, 4, 2, 170), (5, 6, 120, 14))
        pygame.draw.ellipse(shadow, (60, 45, 5, 100), (15, 8, 100, 10))
        surface.blit(shadow, (x - 65, y - 13))
    def _draw_thunder_aura(surface, x, y, phase):
        """Yellow electric aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_kazureth._alpha((95 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_kazureth._aacircle(aura,
                                      (*_NS_kazureth.PALETTE["light_darkest"], alpha),
                                      (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_kazureth._alpha((60 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_kazureth._aacircle(aura,
                                      (*_NS_kazureth.PALETTE["light_dark"], alpha),
                                      (110, 90), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_kazureth._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_kazureth._aacircle(aura,
                                      (*_NS_kazureth.PALETTE["light_mid"], alpha),
                                      (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        # Floating sparks
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            radius = 38 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_kazureth.PALETTE["light_bright"],
                            (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kazureth.PALETTE["light_shine"], (sx, sy, 1, 1))
        # Occasional random lightning arcs
        for i in range(3):
            if math.sin(phase * 3 + i * 2.7) > 0.7:
                ax = x + int(math.cos(phase + i) * 40)
                ay = y - 10 + int(math.sin(phase * 2 + i) * 15)
                bx = ax + int(math.cos(phase * 1.5 + i) * 25)
                by = ay + int(math.sin(phase * 1.5 + i) * 25)
                _NS_kazureth._draw_lightning_bolt(
                    surface, (ax, ay), (bx, by),
                    _NS_kazureth.PALETTE["light_bright"],
                    width=1, jitter=3, alpha=180
                )
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring beneath body."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_kazureth.PALETTE["light_darkest"], 210),
                           (5, 15, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_kazureth.PALETTE["light_dark"], 220),
                           (14, 17, 132, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_kazureth.PALETTE["light_mid"], 200),
                           (25, 19, 110, 16), 1)
        # Runes (lightning bolt symbols)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 27 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 27 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_kazureth.PALETTE["light_bright"], 220),
                            (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_kazureth.PALETTE["light_hot"],
                                       _NS_kazureth._alpha(160 * pulse)),
                               (12, 10, 136, 32), 1)
        surface.blit(ring, (x - 80, y - 25))
    # ============================================================
    # SKILL Q - THUNDERCLAP AND FLASH (dash + slash burst)
    # ============================================================
    def _draw_thunderclap_ground(surface, boss, x, y, timer, phase):
        """Dash trail on ground."""
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kazureth._target_position(boss, x, y)
        if 0.2 < progress < 0.6:
            # Line of dash on ground
            for i in range(8):
                dt = (progress - 0.2) / 0.4 - i * 0.06
                if dt < 0:
                    continue
                dx = int(x + (tx - x) * dt)
                dy = ty + 40
                alpha = _NS_kazureth._alpha(150 * (1 - i / 8))
                pygame.draw.ellipse(surface,
                                   (*_NS_kazureth.PALETTE["light_mid"], alpha),
                                   (dx - 8, dy - 3, 16, 6))
    def _draw_thunderclap_skill(surface, boss, x, y, timer, phase):
        """Rapid dash with lightning + final slash."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kazureth._target_position(boss, x, y)
        if progress < 0.25:
            # Wind up - crouch, lightning gathers
            t = progress / 0.25
            for r in range(int(15 * t), 0, -2):
                alpha = _NS_kazureth._alpha(200 * t)
                _NS_kazureth._aacircle(surface,
                                      (*_NS_kazureth.PALETTE["light_mid"], alpha),
                                      (x, y - 10), r)
            # Lightning crackle
            for i in range(4):
                ang = i * math.pi / 2 + phase * 3
                sx = x + int(math.cos(ang) * 20)
                sy = y - 10 + int(math.sin(ang) * 15)
                _NS_kazureth._draw_lightning_bolt(
                    surface, (x, y - 10), (sx, sy),
                    _NS_kazureth.PALETTE["light_bright"],
                    width=2, jitter=3, alpha=int(200 * t)
                )
        elif progress < 0.55:
            # DASH - streak of lightning between origin and target
            t = (progress - 0.25) / 0.3
            dash_x = int(x + (tx - x - facing * 40) * t)
            # Streak lines
            for i in range(10):
                trail_t = t - i * 0.06
                if trail_t < 0:
                    continue
                sx = int(x + (dash_x - x) * trail_t)
                alpha = _NS_kazureth._alpha(240 - i * 22)
                # Horizontal streak
                _NS_kazureth._aaline(surface,
                                    (*_NS_kazureth.PALETTE["light_darkest"], alpha),
                                    (sx - facing * 30, y - 10),
                                    (sx, y - 10), 6)
                _NS_kazureth._aaline(surface,
                                    (*_NS_kazureth.PALETTE["light_dark"], alpha),
                                    (sx - facing * 30, y - 10),
                                    (sx, y - 10), 4)
                _NS_kazureth._aaline(surface,
                                    (*_NS_kazureth.PALETTE["light_mid"], alpha),
                                    (sx - facing * 30, y - 10),
                                    (sx, y - 10), 3)
                _NS_kazureth._aaline(surface,
                                    (*_NS_kazureth.PALETTE["light_bright"], alpha),
                                    (sx - facing * 30, y - 10),
                                    (sx, y - 10), 2)
                _NS_kazureth._aaline(surface,
                                    (*_NS_kazureth.PALETTE["light_hot"], alpha),
                                    (sx - facing * 30, y - 10),
                                    (sx, y - 10), 1)
            # Big lightning bolt along dash path
            _NS_kazureth._draw_lightning_bolt(
                surface, (x, y - 10), (dash_x, y - 10),
                _NS_kazureth.PALETTE["light_hot"],
                width=3, segments=8, jitter=5, alpha=220
            )
        else:
            # SLASH IMPACT at target
            t = (progress - 0.55) / 0.45
            # Big burst at target
            burst_r = int(15 + t * 30)
            alpha = _NS_kazureth._alpha(255 * (1 - t))
            _NS_kazureth._aacircle(surface, (*_NS_kazureth.PALETTE["light_darkest"], alpha),
                                  (tx, ty), burst_r + 4)
            _NS_kazureth._aacircle(surface, (*_NS_kazureth.PALETTE["light_dark"], alpha),
                                  (tx, ty), burst_r)
            _NS_kazureth._aacircle(surface, (*_NS_kazureth.PALETTE["light_mid"], alpha),
                                  (tx, ty), max(1, burst_r - 8))
            _NS_kazureth._aacircle(surface, (*_NS_kazureth.PALETTE["light_bright"], alpha),
                                  (tx, ty), max(1, burst_r - 15))
            _NS_kazureth._aacircle(surface, (*_NS_kazureth.PALETTE["light_hot"], alpha),
                                  (tx, ty), max(1, burst_r - 22))
            _NS_kazureth._aacircle(surface, (*_NS_kazureth.PALETTE["light_shine"], alpha),
                                  (tx, ty), max(1, burst_r // 5))
            # Slash arc
            for arc_i in range(3):
                arc_angle = -math.pi * 0.3 + arc_i * math.pi * 0.3
                for pt_i in range(8):
                    pt_t = pt_i / 7
                    px = tx + int(math.cos(arc_angle + pt_t * math.pi * 0.4) * burst_r * 0.9) * facing
                    py = ty + int(math.sin(arc_angle + pt_t * math.pi * 0.4) * burst_r * 0.9)
                    pygame.draw.rect(surface,
                                    (*_NS_kazureth.PALETTE["light_shine"], alpha),
                                    (px, py, 2, 2))
            # Radial lightning bolts
            for i in range(10):
                angle_r = i * math.pi / 5
                ex = tx + int(math.cos(angle_r) * burst_r * 1.2)
                ey = ty + int(math.sin(angle_r) * burst_r * 1.2)
                _NS_kazureth._draw_lightning_bolt(
                    surface, (tx, ty), (ex, ey),
                    _NS_kazureth.PALETTE["light_bright"],
                    width=2, segments=4, jitter=4, alpha=int(220 * (1 - t))
                )
    # ============================================================
    # SKILL W - LIGHTNING CLOAK
    # ============================================================
    def _draw_lightning_cloak(surface, boss, x, y, timer, phase):
        """Electric aura around body."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Aura bubble
        breath = math.sin(phase * 2.5) * 2
        r = 38 + int(breath)
        cloak = pygame.Surface((r * 2 + 30, r * 2 + 30), pygame.SRCALPHA)
        center = (r + 15, r + 15)
        # Ring layers
        for i, (thickness, alpha_val) in enumerate([
            (3, 100), (2, 140), (1, 180),
        ]):
            _NS_kazureth._aacircle(cloak,
                                  (*_NS_kazureth.PALETTE["light_dark"], alpha_val),
                                  center, r - i, thickness)
            _NS_kazureth._aacircle(cloak,
                                  (*_NS_kazureth.PALETTE["light_mid"], alpha_val),
                                  center, r - i - 1, 1)
        # Rotating sparks
        for i in range(18):
            angle = phase * 2 + i * math.pi / 9
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            pygame.draw.rect(cloak, _NS_kazureth.PALETTE["light_bright"], (sx, sy, 2, 2))
            pygame.draw.rect(cloak, _NS_kazureth.PALETTE["light_shine"], (sx, sy, 1, 1))
        surface.blit(cloak, (x - r - 15, y - r - 15))
        # Random lightning bolts INSIDE the aura
        for i in range(3):
            if math.sin(phase * 5 + i * 2) > 0.4:
                ang1 = phase * 3 + i * 2
                ang2 = ang1 + math.pi + math.sin(phase + i)
                sx = x + int(math.cos(ang1) * r * 0.9)
                sy = y + int(math.sin(ang1) * r * 0.9)
                ex = x + int(math.cos(ang2) * r * 0.9)
                ey = y + int(math.sin(ang2) * r * 0.9)
                _NS_kazureth._draw_lightning_bolt(
                    surface, (sx, sy), (ex, ey),
                    _NS_kazureth.PALETTE["light_hot"],
                    width=2, jitter=4, alpha=200
                )
        # Outer lightning tendrils
        for i in range(6):
            angle = phase * 1.5 + i * math.pi / 3
            end_x = x + int(math.cos(angle) * (r + 12))
            end_y = y + int(math.sin(angle) * (r + 12))
            start_x = x + int(math.cos(angle) * r)
            start_y = y + int(math.sin(angle) * r)
            _NS_kazureth._draw_lightning_bolt(
                surface, (start_x, start_y), (end_x, end_y),
                _NS_kazureth.PALETTE["light_bright"],
                width=1, jitter=3, alpha=180
            )
            pygame.draw.rect(surface, _NS_kazureth.PALETTE["light_shine"],
                            (end_x, end_y, 1, 1))
    # ============================================================
    # SKILL E - DISTANT THUNDER (storm cloud + lightning)
    # ============================================================
    def _draw_distant_thunder_ground(surface, boss, x, y, timer, phase):
        """Ground charring where lightning hits."""
        tx, ty = _NS_kazureth._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.3:
            t = min(1.0, (progress - 0.3) / 0.7)
            r = int(35 * t)
            if r > 3:
                pygame.draw.ellipse(surface,
                                   (*_NS_kazureth.PALETTE["light_darkest"], 200),
                                   (tx - r, ty - r // 3, r * 2, r * 2 // 3))
                pygame.draw.ellipse(surface,
                                   (*_NS_kazureth.PALETTE["light_dark"], 180),
                                   (tx - r + 3, ty - r // 3 + 2,
                                    r * 2 - 6, r * 2 // 3 - 4))
                pygame.draw.ellipse(surface,
                                   (*_NS_kazureth.PALETTE["light_mid"], 130),
                                   (tx - r + 8, ty - r // 3 + 4,
                                    r * 2 - 16, r * 2 // 3 - 8))
    def _draw_distant_thunder_skill(surface, boss, x, y, timer, phase):
        """Storm cloud above + lightning strikes."""
        tx, ty = _NS_kazureth._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Storm cloud position (above target)
        cloud_y = ty - 90
        if progress < 0.3:
            # Cloud forming
            t = progress / 0.3
            _NS_kazureth._draw_storm_cloud(surface, tx, cloud_y, t, phase, brewing=True)
        else:
            # Full cloud + lightning strikes
            _NS_kazureth._draw_storm_cloud(surface, tx, cloud_y, 1.0, phase, brewing=False)
            # Multiple lightning strikes from cloud to ground area
            strike_cycle = int((1 - progress) * 8)
            for strike_i in range(3):
                # Different strike positions
                strike_offset_x = (strike_i - 1) * 25
                strike_x = tx + strike_offset_x
                # Strike based on cycle
                if math.sin(phase * 6 + strike_i * 2) > 0.3:
                    # Draw main strike bolt
                    _NS_kazureth._draw_lightning_bolt(
                        surface, (strike_x + int(math.sin(phase + strike_i) * 5), cloud_y + 10),
                        (strike_x, ty), _NS_kazureth.PALETTE["light_hot"],
                        width=4, segments=8, jitter=6, alpha=240
                    )
                    _NS_kazureth._draw_lightning_bolt(
                        surface, (strike_x + int(math.sin(phase + strike_i) * 5), cloud_y + 10),
                        (strike_x, ty), _NS_kazureth.PALETTE["light_shine"],
                        width=2, segments=8, jitter=4, alpha=255
                    )
                    _NS_kazureth._draw_lightning_bolt(
                        surface, (strike_x + int(math.sin(phase + strike_i) * 5), cloud_y + 10),
                        (strike_x, ty), _NS_kazureth.PALETTE["white"],
                        width=1, segments=8, jitter=2, alpha=255
                    )
                    # Impact flash at ground
                    for r in range(15, 3, -2):
                        alpha = _NS_kazureth._alpha(200 * (15 - r) / 15)
                        _NS_kazureth._aacircle(surface,
                                              (*_NS_kazureth.PALETTE["light_bright"], alpha),
                                              (strike_x, ty), r)
                    _NS_kazureth._aacircle(surface, _NS_kazureth.PALETTE["light_shine"],
                                          (strike_x, ty), 4)
                    pygame.draw.rect(surface, _NS_kazureth.PALETTE["white"],
                                    (strike_x, ty, 2, 2))
                    # Ground crackles
                    for j in range(4):
                        ang = j * math.pi / 2 + phase
                        ex = strike_x + int(math.cos(ang) * 20)
                        ey = ty + int(math.sin(ang) * 8)
                        _NS_kazureth._draw_lightning_bolt(
                            surface, (strike_x, ty), (ex, ey),
                            _NS_kazureth.PALETTE["light_bright"],
                            width=1, jitter=3, alpha=180
                        )
    def _draw_storm_cloud(surface, cx, cy, opacity, phase, brewing=False):
        """Grey storm cloud sprite."""
        alpha_mult = opacity
        # Cloud puffs
        puffs = [
            (-24, 4, 12),
            (-16, -2, 14),
            (-6, -6, 16),
            (4, -8, 15),
            (14, -4, 14),
            (22, 2, 12),
            (10, 6, 10),
            (-10, 6, 10),
        ]
        for puff_x, puff_y, puff_r in puffs:
            px = cx + puff_x
            py = cy + puff_y
            # Base darkest
            alpha = _NS_kazureth._alpha(220 * alpha_mult)
            _NS_kazureth._aacircle(surface,
                                  (*_NS_kazureth.PALETTE["cloud_darkest"], alpha),
                                  (px + 1, py + 1), puff_r + 1)
            _NS_kazureth._aacircle(surface,
                                  (*_NS_kazureth.PALETTE["cloud_dark"], alpha),
                                  (px, py), puff_r)
            _NS_kazureth._aacircle(surface,
                                  (*_NS_kazureth.PALETTE["cloud_mid"], alpha),
                                  (px - 1, py - 1), puff_r - 3)
            # Highlight
            _NS_kazureth._aacircle(surface,
                                  (*_NS_kazureth.PALETTE["cloud_light"],
                                   _NS_kazureth._alpha(180 * alpha_mult)),
                                  (px - 2, py - 3), max(2, puff_r - 6))
        # Interior lightning glow (brewing)
        if brewing or math.sin(phase * 4) > 0.3:
            glow_pulse = math.sin(phase * 5) * 0.3 + 0.7
            for r in range(20, 3, -3):
                alpha = _NS_kazureth._alpha(180 * glow_pulse * alpha_mult * (20 - r) / 20)
                _NS_kazureth._aacircle(surface,
                                      (*_NS_kazureth.PALETTE["light_bright"], alpha),
                                      (cx, cy), r)
            # Small bolt inside cloud
            if math.sin(phase * 6) > 0.5:
                start_pt = (cx + int(math.sin(phase * 3) * 15), cy - 3)
                end_pt = (cx + int(math.cos(phase * 3) * 15), cy + 3)
                _NS_kazureth._draw_lightning_bolt(
                    surface, start_pt, end_pt,
                    _NS_kazureth.PALETTE["light_hot"],
                    width=2, jitter=3, alpha=int(220 * alpha_mult)
                )
    # ============================================================
    # SKILL R - HONOIKAZUCHI NO KAMI (Thunder Dragon)
    # ============================================================
    def _draw_honoikazuchi_skill(surface, boss, x, y, timer, phase):
        """Giant lightning dragon charges forward."""
        facing = boss.direction
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kazureth._target_position(boss, x, y)
        if progress < 0.2:
            # Charge up
            t = progress / 0.2
            # Massive lightning gather around body
            for r in range(int(30 * t), 0, -2):
                alpha = _NS_kazureth._alpha(220 * t)
                _NS_kazureth._aacircle(surface,
                                      (*_NS_kazureth.PALETTE["light_dark"], alpha),
                                      (x, y - 8), r)
            for r in range(int(20 * t), 0, -2):
                alpha = _NS_kazureth._alpha(250 * t)
                _NS_kazureth._aacircle(surface,
                                      (*_NS_kazureth.PALETTE["light_mid"], alpha),
                                      (x, y - 8), r)
            _NS_kazureth._aacircle(surface, _NS_kazureth.PALETTE["light_bright"],
                                  (x, y - 8), max(1, int(10 * t)))
            # Lightning arcs
            for i in range(8):
                ang = i * math.pi / 4 + phase * 2
                sx = x + int(math.cos(ang) * 30)
                sy = y - 8 + int(math.sin(ang) * 20)
                _NS_kazureth._draw_lightning_bolt(
                    surface, (x, y - 8), (sx, sy),
                    _NS_kazureth.PALETTE["light_hot"],
                    width=2, jitter=4, alpha=int(220 * t)
                )
        elif progress < 0.8:
            # DRAGON CHARGES FORWARD
            t = (progress - 0.2) / 0.6
            # Dragon travels from boss to beyond target
            travel_dist = 300
            head_travel = int(t * travel_dist)
            head_x = x + facing * (30 + head_travel)
            head_y = y - 8 + int(math.sin(phase * 2) * 3)
            _NS_kazureth._draw_thunder_dragon(surface, x + facing * 20, y - 8,
                                             head_x, head_y, facing, phase, t)
            # Impact when dragon reaches target
            if t > 0.5:
                impact_t = min(1.0, (t - 0.5) / 0.3)
                for r in range(int(40 * impact_t), 5, -3):
                    alpha = _NS_kazureth._alpha(240 * (1 - impact_t) * impact_t)
                    _NS_kazureth._aacircle(surface,
                                          (*_NS_kazureth.PALETTE["light_hot"], alpha),
                                          (tx, ty), r)
        else:
            # Aftermath - lingering electricity
            t = (progress - 0.8) / 0.2
            for i in range(10):
                rise_t = (phase * 0.8 + i * 0.1) % 1.0
                rx = tx + int(math.sin(phase + i) * 40)
                ry = ty - int(rise_t * 40)
                alpha = _NS_kazureth._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    pygame.draw.rect(surface, (*_NS_kazureth.PALETTE["light_mid"], alpha),
                                    (rx, ry, 3, 3))
                    pygame.draw.rect(surface, (*_NS_kazureth.PALETTE["light_bright"], alpha),
                                    (rx, ry, 2, 2))
                    pygame.draw.rect(surface, (*_NS_kazureth.PALETTE["light_shine"], alpha),
                                    (rx, ry, 1, 1))
    def _draw_thunder_dragon(surface, start_x, start_y, head_x, head_y, facing,
                             phase, progress):
        """Draw serpentine thunder dragon."""
        # Body as sinuous line
        num_segments = 12
        segment_len = math.sqrt((head_x - start_x) ** 2 + (head_y - start_y) ** 2) / num_segments
        # Generate wavy path
        points = []
        for i in range(num_segments + 1):
            t = i / num_segments
            base_x = start_x + (head_x - start_x) * t
            base_y = start_y + (head_y - start_y) * t
            # Sine wave amplitude fades toward head
            wave = math.sin(t * math.pi * 4 - phase * 5) * 25 * (1 - t * 0.5)
            # Perpendicular offset
            dx = head_x - start_x
            dy = head_y - start_y
            length = max(1, math.sqrt(dx * dx + dy * dy))
            perp_x = -dy / length
            perp_y = dx / length
            points.append((int(base_x + perp_x * wave),
                          int(base_y + perp_y * wave)))
        # Draw body segments with tapering thickness
        for i in range(len(points) - 1):
            thickness = max(3, 18 - i)
            alpha = _NS_kazureth._alpha(240)
            # Layers
            _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["drag_darkest"],
                                points[i], points[i + 1], thickness + 2)
            _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["drag_dark"],
                                points[i], points[i + 1], thickness)
            _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["drag_mid"],
                                points[i], points[i + 1], max(2, thickness - 3))
            _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["drag_light"],
                                points[i], points[i + 1], max(1, thickness - 6))
            _NS_kazureth._aaline(surface, _NS_kazureth.PALETTE["drag_shine"],
                                points[i], points[i + 1], max(1, thickness - 10))
            # Scale details along body
            if i % 2 == 0 and thickness > 5:
                mid_x = int((points[i][0] + points[i + 1][0]) / 2)
                mid_y = int((points[i][1] + points[i + 1][1]) / 2)
                perp_ang = math.atan2(points[i + 1][1] - points[i][1],
                                     points[i + 1][0] - points[i][0]) + math.pi / 2
                spike_len = thickness // 2 + 2
                spike_x = mid_x + int(math.cos(perp_ang) * spike_len)
                spike_y = mid_y + int(math.sin(perp_ang) * spike_len)
                _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["drag_dark"], [
                    (mid_x - 3, mid_y),
                    (spike_x, spike_y),
                    (mid_x + 3, mid_y),
                ])
                _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["drag_mid"], [
                    (mid_x - 2, mid_y),
                    (spike_x, spike_y),
                    (mid_x + 2, mid_y),
                ])
                pygame.draw.rect(surface, _NS_kazureth.PALETTE["light_shine"],
                                (spike_x, spike_y, 1, 1))
        # Lightning crackles around body
        for i in range(len(points) - 1):
            if math.sin(phase * 6 + i) > 0.3:
                p = points[i]
                ang = phase + i
                ex = p[0] + int(math.cos(ang) * 15)
                ey = p[1] + int(math.sin(ang) * 15)
                _NS_kazureth._draw_lightning_bolt(
                    surface, p, (ex, ey),
                    _NS_kazureth.PALETTE["light_bright"],
                    width=1, jitter=3, alpha=200
                )
        # DRAGON HEAD (large)
        head_pt = points[-1]
        _NS_kazureth._draw_dragon_head(surface, head_pt[0], head_pt[1], facing, phase)
    def _draw_dragon_head(surface, cx, cy, facing, phase):
        """Golden thunder dragon head."""
        # Head shape (elongated snout)
        head_shape = [
            (cx - 12 * facing, cy - 4),
            (cx - 10 * facing, cy - 10),
            (cx - 4 * facing, cy - 14),
            (cx + 4 * facing, cy - 14),
            (cx + 12 * facing, cy - 10),
            (cx + 20 * facing, cy - 6),
            (cx + 24 * facing, cy - 2),
            (cx + 22 * facing, cy + 4),
            (cx + 14 * facing, cy + 8),
            (cx + 2 * facing, cy + 10),
            (cx - 8 * facing, cy + 8),
            (cx - 12 * facing, cy + 4),
        ]
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["shadow_deep"],
                          [(px + 2, py + 2) for px, py in head_shape])
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["drag_darkest"], head_shape)
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["drag_dark"], [
            (cx - 10 * facing, cy - 3),
            (cx - 8 * facing, cy - 9),
            (cx - 3 * facing, cy - 13),
            (cx + 3 * facing, cy - 13),
            (cx + 10 * facing, cy - 9),
            (cx + 18 * facing, cy - 5),
            (cx + 22 * facing, cy - 2),
            (cx + 20 * facing, cy + 3),
            (cx + 12 * facing, cy + 6),
            (cx, cy + 8),
            (cx - 6 * facing, cy + 6),
            (cx - 10 * facing, cy + 3),
        ])
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["drag_mid"], [
            (cx - 8 * facing, cy - 2),
            (cx - 4 * facing, cy - 10),
            (cx + 4 * facing, cy - 10),
            (cx + 14 * facing, cy - 6),
            (cx + 18 * facing, cy - 2),
            (cx + 12 * facing, cy + 4),
            (cx - 4 * facing, cy + 5),
            (cx - 8 * facing, cy + 2),
        ])
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["drag_light"], [
            (cx - 4 * facing, cy - 6),
            (cx + 2 * facing, cy - 8),
            (cx + 10 * facing, cy - 4),
            (cx + 8 * facing, cy),
            (cx - 2 * facing, cy),
        ])
        pygame.draw.rect(surface, _NS_kazureth.PALETTE["drag_shine"],
                        (cx + 2 * facing, cy - 6, 3, 2))
        # Snout tip (bright)
        pygame.draw.rect(surface, _NS_kazureth.PALETTE["light_hot"],
                        (cx + 22 * facing, cy - 2, 2, 2))
        pygame.draw.rect(surface, _NS_kazureth.PALETTE["light_shine"],
                        (cx + 23 * facing, cy - 1, 1, 1))
        # HORNS
        for horn_off_x, horn_off_y in [(-4, -12), (-2, -14), (2, -14), (4, -12)]:
            h_base_x = cx + horn_off_x * facing
            h_base_y = cy + horn_off_y
            h_tip_x = h_base_x - facing * 3
            h_tip_y = h_base_y - 6
            _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["drag_darkest"], [
                (h_base_x - 2, h_base_y),
                (h_tip_x, h_tip_y),
                (h_base_x + 2, h_base_y),
            ])
            _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["drag_dark"], [
                (h_base_x - 1, h_base_y),
                (h_tip_x, h_tip_y + 1),
                (h_base_x + 1, h_base_y),
            ])
            pygame.draw.rect(surface, _NS_kazureth.PALETTE["light_shine"],
                            (h_tip_x, h_tip_y, 1, 1))
        # EYE (glowing white/yellow)
        for r in range(5, 0, -1):
            alpha = _NS_kazureth._alpha(180 * (5 - r) / 5)
            _NS_kazureth._aacircle(surface, (*_NS_kazureth.PALETTE["light_bright"], alpha),
                                  (cx + 4 * facing, cy - 6), r)
        pygame.draw.rect(surface, _NS_kazureth.PALETTE["light_shine"],
                        (cx + 4 * facing, cy - 6, 2, 2))
        pygame.draw.rect(surface, _NS_kazureth.PALETTE["white"],
                        (cx + 4 * facing, cy - 6, 1, 1))
        # Open mouth with lightning
        _NS_kazureth._poly(surface, _NS_kazureth.PALETTE["shadow_deep"], [
            (cx + 8 * facing, cy + 2),
            (cx + 20 * facing, cy + 2),
            (cx + 20 * facing, cy + 6),
            (cx + 8 * facing, cy + 6),
        ])
        # Fangs
        for f_off in (10, 14, 18):
            f_x = cx + f_off * facing
            pygame.draw.line(surface, _NS_kazureth.PALETTE["light_shine"],
                            (f_x, cy + 2), (f_x, cy + 6), 2)
            pygame.draw.line(surface, _NS_kazureth.PALETTE["white"],
                            (f_x, cy + 2), (f_x, cy + 6), 1)
        # Lightning breath from mouth
        for i in range(4):
            end_x = cx + int((25 + i * 6) * facing)
            end_y = cy + 4 + int(math.sin(phase * 3 + i) * 3)
            _NS_kazureth._draw_lightning_bolt(
                surface, (cx + 20 * facing, cy + 4), (end_x, end_y),
                _NS_kazureth.PALETTE["light_hot"],
                width=2, jitter=3, alpha=220
            )


# ====================================================================
# SETHRAKHAR (SUNFORGED BUTCHER) - Mini Boss
# ====================================================================

class _NS_sethrakhar:
    """Namespace sethrakhar - ascended crocodile mini-boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Dark green crocodile scales (body)
        "scale_darkest": (10, 20, 8),
        "scale_dark": (30, 55, 22),
        "scale_mid": (65, 100, 40),
        "scale_light": (110, 150, 65),
        "scale_edge": (155, 190, 95),
        "scale_shine": (200, 230, 140),
        # Belly / underside (tan)
        "belly_darkest": (55, 40, 15),
        "belly_dark": (105, 80, 30),
        "belly_mid": (170, 135, 55),
        "belly_light": (215, 180, 95),
        "belly_shine": (250, 225, 145),
        # Golden armor (pauldrons, gauntlets)
        "gold_darkest": (55, 35, 8),
        "gold_dark": (110, 75, 15),
        "gold_mid": (185, 140, 35),
        "gold_light": (240, 200, 75),
        "gold_shine": (255, 235, 150),
        "gold_glare": (255, 250, 210),
        # Bronze (weapon body, dark armor)
        "bronze_darkest": (20, 12, 5),
        "bronze_dark": (55, 35, 15),
        "bronze_mid": (95, 65, 30),
        "bronze_light": (140, 100, 50),
        # Orange fury flame (main magic theme)
        "fury_darkest": (55, 15, 3),
        "fury_dark": (135, 50, 10),
        "fury_mid": (220, 100, 25),
        "fury_light": (255, 160, 55),
        "fury_hot": (255, 210, 100),
        "fury_shine": (255, 245, 180),
        # Amber/red eye
        "eye_socket": (8, 3, 2),
        "eye_dark": (95, 25, 10),
        "eye_mid": (215, 90, 25),
        "eye_light": (255, 170, 60),
        "eye_glow": (255, 230, 150),
        # Fangs/bone (yellowish)
        "fang_dark": (95, 75, 40),
        "fang_mid": (180, 155, 100),
        "fang_light": (240, 220, 170),
        "fang_shine": (255, 250, 220),
        # Blade steel
        "blade_darkest": (25, 20, 15),
        "blade_dark": (60, 55, 50),
        "blade_mid": (110, 105, 100),
        "blade_light": (175, 170, 165),
        "blade_shine": (230, 225, 220),
        # Dark red cloth (loincloth)
        "cloth_darkest": (25, 10, 8),
        "cloth_dark": (75, 25, 15),
        "cloth_mid": (135, 50, 30),
        "cloth_light": (185, 85, 55),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_sethrakhar._clamp(color)
        if _NS_sethrakhar.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_sethrakhar._clamp(color)
        if _NS_sethrakhar.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_sethrakhar._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 200 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_sethrakhar(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_sethrakhar._detect_moving(boss)
        _NS_sethrakhar._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_seth_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_sethrakhar._draw_fury_aura(surface, x, y, pulse)
        _NS_sethrakhar._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "r":
            _NS_sethrakhar._draw_dominus_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_sethrakhar._draw_empoweredstun_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (always floating)
        if attacking:
            _NS_sethrakhar._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_sethrakhar._draw_float_move(surface, boss, x, y)
        else:
            _NS_sethrakhar._draw_float_idle(surface, boss, x, y)
        # Foreground FX
        if active_skill == "q":
            _NS_sethrakhar._draw_ruthlesspredator_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_sethrakhar._draw_empoweredstun_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_sethrakhar._draw_sliceanddice_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_sethrakhar._draw_dominus_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_seth_previous_timer", 0))
        active = bool(getattr(boss, "_seth_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._seth_attack_active = True
            boss._seth_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._seth_attack_frame = int(getattr(boss, "_seth_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._seth_attack_active = False
            boss._seth_attack_frame = 0
            active = False
        boss._seth_previous_timer = timer
        boss._seth_attack_progress = (
            min(1.0, getattr(boss, "_seth_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_seth_last_x"):
            boss._seth_last_x = boss.x
            boss._seth_last_y = boss.y
            return False
        dx = abs(boss.x - boss._seth_last_x)
        dy = abs(boss.y - boss._seth_last_y)
        boss._seth_last_x = boss.x
        boss._seth_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS (Floating)
    # ============================================================
    def _draw_float_idle(surface, boss, x, y):
        hover = int(math.sin(boss.pulse * 0.7) * 4) - 6
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_sethrakhar._draw_float_shadow(surface, x + sway, y + 50, boss.pulse)
        _NS_sethrakhar._draw_fury_flames(surface, x + sway, y + 40, boss.pulse)
        _NS_sethrakhar._draw_body(surface, x + sway, y + hover,
                                  boss.direction, boss.pulse, "idle")
    def _draw_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.5
        hover = int(math.sin(phase * 0.9) * 5) - 7
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_sethrakhar._draw_float_shadow(surface, x + sway, y + 50, phase)
        _NS_sethrakhar._draw_fury_flames(surface, x + sway, y + 40, phase,
                                         trail=True, facing=boss.direction)
        _NS_sethrakhar._draw_body(surface, x + sway, y + hover,
                                  boss.direction, phase, "float")
    def _draw_attack(surface, boss, x, y):
        """Melee: massive khopesh swing."""
        progress = getattr(boss, "_seth_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 6) * boss.direction
            lift = int(t * 5)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lunge = int((-6 + t * 22)) * boss.direction
            lift = int(5 - t * 7)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(16 * (1 - t)) * boss.direction
            lift = int(-2 + t * 4)
        hover = int(math.sin(boss.pulse * 0.7) * 3) - 5
        _NS_sethrakhar._draw_float_shadow(surface, x + lunge, y + 50, boss.pulse)
        _NS_sethrakhar._draw_fury_flames(surface, x + lunge, y + 40,
                                         boss.pulse, intense=True)
        _NS_sethrakhar._draw_body(surface, x + lunge, y + hover - lift,
                                  boss.direction, boss.pulse,
                                  "attack", progress)
        _NS_sethrakhar._draw_khopesh_slash(surface, boss, x + lunge,
                                           y + hover - lift, progress)
    # ============================================================
    # BODY - Crocodile warrior
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Tail behind
        _NS_sethrakhar._draw_croc_tail(surface, cx, cy + 4, facing, phase, action)
        # Back arm (holds nothing)
        _NS_sethrakhar._draw_back_arm(surface, cx, cy - 2, facing, phase)
        # Torso (muscular chest)
        _NS_sethrakhar._draw_muscular_torso(surface, cx, cy, facing, phase)
        # Loincloth
        _NS_sethrakhar._draw_loincloth(surface, cx, cy + 8, facing, phase, action)
        # Legs (dangling)
        _NS_sethrakhar._draw_croc_legs(surface, cx, cy + 8, facing, phase, action)
        # Head (crocodile head with big jaw)
        _NS_sethrakhar._draw_croc_head(surface, cx, cy - 18, facing, phase, action,
                                       attack_progress)
        # Front arm holding khopesh (LAST for priority)
        _NS_sethrakhar._draw_khopesh_arm(surface, cx, cy - 2, facing, phase, action,
                                         attack_progress)
    def _draw_croc_tail(surface, cx, cy, facing, phase, action):
        """Long crocodile tail curving behind."""
        back = -facing
        base_x = cx + back * 10
        base_y = cy + 4
        tail_wave = math.sin(phase * 1.2) * 3
        if action == "float":
            tail_wave = math.sin(phase * 1.5) * 5
        segments = 7
        points = [(base_x, base_y)]
        for i in range(1, segments + 1):
            t = i / segments
            x_off = int(back * (10 + t * 24))
            y_off = int(4 + t * 8 - t * t * 4)
            wave = math.sin(phase * 1.2 + t * math.pi) * (4 + t * 3)
            y_off += int(wave)
            points.append((base_x + x_off, base_y + y_off))
        # Draw tapered tail
        for i in range(len(points) - 1):
            thickness = max(2, 11 - i)
            _NS_sethrakhar._aaline(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                                   (points[i][0] + 2, points[i][1] + 2),
                                   (points[i + 1][0] + 2, points[i + 1][1] + 2),
                                   thickness + 1)
            _NS_sethrakhar._aaline(surface, _NS_sethrakhar.PALETTE["scale_darkest"],
                                   points[i], points[i + 1], thickness)
            _NS_sethrakhar._aaline(surface, _NS_sethrakhar.PALETTE["scale_dark"],
                                   points[i], points[i + 1], max(1, thickness - 2))
            _NS_sethrakhar._aaline(surface, _NS_sethrakhar.PALETTE["scale_mid"],
                                   (points[i][0], points[i][1] - 1),
                                   (points[i + 1][0], points[i + 1][1] - 1),
                                   max(1, thickness - 4))
            # Belly stripe
            _NS_sethrakhar._aaline(surface, _NS_sethrakhar.PALETTE["belly_dark"],
                                   (points[i][0], points[i][1] + 1),
                                   (points[i + 1][0], points[i + 1][1] + 1),
                                   max(1, thickness - 4))
            _NS_sethrakhar._aaline(surface, _NS_sethrakhar.PALETTE["belly_mid"],
                                   (points[i][0], points[i][1] + 2),
                                   (points[i + 1][0], points[i + 1][1] + 2),
                                   max(1, thickness - 6))
        # Dorsal spikes along tail
        for i in range(1, len(points) - 1, 2):
            spike_size = max(1, 4 - i // 2)
            spike_x = points[i][0]
            spike_y = points[i][1] - max(1, 5 - i)
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["scale_darkest"], [
                (points[i][0] - 2, points[i][1] - 1),
                (spike_x, spike_y),
                (points[i][0] + 2, points[i][1] - 1),
            ])
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["scale_dark"], [
                (points[i][0] - 1, points[i][1] - 1),
                (spike_x, spike_y),
                (points[i][0] + 1, points[i][1] - 1),
            ])
            pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["scale_edge"],
                             (spike_x, spike_y, 1, 1))
    def _draw_muscular_torso(surface, cx, cy, facing, phase):
        """Big muscular crocodile chest with armor."""
        breath = math.sin(phase * 0.7) * 1
        # Base torso (wider than normal humanoid - big brute)
        torso_pts = [
            (cx - 11, cy - 6),
            (cx - 12, cy),
            (cx - 11, cy + 7),
            (cx - 8, cy + 11),
            (cx + 8, cy + 11),
            (cx + 11, cy + 7),
            (cx + 12, cy),
            (cx + 11, cy - 6),
        ]
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in torso_pts])
        # Scale layer (green scales)
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["scale_darkest"], torso_pts)
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["scale_dark"], [
            (cx - 10, cy - 5),
            (cx - 11, cy),
            (cx - 10, cy + 6),
            (cx - 7, cy + 10),
            (cx + 7, cy + 10),
            (cx + 10, cy + 6),
            (cx + 11, cy),
            (cx + 10, cy - 5),
        ])
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["scale_mid"], [
            (cx - 8, cy - 4),
            (cx - 9, cy),
            (cx - 8, cy + 4),
            (cx - 5, cy + 8),
            (cx + 5, cy + 8),
            (cx + 8, cy + 4),
            (cx + 9, cy),
            (cx + 8, cy - 4),
        ])
        # BELLY (lighter tan - big muscular abs)
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["belly_dark"], [
            (cx - 6, cy - 2),
            (cx + 6, cy - 2),
            (cx + 7, cy + 2),
            (cx + 6, cy + 7),
            (cx + 3, cy + 10),
            (cx - 3, cy + 10),
            (cx - 6, cy + 7),
            (cx - 7, cy + 2),
        ])
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["belly_mid"], [
            (cx - 5, cy - 1),
            (cx + 5, cy - 1),
            (cx + 6, cy + 2),
            (cx + 5, cy + 6),
            (cx + 2, cy + 9),
            (cx - 2, cy + 9),
            (cx - 5, cy + 6),
            (cx - 6, cy + 2),
        ])
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["belly_light"], [
            (cx - 3, cy),
            (cx + 3, cy),
            (cx + 4, cy + 3),
            (cx + 3, cy + 6),
            (cx - 3, cy + 6),
            (cx - 4, cy + 3),
        ])
        # AB LINES (segment stripes on belly)
        for i, ab_y in enumerate((cy + 1, cy + 4, cy + 7)):
            pygame.draw.line(surface, _NS_sethrakhar.PALETTE["belly_darkest"],
                             (cx - 4 + i, ab_y), (cx + 4 - i, ab_y), 1)
        # Center line
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["belly_darkest"],
                         (cx, cy), (cx, cy + 9), 1)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["belly_dark"],
                         (cx, cy), (cx, cy + 9), 1)
        # Scale texture on green parts (small V chevrons)
        for row in range(2):
            y_row = cy - 4 + row * 3
            for i, dx in enumerate((-9, -8, 8, 9)):
                pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_darkest"],
                                 (cx + dx, y_row), (cx + dx, y_row + 1), 1)
                pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["scale_edge"],
                                 (cx + dx, y_row, 1, 1))
        # SHOULDER PAULDRONS (golden ornate)
        for side in (-1, 1):
            paul_x = cx + side * 11
            paul_y = cy - 6
            # Base
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["shadow_deep"], [
                (paul_x - 4, paul_y),
                (paul_x + 4, paul_y),
                (paul_x + 5, paul_y + 5),
                (paul_x + 3, paul_y + 7),
                (paul_x - 3, paul_y + 7),
                (paul_x - 5, paul_y + 5),
            ])
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["bronze_darkest"], [
                (paul_x - 4, paul_y - 1),
                (paul_x + 4, paul_y - 1),
                (paul_x + 5, paul_y + 4),
                (paul_x + 3, paul_y + 6),
                (paul_x - 3, paul_y + 6),
                (paul_x - 5, paul_y + 4),
            ])
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["gold_darkest"], [
                (paul_x - 3, paul_y - 1),
                (paul_x + 3, paul_y - 1),
                (paul_x + 4, paul_y + 3),
                (paul_x + 2, paul_y + 5),
                (paul_x - 2, paul_y + 5),
                (paul_x - 4, paul_y + 3),
            ])
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["gold_dark"], [
                (paul_x - 3, paul_y),
                (paul_x + 3, paul_y),
                (paul_x + 3, paul_y + 3),
                (paul_x - 3, paul_y + 3),
            ])
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["gold_mid"], [
                (paul_x - 2, paul_y),
                (paul_x + 2, paul_y),
                (paul_x + 2, paul_y + 2),
                (paul_x - 2, paul_y + 2),
            ])
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["gold_light"], [
                (paul_x - 2, paul_y),
                (paul_x + 2, paul_y),
                (paul_x, paul_y + 1),
            ])
            pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["gold_shine"],
                             (paul_x, paul_y, 1, 1))
            # Big spike on pauldron (backward-facing curved horn)
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["shadow_deep"], [
                (paul_x, paul_y - 6),
                (paul_x - 2, paul_y),
                (paul_x + 2, paul_y),
            ])
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["bronze_dark"], [
                (paul_x - side, paul_y - 5),
                (paul_x - 2, paul_y),
                (paul_x + 2, paul_y),
            ])
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["gold_dark"], [
                (paul_x - side, paul_y - 5),
                (paul_x - 1, paul_y),
                (paul_x + 1, paul_y),
            ])
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["gold_light"], [
                (paul_x - side, paul_y - 4),
                (paul_x, paul_y),
                (paul_x + 1, paul_y),
            ])
            pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["gold_shine"],
                             (paul_x - side, paul_y - 4, 1, 1))
        # WAIST BELT (dark bronze with gold trim)
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["bronze_darkest"],
                         (cx - 9, cy + 8, 18, 3))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["bronze_dark"],
                         (cx - 9, cy + 8, 18, 2))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["gold_dark"],
                         (cx - 9, cy + 8, 18, 1))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["gold_light"],
                         (cx - 8, cy + 8, 16, 1))
        # Belt buckle (fury gem)
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["gold_dark"],
                         (cx - 2, cy + 8, 5, 3))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fury_dark"],
                         (cx - 1, cy + 9, 3, 1))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fury_light"],
                         (cx, cy + 9, 1, 1))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fury_shine"],
                         (cx, cy + 9, 1, 1))
    def _draw_loincloth(surface, cx, cy, facing, phase, action):
        """Dark red loincloth hanging from belt."""
        sway = math.sin(phase * 0.5) * 2
        cloth_pts = [
            (cx - 5, cy),
            (cx - 6, cy + 6 + int(sway * 0.5)),
            (cx - 5, cy + 12 + int(sway)),
            (cx - 3, cy + 15 + int(sway * 0.8)),
            (cx, cy + 16 + int(sway * 0.6)),
            (cx + 3, cy + 15 + int(sway * 0.8)),
            (cx + 5, cy + 12 + int(sway)),
            (cx + 6, cy + 6 + int(sway * 0.5)),
            (cx + 5, cy),
        ]
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                             [(px + 1, py + 2) for px, py in cloth_pts])
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["cloth_darkest"], cloth_pts)
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["cloth_dark"], [
            (cx - 4, cy + 1),
            (cx - 5, cy + 6 + int(sway * 0.4)),
            (cx - 4, cy + 11 + int(sway * 0.9)),
            (cx - 2, cy + 13),
            (cx, cy + 14 + int(sway * 0.5)),
            (cx + 2, cy + 13),
            (cx + 4, cy + 11 + int(sway * 0.9)),
            (cx + 5, cy + 6 + int(sway * 0.4)),
            (cx + 4, cy + 1),
        ])
        # Highlight fold
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["cloth_mid"],
                         (cx, cy + 1), (cx + int(sway * 0.5), cy + 14), 1)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["cloth_light"],
                         (cx - 1, cy + 3), (cx - 1 + int(sway * 0.4), cy + 11), 1)
        # Gold trim along top edge
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["gold_dark"],
                         (cx - 5, cy), (cx + 5, cy), 1)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["gold_light"],
                         (cx - 5, cy), (cx + 5, cy), 1)
    def _draw_croc_legs(surface, cx, cy, facing, phase, action):
        """Muscular scaled legs (dangling)."""
        sway = math.sin(phase * 0.9) * 1.5
        for side in (-1, 1):
            leg_x_top = cx + side * 5
            leg_x_bot = cx + side * 6 + int(sway * side * 0.5)
            leg_y_top = cy
            leg_y_bot = cy + 15
            # Thick thigh
            pygame.draw.line(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                             (leg_x_top + 1, leg_y_top + 1),
                             (leg_x_bot + 1, leg_y_bot + 1), 7)
            pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_darkest"],
                             (leg_x_top, leg_y_top),
                             (leg_x_bot, leg_y_bot), 6)
            pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_dark"],
                             (leg_x_top, leg_y_top),
                             (leg_x_bot, leg_y_bot), 5)
            pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_mid"],
                             (leg_x_top - side, leg_y_top),
                             (leg_x_bot - side, leg_y_bot), 3)
            pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_edge"],
                             (leg_x_top - side, leg_y_top + 2),
                             (leg_x_bot - side, leg_y_bot - 2), 1)
            # Belly side
            pygame.draw.line(surface, _NS_sethrakhar.PALETTE["belly_dark"],
                             (leg_x_top + side, leg_y_top + 2),
                             (leg_x_bot + side, leg_y_bot - 2), 2)
            pygame.draw.line(surface, _NS_sethrakhar.PALETTE["belly_mid"],
                             (leg_x_top + side, leg_y_top + 3),
                             (leg_x_bot + side, leg_y_bot - 3), 1)
            # Golden greaves (armor at ankle)
            greave_x = leg_x_bot
            greave_y = leg_y_bot + 1
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["shadow_deep"], [
                (greave_x - 4, greave_y - 2),
                (greave_x + 4, greave_y - 2),
                (greave_x + 5, greave_y + 3),
                (greave_x - 5, greave_y + 3),
            ])
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["gold_darkest"], [
                (greave_x - 4, greave_y - 3),
                (greave_x + 4, greave_y - 3),
                (greave_x + 4, greave_y + 2),
                (greave_x - 4, greave_y + 2),
            ])
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["gold_dark"], [
                (greave_x - 3, greave_y - 3),
                (greave_x + 3, greave_y - 3),
                (greave_x + 3, greave_y + 1),
                (greave_x - 3, greave_y + 1),
            ])
            pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["gold_mid"],
                             (greave_x - 3, greave_y - 3, 6, 2))
            pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["gold_light"],
                             (greave_x - 3, greave_y - 3, 6, 1))
            # Clawed foot (3 toes with claws)
            for i, toe_x_off in enumerate((-3, 0, 3)):
                toe_x = greave_x + toe_x_off
                toe_y = greave_y + 3
                pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["scale_dark"],
                                 (toe_x, toe_y, 2, 2))
                pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["scale_mid"],
                                 (toe_x, toe_y, 1, 1))
                # Claw
                pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fang_light"],
                                 (toe_x, toe_y + 2, 1, 1))
    def _draw_back_arm(surface, cx, cy, facing, phase):
        """Back arm - muscular hanging."""
        back_shoulder_x = cx - facing * 6
        back_shoulder_y = cy - 2
        arm_angle = math.pi * 0.4 + math.sin(phase * 0.5) * 0.1
        arm_length = 13
        back_hand_x = back_shoulder_x - int(math.cos(arm_angle) * arm_length) * facing
        back_hand_y = back_shoulder_y + int(math.sin(arm_angle) * arm_length) + 2
        elbow_x = back_shoulder_x - int(math.cos(arm_angle) * (arm_length * 0.5)) * facing
        elbow_y = back_shoulder_y + int(math.sin(arm_angle) * (arm_length * 0.5))
        # Upper arm (scaled)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                         (back_shoulder_x + 1, back_shoulder_y + 1),
                         (elbow_x + 1, elbow_y + 1), 6)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_darkest"],
                         (back_shoulder_x, back_shoulder_y),
                         (elbow_x, elbow_y), 5)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_dark"],
                         (back_shoulder_x, back_shoulder_y),
                         (elbow_x, elbow_y), 4)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_mid"],
                         (back_shoulder_x - 1, back_shoulder_y),
                         (elbow_x - 1, elbow_y), 2)
        # Forearm
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                         (elbow_x + 1, elbow_y + 1),
                         (back_hand_x + 1, back_hand_y + 1), 5)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_darkest"],
                         (elbow_x, elbow_y), (back_hand_x, back_hand_y), 4)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_dark"],
                         (elbow_x, elbow_y), (back_hand_x, back_hand_y), 3)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_mid"],
                         (elbow_x - 1, elbow_y), (back_hand_x - 1, back_hand_y), 2)
        # Bronze bracer at forearm
        forearm_mid_x = int((elbow_x + back_hand_x) / 2)
        forearm_mid_y = int((elbow_y + back_hand_y) / 2)
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["bronze_darkest"],
                         (forearm_mid_x - 3, forearm_mid_y - 2, 6, 4))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["bronze_dark"],
                         (forearm_mid_x - 3, forearm_mid_y - 2, 6, 3))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["gold_dark"],
                         (forearm_mid_x - 3, forearm_mid_y - 2, 6, 1))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["gold_light"],
                         (forearm_mid_x - 2, forearm_mid_y - 2, 4, 1))
        # Clawed fist
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                         (back_hand_x - 2, back_hand_y - 1, 5, 5))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["scale_darkest"],
                         (back_hand_x - 2, back_hand_y - 1, 4, 4))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["scale_dark"],
                         (back_hand_x - 2, back_hand_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["scale_mid"],
                         (back_hand_x - 1, back_hand_y - 1, 3, 2))
        # Claws
        for i in range(3):
            claw_x = back_hand_x - facing * (2 - i)
            claw_y = back_hand_y + 3
            pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fang_dark"],
                             (claw_x, claw_y, 1, 2))
            pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fang_light"],
                             (claw_x, claw_y + 1, 1, 1))
    def _draw_khopesh_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding massive khopesh."""
        shoulder_x = cx + facing * 6
        shoulder_y = cy - 2
        # Attack: raise weapon and swing
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                arm_angle = -math.pi * 0.6 * t  # raise up
                weapon_angle = -math.pi * 0.7 - t * math.pi * 0.3
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                arm_angle = -math.pi * 0.6 + math.pi * 1.0 * t  # swing down
                weapon_angle = -math.pi * 1.0 + math.pi * 1.4 * t
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * 0.4 * (1 - t) - math.pi * 0.1 * t
                weapon_angle = math.pi * 0.4 * (1 - t) - math.pi * 0.3 * t
        else:
            # Battle stance - weapon on side
            arm_angle = math.pi * 0.15 + math.sin(phase * 0.5) * 0.1
            weapon_angle = -math.pi * 0.15
        arm_length = 13
        hand_x = shoulder_x + int(math.cos(arm_angle) * arm_length) * facing
        hand_y = shoulder_y + int(math.sin(arm_angle) * arm_length) + 4
        elbow_x = shoulder_x + int(math.cos(arm_angle) * (arm_length * 0.55)) * facing
        elbow_y = shoulder_y + int(math.sin(arm_angle) * (arm_length * 0.55)) + 2
        # Upper arm (scaled + muscular)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                         (shoulder_x + 1, shoulder_y + 1),
                         (elbow_x + 1, elbow_y + 1), 7)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_darkest"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_dark"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_mid"],
                         (shoulder_x - 1, shoulder_y),
                         (elbow_x - 1, elbow_y), 3)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_edge"],
                         (shoulder_x - 1, shoulder_y + 1),
                         (elbow_x - 1, elbow_y - 1), 1)
        # Forearm
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                         (elbow_x + 1, elbow_y + 1),
                         (hand_x + 1, hand_y + 1), 6)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_darkest"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 5)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_dark"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 4)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_mid"],
                         (elbow_x - 1, elbow_y), (hand_x - 1, hand_y), 2)
        # Big golden bracer (ornate)
        forearm_mid_x = int((elbow_x + hand_x) / 2)
        forearm_mid_y = int((elbow_y + hand_y) / 2)
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                         (forearm_mid_x - 4, forearm_mid_y - 3, 8, 6))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["bronze_darkest"],
                         (forearm_mid_x - 4, forearm_mid_y - 3, 8, 5))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["gold_darkest"],
                         (forearm_mid_x - 4, forearm_mid_y - 3, 8, 4))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["gold_dark"],
                         (forearm_mid_x - 3, forearm_mid_y - 3, 6, 3))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["gold_mid"],
                         (forearm_mid_x - 3, forearm_mid_y - 3, 6, 2))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["gold_light"],
                         (forearm_mid_x - 2, forearm_mid_y - 3, 4, 1))
        # Fury gem in bracer
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fury_dark"],
                         (forearm_mid_x - 1, forearm_mid_y - 1, 2, 2))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fury_hot"],
                         (forearm_mid_x, forearm_mid_y - 1, 1, 1))
        # Clawed fist gripping weapon
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                         (hand_x - 2, hand_y - 1, 5, 5))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["scale_darkest"],
                         (hand_x - 2, hand_y - 1, 4, 4))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["scale_dark"],
                         (hand_x - 2, hand_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["scale_mid"],
                         (hand_x - 1, hand_y - 1, 3, 2))
        # KHOPESH WEAPON (massive curved double-blade)
        _NS_sethrakhar._draw_khopesh(surface, hand_x, hand_y, facing, phase,
                                     action, attack_progress, weapon_angle)
    def _draw_khopesh(surface, hand_x, hand_y, facing, phase, action,
                      attack_progress, weapon_angle):
        """Massive curved double-blade khopesh (Egyptian-style sickle sword)."""
        # Weapon direction
        # Grip end
        grip_len = 8
        grip_end_x = hand_x - int(math.cos(weapon_angle) * grip_len) * facing
        grip_end_y = hand_y - int(math.sin(weapon_angle) * grip_len)
        # Handle
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                         (grip_end_x + 1, grip_end_y + 1),
                         (hand_x + 1, hand_y + 1), 4)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["bronze_darkest"],
                         (grip_end_x, grip_end_y), (hand_x, hand_y), 3)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["bronze_dark"],
                         (grip_end_x, grip_end_y), (hand_x, hand_y), 2)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["bronze_mid"],
                         (grip_end_x, grip_end_y), (hand_x, hand_y), 1)
        # Pommel (skull-shaped at end)
        _NS_sethrakhar._aacircle(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                                 (grip_end_x, grip_end_y), 4)
        _NS_sethrakhar._aacircle(surface, _NS_sethrakhar.PALETTE["gold_darkest"],
                                 (grip_end_x, grip_end_y), 3)
        _NS_sethrakhar._aacircle(surface, _NS_sethrakhar.PALETTE["gold_dark"],
                                 (grip_end_x, grip_end_y), 2)
        _NS_sethrakhar._aacircle(surface, _NS_sethrakhar.PALETTE["gold_light"],
                                 (grip_end_x, grip_end_y), 1)
        # GUARD (base of blade)
        guard_len = 6
        guard_x = hand_x + int(math.cos(weapon_angle) * guard_len) * facing
        guard_y = hand_y + int(math.sin(weapon_angle) * guard_len)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                         (hand_x + 1, hand_y + 1),
                         (guard_x + 1, guard_y + 1), 5)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["bronze_darkest"],
                         (hand_x, hand_y), (guard_x, guard_y), 4)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["gold_dark"],
                         (hand_x, hand_y), (guard_x, guard_y), 3)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["gold_mid"],
                         (hand_x, hand_y), (guard_x, guard_y), 2)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["gold_light"],
                         (hand_x, hand_y), (guard_x, guard_y), 1)
        # HUGE CURVED BLADE (khopesh style - curves outward like a sickle)
        # Blade curves ~90 degrees
        perp_x = -math.sin(weapon_angle)
        perp_y = math.cos(weapon_angle)
        # Blade start (at guard) → curves → tip
        blade_segments = 8
        prev = (guard_x, guard_y)
        blade_points = []
        for i in range(1, blade_segments + 1):
            t = i / blade_segments
            # Bezier curve for blade
            # From guard, curves outward-forward
            curve_angle = weapon_angle + t * math.pi * 0.5  # 90-degree curve
            radius = 22
            bx = int(guard_x + math.cos(curve_angle) * radius * facing - math.cos(weapon_angle) * radius * facing)
            by = int(guard_y + math.sin(curve_angle) * radius - math.sin(weapon_angle) * radius)
            blade_points.append((bx, by))
        # Draw blade as thick curved shape (with double-edge)
        for i in range(len(blade_points) - 1):
            thickness = max(3, 8 - i)
            p1 = blade_points[i] if i > 0 else prev
            p2 = blade_points[i + 1]
            # Shadow
            pygame.draw.line(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                             (p1[0] + 2, p1[1] + 2),
                             (p2[0] + 2, p2[1] + 2), thickness + 1)
            # Blade body (dark bronze base)
            pygame.draw.line(surface, _NS_sethrakhar.PALETTE["bronze_darkest"],
                             p1, p2, thickness)
            pygame.draw.line(surface, _NS_sethrakhar.PALETTE["bronze_dark"],
                             p1, p2, thickness - 1)
            pygame.draw.line(surface, _NS_sethrakhar.PALETTE["gold_darkest"],
                             p1, p2, max(1, thickness - 2))
            pygame.draw.line(surface, _NS_sethrakhar.PALETTE["gold_dark"],
                             p1, p2, max(1, thickness - 3))
            pygame.draw.line(surface, _NS_sethrakhar.PALETTE["gold_mid"],
                             (p1[0], p1[1] - 1), (p2[0], p2[1] - 1),
                             max(1, thickness - 4))
            # Steel edge (sharp)
            pygame.draw.line(surface, _NS_sethrakhar.PALETTE["blade_mid"],
                             (p1[0], p1[1] - 2), (p2[0], p2[1] - 2), 1)
            pygame.draw.line(surface, _NS_sethrakhar.PALETTE["blade_shine"],
                             (p1[0], p1[1] - 3), (p2[0], p2[1] - 3), 1)
        # Sharp tip
        if blade_points:
            tip = blade_points[-1]
            pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["blade_light"],
                             (tip[0], tip[1], 2, 2))
            pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["blade_shine"],
                             (tip[0], tip[1], 1, 1))
            pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["white"],
                             (tip[0], tip[1], 1, 1))
        # SECOND BLADE (small back-hook - khopesh signature)
        # Small curved hook on back of blade near guard
        back_hook_x = guard_x + int(math.cos(weapon_angle + math.pi * 0.7) * 8) * facing
        back_hook_y = guard_y + int(math.sin(weapon_angle + math.pi * 0.7) * 8)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                         (guard_x + 1, guard_y + 1),
                         (back_hook_x + 1, back_hook_y + 1), 4)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["gold_dark"],
                         (guard_x, guard_y),
                         (back_hook_x, back_hook_y), 3)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["gold_mid"],
                         (guard_x, guard_y),
                         (back_hook_x, back_hook_y), 2)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["gold_light"],
                         (guard_x, guard_y),
                         (back_hook_x, back_hook_y), 1)
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["blade_shine"],
                         (back_hook_x, back_hook_y, 1, 1))
        # FURY FLAMES around blade (constant)
        flame_pulse = math.sin(phase * 3) * 0.3 + 0.7
        for i, blade_pt in enumerate(blade_points[::2]):
            flame_alpha = _NS_sethrakhar._alpha(180 * flame_pulse)
            for r in range(4, 0, -1):
                alpha = _NS_sethrakhar._alpha(flame_alpha * (4 - r) / 4)
                _NS_sethrakhar._aacircle(surface,
                                         (*_NS_sethrakhar.PALETTE["fury_mid"], alpha),
                                         blade_pt, r)
            pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fury_hot"],
                             (blade_pt[0], blade_pt[1] - 2, 1, 1))
            pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fury_shine"],
                             (blade_pt[0], blade_pt[1] - 2, 1, 1))
    def _draw_croc_head(surface, cx, cy, facing, phase, action, attack_progress):
        """Big crocodile head with massive jaws and fangs."""
        # Head shape (elongated snout forward)
        head_shape = [
            (cx - 7 * facing, cy + 4),      # back bottom
            (cx - 9 * facing, cy),          # back top
            (cx - 8 * facing, cy - 6),      # crown back
            (cx - 3 * facing, cy - 9),      # top mid
            (cx + 4 * facing, cy - 7),      # top front
            (cx + 12 * facing, cy - 4),     # snout top
            (cx + 20 * facing, cy - 1),     # snout tip top
            (cx + 22 * facing, cy + 3),     # snout tip
            (cx + 20 * facing, cy + 6),     # snout tip bottom
            (cx + 12 * facing, cy + 8),     # snout bottom
            (cx + 4 * facing, cy + 9),      # jaw front
            (cx - 4 * facing, cy + 9),      # jaw back
        ]
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in head_shape])
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["scale_darkest"], head_shape)
        # Green top
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["scale_dark"], [
            (cx - 7 * facing, cy + 3),
            (cx - 8 * facing, cy),
            (cx - 7 * facing, cy - 5),
            (cx - 2 * facing, cy - 8),
            (cx + 4 * facing, cy - 6),
            (cx + 11 * facing, cy - 3),
            (cx + 19 * facing, cy),
            (cx + 21 * facing, cy + 2),
            (cx + 17 * facing, cy + 2),
            (cx + 5 * facing, cy - 1),
            (cx - 5 * facing, cy),
        ])
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["scale_mid"], [
            (cx - 5 * facing, cy - 1),
            (cx - 3 * facing, cy - 6),
            (cx + 4 * facing, cy - 6),
            (cx + 11 * facing, cy - 2),
            (cx + 17 * facing, cy),
            (cx + 5 * facing, cy - 2),
        ])
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["scale_edge"], [
            (cx - 2 * facing, cy - 4),
            (cx + 3 * facing, cy - 5),
            (cx + 8 * facing, cy - 3),
            (cx + 5 * facing, cy - 2),
        ])
        # SNOUT belly tan (bottom of snout)
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["belly_dark"], [
            (cx + 12 * facing, cy - 2),
            (cx + 19 * facing, cy),
            (cx + 21 * facing, cy + 3),
            (cx + 19 * facing, cy + 5),
            (cx + 12 * facing, cy + 7),
        ])
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["belly_mid"], [
            (cx + 13 * facing, cy),
            (cx + 18 * facing, cy + 2),
            (cx + 17 * facing, cy + 4),
            (cx + 13 * facing, cy + 5),
        ])
        # Jaw (bottom)
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["belly_dark"], [
            (cx - 3 * facing, cy + 8),
            (cx + 5 * facing, cy + 8),
            (cx + 14 * facing, cy + 6),
            (cx + 12 * facing, cy + 8),
            (cx + 3 * facing, cy + 9),
        ])
        # SPIKES on top of head/crown (dorsal ridge)
        for i, x_off in enumerate((-6, -3, 0, 3, 6, 9)):
            spike_wave = math.sin(phase * 0.5 + i * 0.4) * 1
            spike_size = 3 + int((1 - abs(x_off - 3) / 9) * 3)
            spike_x = cx + int(x_off * facing)
            spike_base_y = cy - 8
            spike_tip_y = spike_base_y - spike_size - int(spike_wave)
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_tip_y + 1),
                (spike_x - 2, spike_base_y + 1),
                (spike_x + 2, spike_base_y + 1),
            ])
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["scale_darkest"], [
                (spike_x, spike_tip_y),
                (spike_x - 2, spike_base_y),
                (spike_x + 2, spike_base_y),
            ])
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["fury_dark"], [
                (spike_x, spike_tip_y),
                (spike_x - 1, spike_base_y),
                (spike_x + 1, spike_base_y),
            ])
            pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fury_hot"],
                             (spike_x, spike_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fury_shine"],
                             (spike_x, spike_tip_y, 1, 1))
        # GOLDEN HEADDRESS/CROWN on back of head
        _NS_sethrakhar._draw_headdress(surface, cx, cy - 8, facing, phase)
        # AMBER EYE (fierce red-orange)
        _NS_sethrakhar._draw_croc_eye(surface, cx + 2 * facing, cy - 3, facing, phase, action)
        # NOSTRIL
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                         (cx + 18 * facing, cy, 2, 1))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fury_dark"],
                         (cx + 19 * facing, cy, 1, 1))
        # MASSIVE FANGS + MOUTH (opens on attack)
        mouth_open = 0
        if action == "attack":
            mouth_open = max(0, math.sin(attack_progress * math.pi) * 6)
        _NS_sethrakhar._draw_croc_mouth(surface, cx, cy, facing, phase, mouth_open)
    def _draw_headdress(surface, cx, cy, facing, phase):
        """Golden pharaoh-style headdress on back of crocodile head."""
        # Small crest at back
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["shadow_deep"], [
            (cx - 8 * facing, cy + 1),
            (cx - 6 * facing, cy - 3),
            (cx - 3 * facing, cy - 4),
            (cx - 2 * facing, cy - 1),
        ])
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["gold_darkest"], [
            (cx - 7 * facing, cy),
            (cx - 5 * facing, cy - 3),
            (cx - 2 * facing, cy - 3),
            (cx - 1 * facing, cy - 1),
        ])
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["gold_dark"], [
            (cx - 6 * facing, cy),
            (cx - 4 * facing, cy - 2),
            (cx - 2 * facing, cy - 2),
            (cx - 1 * facing, cy),
        ])
        _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["gold_mid"], [
            (cx - 5 * facing, cy - 1),
            (cx - 3 * facing, cy - 2),
            (cx - 2 * facing, cy - 1),
        ])
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["gold_light"],
                         (cx - 4 * facing, cy - 2, 1, 1))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["gold_shine"],
                         (cx - 4 * facing, cy - 2, 1, 1))
    def _draw_croc_eye(surface, cx, cy, facing, phase, action):
        """Fierce amber/red eye."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        intensity = 1.5 if action == "attack" else 1.0
        ex = cx
        ey = cy
        # Deep socket
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                         (ex - 2, ey - 2, 5, 4))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["eye_socket"],
                         (ex - 1, ey - 2, 4, 4))
        # Glow halo (orange/red)
        for radius in range(6, 0, -1):
            alpha = _NS_sethrakhar._alpha(100 * (6 - radius) / 6 * pulse * intensity)
            _NS_sethrakhar._aacircle(surface,
                                     (*_NS_sethrakhar.PALETTE["eye_mid"], alpha),
                                     (ex + 1, ey), radius)
        # Iris (amber)
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["eye_dark"],
                         (ex - 1, ey - 1, 4, 3))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["eye_mid"],
                         (ex, ey - 1, 3, 3))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["eye_light"],
                         (ex + 1, ey - 1, 2, 2))
        # Bright core
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["eye_glow"],
                         (ex + 2, ey, 1, 1))
        pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["white"],
                         (ex + 2, ey, 1, 1))
        # Vertical reptilian pupil
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                         (ex + 1, ey - 1), (ex + 1, ey + 1), 1)
        # Eyebrow ridge (crocodile scale ridge above eye)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_darkest"],
                         (ex - 2, ey - 3), (ex + 3, ey - 3), 1)
        pygame.draw.line(surface, _NS_sethrakhar.PALETTE["scale_dark"],
                         (ex - 2, ey - 3), (ex + 3, ey - 3), 1)
    def _draw_croc_mouth(surface, cx, cy, facing, phase, mouth_open):
        """Massive jaws with sharp fangs (Renekton signature)."""
        mouth_y = cy + 4
        mouth_x_start = cx + 5 * facing
        mouth_x_end = cx + 20 * facing
        if mouth_open > 0:
            # Open mouth cavity (dark)
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["shadow_deep"], [
                (mouth_x_start, mouth_y),
                (mouth_x_end, mouth_y),
                (mouth_x_end, mouth_y + int(mouth_open)),
                (mouth_x_start, mouth_y + int(mouth_open * 0.6)),
            ])
            _NS_sethrakhar._poly(surface, _NS_sethrakhar.PALETTE["cloth_darkest"], [
                (mouth_x_start + facing, mouth_y + 1),
                (mouth_x_end - facing, mouth_y + 1),
                (mouth_x_end - facing, mouth_y + int(mouth_open) - 1),
                (mouth_x_start + facing, mouth_y + int(mouth_open * 0.6) - 1),
            ])
            # Fury glow inside (angry roar)
            glow_r = int(3 + mouth_open * 0.4)
            for r in range(glow_r + 2, 0, -1):
                alpha = _NS_sethrakhar._alpha(200 * (glow_r + 2 - r) / (glow_r + 2))
                _NS_sethrakhar._aacircle(surface,
                                         (*_NS_sethrakhar.PALETTE["fury_dark"], alpha),
                                         (cx + 12 * facing, mouth_y + int(mouth_open * 0.5)), r)
            _NS_sethrakhar._aacircle(surface, _NS_sethrakhar.PALETTE["fury_mid"],
                                     (cx + 12 * facing, mouth_y + int(mouth_open * 0.5)),
                                     max(1, glow_r - 1))
            _NS_sethrakhar._aacircle(surface, _NS_sethrakhar.PALETTE["fury_hot"],
                                     (cx + 12 * facing, mouth_y + int(mouth_open * 0.5)),
                                     max(1, glow_r - 3))
            pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fury_shine"],
                             (cx + 12 * facing, mouth_y + int(mouth_open * 0.5), 1, 1))
            # UPPER FANGS (many sharp teeth like reference)
            for i, x_off in enumerate((6, 9, 12, 15, 18)):
                fang_x = cx + int(x_off * facing)
                fang_tip_y = mouth_y + int(mouth_open * 0.85)
                fang_h = int(mouth_open * 0.85)
                pygame.draw.line(surface, _NS_sethrakhar.PALETTE["fang_dark"],
                                 (fang_x, mouth_y), (fang_x, fang_tip_y), 2)
                pygame.draw.line(surface, _NS_sethrakhar.PALETTE["fang_mid"],
                                 (fang_x, mouth_y), (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fang_light"],
                                 (fang_x, fang_tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fang_shine"],
                                 (fang_x, fang_tip_y, 1, 1))
            # LOWER FANGS
            for i, x_off in enumerate((7, 10, 13, 16, 19)):
                fang_x = cx + int(x_off * facing)
                fang_top_y = mouth_y + int(mouth_open) - 1
                fang_tip_y = fang_top_y - 3
                pygame.draw.line(surface, _NS_sethrakhar.PALETTE["fang_dark"],
                                 (fang_x, fang_top_y), (fang_x, fang_tip_y), 2)
                pygame.draw.line(surface, _NS_sethrakhar.PALETTE["fang_mid"],
                                 (fang_x, fang_top_y), (fang_x, fang_tip_y), 1)
                pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fang_light"],
                                 (fang_x, fang_tip_y, 1, 1))
        else:
            # Closed mouth (grinning with visible fangs)
            pygame.draw.line(surface, _NS_sethrakhar.PALETTE["shadow_deep"],
                             (mouth_x_start, mouth_y + 1),
                             (mouth_x_end, mouth_y + 1), 1)
            # Visible fang tips
            for x_off in (7, 10, 13, 16, 19):
                fang_x = cx + int(x_off * facing)
                pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fang_mid"],
                                 (fang_x, mouth_y, 1, 3))
                pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fang_light"],
                                 (fang_x, mouth_y + 1, 1, 1))
    # ============================================================
    # MELEE ATTACK - KHOPESH SLASH
    # ============================================================
    def _draw_khopesh_slash(surface, boss, x, y, progress):
        """Massive fire slash arc during khopesh swing."""
        if progress < 0.4 or progress > 0.85:
            return
        facing = boss.direction
        t = (progress - 0.4) / 0.45
        t = min(1.0, max(0.0, t))
        center_x = x + facing * 10
        center_y = y - 4
        radius = 38 + int(t * 12)
        # Downward slash arc
        start_angle = -math.pi * 0.7 + t * 0.4
        end_angle = math.pi * 0.5 - (1 - t) * 0.4
        # Main slash - fiery orange
        num_slashes = 8
        for i in range(num_slashes):
            slash_t = i / (num_slashes - 1)
            angle = start_angle + (end_angle - start_angle) * slash_t
            inner_x = center_x + int(math.cos(angle) * (radius - 15)) * facing
            inner_y = center_y + int(math.sin(angle) * (radius - 15))
            outer_x = center_x + int(math.cos(angle) * (radius + 8)) * facing
            outer_y = center_y + int(math.sin(angle) * (radius + 8))
            alpha = _NS_sethrakhar._alpha(240 * (1 - t * 0.4))
            # Thick fire arc
            pygame.draw.line(surface,
                             (*_NS_sethrakhar.PALETTE["fury_darkest"], alpha),
                             (inner_x, inner_y), (outer_x, outer_y), 5)
            pygame.draw.line(surface,
                             (*_NS_sethrakhar.PALETTE["fury_dark"], alpha),
                             (inner_x, inner_y), (outer_x, outer_y), 4)
            pygame.draw.line(surface,
                             (*_NS_sethrakhar.PALETTE["fury_mid"], alpha),
                             (inner_x, inner_y), (outer_x, outer_y), 3)
            pygame.draw.line(surface,
                             (*_NS_sethrakhar.PALETTE["fury_light"], alpha),
                             (inner_x, inner_y), (outer_x, outer_y), 2)
            pygame.draw.line(surface,
                             (*_NS_sethrakhar.PALETTE["fury_hot"], alpha),
                             (inner_x, inner_y), (outer_x, outer_y), 1)
            # Tip sparks
            pygame.draw.rect(surface,
                             (*_NS_sethrakhar.PALETTE["fury_hot"], alpha),
                             (outer_x, outer_y, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_sethrakhar.PALETTE["fury_shine"], alpha),
                             (outer_x, outer_y, 1, 1))
        # Fire embers flying out
        for i in range(12):
            drop_angle = start_angle + (end_angle - start_angle) * (i / 11)
            drop_dist = radius + 8 + int(t * 16)
            drop_x = center_x + int(math.cos(drop_angle) * drop_dist) * facing
            drop_y = center_y + int(math.sin(drop_angle) * drop_dist)
            alpha = _NS_sethrakhar._alpha(220 * (1 - t))
            pygame.draw.rect(surface,
                             (*_NS_sethrakhar.PALETTE["fury_mid"], alpha),
                             (drop_x, drop_y, 3, 3))
            pygame.draw.rect(surface,
                             (*_NS_sethrakhar.PALETTE["fury_hot"], alpha),
                             (drop_x, drop_y, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_sethrakhar.PALETTE["fury_shine"], alpha),
                             (drop_x, drop_y, 1, 1))
    # ============================================================
    # FURY FLAMES (ambient)
    # ============================================================
    def _draw_fury_flames(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        """Orange fury flames below floating boss."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((160, 55), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(38, 3, -3):
            alpha = _NS_sethrakhar._alpha((38 - radius) * 2.2 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_sethrakhar.PALETTE["fury_darkest"], alpha),
                    (80 - radius * 2, 27 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(24, 3, -2):
            alpha = _NS_sethrakhar._alpha((24 - radius) * 3.4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_sethrakhar.PALETTE["fury_dark"], alpha),
                    (80 - radius, 27 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 80, cy - 12))
        # Rising fire particles (flames licking up)
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.5 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase * 2 + i) * 3)
            sy = cy + 6 - int(t * 32)
            alpha = _NS_sethrakhar._alpha(230 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_sethrakhar._aacircle(surface,
                                     (*_NS_sethrakhar.PALETTE["fury_dark"], alpha),
                                     (sx, sy), 3)
            _NS_sethrakhar._aacircle(surface,
                                     (*_NS_sethrakhar.PALETTE["fury_mid"], alpha),
                                     (sx, sy - 1), 2)
            pygame.draw.rect(surface,
                             (*_NS_sethrakhar.PALETTE["fury_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_sethrakhar.PALETTE["fury_hot"], alpha),
                             (sx, sy - 2, 1, 1))
        # Bright sparkles
        for i in range(10):
            ember_t = (phase * 0.7 + i * 0.15) % 1.0
            ex = cx - 28 + i * 6 + int(math.sin(phase + i) * 4)
            ey = cy + 4 - int(ember_t * 26)
            alpha = _NS_sethrakhar._alpha(230 * (1 - ember_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface,
                                 (*_NS_sethrakhar.PALETTE["fury_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_sethrakhar.PALETTE["fury_shine"], alpha),
                                 (ex, ey, 1, 1))
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_sethrakhar._alpha(160 - i * 22)
                if alpha <= 0:
                    continue
                _NS_sethrakhar._aacircle(surface,
                                         (*_NS_sethrakhar.PALETTE["fury_dark"], alpha),
                                         (sx, sy), max(2, 6 - i))
                _NS_sethrakhar._aacircle(surface,
                                         (*_NS_sethrakhar.PALETTE["fury_mid"], alpha),
                                         (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface,
                                 (*_NS_sethrakhar.PALETTE["fury_hot"], alpha),
                                 (sx, sy - 1, 2, 2))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        hover_offset = int(math.sin(phase * 0.8) * 1)
        shadow = pygame.Surface((140, 28), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 14 - radius, 120 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (12, 6, 3, 170), (10, 8, 120, 12))
        pygame.draw.ellipse(shadow, (55, 25, 10, 110), (18, 10, 104, 8))
        surface.blit(shadow, (x - 70, y - 14 + hover_offset))
    def _draw_fury_aura(surface, x, y, phase):
        """Orange fire aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((230, 195), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_sethrakhar._alpha((100 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_sethrakhar._aacircle(aura,
                                         (*_NS_sethrakhar.PALETTE["fury_darkest"], alpha),
                                         (115, 97), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_sethrakhar._alpha((65 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_sethrakhar._aacircle(aura,
                                         (*_NS_sethrakhar.PALETTE["fury_dark"], alpha),
                                         (115, 97), radius)
        for radius in range(38, 5, -3):
            alpha = _NS_sethrakhar._alpha((38 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_sethrakhar._aacircle(aura,
                                         (*_NS_sethrakhar.PALETTE["fury_mid"], alpha),
                                         (115, 97), radius)
        surface.blit(aura, (x - 115, y - 97))
        # Rising ember particles
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 42 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fury_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fury_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Fiery rune ring on ground."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_sethrakhar.PALETTE["fury_darkest"], 210),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_sethrakhar.PALETTE["fury_dark"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_sethrakhar.PALETTE["fury_mid"], 200),
                            (25, 22, 120, 18), 1)
        # Fire runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_sethrakhar.PALETTE["fury_hot"], 230),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_sethrakhar.PALETTE["fury_shine"],
                                 _NS_sethrakhar._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))
    # ============================================================
    # SKILL Q: RUTHLESS PREDATOR (empowered slash)
    # ============================================================
    def _draw_ruthlesspredator_foreground(surface, boss, x, y, timer, phase):
        """Empowered fire slash - bigger arc + crit spark at target."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_sethrakhar._target_position(boss, x, y)
        if progress < 0.35:
            # Wind-up: charge fire in blade
            t = progress / 0.35
            blade_pos_x = x + facing * 20
            blade_pos_y = y - 20
            for r in range(int(12 * t), 0, -1):
                alpha = _NS_sethrakhar._alpha(200 * (12 * t - r) / max(1, 12 * t))
                _NS_sethrakhar._aacircle(surface,
                                         (*_NS_sethrakhar.PALETTE["fury_dark"], alpha),
                                         (blade_pos_x, blade_pos_y), r)
            _NS_sethrakhar._aacircle(surface, _NS_sethrakhar.PALETTE["fury_mid"],
                                     (blade_pos_x, blade_pos_y), max(1, int(6 * t)))
            _NS_sethrakhar._aacircle(surface, _NS_sethrakhar.PALETTE["fury_hot"],
                                     (blade_pos_x, blade_pos_y), max(1, int(3 * t)))
            pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fury_shine"],
                             (blade_pos_x, blade_pos_y, 1, 1))
        else:
            # SLASH ARC (huge crescent of fire)
            t = (progress - 0.35) / 0.65
            center_x = x + facing * 12
            center_y = y - 4
            radius = 45 + int(t * 15)
            start_angle = -math.pi * 0.75 + t * 0.3
            end_angle = math.pi * 0.55 - (1 - t) * 0.3
            # Draw thick fire crescent (like reference image)
            num_slashes = 10
            for i in range(num_slashes):
                slash_t = i / (num_slashes - 1)
                angle = start_angle + (end_angle - start_angle) * slash_t
                inner_x = center_x + int(math.cos(angle) * (radius - 18)) * facing
                inner_y = center_y + int(math.sin(angle) * (radius - 18))
                outer_x = center_x + int(math.cos(angle) * (radius + 10)) * facing
                outer_y = center_y + int(math.sin(angle) * (radius + 10))
                alpha = _NS_sethrakhar._alpha(250 * (1 - t * 0.4))
                pygame.draw.line(surface,
                                 (*_NS_sethrakhar.PALETTE["fury_darkest"], alpha),
                                 (inner_x, inner_y), (outer_x, outer_y), 6)
                pygame.draw.line(surface,
                                 (*_NS_sethrakhar.PALETTE["fury_dark"], alpha),
                                 (inner_x, inner_y), (outer_x, outer_y), 5)
                pygame.draw.line(surface,
                                 (*_NS_sethrakhar.PALETTE["fury_mid"], alpha),
                                 (inner_x, inner_y), (outer_x, outer_y), 3)
                pygame.draw.line(surface,
                                 (*_NS_sethrakhar.PALETTE["fury_light"], alpha),
                                 (inner_x, inner_y), (outer_x, outer_y), 2)
                pygame.draw.line(surface,
                                 (*_NS_sethrakhar.PALETTE["fury_hot"], alpha),
                                 (inner_x, inner_y), (outer_x, outer_y), 1)
                # Bright edge sparks
                pygame.draw.rect(surface,
                                 (*_NS_sethrakhar.PALETTE["fury_shine"], alpha),
                                 (outer_x, outer_y, 2, 2))
            # CRIT SPARK burst at target
            if t > 0.5:
                st = (t - 0.5) / 0.5
                sparkle_r = int(15 + st * 15)
                alpha = _NS_sethrakhar._alpha(255 * (1 - st))
                # Star burst
                for i in range(8):
                    a = i * math.pi / 4
                    lx = tx + int(math.cos(a) * sparkle_r)
                    ly = ty + int(math.sin(a) * sparkle_r)
                    pygame.draw.line(surface,
                                     (*_NS_sethrakhar.PALETTE["fury_mid"], alpha),
                                     (tx, ty), (lx, ly), 3)
                    pygame.draw.line(surface,
                                     (*_NS_sethrakhar.PALETTE["fury_light"], alpha),
                                     (tx, ty), (lx, ly), 2)
                    pygame.draw.line(surface,
                                     (*_NS_sethrakhar.PALETTE["fury_shine"], alpha),
                                     (tx, ty), (lx, ly), 1)
                    pygame.draw.rect(surface,
                                     (*_NS_sethrakhar.PALETTE["white"], alpha),
                                     (lx, ly, 1, 1))
                # Center bright flash
                _NS_sethrakhar._aacircle(surface, _NS_sethrakhar.PALETTE["fury_hot"],
                                         (tx, ty), 5)
                _NS_sethrakhar._aacircle(surface, _NS_sethrakhar.PALETTE["fury_shine"],
                                         (tx, ty), 3)
                _NS_sethrakhar._aacircle(surface, _NS_sethrakhar.PALETTE["white"],
                                         (tx, ty), 1)
    # ============================================================
    # SKILL W: EMPOWERED STUN (parry then slam)
    # ============================================================
    def _draw_empoweredstun_ground(surface, boss, x, y, timer, phase):
        """Ground streak for stun charge."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if 0.3 < progress < 0.7:
            for i in range(6):
                line_t = (phase * 2 + i * 0.2) % 1.0
                lx_start = x - facing * (10 + i * 8)
                lx_end = lx_start - facing * 16
                ly = y + 40 + int(math.sin(i) * 3)
                alpha = _NS_sethrakhar._alpha(180 * (1 - line_t) * (1 - progress * 0.3))
                pygame.draw.line(surface,
                                 (*_NS_sethrakhar.PALETTE["fury_dark"], alpha),
                                 (lx_start, ly), (lx_end, ly), 2)
                pygame.draw.line(surface,
                                 (*_NS_sethrakhar.PALETTE["fury_light"], alpha),
                                 (lx_start, ly), (lx_end, ly), 1)
    def _draw_empoweredstun_foreground(surface, boss, x, y, timer, phase):
        """Parry shield + forward slash + stun stars."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_sethrakhar._target_position(boss, x, y)
        if progress < 0.3:
            # PARRY - shield in front of body
            t = progress / 0.3
            shield_x = x + facing * 18
            shield_y = y - 8
            for r in range(int(14 * t), 0, -1):
                alpha = _NS_sethrakhar._alpha(180 * (14 * t - r) / max(1, 14 * t))
                _NS_sethrakhar._aacircle(surface,
                                         (*_NS_sethrakhar.PALETTE["fury_dark"], alpha),
                                         (shield_x, shield_y), r)
            # Shield ring
            _NS_sethrakhar._aacircle(surface, _NS_sethrakhar.PALETTE["fury_mid"],
                                     (shield_x, shield_y), int(12 * t), 2)
            _NS_sethrakhar._aacircle(surface, _NS_sethrakhar.PALETTE["fury_light"],
                                     (shield_x, shield_y), int(10 * t), 1)
            # Deflection sparks
            for i in range(4):
                sa = phase * 4 + i * math.pi / 2
                sx = shield_x + int(math.cos(sa) * 10)
                sy = shield_y + int(math.sin(sa) * 10)
                pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["fury_shine"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["white"], (sx, sy, 1, 1))
        elif progress < 0.7:
            # DASH SLASH forward
            t = (progress - 0.3) / 0.4
            # Speed lines
            for i in range(8):
                line_t = (phase * 5 + i * 0.12) % 1.0
                sy = y - 10 + int(math.sin(i * 0.7) * 8)
                sx_start = x + facing * int(i * 8)
                sx_end = sx_start - facing * 20
                alpha = _NS_sethrakhar._alpha(220 * (1 - line_t) * (1 - t * 0.5))
                pygame.draw.line(surface,
                                 (*_NS_sethrakhar.PALETTE["fury_dark"], alpha),
                                 (sx_start, sy), (sx_end, sy), 2)
                pygame.draw.line(surface,
                                 (*_NS_sethrakhar.PALETTE["fury_hot"], alpha),
                                 (sx_start, sy), (sx_end, sy - 1), 1)
            # Impact at target
            if t > 0.4:
                impact_t = (t - 0.4) / 0.6
                impact_r = int(10 + impact_t * 22)
                alpha = _NS_sethrakhar._alpha(240 * (1 - impact_t))
                _NS_sethrakhar._aacircle(surface,
                                         (*_NS_sethrakhar.PALETTE["fury_darkest"], alpha),
                                         (tx, ty), impact_r + 2, 3)
                _NS_sethrakhar._aacircle(surface,
                                         (*_NS_sethrakhar.PALETTE["fury_dark"], alpha),
                                         (tx, ty), impact_r, 2)
                _NS_sethrakhar._aacircle(surface,
                                         (*_NS_sethrakhar.PALETTE["fury_mid"], alpha),
                                         (tx, ty), max(1, impact_r - 5), 2)
                _NS_sethrakhar._aacircle(surface,
                                         (*_NS_sethrakhar.PALETTE["fury_light"], alpha),
                                         (tx, ty), max(1, impact_r - 10), 1)
        else:
            # STUN STARS above target
            t = (progress - 0.7) / 0.3
            for i in range(4):
                star_angle = phase * 2 + i * math.pi * 2 / 4
                sx = tx + int(math.cos(star_angle) * 12)
                sy = ty - 15 + int(math.sin(star_angle) * 4)
                alpha = _NS_sethrakhar._alpha(240 * (1 - t))
                # Star (5-point)
                for pt_i in range(5):
                    pt_a = -math.pi / 2 + pt_i * math.pi * 2 / 5
                    px = sx + int(math.cos(pt_a) * 4)
                    py = sy + int(math.sin(pt_a) * 4)
                    pygame.draw.line(surface,
                                     (*_NS_sethrakhar.PALETTE["fury_hot"], alpha),
                                     (sx, sy), (px, py), 2)
                    pygame.draw.line(surface,
                                     (*_NS_sethrakhar.PALETTE["fury_shine"], alpha),
                                     (sx, sy), (px, py), 1)
                pygame.draw.rect(surface, _NS_sethrakhar.PALETTE["white"],
                                 (sx, sy, 1, 1))
    # ============================================================
    # SKILL E: SLICE AND DICE (double slash)
    # ============================================================
    def _draw_sliceanddice_foreground(surface, boss, x, y, timer, phase):
        """Two consecutive slashes with fire crescents."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_sethrakhar._target_position(boss, x, y)
        # Two slashes in sequence
        # First slash: 0 - 0.5
        # Second slash: 0.5 - 1.0 (larger)
        for slash_num in (1, 2):
            slash_start = 0.0 if slash_num == 1 else 0.5
            slash_end = 0.5 if slash_num == 1 else 1.0
            if slash_start <= progress <= slash_end:
                local_t = (progress - slash_start) / (slash_end - slash_start)
                center_x = x + facing * 10
                center_y = y - 4
                # Second slash is bigger
                base_radius = 32 if slash_num == 1 else 44
                radius = base_radius + int(local_t * 10)
                # Alternate directions
                if slash_num == 1:
                    start_angle = -math.pi * 0.6 + local_t * 0.3
                    end_angle = math.pi * 0.4 - (1 - local_t) * 0.3
                else:
                    start_angle = math.pi * 0.5 - local_t * 0.3
                    end_angle = -math.pi * 0.5 + (1 - local_t) * 0.3
                num_slashes = 8
                for i in range(num_slashes):
                    slash_t = i / (num_slashes - 1)
                    angle = start_angle + (end_angle - start_angle) * slash_t
                    inner_x = center_x + int(math.cos(angle) * (radius - 12)) * facing
                    inner_y = center_y + int(math.sin(angle) * (radius - 12))
                    outer_x = center_x + int(math.cos(angle) * (radius + 6)) * facing
                    outer_y = center_y + int(math.sin(angle) * (radius + 6))
                    alpha = _NS_sethrakhar._alpha(240 * (1 - local_t * 0.4))
                    pygame.draw.line(surface,
                                     (*_NS_sethrakhar.PALETTE["fury_darkest"], alpha),
                                     (inner_x, inner_y), (outer_x, outer_y), 5)
                    pygame.draw.line(surface,
                                     (*_NS_sethrakhar.PALETTE["fury_dark"], alpha),
                                     (inner_x, inner_y), (outer_x, outer_y), 4)
                    pygame.draw.line(surface,
                                     (*_NS_sethrakhar.PALETTE["fury_mid"], alpha),
                                     (inner_x, inner_y), (outer_x, outer_y), 3)
                    pygame.draw.line(surface,
                                     (*_NS_sethrakhar.PALETTE["fury_light"], alpha),
                                     (inner_x, inner_y), (outer_x, outer_y), 2)
                    pygame.draw.line(surface,
                                     (*_NS_sethrakhar.PALETTE["fury_hot"], alpha),
                                     (inner_x, inner_y), (outer_x, outer_y), 1)
                    pygame.draw.rect(surface,
                                     (*_NS_sethrakhar.PALETTE["fury_shine"], alpha),
                                     (outer_x, outer_y, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_sethrakhar.PALETTE["white"], alpha),
                                     (outer_x, outer_y, 1, 1))
    # ============================================================
    # SKILL R: DOMINUS (transform - massive fury mode)
    # ============================================================
    def _draw_dominus_ground(surface, boss, x, y, timer, phase):
        """Massive fire ring on ground during transformation."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(70 * min(1.0, progress * 2))
        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_sethrakhar.PALETTE["fury_darkest"], 230),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 4)
            pygame.draw.ellipse(surface,
                                (*_NS_sethrakhar.PALETTE["fury_dark"], 210),
                                (x - r + 4, y + 40 - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_sethrakhar.PALETTE["fury_mid"], 220),
                                (x - r + 8, y + 40 - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8), 2)
            pygame.draw.ellipse(surface,
                                (*_NS_sethrakhar.PALETTE["fury_hot"], 180),
                                (x - r + 14, y + 40 - r // 3 + 7,
                                 r * 2 - 28, r * 2 // 3 - 14), 1)
            # Runes
            for i in range(14):
                angle = phase * 0.4 + i * math.pi / 7
                x1 = x + int(math.cos(angle) * r)
                y1 = y + 40 + int(math.sin(angle) * r * 0.4)
                x2 = x + int(math.cos(angle) * (r - 10))
                y2 = y + 40 + int(math.sin(angle) * (r - 10) * 0.4)
                pygame.draw.line(surface, _NS_sethrakhar.PALETTE["fury_shine"],
                                 (x1, y1), (x2, y2), 2)
    def _draw_dominus_foreground(surface, boss, x, y, timer, phase):
        """Massive fire aura + rising fire pillars around boss during Dominus."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Body aura (bigger fire around boss)
        aura_r = 50 + int(math.sin(phase * 3) * 6)
        for r in range(aura_r, 3, -3):
            alpha = _NS_sethrakhar._alpha(120 * (aura_r - r) / aura_r)
            _NS_sethrakhar._aacircle(surface,
                                     (*_NS_sethrakhar.PALETTE["fury_dark"], alpha),
                                     (x, y - 8), r)
        # Rising fire pillars around boss (like Ignite AoE)
        num_pillars = 8
        pillar_radius = 60
        for i in range(num_pillars):
            angle = i * math.pi * 2 / num_pillars + phase * 0.5
            px = x + int(math.cos(angle) * pillar_radius)
            py = y + 20 + int(math.sin(angle) * pillar_radius * 0.4)
            # Pillar (rising fire column)
            for layer in range(8):
                layer_t = (phase * 1.5 + i * 0.12 + layer * 0.15) % 1.0
                layer_y = py - int(layer_t * 30)
                layer_alpha = _NS_sethrakhar._alpha(220 * (1 - layer_t))
                layer_w = int(5 + layer_t * 3)
                layer_h = int(3 + layer_t * 2)
                pygame.draw.ellipse(surface,
                                    (*_NS_sethrakhar.PALETTE["fury_dark"], layer_alpha),
                                    (px - layer_w, layer_y - layer_h,
                                     layer_w * 2, layer_h * 2))
                pygame.draw.ellipse(surface,
                                    (*_NS_sethrakhar.PALETTE["fury_mid"], layer_alpha),
                                    (px - layer_w + 1, layer_y - layer_h + 1,
                                     layer_w * 2 - 2, layer_h * 2 - 2))
                pygame.draw.rect(surface,
                                 (*_NS_sethrakhar.PALETTE["fury_hot"], layer_alpha),
                                 (px, layer_y, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_sethrakhar.PALETTE["fury_shine"], layer_alpha),
                                 (px, layer_y - 1, 1, 1))
        # Rising fire particles/embers all around
        for i in range(24):
            spark_t = (phase * 0.8 + i * 0.05) % 1.0
            spark_angle = i * math.pi * 2 / 24
            sr = 30 + int(spark_t * 40)
            sx = x + int(math.cos(spark_angle) * sr)
            sy = y - 5 + int(math.sin(spark_angle) * sr * 0.5) - int(spark_t * 25)
            alpha = _NS_sethrakhar._alpha(230 * (1 - spark_t))
            if alpha > 0:
                pygame.draw.rect(surface,
                                 (*_NS_sethrakhar.PALETTE["fury_hot"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_sethrakhar.PALETTE["fury_shine"], alpha),
                                 (sx, sy, 1, 1))
        # Screen shake indication (flash white briefly at start)
        if progress < 0.1:
            t = progress / 0.1
            flash_alpha = _NS_sethrakhar._alpha(180 * (1 - t))
            flash_surf = pygame.Surface((250, 250), pygame.SRCALPHA)
            for r in range(120, 0, -8):
                a = _NS_sethrakhar._alpha(flash_alpha * (120 - r) / 120)
                _NS_sethrakhar._aacircle(flash_surf,
                                         (*_NS_sethrakhar.PALETTE["fury_hot"], a),
                                         (125, 125), r)
            surface.blit(flash_surf, (x - 125, y - 125))


# ====================================================================
# NYRELLIETH (FROST-VEILED HUNTRESS) - TRUE BOSS
# ====================================================================

class _NS_nyrellieth:
    """Namespace nyrellieth - dark elf ice ranger TRUE BOSS."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Dark navy blue cape/robe (main garb)
        "cape_darkest": (5, 8, 20),
        "cape_dark": (15, 22, 45),
        "cape_mid": (35, 45, 80),
        "cape_light": (65, 80, 120),
        "cape_edge": (110, 125, 165),
        # Ice cyan/blue (main magic theme)
        "ice_darkest": (5, 25, 45),
        "ice_dark": (20, 70, 110),
        "ice_mid": (60, 160, 220),
        "ice_light": (140, 220, 255),
        "ice_hot": (200, 245, 255),
        "ice_shine": (240, 255, 255),
        # Pale purple/blue skin (dark elf)
        "skin_darkest": (65, 55, 85),
        "skin_dark": (110, 100, 135),
        "skin_mid": (160, 150, 180),
        "skin_light": (200, 195, 215),
        "skin_shine": (230, 225, 235),
        # Silver white hair
        "hair_darkest": (75, 75, 95),
        "hair_dark": (135, 135, 155),
        "hair_mid": (195, 195, 215),
        "hair_light": (235, 235, 245),
        "hair_shine": (255, 255, 255),
        # Dark leather armor (chest, bracers, boots)
        "leather_darkest": (8, 5, 12),
        "leather_dark": (25, 18, 30),
        "leather_mid": (55, 45, 60),
        "leather_light": (95, 80, 105),
        "leather_edge": (135, 115, 145),
        # Gold accents (bow decoration, jewelry)
        "gold_dark": (75, 55, 15),
        "gold_mid": (155, 120, 40),
        "gold_light": (220, 185, 90),
        "gold_shine": (255, 235, 160),
        # Bow (dark wood/ice)
        "bow_darkest": (5, 15, 30),
        "bow_dark": (15, 35, 60),
        "bow_mid": (35, 75, 115),
        "bow_light": (75, 130, 175),
        # Glowing white/blue eyes
        "eye_socket": (5, 3, 8),
        "eye_dark": (35, 55, 90),
        "eye_mid": (140, 190, 235),
        "eye_light": (220, 245, 255),
        "eye_glow": (245, 255, 255),
        # Frost mist
        "mist_dark": (25, 45, 80),
        "mist_mid": (75, 130, 180),
        "mist_light": (170, 220, 245),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_nyrellieth._clamp(color)
        if _NS_nyrellieth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_nyrellieth._clamp(color)
        if _NS_nyrellieth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_nyrellieth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 260 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_nyrellieth(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_nyrellieth._detect_moving(boss)
        _NS_nyrellieth._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_nyr_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient (TRUE BOSS = bigger)
        _NS_nyrellieth._draw_frost_aura(surface, x, y, pulse)
        _NS_nyrellieth._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "r":
            _NS_nyrellieth._draw_marksmanship_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (always floating)
        if attacking:
            _NS_nyrellieth._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_nyrellieth._draw_float_move(surface, boss, x, y)
        else:
            _NS_nyrellieth._draw_float_idle(surface, boss, x, y)
        # Marksmanship aura around body (R)
        if active_skill == "r":
            _NS_nyrellieth._draw_marksmanship_aura(surface, boss, x, y, skill_timer, pulse)
        # Foreground FX
        if active_skill == "q":
            _NS_nyrellieth._draw_frostarrow_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_nyrellieth._draw_multishot_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_nyrellieth._draw_silence_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_nyr_previous_timer", 0))
        active = bool(getattr(boss, "_nyr_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._nyr_attack_active = True
            boss._nyr_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._nyr_attack_frame = int(getattr(boss, "_nyr_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._nyr_attack_active = False
            boss._nyr_attack_frame = 0
            active = False
        boss._nyr_previous_timer = timer
        boss._nyr_attack_progress = (
            min(1.0, getattr(boss, "_nyr_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_nyr_last_x"):
            boss._nyr_last_x = boss.x
            boss._nyr_last_y = boss.y
            return False
        dx = abs(boss.x - boss._nyr_last_x)
        dy = abs(boss.y - boss._nyr_last_y)
        boss._nyr_last_x = boss.x
        boss._nyr_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS (Floating)
    # ============================================================
    def _draw_float_idle(surface, boss, x, y):
        hover = int(math.sin(boss.pulse * 0.7) * 5) - 10
        sway = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_nyrellieth._draw_float_shadow(surface, x + sway, y + 52, boss.pulse)
        _NS_nyrellieth._draw_frost_mist(surface, x + sway, y + 42, boss.pulse)
        _NS_nyrellieth._draw_body(surface, x + sway, y + hover,
                                  boss.direction, boss.pulse, "idle")
    def _draw_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.5
        hover = int(math.sin(phase * 0.9) * 6) - 11
        sway = int(math.sin(phase * 0.7) * 3)
        _NS_nyrellieth._draw_float_shadow(surface, x + sway, y + 52, phase)
        _NS_nyrellieth._draw_frost_mist(surface, x + sway, y + 42, phase,
                                        trail=True, facing=boss.direction)
        _NS_nyrellieth._draw_body(surface, x + sway, y + hover,
                                  boss.direction, phase, "float")
    def _draw_attack(surface, boss, x, y):
        """Ranged: draw bow, aim, release ice arrow."""
        progress = getattr(boss, "_nyr_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Draw back → release → recovery
        if progress < 0.4:
            t = progress / 0.4
            lean = -int(t * 3) * boss.direction
            lift = int(t * 2)
        elif progress < 0.6:
            t = (progress - 0.4) / 0.2
            lean = int((-3 + t * 6)) * boss.direction
            lift = int(2 - t * 4)
        else:
            t = (progress - 0.6) / 0.4
            lean = int(3 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        hover = int(math.sin(boss.pulse * 0.7) * 3) - 8
        _NS_nyrellieth._draw_float_shadow(surface, x + lean, y + 52, boss.pulse)
        _NS_nyrellieth._draw_frost_mist(surface, x + lean, y + 42,
                                        boss.pulse, intense=True)
        _NS_nyrellieth._draw_body(surface, x + lean, y + hover - lift,
                                  boss.direction, boss.pulse,
                                  "attack", progress)
        _NS_nyrellieth._draw_ice_arrow_projectile(surface, boss, x + lean,
                                                  y + hover - lift, progress)
    # ============================================================
    # BODY - Dark elf ranger
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        # Cape/hood BEHIND body
        _NS_nyrellieth._draw_hooded_cape(surface, cx, cy, facing, phase, action)
        # Torso (dark leather)
        _NS_nyrellieth._draw_ranger_torso(surface, cx, cy, facing, phase)
        # Long skirt/robe (dangling because floating)
        _NS_nyrellieth._draw_flowing_robe(surface, cx, cy + 8, facing, phase, action)
        # Back arm (holding arrow at quiver)
        _NS_nyrellieth._draw_arrow_arm(surface, cx, cy - 2, facing, phase, action,
                                       attack_progress)
        # Head with hood + silver hair
        _NS_nyrellieth._draw_dark_elf_head(surface, cx, cy - 20, facing, phase,
                                           action, attack_progress)
        # FRONT arm holding bow (LAST for priority)
        _NS_nyrellieth._draw_bow_arm(surface, cx, cy - 2, facing, phase, action,
                                     attack_progress)
    def _draw_hooded_cape(surface, cx, cy, facing, phase, action):
        """Long dark cape flowing behind."""
        wind = math.sin(phase * 0.6) * 3
        sway = math.sin(phase * 0.4) * 2
        back = -facing
        cape_pts = [
            (cx - facing * 3, cy - 6),
            (cx + back * 5, cy - 4),
            (cx + back * 10, cy + 3 + int(wind)),
            (cx + back * 13, cy + 12 + int(sway)),
            (cx + back * 15, cy + 22 + int(sway * 1.2)),
            (cx + back * 13, cy + 30 + int(sway * 0.9)),
            # Torn/pointed edges
            (cx + back * 9, cy + 32 + int(sway * 0.7)),
            (cx + back * 6, cy + 28),
            (cx + back * 2, cy + 32 + int(sway * 0.6)),
            (cx - facing * 2, cy + 22),
            (cx + facing * 3, cy + 6),
        ]
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["shadow_deep"],
                             [(px + 2, py + 3) for px, py in cape_pts])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["cape_darkest"], cape_pts)
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["cape_dark"], [
            (cx - facing * 2, cy - 5),
            (cx + back * 4, cy - 3),
            (cx + back * 9, cy + 3 + int(wind)),
            (cx + back * 11, cy + 12 + int(sway * 0.9)),
            (cx + back * 12, cy + 22 + int(sway * 1.0)),
            (cx + back * 10, cy + 28 + int(sway * 0.8)),
            (cx + back * 5, cy + 26),
            (cx + back * 1, cy + 22),
            (cx + facing * 2, cy + 6),
        ])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["cape_mid"], [
            (cx + back * 3, cy - 1),
            (cx + back * 7, cy + 4 + int(wind * 0.8)),
            (cx + back * 9, cy + 14 + int(sway * 0.8)),
            (cx + back * 8, cy + 22 + int(sway * 0.6)),
            (cx + back * 4, cy + 20),
            (cx + back * 1, cy + 12),
        ])
        # Highlight fold
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["cape_light"],
                         (cx + back * 4, cy),
                         (cx + back * 8, cy + 18 + int(sway * 0.6)), 1)
        # Ice edge glow (subtle magic)
        for edge_x_off, edge_y_off in [
            (back * 10, 30 + int(sway * 0.7)),
            (back * 6, 32),
            (back * 2, 30 + int(sway * 0.5)),
        ]:
            edge_x = cx + edge_x_off
            edge_y = cy + edge_y_off
            glow_alpha = _NS_nyrellieth._alpha(100 + math.sin(phase * 2 + edge_x_off) * 40)
            pygame.draw.rect(surface,
                             (*_NS_nyrellieth.PALETTE["ice_dark"], glow_alpha),
                             (edge_x, edge_y, 1, 2))
            pygame.draw.rect(surface,
                             (*_NS_nyrellieth.PALETTE["ice_light"], glow_alpha),
                             (edge_x, edge_y + 1, 1, 1))
    def _draw_ranger_torso(surface, cx, cy, facing, phase):
        """Dark leather ranger corset."""
        breath = math.sin(phase * 0.7) * 1
        torso_pts = [
            (cx - 8, cy - 5),
            (cx - 9, cy),
            (cx - 8, cy + 6),
            (cx - 6, cy + 10),
            (cx + 6, cy + 10),
            (cx + 8, cy + 6),
            (cx + 9, cy),
            (cx + 8, cy - 5),
        ]
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in torso_pts])
        # Base skin
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["skin_dark"], torso_pts)
        # Dark leather corset
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["leather_darkest"], [
            (cx - 8, cy - 3),
            (cx - 9, cy + 1),
            (cx - 8, cy + 6),
            (cx - 5, cy + 9),
            (cx + 5, cy + 9),
            (cx + 8, cy + 6),
            (cx + 9, cy + 1),
            (cx + 8, cy - 3),
        ])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["leather_dark"], [
            (cx - 7, cy - 2),
            (cx - 8, cy + 1),
            (cx - 7, cy + 5),
            (cx - 4, cy + 8),
            (cx + 4, cy + 8),
            (cx + 7, cy + 5),
            (cx + 8, cy + 1),
            (cx + 7, cy - 2),
        ])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["leather_mid"], [
            (cx - 6, cy - 1),
            (cx - 7, cy + 1),
            (cx - 6, cy + 4),
            (cx - 3, cy + 7),
            (cx + 3, cy + 7),
            (cx + 6, cy + 4),
            (cx + 7, cy + 1),
            (cx + 6, cy - 1),
        ])
        # Highlight on sides
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["leather_light"],
                         (cx - 5, cy), (cx - 5, cy + 6), 1)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["leather_light"],
                         (cx + 5, cy), (cx + 5, cy + 6), 1)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["leather_edge"],
                         (cx - 5, cy), (cx - 5, cy + 3), 1)
        # Pale skin at collar (V-neck)
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["skin_mid"], [
            (cx - 3, cy - 4),
            (cx + 3, cy - 4),
            (cx + 2, cy - 2),
            (cx - 2, cy - 2),
        ])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["skin_light"], [
            (cx - 2, cy - 4),
            (cx + 2, cy - 4),
            (cx + 1, cy - 3),
            (cx - 1, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["skin_shine"],
                         (cx, cy - 4, 1, 1))
        # Gold trim V-collar
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["gold_dark"],
                         (cx - 4, cy - 3), (cx, cy - 1), 1)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["gold_dark"],
                         (cx, cy - 1), (cx + 4, cy - 3), 1)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["gold_mid"],
                         (cx - 3, cy - 3), (cx, cy - 2), 1)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["gold_light"],
                         (cx - 3, cy - 3), (cx, cy - 2), 1)
        # ICE GEM central chest
        gem_cx = cx
        gem_cy = cy + 2
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["shadow_deep"],
                         (gem_cx - 2, gem_cy - 2, 4, 4))
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["ice_darkest"], [
            (gem_cx, gem_cy - 2),
            (gem_cx + 2, gem_cy),
            (gem_cx, gem_cy + 2),
            (gem_cx - 2, gem_cy),
        ])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["ice_dark"], [
            (gem_cx, gem_cy - 1),
            (gem_cx + 1, gem_cy),
            (gem_cx, gem_cy + 1),
            (gem_cx - 1, gem_cy),
        ])
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_light"],
                         (gem_cx, gem_cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_shine"],
                         (gem_cx, gem_cy - 1, 1, 1))
        # Corset straps (crossing X pattern)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["leather_edge"],
                         (cx - 3, cy + 4), (cx + 3, cy + 7), 1)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["leather_edge"],
                         (cx + 3, cy + 4), (cx - 3, cy + 7), 1)
        # SHOULDER GUARDS (dark leather with ice-tipped spikes)
        for side in (-1, 1):
            paul_x = cx + side * 9
            paul_y = cy - 5
            _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["shadow_deep"], [
                (paul_x - 3, paul_y),
                (paul_x + 3, paul_y),
                (paul_x + 3, paul_y + 5),
                (paul_x - 3, paul_y + 5),
            ])
            _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["leather_darkest"], [
                (paul_x - 3, paul_y - 1),
                (paul_x + 3, paul_y - 1),
                (paul_x + 3, paul_y + 4),
                (paul_x - 3, paul_y + 4),
            ])
            _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["leather_dark"], [
                (paul_x - 2, paul_y - 1),
                (paul_x + 2, paul_y - 1),
                (paul_x + 2, paul_y + 3),
                (paul_x - 2, paul_y + 3),
            ])
            # Gold trim
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["gold_mid"],
                             (paul_x - 3, paul_y - 1),
                             (paul_x + 3, paul_y - 1), 1)
            # ICE SPIKE upward
            _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["shadow_deep"], [
                (paul_x, paul_y - 5),
                (paul_x - 2, paul_y),
                (paul_x + 2, paul_y),
            ])
            _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["ice_dark"], [
                (paul_x, paul_y - 4),
                (paul_x - 1, paul_y),
                (paul_x + 1, paul_y),
            ])
            _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["ice_mid"], [
                (paul_x, paul_y - 3),
                (paul_x, paul_y),
                (paul_x + 1, paul_y),
            ])
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_light"],
                             (paul_x, paul_y - 3, 1, 1))
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_shine"],
                             (paul_x, paul_y - 3, 1, 1))
        # Belt
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["leather_darkest"],
                         (cx - 7, cy + 8, 14, 2))
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["leather_dark"],
                         (cx - 7, cy + 8, 14, 1))
        # Gold buckle
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["gold_dark"],
                         (cx - 2, cy + 8, 5, 2))
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["gold_mid"],
                         (cx - 1, cy + 8, 3, 1))
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["gold_light"],
                         (cx, cy + 8, 1, 1))
    def _draw_flowing_robe(surface, cx, cy, facing, phase, action):
        """Long dark robe/skirt dangling."""
        sway1 = math.sin(phase * 0.5) * 3
        sway2 = math.sin(phase * 0.7) * 2
        # Skirt outline
        skirt_pts = [
            (cx - 7, cy),
            (cx - 9 + int(sway1 * 0.3), cy + 7),
            (cx - 11 + int(sway1 * 0.6), cy + 15),
            (cx - 12 + int(sway1), cy + 22),
            (cx - 10 + int(sway1 * 0.9), cy + 28),
            (cx - 5 + int(sway2 * 0.5), cy + 32),
            (cx + int(sway2), cy + 34),
            (cx + 5 + int(sway2 * 0.5), cy + 32),
            (cx + 10 + int(sway1 * 0.9), cy + 28),
            (cx + 12 + int(sway1), cy + 22),
            (cx + 11 + int(sway1 * 0.6), cy + 15),
            (cx + 9 + int(sway1 * 0.3), cy + 7),
            (cx + 7, cy),
        ]
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["shadow_deep"],
                             [(px + 2, py + 3) for px, py in skirt_pts])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["cape_darkest"], skirt_pts)
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["cape_dark"], [
            (cx - 6, cy + 1),
            (cx - 8 + int(sway1 * 0.3), cy + 7),
            (cx - 10 + int(sway1 * 0.6), cy + 15),
            (cx - 10 + int(sway1), cy + 22),
            (cx - 8 + int(sway1 * 0.9), cy + 26),
            (cx - 4 + int(sway2 * 0.5), cy + 30),
            (cx + int(sway2), cy + 31),
            (cx + 4 + int(sway2 * 0.5), cy + 30),
            (cx + 8 + int(sway1 * 0.9), cy + 26),
            (cx + 10 + int(sway1), cy + 22),
            (cx + 10 + int(sway1 * 0.6), cy + 15),
            (cx + 8 + int(sway1 * 0.3), cy + 7),
            (cx + 6, cy + 1),
        ])
        # Vertical fold highlights
        for fold_x_off in (-6, -3, 0, 3, 6):
            fold_x_top = cx + fold_x_off
            fold_x_bot = cx + fold_x_off + int(sway1 * (abs(fold_x_off) / 6))
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["cape_mid"],
                             (fold_x_top, cy + 3), (fold_x_bot, cy + 28), 1)
            if fold_x_off in (-3, 3):
                pygame.draw.line(surface, _NS_nyrellieth.PALETTE["cape_light"],
                                 (fold_x_top, cy + 3),
                                 (fold_x_bot, cy + 24), 1)
        # Gold trim at bottom
        for i, ex in enumerate(range(-10, 12, 4)):
            ex_x = cx + ex + int(sway1 * 0.7)
            ex_y = cy + 30
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["gold_dark"],
                             (ex_x, ex_y, 2, 1))
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["gold_light"],
                             (ex_x, ex_y, 1, 1))
        # Ice sparkles at bottom edges
        for edge_x_off in (-10, -5, 0, 5, 10):
            edge_x = cx + edge_x_off + int(sway1 * 0.7)
            edge_y = cy + 31
            glow_alpha = _NS_nyrellieth._alpha(120 + math.sin(phase * 2 + edge_x_off) * 40)
            pygame.draw.rect(surface,
                             (*_NS_nyrellieth.PALETTE["ice_mid"], glow_alpha),
                             (edge_x, edge_y, 1, 2))
            pygame.draw.rect(surface,
                             (*_NS_nyrellieth.PALETTE["ice_light"], glow_alpha),
                             (edge_x, edge_y + 1, 1, 1))
    def _draw_arrow_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm - holds arrow at quiver, draws when attacking."""
        back_shoulder_x = cx - facing * 5
        back_shoulder_y = cy - 2
        # Attack: draw arrow back
        if action == "attack":
            if attack_progress < 0.4:
                # Draw string back
                t = attack_progress / 0.4
                arm_angle = math.pi * 0.35 - t * math.pi * 0.5
            elif attack_progress < 0.55:
                # Hold drawn
                arm_angle = -math.pi * 0.15
            else:
                # Release forward
                t = (attack_progress - 0.55) / 0.45
                arm_angle = -math.pi * 0.15 + math.pi * 0.5 * t
        else:
            # At quiver
            arm_angle = math.pi * 0.35 + math.sin(phase * 0.5) * 0.05
        arm_length = 11
        back_hand_x = back_shoulder_x + int(math.cos(arm_angle) * arm_length) * facing
        back_hand_y = back_shoulder_y + int(math.sin(arm_angle) * arm_length) + 2
        elbow_x = back_shoulder_x + int(math.cos(arm_angle) * (arm_length * 0.5)) * facing
        elbow_y = back_shoulder_y + int(math.sin(arm_angle) * (arm_length * 0.5))
        # Upper arm (leather sleeve dark)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["shadow_deep"],
                         (back_shoulder_x + 1, back_shoulder_y + 1),
                         (elbow_x + 1, elbow_y + 1), 5)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["leather_darkest"],
                         (back_shoulder_x, back_shoulder_y),
                         (elbow_x, elbow_y), 4)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["leather_dark"],
                         (back_shoulder_x, back_shoulder_y),
                         (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["leather_mid"],
                         (back_shoulder_x - 1, back_shoulder_y),
                         (elbow_x - 1, elbow_y), 2)
        # Forearm (skin - fingerless glove)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["shadow_deep"],
                         (elbow_x + 1, elbow_y + 1),
                         (back_hand_x + 1, back_hand_y + 1), 4)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["skin_darkest"],
                         (elbow_x, elbow_y), (back_hand_x, back_hand_y), 3)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["skin_dark"],
                         (elbow_x, elbow_y), (back_hand_x, back_hand_y), 2)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["skin_mid"],
                         (elbow_x - 1, elbow_y), (back_hand_x - 1, back_hand_y), 1)
        # Bracer at wrist
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["leather_darkest"],
                         (back_hand_x - 2, back_hand_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["leather_dark"],
                         (back_hand_x - 2, back_hand_y - 1, 4, 2))
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["gold_dark"],
                         (back_hand_x - 2, back_hand_y - 1, 4, 1))
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["gold_light"],
                         (back_hand_x - 1, back_hand_y - 1, 2, 1))
        # Hand
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["skin_dark"],
                         (back_hand_x - 1, back_hand_y + 1, 3, 2))
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["skin_mid"],
                         (back_hand_x - 1, back_hand_y + 1, 2, 1))
    def _draw_bow_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding the ice bow - extended forward."""
        shoulder_x = cx + facing * 5
        shoulder_y = cy - 2
        # Arm extended forward holding bow (steady aim)
        if action == "attack":
            if attack_progress < 0.4:
                # Steady aim
                arm_angle = -math.pi * 0.05
            elif attack_progress < 0.6:
                # Release - slight kick
                t = (attack_progress - 0.4) / 0.2
                arm_angle = -math.pi * 0.05 + math.pi * 0.05 * t
            else:
                t = (attack_progress - 0.6) / 0.4
                arm_angle = math.pi * 0.02 * (1 - t)
        else:
            # Bow aimed forward
            arm_angle = -math.pi * 0.03 + math.sin(phase * 0.4) * 0.03
        arm_length = 13
        hand_x = shoulder_x + int(math.cos(arm_angle) * arm_length) * facing
        hand_y = shoulder_y + int(math.sin(arm_angle) * arm_length) + 4
        elbow_x = shoulder_x + int(math.cos(arm_angle) * (arm_length * 0.55)) * facing
        elbow_y = shoulder_y + int(math.sin(arm_angle) * (arm_length * 0.55)) + 2
        # Upper arm (leather)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["shadow_deep"],
                         (shoulder_x + 1, shoulder_y + 1),
                         (elbow_x + 1, elbow_y + 1), 5)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["leather_darkest"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["leather_dark"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["leather_mid"],
                         (shoulder_x - 1, shoulder_y),
                         (elbow_x - 1, elbow_y), 2)
        # Forearm (skin)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["shadow_deep"],
                         (elbow_x + 1, elbow_y + 1),
                         (hand_x + 1, hand_y + 1), 4)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["skin_darkest"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 3)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["skin_dark"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 2)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["skin_mid"],
                         (elbow_x - 1, elbow_y), (hand_x - 1, hand_y), 1)
        # Bracer
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["leather_darkest"],
                         (hand_x - 2, hand_y - 1, 4, 4))
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["leather_dark"],
                         (hand_x - 2, hand_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["gold_dark"],
                         (hand_x - 2, hand_y - 1, 4, 1))
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["gold_light"],
                         (hand_x - 1, hand_y - 1, 2, 1))
        # ICE BOW
        _NS_nyrellieth._draw_ice_bow(surface, hand_x, hand_y, facing, phase, action,
                                     attack_progress)
    def _draw_ice_bow(surface, hand_x, hand_y, facing, phase, action, attack_progress):
        """Massive curved ice bow."""
        # Bow center at hand
        bow_cx = hand_x
        bow_cy = hand_y
        # Top and bottom tips (long curved bow)
        bow_top_x = bow_cx + facing * 2
        bow_top_y = bow_cy - 22
        bow_bot_x = bow_cx + facing * 2
        bow_bot_y = bow_cy + 22
        # Curve outward (facing direction)
        curve_outward_top = bow_cx + facing * 8
        curve_outward_mid = bow_cx + facing * 12
        curve_outward_bot = bow_cx + facing * 8
        # Bow arms (upper and lower) - curved shape
        # Upper arm bezier
        upper_segments = 5
        prev = (bow_cx + facing * 4, bow_cy - 2)
        for i in range(1, upper_segments + 1):
            t = i / upper_segments
            # Bezier from bow_cx, bow_cy through curve_outward_top to bow_top
            bx = int((1 - t) ** 2 * (bow_cx + facing * 4)
                     + 2 * (1 - t) * t * curve_outward_top
                     + t ** 2 * bow_top_x)
            by = int((1 - t) ** 2 * (bow_cy - 2)
                     + 2 * (1 - t) * t * (bow_cy - 12)
                     + t ** 2 * bow_top_y)
            thickness = max(2, 5 - i)
            # Shadow
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["shadow_deep"],
                             (prev[0] + 2, prev[1] + 2),
                             (bx + 2, by + 2), thickness + 1)
            # Dark bow wood/ice base
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["bow_darkest"],
                             prev, (bx, by), thickness)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["bow_dark"],
                             prev, (bx, by), thickness - 1)
            # Ice mid layer
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["bow_mid"],
                             prev, (bx, by), max(1, thickness - 2))
            # Bright ice edge
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_dark"],
                             (prev[0] - facing, prev[1]),
                             (bx - facing, by), 1)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_mid"],
                             (prev[0] - facing, prev[1] - 1),
                             (bx - facing, by - 1), 1)
            prev = (bx, by)
        # Sharp tip top (ice crystal)
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["shadow_deep"], [
            (bow_top_x + 1, bow_top_y - 3 + 1),
            (bow_top_x - 2 + 1, bow_top_y + 1),
            (bow_top_x + 2 + 1, bow_top_y + 1),
        ])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["ice_dark"], [
            (bow_top_x, bow_top_y - 3),
            (bow_top_x - 2, bow_top_y),
            (bow_top_x + 2, bow_top_y),
        ])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["ice_mid"], [
            (bow_top_x, bow_top_y - 2),
            (bow_top_x - 1, bow_top_y),
            (bow_top_x + 1, bow_top_y),
        ])
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_light"],
                         (bow_top_x, bow_top_y - 2, 1, 1))
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_shine"],
                         (bow_top_x, bow_top_y - 2, 1, 1))
        # Lower arm bezier (mirrored)
        prev = (bow_cx + facing * 4, bow_cy + 2)
        for i in range(1, upper_segments + 1):
            t = i / upper_segments
            bx = int((1 - t) ** 2 * (bow_cx + facing * 4)
                     + 2 * (1 - t) * t * curve_outward_bot
                     + t ** 2 * bow_bot_x)
            by = int((1 - t) ** 2 * (bow_cy + 2)
                     + 2 * (1 - t) * t * (bow_cy + 12)
                     + t ** 2 * bow_bot_y)
            thickness = max(2, 5 - i)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["shadow_deep"],
                             (prev[0] + 2, prev[1] + 2),
                             (bx + 2, by + 2), thickness + 1)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["bow_darkest"],
                             prev, (bx, by), thickness)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["bow_dark"],
                             prev, (bx, by), thickness - 1)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["bow_mid"],
                             prev, (bx, by), max(1, thickness - 2))
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_dark"],
                             (prev[0] - facing, prev[1]),
                             (bx - facing, by), 1)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_mid"],
                             (prev[0] - facing, prev[1] + 1),
                             (bx - facing, by + 1), 1)
            prev = (bx, by)
        # Sharp tip bottom
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["shadow_deep"], [
            (bow_bot_x + 1, bow_bot_y + 3 + 1),
            (bow_bot_x - 2 + 1, bow_bot_y + 1),
            (bow_bot_x + 2 + 1, bow_bot_y + 1),
        ])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["ice_dark"], [
            (bow_bot_x, bow_bot_y + 3),
            (bow_bot_x - 2, bow_bot_y),
            (bow_bot_x + 2, bow_bot_y),
        ])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["ice_mid"], [
            (bow_bot_x, bow_bot_y + 2),
            (bow_bot_x - 1, bow_bot_y),
            (bow_bot_x + 1, bow_bot_y),
        ])
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_light"],
                         (bow_bot_x, bow_bot_y + 2, 1, 1))
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_shine"],
                         (bow_bot_x, bow_bot_y + 2, 1, 1))
        # BOWSTRING (glowing ice)
        # String position depends on draw
        if action == "attack" and 0.4 <= attack_progress <= 0.55:
            # Drawn back
            string_pull_x = bow_cx - facing * 6
        elif action == "attack" and attack_progress < 0.4:
            # Being drawn
            t = attack_progress / 0.4
            string_pull_x = bow_cx - int(facing * 6 * t)
        else:
            string_pull_x = bow_cx
        # String from top tip to pull point to bottom tip
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_darkest"],
                         (bow_top_x, bow_top_y),
                         (string_pull_x, bow_cy), 1)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_mid"],
                         (bow_top_x, bow_top_y),
                         (string_pull_x, bow_cy), 1)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_darkest"],
                         (string_pull_x, bow_cy),
                         (bow_bot_x, bow_bot_y), 1)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_mid"],
                         (string_pull_x, bow_cy),
                         (bow_bot_x, bow_bot_y), 1)
        # Center grip (dark leather wrap)
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["shadow_deep"],
                         (bow_cx + facing * 2 - 1, bow_cy - 3, 3, 6))
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["leather_darkest"],
                         (bow_cx + facing * 2 - 1, bow_cy - 3, 3, 5))
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["leather_dark"],
                         (bow_cx + facing * 2 - 1, bow_cy - 3, 2, 5))
        # Gold band
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["gold_mid"],
                         (bow_cx + facing * 2 - 1, bow_cy - 1, 3, 1))
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["gold_light"],
                         (bow_cx + facing * 2 - 1, bow_cy, 3, 1))
        # Ice crystal decorations along bow
        for pos_t in (0.3, 0.6):
            # Upper crystal
            ux = int(bow_cx + (curve_outward_top - bow_cx) * pos_t * facing)
            uy = int(bow_cy - 8 * pos_t)
            crystal_pulse = math.sin(phase * 2 + pos_t) * 0.3 + 0.7
            for r in range(3, 0, -1):
                alpha = _NS_nyrellieth._alpha(150 * (3 - r) / 3 * crystal_pulse)
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_mid"], alpha),
                                         (ux, uy), r)
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_shine"], (ux, uy, 1, 1))
            # Lower crystal
            lx = int(bow_cx + (curve_outward_bot - bow_cx) * pos_t * facing)
            ly = int(bow_cy + 8 * pos_t)
            for r in range(3, 0, -1):
                alpha = _NS_nyrellieth._alpha(150 * (3 - r) / 3 * crystal_pulse)
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_mid"], alpha),
                                         (lx, ly), r)
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_shine"], (lx, ly, 1, 1))
        # Arrow nocked (visible when drawing)
        if action == "attack" and attack_progress < 0.6:
            # Arrow shaft from string to tip
            arrow_tip_x = bow_cx + facing * 12
            arrow_tail_x = string_pull_x - facing * 2
            arrow_y = bow_cy
            # Arrow shaft (dark)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["shadow_deep"],
                             (arrow_tail_x + 1, arrow_y + 1),
                             (arrow_tip_x + 1, arrow_y + 1), 2)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["bow_darkest"],
                             (arrow_tail_x, arrow_y),
                             (arrow_tip_x, arrow_y), 1)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["bow_mid"],
                             (arrow_tail_x, arrow_y),
                             (arrow_tip_x, arrow_y), 1)
            # Arrow tip (ice crystal)
            _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["ice_darkest"], [
                (arrow_tip_x + facing * 3, arrow_y),
                (arrow_tip_x, arrow_y - 2),
                (arrow_tip_x, arrow_y + 2),
            ])
            _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["ice_mid"], [
                (arrow_tip_x + facing * 2, arrow_y),
                (arrow_tip_x + facing, arrow_y - 1),
                (arrow_tip_x + facing, arrow_y + 1),
            ])
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_shine"],
                             (arrow_tip_x + facing * 2, arrow_y, 1, 1))
            # Fletching (feather at tail)
            for f_y_off in (-1, 1):
                pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_dark"],
                                 (arrow_tail_x, arrow_y),
                                 (arrow_tail_x - facing * 2, arrow_y + f_y_off), 1)
                pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_mid"],
                                 (arrow_tail_x, arrow_y),
                                 (arrow_tail_x - facing * 2, arrow_y + f_y_off), 1)
        # Charging glow when drawing
        if action == "attack" and attack_progress < 0.55:
            charge_t = min(1.0, attack_progress / 0.55)
            glow_size = int(4 + charge_t * 3)
            arrow_tip_x = bow_cx + facing * 12
            for r in range(glow_size + 3, 0, -1):
                alpha = _NS_nyrellieth._alpha(180 * (glow_size + 3 - r) / (glow_size + 3))
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_light"], alpha),
                                         (arrow_tip_x, bow_cy), r)
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_shine"],
                             (arrow_tip_x, bow_cy, 1, 1))
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["white"],
                             (arrow_tip_x, bow_cy, 1, 1))
    def _draw_dark_elf_head(surface, cx, cy, facing, phase, action, attack_progress):
        """Dark elf head with hood + silver hair + glowing eyes."""
        # Face oval (dark elf slender)
        head_pts = [
            (cx - 5, cy + 3),
            (cx - 6, cy - 1),
            (cx - 5, cy - 6),
            (cx - 2, cy - 8),
            (cx + 3, cy - 8),
            (cx + 6, cy - 5),
            (cx + 7, cy - 1),
            (cx + 6, cy + 3),
            (cx + 3, cy + 6),
            (cx - 2, cy + 6),
            (cx - 4, cy + 4),
        ]
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in head_pts])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["skin_darkest"], head_pts)
        # Face base (pale purple)
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["skin_dark"], [
            (cx - 4, cy + 2),
            (cx - 5, cy - 1),
            (cx - 4, cy - 5),
            (cx - 2, cy - 7),
            (cx + 3, cy - 7),
            (cx + 5, cy - 4),
            (cx + 6, cy - 1),
            (cx + 5, cy + 3),
            (cx + 2, cy + 5),
            (cx - 2, cy + 5),
        ])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["skin_mid"], [
            (cx - 3, cy - 2),
            (cx - 3, cy - 5),
            (cx, cy - 6),
            (cx + 3, cy - 6),
            (cx + 5, cy - 3),
            (cx + 5, cy),
            (cx + 3, cy + 3),
            (cx, cy + 4),
            (cx - 2, cy + 3),
        ])
        # Highlights
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["skin_light"], [
            (cx + 1, cy - 4),
            (cx + 3, cy - 4),
            (cx + 4, cy - 2),
            (cx + 2, cy),
        ])
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["skin_shine"],
                         (cx + facing * 2, cy - 3, 1, 1))
        # ELF POINTED EARS
        for side in (-1, 1):
            ear_x = cx + side * 6
            ear_y = cy - 1
            # Pointed ear extending outward
            _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["shadow_deep"], [
                (ear_x, ear_y - 2),
                (ear_x + side * 3, ear_y),
                (ear_x, ear_y + 3),
            ])
            _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["skin_dark"], [
                (ear_x, ear_y - 2),
                (ear_x + side * 2, ear_y),
                (ear_x, ear_y + 2),
            ])
            _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["skin_mid"], [
                (ear_x, ear_y - 1),
                (ear_x + side * 1, ear_y),
                (ear_x, ear_y + 1),
            ])
        # HOOD covering top of head + hair spilling out
        _NS_nyrellieth._draw_hood(surface, cx, cy, facing, phase)
        # LONG SILVER HAIR flowing behind
        _NS_nyrellieth._draw_silver_hair(surface, cx, cy, facing, phase)
        # GLOWING WHITE EYES (Drow signature)
        _NS_nyrellieth._draw_glowing_eyes(surface, cx, cy - 3, facing, phase, action)
        # Nose
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["skin_darkest"],
                         (cx + facing, cy - 1, 1, 1))
        # Focused mouth (calm/focused)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["skin_darkest"],
                         (cx - 1, cy + 3), (cx + 2, cy + 3), 1)
    def _draw_hood(surface, cx, cy, facing, phase):
        """Dark hood over top of head."""
        wind = math.sin(phase * 0.5) * 1
        hood_pts = [
            (cx - 7, cy - 4),
            (cx - 8, cy - 7),
            (cx - 6, cy - 10),
            (cx - 2, cy - 12),
            (cx + 3, cy - 12),
            (cx + 6, cy - 10),
            (cx + 8, cy - 7),
            (cx + 7, cy - 4),
            (cx + 5, cy - 4),
            (cx + 3, cy - 7),
            (cx - 3, cy - 7),
            (cx - 5, cy - 4),
        ]
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["shadow_deep"],
                             [(px + 1, py + 1) for px, py in hood_pts])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["cape_darkest"], hood_pts)
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["cape_dark"], [
            (cx - 7, cy - 5),
            (cx - 7, cy - 8),
            (cx - 5, cy - 10),
            (cx - 1, cy - 11),
            (cx + 3, cy - 11),
            (cx + 5, cy - 10),
            (cx + 7, cy - 7),
            (cx + 6, cy - 5),
            (cx + 5, cy - 5),
            (cx + 3, cy - 7),
            (cx - 3, cy - 7),
            (cx - 5, cy - 5),
        ])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["cape_mid"], [
            (cx - 6, cy - 6),
            (cx - 6, cy - 8),
            (cx - 3, cy - 10),
            (cx + 3, cy - 10),
            (cx + 5, cy - 8),
            (cx + 4, cy - 6),
            (cx + 2, cy - 8),
            (cx - 2, cy - 8),
        ])
        # Hood shadow inside (dark)
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["shadow_deep"], [
            (cx - 4, cy - 6),
            (cx + 4, cy - 6),
            (cx + 3, cy - 4),
            (cx - 3, cy - 4),
        ])
        # Gold trim along hood edge
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["gold_dark"],
                         (cx - 5, cy - 4), (cx - 3, cy - 6), 1)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["gold_light"],
                         (cx - 4, cy - 4), (cx - 3, cy - 5), 1)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["gold_dark"],
                         (cx + 5, cy - 4), (cx + 3, cy - 6), 1)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["gold_light"],
                         (cx + 4, cy - 4), (cx + 3, cy - 5), 1)
    def _draw_silver_hair(surface, cx, cy, facing, phase):
        """Long silver hair flowing behind (peeking out of hood)."""
        sway1 = math.sin(phase * 0.5) * 3
        sway2 = math.sin(phase * 0.7) * 2
        # Hair mass behind body (long)
        hair_bulk = [
            (cx - 7, cy - 3),
            (cx - 10, cy),
            (cx - 12, cy + 5),
            (cx - 13, cy + 12 + int(sway2 * 0.5)),
            (cx - 11, cy + 18 + int(sway2)),
            (cx - 8, cy + 24 + int(sway1)),
            (cx - 3, cy + 26 + int(sway1 * 0.8)),
            (cx + 2, cy + 25 + int(sway1 * 0.6)),
            (cx + 6, cy + 20 + int(sway1 * 0.5)),
            (cx + 8, cy + 12 + int(sway2 * 0.6)),
            (cx + 7, cy + 5),
            (cx + 5, cy),
            (cx + 5, cy - 3),
        ]
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["shadow_deep"],
                             [(px + 1, py + 2) for px, py in hair_bulk])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["hair_darkest"], hair_bulk)
        # Mid layer (silver)
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["hair_dark"], [
            (cx - 6, cy - 2),
            (cx - 9, cy + 1),
            (cx - 11, cy + 5),
            (cx - 11, cy + 12 + int(sway2 * 0.4)),
            (cx - 9, cy + 18 + int(sway2 * 0.8)),
            (cx - 6, cy + 22 + int(sway1 * 0.8)),
            (cx - 2, cy + 22 + int(sway1 * 0.6)),
            (cx + 2, cy + 20 + int(sway1 * 0.5)),
            (cx + 6, cy + 15 + int(sway2 * 0.6)),
            (cx + 7, cy + 8),
            (cx + 6, cy + 1),
            (cx + 4, cy - 3),
        ])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["hair_mid"], [
            (cx - 5, cy - 1),
            (cx - 8, cy + 2),
            (cx - 9, cy + 8),
            (cx - 8, cy + 15),
            (cx - 3, cy + 18 + int(sway1 * 0.5)),
            (cx + 2, cy + 15),
            (cx + 5, cy + 10),
            (cx + 5, cy + 3),
            (cx + 3, cy),
        ])
        # Silver strands highlight
        for i, (x_off, y_start, length) in enumerate([
            (-8, 0, 18), (-4, -2, 22), (2, -2, 20), (5, 0, 15),
        ]):
            for dy in range(length):
                if dy % 4 == 0:
                    hx = cx + x_off + int(math.sin(phase * 0.3 + i + dy * 0.2) * 0.5)
                    hy = cy + y_start + dy
                    pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["hair_light"],
                                     (hx, hy, 1, 1))
                elif dy % 7 == 0:
                    hx = cx + x_off
                    hy = cy + y_start + dy
                    pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["hair_shine"],
                                     (hx, hy, 1, 1))
        # Hair bangs peeking out from hood
        for i in range(4):
            bx = cx - 4 + i * 2
            by_top = cy - 6
            by_bot = cy - 3 + (i % 2)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["hair_dark"],
                             (bx, by_top), (bx, by_bot), 1)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["hair_mid"],
                             (bx + 1, by_top), (bx + 1, by_bot - 1), 1)
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["hair_light"],
                             (bx, by_bot - 1, 1, 1))
    def _draw_glowing_eyes(surface, cx, cy, facing, phase, action):
        """Bright glowing white-blue eyes (Drow signature)."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        intensity = 1.5 if action == "attack" else 1.0
        for side in (-1, 1):
            ex = cx + side * 2 + (1 if facing == 1 else -1)
            ey = cy
            # Deep dark socket
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["eye_socket"],
                             (ex - 1, ey - 1, 3, 2))
            # White-blue glow halo
            for radius in range(5, 0, -1):
                alpha = _NS_nyrellieth._alpha(120 * (5 - radius) / 5 * pulse * intensity)
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["eye_mid"], alpha),
                                         (ex, ey), radius)
            # Bright eye core
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["eye_dark"],
                             (ex - 1, ey - 1, 3, 2))
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["eye_mid"],
                             (ex, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["eye_glow"],
                             (ex + 1, ey, 1, 1))
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["white"],
                             (ex + 1, ey, 1, 1))
    # ============================================================
    # RANGED ATTACK - ICE ARROW PROJECTILE
    # ============================================================
    def _draw_ice_arrow_projectile(surface, boss, x, y, progress):
        """Ice arrow with cyan trail."""
        if progress < 0.55:
            return
        facing = boss.direction
        tx, ty = _NS_nyrellieth._target_position(boss, x, y)
        # Launch from bow center
        start_x = x + facing * 22
        start_y = y - 4
        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Direction for arrow orientation
        dx = tx - start_x
        dy = ty - start_y
        length = math.hypot(dx, dy)
        if length > 1:
            nx = dx / length
            ny = dy / length
            perp_x = -ny
            perp_y = nx
        else:
            nx, ny = facing, 0
            perp_x, perp_y = 0, 1
        # Long ice trail
        for i in range(12):
            trail_t = max(0.0, t - i * 0.04)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_nyrellieth._alpha(240 - i * 20)
            size = max(1, 7 - i)
            _NS_nyrellieth._aacircle(surface,
                                     (*_NS_nyrellieth.PALETTE["ice_darkest"], alpha),
                                     (px, py), size)
            _NS_nyrellieth._aacircle(surface,
                                     (*_NS_nyrellieth.PALETTE["ice_dark"], alpha),
                                     (px, py), max(1, size - 1))
            _NS_nyrellieth._aacircle(surface,
                                     (*_NS_nyrellieth.PALETTE["ice_mid"], alpha),
                                     (px, py), max(1, size - 2))
            _NS_nyrellieth._aacircle(surface,
                                     (*_NS_nyrellieth.PALETTE["ice_light"], alpha),
                                     (px, py), max(1, size - 3))
            # Frost sparks
            if i < 5:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface,
                                     (*_NS_nyrellieth.PALETTE["ice_hot"], alpha),
                                     (spark_x, spark_y, 1, 1))
        # ARROW SHAPE at head (not just a ball)
        arrow_shaft_start_x = bx - int(nx * 10)
        arrow_shaft_start_y = by - int(ny * 10)
        # Shaft
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["shadow_deep"],
                         (arrow_shaft_start_x + 1, arrow_shaft_start_y + 1),
                         (bx + 1, by + 1), 3)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_darkest"],
                         (arrow_shaft_start_x, arrow_shaft_start_y),
                         (bx, by), 2)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_dark"],
                         (arrow_shaft_start_x, arrow_shaft_start_y),
                         (bx, by), 1)
        pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_light"],
                         (arrow_shaft_start_x, arrow_shaft_start_y),
                         (bx, by), 1)
        # Arrowhead (crystal tip)
        tip_x = bx + int(nx * 4)
        tip_y = by + int(ny * 4)
        head_a = (bx + int(perp_x * 3), by + int(perp_y * 3))
        head_b = (bx - int(perp_x * 3), by - int(perp_y * 3))
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["shadow_deep"], [
            (tip_x + 1, tip_y + 1),
            (head_a[0] + 1, head_a[1] + 1),
            (head_b[0] + 1, head_b[1] + 1),
        ])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["ice_darkest"],
                             [(tip_x, tip_y), head_a, head_b])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["ice_dark"], [
            (tip_x, tip_y),
            (int((tip_x + head_a[0]) / 2), int((tip_y + head_a[1]) / 2)),
            (bx, by),
        ])
        _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["ice_mid"], [
            (tip_x, tip_y),
            (int((tip_x + bx) / 2), int((tip_y + by) / 2)),
            (bx, by),
        ])
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_light"],
                         (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_shine"],
                         (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["white"],
                         (tip_x, tip_y, 1, 1))
        # Fletching (feathers at back of arrow)
        for f in (-1, 1):
            f_end_x = arrow_shaft_start_x - int(nx * 2) + int(perp_x * f * 2)
            f_end_y = arrow_shaft_start_y - int(ny * 2) + int(perp_y * f * 2)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_dark"],
                             (arrow_shaft_start_x, arrow_shaft_start_y),
                             (f_end_x, f_end_y), 1)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_mid"],
                             (arrow_shaft_start_x, arrow_shaft_start_y),
                             (f_end_x, f_end_y), 1)
        # Radial glow around arrow
        for r in range(10, 3, -2):
            alpha = _NS_nyrellieth._alpha(70 * (10 - r) / 10)
            _NS_nyrellieth._aacircle(surface,
                                     (*_NS_nyrellieth.PALETTE["ice_light"], alpha),
                                     (bx, by), r)
        # IMPACT (frost burst)
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(10 + st * 22)
            alpha = _NS_nyrellieth._alpha(240 * (1 - st))
            _NS_nyrellieth._aacircle(surface,
                                     (*_NS_nyrellieth.PALETTE["ice_darkest"], alpha),
                                     (tx, ty), radius + 3, 3)
            _NS_nyrellieth._aacircle(surface,
                                     (*_NS_nyrellieth.PALETTE["ice_dark"], alpha),
                                     (tx, ty), radius, 3)
            _NS_nyrellieth._aacircle(surface,
                                     (*_NS_nyrellieth.PALETTE["ice_mid"], alpha),
                                     (tx, ty), max(1, radius - 5), 2)
            _NS_nyrellieth._aacircle(surface,
                                     (*_NS_nyrellieth.PALETTE["ice_light"], alpha),
                                     (tx, ty), max(1, radius - 10), 1)
            # Frost shards flying out
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                # Ice shard shape
                pygame.draw.line(surface,
                                 (*_NS_nyrellieth.PALETTE["ice_mid"], alpha),
                                 (tx, ty), (ex, ey), 1)
                pygame.draw.rect(surface,
                                 (*_NS_nyrellieth.PALETTE["ice_shine"], alpha),
                                 (ex, ey, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_nyrellieth.PALETTE["white"], alpha),
                                 (ex, ey, 1, 1))
    # ============================================================
    # FROST MIST (ambient)
    # ============================================================
    def _draw_frost_mist(surface, cx, cy, phase, trail=False, facing=1,
                         intense=False):
        """Icy cyan mist below floating ranger."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((160, 55), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(38, 3, -3):
            alpha = _NS_nyrellieth._alpha((38 - radius) * 2.2 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_nyrellieth.PALETTE["mist_dark"], alpha),
                    (80 - radius * 2, 27 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(26, 3, -2):
            alpha = _NS_nyrellieth._alpha((26 - radius) * 3.4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_nyrellieth.PALETTE["mist_mid"], alpha),
                    (80 - radius, 27 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 80, cy - 12))
        # Rising ice crystals/sparkles
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 28)
            alpha = _NS_nyrellieth._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_nyrellieth._aacircle(surface,
                                     (*_NS_nyrellieth.PALETTE["ice_dark"], alpha),
                                     (sx, sy), 3)
            _NS_nyrellieth._aacircle(surface,
                                     (*_NS_nyrellieth.PALETTE["ice_mid"], alpha),
                                     (sx, sy - 1), 2)
            pygame.draw.rect(surface,
                             (*_NS_nyrellieth.PALETTE["ice_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_nyrellieth.PALETTE["ice_hot"], alpha),
                             (sx, sy - 2, 1, 1))
        # Snowflake sparkles
        for i in range(8):
            ember_t = (phase * 0.6 + i * 0.15) % 1.0
            ex = cx - 24 + i * 6 + int(math.sin(phase + i) * 4)
            ey = cy + 4 - int(ember_t * 26)
            alpha = _NS_nyrellieth._alpha(230 * (1 - ember_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface,
                                 (*_NS_nyrellieth.PALETTE["ice_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_nyrellieth.PALETTE["ice_shine"], alpha),
                                 (ex, ey, 1, 1))
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_nyrellieth._alpha(160 - i * 22)
                if alpha <= 0:
                    continue
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_dark"], alpha),
                                         (sx, sy), max(2, 6 - i))
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_mid"], alpha),
                                         (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface,
                                 (*_NS_nyrellieth.PALETTE["ice_light"], alpha),
                                 (sx, sy - 1, 2, 2))
    # ============================================================
    # AMBIENT (TRUE BOSS scale)
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        hover_offset = int(math.sin(phase * 0.8) * 1)
        shadow = pygame.Surface((140, 28), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 14 - radius, 120 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (3, 5, 12, 170), (10, 8, 120, 12))
        pygame.draw.ellipse(shadow, (15, 30, 55, 110), (18, 10, 104, 8))
        surface.blit(shadow, (x - 70, y - 14 + hover_offset))
    def _draw_frost_aura(surface, x, y, phase):
        """Massive frost aura (TRUE BOSS)."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for radius in range(105, 5, -5):
            alpha = _NS_nyrellieth._alpha((105 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_nyrellieth._aacircle(aura,
                                         (*_NS_nyrellieth.PALETTE["ice_darkest"], alpha),
                                         (120, 100), radius)
        for radius in range(70, 5, -4):
            alpha = _NS_nyrellieth._alpha((70 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_nyrellieth._aacircle(aura,
                                         (*_NS_nyrellieth.PALETTE["ice_dark"], alpha),
                                         (120, 100), radius)
        for radius in range(40, 5, -3):
            alpha = _NS_nyrellieth._alpha((40 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_nyrellieth._aacircle(aura,
                                         (*_NS_nyrellieth.PALETTE["ice_mid"], alpha),
                                         (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))
        # Snowflakes falling
        for i in range(10):
            fall_t = (phase * 0.3 + i * 0.1) % 1.0
            fx = x - 60 + i * 12 + int(math.sin(phase + i) * 6)
            fy = y - 40 + int(fall_t * 80)
            alpha = _NS_nyrellieth._alpha(200 * (1 - fall_t))
            if alpha > 0:
                # Simple snowflake shape (small plus)
                pygame.draw.rect(surface,
                                 (*_NS_nyrellieth.PALETTE["ice_light"], alpha),
                                 (fx, fy, 2, 1))
                pygame.draw.rect(surface,
                                 (*_NS_nyrellieth.PALETTE["ice_light"], alpha),
                                 (fx, fy - 1, 1, 2))
                pygame.draw.rect(surface,
                                 (*_NS_nyrellieth.PALETTE["ice_shine"], alpha),
                                 (fx, fy, 1, 1))
        # Floating ice particles
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 45 + int(math.sin(phase + i) * 14)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Large frost rune ring (TRUE BOSS)."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 58), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_nyrellieth.PALETTE["ice_darkest"], 210),
                            (5, 20, 170, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_nyrellieth.PALETTE["ice_dark"], 230),
                            (14, 22, 152, 24), 2)
        pygame.draw.ellipse(ring, (*_NS_nyrellieth.PALETTE["ice_mid"], 220),
                            (25, 24, 130, 20), 1)
        # Frost runes (radial spokes)
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 90 + int(math.cos(angle) * 48)
            y1 = 32 + int(math.sin(angle) * 9)
            x2 = 90 + int(math.cos(angle) * 76)
            y2 = 32 + int(math.sin(angle) * 13)
            pygame.draw.line(ring, (*_NS_nyrellieth.PALETTE["ice_light"], 230),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_nyrellieth.PALETTE["ice_hot"],
                                 _NS_nyrellieth._alpha(150 * pulse)),
                                (15, 12, 150, 42), 1)
        surface.blit(ring, (x - 90, y - 29))
    # ============================================================
    # SKILL Q: FROST ARROWS (enhanced ice shot)
    # ============================================================
    def _draw_frostarrow_foreground(surface, boss, x, y, timer, phase):
        """Enhanced frost arrow projectile."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_nyrellieth._target_position(boss, x, y)
        if progress < 0.25:
            # Charge in bow
            t = progress / 0.25
            bow_pos_x = x + facing * 22
            bow_pos_y = y - 4
            cr = int(4 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_nyrellieth._alpha(220 * (cr + 5 - r) / (cr + 5))
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_darkest"], alpha),
                                         (bow_pos_x, bow_pos_y), r)
            _NS_nyrellieth._aacircle(surface, _NS_nyrellieth.PALETTE["ice_dark"],
                                     (bow_pos_x, bow_pos_y), cr - 1)
            _NS_nyrellieth._aacircle(surface, _NS_nyrellieth.PALETTE["ice_mid"],
                                     (bow_pos_x, bow_pos_y), max(1, cr - 3))
            _NS_nyrellieth._aacircle(surface, _NS_nyrellieth.PALETTE["ice_light"],
                                     (bow_pos_x, bow_pos_y), max(1, cr - 4))
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_shine"],
                             (bow_pos_x, bow_pos_y, 1, 1))
            # Frost gathering
            for i in range(4):
                angle = phase * 4 + i * math.pi / 2
                sx = bow_pos_x + int(math.cos(angle) * (10 - t * 5))
                sy = bow_pos_y + int(math.sin(angle) * (10 - t * 5))
                pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_light"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_shine"], (sx, sy, 1, 1))
        else:
            # Arrow flies (larger/brighter than basic)
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 26
            start_y = y - 4
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Direction
            dx = tx - start_x
            dy = ty - start_y
            length = math.hypot(dx, dy)
            if length > 1:
                nx = dx / length
                ny = dy / length
                perp_x = -ny
                perp_y = nx
            else:
                nx, ny = facing, 0
                perp_x, perp_y = 0, 1
            # Extra bright trail
            for i in range(14):
                trail_t = max(0.0, t - i * 0.035)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_nyrellieth._alpha(250 - i * 18)
                size = max(1, 9 - i)
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_darkest"], alpha),
                                         (px, py), size)
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_dark"], alpha),
                                         (px, py), max(1, size - 1))
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_mid"], alpha),
                                         (px, py), max(1, size - 2))
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_light"], alpha),
                                         (px, py), max(1, size - 3))
                # Sparks
                if i < 6:
                    for s in range(3):
                        spark_x = px + int(math.sin(t * 8 + i + s) * (size + 2))
                        spark_y = py + int(math.cos(t * 8 + i + s) * (size + 2))
                        pygame.draw.rect(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_hot"], alpha),
                                         (spark_x, spark_y, 1, 1))
            # Arrow shape
            arrow_start_x = bx - int(nx * 12)
            arrow_start_y = by - int(ny * 12)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["shadow_deep"],
                             (arrow_start_x + 1, arrow_start_y + 1),
                             (bx + 1, by + 1), 4)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_darkest"],
                             (arrow_start_x, arrow_start_y),
                             (bx, by), 3)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_mid"],
                             (arrow_start_x, arrow_start_y),
                             (bx, by), 2)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_shine"],
                             (arrow_start_x, arrow_start_y),
                             (bx, by), 1)
            # Big arrowhead
            tip_x = bx + int(nx * 6)
            tip_y = by + int(ny * 6)
            head_a = (bx + int(perp_x * 4), by + int(perp_y * 4))
            head_b = (bx - int(perp_x * 4), by - int(perp_y * 4))
            _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["ice_darkest"],
                                 [(tip_x, tip_y), head_a, head_b])
            _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["ice_mid"], [
                (tip_x, tip_y),
                (int((tip_x + bx) / 2), int((tip_y + by) / 2)),
                (bx, by),
            ])
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_shine"],
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["white"],
                             (tip_x, tip_y, 1, 1))
            # Big impact freeze zone
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(15 + st * 25)
                alpha = _NS_nyrellieth._alpha(240 * (1 - st))
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_darkest"], alpha),
                                         (tx, ty), radius + 3, 3)
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_dark"], alpha),
                                         (tx, ty), radius, 3)
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_mid"], alpha),
                                         (tx, ty), max(1, radius - 5), 2)
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_light"], alpha),
                                         (tx, ty), max(1, radius - 12), 1)
                # Ice shard crystals bursting outward
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    # Crystal spike
                    tip_local = (ex + int(math.cos(angle_s) * 4),
                                 ey + int(math.sin(angle_s) * 4))
                    perp_a = angle_s + math.pi / 2
                    base_a = (ex + int(math.cos(perp_a) * 2),
                              ey + int(math.sin(perp_a) * 2))
                    base_b = (ex - int(math.cos(perp_a) * 2),
                              ey - int(math.sin(perp_a) * 2))
                    _NS_nyrellieth._poly(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_mid"], alpha),
                                         [tip_local, base_a, base_b])
                    _NS_nyrellieth._poly(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_light"], alpha),
                                         [tip_local,
                                          (int((tip_local[0] + ex) / 2),
                                           int((tip_local[1] + ey) / 2)),
                                          (ex, ey)])
                    pygame.draw.rect(surface,
                                     (*_NS_nyrellieth.PALETTE["ice_shine"], alpha),
                                     (tip_local[0], tip_local[1], 1, 1))
    # ============================================================
    # SKILL W: MULTISHOT (5 arrows at once)
    # ============================================================
    def _draw_multishot_foreground(surface, boss, x, y, timer, phase):
        """5 ice arrows spread outward."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_nyrellieth._target_position(boss, x, y)
        if progress < 0.25:
            # Charge in bow
            t = progress / 0.25
            bow_pos_x = x + facing * 22
            bow_pos_y = y - 4
            cr = int(6 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_nyrellieth._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_dark"], alpha),
                                         (bow_pos_x, bow_pos_y), r)
            _NS_nyrellieth._aacircle(surface, _NS_nyrellieth.PALETTE["ice_mid"],
                                     (bow_pos_x, bow_pos_y), cr - 2)
            _NS_nyrellieth._aacircle(surface, _NS_nyrellieth.PALETTE["ice_light"],
                                     (bow_pos_x, bow_pos_y), max(1, cr - 4))
            _NS_nyrellieth._aacircle(surface, _NS_nyrellieth.PALETTE["ice_shine"],
                                     (bow_pos_x, bow_pos_y), max(1, cr - 6))
        else:
            # Arrows fly in a spread pattern (5 arrows)
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 26
            start_y = y - 4
            # Base direction to target
            base_dx = tx - start_x
            base_dy = ty - start_y
            base_len = math.hypot(base_dx, base_dy)
            if base_len < 1:
                base_len = 1
            base_nx = base_dx / base_len
            base_ny = base_dy / base_len
            base_angle = math.atan2(base_ny, base_nx)
            # 5 arrows with spread angles
            num_arrows = 5
            spread = math.pi * 0.35  # total spread angle
            for arrow_i in range(num_arrows):
                offset_ratio = (arrow_i - (num_arrows - 1) / 2) / max(1, (num_arrows - 1) / 2)
                arrow_angle = base_angle + offset_ratio * spread / 2
                # Each arrow's target position (extended in that direction)
                arrow_travel_dist = base_len
                arrow_tx = start_x + math.cos(arrow_angle) * arrow_travel_dist
                arrow_ty = start_y + math.sin(arrow_angle) * arrow_travel_dist
                bx = int(start_x + (arrow_tx - start_x) * t)
                by = int(start_y + (arrow_ty - start_y) * t)
                # Direction
                nx = math.cos(arrow_angle)
                ny = math.sin(arrow_angle)
                perp_x = -ny
                perp_y = nx
                # Short trail per arrow
                for i in range(6):
                    trail_t = max(0.0, t - i * 0.06)
                    px = int(start_x + (arrow_tx - start_x) * trail_t)
                    py = int(start_y + (arrow_ty - start_y) * trail_t)
                    alpha = _NS_nyrellieth._alpha(220 - i * 30)
                    size = max(1, 5 - i)
                    _NS_nyrellieth._aacircle(surface,
                                             (*_NS_nyrellieth.PALETTE["ice_dark"], alpha),
                                             (px, py), size)
                    _NS_nyrellieth._aacircle(surface,
                                             (*_NS_nyrellieth.PALETTE["ice_mid"], alpha),
                                             (px, py), max(1, size - 1))
                    _NS_nyrellieth._aacircle(surface,
                                             (*_NS_nyrellieth.PALETTE["ice_light"], alpha),
                                             (px, py), max(1, size - 2))
                # Arrow shaft
                arrow_start_x = bx - int(nx * 8)
                arrow_start_y = by - int(ny * 8)
                pygame.draw.line(surface, _NS_nyrellieth.PALETTE["shadow_deep"],
                                 (arrow_start_x + 1, arrow_start_y + 1),
                                 (bx + 1, by + 1), 3)
                pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_darkest"],
                                 (arrow_start_x, arrow_start_y),
                                 (bx, by), 2)
                pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_light"],
                                 (arrow_start_x, arrow_start_y),
                                 (bx, by), 1)
                # Arrowhead
                tip_x = bx + int(nx * 4)
                tip_y = by + int(ny * 4)
                head_a = (bx + int(perp_x * 2), by + int(perp_y * 2))
                head_b = (bx - int(perp_x * 2), by - int(perp_y * 2))
                _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["ice_darkest"],
                                     [(tip_x, tip_y), head_a, head_b])
                _NS_nyrellieth._poly(surface, _NS_nyrellieth.PALETTE["ice_mid"], [
                    (tip_x, tip_y),
                    (int((tip_x + bx) / 2), int((tip_y + by) / 2)),
                    (bx, by),
                ])
                pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_shine"],
                                 (tip_x, tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["white"],
                                 (tip_x, tip_y, 1, 1))
                # Fletching
                for f in (-1, 1):
                    f_end_x = arrow_start_x - int(nx * 2) + int(perp_x * f * 2)
                    f_end_y = arrow_start_y - int(ny * 2) + int(perp_y * f * 2)
                    pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_dark"],
                                     (arrow_start_x, arrow_start_y),
                                     (f_end_x, f_end_y), 1)
                    pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_mid"],
                                     (arrow_start_x, arrow_start_y),
                                     (f_end_x, f_end_y), 1)
    # ============================================================
    # SKILL E: SILENCE (beam that silences target)
    # ============================================================
    def _draw_silence_foreground(surface, boss, x, y, timer, phase):
        """Beam of silence energy to target + silence symbol above."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_nyrellieth._target_position(boss, x, y)
        if progress < 0.2:
            # Wind-up: gather at hand
            t = progress / 0.2
            hand_x = x + facing * 22
            hand_y = y - 4
            for r in range(int(10 * t), 0, -1):
                alpha = _NS_nyrellieth._alpha(200 * (10 * t - r) / max(1, 10 * t))
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_dark"], alpha),
                                         (hand_x, hand_y), r)
            _NS_nyrellieth._aacircle(surface, _NS_nyrellieth.PALETTE["ice_mid"],
                                     (hand_x, hand_y), max(1, int(5 * t)))
            _NS_nyrellieth._aacircle(surface, _NS_nyrellieth.PALETTE["ice_light"],
                                     (hand_x, hand_y), max(1, int(3 * t)))
        else:
            # BEAM to target
            t = (progress - 0.2) / 0.8
            hand_x = x + facing * 22
            hand_y = y - 4
            beam_intensity = math.sin(phase * 5) * 0.2 + 0.8
            # Multi-layer beam
            for layer_i, (width, color) in enumerate([
                (6, _NS_nyrellieth.PALETTE["ice_darkest"]),
                (4, _NS_nyrellieth.PALETTE["ice_dark"]),
                (2, _NS_nyrellieth.PALETTE["ice_mid"]),
                (1, _NS_nyrellieth.PALETTE["ice_shine"]),
            ]):
                alpha = _NS_nyrellieth._alpha(230 * beam_intensity)
                pygame.draw.line(surface, (*color, alpha),
                                 (hand_x, hand_y), (tx, ty), width)
            # Wavy sparkles along beam
            beam_len = math.hypot(tx - hand_x, ty - hand_y)
            if beam_len > 5:
                dx = (tx - hand_x) / beam_len
                dy = (ty - hand_y) / beam_len
                perp_x = -dy
                perp_y = dx
                for i in range(int(beam_len / 6)):
                    seg_dist = i * 6
                    sx = int(hand_x + dx * seg_dist)
                    sy = int(hand_y + dy * seg_dist)
                    wave = math.sin(phase * 6 + i * 0.5) * 4
                    sx += int(perp_x * wave)
                    sy += int(perp_y * wave)
                    pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_hot"],
                                     (sx, sy, 2, 2))
                    pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_shine"],
                                     (sx, sy, 1, 1))
            # Origin glow
            for r in range(6, 0, -1):
                alpha = _NS_nyrellieth._alpha(150 * (6 - r) / 6 * beam_intensity)
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_light"], alpha),
                                         (hand_x, hand_y), r)
            # Target glow
            for r in range(8, 0, -1):
                alpha = _NS_nyrellieth._alpha(140 * (8 - r) / 8 * beam_intensity)
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_dark"], alpha),
                                         (tx, ty), r)
            _NS_nyrellieth._aacircle(surface, _NS_nyrellieth.PALETTE["ice_mid"], (tx, ty), 4)
            _NS_nyrellieth._aacircle(surface, _NS_nyrellieth.PALETTE["ice_shine"], (tx, ty), 2)
            # SILENCE SYMBOL above target (Ø circle with slash)
            sym_x = tx
            sym_y = ty - 22
            sym_pulse = math.sin(phase * 3) * 0.3 + 0.7
            sym_r = 6
            # Circle
            _NS_nyrellieth._aacircle(surface, _NS_nyrellieth.PALETTE["shadow_deep"],
                                     (sym_x, sym_y), sym_r + 1)
            _NS_nyrellieth._aacircle(surface, _NS_nyrellieth.PALETTE["ice_darkest"],
                                     (sym_x, sym_y), sym_r, 2)
            _NS_nyrellieth._aacircle(surface, _NS_nyrellieth.PALETTE["ice_mid"],
                                     (sym_x, sym_y), sym_r, 1)
            # Diagonal slash through circle
            slash_a = (sym_x - int(sym_r * 0.7), sym_y - int(sym_r * 0.7))
            slash_b = (sym_x + int(sym_r * 0.7), sym_y + int(sym_r * 0.7))
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_darkest"],
                             slash_a, slash_b, 3)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_light"],
                             slash_a, slash_b, 2)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_shine"],
                             slash_a, slash_b, 1)
            # Glow around symbol
            for r in range(10, 3, -2):
                alpha = _NS_nyrellieth._alpha(120 * (10 - r) / 10 * sym_pulse)
                _NS_nyrellieth._aacircle(surface,
                                         (*_NS_nyrellieth.PALETTE["ice_light"], alpha),
                                         (sym_x, sym_y), r)
    # ============================================================
    # SKILL R: MARKSMANSHIP (aura buff)
    # ============================================================
    def _draw_marksmanship_ground(surface, boss, x, y, timer, phase):
        """Frost rune circle under boss."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 2))
        if r > 3:
            # Concentric rings
            pygame.draw.ellipse(surface,
                                (*_NS_nyrellieth.PALETTE["ice_darkest"], 220),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_nyrellieth.PALETTE["ice_dark"], 200),
                                (x - r + 4, y + 40 - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface,
                                (*_NS_nyrellieth.PALETTE["ice_mid"], 220),
                                (x - r + 10, y + 40 - r // 3 + 5,
                                 r * 2 - 20, r * 2 // 3 - 10), 2)
            pygame.draw.ellipse(surface,
                                (*_NS_nyrellieth.PALETTE["ice_light"], 180),
                                (x - r + 16, y + 40 - r // 3 + 8,
                                 r * 2 - 32, r * 2 // 3 - 16), 1)
            # Star/snowflake shape in center
            for i in range(6):
                angle = phase * 0.3 + i * math.pi / 3
                x1 = x + int(math.cos(angle) * r)
                y1 = y + 40 + int(math.sin(angle) * r * 0.4)
                x2 = x + int(math.cos(angle) * (r - 12))
                y2 = y + 40 + int(math.sin(angle) * (r - 12) * 0.4)
                pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_shine"],
                                 (x1, y1), (x2, y2), 2)
    def _draw_marksmanship_aura(surface, boss, x, y, timer, phase):
        """Ice snowflake aura around boss."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Body aura (ice)
        aura_r = 45 + int(math.sin(phase * 3) * 4)
        aura_surf = pygame.Surface((aura_r * 2 + 20, aura_r * 2 + 20), pygame.SRCALPHA)
        center = (aura_r + 10, aura_r + 10)
        for r in range(aura_r, 3, -3):
            alpha = _NS_nyrellieth._alpha(100 * (aura_r - r) / aura_r)
            _NS_nyrellieth._aacircle(aura_surf,
                                     (*_NS_nyrellieth.PALETTE["ice_dark"], alpha),
                                     center, r)
        # Snowflakes orbiting
        for i in range(10):
            angle = -phase * 1.5 + i * math.pi / 5
            sx = center[0] + int(math.cos(angle) * aura_r)
            sy = center[1] + int(math.sin(angle) * aura_r)
            # Small snowflake (cross)
            pygame.draw.rect(aura_surf, _NS_nyrellieth.PALETTE["ice_light"],
                             (sx - 1, sy, 3, 1))
            pygame.draw.rect(aura_surf, _NS_nyrellieth.PALETTE["ice_light"],
                             (sx, sy - 1, 1, 3))
            pygame.draw.rect(aura_surf, _NS_nyrellieth.PALETTE["ice_shine"],
                             (sx, sy, 1, 1))
            pygame.draw.rect(aura_surf, _NS_nyrellieth.PALETTE["white"],
                             (sx, sy, 1, 1))
        surface.blit(aura_surf, (x - aura_r - 10, y - aura_r - 10 - 5))
        # Big snowflake symbol above head (Marksmanship icon)
        sym_x = x
        sym_y = y - 40
        sym_pulse = math.sin(phase * 2) * 0.3 + 0.7
        # 6-point snowflake/star
        for i in range(6):
            angle = i * math.pi / 3 + phase * 0.3
            outer_r = 10
            outer_x = sym_x + int(math.cos(angle) * outer_r)
            outer_y = sym_y + int(math.sin(angle) * outer_r)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_darkest"],
                             (sym_x, sym_y), (outer_x, outer_y), 3)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_mid"],
                             (sym_x, sym_y), (outer_x, outer_y), 2)
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_shine"],
                             (sym_x, sym_y), (outer_x, outer_y), 1)
            # Small tips at outer end
            tip_perp = angle + math.pi / 2
            tip_a = (outer_x + int(math.cos(tip_perp) * 2),
                     outer_y + int(math.sin(tip_perp) * 2))
            tip_b = (outer_x - int(math.cos(tip_perp) * 2),
                     outer_y - int(math.sin(tip_perp) * 2))
            pygame.draw.line(surface, _NS_nyrellieth.PALETTE["ice_light"],
                             tip_a, tip_b, 1)
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["ice_shine"],
                             (outer_x, outer_y, 1, 1))
            pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["white"],
                             (outer_x, outer_y, 1, 1))
        # Center glow
        for r in range(8, 0, -1):
            alpha = _NS_nyrellieth._alpha(200 * (8 - r) / 8 * sym_pulse)
            _NS_nyrellieth._aacircle(surface,
                                     (*_NS_nyrellieth.PALETTE["ice_light"], alpha),
                                     (sym_x, sym_y), r)
        pygame.draw.rect(surface, _NS_nyrellieth.PALETTE["white"],
                         (sym_x, sym_y, 1, 1))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_ignakhor(surface, boss, x, y):
    """Entry point ignakhor."""
    return _NS_ignakhor.draw_ignakhor(surface, boss, x, y)


def draw_kazureth(surface, boss, x, y):
    """Entry point kazureth."""
    return _NS_kazureth.draw_kazureth(surface, boss, x, y)


def draw_sethrakhar(surface, boss, x, y):
    """Entry point sethrakhar."""
    return _NS_sethrakhar.draw_sethrakhar(surface, boss, x, y)


def draw_nyrellieth(surface, boss, x, y):
    """Entry point nyrellieth."""
    return _NS_nyrellieth.draw_nyrellieth(surface, boss, x, y)
