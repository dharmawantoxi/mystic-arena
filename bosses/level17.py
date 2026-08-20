"""
bosses/level17.py - Semua boss Level 17

Berisi:
  - kaelthorn   (mini boss - MELEE azure vanguard warrior)
  - solvanth    (mini boss - MELEE radiant guardian centaur)
  - xyrael      (mini boss - MELEE cyan wraith assassin)
  - nyxareth    (TRUE BOSS - Cosmic Sovereign, RANGED cosmic mage)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _nx_ (nyxareth) di-rename -> _nxa_ (bentrok dengan level5)
  - _xr_ (xyrael)   di-rename -> _xya_ (bentrok dengan level3)
  - _kt_ (kaelthorn) & _sv_ (solvanth) sudah unik.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True



# ====================================================================
# kaelthorn.py
# ====================================================================

"""
KAELTHORN - The Azure Vanguard
Mini boss warrior dengan blade besar bertema energi biru.
Gaya rendering mengikuti _NS_vhorethzir.
"""



class _NS_kaelthorn:
    """Namespace kaelthorn - warrior mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin tones (tan warrior)
        "skin_darkest": (60, 30, 20),
        "skin_dark": (110, 65, 40),
        "skin_mid": (165, 105, 65),
        "skin_light": (210, 150, 100),
        "skin_shine": (240, 200, 155),

        # Muscle shadow
        "muscle_shadow": (75, 40, 25),
        "muscle_deep": (45, 22, 15),

        # Hair/bandana (red)
        "hair_dark": (50, 15, 10),
        "hair_mid": (110, 30, 25),
        "hair_light": (170, 55, 40),
        "bandana_dark": (90, 20, 20),
        "bandana_mid": (160, 35, 35),
        "bandana_light": (220, 70, 60),

        # Pants/sash (brown/red)
        "cloth_darkest": (35, 20, 10),
        "cloth_dark": (75, 45, 22),
        "cloth_mid": (125, 80, 40),
        "cloth_light": (180, 130, 75),
        "sash_dark": (100, 25, 20),
        "sash_mid": (160, 45, 35),
        "sash_light": (210, 80, 65),

        # Gold accents (belt buckle, jewelry)
        "gold_dark": (95, 65, 15),
        "gold_mid": (180, 140, 40),
        "gold_light": (245, 210, 90),
        "gold_shine": (255, 245, 180),

        # Blade (steel + blue enchant)
        "blade_darkest": (30, 40, 55),
        "blade_dark": (75, 90, 115),
        "blade_mid": (140, 160, 185),
        "blade_light": (210, 225, 240),
        "blade_shine": (250, 253, 255),

        # Azure blue energy (main theme)
        "azure_darkest": (5, 15, 45),
        "azure_dark": (20, 55, 130),
        "azure_mid": (55, 130, 230),
        "azure_light": (130, 200, 255),
        "azure_hot": (200, 240, 255),
        "azure_shine": (240, 250, 255),

        # Eye (fierce)
        "eye_dark": (40, 20, 10),
        "eye_white": (230, 220, 200),
        "eye_blue": (80, 150, 220),

        # Ground/rune
        "rune_dark": (10, 25, 60),
        "rune_mid": (40, 100, 200),
        "rune_light": (150, 220, 255),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    # ============================================================
    # HELPERS
    # ============================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kaelthorn._clamp(color)
        if _NS_kaelthorn.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_kaelthorn._clamp(color)
        if _NS_kaelthorn.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_kaelthorn._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar
            # (x, y) dengan kompensasi scale (hero di-render di
            # canvas lalu di-scale; boss langsung di layar).
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return int(x + 220 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_kaelthorn(surface, boss, x, y):
        """Entry point utama."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_kaelthorn._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_kt_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_kaelthorn._draw_azure_aura(surface, x, y, pulse)
        _NS_kaelthorn._draw_ground_ring(surface, x, y + 46, pulse, active_skill)

        # Skill ground FX.
        if active_skill == "e":
            _NS_kaelthorn._draw_spin_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaelthorn._draw_leap_ground(surface, boss, x, y, skill_timer, pulse)

        # Body (always floating - bob).
        if active_skill == "r":
            _NS_kaelthorn._draw_body_leap(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaelthorn._draw_body_spin(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "q":
            _NS_kaelthorn._draw_body_charge(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kaelthorn._draw_body_throw(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_kaelthorn._draw_body_attack(surface, boss, x, y)
        else:
            _NS_kaelthorn._draw_body_idle(surface, boss, x, y)

        # Foreground skill FX.
        if active_skill == "q":
            _NS_kaelthorn._draw_bravest_fighter_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kaelthorn._draw_justice_blade_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaelthorn._draw_defenders_assault_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaelthorn._draw_chivalry_fists_fx(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kt_previous_timer", 0))
        active = bool(getattr(boss, "_kt_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._kt_attack_active = True
            boss._kt_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._kt_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._kt_attack_frame = int(getattr(boss, "_kt_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._kt_attack_active = False
            boss._kt_attack_frame = 0
            active = False

        boss._kt_previous_timer = timer
        boss._kt_attack_progress = (
            min(1.0, getattr(boss, "_kt_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        # Floating bob.
        bob = int(math.sin(boss.pulse * 0.8) * 5)
        _NS_kaelthorn._draw_shadow(surface, x, y + 50)
        _NS_kaelthorn._draw_float_particles(surface, x, y + 40, boss.pulse)
        _NS_kaelthorn._draw_warrior_body(surface, x, y + bob, boss.direction,
                                          boss.pulse, "idle")

    def _draw_body_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_kt_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_kt_attack_dir", None)
        if facing is None:
            facing = boss.direction
        bob = int(math.sin(boss.pulse * 0.8) * 4)
        # Slight lunge forward during swing.
        if progress < 0.5:
            lunge = int(progress * 8) * facing
        else:
            lunge = int((1 - progress) * 8) * facing

        _NS_kaelthorn._draw_shadow(surface, x + lunge, y + 50)
        _NS_kaelthorn._draw_float_particles(surface, x + lunge, y + 40, boss.pulse)
        _NS_kaelthorn._draw_warrior_body(surface, x + lunge, y + bob,
                                          facing, boss.pulse,
                                          "attack", progress)
        # Melee swing arc.
        _NS_kaelthorn._draw_melee_swing(surface, x + lunge, y + bob,
                                        facing, progress)

    def _draw_body_charge(surface, boss, x, y, timer, pulse):
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        bob = int(math.sin(pulse * 0.8) * 3)
        # Charge forward then swing.
        if progress < 0.4:
            lunge = int(progress / 0.4 * 25) * boss.direction
        elif progress < 0.7:
            lunge = int(25) * boss.direction
        else:
            lunge = int((1 - (progress - 0.7) / 0.3) * 25) * boss.direction

        _NS_kaelthorn._draw_shadow(surface, x + lunge, y + 50)
        _NS_kaelthorn._draw_float_particles(surface, x + lunge, y + 40, pulse,
                                             intense=True)
        _NS_kaelthorn._draw_warrior_body(surface, x + lunge, y + bob,
                                          boss.direction, pulse, "charge",
                                          progress)

    def _draw_body_throw(surface, boss, x, y, timer, pulse):
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        bob = int(math.sin(pulse * 0.8) * 4)
        _NS_kaelthorn._draw_shadow(surface, x, y + 50)
        _NS_kaelthorn._draw_float_particles(surface, x, y + 40, pulse)
        _NS_kaelthorn._draw_warrior_body(surface, x, y + bob, boss.direction,
                                          pulse, "throw", progress)

    def _draw_body_spin(surface, boss, x, y, timer, pulse):
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        bob = int(math.sin(pulse * 0.8) * 4)
        _NS_kaelthorn._draw_shadow(surface, x, y + 50)
        _NS_kaelthorn._draw_float_particles(surface, x, y + 40, pulse,
                                             intense=True)
        _NS_kaelthorn._draw_warrior_body(surface, x, y + bob, boss.direction,
                                          pulse, "spin", progress)

    def _draw_body_leap(surface, boss, x, y, timer, pulse):
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Leap up then slam down.
        if progress < 0.4:
            t = progress / 0.4
            lift = int(t * 60)
        elif progress < 0.7:
            lift = 60
        else:
            t = (progress - 0.7) / 0.3
            lift = int(60 * (1 - t) - t * 5)  # slam past ground

        _NS_kaelthorn._draw_shadow(surface, x, y + 50)
        _NS_kaelthorn._draw_float_particles(surface, x, y + 40, pulse)
        _NS_kaelthorn._draw_warrior_body(surface, x, y - lift, boss.direction,
                                          pulse, "leap", progress)

    # ============================================================
    # WARRIOR BODY
    # ============================================================
    def _draw_warrior_body(surface, cx, cy, facing, phase, action,
                            action_progress=0):
        """Complete warrior: legs, torso, arms, head, blade."""
        # Order: back leg, back arm, torso, front leg, head, front arm w/ blade
        _NS_kaelthorn._draw_back_leg(surface, cx, cy, facing, phase, action,
                                      action_progress)
        _NS_kaelthorn._draw_torso(surface, cx, cy, facing, phase, action,
                                   action_progress)
        _NS_kaelthorn._draw_front_leg(surface, cx, cy, facing, phase, action,
                                       action_progress)
        _NS_kaelthorn._draw_head(surface, cx, cy - 22, facing, phase, action)
        _NS_kaelthorn._draw_back_arm(surface, cx, cy, facing, phase, action,
                                      action_progress)
        _NS_kaelthorn._draw_front_arm_blade(surface, cx, cy, facing, phase,
                                             action, action_progress)

    def _draw_back_leg(surface, cx, cy, facing, phase, action, progress):
        # Back leg (further from camera).
        base_x = cx - facing * 4
        knee_x = cx - facing * 6
        knee_y = cy + 18
        foot_x = cx - facing * 5
        foot_y = cy + 32

        # Shadow.
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["shadow_deep"],
                              (base_x + 2, cy + 8), (knee_x + 2, knee_y + 1), 7)
        # Thigh.
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["cloth_darkest"], [
            (base_x - 4, cy + 8), (base_x + 3, cy + 8),
            (knee_x + 3, knee_y), (knee_x - 3, knee_y),
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["cloth_dark"], [
            (base_x - 3, cy + 9), (base_x + 2, cy + 9),
            (knee_x + 2, knee_y - 1), (knee_x - 2, knee_y - 1),
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["cloth_mid"], [
            (base_x - 1, cy + 10), (base_x + 1, cy + 10),
            (knee_x + 1, knee_y - 2), (knee_x, knee_y - 2),
        ])
        # Shin (skin).
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["skin_darkest"], [
            (knee_x - 3, knee_y), (knee_x + 3, knee_y),
            (foot_x + 2, foot_y), (foot_x - 2, foot_y),
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["skin_dark"], [
            (knee_x - 2, knee_y + 1), (knee_x + 2, knee_y + 1),
            (foot_x + 1, foot_y - 1), (foot_x - 1, foot_y - 1),
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["skin_mid"], [
            (knee_x - 1, knee_y + 2), (knee_x + 1, knee_y + 2),
            (foot_x, foot_y - 2), (foot_x - 1, foot_y - 2),
        ])
        # Foot/sandal.
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["cloth_darkest"], [
            (foot_x - 4, foot_y - 1), (foot_x + 5, foot_y - 1),
            (foot_x + 5, foot_y + 2), (foot_x - 4, foot_y + 2),
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["cloth_dark"], [
            (foot_x - 3, foot_y), (foot_x + 4, foot_y),
            (foot_x + 4, foot_y + 1), (foot_x - 3, foot_y + 1),
        ])

    def _draw_front_leg(surface, cx, cy, facing, phase, action, progress):
        base_x = cx + facing * 4
        knee_x = cx + facing * 6
        knee_y = cy + 18
        foot_x = cx + facing * 8
        foot_y = cy + 32

        # Shadow.
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["shadow_deep"],
                              (base_x + 2, cy + 8), (knee_x + 2, knee_y + 1), 8)
        # Thigh.
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["cloth_darkest"], [
            (base_x - 4, cy + 8), (base_x + 4, cy + 8),
            (knee_x + 4, knee_y), (knee_x - 4, knee_y),
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["cloth_dark"], [
            (base_x - 3, cy + 9), (base_x + 3, cy + 9),
            (knee_x + 3, knee_y - 1), (knee_x - 3, knee_y - 1),
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["cloth_mid"], [
            (base_x - 1, cy + 10), (base_x + 2, cy + 10),
            (knee_x + 2, knee_y - 2), (knee_x, knee_y - 2),
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["cloth_light"], [
            (base_x, cy + 11), (base_x + 1, cy + 11),
            (knee_x + 1, knee_y - 3), (knee_x, knee_y - 3),
        ])
        # Shin.
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["skin_darkest"], [
            (knee_x - 4, knee_y), (knee_x + 4, knee_y),
            (foot_x + 3, foot_y), (foot_x - 3, foot_y),
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["skin_dark"], [
            (knee_x - 3, knee_y + 1), (knee_x + 3, knee_y + 1),
            (foot_x + 2, foot_y - 1), (foot_x - 2, foot_y - 1),
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["skin_mid"], [
            (knee_x - 1, knee_y + 2), (knee_x + 2, knee_y + 2),
            (foot_x + 1, foot_y - 2), (foot_x - 1, foot_y - 2),
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["skin_light"], [
            (knee_x, knee_y + 3), (knee_x + 1, knee_y + 3),
            (foot_x, foot_y - 3), (foot_x, foot_y - 3),
        ])
        # Foot.
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["cloth_darkest"], [
            (foot_x - 4, foot_y - 1), (foot_x + 6, foot_y - 1),
            (foot_x + 6, foot_y + 3), (foot_x - 4, foot_y + 3),
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["cloth_dark"], [
            (foot_x - 3, foot_y), (foot_x + 5, foot_y),
            (foot_x + 5, foot_y + 2), (foot_x - 3, foot_y + 2),
        ])
        pygame.draw.line(surface, _NS_kaelthorn.PALETTE["cloth_mid"],
                         (foot_x - 2, foot_y + 1), (foot_x + 4, foot_y + 1), 1)

    def _draw_torso(surface, cx, cy, facing, phase, action, progress):
        """Muscular torso (bare chest with tan skin)."""
        breath = math.sin(phase * 0.7) * 1

        # Torso shape.
        torso_shape = [
            (cx - 10, cy - 10),
            (cx - 12, cy - 5),
            (cx - 11, cy + 3),
            (cx - 8, cy + 8),
            (cx + 8, cy + 8),
            (cx + 11, cy + 3),
            (cx + 12, cy - 5),
            (cx + 10, cy - 10),
            (cx + 5, cy - 12),
            (cx - 5, cy - 12),
        ]
        # Shadow.
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in torso_shape])
        # Base.
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["skin_darkest"],
                            torso_shape)
        # Muscle base.
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["skin_dark"], [
            (cx - 10, cy - 8), (cx - 11, cy),
            (cx - 8, cy + 6), (cx + 8, cy + 6),
            (cx + 11, cy), (cx + 10, cy - 8),
            (cx + 5, cy - 11), (cx - 5, cy - 11),
        ])
        # Mid tone.
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["skin_mid"], [
            (cx - 8, cy - 6), (cx - 9, cy),
            (cx - 6, cy + 4), (cx + 6, cy + 4),
            (cx + 9, cy), (cx + 8, cy - 6),
            (cx + 4, cy - 9), (cx - 4, cy - 9),
        ])
        # Chest highlight (pectorals).
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["skin_light"], [
            (cx - 6, cy - 5), (cx - 2, cy - 6),
            (cx - 2, cy - 1), (cx - 5, cy),
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["skin_light"], [
            (cx + 2, cy - 6), (cx + 6, cy - 5),
            (cx + 5, cy), (cx + 2, cy - 1),
        ])
        # Chest shine.
        pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["skin_shine"],
                         (cx - 4, cy - 4, 1, 1))
        pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["skin_shine"],
                         (cx + 3, cy - 4, 1, 1))

        # Ab muscles (center line + lines).
        pygame.draw.line(surface, _NS_kaelthorn.PALETTE["muscle_shadow"],
                         (cx, cy - 4), (cx, cy + 6), 1)
        for dy in (0, 3):
            pygame.draw.line(surface, _NS_kaelthorn.PALETTE["muscle_shadow"],
                             (cx - 4, cy + dy), (cx + 4, cy + dy), 1)

        # Belt/sash (red waist).
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["sash_dark"], [
            (cx - 11, cy + 6), (cx + 11, cy + 6),
            (cx + 12, cy + 10), (cx - 12, cy + 10),
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["sash_mid"], [
            (cx - 10, cy + 7), (cx + 10, cy + 7),
            (cx + 11, cy + 9), (cx - 11, cy + 9),
        ])
        pygame.draw.line(surface, _NS_kaelthorn.PALETTE["sash_light"],
                         (cx - 8, cy + 8), (cx + 8, cy + 8), 1)
        # Gold belt buckle.
        pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["gold_dark"],
                         (cx - 3, cy + 7, 6, 3))
        pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["gold_mid"],
                         (cx - 2, cy + 8, 4, 2))
        pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["gold_light"],
                         (cx - 1, cy + 8, 2, 1))
        pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["gold_shine"],
                         (cx, cy + 8, 1, 1))

        # Loincloth flap (in front).
        flap_sway = math.sin(phase * 0.5) * 1
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["sash_dark"], [
            (cx - 5, cy + 10), (cx + 5, cy + 10),
            (cx + 6 + int(flap_sway), cy + 20),
            (cx - 6 + int(flap_sway), cy + 20),
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["sash_mid"], [
            (cx - 4, cy + 11), (cx + 4, cy + 11),
            (cx + 5 + int(flap_sway), cy + 19),
            (cx - 5 + int(flap_sway), cy + 19),
        ])
        pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["sash_light"],
                         (cx - 2 + int(flap_sway), cy + 14, 4, 3))

        # Shoulder tattoo (subtle).
        pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["muscle_deep"],
                         (cx - 9 * facing, cy - 8, 3, 2))

    def _draw_head(surface, cx, cy, facing, phase, action):
        """Head with bandana, hair, face, eye."""
        # Face base.
        face_shape = [
            (cx - 6, cy - 4), (cx - 7, cy + 1),
            (cx - 5, cy + 5), (cx - 2, cy + 7),
            (cx + 2, cy + 7), (cx + 5, cy + 5),
            (cx + 7, cy + 1), (cx + 6, cy - 4),
            (cx + 3, cy - 7), (cx - 3, cy - 7),
        ]
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in face_shape])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["skin_darkest"],
                            face_shape)
        # Face mid.
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["skin_dark"], [
            (cx - 5, cy - 3), (cx - 6, cy + 1),
            (cx - 4, cy + 4), (cx + 4, cy + 4),
            (cx + 6, cy + 1), (cx + 5, cy - 3),
            (cx + 2, cy - 6), (cx - 2, cy - 6),
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["skin_mid"], [
            (cx - 4, cy - 2), (cx - 5, cy + 1),
            (cx - 3, cy + 3), (cx + 3, cy + 3),
            (cx + 5, cy + 1), (cx + 4, cy - 2),
            (cx + 1, cy - 5), (cx - 1, cy - 5),
        ])
        # Cheek/nose highlight.
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["skin_light"], [
            (cx - 2, cy - 1), (cx + 2, cy - 1),
            (cx + 2, cy + 2), (cx - 2, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["skin_shine"],
                         (cx, cy, 1, 1))

        # Bandana (red).
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["bandana_dark"], [
            (cx - 7, cy - 5), (cx + 7, cy - 5),
            (cx + 8, cy - 3), (cx - 8, cy - 3),
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["bandana_mid"], [
            (cx - 6, cy - 5), (cx + 6, cy - 5),
            (cx + 7, cy - 4), (cx - 7, cy - 4),
        ])
        pygame.draw.line(surface, _NS_kaelthorn.PALETTE["bandana_light"],
                         (cx - 5, cy - 5), (cx + 5, cy - 5), 1)
        # Bandana tail behind.
        tail_sway = math.sin(phase * 0.6) * 2
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["bandana_dark"], [
            (cx - 6 * facing, cy - 4),
            (cx - 10 * facing + int(tail_sway), cy - 2),
            (cx - 11 * facing + int(tail_sway), cy + 2),
            (cx - 7 * facing, cy - 2),
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["bandana_mid"], [
            (cx - 7 * facing, cy - 3),
            (cx - 9 * facing + int(tail_sway), cy - 1),
            (cx - 10 * facing + int(tail_sway), cy + 1),
        ])

        # Hair (dark, spiky under bandana at back).
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["hair_dark"], [
            (cx - 7, cy - 3), (cx - 6, cy + 3),
            (cx - 8, cy + 4), (cx - 9, cy),
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["hair_mid"], [
            (cx - 6, cy - 2), (cx - 5, cy + 2),
            (cx - 7, cy + 3),
        ])

        # Eye (fierce).
        ex = cx + 2 * facing
        ey = cy
        pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["eye_dark"],
                         (ex - 1, ey, 3, 2))
        pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["eye_white"],
                         (ex, ey, 2, 1))
        pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["eye_blue"],
                         (ex + 1, ey, 1, 1))
        # Second eye (partial).
        pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["eye_dark"],
                         (cx - 3 * facing, ey, 2, 2))
        pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["eye_white"],
                         (cx - 3 * facing + 1, ey, 1, 1))

        # Eyebrow (angry).
        pygame.draw.line(surface, _NS_kaelthorn.PALETTE["hair_dark"],
                         (cx - 4, cy - 2), (cx + 5, cy - 2), 1)

        # Mouth (grim line).
        pygame.draw.line(surface, _NS_kaelthorn.PALETTE["muscle_deep"],
                         (cx - 2, cy + 4), (cx + 2, cy + 4), 1)

    def _draw_back_arm(surface, cx, cy, facing, phase, action, progress):
        """Back arm (further arm)."""
        shoulder_x = cx - facing * 10
        shoulder_y = cy - 8

        # Arm angle changes with action.
        arm_swing = math.sin(phase * 0.6) * 4
        if action == "attack":
            arm_swing = math.sin(progress * math.pi) * -10
        elif action == "spin":
            arm_swing = math.cos(progress * math.pi * 4) * 8
        elif action == "throw":
            if progress < 0.5:
                arm_swing = -8
            else:
                arm_swing = 12

        elbow_x = shoulder_x - facing * 6
        elbow_y = shoulder_y + 8 + int(arm_swing * 0.3)
        hand_x = elbow_x - facing * 4
        hand_y = elbow_y + 10 + int(arm_swing * 0.4)

        # Shadow.
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["shadow_deep"],
                              (shoulder_x + 2, shoulder_y + 2),
                              (elbow_x + 2, elbow_y + 2), 5)
        # Upper arm (bicep).
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["skin_darkest"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["skin_dark"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["skin_mid"],
                              (shoulder_x, shoulder_y - 1),
                              (elbow_x, elbow_y - 1), 1)
        # Forearm.
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["skin_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["skin_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 2)
        # Hand.
        _NS_kaelthorn._aacircle(surface, _NS_kaelthorn.PALETTE["skin_darkest"],
                                (hand_x, hand_y), 3)
        _NS_kaelthorn._aacircle(surface, _NS_kaelthorn.PALETTE["skin_dark"],
                                (hand_x, hand_y), 2)
        _NS_kaelthorn._aacircle(surface, _NS_kaelthorn.PALETTE["skin_mid"],
                                (hand_x, hand_y - 1), 1)

    def _draw_front_arm_blade(surface, cx, cy, facing, phase, action,
                               progress):
        """Front arm holding the blade."""
        shoulder_x = cx + facing * 10
        shoulder_y = cy - 8

        # Arm pose changes.
        if action == "attack":
            # Swing arc.
            angle = (progress - 0.5) * math.pi * 1.2
            elbow_x = shoulder_x + facing * int(math.cos(angle) * 8)
            elbow_y = shoulder_y + int(math.sin(angle) * 8) + 2
            hand_x = shoulder_x + facing * int(math.cos(angle) * 16)
            hand_y = shoulder_y + int(math.sin(angle) * 16) + 4
            blade_angle = angle + (0.3 if facing > 0 else -0.3)
        elif action == "charge":
            elbow_x = shoulder_x + facing * 6
            elbow_y = shoulder_y - 2
            hand_x = shoulder_x + facing * 14
            hand_y = shoulder_y - 4
            blade_angle = -0.3 if facing > 0 else math.pi + 0.3
        elif action == "throw":
            if progress < 0.5:
                # Wind up back.
                t = progress / 0.5
                elbow_x = shoulder_x - facing * int(t * 4)
                elbow_y = shoulder_y - int(t * 4)
                hand_x = shoulder_x - facing * int(t * 8)
                hand_y = shoulder_y - int(t * 8)
                blade_angle = math.pi * 0.7 if facing > 0 else math.pi * 0.3
            else:
                # Throw forward.
                t = (progress - 0.5) / 0.5
                elbow_x = shoulder_x + facing * int(t * 8)
                elbow_y = shoulder_y - 2
                hand_x = shoulder_x + facing * int(4 + t * 10)
                hand_y = shoulder_y - 2
                blade_angle = 0
        elif action == "spin":
            angle = progress * math.pi * 6
            elbow_x = shoulder_x + int(math.cos(angle) * 8)
            elbow_y = shoulder_y + int(math.sin(angle) * 4) + 2
            hand_x = shoulder_x + int(math.cos(angle) * 16)
            hand_y = shoulder_y + int(math.sin(angle) * 8) + 4
            blade_angle = angle + math.pi / 2
        elif action == "leap":
            if progress < 0.7:
                elbow_x = shoulder_x + facing * 4
                elbow_y = shoulder_y - 6
                hand_x = shoulder_x + facing * 6
                hand_y = shoulder_y - 14
                blade_angle = -math.pi / 2 if facing > 0 else -math.pi / 2
            else:
                elbow_x = shoulder_x + facing * 4
                elbow_y = shoulder_y + 6
                hand_x = shoulder_x + facing * 6
                hand_y = shoulder_y + 12
                blade_angle = math.pi / 2
        else:
            # Idle: blade held at ready.
            sway = math.sin(phase * 0.5) * 1
            elbow_x = shoulder_x + facing * 8
            elbow_y = shoulder_y + 6 + int(sway)
            hand_x = shoulder_x + facing * 14
            hand_y = shoulder_y + 10 + int(sway)
            blade_angle = -0.2 if facing > 0 else math.pi + 0.2

        # Shadow.
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["shadow_deep"],
                              (shoulder_x + 2, shoulder_y + 2),
                              (elbow_x + 2, elbow_y + 2), 6)
        # Upper arm.
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["skin_darkest"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["skin_dark"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["skin_mid"],
                              (shoulder_x, shoulder_y - 1),
                              (elbow_x, elbow_y - 1), 2)
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["skin_light"],
                              (shoulder_x, shoulder_y - 2),
                              (elbow_x, elbow_y - 2), 1)
        # Forearm.
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["skin_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["skin_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["skin_mid"],
                              (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
        # Wrist band (leather).
        _NS_kaelthorn._aacircle(surface, _NS_kaelthorn.PALETTE["cloth_darkest"],
                                (hand_x, hand_y), 4)
        _NS_kaelthorn._aacircle(surface, _NS_kaelthorn.PALETTE["cloth_dark"],
                                (hand_x, hand_y), 3)
        _NS_kaelthorn._aacircle(surface, _NS_kaelthorn.PALETTE["cloth_mid"],
                                (hand_x, hand_y - 1), 2)
        # Hand grip.
        _NS_kaelthorn._aacircle(surface, _NS_kaelthorn.PALETTE["skin_dark"],
                                (hand_x, hand_y), 2)

        # Draw blade if not thrown away.
        if action != "throw" or progress < 0.6:
            _NS_kaelthorn._draw_blade(surface, hand_x, hand_y, blade_angle,
                                       facing, phase, action, progress)

    def _draw_blade(surface, hx, hy, angle, facing, phase, action, progress):
        """Curved warrior blade with azure enchant glow."""
        # Blade length.
        length = 30
        # Direction vectors.
        dx = math.cos(angle) * facing
        dy = math.sin(angle)

        # Blade tip.
        tip_x = hx + int(dx * length)
        tip_y = hy + int(dy * length)

        # Perpendicular for width.
        perp_dx = -math.sin(angle) * facing
        perp_dy = math.cos(angle)

        # Curved blade points (slight curve upward).
        curve = 3
        curve_mid_x = hx + int(dx * length * 0.5) + int(perp_dx * curve)
        curve_mid_y = hy + int(dy * length * 0.5) + int(perp_dy * curve)

        # Blade shape.
        base_a = (hx + int(perp_dx * 3), hy + int(perp_dy * 3))
        base_b = (hx - int(perp_dx * 2), hy - int(perp_dy * 2))
        mid_a = (curve_mid_x + int(perp_dx * 4),
                 curve_mid_y + int(perp_dy * 4))
        mid_b = (curve_mid_x - int(perp_dx * 1),
                 curve_mid_y - int(perp_dy * 1))

        # Shadow.
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["shadow_deep"], [
            (base_a[0] + 2, base_a[1] + 2),
            (mid_a[0] + 2, mid_a[1] + 2),
            (tip_x + 2, tip_y + 2),
            (mid_b[0] + 2, mid_b[1] + 2),
            (base_b[0] + 2, base_b[1] + 2),
        ])
        # Blade body.
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["blade_darkest"], [
            base_a, mid_a, (tip_x, tip_y), mid_b, base_b,
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["blade_dark"], [
            base_a,
            (int((base_a[0] + mid_a[0]) / 2), int((base_a[1] + mid_a[1]) / 2)),
            (tip_x, tip_y),
            (int((base_b[0] + mid_b[0]) / 2), int((base_b[1] + mid_b[1]) / 2)),
            base_b,
        ])
        _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["blade_mid"], [
            (int(base_a[0] * 0.7 + base_b[0] * 0.3),
             int(base_a[1] * 0.7 + base_b[1] * 0.3)),
            (int(mid_a[0] * 0.7 + mid_b[0] * 0.3),
             int(mid_a[1] * 0.7 + mid_b[1] * 0.3)),
            (tip_x, tip_y),
        ])
        # Bright edge highlight.
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["blade_light"],
                              base_a, mid_a, 1)
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["blade_light"],
                              mid_a, (tip_x, tip_y), 1)
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["blade_shine"],
                              (int(base_a[0] * 0.5 + mid_a[0] * 0.5),
                               int(base_a[1] * 0.5 + mid_a[1] * 0.5)),
                              (tip_x, tip_y), 1)

        # Azure glow along blade edge.
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        alpha_glow = _NS_kaelthorn._alpha(200 * pulse)
        _NS_kaelthorn._aaline(surface,
                              (*_NS_kaelthorn.PALETTE["azure_light"],
                               alpha_glow),
                              base_a, (tip_x, tip_y), 1)
        # Tip glow.
        _NS_kaelthorn._aacircle(surface, _NS_kaelthorn.PALETTE["azure_mid"],
                                (tip_x, tip_y), 2)
        _NS_kaelthorn._aacircle(surface, _NS_kaelthorn.PALETTE["azure_light"],
                                (tip_x, tip_y), 1)
        pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["azure_shine"],
                         (tip_x, tip_y, 1, 1))

        # Cross-guard at hand.
        guard_a = (hx + int(perp_dx * 5), hy + int(perp_dy * 5))
        guard_b = (hx - int(perp_dx * 4), hy - int(perp_dy * 4))
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["gold_dark"],
                              guard_a, guard_b, 3)
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["gold_mid"],
                              guard_a, guard_b, 2)
        _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["gold_light"],
                              guard_a, guard_b, 1)

    def _draw_melee_swing(surface, cx, cy, facing, progress):
        """Blue slash arc during basic attack."""
        if progress < 0.3 or progress > 0.85:
            return
        t = (progress - 0.3) / 0.55

        # Arc from top to bottom sweep.
        start_angle = -math.pi / 3
        end_angle = math.pi / 3
        cur_angle = start_angle + (end_angle - start_angle) * t

        # Arc trail (multiple segments fading).
        for i in range(8):
            trail_t = t - i * 0.05
            if trail_t < 0:
                continue
            a = start_angle + (end_angle - start_angle) * trail_t
            radius = 26
            arc_x = cx + int(math.cos(a) * radius) * facing
            arc_y = cy - 6 + int(math.sin(a) * radius)
            alpha = _NS_kaelthorn._alpha(220 - i * 25)

            _NS_kaelthorn._aacircle(surface,
                                    (*_NS_kaelthorn.PALETTE["azure_dark"],
                                     alpha), (arc_x, arc_y), 4)
            _NS_kaelthorn._aacircle(surface,
                                    (*_NS_kaelthorn.PALETTE["azure_mid"],
                                     alpha), (arc_x, arc_y), 3)
            _NS_kaelthorn._aacircle(surface,
                                    (*_NS_kaelthorn.PALETTE["azure_light"],
                                     alpha), (arc_x, arc_y), 2)
            pygame.draw.rect(surface,
                             (*_NS_kaelthorn.PALETTE["azure_hot"], alpha),
                             (arc_x, arc_y, 1, 1))

    # ============================================================
    # FLOAT PARTICLES
    # ============================================================
    def _draw_float_particles(surface, cx, cy, phase, intense=False):
        """Azure energy particles floating under boss (levitation)."""
        strength = 1.5 if intense else 1.0

        # Base energy pool (small ellipse under feet).
        pool = pygame.Surface((80, 24), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for r in range(18, 2, -2):
            alpha = _NS_kaelthorn._alpha((18 - r) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(pool,
                                    (*_NS_kaelthorn.PALETTE["azure_dark"],
                                     alpha),
                                    (40 - r, 12 - r // 4,
                                     r * 2, max(2, r // 2)))
        for r in range(10, 1, -1):
            alpha = _NS_kaelthorn._alpha((10 - r) * 6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(pool,
                                    (*_NS_kaelthorn.PALETTE["azure_mid"],
                                     alpha),
                                    (40 - r, 12 - r // 4,
                                     r * 2, max(2, r // 3)))
        surface.blit(pool, (cx - 40, cy - 5))

        # Rising sparkles.
        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            sx = cx - 20 + i * 5 + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 24)
            alpha = _NS_kaelthorn._alpha(230 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_kaelthorn._aacircle(surface,
                                    (*_NS_kaelthorn.PALETTE["azure_dark"],
                                     alpha), (sx, sy), 2)
            pygame.draw.rect(surface,
                             (*_NS_kaelthorn.PALETTE["azure_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_kaelthorn.PALETTE["azure_hot"], alpha),
                             (sx, sy - 2, 1, 1))

        # Small crystals scattered.
        for i in range(4):
            angle = phase * 0.8 + i * math.pi / 2
            sx = cx + int(math.cos(angle) * 22)
            sy = cy + 8 + int(math.sin(angle) * 4)
            pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["azure_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["azure_hot"],
                             (sx, sy, 1, 1))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((100, 24), pygame.SRCALPHA)
        for r in range(12, 0, -1):
            alpha = max(0, (12 - r) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - r, 12 - r,
                                 80 + r * 2, r * 2))
        pygame.draw.ellipse(shadow, (5, 10, 25, 160), (5, 6, 90, 12))
        pygame.draw.ellipse(shadow, (30, 80, 180, 90), (12, 8, 76, 8))
        surface.blit(shadow, (x - 50, y - 12))

    def _draw_azure_aura(surface, x, y, phase):
        """Blue heroic aura."""
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75
        aura = pygame.Surface((200, 160), pygame.SRCALPHA)
        for r in range(80, 5, -5):
            alpha = _NS_kaelthorn._alpha((80 - r) * 1.2 * pulse)
            if alpha > 0:
                _NS_kaelthorn._aacircle(aura,
                                        (*_NS_kaelthorn.PALETTE["azure_darkest"],
                                         alpha), (100, 80), r)
        for r in range(50, 5, -4):
            alpha = _NS_kaelthorn._alpha((50 - r) * 1.5 * pulse)
            if alpha > 0:
                _NS_kaelthorn._aacircle(aura,
                                        (*_NS_kaelthorn.PALETTE["azure_dark"],
                                         alpha), (100, 80), r)
        surface.blit(aura, (x - 100, y - 80))

        # Floating sparkles around.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            radius = 40 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["azure_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["azure_hot"],
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground rune ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((150, 46), pygame.SRCALPHA)
        pygame.draw.ellipse(ring,
                            (*_NS_kaelthorn.PALETTE["rune_dark"], 200),
                            (5, 15, 140, 22), 3)
        pygame.draw.ellipse(ring,
                            (*_NS_kaelthorn.PALETTE["azure_darkest"], 220),
                            (14, 17, 122, 18), 2)
        pygame.draw.ellipse(ring,
                            (*_NS_kaelthorn.PALETTE["azure_dark"], 230),
                            (25, 19, 100, 14), 1)

        # Runes around ring.
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 75 + int(math.cos(angle) * 40)
            y1 = 26 + int(math.sin(angle) * 7)
            x2 = 75 + int(math.cos(angle) * 62)
            y2 = 26 + int(math.sin(angle) * 11)
            pygame.draw.line(ring,
                             (*_NS_kaelthorn.PALETTE["azure_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_kaelthorn.PALETTE["azure_hot"],
                                 _NS_kaelthorn._alpha(150 * pulse)),
                                (15, 10, 120, 32), 1)
        surface.blit(ring, (x - 75, y - 23))

    # ============================================================
    # SKILL Q: BRAVEST FIGHTER - charging slash
    # ============================================================
    def _draw_bravest_fighter_fx(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.4:
            # Charge trail behind.
            for i in range(6):
                tx = x - facing * (i * 8)
                ty = y + 5 + int(math.sin(phase + i) * 3)
                alpha = _NS_kaelthorn._alpha(200 - i * 30)
                _NS_kaelthorn._aacircle(surface,
                                        (*_NS_kaelthorn.PALETTE["azure_mid"],
                                         alpha), (tx, ty), 4)
                _NS_kaelthorn._aacircle(surface,
                                        (*_NS_kaelthorn.PALETTE["azure_light"],
                                         alpha), (tx, ty), 2)
        else:
            # Big slash arc in front.
            t = (progress - 0.4) / 0.6
            arc_intensity = math.sin(t * math.pi)

            # Large crescent slash.
            for offset in range(3):
                for i in range(15):
                    a = -math.pi / 2 + (i / 14) * math.pi
                    radius = 45 - offset * 6
                    ax = x + int(math.cos(a) * radius) * facing
                    ay = y + int(math.sin(a) * radius)
                    alpha = _NS_kaelthorn._alpha(240 * arc_intensity
                                                  - offset * 30)
                    if alpha <= 0:
                        continue
                    size = 5 - offset
                    _NS_kaelthorn._aacircle(surface,
                                            (*_NS_kaelthorn.PALETTE["azure_darkest"],
                                             alpha), (ax, ay), size + 1)
                    _NS_kaelthorn._aacircle(surface,
                                            (*_NS_kaelthorn.PALETTE["azure_mid"],
                                             alpha), (ax, ay), size)
                    _NS_kaelthorn._aacircle(surface,
                                            (*_NS_kaelthorn.PALETTE["azure_light"],
                                             alpha), (ax, ay), max(1, size - 2))
                    pygame.draw.rect(surface,
                                     (*_NS_kaelthorn.PALETTE["azure_hot"], alpha),
                                     (ax, ay, 1, 1))

    # ============================================================
    # SKILL W: JUSTICE BLADE - throw projectile
    # ============================================================
    def _draw_justice_blade_fx(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kaelthorn._target_position(boss, x, y)

        if progress < 0.4:
            # Charge in hand.
            hx = x + facing * 16
            hy = y - 12
            cr = int(3 + progress / 0.4 * 5)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_kaelthorn._alpha(200 * (cr + 3 - r) / (cr + 3))
                _NS_kaelthorn._aacircle(surface,
                                        (*_NS_kaelthorn.PALETTE["azure_mid"],
                                         alpha), (hx, hy), r)
            _NS_kaelthorn._aacircle(surface, _NS_kaelthorn.PALETTE["azure_light"],
                                    (hx, hy), max(1, cr - 2))
            pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["azure_shine"],
                             (hx, hy, 1, 1))
        else:
            # Projectile flies as arrow-blade.
            t = (progress - 0.4) / 0.6
            sx = x + facing * 20
            sy = y - 8
            bx = int(sx + (tx - sx) * t)
            by = int(sy + (ty - sy) * t)

            # Trail behind.
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(sx + (tx - sx) * trail_t)
                py = int(sy + (ty - sy) * trail_t)
                alpha = _NS_kaelthorn._alpha(220 - i * 22)
                size = max(1, 6 - i)
                _NS_kaelthorn._aacircle(surface,
                                        (*_NS_kaelthorn.PALETTE["azure_darkest"],
                                         alpha), (px, py), size + 1)
                _NS_kaelthorn._aacircle(surface,
                                        (*_NS_kaelthorn.PALETTE["azure_mid"],
                                         alpha), (px, py), size)
                _NS_kaelthorn._aacircle(surface,
                                        (*_NS_kaelthorn.PALETTE["azure_light"],
                                         alpha), (px, py), max(1, size - 2))

            # Projectile body - arrow blade shape.
            angle = math.atan2(ty - sy, tx - sx)
            tip_x = bx + int(math.cos(angle) * 10)
            tip_y = by + int(math.sin(angle) * 10)
            perp = angle + math.pi / 2
            a_x = bx + int(math.cos(perp) * 4)
            a_y = by + int(math.sin(perp) * 4)
            b_x = bx - int(math.cos(perp) * 4)
            b_y = by - int(math.sin(perp) * 4)
            back_x = bx - int(math.cos(angle) * 6)
            back_y = by - int(math.sin(angle) * 6)

            _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["azure_dark"], [
                (tip_x, tip_y), (a_x, a_y), (back_x, back_y), (b_x, b_y),
            ])
            _NS_kaelthorn._poly(surface, _NS_kaelthorn.PALETTE["azure_mid"], [
                (tip_x, tip_y),
                (int((tip_x + a_x) / 2), int((tip_y + a_y) / 2)),
                (back_x, back_y),
                (int((tip_x + b_x) / 2), int((tip_y + b_y) / 2)),
            ])
            _NS_kaelthorn._aaline(surface, _NS_kaelthorn.PALETTE["azure_shine"],
                                  (tip_x, tip_y), (back_x, back_y), 1)
            pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["white"],
                             (tip_x, tip_y, 1, 1))

            # Impact.
            if t > 0.9:
                st = (t - 0.9) / 0.1
                radius = int(6 + st * 20)
                alpha = _NS_kaelthorn._alpha(240 * (1 - st))
                _NS_kaelthorn._aacircle(surface,
                                        (*_NS_kaelthorn.PALETTE["azure_dark"],
                                         alpha), (tx, ty), radius, 3)
                _NS_kaelthorn._aacircle(surface,
                                        (*_NS_kaelthorn.PALETTE["azure_light"],
                                         alpha), (tx, ty),
                                        max(1, radius - 6), 2)
                for i in range(8):
                    aa = i * math.pi / 4
                    ex = tx + int(math.cos(aa) * radius)
                    ey = ty + int(math.sin(aa) * radius)
                    pygame.draw.rect(surface,
                                     (*_NS_kaelthorn.PALETTE["azure_hot"],
                                      alpha), (ex, ey, 2, 2))

    # ============================================================
    # SKILL E: DEFENDER'S ASSAULT - spin blade around
    # ============================================================
    def _draw_spin_ground(surface, boss, x, y, timer, phase):
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Expanding ground circle.
        r = int(20 + progress * 30)
        alpha = _NS_kaelthorn._alpha(200 * (1 - progress * 0.5))
        pygame.draw.ellipse(surface,
                            (*_NS_kaelthorn.PALETTE["azure_dark"], alpha),
                            (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 2)
        pygame.draw.ellipse(surface,
                            (*_NS_kaelthorn.PALETTE["azure_mid"], alpha),
                            (x - r + 3, y + 40 - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 1)

    def _draw_defenders_assault_fx(surface, boss, x, y, timer, phase):
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Spinning blade arcs around boss.
        num_arcs = 3
        for arc_i in range(num_arcs):
            spin_angle = progress * math.pi * 8 + arc_i * (math.pi * 2 / num_arcs)
            for i in range(12):
                a = spin_angle + i * 0.15
                radius = 30 + int(math.sin(phase + i) * 3)
                px = x + int(math.cos(a) * radius)
                py = y - 4 + int(math.sin(a) * radius * 0.5)
                alpha = _NS_kaelthorn._alpha(220 - i * 15)
                size = max(1, 5 - i // 2)
                _NS_kaelthorn._aacircle(surface,
                                        (*_NS_kaelthorn.PALETTE["azure_dark"],
                                         alpha), (px, py), size + 1)
                _NS_kaelthorn._aacircle(surface,
                                        (*_NS_kaelthorn.PALETTE["azure_mid"],
                                         alpha), (px, py), size)
                _NS_kaelthorn._aacircle(surface,
                                        (*_NS_kaelthorn.PALETTE["azure_light"],
                                         alpha), (px, py), max(1, size - 2))
                pygame.draw.rect(surface,
                                 (*_NS_kaelthorn.PALETTE["azure_hot"], alpha),
                                 (px, py, 1, 1))

        # Central swirl.
        for i in range(6):
            angle = progress * math.pi * 10 + i * math.pi / 3
            r = 15
            sx = x + int(math.cos(angle) * r)
            sy = y - 4 + int(math.sin(angle) * r * 0.5)
            pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["azure_shine"],
                             (sx, sy, 2, 2))

    # ============================================================
    # SKILL R: CHIVALRY FISTS - leap and slam
    # ============================================================
    def _draw_leap_ground(surface, boss, x, y, timer, pulse):
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.7:
            # Impact crystals rising from ground.
            t = (progress - 0.7) / 0.3
            r = int(20 + t * 40)
            alpha = _NS_kaelthorn._alpha(240 * (1 - t * 0.5))
            pygame.draw.ellipse(surface,
                                (*_NS_kaelthorn.PALETTE["azure_darkest"],
                                 alpha),
                                (x - r, y + 40 - r // 3,
                                 r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_kaelthorn.PALETTE["azure_dark"], alpha),
                                (x - r + 3, y + 40 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))

    def _draw_chivalry_fists_fx(surface, boss, x, y, timer, phase):
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.4:
            # Rising blue energy under boss during leap.
            for i in range(8):
                t = (phase * 1.2 + i * 0.13) % 1.0
                sx = x - 20 + i * 5 + int(math.sin(phase + i) * 3)
                sy = y + 40 - int(t * 40)
                alpha = _NS_kaelthorn._alpha(220 * (1 - t))
                _NS_kaelthorn._aacircle(surface,
                                        (*_NS_kaelthorn.PALETTE["azure_mid"],
                                         alpha), (sx, sy), 3)
                pygame.draw.rect(surface,
                                 (*_NS_kaelthorn.PALETTE["azure_hot"], alpha),
                                 (sx, sy, 1, 1))
        elif progress < 0.7:
            # Hanging in air (glowing).
            for i in range(6):
                angle = phase * 2 + i * math.pi / 3
                sx = x + int(math.cos(angle) * 20)
                sy = y - 60 + int(math.sin(angle) * 8)
                _NS_kaelthorn._aacircle(surface,
                                        _NS_kaelthorn.PALETTE["azure_mid"],
                                        (sx, sy), 3)
                pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["azure_shine"],
                                 (sx, sy, 1, 1))
        else:
            # SLAM - crystal spikes erupt from ground.
            t = (progress - 0.7) / 0.3

            # Central impact burst.
            burst_r = int(15 + t * 25)
            burst_alpha = _NS_kaelthorn._alpha(255 * (1 - t))
            _NS_kaelthorn._aacircle(surface,
                                    (*_NS_kaelthorn.PALETTE["azure_shine"],
                                     burst_alpha), (x, y + 30),
                                    burst_r // 3)
            _NS_kaelthorn._aacircle(surface,
                                    (*_NS_kaelthorn.PALETTE["azure_hot"],
                                     burst_alpha), (x, y + 30),
                                    burst_r // 2)

            # Crystal spike columns rising from ground (like Lapu Lapu R).
            num_spikes = 12
            for i in range(num_spikes):
                # Spread outward.
                spread_dist = 15 + (i % 4) * 12
                angle = i * math.pi * 2 / num_spikes
                spike_x = x + int(math.cos(angle) * spread_dist)
                spike_base_y = y + 40 + int(math.sin(angle) * spread_dist * 0.4)

                # Spike grows then falls.
                spike_h = int((1 - abs(t - 0.5) * 2) * 30)
                if spike_h < 2:
                    continue

                spike_tip_y = spike_base_y - spike_h
                spike_width = 4

                # Shadow.
                _NS_kaelthorn._poly(surface,
                                    _NS_kaelthorn.PALETTE["shadow_deep"], [
                    (spike_x + 1, spike_tip_y + 1),
                    (spike_x - spike_width + 1, spike_base_y + 1),
                    (spike_x + spike_width + 1, spike_base_y + 1),
                ])
                # Spike body.
                _NS_kaelthorn._poly(surface,
                                    _NS_kaelthorn.PALETTE["azure_darkest"], [
                    (spike_x, spike_tip_y),
                    (spike_x - spike_width, spike_base_y),
                    (spike_x + spike_width, spike_base_y),
                ])
                _NS_kaelthorn._poly(surface,
                                    _NS_kaelthorn.PALETTE["azure_dark"], [
                    (spike_x, spike_tip_y),
                    (spike_x - spike_width + 1, spike_base_y),
                    (spike_x + spike_width - 1, spike_base_y),
                ])
                _NS_kaelthorn._poly(surface,
                                    _NS_kaelthorn.PALETTE["azure_mid"], [
                    (spike_x, spike_tip_y),
                    (spike_x - 1, spike_base_y),
                    (spike_x + 1, spike_base_y),
                ])
                # Bright edge.
                _NS_kaelthorn._aaline(surface,
                                      _NS_kaelthorn.PALETTE["azure_light"],
                                      (spike_x, spike_tip_y),
                                      (spike_x - spike_width, spike_base_y), 1)
                pygame.draw.rect(surface,
                                 _NS_kaelthorn.PALETTE["azure_shine"],
                                 (spike_x, spike_tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_kaelthorn.PALETTE["white"],
                                 (spike_x, spike_tip_y, 1, 1))

            # Debris rocks flying.
            for i in range(12):
                debris_t = (phase * 1.5 + i * 0.15) % 1.0
                if debris_t > t:
                    continue
                angle = i * math.pi / 6
                dist = int(debris_t * 40)
                dx = x + int(math.cos(angle) * dist)
                dy = y + 30 - int(debris_t * 20) + int(debris_t ** 2 * 15)
                pygame.draw.rect(surface,
                                 _NS_kaelthorn.PALETTE["cloth_dark"],
                                 (dx, dy, 2, 2))
                pygame.draw.rect(surface,
                                 _NS_kaelthorn.PALETTE["cloth_mid"],
                                 (dx, dy, 1, 1))


# ====================================================================
# solvanth.py
# ====================================================================

"""
SOLVANTH - The Radiant Guardian
Mini boss centaur dengan armor emas dan staff kristal biru.
Gaya rendering mengikuti _NS_vhorethzir.
"""



class _NS_solvanth:
    """Namespace solvanth - centaur guardian mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin (upper body, tan)
        "skin_darkest": (60, 35, 25),
        "skin_dark": (115, 75, 50),
        "skin_mid": (175, 125, 85),
        "skin_light": (220, 175, 130),
        "skin_shine": (245, 215, 175),

        # Horse body (tan/palomino)
        "horse_darkest": (55, 35, 20),
        "horse_dark": (105, 70, 35),
        "horse_mid": (165, 120, 65),
        "horse_light": (215, 175, 110),
        "horse_shine": (245, 215, 155),

        # Horse mane/tail (darker tan)
        "mane_dark": (45, 25, 10),
        "mane_mid": (95, 60, 25),
        "mane_light": (155, 105, 55),

        # Hooves (dark brown)
        "hoof_dark": (25, 15, 8),
        "hoof_mid": (55, 35, 20),
        "hoof_light": (100, 70, 40),

        # Gold armor (main theme)
        "gold_darkest": (60, 40, 5),
        "gold_dark": (120, 85, 15),
        "gold_mid": (200, 155, 35),
        "gold_light": (245, 215, 90),
        "gold_shine": (255, 245, 180),
        "gold_bright": (255, 255, 230),

        # Silver armor accents
        "silver_dark": (75, 80, 95),
        "silver_mid": (150, 155, 170),
        "silver_light": (215, 220, 230),
        "silver_shine": (250, 252, 255),

        # Blue crystal (staff top, gems)
        "crystal_darkest": (10, 25, 60),
        "crystal_dark": (30, 70, 150),
        "crystal_mid": (70, 140, 230),
        "crystal_light": (150, 210, 255),
        "crystal_shine": (230, 245, 255),

        # Hair (blonde/gold)
        "hair_dark": (95, 65, 20),
        "hair_mid": (170, 130, 50),
        "hair_light": (230, 195, 100),

        # Radiant holy light (skill theme)
        "holy_darkest": (60, 40, 5),
        "holy_dark": (150, 100, 20),
        "holy_mid": (240, 190, 40),
        "holy_light": (255, 230, 130),
        "holy_hot": (255, 245, 200),
        "holy_shine": (255, 255, 240),

        # Eye
        "eye_dark": (20, 15, 10),
        "eye_white": (240, 235, 220),
        "eye_blue": (80, 160, 230),

        # Rune ground
        "rune_dark": (60, 45, 10),
        "rune_mid": (180, 140, 30),
        "rune_light": (255, 220, 100),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    # ============================================================
    # HELPERS
    # ============================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_solvanth._clamp(color)
        if _NS_solvanth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_solvanth._clamp(color)
        if _NS_solvanth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        # Validate points: harus list of (x, y) tuples/pairs
        valid_points = []
        for p in points:
            try:
                if hasattr(p, '__len__') and len(p) >= 2:
                    valid_points.append((int(p[0]), int(p[1])))
            except (TypeError, ValueError):
                continue

        if len(valid_points) < 3:
            if len(valid_points) == 2:
                pygame.draw.line(surface, _NS_solvanth._clamp(color),
                                 valid_points[0], valid_points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_solvanth._clamp(color), valid_points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar
            # (x, y) dengan kompensasi scale (hero di-render di
            # canvas lalu di-scale; boss langsung di layar).
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return int(x + 220 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_solvanth(surface, boss, x, y):
        """Entry point utama."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_solvanth._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_sv_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_solvanth._draw_holy_aura(surface, x, y, pulse)
        _NS_solvanth._draw_ground_ring(surface, x, y + 60, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "q":
            _NS_solvanth._draw_ring_punishment_ground(surface, boss, x, y,
                                                       skill_timer, pulse)
        elif active_skill == "w":
            _NS_solvanth._draw_glorious_pathway_ground(surface, boss, x, y,
                                                        skill_timer, pulse)
        elif active_skill == "e":
            _NS_solvanth._draw_law_order_ground(surface, boss, x, y,
                                                 skill_timer, pulse)
        elif active_skill == "r":
            _NS_solvanth._draw_wrath_ground(surface, boss, x, y,
                                             skill_timer, pulse)

        # Body (always floating - bob).
        if active_skill == "r":
            _NS_solvanth._draw_body_leap(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_solvanth._draw_body_smash(surface, boss, x, y, skill_timer, pulse)
        elif active_skill in ("q", "w"):
            _NS_solvanth._draw_body_cast(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_solvanth._draw_body_attack(surface, boss, x, y)
        else:
            _NS_solvanth._draw_body_idle(surface, boss, x, y)

        # Foreground skill FX.
        if active_skill == "q":
            _NS_solvanth._draw_ring_punishment_fg(surface, boss, x, y,
                                                    skill_timer, pulse)
        elif active_skill == "e":
            _NS_solvanth._draw_law_order_fg(surface, boss, x, y,
                                             skill_timer, pulse)
        elif active_skill == "r":
            _NS_solvanth._draw_wrath_fg(surface, boss, x, y,
                                         skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_sv_previous_timer", 0))
        active = bool(getattr(boss, "_sv_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._sv_attack_active = True
            boss._sv_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._sv_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._sv_attack_frame = int(getattr(boss, "_sv_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._sv_attack_active = False
            boss._sv_attack_frame = 0
            active = False

        boss._sv_previous_timer = timer
        boss._sv_attack_progress = (
            min(1.0, getattr(boss, "_sv_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 4)
        _NS_solvanth._draw_shadow(surface, x, y + 55)
        _NS_solvanth._draw_float_particles(surface, x, y + 45, boss.pulse)
        _NS_solvanth._draw_centaur_body(surface, x, y + bob, boss.direction,
                                          boss.pulse, "idle")

    def _draw_body_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_sv_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_sv_attack_dir", None)
        if facing is None:
            facing = boss.direction
        bob = int(math.sin(boss.pulse * 0.7) * 3)
        # Slight forward motion during swing.
        if progress < 0.5:
            lunge = int(progress * 6) * facing
        else:
            lunge = int((1 - progress) * 6) * facing

        _NS_solvanth._draw_shadow(surface, x + lunge, y + 55)
        _NS_solvanth._draw_float_particles(surface, x + lunge, y + 45, boss.pulse)
        _NS_solvanth._draw_centaur_body(surface, x + lunge, y + bob,
                                          facing, boss.pulse,
                                          "attack", progress)
        _NS_solvanth._draw_melee_swing(surface, x + lunge, y + bob - 5,
                                        facing, progress)

    def _draw_body_cast(surface, boss, x, y, timer, pulse):
        bob = int(math.sin(pulse * 0.7) * 3)
        # Slight lift while casting.
        lift = int(math.sin(pulse * 2) * 2) + 2
        _NS_solvanth._draw_shadow(surface, x, y + 55)
        _NS_solvanth._draw_float_particles(surface, x, y + 45, pulse,
                                             intense=True)
        _NS_solvanth._draw_centaur_body(surface, x, y + bob - lift,
                                          boss.direction, pulse, "cast")

    def _draw_body_smash(surface, boss, x, y, timer, pulse):
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        bob = int(math.sin(pulse * 0.7) * 3)
        # Rear up then slam.
        if progress < 0.4:
            t = progress / 0.4
            lift = int(t * 12)
        elif progress < 0.6:
            lift = 12
        else:
            t = (progress - 0.6) / 0.4
            lift = int(12 * (1 - t))

        _NS_solvanth._draw_shadow(surface, x, y + 55)
        _NS_solvanth._draw_float_particles(surface, x, y + 45, pulse,
                                             intense=True)
        _NS_solvanth._draw_centaur_body(surface, x, y + bob - lift,
                                          boss.direction, pulse, "smash",
                                          progress)

    def _draw_body_leap(surface, boss, x, y, timer, pulse):
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Big leap up then slam.
        if progress < 0.4:
            t = progress / 0.4
            lift = int(t * 80)
        elif progress < 0.7:
            lift = 80
        else:
            t = (progress - 0.7) / 0.3
            lift = int(80 * (1 - t) - t * 5)

        _NS_solvanth._draw_shadow(surface, x, y + 55)
        _NS_solvanth._draw_float_particles(surface, x, y + 45, pulse)
        _NS_solvanth._draw_centaur_body(surface, x, y + bob_offset(pulse) - lift,
                                          boss.direction, pulse, "leap",
                                          progress)


    # ============================================================
    # CENTAUR BODY (Horse + Human torso + Helmet + Staff)
    # ============================================================
    def _draw_centaur_body(surface, cx, cy, facing, phase, action,
                            progress=0):
        """Full centaur: horse body + human torso + helmet + staff."""
        # Order: back legs, horse body, front legs, tail, human torso,
        # arms, head/helmet, staff.
        _NS_solvanth._draw_horse_back_legs(surface, cx, cy, facing, phase, action)
        _NS_solvanth._draw_horse_body(surface, cx, cy, facing, phase, action)
        _NS_solvanth._draw_horse_tail(surface, cx, cy, facing, phase)
        _NS_solvanth._draw_horse_front_legs(surface, cx, cy, facing, phase, action)
        _NS_solvanth._draw_human_torso(surface, cx, cy, facing, phase, action)
        _NS_solvanth._draw_helmet_head(surface, cx, cy, facing, phase, action)
        _NS_solvanth._draw_back_arm(surface, cx, cy, facing, phase, action, progress)
        _NS_solvanth._draw_staff_arm(surface, cx, cy, facing, phase, action, progress)


    def _draw_horse_back_legs(surface, cx, cy, facing, phase, action):
        """Two back legs (hind legs of horse)."""
        # Back legs are further from viewer (behind).
        for leg_i, side in enumerate([-1, 1]):
            base_x = cx - facing * 18 + side * 3
            base_y = cy + 20
            knee_x = base_x + side * 2
            knee_y = cy + 32
            hoof_x = base_x + side
            hoof_y = cy + 50

            # Shadow.
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["shadow_deep"],
                                  (base_x + 2, base_y + 2), (hoof_x + 2, hoof_y + 2), 6)
            # Thigh.
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["horse_darkest"],
                                  (base_x, base_y), (knee_x, knee_y), 7)
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["horse_dark"],
                                  (base_x, base_y), (knee_x, knee_y), 5)
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["horse_mid"],
                                  (base_x, base_y - 1), (knee_x, knee_y - 1), 2)
            # Shin.
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["horse_darkest"],
                                  (knee_x, knee_y), (hoof_x, hoof_y), 4)
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["horse_dark"],
                                  (knee_x, knee_y), (hoof_x, hoof_y), 2)
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["horse_mid"],
                                  (knee_x, knee_y - 1), (hoof_x, hoof_y - 1), 1)
            # Hoof.
            _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["hoof_dark"], [
                (hoof_x - 3, hoof_y - 2), (hoof_x + 3, hoof_y - 2),
                (hoof_x + 3, hoof_y + 2), (hoof_x - 3, hoof_y + 2),
            ])
            _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["hoof_mid"], [
                (hoof_x - 2, hoof_y - 1), (hoof_x + 2, hoof_y - 1),
                (hoof_x + 2, hoof_y + 1), (hoof_x - 2, hoof_y + 1),
            ])
            # Gold hoof ring.
            pygame.draw.line(surface, _NS_solvanth.PALETTE["gold_mid"],
                             (hoof_x - 3, hoof_y - 2), (hoof_x + 3, hoof_y - 2), 1)
            pygame.draw.rect(surface, _NS_solvanth.PALETTE["gold_light"],
                             (hoof_x, hoof_y - 2, 1, 1))


    def _draw_horse_body(surface, cx, cy, facing, phase, action):
        """Horse body (barrel + rump)."""
        # Main horse barrel (elongated horizontally).
        body_shape = [
            (cx - 22, cy + 6),
            (cx - 24, cy + 12),
            (cx - 22, cy + 22),
            (cx - 14, cy + 26),
            (cx + 8, cy + 26),
            (cx + 18, cy + 24),
            (cx + 22, cy + 18),
            (cx + 20, cy + 10),
            (cx + 14, cy + 6),
            (cx + 4, cy + 4),
            (cx - 10, cy + 4),
        ]
        # Shadow.
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["shadow_deep"],
                            [(px + 2, py + 3) for px, py in body_shape])
        # Base dark.
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["horse_darkest"], body_shape)
        # Mid tone.
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["horse_dark"], [
            (cx - 20, cy + 8), (cx - 22, cy + 14),
            (cx - 20, cy + 20), (cx - 12, cy + 24),
            (cx + 8, cy + 24), (cx + 16, cy + 22),
            (cx + 20, cy + 16), (cx + 18, cy + 10),
            (cx + 12, cy + 7), (cx - 8, cy + 6),
        ])
        # Highlight.
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["horse_mid"], [
            (cx - 16, cy + 8), (cx - 18, cy + 14),
            (cx - 14, cy + 18), (cx + 6, cy + 20),
            (cx + 14, cy + 18), (cx + 16, cy + 12),
            (cx + 10, cy + 8), (cx - 4, cy + 7),
        ])
        # Top light stripe.
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["horse_light"], [
            (cx - 12, cy + 8), (cx + 8, cy + 8),
            (cx + 10, cy + 10), (cx - 10, cy + 10),
        ])
        # Shine spots.
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["horse_shine"],
                         (cx - 6, cy + 9, 3, 1))
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["horse_shine"],
                         (cx + 4, cy + 9, 2, 1))

        # Horse chest armor plate (silver).
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["silver_dark"], [
            (cx + facing * 10, cy + 6), (cx + facing * 22, cy + 10),
            (cx + facing * 22, cy + 18), (cx + facing * 12, cy + 16),
        ])
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["silver_mid"], [
            (cx + facing * 12, cy + 7), (cx + facing * 20, cy + 11),
            (cx + facing * 20, cy + 16), (cx + facing * 14, cy + 14),
        ])
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["silver_light"], [
            (cx + facing * 14, cy + 9), (cx + facing * 18, cy + 12),
            (cx + facing * 17, cy + 14), (cx + facing * 15, cy + 12),
        ])
        # Gold trim on chest plate.
        pygame.draw.line(surface, _NS_solvanth.PALETTE["gold_dark"],
                         (cx + facing * 10, cy + 6), (cx + facing * 22, cy + 10), 1)
        pygame.draw.line(surface, _NS_solvanth.PALETTE["gold_mid"],
                         (cx + facing * 11, cy + 7), (cx + facing * 21, cy + 11), 1)
        # Blue crystal on chest plate.
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["crystal_dark"],
                         (cx + facing * 16, cy + 11, 3, 3))
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["crystal_mid"],
                         (cx + facing * 17, cy + 12, 2, 2))
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["crystal_shine"],
                         (cx + facing * 17, cy + 12, 1, 1))

        # Side armor plates (gold on flank).
        for i in range(2):
            plate_x = cx - 12 + i * 8
            _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_darkest"], [
                (plate_x, cy + 14), (plate_x + 6, cy + 14),
                (plate_x + 7, cy + 22), (plate_x - 1, cy + 22),
            ])
            _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_dark"], [
                (plate_x + 1, cy + 15), (plate_x + 5, cy + 15),
                (plate_x + 6, cy + 21), (plate_x, cy + 21),
            ])
            _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_mid"], [
                (plate_x + 2, cy + 16), (plate_x + 4, cy + 16),
                (plate_x + 5, cy + 20), (plate_x + 1, cy + 20),
            ])
            pygame.draw.rect(surface, _NS_solvanth.PALETTE["gold_light"],
                             (plate_x + 2, cy + 17, 2, 1))
            pygame.draw.rect(surface, _NS_solvanth.PALETTE["gold_shine"],
                             (plate_x + 2, cy + 17, 1, 1))


    def _draw_horse_tail(surface, cx, cy, facing, phase):
        """Flowing horse tail at back."""
        tail_sway = math.sin(phase * 0.6) * 3
        base_x = cx - facing * 22
        base_y = cy + 8

        # Multiple hair strands.
        for i, (offset_x, offset_y, length) in enumerate([
            (-6, 2, 20), (-8, 6, 24), (-6, 10, 22),
            (-4, 14, 18), (-10, 4, 22),
        ]):
            wave = math.sin(phase * 0.8 + i * 0.5) * 2
            start = (base_x + offset_x * facing, base_y + offset_y)
            mid = (start[0] - facing * (length * 0.5) + int(wave),
                   start[1] + int(length * 0.3))
            end = (start[0] - facing * length + int(tail_sway),
                   start[1] + int(length * 0.6) + int(wave))

            # Shadow.
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["shadow_deep"],
                                  (start[0] + 2, start[1] + 2),
                                  (mid[0] + 2, mid[1] + 2), 3)
            # Main strand.
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["mane_dark"],
                                  start, mid, 3)
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["mane_dark"],
                                  mid, end, 2)
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["mane_mid"],
                                  start, mid, 1)
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["mane_mid"],
                                  mid, end, 1)
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["mane_light"],
                                  (start[0], start[1] - 1),
                                  (mid[0], mid[1] - 1), 1)


    def _draw_horse_front_legs(surface, cx, cy, facing, phase, action):
        """Two front legs (visible)."""
        for leg_i, side in enumerate([-1, 1]):
            base_x = cx + facing * 14 + side * 3
            base_y = cy + 22
            knee_x = base_x + side
            knee_y = cy + 34
            hoof_x = base_x
            hoof_y = cy + 50

            # Shadow.
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["shadow_deep"],
                                  (base_x + 2, base_y + 2), (hoof_x + 2, hoof_y + 2), 7)
            # Thigh.
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["horse_darkest"],
                                  (base_x, base_y), (knee_x, knee_y), 8)
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["horse_dark"],
                                  (base_x, base_y), (knee_x, knee_y), 6)
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["horse_mid"],
                                  (base_x, base_y - 1), (knee_x, knee_y - 1), 3)
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["horse_light"],
                                  (base_x, base_y - 2), (knee_x, knee_y - 2), 1)
            # Shin.
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["horse_darkest"],
                                  (knee_x, knee_y), (hoof_x, hoof_y), 5)
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["horse_dark"],
                                  (knee_x, knee_y), (hoof_x, hoof_y), 3)
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["horse_mid"],
                                  (knee_x, knee_y - 1), (hoof_x, hoof_y - 1), 1)

            # Gold armor greaves on shin.
            _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_darkest"], [
                (knee_x - 3, knee_y + 4), (knee_x + 3, knee_y + 4),
                (knee_x + 4, knee_y + 10), (knee_x - 4, knee_y + 10),
            ])
            _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_dark"], [
                (knee_x - 2, knee_y + 5), (knee_x + 2, knee_y + 5),
                (knee_x + 3, knee_y + 9), (knee_x - 3, knee_y + 9),
            ])
            _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_mid"], [
                (knee_x - 1, knee_y + 6), (knee_x + 1, knee_y + 6),
                (knee_x + 2, knee_y + 8), (knee_x - 2, knee_y + 8),
            ])
            pygame.draw.rect(surface, _NS_solvanth.PALETTE["gold_shine"],
                             (knee_x, knee_y + 6, 1, 1))

            # Hoof.
            _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["hoof_dark"], [
                (hoof_x - 4, hoof_y - 2), (hoof_x + 4, hoof_y - 2),
                (hoof_x + 4, hoof_y + 3), (hoof_x - 4, hoof_y + 3),
            ])
            _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["hoof_mid"], [
                (hoof_x - 3, hoof_y - 1), (hoof_x + 3, hoof_y - 1),
                (hoof_x + 3, hoof_y + 2), (hoof_x - 3, hoof_y + 2),
            ])
            pygame.draw.line(surface, _NS_solvanth.PALETTE["hoof_light"],
                             (hoof_x - 3, hoof_y - 1), (hoof_x + 3, hoof_y - 1), 1)
            # Gold horseshoe.
            pygame.draw.line(surface, _NS_solvanth.PALETTE["gold_mid"],
                             (hoof_x - 4, hoof_y - 2), (hoof_x + 4, hoof_y - 2), 1)


    def _draw_human_torso(surface, cx, cy, facing, phase, action):
        """Human upper torso rising from horse body."""
        # Torso rises up from horse withers (front of horse body).
        torso_base_y = cy + 4
        torso_top_y = cy - 12

        breath = math.sin(phase * 0.7) * 1

        # Torso silhouette (armored, muscular).
        torso_shape = [
            (cx + facing * 4 - 10, torso_base_y),
            (cx + facing * 4 - 12, cy - 4),
            (cx + facing * 4 - 11, cy - 10),
            (cx + facing * 4 - 6, torso_top_y),
            (cx + facing * 4 + 6, torso_top_y),
            (cx + facing * 4 + 11, cy - 10),
            (cx + facing * 4 + 12, cy - 4),
            (cx + facing * 4 + 10, torso_base_y),
        ]
        # Shadow.
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in torso_shape])

        # Chest armor (silver + gold).
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["silver_dark"], torso_shape)
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["silver_mid"], [
            (cx + facing * 4 - 9, cy - 2), (cx + facing * 4 - 10, cy - 6),
            (cx + facing * 4 - 8, cy - 9), (cx + facing * 4 - 5, torso_top_y + 1),
            (cx + facing * 4 + 5, torso_top_y + 1), (cx + facing * 4 + 8, cy - 9),
            (cx + facing * 4 + 10, cy - 6), (cx + facing * 4 + 9, cy - 2),
            (cx + facing * 4 + 8, cy + 2), (cx + facing * 4 - 8, cy + 2),
        ])
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["silver_light"], [
            (cx + facing * 4 - 6, cy - 4), (cx + facing * 4 - 4, cy - 8),
            (cx + facing * 4 + 4, cy - 8), (cx + facing * 4 + 6, cy - 4),
            (cx + facing * 4 + 5, cy), (cx + facing * 4 - 5, cy),
        ])
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["silver_shine"],
                         (cx + facing * 4 - 2, cy - 6, 1, 1))
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["silver_shine"],
                         (cx + facing * 4 + 1, cy - 6, 1, 1))

        # Gold pauldron (shoulder) - large ornate.
        # Front shoulder (facing side).
        pauldron_x = cx + facing * 12
        pauldron_y = cy - 10
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_darkest"], [
            (pauldron_x - 4, pauldron_y - 2),
            (pauldron_x + 6, pauldron_y),
            (pauldron_x + 7, pauldron_y + 6),
            (pauldron_x - 3, pauldron_y + 8),
        ])
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_dark"], [
            (pauldron_x - 3, pauldron_y - 1),
            (pauldron_x + 5, pauldron_y + 1),
            (pauldron_x + 6, pauldron_y + 6),
            (pauldron_x - 2, pauldron_y + 7),
        ])
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_mid"], [
            (pauldron_x - 1, pauldron_y),
            (pauldron_x + 4, pauldron_y + 2),
            (pauldron_x + 5, pauldron_y + 5),
            (pauldron_x, pauldron_y + 6),
        ])
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_light"], [
            (pauldron_x + 1, pauldron_y + 1),
            (pauldron_x + 3, pauldron_y + 2),
            (pauldron_x + 4, pauldron_y + 4),
            (pauldron_x + 2, pauldron_y + 4),
        ])
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["gold_shine"],
                         (pauldron_x + 2, pauldron_y + 2, 1, 1))
        # Spike on top of pauldron.
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_dark"], [
            (pauldron_x + 1, pauldron_y - 2),
            (pauldron_x - 1, pauldron_y + 1),
            (pauldron_x + 3, pauldron_y + 1),
        ])
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_light"], [
            (pauldron_x + 1, pauldron_y - 2),
            (pauldron_x, pauldron_y + 1),
            (pauldron_x + 2, pauldron_y + 1),
        ])

        # Back shoulder pauldron.
        back_pauldron_x = cx - facing * 8
        back_pauldron_y = cy - 10
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_darkest"], [
            (back_pauldron_x - 3, back_pauldron_y),
            (back_pauldron_x + 4, back_pauldron_y - 1),
            (back_pauldron_x + 4, back_pauldron_y + 5),
            (back_pauldron_x - 2, back_pauldron_y + 6),
        ])
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_dark"], [
            (back_pauldron_x - 2, back_pauldron_y + 1),
            (back_pauldron_x + 3, back_pauldron_y),
            (back_pauldron_x + 3, back_pauldron_y + 4),
            (back_pauldron_x - 1, back_pauldron_y + 5),
        ])
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_mid"], [
            (back_pauldron_x - 1, back_pauldron_y + 2),
            (back_pauldron_x + 2, back_pauldron_y + 1),
            (back_pauldron_x + 2, back_pauldron_y + 4),
        ])

        # Gold trim on chest.
        pygame.draw.line(surface, _NS_solvanth.PALETTE["gold_dark"],
                         (cx + facing * 4 - 8, cy - 4),
                         (cx + facing * 4 + 8, cy - 4), 1)
        pygame.draw.line(surface, _NS_solvanth.PALETTE["gold_mid"],
                         (cx + facing * 4 - 6, cy - 3),
                         (cx + facing * 4 + 6, cy - 3), 1)

        # Central blue crystal gem on chest.
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["crystal_darkest"],
                         (cx + facing * 4 - 2, cy - 2, 4, 4))
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["crystal_dark"],
                         (cx + facing * 4 - 2, cy - 2, 3, 3))
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["crystal_mid"],
                         (cx + facing * 4 - 1, cy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["crystal_light"],
                         (cx + facing * 4 - 1, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["crystal_shine"],
                         (cx + facing * 4, cy - 1, 1, 1))


    def _draw_helmet_head(surface, cx, cy, facing, phase, action):
        """Ornate golden helmet with tall crown."""
        head_cx = cx + facing * 4
        head_cy = cy - 20

        # Face (small, mostly covered by helm).
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["shadow_deep"], [
            (head_cx - 4, head_cy + 3), (head_cx + 4, head_cy + 3),
            (head_cx + 4, head_cy + 7), (head_cx - 4, head_cy + 7),
        ])
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["skin_dark"], [
            (head_cx - 4, head_cy + 2), (head_cx + 4, head_cy + 2),
            (head_cx + 4, head_cy + 6), (head_cx - 4, head_cy + 6),
        ])
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["skin_mid"], [
            (head_cx - 3, head_cy + 3), (head_cx + 3, head_cy + 3),
            (head_cx + 3, head_cy + 5), (head_cx - 3, head_cy + 5),
        ])
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["skin_light"],
                         (head_cx - 2, head_cy + 4, 4, 1))

        # Eyes glowing blue (visible under helm).
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["eye_dark"],
                         (head_cx - 2, head_cy + 3, 5, 2))
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["crystal_light"],
                         (head_cx - 1, head_cy + 3, 1, 1))
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["crystal_shine"],
                         (head_cx - 1, head_cy + 3, 1, 1))
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["crystal_light"],
                         (head_cx + 1, head_cy + 3, 1, 1))
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["crystal_shine"],
                         (head_cx + 1, head_cy + 3, 1, 1))

        # Mouth/beard hint.
        pygame.draw.line(surface, _NS_solvanth.PALETTE["skin_darkest"],
                         (head_cx - 2, head_cy + 6), (head_cx + 2, head_cy + 6), 1)

        # HELMET (ornate gold with tall crown horns).
        # Main helm dome.
        helm_shape = [
            (head_cx - 6, head_cy + 3),
            (head_cx - 7, head_cy),
            (head_cx - 6, head_cy - 4),
            (head_cx - 3, head_cy - 8),
            (head_cx + 3, head_cy - 8),
            (head_cx + 6, head_cy - 4),
            (head_cx + 7, head_cy),
            (head_cx + 6, head_cy + 3),
        ]
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in helm_shape])
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_darkest"], helm_shape)
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_dark"], [
            (head_cx - 5, head_cy + 2), (head_cx - 6, head_cy),
            (head_cx - 5, head_cy - 3), (head_cx - 2, head_cy - 7),
            (head_cx + 2, head_cy - 7), (head_cx + 5, head_cy - 3),
            (head_cx + 6, head_cy), (head_cx + 5, head_cy + 2),
        ])
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_mid"], [
            (head_cx - 4, head_cy + 1), (head_cx - 5, head_cy - 1),
            (head_cx - 3, head_cy - 5), (head_cx, head_cy - 7),
            (head_cx + 3, head_cy - 5), (head_cx + 5, head_cy - 1),
            (head_cx + 4, head_cy + 1),
        ])
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_light"], [
            (head_cx - 2, head_cy - 2), (head_cx, head_cy - 6),
            (head_cx + 2, head_cy - 2), (head_cx, head_cy - 1),
        ])
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["gold_shine"],
                         (head_cx, head_cy - 5, 1, 1))
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["gold_bright"],
                         (head_cx - 1, head_cy - 3, 1, 1))

        # CROWN HORNS (tall spikes going up from helm).
        for i, (hx, hy_top, hy_bot, w) in enumerate([
            (head_cx - 5, head_cy - 15, head_cy - 6, 2),
            (head_cx - 2, head_cy - 18, head_cy - 8, 2),
            (head_cx + 2, head_cy - 18, head_cy - 8, 2),
            (head_cx + 5, head_cy - 15, head_cy - 6, 2),
        ]):
            sway = math.sin(phase * 0.5 + i) * 0.5
            hx += int(sway)
            _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["shadow_deep"], [
                (hx + 1, hy_top + 1), (hx - w + 1, hy_bot + 1),
                (hx + w + 1, hy_bot + 1),
            ])
            _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_darkest"], [
                (hx, hy_top), (hx - w, hy_bot), (hx + w, hy_bot),
            ])
            _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_dark"], [
                (hx, hy_top), (hx - w + 1, hy_bot), (hx + w - 1, hy_bot),
            ])
            _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_mid"], [
                (hx, hy_top), (hx, hy_bot), (hx + w - 1, hy_bot),
            ])
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["gold_light"],
                                  (hx, hy_top), (hx, hy_bot), 1)
            pygame.draw.rect(surface, _NS_solvanth.PALETTE["gold_shine"],
                             (hx, hy_top, 1, 1))
            pygame.draw.rect(surface, _NS_solvanth.PALETTE["gold_bright"],
                             (hx, hy_top, 1, 1))

        # Central big crown spike (tallest).
        big_spike_x = head_cx
        big_spike_top = head_cy - 22
        big_spike_bot = head_cy - 10
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["shadow_deep"], [
            (big_spike_x + 1, big_spike_top + 1),
            (big_spike_x - 3, big_spike_bot + 1),
            (big_spike_x + 3, big_spike_bot + 1),
        ])
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_darkest"], [
            (big_spike_x, big_spike_top),
            (big_spike_x - 3, big_spike_bot),
            (big_spike_x + 3, big_spike_bot),
        ])
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_dark"], [
            (big_spike_x, big_spike_top),
            (big_spike_x - 2, big_spike_bot),
            (big_spike_x + 2, big_spike_bot),
        ])
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["gold_mid"], [
            (big_spike_x, big_spike_top),
            (big_spike_x, big_spike_bot),
            (big_spike_x + 2, big_spike_bot),
        ])
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["gold_light"],
                              (big_spike_x, big_spike_top),
                              (big_spike_x, big_spike_bot), 1)
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["gold_bright"],
                         (big_spike_x, big_spike_top, 1, 1))

        # Small blue gem on forehead of helm.
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["crystal_dark"],
                         (head_cx - 1, head_cy - 3, 2, 2))
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["crystal_mid"],
                         (head_cx, head_cy - 3, 1, 1))
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["crystal_shine"],
                         (head_cx, head_cy - 3, 1, 1))


    def _draw_back_arm(surface, cx, cy, facing, phase, action, progress):
        """Back arm (extended/gesturing)."""
        shoulder_x = cx - facing * 6
        shoulder_y = cy - 8

        # Gesture varies by action.
        if action == "cast":
            elbow_x = shoulder_x - facing * 6
            elbow_y = shoulder_y - 4
            hand_x = shoulder_x - facing * 12
            hand_y = shoulder_y - 8
        else:
            sway = math.sin(phase * 0.5) * 1
            elbow_x = shoulder_x - facing * 5
            elbow_y = shoulder_y + 4 + int(sway)
            hand_x = shoulder_x - facing * 8
            hand_y = shoulder_y + 10

        # Shadow.
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["shadow_deep"],
                              (shoulder_x + 2, shoulder_y + 2),
                              (elbow_x + 2, elbow_y + 2), 5)
        # Upper arm (armored).
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["silver_dark"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["silver_mid"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["silver_light"],
                              (shoulder_x, shoulder_y - 1),
                              (elbow_x, elbow_y - 1), 1)
        # Elbow gold cap.
        _NS_solvanth._aacircle(surface, _NS_solvanth.PALETTE["gold_dark"],
                                (elbow_x, elbow_y), 3)
        _NS_solvanth._aacircle(surface, _NS_solvanth.PALETTE["gold_mid"],
                                (elbow_x, elbow_y), 2)
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["gold_shine"],
                         (elbow_x, elbow_y - 1, 1, 1))
        # Forearm (skin).
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["skin_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["skin_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 2)
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["skin_mid"],
                              (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
        # Hand.
        _NS_solvanth._aacircle(surface, _NS_solvanth.PALETTE["skin_darkest"],
                                (hand_x, hand_y), 3)
        _NS_solvanth._aacircle(surface, _NS_solvanth.PALETTE["skin_dark"],
                                (hand_x, hand_y), 2)
        _NS_solvanth._aacircle(surface, _NS_solvanth.PALETTE["skin_mid"],
                                (hand_x, hand_y - 1), 1)

        # Gold bracer.
        _NS_solvanth._aacircle(surface, _NS_solvanth.PALETTE["gold_dark"],
                                (hand_x + facing, hand_y - 2), 2)
        _NS_solvanth._aacircle(surface, _NS_solvanth.PALETTE["gold_mid"],
                                (hand_x + facing, hand_y - 2), 1)


    def _draw_staff_arm(surface, cx, cy, facing, phase, action, progress):
        """Front arm holding the staff."""
        shoulder_x = cx + facing * 10
        shoulder_y = cy - 8

        if action == "attack":
            # Swing motion.
            angle = -math.pi / 3 + progress * math.pi * 0.9
            elbow_x = shoulder_x + facing * int(math.cos(angle) * 6)
            elbow_y = shoulder_y + int(math.sin(angle) * 6)
            hand_x = shoulder_x + facing * int(math.cos(angle) * 12)
            hand_y = shoulder_y + int(math.sin(angle) * 12)
            staff_tip_angle = angle - math.pi / 4
        elif action == "cast":
            # Raise staff high.
            elbow_x = shoulder_x + facing * 4
            elbow_y = shoulder_y - 6
            hand_x = shoulder_x + facing * 8
            hand_y = shoulder_y - 16
            staff_tip_angle = -math.pi / 2 + 0.2
        elif action == "smash":
            # Down slam.
            if progress < 0.4:
                # Raise up.
                t = progress / 0.4
                elbow_x = shoulder_x + facing * 4
                elbow_y = shoulder_y - int(t * 8)
                hand_x = shoulder_x + facing * 8
                hand_y = shoulder_y - int(t * 18)
                staff_tip_angle = -math.pi / 2
            else:
                # Slam down.
                t = (progress - 0.4) / 0.6
                elbow_x = shoulder_x + facing * (4 + int(t * 4))
                elbow_y = shoulder_y - 8 + int(t * 16)
                hand_x = shoulder_x + facing * (8 + int(t * 6))
                hand_y = shoulder_y - 18 + int(t * 30)
                staff_tip_angle = -math.pi / 2 + t * math.pi
        elif action == "leap":
            # Overhead thunder pose.
            elbow_x = shoulder_x + facing * 2
            elbow_y = shoulder_y - 8
            hand_x = shoulder_x + facing * 4
            hand_y = shoulder_y - 20
            staff_tip_angle = -math.pi / 2
        else:
            # Idle: staff held vertical.
            sway = math.sin(phase * 0.6) * 1
            elbow_x = shoulder_x + facing * 4
            elbow_y = shoulder_y + 4 + int(sway)
            hand_x = shoulder_x + facing * 8
            hand_y = shoulder_y + 2 + int(sway)
            staff_tip_angle = -math.pi / 2 + 0.15

        # Shadow.
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["shadow_deep"],
                              (shoulder_x + 2, shoulder_y + 2),
                              (elbow_x + 2, elbow_y + 2), 6)
        # Upper arm (armored).
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["silver_dark"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["silver_mid"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["silver_light"],
                              (shoulder_x, shoulder_y - 1),
                              (elbow_x, elbow_y - 1), 2)
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["silver_shine"],
                              (shoulder_x, shoulder_y - 2),
                              (elbow_x, elbow_y - 2), 1)
        # Elbow gold cap.
        _NS_solvanth._aacircle(surface, _NS_solvanth.PALETTE["gold_dark"],
                                (elbow_x, elbow_y), 3)
        _NS_solvanth._aacircle(surface, _NS_solvanth.PALETTE["gold_mid"],
                                (elbow_x, elbow_y), 2)
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["gold_shine"],
                         (elbow_x, elbow_y - 1, 1, 1))
        # Forearm (skin).
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["skin_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["skin_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["skin_mid"],
                              (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
        # Gold bracer.
        _NS_solvanth._aacircle(surface, _NS_solvanth.PALETTE["gold_dark"],
                                (hand_x, hand_y), 4)
        _NS_solvanth._aacircle(surface, _NS_solvanth.PALETTE["gold_mid"],
                                (hand_x, hand_y), 3)
        _NS_solvanth._aacircle(surface, _NS_solvanth.PALETTE["gold_light"],
                                (hand_x, hand_y - 1), 1)
        # Hand.
        _NS_solvanth._aacircle(surface, _NS_solvanth.PALETTE["skin_dark"],
                                (hand_x, hand_y), 2)

        # Draw staff.
        _NS_solvanth._draw_staff(surface, hand_x, hand_y, staff_tip_angle,
                                  facing, phase)


    def _draw_staff(surface, hx, hy, angle, facing, phase):
        """Long staff with blue crystal on top."""
        length = 42
        # Top end (crystal).
        top_x = hx + int(math.cos(angle) * length)
        top_y = hy + int(math.sin(angle) * length)
        # Bottom end.
        bot_x = hx - int(math.cos(angle) * 12)
        bot_y = hy - int(math.sin(angle) * 12)

        # Shadow.
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["shadow_deep"],
                              (bot_x + 2, bot_y + 2), (top_x + 2, top_y + 2), 4)
        # Staff shaft (gold).
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["gold_darkest"],
                              (bot_x, bot_y), (top_x, top_y), 4)
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["gold_dark"],
                              (bot_x, bot_y), (top_x, top_y), 3)
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["gold_mid"],
                              (bot_x, bot_y), (top_x, top_y), 1)
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["gold_light"],
                              (bot_x, bot_y - 1), (top_x, top_y - 1), 1)

        # Decorative rings along staff.
        for t_ring in (0.25, 0.5, 0.75):
            rx = int(bot_x + (top_x - bot_x) * t_ring)
            ry = int(bot_y + (top_y - bot_y) * t_ring)
            perp = angle + math.pi / 2
            r_a = (rx + int(math.cos(perp) * 3), ry + int(math.sin(perp) * 3))
            r_b = (rx - int(math.cos(perp) * 3), ry - int(math.sin(perp) * 3))
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["gold_darkest"],
                                  r_a, r_b, 2)
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["gold_light"],
                                  r_a, r_b, 1)

        # Blue crystal on top (elongated diamond).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        perp = angle + math.pi / 2
        crystal_top_x = top_x + int(math.cos(angle) * 8)
        crystal_top_y = top_y + int(math.sin(angle) * 8)
        crystal_a = (top_x + int(math.cos(perp) * 4),
                     top_y + int(math.sin(perp) * 4))
        crystal_b = (top_x - int(math.cos(perp) * 4),
                     top_y - int(math.sin(perp) * 4))
        crystal_bot = (top_x - int(math.cos(angle) * 2),
                       top_y - int(math.sin(angle) * 2))

        # Shadow.
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["shadow_deep"], [
            (crystal_top_x + 2, crystal_top_y + 2),
            (crystal_a[0] + 2, crystal_a[1] + 2),
            (crystal_bot[0] + 2, crystal_bot[1] + 2),
            (crystal_b[0] + 2, crystal_b[1] + 2),
        ])
        # Crystal body.
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["crystal_darkest"], [
            (crystal_top_x, crystal_top_y), crystal_a, crystal_bot, crystal_b,
        ])
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["crystal_dark"], [
            (crystal_top_x, crystal_top_y),
            (int((crystal_top_x + crystal_a[0]) / 2),
             int((crystal_top_y + crystal_a[1]) / 2)),
            crystal_bot,
            (int((crystal_top_x + crystal_b[0]) / 2),
             int((crystal_top_y + crystal_b[1]) / 2)),
        ])
        _NS_solvanth._poly(surface, _NS_solvanth.PALETTE["crystal_mid"], [
            (crystal_top_x, crystal_top_y),
            (top_x, top_y),
            crystal_bot,
        ])
        # Highlight.
        _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["crystal_light"],
                              (crystal_top_x, crystal_top_y),
                              crystal_bot, 1)
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["crystal_shine"],
                         (crystal_top_x, crystal_top_y, 1, 1))
        pygame.draw.rect(surface, _NS_solvanth.PALETTE["white"],
                         (crystal_top_x, crystal_top_y, 1, 1))

        # Crystal glow aura.
        for r in range(8, 1, -1):
            alpha = _NS_solvanth._alpha(80 * (8 - r) / 8 * pulse)
            _NS_solvanth._aacircle(surface,
                                    (*_NS_solvanth.PALETTE["crystal_light"],
                                     alpha), (crystal_top_x, crystal_top_y), r)

        # Gold prongs holding crystal.
        for prong_side in [-1, 1]:
            prong_x = top_x + int(math.cos(perp) * 3 * prong_side)
            prong_y = top_y + int(math.sin(perp) * 3 * prong_side)
            prong_tip_x = prong_x + int(math.cos(angle) * 4)
            prong_tip_y = prong_y + int(math.sin(angle) * 4)
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["gold_dark"],
                                  (prong_x, prong_y), (prong_tip_x, prong_tip_y), 2)
            _NS_solvanth._aaline(surface, _NS_solvanth.PALETTE["gold_light"],
                                  (prong_x, prong_y), (prong_tip_x, prong_tip_y), 1)


    def _draw_melee_swing(surface, cx, cy, facing, progress):
        """Golden arc from staff swing."""
        if progress < 0.3 or progress > 0.9:
            return
        t = (progress - 0.3) / 0.6

        for i in range(10):
            trail_t = t - i * 0.04
            if trail_t < 0:
                continue
            a = -math.pi / 3 + trail_t * math.pi * 0.9
            radius = 35
            arc_x = cx + int(math.cos(a) * radius) * facing
            arc_y = cy + int(math.sin(a) * radius)
            alpha = _NS_solvanth._alpha(230 - i * 22)

            _NS_solvanth._aacircle(surface,
                                    (*_NS_solvanth.PALETTE["holy_dark"], alpha),
                                    (arc_x, arc_y), 5)
            _NS_solvanth._aacircle(surface,
                                    (*_NS_solvanth.PALETTE["holy_mid"], alpha),
                                    (arc_x, arc_y), 4)
            _NS_solvanth._aacircle(surface,
                                    (*_NS_solvanth.PALETTE["holy_light"], alpha),
                                    (arc_x, arc_y), 2)
            pygame.draw.rect(surface,
                             (*_NS_solvanth.PALETTE["holy_shine"], alpha),
                             (arc_x, arc_y, 1, 1))

    # ============================================================
    # FLOAT PARTICLES
    # ============================================================
    def _draw_float_particles(surface, cx, cy, phase, intense=False):
        """Golden radiant particles under boss (holy floating)."""
        strength = 1.5 if intense else 1.0

        # Base golden pool.
        pool = pygame.Surface((100, 24), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for r in range(20, 2, -2):
            alpha = _NS_solvanth._alpha((20 - r) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(pool,
                                    (*_NS_solvanth.PALETTE["holy_dark"], alpha),
                                    (50 - r, 12 - r // 4,
                                     r * 2, max(2, r // 2)))
        for r in range(12, 1, -1):
            alpha = _NS_solvanth._alpha((12 - r) * 6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(pool,
                                    (*_NS_solvanth.PALETTE["holy_mid"], alpha),
                                    (50 - r, 12 - r // 4,
                                     r * 2, max(2, r // 3)))
        surface.blit(pool, (cx - 50, cy - 5))

        # Rising golden sparkles.
        for i in range(10):
            t = (phase * 0.5 + i * 0.11) % 1.0
            sx = cx - 25 + i * 5 + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 26)
            alpha = _NS_solvanth._alpha(230 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_solvanth._aacircle(surface,
                                    (*_NS_solvanth.PALETTE["holy_dark"], alpha),
                                    (sx, sy), 2)
            pygame.draw.rect(surface,
                             (*_NS_solvanth.PALETTE["holy_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_solvanth.PALETTE["holy_hot"], alpha),
                             (sx, sy - 2, 1, 1))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for r in range(14, 0, -1):
            alpha = max(0, (14 - r) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - r, 15 - r,
                                 120 + r * 2, r * 2))
        pygame.draw.ellipse(shadow, (5, 10, 5, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (60, 40, 5, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))

    def _draw_holy_aura(surface, x, y, phase):
        """Golden holy aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for r in range(100, 5, -5):
            alpha = _NS_solvanth._alpha((100 - r) * 1.2 * pulse)
            if alpha > 0:
                _NS_solvanth._aacircle(aura,
                                        (*_NS_solvanth.PALETTE["holy_darkest"], alpha),
                                        (110, 100), r)
        for r in range(60, 5, -4):
            alpha = _NS_solvanth._alpha((60 - r) * 1.4 * pulse)
            if alpha > 0:
                _NS_solvanth._aacircle(aura,
                                        (*_NS_solvanth.PALETTE["holy_dark"], alpha),
                                        (110, 100), r)
        surface.blit(aura, (x - 110, y - 100))

        # Sparkles.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_solvanth.PALETTE["holy_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_solvanth.PALETTE["holy_hot"],
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ornate golden rune circle."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring,
                            (*_NS_solvanth.PALETTE["rune_dark"], 200),
                            (5, 18, 170, 26), 3)
        pygame.draw.ellipse(ring,
                            (*_NS_solvanth.PALETTE["holy_darkest"], 220),
                            (14, 20, 152, 22), 2)
        pygame.draw.ellipse(ring,
                            (*_NS_solvanth.PALETTE["holy_dark"], 230),
                            (25, 22, 130, 18), 1)

        # Rune marks.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 90 + int(math.cos(angle) * 78)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring,
                             (*_NS_solvanth.PALETTE["holy_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_solvanth.PALETTE["holy_hot"],
                                 _NS_solvanth._alpha(150 * pulse)),
                                (15, 12, 150, 38), 1)
        surface.blit(ring, (x - 90, y - 27))

    # ============================================================
    # SKILL Q: RING OF PUNISHMENT - expanding golden ring
    # ============================================================
    def _draw_ring_punishment_ground(surface, boss, x, y, timer, phase):
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(20 + progress * 60)

        # Expanding ring.
        for i in range(3):
            actual_r = r - i * 4
            if actual_r < 5:
                continue
            alpha = _NS_solvanth._alpha(230 * (1 - progress * 0.6))
            pygame.draw.ellipse(surface,
                                (*_NS_solvanth.PALETTE["holy_dark"], alpha),
                                (x - actual_r, y + 55 - actual_r // 3,
                                 actual_r * 2, actual_r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_solvanth.PALETTE["holy_mid"], alpha),
                                (x - actual_r + 2, y + 55 - actual_r // 3 + 1,
                                 actual_r * 2 - 4, actual_r * 2 // 3 - 2), 2)
            pygame.draw.ellipse(surface,
                                (*_NS_solvanth.PALETTE["holy_light"], alpha),
                                (x - actual_r + 4, y + 55 - actual_r // 3 + 2,
                                 actual_r * 2 - 8, actual_r * 2 // 3 - 4), 1)

    def _draw_ring_punishment_fg(surface, boss, x, y, timer, phase):
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(20 + progress * 60)

        # Sparkles around ring edge.
        num_sparkles = 20
        for i in range(num_sparkles):
            angle = i * math.pi * 2 / num_sparkles + phase * 0.5
            sx = x + int(math.cos(angle) * r)
            sy = y + 55 + int(math.sin(angle) * r * 0.35)
            alpha = _NS_solvanth._alpha(230 * (1 - progress * 0.5))
            _NS_solvanth._aacircle(surface,
                                    (*_NS_solvanth.PALETTE["holy_mid"], alpha),
                                    (sx, sy), 2)
            pygame.draw.rect(surface,
                             (*_NS_solvanth.PALETTE["holy_hot"], alpha),
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_solvanth.PALETTE["holy_shine"], alpha),
                             (sx, sy, 1, 1))

    # ============================================================
    # SKILL W: GLORIOUS PATHWAY - rectangle path of light
    # ============================================================
    def _draw_glorious_pathway_ground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Rectangular pathway of light in front.
        path_length = 140
        path_width = 40
        # Grow from start to full length.
        actual_length = int(path_length * min(1.0, progress * 2))

        start_x = x + facing * 20
        end_x = start_x + facing * actual_length

        # Path base (translucent).
        path_surf = pygame.Surface(
            (abs(end_x - start_x) + 20, path_width + 10),
            pygame.SRCALPHA
        )
        px_left = min(start_x, end_x) - 10

        pulse = math.sin(phase * 2) * 0.2 + 0.8

        # Rectangle segments layered.
        rect_x = 10
        rect_y = 5
        rect_w = abs(end_x - start_x)
        rect_h = path_width

        pygame.draw.rect(path_surf,
                         (*_NS_solvanth.PALETTE["holy_darkest"],
                          int(180 * pulse)),
                         (rect_x, rect_y, rect_w, rect_h))
        pygame.draw.rect(path_surf,
                         (*_NS_solvanth.PALETTE["holy_dark"],
                          int(200 * pulse)),
                         (rect_x + 3, rect_y + 3,
                          rect_w - 6, rect_h - 6))
        pygame.draw.rect(path_surf,
                         (*_NS_solvanth.PALETTE["holy_mid"],
                          int(180 * pulse)),
                         (rect_x + 6, rect_y + 6,
                          rect_w - 12, rect_h - 12))
        pygame.draw.rect(path_surf,
                         (*_NS_solvanth.PALETTE["holy_light"],
                          int(140 * pulse)),
                         (rect_x + 10, rect_y + 10,
                          rect_w - 20, rect_h - 20))

        # Bright edges.
        pygame.draw.rect(path_surf,
                         (*_NS_solvanth.PALETTE["holy_hot"], 220),
                         (rect_x, rect_y, rect_w, rect_h), 2)

        # Runes along path.
        num_runes = 4
        for i in range(num_runes):
            rune_x = rect_x + int((i + 0.5) * rect_w / num_runes)
            rune_y = rect_y + rect_h // 2
            pygame.draw.rect(path_surf,
                             (*_NS_solvanth.PALETTE["holy_shine"], 240),
                             (rune_x - 2, rune_y - 2, 4, 4))
            pygame.draw.rect(path_surf,
                             (*_NS_solvanth.PALETTE["white"], 240),
                             (rune_x - 1, rune_y - 1, 2, 2))

        surface.blit(path_surf, (px_left, y + 40 - path_width // 2))

        # Sparkles above pathway.
        for i in range(15):
            spark_t = (phase * 0.6 + i * 0.1) % 1.0
            spark_x = start_x + facing * int((i / 15) * actual_length)
            spark_y = y + 40 - int(spark_t * 15)
            alpha = _NS_solvanth._alpha(220 * (1 - spark_t))
            pygame.draw.rect(surface,
                             (*_NS_solvanth.PALETTE["holy_hot"], alpha),
                             (spark_x, spark_y, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_solvanth.PALETTE["holy_shine"], alpha),
                             (spark_x, spark_y, 1, 1))

    # ============================================================
    # SKILL E: LAW AND ORDER - ground smash rectangle
    # ============================================================
    def _draw_law_order_ground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Rectangle burst in front.
        if progress < 0.5:
            return  # wait for smash animation to play

        t = (progress - 0.5) / 0.5
        rect_length = int(100 * t)
        rect_width = 50

        if rect_length < 5:
            return

        start_x = x + facing * 20
        rect_left = min(start_x, start_x + facing * rect_length)
        rect_right = max(start_x, start_x + facing * rect_length)

        # Ground blast (gold rectangle).
        alpha = _NS_solvanth._alpha(230 * (1 - t * 0.6))
        blast_surf = pygame.Surface(
            (rect_right - rect_left + 10, rect_width + 10),
            pygame.SRCALPHA
        )
        pygame.draw.rect(blast_surf,
                         (*_NS_solvanth.PALETTE["holy_darkest"], alpha),
                         (0, 0, rect_right - rect_left, rect_width))
        pygame.draw.rect(blast_surf,
                         (*_NS_solvanth.PALETTE["holy_dark"], alpha),
                         (3, 3, rect_right - rect_left - 6, rect_width - 6))
        pygame.draw.rect(blast_surf,
                         (*_NS_solvanth.PALETTE["holy_mid"], alpha),
                         (6, 6, rect_right - rect_left - 12, rect_width - 12))
        pygame.draw.rect(blast_surf,
                         (*_NS_solvanth.PALETTE["holy_hot"], alpha),
                         (0, 0, rect_right - rect_left, rect_width), 2)
        surface.blit(blast_surf, (rect_left, y + 40 - rect_width // 2))

    def _draw_law_order_fg(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.5:
            # Charging - gathering energy in staff.
            hx = x + facing * 12
            hy = y - 26
            cr = int(3 + progress / 0.5 * 6)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_solvanth._alpha(200 * (cr + 3 - r) / (cr + 3))
                _NS_solvanth._aacircle(surface,
                                        (*_NS_solvanth.PALETTE["holy_mid"], alpha),
                                        (hx, hy), r)
            _NS_solvanth._aacircle(surface, _NS_solvanth.PALETTE["holy_light"],
                                    (hx, hy), max(1, cr - 2))
            pygame.draw.rect(surface, _NS_solvanth.PALETTE["holy_shine"],
                             (hx, hy, 1, 1))
        else:
            # Vertical light columns erupting from ground rectangle.
            t = (progress - 0.5) / 0.5
            num_columns = 6
            start_x = x + facing * 20
            length = 100

            for i in range(num_columns):
                col_x = start_x + facing * int((i + 0.5) / num_columns * length)
                col_h = int((math.sin(t * math.pi + i * 0.3) * 40))
                if col_h < 5:
                    continue
                col_y_base = y + 40
                col_y_top = col_y_base - col_h

                alpha = _NS_solvanth._alpha(240 * (1 - t * 0.5))
                # Column layers.
                for cw, cc in [
                    (8, _NS_solvanth.PALETTE["holy_darkest"]),
                    (6, _NS_solvanth.PALETTE["holy_dark"]),
                    (4, _NS_solvanth.PALETTE["holy_mid"]),
                    (2, _NS_solvanth.PALETTE["holy_light"]),
                    (1, _NS_solvanth.PALETTE["holy_shine"]),
                ]:
                    pygame.draw.rect(surface, (*cc, alpha),
                                     (col_x - cw // 2, col_y_top,
                                      cw, col_h))

                # Sparkles at top.
                pygame.draw.rect(surface,
                                 (*_NS_solvanth.PALETTE["white"], alpha),
                                 (col_x, col_y_top, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_solvanth.PALETTE["holy_hot"], alpha),
                                 (col_x - 1, col_y_top - 1, 3, 2))

    # ============================================================
    # SKILL R: WRATH OF GOD - sky beam
    # ============================================================
    def _draw_wrath_ground(surface, boss, x, y, timer, pulse):
        tx, ty = _NS_solvanth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.4:
            # Warning circle at target.
            t = progress / 0.4
            r = int(35 * t)
            alpha = _NS_solvanth._alpha(200 * t)
            pygame.draw.ellipse(surface,
                                (*_NS_solvanth.PALETTE["holy_dark"], alpha),
                                (tx - r, ty - r // 3,
                                 r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_solvanth.PALETTE["holy_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
        elif progress < 0.7:
            # During strike - big pool.
            r = 45
            alpha = _NS_solvanth._alpha(240)
            pygame.draw.ellipse(surface,
                                (*_NS_solvanth.PALETTE["holy_darkest"], alpha),
                                (tx - r, ty - r // 3,
                                 r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_solvanth.PALETTE["holy_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
        else:
            # Aftermath fading circle.
            t = (progress - 0.7) / 0.3
            r = int(45 + t * 20)
            alpha = _NS_solvanth._alpha(200 * (1 - t))
            pygame.draw.ellipse(surface,
                                (*_NS_solvanth.PALETTE["holy_dark"], alpha),
                                (tx - r, ty - r // 3,
                                 r * 2, r * 2 // 3), 2)

    def _draw_wrath_fg(surface, boss, x, y, timer, phase):
        tx, ty = _NS_solvanth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.4:
            # Gathering energy in sky.
            t = progress / 0.4
            gather_y = ty - int((1 - t) * 100)
            gather_r = int(5 + t * 6)
            for r in range(gather_r + 4, 0, -1):
                alpha = _NS_solvanth._alpha(200 * (gather_r + 4 - r) / (gather_r + 4))
                _NS_solvanth._aacircle(surface,
                                        (*_NS_solvanth.PALETTE["holy_dark"], alpha),
                                        (tx, gather_y), r)
            _NS_solvanth._aacircle(surface, _NS_solvanth.PALETTE["holy_light"],
                                    (tx, gather_y), max(1, gather_r - 2))
            pygame.draw.rect(surface, _NS_solvanth.PALETTE["holy_shine"],
                             (tx, gather_y, 1, 1))
        elif progress < 0.7:
            # MASSIVE BEAM from sky.
            t = (progress - 0.4) / 0.3
            intensity = math.sin(t * math.pi)
            beam_top_y = max(0, ty - 250)

            # Multi-layer beam.
            for layer_i, (width, color) in enumerate([
                (30, _NS_solvanth.PALETTE["holy_darkest"]),
                (24, _NS_solvanth.PALETTE["holy_dark"]),
                (18, _NS_solvanth.PALETTE["holy_mid"]),
                (12, _NS_solvanth.PALETTE["holy_light"]),
                (6, _NS_solvanth.PALETTE["holy_hot"]),
                (2, _NS_solvanth.PALETTE["holy_shine"]),
            ]):
                alpha = _NS_solvanth._alpha(240 * intensity)
                pygame.draw.rect(surface, (*color, alpha),
                                 (tx - width // 2, beam_top_y,
                                  width, ty - beam_top_y))

            # Sparkles falling within beam.
            for i in range(20):
                spark_t = (phase * 3 + i * 0.1) % 1.0
                spark_y = beam_top_y + int(spark_t * (ty - beam_top_y))
                spark_x = tx + int(math.sin(phase * 5 + i) * 8)
                alpha = _NS_solvanth._alpha(240 * intensity)
                pygame.draw.rect(surface,
                                 (*_NS_solvanth.PALETTE["holy_shine"], alpha),
                                 (spark_x, spark_y, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_solvanth.PALETTE["white"], alpha),
                                 (spark_x, spark_y, 1, 1))

            # Impact burst.
            impact_r = int(20 + t * 20)
            impact_alpha = _NS_solvanth._alpha(255 * intensity)
            _NS_solvanth._aacircle(surface,
                                    (*_NS_solvanth.PALETTE["holy_shine"],
                                     impact_alpha), (tx, ty), impact_r // 3)
            _NS_solvanth._aacircle(surface,
                                    (*_NS_solvanth.PALETTE["holy_hot"],
                                     impact_alpha), (tx, ty), impact_r // 2)

            # Debris/rock chunks scattered.
            for i in range(8):
                angle = i * math.pi / 4
                dist = impact_r + int(t * 15)
                dx = tx + int(math.cos(angle) * dist)
                dy = ty + int(math.sin(angle) * dist * 0.5)
                pygame.draw.rect(surface,
                                 _NS_solvanth.PALETTE["hoof_dark"],
                                 (dx, dy, 3, 3))
                pygame.draw.rect(surface,
                                 _NS_solvanth.PALETTE["hoof_mid"],
                                 (dx, dy, 2, 2))
                pygame.draw.rect(surface,
                                 _NS_solvanth.PALETTE["gold_mid"],
                                 (dx, dy, 1, 1))
        else:
            # Aftermath: rising light particles.
            t = (progress - 0.7) / 0.3
            for i in range(12):
                rise_t = (phase * 0.8 + i * 0.08) % 1.0
                rx = tx + int(math.sin(phase + i) * 25)
                ry = ty - int(rise_t * 40)
                alpha = _NS_solvanth._alpha(230 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_solvanth._aacircle(surface,
                                            (*_NS_solvanth.PALETTE["holy_mid"],
                                             alpha), (rx, ry), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_solvanth.PALETTE["holy_hot"],
                                      alpha), (rx, ry - 1, 1, 1))


def bob_offset(pulse):
    return int(math.sin(pulse * 0.7) * 3)


# ====================================================================
# xyrael.py
# ====================================================================

"""
XY'RAEL - The Cyan Wraith
Mini boss assassin dengan katana crystalline biru.
Gaya rendering mengikuti _NS_vhorethzir.
"""



class _NS_xyrael:
    """Namespace xyrael - cyan wraith assassin mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin (pale assassin)
        "skin_darkest": (95, 75, 70),
        "skin_dark": (155, 130, 120),
        "skin_mid": (210, 185, 170),
        "skin_light": (240, 220, 205),
        "skin_shine": (255, 245, 235),

        # Silver/white hair
        "hair_darkest": (55, 60, 80),
        "hair_dark": (110, 120, 145),
        "hair_mid": (170, 180, 200),
        "hair_light": (215, 220, 235),
        "hair_shine": (245, 248, 255),

        # Dark ninja outfit (blue-black)
        "cloth_darkest": (8, 12, 25),
        "cloth_dark": (20, 30, 55),
        "cloth_mid": (40, 55, 90),
        "cloth_light": (75, 95, 140),
        "cloth_shine": (130, 160, 210),

        # Belt/sash (blue)
        "sash_dark": (20, 40, 90),
        "sash_mid": (50, 90, 170),
        "sash_light": (110, 160, 230),

        # Gold accents (buckle, trim)
        "gold_dark": (85, 65, 15),
        "gold_mid": (170, 135, 40),
        "gold_light": (240, 210, 100),
        "gold_shine": (255, 245, 180),

        # Blade steel
        "blade_darkest": (25, 35, 55),
        "blade_dark": (65, 85, 115),
        "blade_mid": (135, 155, 190),
        "blade_light": (210, 225, 245),
        "blade_shine": (250, 253, 255),

        # Cyan energy (main theme)
        "cyan_darkest": (5, 20, 55),
        "cyan_dark": (15, 60, 140),
        "cyan_mid": (40, 130, 220),
        "cyan_light": (110, 200, 255),
        "cyan_hot": (180, 235, 255),
        "cyan_shine": (230, 250, 255),

        # Eye (cyan piercing)
        "eye_dark": (10, 15, 30),
        "eye_white": (230, 235, 245),
        "eye_cyan": (100, 200, 255),

        # Ground/rune
        "rune_dark": (10, 25, 60),
        "rune_mid": (40, 100, 200),
        "rune_light": (140, 220, 255),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    # ============================================================
    # HELPERS
    # ============================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_xyrael._clamp(color)
        if _NS_xyrael.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_xyrael._clamp(color)
        if _NS_xyrael.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        # Defensive validation.
        valid_points = []
        for p in points:
            try:
                if hasattr(p, '__len__') and len(p) >= 2:
                    valid_points.append((int(p[0]), int(p[1])))
            except (TypeError, ValueError):
                continue
        if len(valid_points) < 3:
            if len(valid_points) == 2:
                pygame.draw.line(surface, _NS_xyrael._clamp(color),
                                 valid_points[0], valid_points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_xyrael._clamp(color), valid_points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar
            # (x, y) dengan kompensasi scale (hero di-render di
            # canvas lalu di-scale; boss langsung di layar).
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return int(x + 220 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_xyrael(surface, boss, x, y):
        """Entry point utama."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_xyrael._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_xya_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_xyrael._draw_cyan_aura(surface, x, y, pulse)
        _NS_xyrael._draw_ground_ring(surface, x, y + 46, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "e":
            _NS_xyrael._draw_tempest_ground(surface, boss, x, y,
                                             skill_timer, pulse)
        elif active_skill == "r":
            _NS_xyrael._draw_lightness_ground(surface, boss, x, y,
                                               skill_timer, pulse)
        elif active_skill == "q":
            _NS_xyrael._draw_finch_ground(surface, boss, x, y,
                                           skill_timer, pulse)

        # Body pose.
        if active_skill == "r":
            _NS_xyrael._draw_body_lightness(surface, boss, x, y,
                                              skill_timer, pulse)
        elif active_skill == "e":
            _NS_xyrael._draw_body_tempest(surface, boss, x, y,
                                            skill_timer, pulse)
        elif active_skill == "q":
            _NS_xyrael._draw_body_dash(surface, boss, x, y,
                                        skill_timer, pulse)
        elif active_skill == "w":
            _NS_xyrael._draw_body_spin(surface, boss, x, y,
                                        skill_timer, pulse)
        elif attacking:
            _NS_xyrael._draw_body_attack(surface, boss, x, y)
        else:
            _NS_xyrael._draw_body_idle(surface, boss, x, y)

        # Foreground skill FX.
        if active_skill == "q":
            _NS_xyrael._draw_finch_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_xyrael._draw_defiant_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_xyrael._draw_tempest_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_xyrael._draw_lightness_fg(surface, boss, x, y,
                                            skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_xya_previous_timer", 0))
        active = bool(getattr(boss, "_xya_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._xya_attack_active = True
            boss._xya_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._xya_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._xya_attack_frame = int(getattr(boss, "_xya_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._xya_attack_active = False
            boss._xya_attack_frame = 0
            active = False

        boss._xya_previous_timer = timer
        boss._xya_attack_progress = (
            min(1.0, getattr(boss, "_xya_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 5)
        _NS_xyrael._draw_shadow(surface, x, y + 50)
        _NS_xyrael._draw_float_particles(surface, x, y + 40, boss.pulse)
        _NS_xyrael._draw_assassin_body(surface, x, y + bob, boss.direction,
                                        boss.pulse, "idle")

    def _draw_body_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_xya_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_xya_attack_dir", None)
        if facing is None:
            facing = boss.direction
        bob = int(math.sin(boss.pulse * 0.7) * 3)
        # Quick lunge forward.
        if progress < 0.4:
            lunge = int(progress / 0.4 * 10) * facing
        else:
            lunge = int((1 - (progress - 0.4) / 0.6) * 10) * facing

        _NS_xyrael._draw_shadow(surface, x + lunge, y + 50)
        _NS_xyrael._draw_float_particles(surface, x + lunge, y + 40, boss.pulse)
        _NS_xyrael._draw_assassin_body(surface, x + lunge, y + bob,
                                        facing, boss.pulse,
                                        "attack", progress)
        _NS_xyrael._draw_melee_swing(surface, x + lunge, y + bob,
                                      facing, progress)

    def _draw_body_dash(surface, boss, x, y, timer, pulse):
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        bob = int(math.sin(pulse * 0.7) * 2)
        # Fast dash forward.
        if progress < 0.5:
            lunge = int(progress / 0.5 * 35) * boss.direction
        else:
            lunge = int(35) * boss.direction

        _NS_xyrael._draw_shadow(surface, x + lunge, y + 50)
        _NS_xyrael._draw_float_particles(surface, x + lunge, y + 40, pulse,
                                          intense=True)
        _NS_xyrael._draw_assassin_body(surface, x + lunge, y + bob,
                                        boss.direction, pulse, "dash",
                                        progress)

    def _draw_body_spin(surface, boss, x, y, timer, pulse):
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        bob = int(math.sin(pulse * 0.7) * 3)
        _NS_xyrael._draw_shadow(surface, x, y + 50)
        _NS_xyrael._draw_float_particles(surface, x, y + 40, pulse,
                                          intense=True)
        _NS_xyrael._draw_assassin_body(surface, x, y + bob, boss.direction,
                                        pulse, "spin", progress)

    def _draw_body_tempest(surface, boss, x, y, timer, pulse):
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Jump up during tempest.
        if progress < 0.3:
            t = progress / 0.3
            lift = int(t * 40)
        elif progress < 0.75:
            lift = 40
        else:
            t = (progress - 0.75) / 0.25
            lift = int(40 * (1 - t))

        _NS_xyrael._draw_shadow(surface, x, y + 50)
        _NS_xyrael._draw_float_particles(surface, x, y + 40, pulse,
                                          intense=True)
        _NS_xyrael._draw_assassin_body(surface, x, y - lift, boss.direction,
                                        pulse, "tempest", progress)

    def _draw_body_lightness(surface, boss, x, y, timer, pulse):
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        bob = int(math.sin(pulse * 1.5) * 4)
        _NS_xyrael._draw_shadow(surface, x, y + 50)
        _NS_xyrael._draw_ethereal_trail(surface, boss, x, y + bob, pulse,
                                          progress)
        _NS_xyrael._draw_assassin_body(surface, x, y + bob, boss.direction,
                                        pulse, "lightness", progress)

    # ============================================================
    # ASSASSIN BODY
    # ============================================================
    def _draw_assassin_body(surface, cx, cy, facing, phase, action,
                             progress=0):
        """Assassin: legs, torso, arms, head, katana."""
        # Ethereal alpha for lightness form.
        ethereal = (action == "lightness")

        _NS_xyrael._draw_back_leg(surface, cx, cy, facing, phase, action, ethereal)
        _NS_xyrael._draw_front_leg(surface, cx, cy, facing, phase, action, ethereal)
        _NS_xyrael._draw_torso(surface, cx, cy, facing, phase, action, ethereal)
        _NS_xyrael._draw_back_arm(surface, cx, cy, facing, phase, action,
                                    progress, ethereal)
        _NS_xyrael._draw_head_hair(surface, cx, cy - 22, facing, phase, action,
                                     ethereal)
        _NS_xyrael._draw_katana_arm(surface, cx, cy, facing, phase, action,
                                      progress, ethereal)

    def _draw_back_leg(surface, cx, cy, facing, phase, action, ethereal):
        base_x = cx - facing * 3
        knee_x = cx - facing * 5
        knee_y = cy + 18
        foot_x = cx - facing * 5
        foot_y = cy + 32

        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["shadow_deep"],
                            (base_x + 2, cy + 6), (knee_x + 2, knee_y + 1), 6)
        # Thigh (ninja pants).
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_darkest"], [
            (base_x - 3, cy + 6), (base_x + 3, cy + 6),
            (knee_x + 3, knee_y), (knee_x - 3, knee_y),
        ])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_dark"], [
            (base_x - 2, cy + 7), (base_x + 2, cy + 7),
            (knee_x + 2, knee_y - 1), (knee_x - 2, knee_y - 1),
        ])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_mid"], [
            (base_x - 1, cy + 8), (base_x + 1, cy + 8),
            (knee_x + 1, knee_y - 2), (knee_x, knee_y - 2),
        ])
        # Shin.
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_darkest"], [
            (knee_x - 3, knee_y), (knee_x + 3, knee_y),
            (foot_x + 2, foot_y), (foot_x - 2, foot_y),
        ])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_dark"], [
            (knee_x - 2, knee_y + 1), (knee_x + 2, knee_y + 1),
            (foot_x + 1, foot_y - 1), (foot_x - 1, foot_y - 1),
        ])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_mid"], [
            (knee_x - 1, knee_y + 2), (knee_x + 1, knee_y + 2),
            (foot_x, foot_y - 2), (foot_x - 1, foot_y - 2),
        ])
        # Boot.
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_darkest"], [
            (foot_x - 4, foot_y - 1), (foot_x + 3, foot_y - 1),
            (foot_x + 3, foot_y + 2), (foot_x - 4, foot_y + 2),
        ])
        pygame.draw.line(surface, _NS_xyrael.PALETTE["cyan_dark"],
                         (foot_x - 3, foot_y), (foot_x + 2, foot_y), 1)

    def _draw_front_leg(surface, cx, cy, facing, phase, action, ethereal):
        base_x = cx + facing * 3
        knee_x = cx + facing * 5
        knee_y = cy + 18
        foot_x = cx + facing * 7
        foot_y = cy + 32

        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["shadow_deep"],
                            (base_x + 2, cy + 6), (knee_x + 2, knee_y + 1), 7)
        # Thigh.
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_darkest"], [
            (base_x - 3, cy + 6), (base_x + 3, cy + 6),
            (knee_x + 3, knee_y), (knee_x - 3, knee_y),
        ])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_dark"], [
            (base_x - 2, cy + 7), (base_x + 2, cy + 7),
            (knee_x + 2, knee_y - 1), (knee_x - 2, knee_y - 1),
        ])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_mid"], [
            (base_x - 1, cy + 8), (base_x + 2, cy + 8),
            (knee_x + 2, knee_y - 2), (knee_x, knee_y - 2),
        ])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_light"], [
            (base_x, cy + 9), (base_x + 1, cy + 9),
            (knee_x + 1, knee_y - 3), (knee_x, knee_y - 3),
        ])
        # Shin.
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_darkest"], [
            (knee_x - 3, knee_y), (knee_x + 3, knee_y),
            (foot_x + 2, foot_y), (foot_x - 2, foot_y),
        ])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_dark"], [
            (knee_x - 2, knee_y + 1), (knee_x + 2, knee_y + 1),
            (foot_x + 1, foot_y - 1), (foot_x - 1, foot_y - 1),
        ])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_mid"], [
            (knee_x - 1, knee_y + 2), (knee_x + 2, knee_y + 2),
            (foot_x + 1, foot_y - 2), (foot_x - 1, foot_y - 2),
        ])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_light"], [
            (knee_x, knee_y + 3), (knee_x + 1, knee_y + 3),
            (foot_x, foot_y - 3), (foot_x, foot_y - 3),
        ])
        # Boot.
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_darkest"], [
            (foot_x - 3, foot_y - 1), (foot_x + 5, foot_y - 1),
            (foot_x + 5, foot_y + 3), (foot_x - 3, foot_y + 3),
        ])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_dark"], [
            (foot_x - 2, foot_y), (foot_x + 4, foot_y),
            (foot_x + 4, foot_y + 2), (foot_x - 2, foot_y + 2),
        ])
        # Cyan trim.
        pygame.draw.line(surface, _NS_xyrael.PALETTE["cyan_mid"],
                         (foot_x - 2, foot_y), (foot_x + 4, foot_y), 1)
        pygame.draw.rect(surface, _NS_xyrael.PALETTE["cyan_hot"],
                         (foot_x, foot_y, 1, 1))

    def _draw_torso(surface, cx, cy, facing, phase, action, ethereal):
        """Slim assassin torso (dark ninja robe)."""
        breath = math.sin(phase * 0.7) * 1

        # Torso shape (slimmer than warrior).
        torso_shape = [
            (cx - 8, cy - 8),
            (cx - 10, cy - 3),
            (cx - 9, cy + 4),
            (cx - 6, cy + 8),
            (cx + 6, cy + 8),
            (cx + 9, cy + 4),
            (cx + 10, cy - 3),
            (cx + 8, cy - 8),
            (cx + 4, cy - 11),
            (cx - 4, cy - 11),
        ]
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["shadow_deep"],
                          [(px + 2, py + 2) for px, py in torso_shape])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_darkest"], torso_shape)
        # Mid tone.
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_dark"], [
            (cx - 8, cy - 6), (cx - 9, cy),
            (cx - 6, cy + 6), (cx + 6, cy + 6),
            (cx + 9, cy), (cx + 8, cy - 6),
            (cx + 4, cy - 10), (cx - 4, cy - 10),
        ])
        # Highlight.
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_mid"], [
            (cx - 6, cy - 4), (cx - 7, cy),
            (cx - 4, cy + 4), (cx + 4, cy + 4),
            (cx + 7, cy), (cx + 6, cy - 4),
            (cx + 3, cy - 8), (cx - 3, cy - 8),
        ])
        # Chest V-line (armor opening).
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_darkest"], [
            (cx - 3, cy - 8), (cx + 3, cy - 8),
            (cx, cy + 2),
        ])
        # Blue crystal on chest.
        pygame.draw.rect(surface, _NS_xyrael.PALETTE["cyan_darkest"],
                         (cx - 1, cy - 4, 3, 3))
        pygame.draw.rect(surface, _NS_xyrael.PALETTE["cyan_mid"],
                         (cx, cy - 3, 2, 2))
        pygame.draw.rect(surface, _NS_xyrael.PALETTE["cyan_shine"],
                         (cx, cy - 3, 1, 1))

        # Sash (blue belt).
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["sash_dark"], [
            (cx - 9, cy + 6), (cx + 9, cy + 6),
            (cx + 10, cy + 9), (cx - 10, cy + 9),
        ])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["sash_mid"], [
            (cx - 8, cy + 7), (cx + 8, cy + 7),
            (cx + 9, cy + 8), (cx - 9, cy + 8),
        ])
        pygame.draw.line(surface, _NS_xyrael.PALETTE["sash_light"],
                         (cx - 6, cy + 7), (cx + 6, cy + 7), 1)
        # Gold buckle.
        pygame.draw.rect(surface, _NS_xyrael.PALETTE["gold_dark"],
                         (cx - 2, cy + 6, 4, 3))
        pygame.draw.rect(surface, _NS_xyrael.PALETTE["gold_mid"],
                         (cx - 1, cy + 7, 2, 2))
        pygame.draw.rect(surface, _NS_xyrael.PALETTE["gold_shine"],
                         (cx, cy + 7, 1, 1))

        # Cloth flap in front (small).
        flap_sway = math.sin(phase * 0.5) * 1
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_darkest"], [
            (cx - 3, cy + 9), (cx + 3, cy + 9),
            (cx + 4 + int(flap_sway), cy + 16),
            (cx - 4 + int(flap_sway), cy + 16),
        ])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cloth_dark"], [
            (cx - 2, cy + 10), (cx + 2, cy + 10),
            (cx + 3 + int(flap_sway), cy + 15),
            (cx - 3 + int(flap_sway), cy + 15),
        ])
        pygame.draw.line(surface, _NS_xyrael.PALETTE["cyan_dark"],
                         (cx - 2 + int(flap_sway), cy + 12),
                         (cx + 2 + int(flap_sway), cy + 12), 1)

        # Shoulder gold trim.
        pygame.draw.line(surface, _NS_xyrael.PALETTE["gold_dark"],
                         (cx - 8, cy - 9), (cx + 8, cy - 9), 1)
        pygame.draw.line(surface, _NS_xyrael.PALETTE["gold_mid"],
                         (cx - 6, cy - 10), (cx + 6, cy - 10), 1)

    def _draw_head_hair(surface, cx, cy, facing, phase, action, ethereal):
        """Head with pale skin + silver hair + ponytail."""
        # Face base.
        face_shape = [
            (cx - 5, cy - 4), (cx - 6, cy),
            (cx - 4, cy + 5), (cx - 1, cy + 7),
            (cx + 3, cy + 7), (cx + 5, cy + 5),
            (cx + 6, cy), (cx + 5, cy - 4),
            (cx + 2, cy - 7), (cx - 2, cy - 7),
        ]
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["shadow_deep"],
                          [(px + 2, py + 2) for px, py in face_shape])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["skin_darkest"], face_shape)
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["skin_dark"], [
            (cx - 4, cy - 3), (cx - 5, cy),
            (cx - 3, cy + 4), (cx + 3, cy + 4),
            (cx + 5, cy), (cx + 4, cy - 3),
            (cx + 2, cy - 6), (cx - 2, cy - 6),
        ])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["skin_mid"], [
            (cx - 3, cy - 2), (cx - 4, cy),
            (cx - 2, cy + 3), (cx + 3, cy + 3),
            (cx + 4, cy), (cx + 3, cy - 2),
            (cx + 1, cy - 5), (cx - 1, cy - 5),
        ])
        # Face highlight.
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["skin_light"], [
            (cx - 1, cy - 1), (cx + 2, cy - 1),
            (cx + 2, cy + 2), (cx - 1, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_xyrael.PALETTE["skin_shine"],
                         (cx, cy, 1, 1))

        # Silver hair (top, framing face).
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["hair_darkest"], [
            (cx - 6, cy - 7), (cx - 7, cy - 3),
            (cx - 6, cy + 2), (cx - 5, cy - 2),
            (cx - 4, cy - 7),
        ])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["hair_dark"], [
            (cx - 5, cy - 7), (cx - 6, cy - 3),
            (cx - 5, cy), (cx - 4, cy - 2),
            (cx - 3, cy - 7),
        ])
        # Top hair (fringe/bangs).
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["hair_darkest"], [
            (cx - 4, cy - 8), (cx + 4, cy - 8),
            (cx + 6, cy - 6), (cx + 5, cy - 3),
            (cx + 3, cy - 6), (cx - 3, cy - 6),
            (cx - 5, cy - 3), (cx - 6, cy - 6),
        ])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["hair_dark"], [
            (cx - 3, cy - 7), (cx + 3, cy - 7),
            (cx + 5, cy - 5), (cx + 3, cy - 5),
            (cx - 3, cy - 5), (cx - 5, cy - 5),
        ])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["hair_mid"], [
            (cx - 2, cy - 6), (cx + 2, cy - 6),
            (cx + 3, cy - 4), (cx - 3, cy - 4),
        ])
        # Fringe over one eye (bangs).
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["hair_dark"], [
            (cx - 2, cy - 5), (cx + 1, cy - 5),
            (cx, cy - 1), (cx - 2, cy - 2),
        ])
        pygame.draw.rect(surface, _NS_xyrael.PALETTE["hair_light"],
                         (cx - 1, cy - 5, 1, 3))
        pygame.draw.rect(surface, _NS_xyrael.PALETTE["hair_shine"],
                         (cx - 1, cy - 6, 1, 1))

        # PONYTAIL flowing back (very long, khas Ling).
        ponytail_sway = math.sin(phase * 0.7) * 4
        base_pt_x = cx - facing * 5
        base_pt_y = cy - 5

        # Multiple strands.
        for i, (offset_y, length, curve) in enumerate([
            (-2, 18, 3), (0, 22, 4), (2, 20, 3), (4, 16, 2),
        ]):
            start = (base_pt_x, base_pt_y + offset_y)
            wave = math.sin(phase * 0.9 + i * 0.5) * 2
            mid = (start[0] - facing * (length * 0.5),
                   start[1] + int(curve + wave))
            end = (start[0] - facing * length + int(ponytail_sway),
                   start[1] + int(curve * 2 + wave))

            # Shadow.
            _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["shadow_deep"],
                                (start[0] + 1, start[1] + 1),
                                (end[0] + 1, end[1] + 1), 3)
            # Main strand.
            _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["hair_darkest"],
                                start, mid, 3)
            _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["hair_darkest"],
                                mid, end, 2)
            _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["hair_dark"],
                                start, mid, 2)
            _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["hair_dark"],
                                mid, end, 1)
            _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["hair_mid"],
                                (start[0], start[1] - 1),
                                (mid[0], mid[1] - 1), 1)
            # Highlight strand.
            if i == 1:
                _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["hair_light"],
                                    start, end, 1)
                pygame.draw.rect(surface, _NS_xyrael.PALETTE["hair_shine"],
                                 (mid[0], mid[1] - 1, 1, 1))

        # Piercing cyan eye (glow).
        ex = cx + 2 * facing
        ey = cy + 1
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Glow around eye.
        for r in range(3, 0, -1):
            alpha = _NS_xyrael._alpha(150 * (3 - r) / 3 * pulse)
            _NS_xyrael._aacircle(surface,
                                  (*_NS_xyrael.PALETTE["cyan_light"], alpha),
                                  (ex, ey), r)
        pygame.draw.rect(surface, _NS_xyrael.PALETTE["eye_dark"],
                         (ex - 1, ey, 3, 2))
        pygame.draw.rect(surface, _NS_xyrael.PALETTE["cyan_light"],
                         (ex, ey, 2, 1))
        pygame.draw.rect(surface, _NS_xyrael.PALETTE["cyan_shine"],
                         (ex + 1, ey, 1, 1))

        # Small mouth (calm).
        pygame.draw.line(surface, _NS_xyrael.PALETTE["skin_darkest"],
                         (cx - 1, cy + 5), (cx + 1, cy + 5), 1)

    def _draw_back_arm(surface, cx, cy, facing, phase, action, progress,
                        ethereal):
        """Back arm - typically holding sheath or gesturing."""
        shoulder_x = cx - facing * 8
        shoulder_y = cy - 8

        # Arm angle changes with action.
        if action == "attack":
            arm_swing = math.sin(progress * math.pi) * -8
        elif action == "spin":
            arm_swing = math.cos(progress * math.pi * 4) * 6
        elif action == "dash":
            arm_swing = -12
        elif action == "tempest":
            arm_swing = -6 if progress > 0.3 else 0
        else:
            arm_swing = math.sin(phase * 0.6) * 3

        elbow_x = shoulder_x - facing * 5
        elbow_y = shoulder_y + 6 + int(arm_swing * 0.3)
        hand_x = shoulder_x - facing * 8
        hand_y = shoulder_y + 12 + int(arm_swing * 0.4)

        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["shadow_deep"],
                            (shoulder_x + 2, shoulder_y + 2),
                            (elbow_x + 2, elbow_y + 2), 4)
        # Upper arm (ninja sleeve).
        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["cloth_darkest"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["cloth_dark"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 2)
        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["cloth_mid"],
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), 1)
        # Forearm (skin).
        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["skin_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["skin_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 2)
        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["skin_mid"],
                            (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
        # Cyan wrist wrap.
        _NS_xyrael._aacircle(surface, _NS_xyrael.PALETTE["cyan_dark"],
                              (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_xyrael.PALETTE["cyan_hot"],
                         (hand_x, hand_y - 1, 1, 1))
        # Hand.
        _NS_xyrael._aacircle(surface, _NS_xyrael.PALETTE["skin_dark"],
                              (hand_x, hand_y), 2)

    def _draw_katana_arm(surface, cx, cy, facing, phase, action, progress,
                          ethereal):
        """Front arm holding katana."""
        shoulder_x = cx + facing * 8
        shoulder_y = cy - 8

        # Pose logic.
        if action == "attack":
            # Fast swing.
            angle = -math.pi / 3 + progress * math.pi * 1.1
            elbow_x = shoulder_x + facing * int(math.cos(angle) * 7)
            elbow_y = shoulder_y + int(math.sin(angle) * 7)
            hand_x = shoulder_x + facing * int(math.cos(angle) * 14)
            hand_y = shoulder_y + int(math.sin(angle) * 14)
            blade_angle = angle - 0.3
        elif action == "dash":
            # Blade extended forward.
            elbow_x = shoulder_x + facing * 7
            elbow_y = shoulder_y + 2
            hand_x = shoulder_x + facing * 16
            hand_y = shoulder_y + 3
            blade_angle = 0.1 if facing > 0 else math.pi - 0.1
        elif action == "spin":
            angle = progress * math.pi * 6
            elbow_x = shoulder_x + int(math.cos(angle) * 8)
            elbow_y = shoulder_y + int(math.sin(angle) * 4) + 2
            hand_x = shoulder_x + int(math.cos(angle) * 16)
            hand_y = shoulder_y + int(math.sin(angle) * 8) + 4
            blade_angle = angle + math.pi / 2
        elif action == "tempest":
            # Overhead pose.
            elbow_x = shoulder_x + facing * 3
            elbow_y = shoulder_y - 6
            hand_x = shoulder_x + facing * 5
            hand_y = shoulder_y - 14
            blade_angle = -math.pi / 2
        elif action == "lightness":
            # Blade back trailing.
            elbow_x = shoulder_x + facing * 4
            elbow_y = shoulder_y + 4
            hand_x = shoulder_x + facing * 10
            hand_y = shoulder_y + 8
            blade_angle = 0.5 if facing > 0 else math.pi - 0.5
        else:
            # Idle: blade held to side.
            sway = math.sin(phase * 0.6) * 1
            elbow_x = shoulder_x + facing * 6
            elbow_y = shoulder_y + 6 + int(sway)
            hand_x = shoulder_x + facing * 12
            hand_y = shoulder_y + 10 + int(sway)
            blade_angle = -0.15 if facing > 0 else math.pi + 0.15

        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["shadow_deep"],
                            (shoulder_x + 2, shoulder_y + 2),
                            (elbow_x + 2, elbow_y + 2), 5)
        # Upper arm.
        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["cloth_darkest"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["cloth_dark"],
                            (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["cloth_mid"],
                            (shoulder_x, shoulder_y - 1),
                            (elbow_x, elbow_y - 1), 1)
        # Gold trim on shoulder.
        _NS_xyrael._aacircle(surface, _NS_xyrael.PALETTE["gold_dark"],
                              (shoulder_x, shoulder_y), 3)
        _NS_xyrael._aacircle(surface, _NS_xyrael.PALETTE["gold_mid"],
                              (shoulder_x, shoulder_y), 2)
        pygame.draw.rect(surface, _NS_xyrael.PALETTE["gold_shine"],
                         (shoulder_x, shoulder_y - 1, 1, 1))
        # Forearm (skin).
        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["skin_darkest"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["skin_dark"],
                            (elbow_x, elbow_y), (hand_x, hand_y), 2)
        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["skin_mid"],
                            (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
        # Cyan wrap on wrist.
        _NS_xyrael._aacircle(surface, _NS_xyrael.PALETTE["cyan_dark"],
                              (hand_x, hand_y), 3)
        _NS_xyrael._aacircle(surface, _NS_xyrael.PALETTE["cyan_mid"],
                              (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_xyrael.PALETTE["cyan_shine"],
                         (hand_x, hand_y, 1, 1))
        # Hand.
        _NS_xyrael._aacircle(surface, _NS_xyrael.PALETTE["skin_dark"],
                              (hand_x, hand_y), 2)

        # Katana.
        _NS_xyrael._draw_katana(surface, hand_x, hand_y, blade_angle,
                                 facing, phase, action)

    def _draw_katana(surface, hx, hy, angle, facing, phase, action):
        """Long straight katana with cyan glow."""
        length = 36
        dx = math.cos(angle) * facing
        dy = math.sin(angle)

        tip_x = hx + int(dx * length)
        tip_y = hy + int(dy * length)

        # Perpendicular for blade width.
        perp_dx = -math.sin(angle) * facing
        perp_dy = math.cos(angle)

        # Straight blade (katana is straight, slight taper).
        base_a = (hx + int(perp_dx * 2), hy + int(perp_dy * 2))
        base_b = (hx - int(perp_dx * 2), hy - int(perp_dy * 2))

        # Point near tip (taper).
        near_tip_x = hx + int(dx * (length - 4))
        near_tip_y = hy + int(dy * (length - 4))
        near_tip_a = (near_tip_x + int(perp_dx * 2),
                      near_tip_y + int(perp_dy * 2))
        near_tip_b = (near_tip_x - int(perp_dx * 2),
                      near_tip_y - int(perp_dy * 2))

        # Shadow.
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["shadow_deep"], [
            (base_a[0] + 2, base_a[1] + 2),
            (near_tip_a[0] + 2, near_tip_a[1] + 2),
            (tip_x + 2, tip_y + 2),
            (near_tip_b[0] + 2, near_tip_b[1] + 2),
            (base_b[0] + 2, base_b[1] + 2),
        ])
        # Blade body.
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["blade_darkest"], [
            base_a, near_tip_a, (tip_x, tip_y), near_tip_b, base_b,
        ])
        _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["blade_dark"], [
            (int(base_a[0] * 0.9 + base_b[0] * 0.1),
             int(base_a[1] * 0.9 + base_b[1] * 0.1)),
            (int(near_tip_a[0] * 0.9 + near_tip_b[0] * 0.1),
             int(near_tip_a[1] * 0.9 + near_tip_b[1] * 0.1)),
            (tip_x, tip_y),
            (int(near_tip_a[0] * 0.1 + near_tip_b[0] * 0.9),
             int(near_tip_a[1] * 0.1 + near_tip_b[1] * 0.9)),
            (int(base_a[0] * 0.1 + base_b[0] * 0.9),
             int(base_a[1] * 0.1 + base_b[1] * 0.9)),
        ])
        # Bright center line (blade shine).
        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["blade_light"],
                            (int((base_a[0] + base_b[0]) / 2),
                             int((base_a[1] + base_b[1]) / 2)),
                            (tip_x, tip_y), 1)
        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["blade_shine"],
                            (int((base_a[0] + base_b[0]) / 2),
                             int((base_a[1] + base_b[1]) / 2)),
                            (int((near_tip_a[0] + near_tip_b[0]) / 2),
                             int((near_tip_a[1] + near_tip_b[1]) / 2)),
                            1)

        # CYAN CRYSTALLINE GLOW along edge (khas Ling).
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        alpha_glow = _NS_xyrael._alpha(220 * pulse)
        # Wide glow.
        for glow_layer in range(3):
            glow_alpha = _NS_xyrael._alpha((220 - glow_layer * 60) * pulse)
            _NS_xyrael._aaline(surface,
                                (*_NS_xyrael.PALETTE["cyan_mid"], glow_alpha),
                                base_a, (tip_x, tip_y), 1)
            _NS_xyrael._aaline(surface,
                                (*_NS_xyrael.PALETTE["cyan_mid"], glow_alpha),
                                base_b, (tip_x, tip_y), 1)
        _NS_xyrael._aaline(surface,
                            (*_NS_xyrael.PALETTE["cyan_light"], alpha_glow),
                            base_a, (tip_x, tip_y), 1)
        _NS_xyrael._aaline(surface,
                            (*_NS_xyrael.PALETTE["cyan_hot"], alpha_glow),
                            (int((base_a[0] + base_b[0]) / 2),
                             int((base_a[1] + base_b[1]) / 2)),
                            (tip_x, tip_y), 1)

        # Bright tip glow.
        for r in range(4, 0, -1):
            alpha = _NS_xyrael._alpha(180 * (4 - r) / 4 * pulse)
            _NS_xyrael._aacircle(surface,
                                  (*_NS_xyrael.PALETTE["cyan_light"], alpha),
                                  (tip_x, tip_y), r)
        _NS_xyrael._aacircle(surface, _NS_xyrael.PALETTE["cyan_hot"],
                              (tip_x, tip_y), 2)
        _NS_xyrael._aacircle(surface, _NS_xyrael.PALETTE["cyan_shine"],
                              (tip_x, tip_y), 1)
        pygame.draw.rect(surface, _NS_xyrael.PALETTE["white"],
                         (tip_x, tip_y, 1, 1))

        # Cross-guard (small, gold + cyan gem).
        guard_a = (hx + int(perp_dx * 4), hy + int(perp_dy * 4))
        guard_b = (hx - int(perp_dx * 4), hy - int(perp_dy * 4))
        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["gold_dark"],
                            guard_a, guard_b, 3)
        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["gold_mid"],
                            guard_a, guard_b, 2)
        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["gold_light"],
                            guard_a, guard_b, 1)

        # Handle behind hand.
        handle_back_x = hx - int(dx * 8)
        handle_back_y = hy - int(dy * 8)
        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["cloth_darkest"],
                            (hx, hy), (handle_back_x, handle_back_y), 3)
        _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["sash_dark"],
                            (hx, hy), (handle_back_x, handle_back_y), 2)
        # Pommel (cyan gem).
        _NS_xyrael._aacircle(surface, _NS_xyrael.PALETTE["gold_dark"],
                              (handle_back_x, handle_back_y), 2)
        pygame.draw.rect(surface, _NS_xyrael.PALETTE["cyan_light"],
                         (handle_back_x, handle_back_y, 1, 1))

    def _draw_melee_swing(surface, cx, cy, facing, progress):
        """Fast cyan slash arc from katana."""
        if progress < 0.25 or progress > 0.85:
            return
        t = (progress - 0.25) / 0.6

        # Multiple trail segments.
        for i in range(10):
            trail_t = t - i * 0.05
            if trail_t < 0:
                continue
            a = -math.pi / 3 + trail_t * math.pi * 1.1
            radius = 30
            arc_x = cx + int(math.cos(a) * radius) * facing
            arc_y = cy - 5 + int(math.sin(a) * radius)
            alpha = _NS_xyrael._alpha(230 - i * 22)

            _NS_xyrael._aacircle(surface,
                                  (*_NS_xyrael.PALETTE["cyan_dark"], alpha),
                                  (arc_x, arc_y), 4)
            _NS_xyrael._aacircle(surface,
                                  (*_NS_xyrael.PALETTE["cyan_mid"], alpha),
                                  (arc_x, arc_y), 3)
            _NS_xyrael._aacircle(surface,
                                  (*_NS_xyrael.PALETTE["cyan_light"], alpha),
                                  (arc_x, arc_y), 2)
            pygame.draw.rect(surface,
                             (*_NS_xyrael.PALETTE["cyan_hot"], alpha),
                             (arc_x, arc_y, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_xyrael.PALETTE["white"], alpha),
                             (arc_x, arc_y, 1, 1))

    # ============================================================
    # FLOAT PARTICLES (cyan crystalline)
    # ============================================================
    def _draw_float_particles(surface, cx, cy, phase, intense=False):
        strength = 1.5 if intense else 1.0

        # Cyan energy pool below.
        pool = pygame.Surface((90, 24), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        for r in range(18, 2, -2):
            alpha = _NS_xyrael._alpha((18 - r) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(pool,
                                    (*_NS_xyrael.PALETTE["cyan_dark"], alpha),
                                    (45 - r, 12 - r // 4,
                                     r * 2, max(2, r // 2)))
        for r in range(10, 1, -1):
            alpha = _NS_xyrael._alpha((10 - r) * 6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(pool,
                                    (*_NS_xyrael.PALETTE["cyan_mid"], alpha),
                                    (45 - r, 12 - r // 4,
                                     r * 2, max(2, r // 3)))
        surface.blit(pool, (cx - 45, cy - 5))

        # Crystalline shards floating up.
        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            sx = cx - 20 + i * 5 + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 24)
            alpha = _NS_xyrael._alpha(230 * (1 - t) * strength)
            if alpha <= 0:
                continue
            # Small diamond shard.
            _NS_xyrael._poly(surface, (*_NS_xyrael.PALETTE["cyan_dark"], alpha), [
                (sx, sy - 2), (sx + 1, sy), (sx, sy + 1), (sx - 1, sy),
            ])
            pygame.draw.rect(surface,
                             (*_NS_xyrael.PALETTE["cyan_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_xyrael.PALETTE["cyan_shine"], alpha),
                             (sx, sy - 2, 1, 1))

        # Scattered crystals.
        for i in range(4):
            angle = phase * 0.8 + i * math.pi / 2
            sx = cx + int(math.cos(angle) * 22)
            sy = cy + 8 + int(math.sin(angle) * 4)
            pygame.draw.rect(surface, _NS_xyrael.PALETTE["cyan_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_xyrael.PALETTE["cyan_hot"],
                             (sx, sy, 1, 1))

    # ============================================================
    # ETHEREAL TRAIL (for lightness form)
    # ============================================================
    def _draw_ethereal_trail(surface, boss, cx, cy, phase, progress):
        """Fast-moving ghost trail behind assassin."""
        facing = boss.direction
        for i in range(8):
            offset = i * 12
            tx = cx - offset * facing
            ty = cy + int(math.sin(phase + i) * 2)
            alpha = _NS_xyrael._alpha(180 * (1 - i / 8))
            # Silhouette wisp.
            _NS_xyrael._aacircle(surface,
                                  (*_NS_xyrael.PALETTE["cyan_dark"], alpha),
                                  (tx, ty), max(2, 8 - i))
            _NS_xyrael._aacircle(surface,
                                  (*_NS_xyrael.PALETTE["cyan_mid"], alpha // 2),
                                  (tx, ty - 5), max(1, 6 - i))
            pygame.draw.rect(surface,
                             (*_NS_xyrael.PALETTE["cyan_hot"], alpha),
                             (tx, ty - 3, 1, 2))

    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((100, 24), pygame.SRCALPHA)
        for r in range(12, 0, -1):
            alpha = max(0, (12 - r) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - r, 12 - r,
                                 80 + r * 2, r * 2))
        pygame.draw.ellipse(shadow, (5, 10, 25, 160), (5, 6, 90, 12))
        pygame.draw.ellipse(shadow, (30, 80, 180, 80), (12, 8, 76, 8))
        surface.blit(shadow, (x - 50, y - 12))

    def _draw_cyan_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.25 + 0.75
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for r in range(90, 5, -5):
            alpha = _NS_xyrael._alpha((90 - r) * 1.2 * pulse)
            if alpha > 0:
                _NS_xyrael._aacircle(aura,
                                      (*_NS_xyrael.PALETTE["cyan_darkest"], alpha),
                                      (100, 90), r)
        for r in range(55, 5, -4):
            alpha = _NS_xyrael._alpha((55 - r) * 1.4 * pulse)
            if alpha > 0:
                _NS_xyrael._aacircle(aura,
                                      (*_NS_xyrael.PALETTE["cyan_dark"], alpha),
                                      (100, 90), r)
        surface.blit(aura, (x - 100, y - 90))

        # Diamond sparkles around.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            radius = 40 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cyan_mid"], [
                (sx, sy - 2), (sx + 2, sy), (sx, sy + 2), (sx - 2, sy),
            ])
            pygame.draw.rect(surface, _NS_xyrael.PALETTE["cyan_hot"],
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((150, 46), pygame.SRCALPHA)
        pygame.draw.ellipse(ring,
                            (*_NS_xyrael.PALETTE["rune_dark"], 200),
                            (5, 15, 140, 22), 3)
        pygame.draw.ellipse(ring,
                            (*_NS_xyrael.PALETTE["cyan_darkest"], 220),
                            (14, 17, 122, 18), 2)
        pygame.draw.ellipse(ring,
                            (*_NS_xyrael.PALETTE["cyan_dark"], 230),
                            (25, 19, 100, 14), 1)

        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 75 + int(math.cos(angle) * 40)
            y1 = 26 + int(math.sin(angle) * 7)
            x2 = 75 + int(math.cos(angle) * 62)
            y2 = 26 + int(math.sin(angle) * 11)
            pygame.draw.line(ring,
                             (*_NS_xyrael.PALETTE["cyan_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_xyrael.PALETTE["cyan_hot"],
                                 _NS_xyrael._alpha(150 * pulse)),
                                (15, 10, 120, 32), 1)
        surface.blit(ring, (x - 75, y - 23))

    # ============================================================
    # SKILL Q: FINCH POISE - dash slash
    # ============================================================
    def _draw_finch_ground(surface, boss, x, y, timer, phase):
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        if progress > 0.3:
            # Dash trail on ground.
            for i in range(6):
                tx = x - facing * (i * 12)
                ty = y + 40
                alpha = _NS_xyrael._alpha(200 - i * 30)
                pygame.draw.ellipse(surface,
                                    (*_NS_xyrael.PALETTE["cyan_dark"], alpha),
                                    (tx - 8, ty - 3, 16, 6))
                pygame.draw.ellipse(surface,
                                    (*_NS_xyrael.PALETTE["cyan_mid"], alpha),
                                    (tx - 6, ty - 2, 12, 4))

    def _draw_finch_fg(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Fast forward slash - single big crescent.
        if progress < 0.5:
            # Trail behind boss.
            for i in range(8):
                tx = x - facing * (i * 8)
                ty = y - 8 + int(math.sin(phase + i) * 2)
                alpha = _NS_xyrael._alpha(230 - i * 28)
                _NS_xyrael._aacircle(surface,
                                      (*_NS_xyrael.PALETTE["cyan_mid"], alpha),
                                      (tx, ty), 4)
                _NS_xyrael._aacircle(surface,
                                      (*_NS_xyrael.PALETTE["cyan_light"], alpha),
                                      (tx, ty), 2)
        else:
            # Slash arc in front.
            t = (progress - 0.5) / 0.5
            arc_intensity = math.sin(t * math.pi)
            for i in range(15):
                a = -math.pi / 3 + (i / 14) * math.pi * 0.9
                radius = 40
                ax = x + int(math.cos(a) * radius) * facing
                ay = y - 4 + int(math.sin(a) * radius)
                alpha = _NS_xyrael._alpha(240 * arc_intensity)
                if alpha <= 0:
                    continue
                _NS_xyrael._aacircle(surface,
                                      (*_NS_xyrael.PALETTE["cyan_dark"], alpha),
                                      (ax, ay), 5)
                _NS_xyrael._aacircle(surface,
                                      (*_NS_xyrael.PALETTE["cyan_mid"], alpha),
                                      (ax, ay), 4)
                _NS_xyrael._aacircle(surface,
                                      (*_NS_xyrael.PALETTE["cyan_light"], alpha),
                                      (ax, ay), 2)
                pygame.draw.rect(surface,
                                 (*_NS_xyrael.PALETTE["cyan_hot"], alpha),
                                 (ax, ay, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_xyrael.PALETTE["white"], alpha),
                                 (ax, ay, 1, 1))

    # ============================================================
    # SKILL W: DEFIANT SWORD - multiple curved slashes around boss
    # ============================================================
    def _draw_defiant_fg(surface, boss, x, y, timer, phase):
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Multiple curved blade slashes emanating outward.
        num_slashes = 6
        for i in range(num_slashes):
            slash_angle = i * math.pi * 2 / num_slashes + progress * math.pi
            slash_dist = 30 + int(progress * 25)

            # Slash line (curved trail).
            for j in range(6):
                t = j / 5
                a = slash_angle + t * 0.3
                dist = slash_dist - int(t * 8)
                sx = x + int(math.cos(a) * dist)
                sy = y - 4 + int(math.sin(a) * dist * 0.6)
                alpha = _NS_xyrael._alpha(230 * (1 - progress * 0.5)
                                            * (1 - t * 0.5))
                if alpha <= 0:
                    continue
                size = max(1, 4 - j // 2)
                _NS_xyrael._aacircle(surface,
                                      (*_NS_xyrael.PALETTE["cyan_dark"], alpha),
                                      (sx, sy), size + 1)
                _NS_xyrael._aacircle(surface,
                                      (*_NS_xyrael.PALETTE["cyan_mid"], alpha),
                                      (sx, sy), size)
                _NS_xyrael._aacircle(surface,
                                      (*_NS_xyrael.PALETTE["cyan_light"], alpha),
                                      (sx, sy), max(1, size - 2))
                pygame.draw.rect(surface,
                                 (*_NS_xyrael.PALETTE["cyan_hot"], alpha),
                                 (sx, sy, 1, 1))

            # Blade tip (small sword shape at end).
            tip_a = slash_angle
            tip_x = x + int(math.cos(tip_a) * slash_dist)
            tip_y = y - 4 + int(math.sin(tip_a) * slash_dist * 0.6)
            perp = tip_a + math.pi / 2
            tip_end_x = tip_x + int(math.cos(tip_a) * 8)
            tip_end_y = tip_y + int(math.sin(tip_a) * 8)
            wing_a = (tip_x + int(math.cos(perp) * 2),
                      tip_y + int(math.sin(perp) * 2))
            wing_b = (tip_x - int(math.cos(perp) * 2),
                      tip_y - int(math.sin(perp) * 2))
            alpha = _NS_xyrael._alpha(240 * (1 - progress * 0.4))
            _NS_xyrael._poly(surface,
                              (*_NS_xyrael.PALETTE["cyan_mid"], alpha), [
                                  (tip_end_x, tip_end_y), wing_a, wing_b,
                              ])
            _NS_xyrael._poly(surface,
                              (*_NS_xyrael.PALETTE["cyan_light"], alpha), [
                                  (tip_end_x, tip_end_y),
                                  (int((tip_end_x + wing_a[0]) / 2),
                                   int((tip_end_y + wing_a[1]) / 2)),
                                  tip_x,
                              ])
            pygame.draw.rect(surface, _NS_xyrael.PALETTE["cyan_shine"],
                             (tip_end_x, tip_end_y, 1, 1))

    # ============================================================
    # SKILL E: TEMPEST OF BLADES - crystal blade spikes from ground (SIGNATURE!)
    # ============================================================
    def _draw_tempest_ground(surface, boss, x, y, timer, phase):
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            return

        # Ground glow.
        t = (progress - 0.3) / 0.7
        r = int(50 * min(1.0, t * 2))
        alpha = _NS_xyrael._alpha(200 * (1 - t * 0.4))
        pygame.draw.ellipse(surface,
                            (*_NS_xyrael.PALETTE["cyan_darkest"], alpha),
                            (x - r, y + 40 - r // 3,
                             r * 2, r * 2 // 3))
        pygame.draw.ellipse(surface,
                            (*_NS_xyrael.PALETTE["cyan_dark"], alpha),
                            (x - r + 3, y + 40 - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4))
        pygame.draw.ellipse(surface,
                            (*_NS_xyrael.PALETTE["cyan_mid"], alpha),
                            (x - r + 8, y + 40 - r // 3 + 4,
                             r * 2 - 16, r * 2 // 3 - 8))

    def _draw_tempest_fg(surface, boss, x, y, timer, phase):
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            return

        t = (progress - 0.3) / 0.7

        # CRYSTAL BLADE SPIKES erupting from ground (like Ling's E).
        num_spikes = 14
        for i in range(num_spikes):
            # Spread in area.
            angle = i * math.pi * 2 / num_spikes + t * 0.5
            spread_dist = 15 + (i % 5) * 10
            spike_x = x + int(math.cos(angle) * spread_dist)
            spike_base_y = y + 40 + int(math.sin(angle) * spread_dist * 0.4)

            # Spike stagger appearance.
            spike_progress = min(1.0, max(0.0, t * 2 - i * 0.05))
            if spike_progress < 0.05:
                continue

            # Spike height (blade-like tall).
            max_h = 40 + (i % 3) * 8
            spike_h = int(spike_progress * max_h)
            if spike_progress > 0.7:
                # Fade out at end.
                fade = 1 - (spike_progress - 0.7) / 0.3
                spike_h = int(spike_h * (0.7 + fade * 0.3))

            if spike_h < 3:
                continue

            spike_tip_y = spike_base_y - spike_h
            spike_width = 3

            # Shadow.
            _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_tip_y + 1),
                (spike_x - spike_width + 1, spike_base_y + 1),
                (spike_x + spike_width + 1, spike_base_y + 1),
            ])
            # Spike body (elongated blade shape).
            _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cyan_darkest"], [
                (spike_x, spike_tip_y),
                (spike_x - spike_width, spike_base_y),
                (spike_x + spike_width, spike_base_y),
            ])
            _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cyan_dark"], [
                (spike_x, spike_tip_y),
                (spike_x - spike_width + 1, spike_base_y),
                (spike_x + spike_width - 1, spike_base_y),
            ])
            _NS_xyrael._poly(surface, _NS_xyrael.PALETTE["cyan_mid"], [
                (spike_x, spike_tip_y),
                (spike_x - 1, spike_base_y),
                (spike_x + 1, spike_base_y),
            ])
            # Bright center vein.
            _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["cyan_light"],
                                (spike_x, spike_tip_y),
                                (spike_x, spike_base_y), 1)
            _NS_xyrael._aaline(surface, _NS_xyrael.PALETTE["cyan_hot"],
                                (spike_x, spike_tip_y + 2),
                                (spike_x, spike_base_y - 2), 1)

            # Bright tip.
            pygame.draw.rect(surface, _NS_xyrael.PALETTE["cyan_shine"],
                             (spike_x, spike_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_xyrael.PALETTE["white"],
                             (spike_x, spike_tip_y, 1, 1))

            # Glow around tip.
            for gr in range(3, 0, -1):
                alpha = _NS_xyrael._alpha(120 * (3 - gr) / 3)
                _NS_xyrael._aacircle(surface,
                                      (*_NS_xyrael.PALETTE["cyan_light"], alpha),
                                      (spike_x, spike_tip_y), gr)

        # Rising cyan particles around.
        for i in range(12):
            p_t = (phase * 1.5 + i * 0.1) % 1.0
            angle = i * math.pi * 2 / 12
            px = x + int(math.cos(angle) * 40)
            py = y + 40 - int(p_t * 50)
            alpha = _NS_xyrael._alpha(230 * (1 - p_t))
            _NS_xyrael._poly(surface, (*_NS_xyrael.PALETTE["cyan_light"], alpha), [
                (px, py - 2), (px + 1, py), (px, py + 1), (px - 1, py),
            ])
            pygame.draw.rect(surface,
                             (*_NS_xyrael.PALETTE["cyan_shine"], alpha),
                             (px, py, 1, 1))

    # ============================================================
    # SKILL R: LIGHTNESS OF BEING - ethereal ghost form
    # ============================================================
    def _draw_lightness_ground(surface, boss, x, y, timer, phase):
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Pulsing energy ring.
        r = int(30 + math.sin(phase * 2) * 5)
        alpha = _NS_xyrael._alpha(200 * (1 - progress * 0.3))
        pygame.draw.ellipse(surface,
                            (*_NS_xyrael.PALETTE["cyan_mid"], alpha),
                            (x - r, y + 40 - r // 3,
                             r * 2, r * 2 // 3), 2)
        pygame.draw.ellipse(surface,
                            (*_NS_xyrael.PALETTE["cyan_light"], alpha),
                            (x - r + 3, y + 40 - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4), 1)

    def _draw_lightness_fg(surface, boss, x, y, timer, phase):
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ethereal flames rising from body.
        for i in range(10):
            t = (phase * 1.0 + i * 0.1) % 1.0
            angle = i * math.pi / 5 + phase * 0.5
            offset_x = int(math.cos(angle) * 10)
            offset_y = int(math.sin(angle) * 15)
            fx = x + offset_x
            fy = y + offset_y - int(t * 30)
            alpha = _NS_xyrael._alpha(220 * (1 - t) * (1 - progress * 0.3))
            _NS_xyrael._aacircle(surface,
                                  (*_NS_xyrael.PALETTE["cyan_dark"], alpha),
                                  (fx, fy), 4)
            _NS_xyrael._aacircle(surface,
                                  (*_NS_xyrael.PALETTE["cyan_mid"], alpha),
                                  (fx, fy - 2), 3)
            _NS_xyrael._aacircle(surface,
                                  (*_NS_xyrael.PALETTE["cyan_light"], alpha),
                                  (fx, fy - 3), 2)
            pygame.draw.rect(surface,
                             (*_NS_xyrael.PALETTE["cyan_hot"], alpha),
                             (fx, fy - 4, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_xyrael.PALETTE["cyan_shine"], alpha),
                             (fx, fy - 5, 1, 1))

        # Fast forward motion streaks.
        facing = boss.direction
        for i in range(5):
            streak_x = x + facing * (i * 15)
            streak_y = y - 8 + int(math.sin(phase * 2 + i) * 4)
            alpha = _NS_xyrael._alpha(200 - i * 35)
            _NS_xyrael._aaline(surface,
                                (*_NS_xyrael.PALETTE["cyan_light"], alpha),
                                (streak_x, streak_y),
                                (streak_x + facing * 8, streak_y), 2)
            _NS_xyrael._aaline(surface,
                                (*_NS_xyrael.PALETTE["cyan_hot"], alpha),
                                (streak_x, streak_y),
                                (streak_x + facing * 6, streak_y), 1)


# ====================================================================
# nyxareth.py
# ====================================================================

"""
NYXARETH - The Cosmic Sovereign
TRUE BOSS cosmic mage dengan galactic power.
Gaya rendering mengikuti _NS_vhorethzir.
"""



class _NS_nyxareth:
    """Namespace nyxareth - cosmic true boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin (pale cosmic)
        "skin_darkest": (60, 45, 75),
        "skin_dark": (110, 90, 130),
        "skin_mid": (170, 150, 190),
        "skin_light": (215, 200, 230),
        "skin_shine": (245, 235, 250),

        # Robe cosmic purple (main body)
        "robe_darkest": (10, 5, 25),
        "robe_dark": (30, 15, 60),
        "robe_mid": (65, 35, 115),
        "robe_light": (110, 65, 175),
        "robe_shine": (170, 120, 230),

        # Deep void purple
        "void_darkest": (5, 0, 15),
        "void_dark": (15, 8, 35),
        "void_mid": (35, 20, 75),
        "void_light": (70, 45, 130),

        # Gold armor trim (chest plate, accents)
        "gold_darkest": (55, 40, 10),
        "gold_dark": (115, 85, 25),
        "gold_mid": (200, 155, 50),
        "gold_light": (245, 215, 110),
        "gold_shine": (255, 245, 190),

        # Cosmic purple (skill theme - main)
        "cosmic_darkest": (25, 5, 55),
        "cosmic_dark": (65, 20, 130),
        "cosmic_mid": (135, 55, 220),
        "cosmic_light": (200, 130, 255),
        "cosmic_hot": (235, 180, 255),
        "cosmic_shine": (250, 225, 255),

        # Star white
        "star_dim": (180, 180, 220),
        "star_mid": (230, 220, 255),
        "star_bright": (255, 255, 255),

        # Eye (purple glow)
        "eye_dark": (10, 5, 20),
        "eye_purple": (180, 100, 255),
        "eye_shine": (240, 200, 255),

        # Ground/rune
        "rune_dark": (25, 10, 55),
        "rune_mid": (100, 40, 180),
        "rune_light": (200, 130, 255),

        # Nebula (background aura)
        "nebula_dark": (40, 15, 80),
        "nebula_mid": (100, 40, 170),
        "nebula_pink": (200, 100, 220),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    # ============================================================
    # HELPERS
    # ============================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_nyxareth._clamp(color)
        if _NS_nyxareth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_nyxareth._clamp(color)
        if _NS_nyxareth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        valid_points = []
        for p in points:
            try:
                if hasattr(p, '__len__') and len(p) >= 2:
                    valid_points.append((int(p[0]), int(p[1])))
            except (TypeError, ValueError):
                continue
        if len(valid_points) < 3:
            if len(valid_points) == 2:
                pygame.draw.line(surface, _NS_nyxareth._clamp(color),
                                 valid_points[0], valid_points[1], 1)
            return
        pygame.draw.polygon(surface, _NS_nyxareth._clamp(color), valid_points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar
            # (x, y) dengan kompensasi scale (hero di-render di
            # canvas lalu di-scale; boss langsung di layar).
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        return int(x + 260 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_nyxareth(surface, boss, x, y):
        """Entry point utama."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_nyxareth._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_nxa_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 45) - 15
        )

        # BIG cosmic aura behind (true boss).
        _NS_nyxareth._draw_cosmic_aura(surface, x, y, pulse)
        _NS_nyxareth._draw_ground_ring(surface, x, y + 55, pulse, active_skill)

        # Ultimate FX (largest - drawn behind everything else too).
        if active_skill == "4":
            _NS_nyxareth._draw_astro_realm_bg(surface, boss, x, y,
                                               skill_timer, pulse)

        # Skill ground FX.
        if active_skill == "1":
            _NS_nyxareth._draw_starsplit_ground(surface, boss, x, y,
                                                  skill_timer, pulse)
        elif active_skill == "2":
            _NS_nyxareth._draw_realworld_ground(surface, boss, x, y,
                                                  skill_timer, pulse)
        elif active_skill == "3":
            _NS_nyxareth._draw_spacetime_ground(surface, boss, x, y,
                                                  skill_timer, pulse)

        # Body.
        if attacking:
            _NS_nyxareth._draw_body_attack(surface, boss, x, y)
        elif active_skill:
            _NS_nyxareth._draw_body_cast(surface, boss, x, y, pulse, active_skill)
        else:
            _NS_nyxareth._draw_body_idle(surface, boss, x, y)

        # Foreground skill FX.
        if active_skill == "1":
            _NS_nyxareth._draw_starsplit_fg(surface, boss, x, y,
                                              skill_timer, pulse)
        elif active_skill == "2":
            _NS_nyxareth._draw_realworld_fg(surface, boss, x, y,
                                              skill_timer, pulse)
        elif active_skill == "3":
            _NS_nyxareth._draw_spacetime_fg(surface, boss, x, y,
                                              skill_timer, pulse)
        elif active_skill == "4":
            _NS_nyxareth._draw_astro_realm_fg(surface, boss, x, y,
                                                skill_timer, pulse)

        # Basic attack projectile (star bolt).
        if attacking:
            _NS_nyxareth._draw_star_bolt(surface, boss, x, y)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_nxa_previous_timer", 0))
        active = bool(getattr(boss, "_nxa_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._nxa_attack_active = True
            boss._nxa_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._nxa_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._nxa_attack_frame = int(getattr(boss, "_nxa_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._nxa_attack_active = False
            boss._nxa_attack_frame = 0
            active = False

        boss._nxa_previous_timer = timer
        boss._nxa_attack_progress = (
            min(1.0, getattr(boss, "_nxa_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        # Slow floating bob.
        bob = int(math.sin(boss.pulse * 0.5) * 6)
        _NS_nyxareth._draw_shadow(surface, x, y + 55)
        _NS_nyxareth._draw_float_wisps(surface, x, y + 30, boss.pulse)
        _NS_nyxareth._draw_cosmic_body(surface, x, y + bob, boss.direction,
                                        boss.pulse, "idle")

    def _draw_body_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_nxa_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_nxa_attack_dir", None)
        if facing is None:
            facing = boss.direction
        bob = int(math.sin(boss.pulse * 0.5) * 5)
        _NS_nyxareth._draw_shadow(surface, x, y + 55)
        _NS_nyxareth._draw_float_wisps(surface, x, y + 30, boss.pulse,
                                        intense=True)
        _NS_nyxareth._draw_cosmic_body(surface, x, y + bob, facing,
                                        boss.pulse, "attack",
                                        getattr(boss, "_nxa_attack_progress", 0))

    def _draw_body_cast(surface, boss, x, y, pulse, skill):
        bob = int(math.sin(pulse * 0.5) * 4)
        # Slight rise when casting.
        lift = int(math.sin(pulse * 1.5) * 2) + 3
        _NS_nyxareth._draw_shadow(surface, x, y + 55)
        _NS_nyxareth._draw_float_wisps(surface, x, y + 30, pulse,
                                        intense=True)
        _NS_nyxareth._draw_cosmic_body(surface, x, y + bob - lift,
                                        boss.direction, pulse, "cast",
                                        skill=skill)

    # ============================================================
    # BODY (Floating cosmic mage - no legs, robe trails below)
    # ============================================================
    def _draw_cosmic_body(surface, cx, cy, facing, phase, action,
                          progress=0, skill=None):
        """Full cosmic mage: robe trail, torso, arms, orb, crown head."""
        # Order: robe trail (bottom), torso, back arm, front arm+orb, head+crown
        _NS_nyxareth._draw_robe_trail(surface, cx, cy, facing, phase)
        _NS_nyxareth._draw_cosmic_torso(surface, cx, cy, facing, phase, action)
        _NS_nyxareth._draw_shoulder_horns(surface, cx, cy, facing, phase)
        _NS_nyxareth._draw_back_arm_orb(surface, cx, cy, facing, phase, action,
                                          progress, skill)
        _NS_nyxareth._draw_front_arm(surface, cx, cy, facing, phase, action,
                                       progress)
        _NS_nyxareth._draw_crown_head(surface, cx, cy - 22, facing, phase, action)

    def _draw_robe_trail(surface, cx, cy, facing, phase):
        """Long flowing robe trailing below (no legs visible)."""
        sway = math.sin(phase * 0.4) * 3
        sway2 = math.sin(phase * 0.6 + 1) * 2

        # Main robe body extending down and out.
        robe_shape = [
            (cx - 14, cy + 10),
            (cx - 22, cy + 20),
            (cx - 28 + int(sway), cy + 32),
            (cx - 30 + int(sway), cy + 45),
            (cx - 24 + int(sway2), cy + 55),
            (cx - 12 + int(sway2), cy + 60),
            (cx, cy + 62),
            (cx + 12 + int(sway2), cy + 60),
            (cx + 24 + int(sway2), cy + 55),
            (cx + 30 + int(sway), cy + 45),
            (cx + 28 + int(sway), cy + 32),
            (cx + 22, cy + 20),
            (cx + 14, cy + 10),
        ]
        # Shadow.
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["shadow_deep"],
                            [(px + 3, py + 3) for px, py in robe_shape])
        # Base darkest.
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["void_darkest"],
                            robe_shape)
        # Inner shading.
        inner = [
            (cx - 12, cy + 12),
            (cx - 20, cy + 22),
            (cx - 26 + int(sway), cy + 32),
            (cx - 28 + int(sway), cy + 44),
            (cx - 22 + int(sway2), cy + 52),
            (cx - 10 + int(sway2), cy + 57),
            (cx, cy + 58),
            (cx + 10 + int(sway2), cy + 57),
            (cx + 22 + int(sway2), cy + 52),
            (cx + 28 + int(sway), cy + 44),
            (cx + 26 + int(sway), cy + 32),
            (cx + 20, cy + 22),
            (cx + 12, cy + 12),
        ]
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["robe_darkest"], inner)
        # Mid tone.
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["robe_dark"], [
            (cx - 10, cy + 14),
            (cx - 18, cy + 24),
            (cx - 22 + int(sway), cy + 34),
            (cx - 20 + int(sway2), cy + 48),
            (cx, cy + 52),
            (cx + 20 + int(sway2), cy + 48),
            (cx + 22 + int(sway), cy + 34),
            (cx + 18, cy + 24),
            (cx + 10, cy + 14),
        ])
        # Light streaks (fabric folds).
        for stripe_i, (start_ratio, end_ratio) in enumerate([
            (-0.7, -0.3), (0.3, 0.7), (0.0, 0.0),
        ]):
            top_x = cx + int(start_ratio * 12)
            bot_x = cx + int(end_ratio * 24) + int(sway)
            _NS_nyxareth._aaline(surface, _NS_nyxareth.PALETTE["robe_mid"],
                                  (top_x, cy + 14), (bot_x, cy + 45), 2)
            _NS_nyxareth._aaline(surface, _NS_nyxareth.PALETTE["robe_light"],
                                  (top_x, cy + 16), (bot_x - 1, cy + 40), 1)

        # Purple magic wisps at bottom edge.
        for i in range(8):
            t = (phase * 0.6 + i * 0.13) % 1.0
            wx = cx - 25 + i * 7 + int(math.sin(phase + i) * 3)
            wy = cy + 55 + int(t * 8)
            alpha = _NS_nyxareth._alpha(200 * (1 - t))
            _NS_nyxareth._aacircle(surface,
                                    (*_NS_nyxareth.PALETTE["cosmic_dark"], alpha),
                                    (wx, wy), 3)
            _NS_nyxareth._aacircle(surface,
                                    (*_NS_nyxareth.PALETTE["cosmic_mid"], alpha),
                                    (wx, wy - 1), 2)
            pygame.draw.rect(surface,
                             (*_NS_nyxareth.PALETTE["cosmic_light"], alpha),
                             (wx, wy - 1, 1, 1))

        # Gold trim at hem.
        for i in range(6):
            hem_x = cx - 22 + i * 9
            hem_y = cy + 52 + int(sway2 * 0.5)
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["gold_dark"],
                             (hem_x, hem_y, 2, 1))
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["gold_mid"],
                             (hem_x, hem_y, 1, 1))
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["gold_shine"],
                             (hem_x, hem_y, 1, 1))

    def _draw_cosmic_torso(surface, cx, cy, facing, phase, action):
        """Ornate armored torso (chest plate + robe collar)."""
        breath = math.sin(phase * 0.7) * 1

        # Torso silhouette (wider top, tapering to robe).
        torso_shape = [
            (cx - 12, cy - 8),
            (cx - 14, cy - 2),
            (cx - 13, cy + 5),
            (cx - 8, cy + 10),
            (cx + 8, cy + 10),
            (cx + 13, cy + 5),
            (cx + 14, cy - 2),
            (cx + 12, cy - 8),
            (cx + 6, cy - 12),
            (cx - 6, cy - 12),
        ]
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in torso_shape])
        # Base robe (dark).
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["robe_darkest"], torso_shape)
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["robe_dark"], [
            (cx - 11, cy - 6), (cx - 13, cy - 1),
            (cx - 12, cy + 4), (cx - 7, cy + 9),
            (cx + 7, cy + 9), (cx + 12, cy + 4),
            (cx + 13, cy - 1), (cx + 11, cy - 6),
            (cx + 5, cy - 11), (cx - 5, cy - 11),
        ])
        # Mid.
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["robe_mid"], [
            (cx - 9, cy - 4), (cx - 11, cy),
            (cx - 6, cy + 8), (cx + 6, cy + 8),
            (cx + 11, cy), (cx + 9, cy - 4),
            (cx + 4, cy - 9), (cx - 4, cy - 9),
        ])

        # Ornate GOLD CHEST PLATE (large decorative).
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["gold_darkest"], [
            (cx - 8, cy - 6), (cx + 8, cy - 6),
            (cx + 10, cy - 2), (cx + 8, cy + 3),
            (cx, cy + 6), (cx - 8, cy + 3),
            (cx - 10, cy - 2),
        ])
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["gold_dark"], [
            (cx - 7, cy - 5), (cx + 7, cy - 5),
            (cx + 9, cy - 2), (cx + 7, cy + 2),
            (cx, cy + 5), (cx - 7, cy + 2),
            (cx - 9, cy - 2),
        ])
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["gold_mid"], [
            (cx - 6, cy - 4), (cx + 6, cy - 4),
            (cx + 8, cy - 2), (cx + 6, cy + 1),
            (cx, cy + 4), (cx - 6, cy + 1),
            (cx - 8, cy - 2),
        ])
        # Gold decorative curls.
        pygame.draw.line(surface, _NS_nyxareth.PALETTE["gold_light"],
                         (cx - 6, cy - 3), (cx + 6, cy - 3), 1)
        pygame.draw.line(surface, _NS_nyxareth.PALETTE["gold_light"],
                         (cx - 5, cy + 2), (cx + 5, cy + 2), 1)
        # Center gem: PURPLE GALACTIC ORB embedded.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(5, 0, -1):
            alpha = _NS_nyxareth._alpha(200 * (5 - r) / 5 * pulse)
            _NS_nyxareth._aacircle(surface,
                                    (*_NS_nyxareth.PALETTE["cosmic_light"], alpha),
                                    (cx, cy - 1), r)
        pygame.draw.rect(surface, _NS_nyxareth.PALETTE["cosmic_darkest"],
                         (cx - 2, cy - 2, 4, 4))
        pygame.draw.rect(surface, _NS_nyxareth.PALETTE["cosmic_dark"],
                         (cx - 1, cy - 2, 3, 3))
        pygame.draw.rect(surface, _NS_nyxareth.PALETTE["cosmic_mid"],
                         (cx - 1, cy - 1, 2, 2))
        pygame.draw.rect(surface, _NS_nyxareth.PALETTE["cosmic_light"],
                         (cx, cy - 1, 1, 1))
        pygame.draw.rect(surface, _NS_nyxareth.PALETTE["cosmic_shine"],
                         (cx, cy - 1, 1, 1))

        # Ornate collar at neck (rising up).
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["robe_darkest"], [
            (cx - 8, cy - 10), (cx - 10, cy - 14),
            (cx - 6, cy - 16), (cx + 6, cy - 16),
            (cx + 10, cy - 14), (cx + 8, cy - 10),
        ])
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["robe_dark"], [
            (cx - 7, cy - 11), (cx - 9, cy - 14),
            (cx - 5, cy - 15), (cx + 5, cy - 15),
            (cx + 9, cy - 14), (cx + 7, cy - 11),
        ])
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["robe_mid"], [
            (cx - 6, cy - 12), (cx - 7, cy - 14),
            (cx + 7, cy - 14), (cx + 6, cy - 12),
        ])
        # Gold trim on collar.
        pygame.draw.line(surface, _NS_nyxareth.PALETTE["gold_mid"],
                         (cx - 8, cy - 14), (cx + 8, cy - 14), 1)
        pygame.draw.line(surface, _NS_nyxareth.PALETTE["gold_light"],
                         (cx - 7, cy - 15), (cx + 7, cy - 15), 1)

    def _draw_shoulder_horns(surface, cx, cy, facing, phase):
        """Curved horns/spikes on shoulders (like Yve's shoulder pieces)."""
        for side in [-1, 1]:
            shoulder_x = cx + side * 12
            shoulder_y = cy - 6

            # Big curving horn.
            sway = math.sin(phase * 0.4 + side) * 0.5
            horn_tip_x = shoulder_x + side * (10 + int(sway))
            horn_tip_y = shoulder_y - 12

            # Horn base.
            base_a = (shoulder_x + side * 2, shoulder_y - 2)
            base_b = (shoulder_x - side * 1, shoulder_y + 2)

            # Shadow.
            _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["shadow_deep"], [
                (horn_tip_x + 1, horn_tip_y + 1),
                (base_a[0] + 1, base_a[1] + 1),
                (base_b[0] + 1, base_b[1] + 1),
            ])
            # Horn body (dark purple).
            _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["void_darkest"], [
                (horn_tip_x, horn_tip_y), base_a, base_b,
            ])
            _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["robe_darkest"], [
                (horn_tip_x, horn_tip_y),
                (int((horn_tip_x + base_a[0]) / 2),
                 int((horn_tip_y + base_a[1]) / 2)),
                base_b,
            ])
            _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["robe_dark"], [
                (horn_tip_x, horn_tip_y),
                (int((horn_tip_x + base_a[0]) / 2 + side * 1),
                 int((horn_tip_y + base_a[1]) / 2)),
                (int((base_a[0] + base_b[0]) / 2),
                 int((base_a[1] + base_b[1]) / 2)),
            ])
            # Gold trim edge.
            pygame.draw.line(surface, _NS_nyxareth.PALETTE["gold_dark"],
                             (horn_tip_x, horn_tip_y), base_a, 1)
            pygame.draw.line(surface, _NS_nyxareth.PALETTE["gold_light"],
                             (horn_tip_x, horn_tip_y),
                             (int((horn_tip_x + base_a[0]) / 2),
                              int((horn_tip_y + base_a[1]) / 2)), 1)
            # Purple glow tip.
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["cosmic_light"],
                             (horn_tip_x, horn_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["cosmic_shine"],
                             (horn_tip_x, horn_tip_y, 1, 1))

    def _draw_back_arm_orb(surface, cx, cy, facing, phase, action, progress,
                            skill=None):
        """Back arm holding floating galactic orb."""
        shoulder_x = cx - facing * 6
        shoulder_y = cy - 4

        if action == "cast":
            # Arm extended outward with orb.
            elbow_x = shoulder_x - facing * 8
            elbow_y = shoulder_y + 4
            hand_x = shoulder_x - facing * 16
            hand_y = shoulder_y + 8
        else:
            sway = math.sin(phase * 0.5) * 1
            elbow_x = shoulder_x - facing * 6
            elbow_y = shoulder_y + 4 + int(sway)
            hand_x = shoulder_x - facing * 12
            hand_y = shoulder_y + 8 + int(sway)

        # Robe sleeve (long flowing).
        _NS_nyxareth._aaline(surface, _NS_nyxareth.PALETTE["shadow_deep"],
                              (shoulder_x + 2, shoulder_y + 2),
                              (elbow_x + 2, elbow_y + 2), 6)
        _NS_nyxareth._aaline(surface, _NS_nyxareth.PALETTE["robe_darkest"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_nyxareth._aaline(surface, _NS_nyxareth.PALETTE["robe_dark"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_nyxareth._aaline(surface, _NS_nyxareth.PALETTE["robe_mid"],
                              (shoulder_x, shoulder_y - 1),
                              (elbow_x, elbow_y - 1), 2)
        _NS_nyxareth._aaline(surface, _NS_nyxareth.PALETTE["robe_light"],
                              (shoulder_x, shoulder_y - 2),
                              (elbow_x, elbow_y - 2), 1)
        # Forearm sleeve (flared/wide).
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["robe_darkest"], [
            (elbow_x - 3, elbow_y - 2), (elbow_x + 3, elbow_y + 2),
            (hand_x + 5, hand_y + 4), (hand_x - 5, hand_y - 4),
        ])
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["robe_dark"], [
            (elbow_x - 2, elbow_y - 1), (elbow_x + 2, elbow_y + 1),
            (hand_x + 4, hand_y + 3), (hand_x - 4, hand_y - 3),
        ])
        # Gold cuff.
        pygame.draw.line(surface, _NS_nyxareth.PALETTE["gold_dark"],
                         (hand_x - 5, hand_y - 4), (hand_x + 5, hand_y + 4), 2)
        pygame.draw.line(surface, _NS_nyxareth.PALETTE["gold_mid"],
                         (hand_x - 4, hand_y - 3), (hand_x + 4, hand_y + 3), 1)
        # Hand (pale skin).
        _NS_nyxareth._aacircle(surface, _NS_nyxareth.PALETTE["skin_dark"],
                                (hand_x, hand_y), 3)
        _NS_nyxareth._aacircle(surface, _NS_nyxareth.PALETTE["skin_mid"],
                                (hand_x, hand_y), 2)

        # FLOATING GALACTIC ORB above hand.
        orb_x = hand_x - facing * 4
        orb_y = hand_y - 8 + int(math.sin(phase * 1.5) * 2)
        _NS_nyxareth._draw_galactic_orb(surface, orb_x, orb_y, phase,
                                          casting=(action == "cast"))

    def _draw_galactic_orb(surface, ox, oy, phase, casting=False):
        """Purple galactic orb with swirling stars."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        size_mult = 1.3 if casting else 1.0
        base_r = int(8 * size_mult)

        # Outer glow.
        for r in range(base_r + 8, 1, -1):
            alpha = _NS_nyxareth._alpha(120 * (base_r + 8 - r)
                                          / (base_r + 8) * pulse)
            _NS_nyxareth._aacircle(surface,
                                    (*_NS_nyxareth.PALETTE["cosmic_darkest"],
                                     alpha), (ox, oy), r)
        for r in range(base_r + 4, 1, -1):
            alpha = _NS_nyxareth._alpha(180 * (base_r + 4 - r)
                                          / (base_r + 4) * pulse)
            _NS_nyxareth._aacircle(surface,
                                    (*_NS_nyxareth.PALETTE["cosmic_dark"],
                                     alpha), (ox, oy), r)

        # Orb body.
        _NS_nyxareth._aacircle(surface, _NS_nyxareth.PALETTE["cosmic_darkest"],
                                (ox, oy), base_r)
        _NS_nyxareth._aacircle(surface, _NS_nyxareth.PALETTE["cosmic_dark"],
                                (ox, oy), base_r - 1)
        _NS_nyxareth._aacircle(surface, _NS_nyxareth.PALETTE["cosmic_mid"],
                                (ox, oy), base_r - 3)
        _NS_nyxareth._aacircle(surface, _NS_nyxareth.PALETTE["cosmic_light"],
                                (ox, oy), max(1, base_r - 5))

        # Bright core.
        _NS_nyxareth._aacircle(surface, _NS_nyxareth.PALETTE["cosmic_shine"],
                                (ox, oy), max(1, base_r - 6))
        pygame.draw.rect(surface, _NS_nyxareth.PALETTE["white"],
                         (ox, oy, 1, 1))

        # Swirling stars inside/around.
        for i in range(6):
            angle = phase * 2 + i * math.pi / 3
            r_dist = base_r + 2 + int(math.sin(phase + i) * 2)
            sx = ox + int(math.cos(angle) * r_dist)
            sy = oy + int(math.sin(angle) * r_dist)
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["star_bright"],
                             (sx, sy, 1, 1))

        # Orbital ring around orb.
        for i in range(12):
            angle = phase * 1.5 + i * math.pi / 6
            rx = ox + int(math.cos(angle) * (base_r + 3))
            ry = oy + int(math.sin(angle) * (base_r + 3) * 0.4)
            alpha = _NS_nyxareth._alpha(180 * pulse)
            pygame.draw.rect(surface,
                             (*_NS_nyxareth.PALETTE["cosmic_hot"], alpha),
                             (rx, ry, 1, 1))

    def _draw_front_arm(surface, cx, cy, facing, phase, action, progress):
        """Front arm - clawed/gesturing."""
        shoulder_x = cx + facing * 6
        shoulder_y = cy - 4

        if action == "attack":
            # Reach forward casting.
            elbow_x = shoulder_x + facing * 6
            elbow_y = shoulder_y + 2
            hand_x = shoulder_x + facing * 14
            hand_y = shoulder_y - 2
        elif action == "cast":
            elbow_x = shoulder_x + facing * 5
            elbow_y = shoulder_y - 2
            hand_x = shoulder_x + facing * 12
            hand_y = shoulder_y - 8
        else:
            sway = math.sin(phase * 0.5) * 1
            elbow_x = shoulder_x + facing * 4
            elbow_y = shoulder_y + 6 + int(sway)
            hand_x = shoulder_x + facing * 10
            hand_y = shoulder_y + 10 + int(sway)

        # Robe sleeve.
        _NS_nyxareth._aaline(surface, _NS_nyxareth.PALETTE["shadow_deep"],
                              (shoulder_x + 2, shoulder_y + 2),
                              (elbow_x + 2, elbow_y + 2), 5)
        _NS_nyxareth._aaline(surface, _NS_nyxareth.PALETTE["robe_darkest"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_nyxareth._aaline(surface, _NS_nyxareth.PALETTE["robe_dark"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_nyxareth._aaline(surface, _NS_nyxareth.PALETTE["robe_mid"],
                              (shoulder_x, shoulder_y - 1),
                              (elbow_x, elbow_y - 1), 1)

        # Flared sleeve at forearm.
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["robe_darkest"], [
            (elbow_x - 2, elbow_y - 2), (elbow_x + 2, elbow_y + 2),
            (hand_x + 4, hand_y + 3), (hand_x - 4, hand_y - 3),
        ])
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["robe_dark"], [
            (elbow_x - 1, elbow_y - 1), (elbow_x + 1, elbow_y + 1),
            (hand_x + 3, hand_y + 2), (hand_x - 3, hand_y - 2),
        ])
        # Gold cuff.
        pygame.draw.line(surface, _NS_nyxareth.PALETTE["gold_dark"],
                         (hand_x - 4, hand_y - 3), (hand_x + 4, hand_y + 3), 2)
        pygame.draw.line(surface, _NS_nyxareth.PALETTE["gold_mid"],
                         (hand_x - 3, hand_y - 2), (hand_x + 3, hand_y + 2), 1)

        # Claw-like hand.
        _NS_nyxareth._aacircle(surface, _NS_nyxareth.PALETTE["skin_dark"],
                                (hand_x, hand_y), 3)
        _NS_nyxareth._aacircle(surface, _NS_nyxareth.PALETTE["skin_mid"],
                                (hand_x, hand_y), 2)

        # Small purple energy at fingertips (mage aura).
        for finger_i in range(3):
            angle = -math.pi / 4 + finger_i * math.pi / 4
            fx = hand_x + int(math.cos(angle) * 3) * facing
            fy = hand_y + int(math.sin(angle) * 3)
            pulse = math.sin(phase * 3 + finger_i) * 0.3 + 0.7
            alpha = _NS_nyxareth._alpha(220 * pulse)
            _NS_nyxareth._aacircle(surface,
                                    (*_NS_nyxareth.PALETTE["cosmic_mid"], alpha),
                                    (fx, fy), 2)
            pygame.draw.rect(surface,
                             (*_NS_nyxareth.PALETTE["cosmic_light"], alpha),
                             (fx, fy, 1, 1))

    def _draw_crown_head(surface, cx, cy, facing, phase, action):
        """Head with tall spike crown headdress (SIGNATURE)."""
        head_cx = cx
        head_cy = cy

        # Face (shadowed, mostly obscured).
        face_shape = [
            (head_cx - 5, head_cy - 3), (head_cx - 6, head_cy + 1),
            (head_cx - 4, head_cy + 5), (head_cx - 1, head_cy + 7),
            (head_cx + 3, head_cy + 7), (head_cx + 5, head_cy + 5),
            (head_cx + 6, head_cy + 1), (head_cx + 5, head_cy - 3),
            (head_cx + 2, head_cy - 6), (head_cx - 2, head_cy - 6),
        ]
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in face_shape])
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["skin_darkest"], face_shape)
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["skin_dark"], [
            (head_cx - 4, head_cy - 2), (head_cx - 5, head_cy + 1),
            (head_cx - 3, head_cy + 4), (head_cx + 3, head_cy + 4),
            (head_cx + 5, head_cy + 1), (head_cx + 4, head_cy - 2),
            (head_cx + 2, head_cy - 5), (head_cx - 2, head_cy - 5),
        ])
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["skin_mid"], [
            (head_cx - 3, head_cy - 1), (head_cx - 4, head_cy + 1),
            (head_cx - 2, head_cy + 3), (head_cx + 2, head_cy + 3),
            (head_cx + 4, head_cy + 1), (head_cx + 3, head_cy - 1),
            (head_cx + 1, head_cy - 4), (head_cx - 1, head_cy - 4),
        ])
        # Cheek highlight.
        pygame.draw.rect(surface, _NS_nyxareth.PALETTE["skin_light"],
                         (head_cx - 1, head_cy + 1, 3, 2))
        pygame.draw.rect(surface, _NS_nyxareth.PALETTE["skin_shine"],
                         (head_cx, head_cy + 2, 1, 1))

        # GLOWING PURPLE EYES (menakutkan).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for ey_side in [-1, 1]:
            eye_x = head_cx + ey_side * 2
            eye_y = head_cy
            # Deep socket.
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["eye_dark"],
                             (eye_x - 1, eye_y - 1, 2, 2))
            # Glow.
            for r in range(3, 0, -1):
                alpha = _NS_nyxareth._alpha(180 * (3 - r) / 3 * pulse)
                _NS_nyxareth._aacircle(surface,
                                        (*_NS_nyxareth.PALETTE["eye_purple"],
                                         alpha), (eye_x, eye_y), r)
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["eye_purple"],
                             (eye_x, eye_y, 1, 1))
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["eye_shine"],
                             (eye_x, eye_y, 1, 1))

        # Mouth (grim/mysterious).
        pygame.draw.line(surface, _NS_nyxareth.PALETTE["skin_darkest"],
                         (head_cx - 2, head_cy + 5), (head_cx + 2, head_cy + 5), 1)

        # CROWN HEADDRESS BASE (dark purple with gold trim).
        crown_base = [
            (head_cx - 7, head_cy - 5), (head_cx + 7, head_cy - 5),
            (head_cx + 8, head_cy - 3), (head_cx - 8, head_cy - 3),
        ]
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["shadow_deep"],
                            [(px + 1, py + 1) for px, py in crown_base])
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["void_darkest"], crown_base)
        _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["robe_dark"], [
            (head_cx - 6, head_cy - 5), (head_cx + 6, head_cy - 5),
            (head_cx + 7, head_cy - 4), (head_cx - 7, head_cy - 4),
        ])
        pygame.draw.line(surface, _NS_nyxareth.PALETTE["gold_dark"],
                         (head_cx - 7, head_cy - 3), (head_cx + 7, head_cy - 3), 1)
        pygame.draw.line(surface, _NS_nyxareth.PALETTE["gold_light"],
                         (head_cx - 6, head_cy - 3), (head_cx + 6, head_cy - 3), 1)

        # TALL CROWN SPIKES (5 spikes, khas Yve).
        for i, (spike_off_x, spike_h) in enumerate([
            (-7, 10), (-4, 15), (0, 22), (4, 15), (7, 10),
        ]):
            sway = math.sin(phase * 0.4 + i * 0.5) * 0.7
            spike_x = head_cx + spike_off_x + int(sway)
            spike_base_y = head_cy - 5
            spike_tip_y = spike_base_y - spike_h

            spike_width = 2 if abs(spike_off_x) < 5 else 2

            # Shadow.
            _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_tip_y + 1),
                (spike_x - spike_width + 1, spike_base_y + 1),
                (spike_x + spike_width + 1, spike_base_y + 1),
            ])
            # Dark base.
            _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["void_darkest"], [
                (spike_x, spike_tip_y),
                (spike_x - spike_width, spike_base_y),
                (spike_x + spike_width, spike_base_y),
            ])
            _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["robe_darkest"], [
                (spike_x, spike_tip_y),
                (spike_x - spike_width + 1, spike_base_y),
                (spike_x + spike_width - 1, spike_base_y),
            ])
            _NS_nyxareth._poly(surface, _NS_nyxareth.PALETTE["robe_dark"], [
                (spike_x, spike_tip_y),
                (spike_x, spike_base_y),
                (spike_x + spike_width - 1, spike_base_y),
            ])
            # Bright edge.
            _NS_nyxareth._aaline(surface, _NS_nyxareth.PALETTE["gold_dark"],
                                  (spike_x, spike_tip_y),
                                  (spike_x - spike_width, spike_base_y), 1)
            # Purple glow tip.
            for gr in range(3, 0, -1):
                alpha = _NS_nyxareth._alpha(150 * (3 - gr) / 3)
                _NS_nyxareth._aacircle(surface,
                                        (*_NS_nyxareth.PALETTE["cosmic_light"],
                                         alpha), (spike_x, spike_tip_y), gr)
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["cosmic_shine"],
                             (spike_x, spike_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["white"],
                             (spike_x, spike_tip_y, 1, 1))

        # Gems along crown base.
        for gem_off_x in (-4, 0, 4):
            gx = head_cx + gem_off_x
            gy = head_cy - 4
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["cosmic_dark"],
                             (gx, gy, 2, 1))
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["cosmic_light"],
                             (gx, gy, 1, 1))
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["cosmic_shine"],
                             (gx, gy, 1, 1))

    # ============================================================
    # BASIC ATTACK STAR BOLT PROJECTILE
    # ============================================================
    def _draw_star_bolt(surface, boss, x, y):
        """Small star bolt projectile as basic attack."""
        progress = getattr(boss, "_nxa_attack_progress", 0)
        if progress < 0.5:
            return

        facing = boss.direction
        tx, ty = _NS_nyxareth._target_position(boss, x, y)

        # Launch from front hand.
        start_x = x + facing * 20
        start_y = y - 6

        t = (progress - 0.5) / 0.5
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Trail.
        for i in range(8):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_nyxareth._alpha(220 - i * 25)
            size = max(1, 6 - i)
            _NS_nyxareth._aacircle(surface,
                                    (*_NS_nyxareth.PALETTE["cosmic_darkest"], alpha),
                                    (px, py), size + 1)
            _NS_nyxareth._aacircle(surface,
                                    (*_NS_nyxareth.PALETTE["cosmic_dark"], alpha),
                                    (px, py), size)
            _NS_nyxareth._aacircle(surface,
                                    (*_NS_nyxareth.PALETTE["cosmic_mid"], alpha),
                                    (px, py), max(1, size - 2))
            _NS_nyxareth._aacircle(surface,
                                    (*_NS_nyxareth.PALETTE["cosmic_light"], alpha),
                                    (px, py), max(1, size - 3))

        # Star shape at head.
        for arm_i in range(4):
            arm_angle = arm_i * math.pi / 2 + t * math.pi
            for arm_len in (5, 8):
                ax = bx + int(math.cos(arm_angle) * arm_len)
                ay = by + int(math.sin(arm_angle) * arm_len)
                pygame.draw.rect(surface, _NS_nyxareth.PALETTE["cosmic_light"],
                                 (ax, ay, 1, 1))
                pygame.draw.rect(surface, _NS_nyxareth.PALETTE["cosmic_shine"],
                                 (ax, ay, 1, 1))
        # Bright core.
        for r in range(5, 0, -1):
            alpha = _NS_nyxareth._alpha(100 * (5 - r) / 5)
            _NS_nyxareth._aacircle(surface,
                                    (*_NS_nyxareth.PALETTE["cosmic_light"], alpha),
                                    (bx, by), r)
        _NS_nyxareth._aacircle(surface, _NS_nyxareth.PALETTE["cosmic_shine"],
                                (bx, by), 2)
        pygame.draw.rect(surface, _NS_nyxareth.PALETTE["white"], (bx, by, 1, 1))

        # Impact splash.
        if t > 0.9:
            st = (t - 0.9) / 0.1
            r = int(6 + st * 15)
            alpha = _NS_nyxareth._alpha(230 * (1 - st))
            _NS_nyxareth._aacircle(surface,
                                    (*_NS_nyxareth.PALETTE["cosmic_dark"], alpha),
                                    (tx, ty), r, 2)
            _NS_nyxareth._aacircle(surface,
                                    (*_NS_nyxareth.PALETTE["cosmic_light"], alpha),
                                    (tx, ty), max(1, r - 4), 1)

    # ============================================================
    # FLOAT WISPS (cosmic energy under body)
    # ============================================================
    def _draw_float_wisps(surface, cx, cy, phase, intense=False):
        strength = 1.5 if intense else 1.0

        # Cosmic energy pool below.
        pool = pygame.Surface((120, 30), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.3 + 0.7
        for r in range(24, 2, -2):
            alpha = _NS_nyxareth._alpha((24 - r) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(pool,
                                    (*_NS_nyxareth.PALETTE["cosmic_darkest"],
                                     alpha),
                                    (60 - r, 15 - r // 4,
                                     r * 2, max(2, r // 2)))
        for r in range(14, 1, -1):
            alpha = _NS_nyxareth._alpha((14 - r) * 5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(pool,
                                    (*_NS_nyxareth.PALETTE["cosmic_mid"], alpha),
                                    (60 - r, 15 - r // 4,
                                     r * 2, max(2, r // 3)))
        surface.blit(pool, (cx - 60, cy - 5))

        # Rising cosmic sparkles.
        for i in range(10):
            t = (phase * 0.5 + i * 0.11) % 1.0
            sx = cx - 25 + i * 5 + int(math.sin(phase + i) * 3)
            sy = cy + 12 - int(t * 30)
            alpha = _NS_nyxareth._alpha(230 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_nyxareth._aacircle(surface,
                                    (*_NS_nyxareth.PALETTE["cosmic_dark"], alpha),
                                    (sx, sy), 2)
            pygame.draw.rect(surface,
                             (*_NS_nyxareth.PALETTE["cosmic_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_nyxareth.PALETTE["star_bright"], alpha),
                             (sx, sy - 2, 1, 1))

    # ============================================================
    # AMBIENT (TRUE BOSS - bigger aura)
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((160, 34), pygame.SRCALPHA)
        for r in range(16, 0, -1):
            alpha = max(0, (16 - r) * 14)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - r, 17 - r,
                                 140 + r * 2, r * 2))
        pygame.draw.ellipse(shadow, (10, 5, 25, 170), (5, 10, 150, 14))
        pygame.draw.ellipse(shadow, (60, 20, 100, 110), (12, 12, 136, 10))
        surface.blit(shadow, (x - 80, y - 17))

    def _draw_cosmic_aura(surface, x, y, phase):
        """LARGE cosmic aura with nebula (TRUE BOSS)."""
        pulse = math.sin(phase * 0.4) * 0.3 + 0.7

        aura = pygame.Surface((280, 240), pygame.SRCALPHA)
        # Outermost nebula.
        for r in range(120, 5, -6):
            alpha = _NS_nyxareth._alpha((120 - r) * 0.9 * pulse)
            if alpha > 0:
                _NS_nyxareth._aacircle(aura,
                                        (*_NS_nyxareth.PALETTE["nebula_dark"],
                                         alpha), (140, 120), r)
        for r in range(80, 5, -5):
            alpha = _NS_nyxareth._alpha((80 - r) * 1.2 * pulse)
            if alpha > 0:
                _NS_nyxareth._aacircle(aura,
                                        (*_NS_nyxareth.PALETTE["cosmic_darkest"],
                                         alpha), (140, 120), r)
        for r in range(50, 5, -4):
            alpha = _NS_nyxareth._alpha((50 - r) * 1.5 * pulse)
            if alpha > 0:
                _NS_nyxareth._aacircle(aura,
                                        (*_NS_nyxareth.PALETTE["cosmic_dark"],
                                         alpha), (140, 120), r)
        # Pink nebula accent.
        for r in range(35, 5, -3):
            alpha = _NS_nyxareth._alpha((35 - r) * 1.2 * pulse)
            if alpha > 0:
                _NS_nyxareth._aacircle(aura,
                                        (*_NS_nyxareth.PALETTE["nebula_pink"],
                                         alpha // 2), (140, 120), r)
        surface.blit(aura, (x - 140, y - 120))

        # Stars orbiting.
        for i in range(20):
            angle = phase * 0.2 + i * math.pi / 10
            radius = 60 + int(math.sin(phase + i) * 20)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.5)
            # Varying star sizes.
            if i % 4 == 0:
                pygame.draw.rect(surface, _NS_nyxareth.PALETTE["star_bright"],
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_nyxareth.PALETTE["star_bright"],
                                 (sx - 1, sy, 1, 1))
                pygame.draw.rect(surface, _NS_nyxareth.PALETTE["star_bright"],
                                 (sx + 2, sy, 1, 1))
                pygame.draw.rect(surface, _NS_nyxareth.PALETTE["star_bright"],
                                 (sx, sy - 1, 1, 1))
                pygame.draw.rect(surface, _NS_nyxareth.PALETTE["star_bright"],
                                 (sx, sy + 2, 1, 1))
            else:
                pygame.draw.rect(surface, _NS_nyxareth.PALETTE["star_mid"],
                                 (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """LARGE ground rune circle (true boss)."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((200, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring,
                            (*_NS_nyxareth.PALETTE["rune_dark"], 200),
                            (5, 20, 190, 28), 3)
        pygame.draw.ellipse(ring,
                            (*_NS_nyxareth.PALETTE["cosmic_darkest"], 220),
                            (14, 22, 172, 24), 2)
        pygame.draw.ellipse(ring,
                            (*_NS_nyxareth.PALETTE["cosmic_dark"], 230),
                            (25, 24, 150, 20), 1)

        # Rune marks.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 100 + int(math.cos(angle) * 55)
            y1 = 34 + int(math.sin(angle) * 8)
            x2 = 100 + int(math.cos(angle) * 85)
            y2 = 34 + int(math.sin(angle) * 13)
            pygame.draw.line(ring,
                             (*_NS_nyxareth.PALETTE["cosmic_light"], 220),
                             (x1, y1), (x2, y2), 1)

        # Stars in ring.
        for i in range(8):
            angle = phase * 0.5 + i * math.pi / 4
            sx = 100 + int(math.cos(angle) * 70)
            sy = 34 + int(math.sin(angle) * 10)
            pygame.draw.rect(ring, (*_NS_nyxareth.PALETTE["star_bright"], 220),
                             (sx, sy, 1, 1))

        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_nyxareth.PALETTE["cosmic_hot"],
                                 _NS_nyxareth._alpha(150 * pulse)),
                                (15, 14, 170, 40), 1)
        surface.blit(ring, (x - 100, y - 30))

    # ============================================================
    # SKILL 1: STARSPLIT (beam with starfield)
    # ============================================================
    def _draw_starsplit_ground(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.3:
            return

        # Beam path warning line.
        t = (progress - 0.3) / 0.7
        beam_length = int(200 * t)
        start_x = x + facing * 20
        end_x = start_x + facing * beam_length
        beam_y = y + 40

        alpha = _NS_nyxareth._alpha(180 * (1 - t * 0.4))
        # Path glow rectangle.
        beam_left = min(start_x, end_x)
        beam_w = abs(end_x - start_x)
        if beam_w > 5:
            pygame.draw.ellipse(surface,
                                (*_NS_nyxareth.PALETTE["cosmic_dark"], alpha),
                                (beam_left, beam_y - 8, beam_w, 16))
            pygame.draw.ellipse(surface,
                                (*_NS_nyxareth.PALETTE["cosmic_mid"], alpha),
                                (beam_left + 4, beam_y - 5, beam_w - 8, 10))

    def _draw_starsplit_fg(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Charge phase.
        if progress < 0.3:
            t = progress / 0.3
            hx = x + facing * 20
            hy = y - 6
            cr = int(3 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_nyxareth._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_nyxareth._aacircle(surface,
                                        (*_NS_nyxareth.PALETTE["cosmic_dark"],
                                         alpha), (hx, hy), r)
            _NS_nyxareth._aacircle(surface, _NS_nyxareth.PALETTE["cosmic_light"],
                                    (hx, hy), max(1, cr - 3))
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["cosmic_shine"],
                             (hx, hy, 1, 1))
        else:
            # BEAM SPLIT with starfield.
            t = (progress - 0.3) / 0.7
            intensity = math.sin(t * math.pi)
            beam_length = int(200 * t)
            start_x = x + facing * 20
            end_x = start_x + facing * beam_length
            beam_y = y - 6

            # Multi-layer beam.
            for layer_i, (width, color) in enumerate([
                (10, _NS_nyxareth.PALETTE["cosmic_darkest"]),
                (7, _NS_nyxareth.PALETTE["cosmic_dark"]),
                (5, _NS_nyxareth.PALETTE["cosmic_mid"]),
                (3, _NS_nyxareth.PALETTE["cosmic_light"]),
                (1, _NS_nyxareth.PALETTE["cosmic_shine"]),
            ]):
                alpha = _NS_nyxareth._alpha(240 * intensity)
                beam_left = min(start_x, end_x)
                pygame.draw.rect(surface, (*color, alpha),
                                 (beam_left, beam_y - width // 2,
                                  abs(end_x - start_x), width))

            # Star spikes along beam (radiating perpendicular).
            num_stars = 8
            for i in range(num_stars):
                star_x = start_x + facing * int((i + 1) / num_stars * beam_length)
                # Perpendicular star spikes.
                for arm in range(4):
                    arm_angle = arm * math.pi / 2 + phase
                    arm_len = 6
                    ax = star_x + int(math.cos(arm_angle) * arm_len)
                    ay = beam_y + int(math.sin(arm_angle) * arm_len)
                    alpha = _NS_nyxareth._alpha(240 * intensity)
                    _NS_nyxareth._aaline(surface,
                                          (*_NS_nyxareth.PALETTE["cosmic_light"],
                                           alpha),
                                          (star_x, beam_y), (ax, ay), 1)
                # Star bright center.
                pygame.draw.rect(surface,
                                 (*_NS_nyxareth.PALETTE["star_bright"],
                                  _NS_nyxareth._alpha(255 * intensity)),
                                 (star_x, beam_y, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_nyxareth.PALETTE["white"],
                                  _NS_nyxareth._alpha(255 * intensity)),
                                 (star_x, beam_y, 1, 1))

            # End impact.
            end_r = int(15 + t * 10)
            end_alpha = _NS_nyxareth._alpha(255 * intensity)
            _NS_nyxareth._aacircle(surface,
                                    (*_NS_nyxareth.PALETTE["cosmic_dark"],
                                     end_alpha), (end_x, beam_y), end_r, 2)
            _NS_nyxareth._aacircle(surface,
                                    (*_NS_nyxareth.PALETTE["cosmic_light"],
                                     end_alpha), (end_x, beam_y),
                                    max(1, end_r // 2))

    # ============================================================
    # SKILL 2: REAL WORLD MANIPULATION (control area with orbit rings)
    # ============================================================
    def _draw_realworld_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_nyxareth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        r = int(55 * min(1.0, progress * 2.5))
        if r < 5:
            return

        # Ground area (translucent purple pool).
        alpha = _NS_nyxareth._alpha(180 * (1 - progress * 0.3))
        pygame.draw.ellipse(surface,
                            (*_NS_nyxareth.PALETTE["cosmic_darkest"], alpha),
                            (tx - r, ty - r // 3,
                             r * 2, r * 2 // 3))
        pygame.draw.ellipse(surface,
                            (*_NS_nyxareth.PALETTE["cosmic_dark"], alpha),
                            (tx - r + 3, ty - r // 3 + 2,
                             r * 2 - 6, r * 2 // 3 - 4))
        pygame.draw.ellipse(surface,
                            (*_NS_nyxareth.PALETTE["cosmic_mid"], alpha // 2),
                            (tx - r + 8, ty - r // 3 + 4,
                             r * 2 - 16, r * 2 // 3 - 8))

    def _draw_realworld_fg(surface, boss, x, y, timer, phase):
        tx, ty = _NS_nyxareth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(55 * min(1.0, progress * 2.5))

        if r < 5:
            return

        # Orbiting rings (like Saturn - khas skill icon).
        for ring_i, (ring_r, ring_tilt, ring_speed) in enumerate([
            (r, 0.3, 1.0), (int(r * 0.7), -0.4, 1.5), (int(r * 0.5), 0.5, 2.0),
        ]):
            # Draw ellipse ring at angle.
            alpha = _NS_nyxareth._alpha(220 * (1 - progress * 0.3))
            for edge in range(2):
                pygame.draw.ellipse(surface,
                                    (*_NS_nyxareth.PALETTE["cosmic_dark"],
                                     alpha - edge * 40),
                                    (tx - ring_r, ty - int(ring_r * ring_tilt),
                                     ring_r * 2, int(ring_r * ring_tilt * 2)
                                     if ring_tilt > 0 else int(-ring_r * ring_tilt * 2)),
                                    2 - edge)
            # Bright orbit particles.
            for orbit_i in range(8):
                orb_angle = phase * ring_speed + orbit_i * math.pi / 4
                ox = tx + int(math.cos(orb_angle) * ring_r)
                oy = ty + int(math.sin(orb_angle) * ring_r * ring_tilt)
                pygame.draw.rect(surface,
                                 (*_NS_nyxareth.PALETTE["cosmic_hot"], alpha),
                                 (ox, oy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_nyxareth.PALETTE["star_bright"], alpha),
                                 (ox, oy, 1, 1))

        # Stars scattered inside area.
        for i in range(15):
            angle = i * math.pi * 2 / 15 + phase * 0.5
            dist = int(r * (0.3 + (i % 3) * 0.25))
            sx = tx + int(math.cos(angle) * dist)
            sy = ty + int(math.sin(angle) * dist * 0.5)
            pulse = math.sin(phase * 2 + i) * 0.5 + 0.5
            alpha = _NS_nyxareth._alpha(230 * pulse)
            if i % 3 == 0:
                # Big star.
                pygame.draw.rect(surface,
                                 (*_NS_nyxareth.PALETTE["star_bright"], alpha),
                                 (sx, sy, 2, 2))
                for arm_a in (0, math.pi / 2):
                    ax = sx + int(math.cos(arm_a) * 2)
                    ay = sy + int(math.sin(arm_a) * 2)
                    pygame.draw.rect(surface,
                                     (*_NS_nyxareth.PALETTE["star_bright"],
                                      alpha), (ax, ay, 1, 1))
            else:
                pygame.draw.rect(surface,
                                 (*_NS_nyxareth.PALETTE["star_mid"], alpha),
                                 (sx, sy, 1, 1))

    # ============================================================
    # SKILL 3: SPACE TIME FUSION (black hole)
    # ============================================================
    def _draw_spacetime_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_nyxareth._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Growing black hole shadow.
        r = int(35 * min(1.0, progress * 2))
        if r < 3:
            return

        alpha = _NS_nyxareth._alpha(240)
        # Deep dark center.
        pygame.draw.ellipse(surface,
                            (*_NS_nyxareth.PALETTE["shadow_deep"], alpha),
                            (tx - r, ty - r // 3,
                             r * 2, r * 2 // 3))

    def _draw_spacetime_fg(surface, boss, x, y, timer, phase):
        tx, ty = _NS_nyxareth._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        r = int(35 * min(1.0, progress * 2))
        if r < 3:
            return

        # Explosion at end.
        if progress > 0.85:
            explode_t = (progress - 0.85) / 0.15
            explode_r = int(r + explode_t * 40)
            for exp_layer in range(4):
                exp_alpha = _NS_nyxareth._alpha(255 * (1 - explode_t)
                                                  - exp_layer * 40)
                if exp_alpha <= 0:
                    continue
                _NS_nyxareth._aacircle(surface,
                                        (*_NS_nyxareth.PALETTE["cosmic_light"],
                                         exp_alpha), (tx, ty),
                                        explode_r - exp_layer * 3, 2)
            return

        # BLACK HOLE with swirling accretion disk.
        # Center: pure black.
        _NS_nyxareth._aacircle(surface, _NS_nyxareth.PALETTE["shadow_deep"],
                                (tx, ty), r)
        _NS_nyxareth._aacircle(surface, _NS_nyxareth.PALETTE["void_darkest"],
                                (tx, ty), r - 2)

        # Event horizon (bright ring).
        for ring_r in (r, r + 2, r + 4):
            alpha = _NS_nyxareth._alpha(220 - (ring_r - r) * 30)
            _NS_nyxareth._aacircle(surface,
                                    (*_NS_nyxareth.PALETTE["cosmic_light"],
                                     alpha), (tx, ty), ring_r, 1)

        # Swirling accretion (spiral arms).
        for arm_i in range(3):
            arm_start_angle = arm_i * math.pi * 2 / 3 + phase * 3
            for spiral_i in range(15):
                spiral_t = spiral_i / 14
                spiral_angle = arm_start_angle + spiral_t * math.pi * 1.5
                spiral_r = r + 2 + int(spiral_t * 20)
                sx = tx + int(math.cos(spiral_angle) * spiral_r)
                sy = ty + int(math.sin(spiral_angle) * spiral_r * 0.5)
                alpha = _NS_nyxareth._alpha(220 * (1 - spiral_t * 0.6))
                color = _NS_nyxareth.PALETTE["cosmic_hot"] if spiral_t < 0.3 \
                    else _NS_nyxareth.PALETTE["cosmic_mid"]
                size = max(1, 3 - spiral_i // 5)
                _NS_nyxareth._aacircle(surface, (*color, alpha), (sx, sy), size)
                pygame.draw.rect(surface,
                                 (*_NS_nyxareth.PALETTE["star_bright"], alpha),
                                 (sx, sy, 1, 1))

        # Particles being sucked in.
        for i in range(8):
            pull_t = (phase * 0.8 + i * 0.13) % 1.0
            pull_angle = i * math.pi / 4
            pull_r = int((1 - pull_t) * (r + 40) + pull_t * r)
            px = tx + int(math.cos(pull_angle) * pull_r)
            py = ty + int(math.sin(pull_angle) * pull_r * 0.6)
            alpha = _NS_nyxareth._alpha(220 * pull_t)
            pygame.draw.rect(surface,
                             (*_NS_nyxareth.PALETTE["star_bright"], alpha),
                             (px, py, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_nyxareth.PALETTE["cosmic_hot"], alpha),
                             (px, py, 1, 1))

    # ============================================================
    # SKILL 4: ASTRO REALM (ULTIMATE - covers screen with cosmic dome)
    # ============================================================
    def _draw_astro_realm_bg(surface, boss, x, y, timer, phase):
        """Background layer of ultimate - covers entire screen."""
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        w, h = surface.get_size()

        # Growing cosmic dome (rectangle covering more area).
        alpha_base = _NS_nyxareth._alpha(80 * min(1.0, progress * 3))

        # Deep cosmic layer.
        cosmic_layer = pygame.Surface((w, h), pygame.SRCALPHA)
        cosmic_layer.fill((*_NS_nyxareth.PALETTE["cosmic_darkest"], alpha_base))
        surface.blit(cosmic_layer, (0, 0))

        # Stars all over screen.
        num_stars = 60
        for i in range(num_stars):
            # Pseudo-random star positions based on i.
            sx = int((i * 37 + phase * 5) % w)
            sy = int((i * 71 + phase * 3) % h)
            twinkle = math.sin(phase * 3 + i) * 0.5 + 0.5
            alpha = _NS_nyxareth._alpha(230 * twinkle * min(1.0, progress * 2))

            if i % 5 == 0:
                # Big star with cross.
                pygame.draw.rect(surface,
                                 (*_NS_nyxareth.PALETTE["star_bright"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_nyxareth.PALETTE["star_bright"], alpha),
                                 (sx - 1, sy, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_nyxareth.PALETTE["star_bright"], alpha),
                                 (sx + 2, sy, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_nyxareth.PALETTE["star_bright"], alpha),
                                 (sx, sy - 1, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_nyxareth.PALETTE["star_bright"], alpha),
                                 (sx, sy + 2, 1, 1))
            else:
                pygame.draw.rect(surface,
                                 (*_NS_nyxareth.PALETTE["star_mid"], alpha),
                                 (sx, sy, 1, 1))

    def _draw_astro_realm_fg(surface, boss, x, y, timer, phase):
        """Foreground layer of ultimate."""
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # BIG rune circle expanding around boss.
        r = int(80 + min(1.0, progress * 2) * 60)
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Multiple concentric rings.
        for ring_i, ring_scale in enumerate([1.0, 0.75, 0.5, 0.25]):
            ring_r = int(r * ring_scale)
            alpha = _NS_nyxareth._alpha(230 * pulse * (1 - progress * 0.3))
            pygame.draw.ellipse(surface,
                                (*_NS_nyxareth.PALETTE["cosmic_dark"], alpha),
                                (x - ring_r, y - ring_r // 3,
                                 ring_r * 2, ring_r * 2 // 3), 2)
            pygame.draw.ellipse(surface,
                                (*_NS_nyxareth.PALETTE["cosmic_mid"], alpha),
                                (x - ring_r + 2, y - ring_r // 3 + 1,
                                 ring_r * 2 - 4, ring_r * 2 // 3 - 2), 1)

        # Rotating rune segments on outer ring.
        num_runes = 12
        for i in range(num_runes):
            angle = phase * 0.5 + i * math.pi * 2 / num_runes
            rx = x + int(math.cos(angle) * r)
            ry = y + int(math.sin(angle) * r * 0.4)
            # Small rune mark.
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["cosmic_hot"],
                             (rx - 1, ry - 1, 3, 3))
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["cosmic_shine"],
                             (rx, ry, 1, 1))
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["white"],
                             (rx, ry, 1, 1))

        # Connecting lines from center to runes (like magic circle).
        for i in range(num_runes):
            angle = phase * 0.5 + i * math.pi * 2 / num_runes
            rx = x + int(math.cos(angle) * r)
            ry = y + int(math.sin(angle) * r * 0.4)
            alpha = _NS_nyxareth._alpha(120 * pulse)
            _NS_nyxareth._aaline(surface,
                                  (*_NS_nyxareth.PALETTE["cosmic_light"], alpha),
                                  (x, y), (rx, ry), 1)

        # Cosmic energy pillars rising from ring points.
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            pillar_x = x + int(math.cos(angle) * (r * 0.7))
            pillar_y = y + int(math.sin(angle) * (r * 0.7) * 0.4)
            pillar_h = int(30 + math.sin(phase * 2 + i) * 10)
            for layer in range(4):
                width = 6 - layer * 1
                alpha = _NS_nyxareth._alpha(180 * pulse)
                pygame.draw.rect(surface,
                                 (*_NS_nyxareth.PALETTE["cosmic_mid"], alpha),
                                 (pillar_x - width // 2, pillar_y - pillar_h,
                                  width, pillar_h))
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["cosmic_shine"],
                             (pillar_x, pillar_y - pillar_h, 1, 1))
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["star_bright"],
                             (pillar_x, pillar_y - pillar_h, 1, 1))

        # Central bright core.
        if progress < 0.9:
            core_r = int(15 + math.sin(phase * 2) * 5)
            for cr in range(core_r + 5, 0, -1):
                alpha = _NS_nyxareth._alpha(180 * (core_r + 5 - cr)
                                              / (core_r + 5) * pulse)
                _NS_nyxareth._aacircle(surface,
                                        (*_NS_nyxareth.PALETTE["cosmic_light"],
                                         alpha), (x, y), cr)
            _NS_nyxareth._aacircle(surface, _NS_nyxareth.PALETTE["cosmic_shine"],
                                    (x, y), 5)
            pygame.draw.rect(surface, _NS_nyxareth.PALETTE["white"],
                             (x, y, 1, 1))


# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_kaelthorn(surface, boss, x, y):
    """Entry point kaelthorn."""
    return _NS_kaelthorn.draw_kaelthorn(surface, boss, x, y)


def draw_solvanth(surface, boss, x, y):
    """Entry point solvanth."""
    return _NS_solvanth.draw_solvanth(surface, boss, x, y)


def draw_xyrael(surface, boss, x, y):
    """Entry point xyrael."""
    return _NS_xyrael.draw_xyrael(surface, boss, x, y)


def draw_nyxareth(surface, boss, x, y):
    """Entry point nyxareth."""
    return _NS_nyxareth.draw_nyxareth(surface, boss, x, y)
