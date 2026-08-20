"""
bosses/level32.py - Semua boss Level 32

Berisi:
  - ghrakmaal  (mini boss - MELEE colossus of sundered earth)
  - selunara   (mini boss - RANGED moonbound huntress, lunar archer)
  - vessyra    (mini boss - RANGED gorgon queen, petrify gaze)
  - malzeroth  (TRUE BOSS - RANGED hexbound sovereign, hex mage)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _gh_ (ghrakmaal), _vy_ (vessyra), _mz_ (malzeroth) sudah unik.
  - _sl_ (selunara) di-rename -> _sel_ (bentrok dengan solareth
    level 24), termasuk atribut _last_x/_last_y.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# GHRAKMAAL (COLOSSUS OF SUNDERED EARTH) - Mini Boss
# ====================================================================

class _NS_ghrakmaal:
    """Namespace ghrakmaal - true boss earth titan."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Fur/mane (orange-brown lion mane)
        "fur_darkest": (30, 15, 5),
        "fur_dark": (75, 40, 15),
        "fur_mid": (140, 80, 30),
        "fur_light": (200, 130, 55),
        "fur_shine": (240, 180, 90),
        # Bull skin (tan-brown)
        "skin_darkest": (35, 20, 10),
        "skin_dark": (85, 55, 30),
        "skin_mid": (140, 100, 65),
        "skin_light": (195, 155, 110),
        "skin_shine": (235, 200, 155),
        # Horns/tusks (bone)
        "bone_dark": (55, 40, 25),
        "bone_mid": (140, 115, 80),
        "bone_light": (215, 195, 155),
        "bone_shine": (250, 235, 200),
        # Totem wood (dark stained)
        "wood_darkest": (20, 10, 5),
        "wood_dark": (55, 30, 15),
        "wood_mid": (110, 65, 35),
        "wood_light": (170, 115, 65),
        "wood_shine": (220, 170, 110),
        # Totem iron bands (dark steel)
        "iron_darkest": (10, 8, 6),
        "iron_dark": (35, 30, 25),
        "iron_mid": (75, 68, 60),
        "iron_light": (145, 138, 128),
        "iron_shine": (210, 205, 195),
        # Rune/glow on totem (fiery orange)
        "rune_dark": (85, 25, 5),
        "rune_mid": (200, 75, 15),
        "rune_light": (255, 145, 40),
        "rune_shine": (255, 220, 130),
        # Molten earth (skills)
        "molten_darkest": (30, 8, 3),
        "molten_dark": (110, 30, 8),
        "molten_mid": (215, 90, 20),
        "molten_light": (255, 165, 55),
        "molten_hot": (255, 220, 130),
        "molten_shine": (255, 250, 200),
        # Rock (fissure debris)
        "rock_darkest": (18, 15, 12),
        "rock_dark": (55, 45, 38),
        "rock_mid": (100, 85, 70),
        "rock_light": (160, 140, 115),
        # Eye (orange fiery)
        "eye_socket": (10, 5, 2),
        "eye_dark": (95, 25, 5),
        "eye_mid": (220, 90, 20),
        "eye_light": (255, 170, 60),
        "eye_glow": (255, 235, 160),
        # Leather straps
        "leather_dark": (35, 20, 12),
        "leather_mid": (75, 45, 25),
        "leather_light": (130, 85, 45),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_ghrakmaal._clamp(color)
        if _NS_ghrakmaal.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_ghrakmaal._clamp(color)
        if _NS_ghrakmaal.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_ghrakmaal._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 200 * getattr(boss, "direction", 1)), int(y)
    def _totem_position(boss, x, y):
        """Posisi totem: on back (idle) atau di tangan (swing overhead → smash down)."""
        facing = boss.direction
        active_progress = getattr(boss, "_gh_attack_progress", 0.0)
        active = getattr(boss, "_gh_attack_active", False)
        # Idle: totem di punggung.
        if not active:
            return x - facing * 12, y - 32, "idle"
        p = active_progress
        # Idle start point (posisi di punggung).
        idle_x, idle_y = x - facing * 12, y - 32
        # Overhead point (di atas kepala, sedikit ke depan).
        overhead_x, overhead_y = x + facing * 4, y - 62
        # Impact point (di depan bawah, hantam tanah).
        impact_x, impact_y = x + facing * 26, y + 12
        if p < 0.40:
            # WIND UP: angkat totem dari punggung ke atas kepala (LAMBAT karena berat).
            t = p / 0.40
            # Ease-in (mulai pelan, terus cepat).
            t = t * t
            tx = int(idle_x + (overhead_x - idle_x) * t)
            ty = int(idle_y + (overhead_y - idle_y) * t)
            return tx, ty, "swing_up"
        elif p < 0.58:
            # SMASH DOWN: hantam cepat dari atas ke bawah.
            t = (p - 0.40) / 0.18
            # Ease-out (mulai cepat karena momentum).
            t = 1 - (1 - t) * (1 - t)
            tx = int(overhead_x + (impact_x - overhead_x) * t)
            ty = int(overhead_y + (impact_y - overhead_y) * t)
            return tx, ty, "swing_down"
        elif p < 0.75:
            # IMPACT HOLD: totem menempel di tanah.
            return impact_x, impact_y, "impact"
        else:
            # RETURN: kembali ke punggung.
            t = (p - 0.75) / 0.25
            # Ease-out (halus).
            t = 1 - (1 - t) * (1 - t)
            tx = int(impact_x + (idle_x - impact_x) * t)
            ty = int(impact_y + (idle_y - impact_y) * t)
            return tx, ty, "return"
    def _arm_elbow(shoulder, hand, bend=4):
        """Hitung posisi siku antara shoulder dan hand dengan tekukan alami ke bawah."""
        sx, sy = shoulder
        hx, hy = hand
        mid_x = (sx + hx) / 2
        mid_y = (sy + hy) / 2
        dx = hx - sx
        dy = hy - sy
        # Perpendicular (tegak lurus lengan).
        length = max(1.0, math.sqrt(dx * dx + dy * dy))
        perp_x = -dy / length
        perp_y = dx / length
        # Elbow selalu tekuk ke bawah (positif y).
        if perp_y < 0:
            perp_x = -perp_x
            perp_y = -perp_y
        return (int(mid_x + perp_x * bend), int(mid_y + perp_y * bend))
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_ghrakmaal(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_ghrakmaal._update_attack_anim(boss)
        attack_progress = getattr(boss, "_gh_attack_progress", 0.0)
        attacking = (
            getattr(boss, "_gh_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 55) - 15
        )
        # Ambient FX.
        _NS_ghrakmaal._draw_earth_aura(surface, x, y, pulse)
        _NS_ghrakmaal._draw_ground_ring(surface, x, y + 54, pulse, active_skill)
        # Skill ground FX (behind body).
        if active_skill == "q":
            _NS_ghrakmaal._draw_fissure_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_ghrakmaal._draw_aftershock_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_ghrakmaal._draw_echoslam_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_ghrakmaal._draw_enchanttotem_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating body (heavy floating).
        float_bob = math.sin(pulse * 0.4) * 3
        body_y = y + int(float_bob)
        # Body pose.
        if attacking:
            _NS_ghrakmaal._draw_body_attack(surface, boss, x, body_y)
        else:
            _NS_ghrakmaal._draw_body_idle(surface, boss, x, body_y)
        # Foreground FX.
        if active_skill == "q":
            _NS_ghrakmaal._draw_fissure_foreground(surface, boss, x, body_y,
                                                    skill_timer, pulse)
        elif active_skill == "w":
            _NS_ghrakmaal._draw_aftershock_foreground(surface, boss, x, body_y,
                                                       skill_timer, pulse)
        elif active_skill == "e":
            _NS_ghrakmaal._draw_echoslam_foreground(surface, boss, x, body_y,
                                                      skill_timer, pulse)
        elif active_skill == "r":
            _NS_ghrakmaal._draw_enchanttotem_projectile(surface, boss, x, body_y,
                                                         skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 55)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_gh_attack_active", False))
        if not active and timer >= cooldown - 2:
            boss._gh_attack_active = True
            boss._gh_attack_frame = 0
            active = True
        elif active:
            boss._gh_attack_frame = int(getattr(boss, "_gh_attack_frame", 0)) + 1
            if boss._gh_attack_frame >= cooldown:
                boss._gh_attack_active = False
                boss._gh_attack_frame = 0
                active = False
        boss._gh_previous_timer = timer
        boss._gh_attack_progress = (
            min(1.0, getattr(boss, "_gh_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # BODY DRAWING
    # ============================================================
    def _draw_body_idle(surface, boss, cx, cy):
        _NS_ghrakmaal._draw_float_shadow(surface, cx, cy + 56, boss.pulse)
        _NS_ghrakmaal._draw_earth_dust(surface, cx, cy + 44, boss.pulse)
        _NS_ghrakmaal._draw_body(surface, boss, cx, cy, "idle", 0)
    def _draw_body_attack(surface, boss, cx, cy):
        progress = getattr(boss, "_gh_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        _NS_ghrakmaal._draw_float_shadow(surface, cx, cy + 56, boss.pulse)
        _NS_ghrakmaal._draw_earth_dust(surface, cx, cy + 44, boss.pulse, intense=True)
        _NS_ghrakmaal._draw_body(surface, boss, cx, cy, "attack", progress)
        # Shockwave saat totem menghantam tanah (impact phase: 0.58-0.85).
        if 0.58 < progress < 0.85:
            shockwave_t = (progress - 0.58) / 0.27
            _NS_ghrakmaal._draw_slam_shockwave(surface, boss, cx, cy, shockwave_t)
    def _draw_body(surface, boss, cx, cy, action, progress):
        """Full body: legs, torso, arms, head, totem."""
        facing = boss.direction
        phase = boss.pulse
        totem_x, totem_y, totem_state = _NS_ghrakmaal._totem_position(boss, cx, cy)
        is_idle = (totem_state == "idle")
        # Idle: totem di punggung (di belakang torso).
        if is_idle:
            _NS_ghrakmaal._draw_totem(surface, totem_x, totem_y, facing, phase,
                                       rotated=True)
        # Body parts.
        _NS_ghrakmaal._draw_legs(surface, cx, cy, facing, phase)
        _NS_ghrakmaal._draw_torso(surface, cx, cy, facing, phase)
        _NS_ghrakmaal._draw_mane(surface, cx, cy - 22, facing, phase)
        _NS_ghrakmaal._draw_bull_head(surface, cx, cy - 28, facing, phase, action, progress)
        # Arms (both grip totem when swinging).
        _NS_ghrakmaal._draw_arms(surface, cx, cy, facing, phase, action, progress,
                                  totem_x, totem_y, totem_state)
        # Swinging: totem drawn IN HAND (foreground, in front of body).
        if not is_idle:
            _NS_ghrakmaal._draw_totem(surface, totem_x, totem_y, facing, phase,
                                       rotated=False, swing_progress=progress)
    def _draw_legs(surface, cx, cy, facing, phase):
        """Massive stocky legs."""
        for side in (-1, 1):
            leg_x = cx + side * 12
            # Thigh (bulky).
            thigh_pts = [
                (leg_x - 8, cy + 6),
                (leg_x + 8, cy + 6),
                (leg_x + 10, cy + 18),
                (leg_x + 8, cy + 30),
                (leg_x - 8, cy + 30),
                (leg_x - 10, cy + 18),
            ]
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["shadow_deep"],
                                [(p[0] + 2, p[1] + 2) for p in thigh_pts])
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["skin_darkest"], thigh_pts)
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["skin_dark"], [
                (leg_x - 7, cy + 7),
                (leg_x + 7, cy + 7),
                (leg_x + 9, cy + 18),
                (leg_x + 7, cy + 29),
                (leg_x - 7, cy + 29),
                (leg_x - 9, cy + 18),
            ])
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["skin_mid"], [
                (leg_x - 5, cy + 9),
                (leg_x + 5, cy + 9),
                (leg_x + 7, cy + 18),
                (leg_x + 4, cy + 26),
                (leg_x - 4, cy + 26),
                (leg_x - 7, cy + 18),
            ])
            # Fur tufts on knees.
            for tuft_x in (-4, 0, 4):
                pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["fur_dark"],
                                 (leg_x + tuft_x, cy + 18),
                                 (leg_x + tuft_x - 1, cy + 22), 2)
                pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["fur_mid"],
                                 (leg_x + tuft_x, cy + 18),
                                 (leg_x + tuft_x - 1, cy + 22), 1)
            # Feet (hooved boots).
            foot_pts = [
                (leg_x - 10, cy + 30),
                (leg_x + 10, cy + 30),
                (leg_x + 12, cy + 34),
                (leg_x + 10, cy + 38),
                (leg_x - 10, cy + 38),
                (leg_x - 12, cy + 34),
            ]
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["shadow_deep"],
                                [(p[0] + 2, p[1] + 2) for p in foot_pts])
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["leather_dark"], foot_pts)
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["leather_mid"], [
                (leg_x - 9, cy + 31),
                (leg_x + 9, cy + 31),
                (leg_x + 11, cy + 34),
                (leg_x + 9, cy + 37),
                (leg_x - 9, cy + 37),
                (leg_x - 11, cy + 34),
            ])
            # Iron plating on foot.
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_dark"],
                             (leg_x - 8, cy + 33, 16, 3))
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_mid"],
                             (leg_x - 7, cy + 33, 14, 1))
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_light"],
                             (leg_x - 6, cy + 33, 12, 1))
            # Hoof toenails.
            for toe_x in (-6, -2, 2, 6):
                pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["bone_mid"],
                                 (leg_x + toe_x, cy + 37, 2, 1))
    def _draw_torso(surface, cx, cy, facing, phase):
        """Massive muscular torso."""
        breath = math.sin(phase * 0.5) * 1
        torso_pts = [
            (cx - 22, cy - 15),
            (cx - 26, cy - 5),
            (cx - 24, cy + 6),
            (cx - 18, cy + 12),
            (cx + 18, cy + 12),
            (cx + 24, cy + 6),
            (cx + 26, cy - 5),
            (cx + 22, cy - 15),
            (cx + 14, cy - 20),
            (cx - 14, cy - 20),
        ]
        _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in torso_pts])
        _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["skin_darkest"], torso_pts)
        _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["skin_dark"], [
            (cx - 20, cy - 14),
            (cx - 24, cy - 4),
            (cx - 22, cy + 5),
            (cx - 16, cy + 11),
            (cx + 16, cy + 11),
            (cx + 22, cy + 5),
            (cx + 24, cy - 4),
            (cx + 20, cy - 14),
            (cx + 12, cy - 18),
            (cx - 12, cy - 18),
        ])
        _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["skin_mid"], [
            (cx - 16, cy - 10),
            (cx - 20, cy - 2),
            (cx - 16, cy + 6),
            (cx + 16, cy + 6),
            (cx + 20, cy - 2),
            (cx + 16, cy - 10),
            (cx + 8, cy - 14),
            (cx - 8, cy - 14),
        ])
        # Muscle definition (chest split).
        pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["skin_darkest"],
                         (cx, cy - 12), (cx, cy + 8), 1)
        # Pec shading.
        _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["skin_light"], [
            (cx - 12, cy - 10),
            (cx - 4, cy - 10),
            (cx - 6, cy - 4),
            (cx - 12, cy - 4),
        ])
        _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["skin_light"], [
            (cx + 4, cy - 10),
            (cx + 12, cy - 10),
            (cx + 12, cy - 4),
            (cx + 6, cy - 4),
        ])
        # Highlights.
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["skin_shine"], (cx - 9, cy - 8, 3, 1))
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["skin_shine"], (cx + 7, cy - 8, 3, 1))
        # Abs (small V's).
        for row in range(2):
            for side_ab in (-1, 1):
                ab_y = cy - 2 + row * 4
                pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["skin_darkest"],
                                 (cx + side_ab * 2, ab_y),
                                 (cx + side_ab * 5, ab_y), 1)
        # Big leather belt.
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["leather_dark"],
                         (cx - 22, cy + 7, 44, 6))
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["leather_mid"],
                         (cx - 21, cy + 8, 42, 4))
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["leather_light"],
                         (cx - 20, cy + 9, 40, 1))
        # Iron belt buckle.
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_dark"],
                         (cx - 6, cy + 7, 12, 6))
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_mid"],
                         (cx - 5, cy + 8, 10, 4))
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_light"],
                         (cx - 4, cy + 9, 8, 1))
        # Rune symbol on buckle.
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["rune_mid"], (cx - 1, cy + 9, 2, 2))
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["rune_light"], (cx, cy + 10, 1, 1))
        # Leather straps across chest (X shape).
        pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["leather_dark"],
                         (cx - 20, cy - 12), (cx + 18, cy + 6), 3)
        pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["leather_mid"],
                         (cx - 20, cy - 12), (cx + 18, cy + 6), 2)
        pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["leather_dark"],
                         (cx + 20, cy - 12), (cx - 18, cy + 6), 3)
        pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["leather_mid"],
                         (cx + 20, cy - 12), (cx - 18, cy + 6), 2)
    def _draw_mane(surface, cx, cy, facing, phase):
        """Big lion-like mane around neck/shoulders."""
        sway = math.sin(phase * 0.4) * 1
        # Mane shape (big collar).
        mane_pts = [
            (cx - 24, cy + 4),
            (cx - 28 + int(sway), cy - 2),
            (cx - 26, cy - 10),
            (cx - 20, cy - 14),
            (cx - 12, cy - 15),
            (cx, cy - 16),
            (cx + 12, cy - 15),
            (cx + 20, cy - 14),
            (cx + 26, cy - 10),
            (cx + 28 - int(sway), cy - 2),
            (cx + 24, cy + 4),
            (cx + 16, cy + 6),
            (cx - 16, cy + 6),
        ]
        _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in mane_pts])
        _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["fur_darkest"], mane_pts)
        _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["fur_dark"], [
            (cx - 22, cy + 3),
            (cx - 26 + int(sway), cy - 2),
            (cx - 24, cy - 9),
            (cx - 18, cy - 13),
            (cx - 10, cy - 14),
            (cx, cy - 15),
            (cx + 10, cy - 14),
            (cx + 18, cy - 13),
            (cx + 24, cy - 9),
            (cx + 26 - int(sway), cy - 2),
            (cx + 22, cy + 3),
        ])
        # Mane highlights (mid tone).
        _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["fur_mid"], [
            (cx - 18, cy - 2),
            (cx - 20, cy - 8),
            (cx - 12, cy - 12),
            (cx, cy - 13),
            (cx + 12, cy - 12),
            (cx + 20, cy - 8),
            (cx + 18, cy - 2),
        ])
        # Fur tufts (light strands).
        for i in range(-4, 5):
            tuft_x = cx + i * 4 + int(sway * 0.3)
            tuft_top_y = cy - 12 + int(math.sin(i * 0.5) * 2)
            tuft_bot_y = cy - 4
            pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["fur_mid"],
                             (tuft_x, tuft_top_y), (tuft_x, tuft_bot_y), 1)
            pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["fur_light"],
                             (tuft_x - 1, tuft_top_y + 1),
                             (tuft_x - 1, tuft_bot_y - 1), 1)
        # Sheen on top of mane.
        for x_off in (-12, -6, 0, 6, 12):
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["fur_shine"],
                             (cx + x_off, cy - 13, 2, 1))
    def _draw_bull_head(surface, cx, cy, facing, phase, action, progress):
        """Bull face with big horns."""
        # Head shape (broad snout).
        head_pts = [
            (cx - 12, cy),
            (cx - 14, cy - 6),
            (cx - 10, cy - 12),
            (cx - 4, cy - 14),
            (cx + 4, cy - 14),
            (cx + 10, cy - 12),
            (cx + 14, cy - 6),
            (cx + 12, cy),
            (cx + 10, cy + 6),
            (cx + 6, cy + 10),
            (cx - 6, cy + 10),
            (cx - 10, cy + 6),
        ]
        _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in head_pts])
        _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["skin_darkest"], head_pts)
        _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["skin_dark"], [
            (cx - 11, cy),
            (cx - 13, cy - 5),
            (cx - 9, cy - 11),
            (cx - 3, cy - 13),
            (cx + 3, cy - 13),
            (cx + 9, cy - 11),
            (cx + 13, cy - 5),
            (cx + 11, cy),
            (cx + 9, cy + 5),
            (cx + 5, cy + 9),
            (cx - 5, cy + 9),
            (cx - 9, cy + 5),
        ])
        _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["skin_mid"], [
            (cx - 8, cy - 2),
            (cx - 10, cy - 6),
            (cx - 6, cy - 10),
            (cx + 6, cy - 10),
            (cx + 10, cy - 6),
            (cx + 8, cy - 2),
            (cx + 6, cy + 4),
            (cx - 6, cy + 4),
        ])
        # Snout highlight.
        _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["skin_light"], [
            (cx - 5, cy + 2),
            (cx + 5, cy + 2),
            (cx + 4, cy + 8),
            (cx - 4, cy + 8),
        ])
        # HUGE HORNS.
        _NS_ghrakmaal._draw_bull_horns(surface, cx, cy, facing, phase)
        # Fur tuft on top of head.
        for x_off in (-6, -2, 2, 6):
            pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["fur_dark"],
                             (cx + x_off, cy - 14),
                             (cx + x_off - 1, cy - 18), 2)
            pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["fur_mid"],
                             (cx + x_off, cy - 14),
                             (cx + x_off - 1, cy - 18), 1)
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["fur_light"],
                             (cx + x_off - 1, cy - 18, 1, 1))
        # EYES (fiery orange).
        _NS_ghrakmaal._draw_bull_eyes(surface, cx, cy, phase, action)
        # NOSTRILS.
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["shadow_deep"],
                         (cx - 3, cy + 4, 2, 1))
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["shadow_deep"],
                         (cx + 2, cy + 4, 2, 1))
        # Bull ring on nose (iron).
        pygame.draw.arc(surface, _NS_ghrakmaal.PALETTE["iron_dark"],
                        (cx - 4, cy + 5, 8, 6), 0, math.pi, 2)
        pygame.draw.arc(surface, _NS_ghrakmaal.PALETTE["iron_light"],
                        (cx - 4, cy + 5, 8, 6), 0, math.pi, 1)
        # MOUTH with TUSKS.
        _NS_ghrakmaal._draw_bull_mouth(surface, cx, cy, phase, action, progress)
    def _draw_bull_horns(surface, cx, cy, facing, phase):
        """Massive curved bull horns."""
        for side in (-1, 1):
            # Horn base.
            base_x = cx + side * 10
            base_y = cy - 10
            # Curve outward and up.
            tip_x = cx + side * 20
            tip_y = cy - 20
            mid_x = cx + side * 16
            mid_y = cy - 12
            # Shadow.
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["shadow_deep"], [
                (base_x + 1, base_y + 2),
                (base_x + side * 3 + 1, base_y - 4 + 1),
                (tip_x + 1, tip_y + 1),
                (mid_x + 1, mid_y + 1),
            ])
            # Horn shape.
            horn_pts = [
                (base_x, base_y + 2),
                (base_x + side * 3, base_y - 4),
                (mid_x, mid_y - 2),
                (tip_x, tip_y),
                (mid_x + side, mid_y + 1),
                (base_x + side * 2, base_y + 1),
            ]
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["bone_dark"], horn_pts)
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["bone_mid"], [
                (base_x + side, base_y),
                (base_x + side * 3, base_y - 3),
                (mid_x, mid_y - 1),
                (tip_x, tip_y),
                (mid_x, mid_y),
            ])
            # Horn ridges (natural growth lines).
            for ridge_i in range(3):
                rx = base_x + side * (3 + ridge_i * 4)
                ry = base_y - 4 - ridge_i * 3
                pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["bone_dark"],
                                 (rx, ry), (rx + side, ry - 1), 1)
            # Highlight on top edge.
            pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["bone_light"],
                             (base_x + side * 2, base_y - 2),
                             (tip_x - side, tip_y + 1), 1)
            # Sharp glowing tip.
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["bone_shine"], (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["rune_light"], (tip_x, tip_y, 1, 1))
    def _draw_bull_eyes(surface, cx, cy, phase, action):
        """Fiery orange bull eyes."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        eye_intensity = 1.4 if action == "attack" else 1.0
        for side in (-1, 1):
            ex = cx + side * 4
            ey = cy - 6
            # Deep socket.
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["eye_socket"],
                             (ex - 2, ey - 1, 4, 3))
            # Glow halo.
            for r in range(6, 0, -1):
                alpha = _NS_ghrakmaal._alpha(110 * (6 - r) / 6 * pulse * eye_intensity)
                _NS_ghrakmaal._aacircle(surface,
                                        (*_NS_ghrakmaal.PALETTE["eye_mid"], alpha),
                                        (ex, ey), r)
            # Iris.
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["eye_dark"], (ex - 1, ey - 1, 3, 3))
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["eye_mid"], (ex, ey - 1, 2, 3))
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["eye_light"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["eye_glow"], (ex, ey, 1, 1))
    def _draw_bull_mouth(surface, cx, cy, phase, action, progress):
        """Mouth with big tusks."""
        # Mouth line.
        pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["shadow_deep"],
                         (cx - 4, cy + 8), (cx + 4, cy + 8), 1)
        pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["skin_darkest"],
                         (cx - 4, cy + 7), (cx + 4, cy + 7), 1)
        # Roar during attack (open mouth).
        if action == "attack" and 0.3 < progress < 0.7:
            roar = math.sin((progress - 0.3) / 0.4 * math.pi) * 3
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["shadow_deep"], [
                (cx - 4, cy + 7),
                (cx + 4, cy + 7),
                (cx + 3, cy + 7 + int(roar)),
                (cx - 3, cy + 7 + int(roar)),
            ])
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["rune_dark"], [
                (cx - 3, cy + 8),
                (cx + 3, cy + 8),
                (cx + 2, cy + 7 + int(roar) - 1),
                (cx - 2, cy + 7 + int(roar) - 1),
            ])
        # UPWARD TUSKS.
        for side in (-1, 1):
            tusk_x = cx + side * 3
            tusk_base_y = cy + 8
            tusk_tip_y = cy + 4
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["shadow_deep"], [
                (tusk_x - 1 + 1, tusk_base_y + 1),
                (tusk_x + side + 1, tusk_tip_y + 1),
                (tusk_x + 1 + 1, tusk_base_y + 1),
            ])
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["bone_dark"], [
                (tusk_x - 1, tusk_base_y),
                (tusk_x + side, tusk_tip_y),
                (tusk_x + 1, tusk_base_y),
            ])
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["bone_mid"], [
                (tusk_x, tusk_base_y),
                (tusk_x + side, tusk_tip_y),
                (tusk_x + 1, tusk_base_y),
            ])
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["bone_shine"],
                             (tusk_x + side, tusk_tip_y, 1, 1))
    def _draw_arms(surface, cx, cy, facing, phase, action, progress,
                    totem_x, totem_y, totem_state):
        """Two massive arms. Both grip totem when swinging (heavy weapon)."""
        is_swinging = (totem_state != "idle")
        # Shoulder positions.
        front_sh_x = cx + facing * 20
        front_sh_y = cy - 10
        back_sh_x = cx - facing * 20
        back_sh_y = cy - 10
        if is_swinging:
            # BOTH HANDS grip the totem (2-handed grip).
            # Grip points on totem (on the side closer to body).
            # Front hand: upper grip (near top of totem).
            front_hand_x = totem_x - facing * 3
            front_hand_y = totem_y - 6
            # Back hand: lower grip (near middle/bottom of totem).
            back_hand_x = totem_x - facing * 3
            back_hand_y = totem_y + 6
            # Compute elbows with natural bend.
            front_elbow = _NS_ghrakmaal._arm_elbow(
                (front_sh_x, front_sh_y), (front_hand_x, front_hand_y), bend=5)
            back_elbow = _NS_ghrakmaal._arm_elbow(
                (back_sh_x, back_sh_y), (back_hand_x, back_hand_y), bend=5)
        else:
            # Idle: arms hanging relaxed.
            front_elbow = (front_sh_x + facing * 2, front_sh_y + 12)
            front_hand_x = front_elbow[0] + facing * 1
            front_hand_y = front_elbow[1] + 12
            back_elbow = (back_sh_x - facing * 2, back_sh_y + 12)
            back_hand_x = back_elbow[0] - facing * 1
            back_hand_y = back_elbow[1] + 12
        # =========================
        # DRAW BACK ARM FIRST (behind body).
        # =========================
        _NS_ghrakmaal._draw_arm_segment(surface,
                                         (back_sh_x, back_sh_y),
                                         back_elbow,
                                         (back_hand_x, back_hand_y),
                                         is_gauntlet_big=is_swinging)
        # =========================
        # DRAW FRONT ARM (in front of body).
        # =========================
        _NS_ghrakmaal._draw_arm_segment(surface,
                                         (front_sh_x, front_sh_y),
                                         front_elbow,
                                         (front_hand_x, front_hand_y),
                                         is_gauntlet_big=True)
    def _draw_arm_segment(surface, shoulder, elbow, hand, is_gauntlet_big=True):
        """Draw a single arm: shoulder → elbow → hand with gauntlet."""
        sx, sy = shoulder
        ex, ey = elbow
        hx, hy = hand
        # Upper arm.
        pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["shadow_deep"],
                         (sx + 1, sy + 1), (ex + 1, ey + 1), 8)
        pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["skin_darkest"],
                         (sx, sy), (ex, ey), 7)
        pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["skin_dark"],
                         (sx, sy), (ex, ey), 5)
        pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["skin_mid"],
                         (sx, sy - 1), (ex, ey - 1), 2)
        # Forearm.
        pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["shadow_deep"],
                         (ex + 1, ey + 1), (hx + 1, hy + 1), 7)
        pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["skin_darkest"],
                         (ex, ey), (hx, hy), 6)
        pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["skin_dark"],
                         (ex, ey), (hx, hy), 4)
        pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["skin_mid"],
                         (ex, ey - 1), (hx, hy - 1), 1)
        # Iron gauntlet.
        g = 4 if is_gauntlet_big else 3
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_darkest"],
                         (hx - g, hy - g, g * 2, g * 2))
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_dark"],
                         (hx - g + 1, hy - g + 1, g * 2 - 2, g * 2 - 2))
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_mid"],
                         (hx - g + 2, hy - g + 1, g * 2 - 4, 2))
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_light"],
                         (hx - g + 2, hy - g + 2, g * 2 - 4, 1))
        # Knuckle spikes.
        for kx in range(-g + 1, g, 2):
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_light"],
                             (hx + kx, hy + g - 2, 1, 1))
    # ============================================================
    # TOTEM (signature weapon)
    # ============================================================
    def _draw_totem(surface, tx, ty, facing, phase, rotated=False,
                     swing_progress=0):
        """Massive stone/wood totem cylinder with iron bands + runes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        if rotated:
            # Horizontal orientation (on back).
            # Cylinder rotated 90 degrees.
            w = 32  # length of cylinder
            h = 16  # diameter
            # Body.
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["shadow_deep"], [
                (tx - w // 2 + 2, ty - h // 2 + 2),
                (tx + w // 2 + 2, ty - h // 2 + 2),
                (tx + w // 2 + 2, ty + h // 2 + 2),
                (tx - w // 2 + 2, ty + h // 2 + 2),
            ])
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["wood_darkest"],
                             (tx - w // 2, ty - h // 2, w, h))
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["wood_dark"],
                             (tx - w // 2 + 1, ty - h // 2 + 1, w - 2, h - 2))
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["wood_mid"],
                             (tx - w // 2 + 2, ty - h // 2 + 3, w - 4, h - 6))
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["wood_light"],
                             (tx - w // 2 + 3, ty - h // 2 + 4, w - 6, 2))
            # End caps (iron circles).
            for cap_x in (tx - w // 2, tx + w // 2 - 1):
                _NS_ghrakmaal._aacircle(surface, _NS_ghrakmaal.PALETTE["iron_darkest"],
                                        (cap_x, ty), h // 2 + 1)
                _NS_ghrakmaal._aacircle(surface, _NS_ghrakmaal.PALETTE["iron_dark"],
                                        (cap_x, ty), h // 2)
                _NS_ghrakmaal._aacircle(surface, _NS_ghrakmaal.PALETTE["iron_mid"],
                                        (cap_x, ty), h // 2 - 2)
                _NS_ghrakmaal._aacircle(surface, _NS_ghrakmaal.PALETTE["iron_light"],
                                        (cap_x, ty), h // 2 - 4)
            # Iron bands across cylinder.
            for band_x in (tx - w // 4, tx, tx + w // 4):
                pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_darkest"],
                                 (band_x - 2, ty - h // 2, 4, h))
                pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_dark"],
                                 (band_x - 1, ty - h // 2 + 1, 3, h - 2))
                pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_mid"],
                                 (band_x, ty - h // 2 + 2, 1, h - 4))
            # Rune glow (subtle when idle).
            rune_alpha = _NS_ghrakmaal._alpha(120 * pulse)
            for rune_x in (tx - 8, tx + 8):
                _NS_ghrakmaal._aacircle(surface, (*_NS_ghrakmaal.PALETTE["rune_mid"], rune_alpha),
                                        (rune_x, ty), 2)
                pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["rune_light"], (rune_x, ty, 1, 1))
        else:
            # Vertical orientation (swinging in hand).
            w = 18
            h = 32
            # Charge intensity increases as attack progresses.
            charge_intensity = 0
            if 0.3 < swing_progress < 0.7:
                charge_intensity = math.sin((swing_progress - 0.3) / 0.4 * math.pi)
            # Aura around totem during swing.
            if charge_intensity > 0:
                for r in range(20, 5, -3):
                    alpha = _NS_ghrakmaal._alpha(60 * (20 - r) / 20 * charge_intensity)
                    _NS_ghrakmaal._aacircle(surface,
                                            (*_NS_ghrakmaal.PALETTE["rune_light"], alpha),
                                            (tx, ty), r)
            # Body.
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["shadow_deep"], [
                (tx - w // 2 + 2, ty - h // 2 + 2),
                (tx + w // 2 + 2, ty - h // 2 + 2),
                (tx + w // 2 + 2, ty + h // 2 + 2),
                (tx - w // 2 + 2, ty + h // 2 + 2),
            ])
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["wood_darkest"],
                             (tx - w // 2, ty - h // 2, w, h))
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["wood_dark"],
                             (tx - w // 2 + 1, ty - h // 2 + 1, w - 2, h - 2))
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["wood_mid"],
                             (tx - w // 2 + 3, ty - h // 2 + 2, w - 6, h - 4))
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["wood_light"],
                             (tx - w // 2 + 4, ty - h // 2 + 3, 2, h - 6))
            # End caps (top and bottom).
            for cap_y in (ty - h // 2, ty + h // 2 - 1):
                _NS_ghrakmaal._aacircle(surface, _NS_ghrakmaal.PALETTE["iron_darkest"],
                                        (tx, cap_y), w // 2 + 1)
                _NS_ghrakmaal._aacircle(surface, _NS_ghrakmaal.PALETTE["iron_dark"],
                                        (tx, cap_y), w // 2)
                _NS_ghrakmaal._aacircle(surface, _NS_ghrakmaal.PALETTE["iron_mid"],
                                        (tx, cap_y), w // 2 - 2)
                _NS_ghrakmaal._aacircle(surface, _NS_ghrakmaal.PALETTE["iron_light"],
                                        (tx, cap_y), w // 2 - 4)
                pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_shine"],
                                 (tx - 1, cap_y - 1, 2, 1))
            # Iron bands (horizontal across totem).
            for band_y in (ty - h // 4, ty, ty + h // 4):
                pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_darkest"],
                                 (tx - w // 2, band_y - 2, w, 4))
                pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_dark"],
                                 (tx - w // 2 + 1, band_y - 1, w - 2, 3))
                pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_mid"],
                                 (tx - w // 2 + 2, band_y, w - 4, 1))
                # Rivets.
                for rivet_x in (tx - w // 2 + 2, tx + w // 2 - 3):
                    pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_light"],
                                     (rivet_x, band_y, 1, 1))
            # RUNES (fiery orange) on totem body.
            rune_intensity = 0.8 + charge_intensity * 0.5
            for rune_y_off in (-h // 4 - 4, 0, h // 4 - 4):
                rune_y = ty + rune_y_off
                rune_alpha = _NS_ghrakmaal._alpha(180 * pulse * rune_intensity)
                # Glow behind rune.
                for r in range(5, 0, -1):
                    alpha = _NS_ghrakmaal._alpha(60 * (5 - r) / 5 * pulse * rune_intensity)
                    _NS_ghrakmaal._aacircle(surface,
                                            (*_NS_ghrakmaal.PALETTE["rune_light"], alpha),
                                            (tx, rune_y), r)
                # Rune shape (X or asterisk).
                pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["rune_dark"],
                                 (tx - 3, rune_y), (tx + 3, rune_y), 1)
                pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["rune_mid"],
                                 (tx - 2, rune_y), (tx + 2, rune_y), 1)
                pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["rune_dark"],
                                 (tx, rune_y - 3), (tx, rune_y + 3), 1)
                pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["rune_mid"],
                                 (tx, rune_y - 2), (tx, rune_y + 2), 1)
                pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["rune_light"],
                                 (tx, rune_y, 1, 1))
                pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["rune_shine"],
                                 (tx, rune_y, 1, 1))
            # Spikes on top cap (fierce look).
            for spike_i in range(3):
                spike_x = tx + (spike_i - 1) * 4
                spike_top_y = ty - h // 2 - 4
                _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["iron_darkest"], [
                    (spike_x - 1, ty - h // 2 - 1),
                    (spike_x, spike_top_y),
                    (spike_x + 1, ty - h // 2 - 1),
                ])
                _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["iron_mid"], [
                    (spike_x, ty - h // 2 - 1),
                    (spike_x, spike_top_y),
                    (spike_x + 1, ty - h // 2 - 1),
                ])
                pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["iron_shine"],
                                 (spike_x, spike_top_y, 1, 1))
    # ============================================================
    # SHOCKWAVE (basic attack impact)
    # ============================================================
    def _draw_slam_shockwave(surface, boss, cx, cy, t):
        """Radial shockwave when totem slams ground - origin at totem impact point."""
        facing = boss.direction
        # Impact point sama dengan trajectory totem.
        origin_x = cx + facing * 26
        origin_y = cy + 42
        radius = int(15 + t * 45)
        alpha = _NS_ghrakmaal._alpha(240 * (1 - t))
        # Multiple concentric rings.
        for i in range(3):
            r = max(1, radius - i * 6)
            a = _NS_ghrakmaal._alpha(alpha * (3 - i) / 3)
            pygame.draw.ellipse(surface,
                                (*_NS_ghrakmaal.PALETTE["molten_dark"], a),
                                (origin_x - r, origin_y - r // 3, r * 2, r * 2 // 3), 2)
            pygame.draw.ellipse(surface,
                                (*_NS_ghrakmaal.PALETTE["molten_mid"], a),
                                (origin_x - r + 2, origin_y - r // 3 + 1,
                                 r * 2 - 4, r * 2 // 3 - 2), 1)
        # Rising debris + sparks.
        for i in range(14):
            angle = i * math.pi * 2 / 14
            rd = int(radius * 0.7)
            rx = origin_x + int(math.cos(angle) * rd)
            ry = origin_y + int(math.sin(angle) * rd * 0.5) - int(t * 10)
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["rock_dark"], [
                (rx - 2, ry), (rx, ry - 2), (rx + 2, ry), (rx, ry + 1),
            ])
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["rock_mid"], [
                (rx - 1, ry), (rx, ry - 1), (rx + 1, ry),
            ])
            pygame.draw.rect(surface, (*_NS_ghrakmaal.PALETTE["molten_hot"], alpha),
                             (rx, ry - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_ghrakmaal.PALETTE["molten_shine"], alpha),
                             (rx, ry - 1, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        """Big shadow beneath colossus."""
        breath = math.sin(phase * 0.5) * 0.15 + 0.85
        shadow = pygame.Surface((170, 40), pygame.SRCALPHA)
        for radius in range(16, 0, -1):
            alpha = max(0, int((16 - radius) * 14 * breath))
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (16 - radius, 20 - radius,
                                 138 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (10, 5, 3, int(180 * breath)),
                            (12, 12, 146, 14))
        surface.blit(shadow, (x - 85, y - 20))
    def _draw_earth_dust(surface, cx, cy, phase, intense=False):
        """Dust particles floating up from ground (earth energy)."""
        strength = 1.5 if intense else 1.0
        for i in range(10):
            t = (phase * 0.3 + i * 0.11) % 1.0
            dx = cx + int(math.sin(phase + i * 0.7) * 30) - 15 + i * 3
            dy = cy - int(t * 20)
            alpha = _NS_ghrakmaal._alpha(200 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_ghrakmaal.PALETTE["rock_mid"], alpha),
                                 (dx, dy, 2, 2))
                pygame.draw.rect(surface, (*_NS_ghrakmaal.PALETTE["rock_light"], alpha),
                                 (dx, dy - 1, 1, 1))
        # Molten embers rising.
        for i in range(6):
            t = (phase * 0.5 + i * 0.17) % 1.0
            ex = cx + int(math.sin(phase * 1.2 + i) * 22) - 10 + i * 4
            ey = cy - int(t * 18)
            alpha = _NS_ghrakmaal._alpha(220 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_ghrakmaal.PALETTE["molten_mid"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_ghrakmaal.PALETTE["molten_hot"], alpha),
                                 (ex, ey, 1, 1))
                pygame.draw.rect(surface, (*_NS_ghrakmaal.PALETTE["molten_shine"], alpha),
                                 (ex, ey - 1, 1, 1))
    def _draw_earth_aura(surface, x, y, phase):
        """Massive orange-brown aura (TRUE BOSS scale)."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_ghrakmaal._alpha((100 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_ghrakmaal._aacircle(aura,
                                        (*_NS_ghrakmaal.PALETTE["molten_darkest"], alpha),
                                        (120, 100), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_ghrakmaal._alpha((65 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_ghrakmaal._aacircle(aura,
                                        (*_NS_ghrakmaal.PALETTE["molten_dark"], alpha),
                                        (120, 100), radius)
        surface.blit(aura, (x - 120, y - 100))
        # Floating molten embers around body.
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 45 + int(math.sin(phase + i) * 15)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.45)
            color = _NS_ghrakmaal.PALETTE["molten_mid"] if i % 2 == 0 else _NS_ghrakmaal.PALETTE["molten_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["molten_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Fiery runic ground ring (TRUE BOSS scale)."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((190, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_ghrakmaal.PALETTE["molten_darkest"], 200),
                            (5, 20, 180, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_ghrakmaal.PALETTE["molten_dark"], 220),
                            (14, 22, 162, 26), 2)
        pygame.draw.ellipse(ring, (*_NS_ghrakmaal.PALETTE["molten_mid"], 200),
                            (25, 24, 140, 22), 1)
        pygame.draw.ellipse(ring, (*_NS_ghrakmaal.PALETTE["rune_dark"], 180),
                            (40, 26, 110, 18), 1)
        # Rune spikes.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 95 + int(math.cos(angle) * 50)
            y1 = 33 + int(math.sin(angle) * 9)
            x2 = 95 + int(math.cos(angle) * 78)
            y2 = 33 + int(math.sin(angle) * 14)
            pygame.draw.line(ring, (*_NS_ghrakmaal.PALETTE["rune_light"], 220),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.rect(ring, _NS_ghrakmaal.PALETTE["molten_hot"], (x2, y2, 1, 1))
        if skill:
            pygame.draw.ellipse(ring, (*_NS_ghrakmaal.PALETTE["molten_hot"],
                                       _NS_ghrakmaal._alpha(160 * pulse)),
                                (15, 14, 160, 42), 1)
        surface.blit(ring, (x - 95, y - 30))
    # ============================================================
    # SKILL Q: FISSURE (line of jagged rocks erupting)
    # ============================================================
    def _draw_fissure_ground(surface, boss, x, y, timer, phase):
        """Ground crack line from boss to target."""
        tx, ty = _NS_ghrakmaal._target_position(boss, x, y)
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        start_x = x + facing * 30
        start_y = y + 40
        if progress < 0.25:
            # Warning: crack forming.
            t = progress / 0.25
            end_x = int(start_x + (tx - start_x) * t)
            end_y = int(start_y + (ty - start_y) * t * 0.3)  # keep on ground
            pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["rune_dark"],
                             (start_x, start_y), (end_x, end_y), 3)
            pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["molten_mid"],
                             (start_x, start_y), (end_x, end_y), 1)
    def _draw_fissure_foreground(surface, boss, x, y, timer, phase):
        """Jagged rock spikes erupting along fissure line."""
        tx, ty = _NS_ghrakmaal._target_position(boss, x, y)
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        start_x = x + facing * 30
        start_y = y + 40  # ground level
        if progress < 0.25:
            return  # only crack visible
        # Fissure line active.
        t = (progress - 0.25) / 0.75
        num_spikes = 8
        for i in range(num_spikes):
            spike_t = i / (num_spikes - 1)
            # Position along line from boss to target.
            spike_x = int(start_x + (tx - start_x) * spike_t)
            spike_y = int(start_y + (ty - start_y) * spike_t * 0.3)  # keep low
            # Each spike has staggered emerge time.
            emerge_t = min(1.0, max(0.0, t * 2 - spike_t * 0.8))
            if emerge_t <= 0:
                continue
            spike_h = int(28 * emerge_t)
            spike_w = 5
            # Jagged rock spike.
            pts = [
                (spike_x, spike_y - spike_h),
                (spike_x - spike_w, spike_y - spike_h // 2),
                (spike_x - spike_w // 2, spike_y),
                (spike_x + spike_w // 2, spike_y),
                (spike_x + spike_w, spike_y - spike_h // 2),
            ]
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 2) for p in pts])
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["rock_darkest"], pts)
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["rock_dark"], [
                (spike_x, spike_y - spike_h + 1),
                (spike_x - spike_w + 1, spike_y - spike_h // 2),
                (spike_x, spike_y - 1),
                (spike_x + spike_w - 1, spike_y - spike_h // 2),
            ])
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["rock_mid"], [
                (spike_x, spike_y - spike_h + 2),
                (spike_x - spike_w // 2, spike_y - spike_h // 2),
                (spike_x, spike_y - 2),
            ])
            # Molten crack down center.
            pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["molten_dark"],
                             (spike_x, spike_y - spike_h + 2),
                             (spike_x, spike_y - 2), 1)
            pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["molten_hot"],
                             (spike_x, spike_y - spike_h + 3),
                             (spike_x, spike_y - 3), 1)
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["molten_shine"],
                             (spike_x, spike_y - spike_h + 1, 1, 1))
        # Ground crack line (glowing).
        for i in range(20):
            crack_t = i / 19
            cx_p = int(start_x + (tx - start_x) * crack_t)
            cy_p = int(start_y + (ty - start_y) * crack_t * 0.3)
            alpha = _NS_ghrakmaal._alpha(230 * (1 - t * 0.3))
            offset_x = int(math.sin(crack_t * 8) * 2)
            pygame.draw.rect(surface, (*_NS_ghrakmaal.PALETTE["molten_dark"], alpha),
                             (cx_p + offset_x - 1, cy_p, 3, 2))
            pygame.draw.rect(surface, (*_NS_ghrakmaal.PALETTE["molten_hot"], alpha),
                             (cx_p + offset_x, cy_p, 1, 1))
            pygame.draw.rect(surface, (*_NS_ghrakmaal.PALETTE["molten_shine"], alpha),
                             (cx_p + offset_x, cy_p, 1, 1))
    # ============================================================
    # SKILL W: AFTERSHOCK (AoE stun around boss)
    # ============================================================
    def _draw_aftershock_ground(surface, boss, x, y, timer, phase):
        """Ground shockwave rings around boss."""
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        origin_x = x
        origin_y = y + 42
        # Growing rings.
        for ring_i in range(3):
            ring_delay = ring_i * 0.15
            ring_t = max(0.0, progress - ring_delay)
            if ring_t <= 0 or ring_t > 0.7:
                continue
            local_t = ring_t / 0.7
            r = int(20 + local_t * 55)
            alpha = _NS_ghrakmaal._alpha(220 * (1 - local_t))
            pygame.draw.ellipse(surface, (*_NS_ghrakmaal.PALETTE["molten_dark"], alpha),
                                (origin_x - r, origin_y - r // 3,
                                 r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_ghrakmaal.PALETTE["molten_mid"], alpha),
                                (origin_x - r + 2, origin_y - r // 3 + 1,
                                 r * 2 - 4, r * 2 // 3 - 2), 2)
            pygame.draw.ellipse(surface, (*_NS_ghrakmaal.PALETTE["molten_hot"], alpha),
                                (origin_x - r + 4, origin_y - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4), 1)
    def _draw_aftershock_foreground(surface, boss, x, y, timer, phase):
        """Rock chunks + sparks flying up around boss."""
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        origin_x = x
        origin_y = y + 42
        # Rock debris flying outward.
        for i in range(16):
            angle = i * math.pi * 2 / 16
            travel_t = (progress * 1.5 + i * 0.05) % 1.0
            dist = int(travel_t * 60)
            rock_x = origin_x + int(math.cos(angle) * dist)
            # Arc trajectory.
            rock_y = origin_y + int(math.sin(angle) * dist * 0.4) - int(math.sin(travel_t * math.pi) * 20)
            alpha = _NS_ghrakmaal._alpha(230 * (1 - travel_t))
            if alpha > 0:
                # Rock chunk.
                _NS_ghrakmaal._poly(surface,
                                    (*_NS_ghrakmaal.PALETTE["rock_dark"], alpha), [
                                        (rock_x - 2, rock_y),
                                        (rock_x, rock_y - 2),
                                        (rock_x + 2, rock_y),
                                        (rock_x + 1, rock_y + 2),
                                        (rock_x - 1, rock_y + 2),
                                    ])
                _NS_ghrakmaal._poly(surface,
                                    (*_NS_ghrakmaal.PALETTE["rock_mid"], alpha), [
                                        (rock_x - 1, rock_y),
                                        (rock_x, rock_y - 1),
                                        (rock_x + 1, rock_y),
                                    ])
                pygame.draw.rect(surface, (*_NS_ghrakmaal.PALETTE["rock_light"], alpha),
                                 (rock_x, rock_y, 1, 1))
        # Molten sparks.
        for i in range(20):
            angle = i * math.pi * 2 / 20 + phase * 0.5
            spark_t = (phase * 0.8 + i * 0.05) % 1.0
            dist = int(spark_t * 50)
            sx = origin_x + int(math.cos(angle) * dist)
            sy = origin_y + int(math.sin(angle) * dist * 0.4) - int(spark_t * 15)
            alpha = _NS_ghrakmaal._alpha(240 * (1 - spark_t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_ghrakmaal.PALETTE["molten_hot"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_ghrakmaal.PALETTE["molten_shine"], alpha),
                                 (sx, sy, 1, 1))
    # ============================================================
    # SKILL E: ECHO SLAM (targeted crater with radial burst)
    # ============================================================
    def _draw_echoslam_ground(surface, boss, x, y, timer, phase):
        """Crater at target with molten pool."""
        tx, ty = _NS_ghrakmaal._target_position(boss, x, y)
        duration = 75
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.25:
            # Warning: growing rune circle.
            t = progress / 0.25
            r = int(25 * t)
            alpha = _NS_ghrakmaal._alpha(200 * t)
            pygame.draw.ellipse(surface, (*_NS_ghrakmaal.PALETTE["rune_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["molten_hot"], (sx, sy, 2, 2))
        else:
            # Crater with pulsing molten pool.
            t = (progress - 0.25) / 0.75
            r = int(30 + t * 15)
            pulse_alpha = int(math.sin(phase * 3) * 40 + 200)
            alpha = _NS_ghrakmaal._alpha(pulse_alpha * (1 - t * 0.4))
            pygame.draw.ellipse(surface, (*_NS_ghrakmaal.PALETTE["molten_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_ghrakmaal.PALETTE["molten_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_ghrakmaal.PALETTE["molten_mid"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
            pygame.draw.ellipse(surface, (*_NS_ghrakmaal.PALETTE["molten_hot"], alpha),
                                (tx - r + 14, ty - r // 3 + 6,
                                 r * 2 - 28, r * 2 // 3 - 12))
            # Molten pool center.
            _NS_ghrakmaal._aacircle(surface, _NS_ghrakmaal.PALETTE["molten_shine"], (tx, ty), 3)
    def _draw_echoslam_foreground(surface, boss, x, y, timer, phase):
        """Radial rock spikes + upward burst."""
        tx, ty = _NS_ghrakmaal._target_position(boss, x, y)
        duration = 75
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.25:
            return
        t = (progress - 0.25) / 0.75
        # Radial rock spikes forming crater rim.
        for i in range(10):
            angle = i * math.pi * 2 / 10
            spike_r = 32
            spike_x = tx + int(math.cos(angle) * spike_r)
            spike_y = ty + int(math.sin(angle) * spike_r * 0.5)
            emerge_t = min(1.0, t * 2)
            spike_h = int(20 * emerge_t)
            pts = [
                (spike_x, spike_y - spike_h),
                (spike_x - 3, spike_y - spike_h // 2),
                (spike_x - 2, spike_y),
                (spike_x + 2, spike_y),
                (spike_x + 3, spike_y - spike_h // 2),
            ]
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 2) for p in pts])
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["rock_darkest"], pts)
            _NS_ghrakmaal._poly(surface, _NS_ghrakmaal.PALETTE["rock_dark"], [
                (spike_x, spike_y - spike_h + 1),
                (spike_x - 2, spike_y - spike_h // 2),
                (spike_x, spike_y - 1),
                (spike_x + 2, spike_y - spike_h // 2),
            ])
            # Molten crack.
            pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["molten_hot"],
                             (spike_x, spike_y - spike_h + 2),
                             (spike_x, spike_y - 2), 1)
        # UPWARD MASSIVE BURST from center (like geyser).
        if progress < 0.5:
            burst_t = (progress - 0.25) / 0.25
            burst_h = int(burst_t * 80)
            burst_alpha = _NS_ghrakmaal._alpha(240 * (1 - burst_t))
            for layer_i, (width, color) in enumerate([
                (14, _NS_ghrakmaal.PALETTE["molten_darkest"]),
                (10, _NS_ghrakmaal.PALETTE["molten_dark"]),
                (7, _NS_ghrakmaal.PALETTE["molten_mid"]),
                (4, _NS_ghrakmaal.PALETTE["molten_hot"]),
                (2, _NS_ghrakmaal.PALETTE["molten_shine"]),
            ]):
                alpha = _NS_ghrakmaal._alpha(burst_alpha)
                pygame.draw.line(surface, (*color, alpha),
                                 (tx, ty), (tx, ty - burst_h), width)
            # Sparks flying up.
            for i in range(15):
                spark_t = (phase * 2 + i * 0.1) % 1.0
                sy_off = int(spark_t * burst_h)
                sx_off = int(math.sin(phase * 3 + i) * 6)
                sx = tx + sx_off
                sy = ty - sy_off
                alpha = _NS_ghrakmaal._alpha(240 * burst_t * (1 - spark_t))
                if alpha > 0:
                    pygame.draw.rect(surface, (*_NS_ghrakmaal.PALETTE["molten_hot"], alpha),
                                     (sx, sy, 2, 2))
                    pygame.draw.rect(surface, (*_NS_ghrakmaal.PALETTE["molten_shine"], alpha),
                                     (sx, sy, 1, 1))
    # ============================================================
    # SKILL R: ENCHANT TOTEM (throw totem at target)
    # ============================================================
    def _draw_enchanttotem_ground(surface, boss, x, y, timer, phase):
        """Ground rune where totem will land."""
        tx, ty = _NS_ghrakmaal._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            # Warning: forming rune.
            t = progress / 0.4
            r = int(28 * t)
            alpha = _NS_ghrakmaal._alpha(200 * t)
            pygame.draw.ellipse(surface, (*_NS_ghrakmaal.PALETTE["rune_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_ghrakmaal.PALETTE["molten_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["molten_hot"], (sx, sy, 2, 2))
        else:
            # After landing: MASSIVE crater with lingering rock spikes.
            t = (progress - 0.4) / 0.6
            r = int(42 - t * 5)
            alpha = _NS_ghrakmaal._alpha(220 * (1 - t * 0.5))
            pygame.draw.ellipse(surface, (*_NS_ghrakmaal.PALETTE["molten_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_ghrakmaal.PALETTE["molten_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_ghrakmaal.PALETTE["molten_mid"], alpha),
                                (tx - r + 10, ty - r // 3 + 5,
                                 r * 2 - 20, r * 2 // 3 - 10))
            pygame.draw.ellipse(surface, (*_NS_ghrakmaal.PALETTE["molten_hot"], alpha),
                                (tx - r + 18, ty - r // 3 + 8,
                                 r * 2 - 36, r * 2 // 3 - 16))
    def _draw_enchanttotem_projectile(surface, boss, x, y, timer, phase):
        """Totem flying toward target with fiery aura."""
        tx, ty = _NS_ghrakmaal._target_position(boss, x, y)
        facing = boss.direction
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Origin: near boss hand.
        start_x = x + facing * 32
        start_y = y - 5
        if progress < 0.3:
            # Charge up: totem glowing intensely in hand (drawn by body).
            # Just add extra charge aura here.
            t = progress / 0.3
            for r in range(int(20 + t * 15), 0, -3):
                alpha = _NS_ghrakmaal._alpha(80 * (35 - r) / 35 * t)
                _NS_ghrakmaal._aacircle(surface,
                                        (*_NS_ghrakmaal.PALETTE["rune_light"], alpha),
                                        (start_x - facing * 8, start_y - 15), r)
            # Energy converging.
            for i in range(10):
                angle = phase * 3 + i * math.pi / 5
                spark_dist = int(25 * (1 - t))
                sx = start_x - facing * 8 + int(math.cos(angle) * spark_dist)
                sy = start_y - 15 + int(math.sin(angle) * spark_dist)
                pygame.draw.line(surface, _NS_ghrakmaal.PALETTE["molten_hot"],
                                 (sx, sy), (start_x - facing * 8, start_y - 15), 1)
                pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["molten_shine"], (sx, sy, 1, 1))
        elif progress < 0.7:
            # THROW: totem in flight (arc trajectory).
            t = (progress - 0.3) / 0.4
            # Arc trajectory.
            arc = math.sin(t * math.pi) * 40
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t - arc)
            rot = t * math.pi * 3  # spinning
            # Fiery trail (comet).
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t -
                         math.sin(trail_t * math.pi) * 40)
                alpha = _NS_ghrakmaal._alpha(230 - i * 22)
                size = max(2, 10 - i)
                _NS_ghrakmaal._aacircle(surface,
                                        (*_NS_ghrakmaal.PALETTE["molten_darkest"], alpha),
                                        (px, py), size)
                _NS_ghrakmaal._aacircle(surface,
                                        (*_NS_ghrakmaal.PALETTE["molten_dark"], alpha),
                                        (px, py), max(1, size - 2))
                _NS_ghrakmaal._aacircle(surface,
                                        (*_NS_ghrakmaal.PALETTE["molten_mid"], alpha),
                                        (px, py), max(1, size - 4))
                _NS_ghrakmaal._aacircle(surface,
                                        (*_NS_ghrakmaal.PALETTE["molten_hot"], alpha),
                                        (px, py), max(1, size - 6))
            # Big glow around totem.
            for r in range(24, 6, -3):
                alpha = _NS_ghrakmaal._alpha(80 * (24 - r) / 24)
                _NS_ghrakmaal._aacircle(surface,
                                        (*_NS_ghrakmaal.PALETTE["molten_light"], alpha),
                                        (bx, by), r)
            # Draw spinning totem projectile.
            _NS_ghrakmaal._draw_flying_totem(surface, bx, by, rot, facing)
        elif progress < 0.85:
            # IMPACT: massive explosion at target.
            t = (progress - 0.7) / 0.15
            intensity = math.sin(t * math.pi)
            impact_r = int(20 + t * 45)
            impact_alpha = _NS_ghrakmaal._alpha(255 * intensity)
            # Multiple explosion rings.
            _NS_ghrakmaal._aacircle(surface, (*_NS_ghrakmaal.PALETTE["molten_darkest"], impact_alpha),
                                    (tx, ty), impact_r + 5, 4)
            _NS_ghrakmaal._aacircle(surface, (*_NS_ghrakmaal.PALETTE["molten_dark"], impact_alpha),
                                    (tx, ty), impact_r, 3)
            _NS_ghrakmaal._aacircle(surface, (*_NS_ghrakmaal.PALETTE["molten_mid"], impact_alpha),
                                    (tx, ty), max(1, impact_r - 8), 3)
            _NS_ghrakmaal._aacircle(surface, (*_NS_ghrakmaal.PALETTE["molten_light"], impact_alpha),
                                    (tx, ty), max(1, impact_r - 16), 2)
            _NS_ghrakmaal._aacircle(surface, (*_NS_ghrakmaal.PALETTE["molten_hot"], impact_alpha),
                                    (tx, ty), max(1, impact_r - 24))
            _NS_ghrakmaal._aacircle(surface, (*_NS_ghrakmaal.PALETTE["molten_shine"], impact_alpha),
                                    (tx, ty), max(1, impact_r // 4))
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["white"],
                             (tx - 1, ty - 1, 2, 2))
            # Radial rock spikes exploding outward.
            for i in range(16):
                angle = i * math.pi / 8
                spike_dist = impact_r
                spike_x = tx + int(math.cos(angle) * spike_dist)
                spike_y = ty + int(math.sin(angle) * spike_dist * 0.7)
                spike_len = int(15 * (1 - t))
                # Rock chunk flying outward.
                end_x = spike_x + int(math.cos(angle) * spike_len)
                end_y = spike_y + int(math.sin(angle) * spike_len * 0.7)
                pygame.draw.line(surface, (*_NS_ghrakmaal.PALETTE["rock_dark"], impact_alpha),
                                 (spike_x, spike_y), (end_x, end_y), 3)
                pygame.draw.line(surface, (*_NS_ghrakmaal.PALETTE["molten_hot"], impact_alpha),
                                 (spike_x, spike_y), (end_x, end_y), 1)
                _NS_ghrakmaal._poly(surface, (*_NS_ghrakmaal.PALETTE["rock_mid"], impact_alpha), [
                    (end_x - 2, end_y),
                    (end_x, end_y - 2),
                    (end_x + 2, end_y),
                    (end_x, end_y + 1),
                ])
            # The totem itself lying at impact site (broken).
            _NS_ghrakmaal._draw_broken_totem(surface, tx, ty, phase)
        else:
            # Aftermath: molten pool + rising embers + totem remnant.
            t = (progress - 0.85) / 0.15
            _NS_ghrakmaal._draw_broken_totem(surface, tx, ty, phase)
            for i in range(15):
                rise_t = (phase * 0.7 + i * 0.08) % 1.0
                rx = tx + int(math.sin(phase + i) * 25)
                ry = ty - int(rise_t * 35)
                alpha = _NS_ghrakmaal._alpha(220 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    pygame.draw.rect(surface, (*_NS_ghrakmaal.PALETTE["molten_mid"], alpha),
                                     (rx, ry, 2, 2))
                    pygame.draw.rect(surface, (*_NS_ghrakmaal.PALETTE["molten_hot"], alpha),
                                     (rx, ry, 1, 1))
                    pygame.draw.rect(surface, (*_NS_ghrakmaal.PALETTE["molten_shine"], alpha),
                                     (rx, ry - 1, 1, 1))
    def _draw_flying_totem(surface, cx, cy, rot, facing):
        """Spinning totem projectile (simplified vertical totem)."""
        # We approximate rotation by drawing an oval with rune glow.
        w = 20
        h = 32
        # Rough rotation: swap w/h based on rotation angle.
        rot_norm = (rot % math.pi) / math.pi
        aspect = abs(math.cos(rot_norm * math.pi))
        cur_w = int(w * (0.4 + 0.6 * aspect))
        cur_h = int(h * (0.4 + 0.6 * (1 - aspect)))
        if cur_w < cur_h:
            actual_w = cur_w
            actual_h = cur_h
        else:
            actual_w = cur_h
            actual_h = cur_w
        # Shadow.
        pygame.draw.ellipse(surface, _NS_ghrakmaal.PALETTE["shadow_deep"],
                            (cx - actual_w // 2 + 2, cy - actual_h // 2 + 2,
                             actual_w, actual_h))
        # Totem body.
        pygame.draw.ellipse(surface, _NS_ghrakmaal.PALETTE["wood_darkest"],
                            (cx - actual_w // 2, cy - actual_h // 2, actual_w, actual_h))
        pygame.draw.ellipse(surface, _NS_ghrakmaal.PALETTE["wood_dark"],
                            (cx - actual_w // 2 + 1, cy - actual_h // 2 + 1,
                             actual_w - 2, actual_h - 2))
        pygame.draw.ellipse(surface, _NS_ghrakmaal.PALETTE["wood_mid"],
                            (cx - actual_w // 2 + 3, cy - actual_h // 2 + 3,
                             actual_w - 6, actual_h - 6))
        # Iron end caps.
        for cap_off in (-actual_h // 2 + 3, actual_h // 2 - 3):
            _NS_ghrakmaal._aacircle(surface, _NS_ghrakmaal.PALETTE["iron_dark"],
                                    (cx, cy + cap_off), actual_w // 2 - 1)
            _NS_ghrakmaal._aacircle(surface, _NS_ghrakmaal.PALETTE["iron_mid"],
                                    (cx, cy + cap_off), actual_w // 2 - 3)
        # Iron band in middle.
        pygame.draw.ellipse(surface, _NS_ghrakmaal.PALETTE["iron_darkest"],
                            (cx - actual_w // 2, cy - 2, actual_w, 4))
        pygame.draw.ellipse(surface, _NS_ghrakmaal.PALETTE["iron_mid"],
                            (cx - actual_w // 2 + 1, cy - 1, actual_w - 2, 2))
        # Glowing rune center.
        for r in range(6, 0, -1):
            alpha = _NS_ghrakmaal._alpha(140 * (6 - r) / 6)
            _NS_ghrakmaal._aacircle(surface,
                                    (*_NS_ghrakmaal.PALETTE["molten_hot"], alpha),
                                    (cx, cy), r)
        _NS_ghrakmaal._aacircle(surface, _NS_ghrakmaal.PALETTE["molten_shine"], (cx, cy), 2)
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["white"], (cx, cy, 1, 1))
    def _draw_broken_totem(surface, tx, ty, phase):
        """Totem lying on ground after impact."""
        w = 26
        h = 12
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["shadow_deep"],
                         (tx - w // 2 + 2, ty - h // 2 + 4, w, h))
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["wood_darkest"],
                         (tx - w // 2, ty - h // 2 + 2, w, h))
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["wood_dark"],
                         (tx - w // 2 + 1, ty - h // 2 + 3, w - 2, h - 2))
        pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["wood_mid"],
                         (tx - w // 2 + 2, ty - h // 2 + 4, w - 4, h - 6))
        # End caps.
        for cap_x in (tx - w // 2, tx + w // 2 - 1):
            _NS_ghrakmaal._aacircle(surface, _NS_ghrakmaal.PALETTE["iron_dark"],
                                    (cap_x, ty + 2), h // 2)
            _NS_ghrakmaal._aacircle(surface, _NS_ghrakmaal.PALETTE["iron_mid"],
                                    (cap_x, ty + 2), h // 2 - 2)
        # Glowing runes.
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for rune_x in (tx - 6, tx + 6):
            for r in range(4, 0, -1):
                alpha = _NS_ghrakmaal._alpha(150 * (4 - r) / 4 * pulse)
                _NS_ghrakmaal._aacircle(surface,
                                        (*_NS_ghrakmaal.PALETTE["molten_hot"], alpha),
                                        (rune_x, ty + 2), r)
            pygame.draw.rect(surface, _NS_ghrakmaal.PALETTE["molten_shine"], (rune_x, ty + 2, 1, 1))



# ====================================================================
# SELUNARA (MOONBOUND HUNTRESS) - Mini Boss
# ====================================================================

class _NS_selunara:
    """Namespace selunara - moon rider mini boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Elf skin (pale)
        "skin_dark": (140, 105, 100),
        "skin_mid": (200, 165, 155),
        "skin_light": (240, 210, 195),
        # Dark hair (blue-black)
        "hair_dark": (15, 15, 30),
        "hair_mid": (30, 30, 55),
        "hair_light": (55, 55, 90),
        # Blue armor (dark navy with steel)
        "armor_darkest": (10, 15, 30),
        "armor_dark": (25, 35, 65),
        "armor_mid": (55, 75, 120),
        "armor_light": (110, 140, 190),
        "armor_shine": (180, 205, 240),
        # Gold trim
        "gold_dark": (85, 55, 15),
        "gold_mid": (175, 130, 40),
        "gold_light": (235, 195, 90),
        "gold_shine": (255, 240, 170),
        # Panther fur (dark blue-grey)
        "fur_darkest": (15, 20, 35),
        "fur_dark": (35, 45, 70),
        "fur_mid": (65, 80, 110),
        "fur_light": (115, 130, 165),
        "fur_shine": (170, 185, 215),
        # Panther belly (lighter)
        "belly_dark": (55, 60, 85),
        "belly_mid": (95, 105, 135),
        "belly_light": (150, 160, 190),
        # Lunar magic (purple-magenta)
        "lunar_darkest": (20, 5, 35),
        "lunar_dark": (75, 25, 130),
        "lunar_mid": (155, 70, 220),
        "lunar_light": (215, 145, 255),
        "lunar_shine": (245, 210, 255),
        "lunar_hot": (255, 240, 255),
        # Silver moonlight (Q beam + eclipse core)
        "moon_dark": (60, 60, 110),
        "moon_mid": (140, 145, 200),
        "moon_light": (215, 220, 255),
        "moon_shine": (255, 255, 255),
        # Glowing blue eyes (panther)
        "eye_dark": (15, 40, 90),
        "eye_mid": (60, 130, 230),
        "eye_light": (150, 210, 255),
        "eye_glow": (230, 245, 255),
        # Glaive/weapon steel
        "steel_dark": (35, 40, 65),
        "steel_mid": (110, 120, 155),
        "steel_light": (200, 210, 235),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 6),
        "white": (255, 255, 255),
    }
    # ------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_selunara._clamp(color)
        if _NS_selunara.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_selunara._clamp(color)
        if _NS_selunara.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_selunara._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 240 * getattr(boss, "direction", 1)), int(y)
    def _glaive_hand_position(boss, x, y):
        """Posisi tangan yang memegang glaive (untuk sumber projectile)."""
        facing = boss.direction
        # Rider berada di atas mount, tangan glaive di depan (facing side).
        hx = x + facing * 18
        hy = y - 28  # kira-kira sejajar dengan tangan rider
        # Small float animation.
        hy += int(math.sin(boss.pulse * 0.6) * 2)
        return hx, hy
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_selunara(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_selunara._update_attack_anim(boss)
        attack_progress = getattr(boss, "_sel_attack_progress", 0.0)
        attacking = (
            getattr(boss, "_sel_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 48) - 15
        )
        # Ambient FX.
        _NS_selunara._draw_lunar_aura(surface, x, y, pulse)
        _NS_selunara._draw_ground_ring(surface, x, y + 52, pulse, active_skill)
        # Skill ground FX (behind body).
        if active_skill == "q":
            _NS_selunara._draw_lucentbeam_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_selunara._draw_eclipse_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating body.
        float_bob = math.sin(pulse * 0.6) * 4
        body_y = y + int(float_bob)
        # Body pose.
        if attacking:
            _NS_selunara._draw_body_attack(surface, boss, x, body_y)
        else:
            _NS_selunara._draw_body_idle(surface, boss, x, body_y)
        # Shield bubble on top of body.
        if active_skill == "e":
            _NS_selunara._draw_lunar_shroud_bubble(surface, boss, x, body_y,
                                                   skill_timer, pulse)
        # Foreground FX (projectiles).
        if active_skill == "q":
            _NS_selunara._draw_lucentbeam_projectile(surface, boss, x, body_y,
                                                     skill_timer, pulse)
        elif active_skill == "w":
            _NS_selunara._draw_moonglaive_projectile(surface, boss, x, body_y,
                                                     skill_timer, pulse)
        elif active_skill == "r":
            _NS_selunara._draw_eclipse_beams(surface, boss, x, body_y,
                                             skill_timer, pulse)
        else:
            if attacking and attack_progress > 0:
                _NS_selunara._draw_basic_glaive_throw(surface, boss, x, body_y)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_sel_attack_active", False))
        if not active and timer >= cooldown - 2:
            boss._sel_attack_active = True
            boss._sel_attack_frame = 0
            active = True
        elif active:
            boss._sel_attack_frame = int(getattr(boss, "_sel_attack_frame", 0)) + 1
            if boss._sel_attack_frame >= cooldown:
                boss._sel_attack_active = False
                boss._sel_attack_frame = 0
                active = False
        boss._sel_previous_timer = timer
        boss._sel_attack_progress = (
            min(1.0, getattr(boss, "_sel_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # BODY DRAWING
    # ============================================================
    def _draw_body_idle(surface, boss, cx, cy):
        _NS_selunara._draw_float_shadow(surface, cx, cy + 54, boss.pulse)
        _NS_selunara._draw_floating_stars(surface, cx, cy + 40, boss.pulse)
        _NS_selunara._draw_body(surface, boss, cx, cy, "idle", 0)
    def _draw_body_attack(surface, boss, cx, cy):
        progress = getattr(boss, "_sel_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        _NS_selunara._draw_float_shadow(surface, cx, cy + 54, boss.pulse)
        _NS_selunara._draw_floating_stars(surface, cx, cy + 40, boss.pulse)
        _NS_selunara._draw_body(surface, boss, cx, cy, "attack", progress)
    def _draw_body(surface, boss, cx, cy, action, progress):
        """Full body: panther mount + rider on top."""
        facing = boss.direction
        phase = boss.pulse
        # Draw mount (panther) first - it's the base.
        _NS_selunara._draw_panther(surface, cx, cy + 8, facing, phase)
        # Draw rider on top.
        _NS_selunara._draw_rider(surface, cx, cy - 18, facing, phase, action, progress)
    # ============================================================
    # PANTHER MOUNT (Nova)
    # ============================================================
    def _draw_panther(surface, cx, cy, facing, phase):
        """Blue lunar panther/lion mount."""
        breath = math.sin(phase * 0.5) * 1
        # Tail (behind).
        _NS_selunara._draw_panther_tail(surface, cx, cy, facing, phase)
        # Back legs (partial, from side view).
        _NS_selunara._draw_panther_back_legs(surface, cx, cy, facing, phase)
        # Body (large elongated).
        body_pts = [
            (cx - facing * 28, cy - 2),          # back rump
            (cx - facing * 30, cy - 8),          # back top
            (cx - facing * 24, cy - 14),         # back
            (cx - facing * 10, cy - 16),         # mid back
            (cx + facing * 4, cy - 16),          # front back
            (cx + facing * 18, cy - 13),         # shoulder
            (cx + facing * 24, cy - 8),          # chest top
            (cx + facing * 26, cy - 2),          # chest front
            (cx + facing * 24, cy + 6),          # chest bottom
            (cx + facing * 14, cy + 10),         # belly front
            (cx - facing * 8, cy + 12),          # belly mid
            (cx - facing * 22, cy + 10),         # belly back
            (cx - facing * 28, cy + 4),          # rump bottom
        ]
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 3) for p in body_pts])
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["fur_darkest"], body_pts)
        # Body shading layers.
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["fur_dark"], [
            (cx - facing * 26, cy - 3),
            (cx - facing * 28, cy - 7),
            (cx - facing * 22, cy - 12),
            (cx - facing * 8, cy - 14),
            (cx + facing * 4, cy - 14),
            (cx + facing * 16, cy - 11),
            (cx + facing * 22, cy - 6),
            (cx + facing * 24, cy - 1),
            (cx + facing * 22, cy + 4),
            (cx + facing * 12, cy + 8),
            (cx - facing * 8, cy + 10),
            (cx - facing * 20, cy + 8),
            (cx - facing * 26, cy + 2),
        ])
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["fur_mid"], [
            (cx - facing * 22, cy - 5),
            (cx - facing * 20, cy - 10),
            (cx - facing * 6, cy - 12),
            (cx + facing * 4, cy - 12),
            (cx + facing * 14, cy - 9),
            (cx + facing * 18, cy - 4),
            (cx + facing * 16, cy),
            (cx - facing * 8, cy + 2),
            (cx - facing * 20, cy),
        ])
        # Highlight on back.
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["fur_light"], [
            (cx - facing * 12, cy - 10),
            (cx, cy - 11),
            (cx + facing * 8, cy - 9),
            (cx + facing * 4, cy - 6),
            (cx - facing * 8, cy - 6),
        ])
        # Sheen line.
        pygame.draw.line(surface, _NS_selunara.PALETTE["fur_shine"],
                         (cx - facing * 8, cy - 9), (cx + facing * 4, cy - 8), 1)
        # Belly (lighter).
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["belly_dark"], [
            (cx - facing * 20, cy + 6),
            (cx + facing * 14, cy + 6),
            (cx + facing * 18, cy + 8),
            (cx + facing * 12, cy + 10),
            (cx - facing * 8, cy + 11),
            (cx - facing * 20, cy + 9),
        ])
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["belly_mid"], [
            (cx - facing * 16, cy + 7),
            (cx + facing * 12, cy + 7),
            (cx + facing * 14, cy + 9),
            (cx - facing * 6, cy + 10),
            (cx - facing * 16, cy + 9),
        ])
        # Gold armor plate on shoulder/chest.
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["gold_dark"], [
            (cx + facing * 18, cy - 12),
            (cx + facing * 24, cy - 6),
            (cx + facing * 22, cy),
            (cx + facing * 14, cy - 4),
        ])
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["gold_mid"], [
            (cx + facing * 19, cy - 10),
            (cx + facing * 22, cy - 6),
            (cx + facing * 20, cy - 2),
            (cx + facing * 15, cy - 4),
        ])
        pygame.draw.rect(surface, _NS_selunara.PALETTE["gold_light"],
                         (cx + facing * 19, cy - 8, 2, 1))
        # Crescent moon symbol on shoulder plate.
        pygame.draw.circle(surface, _NS_selunara.PALETTE["lunar_light"],
                           (cx + facing * 18, cy - 6), 2)
        pygame.draw.circle(surface, _NS_selunara.PALETTE["gold_mid"],
                           (cx + facing * 19, cy - 6), 2)
        pygame.draw.rect(surface, _NS_selunara.PALETTE["lunar_shine"],
                         (cx + facing * 17, cy - 7, 1, 1))
        # Front legs.
        _NS_selunara._draw_panther_front_legs(surface, cx, cy, facing, phase)
        # Head (front).
        _NS_selunara._draw_panther_head(surface, cx + facing * 28, cy - 8,
                                        facing, phase)
    def _draw_panther_back_legs(surface, cx, cy, facing, phase):
        """Back legs (partial visible)."""
        # Rear leg.
        leg_x = cx - facing * 22
        pygame.draw.line(surface, _NS_selunara.PALETTE["fur_darkest"],
                         (leg_x, cy + 8), (leg_x - facing * 2, cy + 22), 6)
        pygame.draw.line(surface, _NS_selunara.PALETTE["fur_dark"],
                         (leg_x, cy + 8), (leg_x - facing * 2, cy + 22), 4)
        pygame.draw.line(surface, _NS_selunara.PALETTE["fur_mid"],
                         (leg_x, cy + 10), (leg_x - facing * 2, cy + 20), 2)
        # Paw.
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["fur_darkest"], [
            (leg_x - facing * 5, cy + 22),
            (leg_x + facing * 2, cy + 22),
            (leg_x + facing * 3, cy + 25),
            (leg_x - facing * 5, cy + 25),
        ])
        # Claws.
        for i, cx_off in enumerate((-3, 0, 2)):
            claw_x = leg_x + facing * cx_off
            pygame.draw.rect(surface, _NS_selunara.PALETTE["moon_light"],
                             (claw_x, cy + 25, 1, 1))
    def _draw_panther_front_legs(surface, cx, cy, facing, phase):
        """Front legs (muscular)."""
        leg_x = cx + facing * 20
        pygame.draw.line(surface, _NS_selunara.PALETTE["fur_darkest"],
                         (leg_x, cy + 6), (leg_x + facing * 2, cy + 22), 7)
        pygame.draw.line(surface, _NS_selunara.PALETTE["fur_dark"],
                         (leg_x, cy + 6), (leg_x + facing * 2, cy + 22), 5)
        pygame.draw.line(surface, _NS_selunara.PALETTE["fur_mid"],
                         (leg_x, cy + 8), (leg_x + facing * 2, cy + 20), 3)
        pygame.draw.line(surface, _NS_selunara.PALETTE["fur_light"],
                         (leg_x - 1, cy + 10), (leg_x + facing * 2 - 1, cy + 18), 1)
        # Paw.
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["fur_darkest"], [
            (leg_x - facing * 2, cy + 22),
            (leg_x + facing * 5, cy + 22),
            (leg_x + facing * 6, cy + 26),
            (leg_x - facing * 2, cy + 26),
        ])
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["fur_dark"], [
            (leg_x - facing * 1, cy + 23),
            (leg_x + facing * 4, cy + 23),
            (leg_x + facing * 4, cy + 25),
            (leg_x - facing * 1, cy + 25),
        ])
        # Glowing claws.
        for i, cx_off in enumerate((-1, 2, 5)):
            claw_x = leg_x + facing * cx_off
            pygame.draw.rect(surface, _NS_selunara.PALETTE["moon_mid"],
                             (claw_x, cy + 26, 1, 1))
            pygame.draw.rect(surface, _NS_selunara.PALETTE["moon_light"],
                             (claw_x, cy + 26, 1, 1))
    def _draw_panther_tail(surface, cx, cy, facing, phase):
        """Long swishy tail."""
        base_x = cx - facing * 28
        base_y = cy - 2
        tail_wave = math.sin(phase * 1.2) * 4
        segments = 6
        points = [(base_x, base_y)]
        for i in range(1, segments + 1):
            t = i / segments
            x_off = int(-facing * (10 + t * 12))
            y_off = int(-t * 6 + math.sin(phase * 1.2 + t * math.pi) * (3 + t * 2))
            points.append((base_x + x_off, base_y + y_off))
        # Draw tail tapered.
        for i in range(len(points) - 1):
            thickness = max(2, 6 - i)
            _NS_selunara._aaline(surface, _NS_selunara.PALETTE["shadow_deep"],
                                 (points[i][0] + 1, points[i][1] + 1),
                                 (points[i + 1][0] + 1, points[i + 1][1] + 1),
                                 thickness + 1)
            _NS_selunara._aaline(surface, _NS_selunara.PALETTE["fur_darkest"],
                                 points[i], points[i + 1], thickness)
            _NS_selunara._aaline(surface, _NS_selunara.PALETTE["fur_dark"],
                                 points[i], points[i + 1], max(1, thickness - 2))
            _NS_selunara._aaline(surface, _NS_selunara.PALETTE["fur_mid"],
                                 (points[i][0], points[i][1] - 1),
                                 (points[i + 1][0], points[i + 1][1] - 1),
                                 max(1, thickness - 4))
        # Tail tip glow (lunar magic).
        if len(points) >= 1:
            tip = points[-1]
            _NS_selunara._aacircle(surface, _NS_selunara.PALETTE["lunar_dark"], tip, 3)
            _NS_selunara._aacircle(surface, _NS_selunara.PALETTE["lunar_mid"], tip, 2)
            _NS_selunara._aacircle(surface, _NS_selunara.PALETTE["lunar_light"], tip, 1)
            pygame.draw.rect(surface, _NS_selunara.PALETTE["lunar_shine"],
                             (tip[0], tip[1], 1, 1))
    def _draw_panther_head(surface, hx, hy, facing, phase):
        """Panther head with glowing blue eyes."""
        # Head shape.
        head_pts = [
            (hx - facing * 8, hy - 2),
            (hx - facing * 6, hy - 8),
            (hx - facing * 2, hy - 10),
            (hx + facing * 4, hy - 9),
            (hx + facing * 8, hy - 4),
            (hx + facing * 10, hy),
            (hx + facing * 8, hy + 4),
            (hx + facing * 2, hy + 6),
            (hx - facing * 4, hy + 6),
            (hx - facing * 8, hy + 2),
        ]
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in head_pts])
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["fur_darkest"], head_pts)
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["fur_dark"], [
            (hx - facing * 7, hy - 1),
            (hx - facing * 5, hy - 7),
            (hx - facing * 1, hy - 9),
            (hx + facing * 4, hy - 8),
            (hx + facing * 7, hy - 3),
            (hx + facing * 9, hy),
            (hx + facing * 7, hy + 3),
            (hx + facing * 2, hy + 5),
            (hx - facing * 3, hy + 5),
            (hx - facing * 7, hy + 1),
        ])
        # Face highlights.
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["fur_mid"], [
            (hx - facing * 3, hy - 6),
            (hx + facing * 3, hy - 6),
            (hx + facing * 5, hy - 2),
            (hx + facing * 3, hy + 2),
            (hx - facing * 3, hy + 2),
        ])
        # Nose bridge.
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["fur_light"], [
            (hx + facing * 1, hy - 4),
            (hx + facing * 5, hy - 2),
            (hx + facing * 6, hy),
            (hx + facing * 3, hy - 1),
        ])
        # Ears (pointy).
        for side in (-1, 1):
            ear_x = hx + facing * (side * 4 - 1)
            ear_top_y = hy - 12
            _NS_selunara._poly(surface, _NS_selunara.PALETTE["fur_darkest"], [
                (ear_x - 2, hy - 7),
                (ear_x, ear_top_y),
                (ear_x + 3, hy - 8),
            ])
            _NS_selunara._poly(surface, _NS_selunara.PALETTE["fur_dark"], [
                (ear_x - 1, hy - 7),
                (ear_x, ear_top_y + 1),
                (ear_x + 2, hy - 8),
            ])
            # Inner ear pink glow.
            pygame.draw.rect(surface, _NS_selunara.PALETTE["lunar_light"],
                             (ear_x, hy - 9, 1, 1))
        # Glowing blue eyes.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for side in (-1, 1):
            ex = hx + facing * (side * 2 + 1)
            ey = hy - 3
            # Eye glow halo.
            for r in range(5, 0, -1):
                alpha = _NS_selunara._alpha(100 * (5 - r) / 5 * pulse)
                _NS_selunara._aacircle(surface,
                                       (*_NS_selunara.PALETTE["eye_mid"], alpha),
                                       (ex, ey), r)
            pygame.draw.rect(surface, _NS_selunara.PALETTE["eye_dark"], (ex - 1, ey, 3, 1))
            pygame.draw.rect(surface, _NS_selunara.PALETTE["eye_mid"], (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_selunara.PALETTE["eye_light"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_selunara.PALETTE["eye_glow"], (ex, ey, 1, 1))
        # Nose.
        pygame.draw.rect(surface, _NS_selunara.PALETTE["shadow_deep"],
                         (hx + facing * 7, hy + 1, 2, 1))
        # Mouth line.
        pygame.draw.line(surface, _NS_selunara.PALETTE["shadow_deep"],
                         (hx + facing * 5, hy + 4),
                         (hx + facing * 8, hy + 3), 1)
        # Small fangs.
        pygame.draw.rect(surface, _NS_selunara.PALETTE["moon_light"],
                         (hx + facing * 6, hy + 4, 1, 1))
        pygame.draw.rect(surface, _NS_selunara.PALETTE["moon_light"],
                         (hx + facing * 7, hy + 4, 1, 1))
        # Crescent moon mark on forehead.
        cx_moon = hx + facing * 1
        cy_moon = hy - 6
        pygame.draw.arc(surface, _NS_selunara.PALETTE["lunar_light"],
                        (cx_moon - 2, cy_moon - 2, 4, 4),
                        math.pi / 4, math.pi * 5 / 4, 1)
        pygame.draw.rect(surface, _NS_selunara.PALETTE["lunar_shine"],
                         (cx_moon, cy_moon - 1, 1, 1))
    # ============================================================
    # RIDER (Selunara herself)
    # ============================================================
    def _draw_rider(surface, cx, cy, facing, phase, action, progress):
        """Elf rider sitting on panther."""
        # Cape behind.
        _NS_selunara._draw_rider_cape(surface, cx, cy, facing, phase)
        # Torso.
        _NS_selunara._draw_rider_torso(surface, cx, cy, facing, phase)
        # Legs (astride mount).
        _NS_selunara._draw_rider_legs(surface, cx, cy, facing, phase)
        # Arms and glaive.
        _NS_selunara._draw_rider_arms(surface, cx, cy, facing, phase, action, progress)
        # Head with helm.
        _NS_selunara._draw_rider_head(surface, cx, cy - 14, facing, phase)
    def _draw_rider_cape(surface, cx, cy, facing, phase):
        """Blue cape flowing behind rider."""
        sway = math.sin(phase * 0.6) * 2
        cape_pts = [
            (cx - facing * 6, cy - 8),
            (cx - facing * 12 + int(sway), cy),
            (cx - facing * 15 + int(sway), cy + 8),
            (cx - facing * 12 + int(sway * 0.5), cy + 16),
            (cx - facing * 6, cy + 18),
            (cx + facing * 2, cy + 10),
            (cx + facing * 2, cy - 6),
        ]
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in cape_pts])
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["armor_darkest"], cape_pts)
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["armor_dark"], [
            (cx - facing * 5, cy - 7),
            (cx - facing * 10 + int(sway), cy),
            (cx - facing * 12 + int(sway), cy + 8),
            (cx - facing * 10 + int(sway * 0.5), cy + 14),
            (cx - facing * 5, cy + 16),
            (cx + facing * 1, cy + 8),
        ])
        # Gold trim edge.
        pygame.draw.line(surface, _NS_selunara.PALETTE["gold_mid"],
                         (cx - facing * 6, cy - 8),
                         (cx - facing * 12 + int(sway), cy), 1)
        pygame.draw.line(surface, _NS_selunara.PALETTE["gold_dark"],
                         (cx - facing * 12 + int(sway), cy),
                         (cx - facing * 15 + int(sway), cy + 8), 1)
    def _draw_rider_torso(surface, cx, cy, facing, phase):
        """Dark blue armored torso."""
        torso_pts = [
            (cx - 7, cy - 10),
            (cx - 9, cy - 4),
            (cx - 7, cy + 6),
            (cx + 7, cy + 6),
            (cx + 9, cy - 4),
            (cx + 7, cy - 10),
        ]
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in torso_pts])
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["armor_darkest"], torso_pts)
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["armor_dark"], [
            (cx - 6, cy - 9),
            (cx - 8, cy - 4),
            (cx - 6, cy + 5),
            (cx + 6, cy + 5),
            (cx + 8, cy - 4),
            (cx + 6, cy - 9),
        ])
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["armor_mid"], [
            (cx - 4, cy - 7),
            (cx - 5, cy - 3),
            (cx - 3, cy + 3),
            (cx + 3, cy + 3),
            (cx + 5, cy - 3),
            (cx + 4, cy - 7),
        ])
        # Chest highlight.
        pygame.draw.line(surface, _NS_selunara.PALETTE["armor_light"],
                         (cx - 2, cy - 6), (cx + 2, cy - 6), 1)
        # Cleavage/center line.
        pygame.draw.line(surface, _NS_selunara.PALETTE["armor_darkest"],
                         (cx, cy - 6), (cx, cy + 2), 1)
        # Gold belt.
        pygame.draw.rect(surface, _NS_selunara.PALETTE["gold_dark"],
                         (cx - 7, cy + 4, 14, 3))
        pygame.draw.rect(surface, _NS_selunara.PALETTE["gold_mid"],
                         (cx - 6, cy + 4, 12, 2))
        pygame.draw.rect(surface, _NS_selunara.PALETTE["gold_light"],
                         (cx - 5, cy + 5, 10, 1))
        # Belt gem.
        _NS_selunara._aacircle(surface, _NS_selunara.PALETTE["lunar_dark"], (cx, cy + 5), 2)
        _NS_selunara._aacircle(surface, _NS_selunara.PALETTE["lunar_mid"], (cx, cy + 5), 1)
        pygame.draw.rect(surface, _NS_selunara.PALETTE["lunar_shine"], (cx, cy + 5, 1, 1))
        # Shoulder pauldrons.
        for side in (-1, 1):
            base_x = cx + side * 8
            paul_pts = [
                (base_x - side, cy - 9),
                (base_x + side * 4, cy - 11),
                (base_x + side * 5, cy - 6),
                (base_x + side * 2, cy - 4),
                (base_x - side, cy - 6),
            ]
            _NS_selunara._poly(surface, _NS_selunara.PALETTE["armor_darkest"], paul_pts)
            _NS_selunara._poly(surface, _NS_selunara.PALETTE["gold_dark"], [
                (base_x, cy - 8),
                (base_x + side * 3, cy - 10),
                (base_x + side * 4, cy - 7),
                (base_x + side, cy - 5),
            ])
            _NS_selunara._poly(surface, _NS_selunara.PALETTE["gold_mid"], [
                (base_x + side, cy - 8),
                (base_x + side * 3, cy - 9),
                (base_x + side * 3, cy - 7),
                (base_x + side, cy - 6),
            ])
            pygame.draw.rect(surface, _NS_selunara.PALETTE["gold_light"],
                             (base_x + side * 2, cy - 9, 1, 1))
            # Spike on pauldron.
            _NS_selunara._poly(surface, _NS_selunara.PALETTE["armor_darkest"], [
                (base_x + side * 2, cy - 11),
                (base_x + side * 3, cy - 15),
                (base_x + side * 4, cy - 10),
            ])
            _NS_selunara._poly(surface, _NS_selunara.PALETTE["armor_mid"], [
                (base_x + side * 3, cy - 11),
                (base_x + side * 3, cy - 14),
                (base_x + side * 4, cy - 10),
            ])
            pygame.draw.rect(surface, _NS_selunara.PALETTE["armor_shine"],
                             (base_x + side * 3, cy - 14, 1, 1))
    def _draw_rider_legs(surface, cx, cy, facing, phase):
        """Legs astride the mount (partially visible)."""
        # Left leg (thigh visible).
        for side in (-1, 1):
            leg_x = cx + side * 4
            # Thigh going down to mount.
            _NS_selunara._poly(surface, _NS_selunara.PALETTE["armor_darkest"], [
                (leg_x - 2, cy + 6),
                (leg_x + 3, cy + 6),
                (leg_x + 4, cy + 14),
                (leg_x - 1, cy + 14),
            ])
            _NS_selunara._poly(surface, _NS_selunara.PALETTE["armor_dark"], [
                (leg_x - 1, cy + 7),
                (leg_x + 2, cy + 7),
                (leg_x + 3, cy + 13),
                (leg_x, cy + 13),
            ])
            _NS_selunara._poly(surface, _NS_selunara.PALETTE["armor_mid"], [
                (leg_x, cy + 8),
                (leg_x + 1, cy + 8),
                (leg_x + 2, cy + 12),
                (leg_x + 1, cy + 12),
            ])
            # Gold knee.
            pygame.draw.rect(surface, _NS_selunara.PALETTE["gold_mid"],
                             (leg_x, cy + 13, 2, 1))
    def _draw_rider_arms(surface, cx, cy, facing, phase, action, progress):
        """Two arms: one holds glaive (front), other rein (back)."""
        # Swing animation.
        swing = 0
        if action == "attack":
            # Wind back → forward throw.
            if progress < 0.35:
                swing = -int(progress / 0.35 * 6)  # wind back
            elif progress < 0.55:
                t = (progress - 0.35) / 0.2
                swing = int(-6 + t * 14)  # throw forward
            else:
                t = (progress - 0.55) / 0.45
                swing = int(8 * (1 - t))  # return
        # Front arm (glaive).
        shoulder_x = cx + facing * 6
        shoulder_y = cy - 6
        # Elbow position depends on swing.
        elbow_x = shoulder_x + facing * (6 + swing)
        elbow_y = shoulder_y + 4
        hand_x = elbow_x + facing * (8 + swing // 2)
        hand_y = elbow_y - 2 - swing // 2
        # Upper arm.
        pygame.draw.line(surface, _NS_selunara.PALETTE["armor_darkest"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        pygame.draw.line(surface, _NS_selunara.PALETTE["armor_dark"],
                         (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        pygame.draw.line(surface, _NS_selunara.PALETTE["armor_mid"],
                         (shoulder_x, shoulder_y - 1), (elbow_x, elbow_y - 1), 1)
        # Forearm.
        pygame.draw.line(surface, _NS_selunara.PALETTE["armor_darkest"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 4)
        pygame.draw.line(surface, _NS_selunara.PALETTE["armor_dark"],
                         (elbow_x, elbow_y), (hand_x, hand_y), 3)
        pygame.draw.line(surface, _NS_selunara.PALETTE["armor_mid"],
                         (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
        # Hand.
        _NS_selunara._aacircle(surface, _NS_selunara.PALETTE["skin_dark"], (hand_x, hand_y), 2)
        _NS_selunara._aacircle(surface, _NS_selunara.PALETTE["skin_mid"], (hand_x, hand_y), 1)
        # Glaive (moon-shaped weapon) - only drawn if NOT thrown.
        # Selama attack, glaive tetap terlihat sampai frame throw.
        if action == "attack" and progress > 0.5 and progress < 0.9:
            pass  # glaive is airborne, drawn as projectile
        else:
            _NS_selunara._draw_glaive(surface, hand_x, hand_y, facing, phase)
        # Store hand position for projectile source.
        # (used in _glaive_hand_position, but we compute there separately)
        # Back arm (holding reins).
        back_sh_x = cx - facing * 4
        back_sh_y = cy - 6
        back_elbow_x = back_sh_x - facing * 2
        back_elbow_y = back_sh_y + 4
        back_hand_x = back_elbow_x + facing * 2
        back_hand_y = back_elbow_y + 4
        pygame.draw.line(surface, _NS_selunara.PALETTE["armor_darkest"],
                         (back_sh_x, back_sh_y), (back_elbow_x, back_elbow_y), 4)
        pygame.draw.line(surface, _NS_selunara.PALETTE["armor_dark"],
                         (back_sh_x, back_sh_y), (back_elbow_x, back_elbow_y), 3)
        pygame.draw.line(surface, _NS_selunara.PALETTE["armor_darkest"],
                         (back_elbow_x, back_elbow_y), (back_hand_x, back_hand_y), 3)
        pygame.draw.line(surface, _NS_selunara.PALETTE["armor_dark"],
                         (back_elbow_x, back_elbow_y), (back_hand_x, back_hand_y), 2)
        _NS_selunara._aacircle(surface, _NS_selunara.PALETTE["skin_dark"],
                               (back_hand_x, back_hand_y), 1)
    def _draw_glaive(surface, hx, hy, facing, phase):
        """Crescent moon-shaped glaive."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Handle grip.
        grip_end_x = hx + facing * 2
        grip_end_y = hy - 6
        pygame.draw.line(surface, _NS_selunara.PALETTE["gold_dark"],
                         (hx, hy), (grip_end_x, grip_end_y), 3)
        pygame.draw.line(surface, _NS_selunara.PALETTE["gold_mid"],
                         (hx, hy), (grip_end_x, grip_end_y), 2)
        # Curved blade (crescent).
        blade_center_x = grip_end_x
        blade_center_y = grip_end_y - 4
        # Inner arc points.
        blade_pts_outer = []
        blade_pts_inner = []
        for i in range(9):
            t = i / 8
            angle = math.pi * 0.2 + t * math.pi * 0.9
            # Outer curve (blade edge).
            ox = blade_center_x + int(math.cos(angle) * 9) * facing
            oy = blade_center_y + int(math.sin(angle) * 9) - 2
            blade_pts_outer.append((ox, oy))
            # Inner curve.
            ix = blade_center_x + int(math.cos(angle) * 5) * facing
            iy = blade_center_y + int(math.sin(angle) * 5) - 2
            blade_pts_inner.append((ix, iy))
        # Blade shape (crescent).
        blade_pts = blade_pts_outer + list(reversed(blade_pts_inner))
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 1) for p in blade_pts])
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["steel_dark"], blade_pts)
        # Inner shading.
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["steel_mid"], [
            (p[0] - facing, p[1] + 1) for p in blade_pts_outer
        ] + list(reversed([(p[0] + facing, p[1] - 1) for p in blade_pts_inner])))
        # Edge highlight.
        for p in blade_pts_outer:
            pygame.draw.rect(surface, _NS_selunara.PALETTE["steel_light"], (p[0], p[1], 1, 1))
        # Lunar glow along blade.
        for r in range(6, 0, -1):
            alpha = _NS_selunara._alpha(60 * (6 - r) / 6 * pulse)
            _NS_selunara._aacircle(surface,
                                   (*_NS_selunara.PALETTE["lunar_mid"], alpha),
                                   (blade_pts_outer[4][0], blade_pts_outer[4][1]), r)
        pygame.draw.rect(surface, _NS_selunara.PALETTE["lunar_shine"],
                         (blade_pts_outer[4][0], blade_pts_outer[4][1], 1, 1))
    def _draw_rider_head(surface, cx, cy, facing, phase):
        """Elf head with horned helm and long hair."""
        # Long hair behind (flowing).
        sway = math.sin(phase * 0.5) * 1
        hair_pts = [
            (cx - 5, cy - 2),
            (cx - 7 + int(sway), cy + 4),
            (cx - 6 + int(sway), cy + 12),
            (cx - 3 + int(sway * 0.5), cy + 18),
            (cx + 3, cy + 18),
            (cx + 5, cy + 8),
            (cx + 4, cy),
        ]
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 1) for p in hair_pts])
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["hair_dark"], hair_pts)
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["hair_mid"], [
            (cx - 4, cy - 1),
            (cx - 6 + int(sway), cy + 4),
            (cx - 5 + int(sway), cy + 10),
            (cx - 2 + int(sway * 0.5), cy + 16),
            (cx + 2, cy + 16),
            (cx + 4, cy + 8),
        ])
        # Face.
        face_pts = [
            (cx - 4, cy - 2),
            (cx - 5, cy + 2),
            (cx - 3, cy + 6),
            (cx + 3, cy + 6),
            (cx + 5, cy + 2),
            (cx + 4, cy - 2),
        ]
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 1) for p in face_pts])
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["skin_dark"], face_pts)
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["skin_mid"], [
            (cx - 3, cy - 1),
            (cx - 4, cy + 2),
            (cx - 2, cy + 5),
            (cx + 2, cy + 5),
            (cx + 4, cy + 2),
            (cx + 3, cy - 1),
        ])
        pygame.draw.rect(surface, _NS_selunara.PALETTE["skin_light"], (cx - 1, cy + 1, 1, 1))
        pygame.draw.rect(surface, _NS_selunara.PALETTE["skin_light"], (cx + 1, cy + 1, 1, 1))
        # Elf pointy ears.
        for side in (-1, 1):
            _NS_selunara._poly(surface, _NS_selunara.PALETTE["skin_dark"], [
                (cx + side * 4, cy + 1),
                (cx + side * 6, cy - 2),
                (cx + side * 5, cy + 3),
            ])
            pygame.draw.rect(surface, _NS_selunara.PALETTE["skin_mid"],
                             (cx + side * 5, cy, 1, 1))
        # Glowing blue eyes.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy + 2
            for r in range(3, 0, -1):
                alpha = _NS_selunara._alpha(120 * (3 - r) / 3 * pulse)
                _NS_selunara._aacircle(surface,
                                       (*_NS_selunara.PALETTE["eye_mid"], alpha),
                                       (ex, ey), r)
            pygame.draw.rect(surface, _NS_selunara.PALETTE["eye_light"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_selunara.PALETTE["eye_glow"], (ex, ey, 1, 1))
        # Mouth.
        pygame.draw.line(surface, _NS_selunara.PALETTE["shadow_deep"],
                         (cx - 1, cy + 4), (cx + 1, cy + 4), 1)
        # HELM (winged/horned with crescent moon gem).
        _NS_selunara._draw_helm(surface, cx, cy, facing, phase)
    def _draw_helm(surface, cx, cy, facing, phase):
        """Ornate winged helm with lunar gem."""
        # Base helm cap.
        helm_pts = [
            (cx - 5, cy - 3),
            (cx - 6, cy - 6),
            (cx - 3, cy - 9),
            (cx + 3, cy - 9),
            (cx + 6, cy - 6),
            (cx + 5, cy - 3),
        ]
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 1) for p in helm_pts])
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["armor_darkest"], helm_pts)
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["armor_dark"], [
            (cx - 4, cy - 3),
            (cx - 5, cy - 5),
            (cx - 2, cy - 8),
            (cx + 2, cy - 8),
            (cx + 5, cy - 5),
            (cx + 4, cy - 3),
        ])
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["armor_mid"], [
            (cx - 2, cy - 4),
            (cx - 3, cy - 6),
            (cx - 1, cy - 7),
            (cx + 1, cy - 7),
            (cx + 3, cy - 6),
            (cx + 2, cy - 4),
        ])
        pygame.draw.rect(surface, _NS_selunara.PALETTE["armor_shine"], (cx, cy - 7, 1, 1))
        # Gold trim.
        pygame.draw.line(surface, _NS_selunara.PALETTE["gold_mid"],
                         (cx - 5, cy - 3), (cx + 5, cy - 3), 1)
        pygame.draw.line(surface, _NS_selunara.PALETTE["gold_light"],
                         (cx - 3, cy - 3), (cx + 3, cy - 3), 1)
        # Central crescent moon gem.
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        gem_x = cx
        gem_y = cy - 6
        for r in range(4, 0, -1):
            alpha = _NS_selunara._alpha(120 * (4 - r) / 4 * pulse)
            _NS_selunara._aacircle(surface,
                                   (*_NS_selunara.PALETTE["lunar_mid"], alpha),
                                   (gem_x, gem_y), r)
        pygame.draw.rect(surface, _NS_selunara.PALETTE["lunar_dark"], (gem_x - 1, gem_y, 3, 1))
        pygame.draw.rect(surface, _NS_selunara.PALETTE["lunar_mid"], (gem_x, gem_y, 2, 1))
        pygame.draw.rect(surface, _NS_selunara.PALETTE["lunar_shine"], (gem_x, gem_y, 1, 1))
        # Side horns/wings on helm.
        for side in (-1, 1):
            horn_base_x = cx + side * 5
            horn_base_y = cy - 6
            horn_tip_x = cx + side * 9
            horn_tip_y = cy - 12
            _NS_selunara._poly(surface, _NS_selunara.PALETTE["shadow_deep"], [
                (horn_base_x + 1, horn_base_y + 1),
                (horn_tip_x + 1, horn_tip_y + 1),
                (horn_base_x + side * 2 + 1, horn_base_y - 1 + 1),
            ])
            _NS_selunara._poly(surface, _NS_selunara.PALETTE["gold_dark"], [
                (horn_base_x, horn_base_y),
                (horn_tip_x, horn_tip_y),
                (horn_base_x + side * 2, horn_base_y - 1),
            ])
            _NS_selunara._poly(surface, _NS_selunara.PALETTE["gold_mid"], [
                (horn_base_x + side, horn_base_y),
                (horn_tip_x, horn_tip_y),
                (horn_base_x + side * 2, horn_base_y - 1),
            ])
            pygame.draw.rect(surface, _NS_selunara.PALETTE["gold_light"],
                             (horn_tip_x, horn_tip_y, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        """Shadow beneath mount."""
        breath = math.sin(phase * 0.6) * 0.15 + 0.85
        shadow = pygame.Surface((150, 30), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, int((12 - radius) * 16 * breath))
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (12 - radius, 15 - radius,
                                 126 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (5, 5, 15, int(160 * breath)),
                            (10, 10, 130, 10))
        surface.blit(shadow, (x - 75, y - 15))
    def _draw_floating_stars(surface, cx, cy, phase):
        """Small floating star particles under character."""
        for i in range(8):
            t = (phase * 0.4 + i * 0.13) % 1.0
            dx = cx + int(math.sin(phase + i * 0.7) * 25) - 12 + i * 3
            dy = cy - int(t * 18)
            alpha = _NS_selunara._alpha(200 * (1 - t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_selunara.PALETTE["lunar_mid"], alpha),
                                 (dx, dy, 1, 1))
                pygame.draw.rect(surface, (*_NS_selunara.PALETTE["lunar_shine"], alpha),
                                 (dx, dy - 1, 1, 1))
    def _draw_lunar_aura(surface, x, y, phase):
        """Purple lunar aura around character."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_selunara._alpha((85 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_selunara._aacircle(aura,
                                       (*_NS_selunara.PALETTE["lunar_darkest"], alpha),
                                       (100, 90), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_selunara._alpha((55 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_selunara._aacircle(aura,
                                       (*_NS_selunara.PALETTE["lunar_dark"], alpha),
                                       (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))
        # Floating star particles.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 42 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_selunara.PALETTE["lunar_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_selunara.PALETTE["lunar_shine"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Runic ground ring with lunar theme."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 56), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_selunara.PALETTE["lunar_darkest"], 200),
                            (5, 18, 170, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_selunara.PALETTE["lunar_dark"], 220),
                            (14, 20, 152, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_selunara.PALETTE["lunar_mid"], 180),
                            (25, 22, 130, 18), 1)
        # Star runes.
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 90 + int(math.cos(angle) * 48)
            y1 = 30 + int(math.sin(angle) * 8)
            x2 = 90 + int(math.cos(angle) * 74)
            y2 = 30 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_selunara.PALETTE["lunar_light"], 220),
                             (x1, y1), (x2, y2), 1)
            pygame.draw.rect(ring, _NS_selunara.PALETTE["lunar_shine"], (x2, y2, 1, 1))
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_selunara.PALETTE["lunar_shine"],
                                 _NS_selunara._alpha(150 * pulse)),
                                (15, 12, 150, 38), 1)
        surface.blit(ring, (x - 90, y - 28))
    # ============================================================
    # BASIC ATTACK: Glaive throw
    # ============================================================
    def _draw_basic_glaive_throw(surface, boss, x, y):
        """Throw a small crescent glaive at target."""
        progress = getattr(boss, "_sel_attack_progress", 0.0)
        if progress < 0.5:
            return
        facing = boss.direction
        tx, ty = _NS_selunara._target_position(boss, x, y)
        sx, sy = _NS_selunara._glaive_hand_position(boss, x, y)
        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        # Arc trajectory.
        arc = math.sin(t * math.pi) * 12
        bx = int(sx + (tx - sx) * t)
        by = int(sy + (ty - sy) * t - arc)
        # Rotation angle for glaive.
        rot = t * math.pi * 4  # spinning
        # Trail (crescent shapes).
        for i in range(7):
            trail_t = max(0.0, t - i * 0.06)
            px = int(sx + (tx - sx) * trail_t)
            py = int(sy + (ty - sy) * trail_t - math.sin(trail_t * math.pi) * 12)
            alpha = _NS_selunara._alpha(220 - i * 28)
            size = max(1, 5 - i)
            _NS_selunara._aacircle(surface,
                                   (*_NS_selunara.PALETTE["lunar_dark"], alpha),
                                   (px, py), size)
            _NS_selunara._aacircle(surface,
                                   (*_NS_selunara.PALETTE["lunar_mid"], alpha),
                                   (px, py), max(1, size - 1))
            _NS_selunara._aacircle(surface,
                                   (*_NS_selunara.PALETTE["lunar_light"], alpha),
                                   (px, py), max(1, size - 2))
        # Draw spinning glaive at bx, by.
        _NS_selunara._draw_flying_glaive(surface, bx, by, rot, facing)
    def _draw_flying_glaive(surface, cx, cy, rot, facing):
        """Draw a spinning crescent glaive."""
        # Compute crescent points rotated.
        outer_pts = []
        inner_pts = []
        for i in range(9):
            t = i / 8
            angle = math.pi * 0.2 + t * math.pi * 0.9 + rot
            ox = cx + int(math.cos(angle) * 7)
            oy = cy + int(math.sin(angle) * 7)
            outer_pts.append((ox, oy))
            ix = cx + int(math.cos(angle) * 3)
            iy = cy + int(math.sin(angle) * 3)
            inner_pts.append((ix, iy))
        blade_pts = outer_pts + list(reversed(inner_pts))
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 1) for p in blade_pts])
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["steel_dark"], blade_pts)
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["steel_mid"],
                           [(p[0], p[1]) for p in outer_pts] +
                           list(reversed([(p[0], p[1]) for p in inner_pts])))
        # Edge highlight.
        for p in outer_pts:
            pygame.draw.rect(surface, _NS_selunara.PALETTE["steel_light"], (p[0], p[1], 1, 1))
        # Lunar glow center.
        _NS_selunara._aacircle(surface, _NS_selunara.PALETTE["lunar_mid"], (cx, cy), 3)
        _NS_selunara._aacircle(surface, _NS_selunara.PALETTE["lunar_light"], (cx, cy), 2)
        pygame.draw.rect(surface, _NS_selunara.PALETTE["lunar_shine"], (cx, cy, 1, 1))
    # ============================================================
    # SKILL Q: LUCENT BEAM (vertical beam from sky on target)
    # ============================================================
    def _draw_lucentbeam_ground(surface, boss, x, y, timer, phase):
        """Ground rune at target."""
        tx, ty = _NS_selunara._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            t = progress / 0.3
            r = int(15 * t)
            alpha = _NS_selunara._alpha(200 * t)
            pygame.draw.ellipse(surface, (*_NS_selunara.PALETTE["lunar_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)
            # Runes.
            for i in range(6):
                angle = i * math.pi / 3 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_selunara.PALETTE["lunar_shine"], (sx, sy, 2, 2))
        else:
            # Aftermath crater.
            t = (progress - 0.3) / 0.7
            r = int(20 + t * 8)
            alpha = _NS_selunara._alpha(200 * (1 - t * 0.5))
            pygame.draw.ellipse(surface, (*_NS_selunara.PALETTE["lunar_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_selunara.PALETTE["lunar_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_selunara.PALETTE["lunar_mid"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
    def _draw_lucentbeam_projectile(surface, boss, x, y, timer, phase):
        """Beam from Selunara's glaive at target."""
        tx, ty = _NS_selunara._target_position(boss, x, y)
        sx, sy = _NS_selunara._glaive_hand_position(boss, x, y)
        # Beam origin adjusted upward (glaive tip).
        sy -= 4
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Charge at glaive.
            t = progress / 0.3
            cr = int(3 + t * 7)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_selunara._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_selunara._aacircle(surface,
                                       (*_NS_selunara.PALETTE["lunar_dark"], alpha),
                                       (sx, sy), r)
            _NS_selunara._aacircle(surface, _NS_selunara.PALETTE["lunar_mid"], (sx, sy), cr - 1)
            _NS_selunara._aacircle(surface, _NS_selunara.PALETTE["lunar_light"], (sx, sy), max(1, cr - 3))
            _NS_selunara._aacircle(surface, _NS_selunara.PALETTE["lunar_shine"], (sx, sy), max(1, cr - 5))
            # Orbit sparks.
            for i in range(6):
                angle = phase * 5 + i * math.pi / 3
                orbit_r = cr + 4
                ox = sx + int(math.cos(angle) * orbit_r)
                oy = sy + int(math.sin(angle) * orbit_r)
                pygame.draw.rect(surface, _NS_selunara.PALETTE["lunar_shine"], (ox, oy, 1, 1))
        elif progress < 0.75:
            # BEAM STRIKE.
            t = (progress - 0.3) / 0.45
            intensity = math.sin(t * math.pi)
            # Multi-layer beam from glaive to target.
            for width, color in [
                (10, _NS_selunara.PALETTE["lunar_darkest"]),
                (7, _NS_selunara.PALETTE["lunar_dark"]),
                (5, _NS_selunara.PALETTE["lunar_mid"]),
                (3, _NS_selunara.PALETTE["lunar_light"]),
                (1, _NS_selunara.PALETTE["moon_shine"]),
            ]:
                alpha = _NS_selunara._alpha(255 * intensity)
                if alpha > 0:
                    pygame.draw.line(surface, (*color, alpha), (sx, sy), (tx, ty), width)
            pygame.draw.line(surface, _NS_selunara.PALETTE["white"], (sx, sy), (tx, ty), 1)
            # Sparks along beam.
            for i in range(15):
                spark_t = ((phase * 3 + i * 0.08) % 1.0)
                dx = tx - sx
                dy = ty - sy
                length = max(1, math.sqrt(dx * dx + dy * dy))
                perp_x = -dy / length
                perp_y = dx / length
                px = int(sx + dx * spark_t)
                py = int(sy + dy * spark_t)
                offset = math.sin(phase * 6 + i) * 4
                px += int(perp_x * offset)
                py += int(perp_y * offset)
                alpha = _NS_selunara._alpha(230 * intensity)
                pygame.draw.rect(surface, (*_NS_selunara.PALETTE["lunar_shine"], alpha),
                                 (px, py, 2, 2))
                pygame.draw.rect(surface, (*_NS_selunara.PALETTE["white"], alpha),
                                 (px, py, 1, 1))
            # Impact burst.
            impact_r = int(12 + t * 16)
            alpha = _NS_selunara._alpha(240 * intensity)
            _NS_selunara._aacircle(surface, (*_NS_selunara.PALETTE["lunar_darkest"], alpha),
                                   (tx, ty), impact_r + 2, 2)
            _NS_selunara._aacircle(surface, (*_NS_selunara.PALETTE["lunar_dark"], alpha),
                                   (tx, ty), impact_r, 2)
            _NS_selunara._aacircle(surface, (*_NS_selunara.PALETTE["lunar_mid"], alpha),
                                   (tx, ty), max(1, impact_r - 5), 2)
            _NS_selunara._aacircle(surface, (*_NS_selunara.PALETTE["lunar_light"], alpha),
                                   (tx, ty), max(1, impact_r - 10), 1)
            _NS_selunara._aacircle(surface, (*_NS_selunara.PALETTE["lunar_shine"], alpha),
                                   (tx, ty), max(1, impact_r // 4))
            for i in range(10):
                angle_s = i * math.pi / 5
                ex = tx + int(math.cos(angle_s) * impact_r)
                ey = ty + int(math.sin(angle_s) * impact_r * 0.7)
                pygame.draw.rect(surface, (*_NS_selunara.PALETTE["lunar_shine"], alpha),
                                 (ex, ey, 2, 2))
        else:
            # Aftermath sparkles.
            t = (progress - 0.75) / 0.25
            for i in range(10):
                rise_t = (phase * 0.6 + i * 0.1) % 1.0
                rx = tx + int(math.sin(phase + i) * 15)
                ry = ty - int(rise_t * 22)
                alpha = _NS_selunara._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    pygame.draw.rect(surface, (*_NS_selunara.PALETTE["lunar_mid"], alpha),
                                     (rx, ry, 2, 2))
                    pygame.draw.rect(surface, (*_NS_selunara.PALETTE["lunar_shine"], alpha),
                                     (rx, ry, 1, 1))
    # ============================================================
    # SKILL W: MOON GLAIVE (arcing crescent)
    # ============================================================
    def _draw_moonglaive_projectile(surface, boss, x, y, timer, phase):
        """Big crescent glaive arcs forward and returns."""
        tx, ty = _NS_selunara._target_position(boss, x, y)
        sx, sy = _NS_selunara._glaive_hand_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.2:
            # Charge at glaive.
            t = progress / 0.2
            cr = int(4 + t * 6)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_selunara._alpha(220 * (cr + 4 - r) / (cr + 4))
                _NS_selunara._aacircle(surface,
                                       (*_NS_selunara.PALETTE["lunar_dark"], alpha),
                                       (sx, sy), r)
            _NS_selunara._aacircle(surface, _NS_selunara.PALETTE["lunar_mid"], (sx, sy), cr - 1)
            _NS_selunara._aacircle(surface, _NS_selunara.PALETTE["lunar_light"], (sx, sy), max(1, cr - 3))
            return
        # Trajectory: out and back (boomerang).
        t = (progress - 0.2) / 0.8
        # Position along boomerang path.
        # Out: t=0 to 0.5, back: 0.5 to 1.0.
        if t < 0.5:
            path_t = t / 0.5  # 0 → 1 (out)
            cur_target = (tx, ty)
        else:
            path_t = 1.0 - ((t - 0.5) / 0.5)  # 1 → 0 (back)
            cur_target = (tx, ty)
        # Position: interpolate sx,sy → tx,ty with arc.
        arc = math.sin(path_t * math.pi) * 20
        bx = int(sx + (cur_target[0] - sx) * path_t)
        by = int(sy + (cur_target[1] - sy) * path_t - arc)
        rot = t * math.pi * 8  # fast spin
        # Big trail (crescent afterimage).
        for i in range(10):
            trail_t = max(0.0, path_t - i * 0.05)
            if t < 0.5:
                # Going out.
                tpath = trail_t
            else:
                # Coming back.
                tpath = max(0.0, trail_t)
            px = int(sx + (cur_target[0] - sx) * tpath)
            py = int(sy + (cur_target[1] - sy) * tpath -
                     math.sin(tpath * math.pi) * 20)
            alpha = _NS_selunara._alpha(220 - i * 20)
            # Crescent trail dot.
            _NS_selunara._aacircle(surface,
                                   (*_NS_selunara.PALETTE["lunar_dark"], alpha),
                                   (px, py), max(1, 6 - i))
            _NS_selunara._aacircle(surface,
                                   (*_NS_selunara.PALETTE["lunar_mid"], alpha),
                                   (px, py), max(1, 4 - i))
            _NS_selunara._aacircle(surface,
                                   (*_NS_selunara.PALETTE["lunar_light"], alpha),
                                   (px, py), max(1, 2 - i // 2))
        # Bigger glaive with glow halo.
        for r in range(14, 4, -2):
            alpha = _NS_selunara._alpha(80 * (14 - r) / 14)
            _NS_selunara._aacircle(surface,
                                   (*_NS_selunara.PALETTE["lunar_light"], alpha),
                                   (bx, by), r)
        # Draw big spinning glaive (2x normal size).
        _NS_selunara._draw_flying_glaive_big(surface, bx, by, rot,
                                              boss.direction)
        # Impact at target (peak of arc).
        if 0.45 < t < 0.55:
            st = abs(t - 0.5) / 0.05
            radius = int(15 * (1 - st))
            alpha = _NS_selunara._alpha(240 * (1 - st))
            _NS_selunara._aacircle(surface, (*_NS_selunara.PALETTE["lunar_dark"], alpha),
                                   (tx, ty), radius + 2, 2)
            _NS_selunara._aacircle(surface, (*_NS_selunara.PALETTE["lunar_light"], alpha),
                                   (tx, ty), radius, 1)
            _NS_selunara._aacircle(surface, (*_NS_selunara.PALETTE["lunar_shine"], alpha),
                                   (tx, ty), max(1, radius // 2))
            for i in range(8):
                angle_s = i * math.pi / 4
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius)
                pygame.draw.rect(surface,
                                 (*_NS_selunara.PALETTE["lunar_shine"], alpha),
                                 (ex, ey, 2, 2))
    def _draw_flying_glaive_big(surface, cx, cy, rot, facing):
        """Bigger spinning crescent glaive for W skill."""
        outer_pts = []
        inner_pts = []
        for i in range(11):
            t = i / 10
            angle = math.pi * 0.15 + t * math.pi * 1.0 + rot
            ox = cx + int(math.cos(angle) * 10)
            oy = cy + int(math.sin(angle) * 10)
            outer_pts.append((ox, oy))
            ix = cx + int(math.cos(angle) * 5)
            iy = cy + int(math.sin(angle) * 5)
            inner_pts.append((ix, iy))
        blade_pts = outer_pts + list(reversed(inner_pts))
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 1) for p in blade_pts])
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["steel_dark"], blade_pts)
        _NS_selunara._poly(surface, _NS_selunara.PALETTE["steel_mid"],
                           [(p[0], p[1]) for p in outer_pts] +
                           list(reversed([(p[0], p[1]) for p in inner_pts])))
        # Edge highlights.
        for p in outer_pts:
            pygame.draw.rect(surface, _NS_selunara.PALETTE["steel_light"], (p[0], p[1], 1, 1))
        # Lunar glow overlay along blade.
        for p in outer_pts[::2]:
            pygame.draw.rect(surface, _NS_selunara.PALETTE["lunar_light"], (p[0], p[1], 1, 1))
        # Center core.
        _NS_selunara._aacircle(surface, _NS_selunara.PALETTE["lunar_darkest"], (cx, cy), 4)
        _NS_selunara._aacircle(surface, _NS_selunara.PALETTE["lunar_mid"], (cx, cy), 3)
        _NS_selunara._aacircle(surface, _NS_selunara.PALETTE["lunar_light"], (cx, cy), 2)
        _NS_selunara._aacircle(surface, _NS_selunara.PALETTE["lunar_shine"], (cx, cy), 1)
        pygame.draw.rect(surface, _NS_selunara.PALETTE["white"], (cx, cy, 1, 1))
    # ============================================================
    # SKILL E: LUNAR SHROUD (defensive shield around boss)
    # ============================================================
    def _draw_lunar_shroud_bubble(surface, boss, x, y, timer, pulse):
        """Protective bubble of lunar energy."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        breath = math.sin(pulse * 2) * 3
        r = 60 + int(breath)
        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)
        # Ring layers.
        for i, (thickness, alpha_val) in enumerate([
            (3, 120), (2, 160), (1, 200),
        ]):
            _NS_selunara._aacircle(bubble,
                                   (*_NS_selunara.PALETTE["lunar_dark"], alpha_val),
                                   center, r - i, thickness)
            _NS_selunara._aacircle(bubble,
                                   (*_NS_selunara.PALETTE["lunar_mid"], alpha_val),
                                   center, r - i - 1, 1)
        # Rotating sparkles.
        for i in range(24):
            angle = pulse * 1.5 + i * math.pi / 12
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            pygame.draw.rect(bubble, _NS_selunara.PALETTE["lunar_light"], (sx, sy, 2, 2))
            pygame.draw.rect(bubble, _NS_selunara.PALETTE["lunar_shine"], (sx, sy, 1, 1))
        # Small stars inside.
        for i in range(10):
            angle = pulse * 0.5 + i * math.pi / 5
            inner_r = r - 12
            bx = center[0] + int(math.cos(angle) * inner_r)
            by = center[1] + int(math.sin(angle) * inner_r * 0.7)
            _NS_selunara._aacircle(bubble, _NS_selunara.PALETTE["lunar_mid"], (bx, by), 2)
            pygame.draw.rect(bubble, _NS_selunara.PALETTE["lunar_shine"], (bx, by, 1, 1))
        surface.blit(bubble, (x - r - 10, y - r - 10))
        # Energy tendrils outward.
        for i in range(8):
            angle = pulse * 0.8 + i * math.pi / 4
            end_x = x + int(math.cos(angle) * (r + 10))
            end_y = y + int(math.sin(angle) * (r + 10))
            alpha = _NS_selunara._alpha(150 + math.sin(pulse * 3 + i) * 40)
            pygame.draw.line(surface, (*_NS_selunara.PALETTE["lunar_light"], alpha),
                             (x + int(math.cos(angle) * r),
                              y + int(math.sin(angle) * r)),
                             (end_x, end_y), 1)
            pygame.draw.rect(surface, _NS_selunara.PALETTE["lunar_shine"], (end_x, end_y, 1, 1))
    # ============================================================
    # SKILL R: ECLIPSE (multiple beams from sky)
    # ============================================================
    def _draw_eclipse_ground(surface, boss, x, y, timer, phase):
        """Large ground circle showing eclipse area."""
        tx, ty = _NS_selunara._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Growing circle.
        max_r = 70
        if progress < 0.25:
            t = progress / 0.25
            r = int(max_r * t)
        else:
            r = max_r
        alpha = _NS_selunara._alpha(200)
        pygame.draw.ellipse(surface, (*_NS_selunara.PALETTE["lunar_darkest"], alpha),
                            (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
        pygame.draw.ellipse(surface, (*_NS_selunara.PALETTE["lunar_dark"], alpha),
                            (tx - r + 4, ty - r // 3 + 3,
                             r * 2 - 8, r * 2 // 3 - 6), 2)
        pygame.draw.ellipse(surface, (*_NS_selunara.PALETTE["lunar_mid"], 150),
                            (tx - r + 10, ty - r // 3 + 6,
                             r * 2 - 20, r * 2 // 3 - 12), 1)
        # Runes around circle.
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            rx = tx + int(math.cos(angle) * r)
            ry = ty + int(math.sin(angle) * r * 0.4)
            pygame.draw.rect(surface, _NS_selunara.PALETTE["lunar_shine"], (rx, ry, 2, 2))
    def _draw_eclipse_beams(surface, boss, x, y, timer, phase):
        """Multiple beams crashing down from sky within eclipse area."""
        tx, ty = _NS_selunara._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Store beam positions in boss state (persistent).
        if not hasattr(boss, "_sel_eclipse_beams") or progress > 0.98:
            boss._sel_eclipse_beams = []
            for _ in range(8):
                angle = (hash(str(_)) % 628) / 100.0
                dist = 20 + (hash(str(_ + 100)) % 40)
                bx = tx + int(math.cos(angle) * dist)
                by = ty + int(math.sin(angle) * dist * 0.4)
                # Time offset for staggered impacts.
                t_offset = 0.2 + (hash(str(_ + 200)) % 30) / 100.0
                boss._sel_eclipse_beams.append((bx, by, t_offset))
        if progress < 0.15:
            # Wind-up: just ground circle showing.
            return
        # Draw each beam based on its timing.
        for bx, by, t_offset in boss._sel_eclipse_beams:
            beam_progress = (progress - 0.15) / 0.75
            beam_local_t = beam_progress - t_offset
            if beam_local_t < 0 or beam_local_t > 0.5:
                continue
            local_t = beam_local_t / 0.5  # 0 → 1 over 30% duration
            intensity = math.sin(local_t * math.pi)
            # Beam from top of screen.
            beam_top_y = max(0, by - 250)
            # Multi-layer beam.
            for width, color in [
                (10, _NS_selunara.PALETTE["lunar_darkest"]),
                (7, _NS_selunara.PALETTE["lunar_dark"]),
                (5, _NS_selunara.PALETTE["lunar_mid"]),
                (3, _NS_selunara.PALETTE["lunar_light"]),
                (1, _NS_selunara.PALETTE["moon_shine"]),
            ]:
                alpha = _NS_selunara._alpha(255 * intensity)
                if alpha > 0:
                    pygame.draw.rect(surface, (*color, alpha),
                                     (bx - width // 2, beam_top_y,
                                      width, by - beam_top_y))
            # Bright core line.
            pygame.draw.line(surface, _NS_selunara.PALETTE["white"],
                             (bx, beam_top_y), (bx, by), 1)
            # Sparkles rising.
            for i in range(8):
                s_t = (phase * 2 + i * 0.13) % 1.0
                sy_pos = by - int(s_t * (by - beam_top_y))
                sx_pos = bx + int(math.sin(phase * 5 + i) * 4)
                alpha = _NS_selunara._alpha(240 * intensity * (1 - s_t * 0.4))
                pygame.draw.rect(surface, (*_NS_selunara.PALETTE["lunar_shine"], alpha),
                                 (sx_pos, sy_pos, 2, 2))
            # Impact burst at ground.
            impact_r = int(10 + local_t * 15)
            impact_alpha = _NS_selunara._alpha(240 * intensity)
            _NS_selunara._aacircle(surface,
                                   (*_NS_selunara.PALETTE["lunar_darkest"], impact_alpha),
                                   (bx, by), impact_r + 2, 2)
            _NS_selunara._aacircle(surface,
                                   (*_NS_selunara.PALETTE["lunar_dark"], impact_alpha),
                                   (bx, by), impact_r, 2)
            _NS_selunara._aacircle(surface,
                                   (*_NS_selunara.PALETTE["lunar_mid"], impact_alpha),
                                   (bx, by), max(1, impact_r - 4), 1)
            _NS_selunara._aacircle(surface,
                                   (*_NS_selunara.PALETTE["lunar_shine"], impact_alpha),
                                   (bx, by), max(1, impact_r // 3))
            for i in range(8):
                angle_s = i * math.pi / 4
                ex = bx + int(math.cos(angle_s) * impact_r)
                ey = by + int(math.sin(angle_s) * impact_r * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_selunara.PALETTE["lunar_shine"], impact_alpha),
                                 (ex, ey, 2, 2))



# ====================================================================
# VESSYRA (GORGON QUEEN) - Mini Boss
# ====================================================================

class _NS_vessyra:
    """Namespace vessyra - Gorgon Queen mini boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Skin (pale green — gorgon)
        "skin_darkest": (20, 40, 30),
        "skin_dark": (55, 100, 70),
        "skin_mid": (110, 165, 120),
        "skin_light": (170, 215, 175),
        "skin_shine": (215, 245, 215),
        # Serpent scales (body — dark forest green)
        "scale_darkest": (8, 25, 18),
        "scale_dark": (25, 65, 40),
        "scale_mid": (55, 115, 65),
        "scale_light": (105, 175, 105),
        "scale_shine": (165, 220, 155),
        # Belly scales (yellow-tan underside)
        "belly_darkest": (35, 25, 8),
        "belly_dark": (95, 75, 30),
        "belly_mid": (170, 140, 65),
        "belly_light": (225, 200, 120),
        # Snake hair (green, similar to skin but darker)
        "snake_darkest": (15, 30, 15),
        "snake_dark": (35, 75, 40),
        "snake_mid": (75, 135, 80),
        "snake_light": (130, 195, 130),
        # Top/cloth (dark forest green with gold trim)
        "cloth_darkest": (12, 25, 15),
        "cloth_dark": (30, 55, 35),
        "cloth_mid": (60, 90, 60),
        "cloth_light": (105, 145, 100),
        # Dark accent (near-black, purple-tinted)
        "accent_dark": (25, 15, 30),
        "accent_mid": (55, 35, 65),
        # Gold ornaments (rich)
        "gold_darkest": (60, 40, 5),
        "gold_dark": (115, 80, 15),
        "gold_mid": (215, 165, 40),
        "gold_light": (250, 220, 100),
        "gold_shine": (255, 245, 175),
        # TOXIC/MAGIC GREEN (arrows, aura — signature)
        "magic_darkest": (10, 30, 5),
        "magic_dark": (25, 90, 20),
        "magic_mid": (85, 195, 55),
        "magic_light": (170, 245, 120),
        "magic_hot": (220, 255, 180),
        "magic_shine": (250, 255, 220),
        # Red eyes (fierce)
        "eye_dark": (55, 5, 10),
        "eye_mid": (200, 30, 30),
        "eye_hot": (255, 120, 100),
        "eye_shine": (255, 210, 190),
        # Snake eyes (yellow)
        "snake_eye_dark": (95, 65, 10),
        "snake_eye_mid": (245, 210, 30),
        "snake_eye_hot": (255, 250, 150),
        # Stone (Stone Gaze effect)
        "stone_dark": (55, 55, 60),
        "stone_mid": (110, 108, 115),
        "stone_light": (170, 170, 180),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vessyra._clamp(color)
        if _NS_vessyra.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_vessyra._clamp(color)
        if _NS_vessyra.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_vessyra._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 240 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_vessyra(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_vessyra._detect_moving(boss)
        _NS_vessyra._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_vy_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_vessyra._draw_gorgon_aura(surface, x, y, pulse)
        _NS_vessyra._draw_ground_ring(surface, x, y + 54, pulse, active_skill)
        # Skill ground FX
        if active_skill == "e":  # Stone Gaze
            _NS_vessyra._draw_stone_ground(surface, boss, x, y, skill_timer, pulse)
        # Body
        if attacking:
            _NS_vessyra._draw_attack(surface, boss, x, y)
        elif moving:
            _NS_vessyra._draw_walk(surface, boss, x, y)
        else:
            _NS_vessyra._draw_idle(surface, boss, x, y)
        # Mana Shield (over body)
        if active_skill == "r":
            _NS_vessyra._draw_mana_shield(surface, boss, x, y, skill_timer, pulse)
        # Foreground skill FX
        if active_skill == "q":
            _NS_vessyra._draw_split_shot(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vessyra._draw_mystic_snake(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_vessyra._draw_stone_gaze_beam(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vy_previous_timer", 0))
        active = bool(getattr(boss, "_vy_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._vy_attack_active = True
            boss._vy_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._vy_attack_frame = int(getattr(boss, "_vy_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._vy_attack_active = False
            boss._vy_attack_frame = 0
            active = False
        boss._vy_previous_timer = timer
        boss._vy_attack_progress = (
            min(1.0, getattr(boss, "_vy_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_vy_last_x"):
            boss._vy_last_x = boss.x
            boss._vy_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vy_last_x)
        dy = abs(boss.y - boss._vy_last_y)
        boss._vy_last_x = boss.x
        boss._vy_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS (floating serpentine)
    # ============================================================
    def _draw_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 3)
        _NS_vessyra._draw_shadow(surface, x, y + 55)
        _NS_vessyra._draw_body(surface, x, y + bob, boss.direction, boss.pulse,
                                "idle", 0)
    def _draw_walk(surface, boss, x, y):
        # Serpentine floating slither
        phase = boss.pulse * 1.6
        float_bob = int(math.sin(phase * 0.9) * 4)
        sway = int(math.sin(phase * 0.6) * 3)
        _NS_vessyra._draw_shadow(surface, x + sway, y + 55, faded=True)
        _NS_vessyra._draw_snake_trail(surface, x + sway, y + 44, phase,
                                       boss.direction)
        _NS_vessyra._draw_body(surface, x + sway, y + float_bob - 2,
                                boss.direction, phase, "walk", 0)
    def _draw_attack(surface, boss, x, y):
        progress = getattr(boss, "_vy_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Bow shot: draw back → release → recovery
        if progress < 0.4:
            # Draw arrow back
            t = progress / 0.4
            lunge = -int(t * 2) * boss.direction
            lift = int(t * 2)
        elif progress < 0.55:
            # Release
            t = (progress - 0.4) / 0.15
            lunge = int((-2 + t * 6)) * boss.direction
            lift = int(2 - t * 3)
        else:
            # Recovery
            t = (progress - 0.55) / 0.45
            lunge = int(4 * (1 - t)) * boss.direction
            lift = int(-1 + t)
        bob = int(math.sin(boss.pulse * 0.5) * 2)
        _NS_vessyra._draw_shadow(surface, x + lunge, y + 55)
        _NS_vessyra._draw_body(surface, x + lunge, y - lift + bob,
                                boss.direction, boss.pulse, "attack", progress)
        _NS_vessyra._draw_basic_arrow(surface, boss, x + lunge, y - lift + bob,
                                       progress)
    # ============================================================
    # BODY (Gorgon with serpent tail)
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Layered: serpent tail (behind & bottom) → torso → snake hair (behind head)
        → rear arm → head → front arm + bow."""
        # SERPENT TAIL (bottom half — big coil)
        _NS_vessyra._draw_serpent_tail(surface, cx, cy + 14, facing, phase, action)
        # TORSO (upper humanoid half)
        _NS_vessyra._draw_torso(surface, cx, cy - 2, facing, phase, action)
        # SNAKE HAIR (many living snakes)
        _NS_vessyra._draw_snake_hair(surface, cx, cy - 18, facing, phase)
        # Rear arm (holds bow shaft)
        _NS_vessyra._draw_rear_arm(surface, cx, cy - 2, facing, phase, action,
                                    attack_progress)
        # Head + face + crown
        _NS_vessyra._draw_head(surface, cx + facing * 1, cy - 16, facing,
                                phase, action)
        # Crown/tiara
        _NS_vessyra._draw_crown(surface, cx + facing * 1, cy - 22, facing, phase)
        # Front arm + BOW (main feature)
        _NS_vessyra._draw_bow_arm(surface, cx, cy - 2, facing, phase, action,
                                   attack_progress)
    def _draw_serpent_tail(surface, cx, cy, facing, phase, action):
        """Big serpent tail coiling below."""
        # Slithering wave animation
        wave = math.sin(phase * 1.0) * 3
        wave2 = math.sin(phase * 0.7 + 1) * 2
        slither = math.sin(phase * 1.5) * 2 if action == "walk" else 0
        # Main body of the tail (S-curve/coil shape)
        # Front bulge (where it connects to torso)
        front_pts = [
            (cx - 12, cy - 8),
            (cx + 12, cy - 8),
            (cx + 15, cy - 4),
            (cx + 16, cy + 2),
            (cx + 13, cy + 8),
            (cx + 5, cy + 12),
            (cx - 5, cy + 12),
            (cx - 13, cy + 8),
            (cx - 16, cy + 2),
            (cx - 15, cy - 4),
        ]
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["shadow_deep"],
                          [(p[0] + 2, p[1] + 3) for p in front_pts])
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["scale_darkest"],
                          front_pts)
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["scale_dark"], [
            (cx - 11, cy - 7), (cx + 11, cy - 7),
            (cx + 14, cy - 3), (cx + 15, cy + 2),
            (cx + 12, cy + 7), (cx + 4, cy + 11),
            (cx - 4, cy + 11), (cx - 12, cy + 7),
            (cx - 15, cy + 2), (cx - 14, cy - 3),
        ])
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["scale_mid"], [
            (cx - 8, cy - 5), (cx + 8, cy - 5),
            (cx + 12, cy - 2), (cx + 13, cy + 2),
            (cx + 10, cy + 6), (cx + 3, cy + 9),
            (cx - 3, cy + 9), (cx - 10, cy + 6),
            (cx - 13, cy + 2), (cx - 12, cy - 2),
        ])
        # Highlight top
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["scale_light"], [
            (cx - 5, cy - 3),
            (cx + 5, cy - 3),
            (cx + 8, cy),
            (cx + 5, cy + 3),
            (cx - 5, cy + 3),
            (cx - 8, cy),
        ])
        # Belly (yellow-tan underside — visible bottom front)
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["belly_dark"], [
            (cx - 10, cy + 8),
            (cx + 10, cy + 8),
            (cx + 4, cy + 11),
            (cx - 4, cy + 11),
        ])
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["belly_mid"], [
            (cx - 7, cy + 9),
            (cx + 7, cy + 9),
            (cx + 2, cy + 10),
            (cx - 2, cy + 10),
        ])
        # Belly segment stripes
        for stripe_x in (-6, -2, 2, 6):
            pygame.draw.line(surface, _NS_vessyra.PALETTE["belly_darkest"],
                             (cx + stripe_x - 1, cy + 9),
                             (cx + stripe_x + 1, cy + 9), 1)
        # Scale texture on back
        for row in range(3):
            y_row = cy - 6 + row * 3
            for i, dx in enumerate((-10, -6, -2, 2, 6, 10)):
                offset_x = (row % 2) * 2 - 1
                pygame.draw.line(surface, _NS_vessyra.PALETTE["scale_darkest"],
                                 (cx + dx + offset_x - 1, y_row),
                                 (cx + dx + offset_x, y_row - 1), 1)
                pygame.draw.line(surface, _NS_vessyra.PALETTE["scale_darkest"],
                                 (cx + dx + offset_x, y_row - 1),
                                 (cx + dx + offset_x + 1, y_row), 1)
                pygame.draw.rect(surface, _NS_vessyra.PALETTE["scale_edge"] if False else _NS_vessyra.PALETTE["scale_light"],
                                 (cx + dx + offset_x, y_row - 1, 1, 1))
        # LOWER TAIL — long tapering coil going down-back
        back = -facing
        num_segments = 10
        prev_x = cx + back * 8
        prev_y = cy + 8
        for seg_i in range(num_segments):
            t = seg_i / num_segments
            # S-curve trajectory
            seg_wave = math.sin(phase * 1.0 + t * math.pi * 2) * (5 + t * 4)
            seg_x = int(prev_x + back * (3 + t * 2))
            seg_y = int(cy + 10 + t * 20 + seg_wave)
            thickness = max(2, int(14 - t * 12))
            # Shadow
            _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["shadow_deep"],
                                 (prev_x + 2, prev_y + 2),
                                 (seg_x + 2, seg_y + 2), thickness + 1)
            _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["scale_darkest"],
                                 (prev_x, prev_y), (seg_x, seg_y), thickness)
            _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["scale_dark"],
                                 (prev_x, prev_y), (seg_x, seg_y),
                                 max(1, thickness - 2))
            _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["scale_mid"],
                                 (prev_x, prev_y - 1), (seg_x, seg_y - 1),
                                 max(1, thickness - 4))
            # Belly bottom
            _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["belly_dark"],
                                 (prev_x, prev_y + 1), (seg_x, seg_y + 1),
                                 max(1, thickness - 4))
            _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["belly_mid"],
                                 (prev_x, prev_y + 2), (seg_x, seg_y + 2),
                                 max(1, thickness - 6))
            prev_x = seg_x
            prev_y = seg_y
        # Tail tip spike
        if num_segments > 0:
            tip_angle = math.atan2(seg_y - (prev_y if seg_i == 0 else seg_y),
                                    seg_x - prev_x)
            tail_tip_x = seg_x + back * 4
            tail_tip_y = seg_y + 2
            _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["scale_darkest"], [
                (tail_tip_x, tail_tip_y),
                (seg_x, seg_y - 2),
                (seg_x, seg_y + 2),
            ])
            _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["scale_mid"], [
                (tail_tip_x, tail_tip_y),
                (seg_x, seg_y - 1),
                (seg_x, seg_y + 1),
            ])
    def _draw_torso(surface, cx, cy, facing, phase, action):
        """Female gorgon upper torso — green skin + dark cloth top."""
        breath = math.sin(phase * 0.7) * 1
        # Torso shape (feminine)
        torso = [
            (cx - 6, cy - 6),
            (cx + 6, cy - 6),
            (cx + 8, cy - 2),
            (cx + 8, cy + 4),
            (cx + 6, cy + 10),
            (cx - 6, cy + 10),
            (cx - 8, cy + 4),
            (cx - 8, cy - 2),
        ]
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in torso])
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["skin_darkest"], torso)
        # Skin base (green)
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["skin_dark"], [
            (cx - 5, cy - 5), (cx + 5, cy - 5),
            (cx + 7, cy - 2), (cx + 7, cy + 3),
            (cx + 5, cy + 9), (cx - 5, cy + 9),
            (cx - 7, cy + 3), (cx - 7, cy - 2),
        ])
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["skin_mid"], [
            (cx - 4, cy - 3), (cx + 4, cy - 3),
            (cx + 6, cy), (cx + 5, cy + 4),
            (cx + 3, cy + 7), (cx - 3, cy + 7),
            (cx - 5, cy + 4), (cx - 6, cy),
        ])
        # Highlight
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["skin_light"], [
            (cx + facing, cy - 3),
            (cx + 3 * facing, cy - 2),
            (cx + 3 * facing, cy + 1),
            (cx + facing, cy + 2),
        ])
        # DARK CLOTH TOP (halter/bra style with gold trim)
        top_pts = [
            (cx - 6, cy - 5),
            (cx + 6, cy - 5),
            (cx + 8, cy - 2),
            (cx + 6, cy + 1),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
            (cx - 6, cy + 1),
            (cx - 8, cy - 2),
        ]
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["cloth_darkest"], top_pts)
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["cloth_dark"], [
            (cx - 5, cy - 4), (cx + 5, cy - 4),
            (cx + 7, cy - 2), (cx + 5, cy),
            (cx + 2, cy + 2), (cx - 2, cy + 2),
            (cx - 5, cy), (cx - 7, cy - 2),
        ])
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["cloth_mid"], [
            (cx - 3, cy - 3), (cx + 3, cy - 3),
            (cx + 5, cy - 1), (cx + 3, cy + 1),
            (cx - 3, cy + 1), (cx - 5, cy - 1),
        ])
        # Gold trim
        pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_dark"],
                         (cx - 6, cy - 5), (cx + 6, cy - 5), 1)
        pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_mid"],
                         (cx - 4, cy - 5), (cx + 4, cy - 5), 1)
        # Bottom gold trim
        pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_dark"],
                         (cx - 6, cy + 1), (cx + 6, cy + 1), 1)
        pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_mid"],
                         (cx - 4, cy + 2), (cx + 4, cy + 2), 1)
        # Central gold pendant (with green gem)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        pend_x = cx
        pend_y = cy - 2
        _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["gold_darkest"],
                               (pend_x, pend_y), 3)
        _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["gold_dark"],
                               (pend_x, pend_y), 2)
        for r in range(2, 0, -1):
            a = _NS_vessyra._alpha(200 * (2 - r) / 2 * pulse)
            _NS_vessyra._aacircle(surface,
                                   (*_NS_vessyra.PALETTE["magic_mid"], a),
                                   (pend_x, pend_y), r)
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["magic_hot"],
                         (pend_x, pend_y, 1, 1))
        # Shoulder ornaments (gold epaulettes)
        for side in (-1, 1):
            sp_x = cx + side * 7
            sp_y = cy - 5
            # Gold shoulder cap
            _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["gold_darkest"],
                                   (sp_x, sp_y), 3)
            _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["gold_dark"],
                                   (sp_x, sp_y), 2)
            _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["gold_mid"],
                                   (sp_x, sp_y), 1)
            pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_shine"],
                             (sp_x, sp_y - 1, 1, 1))
        # Waist sash (gold belt/wrap between torso and tail)
        sash_y = cy + 8
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_darkest"],
                         (cx - 8, sash_y, 16, 3))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_dark"],
                         (cx - 8, sash_y, 16, 2))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_mid"],
                         (cx - 8, sash_y, 16, 1))
        # Central buckle
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_darkest"],
                         (cx - 3, sash_y - 1, 6, 4))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_dark"],
                         (cx - 2, sash_y, 5, 3))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_mid"],
                         (cx - 1, sash_y, 3, 2))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["magic_mid"],
                         (cx, sash_y + 1, 1, 1))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["magic_hot"],
                         (cx, sash_y + 1, 1, 1))
        # Hanging cloth flaps below sash (like Medusa's front skirt piece)
        # Left flap (dark purple)
        flap_wave = int(math.sin(phase * 0.6) * 1)
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["accent_dark"], [
            (cx - 5, cy + 11),
            (cx - 3, cy + 11),
            (cx - 2, cy + 16),
            (cx - 4 + flap_wave, cy + 18),
            (cx - 6, cy + 15),
        ])
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["accent_mid"], [
            (cx - 4, cy + 12),
            (cx - 3, cy + 15),
            (cx - 4 + flap_wave, cy + 17),
        ])
        # Right flap
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["accent_dark"], [
            (cx + 3, cy + 11),
            (cx + 5, cy + 11),
            (cx + 6, cy + 15),
            (cx + 4 - flap_wave, cy + 18),
            (cx + 2, cy + 16),
        ])
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["accent_mid"], [
            (cx + 3, cy + 12),
            (cx + 4, cy + 15),
            (cx + 4 - flap_wave, cy + 17),
        ])
    def _draw_snake_hair(surface, cx, cy, facing, phase):
        """LIVING SNAKE HAIR — many writhing snakes coming out of head."""
        # Many snakes in different directions
        # Each snake is a curved segment ending in a small snake head
        num_snakes = 10
        snake_configs = [
            # (base_x_off, base_y_off, base_angle, wave_speed, length, size_mult)
            (-6, 2, math.pi * 0.6, 1.5, 8, 1.0),
            (-4, -1, math.pi * 0.75, 1.3, 10, 1.1),
            (-2, -3, math.pi * 0.85, 1.6, 9, 0.9),
            (0, -4, math.pi * 0.95, 1.4, 11, 1.2),
            (2, -3, math.pi * 1.05, 1.7, 9, 0.9),
            (4, -1, math.pi * 1.15, 1.3, 10, 1.1),
            (6, 2, math.pi * 1.3, 1.5, 8, 1.0),
            (-5, 4, math.pi * 0.5, 1.2, 7, 0.8),
            (5, 4, math.pi * 1.4, 1.2, 7, 0.8),
            (0, -5, math.pi * 0.95, 1.8, 12, 1.15),
        ]
        for snake_i, (base_x_off, base_y_off, base_angle, wave_speed, length,
                      size_mult) in enumerate(snake_configs):
            base_x = cx + base_x_off
            base_y = cy + base_y_off
            # Wave animation
            wave_offset = math.sin(phase * wave_speed + snake_i * 0.5) * 2
            # Snake segments (curved)
            num_segs = 6
            prev_x = base_x
            prev_y = base_y
            for seg_i in range(1, num_segs + 1):
                t = seg_i / num_segs
                seg_angle = base_angle + math.sin(phase * wave_speed + snake_i + t * 2) * 0.3
                seg_x = int(base_x + math.cos(seg_angle) * (length * t) + wave_offset * t)
                seg_y = int(base_y - math.sin(seg_angle) * (length * t))
                thickness = max(1, int((4 - seg_i * 0.5) * size_mult))
                # Shadow
                _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["shadow_deep"],
                                     (prev_x + 1, prev_y + 1),
                                     (seg_x + 1, seg_y + 1), thickness + 1)
                _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["snake_darkest"],
                                     (prev_x, prev_y), (seg_x, seg_y),
                                     thickness)
                _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["snake_dark"],
                                     (prev_x, prev_y), (seg_x, seg_y),
                                     max(1, thickness - 1))
                if thickness > 2:
                    _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["snake_mid"],
                                         (prev_x, prev_y - 1),
                                         (seg_x, seg_y - 1),
                                         max(1, thickness - 2))
                prev_x = seg_x
                prev_y = seg_y
            # SNAKE HEAD at end (small triangular head)
            head_size = max(2, int(3 * size_mult))
            head_x = prev_x
            head_y = prev_y
            # Head shape (small triangle-ish)
            _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["shadow_deep"],
                                   (head_x + 1, head_y + 1), head_size)
            _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["snake_darkest"],
                                   (head_x, head_y), head_size)
            _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["snake_dark"],
                                   (head_x, head_y), head_size - 1)
            _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["snake_mid"],
                                   (head_x, head_y - 1), max(1, head_size - 2))
            # Snake tiny eyes (yellow glow)
            eye_pulse = math.sin(phase * 3 + snake_i) * 0.4 + 0.6
            for eye_off in (-1, 1):
                ex = head_x + eye_off
                ey = head_y
                pygame.draw.rect(surface, _NS_vessyra.PALETTE["snake_eye_dark"],
                                 (ex, ey, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_vessyra.PALETTE["snake_eye_hot"],
                                  _NS_vessyra._alpha(255 * eye_pulse)),
                                 (ex, ey, 1, 1))
            # Small forked tongue occasionally
            if int(phase * 3 + snake_i) % 4 == 0:
                pygame.draw.line(surface, _NS_vessyra.PALETTE["eye_mid"],
                                 (head_x, head_y + 1),
                                 (head_x, head_y + 3), 1)
    def _draw_rear_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Rear arm — holds bow shaft (offhand supports bow)."""
        back = -facing
        shoulder = (cx + back * 6, cy - 4)
        # Rear arm typically holds bow bottom
        if action == "attack":
            if attack_progress < 0.4:
                elbow_off_x = back * 2
                elbow_off_y = 3
            else:
                elbow_off_x = back * 2
                elbow_off_y = 3
        else:
            gesture = math.sin(phase * 0.6) * 1
            elbow_off_x = back * 2
            elbow_off_y = 3 + int(gesture)
        elbow = (shoulder[0] + elbow_off_x, shoulder[1] + elbow_off_y)
        hand = (elbow[0] + back * 1, elbow[1] + 5)
        # Upper arm (bare green skin)
        _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["shadow_deep"],
                             (shoulder[0] + 1, shoulder[1] + 1),
                             (elbow[0] + 1, elbow[1] + 1), 6)
        _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["skin_darkest"],
                             shoulder, elbow, 5)
        _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["skin_dark"],
                             shoulder, elbow, 4)
        _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["skin_mid"],
                             (shoulder[0], shoulder[1] - 1),
                             (elbow[0], elbow[1] - 1), 2)
        # Gold armband on upper arm
        arm_mid_x = int((shoulder[0] + elbow[0]) / 2)
        arm_mid_y = int((shoulder[1] + elbow[1]) / 2)
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_dark"],
                         (arm_mid_x - 2, arm_mid_y - 1, 5, 3))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_mid"],
                         (arm_mid_x - 2, arm_mid_y - 1, 5, 2))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_shine"],
                         (arm_mid_x, arm_mid_y - 1, 2, 1))
        # Forearm
        _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["shadow_deep"],
                             (elbow[0] + 1, elbow[1] + 1),
                             (hand[0] + 1, hand[1] + 1), 5)
        _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["skin_darkest"],
                             elbow, hand, 4)
        _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["skin_dark"],
                             elbow, hand, 3)
        # Gold bracelet at wrist
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_dark"],
                         (hand[0] - 2, hand[1] - 1, 4, 3))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_mid"],
                         (hand[0] - 2, hand[1] - 1, 4, 2))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_shine"],
                         (hand[0], hand[1] - 1, 1, 1))
        # Hand
        _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["skin_dark"], hand, 2)
        _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["skin_mid"], hand, 1)
    def _draw_head(surface, cx, cy, facing, phase, action):
        """Gorgon face — green skin, red eyes, elegant."""
        # Head shape (feminine oval)
        head = [
            (cx - 4, cy - 2),
            (cx - 5, cy - 5),
            (cx - 3, cy - 8),
            (cx, cy - 9),
            (cx + 3, cy - 8),
            (cx + 5, cy - 5),
            (cx + 5, cy - 1),
            (cx + 4, cy + 3),
            (cx + 2, cy + 5),
            (cx - 2, cy + 5),
            (cx - 4, cy + 3),
        ]
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["shadow_deep"],
                          [(p[0] + 1, p[1] + 2) for p in head])
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["skin_darkest"], head)
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["skin_dark"], [
            (cx - 3, cy - 2), (cx - 4, cy - 4),
            (cx - 2, cy - 7), (cx, cy - 8),
            (cx + 2, cy - 7), (cx + 4, cy - 4),
            (cx + 4, cy - 1), (cx + 3, cy + 2),
            (cx + 1, cy + 4), (cx - 1, cy + 4), (cx - 3, cy + 2),
        ])
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["skin_mid"], [
            (cx - 3, cy - 3), (cx - 2, cy - 6),
            (cx, cy - 7), (cx + 2, cy - 6),
            (cx + 3, cy - 3),
        ])
        # Highlight
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["skin_light"], [
            (cx + facing, cy - 5),
            (cx + 3 * facing, cy - 4),
            (cx + 3 * facing, cy - 2),
            (cx + facing, cy - 2),
        ])
        # Pointed elf-like ears (gorgon)
        for side in (-1, 1):
            ear_x = cx + side * 5
            ear_y = cy - 3
            # Ear extends outward as pointed triangle
            _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["skin_dark"], [
                (ear_x, ear_y - 1),
                (ear_x + side * 2, ear_y - 3),
                (ear_x + side, ear_y + 1),
            ])
            _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["skin_mid"], [
                (ear_x, ear_y),
                (ear_x + side, ear_y - 2),
                (ear_x + side, ear_y),
            ])
            # Gold earring
            pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_mid"],
                             (ear_x + side * 2, ear_y + 1, 1, 1))
            pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_shine"],
                             (ear_x + side * 2, ear_y + 1, 1, 1))
        # RED GLOWING EYES (fierce gorgon gaze)
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Furrowed brow (intense stare)
        pygame.draw.line(surface, _NS_vessyra.PALETTE["scale_darkest"],
                         (cx - 4, cy - 6), (cx - 1, cy - 5), 1)
        pygame.draw.line(surface, _NS_vessyra.PALETTE["scale_darkest"],
                         (cx + 4, cy - 6), (cx + 1, cy - 5), 1)
        # Eye sockets
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["shadow_deep"],
                         (cx - 3, cy - 5, 2, 2))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["shadow_deep"],
                         (cx + 1, cy - 5, 2, 2))
        # Whites (or pale)
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["skin_shine"],
                         (cx - 3, cy - 5, 2, 2))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["skin_shine"],
                         (cx + 1, cy - 5, 2, 2))
        # Red pupils
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["eye_dark"],
                         (cx - 2, cy - 5, 1, 2))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["eye_dark"],
                         (cx + 2, cy - 5, 1, 2))
        # Red glow halo
        for r in range(4, 0, -1):
            a = _NS_vessyra._alpha(120 * (4 - r) / 4 * eye_pulse)
            _NS_vessyra._aacircle(surface,
                                   (*_NS_vessyra.PALETTE["eye_mid"], a),
                                   (cx - 2, cy - 4), r)
            _NS_vessyra._aacircle(surface,
                                   (*_NS_vessyra.PALETTE["eye_mid"], a),
                                   (cx + 2, cy - 4), r)
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["eye_hot"],
                         (cx - 2, cy - 4, 1, 1))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["eye_hot"],
                         (cx + 2, cy - 4, 1, 1))
        # Bright glint
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["eye_shine"],
                         (cx - 2, cy - 4, 1, 1))
        # Nose (small elegant)
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["skin_darkest"],
                         (cx, cy - 2, 1, 2))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["skin_light"],
                         (cx + facing, cy - 2, 1, 1))
        # Lips (dark green — sinister)
        pygame.draw.line(surface, _NS_vessyra.PALETTE["scale_darkest"],
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["magic_dark"],
                         (cx, cy + 2, 1, 1))
    def _draw_crown(surface, cx, cy, facing, phase):
        """Ornate gold crown with green gem — Medusa signature."""
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        # Base band
        pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_darkest"],
                         (cx - 6, cy + 5), (cx + 6, cy + 5), 2)
        pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_dark"],
                         (cx - 6, cy + 5), (cx + 6, cy + 5), 1)
        pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_mid"],
                         (cx - 5, cy + 5), (cx + 5, cy + 5), 1)
        pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_shine"],
                         (cx - 2, cy + 5), (cx + 2, cy + 5), 1)
        # Central FRONT SPIKE (tall) with green gem
        spike_wave = int(math.sin(phase * 0.5) * 1)
        # Spike
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["shadow_deep"], [
            (cx + 1, cy - 3 + spike_wave),
            (cx - 2, cy + 5),
            (cx + 3, cy + 5),
        ])
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["gold_darkest"], [
            (cx, cy - 3 + spike_wave),
            (cx - 2, cy + 5),
            (cx + 2, cy + 5),
        ])
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["gold_dark"], [
            (cx, cy - 3 + spike_wave),
            (cx - 1, cy + 4),
            (cx + 1, cy + 4),
        ])
        _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["gold_mid"], [
            (cx, cy - 3 + spike_wave),
            (cx, cy + 3),
            (cx + 1, cy + 3),
        ])
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_shine"],
                         (cx, cy - 2 + spike_wave, 1, 1))
        # Central gem (green — Medusa signature)
        gem_x = cx
        gem_y = cy + 2
        for r in range(4, 0, -1):
            a = _NS_vessyra._alpha(200 * (4 - r) / 4 * pulse)
            _NS_vessyra._aacircle(surface,
                                   (*_NS_vessyra.PALETTE["magic_mid"], a),
                                   (gem_x, gem_y), r)
        _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["magic_darkest"],
                               (gem_x, gem_y), 2)
        _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["magic_mid"],
                               (gem_x, gem_y), 1)
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["magic_hot"],
                         (gem_x, gem_y, 1, 1))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["magic_shine"],
                         (gem_x, gem_y, 1, 1))
        # Side spikes (smaller)
        for i, (spike_x_off, tip_off_y) in enumerate([(-4, -1), (-2, -2),
                                                        (2, -2), (4, -1)]):
            spike_x = cx + spike_x_off
            spike_base_y = cy + 5
            spike_tip_y = cy + tip_off_y
            _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_tip_y + 1),
                (spike_x - 1, spike_base_y + 1),
                (spike_x + 2, spike_base_y + 1),
            ])
            _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["gold_dark"], [
                (spike_x, spike_tip_y),
                (spike_x - 1, spike_base_y),
                (spike_x + 1, spike_base_y),
            ])
            _NS_vessyra._poly(surface, _NS_vessyra.PALETTE["gold_mid"], [
                (spike_x, spike_tip_y),
                (spike_x, spike_base_y),
                (spike_x + 1, spike_base_y),
            ])
            pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_shine"],
                             (spike_x, spike_tip_y, 1, 1))
    def _draw_bow_arm(surface, cx, cy, facing, phase, action, attack_progress):
        """Front arm holding BOW."""
        shoulder = (cx + facing * 5, cy - 4)
        if action == "attack":
            if attack_progress < 0.4:
                # Draw arrow back — arm holds bow steady, pulls back
                t = attack_progress / 0.4
                elbow_off_x = facing * (4 + int(t * 2))
                elbow_off_y = int(-1 - t)
                hand_off_x = facing * (10 + int(t * 3))
                hand_off_y = int(-3 - t)
            elif attack_progress < 0.55:
                # Release
                t = (attack_progress - 0.4) / 0.15
                elbow_off_x = facing * (6 - int(t))
                elbow_off_y = int(-2 + t)
                hand_off_x = facing * (13 - int(t * 2))
                hand_off_y = int(-4 + t)
            else:
                # Recovery
                t = (attack_progress - 0.55) / 0.45
                elbow_off_x = facing * (5 - int(t))
                elbow_off_y = int(-1 + t)
                hand_off_x = facing * (11 - int(t * 3))
                hand_off_y = int(-3 + t * 2)
        else:
            sway = math.sin(phase * 0.5) * 1
            elbow_off_x = facing * 4
            elbow_off_y = int(-1 + sway)
            hand_off_x = facing * 10
            hand_off_y = int(-3 + sway)
        elbow = (shoulder[0] + elbow_off_x, shoulder[1] + elbow_off_y)
        hand = (shoulder[0] + hand_off_x, shoulder[1] + hand_off_y)
        # Upper arm (bare green skin)
        _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["shadow_deep"],
                             (shoulder[0] + 1, shoulder[1] + 1),
                             (elbow[0] + 1, elbow[1] + 1), 6)
        _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["skin_darkest"],
                             shoulder, elbow, 5)
        _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["skin_dark"],
                             shoulder, elbow, 4)
        _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["skin_mid"],
                             (shoulder[0], shoulder[1] - 1),
                             (elbow[0], elbow[1] - 1), 2)
        # Gold armband
        arm_mid_x = int((shoulder[0] + elbow[0]) / 2)
        arm_mid_y = int((shoulder[1] + elbow[1]) / 2)
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_dark"],
                         (arm_mid_x - 2, arm_mid_y - 1, 5, 3))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_mid"],
                         (arm_mid_x - 2, arm_mid_y - 1, 5, 2))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_shine"],
                         (arm_mid_x, arm_mid_y - 1, 2, 1))
        # Forearm
        _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["shadow_deep"],
                             (elbow[0] + 1, elbow[1] + 1),
                             (hand[0] + 1, hand[1] + 1), 5)
        _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["skin_darkest"],
                             elbow, hand, 4)
        _NS_vessyra._aaline(surface, _NS_vessyra.PALETTE["skin_dark"],
                             elbow, hand, 3)
        # Gold bracelet at wrist
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_dark"],
                         (hand[0] - 2, hand[1] - 1, 4, 3))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_mid"],
                         (hand[0] - 2, hand[1] - 1, 4, 2))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_shine"],
                         (hand[0], hand[1] - 1, 1, 1))
        # Hand grip
        _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["skin_darkest"],
                               hand, 2)
        _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["skin_mid"],
                               hand, 1)
        # BOW
        _NS_vessyra._draw_bow(surface, hand[0], hand[1], facing, phase, action,
                               attack_progress)
    def _draw_bow(surface, hx, hy, facing, phase, action, attack_progress):
        """Ornate gold bow with green magic string."""
        # Bow is vertical (long recurve)
        bow_top_y = hy - 14
        bow_bot_y = hy + 14
        # Slight curve outward
        bow_curve_x = hx + facing * 3
        # Top limb of bow (curved)
        top_mid_x = int((hx + bow_curve_x) / 2)
        top_mid_y = int((hy + bow_top_y) / 2)
        # Curve using bezier-ish approximation
        for i in range(10):
            t = i / 10
            t2 = (i + 1) / 10
            x1 = int((1 - t) ** 2 * hx + 2 * (1 - t) * t * bow_curve_x + t ** 2 * hx)
            y1 = int((1 - t) ** 2 * hy + 2 * (1 - t) * t * top_mid_y + t ** 2 * bow_top_y)
            x2 = int((1 - t2) ** 2 * hx + 2 * (1 - t2) * t2 * bow_curve_x + t2 ** 2 * hx)
            y2 = int((1 - t2) ** 2 * hy + 2 * (1 - t2) * t2 * top_mid_y + t2 ** 2 * bow_top_y)
            # Shadow
            pygame.draw.line(surface, _NS_vessyra.PALETTE["shadow_deep"],
                             (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 3)
            pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_darkest"],
                             (x1, y1), (x2, y2), 3)
            pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_dark"],
                             (x1, y1), (x2, y2), 2)
            pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_mid"],
                             (x1, y1), (x2, y2), 1)
            if i % 2 == 0:
                pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_shine"],
                                 (x1, y1, 1, 1))
        # Bottom limb of bow (mirror)
        bot_mid_y = int((hy + bow_bot_y) / 2)
        for i in range(10):
            t = i / 10
            t2 = (i + 1) / 10
            x1 = int((1 - t) ** 2 * hx + 2 * (1 - t) * t * bow_curve_x + t ** 2 * hx)
            y1 = int((1 - t) ** 2 * hy + 2 * (1 - t) * t * bot_mid_y + t ** 2 * bow_bot_y)
            x2 = int((1 - t2) ** 2 * hx + 2 * (1 - t2) * t2 * bow_curve_x + t2 ** 2 * hx)
            y2 = int((1 - t2) ** 2 * hy + 2 * (1 - t2) * t2 * bot_mid_y + t2 ** 2 * bow_bot_y)
            pygame.draw.line(surface, _NS_vessyra.PALETTE["shadow_deep"],
                             (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 3)
            pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_darkest"],
                             (x1, y1), (x2, y2), 3)
            pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_dark"],
                             (x1, y1), (x2, y2), 2)
            pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_mid"],
                             (x1, y1), (x2, y2), 1)
            if i % 2 == 0:
                pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_shine"],
                                 (x1, y1, 1, 1))
        # Tips of the bow (ornaments)
        for tip_y in (bow_top_y, bow_bot_y):
            _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["gold_darkest"],
                                   (hx, tip_y), 2)
            _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["gold_mid"],
                                   (hx, tip_y), 1)
            pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_shine"],
                             (hx, tip_y, 1, 1))
        # Central grip
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_darkest"],
                         (hx - 1, hy - 2, 3, 5))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_dark"],
                         (hx - 1, hy - 2, 3, 4))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["gold_mid"],
                         (hx - 1, hy - 2, 2, 3))
        # Central gem
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["magic_dark"],
                         (hx, hy, 1, 1))
        pygame.draw.rect(surface,
                         (*_NS_vessyra.PALETTE["magic_hot"],
                          _NS_vessyra._alpha(255 * pulse)),
                         (hx, hy, 1, 1))
        # BOWSTRING (green magic energy)
        # Determine pull position based on attack_progress
        if action == "attack" and attack_progress < 0.4:
            # Pulled back
            pull_off = int(-facing * (2 + attack_progress / 0.4 * 6))
        elif action == "attack" and 0.4 <= attack_progress < 0.55:
            t = (attack_progress - 0.4) / 0.15
            pull_off = int(-facing * (8 - t * 6))
        else:
            pull_off = int(-facing * 2)  # slight rest tension
        string_top = (hx, bow_top_y)
        string_bot = (hx, bow_bot_y)
        string_mid = (hx + pull_off, hy)
        pygame.draw.line(surface, _NS_vessyra.PALETTE["magic_dark"],
                         string_top, string_mid, 1)
        pygame.draw.line(surface, _NS_vessyra.PALETTE["magic_dark"],
                         string_mid, string_bot, 1)
        pygame.draw.line(surface, _NS_vessyra.PALETTE["magic_light"],
                         string_top, string_mid, 1)
        pygame.draw.line(surface, _NS_vessyra.PALETTE["magic_light"],
                         string_mid, string_bot, 1)
        # NOCKED ARROW (during aim phase)
        if action == "attack" and attack_progress < 0.4:
            # Draw arrow being pulled
            arrow_head_x = hx + facing * 8
            arrow_tail_x = string_mid[0] - facing * 2
            arrow_y = string_mid[1]
            # Shaft
            pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_dark"],
                             (arrow_tail_x, arrow_y),
                             (arrow_head_x, arrow_y), 2)
            pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_light"],
                             (arrow_tail_x, arrow_y),
                             (arrow_head_x, arrow_y), 1)
            # Arrowhead (green glowing tip)
            for r in range(4, 0, -1):
                a = _NS_vessyra._alpha(200 * (4 - r) / 4)
                _NS_vessyra._aacircle(surface,
                                       (*_NS_vessyra.PALETTE["magic_mid"], a),
                                       (arrow_head_x, arrow_y), r)
            pygame.draw.rect(surface, _NS_vessyra.PALETTE["magic_hot"],
                             (arrow_head_x, arrow_y, 1, 1))
            pygame.draw.rect(surface, _NS_vessyra.PALETTE["magic_shine"],
                             (arrow_head_x, arrow_y, 1, 1))
            # Fletching
            pygame.draw.line(surface, _NS_vessyra.PALETTE["magic_mid"],
                             (arrow_tail_x, arrow_y - 1),
                             (arrow_tail_x - facing * 2, arrow_y - 2), 1)
            pygame.draw.line(surface, _NS_vessyra.PALETTE["magic_mid"],
                             (arrow_tail_x, arrow_y + 1),
                             (arrow_tail_x - facing * 2, arrow_y + 2), 1)
        # Small green energy sparkles along string
        for i in range(3):
            spark_t = i / 3
            sp_y = int(bow_top_y + (bow_bot_y - bow_top_y) * spark_t)
            sp_x = hx + pull_off + int(math.sin(phase * 3 + i) * 1)
            pygame.draw.rect(surface, _NS_vessyra.PALETTE["magic_hot"],
                             (sp_x, sp_y, 1, 1))
    # ============================================================
    # BASIC ATTACK — green arrow
    # ============================================================
    def _draw_basic_arrow(surface, boss, x, y, progress):
        """Basic green magic arrow — ranged attack."""
        if progress < 0.55:
            return
        facing = boss.direction
        tx, ty = _NS_vessyra._target_position(boss, x, y)
        start_x = x + facing * 20
        start_y = y - 8
        t = (progress - 0.55) / 0.45
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Arrow direction
        dx = tx - start_x
        dy = ty - start_y
        length = math.sqrt(dx * dx + dy * dy)
        if length == 0:
            return
        ux = dx / length
        uy = dy / length
        # Trail
        for i in range(7):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_vessyra._alpha(230 - i * 30)
            size = max(1, 4 - i)
            _NS_vessyra._aacircle(surface,
                                   (*_NS_vessyra.PALETTE["magic_dark"], alpha),
                                   (px, py), size + 1)
            _NS_vessyra._aacircle(surface,
                                   (*_NS_vessyra.PALETTE["magic_mid"], alpha),
                                   (px, py), size)
            _NS_vessyra._aacircle(surface,
                                   (*_NS_vessyra.PALETTE["magic_light"], alpha),
                                   (px, py), max(1, size - 1))
        # Arrow shaft
        shaft_len = 8
        shaft_start_x = bx - int(ux * shaft_len)
        shaft_start_y = by - int(uy * shaft_len)
        pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_dark"],
                         (shaft_start_x, shaft_start_y), (bx, by), 2)
        pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_mid"],
                         (shaft_start_x, shaft_start_y), (bx, by), 1)
        # Arrowhead (bright green glow)
        for r in range(5, 0, -1):
            a = _NS_vessyra._alpha(200 * (5 - r) / 5)
            _NS_vessyra._aacircle(surface,
                                   (*_NS_vessyra.PALETTE["magic_light"], a),
                                   (bx, by), r)
        _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["magic_hot"],
                               (bx, by), 2)
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["magic_shine"],
                         (bx, by, 1, 1))
        pygame.draw.rect(surface, _NS_vessyra.PALETTE["white"],
                         (bx, by, 1, 1))
        # Fletching
        perp_x = -uy
        perp_y = ux
        for side in (-1, 1):
            fx = shaft_start_x + int(perp_x * 2 * side)
            fy = shaft_start_y + int(perp_y * 2 * side)
            pygame.draw.line(surface, _NS_vessyra.PALETTE["magic_mid"],
                             (shaft_start_x, shaft_start_y), (fx, fy), 1)
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y, faded=False):
        shadow = pygame.Surface((150, 30), pygame.SRCALPHA)
        mult = 0.5 if faded else 1.0
        for radius in range(14, 0, -1):
            alpha = int(max(0, (14 - radius) * 16) * mult)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 15 - radius,
                                 130 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 8, 3, int(170 * mult)),
                            (5, 7, 140, 16))
        pygame.draw.ellipse(shadow, (15, 45, 20, int(120 * mult)),
                            (12, 9, 126, 12))
        surface.blit(shadow, (x - 75, y - 15))
    def _draw_gorgon_aura(surface, x, y, phase):
        """Green toxic aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_vessyra._alpha((95 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_vessyra._aacircle(aura,
                                       (*_NS_vessyra.PALETTE["magic_darkest"], alpha),
                                       (110, 90), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_vessyra._alpha((60 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_vessyra._aacircle(aura,
                                       (*_NS_vessyra.PALETTE["magic_dark"], alpha),
                                       (110, 90), radius)
        for radius in range(35, 5, -2):
            alpha = _NS_vessyra._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_vessyra._aacircle(aura,
                                       (*_NS_vessyra.PALETTE["magic_mid"], alpha),
                                       (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))
        # Floating green particles + tiny snakes
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 44 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_vessyra.PALETTE["magic_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_vessyra.PALETTE["magic_hot"],
                             (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Green ground ring with serpent motif."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_vessyra.PALETTE["magic_darkest"], 210),
                            (5, 20, 160, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_vessyra.PALETTE["magic_dark"], 220),
                            (14, 22, 142, 24), 2)
        pygame.draw.ellipse(ring, (*_NS_vessyra.PALETTE["magic_mid"], 230),
                            (25, 24, 120, 20), 1)
        # Runes
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            x1 = 85 + int(math.cos(angle) * 48)
            y1 = 32 + int(math.sin(angle) * 9)
            x2 = 85 + int(math.cos(angle) * 70)
            y2 = 32 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_vessyra.PALETTE["magic_hot"], 230),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_vessyra.PALETTE["magic_shine"],
                                       _NS_vessyra._alpha(150 * pulse)),
                                (15, 12, 140, 42), 1)
        surface.blit(ring, (x - 85, y - 27))
    def _draw_snake_trail(surface, cx, cy, phase, facing):
        """Trail behind slithering movement."""
        for i in range(8):
            t = (phase * 0.5 + i * 0.13) % 1.0
            wx = cx + int(math.sin(phase + i) * 12) - facing * i * 3
            wy = cy + int(t * 10)
            alpha = _NS_vessyra._alpha(180 * (1 - t))
            if alpha > 0:
                _NS_vessyra._aacircle(surface,
                                       (*_NS_vessyra.PALETTE["magic_dark"], alpha),
                                       (wx, wy), 3)
                _NS_vessyra._aacircle(surface,
                                       (*_NS_vessyra.PALETTE["magic_mid"], alpha),
                                       (wx, wy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_vessyra.PALETTE["magic_hot"], alpha),
                                 (wx, wy, 1, 1))
    # ============================================================
    # SKILL Q - SPLIT SHOT (multiple arrows fan)
    # ============================================================
    def _draw_split_shot(surface, boss, x, y, timer, phase):
        """Multiple green arrows in fan spread."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vessyra._target_position(boss, x, y)
        if progress < 0.2:
            # Charge — glowing energy at bow
            t = progress / 0.2
            mx = x + facing * 15
            my = y - 8
            cr = int(4 + t * 8)
            for r in range(cr + 4, 0, -1):
                a = _NS_vessyra._alpha(220 * (cr + 4 - r) / (cr + 4))
                _NS_vessyra._aacircle(surface,
                                       (*_NS_vessyra.PALETTE["magic_dark"], a),
                                       (mx, my), r)
            _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["magic_mid"],
                                   (mx, my), cr - 2)
            _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["magic_hot"],
                                   (mx, my), max(1, cr - 4))
        else:
            # Fan of arrows
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 20
            start_y = y - 8
            num_arrows = 6
            for i in range(num_arrows):
                # Fan angle spread
                fan_off_y = int((i - num_arrows / 2 + 0.5) * 12)
                effective_ty = ty + fan_off_y
                arrow_t = min(1.0, t * 1.1)
                bx = int(start_x + (tx - start_x) * arrow_t)
                by = int(start_y + (effective_ty - start_y) * arrow_t)
                # Direction
                dx = tx - start_x
                dy = effective_ty - start_y
                length = math.sqrt(dx * dx + dy * dy)
                if length == 0:
                    continue
                ux = dx / length
                uy = dy / length
                # Trail
                for tr in range(5):
                    trail_t = max(0.0, arrow_t - tr * 0.05)
                    px = int(start_x + (tx - start_x) * trail_t)
                    py = int(start_y + (effective_ty - start_y) * trail_t)
                    alpha = _NS_vessyra._alpha(220 - tr * 35)
                    _NS_vessyra._aacircle(surface,
                                           (*_NS_vessyra.PALETTE["magic_dark"], alpha),
                                           (px, py), max(1, 4 - tr))
                    _NS_vessyra._aacircle(surface,
                                           (*_NS_vessyra.PALETTE["magic_mid"], alpha),
                                           (px, py), max(1, 3 - tr))
                    _NS_vessyra._aacircle(surface,
                                           (*_NS_vessyra.PALETTE["magic_light"], alpha),
                                           (px, py), max(1, 2 - tr))
                # Arrow shaft + head
                shaft_len = 8
                shaft_start_x = bx - int(ux * shaft_len)
                shaft_start_y = by - int(uy * shaft_len)
                pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_dark"],
                                 (shaft_start_x, shaft_start_y), (bx, by), 2)
                pygame.draw.line(surface, _NS_vessyra.PALETTE["gold_mid"],
                                 (shaft_start_x, shaft_start_y), (bx, by), 1)
                # Head
                for r in range(4, 0, -1):
                    a = _NS_vessyra._alpha(200 * (4 - r) / 4)
                    _NS_vessyra._aacircle(surface,
                                           (*_NS_vessyra.PALETTE["magic_light"], a),
                                           (bx, by), r)
                _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["magic_hot"],
                                       (bx, by), 2)
                pygame.draw.rect(surface, _NS_vessyra.PALETTE["magic_shine"],
                                 (bx, by, 1, 1))
    # ============================================================
    # SKILL W - MYSTIC SNAKE (snake projectile)
    # ============================================================
    def _draw_mystic_snake(surface, boss, x, y, timer, phase):
        """Big green snake slithering toward target."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vessyra._target_position(boss, x, y)
        start_x = x + facing * 22
        start_y = y - 6
        t = progress
        # Head of snake at target
        hx = int(start_x + (tx - start_x) * t)
        hy = int(start_y + (ty - start_y) * t)
        # Direction
        dx = tx - start_x
        dy = ty - start_y
        length = math.sqrt(dx * dx + dy * dy)
        if length == 0:
            return
        ux = dx / length
        uy = dy / length
        perp_x = -uy
        perp_y = ux
        # SNAKE BODY (curving segments along path)
        num_segs = 10
        for seg_i in range(num_segs):
            # Segment position (behind head)
            seg_offset = seg_i * 8
            seg_t = max(0.0, t - seg_offset / max(1, length))
            seg_px = int(start_x + (tx - start_x) * seg_t)
            seg_py = int(start_y + (ty - start_y) * seg_t)
            # Add serpentine wave perpendicular to travel direction
            wave = math.sin(phase * 3 + seg_i * 0.5) * (5 - seg_i * 0.3)
            seg_px += int(perp_x * wave)
            seg_py += int(perp_y * wave)
            thickness = max(2, int(7 - seg_i * 0.4))
            # Body layers
            _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["shadow_deep"],
                                   (seg_px + 1, seg_py + 1), thickness + 1)
            _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["magic_darkest"],
                                   (seg_px, seg_py), thickness)
            _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["magic_dark"],
                                   (seg_px, seg_py), thickness - 1)
            _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["magic_mid"],
                                   (seg_px, seg_py), max(1, thickness - 2))
            if seg_i < 6:
                _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["magic_light"],
                                       (seg_px, seg_py - 1),
                                       max(1, thickness - 4))
            # Scales spot
            if thickness > 3 and seg_i % 2 == 0:
                pygame.draw.rect(surface, _NS_vessyra.PALETTE["magic_hot"],
                                 (seg_px, seg_py, 1, 1))
        # SNAKE HEAD (bigger, more detailed)
        head_size = 5
        # Shadow
        _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["shadow_deep"],
                               (hx + 2, hy + 2), head_size + 1)
        # Head body
        _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["magic_darkest"],
                               (hx, hy), head_size + 1)
        _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["magic_dark"],
                               (hx, hy), head_size)
        _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["magic_mid"],
                               (hx, hy), head_size - 1)
        _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["magic_light"],
                               (hx - int(ux), hy - int(uy)),
                               max(1, head_size - 3))
        # Head snout (elongated forward)
        snout_x = hx + int(ux * 4)
        snout_y = hy + int(uy * 4)
        pygame.draw.line(surface, _NS_vessyra.PALETTE["magic_darkest"],
                         (hx, hy), (snout_x, snout_y), 4)
        pygame.draw.line(surface, _NS_vessyra.PALETTE["magic_mid"],
                         (hx, hy), (snout_x, snout_y), 2)
        # Eyes (glowing yellow)
        for side in (-1, 1):
            ex = hx + int(perp_x * 2 * side)
            ey = hy + int(perp_y * 2 * side)
            pygame.draw.rect(surface, _NS_vessyra.PALETTE["snake_eye_dark"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_vessyra.PALETTE["snake_eye_hot"],
                             (ex, ey, 1, 1))
        # Forked tongue (occasionally)
        if int(phase * 4) % 3 == 0:
            tongue_end_x = snout_x + int(ux * 3)
            tongue_end_y = snout_y + int(uy * 3)
            pygame.draw.line(surface, _NS_vessyra.PALETTE["eye_mid"],
                             (snout_x, snout_y),
                             (tongue_end_x, tongue_end_y), 1)
            # Fork
            pygame.draw.line(surface, _NS_vessyra.PALETTE["eye_mid"],
                             (tongue_end_x, tongue_end_y),
                             (tongue_end_x + int(perp_x * 2),
                              tongue_end_y + int(perp_y * 2)), 1)
            pygame.draw.line(surface, _NS_vessyra.PALETTE["eye_mid"],
                             (tongue_end_x, tongue_end_y),
                             (tongue_end_x - int(perp_x * 2),
                              tongue_end_y - int(perp_y * 2)), 1)
        # Impact stun on target
        if t > 0.9:
            st = (t - 0.9) / 0.1
            radius = int(12 + st * 15)
            alpha = _NS_vessyra._alpha(240 * (1 - st))
            _NS_vessyra._aacircle(surface,
                                   (*_NS_vessyra.PALETTE["magic_mid"], alpha),
                                   (tx, ty), radius, 2)
            _NS_vessyra._aacircle(surface,
                                   (*_NS_vessyra.PALETTE["magic_hot"], alpha),
                                   (tx, ty), max(1, radius - 6), 1)
            # Stun stars
            for i in range(5):
                angle = i * math.pi / 2.5 + phase
                ex = tx + int(math.cos(angle) * radius)
                ey = ty + int(math.sin(angle) * radius * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_vessyra.PALETTE["magic_shine"], alpha),
                                 (ex - 1, ey, 3, 1))
                pygame.draw.rect(surface,
                                 (*_NS_vessyra.PALETTE["magic_shine"], alpha),
                                 (ex, ey - 1, 1, 3))
    # ============================================================
    # SKILL E - STONE GAZE (petrify beam from eyes)
    # ============================================================
    def _draw_stone_ground(surface, boss, x, y, timer, phase):
        """Ground effect at target — stone spread."""
        tx, ty = _NS_vessyra._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress > 0.3:
            r = int(30 * min(1.0, (progress - 0.3) / 0.7 * 2))
            if r > 3:
                pygame.draw.ellipse(surface,
                                    (*_NS_vessyra.PALETTE["stone_dark"], 200),
                                    (tx - r, ty - r // 3, r * 2, r * 2 // 3))
                pygame.draw.ellipse(surface,
                                    (*_NS_vessyra.PALETTE["stone_mid"], 180),
                                    (tx - r + 3, ty - r // 3 + 2,
                                     r * 2 - 6, r * 2 // 3 - 4))
                # Crack pattern
                for i in range(5):
                    angle = i * math.pi / 2.5 + phase * 0.2
                    end_x = tx + int(math.cos(angle) * r * 0.8)
                    end_y = ty + int(math.sin(angle) * r * 0.4)
                    pygame.draw.line(surface,
                                     (*_NS_vessyra.PALETTE["stone_light"], 220),
                                     (tx, ty), (end_x, end_y), 1)
    def _draw_stone_gaze_beam(surface, boss, x, y, timer, phase):
        """Green petrifying beam from eyes to target."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vessyra._target_position(boss, x, y)
        if progress < 0.15:
            # Charge — eyes glow brighter
            t = progress / 0.15
            eye_x = x + facing * 2
            eye_y = y - 20  # eye level
            for eye_off in (-2, 2):
                for r in range(int(4 * t), 0, -1):
                    a = _NS_vessyra._alpha(220 * t * r / max(1, 4 * t))
                    _NS_vessyra._aacircle(surface,
                                           (*_NS_vessyra.PALETTE["magic_mid"], a),
                                           (eye_x + eye_off, eye_y), r)
                pygame.draw.rect(surface, _NS_vessyra.PALETTE["magic_hot"],
                                 (eye_x + eye_off, eye_y, 1, 1))
        elif progress < 0.7:
            # BEAM — green rays from both eyes to target
            t = (progress - 0.15) / 0.55
            intensity = math.sin(t * math.pi)
            eye_x = x + facing * 2
            eye_y = y - 20
            # Beam from each eye
            for eye_off in (-2, 2):
                start = (eye_x + eye_off, eye_y)
                end = (tx, ty)
                # Multi-layer beam
                for layer_i, (width, alpha_val) in enumerate([
                    (7, 100), (5, 140), (3, 180), (2, 220), (1, 255),
                ]):
                    a = _NS_vessyra._alpha(alpha_val * intensity)
                    colors = [
                        _NS_vessyra.PALETTE["magic_darkest"],
                        _NS_vessyra.PALETTE["magic_dark"],
                        _NS_vessyra.PALETTE["magic_mid"],
                        _NS_vessyra.PALETTE["magic_light"],
                        _NS_vessyra.PALETTE["magic_shine"],
                    ]
                    color = colors[min(layer_i, 4)]
                    # Perpendicular offset for beam width
                    dx = end[0] - start[0]
                    dy = end[1] - start[1]
                    length = math.sqrt(dx * dx + dy * dy)
                    if length == 0:
                        continue
                    px = -dy / length
                    py = dx / length
                    beam_pts = [
                        (int(start[0] + px * width / 2),
                         int(start[1] + py * width / 2)),
                        (int(end[0] + px * width / 2),
                         int(end[1] + py * width / 2)),
                        (int(end[0] - px * width / 2),
                         int(end[1] - py * width / 2)),
                        (int(start[0] - px * width / 2),
                         int(start[1] - py * width / 2)),
                    ]
                    _NS_vessyra._poly(surface, (*color, a), beam_pts)
                # Sparkles along beam
                for spark_i in range(6):
                    sp_t = (phase * 3 + spark_i * 0.2) % 1.0
                    sp_x = int(start[0] + (end[0] - start[0]) * sp_t)
                    sp_y = int(start[1] + (end[1] - start[1]) * sp_t)
                    a = _NS_vessyra._alpha(240 * intensity)
                    pygame.draw.rect(surface,
                                     (*_NS_vessyra.PALETTE["magic_shine"], a),
                                     (sp_x, sp_y, 2, 2))
            # Impact on target — swirling green energy
            imp_r = int(8 + intensity * 8)
            impact_alpha = _NS_vessyra._alpha(240 * intensity)
            for r in range(imp_r, 0, -1):
                a = _NS_vessyra._alpha(impact_alpha * (imp_r - r) / imp_r)
                _NS_vessyra._aacircle(surface,
                                       (*_NS_vessyra.PALETTE["magic_mid"], a),
                                       (tx, ty), r)
            _NS_vessyra._aacircle(surface, _NS_vessyra.PALETTE["magic_hot"],
                                   (tx, ty), max(1, imp_r // 3))
            # Radial energy lines
            for i in range(8):
                angle_s = i * math.pi / 4 + phase
                ex = tx + int(math.cos(angle_s) * imp_r)
                ey = ty + int(math.sin(angle_s) * imp_r * 0.8)
                pygame.draw.line(surface,
                                 (*_NS_vessyra.PALETTE["magic_shine"], impact_alpha),
                                 (tx, ty), (ex, ey), 1)
        else:
            # Aftermath — stone particles
            t = (progress - 0.7) / 0.3
            for i in range(10):
                rise_t = (phase * 0.6 + i * 0.1) % 1.0
                rx = tx + int(math.sin(phase + i) * 20)
                ry = ty - int(rise_t * 25)
                alpha = _NS_vessyra._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    pygame.draw.rect(surface,
                                     (*_NS_vessyra.PALETTE["stone_mid"], alpha),
                                     (rx, ry, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_vessyra.PALETTE["stone_light"], alpha),
                                     (rx, ry, 1, 1))
    # ============================================================
    # SKILL R - MANA SHIELD (green bubble around boss)
    # ============================================================
    def _draw_mana_shield(surface, boss, x, y, timer, pulse):
        """Green magical shield bubble around body."""
        r = 55
        pulse_val = math.sin(pulse * 2) * 0.25 + 0.75
        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)
        # Rings
        for i, (thick, alpha) in enumerate([(4, 100), (3, 140), (2, 180), (1, 220)]):
            a = _NS_vessyra._alpha(alpha * pulse_val)
            _NS_vessyra._aacircle(bubble,
                                   (*_NS_vessyra.PALETTE["magic_dark"], a),
                                   center, r - i, thick)
            _NS_vessyra._aacircle(bubble,
                                   (*_NS_vessyra.PALETTE["magic_mid"], a),
                                   center, r - i - 1, 1)
        # Sparkles along edge
        for i in range(20):
            angle = pulse * 1.5 + i * math.pi / 10
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            pygame.draw.rect(bubble, _NS_vessyra.PALETTE["magic_light"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(bubble, _NS_vessyra.PALETTE["magic_hot"],
                             (sx, sy, 1, 1))
        # Runes rotating on shield
        for i in range(6):
            angle = pulse * 0.8 + i * math.pi / 3
            inner_r = r - 5
            bx = center[0] + int(math.cos(angle) * inner_r)
            by = center[1] + int(math.sin(angle) * inner_r)
            _NS_vessyra._aacircle(bubble, _NS_vessyra.PALETTE["magic_mid"],
                                   (bx, by), 2)
            _NS_vessyra._aacircle(bubble, _NS_vessyra.PALETTE["magic_hot"],
                                   (bx, by), 1)
        surface.blit(bubble, (x - r - 10, y - r - 10))
        # Extra sparks around shield
        for i in range(8):
            angle = pulse * 0.8 + i * math.pi / 4
            end_x = x + int(math.cos(angle) * (r + 6))
            end_y = y + int(math.sin(angle) * (r + 6))
            alpha = _NS_vessyra._alpha(150 + math.sin(pulse * 3 + i) * 40)
            pygame.draw.line(surface,
                             (*_NS_vessyra.PALETTE["magic_light"], alpha),
                             (x + int(math.cos(angle) * r),
                              y + int(math.sin(angle) * r)),
                             (end_x, end_y), 1)
            pygame.draw.rect(surface, _NS_vessyra.PALETTE["magic_hot"],
                             (end_x, end_y, 1, 1))



# ====================================================================
# MALZEROTH (HEXBOUND SOVEREIGN) - TRUE BOSS
# ====================================================================

class _NS_malzeroth:
    """Namespace malzeroth - demon witch mini boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Purple demon skin
        "skin_darkest": (25, 15, 40),
        "skin_dark": (55, 35, 80),
        "skin_mid": (95, 65, 130),
        "skin_light": (145, 110, 180),
        "skin_shine": (200, 170, 225),
        # Red cloak/robe
        "cloak_darkest": (35, 8, 12),
        "cloak_dark": (75, 18, 25),
        "cloak_mid": (135, 35, 45),
        "cloak_light": (185, 60, 65),
        "cloak_shine": (230, 110, 100),
        # Gold ornaments
        "gold_dark": (85, 55, 15),
        "gold_mid": (175, 130, 40),
        "gold_light": (235, 195, 90),
        "gold_shine": (255, 240, 170),
        # Yellow demon eyes
        "eye_socket": (10, 5, 3),
        "eye_dark": (95, 55, 10),
        "eye_mid": (215, 165, 30),
        "eye_light": (255, 230, 100),
        "eye_glow": (255, 255, 200),
        # Purple crystal magic (Q Earth Spike)
        "crystal_darkest": (25, 5, 45),
        "crystal_dark": (65, 20, 105),
        "crystal_mid": (140, 60, 200),
        "crystal_light": (200, 130, 245),
        "crystal_shine": (240, 210, 255),
        # Green hex magic (W)
        "hex_darkest": (15, 30, 8),
        "hex_dark": (45, 90, 20),
        "hex_mid": (110, 180, 50),
        "hex_light": (180, 240, 100),
        "hex_shine": (230, 255, 180),
        # Orange mana drain (E)
        "mana_darkest": (40, 10, 5),
        "mana_dark": (120, 40, 15),
        "mana_mid": (215, 95, 25),
        "mana_light": (255, 165, 60),
        "mana_shine": (255, 225, 140),
        # Blood/HP drain (E) — merah gelap darah
        "hp_darkest": (25, 5, 8),
        "hp_dark": (85, 15, 20),
        "hp_mid": (180, 30, 45),
        "hp_light": (240, 70, 80),
        "hp_shine": (255, 170, 170),
        # Red finger of death (R)
        "death_darkest": (30, 3, 5),
        "death_dark": (110, 15, 20),
        "death_mid": (210, 40, 45),
        "death_light": (255, 100, 80),
        "death_shine": (255, 200, 160),
        # Horn/claw bone
        "bone_dark": (35, 25, 15),
        "bone_mid": (90, 70, 50),
        "bone_light": (170, 145, 105),
        # Staff wood
        "wood_dark": (35, 20, 15),
        "wood_mid": (75, 45, 30),
        "wood_light": (130, 90, 60),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }
    # ------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_malzeroth._clamp(color)
        if _NS_malzeroth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_malzeroth._clamp(color)
        if _NS_malzeroth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_malzeroth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    def _staff_crystal_position(boss, x, y):
        """Posisi kristal di ujung tongkat (sumber semua projectile/spell)."""
        facing = boss.direction
        # Staff berada di sisi berlawanan facing (arm belakang pegang staff).
        # staff_arm_x = cx - facing * 10
        # staff_top offset dari arm = -facing * 8, y offset = -32
        # crystal offset dari staff top = y -10
        # Float bob sudah include di y yang dipassing.
        staff_top_x = x - facing * 10 - facing * 8   # = x - facing * 18
        crystal_y = y - 6 - 32 - 10                   # = y - 48
        # Sedikit float animation di kristal.
        crystal_y += int(math.sin(boss.pulse * 1.5) * 1)
        return staff_top_x, crystal_y
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_malzeroth(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_malzeroth._update_attack_anim(boss)
        attack_progress = getattr(boss, "_mz_attack_progress", 0.0)
        attacking = (
            getattr(boss, "_mz_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient FX behind body.
        _NS_malzeroth._draw_demon_aura(surface, x, y, pulse)
        _NS_malzeroth._draw_ground_ring(surface, x, y + 48, pulse, active_skill)
        # Skill ground FX (behind body).
        if active_skill == "q":
            _NS_malzeroth._draw_earthspike_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_malzeroth._draw_finger_ground(surface, boss, x, y, skill_timer, pulse)
        # Floating body.
        float_bob = math.sin(pulse * 0.6) * 5
        body_y = y + int(float_bob)
        # Body pose.
        if attacking:
            _NS_malzeroth._draw_body_attack(surface, boss, x, body_y)
        else:
            _NS_malzeroth._draw_body_idle(surface, boss, x, body_y)
        # Foreground FX.
        if active_skill == "q":
            _NS_malzeroth._draw_earthspike_projectile(surface, boss, x, body_y,
                                                      skill_timer, pulse)
        elif active_skill == "w":
            _NS_malzeroth._draw_hex_projectile(surface, boss, x, body_y,
                                               skill_timer, pulse)
        elif active_skill == "e":
            _NS_malzeroth._draw_hp_drain_beam(surface, boss, x, body_y,
                                              skill_timer, pulse)
        elif active_skill == "r":
            _NS_malzeroth._draw_finger_beam(surface, boss, x, body_y,
                                            skill_timer, pulse)
        else:
            # Basic attack projectile - HANYA saat tidak ada skill aktif.
            if attacking and attack_progress > 0:
                _NS_malzeroth._draw_basic_projectile(surface, boss, x, body_y)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_mz_previous_timer", 0))
        active = bool(getattr(boss, "_mz_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._mz_attack_active = True
            boss._mz_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._mz_attack_frame = int(getattr(boss, "_mz_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._mz_attack_active = False
            boss._mz_attack_frame = 0
            active = False
        boss._mz_previous_timer = timer
        boss._mz_attack_progress = (
            min(1.0, getattr(boss, "_mz_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # BODY DRAWING
    # ============================================================
    def _draw_body_idle(surface, boss, cx, cy):
        _NS_malzeroth._draw_float_shadow(surface, cx, cy + 52, boss.pulse)
        _NS_malzeroth._draw_floating_dust(surface, cx, cy + 40, boss.pulse)
        _NS_malzeroth._draw_body(surface, boss, cx, cy, "idle", 0)
    def _draw_body_attack(surface, boss, cx, cy):
        progress = getattr(boss, "_mz_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))
        # Arm raises during cast.
        _NS_malzeroth._draw_float_shadow(surface, cx, cy + 52, boss.pulse)
        _NS_malzeroth._draw_floating_dust(surface, cx, cy + 40, boss.pulse)
        _NS_malzeroth._draw_body(surface, boss, cx, cy, "attack", progress)
    def _draw_body(surface, boss, cx, cy, action, progress):
        """Full body: cloak, legs (hidden), torso, arms, head, staff."""
        facing = boss.direction
        phase = boss.pulse
        # Draw cloak backdrop first (largest silhouette).
        _NS_malzeroth._draw_cloak(surface, cx, cy, facing, phase)
        # Robed lower body (dangling).
        _NS_malzeroth._draw_robe_bottom(surface, cx, cy, facing, phase)
        # Torso.
        _NS_malzeroth._draw_torso(surface, cx, cy, facing, phase)
        # Arms with staff.
        _NS_malzeroth._draw_arms_and_staff(surface, cx, cy, facing, phase,
                                            action, progress)
        # Head with horns and demon face.
        _NS_malzeroth._draw_head(surface, cx, cy - 26, facing, phase, action,
                                  progress)
        # Shoulder pauldrons (over torso).
        _NS_malzeroth._draw_pauldrons(surface, cx, cy - 12, facing, phase)
    def _draw_cloak(surface, cx, cy, facing, phase):
        """Red cloak silhouette behind body."""
        sway = math.sin(phase * 0.5) * 2
        cloak_pts = [
            (cx - 18, cy - 18),                    # top left shoulder
            (cx - 22, cy - 8),                     # left flare
            (cx - 26 + int(sway), cy + 5),         # left mid
            (cx - 28 + int(sway), cy + 20),        # left bottom
            (cx - 22 + int(sway * 0.5), cy + 32),  # left tail
            (cx - 12, cy + 38),                    # bottom left
            (cx, cy + 40),                         # bottom
            (cx + 12, cy + 38),                    # bottom right
            (cx + 22 - int(sway * 0.5), cy + 32),  # right tail
            (cx + 28 - int(sway), cy + 20),        # right bottom
            (cx + 26 - int(sway), cy + 5),         # right mid
            (cx + 22, cy - 8),                     # right flare
            (cx + 18, cy - 18),                    # top right shoulder
            (cx + 10, cy - 20),                    # top right
            (cx, cy - 22),                         # top
            (cx - 10, cy - 20),                    # top left
        ]
        _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 3) for p in cloak_pts])
        _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["cloak_darkest"], cloak_pts)
        # Inner darker layer.
        inner_pts = [
            (cx - 16, cy - 16),
            (cx - 20, cy - 6),
            (cx - 22, cy + 6),
            (cx - 20, cy + 22),
            (cx - 14, cy + 32),
            (cx, cy + 34),
            (cx + 14, cy + 32),
            (cx + 20, cy + 22),
            (cx + 22, cy + 6),
            (cx + 20, cy - 6),
            (cx + 16, cy - 16),
            (cx, cy - 20),
        ]
        _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["cloak_dark"], inner_pts)
        # Cloak inner front slit (V shape open).
        front_slit = [
            (cx - 8, cy - 10),
            (cx + 8, cy - 10),
            (cx + 6, cy + 20),
            (cx, cy + 32),
            (cx - 6, cy + 20),
        ]
        _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["cloak_mid"], front_slit)
        # Highlights on cloak edge.
        for i, (px, py) in enumerate(cloak_pts[:6]):
            if i > 0:
                pygame.draw.line(surface, _NS_malzeroth.PALETTE["cloak_light"],
                                 cloak_pts[i - 1], (px, py), 1)
        # Gold trim along neckline.
        pygame.draw.line(surface, _NS_malzeroth.PALETTE["gold_dark"],
                         (cx - 16, cy - 16), (cx - 8, cy - 20), 1)
        pygame.draw.line(surface, _NS_malzeroth.PALETTE["gold_mid"],
                         (cx - 8, cy - 20), (cx + 8, cy - 20), 1)
        pygame.draw.line(surface, _NS_malzeroth.PALETTE["gold_dark"],
                         (cx + 8, cy - 20), (cx + 16, cy - 16), 1)
    def _draw_robe_bottom(surface, cx, cy, facing, phase):
        """Wavy dangling robe (character floats — no legs)."""
        sway = math.sin(phase * 0.7) * 3
        for i, offset in enumerate((-10, -4, 2, 8)):
            wave = math.sin(phase * 0.6 + i * 0.5) * 2
            x_off = offset + int(sway * (i * 0.3))
            pts = [
                (cx + x_off - 3, cy + 12),
                (cx + x_off + 3, cy + 12),
                (cx + x_off + 4 + int(wave), cy + 24),
                (cx + x_off + int(wave * 0.5), cy + 34),
                (cx + x_off - 4 + int(wave), cy + 24),
            ]
            _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["cloak_darkest"], pts)
            _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["cloak_dark"], [
                (pts[0][0] + 1, pts[0][1] + 1),
                (pts[1][0] - 1, pts[1][1] + 1),
                (pts[2][0] - 1, pts[2][1] - 1),
                (pts[3][0], pts[3][1] - 1),
                (pts[4][0] + 1, pts[4][1] - 1),
            ])
    def _draw_torso(surface, cx, cy, facing, phase):
        """Purple demon torso with gold belt."""
        torso_pts = [
            (cx - 12, cy - 16),
            (cx - 14, cy - 8),
            (cx - 12, cy + 4),
            (cx - 8, cy + 12),
            (cx + 8, cy + 12),
            (cx + 12, cy + 4),
            (cx + 14, cy - 8),
            (cx + 12, cy - 16),
        ]
        _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["skin_darkest"], torso_pts)
        _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["skin_dark"], [
            (cx - 11, cy - 14),
            (cx - 12, cy - 6),
            (cx - 10, cy + 3),
            (cx - 6, cy + 10),
            (cx + 6, cy + 10),
            (cx + 10, cy + 3),
            (cx + 12, cy - 6),
            (cx + 11, cy - 14),
        ])
        # Chest muscle shading.
        _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["skin_mid"], [
            (cx - 8, cy - 10),
            (cx - 6, cy - 4),
            (cx - 4, cy + 4),
            (cx + 4, cy + 4),
            (cx + 6, cy - 4),
            (cx + 8, cy - 10),
        ])
        _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["skin_light"], [
            (cx - 4, cy - 8),
            (cx + 4, cy - 8),
            (cx + 2, cy - 2),
            (cx - 2, cy - 2),
        ])
        # Gold ornate belt/medallion.
        pygame.draw.rect(surface, _NS_malzeroth.PALETTE["gold_dark"],
                         (cx - 10, cy + 8, 20, 4))
        pygame.draw.rect(surface, _NS_malzeroth.PALETTE["gold_mid"],
                         (cx - 9, cy + 8, 18, 3))
        pygame.draw.rect(surface, _NS_malzeroth.PALETTE["gold_light"],
                         (cx - 8, cy + 9, 16, 1))
        # Central medallion gem.
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["gold_dark"], (cx, cy + 10), 3)
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["gold_mid"], (cx, cy + 10), 2)
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["crystal_mid"], (cx, cy + 10), 1)
        pygame.draw.rect(surface, _NS_malzeroth.PALETTE["crystal_shine"], (cx, cy + 10, 1, 1))
    def _draw_pauldrons(surface, cx, cy, facing, phase):
        """Ornate spiked shoulder armor."""
        for side in (-1, 1):
            base_x = cx + side * 14
            # Pauldron base.
            paul_pts = [
                (base_x - 4 * side, cy - 4),
                (base_x + 6 * side, cy - 6),
                (base_x + 8 * side, cy),
                (base_x + 5 * side, cy + 4),
                (base_x - 3 * side, cy + 2),
            ]
            _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["gold_dark"], paul_pts)
            _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["gold_mid"], [
                (base_x - 2 * side, cy - 3),
                (base_x + 5 * side, cy - 4),
                (base_x + 6 * side, cy),
                (base_x + 3 * side, cy + 2),
            ])
            pygame.draw.rect(surface, _NS_malzeroth.PALETTE["gold_light"],
                             (base_x + 2 * side, cy - 3, 2, 1))
            # Spike on top of pauldron.
            _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["bone_dark"], [
                (base_x + 2 * side, cy - 6),
                (base_x + 4 * side, cy - 12),
                (base_x + 6 * side, cy - 5),
            ])
            _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["bone_mid"], [
                (base_x + 3 * side, cy - 6),
                (base_x + 4 * side, cy - 11),
                (base_x + 5 * side, cy - 5),
            ])
            pygame.draw.rect(surface, _NS_malzeroth.PALETTE["bone_light"],
                             (base_x + 4 * side, cy - 11, 1, 1))
    def _draw_arms_and_staff(surface, cx, cy, facing, phase, action, progress):
        """Two arms: one holds staff, other casts spells."""
        # Arm raise animation.
        cast_lift = 0
        if action == "attack":
            if progress < 0.4:
                cast_lift = int(progress / 0.4 * 8)
            elif progress < 0.7:
                cast_lift = 8
            else:
                cast_lift = int(8 * (1 - (progress - 0.7) / 0.3))
        # LEFT ARM - holds staff (back arm).
        staff_arm_x = cx - facing * 10
        staff_arm_y = cy - 6
        # Upper arm.
        pygame.draw.line(surface, _NS_malzeroth.PALETTE["skin_darkest"],
                         (staff_arm_x, staff_arm_y - 2),
                         (staff_arm_x - facing * 4, staff_arm_y + 6), 5)
        pygame.draw.line(surface, _NS_malzeroth.PALETTE["skin_dark"],
                         (staff_arm_x, staff_arm_y - 2),
                         (staff_arm_x - facing * 4, staff_arm_y + 6), 3)
        # Forearm.
        pygame.draw.line(surface, _NS_malzeroth.PALETTE["skin_darkest"],
                         (staff_arm_x - facing * 4, staff_arm_y + 6),
                         (staff_arm_x - facing * 8, staff_arm_y - 4), 5)
        pygame.draw.line(surface, _NS_malzeroth.PALETTE["skin_dark"],
                         (staff_arm_x - facing * 4, staff_arm_y + 6),
                         (staff_arm_x - facing * 8, staff_arm_y - 4), 3)
        # Staff (long).
        staff_top_x = staff_arm_x - facing * 8
        staff_top_y = staff_arm_y - 32
        staff_bot_x = staff_arm_x - facing * 8
        staff_bot_y = staff_arm_y + 22
        # Staff shaft.
        pygame.draw.line(surface, _NS_malzeroth.PALETTE["shadow_deep"],
                         (staff_top_x + 1, staff_top_y + 1),
                         (staff_bot_x + 1, staff_bot_y + 1), 4)
        pygame.draw.line(surface, _NS_malzeroth.PALETTE["wood_dark"],
                         (staff_top_x, staff_top_y),
                         (staff_bot_x, staff_bot_y), 3)
        pygame.draw.line(surface, _NS_malzeroth.PALETTE["wood_mid"],
                         (staff_top_x, staff_top_y),
                         (staff_bot_x, staff_bot_y), 2)
        pygame.draw.line(surface, _NS_malzeroth.PALETTE["wood_light"],
                         (staff_top_x - 1, staff_top_y),
                         (staff_bot_x - 1, staff_bot_y), 1)
        # Staff head - gold orb holder + crystal.
        _NS_malzeroth._draw_staff_head(surface, staff_top_x, staff_top_y, phase)
        # RIGHT ARM - casting arm (front).
        cast_arm_x = cx + facing * 10
        cast_arm_y = cy - 6 - cast_lift
        # Upper arm.
        pygame.draw.line(surface, _NS_malzeroth.PALETTE["skin_darkest"],
                         (cast_arm_x, cast_arm_y),
                         (cast_arm_x + facing * 6, cast_arm_y + 4), 5)
        pygame.draw.line(surface, _NS_malzeroth.PALETTE["skin_dark"],
                         (cast_arm_x, cast_arm_y),
                         (cast_arm_x + facing * 6, cast_arm_y + 4), 3)
        pygame.draw.line(surface, _NS_malzeroth.PALETTE["skin_mid"],
                         (cast_arm_x, cast_arm_y - 1),
                         (cast_arm_x + facing * 6, cast_arm_y + 3), 1)
        # Forearm (extending forward).
        forearm_end_x = cast_arm_x + facing * 14
        forearm_end_y = cast_arm_y - 2 - cast_lift // 2
        pygame.draw.line(surface, _NS_malzeroth.PALETTE["skin_darkest"],
                         (cast_arm_x + facing * 6, cast_arm_y + 4),
                         (forearm_end_x, forearm_end_y), 5)
        pygame.draw.line(surface, _NS_malzeroth.PALETTE["skin_dark"],
                         (cast_arm_x + facing * 6, cast_arm_y + 4),
                         (forearm_end_x, forearm_end_y), 3)
        pygame.draw.line(surface, _NS_malzeroth.PALETTE["skin_mid"],
                         (cast_arm_x + facing * 6, cast_arm_y + 3),
                         (forearm_end_x, forearm_end_y - 1), 1)
        # Claw hand.
        _NS_malzeroth._draw_claw_hand(surface, forearm_end_x, forearm_end_y,
                                       facing, phase, action)
        # Store hand position for spell FX.
        boss = None  # not used
    def _draw_staff_head(surface, sx, sy, phase):
        """Ornate staff head with floating crystal."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Gold clawed holder.
        _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["gold_dark"], [
            (sx - 4, sy + 2),
            (sx - 5, sy - 3),
            (sx - 2, sy - 6),
            (sx + 2, sy - 6),
            (sx + 5, sy - 3),
            (sx + 4, sy + 2),
        ])
        _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["gold_mid"], [
            (sx - 3, sy + 1),
            (sx - 4, sy - 2),
            (sx - 1, sy - 5),
            (sx + 1, sy - 5),
            (sx + 4, sy - 2),
            (sx + 3, sy + 1),
        ])
        pygame.draw.rect(surface, _NS_malzeroth.PALETTE["gold_light"], (sx - 1, sy - 4, 2, 1))
        # Purple crystal floating in holder.
        crystal_y = sy - 10 + int(math.sin(phase * 1.5) * 1)
        # Crystal glow.
        for r in range(9, 0, -1):
            alpha = _NS_malzeroth._alpha(80 * (9 - r) / 9 * pulse)
            _NS_malzeroth._aacircle(surface,
                                    (*_NS_malzeroth.PALETTE["crystal_mid"], alpha),
                                    (sx, crystal_y), r)
        # Crystal shape (diamond).
        _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["crystal_darkest"], [
            (sx, crystal_y - 5),
            (sx - 3, crystal_y),
            (sx, crystal_y + 5),
            (sx + 3, crystal_y),
        ])
        _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["crystal_dark"], [
            (sx, crystal_y - 4),
            (sx - 2, crystal_y),
            (sx, crystal_y + 4),
            (sx + 2, crystal_y),
        ])
        _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["crystal_mid"], [
            (sx, crystal_y - 3),
            (sx - 1, crystal_y),
            (sx, crystal_y + 3),
            (sx + 1, crystal_y),
        ])
        pygame.draw.rect(surface, _NS_malzeroth.PALETTE["crystal_light"], (sx, crystal_y - 1, 1, 1))
        pygame.draw.rect(surface, _NS_malzeroth.PALETTE["crystal_shine"], (sx, crystal_y - 2, 1, 1))
        # Sparkles around crystal.
        for i in range(4):
            angle = phase * 3 + i * math.pi / 2
            spark_x = sx + int(math.cos(angle) * 7)
            spark_y = crystal_y + int(math.sin(angle) * 7)
            pygame.draw.rect(surface, _NS_malzeroth.PALETTE["crystal_shine"],
                             (spark_x, spark_y, 1, 1))
    def _draw_claw_hand(surface, hx, hy, facing, phase, action):
        """Demon clawed hand."""
        # Palm.
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["skin_darkest"], (hx, hy), 3)
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["skin_dark"], (hx, hy), 2)
        pygame.draw.rect(surface, _NS_malzeroth.PALETTE["skin_mid"], (hx, hy - 1, 1, 1))
        # 3 claws extending.
        for i, angle_off in enumerate((-0.4, 0, 0.4)):
            angle = angle_off
            claw_len = 5
            end_x = hx + int(math.cos(angle) * claw_len) * facing
            end_y = hy + int(math.sin(angle) * claw_len)
            pygame.draw.line(surface, _NS_malzeroth.PALETTE["bone_dark"],
                             (hx, hy), (end_x, end_y), 2)
            pygame.draw.line(surface, _NS_malzeroth.PALETTE["bone_mid"],
                             (hx, hy), (end_x, end_y), 1)
            pygame.draw.rect(surface, _NS_malzeroth.PALETTE["bone_light"],
                             (end_x, end_y, 1, 1))
        # Casting glow at hand during attack.
        if action == "attack":
            for r in range(6, 0, -1):
                alpha = _NS_malzeroth._alpha(120 * (6 - r) / 6)
                _NS_malzeroth._aacircle(surface,
                                        (*_NS_malzeroth.PALETTE["crystal_mid"], alpha),
                                        (hx + facing * 3, hy), r)
    def _draw_head(surface, cx, cy, facing, phase, action, progress):
        """Demon head with horns, yellow eyes, fangs."""
        # Skull/face.
        face_pts = [
            (cx - 8, cy - 6),
            (cx - 10, cy - 2),
            (cx - 9, cy + 4),
            (cx - 5, cy + 8),
            (cx + 5, cy + 8),
            (cx + 9, cy + 4),
            (cx + 10, cy - 2),
            (cx + 8, cy - 6),
            (cx + 4, cy - 8),
            (cx - 4, cy - 8),
        ]
        _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in face_pts])
        _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["skin_darkest"], face_pts)
        _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["skin_dark"], [
            (cx - 7, cy - 5),
            (cx - 9, cy - 1),
            (cx - 8, cy + 3),
            (cx - 4, cy + 7),
            (cx + 4, cy + 7),
            (cx + 8, cy + 3),
            (cx + 9, cy - 1),
            (cx + 7, cy - 5),
            (cx + 3, cy - 7),
            (cx - 3, cy - 7),
        ])
        # Cheek highlights.
        _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["skin_mid"], [
            (cx - 5, cy - 3),
            (cx - 6, cy + 1),
            (cx - 3, cy + 4),
            (cx - 1, cy),
        ])
        _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["skin_mid"], [
            (cx + 5, cy - 3),
            (cx + 6, cy + 1),
            (cx + 3, cy + 4),
            (cx + 1, cy),
        ])
        pygame.draw.rect(surface, _NS_malzeroth.PALETTE["skin_light"], (cx - 4, cy - 4, 1, 1))
        pygame.draw.rect(surface, _NS_malzeroth.PALETTE["skin_light"], (cx + 3, cy - 4, 1, 1))
        # Horns (2 large curved back horns).
        _NS_malzeroth._draw_horns(surface, cx, cy, facing, phase)
        # Eyes (glowing yellow).
        _NS_malzeroth._draw_demon_eyes(surface, cx, cy, phase, action)
        # Nose + mouth with fangs.
        _NS_malzeroth._draw_demon_mouth(surface, cx, cy, phase, action, progress)
    def _draw_horns(surface, cx, cy, facing, phase):
        """Two curved horns going up and back."""
        sway = math.sin(phase * 0.3) * 0.5
        for side in (-1, 1):
            # Base of horn.
            base_x = cx + side * 6
            base_y = cy - 6
            # Curved horn tip.
            tip_x = cx + side * 10
            tip_y = cy - 18
            # Horn body.
            _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["shadow_deep"], [
                (base_x - side * 2 + 1, base_y + 1),
                (base_x + side * 3 + 1, base_y - 2 + 1),
                (tip_x + 1, tip_y + 1),
                (tip_x - side * 2 + 1, tip_y + 3 + 1),
            ])
            _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["bone_dark"], [
                (base_x - side * 2, base_y),
                (base_x + side * 3, base_y - 2),
                (tip_x, tip_y),
                (tip_x - side * 2, tip_y + 3),
            ])
            _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["bone_mid"], [
                (base_x - side, base_y - 1),
                (base_x + side * 2, base_y - 2),
                (tip_x - side, tip_y + 1),
                (tip_x - side * 2, tip_y + 2),
            ])
            # Horn ridges.
            for ridge_i in range(3):
                ry = base_y - 3 - ridge_i * 4
                pygame.draw.line(surface, _NS_malzeroth.PALETTE["bone_dark"],
                                 (base_x + side * (2 - ridge_i), ry),
                                 (base_x + side * (3 - ridge_i), ry - 1), 1)
            # Sharp tip.
            pygame.draw.rect(surface, _NS_malzeroth.PALETTE["bone_light"], (tip_x, tip_y, 1, 1))
            # Small side spike.
            _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["bone_dark"], [
                (base_x + side * 4, base_y - 4),
                (base_x + side * 7, base_y - 8),
                (base_x + side * 5, base_y - 3),
            ])
            _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["bone_mid"], [
                (base_x + side * 5, base_y - 4),
                (base_x + side * 6, base_y - 7),
                (base_x + side * 5, base_y - 3),
            ])
    def _draw_demon_eyes(surface, cx, cy, phase, action):
        """Glowing yellow eyes."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        eye_intensity = 1.3 if action == "attack" else 1.0
        for side in (-1, 1):
            ex = cx + side * 3
            ey = cy - 1
            # Eye socket.
            pygame.draw.rect(surface, _NS_malzeroth.PALETTE["eye_socket"],
                             (ex - 1, ey - 1, 3, 3))
            # Glow halo.
            for r in range(5, 0, -1):
                alpha = _NS_malzeroth._alpha(100 * (5 - r) / 5 * pulse * eye_intensity)
                _NS_malzeroth._aacircle(surface,
                                        (*_NS_malzeroth.PALETTE["eye_mid"], alpha),
                                        (ex, ey), r)
            # Eye core.
            pygame.draw.rect(surface, _NS_malzeroth.PALETTE["eye_dark"], (ex - 1, ey, 3, 1))
            pygame.draw.rect(surface, _NS_malzeroth.PALETTE["eye_mid"], (ex, ey, 2, 1))
            pygame.draw.rect(surface, _NS_malzeroth.PALETTE["eye_light"], (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_malzeroth.PALETTE["eye_glow"], (ex, ey, 1, 1))
    def _draw_demon_mouth(surface, cx, cy, phase, action, progress):
        """Fanged mouth."""
        mouth_open = 0
        if action == "attack":
            mouth_open = max(0, math.sin(progress * math.pi) * 3)
        # Nose bridge.
        pygame.draw.line(surface, _NS_malzeroth.PALETTE["skin_darkest"],
                         (cx, cy + 1), (cx, cy + 3), 1)
        if mouth_open > 0:
            # Open mouth.
            _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["shadow_deep"], [
                (cx - 3, cy + 4),
                (cx + 3, cy + 4),
                (cx + 2, cy + 4 + int(mouth_open)),
                (cx - 2, cy + 4 + int(mouth_open)),
            ])
            # Inner red glow.
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["cloak_dark"],
                                    (cx, cy + 5), max(1, int(mouth_open) - 1))
            # Upper fangs.
            for x_off in (-2, 0, 2):
                pygame.draw.line(surface, _NS_malzeroth.PALETTE["bone_dark"],
                                 (cx + x_off, cy + 4),
                                 (cx + x_off, cy + 4 + int(mouth_open) - 1), 1)
                pygame.draw.rect(surface, _NS_malzeroth.PALETTE["bone_light"],
                                 (cx + x_off, cy + 4 + int(mouth_open) - 1, 1, 1))
        else:
            # Closed grin.
            pygame.draw.line(surface, _NS_malzeroth.PALETTE["shadow_deep"],
                             (cx - 3, cy + 4), (cx + 3, cy + 4), 1)
            # Visible fangs.
            for x_off in (-2, 2):
                pygame.draw.rect(surface, _NS_malzeroth.PALETTE["bone_mid"],
                                 (cx + x_off, cy + 4, 1, 2))
                pygame.draw.rect(surface, _NS_malzeroth.PALETTE["bone_light"],
                                 (cx + x_off, cy + 5, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        """Shadow beneath floating character (breathes)."""
        breath = math.sin(phase * 0.6) * 0.15 + 0.85
        shadow = pygame.Surface((100, 24), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, int((10 - radius) * 18 * breath))
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 12 - radius,
                                 80 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (5, 3, 15, int(150 * breath)),
                            (10, 8, 80, 8))
        surface.blit(shadow, (x - 50, y - 12))
    def _draw_floating_dust(surface, cx, cy, phase):
        """Small floating dust particles under character."""
        for i in range(6):
            t = (phase * 0.4 + i * 0.17) % 1.0
            dx = cx + int(math.sin(phase + i * 0.7) * 20) - 10 + i * 3
            dy = cy - int(t * 15)
            alpha = _NS_malzeroth._alpha(200 * (1 - t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_malzeroth.PALETTE["crystal_mid"], alpha),
                                 (dx, dy, 1, 1))
                pygame.draw.rect(surface, (*_NS_malzeroth.PALETTE["crystal_light"], alpha),
                                 (dx, dy - 1, 1, 1))
    def _draw_demon_aura(surface, x, y, phase):
        """Dark purple aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(75, 5, -5):
            alpha = _NS_malzeroth._alpha((75 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_malzeroth._aacircle(aura,
                                        (*_NS_malzeroth.PALETTE["crystal_darkest"], alpha),
                                        (90, 80), radius)
        for radius in range(45, 5, -4):
            alpha = _NS_malzeroth._alpha((45 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_malzeroth._aacircle(aura,
                                        (*_NS_malzeroth.PALETTE["crystal_dark"], alpha),
                                        (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))
        # Floating purple sparks around.
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            radius = 32 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_malzeroth.PALETTE["crystal_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_malzeroth.PALETTE["crystal_shine"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Runic ground ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_malzeroth.PALETTE["crystal_darkest"], 200),
                            (5, 15, 150, 22), 3)
        pygame.draw.ellipse(ring, (*_NS_malzeroth.PALETTE["crystal_dark"], 220),
                            (14, 17, 132, 18), 2)
        pygame.draw.ellipse(ring, (*_NS_malzeroth.PALETTE["crystal_mid"], 180),
                            (25, 19, 110, 14), 1)
        # Runes.
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 26 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 66)
            y2 = 26 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_malzeroth.PALETTE["crystal_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_malzeroth.PALETTE["crystal_shine"],
                                       _NS_malzeroth._alpha(150 * pulse)),
                                (15, 10, 130, 34), 1)
        surface.blit(ring, (x - 80, y - 25))
    # ============================================================
    # BASIC ATTACK PROJECTILE (purple bolt)
    # ============================================================
    def _draw_basic_projectile(surface, boss, x, y):
        """Bolt ungu dari KRISTAL TONGKAT menuju target."""
        progress = getattr(boss, "_mz_attack_progress", 0.0)
        facing = boss.direction
        # Sumber = kristal tongkat.
        sx, sy = _NS_malzeroth._staff_crystal_position(boss, x, y)
        if progress < 0.35:
            # Charge up di kristal tongkat.
            t = progress / 0.35
            cr = int(3 + t * 6)
            # Aura membesar.
            for r in range(cr + 5, 0, -1):
                alpha = _NS_malzeroth._alpha(180 * (cr + 5 - r) / (cr + 5))
                _NS_malzeroth._aacircle(surface,
                                        (*_NS_malzeroth.PALETTE["crystal_dark"], alpha),
                                        (sx, sy), r)
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["crystal_mid"], (sx, sy), max(1, cr - 1))
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["crystal_light"], (sx, sy), max(1, cr - 3))
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["crystal_shine"], (sx, sy), max(1, cr - 5))
            # Energy orbit around crystal.
            for i in range(5):
                angle = boss.pulse * 5 + i * math.pi * 2 / 5
                orbit_r = cr + 3
                ox = sx + int(math.cos(angle) * orbit_r)
                oy = sy + int(math.sin(angle) * orbit_r)
                pygame.draw.rect(surface, _NS_malzeroth.PALETTE["crystal_shine"], (ox, oy, 1, 1))
            return
        tx, ty = _NS_malzeroth._target_position(boss, x, y)
        # Progress projectile 0.35 → 1.0.
        t = (progress - 0.35) / 0.65
        t = max(0.0, min(1.0, t))
        bx = int(sx + (tx - sx) * t)
        by = int(sy + (ty - sy) * t)
        # Trail (comet).
        for i in range(9):
            trail_t = max(0.0, t - i * 0.05)
            px = int(sx + (tx - sx) * trail_t)
            py = int(sy + (ty - sy) * trail_t)
            alpha = _NS_malzeroth._alpha(230 - i * 24)
            size = max(1, 6 - i)
            _NS_malzeroth._aacircle(surface,
                                    (*_NS_malzeroth.PALETTE["crystal_darkest"], alpha),
                                    (px, py), size)
            _NS_malzeroth._aacircle(surface,
                                    (*_NS_malzeroth.PALETTE["crystal_dark"], alpha),
                                    (px, py), max(1, size - 1))
            _NS_malzeroth._aacircle(surface,
                                    (*_NS_malzeroth.PALETTE["crystal_mid"], alpha),
                                    (px, py), max(1, size - 2))
            _NS_malzeroth._aacircle(surface,
                                    (*_NS_malzeroth.PALETTE["crystal_light"], alpha),
                                    (px, py), max(1, size - 3))
            if i < 4:
                for s in range(2):
                    spark_x = px + int(math.sin(t * 8 + i + s) * (size + 1))
                    spark_y = py + int(math.cos(t * 8 + i + s) * (size + 1))
                    pygame.draw.rect(surface,
                                     (*_NS_malzeroth.PALETTE["crystal_shine"], alpha),
                                     (spark_x, spark_y, 1, 1))
        # Bright head.
        for r in range(11, 3, -2):
            alpha = _NS_malzeroth._alpha(70 * (11 - r) / 11)
            _NS_malzeroth._aacircle(surface,
                                    (*_NS_malzeroth.PALETTE["crystal_light"], alpha),
                                    (bx, by), r)
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["crystal_darkest"], (bx, by), 7)
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["crystal_dark"], (bx, by), 5)
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["crystal_mid"], (bx, by), 3)
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["crystal_light"], (bx, by), 2)
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["crystal_shine"], (bx, by), 1)
        pygame.draw.rect(surface, _NS_malzeroth.PALETTE["white"], (bx, by, 1, 1))
        # Impact splash.
        if t > 0.88:
            st = (t - 0.88) / 0.12
            radius = int(8 + st * 18)
            alpha = _NS_malzeroth._alpha(240 * (1 - st))
            _NS_malzeroth._aacircle(surface,
                                    (*_NS_malzeroth.PALETTE["crystal_darkest"], alpha),
                                    (tx, ty), radius + 2, 3)
            _NS_malzeroth._aacircle(surface,
                                    (*_NS_malzeroth.PALETTE["crystal_dark"], alpha),
                                    (tx, ty), radius, 2)
            _NS_malzeroth._aacircle(surface,
                                    (*_NS_malzeroth.PALETTE["crystal_mid"], alpha),
                                    (tx, ty), max(1, radius - 5), 2)
            _NS_malzeroth._aacircle(surface,
                                    (*_NS_malzeroth.PALETTE["crystal_light"], alpha),
                                    (tx, ty), max(1, radius - 10), 1)
            for i in range(8):
                angle_s = i * math.pi / 4
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface,
                                 (*_NS_malzeroth.PALETTE["crystal_shine"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # SKILL Q: EARTH SPIKE (ground crystals rise at target)
    # ============================================================
    def _draw_earthspike_ground(surface, boss, x, y, timer, phase):
        """Ground crack warning."""
        tx, ty = _NS_malzeroth._target_position(boss, x, y)
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.5:
            # Growing crack.
            t = progress / 0.5
            crack_r = int(10 * t)
            for i in range(4):
                angle = i * math.pi / 2 + phase * 0.5
                ex = tx + int(math.cos(angle) * crack_r)
                ey = ty + int(math.sin(angle) * crack_r * 0.4)
                pygame.draw.line(surface, (*_NS_malzeroth.PALETTE["crystal_dark"], 180),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface, _NS_malzeroth.PALETTE["crystal_light"],
                                 (ex, ey, 1, 1))
    def _draw_earthspike_projectile(surface, boss, x, y, timer, phase):
        """Purple crystal spike - projectile keluar dari KRISTAL TONGKAT."""
        tx, ty = _NS_malzeroth._target_position(boss, x, y)
        sx, sy = _NS_malzeroth._staff_crystal_position(boss, x, y)
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Charge di kristal tongkat.
            t = progress / 0.3
            cr = int(3 + t * 7)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_malzeroth._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_malzeroth._aacircle(surface,
                                        (*_NS_malzeroth.PALETTE["crystal_dark"], alpha),
                                        (sx, sy), r)
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["crystal_mid"], (sx, sy), cr - 1)
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["crystal_light"], (sx, sy), max(1, cr - 3))
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["crystal_shine"], (sx, sy), max(1, cr - 5))
            # Orbit sparks gathering into crystal.
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                orbit_r = int(cr + 6 - t * 3)
                ox = sx + int(math.cos(angle) * orbit_r)
                oy = sy + int(math.sin(angle) * orbit_r)
                pygame.draw.rect(surface, _NS_malzeroth.PALETTE["crystal_light"], (ox, oy, 2, 2))
                pygame.draw.rect(surface, _NS_malzeroth.PALETTE["crystal_shine"], (ox, oy, 1, 1))
        elif progress < 0.5:
            # Projectile terbang dari tongkat ke target.
            t = (progress - 0.3) / 0.2
            bx = int(sx + (tx - sx) * t)
            by = int(sy + (ty - sy) * t)
            for i in range(6):
                trail_t = max(0.0, t - i * 0.08)
                px = int(sx + (tx - sx) * trail_t)
                py = int(sy + (ty - sy) * trail_t)
                alpha = _NS_malzeroth._alpha(230 - i * 35)
                size = max(1, 5 - i)
                _NS_malzeroth._aacircle(surface,
                                        (*_NS_malzeroth.PALETTE["crystal_dark"], alpha),
                                        (px, py), size)
                _NS_malzeroth._aacircle(surface,
                                        (*_NS_malzeroth.PALETTE["crystal_light"], alpha),
                                        (px, py), max(1, size - 2))
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["crystal_darkest"], (bx, by), 7)
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["crystal_mid"], (bx, by), 4)
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["crystal_shine"], (bx, by), 2)
        else:
            # Crystal spike erupts from ground (di posisi target).
            t = (progress - 0.5) / 0.5
            spike_h = int(30 * min(1.0, t * 3))
            for i, (offset_x, size_mult) in enumerate([
                (0, 1.0), (-6, 0.7), (6, 0.7), (-3, 0.5), (3, 0.5),
            ]):
                spx = tx + offset_x
                spy = ty
                h = int(spike_h * size_mult)
                w = int(4 * size_mult)
                pts = [
                    (spx, spy - h),
                    (spx - w, spy - h // 2),
                    (spx - w // 2, spy),
                    (spx + w // 2, spy),
                    (spx + w, spy - h // 2),
                ]
                _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["shadow_deep"],
                                    [(p[0] + 1, p[1] + 1) for p in pts])
                _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["crystal_darkest"], pts)
                _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["crystal_dark"], [
                    (spx, spy - h + 1),
                    (spx - w + 1, spy - h // 2),
                    (spx, spy - 1),
                    (spx + w - 1, spy - h // 2),
                ])
                _NS_malzeroth._poly(surface, _NS_malzeroth.PALETTE["crystal_mid"], [
                    (spx, spy - h + 2),
                    (spx - w // 2, spy - h // 2),
                    (spx, spy - 2),
                ])
                pygame.draw.line(surface, _NS_malzeroth.PALETTE["crystal_light"],
                                 (spx, spy - h + 3), (spx, spy - 3), 1)
                pygame.draw.rect(surface, _NS_malzeroth.PALETTE["crystal_shine"],
                                 (spx, spy - h + 1, 1, 1))
            # Impact sparks.
            for i in range(10):
                angle = i * math.pi / 5
                sr = int(15 + t * 10)
                ex = tx + int(math.cos(angle) * sr)
                ey = ty + int(math.sin(angle) * sr * 0.5)
                alpha = _NS_malzeroth._alpha(220 * (1 - t))
                pygame.draw.rect(surface, (*_NS_malzeroth.PALETTE["crystal_shine"], alpha),
                                 (ex, ey, 2, 2))
    # ============================================================
    # SKILL W: HEX (green transformation beam)
    # ============================================================
    def _draw_hex_projectile(surface, boss, x, y, timer, phase):
        """Green hex projectile dari KRISTAL TONGKAT."""
        tx, ty = _NS_malzeroth._target_position(boss, x, y)
        sx, sy = _NS_malzeroth._staff_crystal_position(boss, x, y)
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.25:
            # Charge di kristal tongkat (kristal berubah hijau).
            t = progress / 0.25
            cr = int(3 + t * 6)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_malzeroth._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_malzeroth._aacircle(surface,
                                        (*_NS_malzeroth.PALETTE["hex_dark"], alpha),
                                        (sx, sy), r)
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hex_mid"], (sx, sy), cr - 1)
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hex_light"], (sx, sy), max(1, cr - 3))
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hex_shine"], (sx, sy), max(1, cr - 5))
            # Sparks berputar di sekitar kristal.
            for i in range(6):
                angle = phase * 5 + i * math.pi / 3
                orbit_r = cr + 4
                ox = sx + int(math.cos(angle) * orbit_r)
                oy = sy + int(math.sin(angle) * orbit_r)
                pygame.draw.rect(surface, _NS_malzeroth.PALETTE["hex_shine"], (ox, oy, 1, 1))
        else:
            # Traveling hex bolt dengan spiral.
            t = (progress - 0.25) / 0.75
            bx = int(sx + (tx - sx) * t)
            by = int(sy + (ty - sy) * t)
            # Wavy trail.
            for i in range(10):
                trail_t = max(0.0, t - i * 0.05)
                base_x = int(sx + (tx - sx) * trail_t)
                base_y = int(sy + (ty - sy) * trail_t)
                spiral = math.sin(trail_t * 15 + i * 0.5) * 4
                px = base_x
                py = base_y + int(spiral)
                alpha = _NS_malzeroth._alpha(230 - i * 22)
                size = max(1, 6 - i)
                _NS_malzeroth._aacircle(surface,
                                        (*_NS_malzeroth.PALETTE["hex_dark"], alpha),
                                        (px, py), size)
                _NS_malzeroth._aacircle(surface,
                                        (*_NS_malzeroth.PALETTE["hex_mid"], alpha),
                                        (px, py), max(1, size - 1))
                _NS_malzeroth._aacircle(surface,
                                        (*_NS_malzeroth.PALETTE["hex_light"], alpha),
                                        (px, py), max(1, size - 3))
            # Head.
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hex_darkest"], (bx, by), 7)
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hex_dark"], (bx, by), 5)
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hex_mid"], (bx, by), 3)
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hex_light"], (bx, by), 2)
            pygame.draw.rect(surface, _NS_malzeroth.PALETTE["hex_shine"], (bx, by, 1, 1))
            for r in range(10, 3, -2):
                alpha = _NS_malzeroth._alpha(80 * (10 - r) / 10)
                _NS_malzeroth._aacircle(surface,
                                        (*_NS_malzeroth.PALETTE["hex_light"], alpha),
                                        (bx, by), r)
            # Impact puff.
            if t > 0.9:
                st = (t - 0.9) / 0.1
                puff_r = int(20 * st)
                alpha = _NS_malzeroth._alpha(240 * (1 - st))
                _NS_malzeroth._aacircle(surface,
                                        (*_NS_malzeroth.PALETTE["hex_light"], alpha),
                                        (tx, ty), puff_r + 3)
                _NS_malzeroth._aacircle(surface,
                                        (*_NS_malzeroth.PALETTE["hex_shine"], alpha),
                                        (tx, ty), max(1, puff_r))
                for i in range(8):
                    angle = i * math.pi / 4
                    ex = tx + int(math.cos(angle) * puff_r)
                    ey = ty + int(math.sin(angle) * puff_r)
                    pygame.draw.rect(surface, _NS_malzeroth.PALETTE["hex_shine"], (ex, ey, 2, 2))
    # ============================================================
    # SKILL E: HP DRAIN (blood/vitality drain beam - red)
    # ============================================================
    def _draw_hp_drain_beam(surface, boss, x, y, timer, phase):
        """Beam merah darah dari KRISTAL TONGKAT ke target."""
        tx, ty = _NS_malzeroth._target_position(boss, x, y)
        # Sumber = kristal tongkat.
        start_x, start_y = _NS_malzeroth._staff_crystal_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Beam segments (wavy).
        segments = 24
        prev = (start_x, start_y)
        for i in range(1, segments + 1):
            t = i / segments
            base_x = int(start_x + (tx - start_x) * t)
            base_y = int(start_y + (ty - start_y) * t)
            dx = tx - start_x
            dy = ty - start_y
            length = max(1, math.sqrt(dx * dx + dy * dy))
            perp_x = -dy / length
            perp_y = dx / length
            wave = math.sin(phase * 5 + t * 14) * 5
            px = base_x + int(perp_x * wave)
            py = base_y + int(perp_y * wave)
            for width, color in [
                (6, _NS_malzeroth.PALETTE["hp_darkest"]),
                (4, _NS_malzeroth.PALETTE["hp_dark"]),
                (2, _NS_malzeroth.PALETTE["hp_mid"]),
                (1, _NS_malzeroth.PALETTE["hp_light"]),
            ]:
                pygame.draw.line(surface, color, prev, (px, py), width)
            prev = (px, py)
        # Blood droplets flowing FROM target TO staff crystal.
        for i in range(14):
            flow_t = ((phase * 0.6 + i * 0.07) % 1.0)
            t = 1.0 - flow_t
            base_x = int(start_x + (tx - start_x) * t)
            base_y = int(start_y + (ty - start_y) * t)
            dx = tx - start_x
            dy = ty - start_y
            length = max(1, math.sqrt(dx * dx + dy * dy))
            perp_x = -dy / length
            perp_y = dx / length
            wave = math.sin(phase * 5 + t * 14) * 5
            px = base_x + int(perp_x * wave)
            py = base_y + int(perp_y * wave)
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hp_darkest"], (px, py), 3)
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hp_dark"], (px, py), 2)
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hp_mid"], (px, py), 1)
            pygame.draw.rect(surface, _NS_malzeroth.PALETTE["hp_shine"], (px, py, 1, 1))
        # Bleeding glow at target.
        wound_pulse = math.sin(phase * 4) * 0.3 + 0.7
        for r in range(14, 0, -2):
            alpha = _NS_malzeroth._alpha(120 * (14 - r) / 14 * wound_pulse)
            _NS_malzeroth._aacircle(surface, (*_NS_malzeroth.PALETTE["hp_dark"], alpha),
                                    (tx, ty), r)
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hp_darkest"], (tx, ty), 6)
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hp_dark"], (tx, ty), 4)
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hp_mid"], (tx, ty), 3)
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hp_light"], (tx, ty), 2)
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hp_shine"], (tx, ty), 1)
        # Blood splatter around wound.
        for i in range(6):
            angle = phase * 2 + i * math.pi / 3
            spatter_r = int(10 + math.sin(phase * 3 + i) * 3)
            spx = tx + int(math.cos(angle) * spatter_r)
            spy = ty + int(math.sin(angle) * spatter_r)
            pygame.draw.rect(surface, _NS_malzeroth.PALETTE["hp_mid"], (spx, spy, 2, 2))
            pygame.draw.rect(surface, _NS_malzeroth.PALETTE["hp_dark"], (spx + 1, spy + 1, 1, 1))
        # Absorbing glow at staff crystal (kristal menyerap darah).
        heal_pulse = math.sin(phase * 3) * 0.3 + 0.7
        for r in range(12, 0, -1):
            alpha = _NS_malzeroth._alpha(140 * (12 - r) / 12 * heal_pulse)
            _NS_malzeroth._aacircle(surface, (*_NS_malzeroth.PALETTE["hp_dark"], alpha),
                                    (start_x, start_y), r)
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hp_darkest"], (start_x, start_y), 6)
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hp_dark"], (start_x, start_y), 4)
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hp_mid"], (start_x, start_y), 3)
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hp_light"], (start_x, start_y), 2)
        _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["hp_shine"], (start_x, start_y), 1)
        # Healing sparkles naik dari kristal tongkat.
        for i in range(5):
            heal_t = (phase * 0.5 + i * 0.2) % 1.0
            hx = start_x + int(math.sin(phase + i) * 6)
            hy = start_y - int(heal_t * 20)
            alpha = _NS_malzeroth._alpha(230 * (1 - heal_t))
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_malzeroth.PALETTE["hp_light"], alpha),
                                 (hx, hy, 2, 2))
                pygame.draw.rect(surface, (*_NS_malzeroth.PALETTE["hp_shine"], alpha),
                                 (hx, hy, 1, 1))
    # ============================================================
    # SKILL R: FINGER OF DEATH (massive red beam)
    # ============================================================
    def _draw_finger_ground(surface, boss, x, y, timer, phase):
        """Red impact ring at target."""
        tx, ty = _NS_malzeroth._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Warning circle.
            t = progress / 0.3
            r = int(20 * t)
            alpha = _NS_malzeroth._alpha(180 * t)
            pygame.draw.ellipse(surface, (*_NS_malzeroth.PALETTE["death_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_malzeroth.PALETTE["death_mid"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            # Runes.
            for i in range(6):
                angle = i * math.pi / 3 + phase * 0.5
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.4)
                pygame.draw.rect(surface, _NS_malzeroth.PALETTE["death_light"], (sx, sy, 2, 2))
        else:
            # Post-blast crater.
            t = (progress - 0.3) / 0.7
            r = int(25 + t * 10)
            alpha = _NS_malzeroth._alpha(220 * (1 - t * 0.5))
            pygame.draw.ellipse(surface, (*_NS_malzeroth.PALETTE["death_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_malzeroth.PALETTE["death_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_malzeroth.PALETTE["death_mid"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
    def _draw_finger_beam(surface, boss, x, y, timer, phase):
        """Massive red beam dari KRISTAL TONGKAT."""
        tx, ty = _NS_malzeroth._target_position(boss, x, y)
        start_x, start_y = _NS_malzeroth._staff_crystal_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Wind-up: intense red glow di kristal tongkat.
            t = progress / 0.3
            cr = int(5 + t * 10)
            for r in range(cr + 8, 0, -1):
                alpha = _NS_malzeroth._alpha(200 * (cr + 8 - r) / (cr + 8))
                _NS_malzeroth._aacircle(surface,
                                        (*_NS_malzeroth.PALETTE["death_darkest"], alpha),
                                        (start_x, start_y), r)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_malzeroth._alpha(220 * (cr + 4 - r) / (cr + 4))
                _NS_malzeroth._aacircle(surface,
                                        (*_NS_malzeroth.PALETTE["death_dark"], alpha),
                                        (start_x, start_y), r)
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["death_mid"], (start_x, start_y), cr - 1)
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["death_light"], (start_x, start_y), max(1, cr - 3))
            _NS_malzeroth._aacircle(surface, _NS_malzeroth.PALETTE["death_shine"], (start_x, start_y), max(1, cr - 5))
            # Energy converging to crystal.
            for i in range(10):
                angle = phase * 3 + i * math.pi / 5
                spark_dist = int(20 * (1 - t))
                spx = start_x + int(math.cos(angle) * spark_dist)
                spy = start_y + int(math.sin(angle) * spark_dist)
                pygame.draw.line(surface, _NS_malzeroth.PALETTE["death_light"],
                                 (spx, spy), (start_x, start_y), 1)
                pygame.draw.rect(surface, _NS_malzeroth.PALETTE["death_shine"], (spx, spy, 1, 1))
        elif progress < 0.7:
            # STRIKE.
            t = (progress - 0.3) / 0.4
            intensity = math.sin(t * math.pi)
            for layer_i, (width, color) in enumerate([
                (12, _NS_malzeroth.PALETTE["death_darkest"]),
                (8, _NS_malzeroth.PALETTE["death_dark"]),
                (5, _NS_malzeroth.PALETTE["death_mid"]),
                (3, _NS_malzeroth.PALETTE["death_light"]),
                (1, _NS_malzeroth.PALETTE["death_shine"]),
            ]):
                actual_alpha = _NS_malzeroth._alpha(255 * intensity)
                if actual_alpha <= 0:
                    continue
                pygame.draw.line(surface, (*color, actual_alpha),
                                 (start_x, start_y), (tx, ty), width)
            pygame.draw.line(surface, _NS_malzeroth.PALETTE["white"],
                             (start_x, start_y), (tx, ty), 1)
            # Sparks along beam.
            for i in range(12):
                spark_t = ((phase * 2 + i * 0.1) % 1.0)
                dx = tx - start_x
                dy = ty - start_y
                length = max(1, math.sqrt(dx * dx + dy * dy))
                perp_x = -dy / length
                perp_y = dx / length
                spx = int(start_x + dx * spark_t)
                spy = int(start_y + dy * spark_t)
                offset = math.sin(phase * 5 + i) * 6
                spx += int(perp_x * offset)
                spy += int(perp_y * offset)
                alpha = _NS_malzeroth._alpha(240 * intensity)
                pygame.draw.rect(surface, (*_NS_malzeroth.PALETTE["death_shine"], alpha),
                                 (spx, spy, 2, 2))
                pygame.draw.rect(surface, (*_NS_malzeroth.PALETTE["white"], alpha),
                                 (spx, spy, 1, 1))
            # Impact burst.
            impact_r = int(15 + t * 20)
            impact_alpha = _NS_malzeroth._alpha(240 * intensity)
            _NS_malzeroth._aacircle(surface, (*_NS_malzeroth.PALETTE["death_darkest"], impact_alpha),
                                    (tx, ty), impact_r + 3, 3)
            _NS_malzeroth._aacircle(surface, (*_NS_malzeroth.PALETTE["death_dark"], impact_alpha),
                                    (tx, ty), impact_r, 3)
            _NS_malzeroth._aacircle(surface, (*_NS_malzeroth.PALETTE["death_mid"], impact_alpha),
                                    (tx, ty), max(1, impact_r - 6), 2)
            _NS_malzeroth._aacircle(surface, (*_NS_malzeroth.PALETTE["death_light"], impact_alpha),
                                    (tx, ty), max(1, impact_r - 12), 1)
            _NS_malzeroth._aacircle(surface, (*_NS_malzeroth.PALETTE["death_shine"], impact_alpha),
                                    (tx, ty), max(1, impact_r // 4))
            for i in range(12):
                angle_s = i * math.pi / 6
                ex = tx + int(math.cos(angle_s) * impact_r)
                ey = ty + int(math.sin(angle_s) * impact_r * 0.7)
                pygame.draw.line(surface, (*_NS_malzeroth.PALETTE["death_light"], impact_alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_malzeroth.PALETTE["death_shine"], impact_alpha),
                                 (ex, ey, 2, 2))
        else:
            # Aftermath embers rising.
            t = (progress - 0.7) / 0.3
            for i in range(12):
                rise_t = (phase * 0.6 + i * 0.08) % 1.0
                rx = tx + int(math.sin(phase + i) * 18)
                ry = ty - int(rise_t * 25)
                alpha = _NS_malzeroth._alpha(200 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    pygame.draw.rect(surface, (*_NS_malzeroth.PALETTE["death_mid"], alpha),
                                     (rx, ry, 2, 2))
                    pygame.draw.rect(surface, (*_NS_malzeroth.PALETTE["death_shine"], alpha),
                                     (rx, ry, 1, 1))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_ghrakmaal(surface, boss, x, y):
    """Entry point ghrakmaal."""
    return _NS_ghrakmaal.draw_ghrakmaal(surface, boss, x, y)


def draw_selunara(surface, boss, x, y):
    """Entry point selunara."""
    return _NS_selunara.draw_selunara(surface, boss, x, y)


def draw_vessyra(surface, boss, x, y):
    """Entry point vessyra."""
    return _NS_vessyra.draw_vessyra(surface, boss, x, y)


def draw_malzeroth(surface, boss, x, y):
    """Entry point malzeroth."""
    return _NS_malzeroth.draw_malzeroth(surface, boss, x, y)
