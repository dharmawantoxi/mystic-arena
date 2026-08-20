"""
bosses/level20.py - Semua boss Level 20

Berisi:
  - astraelion   (mini boss - MELEE starlight swordmaster assassin)
  - morvaenthir  (mini boss - RANGED soul reaper necromancer)
  - thornvaegrim (mini boss - MELEE twisted elderwood treant tank)
  - morthraxis   (TRUE BOSS - Crimson Sovereign, RANGED vampire)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _mor_ (morvaenthir) di-rename -> _mvt_ (bentrok dengan Morgath
    level lama) - termasuk atribut _last_x/_last_y.
  - _ast_ (astraelion), _thn_ (thornvaegrim), _mrx_ (morthraxis)
    sudah unik. Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True



# ====================================================================
# astraelion.py
# ====================================================================

# ====================================================================
# ASTRAELION - The Starlight Swordmaster (Mini Boss - Assassin)
# ====================================================================


class _NS_astraelion:
    """Namespace astraelion - Cosmic swordmaster assassin mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin (young noble)
        "skin_darkest": (130, 90, 75),
        "skin_dark": (200, 155, 130),
        "skin_mid": (240, 205, 180),
        "skin_light": (255, 230, 210),
        "skin_shine": (255, 245, 230),

        # Blonde hair
        "hair_darkest": (65, 40, 15),
        "hair_dark": (130, 90, 30),
        "hair_mid": (210, 160, 55),
        "hair_light": (250, 220, 130),
        "hair_shine": (255, 250, 200),

        # Navy/dark blue armor base
        "armor_darkest": (5, 10, 22),
        "armor_dark": (18, 28, 55),
        "armor_mid": (45, 65, 105),
        "armor_light": (90, 120, 175),
        "armor_edge": (150, 185, 235),
        "armor_shine": (210, 230, 255),

        # Silver plate (helmet/pauldrons)
        "silver_darkest": (18, 22, 35),
        "silver_dark": (55, 65, 85),
        "silver_mid": (115, 130, 155),
        "silver_light": (180, 195, 220),
        "silver_shine": (240, 245, 255),

        # Violet/purple magic (main energy)
        "violet_darkest": (25, 8, 55),
        "violet_dark": (75, 30, 145),
        "violet_mid": (145, 75, 225),
        "violet_light": (210, 155, 255),
        "violet_hot": (240, 200, 255),
        "violet_shine": (250, 235, 255),

        # Cyan-blue (eyes, energy accent)
        "cyan_dark": (10, 60, 130),
        "cyan_mid": (60, 155, 240),
        "cyan_light": (170, 220, 255),
        "cyan_glow": (230, 245, 255),

        # Gold trim accents
        "gold_dark": (95, 65, 25),
        "gold_mid": (200, 155, 65),
        "gold_light": (250, 220, 130),
        "gold_shine": (255, 245, 200),

        # Sword blade (crystalline violet-white)
        "blade_darkest": (30, 15, 60),
        "blade_dark": (80, 55, 150),
        "blade_mid": (150, 110, 230),
        "blade_light": (220, 180, 255),
        "blade_shine": (250, 240, 255),

        # Mist
        "mist_dark": (18, 8, 40),
        "mist_mid": (70, 35, 130),
        "mist_light": (170, 120, 230),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 5),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_astraelion._clamp(color)
        if _NS_astraelion.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_astraelion._clamp(color)
        if _NS_astraelion.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        pygame.draw.polygon(surface, _NS_astraelion._clamp(color), points)

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
        return int(x + 180 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_astraelion(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_astraelion._detect_moving(boss)
        _NS_astraelion._update_ast_attack_anim(boss)
        attacking = (
            getattr(boss, "_ast_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_astraelion._draw_star_aura(surface, x, y, pulse)
        _NS_astraelion._draw_ground_ring(surface, x, y + 52, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "e":
            _NS_astraelion._draw_forceescape_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_astraelion._draw_zeroreturn_ground(surface, boss, x, y, skill_timer, pulse)

        # Body (floating).
        if attacking:
            _NS_astraelion._draw_ast_attack(surface, boss, x, y)
        elif moving:
            _NS_astraelion._draw_ast_float_move(surface, boss, x, y)
        else:
            _NS_astraelion._draw_ast_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_astraelion._draw_swordfall(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_astraelion._draw_spiritblade(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_astraelion._draw_forceescape_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_astraelion._draw_zeroreturn_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_ast_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_ast_previous_timer", 0))
        active = bool(getattr(boss, "_ast_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._ast_attack_active = True
            boss._ast_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._ast_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._ast_attack_frame = int(
                getattr(boss, "_ast_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._ast_attack_active = False
            boss._ast_attack_frame = 0
            active = False

        boss._ast_previous_timer = timer
        boss._ast_attack_progress = (
            min(1.0, getattr(boss, "_ast_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_ast_last_x"):
            boss._ast_last_x = boss.x
            boss._ast_last_y = boss.y
            return False
        dx = abs(boss.x - boss._ast_last_x)
        dy = abs(boss.y - boss._ast_last_y)
        boss._ast_last_x = boss.x
        boss._ast_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS (FLOATING)
    # ============================================================
    def _draw_ast_idle(surface, boss, x, y):
        float_bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_astraelion._draw_shadow(surface, x, y + 52)
        _NS_astraelion._draw_star_particles(surface, x, y + 42, boss.pulse)
        _NS_astraelion._draw_ast_body(surface, x, y - 5 + float_bob,
                                      boss.direction, boss.pulse, "idle", 0)

    def _draw_ast_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.5
        float_bob = int(math.sin(phase * 0.9) * 5)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_astraelion._draw_shadow(surface, x + sway, y + 52)
        _NS_astraelion._draw_star_particles(surface, x + sway, y + 42, phase,
                                            trail=True, facing=boss.direction)
        _NS_astraelion._draw_ast_body(surface, x + sway, y - 7 + float_bob,
                                      boss.direction, phase, "move", 0)

    def _draw_ast_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_ast_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_ast_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Melee sword slash: wind-up → slash → recovery
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 4) * facing
            lift = int(t * 3)
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            lunge = int((-4 + t * 14)) * facing
            lift = int(3 - t * 6)
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(10 * (1 - t)) * facing
            lift = int(-3 + t * 3)

        float_bob = int(math.sin(boss.pulse * 0.5) * 3)
        _NS_astraelion._draw_shadow(surface, x + lunge, y + 52)
        _NS_astraelion._draw_star_particles(surface, x + lunge, y + 42, boss.pulse,
                                            intense=True)
        _NS_astraelion._draw_ast_body(surface, x + lunge, y - 5 - lift + float_bob,
                                      facing, boss.pulse, "attack", progress)

    # ============================================================
    # BODY (Noble swordmaster with sword, cape, armor)
    # ============================================================
    def _draw_ast_body(surface, cx, cy, facing, phase, action, attack_progress):
        """Draw noble swordmaster body."""
        # Cape flowing behind FIRST.
        _NS_astraelion._draw_flowing_cape(surface, cx, cy, facing, phase)

        # Robe tatters below (floating - no legs).
        _NS_astraelion._draw_robe_bottom(surface, cx, cy + 8, facing, phase)

        # Torso armor.
        _NS_astraelion._draw_ast_torso(surface, cx, cy, facing, phase)

        # Pauldrons.
        _NS_astraelion._draw_pauldrons(surface, cx, cy - 4, facing, phase)

        # Back arm.
        _NS_astraelion._draw_ast_arm_back(surface, cx, cy + 2, facing, phase,
                                          action, attack_progress)

        # Head + hair.
        _NS_astraelion._draw_ast_head(surface, cx, cy - 14, facing, phase)

        # Front arm with sword.
        _NS_astraelion._draw_ast_arm_front(surface, cx, cy + 2, facing, phase,
                                           action, attack_progress)

        # SWORD (energy sword - drawn last for foreground).
        _NS_astraelion._draw_energy_sword(surface, cx, cy, facing, phase, action,
                                          attack_progress)

    def _draw_flowing_cape(surface, cx, cy, facing, phase):
        """Violet-blue cape flowing behind."""
        sway = math.sin(phase * 0.5) * 3
        back_dir = -facing

        # Cape silhouette.
        cape_points = [
            (cx + back_dir * 6, cy - 6),
            (cx + back_dir * 10, cy - 2),
            (cx + back_dir * 14, cy + 4),
            (cx + back_dir * 16 + int(sway), cy + 10),
            (cx + back_dir * 14 + int(sway * 1.3), cy + 16),
            (cx + back_dir * 10 + int(sway), cy + 20),
            (cx + back_dir * 4, cy + 18),
            (cx + back_dir * 2, cy + 10),
            (cx, cy + 2),
        ]
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in cape_points])
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["armor_darkest"], cape_points)

        # Layered cape (dark navy).
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["armor_dark"], [
            (cx + back_dir * 6, cy - 5),
            (cx + back_dir * 9, cy - 1),
            (cx + back_dir * 13, cy + 4),
            (cx + back_dir * 14 + int(sway), cy + 9),
            (cx + back_dir * 12 + int(sway), cy + 15),
            (cx + back_dir * 8, cy + 18),
            (cx + back_dir * 3, cy + 15),
            (cx + back_dir * 1, cy + 8),
            (cx, cy + 3),
        ])
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["armor_mid"], [
            (cx + back_dir * 7, cy - 3),
            (cx + back_dir * 10, cy + 2),
            (cx + back_dir * 12, cy + 8),
            (cx + back_dir * 10 + int(sway), cy + 14),
            (cx + back_dir * 6, cy + 15),
            (cx + back_dir * 3, cy + 10),
            (cx + back_dir * 1, cy + 4),
        ])

        # Violet accent on inner cape.
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["violet_dark"], [
            (cx + back_dir * 5, cy - 3),
            (cx + back_dir * 7, cy + 2),
            (cx + back_dir * 8, cy + 8),
            (cx + back_dir * 6, cy + 12),
            (cx + back_dir * 3, cy + 8),
            (cx + back_dir * 1, cy + 3),
        ])

        # Bright violet edge (energy glow).
        pygame.draw.line(surface, _NS_astraelion.PALETTE["violet_mid"],
                        (cx + back_dir * 6, cy - 4),
                        (cx + back_dir * 10, cy + 1), 1)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["violet_light"],
                        (cx + back_dir * 12, cy + 4),
                        (cx + back_dir * 14 + int(sway), cy + 8), 1)

        # Torn edges at bottom (like referring image).
        for i, (tx_off, ty_off) in enumerate([(-14, 18), (-10, 20), (-6, 18)]):
            tx = cx + back_dir * abs(tx_off)
            ty = cy + ty_off + int(sway)
            _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["armor_dark"], [
                (tx, ty - 2),
                (tx + 2, ty),
                (tx, ty + 3),
                (tx - 2, ty),
            ])
            _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["armor_mid"], [
                (tx, ty - 1),
                (tx + 1, ty),
                (tx, ty + 2),
                (tx - 1, ty),
            ])
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_light"], (tx, ty, 1, 1))

        # Small violet embers escaping.
        for i in range(3):
            em_t = (phase * 0.5 + i * 0.33) % 1.0
            emx = cx + back_dir * (8 + i * 3) + int(math.sin(phase + i) * 2)
            emy = cy + 15 - int(em_t * 12)
            alpha = _NS_astraelion._alpha(200 * (1 - em_t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_astraelion.PALETTE["violet_light"], alpha),
                                (emx, emy, 1, 1))
                pygame.draw.rect(surface, (*_NS_astraelion.PALETTE["violet_hot"], alpha),
                                (emx, emy, 1, 1))

    def _draw_robe_bottom(surface, cx, cy, facing, phase):
        """Trailing armor/robe skirt below (no legs, floating)."""
        sway = math.sin(phase * 0.5) * 2

        # Armor skirt (long tapered).
        skirt_shape = [
            (cx - 11, cy - 8),
            (cx - 14, cy - 2),
            (cx - 13, cy + 4),
            (cx - 10, cy + 12 + int(sway)),
            (cx - 4, cy + 18),
            (cx + 4, cy + 18 - int(sway)),
            (cx + 10, cy + 12),
            (cx + 13, cy + 4),
            (cx + 14, cy - 2),
            (cx + 11, cy - 8),
        ]
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in skirt_shape])
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["armor_darkest"], skirt_shape)

        # Layered.
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["armor_dark"], [
            (cx - 10, cy - 7),
            (cx - 13, cy - 1),
            (cx - 12, cy + 4),
            (cx - 6, cy + 14),
            (cx + 6, cy + 14),
            (cx + 12, cy + 4),
            (cx + 13, cy - 1),
            (cx + 10, cy - 7),
        ])
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["armor_mid"], [
            (cx - 8, cy - 5),
            (cx - 11, cy),
            (cx - 9, cy + 6),
            (cx - 4, cy + 12),
            (cx + 4, cy + 12),
            (cx + 9, cy + 6),
            (cx + 11, cy),
            (cx + 8, cy - 5),
        ])

        # Vertical fold lines.
        for x_off in [-8, -4, 0, 4, 8]:
            fold_x = cx + x_off
            pygame.draw.line(surface, _NS_astraelion.PALETTE["armor_darkest"],
                            (fold_x, cy - 4), (fold_x - x_off // 3, cy + 14), 1)

        # Gold belt/waist.
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["shadow_deep"],
                        (cx - 12, cy - 8, 24, 4))
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["gold_dark"],
                        (cx - 11, cy - 8, 22, 3))
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["gold_mid"],
                        (cx - 11, cy - 7, 22, 2))
        pygame.draw.line(surface, _NS_astraelion.PALETTE["gold_light"],
                        (cx - 10, cy - 7), (cx + 10, cy - 7), 1)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["gold_shine"],
                        (cx - 8, cy - 8), (cx + 8, cy - 8), 1)

        # Central gem on belt (violet).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_astraelion._alpha(150 * (4 - r) / 4 * pulse)
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["violet_mid"], alpha),
                                    (cx, cy - 6), r)
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_darkest"], (cx - 1, cy - 7, 3, 3))
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_dark"], (cx - 1, cy - 6, 2, 2))
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_light"], (cx, cy - 6, 1, 1))
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_shine"], (cx, cy - 6, 1, 1))

    def _draw_ast_torso(surface, cx, cy, facing, phase):
        """Armored torso (navy blue with silver plates)."""
        breath = math.sin(phase * 0.7) * 1

        # Torso silhouette.
        torso_shape = [
            (cx - 9, cy - 6),
            (cx - 11, cy - 3),
            (cx - 10, cy + 3),
            (cx - 7, cy + 7),
            (cx + 7, cy + 7),
            (cx + 10, cy + 3),
            (cx + 11, cy - 3),
            (cx + 9, cy - 6),
            (cx + 5, cy - 8),
            (cx - 5, cy - 8),
        ]
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in torso_shape])
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["armor_darkest"], torso_shape)

        # Base armor layer.
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["armor_dark"], [
            (cx - 8, cy - 5),
            (cx - 10, cy - 2),
            (cx - 9, cy + 2),
            (cx - 6, cy + 6),
            (cx + 6, cy + 6),
            (cx + 9, cy + 2),
            (cx + 10, cy - 2),
            (cx + 8, cy - 5),
            (cx + 4, cy - 7),
            (cx - 4, cy - 7),
        ])
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["armor_mid"], [
            (cx - 6, cy - 3),
            (cx - 8, cy),
            (cx - 6, cy + 5),
            (cx + 6, cy + 5),
            (cx + 8, cy),
            (cx + 6, cy - 3),
            (cx + 3, cy - 6),
            (cx - 3, cy - 6),
        ])

        # SILVER CHEST PLATE (central).
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["silver_darkest"], [
            (cx - 5, cy - 4),
            (cx - 6, cy - 1),
            (cx - 5, cy + 4),
            (cx - 2, cy + 6),
            (cx + 2, cy + 6),
            (cx + 5, cy + 4),
            (cx + 6, cy - 1),
            (cx + 5, cy - 4),
            (cx + 3, cy - 6),
            (cx - 3, cy - 6),
        ])
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["silver_dark"], [
            (cx - 4, cy - 3),
            (cx - 5, cy),
            (cx - 4, cy + 3),
            (cx - 1, cy + 5),
            (cx + 1, cy + 5),
            (cx + 4, cy + 3),
            (cx + 5, cy),
            (cx + 4, cy - 3),
            (cx + 2, cy - 5),
            (cx - 2, cy - 5),
        ])
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["silver_mid"], [
            (cx - 3, cy - 2),
            (cx - 4, cy),
            (cx - 3, cy + 3),
            (cx + 3, cy + 3),
            (cx + 4, cy),
            (cx + 3, cy - 2),
            (cx + 2, cy - 4),
            (cx - 2, cy - 4),
        ])
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["silver_light"], [
            (cx - 2, cy - 1),
            (cx - 2, cy + 2),
            (cx + 2, cy + 2),
            (cx + 2, cy - 1),
            (cx + 1, cy - 3),
            (cx - 1, cy - 3),
        ])
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["silver_shine"], (cx, cy, 1, 1))

        # CENTRAL VIOLET GEM (chest emblem).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        emblem_y = cy + 1
        for r in range(4, 0, -1):
            alpha = _NS_astraelion._alpha(180 * (4 - r) / 4 * pulse)
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["violet_mid"], alpha),
                                    (cx, emblem_y), r)
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_darkest"],
                        (cx - 1, emblem_y - 1, 3, 3))
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_dark"],
                        (cx - 1, emblem_y, 2, 2))
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_light"],
                        (cx, emblem_y, 1, 1))
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_shine"],
                        (cx, emblem_y, 1, 1))
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["white"],
                        (cx, emblem_y, 1, 1))

        # Center vertical seam.
        pygame.draw.line(surface, _NS_astraelion.PALETTE["silver_darkest"],
                        (cx, cy - 4), (cx, cy + 5), 1)

        # Gold trim edges.
        pygame.draw.line(surface, _NS_astraelion.PALETTE["gold_dark"],
                        (cx - 5, cy - 4), (cx - 6, cy - 1), 1)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["gold_mid"],
                        (cx + 5, cy - 4), (cx + 6, cy - 1), 1)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["gold_light"],
                        (cx - 2, cy + 6), (cx + 2, cy + 6), 1)

    def _draw_pauldrons(surface, cx, cy, facing, phase):
        """Silver spiky pauldrons on shoulders."""
        for side in [-1, 1]:
            px = cx + side * 10
            py = cy

            # Main pauldron plate.
            pauldron = [
                (px - side * 2, py - 3),
                (px + side * 5, py - 4),
                (px + side * 7, py + 1),
                (px + side * 5, py + 5),
                (px - side * 2, py + 4),
            ]
            _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["shadow_deep"],
                                [(x + 1, y + 1) for x, y in pauldron])
            _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["silver_darkest"], pauldron)
            _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["silver_dark"], [
                (px - side, py - 2),
                (px + side * 4, py - 3),
                (px + side * 6, py + 1),
                (px + side * 4, py + 4),
                (px - side, py + 3),
            ])
            _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["silver_mid"], [
                (px, py - 1),
                (px + side * 3, py - 2),
                (px + side * 4, py + 1),
                (px + side * 3, py + 3),
                (px, py + 2),
            ])
            _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["silver_light"], [
                (px + side, py),
                (px + side * 2, py - 1),
                (px + side * 2, py + 1),
            ])
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["silver_shine"],
                            (px + side * 2, py, 1, 1))

            # Gold trim.
            pygame.draw.line(surface, _NS_astraelion.PALETTE["gold_mid"],
                            (px - side * 2, py - 3), (px + side * 5, py - 4), 1)
            pygame.draw.line(surface, _NS_astraelion.PALETTE["gold_light"],
                            (px + side * 3, py - 3), (px + side * 5, py - 3), 1)

            # Small crystalline spike on top (violet-tinted).
            spike_x = px + side * 2
            spike_top_y = py - 6
            spike_base_y = py - 3
            _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_top_y + 1),
                (spike_x - 1, spike_base_y + 1),
                (spike_x + 2, spike_base_y + 1),
            ])
            _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["silver_darkest"], [
                (spike_x, spike_top_y),
                (spike_x - 1, spike_base_y),
                (spike_x + 1, spike_base_y),
            ])
            _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["silver_mid"], [
                (spike_x, spike_top_y),
                (spike_x, spike_base_y),
                (spike_x + 1, spike_base_y),
            ])
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_light"],
                            (spike_x, spike_top_y, 1, 1))

    def _draw_ast_arm_back(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm."""
        sway = math.sin(phase * 0.4) * 1
        back_dir = -facing
        shoulder_x = cx + back_dir * 8
        shoulder_y = cy - 3
        elbow_x = shoulder_x + back_dir * 2
        elbow_y = shoulder_y + 5 + int(sway)
        hand_x = elbow_x - back_dir * 1
        hand_y = elbow_y + 5 + int(sway)

        # Upper arm (armor sleeve navy).
        pygame.draw.line(surface, _NS_astraelion.PALETTE["shadow_deep"],
                        (shoulder_x + 1, shoulder_y + 1), (elbow_x + 1, elbow_y + 1), 3)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["armor_darkest"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["armor_dark"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 2)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["armor_mid"],
                        (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 1)

        # Silver forearm gauntlet.
        pygame.draw.line(surface, _NS_astraelion.PALETTE["shadow_deep"],
                        (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 3)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["silver_darkest"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 3)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["silver_dark"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 2)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["silver_mid"],
                        (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)

        # Gauntlet.
        _NS_astraelion._aacircle(surface, _NS_astraelion.PALETTE["silver_dark"],
                                (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["silver_light"], (hand_x, hand_y, 1, 1))

    def _draw_ast_arm_front(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding sword."""
        sway = math.sin(phase * 0.4) * 1

        # Arm pose based on action.
        if action == "attack":
            if attack_progress < 0.3:
                # Raise sword up.
                t = attack_progress / 0.3
                shoulder_angle = -0.2 - t * 0.9
                elbow_bend = 0.4 - t * 0.2
            elif attack_progress < 0.55:
                # SLASH DOWN.
                t = (attack_progress - 0.3) / 0.25
                shoulder_angle = -1.1 + t * 1.5
                elbow_bend = 0.2 + t * 0.3
            else:
                # Recovery.
                t = (attack_progress - 0.55) / 0.45
                shoulder_angle = 0.4 - t * 0.6
                elbow_bend = 0.5 - t * 0.1
        else:
            shoulder_angle = -0.1 + math.sin(phase * 0.5) * 0.1
            elbow_bend = 0.5

        shoulder_x = cx + facing * 8
        shoulder_y = cy - 3
        upper_len = 6
        elbow_x = shoulder_x + int(math.cos(shoulder_angle) * upper_len) * facing
        elbow_y = shoulder_y + int(math.sin(shoulder_angle) * upper_len) + 2

        forearm_angle = shoulder_angle + elbow_bend
        forearm_len = 8
        hand_x = elbow_x + int(math.cos(forearm_angle) * forearm_len) * facing
        hand_y = elbow_y + int(math.sin(forearm_angle) * forearm_len) + 3

        # Upper arm (armor sleeve).
        pygame.draw.line(surface, _NS_astraelion.PALETTE["shadow_deep"],
                        (shoulder_x + 1, shoulder_y + 1), (elbow_x + 1, elbow_y + 1), 3)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["armor_darkest"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["armor_dark"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 2)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["armor_mid"],
                        (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 1)

        # Silver forearm gauntlet.
        pygame.draw.line(surface, _NS_astraelion.PALETTE["shadow_deep"],
                        (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 3)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["silver_darkest"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 3)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["silver_dark"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 2)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["silver_mid"],
                        (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)

        # Gauntlet with gold trim.
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["gold_dark"],
                        (elbow_x - 1, elbow_y - 1, 3, 2))
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["gold_mid"],
                        (elbow_x, elbow_y - 1, 2, 1))

        # Fist holding sword.
        _NS_astraelion._aacircle(surface, _NS_astraelion.PALETTE["silver_darkest"],
                                (hand_x, hand_y), 3)
        _NS_astraelion._aacircle(surface, _NS_astraelion.PALETTE["silver_dark"],
                                (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["silver_light"], (hand_x, hand_y, 1, 1))

        # Store hand pos on boss for sword.
        # But we can compute again in sword function.

    def _draw_ast_head(surface, cx, cy, facing, phase):
        """Male noble face with blonde hair, cyan eyes."""
        # Head shape.
        head_shape = [
            (cx - 5, cy - 1),
            (cx - 6, cy + 2),
            (cx - 5, cy + 6),
            (cx - 2, cy + 8),
            (cx + 2, cy + 8),
            (cx + 5, cy + 6),
            (cx + 6, cy + 2),
            (cx + 5, cy - 1),
            (cx + 3, cy - 4),
            (cx - 3, cy - 4),
        ]
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in head_shape])
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["skin_darkest"], head_shape)

        # Skin layers.
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["skin_dark"], [
            (cx - 4, cy),
            (cx - 5, cy + 2),
            (cx - 4, cy + 6),
            (cx - 2, cy + 7),
            (cx + 2, cy + 7),
            (cx + 4, cy + 6),
            (cx + 5, cy + 2),
            (cx + 4, cy),
            (cx + 2, cy - 3),
            (cx - 2, cy - 3),
        ])
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["skin_mid"], [
            (cx - 3, cy + 1),
            (cx - 4, cy + 3),
            (cx - 3, cy + 5),
            (cx + 3, cy + 5),
            (cx + 4, cy + 3),
            (cx + 3, cy + 1),
            (cx + 2, cy - 2),
            (cx - 2, cy - 2),
        ])
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["skin_light"], [
            (cx - 2, cy + 2),
            (cx - 2, cy + 4),
            (cx + 2, cy + 4),
            (cx + 2, cy + 2),
            (cx + 1, cy),
            (cx - 1, cy),
        ])
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["skin_shine"], (cx, cy + 3, 1, 1))

        # BLONDE HAIR TOP with wind-swept bangs.
        _NS_astraelion._draw_blonde_hair(surface, cx, cy, facing, phase)

        # CYAN EYES (bright).
        _NS_astraelion._draw_cyan_eyes(surface, cx, cy + 2, facing, phase)

        # Small nose.
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["skin_darkest"], (cx, cy + 4, 1, 1))

        # Serious mouth.
        pygame.draw.line(surface, _NS_astraelion.PALETTE["skin_darkest"],
                        (cx - 1, cy + 6), (cx + 1, cy + 6), 1)

    def _draw_blonde_hair(surface, cx, cy, facing, phase):
        """Blonde wind-swept hair."""
        # Top hair (spiky/swept).
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["shadow_deep"], [
            (cx - 6, cy - 1),
            (cx - 5, cy - 4),
            (cx - 2, cy - 5),
            (cx, cy - 4),
            (cx + 2, cy - 5),
            (cx + 5, cy - 4),
            (cx + 6, cy - 1),
            (cx + 5, cy + 1),
            (cx - 5, cy + 1),
        ])
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["hair_darkest"], [
            (cx - 6, cy - 1),
            (cx - 5, cy - 3),
            (cx - 2, cy - 4),
            (cx, cy - 3),
            (cx + 2, cy - 4),
            (cx + 5, cy - 3),
            (cx + 6, cy - 1),
            (cx + 5, cy),
            (cx - 5, cy),
        ])
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["hair_dark"], [
            (cx - 5, cy - 1),
            (cx - 4, cy - 3),
            (cx - 1, cy - 3),
            (cx + 1, cy - 3),
            (cx + 4, cy - 3),
            (cx + 5, cy - 1),
            (cx + 4, cy),
            (cx - 4, cy),
        ])
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["hair_mid"], [
            (cx - 3, cy - 1),
            (cx - 2, cy - 2),
            (cx + 2, cy - 2),
            (cx + 3, cy - 1),
            (cx + 2, cy),
            (cx - 2, cy),
        ])
        # Bright highlights.
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["hair_light"], (cx - 3, cy - 2, 1, 1))
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["hair_light"], (cx + 2, cy - 2, 1, 1))
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["hair_shine"], (cx - 1, cy - 3, 1, 1))
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["hair_shine"], (cx + 1, cy - 3, 1, 1))

        # Side wind-swept spikes.
        sway = math.sin(phase * 0.6) * 1
        for side, x_off in [(-1, -6), (1, 6)]:
            spike_top_x = cx + x_off + side * 2 + int(sway * side)
            spike_top_y = cy - 3
            spike_bot_x = cx + x_off
            spike_bot_y = cy + 2
            pygame.draw.line(surface, _NS_astraelion.PALETTE["hair_darkest"],
                            (spike_bot_x, spike_bot_y), (spike_top_x, spike_top_y), 2)
            pygame.draw.line(surface, _NS_astraelion.PALETTE["hair_dark"],
                            (spike_bot_x, spike_bot_y), (spike_top_x, spike_top_y), 1)
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["hair_light"],
                            (spike_top_x, spike_top_y, 1, 1))

    def _draw_cyan_eyes(surface, cx, cy, facing, phase):
        """Bright cyan determined eyes."""
        pulse = math.sin(phase * 2.5) * 0.2 + 0.8

        for side in [-1, 1]:
            ex = cx + side * 2
            ey = cy

            # Eye white.
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["white"], (ex - 1, ey, 2, 1))

            # Iris (cyan).
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["cyan_dark"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["cyan_mid"], (ex, ey, 1, 1))

            # Glow.
            for r in range(3, 0, -1):
                alpha = _NS_astraelion._alpha(100 * (3 - r) / 3 * pulse)
                _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["cyan_mid"], alpha),
                                        (ex, ey), r)

            pygame.draw.rect(surface, _NS_astraelion.PALETTE["cyan_glow"], (ex, ey, 1, 1))

            # Sharp eyebrow.
            pygame.draw.line(surface, _NS_astraelion.PALETTE["hair_dark"],
                            (ex - 1, ey - 2), (ex + 1, ey - 2), 1)

    def _draw_energy_sword(surface, cx, cy, facing, phase, action, attack_progress):
        """Large violet energy sword - the star of the show."""
        # Determine sword angle based on action.
        if action == "attack":
            if attack_progress < 0.3:
                # Raise high.
                t = attack_progress / 0.3
                angle = -math.pi / 2 - t * 0.8
            elif attack_progress < 0.55:
                # SLASH ARC.
                t = (attack_progress - 0.3) / 0.25
                angle = (-math.pi / 2 - 0.8) + t * 2.0
            else:
                # Recovery.
                t = (attack_progress - 0.55) / 0.45
                angle = 0.7 - t * 0.9
        else:
            # Idle: sword pointed forward/down slightly.
            angle = -0.2 + math.sin(phase * 0.4) * 0.05

        # Apply facing.
        actual_angle = angle * facing if angle > -math.pi / 2 else angle
        # Simpler: just flip via multiplier on final.
        # Actually let's use direct formula:
        # Base pose for facing right; for left, mirror the angle.
        base_angle = angle
        # In pygame, x-axis positive is right. We want swordto follow direction.
        # We'll compute normally then flip x-component.

        # Hand position.
        hand_x = cx + facing * 12
        hand_y = cy + 5

        # Sword parameters.
        blade_length = 42
        blade_width = 5

        # Compute tip.
        cos_a = math.cos(base_angle)
        sin_a = math.sin(base_angle)
        tip_x = hand_x + int(cos_a * blade_length) * facing
        tip_y = hand_y + int(sin_a * blade_length)

        # Perpendicular for blade width.
        perp = base_angle + math.pi / 2
        perp_x = math.cos(perp) * facing
        perp_y = math.sin(perp)

        # Draw HANDLE first (short grip).
        handle_len = 6
        handle_end_x = hand_x - int(cos_a * handle_len) * facing
        handle_end_y = hand_y - int(sin_a * handle_len)

        pygame.draw.line(surface, _NS_astraelion.PALETTE["shadow_deep"],
                        (hand_x + 1, hand_y + 1), (handle_end_x + 1, handle_end_y + 1), 4)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["silver_darkest"],
                        (hand_x, hand_y), (handle_end_x, handle_end_y), 3)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["silver_dark"],
                        (hand_x, hand_y), (handle_end_x, handle_end_y), 2)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["silver_mid"],
                        (hand_x, hand_y), (handle_end_x, handle_end_y), 1)

        # Pommel (small orb at handle end).
        _NS_astraelion._aacircle(surface, _NS_astraelion.PALETTE["gold_dark"],
                                (handle_end_x, handle_end_y), 2)
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_light"],
                        (handle_end_x, handle_end_y, 1, 1))

        # CROSSGUARD (short bar at hand).
        crossguard_a = (hand_x + int(perp_x * 4), hand_y + int(perp_y * 4))
        crossguard_b = (hand_x - int(perp_x * 4), hand_y - int(perp_y * 4))
        pygame.draw.line(surface, _NS_astraelion.PALETTE["shadow_deep"],
                        (crossguard_a[0] + 1, crossguard_a[1] + 1),
                        (crossguard_b[0] + 1, crossguard_b[1] + 1), 3)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["gold_dark"],
                        crossguard_a, crossguard_b, 3)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["gold_mid"],
                        crossguard_a, crossguard_b, 2)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["gold_light"],
                        crossguard_a, crossguard_b, 1)
        # Small gems.
        for gem_off in [-2, 2]:
            gemx = hand_x + int(perp_x * gem_off)
            gemy = hand_y + int(perp_y * gem_off)
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_light"], (gemx, gemy, 1, 1))

        # BLADE (energy sword - crystalline).
        # Blade base at hand, extends to tip.
        blade_base_a = (hand_x + int(perp_x * blade_width),
                        hand_y + int(perp_y * blade_width))
        blade_base_b = (hand_x - int(perp_x * blade_width),
                        hand_y - int(perp_y * blade_width))
        # Middle points.
        mid_x = int((hand_x + tip_x) / 2)
        mid_y = int((hand_y + tip_y) / 2)
        blade_mid_a = (mid_x + int(perp_x * (blade_width - 1)),
                       mid_y + int(perp_y * (blade_width - 1)))
        blade_mid_b = (mid_x - int(perp_x * (blade_width - 1)),
                       mid_y - int(perp_y * (blade_width - 1)))

        # Draw blade as polygon (diamond-like tapering).
        blade_poly = [
            blade_base_a,
            blade_mid_a,
            (tip_x, tip_y),
            blade_mid_b,
            blade_base_b,
        ]
        # Shadow.
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in blade_poly])
        # Layered blade.
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["blade_darkest"], blade_poly)
        # Inner narrower.
        inner_poly = [
            (int(hand_x + perp_x * (blade_width - 1)),
             int(hand_y + perp_y * (blade_width - 1))),
            (int(mid_x + perp_x * (blade_width - 2)),
             int(mid_y + perp_y * (blade_width - 2))),
            (tip_x, tip_y),
            (int(mid_x - perp_x * (blade_width - 2)),
             int(mid_y - perp_y * (blade_width - 2))),
            (int(hand_x - perp_x * (blade_width - 1)),
             int(hand_y - perp_y * (blade_width - 1))),
        ]
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["blade_dark"], inner_poly)

        # Even more inner (bright core).
        core_poly = [
            (int(hand_x + perp_x * 1), int(hand_y + perp_y * 1)),
            (int(mid_x + perp_x * 1), int(mid_y + perp_y * 1)),
            (tip_x, tip_y),
            (int(mid_x - perp_x * 1), int(mid_y - perp_y * 1)),
            (int(hand_x - perp_x * 1), int(hand_y - perp_y * 1)),
        ]
        _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["blade_mid"], core_poly)

        # Center bright line.
        pygame.draw.line(surface, _NS_astraelion.PALETTE["blade_light"],
                        (hand_x, hand_y), (tip_x, tip_y), 1)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["blade_shine"],
                        (int(hand_x + cos_a * 4 * facing), int(hand_y + sin_a * 4)),
                        (int(tip_x - cos_a * 4 * facing), int(tip_y - sin_a * 4)), 1)

        # Bright tip.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(6, 0, -1):
            alpha = _NS_astraelion._alpha(150 * (6 - r) / 6 * pulse)
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["blade_light"], alpha),
                                    (tip_x, tip_y), r)
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["blade_shine"], (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["white"], (tip_x, tip_y, 1, 1))

        # Crystalline fragments along blade (like referring image - star shatter).
        for frag_i in range(5):
            frag_t = 0.15 + frag_i * 0.17
            frag_x = int(hand_x + (tip_x - hand_x) * frag_t)
            frag_y = int(hand_y + (tip_y - hand_y) * frag_t)
            frag_perp_off = int(math.sin(phase * 2 + frag_i) * 2)
            # Fragment above/below blade.
            for side in [-1, 1]:
                fx = frag_x + int(perp_x * (blade_width + 3) * side)
                fy = frag_y + int(perp_y * (blade_width + 3) * side) + frag_perp_off
                alpha = _NS_astraelion._alpha(180)
                # Small violet shard.
                _NS_astraelion._poly(surface,
                                    (*_NS_astraelion.PALETTE["violet_dark"], alpha), [
                                        (fx, fy - 2),
                                        (fx + 1, fy),
                                        (fx, fy + 2),
                                        (fx - 1, fy),
                                    ])
                _NS_astraelion._poly(surface,
                                    (*_NS_astraelion.PALETTE["violet_light"], alpha), [
                                        (fx, fy - 1),
                                        (fx + 1, fy),
                                        (fx, fy + 1),
                                    ])
                pygame.draw.rect(surface,
                                (*_NS_astraelion.PALETTE["violet_shine"], alpha),
                                (fx, fy, 1, 1))

        # Violet energy glow along blade (outer aura).
        glow_alpha = _NS_astraelion._alpha(160 * pulse)
        for offset in [3, 2, 1]:
            side_a = (int(hand_x + perp_x * (blade_width + offset)),
                      int(hand_y + perp_y * (blade_width + offset)))
            side_b = (int(tip_x + perp_x * (offset - 1)),
                      int(tip_y + perp_y * (offset - 1)))
            side_c = (int(hand_x - perp_x * (blade_width + offset)),
                      int(hand_y - perp_y * (blade_width + offset)))
            side_d = (int(tip_x - perp_x * (offset - 1)),
                      int(tip_y - perp_y * (offset - 1)))
            pygame.draw.line(surface,
                            (*_NS_astraelion.PALETTE["violet_mid"], glow_alpha),
                            side_a, side_b, 1)
            pygame.draw.line(surface,
                            (*_NS_astraelion.PALETTE["violet_mid"], glow_alpha),
                            side_c, side_d, 1)

        # SWING TRAIL (during attack).
        if action == "attack" and 0.3 < attack_progress < 0.65:
            _NS_astraelion._draw_sword_trail(surface, hand_x, hand_y, facing,
                                             attack_progress, phase)

    def _draw_sword_trail(surface, hand_x, hand_y, facing, progress, phase):
        """Violet arc trail from sword slash."""
        swing_t = (progress - 0.3) / 0.35
        intensity = math.sin(swing_t * math.pi)

        # Arc spans from up to down.
        start_angle = -math.pi / 2 - 0.8
        end_angle = -math.pi / 2 - 0.8 + 2.0

        segments = 15
        for i in range(segments):
            t1 = i / segments
            t2 = (i + 1) / segments
            if t1 > swing_t:
                continue
            a1 = start_angle + (end_angle - start_angle) * t1
            a2 = start_angle + (end_angle - start_angle) * t2

            radius = 40
            p1 = (hand_x + int(math.cos(a1) * radius) * facing,
                  hand_y + int(math.sin(a1) * radius))
            p2 = (hand_x + int(math.cos(a2) * radius) * facing,
                  hand_y + int(math.sin(a2) * radius))

            fade = 1.0 - (swing_t - t1) * 0.8
            alpha = _NS_astraelion._alpha(240 * intensity * fade)

            for w, color_key in [
                (7, "violet_darkest"),
                (5, "violet_dark"),
                (3, "violet_mid"),
                (2, "violet_light"),
                (1, "violet_shine"),
            ]:
                pygame.draw.line(surface,
                                (*_NS_astraelion.PALETTE[color_key], alpha),
                                p1, p2, w)

            # Bright sparks along trail.
            if i % 2 == 0:
                pygame.draw.rect(surface,
                                (*_NS_astraelion.PALETTE["violet_hot"], alpha),
                                (p2[0], p2[1], 2, 2))
                pygame.draw.rect(surface,
                                (*_NS_astraelion.PALETTE["white"], alpha),
                                (p2[0], p2[1], 1, 1))

    # ============================================================
    # FLOATING STAR PARTICLES (violet stars below)
    # ============================================================
    def _draw_star_particles(surface, cx, cy, phase, trail=False, facing=1,
                             intense=False):
        """Violet star particles below (cosmic hover)."""
        strength = 1.5 if intense else 1.0

        # Ground glow.
        glow = pygame.Surface((120, 30), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for r in range(26, 3, -2):
            alpha = _NS_astraelion._alpha((26 - r) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(glow, (*_NS_astraelion.PALETTE["mist_dark"], alpha),
                                    (60 - r * 2, 15 - r // 3, r * 4, max(3, r // 2)))
        for r in range(18, 3, -2):
            alpha = _NS_astraelion._alpha((18 - r) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(glow, (*_NS_astraelion.PALETTE["mist_mid"], alpha),
                                    (60 - r, 15 - r // 4, r * 2, max(2, r // 3)))
        surface.blit(glow, (cx - 60, cy - 8))

        # Rising star wisps.
        for i, offset in enumerate([-20, -12, -4, 4, 12, 20]):
            t = (phase * 0.5 + i * 0.15) % 1.0
            wx = cx + offset + int(math.sin(phase * 2 + i) * 3)
            wy = cy + 4 - int(t * 24)
            alpha = _NS_astraelion._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["mist_dark"], alpha),
                                    (wx, wy), 3)
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["mist_mid"], alpha),
                                    (wx, wy - 1), 2)
            pygame.draw.rect(surface, (*_NS_astraelion.PALETTE["violet_light"], alpha),
                            (wx, wy - 1, 1, 1))

        # Star shapes rising (4-point stars).
        for i in range(5):
            st_t = (phase * 0.6 + i * 0.2) % 1.0
            stx = cx - 16 + i * 8 + int(math.sin(phase + i) * 3)
            sty = cy + 6 - int(st_t * 22)
            alpha = _NS_astraelion._alpha(230 * (1 - st_t) * strength)
            if alpha > 0:
                # 4-point star.
                _NS_astraelion._poly(surface, (*_NS_astraelion.PALETTE["violet_dark"], alpha), [
                    (stx, sty - 3),
                    (stx + 1, sty),
                    (stx, sty + 3),
                    (stx - 1, sty),
                ])
                _NS_astraelion._poly(surface, (*_NS_astraelion.PALETTE["violet_mid"], alpha), [
                    (stx + 3, sty),
                    (stx, sty + 1),
                    (stx - 3, sty),
                    (stx, sty - 1),
                ])
                pygame.draw.rect(surface, (*_NS_astraelion.PALETTE["violet_shine"], alpha),
                                (stx, sty, 1, 1))
                pygame.draw.rect(surface, (*_NS_astraelion.PALETTE["white"], alpha),
                                (stx, sty, 1, 1))

        # Cyan sparkles.
        for i in range(8):
            spark_t = (phase * 0.7 + i * 0.12) % 1.0
            sx = cx - 22 + i * 6 + int(math.sin(phase + i) * 3)
            sy = cy + 2 - int(spark_t * 20)
            alpha = _NS_astraelion._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_astraelion.PALETTE["cyan_mid"], alpha),
                                (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_astraelion.PALETTE["cyan_light"], alpha),
                                (sx, sy, 1, 1))

        # Trail behind.
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_astraelion._alpha(170 - i * 25)
                if alpha <= 0:
                    continue
                _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["mist_dark"], alpha),
                                        (sx, sy), max(2, 6 - i))
                _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["mist_mid"], alpha),
                                        (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_astraelion.PALETTE["violet_light"], alpha),
                                (sx, sy - 1, 2, 2))
                pygame.draw.rect(surface, (*_NS_astraelion.PALETTE["violet_hot"], alpha),
                                (sx, sy - 1, 1, 1))

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((120, 28), pygame.SRCALPHA)
        for r in range(12, 0, -1):
            alpha = max(0, (12 - r) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - r, 14 - r, 100 + r * 2, r * 2))
        pygame.draw.ellipse(shadow, (3, 2, 8, 170), (5, 6, 110, 14))
        pygame.draw.ellipse(shadow, (30, 15, 60, 110), (12, 8, 96, 10))
        surface.blit(shadow, (x - 60, y - 14))

    def _draw_star_aura(surface, x, y, phase):
        """Cosmic violet aura with stars."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((200, 170), pygame.SRCALPHA)
        for r in range(85, 5, -5):
            alpha = _NS_astraelion._alpha((85 - r) * 1.2 * pulse)
            if alpha > 0:
                _NS_astraelion._aacircle(aura, (*_NS_astraelion.PALETTE["mist_dark"], alpha),
                                        (100, 85), r)
        for r in range(55, 5, -4):
            alpha = _NS_astraelion._alpha((55 - r) * 1.4 * pulse)
            if alpha > 0:
                _NS_astraelion._aacircle(aura, (*_NS_astraelion.PALETTE["mist_mid"], alpha),
                                        (100, 85), r)
        for r in range(32, 5, -3):
            alpha = _NS_astraelion._alpha((32 - r) * 1.4 * pulse)
            if alpha > 0:
                _NS_astraelion._aacircle(aura, (*_NS_astraelion.PALETTE["violet_darkest"], alpha),
                                        (100, 85), r)
        surface.blit(aura, (x - 100, y - 85))

        # Floating stars.
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 34 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            # Small star sparkle.
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_hot"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["white"], (sx, sy, 1, 1))
            # 4-point star arms.
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_light"], (sx - 1, sy, 1, 1))
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_light"], (sx + 1, sy, 1, 1))
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_light"], (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_light"], (sx, sy + 1, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring with cosmic runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 48), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_astraelion.PALETTE["mist_dark"], 200),
                            (5, 15, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_astraelion.PALETTE["violet_darkest"], 220),
                            (12, 17, 136, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_astraelion.PALETTE["violet_dark"], 230),
                            (22, 19, 116, 16), 1)
        pygame.draw.ellipse(ring, (*_NS_astraelion.PALETTE["cyan_dark"], 180),
                            (35, 21, 90, 12), 1)

        # Runes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 27 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 62)
            y2 = 27 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_astraelion.PALETTE["violet_light"], 220),
                            (x1, y1), (x2, y2), 1)

        # 4-point stars.
        for i in range(5):
            angle = phase * 0.3 + i * math.pi / 2.5 + math.pi / 5
            sx = 80 + int(math.cos(angle) * 55)
            sy = 27 + int(math.sin(angle) * 9)
            pygame.draw.rect(ring, (*_NS_astraelion.PALETTE["violet_hot"], 240), (sx, sy, 2, 2))
            pygame.draw.rect(ring, (*_NS_astraelion.PALETTE["violet_shine"], 240), (sx, sy, 1, 1))

        if skill:
            pygame.draw.ellipse(ring, (*_NS_astraelion.PALETTE["violet_hot"],
                                       _NS_astraelion._alpha(150 * pulse)),
                                (14, 10, 132, 34), 1)
        surface.blit(ring, (x - 80, y - 24))

    # ============================================================
    # SKILL: Q - SWORD FALL (dash forward with sword)
    # ============================================================
    def _draw_swordfall(surface, boss, x, y, timer, phase):
        """Dash forward + impact sword slam."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_astraelion._target_position(boss, x, y)

        start_x = x + facing * 16
        start_y = y - 6

        # Streak trail.
        t = progress
        current_x = int(start_x + (tx - start_x) * t)
        current_y = int(start_y + (ty - start_y) * t)

        # Long violet streak (like referring image).
        for i in range(12):
            trail_t = max(0.0, t - i * 0.05)
            if trail_t <= 0:
                continue
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_astraelion._alpha(240 - i * 20)

            perp_angle = math.atan2(ty - start_y, tx - start_x) + math.pi / 2
            perp_x = math.cos(perp_angle)
            perp_y = math.sin(perp_angle)
            size = max(1, 8 - i // 2)

            for w, color_key in [
                (size + 2, "violet_darkest"),
                (size, "violet_dark"),
                (max(1, size - 2), "violet_mid"),
                (1, "violet_light"),
            ]:
                p1 = (px + int(perp_x * w // 2), py + int(perp_y * w // 2))
                p2 = (px - int(perp_x * w // 2), py - int(perp_y * w // 2))
                pygame.draw.line(surface, (*_NS_astraelion.PALETTE[color_key], alpha),
                                p1, p2, 2)

        # Arrow-shape head (sword tip).
        head_angle = math.atan2(ty - start_y, tx - start_x)
        arrow_len = 20
        arrow_wid = 8

        tip = (current_x + int(math.cos(head_angle) * arrow_len),
               current_y + int(math.sin(head_angle) * arrow_len))
        perp = head_angle + math.pi / 2
        base_a = (current_x + int(math.cos(perp) * arrow_wid),
                  current_y + int(math.sin(perp) * arrow_wid))
        base_b = (current_x - int(math.cos(perp) * arrow_wid),
                  current_y - int(math.sin(perp) * arrow_wid))

        alpha = _NS_astraelion._alpha(240)
        _NS_astraelion._poly(surface, (*_NS_astraelion.PALETTE["violet_darkest"], alpha),
                            [tip, base_a, base_b])
        _NS_astraelion._poly(surface, (*_NS_astraelion.PALETTE["violet_dark"], alpha), [
            tip,
            (int((tip[0] + base_a[0]) / 2), int((tip[1] + base_a[1]) / 2)),
            (current_x, current_y),
            (int((tip[0] + base_b[0]) / 2), int((tip[1] + base_b[1]) / 2)),
        ])
        _NS_astraelion._poly(surface, (*_NS_astraelion.PALETTE["violet_mid"], alpha), [
            tip, (current_x, current_y),
            (int((tip[0] + base_a[0]) / 2), int((tip[1] + base_a[1]) / 2)),
        ])
        pygame.draw.line(surface, _NS_astraelion.PALETTE["violet_light"],
                        (current_x, current_y), tip, 2)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["violet_shine"],
                        (current_x, current_y), tip, 1)

        # Bright tip glow.
        for r in range(6, 0, -1):
            a = _NS_astraelion._alpha(180 * (6 - r) / 6)
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["violet_hot"], a), tip, r)
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["white"], (tip[0], tip[1], 1, 1))

        # Impact burst (star burst) when reaching target.
        if t > 0.85:
            st = (t - 0.85) / 0.15
            r = int(15 + st * 25)
            alpha = _NS_astraelion._alpha(240 * (1 - st))

            # Central star burst.
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["violet_darkest"], alpha),
                                    (tx, ty), r + 3, 3)
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["violet_dark"], alpha),
                                    (tx, ty), r, 3)
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["violet_mid"], alpha),
                                    (tx, ty), max(1, r - 5), 2)
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["violet_light"], alpha),
                                    (tx, ty), max(1, r - 12), 1)
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["white"], alpha),
                                    (tx, ty), max(1, r // 5))

            # 8-point star burst rays.
            for i in range(8):
                ray_angle = i * math.pi / 4
                ray_len = int(r * 1.4)
                ex = tx + int(math.cos(ray_angle) * ray_len)
                ey = ty + int(math.sin(ray_angle) * ray_len)
                for w, color_key in [
                    (4, "violet_dark"),
                    (2, "violet_light"),
                    (1, "violet_shine"),
                ]:
                    pygame.draw.line(surface, (*_NS_astraelion.PALETTE[color_key], alpha),
                                    (tx, ty), (ex, ey), w)
                pygame.draw.rect(surface, (*_NS_astraelion.PALETTE["white"], alpha),
                                (ex, ey, 2, 2))

    # ============================================================
    # SKILL: W - SPIRIT BLADE (thrown energy blade)
    # ============================================================
    def _draw_spiritblade(surface, boss, x, y, timer, phase):
        """Energy blade projectile flying forward."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_astraelion._target_position(boss, x, y)

        start_x = x + facing * 26
        start_y = y - 6

        t = progress
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Long trail (bright violet).
        for i in range(10):
            trail_t = max(0.0, t - i * 0.05)
            if trail_t <= 0:
                continue
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_astraelion._alpha(240 - i * 22)

            # Elongated blade shape trail.
            angle = math.atan2(ty - start_y, tx - start_x)
            perp = angle + math.pi / 2
            perp_x = math.cos(perp)
            perp_y = math.sin(perp)

            for w, color_key in [
                (6, "violet_darkest"),
                (4, "violet_dark"),
                (2, "violet_mid"),
                (1, "violet_light"),
            ]:
                p1 = (px + int(perp_x * w // 2), py + int(perp_y * w // 2))
                p2 = (px - int(perp_x * w // 2), py - int(perp_y * w // 2))
                pygame.draw.line(surface, (*_NS_astraelion.PALETTE[color_key], alpha),
                                p1, p2, 2)

        # BLADE PROJECTILE (elongated diamond).
        angle = math.atan2(ty - start_y, tx - start_x)
        blade_len = 18
        blade_wid = 6

        tip_x = bx + int(math.cos(angle) * blade_len)
        tip_y = by + int(math.sin(angle) * blade_len)
        tail_x = bx - int(math.cos(angle) * blade_len)
        tail_y = by - int(math.sin(angle) * blade_len)
        perp = angle + math.pi / 2
        side_a = (bx + int(math.cos(perp) * blade_wid),
                  by + int(math.sin(perp) * blade_wid))
        side_b = (bx - int(math.cos(perp) * blade_wid),
                  by - int(math.sin(perp) * blade_wid))

        alpha = _NS_astraelion._alpha(240)
        # Shadow.
        _NS_astraelion._poly(surface, (*_NS_astraelion.PALETTE["shadow_deep"], alpha), [
            (tip_x + 1, tip_y + 1),
            (side_a[0] + 1, side_a[1] + 1),
            (tail_x + 1, tail_y + 1),
            (side_b[0] + 1, side_b[1] + 1),
        ])
        # Blade layers.
        _NS_astraelion._poly(surface, (*_NS_astraelion.PALETTE["violet_darkest"], alpha),
                            [(tip_x, tip_y), side_a, (tail_x, tail_y), side_b])
        _NS_astraelion._poly(surface, (*_NS_astraelion.PALETTE["violet_dark"], alpha), [
            (tip_x, tip_y),
            (int((tip_x + side_a[0]) / 2), int((tip_y + side_a[1]) / 2)),
            (tail_x, tail_y),
            (int((tip_x + side_b[0]) / 2), int((tip_y + side_b[1]) / 2)),
        ])
        _NS_astraelion._poly(surface, (*_NS_astraelion.PALETTE["violet_mid"], alpha), [
            (tip_x, tip_y),
            (bx, by),
            (tail_x, tail_y),
        ])
        # Bright core line.
        pygame.draw.line(surface, _NS_astraelion.PALETTE["violet_light"],
                        (tail_x, tail_y), (tip_x, tip_y), 2)
        pygame.draw.line(surface, _NS_astraelion.PALETTE["violet_shine"],
                        (tail_x, tail_y), (tip_x, tip_y), 1)

        # Bright tip.
        for r in range(5, 0, -1):
            a = _NS_astraelion._alpha(180 * (5 - r) / 5)
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["violet_hot"], a),
                                    (tip_x, tip_y), r)
        pygame.draw.rect(surface, _NS_astraelion.PALETTE["white"], (tip_x, tip_y, 1, 1))

        # Star sparkles trailing.
        for i in range(8):
            sp_t = (phase * 2 + i * 0.12) % 1.0
            sp_p = min(1.0, t * sp_t)
            spx = int(start_x + (tx - start_x) * sp_p)
            spy = int(start_y + (ty - start_y) * sp_p) + int(math.sin(phase * 4 + i) * 3)
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_hot"], (spx, spy, 2, 2))
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["white"], (spx, spy, 1, 1))

        # Impact.
        if t > 0.88:
            st = (t - 0.88) / 0.12
            r = int(10 + st * 20)
            alpha = _NS_astraelion._alpha(230 * (1 - st))
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["violet_dark"], alpha),
                                    (tx, ty), r + 2, 2)
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["violet_mid"], alpha),
                                    (tx, ty), r, 2)
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["violet_light"], alpha),
                                    (tx, ty), max(1, r - 6), 1)
            # Star burst.
            for i in range(6):
                angle_s = i * math.pi / 3
                ex = tx + int(math.cos(angle_s) * r)
                ey = ty + int(math.sin(angle_s) * r * 0.7)
                pygame.draw.rect(surface, (*_NS_astraelion.PALETTE["violet_hot"], alpha),
                                (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_astraelion.PALETTE["white"], alpha),
                                (ex, ey, 1, 1))

    # ============================================================
    # SKILL: E - FORCE ESCAPE (blink with shadow left behind)
    # ============================================================
    def _draw_forceescape_ground(surface, boss, x, y, timer, phase):
        """Ground rune circle."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(2):
            r = int(28 + i * 4 + math.sin(phase * 2) * 2)
            alpha = _NS_astraelion._alpha(220 - i * 60)
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["violet_mid"], alpha),
                                    (x, y + 40), r, 2)
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["violet_light"], alpha),
                                    (x, y + 40), r, 1)

    def _draw_forceescape_foreground(surface, boss, x, y, timer, phase):
        """Shadow silhouette left behind + violet trail."""
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction

        # Shadow afterimages (like referring image - dark silhouettes).
        for i in range(4):
            trail_offset = (i + 1) * 12 * facing
            alpha = _NS_astraelion._alpha(220 - i * 40)
            if alpha <= 0:
                continue

            tx = x - trail_offset
            ty = y - 5 + int(math.sin(phase + i) * 2)

            # Body silhouette (dark violet ghost).
            silhouette = [
                (tx - 9, ty - 6),
                (tx - 11, ty),
                (tx - 10, ty + 8),
                (tx - 4, ty + 16),
                (tx + 4, ty + 16),
                (tx + 10, ty + 8),
                (tx + 11, ty),
                (tx + 9, ty - 6),
                (tx + 5, ty - 14),
                (tx - 5, ty - 14),
            ]
            _NS_astraelion._poly(surface,
                                (*_NS_astraelion.PALETTE["violet_darkest"], alpha),
                                silhouette)
            _NS_astraelion._poly(surface,
                                (*_NS_astraelion.PALETTE["violet_dark"], alpha // 2), [
                                    (tx - 7, ty - 4),
                                    (tx - 9, ty),
                                    (tx - 8, ty + 6),
                                    (tx - 3, ty + 12),
                                    (tx + 3, ty + 12),
                                    (tx + 8, ty + 6),
                                    (tx + 9, ty),
                                    (tx + 7, ty - 4),
                                    (tx + 4, ty - 12),
                                    (tx - 4, ty - 12),
                                ])

            # Cyan glowing eyes in silhouette.
            for side in [-1, 1]:
                pygame.draw.rect(surface,
                                (*_NS_astraelion.PALETTE["cyan_light"], alpha),
                                (tx + side * 2, ty - 10, 1, 1))
                pygame.draw.rect(surface,
                                (*_NS_astraelion.PALETTE["cyan_glow"], alpha),
                                (tx + side * 2, ty - 10, 1, 1))

            # Sword silhouette on shadow.
            sword_start_x = tx + facing * 8
            sword_start_y = ty
            sword_end_x = sword_start_x + facing * 20
            sword_end_y = sword_start_y - 15
            pygame.draw.line(surface,
                            (*_NS_astraelion.PALETTE["violet_mid"], alpha),
                            (sword_start_x, sword_start_y),
                            (sword_end_x, sword_end_y), 2)
            pygame.draw.line(surface,
                            (*_NS_astraelion.PALETTE["violet_light"], alpha),
                            (sword_start_x, sword_start_y),
                            (sword_end_x, sword_end_y), 1)

        # Speed lines.
        for i in range(6):
            line_y = y - 8 + i * 5
            line_x_start = x - 45 * facing
            line_x_end = x - 12 * facing
            alpha = _NS_astraelion._alpha(200 - i * 25)
            pygame.draw.line(surface,
                            (*_NS_astraelion.PALETTE["violet_light"], alpha),
                            (line_x_start, line_y), (line_x_end, line_y), 2)
            pygame.draw.line(surface,
                            (*_NS_astraelion.PALETTE["violet_shine"], alpha),
                            (line_x_start, line_y), (line_x_end, line_y), 1)

        # Stars burst effect.
        for i in range(10):
            angle = i * math.pi / 5 + phase
            r = 20 + int(math.sin(phase * 2 + i) * 5)
            sx = x + int(math.cos(angle) * r)
            sy = y + int(math.sin(angle) * r * 0.5)
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_hot"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["white"], (sx, sy, 1, 1))

    # ============================================================
    # SKILL: R - ZERO RETURN (multi-slash ultimate)
    # ============================================================
    def _draw_zeroreturn_ground(surface, boss, x, y, timer, phase):
        """Bright ring around boss (ultimate mode)."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 3) * 0.3 + 0.7

        for i in range(3):
            r = int(38 + i * 6 + math.sin(phase * 2) * 3)
            alpha = _NS_astraelion._alpha(220 - i * 50)
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["violet_mid"], alpha),
                                    (x, y + 40), r, 2)
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["violet_light"], alpha),
                                    (x, y + 40), r, 1)

        # 8-point rune stars around ring.
        for i in range(8):
            angle = phase * 0.8 + i * math.pi / 4
            rx = x + int(math.cos(angle) * 40)
            ry = y + 40 + int(math.sin(angle) * 14)
            # Star.
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_hot"], (rx, ry, 3, 3))
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["violet_shine"], (rx, ry, 2, 2))
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["white"], (rx, ry, 1, 1))

    def _draw_zeroreturn_foreground(surface, boss, x, y, timer, phase):
        """Multiple energy swords orbiting + aura amplification."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        tx, ty = _NS_astraelion._target_position(boss, x, y)

        # Aura around boss (bright violet).
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        aura_r = int(45 * pulse)
        for r in range(aura_r, 5, -3):
            alpha = _NS_astraelion._alpha(150 * (aura_r - r) / aura_r * pulse)
            _NS_astraelion._aacircle(surface, (*_NS_astraelion.PALETTE["violet_mid"], alpha),
                                    (x, y - 4), r)

        # 6 orbiting energy swords around boss.
        num_swords = 6
        for i in range(num_swords):
            sword_angle = phase * 1.5 + i * math.pi * 2 / num_swords
            orbit_r = 45 + int(math.sin(phase * 2 + i) * 3)
            sw_center_x = x + int(math.cos(sword_angle) * orbit_r)
            sw_center_y = y - 4 + int(math.sin(sword_angle) * orbit_r * 0.6)

            # Sword pointing outward.
            sword_len = 14
            sword_wid = 3
            outward_angle = sword_angle
            sw_tip_x = sw_center_x + int(math.cos(outward_angle) * sword_len)
            sw_tip_y = sw_center_y + int(math.sin(outward_angle) * sword_len * 0.7)
            sw_tail_x = sw_center_x - int(math.cos(outward_angle) * sword_len // 2)
            sw_tail_y = sw_center_y - int(math.sin(outward_angle) * sword_len // 2 * 0.7)
            perp_o = outward_angle + math.pi / 2
            side_a = (sw_center_x + int(math.cos(perp_o) * sword_wid),
                      sw_center_y + int(math.sin(perp_o) * sword_wid))
            side_b = (sw_center_x - int(math.cos(perp_o) * sword_wid),
                      sw_center_y - int(math.sin(perp_o) * sword_wid))

            _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["violet_darkest"],
                                [(sw_tip_x, sw_tip_y), side_a,
                                 (sw_tail_x, sw_tail_y), side_b])
            _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["violet_dark"], [
                (sw_tip_x, sw_tip_y),
                (int((sw_tip_x + side_a[0]) / 2), int((sw_tip_y + side_a[1]) / 2)),
                (sw_tail_x, sw_tail_y),
                (int((sw_tip_x + side_b[0]) / 2), int((sw_tip_y + side_b[1]) / 2)),
            ])
            _NS_astraelion._poly(surface, _NS_astraelion.PALETTE["violet_mid"], [
                (sw_tip_x, sw_tip_y),
                (sw_center_x, sw_center_y),
                (sw_tail_x, sw_tail_y),
            ])
            # Bright edge.
            pygame.draw.line(surface, _NS_astraelion.PALETTE["violet_light"],
                            (sw_tail_x, sw_tail_y), (sw_tip_x, sw_tip_y), 1)
            pygame.draw.line(surface, _NS_astraelion.PALETTE["violet_shine"],
                            (sw_tail_x, sw_tail_y), (sw_tip_x, sw_tip_y), 1)
            # Bright tip.
            for r_glow in range(3, 0, -1):
                a = _NS_astraelion._alpha(140 * (3 - r_glow) / 3)
                _NS_astraelion._aacircle(surface,
                                        (*_NS_astraelion.PALETTE["violet_hot"], a),
                                        (sw_tip_x, sw_tip_y), r_glow)
            pygame.draw.rect(surface, _NS_astraelion.PALETTE["white"],
                            (sw_tip_x, sw_tip_y, 1, 1))

        # Rising star particles.
        for i in range(12):
            st_t = (phase * 0.8 + i * 0.08) % 1.0
            st_angle = i * math.pi / 6
            st_r = 35 + int(st_t * 20)
            stx = x + int(math.cos(st_angle) * st_r)
            sty = y - int(st_t * 25) + int(math.sin(st_angle) * st_r * 0.5)
            alpha = _NS_astraelion._alpha(230 * (1 - st_t))
            if alpha > 0:
                # 4-point star.
                pygame.draw.rect(surface, (*_NS_astraelion.PALETTE["violet_hot"], alpha),
                                (stx, sty, 2, 2))
                pygame.draw.rect(surface, (*_NS_astraelion.PALETTE["violet_light"], alpha),
                                (stx - 1, sty, 1, 1))
                pygame.draw.rect(surface, (*_NS_astraelion.PALETTE["violet_light"], alpha),
                                (stx + 1, sty, 1, 1))
                pygame.draw.rect(surface, (*_NS_astraelion.PALETTE["violet_light"], alpha),
                                (stx, sty - 1, 1, 1))
                pygame.draw.rect(surface, (*_NS_astraelion.PALETTE["violet_light"], alpha),
                                (stx, sty + 1, 1, 1))
                pygame.draw.rect(surface, (*_NS_astraelion.PALETTE["white"], alpha),
                                (stx, sty, 1, 1))

        # Cross-slash marks at target (multi-hits).
        if progress > 0.3:
            num_slashes = 5
            for i in range(num_slashes):
                slash_progress = max(0, min(1, (progress - 0.3) * num_slashes - i))
                if slash_progress <= 0:
                    continue
                slash_angle = i * math.pi / 3 + phase
                slash_x = tx + int(math.cos(slash_angle) * 20)
                slash_y = ty + int(math.sin(slash_angle) * 20)

                # Slash cross mark.
                slash_len = 12
                slash_a = slash_angle + math.pi / 4
                slash_e1 = (slash_x + int(math.cos(slash_a) * slash_len),
                            slash_y + int(math.sin(slash_a) * slash_len))
                slash_e2 = (slash_x - int(math.cos(slash_a) * slash_len),
                            slash_y - int(math.sin(slash_a) * slash_len))

                alpha = _NS_astraelion._alpha(240 * (1 - slash_progress * 0.5))
                for w, color_key in [
                    (4, "violet_darkest"),
                    (3, "violet_dark"),
                    (2, "violet_mid"),
                    (1, "violet_shine"),
                ]:
                    pygame.draw.line(surface,
                                    (*_NS_astraelion.PALETTE[color_key], alpha),
                                    slash_e1, slash_e2, w)

                # Star burst at slash origin.
                for r_burst in range(5, 0, -1):
                    a = _NS_astraelion._alpha(180 * (5 - r_burst) / 5 * (1 - slash_progress))
                    _NS_astraelion._aacircle(surface,
                                            (*_NS_astraelion.PALETTE["violet_hot"], a),
                                            (slash_x, slash_y), r_burst)
                pygame.draw.rect(surface, (*_NS_astraelion.PALETTE["white"], alpha),
                                (slash_x, slash_y, 1, 1))


