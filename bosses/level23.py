"""
bosses/level23.py - Semua boss Level 23

Berisi:
  - drav          (mini boss - MELEE tideforged warden)
  - lyrienne      (mini boss - RANGED twilight chorister)
  - valthar       (mini boss - MELEE gold sentinel colossus)
  - seraphienne   (TRUE BOSS - RANGED empyrean executioner)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _drv_ (drav), _lyr_ (lyrienne), _val_ (valthar),
    _srp_ (seraphienne) sudah unik. Nama fungsi namespace (_draw_*)
    TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# DRAV (TIDEFORGED WARDEN) - Mini Boss
# ====================================================================

class _NS_drav:
    """Namespace drav - mini boss ocean armor dengan energy core biru."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Dark navy armor
        "armor_darkest": (5, 8, 18),
        "armor_dark": (18, 28, 50),
        "armor_mid": (45, 65, 100),
        "armor_light": (100, 130, 175),
        "armor_shine": (180, 210, 240),
        # Dark crevice (between plates)
        "crevice_darkest": (2, 3, 8),
        "crevice_dark": (10, 15, 25),
        # Core cyan (glowing energy)
        "core_darkest": (5, 30, 55),
        "core_dark": (20, 90, 155),
        "core_mid": (55, 175, 240),
        "core_light": (150, 230, 255),
        "core_hot": (220, 250, 255),
        "core_shine": (255, 255, 255),
        # Water/wave cyan
        "wave_darkest": (10, 40, 75),
        "wave_dark": (30, 110, 175),
        "wave_mid": (70, 190, 245),
        "wave_light": (170, 235, 255),
        # Gold trim (crown/anchor)
        "gold_darkest": (40, 25, 5),
        "gold_dark": (110, 75, 20),
        "gold_mid": (200, 155, 55),
        "gold_light": (250, 220, 120),
        "gold_shine": (255, 250, 220),
        # Iron chain (dark metal)
        "chain_darkest": (8, 10, 15),
        "chain_dark": (30, 35, 45),
        "chain_mid": (75, 85, 100),
        "chain_light": (140, 155, 175),
        # Anchor metal (dark iron+brass)
        "anchor_darkest": (10, 12, 20),
        "anchor_dark": (35, 40, 55),
        "anchor_mid": (85, 95, 115),
        "anchor_light": (150, 165, 190),
        "anchor_shine": (215, 225, 240),
        # Eye (glowing white-cyan)
        "eye_socket": (2, 8, 15),
        "eye_dark": (30, 80, 120),
        "eye_mid": (130, 210, 255),
        "eye_light": (220, 250, 255),
        "eye_glow": (255, 255, 255),
        # Ambient mist
        "mist_dark": (15, 30, 55),
        "mist_mid": (50, 100, 150),
        "mist_light": (140, 200, 235),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 6),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_drav._clamp(color)
        if _NS_drav.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_drav._clamp(color)
        if _NS_drav.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_drav._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 240 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_drav(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_drav._update_drv_attack_anim(boss)
        attacking = (
            getattr(boss, "_drv_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_drav._draw_ocean_aura(surface, x, y, pulse)
        _NS_drav._draw_ground_ring(surface, x, y + 54, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "r":
            _NS_drav._draw_vortex_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_drav._draw_tidalwave_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_drav._draw_chainlink_ground(surface, boss, x, y, skill_timer, pulse)
        # Body — floating with slow water bob
        floating_bob = math.sin(pulse * 0.6) * 5
        if attacking:
            _NS_drav._draw_drv_attack(surface, boss, x, y - floating_bob)
        else:
            _NS_drav._draw_drv_idle(surface, boss, x, y - floating_bob)
        # Foreground FX
        if active_skill == "q":
            _NS_drav._draw_anchor_throw_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_drav._draw_tidalwave_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_drav._draw_chainlink_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_drav._draw_vortex_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_drv_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 52)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_drv_previous_timer", 0))
        active = bool(getattr(boss, "_drv_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._drv_attack_active = True
            boss._drv_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._drv_attack_frame = int(getattr(boss, "_drv_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._drv_attack_active = False
            boss._drv_attack_frame = 0
            active = False
        boss._drv_previous_timer = timer
        boss._drv_attack_progress = (
            min(1.0, getattr(boss, "_drv_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_drv_idle(surface, boss, x, y):
        _NS_drav._draw_shadow(surface, x, y + 58)
        _NS_drav._draw_water_ripples(surface, x, y + 54, boss.pulse)
        _NS_drav._draw_floating_bubbles(surface, x, y + 30, boss.pulse)
        _NS_drav._draw_drv_body(surface, x, y, boss.direction, boss.pulse, "idle")
    def _draw_drv_attack(surface, boss, x, y):
        progress = getattr(boss, "_drv_attack_progress", 0.0)
        # Big anchor swing: wind-up → slam → recovery
        if progress < 0.35:
            t = progress / 0.35
            swing_offset = -int(t * 4) * boss.direction
            lift = int(t * 5)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            swing_offset = int((-4 + t * 14)) * boss.direction
            lift = int(5 - t * 9)
        else:
            t = (progress - 0.6) / 0.4
            swing_offset = int(10 * (1 - t)) * boss.direction
            lift = int(-4 + t * 4)
        _NS_drav._draw_shadow(surface, x + swing_offset, y + 58)
        _NS_drav._draw_water_ripples(surface, x + swing_offset, y + 54, boss.pulse,
                                      intense=True)
        _NS_drav._draw_floating_bubbles(surface, x + swing_offset, y + 30, boss.pulse,
                                         intense=True)
        _NS_drav._draw_drv_body(surface, x + swing_offset, y - lift,
                                 boss.direction, boss.pulse, "attack", progress)
        _NS_drav._draw_anchor_swing_slash(surface, x + swing_offset, y - lift,
                                           boss.direction, progress)
    # ============================================================
    # BODY (humanoid armor with anchor)
    # ============================================================
    def _draw_drv_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw armor body: back chains → legs → torso → arms → shoulder → head → crown."""
        _NS_drav._draw_back_chains(surface, cx, cy - 4, facing, phase)
        _NS_drav._draw_armor_legs(surface, cx, cy + 22, facing, phase)
        _NS_drav._draw_armor_torso(surface, cx, cy, facing, phase)
        _NS_drav._draw_armor_arms(surface, cx, cy, facing, phase, action, attack_progress)
        _NS_drav._draw_shoulder_pauldrons(surface, cx, cy - 8, facing, phase)
        # Head lunge on attack
        head_lunge = 0
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                head_lunge = -int(t * 2) * facing
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                head_lunge = int((-2 + t * 8)) * facing
            else:
                t = (attack_progress - 0.6) / 0.4
                head_lunge = int(6 * (1 - t)) * facing
        _NS_drav._draw_armor_head(surface, cx + head_lunge, cy - 24, facing, phase)
        _NS_drav._draw_gold_crown(surface, cx + head_lunge, cy - 32, facing, phase)
    def _draw_back_chains(surface, cx, cy, facing, phase):
        """Dangling chains from back with slight sway."""
        back_dir = -facing
        for chain_i, (base_off_x, base_off_y, length) in enumerate([
            (-6, -6, 24), (-10, -2, 28), (-8, 6, 22),
        ]):
            base_x = cx + back_dir * base_off_x
            base_y = cy + base_off_y
            sway = math.sin(phase * 1.2 + chain_i) * 3
            # Chain links (small circles connected)
            num_links = length // 3
            for i in range(num_links):
                t = i / num_links
                link_x = base_x + int(sway * t)
                link_y = base_y + int(length * t)
                # Chain link
                pygame.draw.circle(surface, _NS_drav.PALETTE["shadow_deep"],
                                   (link_x + 1, link_y + 1), 2)
                pygame.draw.circle(surface, _NS_drav.PALETTE["chain_darkest"],
                                   (link_x, link_y), 2)
                pygame.draw.circle(surface, _NS_drav.PALETTE["chain_dark"],
                                   (link_x, link_y), 1)
                pygame.draw.rect(surface, _NS_drav.PALETTE["chain_light"],
                                 (link_x, link_y - 1, 1, 1))
    def _draw_armor_legs(surface, cx, cy, facing, phase):
        """Short thick armored legs."""
        for side_mult in (-1, 1):
            leg_x = cx + side_mult * 9
            # Thigh
            _NS_drav._poly(surface, _NS_drav.PALETTE["shadow_deep"], [
                (leg_x - 6 + 2, cy - 8 + 2), (leg_x + 6 + 2, cy - 8 + 2),
                (leg_x + 7 + 2, cy + 5 + 2), (leg_x - 7 + 2, cy + 5 + 2),
            ])
            _NS_drav._poly(surface, _NS_drav.PALETTE["armor_darkest"], [
                (leg_x - 6, cy - 8), (leg_x + 6, cy - 8),
                (leg_x + 7, cy + 5), (leg_x - 7, cy + 5),
            ])
            _NS_drav._poly(surface, _NS_drav.PALETTE["armor_dark"], [
                (leg_x - 5, cy - 7), (leg_x + 5, cy - 7),
                (leg_x + 6, cy + 4), (leg_x - 6, cy + 4),
            ])
            _NS_drav._poly(surface, _NS_drav.PALETTE["armor_mid"], [
                (leg_x - 3, cy - 6), (leg_x + 3, cy - 6),
                (leg_x + 4, cy + 3), (leg_x - 4, cy + 3),
            ])
            _NS_drav._poly(surface, _NS_drav.PALETTE["armor_light"], [
                (leg_x - 2, cy - 5), (leg_x + 1, cy - 5),
                (leg_x + 2, cy + 2), (leg_x - 2, cy + 2),
            ])
            # Knee gold trim
            pygame.draw.rect(surface, _NS_drav.PALETTE["gold_dark"],
                             (leg_x - 7, cy, 14, 3))
            pygame.draw.rect(surface, _NS_drav.PALETTE["gold_mid"],
                             (leg_x - 6, cy + 1, 12, 1))
            pygame.draw.rect(surface, _NS_drav.PALETTE["gold_light"],
                             (leg_x - 1, cy + 1, 2, 1))
            # Cyan core on knee
            core_pulse = math.sin(phase * 2) * 0.3 + 0.7
            core_alpha = _NS_drav._alpha(220 * core_pulse)
            _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_dark"], core_alpha),
                                (leg_x, cy + 1), 3)
            _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_mid"], core_alpha),
                                (leg_x, cy + 1), 2)
            pygame.draw.rect(surface, _NS_drav.PALETTE["core_light"], (leg_x, cy + 1, 1, 1))
            # Lower leg / boot
            _NS_drav._poly(surface, _NS_drav.PALETTE["shadow_deep"], [
                (leg_x - 7 + 2, cy + 5 + 2), (leg_x + 7 + 2, cy + 5 + 2),
                (leg_x + 8 + 2, cy + 16 + 2), (leg_x - 8 + 2, cy + 16 + 2),
            ])
            _NS_drav._poly(surface, _NS_drav.PALETTE["armor_darkest"], [
                (leg_x - 7, cy + 5), (leg_x + 7, cy + 5),
                (leg_x + 8, cy + 16), (leg_x - 8, cy + 16),
            ])
            _NS_drav._poly(surface, _NS_drav.PALETTE["armor_dark"], [
                (leg_x - 6, cy + 6), (leg_x + 6, cy + 6),
                (leg_x + 7, cy + 15), (leg_x - 7, cy + 15),
            ])
            _NS_drav._poly(surface, _NS_drav.PALETTE["armor_mid"], [
                (leg_x - 4, cy + 8), (leg_x + 4, cy + 8),
                (leg_x + 5, cy + 13), (leg_x - 5, cy + 13),
            ])
            # Boot gold trim
            pygame.draw.rect(surface, _NS_drav.PALETTE["gold_dark"],
                             (leg_x - 8, cy + 14, 16, 3))
            pygame.draw.rect(surface, _NS_drav.PALETTE["gold_mid"],
                             (leg_x - 7, cy + 15, 14, 1))
    def _draw_armor_torso(surface, cx, cy, facing, phase):
        """Massive tank torso with BIG glowing cyan core in center chest."""
        breath = math.sin(phase * 0.5) * 1
        # Big blocky torso
        torso_shape = [
            (cx - 20, cy + 18),
            (cx - 24, cy + 6),
            (cx - 26, cy - 4 - int(breath)),
            (cx - 22, cy - 14),
            (cx - 12, cy - 17),
            (cx - 6, cy - 19),
            (cx + 6, cy - 19),
            (cx + 12, cy - 17),
            (cx + 22, cy - 14),
            (cx + 26, cy - 4 - int(breath)),
            (cx + 24, cy + 6),
            (cx + 20, cy + 18),
            (cx + 10, cy + 22),
            (cx - 10, cy + 22),
        ]
        _NS_drav._poly(surface, _NS_drav.PALETTE["shadow_deep"],
                        [(px + 2, py + 3) for px, py in torso_shape])
        _NS_drav._poly(surface, _NS_drav.PALETTE["armor_darkest"], torso_shape)
        # Main armor plate
        _NS_drav._poly(surface, _NS_drav.PALETTE["armor_dark"], [
            (cx - 19, cy + 17), (cx - 22, cy + 5), (cx - 24, cy - 3),
            (cx - 20, cy - 13), (cx - 10, cy - 16), (cx + 10, cy - 16),
            (cx + 20, cy - 13), (cx + 24, cy - 3), (cx + 22, cy + 5),
            (cx + 19, cy + 17), (cx + 9, cy + 20), (cx - 9, cy + 20),
        ])
        _NS_drav._poly(surface, _NS_drav.PALETTE["armor_mid"], [
            (cx - 16, cy + 15), (cx - 19, cy + 3), (cx - 21, cy - 2),
            (cx - 17, cy - 12), (cx - 6, cy - 13), (cx + 6, cy - 13),
            (cx + 17, cy - 12), (cx + 21, cy - 2), (cx + 19, cy + 3),
            (cx + 16, cy + 15), (cx + 7, cy + 18), (cx - 7, cy + 18),
        ])
        # Highlight
        _NS_drav._poly(surface, _NS_drav.PALETTE["armor_light"], [
            (cx - 4, cy - 10), (cx + 4, cy - 10), (cx + 6, cy - 6),
            (cx + 4, cy - 2), (cx - 4, cy - 2), (cx - 6, cy - 6),
        ])
        # Plate fracture lines (armor segments)
        for pts in [
            [(cx - 18, cy - 8), (cx - 12, cy - 4), (cx - 16, cy + 6),
             (cx - 14, cy + 15)],
            [(cx + 18, cy - 8), (cx + 12, cy - 4), (cx + 16, cy + 6),
             (cx + 14, cy + 15)],
        ]:
            for i in range(len(pts) - 1):
                pygame.draw.line(surface, _NS_drav.PALETTE["crevice_dark"],
                                 pts[i], pts[i + 1], 1)
        # 💠 HUGE CYAN CORE in center chest (SIGNATURE feature)
        _NS_drav._draw_chest_core(surface, cx, cy - 2, phase)
        # Gold trim borders
        # Belt
        pygame.draw.rect(surface, _NS_drav.PALETTE["gold_dark"],
                         (cx - 20, cy + 14, 40, 4))
        pygame.draw.rect(surface, _NS_drav.PALETTE["gold_mid"],
                         (cx - 19, cy + 15, 38, 2))
        pygame.draw.rect(surface, _NS_drav.PALETTE["gold_light"],
                         (cx - 2, cy + 15, 4, 1))
        # Central belt buckle (with small core)
        pygame.draw.rect(surface, _NS_drav.PALETTE["gold_darkest"],
                         (cx - 5, cy + 13, 10, 7))
        pygame.draw.rect(surface, _NS_drav.PALETTE["gold_dark"],
                         (cx - 4, cy + 14, 8, 5))
        pygame.draw.rect(surface, _NS_drav.PALETTE["gold_mid"],
                         (cx - 3, cy + 15, 6, 3))
        # Belt buckle core
        pygame.draw.rect(surface, _NS_drav.PALETTE["core_dark"], (cx - 2, cy + 16, 4, 2))
        pygame.draw.rect(surface, _NS_drav.PALETTE["core_light"], (cx - 1, cy + 16, 2, 1))
        pygame.draw.rect(surface, _NS_drav.PALETTE["core_shine"], (cx, cy + 16, 1, 1))
        # Neck trim
        pygame.draw.rect(surface, _NS_drav.PALETTE["gold_dark"],
                         (cx - 7, cy - 18, 14, 2))
        pygame.draw.rect(surface, _NS_drav.PALETTE["gold_mid"],
                         (cx - 6, cy - 17, 12, 1))
    def _draw_chest_core(surface, cx, cy, phase):
        """Massive glowing cyan energy core in center of chest."""
        core_pulse = math.sin(phase * 1.5) * 0.35 + 0.65
        # Deep socket
        core_shape = [
            (cx - 8, cy - 4), (cx - 10, cy + 2), (cx - 6, cy + 10),
            (cx + 6, cy + 10), (cx + 10, cy + 2), (cx + 8, cy - 4),
        ]
        _NS_drav._poly(surface, _NS_drav.PALETTE["shadow_deep"],
                        [(px + 1, py + 1) for px, py in core_shape])
        _NS_drav._poly(surface, _NS_drav.PALETTE["crevice_darkest"], core_shape)
        # Layered glow (largest to smallest)
        for r in range(14, 0, -1):
            alpha = _NS_drav._alpha(80 * (14 - r) / 14 * core_pulse)
            _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_light"], alpha),
                                (cx, cy + 3), r)
        # Inner core body
        _NS_drav._poly(surface, _NS_drav.PALETTE["core_darkest"], [
            (cx - 7, cy - 3), (cx - 9, cy + 2), (cx - 5, cy + 9),
            (cx + 5, cy + 9), (cx + 9, cy + 2), (cx + 7, cy - 3),
        ])
        _NS_drav._poly(surface, _NS_drav.PALETTE["core_dark"], [
            (cx - 6, cy - 2), (cx - 8, cy + 2), (cx - 4, cy + 8),
            (cx + 4, cy + 8), (cx + 8, cy + 2), (cx + 6, cy - 2),
        ])
        _NS_drav._poly(surface, _NS_drav.PALETTE["core_mid"], [
            (cx - 4, cy - 1), (cx - 6, cy + 2), (cx - 3, cy + 6),
            (cx + 3, cy + 6), (cx + 6, cy + 2), (cx + 4, cy - 1),
        ])
        _NS_drav._poly(surface, _NS_drav.PALETTE["core_light"], [
            (cx - 3, cy), (cx - 4, cy + 2), (cx - 2, cy + 5),
            (cx + 2, cy + 5), (cx + 4, cy + 2), (cx + 3, cy),
        ])
        # Bright center
        _NS_drav._aacircle(surface, _NS_drav.PALETTE["core_hot"], (cx, cy + 2), 3)
        _NS_drav._aacircle(surface, _NS_drav.PALETTE["core_shine"], (cx, cy + 2), 2)
        pygame.draw.rect(surface, _NS_drav.PALETTE["white"], (cx, cy + 2, 1, 1))
        # Anchor symbol overlay (dark silhouette on core)
        # Anchor top ring
        anchor_alpha = _NS_drav._alpha(180)
        pygame.draw.circle(surface, (*_NS_drav.PALETTE["shadow_deep"], anchor_alpha),
                           (cx, cy - 1), 2, 1)
        # Vertical bar
        pygame.draw.line(surface, (*_NS_drav.PALETTE["shadow_deep"], anchor_alpha),
                         (cx, cy), (cx, cy + 5), 1)
        # Horizontal bar
        pygame.draw.line(surface, (*_NS_drav.PALETTE["shadow_deep"], anchor_alpha),
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)
        # Bottom hooks
        pygame.draw.line(surface, (*_NS_drav.PALETTE["shadow_deep"], anchor_alpha),
                         (cx - 3, cy + 5), (cx - 2, cy + 6), 1)
        pygame.draw.line(surface, (*_NS_drav.PALETTE["shadow_deep"], anchor_alpha),
                         (cx + 3, cy + 5), (cx + 2, cy + 6), 1)
        # Rotating swirl inside core
        for i in range(3):
            swirl_ang = phase * 2 + i * math.pi * 2 / 3
            sr = 3
            sx = cx + int(math.cos(swirl_ang) * sr)
            sy = cy + 3 + int(math.sin(swirl_ang) * sr * 0.7)
            pygame.draw.rect(surface, _NS_drav.PALETTE["core_hot"], (sx, sy, 1, 1))
        # Small core sparks around edge
        for i in range(6):
            ang = phase * 1 + i * math.pi / 3
            sr = 12
            sx = cx + int(math.cos(ang) * sr)
            sy = cy + 3 + int(math.sin(ang) * sr * 0.7)
            alpha = _NS_drav._alpha(200 * core_pulse)
            pygame.draw.rect(surface, (*_NS_drav.PALETTE["core_shine"], alpha), (sx, sy, 1, 1))
    def _draw_armor_arms(surface, cx, cy, facing, phase, action, attack_progress):
        """Two arms: far arm (idle back), near arm HOLDS the anchor."""
        idle_sway = math.sin(phase * 0.5) * 2
        # FAR ARM (behind, holds chain)
        far_shoulder = (cx - facing * 18, cy - 11)
        far_elbow = (cx - facing * 24, cy - 3)
        far_fist = (cx - facing * 26, cy + 12 + int(idle_sway * 0.3))
        _NS_drav._draw_armor_arm(surface, far_shoulder, far_elbow, far_fist,
                                  facing, phase, dark=True)
        # NEAR ARM — holds ANCHOR, swings on attack
        if action == "attack":
            if attack_progress < 0.35:
                # Wind-up: arm back+up (raise anchor)
                t = attack_progress / 0.35
                angle = math.radians(-40 - t * 80) * facing
                arm_len = 24
            elif attack_progress < 0.6:
                # SLAM: swing forward+down
                t = (attack_progress - 0.35) / 0.25
                angle = math.radians(-120 + t * 180) * facing
                arm_len = 26
            else:
                # Recovery
                t = (attack_progress - 0.6) / 0.4
                angle = math.radians(60 - t * 60) * facing
                arm_len = 24
            shoulder = (cx + facing * 18, cy - 11)
            elbow = (shoulder[0] + int(math.cos(angle) * arm_len * 0.5),
                     shoulder[1] + int(math.sin(angle) * arm_len * 0.5))
            fist = (shoulder[0] + int(math.cos(angle) * arm_len),
                    shoulder[1] + int(math.sin(angle) * arm_len))
            _NS_drav._draw_armor_arm(surface, shoulder, elbow, fist,
                                      facing, phase, dark=False)
            # Anchor at fist tip
            _NS_drav._draw_anchor_weapon(surface, fist, facing, phase, angle_rad=angle)
        else:
            near_shoulder = (cx + facing * 18, cy - 11)
            near_elbow = (cx + facing * 22, cy + 2 + int(idle_sway * 0.3))
            near_fist = (cx + facing * 24, cy + 16 + int(idle_sway * 0.5))
            _NS_drav._draw_armor_arm(surface, near_shoulder, near_elbow, near_fist,
                                      facing, phase, dark=False)
            # Anchor hanging down at fist
            _NS_drav._draw_anchor_weapon(surface, near_fist, facing, phase,
                                          angle_rad=math.radians(90))
    def _draw_armor_arm(surface, shoulder, elbow, fist, facing, phase, dark=False):
        """Armored arm with cyan core accents."""
        stone_dark_c = _NS_drav.PALETTE["armor_darkest"] if dark else _NS_drav.PALETTE["armor_dark"]
        stone_mid_c = _NS_drav.PALETTE["armor_dark"] if dark else _NS_drav.PALETTE["armor_mid"]
        stone_light_c = _NS_drav.PALETTE["armor_mid"] if dark else _NS_drav.PALETTE["armor_light"]
        # Shadow
        _NS_drav._aaline(surface, _NS_drav.PALETTE["shadow_deep"],
                          (shoulder[0] + 2, shoulder[1] + 3),
                          (elbow[0] + 2, elbow[1] + 3), 10)
        _NS_drav._aaline(surface, _NS_drav.PALETTE["shadow_deep"],
                          (elbow[0] + 2, elbow[1] + 3),
                          (fist[0] + 2, fist[1] + 3), 9)
        # Upper arm
        _NS_drav._aaline(surface, _NS_drav.PALETTE["armor_darkest"], shoulder, elbow, 10)
        _NS_drav._aaline(surface, stone_dark_c, shoulder, elbow, 8)
        _NS_drav._aaline(surface, stone_mid_c,
                          (shoulder[0], shoulder[1] - 1),
                          (elbow[0], elbow[1] - 1), 5)
        _NS_drav._aaline(surface, stone_light_c,
                          (shoulder[0], shoulder[1] - 2),
                          (elbow[0], elbow[1] - 2), 2)
        # Cyan core band on upper arm
        mid_ux = (shoulder[0] + elbow[0]) // 2
        mid_uy = (shoulder[1] + elbow[1]) // 2
        core_pulse = math.sin(phase * 2) * 0.3 + 0.7
        core_alpha = _NS_drav._alpha(200 * core_pulse)
        _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_dark"], core_alpha),
                            (mid_ux, mid_uy), 5)
        _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_mid"], core_alpha),
                            (mid_ux, mid_uy), 3)
        pygame.draw.rect(surface, _NS_drav.PALETTE["core_light"], (mid_ux, mid_uy, 1, 1))
        # Elbow joint
        pygame.draw.rect(surface, _NS_drav.PALETTE["armor_darkest"],
                         (elbow[0] - 4, elbow[1] - 4, 9, 9))
        pygame.draw.rect(surface, stone_dark_c, (elbow[0] - 4, elbow[1] - 4, 8, 8))
        pygame.draw.rect(surface, stone_mid_c, (elbow[0] - 3, elbow[1] - 3, 6, 6))
        pygame.draw.rect(surface, stone_light_c, (elbow[0] - 2, elbow[1] - 3, 3, 3))
        # Gold accent
        pygame.draw.rect(surface, _NS_drav.PALETTE["gold_mid"], (elbow[0] - 1, elbow[1], 2, 1))
        # Forearm
        _NS_drav._aaline(surface, _NS_drav.PALETTE["armor_darkest"], elbow, fist, 9)
        _NS_drav._aaline(surface, stone_dark_c, elbow, fist, 7)
        _NS_drav._aaline(surface, stone_mid_c,
                          (elbow[0], elbow[1] - 1), (fist[0], fist[1] - 1), 4)
        _NS_drav._aaline(surface, stone_light_c,
                          (elbow[0], elbow[1] - 2), (fist[0], fist[1] - 2), 1)
        # Gauntlet fist (small stone box)
        fx, fy = fist
        pygame.draw.rect(surface, _NS_drav.PALETTE["shadow_deep"],
                         (fx - 5 + 1, fy - 5 + 1, 11, 11))
        pygame.draw.rect(surface, _NS_drav.PALETTE["armor_darkest"],
                         (fx - 5, fy - 5, 10, 10))
        pygame.draw.rect(surface, stone_dark_c, (fx - 4, fy - 4, 8, 8))
        pygame.draw.rect(surface, stone_mid_c, (fx - 3, fy - 3, 6, 6))
        pygame.draw.rect(surface, stone_light_c, (fx - 2, fy - 3, 3, 2))
        # Gold knuckle band
        pygame.draw.rect(surface, _NS_drav.PALETTE["gold_dark"], (fx - 5, fy - 1, 10, 2))
        pygame.draw.rect(surface, _NS_drav.PALETTE["gold_mid"], (fx - 4, fy - 1, 8, 1))
    def _draw_anchor_weapon(surface, hand_pt, facing, phase, angle_rad=math.pi / 2):
        """Big anchor weapon extending from hand.
        The anchor axis is oriented in angle_rad (radians from +x axis).
        """
        # Direction along axis
        ux = math.cos(angle_rad)
        uy = math.sin(angle_rad)
        # Perpendicular
        px_dir = -uy
        py_dir = ux
        # Anchor length
        anchor_len = 24
        # Handle (grip) starts at hand
        handle_end_x = hand_pt[0] + int(ux * 4)
        handle_end_y = hand_pt[1] + int(uy * 4)
        # Shaft going further
        shaft_end_x = hand_pt[0] + int(ux * anchor_len)
        shaft_end_y = hand_pt[1] + int(uy * anchor_len)
        # Cross bar position (about 70% down shaft)
        cross_x = hand_pt[0] + int(ux * anchor_len * 0.72)
        cross_y = hand_pt[1] + int(uy * anchor_len * 0.72)
        # Cross bar length
        cross_len = 12
        cross_a = (cross_x + int(px_dir * cross_len), cross_y + int(py_dir * cross_len))
        cross_b = (cross_x - int(px_dir * cross_len), cross_y - int(py_dir * cross_len))
        # Hook tips (curve down from cross bar ends)
        hook_a_tip = (cross_a[0] + int(ux * 6) + int(px_dir * 3),
                       cross_a[1] + int(uy * 6) + int(py_dir * 3))
        hook_b_tip = (cross_b[0] + int(ux * 6) - int(px_dir * 3),
                       cross_b[1] + int(uy * 6) - int(py_dir * 3))
        # Top ring (at hand end)
        ring_cx = hand_pt[0] - int(ux * 2)
        ring_cy = hand_pt[1] - int(uy * 2)
        # Shadow first
        pygame.draw.circle(surface, _NS_drav.PALETTE["shadow_deep"],
                           (ring_cx + 2, ring_cy + 2), 4, 2)
        _NS_drav._aaline(surface, _NS_drav.PALETTE["shadow_deep"],
                          (hand_pt[0] + 2, hand_pt[1] + 2),
                          (shaft_end_x + 2, shaft_end_y + 2), 5)
        _NS_drav._aaline(surface, _NS_drav.PALETTE["shadow_deep"],
                          (cross_a[0] + 2, cross_a[1] + 2),
                          (cross_b[0] + 2, cross_b[1] + 2), 5)
        # Draw top RING
        pygame.draw.circle(surface, _NS_drav.PALETTE["anchor_darkest"],
                           (ring_cx, ring_cy), 5)
        pygame.draw.circle(surface, _NS_drav.PALETTE["anchor_dark"],
                           (ring_cx, ring_cy), 4)
        pygame.draw.circle(surface, _NS_drav.PALETTE["crevice_darkest"],
                           (ring_cx, ring_cy), 2)
        pygame.draw.circle(surface, _NS_drav.PALETTE["anchor_light"],
                           (ring_cx - 1, ring_cy - 1), 1)
        # Draw SHAFT (main vertical bar)
        _NS_drav._aaline(surface, _NS_drav.PALETTE["anchor_darkest"],
                          hand_pt, (shaft_end_x, shaft_end_y), 6)
        _NS_drav._aaline(surface, _NS_drav.PALETTE["anchor_dark"],
                          hand_pt, (shaft_end_x, shaft_end_y), 5)
        _NS_drav._aaline(surface, _NS_drav.PALETTE["anchor_mid"],
                          (hand_pt[0] + int(px_dir), hand_pt[1] + int(py_dir)),
                          (shaft_end_x + int(px_dir), shaft_end_y + int(py_dir)), 2)
        _NS_drav._aaline(surface, _NS_drav.PALETTE["anchor_light"],
                          (hand_pt[0] + int(px_dir * 2), hand_pt[1] + int(py_dir * 2)),
                          (shaft_end_x + int(px_dir * 2), shaft_end_y + int(py_dir * 2)), 1)
        # Gold bands on shaft (2 rings)
        for band_t in (0.3, 0.55):
            bx = hand_pt[0] + int(ux * anchor_len * band_t)
            by = hand_pt[1] + int(uy * anchor_len * band_t)
            pygame.draw.circle(surface, _NS_drav.PALETTE["gold_dark"], (bx, by), 4)
            pygame.draw.circle(surface, _NS_drav.PALETTE["gold_mid"], (bx, by), 3)
            pygame.draw.circle(surface, _NS_drav.PALETTE["gold_light"], (bx - 1, by - 1), 1)
        # Draw CROSS BAR
        _NS_drav._aaline(surface, _NS_drav.PALETTE["anchor_darkest"], cross_a, cross_b, 6)
        _NS_drav._aaline(surface, _NS_drav.PALETTE["anchor_dark"], cross_a, cross_b, 5)
        _NS_drav._aaline(surface, _NS_drav.PALETTE["anchor_mid"],
                          (cross_a[0], cross_a[1] - 1),
                          (cross_b[0], cross_b[1] - 1), 2)
        # Draw HOOK tips (curved arm+point)
        for base, tip in [(cross_a, hook_a_tip), (cross_b, hook_b_tip)]:
            _NS_drav._aaline(surface, _NS_drav.PALETTE["anchor_darkest"], base, tip, 5)
            _NS_drav._aaline(surface, _NS_drav.PALETTE["anchor_dark"], base, tip, 4)
            _NS_drav._aaline(surface, _NS_drav.PALETTE["anchor_mid"],
                              (base[0], base[1] - 1), (tip[0], tip[1] - 1), 2)
            # Sharp pointed spike at end
            spike_ext = 4
            spike_tip_x = tip[0] + int(ux * spike_ext)
            spike_tip_y = tip[1] + int(uy * spike_ext)
            _NS_drav._poly(surface, _NS_drav.PALETTE["shadow_deep"], [
                (tip[0] - int(px_dir * 2) + 1, tip[1] - int(py_dir * 2) + 1),
                (spike_tip_x + 1, spike_tip_y + 1),
                (tip[0] + int(px_dir * 2) + 1, tip[1] + int(py_dir * 2) + 1),
            ])
            _NS_drav._poly(surface, _NS_drav.PALETTE["anchor_darkest"], [
                (tip[0] - int(px_dir * 2), tip[1] - int(py_dir * 2)),
                (spike_tip_x, spike_tip_y),
                (tip[0] + int(px_dir * 2), tip[1] + int(py_dir * 2)),
            ])
            _NS_drav._poly(surface, _NS_drav.PALETTE["anchor_mid"], [
                (tip[0] - int(px_dir), tip[1] - int(py_dir)),
                (spike_tip_x, spike_tip_y),
                (tip[0] + int(px_dir), tip[1] + int(py_dir)),
            ])
            pygame.draw.rect(surface, _NS_drav.PALETTE["anchor_shine"],
                             (spike_tip_x, spike_tip_y, 1, 1))
        # Small cyan glow at cross center (anchor's soul)
        core_pulse = math.sin(phase * 2) * 0.3 + 0.7
        core_alpha = _NS_drav._alpha(220 * core_pulse)
        for r in range(4, 0, -1):
            alpha = _NS_drav._alpha(100 * (4 - r) / 4 * core_pulse)
            _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_light"], alpha),
                                (cross_x, cross_y), r)
        _NS_drav._aacircle(surface, _NS_drav.PALETTE["core_hot"], (cross_x, cross_y), 2)
        pygame.draw.rect(surface, _NS_drav.PALETTE["core_shine"], (cross_x, cross_y, 1, 1))
    def _draw_shoulder_pauldrons(surface, cx, cy, facing, phase):
        """Big shoulder pauldrons with cyan core."""
        for side in (-1, 1):
            base_x = cx + side * 20
            base_y = cy - 2
            # Pauldron dome
            pauld_pts = [
                (base_x - 7, base_y - 2), (base_x - 6, base_y - 9),
                (base_x - 1, base_y - 12), (base_x + 4, base_y - 11),
                (base_x + 7, base_y - 7), (base_x + 8, base_y),
                (base_x + 6, base_y + 4), (base_x - 6, base_y + 4),
            ]
            _NS_drav._poly(surface, _NS_drav.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in pauld_pts])
            _NS_drav._poly(surface, _NS_drav.PALETTE["armor_darkest"], pauld_pts)
            _NS_drav._poly(surface, _NS_drav.PALETTE["armor_dark"], [
                (base_x - 6, base_y - 2), (base_x - 5, base_y - 8),
                (base_x - 1, base_y - 11), (base_x + 4, base_y - 10),
                (base_x + 6, base_y - 6), (base_x + 7, base_y),
                (base_x + 5, base_y + 3), (base_x - 5, base_y + 3),
            ])
            _NS_drav._poly(surface, _NS_drav.PALETTE["armor_mid"], [
                (base_x - 4, base_y - 2), (base_x - 3, base_y - 7),
                (base_x, base_y - 9), (base_x + 3, base_y - 7),
                (base_x + 5, base_y - 2), (base_x + 4, base_y + 2),
                (base_x - 3, base_y + 2),
            ])
            _NS_drav._poly(surface, _NS_drav.PALETTE["armor_light"], [
                (base_x - 1, base_y - 6), (base_x + 2, base_y - 6),
                (base_x + 3, base_y - 2), (base_x, base_y - 1),
            ])
            # Gold trim rim
            pygame.draw.line(surface, _NS_drav.PALETTE["gold_dark"],
                             (base_x - 7, base_y + 3), (base_x + 6, base_y + 3), 2)
            pygame.draw.line(surface, _NS_drav.PALETTE["gold_mid"],
                             (base_x - 7, base_y + 3), (base_x + 6, base_y + 3), 1)
            # Cyan core on pauldron center
            core_pulse = math.sin(phase * 2) * 0.3 + 0.7
            core_alpha = _NS_drav._alpha(220 * core_pulse)
            for r in range(4, 0, -1):
                alpha = _NS_drav._alpha(80 * (4 - r) / 4 * core_pulse)
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_light"], alpha),
                                    (base_x, base_y - 4), r)
            _NS_drav._aacircle(surface, _NS_drav.PALETTE["core_mid"], (base_x, base_y - 4), 2)
            pygame.draw.rect(surface, _NS_drav.PALETTE["core_shine"], (base_x, base_y - 4, 1, 1))
    def _draw_armor_head(surface, cx, cy, facing, phase):
        """Helmed head — but face is hidden, only glowing cyan behind slit."""
        head_shape = [
            (cx - 8, cy + 6), (cx - 10, cy + 2), (cx - 10, cy - 4),
            (cx - 7, cy - 8), (cx - 2, cy - 10), (cx + 4, cy - 10),
            (cx + 9, cy - 7), (cx + 11, cy - 2), (cx + 10, cy + 4),
            (cx + 7, cy + 7), (cx + 1, cy + 8), (cx - 5, cy + 7),
        ]
        _NS_drav._poly(surface, _NS_drav.PALETTE["shadow_deep"],
                        [(px + 2, py + 2) for px, py in head_shape])
        _NS_drav._poly(surface, _NS_drav.PALETTE["armor_darkest"], head_shape)
        _NS_drav._poly(surface, _NS_drav.PALETTE["armor_dark"], [
            (cx - 8, cy + 5), (cx - 9, cy + 1), (cx - 9, cy - 3),
            (cx - 6, cy - 7), (cx - 2, cy - 9), (cx + 4, cy - 9),
            (cx + 8, cy - 6), (cx + 10, cy - 2), (cx + 9, cy + 3),
            (cx + 6, cy + 6), (cx + 1, cy + 7), (cx - 5, cy + 6),
        ])
        _NS_drav._poly(surface, _NS_drav.PALETTE["armor_mid"], [
            (cx - 6, cy + 3), (cx - 7, cy - 2), (cx - 4, cy - 6),
            (cx + 3, cy - 6), (cx + 7, cy - 2), (cx + 7, cy + 3),
            (cx + 4, cy + 5), (cx - 3, cy + 5),
        ])
        _NS_drav._poly(surface, _NS_drav.PALETTE["armor_light"], [
            (cx + facing * 2, cy - 5), (cx + facing * 5, cy - 3),
            (cx + facing * 4, cy), (cx + facing, cy - 2),
        ])
        # HELM VISOR SLIT (dark cavity with bright cyan glow inside — like Atlas's face)
        pygame.draw.rect(surface, _NS_drav.PALETTE["shadow_deep"],
                         (cx - 7, cy - 5, 15, 5))
        pygame.draw.rect(surface, _NS_drav.PALETTE["crevice_darkest"],
                         (cx - 6, cy - 4, 13, 4))
        # Glowing cyan interior (like burning core inside)
        _NS_drav._draw_glow_visor(surface, cx, cy - 2, phase)
        # Face plate lower (chin guard with gold trim)
        pygame.draw.rect(surface, _NS_drav.PALETTE["gold_dark"], (cx - 6, cy + 3, 12, 2))
        pygame.draw.rect(surface, _NS_drav.PALETTE["gold_mid"], (cx - 5, cy + 4, 10, 1))
        # Face plate rivets
        pygame.draw.rect(surface, _NS_drav.PALETTE["gold_mid"], (cx - 5, cy + 3, 1, 1))
        pygame.draw.rect(surface, _NS_drav.PALETTE["gold_mid"], (cx + 4, cy + 3, 1, 1))
        # Helm side vents (dark slits)
        for side in (-1, 1):
            for i in range(3):
                pygame.draw.rect(surface, _NS_drav.PALETTE["crevice_darkest"],
                                 (cx + side * 8, cy + i * 2, 1, 1))
    def _draw_glow_visor(surface, cx, cy, phase):
        """Bright cyan glow behind helm slit."""
        pulse = math.sin(phase * 1.8) * 0.35 + 0.65
        # Big central glow
        for r in range(6, 0, -1):
            alpha = _NS_drav._alpha(180 * (6 - r) / 6 * pulse)
            _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_light"], alpha), (cx, cy), r)
        # 2 bright eye points
        for eye_x in (cx - 3, cx + 3):
            _NS_drav._aacircle(surface, _NS_drav.PALETTE["core_hot"], (eye_x, cy), 2)
            pygame.draw.rect(surface, _NS_drav.PALETTE["core_shine"], (eye_x, cy, 1, 1))
            pygame.draw.rect(surface, _NS_drav.PALETTE["white"], (eye_x, cy, 1, 1))
    def _draw_gold_crown(surface, cx, cy, facing, phase):
        """Golden royal crown on top of helm (like Atlas's crown)."""
        # 5 gold spikes with jewels
        for i, (dx, height) in enumerate([
            (-7, 4), (-4, 6), (0, 9), (4, 6), (7, 4),
        ]):
            spike_x = cx + dx
            spike_tip_y = cy - height
            _NS_drav._poly(surface, _NS_drav.PALETTE["shadow_deep"], [
                (spike_x - 1 + 1, cy + 1 + 1),
                (spike_x + 1, spike_tip_y + 1),
                (spike_x + 1 + 1, cy + 1 + 1),
            ])
            _NS_drav._poly(surface, _NS_drav.PALETTE["gold_darkest"], [
                (spike_x - 1, cy + 1), (spike_x, spike_tip_y), (spike_x + 1, cy + 1),
            ])
            _NS_drav._poly(surface, _NS_drav.PALETTE["gold_dark"], [
                (spike_x - 1, cy + 1), (spike_x, spike_tip_y),
                (int((spike_x + spike_x + 1) / 2), int((spike_tip_y + cy + 1) / 2)),
            ])
            _NS_drav._poly(surface, _NS_drav.PALETTE["gold_mid"], [
                (spike_x, cy), (spike_x, spike_tip_y),
                (int((spike_x * 3 + spike_x + 1) / 4),
                 int((spike_tip_y * 3 + cy + 1) / 4)),
            ])
            pygame.draw.rect(surface, _NS_drav.PALETTE["gold_light"],
                             (spike_x, spike_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_drav.PALETTE["gold_shine"],
                             (spike_x, spike_tip_y, 1, 1))
        # Base crown band
        pygame.draw.rect(surface, _NS_drav.PALETTE["gold_dark"],
                         (cx - 9, cy + 1, 19, 3))
        pygame.draw.rect(surface, _NS_drav.PALETTE["gold_mid"],
                         (cx - 8, cy + 2, 17, 1))
        # Central cyan gem (biggest)
        core_pulse = math.sin(phase * 2) * 0.3 + 0.7
        core_alpha = _NS_drav._alpha(230 * core_pulse)
        for r in range(4, 0, -1):
            alpha = _NS_drav._alpha(100 * (4 - r) / 4 * core_pulse)
            _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_light"], alpha),
                                (cx, cy + 2), r)
        pygame.draw.rect(surface, _NS_drav.PALETTE["core_dark"], (cx - 1, cy + 2, 3, 1))
        pygame.draw.rect(surface, _NS_drav.PALETTE["core_mid"], (cx, cy + 2, 2, 1))
        pygame.draw.rect(surface, _NS_drav.PALETTE["core_shine"], (cx, cy + 2, 1, 1))
        # Small side gems
        for gem_x in (cx - 5, cx + 5):
            pygame.draw.rect(surface, _NS_drav.PALETTE["core_dark"], (gem_x, cy + 2, 1, 1))
            pygame.draw.rect(surface, _NS_drav.PALETTE["core_light"], (gem_x, cy + 2, 1, 1))
    # ============================================================
    # ANCHOR SWING SLASH (basic attack arc)
    # ============================================================
    def _draw_anchor_swing_slash(surface, cx, cy, facing, progress):
        """Cyan crescent slash arc from anchor swing."""
        if progress < 0.35 or progress > 0.75:
            return
        t = (progress - 0.35) / 0.4
        intensity = math.sin(t * math.pi)
        alpha = _NS_drav._alpha(255 * intensity)
        arc_cx = cx + facing * 22
        arc_cy = cy + 8
        arc_r = 28
        # Slash arc lines (bigger and more dramatic for anchor)
        start_angle = math.radians(-85) if facing > 0 else math.radians(180 + 85)
        end_angle = math.radians(85) if facing > 0 else math.radians(180 - 85)
        sweep = start_angle + (end_angle - start_angle) * t
        trail_start = start_angle + (end_angle - start_angle) * max(0, t - 0.4)
        prev_pt = None
        num_segments = 14
        for i in range(num_segments + 1):
            seg_t = i / num_segments
            angle = trail_start + (sweep - trail_start) * seg_t
            px = arc_cx + int(math.cos(angle) * arc_r)
            py = arc_cy + int(math.sin(angle) * arc_r)
            if prev_pt is not None:
                for thickness, color in [
                    (7, (*_NS_drav.PALETTE["wave_darkest"], alpha // 3)),
                    (5, (*_NS_drav.PALETTE["wave_dark"], alpha // 2)),
                    (3, (*_NS_drav.PALETTE["core_mid"], alpha)),
                    (2, (*_NS_drav.PALETTE["core_light"], alpha)),
                    (1, (*_NS_drav.PALETTE["core_shine"], alpha)),
                ]:
                    pygame.draw.line(surface, color, prev_pt, (px, py), thickness)
            prev_pt = (px, py)
        # Water droplets along arc
        for i in range(8):
            angle = math.radians(-85) + math.radians(170) * (i / 8)
            if facing < 0:
                angle = math.radians(180) - angle
            spark_r = arc_r + int(math.sin(i + progress * 10) * 5)
            sx = arc_cx + int(math.cos(angle) * spark_r)
            sy = arc_cy + int(math.sin(angle) * spark_r)
            _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_hot"], alpha), (sx, sy), 2)
            pygame.draw.rect(surface, (*_NS_drav.PALETTE["core_shine"], alpha), (sx, sy, 1, 1))
        # Small water splash particles
        for i in range(5):
            angle = math.radians(-70) + math.radians(140) * (i / 5)
            if facing < 0:
                angle = math.radians(180) - angle
            dust_r = arc_r + 8 + int(math.sin(progress * 5 + i) * 3)
            dx = arc_cx + int(math.cos(angle) * dust_r)
            dy = arc_cy + int(math.sin(angle) * dust_r)
            _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["wave_light"], alpha), (dx, dy), 2)
    # ============================================================
    # WATER RIPPLES + FLOATING BUBBLES (ambient)
    # ============================================================
    def _draw_water_ripples(surface, cx, cy, phase, intense=False):
        """Water ripples on ground below boss."""
        strength = 1.4 if intense else 1.0
        for i in range(3):
            ripple_t = (phase * 0.5 + i * 0.33) % 1.0
            r = int(40 * ripple_t)
            if r < 3:
                continue
            alpha = _NS_drav._alpha(180 * (1 - ripple_t) * strength)
            pygame.draw.ellipse(surface, (*_NS_drav.PALETTE["wave_mid"], alpha),
                                (cx - r, cy - r // 3, r * 2, r * 2 // 3), 1)
            pygame.draw.ellipse(surface, (*_NS_drav.PALETTE["wave_light"], alpha),
                                (cx - r + 1, cy - r // 3 + 1,
                                 r * 2 - 2, r * 2 // 3 - 2), 1)
    def _draw_floating_bubbles(surface, cx, cy, phase, intense=False):
        """Rising water bubbles around body."""
        strength = 1.3 if intense else 1.0
        for i in range(10):
            t = (phase * 0.6 + i * 0.11) % 1.0
            bx = cx - 30 + i * 6 + int(math.sin(phase + i) * 3)
            by = cy + 15 - int(t * 45)
            alpha = _NS_drav._alpha(200 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["wave_dark"], alpha), (bx, by), 3)
            _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["wave_mid"], alpha), (bx, by - 1), 2)
            pygame.draw.rect(surface, (*_NS_drav.PALETTE["wave_light"], alpha), (bx, by - 1, 1, 1))
            pygame.draw.rect(surface, (*_NS_drav.PALETTE["core_shine"], alpha), (bx, by - 2, 1, 1))
        # Cyan sparks
        for i in range(6):
            t = (phase * 0.5 + i * 0.17) % 1.0
            ex = cx - 20 + i * 8 + int(math.sin(phase + i) * 3)
            ey = cy + 10 - int(t * 30)
            alpha = _NS_drav._alpha(230 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_drav.PALETTE["core_light"], alpha), (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_drav.PALETTE["core_hot"], alpha), (ex, ey, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((150, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 15 - radius, 130 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 5, 12, 170), (5, 9, 140, 12))
        surface.blit(shadow, (x - 75, y - 15))
    def _draw_ocean_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_drav._alpha((95 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_drav._aacircle(aura, (*_NS_drav.PALETTE["mist_dark"], alpha),
                                    (110, 100), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_drav._alpha((60 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_drav._aacircle(aura, (*_NS_drav.PALETTE["wave_darkest"], alpha),
                                    (110, 100), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_drav._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_drav._aacircle(aura, (*_NS_drav.PALETTE["wave_dark"], alpha),
                                    (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))
        # Floating outer cyan sparks
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 50 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_drav.PALETTE["core_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_drav.PALETTE["core_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 56), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_drav.PALETTE["mist_dark"], 200),
                            (5, 20, 170, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_drav.PALETTE["wave_darkest"], 220),
                            (14, 22, 152, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_drav.PALETTE["wave_dark"], 230),
                            (25, 24, 130, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_drav.PALETTE["core_dark"], 180),
                            (40, 26, 100, 14), 1)
        # Runes
        for i in range(11):
            angle = phase * 0.3 + i * math.pi / 5.5
            x1 = 90 + int(math.cos(angle) * 48)
            y1 = 33 + int(math.sin(angle) * 8)
            x2 = 90 + int(math.cos(angle) * 76)
            y2 = 33 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_drav.PALETTE["core_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_drav.PALETTE["core_hot"],
                                        _NS_drav._alpha(150 * pulse)),
                                (14, 14, 152, 38), 1)
        surface.blit(ring, (x - 90, y - 28))
    # ============================================================
    # SKILL Q - ANCHOR THROW (range projectile with chain)
    # ============================================================
    def _draw_anchor_throw_skill(surface, boss, x, y, timer, phase):
        """Anchor flies to target with chain trailing back to boss."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_drav._target_position(boss, x, y)
        # Boss hand origin (where anchor + chain start)
        hand_x = x + facing * 22
        hand_y = y + 16
        if progress < 0.2:
            # Charge in hand
            t = progress / 0.2
            cr = int(3 + t * 6)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_drav._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_dark"], alpha),
                                    (hand_x, hand_y), r)
            _NS_drav._aacircle(surface, _NS_drav.PALETTE["core_mid"], (hand_x, hand_y), cr - 2)
            _NS_drav._aacircle(surface, _NS_drav.PALETTE["core_light"], (hand_x, hand_y),
                                max(1, cr - 4))
            _NS_drav._aacircle(surface, _NS_drav.PALETTE["core_shine"], (hand_x, hand_y),
                                max(1, cr - 6))
        elif progress < 0.75:
            # ANCHOR FLIES TO TARGET
            t = (progress - 0.2) / 0.55
            # Parabolic arc
            arc_h = 20
            bx = int(hand_x + (tx - hand_x) * t)
            by = int(hand_y + (ty - hand_y) * t - math.sin(t * math.pi) * arc_h)
            # Direction of travel
            dx = tx - hand_x
            dy = ty - hand_y
            travel_len = max(1, math.sqrt(dx * dx + dy * dy))
            angle_travel = math.atan2(dy, dx)
            # CHAIN from hand to anchor (many links)
            num_links = 12
            for i in range(num_links + 1):
                link_t = i / num_links
                lx = int(hand_x + (bx - hand_x) * link_t)
                ly = int(hand_y + (by - hand_y) * link_t
                          + math.sin(link_t * math.pi) * 4)
                pygame.draw.circle(surface, _NS_drav.PALETTE["shadow_deep"],
                                   (lx + 1, ly + 1), 2)
                pygame.draw.circle(surface, _NS_drav.PALETTE["chain_darkest"], (lx, ly), 2)
                pygame.draw.circle(surface, _NS_drav.PALETTE["chain_dark"], (lx, ly), 1)
                pygame.draw.rect(surface, _NS_drav.PALETTE["chain_light"],
                                 (lx, ly - 1, 1, 1))
            # ANCHOR at head of chain (spinning slightly)
            spin_angle = angle_travel + phase * 0.8
            _NS_drav._draw_anchor_weapon(surface, (bx, by), facing, phase,
                                          angle_rad=spin_angle)
            # Cyan trail behind anchor
            for i in range(6):
                trail_t = max(0, t - i * 0.05)
                px = int(hand_x + (tx - hand_x) * trail_t)
                py = int(hand_y + (ty - hand_y) * trail_t
                          - math.sin(trail_t * math.pi) * arc_h)
                alpha = _NS_drav._alpha(200 - i * 30)
                size = max(1, 5 - i)
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_dark"], alpha),
                                    (px, py), size)
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_mid"], alpha),
                                    (px, py), max(1, size - 1))
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_light"], alpha),
                                    (px, py), max(1, size - 2))
            # Impact burst
            if t > 0.88:
                st = (t - 0.88) / 0.12
                r = int(12 + st * 25)
                alpha = _NS_drav._alpha(240 * (1 - st))
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_darkest"], alpha),
                                    (tx, ty), r + 3, 3)
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_dark"], alpha),
                                    (tx, ty), r, 3)
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_mid"], alpha),
                                    (tx, ty), max(1, r - 6), 2)
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_hot"], alpha),
                                    (tx, ty), max(1, r - 12), 1)
                # Big burst star
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * r)
                    ey = ty + int(math.sin(angle_s) * r * 0.9)
                    pygame.draw.line(surface, (*_NS_drav.PALETTE["core_light"], alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface, (*_NS_drav.PALETTE["core_shine"], alpha),
                                     (ex, ey, 2, 2))
                # AIRBORNE arrows
                for a_i in range(2):
                    ax = tx - 8 + a_i * 16
                    ay = ty - 14 - int(math.sin(phase * 3 + a_i) * 3)
                    pygame.draw.polygon(surface, (*_NS_drav.PALETTE["core_hot"], alpha),
                                        [(ax, ay), (ax - 3, ay + 5), (ax + 3, ay + 5)])
        else:
            # RETRACT: anchor pulling back toward boss
            t = (progress - 0.75) / 0.25
            # Interpolate back
            bx = int(tx + (hand_x - tx) * t)
            by = int(ty + (hand_y - ty) * t)
            # Chain from hand to anchor (going back)
            num_links = 12
            for i in range(num_links + 1):
                link_t = i / num_links
                lx = int(hand_x + (bx - hand_x) * link_t)
                ly = int(hand_y + (by - hand_y) * link_t)
                pygame.draw.circle(surface, _NS_drav.PALETTE["chain_darkest"], (lx, ly), 2)
                pygame.draw.circle(surface, _NS_drav.PALETTE["chain_dark"], (lx, ly), 1)
            # Anchor at position
            spin_angle = math.atan2(hand_y - ty, hand_x - tx) + phase * 1.2
            _NS_drav._draw_anchor_weapon(surface, (bx, by), facing, phase,
                                          angle_rad=spin_angle)
    # ============================================================
    # SKILL W - TIDAL WAVE (AoE wave moving forward)
    # ============================================================
    def _draw_tidalwave_ground(surface, boss, x, y, timer, phase):
        """Wave line indicator on ground."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # No ground indicator (wave IS the effect)
    def _draw_tidalwave_foreground(surface, boss, x, y, timer, phase):
        """Big cyan wave moving forward."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_drav._target_position(boss, x, y)
        if progress < 0.2:
            # Wind-up: gather water at hands
            t = progress / 0.2
            cx_gather = x + facing * 22
            cy_gather = y + 5
            cr = int(4 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_drav._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["wave_dark"], alpha),
                                    (cx_gather, cy_gather), r)
            _NS_drav._aacircle(surface, _NS_drav.PALETTE["wave_mid"],
                                (cx_gather, cy_gather), cr - 2)
            _NS_drav._aacircle(surface, _NS_drav.PALETTE["wave_light"],
                                (cx_gather, cy_gather), max(1, cr - 4))
        else:
            # WAVE MOVES FORWARD
            t = (progress - 0.2) / 0.8
            wave_dist = int(t * 200)
            wave_cx = x + facing * (30 + wave_dist)
            wave_cy = y + 20
            # Wave shape (crescent curling forward)
            wave_h = 45
            wave_w = 55
            wave_alpha = _NS_drav._alpha(240 * (1 - t * 0.3))
            # Multi-layer wave (dark to light)
            for layer_i, (offset, alpha_mult, color) in enumerate([
                (0, 1.0, _NS_drav.PALETTE["wave_darkest"]),
                (-2, 0.9, _NS_drav.PALETTE["wave_dark"]),
                (-4, 0.8, _NS_drav.PALETTE["wave_mid"]),
                (-6, 0.7, _NS_drav.PALETTE["core_light"]),
            ]):
                # Wave crescent shape
                wave_pts = []
                num_pts = 12
                for i in range(num_pts):
                    ang = math.pi * (0.5 - i / (num_pts - 1) * 1.4) * facing
                    px = wave_cx + int(math.cos(ang) * wave_w + offset * facing)
                    py = wave_cy + int(math.sin(ang) * wave_h * 0.7) - offset
                    wave_pts.append((px, py))
                # Base of wave
                wave_pts.append((wave_cx - facing * wave_w // 2, wave_cy + 10))
                _NS_drav._poly(surface, (*color, int(wave_alpha * alpha_mult)), wave_pts)
            # Wave top curl (spray)
            curl_x = wave_cx + facing * int(wave_w * 0.7)
            curl_y = wave_cy - int(wave_h * 0.6)
            for r in range(8, 0, -1):
                alpha = _NS_drav._alpha(200 * (8 - r) / 8 * (1 - t * 0.3))
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_light"], alpha),
                                    (curl_x, curl_y), r)
            _NS_drav._aacircle(surface, _NS_drav.PALETTE["core_hot"], (curl_x, curl_y), 3)
            _NS_drav._aacircle(surface, _NS_drav.PALETTE["core_shine"], (curl_x, curl_y), 1)
            # Water sprays flying up
            for i in range(8):
                spray_ang = math.pi * (0.2 + i / 8 * 0.6)
                spray_r = 30 + int(math.sin(phase + i) * 8)
                sx = wave_cx + int(math.cos(spray_ang) * spray_r * facing)
                sy = wave_cy - int(math.sin(spray_ang) * spray_r * 0.9)
                alpha = _NS_drav._alpha(230 * (1 - t * 0.4))
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["wave_light"], alpha),
                                    (sx, sy), 3)
                pygame.draw.rect(surface, (*_NS_drav.PALETTE["core_shine"], alpha),
                                 (sx, sy, 1, 1))
            # Foam bubbles at base
            for i in range(10):
                foam_x = wave_cx + facing * (i * 6 - 30)
                foam_y = wave_cy + 8 + int(math.sin(phase * 2 + i) * 2)
                alpha = _NS_drav._alpha(200 * (1 - t * 0.3))
                pygame.draw.rect(surface, (*_NS_drav.PALETTE["wave_light"], alpha),
                                 (foam_x, foam_y, 2, 2))
                pygame.draw.rect(surface, (*_NS_drav.PALETTE["core_shine"], alpha),
                                 (foam_x, foam_y, 1, 1))
    # ============================================================
    # SKILL E - CHAIN LINK (energy chain around boss)
    # ============================================================
    def _draw_chainlink_ground(surface, boss, x, y, timer, phase):
        """Rings under boss."""
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(2):
            r = int(35 + i * 8 + math.sin(phase * 2) * 3)
            alpha = _NS_drav._alpha(220 - i * 60)
            _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_mid"], alpha),
                                (x, y + 50), r, 2)
            _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_light"], alpha),
                                (x, y + 50), r, 1)
    def _draw_chainlink_foreground(surface, boss, x, y, timer, phase):
        """Cyan energy chains rotating around boss (like Fatal Links passive)."""
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # 3 rotating chain rings around boss at different heights
        for chain_i in range(3):
            chain_y = y + chain_i * 15 - 10
            radius = 35 + chain_i * 3
            num_links = 16
            for i in range(num_links):
                ang = phase * 1.5 + i * math.pi * 2 / num_links + chain_i
                lx = x + int(math.cos(ang) * radius)
                ly = chain_y + int(math.sin(ang) * radius * 0.4)
                # 3D perspective (fade if behind)
                depth = math.sin(ang) * 0.5 + 0.5
                alpha = _NS_drav._alpha(220 * depth * (1 - progress * 0.3))
                # Chain link
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["chain_darkest"], alpha),
                                    (lx, ly), 3)
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["chain_dark"], alpha),
                                    (lx, ly), 2)
                pygame.draw.rect(surface, (*_NS_drav.PALETTE["core_light"], alpha),
                                 (lx, ly, 1, 1))
                pygame.draw.rect(surface, (*_NS_drav.PALETTE["core_shine"], alpha),
                                 (lx, ly, 1, 1))
        # Central cyan burst pulse
        pulse = math.sin(phase * 3) * 0.4 + 0.6
        for r in range(25, 5, -3):
            alpha = _NS_drav._alpha(60 * (25 - r) / 25 * pulse * (1 - progress * 0.5))
            _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_mid"], alpha), (x, y), r)
    # ============================================================
    # SKILL R - OCEAN GLADIATOR (ultimate vortex)
    # ============================================================
    def _draw_vortex_ground(surface, boss, x, y, timer, phase):
        """Massive whirlpool vortex on ground."""
        tx, ty = _NS_drav._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Warning grows
            t = progress / 0.3
            r = int(60 * t)
            alpha = _NS_drav._alpha(200 * t)
            pygame.draw.ellipse(surface, (*_NS_drav.PALETTE["wave_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_drav.PALETTE["core_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
        else:
            # ACTIVE VORTEX (swirling water)
            t = (progress - 0.3) / 0.7
            r_max = int(80 * min(1.0, t * 1.5))
            alpha_base = _NS_drav._alpha(230 * (1 - t * 0.4))
            # Multiple concentric rings (whirlpool depth)
            for ring_i in range(5):
                ring_r = r_max - ring_i * 12
                if ring_r <= 0:
                    continue
                ring_alpha = _NS_drav._alpha(alpha_base * (0.6 + ring_i * 0.1))
                # Rotating ellipses (spiraling)
                pygame.draw.ellipse(surface, (*_NS_drav.PALETTE["wave_dark"], ring_alpha),
                                    (tx - ring_r, ty - ring_r // 3,
                                     ring_r * 2, ring_r * 2 // 3))
                pygame.draw.ellipse(surface, (*_NS_drav.PALETTE["core_dark"], ring_alpha),
                                    (tx - ring_r + 4, ty - ring_r // 3 + 2,
                                     ring_r * 2 - 8, ring_r * 2 // 3 - 4), 1)
            # Center dark pit (deepest)
            pygame.draw.ellipse(surface, (*_NS_drav.PALETTE["shadow_deep"], alpha_base),
                                (tx - 15, ty - 6, 30, 12))
    def _draw_vortex_foreground(surface, boss, x, y, timer, phase):
        """Vortex spiral effect + pulling particles."""
        tx, ty = _NS_drav._target_position(boss, x, y)
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        if progress < 0.3:
            # PHASE 1: Boss leap indicator (small silhouette rising)
            t = progress / 0.3
            # Boss silhouette hint above
            rise_y = y - int(t * 60)
            for r in range(12, 3, -2):
                alpha = _NS_drav._alpha(120 * (12 - r) / 12 * t)
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_light"], alpha),
                                    (x, rise_y), r)
        elif progress < 0.85:
            # PHASE 2: ACTIVE VORTEX
            t = (progress - 0.3) / 0.55
            # Spiraling water tendrils (rising up from center)
            for spiral_i in range(20):
                spiral_t = (phase * 1.2 + spiral_i * 0.06) % 1.0
                sp_r = int(75 * (1 - spiral_t))
                sp_ang = spiral_t * math.pi * 6 + spiral_i * math.pi / 10
                sp_x = tx + int(math.cos(sp_ang) * sp_r)
                sp_y = ty + int(math.sin(sp_ang) * sp_r * 0.5) - int(spiral_t * 25)
                alpha = _NS_drav._alpha(220 * (1 - spiral_t))
                size = max(1, 4 - int(spiral_t * 3))
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["wave_dark"], alpha),
                                    (sp_x, sp_y), size + 1)
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["wave_mid"], alpha),
                                    (sp_x, sp_y), size)
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_light"], alpha),
                                    (sp_x, sp_y), max(1, size - 1))
                pygame.draw.rect(surface, (*_NS_drav.PALETTE["core_shine"], alpha),
                                 (sp_x, sp_y, 1, 1))
            # Rising water pillars around edge
            for pi in range(6):
                p_ang = pi * math.pi / 3 + phase * 0.3
                p_dist = 60
                px = tx + int(math.cos(p_ang) * p_dist)
                py = ty + int(math.sin(p_ang) * p_dist * 0.4)
                pillar_h = int(30 + math.sin(phase * 2 + pi) * 8)
                # Pillar body
                for py_i in range(pillar_h):
                    alpha = _NS_drav._alpha(200 * (1 - py_i / pillar_h))
                    pygame.draw.rect(surface, (*_NS_drav.PALETTE["wave_mid"], alpha),
                                     (px, py - py_i, 3, 1))
                    pygame.draw.rect(surface, (*_NS_drav.PALETTE["core_light"], alpha),
                                     (px + 1, py - py_i, 1, 1))
                # Top spray
                _NS_drav._aacircle(surface, _NS_drav.PALETTE["core_hot"],
                                    (px + 1, py - pillar_h), 3)
                pygame.draw.rect(surface, _NS_drav.PALETTE["core_shine"],
                                 (px + 1, py - pillar_h, 1, 1))
            # IMMOBILIZE indicators (chains binding target)
            if t > 0.2:
                for c_i in range(4):
                    c_ang = c_i * math.pi / 2 + phase * 0.5
                    c_dist = 25 + int(math.sin(phase * 3 + c_i) * 2)
                    cx_chain = tx + int(math.cos(c_ang) * c_dist)
                    cy_chain = ty + int(math.sin(c_ang) * c_dist * 0.6)
                    # Chain from edge to center
                    for link_i in range(4):
                        link_t = link_i / 4
                        lx = int(tx + (cx_chain - tx) * link_t)
                        ly = int(ty + (cy_chain - ty) * link_t)
                        pygame.draw.circle(surface, _NS_drav.PALETTE["chain_dark"], (lx, ly), 2)
                        pygame.draw.rect(surface, _NS_drav.PALETTE["core_light"], (lx, ly, 1, 1))
            # Big impact at center (initial slam)
            if t < 0.3:
                impact_t = t / 0.3
                intensity = math.sin(impact_t * math.pi)
                r = int(30 + impact_t * 30)
                alpha = _NS_drav._alpha(250 * intensity)
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_darkest"], alpha),
                                    (tx, ty), r + 3, 3)
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_dark"], alpha),
                                    (tx, ty), r, 3)
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_mid"], alpha),
                                    (tx, ty), max(1, r - 6), 2)
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_light"], alpha),
                                    (tx, ty), max(1, r - 12), 1)
                _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["white"], alpha),
                                    (tx, ty), max(1, r // 5))
        else:
            # Aftermath: settling water
            t = (progress - 0.85) / 0.15
            for i in range(8):
                fall_t = (phase * 0.7 + i * 0.1) % 1.0
                fx = tx + int(math.sin(phase + i) * 25)
                fy = ty - int(fall_t * 30)
                alpha = _NS_drav._alpha(180 * (1 - t) * (1 - fall_t))
                if alpha > 0:
                    _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["wave_mid"], alpha),
                                        (fx, fy), 3)
                    _NS_drav._aacircle(surface, (*_NS_drav.PALETTE["core_light"], alpha),
                                        (fx, fy), 2)
                    pygame.draw.rect(surface, (*_NS_drav.PALETTE["core_shine"], alpha),
                                     (fx, fy, 1, 1))



# ====================================================================
# LYRIENNE (CHORISTER OF TWILIGHT VESPERS) - Mini Boss
# ====================================================================

class _NS_lyrienne:
    """Namespace lyrienne - mini boss mage/support tema musik ungu."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Purple magic (main theme)
        "magic_darkest": (18, 5, 30),
        "magic_dark": (60, 25, 100),
        "magic_mid": (140, 70, 210),
        "magic_light": (200, 140, 250),
        "magic_hot": (235, 195, 255),
        "magic_shine": (250, 240, 255),
        # Purple deeper (shadows)
        "purple_darkest": (10, 3, 22),
        "purple_dark": (35, 15, 65),
        "purple_mid": (75, 40, 130),
        # Skin (pale porcelain)
        "skin_darkest": (95, 65, 75),
        "skin_dark": (165, 130, 135),
        "skin_mid": (220, 190, 190),
        "skin_light": (245, 225, 225),
        "skin_shine": (255, 245, 245),
        # Hair (purple lavender)
        "hair_darkest": (35, 15, 55),
        "hair_dark": (80, 45, 130),
        "hair_mid": (155, 110, 200),
        "hair_light": (215, 180, 240),
        "hair_shine": (245, 225, 250),
        # Dress (white with purple accents)
        "dress_darkest": (60, 55, 90),
        "dress_dark": (120, 115, 155),
        "dress_mid": (195, 190, 220),
        "dress_light": (240, 235, 250),
        "dress_shine": (255, 253, 255),
        # Purple dress accent
        "acc_dark": (75, 45, 125),
        "acc_mid": (140, 90, 200),
        "acc_light": (200, 155, 235),
        # Gold trim
        "gold_darkest": (40, 25, 5),
        "gold_dark": (110, 75, 20),
        "gold_mid": (200, 155, 55),
        "gold_light": (250, 220, 120),
        "gold_shine": (255, 250, 220),
        # Staff crystal (bright purple)
        "crystal_dark": (75, 20, 130),
        "crystal_mid": (170, 90, 230),
        "crystal_light": (225, 175, 255),
        "crystal_shine": (255, 245, 255),
        # Eye (violet)
        "eye_dark": (50, 15, 90),
        "eye_mid": (150, 90, 210),
        "eye_light": (220, 180, 250),
        "eye_shine": (255, 255, 255),
        # Heal green (for W skill)
        "heal_dark": (25, 90, 45),
        "heal_mid": (85, 200, 110),
        "heal_light": (180, 250, 200),
        # Ambient mist
        "mist_dark": (25, 15, 45),
        "mist_mid": (75, 50, 125),
        "mist_light": (170, 130, 210),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 5),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_lyrienne._clamp(color)
        if _NS_lyrienne.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_lyrienne._clamp(color)
        if _NS_lyrienne.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_lyrienne._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 250 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # MUSIC NOTE DRAWING HELPER
    # ============================================================
    def _draw_music_note(surface, cx, cy, size, color, alpha=255):
        """Draw a small music note (eighth note ♪)."""
        c = (*color, alpha) if len(color) == 3 else color
        # Note head (small ellipse)
        pygame.draw.ellipse(surface, c, (cx - size, cy, size * 2, size + 1))
        # Stem (vertical line up)
        pygame.draw.line(surface, c, (cx + size - 1, cy),
                         (cx + size - 1, cy - size * 3), 1)
        # Flag (curve at top of stem)
        pygame.draw.line(surface, c, (cx + size - 1, cy - size * 3),
                         (cx + size + 1, cy - size * 2), 1)
    def _draw_treble_clef(surface, cx, cy, size, color, alpha=255):
        """Draw a treble clef (simplified)."""
        c = (*color, alpha) if len(color) == 3 else color
        # Main vertical S-curve (stylized as multiple arcs)
        # Top loop
        pygame.draw.circle(surface, c, (cx, cy - size), size, 1)
        # Middle loop (bigger)
        pygame.draw.circle(surface, c, (cx, cy), int(size * 1.3), 1)
        # Bottom loop (small)
        pygame.draw.circle(surface, c, (cx - size // 2, cy + size + 1),
                           size // 2, 1)
        # Center vertical stem
        pygame.draw.line(surface, c, (cx, cy - size * 2),
                         (cx, cy + size * 2), 1)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_lyrienne(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_lyrienne._update_lyr_attack_anim(boss)
        attacking = (
            getattr(boss, "_lyr_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_lyrienne._draw_magic_aura(surface, x, y, pulse)
        _NS_lyrienne._draw_ground_ring(surface, x, y + 55, pulse, active_skill)
        # Skill ground FX
        if active_skill == "w":
            _NS_lyrienne._draw_care_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_lyrienne._draw_symphony_ground(surface, boss, x, y, skill_timer, pulse)
        # Body — floating with slow bob
        floating_bob = math.sin(pulse * 0.7) * 5
        if attacking:
            _NS_lyrienne._draw_lyr_attack(surface, boss, x, y - floating_bob)
        else:
            _NS_lyrienne._draw_lyr_idle(surface, boss, x, y - floating_bob)
        # Foreground FX
        if active_skill == "q":
            _NS_lyrienne._draw_melodywave_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_lyrienne._draw_care_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_lyrienne._draw_sonatabind_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_lyrienne._draw_symphony_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_lyr_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_lyr_previous_timer", 0))
        active = bool(getattr(boss, "_lyr_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._lyr_attack_active = True
            boss._lyr_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._lyr_attack_frame = int(getattr(boss, "_lyr_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._lyr_attack_active = False
            boss._lyr_attack_frame = 0
            active = False
        boss._lyr_previous_timer = timer
        boss._lyr_attack_progress = (
            min(1.0, getattr(boss, "_lyr_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_lyr_idle(surface, boss, x, y):
        _NS_lyrienne._draw_shadow(surface, x, y + 60)
        _NS_lyrienne._draw_floating_notes(surface, x, y, boss.pulse)
        _NS_lyrienne._draw_lyr_body(surface, x, y, boss.direction, boss.pulse, "idle")
    def _draw_lyr_attack(surface, boss, x, y):
        progress = getattr(boss, "_lyr_attack_progress", 0.0)
        # Staff swing (elegant, not too aggressive)
        if progress < 0.35:
            t = progress / 0.35
            swing_offset = -int(t * 2) * boss.direction
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            swing_offset = int((-2 + t * 8)) * boss.direction
            lift = int(3 - t * 5)
        else:
            t = (progress - 0.6) / 0.4
            swing_offset = int(6 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        _NS_lyrienne._draw_shadow(surface, x + swing_offset, y + 60)
        _NS_lyrienne._draw_floating_notes(surface, x + swing_offset, y, boss.pulse,
                                           intense=True)
        _NS_lyrienne._draw_lyr_body(surface, x + swing_offset, y - lift,
                                     boss.direction, boss.pulse, "attack", progress)
        _NS_lyrienne._draw_staff_slash(surface, x + swing_offset, y - lift,
                                        boss.direction, progress)
    # ============================================================
    # BODY (elegant mage girl with staff)
    # ============================================================
    def _draw_lyr_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw mage body: dress skirt → torso → arms → head → hair → staff."""
        # Order: back hair → dress (skirt bottom) → torso → arms → head → front hair → staff
        _NS_lyrienne._draw_back_hair(surface, cx, cy - 12, facing, phase)
        _NS_lyrienne._draw_dress_skirt(surface, cx, cy + 8, phase)
        _NS_lyrienne._draw_dress_torso(surface, cx, cy, facing, phase)
        _NS_lyrienne._draw_lyr_arms(surface, cx, cy, facing, phase, action, attack_progress)
        _NS_lyrienne._draw_lyr_head(surface, cx, cy - 22, facing, phase)
        _NS_lyrienne._draw_front_hair(surface, cx, cy - 22, facing, phase)
        _NS_lyrienne._draw_head_flower(surface, cx, cy - 28, facing, phase)
        # Staff (held by near hand)
        _NS_lyrienne._draw_magic_staff(surface, cx, cy, facing, phase, action, attack_progress)
    def _draw_dress_skirt(surface, cx, cy, phase):
        """Flowing skirt (bell-shaped, white with purple accents)."""
        pulse = math.sin(phase * 0.7) * 1
        # Skirt shape (widens toward bottom, elegant)
        skirt_pts = [
            (cx - 12, cy - 6),          # top left
            (cx - 18, cy + 4),
            (cx - 22, cy + 14),
            (cx - 24, cy + 24 + int(pulse)),
            (cx + 24, cy + 24 + int(pulse)),
            (cx + 22, cy + 14),
            (cx + 18, cy + 4),
            (cx + 12, cy - 6),
        ]
        # Shadow
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["shadow_deep"],
                            [(px + 2, py + 3) for px, py in skirt_pts])
        # Base skirt (dark to light gradient)
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["dress_darkest"], skirt_pts)
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["dress_dark"], [
            (cx - 11, cy - 5), (cx - 17, cy + 3), (cx - 20, cy + 13),
            (cx - 22, cy + 23), (cx + 22, cy + 23), (cx + 20, cy + 13),
            (cx + 17, cy + 3), (cx + 11, cy - 5),
        ])
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["dress_mid"], [
            (cx - 9, cy - 4), (cx - 14, cy + 2), (cx - 17, cy + 12),
            (cx - 18, cy + 20), (cx + 18, cy + 20), (cx + 17, cy + 12),
            (cx + 14, cy + 2), (cx + 9, cy - 4),
        ])
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["dress_light"], [
            (cx - 6, cy - 3), (cx - 8, cy + 2), (cx - 10, cy + 12),
            (cx - 10, cy + 18), (cx + 10, cy + 18), (cx + 10, cy + 12),
            (cx + 8, cy + 2), (cx + 6, cy - 3),
        ])
        # Center highlight
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["dress_shine"], [
            (cx - 2, cy), (cx + 2, cy), (cx + 3, cy + 10),
            (cx - 3, cy + 10),
        ])
        # Skirt folds (vertical lines)
        for x_off in (-14, -8, -4, 4, 8, 14):
            pygame.draw.line(surface, _NS_lyrienne.PALETTE["dress_dark"],
                             (cx + x_off, cy + 2),
                             (cx + int(x_off * 1.3), cy + 22), 1)
        # PURPLE ACCENT trim at bottom (curved band)
        bottom_pts = [
            (cx - 24, cy + 22), (cx - 22, cy + 20), (cx + 22, cy + 20),
            (cx + 24, cy + 22), (cx + 22, cy + 24), (cx - 22, cy + 24),
        ]
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["acc_dark"], bottom_pts)
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["acc_mid"], [
            (cx - 22, cy + 21), (cx + 22, cy + 21),
            (cx + 20, cy + 23), (cx - 20, cy + 23),
        ])
        # Gold trim on bottom
        pygame.draw.line(surface, _NS_lyrienne.PALETTE["gold_dark"],
                         (cx - 22, cy + 24), (cx + 22, cy + 24), 2)
        pygame.draw.line(surface, _NS_lyrienne.PALETTE["gold_mid"],
                         (cx - 22, cy + 24), (cx + 22, cy + 24), 1)
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["gold_shine"], (cx, cy + 24, 1, 1))
        # Purple gem decoration at center bottom
        gem_x = cx
        gem_y = cy + 22
        _NS_lyrienne._aacircle(surface, _NS_lyrienne.PALETTE["crystal_dark"], (gem_x, gem_y), 3)
        _NS_lyrienne._aacircle(surface, _NS_lyrienne.PALETTE["crystal_mid"], (gem_x, gem_y), 2)
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["crystal_light"], (gem_x, gem_y, 1, 1))
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["crystal_shine"], (gem_x, gem_y, 1, 1))
    def _draw_dress_torso(surface, cx, cy, facing, phase):
        """Slim mage torso with corset details."""
        breath = math.sin(phase * 0.7) * 1
        # Slim torso shape
        torso_pts = [
            (cx - 8, cy + 8),
            (cx - 10, cy + 2),
            (cx - 10, cy - 4 - int(breath)),
            (cx - 8, cy - 10),
            (cx - 4, cy - 13),
            (cx + 4, cy - 13),
            (cx + 8, cy - 10),
            (cx + 10, cy - 4 - int(breath)),
            (cx + 10, cy + 2),
            (cx + 8, cy + 8),
        ]
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in torso_pts])
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["dress_darkest"], torso_pts)
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["dress_dark"], [
            (cx - 7, cy + 7), (cx - 9, cy + 1), (cx - 9, cy - 3),
            (cx - 7, cy - 9), (cx - 3, cy - 12), (cx + 3, cy - 12),
            (cx + 7, cy - 9), (cx + 9, cy - 3), (cx + 9, cy + 1),
            (cx + 7, cy + 7),
        ])
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["dress_mid"], [
            (cx - 5, cy + 5), (cx - 7, cy), (cx - 6, cy - 8),
            (cx - 2, cy - 11), (cx + 2, cy - 11), (cx + 6, cy - 8),
            (cx + 7, cy), (cx + 5, cy + 5),
        ])
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["dress_light"], [
            (cx - 3, cy - 6), (cx + 3, cy - 6), (cx + 4, cy - 2),
            (cx + 2, cy + 4), (cx - 2, cy + 4), (cx - 4, cy - 2),
        ])
        # Skin (upper chest, collarbone) — small V-shape
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["skin_dark"], [
            (cx - 3, cy - 10), (cx + 3, cy - 10),
            (cx + 1, cy - 7), (cx - 1, cy - 7),
        ])
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["skin_mid"], [
            (cx - 2, cy - 9), (cx + 2, cy - 9),
            (cx + 1, cy - 8), (cx - 1, cy - 8),
        ])
        # Corset laces (vertical purple lines)
        for x_off in (-2, 0, 2):
            pygame.draw.line(surface, _NS_lyrienne.PALETTE["acc_dark"],
                             (cx + x_off, cy - 4), (cx + x_off, cy + 6), 1)
        # Crossed lace X pattern
        pygame.draw.line(surface, _NS_lyrienne.PALETTE["gold_mid"],
                         (cx - 3, cy - 2), (cx + 3, cy + 2), 1)
        pygame.draw.line(surface, _NS_lyrienne.PALETTE["gold_mid"],
                         (cx + 3, cy - 2), (cx - 3, cy + 2), 1)
        # Gold trim on neckline
        pygame.draw.line(surface, _NS_lyrienne.PALETTE["gold_dark"],
                         (cx - 5, cy - 9), (cx + 5, cy - 9), 1)
        pygame.draw.line(surface, _NS_lyrienne.PALETTE["gold_mid"],
                         (cx - 5, cy - 10), (cx + 5, cy - 10), 1)
        # Gold trim on waist
        pygame.draw.line(surface, _NS_lyrienne.PALETTE["gold_dark"],
                         (cx - 8, cy + 6), (cx + 8, cy + 6), 2)
        pygame.draw.line(surface, _NS_lyrienne.PALETTE["gold_mid"],
                         (cx - 8, cy + 6), (cx + 8, cy + 6), 1)
        # Purple gem on chest center
        gem_pulse = math.sin(phase * 2) * 0.3 + 0.7
        gem_alpha = _NS_lyrienne._alpha(220 * gem_pulse)
        _NS_lyrienne._aacircle(surface, (*_NS_lyrienne.PALETTE["crystal_dark"], gem_alpha),
                                (cx, cy - 7), 2)
        _NS_lyrienne._aacircle(surface, (*_NS_lyrienne.PALETTE["crystal_mid"], gem_alpha),
                                (cx, cy - 7), 1)
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["crystal_shine"], (cx, cy - 7, 1, 1))
    def _draw_lyr_arms(surface, cx, cy, facing, phase, action, attack_progress):
        """Slim arms — far arm outstretched, near arm holds staff."""
        idle_sway = math.sin(phase * 0.6) * 2
        # FAR ARM (outstretched, gesture like casting)
        far_shoulder = (cx - facing * 8, cy - 9)
        far_elbow = (cx - facing * 15, cy - 5 + int(idle_sway * 0.3))
        far_hand = (cx - facing * 22, cy - 2 + int(idle_sway * 0.4))
        _NS_lyrienne._draw_slim_arm(surface, far_shoulder, far_elbow, far_hand,
                                     facing, dark=True)
        # Magic sparkle at outstretched hand
        _NS_lyrienne._draw_hand_magic(surface, far_hand, phase, small=True)
        # NEAR ARM (holds staff)
        if action == "attack":
            # Staff arm raises during attack
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                angle = math.radians(-70 - t * 40) * facing
                arm_len = 18
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                angle = math.radians(-110 + t * 120) * facing
                arm_len = 20
            else:
                t = (attack_progress - 0.6) / 0.4
                angle = math.radians(10 - t * 10) * facing
                arm_len = 18
            shoulder = (cx + facing * 8, cy - 9)
            elbow = (shoulder[0] + int(math.cos(angle) * arm_len * 0.5),
                     shoulder[1] + int(math.sin(angle) * arm_len * 0.5))
            hand = (shoulder[0] + int(math.cos(angle) * arm_len),
                    shoulder[1] + int(math.sin(angle) * arm_len))
            _NS_lyrienne._draw_slim_arm(surface, shoulder, elbow, hand, facing, dark=False)
        else:
            # Staff resting
            near_shoulder = (cx + facing * 8, cy - 9)
            near_elbow = (cx + facing * 12, cy - 2 + int(idle_sway * 0.3))
            near_hand = (cx + facing * 15, cy + 8 + int(idle_sway * 0.4))
            _NS_lyrienne._draw_slim_arm(surface, near_shoulder, near_elbow, near_hand,
                                         facing, dark=False)
    def _draw_slim_arm(surface, shoulder, elbow, hand, facing, dark=False):
        """Slim elegant arm with white sleeve."""
        dress_dark_c = _NS_lyrienne.PALETTE["dress_darkest"] if dark else _NS_lyrienne.PALETTE["dress_dark"]
        dress_mid_c = _NS_lyrienne.PALETTE["dress_dark"] if dark else _NS_lyrienne.PALETTE["dress_mid"]
        dress_light_c = _NS_lyrienne.PALETTE["dress_mid"] if dark else _NS_lyrienne.PALETTE["dress_light"]
        # Shadow
        _NS_lyrienne._aaline(surface, _NS_lyrienne.PALETTE["shadow_deep"],
                              (shoulder[0] + 2, shoulder[1] + 2),
                              (elbow[0] + 2, elbow[1] + 2), 5)
        _NS_lyrienne._aaline(surface, _NS_lyrienne.PALETTE["shadow_deep"],
                              (elbow[0] + 2, elbow[1] + 2),
                              (hand[0] + 2, hand[1] + 2), 4)
        # Upper arm (sleeve - white)
        _NS_lyrienne._aaline(surface, _NS_lyrienne.PALETTE["dress_darkest"], shoulder, elbow, 5)
        _NS_lyrienne._aaline(surface, dress_dark_c, shoulder, elbow, 4)
        _NS_lyrienne._aaline(surface, dress_mid_c,
                              (shoulder[0], shoulder[1] - 1),
                              (elbow[0], elbow[1] - 1), 3)
        _NS_lyrienne._aaline(surface, dress_light_c,
                              (shoulder[0], shoulder[1] - 1),
                              (elbow[0], elbow[1] - 1), 1)
        # Forearm (sleeve extends)
        _NS_lyrienne._aaline(surface, _NS_lyrienne.PALETTE["dress_darkest"], elbow, hand, 4)
        _NS_lyrienne._aaline(surface, dress_dark_c, elbow, hand, 3)
        _NS_lyrienne._aaline(surface, dress_mid_c,
                              (elbow[0], elbow[1] - 1), (hand[0], hand[1] - 1), 2)
        # Sleeve cuff (flowing decoration at hand)
        cuff_dx = hand[0] - elbow[0]
        cuff_dy = hand[1] - elbow[1]
        cuff_len = max(1, math.sqrt(cuff_dx * cuff_dx + cuff_dy * cuff_dy))
        perp_x = -cuff_dy / cuff_len
        perp_y = cuff_dx / cuff_len
        cuff_a = (hand[0] + int(perp_x * 3), hand[1] + int(perp_y * 3))
        cuff_b = (hand[0] - int(perp_x * 3), hand[1] - int(perp_y * 3))
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["dress_light"],
                            [cuff_a, cuff_b, (hand[0] + int(cuff_dx / cuff_len * 3),
                                              hand[1] + int(cuff_dy / cuff_len * 3))])
        # Purple accent on cuff
        pygame.draw.line(surface, _NS_lyrienne.PALETTE["acc_mid"], cuff_a, cuff_b, 1)
        pygame.draw.line(surface, _NS_lyrienne.PALETTE["gold_mid"], cuff_a, cuff_b, 1)
        # HAND (skin visible below cuff)
        pygame.draw.circle(surface, _NS_lyrienne.PALETTE["shadow_deep"],
                           (hand[0] + 1, hand[1] + 1), 3)
        pygame.draw.circle(surface, _NS_lyrienne.PALETTE["skin_dark"], hand, 3)
        pygame.draw.circle(surface, _NS_lyrienne.PALETTE["skin_mid"], hand, 2)
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["skin_light"],
                         (hand[0], hand[1] - 1, 1, 1))
    def _draw_hand_magic(surface, hand, phase, small=False):
        """Magic sparkle at outstretched hand."""
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        cr = 4 if small else 6
        for r in range(cr + 2, 0, -1):
            alpha = _NS_lyrienne._alpha(100 * (cr + 2 - r) / (cr + 2) * pulse)
            _NS_lyrienne._aacircle(surface,
                                    (*_NS_lyrienne.PALETTE["magic_light"], alpha),
                                    hand, r)
        _NS_lyrienne._aacircle(surface, _NS_lyrienne.PALETTE["magic_mid"], hand, max(1, cr - 2))
        _NS_lyrienne._aacircle(surface, _NS_lyrienne.PALETTE["magic_hot"], hand, max(1, cr - 3))
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["magic_shine"], (hand[0], hand[1], 1, 1))
        # Orbiting music notes around hand
        for i in range(3):
            ang = phase * 1.5 + i * math.pi * 2 / 3
            nx = hand[0] + int(math.cos(ang) * 6)
            ny = hand[1] + int(math.sin(ang) * 6)
            alpha = _NS_lyrienne._alpha(200 * pulse)
            _NS_lyrienne._draw_music_note(surface, nx, ny, 1,
                                           _NS_lyrienne.PALETTE["magic_light"], alpha)
    def _draw_lyr_head(surface, cx, cy, facing, phase):
        """Pretty face with violet eyes."""
        # Face shape (rounded, feminine)
        head_pts = [
            (cx - 6, cy + 5), (cx - 7, cy + 1), (cx - 7, cy - 4),
            (cx - 5, cy - 8), (cx - 1, cy - 10), (cx + 3, cy - 10),
            (cx + 6, cy - 7), (cx + 7, cy - 3), (cx + 7, cy + 2),
            (cx + 5, cy + 6), (cx, cy + 7),
        ]
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in head_pts])
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["skin_darkest"], head_pts)
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["skin_dark"], [
            (cx - 6, cy + 4), (cx - 6, cy), (cx - 6, cy - 3),
            (cx - 4, cy - 7), (cx, cy - 9), (cx + 3, cy - 9),
            (cx + 5, cy - 6), (cx + 6, cy - 2), (cx + 6, cy + 1),
            (cx + 4, cy + 5), (cx, cy + 6),
        ])
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["skin_mid"], [
            (cx - 4, cy + 3), (cx - 5, cy - 1), (cx - 4, cy - 5),
            (cx - 1, cy - 7), (cx + 3, cy - 7), (cx + 5, cy - 4),
            (cx + 5, cy + 1), (cx + 3, cy + 4), (cx, cy + 5),
        ])
        # Cheek highlight
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["skin_light"], [
            (cx + facing * 2, cy - 3), (cx + facing * 4, cy - 1),
            (cx + facing * 3, cy + 2), (cx + facing, cy),
        ])
        # Blush
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["acc_light"],
                         (cx + facing * 3, cy + 1, 1, 1))
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["acc_light"],
                         (cx - facing * 3, cy + 2, 1, 1))
        # EYES (violet with sparkle)
        _NS_lyrienne._draw_lyr_eye(surface, cx - 2, cy - 3, phase)
        _NS_lyrienne._draw_lyr_eye(surface, cx + 3, cy - 3, phase)
        # Nose (tiny)
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["skin_darkest"], (cx + 1, cy, 1, 1))
        # Smile (small curve)
        pygame.draw.line(surface, _NS_lyrienne.PALETTE["acc_dark"],
                         (cx - 1, cy + 3), (cx + 2, cy + 3), 1)
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["acc_mid"], (cx, cy + 4, 2, 1))
    def _draw_lyr_eye(surface, ex, ey, phase):
        """Violet anime-style big eye."""
        pulse = math.sin(phase * 2) * 0.15 + 0.85
        # Eye shape (larger for anime look)
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["shadow_deep"], (ex - 1, ey - 1, 3, 3))
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["white"], (ex - 1, ey - 1, 3, 3))
        # Iris (violet)
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["eye_dark"], (ex, ey - 1, 2, 3))
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["eye_mid"], (ex, ey, 2, 2))
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["eye_light"], (ex + 1, ey, 1, 1))
        # Sparkle
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["eye_shine"], (ex, ey, 1, 1))
        # Top eyelash
        pygame.draw.line(surface, _NS_lyrienne.PALETTE["hair_dark"],
                         (ex - 1, ey - 1), (ex + 1, ey - 1), 1)
    def _draw_back_hair(surface, cx, cy, facing, phase):
        """Long flowing purple hair behind body."""
        sway = math.sin(phase * 0.5) * 2
        # Big hair mass behind
        hair_pts = [
            (cx - 12, cy - 4),
            (cx - 14, cy + 4),
            (cx - 15 + int(sway), cy + 16),
            (cx - 13 + int(sway), cy + 28),
            (cx - 8 + int(sway * 0.5), cy + 38),
            (cx + 8 - int(sway * 0.5), cy + 38),
            (cx + 13 - int(sway), cy + 28),
            (cx + 15 - int(sway), cy + 16),
            (cx + 14, cy + 4),
            (cx + 12, cy - 4),
            (cx + 8, cy - 8),
            (cx - 8, cy - 8),
        ]
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in hair_pts])
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["hair_darkest"], hair_pts)
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["hair_dark"], [
            (cx - 11, cy - 3), (cx - 13, cy + 3),
            (cx - 14 + int(sway), cy + 15),
            (cx - 12 + int(sway), cy + 26),
            (cx - 6 + int(sway * 0.5), cy + 36),
            (cx + 6 - int(sway * 0.5), cy + 36),
            (cx + 12 - int(sway), cy + 26),
            (cx + 14 - int(sway), cy + 15),
            (cx + 13, cy + 3), (cx + 11, cy - 3),
            (cx + 6, cy - 7), (cx - 6, cy - 7),
        ])
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["hair_mid"], [
            (cx - 9, cy), (cx - 10, cy + 8),
            (cx - 11 + int(sway * 0.7), cy + 22),
            (cx - 4 + int(sway * 0.3), cy + 34),
            (cx + 4 - int(sway * 0.3), cy + 34),
            (cx + 11 - int(sway * 0.7), cy + 22),
            (cx + 10, cy + 8), (cx + 9, cy),
        ])
        # Highlight streaks
        for streak_x in (-9, -3, 3, 9):
            for streak_i in range(4):
                sy_start = cy + 6 + streak_i * 8
                pygame.draw.line(surface, _NS_lyrienne.PALETTE["hair_light"],
                                 (cx + streak_x, sy_start),
                                 (cx + streak_x + int(sway * 0.5),
                                  sy_start + 6), 1)
        # Bright highlights
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["hair_shine"],
                         (cx + 5, cy + 4, 1, 4))
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["hair_shine"],
                         (cx - 5, cy + 4, 1, 4))
    def _draw_front_hair(surface, cx, cy, facing, phase):
        """Front bangs and side locks."""
        sway = math.sin(phase * 0.6) * 1
        # Front bangs (fringe over forehead)
        bang_pts = [
            (cx - 7, cy - 5), (cx - 6, cy - 9), (cx - 2, cy - 11),
            (cx + 3, cy - 11), (cx + 7, cy - 9), (cx + 8, cy - 5),
            (cx + 5, cy - 3), (cx + 2, cy - 5), (cx - 2, cy - 5),
            (cx - 5, cy - 3),
        ]
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["hair_darkest"],
                            [(px + 1, py + 1) for px, py in bang_pts])
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["hair_dark"], bang_pts)
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["hair_mid"], [
            (cx - 6, cy - 5), (cx - 5, cy - 8), (cx - 1, cy - 10),
            (cx + 2, cy - 10), (cx + 6, cy - 8), (cx + 7, cy - 5),
            (cx + 4, cy - 4), (cx + 1, cy - 5), (cx - 1, cy - 5),
            (cx - 4, cy - 4),
        ])
        # Bright highlights on bangs
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["hair_light"], (cx - 3, cy - 8, 2, 1))
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["hair_light"], (cx + 3, cy - 8, 2, 1))
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["hair_shine"], (cx, cy - 9, 1, 1))
        # Side locks (falling in front of face)
        for side_x in (-7, 8):
            lock_x = cx + side_x
            lock_pts = [
                (lock_x, cy - 4),
                (lock_x - 1 + int(sway), cy + 4),
                (lock_x + int(sway), cy + 10),
                (lock_x + 2 + int(sway * 0.5), cy + 6),
                (lock_x + 1, cy - 2),
            ]
            _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["hair_dark"],
                                [(px + 1, py + 1) for px, py in lock_pts])
            _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["hair_mid"], lock_pts)
            pygame.draw.rect(surface, _NS_lyrienne.PALETTE["hair_light"],
                             (lock_x + int(sway), cy + 2, 1, 1))
    def _draw_head_flower(surface, cx, cy, facing, phase):
        """Golden flower ornament on head."""
        # Central golden flower (5 petals)
        flower_r = 4
        # Petals
        for i in range(5):
            ang = i * math.pi * 2 / 5 - math.pi / 2
            px_petal = cx + int(math.cos(ang) * flower_r)
            py_petal = cy + int(math.sin(ang) * flower_r)
            # Petal shape (small triangle)
            _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["gold_dark"], [
                (cx, cy), (px_petal, py_petal),
                (cx + int(math.cos(ang + 0.5) * flower_r * 0.7),
                 cy + int(math.sin(ang + 0.5) * flower_r * 0.7)),
            ])
            _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["gold_mid"], [
                (cx, cy),
                (int((cx + px_petal) / 2), int((cy + py_petal) / 2)),
                (cx + int(math.cos(ang + 0.3) * flower_r * 0.5),
                 cy + int(math.sin(ang + 0.3) * flower_r * 0.5)),
            ])
        # Central purple gem
        gem_pulse = math.sin(phase * 2) * 0.3 + 0.7
        gem_alpha = _NS_lyrienne._alpha(230 * gem_pulse)
        _NS_lyrienne._aacircle(surface, (*_NS_lyrienne.PALETTE["crystal_dark"], gem_alpha),
                                (cx, cy), 2)
        _NS_lyrienne._aacircle(surface, (*_NS_lyrienne.PALETTE["crystal_mid"], gem_alpha),
                                (cx, cy), 1)
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["crystal_shine"], (cx, cy, 1, 1))
        # Gold sparkle rays
        for i in range(4):
            ang = phase * 2 + i * math.pi / 2
            sx = cx + int(math.cos(ang) * 7)
            sy = cy + int(math.sin(ang) * 7)
            pygame.draw.rect(surface, _NS_lyrienne.PALETTE["gold_light"], (sx, sy, 1, 1))
    def _draw_magic_staff(surface, cx, cy, facing, phase, action, attack_progress):
        """Magic staff held by near hand."""
        # Determine hand position and staff angle
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                staff_angle = math.radians(-100 - t * 40) * facing
                staff_len = 30
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                staff_angle = math.radians(-140 + t * 130) * facing
                staff_len = 32
            else:
                t = (attack_progress - 0.6) / 0.4
                staff_angle = math.radians(-10 - t * 60) * facing
                staff_len = 30
            arm_len = 20
            shoulder = (cx + facing * 8, cy - 9)
            hand = (shoulder[0] + int(math.cos(staff_angle * 0.9) * arm_len),
                    shoulder[1] + int(math.sin(staff_angle * 0.9) * arm_len))
        else:
            # Idle: staff held vertically at side
            idle_sway = math.sin(phase * 0.6) * 2
            hand = (cx + facing * 15, cy + 8 + int(idle_sway * 0.4))
            staff_angle = math.radians(-95)  # nearly vertical, slight tilt
            staff_len = 34
        # Staff direction
        ux = math.cos(staff_angle)
        uy = math.sin(staff_angle)
        # Staff bottom (below hand)
        bottom_x = hand[0] - int(ux * staff_len * 0.3)
        bottom_y = hand[1] - int(uy * staff_len * 0.3)
        # Staff top (above hand)
        top_x = hand[0] + int(ux * staff_len * 0.7)
        top_y = hand[1] + int(uy * staff_len * 0.7)
        # Shadow
        _NS_lyrienne._aaline(surface, _NS_lyrienne.PALETTE["shadow_deep"],
                              (bottom_x + 2, bottom_y + 2),
                              (top_x + 2, top_y + 2), 4)
        # Staff shaft (gold/brown)
        _NS_lyrienne._aaline(surface, _NS_lyrienne.PALETTE["shadow_deep"],
                              (bottom_x, bottom_y), (top_x, top_y), 4)
        _NS_lyrienne._aaline(surface, _NS_lyrienne.PALETTE["gold_darkest"],
                              (bottom_x, bottom_y), (top_x, top_y), 3)
        _NS_lyrienne._aaline(surface, _NS_lyrienne.PALETTE["gold_dark"],
                              (bottom_x, bottom_y), (top_x, top_y), 2)
        _NS_lyrienne._aaline(surface, _NS_lyrienne.PALETTE["gold_mid"],
                              (bottom_x + 1, bottom_y), (top_x + 1, top_y), 1)
        # Staff decorations (small gold bands)
        for band_t in (0.35, 0.55):
            bx = int(hand[0] + ux * (staff_len * 0.7 * band_t))
            by = int(hand[1] + uy * (staff_len * 0.7 * band_t))
            perp_x = -uy
            perp_y = ux
            a = (bx + int(perp_x * 2), by + int(perp_y * 2))
            b = (bx - int(perp_x * 2), by - int(perp_y * 2))
            pygame.draw.line(surface, _NS_lyrienne.PALETTE["gold_dark"], a, b, 2)
            pygame.draw.line(surface, _NS_lyrienne.PALETTE["gold_light"], a, b, 1)
        # STAFF TOP — big glowing crystal in ornamental setting
        _NS_lyrienne._draw_staff_crystal(surface, (top_x, top_y), staff_angle, phase)
        # Bottom cap
        pygame.draw.circle(surface, _NS_lyrienne.PALETTE["gold_dark"],
                           (bottom_x, bottom_y), 3)
        pygame.draw.circle(surface, _NS_lyrienne.PALETTE["gold_mid"],
                           (bottom_x, bottom_y), 2)
        pygame.draw.circle(surface, _NS_lyrienne.PALETTE["gold_light"],
                           (bottom_x, bottom_y), 1)
    def _draw_staff_crystal(surface, top_pt, angle, phase):
        """Ornate crystal top with glowing purple crystal."""
        tx, ty = top_pt
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        ux = math.cos(angle)
        uy = math.sin(angle)
        # Ornamental gold curls (leaf-like) surrounding crystal
        # 3 leaves fanning out
        for i, leaf_ang_off in enumerate((-0.7, 0.0, 0.7)):
            leaf_ang = angle + leaf_ang_off
            leaf_len = 8
            leaf_tip_x = tx + int(math.cos(leaf_ang) * leaf_len)
            leaf_tip_y = ty + int(math.sin(leaf_ang) * leaf_len)
            # Perpendicular for leaf width
            perp_x = -math.sin(leaf_ang)
            perp_y = math.cos(leaf_ang)
            mid_x = tx + int(math.cos(leaf_ang) * leaf_len * 0.5)
            mid_y = ty + int(math.sin(leaf_ang) * leaf_len * 0.5)
            side_a = (mid_x + int(perp_x * 3), mid_y + int(perp_y * 3))
            side_b = (mid_x - int(perp_x * 3), mid_y - int(perp_y * 3))
            _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["shadow_deep"], [
                (tx + 1, ty + 1), (leaf_tip_x + 1, leaf_tip_y + 1),
                (side_a[0] + 1, side_a[1] + 1),
            ])
            _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["gold_dark"], [
                (tx, ty), (leaf_tip_x, leaf_tip_y), side_a,
            ])
            _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["gold_dark"], [
                (tx, ty), (leaf_tip_x, leaf_tip_y), side_b,
            ])
            _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["gold_mid"], [
                (tx, ty),
                (int((tx + leaf_tip_x) / 2), int((ty + leaf_tip_y) / 2)),
                side_a,
            ])
            _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["gold_light"], [
                (tx, ty),
                (int((tx + leaf_tip_x) / 2), int((ty + leaf_tip_y) / 2)),
                (int((tx + side_a[0]) / 2), int((ty + side_a[1]) / 2)),
            ])
        # CENTRAL BIG CRYSTAL (violet glowing)
        crystal_cx = tx + int(ux * 3)
        crystal_cy = ty + int(uy * 3)
        # Layered glow
        for r in range(10, 0, -1):
            alpha = _NS_lyrienne._alpha(100 * (10 - r) / 10 * pulse)
            _NS_lyrienne._aacircle(surface,
                                    (*_NS_lyrienne.PALETTE["magic_light"], alpha),
                                    (crystal_cx, crystal_cy), r)
        # Crystal body (diamond shape)
        cr_size = 5
        diamond_pts = [
            (crystal_cx, crystal_cy - cr_size),
            (crystal_cx + cr_size - 1, crystal_cy),
            (crystal_cx, crystal_cy + cr_size),
            (crystal_cx - cr_size + 1, crystal_cy),
        ]
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["shadow_deep"],
                            [(px + 1, py + 1) for px, py in diamond_pts])
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["crystal_dark"], diamond_pts)
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["crystal_mid"], [
            (crystal_cx, crystal_cy - cr_size + 1),
            (crystal_cx + cr_size - 2, crystal_cy),
            (crystal_cx, crystal_cy + cr_size - 1),
            (crystal_cx - cr_size + 2, crystal_cy),
        ])
        _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["crystal_light"], [
            (crystal_cx, crystal_cy - cr_size + 2),
            (crystal_cx + cr_size - 3, crystal_cy),
            (crystal_cx, crystal_cy + cr_size - 2),
            (crystal_cx - cr_size + 3, crystal_cy),
        ])
        # Bright center
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["crystal_shine"],
                         (crystal_cx, crystal_cy, 1, 1))
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["magic_shine"],
                         (crystal_cx - 1, crystal_cy - 1, 1, 1))
        # Rotating small notes around crystal
        for i in range(3):
            ang = phase * 1.8 + i * math.pi * 2 / 3
            nx = crystal_cx + int(math.cos(ang) * 8)
            ny = crystal_cy + int(math.sin(ang) * 8)
            alpha = _NS_lyrienne._alpha(200 * pulse)
            _NS_lyrienne._draw_music_note(surface, nx, ny, 1,
                                           _NS_lyrienne.PALETTE["magic_hot"], alpha)
    # ============================================================
    # STAFF SLASH (basic attack arc)
    # ============================================================
    def _draw_staff_slash(surface, cx, cy, facing, progress):
        """Purple magic arc from staff swing."""
        if progress < 0.35 or progress > 0.75:
            return
        t = (progress - 0.35) / 0.4
        intensity = math.sin(t * math.pi)
        alpha = _NS_lyrienne._alpha(240 * intensity)
        arc_cx = cx + facing * 20
        arc_cy = cy - 4
        arc_r = 26
        # Slash arc lines
        start_angle = math.radians(-80) if facing > 0 else math.radians(180 + 80)
        end_angle = math.radians(80) if facing > 0 else math.radians(180 - 80)
        sweep = start_angle + (end_angle - start_angle) * t
        trail_start = start_angle + (end_angle - start_angle) * max(0, t - 0.4)
        prev_pt = None
        num_segments = 12
        for i in range(num_segments + 1):
            seg_t = i / num_segments
            angle = trail_start + (sweep - trail_start) * seg_t
            px = arc_cx + int(math.cos(angle) * arc_r)
            py = arc_cy + int(math.sin(angle) * arc_r)
            if prev_pt is not None:
                for thickness, color in [
                    (5, (*_NS_lyrienne.PALETTE["magic_darkest"], alpha // 3)),
                    (3, (*_NS_lyrienne.PALETTE["magic_dark"], alpha // 2)),
                    (2, (*_NS_lyrienne.PALETTE["magic_mid"], alpha)),
                    (1, (*_NS_lyrienne.PALETTE["magic_light"], alpha)),
                ]:
                    pygame.draw.line(surface, color, prev_pt, (px, py), thickness)
            prev_pt = (px, py)
        # Music notes along arc
        for i in range(5):
            angle = math.radians(-80) + math.radians(160) * (i / 5)
            if facing < 0:
                angle = math.radians(180) - angle
            note_r = arc_r + int(math.sin(i + progress * 8) * 4)
            nx = arc_cx + int(math.cos(angle) * note_r)
            ny = arc_cy + int(math.sin(angle) * note_r)
            _NS_lyrienne._draw_music_note(surface, nx, ny, 2,
                                           _NS_lyrienne.PALETTE["magic_hot"], alpha)
        # Sparkles
        for i in range(6):
            angle = math.radians(-70) + math.radians(140) * (i / 6)
            if facing < 0:
                angle = math.radians(180) - angle
            spark_r = arc_r + 8 + int(math.sin(progress * 5 + i) * 3)
            sx = arc_cx + int(math.cos(angle) * spark_r)
            sy = arc_cy + int(math.sin(angle) * spark_r)
            pygame.draw.rect(surface, (*_NS_lyrienne.PALETTE["magic_shine"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_lyrienne.PALETTE["white"], alpha), (sx, sy, 1, 1))
    # ============================================================
    # FLOATING MUSIC NOTES (ambient)
    # ============================================================
    def _draw_floating_notes(surface, cx, cy, phase, intense=False):
        """Music notes floating around the mage."""
        strength = 1.4 if intense else 1.0
        # Orbiting notes
        for i in range(8):
            angle = phase * 0.4 + i * math.pi / 4
            radius = 40 + int(math.sin(phase + i) * 10)
            nx = cx + int(math.cos(angle) * radius)
            ny = cy + int(math.sin(angle) * radius * 0.5)
            alpha = _NS_lyrienne._alpha(220 * strength)
            note_color = _NS_lyrienne.PALETTE["magic_mid"] if i % 2 else _NS_lyrienne.PALETTE["magic_hot"]
            _NS_lyrienne._draw_music_note(surface, nx, ny, 2, note_color, alpha)
        # Rising notes (like bubbles)
        for i in range(5):
            t = (phase * 0.5 + i * 0.2) % 1.0
            rx = cx - 20 + i * 10 + int(math.sin(phase + i) * 3)
            ry = cy + 25 - int(t * 45)
            alpha = _NS_lyrienne._alpha(230 * (1 - t) * strength)
            if alpha > 0:
                _NS_lyrienne._draw_music_note(surface, rx, ry, 2,
                                               _NS_lyrienne.PALETTE["magic_light"], alpha)
        # Sparkle stars
        for i in range(10):
            t = (phase * 0.6 + i * 0.1) % 1.0
            sx = cx - 30 + i * 6 + int(math.sin(phase + i) * 2)
            sy = cy + 20 - int(t * 40)
            alpha = _NS_lyrienne._alpha(220 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_lyrienne.PALETTE["magic_hot"], alpha),
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface, (*_NS_lyrienne.PALETTE["magic_shine"], alpha),
                                 (sx, sy, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((120, 26), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 13 - radius, 100 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (10, 5, 20, 170), (5, 8, 110, 10))
        surface.blit(shadow, (x - 60, y - 13))
    def _draw_magic_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_lyrienne._alpha((90 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_lyrienne._aacircle(aura, (*_NS_lyrienne.PALETTE["mist_dark"], alpha),
                                        (110, 100), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_lyrienne._alpha((55 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_lyrienne._aacircle(aura, (*_NS_lyrienne.PALETTE["mist_mid"], alpha),
                                        (110, 100), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_lyrienne._alpha((30 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_lyrienne._aacircle(aura, (*_NS_lyrienne.PALETTE["magic_dark"], alpha),
                                        (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))
        # Floating outer sparks
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 50 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_lyrienne.PALETTE["magic_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_lyrienne.PALETTE["magic_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_lyrienne.PALETTE["mist_dark"], 200),
                            (5, 15, 160, 25), 3)
        pygame.draw.ellipse(ring, (*_NS_lyrienne.PALETTE["magic_darkest"], 220),
                            (14, 18, 142, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_lyrienne.PALETTE["magic_dark"], 230),
                            (25, 20, 120, 16), 1)
        # Music-themed runes (small notes around ring)
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            rx = 85 + int(math.cos(angle) * 50)
            ry = 27 + int(math.sin(angle) * 9)
            _NS_lyrienne._draw_music_note(ring, rx, ry, 1,
                                           _NS_lyrienne.PALETTE["magic_light"], 220)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_lyrienne.PALETTE["magic_hot"],
                                        _NS_lyrienne._alpha(150 * pulse)),
                                (14, 10, 142, 36), 1)
        surface.blit(ring, (x - 85, y - 25))
    # ============================================================
    # SKILL Q - MELODY WAVE (range projectile)
    # ============================================================
    def _draw_melodywave_skill(surface, boss, x, y, timer, phase):
        """Purple music wave projectile toward target."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_lyrienne._target_position(boss, x, y)
        # Charge point (staff tip)
        start_x = x + facing * 24
        start_y = y - 8
        if progress < 0.25:
            # Charge at staff
            t = progress / 0.25
            cr = int(4 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_lyrienne._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_lyrienne._aacircle(surface, (*_NS_lyrienne.PALETTE["magic_dark"], alpha),
                                        (start_x, start_y), r)
            _NS_lyrienne._aacircle(surface, _NS_lyrienne.PALETTE["magic_mid"],
                                    (start_x, start_y), cr - 2)
            _NS_lyrienne._aacircle(surface, _NS_lyrienne.PALETTE["magic_hot"],
                                    (start_x, start_y), max(1, cr - 4))
            _NS_lyrienne._aacircle(surface, _NS_lyrienne.PALETTE["magic_shine"],
                                    (start_x, start_y), max(1, cr - 6))
        else:
            t = (progress - 0.25) / 0.75
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Direction of travel
            dx = tx - start_x
            dy = ty - start_y
            travel_len = max(1, math.sqrt(dx * dx + dy * dy))
            ux, uy = dx / travel_len, dy / travel_len
            perp_x, perp_y = -uy, ux
            # Wave body — series of curved crescents
            wave_len = 20
            # Draw as 3 curved lines (main wave + 2 side echoes)
            for wave_line in (-4, 0, 4):
                # Create wave path as offset polyline
                num_pts = 8
                wave_pts = []
                for i in range(num_pts):
                    pt = i / (num_pts - 1)
                    wx = bx - int(ux * wave_len * pt)
                    wy = by - int(uy * wave_len * pt)
                    # Sinusoidal offset
                    offset = math.sin(pt * math.pi * 2 + phase * 3) * (3 + wave_line * 0.3)
                    wx += int(perp_x * (wave_line + offset))
                    wy += int(perp_y * (wave_line + offset))
                    wave_pts.append((wx, wy))
                # Draw wave line
                for i in range(len(wave_pts) - 1):
                    for thickness, color in [
                        (5, (*_NS_lyrienne.PALETTE["magic_darkest"], 120)),
                        (3, (*_NS_lyrienne.PALETTE["magic_dark"], 180)),
                        (2, (*_NS_lyrienne.PALETTE["magic_mid"], 220)),
                        (1, (*_NS_lyrienne.PALETTE["magic_light"], 240)),
                    ]:
                        pygame.draw.line(surface, color, wave_pts[i], wave_pts[i + 1],
                                          thickness)
            # Bright wave head (music note as projectile head)
            for r in range(10, 3, -1):
                alpha = _NS_lyrienne._alpha(120 * (10 - r) / 10)
                _NS_lyrienne._aacircle(surface, (*_NS_lyrienne.PALETTE["magic_light"], alpha),
                                        (bx, by), r)
            _NS_lyrienne._aacircle(surface, _NS_lyrienne.PALETTE["magic_darkest"], (bx, by), 6)
            _NS_lyrienne._aacircle(surface, _NS_lyrienne.PALETTE["magic_dark"], (bx, by), 4)
            _NS_lyrienne._aacircle(surface, _NS_lyrienne.PALETTE["magic_mid"], (bx, by), 3)
            _NS_lyrienne._aacircle(surface, _NS_lyrienne.PALETTE["magic_light"], (bx, by), 2)
            _NS_lyrienne._aacircle(surface, _NS_lyrienne.PALETTE["magic_shine"], (bx, by), 1)
            pygame.draw.rect(surface, _NS_lyrienne.PALETTE["white"], (bx, by, 1, 1))
            # Trailing music notes
            for i in range(6):
                trail_t = max(0, t - i * 0.06)
                if trail_t <= 0:
                    continue
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_lyrienne._alpha(200 - i * 25)
                _NS_lyrienne._draw_music_note(surface, px, py, 2,
                                               _NS_lyrienne.PALETTE["magic_hot"], alpha)
            # Impact burst
            if t > 0.88:
                st = (t - 0.88) / 0.12
                r = int(12 + st * 25)
                alpha = _NS_lyrienne._alpha(240 * (1 - st))
                # Musical circle at impact
                _NS_lyrienne._aacircle(surface, (*_NS_lyrienne.PALETTE["magic_darkest"], alpha),
                                        (tx, ty), r + 3, 3)
                _NS_lyrienne._aacircle(surface, (*_NS_lyrienne.PALETTE["magic_dark"], alpha),
                                        (tx, ty), r, 3)
                _NS_lyrienne._aacircle(surface, (*_NS_lyrienne.PALETTE["magic_mid"], alpha),
                                        (tx, ty), max(1, r - 6), 2)
                _NS_lyrienne._aacircle(surface, (*_NS_lyrienne.PALETTE["magic_hot"], alpha),
                                        (tx, ty), max(1, r - 12), 1)
                # Notes fly outward
                for i in range(8):
                    angle_s = i * math.pi / 4
                    nx = tx + int(math.cos(angle_s) * r)
                    ny = ty + int(math.sin(angle_s) * r * 0.8)
                    _NS_lyrienne._draw_music_note(surface, nx, ny, 2,
                                                   _NS_lyrienne.PALETTE["magic_shine"], alpha)
    # ============================================================
    # SKILL W - RHYTHM OF CARE (heal AoE)
    # ============================================================
    def _draw_care_ground(surface, boss, x, y, timer, pulse):
        """Heal green circle on ground at target."""
        tx, ty = _NS_lyrienne._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(55 * min(1.0, progress * 2))
        if r > 3:
            # Concentric green circles
            pygame.draw.ellipse(surface, (*_NS_lyrienne.PALETTE["heal_dark"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_lyrienne.PALETTE["heal_mid"], 180),
                                (tx - r + 4, ty - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_lyrienne.PALETTE["heal_light"], 150),
                                (tx - r + 10, ty - r // 3 + 5,
                                 r * 2 - 20, r * 2 // 3 - 10), 1)
    def _draw_care_foreground(surface, boss, x, y, timer, phase):
        """Rising heal music notes at target."""
        tx, ty = _NS_lyrienne._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r_check = int(55 * min(1.0, progress * 2))
        if r_check < 3:
            return
        # Rising green music notes
        for i in range(10):
            note_t = (phase * 0.6 + i * 0.1) % 1.0
            angle_offset = i * math.pi * 2 / 10
            spread_r = 30 + int(math.cos(phase + i) * 8)
            nx = tx + int(math.cos(angle_offset) * spread_r)
            ny_base = ty + int(math.sin(angle_offset) * spread_r * 0.5)
            ny = ny_base - int(note_t * 30)
            alpha = _NS_lyrienne._alpha(230 * (1 - note_t))
            note_color = _NS_lyrienne.PALETTE["heal_mid"] if i % 2 else _NS_lyrienne.PALETTE["heal_light"]
            _NS_lyrienne._draw_music_note(surface, nx, ny, 2, note_color, alpha)
        # Green sparkles
        for i in range(12):
            spark_t = (phase * 0.8 + i * 0.08) % 1.0
            angle = i * math.pi * 2 / 12
            sr = 40 + int(math.sin(phase + i) * 6)
            sx = tx + int(math.cos(angle) * sr)
            sy = ty + int(math.sin(angle) * sr * 0.5) - int(spark_t * 20)
            alpha = _NS_lyrienne._alpha(220 * (1 - spark_t))
            pygame.draw.rect(surface, (*_NS_lyrienne.PALETTE["heal_light"], alpha), (sx, sy, 1, 1))
            pygame.draw.rect(surface, (*_NS_lyrienne.PALETTE["white"], alpha), (sx, sy, 1, 1))
        # Central heal glow (with + symbol)
        pulse_c = math.sin(phase * 3) * 0.3 + 0.7
        for r in range(15, 0, -2):
            alpha = _NS_lyrienne._alpha(80 * (15 - r) / 15 * pulse_c)
            _NS_lyrienne._aacircle(surface, (*_NS_lyrienne.PALETTE["heal_mid"], alpha), (tx, ty), r)
        # Plus sign
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["heal_light"], (tx - 3, ty - 1, 7, 2))
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["heal_light"], (tx - 1, ty - 3, 2, 7))
        pygame.draw.rect(surface, _NS_lyrienne.PALETTE["white"], (tx, ty, 1, 1))
        # Heal numbers floating up
        for i in range(3):
            num_t = (phase * 0.5 + i * 0.33) % 1.0
            nx = tx - 20 + i * 15
            ny = ty - 25 - int(num_t * 25)
            alpha = _NS_lyrienne._alpha(220 * (1 - num_t))
            # Draw "+" symbol as heal number placeholder
            pygame.draw.rect(surface, (*_NS_lyrienne.PALETTE["heal_light"], alpha), (nx, ny, 3, 1))
            pygame.draw.rect(surface, (*_NS_lyrienne.PALETTE["heal_light"], alpha), (nx + 1, ny - 1, 1, 3))
    # ============================================================
    # SKILL E - SONATA BIND (CC projectile with stun)
    # ============================================================
    def _draw_sonatabind_skill(surface, boss, x, y, timer, phase):
        """String/arrow of purple that binds target."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_lyrienne._target_position(boss, x, y)
        start_x = x + facing * 24
        start_y = y - 8
        if progress < 0.2:
            # Charge (bow forming)
            t = progress / 0.2
            cr = int(4 + t * 6)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_lyrienne._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_lyrienne._aacircle(surface, (*_NS_lyrienne.PALETTE["magic_dark"], alpha),
                                        (start_x, start_y), r)
            _NS_lyrienne._aacircle(surface, _NS_lyrienne.PALETTE["magic_mid"],
                                    (start_x, start_y), cr - 2)
            _NS_lyrienne._aacircle(surface, _NS_lyrienne.PALETTE["magic_hot"],
                                    (start_x, start_y), max(1, cr - 4))
        elif progress < 0.6:
            # ARROW FLYING TO TARGET
            t = (progress - 0.2) / 0.4
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            dx = tx - start_x
            dy = ty - start_y
            travel_len = max(1, math.sqrt(dx * dx + dy * dy))
            ux, uy = dx / travel_len, dy / travel_len
            perp_x, perp_y = -uy, ux
            # ARROW BODY (elongated line with pointed tip)
            arrow_len = 16
            tip_x = bx + int(ux * arrow_len // 2)
            tip_y = by + int(uy * arrow_len // 2)
            tail_x = bx - int(ux * arrow_len // 2)
            tail_y = by - int(uy * arrow_len // 2)
            # Arrow shaft
            for thickness, color in [
                (5, _NS_lyrienne.PALETTE["magic_darkest"]),
                (3, _NS_lyrienne.PALETTE["magic_dark"]),
                (2, _NS_lyrienne.PALETTE["magic_mid"]),
                (1, _NS_lyrienne.PALETTE["magic_light"]),
            ]:
                pygame.draw.line(surface, color, (tail_x, tail_y), (tip_x, tip_y), thickness)
            # Arrow head (diamond)
            head_a = (tip_x + int(perp_x * 3), tip_y + int(perp_y * 3))
            head_b = (tip_x - int(perp_x * 3), tip_y - int(perp_y * 3))
            head_tip = (tip_x + int(ux * 4), tip_y + int(uy * 4))
            _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["magic_darkest"],
                                [head_a, head_b, head_tip])
            _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["magic_mid"], [
                (int((head_a[0] + tip_x) / 2), int((head_a[1] + tip_y) / 2)),
                (int((head_b[0] + tip_x) / 2), int((head_b[1] + tip_y) / 2)),
                head_tip,
            ])
            pygame.draw.rect(surface, _NS_lyrienne.PALETTE["magic_shine"],
                             (head_tip[0], head_tip[1], 1, 1))
            # Arrow fletching (at tail)
            fletch_a = (tail_x + int(perp_x * 3) - int(ux * 3),
                         tail_y + int(perp_y * 3) - int(uy * 3))
            fletch_b = (tail_x - int(perp_x * 3) - int(ux * 3),
                         tail_y - int(perp_y * 3) - int(uy * 3))
            fletch_pt_a = (tail_x + int(perp_x * 2), tail_y + int(perp_y * 2))
            fletch_pt_b = (tail_x - int(perp_x * 2), tail_y - int(perp_y * 2))
            _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["magic_hot"],
                                [fletch_pt_a, fletch_a, (tail_x, tail_y)])
            _NS_lyrienne._poly(surface, _NS_lyrienne.PALETTE["magic_hot"],
                                [fletch_pt_b, fletch_b, (tail_x, tail_y)])
            # Trailing string/thread (like a music string)
            for i in range(1, 10):
                trail_t = max(0, t - i * 0.04)
                if trail_t <= 0:
                    continue
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_lyrienne._alpha(180 - i * 20)
                # Small string wave
                wobble = math.sin(trail_t * 10) * 2
                px += int(perp_x * wobble)
                py += int(perp_y * wobble)
                pygame.draw.line(surface, (*_NS_lyrienne.PALETTE["magic_light"], alpha),
                                 (px, py), (px + int(perp_x * 2), py + int(perp_y * 2)), 1)
            # Impact burst at target
            if t > 0.9:
                st = (t - 0.9) / 0.1
                r = int(10 + st * 20)
                alpha = _NS_lyrienne._alpha(250 * (1 - st))
                # Big star burst
                for i in range(8):
                    ang_s = i * math.pi / 4
                    ex = tx + int(math.cos(ang_s) * r)
                    ey = ty + int(math.sin(ang_s) * r)
                    pygame.draw.line(surface, (*_NS_lyrienne.PALETTE["magic_light"], alpha),
                                     (tx, ty), (ex, ey), 3)
                    pygame.draw.line(surface, (*_NS_lyrienne.PALETTE["magic_shine"], alpha),
                                     (tx, ty), (ex, ey), 1)
                    pygame.draw.rect(surface, (*_NS_lyrienne.PALETTE["white"], alpha),
                                     (ex, ey, 2, 2))
        else:
            # STUN: target bound with strings + rotating notes
            t = (progress - 0.6) / 0.4
            # Rotating stun stars around target
            for i in range(4):
                ang = phase * 3 + i * math.pi / 2
                sr = 18
                sx = tx + int(math.cos(ang) * sr)
                sy = ty + int(math.sin(ang) * sr * 0.6)
                # Stun star (multi-pointed)
                alpha = _NS_lyrienne._alpha(220 * (1 - t))
                for pt_i in range(4):
                    star_ang = pt_i * math.pi / 2 + phase
                    ex = sx + int(math.cos(star_ang) * 3)
                    ey = sy + int(math.sin(star_ang) * 3)
                    pygame.draw.line(surface, (*_NS_lyrienne.PALETTE["magic_hot"], alpha),
                                     (sx, sy), (ex, ey), 2)
                pygame.draw.rect(surface, (*_NS_lyrienne.PALETTE["magic_shine"], alpha),
                                 (sx, sy, 1, 1))
            # Binding string around target
            for i in range(6):
                ang = phase * 2 + i * math.pi / 3
                sr = 12
                bx1 = tx + int(math.cos(ang) * sr)
                by1 = ty + int(math.sin(ang) * sr * 0.7)
                alpha = _NS_lyrienne._alpha(200 * (1 - t))
                pygame.draw.line(surface, (*_NS_lyrienne.PALETTE["magic_mid"], alpha),
                                 (tx, ty), (bx1, by1), 1)
    # ============================================================
    # SKILL R - SYMPHONY OF HARMONY (ultimate concert AoE)
    # ============================================================
    def _draw_symphony_ground(surface, boss, x, y, timer, phase):
        """Big musical ground circle."""
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(90 * min(1.0, progress * 1.5))
        if r > 5:
            # Big concentric ring pattern
            for ring_i in range(4):
                ring_r = r - ring_i * 15
                if ring_r <= 0:
                    continue
                alpha = _NS_lyrienne._alpha(200 - ring_i * 30)
                pygame.draw.ellipse(surface, (*_NS_lyrienne.PALETTE["magic_darkest"], alpha),
                                    (x - ring_r, y + 40 - ring_r // 3,
                                     ring_r * 2, ring_r * 2 // 3), 2)
                pygame.draw.ellipse(surface, (*_NS_lyrienne.PALETTE["magic_mid"], alpha),
                                    (x - ring_r + 3, y + 40 - ring_r // 3 + 2,
                                     ring_r * 2 - 6, ring_r * 2 // 3 - 4), 1)
            # Music notes on outer ring
            for i in range(10):
                ang = i * math.pi / 5 + phase * 0.3
                nx = x + int(math.cos(ang) * r)
                ny = y + 40 + int(math.sin(ang) * r * 0.35)
                _NS_lyrienne._draw_music_note(surface, nx, ny, 2,
                                               _NS_lyrienne.PALETTE["magic_hot"], 220)
    def _draw_symphony_foreground(surface, boss, x, y, timer, phase):
        """Big magical treble clef + music notes rising."""
        duration = 110
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.35:
            # Wind-up: gathering magic at staff
            t = progress / 0.35
            gather_y = y - 20 - int(t * 15)
            gr = int(6 + t * 12)
            for r in range(gr + 5, 0, -1):
                alpha = _NS_lyrienne._alpha(160 * (gr + 5 - r) / (gr + 5))
                _NS_lyrienne._aacircle(surface, (*_NS_lyrienne.PALETTE["magic_light"], alpha),
                                        (x, gather_y), r)
            _NS_lyrienne._aacircle(surface, _NS_lyrienne.PALETTE["magic_mid"], (x, gather_y), gr - 2)
            _NS_lyrienne._aacircle(surface, _NS_lyrienne.PALETTE["magic_hot"], (x, gather_y), max(1, gr - 4))
            _NS_lyrienne._aacircle(surface, _NS_lyrienne.PALETTE["magic_shine"], (x, gather_y), max(1, gr - 6))
            # Rising notes into gather point
            for i in range(6):
                ang = i * math.pi / 3 + phase * 2
                dist = int(20 + t * 15)
                nx = x + int(math.cos(ang) * dist)
                ny = gather_y + int(math.sin(ang) * dist * 0.5)
                alpha = _NS_lyrienne._alpha(220)
                _NS_lyrienne._draw_music_note(surface, nx, ny, 2,
                                               _NS_lyrienne.PALETTE["magic_hot"], alpha)
        elif progress < 0.8:
            # ACTIVE SYMPHONY
            t = (progress - 0.35) / 0.45
            intensity = math.sin(t * math.pi)
            # HUGE TREBLE CLEF in center (glowing)
            clef_alpha = _NS_lyrienne._alpha(240 * intensity)
            # Layered treble clef
            for size_layer in (10, 9, 8):
                _NS_lyrienne._draw_treble_clef(surface, x, y - 5, size_layer,
                                                _NS_lyrienne.PALETTE["magic_darkest"], clef_alpha)
            _NS_lyrienne._draw_treble_clef(surface, x, y - 5, 8,
                                            _NS_lyrienne.PALETTE["magic_dark"], clef_alpha)
            _NS_lyrienne._draw_treble_clef(surface, x, y - 5, 7,
                                            _NS_lyrienne.PALETTE["magic_mid"], clef_alpha)
            _NS_lyrienne._draw_treble_clef(surface, x, y - 5, 6,
                                            _NS_lyrienne.PALETTE["magic_light"], clef_alpha)
            # Big central glow behind clef
            for r in range(30, 5, -3):
                alpha = _NS_lyrienne._alpha(80 * (30 - r) / 30 * intensity)
                _NS_lyrienne._aacircle(surface, (*_NS_lyrienne.PALETTE["magic_mid"], alpha),
                                        (x, y - 5), r)
            # Music staff lines (5 horizontal lines like sheet music)
            for line_i in range(5):
                ly = y + 5 + line_i * 4 - 15
                # Curved line across
                for i in range(0, 140, 4):
                    lx = x - 70 + i
                    y_offset = math.sin(phase * 2 + i * 0.1) * 2
                    alpha = _NS_lyrienne._alpha(180 * intensity)
                    pygame.draw.rect(surface, (*_NS_lyrienne.PALETTE["magic_light"], alpha),
                                     (lx, ly + int(y_offset), 3, 1))
            # Music notes rising and falling in patterns
            for i in range(16):
                note_t = (phase * 0.8 + i * 0.08) % 1.0
                nx = x - 80 + i * 10 + int(math.sin(phase + i) * 3)
                ny = y - 30 + int(math.sin(phase * 2 + i * 0.5) * 12)
                alpha = _NS_lyrienne._alpha(230 * intensity)
                # Vary note colors
                colors = [_NS_lyrienne.PALETTE["magic_light"],
                          _NS_lyrienne.PALETTE["magic_hot"],
                          _NS_lyrienne.PALETTE["magic_shine"]]
                note_color = colors[i % 3]
                size = 2 + (i % 2)
                _NS_lyrienne._draw_music_note(surface, nx, ny, size, note_color, alpha)
            # Rotating outer notes (bigger orbit)
            for i in range(8):
                ang = phase * 1.5 + i * math.pi / 4
                r_orb = 60
                nx = x + int(math.cos(ang) * r_orb)
                ny = y + int(math.sin(ang) * r_orb * 0.6)
                alpha = _NS_lyrienne._alpha(230 * intensity)
                _NS_lyrienne._draw_music_note(surface, nx, ny, 3,
                                               _NS_lyrienne.PALETTE["magic_hot"], alpha)
            # Big burst rings expanding outward
            for burst_i in range(3):
                burst_t = (phase * 0.8 + burst_i * 0.33) % 1.0
                burst_r = int(burst_t * 80)
                burst_alpha = _NS_lyrienne._alpha(220 * (1 - burst_t) * intensity)
                _NS_lyrienne._aacircle(surface, (*_NS_lyrienne.PALETTE["magic_light"], burst_alpha),
                                        (x, y), burst_r, 2)
                _NS_lyrienne._aacircle(surface, (*_NS_lyrienne.PALETTE["magic_shine"], burst_alpha),
                                        (x, y), burst_r, 1)
            # Sparkle stars everywhere
            for i in range(20):
                spark_ang = i * math.pi / 10 + phase * 0.5
                sr = 40 + int(math.sin(phase * 2 + i) * 15)
                sx = x + int(math.cos(spark_ang) * sr)
                sy = y + int(math.sin(spark_ang) * sr * 0.6)
                alpha = _NS_lyrienne._alpha(240 * intensity)
                pygame.draw.rect(surface, (*_NS_lyrienne.PALETTE["magic_shine"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_lyrienne.PALETTE["white"], alpha), (sx, sy, 1, 1))
        else:
            # Aftermath: notes drifting away
            t = (progress - 0.8) / 0.2
            for i in range(12):
                drift_t = (phase * 0.5 + i * 0.08) % 1.0
                ang = i * math.pi / 6
                dr = 30 + int(drift_t * 60)
                dx = x + int(math.cos(ang) * dr)
                dy = y + int(math.sin(ang) * dr * 0.6) - int(drift_t * 20)
                alpha = _NS_lyrienne._alpha(180 * (1 - t) * (1 - drift_t))
                if alpha > 0:
                    _NS_lyrienne._draw_music_note(surface, dx, dy, 2,
                                                   _NS_lyrienne.PALETTE["magic_light"], alpha)



# ====================================================================
# VALTHAR (SENTINEL OF BROKEN KINGS) - Mini Boss
# ====================================================================

class _NS_valthar:
    """Namespace valthar - mini boss colossus armor emas."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Stone armor (silver-white)
        "stone_darkest": (25, 28, 35),
        "stone_dark": (65, 72, 85),
        "stone_mid": (130, 140, 155),
        "stone_light": (200, 208, 220),
        "stone_shine": (245, 248, 255),
        # Dark crevices (between plates)
        "crevice_darkest": (8, 10, 15),
        "crevice_dark": (20, 22, 30),
        # Gold trim (accents)
        "gold_darkest": (40, 25, 5),
        "gold_dark": (110, 75, 20),
        "gold_mid": (200, 155, 55),
        "gold_light": (250, 220, 120),
        "gold_hot": (255, 240, 180),
        "gold_shine": (255, 250, 220),
        # Petricite glow (magic energy)
        "magic_darkest": (30, 20, 5),
        "magic_dark": (100, 70, 15),
        "magic_mid": (210, 165, 50),
        "magic_light": (255, 220, 110),
        "magic_hot": (255, 245, 175),
        # Wing feathers (gold)
        "wing_dark": (85, 55, 15),
        "wing_mid": (175, 130, 45),
        "wing_light": (240, 200, 100),
        "wing_shine": (255, 235, 160),
        # Eye (glowing blue-white — like Galio's petricite eyes)
        "eye_socket": (5, 8, 12),
        "eye_dark": (30, 55, 80),
        "eye_mid": (110, 170, 220),
        "eye_light": (200, 230, 255),
        "eye_glow": (255, 255, 255),
        # Ambient
        "mist_dark": (25, 25, 35),
        "mist_mid": (85, 90, 110),
        "mist_light": (170, 180, 205),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 3, 5),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_valthar._clamp(color)
        if _NS_valthar.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_valthar._clamp(color)
        if _NS_valthar.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_valthar._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 240 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_valthar(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_valthar._update_val_attack_anim(boss)
        attacking = (
            getattr(boss, "_val_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_valthar._draw_gold_aura(surface, x, y, pulse)
        _NS_valthar._draw_ground_ring(surface, x, y + 52, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "r":
            _NS_valthar._draw_entrance_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_valthar._draw_punch_ground(surface, boss, x, y, skill_timer, pulse)
        # Body — floating with slow bob + wing flap
        floating_bob = math.sin(pulse * 0.6) * 5
        if attacking:
            _NS_valthar._draw_val_attack(surface, boss, x, y - floating_bob)
        else:
            _NS_valthar._draw_val_idle(surface, boss, x, y - floating_bob)
        # Shield bubble if W active (over body)
        if active_skill == "w":
            _NS_valthar._draw_shield_bubble(surface, boss, x, y - floating_bob,
                                             skill_timer, pulse)
        # Foreground FX
        if active_skill == "q":
            _NS_valthar._draw_winds_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_valthar._draw_punch_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_valthar._draw_entrance_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_val_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_val_previous_timer", 0))
        active = bool(getattr(boss, "_val_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._val_attack_active = True
            boss._val_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._val_attack_frame = int(getattr(boss, "_val_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._val_attack_active = False
            boss._val_attack_frame = 0
            active = False
        boss._val_previous_timer = timer
        boss._val_attack_progress = (
            min(1.0, getattr(boss, "_val_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_val_idle(surface, boss, x, y):
        _NS_valthar._draw_shadow(surface, x, y + 56)
        _NS_valthar._draw_gold_particles(surface, x, y + 30, boss.pulse)
        _NS_valthar._draw_val_body(surface, x, y, boss.direction, boss.pulse, "idle")
    def _draw_val_attack(surface, boss, x, y):
        progress = getattr(boss, "_val_attack_progress", 0.0)
        # Colossus punch: wind-up → slam → recovery
        if progress < 0.35:
            t = progress / 0.35
            swing_offset = -int(t * 3) * boss.direction
            lift = int(t * 4)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            swing_offset = int((-3 + t * 12)) * boss.direction
            lift = int(4 - t * 8)
        else:
            t = (progress - 0.6) / 0.4
            swing_offset = int(9 * (1 - t)) * boss.direction
            lift = int(-3 + t * 3)
        _NS_valthar._draw_shadow(surface, x + swing_offset, y + 56)
        _NS_valthar._draw_gold_particles(surface, x + swing_offset, y + 30, boss.pulse,
                                          intense=True)
        _NS_valthar._draw_val_body(surface, x + swing_offset, y - lift,
                                     boss.direction, boss.pulse, "attack", progress)
        _NS_valthar._draw_fist_slash(surface, x + swing_offset, y - lift,
                                       boss.direction, progress)
    # ============================================================
    # BODY (upright humanoid colossus with wings)
    # ============================================================
    def _draw_val_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw colossus body: wings, legs, torso, arms, head, crown."""
        # Order: wings (behind) → legs → torso → arms → shoulder pauldrons → head → crown
        _NS_valthar._draw_gold_wings(surface, cx, cy - 8, facing, phase, action,
                                       attack_progress)
        _NS_valthar._draw_colossus_legs(surface, cx, cy + 22, facing, phase)
        _NS_valthar._draw_colossus_torso(surface, cx, cy, facing, phase)
        _NS_valthar._draw_colossus_arms(surface, cx, cy, facing, phase, action,
                                          attack_progress)
        _NS_valthar._draw_shoulder_pauldrons(surface, cx, cy - 8, facing, phase)
        # Head
        head_lunge = 0
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                head_lunge = -int(t * 2) * facing
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                head_lunge = int((-2 + t * 8)) * facing
            else:
                t = (attack_progress - 0.6) / 0.4
                head_lunge = int(6 * (1 - t)) * facing
        _NS_valthar._draw_colossus_head(surface, cx + head_lunge, cy - 24,
                                          facing, phase)
        _NS_valthar._draw_crown(surface, cx + head_lunge, cy - 32, facing, phase)
    def _draw_gold_wings(surface, cx, cy, facing, phase, action, attack_progress):
        """Golden wings behind body (feathered)."""
        # Wing flap
        if action == "attack":
            beat = math.sin(phase * 2 + attack_progress * 4) * 4
        else:
            beat = math.sin(phase * 0.9) * 3
        for side_i, (side_mult, size_mult, alpha_mult) in enumerate([
            (-1, 1.0, 1.0),   # far wing
            (1, 0.72, 0.8),   # near wing
        ]):
            base_x = cx - facing * 4
            base_y = cy - 4
            # Wing bones/spars
            spar1_len = int(30 * size_mult)
            spar1_angle = math.pi * 0.7 * side_mult - math.radians(beat)
            spar2_len = int(34 * size_mult)
            spar2_angle = math.pi * 0.88 * side_mult - math.radians(beat * 0.8)
            spar3_len = int(28 * size_mult)
            spar3_angle = math.pi * 1.05 * side_mult - math.radians(beat * 0.5)
            tip1_x = base_x + int(math.cos(spar1_angle) * spar1_len) * (-facing)
            tip1_y = base_y - int(math.sin(spar1_angle) * spar1_len)
            tip2_x = base_x + int(math.cos(spar2_angle) * spar2_len) * (-facing)
            tip2_y = base_y - int(math.sin(spar2_angle) * spar2_len)
            tip3_x = base_x + int(math.cos(spar3_angle) * spar3_len) * (-facing)
            tip3_y = base_y - int(math.sin(spar3_angle) * spar3_len)
            # Wing membrane (feathered look)
            wing_points = [
                (base_x, base_y),
                (tip1_x, tip1_y),
                (int(tip1_x * 0.6 + tip2_x * 0.4),
                 int(tip1_y * 0.6 + tip2_y * 0.4) + int(4 * size_mult)),
                (tip2_x, tip2_y),
                (int(tip2_x * 0.6 + tip3_x * 0.4),
                 int(tip2_y * 0.6 + tip3_y * 0.4) + int(4 * size_mult)),
                (tip3_x, tip3_y),
                (base_x - facing * 3, base_y + int(6 * size_mult)),
            ]
            wing_surf = pygame.Surface((180, 120), pygame.SRCALPHA)
            offset_x = base_x - 90
            offset_y = base_y - 60
            local_points = [(p[0] - offset_x, p[1] - offset_y)
                            for p in wing_points]
            # Base wing shape (gold)
            _NS_valthar._poly(wing_surf, (*_NS_valthar.PALETTE["gold_darkest"],
                                            int(230 * alpha_mult)), local_points)
            # Inner brighter fill
            inner_pts = []
            cx_local = sum(p[0] for p in local_points) / len(local_points)
            cy_local = sum(p[1] for p in local_points) / len(local_points)
            for p in local_points:
                inner_pts.append(
                    (int(p[0] * 0.82 + cx_local * 0.18),
                     int(p[1] * 0.82 + cy_local * 0.18))
                )
            _NS_valthar._poly(wing_surf, (*_NS_valthar.PALETTE["gold_dark"],
                                            int(230 * alpha_mult)), inner_pts)
            _NS_valthar._poly(wing_surf, (*_NS_valthar.PALETTE["gold_mid"],
                                            int(200 * alpha_mult)), [
                (int(p[0] * 0.7 + cx_local * 0.3),
                 int(p[1] * 0.7 + cy_local * 0.3)) for p in local_points
            ])
            # Feather details (bones + parallel lines)
            bone_base = (base_x - offset_x, base_y - offset_y)
            for tip in [(tip1_x - offset_x, tip1_y - offset_y),
                        (tip2_x - offset_x, tip2_y - offset_y),
                        (tip3_x - offset_x, tip3_y - offset_y)]:
                # Main bone
                pygame.draw.line(wing_surf,
                                 (*_NS_valthar.PALETTE["gold_darkest"],
                                  int(240 * alpha_mult)),
                                 bone_base, tip, 3)
                pygame.draw.line(wing_surf,
                                 (*_NS_valthar.PALETTE["gold_dark"],
                                  int(240 * alpha_mult)),
                                 bone_base, tip, 2)
                pygame.draw.line(wing_surf,
                                 (*_NS_valthar.PALETTE["gold_light"],
                                  int(200 * alpha_mult)),
                                 bone_base, tip, 1)
                # Feathers along bone (perpendicular lines)
                bone_dx = tip[0] - bone_base[0]
                bone_dy = tip[1] - bone_base[1]
                bone_len = math.sqrt(bone_dx * bone_dx + bone_dy * bone_dy)
                if bone_len > 0:
                    perp_x = -bone_dy / bone_len
                    perp_y = bone_dx / bone_len
                    for f in range(3, int(bone_len), 5):
                        fx_start = bone_base[0] + int(bone_dx * f / bone_len)
                        fy_start = bone_base[1] + int(bone_dy * f / bone_len)
                        f_len = 4
                        fx_end = fx_start + int(perp_x * f_len)
                        fy_end = fy_start + int(perp_y * f_len)
                        pygame.draw.line(wing_surf,
                                         (*_NS_valthar.PALETTE["gold_mid"],
                                          int(200 * alpha_mult)),
                                         (fx_start, fy_start), (fx_end, fy_end), 1)
                        pygame.draw.rect(wing_surf,
                                         (*_NS_valthar.PALETTE["gold_shine"],
                                          int(220 * alpha_mult)),
                                         (fx_end, fy_end, 1, 1))
                # Bright tip
                _NS_valthar._aacircle(wing_surf,
                                       (*_NS_valthar.PALETTE["gold_hot"],
                                        int(240 * alpha_mult)), tip, 2)
                pygame.draw.rect(wing_surf,
                                 (*_NS_valthar.PALETTE["gold_shine"],
                                  int(255 * alpha_mult)), (tip[0], tip[1], 1, 1))
            # Bright top edge shine
            pygame.draw.line(wing_surf,
                             (*_NS_valthar.PALETTE["gold_shine"],
                              int(200 * alpha_mult)),
                             bone_base,
                             (tip1_x - offset_x, tip1_y - offset_y), 1)
            surface.blit(wing_surf, (offset_x, offset_y))
    def _draw_colossus_legs(surface, cx, cy, facing, phase):
        """Short stumpy armored legs (colossus has thick short legs)."""
        pulse = math.sin(phase * 0.6) * 1
        # Two thick armored legs
        for side_mult in (-1, 1):
            leg_x = cx + side_mult * 8
            # Thigh
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["shadow_deep"], [
                (leg_x - 5 + 2, cy - 8 + 2), (leg_x + 5 + 2, cy - 8 + 2),
                (leg_x + 6 + 2, cy + 4 + 2), (leg_x - 6 + 2, cy + 4 + 2),
            ])
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_darkest"], [
                (leg_x - 5, cy - 8), (leg_x + 5, cy - 8),
                (leg_x + 6, cy + 4), (leg_x - 6, cy + 4),
            ])
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_dark"], [
                (leg_x - 4, cy - 7), (leg_x + 4, cy - 7),
                (leg_x + 5, cy + 3), (leg_x - 5, cy + 3),
            ])
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_mid"], [
                (leg_x - 3, cy - 6), (leg_x + 3, cy - 6),
                (leg_x + 4, cy + 2), (leg_x - 4, cy + 2),
            ])
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_light"], [
                (leg_x - 2, cy - 5), (leg_x + 1, cy - 5),
                (leg_x + 2, cy + 1), (leg_x - 2, cy + 1),
            ])
            # Knee gold trim
            pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_dark"],
                             (leg_x - 6, cy - 1, 12, 3))
            pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_mid"],
                             (leg_x - 5, cy, 10, 1))
            pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_light"],
                             (leg_x - 1, cy, 2, 1))
            # Lower leg / boot
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["shadow_deep"], [
                (leg_x - 6 + 2, cy + 4 + 2), (leg_x + 6 + 2, cy + 4 + 2),
                (leg_x + 7 + 2, cy + 14 + 2), (leg_x - 7 + 2, cy + 14 + 2),
            ])
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_darkest"], [
                (leg_x - 6, cy + 4), (leg_x + 6, cy + 4),
                (leg_x + 7, cy + 14), (leg_x - 7, cy + 14),
            ])
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_dark"], [
                (leg_x - 5, cy + 5), (leg_x + 5, cy + 5),
                (leg_x + 6, cy + 13), (leg_x - 6, cy + 13),
            ])
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_mid"], [
                (leg_x - 3, cy + 7), (leg_x + 3, cy + 7),
                (leg_x + 4, cy + 11), (leg_x - 4, cy + 11),
            ])
            # Boot gold trim
            pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_dark"],
                             (leg_x - 7, cy + 12, 14, 3))
            pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_mid"],
                             (leg_x - 6, cy + 13, 12, 1))
    def _draw_colossus_torso(surface, cx, cy, facing, phase):
        """Massive armored torso with gold trim and center emblem."""
        breath = math.sin(phase * 0.5) * 1
        # Big blocky torso
        torso_shape = [
            (cx - 18, cy + 18),
            (cx - 22, cy + 8),
            (cx - 24, cy - 4 - int(breath)),
            (cx - 20, cy - 12),
            (cx - 12, cy - 16),
            (cx - 6, cy - 18),
            (cx + 6, cy - 18),
            (cx + 12, cy - 16),
            (cx + 20, cy - 12),
            (cx + 24, cy - 4 - int(breath)),
            (cx + 22, cy + 8),
            (cx + 18, cy + 18),
            (cx + 10, cy + 22),
            (cx - 10, cy + 22),
        ]
        _NS_valthar._poly(surface, _NS_valthar.PALETTE["shadow_deep"],
                           [(px + 2, py + 3) for px, py in torso_shape])
        _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_darkest"], torso_shape)
        # Main stone plate
        _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_dark"], [
            (cx - 17, cy + 17), (cx - 20, cy + 7), (cx - 22, cy - 3),
            (cx - 18, cy - 11), (cx - 10, cy - 15), (cx + 10, cy - 15),
            (cx + 18, cy - 11), (cx + 22, cy - 3), (cx + 20, cy + 7),
            (cx + 17, cy + 17), (cx + 9, cy + 20), (cx - 9, cy + 20),
        ])
        _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_mid"], [
            (cx - 14, cy + 15), (cx - 17, cy + 5), (cx - 19, cy - 2),
            (cx - 15, cy - 10), (cx - 6, cy - 12), (cx + 6, cy - 12),
            (cx + 15, cy - 10), (cx + 19, cy - 2), (cx + 17, cy + 5),
            (cx + 14, cy + 15), (cx + 7, cy + 18), (cx - 7, cy + 18),
        ])
        # Chest highlight
        _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_light"], [
            (cx - 6, cy - 8), (cx + 6, cy - 8), (cx + 9, cy - 2),
            (cx + 5, cy + 6), (cx - 5, cy + 6), (cx - 9, cy - 2),
        ])
        _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_shine"], [
            (cx - 3, cy - 6), (cx + 3, cy - 6), (cx + 4, cy - 2),
            (cx + 2, cy + 2), (cx - 2, cy + 2), (cx - 4, cy - 2),
        ])
        # Plate fracture lines
        for pts in [
            [(cx - 15, cy - 8), (cx - 10, cy - 4), (cx - 14, cy + 4), (cx - 12, cy + 14)],
            [(cx + 15, cy - 8), (cx + 10, cy - 4), (cx + 14, cy + 4), (cx + 12, cy + 14)],
        ]:
            for i in range(len(pts) - 1):
                pygame.draw.line(surface, _NS_valthar.PALETTE["crevice_dark"],
                                 pts[i], pts[i + 1], 1)
        # 🏆 CENTER CHEST EMBLEM (gold V-shape shield)
        # Big gold triangular emblem in center of chest
        emblem_pts = [
            (cx - 6, cy - 4), (cx + 6, cy - 4),
            (cx + 4, cy + 2), (cx, cy + 8), (cx - 4, cy + 2),
        ]
        _NS_valthar._poly(surface, _NS_valthar.PALETTE["gold_darkest"],
                           [(px + 1, py + 1) for px, py in emblem_pts])
        _NS_valthar._poly(surface, _NS_valthar.PALETTE["gold_dark"], emblem_pts)
        _NS_valthar._poly(surface, _NS_valthar.PALETTE["gold_mid"], [
            (cx - 5, cy - 3), (cx + 5, cy - 3),
            (cx + 3, cy + 1), (cx, cy + 6), (cx - 3, cy + 1),
        ])
        _NS_valthar._poly(surface, _NS_valthar.PALETTE["gold_light"], [
            (cx - 3, cy - 2), (cx + 3, cy - 2),
            (cx + 1, cy), (cx, cy + 3), (cx - 1, cy),
        ])
        pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_shine"], (cx, cy - 1, 1, 1))
        # Gold trim borders
        # Belt
        pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_dark"],
                         (cx - 18, cy + 14, 36, 4))
        pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_mid"],
                         (cx - 17, cy + 15, 34, 2))
        pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_light"],
                         (cx - 2, cy + 15, 4, 1))
        # Central belt buckle
        pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_darkest"],
                         (cx - 4, cy + 13, 8, 6))
        pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_dark"],
                         (cx - 3, cy + 14, 6, 4))
        pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_mid"],
                         (cx - 2, cy + 15, 4, 2))
        pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_light"],
                         (cx - 1, cy + 15, 2, 1))
        # Neck trim
        pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_dark"],
                         (cx - 7, cy - 17, 14, 2))
        pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_mid"],
                         (cx - 6, cy - 16, 12, 1))
        # Magic petricite glow spots
        crack_alpha = _NS_valthar._alpha(180 + math.sin(phase * 2) * 55)
        for spot in [(cx - 12, cy), (cx + 12, cy), (cx, cy - 10)]:
            _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["magic_mid"], crack_alpha),
                                   spot, 2)
            _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["magic_hot"], crack_alpha),
                                   spot, 1)
    def _draw_colossus_arms(surface, cx, cy, facing, phase, action, attack_progress):
        """Two massive armored arms."""
        idle_sway = math.sin(phase * 0.5) * 2
        # FAR ARM (behind)
        far_shoulder = (cx - facing * 16, cy - 10)
        far_elbow = (cx - facing * 22, cy - 2)
        far_fist = (cx - facing * 24, cy + 14 + int(idle_sway * 0.3))
        _NS_valthar._draw_stone_arm(surface, far_shoulder, far_elbow, far_fist,
                                      facing, phase, dark=True)
        # NEAR ARM (front) — swings on attack
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                angle = math.radians(-30 - t * 70) * facing
                arm_len = 22
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                angle = math.radians(-100 + t * 160) * facing
                arm_len = 24
            else:
                t = (attack_progress - 0.6) / 0.4
                angle = math.radians(60 - t * 60) * facing
                arm_len = 22
            shoulder = (cx + facing * 16, cy - 10)
            elbow = (shoulder[0] + int(math.cos(angle) * arm_len * 0.5),
                     shoulder[1] + int(math.sin(angle) * arm_len * 0.5))
            fist = (shoulder[0] + int(math.cos(angle) * arm_len),
                    shoulder[1] + int(math.sin(angle) * arm_len))
            _NS_valthar._draw_stone_arm(surface, shoulder, elbow, fist,
                                          facing, phase, dark=False, big_fist=True)
        else:
            near_shoulder = (cx + facing * 16, cy - 10)
            near_elbow = (cx + facing * 22, cy - 1 + int(idle_sway * 0.3))
            near_fist = (cx + facing * 24, cy + 16 + int(idle_sway * 0.5))
            _NS_valthar._draw_stone_arm(surface, near_shoulder, near_elbow, near_fist,
                                          facing, phase, dark=False)
    def _draw_stone_arm(surface, shoulder, elbow, fist, facing, phase,
                        dark=False, big_fist=False):
        """Armored arm with gold trim."""
        stone_dark_c = _NS_valthar.PALETTE["stone_darkest"] if dark else _NS_valthar.PALETTE["stone_dark"]
        stone_mid_c = _NS_valthar.PALETTE["stone_dark"] if dark else _NS_valthar.PALETTE["stone_mid"]
        stone_light_c = _NS_valthar.PALETTE["stone_mid"] if dark else _NS_valthar.PALETTE["stone_light"]
        # Shadow
        _NS_valthar._aaline(surface, _NS_valthar.PALETTE["shadow_deep"],
                             (shoulder[0] + 2, shoulder[1] + 3),
                             (elbow[0] + 2, elbow[1] + 3), 10)
        _NS_valthar._aaline(surface, _NS_valthar.PALETTE["shadow_deep"],
                             (elbow[0] + 2, elbow[1] + 3),
                             (fist[0] + 2, fist[1] + 3), 9)
        # Upper arm
        _NS_valthar._aaline(surface, _NS_valthar.PALETTE["stone_darkest"], shoulder, elbow, 10)
        _NS_valthar._aaline(surface, stone_dark_c, shoulder, elbow, 8)
        _NS_valthar._aaline(surface, stone_mid_c,
                             (shoulder[0], shoulder[1] - 1),
                             (elbow[0], elbow[1] - 1), 5)
        _NS_valthar._aaline(surface, stone_light_c,
                             (shoulder[0], shoulder[1] - 2),
                             (elbow[0], elbow[1] - 2), 2)
        # Gold band on upper arm
        mid_ux = (shoulder[0] + elbow[0]) // 2
        mid_uy = (shoulder[1] + elbow[1]) // 2
        pygame.draw.circle(surface, _NS_valthar.PALETTE["gold_dark"], (mid_ux, mid_uy), 5)
        pygame.draw.circle(surface, _NS_valthar.PALETTE["gold_mid"], (mid_ux, mid_uy), 4)
        pygame.draw.circle(surface, _NS_valthar.PALETTE["gold_light"], (mid_ux, mid_uy), 2)
        # Elbow joint (chunky)
        pygame.draw.rect(surface, _NS_valthar.PALETTE["stone_darkest"],
                         (elbow[0] - 4, elbow[1] - 4, 9, 9))
        pygame.draw.rect(surface, stone_dark_c, (elbow[0] - 4, elbow[1] - 4, 8, 8))
        pygame.draw.rect(surface, stone_mid_c, (elbow[0] - 3, elbow[1] - 3, 6, 6))
        pygame.draw.rect(surface, stone_light_c, (elbow[0] - 2, elbow[1] - 3, 3, 3))
        # Gold accent on elbow
        pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_mid"], (elbow[0] - 1, elbow[1], 2, 1))
        # Forearm
        _NS_valthar._aaline(surface, _NS_valthar.PALETTE["stone_darkest"], elbow, fist, 9)
        _NS_valthar._aaline(surface, stone_dark_c, elbow, fist, 7)
        _NS_valthar._aaline(surface, stone_mid_c,
                             (elbow[0], elbow[1] - 1), (fist[0], fist[1] - 1), 4)
        _NS_valthar._aaline(surface, stone_light_c,
                             (elbow[0], elbow[1] - 2), (fist[0], fist[1] - 2), 1)
        # Gold band on forearm (wrist)
        mid_fx = int(elbow[0] * 0.3 + fist[0] * 0.7)
        mid_fy = int(elbow[1] * 0.3 + fist[1] * 0.7)
        pygame.draw.circle(surface, _NS_valthar.PALETTE["gold_dark"], (mid_fx, mid_fy), 4)
        pygame.draw.circle(surface, _NS_valthar.PALETTE["gold_mid"], (mid_fx, mid_fy), 3)
        # STONE FIST
        _NS_valthar._draw_stone_fist(surface, fist, facing, phase, dark=dark, big=big_fist)
    def _draw_stone_fist(surface, fist, facing, phase, dark=False, big=False):
        """Massive gauntlet fist with gold trim."""
        size = 8 if big else 6
        fx, fy = fist
        stone_dark_c = _NS_valthar.PALETTE["stone_darkest"] if dark else _NS_valthar.PALETTE["stone_dark"]
        stone_mid_c = _NS_valthar.PALETTE["stone_dark"] if dark else _NS_valthar.PALETTE["stone_mid"]
        stone_light_c = _NS_valthar.PALETTE["stone_mid"] if dark else _NS_valthar.PALETTE["stone_light"]
        # Fist shape
        fist_pts = [
            (fx - size, fy - size + 1), (fx - size + 2, fy - size - 1),
            (fx + size - 2, fy - size - 1), (fx + size, fy - size + 2),
            (fx + size, fy + size - 1), (fx + size - 2, fy + size + 1),
            (fx - size + 2, fy + size + 1), (fx - size, fy + size - 1),
        ]
        _NS_valthar._poly(surface, _NS_valthar.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in fist_pts])
        _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_darkest"], fist_pts)
        _NS_valthar._poly(surface, stone_dark_c, [
            (fx - size + 1, fy - size + 1), (fx - size + 2, fy - size),
            (fx + size - 2, fy - size), (fx + size - 1, fy - size + 1),
            (fx + size - 1, fy + size - 1), (fx + size - 2, fy + size),
            (fx - size + 2, fy + size), (fx - size + 1, fy + size - 1),
        ])
        _NS_valthar._poly(surface, stone_mid_c, [
            (fx - size + 2, fy - 2), (fx - size + 3, fy - size + 3),
            (fx + size - 3, fy - size + 3), (fx + size - 2, fy - 2),
            (fx + size - 3, fy + size - 3), (fx - size + 3, fy + size - 3),
        ])
        pygame.draw.rect(surface, stone_light_c, (fx - 2, fy - 3, 4, 3))
        # Gold knuckle band
        pygame.draw.line(surface, _NS_valthar.PALETTE["gold_dark"],
                         (fx - size + 1, fy - 2), (fx + size - 1, fy - 2), 2)
        pygame.draw.line(surface, _NS_valthar.PALETTE["gold_mid"],
                         (fx - size + 1, fy - 2), (fx + size - 1, fy - 2), 1)
        pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_shine"], (fx, fy - 2, 1, 1))
        # Knuckle plates (small squares)
        for i, kx in enumerate((-4, 0, 4)):
            plate_x = fx + kx
            pygame.draw.rect(surface, _NS_valthar.PALETTE["stone_darkest"],
                             (plate_x - 1, fy - size - 1, 3, 3))
            pygame.draw.rect(surface, _NS_valthar.PALETTE["stone_mid"],
                             (plate_x - 1, fy - size - 1, 2, 2))
            pygame.draw.rect(surface, _NS_valthar.PALETTE["stone_light"],
                             (plate_x - 1, fy - size - 1, 1, 1))
            pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_mid"], (plate_x, fy - size, 1, 1))
    def _draw_shoulder_pauldrons(surface, cx, cy, facing, phase):
        """Large shoulder plates with gold trim."""
        for side in (-1, 1):
            base_x = cx + side * 18
            base_y = cy - 2
            # Pauldron shape (dome)
            pauld_pts = [
                (base_x - 6, base_y - 2),
                (base_x - 5, base_y - 8),
                (base_x - 1, base_y - 11),
                (base_x + 3, base_y - 10),
                (base_x + 6, base_y - 6),
                (base_x + 7, base_y),
                (base_x + 5, base_y + 4),
                (base_x - 5, base_y + 4),
            ]
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["shadow_deep"],
                               [(px + 2, py + 2) for px, py in pauld_pts])
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_darkest"], pauld_pts)
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_dark"], [
                (base_x - 5, base_y - 2), (base_x - 4, base_y - 7),
                (base_x - 1, base_y - 10), (base_x + 3, base_y - 9),
                (base_x + 5, base_y - 5), (base_x + 6, base_y),
                (base_x + 4, base_y + 3), (base_x - 4, base_y + 3),
            ])
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_mid"], [
                (base_x - 3, base_y - 2), (base_x - 3, base_y - 6),
                (base_x, base_y - 8), (base_x + 3, base_y - 6),
                (base_x + 4, base_y - 2), (base_x + 3, base_y + 2),
                (base_x - 3, base_y + 2),
            ])
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_light"], [
                (base_x - 1, base_y - 5), (base_x + 2, base_y - 5),
                (base_x + 3, base_y - 2), (base_x, base_y - 1),
            ])
            # Gold trim rim
            pygame.draw.line(surface, _NS_valthar.PALETTE["gold_dark"],
                             (base_x - 6, base_y + 3), (base_x + 6, base_y + 3), 2)
            pygame.draw.line(surface, _NS_valthar.PALETTE["gold_mid"],
                             (base_x - 6, base_y + 3), (base_x + 6, base_y + 3), 1)
            # Gold ornament on top of pauldron (small spike/emblem)
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["gold_darkest"], [
                (base_x - 1 + 1, base_y - 10 + 1),
                (base_x + 1, base_y - 14 + 1),
                (base_x + 1 + 1, base_y - 10 + 1),
            ])
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["gold_dark"], [
                (base_x - 1, base_y - 10), (base_x, base_y - 14), (base_x + 1, base_y - 10),
            ])
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["gold_mid"], [
                (base_x, base_y - 10), (base_x, base_y - 14),
                (base_x + 1, base_y - 12),
            ])
            pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_shine"], (base_x, base_y - 14, 1, 1))
    def _draw_colossus_head(surface, cx, cy, facing, phase):
        """Stone helmed head with glowing blue eyes."""
        head_shape = [
            (cx - 8, cy + 6), (cx - 10, cy + 2), (cx - 10, cy - 4),
            (cx - 7, cy - 8), (cx - 2, cy - 10), (cx + 4, cy - 10),
            (cx + 9, cy - 7), (cx + 11, cy - 2), (cx + 10, cy + 4),
            (cx + 7, cy + 7), (cx + 1, cy + 8), (cx - 5, cy + 7),
        ]
        _NS_valthar._poly(surface, _NS_valthar.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in head_shape])
        _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_darkest"], head_shape)
        _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_dark"], [
            (cx - 8, cy + 5), (cx - 9, cy + 1), (cx - 9, cy - 3),
            (cx - 6, cy - 7), (cx - 2, cy - 9), (cx + 4, cy - 9),
            (cx + 8, cy - 6), (cx + 10, cy - 2), (cx + 9, cy + 3),
            (cx + 6, cy + 6), (cx + 1, cy + 7), (cx - 5, cy + 6),
        ])
        _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_mid"], [
            (cx - 6, cy + 3), (cx - 7, cy - 2), (cx - 4, cy - 6),
            (cx + 3, cy - 6), (cx + 7, cy - 2), (cx + 7, cy + 3),
            (cx + 4, cy + 5), (cx - 3, cy + 5),
        ])
        _NS_valthar._poly(surface, _NS_valthar.PALETTE["stone_light"], [
            (cx + facing * 2, cy - 5), (cx + facing * 5, cy - 3),
            (cx + facing * 4, cy), (cx + facing, cy - 2),
        ])
        # HELM VISOR (dark horizontal slit for eyes)
        pygame.draw.rect(surface, _NS_valthar.PALETTE["shadow_deep"],
                         (cx - 6, cy - 4, 13, 4))
        pygame.draw.rect(surface, _NS_valthar.PALETTE["crevice_darkest"],
                         (cx - 5, cy - 3, 11, 3))
        # Glowing eyes inside visor
        _NS_valthar._draw_glow_eye(surface, cx - 3, cy - 2, phase)
        _NS_valthar._draw_glow_eye(surface, cx + 3, cy - 2, phase)
        # Nose guard (vertical line)
        pygame.draw.line(surface, _NS_valthar.PALETTE["stone_darkest"],
                         (cx, cy), (cx, cy + 5), 2)
        pygame.draw.line(surface, _NS_valthar.PALETTE["gold_dark"],
                         (cx, cy + 1), (cx, cy + 4), 1)
        pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_mid"], (cx, cy + 2, 1, 1))
        # Helm side vents
        for side in (-1, 1):
            for i in range(3):
                pygame.draw.rect(surface, _NS_valthar.PALETTE["crevice_darkest"],
                                 (cx + side * 7, cy + i * 2, 1, 1))
        # Gold cheek trim
        pygame.draw.line(surface, _NS_valthar.PALETTE["gold_dark"],
                         (cx - 8, cy + 1), (cx - 5, cy + 5), 1)
        pygame.draw.line(surface, _NS_valthar.PALETTE["gold_dark"],
                         (cx + 8, cy + 1), (cx + 5, cy + 5), 1)
    def _draw_glow_eye(surface, ex, ey, phase):
        """Glowing blue-white petricite eye."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Halo
        for r in range(4, 0, -1):
            alpha = _NS_valthar._alpha(120 * (4 - r) / 4 * pulse)
            _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["eye_mid"], alpha), (ex, ey), r)
        # Core
        pygame.draw.rect(surface, _NS_valthar.PALETTE["eye_dark"], (ex - 1, ey - 1, 3, 2))
        pygame.draw.rect(surface, _NS_valthar.PALETTE["eye_mid"], (ex, ey - 1, 2, 2))
        pygame.draw.rect(surface, _NS_valthar.PALETTE["eye_light"], (ex, ey, 1, 1))
        pygame.draw.rect(surface, _NS_valthar.PALETTE["eye_glow"], (ex, ey, 1, 1))
    def _draw_crown(surface, cx, cy, facing, phase):
        """Golden crown of spikes on top of helm."""
        # Central big spike + 2 side spikes
        for i, (dx, height) in enumerate([
            (-6, 4), (-3, 6), (0, 9), (3, 6), (6, 4),
        ]):
            spike_x = cx + dx
            spike_tip_y = cy - height
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["shadow_deep"], [
                (spike_x - 1 + 1, cy + 1 + 1),
                (spike_x + 1, spike_tip_y + 1),
                (spike_x + 1 + 1, cy + 1 + 1),
            ])
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["gold_darkest"], [
                (spike_x - 1, cy + 1), (spike_x, spike_tip_y), (spike_x + 1, cy + 1),
            ])
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["gold_dark"], [
                (spike_x - 1, cy + 1), (spike_x, spike_tip_y),
                (int((spike_x + spike_x + 1) / 2), int((spike_tip_y + cy + 1) / 2)),
            ])
            _NS_valthar._poly(surface, _NS_valthar.PALETTE["gold_mid"], [
                (spike_x, cy), (spike_x, spike_tip_y),
                (int((spike_x * 3 + spike_x + 1) / 4),
                 int((spike_tip_y * 3 + cy + 1) / 4)),
            ])
            pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_light"],
                             (spike_x, spike_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_shine"],
                             (spike_x, spike_tip_y, 1, 1))
        # Base band (crown ring)
        pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_dark"],
                         (cx - 8, cy + 1, 17, 2))
        pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_mid"],
                         (cx - 7, cy + 2, 15, 1))
        pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_shine"],
                         (cx - 1, cy + 2, 3, 1))
    # ============================================================
    # FIST SLASH (basic attack arc)
    # ============================================================
    def _draw_fist_slash(surface, cx, cy, facing, progress):
        """Gold slash arc during fist swing."""
        if progress < 0.35 or progress > 0.75:
            return
        t = (progress - 0.35) / 0.4
        intensity = math.sin(t * math.pi)
        alpha = _NS_valthar._alpha(255 * intensity)
        arc_cx = cx + facing * 22
        arc_cy = cy + 6
        arc_r = 24
        # Slash arc lines
        start_angle = math.radians(-80) if facing > 0 else math.radians(180 + 80)
        end_angle = math.radians(80) if facing > 0 else math.radians(180 - 80)
        sweep = start_angle + (end_angle - start_angle) * t
        trail_start = start_angle + (end_angle - start_angle) * max(0, t - 0.4)
        prev_pt = None
        num_segments = 12
        for i in range(num_segments + 1):
            seg_t = i / num_segments
            angle = trail_start + (sweep - trail_start) * seg_t
            px = arc_cx + int(math.cos(angle) * arc_r)
            py = arc_cy + int(math.sin(angle) * arc_r)
            if prev_pt is not None:
                for thickness, color in [
                    (6, (*_NS_valthar.PALETTE["gold_darkest"], alpha // 3)),
                    (4, (*_NS_valthar.PALETTE["gold_dark"], alpha // 2)),
                    (3, (*_NS_valthar.PALETTE["gold_mid"], alpha)),
                    (2, (*_NS_valthar.PALETTE["gold_light"], alpha)),
                    (1, (*_NS_valthar.PALETTE["gold_shine"], alpha)),
                ]:
                    pygame.draw.line(surface, color, prev_pt, (px, py), thickness)
            prev_pt = (px, py)
        # Sparks along arc
        for i in range(7):
            angle = math.radians(-80) + math.radians(160) * (i / 7)
            if facing < 0:
                angle = math.radians(180) - angle
            spark_r = arc_r + int(math.sin(i + progress * 10) * 4)
            sx = arc_cx + int(math.cos(angle) * spark_r)
            sy = arc_cy + int(math.sin(angle) * spark_r)
            pygame.draw.rect(surface, (*_NS_valthar.PALETTE["gold_hot"], alpha), (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_valthar.PALETTE["gold_shine"], alpha), (sx, sy, 1, 1))
    # ============================================================
    # GOLD PARTICLES (ambient)
    # ============================================================
    def _draw_gold_particles(surface, cx, cy, phase, intense=False):
        """Gold sparkles floating around body."""
        strength = 1.4 if intense else 1.0
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            radius = 40 + int(math.sin(phase + i) * 10)
            rx = cx + int(math.cos(angle) * radius)
            ry = cy + int(math.sin(angle) * radius * 0.5)
            alpha = _NS_valthar._alpha(220 * strength)
            pygame.draw.rect(surface, (*_NS_valthar.PALETTE["gold_mid"], alpha), (rx, ry, 2, 2))
            pygame.draw.rect(surface, (*_NS_valthar.PALETTE["gold_shine"], alpha), (rx, ry, 1, 1))
        # Rising gold embers
        for i in range(6):
            t = (phase * 0.5 + i * 0.17) % 1.0
            ex = cx - 20 + i * 8 + int(math.sin(phase + i) * 3)
            ey = cy + 20 - int(t * 30)
            alpha = _NS_valthar._alpha(230 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_valthar.PALETTE["gold_light"], alpha), (ex, ey, 2, 2))
                pygame.draw.rect(surface, (*_NS_valthar.PALETTE["gold_hot"], alpha), (ex, ey, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((150, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = max(0, (14 - radius) * 15)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 15 - radius, 130 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (5, 5, 8, 170), (5, 9, 140, 12))
        surface.blit(shadow, (x - 75, y - 15))
    def _draw_gold_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 190), pygame.SRCALPHA)
        for radius in range(95, 5, -5):
            alpha = _NS_valthar._alpha((95 - radius) * 1.1 * pulse)
            if alpha > 0:
                _NS_valthar._aacircle(aura, (*_NS_valthar.PALETTE["mist_dark"], alpha),
                                       (110, 95), radius)
        for radius in range(60, 5, -4):
            alpha = _NS_valthar._alpha((60 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_valthar._aacircle(aura, (*_NS_valthar.PALETTE["gold_darkest"], alpha),
                                       (110, 95), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_valthar._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_valthar._aacircle(aura, (*_NS_valthar.PALETTE["gold_dark"], alpha),
                                       (110, 95), radius)
        surface.blit(aura, (x - 110, y - 95))
        # Floating outer sparks
        for i in range(14):
            angle = phase * 0.3 + i * math.pi / 7
            radius = 50 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_hot"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 54), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_valthar.PALETTE["mist_dark"], 200),
                            (5, 18, 170, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_valthar.PALETTE["gold_darkest"], 220),
                            (14, 20, 152, 22), 2)
        pygame.draw.ellipse(ring, (*_NS_valthar.PALETTE["gold_dark"], 230),
                            (25, 22, 130, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_valthar.PALETTE["gold_mid"], 180),
                            (40, 24, 100, 14), 1)
        # Runes
        for i in range(11):
            angle = phase * 0.3 + i * math.pi / 5.5
            x1 = 90 + int(math.cos(angle) * 48)
            y1 = 31 + int(math.sin(angle) * 8)
            x2 = 90 + int(math.cos(angle) * 76)
            y2 = 31 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_valthar.PALETTE["gold_light"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_valthar.PALETTE["gold_hot"],
                                        _NS_valthar._alpha(150 * pulse)),
                                (14, 12, 152, 38), 1)
        surface.blit(ring, (x - 90, y - 27))
    # ============================================================
    # SKILL Q - WINDS OF WAR (two gust projectiles)
    # ============================================================
    def _draw_winds_skill(surface, boss, x, y, timer, phase):
        """Two curved gold wind gusts flying toward target."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_valthar._target_position(boss, x, y)
        if progress < 0.2:
            # Charge in fist
            t = progress / 0.2
            hand_x = x + facing * 26
            hand_y = y + 4
            cr = int(3 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_valthar._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_dark"], alpha),
                                       (hand_x, hand_y), r)
            _NS_valthar._aacircle(surface, _NS_valthar.PALETTE["gold_mid"],
                                   (hand_x, hand_y), cr - 2)
            _NS_valthar._aacircle(surface, _NS_valthar.PALETTE["gold_light"],
                                   (hand_x, hand_y), max(1, cr - 4))
            _NS_valthar._aacircle(surface, _NS_valthar.PALETTE["gold_shine"],
                                   (hand_x, hand_y), max(1, cr - 6))
        else:
            t = (progress - 0.2) / 0.8
            start_x = x + facing * 28
            start_y = y + 4
            # TWO gust projectiles (offset vertically)
            for gust_i, y_offset in enumerate((-8, 8)):
                # Each gust delayed slightly
                gust_t = max(0, t - gust_i * 0.1)
                if gust_t <= 0:
                    continue
                sy_start = start_y + y_offset
                ty_end = ty + y_offset // 2
                bx = int(start_x + (tx - start_x) * gust_t)
                by = int(sy_start + (ty_end - sy_start) * gust_t)
                # Gust as flowing crescent (curved trail)
                # Draw multiple segments creating swirl shape
                for seg_i in range(8):
                    seg_offset = seg_i * 3
                    prev_t = max(0, gust_t - seg_i * 0.03)
                    if prev_t <= 0:
                        continue
                    px = int(start_x + (tx - start_x) * prev_t)
                    py = int(sy_start + (ty_end - sy_start) * prev_t)
                    # Add swirl offset (perpendicular oscillation)
                    swirl = math.sin(prev_t * 8 + gust_i) * 4
                    perp_offset = int(swirl)
                    py_offset = py + perp_offset
                    alpha = _NS_valthar._alpha(230 - seg_i * 22)
                    size = max(1, 6 - seg_i)
                    _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_darkest"], alpha),
                                           (px, py_offset), size + 1)
                    _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_dark"], alpha),
                                           (px, py_offset), size)
                    _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_mid"], alpha),
                                           (px, py_offset), max(1, size - 1))
                    _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_light"], alpha),
                                           (px, py_offset), max(1, size - 2))
                # Bright gust head
                for r in range(8, 2, -1):
                    alpha = _NS_valthar._alpha(120 * (8 - r) / 8)
                    _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_hot"], alpha),
                                           (bx, by), r)
                _NS_valthar._aacircle(surface, _NS_valthar.PALETTE["gold_mid"], (bx, by), 4)
                _NS_valthar._aacircle(surface, _NS_valthar.PALETTE["gold_light"], (bx, by), 2)
                _NS_valthar._aacircle(surface, _NS_valthar.PALETTE["gold_shine"], (bx, by), 1)
                pygame.draw.rect(surface, _NS_valthar.PALETTE["white"], (bx, by, 1, 1))
                # Curved swoosh tail (like commas/crescents)
                for tail_i in range(4):
                    tail_ang = math.pi / 2 + tail_i * math.pi / 6 * facing
                    tail_x = bx - int(math.cos(tail_ang) * (4 + tail_i * 2)) * facing
                    tail_y = by + int(math.sin(tail_ang) * (2 + tail_i))
                    alpha = _NS_valthar._alpha(200 - tail_i * 40)
                    pygame.draw.rect(surface, (*_NS_valthar.PALETTE["gold_hot"], alpha),
                                     (tail_x, tail_y, 2, 2))
                    pygame.draw.rect(surface, (*_NS_valthar.PALETTE["gold_shine"], alpha),
                                     (tail_x, tail_y, 1, 1))
                # Impact
                if gust_t > 0.9:
                    st = (gust_t - 0.9) / 0.1
                    radius = int(10 + st * 20)
                    alpha = _NS_valthar._alpha(220 * (1 - st))
                    _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_dark"], alpha),
                                           (tx, ty_end), radius, 2)
                    _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_mid"], alpha),
                                           (tx, ty_end), max(1, radius - 4), 1)
                    for k in range(8):
                        ang_s = k * math.pi / 4
                        ex_s = tx + int(math.cos(ang_s) * radius)
                        ey_s = ty_end + int(math.sin(ang_s) * radius * 0.7)
                        pygame.draw.rect(surface, (*_NS_valthar.PALETTE["gold_hot"], alpha),
                                         (ex_s, ey_s, 2, 2))
    # ============================================================
    # SKILL W - DURAND'S SHIELD (shield bubble in front)
    # ============================================================
    def _draw_shield_bubble(surface, boss, x, y, timer, phase):
        """Gold shield bubble in front of boss."""
        facing = boss.direction
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Shield forms in front
        shield_cx = x + facing * 25
        shield_cy = y
        shield_r = 30 + int(math.sin(phase * 2) * 2)
        # Shield semi-circle facing forward
        shield_surf = pygame.Surface((shield_r * 2 + 20, shield_r * 2 + 20),
                                      pygame.SRCALPHA)
        center = (shield_r + 10, shield_r + 10)
        # Multiple ring layers
        for i, (thickness, alpha_val) in enumerate([
            (4, 140), (3, 180), (2, 220), (1, 255),
        ]):
            _NS_valthar._aacircle(shield_surf, (*_NS_valthar.PALETTE["gold_darkest"], alpha_val),
                                   center, shield_r - i, thickness)
            _NS_valthar._aacircle(shield_surf, (*_NS_valthar.PALETTE["gold_mid"], alpha_val),
                                   center, shield_r - i - 1, max(1, thickness - 1))
            _NS_valthar._aacircle(shield_surf, (*_NS_valthar.PALETTE["gold_light"], alpha_val),
                                   center, shield_r - i - 2, 1)
        # Rotating gold sparkles on ring
        for i in range(16):
            angle = phase * 1.5 + i * math.pi / 8
            sx = center[0] + int(math.cos(angle) * shield_r)
            sy = center[1] + int(math.sin(angle) * shield_r)
            pygame.draw.rect(shield_surf, _NS_valthar.PALETTE["gold_hot"], (sx, sy, 2, 2))
            pygame.draw.rect(shield_surf, _NS_valthar.PALETTE["gold_shine"], (sx, sy, 1, 1))
        # Inner shield fill (translucent gold)
        inner_alpha = _NS_valthar._alpha(80 + math.sin(phase * 2) * 20)
        _NS_valthar._aacircle(shield_surf, (*_NS_valthar.PALETTE["gold_mid"], inner_alpha),
                               center, shield_r - 4)
        # Hex pattern inside (subtle)
        for hi in range(3):
            for hj in range(3):
                hx = center[0] - 12 + hi * 12
                hy = center[1] - 12 + hj * 12
                pygame.draw.line(shield_surf, (*_NS_valthar.PALETTE["gold_light"], 100),
                                 (hx, hy - 2), (hx + 2, hy - 1), 1)
                pygame.draw.line(shield_surf, (*_NS_valthar.PALETTE["gold_light"], 100),
                                 (hx + 2, hy - 1), (hx + 2, hy + 1), 1)
        # Central shield emblem (V-shape)
        emb_pts = [
            (center[0] - 6, center[1] - 4), (center[0] + 6, center[1] - 4),
            (center[0] + 4, center[1] + 2), (center[0], center[1] + 8),
            (center[0] - 4, center[1] + 2),
        ]
        _NS_valthar._poly(shield_surf, (*_NS_valthar.PALETTE["gold_dark"], 220), emb_pts)
        _NS_valthar._poly(shield_surf, (*_NS_valthar.PALETTE["gold_hot"], 240), [
            (center[0] - 4, center[1] - 3), (center[0] + 4, center[1] - 3),
            (center[0] + 2, center[1]), (center[0], center[1] + 5),
            (center[0] - 2, center[1]),
        ])
        surface.blit(shield_surf, (shield_cx - shield_r - 10, shield_cy - shield_r - 10))
        # Extra energy tendrils outward
        for i in range(6):
            angle = phase * 0.8 + i * math.pi / 3
            end_x = shield_cx + int(math.cos(angle) * (shield_r + 6))
            end_y = shield_cy + int(math.sin(angle) * (shield_r + 6))
            alpha = _NS_valthar._alpha(150 + math.sin(phase * 3 + i) * 40)
            pygame.draw.line(surface, (*_NS_valthar.PALETTE["gold_hot"], alpha),
                             (shield_cx + int(math.cos(angle) * shield_r),
                              shield_cy + int(math.sin(angle) * shield_r)),
                             (end_x, end_y), 1)
            pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_shine"],
                             (end_x, end_y, 1, 1))
    # ============================================================
    # SKILL E - JUSTICE PUNCH (dash + fist impact)
    # ============================================================
    def _draw_punch_ground(surface, boss, x, y, timer, phase):
        """Line trail on ground during dash."""
        tx, ty = _NS_valthar._target_position(boss, x, y)
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.35:
            alpha = _NS_valthar._alpha(200 * (progress / 0.35))
            for w, c in [(6, _NS_valthar.PALETTE["gold_darkest"]),
                         (3, _NS_valthar.PALETTE["gold_mid"]),
                         (1, _NS_valthar.PALETTE["gold_light"])]:
                pygame.draw.line(surface, (*c, alpha), (x, y + 50), (tx, ty), w)
    def _draw_punch_foreground(surface, boss, x, y, timer, phase):
        """Boss dashes with fist forward then impacts target."""
        tx, ty = _NS_valthar._target_position(boss, x, y)
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        if progress < 0.35:
            # Wind-up: fist charging with gold energy
            pass
        elif progress < 0.75:
            # DASH: motion trail from boss to target
            t = (progress - 0.35) / 0.4
            for i in range(8):
                trail_t = max(0, t - i * 0.06)
                px = int(x + (tx - x) * trail_t)
                py = int(y + (ty - y) * trail_t)
                alpha = _NS_valthar._alpha(230 - i * 25)
                size = max(2, 9 - i)
                _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_darkest"], alpha),
                                       (px, py), size)
                _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_mid"], alpha),
                                       (px, py), max(1, size - 2))
                _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_light"], alpha),
                                       (px, py), max(1, size - 4))
            # IMPACT burst at target
            if t > 0.75:
                bt = (t - 0.75) / 0.25
                intensity = math.sin(bt * math.pi)
                r = int(15 + bt * 25)
                alpha = _NS_valthar._alpha(250 * intensity)
                # Big impact rings
                _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_darkest"], alpha),
                                       (tx, ty), r + 3, 3)
                _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_dark"], alpha),
                                       (tx, ty), r, 3)
                _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_mid"], alpha),
                                       (tx, ty), max(1, r - 6), 2)
                _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_hot"], alpha),
                                       (tx, ty), max(1, r - 12), 1)
                # Radial rays
                for i in range(12):
                    angle_s = i * math.pi / 6
                    ex = tx + int(math.cos(angle_s) * r)
                    ey = ty + int(math.sin(angle_s) * r * 0.9)
                    pygame.draw.line(surface, (*_NS_valthar.PALETTE["gold_light"], alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface, (*_NS_valthar.PALETTE["gold_shine"], alpha),
                                     (ex, ey, 2, 2))
                # KNOCKUP indicator (upward arrows)
                for a_i in range(2):
                    ax = tx - 8 + a_i * 16
                    ay = ty - 15 - int(math.sin(phase * 3 + a_i) * 3)
                    pygame.draw.polygon(surface, (*_NS_valthar.PALETTE["gold_hot"], alpha),
                                        [(ax, ay), (ax - 3, ay + 5), (ax + 3, ay + 5)])
        else:
            # Aftermath: knockup lingering
            t = (progress - 0.75) / 0.25
            for a_i in range(3):
                ax = tx - 12 + a_i * 12
                ay = ty - 18 + int(t * 6)
                alpha = _NS_valthar._alpha(200 * (1 - t))
                pygame.draw.polygon(surface, (*_NS_valthar.PALETTE["gold_hot"], alpha),
                                    [(ax, ay), (ax - 3, ay + 4), (ax + 3, ay + 4)])
    # ============================================================
    # SKILL R - HERO'S ENTRANCE (leap up + landing shockwave)
    # ============================================================
    def _draw_entrance_ground(surface, boss, x, y, timer, phase):
        """Landing zone indicator at target."""
        tx, ty = _NS_valthar._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            # Warning: growing circle
            t = progress / 0.4
            r = int(50 * t)
            alpha = _NS_valthar._alpha(200 * t)
            pygame.draw.ellipse(surface, (*_NS_valthar.PALETTE["gold_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_valthar.PALETTE["gold_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_valthar.PALETTE["gold_mid"], alpha),
                                (tx - r + 6, ty - r // 3 + 4,
                                 r * 2 - 12, r * 2 // 3 - 8), 1)
            # Warning rune circle
            for i in range(8):
                ang = i * math.pi / 4 + phase * 0.5
                sx = tx + int(math.cos(ang) * r)
                sy = ty + int(math.sin(ang) * r * 0.4)
                pygame.draw.rect(surface, _NS_valthar.PALETTE["gold_hot"], (sx, sy, 2, 2))
        elif progress < 0.7:
            # Impact ring expanding
            t = (progress - 0.4) / 0.3
            r = int(50 + t * 30)
            alpha = _NS_valthar._alpha(230 * (1 - t * 0.4))
            pygame.draw.ellipse(surface, (*_NS_valthar.PALETTE["gold_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_valthar.PALETTE["gold_dark"], alpha),
                                (tx - r + 4, ty - r // 3 + 2,
                                 r * 2 - 8, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_valthar.PALETTE["gold_mid"], alpha),
                                (tx - r + 10, ty - r // 3 + 5,
                                 r * 2 - 20, r * 2 // 3 - 10))
        else:
            # Aftermath: fading crater
            t = (progress - 0.7) / 0.3
            r = int(75 * (1 - t * 0.3))
            alpha = _NS_valthar._alpha(180 * (1 - t))
            pygame.draw.ellipse(surface, (*_NS_valthar.PALETTE["gold_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)
    def _draw_entrance_foreground(surface, boss, x, y, timer, phase):
        """Boss leaps high then crashes down at target with wings spread."""
        tx, ty = _NS_valthar._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            # PHASE 1: Boss ascends (small silhouette rising to sky)
            t = progress / 0.4
            # Boss silhouette rising above
            rise_y = y - int(t * 80)
            silhouette = pygame.Surface((60, 60), pygame.SRCALPHA)
            for r in range(15, 3, -2):
                alpha = _NS_valthar._alpha(100 * (15 - r) / 15 * t)
                _NS_valthar._aacircle(silhouette, (*_NS_valthar.PALETTE["gold_mid"], alpha),
                                       (30, 30), r)
            _NS_valthar._aacircle(silhouette, _NS_valthar.PALETTE["gold_light"], (30, 30), 5)
            _NS_valthar._aacircle(silhouette, _NS_valthar.PALETTE["gold_hot"], (30, 30), 3)
            _NS_valthar._aacircle(silhouette, _NS_valthar.PALETTE["gold_shine"], (30, 30), 1)
            surface.blit(silhouette, (x - 30, rise_y - 30))
        elif progress < 0.7:
            # PHASE 2: Falling down + impact
            t = (progress - 0.4) / 0.3
            if t < 0.6:
                # Falling: bright light streaking down
                fall_t = t / 0.6
                fall_y = int(y - 80 + fall_t * (ty - y + 80))
                # Bright meteor-like boss falling
                for r in range(18, 3, -2):
                    alpha = _NS_valthar._alpha(180 * (18 - r) / 18)
                    _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_light"], alpha),
                                           (tx, fall_y), r)
                _NS_valthar._aacircle(surface, _NS_valthar.PALETTE["gold_mid"], (tx, fall_y), 8)
                _NS_valthar._aacircle(surface, _NS_valthar.PALETTE["gold_hot"], (tx, fall_y), 5)
                _NS_valthar._aacircle(surface, _NS_valthar.PALETTE["gold_shine"], (tx, fall_y), 2)
                pygame.draw.rect(surface, _NS_valthar.PALETTE["white"], (tx, fall_y, 1, 1))
                # Fall trail (streak up from meteor)
                for i in range(10):
                    trail_y = fall_y - i * 6
                    if trail_y < 0:
                        continue
                    alpha = _NS_valthar._alpha(200 - i * 20)
                    size = max(1, 5 - i // 2)
                    _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_hot"], alpha),
                                           (tx, trail_y), size)
                    _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_shine"], alpha),
                                           (tx, trail_y), max(1, size - 2))
            else:
                # IMPACT: massive shockwave burst
                impact_t = (t - 0.6) / 0.4
                intensity = math.sin(impact_t * math.pi)
                r = int(20 + impact_t * 50)
                alpha = _NS_valthar._alpha(250 * intensity)
                # Multi-layer shockwave
                _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_darkest"], alpha),
                                       (tx, ty), r + 5, 4)
                _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_dark"], alpha),
                                       (tx, ty), r, 3)
                _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_mid"], alpha),
                                       (tx, ty), max(1, r - 8), 2)
                _NS_valthar._aacircle(surface, (*_NS_valthar.PALETTE["gold_hot"], alpha),
                                       (tx, ty), max(1, r - 16), 1)
                # Bright center flash
                _NS_valthar._aacircle(surface, _NS_valthar.PALETTE["gold_shine"],
                                       (tx, ty), max(1, r // 4))
                _NS_valthar._aacircle(surface, _NS_valthar.PALETTE["white"],
                                       (tx, ty), max(1, r // 8))
                # Radial rays
                for i in range(14):
                    ang = i * math.pi / 7
                    ex = tx + int(math.cos(ang) * r)
                    ey = ty + int(math.sin(ang) * r * 0.7)
                    pygame.draw.line(surface, (*_NS_valthar.PALETTE["gold_hot"], alpha),
                                     (tx, ty), (ex, ey), 3)
                    pygame.draw.rect(surface, (*_NS_valthar.PALETTE["gold_shine"], alpha),
                                     (ex, ey, 3, 3))
                # Upward gold pillars
                for pi in range(6):
                    p_ang = pi * math.pi / 3
                    px_p = tx + int(math.cos(p_ang) * r * 0.6)
                    py_p = ty + int(math.sin(p_ang) * r * 0.4)
                    pillar_h = int(30 * intensity)
                    pygame.draw.line(surface, (*_NS_valthar.PALETTE["gold_hot"], alpha),
                                     (px_p, py_p), (px_p, py_p - pillar_h), 3)
                    pygame.draw.line(surface, (*_NS_valthar.PALETTE["gold_shine"], alpha),
                                     (px_p, py_p), (px_p, py_p - pillar_h), 1)
                # KNOCKUP arrows
                for a_i in range(4):
                    ax = tx - 20 + a_i * 15
                    ay = ty - 20 - int(math.sin(phase * 3 + a_i) * 4)
                    pygame.draw.polygon(surface, (*_NS_valthar.PALETTE["gold_hot"], alpha),
                                        [(ax, ay), (ax - 4, ay + 5), (ax + 4, ay + 5)])
        else:
            # Aftermath: lingering gold dust
            t = (progress - 0.7) / 0.3
            for i in range(15):
                dust_t = (phase * 0.7 + i * 0.08) % 1.0
                dx = tx + int(math.sin(phase + i) * 30)
                dy = ty - int(dust_t * 35)
                alpha = _NS_valthar._alpha(200 * (1 - t) * (1 - dust_t))
                if alpha > 0:
                    pygame.draw.rect(surface, (*_NS_valthar.PALETTE["gold_mid"], alpha),
                                     (dx, dy, 2, 2))
                    pygame.draw.rect(surface, (*_NS_valthar.PALETTE["gold_hot"], alpha),
                                     (dx, dy, 1, 1))



# ====================================================================
# SERAPHIENNE (EMPYREAN EXECUTIONER) - TRUE BOSS
# ====================================================================

class _NS_seraphienne:
    """Namespace seraphienne - TRUE BOSS angelic warrior tema emas divine."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Gold divine (main theme)
        "gold_darkest": (35, 20, 3),
        "gold_dark": (105, 70, 15),
        "gold_mid": (200, 150, 45),
        "gold_light": (250, 215, 105),
        "gold_hot": (255, 240, 170),
        "gold_shine": (255, 252, 220),
        "gold_white": (255, 255, 240),
        # White armor
        "armor_darkest": (55, 55, 70),
        "armor_dark": (110, 110, 130),
        "armor_mid": (175, 175, 195),
        "armor_light": (230, 230, 240),
        "armor_shine": (255, 255, 255),
        # Skin (radiant fair)
        "skin_darkest": (110, 85, 90),
        "skin_dark": (180, 150, 150),
        "skin_mid": (230, 205, 200),
        "skin_light": (250, 235, 230),
        "skin_shine": (255, 250, 245),
        # Hair (blonde/gold)
        "hair_darkest": (60, 40, 10),
        "hair_dark": (140, 100, 30),
        "hair_mid": (220, 175, 75),
        "hair_light": (250, 220, 140),
        "hair_shine": (255, 245, 190),
        # Divine energy (bright yellow-white)
        "divine_dark": (155, 100, 20),
        "divine_mid": (240, 180, 55),
        "divine_light": (255, 230, 130),
        "divine_hot": (255, 250, 200),
        "divine_shine": (255, 255, 255),
        # Wing feathers (gold gradient)
        "feather_dark": (95, 65, 15),
        "feather_mid": (190, 145, 50),
        "feather_light": (245, 210, 110),
        "feather_shine": (255, 245, 175),
        # Blade (bright gold with fire)
        "blade_darkest": (65, 40, 5),
        "blade_dark": (150, 105, 25),
        "blade_mid": (230, 175, 55),
        "blade_light": (255, 225, 130),
        "blade_fire": (255, 200, 80),
        "blade_hot": (255, 245, 190),
        # Eye (bright divine gold)
        "eye_dark": (75, 45, 10),
        "eye_mid": (210, 170, 55),
        "eye_light": (250, 225, 130),
        "eye_glow": (255, 255, 220),
        # Mist / ambient
        "mist_dark": (35, 25, 15),
        "mist_mid": (100, 80, 45),
        "mist_light": (200, 175, 120),
        "shadow": (0, 0, 0),
        "shadow_deep": (3, 3, 5),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_seraphienne._clamp(color)
        if _NS_seraphienne.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_seraphienne._clamp(color)
        if _NS_seraphienne.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_seraphienne._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 260 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_seraphienne(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        _NS_seraphienne._update_srp_attack_anim(boss)
        attacking = (
            getattr(boss, "_srp_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient (BIG for TRUE BOSS)
        _NS_seraphienne._draw_divine_aura(surface, x, y, pulse)
        _NS_seraphienne._draw_ground_ring(surface, x, y + 62, pulse, active_skill)
        # Skill ground FX (behind body)
        if active_skill == "w":
            _NS_seraphienne._draw_blessing_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_seraphienne._draw_intervention_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_seraphienne._draw_starfire_ground(surface, boss, x, y, skill_timer, pulse)
        # Body — floating with slow majestic bob
        floating_bob = math.sin(pulse * 0.5) * 6
        if attacking:
            _NS_seraphienne._draw_srp_attack(surface, boss, x, y - floating_bob)
        else:
            _NS_seraphienne._draw_srp_idle(surface, boss, x, y - floating_bob)
        # Divine shield bubble if W active (over body)
        if active_skill == "w":
            _NS_seraphienne._draw_blessing_bubble(surface, boss, x, y - floating_bob,
                                                    skill_timer, pulse)
        # Foreground FX
        if active_skill == "q":
            _NS_seraphienne._draw_reckoning_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_seraphienne._draw_starfire_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_seraphienne._draw_intervention_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_srp_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 55)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_srp_previous_timer", 0))
        active = bool(getattr(boss, "_srp_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._srp_attack_active = True
            boss._srp_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._srp_attack_frame = int(getattr(boss, "_srp_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._srp_attack_active = False
            boss._srp_attack_frame = 0
            active = False
        boss._srp_previous_timer = timer
        boss._srp_attack_progress = (
            min(1.0, getattr(boss, "_srp_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_srp_idle(surface, boss, x, y):
        _NS_seraphienne._draw_shadow(surface, x, y + 66)
        _NS_seraphienne._draw_falling_feathers(surface, x, y, boss.pulse)
        _NS_seraphienne._draw_divine_particles(surface, x, y + 30, boss.pulse)
        _NS_seraphienne._draw_srp_body(surface, x, y, boss.direction, boss.pulse, "idle")
    def _draw_srp_attack(surface, boss, x, y):
        progress = getattr(boss, "_srp_attack_progress", 0.0)
        # Angel sword swing (elegant, powerful)
        if progress < 0.35:
            t = progress / 0.35
            swing_offset = -int(t * 3) * boss.direction
            lift = int(t * 4)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            swing_offset = int((-3 + t * 13)) * boss.direction
            lift = int(4 - t * 7)
        else:
            t = (progress - 0.6) / 0.4
            swing_offset = int(10 * (1 - t)) * boss.direction
            lift = int(-3 + t * 3)
        _NS_seraphienne._draw_shadow(surface, x + swing_offset, y + 66)
        _NS_seraphienne._draw_falling_feathers(surface, x + swing_offset, y, boss.pulse,
                                                 intense=True)
        _NS_seraphienne._draw_divine_particles(surface, x + swing_offset, y + 30, boss.pulse,
                                                 intense=True)
        _NS_seraphienne._draw_srp_body(surface, x + swing_offset, y - lift,
                                        boss.direction, boss.pulse, "attack", progress)
        _NS_seraphienne._draw_divine_slash(surface, x + swing_offset, y - lift,
                                             boss.direction, progress)
    # ============================================================
    # BODY (angel warrior with wings and greatsword)
    # ============================================================
    def _draw_srp_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Draw angel body: wings, torso, arms, sword, head, halo."""
        # Order: wings (behind) → dress skirt → torso → arms → shoulder pauldrons → head → hair → halo → sword
        _NS_seraphienne._draw_divine_wings(surface, cx, cy - 12, facing, phase, action,
                                             attack_progress)
        _NS_seraphienne._draw_dress_skirt(surface, cx, cy + 12, phase)
        _NS_seraphienne._draw_armor_torso(surface, cx, cy, facing, phase)
        _NS_seraphienne._draw_srp_arms(surface, cx, cy, facing, phase, action, attack_progress)
        _NS_seraphienne._draw_shoulder_pauldrons(surface, cx, cy - 8, facing, phase)
        # Head lunge slightly on attack
        head_lunge = 0
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                head_lunge = -int(t * 2) * facing
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                head_lunge = int((-2 + t * 6)) * facing
            else:
                t = (attack_progress - 0.6) / 0.4
                head_lunge = int(4 * (1 - t)) * facing
        _NS_seraphienne._draw_srp_head(surface, cx + head_lunge, cy - 26, facing, phase)
        _NS_seraphienne._draw_flowing_hair(surface, cx + head_lunge, cy - 22, facing, phase)
        _NS_seraphienne._draw_gold_helm_crown(surface, cx + head_lunge, cy - 32,
                                                facing, phase)
        _NS_seraphienne._draw_halo(surface, cx + head_lunge, cy - 34, phase)
        # SWORD (held by near hand)
        _NS_seraphienne._draw_divine_sword(surface, cx, cy, facing, phase, action, attack_progress)
    def _draw_divine_wings(surface, cx, cy, facing, phase, action, attack_progress):
        """MASSIVE golden angel wings behind body."""
        # Wing flap
        if action == "attack":
            beat = math.sin(phase * 2 + attack_progress * 4) * 5
        else:
            beat = math.sin(phase * 1.0) * 4
        # Both wings prominent (TRUE BOSS = big wings)
        for side_i, (side_mult, size_mult, alpha_mult) in enumerate([
            (-1, 1.0, 1.0),   # far wing
            (1, 0.85, 0.9),   # near wing (also big for TRUE BOSS)
        ]):
            base_x = cx - facing * 4
            base_y = cy
            # Bigger wings with more spars
            spar1_len = int(38 * size_mult)
            spar1_angle = math.pi * 0.68 * side_mult - math.radians(beat)
            spar2_len = int(44 * size_mult)
            spar2_angle = math.pi * 0.85 * side_mult - math.radians(beat * 0.85)
            spar3_len = int(40 * size_mult)
            spar3_angle = math.pi * 1.02 * side_mult - math.radians(beat * 0.7)
            spar4_len = int(32 * size_mult)
            spar4_angle = math.pi * 1.15 * side_mult - math.radians(beat * 0.5)
            tip1_x = base_x + int(math.cos(spar1_angle) * spar1_len) * (-facing)
            tip1_y = base_y - int(math.sin(spar1_angle) * spar1_len)
            tip2_x = base_x + int(math.cos(spar2_angle) * spar2_len) * (-facing)
            tip2_y = base_y - int(math.sin(spar2_angle) * spar2_len)
            tip3_x = base_x + int(math.cos(spar3_angle) * spar3_len) * (-facing)
            tip3_y = base_y - int(math.sin(spar3_angle) * spar3_len)
            tip4_x = base_x + int(math.cos(spar4_angle) * spar4_len) * (-facing)
            tip4_y = base_y - int(math.sin(spar4_angle) * spar4_len)
            # Wing membrane (feathered look)
            wing_points = [
                (base_x, base_y),
                (tip1_x, tip1_y),
                (int(tip1_x * 0.55 + tip2_x * 0.45),
                 int(tip1_y * 0.55 + tip2_y * 0.45) + int(4 * size_mult)),
                (tip2_x, tip2_y),
                (int(tip2_x * 0.55 + tip3_x * 0.45),
                 int(tip2_y * 0.55 + tip3_y * 0.45) + int(4 * size_mult)),
                (tip3_x, tip3_y),
                (int(tip3_x * 0.55 + tip4_x * 0.45),
                 int(tip3_y * 0.55 + tip4_y * 0.45) + int(4 * size_mult)),
                (tip4_x, tip4_y),
                (base_x - facing * 4, base_y + int(8 * size_mult)),
            ]
            wing_surf = pygame.Surface((220, 160), pygame.SRCALPHA)
            offset_x = base_x - 110
            offset_y = base_y - 80
            local_points = [(p[0] - offset_x, p[1] - offset_y)
                            for p in wing_points]
            # Base wing (dark gold)
            _NS_seraphienne._poly(wing_surf, (*_NS_seraphienne.PALETTE["feather_dark"],
                                                int(240 * alpha_mult)), local_points)
            # Inner mid layer
            inner_pts = []
            cx_local = sum(p[0] for p in local_points) / len(local_points)
            cy_local = sum(p[1] for p in local_points) / len(local_points)
            for p in local_points:
                inner_pts.append(
                    (int(p[0] * 0.82 + cx_local * 0.18),
                     int(p[1] * 0.82 + cy_local * 0.18))
                )
            _NS_seraphienne._poly(wing_surf, (*_NS_seraphienne.PALETTE["feather_mid"],
                                                int(230 * alpha_mult)), inner_pts)
            # Bright inner layer
            inner2_pts = []
            for p in local_points:
                inner2_pts.append(
                    (int(p[0] * 0.65 + cx_local * 0.35),
                     int(p[1] * 0.65 + cy_local * 0.35))
                )
            _NS_seraphienne._poly(wing_surf, (*_NS_seraphienne.PALETTE["feather_light"],
                                                int(180 * alpha_mult)), inner2_pts)
            # Feather details (bone lines with feather branches)
            bone_base = (base_x - offset_x, base_y - offset_y)
            for tip in [(tip1_x - offset_x, tip1_y - offset_y),
                        (tip2_x - offset_x, tip2_y - offset_y),
                        (tip3_x - offset_x, tip3_y - offset_y),
                        (tip4_x - offset_x, tip4_y - offset_y)]:
                # Main bone (thick)
                pygame.draw.line(wing_surf,
                                 (*_NS_seraphienne.PALETTE["feather_dark"],
                                  int(255 * alpha_mult)),
                                 bone_base, tip, 4)
                pygame.draw.line(wing_surf,
                                 (*_NS_seraphienne.PALETTE["gold_dark"],
                                  int(255 * alpha_mult)),
                                 bone_base, tip, 2)
                pygame.draw.line(wing_surf,
                                 (*_NS_seraphienne.PALETTE["gold_light"],
                                  int(220 * alpha_mult)),
                                 bone_base, tip, 1)
                # Feathers along bone (parallel lines perpendicular)
                bone_dx = tip[0] - bone_base[0]
                bone_dy = tip[1] - bone_base[1]
                bone_len = math.sqrt(bone_dx * bone_dx + bone_dy * bone_dy)
                if bone_len > 0:
                    perp_x = -bone_dy / bone_len
                    perp_y = bone_dx / bone_len
                    for f in range(4, int(bone_len), 4):
                        fx_start = bone_base[0] + int(bone_dx * f / bone_len)
                        fy_start = bone_base[1] + int(bone_dy * f / bone_len)
                        f_len = 5
                        fx_end = fx_start + int(perp_x * f_len)
                        fy_end = fy_start + int(perp_y * f_len)
                        pygame.draw.line(wing_surf,
                                         (*_NS_seraphienne.PALETTE["feather_mid"],
                                          int(220 * alpha_mult)),
                                         (fx_start, fy_start), (fx_end, fy_end), 1)
                        pygame.draw.line(wing_surf,
                                         (*_NS_seraphienne.PALETTE["feather_light"],
                                          int(200 * alpha_mult)),
                                         (fx_start, fy_start),
                                         (fx_start + int(perp_x * (f_len - 1)),
                                          fy_start + int(perp_y * (f_len - 1))), 1)
                        # Tip sparkles
                        pygame.draw.rect(wing_surf,
                                         (*_NS_seraphienne.PALETTE["feather_shine"],
                                          int(220 * alpha_mult)),
                                         (fx_end, fy_end, 1, 1))
                # Bright tip glow
                _NS_seraphienne._aacircle(wing_surf,
                                            (*_NS_seraphienne.PALETTE["gold_hot"],
                                             int(240 * alpha_mult)), tip, 3)
                _NS_seraphienne._aacircle(wing_surf,
                                            (*_NS_seraphienne.PALETTE["gold_shine"],
                                             int(255 * alpha_mult)), tip, 1)
                pygame.draw.rect(wing_surf, (*_NS_seraphienne.PALETTE["white"],
                                              int(255 * alpha_mult)),
                                 (tip[0], tip[1], 1, 1))
            # Bright top edge shine
            pygame.draw.line(wing_surf,
                             (*_NS_seraphienne.PALETTE["gold_shine"],
                              int(220 * alpha_mult)),
                             bone_base,
                             (tip1_x - offset_x, tip1_y - offset_y), 2)
            # Divine radiance from wing base (glow)
            for r in range(15, 3, -2):
                alpha = _NS_seraphienne._alpha(60 * (15 - r) / 15 * alpha_mult)
                _NS_seraphienne._aacircle(wing_surf,
                                            (*_NS_seraphienne.PALETTE["gold_light"], alpha),
                                            bone_base, r)
            surface.blit(wing_surf, (offset_x, offset_y))
    def _draw_dress_skirt(surface, cx, cy, phase):
        """Long flowing white dress with gold trim (angelic gown)."""
        pulse = math.sin(phase * 0.6) * 2
        # Dress shape (longer/flowing than regular skirt)
        skirt_pts = [
            (cx - 14, cy - 8),
            (cx - 18, cy),
            (cx - 22, cy + 10),
            (cx - 25, cy + 22),
            (cx - 26 + int(pulse), cy + 34),
            (cx + 26 - int(pulse), cy + 34),
            (cx + 25, cy + 22),
            (cx + 22, cy + 10),
            (cx + 18, cy),
            (cx + 14, cy - 8),
        ]
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["shadow_deep"],
                                [(px + 2, py + 3) for px, py in skirt_pts])
        # Base skirt (dark gradient)
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["armor_darkest"], skirt_pts)
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["armor_dark"], [
            (cx - 13, cy - 7), (cx - 17, cy - 1), (cx - 20, cy + 9),
            (cx - 23, cy + 21), (cx - 24 + int(pulse), cy + 33),
            (cx + 24 - int(pulse), cy + 33),
            (cx + 23, cy + 21), (cx + 20, cy + 9),
            (cx + 17, cy - 1), (cx + 13, cy - 7),
        ])
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["armor_mid"], [
            (cx - 11, cy - 6), (cx - 14, cy), (cx - 17, cy + 8),
            (cx - 20, cy + 18), (cx - 20, cy + 30),
            (cx + 20, cy + 30), (cx + 20, cy + 18),
            (cx + 17, cy + 8), (cx + 14, cy), (cx + 11, cy - 6),
        ])
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["armor_light"], [
            (cx - 8, cy - 4), (cx - 10, cy), (cx - 12, cy + 8),
            (cx - 14, cy + 16), (cx - 14, cy + 26),
            (cx + 14, cy + 26), (cx + 14, cy + 16),
            (cx + 12, cy + 8), (cx + 10, cy), (cx + 8, cy - 4),
        ])
        # Center bright highlight
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["armor_shine"], [
            (cx - 3, cy), (cx + 3, cy), (cx + 4, cy + 12),
            (cx + 2, cy + 22), (cx - 2, cy + 22), (cx - 4, cy + 12),
        ])
        # Skirt panels (vertical seam lines)
        for x_off in (-14, -8, -3, 3, 8, 14):
            pygame.draw.line(surface, _NS_seraphienne.PALETTE["gold_dark"],
                             (cx + x_off, cy),
                             (cx + int(x_off * 1.3), cy + 30), 1)
            pygame.draw.line(surface, _NS_seraphienne.PALETTE["gold_mid"],
                             (cx + x_off + 1, cy),
                             (cx + int(x_off * 1.3) + 1, cy + 30), 1)
        # BOTTOM GOLD TRIM (thick decorative band)
        bottom_pts = [
            (cx - 26 + int(pulse), cy + 32), (cx + 26 - int(pulse), cy + 32),
            (cx + 25 - int(pulse), cy + 34), (cx - 25 + int(pulse), cy + 34),
        ]
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_darkest"], bottom_pts)
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_dark"], [
            (cx - 25 + int(pulse), cy + 32), (cx + 25 - int(pulse), cy + 32),
            (cx + 24 - int(pulse), cy + 34), (cx - 24 + int(pulse), cy + 34),
        ])
        pygame.draw.line(surface, _NS_seraphienne.PALETTE["gold_mid"],
                         (cx - 24 + int(pulse), cy + 33),
                         (cx + 24 - int(pulse), cy + 33), 1)
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_shine"], (cx, cy + 33, 1, 1))
        # Front tabard (decorative panel)
        tabard_pts = [
            (cx - 5, cy - 5), (cx + 5, cy - 5),
            (cx + 7, cy + 10), (cx + 5, cy + 25), (cx, cy + 32),
            (cx - 5, cy + 25), (cx - 7, cy + 10),
        ]
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_dark"],
                                [(px + 1, py + 1) for px, py in tabard_pts])
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_darkest"], tabard_pts)
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_dark"], [
            (cx - 4, cy - 4), (cx + 4, cy - 4),
            (cx + 6, cy + 10), (cx + 4, cy + 24), (cx, cy + 30),
            (cx - 4, cy + 24), (cx - 6, cy + 10),
        ])
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_mid"], [
            (cx - 3, cy - 3), (cx + 3, cy - 3),
            (cx + 4, cy + 10), (cx + 3, cy + 22), (cx, cy + 28),
            (cx - 3, cy + 22), (cx - 4, cy + 10),
        ])
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_light"], [
            (cx - 1, cy), (cx + 1, cy),
            (cx + 2, cy + 10), (cx + 1, cy + 20), (cx, cy + 26),
            (cx - 1, cy + 20), (cx - 2, cy + 10),
        ])
        # Bright tabard center
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_shine"], (cx, cy + 10, 1, 8))
        # Sword symbol on tabard (small decoration)
        pygame.draw.line(surface, _NS_seraphienne.PALETTE["gold_hot"],
                         (cx, cy + 4), (cx, cy + 14), 1)
        pygame.draw.line(surface, _NS_seraphienne.PALETTE["gold_hot"],
                         (cx - 2, cy + 6), (cx + 2, cy + 6), 1)
    def _draw_armor_torso(surface, cx, cy, facing, phase):
        """Angel breastplate torso — gold + white with divine gem."""
        breath = math.sin(phase * 0.6) * 1
        # Slim curved torso (feminine but armored)
        torso_pts = [
            (cx - 10, cy + 10),
            (cx - 12, cy + 2),
            (cx - 12, cy - 5 - int(breath)),
            (cx - 10, cy - 12),
            (cx - 5, cy - 15),
            (cx + 5, cy - 15),
            (cx + 10, cy - 12),
            (cx + 12, cy - 5 - int(breath)),
            (cx + 12, cy + 2),
            (cx + 10, cy + 10),
        ]
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["shadow_deep"],
                                [(px + 2, py + 2) for px, py in torso_pts])
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["armor_darkest"], torso_pts)
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["armor_dark"], [
            (cx - 9, cy + 9), (cx - 11, cy + 1), (cx - 11, cy - 4),
            (cx - 9, cy - 11), (cx - 4, cy - 14), (cx + 4, cy - 14),
            (cx + 9, cy - 11), (cx + 11, cy - 4), (cx + 11, cy + 1),
            (cx + 9, cy + 9),
        ])
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["armor_mid"], [
            (cx - 7, cy + 7), (cx - 9, cy), (cx - 8, cy - 10),
            (cx - 3, cy - 13), (cx + 3, cy - 13), (cx + 8, cy - 10),
            (cx + 9, cy), (cx + 7, cy + 7),
        ])
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["armor_light"], [
            (cx - 5, cy + 5), (cx - 7, cy - 1), (cx - 4, cy - 9),
            (cx + 4, cy - 9), (cx + 7, cy - 1), (cx + 5, cy + 5),
        ])
        # Center shine
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["armor_shine"], [
            (cx - 2, cy - 6), (cx + 2, cy - 6),
            (cx + 3, cy - 2), (cx + 1, cy + 2), (cx - 1, cy + 2), (cx - 3, cy - 2),
        ])
        # Skin (upper chest V-shape neckline)
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["skin_dark"], [
            (cx - 4, cy - 12), (cx + 4, cy - 12),
            (cx + 1, cy - 8), (cx - 1, cy - 8),
        ])
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["skin_mid"], [
            (cx - 3, cy - 11), (cx + 3, cy - 11),
            (cx + 1, cy - 9), (cx - 1, cy - 9),
        ])
        # Gold plate segments (armor lines)
        pygame.draw.line(surface, _NS_seraphienne.PALETTE["gold_dark"],
                         (cx - 10, cy - 5), (cx + 10, cy - 5), 1)
        pygame.draw.line(surface, _NS_seraphienne.PALETTE["gold_mid"],
                         (cx - 10, cy - 6), (cx + 10, cy - 6), 1)
        pygame.draw.line(surface, _NS_seraphienne.PALETTE["gold_dark"],
                         (cx - 10, cy + 2), (cx + 10, cy + 2), 1)
        # Gold trim borders
        # Neckline gold trim
        pygame.draw.line(surface, _NS_seraphienne.PALETTE["gold_dark"],
                         (cx - 7, cy - 11), (cx + 7, cy - 11), 1)
        pygame.draw.line(surface, _NS_seraphienne.PALETTE["gold_mid"],
                         (cx - 7, cy - 12), (cx + 7, cy - 12), 1)
        # Waist gold trim
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_darkest"],
                         (cx - 11, cy + 8, 22, 4))
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_dark"],
                         (cx - 10, cy + 8, 20, 3))
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_mid"],
                         (cx - 9, cy + 9, 18, 1))
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_light"],
                         (cx - 2, cy + 9, 4, 1))
        # DIVINE GEM on chest (bright yellow-white)
        gem_pulse = math.sin(phase * 2) * 0.35 + 0.65
        gem_alpha = _NS_seraphienne._alpha(240 * gem_pulse)
        for r in range(6, 0, -1):
            alpha = _NS_seraphienne._alpha(120 * (6 - r) / 6 * gem_pulse)
            _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_light"], alpha),
                                        (cx, cy - 2), r)
        _NS_seraphienne._aacircle(surface, _NS_seraphienne.PALETTE["gold_dark"], (cx, cy - 2), 3)
        _NS_seraphienne._aacircle(surface, _NS_seraphienne.PALETTE["gold_mid"], (cx, cy - 2), 2)
        _NS_seraphienne._aacircle(surface, _NS_seraphienne.PALETTE["gold_hot"], (cx, cy - 2), 1)
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_shine"], (cx, cy - 2, 1, 1))
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["white"], (cx, cy - 2, 1, 1))
    def _draw_srp_arms(surface, cx, cy, facing, phase, action, attack_progress):
        """Two arms with armor."""
        idle_sway = math.sin(phase * 0.5) * 2
        # FAR ARM (behind body, holds nothing, gestures)
        far_shoulder = (cx - facing * 12, cy - 10)
        far_elbow = (cx - facing * 18, cy - 3 + int(idle_sway * 0.3))
        far_hand = (cx - facing * 22, cy + 8 + int(idle_sway * 0.4))
        _NS_seraphienne._draw_armored_arm(surface, far_shoulder, far_elbow, far_hand,
                                            facing, phase, dark=True)
        # NEAR ARM (holds sword) — swings on attack
        if action == "attack":
            # Sword swing arc
            if attack_progress < 0.35:
                # Wind-up: sword back+up
                t = attack_progress / 0.35
                angle = math.radians(-80 - t * 60) * facing
                arm_len = 22
            elif attack_progress < 0.6:
                # SLASH: sword swings forward+down
                t = (attack_progress - 0.35) / 0.25
                angle = math.radians(-140 + t * 180) * facing
                arm_len = 24
            else:
                # Recovery
                t = (attack_progress - 0.6) / 0.4
                angle = math.radians(40 - t * 60) * facing
                arm_len = 22
            shoulder = (cx + facing * 12, cy - 10)
            elbow = (shoulder[0] + int(math.cos(angle) * arm_len * 0.5),
                     shoulder[1] + int(math.sin(angle) * arm_len * 0.5))
            hand = (shoulder[0] + int(math.cos(angle) * arm_len),
                    shoulder[1] + int(math.sin(angle) * arm_len))
            _NS_seraphienne._draw_armored_arm(surface, shoulder, elbow, hand,
                                                facing, phase, dark=False)
        else:
            # Idle: sword held to side
            near_shoulder = (cx + facing * 12, cy - 10)
            near_elbow = (cx + facing * 16, cy + int(idle_sway * 0.3))
            near_hand = (cx + facing * 18, cy + 14 + int(idle_sway * 0.4))
            _NS_seraphienne._draw_armored_arm(surface, near_shoulder, near_elbow, near_hand,
                                                facing, phase, dark=False)
    def _draw_armored_arm(surface, shoulder, elbow, hand, facing, phase, dark=False):
        """Armored angel arm (white + gold)."""
        armor_dark_c = _NS_seraphienne.PALETTE["armor_darkest"] if dark else _NS_seraphienne.PALETTE["armor_dark"]
        armor_mid_c = _NS_seraphienne.PALETTE["armor_dark"] if dark else _NS_seraphienne.PALETTE["armor_mid"]
        armor_light_c = _NS_seraphienne.PALETTE["armor_mid"] if dark else _NS_seraphienne.PALETTE["armor_light"]
        # Shadow
        _NS_seraphienne._aaline(surface, _NS_seraphienne.PALETTE["shadow_deep"],
                                  (shoulder[0] + 2, shoulder[1] + 2),
                                  (elbow[0] + 2, elbow[1] + 2), 7)
        _NS_seraphienne._aaline(surface, _NS_seraphienne.PALETTE["shadow_deep"],
                                  (elbow[0] + 2, elbow[1] + 2),
                                  (hand[0] + 2, hand[1] + 2), 6)
        # Upper arm
        _NS_seraphienne._aaline(surface, _NS_seraphienne.PALETTE["armor_darkest"], shoulder, elbow, 7)
        _NS_seraphienne._aaline(surface, armor_dark_c, shoulder, elbow, 5)
        _NS_seraphienne._aaline(surface, armor_mid_c,
                                  (shoulder[0], shoulder[1] - 1),
                                  (elbow[0], elbow[1] - 1), 3)
        _NS_seraphienne._aaline(surface, armor_light_c,
                                  (shoulder[0], shoulder[1] - 2),
                                  (elbow[0], elbow[1] - 2), 1)
        # Gold band on upper arm
        mid_ux = (shoulder[0] + elbow[0]) // 2
        mid_uy = (shoulder[1] + elbow[1]) // 2
        pygame.draw.circle(surface, _NS_seraphienne.PALETTE["gold_dark"], (mid_ux, mid_uy), 4)
        pygame.draw.circle(surface, _NS_seraphienne.PALETTE["gold_mid"], (mid_ux, mid_uy), 3)
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_light"], (mid_ux, mid_uy, 1, 1))
        # Elbow joint (armored)
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["armor_darkest"],
                         (elbow[0] - 3, elbow[1] - 3, 7, 7))
        pygame.draw.rect(surface, armor_dark_c, (elbow[0] - 3, elbow[1] - 3, 6, 6))
        pygame.draw.rect(surface, armor_mid_c, (elbow[0] - 2, elbow[1] - 2, 4, 4))
        pygame.draw.rect(surface, armor_light_c, (elbow[0] - 1, elbow[1] - 2, 2, 2))
        # Forearm
        _NS_seraphienne._aaline(surface, _NS_seraphienne.PALETTE["armor_darkest"], elbow, hand, 6)
        _NS_seraphienne._aaline(surface, armor_dark_c, elbow, hand, 4)
        _NS_seraphienne._aaline(surface, armor_mid_c,
                                  (elbow[0], elbow[1] - 1), (hand[0], hand[1] - 1), 2)
        # Gold gauntlet at wrist
        wrist_ux = int(elbow[0] * 0.2 + hand[0] * 0.8)
        wrist_uy = int(elbow[1] * 0.2 + hand[1] * 0.8)
        pygame.draw.circle(surface, _NS_seraphienne.PALETTE["gold_dark"], (wrist_ux, wrist_uy), 4)
        pygame.draw.circle(surface, _NS_seraphienne.PALETTE["gold_mid"], (wrist_ux, wrist_uy), 3)
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_light"],
                         (wrist_ux - 1, wrist_uy - 1, 1, 1))
        # HAND (armored gauntlet)
        pygame.draw.circle(surface, _NS_seraphienne.PALETTE["shadow_deep"],
                           (hand[0] + 1, hand[1] + 1), 4)
        pygame.draw.circle(surface, _NS_seraphienne.PALETTE["armor_dark"], hand, 4)
        pygame.draw.circle(surface, _NS_seraphienne.PALETTE["armor_mid"], hand, 3)
        pygame.draw.circle(surface, _NS_seraphienne.PALETTE["gold_mid"], hand, 2)
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_light"],
                         (hand[0], hand[1] - 1, 1, 1))
    def _draw_shoulder_pauldrons(surface, cx, cy, facing, phase):
        """Big gold pauldrons on shoulders."""
        for side in (-1, 1):
            base_x = cx + side * 14
            base_y = cy
            # Pauldron dome shape
            pauld_pts = [
                (base_x - 6, base_y - 2), (base_x - 5, base_y - 8),
                (base_x - 1, base_y - 11), (base_x + 4, base_y - 10),
                (base_x + 7, base_y - 6), (base_x + 8, base_y),
                (base_x + 6, base_y + 4), (base_x - 5, base_y + 4),
            ]
            _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["shadow_deep"],
                                    [(px + 2, py + 2) for px, py in pauld_pts])
            _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_darkest"], pauld_pts)
            _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_dark"], [
                (base_x - 5, base_y - 2), (base_x - 4, base_y - 7),
                (base_x - 1, base_y - 10), (base_x + 3, base_y - 9),
                (base_x + 6, base_y - 5), (base_x + 7, base_y),
                (base_x + 5, base_y + 3), (base_x - 4, base_y + 3),
            ])
            _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_mid"], [
                (base_x - 3, base_y - 2), (base_x - 3, base_y - 6),
                (base_x, base_y - 8), (base_x + 3, base_y - 6),
                (base_x + 5, base_y - 2), (base_x + 4, base_y + 2),
                (base_x - 3, base_y + 2),
            ])
            _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_light"], [
                (base_x - 1, base_y - 5), (base_x + 2, base_y - 5),
                (base_x + 3, base_y - 2), (base_x, base_y - 1),
            ])
            # Bright highlight
            pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_shine"],
                             (base_x, base_y - 5, 1, 1))
            # Divine gem on pauldron
            gem_pulse = math.sin(phase * 2) * 0.3 + 0.7
            gem_alpha = _NS_seraphienne._alpha(220 * gem_pulse)
            _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_hot"], gem_alpha),
                                        (base_x, base_y - 2), 2)
            pygame.draw.rect(surface, _NS_seraphienne.PALETTE["white"], (base_x, base_y - 2, 1, 1))
            # Small angelic spike on pauldron top
            _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_dark"], [
                (base_x - 1, base_y - 10), (base_x, base_y - 14),
                (base_x + 1, base_y - 10),
            ])
            _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_mid"], [
                (base_x, base_y - 10), (base_x, base_y - 14),
                (base_x + 1, base_y - 12),
            ])
            pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_shine"],
                             (base_x, base_y - 14, 1, 1))
    def _draw_srp_head(surface, cx, cy, facing, phase):
        """Angelic face with glowing gold eyes."""
        # Face shape
        head_pts = [
            (cx - 6, cy + 5), (cx - 7, cy + 1), (cx - 7, cy - 4),
            (cx - 5, cy - 8), (cx - 1, cy - 10), (cx + 3, cy - 10),
            (cx + 6, cy - 7), (cx + 7, cy - 3), (cx + 7, cy + 2),
            (cx + 5, cy + 6), (cx, cy + 7),
        ]
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["shadow_deep"],
                                [(px + 2, py + 2) for px, py in head_pts])
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["skin_darkest"], head_pts)
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["skin_dark"], [
            (cx - 6, cy + 4), (cx - 6, cy), (cx - 6, cy - 3),
            (cx - 4, cy - 7), (cx, cy - 9), (cx + 3, cy - 9),
            (cx + 5, cy - 6), (cx + 6, cy - 2), (cx + 6, cy + 1),
            (cx + 4, cy + 5), (cx, cy + 6),
        ])
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["skin_mid"], [
            (cx - 4, cy + 3), (cx - 5, cy - 1), (cx - 4, cy - 5),
            (cx - 1, cy - 7), (cx + 3, cy - 7), (cx + 5, cy - 4),
            (cx + 5, cy + 1), (cx + 3, cy + 4), (cx, cy + 5),
        ])
        # Cheek highlight
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["skin_light"], [
            (cx + facing * 2, cy - 3), (cx + facing * 4, cy - 1),
            (cx + facing * 3, cy + 2), (cx + facing, cy),
        ])
        # GOLD EYES (glowing divine)
        _NS_seraphienne._draw_glow_eye(surface, cx - 3, cy - 3, phase)
        _NS_seraphienne._draw_glow_eye(surface, cx + 3, cy - 3, phase)
        # Nose (small)
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["skin_darkest"], (cx + 1, cy, 1, 1))
        # Serious mouth (small line, warrior expression)
        pygame.draw.line(surface, _NS_seraphienne.PALETTE["skin_darkest"],
                         (cx - 2, cy + 3), (cx + 2, cy + 3), 1)
    def _draw_glow_eye(surface, ex, ey, phase):
        """Bright gold glowing eye."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Halo
        for r in range(4, 0, -1):
            alpha = _NS_seraphienne._alpha(120 * (4 - r) / 4 * pulse)
            _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_light"], alpha),
                                        (ex, ey), r)
        # Core
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["eye_dark"], (ex - 1, ey - 1, 3, 2))
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["eye_mid"], (ex, ey - 1, 2, 2))
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["eye_light"], (ex, ey, 1, 1))
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["eye_glow"], (ex, ey, 1, 1))
    def _draw_flowing_hair(surface, cx, cy, facing, phase):
        """Long flowing blonde hair behind."""
        sway = math.sin(phase * 0.5) * 2
        # Big hair mass behind
        hair_pts = [
            (cx - 9, cy - 4), (cx - 12, cy + 2),
            (cx - 13 + int(sway), cy + 12),
            (cx - 11 + int(sway), cy + 22),
            (cx - 6 + int(sway * 0.5), cy + 30),
            (cx + 6 - int(sway * 0.5), cy + 30),
            (cx + 11 - int(sway), cy + 22),
            (cx + 13 - int(sway), cy + 12),
            (cx + 12, cy + 2), (cx + 9, cy - 4),
            (cx + 6, cy - 8), (cx - 6, cy - 8),
        ]
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["shadow_deep"],
                                [(px + 2, py + 2) for px, py in hair_pts])
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["hair_darkest"], hair_pts)
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["hair_dark"], [
            (cx - 8, cy - 3), (cx - 11, cy + 1),
            (cx - 12 + int(sway), cy + 11),
            (cx - 10 + int(sway), cy + 20),
            (cx - 4 + int(sway * 0.5), cy + 28),
            (cx + 4 - int(sway * 0.5), cy + 28),
            (cx + 10 - int(sway), cy + 20),
            (cx + 12 - int(sway), cy + 11),
            (cx + 11, cy + 1), (cx + 8, cy - 3),
            (cx + 5, cy - 7), (cx - 5, cy - 7),
        ])
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["hair_mid"], [
            (cx - 6, cy - 1), (cx - 8, cy + 6),
            (cx - 9 + int(sway * 0.7), cy + 18),
            (cx - 2 + int(sway * 0.3), cy + 26),
            (cx + 2 - int(sway * 0.3), cy + 26),
            (cx + 9 - int(sway * 0.7), cy + 18),
            (cx + 8, cy + 6), (cx + 6, cy - 1),
        ])
        # Highlights
        for streak_x in (-7, -3, 3, 7):
            for streak_i in range(3):
                sy_start = cy + 4 + streak_i * 7
                pygame.draw.line(surface, _NS_seraphienne.PALETTE["hair_light"],
                                 (cx + streak_x, sy_start),
                                 (cx + streak_x + int(sway * 0.5),
                                  sy_start + 6), 1)
        # Bright shine
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["hair_shine"], (cx + 4, cy + 4, 1, 3))
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["hair_shine"], (cx - 4, cy + 4, 1, 3))
    def _draw_gold_helm_crown(surface, cx, cy, facing, phase):
        """Gold winged helmet/crown (Kayle's signature)."""
        # Central crown pieces
        # Central big spike
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["shadow_deep"], [
            (cx - 2 + 1, cy + 4 + 1), (cx + 1, cy - 4 + 1), (cx + 2 + 1, cy + 4 + 1),
        ])
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_darkest"], [
            (cx - 2, cy + 4), (cx, cy - 4), (cx + 2, cy + 4),
        ])
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_dark"], [
            (cx - 2, cy + 4), (cx, cy - 4), (cx + 1, cy + 2),
        ])
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_mid"], [
            (cx - 1, cy + 3), (cx, cy - 4), (cx + 1, cy + 3),
        ])
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_light"], [
            (cx, cy + 2), (cx, cy - 4), (cx + 1, cy + 2),
        ])
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_shine"], (cx, cy - 4, 1, 1))
        # Side wing pieces (like helm wings from Kayle)
        for side in (-1, 1):
            # Small wing shape jutting from helm side
            wing_base_x = cx + side * 4
            wing_base_y = cy + 3
            wing_tip_x = cx + side * 10
            wing_tip_y = cy - 1
            _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["shadow_deep"], [
                (wing_base_x + 1, wing_base_y + 1),
                (wing_tip_x + 1, wing_tip_y + 1),
                (wing_base_x + side * 3 + 1, wing_base_y - 1 + 1),
            ])
            _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_darkest"], [
                (wing_base_x, wing_base_y),
                (wing_tip_x, wing_tip_y),
                (wing_base_x + side * 3, wing_base_y - 1),
            ])
            _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_dark"], [
                (wing_base_x, wing_base_y),
                (int((wing_base_x + wing_tip_x) / 2), int((wing_base_y + wing_tip_y) / 2)),
                (wing_base_x + side * 2, wing_base_y - 1),
            ])
            _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_mid"], [
                (wing_base_x, wing_base_y),
                (wing_base_x + side * 2, wing_base_y - 1),
                (int((wing_base_x + wing_tip_x) / 2), wing_base_y - 1),
            ])
            # Feather lines on helm wing
            pygame.draw.line(surface, _NS_seraphienne.PALETTE["gold_light"],
                             (wing_base_x, wing_base_y), (wing_tip_x, wing_tip_y), 1)
            pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_shine"],
                             (wing_tip_x, wing_tip_y, 1, 1))
        # Base helm band
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_dark"], (cx - 6, cy + 4, 13, 2))
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_mid"], (cx - 5, cy + 5, 11, 1))
        # Central gem on forehead
        gem_pulse = math.sin(phase * 2) * 0.3 + 0.7
        gem_alpha = _NS_seraphienne._alpha(230 * gem_pulse)
        for r in range(3, 0, -1):
            alpha = _NS_seraphienne._alpha(120 * (3 - r) / 3 * gem_pulse)
            _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_light"], alpha),
                                        (cx, cy + 5), r)
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_hot"], (cx, cy + 5, 1, 1))
    def _draw_halo(surface, cx, cy, phase):
        """Divine halo above head."""
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        # Big glowing ring (ellipse in perspective)
        halo_alpha = _NS_seraphienne._alpha(200 * pulse)
        for i, (rx, ry, thickness) in enumerate([
            (12, 4, 3), (11, 3, 2), (10, 2, 1),
        ]):
            pygame.draw.ellipse(surface, (*_NS_seraphienne.PALETTE["gold_dark"], halo_alpha),
                                (cx - rx, cy - ry, rx * 2, ry * 2), thickness)
        pygame.draw.ellipse(surface, (*_NS_seraphienne.PALETTE["gold_mid"], halo_alpha),
                            (cx - 10, cy - 2, 20, 4), 2)
        pygame.draw.ellipse(surface, (*_NS_seraphienne.PALETTE["gold_hot"], halo_alpha),
                            (cx - 9, cy - 2, 18, 3), 1)
        pygame.draw.ellipse(surface, (*_NS_seraphienne.PALETTE["gold_shine"], halo_alpha),
                            (cx - 8, cy - 1, 16, 2), 1)
        # Radial sparkles around halo
        for i in range(8):
            ang = phase * 0.5 + i * math.pi / 4
            sr = 14
            sx = cx + int(math.cos(ang) * sr)
            sy = cy + int(math.sin(ang) * 4)
            alpha = _NS_seraphienne._alpha(230 * pulse)
            pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["gold_shine"], alpha),
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["white"], alpha), (sx, sy, 1, 1))
    def _draw_divine_sword(surface, cx, cy, facing, phase, action, attack_progress):
        """Big golden greatsword held by near hand."""
        # Determine hand position and sword angle
        if action == "attack":
            if attack_progress < 0.35:
                t = attack_progress / 0.35
                sword_angle = math.radians(-115 - t * 40) * facing
                arm_len = 22
            elif attack_progress < 0.6:
                t = (attack_progress - 0.35) / 0.25
                sword_angle = math.radians(-155 + t * 150) * facing
                arm_len = 24
            else:
                t = (attack_progress - 0.6) / 0.4
                sword_angle = math.radians(-5 - t * 60) * facing
                arm_len = 22
            shoulder = (cx + facing * 12, cy - 10)
            hand = (shoulder[0] + int(math.cos(sword_angle * 0.9) * arm_len),
                    shoulder[1] + int(math.sin(sword_angle * 0.9) * arm_len))
        else:
            # Idle: sword tilted downward
            idle_sway = math.sin(phase * 0.5) * 2
            hand = (cx + facing * 18, cy + 14 + int(idle_sway * 0.4))
            sword_angle = math.radians(-100 * facing) if facing > 0 else math.radians(-80)
            # Simple: point down
            sword_angle = math.radians(80) * facing
        # Sword direction
        ux = math.cos(sword_angle)
        uy = math.sin(sword_angle)
        # Handle (grip) - below hand
        handle_len = 6
        handle_bottom = (hand[0] - int(ux * handle_len),
                         hand[1] - int(uy * handle_len))
        # Blade (long, extending from hand)
        blade_len = 42
        blade_tip = (hand[0] + int(ux * blade_len),
                     hand[1] + int(uy * blade_len))
        blade_mid = (hand[0] + int(ux * blade_len * 0.5),
                     hand[1] + int(uy * blade_len * 0.5))
        # Perpendicular for blade width
        perp_x = -uy
        perp_y = ux
        # Shadow of whole sword
        _NS_seraphienne._aaline(surface, _NS_seraphienne.PALETTE["shadow_deep"],
                                  (handle_bottom[0] + 2, handle_bottom[1] + 2),
                                  (blade_tip[0] + 2, blade_tip[1] + 2), 5)
        # HANDLE (dark brown/gold)
        _NS_seraphienne._aaline(surface, _NS_seraphienne.PALETTE["blade_darkest"],
                                  handle_bottom, hand, 4)
        _NS_seraphienne._aaline(surface, _NS_seraphienne.PALETTE["gold_darkest"],
                                  handle_bottom, hand, 3)
        _NS_seraphienne._aaline(surface, _NS_seraphienne.PALETTE["gold_dark"],
                                  handle_bottom, hand, 2)
        # Handle wrapping lines
        for wrap_t in (0.2, 0.5, 0.8):
            wx = int(handle_bottom[0] + (hand[0] - handle_bottom[0]) * wrap_t)
            wy = int(handle_bottom[1] + (hand[1] - handle_bottom[1]) * wrap_t)
            pygame.draw.circle(surface, _NS_seraphienne.PALETTE["gold_mid"], (wx, wy), 2)
        # Pommel (round decoration at handle bottom)
        pygame.draw.circle(surface, _NS_seraphienne.PALETTE["gold_darkest"],
                           (handle_bottom[0] + 1, handle_bottom[1] + 1), 3)
        pygame.draw.circle(surface, _NS_seraphienne.PALETTE["gold_dark"], handle_bottom, 3)
        pygame.draw.circle(surface, _NS_seraphienne.PALETTE["gold_mid"], handle_bottom, 2)
        pygame.draw.circle(surface, _NS_seraphienne.PALETTE["gold_light"],
                           (handle_bottom[0] - 1, handle_bottom[1] - 1), 1)
        # CROSSGUARD (perpendicular at hand position)
        guard_len = 8
        guard_a = (hand[0] + int(perp_x * guard_len),
                   hand[1] + int(perp_y * guard_len))
        guard_b = (hand[0] - int(perp_x * guard_len),
                   hand[1] - int(perp_y * guard_len))
        _NS_seraphienne._aaline(surface, _NS_seraphienne.PALETTE["shadow_deep"],
                                  (guard_a[0] + 1, guard_a[1] + 1),
                                  (guard_b[0] + 1, guard_b[1] + 1), 5)
        _NS_seraphienne._aaline(surface, _NS_seraphienne.PALETTE["gold_darkest"], guard_a, guard_b, 4)
        _NS_seraphienne._aaline(surface, _NS_seraphienne.PALETTE["gold_dark"], guard_a, guard_b, 3)
        _NS_seraphienne._aaline(surface, _NS_seraphienne.PALETTE["gold_mid"],
                                  (guard_a[0], guard_a[1] - 1),
                                  (guard_b[0], guard_b[1] - 1), 2)
        # Guard tips (small decorative)
        pygame.draw.circle(surface, _NS_seraphienne.PALETTE["gold_light"], guard_a, 2)
        pygame.draw.circle(surface, _NS_seraphienne.PALETTE["gold_light"], guard_b, 2)
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_shine"], (guard_a[0], guard_a[1], 1, 1))
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_shine"], (guard_b[0], guard_b[1], 1, 1))
        # BLADE — main body (long diamond shape)
        blade_a = (hand[0] + int(perp_x * 3),
                   hand[1] + int(perp_y * 3))
        blade_b = (hand[0] - int(perp_x * 3),
                   hand[1] - int(perp_y * 3))
        blade_mid_a = (blade_mid[0] + int(perp_x * 2),
                        blade_mid[1] + int(perp_y * 2))
        blade_mid_b = (blade_mid[0] - int(perp_x * 2),
                        blade_mid[1] - int(perp_y * 2))
        blade_shape = [blade_a, blade_mid_a, blade_tip, blade_mid_b, blade_b]
        # Shadow
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["shadow_deep"],
                                [(px + 2, py + 2) for px, py in blade_shape])
        # Blade layers (dark to bright)
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["blade_darkest"], blade_shape)
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["blade_dark"], [
            (hand[0] + int(perp_x * 2), hand[1] + int(perp_y * 2)),
            (blade_mid[0] + int(perp_x), blade_mid[1] + int(perp_y)),
            blade_tip,
            (blade_mid[0] - int(perp_x), blade_mid[1] - int(perp_y)),
            (hand[0] - int(perp_x * 2), hand[1] - int(perp_y * 2)),
        ])
        _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["blade_mid"], [
            (hand[0] + int(perp_x), hand[1] + int(perp_y)),
            (blade_mid[0], blade_mid[1]),
            blade_tip,
            (blade_mid[0], blade_mid[1]),
            (hand[0] - int(perp_x), hand[1] - int(perp_y)),
        ])
        # Central fuller line (bright core)
        pygame.draw.line(surface, _NS_seraphienne.PALETTE["blade_light"],
                         hand, blade_tip, 1)
        pygame.draw.line(surface, _NS_seraphienne.PALETTE["blade_hot"],
                         hand, blade_tip, 1)
        # DIVINE FIRE along blade (E starfire effect subtly always visible)
        fire_alpha = _NS_seraphienne._alpha(180 + math.sin(phase * 2) * 40)
        for r in range(6, 0, -1):
            glow_alpha = _NS_seraphienne._alpha(50 * (6 - r) / 6 * (fire_alpha / 255))
            _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["blade_fire"], glow_alpha),
                                        blade_tip, r)
        _NS_seraphienne._aacircle(surface, _NS_seraphienne.PALETTE["gold_hot"], blade_tip, 3)
        _NS_seraphienne._aacircle(surface, _NS_seraphienne.PALETTE["gold_shine"], blade_tip, 1)
        pygame.draw.rect(surface, _NS_seraphienne.PALETTE["white"], (blade_tip[0], blade_tip[1], 1, 1))
        # Small fire particles along blade
        for i in range(4):
            fire_t = (phase * 0.8 + i * 0.25) % 1.0
            fx = int(hand[0] + (blade_tip[0] - hand[0]) * fire_t)
            fy = int(hand[1] + (blade_tip[1] - hand[1]) * fire_t)
            wobble = int(math.sin(phase * 3 + i) * 2)
            fx += int(perp_x * wobble)
            fy += int(perp_y * wobble)
            f_alpha = _NS_seraphienne._alpha(180 * (1 - fire_t * 0.5))
            pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["blade_fire"], f_alpha), (fx, fy, 1, 1))
            pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["gold_hot"], f_alpha), (fx, fy, 1, 1))
    # ============================================================
    # DIVINE SLASH (basic attack arc)
    # ============================================================
    def _draw_divine_slash(surface, cx, cy, facing, progress):
        """Gold divine slash arc during sword swing."""
        if progress < 0.35 or progress > 0.75:
            return
        t = (progress - 0.35) / 0.4
        intensity = math.sin(t * math.pi)
        alpha = _NS_seraphienne._alpha(255 * intensity)
        arc_cx = cx + facing * 26
        arc_cy = cy + 4
        arc_r = 32
        # Slash arc lines (big and dramatic)
        start_angle = math.radians(-90) if facing > 0 else math.radians(180 + 90)
        end_angle = math.radians(90) if facing > 0 else math.radians(180 - 90)
        sweep = start_angle + (end_angle - start_angle) * t
        trail_start = start_angle + (end_angle - start_angle) * max(0, t - 0.4)
        prev_pt = None
        num_segments = 14
        for i in range(num_segments + 1):
            seg_t = i / num_segments
            angle = trail_start + (sweep - trail_start) * seg_t
            px = arc_cx + int(math.cos(angle) * arc_r)
            py = arc_cy + int(math.sin(angle) * arc_r)
            if prev_pt is not None:
                for thickness, color in [
                    (7, (*_NS_seraphienne.PALETTE["gold_darkest"], alpha // 3)),
                    (5, (*_NS_seraphienne.PALETTE["gold_dark"], alpha // 2)),
                    (4, (*_NS_seraphienne.PALETTE["gold_mid"], alpha)),
                    (3, (*_NS_seraphienne.PALETTE["gold_light"], alpha)),
                    (2, (*_NS_seraphienne.PALETTE["gold_hot"], alpha)),
                    (1, (*_NS_seraphienne.PALETTE["gold_shine"], alpha)),
                ]:
                    pygame.draw.line(surface, color, prev_pt, (px, py), thickness)
            prev_pt = (px, py)
        # Sparks and divine feathers along arc
        for i in range(8):
            angle = math.radians(-90) + math.radians(180) * (i / 8)
            if facing < 0:
                angle = math.radians(180) - angle
            spark_r = arc_r + int(math.sin(i + progress * 10) * 5)
            sx = arc_cx + int(math.cos(angle) * spark_r)
            sy = arc_cy + int(math.sin(angle) * spark_r)
            # Sparkle star
            pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["gold_hot"], alpha), (sx, sy, 3, 3))
            pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["white"], alpha), (sx, sy, 1, 1))
        # Small feather particles
        for i in range(5):
            angle = math.radians(-70) + math.radians(140) * (i / 5)
            if facing < 0:
                angle = math.radians(180) - angle
            fr = arc_r + 10 + int(math.sin(progress * 5 + i) * 3)
            fx = arc_cx + int(math.cos(angle) * fr)
            fy = arc_cy + int(math.sin(angle) * fr)
            pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["feather_light"], alpha), (fx, fy, 2, 1))
            pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["feather_shine"], alpha), (fx, fy, 1, 1))
    # ============================================================
    # FALLING FEATHERS + DIVINE PARTICLES (ambient)
    # ============================================================
    def _draw_falling_feathers(surface, cx, cy, phase, intense=False):
        """Gold feathers falling gracefully."""
        strength = 1.4 if intense else 1.0
        for i in range(6):
            t = (phase * 0.3 + i * 0.17) % 1.0
            fx = cx - 40 + i * 14 + int(math.sin(phase * 0.7 + i) * 8)
            fy = cy - 40 + int(t * 80)
            # Feather rotation angle
            rot = math.sin(phase + i * 2) * 0.3
            alpha = _NS_seraphienne._alpha(200 * (1 - abs(t - 0.5) * 1.5) * strength)
            if alpha <= 0:
                continue
            # Small feather shape (elongated leaf)
            feather_len = 4
            fx1 = fx + int(math.cos(rot) * feather_len)
            fy1 = fy + int(math.sin(rot) * feather_len)
            fx2 = fx - int(math.cos(rot) * feather_len)
            fy2 = fy - int(math.sin(rot) * feather_len)
            perp = rot + math.pi / 2
            side1 = (fx + int(math.cos(perp) * 1), fy + int(math.sin(perp) * 1))
            side2 = (fx - int(math.cos(perp) * 1), fy - int(math.sin(perp) * 1))
            _NS_seraphienne._poly(surface, (*_NS_seraphienne.PALETTE["feather_dark"], alpha),
                                    [(fx1, fy1), side1, (fx2, fy2), side2])
            _NS_seraphienne._poly(surface, (*_NS_seraphienne.PALETTE["feather_mid"], alpha),
                                    [(fx1, fy1), side1, (fx2, fy2)])
            pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["feather_shine"], alpha),
                             (fx1, fy1, 1, 1))
    def _draw_divine_particles(surface, cx, cy, phase, intense=False):
        """Gold sparkles rising."""
        strength = 1.4 if intense else 1.0
        for i in range(12):
            t = (phase * 0.5 + i * 0.09) % 1.0
            sx = cx - 30 + i * 5 + int(math.sin(phase + i) * 3)
            sy = cy + 20 - int(t * 40)
            alpha = _NS_seraphienne._alpha(230 * (1 - t) * strength)
            if alpha > 0:
                pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["gold_light"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["gold_hot"], alpha),
                                 (sx, sy, 1, 1))
        # Bigger orbiting sparkles
        for i in range(8):
            angle = phase * 0.4 + i * math.pi / 4
            radius = 45 + int(math.sin(phase + i) * 12)
            ox = cx + int(math.cos(angle) * radius)
            oy = cy + int(math.sin(angle) * radius * 0.5)
            alpha = _NS_seraphienne._alpha(220 * strength)
            pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["gold_hot"], alpha), (ox, oy, 2, 2))
            pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["gold_shine"], alpha), (ox, oy, 1, 1))
    # ============================================================
    # AMBIENT / GROUND (TRUE BOSS scale)
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((170, 34), pygame.SRCALPHA)
        for radius in range(16, 0, -1):
            alpha = max(0, (16 - radius) * 14)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 17 - radius, 150 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (5, 4, 3, 180), (5, 11, 160, 14))
        pygame.draw.ellipse(shadow, (35, 25, 10, 120), (12, 13, 146, 10))
        surface.blit(shadow, (x - 85, y - 17))
    def _draw_divine_aura(surface, x, y, phase):
        """MASSIVE golden divine aura (TRUE BOSS)."""
        pulse = math.sin(phase * 0.5) * 0.3 + 0.7
        aura = pygame.Surface((260, 220), pygame.SRCALPHA)
        # Outer heat glow
        for radius in range(115, 5, -5):
            alpha = _NS_seraphienne._alpha((115 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_seraphienne._aacircle(aura, (*_NS_seraphienne.PALETTE["mist_dark"], alpha),
                                            (130, 110), radius)
        for radius in range(80, 5, -4):
            alpha = _NS_seraphienne._alpha((80 - radius) * 1.4 * pulse)
            if alpha > 0:
                _NS_seraphienne._aacircle(aura, (*_NS_seraphienne.PALETTE["gold_darkest"], alpha),
                                            (130, 110), radius)
        # Bright inner
        for radius in range(50, 5, -3):
            alpha = _NS_seraphienne._alpha((50 - radius) * 1.6 * pulse)
            if alpha > 0:
                _NS_seraphienne._aacircle(aura, (*_NS_seraphienne.PALETTE["gold_dark"], alpha),
                                            (130, 110), radius)
        surface.blit(aura, (x - 130, y - 110))
        # Divine rays emanating
        pulse2 = math.sin(phase * 0.8) * 0.3 + 0.7
        for i in range(8):
            ang = phase * 0.15 + i * math.pi / 4
            for r in range(80, 20, -8):
                rx = x + int(math.cos(ang) * r)
                ry = y + int(math.sin(ang) * r * 0.6)
                alpha = _NS_seraphienne._alpha(50 * (80 - r) / 80 * pulse2)
                pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["gold_light"], alpha),
                                 (rx, ry, 3, 3))
                pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["gold_hot"], alpha),
                                 (rx, ry, 1, 1))
        # Floating orbital sparkles
        for i in range(18):
            angle = phase * 0.3 + i * math.pi / 9
            radius = 60 + int(math.sin(phase + i) * 18)
            sx = x + int(math.cos(angle) * radius)
            sy = y + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_light"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_shine"], (sx, sy, 1, 1))
    def _draw_ground_ring(surface, x, y, phase, skill):
        """Big divine ground ring (TRUE BOSS)."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((200, 62), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_seraphienne.PALETTE["mist_dark"], 200),
                            (5, 22, 190, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_seraphienne.PALETTE["gold_darkest"], 220),
                            (14, 24, 172, 26), 2)
        pygame.draw.ellipse(ring, (*_NS_seraphienne.PALETTE["gold_dark"], 230),
                            (25, 26, 150, 22), 1)
        pygame.draw.ellipse(ring, (*_NS_seraphienne.PALETTE["gold_mid"], 200),
                            (40, 28, 120, 18), 1)
        pygame.draw.ellipse(ring, (*_NS_seraphienne.PALETTE["gold_hot"], 150),
                            (55, 30, 90, 14), 1)
        # Divine runes (cross/sword symbols)
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 100 + int(math.cos(angle) * 55)
            y1 = 35 + int(math.sin(angle) * 10)
            x2 = 100 + int(math.cos(angle) * 88)
            y2 = 35 + int(math.sin(angle) * 15)
            pygame.draw.line(ring, (*_NS_seraphienne.PALETTE["gold_light"], 220),
                             (x1, y1), (x2, y2), 2)
            pygame.draw.line(ring, (*_NS_seraphienne.PALETTE["gold_shine"], 220),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring, (*_NS_seraphienne.PALETTE["gold_hot"],
                                        _NS_seraphienne._alpha(180 * pulse)),
                                (15, 14, 170, 44), 1)
        surface.blit(ring, (x - 100, y - 32))
    # ============================================================
    # SKILL Q - RECKONING (energy spear projectile)
    # ============================================================
    def _draw_reckoning_skill(surface, boss, x, y, timer, phase):
        """Golden energy spear flying toward target."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_seraphienne._target_position(boss, x, y)
        # Charge point (sword tip / hand)
        start_x = x + facing * 30
        start_y = y - 5
        if progress < 0.25:
            # Charge at hand
            t = progress / 0.25
            cr = int(5 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_seraphienne._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_dark"], alpha),
                                            (start_x, start_y), r)
            _NS_seraphienne._aacircle(surface, _NS_seraphienne.PALETTE["gold_mid"],
                                        (start_x, start_y), cr - 2)
            _NS_seraphienne._aacircle(surface, _NS_seraphienne.PALETTE["gold_light"],
                                        (start_x, start_y), max(1, cr - 4))
            _NS_seraphienne._aacircle(surface, _NS_seraphienne.PALETTE["gold_hot"],
                                        (start_x, start_y), max(1, cr - 6))
            _NS_seraphienne._aacircle(surface, _NS_seraphienne.PALETTE["gold_shine"],
                                        (start_x, start_y), max(1, cr - 8))
            pygame.draw.rect(surface, _NS_seraphienne.PALETTE["white"], (start_x, start_y, 1, 1))
            # Sparks gathering
            for i in range(6):
                ang = phase * 4 + i * math.pi / 3
                sx = start_x + int(math.cos(ang) * (cr + 3))
                sy = start_y + int(math.sin(ang) * (cr + 3))
                pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_hot"], (sx, sy, 2, 2))
        else:
            t = (progress - 0.25) / 0.75
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)
            # Direction
            dx = tx - start_x
            dy = ty - start_y
            travel_len = max(1, math.sqrt(dx * dx + dy * dy))
            ux, uy = dx / travel_len, dy / travel_len
            perp_x, perp_y = -uy, ux
            # SPEAR shape (long elongated diamond, sharp point)
            spear_len = 24
            tip = (bx + int(ux * spear_len // 2), by + int(uy * spear_len // 2))
            tail = (bx - int(ux * spear_len // 2), by - int(uy * spear_len // 2))
            side_a = (bx + int(perp_x * 4), by + int(perp_y * 4))
            side_b = (bx - int(perp_x * 4), by - int(perp_y * 4))
            spear_shape = [tip, side_a, tail, side_b]
            # Shadow
            _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["shadow_deep"],
                                    [(px + 2, py + 2) for px, py in spear_shape])
            # Layers
            _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_darkest"], spear_shape)
            _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_dark"], [
                tip,
                (int((tip[0] + side_a[0]) / 2), int((tip[1] + side_a[1]) / 2)),
                (int((tip[0] + tail[0]) / 2), int((tip[1] + tail[1]) / 2)),
                (int((tip[0] + side_b[0]) / 2), int((tip[1] + side_b[1]) / 2)),
            ])
            _NS_seraphienne._poly(surface, _NS_seraphienne.PALETTE["gold_mid"], [
                tip,
                (int((tip[0] * 3 + side_a[0]) / 4), int((tip[1] * 3 + side_a[1]) / 4)),
                (int((tip[0] + tail[0]) / 2), int((tip[1] + tail[1]) / 2)),
                (int((tip[0] * 3 + side_b[0]) / 4), int((tip[1] * 3 + side_b[1]) / 4)),
            ])
            # Bright center line
            pygame.draw.line(surface, _NS_seraphienne.PALETTE["gold_light"], tip, tail, 2)
            pygame.draw.line(surface, _NS_seraphienne.PALETTE["gold_hot"], tip, tail, 1)
            pygame.draw.line(surface, _NS_seraphienne.PALETTE["gold_shine"], tip, tail, 1)
            pygame.draw.rect(surface, _NS_seraphienne.PALETTE["white"], (tip[0], tip[1], 1, 1))
            # BIG comet trail behind spear
            for i in range(1, 12):
                trail_t = max(0.0, t - i * 0.045)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_seraphienne._alpha(240 - i * 20)
                size = max(1, 9 - i)
                _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_darkest"], alpha),
                                            (px, py), size + 1)
                _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_dark"], alpha),
                                            (px, py), size)
                _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_mid"], alpha),
                                            (px, py), max(1, size - 1))
                _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_light"], alpha),
                                            (px, py), max(1, size - 2))
                _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_hot"], alpha),
                                            (px, py), max(1, size - 3))
                # Feather particles in trail
                if i < 5:
                    for s in range(2):
                        f_ang = t * 8 + i + s
                        fx = px + int(math.sin(f_ang) * (size + 2))
                        fy = py + int(math.cos(f_ang) * (size + 2))
                        pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["feather_shine"], alpha),
                                         (fx, fy, 2, 1))
                        pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["gold_shine"], alpha),
                                         (fx, fy, 1, 1))
            # Big glow around spear
            for r in range(15, 3, -2):
                alpha = _NS_seraphienne._alpha(100 * (15 - r) / 15)
                _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_light"], alpha),
                                            (bx, by), r)
            # HUGE impact burst
            if t > 0.85:
                st = (t - 0.85) / 0.15
                r = int(15 + st * 35)
                alpha = _NS_seraphienne._alpha(250 * (1 - st))
                # Multi-ring burst
                _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_darkest"], alpha),
                                            (tx, ty), r + 5, 4)
                _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_dark"], alpha),
                                            (tx, ty), r, 3)
                _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_mid"], alpha),
                                            (tx, ty), max(1, r - 7), 2)
                _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_light"], alpha),
                                            (tx, ty), max(1, r - 14), 2)
                _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_hot"], alpha),
                                            (tx, ty), max(1, r - 20), 1)
                _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["white"], alpha),
                                            (tx, ty), max(1, r // 5))
                # Radial rays
                for i in range(14):
                    angle_s = i * math.pi / 7
                    ex = tx + int(math.cos(angle_s) * r)
                    ey = ty + int(math.sin(angle_s) * r * 0.9)
                    pygame.draw.line(surface, (*_NS_seraphienne.PALETTE["gold_hot"], alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["gold_shine"], alpha),
                                     (ex, ey, 3, 3))
                    pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["white"], alpha),
                                     (ex, ey, 1, 1))
                # Damage number placeholders
                for a_i in range(3):
                    ax = tx - 20 + a_i * 15
                    ay = ty - 20 - int(math.sin(phase * 3 + a_i) * 3)
                    pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["gold_hot"], alpha),
                                     (ax, ay, 3, 2))
    # ============================================================
    # SKILL W - DIVINE BLESSING (shield + heal aura)
    # ============================================================
    def _draw_blessing_ground(surface, boss, x, y, timer, phase):
        """Ring under boss during blessing."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(2):
            r = int(45 + i * 8 + math.sin(phase * 2) * 3)
            alpha = _NS_seraphienne._alpha(220 - i * 70)
            _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_mid"], alpha),
                                        (x, y + 55), r, 2)
            _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_light"], alpha),
                                        (x, y + 55), r, 1)
    def _draw_blessing_bubble(surface, boss, x, y, timer, phase):
        """Golden dome shield around boss."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Bubble radius
        breath = math.sin(phase * 2) * 3
        r = 62 + int(breath)
        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)
        # Multiple ring layers
        for i, (thickness, alpha_val) in enumerate([
            (4, 130), (3, 170), (2, 210), (1, 250),
        ]):
            _NS_seraphienne._aacircle(bubble, (*_NS_seraphienne.PALETTE["gold_darkest"], alpha_val),
                                        center, r - i, thickness)
            _NS_seraphienne._aacircle(bubble, (*_NS_seraphienne.PALETTE["gold_mid"], alpha_val),
                                        center, r - i - 1, max(1, thickness - 1))
            _NS_seraphienne._aacircle(bubble, (*_NS_seraphienne.PALETTE["gold_light"], alpha_val),
                                        center, r - i - 2, 1)
        # Inner translucent fill
        inner_alpha = _NS_seraphienne._alpha(70 + math.sin(phase * 2) * 20)
        _NS_seraphienne._aacircle(bubble, (*_NS_seraphienne.PALETTE["gold_mid"], inner_alpha),
                                    center, r - 4)
        # Rotating gold sparkles on edge
        for i in range(20):
            angle = phase * 1.5 + i * math.pi / 10
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            pygame.draw.rect(bubble, _NS_seraphienne.PALETTE["gold_hot"], (sx, sy, 3, 3))
            pygame.draw.rect(bubble, _NS_seraphienne.PALETTE["gold_shine"], (sx, sy, 1, 1))
        # Cross emblems at 4 cardinal points
        for i in range(4):
            angle = phase * 0.5 + i * math.pi / 2
            emb_x = center[0] + int(math.cos(angle) * (r - 5))
            emb_y = center[1] + int(math.sin(angle) * (r - 5))
            emb_alpha = _NS_seraphienne._alpha(240)
            # Vertical bar
            pygame.draw.rect(bubble, (*_NS_seraphienne.PALETTE["gold_hot"], emb_alpha),
                             (emb_x, emb_y - 4, 2, 8))
            # Horizontal bar
            pygame.draw.rect(bubble, (*_NS_seraphienne.PALETTE["gold_hot"], emb_alpha),
                             (emb_x - 3, emb_y - 1, 8, 2))
            pygame.draw.rect(bubble, (*_NS_seraphienne.PALETTE["gold_shine"], emb_alpha),
                             (emb_x, emb_y, 1, 1))
        surface.blit(bubble, (x - r - 10, y - r - 10))
        # Energy tendrils
        for i in range(8):
            angle = phase * 0.8 + i * math.pi / 4
            end_x = x + int(math.cos(angle) * (r + 8))
            end_y = y + int(math.sin(angle) * (r + 8))
            alpha = _NS_seraphienne._alpha(160 + math.sin(phase * 3 + i) * 40)
            pygame.draw.line(surface, (*_NS_seraphienne.PALETTE["gold_hot"], alpha),
                             (x + int(math.cos(angle) * r),
                              y + int(math.sin(angle) * r)),
                             (end_x, end_y), 2)
            pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_shine"], (end_x, end_y, 1, 1))
    # ============================================================
    # SKILL E - STARFIRE SPELLBLADE (empowered sword beam)
    # ============================================================
    def _draw_starfire_ground(surface, boss, x, y, timer, phase):
        """Small burning trail from boss to target."""
        tx, ty = _NS_seraphienne._target_position(boss, x, y)
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            # Line indicator warming up
            alpha = _NS_seraphienne._alpha(180 * (progress / 0.4))
            for w, c in [(6, _NS_seraphienne.PALETTE["gold_dark"]),
                         (3, _NS_seraphienne.PALETTE["gold_mid"]),
                         (1, _NS_seraphienne.PALETTE["gold_hot"])]:
                pygame.draw.line(surface, (*c, alpha), (x, y + 55), (tx, ty), w)
    def _draw_starfire_foreground(surface, boss, x, y, timer, phase):
        """Sword ignites → firing beam at target."""
        tx, ty = _NS_seraphienne._target_position(boss, x, y)
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        facing = boss.direction
        # Sword ignition (blade glow amplified)
        sword_tip = (x + facing * 40, y - 20)
        if progress < 0.4:
            # Wind-up: sword blazing bright
            t = progress / 0.4
            intensity = t
            for r in range(15, 0, -2):
                alpha = _NS_seraphienne._alpha(180 * (15 - r) / 15 * intensity)
                _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["blade_fire"], alpha),
                                            sword_tip, r)
            _NS_seraphienne._aacircle(surface, _NS_seraphienne.PALETTE["gold_hot"], sword_tip, 6)
            _NS_seraphienne._aacircle(surface, _NS_seraphienne.PALETTE["gold_shine"], sword_tip, 3)
            _NS_seraphienne._aacircle(surface, _NS_seraphienne.PALETTE["white"], sword_tip, 1)
            # Fire particles gathering
            for i in range(8):
                ang = phase * 3 + i * math.pi / 4
                sx = sword_tip[0] + int(math.cos(ang) * (12 + int(intensity * 5)))
                sy = sword_tip[1] + int(math.sin(ang) * (12 + int(intensity * 5)))
                pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_hot"], (sx, sy, 2, 2))
                pygame.draw.rect(surface, _NS_seraphienne.PALETTE["white"], (sx, sy, 1, 1))
        elif progress < 0.8:
            # BEAM FIRING: energy travels to target
            t = (progress - 0.4) / 0.4
            intensity = math.sin(t * math.pi)
            # Direction from sword to target
            dx = tx - sword_tip[0]
            dy = ty - sword_tip[1]
            travel_len = max(1, math.sqrt(dx * dx + dy * dy))
            ux, uy = dx / travel_len, dy / travel_len
            # Beam extends from sword to target
            beam_end_x = int(sword_tip[0] + ux * travel_len * min(1.0, t * 1.5))
            beam_end_y = int(sword_tip[1] + uy * travel_len * min(1.0, t * 1.5))
            # Multi-layer beam
            for thickness, color in [
                (10, (*_NS_seraphienne.PALETTE["gold_darkest"],
                      _NS_seraphienne._alpha(200 * intensity))),
                (7, (*_NS_seraphienne.PALETTE["gold_dark"],
                     _NS_seraphienne._alpha(220 * intensity))),
                (5, (*_NS_seraphienne.PALETTE["gold_mid"],
                     _NS_seraphienne._alpha(240 * intensity))),
                (3, (*_NS_seraphienne.PALETTE["gold_hot"],
                     _NS_seraphienne._alpha(255 * intensity))),
                (1, (*_NS_seraphienne.PALETTE["gold_shine"],
                     _NS_seraphienne._alpha(255 * intensity))),
            ]:
                pygame.draw.line(surface, color, sword_tip, (beam_end_x, beam_end_y), thickness)
            # Sparkles along beam
            for i in range(10):
                spark_t = (phase * 2 + i * 0.1) % 1.0
                spark_x = sword_tip[0] + int((beam_end_x - sword_tip[0]) * spark_t)
                spark_y = sword_tip[1] + int((beam_end_y - sword_tip[1]) * spark_t)
                perp = math.atan2(uy, ux) + math.pi / 2
                offset = math.sin(phase * 5 + i) * 3
                spark_x += int(math.cos(perp) * offset)
                spark_y += int(math.sin(perp) * offset)
                pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["gold_shine"],
                                            _NS_seraphienne._alpha(230 * intensity)),
                                 (spark_x, spark_y, 2, 2))
                pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["white"],
                                            _NS_seraphienne._alpha(255 * intensity)),
                                 (spark_x, spark_y, 1, 1))
            # Impact at target
            if t > 0.5:
                st = (t - 0.5) / 0.5
                r = int(12 + st * 25)
                alpha = _NS_seraphienne._alpha(240 * intensity)
                _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_darkest"], alpha),
                                            (tx, ty), r + 3, 3)
                _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_dark"], alpha),
                                            (tx, ty), r, 3)
                _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_mid"], alpha),
                                            (tx, ty), max(1, r - 6), 2)
                _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_hot"], alpha),
                                            (tx, ty), max(1, r - 12), 1)
                # Star burst rays
                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = tx + int(math.cos(angle_s) * r)
                    ey = ty + int(math.sin(angle_s) * r)
                    pygame.draw.line(surface, (*_NS_seraphienne.PALETTE["gold_shine"], alpha),
                                     (tx, ty), (ex, ey), 2)
                    pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["white"], alpha),
                                     (ex, ey, 2, 2))
        else:
            # Aftermath: lingering embers
            t = (progress - 0.8) / 0.2
            for i in range(8):
                em_t = (phase * 0.8 + i * 0.13) % 1.0
                ex = tx + int(math.sin(phase + i) * 15)
                ey = ty - int(em_t * 25)
                alpha = _NS_seraphienne._alpha(200 * (1 - t) * (1 - em_t))
                if alpha > 0:
                    pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["gold_hot"], alpha),
                                     (ex, ey, 2, 2))
                    pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["gold_shine"], alpha),
                                     (ex, ey, 1, 1))
    # ============================================================
    # SKILL R - INTERVENTION (invulnerability + pillar of light)
    # ============================================================
    def _draw_intervention_ground(surface, boss, x, y, timer, phase):
        """Massive golden circle under boss."""
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(90 * min(1.0, progress * 1.5))
        if r > 5:
            # Big concentric rings pattern
            for ring_i in range(5):
                ring_r = r - ring_i * 14
                if ring_r <= 0:
                    continue
                alpha = _NS_seraphienne._alpha(220 - ring_i * 30)
                pygame.draw.ellipse(surface, (*_NS_seraphienne.PALETTE["gold_darkest"], alpha),
                                    (x - ring_r, y + 55 - ring_r // 3,
                                     ring_r * 2, ring_r * 2 // 3), 3)
                pygame.draw.ellipse(surface, (*_NS_seraphienne.PALETTE["gold_mid"], alpha),
                                    (x - ring_r + 3, y + 55 - ring_r // 3 + 2,
                                     ring_r * 2 - 6, ring_r * 2 // 3 - 4), 2)
                pygame.draw.ellipse(surface, (*_NS_seraphienne.PALETTE["gold_hot"], alpha),
                                    (x - ring_r + 6, y + 55 - ring_r // 3 + 4,
                                     ring_r * 2 - 12, ring_r * 2 // 3 - 8), 1)
            # Cross/sword symbols around ring
            for i in range(12):
                ang = i * math.pi / 6 + phase * 0.2
                rx = x + int(math.cos(ang) * r)
                ry = y + 55 + int(math.sin(ang) * r * 0.35)
                # Small vertical bar
                pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_shine"], (rx, ry - 3, 2, 6))
                pygame.draw.rect(surface, _NS_seraphienne.PALETTE["white"], (rx, ry - 2, 1, 4))
    def _draw_intervention_foreground(surface, boss, x, y, timer, phase):
        """Descending pillar of light + shield dome + invulnerability rays."""
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # PHASE 1: Descending light from sky
            t = progress / 0.3
            # Light pillar from sky to boss (getting brighter)
            beam_top_y = max(0, y - 200)
            beam_bot_y = y
            intensity = t
            # Multi-layer pillar (widening)
            for layer_i, (width, alpha_val) in enumerate([
                (24, 100), (18, 140), (12, 180), (6, 220), (2, 255),
            ]):
                actual_alpha = _NS_seraphienne._alpha(alpha_val * intensity)
                colors = [
                    _NS_seraphienne.PALETTE["gold_darkest"],
                    _NS_seraphienne.PALETTE["gold_dark"],
                    _NS_seraphienne.PALETTE["gold_mid"],
                    _NS_seraphienne.PALETTE["gold_hot"],
                    _NS_seraphienne.PALETTE["gold_shine"],
                ]
                color = colors[min(layer_i, 4)]
                pygame.draw.rect(surface, (*color, actual_alpha),
                                 (x - width // 2, beam_top_y, width, beam_bot_y - beam_top_y))
            # Sparkles rising in pillar
            for i in range(15):
                spark_t = (phase * 2 + i * 0.13) % 1.0
                spark_y = beam_bot_y - int(spark_t * (beam_bot_y - beam_top_y))
                spark_x = x + int(math.sin(phase * 5 + i) * 8)
                alpha = _NS_seraphienne._alpha(240 * intensity * (1 - spark_t * 0.5))
                pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["gold_shine"], alpha),
                                 (spark_x, spark_y, 2, 2))
                pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["white"], alpha),
                                 (spark_x, spark_y, 1, 1))
        elif progress < 0.8:
            # PHASE 2: DIVINE SHIELD DOME (invulnerability)
            t = (progress - 0.3) / 0.5
            # Big shield dome
            dome_r = 55 + int(math.sin(phase * 2) * 3)
            dome = pygame.Surface((dome_r * 2 + 20, dome_r * 2 + 20), pygame.SRCALPHA)
            dome_center = (dome_r + 10, dome_r + 10)
            # Multi-layer dome
            for i, (thickness, alpha_val) in enumerate([
                (5, 160), (4, 200), (3, 230), (2, 250), (1, 255),
            ]):
                _NS_seraphienne._aacircle(dome, (*_NS_seraphienne.PALETTE["gold_darkest"], alpha_val),
                                            dome_center, dome_r - i, thickness)
                _NS_seraphienne._aacircle(dome, (*_NS_seraphienne.PALETTE["gold_mid"], alpha_val),
                                            dome_center, dome_r - i - 1,
                                            max(1, thickness - 1))
                _NS_seraphienne._aacircle(dome, (*_NS_seraphienne.PALETTE["gold_light"], alpha_val),
                                            dome_center, dome_r - i - 2, 1)
            # Inner fill (translucent)
            inner_alpha = _NS_seraphienne._alpha(80 + math.sin(phase * 2) * 25)
            _NS_seraphienne._aacircle(dome, (*_NS_seraphienne.PALETTE["gold_mid"], inner_alpha),
                                        dome_center, dome_r - 5)
            # Rotating cross emblems
            for i in range(4):
                angle = phase * 0.8 + i * math.pi / 2
                emb_x = dome_center[0] + int(math.cos(angle) * (dome_r - 6))
                emb_y = dome_center[1] + int(math.sin(angle) * (dome_r - 6))
                emb_alpha = _NS_seraphienne._alpha(250)
                pygame.draw.rect(dome, (*_NS_seraphienne.PALETTE["gold_hot"], emb_alpha),
                                 (emb_x, emb_y - 5, 2, 10))
                pygame.draw.rect(dome, (*_NS_seraphienne.PALETTE["gold_hot"], emb_alpha),
                                 (emb_x - 4, emb_y - 1, 10, 2))
                pygame.draw.rect(dome, (*_NS_seraphienne.PALETTE["white"], emb_alpha),
                                 (emb_x, emb_y, 1, 1))
            # Rotating sparkles
            for i in range(24):
                angle = phase * 1.5 + i * math.pi / 12
                sx = dome_center[0] + int(math.cos(angle) * dome_r)
                sy = dome_center[1] + int(math.sin(angle) * dome_r)
                pygame.draw.rect(dome, _NS_seraphienne.PALETTE["gold_shine"], (sx, sy, 3, 3))
                pygame.draw.rect(dome, _NS_seraphienne.PALETTE["white"], (sx, sy, 1, 1))
            surface.blit(dome, (x - dome_r - 10, y - dome_r - 10))
            # INVULNERABILITY indicator (small shield icons floating up)
            for a_i in range(3):
                ax = x - 15 + a_i * 15
                ay = y - 40 - int(math.sin(phase * 3 + a_i) * 4) - int(t * 15)
                alpha = _NS_seraphienne._alpha(220 * (1 - t * 0.5))
                # Shield shape (small)
                pygame.draw.polygon(surface, (*_NS_seraphienne.PALETTE["gold_hot"], alpha), [
                    (ax, ay - 3), (ax + 3, ay - 2),
                    (ax + 3, ay + 2), (ax, ay + 4), (ax - 3, ay + 2),
                    (ax - 3, ay - 2),
                ])
                pygame.draw.polygon(surface, (*_NS_seraphienne.PALETTE["gold_shine"], alpha), [
                    (ax, ay - 2), (ax + 2, ay - 1),
                    (ax + 2, ay + 1), (ax, ay + 3), (ax - 2, ay + 1),
                    (ax - 2, ay - 1),
                ])
            # Divine light rays emanating outward
            for i in range(12):
                ang = phase * 0.4 + i * math.pi / 6
                ray_len = 20 + int(math.sin(phase * 2 + i) * 8)
                rx1 = x + int(math.cos(ang) * dome_r)
                ry1 = y + int(math.sin(ang) * dome_r)
                rx2 = x + int(math.cos(ang) * (dome_r + ray_len))
                ry2 = y + int(math.sin(ang) * (dome_r + ray_len))
                alpha = _NS_seraphienne._alpha(200 + math.sin(phase * 3 + i) * 40)
                pygame.draw.line(surface, (*_NS_seraphienne.PALETTE["gold_hot"], alpha),
                                 (rx1, ry1), (rx2, ry2), 2)
                pygame.draw.rect(surface, _NS_seraphienne.PALETTE["gold_shine"], (rx2, ry2, 2, 2))
        else:
            # Aftermath: lingering divine glow + feathers
            t = (progress - 0.8) / 0.2
            # Fading dome
            r_fade = 55
            alpha_fade = _NS_seraphienne._alpha(200 * (1 - t))
            _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_mid"], alpha_fade),
                                        (x, y), r_fade, 2)
            _NS_seraphienne._aacircle(surface, (*_NS_seraphienne.PALETTE["gold_light"], alpha_fade),
                                        (x, y), r_fade, 1)
            # Feathers gently falling
            for i in range(10):
                fall_t = (phase * 0.5 + i * 0.1) % 1.0
                fx = x + int(math.sin(phase + i) * 40)
                fy = y - 30 + int(fall_t * 60)
                alpha = _NS_seraphienne._alpha(180 * (1 - t) * (1 - fall_t))
                if alpha > 0:
                    # Small feather
                    pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["feather_mid"], alpha),
                                     (fx, fy, 3, 1))
                    pygame.draw.rect(surface, (*_NS_seraphienne.PALETTE["feather_shine"], alpha),
                                     (fx + 1, fy, 1, 1))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_drav(surface, boss, x, y):
    """Entry point drav."""
    return _NS_drav.draw_drav(surface, boss, x, y)


def draw_lyrienne(surface, boss, x, y):
    """Entry point lyrienne."""
    return _NS_lyrienne.draw_lyrienne(surface, boss, x, y)


def draw_valthar(surface, boss, x, y):
    """Entry point valthar."""
    return _NS_valthar.draw_valthar(surface, boss, x, y)


def draw_seraphienne(surface, boss, x, y):
    """Entry point seraphienne."""
    return _NS_seraphienne.draw_seraphienne(surface, boss, x, y)
