"""
bosses/level9.py - Semua boss Level 9

Berisi:
  - kenshiro   (mini boss)
  - khazan     (mini boss)
  - wiro       (mini boss)
  - naraka     (TRUE BOSS)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True



# ====================================================================
# kenshiro.py
# ====================================================================

# ====================================================================
# KENSHIRO (Ryoma-inspired) - The Wandering Blade - Mini Boss
# ====================================================================


class _NS_kenshiro:
    """Namespace kenshiro - Wandering ronin mini boss (floating)."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin (light asian tan)
        "skin_darkest": (65, 42, 32),
        "skin_dark": (125, 88, 68),
        "skin_mid": (185, 140, 110),
        "skin_light": (225, 185, 150),
        "skin_shine": (250, 220, 190),

        # Hair (black with slight brown)
        "hair_darkest": (8, 6, 10),
        "hair_dark": (28, 22, 30),
        "hair_mid": (60, 50, 58),
        "hair_light": (95, 82, 90),

        # Kimono / cloth (dark blue-navy)
        "cloth_darkest": (8, 12, 25),
        "cloth_dark": (22, 32, 60),
        "cloth_mid": (48, 65, 105),
        "cloth_light": (95, 118, 165),
        "cloth_edge": (145, 170, 215),

        # White kimono under-layer
        "white_darkest": (60, 62, 70),
        "white_dark": (120, 122, 130),
        "white_mid": (180, 182, 190),
        "white_light": (230, 232, 240),

        # Straw hat (kasa)
        "hat_darkest": (35, 22, 10),
        "hat_dark": (85, 55, 25),
        "hat_mid": (145, 105, 55),
        "hat_light": (200, 160, 100),
        "hat_shine": (235, 200, 145),

        # Armor accents (dark iron)
        "armor_darkest": (12, 10, 15),
        "armor_dark": (35, 32, 40),
        "armor_mid": (75, 70, 82),
        "armor_light": (130, 125, 140),
        "armor_shine": (185, 180, 195),

        # Gold accents
        "gold_darkest": (55, 32, 8),
        "gold_dark": (115, 78, 22),
        "gold_mid": (195, 148, 55),
        "gold_light": (245, 210, 115),
        "gold_shine": (255, 245, 190),

        # Katana blade (steel)
        "blade_darkest": (30, 32, 40),
        "blade_dark": (80, 82, 95),
        "blade_mid": (155, 158, 175),
        "blade_light": (215, 218, 230),
        "blade_shine": (250, 252, 255),

        # Sword energy (bright golden - main FX)
        "energy_darkest": (60, 30, 5),
        "energy_dark": (145, 85, 15),
        "energy_mid": (235, 165, 40),
        "energy_light": (255, 220, 110),
        "energy_hot": (255, 245, 190),
        "energy_shine": (255, 255, 230),

        # Eye glow (dim amber - concentrated warrior)
        "eye_dark": (55, 30, 10),
        "eye_mid": (180, 120, 40),
        "eye_light": (235, 190, 100),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 3),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _rgba(color, alpha):
        return (max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
                max(0, min(255, int(alpha))))

    def _aacircle(surface, color, center, radius, width=0):
        if len(color) == 4:
            color = (max(0, min(255, int(color[0]))),
                     max(0, min(255, int(color[1]))),
                     max(0, min(255, int(color[2]))),
                     max(0, min(255, int(color[3]))))
        else:
            color = _NS_kenshiro._clamp(color)
        if _NS_kenshiro.HAS_AACIRCLE and radius > 1:
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
            color = _NS_kenshiro._clamp(color)
        if _NS_kenshiro.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_kenshiro._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # dengan kompensasi scale (hero di-render di canvas lalu
            # di-scale; boss langsung di layar scale=1).
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return int(x + 220 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_kenshiro(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kenshiro._detect_moving(boss)
        _NS_kenshiro._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_ken_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        _NS_kenshiro._draw_gold_aura(surface, x, y, pulse)
        _NS_kenshiro._draw_ground_ring(surface, x, y + 48, pulse, active_skill)

        # Skill ground FX
        if active_skill == "w":
            _NS_kenshiro._draw_assault_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kenshiro._draw_gale_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kenshiro._draw_supremacy_ground(surface, boss, x, y, skill_timer, pulse)

        # BODY
        if active_skill == "e":
            _NS_kenshiro._draw_gale_body(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kenshiro._draw_assault_body(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kenshiro._draw_supremacy_body(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_kenshiro._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_kenshiro._draw_float_move(surface, boss, x, y)
        else:
            _NS_kenshiro._draw_idle(surface, boss, x, y)

        # Foreground FX
        if active_skill == "q":
            _NS_kenshiro._draw_swiftslash_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kenshiro._draw_assault_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kenshiro._draw_gale_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kenshiro._draw_supremacy_fg(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_ken_previous_timer", 0))
        active = bool(getattr(boss, "_ken_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._ken_attack_active = True
            boss._ken_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._ken_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._ken_attack_frame = int(getattr(boss, "_ken_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._ken_attack_active = False
            boss._ken_attack_frame = 0
            active = False

        boss._ken_previous_timer = timer
        boss._ken_attack_progress = (
            min(1.0, getattr(boss, "_ken_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_ken_last_x"):
            boss._ken_last_x = boss.x
            boss._ken_last_y = boss.y
            return False
        dx = abs(boss.x - boss._ken_last_x)
        dy = abs(boss.y - boss._ken_last_y)
        boss._ken_last_x = boss.x
        boss._ken_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        # Meditative float - slow drift
        float_bob = int(math.sin(boss.pulse * 0.5) * 6)
        float_sway = int(math.sin(boss.pulse * 0.35) * 2)
        _NS_kenshiro._draw_shadow_float(surface, x, y + 52, boss.pulse, intensity=1.0)
        _NS_kenshiro._draw_float_wisps(surface, x, y + 46, boss.pulse, intensity=1.0)
        _NS_kenshiro._draw_body(surface, x + float_sway, y + float_bob,
                                 boss.direction, boss.pulse, "idle")

    def _draw_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.7
        # Floating movement (no leg stride)
        float_bob = int(math.sin(phase * 0.7) * 5)
        float_sway = int(math.sin(phase * 0.5) * 2)
        _NS_kenshiro._draw_shadow_float(surface, x + float_sway, y + 52, phase,
                                         intensity=0.85)
        _NS_kenshiro._draw_float_wisps(surface, x + float_sway, y + 46, phase,
                                        intensity=1.4, trail=True, facing=boss.direction)
        _NS_kenshiro._draw_body(surface, x + float_sway, y + float_bob,
                                 boss.direction, phase, "float")

    def _draw_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_ken_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        # Arah terkunci saat serangan dimulai (lihat
        # _update_attack_anim). Fallback ke arah live.
        facing = getattr(boss, "_ken_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Katana swing - fast decisive strike
        if progress < 0.2:
            # Anticipation - draw back
            t = progress / 0.2
            lunge = -int(t * 4) * boss.direction
            lift = int(t * 3)
            float_bob = int(math.sin(boss.pulse * 0.5) * 4)
        elif progress < 0.4:
            # EXPLOSIVE strike
            t = (progress - 0.2) / 0.2
            t_ease = 1 - (1 - t) ** 2
            lunge = int((-4 + t_ease * 18)) * boss.direction
            lift = int(3 - t_ease * 5)
            float_bob = 0
        else:
            # Recovery back to float
            t = (progress - 0.4) / 0.6
            lunge = int(14 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
            float_bob = int(math.sin(boss.pulse * 0.5) * 4 * t)

        _NS_kenshiro._draw_shadow_float(surface, x + lunge, y + 52, boss.pulse,
                                         intensity=0.9)
        _NS_kenshiro._draw_float_wisps(surface, x + lunge, y + 46, boss.pulse,
                                        intensity=1.2)
        _NS_kenshiro._draw_body(surface, x + lunge, y - lift + float_bob,
                                 boss.direction, boss.pulse, "attack", progress)
        # Slash trail
        _NS_kenshiro._draw_katana_slash(surface, boss, x + lunge,
                                          y - lift + float_bob, progress)

    def _draw_gale_body(surface, boss, x, y, timer, phase):
        """Dragon's Gale - spinning katana."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        spin = progress * math.pi * 10

        float_bob = int(math.sin(progress * math.pi * 2) * -4)
        _NS_kenshiro._draw_shadow_float(surface, x, y + 52, phase, intensity=0.9)
        _NS_kenshiro._draw_float_wisps(surface, x, y + 46, phase, intensity=1.5)
        _NS_kenshiro._draw_body(surface, x, y + float_bob, boss.direction, phase,
                                 "spin", spin_angle=spin)

    def _draw_assault_body(surface, boss, x, y, timer, phase):
        """Forward Assault - dash forward."""
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kenshiro._target_position(boss, x, y)

        if progress < 0.75:
            t = progress / 0.75
            t_ease = 1 - (1 - t) ** 3  # fast dash
            cx = int(x + (tx - x) * t_ease * 0.9)
            cy = int(y + (ty - y) * t_ease * 0.9)
        else:
            t = (progress - 0.75) / 0.25
            cx = int(x + (tx - x) * 0.9)
            cy = int(y + (ty - y) * 0.9)

        float_bob = int(math.sin(phase * 0.5) * 3)
        _NS_kenshiro._draw_shadow_float(surface, cx, cy + 52, phase, intensity=0.8)
        _NS_kenshiro._draw_float_wisps(surface, cx, cy + 46, phase, intensity=1.6,
                                        trail=True, facing=boss.direction)
        # Attack pose (blade forward)
        _NS_kenshiro._draw_body(surface, cx, cy + float_bob, boss.direction, phase,
                                 "attack", attack_progress=0.35)

    def _draw_supremacy_body(surface, boss, x, y, timer, phase):
        """Blade Supremacy - powerful pose while performing multiple slashes."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Multiple attack cycles
        cycle_progress = (progress * 3) % 1.0

        float_bob = int(math.sin(progress * math.pi * 4) * -3)
        _NS_kenshiro._draw_shadow_float(surface, x, y + 52, phase, intensity=1.0)
        _NS_kenshiro._draw_float_wisps(surface, x, y + 46, phase, intensity=1.8)
        _NS_kenshiro._draw_body(surface, x, y + float_bob, boss.direction, phase,
                                 "attack", attack_progress=cycle_progress * 0.5)

    # ============================================================
    # BODY (Humanoid Ronin)
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0,
                    spin_angle=0):
        """Draw ronin body."""
        # Cape/haori flowing behind
        _NS_kenshiro._draw_cape(surface, cx, cy - 8, facing, phase, action)

        # Legs (dangling since floating)
        _NS_kenshiro._draw_legs(surface, cx, cy + 18, facing, phase, action, attack_progress)

        # Robe/kimono lower
        _NS_kenshiro._draw_kimono_lower(surface, cx, cy + 6, facing, phase)

        # Torso (kimono top)
        _NS_kenshiro._draw_torso(surface, cx, cy - 8, facing, phase, action)

        # Back arm (holds scabbard/off-hand)
        _NS_kenshiro._draw_arm_back(surface, cx, cy - 6, facing, phase, action,
                                     attack_progress, spin_angle)

        # Head with hat and hair
        _NS_kenshiro._draw_head(surface, cx, cy - 22, facing, phase, action)

        # Front arm with katana
        _NS_kenshiro._draw_arm_front(surface, cx, cy - 6, facing, phase, action,
                                      attack_progress, spin_angle)

    def _draw_legs(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Legs - dangling in float, positioned in stance for attack."""
        if action in ("idle", "float"):
            # Floating - both legs relaxed dangling with slight sway
            sway = math.sin(phase * 0.6) * 1
            bx = cx - 4 + int(sway)
            by = cy - 1
            _NS_kenshiro._draw_leg_float(surface, bx, by, facing, back=True, phase=phase)
            fx = cx + 4 - int(sway)
            fy = cy
            _NS_kenshiro._draw_leg_float(surface, fx, fy, facing, back=False, phase=phase)
        elif action == "attack" and attack_progress < 0.4:
            # Combat stance - legs planted (temporary landing)
            bx = cx - 5
            by = cy
            _NS_kenshiro._draw_leg(surface, bx, by, facing, back=True)
            fx = cx + 5
            fy = cy
            _NS_kenshiro._draw_leg(surface, fx, fy, facing, back=False)
        elif action == "spin":
            # Both legs together (spinning)
            sway = math.sin(spin_angle * 0.5) * 2 if False else 0
            bx = cx - 3
            by = cy - 1
            _NS_kenshiro._draw_leg_float(surface, bx, by, facing, back=True, phase=phase)
            fx = cx + 3
            fy = cy - 1
            _NS_kenshiro._draw_leg_float(surface, fx, fy, facing, back=False, phase=phase)
        else:
            # Recovery back to float
            bx = cx - 4
            by = cy - 1
            _NS_kenshiro._draw_leg_float(surface, bx, by, facing, back=True, phase=phase)
            fx = cx + 4
            fy = cy - 1
            _NS_kenshiro._draw_leg_float(surface, fx, fy, facing, back=False, phase=phase)

    def _draw_leg_float(surface, cx, cy, facing, back=False, phase=0):
        """Floating leg - relaxed with wisp underneath."""
        # Upper leg (kimono cloth - dark blue)
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                         (cx - 3, cy - 8, 7, 9))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["cloth_darkest"],
                         (cx - 3, cy - 8, 6, 8))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["cloth_dark"],
                         (cx - 2, cy - 8, 4, 7))
        if not back:
            pygame.draw.rect(surface, _NS_kenshiro.PALETTE["cloth_mid"],
                             (cx - 1, cy - 7, 2, 5))

        # Lower leg (dark cloth wrap)
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                         (cx - 2, cy + 1, 5, 7))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["cloth_darkest"],
                         (cx - 2, cy + 1, 4, 6))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["cloth_dark"],
                         (cx - 1, cy + 1, 3, 5))

        # Straw sandal / geta
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                         (cx - 3, cy + 7, 7, 4))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["hat_darkest"],
                         (cx - 3, cy + 7, 6, 3))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["hat_dark"],
                         (cx - 2, cy + 7, 4, 2))
        if not back:
            pygame.draw.rect(surface, _NS_kenshiro.PALETTE["hat_mid"],
                             (cx - 2, cy + 7, 3, 1))

        # Wisp under sandal (floating energy)
        wisp_t = (phase * 0.8 + cx * 0.1) % 1.0
        wy = cy + 11 + int(wisp_t * 6)
        alpha = _NS_kenshiro._alpha(160 * (1 - wisp_t))
        if alpha > 0 and not back:
            _NS_kenshiro._aacircle(surface,
                _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_dark"], alpha),
                (cx, wy), 2)
            _NS_kenshiro._aacircle(surface,
                _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_mid"], alpha),
                (cx, wy), 1)
            pygame.draw.rect(surface,
                _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_hot"], alpha),
                (cx, wy, 1, 1))

    def _draw_leg(surface, cx, cy, facing, back=False):
        """Planted leg (combat stance)."""
        # Thigh
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                         (cx - 3, cy - 8, 7, 9))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["cloth_darkest"],
                         (cx - 3, cy - 8, 6, 8))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["cloth_dark"],
                         (cx - 2, cy - 8, 4, 7))
        if not back:
            pygame.draw.rect(surface, _NS_kenshiro.PALETTE["cloth_mid"],
                             (cx - 1, cy - 7, 2, 5))

        # Lower leg
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                         (cx - 2, cy + 1, 5, 6))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["cloth_darkest"],
                         (cx - 2, cy + 1, 4, 5))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["cloth_dark"],
                         (cx - 1, cy + 1, 3, 4))

        # Sandal
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                         (cx - 4, cy + 6, 9, 5))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["hat_darkest"],
                         (cx - 4, cy + 6, 8, 4))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["hat_dark"],
                         (cx - 3, cy + 6, 6, 3))
        if not back:
            pygame.draw.rect(surface, _NS_kenshiro.PALETTE["hat_mid"],
                             (cx - 3, cy + 6, 5, 1))

    def _draw_kimono_lower(surface, cx, cy, facing, phase):
        """Lower kimono skirt (hakama-like)."""
        sway = math.sin(phase * 0.5) * 1

        # Kimono skirt (wide bottom)
        skirt_pts = [
            (cx - 9, cy - 4),
            (cx + 9, cy - 4),
            (cx + 13, cy + 8),
            (cx + 8 + int(sway), cy + 14),
            (cx - 8 + int(sway), cy + 14),
            (cx - 13, cy + 8),
        ]
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                            [(px + 1, py + 1) for px, py in skirt_pts])
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["cloth_darkest"], skirt_pts)

        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["cloth_dark"], [
            (cx - 8, cy - 3),
            (cx + 8, cy - 3),
            (cx + 12, cy + 7),
            (cx + 7 + int(sway), cy + 13),
            (cx - 7 + int(sway), cy + 13),
            (cx - 12, cy + 7),
        ])

        # Highlight
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["cloth_mid"], [
            (cx - 5, cy - 2),
            (cx + 3, cy - 2),
            (cx + 5, cy + 6),
            (cx - 3, cy + 12),
            (cx - 7, cy + 6),
        ])
        # Bright spot
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["cloth_light"],
                         (cx - 1, cy + 2, 1, 6))

        # Fold lines
        for x_off in (-7, -3, 3, 7):
            pygame.draw.line(surface, _NS_kenshiro.PALETTE["cloth_darkest"],
                             (cx + x_off, cy - 3),
                             (cx + x_off + int(sway * 0.5), cy + 12), 1)

        # OBI (belt) - dark
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                         (cx - 10, cy - 4, 21, 4))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["armor_darkest"],
                         (cx - 10, cy - 4, 20, 4))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["armor_dark"],
                         (cx - 10, cy - 4, 20, 3))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["armor_mid"],
                         (cx - 9, cy - 3, 18, 2))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["armor_light"],
                         (cx - 8, cy - 3, 4, 1))

        # Gold buckle center
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["gold_dark"],
                         (cx - 2, cy - 4, 5, 4))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["gold_mid"],
                         (cx - 1, cy - 3, 3, 2))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["gold_light"],
                         (cx - 1, cy - 3, 2, 1))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["gold_shine"],
                         (cx, cy - 3, 1, 1))

    def _draw_torso(surface, cx, cy, facing, phase, action):
        """Kimono top with white under-layer visible."""
        breath = math.sin(phase * 0.6) * 1

        # Main torso shape
        torso_pts = [
            (cx - 8, cy - 3),
            (cx - 9, cy + 3),
            (cx - 7, cy + 10),
            (cx + 7, cy + 10),
            (cx + 9, cy + 3),
            (cx + 8, cy - 3),
            (cx + 5, cy - 6),
            (cx - 5, cy - 6),
        ]
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                            [(px + 1, py + 1) for px, py in torso_pts])
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["cloth_darkest"], torso_pts)

        # Main kimono
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["cloth_dark"], [
            (cx - 7, cy - 2 + int(breath)),
            (cx - 8, cy + 3),
            (cx - 6, cy + 9),
            (cx + 6, cy + 9),
            (cx + 8, cy + 3),
            (cx + 7, cy - 2 + int(breath)),
            (cx + 4, cy - 5),
            (cx - 4, cy - 5),
        ])

        # Highlight
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["cloth_mid"], [
            (cx - 4, cy - 1 + int(breath)),
            (cx - 6, cy + 3),
            (cx - 3, cy + 8),
            (cx + 4, cy + 8),
            (cx + 6, cy + 3),
            (cx + 4, cy - 1 + int(breath)),
            (cx + 2, cy - 4),
            (cx - 2, cy - 4),
        ])

        # WHITE UNDER-KIMONO (V-collar visible at neck)
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["white_darkest"], [
            (cx - 3, cy - 5),
            (cx + 3, cy - 5),
            (cx + 1, cy + 2),
            (cx - 1, cy + 2),
        ])
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["white_dark"], [
            (cx - 2, cy - 5),
            (cx + 2, cy - 5),
            (cx + 1, cy),
            (cx - 1, cy),
        ])
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["white_mid"],
                         (cx - 1, cy - 4, 2, 3))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["white_light"],
                         (cx, cy - 3, 1, 1))

        # V-collar edges (cloth edge)
        pygame.draw.line(surface, _NS_kenshiro.PALETTE["cloth_darkest"],
                         (cx - 4, cy - 5), (cx - 1, cy + 2), 1)
        pygame.draw.line(surface, _NS_kenshiro.PALETTE["cloth_darkest"],
                         (cx + 4, cy - 5), (cx + 1, cy + 2), 1)

        # Kimono edge highlight (right side/facing)
        pygame.draw.line(surface, _NS_kenshiro.PALETTE["cloth_edge"],
                         (cx + facing * 3, cy - 4), (cx + facing * 2, cy + 8), 1)

        # Fold lines
        pygame.draw.line(surface, _NS_kenshiro.PALETTE["cloth_darkest"],
                         (cx - 5, cy + 2 + int(breath)), (cx - 6, cy + 8), 1)
        pygame.draw.line(surface, _NS_kenshiro.PALETTE["cloth_darkest"],
                         (cx + 5, cy + 2 + int(breath)), (cx + 6, cy + 8), 1)

        # Shoulder pauldron/plate on facing side
        sx = cx + facing * 7
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                         (sx - 2 + 1, cy - 5 + 1, 4, 4))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["armor_darkest"],
                         (sx - 2, cy - 5, 4, 4))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["armor_dark"],
                         (sx - 2, cy - 5, 3, 3))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["armor_mid"],
                         (sx - 1, cy - 5, 2, 2))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["gold_dark"],
                         (sx - 1, cy - 5, 2, 1))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["gold_mid"],
                         (sx - 1, cy - 5, 1, 1))

    def _draw_cape(surface, cx, cy, facing, phase, action):
        """Long haori/cape flowing behind."""
        sway = math.sin(phase * 0.8) * 4
        if action in ("float", "attack"):
            sway += math.sin(phase * 1.5) * 3
        if action == "spin":
            sway += math.sin(phase * 3) * 5

        back_dir = -facing

        # Long dramatic cape
        cape_pts = [
            (cx + back_dir * 3, cy + 2),
            (cx + back_dir * 8, cy + 8 + int(sway * 0.5)),
            (cx + back_dir * 14, cy + 18 + int(sway)),
            (cx + back_dir * 17, cy + 28 + int(sway * 1.3)),
            (cx + back_dir * 15, cy + 38 + int(sway)),
            (cx + back_dir * 8, cy + 42),
            (cx + back_dir * 2, cy + 36),
            (cx, cy + 20),
            (cx + back_dir * 1, cy + 4),
        ]
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                            [(px + 1, py + 1) for px, py in cape_pts])
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["cloth_darkest"], cape_pts)

        # Mid
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["cloth_dark"], [
            (cx + back_dir * 3, cy + 3),
            (cx + back_dir * 6, cy + 8 + int(sway * 0.5)),
            (cx + back_dir * 12, cy + 18 + int(sway)),
            (cx + back_dir * 14, cy + 26 + int(sway)),
            (cx + back_dir * 12, cy + 36),
            (cx + back_dir * 6, cy + 38),
            (cx + back_dir * 2, cy + 32),
            (cx, cy + 20),
            (cx + back_dir * 1, cy + 4),
        ])

        # Fold lines
        for i in range(3):
            fold_x = back_dir * (4 + i * 3)
            pygame.draw.line(surface, _NS_kenshiro.PALETTE["cloth_darkest"],
                             (cx + fold_x, cy + 6 + i * 2 + int(sway * 0.3)),
                             (cx + fold_x + back_dir * 2,
                              cy + 34 + int(sway * 0.5)), 1)

        # Highlight edge
        pygame.draw.line(surface, _NS_kenshiro.PALETTE["cloth_mid"],
                         (cx + back_dir * 1, cy + 6),
                         (cx + back_dir * 3, cy + 32), 2)
        pygame.draw.line(surface, _NS_kenshiro.PALETTE["cloth_light"],
                         (cx, cy + 8), (cx + back_dir * 2, cy + 28), 1)

    def _draw_arm_back(surface, cx, cy, facing, phase, action, attack_progress,
                        spin_angle=0):
        """Back arm - holds scabbard/sheath or off-hand."""
        base_x = cx - facing * 7
        base_y = cy

        if action == "attack":
            if attack_progress < 0.2:
                arm_angle = -0.5
            elif attack_progress < 0.4:
                t = (attack_progress - 0.2) / 0.2
                arm_angle = -0.5 + t * 0.6
            else:
                arm_angle = 0.1
        elif action == "spin":
            arm_angle = -0.3 + math.sin(spin_angle) * 0.2
        else:
            arm_angle = -0.15 + math.sin(phase * 0.6) * 0.08

        elbow_x = base_x - facing * int(3 + math.sin(arm_angle) * 2)
        elbow_y = base_y + int(4 - math.cos(arm_angle) * 2)
        hand_x = elbow_x + facing * int(1 + math.sin(arm_angle + 0.5) * 2)
        hand_y = elbow_y + int(5 - math.cos(arm_angle + 0.5) * 2)

        # Upper arm (kimono sleeve - wide flowing)
        _NS_kenshiro._aaline(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                              (base_x + 1, base_y + 1), (elbow_x + 1, elbow_y + 1), 6)
        _NS_kenshiro._aaline(surface, _NS_kenshiro.PALETTE["cloth_darkest"],
                              (base_x, base_y), (elbow_x, elbow_y), 5)
        _NS_kenshiro._aaline(surface, _NS_kenshiro.PALETTE["cloth_dark"],
                              (base_x, base_y), (elbow_x, elbow_y), 4)
        _NS_kenshiro._aaline(surface, _NS_kenshiro.PALETTE["cloth_mid"],
                              (base_x, base_y - 1), (elbow_x, elbow_y - 1), 2)

        # Forearm (bare skin visible)
        _NS_kenshiro._aaline(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                              (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 4)
        _NS_kenshiro._aaline(surface, _NS_kenshiro.PALETTE["skin_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_kenshiro._aaline(surface, _NS_kenshiro.PALETTE["skin_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 2)

        # Hand
        _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                                (hand_x + 1, hand_y + 1), 3)
        _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["skin_darkest"],
                                (hand_x, hand_y), 3)
        _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["skin_dark"],
                                (hand_x, hand_y), 2)
        _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["skin_mid"],
                                (hand_x - facing, hand_y - 1), 1)

        # SCABBARD (katana sheath) - held in back hand or at waist
        # Draw it at the hip area (thin long shape)
        if action != "spin":
            scabbard_angle = 0.2
            scab_len = 26
            scab_dx = math.cos(scabbard_angle)
            scab_dy = math.sin(scabbard_angle)
            scab_start_x = hand_x
            scab_start_y = hand_y
            scab_end_x = scab_start_x - facing * int(scab_dx * scab_len)
            scab_end_y = scab_start_y + int(scab_dy * scab_len)

            # Scabbard body
            pygame.draw.line(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                             (scab_start_x + 1, scab_start_y + 1),
                             (scab_end_x + 1, scab_end_y + 1), 4)
            pygame.draw.line(surface, _NS_kenshiro.PALETTE["hat_darkest"],
                             (scab_start_x, scab_start_y),
                             (scab_end_x, scab_end_y), 3)
            pygame.draw.line(surface, _NS_kenshiro.PALETTE["hat_dark"],
                             (scab_start_x, scab_start_y),
                             (scab_end_x, scab_end_y), 2)
            pygame.draw.line(surface, _NS_kenshiro.PALETTE["hat_mid"],
                             (scab_start_x, scab_start_y - 1),
                             (scab_end_x, scab_end_y - 1), 1)

            # Gold tip on scabbard
            _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["gold_mid"],
                                    (scab_end_x, scab_end_y), 2)
            _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["gold_light"],
                                    (scab_end_x, scab_end_y), 1)

    def _draw_arm_front(surface, cx, cy, facing, phase, action, attack_progress,
                         spin_angle=0):
        """Front arm holds katana."""
        base_x = cx + facing * 7
        base_y = cy

        if action == "attack":
            if attack_progress < 0.2:
                # Draw back
                t = attack_progress / 0.2
                arm_angle = -0.3 - t * 0.8
            elif attack_progress < 0.4:
                # Explosive strike
                t = (attack_progress - 0.2) / 0.2
                t_ease = 1 - (1 - t) ** 2
                arm_angle = -1.1 + t_ease * 2.6
            else:
                t = (attack_progress - 0.4) / 0.6
                arm_angle = 1.5 - t * 1.2
        elif action == "spin":
            arm_angle = spin_angle * 0.3
        else:
            arm_angle = 0.3 + math.sin(phase * 0.6 + 0.5) * 0.08

        elbow_x = base_x + facing * int(4 + math.cos(arm_angle) * 3)
        elbow_y = base_y + int(3 + math.sin(arm_angle) * 3)
        hand_x = elbow_x + facing * int(5 + math.cos(arm_angle + 0.3) * 4)
        hand_y = elbow_y + int(4 + math.sin(arm_angle + 0.3) * 5)

        # Upper arm (kimono sleeve)
        _NS_kenshiro._aaline(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                              (base_x + 1, base_y + 1), (elbow_x + 1, elbow_y + 1), 6)
        _NS_kenshiro._aaline(surface, _NS_kenshiro.PALETTE["cloth_darkest"],
                              (base_x, base_y), (elbow_x, elbow_y), 5)
        _NS_kenshiro._aaline(surface, _NS_kenshiro.PALETTE["cloth_dark"],
                              (base_x, base_y), (elbow_x, elbow_y), 4)
        _NS_kenshiro._aaline(surface, _NS_kenshiro.PALETTE["cloth_mid"],
                              (base_x, base_y - 1), (elbow_x, elbow_y - 1), 2)
        _NS_kenshiro._aaline(surface, _NS_kenshiro.PALETTE["cloth_light"],
                              (base_x, base_y - 2), (elbow_x, elbow_y - 2), 1)

        # Forearm bare skin
        _NS_kenshiro._aaline(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                              (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 4)
        _NS_kenshiro._aaline(surface, _NS_kenshiro.PALETTE["skin_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_kenshiro._aaline(surface, _NS_kenshiro.PALETTE["skin_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 2)
        _NS_kenshiro._aaline(surface, _NS_kenshiro.PALETTE["skin_mid"],
                              (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)

        # Wrist wrap
        mid_x = int((elbow_x + hand_x) / 2)
        mid_y = int((elbow_y + hand_y) / 2)
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["armor_darkest"],
                         (mid_x - 1, mid_y - 1, 3, 3))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["armor_dark"],
                         (mid_x, mid_y - 1, 2, 2))

        # Fist gripping katana handle
        _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                                (hand_x + 1, hand_y + 1), 4)
        _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["skin_darkest"],
                                (hand_x, hand_y), 4)
        _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["skin_dark"],
                                (hand_x, hand_y), 3)
        _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["skin_mid"],
                                (hand_x - facing, hand_y - 1), 2)
        _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["skin_light"],
                                (hand_x - facing, hand_y - 1), 1)

        # KATANA
        if action == "attack":
            if attack_progress < 0.2:
                blade_angle = (-math.pi * 0.2 - (attack_progress / 0.2) * 0.6) * facing
            elif attack_progress < 0.4:
                t = (attack_progress - 0.2) / 0.2
                t_ease = 1 - (1 - t) ** 2
                start_a = -math.pi * 0.8 * facing
                end_a = math.pi * 0.7 * facing
                blade_angle = start_a + (end_a - start_a) * t_ease
            else:
                blade_angle = math.pi * 0.5 * facing
        elif action == "spin":
            blade_angle = spin_angle * facing
        else:
            blade_angle = math.pi * 0.15 * facing + math.sin(phase * 0.5) * 0.05

        _NS_kenshiro._draw_katana(surface, hand_x, hand_y, facing, blade_angle,
                                    phase, action)

    def _draw_katana(surface, cx, cy, facing, angle, phase, action):
        """Long straight katana with slight curve."""
        blade_len = 34
        dx = math.cos(angle)
        dy = math.sin(angle)

        # Blade tip
        tip_x = cx + int(dx * blade_len) * facing
        tip_y = cy + int(dy * blade_len)

        # Perpendicular
        perp_x = -dy
        perp_y = dx

        # Handle end (tsuka goes opposite direction from blade)
        handle_len = 8
        handle_end_x = cx - int(dx * handle_len) * facing
        handle_end_y = cy - int(dy * handle_len)

        # TSUBA (guard) - small circle at grip
        _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                                (cx + 1, cy + 1), 4)
        _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["armor_darkest"],
                                (cx, cy), 4)
        _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["armor_dark"],
                                (cx, cy), 3)
        _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["gold_dark"],
                                (cx, cy), 2)
        _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["gold_mid"],
                                (cx, cy), 1)

        # TSUKA (handle) - dark wrap
        pygame.draw.line(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                         (cx + 1, cy + 1), (handle_end_x + 1, handle_end_y + 1), 5)
        pygame.draw.line(surface, _NS_kenshiro.PALETTE["armor_darkest"],
                         (cx, cy), (handle_end_x, handle_end_y), 4)
        pygame.draw.line(surface, _NS_kenshiro.PALETTE["armor_dark"],
                         (cx, cy), (handle_end_x, handle_end_y), 3)

        # Handle wrap pattern
        for i in range(3):
            wrap_t = 0.3 + i * 0.25
            wrap_x = int(cx + (handle_end_x - cx) * wrap_t)
            wrap_y = int(cy + (handle_end_y - cy) * wrap_t)
            pygame.draw.rect(surface, _NS_kenshiro.PALETTE["gold_dark"],
                             (wrap_x - 1, wrap_y - 1, 2, 2))
            pygame.draw.rect(surface, _NS_kenshiro.PALETTE["gold_mid"],
                             (wrap_x, wrap_y, 1, 1))

        # Pommel (kashira)
        _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["armor_darkest"],
                                (handle_end_x, handle_end_y), 2)
        _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["gold_dark"],
                                (handle_end_x, handle_end_y), 1)

        # BLADE (long straight, slight curve)
        # Compute blade edge points along the length
        base_top_x = cx + int(perp_x * 1) * facing
        base_top_y = cy + int(perp_y * 1)
        base_bot_x = cx - int(perp_x * 1) * facing
        base_bot_y = cy - int(perp_y * 1)

        # Slight curve at middle (subtle - katana barely curves)
        mid_top_x = cx + int(dx * blade_len * 0.5) * facing + int(perp_x * 2) * facing
        mid_top_y = cy + int(dy * blade_len * 0.5) + int(perp_y * 2)
        mid_bot_x = cx + int(dx * blade_len * 0.5) * facing - int(perp_x * 2) * facing
        mid_bot_y = cy + int(dy * blade_len * 0.5) - int(perp_y * 2)

        # Blade shape (tapered)
        blade_shape = [
            (base_top_x, base_top_y),
            (mid_top_x, mid_top_y),
            (tip_x, tip_y),
            (mid_bot_x, mid_bot_y),
            (base_bot_x, base_bot_y),
        ]
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in blade_shape])
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["blade_darkest"], blade_shape)

        # Mid
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["blade_dark"], [
            (int((base_top_x + base_bot_x) / 2 + perp_x * 1 * facing),
             int((base_top_y + base_bot_y) / 2 + perp_y * 1)),
            (int(mid_top_x * 0.6 + tip_x * 0.4),
             int(mid_top_y * 0.6 + tip_y * 0.4)),
            (tip_x, tip_y),
            (int(mid_bot_x * 0.6 + tip_x * 0.4),
             int(mid_bot_y * 0.6 + tip_y * 0.4)),
            (int((base_top_x + base_bot_x) / 2 - perp_x * 1 * facing),
             int((base_top_y + base_bot_y) / 2 - perp_y * 1)),
        ])

        # Central bright line (hamon - blade edge)
        pygame.draw.line(surface, _NS_kenshiro.PALETTE["blade_mid"],
                         (cx, cy), (tip_x, tip_y), 2)
        pygame.draw.line(surface, _NS_kenshiro.PALETTE["blade_light"],
                         (cx, cy), (tip_x, tip_y), 1)

        # Bright edges
        pygame.draw.line(surface, _NS_kenshiro.PALETTE["blade_shine"],
                         (base_top_x, base_top_y), (mid_top_x, mid_top_y), 1)
        pygame.draw.line(surface, _NS_kenshiro.PALETTE["blade_shine"],
                         (mid_top_x, mid_top_y), (tip_x, tip_y), 1)

        # Bright tip
        _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["blade_shine"], (tip_x, tip_y), 2)
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["white"], (tip_x, tip_y, 1, 1))

        # Golden energy trailing along blade (subtle idle glow)
        if action in ("attack", "spin"):
            glow_pulse = 1.0
        else:
            glow_pulse = math.sin(phase * 2) * 0.3 + 0.5

        glow_surf = pygame.Surface((100, 100), pygame.SRCALPHA)
        off_x = cx - 50
        off_y = cy - 50
        for pt_i in range(4):
            t = pt_i / 3
            gx = int(cx + (tip_x - cx) * t) - off_x
            gy = int(cy + (tip_y - cy) * t) - off_y
            for r in range(5, 0, -1):
                alpha = _NS_kenshiro._alpha(80 * (5 - r) / 5 * glow_pulse)
                _NS_kenshiro._aacircle(glow_surf,
                    _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_mid"], alpha),
                    (gx, gy), r)
        surface.blit(glow_surf, (off_x, off_y))

    def _draw_head(surface, cx, cy, facing, phase, action):
        """Head with kasa hat + long black hair."""
        # Neck
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                         (cx - 2, cy + 6, 5, 4))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["skin_darkest"],
                         (cx - 2, cy + 6, 4, 4))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["skin_dark"],
                         (cx - 1, cy + 6, 3, 3))

        # Long hair flowing (behind head/shoulders)
        _NS_kenshiro._draw_long_hair(surface, cx, cy + 2, facing, phase)

        # Head shape (partially covered by hat)
        head_pts = [
            (cx - 5, cy - 1),
            (cx - 6, cy + 2),
            (cx - 4, cy + 6),
            (cx + 4, cy + 6),
            (cx + 6, cy + 2),
            (cx + 5, cy - 1),
        ]
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                            [(px + 1, py + 1) for px, py in head_pts])
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["skin_darkest"], head_pts)

        # Face mid tone
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["skin_dark"], [
            (cx - 4, cy),
            (cx - 5, cy + 2),
            (cx - 3, cy + 5),
            (cx + 3, cy + 5),
            (cx + 5, cy + 2),
            (cx + 4, cy),
        ])

        # Face light (highlight on facing side)
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["skin_mid"], [
            (cx + facing * 1, cy),
            (cx + facing * 4, cy + 1),
            (cx + facing * 3, cy + 4),
            (cx + facing * 1, cy + 3),
        ])
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["skin_light"],
                         (cx + facing * 3, cy + 1, 1, 1))

        # Shadow under hat brim (dark strip across upper face)
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                         (cx - 5, cy, 11, 2))

        # Just eye slits visible under hat shadow
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_off in (-2, 2):
            ex = cx + eye_off
            ey = cy + 1
            # Small amber glow through darkness
            for r in range(2, 0, -1):
                alpha = _NS_kenshiro._alpha(180 * (2 - r) / 2 * eye_pulse)
                _NS_kenshiro._aacircle(surface,
                    _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["eye_mid"], alpha),
                    (ex, ey), r)
            pygame.draw.rect(surface, _NS_kenshiro.PALETTE["eye_light"],
                             (ex, ey, 1, 1))

        # Mouth (subtle grim line)
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["skin_darkest"],
                         (cx - 2, cy + 4, 4, 1))

        # KASA HAT (straw hat)
        _NS_kenshiro._draw_kasa_hat(surface, cx, cy - 3, facing, phase)

    def _draw_long_hair(surface, cx, cy, facing, phase):
        """Long black hair flowing down behind."""
        sway = math.sin(phase * 0.7) * 1

        # Hair mass behind head (flowing to shoulders)
        hair_pts = [
            (cx - 6, cy - 2),
            (cx - 8, cy + 3),
            (cx - 9 + int(sway), cy + 10),
            (cx - 7 + int(sway), cy + 16),
            (cx - 3, cy + 15),
            (cx - 3, cy + 5),
        ]
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                            [(px + 1, py + 1) for px, py in hair_pts])
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["hair_darkest"], hair_pts)

        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["hair_dark"], [
            (cx - 5, cy - 1),
            (cx - 7, cy + 3),
            (cx - 8 + int(sway), cy + 9),
            (cx - 6 + int(sway), cy + 14),
            (cx - 4, cy + 13),
            (cx - 3, cy + 5),
        ])

        # Highlights (strand lines)
        pygame.draw.line(surface, _NS_kenshiro.PALETTE["hair_mid"],
                         (cx - 6, cy + 2), (cx - 7 + int(sway), cy + 13), 1)
        pygame.draw.line(surface, _NS_kenshiro.PALETTE["hair_mid"],
                         (cx - 4, cy + 4), (cx - 5 + int(sway), cy + 12), 1)

        # Hair on other side (small, mostly hidden by hat)
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["hair_darkest"],
                         (cx + 4, cy + 3, 2, 8))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["hair_dark"],
                         (cx + 4, cy + 3, 1, 7))

    def _draw_kasa_hat(surface, cx, cy, facing, phase):
        """Kasa - traditional straw hat (wide cone)."""
        # Wide brim shape (conical from top view = ellipse from side)
        brim_pts = [
            (cx - 15, cy),
            (cx - 12, cy - 3),
            (cx - 6, cy - 5),
            (cx + 6, cy - 5),
            (cx + 12, cy - 3),
            (cx + 15, cy),
            (cx + 14, cy + 2),
            (cx + 8, cy + 3),
            (cx - 8, cy + 3),
            (cx - 14, cy + 2),
        ]
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["shadow_deep"],
                            [(px + 1, py + 2) for px, py in brim_pts])
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["hat_darkest"], brim_pts)

        # Brim mid tone
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["hat_dark"], [
            (cx - 14, cy),
            (cx - 11, cy - 2),
            (cx - 5, cy - 4),
            (cx + 5, cy - 4),
            (cx + 11, cy - 2),
            (cx + 14, cy),
            (cx + 13, cy + 1),
            (cx + 7, cy + 2),
            (cx - 7, cy + 2),
            (cx - 13, cy + 1),
        ])

        # Brim highlight (facing side)
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["hat_mid"], [
            (cx + facing * 3, cy - 4),
            (cx + facing * 10, cy - 2),
            (cx + facing * 13, cy),
            (cx + facing * 11, cy + 1),
            (cx + facing * 5, cy + 1),
        ])
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["hat_light"], [
            (cx + facing * 5, cy - 3),
            (cx + facing * 9, cy - 2),
            (cx + facing * 11, cy),
            (cx + facing * 8, cy),
        ])
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["hat_shine"],
                         (cx + facing * 8, cy - 1, 2, 1))

        # Radial straw lines on brim
        for i in range(-3, 4):
            spoke_x_end = cx + i * 4
            pygame.draw.line(surface, _NS_kenshiro.PALETTE["hat_darkest"],
                             (cx, cy - 1),
                             (spoke_x_end, cy - 4 if abs(i) < 3 else cy - 2), 1)

        # Top cone (pointed peak)
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["shadow_deep"], [
            (cx + 1, cy - 8 + 1),
            (cx - 5 + 1, cy - 3 + 1),
            (cx + 5 + 1, cy - 3 + 1),
        ])
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["hat_darkest"], [
            (cx, cy - 8),
            (cx - 5, cy - 3),
            (cx + 5, cy - 3),
        ])
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["hat_dark"], [
            (cx, cy - 8),
            (cx - 4, cy - 3),
            (cx + 4, cy - 3),
        ])
        _NS_kenshiro._poly(surface, _NS_kenshiro.PALETTE["hat_mid"], [
            (cx, cy - 8),
            (cx + facing * 3, cy - 3),
            (cx + facing * 1, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["hat_light"],
                         (cx, cy - 8, 1, 3))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["hat_shine"],
                         (cx, cy - 8, 1, 1))

        # Rope/string tie
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["hair_darkest"],
                         (cx - 4, cy - 2, 2, 1))
        pygame.draw.rect(surface, _NS_kenshiro.PALETTE["hair_darkest"],
                         (cx + 3, cy - 2, 2, 1))

    # ============================================================
    # KATANA SLASH TRAIL
    # ============================================================
    def _draw_katana_slash(surface, boss, cx, cy, progress):
        """Golden crescent slash trail."""
        if progress < 0.2 or progress > 0.55:
            return

        facing = boss.direction
        if progress < 0.4:
            swing_t = (progress - 0.2) / 0.2
        else:
            swing_t = 1.0
        swing_t = max(0.0, min(1.0, swing_t))

        fade = 1.0 if progress <= 0.4 else max(0.0, 1 - (progress - 0.4) / 0.15)

        slash_cx = cx + facing * 28
        slash_cy = cy - 6

        slash_surf = pygame.Surface((200, 200), pygame.SRCALPHA)
        center = (100, 100)

        start_angle = -math.pi * 0.8
        end_angle = math.pi * 0.7

        radius = 42

        # Trail ghosts
        trail_steps = 12
        current_a = start_angle + (end_angle - start_angle) * swing_t

        for step in range(trail_steps):
            step_t = step / trail_steps
            trail_progress = max(0.0, swing_t - step_t * 0.35)
            trail_a = start_angle + (end_angle - start_angle) * trail_progress

            fade_step = (1 - step_t) * fade
            alpha_step = _NS_kenshiro._alpha(240 * fade_step)
            if alpha_step <= 0:
                continue

            arc_pts = []
            arc_span = 0.15
            for i in range(7):
                a = trail_a - arc_span + (arc_span * 2) * i / 6
                r_var = radius + math.sin(step + i) * 2
                px = center[0] + int(math.cos(a) * r_var) * facing
                py = center[1] + int(math.sin(a) * r_var)
                arc_pts.append((px, py))

            layer_thick = max(2, int(10 * fade_step))
            for layer_i, (thick_mult, color, a_mult) in enumerate([
                (1.3, _NS_kenshiro.PALETTE["energy_darkest"], 0.5),
                (1.1, _NS_kenshiro.PALETTE["energy_dark"], 0.7),
                (0.85, _NS_kenshiro.PALETTE["energy_mid"], 0.9),
                (0.6, _NS_kenshiro.PALETTE["energy_light"], 1.0),
                (0.4, _NS_kenshiro.PALETTE["energy_hot"], 1.0),
            ]):
                thick = max(1, int(layer_thick * thick_mult))
                a = _NS_kenshiro._alpha(alpha_step * a_mult)
                if a <= 0:
                    continue
                for i in range(len(arc_pts) - 1):
                    pygame.draw.line(slash_surf,
                                     _NS_kenshiro._rgba(color, a),
                                     arc_pts[i], arc_pts[i + 1], thick)

        # Leading edge
        if swing_t > 0.05:
            leading_pts = []
            arc_span_lead = 0.5
            for i in range(12):
                a = current_a - arc_span_lead + (arc_span_lead * 2) * i / 11
                px = center[0] + int(math.cos(a) * radius) * facing
                py = center[1] + int(math.sin(a) * radius)
                leading_pts.append((px, py))

            for thick, color in [
                (10, _NS_kenshiro.PALETTE["energy_darkest"]),
                (8, _NS_kenshiro.PALETTE["energy_dark"]),
                (6, _NS_kenshiro.PALETTE["energy_mid"]),
                (4, _NS_kenshiro.PALETTE["energy_light"]),
                (2, _NS_kenshiro.PALETTE["energy_hot"]),
                (1, _NS_kenshiro.PALETTE["energy_shine"]),
            ]:
                a = _NS_kenshiro._alpha(255 * fade)
                if a <= 0:
                    continue
                for i in range(len(leading_pts) - 1):
                    pygame.draw.line(slash_surf,
                                     _NS_kenshiro._rgba(color, a),
                                     leading_pts[i], leading_pts[i + 1], thick)

        # Sparkles
        for i in range(15):
            drop_angle = start_angle + (end_angle - start_angle) * (i / 15) * swing_t
            drop_r = radius + int(math.sin(swing_t * 8 + i) * 10) + 6
            dx = center[0] + int(math.cos(drop_angle) * drop_r) * facing
            dy = center[1] + int(math.sin(drop_angle) * drop_r)
            drop_a = _NS_kenshiro._alpha(230 * fade * (i / 15))
            if drop_a > 0:
                pygame.draw.rect(slash_surf,
                    _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_light"], drop_a),
                    (dx, dy, 2, 2))
                pygame.draw.rect(slash_surf,
                    _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_shine"], drop_a),
                    (dx, dy, 1, 1))

        surface.blit(slash_surf, (slash_cx - 100, slash_cy - 100))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow_float(surface, x, y, phase, intensity=1.0):
        """Shadow that pulses with float height."""
        float_offset = math.sin(phase * 0.5) * 6
        scale = 1.0 - (float_offset + 6) / 24
        scale = max(0.55, min(1.0, scale))

        w = int(110 * scale * intensity)
        h = int(26 * scale)
        shadow = pygame.Surface((w + 20, h + 8), pygame.SRCALPHA)
        for radius in range(int(13 * scale), 0, -1):
            alpha = max(0, int((13 * scale - radius) * 16 * intensity))
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, (h + 8) // 2 - radius,
                                 w + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow,
            _NS_kenshiro._rgba((10, 5, 3), int(190 * intensity)),
            (5, (h + 8) // 2 - h // 2, w + 10, h))
        surface.blit(shadow, (x - (w + 20) // 2, y - (h + 8) // 2))

    def _draw_float_wisps(surface, cx, cy, phase, intensity=1.0, trail=False, facing=1):
        """Golden wisps rising."""
        for i in range(int(10 * intensity)):
            t = (phase * 0.6 + i * 0.15) % 1.0
            offset_x = int(math.sin(phase * 0.8 + i) * 12)
            sx = cx + offset_x + (i - 5) * 3
            sy = cy - int(t * 42)
            alpha = _NS_kenshiro._alpha(220 * (1 - t) * intensity)
            if alpha <= 0:
                continue
            _NS_kenshiro._aacircle(surface,
                _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_darkest"], alpha),
                (sx, sy), 3)
            _NS_kenshiro._aacircle(surface,
                _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_dark"], alpha),
                (sx, sy - 1), 2)
            _NS_kenshiro._aacircle(surface,
                _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_mid"], alpha),
                (sx, sy - 1), 1)
            pygame.draw.rect(surface,
                _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_light"], alpha),
                (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_hot"], alpha),
                (sx, sy - 2, 1, 1))

        # Spiraling sparkles
        for i in range(int(6 * intensity)):
            angle = phase * 1.5 + i * math.pi / 3
            radius = 20 + int(math.sin(phase + i) * 4)
            sx = cx + int(math.cos(angle) * radius)
            sy = cy - 10 + int(math.sin(angle) * radius * 0.4)
            alpha = _NS_kenshiro._alpha(240 * intensity)
            pygame.draw.rect(surface,
                _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_light"], alpha),
                (sx, sy, 2, 2))
            pygame.draw.rect(surface,
                _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_hot"], alpha),
                (sx, sy, 1, 1))
            pygame.draw.rect(surface,
                _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["white"], alpha),
                (sx, sy, 1, 1))

        # Trail
        if trail:
            for i in range(7):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + 4 + int(math.sin(phase + i) * 2)
                alpha = _NS_kenshiro._alpha(200 - i * 26)
                if alpha <= 0:
                    continue
                _NS_kenshiro._aacircle(surface,
                    _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_darkest"], alpha),
                    (sx, sy), max(1, 6 - i))
                _NS_kenshiro._aacircle(surface,
                    _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_dark"], alpha),
                    (sx, sy), max(1, 5 - i))
                _NS_kenshiro._aacircle(surface,
                    _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_mid"], alpha),
                    (sx, sy), max(1, 3 - i))
                pygame.draw.rect(surface,
                    _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_light"], alpha),
                    (sx, sy - 1, 2, 2))
                pygame.draw.rect(surface,
                    _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_hot"], alpha),
                    (sx, sy - 1, 1, 1))

    def _draw_gold_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(90, 5, -4):
            alpha = _NS_kenshiro._alpha((90 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_kenshiro._aacircle(aura,
                    _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_darkest"], alpha),
                    (100, 90), radius)
        for radius in range(55, 5, -3):
            alpha = _NS_kenshiro._alpha((55 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_kenshiro._aacircle(aura,
                    _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_dark"], alpha),
                    (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))

        # Floating gold sparkles
        for i in range(14):
            angle = phase * 0.4 + i * math.pi / 7
            r = 36 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * r)
            sy = y - 5 + int(math.sin(angle) * r * 0.5)
            pygame.draw.rect(surface, _NS_kenshiro.PALETTE["energy_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kenshiro.PALETTE["energy_hot"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((150, 48), pygame.SRCALPHA)
        pygame.draw.ellipse(ring,
            _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_darkest"], 200),
            (5, 15, 140, 24), 3)
        pygame.draw.ellipse(ring,
            _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_dark"], 220),
            (14, 18, 122, 20), 2)
        pygame.draw.ellipse(ring,
            _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_mid"], 180),
            (30, 22, 90, 12), 1)

        # Rune spokes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 75 + int(math.cos(angle) * 46)
            y1 = 27 + int(math.sin(angle) * 9)
            x2 = 75 + int(math.cos(angle) * 68)
            y2 = 27 + int(math.sin(angle) * 13)
            pygame.draw.line(ring,
                _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_light"], 220),
                (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_hot"],
                                    _NS_kenshiro._alpha(160 * pulse)),
                (14, 11, 122, 32), 1)
        surface.blit(ring, (x - 75, y - 24))

    # ============================================================
    # SKILL Q: SWIFT SLASH
    # ============================================================
    def _draw_swiftslash_fg(surface, boss, x, y, timer, phase):
        """Big golden crescent slash."""
        facing = boss.direction
        duration = 30
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.15:
            # Charge glow at hand
            t = progress / 0.15
            charge_x = x + facing * 20
            charge_y = y - 10
            cr = int(4 + t * 6)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_kenshiro._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_kenshiro._aacircle(surface,
                    _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_darkest"], alpha),
                    (charge_x, charge_y), r)
            _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["energy_mid"],
                                    (charge_x, charge_y), max(1, cr - 2))
            _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["energy_hot"],
                                    (charge_x, charge_y), max(1, cr - 4))
        elif progress < 0.55:
            # BIG SLASH ARC
            t = (progress - 0.15) / 0.4
            swing_t = t
            fade = 1.0

            slash_cx = x + facing * 45
            slash_cy = y - 6

            slash_surf = pygame.Surface((240, 240), pygame.SRCALPHA)
            center = (120, 120)

            start_angle = -math.pi * 0.85
            end_angle = math.pi * 0.85
            radius = 55

            current_a = start_angle + (end_angle - start_angle) * swing_t

            # Trail
            for step in range(14):
                step_t = step / 14
                trail_progress = max(0.0, swing_t - step_t * 0.35)
                trail_a = start_angle + (end_angle - start_angle) * trail_progress

                fade_step = (1 - step_t) * fade
                alpha_step = _NS_kenshiro._alpha(240 * fade_step)
                if alpha_step <= 0:
                    continue

                arc_pts = []
                arc_span = 0.15
                for i in range(7):
                    a = trail_a - arc_span + (arc_span * 2) * i / 6
                    r_var = radius + math.sin(step + i) * 2
                    px = center[0] + int(math.cos(a) * r_var) * facing
                    py = center[1] + int(math.sin(a) * r_var)
                    arc_pts.append((px, py))

                layer_thick = max(3, int(14 * fade_step))
                for layer_i, (thick_mult, color, a_mult) in enumerate([
                    (1.3, _NS_kenshiro.PALETTE["energy_darkest"], 0.5),
                    (1.1, _NS_kenshiro.PALETTE["energy_dark"], 0.7),
                    (0.85, _NS_kenshiro.PALETTE["energy_mid"], 0.9),
                    (0.6, _NS_kenshiro.PALETTE["energy_light"], 1.0),
                    (0.4, _NS_kenshiro.PALETTE["energy_hot"], 1.0),
                ]):
                    thick = max(1, int(layer_thick * thick_mult))
                    a = _NS_kenshiro._alpha(alpha_step * a_mult)
                    if a <= 0:
                        continue
                    for i in range(len(arc_pts) - 1):
                        pygame.draw.line(slash_surf,
                                         _NS_kenshiro._rgba(color, a),
                                         arc_pts[i], arc_pts[i + 1], thick)

            # Leading edge super bright
            if swing_t > 0.05:
                leading_pts = []
                arc_span_lead = 0.55
                for i in range(12):
                    a = current_a - arc_span_lead + (arc_span_lead * 2) * i / 11
                    px = center[0] + int(math.cos(a) * radius) * facing
                    py = center[1] + int(math.sin(a) * radius)
                    leading_pts.append((px, py))

                for thick, color in [
                    (14, _NS_kenshiro.PALETTE["energy_darkest"]),
                    (11, _NS_kenshiro.PALETTE["energy_dark"]),
                    (8, _NS_kenshiro.PALETTE["energy_mid"]),
                    (5, _NS_kenshiro.PALETTE["energy_light"]),
                    (3, _NS_kenshiro.PALETTE["energy_hot"]),
                    (2, _NS_kenshiro.PALETTE["energy_shine"]),
                    (1, _NS_kenshiro.PALETTE["white"]),
                ]:
                    for i in range(len(leading_pts) - 1):
                        pygame.draw.line(slash_surf,
                                         _NS_kenshiro._rgba(color, 255),
                                         leading_pts[i], leading_pts[i + 1], thick)

            # Sparkles
            for i in range(20):
                drop_angle = start_angle + (end_angle - start_angle) * (i / 20) * swing_t
                drop_r = radius + int(math.sin(swing_t * 8 + i) * 12) + 8
                dx = center[0] + int(math.cos(drop_angle) * drop_r) * facing
                dy = center[1] + int(math.sin(drop_angle) * drop_r)
                drop_a = _NS_kenshiro._alpha(240 * (i / 20))
                if drop_a > 0:
                    pygame.draw.rect(slash_surf,
                        _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_light"], drop_a),
                        (dx, dy, 3, 3))
                    pygame.draw.rect(slash_surf,
                        _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_shine"], drop_a),
                        (dx, dy, 1, 1))

            surface.blit(slash_surf, (slash_cx - 120, slash_cy - 120))

    # ============================================================
    # SKILL W: FORWARD ASSAULT
    # ============================================================
    def _draw_assault_ground(surface, boss, x, y, timer, phase):
        """Line path from origin to target."""
        tx, ty = _NS_kenshiro._target_position(boss, x, y)
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress > 0.75:
            # Landing burst at target
            t = (progress - 0.75) / 0.25
            end_x = int(x + (tx - x) * 0.9)
            end_y = int(y + (ty - y) * 0.9)
            r = int(35 * t)
            alpha = _NS_kenshiro._alpha(240 * (1 - t))
            pygame.draw.ellipse(surface,
                _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_darkest"], alpha),
                (end_x - r, end_y + 42 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_hot"], alpha),
                (end_x - r + 4, end_y + 42 - r // 3 + 3,
                 r * 2 - 8, r * 2 // 3 - 6), 1)

    def _draw_assault_fg(surface, boss, x, y, timer, phase):
        """Dash line + trail."""
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kenshiro._target_position(boss, x, y)
        facing = boss.direction

        if progress < 0.75:
            t = progress / 0.75
            t_ease = 1 - (1 - t) ** 3

            # Golden dash line from start to current position
            end_x = int(x + (tx - x) * t_ease * 0.9)
            end_y = int(y + (ty - y) * t_ease * 0.9)

            # Multi-layer line (motion)
            for thick, color, a_mult in [
                (10, _NS_kenshiro.PALETTE["energy_darkest"], 0.4),
                (7, _NS_kenshiro.PALETTE["energy_dark"], 0.6),
                (5, _NS_kenshiro.PALETTE["energy_mid"], 0.8),
                (3, _NS_kenshiro.PALETTE["energy_light"], 1.0),
                (2, _NS_kenshiro.PALETTE["energy_hot"], 1.0),
                (1, _NS_kenshiro.PALETTE["energy_shine"], 1.0),
            ]:
                alpha = _NS_kenshiro._alpha(240 * a_mult * (1 - t * 0.3))
                pygame.draw.line(surface,
                    _NS_kenshiro._rgba(color, alpha),
                    (x + facing * 15, y - 6),
                    (end_x, end_y), thick)

            # Arrow tip at leading edge
            for r in range(8, 0, -1):
                alpha = _NS_kenshiro._alpha(200 * (8 - r) / 8)
                _NS_kenshiro._aacircle(surface,
                    _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_light"], alpha),
                    (end_x, end_y), r)
            _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["energy_hot"],
                                    (end_x, end_y), 3)
            _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["white"],
                                    (end_x, end_y), 1)

    # ============================================================
    # SKILL E: DRAGON'S GALE (spin)
    # ============================================================
    def _draw_gale_ground(surface, boss, x, y, timer, phase):
        """Expanding ground circle."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(48 + math.sin(phase * 3) * 4)
        alpha = _NS_kenshiro._alpha(220 * (1 - progress * 0.4))
        pygame.draw.ellipse(surface,
            _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_darkest"], alpha),
            (x - r, y + 44 - r // 3, r * 2, r * 2 // 3), 4)
        pygame.draw.ellipse(surface,
            _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_dark"], alpha),
            (x - r + 4, y + 44 - r // 3 + 3,
             r * 2 - 8, r * 2 // 3 - 6), 3)
        pygame.draw.ellipse(surface,
            _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_hot"], alpha),
            (x - r + 10, y + 44 - r // 3 + 6,
             r * 2 - 20, r * 2 // 3 - 12), 1)

    def _draw_gale_fg(surface, boss, x, y, timer, phase):
        """Multiple golden crescent arcs spinning around."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        spin = progress * math.pi * 12

        slash_surf = pygame.Surface((260, 260), pygame.SRCALPHA)
        center = (130, 130)
        radius = 60

        # 4 rotating arcs
        for arm_i in range(4):
            arm_start = spin + arm_i * (math.pi / 2)
            arc_pts = []
            steps = 20
            arc_span = math.pi * 0.5
            for i in range(steps + 1):
                a = arm_start + arc_span * i / steps
                px = center[0] + int(math.cos(a) * radius)
                py = center[1] + int(math.sin(a) * radius * 0.85)
                arc_pts.append((px, py))

            for layer_i, (r_off, thick, color, a_mult) in enumerate([
                (4, 10, _NS_kenshiro.PALETTE["energy_darkest"], 0.6),
                (2, 8, _NS_kenshiro.PALETTE["energy_dark"], 0.8),
                (0, 6, _NS_kenshiro.PALETTE["energy_mid"], 1.0),
                (-1, 4, _NS_kenshiro.PALETTE["energy_light"], 1.0),
                (-2, 2, _NS_kenshiro.PALETTE["energy_hot"], 1.0),
            ]):
                for k in range(len(arc_pts) - 1):
                    fade_k = 1 - (k / len(arc_pts))
                    alpha_val = _NS_kenshiro._alpha(240 * a_mult * fade_k)
                    if alpha_val <= 0:
                        continue
                    pygame.draw.line(slash_surf,
                                     _NS_kenshiro._rgba(color, alpha_val),
                                     arc_pts[k], arc_pts[k + 1], thick)

            # Bright tip
            if arc_pts:
                tip = arc_pts[-1]
                pygame.draw.rect(slash_surf,
                                 _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_shine"], 255),
                                 (tip[0], tip[1], 3, 3))
                pygame.draw.rect(slash_surf,
                                 _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["white"], 255),
                                 (tip[0], tip[1], 2, 2))

        # Sparkles flying out
        for i in range(24):
            angle = spin * 0.5 + i * math.pi / 12
            r_p = radius + int(math.sin(phase + i) * 12) - 5
            px = center[0] + int(math.cos(angle) * r_p)
            py = center[1] + int(math.sin(angle) * r_p * 0.85)
            alpha = _NS_kenshiro._alpha(230)
            pygame.draw.rect(slash_surf,
                _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_light"], alpha),
                (px, py, 2, 2))
            pygame.draw.rect(slash_surf,
                _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_shine"], alpha),
                (px, py, 1, 1))

        surface.blit(slash_surf, (x - 130, y - 130))

    # ============================================================
    # SKILL R: BLADE SUPREMACY (X-cross execute)
    # ============================================================
    def _draw_supremacy_ground(surface, boss, x, y, timer, phase):
        """Radial ground marker."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(55 + math.sin(phase * 2) * 4)
        alpha = _NS_kenshiro._alpha(230 * (1 - progress * 0.3))
        pygame.draw.ellipse(surface,
            _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_darkest"], alpha),
            (x - r, y + 44 - r // 3, r * 2, r * 2 // 3), 4)
        pygame.draw.ellipse(surface,
            _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_hot"], alpha),
            (x - r + 5, y + 44 - r // 3 + 4,
             r * 2 - 10, r * 2 // 3 - 8), 2)

        # Radial spikes on ground
        for i in range(12):
            angle = i * math.pi / 6 + phase * 0.3
            spike_len = 60 + int(math.sin(phase * 2 + i) * 8)
            sx = x + int(math.cos(angle) * spike_len)
            sy = y + 44 + int(math.sin(angle) * spike_len * 0.4)
            pygame.draw.line(surface,
                _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_light"], alpha),
                (x, y + 44), (sx, sy), 2)
            pygame.draw.rect(surface,
                _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_shine"], alpha),
                (sx, sy, 2, 2))

    def _draw_supremacy_fg(surface, boss, x, y, timer, phase):
        """Multiple crossing slashes forming X pattern."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        # 3 phases: charge, multi-slash, X finish
        if progress < 0.25:
            # Charge - big golden aura at katana
            t = progress / 0.25
            charge_x = x + facing * 25
            charge_y = y - 8
            cr = int(6 + t * 12)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_kenshiro._alpha(220 * (cr + 6 - r) / (cr + 6))
                _NS_kenshiro._aacircle(surface,
                    _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_darkest"], alpha),
                    (charge_x, charge_y), r)
            for r in range(cr, 0, -1):
                alpha = _NS_kenshiro._alpha(240 * (cr - r + 1) / cr)
                _NS_kenshiro._aacircle(surface,
                    _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_mid"], alpha),
                    (charge_x, charge_y), r)
            _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["energy_light"],
                                    (charge_x, charge_y), max(1, cr - 3))
            _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["energy_shine"],
                                    (charge_x, charge_y), max(1, cr - 5))
            pygame.draw.rect(surface, _NS_kenshiro.PALETTE["white"],
                             (charge_x, charge_y, 1, 1))

            # Sparks
            for i in range(8):
                angle = phase * 5 + i * math.pi / 4
                sx = charge_x + int(math.cos(angle) * (cr + 4))
                sy = charge_y + int(math.sin(angle) * (cr + 4))
                pygame.draw.rect(surface, _NS_kenshiro.PALETTE["energy_hot"], (sx, sy, 2, 2))

        elif progress < 0.75:
            # Multi-slash flurry - 5 quick slashes appear
            t = (progress - 0.25) / 0.5

            # Draw multiple crescents overlapping
            slash_cx = x + facing * 30
            slash_cy = y - 6

            num_slashes = 5
            for slash_i in range(num_slashes):
                slash_delay = slash_i * 0.15
                if t < slash_delay:
                    continue
                slash_t = (t - slash_delay) / (1 - slash_delay) if (1 - slash_delay) > 0 else 0
                slash_t = min(1.0, slash_t)

                # Different angle for each slash
                base_angle_offset = (slash_i - 2) * 0.35

                slash_surf = pygame.Surface((200, 200), pygame.SRCALPHA)
                center = (100, 100)

                start_angle = -math.pi * 0.7 + base_angle_offset
                end_angle = math.pi * 0.7 + base_angle_offset
                radius = 44

                current_a = start_angle + (end_angle - start_angle) * slash_t
                fade_slash = max(0.0, 1 - slash_t * 0.5)

                # Trail
                for step in range(8):
                    step_t = step / 8
                    trail_progress = max(0.0, slash_t - step_t * 0.3)
                    trail_a = start_angle + (end_angle - start_angle) * trail_progress
                    fade_step = (1 - step_t) * fade_slash
                    alpha_step = _NS_kenshiro._alpha(220 * fade_step)
                    if alpha_step <= 0:
                        continue

                    arc_pts = []
                    for i in range(6):
                        a = trail_a - 0.15 + 0.3 * i / 5
                        px = center[0] + int(math.cos(a) * radius) * facing
                        py = center[1] + int(math.sin(a) * radius)
                        arc_pts.append((px, py))

                    for thick, color, a_mult in [
                        (7, _NS_kenshiro.PALETTE["energy_dark"], 0.7),
                        (5, _NS_kenshiro.PALETTE["energy_mid"], 0.9),
                        (3, _NS_kenshiro.PALETTE["energy_light"], 1.0),
                        (1, _NS_kenshiro.PALETTE["energy_hot"], 1.0),
                    ]:
                        a = _NS_kenshiro._alpha(alpha_step * a_mult)
                        for i in range(len(arc_pts) - 1):
                            pygame.draw.line(slash_surf,
                                             _NS_kenshiro._rgba(color, a),
                                             arc_pts[i], arc_pts[i + 1], thick)

                # Leading edge
                if slash_t > 0.1:
                    leading_pts = []
                    for i in range(10):
                        a = current_a - 0.5 + 1.0 * i / 9
                        px = center[0] + int(math.cos(a) * radius) * facing
                        py = center[1] + int(math.sin(a) * radius)
                        leading_pts.append((px, py))
                    for thick, color in [
                        (8, _NS_kenshiro.PALETTE["energy_dark"]),
                        (5, _NS_kenshiro.PALETTE["energy_mid"]),
                        (3, _NS_kenshiro.PALETTE["energy_hot"]),
                        (1, _NS_kenshiro.PALETTE["white"]),
                    ]:
                        a = _NS_kenshiro._alpha(255 * fade_slash)
                        for i in range(len(leading_pts) - 1):
                            pygame.draw.line(slash_surf,
                                             _NS_kenshiro._rgba(color, a),
                                             leading_pts[i], leading_pts[i + 1], thick)

                surface.blit(slash_surf, (slash_cx - 100, slash_cy - 100))
        else:
            # FINAL X-CROSS finish
            t = (progress - 0.75) / 0.25
            intensity = math.sin(t * math.pi)
            tx, ty = _NS_kenshiro._target_position(boss, x, y)

            # Two big X slashes
            slash_len = int(70 + t * 20)
            for slash_dir in [(1, 1), (1, -1)]:
                dx, dy = slash_dir
                p1 = (tx - dx * slash_len, ty - dy * slash_len)
                p2 = (tx + dx * slash_len, ty + dy * slash_len)

                for thick, color, a_mult in [
                    (14, _NS_kenshiro.PALETTE["energy_darkest"], 0.5),
                    (11, _NS_kenshiro.PALETTE["energy_dark"], 0.7),
                    (8, _NS_kenshiro.PALETTE["energy_mid"], 0.9),
                    (5, _NS_kenshiro.PALETTE["energy_light"], 1.0),
                    (3, _NS_kenshiro.PALETTE["energy_hot"], 1.0),
                    (2, _NS_kenshiro.PALETTE["energy_shine"], 1.0),
                    (1, _NS_kenshiro.PALETTE["white"], 1.0),
                ]:
                    alpha = _NS_kenshiro._alpha(255 * intensity * a_mult)
                    if alpha <= 0:
                        continue
                    pygame.draw.line(surface,
                        _NS_kenshiro._rgba(color, alpha), p1, p2, thick)

            # Central flash
            for r in range(25, 0, -2):
                alpha = _NS_kenshiro._alpha(240 * intensity * (25 - r) / 25)
                _NS_kenshiro._aacircle(surface,
                    _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_hot"], alpha),
                    (tx, ty), r)
            _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["energy_shine"],
                                    (tx, ty), 8)
            _NS_kenshiro._aacircle(surface, _NS_kenshiro.PALETTE["white"], (tx, ty), 4)

            # Radial spatter
            for i in range(16):
                angle = i * math.pi / 8
                spatter_len = int(slash_len * 0.8)
                sx = tx + int(math.cos(angle) * spatter_len)
                sy = ty + int(math.sin(angle) * spatter_len)
                alpha = _NS_kenshiro._alpha(240 * intensity)
                pygame.draw.rect(surface,
                    _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_light"], alpha),
                    (sx, sy, 3, 3))
                pygame.draw.rect(surface,
                    _NS_kenshiro._rgba(_NS_kenshiro.PALETTE["energy_shine"], alpha),
                    (sx, sy, 1, 1))


# ====================================================================
# khazan.py
# ====================================================================

# ====================================================================
# KHAZAN (Murad-inspired) - The Blade Shadow - Mini Boss
# ====================================================================


class _NS_khazan:
    """Namespace khazan - Desert assassin mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin (tan/desert)
        "skin_darkest": (55, 32, 20),
        "skin_dark": (105, 68, 42),
        "skin_mid": (165, 115, 78),
        "skin_light": (215, 168, 125),
        "skin_shine": (245, 210, 170),

        # Hair (silver-white)
        "hair_darkest": (60, 60, 75),
        "hair_dark": (110, 115, 135),
        "hair_mid": (175, 180, 200),
        "hair_light": (225, 230, 245),
        "hair_shine": (255, 255, 255),

        # Cloth (dark grey-brown pants)
        "cloth_darkest": (18, 15, 15),
        "cloth_dark": (42, 38, 40),
        "cloth_mid": (75, 68, 72),
        "cloth_light": (115, 108, 115),

        # Armor (dark iron with slight gold hue)
        "armor_darkest": (12, 10, 15),
        "armor_dark": (32, 28, 38),
        "armor_mid": (68, 62, 78),
        "armor_light": (120, 115, 135),
        "armor_shine": (185, 180, 200),

        # Gold accents
        "gold_darkest": (55, 32, 8),
        "gold_dark": (115, 78, 22),
        "gold_mid": (195, 148, 55),
        "gold_light": (245, 210, 115),
        "gold_shine": (255, 245, 190),

        # Red scarf / accents
        "red_darkest": (55, 10, 15),
        "red_dark": (120, 25, 35),
        "red_mid": (195, 55, 60),
        "red_light": (240, 100, 95),
        "red_shine": (255, 170, 155),

        # Blade energy (bright golden - main FX)
        "energy_darkest": (55, 30, 5),
        "energy_dark": (140, 85, 15),
        "energy_mid": (235, 165, 40),
        "energy_light": (255, 220, 110),
        "energy_hot": (255, 245, 190),
        "energy_shine": (255, 255, 230),

        # Eye glow (bright amber)
        "eye_dark": (95, 45, 10),
        "eye_mid": (220, 140, 30),
        "eye_light": (255, 210, 100),
        "eye_glow": (255, 245, 200),

        # Shadow smoke (for Vanish skill)
        "smoke_darkest": (15, 8, 20),
        "smoke_dark": (40, 25, 55),
        "smoke_mid": (75, 55, 90),
        "smoke_light": (140, 115, 155),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 3),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _rgba(color, alpha):
        return (max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
                max(0, min(255, int(alpha))))

    def _aacircle(surface, color, center, radius, width=0):
        if len(color) == 4:
            color = (max(0, min(255, int(color[0]))),
                     max(0, min(255, int(color[1]))),
                     max(0, min(255, int(color[2]))),
                     max(0, min(255, int(color[3]))))
        else:
            color = _NS_khazan._clamp(color)
        if _NS_khazan.HAS_AACIRCLE and radius > 1:
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
            color = _NS_khazan._clamp(color)
        if _NS_khazan.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_khazan._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # dengan kompensasi scale (hero di-render di canvas lalu
            # di-scale; boss langsung di layar scale=1).
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return int(x + 220 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_khazan(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_khazan._detect_moving(boss)
        _NS_khazan._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_kzn_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        _NS_khazan._draw_gold_aura(surface, x, y, pulse)
        _NS_khazan._draw_ground_ring(surface, x, y + 46, pulse, active_skill)

        # Skill ground FX
        if active_skill == "w":
            _NS_khazan._draw_leap_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_khazan._draw_spin_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_khazan._draw_vanish_ground(surface, boss, x, y, skill_timer, pulse)

        # BODY
        if active_skill == "e":
            _NS_khazan._draw_spin_body(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_khazan._draw_vanish_body(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_khazan._draw_leap_body(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_khazan._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_khazan._draw_walk(surface, boss, x, y)
        else:
            _NS_khazan._draw_idle(surface, boss, x, y)

        # Foreground FX
        if active_skill == "q":
            _NS_khazan._draw_chainedblade_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_khazan._draw_leap_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_khazan._draw_spin_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_khazan._draw_vanish_fg(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kzn_previous_timer", 0))
        active = bool(getattr(boss, "_kzn_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._kzn_attack_active = True
            boss._kzn_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._kzn_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._kzn_attack_frame = int(getattr(boss, "_kzn_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._kzn_attack_active = False
            boss._kzn_attack_frame = 0
            active = False

        boss._kzn_previous_timer = timer
        boss._kzn_attack_progress = (
            min(1.0, getattr(boss, "_kzn_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_kzn_last_x"):
            boss._kzn_last_x = boss.x
            boss._kzn_last_y = boss.y
            return False
        dx = abs(boss.x - boss._kzn_last_x)
        dy = abs(boss.y - boss._kzn_last_y)
        boss._kzn_last_x = boss.x
        boss._kzn_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        # Dramatic slow float (bigger bob + subtle sway)
        float_bob = int(math.sin(boss.pulse * 0.5) * 6)
        float_sway = int(math.sin(boss.pulse * 0.35) * 2)
        _NS_khazan._draw_shadow_float(surface, x, y + 50, boss.pulse, intensity=1.0)
        _NS_khazan._draw_float_wisps(surface, x, y + 44, boss.pulse, intensity=1.0)
        _NS_khazan._draw_body(surface, x + float_sway, y + float_bob,
                              boss.direction, boss.pulse, "idle")

    def _draw_walk(surface, boss, x, y):
        phase = boss.pulse * 1.8
        # Floating bob (faster, still dramatic)
        float_bob = int(math.sin(phase * 0.7) * 5)
        float_sway = int(math.sin(phase * 0.5) * 2)
        _NS_khazan._draw_shadow_float(surface, x + float_sway, y + 50, phase,
                                      intensity=0.85)
        # Bigger trail while moving
        _NS_khazan._draw_float_wisps(surface, x + float_sway, y + 44, phase,
                                     intensity=1.4, trail=True, facing=boss.direction)
        # Body uses "float" action (legs relaxed, no walking)
        _NS_khazan._draw_body(surface, x + float_sway, y + float_bob,
                              boss.direction, phase, "float")

    def _draw_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_kzn_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        # Arah terkunci saat serangan dimulai (lihat
        # _update_attack_anim). Fallback ke arah live.
        facing = getattr(boss, "_kzn_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Fast dual-blade swing
        if progress < 0.15:
            t = progress / 0.15
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 2)
        elif progress < 0.35:
            t = (progress - 0.15) / 0.20
            t_ease = 1 - (1 - t) ** 2
            lunge = int((-3 + t_ease * 14)) * boss.direction
            lift = int(2 - t_ease * 3)
        else:
            t = (progress - 0.35) / 0.65
            lunge = int(11 * (1 - t)) * boss.direction
            lift = int(-1 + t)

        _NS_khazan._draw_shadow(surface, x + lunge, y + 50)
        _NS_khazan._draw_body(surface, x + lunge, y - lift, boss.direction,
                               boss.pulse, "attack", progress)
        # Dual slash trail
        _NS_khazan._draw_dual_slash(surface, boss, x + lunge, y - lift, progress)

    def _draw_spin_body(surface, boss, x, y, timer, phase):
        """Endless Strike - spinning."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        spin = progress * math.pi * 10

        bob = int(math.sin(progress * math.pi) * -3)
        _NS_khazan._draw_shadow(surface, x, y + 50)
        _NS_khazan._draw_body(surface, x, y + bob, boss.direction, phase, "spin",
                               spin_angle=spin)

    def _draw_vanish_body(surface, boss, x, y, timer, phase):
        """Vanish - fade out then reappear behind target."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.35:
            # Fading out from position (smoke rising)
            alpha_t = 1.0 - progress / 0.35
            _NS_khazan._draw_shadow(surface, x, y + 50)
            body_surf = pygame.Surface((160, 160), pygame.SRCALPHA)
            _NS_khazan._draw_body(body_surf, 80, 80, boss.direction, phase, "idle")
            body_surf.set_alpha(int(255 * alpha_t))
            surface.blit(body_surf, (x - 80, y - 80))
        elif progress < 0.7:
            # Invisible - traveling (just smoke)
            pass
        else:
            # Reappearing behind target with backstab
            alpha_t = (progress - 0.7) / 0.3
            tx, ty = _NS_khazan._target_position(boss, x, y)
            behind_x = tx - boss.direction * 40
            behind_y = ty
            _NS_khazan._draw_shadow(surface, behind_x, behind_y + 50)
            body_surf = pygame.Surface((160, 160), pygame.SRCALPHA)
            # Show backstab attack pose
            _NS_khazan._draw_body(body_surf, 80, 80, boss.direction, phase, "attack",
                                    attack_progress=0.35)
            body_surf.set_alpha(int(255 * alpha_t))
            surface.blit(body_surf, (behind_x - 80, behind_y - 80))

    def _draw_leap_body(surface, boss, x, y, timer, phase):
        """Flashy Leap - dash toward target."""
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_khazan._target_position(boss, x, y)

        # Interpolate position toward target
        if progress < 0.7:
            t = progress / 0.7
            # Arc trajectory
            arc_h = -30 * math.sin(t * math.pi)
            cx = int(x + (tx - x) * t)
            cy = int(y + (ty - y) * t + arc_h)
        else:
            # Landed at target
            cx = tx
            cy = ty

        _NS_khazan._draw_shadow(surface, cx, cy + 50)
        # Body in mid-jump pose (dynamic)
        _NS_khazan._draw_body(surface, cx, cy, boss.direction, phase, "leap",
                               attack_progress=progress)

    # ============================================================
    # BODY (Humanoid HD assassin)
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0,
                    spin_angle=0):
        """Draw agile assassin body."""
        # Legs first
        _NS_khazan._draw_legs(surface, cx, cy + 16, facing, phase, action, attack_progress)

        # Waist / belt
        _NS_khazan._draw_waist(surface, cx, cy + 4, facing, phase)

        # Red scarf/sash trailing behind
        _NS_khazan._draw_scarf(surface, cx, cy - 4, facing, phase, action)

        # Torso
        _NS_khazan._draw_torso(surface, cx, cy - 8, facing, phase, action)

        # Back arm with blade (behind body)
        _NS_khazan._draw_arm_back(surface, cx, cy - 6, facing, phase, action,
                                    attack_progress, spin_angle)

        # Head with hair, mask, hood
        _NS_khazan._draw_head(surface, cx, cy - 20, facing, phase, action)

        # Front arm with blade (in front)
        _NS_khazan._draw_arm_front(surface, cx, cy - 6, facing, phase, action,
                                     attack_progress, spin_angle)

    def _draw_legs(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Agile legs. In float mode, legs dangle relaxed."""
        if action == "float":
            # Floating - legs dangle slightly with subtle sway
            leg_sway = math.sin(phase * 0.6) * 1
            # Both legs relaxed, slightly bent, dangling
            bx = cx - 3 + int(leg_sway)
            by = cy - 1  # slightly higher (relaxed)
            _NS_khazan._draw_leg_float(surface, bx, by, facing, back=True, phase=phase)

            fx = cx + 3 - int(leg_sway)
            fy = cy
            _NS_khazan._draw_leg_float(surface, fx, fy, facing, back=False, phase=phase)
            return
        elif action == "idle":
            # Idle floating - legs slightly dangle
            leg_sway = math.sin(phase * 0.4) * 1
            bx = cx - 3 + int(leg_sway)
            by = cy - 1
            _NS_khazan._draw_leg_float(surface, bx, by, facing, back=True, phase=phase)
            fx = cx + 3 - int(leg_sway)
            fy = cy
            _NS_khazan._draw_leg_float(surface, fx, fy, facing, back=False, phase=phase)
            return
        elif action == "leap":
            # Both legs bent for jump
            stride = 0
            back_lift = 3
            front_lift = 4
        elif action == "attack" and attack_progress < 0.35:
            stride = 2
            back_lift = front_lift = 0
        else:
            stride = 0
            back_lift = front_lift = 0

        # Standard leg drawing (for attack/spin/leap)
        bx = cx - 4 + int(stride)
        by = cy - int(back_lift)
        _NS_khazan._draw_leg(surface, bx, by, facing, back=True)

        fx = cx + 4 - int(stride)
        fy = cy - int(front_lift)
        _NS_khazan._draw_leg(surface, fx, fy, facing, back=False)

    def _draw_leg_float(surface, cx, cy, facing, back=False, phase=0):
        """Floating leg - relaxed, slight bend, dangling with energy trail below."""
        # Thigh (dark cloth, slightly bent inward)
        pygame.draw.rect(surface, _NS_khazan.PALETTE["shadow_deep"],
                         (cx - 3, cy - 8, 7, 9))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["cloth_darkest"],
                         (cx - 3, cy - 8, 6, 8))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["cloth_dark"],
                         (cx - 2, cy - 8, 4, 7))
        if not back:
            pygame.draw.rect(surface, _NS_khazan.PALETTE["cloth_mid"],
                             (cx - 1, cy - 7, 2, 5))

        # Knee guard
        pygame.draw.rect(surface, _NS_khazan.PALETTE["armor_darkest"],
                         (cx - 3, cy, 6, 3))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["armor_dark"],
                         (cx - 2, cy, 5, 2))
        if not back:
            pygame.draw.rect(surface, _NS_khazan.PALETTE["armor_mid"],
                             (cx - 2, cy, 4, 1))
            pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_dark"],
                             (cx - 1, cy, 2, 1))

        # Lower leg (dangling straight down but slightly angled inward)
        pygame.draw.rect(surface, _NS_khazan.PALETTE["shadow_deep"],
                         (cx - 2, cy + 3, 5, 5))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["cloth_darkest"],
                         (cx - 2, cy + 3, 4, 4))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["cloth_dark"],
                         (cx - 1, cy + 3, 3, 3))

        # Boot (dangling with gold cap pointing down)
        pygame.draw.rect(surface, _NS_khazan.PALETTE["shadow_deep"],
                         (cx - 3, cy + 7, 7, 5))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["armor_darkest"],
                         (cx - 3, cy + 7, 6, 4))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["armor_dark"],
                         (cx - 2, cy + 7, 4, 3))
        if not back:
            pygame.draw.rect(surface, _NS_khazan.PALETTE["armor_mid"],
                             (cx - 2, cy + 7, 3, 1))
            pygame.draw.rect(surface, _NS_khazan.PALETTE["armor_light"],
                             (cx - 1, cy + 7, 1, 1))

        # Gold toe cap (pointing down)
        pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_dark"],
                         (cx - 1, cy + 10, 3, 2))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_mid"],
                         (cx, cy + 10, 2, 1))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_light"],
                         (cx, cy + 10, 1, 1))

        # SMALL GOLDEN WISP under boot (floating energy)
        wisp_t = (phase * 0.8 + cx * 0.1) % 1.0
        wy = cy + 12 + int(wisp_t * 6)
        alpha = _NS_khazan._alpha(180 * (1 - wisp_t))
        if alpha > 0 and not back:
            _NS_khazan._aacircle(surface,
                                 _NS_khazan._rgba(_NS_khazan.PALETTE["energy_dark"], alpha),
                                 (cx, wy), 2)
            _NS_khazan._aacircle(surface,
                                 _NS_khazan._rgba(_NS_khazan.PALETTE["energy_mid"], alpha),
                                 (cx, wy), 1)
            pygame.draw.rect(surface,
                             _NS_khazan._rgba(_NS_khazan.PALETTE["energy_hot"], alpha),
                             (cx, wy, 1, 1))

    def _draw_leg(surface, cx, cy, facing, back=False):
        """Single armored leg with boot."""
        # Thigh (dark cloth pants)
        pygame.draw.rect(surface, _NS_khazan.PALETTE["shadow_deep"],
                         (cx - 3, cy - 8, 7, 10))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["cloth_darkest"],
                         (cx - 3, cy - 8, 6, 9))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["cloth_dark"],
                         (cx - 2, cy - 8, 4, 8))
        if not back:
            pygame.draw.rect(surface, _NS_khazan.PALETTE["cloth_mid"],
                             (cx - 1, cy - 7, 2, 6))

        # Knee guard (metal plate)
        pygame.draw.rect(surface, _NS_khazan.PALETTE["armor_darkest"],
                         (cx - 3, cy + 1, 6, 3))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["armor_dark"],
                         (cx - 2, cy + 1, 5, 2))
        if not back:
            pygame.draw.rect(surface, _NS_khazan.PALETTE["armor_mid"],
                             (cx - 2, cy + 1, 4, 1))
            pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_dark"],
                             (cx - 1, cy + 1, 2, 1))

        # Lower leg (leather wrap)
        pygame.draw.rect(surface, _NS_khazan.PALETTE["shadow_deep"],
                         (cx - 2, cy + 4, 5, 5))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["cloth_darkest"],
                         (cx - 2, cy + 4, 4, 4))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["cloth_dark"],
                         (cx - 1, cy + 4, 3, 3))

        # Boot (dark with metal cap)
        pygame.draw.rect(surface, _NS_khazan.PALETTE["shadow_deep"],
                         (cx - 4, cy + 8, 9, 5))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["armor_darkest"],
                         (cx - 4, cy + 8, 8, 4))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["armor_dark"],
                         (cx - 3, cy + 8, 6, 3))
        if not back:
            pygame.draw.rect(surface, _NS_khazan.PALETTE["armor_mid"],
                             (cx - 3, cy + 8, 5, 1))
            pygame.draw.rect(surface, _NS_khazan.PALETTE["armor_light"],
                             (cx - 2, cy + 8, 2, 1))

        # Boot toe cap (gold)
        pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_dark"],
                         (cx + facing * 3, cy + 10, 2, 2))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_mid"],
                         (cx + facing * 3, cy + 10, 1, 1))

    def _draw_waist(surface, cx, cy, facing, phase):
        """Belt with buckle."""
        # Belt
        pygame.draw.rect(surface, _NS_khazan.PALETTE["shadow_deep"],
                         (cx - 10, cy - 2, 21, 4))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["cloth_darkest"],
                         (cx - 10, cy - 2, 20, 4))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["cloth_dark"],
                         (cx - 10, cy - 2, 20, 3))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["cloth_mid"],
                         (cx - 9, cy - 1, 18, 1))

        # Gold buckle
        pygame.draw.rect(surface, _NS_khazan.PALETTE["shadow_deep"],
                         (cx - 3, cy - 2, 7, 5))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_darkest"],
                         (cx - 3, cy - 2, 6, 4))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_dark"],
                         (cx - 2, cy - 2, 5, 3))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_mid"],
                         (cx - 2, cy - 2, 4, 2))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_light"],
                         (cx - 2, cy - 2, 2, 1))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_shine"],
                         (cx - 1, cy - 2, 1, 1))

        # Belt studs
        for sx_off in (-7, 6):
            pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_dark"],
                             (cx + sx_off - 1, cy - 1, 2, 2))
            pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_light"],
                             (cx + sx_off, cy - 1, 1, 1))

    def _draw_scarf(surface, cx, cy, facing, phase, action):
        """Red scarf/sash flowing behind."""
        sway = math.sin(phase * 1.2) * 3
        if action in ("walk", "attack"):
            sway += math.sin(phase * 2) * 2

        back_dir = -facing

        # Long trailing scarf
        segments = 6
        points = [(cx + back_dir * 2, cy + 2)]
        for i in range(1, segments + 1):
            t = i / segments
            x_off = int(back_dir * (3 + t * 18))
            y_off = int(1 + t * 12 + math.sin(phase * 1.5 + t * 3) * (2 + t * 2))
            points.append((cx + x_off, cy + y_off))

        # Draw scarf as flowing ribbon
        for i in range(len(points) - 1):
            thickness = max(2, 6 - i)
            _NS_khazan._aaline(surface, _NS_khazan.PALETTE["shadow_deep"],
                                (points[i][0] + 1, points[i][1] + 1),
                                (points[i + 1][0] + 1, points[i + 1][1] + 1),
                                thickness + 1)
            _NS_khazan._aaline(surface, _NS_khazan.PALETTE["red_darkest"],
                                points[i], points[i + 1], thickness)
            _NS_khazan._aaline(surface, _NS_khazan.PALETTE["red_dark"],
                                points[i], points[i + 1], max(1, thickness - 1))
            _NS_khazan._aaline(surface, _NS_khazan.PALETTE["red_mid"],
                                (points[i][0], points[i][1] - 1),
                                (points[i + 1][0], points[i + 1][1] - 1),
                                max(1, thickness - 2))
            if thickness > 3:
                _NS_khazan._aaline(surface, _NS_khazan.PALETTE["red_light"],
                                    (points[i][0], points[i][1] - 2),
                                    (points[i + 1][0], points[i + 1][1] - 2),
                                    max(1, thickness - 4))

        # Tail tip highlight
        end = points[-1]
        pygame.draw.rect(surface, _NS_khazan.PALETTE["red_light"],
                         (end[0], end[1], 2, 2))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["red_shine"],
                         (end[0], end[1], 1, 1))

    def _draw_torso(surface, cx, cy, facing, phase, action):
        """Chest armor with strap details."""
        breath = math.sin(phase * 0.7) * 1

        # Torso shape (leaner than barbarian)
        torso_pts = [
            (cx - 8, cy - 3),
            (cx - 9, cy + 3),
            (cx - 7, cy + 10),
            (cx + 7, cy + 10),
            (cx + 9, cy + 3),
            (cx + 8, cy - 3),
            (cx + 5, cy - 6),
            (cx - 5, cy - 6),
        ]
        _NS_khazan._poly(surface, _NS_khazan.PALETTE["shadow_deep"],
                          [(px + 1, py + 1) for px, py in torso_pts])
        _NS_khazan._poly(surface, _NS_khazan.PALETTE["armor_darkest"], torso_pts)

        # Main plate
        _NS_khazan._poly(surface, _NS_khazan.PALETTE["armor_dark"], [
            (cx - 7, cy - 2 + int(breath)),
            (cx - 8, cy + 3),
            (cx - 6, cy + 9),
            (cx + 6, cy + 9),
            (cx + 8, cy + 3),
            (cx + 7, cy - 2 + int(breath)),
            (cx + 4, cy - 5),
            (cx - 4, cy - 5),
        ])

        # Chest plate highlight
        _NS_khazan._poly(surface, _NS_khazan.PALETTE["armor_mid"], [
            (cx - 5, cy - 1 + int(breath)),
            (cx - 6, cy + 3),
            (cx - 4, cy + 7),
            (cx + 4, cy + 7),
            (cx + 6, cy + 3),
            (cx + 5, cy - 1 + int(breath)),
            (cx + 3, cy - 4),
            (cx - 3, cy - 4),
        ])

        # Bright chest highlight
        _NS_khazan._poly(surface, _NS_khazan.PALETTE["armor_light"], [
            (cx - 2, cy + 1 + int(breath)),
            (cx + 2, cy + 1 + int(breath)),
            (cx + 2, cy + 5),
            (cx - 2, cy + 5),
        ])
        pygame.draw.rect(surface, _NS_khazan.PALETTE["armor_shine"],
                         (cx - 1, cy + 2 + int(breath), 2, 1))

        # Gold chest emblem (V-shape)
        pygame.draw.line(surface, _NS_khazan.PALETTE["gold_dark"],
                         (cx - 4, cy - 5), (cx, cy - 1), 2)
        pygame.draw.line(surface, _NS_khazan.PALETTE["gold_dark"],
                         (cx + 4, cy - 5), (cx, cy - 1), 2)
        pygame.draw.line(surface, _NS_khazan.PALETTE["gold_mid"],
                         (cx - 3, cy - 5), (cx, cy - 2), 1)
        pygame.draw.line(surface, _NS_khazan.PALETTE["gold_mid"],
                         (cx + 3, cy - 5), (cx, cy - 2), 1)

        # Central chest gem
        gem_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(3, 0, -1):
            alpha = _NS_khazan._alpha(140 * (3 - r) / 3 * gem_pulse)
            _NS_khazan._aacircle(surface,
                _NS_khazan._rgba(_NS_khazan.PALETTE["energy_mid"], alpha),
                (cx, cy + 3), r)
        pygame.draw.rect(surface, _NS_khazan.PALETTE["energy_dark"],
                         (cx - 1, cy + 2, 2, 3))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["energy_mid"],
                         (cx, cy + 2, 1, 2))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["energy_light"],
                         (cx, cy + 2, 1, 1))

        # Bandolier strap (diagonal)
        strap_start = (cx - 8, cy - 2)
        strap_end = (cx + 8, cy + 8)
        pygame.draw.line(surface, _NS_khazan.PALETTE["shadow_deep"],
                         (strap_start[0] + 1, strap_start[1] + 1),
                         (strap_end[0] + 1, strap_end[1] + 1), 3)
        pygame.draw.line(surface, _NS_khazan.PALETTE["cloth_darkest"],
                         strap_start, strap_end, 2)
        pygame.draw.line(surface, _NS_khazan.PALETTE["cloth_dark"],
                         (strap_start[0], strap_start[1] - 1),
                         (strap_end[0], strap_end[1] - 1), 1)

        # Pointed shoulder pauldrons
        for side_sign in (-1, 1):
            sx = cx + side_sign * 8
            # Sharp pauldron
            _NS_khazan._poly(surface, _NS_khazan.PALETTE["shadow_deep"], [
                (sx - 3 + 1, cy - 5 + 1),
                (sx - 4 + 1, cy - 2 + 1),
                (sx - 1 + 1, cy + 1),
                (sx + 4 + 1, cy + 1),
                (sx + 3 + 1, cy - 4 + 1),
            ])
            _NS_khazan._poly(surface, _NS_khazan.PALETTE["armor_darkest"], [
                (sx - 3, cy - 5),
                (sx - 4, cy - 2),
                (sx - 1, cy),
                (sx + 4, cy),
                (sx + 3, cy - 4),
            ])
            _NS_khazan._poly(surface, _NS_khazan.PALETTE["armor_dark"], [
                (sx - 2, cy - 4),
                (sx - 3, cy - 2),
                (sx, cy - 1),
                (sx + 3, cy - 1),
                (sx + 2, cy - 3),
            ])
            _NS_khazan._poly(surface, _NS_khazan.PALETTE["armor_mid"], [
                (sx - 1, cy - 3),
                (sx - 2, cy - 2),
                (sx, cy - 2),
                (sx + 2, cy - 2),
                (sx + 1, cy - 2),
            ])
            # Gold trim
            pygame.draw.line(surface, _NS_khazan.PALETTE["gold_mid"],
                             (sx - 3, cy - 5), (sx + 3, cy - 4), 1)
            pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_light"],
                             (sx, cy - 5, 1, 1))

    def _draw_arm_back(surface, cx, cy, facing, phase, action, attack_progress,
                        spin_angle=0):
        """Back arm holding second blade."""
        base_x = cx - facing * 8
        base_y = cy

        if action == "attack":
            # Back arm swings opposite to front
            if attack_progress < 0.15:
                arm_angle = -0.4
            elif attack_progress < 0.35:
                t = (attack_progress - 0.15) / 0.20
                t_ease = 1 - (1 - t) ** 2
                arm_angle = -0.4 + t_ease * 1.4
            else:
                t = (attack_progress - 0.35) / 0.65
                arm_angle = 1.0 - t * 0.8
        elif action == "spin":
            arm_angle = spin_angle * 0.3 + math.pi
        elif action == "leap":
            arm_angle = 0.8  # extended back
        elif action == "walk":
            arm_angle = math.sin(phase * 2 + math.pi) * 0.25
        else:
            arm_angle = -0.1 + math.sin(phase * 0.6) * 0.1

        elbow_x = base_x - facing * int(4 + math.cos(arm_angle) * 3)
        elbow_y = base_y + int(3 + math.sin(arm_angle) * 3)
        hand_x = elbow_x - facing * int(3 + math.cos(arm_angle + 0.4) * 4)
        hand_y = elbow_y + int(4 + math.sin(arm_angle + 0.4) * 4)

        # Upper arm
        _NS_khazan._aaline(surface, _NS_khazan.PALETTE["shadow_deep"],
                            (base_x + 1, base_y + 1), (elbow_x + 1, elbow_y + 1), 5)
        _NS_khazan._aaline(surface, _NS_khazan.PALETTE["cloth_darkest"],
                            (base_x, base_y), (elbow_x, elbow_y), 4)
        _NS_khazan._aaline(surface, _NS_khazan.PALETTE["cloth_dark"],
                            (base_x, base_y), (elbow_x, elbow_y), 3)

        # Forearm (with armor bracer)
        _NS_khazan._aaline(surface, _NS_khazan.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 4)
        _NS_khazan._aaline(surface, _NS_khazan.PALETTE["armor_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_khazan._aaline(surface, _NS_khazan.PALETTE["armor_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 2)

        # Bracer stud
        pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_mid"],
                         (int((elbow_x + hand_x) / 2), int((elbow_y + hand_y) / 2), 2, 2))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_light"],
                         (int((elbow_x + hand_x) / 2), int((elbow_y + hand_y) / 2), 1, 1))

        # Hand
        _NS_khazan._aacircle(surface, _NS_khazan.PALETTE["shadow_deep"],
                              (hand_x + 1, hand_y + 1), 3)
        _NS_khazan._aacircle(surface, _NS_khazan.PALETTE["armor_darkest"],
                              (hand_x, hand_y), 3)
        _NS_khazan._aacircle(surface, _NS_khazan.PALETTE["armor_dark"],
                              (hand_x, hand_y), 2)

        # SECOND BLADE (in back hand)
        blade_angle = arm_angle + math.pi * 0.6 * facing
        if action == "attack":
            if attack_progress < 0.15:
                blade_angle = -math.pi * 0.3 * facing
            elif attack_progress < 0.35:
                t = (attack_progress - 0.15) / 0.20
                t_ease = 1 - (1 - t) ** 2
                blade_angle = -math.pi * 0.3 * facing + t_ease * math.pi * 1.1 * facing
            else:
                blade_angle = math.pi * 0.8 * facing
        elif action == "spin":
            blade_angle = (spin_angle + math.pi) * facing
        else:
            blade_angle = math.pi * 0.7 * facing

        _NS_khazan._draw_blade(surface, hand_x, hand_y, facing, blade_angle,
                                phase, back=True)

    def _draw_arm_front(surface, cx, cy, facing, phase, action, attack_progress,
                         spin_angle=0):
        """Front arm holding main blade."""
        base_x = cx + facing * 8
        base_y = cy

        if action == "attack":
            if attack_progress < 0.15:
                t = attack_progress / 0.15
                arm_angle = -0.3 - t * 0.6
            elif attack_progress < 0.35:
                t = (attack_progress - 0.15) / 0.20
                t_ease = 1 - (1 - t) ** 2
                arm_angle = -0.9 + t_ease * 2.4
            else:
                t = (attack_progress - 0.35) / 0.65
                arm_angle = 1.5 - t * 1.2
        elif action == "spin":
            arm_angle = spin_angle * 0.3
        elif action == "leap":
            arm_angle = -0.5  # extended forward
        elif action == "walk":
            arm_angle = math.sin(phase * 2) * 0.25 + 0.2
        else:
            arm_angle = 0.3 + math.sin(phase * 0.6 + 0.5) * 0.08

        elbow_x = base_x + facing * int(4 + math.cos(arm_angle) * 3)
        elbow_y = base_y + int(3 + math.sin(arm_angle) * 3)
        hand_x = elbow_x + facing * int(4 + math.cos(arm_angle + 0.3) * 4)
        hand_y = elbow_y + int(4 + math.sin(arm_angle + 0.3) * 5)

        # Upper arm
        _NS_khazan._aaline(surface, _NS_khazan.PALETTE["shadow_deep"],
                            (base_x + 1, base_y + 1), (elbow_x + 1, elbow_y + 1), 5)
        _NS_khazan._aaline(surface, _NS_khazan.PALETTE["cloth_darkest"],
                            (base_x, base_y), (elbow_x, elbow_y), 4)
        _NS_khazan._aaline(surface, _NS_khazan.PALETTE["cloth_dark"],
                            (base_x, base_y), (elbow_x, elbow_y), 3)
        _NS_khazan._aaline(surface, _NS_khazan.PALETTE["cloth_mid"],
                            (base_x, base_y - 1), (elbow_x, elbow_y - 1), 1)

        # Forearm with bracer
        _NS_khazan._aaline(surface, _NS_khazan.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 4)
        _NS_khazan._aaline(surface, _NS_khazan.PALETTE["armor_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_khazan._aaline(surface, _NS_khazan.PALETTE["armor_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 2)
        _NS_khazan._aaline(surface, _NS_khazan.PALETTE["armor_mid"],
                            (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)

        # Bracer detail
        mid_x = int((elbow_x + hand_x) / 2)
        mid_y = int((elbow_y + hand_y) / 2)
        pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_dark"],
                         (mid_x - 1, mid_y - 1, 3, 3))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_mid"],
                         (mid_x, mid_y - 1, 2, 2))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_shine"],
                         (mid_x, mid_y - 1, 1, 1))

        # Hand
        _NS_khazan._aacircle(surface, _NS_khazan.PALETTE["shadow_deep"],
                              (hand_x + 1, hand_y + 1), 3)
        _NS_khazan._aacircle(surface, _NS_khazan.PALETTE["armor_darkest"],
                              (hand_x, hand_y), 3)
        _NS_khazan._aacircle(surface, _NS_khazan.PALETTE["armor_dark"],
                              (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_mid"],
                         (hand_x - facing, hand_y - 1, 1, 1))

        # MAIN BLADE
        blade_angle = arm_angle + 0.3 * facing
        if action == "attack":
            if attack_progress < 0.15:
                blade_angle = (-math.pi * 0.2 - (attack_progress / 0.15) * 0.5) * facing
            elif attack_progress < 0.35:
                t = (attack_progress - 0.15) / 0.20
                t_ease = 1 - (1 - t) ** 2
                start_a = -math.pi * 0.7 * facing
                end_a = math.pi * 0.7 * facing
                blade_angle = start_a + (end_a - start_a) * t_ease
            else:
                blade_angle = math.pi * 0.5 * facing
        elif action == "spin":
            blade_angle = spin_angle * facing
        elif action == "leap":
            blade_angle = -math.pi * 0.2 * facing
        else:
            blade_angle = math.pi * 0.15 * facing + math.sin(phase * 0.5) * 0.05

        _NS_khazan._draw_blade(surface, hand_x, hand_y, facing, blade_angle,
                                phase, back=False)

    def _draw_blade(surface, cx, cy, facing, angle, phase, back=False):
        """Curved scimitar/khopesh blade with golden energy."""
        blade_len = 22 if not back else 20
        dx = math.cos(angle)
        dy = math.sin(angle)

        # Compute curved blade points
        # Blade curves like a scimitar (crescent)
        curve_pts = []
        segments = 8
        for i in range(segments + 1):
            t = i / segments
            # Distance along handle direction
            r = blade_len * t
            # Add curve (perpendicular offset)
            curve = math.sin(t * math.pi) * 4
            perp_x = -dy * curve
            perp_y = dx * curve
            px = cx + int((dx * r + perp_x) * facing)
            py = cy + int(dy * r + perp_y)
            curve_pts.append((px, py))

        # Draw blade as tapered curve
        for i in range(len(curve_pts) - 1):
            t = i / len(curve_pts)
            thickness = int(4 * (1 - t)) + 1

            # Shadow
            _NS_khazan._aaline(surface, _NS_khazan.PALETTE["shadow_deep"],
                                (curve_pts[i][0] + 1, curve_pts[i][1] + 1),
                                (curve_pts[i + 1][0] + 1, curve_pts[i + 1][1] + 1),
                                thickness + 1)
            # Dark base
            _NS_khazan._aaline(surface, _NS_khazan.PALETTE["armor_darkest"],
                                curve_pts[i], curve_pts[i + 1], thickness)
            # Mid
            _NS_khazan._aaline(surface, _NS_khazan.PALETTE["armor_mid"],
                                curve_pts[i], curve_pts[i + 1], max(1, thickness - 1))
            # Bright edge
            _NS_khazan._aaline(surface, _NS_khazan.PALETTE["armor_shine"],
                                (curve_pts[i][0], curve_pts[i][1] - 1),
                                (curve_pts[i + 1][0], curve_pts[i + 1][1] - 1), 1)

        # GOLDEN ENERGY along blade edge
        alpha_mult = 1.0 if not back else 0.75
        glow_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
        offset_x = cx - 40
        offset_y = cy - 40

        for i in range(len(curve_pts) - 1):
            p1 = (curve_pts[i][0] - offset_x, curve_pts[i][1] - offset_y)
            p2 = (curve_pts[i + 1][0] - offset_x, curve_pts[i + 1][1] - offset_y)
            # Layered glow
            for thick, color, a_mult in [
                (5, _NS_khazan.PALETTE["energy_darkest"], 0.4),
                (3, _NS_khazan.PALETTE["energy_dark"], 0.6),
                (2, _NS_khazan.PALETTE["energy_mid"], 0.8),
                (1, _NS_khazan.PALETTE["energy_light"], 1.0),
            ]:
                alpha_val = _NS_khazan._alpha(220 * alpha_mult * a_mult)
                if alpha_val > 0:
                    pygame.draw.line(glow_surf,
                        _NS_khazan._rgba(color, alpha_val), p1, p2, thick)

        surface.blit(glow_surf, (offset_x, offset_y))

        # Bright tip
        tip = curve_pts[-1]
        _NS_khazan._aacircle(surface, _NS_khazan.PALETTE["energy_light"], tip, 2)
        _NS_khazan._aacircle(surface, _NS_khazan.PALETTE["energy_hot"], tip, 1)
        pygame.draw.rect(surface, _NS_khazan.PALETTE["white"], (tip[0], tip[1], 1, 1))

        # Handle/hilt (at base)
        base = curve_pts[0]
        pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_dark"],
                         (base[0] - 2, base[1] - 1, 4, 3))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_mid"],
                         (base[0] - 1, base[1] - 1, 3, 2))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["gold_light"],
                         (base[0], base[1] - 1, 1, 1))

    def _draw_head(surface, cx, cy, facing, phase, action):
        """Head with silver hair, red mask, glowing amber eyes."""
        # Neck
        pygame.draw.rect(surface, _NS_khazan.PALETTE["shadow_deep"],
                         (cx - 2, cy + 6, 5, 3))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["skin_darkest"],
                         (cx - 2, cy + 6, 4, 3))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["skin_dark"],
                         (cx - 1, cy + 6, 3, 2))

        # HAIR (silver spiky - back layer)
        _NS_khazan._draw_hair(surface, cx, cy - 4, facing, phase)

        # Head shape
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
        _NS_khazan._poly(surface, _NS_khazan.PALETTE["shadow_deep"],
                          [(px + 1, py + 1) for px, py in head_pts])
        _NS_khazan._poly(surface, _NS_khazan.PALETTE["skin_darkest"], head_pts)

        # Skin mid tone
        _NS_khazan._poly(surface, _NS_khazan.PALETTE["skin_dark"], [
            (cx - 5, cy - 1),
            (cx - 6, cy + 2),
            (cx - 4, cy + 5),
            (cx + 4, cy + 5),
            (cx + 6, cy + 2),
            (cx + 5, cy - 1),
            (cx + 3, cy - 4),
            (cx - 3, cy - 4),
        ])

        # Face highlight
        _NS_khazan._poly(surface, _NS_khazan.PALETTE["skin_mid"], [
            (cx - 3, cy),
            (cx - 4, cy + 2),
            (cx - 2, cy + 4),
            (cx + 4, cy + 4),
            (cx + 5, cy + 2),
            (cx + 4, cy - 1),
            (cx + 2, cy - 3),
            (cx - 2, cy - 3),
        ])

        # Cheek highlight (facing side)
        _NS_khazan._poly(surface, _NS_khazan.PALETTE["skin_light"], [
            (cx + facing * 1, cy - 1),
            (cx + facing * 4, cy),
            (cx + facing * 3, cy + 2),
            (cx + facing * 1, cy + 1),
        ])
        pygame.draw.rect(surface, _NS_khazan.PALETTE["skin_shine"],
                         (cx + facing * 3, cy, 1, 1))

        # RED MASK/SCARF covering lower face (from nose down)
        _NS_khazan._poly(surface, _NS_khazan.PALETTE["shadow_deep"], [
            (cx - 6 + 1, cy + 2 + 1),
            (cx + 6 + 1, cy + 2 + 1),
            (cx + 7 + 1, cy + 6 + 1),
            (cx - 7 + 1, cy + 6 + 1),
        ])
        _NS_khazan._poly(surface, _NS_khazan.PALETTE["red_darkest"], [
            (cx - 6, cy + 2),
            (cx + 6, cy + 2),
            (cx + 7, cy + 6),
            (cx - 7, cy + 6),
        ])
        _NS_khazan._poly(surface, _NS_khazan.PALETTE["red_dark"], [
            (cx - 5, cy + 2),
            (cx + 5, cy + 2),
            (cx + 6, cy + 5),
            (cx - 6, cy + 5),
        ])
        _NS_khazan._poly(surface, _NS_khazan.PALETTE["red_mid"], [
            (cx - 4, cy + 3),
            (cx + 4, cy + 3),
            (cx + 5, cy + 4),
            (cx - 5, cy + 4),
        ])
        pygame.draw.rect(surface, _NS_khazan.PALETTE["red_light"],
                         (cx + facing * 2, cy + 3, 2, 1))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["red_shine"],
                         (cx + facing * 3, cy + 3, 1, 1))

        # Mask top edge (crease/wrinkle line)
        pygame.draw.line(surface, _NS_khazan.PALETTE["red_darkest"],
                         (cx - 5, cy + 2), (cx + 5, cy + 2), 1)

        # Sharp eyebrows (angry assassin)
        pygame.draw.rect(surface, _NS_khazan.PALETTE["hair_darkest"],
                         (cx - 4, cy - 1, 3, 1))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["hair_darkest"],
                         (cx + 1, cy - 1, 3, 1))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["hair_dark"],
                         (cx - 4, cy - 1, 2, 1))
        pygame.draw.rect(surface, _NS_khazan.PALETTE["hair_dark"],
                         (cx + 2, cy - 1, 2, 1))

        # GLOWING AMBER EYES
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_off in (-2, 2):
            ex = cx + eye_off
            ey = cy + 1
            # Halo
            for r in range(3, 0, -1):
                alpha = _NS_khazan._alpha(160 * (3 - r) / 3 * eye_pulse)
                _NS_khazan._aacircle(surface,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["eye_mid"], alpha),
                    (ex, ey), r)
            pygame.draw.rect(surface, _NS_khazan.PALETTE["shadow_deep"],
                             (ex - 1, ey, 3, 2))
            pygame.draw.rect(surface, _NS_khazan.PALETTE["eye_dark"],
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_khazan.PALETTE["eye_mid"],
                             (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_khazan.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_khazan.PALETTE["eye_glow"],
                             (ex, ey, 1, 1))

    def _draw_hair(surface, cx, cy, facing, phase):
        """Silver spiky hair (mohawk-ish + swept back)."""
        # Base hair on top of head
        _NS_khazan._poly(surface, _NS_khazan.PALETTE["shadow_deep"], [
            (cx - 4 + 1, cy - 1 + 1),
            (cx - 6 + 1, cy + 3 + 1),
            (cx - 3 + 1, cy + 2 + 1),
            (cx + 3 + 1, cy + 2 + 1),
            (cx + 6 + 1, cy + 3 + 1),
            (cx + 4 + 1, cy - 1 + 1),
        ])
        _NS_khazan._poly(surface, _NS_khazan.PALETTE["hair_darkest"], [
            (cx - 4, cy - 1),
            (cx - 6, cy + 3),
            (cx - 3, cy + 2),
            (cx + 3, cy + 2),
            (cx + 6, cy + 3),
            (cx + 4, cy - 1),
        ])
        _NS_khazan._poly(surface, _NS_khazan.PALETTE["hair_dark"], [
            (cx - 3, cy),
            (cx - 5, cy + 2),
            (cx - 2, cy + 2),
            (cx + 2, cy + 2),
            (cx + 5, cy + 2),
            (cx + 3, cy),
        ])
        _NS_khazan._poly(surface, _NS_khazan.PALETTE["hair_mid"], [
            (cx - 2, cy),
            (cx - 3, cy + 1),
            (cx + 3, cy + 1),
            (cx + 2, cy),
        ])

        # Spikes on top
        for i, (x_off, height) in enumerate([(-3, 4), (-1, 5), (1, 5), (3, 4)]):
            spike_h = height + int(math.sin(phase + i) * 1)
            spike_x = cx + x_off
            spike_top_y = cy - spike_h

            _NS_khazan._poly(surface, _NS_khazan.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_top_y + 1),
                (spike_x - 2 + 1, cy + 1),
                (spike_x + 2 + 1, cy + 1),
            ])
            _NS_khazan._poly(surface, _NS_khazan.PALETTE["hair_darkest"], [
                (spike_x, spike_top_y),
                (spike_x - 2, cy),
                (spike_x + 2, cy),
            ])
            _NS_khazan._poly(surface, _NS_khazan.PALETTE["hair_dark"], [
                (spike_x, spike_top_y),
                (spike_x - 1, cy),
                (spike_x + 1, cy),
            ])
            _NS_khazan._poly(surface, _NS_khazan.PALETTE["hair_mid"], [
                (spike_x, spike_top_y),
                (spike_x, cy),
                (spike_x + 1, cy),
            ])
            pygame.draw.rect(surface, _NS_khazan.PALETTE["hair_light"],
                             (spike_x, spike_top_y, 1, 2))
            pygame.draw.rect(surface, _NS_khazan.PALETTE["hair_shine"],
                             (spike_x, spike_top_y, 1, 1))

        # Side hair strands (swept back opposite facing)
        for i in range(3):
            strand_x = cx - facing * (4 + i)
            strand_y = cy + i * 2
            pygame.draw.rect(surface, _NS_khazan.PALETTE["hair_darkest"],
                             (strand_x, strand_y, 2, 3))
            pygame.draw.rect(surface, _NS_khazan.PALETTE["hair_dark"],
                             (strand_x, strand_y, 1, 3))
            pygame.draw.rect(surface, _NS_khazan.PALETTE["hair_mid"],
                             (strand_x, strand_y + 1, 1, 1))

    # ============================================================
    # DUAL BLADE SLASH TRAIL
    # ============================================================
    def _draw_dual_slash(surface, boss, cx, cy, progress):
        """Dual golden crescent slash trails (front + back arm)."""
        if progress < 0.15 or progress > 0.55:
            return

        facing = boss.direction
        if progress < 0.35:
            swing_t = (progress - 0.15) / 0.20
        else:
            swing_t = 1.0
        swing_t = max(0.0, min(1.0, swing_t))

        fade = 1.0 if progress <= 0.35 else max(0.0, 1 - (progress - 0.35) / 0.20)

        # Draw two overlapping slashes (X pattern)
        for slash_i, (angle_offset, y_off, alpha_mult) in enumerate([
            (0, -8, 1.0),      # front blade upper slash
            (math.pi * 0.15, 6, 0.85),  # back blade lower slash
        ]):
            slash_cx = cx + facing * 24
            slash_cy = cy - 4 + y_off

            slash_surf = pygame.Surface((160, 160), pygame.SRCALPHA)
            center = (80, 80)

            start_angle = -math.pi * 0.7 + angle_offset
            end_angle = math.pi * 0.7 + angle_offset

            radius = 32

            # Trail ghosts
            trail_steps = 8
            current_a = start_angle + (end_angle - start_angle) * swing_t

            for step in range(trail_steps):
                step_t = step / trail_steps
                trail_progress = max(0.0, swing_t - step_t * 0.4)
                trail_a = start_angle + (end_angle - start_angle) * trail_progress

                fade_step = (1 - step_t) * fade * alpha_mult
                alpha_step = _NS_khazan._alpha(240 * fade_step)
                if alpha_step <= 0:
                    continue

                arc_pts = []
                arc_span = 0.15
                for i in range(6):
                    a = trail_a - arc_span + (arc_span * 2) * i / 5
                    px = center[0] + int(math.cos(a) * radius) * facing
                    py = center[1] + int(math.sin(a) * radius)
                    arc_pts.append((px, py))

                layer_thick = max(2, int(8 * fade_step))
                for layer_i, (thick_mult, color, a_mult) in enumerate([
                    (1.2, _NS_khazan.PALETTE["energy_darkest"], 0.5),
                    (1.0, _NS_khazan.PALETTE["energy_dark"], 0.7),
                    (0.8, _NS_khazan.PALETTE["energy_mid"], 0.9),
                    (0.6, _NS_khazan.PALETTE["energy_light"], 1.0),
                    (0.4, _NS_khazan.PALETTE["energy_hot"], 1.0),
                ]):
                    thick = max(1, int(layer_thick * thick_mult))
                    a = _NS_khazan._alpha(alpha_step * a_mult)
                    if a <= 0:
                        continue
                    for i in range(len(arc_pts) - 1):
                        pygame.draw.line(slash_surf,
                                         _NS_khazan._rgba(color, a),
                                         arc_pts[i], arc_pts[i + 1], thick)

            # Leading edge (brightest)
            if swing_t > 0.05:
                leading_pts = []
                arc_span_lead = 0.45
                for i in range(10):
                    a = current_a - arc_span_lead + (arc_span_lead * 2) * i / 9
                    px = center[0] + int(math.cos(a) * radius) * facing
                    py = center[1] + int(math.sin(a) * radius)
                    leading_pts.append((px, py))

                for thick, color in [
                    (8, _NS_khazan.PALETTE["energy_darkest"]),
                    (6, _NS_khazan.PALETTE["energy_dark"]),
                    (4, _NS_khazan.PALETTE["energy_mid"]),
                    (3, _NS_khazan.PALETTE["energy_light"]),
                    (2, _NS_khazan.PALETTE["energy_hot"]),
                    (1, _NS_khazan.PALETTE["energy_shine"]),
                ]:
                    a = _NS_khazan._alpha(255 * fade * alpha_mult)
                    if a <= 0:
                        continue
                    for i in range(len(leading_pts) - 1):
                        pygame.draw.line(slash_surf,
                                         _NS_khazan._rgba(color, a),
                                         leading_pts[i], leading_pts[i + 1], thick)

            # Sparkles
            for i in range(12):
                drop_angle = start_angle + (end_angle - start_angle) * (i / 12) * swing_t
                drop_r = radius + int(math.sin(swing_t * 8 + i) * 8) + 5
                dx = center[0] + int(math.cos(drop_angle) * drop_r) * facing
                dy = center[1] + int(math.sin(drop_angle) * drop_r)
                drop_a = _NS_khazan._alpha(220 * fade * alpha_mult * (i / 12))
                if drop_a > 0:
                    pygame.draw.rect(slash_surf,
                        _NS_khazan._rgba(_NS_khazan.PALETTE["energy_light"], drop_a),
                        (dx, dy, 2, 2))
                    pygame.draw.rect(slash_surf,
                        _NS_khazan._rgba(_NS_khazan.PALETTE["energy_shine"], drop_a),
                        (dx, dy, 1, 1))

            surface.blit(slash_surf, (slash_cx - 80, slash_cy - 80))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((100, 24), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 12 - radius, 80 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (10, 5, 3, 190), (5, 7, 90, 10))
        surface.blit(shadow, (x - 50, y - 12))

    def _draw_shadow_float(surface, x, y, phase, intensity=1.0):
        """Shadow that pulses with float bob (smaller when floating high)."""
        # Shadow shrinks when Khazan floats higher
        float_offset = math.sin(phase * 0.5) * 6
        # Higher float = smaller shadow
        scale = 1.0 - (float_offset + 6) / 24  # 0.75 to 1.0
        scale = max(0.55, min(1.0, scale))

        w = int(100 * scale * intensity)
        h = int(24 * scale)
        shadow = pygame.Surface((w + 20, h + 8), pygame.SRCALPHA)
        for radius in range(int(12 * scale), 0, -1):
            alpha = max(0, int((12 * scale - radius) * 16 * intensity))
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, (h + 8) // 2 - radius,
                                 w + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow,
            _NS_khazan._rgba((10, 5, 3), int(190 * intensity)),
            (5, (h + 8) // 2 - h // 2, w + 10, h))
        surface.blit(shadow, (x - (w + 20) // 2, y - (h + 8) // 2))

    def _draw_float_wisps(surface, cx, cy, phase, intensity=1.0, trail=False, facing=1):
        """Golden wisps/embers rising from below (like anti-grav particles)."""
        # Rising energy particles from beneath the character (like they're floating)
        for i in range(int(10 * intensity)):
            t = (phase * 0.6 + i * 0.15) % 1.0
            offset_x = int(math.sin(phase * 0.8 + i) * 12)
            sx = cx + offset_x + (i - 5) * 3
            sy = cy - int(t * 40)
            alpha = _NS_khazan._alpha(220 * (1 - t) * intensity)
            if alpha <= 0:
                continue
            _NS_khazan._aacircle(surface,
                _NS_khazan._rgba(_NS_khazan.PALETTE["energy_darkest"], alpha),
                (sx, sy), 3)
            _NS_khazan._aacircle(surface,
                _NS_khazan._rgba(_NS_khazan.PALETTE["energy_dark"], alpha),
                (sx, sy - 1), 2)
            _NS_khazan._aacircle(surface,
                _NS_khazan._rgba(_NS_khazan.PALETTE["energy_mid"], alpha),
                (sx, sy - 1), 1)
            pygame.draw.rect(surface,
                _NS_khazan._rgba(_NS_khazan.PALETTE["energy_light"], alpha),
                (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                _NS_khazan._rgba(_NS_khazan.PALETTE["energy_hot"], alpha),
                (sx, sy - 2, 1, 1))

        # Sparkling embers spiraling around
        for i in range(int(6 * intensity)):
            angle = phase * 1.5 + i * math.pi / 3
            radius = 18 + int(math.sin(phase + i) * 4)
            sx = cx + int(math.cos(angle) * radius)
            sy = cy - 10 + int(math.sin(angle) * radius * 0.4)
            alpha = _NS_khazan._alpha(240 * intensity)
            pygame.draw.rect(surface,
                _NS_khazan._rgba(_NS_khazan.PALETTE["energy_light"], alpha),
                (sx, sy, 2, 2))
            pygame.draw.rect(surface,
                _NS_khazan._rgba(_NS_khazan.PALETTE["energy_hot"], alpha),
                (sx, sy, 1, 1))
            pygame.draw.rect(surface,
                _NS_khazan._rgba(_NS_khazan.PALETTE["white"], alpha),
                (sx, sy, 1, 1))

        # Trail behind (when moving)
        if trail:
            for i in range(7):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + 4 + int(math.sin(phase + i) * 2)
                alpha = _NS_khazan._alpha(200 - i * 26)
                if alpha <= 0:
                    continue
                _NS_khazan._aacircle(surface,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["energy_darkest"], alpha),
                    (sx, sy), max(1, 6 - i))
                _NS_khazan._aacircle(surface,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["energy_dark"], alpha),
                    (sx, sy), max(1, 5 - i))
                _NS_khazan._aacircle(surface,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["energy_mid"], alpha),
                    (sx, sy), max(1, 3 - i))
                pygame.draw.rect(surface,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["energy_light"], alpha),
                    (sx, sy - 1, 2, 2))
                pygame.draw.rect(surface,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["energy_hot"], alpha),
                    (sx, sy - 1, 1, 1))

    def _draw_gold_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(80, 5, -4):
            alpha = _NS_khazan._alpha((80 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_khazan._aacircle(aura,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["energy_darkest"], alpha),
                    (90, 80), radius)
        for radius in range(50, 5, -3):
            alpha = _NS_khazan._alpha((50 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_khazan._aacircle(aura,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["energy_dark"], alpha),
                    (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))

        # Golden sparks floating
        for i in range(12):
            angle = phase * 0.4 + i * math.pi / 6
            r = 32 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * r)
            sy = y - 5 + int(math.sin(angle) * r * 0.5)
            alpha = _NS_khazan._alpha(230 + math.sin(phase * 4 + i) * 25)
            pygame.draw.rect(surface, _NS_khazan.PALETTE["energy_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_khazan.PALETTE["energy_hot"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((140, 46), pygame.SRCALPHA)
        pygame.draw.ellipse(ring,
            _NS_khazan._rgba(_NS_khazan.PALETTE["energy_darkest"], 200),
            (5, 14, 130, 22), 2)
        pygame.draw.ellipse(ring,
            _NS_khazan._rgba(_NS_khazan.PALETTE["energy_dark"], 220),
            (14, 17, 112, 18), 2)
        pygame.draw.ellipse(ring,
            _NS_khazan._rgba(_NS_khazan.PALETTE["energy_mid"], 180),
            (28, 20, 84, 12), 1)

        # Rune spokes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 70 + int(math.cos(angle) * 42)
            y1 = 25 + int(math.sin(angle) * 8)
            x2 = 70 + int(math.cos(angle) * 62)
            y2 = 25 + int(math.sin(angle) * 12)
            pygame.draw.line(ring,
                _NS_khazan._rgba(_NS_khazan.PALETTE["energy_light"], 220),
                (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                _NS_khazan._rgba(_NS_khazan.PALETTE["energy_hot"],
                                  _NS_khazan._alpha(160 * pulse)),
                (14, 10, 112, 30), 1)
        surface.blit(ring, (x - 70, y - 23))

    # ============================================================
    # SKILL Q: CHAINED BLADE (fan of projectiles)
    # ============================================================
    def _draw_chainedblade_fg(surface, boss, x, y, timer, phase):
        """Fan of 5 blade projectiles."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_khazan._target_position(boss, x, y)

        if progress < 0.2:
            # Charge - swirl golden energy at hand
            t = progress / 0.2
            charge_x = x + facing * 20
            charge_y = y - 8
            cr = int(3 + t * 6)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_khazan._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_khazan._aacircle(surface,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["energy_darkest"], alpha),
                    (charge_x, charge_y), r)
            _NS_khazan._aacircle(surface, _NS_khazan.PALETTE["energy_mid"],
                                  (charge_x, charge_y), max(1, cr - 2))
            _NS_khazan._aacircle(surface, _NS_khazan.PALETTE["energy_light"],
                                  (charge_x, charge_y), max(1, cr - 4))
            _NS_khazan._aacircle(surface, _NS_khazan.PALETTE["energy_hot"],
                                  (charge_x, charge_y), max(1, cr - 6))

            # Sparks
            for i in range(5):
                angle = phase * 4 + i * math.pi * 2 / 5
                sx = charge_x + int(math.cos(angle) * (cr + 3))
                sy = charge_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_khazan.PALETTE["energy_hot"], (sx, sy, 1, 1))
        else:
            # Launch fan of 5 blades
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 22
            start_y = y - 8

            # Fan angles
            base_angle = math.atan2(ty - start_y, tx - start_x)
            fan_spread = 0.4

            for blade_i in range(5):
                blade_angle = base_angle + (blade_i - 2) * (fan_spread / 4)
                fly_dist = int(200 * t)
                bx = start_x + int(math.cos(blade_angle) * fly_dist)
                by = start_y + int(math.sin(blade_angle) * fly_dist)

                # Trail
                for i in range(8):
                    trail_t = max(0.0, t - i * 0.05)
                    trail_dist = int(200 * trail_t)
                    tpx = start_x + int(math.cos(blade_angle) * trail_dist)
                    tpy = start_y + int(math.sin(blade_angle) * trail_dist)
                    alpha = _NS_khazan._alpha(220 - i * 25)
                    size = max(1, 5 - i)
                    _NS_khazan._aacircle(surface,
                        _NS_khazan._rgba(_NS_khazan.PALETTE["energy_dark"], alpha),
                        (tpx, tpy), size)
                    _NS_khazan._aacircle(surface,
                        _NS_khazan._rgba(_NS_khazan.PALETTE["energy_mid"], alpha),
                        (tpx, tpy), max(1, size - 1))
                    _NS_khazan._aacircle(surface,
                        _NS_khazan._rgba(_NS_khazan.PALETTE["energy_light"], alpha),
                        (tpx, tpy), max(1, size - 2))

                # Blade shape at head (small curved blade)
                bdx = math.cos(blade_angle)
                bdy = math.sin(blade_angle)
                tip_x = bx + int(bdx * 8)
                tip_y = by + int(bdy * 8)
                perp_x = -bdy
                perp_y = bdx

                # Blade triangle points (FIXED - proper tuples)
                p1 = (bx + int(perp_x * 2), by + int(perp_y * 2))
                p2 = (tip_x, tip_y)
                p3 = (bx - int(perp_x * 2), by - int(perp_y * 2))

                blade_pts = [p1, p2, p3]
                blade_shadow = [(p1[0] + 1, p1[1] + 1),
                                (p2[0] + 1, p2[1] + 1),
                                (p3[0] + 1, p3[1] + 1)]

                _NS_khazan._poly(surface, _NS_khazan.PALETTE["shadow_deep"], blade_shadow)
                _NS_khazan._poly(surface, _NS_khazan.PALETTE["armor_darkest"], blade_pts)

                # Highlight (mid-tone triangle inside)
                mid_p1 = (int((p1[0] + tip_x) / 2), int((p1[1] + tip_y) / 2))
                mid_p3 = (int((p3[0] + tip_x) / 2), int((p3[1] + tip_y) / 2))
                _NS_khazan._poly(surface, _NS_khazan.PALETTE["armor_mid"],
                                  [mid_p1, p2, mid_p3])

                # Glow around blade
                for r in range(6, 0, -1):
                    alpha = _NS_khazan._alpha(100 * (6 - r) / 6)
                    _NS_khazan._aacircle(surface,
                        _NS_khazan._rgba(_NS_khazan.PALETTE["energy_mid"], alpha),
                        (bx, by), r)
                _NS_khazan._aacircle(surface, _NS_khazan.PALETTE["energy_light"],
                                      (bx, by), 2)
                _NS_khazan._aacircle(surface, _NS_khazan.PALETTE["energy_shine"],
                                      (bx, by), 1)
                pygame.draw.rect(surface, _NS_khazan.PALETTE["white"], (tip_x, tip_y, 1, 1))
    # ============================================================
    # SKILL W: FLASHY LEAP (dash + AoE landing)
    # ============================================================
    def _draw_leap_ground(surface, boss, x, y, timer, phase):
        """Landing zone marker at target."""
        tx, ty = _NS_khazan._target_position(boss, x, y)
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress > 0.6:
            # Landing burst - expanding ring
            t = (progress - 0.6) / 0.4
            r = int(40 * t)
            alpha = _NS_khazan._alpha(240 * (1 - t))
            pygame.draw.ellipse(surface,
                _NS_khazan._rgba(_NS_khazan.PALETTE["energy_darkest"], alpha),
                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                _NS_khazan._rgba(_NS_khazan.PALETTE["energy_mid"], alpha),
                (tx - r + 3, ty - r // 3 + 2,
                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface,
                _NS_khazan._rgba(_NS_khazan.PALETTE["energy_hot"], alpha),
                (tx - r + 6, ty - r // 3 + 4,
                 r * 2 - 12, r * 2 // 3 - 8), 1)
        else:
            # Warning marker
            alpha = _NS_khazan._alpha(180 * progress)
            r = 25
            pygame.draw.ellipse(surface,
                _NS_khazan._rgba(_NS_khazan.PALETTE["energy_light"], alpha),
                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface,
                _NS_khazan._rgba(_NS_khazan.PALETTE["energy_hot"], alpha),
                (tx - r + 3, ty - r // 3 + 2,
                 r * 2 - 6, r * 2 // 3 - 4), 1)

    def _draw_leap_fg(surface, boss, x, y, timer, phase):
        """Leap dust trail + landing sparkles."""
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_khazan._target_position(boss, x, y)

        if progress < 0.7:
            # Trailing dust behind leaper
            t = progress / 0.7
            cur_x = int(x + (tx - x) * t)
            cur_y = int(y + (ty - y) * t - 30 * math.sin(t * math.pi))

            # Motion trail
            for i in range(8):
                trail_t = max(0.0, t - i * 0.05)
                px = int(x + (tx - x) * trail_t)
                py = int(y + (ty - y) * trail_t - 30 * math.sin(trail_t * math.pi))
                alpha = _NS_khazan._alpha(200 - i * 25)
                size = max(1, 5 - i)
                _NS_khazan._aacircle(surface,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["energy_dark"], alpha),
                    (px, py), size)
                _NS_khazan._aacircle(surface,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["energy_mid"], alpha),
                    (px, py), max(1, size - 1))
                pygame.draw.rect(surface, _NS_khazan.PALETTE["energy_hot"],
                                 (px, py, 1, 1))
        else:
            # Landing burst
            t = (progress - 0.7) / 0.3
            burst_r = int(15 + t * 30)
            for i in range(12):
                angle = i * math.pi / 6
                ex = tx + int(math.cos(angle) * burst_r)
                ey = ty + int(math.sin(angle) * burst_r * 0.7)
                alpha = _NS_khazan._alpha(240 * (1 - t))
                pygame.draw.rect(surface,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["energy_light"], alpha),
                    (ex, ey, 2, 2))
                pygame.draw.rect(surface,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["energy_shine"], alpha),
                    (ex, ey, 1, 1))

    # ============================================================
    # SKILL E: ENDLESS STRIKE (spin blades)
    # ============================================================
    def _draw_spin_ground(surface, boss, x, y, timer, phase):
        """Ground circle."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(40 + math.sin(phase * 3) * 3)
        alpha = _NS_khazan._alpha(220 * (1 - progress * 0.5))
        pygame.draw.ellipse(surface,
            _NS_khazan._rgba(_NS_khazan.PALETTE["energy_darkest"], alpha),
            (x - r, y + 42 - r // 3, r * 2, r * 2 // 3), 3)
        pygame.draw.ellipse(surface,
            _NS_khazan._rgba(_NS_khazan.PALETTE["energy_mid"], alpha),
            (x - r + 4, y + 42 - r // 3 + 3,
             r * 2 - 8, r * 2 // 3 - 6), 2)

    def _draw_spin_fg(surface, boss, x, y, timer, phase):
        """Multiple crescent slashes around boss."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        spin = progress * math.pi * 10

        slash_surf = pygame.Surface((200, 200), pygame.SRCALPHA)
        center = (100, 100)
        radius = 46

        # Draw 3 slash arcs at different rotations
        for arm_i in range(3):
            arm_start = spin + arm_i * (math.pi * 2 / 3)
            arc_pts = []
            steps = 18
            arc_span = math.pi * 0.55
            for i in range(steps + 1):
                a = arm_start + arc_span * i / steps
                px = center[0] + int(math.cos(a) * radius)
                py = center[1] + int(math.sin(a) * radius * 0.75)
                arc_pts.append((px, py))

            for layer_i, (r_off, thick, color, a_mult) in enumerate([
                (3, 8, _NS_khazan.PALETTE["energy_darkest"], 0.6),
                (2, 6, _NS_khazan.PALETTE["energy_dark"], 0.8),
                (0, 4, _NS_khazan.PALETTE["energy_mid"], 1.0),
                (-1, 3, _NS_khazan.PALETTE["energy_light"], 1.0),
                (-2, 2, _NS_khazan.PALETTE["energy_hot"], 1.0),
            ]):
                for k in range(len(arc_pts) - 1):
                    fade_k = 1 - (k / len(arc_pts))
                    alpha_val = _NS_khazan._alpha(230 * a_mult * fade_k)
                    if alpha_val <= 0:
                        continue
                    pygame.draw.line(slash_surf,
                                     _NS_khazan._rgba(color, alpha_val),
                                     arc_pts[k], arc_pts[k + 1], thick)

            # Bright tip
            if arc_pts:
                tip = arc_pts[-1]
                pygame.draw.rect(slash_surf,
                                 _NS_khazan._rgba(_NS_khazan.PALETTE["energy_shine"], 255),
                                 (tip[0], tip[1], 2, 2))
                pygame.draw.rect(slash_surf,
                                 _NS_khazan._rgba(_NS_khazan.PALETTE["white"], 255),
                                 (tip[0], tip[1], 1, 1))

        # Sparkles flying out
        for i in range(20):
            angle = spin * 0.5 + i * math.pi / 10
            r_p = radius + int(math.sin(phase + i) * 10) - 4
            px = center[0] + int(math.cos(angle) * r_p)
            py = center[1] + int(math.sin(angle) * r_p * 0.75)
            alpha = _NS_khazan._alpha(220)
            pygame.draw.rect(slash_surf,
                _NS_khazan._rgba(_NS_khazan.PALETTE["energy_light"], alpha),
                (px, py, 2, 2))
            pygame.draw.rect(slash_surf,
                _NS_khazan._rgba(_NS_khazan.PALETTE["energy_shine"], alpha),
                (px, py, 1, 1))

        surface.blit(slash_surf, (x - 100, y - 100))

    # ============================================================
    # SKILL R: VANISH
    # ============================================================
    def _draw_vanish_ground(surface, boss, x, y, timer, phase):
        """Smoke/shadow ring where boss vanishes and reappears."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_khazan._target_position(boss, x, y)

        if progress < 0.35:
            # Ring at origin (fading)
            t = progress / 0.35
            r = int(25 + t * 15)
            alpha = _NS_khazan._alpha(240 * (1 - t))
            pygame.draw.ellipse(surface,
                _NS_khazan._rgba(_NS_khazan.PALETTE["smoke_dark"], alpha),
                (x - r, y + 42 - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface,
                _NS_khazan._rgba(_NS_khazan.PALETTE["smoke_light"], alpha),
                (x - r + 3, y + 42 - r // 3 + 2,
                 r * 2 - 6, r * 2 // 3 - 4), 1)
        elif progress > 0.65:
            # Arrival ring at target (behind)
            t = (progress - 0.65) / 0.35
            behind_x = tx - boss.direction * 40
            behind_y = ty
            r = int(30 * (1 - t) + 15)
            alpha = _NS_khazan._alpha(240 * t if t < 0.5 else 240 * (1 - t))
            pygame.draw.ellipse(surface,
                _NS_khazan._rgba(_NS_khazan.PALETTE["smoke_dark"], alpha),
                (behind_x - r, behind_y + 42 - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface,
                _NS_khazan._rgba(_NS_khazan.PALETTE["energy_mid"], alpha),
                (behind_x - r + 3, behind_y + 42 - r // 3 + 2,
                 r * 2 - 6, r * 2 // 3 - 4), 1)

    def _draw_vanish_fg(surface, boss, x, y, timer, phase):
        """Smoke effects + backstab slash."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_khazan._target_position(boss, x, y)

        if progress < 0.35:
            # Rising smoke from origin
            t = progress / 0.35
            for i in range(12):
                s_t = (phase * 0.7 + i * 0.1) % 1.0
                sx = x + int(math.sin(phase + i) * 15)
                sy = y - int(s_t * 40)
                alpha = _NS_khazan._alpha(200 * (1 - s_t) * (1 - t * 0.3))
                _NS_khazan._aacircle(surface,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["smoke_darkest"], alpha),
                    (sx, sy), 5)
                _NS_khazan._aacircle(surface,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["smoke_dark"], alpha),
                    (sx, sy - 1), 4)
                _NS_khazan._aacircle(surface,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["smoke_mid"], alpha),
                    (sx, sy - 1), 3)
                pygame.draw.rect(surface,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["smoke_light"], alpha),
                    (sx, sy - 2, 1, 1))
        elif progress < 0.65:
            # Traveling dashes (motion lines from origin to target)
            t = (progress - 0.35) / 0.30
            behind_x = tx - boss.direction * 40
            behind_y = ty

            for i in range(6):
                offset_t = i * 0.15
                if t > offset_t:
                    dash_t = (t - offset_t) / (1 - offset_t) if offset_t < 1 else 0
                    dash_t = min(1.0, dash_t)
                    dash_x = int(x + (behind_x - x) * dash_t)
                    dash_y = int(y + (behind_y - y) * dash_t + math.sin(dash_t * math.pi) * -15)
                    alpha = _NS_khazan._alpha(240 * (1 - dash_t) * (1 - i * 0.1))
                    _NS_khazan._aacircle(surface,
                        _NS_khazan._rgba(_NS_khazan.PALETTE["smoke_dark"], alpha),
                        (dash_x, dash_y), 4)
                    _NS_khazan._aacircle(surface,
                        _NS_khazan._rgba(_NS_khazan.PALETTE["smoke_mid"], alpha),
                        (dash_x, dash_y), 3)
                    # Golden sparks in trail
                    pygame.draw.rect(surface,
                        _NS_khazan._rgba(_NS_khazan.PALETTE["energy_light"], alpha),
                        (dash_x, dash_y, 1, 1))
                    pygame.draw.rect(surface,
                        _NS_khazan._rgba(_NS_khazan.PALETTE["energy_hot"], alpha),
                        (dash_x, dash_y - 1, 1, 1))
        else:
            # Arrival + backstab slash on target
            t = (progress - 0.65) / 0.35
            intensity = math.sin(t * math.pi)

            # Big slash across target
            behind_x = tx - boss.direction * 40
            behind_y = ty

            # Slash line from behind to target
            slash_start_x = behind_x + boss.direction * 10
            slash_start_y = behind_y - 15
            slash_end_x = tx + boss.direction * 10
            slash_end_y = ty + 15

            for thick, color in [
                (10, _NS_khazan.PALETTE["energy_darkest"]),
                (8, _NS_khazan.PALETTE["energy_dark"]),
                (5, _NS_khazan.PALETTE["energy_mid"]),
                (3, _NS_khazan.PALETTE["energy_light"]),
                (2, _NS_khazan.PALETTE["energy_hot"]),
                (1, _NS_khazan.PALETTE["energy_shine"]),
            ]:
                alpha = _NS_khazan._alpha(255 * intensity)
                if alpha <= 0:
                    continue
                pygame.draw.line(surface,
                    _NS_khazan._rgba(color, alpha),
                    (slash_start_x, slash_start_y),
                    (slash_end_x, slash_end_y), thick)

            # Impact flash at target
            for r in range(18, 0, -2):
                alpha = _NS_khazan._alpha(220 * intensity * (18 - r) / 18)
                _NS_khazan._aacircle(surface,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["energy_hot"], alpha),
                    (tx, ty), r)
            _NS_khazan._aacircle(surface, _NS_khazan.PALETTE["energy_shine"], (tx, ty), 6)
            _NS_khazan._aacircle(surface, _NS_khazan.PALETTE["white"], (tx, ty), 3)

            # Radial spatter
            for i in range(12):
                angle = i * math.pi / 6
                spatter_len = int(25 + t * 20)
                sx = tx + int(math.cos(angle) * spatter_len)
                sy = ty + int(math.sin(angle) * spatter_len * 0.7)
                alpha = _NS_khazan._alpha(240 * intensity)
                pygame.draw.rect(surface,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["energy_light"], alpha),
                    (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                    _NS_khazan._rgba(_NS_khazan.PALETTE["energy_hot"], alpha),
                    (sx, sy, 1, 1))


# ====================================================================
# wiro.py
# ====================================================================

# ====================================================================
# WIRO - The Wind Blade - Mini Boss
# ====================================================================


class _NS_wiro:
    """Namespace wiro - Wind blade wanderer (floating)."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin (asian tan)
        "skin_darkest": (55, 32, 22),
        "skin_dark": (115, 78, 55),
        "skin_mid": (175, 128, 95),
        "skin_light": (215, 175, 135),
        "skin_shine": (245, 210, 175),

        # Hair (black flowing)
        "hair_darkest": (5, 4, 8),
        "hair_dark": (22, 18, 25),
        "hair_mid": (48, 40, 48),
        "hair_light": (85, 72, 82),

        # Leather armor (dark brown-black)
        "leather_darkest": (12, 8, 6),
        "leather_dark": (30, 22, 16),
        "leather_mid": (60, 45, 32),
        "leather_light": (105, 82, 55),

        # Cloth pants (dark grey)
        "cloth_darkest": (12, 12, 16),
        "cloth_dark": (28, 28, 35),
        "cloth_mid": (55, 55, 65),
        "cloth_light": (100, 100, 115),

        # Metal armor accents (dark iron)
        "armor_darkest": (10, 10, 15),
        "armor_dark": (32, 30, 38),
        "armor_mid": (72, 68, 82),
        "armor_light": (128, 122, 140),
        "armor_shine": (185, 180, 195),

        # Gold accents
        "gold_darkest": (60, 35, 8),
        "gold_dark": (120, 82, 22),
        "gold_mid": (200, 152, 55),
        "gold_light": (250, 215, 115),
        "gold_shine": (255, 250, 195),

        # Sword blade (steel with gold edge)
        "blade_darkest": (30, 32, 40),
        "blade_dark": (85, 88, 100),
        "blade_mid": (160, 165, 180),
        "blade_light": (220, 225, 235),
        "blade_shine": (250, 252, 255),

        # WIND energy (bright golden - main FX)
        "wind_darkest": (60, 35, 5),
        "wind_dark": (145, 90, 15),
        "wind_mid": (235, 170, 45),
        "wind_light": (255, 220, 110),
        "wind_hot": (255, 245, 190),
        "wind_shine": (255, 255, 230),

        # Eye glow (bright amber - focused warrior)
        "eye_dark": (65, 35, 10),
        "eye_mid": (200, 130, 35),
        "eye_light": (255, 210, 100),
        "eye_glow": (255, 245, 200),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 3),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _rgba(color, alpha):
        return (max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
                max(0, min(255, int(alpha))))

    def _aacircle(surface, color, center, radius, width=0):
        if len(color) == 4:
            color = (max(0, min(255, int(color[0]))),
                     max(0, min(255, int(color[1]))),
                     max(0, min(255, int(color[2]))),
                     max(0, min(255, int(color[3]))))
        else:
            color = _NS_wiro._clamp(color)
        if _NS_wiro.HAS_AACIRCLE and radius > 1:
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
            color = _NS_wiro._clamp(color)
        if _NS_wiro.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_wiro._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # dengan kompensasi scale (hero di-render di canvas lalu
            # di-scale; boss langsung di layar scale=1).
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return int(x + 220 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_wiro(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_wiro._detect_moving(boss)
        _NS_wiro._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_wir_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        _NS_wiro._draw_wind_aura(surface, x, y, pulse)
        _NS_wiro._draw_ground_ring(surface, x, y + 48, pulse, active_skill)

        # Skill ground FX
        if active_skill == "e":
            _NS_wiro._draw_dash_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_wiro._draw_whirl_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_wiro._draw_typhoon_ground(surface, boss, x, y, skill_timer, pulse)

        # BODY
        if active_skill == "w":
            _NS_wiro._draw_whirl_body(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_wiro._draw_dash_body(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_wiro._draw_typhoon_body(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_wiro._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_wiro._draw_float_move(surface, boss, x, y)
        else:
            _NS_wiro._draw_idle(surface, boss, x, y)

        # Foreground FX
        if active_skill == "q":
            _NS_wiro._draw_windcut_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_wiro._draw_whirl_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_wiro._draw_dash_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_wiro._draw_typhoon_fg(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_wir_previous_timer", 0))
        active = bool(getattr(boss, "_wir_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._wir_attack_active = True
            boss._wir_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._wir_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._wir_attack_frame = int(getattr(boss, "_wir_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._wir_attack_active = False
            boss._wir_attack_frame = 0
            active = False

        boss._wir_previous_timer = timer
        boss._wir_attack_progress = (
            min(1.0, getattr(boss, "_wir_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_wir_last_x"):
            boss._wir_last_x = boss.x
            boss._wir_last_y = boss.y
            return False
        dx = abs(boss.x - boss._wir_last_x)
        dy = abs(boss.y - boss._wir_last_y)
        boss._wir_last_x = boss.x
        boss._wir_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        # Dramatic wind float
        float_bob = int(math.sin(boss.pulse * 0.5) * 6)
        float_sway = int(math.sin(boss.pulse * 0.35) * 2)
        _NS_wiro._draw_shadow_float(surface, x, y + 52, boss.pulse, intensity=1.0)
        _NS_wiro._draw_wind_wisps(surface, x, y + 46, boss.pulse, intensity=1.0)
        _NS_wiro._draw_body(surface, x + float_sway, y + float_bob,
                             boss.direction, boss.pulse, "idle")

    def _draw_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.7
        float_bob = int(math.sin(phase * 0.7) * 5)
        float_sway = int(math.sin(phase * 0.5) * 2)
        _NS_wiro._draw_shadow_float(surface, x + float_sway, y + 52, phase,
                                     intensity=0.85)
        _NS_wiro._draw_wind_wisps(surface, x + float_sway, y + 46, phase,
                                   intensity=1.5, trail=True, facing=boss.direction)
        _NS_wiro._draw_body(surface, x + float_sway, y + float_bob,
                             boss.direction, phase, "float")

    def _draw_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_wir_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        # Arah terkunci saat serangan dimulai (lihat
        # _update_attack_anim). Fallback ke arah live.
        facing = getattr(boss, "_wir_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Wind swing - decisive strike
        if progress < 0.2:
            t = progress / 0.2
            lunge = -int(t * 4) * boss.direction
            lift = int(t * 3)
            float_bob = int(math.sin(boss.pulse * 0.5) * 4)
        elif progress < 0.4:
            t = (progress - 0.2) / 0.2
            t_ease = 1 - (1 - t) ** 2
            lunge = int((-4 + t_ease * 18)) * boss.direction
            lift = int(3 - t_ease * 5)
            float_bob = 0
        else:
            t = (progress - 0.4) / 0.6
            lunge = int(14 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
            float_bob = int(math.sin(boss.pulse * 0.5) * 4 * t)

        _NS_wiro._draw_shadow_float(surface, x + lunge, y + 52, boss.pulse,
                                     intensity=0.9)
        _NS_wiro._draw_wind_wisps(surface, x + lunge, y + 46, boss.pulse,
                                   intensity=1.3)
        _NS_wiro._draw_body(surface, x + lunge, y - lift + float_bob,
                             boss.direction, boss.pulse, "attack", progress)
        _NS_wiro._draw_sword_slash(surface, boss, x + lunge,
                                    y - lift + float_bob, progress)

    def _draw_whirl_body(surface, boss, x, y, timer, phase):
        """Blade Whirl - spinning."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        spin = progress * math.pi * 12

        float_bob = int(math.sin(progress * math.pi * 2) * -5)
        _NS_wiro._draw_shadow_float(surface, x, y + 52, phase, intensity=0.9)
        _NS_wiro._draw_wind_wisps(surface, x, y + 46, phase, intensity=1.8)
        _NS_wiro._draw_body(surface, x, y + float_bob, boss.direction, phase,
                             "spin", spin_angle=spin)

    def _draw_dash_body(surface, boss, x, y, timer, phase):
        """Sword Dash - blitz forward."""
        duration = 35
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_wiro._target_position(boss, x, y)

        if progress < 0.75:
            t = progress / 0.75
            t_ease = 1 - (1 - t) ** 3
            cx = int(x + (tx - x) * t_ease * 0.9)
            cy = int(y + (ty - y) * t_ease * 0.9)
        else:
            cx = int(x + (tx - x) * 0.9)
            cy = int(y + (ty - y) * 0.9)

        float_bob = int(math.sin(phase * 0.5) * 3)
        _NS_wiro._draw_shadow_float(surface, cx, cy + 52, phase, intensity=0.8)
        _NS_wiro._draw_wind_wisps(surface, cx, cy + 46, phase, intensity=1.7,
                                   trail=True, facing=boss.direction)
        _NS_wiro._draw_body(surface, cx, cy + float_bob, boss.direction, phase,
                             "attack", attack_progress=0.35)

    def _draw_typhoon_body(surface, boss, x, y, timer, phase):
        """Typhoon - stay in center of storm."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Boss floats higher during typhoon
        float_bob = int(math.sin(progress * math.pi * 3) * -4) - int(progress * 8)
        _NS_wiro._draw_shadow_float(surface, x, y + 52, phase, intensity=0.7)
        _NS_wiro._draw_wind_wisps(surface, x, y + 46, phase, intensity=2.0)
        _NS_wiro._draw_body(surface, x, y + float_bob, boss.direction, phase,
                             "idle")

    # ============================================================
    # BODY (Wanderer swordsman)
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0,
                    spin_angle=0):
        """Draw wind blade wanderer."""
        # Long hair flowing (draw first so it goes behind body)
        _NS_wiro._draw_long_hair(surface, cx, cy - 16, facing, phase, action)

        # Legs (dangling)
        _NS_wiro._draw_legs(surface, cx, cy + 18, facing, phase, action, attack_progress)

        # Belt/waist
        _NS_wiro._draw_waist(surface, cx, cy + 6, facing, phase)

        # Torso (leather armor)
        _NS_wiro._draw_torso(surface, cx, cy - 8, facing, phase, action)

        # Back arm (sheath/off-hand)
        _NS_wiro._draw_arm_back(surface, cx, cy - 6, facing, phase, action,
                                 attack_progress, spin_angle)

        # Head
        _NS_wiro._draw_head(surface, cx, cy - 22, facing, phase, action)

        # Front arm with sword
        _NS_wiro._draw_arm_front(surface, cx, cy - 6, facing, phase, action,
                                  attack_progress, spin_angle)

    def _draw_long_hair(surface, cx, cy, facing, phase, action):
        """Long dramatic black hair flowing behind + up (wind swept)."""
        sway = math.sin(phase * 0.7) * 4
        if action in ("float", "attack", "spin"):
            sway += math.sin(phase * 1.5) * 2

        back_dir = -facing

        # Hair mass - wild flowing behind + upward
        # Back hair mane (long, flowing back with wind)
        hair_back_pts = [
            (cx + back_dir * 2, cy - 2),
            (cx + back_dir * 6, cy + 2 + int(sway * 0.5)),
            (cx + back_dir * 12, cy + 8 + int(sway)),
            (cx + back_dir * 16, cy + 16 + int(sway * 1.3)),
            (cx + back_dir * 18, cy + 24 + int(sway * 1.5)),
            (cx + back_dir * 15, cy + 30 + int(sway)),
            (cx + back_dir * 8, cy + 28),
            (cx + back_dir * 3, cy + 18),
            (cx, cy + 4),
            (cx + back_dir * 1, cy - 4),
        ]
        _NS_wiro._poly(surface, _NS_wiro.PALETTE["shadow_deep"],
                        [(px + 1, py + 1) for px, py in hair_back_pts])
        _NS_wiro._poly(surface, _NS_wiro.PALETTE["hair_darkest"], hair_back_pts)

        # Mid tone
        _NS_wiro._poly(surface, _NS_wiro.PALETTE["hair_dark"], [
            (cx + back_dir * 2, cy - 1),
            (cx + back_dir * 5, cy + 2 + int(sway * 0.5)),
            (cx + back_dir * 10, cy + 8 + int(sway)),
            (cx + back_dir * 13, cy + 16 + int(sway)),
            (cx + back_dir * 14, cy + 22 + int(sway)),
            (cx + back_dir * 11, cy + 28),
            (cx + back_dir * 6, cy + 25),
            (cx + back_dir * 2, cy + 16),
            (cx, cy + 4),
        ])

        # Hair strand highlights
        for strand_x_off, strand_y_start in [(3, 4), (5, 8), (7, 12)]:
            pygame.draw.line(surface, _NS_wiro.PALETTE["hair_mid"],
                             (cx + back_dir * strand_x_off, cy + strand_y_start),
                             (cx + back_dir * (strand_x_off + 8 + int(sway * 0.3)),
                              cy + strand_y_start + 12), 1)

        # Wind-swept UP hair (dramatic strands going upward)
        for i in range(4):
            up_x = cx + back_dir * (2 + i * 3)
            up_y_base = cy - 3
            up_h = 8 + int(math.sin(phase + i) * 2)
            up_y_top = up_y_base - up_h
            # Angled backward with wind
            up_x_top = up_x + back_dir * int(up_h * 0.4 + sway * 0.4)

            _NS_wiro._poly(surface, _NS_wiro.PALETTE["shadow_deep"], [
                (up_x + 1, up_y_base + 1),
                (up_x_top + 1, up_y_top + 1),
                (up_x + back_dir * 2 + 1, up_y_base + 1),
            ])
            _NS_wiro._poly(surface, _NS_wiro.PALETTE["hair_darkest"], [
                (up_x, up_y_base),
                (up_x_top, up_y_top),
                (up_x + back_dir * 2, up_y_base),
            ])
            _NS_wiro._poly(surface, _NS_wiro.PALETTE["hair_dark"], [
                (up_x + back_dir * 1, up_y_base),
                (up_x_top, up_y_top),
                (up_x + back_dir * 2, up_y_base),
            ])
            pygame.draw.rect(surface, _NS_wiro.PALETTE["hair_mid"],
                             (up_x_top, up_y_top, 1, 2))

    def _draw_legs(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Legs dangling in float."""
        if action in ("idle", "float", "spin"):
            sway = math.sin(phase * 0.6) * 1
            bx = cx - 4 + int(sway)
            by = cy - 1
            _NS_wiro._draw_leg_float(surface, bx, by, facing, back=True, phase=phase)
            fx = cx + 4 - int(sway)
            fy = cy
            _NS_wiro._draw_leg_float(surface, fx, fy, facing, back=False, phase=phase)
        elif action == "attack" and attack_progress < 0.4:
            # Combat stance
            bx = cx - 5
            by = cy
            _NS_wiro._draw_leg(surface, bx, by, facing, back=True)
            fx = cx + 5
            fy = cy
            _NS_wiro._draw_leg(surface, fx, fy, facing, back=False)
        else:
            bx = cx - 4
            by = cy - 1
            _NS_wiro._draw_leg_float(surface, bx, by, facing, back=True, phase=phase)
            fx = cx + 4
            fy = cy - 1
            _NS_wiro._draw_leg_float(surface, fx, fy, facing, back=False, phase=phase)

    def _draw_leg_float(surface, cx, cy, facing, back=False, phase=0):
        """Floating leg with wisp underneath."""
        # Upper leg (dark cloth pants)
        pygame.draw.rect(surface, _NS_wiro.PALETTE["shadow_deep"],
                         (cx - 3, cy - 8, 7, 9))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["cloth_darkest"],
                         (cx - 3, cy - 8, 6, 8))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["cloth_dark"],
                         (cx - 2, cy - 8, 4, 7))
        if not back:
            pygame.draw.rect(surface, _NS_wiro.PALETTE["cloth_mid"],
                             (cx - 1, cy - 7, 2, 5))

        # Leather binding (wrap around thigh - dark leather straps)
        pygame.draw.rect(surface, _NS_wiro.PALETTE["leather_darkest"],
                         (cx - 3, cy - 4, 6, 1))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["leather_dark"],
                         (cx - 3, cy - 4, 5, 1))

        # Lower leg (dark cloth)
        pygame.draw.rect(surface, _NS_wiro.PALETTE["shadow_deep"],
                         (cx - 2, cy + 1, 5, 7))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["cloth_darkest"],
                         (cx - 2, cy + 1, 4, 6))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["cloth_dark"],
                         (cx - 1, cy + 1, 3, 5))

        # Boot (dark leather)
        pygame.draw.rect(surface, _NS_wiro.PALETTE["shadow_deep"],
                         (cx - 3, cy + 7, 7, 4))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["leather_darkest"],
                         (cx - 3, cy + 7, 6, 3))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["leather_dark"],
                         (cx - 2, cy + 7, 4, 2))
        if not back:
            pygame.draw.rect(surface, _NS_wiro.PALETTE["leather_mid"],
                             (cx - 2, cy + 7, 3, 1))

        # Gold buckle on boot
        if not back:
            pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_dark"],
                             (cx - 1, cy + 9, 2, 1))
            pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_mid"],
                             (cx, cy + 9, 1, 1))

        # WIND WISP under boot
        wisp_t = (phase * 0.8 + cx * 0.1) % 1.0
        wy = cy + 11 + int(wisp_t * 6)
        alpha = _NS_wiro._alpha(180 * (1 - wisp_t))
        if alpha > 0 and not back:
            _NS_wiro._aacircle(surface,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_dark"], alpha),
                (cx, wy), 2)
            _NS_wiro._aacircle(surface,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_mid"], alpha),
                (cx, wy), 1)
            pygame.draw.rect(surface,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_hot"], alpha),
                (cx, wy, 1, 1))

    def _draw_leg(surface, cx, cy, facing, back=False):
        """Planted leg (combat)."""
        pygame.draw.rect(surface, _NS_wiro.PALETTE["shadow_deep"],
                         (cx - 3, cy - 8, 7, 9))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["cloth_darkest"],
                         (cx - 3, cy - 8, 6, 8))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["cloth_dark"],
                         (cx - 2, cy - 8, 4, 7))
        if not back:
            pygame.draw.rect(surface, _NS_wiro.PALETTE["cloth_mid"],
                             (cx - 1, cy - 7, 2, 5))

        # Leather strap
        pygame.draw.rect(surface, _NS_wiro.PALETTE["leather_darkest"],
                         (cx - 3, cy - 4, 6, 1))

        # Lower leg
        pygame.draw.rect(surface, _NS_wiro.PALETTE["shadow_deep"],
                         (cx - 2, cy + 1, 5, 6))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["cloth_darkest"],
                         (cx - 2, cy + 1, 4, 5))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["cloth_dark"],
                         (cx - 1, cy + 1, 3, 4))

        # Boot
        pygame.draw.rect(surface, _NS_wiro.PALETTE["shadow_deep"],
                         (cx - 3, cy + 6, 7, 5))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["leather_darkest"],
                         (cx - 3, cy + 6, 6, 4))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["leather_dark"],
                         (cx - 2, cy + 6, 4, 3))
        if not back:
            pygame.draw.rect(surface, _NS_wiro.PALETTE["leather_mid"],
                             (cx - 2, cy + 6, 3, 1))
            pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_dark"],
                             (cx - 1, cy + 8, 2, 1))
            pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_mid"],
                             (cx, cy + 8, 1, 1))

    def _draw_waist(surface, cx, cy, facing, phase):
        """Belt with buckle + hanging straps."""
        # Wide belt
        pygame.draw.rect(surface, _NS_wiro.PALETTE["shadow_deep"],
                         (cx - 11, cy - 3, 23, 5))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["leather_darkest"],
                         (cx - 11, cy - 3, 22, 5))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["leather_dark"],
                         (cx - 11, cy - 3, 22, 4))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["leather_mid"],
                         (cx - 10, cy - 2, 20, 2))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["leather_light"],
                         (cx - 9, cy - 2, 4, 1))

        # Gold buckle center
        pygame.draw.rect(surface, _NS_wiro.PALETTE["shadow_deep"],
                         (cx - 3, cy - 3, 7, 5))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_darkest"],
                         (cx - 3, cy - 3, 6, 4))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_dark"],
                         (cx - 2, cy - 3, 5, 3))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_mid"],
                         (cx - 2, cy - 3, 4, 2))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_light"],
                         (cx - 2, cy - 3, 2, 1))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_shine"],
                         (cx - 1, cy - 3, 1, 1))

        # Belt studs
        for sx_off in (-8, 6):
            pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_dark"],
                             (cx + sx_off - 1, cy - 2, 2, 2))
            pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_light"],
                             (cx + sx_off, cy - 2, 1, 1))

        # Hanging cloth strap (from belt down)
        for strap_x_off, strap_len in [(-5, 8), (5, 6)]:
            strap_x = cx + strap_x_off
            for i in range(strap_len):
                pygame.draw.rect(surface, _NS_wiro.PALETTE["cloth_darkest"],
                                 (strap_x, cy + 2 + i, 2, 1))
                if i < strap_len - 2:
                    pygame.draw.rect(surface, _NS_wiro.PALETTE["cloth_dark"],
                                     (strap_x, cy + 2 + i, 1, 1))

    def _draw_torso(surface, cx, cy, facing, phase, action):
        """Leather armor top with straps."""
        breath = math.sin(phase * 0.6) * 1

        # Torso shape (leather jacket)
        torso_pts = [
            (cx - 9, cy - 3),
            (cx - 10, cy + 3),
            (cx - 8, cy + 10),
            (cx + 8, cy + 10),
            (cx + 10, cy + 3),
            (cx + 9, cy - 3),
            (cx + 6, cy - 7),
            (cx - 6, cy - 7),
        ]
        _NS_wiro._poly(surface, _NS_wiro.PALETTE["shadow_deep"],
                        [(px + 1, py + 1) for px, py in torso_pts])
        _NS_wiro._poly(surface, _NS_wiro.PALETTE["leather_darkest"], torso_pts)

        # Main leather
        _NS_wiro._poly(surface, _NS_wiro.PALETTE["leather_dark"], [
            (cx - 8, cy - 2 + int(breath)),
            (cx - 9, cy + 3),
            (cx - 7, cy + 9),
            (cx + 7, cy + 9),
            (cx + 9, cy + 3),
            (cx + 8, cy - 2 + int(breath)),
            (cx + 5, cy - 6),
            (cx - 5, cy - 6),
        ])

        # Highlight (bronze-leather glow)
        _NS_wiro._poly(surface, _NS_wiro.PALETTE["leather_mid"], [
            (cx - 5, cy - 1 + int(breath)),
            (cx - 7, cy + 3),
            (cx - 5, cy + 8),
            (cx + 5, cy + 8),
            (cx + 7, cy + 3),
            (cx + 5, cy - 1 + int(breath)),
            (cx + 3, cy - 5),
            (cx - 3, cy - 5),
        ])

        # Bright leather sheen
        _NS_wiro._poly(surface, _NS_wiro.PALETTE["leather_light"], [
            (cx - 2, cy + 1 + int(breath)),
            (cx + 2, cy + 1 + int(breath)),
            (cx + 2, cy + 6),
            (cx - 2, cy + 6),
        ])

        # Gold-trimmed collar
        pygame.draw.line(surface, _NS_wiro.PALETTE["gold_dark"],
                         (cx - 5, cy - 6), (cx, cy - 2), 2)
        pygame.draw.line(surface, _NS_wiro.PALETTE["gold_dark"],
                         (cx + 5, cy - 6), (cx, cy - 2), 2)
        pygame.draw.line(surface, _NS_wiro.PALETTE["gold_mid"],
                         (cx - 4, cy - 6), (cx, cy - 3), 1)
        pygame.draw.line(surface, _NS_wiro.PALETTE["gold_mid"],
                         (cx + 4, cy - 6), (cx, cy - 3), 1)

        # Chest strap (diagonal leather belt across chest)
        strap_start = (cx - 8, cy - 2)
        strap_end = (cx + 8, cy + 6)
        pygame.draw.line(surface, _NS_wiro.PALETTE["shadow_deep"],
                         (strap_start[0] + 1, strap_start[1] + 1),
                         (strap_end[0] + 1, strap_end[1] + 1), 4)
        pygame.draw.line(surface, _NS_wiro.PALETTE["cloth_darkest"],
                         strap_start, strap_end, 3)
        pygame.draw.line(surface, _NS_wiro.PALETTE["cloth_dark"],
                         (strap_start[0], strap_start[1] - 1),
                         (strap_end[0], strap_end[1] - 1), 2)

        # Gold ring on strap
        strap_mid = (int((strap_start[0] + strap_end[0]) / 2),
                     int((strap_start[1] + strap_end[1]) / 2))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_dark"],
                         (strap_mid[0] - 1, strap_mid[1] - 1, 3, 3))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_mid"],
                         (strap_mid[0], strap_mid[1] - 1, 2, 2))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_shine"],
                         (strap_mid[0], strap_mid[1] - 1, 1, 1))

        # Shoulder armor plate (both sides)
        for side_sign in (-1, 1):
            sx = cx + side_sign * 8
            pygame.draw.rect(surface, _NS_wiro.PALETTE["shadow_deep"],
                             (sx - 3 + 1, cy - 6 + 1, 6, 5))
            pygame.draw.rect(surface, _NS_wiro.PALETTE["armor_darkest"],
                             (sx - 3, cy - 6, 6, 5))
            pygame.draw.rect(surface, _NS_wiro.PALETTE["armor_dark"],
                             (sx - 2, cy - 6, 5, 4))
            pygame.draw.rect(surface, _NS_wiro.PALETTE["armor_mid"],
                             (sx - 2, cy - 6, 3, 2))
            pygame.draw.rect(surface, _NS_wiro.PALETTE["armor_light"],
                             (sx - 1, cy - 6, 1, 1))
            # Gold trim
            pygame.draw.line(surface, _NS_wiro.PALETTE["gold_mid"],
                             (sx - 3, cy - 6), (sx + 2, cy - 6), 1)
            pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_light"],
                             (sx - 1, cy - 6, 1, 1))

    def _draw_arm_back(surface, cx, cy, facing, phase, action, attack_progress,
                        spin_angle=0):
        """Back arm - free hand or holding scabbard."""
        base_x = cx - facing * 8
        base_y = cy

        if action == "attack":
            if attack_progress < 0.2:
                arm_angle = -0.5
            elif attack_progress < 0.4:
                t = (attack_progress - 0.2) / 0.2
                arm_angle = -0.5 + t * 0.6
            else:
                arm_angle = 0.1
        elif action == "spin":
            arm_angle = math.pi + spin_angle * 0.3
        else:
            arm_angle = -0.15 + math.sin(phase * 0.6) * 0.08

        elbow_x = base_x - facing * int(4 + math.cos(arm_angle) * 3)
        elbow_y = base_y + int(4 + math.sin(arm_angle) * 3)
        hand_x = elbow_x + facing * int(2 + math.cos(arm_angle + 0.4) * 3)
        hand_y = elbow_y + int(5 + math.sin(arm_angle + 0.4) * 3)

        # Upper arm (leather sleeve)
        _NS_wiro._aaline(surface, _NS_wiro.PALETTE["shadow_deep"],
                          (base_x + 1, base_y + 1), (elbow_x + 1, elbow_y + 1), 6)
        _NS_wiro._aaline(surface, _NS_wiro.PALETTE["leather_darkest"],
                          (base_x, base_y), (elbow_x, elbow_y), 5)
        _NS_wiro._aaline(surface, _NS_wiro.PALETTE["leather_dark"],
                          (base_x, base_y), (elbow_x, elbow_y), 4)
        _NS_wiro._aaline(surface, _NS_wiro.PALETTE["leather_mid"],
                          (base_x, base_y - 1), (elbow_x, elbow_y - 1), 2)

        # Forearm bare skin
        _NS_wiro._aaline(surface, _NS_wiro.PALETTE["shadow_deep"],
                          (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 4)
        _NS_wiro._aaline(surface, _NS_wiro.PALETTE["skin_darkest"],
                          (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_wiro._aaline(surface, _NS_wiro.PALETTE["skin_dark"],
                          (elbow_x, elbow_y), (hand_x, hand_y), 2)

        # Leather wrist wrap
        mid_x = int((elbow_x + hand_x) / 2)
        mid_y = int((elbow_y + hand_y) / 2)
        pygame.draw.rect(surface, _NS_wiro.PALETTE["armor_darkest"],
                         (mid_x - 1, mid_y - 1, 3, 3))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["armor_dark"],
                         (mid_x, mid_y - 1, 2, 2))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_dark"],
                         (mid_x, mid_y - 1, 1, 1))

        # Hand
        _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["shadow_deep"],
                            (hand_x + 1, hand_y + 1), 3)
        _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["skin_darkest"],
                            (hand_x, hand_y), 3)
        _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["skin_dark"],
                            (hand_x, hand_y), 2)
        _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["skin_mid"],
                            (hand_x - facing, hand_y - 1), 1)

        # Small wind wisp in hand (idle)
        if action == "idle":
            wisp_pulse = math.sin(phase * 3) * 0.4 + 0.6
            _NS_wiro._aacircle(surface,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_mid"],
                                _NS_wiro._alpha(150 * wisp_pulse)),
                (hand_x, hand_y - 2), 3)
            _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["wind_light"],
                                (hand_x, hand_y - 2), 1)

    def _draw_arm_front(surface, cx, cy, facing, phase, action, attack_progress,
                         spin_angle=0):
        """Front arm holds sword."""
        base_x = cx + facing * 8
        base_y = cy

        if action == "attack":
            if attack_progress < 0.2:
                t = attack_progress / 0.2
                arm_angle = -0.3 - t * 0.8
            elif attack_progress < 0.4:
                t = (attack_progress - 0.2) / 0.2
                t_ease = 1 - (1 - t) ** 2
                arm_angle = -1.1 + t_ease * 2.6
            else:
                t = (attack_progress - 0.4) / 0.6
                arm_angle = 1.5 - t * 1.2
        elif action == "spin":
            arm_angle = spin_angle * 0.3
        else:
            arm_angle = 0.3 + math.sin(phase * 0.6 + 0.5) * 0.08

        elbow_x = base_x + facing * int(4 + math.cos(arm_angle) * 3)
        elbow_y = base_y + int(3 + math.sin(arm_angle) * 3)
        hand_x = elbow_x + facing * int(5 + math.cos(arm_angle + 0.3) * 4)
        hand_y = elbow_y + int(4 + math.sin(arm_angle + 0.3) * 5)

        # Upper arm leather
        _NS_wiro._aaline(surface, _NS_wiro.PALETTE["shadow_deep"],
                          (base_x + 1, base_y + 1), (elbow_x + 1, elbow_y + 1), 6)
        _NS_wiro._aaline(surface, _NS_wiro.PALETTE["leather_darkest"],
                          (base_x, base_y), (elbow_x, elbow_y), 5)
        _NS_wiro._aaline(surface, _NS_wiro.PALETTE["leather_dark"],
                          (base_x, base_y), (elbow_x, elbow_y), 4)
        _NS_wiro._aaline(surface, _NS_wiro.PALETTE["leather_mid"],
                          (base_x, base_y - 1), (elbow_x, elbow_y - 1), 2)
        _NS_wiro._aaline(surface, _NS_wiro.PALETTE["leather_light"],
                          (base_x, base_y - 2), (elbow_x, elbow_y - 2), 1)

        # Forearm bare skin
        _NS_wiro._aaline(surface, _NS_wiro.PALETTE["shadow_deep"],
                          (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 4)
        _NS_wiro._aaline(surface, _NS_wiro.PALETTE["skin_darkest"],
                          (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_wiro._aaline(surface, _NS_wiro.PALETTE["skin_dark"],
                          (elbow_x, elbow_y), (hand_x, hand_y), 2)
        _NS_wiro._aaline(surface, _NS_wiro.PALETTE["skin_mid"],
                          (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)

        # Gold wrist bracer
        mid_x = int((elbow_x + hand_x) / 2)
        mid_y = int((elbow_y + hand_y) / 2)
        pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_darkest"],
                         (mid_x - 1, mid_y - 1, 3, 3))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_dark"],
                         (mid_x, mid_y - 1, 2, 2))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_mid"],
                         (mid_x, mid_y - 1, 1, 1))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_shine"],
                         (mid_x, mid_y - 1, 1, 1))

        # Fist gripping sword
        _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["shadow_deep"],
                            (hand_x + 1, hand_y + 1), 4)
        _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["skin_darkest"],
                            (hand_x, hand_y), 4)
        _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["skin_dark"],
                            (hand_x, hand_y), 3)
        _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["skin_mid"],
                            (hand_x - facing, hand_y - 1), 2)
        _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["skin_light"],
                            (hand_x - facing, hand_y - 1), 1)

        # SWORD
        if action == "attack":
            if attack_progress < 0.2:
                blade_angle = (-math.pi * 0.2 - (attack_progress / 0.2) * 0.6) * facing
            elif attack_progress < 0.4:
                t = (attack_progress - 0.2) / 0.2
                t_ease = 1 - (1 - t) ** 2
                start_a = -math.pi * 0.8 * facing
                end_a = math.pi * 0.7 * facing
                blade_angle = start_a + (end_a - start_a) * t_ease
            else:
                blade_angle = math.pi * 0.5 * facing
        elif action == "spin":
            blade_angle = spin_angle * facing
        else:
            blade_angle = math.pi * 0.15 * facing + math.sin(phase * 0.5) * 0.05

        _NS_wiro._draw_sword(surface, hand_x, hand_y, facing, blade_angle,
                              phase, action)

    def _draw_sword(surface, cx, cy, facing, angle, phase, action):
        """Long curved sword (jian/dao) with golden wind aura."""
        blade_len = 38
        dx = math.cos(angle)
        dy = math.sin(angle)

        # Blade with slight curve (curved sword like dao)
        # Compute points along curve
        curve_pts = []
        segments = 10
        for i in range(segments + 1):
            t = i / segments
            r = blade_len * t
            # Slight curve
            curve = math.sin(t * math.pi) * 3
            perp_x = -dy * curve
            perp_y = dx * curve
            px = cx + int((dx * r + perp_x) * facing)
            py = cy + int(dy * r + perp_y)
            curve_pts.append((px, py))

        # Handle end (opposite direction)
        handle_len = 8
        handle_end_x = cx - int(dx * handle_len) * facing
        handle_end_y = cy - int(dy * handle_len)

        # GUARD (crossguard - curved)
        perp_x = -dy
        perp_y = dx
        guard_top_x = cx + int(perp_x * 5) * facing
        guard_top_y = cy + int(perp_y * 5)
        guard_bot_x = cx - int(perp_x * 5) * facing
        guard_bot_y = cy - int(perp_y * 5)

        # Draw crossguard
        pygame.draw.line(surface, _NS_wiro.PALETTE["shadow_deep"],
                         (guard_top_x + 1, guard_top_y + 1),
                         (guard_bot_x + 1, guard_bot_y + 1), 5)
        pygame.draw.line(surface, _NS_wiro.PALETTE["gold_darkest"],
                         (guard_top_x, guard_top_y),
                         (guard_bot_x, guard_bot_y), 4)
        pygame.draw.line(surface, _NS_wiro.PALETTE["gold_dark"],
                         (guard_top_x, guard_top_y),
                         (guard_bot_x, guard_bot_y), 3)
        pygame.draw.line(surface, _NS_wiro.PALETTE["gold_mid"],
                         (guard_top_x, guard_top_y),
                         (guard_bot_x, guard_bot_y), 2)
        pygame.draw.line(surface, _NS_wiro.PALETTE["gold_light"],
                         (guard_top_x, guard_top_y - 1),
                         (guard_bot_x, guard_bot_y - 1), 1)

        # Gem in center of guard
        _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["wind_darkest"], (cx, cy), 3)
        _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["wind_dark"], (cx, cy), 2)
        _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["wind_light"], (cx, cy), 1)

        # HANDLE (dark leather wrap)
        pygame.draw.line(surface, _NS_wiro.PALETTE["shadow_deep"],
                         (cx + 1, cy + 1),
                         (handle_end_x + 1, handle_end_y + 1), 5)
        pygame.draw.line(surface, _NS_wiro.PALETTE["leather_darkest"],
                         (cx, cy), (handle_end_x, handle_end_y), 4)
        pygame.draw.line(surface, _NS_wiro.PALETTE["leather_dark"],
                         (cx, cy), (handle_end_x, handle_end_y), 3)

        # Handle wraps
        for i in range(3):
            wrap_t = 0.3 + i * 0.25
            wrap_x = int(cx + (handle_end_x - cx) * wrap_t)
            wrap_y = int(cy + (handle_end_y - cy) * wrap_t)
            pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_dark"],
                             (wrap_x - 1, wrap_y - 1, 2, 2))
            pygame.draw.rect(surface, _NS_wiro.PALETTE["gold_mid"],
                             (wrap_x, wrap_y, 1, 1))

        # Pommel
        _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["gold_dark"],
                            (handle_end_x, handle_end_y), 3)
        _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["gold_mid"],
                            (handle_end_x, handle_end_y), 2)
        _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["gold_light"],
                            (handle_end_x, handle_end_y), 1)

        # BLADE (curved, tapered)
        for i in range(len(curve_pts) - 1):
            t = i / len(curve_pts)
            thickness = int(4 * (1 - t * 0.6)) + 2

            # Shadow
            _NS_wiro._aaline(surface, _NS_wiro.PALETTE["shadow_deep"],
                              (curve_pts[i][0] + 1, curve_pts[i][1] + 1),
                              (curve_pts[i + 1][0] + 1, curve_pts[i + 1][1] + 1),
                              thickness + 1)
            # Dark base
            _NS_wiro._aaline(surface, _NS_wiro.PALETTE["blade_darkest"],
                              curve_pts[i], curve_pts[i + 1], thickness)
            # Mid
            _NS_wiro._aaline(surface, _NS_wiro.PALETTE["blade_dark"],
                              curve_pts[i], curve_pts[i + 1], max(1, thickness - 1))
            # Bright center
            _NS_wiro._aaline(surface, _NS_wiro.PALETTE["blade_mid"],
                              curve_pts[i], curve_pts[i + 1], max(1, thickness - 2))
            # Bright edge
            _NS_wiro._aaline(surface, _NS_wiro.PALETTE["blade_shine"],
                              (curve_pts[i][0], curve_pts[i][1] - 1),
                              (curve_pts[i + 1][0], curve_pts[i + 1][1] - 1), 1)

        # Bright tip
        tip = curve_pts[-1]
        _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["blade_shine"], tip, 2)
        pygame.draw.rect(surface, _NS_wiro.PALETTE["white"], (tip[0], tip[1], 1, 1))

        # WIND ENERGY along blade
        if action in ("attack", "spin"):
            glow_pulse = 1.0
        else:
            glow_pulse = math.sin(phase * 2) * 0.3 + 0.5

        glow_surf = pygame.Surface((100, 100), pygame.SRCALPHA)
        off_x = cx - 50
        off_y = cy - 50
        for pt_i in range(5):
            t = pt_i / 4
            gx = int(cx + (tip[0] - cx) * t) - off_x
            gy = int(cy + (tip[1] - cy) * t) - off_y
            for r in range(6, 0, -1):
                alpha = _NS_wiro._alpha(90 * (6 - r) / 6 * glow_pulse)
                _NS_wiro._aacircle(glow_surf,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_mid"], alpha),
                    (gx, gy), r)
        surface.blit(glow_surf, (off_x, off_y))

    def _draw_head(surface, cx, cy, facing, phase, action):
        """Head with determined face."""
        # Neck
        pygame.draw.rect(surface, _NS_wiro.PALETTE["shadow_deep"],
                         (cx - 2, cy + 6, 5, 4))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["skin_darkest"],
                         (cx - 2, cy + 6, 4, 4))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["skin_dark"],
                         (cx - 1, cy + 6, 3, 3))

        # Head shape
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
        _NS_wiro._poly(surface, _NS_wiro.PALETTE["shadow_deep"],
                        [(px + 1, py + 1) for px, py in head_pts])
        _NS_wiro._poly(surface, _NS_wiro.PALETTE["skin_darkest"], head_pts)

        # Face mid tone
        _NS_wiro._poly(surface, _NS_wiro.PALETTE["skin_dark"], [
            (cx - 5, cy - 1),
            (cx - 6, cy + 2),
            (cx - 4, cy + 5),
            (cx + 4, cy + 5),
            (cx + 6, cy + 2),
            (cx + 5, cy - 1),
            (cx + 3, cy - 4),
            (cx - 3, cy - 4),
        ])

        # Face highlight
        _NS_wiro._poly(surface, _NS_wiro.PALETTE["skin_mid"], [
            (cx - 3, cy),
            (cx - 4, cy + 2),
            (cx - 2, cy + 4),
            (cx + 4, cy + 4),
            (cx + 5, cy + 2),
            (cx + 4, cy - 1),
            (cx + 2, cy - 3),
            (cx - 2, cy - 3),
        ])

        # Cheek highlight (facing side)
        _NS_wiro._poly(surface, _NS_wiro.PALETTE["skin_light"], [
            (cx + facing * 1, cy - 1),
            (cx + facing * 4, cy),
            (cx + facing * 3, cy + 3),
            (cx + facing * 1, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_wiro.PALETTE["skin_shine"],
                         (cx + facing * 3, cy, 1, 1))

        # Angry/focused eyebrows (thick)
        pygame.draw.rect(surface, _NS_wiro.PALETTE["hair_darkest"],
                         (cx - 4, cy - 1, 3, 1))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["hair_darkest"],
                         (cx + 1, cy - 1, 3, 1))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["hair_dark"],
                         (cx - 4, cy - 1, 2, 1))
        pygame.draw.rect(surface, _NS_wiro.PALETTE["hair_dark"],
                         (cx + 2, cy - 1, 2, 1))

        # GLOWING AMBER EYES (determined warrior)
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_off in (-2, 2):
            ex = cx + eye_off
            ey = cy + 1
            for r in range(3, 0, -1):
                alpha = _NS_wiro._alpha(180 * (3 - r) / 3 * eye_pulse)
                _NS_wiro._aacircle(surface,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["eye_mid"], alpha),
                    (ex, ey), r)
            pygame.draw.rect(surface, _NS_wiro.PALETTE["shadow_deep"],
                             (ex - 1, ey, 3, 2))
            pygame.draw.rect(surface, _NS_wiro.PALETTE["eye_dark"],
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_wiro.PALETTE["eye_mid"],
                             (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_wiro.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_wiro.PALETTE["eye_glow"],
                             (ex, ey, 1, 1))

        # Nose (subtle)
        pygame.draw.rect(surface, _NS_wiro.PALETTE["skin_darkest"],
                         (cx, cy + 2, 1, 2))

        # Determined mouth (small line)
        pygame.draw.rect(surface, _NS_wiro.PALETTE["skin_darkest"],
                         (cx - 2, cy + 4, 4, 1))

        # Small hair strands falling on forehead
        for i in range(3):
            fx = cx - 2 + i * 2
            pygame.draw.rect(surface, _NS_wiro.PALETTE["hair_darkest"],
                             (fx, cy - 5, 2, 3))
            pygame.draw.rect(surface, _NS_wiro.PALETTE["hair_dark"],
                             (fx, cy - 5, 1, 3))
            pygame.draw.rect(surface, _NS_wiro.PALETTE["hair_mid"],
                             (fx + 1, cy - 5, 1, 1))

    # ============================================================
    # SWORD SLASH TRAIL
    # ============================================================
    def _draw_sword_slash(surface, boss, cx, cy, progress):
        """Golden wind slash trail."""
        if progress < 0.2 or progress > 0.55:
            return

        facing = boss.direction
        if progress < 0.4:
            swing_t = (progress - 0.2) / 0.2
        else:
            swing_t = 1.0
        swing_t = max(0.0, min(1.0, swing_t))

        fade = 1.0 if progress <= 0.4 else max(0.0, 1 - (progress - 0.4) / 0.15)

        slash_cx = cx + facing * 30
        slash_cy = cy - 6

        slash_surf = pygame.Surface((220, 220), pygame.SRCALPHA)
        center = (110, 110)

        start_angle = -math.pi * 0.85
        end_angle = math.pi * 0.75

        radius = 48

        # Trail ghosts
        trail_steps = 14
        current_a = start_angle + (end_angle - start_angle) * swing_t

        for step in range(trail_steps):
            step_t = step / trail_steps
            trail_progress = max(0.0, swing_t - step_t * 0.35)
            trail_a = start_angle + (end_angle - start_angle) * trail_progress

            fade_step = (1 - step_t) * fade
            alpha_step = _NS_wiro._alpha(240 * fade_step)
            if alpha_step <= 0:
                continue

            arc_pts = []
            arc_span = 0.15
            for i in range(7):
                a = trail_a - arc_span + (arc_span * 2) * i / 6
                r_var = radius + math.sin(step + i) * 2
                px = center[0] + int(math.cos(a) * r_var) * facing
                py = center[1] + int(math.sin(a) * r_var)
                arc_pts.append((px, py))

            layer_thick = max(2, int(11 * fade_step))
            for layer_i, (thick_mult, color, a_mult) in enumerate([
                (1.3, _NS_wiro.PALETTE["wind_darkest"], 0.5),
                (1.1, _NS_wiro.PALETTE["wind_dark"], 0.7),
                (0.85, _NS_wiro.PALETTE["wind_mid"], 0.9),
                (0.6, _NS_wiro.PALETTE["wind_light"], 1.0),
                (0.4, _NS_wiro.PALETTE["wind_hot"], 1.0),
            ]):
                thick = max(1, int(layer_thick * thick_mult))
                a = _NS_wiro._alpha(alpha_step * a_mult)
                if a <= 0:
                    continue
                for i in range(len(arc_pts) - 1):
                    pygame.draw.line(slash_surf,
                                     _NS_wiro._rgba(color, a),
                                     arc_pts[i], arc_pts[i + 1], thick)

        # Leading edge (brightest)
        if swing_t > 0.05:
            leading_pts = []
            arc_span_lead = 0.55
            for i in range(12):
                a = current_a - arc_span_lead + (arc_span_lead * 2) * i / 11
                px = center[0] + int(math.cos(a) * radius) * facing
                py = center[1] + int(math.sin(a) * radius)
                leading_pts.append((px, py))

            for thick, color in [
                (12, _NS_wiro.PALETTE["wind_darkest"]),
                (9, _NS_wiro.PALETTE["wind_dark"]),
                (6, _NS_wiro.PALETTE["wind_mid"]),
                (4, _NS_wiro.PALETTE["wind_light"]),
                (2, _NS_wiro.PALETTE["wind_hot"]),
                (1, _NS_wiro.PALETTE["wind_shine"]),
            ]:
                a = _NS_wiro._alpha(255 * fade)
                if a <= 0:
                    continue
                for i in range(len(leading_pts) - 1):
                    pygame.draw.line(slash_surf,
                                     _NS_wiro._rgba(color, a),
                                     leading_pts[i], leading_pts[i + 1], thick)

        # Sparkles
        for i in range(18):
            drop_angle = start_angle + (end_angle - start_angle) * (i / 18) * swing_t
            drop_r = radius + int(math.sin(swing_t * 8 + i) * 12) + 8
            dx = center[0] + int(math.cos(drop_angle) * drop_r) * facing
            dy = center[1] + int(math.sin(drop_angle) * drop_r)
            drop_a = _NS_wiro._alpha(230 * fade * (i / 18))
            if drop_a > 0:
                pygame.draw.rect(slash_surf,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_light"], drop_a),
                    (dx, dy, 2, 2))
                pygame.draw.rect(slash_surf,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_shine"], drop_a),
                    (dx, dy, 1, 1))

        surface.blit(slash_surf, (slash_cx - 110, slash_cy - 110))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow_float(surface, x, y, phase, intensity=1.0):
        float_offset = math.sin(phase * 0.5) * 6
        scale = 1.0 - (float_offset + 6) / 24
        scale = max(0.55, min(1.0, scale))

        w = int(110 * scale * intensity)
        h = int(26 * scale)
        shadow = pygame.Surface((w + 20, h + 8), pygame.SRCALPHA)
        for radius in range(int(13 * scale), 0, -1):
            alpha = max(0, int((13 * scale - radius) * 16 * intensity))
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, (h + 8) // 2 - radius,
                                 w + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow,
            _NS_wiro._rgba((10, 5, 3), int(190 * intensity)),
            (5, (h + 8) // 2 - h // 2, w + 10, h))
        surface.blit(shadow, (x - (w + 20) // 2, y - (h + 8) // 2))

    def _draw_wind_wisps(surface, cx, cy, phase, intensity=1.0, trail=False, facing=1):
        """Wind wisps swirling around boss."""
        # Swirling wind lines around boss (not just rising)
        for i in range(int(8 * intensity)):
            t = (phase * 0.7 + i * 0.13) % 1.0
            angle = phase * 1.2 + i * math.pi / 4
            radius = 22 + int(math.sin(phase + i) * 8)
            # Spiral upward
            sx = cx + int(math.cos(angle) * radius)
            sy = cy + int(math.sin(angle) * radius * 0.4) - int(t * 30)
            alpha = _NS_wiro._alpha(220 * (1 - t) * intensity)
            if alpha <= 0:
                continue
            _NS_wiro._aacircle(surface,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_darkest"], alpha),
                (sx, sy), 3)
            _NS_wiro._aacircle(surface,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_dark"], alpha),
                (sx, sy - 1), 2)
            _NS_wiro._aacircle(surface,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_mid"], alpha),
                (sx, sy - 1), 1)
            pygame.draw.rect(surface,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_light"], alpha),
                (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_hot"], alpha),
                (sx, sy - 2, 1, 1))

        # Wind swirl lines (curved streaks around boss)
        for i in range(int(4 * intensity)):
            base_angle = phase * 0.8 + i * math.pi / 2
            center_r = 20 + int(math.sin(phase * 0.5 + i) * 4)
            # Draw curved wind streak
            prev_pt = None
            for step in range(6):
                t = step / 5
                sweep = 0.4
                a = base_angle + sweep * t
                sx = cx + int(math.cos(a) * center_r)
                sy = cy - 8 + int(math.sin(a) * center_r * 0.4)
                if prev_pt is not None:
                    alpha = _NS_wiro._alpha(200 * intensity * (1 - t * 0.5))
                    pygame.draw.line(surface,
                        _NS_wiro._rgba(_NS_wiro.PALETTE["wind_mid"], alpha),
                        prev_pt, (sx, sy), 2)
                    pygame.draw.line(surface,
                        _NS_wiro._rgba(_NS_wiro.PALETTE["wind_light"], alpha),
                        prev_pt, (sx, sy), 1)
                prev_pt = (sx, sy)

        # Bright sparks
        for i in range(int(6 * intensity)):
            angle = phase * 1.5 + i * math.pi / 3
            radius = 26 + int(math.sin(phase + i) * 5)
            sx = cx + int(math.cos(angle) * radius)
            sy = cy - 8 + int(math.sin(angle) * radius * 0.4)
            alpha = _NS_wiro._alpha(240 * intensity)
            pygame.draw.rect(surface,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_hot"], alpha),
                (sx, sy, 2, 2))
            pygame.draw.rect(surface,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_shine"], alpha),
                (sx, sy, 1, 1))

        # Trail behind (when moving)
        if trail:
            for i in range(7):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + 4 + int(math.sin(phase + i) * 2)
                alpha = _NS_wiro._alpha(200 - i * 26)
                if alpha <= 0:
                    continue
                _NS_wiro._aacircle(surface,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_darkest"], alpha),
                    (sx, sy), max(1, 6 - i))
                _NS_wiro._aacircle(surface,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_dark"], alpha),
                    (sx, sy), max(1, 5 - i))
                _NS_wiro._aacircle(surface,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_mid"], alpha),
                    (sx, sy), max(1, 3 - i))
                pygame.draw.rect(surface,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_light"], alpha),
                    (sx, sy - 1, 2, 2))
                pygame.draw.rect(surface,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_hot"], alpha),
                    (sx, sy - 1, 1, 1))

    def _draw_wind_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(90, 5, -4):
            alpha = _NS_wiro._alpha((90 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_wiro._aacircle(aura,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_darkest"], alpha),
                    (100, 90), radius)
        for radius in range(55, 5, -3):
            alpha = _NS_wiro._alpha((55 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_wiro._aacircle(aura,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_dark"], alpha),
                    (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))

        # Floating gold sparkles
        for i in range(14):
            angle = phase * 0.4 + i * math.pi / 7
            r = 36 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * r)
            sy = y - 5 + int(math.sin(angle) * r * 0.5)
            pygame.draw.rect(surface, _NS_wiro.PALETTE["wind_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_wiro.PALETTE["wind_hot"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((150, 48), pygame.SRCALPHA)
        pygame.draw.ellipse(ring,
            _NS_wiro._rgba(_NS_wiro.PALETTE["wind_darkest"], 200),
            (5, 15, 140, 24), 3)
        pygame.draw.ellipse(ring,
            _NS_wiro._rgba(_NS_wiro.PALETTE["wind_dark"], 220),
            (14, 18, 122, 20), 2)
        pygame.draw.ellipse(ring,
            _NS_wiro._rgba(_NS_wiro.PALETTE["wind_mid"], 180),
            (30, 22, 90, 12), 1)

        # Rune spokes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 75 + int(math.cos(angle) * 46)
            y1 = 27 + int(math.sin(angle) * 9)
            x2 = 75 + int(math.cos(angle) * 68)
            y2 = 27 + int(math.sin(angle) * 13)
            pygame.draw.line(ring,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_light"], 220),
                (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_hot"],
                                _NS_wiro._alpha(160 * pulse)),
                (14, 11, 122, 32), 1)
        surface.blit(ring, (x - 75, y - 24))

    # ============================================================
    # SKILL Q: WIND CUT (projectile wave)
    # ============================================================
    def _draw_windcut_fg(surface, boss, x, y, timer, phase):
        """Wind wave projectile flying forward."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_wiro._target_position(boss, x, y)

        if progress < 0.2:
            # Charge - swirl at sword tip
            t = progress / 0.2
            charge_x = x + facing * 30
            charge_y = y - 8
            cr = int(4 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_wiro._alpha(220 * (cr + 5 - r) / (cr + 5))
                _NS_wiro._aacircle(surface,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_darkest"], alpha),
                    (charge_x, charge_y), r)
            for r in range(cr, 0, -1):
                alpha = _NS_wiro._alpha(240 * (cr - r + 1) / cr)
                _NS_wiro._aacircle(surface,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_mid"], alpha),
                    (charge_x, charge_y), r)
            _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["wind_light"],
                                (charge_x, charge_y), max(1, cr - 2))
            _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["wind_hot"],
                                (charge_x, charge_y), max(1, cr - 4))

            # Swirling sparks
            for i in range(6):
                angle = phase * 6 + i * math.pi / 3
                sx = charge_x + int(math.cos(angle) * (cr + 3))
                sy = charge_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_wiro.PALETTE["wind_shine"], (sx, sy, 1, 1))
        else:
            # LAUNCH - crescent wave projectile flies to target
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 32
            start_y = y - 6

            # Position along flight path
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Trail (curved wave shape following the position)
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_wiro._alpha(220 - i * 22)
                size = max(1, 8 - i)
                _NS_wiro._aacircle(surface,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_darkest"], alpha),
                    (px, py), size)
                _NS_wiro._aacircle(surface,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_dark"], alpha),
                    (px, py), max(1, size - 1))
                _NS_wiro._aacircle(surface,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_mid"], alpha),
                    (px, py), max(1, size - 2))
                _NS_wiro._aacircle(surface,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_light"], alpha),
                    (px, py), max(1, size - 3))

            # CRESCENT WAVE SHAPE at head (like a curved blade of wind)
            # Compute perpendicular direction
            dir_x = tx - start_x
            dir_y = ty - start_y
            dir_len = max(1, math.hypot(dir_x, dir_y))
            dir_ux = dir_x / dir_len
            dir_uy = dir_y / dir_len
            perp_x = -dir_uy
            perp_y = dir_ux

            # Draw curved wave (arc perpendicular to flight)
            wave_surf = pygame.Surface((100, 100), pygame.SRCALPHA)
            wave_center = (50, 50)
            for angle_offset_i in range(11):
                a = -math.pi * 0.5 + angle_offset_i * math.pi / 10
                px = wave_center[0] + int(math.cos(a) * 20) * facing
                py = wave_center[1] + int(math.sin(a) * 20)
                # Draw layered vertical wave
                for r, color, a_mult in [
                    (5, _NS_wiro.PALETTE["wind_darkest"], 0.5),
                    (3, _NS_wiro.PALETTE["wind_dark"], 0.7),
                    (2, _NS_wiro.PALETTE["wind_mid"], 0.9),
                    (1, _NS_wiro.PALETTE["wind_light"], 1.0),
                ]:
                    alpha = _NS_wiro._alpha(240 * a_mult)
                    _NS_wiro._aacircle(wave_surf,
                        _NS_wiro._rgba(color, alpha),
                        (px, py), r)
            surface.blit(wave_surf, (bx - 50, by - 50))

            # Bright center head
            for r in range(12, 3, -1):
                alpha = _NS_wiro._alpha(100 * (12 - r) / 12)
                _NS_wiro._aacircle(surface,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_light"], alpha),
                    (bx, by), r)
            _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["wind_hot"], (bx, by), 5)
            _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["wind_shine"], (bx, by), 3)
            _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["white"], (bx, by), 1)

            # Impact
            if t > 0.88:
                st = (t - 0.88) / 0.12
                radius = int(15 + st * 25)
                alpha = _NS_wiro._alpha(240 * (1 - st))
                _NS_wiro._aacircle(surface,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_darkest"], alpha),
                    (tx, ty), radius + 3, 3)
                _NS_wiro._aacircle(surface,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_mid"], alpha),
                    (tx, ty), radius, 2)
                _NS_wiro._aacircle(surface,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_light"], alpha),
                    (tx, ty), max(1, radius - 8), 1)

                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface,
                        _NS_wiro._rgba(_NS_wiro.PALETTE["wind_hot"], alpha),
                        (ex, ey, 2, 2))

    # ============================================================
    # SKILL W: BLADE WHIRL (multiple wind circles)
    # ============================================================
    def _draw_whirl_ground(surface, boss, x, y, timer, phase):
        """Ground rings under whirl."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Multiple concentric rings
        for ring_i in range(3):
            r = int(35 + ring_i * 10 + math.sin(phase * 2 + ring_i) * 2)
            alpha = _NS_wiro._alpha(230 * (1 - progress * 0.3) - ring_i * 40)
            if alpha <= 0:
                continue
            pygame.draw.ellipse(surface,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_dark"], alpha),
                (x - r, y + 44 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_mid"], alpha),
                (x - r + 2, y + 44 - r // 3 + 2,
                 r * 2 - 4, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_hot"], alpha),
                (x - r + 5, y + 44 - r // 3 + 4,
                 r * 2 - 10, r * 2 // 3 - 8), 1)

    def _draw_whirl_fg(surface, boss, x, y, timer, phase):
        """Multiple wind circles spinning at different heights around boss."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        spin = progress * math.pi * 14

        # Multiple concentric spinning arcs at different y-levels
        whirl_surf = pygame.Surface((280, 280), pygame.SRCALPHA)
        center = (140, 140)

        # 3 orbital planes at different heights (vertical stack)
        for orbit_i, (y_off, radius, arc_count, orbit_speed) in enumerate([
            (-15, 55, 3, 1.0),  # top
            (0, 65, 4, 1.2),    # middle (largest)
            (15, 55, 3, 0.9),   # bottom
        ]):
            for arc_i in range(arc_count):
                arm_start = spin * orbit_speed + arc_i * (math.pi * 2 / arc_count)
                arc_pts = []
                steps = 16
                arc_span = math.pi * 0.5
                for i in range(steps + 1):
                    a = arm_start + arc_span * i / steps
                    px = center[0] + int(math.cos(a) * radius)
                    py = center[1] + y_off + int(math.sin(a) * radius * 0.32)
                    arc_pts.append((px, py))

                for layer_i, (r_off, thick, color, a_mult) in enumerate([
                    (3, 9, _NS_wiro.PALETTE["wind_darkest"], 0.6),
                    (2, 7, _NS_wiro.PALETTE["wind_dark"], 0.8),
                    (0, 5, _NS_wiro.PALETTE["wind_mid"], 1.0),
                    (-1, 3, _NS_wiro.PALETTE["wind_light"], 1.0),
                    (-2, 2, _NS_wiro.PALETTE["wind_hot"], 1.0),
                ]):
                    for k in range(len(arc_pts) - 1):
                        fade_k = 1 - (k / len(arc_pts))
                        alpha_val = _NS_wiro._alpha(240 * a_mult * fade_k)
                        if alpha_val <= 0:
                            continue
                        pygame.draw.line(whirl_surf,
                                         _NS_wiro._rgba(color, alpha_val),
                                         arc_pts[k], arc_pts[k + 1], thick)

                # Bright tip
                if arc_pts:
                    tip = arc_pts[-1]
                    pygame.draw.rect(whirl_surf,
                                     _NS_wiro._rgba(_NS_wiro.PALETTE["wind_shine"], 255),
                                     (tip[0], tip[1], 3, 3))
                    pygame.draw.rect(whirl_surf,
                                     _NS_wiro._rgba(_NS_wiro.PALETTE["white"], 255),
                                     (tip[0], tip[1], 1, 1))

        # Sparkles flying out
        for i in range(25):
            angle = spin * 0.3 + i * math.pi / 12
            r_p = 60 + int(math.sin(phase + i) * 15)
            y_off = int(math.sin(phase * 0.8 + i) * 12)
            px = center[0] + int(math.cos(angle) * r_p)
            py = center[1] + y_off + int(math.sin(angle) * r_p * 0.32)
            alpha = _NS_wiro._alpha(230)
            pygame.draw.rect(whirl_surf,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_light"], alpha),
                (px, py, 2, 2))
            pygame.draw.rect(whirl_surf,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_shine"], alpha),
                (px, py, 1, 1))

        surface.blit(whirl_surf, (x - 140, y - 140))

    # ============================================================
    # SKILL E: SWORD DASH
    # ============================================================
    def _draw_dash_ground(surface, boss, x, y, timer, phase):
        """Landing marker at destination."""
        tx, ty = _NS_wiro._target_position(boss, x, y)
        duration = 35
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress > 0.75:
            t = (progress - 0.75) / 0.25
            end_x = int(x + (tx - x) * 0.9)
            end_y = int(y + (ty - y) * 0.9)
            r = int(35 * t)
            alpha = _NS_wiro._alpha(240 * (1 - t))
            pygame.draw.ellipse(surface,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_darkest"], alpha),
                (end_x - r, end_y + 42 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_hot"], alpha),
                (end_x - r + 4, end_y + 42 - r // 3 + 3,
                 r * 2 - 8, r * 2 // 3 - 6), 1)

    def _draw_dash_fg(surface, boss, x, y, timer, pulse):
        """Dash streak trail like light."""
        duration = 35
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_wiro._target_position(boss, x, y)
        facing = boss.direction

        if progress < 0.75:
            t = progress / 0.75
            t_ease = 1 - (1 - t) ** 3

            end_x = int(x + (tx - x) * t_ease * 0.9)
            end_y = int(y + (ty - y) * t_ease * 0.9)

            # Multi-layer streak line
            for thick, color, a_mult in [
                (12, _NS_wiro.PALETTE["wind_darkest"], 0.4),
                (9, _NS_wiro.PALETTE["wind_dark"], 0.6),
                (6, _NS_wiro.PALETTE["wind_mid"], 0.8),
                (4, _NS_wiro.PALETTE["wind_light"], 1.0),
                (2, _NS_wiro.PALETTE["wind_hot"], 1.0),
                (1, _NS_wiro.PALETTE["wind_shine"], 1.0),
            ]:
                alpha = _NS_wiro._alpha(240 * a_mult * (1 - t * 0.3))
                pygame.draw.line(surface,
                    _NS_wiro._rgba(color, alpha),
                    (x + facing * 15, y - 6),
                    (end_x, end_y), thick)

            # Bright leading tip
            for r in range(10, 0, -1):
                alpha = _NS_wiro._alpha(200 * (10 - r) / 10)
                _NS_wiro._aacircle(surface,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_light"], alpha),
                    (end_x, end_y), r)
            _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["wind_hot"],
                                (end_x, end_y), 4)
            _NS_wiro._aacircle(surface, _NS_wiro.PALETTE["wind_shine"],
                                (end_x, end_y), 2)
            pygame.draw.rect(surface, _NS_wiro.PALETTE["white"], (end_x, end_y, 1, 1))

    # ============================================================
    # SKILL R: TYPHOON (massive tornado)
    # ============================================================
    def _draw_typhoon_ground(surface, boss, x, y, timer, phase):
        """Ground vortex."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Growing then stable then fading vortex
        if progress < 0.2:
            scale = progress / 0.2
        elif progress > 0.8:
            scale = (1 - progress) / 0.2
        else:
            scale = 1.0

        r = int(70 * scale + math.sin(phase * 3) * 5)
        if r < 5:
            return

        alpha = _NS_wiro._alpha(240)
        pygame.draw.ellipse(surface,
            _NS_wiro._rgba(_NS_wiro.PALETTE["wind_darkest"], alpha),
            (x - r, y + 44 - r // 3, r * 2, r * 2 // 3), 4)
        pygame.draw.ellipse(surface,
            _NS_wiro._rgba(_NS_wiro.PALETTE["wind_dark"], alpha),
            (x - r + 5, y + 44 - r // 3 + 4,
             r * 2 - 10, r * 2 // 3 - 8), 3)
        pygame.draw.ellipse(surface,
            _NS_wiro._rgba(_NS_wiro.PALETTE["wind_mid"], alpha),
            (x - r + 12, y + 44 - r // 3 + 8,
             r * 2 - 24, r * 2 // 3 - 16), 2)
        pygame.draw.ellipse(surface,
            _NS_wiro._rgba(_NS_wiro.PALETTE["wind_hot"], alpha),
            (x - r + 20, y + 44 - r // 3 + 12,
             r * 2 - 40, r * 2 // 3 - 24), 1)

        # Ground debris spiraling toward center (knock up effect)
        for i in range(16):
            angle = phase * 3 + i * math.pi / 8
            drift_r = r * (0.4 + (i % 3) * 0.2)
            dx = x + int(math.cos(angle) * drift_r)
            dy = y + 44 + int(math.sin(angle) * drift_r * 0.4)
            pygame.draw.rect(surface, _NS_wiro.PALETTE["wind_light"], (dx, dy, 2, 2))
            pygame.draw.rect(surface, _NS_wiro.PALETTE["wind_shine"], (dx, dy, 1, 1))

    def _draw_typhoon_fg(surface, boss, x, y, timer, phase):
        """Massive tornado with multiple spiraling wind bands."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Scale factor (grow-stable-shrink)
        if progress < 0.15:
            scale = progress / 0.15
        elif progress > 0.85:
            scale = (1 - progress) / 0.15
        else:
            scale = 1.0

        if scale < 0.05:
            return

        # Tornado - draw multiple spiraling bands
        # Bottom wider, top narrower (cone shape)
        typhoon_surf = pygame.Surface((240, 320), pygame.SRCALPHA)
        center_x = 120

        # Cone parameters
        cone_top_y = 30
        cone_bot_y = 280
        top_radius = int(35 * scale)
        bot_radius = int(70 * scale)

        # Draw multiple horizontal wind bands (arcs) at different heights
        num_bands = 12
        for band_i in range(num_bands):
            band_t = band_i / (num_bands - 1)
            band_y = int(cone_top_y + (cone_bot_y - cone_top_y) * band_t)
            band_radius = int(top_radius + (bot_radius - top_radius) * band_t)

            # Band rotation offset (spiral effect)
            band_spin = phase * 4 + band_t * math.pi * 2.5

            # Draw partial ellipse arc (2 arms per band to show spinning)
            for arc_i in range(2):
                arm_start = band_spin + arc_i * math.pi
                arc_pts = []
                steps = 20
                arc_span = math.pi * 0.85
                for i in range(steps + 1):
                    a = arm_start + arc_span * i / steps
                    px = center_x + int(math.cos(a) * band_radius)
                    py = band_y + int(math.sin(a) * band_radius * 0.28)
                    arc_pts.append((px, py))

                for layer_i, (thick, color, a_mult) in enumerate([
                    (7, _NS_wiro.PALETTE["wind_darkest"], 0.5),
                    (5, _NS_wiro.PALETTE["wind_dark"], 0.7),
                    (3, _NS_wiro.PALETTE["wind_mid"], 0.9),
                    (2, _NS_wiro.PALETTE["wind_light"], 1.0),
                    (1, _NS_wiro.PALETTE["wind_hot"], 1.0),
                ]):
                    for k in range(len(arc_pts) - 1):
                        fade_k = 1 - (k / len(arc_pts))
                        alpha = _NS_wiro._alpha(230 * a_mult * fade_k)
                        if alpha <= 0:
                            continue
                        pygame.draw.line(typhoon_surf,
                                         _NS_wiro._rgba(color, alpha),
                                         arc_pts[k], arc_pts[k + 1], thick)

        # Vertical rising streaks (wind updraft)
        for i in range(10):
            streak_t = (phase * 0.5 + i * 0.1) % 1.0
            streak_angle = phase * 2 + i * math.pi / 5
            streak_x = center_x + int(math.cos(streak_angle) * bot_radius * 0.7)
            streak_y_start = cone_bot_y - int(streak_t * (cone_bot_y - cone_top_y))
            streak_len = 20
            alpha = _NS_wiro._alpha(200 * (1 - streak_t) * scale)
            if alpha > 0:
                pygame.draw.line(typhoon_surf,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_light"], alpha),
                    (streak_x, streak_y_start),
                    (streak_x, streak_y_start - streak_len), 2)
                pygame.draw.line(typhoon_surf,
                    _NS_wiro._rgba(_NS_wiro.PALETTE["wind_hot"], alpha),
                    (streak_x, streak_y_start),
                    (streak_x, streak_y_start - streak_len), 1)

        # Debris/leaves swirling
        for i in range(20):
            deb_t = (phase * 0.6 + i * 0.08) % 1.0
            deb_y = int(cone_bot_y - deb_t * (cone_bot_y - cone_top_y))
            deb_r_at_y = int(top_radius + (bot_radius - top_radius) * (1 - deb_t))
            deb_angle = phase * 5 + i * math.pi / 10
            deb_x = center_x + int(math.cos(deb_angle) * deb_r_at_y * 0.9)
            alpha = _NS_wiro._alpha(240 * scale)
            pygame.draw.rect(typhoon_surf,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_light"], alpha),
                (deb_x, deb_y, 3, 3))
            pygame.draw.rect(typhoon_surf,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_shine"], alpha),
                (deb_x, deb_y, 2, 2))
            pygame.draw.rect(typhoon_surf,
                _NS_wiro._rgba(_NS_wiro.PALETTE["white"], alpha),
                (deb_x, deb_y, 1, 1))

        # Bright top swirl (peak of tornado)
        for r in range(top_radius + 4, 0, -2):
            alpha = _NS_wiro._alpha(180 * (top_radius + 4 - r) / (top_radius + 4) * scale)
            _NS_wiro._aacircle(typhoon_surf,
                _NS_wiro._rgba(_NS_wiro.PALETTE["wind_hot"], alpha),
                (center_x, cone_top_y), r)

        # Position tornado so bottom is at boss ground level
        surface.blit(typhoon_surf, (x - 120, y + 46 - cone_bot_y))


# ====================================================================
# naraka.py
# ====================================================================

# ====================================================================
# NARAKA (Errol-inspired) - The Lost Soul - TRUE BOSS
# ====================================================================


class _NS_naraka:
    """Namespace naraka - Cursed dark warrior true boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin (pale/cursed)
        "skin_darkest": (50, 45, 55),
        "skin_dark": (95, 88, 100),
        "skin_mid": (150, 138, 155),
        "skin_light": (200, 188, 205),
        "skin_shine": (235, 225, 240),

        # Hair (silver-white spiky)
        "hair_darkest": (70, 75, 90),
        "hair_dark": (125, 130, 145),
        "hair_mid": (185, 190, 205),
        "hair_light": (230, 235, 245),
        "hair_shine": (255, 255, 255),

        # Cloth pants (very dark)
        "cloth_darkest": (8, 10, 15),
        "cloth_dark": (22, 25, 32),
        "cloth_mid": (50, 55, 65),
        "cloth_light": (95, 100, 115),

        # Dark armor (near-black with cyan tint)
        "armor_darkest": (8, 12, 18),
        "armor_dark": (25, 32, 42),
        "armor_mid": (55, 70, 88),
        "armor_light": (105, 125, 150),
        "armor_shine": (170, 195, 220),

        # Chain (dark iron)
        "chain_darkest": (10, 12, 16),
        "chain_dark": (35, 40, 48),
        "chain_mid": (75, 82, 92),
        "chain_light": (130, 140, 155),
        "chain_shine": (190, 200, 215),

        # CYAN energy (main FX - bright teal)
        "cyan_darkest": (5, 40, 60),
        "cyan_dark": (15, 100, 140),
        "cyan_mid": (55, 190, 230),
        "cyan_light": (130, 235, 255),
        "cyan_hot": (200, 250, 255),
        "cyan_shine": (240, 255, 255),

        # Eye glow (bright cyan)
        "eye_dark": (10, 65, 100),
        "eye_mid": (60, 200, 240),
        "eye_light": (170, 245, 255),
        "eye_glow": (240, 255, 255),

        # Dark aura purple (secondary)
        "dark_darkest": (12, 8, 25),
        "dark_dark": (30, 20, 55),
        "dark_mid": (65, 45, 100),
        "dark_light": (120, 90, 175),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 5),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _rgba(color, alpha):
        return (max(0, min(255, int(color[0]))),
                max(0, min(255, int(color[1]))),
                max(0, min(255, int(color[2]))),
                max(0, min(255, int(alpha))))

    def _aacircle(surface, color, center, radius, width=0):
        if len(color) == 4:
            color = (max(0, min(255, int(color[0]))),
                     max(0, min(255, int(color[1]))),
                     max(0, min(255, int(color[2]))),
                     max(0, min(255, int(color[3]))))
        else:
            color = _NS_naraka._clamp(color)
        if _NS_naraka.HAS_AACIRCLE and radius > 1:
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
            color = _NS_naraka._clamp(color)
        if _NS_naraka.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_naraka._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # dengan kompensasi scale (hero di-render di canvas lalu
            # di-scale; boss langsung di layar scale=1).
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return int(x + 260 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_naraka(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_naraka._detect_moving(boss)
        _NS_naraka._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_nrk_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        _NS_naraka._draw_dark_aura(surface, x, y, pulse)
        _NS_naraka._draw_ground_ring(surface, x, y + 70, pulse, active_skill)

        # Skill ground FX
        if active_skill == "w":
            _NS_naraka._draw_shadowstep_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_naraka._draw_chainhammer_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_naraka._draw_execution_ground(surface, boss, x, y, skill_timer, pulse)

        # BODY
        if active_skill == "w":
            _NS_naraka._draw_shadowstep_body(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_naraka._draw_execution_body(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_naraka._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_naraka._draw_float_move(surface, boss, x, y)
        else:
            _NS_naraka._draw_idle(surface, boss, x, y)

        # Foreground FX
        if active_skill == "q":
            _NS_naraka._draw_chaosstrike_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_naraka._draw_chainhammer_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_naraka._draw_execution_fg(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_nrk_previous_timer", 0))
        active = bool(getattr(boss, "_nrk_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._nrk_attack_active = True
            boss._nrk_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._nrk_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._nrk_attack_frame = int(getattr(boss, "_nrk_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._nrk_attack_active = False
            boss._nrk_attack_frame = 0
            active = False

        boss._nrk_previous_timer = timer
        boss._nrk_attack_progress = (
            min(1.0, getattr(boss, "_nrk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_nrk_last_x"):
            boss._nrk_last_x = boss.x
            boss._nrk_last_y = boss.y
            return False
        dx = abs(boss.x - boss._nrk_last_x)
        dy = abs(boss.y - boss._nrk_last_y)
        boss._nrk_last_x = boss.x
        boss._nrk_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        float_bob = int(math.sin(boss.pulse * 0.5) * 7)
        float_sway = int(math.sin(boss.pulse * 0.35) * 3)
        _NS_naraka._draw_shadow_float(surface, x, y + 74, boss.pulse, intensity=1.0)
        _NS_naraka._draw_cyan_wisps(surface, x, y + 66, boss.pulse, intensity=1.0)
        _NS_naraka._draw_floating_chains(surface, x, y, boss.pulse, boss.direction, intensity=1.0)
        _NS_naraka._draw_body(surface, x + float_sway, y + float_bob,
                               boss.direction, boss.pulse, "idle")

    def _draw_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.7
        float_bob = int(math.sin(phase * 0.7) * 6)
        float_sway = int(math.sin(phase * 0.5) * 3)
        _NS_naraka._draw_shadow_float(surface, x + float_sway, y + 74, phase,
                                       intensity=0.85)
        _NS_naraka._draw_cyan_wisps(surface, x + float_sway, y + 66, phase,
                                     intensity=1.6, trail=True, facing=boss.direction)
        _NS_naraka._draw_floating_chains(surface, x + float_sway, y, phase,
                                          boss.direction, intensity=1.3, moving=True)
        _NS_naraka._draw_body(surface, x + float_sway, y + float_bob,
                               boss.direction, phase, "float")

    def _draw_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_nrk_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        # Arah terkunci saat serangan dimulai (lihat
        # _update_attack_anim). Fallback ke arah live.
        facing = getattr(boss, "_nrk_attack_dir", None)
        if facing is None:
            facing = boss.direction

        if progress < 0.2:
            t = progress / 0.2
            lunge = -int(t * 5) * boss.direction
            lift = int(t * 3)
            float_bob = int(math.sin(boss.pulse * 0.5) * 4)
        elif progress < 0.4:
            t = (progress - 0.2) / 0.2
            t_ease = 1 - (1 - t) ** 2
            lunge = int((-5 + t_ease * 22)) * boss.direction
            lift = int(3 - t_ease * 5)
            float_bob = 0
        else:
            t = (progress - 0.4) / 0.6
            lunge = int(17 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
            float_bob = int(math.sin(boss.pulse * 0.5) * 4 * t)

        _NS_naraka._draw_shadow_float(surface, x + lunge, y + 74, boss.pulse,
                                       intensity=0.9)
        _NS_naraka._draw_cyan_wisps(surface, x + lunge, y + 66, boss.pulse,
                                     intensity=1.4)
        _NS_naraka._draw_floating_chains(surface, x + lunge, y, boss.pulse,
                                          boss.direction, intensity=1.5, moving=True)
        _NS_naraka._draw_body(surface, x + lunge, y - lift + float_bob,
                               boss.direction, boss.pulse, "attack", progress)
        _NS_naraka._draw_energy_slash(surface, boss, x + lunge,
                                       y - lift + float_bob, progress)

    def _draw_shadowstep_body(surface, boss, x, y, timer, phase):
        """Shadow Step - fade dash to target."""
        duration = 30
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_naraka._target_position(boss, x, y)

        if progress < 0.3:
            # Fading out from origin
            alpha_t = 1.0 - progress / 0.3
            _NS_naraka._draw_shadow_float(surface, x, y + 74, phase, intensity=alpha_t)
            body_surf = pygame.Surface((240, 240), pygame.SRCALPHA)
            _NS_naraka._draw_body(body_surf, 120, 120, boss.direction, phase, "idle")
            body_surf.set_alpha(int(255 * alpha_t))
            surface.blit(body_surf, (x - 120, y - 120))
        elif progress < 0.6:
            # Traveling (shadow trail)
            t = (progress - 0.3) / 0.3
            _NS_naraka._draw_shadow_trail(surface, x, y, tx, ty, t, boss.direction, phase)
        else:
            # Reappearing behind target
            alpha_t = (progress - 0.6) / 0.4
            behind_x = tx - boss.direction * 50
            behind_y = ty
            _NS_naraka._draw_shadow_float(surface, behind_x, behind_y + 74, phase,
                                           intensity=alpha_t)
            _NS_naraka._draw_cyan_wisps(surface, behind_x, behind_y + 66, phase,
                                         intensity=1.5 * alpha_t)
            body_surf = pygame.Surface((240, 240), pygame.SRCALPHA)
            _NS_naraka._draw_body(body_surf, 120, 120, boss.direction, phase, "attack",
                                    attack_progress=0.35)
            body_surf.set_alpha(int(255 * alpha_t))
            surface.blit(body_surf, (behind_x - 120, behind_y - 120))

    def _draw_execution_body(surface, boss, x, y, timer, phase):
        """Execution Mode - transformation + powered up."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        float_bob = int(math.sin(progress * math.pi * 4) * -5)
        # Higher levitation
        levitation = int(progress * 6)

        _NS_naraka._draw_shadow_float(surface, x, y + 74, phase, intensity=0.75)
        _NS_naraka._draw_cyan_wisps(surface, x, y + 66, phase, intensity=2.0)
        _NS_naraka._draw_floating_chains(surface, x, y, phase, boss.direction,
                                          intensity=2.0, moving=True)
        _NS_naraka._draw_body(surface, x, y + float_bob - levitation,
                               boss.direction, phase, "execution",
                               attack_progress=progress)

    # ============================================================
    # BODY (Cursed warrior)
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0,
                    spin_angle=0):
        """Draw cursed warrior body."""
        # Legs
        _NS_naraka._draw_legs(surface, cx, cy + 24, facing, phase, action, attack_progress)

        # Belt
        _NS_naraka._draw_waist(surface, cx, cy + 8, facing, phase)

        # Torso
        _NS_naraka._draw_torso(surface, cx, cy - 8, facing, phase, action)

        # Back arm with dangling chain
        _NS_naraka._draw_arm_back(surface, cx, cy - 6, facing, phase, action,
                                    attack_progress)

        # Head with spiky hair
        _NS_naraka._draw_head(surface, cx, cy - 26, facing, phase, action, attack_progress)

        # Front arm with energy blade
        _NS_naraka._draw_arm_front(surface, cx, cy - 6, facing, phase, action,
                                     attack_progress)

    def _draw_legs(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Legs dangling in float."""
        if action in ("idle", "float", "execution"):
            sway = math.sin(phase * 0.6) * 1
            bx = cx - 5 + int(sway)
            by = cy - 1
            _NS_naraka._draw_leg_float(surface, bx, by, facing, back=True, phase=phase)
            fx = cx + 5 - int(sway)
            fy = cy
            _NS_naraka._draw_leg_float(surface, fx, fy, facing, back=False, phase=phase)
        elif action == "attack" and attack_progress < 0.4:
            bx = cx - 6
            by = cy
            _NS_naraka._draw_leg(surface, bx, by, facing, back=True)
            fx = cx + 6
            fy = cy
            _NS_naraka._draw_leg(surface, fx, fy, facing, back=False)
        else:
            bx = cx - 5
            by = cy - 1
            _NS_naraka._draw_leg_float(surface, bx, by, facing, back=True, phase=phase)
            fx = cx + 5
            fy = cy - 1
            _NS_naraka._draw_leg_float(surface, fx, fy, facing, back=False, phase=phase)

    def _draw_leg_float(surface, cx, cy, facing, back=False, phase=0):
        """Floating leg with cyan wisp."""
        # Thigh (dark cloth pants)
        pygame.draw.rect(surface, _NS_naraka.PALETTE["shadow_deep"],
                         (cx - 4, cy - 10, 9, 12))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["cloth_darkest"],
                         (cx - 4, cy - 10, 8, 11))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["cloth_dark"],
                         (cx - 3, cy - 10, 6, 10))
        if not back:
            pygame.draw.rect(surface, _NS_naraka.PALETTE["cloth_mid"],
                             (cx - 2, cy - 9, 3, 7))

        # Chain wrap around thigh
        for chain_y in (cy - 6, cy - 2):
            pygame.draw.rect(surface, _NS_naraka.PALETTE["chain_darkest"],
                             (cx - 4, chain_y, 8, 2))
            pygame.draw.rect(surface, _NS_naraka.PALETTE["chain_dark"],
                             (cx - 4, chain_y, 7, 1))
            if not back:
                for link_x in (cx - 3, cx - 1, cx + 1, cx + 3):
                    pygame.draw.rect(surface, _NS_naraka.PALETTE["chain_mid"],
                                     (link_x, chain_y, 1, 1))
                    pygame.draw.rect(surface, _NS_naraka.PALETTE["chain_light"],
                                     (link_x, chain_y, 1, 1))

        # Lower leg (dark cloth)
        pygame.draw.rect(surface, _NS_naraka.PALETTE["shadow_deep"],
                         (cx - 3, cy + 2, 7, 8))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["cloth_darkest"],
                         (cx - 3, cy + 2, 6, 7))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["cloth_dark"],
                         (cx - 2, cy + 2, 4, 6))

        # Boot (dark armored)
        pygame.draw.rect(surface, _NS_naraka.PALETTE["shadow_deep"],
                         (cx - 4, cy + 9, 9, 5))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["armor_darkest"],
                         (cx - 4, cy + 9, 8, 4))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["armor_dark"],
                         (cx - 3, cy + 9, 6, 3))
        if not back:
            pygame.draw.rect(surface, _NS_naraka.PALETTE["armor_mid"],
                             (cx - 3, cy + 9, 5, 2))
            pygame.draw.rect(surface, _NS_naraka.PALETTE["armor_light"],
                             (cx - 2, cy + 9, 3, 1))

        # Cyan crystal on boot (glowing)
        if not back:
            crystal_pulse = math.sin(phase * 2) * 0.3 + 0.7
            for r in range(3, 0, -1):
                alpha = _NS_naraka._alpha(150 * (3 - r) / 3 * crystal_pulse)
                _NS_naraka._aacircle(surface,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_mid"], alpha),
                    (cx, cy + 11), r)
            pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_light"],
                             (cx, cy + 11, 1, 1))
            pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_shine"],
                             (cx, cy + 11, 1, 1))

        # CYAN WISP under boot
        wisp_t = (phase * 0.8 + cx * 0.1) % 1.0
        wy = cy + 14 + int(wisp_t * 8)
        alpha = _NS_naraka._alpha(200 * (1 - wisp_t))
        if alpha > 0 and not back:
            _NS_naraka._aacircle(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_dark"], alpha),
                (cx, wy), 3)
            _NS_naraka._aacircle(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_mid"], alpha),
                (cx, wy), 2)
            _NS_naraka._aacircle(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_light"], alpha),
                (cx, wy), 1)
            pygame.draw.rect(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_hot"], alpha),
                (cx, wy, 1, 1))

    def _draw_leg(surface, cx, cy, facing, back=False):
        """Planted leg."""
        pygame.draw.rect(surface, _NS_naraka.PALETTE["shadow_deep"],
                         (cx - 4, cy - 10, 9, 12))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["cloth_darkest"],
                         (cx - 4, cy - 10, 8, 11))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["cloth_dark"],
                         (cx - 3, cy - 10, 6, 10))
        if not back:
            pygame.draw.rect(surface, _NS_naraka.PALETTE["cloth_mid"],
                             (cx - 2, cy - 9, 3, 7))

        # Chain wrap
        pygame.draw.rect(surface, _NS_naraka.PALETTE["chain_darkest"],
                         (cx - 4, cy - 4, 8, 2))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["chain_dark"],
                         (cx - 4, cy - 4, 7, 1))

        # Lower leg
        pygame.draw.rect(surface, _NS_naraka.PALETTE["shadow_deep"],
                         (cx - 3, cy + 2, 7, 7))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["cloth_darkest"],
                         (cx - 3, cy + 2, 6, 6))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["cloth_dark"],
                         (cx - 2, cy + 2, 4, 5))

        # Boot
        pygame.draw.rect(surface, _NS_naraka.PALETTE["shadow_deep"],
                         (cx - 4, cy + 8, 9, 5))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["armor_darkest"],
                         (cx - 4, cy + 8, 8, 4))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["armor_dark"],
                         (cx - 3, cy + 8, 6, 3))
        if not back:
            pygame.draw.rect(surface, _NS_naraka.PALETTE["armor_mid"],
                             (cx - 3, cy + 8, 5, 2))

    def _draw_waist(surface, cx, cy, facing, phase):
        """Belt with chains hanging."""
        pygame.draw.rect(surface, _NS_naraka.PALETTE["shadow_deep"],
                         (cx - 12, cy - 3, 25, 5))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["armor_darkest"],
                         (cx - 12, cy - 3, 24, 5))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["armor_dark"],
                         (cx - 12, cy - 3, 24, 4))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["armor_mid"],
                         (cx - 11, cy - 2, 22, 2))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["armor_light"],
                         (cx - 10, cy - 2, 5, 1))

        # Central buckle with cyan crystal
        pygame.draw.rect(surface, _NS_naraka.PALETTE["shadow_deep"],
                         (cx - 4, cy - 3, 9, 6))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["armor_darkest"],
                         (cx - 4, cy - 3, 8, 5))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["armor_dark"],
                         (cx - 3, cy - 3, 7, 4))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["armor_mid"],
                         (cx - 3, cy - 3, 5, 3))

        # Cyan crystal center
        gem_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_naraka._alpha(160 * (4 - r) / 4 * gem_pulse)
            _NS_naraka._aacircle(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_mid"], alpha),
                (cx, cy - 1), r)
        pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_dark"],
                         (cx - 1, cy - 2, 3, 3))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_mid"],
                         (cx, cy - 2, 2, 2))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_light"],
                         (cx, cy - 2, 1, 1))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["white"],
                         (cx, cy - 2, 1, 1))

    def _draw_torso(surface, cx, cy, facing, phase, action):
        """Dark armored torso with cyan crystals."""
        breath = math.sin(phase * 0.6) * 1

        # Torso shape (larger for TRUE BOSS)
        torso_pts = [
            (cx - 11, cy - 4),
            (cx - 12, cy + 4),
            (cx - 10, cy + 12),
            (cx + 10, cy + 12),
            (cx + 12, cy + 4),
            (cx + 11, cy - 4),
            (cx + 7, cy - 8),
            (cx - 7, cy - 8),
        ]
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["shadow_deep"],
                          [(px + 2, py + 2) for px, py in torso_pts])
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["armor_darkest"], torso_pts)

        # Main armor
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["armor_dark"], [
            (cx - 10, cy - 3 + int(breath)),
            (cx - 11, cy + 4),
            (cx - 9, cy + 11),
            (cx + 9, cy + 11),
            (cx + 11, cy + 4),
            (cx + 10, cy - 3 + int(breath)),
            (cx + 6, cy - 7),
            (cx - 6, cy - 7),
        ])

        # Highlight
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["armor_mid"], [
            (cx - 7, cy - 2 + int(breath)),
            (cx - 9, cy + 4),
            (cx - 6, cy + 10),
            (cx + 6, cy + 10),
            (cx + 9, cy + 4),
            (cx + 7, cy - 2 + int(breath)),
            (cx + 4, cy - 6),
            (cx - 4, cy - 6),
        ])

        # Bright chest plate
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["armor_light"], [
            (cx - 3, cy + int(breath)),
            (cx + 3, cy + int(breath)),
            (cx + 3, cy + 7),
            (cx - 3, cy + 7),
        ])
        pygame.draw.rect(surface, _NS_naraka.PALETTE["armor_shine"],
                         (cx - 2, cy + 2 + int(breath), 3, 2))

        # BIG CYAN CRYSTAL on chest (main power source)
        crystal_pulse = math.sin(phase * 2) * 0.3 + 0.7
        gy = cy + 4
        # Halo
        for r in range(6, 0, -1):
            alpha = _NS_naraka._alpha(180 * (6 - r) / 6 * crystal_pulse)
            _NS_naraka._aacircle(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_mid"], alpha),
                (cx, gy), r)
        # Crystal diamond shape
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["shadow_deep"], [
            (cx + 1, gy - 4 + 1),
            (cx - 3 + 1, gy + 1),
            (cx + 1, gy + 4 + 1),
            (cx + 3 + 1, gy + 1),
        ])
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["cyan_darkest"], [
            (cx, gy - 4),
            (cx - 3, gy),
            (cx, gy + 4),
            (cx + 3, gy),
        ])
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["cyan_dark"], [
            (cx, gy - 3),
            (cx - 2, gy),
            (cx, gy + 3),
            (cx + 2, gy),
        ])
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["cyan_mid"], [
            (cx, gy - 2),
            (cx - 1, gy),
            (cx, gy + 2),
            (cx + 1, gy),
        ])
        pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_light"], (cx, gy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_shine"], (cx, gy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["white"], (cx, gy - 1, 1, 1))

        # Diagonal armor plate lines
        pygame.draw.line(surface, _NS_naraka.PALETTE["armor_darkest"],
                         (cx - 8, cy + int(breath)), (cx - 6, cy + 10), 1)
        pygame.draw.line(surface, _NS_naraka.PALETTE["armor_darkest"],
                         (cx + 8, cy + int(breath)), (cx + 6, cy + 10), 1)

        # SHOULDER PAULDRONS with cyan crystal spikes
        for side_sign in (-1, 1):
            sx = cx + side_sign * 11
            _NS_naraka._draw_shoulder_crystal(surface, sx, cy - 6, side_sign, phase)

    def _draw_shoulder_crystal(surface, cx, cy, side_sign, phase):
        """Shoulder pauldron with cyan crystal spikes."""
        # Base pauldron
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["shadow_deep"], [
            (cx - 4 + 1, cy + 1),
            (cx - 5 + 1, cy + 4 + 1),
            (cx - 2 + 1, cy + 6 + 1),
            (cx + 5 + 1, cy + 4 + 1),
            (cx + 4 + 1, cy + 1),
        ])
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["armor_darkest"], [
            (cx - 4, cy),
            (cx - 5, cy + 4),
            (cx - 2, cy + 6),
            (cx + 5, cy + 4),
            (cx + 4, cy),
        ])
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["armor_dark"], [
            (cx - 3, cy + 1),
            (cx - 4, cy + 4),
            (cx - 1, cy + 5),
            (cx + 4, cy + 4),
            (cx + 3, cy + 1),
        ])
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["armor_mid"], [
            (cx - 2, cy + 2),
            (cx - 3, cy + 4),
            (cx, cy + 4),
            (cx + 3, cy + 4),
            (cx + 2, cy + 2),
        ])

        # 2 CYAN CRYSTAL SPIKES pointing up
        crystal_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for x_off in (-2, 2):
            sp_x = cx + x_off
            sp_top_y = cy - 6
            sp_base_y = cy
            # Glow
            for r in range(4, 0, -1):
                alpha = _NS_naraka._alpha(140 * (4 - r) / 4 * crystal_pulse)
                _NS_naraka._aacircle(surface,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_mid"], alpha),
                    (sp_x, sp_top_y + 2), r)
            # Crystal spike shape
            _NS_naraka._poly(surface, _NS_naraka.PALETTE["shadow_deep"], [
                (sp_x + 1, sp_top_y + 1),
                (sp_x - 2 + 1, sp_base_y + 1),
                (sp_x + 2 + 1, sp_base_y + 1),
            ])
            _NS_naraka._poly(surface, _NS_naraka.PALETTE["cyan_darkest"], [
                (sp_x, sp_top_y),
                (sp_x - 2, sp_base_y),
                (sp_x + 2, sp_base_y),
            ])
            _NS_naraka._poly(surface, _NS_naraka.PALETTE["cyan_dark"], [
                (sp_x, sp_top_y),
                (sp_x - 1, sp_base_y),
                (sp_x + 1, sp_base_y),
            ])
            _NS_naraka._poly(surface, _NS_naraka.PALETTE["cyan_mid"], [
                (sp_x, sp_top_y),
                (sp_x, sp_base_y),
                (sp_x + 1, sp_base_y),
            ])
            pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_light"],
                             (sp_x, sp_top_y, 1, 2))
            pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_shine"],
                             (sp_x, sp_top_y, 1, 1))
            pygame.draw.rect(surface, _NS_naraka.PALETTE["white"],
                             (sp_x, sp_top_y, 1, 1))

    def _draw_arm_back(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm with dangling chain."""
        base_x = cx - facing * 10
        base_y = cy

        if action == "attack":
            if attack_progress < 0.2:
                arm_angle = -0.5
            elif attack_progress < 0.4:
                t = (attack_progress - 0.2) / 0.2
                arm_angle = -0.5 + t * 0.7
            else:
                arm_angle = 0.2
        elif action == "execution":
            arm_angle = -0.4 + math.sin(phase * 2) * 0.15
        else:
            arm_angle = -0.1 + math.sin(phase * 0.6) * 0.08

        elbow_x = base_x - facing * int(4 + math.cos(arm_angle) * 3)
        elbow_y = base_y + int(5 + math.sin(arm_angle) * 3)
        hand_x = elbow_x + facing * int(2 + math.cos(arm_angle + 0.4) * 3)
        hand_y = elbow_y + int(6 + math.sin(arm_angle + 0.4) * 3)

        # Upper arm (armored)
        _NS_naraka._aaline(surface, _NS_naraka.PALETTE["shadow_deep"],
                            (base_x + 1, base_y + 1), (elbow_x + 1, elbow_y + 1), 7)
        _NS_naraka._aaline(surface, _NS_naraka.PALETTE["armor_darkest"],
                            (base_x, base_y), (elbow_x, elbow_y), 6)
        _NS_naraka._aaline(surface, _NS_naraka.PALETTE["armor_dark"],
                            (base_x, base_y), (elbow_x, elbow_y), 5)
        _NS_naraka._aaline(surface, _NS_naraka.PALETTE["armor_mid"],
                            (base_x, base_y - 1), (elbow_x, elbow_y - 1), 3)

        # Forearm bracer
        _NS_naraka._aaline(surface, _NS_naraka.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 6)
        _NS_naraka._aaline(surface, _NS_naraka.PALETTE["armor_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_naraka._aaline(surface, _NS_naraka.PALETTE["armor_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_naraka._aaline(surface, _NS_naraka.PALETTE["armor_mid"],
                            (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 2)

        # Cyan crystal on bracer
        mid_x = int((elbow_x + hand_x) / 2)
        mid_y = int((elbow_y + hand_y) / 2)
        crystal_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(3, 0, -1):
            alpha = _NS_naraka._alpha(140 * (3 - r) / 3 * crystal_pulse)
            _NS_naraka._aacircle(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_mid"], alpha),
                (mid_x, mid_y), r)
        pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_light"], (mid_x, mid_y, 1, 1))

        # Fist
        _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["shadow_deep"],
                              (hand_x + 1, hand_y + 1), 4)
        _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["armor_darkest"],
                              (hand_x, hand_y), 4)
        _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["armor_dark"],
                              (hand_x, hand_y), 3)
        _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["armor_mid"],
                              (hand_x - facing, hand_y - 1), 2)

        # DANGLING CHAIN from hand
        _NS_naraka._draw_hand_chain(surface, hand_x, hand_y, facing, phase)

    def _draw_hand_chain(surface, cx, cy, facing, phase):
        """Chain hanging from hand."""
        sway = math.sin(phase * 1.2) * 3
        chain_segments = 6
        prev = (cx, cy)
        for i in range(1, chain_segments + 1):
            t = i / chain_segments
            seg_x = cx + int(sway * t * 0.5)
            seg_y = cy + int(t * 12) + int(math.sin(phase * 1.5 + t) * 1)

            # Chain link
            pygame.draw.rect(surface, _NS_naraka.PALETTE["shadow_deep"],
                             (seg_x - 1 + 1, seg_y + 1, 3, 2))
            pygame.draw.rect(surface, _NS_naraka.PALETTE["chain_darkest"],
                             (seg_x - 1, seg_y, 3, 2))
            pygame.draw.rect(surface, _NS_naraka.PALETTE["chain_dark"],
                             (seg_x - 1, seg_y, 2, 2))
            pygame.draw.rect(surface, _NS_naraka.PALETTE["chain_mid"],
                             (seg_x, seg_y, 1, 1))

            prev = (seg_x, seg_y)

        # Cyan energy tip on chain
        tip_x, tip_y = prev
        for r in range(3, 0, -1):
            alpha = _NS_naraka._alpha(140 * (3 - r) / 3)
            _NS_naraka._aacircle(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_mid"], alpha),
                (tip_x, tip_y + 2), r)
        pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_light"], (tip_x, tip_y + 2, 1, 1))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_shine"], (tip_x, tip_y + 2, 1, 1))

    def _draw_arm_front(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm with ENERGY BLADE (extends from hand)."""
        base_x = cx + facing * 10
        base_y = cy

        if action == "attack":
            if attack_progress < 0.2:
                t = attack_progress / 0.2
                arm_angle = -0.3 - t * 0.8
            elif attack_progress < 0.4:
                t = (attack_progress - 0.2) / 0.2
                t_ease = 1 - (1 - t) ** 2
                arm_angle = -1.1 + t_ease * 2.6
            else:
                t = (attack_progress - 0.4) / 0.6
                arm_angle = 1.5 - t * 1.2
        elif action == "execution":
            arm_angle = 0.2 + math.sin(phase * 2) * 0.2
        else:
            arm_angle = 0.3 + math.sin(phase * 0.6 + 0.5) * 0.08

        elbow_x = base_x + facing * int(4 + math.cos(arm_angle) * 4)
        elbow_y = base_y + int(4 + math.sin(arm_angle) * 4)
        hand_x = elbow_x + facing * int(6 + math.cos(arm_angle + 0.3) * 5)
        hand_y = elbow_y + int(5 + math.sin(arm_angle + 0.3) * 6)

        # Upper arm
        _NS_naraka._aaline(surface, _NS_naraka.PALETTE["shadow_deep"],
                            (base_x + 1, base_y + 1), (elbow_x + 1, elbow_y + 1), 7)
        _NS_naraka._aaline(surface, _NS_naraka.PALETTE["armor_darkest"],
                            (base_x, base_y), (elbow_x, elbow_y), 6)
        _NS_naraka._aaline(surface, _NS_naraka.PALETTE["armor_dark"],
                            (base_x, base_y), (elbow_x, elbow_y), 5)
        _NS_naraka._aaline(surface, _NS_naraka.PALETTE["armor_mid"],
                            (base_x, base_y - 1), (elbow_x, elbow_y - 1), 3)
        _NS_naraka._aaline(surface, _NS_naraka.PALETTE["armor_light"],
                            (base_x, base_y - 2), (elbow_x, elbow_y - 2), 1)

        # Forearm bracer
        _NS_naraka._aaline(surface, _NS_naraka.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 6)
        _NS_naraka._aaline(surface, _NS_naraka.PALETTE["armor_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_naraka._aaline(surface, _NS_naraka.PALETTE["armor_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_naraka._aaline(surface, _NS_naraka.PALETTE["armor_mid"],
                            (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 2)

        # Cyan crystal on bracer (bright)
        mid_x = int((elbow_x + hand_x) / 2)
        mid_y = int((elbow_y + hand_y) / 2)
        crystal_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_naraka._alpha(180 * (4 - r) / 4 * crystal_pulse)
            _NS_naraka._aacircle(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_mid"], alpha),
                (mid_x, mid_y), r)
        pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_light"], (mid_x, mid_y, 1, 1))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_shine"], (mid_x, mid_y, 1, 1))

        # Fist
        _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["shadow_deep"],
                              (hand_x + 1, hand_y + 1), 4)
        _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["armor_darkest"],
                              (hand_x, hand_y), 4)
        _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["armor_dark"],
                              (hand_x, hand_y), 3)
        _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["armor_mid"],
                              (hand_x - facing, hand_y - 1), 2)

        # ENERGY BLADE (extends from fist)
        if action == "attack":
            if attack_progress < 0.2:
                blade_angle = (-math.pi * 0.2 - (attack_progress / 0.2) * 0.6) * facing
            elif attack_progress < 0.4:
                t = (attack_progress - 0.2) / 0.2
                t_ease = 1 - (1 - t) ** 2
                start_a = -math.pi * 0.8 * facing
                end_a = math.pi * 0.7 * facing
                blade_angle = start_a + (end_a - start_a) * t_ease
            else:
                blade_angle = math.pi * 0.5 * facing
        elif action == "execution":
            blade_angle = math.pi * 0.15 * facing + math.sin(phase * 2) * 0.1
        else:
            blade_angle = math.pi * 0.15 * facing + math.sin(phase * 0.5) * 0.05

        _NS_naraka._draw_energy_blade(surface, hand_x, hand_y, facing, blade_angle,
                                        phase, action)

    def _draw_energy_blade(surface, cx, cy, facing, angle, phase, action):
        """Cyan energy blade extending from fist (thin curved crescent)."""
        blade_len = 40
        dx = math.cos(angle)
        dy = math.sin(angle)

        # Blade curves like a crescent scythe
        curve_pts = []
        segments = 12
        for i in range(segments + 1):
            t = i / segments
            r = blade_len * t
            # Curve inward
            curve = math.sin(t * math.pi) * 5
            perp_x = -dy * curve
            perp_y = dx * curve
            px = cx + int((dx * r + perp_x) * facing)
            py = cy + int(dy * r + perp_y)
            curve_pts.append((px, py))

        # Draw energy blade (thick glow + bright center)
        # Shadow (dark cyan outline)
        for i in range(len(curve_pts) - 1):
            t = i / len(curve_pts)
            thickness = int(6 * (1 - t * 0.5)) + 2

            # Wider dark glow layer
            _NS_naraka._aaline(surface, _NS_naraka.PALETTE["shadow_deep"],
                                (curve_pts[i][0] + 1, curve_pts[i][1] + 1),
                                (curve_pts[i + 1][0] + 1, curve_pts[i + 1][1] + 1),
                                thickness + 2)

        # Energy glow around blade
        glow_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
        offset_x = cx - 60
        offset_y = cy - 60

        for i in range(len(curve_pts) - 1):
            p1 = (curve_pts[i][0] - offset_x, curve_pts[i][1] - offset_y)
            p2 = (curve_pts[i + 1][0] - offset_x, curve_pts[i + 1][1] - offset_y)
            t = i / len(curve_pts)
            thickness = int(6 * (1 - t * 0.5)) + 2

            for layer_thick, color, a_mult in [
                (thickness + 4, _NS_naraka.PALETTE["cyan_darkest"], 0.4),
                (thickness + 2, _NS_naraka.PALETTE["cyan_dark"], 0.6),
                (thickness, _NS_naraka.PALETTE["cyan_mid"], 0.85),
                (max(1, thickness - 2), _NS_naraka.PALETTE["cyan_light"], 1.0),
                (max(1, thickness - 3), _NS_naraka.PALETTE["cyan_hot"], 1.0),
            ]:
                alpha_val = _NS_naraka._alpha(240 * a_mult)
                pygame.draw.line(glow_surf,
                    _NS_naraka._rgba(color, alpha_val), p1, p2, layer_thick)

            # Central white core
            pygame.draw.line(glow_surf,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_shine"], 255), p1, p2, 1)

        surface.blit(glow_surf, (offset_x, offset_y))

        # Bright tip
        tip = curve_pts[-1]
        for r in range(6, 0, -1):
            alpha = _NS_naraka._alpha(200 * (6 - r) / 6)
            _NS_naraka._aacircle(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_light"], alpha),
                tip, r)
        _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["cyan_hot"], tip, 3)
        _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["cyan_shine"], tip, 2)
        pygame.draw.rect(surface, _NS_naraka.PALETTE["white"], (tip[0], tip[1], 1, 1))

    def _draw_head(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Head with spiky white hair + glowing cyan eyes + optional mask (execution)."""
        # Neck
        pygame.draw.rect(surface, _NS_naraka.PALETTE["shadow_deep"],
                         (cx - 2, cy + 6, 5, 4))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["skin_darkest"],
                         (cx - 2, cy + 6, 4, 4))
        pygame.draw.rect(surface, _NS_naraka.PALETTE["skin_dark"],
                         (cx - 1, cy + 6, 3, 3))

        # Head shape
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
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["shadow_deep"],
                          [(px + 1, py + 1) for px, py in head_pts])
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["skin_darkest"], head_pts)

        # Skin mid tone (pale)
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["skin_dark"], [
            (cx - 5, cy - 1),
            (cx - 6, cy + 2),
            (cx - 4, cy + 5),
            (cx + 4, cy + 5),
            (cx + 6, cy + 2),
            (cx + 5, cy - 1),
            (cx + 3, cy - 4),
            (cx - 3, cy - 4),
        ])

        # Face highlight
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["skin_mid"], [
            (cx - 3, cy),
            (cx - 4, cy + 2),
            (cx - 2, cy + 4),
            (cx + 4, cy + 4),
            (cx + 5, cy + 2),
            (cx + 4, cy - 1),
            (cx + 2, cy - 3),
            (cx - 2, cy - 3),
        ])

        # Cheek highlight
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["skin_light"], [
            (cx + facing * 1, cy - 1),
            (cx + facing * 4, cy),
            (cx + facing * 3, cy + 3),
            (cx + facing * 1, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_naraka.PALETTE["skin_shine"],
                         (cx + facing * 3, cy, 1, 1))

        # SPIKY WHITE HAIR
        _NS_naraka._draw_spiky_hair(surface, cx, cy - 4, facing, phase)

        # EXECUTION MASK (only during R skill)
        if action == "execution" and attack_progress > 0.2:
            # Dark mask forming on face
            mask_alpha = min(1.0, (attack_progress - 0.2) / 0.3)
            _NS_naraka._draw_execution_mask(surface, cx, cy, facing, phase, mask_alpha)
        else:
            # Normal face - GLOWING CYAN EYES
            eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
            for eye_off in (-2, 2):
                ex = cx + eye_off
                ey = cy + 1
                # Halo
                for r in range(3, 0, -1):
                    alpha = _NS_naraka._alpha(200 * (3 - r) / 3 * eye_pulse)
                    _NS_naraka._aacircle(surface,
                        _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_mid"], alpha),
                        (ex, ey), r)
                pygame.draw.rect(surface, _NS_naraka.PALETTE["shadow_deep"],
                                 (ex - 1, ey, 3, 2))
                pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_dark"],
                                 (ex - 1, ey, 2, 1))
                pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_mid"],
                                 (ex, ey, 2, 1))
                pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_light"],
                                 (ex, ey, 1, 1))
                pygame.draw.rect(surface, _NS_naraka.PALETTE["white"],
                                 (ex, ey, 1, 1))

            # Nose
            pygame.draw.rect(surface, _NS_naraka.PALETTE["skin_darkest"],
                             (cx, cy + 2, 1, 2))
            # Grim mouth
            pygame.draw.rect(surface, _NS_naraka.PALETTE["skin_darkest"],
                             (cx - 2, cy + 4, 4, 1))

    def _draw_spiky_hair(surface, cx, cy, facing, phase):
        """Silver-white spiky hair."""
        # Base hair
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["shadow_deep"], [
            (cx - 5 + 1, cy - 1 + 1),
            (cx - 7 + 1, cy + 3 + 1),
            (cx - 3 + 1, cy + 2 + 1),
            (cx + 3 + 1, cy + 2 + 1),
            (cx + 7 + 1, cy + 3 + 1),
            (cx + 5 + 1, cy - 1 + 1),
        ])
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["hair_darkest"], [
            (cx - 5, cy - 1),
            (cx - 7, cy + 3),
            (cx - 3, cy + 2),
            (cx + 3, cy + 2),
            (cx + 7, cy + 3),
            (cx + 5, cy - 1),
        ])
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["hair_dark"], [
            (cx - 4, cy),
            (cx - 6, cy + 2),
            (cx - 2, cy + 2),
            (cx + 2, cy + 2),
            (cx + 6, cy + 2),
            (cx + 4, cy),
        ])
        _NS_naraka._poly(surface, _NS_naraka.PALETTE["hair_mid"], [
            (cx - 3, cy),
            (cx - 4, cy + 1),
            (cx + 4, cy + 1),
            (cx + 3, cy),
        ])

        # Spikes on top
        for i, (x_off, height) in enumerate([(-4, 5), (-2, 7), (0, 8), (2, 7), (4, 5)]):
            spike_h = height + int(math.sin(phase + i) * 1)
            spike_x = cx + x_off
            spike_top_y = cy - spike_h

            _NS_naraka._poly(surface, _NS_naraka.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_top_y + 1),
                (spike_x - 2 + 1, cy + 1),
                (spike_x + 2 + 1, cy + 1),
            ])
            _NS_naraka._poly(surface, _NS_naraka.PALETTE["hair_darkest"], [
                (spike_x, spike_top_y),
                (spike_x - 2, cy),
                (spike_x + 2, cy),
            ])
            _NS_naraka._poly(surface, _NS_naraka.PALETTE["hair_dark"], [
                (spike_x, spike_top_y),
                (spike_x - 1, cy),
                (spike_x + 1, cy),
            ])
            _NS_naraka._poly(surface, _NS_naraka.PALETTE["hair_mid"], [
                (spike_x, spike_top_y),
                (spike_x, cy),
                (spike_x + 1, cy),
            ])
            pygame.draw.rect(surface, _NS_naraka.PALETTE["hair_light"],
                             (spike_x, spike_top_y, 1, 2))
            pygame.draw.rect(surface, _NS_naraka.PALETTE["hair_shine"],
                             (spike_x, spike_top_y, 1, 1))

    def _draw_execution_mask(surface, cx, cy, facing, phase, alpha_mult):
        """Dark demonic mask forming during Execution Mode."""
        alpha_int = int(255 * alpha_mult)

        # Dark mask covering upper face
        mask_pts = [
            (cx - 5, cy - 2),
            (cx - 6, cy + 2),
            (cx - 4, cy + 4),
            (cx + 4, cy + 4),
            (cx + 6, cy + 2),
            (cx + 5, cy - 2),
        ]
        mask_surf = pygame.Surface((30, 20), pygame.SRCALPHA)
        # Offset for surface
        offset_x = cx - 15
        offset_y = cy - 5
        local_mask = [(p[0] - offset_x, p[1] - offset_y) for p in mask_pts]
        _NS_naraka._poly(mask_surf,
            _NS_naraka._rgba(_NS_naraka.PALETTE["armor_darkest"], alpha_int),
            local_mask)
        # Mask decoration - jagged edges
        _NS_naraka._poly(mask_surf,
            _NS_naraka._rgba(_NS_naraka.PALETTE["armor_dark"], alpha_int),
            [(p[0], p[1] + 1) for p in local_mask])
        surface.blit(mask_surf, (offset_x, offset_y))

        # BURNING CYAN EYES through mask (even brighter)
        eye_pulse = math.sin(phase * 3) * 0.3 + 0.7
        for eye_off in (-2, 2):
            ex = cx + eye_off
            ey = cy + 1
            for r in range(5, 0, -1):
                alpha = _NS_naraka._alpha(240 * (5 - r) / 5 * eye_pulse * alpha_mult)
                _NS_naraka._aacircle(surface,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_light"], alpha),
                    (ex, ey), r)
            pygame.draw.rect(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_hot"], alpha_int),
                (ex - 1, ey, 3, 2))
            pygame.draw.rect(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_shine"], alpha_int),
                (ex, ey, 2, 1))
            pygame.draw.rect(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["white"], alpha_int),
                (ex, ey, 1, 1))

        # Small horns/spikes on mask top (facing angles)
        for spike_x_off in (-3, 3):
            sp_x = cx + spike_x_off
            pygame.draw.line(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["armor_darkest"], alpha_int),
                (sp_x, cy - 2), (sp_x + spike_x_off // 2, cy - 4), 2)
            pygame.draw.rect(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_mid"], alpha_int),
                (sp_x + spike_x_off // 2, cy - 4, 1, 1))

    # ============================================================
    # FLOATING CHAINS (ambient - broken chains floating around)
    # ============================================================
    def _draw_floating_chains(surface, cx, cy, phase, facing, intensity=1.0, moving=False):
        """Broken chains floating around boss (iconic - lost soul)."""
        # 3-4 chain fragments floating in orbit around boss
        num_chains = int(3 * intensity)
        for chain_i in range(num_chains):
            base_angle = phase * 0.5 + chain_i * math.pi * 2 / num_chains
            orbit_r = 45 + int(math.sin(phase + chain_i) * 6)
            # Chain start position
            chain_start_x = cx + int(math.cos(base_angle) * orbit_r)
            chain_start_y = cy - 15 + int(math.sin(base_angle) * orbit_r * 0.4)

            # Chain direction (outward with drift)
            chain_dir_angle = base_angle + math.pi / 4 + math.sin(phase * 0.7 + chain_i) * 0.3

            # Draw chain segments
            chain_len = 5
            prev_x = chain_start_x
            prev_y = chain_start_y
            for seg_i in range(chain_len):
                t = seg_i / chain_len
                seg_x = chain_start_x + int(math.cos(chain_dir_angle) * seg_i * 4)
                seg_y = chain_start_y + int(math.sin(chain_dir_angle) * seg_i * 4)
                # Add slight sag
                seg_y += int(math.sin(t * math.pi) * 2)

                # Draw chain link
                pygame.draw.rect(surface, _NS_naraka.PALETTE["shadow_deep"],
                                 (seg_x + 1, seg_y + 1, 3, 2))
                pygame.draw.rect(surface, _NS_naraka.PALETTE["chain_darkest"],
                                 (seg_x, seg_y, 3, 2))
                pygame.draw.rect(surface, _NS_naraka.PALETTE["chain_dark"],
                                 (seg_x, seg_y, 2, 2))
                pygame.draw.rect(surface, _NS_naraka.PALETTE["chain_mid"],
                                 (seg_x + 1, seg_y, 1, 1))
                # Highlight
                if seg_i % 2 == 0:
                    pygame.draw.rect(surface, _NS_naraka.PALETTE["chain_light"],
                                     (seg_x, seg_y, 1, 1))

                # Cyan energy on some links (haunted feel)
                if seg_i == chain_len - 1:
                    for r in range(3, 0, -1):
                        alpha = _NS_naraka._alpha(140 * (3 - r) / 3)
                        _NS_naraka._aacircle(surface,
                            _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_mid"], alpha),
                            (seg_x + 1, seg_y + 1), r)
                    pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_light"],
                                     (seg_x + 1, seg_y + 1, 1, 1))
                    pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_shine"],
                                     (seg_x + 1, seg_y + 1, 1, 1))

    # ============================================================
    # SHADOW TRAIL (for Shadow Step)
    # ============================================================
    def _draw_shadow_trail(surface, x1, y1, x2, y2, t, facing, phase):
        """Shadow trail line from origin to target."""
        # Multi-layer streak
        # Halfway point
        cur_x = int(x1 + (x2 - x1) * t)
        cur_y = int(y1 + (y2 - y1) * t)

        for thick, color, a_mult in [
            (16, _NS_naraka.PALETTE["cyan_darkest"], 0.5),
            (12, _NS_naraka.PALETTE["cyan_dark"], 0.7),
            (8, _NS_naraka.PALETTE["cyan_mid"], 0.9),
            (5, _NS_naraka.PALETTE["cyan_light"], 1.0),
            (3, _NS_naraka.PALETTE["cyan_hot"], 1.0),
            (1, _NS_naraka.PALETTE["cyan_shine"], 1.0),
        ]:
            alpha = _NS_naraka._alpha(240 * a_mult * (1 - t * 0.3))
            pygame.draw.line(surface,
                _NS_naraka._rgba(color, alpha),
                (x1, y1), (cur_x, cur_y), thick)

        # Sparkles along trail
        for i in range(12):
            spark_t = (phase * 3 + i * 0.15) % 1.0
            sp_x = int(x1 + (cur_x - x1) * spark_t)
            sp_y = int(y1 + (cur_y - y1) * spark_t)
            perp_offset = math.sin(phase * 5 + i) * 8
            dx = cur_x - x1
            dy = cur_y - y1
            dl = max(1, math.hypot(dx, dy))
            sp_x += int(-dy / dl * perp_offset)
            sp_y += int(dx / dl * perp_offset)
            pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_hot"], (sp_x, sp_y, 2, 2))
            pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_shine"], (sp_x, sp_y, 1, 1))

    # ============================================================
    # ENERGY SLASH (basic attack)
    # ============================================================
    def _draw_energy_slash(surface, boss, cx, cy, progress):
        """Cyan energy crescent slash."""
        if progress < 0.2 or progress > 0.55:
            return

        facing = boss.direction
        if progress < 0.4:
            swing_t = (progress - 0.2) / 0.2
        else:
            swing_t = 1.0
        swing_t = max(0.0, min(1.0, swing_t))

        fade = 1.0 if progress <= 0.4 else max(0.0, 1 - (progress - 0.4) / 0.15)

        slash_cx = cx + facing * 30
        slash_cy = cy - 6

        slash_surf = pygame.Surface((240, 240), pygame.SRCALPHA)
        center = (120, 120)

        start_angle = -math.pi * 0.85
        end_angle = math.pi * 0.75
        radius = 55

        trail_steps = 14
        current_a = start_angle + (end_angle - start_angle) * swing_t

        for step in range(trail_steps):
            step_t = step / trail_steps
            trail_progress = max(0.0, swing_t - step_t * 0.35)
            trail_a = start_angle + (end_angle - start_angle) * trail_progress

            fade_step = (1 - step_t) * fade
            alpha_step = _NS_naraka._alpha(240 * fade_step)
            if alpha_step <= 0:
                continue

            arc_pts = []
            arc_span = 0.15
            for i in range(7):
                a = trail_a - arc_span + (arc_span * 2) * i / 6
                r_var = radius + math.sin(step + i) * 2
                px = center[0] + int(math.cos(a) * r_var) * facing
                py = center[1] + int(math.sin(a) * r_var)
                arc_pts.append((px, py))

            layer_thick = max(2, int(12 * fade_step))
            for layer_i, (thick_mult, color, a_mult) in enumerate([
                (1.3, _NS_naraka.PALETTE["cyan_darkest"], 0.5),
                (1.1, _NS_naraka.PALETTE["cyan_dark"], 0.7),
                (0.85, _NS_naraka.PALETTE["cyan_mid"], 0.9),
                (0.6, _NS_naraka.PALETTE["cyan_light"], 1.0),
                (0.4, _NS_naraka.PALETTE["cyan_hot"], 1.0),
            ]):
                thick = max(1, int(layer_thick * thick_mult))
                a = _NS_naraka._alpha(alpha_step * a_mult)
                if a <= 0:
                    continue
                for i in range(len(arc_pts) - 1):
                    pygame.draw.line(slash_surf,
                                     _NS_naraka._rgba(color, a),
                                     arc_pts[i], arc_pts[i + 1], thick)

        # Leading edge
        if swing_t > 0.05:
            leading_pts = []
            arc_span_lead = 0.55
            for i in range(12):
                a = current_a - arc_span_lead + (arc_span_lead * 2) * i / 11
                px = center[0] + int(math.cos(a) * radius) * facing
                py = center[1] + int(math.sin(a) * radius)
                leading_pts.append((px, py))

            for thick, color in [
                (14, _NS_naraka.PALETTE["cyan_darkest"]),
                (11, _NS_naraka.PALETTE["cyan_dark"]),
                (8, _NS_naraka.PALETTE["cyan_mid"]),
                (5, _NS_naraka.PALETTE["cyan_light"]),
                (3, _NS_naraka.PALETTE["cyan_hot"]),
                (2, _NS_naraka.PALETTE["cyan_shine"]),
                (1, _NS_naraka.PALETTE["white"]),
            ]:
                a = _NS_naraka._alpha(255 * fade)
                if a <= 0:
                    continue
                for i in range(len(leading_pts) - 1):
                    pygame.draw.line(slash_surf,
                                     _NS_naraka._rgba(color, a),
                                     leading_pts[i], leading_pts[i + 1], thick)

        # Sparkles
        for i in range(20):
            drop_angle = start_angle + (end_angle - start_angle) * (i / 20) * swing_t
            drop_r = radius + int(math.sin(swing_t * 8 + i) * 12) + 8
            dx = center[0] + int(math.cos(drop_angle) * drop_r) * facing
            dy = center[1] + int(math.sin(drop_angle) * drop_r)
            drop_a = _NS_naraka._alpha(230 * fade * (i / 20))
            if drop_a > 0:
                pygame.draw.rect(slash_surf,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_light"], drop_a),
                    (dx, dy, 2, 2))
                pygame.draw.rect(slash_surf,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_shine"], drop_a),
                    (dx, dy, 1, 1))

        surface.blit(slash_surf, (slash_cx - 120, slash_cy - 120))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow_float(surface, x, y, phase, intensity=1.0):
        float_offset = math.sin(phase * 0.5) * 7
        scale = 1.0 - (float_offset + 7) / 28
        scale = max(0.55, min(1.0, scale))

        w = int(140 * scale * intensity)
        h = int(30 * scale)
        shadow = pygame.Surface((w + 20, h + 8), pygame.SRCALPHA)
        for radius in range(int(15 * scale), 0, -1):
            alpha = max(0, int((15 * scale - radius) * 15 * intensity))
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, (h + 8) // 2 - radius,
                                 w + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow,
            _NS_naraka._rgba((5, 10, 15), int(190 * intensity)),
            (5, (h + 8) // 2 - h // 2, w + 10, h))
        # Cyan tint under boss
        pygame.draw.ellipse(shadow,
            _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_darkest"], int(100 * intensity)),
            (15, (h + 8) // 2 - h // 3, w, h // 2))
        surface.blit(shadow, (x - (w + 20) // 2, y - (h + 8) // 2))

    def _draw_cyan_wisps(surface, cx, cy, phase, intensity=1.0, trail=False, facing=1):
        """Cyan energy wisps swirling around."""
        for i in range(int(12 * intensity)):
            t = (phase * 0.6 + i * 0.13) % 1.0
            angle = phase * 1.2 + i * math.pi / 6
            radius = 26 + int(math.sin(phase + i) * 10)
            sx = cx + int(math.cos(angle) * radius)
            sy = cy + int(math.sin(angle) * radius * 0.4) - int(t * 40)
            alpha = _NS_naraka._alpha(230 * (1 - t) * intensity)
            if alpha <= 0:
                continue
            _NS_naraka._aacircle(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_darkest"], alpha),
                (sx, sy), 3)
            _NS_naraka._aacircle(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_dark"], alpha),
                (sx, sy - 1), 2)
            _NS_naraka._aacircle(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_mid"], alpha),
                (sx, sy - 1), 1)
            pygame.draw.rect(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_light"], alpha),
                (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_hot"], alpha),
                (sx, sy - 2, 1, 1))

        # Bright sparks
        for i in range(int(6 * intensity)):
            angle = phase * 1.5 + i * math.pi / 3
            radius = 32 + int(math.sin(phase + i) * 5)
            sx = cx + int(math.cos(angle) * radius)
            sy = cy - 8 + int(math.sin(angle) * radius * 0.4)
            alpha = _NS_naraka._alpha(240 * intensity)
            pygame.draw.rect(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_hot"], alpha),
                (sx, sy, 2, 2))
            pygame.draw.rect(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_shine"], alpha),
                (sx, sy, 1, 1))
            pygame.draw.rect(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["white"], alpha),
                (sx, sy, 1, 1))

        # Trail behind (moving)
        if trail:
            for i in range(8):
                sx = cx - (i + 1) * 16 * facing
                sy = cy + 4 + int(math.sin(phase + i) * 2)
                alpha = _NS_naraka._alpha(220 - i * 24)
                if alpha <= 0:
                    continue
                _NS_naraka._aacircle(surface,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_darkest"], alpha),
                    (sx, sy), max(1, 7 - i))
                _NS_naraka._aacircle(surface,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_dark"], alpha),
                    (sx, sy), max(1, 5 - i))
                _NS_naraka._aacircle(surface,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_mid"], alpha),
                    (sx, sy), max(1, 3 - i))
                pygame.draw.rect(surface,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_light"], alpha),
                    (sx, sy - 1, 2, 2))
                pygame.draw.rect(surface,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_hot"], alpha),
                    (sx, sy - 1, 1, 1))

    def _draw_dark_aura(surface, x, y, phase):
        """Dark aura with cyan inner glow."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((260, 220), pygame.SRCALPHA)
        # Outer dark
        for radius in range(110, 5, -5):
            alpha = _NS_naraka._alpha((110 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_naraka._aacircle(aura,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["dark_darkest"], alpha),
                    (130, 110), radius)
        for radius in range(75, 5, -4):
            alpha = _NS_naraka._alpha((75 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_naraka._aacircle(aura,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["dark_dark"], alpha),
                    (130, 110), radius)
        # Cyan inner
        for radius in range(45, 5, -3):
            alpha = _NS_naraka._alpha((45 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_naraka._aacircle(aura,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_darkest"], alpha),
                    (130, 110), radius)
        surface.blit(aura, (x - 130, y - 110))

        # Floating cyan sparkles
        for i in range(16):
            angle = phase * 0.4 + i * math.pi / 8
            r = 42 + int(math.sin(phase + i) * 14)
            sx = x + int(math.cos(angle) * r)
            sy = y - 5 + int(math.sin(angle) * r * 0.5)
            pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_hot"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_naraka.PALETTE["white"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((190, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring,
            _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_darkest"], 200),
            (5, 18, 180, 30), 3)
        pygame.draw.ellipse(ring,
            _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_dark"], 220),
            (14, 22, 162, 24), 2)
        pygame.draw.ellipse(ring,
            _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_mid"], 180),
            (32, 26, 126, 16), 1)

        # Rune spokes
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 95 + int(math.cos(angle) * 55)
            y1 = 33 + int(math.sin(angle) * 10)
            x2 = 95 + int(math.cos(angle) * 82)
            y2 = 33 + int(math.sin(angle) * 15)
            pygame.draw.line(ring,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_light"], 220),
                (x1, y1), (x2, y2), 2)
            pygame.draw.rect(ring,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_hot"], 240),
                (x2, y2, 2, 2))

        if skill:
            pygame.draw.ellipse(ring,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_hot"],
                                  _NS_naraka._alpha(160 * pulse)),
                (14, 14, 162, 38), 2)
        surface.blit(ring, (x - 95, y - 30))

    # ============================================================
    # SKILL Q: CHAOS STRIKE (big crescent slash)
    # ============================================================
    def _draw_chaosstrike_fg(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 35
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.15:
            # Charge
            t = progress / 0.15
            charge_x = x + facing * 25
            charge_y = y - 8
            cr = int(5 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_naraka._alpha(220 * (cr + 5 - r) / (cr + 5))
                _NS_naraka._aacircle(surface,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_darkest"], alpha),
                    (charge_x, charge_y), r)
            _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["cyan_mid"],
                                  (charge_x, charge_y), max(1, cr - 2))
            _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["cyan_hot"],
                                  (charge_x, charge_y), max(1, cr - 4))
        elif progress < 0.55:
            # BIG CRESCENT SLASH forward
            t = (progress - 0.15) / 0.4
            swing_t = t
            fade = 1.0

            slash_cx = x + facing * 50
            slash_cy = y - 8

            slash_surf = pygame.Surface((280, 280), pygame.SRCALPHA)
            center = (140, 140)

            start_angle = -math.pi * 0.85
            end_angle = math.pi * 0.85
            radius = 68

            current_a = start_angle + (end_angle - start_angle) * swing_t

            # Trail
            for step in range(14):
                step_t = step / 14
                trail_progress = max(0.0, swing_t - step_t * 0.35)
                trail_a = start_angle + (end_angle - start_angle) * trail_progress

                fade_step = (1 - step_t) * fade
                alpha_step = _NS_naraka._alpha(240 * fade_step)
                if alpha_step <= 0:
                    continue

                arc_pts = []
                arc_span = 0.15
                for i in range(7):
                    a = trail_a - arc_span + (arc_span * 2) * i / 6
                    r_var = radius + math.sin(step + i) * 2
                    px = center[0] + int(math.cos(a) * r_var) * facing
                    py = center[1] + int(math.sin(a) * r_var)
                    arc_pts.append((px, py))

                layer_thick = max(3, int(15 * fade_step))
                for thick_mult, color, a_mult in [
                    (1.3, _NS_naraka.PALETTE["cyan_darkest"], 0.5),
                    (1.1, _NS_naraka.PALETTE["cyan_dark"], 0.7),
                    (0.85, _NS_naraka.PALETTE["cyan_mid"], 0.9),
                    (0.6, _NS_naraka.PALETTE["cyan_light"], 1.0),
                    (0.4, _NS_naraka.PALETTE["cyan_hot"], 1.0),
                ]:
                    thick = max(1, int(layer_thick * thick_mult))
                    a = _NS_naraka._alpha(alpha_step * a_mult)
                    if a <= 0:
                        continue
                    for i in range(len(arc_pts) - 1):
                        pygame.draw.line(slash_surf,
                                         _NS_naraka._rgba(color, a),
                                         arc_pts[i], arc_pts[i + 1], thick)

            # Leading edge super bright
            if swing_t > 0.05:
                leading_pts = []
                arc_span_lead = 0.55
                for i in range(12):
                    a = current_a - arc_span_lead + (arc_span_lead * 2) * i / 11
                    px = center[0] + int(math.cos(a) * radius) * facing
                    py = center[1] + int(math.sin(a) * radius)
                    leading_pts.append((px, py))

                for thick, color in [
                    (16, _NS_naraka.PALETTE["cyan_darkest"]),
                    (13, _NS_naraka.PALETTE["cyan_dark"]),
                    (10, _NS_naraka.PALETTE["cyan_mid"]),
                    (6, _NS_naraka.PALETTE["cyan_light"]),
                    (4, _NS_naraka.PALETTE["cyan_hot"]),
                    (2, _NS_naraka.PALETTE["cyan_shine"]),
                    (1, _NS_naraka.PALETTE["white"]),
                ]:
                    for i in range(len(leading_pts) - 1):
                        pygame.draw.line(slash_surf,
                                         _NS_naraka._rgba(color, 255),
                                         leading_pts[i], leading_pts[i + 1], thick)

            # Sparkles
            for i in range(24):
                drop_angle = start_angle + (end_angle - start_angle) * (i / 24) * swing_t
                drop_r = radius + int(math.sin(swing_t * 8 + i) * 14) + 8
                dx = center[0] + int(math.cos(drop_angle) * drop_r) * facing
                dy = center[1] + int(math.sin(drop_angle) * drop_r)
                drop_a = _NS_naraka._alpha(240 * (i / 24))
                if drop_a > 0:
                    pygame.draw.rect(slash_surf,
                        _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_light"], drop_a),
                        (dx, dy, 3, 3))
                    pygame.draw.rect(slash_surf,
                        _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_shine"], drop_a),
                        (dx, dy, 1, 1))

            surface.blit(slash_surf, (slash_cx - 140, slash_cy - 140))

    # ============================================================
    # SKILL W: SHADOW STEP
    # ============================================================
    def _draw_shadowstep_ground(surface, boss, x, y, timer, pulse):
        """Ring markers at origin and destination."""
        duration = 30
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_naraka._target_position(boss, x, y)

        if progress < 0.3:
            # Depart ring
            t = progress / 0.3
            r = int(30 + t * 15)
            alpha = _NS_naraka._alpha(240 * (1 - t))
            _NS_naraka._aacircle(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_darkest"], alpha),
                (x, y + 68), r, 3)
            _NS_naraka._aacircle(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_mid"], alpha),
                (x, y + 68), max(1, r - 4), 2)
        elif progress > 0.6:
            # Arrival ring
            behind_x = tx - boss.direction * 50
            behind_y = ty
            t = (progress - 0.6) / 0.4
            r = int(35 * (1 - t) + 20)
            alpha = _NS_naraka._alpha(240)
            _NS_naraka._aacircle(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_darkest"], alpha),
                (behind_x, behind_y + 68), r, 3)
            _NS_naraka._aacircle(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_hot"], alpha),
                (behind_x, behind_y + 68), max(1, r - 5), 1)

    # ============================================================
    # SKILL E: CHAIN HAMMER (chain projectile + pull)
    # ============================================================
    def _draw_chainhammer_ground(surface, boss, x, y, timer, pulse):
        """Ground indicator."""
        pass  # Skill focuses on foreground

    def _draw_chainhammer_fg(surface, boss, x, y, timer, phase):
        """Chain projectile flying to target then pulling back."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_naraka._target_position(boss, x, y)

        # Origin at hand
        origin_x = x + facing * 22
        origin_y = y - 6

        if progress < 0.15:
            # Charge
            t = progress / 0.15
            cr = int(4 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_naraka._alpha(220 * (cr + 5 - r) / (cr + 5))
                _NS_naraka._aacircle(surface,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_darkest"], alpha),
                    (origin_x, origin_y), r)
            _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["cyan_mid"],
                                  (origin_x, origin_y), max(1, cr - 2))
            _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["cyan_hot"],
                                  (origin_x, origin_y), max(1, cr - 4))
        elif progress < 0.55:
            # LAUNCH CHAIN - flies to target
            t = (progress - 0.15) / 0.4
            # Chain tip position
            tip_x = int(origin_x + (tx - origin_x) * t)
            tip_y = int(origin_y + (ty - origin_y) * t)

            # Draw chain from origin to tip (segmented)
            chain_segs = 12
            for seg_i in range(chain_segs):
                seg_t = seg_i / chain_segs
                seg_end_t = (seg_i + 1) / chain_segs
                seg_x = int(origin_x + (tip_x - origin_x) * seg_t)
                seg_y = int(origin_y + (tip_y - origin_y) * seg_t)
                seg_end_x = int(origin_x + (tip_x - origin_x) * seg_end_t)
                seg_end_y = int(origin_y + (tip_y - origin_y) * seg_end_t)

                # Chain link
                pygame.draw.line(surface, _NS_naraka.PALETTE["shadow_deep"],
                                 (seg_x + 1, seg_y + 1),
                                 (seg_end_x + 1, seg_end_y + 1), 4)
                pygame.draw.line(surface, _NS_naraka.PALETTE["chain_darkest"],
                                 (seg_x, seg_y), (seg_end_x, seg_end_y), 3)
                pygame.draw.line(surface, _NS_naraka.PALETTE["chain_dark"],
                                 (seg_x, seg_y), (seg_end_x, seg_end_y), 2)
                pygame.draw.line(surface, _NS_naraka.PALETTE["chain_mid"],
                                 (seg_x, seg_y - 1), (seg_end_x, seg_end_y - 1), 1)

            # Big CHAIN HAMMER HEAD at tip (spiked ball)
            for r in range(10, 0, -1):
                alpha = _NS_naraka._alpha(180 * (10 - r) / 10)
                _NS_naraka._aacircle(surface,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_mid"], alpha),
                    (tip_x, tip_y), r)
            _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["chain_darkest"], (tip_x, tip_y), 7)
            _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["chain_dark"], (tip_x, tip_y), 6)
            _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["chain_mid"], (tip_x, tip_y), 5)
            _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["chain_light"], (tip_x, tip_y), 3)
            _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["cyan_shine"], (tip_x, tip_y), 2)

            # Spikes on ball
            for spike_i in range(6):
                spike_a = spike_i * math.pi / 3 + phase * 2
                spike_end_x = tip_x + int(math.cos(spike_a) * 8)
                spike_end_y = tip_y + int(math.sin(spike_a) * 8)
                pygame.draw.line(surface, _NS_naraka.PALETTE["chain_darkest"],
                                 (tip_x, tip_y), (spike_end_x, spike_end_y), 2)
                pygame.draw.line(surface, _NS_naraka.PALETTE["chain_mid"],
                                 (tip_x, tip_y), (spike_end_x, spike_end_y), 1)
                pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_hot"],
                                 (spike_end_x, spike_end_y, 2, 2))
                pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_shine"],
                                 (spike_end_x, spike_end_y, 1, 1))

            # Impact at target
            if t > 0.85:
                st = (t - 0.85) / 0.15
                r = int(15 + st * 20)
                alpha = _NS_naraka._alpha(240 * (1 - st))
                _NS_naraka._aacircle(surface,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_darkest"], alpha),
                    (tx, ty), r + 3, 3)
                _NS_naraka._aacircle(surface,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_mid"], alpha),
                    (tx, ty), r, 2)
                for i in range(10):
                    a = i * math.pi / 5
                    ex = tx + int(math.cos(a) * r)
                    ey = ty + int(math.sin(a) * r * 0.7)
                    pygame.draw.rect(surface, _NS_naraka.PALETTE["cyan_hot"], (ex, ey, 2, 2))
                    pygame.draw.rect(surface, _NS_naraka.PALETTE["white"], (ex, ey, 1, 1))
        else:
            # RECALL - chain pulls back
            t = (progress - 0.55) / 0.45
            # Chain returning
            tip_x = int(tx + (origin_x - tx) * t)
            tip_y = int(ty + (origin_y - ty) * t)

            # Draw chain from origin to tip (still visible)
            chain_segs = 12
            for seg_i in range(chain_segs):
                seg_t = seg_i / chain_segs
                seg_end_t = (seg_i + 1) / chain_segs
                seg_x = int(origin_x + (tip_x - origin_x) * seg_t)
                seg_y = int(origin_y + (tip_y - origin_y) * seg_t)
                seg_end_x = int(origin_x + (tip_x - origin_x) * seg_end_t)
                seg_end_y = int(origin_y + (tip_y - origin_y) * seg_end_t)

                pygame.draw.line(surface, _NS_naraka.PALETTE["chain_darkest"],
                                 (seg_x, seg_y), (seg_end_x, seg_end_y), 3)
                pygame.draw.line(surface, _NS_naraka.PALETTE["chain_dark"],
                                 (seg_x, seg_y), (seg_end_x, seg_end_y), 2)
                pygame.draw.line(surface, _NS_naraka.PALETTE["chain_mid"],
                                 (seg_x, seg_y - 1), (seg_end_x, seg_end_y - 1), 1)

            # Hammer head at returning tip
            _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["chain_dark"], (tip_x, tip_y), 5)
            _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["chain_light"], (tip_x, tip_y), 3)
            _NS_naraka._aacircle(surface, _NS_naraka.PALETTE["cyan_hot"], (tip_x, tip_y), 2)

    # ============================================================
    # SKILL R: EXECUTION MODE (transformation + massive slashes)
    # ============================================================
    def _draw_execution_ground(surface, boss, x, y, timer, pulse):
        """Dark pulsing aura on ground."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        r = int(80 + math.sin(pulse * 2) * 6)
        alpha = _NS_naraka._alpha(220)

        # Big dark ring
        pygame.draw.ellipse(surface,
            _NS_naraka._rgba(_NS_naraka.PALETTE["dark_darkest"], alpha),
            (x - r, y + 66 - r // 3, r * 2, r * 2 // 3), 4)
        pygame.draw.ellipse(surface,
            _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_dark"], alpha),
            (x - r + 5, y + 66 - r // 3 + 4,
             r * 2 - 10, r * 2 // 3 - 8), 3)
        pygame.draw.ellipse(surface,
            _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_hot"], alpha),
            (x - r + 12, y + 66 - r // 3 + 8,
             r * 2 - 24, r * 2 // 3 - 16), 2)

        # Radial spikes
        for i in range(12):
            angle = i * math.pi / 6 + pulse * 0.3
            spike_len = 70 + int(math.sin(pulse * 2 + i) * 8)
            sx = x + int(math.cos(angle) * spike_len)
            sy = y + 66 + int(math.sin(angle) * spike_len * 0.4)
            pygame.draw.line(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_light"], alpha),
                (x, y + 66), (sx, sy), 2)
            pygame.draw.rect(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_shine"], alpha),
                (sx, sy, 2, 2))
            pygame.draw.rect(surface,
                _NS_naraka._rgba(_NS_naraka.PALETTE["white"], alpha),
                (sx, sy, 1, 1))

    def _draw_execution_fg(surface, boss, x, y, timer, phase):
        """Powerful cyan energy burst + multiple slashes."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            # TRANSFORMATION - dark energy surge upward
            t = progress / 0.3
            # Rising dark energy pillars
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.5
                rise_t = (phase * 0.6 + i * 0.15) % 1.0
                pillar_x = x + int(math.cos(angle) * 30)
                pillar_y_base = y + 40
                pillar_h = int(60 * t)
                pillar_top = pillar_y_base - pillar_h

                # Dark pillar
                for py in range(pillar_top, pillar_y_base, 3):
                    pillar_t = (py - pillar_top) / pillar_h if pillar_h > 0 else 0
                    alpha = _NS_naraka._alpha(220 * (1 - pillar_t) * t)
                    if alpha > 0:
                        _NS_naraka._aacircle(surface,
                            _NS_naraka._rgba(_NS_naraka.PALETTE["dark_dark"], alpha),
                            (pillar_x, py), 4)
                        _NS_naraka._aacircle(surface,
                            _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_dark"], alpha),
                            (pillar_x, py), 3)
                        pygame.draw.rect(surface,
                            _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_hot"], alpha),
                            (pillar_x, py, 1, 1))

            # Central bright flash growing
            for r in range(int(30 * t), 0, -2):
                alpha = _NS_naraka._alpha(200 * (30 * t - r) / (30 * t) * t if 30 * t > 0 else 0)
                _NS_naraka._aacircle(surface,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_light"], alpha),
                    (x, y - 4), r)

        elif progress < 0.75:
            # MULTIPLE POWER SLASHES around boss
            slash_t = (progress - 0.3) / 0.45
            num_slashes = int(slash_t * 8)  # up to 8 slashes

            for slash_i in range(num_slashes):
                slash_age = min(1.0, (num_slashes - slash_i) / 3)
                slash_angle = slash_i * math.pi / 4 + phase * 0.5
                slash_dist = 60
                slash_cx = x + int(math.cos(slash_angle) * slash_dist)
                slash_cy = y + int(math.sin(slash_angle) * slash_dist * 0.5) - 10

                # Draw crescent slash
                slash_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
                center = (60, 60)
                start_a = slash_angle + math.pi * 0.6
                end_a = slash_angle - math.pi * 0.6
                arc_pts = []
                for i in range(10):
                    a = start_a + (end_a - start_a) * i / 9
                    px = center[0] + int(math.cos(a) * 25)
                    py = center[1] + int(math.sin(a) * 25)
                    arc_pts.append((px, py))
                for thick, color, a_mult in [
                    (8, _NS_naraka.PALETTE["cyan_dark"], 0.7),
                    (6, _NS_naraka.PALETTE["cyan_mid"], 0.9),
                    (4, _NS_naraka.PALETTE["cyan_light"], 1.0),
                    (2, _NS_naraka.PALETTE["cyan_hot"], 1.0),
                    (1, _NS_naraka.PALETTE["cyan_shine"], 1.0),
                ]:
                    a = _NS_naraka._alpha(240 * a_mult * slash_age)
                    for i in range(len(arc_pts) - 1):
                        pygame.draw.line(slash_surf,
                            _NS_naraka._rgba(color, a),
                            arc_pts[i], arc_pts[i + 1], thick)
                surface.blit(slash_surf, (slash_cx - 60, slash_cy - 60))

            # Central bright aura around boss
            aura_r = int(35 + math.sin(phase * 3) * 5)
            for r in range(aura_r, 0, -2):
                alpha = _NS_naraka._alpha(150 * (aura_r - r) / aura_r)
                _NS_naraka._aacircle(surface,
                    _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_light"], alpha),
                    (x, y - 4), r)
        else:
            # Aftermath - fading energy
            t = (progress - 0.75) / 0.25
            for i in range(16):
                rise_t = (phase * 0.7 + i * 0.08) % 1.0
                angle = i * math.pi / 8
                r_p = 50 + int(math.sin(phase + i) * 10)
                rx = x + int(math.cos(angle) * r_p)
                ry = y - 20 + int(math.sin(angle) * r_p * 0.4) - int(rise_t * 25)
                alpha = _NS_naraka._alpha(220 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_naraka._aacircle(surface,
                        _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_dark"], alpha),
                        (rx, ry), 3)
                    _NS_naraka._aacircle(surface,
                        _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_mid"], alpha),
                        (rx, ry), 2)
                    pygame.draw.rect(surface,
                        _NS_naraka._rgba(_NS_naraka.PALETTE["cyan_hot"], alpha),
                        (rx, ry, 1, 1))


# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_kenshiro(surface, boss, x, y):
    """Entry point kenshiro."""
    return _NS_kenshiro.draw_kenshiro(surface, boss, x, y)


def draw_khazan(surface, boss, x, y):
    """Entry point khazan."""
    return _NS_khazan.draw_khazan(surface, boss, x, y)


def draw_wiro(surface, boss, x, y):
    """Entry point wiro."""
    return _NS_wiro.draw_wiro(surface, boss, x, y)


def draw_naraka(surface, boss, x, y):
    """Entry point naraka."""
    return _NS_naraka.draw_naraka(surface, boss, x, y)