# ====================================================================
# morvaenthir.py
# ====================================================================

# ====================================================================
# MORVAENTHIR - The Soul Reaper (Mini Boss - Necromancer Mage)
# ====================================================================


class _NS_morvaenthir:
    """Namespace morvaenthir - Necromancer soul reaper mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin (pale necromancer)
        "skin_darkest": (95, 90, 100),
        "skin_dark": (155, 150, 160),
        "skin_mid": (200, 195, 205),
        "skin_light": (230, 225, 235),
        "skin_shine": (250, 245, 250),

        # Silver-white hair (long)
        "hair_darkest": (60, 65, 75),
        "hair_dark": (110, 115, 130),
        "hair_mid": (170, 175, 190),
        "hair_light": (215, 220, 235),
        "hair_shine": (245, 250, 255),

        # Robe/cloak (very dark navy-black)
        "robe_darkest": (5, 8, 15),
        "robe_dark": (18, 25, 38),
        "robe_mid": (40, 55, 75),
        "robe_light": (75, 95, 120),
        "robe_edge": (120, 145, 175),

        # Gothic armor plates (dark with gold trim)
        "armor_darkest": (10, 15, 22),
        "armor_dark": (30, 40, 55),
        "armor_mid": (65, 80, 100),
        "armor_light": (115, 135, 160),

        # Gold trim
        "gold_dark": (85, 60, 20),
        "gold_mid": (170, 130, 50),
        "gold_light": (240, 200, 110),
        "gold_shine": (255, 245, 190),

        # SOUL MAGIC (teal-green mint - main magic)
        "soul_darkest": (5, 30, 30),
        "soul_dark": (15, 85, 85),
        "soul_mid": (40, 180, 175),
        "soul_light": (110, 240, 225),
        "soul_hot": (170, 255, 240),
        "soul_shine": (230, 255, 250),

        # Eyes (bright teal)
        "eye_socket": (5, 15, 15),
        "eye_dark": (10, 60, 65),
        "eye_mid": (50, 190, 185),
        "eye_light": (150, 250, 235),
        "eye_glow": (230, 255, 250),

        # Skull staff (aged bone)
        "bone_darkest": (50, 45, 30),
        "bone_dark": (95, 85, 60),
        "bone_mid": (160, 145, 105),
        "bone_light": (220, 205, 165),
        "bone_shine": (250, 240, 210),

        # Ghost/spirit color
        "ghost_dark": (30, 90, 90),
        "ghost_mid": (80, 180, 175),
        "ghost_light": (170, 235, 225),

        # Mist
        "mist_dark": (10, 30, 30),
        "mist_mid": (35, 90, 90),
        "mist_light": (110, 200, 195),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_morvaenthir._clamp(color)
        if _NS_morvaenthir.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_morvaenthir._clamp(color)
        if _NS_morvaenthir.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        pygame.draw.polygon(surface, _NS_morvaenthir._clamp(color), points)

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
    def draw_morvaenthir(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_morvaenthir._detect_moving(boss)
        _NS_morvaenthir._update_mor_attack_anim(boss)
        attacking = (
            getattr(boss, "_mvt_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_morvaenthir._draw_soul_aura(surface, x, y, pulse)
        _NS_morvaenthir._draw_ground_ring(surface, x, y + 52, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "e":
            _NS_morvaenthir._draw_essence_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morvaenthir._draw_shadowrealm_ground(surface, boss, x, y, skill_timer, pulse)

        # Body (floating).
        if attacking:
            _NS_morvaenthir._draw_mor_attack(surface, boss, x, y)
        elif moving:
            _NS_morvaenthir._draw_mor_float_move(surface, boss, x, y)
        else:
            _NS_morvaenthir._draw_mor_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_morvaenthir._draw_soulfragment(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_morvaenthir._draw_spiritbind(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_morvaenthir._draw_essence_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morvaenthir._draw_shadowrealm_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_mor_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_mvt_previous_timer", 0))
        active = bool(getattr(boss, "_mvt_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._mvt_attack_active = True
            boss._mvt_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._mvt_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._mvt_attack_frame = int(
                getattr(boss, "_mvt_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._mvt_attack_active = False
            boss._mvt_attack_frame = 0
            active = False

        boss._mvt_previous_timer = timer
        boss._mvt_attack_progress = (
            min(1.0, getattr(boss, "_mvt_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_mvt_last_x"):
            boss._mvt_last_x = boss.x
            boss._mvt_last_y = boss.y
            return False
        dx = abs(boss.x - boss._mvt_last_x)
        dy = abs(boss.y - boss._mvt_last_y)
        boss._mvt_last_x = boss.x
        boss._mvt_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS (FLOATING)
    # ============================================================
    def _draw_mor_idle(surface, boss, x, y):
        float_bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_morvaenthir._draw_shadow(surface, x, y + 54)
        _NS_morvaenthir._draw_soul_wisps(surface, x, y + 42, boss.pulse)
        _NS_morvaenthir._draw_mor_body(surface, x, y - 5 + float_bob,
                                       boss.direction, boss.pulse, "idle", 0)

    def _draw_mor_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.4
        float_bob = int(math.sin(phase * 0.9) * 5)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_morvaenthir._draw_shadow(surface, x + sway, y + 54)
        _NS_morvaenthir._draw_soul_wisps(surface, x + sway, y + 42, phase,
                                         trail=True, facing=boss.direction)
        _NS_morvaenthir._draw_mor_body(surface, x + sway, y - 7 + float_bob,
                                       boss.direction, phase, "move", 0)

    def _draw_mor_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_mvt_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_mvt_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Ranged mage casting motion (raise staff → cast → recovery)
        if progress < 0.35:
            t = progress / 0.35
            lift = int(t * 4)
            lunge = 0
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            lift = int(4 - t * 2)
            lunge = int(t * 4) * facing
        else:
            t = (progress - 0.6) / 0.4
            lift = int(2 * (1 - t))
            lunge = int(4 * (1 - t)) * facing

        float_bob = int(math.sin(boss.pulse * 0.5) * 3)
        _NS_morvaenthir._draw_shadow(surface, x + lunge, y + 54)
        _NS_morvaenthir._draw_soul_wisps(surface, x + lunge, y + 42, boss.pulse,
                                         intense=True)
        _NS_morvaenthir._draw_mor_body(surface, x + lunge, y - 5 - lift + float_bob,
                                       facing, boss.pulse, "attack", progress)
        _NS_morvaenthir._draw_soul_bolt(surface, boss, x + lunge,
                                        y - 5 - lift + float_bob, progress)

    # ============================================================
    # BODY (Necromancer with hood, staff, robe)
    # ============================================================
    def _draw_mor_body(surface, cx, cy, facing, phase, action, attack_progress):
        """Draw necromancer body."""
        # Hair back (long silver hair flowing behind).
        _NS_morvaenthir._draw_hair_back(surface, cx, cy - 12, facing, phase)

        # Robe bottom (trailing tatters - floating, no legs).
        _NS_morvaenthir._draw_robe_bottom(surface, cx, cy + 8, facing, phase)

        # Torso with gothic armor.
        _NS_morvaenthir._draw_mor_torso(surface, cx, cy, facing, phase)

        # Back arm.
        _NS_morvaenthir._draw_mor_arm_back(surface, cx, cy + 2, facing, phase,
                                           action, attack_progress)

        # Head + hood + face.
        _NS_morvaenthir._draw_mor_head(surface, cx, cy - 14, facing, phase)

        # Front arm holding staff.
        _NS_morvaenthir._draw_mor_arm_front(surface, cx, cy + 2, facing, phase,
                                            action, attack_progress)

        # Staff (large, with skull on top).
        _NS_morvaenthir._draw_skull_staff(surface, cx, cy, facing, phase, action,
                                          attack_progress)

    def _draw_hair_back(surface, cx, cy, facing, phase):
        """Long silver hair flowing behind."""
        sway = math.sin(phase * 0.5) * 3

        # Multiple hair strands.
        for strand_i in range(3):
            base_x = cx + (strand_i - 1) * 3
            base_y = cy + 4

            prev = (base_x, base_y)
            segments = 8
            for i in range(1, segments + 1):
                t = i / segments
                wave = math.sin(phase * 0.6 + strand_i + t * math.pi) * (2 + t * 2)
                seg_x = base_x + int(wave * 0.4)
                seg_y = base_y + int(t * 24)
                thickness = max(2, 5 - i // 2)

                _NS_morvaenthir._aaline(surface, _NS_morvaenthir.PALETTE["shadow_deep"],
                                       (prev[0] + 1, prev[1] + 1),
                                       (seg_x + 1, seg_y + 1), thickness + 1)
                _NS_morvaenthir._aaline(surface, _NS_morvaenthir.PALETTE["hair_darkest"],
                                       prev, (seg_x, seg_y), thickness)
                _NS_morvaenthir._aaline(surface, _NS_morvaenthir.PALETTE["hair_dark"],
                                       prev, (seg_x, seg_y), max(1, thickness - 1))
                _NS_morvaenthir._aaline(surface, _NS_morvaenthir.PALETTE["hair_mid"],
                                       (prev[0], prev[1] - 1),
                                       (seg_x, seg_y - 1), max(1, thickness - 2))
                if i < 5:
                    _NS_morvaenthir._aaline(surface, _NS_morvaenthir.PALETTE["hair_light"],
                                           (prev[0], prev[1] - 2),
                                           (seg_x, seg_y - 2), max(1, thickness - 3))
                prev = (seg_x, seg_y)

    def _draw_robe_bottom(surface, cx, cy, facing, phase):
        """Trailing dark robe below (no legs, floating)."""
        sway = math.sin(phase * 0.5) * 3

        # Robe silhouette (long and flowing).
        robe_shape = [
            (cx - 12, cy - 8),
            (cx - 15, cy - 2),
            (cx - 16, cy + 6),
            (cx - 14, cy + 14 + int(sway)),
            (cx - 10, cy + 20),
            (cx - 4, cy + 22),
            (cx + 4, cy + 22 - int(sway)),
            (cx + 10, cy + 20),
            (cx + 14, cy + 14 - int(sway)),
            (cx + 16, cy + 6),
            (cx + 15, cy - 2),
            (cx + 12, cy - 8),
        ]
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in robe_shape])
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["robe_darkest"], robe_shape)

        # Layered folds.
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["robe_dark"], [
            (cx - 11, cy - 7),
            (cx - 14, cy - 1),
            (cx - 15, cy + 6),
            (cx - 10, cy + 18),
            (cx - 2, cy + 20),
            (cx + 4, cy + 19),
            (cx + 10, cy + 16),
            (cx + 15, cy + 6),
            (cx + 14, cy - 1),
            (cx + 11, cy - 7),
        ])
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["robe_mid"], [
            (cx - 9, cy - 5),
            (cx - 12, cy),
            (cx - 12, cy + 8),
            (cx - 6, cy + 14),
            (cx + 6, cy + 14),
            (cx + 12, cy + 8),
            (cx + 12, cy),
            (cx + 9, cy - 5),
        ])

        # Vertical fold lines.
        for x_off in [-10, -5, 0, 5, 10]:
            fold_x = cx + x_off
            pygame.draw.line(surface, _NS_morvaenthir.PALETTE["robe_darkest"],
                            (fold_x, cy - 4), (fold_x - x_off // 3, cy + 18), 1)

        # Ragged bottom edges (tatters).
        tatter_positions = [
            (cx - 12, cy + 18, -1),
            (cx - 6, cy + 22, 0),
            (cx, cy + 22, 0),
            (cx + 6, cy + 22, 0),
            (cx + 12, cy + 18, 1),
        ]
        for tx, ty, tilt in tatter_positions:
            t_sway = math.sin(phase * 0.8 + tx * 0.1) * 1
            ty_actual = ty + int(t_sway)
            _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["robe_darkest"], [
                (tx, ty_actual - 2),
                (tx + 2 + tilt, ty_actual),
                (tx, ty_actual + 3),
                (tx - 2 + tilt, ty_actual),
            ])
            _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["robe_dark"], [
                (tx, ty_actual - 1),
                (tx + 1 + tilt, ty_actual),
                (tx, ty_actual + 2),
                (tx - 1 + tilt, ty_actual),
            ])

        # Gold trim at bottom edge.
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["gold_dark"],
                        (cx - 8, cy + 15), (cx + 8, cy + 15), 1)
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["gold_mid"],
                        (cx - 6, cy + 14), (cx + 6, cy + 14), 1)

        # SOUL WISPS escaping robe.
        for i in range(4):
            wisp_t = (phase * 0.6 + i * 0.25) % 1.0
            wx = cx - 8 + i * 6 + int(math.sin(phase + i) * 3)
            wy = cy + 18 - int(wisp_t * 12)
            alpha = _NS_morvaenthir._alpha(200 * (1 - wisp_t))
            if alpha > 0:
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_dark"], alpha),
                                         (wx, wy), 2)
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_mid"], alpha),
                                         (wx, wy - 1), 1)
                pygame.draw.rect(surface,
                                (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                                (wx, wy - 1, 1, 1))

    def _draw_mor_torso(surface, cx, cy, facing, phase):
        """Torso with gothic armor plate."""
        breath = math.sin(phase * 0.7) * 1

        # Torso silhouette (broad shoulders for male).
        torso_shape = [
            (cx - 10, cy - 6),
            (cx - 12, cy - 3),
            (cx - 11, cy + 3),
            (cx - 8, cy + 7),
            (cx + 8, cy + 7),
            (cx + 11, cy + 3),
            (cx + 12, cy - 3),
            (cx + 10, cy - 6),
            (cx + 6, cy - 8),
            (cx - 6, cy - 8),
        ]
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in torso_shape])
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["robe_darkest"], torso_shape)

        # Robe layers.
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["robe_dark"], [
            (cx - 9, cy - 5),
            (cx - 11, cy - 2),
            (cx - 10, cy + 2),
            (cx - 7, cy + 6),
            (cx + 7, cy + 6),
            (cx + 10, cy + 2),
            (cx + 11, cy - 2),
            (cx + 9, cy - 5),
            (cx + 5, cy - 7),
            (cx - 5, cy - 7),
        ])
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["robe_mid"], [
            (cx - 7, cy - 3),
            (cx - 9, cy),
            (cx - 8, cy + 4),
            (cx - 5, cy + 6),
            (cx + 5, cy + 6),
            (cx + 8, cy + 4),
            (cx + 9, cy),
            (cx + 7, cy - 3),
            (cx + 4, cy - 6),
            (cx - 4, cy - 6),
        ])

        # GOTHIC CHEST PLATE (dark armor with gold trim).
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["armor_darkest"], [
            (cx - 6, cy - 4),
            (cx - 8, cy - 1),
            (cx - 7, cy + 3),
            (cx - 4, cy + 6),
            (cx + 4, cy + 6),
            (cx + 7, cy + 3),
            (cx + 8, cy - 1),
            (cx + 6, cy - 4),
            (cx + 3, cy - 6),
            (cx - 3, cy - 6),
        ])
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["armor_dark"], [
            (cx - 5, cy - 3),
            (cx - 7, cy),
            (cx - 6, cy + 3),
            (cx - 3, cy + 5),
            (cx + 3, cy + 5),
            (cx + 6, cy + 3),
            (cx + 7, cy),
            (cx + 5, cy - 3),
            (cx + 2, cy - 5),
            (cx - 2, cy - 5),
        ])
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["armor_mid"], [
            (cx - 3, cy - 2),
            (cx - 5, cy + 1),
            (cx - 3, cy + 4),
            (cx + 3, cy + 4),
            (cx + 5, cy + 1),
            (cx + 3, cy - 2),
            (cx + 1, cy - 4),
            (cx - 1, cy - 4),
        ])

        # Gold trim edges.
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["gold_dark"],
                        (cx - 6, cy - 4), (cx - 8, cy - 1), 1)
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["gold_mid"],
                        (cx + 6, cy - 4), (cx + 8, cy - 1), 1)
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["gold_dark"],
                        (cx - 4, cy + 6), (cx + 4, cy + 6), 1)

        # Central emblem (soul emblem - glowing teal).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        emblem_y = cy + 1
        # Glow halo.
        for r in range(5, 0, -1):
            alpha = _NS_morvaenthir._alpha(160 * (5 - r) / 5 * pulse)
            _NS_morvaenthir._aacircle(surface,
                                     (*_NS_morvaenthir.PALETTE["soul_mid"], alpha),
                                     (cx, emblem_y), r)
        # Diamond shape.
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["gold_dark"], [
            (cx, emblem_y - 3),
            (cx - 2, emblem_y),
            (cx, emblem_y + 3),
            (cx + 2, emblem_y),
        ])
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["soul_dark"], [
            (cx, emblem_y - 2),
            (cx - 1, emblem_y),
            (cx, emblem_y + 2),
            (cx + 1, emblem_y),
        ])
        pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["soul_light"], (cx, emblem_y, 1, 1))
        pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["soul_shine"], (cx, emblem_y, 1, 1))
        pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["white"], (cx, emblem_y, 1, 1))

        # SHOULDER SPIKES (gothic armor accent).
        for side in [-1, 1]:
            sp_x = cx + side * 11
            sp_y = cy - 5
            # Spike base.
            _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["shadow_deep"], [
                (sp_x + 1, sp_y - 5 + 1),
                (sp_x - 2, sp_y + 1),
                (sp_x + 3, sp_y + 1),
            ])
            _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["armor_darkest"], [
                (sp_x, sp_y - 5),
                (sp_x - 2, sp_y),
                (sp_x + 3, sp_y),
            ])
            _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["armor_mid"], [
                (sp_x, sp_y - 5),
                (sp_x, sp_y),
                (sp_x + 2, sp_y),
            ])
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["gold_mid"],
                            (sp_x, sp_y - 4, 1, 1))
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["gold_shine"],
                            (sp_x, sp_y - 5, 1, 1))

            # Small ornament spikes.
            for spike_off in [-1, 1]:
                mini_x = sp_x + spike_off * 2
                mini_top = sp_y - 3
                pygame.draw.line(surface, _NS_morvaenthir.PALETTE["armor_darkest"],
                                (mini_x, sp_y), (mini_x, mini_top), 1)
                pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["gold_mid"],
                                (mini_x, mini_top, 1, 1))

    def _draw_mor_arm_back(surface, cx, cy, facing, phase, action, attack_progress):
        """Back arm."""
        sway = math.sin(phase * 0.4) * 1
        back_dir = -facing
        shoulder_x = cx + back_dir * 9
        shoulder_y = cy - 3
        elbow_x = shoulder_x + back_dir * 2
        elbow_y = shoulder_y + 5 + int(sway)
        hand_x = elbow_x - back_dir * 1
        hand_y = elbow_y + 6 + int(sway)

        # Shoulder pad.
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["shadow_deep"],
                                 (shoulder_x + 1, shoulder_y + 1), 3)
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["armor_darkest"],
                                 (shoulder_x, shoulder_y), 3)
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["armor_dark"],
                                 (shoulder_x, shoulder_y), 2)

        # Upper arm (dark sleeve).
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["shadow_deep"],
                        (shoulder_x + 1, shoulder_y + 1), (elbow_x + 1, elbow_y + 1), 3)
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["robe_darkest"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["robe_dark"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 2)
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["robe_mid"],
                        (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 1)

        # Forearm.
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["shadow_deep"],
                        (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 3)
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["robe_darkest"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 3)
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["robe_dark"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 2)

        # Hand.
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["skin_darkest"],
                                 (hand_x, hand_y), 2)
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["skin_dark"],
                                 (hand_x, hand_y), 1)

    def _draw_mor_arm_front(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm (holds staff, extended)."""
        sway = math.sin(phase * 0.4) * 1

        # Arm pose - staff hand extended forward.
        if action == "attack":
            if attack_progress < 0.35:
                # Raise arm.
                t = attack_progress / 0.35
                shoulder_angle = -0.3 - t * 0.4
                elbow_bend = 0.5 - t * 0.2
            elif attack_progress < 0.6:
                # Cast forward.
                t = (attack_progress - 0.35) / 0.25
                shoulder_angle = -0.7 + t * 0.7
                elbow_bend = 0.3 + t * 0.2
            else:
                t = (attack_progress - 0.6) / 0.4
                shoulder_angle = 0.0 - t * 0.1
                elbow_bend = 0.5 - t * 0.0
        else:
            shoulder_angle = -0.15 + math.sin(phase * 0.5) * 0.05
            elbow_bend = 0.5

        shoulder_x = cx + facing * 9
        shoulder_y = cy - 3
        upper_len = 6
        elbow_x = shoulder_x + int(math.cos(shoulder_angle) * upper_len) * facing
        elbow_y = shoulder_y + int(math.sin(shoulder_angle) * upper_len) + 2

        forearm_angle = shoulder_angle + elbow_bend
        forearm_len = 8
        hand_x = elbow_x + int(math.cos(forearm_angle) * forearm_len) * facing
        hand_y = elbow_y + int(math.sin(forearm_angle) * forearm_len) + 3

        # Shoulder pad.
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["shadow_deep"],
                                 (shoulder_x + 1, shoulder_y + 1), 3)
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["armor_darkest"],
                                 (shoulder_x, shoulder_y), 3)
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["armor_dark"],
                                 (shoulder_x, shoulder_y), 2)
        pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["gold_mid"],
                        (shoulder_x - facing, shoulder_y - 1, 1, 1))

        # Upper arm (dark sleeve).
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["shadow_deep"],
                        (shoulder_x + 1, shoulder_y + 1), (elbow_x + 1, elbow_y + 1), 3)
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["robe_darkest"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["robe_dark"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 2)
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["robe_mid"],
                        (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 1)

        # Forearm.
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["shadow_deep"],
                        (elbow_x + 1, elbow_y + 1), (hand_x + 1, hand_y + 1), 3)
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["robe_darkest"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 3)
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["robe_dark"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 2)

        # Gold cuff at wrist.
        wrap_x = (elbow_x + hand_x) // 2 + facing * 2
        wrap_y = (elbow_y + hand_y) // 2 + 1
        pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["gold_dark"],
                        (wrap_x - 1, wrap_y - 1, 3, 2))
        pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["gold_mid"],
                        (wrap_x, wrap_y - 1, 2, 1))

        # Hand (pale, gripping).
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["skin_darkest"],
                                 (hand_x, hand_y), 2)
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["skin_dark"],
                                 (hand_x, hand_y), 1)
        pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["skin_mid"], (hand_x, hand_y, 1, 1))

    def _draw_mor_head(surface, cx, cy, facing, phase):
        """Male necromancer face with long silver hair, teal eyes."""
        # Head shape.
        head_shape = [
            (cx - 5, cy - 1),
            (cx - 6, cy + 2),
            (cx - 5, cy + 6),
            (cx - 2, cy + 8),
            (cx + 2, cy + 8),
            (cx + 5, cy + 6),
            (cx + 6, cy + 2),
            (cx + 5, cy - 1),
            (cx + 3, cy - 4),
            (cx - 3, cy - 4),
        ]
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["shadow_deep"],
                             [(px + 2, py + 2) for px, py in head_shape])
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["skin_darkest"], head_shape)

        # Skin base.
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["skin_dark"], [
            (cx - 4, cy),
            (cx - 5, cy + 2),
            (cx - 4, cy + 6),
            (cx - 2, cy + 7),
            (cx + 2, cy + 7),
            (cx + 4, cy + 6),
            (cx + 5, cy + 2),
            (cx + 4, cy),
            (cx + 2, cy - 3),
            (cx - 2, cy - 3),
        ])
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["skin_mid"], [
            (cx - 3, cy + 1),
            (cx - 4, cy + 3),
            (cx - 3, cy + 5),
            (cx + 3, cy + 5),
            (cx + 4, cy + 3),
            (cx + 3, cy + 1),
            (cx + 2, cy - 2),
            (cx - 2, cy - 2),
        ])
        pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["skin_light"], (cx, cy + 2, 1, 1))

        # HAIR TOP (silver-white, center part).
        _NS_morvaenthir._draw_hair_top(surface, cx, cy, facing, phase)

        # TEAL EYES.
        _NS_morvaenthir._draw_teal_eyes(surface, cx, cy + 2, facing, phase)

        # Nose.
        pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["skin_darkest"], (cx, cy + 4, 1, 1))

        # Serious mouth line.
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["skin_darkest"],
                        (cx - 1, cy + 6), (cx + 1, cy + 6), 1)

        # Small beard/stubble.
        pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["hair_darkest"],
                        (cx - 1, cy + 7, 1, 1))
        pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["hair_darkest"],
                        (cx + 1, cy + 7, 1, 1))

    def _draw_hair_top(surface, cx, cy, facing, phase):
        """Silver hair top with center part and side strands."""
        # Top hair shape.
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["shadow_deep"], [
            (cx - 6, cy - 1),
            (cx - 7, cy + 2),
            (cx - 6, cy + 4),
            (cx - 4, cy + 1),
            (cx - 2, cy - 3),
            (cx + 2, cy - 3),
            (cx + 4, cy + 1),
            (cx + 6, cy + 4),
            (cx + 7, cy + 2),
            (cx + 6, cy - 1),
            (cx + 4, cy - 4),
            (cx - 4, cy - 4),
        ])
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["hair_darkest"], [
            (cx - 6, cy - 1),
            (cx - 7, cy + 1),
            (cx - 5, cy + 1),
            (cx - 3, cy - 2),
            (cx + 3, cy - 2),
            (cx + 5, cy + 1),
            (cx + 7, cy + 1),
            (cx + 6, cy - 1),
            (cx + 4, cy - 4),
            (cx - 4, cy - 4),
        ])
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["hair_dark"], [
            (cx - 5, cy - 1),
            (cx - 6, cy),
            (cx - 4, cy),
            (cx - 2, cy - 2),
            (cx + 2, cy - 2),
            (cx + 4, cy),
            (cx + 6, cy),
            (cx + 5, cy - 1),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ])
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["hair_mid"], [
            (cx - 3, cy - 1),
            (cx - 2, cy - 2),
            (cx + 2, cy - 2),
            (cx + 3, cy - 1),
            (cx + 2, cy - 3),
            (cx - 2, cy - 3),
        ])
        # Center part.
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["hair_darkest"],
                        (cx, cy - 3), (cx, cy - 1), 1)
        # Highlight.
        pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["hair_light"], (cx - 1, cy - 3, 1, 1))
        pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["hair_shine"], (cx + 1, cy - 3, 1, 1))

        # Side hair strands going down.
        for side in [-1, 1]:
            sway = math.sin(phase * 0.5 + side) * 1
            bang_x = cx + side * 5
            pygame.draw.line(surface, _NS_morvaenthir.PALETTE["hair_darkest"],
                            (bang_x, cy - 1), (bang_x, cy + 6 + int(sway)), 2)
            pygame.draw.line(surface, _NS_morvaenthir.PALETTE["hair_dark"],
                            (bang_x, cy - 1), (bang_x, cy + 6 + int(sway)), 1)
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["hair_mid"],
                            (bang_x - side, cy + 1, 1, 1))
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["hair_light"],
                            (bang_x, cy + 3 + int(sway), 1, 1))

    def _draw_teal_eyes(surface, cx, cy, facing, phase):
        """Glowing teal eyes."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7

        for side in [-1, 1]:
            ex = cx + side * 2
            ey = cy

            # Socket.
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["eye_socket"],
                            (ex - 1, ey - 1, 2, 2))

            # Glow halo.
            for r in range(4, 0, -1):
                alpha = _NS_morvaenthir._alpha(140 * (4 - r) / 4 * pulse)
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["eye_mid"], alpha),
                                         (ex, ey), r)

            # Iris.
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["eye_dark"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["eye_mid"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["eye_light"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["eye_glow"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["white"], (ex, ey, 1, 1))

    def _draw_skull_staff(surface, cx, cy, facing, phase, action, attack_progress):
        """Large staff with skull and teal fire on top."""
        # Determine staff angle - always pointing up.
        base_angle = -math.pi / 2 - 0.1 * facing
        # Slight animation.
        if action == "attack":
            if attack_progress < 0.35:
                base_angle -= (attack_progress / 0.35) * 0.3 * facing
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                base_angle -= (0.3 - t * 0.5) * facing
            else:
                t = (attack_progress - 0.6) / 0.4
                base_angle -= (-0.2 * (1 - t)) * facing

        staff_length = 42
        base_x = cx + facing * 12
        base_y = cy + 8
        tip_x = base_x + int(math.cos(base_angle) * staff_length)
        tip_y = base_y + int(math.sin(base_angle) * staff_length)

        # Staff shaft (dark wood with gold).
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["shadow_deep"],
                        (base_x + 2, base_y + 2), (tip_x + 2, tip_y + 2), 4)
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["armor_darkest"],
                        (base_x, base_y), (tip_x, tip_y), 3)
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["armor_dark"],
                        (base_x, base_y), (tip_x, tip_y), 2)
        pygame.draw.line(surface, _NS_morvaenthir.PALETTE["armor_mid"],
                        (base_x, base_y), (tip_x, tip_y), 1)

        # Gold segment wraps.
        for t_seg in [0.2, 0.45, 0.7]:
            seg_x = int(base_x + (tip_x - base_x) * t_seg)
            seg_y = int(base_y + (tip_y - base_y) * t_seg)
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["gold_dark"],
                            (seg_x - 1, seg_y - 1, 3, 3))
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["gold_mid"],
                            (seg_x, seg_y - 1, 2, 2))
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["gold_shine"],
                            (seg_x, seg_y, 1, 1))

        # SKULL AT TIP.
        skull_x = tip_x + int(math.cos(base_angle) * 6)
        skull_y = tip_y + int(math.sin(base_angle) * 6)
        _NS_morvaenthir._draw_staff_skull(surface, skull_x, skull_y, phase, action,
                                          attack_progress)

        # Handle end (small orb at base).
        end_x = base_x - int(math.cos(base_angle) * 3)
        end_y = base_y - int(math.sin(base_angle) * 3)
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["armor_darkest"],
                                 (end_x, end_y), 3)
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["gold_dark"],
                                 (end_x, end_y), 2)
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_mid"],
                                 (end_x, end_y), 1)

    def _draw_staff_skull(surface, cx, cy, phase, action, attack_progress):
        """Skull ornament on top of staff with teal flames."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Extra glow during casting.
        boost = 1.0
        if action == "attack" and 0.15 < attack_progress < 0.65:
            boost = 1.6

        # BIG GLOW AURA around skull.
        for r in range(14, 0, -1):
            alpha = _NS_morvaenthir._alpha(140 * (14 - r) / 14 * pulse * boost)
            _NS_morvaenthir._aacircle(surface,
                                     (*_NS_morvaenthir.PALETTE["soul_mid"], alpha),
                                     (cx, cy - 1), r)

        # Skull base shape.
        skull_shape = [
            (cx - 4, cy - 2),
            (cx - 5, cy),
            (cx - 4, cy + 2),
            (cx - 2, cy + 4),
            (cx + 2, cy + 4),
            (cx + 4, cy + 2),
            (cx + 5, cy),
            (cx + 4, cy - 2),
            (cx + 3, cy - 4),
            (cx - 3, cy - 4),
        ]
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["shadow_deep"],
                             [(px + 1, py + 1) for px, py in skull_shape])
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["bone_darkest"], skull_shape)
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["bone_dark"], [
            (cx - 3, cy - 1),
            (cx - 4, cy),
            (cx - 3, cy + 2),
            (cx - 1, cy + 3),
            (cx + 1, cy + 3),
            (cx + 3, cy + 2),
            (cx + 4, cy),
            (cx + 3, cy - 1),
            (cx + 2, cy - 3),
            (cx - 2, cy - 3),
        ])
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["bone_mid"], [
            (cx - 2, cy),
            (cx - 3, cy + 1),
            (cx - 2, cy + 2),
            (cx + 2, cy + 2),
            (cx + 3, cy + 1),
            (cx + 2, cy),
            (cx + 1, cy - 2),
            (cx - 1, cy - 2),
        ])
        _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["bone_light"], [
            (cx - 1, cy),
            (cx - 1, cy + 1),
            (cx + 1, cy + 1),
            (cx + 1, cy),
        ])

        # Eye sockets (glowing teal).
        for side in [-1, 1]:
            ex = cx + side * 2
            ey = cy - 1
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["shadow"],
                            (ex - 1, ey - 1, 2, 2))
            for r in range(3, 0, -1):
                alpha = _NS_morvaenthir._alpha(220 * (3 - r) / 3 * pulse * boost)
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                                         (ex, ey), r)
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["soul_hot"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["white"], (ex, ey, 1, 1))

        # Nose hole.
        pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["shadow"], (cx, cy + 1, 1, 1))

        # Teeth (small marks at bottom).
        for x_off in [-2, -1, 0, 1, 2]:
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["shadow"],
                            (cx + x_off, cy + 3, 1, 1))
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["bone_dark"],
                            (cx + x_off, cy + 3, 1, 1))

        # TEAL FLAMES rising from skull top.
        for i in range(4):
            flame_t = (phase * 1.2 + i * 0.25) % 1.0
            flame_x = cx + (i - 1) * 2 + int(math.sin(phase * 3 + i) * 1)
            flame_y = cy - 4 - int(flame_t * 8)
            flame_size = int(3 * (1 - flame_t))
            alpha = _NS_morvaenthir._alpha(240 * (1 - flame_t) * boost)
            if alpha > 0 and flame_size > 0:
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_dark"], alpha),
                                         (flame_x, flame_y), flame_size + 1)
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_mid"], alpha),
                                         (flame_x, flame_y), flame_size)
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                                         (flame_x, flame_y - 1), max(1, flame_size - 1))
                pygame.draw.rect(surface,
                                (*_NS_morvaenthir.PALETTE["soul_shine"], alpha),
                                (flame_x, flame_y, 1, 1))

        # Curved bone horns/spikes on sides.
        for side in [-1, 1]:
            horn_base_x = cx + side * 4
            horn_base_y = cy - 3
            horn_tip_x = horn_base_x + side * 3
            horn_tip_y = horn_base_y - 5

            _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["shadow_deep"], [
                (horn_tip_x + 1, horn_tip_y + 1),
                (horn_base_x + 1, horn_base_y + 1),
                (horn_base_x + side + 1, horn_base_y + 1),
            ])
            _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["bone_darkest"], [
                (horn_tip_x, horn_tip_y),
                (horn_base_x, horn_base_y),
                (horn_base_x + side, horn_base_y),
            ])
            _NS_morvaenthir._poly(surface, _NS_morvaenthir.PALETTE["bone_mid"], [
                (horn_tip_x, horn_tip_y),
                (horn_base_x, horn_base_y),
            ])
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["bone_light"],
                            (horn_tip_x, horn_tip_y, 1, 1))

        # Sparkles around skull.
        for i in range(4):
            sp_angle = phase * 2 + i * math.pi / 2
            sp_x = cx + int(math.cos(sp_angle) * 8)
            sp_y = cy - 1 + int(math.sin(sp_angle) * 8)
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["soul_hot"], (sp_x, sp_y, 1, 1))
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["white"], (sp_x, sp_y, 1, 1))

    # ============================================================
    # BASIC ATTACK — Soul bolt projectile
    # ============================================================
    def _draw_soul_bolt(surface, boss, x, y, progress):
        """Teal soul bolt projectile."""
        if progress < 0.55:
            return

        facing = boss.direction
        tx, ty = _NS_morvaenthir._target_position(boss, x, y)

        # Launch from skull staff tip.
        start_x = x + facing * 26
        start_y = y - 32

        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Trail (soul essence).
        for i in range(9):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_morvaenthir._alpha(220 - i * 22)
            size = max(1, 6 - i)
            _NS_morvaenthir._aacircle(surface,
                                     (*_NS_morvaenthir.PALETTE["soul_darkest"], alpha),
                                     (px, py), size)
            _NS_morvaenthir._aacircle(surface,
                                     (*_NS_morvaenthir.PALETTE["soul_dark"], alpha),
                                     (px, py), max(1, size - 1))
            _NS_morvaenthir._aacircle(surface,
                                     (*_NS_morvaenthir.PALETTE["soul_mid"], alpha),
                                     (px, py), max(1, size - 2))
            _NS_morvaenthir._aacircle(surface,
                                     (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                                     (px, py), max(1, size - 3))

            if i < 4:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 6 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 6 + i + s) * (size + 1))
                    pygame.draw.rect(surface,
                                    (*_NS_morvaenthir.PALETTE["soul_hot"], alpha),
                                    (spark_x, spark_y, 1, 1))

        # Bright bolt head.
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_darkest"],
                                 (bx, by), 8)
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_dark"],
                                 (bx, by), 6)
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_mid"],
                                 (bx, by), 4)
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_light"],
                                 (bx, by), 3)
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_hot"],
                                 (bx, by), 2)
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_shine"],
                                 (bx, by), 1)
        pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["white"], (bx, by, 1, 1))

        # Radial glow.
        for r in range(12, 3, -2):
            alpha = _NS_morvaenthir._alpha(80 * (12 - r) / 12)
            _NS_morvaenthir._aacircle(surface,
                                     (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                                     (bx, by), r)

        # Impact.
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(8 + st * 22)
            alpha = _NS_morvaenthir._alpha(240 * (1 - st))
            _NS_morvaenthir._aacircle(surface,
                                     (*_NS_morvaenthir.PALETTE["soul_darkest"], alpha),
                                     (tx, ty), radius + 3, 3)
            _NS_morvaenthir._aacircle(surface,
                                     (*_NS_morvaenthir.PALETTE["soul_dark"], alpha),
                                     (tx, ty), radius, 3)
            _NS_morvaenthir._aacircle(surface,
                                     (*_NS_morvaenthir.PALETTE["soul_mid"], alpha),
                                     (tx, ty), max(1, radius - 4), 2)
            _NS_morvaenthir._aacircle(surface,
                                     (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                                     (tx, ty), max(1, radius - 10), 1)
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface,
                                (*_NS_morvaenthir.PALETTE["soul_hot"], alpha),
                                (ex, ey, 2, 2))

    # ============================================================
    # FLOATING SOUL WISPS
    # ============================================================
    def _draw_soul_wisps(surface, cx, cy, phase, trail=False, facing=1,
                         intense=False):
        """Floating soul wisps below (teal ghost fires)."""
        strength = 1.5 if intense else 1.0

        # Ground glow.
        glow = pygame.Surface((120, 30), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for r in range(26, 3, -2):
            alpha = _NS_morvaenthir._alpha((26 - r) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(glow, (*_NS_morvaenthir.PALETTE["mist_dark"], alpha),
                                    (60 - r * 2, 15 - r // 3, r * 4, max(3, r // 2)))
        for r in range(18, 3, -2):
            alpha = _NS_morvaenthir._alpha((18 - r) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(glow, (*_NS_morvaenthir.PALETTE["mist_mid"], alpha),
                                    (60 - r, 15 - r // 4, r * 2, max(2, r // 3)))
        surface.blit(glow, (cx - 60, cy - 8))

        # Rising soul wisps.
        for i, offset in enumerate([-20, -12, -4, 4, 12, 20]):
            t = (phase * 0.5 + i * 0.15) % 1.0
            wx = cx + offset + int(math.sin(phase * 2 + i) * 3)
            wy = cy + 4 - int(t * 24)
            alpha = _NS_morvaenthir._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_morvaenthir._aacircle(surface,
                                     (*_NS_morvaenthir.PALETTE["mist_dark"], alpha),
                                     (wx, wy), 3)
            _NS_morvaenthir._aacircle(surface,
                                     (*_NS_morvaenthir.PALETTE["mist_mid"], alpha),
                                     (wx, wy - 1), 2)
            pygame.draw.rect(surface, (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                            (wx, wy - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_morvaenthir.PALETTE["soul_hot"], alpha),
                            (wx, wy - 2, 1, 1))

        # Small ghost silhouettes floating.
        for i in range(3):
            gh_t = (phase * 0.4 + i * 0.33) % 1.0
            gx = cx - 15 + i * 15 + int(math.sin(phase + i) * 4)
            gy = cy + 8 - int(gh_t * 28)
            alpha = _NS_morvaenthir._alpha(200 * (1 - gh_t) * strength)
            if alpha > 0 and 0 < gy < 40:
                # Small ghost shape.
                _NS_morvaenthir._poly(surface,
                                     (*_NS_morvaenthir.PALETTE["ghost_dark"], alpha), [
                                         (gx, gy - 4),
                                         (gx - 2, gy - 2),
                                         (gx - 2, gy + 2),
                                         (gx - 1, gy + 3),
                                         (gx, gy + 2),
                                         (gx + 1, gy + 3),
                                         (gx + 2, gy + 2),
                                         (gx + 2, gy - 2),
                                     ])
                _NS_morvaenthir._poly(surface,
                                     (*_NS_morvaenthir.PALETTE["ghost_mid"], alpha), [
                                         (gx, gy - 3),
                                         (gx - 1, gy - 1),
                                         (gx - 1, gy + 1),
                                         (gx + 1, gy + 1),
                                         (gx + 1, gy - 1),
                                     ])
                # Ghost eyes.
                pygame.draw.rect(surface,
                                (*_NS_morvaenthir.PALETTE["shadow"], alpha),
                                (gx - 1, gy - 2, 1, 1))
                pygame.draw.rect(surface,
                                (*_NS_morvaenthir.PALETTE["shadow"], alpha),
                                (gx + 1, gy - 2, 1, 1))
                pygame.draw.rect(surface,
                                (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                                (gx - 1, gy - 2, 1, 1))
                pygame.draw.rect(surface,
                                (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                                (gx + 1, gy - 2, 1, 1))

        # Sparkle stars.
        for i in range(10):
            spark_t = (phase * 0.7 + i * 0.1) % 1.0
            sx = cx - 22 + i * 5 + int(math.sin(phase + i) * 3)
            sy = cy + 2 - int(spark_t * 22)
            alpha = _NS_morvaenthir._alpha(240 * (1 - spark_t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_morvaenthir.PALETTE["soul_mid"], alpha),
                                (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_morvaenthir.PALETTE["soul_hot"], alpha),
                                (sx, sy, 1, 1))

        # Trail behind.
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_morvaenthir._alpha(170 - i * 25)
                if alpha <= 0:
                    continue
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["mist_dark"], alpha),
                                         (sx, sy), max(2, 6 - i))
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["mist_mid"], alpha),
                                         (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface, (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                                (sx, sy - 1, 2, 2))

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((130, 28), pygame.SRCALPHA)
        for r in range(13, 0, -1):
            alpha = max(0, (13 - r) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (12 - r, 14 - r, 106 + r * 2, r * 2))
        pygame.draw.ellipse(shadow, (2, 5, 5, 170), (5, 6, 120, 14))
        pygame.draw.ellipse(shadow, (15, 55, 55, 110), (13, 8, 104, 10))
        surface.blit(shadow, (x - 65, y - 14))

    def _draw_soul_aura(surface, x, y, phase):
        """Teal soul aura around necromancer."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((200, 170), pygame.SRCALPHA)
        for r in range(85, 5, -5):
            alpha = _NS_morvaenthir._alpha((85 - r) * 1.2 * pulse)
            if alpha > 0:
                _NS_morvaenthir._aacircle(aura,
                                         (*_NS_morvaenthir.PALETTE["mist_dark"], alpha),
                                         (100, 85), r)
        for r in range(55, 5, -4):
            alpha = _NS_morvaenthir._alpha((55 - r) * 1.4 * pulse)
            if alpha > 0:
                _NS_morvaenthir._aacircle(aura,
                                         (*_NS_morvaenthir.PALETTE["mist_mid"], alpha),
                                         (100, 85), r)
        for r in range(32, 5, -3):
            alpha = _NS_morvaenthir._alpha((32 - r) * 1.4 * pulse)
            if alpha > 0:
                _NS_morvaenthir._aacircle(aura,
                                         (*_NS_morvaenthir.PALETTE["soul_darkest"], alpha),
                                         (100, 85), r)
        surface.blit(aura, (x - 100, y - 85))

        # Floating soul embers.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 34 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["soul_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["soul_hot"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["white"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring with soul runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 48), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_morvaenthir.PALETTE["mist_dark"], 200),
                            (5, 15, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_morvaenthir.PALETTE["soul_darkest"], 220),
                            (12, 17, 136, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_morvaenthir.PALETTE["soul_dark"], 230),
                            (22, 19, 116, 16), 1)
        pygame.draw.ellipse(ring, (*_NS_morvaenthir.PALETTE["ghost_dark"], 180),
                            (35, 21, 90, 12), 1)

        # Runes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 27 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 62)
            y2 = 27 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_morvaenthir.PALETTE["soul_light"], 220),
                            (x1, y1), (x2, y2), 1)

        # Star runes.
        for i in range(5):
            angle = phase * 0.3 + i * math.pi / 2.5 + math.pi / 5
            sx = 80 + int(math.cos(angle) * 55)
            sy = 27 + int(math.sin(angle) * 9)
            pygame.draw.rect(ring, (*_NS_morvaenthir.PALETTE["soul_hot"], 240),
                            (sx, sy, 2, 2))
            pygame.draw.rect(ring, (*_NS_morvaenthir.PALETTE["soul_shine"], 240),
                            (sx, sy, 1, 1))

        if skill:
            pygame.draw.ellipse(ring, (*_NS_morvaenthir.PALETTE["soul_hot"],
                                       _NS_morvaenthir._alpha(150 * pulse)),
                                (14, 10, 132, 34), 1)
        surface.blit(ring, (x - 80, y - 24))

    # ============================================================
    # SKILL: Q - SOUL FRAGMENT (bright teal spirit shard)
    # ============================================================
    def _draw_soulfragment(surface, boss, x, y, timer, phase):
        """Larger, brighter soul fragment projectile."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morvaenthir._target_position(boss, x, y)

        if progress < 0.2:
            # Charge in staff tip.
            t = progress / 0.2
            charge_x = x + facing * 26
            charge_y = y - 32
            cr = int(4 + t * 8)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_morvaenthir._alpha(200 * (cr + 6 - r) / (cr + 6))
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_darkest"], alpha),
                                         (charge_x, charge_y), r)
            for r in range(cr + 3, 0, -1):
                alpha = _NS_morvaenthir._alpha(220 * (cr + 3 - r) / (cr + 3))
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_dark"], alpha),
                                         (charge_x, charge_y), r)
            _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_mid"],
                                     (charge_x, charge_y), cr - 2)
            _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_light"],
                                     (charge_x, charge_y), max(1, cr - 4))
            _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_shine"],
                                     (charge_x, charge_y), max(1, cr - 6))

            # Sparks.
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                sx = charge_x + int(math.cos(angle) * (cr + 3))
                sy = charge_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["soul_hot"], (sx, sy, 1, 1))
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 26
            start_y = y - 32
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Long bright comet trail.
            for i in range(12):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_morvaenthir._alpha(240 - i * 20)
                size = max(1, 9 - i)
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_darkest"], alpha),
                                         (px, py), size)
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_dark"], alpha),
                                         (px, py), max(1, size - 1))
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_mid"], alpha),
                                         (px, py), max(1, size - 2))
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                                         (px, py), max(1, size - 3))

                if i < 5:
                    for s in range(3):
                        spark_angle = t * 8 + i + s
                        spark_x = px + int(math.sin(spark_angle) * (size + 2))
                        spark_y = py + int(math.cos(spark_angle) * (size + 2))
                        pygame.draw.rect(surface,
                                        (*_NS_morvaenthir.PALETTE["soul_hot"], alpha),
                                        (spark_x, spark_y, 1, 1))

            # Huge bright head.
            for r in range(15, 3, -2):
                alpha = _NS_morvaenthir._alpha(100 * (15 - r) / 15)
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                                         (bx, by), r)
            _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_darkest"],
                                     (bx, by), 10)
            _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_dark"],
                                     (bx, by), 8)
            _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_mid"],
                                     (bx, by), 5)
            _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_light"],
                                     (bx, by), 3)
            _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_shine"],
                                     (bx, by), 1)
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["white"], (bx, by, 1, 1))

            # Impact.
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(12 + st * 28)
                alpha = _NS_morvaenthir._alpha(240 * (1 - st))
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_darkest"], alpha),
                                         (tx, ty), radius + 4, 3)
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_dark"], alpha),
                                         (tx, ty), radius, 3)
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_mid"], alpha),
                                         (tx, ty), max(1, radius - 5), 2)
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                                         (tx, ty), max(1, radius - 12), 1)
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface,
                                    (*_NS_morvaenthir.PALETTE["soul_hot"], alpha),
                                    (ex, ey, 2, 2))

    # ============================================================
    # SKILL: W - SPIRIT BIND (chain link to target)
    # ============================================================
    def _draw_spiritbind(surface, boss, x, y, timer, phase):
        """Chain of soul energy binding boss to target."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morvaenthir._target_position(boss, x, y)

        # Link from staff tip to target.
        start_x = x + facing * 26
        start_y = y - 32

        # Chain grows to target quickly.
        chain_progress = min(1.0, progress * 3)

        # Draw chain as segments (like beads).
        segments = 15
        for i in range(segments):
            t = i / segments
            if t > chain_progress:
                break
            # Wavy path.
            wave = math.sin(t * math.pi * 3 + phase * 2) * 4 * (1 - abs(t - 0.5) * 2)
            perp_angle = math.atan2(ty - start_y, tx - start_x) + math.pi / 2
            perp_x = math.cos(perp_angle)
            perp_y = math.sin(perp_angle)

            px = int(start_x + (tx - start_x) * t + perp_x * wave)
            py = int(start_y + (ty - start_y) * t + perp_y * wave)

            # Chain bead.
            _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["shadow_deep"],
                                     (px + 1, py + 1), 4)
            _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_darkest"],
                                     (px, py), 4)
            _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_dark"],
                                     (px, py), 3)
            _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_mid"],
                                     (px, py), 2)
            _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_light"],
                                     (px, py), 1)
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["soul_shine"], (px, py, 1, 1))

        # Connecting energy line between beads.
        for i in range(segments - 1):
            t1 = i / segments
            t2 = (i + 1) / segments
            if t1 > chain_progress:
                break
            wave1 = math.sin(t1 * math.pi * 3 + phase * 2) * 4 * (1 - abs(t1 - 0.5) * 2)
            wave2 = math.sin(t2 * math.pi * 3 + phase * 2) * 4 * (1 - abs(t2 - 0.5) * 2)
            perp_angle = math.atan2(ty - start_y, tx - start_x) + math.pi / 2
            perp_x = math.cos(perp_angle)
            perp_y = math.sin(perp_angle)

            p1x = int(start_x + (tx - start_x) * t1 + perp_x * wave1)
            p1y = int(start_y + (ty - start_y) * t1 + perp_y * wave1)
            p2x = int(start_x + (tx - start_x) * t2 + perp_x * wave2)
            p2y = int(start_y + (ty - start_y) * t2 + perp_y * wave2)

            pygame.draw.line(surface, _NS_morvaenthir.PALETTE["soul_dark"],
                            (p1x, p1y), (p2x, p2y), 3)
            pygame.draw.line(surface, _NS_morvaenthir.PALETTE["soul_mid"],
                            (p1x, p1y), (p2x, p2y), 2)
            pygame.draw.line(surface, _NS_morvaenthir.PALETTE["soul_light"],
                            (p1x, p1y), (p2x, p2y), 1)

        # Ring around target (bound).
        if chain_progress >= 0.9:
            pulse = math.sin(phase * 3) * 0.3 + 0.7
            for i in range(2):
                r = int(20 + i * 4 + math.sin(phase * 2) * 2)
                alpha = _NS_morvaenthir._alpha(220 * pulse - i * 50)
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_mid"], alpha),
                                         (tx, ty), r, 2)
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                                         (tx, ty), r, 1)

            # Runic circle under target.
            for i in range(8):
                angle = phase * 0.8 + i * math.pi / 4
                rx = tx + int(math.cos(angle) * 22)
                ry = ty + int(math.sin(angle) * 8)
                pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["soul_hot"], (rx, ry, 2, 2))
                pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["soul_shine"], (rx, ry, 1, 1))

            # Vertical energy pillar on target.
            for layer_i, (width, alpha_val) in enumerate([
                (8, 100), (5, 140), (2, 200), (1, 240),
            ]):
                actual_alpha = _NS_morvaenthir._alpha(alpha_val * pulse)
                pygame.draw.rect(surface,
                                (*_NS_morvaenthir.PALETTE["soul_mid"], actual_alpha),
                                (tx - width // 2, ty - 40, width, 40))
            # Rising sparks on pillar.
            for i in range(6):
                sp_t = (phase * 2 + i * 0.16) % 1.0
                sp_y = ty - int(sp_t * 40)
                sp_x = tx + int(math.sin(phase * 3 + i) * 3)
                pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["soul_hot"], (sp_x, sp_y, 2, 2))
                pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["soul_shine"], (sp_x, sp_y, 1, 1))

    # ============================================================
    # SKILL: E - ESSENCE FLUX (drain area around boss)
    # ============================================================
    def _draw_essence_ground(surface, boss, x, y, timer, pulse):
        """Circle under boss."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(3):
            r = int(38 + i * 5 + math.sin(pulse * 2) * 3)
            alpha = _NS_morvaenthir._alpha(220 - i * 55)
            _NS_morvaenthir._aacircle(surface,
                                     (*_NS_morvaenthir.PALETTE["soul_mid"], alpha),
                                     (x, y + 42), r, 2)
            _NS_morvaenthir._aacircle(surface,
                                     (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                                     (x, y + 42), r, 1)

        # Runic circle.
        for i in range(8):
            angle = pulse * 0.5 + i * math.pi / 4
            rx = x + int(math.cos(angle) * 32)
            ry = y + 42 + int(math.sin(angle) * 12)
            pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["soul_hot"], (rx, ry, 2, 2))

    def _draw_essence_foreground(surface, boss, x, y, timer, phase):
        """Souls being drained toward boss + healing swirls."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        drain_r = 45

        # Draining particles from outside inward.
        for i in range(20):
            drain_t = (phase * 1.5 + i * 0.05) % 1.0
            angle = i * math.pi / 10
            # Start from outer edge, move to center.
            outer_x = x + int(math.cos(angle) * (drain_r + 20))
            outer_y = y + int(math.sin(angle) * (drain_r + 20) * 0.6) - 4
            # Interpolate inward.
            px = int(outer_x + (x - outer_x) * drain_t)
            py = int(outer_y + (y - outer_y) * drain_t)
            alpha = _NS_morvaenthir._alpha(240 * (1 - drain_t))
            if alpha > 0:
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_dark"], alpha),
                                         (px, py), 3)
                _NS_morvaenthir._aacircle(surface,
                                         (*_NS_morvaenthir.PALETTE["soul_mid"], alpha),
                                         (px, py), 2)
                pygame.draw.rect(surface,
                                (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                                (px, py, 1, 1))
                pygame.draw.rect(surface,
                                (*_NS_morvaenthir.PALETTE["soul_shine"], alpha),
                                (px, py, 1, 1))

        # Swirling spiral (like E icon).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        spiral_center_x = x
        spiral_center_y = y - 4

        # Spiral arms.
        for arm in range(2):
            for i in range(20):
                t = i / 20
                spiral_angle = phase * 3 + arm * math.pi + t * math.pi * 2
                spiral_r = int(t * 25 * pulse)
                sx = spiral_center_x + int(math.cos(spiral_angle) * spiral_r)
                sy = spiral_center_y + int(math.sin(spiral_angle) * spiral_r * 0.7)
                alpha = _NS_morvaenthir._alpha(220 * (1 - t))
                for layer_w, color_key in [
                    (3, "soul_dark"),
                    (2, "soul_mid"),
                    (1, "soul_light"),
                ]:
                    _NS_morvaenthir._aacircle(surface,
                                             (*_NS_morvaenthir.PALETTE[color_key], alpha),
                                             (sx, sy), layer_w)
                pygame.draw.rect(surface, (*_NS_morvaenthir.PALETTE["soul_hot"], alpha),
                                (sx, sy, 1, 1))

        # Central bright core (draining energy).
        for r in range(12, 0, -1):
            alpha = _NS_morvaenthir._alpha(150 * (12 - r) / 12 * pulse)
            _NS_morvaenthir._aacircle(surface,
                                     (*_NS_morvaenthir.PALETTE["soul_mid"], alpha),
                                     (spiral_center_x, spiral_center_y), r)
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_light"],
                                 (spiral_center_x, spiral_center_y), 3)
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_shine"],
                                 (spiral_center_x, spiral_center_y), 2)
        pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["white"],
                        (spiral_center_x, spiral_center_y, 1, 1))

        # Healing plus signs floating up (heal effect).
        for i in range(6):
            heal_t = (phase * 0.5 + i * 0.16) % 1.0
            hx = x + int(math.sin(phase * 2 + i) * 20)
            hy = y - 10 - int(heal_t * 30)
            alpha = _NS_morvaenthir._alpha(220 * (1 - heal_t))
            if alpha > 0:
                pygame.draw.line(surface, (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                                (hx - 2, hy), (hx + 2, hy), 1)
                pygame.draw.line(surface, (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                                (hx, hy - 2), (hx, hy + 2), 1)
                pygame.draw.rect(surface, (*_NS_morvaenthir.PALETTE["soul_shine"], alpha),
                                (hx, hy, 1, 1))

    # ============================================================
    # SKILL: R - SHADOW REALM (large area of souls attacking)
    # ============================================================
    def _draw_shadowrealm_ground(surface, boss, x, y, timer, phase):
        """Large dark area at target."""
        tx, ty = _NS_morvaenthir._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(75 * min(1.0, progress * 2))

        if r > 5:
            # Dark base.
            pygame.draw.ellipse(surface, (*_NS_morvaenthir.PALETTE["shadow"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_morvaenthir.PALETTE["soul_darkest"], 220),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_morvaenthir.PALETTE["soul_dark"], 200),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))

            # Bright edge ring.
            pygame.draw.ellipse(surface, (*_NS_morvaenthir.PALETTE["soul_mid"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface, (*_NS_morvaenthir.PALETTE["soul_light"], 240),
                                (tx - r + 2, ty - r // 3 + 1,
                                 r * 2 - 4, r * 2 // 3 - 2), 1)

    def _draw_shadowrealm_foreground(surface, boss, x, y, timer, phase):
        """Multiple ghosts rising from ground attacking."""
        tx, ty = _NS_morvaenthir._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(75 * min(1.0, progress * 2))

        if r < 10:
            return

        # Multiple ghosts spawning around area.
        num_ghosts = 8
        for i in range(num_ghosts):
            ghost_angle = i * math.pi * 2 / num_ghosts + phase * 0.3
            ghost_r = int(r * 0.7)
            gx = tx + int(math.cos(ghost_angle) * ghost_r)
            gy = ty + int(math.sin(ghost_angle) * ghost_r * 0.5)

            # Ghost animation - rising from ground.
            rise_t = (phase * 0.6 + i * 0.2) % 1.0
            gy -= int(rise_t * 15)
            ghost_alpha = _NS_morvaenthir._alpha(220 * (1 - rise_t * 0.5))

            _NS_morvaenthir._draw_large_ghost(surface, gx, gy, phase + i, ghost_alpha)

        # Central swirling soul vortex.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for spiral_i in range(3):
            for i in range(15):
                t = i / 15
                spiral_angle = phase * 2 + spiral_i * math.pi * 2 / 3 + t * math.pi * 3
                spiral_r = int(t * r * 0.6 * pulse)
                sx = tx + int(math.cos(spiral_angle) * spiral_r)
                sy = ty + int(math.sin(spiral_angle) * spiral_r * 0.5)
                alpha = _NS_morvaenthir._alpha(200 * (1 - t))
                if alpha > 0:
                    _NS_morvaenthir._aacircle(surface,
                                             (*_NS_morvaenthir.PALETTE["soul_dark"], alpha),
                                             (sx, sy), 3)
                    _NS_morvaenthir._aacircle(surface,
                                             (*_NS_morvaenthir.PALETTE["soul_mid"], alpha),
                                             (sx, sy), 2)
                    pygame.draw.rect(surface,
                                    (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                                    (sx, sy, 1, 1))

        # Central bright core.
        for r_c in range(10, 0, -1):
            alpha = _NS_morvaenthir._alpha(180 * (10 - r_c) / 10 * pulse)
            _NS_morvaenthir._aacircle(surface,
                                     (*_NS_morvaenthir.PALETTE["soul_mid"], alpha),
                                     (tx, ty), r_c)
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_darkest"], (tx, ty), 5)
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_dark"], (tx, ty), 3)
        _NS_morvaenthir._aacircle(surface, _NS_morvaenthir.PALETTE["soul_light"], (tx, ty), 2)
        pygame.draw.rect(surface, _NS_morvaenthir.PALETTE["white"], (tx, ty, 1, 1))

        # Rising soul columns around area.
        for i in range(6):
            col_angle = i * math.pi / 3 + phase * 0.2
            col_dist = int(r * 0.9)
            col_x = tx + int(math.cos(col_angle) * col_dist)
            col_y_base = ty + int(math.sin(col_angle) * col_dist * 0.5)

            for layer in range(5):
                layer_t = (phase * 0.7 + i * 0.2 + layer * 0.15) % 1.0
                layer_y = col_y_base - int(layer_t * 25)
                layer_alpha = _NS_morvaenthir._alpha(180 * (1 - layer_t))
                layer_w = int(4 + layer_t * 2)

                pygame.draw.ellipse(surface,
                                    (*_NS_morvaenthir.PALETTE["soul_dark"], layer_alpha),
                                    (col_x - layer_w, layer_y - 2, layer_w * 2, 4))
                pygame.draw.ellipse(surface,
                                    (*_NS_morvaenthir.PALETTE["soul_mid"], layer_alpha),
                                    (col_x - layer_w + 1, layer_y - 1,
                                     layer_w * 2 - 2, 2))
                pygame.draw.rect(surface,
                                (*_NS_morvaenthir.PALETTE["soul_hot"], layer_alpha),
                                (col_x, layer_y, 1, 1))

    def _draw_large_ghost(surface, cx, cy, phase, alpha):
        """Larger spirit ghost with hooded shape (like passive icon)."""
        sway = math.sin(phase * 2) * 1

        # Ghost body (hooded silhouette).
        ghost_shape = [
            (cx, cy - 8),
            (cx - 3, cy - 6),
            (cx - 4, cy - 2),
            (cx - 4, cy + 3),
            (cx - 3, cy + 6 + int(sway)),
            (cx - 1, cy + 5),
            (cx, cy + 7),
            (cx + 1, cy + 5),
            (cx + 3, cy + 6 - int(sway)),
            (cx + 4, cy + 3),
            (cx + 4, cy - 2),
            (cx + 3, cy - 6),
        ]
        _NS_morvaenthir._poly(surface, (*_NS_morvaenthir.PALETTE["shadow_deep"], alpha),
                             [(px + 1, py + 1) for px, py in ghost_shape])
        _NS_morvaenthir._poly(surface, (*_NS_morvaenthir.PALETTE["ghost_dark"], alpha),
                             ghost_shape)
        _NS_morvaenthir._poly(surface, (*_NS_morvaenthir.PALETTE["ghost_mid"], alpha), [
            (cx, cy - 7),
            (cx - 2, cy - 5),
            (cx - 3, cy - 1),
            (cx - 3, cy + 3),
            (cx - 2, cy + 5),
            (cx + 2, cy + 5),
            (cx + 3, cy + 3),
            (cx + 3, cy - 1),
            (cx + 2, cy - 5),
        ])
        _NS_morvaenthir._poly(surface, (*_NS_morvaenthir.PALETTE["ghost_light"], alpha // 2), [
            (cx, cy - 5),
            (cx - 1, cy - 3),
            (cx - 1, cy + 2),
            (cx + 1, cy + 2),
            (cx + 1, cy - 3),
        ])

        # Ghost eyes (glowing teal).
        for side in [-1, 1]:
            ex = cx + side * 2
            ey = cy - 3
            pygame.draw.rect(surface, (*_NS_morvaenthir.PALETTE["shadow"], alpha),
                            (ex - 1, ey - 1, 2, 2))
            pygame.draw.rect(surface, (*_NS_morvaenthir.PALETTE["soul_light"], alpha),
                            (ex, ey, 1, 1))
            pygame.draw.rect(surface, (*_NS_morvaenthir.PALETTE["soul_hot"], alpha),
                            (ex, ey, 1, 1))
            pygame.draw.rect(surface, (*_NS_morvaenthir.PALETTE["white"], alpha),
                            (ex, ey, 1, 1))

        # Wisp trail below.
        for i in range(3):
            wisp_y = cy + 7 + i * 2
            wisp_x = cx + int(math.sin(phase + i) * 2)
            wisp_alpha = _NS_morvaenthir._alpha(alpha * (3 - i) / 3)
            pygame.draw.rect(surface,
                            (*_NS_morvaenthir.PALETTE["ghost_mid"], wisp_alpha),
                            (wisp_x, wisp_y, 1, 1))


# ====================================================================
# thornvaegrim.py
# ====================================================================

# ====================================================================
# THORNVAEGRIM - The Twisted Elderwood (Mini Boss - Treant Tank)
# ====================================================================


class _NS_thornvaegrim:
    """Namespace thornvaegrim - Ancient treant tank mini boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Bark/wood (main body)
        "bark_darkest": (18, 12, 8),
        "bark_dark": (45, 32, 18),
        "bark_mid": (85, 60, 32),
        "bark_light": (140, 105, 60),
        "bark_edge": (185, 150, 95),
        "bark_shine": (220, 190, 140),

        # Moss (green covering)
        "moss_darkest": (10, 25, 8),
        "moss_dark": (30, 65, 22),
        "moss_mid": (60, 115, 40),
        "moss_light": (110, 175, 70),
        "moss_edge": (160, 210, 100),

        # Cyan/turquoise glow (eyes, cracks, magic)
        "glow_darkest": (5, 25, 30),
        "glow_dark": (15, 75, 90),
        "glow_mid": (40, 165, 190),
        "glow_light": (110, 230, 245),
        "glow_hot": (180, 250, 255),
        "glow_shine": (230, 255, 255),

        # Nature green magic (Q, R, E - saplings)
        "nature_darkest": (15, 40, 5),
        "nature_dark": (55, 120, 20),
        "nature_mid": (130, 195, 50),
        "nature_light": (195, 240, 100),
        "nature_hot": (235, 255, 160),
        "nature_shine": (255, 255, 220),

        # Sapling face (E skill - little sapling with eyes)
        "sap_dark": (35, 90, 25),
        "sap_mid": (85, 165, 50),
        "sap_light": (150, 220, 90),

        # Root/soil
        "root_darkest": (12, 8, 5),
        "root_dark": (35, 22, 12),
        "root_mid": (70, 48, 25),

        # Mushroom accents (fungi on bark)
        "shroom_dark": (60, 30, 40),
        "shroom_mid": (140, 70, 90),
        "shroom_light": (210, 130, 150),

        # Mist
        "mist_dark": (15, 30, 20),
        "mist_mid": (55, 100, 60),
        "mist_light": (140, 200, 120),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 2),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_thornvaegrim._clamp(color)
        if _NS_thornvaegrim.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_thornvaegrim._clamp(color)
        if _NS_thornvaegrim.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        pygame.draw.polygon(surface, _NS_thornvaegrim._clamp(color), points)

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
        return int(x + 180 / scale * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_thornvaegrim(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_thornvaegrim._detect_moving(boss)
        _NS_thornvaegrim._update_thn_attack_anim(boss)
        attacking = (
            getattr(boss, "_thn_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind.
        _NS_thornvaegrim._draw_forest_aura(surface, x, y, pulse)
        _NS_thornvaegrim._draw_ground_ring(surface, x, y + 54, pulse, active_skill)

        # Skill ground FX (behind body).
        if active_skill == "q":
            _NS_thornvaegrim._draw_bramble_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_thornvaegrim._draw_grasp_ground(surface, boss, x, y, skill_timer, pulse)

        # Body (floating with hover roots).
        if attacking:
            _NS_thornvaegrim._draw_thn_attack(surface, boss, x, y)
        elif moving:
            _NS_thornvaegrim._draw_thn_float_move(surface, boss, x, y)
        else:
            _NS_thornvaegrim._draw_thn_idle(surface, boss, x, y)

        # Foreground FX.
        if active_skill == "q":
            _NS_thornvaegrim._draw_bramble_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_thornvaegrim._draw_twisted_advance(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_thornvaegrim._draw_sapling_throw(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_thornvaegrim._draw_grasp_foreground(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_thn_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_thn_previous_timer", 0))
        active = bool(getattr(boss, "_thn_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._thn_attack_active = True
            boss._thn_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._thn_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._thn_attack_frame = int(
                getattr(boss, "_thn_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._thn_attack_active = False
            boss._thn_attack_frame = 0
            active = False

        boss._thn_previous_timer = timer
        boss._thn_attack_progress = (
            min(1.0, getattr(boss, "_thn_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_thn_last_x"):
            boss._thn_last_x = boss.x
            boss._thn_last_y = boss.y
            return False
        dx = abs(boss.x - boss._thn_last_x)
        dy = abs(boss.y - boss._thn_last_y)
        boss._thn_last_x = boss.x
        boss._thn_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS (FLOATING - heavy hover)
    # ============================================================
    def _draw_thn_idle(surface, boss, x, y):
        float_bob = int(math.sin(boss.pulse * 0.45) * 3)
        _NS_thornvaegrim._draw_shadow(surface, x, y + 56)
        _NS_thornvaegrim._draw_hover_roots(surface, x, y + 44, boss.pulse)
        _NS_thornvaegrim._draw_thn_body(surface, x, y - 4 + float_bob,
                                        boss.direction, boss.pulse, "idle", 0)

    def _draw_thn_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.3
        float_bob = int(math.sin(phase * 0.8) * 4)
        sway = int(math.sin(phase * 0.4) * 2)
        _NS_thornvaegrim._draw_shadow(surface, x + sway, y + 56)
        _NS_thornvaegrim._draw_hover_roots(surface, x + sway, y + 44, phase,
                                           trail=True, facing=boss.direction)
        _NS_thornvaegrim._draw_thn_body(surface, x + sway, y - 6 + float_bob,
                                        boss.direction, phase, "move", 0)

    def _draw_thn_attack(surface, boss, x, y):
        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_thn_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_thn_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Heavy melee swing: raise arm → smash → recovery
        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 4) * facing
            lift = int(t * 5)
        elif progress < 0.55:
            t = (progress - 0.35) / 0.2
            lunge = int((-4 + t * 12)) * facing
            lift = int(5 - t * 8)
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(8 * (1 - t)) * facing
            lift = int(-3 + t * 3)

        float_bob = int(math.sin(boss.pulse * 0.45) * 3)
        _NS_thornvaegrim._draw_shadow(surface, x + lunge, y + 56)
        _NS_thornvaegrim._draw_hover_roots(surface, x + lunge, y + 44, boss.pulse,
                                           intense=True)
        _NS_thornvaegrim._draw_thn_body(surface, x + lunge, y - 4 - lift + float_bob,
                                        facing, boss.pulse, "attack", progress)

        # Impact shockwave when swing lands.
        if 0.55 < progress < 0.75:
            _NS_thornvaegrim._draw_smash_impact(surface, boss, x + lunge,
                                                y + 44, progress)

    # ============================================================
    # BODY (Massive twisted treant with wooden limbs)
    # ============================================================
    def _draw_thn_body(surface, cx, cy, facing, phase, action, attack_progress):
        """Draw ancient treant body."""
        # Back arm first (behind torso).
        _NS_thornvaegrim._draw_treant_arm_back(surface, cx, cy, facing, phase)

        # Main massive torso (thick trunk).
        _NS_thornvaegrim._draw_treant_torso(surface, cx, cy, facing, phase)

        # Head/upper trunk with glowing eyes.
        _NS_thornvaegrim._draw_treant_head(surface, cx, cy - 14, facing, phase)

        # Moss growth on shoulders & top.
        _NS_thornvaegrim._draw_moss_growth(surface, cx, cy - 12, facing, phase)

        # Small saplings/leaves on body.
        _NS_thornvaegrim._draw_leaves_decoration(surface, cx, cy - 8, facing, phase)

        # Front arm (swinging arm - massive).
        _NS_thornvaegrim._draw_treant_arm_front(surface, cx, cy, facing, phase,
                                                action, attack_progress)

    def _draw_treant_torso(surface, cx, cy, facing, phase):
        """Massive twisted trunk torso."""
        breath = math.sin(phase * 0.6) * 1

        # Main trunk shape (wide, thick).
        trunk_shape = [
            (cx - 14, cy - 8),
            (cx - 17, cy - 3),
            (cx - 18, cy + 4),
            (cx - 16, cy + 12),
            (cx - 12, cy + 16),
            (cx - 4, cy + 18),
            (cx + 4, cy + 18),
            (cx + 12, cy + 16),
            (cx + 16, cy + 12),
            (cx + 18, cy + 4),
            (cx + 17, cy - 3),
            (cx + 14, cy - 8),
            (cx + 10, cy - 10),
            (cx - 10, cy - 10),
        ]
        _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["shadow_deep"],
                              [(px + 3, py + 3) for px, py in trunk_shape])
        _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["bark_darkest"], trunk_shape)

        # Layered bark.
        _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["bark_dark"], [
            (cx - 13, cy - 7),
            (cx - 16, cy - 2),
            (cx - 17, cy + 4),
            (cx - 15, cy + 11),
            (cx - 11, cy + 15),
            (cx + 11, cy + 15),
            (cx + 15, cy + 11),
            (cx + 17, cy + 4),
            (cx + 16, cy - 2),
            (cx + 13, cy - 7),
            (cx + 9, cy - 9),
            (cx - 9, cy - 9),
        ])
        _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["bark_mid"], [
            (cx - 11, cy - 5),
            (cx - 14, cy),
            (cx - 15, cy + 5),
            (cx - 12, cy + 12),
            (cx + 12, cy + 12),
            (cx + 15, cy + 5),
            (cx + 14, cy),
            (cx + 11, cy - 5),
            (cx + 7, cy - 7),
            (cx - 7, cy - 7),
        ])
        _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["bark_light"], [
            (cx - 8, cy - 3),
            (cx - 10, cy + 2),
            (cx - 10, cy + 8),
            (cx - 6, cy + 12),
            (cx + 6, cy + 12),
            (cx + 10, cy + 8),
            (cx + 10, cy + 2),
            (cx + 8, cy - 3),
        ])

        # Bark texture (vertical grain lines).
        for i, x_off in enumerate([-11, -7, -3, 1, 5, 9]):
            grain_x = cx + x_off
            pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_darkest"],
                            (grain_x, cy - 6), (grain_x + 1, cy + 14), 1)

        # Twisted knots (dark oval spots).
        for kx, ky, ks in [(-8, -2, 2), (5, 4, 3), (-4, 8, 2), (9, -4, 2)]:
            knot_x = cx + kx
            knot_y = cy + ky
            _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["bark_darkest"],
                                      (knot_x, knot_y), ks)
            _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["shadow"],
                                      (knot_x, knot_y), max(1, ks - 1))
            if ks > 2:
                pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["bark_dark"],
                                (knot_x, knot_y, 1, 1))

        # GLOWING CYAN CRACKS (magic infusion).
        _NS_thornvaegrim._draw_glowing_cracks(surface, cx, cy, phase)

        # Bright highlight edge on left.
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_edge"],
                        (cx - 12, cy - 6), (cx - 14, cy - 2), 1)
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_shine"],
                        (cx - 10, cy - 5), (cx - 11, cy - 3), 1)

    def _draw_glowing_cracks(surface, cx, cy, phase):
        """Cyan glowing cracks/veins on bark."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Main vertical crack down center.
        crack_points = [
            (cx, cy - 8),
            (cx - 1, cy - 4),
            (cx + 1, cy),
            (cx - 1, cy + 4),
            (cx, cy + 10),
            (cx + 2, cy + 14),
        ]
        for i in range(len(crack_points) - 1):
            alpha = _NS_thornvaegrim._alpha(220 * pulse)
            pygame.draw.line(surface,
                            (*_NS_thornvaegrim.PALETTE["glow_dark"], alpha),
                            crack_points[i], crack_points[i + 1], 3)
            pygame.draw.line(surface,
                            (*_NS_thornvaegrim.PALETTE["glow_mid"], alpha),
                            crack_points[i], crack_points[i + 1], 2)
            pygame.draw.line(surface,
                            (*_NS_thornvaegrim.PALETTE["glow_light"], alpha),
                            crack_points[i], crack_points[i + 1], 1)

        # Side branch cracks.
        for start, end in [
            ((cx - 1, cy - 4), (cx - 6, cy - 2)),
            ((cx + 1, cy), (cx + 7, cy + 2)),
            ((cx - 1, cy + 4), (cx - 5, cy + 7)),
        ]:
            alpha = _NS_thornvaegrim._alpha(180 * pulse)
            pygame.draw.line(surface,
                            (*_NS_thornvaegrim.PALETTE["glow_dark"], alpha),
                            start, end, 2)
            pygame.draw.line(surface,
                            (*_NS_thornvaegrim.PALETTE["glow_mid"], alpha),
                            start, end, 1)
            pygame.draw.rect(surface,
                            (*_NS_thornvaegrim.PALETTE["glow_hot"], alpha),
                            (end[0], end[1], 1, 1))

        # Additional glowing runes/nodes at crack intersections.
        for gx, gy in [(cx, cy - 4), (cx, cy), (cx, cy + 6)]:
            for r in range(4, 0, -1):
                alpha = _NS_thornvaegrim._alpha(160 * (4 - r) / 4 * pulse)
                _NS_thornvaegrim._aacircle(surface,
                                          (*_NS_thornvaegrim.PALETTE["glow_mid"], alpha),
                                          (gx, gy), r)
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["glow_shine"], (gx, gy, 1, 1))
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["white"], (gx, gy, 1, 1))

    def _draw_treant_head(surface, cx, cy, facing, phase):
        """Twisted upper trunk with glowing cyan eyes."""
        # Head/upper trunk shape (like a hollowed tree top).
        head_shape = [
            (cx - 10, cy),
            (cx - 12, cy + 4),
            (cx - 10, cy + 10),
            (cx - 4, cy + 12),
            (cx + 4, cy + 12),
            (cx + 10, cy + 10),
            (cx + 12, cy + 4),
            (cx + 10, cy),
            (cx + 6, cy - 4),
            (cx - 6, cy - 4),
        ]
        _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["shadow_deep"],
                              [(px + 2, py + 2) for px, py in head_shape])
        _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["bark_darkest"], head_shape)

        # Bark layers.
        _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["bark_dark"], [
            (cx - 9, cy + 1),
            (cx - 11, cy + 4),
            (cx - 9, cy + 9),
            (cx - 4, cy + 11),
            (cx + 4, cy + 11),
            (cx + 9, cy + 9),
            (cx + 11, cy + 4),
            (cx + 9, cy + 1),
            (cx + 5, cy - 3),
            (cx - 5, cy - 3),
        ])
        _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["bark_mid"], [
            (cx - 7, cy + 2),
            (cx - 9, cy + 5),
            (cx - 7, cy + 8),
            (cx + 7, cy + 8),
            (cx + 9, cy + 5),
            (cx + 7, cy + 2),
            (cx + 4, cy - 2),
            (cx - 4, cy - 2),
        ])

        # Hollow inside (dark cavity like tree hollow).
        _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["shadow"], [
            (cx - 5, cy + 3),
            (cx - 6, cy + 6),
            (cx - 4, cy + 9),
            (cx + 4, cy + 9),
            (cx + 6, cy + 6),
            (cx + 5, cy + 3),
        ])
        _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["bark_darkest"], [
            (cx - 4, cy + 4),
            (cx - 5, cy + 6),
            (cx - 3, cy + 8),
            (cx + 3, cy + 8),
            (cx + 5, cy + 6),
            (cx + 4, cy + 4),
        ])

        # GLOWING CYAN EYES (menyala).
        _NS_thornvaegrim._draw_cyan_eyes(surface, cx, cy + 5, facing, phase)

        # Bark texture (horizontal ridges).
        for y_off in [2, 5, 8]:
            pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_darkest"],
                            (cx - 8, cy + y_off), (cx + 8, cy + y_off), 1)

        # Growth spikes on top (like branches).
        for spike_off in [-7, -3, 0, 3, 7]:
            spike_wave = math.sin(phase * 0.4 + spike_off * 0.2) * 1
            spike_x = cx + spike_off
            spike_top_y = cy - 6 - int(spike_wave)
            spike_base_y = cy - 3
            _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_top_y + 1),
                (spike_x - 2, spike_base_y + 1),
                (spike_x + 2, spike_base_y + 1),
            ])
            _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["bark_darkest"], [
                (spike_x, spike_top_y),
                (spike_x - 2, spike_base_y),
                (spike_x + 2, spike_base_y),
            ])
            _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["bark_dark"], [
                (spike_x, spike_top_y),
                (spike_x - 1, spike_base_y),
                (spike_x + 1, spike_base_y),
            ])
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["bark_mid"],
                            (spike_x, spike_top_y, 1, 1))

    def _draw_cyan_eyes(surface, cx, cy, facing, phase):
        """Two large glowing cyan eyes."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7

        for side in [-1, 1]:
            ex = cx + side * 3
            ey = cy

            # Deep socket (dark hollow).
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["shadow"],
                            (ex - 2, ey - 2, 5, 4))
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["glow_darkest"],
                            (ex - 2, ey - 2, 4, 4))

            # Glow halo (bright).
            for r in range(7, 0, -1):
                alpha = _NS_thornvaegrim._alpha(150 * (7 - r) / 7 * pulse)
                _NS_thornvaegrim._aacircle(surface,
                                          (*_NS_thornvaegrim.PALETTE["glow_mid"], alpha),
                                          (ex, ey), r)

            # Eye core.
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["glow_dark"],
                            (ex - 1, ey - 1, 3, 3))
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["glow_mid"],
                            (ex - 1, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["glow_light"],
                            (ex, ey - 1, 1, 1))
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["glow_hot"],
                            (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["glow_shine"],
                            (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["white"], (ex, ey, 1, 1))

            # Downward tear/glow drip.
            for i in range(3):
                drip_alpha = _NS_thornvaegrim._alpha(160 * (3 - i) / 3 * pulse)
                pygame.draw.rect(surface,
                                (*_NS_thornvaegrim.PALETTE["glow_light"], drip_alpha),
                                (ex, ey + 2 + i, 1, 1))

    def _draw_moss_growth(surface, cx, cy, facing, phase):
        """Moss covering top and shoulders."""
        # Top moss patch.
        for i, (mx_off, my_off, ms) in enumerate([
            (-8, -2, 3),
            (-4, -3, 4),
            (0, -4, 5),
            (4, -3, 4),
            (8, -2, 3),
        ]):
            sway = math.sin(phase * 0.5 + i) * 1
            mx = cx + mx_off
            my = cy + my_off + int(sway)
            _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["moss_darkest"],
                                      (mx + 1, my + 1), ms)
            _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["moss_dark"],
                                      (mx, my), ms)
            _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["moss_mid"],
                                      (mx, my), max(1, ms - 1))
            _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["moss_light"],
                                      (mx, my - 1), max(1, ms - 2))
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["moss_edge"],
                            (mx, my - 1, 1, 1))

        # Shoulder moss (side).
        for side in [-1, 1]:
            sx = cx + side * 12
            sy = cy + 4
            _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["moss_darkest"],
                                      (sx, sy), 4)
            _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["moss_dark"],
                                      (sx, sy), 3)
            _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["moss_mid"],
                                      (sx, sy - 1), 2)
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["moss_light"],
                            (sx, sy - 1, 1, 1))

        # Small mushrooms on moss.
        for mux, muy in [(cx - 6, cy - 3), (cx + 5, cy - 2)]:
            # Stem.
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["bark_light"],
                            (mux, muy + 1, 1, 2))
            # Cap.
            _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["shroom_dark"],
                                      (mux, muy), 2)
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["shroom_mid"],
                            (mux - 1, muy, 3, 1))
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["shroom_light"],
                            (mux, muy, 1, 1))

    def _draw_leaves_decoration(surface, cx, cy, facing, phase):
        """Small leaves/twigs on body."""
        for i, (lx_off, ly_off) in enumerate([(-14, 4), (14, 6), (-10, 12), (12, 14)]):
            sway = math.sin(phase * 0.6 + i) * 1
            lx = cx + lx_off
            ly = cy + ly_off + int(sway)

            # Small leaf.
            _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["moss_dark"], [
                (lx, ly - 2),
                (lx + 2, ly),
                (lx, ly + 2),
                (lx - 2, ly),
            ])
            _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["moss_mid"], [
                (lx, ly - 1),
                (lx + 1, ly),
                (lx, ly + 1),
                (lx - 1, ly),
            ])
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["moss_edge"],
                            (lx, ly, 1, 1))

    def _draw_treant_arm_back(surface, cx, cy, facing, phase):
        """Back arm (thick wooden branch)."""
        sway = math.sin(phase * 0.4) * 1
        back_dir = -facing
        shoulder_x = cx + back_dir * 12
        shoulder_y = cy - 4
        elbow_x = shoulder_x + back_dir * 4
        elbow_y = shoulder_y + 8 + int(sway)
        hand_x = elbow_x - back_dir * 2
        hand_y = elbow_y + 10 + int(sway)

        # Upper arm (thick branch).
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["shadow_deep"],
                        (shoulder_x + 2, shoulder_y + 2), (elbow_x + 2, elbow_y + 2), 8)
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_darkest"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 7)
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_dark"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_mid"],
                        (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 3)

        # Forearm.
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["shadow_deep"],
                        (elbow_x + 2, elbow_y + 2), (hand_x + 2, hand_y + 2), 7)
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_darkest"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 6)
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_dark"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 4)
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_mid"],
                        (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 2)

        # Big wooden fist.
        _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["shadow_deep"],
                                  (hand_x + 2, hand_y + 2), 5)
        _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["bark_darkest"],
                                  (hand_x, hand_y), 5)
        _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["bark_dark"],
                                  (hand_x, hand_y), 4)
        _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["bark_mid"],
                                  (hand_x - 1, hand_y - 1), 3)
        _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["bark_light"],
                                  (hand_x - 1, hand_y - 1), 2)
        pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["bark_edge"],
                        (hand_x - 1, hand_y - 1, 1, 1))

        # Claw fingers.
        for fi in range(3):
            fang_angle = 0.5 + fi * 0.4
            fx_end = hand_x + int(math.cos(fang_angle) * 4) * back_dir
            fy_end = hand_y + int(math.sin(fang_angle) * 4)
            pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_darkest"],
                            (hand_x, hand_y), (fx_end, fy_end), 2)
            pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_mid"],
                            (hand_x, hand_y), (fx_end, fy_end), 1)
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["bark_light"],
                            (fx_end, fy_end, 1, 1))

    def _draw_treant_arm_front(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm — massive smashing arm."""
        sway = math.sin(phase * 0.4) * 1

        # Arm pose based on action.
        if action == "attack":
            if attack_progress < 0.35:
                # Raise high up.
                t = attack_progress / 0.35
                shoulder_angle = -0.3 - t * 1.2
                elbow_bend = 0.4 - t * 0.3
            elif attack_progress < 0.55:
                # SMASH DOWN.
                t = (attack_progress - 0.35) / 0.2
                shoulder_angle = (-1.5) + t * 2.2
                elbow_bend = 0.1 + t * 0.5
            else:
                # Recovery.
                t = (attack_progress - 0.55) / 0.45
                shoulder_angle = 0.7 - t * 1.0
                elbow_bend = 0.6 - t * 0.2
        else:
            shoulder_angle = 0.1 + math.sin(phase * 0.4) * 0.1
            elbow_bend = 0.5

        shoulder_x = cx + facing * 12
        shoulder_y = cy - 4
        upper_len = 8
        elbow_x = shoulder_x + int(math.cos(shoulder_angle) * upper_len) * facing
        elbow_y = shoulder_y + int(math.sin(shoulder_angle) * upper_len) + 2

        forearm_angle = shoulder_angle + elbow_bend
        forearm_len = 10
        hand_x = elbow_x + int(math.cos(forearm_angle) * forearm_len) * facing
        hand_y = elbow_y + int(math.sin(forearm_angle) * forearm_len) + 3

        # Upper arm (thick branch).
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["shadow_deep"],
                        (shoulder_x + 2, shoulder_y + 2), (elbow_x + 2, elbow_y + 2), 9)
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_darkest"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 8)
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_dark"],
                        (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_mid"],
                        (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 4)
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_light"],
                        (shoulder_x, shoulder_y - 2), (elbow_x, elbow_y - 2), 2)

        # Forearm (even thicker for smashing).
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["shadow_deep"],
                        (elbow_x + 2, elbow_y + 2), (hand_x + 2, hand_y + 2), 9)
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_darkest"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 8)
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_dark"],
                        (elbow_x, elbow_y), (hand_x, hand_y), 6)
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_mid"],
                        (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 4)
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_light"],
                        (elbow_x, elbow_y - 2), (hand_x, hand_y - 2), 2)

        # Elbow joint (moss detail).
        _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["moss_dark"],
                                  (elbow_x, elbow_y), 3)
        _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["moss_mid"],
                                  (elbow_x, elbow_y - 1), 2)
        pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["moss_light"],
                        (elbow_x - 1, elbow_y - 1, 1, 1))

        # HUGE WOODEN FIST/CLUB.
        _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["shadow_deep"],
                                  (hand_x + 2, hand_y + 2), 8)
        _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["bark_darkest"],
                                  (hand_x, hand_y), 8)
        _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["bark_dark"],
                                  (hand_x, hand_y), 7)
        _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["bark_mid"],
                                  (hand_x - 1, hand_y - 1), 5)
        _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["bark_light"],
                                  (hand_x - 1, hand_y - 1), 3)
        pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["bark_edge"],
                        (hand_x - 1, hand_y - 1, 1, 1))
        pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["bark_shine"],
                        (hand_x - 1, hand_y - 2, 1, 1))

        # Claw fingers extended (like tree fingers).
        for fi in range(4):
            fang_angle = -0.3 + fi * 0.35
            fx_end = hand_x + int(math.cos(fang_angle) * 7) * facing
            fy_end = hand_y + int(math.sin(fang_angle) * 7)
            # Finger shadow.
            pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["shadow_deep"],
                            (hand_x + 1, hand_y + 1), (fx_end + 1, fy_end + 1), 3)
            pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_darkest"],
                            (hand_x, hand_y), (fx_end, fy_end), 3)
            pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_dark"],
                            (hand_x, hand_y), (fx_end, fy_end), 2)
            pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["bark_mid"],
                            (hand_x, hand_y), (fx_end, fy_end), 1)
            # Sharp claw tip.
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["bark_edge"],
                            (fx_end, fy_end, 1, 1))
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["bark_shine"],
                            (fx_end, fy_end, 1, 1))

        # Glowing cracks on arm (magic infusion).
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for gx, gy in [
            (int((shoulder_x + elbow_x) / 2), int((shoulder_y + elbow_y) / 2)),
            (int((elbow_x + hand_x) / 2), int((elbow_y + hand_y) / 2)),
        ]:
            for r in range(3, 0, -1):
                alpha = _NS_thornvaegrim._alpha(150 * (3 - r) / 3 * pulse)
                _NS_thornvaegrim._aacircle(surface,
                                          (*_NS_thornvaegrim.PALETTE["glow_mid"], alpha),
                                          (gx, gy), r)
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["glow_hot"], (gx, gy, 1, 1))
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["glow_shine"], (gx, gy, 1, 1))

        # Swing trail (during attack).
        if action == "attack" and 0.35 < attack_progress < 0.65:
            _NS_thornvaegrim._draw_swing_trail(surface, cx + facing * 12, cy - 4,
                                               facing, attack_progress, phase)

    def _draw_swing_trail(surface, hand_x, hand_y, facing, progress, phase):
        """Cyan/green arc trail from arm swing."""
        swing_t = (progress - 0.35) / 0.3
        intensity = math.sin(swing_t * math.pi)

        # Arc spans from up to down.
        start_angle = -1.5 * facing
        end_angle = 0.7 * facing

        segments = 12
        for i in range(segments):
            t1 = i / segments
            t2 = (i + 1) / segments
            if t1 > swing_t:
                continue
            a1 = start_angle + (end_angle - start_angle) * t1
            a2 = start_angle + (end_angle - start_angle) * t2

            radius = 22
            p1 = (hand_x + int(math.cos(a1) * radius),
                  hand_y + int(math.sin(a1) * radius))
            p2 = (hand_x + int(math.cos(a2) * radius),
                  hand_y + int(math.sin(a2) * radius))

            fade = 1.0 - (swing_t - t1) * 0.7
            alpha = _NS_thornvaegrim._alpha(220 * intensity * fade)

            for w, color_key in [
                (6, "nature_dark"),
                (4, "nature_mid"),
                (2, "nature_light"),
                (1, "glow_hot"),
            ]:
                pygame.draw.line(surface,
                                (*_NS_thornvaegrim.PALETTE[color_key], alpha),
                                p1, p2, w)

            # Bright sparks.
            if i % 2 == 0:
                pygame.draw.rect(surface,
                                (*_NS_thornvaegrim.PALETTE["nature_hot"], alpha),
                                (p2[0], p2[1], 2, 2))
                pygame.draw.rect(surface,
                                (*_NS_thornvaegrim.PALETTE["nature_shine"], alpha),
                                (p2[0], p2[1], 1, 1))

    def _draw_smash_impact(surface, boss, x, y, progress):
        """Ground impact shockwave when swing hits."""
        smash_t = (progress - 0.55) / 0.2
        intensity = 1 - smash_t

        facing = boss.direction
        impact_x = x + facing * 24
        impact_y = y - 4

        # Ground crack ellipse.
        r = int(20 + smash_t * 20)
        alpha = _NS_thornvaegrim._alpha(220 * intensity)
        _NS_thornvaegrim._aacircle(surface,
                                  (*_NS_thornvaegrim.PALETTE["nature_darkest"], alpha),
                                  (impact_x, impact_y), r + 3, 3)
        _NS_thornvaegrim._aacircle(surface,
                                  (*_NS_thornvaegrim.PALETTE["nature_dark"], alpha),
                                  (impact_x, impact_y), r, 3)
        _NS_thornvaegrim._aacircle(surface,
                                  (*_NS_thornvaegrim.PALETTE["nature_mid"], alpha),
                                  (impact_x, impact_y), max(1, r - 6), 2)
        _NS_thornvaegrim._aacircle(surface,
                                  (*_NS_thornvaegrim.PALETTE["nature_light"], alpha),
                                  (impact_x, impact_y), max(1, r - 12), 1)

        # Radial cracks / roots bursting out.
        for i in range(8):
            angle = i * math.pi / 4
            end_x = impact_x + int(math.cos(angle) * r)
            end_y = impact_y + int(math.sin(angle) * r * 0.6)
            pygame.draw.line(surface,
                            (*_NS_thornvaegrim.PALETTE["nature_mid"], alpha),
                            (impact_x, impact_y), (end_x, end_y), 2)
            pygame.draw.line(surface,
                            (*_NS_thornvaegrim.PALETTE["nature_light"], alpha),
                            (impact_x, impact_y), (end_x, end_y), 1)
            pygame.draw.rect(surface,
                            (*_NS_thornvaegrim.PALETTE["nature_hot"], alpha),
                            (end_x, end_y, 2, 2))

    # ============================================================
    # HOVER ROOTS (floating FX)
    # ============================================================
    def _draw_hover_roots(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        """Roots and green wisps floating below (heavy hover)."""
        strength = 1.5 if intense else 1.0

        # Ground glow.
        glow = pygame.Surface((130, 32), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for r in range(28, 3, -2):
            alpha = _NS_thornvaegrim._alpha((28 - r) * 3 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(glow, (*_NS_thornvaegrim.PALETTE["mist_dark"], alpha),
                                    (65 - r * 2, 16 - r // 3, r * 4, max(3, r // 2)))
        for r in range(18, 3, -2):
            alpha = _NS_thornvaegrim._alpha((18 - r) * 4 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(glow, (*_NS_thornvaegrim.PALETTE["mist_mid"], alpha),
                                    (65 - r, 16 - r // 4, r * 2, max(2, r // 3)))
        surface.blit(glow, (cx - 65, cy - 8))

        # Dangling roots (curving downward from body base).
        for i, offset in enumerate([-14, -8, -2, 4, 10]):
            root_sway = math.sin(phase * 0.6 + i * 0.5) * 2
            base_x = cx + offset
            base_y = cy - 8
            end_x = base_x + int(root_sway)
            end_y = cy + 4

            # Curved root segments.
            prev = (base_x, base_y)
            for step in range(1, 5):
                t = step / 4
                curve_x = int(base_x + (end_x - base_x) * t
                              + math.sin(t * math.pi + phase + i) * 2)
                curve_y = int(base_y + (end_y - base_y) * t)
                thickness = max(1, 4 - step)

                pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["shadow_deep"],
                                (prev[0] + 1, prev[1] + 1), (curve_x + 1, curve_y + 1),
                                thickness + 1)
                pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["root_darkest"],
                                prev, (curve_x, curve_y), thickness)
                pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["root_dark"],
                                prev, (curve_x, curve_y), max(1, thickness - 1))
                if step < 3:
                    pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["root_mid"],
                                    (prev[0], prev[1] - 1), (curve_x, curve_y - 1),
                                    max(1, thickness - 2))
                prev = (curve_x, curve_y)

            # Root tip.
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["root_mid"],
                            (prev[0], prev[1], 1, 2))

        # Rising cyan/green magic wisps.
        for i, offset in enumerate([-22, -14, -6, 2, 10, 18]):
            t = (phase * 0.5 + i * 0.15) % 1.0
            wx = cx + offset + int(math.sin(phase * 2 + i) * 3)
            wy = cy + 8 - int(t * 22)
            alpha = _NS_thornvaegrim._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            color = _NS_thornvaegrim.PALETTE["nature_mid"] if i % 2 == 0 \
                else _NS_thornvaegrim.PALETTE["glow_mid"]
            hot = _NS_thornvaegrim.PALETTE["nature_hot"] if i % 2 == 0 \
                else _NS_thornvaegrim.PALETTE["glow_hot"]
            _NS_thornvaegrim._aacircle(surface, (*color, alpha), (wx, wy), 3)
            _NS_thornvaegrim._aacircle(surface, (*hot, alpha), (wx, wy - 1), 2)
            pygame.draw.rect(surface, (*_NS_thornvaegrim.PALETTE["nature_shine"], alpha),
                            (wx, wy - 1, 1, 1))

        # Small leaves floating.
        for i in range(4):
            leaf_t = (phase * 0.4 + i * 0.25) % 1.0
            lx = cx - 16 + i * 10 + int(math.sin(phase + i) * 3)
            ly = cy + 4 - int(leaf_t * 18)
            alpha = _NS_thornvaegrim._alpha(200 * (1 - leaf_t) * strength)
            if alpha > 0:
                _NS_thornvaegrim._poly(surface,
                                      (*_NS_thornvaegrim.PALETTE["moss_dark"], alpha), [
                                          (lx, ly - 2),
                                          (lx + 2, ly),
                                          (lx, ly + 2),
                                          (lx - 2, ly),
                                      ])
                _NS_thornvaegrim._poly(surface,
                                      (*_NS_thornvaegrim.PALETTE["moss_mid"], alpha), [
                                          (lx, ly - 1),
                                          (lx + 1, ly),
                                          (lx, ly + 1),
                                          (lx - 1, ly),
                                      ])

        # Trail behind.
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_thornvaegrim._alpha(170 - i * 25)
                if alpha <= 0:
                    continue
                _NS_thornvaegrim._aacircle(surface,
                                          (*_NS_thornvaegrim.PALETTE["mist_dark"], alpha),
                                          (sx, sy), max(2, 6 - i))
                _NS_thornvaegrim._aacircle(surface,
                                          (*_NS_thornvaegrim.PALETTE["mist_mid"], alpha),
                                          (sx, sy), max(1, 4 - i))
                pygame.draw.rect(surface,
                                (*_NS_thornvaegrim.PALETTE["nature_light"], alpha),
                                (sx, sy - 1, 2, 2))

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for r in range(14, 0, -1):
            alpha = max(0, (14 - r) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (12 - r, 15 - r, 116 + r * 2, r * 2))
        pygame.draw.ellipse(shadow, (3, 5, 2, 170), (5, 7, 130, 14))
        pygame.draw.ellipse(shadow, (25, 55, 15, 110), (14, 9, 112, 10))
        surface.blit(shadow, (x - 70, y - 15))

    def _draw_forest_aura(surface, x, y, phase):
        """Dark green forest aura with cyan sparkles."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((210, 180), pygame.SRCALPHA)
        for r in range(90, 5, -5):
            alpha = _NS_thornvaegrim._alpha((90 - r) * 1.2 * pulse)
            if alpha > 0:
                _NS_thornvaegrim._aacircle(aura,
                                          (*_NS_thornvaegrim.PALETTE["mist_dark"], alpha),
                                          (105, 90), r)
        for r in range(60, 5, -4):
            alpha = _NS_thornvaegrim._alpha((60 - r) * 1.4 * pulse)
            if alpha > 0:
                _NS_thornvaegrim._aacircle(aura,
                                          (*_NS_thornvaegrim.PALETTE["mist_mid"], alpha),
                                          (105, 90), r)
        # Cyan inner glow.
        for r in range(32, 5, -3):
            alpha = _NS_thornvaegrim._alpha((32 - r) * 1.3 * pulse)
            if alpha > 0:
                _NS_thornvaegrim._aacircle(aura,
                                          (*_NS_thornvaegrim.PALETTE["glow_darkest"], alpha),
                                          (105, 90), r)
        surface.blit(aura, (x - 105, y - 90))

        # Fireflies (cyan sparkles).
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 36 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = _NS_thornvaegrim.PALETTE["glow_mid"] if i % 2 == 0 \
                else _NS_thornvaegrim.PALETTE["nature_mid"]
            hot = _NS_thornvaegrim.PALETTE["glow_hot"] if i % 2 == 0 \
                else _NS_thornvaegrim.PALETTE["nature_hot"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot, (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["white"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring with nature runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 52), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_thornvaegrim.PALETTE["mist_dark"], 200),
                            (5, 17, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_thornvaegrim.PALETTE["nature_darkest"], 220),
                            (14, 19, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_thornvaegrim.PALETTE["nature_dark"], 230),
                            (25, 21, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_thornvaegrim.PALETTE["glow_darkest"], 180),
                            (40, 23, 90, 14), 1)

        # Runes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 68)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_thornvaegrim.PALETTE["nature_light"], 220),
                            (x1, y1), (x2, y2), 1)

        # Star runes.
        for i in range(5):
            angle = phase * 0.3 + i * math.pi / 2.5 + math.pi / 5
            sx = 85 + int(math.cos(angle) * 58)
            sy = 30 + int(math.sin(angle) * 10)
            pygame.draw.rect(ring, (*_NS_thornvaegrim.PALETTE["glow_hot"], 240), (sx, sy, 2, 2))
            pygame.draw.rect(ring, (*_NS_thornvaegrim.PALETTE["glow_shine"], 240), (sx, sy, 1, 1))

        if skill:
            pygame.draw.ellipse(ring, (*_NS_thornvaegrim.PALETTE["nature_hot"],
                                       _NS_thornvaegrim._alpha(150 * pulse)),
                                (16, 12, 138, 36), 1)
        surface.blit(ring, (x - 85, y - 26))

    # ============================================================
    # SKILL: Q - BRAMBLE SMASH (ground brambles bursting)
    # ============================================================
    def _draw_bramble_ground(surface, boss, x, y, timer, phase):
        """Line of ground crack extending forward."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ground crack line forward.
        line_len = int(80 * progress)
        start_x = x + facing * 20
        start_y = y + 42

        for i in range(line_len // 4):
            wave = math.sin(i * 0.5 + phase) * 3
            px = start_x + facing * i * 4
            py = start_y + int(wave)
            alpha = _NS_thornvaegrim._alpha(220 * (1 - i / max(1, line_len // 4)))
            pygame.draw.ellipse(surface,
                                (*_NS_thornvaegrim.PALETTE["nature_darkest"], alpha),
                                (px - 3, py - 2, 6, 4))
            pygame.draw.ellipse(surface,
                                (*_NS_thornvaegrim.PALETTE["nature_dark"], alpha),
                                (px - 2, py - 1, 4, 2))

    def _draw_bramble_foreground(surface, boss, x, y, timer, phase):
        """Brambles/thorny vines bursting up along ground line."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))

        start_x = x + facing * 20
        start_y = y + 42

        # Brambles pop up along the line as it extends.
        num_brambles = 6
        for i in range(num_brambles):
            bramble_progress = max(0, min(1, (progress * num_brambles) - i))
            if bramble_progress <= 0:
                continue

            bx = start_x + facing * (10 + i * 12)
            by = start_y + int(math.sin(i * 0.5 + phase) * 2)

            # Bramble height (grows quickly).
            height = int(min(16, bramble_progress * 20))

            # Thorny stem.
            wave = math.sin(phase + i) * 2
            top_x = bx + int(wave)
            top_y = by - height

            # Layered stem.
            pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["shadow_deep"],
                            (bx + 1, by + 1), (top_x + 1, top_y + 1), 4)
            pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["nature_darkest"],
                            (bx, by), (top_x, top_y), 3)
            pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["nature_dark"],
                            (bx, by), (top_x, top_y), 2)
            pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["nature_mid"],
                            (bx, by), (top_x, top_y), 1)

            # Thorns sticking out.
            for j in range(3):
                thorn_t = (j + 1) / 4
                thorn_x = int(bx + (top_x - bx) * thorn_t)
                thorn_y = int(by + (top_y - by) * thorn_t)
                for side in [-1, 1]:
                    thorn_end_x = thorn_x + side * 3
                    thorn_end_y = thorn_y - 1
                    pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["nature_darkest"],
                                    (thorn_x, thorn_y), (thorn_end_x, thorn_end_y), 1)
                    pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["nature_light"],
                                    (thorn_end_x, thorn_end_y, 1, 1))

            # Bright glowing tip.
            if bramble_progress > 0.3:
                for r in range(4, 0, -1):
                    a = _NS_thornvaegrim._alpha(180 * (4 - r) / 4)
                    _NS_thornvaegrim._aacircle(surface,
                                              (*_NS_thornvaegrim.PALETTE["nature_light"], a),
                                              (top_x, top_y), r)
                pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["nature_shine"],
                                (top_x, top_y, 1, 1))
                pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["white"],
                                (top_x, top_y, 1, 1))

            # Small leaves along stem.
            for j in range(2):
                lf_t = (j + 1) / 3
                lf_x = int(bx + (top_x - bx) * lf_t)
                lf_y = int(by + (top_y - by) * lf_t)
                _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["moss_dark"], [
                    (lf_x, lf_y - 1),
                    (lf_x + 2, lf_y),
                    (lf_x, lf_y + 1),
                    (lf_x - 1, lf_y),
                ])
                pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["moss_light"],
                                (lf_x, lf_y, 1, 1))

        # Sparkles along the line.
        for i in range(10):
            sp_t = (phase * 2 + i * 0.1) % 1.0
            spx = start_x + facing * int(sp_t * 80)
            spy = start_y + int(math.sin(phase * 3 + i) * 4)
            alpha = _NS_thornvaegrim._alpha(200 * (1 - sp_t))
            pygame.draw.rect(surface, (*_NS_thornvaegrim.PALETTE["nature_hot"], alpha),
                            (spx, spy, 2, 2))

    # ============================================================
    # SKILL: W - TWISTED ADVANCE (dash forward with body)
    # ============================================================
    def _draw_twisted_advance(surface, boss, x, y, timer, phase):
        """Dash trail with treant afterimages."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Afterimages trailing behind.
        for i in range(5):
            trail_offset = (i + 1) * 10 * facing
            alpha = _NS_thornvaegrim._alpha(180 - i * 30)
            if alpha <= 0:
                continue

            # Ghost silhouette of treant.
            tx = x - trail_offset
            ty = y - 4 + int(math.sin(phase + i) * 2)

            silhouette = [
                (tx - 14, ty - 8),
                (tx - 18, ty),
                (tx - 16, ty + 12),
                (tx - 4, ty + 18),
                (tx + 4, ty + 18),
                (tx + 16, ty + 12),
                (tx + 18, ty),
                (tx + 14, ty - 8),
                (tx + 6, ty - 18),
                (tx - 6, ty - 18),
            ]
            _NS_thornvaegrim._poly(surface,
                                  (*_NS_thornvaegrim.PALETTE["nature_darkest"], alpha),
                                  silhouette)
            _NS_thornvaegrim._poly(surface,
                                  (*_NS_thornvaegrim.PALETTE["nature_dark"], alpha // 2), [
                                      (tx - 12, ty - 6),
                                      (tx - 15, ty),
                                      (tx - 13, ty + 10),
                                      (tx + 13, ty + 10),
                                      (tx + 15, ty),
                                      (tx + 12, ty - 6),
                                      (tx + 5, ty - 15),
                                      (tx - 5, ty - 15),
                                  ])

            # Cyan glowing eyes in trail.
            for side in [-1, 1]:
                pygame.draw.rect(surface,
                                (*_NS_thornvaegrim.PALETTE["glow_mid"], alpha),
                                (tx + side * 3, ty - 12, 2, 2))
                pygame.draw.rect(surface,
                                (*_NS_thornvaegrim.PALETTE["glow_hot"], alpha),
                                (tx + side * 3, ty - 12, 1, 1))

        # Speed lines.
        for i in range(6):
            line_y = y - 10 + i * 5
            line_x_start = x - 45 * facing
            line_x_end = x - 12 * facing
            alpha = _NS_thornvaegrim._alpha(200 - i * 25)
            pygame.draw.line(surface,
                            (*_NS_thornvaegrim.PALETTE["nature_light"], alpha),
                            (line_x_start, line_y), (line_x_end, line_y), 2)
            pygame.draw.line(surface,
                            (*_NS_thornvaegrim.PALETTE["nature_shine"], alpha),
                            (line_x_start, line_y), (line_x_end, line_y), 1)

        # Healing particles rising (W heals boss).
        for i in range(6):
            heal_t = (phase * 0.5 + i * 0.16) % 1.0
            hx = x + int(math.sin(phase + i) * 12)
            hy = y - int(heal_t * 30)
            alpha = _NS_thornvaegrim._alpha(220 * (1 - heal_t))
            if alpha > 0:
                pygame.draw.rect(surface,
                                (*_NS_thornvaegrim.PALETTE["nature_light"], alpha),
                                (hx, hy, 2, 2))
                pygame.draw.rect(surface,
                                (*_NS_thornvaegrim.PALETTE["nature_hot"], alpha),
                                (hx, hy, 1, 1))
                # + plus symbol.
                if i % 2 == 0:
                    pygame.draw.line(surface,
                                    (*_NS_thornvaegrim.PALETTE["nature_shine"], alpha),
                                    (hx - 1, hy), (hx + 2, hy), 1)
                    pygame.draw.line(surface,
                                    (*_NS_thornvaegrim.PALETTE["nature_shine"], alpha),
                                    (hx, hy - 1), (hx, hy + 2), 1)

    # ============================================================
    # SKILL: E - SAPLING THROW (arced projectile sapling)
    # ============================================================
    def _draw_sapling_throw(surface, boss, x, y, timer, phase):
        """Cute sapling projectile arcing to target."""
        facing = boss.direction
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_thornvaegrim._target_position(boss, x, y)

        start_x = x + facing * 20
        start_y = y - 10

        # Arced trajectory (parabolic).
        t = progress
        bx = int(start_x + (tx - start_x) * t)
        arc_height = 60
        by = int(start_y + (ty - start_y) * t - math.sin(t * math.pi) * arc_height)

        # Trail.
        for i in range(8):
            trail_t = max(0.0, t - i * 0.06)
            if trail_t <= 0:
                continue
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t
                     - math.sin(trail_t * math.pi) * arc_height)
            alpha = _NS_thornvaegrim._alpha(200 - i * 25)
            size = max(1, 5 - i)
            _NS_thornvaegrim._aacircle(surface,
                                      (*_NS_thornvaegrim.PALETTE["nature_dark"], alpha),
                                      (px, py), size)
            _NS_thornvaegrim._aacircle(surface,
                                      (*_NS_thornvaegrim.PALETTE["nature_mid"], alpha),
                                      (px, py), max(1, size - 1))
            _NS_thornvaegrim._aacircle(surface,
                                      (*_NS_thornvaegrim.PALETTE["nature_light"], alpha),
                                      (px, py), max(1, size - 2))

        # SAPLING body (cute little creature).
        if t < 0.95:
            _NS_thornvaegrim._draw_sapling_creature(surface, bx, by, phase, size=5)

        # Impact + saplings spawn.
        if t > 0.85:
            st = (t - 0.85) / 0.15
            r = int(15 + st * 20)
            alpha = _NS_thornvaegrim._alpha(220 * (1 - st))
            _NS_thornvaegrim._aacircle(surface,
                                      (*_NS_thornvaegrim.PALETTE["nature_dark"], alpha),
                                      (tx, ty), r + 2, 2)
            _NS_thornvaegrim._aacircle(surface,
                                      (*_NS_thornvaegrim.PALETTE["nature_mid"], alpha),
                                      (tx, ty), r, 2)
            _NS_thornvaegrim._aacircle(surface,
                                      (*_NS_thornvaegrim.PALETTE["nature_light"], alpha),
                                      (tx, ty), max(1, r - 6), 1)

            # Spawn small saplings around impact.
            spawn_positions = [(tx, ty), (tx - 15, ty + 3), (tx + 15, ty + 3)]
            for sp_x, sp_y in spawn_positions:
                _NS_thornvaegrim._draw_sapling_creature(surface, sp_x, sp_y - 3,
                                                        phase, size=4)

    def _draw_sapling_creature(surface, cx, cy, phase, size=5):
        """Cute little sapling with eyes."""
        wave = math.sin(phase * 2) * 1

        # Body (rounded green).
        _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["shadow_deep"],
                                  (cx + 1, cy + 1), size)
        _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["nature_darkest"],
                                  (cx, cy), size)
        _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["sap_dark"],
                                  (cx, cy), size)
        _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["sap_mid"],
                                  (cx, cy), max(1, size - 1))
        _NS_thornvaegrim._aacircle(surface, _NS_thornvaegrim.PALETTE["sap_light"],
                                  (cx - 1, cy - 1), max(1, size - 2))

        # Two big eyes.
        for side in [-1, 1]:
            ex = cx + side * 1
            ey = cy - 1
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["shadow"],
                            (ex - 1, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["glow_light"],
                            (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["white"], (ex, ey, 1, 1))

        # Small mouth.
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["shadow"],
                        (cx - 1, cy + 1), (cx + 1, cy + 1), 1)

        # Little sprout on top.
        pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["sap_dark"],
                        (cx, cy - size), (cx + int(wave), cy - size - 2), 1)
        pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["nature_light"],
                        (cx + int(wave), cy - size - 2, 1, 1))
        _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["sap_mid"], [
            (cx - 1, cy - size - 1),
            (cx + int(wave) + 1, cy - size - 2),
            (cx + 1, cy - size),
        ])

        # Little arm sticks.
        for side in [-1, 1]:
            pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["nature_darkest"],
                            (cx + side * size, cy),
                            (cx + side * (size + 2), cy - 1), 1)

    # ============================================================
    # SKILL: R - NATURE'S GRASP (wall of trees charging forward)
    # ============================================================
    def _draw_grasp_ground(surface, boss, x, y, timer, phase):
        """Ground line where wall of trees will pass."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Ground path from boss forward.
        path_len = int(140 * progress)
        start_x = x + facing * 25
        start_y = y + 44

        for i in range(0, path_len, 4):
            wave = math.sin(i * 0.3 + phase) * 3
            px = start_x + facing * i
            py = start_y + int(wave)
            alpha = _NS_thornvaegrim._alpha(220 * (1 - i / max(1, path_len)))
            pygame.draw.ellipse(surface,
                                (*_NS_thornvaegrim.PALETTE["nature_darkest"], alpha),
                                (px - 8, py - 3, 16, 6))
            pygame.draw.ellipse(surface,
                                (*_NS_thornvaegrim.PALETTE["nature_dark"], alpha),
                                (px - 6, py - 2, 12, 4))
            pygame.draw.ellipse(surface,
                                (*_NS_thornvaegrim.PALETTE["nature_mid"], alpha),
                                (px - 4, py - 1, 8, 2))

    def _draw_grasp_foreground(surface, boss, x, y, timer, phase):
        """Massive wall of trees / vines charging forward."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        start_x = x + facing * 25
        start_y = y + 30
        max_distance = 140

        current_distance = int(max_distance * progress)

        # Growing trees along the path.
        num_trees = 5
        for i in range(num_trees):
            tree_progress = max(0, min(1, (progress * num_trees) - i))
            if tree_progress <= 0:
                continue

            tree_x = start_x + facing * (20 + i * 25)
            tree_y = start_y + int(math.sin(i * 0.7 + phase) * 3)

            # Tree height.
            tree_h = int(30 * tree_progress)
            tree_w = int(8 * tree_progress)

            if tree_h < 3:
                continue

            # Trunk shadow.
            _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["shadow_deep"], [
                (tree_x - tree_w // 2 + 2, tree_y + 2),
                (tree_x + tree_w // 2 + 2, tree_y + 2),
                (tree_x + tree_w // 3 + 2, tree_y - tree_h + 2),
                (tree_x - tree_w // 3 + 2, tree_y - tree_h + 2),
            ])

            # Trunk.
            trunk_shape = [
                (tree_x - tree_w // 2, tree_y),
                (tree_x + tree_w // 2, tree_y),
                (tree_x + tree_w // 3, tree_y - tree_h),
                (tree_x - tree_w // 3, tree_y - tree_h),
            ]
            _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["bark_darkest"],
                                  trunk_shape)
            _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["bark_dark"], [
                (tree_x - tree_w // 2 + 1, tree_y),
                (tree_x + tree_w // 2 - 1, tree_y),
                (tree_x + tree_w // 3 - 1, tree_y - tree_h),
                (tree_x - tree_w // 3 + 1, tree_y - tree_h),
            ])
            _NS_thornvaegrim._poly(surface, _NS_thornvaegrim.PALETTE["bark_mid"], [
                (tree_x - 1, tree_y),
                (tree_x + 1, tree_y),
                (tree_x + 1, tree_y - tree_h),
                (tree_x - 1, tree_y - tree_h),
            ])

            # Cyan crack on trunk.
            pulse = math.sin(phase * 2) * 0.3 + 0.7
            alpha = _NS_thornvaegrim._alpha(220 * pulse)
            pygame.draw.line(surface,
                            (*_NS_thornvaegrim.PALETTE["glow_mid"], alpha),
                            (tree_x, tree_y - 2),
                            (tree_x, tree_y - tree_h + 2), 1)

            # Foliage crown.
            if tree_progress > 0.4:
                crown_r = int(10 * (tree_progress - 0.4) * 1.6)
                if crown_r > 2:
                    _NS_thornvaegrim._aacircle(surface,
                                              _NS_thornvaegrim.PALETTE["shadow_deep"],
                                              (tree_x + 1, tree_y - tree_h + 1), crown_r)
                    _NS_thornvaegrim._aacircle(surface,
                                              _NS_thornvaegrim.PALETTE["nature_darkest"],
                                              (tree_x, tree_y - tree_h), crown_r)
                    _NS_thornvaegrim._aacircle(surface,
                                              _NS_thornvaegrim.PALETTE["nature_dark"],
                                              (tree_x, tree_y - tree_h),
                                              max(1, crown_r - 1))
                    _NS_thornvaegrim._aacircle(surface,
                                              _NS_thornvaegrim.PALETTE["nature_mid"],
                                              (tree_x - 1, tree_y - tree_h - 1),
                                              max(1, crown_r - 2))
                    _NS_thornvaegrim._aacircle(surface,
                                              _NS_thornvaegrim.PALETTE["nature_light"],
                                              (tree_x - 1, tree_y - tree_h - 1),
                                              max(1, crown_r - 3))
                    pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["nature_hot"],
                                    (tree_x, tree_y - tree_h, 1, 1))
                    pygame.draw.rect(surface, _NS_thornvaegrim.PALETTE["nature_shine"],
                                    (tree_x, tree_y - tree_h, 1, 1))

                    # Angry face on some trees.
                    if i % 2 == 0 and tree_progress > 0.7:
                        for side in [-1, 1]:
                            pygame.draw.rect(surface,
                                            _NS_thornvaegrim.PALETTE["shadow"],
                                            (tree_x + side * 2, tree_y - tree_h, 1, 1))
                            pygame.draw.rect(surface,
                                            _NS_thornvaegrim.PALETTE["glow_light"],
                                            (tree_x + side * 2, tree_y - tree_h, 1, 1))

            # Vines/roots at base.
            for vine_side in [-1, 1]:
                vine_end_x = tree_x + vine_side * int(tree_w)
                vine_end_y = tree_y + 3
                pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["nature_darkest"],
                                (tree_x, tree_y), (vine_end_x, vine_end_y), 2)
                pygame.draw.line(surface, _NS_thornvaegrim.PALETTE["nature_mid"],
                                (tree_x, tree_y), (vine_end_x, vine_end_y), 1)

        # Massive wave arc going forward (front of wall).
        if progress < 0.8:
            wave_x = start_x + facing * current_distance
            wave_intensity = math.sin(progress * math.pi)
            alpha = _NS_thornvaegrim._alpha(240 * wave_intensity)

            # Curved wave (like R icon - curved crescent).
            for arc_i in range(15):
                arc_t = arc_i / 15
                arc_angle = -math.pi / 2 + arc_t * math.pi
                arc_r = 35
                arc_x = wave_x + int(math.cos(arc_angle) * arc_r * facing)
                arc_y = start_y - 5 + int(math.sin(arc_angle) * arc_r)

                for w, color_key in [
                    (7, "nature_darkest"),
                    (5, "nature_dark"),
                    (3, "nature_mid"),
                    (1, "nature_hot"),
                ]:
                    _NS_thornvaegrim._aacircle(surface,
                                              (*_NS_thornvaegrim.PALETTE[color_key], alpha),
                                              (arc_x, arc_y), w)

            # Rising green energy at the tip.
            for i in range(6):
                p_ang = i * math.pi / 3 + phase * 2
                p_x = wave_x + int(math.cos(p_ang) * 20)
                p_y = start_y - 10 + int(math.sin(p_ang) * 15)
                pygame.draw.rect(surface,
                                (*_NS_thornvaegrim.PALETTE["nature_hot"], alpha),
                                (p_x, p_y, 2, 2))
                pygame.draw.rect(surface,
                                (*_NS_thornvaegrim.PALETTE["nature_shine"], alpha),
                                (p_x, p_y, 1, 1))

        # Rising leaf particles all over.
        for i in range(15):
            lf_t = (phase * 0.4 + i * 0.07) % 1.0
            lf_x = start_x + facing * int((i / 15) * current_distance)
            lf_y = start_y - int(lf_t * 30) + int(math.sin(phase + i) * 3)
            alpha = _NS_thornvaegrim._alpha(220 * (1 - lf_t))
            if alpha > 0 and lf_x < start_x + facing * current_distance:
                _NS_thornvaegrim._poly(surface,
                                      (*_NS_thornvaegrim.PALETTE["nature_mid"], alpha), [
                                          (lf_x, lf_y - 2),
                                          (lf_x + 2, lf_y),
                                          (lf_x, lf_y + 2),
                                          (lf_x - 2, lf_y),
                                      ])
                pygame.draw.rect(surface,
                                (*_NS_thornvaegrim.PALETTE["nature_hot"], alpha),
                                (lf_x, lf_y, 1, 1))


# ====================================================================
# morthraxis.py
# ====================================================================

# ====================================================================
# MORTHRAXIS - The Crimson Sovereign
# ====================================================================


class _NS_morthraxis:
    """Namespace morthraxis - True Boss vampire count."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Pale vampire skin
        "skin_darkest": (60, 40, 45),
        "skin_dark": (130, 100, 110),
        "skin_mid": (200, 170, 180),
        "skin_light": (235, 215, 220),
        "skin_shine": (255, 245, 245),

        # Black hair / dark elements
        "hair_darkest": (5, 5, 10),
        "hair_dark": (25, 20, 30),
        "hair_mid": (55, 45, 60),
        "hair_light": (100, 85, 110),

        # Crimson cape/blood (main theme)
        "blood_darkest": (30, 5, 10),
        "blood_dark": (80, 10, 25),
        "blood_mid": (160, 25, 50),
        "blood_light": (220, 50, 90),
        "blood_hot": (255, 90, 130),
        "blood_shine": (255, 180, 200),

        # Pink/magenta magic glow
        "magic_darkest": (40, 5, 30),
        "magic_dark": (100, 15, 75),
        "magic_mid": (200, 40, 140),
        "magic_light": (255, 100, 200),
        "magic_hot": (255, 160, 230),
        "magic_shine": (255, 230, 250),

        # Red eye glow
        "eye_socket": (10, 2, 5),
        "eye_darkest": (50, 5, 10),
        "eye_dark": (120, 15, 25),
        "eye_mid": (220, 30, 50),
        "eye_light": (255, 80, 100),
        "eye_glow": (255, 200, 200),

        # Fangs (white/bone)
        "fang_dark": (100, 90, 90),
        "fang_mid": (200, 195, 195),
        "fang_light": (245, 240, 240),
        "fang_shine": (255, 255, 255),

        # Gold ornaments
        "gold_dark": (80, 55, 15),
        "gold_mid": (180, 140, 40),
        "gold_light": (240, 210, 100),
        "gold_shine": (255, 245, 180),

        # Black clothing (formal count attire)
        "cloth_darkest": (8, 5, 12),
        "cloth_dark": (25, 18, 30),
        "cloth_mid": (50, 40, 55),
        "cloth_light": (85, 70, 90),

        # Bat wings (membrane)
        "wing_darkest": (15, 5, 20),
        "wing_dark": (40, 10, 40),
        "wing_mid": (90, 20, 70),
        "wing_light": (160, 50, 120),

        # Blood mist
        "mist_dark": (40, 5, 20),
        "mist_mid": (120, 20, 60),
        "mist_light": (220, 60, 130),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_morthraxis._clamp(color)
        if _NS_morthraxis.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_morthraxis._clamp(color)
        if _NS_morthraxis.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_morthraxis._clamp(color), points)

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
    def draw_morthraxis(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_morthraxis._update_mrx_attack_anim(boss)
        attacking = (
            getattr(boss, "_mrx_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind
        _NS_morthraxis._draw_blood_aura(surface, x, y, pulse)
        _NS_morthraxis._draw_ground_ring(surface, x, y + 46, pulse, active_skill)

        # Skill ground FX (behind body)
        if active_skill == "w":
            _NS_morthraxis._draw_sanguine_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morthraxis._draw_baleful_ground(surface, boss, x, y, skill_timer, pulse)

        # Body - always floating
        _NS_morthraxis._draw_mrx_floating(surface, boss, x, y, attacking)

        # Foreground FX
        if active_skill == "q":
            _NS_morthraxis._draw_bat_impale(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_morthraxis._draw_sanguine_bats(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_morthraxis._draw_phantom_mob(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morthraxis._draw_baleful_foreground(surface, boss, x, y, skill_timer, pulse)

        # Basic attack projectile (bat)
        if attacking and active_skill is None:
            _NS_morthraxis._draw_basic_bat_projectile(surface, boss, x, y)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_mrx_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_mrx_previous_timer", 0))
        active = bool(getattr(boss, "_mrx_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._mrx_attack_active = True
            boss._mrx_attack_frame = 0
            # Kunci arah saat serangan dimulai supaya pose serang
            # tidak terbalik-balik kalau hero berbalik/retreat di
            # tengah animasi.
            boss._mrx_attack_dir = int(getattr(boss, "direction", 1))
            active = True
        elif active and timer > 0:
            boss._mrx_attack_frame = int(getattr(boss, "_mrx_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._mrx_attack_active = False
            boss._mrx_attack_frame = 0
            active = False

        boss._mrx_previous_timer = timer
        boss._mrx_attack_progress = (
            min(1.0, getattr(boss, "_mrx_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )

    # ============================================================
    # FLOATING POSE (always floats, cape flows)
    # ============================================================
    def _draw_mrx_floating(surface, boss, x, y, attacking):
        # Floating bob
        float_bob = math.sin(boss.pulse * 0.7) * 6
        cape_sway = math.sin(boss.pulse * 0.5) * 3

        _NS_morthraxis._draw_shadow(surface, x, y + 50)
        _NS_morthraxis._draw_blood_mist(surface, x, y + 30, boss.pulse)

        # Progress LIVE dari attack_timer (tetap mulus walau body
        # hero di-cache - renderer dipanggil tiap N frame).
        t = int(getattr(boss, "timer", 0) or 0)
        cd = max(2, int(getattr(boss, "attack_cooldown", 48)))
        if getattr(boss, "_mrx_attack_active", False) or t > cd - 15:
            progress = max(0.0, min(1.0, (cd - 1 - t) / max(1.0, float(cd - 1))))
        else:
            progress = 0.0

        facing = getattr(boss, "_mrx_attack_dir", None)
        if facing is None:
            facing = boss.direction

        # Cast animation - arm raises
        cast_lift = 0
        if attacking:
            if progress < 0.5:
                cast_lift = int(progress / 0.5 * 8)
            else:
                cast_lift = int((1 - (progress - 0.5) / 0.5) * 8)

        _NS_morthraxis._draw_mrx_body(surface, x, int(y + float_bob),
                                       facing, boss.pulse,
                                       cape_sway, cast_lift, progress if attacking else 0)

    # ============================================================
    # BODY - Vampire Count (upright, floating, cape flowing)
    # ============================================================
    def _draw_mrx_body(surface, cx, cy, facing, phase, cape_sway, cast_lift, attack_progress):
        # Draw cape FIRST (behind body)
        _NS_morthraxis._draw_vampire_cape(surface, cx, cy, facing, phase, cape_sway)

        # Draw bottom (bat wing/mist under feet - since floating)
        _NS_morthraxis._draw_floating_wisps(surface, cx, cy + 30, phase)

        # Body torso
        _NS_morthraxis._draw_vampire_torso(surface, cx, cy, facing, phase)

        # Arms
        _NS_morthraxis._draw_vampire_arms(surface, cx, cy, facing, phase, cast_lift, attack_progress)

        # Head
        _NS_morthraxis._draw_vampire_head(surface, cx, cy - 32, facing, phase, attack_progress)

        # Collar (high vampire collar)
        _NS_morthraxis._draw_high_collar(surface, cx, cy - 20, facing, phase)

    def _draw_vampire_cape(surface, cx, cy, facing, phase, sway):
        """Large flowing crimson cape behind body."""
        # Cape flows down and to the sides
        cape_top_y = cy - 22
        cape_bot_y = cy + 40

        # Main cape shape (behind character)
        cape_points = [
            (cx - 10, cape_top_y),
            (cx - 20 + int(sway), cy - 5),
            (cx - 28 + int(sway * 1.5), cy + 15),
            (cx - 32 + int(sway * 2), cape_bot_y),
            (cx - 20 + int(sway), cape_bot_y + 5),
            (cx - 8, cape_bot_y - 8),
            (cx + 8, cape_bot_y - 8),
            (cx + 20 - int(sway), cape_bot_y + 5),
            (cx + 32 - int(sway * 2), cape_bot_y),
            (cx + 28 - int(sway * 1.5), cy + 15),
            (cx + 20 - int(sway), cy - 5),
            (cx + 10, cape_top_y),
        ]

        # Shadow
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["shadow_deep"],
                              [(p[0] + 2, p[1] + 2) for p in cape_points])

        # Cape outer (dark blood)
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_darkest"], cape_points)

        # Inner cape (crimson main)
        inner_points = [
            (cx - 8, cape_top_y + 2),
            (cx - 16 + int(sway), cy - 3),
            (cx - 22 + int(sway * 1.5), cy + 15),
            (cx - 25 + int(sway * 2), cape_bot_y - 3),
            (cx - 15 + int(sway), cape_bot_y),
            (cx, cape_bot_y - 12),
            (cx + 15 - int(sway), cape_bot_y),
            (cx + 25 - int(sway * 2), cape_bot_y - 3),
            (cx + 22 - int(sway * 1.5), cy + 15),
            (cx + 16 - int(sway), cy - 3),
            (cx + 8, cape_top_y + 2),
        ]
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_dark"], inner_points)

        # Highlight on cape (rim light)
        for i in range(len(cape_points) - 1):
            if i < 4:  # Left side highlights
                p1 = cape_points[i]
                p2 = cape_points[i + 1]
                _NS_morthraxis._aaline(surface, _NS_morthraxis.PALETTE["blood_mid"], p1, p2, 2)
            elif i > 7:  # Right side highlights
                p1 = cape_points[i]
                p2 = cape_points[i + 1]
                _NS_morthraxis._aaline(surface, _NS_morthraxis.PALETTE["blood_mid"], p1, p2, 2)

        # Inner cape mid tone (visible parts)
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_mid"], [
            (cx - 6, cy - 10),
            (cx - 12 + int(sway), cy + 5),
            (cx - 15 + int(sway * 2), cy + 25),
            (cx - 8, cy + 30),
            (cx + 8, cy + 30),
            (cx + 15 - int(sway * 2), cy + 25),
            (cx + 12 - int(sway), cy + 5),
            (cx + 6, cy - 10),
        ])

        # Cape edge tears (jagged bottom)
        for i, xoff in enumerate((-28, -18, -8, 8, 18, 28)):
            tear_x = cx + xoff + int(sway * (2 - i * 0.3))
            tear_y = cape_bot_y + 3 + int(math.sin(phase + i) * 2)
            _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_darkest"], [
                (tear_x - 3, cape_bot_y - 2),
                (tear_x, tear_y + 5),
                (tear_x + 3, cape_bot_y - 2),
            ])
            _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_dark"], [
                (tear_x - 2, cape_bot_y - 2),
                (tear_x, tear_y + 3),
                (tear_x + 2, cape_bot_y - 2),
            ])

        # Gold clasp at shoulders
        for side in (-1, 1):
            clasp_x = cx + side * 9
            clasp_y = cape_top_y + 1
            _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["gold_dark"], (clasp_x, clasp_y), 3)
            _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["gold_mid"], (clasp_x, clasp_y), 2)
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["gold_light"],
                             (clasp_x, clasp_y - 1, 1, 1))
            # Red gem in center
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["blood_hot"],
                             (clasp_x, clasp_y, 1, 1))

    def _draw_vampire_torso(surface, cx, cy, facing, phase):
        """Vampire count torso - formal black attire with red vest."""
        # Torso shape
        torso_pts = [
            (cx - 9, cy - 18),
            (cx - 11, cy - 8),
            (cx - 10, cy + 8),
            (cx - 8, cy + 20),
            (cx + 8, cy + 20),
            (cx + 10, cy + 8),
            (cx + 11, cy - 8),
            (cx + 9, cy - 18),
        ]
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 1) for p in torso_pts])
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["cloth_darkest"], torso_pts)

        # Black coat main
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["cloth_dark"], [
            (cx - 8, cy - 17),
            (cx - 10, cy - 6),
            (cx - 9, cy + 18),
            (cx + 9, cy + 18),
            (cx + 10, cy - 6),
            (cx + 8, cy - 17),
        ])

        # Red vest (center strip)
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_darkest"], [
            (cx - 4, cy - 15),
            (cx - 5, cy - 5),
            (cx - 4, cy + 15),
            (cx + 4, cy + 15),
            (cx + 5, cy - 5),
            (cx + 4, cy - 15),
        ])
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_dark"], [
            (cx - 3, cy - 14),
            (cx - 4, cy - 4),
            (cx - 3, cy + 14),
            (cx + 3, cy + 14),
            (cx + 4, cy - 4),
            (cx + 3, cy - 14),
        ])
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_mid"], [
            (cx - 2, cy - 12),
            (cx - 2, cy + 12),
            (cx + 2, cy + 12),
            (cx + 2, cy - 12),
        ])

        # Gold buttons along vest
        for by_off in (-10, -5, 0, 5, 10):
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["gold_dark"],
                             (cx - 1, cy + by_off, 3, 2))
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["gold_mid"],
                             (cx, cy + by_off, 2, 1))
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["gold_light"],
                             (cx, cy + by_off, 1, 1))

        # Coat lapels (edges of open coat)
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["cloth_mid"], [
            (cx - 8, cy - 15),
            (cx - 6, cy - 10),
            (cx - 5, cy + 5),
            (cx - 7, cy + 8),
            (cx - 9, cy),
        ])
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["cloth_mid"], [
            (cx + 8, cy - 15),
            (cx + 6, cy - 10),
            (cx + 5, cy + 5),
            (cx + 7, cy + 8),
            (cx + 9, cy),
        ])

        # White frilly shirt at collar
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["skin_light"], [
            (cx - 3, cy - 18),
            (cx - 4, cy - 12),
            (cx + 4, cy - 12),
            (cx + 3, cy - 18),
        ])
        pygame.draw.rect(surface, _NS_morthraxis.PALETTE["skin_shine"],
                         (cx - 2, cy - 17, 4, 2))

        # Blood glow from chest (magic core)
        for r in range(5, 0, -1):
            alpha = _NS_morthraxis._alpha(80 + math.sin(phase * 2) * 40)
            _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["magic_light"], alpha),
                                      (cx, cy - 3), r)
        pygame.draw.rect(surface, _NS_morthraxis.PALETTE["magic_shine"],
                         (cx, cy - 3, 1, 1))

    def _draw_vampire_arms(surface, cx, cy, facing, phase, cast_lift, attack_progress):
        """Two arms - one may be raised for casting."""
        # Left arm (back arm - viewer's left when facing right)
        back_side = -facing
        front_side = facing

        # Back arm (usually down/at side)
        back_shoulder = (cx + back_side * 10, cy - 15)
        back_elbow = (cx + back_side * 14, cy - 3)
        back_hand = (cx + back_side * 12, cy + 12)

        # Front arm (raises when casting)
        front_shoulder = (cx + front_side * 10, cy - 15)
        if attack_progress > 0:
            # Raise front arm
            front_elbow = (cx + front_side * 16, cy - 10 - cast_lift)
            front_hand = (cx + front_side * 22, cy - 18 - cast_lift * 2)
        else:
            # Elegant pose - hand slightly out
            front_elbow = (cx + front_side * 14, cy - 3 + int(math.sin(phase * 0.6) * 2))
            front_hand = (cx + front_side * 16, cy + 10 + int(math.sin(phase * 0.6) * 2))

        # Draw back arm (behind torso)
        _NS_morthraxis._draw_arm(surface, back_shoulder, back_elbow, back_hand, phase, is_back=True)

        # Draw front arm (over torso)
        _NS_morthraxis._draw_arm(surface, front_shoulder, front_elbow, front_hand, phase, is_back=False)

        # Magic in front hand when casting
        if attack_progress > 0:
            magic_r = int(3 + attack_progress * 5 + math.sin(phase * 3) * 1)
            for r in range(magic_r + 3, 0, -1):
                alpha = _NS_morthraxis._alpha(200 * (magic_r + 3 - r) / (magic_r + 3))
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["magic_dark"], alpha),
                                          front_hand, r)
            _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["magic_mid"], front_hand, magic_r - 1)
            _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["magic_light"], front_hand, magic_r - 2)
            _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["magic_shine"], front_hand,
                                      max(1, magic_r - 4))

            # Sparks around magic
            for i in range(5):
                angle = phase * 4 + i * math.pi * 2 / 5
                sx = front_hand[0] + int(math.cos(angle) * (magic_r + 2))
                sy = front_hand[1] + int(math.sin(angle) * (magic_r + 2))
                pygame.draw.rect(surface, _NS_morthraxis.PALETTE["magic_hot"], (sx, sy, 1, 1))

    def _draw_arm(surface, shoulder, elbow, hand, phase, is_back):
        """Draw a single arm segment."""
        # Upper arm (shoulder to elbow) - black sleeve
        _NS_morthraxis._aaline(surface, _NS_morthraxis.PALETTE["shadow_deep"],
                                (shoulder[0] + 1, shoulder[1] + 1),
                                (elbow[0] + 1, elbow[1] + 1), 5)
        _NS_morthraxis._aaline(surface, _NS_morthraxis.PALETTE["cloth_darkest"], shoulder, elbow, 4)
        _NS_morthraxis._aaline(surface, _NS_morthraxis.PALETTE["cloth_dark"], shoulder, elbow, 3)
        _NS_morthraxis._aaline(surface, _NS_morthraxis.PALETTE["cloth_mid"],
                                (shoulder[0], shoulder[1] - 1),
                                (elbow[0], elbow[1] - 1), 1)

        # Red trim at cuff
        _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["blood_dark"], elbow, 3)
        _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["blood_mid"], elbow, 2)

        # Forearm (elbow to hand) - dark sleeve
        _NS_morthraxis._aaline(surface, _NS_morthraxis.PALETTE["shadow_deep"],
                                (elbow[0] + 1, elbow[1] + 1),
                                (hand[0] + 1, hand[1] + 1), 4)
        _NS_morthraxis._aaline(surface, _NS_morthraxis.PALETTE["cloth_darkest"], elbow, hand, 3)
        _NS_morthraxis._aaline(surface, _NS_morthraxis.PALETTE["cloth_dark"], elbow, hand, 2)

        # Hand (pale)
        _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["shadow_deep"],
                                  (hand[0] + 1, hand[1] + 1), 4)
        _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["skin_darkest"], hand, 3)
        _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["skin_dark"], hand, 2)
        pygame.draw.rect(surface, _NS_morthraxis.PALETTE["skin_mid"],
                         (hand[0] - 1, hand[1] - 1, 2, 2))
        pygame.draw.rect(surface, _NS_morthraxis.PALETTE["skin_light"], (hand[0], hand[1] - 1, 1, 1))

        # Claw fingers (small pointy)
        for i, (dx, dy) in enumerate([(-2, 2), (0, 3), (2, 2)]):
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["skin_dark"],
                             (hand[0] + dx, hand[1] + dy, 1, 1))

    def _draw_vampire_head(surface, cx, cy, facing, phase, attack_progress):
        """Pale vampire head with sharp features."""
        # Head shape (angular, slightly elongated)
        head_pts = [
            (cx - 7, cy - 10),
            (cx - 8, cy - 4),
            (cx - 7, cy + 3),
            (cx - 5, cy + 8),
            (cx - 2, cy + 10),
            (cx + 2, cy + 10),
            (cx + 5, cy + 8),
            (cx + 7, cy + 3),
            (cx + 8, cy - 4),
            (cx + 7, cy - 10),
            (cx + 4, cy - 12),
            (cx - 4, cy - 12),
        ]
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 1) for p in head_pts])
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["skin_darkest"], head_pts)

        # Face main tone
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["skin_dark"], [
            (cx - 6, cy - 9),
            (cx - 7, cy - 3),
            (cx - 6, cy + 2),
            (cx - 4, cy + 7),
            (cx + 4, cy + 7),
            (cx + 6, cy + 2),
            (cx + 7, cy - 3),
            (cx + 6, cy - 9),
            (cx + 3, cy - 11),
            (cx - 3, cy - 11),
        ])
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["skin_mid"], [
            (cx - 5, cy - 7),
            (cx - 6, cy - 2),
            (cx - 4, cy + 4),
            (cx + 4, cy + 4),
            (cx + 6, cy - 2),
            (cx + 5, cy - 7),
        ])
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["skin_light"], [
            (cx - 3, cy - 5),
            (cx - 4, cy - 1),
            (cx - 2, cy + 2),
            (cx + 2, cy + 2),
            (cx + 4, cy - 1),
            (cx + 3, cy - 5),
        ])

        # Cheekbones (angular highlight)
        pygame.draw.rect(surface, _NS_morthraxis.PALETTE["skin_shine"],
                         (cx - 5, cy - 1, 1, 2))
        pygame.draw.rect(surface, _NS_morthraxis.PALETTE["skin_shine"],
                         (cx + 4, cy - 1, 1, 2))

        # Hair (slicked back black)
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["shadow_deep"], [
            (cx - 8, cy - 11),
            (cx - 7, cy - 13),
            (cx - 4, cy - 14),
            (cx + 4, cy - 14),
            (cx + 7, cy - 13),
            (cx + 8, cy - 11),
            (cx + 7, cy - 8),
            (cx - 7, cy - 8),
        ])
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["hair_darkest"], [
            (cx - 7, cy - 11),
            (cx - 6, cy - 12),
            (cx - 3, cy - 13),
            (cx + 3, cy - 13),
            (cx + 6, cy - 12),
            (cx + 7, cy - 11),
            (cx + 6, cy - 9),
            (cx - 6, cy - 9),
        ])
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["hair_dark"], [
            (cx - 5, cy - 11),
            (cx - 3, cy - 12),
            (cx + 3, cy - 12),
            (cx + 5, cy - 11),
            (cx + 4, cy - 10),
            (cx - 4, cy - 10),
        ])
        # Hair highlight
        pygame.draw.rect(surface, _NS_morthraxis.PALETTE["hair_mid"], (cx - 2, cy - 12, 4, 1))
        pygame.draw.rect(surface, _NS_morthraxis.PALETTE["hair_light"], (cx, cy - 12, 2, 1))

        # Widow's peak (V hair)
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["hair_darkest"], [
            (cx - 2, cy - 9),
            (cx, cy - 6),
            (cx + 2, cy - 9),
        ])
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["hair_dark"], [
            (cx - 1, cy - 9),
            (cx, cy - 7),
            (cx + 1, cy - 9),
        ])

        # Pointed ear (elvish/vampire)
        ear_side = -facing  # visible ear on back-facing side
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["skin_darkest"], [
            (cx + ear_side * 7, cy - 5),
            (cx + ear_side * 10, cy - 6),
            (cx + ear_side * 8, cy - 1),
        ])
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["skin_dark"], [
            (cx + ear_side * 7, cy - 4),
            (cx + ear_side * 9, cy - 5),
            (cx + ear_side * 8, cy - 2),
        ])

        # RED VAMPIRE EYES (both visible in slight 3/4 view)
        _NS_morthraxis._draw_vampire_eyes(surface, cx, cy - 3, facing, phase)

        # Nose (subtle)
        pygame.draw.rect(surface, _NS_morthraxis.PALETTE["skin_darkest"],
                         (cx + facing, cy + 1, 1, 2))

        # MOUTH with FANGS
        mouth_open = 0
        if attack_progress > 0:
            mouth_open = int(math.sin(attack_progress * math.pi) * 3)
        _NS_morthraxis._draw_vampire_mouth(surface, cx, cy + 5, facing, mouth_open)

    def _draw_vampire_eyes(surface, cx, cy, facing, phase):
        """Two glowing red eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        for eye_offset in (-3, 3):
            ex = cx + eye_offset
            ey = cy

            # Eye socket (dark)
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 3, 3))
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["eye_socket"],
                             (ex - 1, ey, 3, 2))

            # Glow halo
            for radius in range(4, 0, -1):
                alpha = _NS_morthraxis._alpha(100 * (4 - radius) / 4 * pulse)
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["eye_mid"], alpha),
                                          (ex, ey), radius)

            # Iris
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["eye_darkest"],
                             (ex - 1, ey, 3, 2))
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["eye_mid"],
                             (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            # Highlight
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["eye_glow"],
                             (ex + 1, ey, 1, 1))

        # Brow (menacing)
        pygame.draw.line(surface, _NS_morthraxis.PALETTE["hair_darkest"],
                         (cx - 5, cy - 2), (cx - 1, cy - 3), 1)
        pygame.draw.line(surface, _NS_morthraxis.PALETTE["hair_darkest"],
                         (cx + 1, cy - 3), (cx + 5, cy - 2), 1)

    def _draw_vampire_mouth(surface, cx, cy, facing, mouth_open):
        """Mouth with prominent fangs."""
        if mouth_open > 0:
            # Open mouth
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["shadow_deep"],
                             (cx - 2, cy, 5, mouth_open))
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["eye_darkest"],
                             (cx - 1, cy + 1, 3, max(1, mouth_open - 1)))

            # Fangs prominent
            for fang_x in (cx - 1, cx + 1):
                pygame.draw.line(surface, _NS_morthraxis.PALETTE["fang_dark"],
                                 (fang_x, cy), (fang_x, cy + mouth_open), 1)
                pygame.draw.rect(surface, _NS_morthraxis.PALETTE["fang_mid"],
                                 (fang_x, cy, 1, mouth_open))
                pygame.draw.rect(surface, _NS_morthraxis.PALETTE["fang_shine"],
                                 (fang_x, cy + mouth_open - 1, 1, 1))
        else:
            # Closed mouth line with fang hint
            pygame.draw.line(surface, _NS_morthraxis.PALETTE["shadow_deep"],
                             (cx - 2, cy), (cx + 2, cy), 1)
            # Small fang tips visible
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["fang_mid"],
                             (cx - 1, cy + 1, 1, 1))
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["fang_mid"],
                             (cx + 1, cy + 1, 1, 1))
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["fang_light"],
                             (cx - 1, cy + 1, 1, 1))
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["fang_light"],
                             (cx + 1, cy + 1, 1, 1))

    def _draw_high_collar(surface, cx, cy, facing, phase):
        """Tall pointed vampire collar."""
        # High collar rising behind head
        collar_pts = [
            (cx - 10, cy + 8),
            (cx - 12, cy),
            (cx - 10, cy - 10),
            (cx - 6, cy - 18),
            (cx - 2, cy - 20),
            (cx + 2, cy - 20),
            (cx + 6, cy - 18),
            (cx + 10, cy - 10),
            (cx + 12, cy),
            (cx + 10, cy + 8),
        ]
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["shadow_deep"],
                              [(p[0] + 1, p[1] + 1) for p in collar_pts])
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_darkest"], collar_pts)

        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_dark"], [
            (cx - 8, cy + 6),
            (cx - 10, cy),
            (cx - 8, cy - 8),
            (cx - 4, cy - 15),
            (cx + 4, cy - 15),
            (cx + 8, cy - 8),
            (cx + 10, cy),
            (cx + 8, cy + 6),
        ])

        # Inner collar (mid tone)
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_mid"], [
            (cx - 6, cy + 4),
            (cx - 8, cy),
            (cx - 6, cy - 6),
            (cx - 3, cy - 12),
            (cx + 3, cy - 12),
            (cx + 6, cy - 6),
            (cx + 8, cy),
            (cx + 6, cy + 4),
        ])

        # Gold trim on collar edges
        pygame.draw.line(surface, _NS_morthraxis.PALETTE["gold_dark"],
                         (cx - 10, cy), (cx - 6, cy - 18), 1)
        pygame.draw.line(surface, _NS_morthraxis.PALETTE["gold_mid"],
                         (cx - 10, cy), (cx - 6, cy - 18), 1)
        pygame.draw.line(surface, _NS_morthraxis.PALETTE["gold_dark"],
                         (cx + 10, cy), (cx + 6, cy - 18), 1)
        pygame.draw.line(surface, _NS_morthraxis.PALETTE["gold_mid"],
                         (cx + 10, cy), (cx + 6, cy - 18), 1)

        # Highlight on collar rim
        pygame.draw.rect(surface, _NS_morthraxis.PALETTE["blood_hot"],
                         (cx - 6, cy - 15, 1, 2))
        pygame.draw.rect(surface, _NS_morthraxis.PALETTE["blood_hot"],
                         (cx + 5, cy - 15, 1, 2))

    def _draw_floating_wisps(surface, cx, cy, phase):
        """Blood mist wisps under the floating body (feet area)."""
        # No feet - just swirling blood mist
        for i in range(8):
            angle = phase * 0.8 + i * math.pi / 4
            r = 12 + int(math.sin(phase * 1.5 + i) * 4)
            wx = cx + int(math.cos(angle) * r)
            wy = cy + int(math.sin(angle) * r * 0.4)
            alpha = _NS_morthraxis._alpha(180 + math.sin(phase * 2 + i) * 60)
            _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["blood_dark"], alpha),
                                      (wx, wy), 3)
            _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["blood_mid"], alpha),
                                      (wx, wy), 2)
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["blood_hot"], (wx, wy, 1, 1))

        # Small bats orbiting feet
        for i in range(3):
            angle = phase * 1.2 + i * math.pi * 2 / 3
            bat_x = cx + int(math.cos(angle) * 20)
            bat_y = cy + int(math.sin(angle) * 6) - 2
            _NS_morthraxis._draw_mini_bat(surface, bat_x, bat_y, phase + i)

    def _draw_mini_bat(surface, cx, cy, phase):
        """Small decorative bat."""
        flap = math.sin(phase * 4) * 2
        # Body
        pygame.draw.rect(surface, _NS_morthraxis.PALETTE["hair_darkest"],
                         (cx - 1, cy, 2, 2))
        # Wings
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["hair_darkest"], [
            (cx - 1, cy),
            (cx - 4, cy - int(flap)),
            (cx - 3, cy + 1),
        ])
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["hair_darkest"], [
            (cx + 1, cy),
            (cx + 4, cy - int(flap)),
            (cx + 3, cy + 1),
        ])
        pygame.draw.rect(surface, _NS_morthraxis.PALETTE["blood_hot"], (cx, cy, 1, 1))

    # ============================================================
    # BASIC ATTACK - Bat Projectile
    # ============================================================
    def _draw_basic_bat_projectile(surface, boss, x, y):
        """Small bat projectile flies toward target."""
        progress = getattr(boss, "_mrx_attack_progress", 0)
        if progress < 0.5:
            return

        facing = boss.direction
        tx, ty = _NS_morthraxis._target_position(boss, x, y)
        start_x = x + facing * 20
        start_y = y - 20

        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Trail
        for i in range(6):
            trail_t = max(0.0, t - i * 0.08)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_morthraxis._alpha(220 - i * 35)
            size = max(1, 4 - i)
            _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["blood_dark"], alpha),
                                      (px, py), size)
            _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["blood_mid"], alpha),
                                      (px, py), max(1, size - 1))

        # Bat shape at head
        wing_flap = int(math.sin(t * 20) * 3)
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_darkest"], [
            (bx, by),
            (bx - 6, by - wing_flap),
            (bx - 4, by + 2),
        ])
        _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_darkest"], [
            (bx, by),
            (bx + 6, by - wing_flap),
            (bx + 4, by + 2),
        ])
        _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["blood_dark"], (bx, by), 3)
        _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["blood_mid"], (bx, by), 2)
        pygame.draw.rect(surface, _NS_morthraxis.PALETTE["magic_hot"], (bx, by, 1, 1))

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 15 - radius,
                                 120 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 2, 5, 170), (5, 8, 130, 14))
        pygame.draw.ellipse(shadow, (60, 15, 30, 110), (12, 10, 116, 10))
        surface.blit(shadow, (x - 70, y - 15))

    def _draw_blood_aura(surface, x, y, phase):
        """Large crimson/pink aura around boss."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_morthraxis._alpha((95 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_morthraxis._aacircle(aura, (*_NS_morthraxis.PALETTE["mist_dark"], alpha),
                                          (110, 100), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_morthraxis._alpha((60 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_morthraxis._aacircle(aura, (*_NS_morthraxis.PALETTE["mist_mid"], alpha),
                                          (110, 100), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_morthraxis._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_morthraxis._aacircle(aura, (*_NS_morthraxis.PALETTE["magic_dark"], alpha),
                                          (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))

        # Floating blood embers
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 38 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            color = _NS_morthraxis.PALETTE["blood_mid"] if i % 2 == 0 else _NS_morthraxis.PALETTE["magic_mid"]
            hot = _NS_morthraxis.PALETTE["blood_hot"] if i % 2 == 0 else _NS_morthraxis.PALETTE["magic_hot"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, hot, (sx, sy, 1, 1))

    def _draw_blood_mist(surface, cx, cy, phase):
        """Blood mist floating around boss."""
        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(30, 3, -3):
            alpha = _NS_morthraxis._alpha((30 - radius) * 2.6 * pulse)
            if alpha > 0:
                pygame.draw.ellipse(mist, (*_NS_morthraxis.PALETTE["mist_dark"], alpha),
                                    (75 - radius * 2, 25 - radius // 3,
                                     radius * 4, max(3, radius // 2)))
        surface.blit(mist, (cx - 75, cy - 10))

        # Rising blood droplets
        for i in range(6):
            t = (phase * 0.4 + i * 0.15) % 1.0
            sx = cx + (-20 + i * 8) + int(math.sin(phase + i) * 3)
            sy = cy + 4 - int(t * 24)
            alpha = _NS_morthraxis._alpha(220 * (1 - t))
            if alpha > 0:
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["blood_dark"], alpha),
                                          (sx, sy), 2)
                pygame.draw.rect(surface, _NS_morthraxis.PALETTE["blood_hot"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring with runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_morthraxis.PALETTE["mist_dark"], 200),
                            (5, 18, 160, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_morthraxis.PALETTE["blood_darkest"], 220),
                            (14, 20, 142, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_morthraxis.PALETTE["blood_dark"], 230),
                            (25, 22, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_morthraxis.PALETTE["magic_dark"], 180),
                            (40, 24, 90, 14), 1)

        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 46)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 85 + int(math.cos(angle) * 72)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_morthraxis.PALETTE["blood_hot"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_morthraxis.PALETTE["magic_hot"],
                                 _NS_morthraxis._alpha(150 * pulse)),
                                (15, 12, 140, 38), 1)
        surface.blit(ring, (x - 85, y - 27))

    # ============================================================
    # SKILL Q - BAT IMPALE (ranged spear-bat projectile)
    # ============================================================
    def _draw_bat_impale(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morthraxis._target_position(boss, x, y)

        if progress < 0.25:
            # Charging in hand
            t = progress / 0.25
            hand_x = x + facing * 22
            hand_y = y - 22
            cr = int(4 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_morthraxis._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["magic_dark"], alpha),
                                          (hand_x, hand_y), r)
            _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["magic_mid"], (hand_x, hand_y), cr - 2)
            _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["magic_light"], (hand_x, hand_y),
                                      max(1, cr - 4))
            _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["magic_shine"], (hand_x, hand_y),
                                      max(1, cr - 6))
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                sx = hand_x + int(math.cos(angle) * (cr + 3))
                sy = hand_y + int(math.sin(angle) * (cr + 3))
                pygame.draw.rect(surface, _NS_morthraxis.PALETTE["magic_hot"], (sx, sy, 1, 1))
        else:
            # Flying bat-spear
            t = (progress - 0.25) / 0.75
            start_x = x + facing * 26
            start_y = y - 22
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Long comet trail
            for i in range(11):
                trail_t = max(0.0, t - i * 0.04)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_morthraxis._alpha(240 - i * 22)
                size = max(1, 8 - i)
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["blood_darkest"], alpha),
                                          (px, py), size)
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["blood_dark"], alpha),
                                          (px, py), max(1, size - 1))
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["blood_mid"], alpha),
                                          (px, py), max(1, size - 2))
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["magic_light"], alpha),
                                          (px, py), max(1, size - 3))
                if i < 5:
                    for s in range(2):
                        spark_x = px + int(math.sin(t * 8 + i + s) * (size + 2))
                        spark_y = py + int(math.cos(t * 8 + i + s) * (size + 2))
                        pygame.draw.rect(surface,
                                         (*_NS_morthraxis.PALETTE["magic_hot"], alpha),
                                         (spark_x, spark_y, 1, 1))

            # Bat-spear head (elongated bat shape)
            wing_span = 8 + int(math.sin(phase * 8) * 2)
            # Direction angle
            angle = math.atan2(ty - start_y, tx - start_x)
            perp = angle + math.pi / 2
            spear_len = 14
            tip_x = bx + int(math.cos(angle) * spear_len)
            tip_y = by + int(math.sin(angle) * spear_len)
            base_a = (bx + int(math.cos(perp) * wing_span),
                      by + int(math.sin(perp) * wing_span))
            base_b = (bx - int(math.cos(perp) * wing_span),
                      by - int(math.sin(perp) * wing_span))

            # Bat wings (spread)
            _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_darkest"], [
                (bx, by), base_a,
                (bx - int(math.cos(angle) * 6), by - int(math.sin(angle) * 6)),
            ])
            _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_darkest"], [
                (bx, by), base_b,
                (bx - int(math.cos(angle) * 6), by - int(math.sin(angle) * 6)),
            ])
            # Wing membrane
            _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_dark"], [
                (bx, by), base_a,
                (bx - int(math.cos(angle) * 4), by - int(math.sin(angle) * 4)),
            ])
            _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_dark"], [
                (bx, by), base_b,
                (bx - int(math.cos(angle) * 4), by - int(math.sin(angle) * 4)),
            ])

            # Spear tip
            _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_darkest"],
                                  [(tip_x, tip_y), base_a, base_b])
            _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_dark"], [
                (tip_x, tip_y),
                (int((tip_x + base_a[0]) / 2), int((tip_y + base_a[1]) / 2)),
                (bx, by),
                (int((tip_x + base_b[0]) / 2), int((tip_y + base_b[1]) / 2)),
            ])
            _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["magic_hot"], (tip_x, tip_y), 2)
            _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["magic_shine"], (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["white"], (tip_x, tip_y, 1, 1))

            # Impact
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(10 + st * 25)
                alpha = _NS_morthraxis._alpha(240 * (1 - st))
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["blood_darkest"], alpha),
                                          (tx, ty), radius + 3, 3)
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["blood_dark"], alpha),
                                          (tx, ty), radius, 3)
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["blood_mid"], alpha),
                                          (tx, ty), max(1, radius - 5), 2)
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["magic_light"], alpha),
                                          (tx, ty), max(1, radius - 10), 1)
                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * radius)
                    ey = ty + int(math.sin(angle_s) * radius * 0.7)
                    pygame.draw.rect(surface, (*_NS_morthraxis.PALETTE["magic_hot"], alpha),
                                     (ex, ey, 2, 2))

    # ============================================================
    # SKILL W - SANGUINE CLAWS (orbiting bats around target)
    # ============================================================
    def _draw_sanguine_ground(surface, boss, x, y, timer, phase):
        """Ground swirl at target."""
        tx, ty = _NS_morthraxis._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_morthraxis.PALETTE["blood_darkest"], 180),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_morthraxis.PALETTE["blood_dark"], 160),
                                (tx - r + 4, ty - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4))

    def _draw_sanguine_bats(surface, boss, x, y, timer, phase):
        """Bats orbiting around target."""
        tx, ty = _NS_morthraxis._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        orbit_r = int(50 * min(1.0, progress * 3))

        if orbit_r < 5:
            return

        # Multiple orbiting bats
        num_bats = 8
        for i in range(num_bats):
            angle = phase * 2 + i * math.pi * 2 / num_bats
            bx = tx + int(math.cos(angle) * orbit_r)
            by = ty + int(math.sin(angle) * orbit_r * 0.5)

            # Trail behind bat
            for tr in range(4):
                trail_angle = angle - tr * 0.15
                trx = tx + int(math.cos(trail_angle) * orbit_r)
                try_ = ty + int(math.sin(trail_angle) * orbit_r * 0.5)
                alpha = _NS_morthraxis._alpha(180 - tr * 40)
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["blood_dark"], alpha),
                                          (trx, try_), max(1, 3 - tr))

            # Bat itself
            wing_flap = int(math.sin(phase * 8 + i) * 3)
            _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["hair_darkest"], [
                (bx, by),
                (bx - 5, by - wing_flap),
                (bx - 4, by + 1),
            ])
            _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["hair_darkest"], [
                (bx, by),
                (bx + 5, by - wing_flap),
                (bx + 4, by + 1),
            ])
            _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_darkest"], [
                (bx, by),
                (bx - 3, by - wing_flap + 1),
                (bx - 3, by + 1),
            ])
            _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_darkest"], [
                (bx, by),
                (bx + 3, by - wing_flap + 1),
                (bx + 3, by + 1),
            ])
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["blood_dark"],
                             (bx - 1, by, 2, 2))
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["eye_light"], (bx, by, 1, 1))

        # Center pulse
        pulse_r = 8 + int(math.sin(phase * 3) * 3)
        for r in range(pulse_r, 0, -1):
            alpha = _NS_morthraxis._alpha(100 * (pulse_r - r) / pulse_r)
            _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["blood_hot"], alpha), (tx, ty), r)

    # ============================================================
    # SKILL E - PHANTOM MOB (piercing bat swarm skillshot)
    # ============================================================
    def _draw_phantom_mob(surface, boss, x, y, timer, phase):
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morthraxis._target_position(boss, x, y)

        start_x = x + facing * 26
        start_y = y - 12

        if progress < 0.15:
            # Charging
            t = progress / 0.15
            cr = int(6 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_morthraxis._alpha(180 * (cr + 5 - r) / (cr + 5))
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["magic_dark"], alpha),
                                          (start_x, start_y), r)
            _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["magic_mid"], (start_x, start_y),
                                      cr - 2)
            _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["magic_light"], (start_x, start_y),
                                      max(1, cr - 4))
        else:
            # Phantom bats flying in a line
            t = (progress - 0.15) / 0.85
            # Total distance
            dist = math.hypot(tx - start_x, ty - start_y)
            angle = math.atan2(ty - start_y, tx - start_x)

            # Head position (leading bat)
            head_x = int(start_x + math.cos(angle) * dist * t)
            head_y = int(start_y + math.sin(angle) * dist * t)

            # Multiple phantom bats spread out along path
            num_bats = 6
            for i in range(num_bats):
                lag = i * 0.06
                bat_t = max(0.0, t - lag)
                bx = int(start_x + math.cos(angle) * dist * bat_t)
                by = int(start_y + math.sin(angle) * dist * bat_t)

                # Sway perpendicular
                perp = angle + math.pi / 2
                sway = math.sin(phase * 3 + i) * (8 + i)
                bx += int(math.cos(perp) * sway)
                by += int(math.sin(perp) * sway)

                alpha = _NS_morthraxis._alpha(240 - i * 20)
                # Bat body
                wing_flap = int(math.sin(phase * 10 + i) * 4)
                _NS_morthraxis._poly(surface,
                                      (*_NS_morthraxis.PALETTE["blood_darkest"], alpha), [
                    (bx, by),
                    (bx - 7, by - wing_flap),
                    (bx - 5, by + 2),
                ])
                _NS_morthraxis._poly(surface,
                                      (*_NS_morthraxis.PALETTE["blood_darkest"], alpha), [
                    (bx, by),
                    (bx + 7, by - wing_flap),
                    (bx + 5, by + 2),
                ])
                _NS_morthraxis._poly(surface,
                                      (*_NS_morthraxis.PALETTE["blood_dark"], alpha), [
                    (bx, by),
                    (bx - 4, by - wing_flap + 1),
                    (bx - 3, by + 1),
                ])
                _NS_morthraxis._poly(surface,
                                      (*_NS_morthraxis.PALETTE["blood_dark"], alpha), [
                    (bx, by),
                    (bx + 4, by - wing_flap + 1),
                    (bx + 3, by + 1),
                ])
                _NS_morthraxis._aacircle(surface,
                                          (*_NS_morthraxis.PALETTE["blood_mid"], alpha),
                                          (bx, by), 2)
                pygame.draw.rect(surface, _NS_morthraxis.PALETTE["eye_light"], (bx, by, 1, 1))

            # Head bat is BIGGER (main phantom)
            _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["shadow_deep"], [
                (head_x + 1, head_y + 1),
                (head_x - 11, head_y - 5),
                (head_x - 9, head_y + 4),
            ])
            _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["shadow_deep"], [
                (head_x + 1, head_y + 1),
                (head_x + 11, head_y - 5),
                (head_x + 9, head_y + 4),
            ])
            wing_flap_big = int(math.sin(phase * 10) * 5)
            _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_darkest"], [
                (head_x, head_y),
                (head_x - 10, head_y - wing_flap_big),
                (head_x - 8, head_y + 3),
            ])
            _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_darkest"], [
                (head_x, head_y),
                (head_x + 10, head_y - wing_flap_big),
                (head_x + 8, head_y + 3),
            ])
            _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_dark"], [
                (head_x, head_y),
                (head_x - 6, head_y - wing_flap_big + 1),
                (head_x - 5, head_y + 2),
            ])
            _NS_morthraxis._poly(surface, _NS_morthraxis.PALETTE["blood_dark"], [
                (head_x, head_y),
                (head_x + 6, head_y - wing_flap_big + 1),
                (head_x + 5, head_y + 2),
            ])
            _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["blood_mid"], (head_x, head_y), 3)
            _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["magic_hot"], (head_x, head_y), 2)
            pygame.draw.rect(surface, _NS_morthraxis.PALETTE["magic_shine"], (head_x, head_y, 1, 1))

            # Glow trail
            for i in range(8):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + math.cos(angle) * dist * trail_t)
                py = int(start_y + math.sin(angle) * dist * trail_t)
                alpha = _NS_morthraxis._alpha(180 - i * 20)
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["magic_dark"], alpha),
                                          (px, py), max(1, 6 - i))
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["magic_light"], alpha),
                                          (px, py), max(1, 3 - i // 2))

            # Explosion on impact
            if t > 0.85:
                st = (t - 0.85) / 0.15
                radius = int(15 + st * 30)
                alpha = _NS_morthraxis._alpha(240 * (1 - st))
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["blood_darkest"], alpha),
                                          (tx, ty), radius + 3, 3)
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["blood_dark"], alpha),
                                          (tx, ty), radius, 3)
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["magic_mid"], alpha),
                                          (tx, ty), max(1, radius - 6), 2)
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["magic_light"], alpha),
                                          (tx, ty), max(1, radius - 12), 1)
                # Radial bat burst
                for i in range(10):
                    burst_angle = i * math.pi / 5
                    ex = tx + int(math.cos(burst_angle) * radius)
                    ey = ty + int(math.sin(burst_angle) * radius * 0.7)
                    _NS_morthraxis._draw_mini_bat(surface, ex, ey, phase + i)

    # ============================================================
    # SKILL R - BALEFUL TRANSFORMATION (buff ultimate)
    # ============================================================
    def _draw_baleful_ground(surface, boss, x, y, timer, phase):
        """Ground energy rings under boss."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(3):
            r = int(40 + i * 10 + math.sin(phase * 2 + i) * 4)
            alpha = _NS_morthraxis._alpha(200 - i * 50)
            _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["blood_dark"], alpha),
                                      (x, y + 40), r, 2)
            _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["magic_light"], alpha),
                                      (x, y + 40), r, 1)

    def _draw_baleful_foreground(surface, boss, x, y, timer, phase):
        """Massive aura + bats spiral upward + wings expanding."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Rising aura column
        for i in range(15):
            t = (phase * 1.2 + i * 0.1) % 1.0
            rx = x + int(math.sin(phase + i) * 30)
            ry = y + 30 - int(t * 80)
            alpha = _NS_morthraxis._alpha(200 * (1 - t))
            if alpha > 0:
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["blood_dark"], alpha),
                                          (rx, ry), 4)
                _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["magic_light"], alpha),
                                          (rx, ry), 2)
                pygame.draw.rect(surface, _NS_morthraxis.PALETTE["magic_shine"], (rx, ry, 1, 1))

        # Giant abyssal wings expanding from back
        wing_scale = min(1.0, progress * 2)
        wing_span = int(80 * wing_scale)
        for side in (-1, 1):
            # Multiple wing bones
            for i, angle_deg in enumerate((30, 15, 0, -15, -30)):
                angle = math.radians(angle_deg + math.sin(phase) * 5)
                tip_x = x + side * int(math.cos(angle) * wing_span)
                tip_y = y - 10 - int(math.sin(angle) * wing_span)
                # Bone
                pygame.draw.line(surface, _NS_morthraxis.PALETTE["shadow_deep"],
                                 (x, y - 10), (tip_x, tip_y), 3)
                pygame.draw.line(surface, _NS_morthraxis.PALETTE["hair_darkest"],
                                 (x, y - 10), (tip_x, tip_y), 2)
                # Claw tip
                _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["blood_hot"],
                                          (tip_x, tip_y), 2)

            # Membrane between bones
            membrane = [(x, y - 10)]
            for angle_deg in (30, 15, 0, -15, -30):
                angle = math.radians(angle_deg + math.sin(phase) * 5)
                tip_x = x + side * int(math.cos(angle) * wing_span)
                tip_y = y - 10 - int(math.sin(angle) * wing_span)
                membrane.append((tip_x, tip_y))
            membrane.append((x, y + 20))

            wing_surf = pygame.Surface((wing_span * 2 + 40, wing_span * 2 + 40),
                                        pygame.SRCALPHA)
            offset_x = x - wing_span - 20
            offset_y = y - wing_span - 20
            local = [(p[0] - offset_x, p[1] - offset_y) for p in membrane]
            _NS_morthraxis._poly(wing_surf,
                                  (*_NS_morthraxis.PALETTE["blood_darkest"], 180), local)
            _NS_morthraxis._poly(wing_surf,
                                  (*_NS_morthraxis.PALETTE["blood_dark"], 160), local)
            surface.blit(wing_surf, (offset_x, offset_y))

        # Orbiting bats
        for i in range(10):
            angle = phase * 2 + i * math.pi / 5
            r = 50 + int(math.sin(phase * 1.5 + i) * 10)
            bx = x + int(math.cos(angle) * r)
            by = y + int(math.sin(angle) * r * 0.5)
            _NS_morthraxis._draw_mini_bat(surface, bx, by, phase + i)

        # Crown-like glow above head
        crown_y = y - 60
        for r in range(8, 0, -1):
            alpha = _NS_morthraxis._alpha(200 * (8 - r) / 8)
            _NS_morthraxis._aacircle(surface, (*_NS_morthraxis.PALETTE["magic_hot"], alpha),
                                      (x, crown_y), r)
        _NS_morthraxis._aacircle(surface, _NS_morthraxis.PALETTE["magic_shine"], (x, crown_y), 2)
        pygame.draw.rect(surface, _NS_morthraxis.PALETTE["white"], (x, crown_y, 1, 1))


# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_astraelion(surface, boss, x, y):
    """Entry point astraelion."""
    return _NS_astraelion.draw_astraelion(surface, boss, x, y)


def draw_morvaenthir(surface, boss, x, y):
    """Entry point morvaenthir."""
    return _NS_morvaenthir.draw_morvaenthir(surface, boss, x, y)


def draw_thornvaegrim(surface, boss, x, y):
    """Entry point thornvaegrim."""
    return _NS_thornvaegrim.draw_thornvaegrim(surface, boss, x, y)


def draw_morthraxis(surface, boss, x, y):
    """Entry point morthraxis."""
    return _NS_morthraxis.draw_morthraxis(surface, boss, x, y)
